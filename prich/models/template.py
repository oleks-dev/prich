from pathlib import Path

import click
from pydantic import BaseModel, Field, model_validator, ConfigDict
from typing import List, Optional, Literal, Annotated, Union
from prich.models.output_shaping import BaseOutputShapingModel
from prich.constants import RESERVED_RUN_TEMPLATE_CLI_OPTIONS
from prich.models.file_scope import FileScope
from prich.core.utils import is_valid_variable_name, is_cli_option_name
from prich.version import TEMPLATE_SCHEMA_VERSION


# Template Variables

class VariableDefinition(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str
    type: Literal["str", "list[str]", "int", "list[int]", "bool", "list[bool]", "path", "list[path]"] = "str"
    description: Optional[str] = None
    default: Optional[str | bool | int | list] = None
    required: Optional[bool] = False
    cli_option: Optional[str] = None


# Template Pipeline Steps

class ValidateStepOutput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    match: Optional[str] = None
    not_match: Optional[str] = None
    on_fail: Optional[Literal["error", "warn", "skip", "continue"]] = "error"
    message: Optional[str] = None


class ExtractVarModel(BaseModel):
    regex: str
    variable: str
    multiple: Optional[bool] = False  # default: single match


class BaseStepModel(BaseOutputShapingModel):
    model_config = ConfigDict(extra='forbid')

    name: str

    # regex transforms
    extract_vars: Optional[list[ExtractVarModel]] = None  # enrichment

    # persistence
    output_variable: Optional[str | None] = None
    output_file: Optional[str | None] = None
    output_file_mode: Optional[Literal["write", "append"]] = None
    output_console: Optional[bool | None] = None

    # execution control
    when: Optional[str | None] = None
    validate_: Optional[ValidateStepOutput | list[ValidateStepOutput]] = Field(alias="validate", default=None)

    def postprocess_extract_vars(self, output: str, variables: dict):
        import re

        # extract side variables
        if self.extract_vars:
            for spec in self.extract_vars:
                pattern = re.compile(spec.regex)
                if spec.multiple:
                    matches = pattern.findall(output)
                    if matches:
                        # if regex has groups, findall returns tuples
                        values = [m if isinstance(m, str) else m[0] for m in matches]
                        variables[spec.variable] = values
                    else:
                        variables[spec.variable] = []
                else:
                    m = pattern.search(output)
                    if m:
                        variables[spec.variable] = m.group(1) if m.groups() else m.group(0)
                    else:
                        variables[spec.variable] = ""


class LLMStep(BaseStepModel):
    type: Literal["llm"]

    # overload provider mentioned in the config
    provider: Optional[str] = None

    # prompt
    instructions: Optional[str] = None
    input: Optional[str] = None

    # These fields are injected at runtime
    rendered_instructions: Optional[str] = Field(default=None, exclude=True)
    rendered_input: Optional[str] = Field(default=None, exclude=True)
    rendered_prompt: Optional[str] = Field(default=None, exclude=True)


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
    model_config = ConfigDict(extra='forbid')
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
        if not self.steps:
            raise click.ClickException(f"No steps found in {self.id} template.")
        for step in self.steps:
            idx += 1
            if step.name in seen:
                raise click.ClickException(f"Duplicate {self.id} template step name (#{idx}): '{step.name}'")
            seen.add(step.name)
        # validate variable names
        variable_default_value_type_error = False
        for variable in self.variables:
            if not is_valid_variable_name(variable.name):
                raise click.ClickException(f"Invalid variable name '{variable.name}' in {self.id} template: Variable name should contain only upper and lowercase letters, underscores, and numbers.")
            cli_option_name_set_from_name = False
            if not variable.cli_option:
                variable.cli_option = f"--{variable.name}"
                cli_option_name_set_from_name = True
            if not is_cli_option_name(variable.cli_option):
                if cli_option_name_set_from_name:
                    raise click.ClickException(f"Invalid cli_option name '{variable.cli_option}' (template {self.id}) auto-set from variable name '{variable.name}', it should contain only lowercase letters, numbers, underscores, and hyphens - or add a separate 'cli_option' param with another name.")
                else:
                    raise click.ClickException(f"Invalid cli_option name '{variable.cli_option}' (template {self.id}) in variable '{variable.name}', it should start with double hyphen '--<option_name>' and contain only lowercase letters, numbers, underscores, and hyphens")
            reserved_names = [x for x in RESERVED_RUN_TEMPLATE_CLI_OPTIONS if x.startswith("--")]
            if variable.cli_option in reserved_names:
                raise click.ClickException(f"Not allowed cli_option name '{variable.cli_option}' (template {self.id}) in variable '{variable.name}', please do not use the following reserved option names: {reserved_names}")
            if variable.default is not None:
                type_variable_default = type(variable.default)
                if ((variable.type == "str" and type_variable_default != str) or
                        (variable.type == "bool" and type_variable_default != bool) or
                        (variable.type == "int" and type_variable_default != int) or
                        (variable.type == "path" and type_variable_default != str)
                ):
                    variable_default_value_type_error = True

                elif variable.type.startswith("list"):
                    if type_variable_default != list:
                        variable_default_value_type_error = True
                    else:
                        list_type = variable.type.split('[')[1][:-1]
                        if list_type == "path":
                            list_type = "str"
                        for list_item in variable.default:
                            if type(list_item).__name__ != list_type:
                                variable_default_value_type_error = True
                                break
                if variable_default_value_type_error:
                    raise click.ClickException(f"Variable {variable.name} default value type error, should be {variable.type} but has value: {variable.default}")
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

        def str_presenter(dumper, data):
            if "\n" in data:  # multiline string
                return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
            return dumper.represent_scalar("tag:yaml.org,2002:str", data)

        yaml.add_representer(str, str_presenter, Dumper=yaml.SafeDumper)

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
        model_dict = self.model_dump(exclude_none=True)
        # fix 'validate_' field
        for step in model_dict.get("steps"):
            step["validate"] = step.pop("validate_") if step.get("validate_") else None
        with open(template_file, "w") as f:
            f.write(yaml.safe_dump(model_dict, sort_keys=False, width=float("inf")))

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
