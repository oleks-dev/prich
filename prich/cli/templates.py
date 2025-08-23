import os
import shutil
import tempfile

import yaml
import subprocess
from pathlib import Path
import click

from prich.core.loaders import get_loaded_templates, get_loaded_config, get_loaded_template
from prich.core.utils import console_print, is_valid_template_id, get_prich_dir, get_prich_templates_dir, shorten_path
from prich.cli.venv_utils import install_template_python_dependencies
from prich.models.template import TemplateModel, VariableDefinition, LLMStep, PromptFields

def _download_zip(url: str) -> Path:
    """ Download zip file into temporary file and return path to it """
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
        return _download_file(url, tmp.name)

def _download_file(url: str, dest_file: str | Path) -> Path:
    import requests
    if type(dest_file) == str:
        dest_file = Path(dest_file)
    dest_file.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(dest_file, "wb") as save_to_file:
        for chunk in response.iter_content(chunk_size=8192):
            save_to_file.write(chunk)
        save_to_file.flush()
    return dest_file

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
            f"Template '{template_id}' already exists in {scope} directory ({shorten_path(str(dest_folder))}). Use --force to overwrite.")


@click.command("install")
@click.argument("path")
@click.option("--force", is_flag=True, help="Overwrite existing templates")
@click.option("--no-venv", is_flag=True, help="Skip venv setup")
@click.option("-g", "--global", "global_install", is_flag=True, help="Install to ~/.prich/templates")
@click.option("-r", "--remote", "from_remote", is_flag=True, help="Install template from prich-templates GitHub repo or zip URL")
def template_install(path: str, force: bool, no_venv: bool, global_install: bool, from_remote: bool):
    """Install a template from PATH, zip, or prich-templates."""
    from rich.console import Console
    from prich.cli.template_utils import get_remote_prich_templates_manifest
    console = Console()
    templates_dir = get_prich_templates_dir(global_install)
    src_dir = None
    remove_source = False

    if from_remote:
        if path.startswith("http://") or path.startswith("https://"):
            if not path.endswith(".zip"):
                raise click.ClickException(f"Remote URL should point to a zip file.")
            from_url = path

            try:
                tmp_zip_file = None
                with console.status(f"Downloading {path} from {from_url}..."):
                    tmp_zip_file = _download_zip(
                        url=from_url
                    )
            except Exception as e:
                if tmp_zip_file and tmp_zip_file.exists():
                    safe_remove(tmp_zip_file)
                raise click.ClickException(
                    f"Failed to download template {path}, check if the template is available in the remote.")
            path = str(tmp_zip_file)

        else:
            if not is_valid_template_id(path):
                raise click.ClickException(f"Remote Template ID {path} is not valid.")
            check_if_dest_present(path, templates_dir / path, global_install, force)

            with console.status("Fetching templates manifest..."):
                templates_manifest = get_remote_prich_templates_manifest()
            if not path in [x.id for x in templates_manifest.templates]:
                raise click.ClickException(f"Remote Template ID {path} not found in the repository {templates_manifest.repository}.")
            template_to_install = [x for x in templates_manifest.templates if x.id == path][0]
            tmp_path = Path(tempfile.mkdtemp())
            with console.status("Downloading..."):
                for file_to_download in template_to_install.files:
                    remote_templates_repo_path = "https://raw.githubusercontent.com/oleks-dev/prich-templates/refs/heads/main/templates/"
                    download_to_file = tmp_path / file_to_download
                    _download_file(f"{remote_templates_repo_path}{file_to_download}", download_to_file)
            # TODO: drop folder name from manifest files
            path = str(tmp_path)

        remove_source = True

    if path.endswith(".zip"):
        try:
            with console.status(f"Extracting..."):
                src_dir = _extract_zip(Path(path))
        except Exception as e:
            safe_remove(src_dir)
            raise click.ClickException(f"Failed to extract template {path}")
        remove_source = True

    else:
        try:
            src_dir = Path(path).resolve()
        except Exception as e:
            src_dir = None
        if (src_dir and not src_dir.is_dir()) or not src_dir:
            raise click.ClickException(f"Path is not a directory: {path}")

    if not src_dir:
        raise click.ClickException("Failed to load or prepare source dir for template installation.")

    yaml_files = list(src_dir.glob("**/*.yaml"))
    if not yaml_files:
        if remove_source:
            safe_remove(src_dir)
        raise click.ClickException("No template YAML found")

    template = None
    template_id = None
    template_folder = None
    yaml_files_issues = []
    for template_yaml in yaml_files:
        try:
            template_content = yaml.safe_load(template_yaml.read_text())
            if not template_content:
                yaml_files_issues.append(f"File {shorten_path(str(template_yaml))} is empty")
                continue
            template = TemplateModel(**template_content)
            template_id = template.id
            template_folder = templates_dir / template_id
            break
        except Exception as e:
            yaml_files_issues.append(f"File {shorten_path(str(template_yaml))}: {str(e)}")
    if not template and not template_id and not template_folder:
        yaml_error_list = "\n ".join(yaml_files_issues)
        raise click.ClickException(f"Failed to load template:\n{yaml_error_list}")

    check_if_dest_present(template_id, template_folder, global_install, force)

    console_print(f"Installing template to {shorten_path(str(template_folder))}:")
    os.makedirs(template_folder, exist_ok=True)
    shutil.copytree(src_dir, template_folder, dirs_exist_ok=True)
    template_files = list(template_folder.glob("**/*"))
    template_files.sort()
    for template_file in template_files:
        console_print(f" + {str(template_file).replace(str(template_folder), '.')}")

    sh_files = list((template_folder / "scripts").glob("**/*.sh"))
    if sh_files:
        console_print("Setup Scripts:")
        for sh_file in sh_files:
            response = input(f"Set {str(sh_file).replace(str(template_folder), '')} as 755 executable [y/n]? ")
            if response.lower() in ['y', 'yes']:
                console_print(f"Running chmod 755...", end='')
                sh_file.chmod(0o755)
                if sh_file.lchmod(0o755):
                    console_print(f" done.")
                else:
                    console_print(f" failed.")
            else:
                console_print("Skipped chmod 755.")

    console_print("[green]Done![/green]")

    if remove_source:
        safe_remove(src_dir)

    if not no_venv and template.venv:
        install_template_venv(template=template, force=force, template_base=template_folder)

    console_print()
    console_print(f"Template [green]{template_id}[/green] installed successfully.")
    console_print(f"Run: [cyan]prich[/cyan] run [green]{template_id}[/green]{' -g' if global_install else ''} --help")


def install_template_venv(template: TemplateModel, template_base: Path = None, force: bool = False):
    """Install Python venv for a template"""
    from prich.cli.venv_utils import install_python_venv

    if not template_base:
        template_base = Path(template.folder)
    scripts_folder = template_base / "scripts"
    if template.venv == "isolated":
        template_venv = scripts_folder / "venv"
        install_python_venv(template_venv, force=force, venv_type="isolated")
        install_template_python_dependencies(template_venv, template_base)
        console_print("[green]Done![/green]")
    elif template.venv == "shared":
        prich_dir = get_prich_dir()
        shared_venv = prich_dir / "venv"
        if shared_venv.exists() and force:
            raise click.ClickException(f"Shared venv with --force is not supported as it might break other templates that uses shared venv, if you are sure that you want to do this you can remove {shorten_path(str(shared_venv))} folder manually and then execute this command again without --force option flag.")
        install_python_venv(shared_venv, venv_type="shared")
        install_template_python_dependencies(shared_venv, template_base)
        console_print("[green]Done![/green]")
    else:
        console_print(f"Template {template.id} doesn't require venv. To setup venv add 'venv: \"isolated\"' or 'venv: \"shared\" into the template and rerun this command.'")


@click.command("venv-install")
@click.argument("template_id")
@click.option("-g", "--global", "global_only", is_flag=True, help="Only global config")
@click.option("-f", "--force", "force", is_flag=True, help="Re-install venv")
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
