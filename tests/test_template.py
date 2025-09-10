import pytest
from click.testing import CliRunner
from prich.models.file_scope import FileScope

from prich.cli.templates import venv_install, show_template
from prich.core.state import _loaded_templates

from tests.fixtures.paths import mock_paths  # noqa: F811
from tests.fixtures.templates import template  # noqa: F811

get_venv_install_CASES = [
    {"id": "install_local_venv_no_params",
     "args": [],
     "expected_exit_code": 2,
     "expected_exception_message": "Usage: venv-install",
    },
    {"id": "install_local_venv_when_no_venv_in_template",
     "args": ["template-local"],
     "expected_exit_code": 0,
     "expected_exception_message": "Template template-local doesn\'t require venv",
    },
    {"id": "install_global_venv_when_no_venv_in_template",
     "args": ["template-global"],
     "expected_exit_code": 0,
     "expected_exception_message": "Template template-global doesn\'t require venv",
    },
    {"id": "install_local_isolated_venv",
     "args": ["template-local"],
     "venv": "isolated",
     "requirements.txt": "requests==2.32.3",
     "expected_exit_code": 0,
     "expected_exception_message": "Installing isolated venv... done",
    },
    {"id": "install_global_isolated_venv",
     "args": ["template-global"],
     "venv": "isolated",
     "requirements.txt": "requests==2.32.3",
     "expected_exit_code": 0,
     "expected_exception_message": "Installing isolated venv... done",
    },
    {"id": "install_local_shared_venv",
     "args": ["template-local"],
     "venv": "shared",
     "requirements.txt": "requests==2.32.3",
     "expected_exit_code": 0,
     "expected_exception_message": "Installing shared venv... done",
    },
    {"id": "install_global_shared_venv",
     "args": ["template-global"],
     "venv": "shared",
     "requirements.txt": "requests==2.32.3",
     "expected_exit_code": 0,
     "expected_exception_message": "Installing shared venv... done",
    },
    {"id": "install_local_isolated_venv_again_and_force",
     "venv": "isolated",
     "multiple": [
         { "args": ["template-local"],
           "expected_exit_code": 0,
           "expected_exception_message": "Installing isolated venv... done",
           },
         { "args": ["template-local"],
           "expected_exit_code": 0,
           "expected_exception_message": "Venv folder found. No dependencies to install. Done!",
           },
         { "args": ["template-local", "--force"],
           "expected_exit_code": 0,
           "expected_exception_message": "Installing isolated venv... done",
           }
     ],
     },
    {"id": "install_global_isolated_venv_again_and_force",
     "venv": "isolated",
     "multiple": [
         { "args": ["template-global"],
           "expected_exit_code": 0,
           "expected_exception_message": "Installing isolated venv... done",
           },
         { "args": ["template-global"],
           "expected_exit_code": 0,
           "expected_exception_message": "Venv folder found. No dependencies to install. Done!",
           },
         { "args": ["template-global", "--force"],
           "expected_exit_code": 0,
           "expected_exception_message": "Installing isolated venv... done",
           }
     ],
     },
    {"id": "install_local_shared_venv_again_and_force",
     "venv": "shared",
     "multiple": [
         {"args": ["template-local"],
          "expected_exit_code": 0,
          "expected_exception_message": "Installing shared venv... done! No dependencies to install. Done!",
          },
         {"args": ["template-local"],
          "expected_exit_code": 0,
          "expected_exception_message": "Venv folder found. No dependencies to install. Done!",
          },
         {"args": ["template-local", "--force"],
          "expected_exit_code": 1,
          "expected_exception_message": "Shared venv with --force is not supported as it might break",
          }
     ]
    },
    {"id": "install_global_shared_venv_again_and_force",
     "venv": "shared",
     "multiple": [
         {"args": ["template-global"],
          "expected_exit_code": 0,
          "expected_exception_message": "Installing shared venv... done! No dependencies to install. Done!",
          },
         {"args": ["template-global"],
          "expected_exit_code": 0,
          "expected_exception_message": "Venv folder found. No dependencies to install. Done!",
          },
         {"args": ["template-global", "--force"],
          "expected_exit_code": 1,
          "expected_exception_message": "Shared venv with --force is not supported as it might break",
          }
     ]
    },
]
@pytest.mark.parametrize("case", get_venv_install_CASES, ids=[c["id"] for c in get_venv_install_CASES])
def test_venv_install(mock_paths, template, case):
    from pathlib import Path
    template_local = template.model_copy(deep=True)
    template_global = template.model_copy(deep=True)
    template_local.id = "template-local"
    template_global.id = "template-global"
    template_local.folder = str(mock_paths.prich.local_templates / template_local.id)
    template_global.folder = str(mock_paths.prich.global_templates / template_global.id)
    template_local.file = str(Path(template_local.folder) / f"{template_local.id}.yaml")
    template_global.file = str(Path(template_global.folder) / f"{template_global.id}.yaml")
    template_local.description = case.get("id")
    template_global.description = case.get("id")
    if case.get("venv") is not None:
        template_local.venv = case.get("venv")
        template_global.venv = case.get("venv")
    template_local.save(FileScope.LOCAL)
    template_global.save(FileScope.GLOBAL)
    if case.get("requirements.txt"):
        local_scripts_folder = Path(template_local.folder) / "scripts"
        local_scripts_folder.mkdir(exist_ok=True)
        requirements_txt = local_scripts_folder / "requirements.txt"
        with open(requirements_txt, "w") as requirements_txt_file:
            requirements_txt_file.write(case.get("requirements.txt"))
        global_scripts_folder = Path(template_global.folder) / "scripts"
        global_scripts_folder.mkdir(exist_ok=True)
        requirements_txt = global_scripts_folder / "requirements.txt"
        with open(requirements_txt, "w") as requirements_txt_file:
            requirements_txt_file.write(case.get("requirements.txt"))
    if case.get("multiple"):
        inputs = case.get("multiple")
    else:
        inputs = [
            {"args": case.get("args"),
             "expected_exit_code": case.get("expected_exit_code"),
             "expected_exception_message": case.get("expected_exception_message"),
             },
        ]
    runner = CliRunner()
    iteration_idx = 0
    with runner.isolated_filesystem():
        iteration_idx += 1
        for case_input in inputs:
            result = runner.invoke(venv_install, case_input.get("args"))
            if case_input.get("expected_exception_message") is not None:
                assert case_input.get("expected_exception_message") in result.output.replace("\n", " "), f"Iteration {iteration_idx}"
            if case_input.get("expected_exit_code") is not None:
                assert result.exit_code == case_input.get("expected_exit_code"), f"Iteration {iteration_idx}"

get_show_template_CASES = [
    {"id": "show_no_tempate_id",
     "args": [],
     "expected_exit_code": 2,
     "expected_exception_message": "Usage: show",
     },
    {"id": "show_template_id",
     "args": ["template-local"],
     "expected_exit_code": 0,
     "expected_exception_message": "Template: id: template-local",
     },
    {"id": "show_template_id_local_with_g",
     "args": ["template-local", "--global"],
     "expected_exit_code": 1,
     "expected_exception_message": "Error: Template template-local not found.",
     },
    {"id": "show_template_id_global",
     "args": ["template-global"],
     "expected_exit_code": 0,
     "expected_exception_message": "Template: id: template-global",
     },

]
@pytest.mark.parametrize("case", get_show_template_CASES, ids=[c["id"] for c in get_show_template_CASES])
def test_show_template(mock_paths, template, case):
    from pathlib import Path
    if case.get("args") is not []:
        template_local = template.model_copy(deep=True)
        template_global = template.model_copy(deep=True)
        template_local.id = "template-local"
        template_global.id = "template-global"
        template_local.folder = str(mock_paths.prich.local_templates / template_local.id)
        template_global.folder = str(mock_paths.prich.global_templates / template_global.id)
        template_local.file = str(Path(template_local.folder) / f"{template_local.id}.yaml")
        template_global.file = str(Path(template_global.folder) / f"{template_global.id}.yaml")
        template_local.description = case.get("id")
        template_global.description = case.get("id")
        template_local.save(FileScope.LOCAL)
        template_global.save(FileScope.GLOBAL)

    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(show_template, case.get("args"))
        if case.get("expected_exception_message") is not None:
            assert case.get("expected_exception_message") in result.output.replace("\n", " ")
        if case.get("expected_exit_code") is not None:
            assert result.exit_code == case.get("expected_exit_code")

get_create_template_CASES = [
    {"id": "create_template_no_template_id",
     "iterations": [
         {"args": [],
          "expected_exception_messages": ["Usage: create [OPTIONS] TEMPLATE_ID"],
          "expected_exit_code": 2},
     ]
     },
    {"id": "create_template_local",
     "iterations": [
         {"args": ["test-tpl"],
          "expected_exception_messages": ["Template test-tpl created in", "local/.prich/templates/test-tpl/test-tpl"],
          "expected_exit_code": 0,
          "check_file": ""},
         {"args": ["test-tpl"],
          "expected_exception_messages": ["Error: Template test-tpl already exists."],
          "expected_exit_code": 1,
          "check_file": ""},
     ]
     },
    {"id": "create_template_global",
     "iterations": [
         {"args": ["test-tpl", "-g"],
          "expected_exception_message": ["Template test-tpl created in", "global/.prich/templates/test-tpl/test-tpl"],
          "expected_exit_code": 0,
          "check_file": ""},
         {"args": ["test-tpl", "-g"],
          "expected_exception_message": ["Error: Template test-tpl already exists."],
          "expected_exit_code": 1,
          "check_file": ""},
     ]
     },
]
@pytest.mark.parametrize("case", get_create_template_CASES, ids=[c["id"] for c in get_create_template_CASES])
def test_create_template(mock_paths, case):
    from prich.cli.templates import create_template
    _loaded_templates.clear()
    runner = CliRunner()
    with runner.isolated_filesystem():
        for iteration in case.get("iterations"):
            result = runner.invoke(create_template, iteration.get("args"))
            if iteration.get("expected_exception_messages") is not None:
                for message in iteration.get("expected_exception_messages"):
                    assert message in result.output.replace("\n", " ")
            if iteration.get("expected_exit_code") is not None:
                assert result.exit_code == iteration.get("expected_exit_code")


