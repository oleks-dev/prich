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
            )
        }
    )

    config.save("global" if global_init else "local")

    console_print(f"Initialized [cyan]prich[/cyan] at [green]{prich_dir}[/green]")
