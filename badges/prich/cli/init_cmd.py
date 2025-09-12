import os
import shutil
import subprocess
import sys
import venv
import click
from prich.constants import PRICH_DIR_NAME
from prich.core.utils import console_print, get_prich_dir
from prich.models.config_providers import EchoProviderModel
from prich.models.config import SettingsConfig, ConfigModel, ProviderModeModel


@click.command()
@click.option("-g", "--global", "global_init", is_flag=True, help=f"Initialize ~/{PRICH_DIR_NAME}/ (global)")
@click.option("--force", is_flag=True, help="Overwrite existing config")
def init(global_init: bool, force: bool):
    """Initialize prich configuration and default venv."""
    prich_dir = get_prich_dir(global_init)

    if prich_dir.exists() and not force:
        raise click.ClickException(f"{prich_dir} exists. Use --force to overwrite.")

    os.makedirs(prich_dir / "templates", exist_ok=True)

    default_venv = prich_dir / "venv"
    if force:
        # for safety, ensure that we remove only related folder
        if PRICH_DIR_NAME in str(default_venv):
            shutil.rmtree(default_venv, ignore_errors=True)
        else:
            raise click.ClickException(f"{PRICH_DIR_NAME} folder is not part of venv folder path")
    if not default_venv.exists():
        builder = venv.EnvBuilder(with_pip=True)
        builder.create(default_venv)
        # replaced with venv lib
        # subprocess.run([sys.executable, "-m", "venv", str(default_venv)], check=True)

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
        },
        provider_modes=[
            ProviderModeModel(name="plain", prompt="{% if instructions %}{{ instructions }}\n{% endif %}{{ input }}"),
            ProviderModeModel(name="flat",
                              prompt="{% if instructions %}### System:\n{{ instructions }}\n\n{% endif %}### User:\n{{ input }}\n\n### Assistant:"),
            # ProviderModeModel(name="mistral-instruct", prompt="""<s>[INST]\n{% if instructions %}{{ instructions }}\n\n{% endif %}{{ input }}\n[/INST]"""),
            # ProviderModeModel(name="llama2-chat", prompt="""<s>[INST]\n{% if instructions %}{{ instructions }}\n\n{% endif %}{{ input }}\n[/INST]"""),
            # ProviderModeModel(name="anthropic", prompt="""Human: {% if instructions %}{{ instructions }}\n\n{% endif %}{{ input }}\n\nAssistant:"""),
            # ProviderModeModel(name="chatml", prompt="""[{% if instructions %}{"role": "system", "content": "{{ instructions }}" },{% endif %}{"role": "user", "content": "{{ input }}" }]""")
        ]
    )

    config.save("global" if global_init else "local")

    console_print(f"Initialized [cyan]prich[/cyan] at [green]{prich_dir}[/green]")


@click.command(hidden=True)
@click.argument("shell", type=click.Choice(["bash", "zsh", "fish"]))
def completion(shell: str):
    """
    Generate shell completion script for BASH, ZSH, or FISH.

    Example:
      prich completion zsh > ~/.zfunc/_prich
    """
    env = os.environ.copy()
    env["_PRICH_COMPLETE"] = f"{shell}_source"

    try:
        # Run this same CLI with modified environment
        subprocess.run(
            [sys.argv[0]],        # re-invoke current CLI script
            env=env,
            text=True,
            check=True                  # raise error if prich fails
        )
    except subprocess.CalledProcessError as e:
        click.echo(f"Error generating completion script: {e}", err=True)
        sys.exit(e.returncode)
