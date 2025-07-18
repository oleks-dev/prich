import click

from prich.cli.run import run_group
from prich.cli.templates import template_install, show_template, create_template, venv_install
from prich.cli.listing import list_tags, list_templates, list_github_templates
from prich.cli.config import config_group
from prich.cli.init_cmd import init
from prich.core.utils import console_print
from prich.version import VERSION

@click.group()
@click.version_option(VERSION, package_name="prich")
def cli():
    """prich: CLI for reusable rich LLM prompts with script pipelines."""
    console_print(f"[bold][cyan]prich v{VERSION}[/cyan][/bold] - CLI for reusable rich LLM prompts with script pipelines")

cli.add_command(run_group)
cli.add_command(template_install)
cli.add_command(config_group)
cli.add_command(init)
cli.add_command(list_tags)
cli.add_command(list_templates)
cli.add_command(list_github_templates)
cli.add_command(show_template)
cli.add_command(create_template)
cli.add_command(venv_install)

if __name__ == "__main__":
    cli()