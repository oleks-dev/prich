import os
import click
from pathlib import Path
from prich.core.utils import shorten_home_path
from prich.core.loaders import get_loaded_config, load_local_config, load_global_config
from prich.core.utils import console_print

def _readable_paths(paths: list[Path]):
    return [f"[green]{shorten_home_path(str(p))}[/green]" for p in paths]

@click.group("config")
def config_group():
    """Manage prich configuration."""
    pass

@config_group.command(name="providers")
@click.option("-g", "--global", "global_only", is_flag=True, help="Only global config providers")
@click.option("-l", "--local", "local_only", is_flag=True, help="Only local config providers")
@click.option("-d", "--details", is_flag=True, help="Show full provider details")
def list_providers(global_only: bool, local_only: bool, details: bool):
    """Show available LLM providers."""
    config, paths = get_loaded_config()
    console_print(f"[bold]Configs[/bold]: {', '.join(_readable_paths(paths))}")
    console_print(f"[bold]Providers{f' ([green]global[/green])' if global_only else f' ([green]local[/green])' if local_only else ''}[/bold]:")
    for provider, providerConfig in config.providers.items():
        console_print(f"- [green]{provider}[/green] ([blue]{providerConfig.provider_type}[/blue]{f', [blue]{providerConfig.model}[/blue]' if providerConfig.model else ''})")
        if details:
            for k, v in providerConfig.model_dump().items():
                if v:
                    console_print(f"    {k}: [blue]{v}[/blue]")

@config_group.command(name="show")
@click.option("-g", "--global", "global_only", is_flag=True, help="Only global config")
@click.option("-l", "--local", "local_only", is_flag=True, help="Only local config")
def show_config(global_only: bool, local_only: bool):
    """Show config."""
    config, paths = get_loaded_config()
    console_print(f"[bold]Configs[/bold]: {', '.join(_readable_paths(paths))}")
    console_print(config.as_yaml())

@config_group.command(name="edit")
@click.option("-g", "--global", "global_only", is_flag=True, help="Only global config")
@click.option("-l", "--local", "local_only", is_flag=True, help="Only local config")
def edit_config(global_only: bool, local_only: bool):
    """Edit config using the default editor."""
    import subprocess
    local_config, local_path = load_local_config()
    global_config, global_path = load_global_config()
    config, path = None, None
    if global_only:
        config, path = global_config, global_path
    elif local_only:
        config, path = local_config, local_path
    elif local_config and local_path:
        config, path = local_config, local_path
    elif global_config and global_path:
        config, path = global_config, global_path
    if not config:
        raise click.ClickException(f"No config file found {shorten_home_path(str(path))}. Please check your configuration or run init.")
    editor_cmd = config.settings.editor if config.settings and config.settings.editor else os.getenv("EDITOR", "vi")
    console_print(f"Executing: {editor_cmd} {str(path)}")
    subprocess.run([editor_cmd, str(path)], check=True, stdout=None)
