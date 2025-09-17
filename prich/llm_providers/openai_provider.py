import contextlib
import json
import os
import click
from json import JSONDecodeError
from contextlib import nullcontext
from prich.constants import PRICH_DIR_NAME
from prich.core.utils import console, console_print, is_print_enabled
from prich.core.variable_utils import replace_env_vars
from prich.models.config_providers import OpenAIProviderModel
from prich.llm_providers.llm_provider_interface import LLMProvider
from prich.llm_providers.base_optional_provider import LazyOptionalProvider


class OpenAIProvider(LLMProvider, LazyOptionalProvider):
    def __init__(self, 
                 name: str,
                 provider: OpenAIProviderModel
                 ):
        super().__init__()
        self.name = name
        self.provider = provider
        self.client = None
        self.show_response = True

    def _ensure_client(self):
        if self.client:
            return
        OpenAI = self._lazy_import_from("openai", "OpenAI")
        configuration = self.provider.configuration if self.provider.configuration is not None else {}
        if configuration.get("api_key"):
            configuration['api_key'] = replace_env_vars(configuration['api_key'], dict(os.environ))
        self.client = OpenAI(**configuration)
        # TODO: add model presence check

    def _get_completion(self, **options) -> str:
        response = self.client.chat.completions.create(**options)
        return response.choices[0].message.content

    @contextlib.contextmanager
    def _get_stream_completion_chunks(self, **options):
        stream = self.client.chat.completions.create(**options)
        try:
            yield stream
        finally:
            stream.close()

    def send_prompt(self, prompt: str = None, instructions: str = None, input_: str = None) -> str:
        self._ensure_client()
        text = []
        try:
            if prompt:
                messages = json.loads(prompt)
            else:
                messages = []
                if instructions:
                    messages.append({"role": "system", "content": instructions})
                messages.append({"role": "user", "content": input_})
            options = self.provider.options if self.provider.options is not None else {}
            options['messages'] = messages

            status = console.status("Thinking...") if is_print_enabled() else nullcontext()

            with status:
                if options.get('stream'):
                    # Streaming mode
                    with self._get_stream_completion_chunks(**options) as response:
                        for chunk in response:
                            if not chunk:
                                continue
                            if chunk.choices and chunk.choices[0].delta:
                                text.append(chunk.choices[0].delta.content)
                                if self.show_response:
                                    if not isinstance(status, nullcontext) and status._live.is_started and chunk:
                                        status.stop()
                                    console_print(text[-1], end='')
                        if self.show_response:
                            console_print()
                else:
                    # Non-streaming mode
                    output = self._get_completion(**options)
                    if self.show_response:
                        if not isinstance(status, nullcontext):
                            status.stop()
                        console_print(output)
                    text.append(output)

            return ''.join(text)
        except Exception as e:
            if isinstance(e, JSONDecodeError):
                raise click.ClickException(f"Failed to decode prompt JSON '{prompt}': {str(e)}")
            if "rate_limit" in str(e).lower():
                raise click.ClickException("Rate limit exceeded. Please try again later.")
            elif "authentication" in str(e).lower():
                raise click.ClickException(f"Invalid API key. Check {PRICH_DIR_NAME}/config.yaml.")
            raise click.ClickException(f"OpenAI error: {str(e)}")

