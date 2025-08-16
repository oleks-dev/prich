import os
from pathlib import Path

import click
import pydantic
import pytest
from prich.models.file_scope import FileScope

from prich.models.template import TemplateModel

from prich.models.template_repo_manifest import TemplatesRepoManifest
from tests.fixtures.config import basic_config

def test_model_template_repo_manifest():
    test_repo = {
      "archives_path": "https://github.com/oleks-dev/prich-templates/tree/main/dist",
      "templates_path": "https://github.com/oleks-dev/prich-templates/tree/main/templates",
      "description": "Templates Available for Installation from prich-templates GitHub Repository",
      "name": "prich Templates",
      "repository": "https://github.com/oleks-dev/prich-templates",
      "schema_version": "1.0",
      "templates": [
        {
          "archive": "cli-expert.zip",
          "archive_checksum": "38c5def03643406f9844e1dde12c2fa69eaa6f570aa1d510f90d682dd5f05a12",
          "author": "prich",
          "description": "CLI command usage helper providing real-world examples for shell commands across different operating systems.",
          "files": [
            "cli-expert/cli-expert.yaml"
          ],
          "folder_checksum": "f9b55f89d3b6ec28aff63665c1e410689a9f3f7f09b7bde0eada49f5be6259e6",
          "id": "cli-expert",
          "name": "CLI Expert",
          "schema_version": "1.0",
          "tags": [
            "os",
            "cli",
            "shell",
            "helper"
          ],
          "version": "1.0",
        }
      ]
    }
    actual = TemplatesRepoManifest(**test_repo)
    assert len(actual.templates) == 1


get_model_template_CASES = [
    {
      "id": "duplicate_step_name",
      "data": {
        "id": "test",
        "name": "Test",
        "schema_version": "1.0",
        "steps": [
          {"name": "step1",
           "call": "",
           "args": [],
           "type": "python"},
          {"name": "step1",
           "call": "",
           "args": [],
           "type": "command"},
        ]
      },
      "expected_exception": click.ClickException,
      "expected_exception_text": "Duplicate test template step name (#2): 'step1'"
    },
    {
      "id": "invalid_step_type",
      "data": {
        "id": "test",
        "name": "Test",
        "schema_version": "1.0",
        "steps": [
          {"name": "step1",
           "call": "",
           "args": [],
           "type": "notsupported"}
        ]
      },
      "expected_exception": pydantic.ValidationError,
      "expected_exception_text": "Input tag 'notsupported' found using 'type' does not match any of the expected tags"
    },
    {
      "id": "invalid_variable_name",
      "data": {
        "id": "test",
        "name": "Test",
        "schema_version": "1.0",
        "steps": [
        ],
        "variables": [
          {"name": "wrong-variable-name"}
        ]
      },
      "expected_exception": click.ClickException,
      "expected_exception_text": "Invalid variable name 'wrong-variable-name' in test template"
    },
]
@pytest.mark.parametrize("case", get_model_template_CASES, ids=[c["id"] for c in get_model_template_CASES])
def test_model_template(case):
  if case.get("expected_exception") is not None:
    with pytest.raises(case.get("expected_exception")) as e:
      TemplateModel(**case.get("data"))
    if case.get("expected_exception_text") is not None:
      if case.get("expected_exception") == click.ClickException:
        assert case.get("expected_exception_text") in e.value.message
      else:
        assert case.get("expected_exception_text") in str(e.value)
  else:
    TemplateModel(**case.get("data"))


get_model_template_save_CASES = [
  {"id": "failed_to_save",
   "template": TemplateModel(
      id = "test1",
      name = "Test1",
      steps = []),
   "location": None, "expected_exception": click.ClickException},
  {"id": "saved_local",
   "template": TemplateModel(
      id = "test2",
      name = "Test2",
      steps = []),
   "location": FileScope.LOCAL},
  {"id": "saved_global",
   "template": TemplateModel(
     id="test3",
     name="Test3",
     steps=[]),
   "location": FileScope.GLOBAL},
  {"id": "saved_local_from_source",
   "template": TemplateModel(
     id="test4",
     name="Test4",
     source=FileScope.LOCAL,
     steps=[]),
   },
  {"id": "saved_global_from_source",
   "template": TemplateModel(
     id="test5",
     name="Test5",
     source=FileScope.GLOBAL,
     steps=[]),
   },
]
@pytest.mark.parametrize("case", get_model_template_save_CASES, ids=[c["id"] for c in get_model_template_save_CASES])
def test_model_template_save(monkeypatch, tmp_path, case):
  global_dir = tmp_path / "home"
  local_dir = tmp_path / "local"
  global_dir.mkdir()
  local_dir.mkdir()
  monkeypatch.setattr(Path, "home", lambda: global_dir)
  monkeypatch.setattr(Path, "cwd", lambda: local_dir)
  template = case.get("template")
  if case.get("expected_exception"):
    with pytest.raises(case.get("expected_exception")):
      template.save(case.get("location"))
  else:
    template.save(case.get("location"))
    if case.get("location") == FileScope.LOCAL or (not case.get("location") and template.source == FileScope.LOCAL):
      test_file = local_dir / ".prich" / "templates" / template.id / f"{template.id}.yaml"
      assert test_file.exists()
      test_file.unlink()
    elif case.get("location") == FileScope.GLOBAL or (not case.get("location") and template.source == FileScope.GLOBAL):
      test_file = global_dir / ".prich" / "templates" / template.id / f"{template.id}.yaml"
      assert test_file.exists()
      test_file.unlink()


get_model_config_CASES = [
  {"id": "wrong_param", "location": None, "expected_exception": click.ClickException, "expected_exception_text": "Save config location param value is not supported"},
  {"id": "save_local", "location": FileScope.LOCAL},
  {"id": "save_global", "location": FileScope.GLOBAL},
]
@pytest.mark.parametrize("case", get_model_config_CASES, ids=[c["id"] for c in get_model_config_CASES])
def test_model_config(tmp_path, monkeypatch, basic_config, case):
  global_dir = tmp_path / "home"
  local_dir = tmp_path / "local"
  global_dir.mkdir()
  local_dir.mkdir()
  monkeypatch.setattr(Path, "home", lambda: global_dir)
  monkeypatch.setattr(Path, "cwd", lambda: local_dir)

  if case.get("expected_exception") is not None:
    with pytest.raises(case.get("expected_exception")) as e:
      basic_config.save(case.get("location"))
    if case.get("expected_exception_text") is not None:
      if case.get("expected_exception") == click.ClickException:
        assert case.get("expected_exception_text") in e.value.message
      else:
        assert case.get("expected_exception_text") in str(e.value)
  else:
    basic_config.save(case.get("location"))
    saved_into_dir = global_dir if case.get("location") == FileScope.GLOBAL else local_dir
    assert (saved_into_dir / ".prich" / "config.yaml").exists()
    basic_config.save(case.get("location"))
    assert (saved_into_dir / ".prich" / "config.yaml").exists()
    assert (saved_into_dir / ".prich" / "config.bak").exists()
