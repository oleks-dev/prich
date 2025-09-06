import os
from pathlib import Path
import click
from prich.constants import PRICH_DIR_NAME
from prich.models.template import CommandStep, PythonStep
from prich.core.file_scope import classify_path
from prich.core.loaders import find_template_files, load_template_model, get_env_vars
from prich.core.utils import console_print, shorten_path, get_prich_dir, is_just_filename, get_cwd_dir, get_home_dir


@click.command(name="validate")
@click.option("--id", "template_id", type=str, help="Template ID to validate")
@click.option("--file", "validate_file", type=Path, help="Template YAML file to validate")
@click.option("-g", "--global", "global_only", is_flag=True, help="Validate only global templates")
@click.option("-l", "--local", "local_only", is_flag=True, help="Validate only local templates")
def validate_templates(template_id: str, validate_file: Path, global_only: bool, local_only: bool):
    """Validate Templates by checking yaml template schema"""
    import sys
    if global_only and local_only:
        raise click.ClickException("Use only one local or global option, use: 'prich validate -g' or 'prich validate -l'")

    if validate_file and (global_only or local_only or template_id):
        raise click.ClickException(f"When YAML file is selected it doesn't combine with local, global, or id options, use: 'prich validate --file ./{PRICH_DIR_NAME}/templates/test-template/test-template.yaml'")

    if validate_file and not validate_file.exists():
        raise click.ClickException(f"Failed to find {validate_file} template file.")

    # Load Template Files
    template_files = []
    if validate_file:
        # Load one template file
        template_files = [validate_file]
    else:
        # Prepare Template Files Path
        file_paths = [get_cwd_dir(), get_home_dir()]
        if global_only:
            file_paths.remove(get_cwd_dir())
        if local_only:
            file_paths.remove(get_home_dir())
        for base_dir in file_paths:
            template_files.extend(find_template_files(base_dir))

    if template_id:
        template_files = [tpl for tpl in template_files if tpl.name == f"{str(template_id)}.yaml"]
        if not template_files:
            raise click.ClickException(f"Failed to find template with id: {template_id}")

    if not template_files:
        console_print("[yellow]No Templates found.[/yellow]")
        return

    template_files.sort()

    failures_found = False
    for template_file in template_files:
        try:
            template = load_template_model(template_file)
            console_print(f"- {template.id} [dim]({template.source.value}) {shorten_path(str(template_file))}[/dim]: [green]is valid[/green]")
            if template.venv in ["isolated", "shared"]:
                venv_folder = (Path(template.folder) / "scripts") if template.venv == "isolated" else get_prich_dir() / "venv"
                if not venv_folder.exists():
                    console_print(f"  [red]Failed to find {template.venv} venv at {shorten_path(str(venv_folder))}. Install it by running 'prich venv-install {template.id}'.[/red]")
                    failures_found = True
            idx = 0
            for step in template.steps:
                idx += 1
                if type(step) in [CommandStep, PythonStep]:
                    call_file = Path(step.call)
                    if not call_file.exists() and not (Path(template.folder) / "scripts" / call_file).exists() and type(step) == CommandStep:
                        env_vars = get_env_vars()
                        if env_vars.get("PATH"):
                            paths = env_vars.get("PATH").split(":")
                            if paths and is_just_filename(step.call):
                                for path in paths:
                                    if (path / Path(step.call)).exists():
                                        call_file = path / Path(step.call)
                                        break
                    if call_file.exists() and not os.access(call_file, os.X_OK) and type(step) == CommandStep:
                        console_print(f"  [red]The call command {shorten_path(str(call_file))} file is not executable in step #{idx} {step.name}[/red]")
                        failures_found = True
                    elif not call_file.exists() and not (Path(template.folder) / "scripts" / call_file).exists():
                        if is_just_filename(call_file):
                            full_path = str(Path(template.folder) / "scripts" / call_file)
                        else:
                            full_path = str(call_file)
                        console_print(f"  [red]Failed to find call {step.type} file {shorten_path(full_path)} for step #{idx} {step.name}")

        except click.ClickException as e:
            failures_found = True
            template_source = classify_path(template_file)
            console_print(f"- [dim]({template_source.value}) {shorten_path(str(template_file))}[/dim]: [red]is not valid[/red]\n  [red]{e.message.replace(f' from {template_file}', '')}[/red]")
    if failures_found:
        sys.exit(1)
