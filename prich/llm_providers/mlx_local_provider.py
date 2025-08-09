import os
import click
from pathlib import Path

from prich.core.utils import is_quiet, is_only_final_output
from prich.core.utils import console_print
from prich.models.config_providers import MLXLocalProviderModel
from prich.llm_providers.llm_provider_interface import LLMProvider
from prich.llm_providers.base_optional_provider import LazyOptionalProvider
from rich.console import Console
from contextlib import nullcontext

os.environ["TOKENIZERS_PARALLELISM"] = "false"

console = Console()


class MLXLocalProvider(LLMProvider, LazyOptionalProvider):
    def __init__(self, 
                 name: str,
                 provider: MLXLocalProviderModel
                 ):
        super().__init__()
        self.name = name
        self.provider = provider
        self.model = None
        self.tokenizer = None
        self.client = None
        self.show_response = True

    def _ensure_client(self):
        if self.client:
            return

        self.load = self._lazy_import_from("mlx_lm.utils", "load", pip_name="mlx")
        self.load_tokenizer = self._lazy_import_from("mlx_lm.utils", "load_tokenizer", pip_name="mlx")
        self.make_sampler = self._lazy_import_from("mlx_lm.sample_utils", "make_sampler", pip_name="mlx")
        self.generate = self._lazy_import_from("mlx_lm.generate", "generate", pip_name="mlx")
        self.stream_generate = self._lazy_import_from("mlx_lm.generate", "stream_generate", pip_name="mlx")

        try:
            model_identifier = Path(os.path.expanduser(self.provider.model_path))
            self.model, _ = self.load(str(model_identifier))
            self.tokenizer = self.load_tokenizer(model_identifier)
        except Exception as e:
            raise click.ClickException(f"mlx_local provider failed to load model {self.provider.model_path}: {str(e)}")

        self.client = True

    def send_prompt(self, prompt: str = None, system: str = None, user: str = None) -> str:
        if system or user:
            raise click.ClickException("mxl_local provider requires provider mode")
        self._ensure_client()
        text = []
        try:
            sampler = self.make_sampler(
                temp=self.provider.temp if self.provider.temp is not None else 0.7,
                top_p=self.provider.top_p if self.provider.top_p is not None else 0.9,
                min_p=self.provider.min_p if self.provider.min_p is not None else 0.0,
                min_tokens_to_keep=self.provider.min_tokens_to_keep if self.provider.min_tokens_to_keep is not None else 1,
                top_k=self.provider.top_k if self.provider.top_k is not None else 0
            )
            status = console.status("Thinking...") if not is_quiet() and not is_only_final_output() else nullcontext()
            with status:
                for response in self.stream_generate(
                    model=self.model,
                    tokenizer=self.tokenizer,
                    prompt=prompt,
                    max_tokens=self.provider.max_tokens if self.provider.max_tokens is not None else 512,
                    sampler=sampler
                ):
                    if not is_quiet() and not is_only_final_output():
                        status.stop()
                    text.append(response.text)
                    if self.show_response:
                        console_print(response.text, end='')
                if self.show_response:
                    console_print()
                return ''.join(text).strip()
        except Exception as e:
            raise click.ClickException(f"mlx_local provider error: {str(e)}")
    