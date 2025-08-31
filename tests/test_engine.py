import os
import tempfile
from subprocess import CompletedProcess

import click
import jinja2
import pytest
from pathlib import Path

from prich.models.config import SecurityConfig
from prich.models.template import ValidateStepOutput, PythonStep, CommandStep, VariableDefinition, LLMStep
from prich.core.loaders import load_config_model
from prich.core.engine import render_prompt, render_template
from tests.fixtures.config import basic_config, basic_config_with_prompts, CONFIG_YAML
from tests.fixtures.templates import template
from tests.generate.templates import generate_template

variables = {
    "name": "Example Name",
    "assistant": "System Assistant"
}

@pytest.mark.parametrize("provider_mode, llm_step, expected", [
    ("chatml",
     LLMStep(type="llm", name="test",
             instructions="User name is {{ name }}.",
             input="Hello, {{ assistant }}"),
     f"""[{{"role": "system", "content": "User name is {variables['name']}."}},{{"role": "user", "content": "Hello, {variables['assistant']}"}}]"""),

    ("chatml",
     LLMStep(type="llm", name="test",
             instructions="User name is {{ name }}.",
             input="Hello, {{ assistant }}",
             # TODO: check (was prompt)
             # prompt="Ignored prompt"
             ),
     f"""[{{"role": "system", "content": "User name is {variables['name']}."}},{{"role": "user", "content": "Hello, {variables['assistant']}"}}]"""),

    ("chatml",
     LLMStep(type="llm", name="test",
             input="Hello, {{ assistant }}"),
     f"""[{{"role": "user", "content": "Hello, {variables['assistant']}"}}]"""),

    ("flat",
     LLMStep(type="llm", name="test",
             input="Hello, {{ assistant }}"),
     f"### User:\nHello, {variables['assistant']}\n\n### Assistant:"
     ),

    ("flat",
     LLMStep(type="llm", name="test",
             instructions="User name is {{ name }}.",
             input="Hello, {{ assistant }}"),
     f"### System:\nUser name is {variables['name']}.\n\n### User:\nHello, {variables['assistant']}\n\n### Assistant:"
     ),

    ("flat",
     LLMStep(type="llm", name="test",
             input="Hello, {{ assistant }}"),
     f"### User:\nHello, {variables['assistant']}\n\n### Assistant:"
     ),

    ("plain",
     LLMStep(type="llm", name="test",
             # TODO: check (was prompt)
             input="Hello, {{ assistant }}"),
     f"Hello, {variables['assistant']}"
     ),

    ("mistral-instruct",
     LLMStep(type="llm", name="test",
             instructions="User name is {{ name }}.",
             input="Hello, {{ assistant }}"),
     f"<s>[INST]\nUser name is {variables['name']}.\n\nHello, {variables['assistant']}\n[/INST]"
     ),

    ("mistral-instruct",
     LLMStep(type="llm", name="test",
             input="Hello, {{ assistant }}"),
     f"<s>[INST]\nHello, {variables['assistant']}\n[/INST]"
     ),

    ("anthropic",
     LLMStep(type="llm", name="test",
             instructions="User name is {{ name }}.",
             input="Hello, {{ assistant }}"),
     f"Human: User name is {variables['name']}.\n\nHello, {variables['assistant']}\n\nAssistant:"
     ),

    ("anthropic",
     LLMStep(type="llm", name="test",
             input="Hello, {{ assistant }}"),
     f"Human: Hello, {variables['assistant']}\n\nAssistant:"
     ),

])
def test_render_prompt(provider_mode, llm_step, expected, basic_config_with_prompts):
    render_prompt(basic_config_with_prompts, llm_step, variables=variables, mode=provider_mode)
    assert llm_step.rendered_prompt == expected

@pytest.mark.parametrize("chat_mode, prompt", [
    ("chatml",
     LLMStep(type="llm", name="test",
             instructions="User name is {{ name }}"),
     ),

    ("flat",
     LLMStep(type="llm", name="test",
             instructions="User name is {{ name }}"),
     ),

    ("plain",
     LLMStep(type="llm", name="test",
             instructions="User name is {{ name }}"),
     ),

    ("mistral-instruct",
     LLMStep(type="llm", name="test",
             instructions="User name is {{ name }}"),
     ),

    ("anthropic",
     LLMStep(type="llm", name="test",
             instructions="User name is {{ name }}"),
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


def test_render_template_prompt_basic():
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.yaml"
        config_path.write_text(CONFIG_YAML)
        config_model, _ = load_config_model(config_path)

    llm_step = LLMStep(type="llm", name="test",
                     instructions="Hello {{ name }}",
                     input="Your input is {{ value }}"
    )
    variables = {"name": "Test", "value": "XYZ"}
    render_prompt(config_model, llm_step, variables, mode="flat")
    assert "Hello Test" in llm_step.rendered_prompt
    assert "Your input is XYZ" in llm_step.rendered_prompt


get_expand_vars_CASES = [
    {"id": "nested_vars_should_not_work",
     "args": ["--file={{{{HOME}}_DIR}}", "{{{{HOME}}}}"],
     "internal_vars": {"HOME_DIR": "./home/", "HOME": "home"},
     "expected_exception": click.ClickException,
     "expected_exception_message": "Render jinja error"
     },
    {"id": "skip_non_str_var",
     "args": [Path("./home"), "--file={{HOME_DIR}}"],
     "internal_vars": {"HOME_DIR": "./home/"},
     "expected_expanded_args": [Path("./home"), "--file=./home/"]},
    {"id": "correct",
     "args": ["--file={{HOME_DIR}}", "{{HOME}}"],
     "internal_vars": {"HOME_DIR": "./home/", "HOME": "home"},
     "expected_expanded_args": ["--file=./home/", "home"]},
    {"id": "correct_with_spaces",
     "args": ["--file={{HOME_DIR}}", "{{HOME}}"],
     "internal_vars": {"HOME_DIR": "./home dir/", "HOME": "home test"},
     "expected_expanded_args": ["--file=./home dir/", "home test"]},
# TODO: this should be added into load env vars
#     {"id": "not_listed_env_var_usage",
#      "args": ["$HOME", "${HOME}"],
#      "internal_vars": {},
#      "expected_exception": click.ClickException,
#      "expected_exception_message": "Environment variable HOME is not listed in allowed environment variables. Add it to config.security.allowed_environment_variables for usage."
#     },
    {"id": "correct_with_env",
     "args": ["--file=$T_HOME_1", "${THOME2}{{HOME_DIR}}"],
     "extra_env_vars": {"T_HOME_1": "./home1/", "THOME2": "home2"},
     "internal_vars": {"HOME_DIR": "./home/"},
     "expected_expanded_args": ["--file=./home1/", "home2./home/"]
     },
]
@pytest.mark.parametrize("case", get_expand_vars_CASES, ids=[c["id"] for c in get_expand_vars_CASES])
def test_expand_vars(monkeypatch, basic_config, case):
    from prich.core.loaders import get_loaded_config
    from prich.core.engine import expand_vars

    if case.get("extra_env_vars"):
        os.environ.update(case.get("extra_env_vars"))
        basic_config.security = SecurityConfig(
            allowed_environment_variables = list(case.get("extra_env_vars").keys())
        )

    monkeypatch.setattr("prich.core.loaders.get_loaded_config",  lambda: (basic_config, ["config.yaml"]))

    if case.get("expected_exception"):
        with pytest.raises(case.get("expected_exception")) as e:
            expand_vars(case.get("args"), case.get("internal_vars"))
        if case.get("expected_exception_message"):
            assert case.get("expected_exception_message") in str(e.value)
    else:
        actual = expand_vars(case.get("args"), case.get("internal_vars"))
        assert actual == case.get("expected_expanded_args")

get_get_jinja_env_CASES = [
    {"id": "when_conditional",
     "conditional_expression_only": True,
     "jinja_template": "{{ 1 == 1 }}",
     "expected_result": "True",
     },
    {"id": "builtin_vars_conditional",
     "conditional_expression_only": True,
     "internal_vars": {"hello_var": "hello"},
     "jinja_template": "{{ 'HELLO' | lower }} {{ hello_var | upper }} {{ ' hello ' | strip }} {{ 'hello' | length }} {{ '10' | int + 10}} {{ '1' | bool != True}}",
     "expected_result": "hello HELLO hello 5 20 False",
     },
    {"id": "builtin_vars",
     "conditional_expression_only": False,
     "internal_vars": {"hello_var": "hello"},
     "jinja_template": "{{ 'HELLO' | lower }} {{ hello_var | upper }} {{ 'hello' | length }} {{ '10' | int + 10}}",
     "expected_result": "hello HELLO 5 20",
     },
    {"id": "not_existing_jinja_filter",
     "conditional_expression_only": False,
     "internal_vars": {"hello_var": "hello"},
     "jinja_template": "{{ hello_var | nonexisting }}",
     "expected_exception": jinja2.exceptions.TemplateAssertionError,
     "expected_exception_message": "No filter named 'nonexisting'."
     },
    {"id": "import_outside_of_cwd",
     "conditional_expression_only": False,
     "jinja_template": "{{ '/users/notexisting/file.txt' | include_file }}",
     "expected_exception": click.ClickException,
     "expected_exception_message": "is outside the current working directory"
     },
    {"id": "not_existing_var",
     "conditional_expression_only": False,
     "jinja_template": "{{ nonexisting }}",
     "expected_exception": jinja2.exceptions.UndefinedError,
     "expected_exception_message": "'nonexisting' is undefined"
     },
    {"id": "include_file_file_not_found",
     "conditional_expression_only": False,
     "jinja_template": "{{ \"not_existing.txt\" | include_file }}",
     "expected_exception": click.ClickException,
     "expected_exception_message": "File not_existing.txt not found"
     },
    {"id": "include_file_with_line_numbers_file_not_found",
     "conditional_expression_only": False,
     "jinja_template": "{{ \"not_existing.txt\" | include_file_with_line_numbers }}",
     "expected_exception": click.ClickException,
     "expected_exception_message": "File not_existing.txt not found"
     },
]
@pytest.mark.parametrize("case", get_get_jinja_env_CASES, ids=[c["id"] for c in get_get_jinja_env_CASES])
def test_get_jinja_env(tmp_path, case):
    from prich.core.engine import get_jinja_env
    jinja_env = get_jinja_env("test_env", case.get("conditional_expression_only"))
    assert jinja_env, "Jinja env is not initialized"
    if case.get("expected_exception"):
        with pytest.raises(case.get("expected_exception")) as e:
            jinja_env.from_string(case.get("jinja_template")).render(case.get("internal_vars", {}))
        if case.get("expected_exception_message"):
            assert case.get("expected_exception_message") in str(e.value)
    else:
        actual = jinja_env.from_string(case.get("jinja_template")).render(case.get("internal_vars", {}))
        if case.get("expected_result") is not None:
            assert actual == case.get("expected_result")


get_should_run_step_CASES = [
    {"id": "true_1==1",
     "when_expr": "1 == 1",
     "expected_result": True
     },
    {"id": "true_1",
     "when_expr": "1",
     "expected_result": True
     },
    {"id": "true",
     "when_expr": "true",
     "expected_result": True
     },
    {"id": "True",
     "when_expr": "True",
     "expected_result": True
     },
    {"id": "false",
     "when_expr": "false",
     "expected_result": False
     },
    {"id": "False",
     "when_expr": "False",
     "expected_result": False
     },
    {"id": "0",
     "when_expr": "False",
     "expected_result": False
     },
    {"id": "false_1!=1",
     "when_expr": "1!=1",
     "expected_result": False
     },
    {"id": "false_p1!=p2",
     "variables": {"p1": 1, "p2": 1},
     "when_expr": "p1!=p2",
     "expected_result": False
     },
    {"id": "true_p1==p2",
     "variables": {"p1": 1, "p2": 1},
     "when_expr": "p1==p2",
     "expected_result": True
     },
    {"id": "true_p1==p2_curly",
     "variables": {"p1": 1, "p2": 1},
     "when_expr": "{{p1==p2}}",
     "expected_result": True
     },
    {"id": "false_p1!=p2_curly",
     "variables": {"p1": 1, "p2": 1},
     "when_expr": "{{p1!=p2}}",
     "expected_result": False
     },
    {"id": "true_p1==p2_curly_w_spaces",
     "variables": {"p1": 1, "p2": 1},
     "when_expr": "{{ p1 == p2 }}",
     "expected_result": True
     },
    {"id": "true_p1!=p2_curly_w_spaces",
     "variables": {"p1": 1, "p2": 1},
     "when_expr": "{{ p1 != p2 }}",
     "expected_result": False
     },
    {"id": "not_defined_variable",
     "when_expr": "something",
     "expected_exception": ValueError,
     "expected_exception_message": "Invalid `when` expression: something - 'something' is undefined"
     },
]
@pytest.mark.parametrize("case", get_should_run_step_CASES, ids=[c["id"] for c in get_should_run_step_CASES])
def test_should_run_step(case):
    from prich.core.engine import should_run_step
    if case.get("expected_exception"):
        with pytest.raises(case.get("expected_exception")):
            should_run_step(case.get("when_expr"), case.get("variables", {}))
    else:
        actual = should_run_step(case.get("when_expr"), case.get("variables", {}))
        if case.get("expected_result") is not None:
            assert actual == case.get("expected_result")


get_validate_step_output_CASES = [
    {"id": "empty",
     "step_validation": None,
     "value": "",
     "expected_result": True,
     },
    {"id": "empty_stepvalidation",
     "step_validation": ValidateStepOutput(),
     "value": "test",
     "expected_result": True,
     },
    {"id": "match",
     "step_validation": ValidateStepOutput(match=".+"),
     "value": "test",
     "expected_result": True,
     },
    {"id": "not_match_startfrom",
     "step_validation": ValidateStepOutput(not_match="^te"),
     "value": "test123",
     "expected_result": False,
     },
    {"id": "match_startfrom",
     "step_validation": ValidateStepOutput(match="^te"),
     "value": "test123",
     "expected_result": True,
     },
]
@pytest.mark.parametrize("case", get_validate_step_output_CASES, ids=[c["id"] for c in get_validate_step_output_CASES])
def test_validate_step_output(case):
    from prich.core.engine import validate_step_output
    if case.get("expected_exception"):
        with pytest.raises(case.get("expected_exception")):
            validate_step_output(case.get("step_validation"), case.get("value", {}), {})
    else:
        actual = validate_step_output(case.get("step_validation"), case.get("value", {}), {})
        if case.get("expected_result") is not None:
            assert actual == case.get("expected_result")

get_run_command_step_CASES = [
    {"id": "python_step_file_not_found",
     "template": generate_template(template_id="test-template"),
     "step": PythonStep(name="test", type="python", call="test.py"),
     "mock_output": CompletedProcess(args=["python", "test.py"], returncode=0, stdout="hello"),
     "expected_exception": click.ClickException,
     "expected_exception_message": "Python script not found: test/templates/test-template/scripts/test.py"
     },
    {"id": "python_step_file_not_found_isolated_venv",
     "template": generate_template(template_id="test-template", isolated_venv=True),
     "step": PythonStep(name="test", type="python", call="test.py"),
     "mock_output": CompletedProcess(args=["python", "test.py"], returncode=0, stdout="hello"),
     "expected_exception": click.ClickException,
     "expected_exception_message": "Python script not found: test/templates/test-template/scripts/test.py"
     },
    {"id": "command_step",
     "template": generate_template(template_id="test-template"),
     "step": CommandStep(name="test", type="command", call="echo", args=["hello"]),
     "mock_output": CompletedProcess(args=["echo", "hello"], returncode=0, stdout="hello"),
     "expected_result": "hello",
     "expected_exitcode": 0,
     },
    {"id": "command_step_exitcode1",
     "template": generate_template(template_id="test-template"),
     "step": CommandStep(name="test", type="command", call="echo", args=["hello"]),
     "mock_output": CompletedProcess(args=["echo", "hello"], returncode=1, stdout="hello"),
     "expected_result": "hello",
     "expected_exitcode": 1,
     },
    {"id": "command_step_cmd_not_exist",
     "template": generate_template(template_id="test-template"),
     "step": CommandStep(name="test", type="command", call="notexistingcommand", args=["hello"]),
     "expected_exception": click.ClickException,
     "expected_exception_message": "Unexpected error in notexistingcommand: [Errno 2] No such file or directory: 'notexistingcommand'"
     },
]
@pytest.mark.parametrize("case", get_run_command_step_CASES, ids=[c["id"] for c in get_run_command_step_CASES])
def test_run_command_step(case, monkeypatch):
    from prich.core.engine import run_command_step

    if case.get("mock_output"):
        monkeypatch.setattr("subprocess.run", lambda cmd, stdout, stderr, text, check, env: case.get("mock_output", None))

    if case.get("expected_exception"):
        with pytest.raises(case.get("expected_exception")) as e:
            run_command_step(case.get("template"), case.get("step"), case.get("variables", {}))
        if case.get("expected_exception_message"):
            assert str(e.value) in case.get("expected_exception_message")
    else:
        actual, actual_exitcode = run_command_step(case.get("template"), case.get("step"), case.get("variables", {}))
        if case.get("expected_result") is not None:
            assert actual == case.get("expected_result")
        if case.get("expected_exitcode") is not None:
            assert actual_exitcode == case.get("expected_exitcode")


def test_render_prompt_fields():
    from prich.core.engine import render_prompt_fields

    with pytest.raises(click.ClickException) as e:
        render_prompt_fields(
            LLMStep(type="llm", name="test",
                    instructions="{{ system }}"
            ),
            {"system": "system"}
        )
    assert "There should be at least an 'input' field." in str(e.value)

    # with pytest.raises(click.ClickException) as e:
    #     render_prompt_fields(
    #         LLMStep(type="llm", name="test",
    #             instructions="{{ system }}",
    #             # TODO: was prompt
    #             input="{{ prompt }}"
    #         ),
    #         {"system": "system", "prompt": "prompt"})
    # assert "There should be Prompt or User or System and User fields." in str(e.value)

    llm_step = LLMStep(type="llm", name="test",
                       instructions="{{ system }}",
                       input="{{ user }}")
    render_prompt_fields(llm_step, {"system": "system", "user": "user"})
    assert llm_step.rendered_instructions == "system"
    assert llm_step.rendered_input == "user"
    assert llm_step.rendered_prompt is None

    llm_step = LLMStep(type="llm", name="test",
                       input="{{ user }}")
    render_prompt_fields(llm_step, {"user": "user"})
    assert llm_step.rendered_instructions is None
    assert llm_step.rendered_input == "user"
    assert llm_step.rendered_prompt is None

    # llm_step = LLMStep(type="llm", name="test",
    #                    prompt="{{ prompt }}")
    # render_prompt_fields(llm_step, {"prompt": "prompt"})
    # assert llm_step.rendered_input == "prompt"

def test_get_variable_type():
    from prich.core.engine import get_variable_type
    assert get_variable_type("str") == click.STRING
    assert get_variable_type("int") == click.INT
    assert get_variable_type("bool") == click.BOOL
    assert get_variable_type("path") == click.Path


def test_create_dynamic_command(basic_config, template):
    from prich.core.engine import create_dynamic_command
    template.variables.append(VariableDefinition(
        name="filelist",
        type="list[str]",
        cli_option="--filelist"
    ))
    actual = create_dynamic_command(basic_config, template)
    assert actual