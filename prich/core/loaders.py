import os

import click
from pathlib import Path
from typing import Dict, Optional, Tuple, List, Iterable
from prich.constants import PRICH_DIR_NAME
from prich.core.file_scope import classify_path
from prich.core.state import _loaded_templates, _loaded_config, _loaded_config_paths
from prich.core.utils import console_print, shorten_path, get_prich_dir
from prich.models.utils import recursive_update
from prich.models.config import ConfigModel
from prich.models.template import TemplateModel
from prich.version import TEMPLATE_SCHEMA_VERSION, CONFIG_SCHEMA_VERSION


def _load_yaml(path: Path) -> Dict:
    import yaml
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def load_config_model(config_file: Path) -> Tuple[Optional[ConfigModel], Optional[Path]]:
    config_yaml = _load_yaml(config_file)
    if not config_yaml:
        return None, config_file
    if config_yaml.get("schema_version") != CONFIG_SCHEMA_VERSION:
        raise click.ClickException(f"Unsupported config schema version {config_yaml.get('schema_version')}, this prich version supports only {CONFIG_SCHEMA_VERSION}: {shorten_path(str(config_file))}")
    from pydantic import TypeAdapter

    # Parse full config
    try:
        adapter = TypeAdapter(ConfigModel)
        config = adapter.validate_python(config_yaml)
        return config, config_file
    except Exception as e:
        msg_lines = [f"[yellow]Failed to load config: {shorten_path(str(config_file))}"]
        if 'errors' in e.__dir__():
            for error in e.errors():
                msg_lines.append(f"  * {error.get('msg')}. {error.get('type')}: {'.'.join(error.get('loc'))}")
        msg_lines.append("[/yellow]")
        console_print("\n".join(msg_lines))
        return None, None

def load_local_config() -> Tuple[ConfigModel, Path]:
    return load_config_model(get_prich_dir(global_only=False) / "config.yaml")

def load_global_config() -> Tuple[ConfigModel, Path]:
    return load_config_model(get_prich_dir(global_only=True) / "config.yaml")

def load_merged_config() -> Tuple[ConfigModel, List[Path]]:
    from prich.core.utils import should_use_global_only, shorten_path, should_use_local_only

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
        raise click.ClickException(f"No providers config found. Check config files: {[shorten_path(str(path_item)) for path_item in result[1]]}")
    raise click.ClickException(f"No config found. Run 'prich init' first.")

def load_template_model(yaml_file: Path) -> TemplateModel | None:
    template_yaml = None
    try:
        if yaml_file.is_file():
            template_yaml = _load_yaml(yaml_file)
            if template_yaml:
                if template_yaml.get("schema_version") != TEMPLATE_SCHEMA_VERSION:
                    raise click.ClickException(
                        f"Unsupported template schema version {template_yaml.get('schema_version') if template_yaml.get('schema_version') else 'NOT SET'}, this prich version supports only {TEMPLATE_SCHEMA_VERSION}: {shorten_path(str(yaml_file))}")
                template_yaml["source"] = classify_path(file=yaml_file)
                template_yaml["folder"] = str(yaml_file.parent)
                template_yaml["file"] = str(yaml_file)
                return TemplateModel(**template_yaml)
        raise click.ClickException(f"Failed to load {shorten_path(str(yaml_file))}, check if file or contents are correct.")
    except Exception as e:
        if 'errors' in e.__dir__():
            raise click.ClickException(f"""Failed to load template {template_yaml.get('name') if template_yaml else '?'} from {yaml_file}: {', '.join([f'{x.get("msg")}: {x.get("loc")}' for x in e.errors()])}""")
        else:
            raise click.ClickException(f"Failed to load template {template_yaml.get('name') if template_yaml else '?'} from {yaml_file}: {e}")

def find_template_files(base_dir: Path) -> List[Path]:
    """Find template YAML files"""
    template_files = []
    template_dir = base_dir / PRICH_DIR_NAME / "templates"
    if template_dir.exists():
        for subdir in template_dir.iterdir():
            if subdir.is_dir():
                yaml_file = subdir / f"{subdir.name}.yaml"
                template_files.append(yaml_file)
    return template_files

def _load_template_models(base_dir: Path) -> List[TemplateModel]:
    """Load Template Models from the base_dir (ignores templates that are failing to load)"""
    templates = []
    template_files = find_template_files(base_dir)
    template_files.sort()
    for template_file in template_files:
        try:
            template = load_template_model(template_file)
            templates.append(template)
        except click.ClickException:
            pass  # ignore load templates that are failed to load
    return templates

def load_templates() -> List[TemplateModel]:
    """Load templates based on the global+local or only local or only global"""
    from prich.core.utils import should_use_global_only, should_use_local_only
    global_templates = _load_template_models(Path.home())
    if should_use_global_only():
        return global_templates
    local_templates = _load_template_models(Path.cwd())
    if should_use_local_only():
        return local_templates
    local_ids = {template.id for template in local_templates if template}
    filtered_globals = [template for template in global_templates if template.id not in local_ids]
    return local_templates + filtered_globals

def get_loaded_config() -> Tuple[ConfigModel, List[Path]]:
    global _loaded_config, _loaded_config_paths
    if _loaded_config is None:
        _loaded_config, _loaded_config_paths = load_merged_config()
    return _loaded_config, _loaded_config_paths

def get_loaded_template(template_id: str) -> TemplateModel:
    if not _loaded_templates:
        get_loaded_templates()
    if template_id not in _loaded_templates:
        raise click.ClickException(f"Template {template_id} not found.")
    return _loaded_templates[template_id]

def get_loaded_templates(tags: List[str] = None) -> List[TemplateModel]:
    if not _loaded_templates:
        templates = load_templates()
        for template in templates:
            _loaded_templates[template.id] = template
    if tags:
        return [t for t in _loaded_templates.values() if t.has_any_tag(tags)]
    return list(_loaded_templates.values())

def get_env_vars() -> dict[str, str]:
    """
    Load environment variables from current os.environ + given env files,
    optionally filtered by allowed_environment_variables.
    """
    from dotenv import dotenv_values
    from prich.core.state import _loaded_env_vars

    if _loaded_env_vars is not None:
        return _loaded_env_vars

    # Start with a copy of current environment
    merged = dict(os.environ)

    config, _ = get_loaded_config()
    env_files = config.settings.env_file if config.settings else None
    allowed_environment_variables = config.security.allowed_environment_variables if config.security else None

    if type(env_files) == str:
        env_files = [env_files]

    # Merge env files in order, last one wins
    if env_files is not None:
        for env_file in env_files:
            path = Path(env_file)
            if path.exists():
                file_vars = dotenv_values(path)
                merged.update({k: v for k, v in file_vars.items() if v is not None})

    # Apply filtering if needed
    if allowed_environment_variables is not None:
        allowed_set = set(allowed_environment_variables)
        merged = {k: v for k, v in merged.items() if k in allowed_set}

    _loaded_env_vars = merged

    return merged