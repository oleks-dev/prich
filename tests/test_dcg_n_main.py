from pathlib import Path

import pytest
from click import Context, Command

from prich.cli.dynamic_command_group import DynamicCommandGroup
from tests.fixtures.paths import mock_paths
from tests.fixtures.config import basic_config

def test_dcg(mock_paths, monkeypatch, basic_config):
    """Just to call the methods"""
    global_dir = mock_paths.home_dir
    local_dir = mock_paths.cwd_dir

    monkeypatch.setattr(Path, "home", lambda: global_dir)
    monkeypatch.setattr(Path, "cwd", lambda: local_dir)

    local_config = basic_config.model_copy(deep=True)
    global_config = basic_config.model_copy(deep=True)
    local_config.save("local")
    global_config.save("global")

    cmd = Command(None)
    ctx = Context(cmd)
    dcg = DynamicCommandGroup(None)
    dcg.list_commands(ctx)
    dcg.get_command(ctx, "test")
    dcg._load_dynamic_commands(ctx)

def test_main_add_commands():
    import prich.cli.main

def test_optional_import():
    from prich.core.optional_imports import ensure_optional_dep
    ensure_optional_dep("requests")
    with pytest.raises(RuntimeError):
        ensure_optional_dep("notexistingone")

def test_lazy_import():
    from prich.llm_providers.base_optional_provider import LazyOptionalProvider
    lop = LazyOptionalProvider()
    lop._lazy_import("requests")
    lop._lazy_import_from("openai", "OpenAI")
