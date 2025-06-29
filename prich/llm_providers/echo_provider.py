from prich.llm_providers.llm_provider_interface import LLMProvider
from prich.models.config import ProviderConfig

class EchoProvider(LLMProvider):
    def __init__(self, name: str, provider: ProviderConfig):
        self.name: str = name
        self.mode: str = provider.mode
        self.show_response: bool = False

    def send_prompt(self, prompt: str) -> str:
        return prompt
