import os
import shutil
import sys
import subprocess
import click
from prich.core.utils import console_print, get_prich_dir
from prich.models.config_providers import EchoProviderModel
from prich.models.config import SettingsConfig, ConfigModel, ProviderModeModel


@click.command()
@click.option("-g", "--global", "global_init", is_flag=True, help="Initialize ~/.prich/ (global)")
@click.option("--force", is_flag=True, help="Overwrite existing config")
def init(global_init: bool, force: bool):
    """Initialize prich configuration and default venv."""
    prich_dir = get_prich_dir(global_init)

    if prich_dir.exists() and not force:
        raise click.ClickException(f"{prich_dir} exists. Use --force to overwrite.")

    os.makedirs(prich_dir / "templates", exist_ok=True)

    default_venv = prich_dir / "venv"
    if force:
        shutil.rmtree(default_venv, ignore_errors=True)
    if not default_venv.exists():
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
        },
        provider_modes=[
            ProviderModeModel(name="plain", prompt="{{ prompt }}"),
            ProviderModeModel(name="flat", prompt="""{% if system %}### System:\n{{ system }}\n\n{% endif %}### User:\n{{ user }}\n\n### Assistant:"""),
            ProviderModeModel(name="mistral-instruct", prompt="""<s>[INST]\n{% if system %}{{ system }}\n\n{% endif %}{{ user }}\n[/INST]"""),
            ProviderModeModel(name="llama2-chat", prompt="""<s>[INST]\n{% if system %}{{ system }}\n\n{% endif %}{{ user }}\n[/INST]"""),
            ProviderModeModel(name="anthropic", prompt="""Human: {% if system %}{{ system }}\n\n{% endif %}{{ user }}\n\nAssistant:"""),
            ProviderModeModel(name="chatml", prompt="""[{% if system %}{"role": "system", "content": "{{ system }}" },{% endif %}{"role": "user", "content": "{{ user }}" }]""")
        ]
    )

    config.save("global" if global_init else "local")

    console_print(f"Initialized [cyan]prich[/cyan] at [green]{prich_dir}[/green]")
