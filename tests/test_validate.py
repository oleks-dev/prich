import os
from pathlib import Path
import pytest
from click.testing import CliRunner
from prich.models.template import CommandStep, PythonStep
from prich.models.file_scope import FileScope

from prich.cli.validate import validate_templates
from tests.fixtures.templates import template  # noqa: F811
from tests.fixtures.config import basic_config  # noqa: F811
from tests.fixtures.paths import mock_paths  # noqa: F811

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
     "expected_output": ["Failed to find", "test.yaml template file."]},
    {"id": "path_as_file", "args": ["--file", "."],
     "expected_output": ["Failed to find", " template file."]},
    {"id": "wrong_template_from_file", "add_wrong_template": True,
     "args": ["--file", "./.prich/templates/tpl-local-wrong/tpl-local-wrong.yaml"],
     "expected_output": "tpl-local-wrong.yaml: is not valid"},
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
         "template-global.yaml: is not valid",
         "Failed to find call command file ~/.prich/templates/template-global/scripts/echo1",
         "Failed to find call command file ~/.prich/templates/template-global/scripts/echo2",
         "template-local.yaml: is not valid",
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
         "template-global.yaml: is not valid",
         "Failed to find isolated venv at ~/.prich/templates/template-global/scripts",
         "Failed to find call python file ~/.prich/templates/template-global/scripts/echo1.py",
         "Failed to find call python file ~/.prich/templates/template-global/scripts/echo2.py",
         "template-local.yaml: is not valid",
         "Failed to find isolated venv at ./.prich/templates/template-local/scripts",
         "Failed to find call python file ./.prich/templates/template-local/scripts/echo1.py",
         "Failed to find call python file ./.prich/templates/template-local/scripts/echo2.py",
     ]},

    # wrong templates from resources
    {"id": "file_empty",
     "args": ["--file", "{resources}/empty.yaml"],
     "expected_output": ["empty.yaml: is not valid", "check if file or contents are correct"]},
    {"id": "file_no_schema_version",
     "args": ["--file", "{resources}/no_schema_version.yaml"],
     "expected_output": ["no_schema_version.yaml", "is not valid", "Failed to load template",
                         "Unsupported template schema version NOT SET"]},
    {"id": "file_not_supported_schema",
     "args": ["--file", "{resources}/not_supported_schema.yaml"],
     "expected_output": ["not_supported_schema.yaml", "is not valid", "Failed to load template",
                         "Unsupported template schema version 0.1"]},
    {"id": "file_no_id",
     "args": ["--file", "{resources}/no_id.yaml"],
     "expected_output": ["no_id.yaml", "is not valid (1 issue)", "Failed to load template",
                         "Missing required field at 'id'", "+id: ..."]},
    {"id": "file_no_name",
     "args": ["--file", "{resources}/no_name.yaml"],
     "expected_output": ["no_name.yaml", "is not valid", "Failed to load template",
                         "Missing required field at 'name'", "+name: ..."]},
    {"id": "file_no_steps",
     "args": ["--file", "{resources}/no_steps.yaml"],
     "expected_output": ["no_steps.yaml", "is not valid", "Failed to load template",
                         "Field value should be a valid list at 'steps'", "steps: null",
                         "See Steps documentation:", "https://oleks-dev.github.io/prich/reference/template/steps/"]},
    {"id": "file_wrong_steps",
     "args": ["--file", "{resources}/wrong_steps.yaml"],
     "expected_output": ["wrong_steps.yaml", "is not valid (3 issues)", "Failed to load template",
                         "1. Field value 'provider' found using 'type' does not match any of the expected values: 'python', 'command', 'llm', 'render' at 'steps[1]':  ---  - name: Ask to generate 1st",
                         "2. Missing required field at 'steps[2].name':  ---  step_name: Ask to generate 2nd",
                         "3. Unrecognized field at 'steps[2].step_name':  ---  step_name: Ask to generate 2nd",
                         "See Steps documentation:", "https://oleks-dev.github.io/prich/reference/template/steps/"]},
    {"id": "file_wrong_variables",
     "args": ["--file", "{resources}/wrong_variables.yaml"],
     "expected_output": ["wrong_variables.yaml", "is not valid (4 issues)", "Failed to load template",
                         "1. Missing required field at 'variables[1].name':  ---  var_name: test  +name: ...",
                         "2. Unrecognized field at 'variables[1].var_name':  ---  var_name: test  ... ",
                         "3. Field value should be 'str',",
                         "4. Field value should be a valid boolean, unable to interpret input at 'variables[4].required'",
                         "See Variables documentation https://oleks-dev.github.io/prich/reference/template/variables/"]},
    {"id": "file_no_python_not_found_isolated_venv",
     "args": ["--file", "{resources}/no_venv.yaml"],
     "expected_output": ["no_venv.yaml", "is not valid (1 issue)",
                         "1. Failed to find isolated venv at",
                         "There are no steps with type 'python' found",
                         "Install it by running 'prich venv-install test-template'."
     ]},
    {"id": "file_no_python_not_found_shared_venv",
     "args": ["--file", "{resources}/no_shared_venv.yaml"],
     "expected_output": ["no_shared_venv.yaml", "is not valid (1 issue)",
                         "1. Failed to find shared venv at",
                         "There are no steps with type 'python' found",
     ]},
    {"id": "file_yaml_error",
     "args": ["--file", "{resources}/yaml_error.yaml"],
     "expected_output": ["yaml_error.yaml", "is not valid (1 issue)",
                         "Failed to load template:", "1. while scanning a simple key",
                         "could not find expected ':'",
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
        resources_path = os.path.dirname(__file__)
        args = []
        for arg in case.get("args"):
            args.append(arg.replace("{resources}", str(Path(resources_path) / "resources")))

        result = runner.invoke(validate_templates, args)
        if case.get("expected_output") is not None:
            if isinstance(case.get("expected_output"), str):
                case["expected_output"] = [case.get("expected_output")]
            for expected_output in case.get("expected_output"):
                assert expected_output in result.output.replace("\n", " ").replace("  ", " ")
