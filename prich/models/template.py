from pathlib import Path

import click
from pydantic import BaseModel, Field, model_validator
from typing import List, Optional, Literal, Annotated, Union

# Template Variables

class VariableDefinition(BaseModel):
    name: str
    type: Literal["str", "list[str]", "int", "list[int]", "bool"] = "str"
    description: Optional[str] = None
    default: Optional[str] = None
    required: bool = False
    cli_option: Optional[str] = None


# Template Pipeline Steps

class PromptFields(BaseModel):
    system: Optional[str] = None
    user: Optional[str] = None
    prompt: Optional[str] = None


class StepValidation(BaseModel):
    match: Optional[str] = None
    not_match: Optional[str] = None
    on_fail: Literal["error", "warn", "skip", "continue"] = "error"


class BaseStepModel(BaseModel):
    name: str
    output_variable: str | None = None
    output_file: str | None = None
    output_file_mode: Literal["write", "append"] = None
    when: str | None = None
    validation: Optional[StepValidation] = None


class LLMStep(BaseStepModel):
    type: Literal["llm"]
    prompt: PromptFields
    provider: Optional[str] = None


class PythonStep(BaseStepModel):
    type: Literal["python"]
    call: str
    args: list[str] = []


class CommandStep(BaseStepModel):
    type: Literal["command"]
    call: str
    args: list[str] = []


class RenderStep(BaseStepModel):
    type: Literal["render"]
    template: str


PipelineStep = Annotated[
    Union[PythonStep, CommandStep, LLMStep, RenderStep],
    Field(discriminator="type")
]


# Main Template

class TemplateModel(BaseModel):
    name: str
    version: str = "1.0"
    description: Optional[str] = None
    author: Optional[str] = None
    tags: Optional[List[str]] = []
    venv: Optional[Literal["shared", "isolated"]] = "shared"
    steps: list[PipelineStep]
    variables: Optional[List[VariableDefinition]] = []

    schema_version: Literal["1.0"] = "1.0"

    # These fields are injected at runtime
    source: Optional[Literal["local", "global"]] = Field(default=None, exclude=True)
    folder: Optional[str] = Field(default=None, exclude=True)
    file: Optional[str] = Field(default=None, exclude=True)

    @model_validator(mode="after")
    def validate_unique_step_names(self) -> "TemplateModel":
        seen = set()
        idx = 0
        for step in self.steps:
            idx += 1
            if step.name in seen:
                raise ValueError(f"Duplicate {self.name} template step name (#{idx}): '{step.name}'")
            seen.add(step.name)
        return self

    def has_tag(self, tag: str) -> bool:
        return tag.lower() in (t.lower() for t in self.tags)
    
    def has_any_tag(self, tags: List[str]) -> bool:
        lowered_tags = {t.lower() for t in self.tags}
        return any(t.lower() in lowered_tags for t in tags)

    def as_yaml(self) -> str:
        import yaml
        return yaml.safe_dump(self.model_dump())

    def save(self, location: Literal["local", "global"] | None = None, filename: Path | str = None):
        import yaml
        prich_dir = None
        if location and filename:
            if location == "local":
                prich_dir = Path.home()
            elif location == "global":
                prich_dir = Path.cwd()
            prich_dir = prich_dir / ".prich"
            template_file = prich_dir / "templates" / self.name
        elif not filename and self.folder and self.file:
            template_file = Path(self.folder) / self.file
        else:
            raise click.ClickException(f"Failed to prepare file path for template {self.name}")
        if template_file.exists():
            import shutil
            template_backup_file = str(template_file).replace(".yaml", ".bak", -1)
            shutil.copy(template_file, template_backup_file)
        with open(template_file, "w") as f:
            return yaml.safe_dump(self.model_dump(), f)
