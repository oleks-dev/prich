from typing import List

import click

from prich.core.loaders import get_loaded_templates
from prich.core.utils import console_print


@click.command(name="tags")
@click.option("-g", "--global", "global_only", is_flag=True, help="List only global templates")
@click.option("-l", "--local", "local_only", is_flag=True, help="List only local templates")
def list_tags(global_only: bool, local_only: bool):
    """List available tags from templates."""
    from collections import Counter
    templates = get_loaded_templates()
    if not templates:
        console_print("[yellow]No templates installed. Use 'prich template install' to add templates.[/yellow]")
        return

    console_print(f"[bold]Available tags{f' ([green]global[/green])' if global_only else f' ([green]local[/green])' if local_only else ''}:[/bold]")
    tags = []
    for t in templates:
        tags.extend(t.tags)
    counts = Counter(tags)
    for t, c in counts.items():
        console_print(f"- [green]{t}[/green] [dim]({c})[/dim]")

@click.command(name="list")
@click.option("-g", "--global", "global_only", is_flag=True, help="List only global templates")
@click.option("-l", "--local", "local_only", is_flag=True, help="List only local templates")
@click.option("-t", "--tag", "tags", multiple=True, help="Tag to include")
def list_templates(global_only: bool, local_only: bool, tags: List[str]):
    """List available templates."""
    templates = get_loaded_templates(tags)
    if not templates and not tags:
        console_print("[yellow]No templates found. Use 'prich install' or 'prich create' to add templates.[/yellow]")
        return
    if not templates and tags:
        console_print(f"[yellow]No templates found with specified tags: {', '.join(tags)}.[/yellow]")
        return

    selected_tags = f" (tags: [green]{', '.join(tags)}[/green])" if tags else ""
    console_print(f"[bold]Available templates{selected_tags}:[/bold]")
    for template in templates:
        source = template.source
        marker = " ([green]g[/green])" if source == "global" else ""
        template_tags = f" [dim](tags: [green]{', '.join(template.tags)}[/green])[/dim]" if template.tags else ""
        console_print(f"- [green]{template.id}[/green]{marker}: [dim][green]{template.description}[/green][/dim]{template_tags}")

