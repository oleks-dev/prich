from pathlib import Path

import click
from pydantic import BaseModel, Field, model_validator
from typing import List, Optional, Literal, Annotated, Union
from prich.models.file_scope import FileScope
from prich.core.utils import is_valid_variable_name
from prich.version import TEMPLATE_SCHEMA_VERSION


# Template Variables

class VariableDefinition(BaseModel):
    name: str
    type: Literal["str", "list[str]", "int", "list[int]", "bool"] = "str"
    description: Optional[str] = None
    default: Optional[str | bool | int | list] = None
    required: Optional[bool] = False
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
    id: str
    name: str
    version: str = "1.0"
    description: Optional[str] = None
    author: Optional[str] = None
    tags: Optional[List[str]] = []
    venv: Optional[Literal["shared", "isolated", None]] = None
    steps: list[PipelineStep]
    variables: Optional[List[VariableDefinition]] = []
    usage_examples: Optional[list[str]] = None

    schema_version: Literal["1.0"] = TEMPLATE_SCHEMA_VERSION

    # These fields are injected at runtime
    source: Optional[Literal[FileScope.LOCAL, FileScope.GLOBAL, FileScope.EXTERNAL]] = Field(default=None, exclude=True)
    folder: Optional[str] = Field(default=None, exclude=True)
    file: Optional[str] = Field(default=None, exclude=True)

    @model_validator(mode="after")
    def validate_unique_step_names_and_variable_names(self) -> "TemplateModel":
        seen = set()
        idx = 0
        # validate step names
        for step in self.steps:
            idx += 1
            if step.name in seen:
                raise click.ClickException(f"Duplicate {self.id} template step name (#{idx}): '{step.name}'")
            seen.add(step.name)
        # validate variable names
        for variable in self.variables:
            if not is_valid_variable_name(variable.name):
                raise click.ClickException(f"Invalid variable name '{variable.name}' in {self.id} template: Variable name should contain only upper and lowercase letters, underscores, and numbers.")
        return self

    def has_tag(self, tag: str) -> bool:
        return tag.lower() in (t.lower() for t in self.tags)
    
    def has_any_tag(self, tags: List[str]) -> bool:
        lowered_tags = {t.lower() for t in self.tags}
        return any(t.lower() in lowered_tags for t in tags)

    def as_yaml(self) -> str:
        import yaml
        return yaml.safe_dump(self.model_dump())

    def save(self, location: Literal[FileScope.LOCAL, FileScope.GLOBAL] | None = None):
        import os, yaml
        prich_dir = None
        if location == "local" or (not location and self.source == FileScope.LOCAL):
            prich_dir = Path.cwd() / ".prich"
        elif location == "global" or (not location and self.source == FileScope.GLOBAL):
            prich_dir = Path.home() / ".prich"
        if location or (not location and self.source):
            template_file = prich_dir / "templates" / self.id / f"{self.id}.yaml"
        else:
            raise click.ClickException(f"Failed to prepare file path for template {self.id}")
        if template_file.exists():
            import shutil
            template_backup_file = str(template_file).replace(".yaml", ".bak", -1)
            shutil.copy(template_file, template_backup_file)
        else:
            os.makedirs(template_file.parent, exist_ok=True)
        with open(template_file, "w") as f:
            return yaml.safe_dump(self.model_dump(), f)

    def describe(self):
        return f"""
        Template: {self.id}
        Name: {self.name}
        Description: {self.description}
        Version: {self.version}
        Tags: {", ".join(self.tags or [])}
        Steps: {len(self.steps)} total
        Variables:
        {self._describe_vars()}
        """

    def _describe_vars(self):
        return "\n".join(
            f"  - {v.name}: {v.description or 'No description'} (type: {v.type})"
            for v in self.variables
        )
