import pytest
from click.testing import CliRunner
from prich.cli.templates import template_install
from tests.fixtures.paths import mock_paths
from tests.fixtures.templates import temp_template_dir

get_template_install_CASES = [
    {"id": "template_install_local",
     "from": "path",
     "iterations": [
         {"additional_args": [],
         "expected_exit_code": 0,
         "expected_messages": ["Template test_template installed successfully", "./.prich"]
         },
         {"additional_args": [],
         "expected_exit_code": 1,
         "expected_messages": ["Error: Template 'test_template' already exists in local directory", "./.prich"]
         },
         {"additional_args": ["--force"],
         "expected_exit_code": 0,
         "expected_messages": ["Template test_template installed successfully", "./.prich"]
         },
    ]},
    {"id": "template_install_global",
     "from": "path",
     "iterations": [
         {"additional_args": ["-g"],
         "expected_exit_code": 0,
         "expected_messages": ["Template test_template installed successfully", "~/.prich"]
         },
         {"additional_args": ["-g"],
         "expected_exit_code": 1,
         "expected_messages": ["Error: Template 'test_template' already exists in global directory", "~/.prich"]
         },
         {"additional_args": ["-g", "--force"],
         "expected_exit_code": 0,
         "expected_messages": ["Template test_template installed successfully", "~/.prich"]
         },
     ]},
    {"id": "template_install_local_from_remote",
     "iterations": [
         {"additional_args": ["code-review", "-r"],
          "expected_exit_code": 0,
          "expected_messages": ["Template code-review installed successfully", "./.prich"]
          },
         {"additional_args": ["code-review", "-r"],
         "expected_exit_code": 1,
         "expected_messages": ["Error: Template 'code-review' already exists in local directory", "./.prich"]
         },
         {"additional_args": ["code-review", "-r", "--force"],
         "expected_exit_code": 0,
         "expected_messages": ["Template code-review installed successfully", "./.prich"]
         },
         ]
     },
    {"id": "template_install_global_from_remote",
     "iterations": [
         {"additional_args": ["code-review", "-r", "-g"],
         "expected_exit_code": 0,
         "expected_messages": ["Template code-review installed successfully", "~/.prich"]
         },
         {"additional_args": ["code-review", "-r", "-g"],
         "expected_exit_code": 1,
         "expected_messages": ["Error: Template 'code-review' already exists in global directory", "~/.prich"]
         },
         {"additional_args": ["code-review", "-r", "-g", "--force"],
         "expected_exit_code": 0,
         "expected_messages": ["Template code-review installed successfully", "~/.prich"]
         },
         ]
     },
    {"id": "template_install_local_not_existing_from_remote",
     "iterations": [
         {"additional_args": ["not-existing-template", "-r"],
         "expected_exit_code": 1,
         "expected_messages": [
             "Error: Remote Template ID not-existing-template not found in the repository"
         ]},
     ]
     },
    {"id": "template_install_global_not_existing_from_remote",
     "iterations": [
         {"additional_args": ["not-existing-template", "-r", "-g"],
          "expected_exit_code": 1,
          "expected_messages": [
              "Error: Remote Template ID not-existing-template not found in the repository"
          ]},
     ]
     },
    {"id": "template_install_from_folder_no_yaml",
     "from": "path",
     "no_yaml_file": True,
     "iterations": [
         {"additional_args": [],
          "expected_exit_code": 1,
          "expected_messages": ["Error: No template YAML found"]
          },
     ]},
    {"id": "template_install_from_folder_empty_yaml",
     "from": "path",
     "empty_yaml_file": True,
     "iterations": [
         {"additional_args": [],
          "expected_exit_code": 1,
          "expected_messages": ["Error: Failed to load template:", " is empty"]
          },
     ]},
    {"id": "template_install_from_folder_empty_yaml_chmod_yes",
     "from": "path",
     "add_scripts_to_folder": True,
     "simulate_input": "yes",
     "iterations": [
         {"additional_args": [],
          "expected_exit_code": 0,
          "expected_messages": ["Installing template to ", "Setup Scripts:", "+ ./scripts/test.py", "+ ./scripts/test.sh", "Running chmod", "Done!", "Template test_template installed successfully."]
          },
     ]},
    {"id": "template_install_from_folder_empty_yaml_chmod_no",
     "from": "path",
     "add_scripts_to_folder": True,
     "simulate_input": "no",
     "iterations": [
         {"additional_args": [],
          "expected_exit_code": 0,
          "expected_messages": ["Installing template to ", "Setup Scripts:", "+ ./scripts/test.py", "+ ./scripts/test.sh", "Skipped chmod 755.", "Done!", "Template test_template installed successfully."]
          },
     ]},
]
@pytest.mark.parametrize("case", get_template_install_CASES, ids=[c["id"] for c in get_template_install_CASES])
def test_template_install_from_folder(case, temp_template_dir, mock_paths, monkeypatch):
    from prich.core.state import _loaded_templates
    _loaded_templates = []
    runner = CliRunner()
    if case.get("no_yaml_file"):
        (temp_template_dir / "test_template.yaml").unlink()
    if case.get("empty_yaml_file"):
        (temp_template_dir / "test_template.yaml").write_text("")
    if case.get("simulate_input"):
        monkeypatch.setattr('builtins.input', lambda _: case.get("simulate_input"))
    if case.get("add_scripts_to_folder"):
        scripts_folder = temp_template_dir / "scripts"
        scripts_folder.mkdir(exist_ok=True)
        (scripts_folder / "test.sh").write_text("#!/bin/bash\necho \"test\"")
        (scripts_folder / "test.py").write_text("print(\"test\")")
        (scripts_folder / "requirements.txt").write_text("httpx==0.28.1")
    with runner.isolated_filesystem():
        for iteration in case.get("iterations"):
            if case.get("from") == "path":
                args = [str(temp_template_dir)]
            else:
                args = []
            args.extend(iteration.get("additional_args"))
            result = runner.invoke(template_install, args)
            if iteration.get("expected_messages") is not None:
                for message in iteration.get("expected_messages"):
                    assert message in result.output
            if iteration.get("expected_exit_code") is not None:
                assert result.exit_code == iteration.get("expected_exit_code")

            # assert Path(mock_paths.prich.local_templates / "test_template" / "test_template.yaml").exists()


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
