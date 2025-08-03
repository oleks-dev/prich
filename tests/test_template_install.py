import shutil
import tempfile
from pathlib import Path
import pytest
from click.testing import CliRunner
from prich.cli.templates import template_install
from prich.core.loaders import load_config_model, _load_template_model
from prich.core.engine import render_prompt
from prich.models.template import PromptFields

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
    prompt:
      system: "System prompt"
      user: "User prompt"
"""

INVALID_TEMPLATE_YAML = """
schema_version: "1.0"
version: "1.0"
variables: []
steps:
  - name: "LLM_step"
    type: llm
    prompt: 
      system: "Missing name"
"""

CONFIG_YAML = """
schema_version: "1.0"
providers:
  show_prompt:
    provider_type: "echo"
    mode: "flat"
provider_modes:
  - name: plain
    prompt: '{{ prompt }}'
  - name: flat
    prompt: |-
      {% if system %}### System:
      {{ system }}

      {% endif %}### User:
      {{ user }}

      ### Assistant:
  - name: mistral-instruct
    prompt: |-
      <s>[INST]
      {% if system %}{{ system }}

      {% endif %}{{ user }}
      [/INST]
  - name: llama2-chat
    prompt: |-
      <s>[INST]
      {% if system %}{{ system }}

      {% endif %}{{ user }}
      [/INST]
  - name: anthropic
    prompt: |-
      Human: {% if system %}{{ system }}

      {% endif %}{{ user }}

      Assistant:
  - name: chatml
    prompt: '[{% if system %}{"role": "system", "content": "{{ system }}"},{% endif %}{"role": "user", "content": "{{ user }}"}]'
settings:
  editor: "vim"
  default_provider: "show_prompt"
"""

@pytest.fixture
def temp_template_dir():
    temp_dir = Path(tempfile.mkdtemp())
    template_dir = temp_dir / "test_template"
    template_dir.mkdir()
    (template_dir / "test_template.yaml").write_text(TEMPLATE_YAML)
    yield template_dir
    shutil.rmtree(temp_dir)

def test_template_install_local(temp_template_dir):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(template_install, [str(temp_template_dir)])
        assert result.exit_code == 0
        assert "Template test_template installed successfully" in result.output
        assert Path(".prich/templates/test_template/test_template.yaml").exists()

def test_template_install_force_overwrite(temp_template_dir):
    runner = CliRunner()
    with runner.isolated_filesystem():
        # First install
        runner.invoke(template_install, [str(temp_template_dir)])
        # Second install without --force should fail
        result = runner.invoke(template_install, [str(temp_template_dir)])
        assert result.exit_code != 0
        assert "already exists" in result.output
        # Now with --force
        result = runner.invoke(template_install, [str(temp_template_dir), "--force"])
        assert result.exit_code == 0
        assert "installed successfully" in result.output

def test_config_model_load():
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.yaml"
        config_path.write_text(CONFIG_YAML)
        config_model, loaded_path = load_config_model(config_path)
        assert config_model is not None
        assert config_model.settings.default_provider == "show_prompt"
        assert "show_prompt" in config_model.providers

def test_render_template_prompt_basic():
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.yaml"
        config_path.write_text(CONFIG_YAML)
        config_model, _ = load_config_model(config_path)

    fields = PromptFields(system="Hello {{ name }}", user="Your input is {{ value }}")
    variables = {"name": "Test", "value": "XYZ"}
    rendered = render_prompt(config_model, fields, variables, template_dir=".", mode="flat")
    assert "Hello Test" in rendered
    assert "Your input is XYZ" in rendered

def test_invalid_template_validation():
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "invalid.yaml"
        file_path.write_text(INVALID_TEMPLATE_YAML)
        with pytest.raises(Exception) as exc:
            _load_template_model(file_path)
        assert "Field required" in str(exc.value)
