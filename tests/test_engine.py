import click
import pytest

from tests.fixtures.config import basic_config_with_prompts
from prich.core.engine import render_prompt, render_template
from prich.models.template import PromptFields

variables = {
    "name": "Example Name",
    "assistant": "System Assistant"
}

@pytest.mark.parametrize("provider_mode, prompt, expected", [
    ("chatml",
     PromptFields(
        system="User name is {{ name }}.",
        user="Hello, {{ assistant }}"),
     f"""[{{"role": "system", "content": "User name is {variables['name']}."}},{{"role": "user", "content": "Hello, {variables['assistant']}"}}]"""),

    ("chatml",
     PromptFields(
        system="User name is {{ name }}.",
        user="Hello, {{ assistant }}",
        prompt="Ignored prompt"),
     f"""[{{"role": "system", "content": "User name is {variables['name']}."}},{{"role": "user", "content": "Hello, {variables['assistant']}"}}]"""),

    ("chatml",
     PromptFields(
        user="Hello, {{ assistant }}"),
     f"""[{{"role": "user", "content": "Hello, {variables['assistant']}"}}]"""),

    ("flat",
     PromptFields(
         user="Hello, {{ assistant }}"),
     f"### User:\nHello, {variables['assistant']}\n\n### Assistant:"
     ),

    ("flat",
     PromptFields(
        system="User name is {{ name }}.",
        user="Hello, {{ assistant }}"),
     f"### System:\nUser name is {variables['name']}.\n\n### User:\nHello, {variables['assistant']}\n\n### Assistant:"
     ),

    ("flat",
     PromptFields(
         user="Hello, {{ assistant }}"),
     f"### User:\nHello, {variables['assistant']}\n\n### Assistant:"
     ),

    ("plain",
     PromptFields(
         prompt="Hello, {{ assistant }}"),
     f"Hello, {variables['assistant']}"
     ),

    ("mistral-instruct",
     PromptFields(
         system="User name is {{ name }}.",
         user="Hello, {{ assistant }}"),
     f"<s>[INST]\nUser name is {variables['name']}.\n\nHello, {variables['assistant']}\n[/INST]"
     ),

    ("mistral-instruct",
     PromptFields(
         user="Hello, {{ assistant }}"),
     f"<s>[INST]\nHello, {variables['assistant']}\n[/INST]"
     ),

    ("anthropic",
     PromptFields(
         system="User name is {{ name }}.",
         user="Hello, {{ assistant }}"),
     f"Human: User name is {variables['name']}.\n\nHello, {variables['assistant']}\n\nAssistant:"
     ),

    ("anthropic",
     PromptFields(
         user="Hello, {{ assistant }}"),
     f"Human: Hello, {variables['assistant']}\n\nAssistant:"
     ),

])
def test_render_prompt(provider_mode, prompt, expected, basic_config_with_prompts):
    actual = render_prompt(basic_config_with_prompts, prompt, variables=variables, mode=provider_mode)
    assert actual == expected

@pytest.mark.parametrize("chat_mode, prompt", [
    ("chatml",
     PromptFields(system="User name is {{ name }}"),
     ),

    ("flat",
     PromptFields(system="User name is {{ name }}"),
     ),

    ("plain",
     PromptFields(system="User name is {{ name }}"),
     ),

    ("mistral-instruct",
     PromptFields(system="User name is {{ name }}"),
     ),

    ("anthropic",
     PromptFields(system="User name is {{ name }}"),
     )

])
def test_render_prompt_exception(chat_mode, prompt, basic_config_with_prompts):
    with pytest.raises(click.ClickException):
        render_prompt(basic_config_with_prompts, prompt, variables=variables, mode=chat_mode)

@pytest.mark.parametrize("template_string, expected", [
    ("Hello {{ assistant }}", "Hello System Assistant"),
    ("Hello {{ assistant|upper }}", "Hello SYSTEM ASSISTANT"),
    ("Hello {{ assistant }}   ", "Hello System Assistant"),
    ("", ""),
    (None, "")
])
def test_render_template(template_string, expected):
    actual = render_template(template_string, variables=variables)
    assert expected == actual
