import tempfile
from pathlib import Path
import pytest
from click.testing import CliRunner
from prich.cli.templates import template_install
from prich.core.loaders import load_config_model, load_template_model
from prich.core.engine import render_prompt
from prich.models.template import PromptFields
from tests.fixtures.config import CONFIG_YAML
from tests.fixtures.paths import mock_paths
from tests.fixtures.templates import temp_template_dir, INVALID_TEMPLATE_YAML


def test_template_install_local(temp_template_dir, mock_paths):
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(template_install, [str(temp_template_dir)])
        assert result.exit_code == 0
        assert "Template test_template installed successfully" in result.output
        assert Path(mock_paths.prich.local_templates / "test_template" / "test_template.yaml").exists()


def test_template_install_force_overwrite(temp_template_dir, mock_paths):
    runner = CliRunner()
    with runner.isolated_filesystem():
        # First install
        runner.invoke(template_install, [str(temp_template_dir)])
        # Second install without --force should fail
        result = runner.invoke(template_install, [str(temp_template_dir)])
        assert result.exit_code != 0
        assert "already exists" in result.output
        # Now with --force
        result = runner.invoke(template_install, [str(temp_template_dir), "--force"])
        assert result.exit_code == 0
        assert "installed successfully" in result.output
