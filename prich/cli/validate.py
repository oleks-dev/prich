from pathlib import Path
import click
from prich.core.file_scope import classify_path
from prich.core.loaders import find_template_files, load_template_model
from prich.core.utils import console_print, shorten_home_path


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
        raise click.ClickException("When YAML file is selected it doesn't combine with local, global, or id options, use: 'prich validate --file ./.prich/templates/test-template/test-template.yaml'")

    if validate_file and not validate_file.exists():
        raise click.ClickException(f"Failed to find {validate_file} template file.")

    # Load Template Files
    template_files = []
    if validate_file:
        # Load one template file
        template_files = [validate_file]
    else:
        # Prepare Template Files Path
        file_paths = [Path.cwd(), Path.home()]
        if global_only:
            file_paths.remove(Path.cwd())
        if local_only:
            file_paths.remove(Path.home())
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
            console_print(f"- {template.id} [dim]({template.source.value}) {shorten_home_path(str(template_file))}[/dim]: [green]is valid[/green]" )
        except click.ClickException as e:
            failures_found = True
            template_source = classify_path(template_file)
            console_print(f"- [dim]({template_source.value}) {shorten_home_path(str(template_file))}[/dim]: [red]is not valid\n  {e.message.replace(f' from {template_file}', '')}[/red]")
    if failures_found:
        sys.exit(1)
