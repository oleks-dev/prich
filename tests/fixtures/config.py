import pytest
import yaml
from pydantic import TypeAdapter
from prich.models.config import ConfigModel


@pytest.fixture
def basic_config():
    adapter = TypeAdapter(ConfigModel)
    config = """
schema_version: "1.0"
providers:
  show_prompt:
    mode: flat
    provider_type: echo
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
settings: 
    default_provider: "show_prompt"
    editor: "vi"
"""
    config = adapter.validate_python(yaml.safe_load(config))
    return config

@pytest.fixture
def basic_config_with_prompts():
    adapter = TypeAdapter(ConfigModel)
    config = """
schema_version: "1.0"
providers:
  show_prompt:
    mode: flat
    provider_type: echo
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
    default_provider: "show_prompt"
    editor: "vi"
"""
    config = adapter.validate_python(yaml.safe_load(config))
    return config
