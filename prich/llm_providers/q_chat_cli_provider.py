import subprocess
import click
from prich.llm_providers.llm_provider_interface import LLMProvider
from prich.models.config import ProviderConfig

class QChatCLIProvider(LLMProvider):
    def __init__(self, name: str, provider: ProviderConfig):
        self.options = provider.options
        self.name = name
        self.mode = provider.mode
        self.show_response: bool = False

    def send_prompt(self, prompt: str) -> str:
        cmd = ['q', 'chat']
        if self.options:
            cmd.extend(self.options)
        try:
            response = subprocess.run(
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                check=True
            )
        except Exception as e:
            raise click.ClickException(f"QChatCLI error: {str(e)}")
        return response if response else ""
