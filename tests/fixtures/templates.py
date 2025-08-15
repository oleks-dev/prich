import pytest
from pathlib import Path
from prich.models.template import TemplateModel, VariableDefinition, PythonStep, LLMStep, PromptFields
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
                default="Assistant",
                required=False
            )
        ],
        steps=[
            LLMStep(
                name="llm step",
                type="llm",
                prompt=PromptFields(
                    system="Hi {{ name }}",
                    user="Analyse `{{ test_output }}`?"
                )
            )
        ],
        source="local",
        folder=str(tmp_path),
        file="",
    )
    return tpl
