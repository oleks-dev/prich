import venv

import click
import pytest
from pathlib import Path
from prich.core.engine import run_template
from prich.core.state import _loaded_templates
from prich.models.template import TemplateModel, TemplateFields, VariableDefinition, Preprocess, PreprocessStep
from prich.models.config import ConfigModel, DefaultsConfig, SecurityConfig, ProviderConfig

@pytest.fixture
def basic_config():
    return ConfigModel(
        schema_version="1.0",
        providers={
            "show_prompt": ProviderConfig(provider_type="echo", mode="flat")
        },
        security=SecurityConfig(),
        defaults=DefaultsConfig(provider="show_prompt")
    )

@pytest.fixture
def shared_venv_template(tmp_path):
    tpl = TemplateModel(
        schema_version="1.0",
        version="1.0",
        name="shared_tpl",
        description="Shared venv template",
        tags=["test"],
        variables=[
            VariableDefinition(name="name", type="str", default="Assistant", required=False)
        ],
        preprocess=Preprocess(
            venv="shared",
            steps=[PreprocessStep(call="test.py", type="python", args=[], output_variable="test_output")]
        ),
        template=TemplateFields(
            system="You are {{ name }}",
            user="Analyse `{{ test_output }}`"
        ),
        source="local",
        folder=str(tmp_path),
        file=str(tmp_path / "shared_tpl.yaml"),
    )
    return tpl

@pytest.fixture
def template(tmp_path):
    tpl = TemplateModel(
        schema_version="1.0",
        version="1.0",
        name="tpl",
        description="Test template",
        tags=["test"],
        variables=[
            VariableDefinition(name="name", type="str", default="Assistant", required=False)
        ],
        preprocess=Preprocess(venv="shared", steps=[]),
        template=TemplateFields(
            system="Hi {{ name }}",
            user="Analyse `{{ test_output }}`?"
        ),
        source="local",
        folder=str(tmp_path),
        file="",
    )
    return tpl


def test_run_template_shared_venv(monkeypatch, template, basic_config, tmp_path):
    template.name = 'test_shared_venv_tpl'
    template.file = str(tmp_path / "shared_venv_tpl.yaml")
    template.preprocess = Preprocess(venv="shared", steps=[PreprocessStep(call="test.py", type="python", venv="shared", args=[], output_variable="test_output")])

    _loaded_templates.clear()
    _loaded_config = None
    _loaded_templates[template.name] = template

    from prich.core.state import _loaded_config_paths

    monkeypatch.setattr("prich.core.loaders.get_loaded_config", lambda: (basic_config, _loaded_config_paths))
    monkeypatch.setattr("prich.core.loaders.load_merged_config", lambda: (basic_config, _loaded_config_paths))

    # Place dummy preprocess script inside the template
    venv_dir = Path(template.folder).parent / "venv"
    venv.create(venv_dir, with_pip=True)
    tpl_script_path = Path(template.folder) / "preprocess" / "test.py"
    print(tpl_script_path)
    tpl_script_path.parent.mkdir(parents=True, exist_ok=True)
    tpl_script_path.write_text("""#!/usr/bin/env python
import sys; print('Preprocess OK')""")
    tpl_script_path.chmod(0o755)

    run_template(template.name, name="Test")

def test_run_template_isolated_venv(monkeypatch, template, basic_config, tmp_path):
    template.name = 'test_isolated_venv_tpl'
    template.file = str(tmp_path / "isolated_venv_tpl.yaml")
    template.preprocess = Preprocess(venv="isolated", steps=[PreprocessStep(call="test.py", type="python", venv="isolated", args=[], output_variable="test_output")])
    _loaded_templates.clear()
    _loaded_config = None
    _loaded_templates[template.name] = template

    from prich.core.state import _loaded_config_paths

    monkeypatch.setattr("prich.core.loaders.get_loaded_config", lambda: (basic_config, _loaded_config_paths))
    monkeypatch.setattr("prich.core.loaders.load_merged_config", lambda: (basic_config, _loaded_config_paths))

    # Place dummy preprocess script inside the template
    venv_dir = Path(template.folder) / "venv"
    venv.create(venv_dir, with_pip=True)
    tpl_script_path = Path(template.folder) / "preprocess" / "test.py"
    print(tpl_script_path)
    tpl_script_path.parent.mkdir(parents=True, exist_ok=True)
    tpl_script_path.write_text("""#!/usr/bin/env python
import sys; print('Preprocess OK')""")
    tpl_script_path.chmod(0o755)

    run_template(template.name, name="Test")

def test_run_template_shell_call(monkeypatch, template, basic_config, tmp_path):
    template.name = 'test_cmd_tpl'
    template.file = str(tmp_path / "test_cmd_tpl.yaml")
    template.preprocess = Preprocess(steps=[PreprocessStep(call="date", type="command", args=["-u"], output_variable="test_output")])
    _loaded_templates.clear()
    _loaded_config = None
    _loaded_templates[template.name] = template

    from prich.core.state import _loaded_config_paths

    monkeypatch.setattr("prich.core.loaders.get_loaded_config", lambda: (basic_config, _loaded_config_paths))
    monkeypatch.setattr("prich.core.loaders.load_merged_config", lambda: (basic_config, _loaded_config_paths))

    run_template(template.name, name="Test")

def test_invalid_template_missing_required_variable(monkeypatch, template, basic_config, tmp_path):
    tpl = TemplateModel(
        schema_version="1.0",
        version="1.0",
        name="missing_var",
        description="Invalid template",
        tags=[],
        variables=[
            VariableDefinition(name="must_be_set", type="str", required=True)
        ],
        template=TemplateFields(
            user="Hello {{ must_be_set }}"
        ),
        source="local",
        folder=str(tmp_path),
        file=str(tmp_path / "invalid.yaml"),
    )
    _loaded_templates.clear()
    _loaded_templates["missing_var"] = tpl

    from prich.core.state import _loaded_config_paths
    monkeypatch.setattr("prich.core.loaders.get_loaded_config", lambda: (basic_config, _loaded_config_paths))
    monkeypatch.setattr("prich.core.loaders.load_merged_config", lambda: (basic_config, _loaded_config_paths))

    import prich.llm_providers.get_llm_provider as prov
    monkeypatch.setattr(prov, "get_llm_provider", lambda name, cfg: type("Mock", (), {
        "name": name,
        "mode": "flat",
        "show_response": False,
        "send_prompt": lambda self, prompt=None: "response"
    })())

    with pytest.raises(click.ClickException) as exc:
        run_template("missing_var")

    assert "Missing required variable" in str(exc.value)