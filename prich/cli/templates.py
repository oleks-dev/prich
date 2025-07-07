import os
import shutil
import yaml
import subprocess
from pathlib import Path
import click
import venv

from prich.core.loaders import get_loaded_templates, get_loaded_config, get_loaded_template
from prich.models.template import TemplateModel, VariableDefinition, LLMStep, PromptFields
from prich.core.utils import console_print, is_valid_template_name, get_prich_dir, get_prich_templates_dir


@click.command("install")
@click.argument("path")
@click.option("--force", is_flag=True, help="Overwrite existing templates")
@click.option("--no-venv", is_flag=True, help="Skip venv setup")
@click.option("-g", "--global", "global_install", is_flag=True, help="Install to ~/.prich/templates")
def template_install(path: str, force: bool, no_venv: bool, global_install: bool):
    """Install a template from PATH."""
    src_dir = Path(path).resolve()
    if not src_dir.is_dir():
        raise click.ClickException(f"Path is not a directory: {path}")

    templates_dir = get_prich_templates_dir()
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

    src_scripts = src_dir / "scripts"
    if src_scripts.exists():
        console_print("Setup Scripts:")
        dest_scripts = template_base / "scripts"
        os.makedirs(dest_scripts, exist_ok=True)
        console_print("Copying...")
        for script in src_scripts.glob("*"):
            dest_script = dest_scripts / script.name
            console_print(f"  - {script.name}")
            shutil.copy(script, dest_script)
            # Set 755 to shell scripts
            if str(script).endswith(".sh"):
                response = input(f"Set {script} as executable [y/n]? ")
                if response.lower() in ['y', 'yes']:
                    console_print(f"Running chmod {script} 755")
                    dest_script.chmod(0o755)
        console_print("[green]Done![/green]")

    if not no_venv and template.venv:
        install_template_venv(template, template_base, force)

    console_print(f"Template [green]{template_name}[/green] installed successfully")
    console_print(f"Run: [cyan]prich[/cyan] run [green]{template_name}[/green] --help")

def install_template_venv(template: TemplateModel, template_base: Path, force: bool = False):
    console_print("Setup venv:")
    scripts_folder = template_base / "scripts"
    src_requirements = scripts_folder / "requirements.txt"
    src_setup_venv = scripts_folder / "setup_venv.sh"
    if src_requirements.exists() or src_setup_venv.exists():
        isolated = template.venv == "isolated"
        if isolated:
            template_venv = scripts_folder / "venv"
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


@click.command("venv-install")
@click.argument("template_name")
@click.option("-g", "--global", "global_only", is_flag=True, help="Only global config")
@click.option("-f", "--force", "force", is_flag=True, help="Remove venv and re-install")
def venv_install(template_name, global_only, force):
    """Install venv for Template with python script steps"""
    template = get_loaded_template(template_name)
    install_template_venv(template, force)

@click.command("show")
@click.argument("template_name")
@click.option("-g", "--global", "global_only", is_flag=True, help="Only global config")
def show_template(template_name, global_only):
    """Show available options for a template."""
    import yaml
    template = get_loaded_template(template_name)
    console_print(f"[bold]Template[/bold]:")
    tpl = yaml.dump(template.model_dump(exclude_none=True), sort_keys=False, indent=2)
    console_print(tpl)

@click.command("create")
@click.argument("template_name")
@click.option("-g", "--global", "global_only", is_flag=True, default=False, help="Only global template")
@click.option("-l", "--local", "local_only", is_flag=True, default=False, help="Only local template")
def create_template(template_name, global_only, local_only):
    """Create new Template based on basic example template."""
    example_template = TemplateModel(
        name=template_name,
        description="Example description",
        version="1.0",
        tags=["example"],
        steps=[
            LLMStep(
                name="LLM Request",
                type="llm",
                prompt=PromptFields(
                    system="You are {{ actor }}",
                    user="Based on {{ topic }}"
                )
            )
        ],
        variables=[
            VariableDefinition(
                name="actor",
                description="Role of the Assistant",
                required=True,
                type="str"
            ),
            VariableDefinition(
                name="topic",
                description="Topic to describe",
                required=True,
                type="str"
            )
        ]
    )

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
    editor_cmd = config.settings.editor
    if not editor_cmd:
        raise click.ClickException(f"Default editor is not set, add settings.editor into config.")
    template_file = template_dir / f"{template_name}.yaml"
    template_file.write_text(yaml.safe_dump(example_template.model_dump()))
    result = subprocess.run([editor_cmd, template_file], check=True)
    if result.returncode == 0:
        console_print(f"Template {template_name} created in {template_file}")
    else:
        raise click.ClickException(f"Editor returned error code {result.returncode} during template {template_name} creation.")
