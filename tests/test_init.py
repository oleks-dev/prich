import shutil
from pathlib import Path
from subprocess import CompletedProcess

import pytest
from click.testing import CliRunner
from tests.fixtures.paths import mock_paths  # noqa: F811

get_init_cmd_CASES = [
    {"id": "init_global", "args_1": ["-g"], "init_folder": "global",
     "expected_output_1": "Initialized prich at "},
    {"id": "init", "args_1": [], "init_folder": "local",
     "expected_output_1": "Initialized prich at "},
    {"id": "double_init_global_exist", "args_1": ["-g"], "args_2": ["-g"], "init_folder": "global",
     "expected_output_1": "Initialized prich at ", "expected_output_2": "exists. Use --force to overwrite"},
    {"id": "double_init_local_exist", "args_1": [], "args_2": [], "init_folder": "local",
     "expected_output_1": "Initialized prich at ", "expected_output_2": "exists. Use --force to overwrite"},
    {"id": "double_init_global_force", "args_1": ["-g"], "args_2": ["-g", "--force"], "init_folder": "global",
     "expected_output_1": "Initialized prich at ", "expected_output_2": "Initialized prich at "},
    {"id": "double_init_local_force", "args_1": [], "args_2": ["--force"], "init_folder": "local",
     "expected_output_1": "Initialized prich at ", "expected_output_2": "Initialized prich at "},
]
@pytest.mark.parametrize("case", get_init_cmd_CASES, ids=[c["id"] for c in get_init_cmd_CASES])
def test_init_cmd(mock_paths, monkeypatch, case):
    from prich.cli.init_cmd import init

    global_dir = mock_paths.home_dir
    local_dir = mock_paths.cwd_dir
    monkeypatch.setattr(Path, "home", lambda: global_dir)
    monkeypatch.setattr(Path, "cwd", lambda: local_dir)

    if case.get("init_folder") == "global":
        prich_dir = global_dir / ".prich"
    elif case.get("init_folder") == "local":
        prich_dir = local_dir / ".prich"
    else:
        assert False, "Wrong init_folder param specified"

    if "/pytest-" in str(prich_dir) and prich_dir.exists():
        shutil.rmtree(prich_dir)
    else:
        raise RuntimeError(f"Failed to check folder before removing! {prich_dir}")

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=mock_paths.home_dir):
        result = runner.invoke(init, case.get("args_1"))
        if case.get("expected_output_1") is not None:
            assert case.get("expected_output_1") in result.output
        if case.get("init_folder"):
            assert (prich_dir / "config.yaml").exists()
            assert (prich_dir / "venv").exists()
        if case.get("expected_output_2") is not None:
            result = runner.invoke(init, case.get("args_2"))
            assert case.get("expected_output_2") in result.output


def test_completion_cmd(tmp_path, monkeypatch):
    from prich.cli.init_cmd import completion

    monkeypatch.setattr("subprocess.run", lambda cmd, env, text, check: CompletedProcess(args=[], returncode=0, stdout="output"))

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        runner.invoke(completion, ["bash"])
        runner.invoke(completion, ["zsh"])
        runner.invoke(completion, ["fish"])
