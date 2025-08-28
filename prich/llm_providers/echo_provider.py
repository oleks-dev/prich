from prich.llm_providers.llm_provider_interface import LLMProvider
from prich.models.config_providers import EchoProviderModel

class EchoProvider(LLMProvider):
    def __init__(self, name: str, provider: EchoProviderModel):
        self.name: str = name
        self.mode: str = provider.mode
        self.show_response: bool = False

    def send_prompt(self, prompt: str = None, instructions: str = None, input_: str = None) -> str:
        if prompt:
            return prompt
        else:
            return f"{instructions}\n{input_}"
