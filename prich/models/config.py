import os

import click
from typing import List, Optional, Literal, Dict, Annotated, Union
from pydantic import BaseModel, Field, field_validator, TypeAdapter, ConfigDict
from prich.constants import PRICH_DIR_NAME
from prich.core.utils import get_cwd_dir, get_home_dir
from prich.models.file_scope import FileScope
from prich.models.config_providers import EchoProviderModel, OpenAIProviderModel, MLXLocalProviderModel, STDINConsumerProviderModel, OllamaProviderModel
from prich.version import CONFIG_SCHEMA_VERSION

ProviderConfig = Annotated[
    Union[
        EchoProviderModel,
        OpenAIProviderModel,
        MLXLocalProviderModel,
        OllamaProviderModel,
        STDINConsumerProviderModel
    ],
    Field(discriminator='provider_type')
]


class SecurityConfig(BaseModel):
    model_config = ConfigDict(extra='forbid')
    allowed_environment_variables: Optional[List[str]] = None


class SettingsConfig(BaseModel):
    model_config = ConfigDict(extra='forbid')
    default_provider: Optional[str] = None
    provider_assignments: Optional[Dict[str, str]] = None
    editor: Optional[str] = None
    env_file: Optional[str | List[str]] = None


class ProviderModeModel(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str
    prompt: str

class ConfigModel(BaseModel):
    model_config = ConfigDict(extra='forbid')
    schema_version: Literal["1.0"] = CONFIG_SCHEMA_VERSION
    providers: Dict[str, ProviderConfig]
    # TODO: make provider_modes optional? It's not used in some cases like with default Ollama non-raw provider
    provider_modes: List[ProviderModeModel]
    settings: Optional[SettingsConfig] = None
    security: Optional[SecurityConfig] = None

    @classmethod
    @field_validator("providers", mode="before")
    def inject_provider_names(cls, raw_providers: dict) -> dict:
        # Inject __name into each provider's context
        return {
            name: TypeAdapter(ProviderConfig).validate_python(entry, context={"__name": name})
            for name, entry in raw_providers.items()
        }

    def as_yaml(self) -> str:
        import yaml
        return yaml.safe_dump(self.model_dump(exclude_none=True), sort_keys=False)

    def save(self, location: Literal[FileScope.LOCAL, FileScope.GLOBAL]):
        import yaml

        def str_presenter(dumper, data):
            if "\n" in data:  # multiline string
                return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
            return dumper.represent_scalar("tag:yaml.org,2002:str", data)

        yaml.add_representer(str, str_presenter, Dumper=yaml.SafeDumper)

        if location == FileScope.LOCAL:
            base_dir = get_cwd_dir()
        elif location == FileScope.GLOBAL:
            base_dir = get_home_dir()
        else:
            raise click.ClickException("Save config location param value is not supported")
        prich_dir = base_dir / PRICH_DIR_NAME
        os.makedirs(prich_dir, exist_ok=True)
        prich_config_file = prich_dir / "config.yaml"
        if prich_config_file.exists():
            import shutil
            prich_config_backup_file = prich_dir / "config.bak"
            shutil.copy(prich_config_file, prich_config_backup_file)
        with open(prich_config_file, "w") as f:
            f.write(yaml.safe_dump(self.model_dump(exclude_none=True), sort_keys=False, width=float("inf")))
