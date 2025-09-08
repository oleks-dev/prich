import os
import re
from pathlib import Path
import click
import yaml
from pydantic import ValidationError as PydanticValidationError
from prich.constants import PRICH_DIR_NAME
from prich.models.template import CommandStep, PythonStep
from prich.core.file_scope import classify_path
from prich.core.loaders import find_template_files, load_template_model, get_env_vars, _load_yaml
from prich.core.utils import console_print, shorten_path, get_prich_dir, is_just_filename, get_cwd_dir, get_home_dir


def template_model_doctor(template_yaml: dict, model_load_error: PydanticValidationError) -> list[str]:
    """Doctor method to describe template model loading failures with detailed yaml key highlight"""
    if template_yaml is None:
        raise click.ClickException("Template YAML data is missing")
    found_issues_list = []
    for err in model_load_error.errors():
        details = None
        if template_yaml and err.get("loc"):
            # hide extra layering
            if err.get("loc")[0] == "steps":
                if err.get("loc")[2] in ['llm', 'command', 'python', 'render']:
                    details = err.get("loc")[2]
                    err['loc'] = tuple(err.get("loc")[:2] + err.get("loc")[3:])

            trace_dir = template_yaml.copy()
            loc_list = err.get("loc")[:-1] if len(err.get("loc")) > 1 else err.get("loc")
            for x in loc_list:
                try:
                    trace_dir = trace_dir[x]
                except Exception:
                    break
            template_overview = yaml.safe_dump(trace_dir, explicit_start=True, explicit_end=True, indent=2,
                                               sort_keys=False)
            # highlight not permitted field
            if 'Extra inputs are not permitted' in err.get("msg"):
                err["msg"] = err["msg"].replace("Extra inputs are not permitted", "Unrecognized field")
                template_overview = re.sub(f"([\n]*\\s|^)({err.get('loc')[-1]})(:)", "\\1[red]\\2[/red]\\3",
                                           template_overview, count=1)
            # highlight block with required field
            elif 'Field required' in err.get("msg"):
                err["msg"] = err['msg'].replace("Field required", "Missing required field")
                template_overview = re.sub("(\.\.\.)", f"[yellow]+{err.get('loc')[-1]}: ...[/yellow]\n\\1",
                                           template_overview, count=1)
            else:
                if 'Input should be' in err.get('msg'):
                    err["msg"] = err['msg'].replace("Input should be", "Field value should be")
                highligh_block = err.get('loc')[-1] if isinstance(err.get('loc')[-1], str) else err.get('loc')[-2]
                template_overview = re.sub(f"([\n]*(?:\s+)|^)({highligh_block})(:)", "\\1[red]\\2[/red]\\3",
                                           template_overview, count=1)
            err_loc_list = []
            for err_loc_item in err.get('loc'):
                if isinstance(err_loc_item, int):
                    err_loc_list.append(f"[[cyan]{str(err_loc_item + 1)}[/cyan]]")
                else:
                    err_loc_list.append(err_loc_item)
            err_loc_string = '.'.join(err_loc_list).replace(".[", "[")
            if err.get("loc")[0] == "steps":
                doc_items = ["See Steps documentation:"]
                if len(err.get("loc")) >= 3 and isinstance(err.get("loc")[2], str) and err.get("loc")[2].startswith(
                        "extract_var"):
                    doc_items.append(
                        "Extract Variables: https://oleks-dev.github.io/prich/reference/template/steps/#extract-variables")
                elif len(err.get("loc")) >= 3 and isinstance(err.get("loc")[2], str) and err.get("loc")[2].startswith(
                        "validat"):
                    doc_items.append(
                        "Validate Output: https://oleks-dev.github.io/prich/reference/template/steps/#validate-output")
                elif len(err.get("loc")) >= 3 and err.get("loc")[2] == "when":
                    doc_items.append(
                        "When to Execute: https://oleks-dev.github.io/prich/reference/template/steps/#when-to-execute-conditional-statement")
                elif len(err.get("loc")) >= 3 and isinstance(err.get("loc")[2], str) and (
                        err.get("loc")[2].startswith("filter") or err.get("loc")[2].startswith("split") or
                        err.get("loc")[2].startswith("strip") or err.get("loc")[2].startswith("regex") or
                        err.get("loc")[2].startswith("extract_regex")):
                    doc_items.append(
                        "Output Text Transformations: https://oleks-dev.github.io/prich/reference/template/steps/#output-text-transformations")
                elif len(err.get("loc")) >= 3 and isinstance(err.get("loc")[2], str) and err.get("loc")[2].startswith(
                        "output_"):
                    doc_items.append(
                        "Store And Show Output: https://oleks-dev.github.io/prich/reference/template/steps/#store-and-show-output")
                if details and details in ["llm", "pyhon", "command", "render"]:
                    doc_items.append(
                        f"{details} step: https://oleks-dev.github.io/prich/reference/template/steps/#{details}-step")
                doc_items.append("https://oleks-dev.github.io/prich/reference/template/steps/")
                doc = '\n'.join(doc_items)
            elif err.get("loc")[0] == "variables":
                doc = "See Variables documentation https://oleks-dev.github.io/prich/reference/template/variables/"
            else:
                doc = "See Template Content Documentation https://oleks-dev.github.io/prich/reference/template/content/"
            err_loc_string = re.sub(f"({err.get('loc')[-1]})$", f"[red]\\1[/red]", err_loc_string)
            found_issues_list.append(f"""{len(found_issues_list)+1}. [red]{err.get('msg')}[/red] '{err_loc_string}':\n{template_overview}{doc}""")
    return found_issues_list


@click.command(name="validate")
@click.option("--id", "template_id", type=str, help="Template ID to validate")
@click.option("--file", "validate_file", type=Path, help="Template YAML file to validate")
@click.option("-g", "--global", "global_only", is_flag=True, help="Validate only global templates")
@click.option("-l", "--local", "local_only", is_flag=True, help="Validate only local templates")
def validate_templates(template_id: str, validate_file: Path, global_only: bool, local_only: bool):
    """Validate Templates by checking yaml template schema"""
    import sys
    if global_only and local_only:
        raise click.ClickException("Use only one local or global option, use: 'prich validate -g' or 'prich validate -l'")

    if validate_file and (global_only or local_only or template_id):
        raise click.ClickException(f"When YAML file is selected it doesn't combine with local, global, or id options, use: 'prich validate --file ./{PRICH_DIR_NAME}/templates/test-template/test-template.yaml'")

    if validate_file and not validate_file.exists():
        raise click.ClickException(f"Failed to find {validate_file} template file.")

    # Load Template Files
    template_files = []
    if validate_file:
        # Load one template file
        template_files = [validate_file]
    else:
        # Prepare Template Files Path
        file_paths = [get_cwd_dir(), get_home_dir()]
        if global_only:
            file_paths.remove(get_cwd_dir())
        if local_only:
            file_paths.remove(get_home_dir())
        for base_dir in file_paths:
            template_files.extend(find_template_files(base_dir))

    if template_id:
        template_files = [tpl for tpl in template_files if tpl.name == f"{str(template_id)}.yaml"]
        if not template_files:
            raise click.ClickException(f"Failed to find template with id: {template_id}")

    if not template_files:
        console_print("[yellow]No Templates found.[/yellow]")
        return

    template_files.sort()

    failures_found = False
    for template_file in template_files:
        template_yaml = None
        template_id = None
        template_name = None
        failures_list = []
        model_failures_count = 0
        try:
            if template_file.is_file():
                template_yaml = _load_yaml(template_file)
                template_id = template_yaml.get("id") if template_yaml else None
                template_name = template_yaml.get("name") if template_yaml else None
            try:
                template = load_template_model(template_file)
            except PydanticValidationError as e:
                found_model_issues = template_model_doctor(template_yaml, e)
                model_failures_count = len(found_model_issues)
                found_model_issues_string = '\n\n'.join(found_model_issues)
                raise click.ClickException(found_model_issues_string)
            except Exception as e:
                raise click.ClickException(f"1. [red]{str(e)}[/red]")
            if template.venv in ["isolated", "shared"]:
                venv_folder = (Path(template.folder) / "scripts") if template.venv == "isolated" else get_prich_dir() / "venv"
                if not venv_folder.exists():
                    failures_list.append(f"{len(failures_list)+1}. [red]Failed to find {template.venv} venv at {shorten_path(str(venv_folder))}.[/red] Install it by running 'prich venv-install {template.id}'.")
            idx = 0
            for step in template.steps:
                idx += 1
                if type(step) in [CommandStep, PythonStep]:
                    call_file = Path(step.call)
                    if not call_file.exists() and not (Path(template.folder) / "scripts" / call_file).exists() and type(step) == CommandStep:
                        env_vars = get_env_vars()
                        if env_vars.get("PATH"):
                            paths = env_vars.get("PATH").split(":")
                            if paths and is_just_filename(step.call):
                                for path in paths:
                                    if (path / Path(step.call)).exists():
                                        call_file = path / Path(step.call)
                                        break
                    if call_file.exists() and not os.access(call_file, os.X_OK) and type(step) == CommandStep:
                        failures_list.append(f"{len(failures_list)+1}. [red]The call command {shorten_path(str(call_file))} file is not executable in step[/red] [white]#{idx} {step.name}[/white]")
                    elif not call_file.exists() and not (Path(template.folder) / "scripts" / call_file).exists():
                        if is_just_filename(call_file):
                            full_path = str(Path(template.folder) / "scripts" / call_file)
                        else:
                            full_path = str(call_file)
                        failures_list.append(f"{len(failures_list)+1}. [red]Failed to find call {step.type} file {shorten_path(full_path)}[/red] for step #{idx} {step.name}")
            console_print(f"- {template.id} [dim]({template.source.value}) {shorten_path(str(template_file))}[/dim]: ", end='')
            if len(failures_list) > 0:
                failures_found = True
                console_print(f"[red]is not valid[/red] ({len(failures_list)} issues)")
                failures = '  ' + f'\n  '.join(failures_list)
                console_print(failures)
                console_print()
            else:
                console_print("[green]is valid[/green]")
        except click.ClickException as e:
            failures_found = True
            template_source = classify_path(template_file)
            error_lines = '  ' + '\n  '.join([x for x in e.message.split('\n')]) + '\n'
            console_print(f"""- {f"{template_id} " if template_id else ''}[dim]({template_source.value}) {shorten_path(str(template_file))}[/dim]: [red]is not valid[/red] {f'({model_failures_count} issues)' if model_failures_count > 0 else '(1 issue)'}\n  [red]Failed to load template{f" {template_id}" if template_id else ""}{f" ({template_name})" if template_name else ""}[/red]:\n{error_lines}""")
        except Exception as e:
            failures_found = True
            template_source = classify_path(template_file)
            console_print(f"""- {f"{template_id} " if template_id else ''}[dim]({template_source.value}) {shorten_path(str(template_file))}[/dim]: [red]is not valid[/red] (1 issue)\n  [red]Failed to load template{f" {template_id}" if template_id else ""}{f" ({template_name})" if template_name else ""}[/red]:\n  {str(e)}""")

    if failures_found:
        sys.exit(1)
