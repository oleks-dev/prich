import subprocess
import click
from prich.llm_providers.llm_provider_interface import LLMProvider
from prich.models.config_providers import STDINConsumerProviderModel

class STDINConsumerProvider(LLMProvider):
    def __init__(self, name: str, provider: STDINConsumerProviderModel):
        self.provider = provider
        self.name = name
        self.show_response: bool = False

    def run_and_capture(self, cmd):
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1  # line-buffered
        )

        output_lines = []

        for line in proc.stdout:
            if self.show_response:
                print(line, end='')  # live output to terminal
            output_lines.append(line)  # also capture

        proc.wait()
        full_output = ''.join(output_lines)
        return full_output, proc.returncode

    def send_prompt(self, prompt: str) -> str:
        cmd = [self.provider.cmd]
        if self.provider.args:
            cmd.extend(self.provider.args)
        try:
            response, _ = self.run_and_capture(cmd)
            print()
        except Exception as e:
            raise click.ClickException(f"STDIN consumer provider error: {str(e)}")
        return response if response else ""
