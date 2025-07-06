import venv

import click
import pytest
from pathlib import Path

from click.testing import CliRunner
from prich.cli.config import list_providers, show_config, edit_config

from prich.core.engine import run_template
from prich.core.state import _loaded_templates
from prich.models.template import TemplateModel, PromptFields, VariableDefinition, PipelineStep, PythonStep, RenderStep, CommandStep, LLMStep
from prich.models.config import ConfigModel, SettingsConfig, ProviderConfig

@pytest.fixture
def basic_config():
    return ConfigModel(
        schema_version="1.0",
        providers={
            "show_prompt": ProviderConfig(provider_type="echo", mode="flat")
        },
        # security=SecurityConfig(),
        settings=SettingsConfig(default_provider="show_prompt")
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
            VariableDefinition(
                name="name",
                type="str",
                default="Assistant",
                required=False
            )
        ],
        venv="shared",
        steps=[
            PythonStep(
                name="Preprocess",
                call="test.py",
                type="python",
                args=[],
                output_variable="test_output"
            ),
            LLMStep(
                name="LLM Step",
                type="llm",
                prompt=PromptFields(
                    system="You are {{ name }}",
                    user="Analyse `{{ test_output }}`"
                )
            )
        ],
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


def test_run_template_shared_venv(monkeypatch, template, basic_config, tmp_path):
    template.name = 'test_shared_venv_tpl'
    template.file = str(tmp_path / "shared_venv_tpl.yaml")
    template.venv = "shared"
    template.steps.insert(0, PythonStep(name="python step", call="test.py", type="python", args=[], output_variable="test_output"))

    _loaded_templates.clear()
    _loaded_config = None
    _loaded_templates[template.name] = template

    from prich.core.state import _loaded_config_paths

    monkeypatch.setattr("prich.core.loaders.get_loaded_config", lambda: (basic_config, _loaded_config_paths))
    monkeypatch.setattr("prich.core.loaders.load_merged_config", lambda: (basic_config, _loaded_config_paths))

    # Place dummy preprocess script inside the template
    venv_dir = Path(template.folder).parent / "venv"
    venv.create(venv_dir, with_pip=True)
    tpl_script_path = Path(template.folder) / "scripts" / "test.py"
    print(tpl_script_path)
    tpl_script_path.parent.mkdir(parents=True, exist_ok=True)
    tpl_script_path.write_text("""#!/usr/bin/env python
import sys; print('Preprocess OK')""")
    tpl_script_path.chmod(0o755)

    run_template(template.name, name="Test")

def test_run_template_isolated_venv(monkeypatch, template, basic_config, tmp_path):
    template.name = 'test_isolated_venv_tpl'
    template.file = str(tmp_path / "isolated_venv_tpl.yaml")
    template.venv = "isolated"
    template.steps.insert(0, PythonStep(name="python step", call="test.py", type="python", args=[], output_variable="test_output"))
    _loaded_templates.clear()
    _loaded_config = None
    _loaded_templates[template.name] = template

    from prich.core.state import _loaded_config_paths

    monkeypatch.setattr("prich.core.loaders.get_loaded_config", lambda: (basic_config, _loaded_config_paths))
    monkeypatch.setattr("prich.core.loaders.load_merged_config", lambda: (basic_config, _loaded_config_paths))

    # Place dummy preprocess script inside the template
    venv_dir = Path(template.folder) / "scripts" / "venv"
    venv.create(venv_dir, with_pip=True)
    tpl_script_path = Path(template.folder) / "scripts" / "test.py"
    print(tpl_script_path)
    tpl_script_path.parent.mkdir(parents=True, exist_ok=True)
    tpl_script_path.write_text("""#!/usr/bin/env python
import sys; print('Preprocess OK')""")
    tpl_script_path.chmod(0o755)

    run_template(template.name, name="Test")

def test_run_template_shell_call(monkeypatch, template, basic_config, tmp_path):
    template.name = 'test_cmd_tpl'
    template.file = str(tmp_path / "test_cmd_tpl.yaml")
    template.steps.insert(0, CommandStep(name="shell call", call="date", type="command", args=["-u"], output_variable="test_output"))
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
        steps=[
          LLMStep(
              name="llm_step",
              type="llm",
              prompt=PromptFields(
                  user="Hello {{ must_be_set }}"
              )
          )
        ],
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

@pytest.mark.parametrize("params", [
    (["-l"]),
    (["-g"]),
    (["-l", "-d"]),
    (["-g", "-d"]),
    (None)
])
def test_config_providers_list(params, monkeypatch, template, basic_config, tmp_path):
    _loaded_templates.clear()
    _loaded_templates[template.name] = template

    from prich.core.state import _loaded_config_paths, _loaded_config
    _loaded_config = None

    monkeypatch.setattr("prich.core.loaders.get_loaded_config", lambda: (basic_config, _loaded_config_paths))
    monkeypatch.setattr("prich.core.loaders.load_merged_config", lambda: (basic_config, _loaded_config_paths))

    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(list_providers, params)
        assert result.exit_code == 0
        assert "Configs:" in result.output
        assert f"Providers{' (global)' if params and '-g' in params else ' (local)' if params and '-l' in params else ''}:" in result.output
        assert "show_prompt (echo)" in result.output

@pytest.mark.parametrize("param", [
    ("-l"),
    ("-g"),
    (None)
])
def test_show_config(param, monkeypatch, template, basic_config, tmp_path):

    _loaded_templates.clear()
    _loaded_config = None
    _loaded_templates[template.name] = template

    from prich.core.state import _loaded_config_paths

    monkeypatch.setattr("prich.cli.config.get_loaded_config", lambda: (basic_config, _loaded_config_paths))
    monkeypatch.setattr("prich.core.loaders.load_merged_config", lambda: (basic_config, _loaded_config_paths))

    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(show_config, [param] if param else [])
        assert result.exit_code == 0
        assert "Configs:" in result.output
        assert basic_config.as_yaml() in result.output

@pytest.mark.parametrize("param", [
    ("-l"),
    ("-g"),
    (None)
])
def test_edit_config(param, monkeypatch, template, basic_config, tmp_path):
    basic_config.settings.editor = "echo"
    global_config = basic_config.model_copy(deep=True)
    global_config.settings.editor = "ls"

    _loaded_templates.clear()
    _loaded_config = None
    _loaded_templates[template.name] = template

    from prich.core.state import _loaded_config_paths
    _loaded_config_paths = [Path(tmp_path)]

    monkeypatch.setattr("prich.cli.config.load_local_config", lambda: (basic_config, _loaded_config_paths[0]))
    monkeypatch.setattr("prich.cli.config.load_global_config", lambda: (global_config, _loaded_config_paths[0]))
    # monkeypatch.setattr("prich.core.loaders.load_local_config", lambda: (basic_config, _loaded_config_paths[0]))
    # monkeypatch.setattr("prich.core.loaders.load_global_config", lambda: (global_config, _loaded_config_paths[0]))
    # monkeypatch.setattr("prich.core.loaders._loaded_config", _loaded_config)
    # monkeypatch.setattr("prich.core.utils.should_use_local_only", lambda: True if param == "-l" else False)
    # monkeypatch.setattr("prich.core.utils.should_use_global_only", lambda: True if param == "-g" else False)

    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(edit_config, [param] if param else [])
        assert result.exit_code == 0
        assert f"Executing: {'echo' if param == '-l' else 'ls' if param == '-g' else 'echo'}" in result.output
