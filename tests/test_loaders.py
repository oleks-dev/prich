import os
from pathlib import Path

import click
import pytest

from tests.fixtures.config import basic_config
from tests.generate.templates import templates
from prich.core.state import _loaded_templates, _loaded_config_paths
from prich.core.loaders import get_loaded_templates, get_loaded_template, get_loaded_config

get_loaded_templates_CASES = [
    {"id": "no_templates", "count": 0, "isolated_venv": False, "global_location": False, "expected_count": 0},
    {"id": "5_templates", "count": 5, "isolated_venv": False, "global_location": False, "expected_count": 5},
    {"id": "50_templates", "count": 50, "isolated_venv": False, "global_location": False, "expected_count": 50},
    {"id": "3_templates", "count": 3, "isolated_venv": True, "global_location": True, "expected_count": 3},
    {"id": "3_templates", "count": 3, "isolated_venv": True, "global_location": False, "expected_count": 3},
    {"id": "20_templates_5_with_tag", "count": 20, "isolated_venv": True, "global_location": True, "expected_count": 5, "tag_first_n": 5},
    {"id": "20_templates_10_with_tag", "count": 20, "isolated_venv": True, "global_location": False, "expected_count": 10, "tag_first_n": 10},
]
@pytest.mark.parametrize("case", get_loaded_templates_CASES, ids=[c["id"] for c in get_loaded_templates_CASES])
def test_get_loaded_templates(monkeypatch, basic_config, case):
    _loaded_templates.clear()
    tpl = templates(count=case.get("count"), isolated_venv=case.get("isolated_venv"), global_location=case.get("global_location"), tag_first_n=case.get("tag_first_n", None))

    monkeypatch.setattr("prich.core.loaders.load_templates", lambda: tpl)
    if case.get("tag_first_n"):
        tags = [tpl[0].tags[1]]
    else:
        tags = None
    print(tags)
    actual = get_loaded_templates(tags)
    assert len(actual) == case.get("expected_count")


get_loaded_template_CASES = [
    {"id": "local_template", "count": 1, "global_location": False},
    {"id": "global_template", "count": 1, "global_location": True},
]
@pytest.mark.parametrize("case", get_loaded_template_CASES, ids=[c["id"] for c in get_loaded_template_CASES])
def test_get_loaded_template(monkeypatch, case):
    _loaded_templates.clear()
    tpl = templates(count=case.get("count"), isolated_venv=case.get("isolated_venv"), global_location=case.get("global_location"))

    monkeypatch.setattr("prich.core.loaders.load_templates", lambda: tpl)

    loaded_template = get_loaded_template(tpl[0].id)
    assert loaded_template



get_loaded_config_CASES = [
    {"id": "local_config", "local_only": True, "expected_providers": ["show_prompt", "local_show_prompt"], "expected_loaded_files": ["local_config.yaml"]},
    {"id": "global_config", "global_only": True, "expected_providers": ["show_prompt", "global_show_prompt"], "expected_loaded_files": ["global_config.yaml"]},
    {"id": "merged_config", "expected_providers": ["show_prompt", "global_show_prompt", "local_show_prompt"], "expected_loaded_files": ["global_config.yaml", "local_config.yaml"]},
]
@pytest.mark.parametrize("case", get_loaded_config_CASES, ids=[c["id"] for c in get_loaded_config_CASES])
def test_get_loaded_config(monkeypatch, case, basic_config):
    from prich.core.state import _loaded_config, _loaded_config_paths
    if _loaded_config:
        _loaded_config.clear()
    if _loaded_config_paths:
        _loaded_config_paths.clear()
    local_config = basic_config.copy(deep=True)
    local_providers = local_config.providers
    local_config.providers.update({'local_show_prompt': list(local_providers.items())[0][1]})
    global_config = basic_config.copy(deep=True)
    global_config.providers.update({'global_show_prompt': list(local_providers.items())[0][1]})

    monkeypatch.setattr("prich.core.loaders._loaded_config", _loaded_config)
    monkeypatch.setattr("prich.core.loaders._loaded_config_paths", _loaded_config_paths)
    monkeypatch.setattr("prich.core.loaders.load_global_config", lambda: (global_config, "global_config.yaml"))
    monkeypatch.setattr("prich.core.loaders.load_local_config", lambda: (local_config, "local_config.yaml"))
    monkeypatch.setattr("prich.core.utils.should_use_global_only", lambda: case.get("global_only", False))
    monkeypatch.setattr("prich.core.utils.should_use_local_only", lambda: case.get("local_only", False))

    loaded_config, loaded_files = get_loaded_config()

    assert loaded_config, "Failed to load config"
    assert list(loaded_config.providers.keys()) == case.get("expected_providers")
    assert list(loaded_files) == case.get("expected_loaded_files")


def test_load_yaml_no_file():
    from prich.core.loaders import _load_yaml
    test_yaml = Path("test_not_present.yaml")
    actual = _load_yaml(test_yaml)
    assert actual == {}

def test_load_config_model_no_file():
    from prich.core.loaders import load_config_model
    test_yaml = Path("test_not_present.yaml")
    actual = load_config_model(test_yaml)
    assert actual == (None, test_yaml)

def test_load_config_model_wrong_schema(monkeypatch):
    from prich.core.loaders import load_config_model
    monkeypatch.setattr("prich.core.loaders._load_yaml", lambda x: ({"schema_version": "0.0"}))
    test_yaml = Path("test_not_present.yaml")
    with pytest.raises(click.ClickException):
        actual = load_config_model(test_yaml)
        assert actual == (None, test_yaml)

def test_find_template_files(tmp_path, monkeypatch):
    from prich.core.loaders import find_template_files
    prich_dir = tmp_path / ".prich"
    templates_dir = prich_dir / "templates"
    template_dir = templates_dir / "test-template"
    os.makedirs(template_dir, exist_ok=True)
    test_yaml = template_dir / "test-template.yaml"
    with open(test_yaml, 'w') as file:
        file.write("")
    actual = find_template_files(prich_dir.parent)
    test_yaml.unlink()
    assert len(actual), 1
