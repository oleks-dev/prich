import subprocess
import click
from prich.llm_providers.llm_provider_interface import LLMProvider
from prich.models.config_providers import STDINConsumerProviderModel

class STDINConsumerProvider(LLMProvider):
    def __init__(self, name: str, provider: STDINConsumerProviderModel):
        self.provider = provider
        self.name = name
        self.show_response: bool = False

    @staticmethod
    def clear_ansi(text: str) -> str:
        import re
        return re.sub(r'\x1b\[[0-9;]*m', '', text)

    def send_prompt(self, prompt: str = None, instructions: str = None, input_: str = None) -> str:
        if instructions or input_:
            raise click.ClickException("stdin consumer provider requires provider mode")
        cmd = [self.provider.call]
        if self.provider.args:
            cmd.extend(self.provider.args)
        try:
            response = subprocess.run(
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                check=False
            )
        except Exception as e:
            raise click.ClickException(f"STDIN consumer provider error: {str(e)}")
        if response.returncode != 0:
            raise click.ClickException(f"stdout:\n{response.stdout}\n\nstderr:\n{response.stderr}\n\nError during STDIN consumer provider execution, exit code {response.returncode}.")
        clean_output = self.clear_ansi(response.stdout)
        return clean_output
