from prich.models.template_repo_manifest import TemplatesRepoManifest

def get_remote_prich_templates_manifest(manifest_url: str = "https://raw.githubusercontent.com/oleks-dev/prich-templates/main/templates/manifest.json"):
    import click
    import json
    import requests
    try:
        response = requests.get(manifest_url)
        response.raise_for_status()
        json_data = json.loads(response.text)
        manifest = TemplatesRepoManifest(**json_data)
    except Exception as e:
        raise click.ClickException(f"Error: Failed to fetch or parse templates repository manifest: {e}")
    return manifest
