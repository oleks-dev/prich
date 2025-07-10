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
    def clean_stdout(text: str, *, strip_prefix=None, slice_range=None) -> str:
        if strip_prefix and text.startswith(strip_prefix):
            text = text[len(strip_prefix):]

        if slice_range:
            start, end = slice_range
            text = text[start:end]

        return text

    @staticmethod
    def clear_ansi(text: str) -> str:
        import re
        return re.sub(r'\x1b\[[0-9;]*m', '', text)

    def send_prompt(self, prompt: str) -> str:
        cmd = [self.provider.cmd]
        if self.provider.args:
            cmd.extend(self.provider.args)
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
        clean_output = self.clear_ansi(response.stdout)
        clean_output = self.clean_stdout(
            clean_output,
            strip_prefix=self.provider.stdout_strip_prefix,
            slice_range=self.provider.stdout_slice
        )
        return clean_output
