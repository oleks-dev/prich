import shutil
from dataclasses import dataclass
from pathlib import Path

from yaml import SafeLoader

from prich.models.config import ConfigModel

from prich.models.file_scope import FileScope
from prich.core.state import _loaded_templates, _loaded_config, _loaded_config_paths
from tests.fixtures.config import CONFIG_YAML

import pytest


@pytest.fixture
def mock_paths(tmp_path, monkeypatch):
    import yaml
    _loaded_templates.clear()
    _loaded_config = None
    _loaded_config_paths = []
    config = ConfigModel(**yaml.load(CONFIG_YAML, SafeLoader))
    home_dir = tmp_path / "home"
    cwd_dir = tmp_path / "local"
    global_prich_dir = home_dir / ".prich"
    local_prich_dir = cwd_dir / ".prich"
    global_prich_templates_dir = global_prich_dir / "templates"
    local_prich_templates_dir = local_prich_dir / "templates"
    home_dir.mkdir(exist_ok=True)
    cwd_dir.mkdir(exist_ok=True)
    global_prich_dir.mkdir(exist_ok=True)
    local_prich_dir.mkdir(exist_ok=True)
    global_prich_templates_dir.mkdir(exist_ok=True)
    local_prich_templates_dir.mkdir(exist_ok=True)
    monkeypatch.setattr(Path, "home", lambda: home_dir)
    monkeypatch.setattr(Path, "cwd", lambda: cwd_dir)
    config.save(FileScope.GLOBAL)
    config.save(FileScope.LOCAL)

    @dataclass
    class PrichFolder:
        global_dir: Path
        local_dir: Path
        global_templates: Path
        local_templates: Path

    @dataclass
    class MainFolder:
        home_dir: Path
        cwd_dir: Path
        prich: PrichFolder

    yield MainFolder(
        home_dir=home_dir,
        cwd_dir=cwd_dir,
        prich=PrichFolder(
            global_dir=global_prich_dir,  #home_dir / ".prich",
            local_dir=local_prich_dir,  #cwd_dir / ".prich",
            global_templates=global_prich_templates_dir,  #home_dir / ".prich" / "templates",
            local_templates=local_prich_templates_dir,  #cwd_dir / ".prich" / "templates"
        )
    )
    if str(tmp_path).startswith("/private/var/folders/"):
        shutil.rmtree(tmp_path)
