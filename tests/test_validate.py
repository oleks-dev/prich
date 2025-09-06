from pathlib import Path
import pytest
from click.testing import CliRunner
from prich.models.template import CommandStep, PythonStep
from prich.models.file_scope import FileScope

from prich.cli.validate import validate_templates
from tests.fixtures.templates import template
from tests.fixtures.config import basic_config
from tests.fixtures.paths import mock_paths

get_validate_template_CASES = [
    {"id": "local_and_global_params", "args": ["-g", "-l"],
     "expected_output": "Error: Use only one local or global option"},
    {"id": "file_with_local_param", "args": ["--file", "test.yaml", "-l"],
     "expected_output": "When YAML file is selected it doesn't combine with local, global, or id options"},
    {"id": "file_with_global_param", "args": ["--file", "test.yaml", "-g"],
     "expected_output": "When YAML file is selected it doesn't combine with local, global, or id options"},
    {"id": "file_with_template_id_param", "args": ["--file", "test.yaml", "--id", "test-template"],
     "expected_output": "When YAML file is selected it doesn't combine with local, global, or id options"},
    {"id": "file_not_present", "args": ["--file", "test.yaml"],
     "expected_output": "Failed to find test.yaml template file."},
    {"id": "no_templates_found", "args": [],
     "expected_output": "No Templates found."},
    {"id": "no_template_if_found", "args": ["--id", "test-template"],
     "expected_output": "Failed to find template with id: test-template"},
    {"id": "local_template_id", "add_template": True, "args": ["--id", "template-local"],
     "expected_output": "- template-local (local)"},
    {"id": "local_template_id_w_local", "add_template": True, "args": ["--id", "template-local", "-l"],
     "expected_output": "- template-local (local)"},
    {"id": "local_template_id_w_global_not_found", "add_template": True, "args": ["--id", "template-local", "-g"],
     "expected_output": "Failed to find template with id: template-local"},
    {"id": "global_template_id", "add_template": True, "args": ["--id", "template-global"],
     "expected_output": "- template-global (global)"},
    {"id": "global_template_id_w_local_not_found", "add_template": True, "args": ["--id", "template-global", "-l"],
     "expected_output": "Failed to find template with id: template-global"},
    {"id": "local_template_wrong", "add_wrong_template": True, "args": [],
     "expected_output": "tpl-local-wrong.yaml: is not valid"},
    {"id": "local_template_not_found_command", "add_template": True, "args": [],
     "override_steps": [
         { "type": "command",
           "name": "step1",
           "call": "echo1",
           "args": []
         },
         { "type": "command",
           "name": "step2",
           "call": "echo2",
           "args": []
         }
     ],
     "expected_output": [
         "template-global.yaml: is valid",
         "Failed to find call command file ~/.prich/templates/template-global/scripts/echo1",
         "Failed to find call command file ~/.prich/templates/template-global/scripts/echo2",
         "template-local.yaml: is valid",
         "Failed to find call command file ./.prich/templates/template-local/scripts/echo1",
         "Failed to find call command file ./.prich/templates/template-local/scripts/echo2",
     ]},
    {"id": "local_template_not_found_python", "add_template": True, "args": [],
     "override_venv": "isolated",
     "override_steps": [
         { "type": "python",
           "name": "step1",
           "call": "echo1.py",
           "args": []
         },
         { "type": "python",
           "name": "step2",
           "call": "echo2.py",
           "args": []
         }
     ],
     "expected_output": [
         "template-global.yaml: is valid",
         "Failed to find isolated venv at ~/.prich/templates/template-global/scripts",
         "Failed to find call python file ~/.prich/templates/template-global/scripts/echo1.py",
         "Failed to find call python file ~/.prich/templates/template-global/scripts/echo2.py",
         "template-local.yaml: is valid",
         "Failed to find isolated venv at ./.prich/templates/template-local/scripts",
         "Failed to find call python file ./.prich/templates/template-local/scripts/echo1.py",
         "Failed to find call python file ./.prich/templates/template-local/scripts/echo2.py",
     ]},
]
@pytest.mark.parametrize("case", get_validate_template_CASES, ids=[c["id"] for c in get_validate_template_CASES])
def test_validate_template(mock_paths, monkeypatch, case, template, basic_config):
    global_dir = mock_paths.home_dir
    local_dir = mock_paths.cwd_dir

    monkeypatch.setattr(Path, "home", lambda: global_dir)
    monkeypatch.setattr(Path, "cwd", lambda: local_dir)

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
        if case.get("override_steps"):
            template_local.steps = []
            template_global.steps = []
            for step in case.get("override_steps"):
                if step.get("type") == "python":
                    template_local.steps.append(PythonStep(**step))
                    template_global.steps.append(PythonStep(**step))
                elif step.get("type") == "command":
                    template_local.steps.append(CommandStep(**step))
                    template_global.steps.append(CommandStep(**step))
                else:
                    raise RuntimeError(f"override_steps step type is not supported: {step}")
        template_local.save(FileScope.LOCAL)
        template_global.save(FileScope.GLOBAL)
    if case.get("add_wrong_template"):
        template_local_wrong = template.model_copy(deep=True)
        template_local_wrong.id = "tpl-local-wrong"
        template_local_wrong.steps = []
        template_local_wrong.save(FileScope.LOCAL)

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=mock_paths.home_dir):
        result = runner.invoke(validate_templates, case.get("args"))
        if case.get("expected_output") is not None:
            if type(case.get("expected_output")) == str:
                case["expected_output"] = [case.get("expected_output")]
            for expected_output in case.get("expected_output"):
                assert expected_output in result.output.replace("\n", "")
