import pytest
from click.testing import CliRunner

from tests.generate.templates import templates, templates_list_to_dict

get_list_tags_CASES = [
    {"id": "local", "count": 4, "args": ["-l"],
     "expected_output": "Available tags (local):"},
    {"id": "global", "count": 5, "args": ["-g"],
     "expected_output": "Available tags (global):"},
    {"id": "tags", "count": 9, "args": [],
     "expected_output": "Available tags:"},
    {"id": "no_templates", "count": 0, "args": [],
     "expected_output": "No templates installed. Use 'prich template install' to add templates.\n"},
    {"id": "l_g_params", "count": 0, "args": ['-l', '-g'],
     "expected_output": "Use only one local or global option, use"},
]
@pytest.mark.parametrize("case", get_list_tags_CASES, ids=[c["id"] for c in get_list_tags_CASES])
def test_list_tags(tmp_path, monkeypatch, case):
    from prich.cli.listing import list_tags
    from prich.core.state import _loaded_templates
    _loaded_templates.clear()
    template_list = templates(count=case.get("count"), isolated_venv=False, global_location=False)

    monkeypatch.setattr("prich.core.loaders.load_templates", lambda: template_list)

    tags = [x.tags[0] for x in template_list]
    tags_list = []
    for tag in tags:
        if tag not in tags_list:
            tags_list.append(tag)
    expected_tags_number = len(tags_list)

    template_dict = templates_list_to_dict(template_list)
    _loaded_templates.update(template_dict)

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(list_tags, case.get("args"))
        if case.get("expected_output") is not None:
            assert case.get("expected_output") in result.output
            assert len(result.output.strip().split('\n')) == expected_tags_number + 1


get_list_templates_CASES = [
    {"id": "local_json_only", "count": 4, "args": ["-l", "-j"],
     "expected_output": "{\n", "check_count": False},
    {"id": "local", "count": 4, "args": ["-l"],
     "expected_output": "Available templates:\n"},
    {"id": "global", "count": 8, "args": ["-g"],
     "expected_output": "Available templates:\n"},
    {"id": "remote_and_l_fail", "count": 1, "args": ["--remote", "-l"],
     "expected_output": "When listing remote templates available for installation the global or local options are not supported", "check_count": False},
    {"id": "remote_and_g_fail", "count": 1, "args": ["--remote", "-g"],
     "expected_output": "When listing remote templates available for installation the global or local options are not supported", "check_count": False},
    {"id": "l_and_g_fail", "count": 1, "args": ["-l", "-g"],
     "expected_output": "Use only one local or global option, use", "check_count": False},
    {"id": "no_templates", "count": 0, "args": [],
     "expected_output": "No templates found. Use", "check_count": False},
    {"id": "no_templates_with_tag", "count": 0, "args": ["--tag", "test"],
     "expected_output": "No templates found with specified tags:", "check_count": False},
    {"id": "remote_list", "count": 0, "args": ["--remote"],
     "expected_output": "prich Templates", "check_count": False},
    {"id": "remote_list_tag_no_result", "count": 0, "args": ["--remote", "--tag", "notexisting"],
     "expected_output": "No templates found by provided tags", "check_count": False},
    {"id": "remote_list_tag", "count": 0, "args": ["--remote", "--tag", "code"],
     "expected_output": "prich Templates", "check_count": False},
    {"id": "remote_list_json", "count": 0, "args": ["--remote", "--json"],
     "expected_output": "{\n", "check_count": False},
]
@pytest.mark.parametrize("case", get_list_templates_CASES, ids=[c["id"] for c in get_list_templates_CASES])
def test_list_templates(tmp_path, monkeypatch, case):
    from prich.cli.listing import list_templates
    from prich.core.state import _loaded_templates
    _loaded_templates.clear()
    template_list = templates(count=case.get("count"), isolated_venv=False, global_location=False)

    monkeypatch.setattr("prich.core.loaders.load_templates", lambda: template_list)

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(list_templates, case.get("args"))
        if case.get("expected_output") is not None:
            assert case.get("expected_output") in result.output
            if case.get("check_count", True):
                assert len(result.output.strip().split('- ')) == len(template_list) + 1
