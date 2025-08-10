from typing import List

import click

from prich.core.loaders import get_loaded_templates
from prich.core.utils import console_print
from prich.models.template_repo_manifest import TemplatesRepoManifest, TemplateRepoItem


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

    def has_any_tag(template: TemplateRepoItem, tags: List[str]) -> bool:
        lowered_tags = {t.lower() for t in template.tags}
        return any(t.lower() in lowered_tags for t in tags)

    TEMPLATES_MANIFEST_URL = "https://raw.githubusercontent.com/oleks-dev/prich-templates/main/templates/manifest.json"

    console = Console()
    try:
        console.print(f"Fetching: {TEMPLATES_MANIFEST_URL}")
        response = requests.get(TEMPLATES_MANIFEST_URL)
        response.raise_for_status()
        json_data = json.loads(response.text)
        manifest = TemplatesRepoManifest(**json_data)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] Failed to fetch or parse templates repository manifest: {e}")
        return

    templates = manifest.templates or []
    if not templates:
        console.print("[yellow]No templates found in the templates repository manifest.[/yellow]")
        return

    if tags:
        templates = [tpl for tpl in templates if has_any_tag(tpl, tags)]
        if not templates:
            console.print("[yellow]No templates found by provided tags in the templates repository manifest.[/yellow]")
            return
        console.print(f"Filtered by tags: {','.join([f'[green]{tag}[/green]' for tag in tags])}")

    if json_only:
        console_print(json.dumps([tpl.model_dump() for tpl in templates], indent=2))
        return

    table = Table(title=manifest.name or "prich Templates", caption=f'{manifest.description or ""} ({manifest.repository})', show_lines=False)
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="green")
    table.add_column("Tags", style="magenta")
    table.add_column("Version", style="yellow")
    table.add_column("Description", style="white")
    table.add_column("Author", style="cyan")
    table.add_column("Archive Checksum", style="dim", overflow="fold")
    table.add_column("Folder Checksum", style="dim", overflow="fold")

    for template in templates:
        table.add_row(
            template.id or "-",
            template.name or "-",
            ", ".join(template.tags or []),
            template.version or "-",
            template.description or "-",
            template.author or "-",
            (template.archive_checksum or "")[:7] + "…" if template.archive_checksum else "",
            (template.folder_checksum or "")[:7] + "…" if template.folder_checksum else ""
        )

    console.print(table)
    console.print()
    console.print("Install template by executing: prich install -r <template_id>")
