import os
import sys
import yaml
import subprocess
from pathlib import Path
import click
from rich.console import Console

console = Console()

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
        subprocess.run([sys.executable, "-m", "venv", str(default_venv)], check=True)

    config_path = prich_dir / "config.yaml"
    config = {
        "schema_version": 1.0,
        "editor": "vim",
        "defaults": {
            "provider": "show_prompt",
            "provider_assignments": {}
        },
        "providers": {
            "grok": {
                "api_endpoint": "https://api.x.ai/v1",
                "api_key": "${PRICH_XAI_API_KEY}",
                "max_tokens": 3000,
                "mode": "mlchat",
                "model": "grok-3",
                "provider_type": "openai",
                "temperature": 0.7
            },
            "mlx-mistral-7b": {
                "mode": "mistral-instruct",
                "model_path": "~/.cache/huggingface/hub/models--mlx-community--Mistral-7B-Instruct-v0.3-4bit/snapshots/a4b8f870474b0eb527f466a03fbc187830d271f5",
                "max_tokens": 3000,
                "provider_type": "MLXLocal",
            },
            "openai-gpt4o": {
                "api_endpoint": "https://openai.com/api",
                "api_key": "${PRICH_OPENAI_API_KEY}",
                "mode": "mlchat",
                "model": "gpt-4o",
                "provider_type": "openai"
            },
            "qchatcli": {
                "mode": "flat",
                "options": ["-v"],
                "provider_type": "qchatcli"
            },
            "show_prompt": {
                "mode": "flat",
                "provider_type": "echo"
            }
        },
        "security": {
            "allow_python_injection": False,
            "require_venv_for_python": True
        }
    }

    with open(config_path, "w") as f:
        yaml.safe_dump(config, f)

    console.print(f"Initialized [cyan]prich[/cyan] at [green]{prich_dir}[/green]")
