import os
import tempfile
from pathlib import Path

import click
import pytest

from tests.fixtures.config import basic_config, CONFIG_YAML
from tests.fixtures.templates import INVALID_TEMPLATE_YAML
from tests.generate.templates import templates, templates_list_to_dict
from prich.core.state import _loaded_templates, _loaded_config_paths
from prich.core.loaders import get_loaded_templates, get_loaded_template, get_loaded_config, load_templates, \
    load_config_model, load_template_model

load_templates_CASES = [
    {"id": "no_templates", "count": 0, "global_location": False, "local_only": False, "global_only": False, "expected_count": 0},
    {"id": "local_template", "count": 1, "global_location": False, "local_only": False, "global_only": False, "expected_count": 1},
    {"id": "global_template_with_only_global", "count": 1, "global_location": True, "local_only": False, "global_only": True, "expected_count": 1},
    {"id": "global_template_with_only_local", "count": 1, "global_location": True, "local_only": True, "global_only": False, "expected_count": 0},
]
@pytest.mark.parametrize("case", load_templates_CASES, ids=[c["id"] for c in load_templates_CASES])
def test_load_templates(monkeypatch, tmp_path, case):
    global_dir = tmp_path / "home"
    local_dir = tmp_path / "local"
    global_dir.mkdir()
    local_dir.mkdir()
    monkeypatch.setattr(Path, "home", lambda: global_dir)
    monkeypatch.setattr(Path, "cwd",  lambda: local_dir)

    _loaded_templates.clear()
    template_list = templates(count=case.get("count"), global_location=case.get("global_location"))
    template_dict = templates_list_to_dict(template_list)
    _loaded_templates.update(template_dict)
    if case.get("global_location"):
        global_templates = template_list
    else:
        global_templates = {}
    if case.get("global_location") is False:
        local_templates = template_list
    else:
        local_templates = {}

    returns = {
        global_dir: global_templates,  # for Path.home()
        local_dir: local_templates,    # for Path.cwd()
    }
    def fake_load(p):
        try:
            return returns[p]
        except KeyError:
            raise AssertionError(f"unexpected path: {p!r}")
    monkeypatch.setattr("prich.core.utils.should_use_global_only", lambda: case.get("global_only", False))
    monkeypatch.setattr("prich.core.utils.should_use_local_only", lambda: case.get("local_only", False))
    monkeypatch.setattr("prich.core.loaders._load_template_models", fake_load)
    actual = load_templates()
    assert len(actual) == case.get("expected_count")
    global_dir.rmdir()
    local_dir.rmdir()
    tmp_path.rmdir()
    if len(actual) > 0:
        assert actual[0].id == template_list[0].id


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


def test_get_loaded_templates_from_memory(monkeypatch):
    _loaded_templates.clear()
    template_list = templates(count=2, isolated_venv=False, global_location=False)

    monkeypatch.setattr("prich.core.loaders.load_templates", lambda: [])

    template_dict = templates_list_to_dict(template_list)
    actual_before = get_loaded_templates()
    assert len(actual_before) == 0
    _loaded_templates.update(template_dict)
    actual_after = get_loaded_templates()
    assert len(actual_after) == 2


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

def test_get_loaded_template_non_existing(monkeypatch):
    _loaded_templates.clear()
    with pytest.raises(click.ClickException):
        get_loaded_template("non-existing")
    template_list = templates(count=2, isolated_venv=False, global_location=False)
    template_dict = templates_list_to_dict(template_list)
    _loaded_templates.update(template_dict)
    with pytest.raises(click.ClickException):
        get_loaded_template("non-existing")


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
    local_config = basic_config.model_copy(deep=True)
    local_providers = local_config.providers
    local_config.providers.update({'local_show_prompt': list(local_providers.items())[0][1]})
    global_config = basic_config.model_copy(deep=True)
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
    test_yaml = Path("config_mock.yaml")
    with pytest.raises(click.ClickException):
        load_config_model(test_yaml)

def test_load_config_model_failed_to_load(monkeypatch):
    from prich.core.loaders import load_config_model
    monkeypatch.setattr("prich.core.loaders._load_yaml", lambda x: ({"schema_version": "1.0"}))
    test_yaml = Path("config_mock.yaml")
    actual = load_config_model(test_yaml)
    assert actual == (None, None)

def test_find_template_files(tmp_path):
    from prich.core.loaders import find_template_files
    prich_dir = tmp_path / ".prich"
    templates_dir = prich_dir / "templates"
    template1_dir = templates_dir / "test-template1"
    template2_dir = templates_dir / "test-template2"
    os.makedirs(template1_dir, exist_ok=True)
    os.makedirs(template2_dir, exist_ok=True)
    test_yaml1 = template1_dir / "test-template.yaml"
    test_yaml2 = template2_dir / "test-template.yaml"
    with open(test_yaml1, 'w') as file:
        file.write("")
    with open(test_yaml2, 'w') as file:
        file.write("")
    random_file = templates_dir / "README.md"
    with open(random_file, 'w') as file:
        file.write("")
    actual = find_template_files(prich_dir.parent)
    test_yaml1.unlink()
    test_yaml2.unlink()
    template1_dir.rmdir()
    template2_dir.rmdir()
    random_file.unlink()
    templates_dir.rmdir()
    prich_dir.rmdir()
    tmp_path.rmdir()
    assert len(actual), 2

def test_find_template_files_no_templates(tmp_path):
    from prich.core.loaders import find_template_files
    prich_dir = tmp_path / ".prich"
    templates_dir = prich_dir / "templates"
    os.makedirs(templates_dir, exist_ok=True)
    actual = find_template_files(prich_dir.parent)
    templates_dir.rmdir()
    prich_dir.rmdir()
    tmp_path.rmdir()
    assert len(actual) == 0

def test_find_template_files_no_templates_folder():
    from prich.core.loaders import find_template_files
    actual = find_template_files(Path("./non-existing"))
    assert len(actual) == 0

def test_config_model_load():
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.yaml"
        config_path.write_text(CONFIG_YAML)
        config_model, loaded_path = load_config_model(config_path)
        assert config_model is not None
        assert config_model.settings.default_provider == "show_prompt"
        assert "show_prompt" in config_model.providers

def test_invalid_template_validation():
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "invalid.yaml"
        file_path.write_text(INVALID_TEMPLATE_YAML)
        with pytest.raises(Exception) as exc:
            load_template_model(file_path)
        assert "Field required" in str(exc.value)