import os
import shutil
import pytest
from pathlib import Path
from yaml import SafeLoader
from prich.models.config import ConfigModel
from prich.models.file_scope import FileScope
from prich.core.state import _loaded_templates, _loaded_config, _loaded_config_paths
from tests.fixtures.config import CONFIG_YAML
from tests.utils.paths import MainFolder, PrichFolder

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

    monkeypatch.setattr(Path, "home", lambda: home_dir)
    monkeypatch.setattr(Path, "cwd", lambda: cwd_dir)
    os.environ['HOME'] = str(home_dir)
    os.environ['PWD'] = str(cwd_dir)
    config.save(FileScope.GLOBAL)
    config.save(FileScope.LOCAL)

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
    if "/pytest-" in str(tmp_path):
        shutil.rmtree(tmp_path)
    else:
        raise RuntimeError(f"Failed to check folder before removing! {tmp_path}")

