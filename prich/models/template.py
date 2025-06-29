from pydantic import BaseModel
from typing import List, Optional, Literal


class PreprocessStep(BaseModel):
    call: str
    type: Literal["python", "command"]
    output_variable: Optional[str] = None
    args: List[str] = []


class Preprocess(BaseModel):
    steps: Optional[List[PreprocessStep]] = []
    venv: Optional[Literal["shared", "isolated"]] = None


class VariableDefinition(BaseModel):
    name: str
    type: Literal["str", "list[str]", "int", "list[int]", "bool"] = "str"
    description: Optional[str] = None
    default: Optional[str] = None
    required: bool = False
    cli_option: Optional[str] = None


class TemplateFields(BaseModel):
    system: Optional[str] = None
    user: Optional[str] = None
    prompt: Optional[str] = None


class TemplateModel(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    version: str = "1.0"
    name: str
    description: Optional[str] = None
    tags: Optional[List[str]] = []
    variables: Optional[List[VariableDefinition]] = []
    preprocess: Optional[Preprocess] = None
    template: TemplateFields

    # These fields are injected at runtime
    source: Optional[Literal["local", "global"]] = None
    folder: Optional[str] = None
    file: Optional[str] = None

    def has_tag(self, tag: str) -> bool:
        return tag.lower() in (t.lower() for t in self.tags)
    
    def has_any_tag(self, tags: List[str]) -> bool:
        lowered_tags = {t.lower() for t in self.tags}
        return any(t.lower() in lowered_tags for t in tags)
