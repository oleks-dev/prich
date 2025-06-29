from pathlib import Path

import click

from prich.core.utils import shorten_home_path
from prich.core.loaders import get_loaded_config
from prich.core.utils import console_print

def _readable_paths(paths: list[Path]):
    return [f"[green]{shorten_home_path(str(p))}[/green]" for p in paths]

@click.group("config")
def config_group():
    """Manage prich configuration."""
    pass

@config_group.command(name="providers")
@click.option("-g", "--global", "global_only", is_flag=True, help="Only global providers")
@click.option("-d", "--details", is_flag=True, help="Show full provider details")
def list_providers(global_only: bool, details: bool):
    """Show available LLM providers."""
    config, paths = get_loaded_config()
    console_print(f"[bold]Configs[/bold]: {', '.join(_readable_paths(paths))}")
    console_print(f"[bold]Providers{f' ([green]g[/green])' if global_only else ''}[/bold]:")
    for provider, providerConfig in config.providers.items():
        console_print(f"- [green]{provider}[/green] ([blue]{providerConfig.provider_type}[/blue]{f', [blue]{providerConfig.model}[/blue]' if providerConfig.model else ''})")
        if details:
            for k, v in providerConfig.dict().items():
                if v:
                    console_print(f"    {k}: [blue]{v}[/blue]")

@config_group.command(name="show")
@click.option("-g", "--global", "global_only", is_flag=True, help="Only global config")
@click.option("-l", "--local", "local_only", is_flag=True, help="Only local config")
def show_config(global_only: bool, local_only: bool):
    """Show config."""
    import yaml
    config, paths = get_loaded_config()
    console_print(f"[bold]Configs[/bold]: {', '.join(_readable_paths(paths))}")
    console_print(yaml.dump(config.dict()))

@config_group.command(name="edit")
@click.option("-g", "--global", "global_only", is_flag=True, help="Only global config")
@click.option("-l", "--local", "local_only", is_flag=True, help="Only local config")
def show_config(global_only: bool, local_only: bool):
    """Edit config."""
    import subprocess

    config, paths = get_loaded_config()
    if not global_only and not local_only:
        raise click.ClickException("Use Edit with --global or --local option only")
    elif (global_only or local_only) and len(paths) == 1:
        subprocess.run(["vim", str(paths[0])], check=True)
