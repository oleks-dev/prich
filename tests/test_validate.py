from pathlib import Path
import pytest
from click.testing import CliRunner

get_validate_template_CASES = [
    {"id": "local_and_global_params", "args": ["-g", "-l"], "expected_output": "Error: Use only one local or global option"},
    {"id": "file_with_local_param", "args": ["--file", "test.yaml", "-l"], "expected_output": "When YAML file is selected it doesn't combine with local, global, or id options"},
    {"id": "file_with_global_param", "args": ["--file", "test.yaml", "-g"], "expected_output": "When YAML file is selected it doesn't combine with local, global, or id options"},
    {"id": "file_with_template_id_param", "args": ["--file", "test.yaml", "--id", "test-template"], "expected_output": "When YAML file is selected it doesn't combine with local, global, or id options"},
    {"id": "file_not_present", "args": ["--file", "test.yaml"], "expected_output": "Failed to find test.yaml template file."},
    {"id": "no_templates_found", "args": [], "expected_output": "No Templates found."},
    {"id": "no_template_if_found", "args": ["--id", "test-template"], "expected_output": " Failed to find template with id: test-template"},
]
@pytest.mark.parametrize("case", get_validate_template_CASES, ids=[c["id"] for c in get_validate_template_CASES])
def test_validate_template(tmp_path, monkeypatch, case):
    from prich.cli.validate import validate_templates

    global_dir = tmp_path / "home"
    local_dir = tmp_path / "local"
    global_dir.mkdir()
    local_dir.mkdir()
    monkeypatch.setattr(Path, "home", lambda: global_dir)
    monkeypatch.setattr(Path, "cwd", lambda: local_dir)

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(validate_templates, case.get("args"))
        if case.get("expected_output") is not None:
            assert case.get("expected_output") in result.output
