import pytest
from click import Context, Command

from prich.cli.dynamic_command_group import DynamicCommandGroup


def test_dcg():
    """Just to call the methods"""
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
