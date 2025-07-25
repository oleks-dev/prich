import os
import shutil
import sys
import subprocess
from pathlib import Path
import click
from prich.core.utils import console_print
from prich.models.config_providers import EchoProviderModel, OpenAIProviderModel, STDINConsumerProviderModel, MLXLocalProviderModel
from prich.models.config import SettingsConfig, ConfigModel


@click.command()
@click.option("-g", "--global", "global_init", is_flag=True, help="Initialize ~/.prich/ (global)")
@click.option("--force", is_flag=True, help="Overwrite existing config")
def init(global_init: bool, force: bool):
    """Initialize prich configuration and default venv."""
    prich_dir = Path.home() / ".prich" if global_init else Path.cwd() / ".prich"

    if prich_dir.exists() and not force:
        raise click.ClickException(f"{prich_dir} exists. Use --force to overwrite.")

    os.makedirs(prich_dir / "templates", exist_ok=True)

    default_venv = prich_dir / "venv"
    if not default_venv.exists():
        shutil.rmtree(default_venv)
        subprocess.run([sys.executable, "-m", "venv", str(default_venv)], check=True)

    config = ConfigModel(
        settings=SettingsConfig(
            default_provider="show_prompt",
            provider_assignments=None,
            editor="vi"
        ),
        security=None,
        providers={
            "show_prompt": EchoProviderModel(
                provider_type="echo",
                mode="flat"
            ),
            "openai-gpt4o": OpenAIProviderModel(
                provider_type="openai",
                api_endpoint="https://openai.com/api",
                api_key="${OPENAI_API_KEY}",
                mode="mlchat",
                model="gpt-4o"
            ),
            "mlx-mistral-7b": MLXLocalProviderModel(
                provider_type="mlx_local",
                mode="mistral-instruct",
                model_path="~/.cache/huggingface/hub/models--mlx-community--Mistral-7B-Instruct-v0.3-4bit/snapshots/a4b8f870474b0eb527f466a03fbc187830d271f5",
                max_tokens=3000
            ),
            "qchatcli": STDINConsumerProviderModel(
                provider_type="stdin_consumer",
                mode="flat",
                cmd="q",
                args=["chat", "--no-interactive"]
            ),
            "grok": OpenAIProviderModel(
                provider_type="openai",
                api_endpoint="https://api.x.ai/v1",
                api_key="${GROK_API_KEY}",
                max_tokens=3000,
                mode="mlchat",
                model="grok-3",
                temperature=0.7
            )
        }
    )

    config.save("global" if global_init else "local")

    console_print(f"Initialized [cyan]prich[/cyan] at [green]{prich_dir}[/green]")
