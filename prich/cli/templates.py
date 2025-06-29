import os
import shutil
import yaml
import subprocess
from pathlib import Path
import click
import venv

from prich.core.loaders import get_loaded_templates, get_loaded_config, get_loaded_template
from prich.models.template import TemplateModel
from prich.core.utils import console_print, is_valid_template_name, get_prich_dir


@click.command("install")
@click.argument("path")
@click.option("--force", is_flag=True, help="Overwrite existing templates")
# @click.option("--no-yaml", is_flag=True, help="Skip YAML template copy/replace")
@click.option("--no-venv", is_flag=True, help="Skip venv setup")
@click.option("-g", "--global", "global_install", is_flag=True, help="Install to ~/.prich/templates")
def template_install(path: str, force: bool, no_venv: bool, global_install: bool):
    """Install a template from PATH."""
    src_dir = Path(path).resolve()
    if not src_dir.is_dir():
        raise click.ClickException(f"Path is not a directory: {path}")

    prich_dir = Path.home() / ".prich" if global_install else Path.cwd() / ".prich"
    templates_dir = prich_dir / "templates"
    yaml_files = list(src_dir.glob("*.yaml"))
    if not yaml_files:
        raise click.ClickException("No template YAML found")

    template_yaml = yaml_files[0]
    template_content = yaml.safe_load(template_yaml.read_text())
    template = TemplateModel(**template_content)
    template_name = template.name
    template_base = templates_dir / template_name
    dest_yaml = template_base / f"{template_name}.yaml"

    if dest_yaml.exists() and not force:
        scope = "global" if global_install else "local"
        raise click.ClickException(f"Template '{template_name}' already exists in {scope} directory ({dest_yaml}). Use --force to overwrite.")

    os.makedirs(template_base, exist_ok=True)
    # if not no_yaml:
    shutil.copy(template_yaml, dest_yaml)

    src_preprocess = src_dir / "preprocess"
    if src_preprocess.exists():
        console_print("Setup Preprocess:")
        dest_preprocess = template_base / "preprocess"
        os.makedirs(dest_preprocess, exist_ok=True)
        console_print("Copying...", end="")
        for script in src_preprocess.glob("*"):
            dest_script = dest_preprocess / script.name
            console_print(f" {script.name}", end="")
            shutil.copy(script, dest_script)
            # Set 755 to shell scripts
            if str(script).endswith(".sh"):
                console_print(f" 755", end="")
                dest_script.chmod(0o755)
        console_print(" [green]done![/green]")

    if not no_venv and template.preprocess and template.preprocess.venv:
        install_template_venv(template, template_base, force)

    console_print(f"Template [green]{template_name}[/green] installed successfully")
    console_print(f"Run: [cyan]prich[/cyan] run [green]{template_name}[/green] --help")

def install_template_venv(template: TemplateModel, template_base: Path, force: bool = False):
    console_print("Setup venv:")
    preprocess_folder = template_base / "preprocess"
    src_requirements = preprocess_folder / "requirements.txt"
    src_setup_venv = preprocess_folder / "setup_venv.sh"
    if src_requirements.exists() or src_setup_venv.exists():
        isolated = template.preprocess.venv == "isolated"
        if isolated:
            template_venv = preprocess_folder / "venv"
            if template_venv.exists() and force:
                console_print(f"Removing existing venv {str(template_venv)}...", end="")
                shutil.rmtree(template_venv)
                console_print(" [green]done![/green]")
            console_print(f"Creating folder {str(template_venv)}...", end="")
            os.makedirs(template_venv, exist_ok=True)
            console_print(" [green]done![/green]")
            if src_setup_venv.exists():
                console_print(f"Installing {str(src_setup_venv)}...", end="")
                console_print(f"Shell {str(src_setup_venv)} file content:")
                console_print(src_setup_venv.read_text())
                selection = input("Accept execution [y/n]?:")
                if selection.lower() != "y":
                    raise click.ClickException("No permission granted, venv installation terminated.")
                subprocess.run([str(src_setup_venv), str(template_venv)], check=True)
                console_print(" [green]done![/green]")
            elif src_requirements.exists():
                console_print(f"Installing isolated venv...", end="")

                # Install venv
                builder = venv.EnvBuilder(with_pip=True)
                builder.create(template_venv)
                # Optional Install venv using cmd
                # subprocess.run([sys.executable, "-m", "venv", str(template_venv)], check=True)

                console_print(" [green]done![/green]")
                console_print(f"Installing dependencies...")
                pip_cmd = str(template_venv / "bin/pip")
                subprocess.run([pip_cmd, "install", "-r", str(src_requirements)], check=True)
                console_print("[green]Done![/green]")
        else:
            console_print(f"Installing dependencies to shared venv:")
            prich_dir = get_prich_dir()
            pip_cmd = prich_dir / "venv" / "bin/pip"
            if not pip_cmd.exists():
                raise click.ClickException(f"No pip {str(pip_cmd)} found in shared venv.")
            subprocess.run([pip_cmd, "install", "-r", str(src_requirements)], check=True)
            console_print("[green]Done![/green]")


@click.command("install-venv")
@click.argument("template_name")
@click.option("-g", "--global", "global_only", is_flag=True, help="Only global config")
@click.option("-f", "--force", "force", is_flag=True, help="Remove venv and re-install")
def install_venv(template_name, global_only, force):
    """Install venv for Template with python preprocess steps"""
    template = get_loaded_template(template_name)
    install_template_venv(template, force)

@click.command("show")
@click.argument("template_name")
@click.option("-g", "--global", "global_only", is_flag=True, help="Only global config")
def show_template(template_name, global_only):
    """Show available options for a template."""
    template = get_loaded_template(template_name)
    details = [f"[bold]Template[/bold]: [green]{template.name}[/green] - [cyan]{template.description}[/cyan]",
               f"[bold]Version[/bold]: [cyan]{template.version}[/cyan]",
               f"[bold]Tags[/bold]: [cyan]{', '.join(template.tags)}[/cyan]", "\n[bold]Variables[/bold]:"]
    for var in template.variables:
        details.append(f"-  [green]{var.name or var.cli_option}[/green] (default [blue]{var.default}[/blue]): {var.description}")
    details.append("\n[bold]Prompt[/bold]:")
    if template.template.system:
        details.append(f"- System:\n[blue]{template.template.system}[/blue]")
    if template.template.user:
        details.append(f"- User:\n[blue]{template.template.user}[/blue]")
    if template.template.prompt:
        details.append(f"- Text:\n[blue]{template.template.prompt}[/blue]")
    if template.preprocess:
        details.append(f"\n[bold]Preprocess[/bold]:")
        if template.preprocess.venv:
            details.append(f"Python venv: {template.preprocess.venv}")
        for step in template.preprocess.steps:
            details.append(f"- [green]{step.call} {' '.join(step.args)}[/green] type: {step.type}, output: {step.output_variable}")
    console_print('  \n'.join(details))

@click.command("create")
@click.argument("template_name")
@click.option("-g", "--global", "global_only", is_flag=True, help="Only global config")
def create_template(template_name, global_only):
    """Create new template"""
    template_tpl = f"""name: {template_name}
schema_version: "1.0"
version: "1.0"
description: "Example description"
tags: ["personal"]
template:
  system: |
    You are {{{{ purpose }}}}
  user: |
    Based on {{{{ topic }}}}
variables:
  - name: purpose
    description: "Assistant purpose"
    required: true
    type: str
  - name: topic
    description: "Topic to describe"
    required: true
    type: str
"""

    config, _ = get_loaded_config()
    installed_templates = get_loaded_templates()
    if template_name in [tpl.name for tpl in installed_templates]:
        raise click.ClickException(f"Template {template_name} is already exists.")
    if not is_valid_template_name(template_name):
        raise click.ClickException(f"Template {template_name} is not correct, please use only lowercase letters, numbers, hyphen, and optional underscore characters.")
    prich_dir = (Path.cwd() if not global_only else Path.home()) / ".prich"
    template_dir = prich_dir / "templates" / template_name
    if template_dir.exists():
        raise click.ClickException(f"Template {template_name} folder {template_dir} already exists.")
    template_dir.mkdir(parents=True, exist_ok=False)
    editor_cmd = config.defaults.editor
    if not editor_cmd:
        raise click.ClickException(f"Default editor is not set, add defaults.editor into config.")
    template_file = template_dir / f"{template_name}.yaml"
    template_file.write_text(template_tpl)
    result = subprocess.run([editor_cmd, template_file], check=True)
    if result.returncode == 0:
        console_print(f"Template {template_name} created in {template_file}")
    else:
        raise click.ClickException(f"Editor returned error code {result.returncode} during template {template_name} creation.")
