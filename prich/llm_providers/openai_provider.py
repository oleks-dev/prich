import json
import click

from prich.core.utils import replace_env_vars
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

    def _ensure_client(self):
        if self.client:
            return
        OpenAI = self._lazy_import_from("openai", "OpenAI")
        configuration = self.provider.configuration if self.provider.configuration is not None else {}
        if configuration.get("api_key"):
            configuration['api_key'] = replace_env_vars(configuration['api_key'])
        self.client = OpenAI(**configuration)

    def send_prompt(self, prompt: str = None, system: str = None, user: str = None) -> str:
        self._ensure_client()
        try:
            if prompt:
                messages = json.loads(prompt)
            else:
                messages = []
                if system:
                    messages.append({"role": "system", "content": system})
                messages.append({"role": "user", "content": user})
            options = self.provider.options if self.provider.options is not None else {}
            options['messages'] = messages
            response = self.client.chat.completions.create(**options)
            return response.choices[0].message.content
        except Exception as e:
            if "rate_limit" in str(e).lower():
                raise click.ClickException("Rate limit exceeded. Please try again later.")
            elif "authentication" in str(e).lower():
                raise click.ClickException("Invalid API key. Check .prich/config.yaml.")
            raise click.ClickException(f"OpenAI error: {str(e)}")

