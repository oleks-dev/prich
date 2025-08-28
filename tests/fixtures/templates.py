import shutil
import tempfile

import pytest
from pathlib import Path

from prich.models.file_scope import FileScope

from prich.models.template import TemplateModel, VariableDefinition, PythonStep, LLMStep, CommandStep, \
    ValidateStepOutput
from tests.generate.templates import generate_template, templates


@pytest.fixture
def template_with_python_and_venv(tmp_path, isolated_venv: bool = False) -> TemplateModel:
    return generate_template(tmp_path, isolated_venv=isolated_venv)

@pytest.fixture()
def templates_fixture(request):
    params = request.param
    def call(**kw):
        return templates(**{**params, **kw})
    return call

@pytest.fixture
def wrong_template_no_steps(tmp_path):
    return TemplateModel(
        schema_version="1.0",
        version="1.0",
        id="tpl",
        name="tpl",
        description="Test template",
        tags=["test"],
        variables=[
            VariableDefinition(
                name="name",
                type="str",
                cli_option="--name",
                default="Assistant",
                required=False
            ),
            VariableDefinition(
                name="name_test",
                type="str",
                default="Assistant",
                required=False
            )
        ],
        steps = []
    )

@pytest.fixture
def template(tmp_path):
    tpl = TemplateModel(
        schema_version="1.0",
        version="1.0",
        id="tpl",
        name="tpl",
        description="Test template",
        tags=["test"],
        variables=[
            VariableDefinition(
                name="name",
                type="str",
                cli_option="--name",
                default="Assistant",
                required=False
            ),
            VariableDefinition(
                name="name_test",
                type="str",
                default="Assistant",
                required=False
            )
        ],
        steps=[
            LLMStep(
                name="llm step",
                type="llm",
                instructions="Hi {{ name }}",
                input="Analyse `{{ test_output }}`?",
                output_variable="llm_response",
                output_file="test_llm_response.txt",
                when="1==1",
                validate=ValidateStepOutput(
                    match=".+",
                    not_match="^not match"
                )
            )
        ],
        source=FileScope.LOCAL,
        folder=str(tmp_path),
        file="test.yaml",
    )
    return tpl

@pytest.fixture
def shared_venv_template(tmp_path):
    tpl = TemplateModel(
        schema_version="1.0",
        version="1.0",
        id="shared_tpl",
        name="shared template",
        description="Shared venv template",
        tags=["test"],
        variables=[
            VariableDefinition(
                name="name",
                type="str",
                default="Assistant",
                required=False
            ),
            VariableDefinition(
                name="test",
                type="bool",
                cli_option="--test",
                required=False
            )
        ],
        venv="shared",
        steps=[
            CommandStep(
                name="Preprocess cmd",
                call="echo",
                type="command",
                args=["test"],
                output_file="echo_output.txt",
                output_variable="test_output_echo",
                validate=ValidateStepOutput(match=".+", not_match="^not")
            ),
            PythonStep(
                name="Preprocess python",
                call="test.py",
                type="python",
                args=[],
                output_variable="test_output"
            ),
            LLMStep(
                name="LLM Step",
                type="llm",
                instructions="You are {{ name }}",
                input="Analyse `{{ test_output }}`"
            )
        ],
        source=FileScope.LOCAL,
        folder=str(tmp_path),
        file=str(tmp_path / "shared_tpl.yaml"),
    )
    return tpl


TEMPLATE_YAML = """
schema_version: "1.0"
id: test_template
name: Test Template
version: "1.0"
description: A test template
variables: []
steps:
  - name: "LLM step"
    type: llm
    instructions: "System prompt"
    input: "User prompt"
"""

INVALID_TEMPLATE_YAML = """
schema_version: "1.0"
version: "1.0"
variables: []
steps:
  - name: "LLM_step"
    type: llm
    instructions: "Missing name"
"""

@pytest.fixture
def temp_template_dir():
    temp_dir = Path(tempfile.mkdtemp())
    template_dir = temp_dir / "test_template"
    template_dir.mkdir()
    (template_dir / "test_template.yaml").write_text(TEMPLATE_YAML)
    yield template_dir

    shutil.rmtree(temp_dir)

@pytest.fixture
def temp_empty_dir():
    temp_dir = Path(tempfile.mkdtemp())
    template_dir = temp_dir / "test_emtpy"
    template_dir.mkdir()
    yield {"name": "test_emtpy",
           "folder": template_dir}

    shutil.rmtree(temp_dir)
