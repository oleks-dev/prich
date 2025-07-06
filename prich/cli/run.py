import click

from prich.cli.dynamic_command_group import DynamicCommandGroup


@click.group("run", cls=DynamicCommandGroup)
@click.option("-g", "--global", "global_only", is_flag=True, default=False, help="Only global config and templates")
@click.option("-l", "--local", "local_only", is_flag=True, default=False, help="Only local config and templates")
def run_group(global_only, local_only):
    """Run a template with dynamic arguments defined in templates.yaml."""
    pass
