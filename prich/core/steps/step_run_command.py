from pathlib import Path
from typing import Dict, Tuple

import click
from prich.core.loaders import get_env_vars
from prich.core.utils import get_prich_dir, is_just_filename, is_verbose, console_print, is_quiet, is_only_final_output
from prich.models.template import TemplateModel, PythonStep, CommandStep
from prich.core.variable_utils import expand_vars


def run_command_step(template: TemplateModel, step: PythonStep | CommandStep, variables: Dict[str, any]) -> Tuple[str, int]:
    import subprocess
    from rich.console import Console
    console = Console()

    method = step.call
    try:
        template_dir = Path(template.folder)
    except Exception as e:
        raise click.ClickException(f"Template folder was not detected properly: {e}")

    if type(step) == PythonStep and step.type == "python":
        method_path = template_dir / "scripts" / method
        if not method_path.exists():
            raise click.ClickException(f"Python script not found: {method_path}")
        if not method.endswith(".py"):
            raise click.ClickException(f"Python script file should end with .py: {method_path}")

        if template.venv in ["shared", "isolated"]:
            if template.venv == "shared":
                venv_path = get_prich_dir() / "venv"
            else:
                venv_path = template_dir / "scripts" / "venv"
            python_path = venv_path / "bin" / "python"
            if not python_path.exists():
                raise click.ClickException(f"{template.venv.capitalize()} venv python not found: {python_path}")
            cmd = [str(python_path), str(method_path)]
        elif template.venv is None:
            cmd = ["python", str(method_path)]
        else:
            raise click.ClickException(f"Python script venv {template.venv} is not supported.")
    elif type(step) == CommandStep and step.type == "command":
        if is_just_filename(method) and (template_dir / "scripts" / method).exists():
            cmd = [str(template_dir / "scripts" / method)]
        else:
            cmd = [method]
    else:
        raise click.ClickException(f"Template command step type {step.type} is not supported.")

    # Inputs / Variables List
    expanded_args = expand_vars(step.args, variables=variables, env_vars=get_env_vars())
    [cmd.append(arg) for arg in expanded_args if arg is not None and arg != ""]

    try:
        if is_verbose():
            console_print(f"[dim]Execute {step.type} [green]{' '.join(cmd)}[/green][/dim]")
        if not is_quiet() and not is_only_final_output():
            with console.status("Processing..."):
                result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=False, env=get_env_vars())
        else:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=False, env=get_env_vars())
        return result.stdout, result.returncode
    except Exception as e:
        raise click.ClickException(f"Unexpected error in {method}: {str(e)}")
