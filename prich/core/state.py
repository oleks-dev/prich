from typing import Optional
from pathlib import Path
from prich.models.config import ConfigModel
from prich.models.template import TemplateModel

# Shared loaded configuration and paths
_loaded_config: Optional[ConfigModel] = None
_loaded_config_paths: list[Path] = []
_loaded_env_vars: Optional[dict[str, str]] = None

# Shared loaded templates cache
_loaded_templates: dict[str, TemplateModel] = {}

__all__ = ["_loaded_config", "_loaded_config_paths", "_loaded_templates", "_loaded_env_vars"]
