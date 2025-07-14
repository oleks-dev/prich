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

@click.command("templates-repo")
@click.option("-t", "--tag", "tags", multiple=True, help="Tag to filter templates")
@click.option("-j", "--json", "json_only", is_flag=True, help="Output raw json index manifest")
def list_github_templates(tags, json_only):
    """List available for installation templates from GitHub."""
    import requests
    import json
    from rich.table import Table
    from rich.console import Console

    def has_any_tag(template: dict, tags: List[str]) -> bool:
        lowered_tags = {t.lower() for t in template.get("tags")}
        return any(t.lower() in lowered_tags for t in tags)

    TEMPLATE_INDEX_URL = "https://raw.githubusercontent.com/oleks-dev/prich-templates/main/templates/index.json"
    console = Console()
    try:
        response = requests.get(TEMPLATE_INDEX_URL)
        response.raise_for_status()
        data = json.loads(response.text)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] Failed to fetch or parse template index: {e}")
        return

    templates = data.get("templates", [])
    if not templates:
        console.print("[yellow]No templates found in the index.[/yellow]")
        return

    if tags:
        templates = [tpl for tpl in templates if has_any_tag(tpl, tags)]
        if not templates:
            console.print("[yellow]No templates found in the index by provided tags.[/yellow]")
            return
        console.print(f"Filtered by tags: {','.join([f'[green]{tag}[/green]' for tag in tags])}")

    if json_only:
        data['templates'] = templates
        console_print(f"[bold]{TEMPLATE_INDEX_URL}[/bold]")
        console_print(json.dumps(data, indent=2))
        return

    table = Table(title=data.get("name", "Templates"), show_lines=False)
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="green")
    table.add_column("Tags", style="magenta")
    table.add_column("Version", style="yellow")
    table.add_column("Description", style="white")
    table.add_column("Author", style="cyan")
    table.add_column("Checksum", style="dim", overflow="fold")

    for template in templates:
        table.add_row(
            template.get("id", "-"),
            template.get("name", "-"),
            ", ".join(template.get("tags", [])),
            template.get("version", "-"),
            template.get("description", "-"),
            template.get("author", "-"),
            template.get("checksum", "")[:12] + "…" if template.get("checksum") else ""
        )

    console.print(table)