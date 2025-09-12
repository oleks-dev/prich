import hashlib
from pathlib import Path

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

def iter_files(base: Path):
    for p in sorted(base.rglob("*")):
        if p.is_file():
            yield p

def directory_hash(dir_path: Path) -> tuple[str, list[str]]:
    FILE_MODE = 0o100644  # regular file with 0644 perms

    h = hashlib.sha256()
    dir_files_list = []
    for p in iter_files(dir_path):
        rel = p.relative_to(dir_path).as_posix()
        dir_files_list.append(str(rel))
        # hash path + normalized type/perms + file bytes
        h.update(b"PATH\x00" + rel.encode("utf-8"))
        h.update(b"MODE\x00" + str(FILE_MODE).encode())
        with p.open("rb") as f:
            while True:
                chunk = f.read(1024 * 1024)
                if not chunk:
                    break
                h.update(chunk)
    return h.hexdigest(), dir_files_list
