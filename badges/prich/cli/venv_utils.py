import shutil
import subprocess
import venv
from pathlib import Path

import click

from prich.constants import PRICH_DIR_NAME
from prich.core.utils import shorten_path, console_print


def install_python_venv(venv_folder: Path, force: bool = False, venv_type: str = ""):
    if venv_folder.exists() and force:
        if PRICH_DIR_NAME in str(venv_folder):
            console_print(f"Removing existing {venv_type} venv folder...", end="")
            shutil.rmtree(venv_folder)
        else:
            raise click.ClickException(f"{PRICH_DIR_NAME} folder is not part of venv folder path")
        console_print(" [green]done![/green]")
    elif venv_folder.exists():
        console_print("Venv folder found.")
        return
    console_print(f"Installing {venv_type} venv...", end="")
    try:
        builder = venv.EnvBuilder(with_pip=True)
        builder.create(venv_folder)
    except Exception as e:
        console_print()
        raise click.ClickException(f"Failed to install {venv_type} venv: {str(e)}")
    console_print(" [green]done![/green]")


def install_template_python_dependencies(venv_folder: Path, template_folder: Path):
    src_requirements = template_folder / "scripts" / "requirements.txt"
    if src_requirements and src_requirements.exists():
        console_print("Installing dependencies:")
        pip_cmd = venv_folder / "bin/pip"
        if not pip_cmd.exists():
            raise click.ClickException(f"No pip {shorten_path(str(pip_cmd))} found in venv.")
        run_cmd = [pip_cmd, "install", "-r", str(src_requirements)]
        subprocess.run(run_cmd, check=True)
    else:
        console_print("No dependencies to install.")
