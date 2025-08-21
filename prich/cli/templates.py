import os
import shutil
import yaml
import subprocess
from pathlib import Path
import click
import venv

from prich.core.utils import shorten_home_path
from prich.core.loaders import get_loaded_templates, get_loaded_config, get_loaded_template
from prich.models.template import TemplateModel, VariableDefinition, LLMStep, PromptFields
from prich.core.utils import console_print, is_valid_template_id, get_prich_dir, get_prich_templates_dir

def _download_zip(url: str) -> Path:
    """ Download zip file into temporary file and return path to it """
    import tempfile
    import requests
    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        for chunk in response.iter_content(chunk_size=8192):
            tmp.write(chunk)
        tmp.flush()
        tmp_path = Path(tmp.name)
    return tmp_path

def _extract_zip(path: Path) -> Path:
    """ Extract zip archive into temporary folder and return path of it """
    import zipfile
    import tempfile
    tmp_path = Path(tempfile.mkdtemp())
    with zipfile.ZipFile(path, 'r') as zip_ref:
        zip_ref.extractall(tmp_path)
    return tmp_path

def safe_remove(path: Path):
    """ Remove folder or file if present """
    try:
        if path.is_file() or path.is_symlink():
            path.unlink()
        elif path.is_dir():
            shutil.rmtree(path)
    except FileNotFoundError:
        pass  # Ignore if it doesn't exist

def check_if_dest_present(template_id: str, dest_folder: Path, global_install: bool, force: bool):
    """ Check if dest template folder already present """
    if dest_folder.exists() and not force:
        scope = "global" if global_install else "local"
        raise click.ClickException(
            f"Template '{template_id}' already exists in {scope} directory ({dest_folder}). Use --force to overwrite.")


@click.command("install")
@click.argument("path")
@click.option("--force", is_flag=True, help="Overwrite existing templates")
@click.option("--no-venv", is_flag=True, help="Skip venv setup")
@click.option("-g", "--global", "global_install", is_flag=True, help="Install to ~/.prich/templates")
@click.option("-r", "--remote", "from_remote", is_flag=True, help="Install template from prich-templates GitHub repo")
def template_install(path: str, force: bool, no_venv: bool, global_install: bool, from_remote: bool):
    """Install a template from PATH, zip, or prich-templates."""
    from rich.console import Console
    console = Console()
    templates_dir = get_prich_templates_dir(global_install)
    src_dir = None
    remove_source = False

    if from_remote:
        if not is_valid_template_id(path):
            raise click.ClickException(f"Remote Template ID {path} is not valid.")
        check_if_dest_present(path, templates_dir / path, global_install, force)

        from_url = f"https://raw.githubusercontent.com/oleks-dev/prich-templates/main/dist/{path}.zip"
        try:
            with console.status(f"Downloading {path} from {from_url}..."):
                tmp_zip_file = _download_zip(
                    url = from_url
                )
        except Exception as e:
            safe_remove(tmp_zip_file)
            raise click.ClickException(f"Failed to download template {path} from prich-templates, check if the template is available.")
        try:
            with console.status(f"Extracting..."):
                src_dir = _extract_zip(tmp_zip_file)
                safe_remove(tmp_zip_file)
        except Exception as e:
            safe_remove(tmp_zip_file)
            raise click.ClickException(f"Failed to extract downloaded template {tmp_zip_file}")
        remove_source = True
    elif path.endswith(".zip"):
        template_id = path[:-4]
        check_if_dest_present(template_id, templates_dir / template_id, global_install, force)
        try:
            src_dir = _extract_zip(Path(path))
        except Exception as e:
            safe_remove(src_dir)
            raise click.ClickException(f"Failed to extract template {path}")
        remove_source = True
    else:
        src_dir = Path(path).resolve()
        if not src_dir.is_dir():
            raise click.ClickException(f"Path is not a directory: {path}")

    if not src_dir:
        raise click.ClickException("Failed to load or prepare source dir for template installation.")

    yaml_files = list(src_dir.glob("**/*.yaml"))
    if not yaml_files:
        if remove_source:
            safe_remove(src_dir)
        raise click.ClickException("No template YAML found")

    template_yaml = yaml_files[0]
    template_content = yaml.safe_load(template_yaml.read_text())
    template = TemplateModel(**template_content)
    template_id = template.id
    template_base = templates_dir / template_id
    dest_yaml = template_base / f"{template_id}.yaml"

    check_if_dest_present(template_id, template_base, global_install, force)

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

    if remove_source:
        safe_remove(src_dir)

    if not no_venv and template.venv:
        install_template_venv(template=template, force=force, template_base=template_base)

    console_print(f"Template [green]{template_id}[/green] installed successfully")
    console_print(f"Run: [cyan]prich[/cyan] run [green]{template_id}[/green] --help")

def install_template_venv(template: TemplateModel, template_base: Path = None, force: bool = False):
    if not template_base:
        template_base = Path(template.folder)
    scripts_folder = template_base / "scripts"
    src_requirements = scripts_folder / "requirements.txt"
    if template.venv == "isolated":
        template_venv = scripts_folder / "venv"
        if template_venv.exists() and force:
            console_print(f"Removing existing venv {shorten_home_path(str(template_venv))}...", end="")
            shutil.rmtree(template_venv)
            console_print(" [green]done![/green]")
        if not template_venv.exists():
            console_print(f"Creating folder {shorten_home_path(str(template_venv))}...", end="")
            os.makedirs(template_venv, exist_ok=True)
            console_print(" [green]done![/green]")
            console_print(f"Installing isolated venv...", end="")

            # Install venv
            try:
                builder = venv.EnvBuilder(with_pip=True)
                builder.create(template_venv)
                # Optional Install venv using cmd
                # subprocess.run([sys.executable, "-m", "venv", str(template_venv)], check=True)
            except Exception as e:
                console_print()
                raise click.ClickException(f"Failed to install venv: {str(e)}")
            console_print(" [green]done![/green]")
        if src_requirements.exists():
            console_print("Installing dependencies...")
            pip_cmd = template_venv / "bin/pip"
            if not pip_cmd.exists():
                raise click.ClickException(f"No pip {shorten_home_path(str(pip_cmd))} found in isolated template venv.")
            subprocess.run([str(pip_cmd), "install", "-r", str(src_requirements)], check=True)
        else:
            console_print(f"No dependencies {shorten_home_path(str(src_requirements))} file found in the template.")
        console_print("[green]Done![/green]")
    elif template.venv == "shared":
        prich_dir = get_prich_dir()
        shared_venv = prich_dir / "venv"
        if shared_venv.exists() and force:
            raise click.ClickException(f"Shared venv with --force is not supported as it might break other templates that uses shared venv, if you are sure that you want to do this you can remove {shorten_home_path(str(shared_venv))} folder manually and then execute this command again without --force option flag.")
        if not shared_venv.exists():
            console_print("No shared venv found, installing...")
            try:
                builder = venv.EnvBuilder(with_pip=True)
                builder.create(shared_venv)
            except Exception as e:
                raise click.ClickException(f"Failed to install venv: {e}")
            console_print(f"Shared venv installed: {shorten_home_path(str(shared_venv))}")
        if src_requirements.exists():
            console_print(f"Installing dependencies to shared venv:")
            pip_cmd = shared_venv / "bin/pip"
            if not pip_cmd.exists():
                raise click.ClickException(f"No pip {shorten_home_path(str(pip_cmd))} found in shared venv.")
            subprocess.run([pip_cmd, "install", "-r", str(src_requirements)], check=True)
        else:
            console_print(f"No dependencies {shorten_home_path(str(src_requirements))} file found in the template.")
        console_print("[green]Done![/green]")
    else:
        console_print(f"Template {template.id} doesn't require venv. To setup venv add 'venv: \"isolated\"' or 'venv: \"shared\" into the template and rerun this command.'")


@click.command("venv-install")
@click.argument("template_id")
@click.option("-g", "--global", "global_only", is_flag=True, help="Only global config")
@click.option("-f", "--force", "force", is_flag=True, help="Remove venv and re-install")
def venv_install(template_id, global_only, force):
    """Install venv for Template with python script steps"""
    template = get_loaded_template(template_id)
    install_template_venv(template=template, force=force)

@click.command("show")
@click.argument("template_id")
@click.option("-g", "--global", "global_only", is_flag=True, help="Only global config")
def show_template(template_id, global_only):
    """Show available options for a template."""
    import yaml
    template = get_loaded_template(template_id)
    console_print(f"Template:")
    tpl = yaml.dump(template.model_dump(exclude_none=True), sort_keys=False, indent=2)
    console_print(tpl)

@click.command("create")
@click.argument("template_id")
@click.option("-g", "--global", "global_only", is_flag=True, default=False, help="Create global template")
@click.option("-e", "--edit", "edit", is_flag=True, default=False, help="Open created template yaml file in editor")
def create_template(template_id: str, global_only: bool, edit: bool):
    """Create new Template based on basic example template."""
    example_template = TemplateModel(
        id=template_id,
        name=template_id.replace("_", " ").replace("-", " ").title(),
        description="Example template - Generate text about specified topic",
        version="1.0",
        tags=["example", "writer"],
        steps=[
            LLMStep(
                name="Ask to generate text",
                type="llm",
                prompt=PromptFields(
                    system="You are {{ role }}",
                    user="Generate text about {{ topic }}"
                )
            )
        ],
        variables=[
            VariableDefinition(
                name="role",
                cli_option="--role",
                description="Role of the Assistant",
                required=False,
                default="article writer",
                type="str"
            ),
            VariableDefinition(
                name="topic",
                cli_option="--topic",
                description="Generate text about Topic",
                required=False,
                default="short brief about LLM usage",
                type="str"
            )
        ]
    )

    config, _ = get_loaded_config()
    installed_templates = get_loaded_templates()
    if template_id in [template.id for template in installed_templates]:
        raise click.ClickException(f"Template {template_id} already exists.")
    if not is_valid_template_id(template_id):
        raise click.ClickException(f"Template {template_id} is not correct, please use only lowercase letters, numbers, hyphen, and optional underscore characters.")
    template_dir = get_prich_templates_dir(global_only) / template_id
    if template_dir.exists():
        raise click.ClickException(f"Template {template_id} folder {template_dir} already exists.")
    template_dir.mkdir(parents=True, exist_ok=False)
    editor_cmd = config.settings.editor
    if not editor_cmd:
        raise click.ClickException(f"Default editor is not set, add settings.editor into config.")
    template_file = template_dir / f"{template_id}.yaml"
    template_file.write_text(yaml.safe_dump(example_template.model_dump(exclude_none=True), indent=2, sort_keys=False))
    console_print(f"Template {template_id} created in {template_file}")
    console_print()
    console_print(f"You can try to run it or modify as you need:")
    console_print(f"* Execute with default values: [green]prich run {template_id}[/green]")
    console_print(f"* Execute with custom values: [green]prich run {template_id} --role journalist --topic \"Large Language Models in the modern data science\"[/green]")
    console_print(f"* Execute with custom value: [green]prich run {template_id} --topic \"Large Language Models usage in CLI tools\"[/green]")
    if edit:
        result = subprocess.run([editor_cmd, template_file], check=True)
        if result.returncode != 0:
            raise click.ClickException(f"Editor returned error code {result.returncode} during opening template {template_id}.")
