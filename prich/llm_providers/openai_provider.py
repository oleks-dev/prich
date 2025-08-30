import json
from contextlib import nullcontext

import click

from prich.core.utils import replace_env_vars, console, is_quiet, is_only_final_output, console_print
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
            configuration['api_key'] = replace_env_vars(configuration['api_key'], False)
        self.client = OpenAI(**configuration)

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

            status = console.status("Thinking...") if not is_quiet() and not is_only_final_output() else nullcontext()

            with status:
                if options['stream']:
                    # Streaming mode
                    with self.client.chat.completions.create(**options) as response:
                        for chunk in response:
                            if not chunk:
                                continue
                            if chunk.choices and chunk.choices[0].delta:
                                text.append(chunk.choices[0].delta.content)
                                if self.show_response and not is_quiet() and not is_only_final_output():
                                    if status._live.is_started and chunk:
                                        status.stop()
                                    console_print(text[-1], end='')
                        if self.show_response and not is_quiet() and not is_only_final_output():
                            console_print()
                else:
                    # Non-streaming mode
                    response = self.client.chat.completions.create(**options)
                    output = response.choices[0].message.content
                    if self.show_response and not is_quiet() and not is_only_final_output():
                        if not is_quiet() and not is_only_final_output():
                            status.stop()
                        console_print()
                    text.append(output)

            return ''.join(text).strip()
        except Exception as e:
            if "rate_limit" in str(e).lower():
                raise click.ClickException("Rate limit exceeded. Please try again later.")
            elif "authentication" in str(e).lower():
                raise click.ClickException("Invalid API key. Check .prich/config.yaml.")
            raise click.ClickException(f"OpenAI error: {str(e)}")

