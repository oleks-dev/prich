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
    allow_python_injection: bool = False
    require_venv_for_python: bool = True

class DefaultsConfig(BaseModel):
    provider: str
    provider_assignments: Optional[Dict[str, str]] = Field(default_factory=dict)
    editor: Optional[str] = None

class ConfigModel(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    providers: Dict[str, ProviderConfig]
    security: SecurityConfig = SecurityConfig()
    defaults: DefaultsConfig
