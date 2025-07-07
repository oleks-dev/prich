from pathlib import Path

import click
from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict


class ProviderConfig(BaseModel):
    provider_type: str
    mode: Optional[str] = None
    api_endpoint: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None
    model_path: Optional[str] = None
    options: Optional[List[str]] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None


class SecurityConfig(BaseModel):
    allowed_environment_variables: list[str] = None


class SettingsConfig(BaseModel):
    default_provider: str
    provider_assignments: Optional[Dict[str, str]] = None
    editor: Optional[str] = None


class ConfigModel(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    providers: Dict[str, ProviderConfig]
    settings: SettingsConfig
    security: Optional[SecurityConfig] = None

    def as_yaml(self) -> str:
        import yaml
        return yaml.safe_dump(self.model_dump(), sort_keys=False)

    def save(self, location: Literal["local", "global"]):
        import yaml
        if location == "local":
            prich_dir = Path.cwd()
        elif location == "global":
            prich_dir = Path.home()
        else:
            raise click.ClickException("Save config location param value is not supported")
        prich_dir = prich_dir / ".prich"
        prich_config_file = prich_dir / "config.yaml"
        if prich_config_file.exists():
            import shutil
            prich_config_backup_file = prich_dir / "config.bak"
            shutil.copy(prich_config_file, prich_config_backup_file)
        with open(prich_config_file, "w") as f:
            f.write(yaml.safe_dump(self.model_dump(exclude_none=True), sort_keys=False))
