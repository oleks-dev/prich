import click
from pathlib import Path
from typing import List, Optional, Literal, Dict, Annotated, Union
from pydantic import BaseModel, Field, field_validator, TypeAdapter
from prich.models.config_providers import EchoProviderModel, OpenAIProviderModel, MLXLocalProviderModel, MLXLocalProviderModel, STDINConsumerProviderModel


ProviderConfig = Annotated[
    Union[
        EchoProviderModel,
        OpenAIProviderModel,
        MLXLocalProviderModel,
        STDINConsumerProviderModel
    ],
    Field(discriminator='provider_type')
]


class SecurityConfig(BaseModel):
    allowed_environment_variables: Optional[List[str]] = None


class SettingsConfig(BaseModel):
    default_provider: str
    provider_assignments: Optional[Dict[str, str]] = None
    editor: Optional[str] = None


class ConfigModel(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    providers: Dict[str, ProviderConfig]
    settings: SettingsConfig
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
