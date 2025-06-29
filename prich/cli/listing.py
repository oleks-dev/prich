from typing import List

import click

from prich.core.loaders import get_loaded_templates
from prich.core.utils import console_print


@click.command(name="tags")
@click.option("-g", "--global", "global_only", is_flag=True, help="List only global templates")
def list_tags(global_only: bool):
    """List available tags from templates."""
    from collections import Counter
    templates = get_loaded_templates()
    if not templates:
        console_print("[yellow]No templates installed. Use 'prich template install' to add templates.[/yellow]")
        return

    console_print(f"[bold]Available tags:[/bold]")
    tags = []
    for t in templates:
        tags.extend(t.tags)
    counts = Counter(tags)
    for t, c in counts.items():
        console_print(f"- [green]{t}[/green] [dim]({c})[/dim]")

@click.command(name="list")
@click.option("-g", "--global", "global_only", is_flag=True, help="List only global templates")
@click.option("-t", "--tag", "tags", multiple=True, help="Tag to include")
def list_templates(global_only: bool, tags: List[str]):
    """List available templates."""
    templates = get_loaded_templates(tags)
    if not templates and not tags:
        console_print("[yellow]No templates installed. Use 'prich install' to add templates.[/yellow]")
        return
    if not templates and tags:
        console_print(f"[yellow]No templates found with specified tags: {', '.join(tags)}.[/yellow]")
        return

    selected_tags = f" (tags: [green]{', '.join(tags)}[/green])" if tags else ""
    console_print(f"[bold]Available templates{selected_tags}:[/bold]")
    for t in templates:
        source = t.source
        marker = " ([blue]g[/blue])" if source == "global" else ""
        template_tags = f" [dim](tags: [green]{', '.join(t.tags)}[/green])[/dim]" if t.tags else ""
        console_print(f"- [green]{t.name}[/green]{marker}: [blue]{t.description}[/blue]{template_tags}")

