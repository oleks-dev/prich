from pathlib import Path
import pytest
from click.testing import CliRunner
from prich.models.file_scope import FileScope

from prich.cli.validate import validate_templates
from tests.fixtures.templates import template

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
]
@pytest.mark.parametrize("case", get_validate_template_CASES, ids=[c["id"] for c in get_validate_template_CASES])
def test_validate_template(tmp_path, monkeypatch, case, template):
    global_dir = tmp_path / "home"
    local_dir = tmp_path / "local"
    global_dir.mkdir()
    local_dir.mkdir()

    monkeypatch.setattr(Path, "home", lambda: global_dir)
    monkeypatch.setattr(Path, "cwd", lambda: local_dir)

    if case.get("add_template"):
        template_local = template.model_copy(deep=True)
        template_global = template.model_copy(deep=True)
        template_local.id = "template-local"
        template_global.id = "template-global"
        template_local.save(FileScope.LOCAL)
        template_global.save(FileScope.GLOBAL)

    if case.get("add_wrong_template"):
        template_local_wrong = template.model_copy(deep=True)
        template_local_wrong.id = "tpl-local-wrong"
        template_local_wrong.steps = []
        template_local_wrong.save(FileScope.LOCAL)

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(validate_templates, case.get("args"))
        if case.get("expected_output") is not None:
            assert case.get("expected_output") in result.output.replace("\n", " ")
