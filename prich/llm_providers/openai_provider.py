import json
import click

from prich.core.utils import replace_env_vars
from prich.models.config import ProviderConfig
from prich.llm_providers.llm_provider_interface import LLMProvider
from prich.llm_providers.base_optional_provider import LazyOptionalProvider

class OpenAIProvider(LLMProvider, LazyOptionalProvider):
    def __init__(self, 
                 name: str,
                 provider: ProviderConfig
                 ):
        super().__init__()
        self.name = name
        self.provider = provider
        self.client = None

    def _ensure_client(self):
        if self.client:
            return
        OpenAI = self._lazy_import_from("openai", "OpenAI")
        self.client = OpenAI(
            api_key=replace_env_vars(self.provider.api_key),
            base_url=self.provider.base_url,
            timeout=self.provider.timeout
        )

    def send_prompt(self, prompt: str) -> str:
        self._ensure_client()
        try:
            messages = json.loads(prompt)
            response = self.client.chat.completions.create(
                model=self.provider.model,
                messages=messages,
                max_tokens=self.provider.max_tokens,
                temperature=self.provider.temperature,
                stop=self.provider.stop,
                timeout=self.provider.timeout
            )
            return response.choices[0].message.content
        except Exception as e:
            if "rate_limit" in str(e).lower():
                raise click.ClickException("Rate limit exceeded. Please try again later.")
            elif "authentication" in str(e).lower():
                raise click.ClickException("Invalid API key. Check .prich/config.yaml.")
            raise click.ClickException(f"OpenAI error: {str(e)}")

