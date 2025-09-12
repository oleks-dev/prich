import re
import venv
import click
import pytest
from pathlib import Path
from click.testing import CliRunner
from prich.cli.run import run_group

from prich.models.file_scope import FileScope

from prich.cli.config import list_providers, show_config, edit_config
from prich.core.engine import run_template
from prich.core.state import _loaded_templates
from prich.models.template import TemplateModel, VariableDefinition, PythonStep, CommandStep, LLMStep, \
    RenderStep, ValidateStepOutput, ExtractVarModel
from prich.models.text_filter_model import TextFilterModel
from tests.fixtures.config import basic_config  # noqa: F811
from tests.fixtures.paths import mock_paths  # noqa: F811
from tests.fixtures.templates import template  # noqa: F811
from tests.utils.utils import capture_stdout

get_run_template_CASES = [
    {"id": "valid_one_llm_step", "template":
        # TemplateModel(
        {
            "id": "test-tpl",
            "name": "Test TPL",
            "steps":[
                LLMStep(
                    name="Ask",
                    type="llm",
                    instructions="system",
                    input="user"
                )
            ]
        # ),
        },
      "expected_exception": None,
      "expected_exception_message": None,
    },
    {"id": "valid_llm_step_and_python_cmd_and_render", "template":
        # TemplateModel(
        {
            "id": "test-tpl",
            "name": "Test TPL",
            "steps": [
                PythonStep(
                    name="Preprocess python",
                    type="python",
                    call="echo.py",
                    args=["test"]
                ),
                CommandStep(
                    name="Preprocess command",
                    type="command",
                    call="echo",
                    args=["test"]
                ),
                CommandStep(
                    name="Preprocess shell script",
                    type="command",
                    call="echo.sh",
                    args=["test"]
                ),
                RenderStep(
                    name="Preprocess render",
                    type="render",
                    template="{{ builtin.now }}"
                ),
                LLMStep(
                    name="Ask",
                    type="llm",
                    instructions="system",
                    input="user",
                    output_file="test_llm_response.txt"
                ),
            ],
            "folder": "."
        # ),
        },
      "expected_exception": None,
      "expected_exception_message": None,
    },
    {"id": "no_template_folder_set", "template":
        # TemplateModel(
        {
            "id": "test-tpl",
            "name": "Test TPL",
            "steps": [
                CommandStep(
                    name="Preprocess command",
                    type="command",
                    call="echo",
                    args=["test"]
                ),
            ],
        # ),
        },
      "expected_exception": click.ClickException,
      "expected_exception_message": "Template folder was not detected properly",
    },
    {"id": "no_python_script_found", "template":
        # TemplateModel(
        {
            "id": "test-tpl",
            "name": "Test TPL",
            "steps": [
                PythonStep(
                    name="Preprocess python",
                    type="python",
                    call="notexisting.py",
                    args=["test"]
                ),
            ],
            "folder": "."
        # ),
        },
      "expected_exception": click.ClickException,
      "expected_exception_message": "Python script not found",
    },
    {"id": "non_python_script_found", "template":
        # TemplateModel(
        {
            "id": "test-tpl",
            "name": "Test TPL",
            "steps": [
                PythonStep(
                    name="Preprocess python",
                    type="python",
                    call="echo.sh",
                    args=["test"]
                ),
            ],
            "folder": "."
        # ),
        },
      "expected_exception": click.ClickException,
      "expected_exception_message": "Python script file should end with .py",
    },
    {"id": "cmd_exec_error", "template":
        # TemplateModel(
        {
            "id": "test-tpl",
            "name": "Test TPL",
            "steps": [
                CommandStep(
                    name="Preprocess command",
                    type="command",
                    call="echo_error.sh",
                    args=["test"]
                ),
            ],
            "folder": "."
        # ),
        },
    },
    {"id": "no_cmd_found", "template":
        # TemplateModel(
        {
            "id": "test-tpl",
            "name": "Test TPL",
            "steps": [
                CommandStep(
                    name="Preprocess command",
                    type="command",
                    call="noecho.sh",
                    args=["test"]
                ),
            ],
            "folder": "."
        # ),
        },
      "expected_exception": click.ClickException,
      "expected_exception_message": "No such file or directory",
    },
    {"id": "no_python_isolated_venv_found", "template":
        # TemplateModel(
        {
            "id": "test-tpl",
            "name": "Test TPL",
            "venv": "isolated",
            "steps": [
                PythonStep(
                    name="Preprocess python",
                    type="python",
                    call="echo.py",
                    args=["test"]
                ),
            ],
            "folder": "."
        # ),
        },
      "expected_exception": click.ClickException,
      "expected_exception_message": "Isolated venv python not found",
    },
    {"id": "valid_one_llm_step_w_vars", "template":
        # TemplateModel(
        {
            "id": "test-tpl",
            "name": "Test TPL",
            "steps": [
                LLMStep(
                    name="Ask",
                    type="llm",
                    instructions="system: test_var1='{{ test_var1 }}'; test_var2='{{ test_var2 }}'; test_var3='{{ test_var3 }}'; test_var4='{{ test_var4 }}'; test_var5='{% for test_var5_item in test_var5 %}{{ test_var5_item }}{% endfor %}'; test_var6='{% for test_var6_item in test_var6 %}{{ test_var6_item }}{% endfor %}';",
                    input="user: test_var1='{{ test_var1 }}'; test_var2='{{ test_var2 }}'; test_var3='{{ test_var3 }}'; test_var4='{{ test_var4 }}'; test_var5='{% for test_var5_item in test_var5 %}{{ test_var5_item }}{% endfor %}'; test_var6='{% for test_var6_item in test_var6 %}{{ test_var6_item }}{% endfor %}';",
                )
            ],
            "variables": [
                VariableDefinition(
                    name="test_var1",
                    type="str",
                    description="test_var1 description",
                    default="test_var1_val",
                ),
                VariableDefinition(
                    name="test_var2",
                    type="int",
                    description="test_var2 description",
                    default=10,
                ),
                VariableDefinition(
                    name="test_var3",
                    type="bool",
                    description="test_var3 description",
                    default=True,
                ),
                VariableDefinition(
                    name="test_var4",
                    type="path",
                    description="test_var4 description",
                    default="./test",
                ),
                VariableDefinition(
                    name="test_var5",
                    type="list[str]",
                    description="test_var5 description",
                    default=["test_l1", "test_l2"],
                ),
                VariableDefinition(
                    name="test_var6",
                    type="list[int]",
                    description="test_var6 description",
                    default=[1, 2],
                ),
            ]
        # ),
        },
      "expected_exception": None,
      "expected_exception_message": None,
    },
    {"id": "no_steps", "template":
        # TemplateModel(
        {
            "id": "test-tpl",
            "name": "Test TPL",
            "steps": []
        # ),
        },
      "expected_exception": click.ClickException,
      "expected_exception_message": "No steps found in template test-tpl.",
     },
    {"id": "run_python_and_validate_error", "template":
        # TemplateModel(
        {
            "id": "test-tpl",
            "name": "Test TPL",
            "steps": [
                PythonStep(
                    name="Preprocess python",
                    type="python",
                    call="echo.py",
                    args=["test"],
                    validate=ValidateStepOutput(
                        match="^est",
                        not_match="test",
                        on_fail="error"
                    )
                ),
            ],
            "folder": "."
        # ),
        },
     "expected_exception": click.ClickException,
     "expected_exception_message": "Validation failed for step output",
     },
    {"id": "run_cmd_and_validate_error_and_exitcode", "template":
        # TemplateModel(
        {
            "id": "test-tpl",
            "name": "Test TPL",
            "steps": [
                CommandStep(
                    name="Preprocess python",
                    type="command",
                    call="python",
                    args=["notpresent"],
                    validate=ValidateStepOutput(
                        not_match="test12345",
                        match_exit_code=2,
                        on_fail="error"
                    )
                ),
            ],
            "folder": "."
        # ),
        },
     },
    {"id": "run_cmd_and_validate_error_and_exitcode_str", "template":
        # TemplateModel(
        {
            "id": "test-tpl",
            "name": "Test TPL",
            "steps": [
                CommandStep(
                    name="Preprocess python",
                    type="command",
                    call="python",
                    args=["notpresent"],
                    validate=ValidateStepOutput(
                        not_match="test12345",
                        match_exit_code="{{test_error_code}}",
                        on_fail="error"
                    )
                ),
            ],
            "variables": [
                VariableDefinition(
                    name="test_error_code",
                    type="int",
                    default=2
                )
            ],
            "folder": "."
        # ),
        },
     },
    {"id": "run_cmd_and_validate_error_and_fail_exitcode", "template":
        # TemplateModel(
        {
            "id": "test-tpl",
            "name": "Test TPL",
            "steps": [
                CommandStep(
                    name="Preprocess python",
                    type="command",
                    call="echo1",
                    args=["test"],
                    validate=ValidateStepOutput(
                        match="No such file or directory: 'echo1'",
                        not_match="test",
                        match_exit_code=1,
                        on_fail="error"
                    )
                ),
            ],
            "folder": "."
        # ),
        },
     "expected_exception": click.ClickException,
     "expected_exception_message": "No such file or directory: 'echo1'",
     },
    {"id": "run_cmd_and_validate_fail_exitcode_format", "template":
        # TemplateModel(
        {
            "id": "test-tpl",
            "name": "Test TPL",
            "steps": [
                CommandStep(
                    name="Preprocess python",
                    type="command",
                    call="echo",
                    args=["test"],
                    validate=ValidateStepOutput(
                        match="No such file or directory: 'echo1'",
                        not_match="test",
                        match_exit_code="hello",
                        on_fail="error"
                    )
                ),
            ],
            "folder": "."
        # ),
        },
     "expected_exception": click.ClickException,
     "expected_exception_message": "invalid literal for int()",
     },
    {"id": "run_cmd_and_validate_error_and_exitcode", "template":
        # TemplateModel(
        {
            "id": "test-tpl",
            "name": "Test TPL",
            "steps": [
                PythonStep(
                    name="Preprocess python",
                    type="python",
                    call="echo.py",
                    args=["test"],
                    validate=ValidateStepOutput(
                        match="^est",
                        not_match="test",
                        match_exit_code=0,
                        on_fail="error"
                    )
                ),
            ],
            "folder": "."
        # ),
        },
     "expected_exception": click.ClickException,
     "expected_exception_message": "Validation failed for step output",
     },
    {"id": "run_cmd_and_validate_warn", "template":
        # TemplateModel(
        {
            "id": "test-tpl",
            "name": "Test TPL",
            "steps": [
                PythonStep(
                    name="Preprocess python",
                    type="python",
                    call="echo.py",
                    args=["test"],
                    validate=ValidateStepOutput(
                        match="^est",
                        not_match="test",
                        on_fail="warn"
                    )
                ),
            ],
            "folder": "."
        # ),
        },
         "expected_output": [
             "Preprocess python\ntest\n\nWarning: Validation failed for step output!\n"
         ]
     },
    {"id": "run_cmd_and_validate_skip", "template":
        # TemplateModel(
        {
            "id": "test-tpl",
            "name": "Test TPL",
            "steps": [
                PythonStep(
                    name="Preprocess python",
                    type="python",
                    call="echo.py",
                    args=["test"],
                    validate=ValidateStepOutput(
                        match="^est",
                        not_match="test",
                        on_fail="skip"
                    )
                ),
            ],
            "folder": "."
        # ),
        },
         "expected_output": [
             "Validation failed for step output – skipping next steps.\n"
         ]
     },
    {"id": "run_cmd_and_validate_continue", "template":
        # TemplateModel(
        {
            "id": "test-tpl",
            "name": "Test TPL",
            "steps": [
                PythonStep(
                    name="Preprocess python",
                    type="python",
                    call="echo.py",
                    args=["test"],
                    validate=ValidateStepOutput(
                        match="^est",
                        not_match="test",
                        on_fail="continue"
                    )
                ),
            ],
            "folder": "."
        # ),
        },
         "expected_output": [
             "Preprocess python\ntest\n\nValidation failed for step output \u2013 continue.\n"
         ]
     },
    {"id": "run_cmd_and_validate_passed", "template":
        # TemplateModel(
        {
            "id": "test-tpl",
            "name": "Test TPL",
            "steps": [
                PythonStep(
                    name="Preprocess python",
                    type="python",
                    call="echo.py",
                    args=["test"],
                    validate=ValidateStepOutput(
                        match="^test",
                        not_match="echo",
                        on_fail="error"
                    )
                ),
            ],
            "folder": "."
        # ),
        },
         "expected_output": [
             "Preprocess python\ntest\n"
         ]
     },
    {"id": "run_cmd_and_strip_prefix", "template":
        # TemplateModel(
        {
            "id": "test-tpl",
            "name": "Test TPL",
            "steps": [
                PythonStep(
                    name="Preprocess python",
                    type="python",
                    call="echo.py",
                    args=["test"],
                    filter=TextFilterModel(strip_prefix="te"),
                    validate=ValidateStepOutput(
                        match="^st",
                        not_match="echo",
                        on_fail="error"
                    )
                ),
            ],
            "folder": "."
        # ),
        },
         "expected_output": [
             "Preprocess python\nst\n"
         ]
     },
    {"id": "run_cmd_and_strip_output", "template":
        # TemplateModel(
        {
            "id": "test-tpl",
            "name": "Test TPL",
            "steps": [
                PythonStep(
                    name="Preprocess python",
                    type="python",
                    call="echo.py",
                    args=[" test "],
                    filter=TextFilterModel(strip=True),
                    validate=ValidateStepOutput(
                        match="^test",
                        not_match="echo",
                        on_fail="error"
                    )
                ),
            ],
            "folder": "."
        # ),
        },
     "expected_output": [
         "Preprocess python\ntest\n"
     ]
     },
    {"id": "run_cmd_and_output_regex_group1", "template":
        # TemplateModel(
        {
            "id": "test-tpl",
            "name": "Test TPL",
            "steps": [
                PythonStep(
                    name="Preprocess python",
                    type="python",
                    call="echo.py",
                    args=[" test "],
                    filter=TextFilterModel(regex_extract="(es)"),
                    validate=ValidateStepOutput(
                        match="^es",
                        not_match="echo",
                        on_fail="error"
                    )
                ),
            ],
            "folder": "."
        # ),
        },
     "expected_output": [
         "Preprocess python\nes\n"
     ]
     },
    {"id": "run_cmd_and_output_regex_group0", "template":
        # TemplateModel(
        {
            "id": "test-tpl",
            "name": "Test TPL",
            "steps": [
                PythonStep(
                    name="Preprocess python",
                    type="python",
                    call="echo.py",
                    args=[" test "],
                    filter=TextFilterModel(regex_extract="es"),
                    validate=ValidateStepOutput(
                        match="^es",
                        not_match="echo",
                        on_fail="error"
                    )
                ),
            ],
            "folder": "."
        # ),
        },
        "expected_output": [
            "Preprocess python\nes\n"
         ]
     },
    {"id": "run_cmd_and_output_extract_vars", "template":
        # TemplateModel(
        {
            "id": "test-tpl",
            "name": "Test TPL",
            "steps": [
                PythonStep(
                    name="Preprocess python",
                    type="python",
                    call="echo.py",
                    args=["test test test"],
                    extract_variables=[ExtractVarModel(
                        regex="(test) ",
                        variable="test"
                    ), ExtractVarModel(
                        regex="notfound",
                        variable="not_found_test"
                    ), ExtractVarModel(
                        regex="(test)",
                        variable="test_list",
                        multiple=True
                    ), ExtractVarModel(
                        regex="notfound",
                        variable="notfound_list",
                        multiple=True
                    )],
                    validate=ValidateStepOutput(
                        match="test test test",
                        not_match="echo",
                        on_fail="error"
                    )
                ),
            ],
            "folder": "."
        # ),
        },
         "is_verbose": True,
         "expected_output": [
             "• Step #1: Preprocess python\n",
             "Output:\ntest test test\n",
             "Inject '(test) ' → test: 'test'\n",
             "Inject 'notfound' → not_found_test: ''\n",
             "Inject '(test)' (3 matches) → test_list: [\'test\', \'test\', \'test\']\n",
             "Inject 'notfound' (0 matches) → notfound_list: []\n",
             "test test test\n\nValidation completed.\n"
         ]
     },
    {"id": "run_cmd_and_slice", "template":
        # TemplateModel(
        {
            "id": "test-tpl",
            "name": "Test TPL",
            "steps": [
                PythonStep(
                    name="Preprocess python",
                    type="python",
                    call="echo.py",
                    args=["test"],
                    filter=TextFilterModel(
                        slice_start=1,
                        slice_end=-1
                    ),
                    validate=ValidateStepOutput(
                        match="^es$",
                        not_match="echo",
                        on_fail="error"
                    )
                ),
            ],
            "folder": "."
        # ),
        },
         "expected_output": [
             "• Preprocess python\nes\n"
         ]
     },
    {"id": "run_cmd_and_slice_start", "template":
        # TemplateModel(
        {
            "id": "test-tpl",
            "name": "Test TPL",
            "steps": [
                PythonStep(
                    name="Preprocess python",
                    type="python",
                    call="echo.py",
                    args=["test"],
                    filter=TextFilterModel(
                        slice_start=1
                    ),
                    validate=ValidateStepOutput(
                        match="^est$",
                        not_match="echo",
                        on_fail="error"
                    )
                ),
            ],
            "folder": "."
        # ),
        },
         "expected_output": [
             "• Preprocess python\nest\n"
         ]
     },
    {"id": "run_cmd_and_slice_end", "template":
        # TemplateModel(
        {
            "id": "test-tpl",
            "name": "Test TPL",
            "steps": [
                PythonStep(
                    name="Preprocess python",
                    type="python",
                    call="echo.py",
                    args=["test"],
                    filter=TextFilterModel(
                        slice_end=-1
                    ),
                    validate=ValidateStepOutput(
                        match="^tes$",
                        not_match="echo",
                        on_fail="error"
                    )
                ),
            ],
            "folder": "."
        # ),
        },
        "expected_output": [
            "• Preprocess python\ntes\n"
        ]
     },
    {"id": "run_cmd_and_slice_end_verbose", "template":
        # TemplateModel(
        {
            "id": "test-tpl",
            "name": "Test TPL",
            "steps": [
                PythonStep(
                    name="Preprocess python",
                    type="python",
                    call="echo.py",
                    args=["test"],
                    filter=TextFilterModel(
                        slice_end=-1
                    ),
                    validate=ValidateStepOutput(
                        match="^tes$",
                        not_match="echo",
                        on_fail="error"
                    )
                ),
            ],
            "folder": "."
        # ),
        },
        "is_verbose": True,
        "expected_output": [
            "• Step #1: Preprocess python\n",
            "Output:\ntest\n",
            "Strip output spaces: True\n",
            "Slice output text to -1\n",
            "tes\n",
            "Validation completed.\n"
        ]
     },
    {"id": "run_cmd_and_sanitize_output", "template":
        # TemplateModel(
        {
            "id": "test-tpl",
            "name": "Test TPL",
            "steps": [
                PythonStep(
                    name="Preprocess python",
                    type="python",
                    call="echo.py",
                    args=["{\"password\": \"secret\"}"],
                    filter=TextFilterModel(
                        regex_replace=[("(?i)(\"password\"\\s*:\\s*\")[^\"]+(\")", r"\1*****\2")]
                    ),
                ),
            ],
            "folder": "."
        # ),
        },
        "expected_output": ["• Preprocess python", "{\"password\": \"*****\"}"]
     },
    {"id": "run_cmd_and_sanitize_output_verbose", "template":
        # TemplateModel(
        {
            "id": "test-tpl",
            "name": "Test TPL",
            "steps": [
                PythonStep(
                    name="Preprocess python",
                    type="python",
                    call="echo.py",
                    args=["{\"password\": \"secret\"}"],
                    filter=TextFilterModel(
                        regex_replace=[("(?i)(\"password\"\\s*:\\s*\")[^\"]+(\")", r"\1*****\2")]
                    ),
                ),
            ],
            "folder": "."
        # ),
        },
        "is_verbose": True,
        "expected_output": [
            "• Step #1: Preprocess python",
            "Output:\n{\"password\": \"secret\"}\n",
            "Apply regex replace: '(?i)(\"password\"\\s*:\\s*\")[^\"]+(\")' → '\\1*****\\2'\n"
            "{\"password\": \"*****\"}"],
        "args": ["--verbose"]
     },
    {"id": "run_cmd_and_save_output", "template":
        # TemplateModel(
        {
            "id": "test-tpl",
            "name": "Test TPL",
            "steps": [
                PythonStep(
                    name="Preprocess python",
                    type="python",
                    call="echo.py",
                    args=["test"],
                    output_variable="test_var",
                    output_file="haudfhiu!@#±%#@$^%^(*0=/////"
                ),
            ],
            "folder": "."
        # ),
        },
     "expected_exception": click.ClickException,
     "expected_exception_message": "Failed to save output to file",
     },
]
@pytest.mark.parametrize("case", get_run_template_CASES, ids=[c["id"] for c in get_run_template_CASES])
def test_run_template(case, monkeypatch, basic_config):
    test_template = TemplateModel(
            id= "test-tpl",
            name= "Test TPL",
            steps= [
                PythonStep(
                    name="Preprocess python",
                    type="python",
                    call="echo.py",
                    args=["test"],
                    output_variable="test_var"
                ),
            ],
        )
        # },

    for k,v in case.get("template").items():
        test_template.__setattr__(k, v)
    if test_template.folder == ".":
        test_template.folder = str(Path(__file__).parent.resolve())
    _loaded_templates.clear()
    _loaded_config = None
    _loaded_templates[test_template.id] = test_template

    from prich.core.state import _loaded_config_paths

    monkeypatch.setattr("prich.core.loaders.get_loaded_config", lambda: (basic_config, _loaded_config_paths))
    monkeypatch.setattr("prich.core.loaders.load_merged_config", lambda: (basic_config, _loaded_config_paths))
    monkeypatch.setattr("prich.core.engine.is_verbose", lambda: case.get("is_verbose", False))

    if case.get("expected_exception") is not None:
        with pytest.raises(click.ClickException) as e:
            run_template(test_template.id)
        if case.get("expected_exception_message") is not None:
            assert case.get("expected_exception_message") in str(e.value)
    else:
        result, out = capture_stdout(run_template, test_template.id)
        if case.get("expected_output"):
            if isinstance(case.get("expected_output"), str):
                case["expected_output"] = [case.get("expected_output")]
            for expected in case["expected_output"]:
                assert expected in out


get_run_template_cli_CASES = [
    {"id": "run_local_template_id", "add_template": True, "args": ["template-local"],
     "expected_output": "• llm step"},
    {"id": "run_local_template_id_verbose", "add_template": True, "args": ["template-local", "--verbose"],
     "extend_steps": [{"type": "render", "name": "render text", "template": "hello {{name}}"}],
     "expected_output": ["Template: tpl (1.0), local", "• Step #1:"]},
    {"id": "run_global_template_id_verbose", "add_template": True, "args": ["template-global", "--verbose"],
     "expected_output": ["Template: tpl (1.0), global", "• Step #1:"]},
    {"id": "run_local_template_id_final", "add_template": True, "args": ["template-local", "--only-final-output"],
     "expected_regex_output": ["^### System(?:.|\\n)+### Assistant:\\n$"]},
    {"id": "run_local_template_id_quiet", "add_template": True, "args": ["template-local", "--quiet"],
     "expected_regex_output": ["^$"]},
]
@pytest.mark.parametrize("case", get_run_template_cli_CASES, ids=[c["id"] for c in get_run_template_cli_CASES])
def test_run_template_cli(mock_paths, monkeypatch, case, template, basic_config):
    global_dir = mock_paths.home_dir
    local_dir = mock_paths.cwd_dir

    monkeypatch.setattr(Path, "home", lambda: global_dir)
    monkeypatch.setattr(Path, "cwd", lambda: local_dir)

    monkeypatch.setattr("prich.core.loaders.get_cwd_dir", lambda: local_dir)
    monkeypatch.setattr("prich.core.loaders.get_home_dir", lambda: global_dir)

    local_config = basic_config.model_copy(deep=True)
    global_config = basic_config.model_copy(deep=True)
    local_config.save("local")
    global_config.save("global")

    if case.get("add_template"):
        template_local = template.model_copy(deep=True)
        template_global = template.model_copy(deep=True)
        template_local.id = "template-local"
        template_global.id = "template-global"
        if case.get("override_venv"):
            template_local.venv = case.get("override_venv")
            template_global.venv = case.get("override_venv")
        if case.get("extend_steps"):
            for step in case.get("extend_steps"):
                if step.get("type") == "python":
                    template_local.steps.append(PythonStep(**step))
                    template_global.steps.append(PythonStep(**step))
                elif step.get("type") == "command":
                    template_local.steps.append(CommandStep(**step))
                    template_global.steps.append(CommandStep(**step))
                elif step.get("type") == "render":
                    template_local.steps.append(RenderStep(**step))
                    template_global.steps.append(RenderStep(**step))
                else:
                    raise RuntimeError(f"override_steps step type is not supported: {step}")
        template_local.save(FileScope.LOCAL)
        template_global.save(FileScope.GLOBAL)

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=mock_paths.home_dir):
        result = runner.invoke(run_group, case.get("args"))
        if case.get("expected_output") is not None:
            if isinstance(case.get("expected_output"), str):
                case["expected_output"] = [case.get("expected_output")]
            for expected_output in case.get("expected_output"):
                assert expected_output in result.output.replace("\n", "")
        if case.get("expected_regex_output"):
            for expected_regex_output in case.get("expected_regex_output"):
                assert re.search(expected_regex_output, result.output)

def test_run_template_shared_venv(monkeypatch, template, basic_config, mock_paths):
    template.name = 'test_shared_venv_tpl'
    template.id = 'test_shared_venv_tpl'
    template.file = str(Path(mock_paths.prich.local_templates / "shared_venv_tpl" / "shared_venv_tpl.yaml"))
    template.folder = str(Path(mock_paths.prich.local_templates / "shared_venv_tpl"))
    template.venv = "shared"
    template.steps.insert(0, PythonStep(name="python step", call="test.py", type="python", args=[], output_variable="test_output"))

    _loaded_templates.clear()
    _loaded_config = None
    _loaded_templates[template.id] = template

    from prich.core.state import _loaded_config_paths

    monkeypatch.setattr("prich.core.loaders.get_loaded_config", lambda: (basic_config, _loaded_config_paths))
    monkeypatch.setattr("prich.core.loaders.load_merged_config", lambda: (basic_config, _loaded_config_paths))

    # Place dummy preprocess script inside the template
    venv_dir = Path(template.folder).parent.parent / "venv"
    venv.create(venv_dir, with_pip=False)

    tpl_script_path = Path(template.folder) / "scripts" / "test.py"
    print(tpl_script_path)
    tpl_script_path.parent.mkdir(parents=True, exist_ok=True)
    tpl_script_path.write_text("""import sys; print('Preprocess OK')""")

    run_template(template.id, name="Test")

def test_run_template_isolated_venv(monkeypatch, template, basic_config, mock_paths):
    template.id = 'test_isolated_venv_tpl'
    template.name = 'test_isolated_venv_tpl'
    template.file = str(Path(mock_paths.prich.local_templates / "isolated_venv_tpl" / "isolated_venv_tpl.yaml"))
    template.folder = str(Path(mock_paths.prich.local_templates / "isolated_venv_tpl"))
    template.venv = "isolated"
    template.steps.insert(0, PythonStep(name="python step", call="test.py", type="python", args=[], output_variable="test_output"))
    _loaded_templates.clear()
    _loaded_config = None
    _loaded_templates[template.id] = template

    from prich.core.state import _loaded_config_paths

    monkeypatch.setattr("prich.core.loaders.get_loaded_config", lambda: (basic_config, _loaded_config_paths))
    monkeypatch.setattr("prich.core.loaders.load_merged_config", lambda: (basic_config, _loaded_config_paths))

    # Place dummy preprocess script inside the template
    venv_dir = Path(template.folder) / "scripts" / "venv"
    venv.create(venv_dir, with_pip=True)
    tpl_script_path = Path(template.folder) / "scripts" / "test.py"
    print(tpl_script_path)
    tpl_script_path.parent.mkdir(parents=True, exist_ok=True)
    tpl_script_path.write_text("""import sys; print('Preprocess OK')""")

    run_template(template.id, name="Test")

def test_run_template_shell_call(monkeypatch, template, basic_config, tmp_path):
    template.name = 'test_cmd_tpl'
    template.file = str(tmp_path / "test_cmd_tpl.yaml")
    template.steps.insert(0, CommandStep(name="shell call", call="date", type="command", args=["-u"], output_variable="test_output"))
    _loaded_templates.clear()
    _loaded_config = None
    _loaded_templates[template.id] = template

    from prich.core.state import _loaded_config_paths

    monkeypatch.setattr("prich.core.loaders.get_loaded_config", lambda: (basic_config, _loaded_config_paths))
    monkeypatch.setattr("prich.core.loaders.load_merged_config", lambda: (basic_config, _loaded_config_paths))

    run_template(template.id, name="Test")

def test_invalid_template_missing_required_variable(monkeypatch, basic_config, tmp_path):
    tpl = TemplateModel(
        schema_version="1.0",
        version="1.0",
        id="missing_var",
        name="missing var",
        description="Invalid template",
        tags=[],
        variables=[
            VariableDefinition(name="must_be_set", type="str", required=True)
        ],
        steps=[
          LLMStep(
              name="llm_step",
              type="llm",
              input="Hello {{ must_be_set }}"
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
    _loaded_templates[template.id] = template

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
    _loaded_templates[template.id] = template

    from prich.core.state import _loaded_config_paths

    monkeypatch.setattr("prich.cli.config.get_loaded_config", lambda: (basic_config, _loaded_config_paths))
    monkeypatch.setattr("prich.core.loaders.load_merged_config", lambda: (basic_config, _loaded_config_paths))

    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(show_config, [param] if param else [])
        assert result.exit_code == 0
        assert "Configs:" in result.output
        assert basic_config.as_yaml().replace('\n', '') in result.output.replace('\n', '')

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
    _loaded_templates[template.id] = template

    from prich.core.state import _loaded_config_paths
    _loaded_config_paths = [Path(tmp_path)]

    monkeypatch.setattr("prich.cli.config.load_local_config", lambda: (basic_config, _loaded_config_paths[0]))
    monkeypatch.setattr("prich.cli.config.load_global_config", lambda: (global_config, _loaded_config_paths[0]))

    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(edit_config, [param] if param else [])
        assert result.exit_code == 0
        assert f"Executing: {'echo' if param == '-l' else 'ls' if param == '-g' else 'echo'}" in result.output
