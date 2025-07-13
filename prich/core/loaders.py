import click
from pathlib import Path
from typing import Dict, Optional, Tuple
from prich.core.utils import console_print, shorten_home_path
from prich.models.utils import recursive_update
from prich.models.config import ConfigModel
from prich.models.template import TemplateModel
from prich.core.state import _loaded_templates, _loaded_config


def _load_yaml(path: Path) -> Dict:
    import yaml
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def load_config_model(path: Path) -> Tuple[Optional[ConfigModel], Optional[Path]]:
    raw_yaml = _load_yaml(path)
    if not raw_yaml:
        return None, path
    if raw_yaml.get("schema_version") != "1.0":
        raise click.ClickException(f"Unsupported config schema version: {raw_yaml.get('schema_version')}")
    from pydantic import TypeAdapter

    # Parse full config
    try:
        adapter = TypeAdapter(ConfigModel)
        config = adapter.validate_python(raw_yaml)
        return config, path
    except Exception as e:
        msg_lines = [f"[yellow]Failed to load config: {shorten_home_path(str(path))}"]
        if 'errors' in e.__dir__():
            for error in e.errors():
                msg_lines.append(f"  * {error.get('msg')}. {error.get('type')}: {'.'.join(error.get('loc'))}")
        msg_lines.append("[/yellow]")
        console_print("\n".join(msg_lines))
        return None, None

def load_local_config() -> Tuple[ConfigModel, Path]:
    return load_config_model(Path.cwd() / ".prich/config.yaml")

def load_global_config() -> Tuple[ConfigModel, Path]:
    return load_config_model(Path.home() / ".prich/config.yaml")

def load_merged_config() -> Tuple[ConfigModel, list[Path]]:
    from prich.core.utils import should_use_global_only, shorten_home_path, should_use_local_only

    if not should_use_local_only():
        global_config, global_path = load_global_config()
    else:
        global_config, global_path = None, None
    if not should_use_global_only():
        local_config, local_path = load_local_config()
    else:
        local_config, local_path = None, None
    result = None
    if local_config and global_config:
        result = ConfigModel(**recursive_update(global_config, local_config).model_dump(exclude_none=True)), [global_path, local_path]
    elif local_config and local_config.providers:
        result = local_config, [local_path]
    elif global_config and global_config.providers:
        result = global_config, [global_path]
    if result and result[0] and result[0].providers:
        return result
    elif result and result[0] and not result[0].providers and result[1]:
        raise click.ClickException(f"No providers config found. Check config files: {[shorten_home_path(str(path_item)) for path_item in result[1]]}")
    raise click.ClickException(f"No config found. Run 'prich init' first.")

def _load_template_model(yaml_file: Path, base_dir: Path = None) -> TemplateModel | None:
    template = None
    try:
        if yaml_file.is_file():
            template = _load_yaml(yaml_file)
            if template:
                template["source"] = "global" if base_dir == Path.home() else "local"
                template["folder"] = str(yaml_file.parent)
                template["file"] = str(yaml_file)
                return TemplateModel(**template)
    except Exception as e:
        if 'errors' in e.__dir__():
            raise click.ClickException(f"""Failed to load template {template.get('name') if template else '?'} from {yaml_file}: {', '.join([f'{x.get("msg")}: {x.get("loc")}' for x in e.errors()])}""")
        else:
            raise click.ClickException(f"Failed to load template {template.get('name') if template else '?'} from {yaml_file}: {e}")

def _load_template_models(base_dir: Path) -> list[TemplateModel]:
    templates = []
    template_dir = base_dir / ".prich/templates"
    if template_dir.exists():
        for subdir in template_dir.iterdir():
            if subdir.is_dir():
                yaml_file = subdir / f"{subdir.name}.yaml"
                template = _load_template_model(yaml_file, base_dir)
                templates.append(template)
    return templates

def load_template_models(): #global_only: bool = False, local_only: bool = False) -> list[TemplateModel]:
    from prich.core.utils import should_use_global_only, shorten_home_path, should_use_local_only
    global_templates = _load_template_models(Path.home())
    if should_use_global_only():
        return global_templates
    local_templates = _load_template_models(Path.cwd())
    if should_use_local_only():
        return local_templates
    local_ids = {template.id for template in local_templates if template}
    filtered_globals = [template for template in global_templates if template.id not in local_ids]
    return local_templates + filtered_globals

def get_loaded_config():
    global _loaded_config, _loaded_config_paths
    if _loaded_config is None:
        _loaded_config, _loaded_config_paths = load_merged_config()
    return _loaded_config, _loaded_config_paths

def get_loaded_template(template_id: str):
    if not _loaded_templates:
        get_loaded_templates()
    if template_id not in _loaded_templates:
        raise click.ClickException(f"Template {template_id} not found.")
    return _loaded_templates[template_id]

def get_loaded_templates(tags: list[str]=None):
    if not _loaded_templates:
        templates = load_template_models()
        for template in templates:
            _loaded_templates[template.id] = template
    if tags:
        return [t for t in _loaded_templates.values() if t.has_any_tag(tags)]
    return list(_loaded_templates.values())
