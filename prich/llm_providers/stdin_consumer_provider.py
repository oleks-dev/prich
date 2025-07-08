import subprocess
import click
from prich.llm_providers.llm_provider_interface import LLMProvider
from prich.models.config import ProviderConfig

class STDINConsumerProvider(LLMProvider):
    def __init__(self, name: str, provider: ProviderConfig):
        self.provider = provider
        self.name = name
        self.show_response: bool = False

    def send_prompt(self, prompt: str) -> str:
        cmd = [self.provider.cmd]
        if self.provider.options:
            cmd.extend(self.provider.options)
        try:
            response = subprocess.run(
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                check=True
            )
        except Exception as e:
            raise click.ClickException(f"STDIN consumer provider error: {str(e)}")
        return response if response else ""
