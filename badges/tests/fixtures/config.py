import pytest
import yaml
from pydantic import TypeAdapter
from prich.models.config import ConfigModel

CONFIG_YAML = """
schema_version: "1.0"
providers:
  show_prompt:
    mode: flat
    provider_type: "echo"
provider_modes:
  - name: plain
    prompt: '{% if instructions %}{{ instructions }}\n{% endif %}{{ input }}'
  - name: flat
    prompt: |-
      {% if instructions %}### System:
      {{ instructions }}

      {% endif %}### User:
      {{ input }}

      ### Assistant:
  - name: mistral-instruct
    prompt: |-
      <s>[INST]
      {% if instructions %}{{ instructions }}

      {% endif %}{{ input }}
      [/INST]
  - name: llama2-chat
    prompt: |-
      <s>[INST]
      {% if instructions %}{{ instructions }}

      {% endif %}{{ input }}
      [/INST]
  - name: anthropic
    prompt: |-
      Human: {% if instructions %}{{ instructions }}

      {% endif %}{{ input }}

      Assistant:
  - name: chatml
    prompt: '[{% if instructions %}{"role": "system", "content": "{{ instructions }}"},{% endif %}{"role": "user", "content": "{{ input }}"}]'
settings:
  default_provider: "show_prompt"
  editor: "vi"
"""


@pytest.fixture
def basic_config():
    adapter = TypeAdapter(ConfigModel)
    config = """
schema_version: "1.0"
providers:
  show_prompt:
    mode: flat
    provider_type: "echo"
provider_modes:
  - name: plain
    prompt: '{% if instructions %}{{ instructions }}\n{% endif %}{{ input }}'
  - name: flat
    prompt: |-
      {% if instructions %}### System:
      {{ instructions }}

      {% endif %}### User:
      {{ input }}

      ### Assistant:
settings: 
    default_provider: "show_prompt"
    editor: "vi"
"""
    config = adapter.validate_python(yaml.safe_load(config))
    return config

@pytest.fixture
def basic_config_with_prompts():
    adapter = TypeAdapter(ConfigModel)
    config = adapter.validate_python(yaml.safe_load(CONFIG_YAML))
    return config
