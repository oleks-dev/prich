import click
import yaml
from typing import Dict
from prich.core.utils import console_print_debug
from prich.core.template_utils import should_run_step
from prich.core.steps.step_render_template import render_template
from prich.core.steps.step_run_command import run_command_step
from prich.core.steps.step_send_to_llm import send_to_llm

from prich.models.template import LLMStep, PythonStep, RenderStep, \
    CommandStep, ValidateStepOutput
from prich.core.utils import console_print, is_quiet, is_only_final_output, \
    is_verbose, models_equal
from prich.core.loaders import get_env_vars
from prich.core.variable_utils import replace_env_vars, expand_vars

def validate_step_output(validate_step: ValidateStepOutput, value: str, variables: Dict[str, any]) -> bool:
    import re
    matched = re.search(
        expand_vars([validate_step.match], variables=variables, env_vars=get_env_vars())[0],
        value
    ) if validate_step and validate_step.match else True
    not_matched = not re.search(
        expand_vars([validate_step.not_match], variables=variables, env_vars=get_env_vars())[0],
        value
    ) if validate_step and validate_step.not_match else True

    if matched and not_matched:
        return True  # validation passed
    return False

def validate_step_exit_code(validate_step: ValidateStepOutput, exit_code: int, variables: Dict[str, any]) -> bool:
    try:
        if validate_step.match_exit_code is not None and exit_code != int(expand_vars([validate_step.match_exit_code], variables=variables, env_vars=get_env_vars())[0]):
            return False
        if validate_step.not_match_exit_code is not None and exit_code == int(expand_vars([validate_step.not_match_exit_code], variables=variables, env_vars=get_env_vars())[0]):
            return False
    except Exception as e:
        raise click.ClickException(f"Failed to validate step exit code: {str(e)}")
    return True

def run_step(step_idx, config, provider, template, variables):
    """ Run step during run_template """
    step = template.steps[step_idx-1]
    step_return_exit_code = None  # Used only for subprocess execute commands
    if not is_verbose() and step.name == template.steps[-1].name and step.output_console is None:
        # show final step output when non-verbose execution
        step.output_console = True

    if is_verbose():
        step_brief = f"\n• Step #{step_idx}: {step.name}"
    else:
        step_brief = f"• {step.name}"

    should_run = should_run_step(step.when, variables)
    if (not should_run and is_verbose()) or should_run:
        when_expression = f" (\"when\" expression \"{step.when}\" is {should_run})" if step.when else ""
        console_print(
            f"[dim]{step_brief}{' - Skipped' if not should_run else ''}{when_expression if is_verbose() else ''}[/dim]")

    # Set output variable to None
    if step.output_variable:
        variables[step.output_variable] = None

    if not should_run:
        return None, None

    output_var = step.output_variable
    if isinstance(step, (PythonStep, CommandStep)):
        step_output, step_return_exit_code = run_command_step(template, step, variables)
    elif isinstance(step, RenderStep):
        step_output = render_template(step, variables)
    elif isinstance(step, LLMStep):
        step_output = send_to_llm(template, step, provider, config, variables)
    else:
        raise click.ClickException(f"Step {step.type} type is not supported.")

    if is_verbose():
        if step.extract_variables or step.filter:
            console_print(f"[dim]Output:\n{step_output}[/dim]")
    step.postprocess_extract_vars(out=step_output, variables=variables)
    step_output = step.postprocess_filter(out=step_output)
    if is_verbose():
        if step.extract_variables:
            for spec in step.extract_variables:
                console_print(
                    f"""[dim]Inject {repr(spec.regex)} {f'({len(variables.get(spec.variable))} matches) ' if spec.multiple else ''}→ {spec.variable}: {f'{repr(variables.get(spec.variable))}' if isinstance(variables.get(spec.variable), str) else variables.get(spec.variable)}[/dim]""")
        if step.filter:
            if step.filter.strip is not None:
                console_print(f"[dim]Strip output spaces: {step.filter.strip}[/dim]")
            if step.filter.strip_prefix:
                console_print(f"[dim]Strip output prefix: \"{step.filter.strip_prefix}\"[/dim]")
            if step.filter.slice_start or step.filter.slice_end:
                console_print(
                    f"[dim]Slice output text{f' from {step.filter.slice_start}' if step.filter.slice_start else ''}{f' to {step.filter.slice_end}' if step.filter.slice_end else ''}[/dim]")
            if step.filter.regex_extract:
                console_print(f"[dim]Apply regex: '{step.filter.regex_extract}'[/dim]")
            if step.filter.regex_replace:
                replace_details = '\n                     '.join(
                    [f"'{x}' → '{y}'" for x, y in step.filter.regex_replace])
                console_print(f"[dim]Apply regex replace: {replace_details}[/dim]")

    # Store last output
    last_output = step_output

    if output_var:
        variables[output_var] = step_output
    if step.output_file:
        save_to_file = step.output_file.name
        try:
            write_mode = step.output_file.mode[:1] if step.output_file.mode else 'w'
            with open(save_to_file, write_mode) as step_output_file:
                if is_verbose():
                    console_print(
                        f"[dim]{'Save' if write_mode == 'w' else 'Append'} output to file: {save_to_file}[/dim]")
                step_output_file.write(step_output)
        except Exception as e:
            raise click.ClickException(f"Failed to save output to file {save_to_file}: {e}")
    # Print step output to console
    if ((step.output_console or is_verbose()) and not (
    isinstance(step, LLMStep))) and not is_only_final_output() and not is_quiet():
        console_print(step_output, markup=False)
    return last_output, step_return_exit_code

def run_step_validation(step, step_output, step_return_exit_code, variables):
    # Validate step output, used in run_template
    skip_following_steps = False
    if step.validate_:
        if isinstance(step.validate_, ValidateStepOutput):
            step_validate = [step.validate_]
        else:
            step_validate = step.validate_
        idx = 0
        for validate in step_validate:
            idx += 1
            validated = True
            if isinstance(step, (PythonStep, CommandStep)) and (
                    validate.match_exit_code is not None or validate.not_match_exit_code is not None):
                validated = validate_step_exit_code(validate, step_return_exit_code, variables)
            elif validate.match_exit_code is not None or validate.not_match_exit_code is not None:
                raise click.ClickException(
                    "Step validation using 'match_exitcode' and/or 'not_match_exitcode' supported only in 'python' and 'command' step types.")
            if validated:
                validated = validate_step_output(validate, step_output, variables)
            if not validated:
                action = validate.on_fail
                failure_msg = validate.message or "Validation failed for step output"
                if action == "warn":
                    console_print(f"[yellow]Warning: {failure_msg}![/yellow]")
                elif action == "error":
                    raise click.ClickException(failure_msg)
                elif action == "skip":
                    console_print(f"[yellow]{failure_msg} – skipping next steps.[/yellow]")
                    skip_following_steps = True
                    break
                elif action == "continue":
                    console_print(f"[yellow]{failure_msg} – continue.[/yellow]")
                    pass
                else:
                    raise click.ClickException(f"Validation type {action} is not supported.")
            else:
                if is_verbose() and len(step_validate) > 1:
                    console_print(f"[dim]Validation #{idx} [green]passed[/green].[/dim]")
        if is_verbose():
            console_print(f"[dim][green]Validation{'s' if len(step_validate) > 1 else ''} completed.[/green][/dim]")
    return skip_following_steps

def run_template(template_id, **kwargs):
    from pathlib import Path
    from pydantic import ValidationError as PydanticValidationError
    from prich.core.loaders import get_loaded_config, get_loaded_template, load_template_model, _load_yaml
    from prich.cli.validate import template_model_doctor

    config, _ = get_loaded_config()
    provider = kwargs.get('provider')
    output_file = kwargs.get('output')
    debug = kwargs.get('debug')

    template = get_loaded_template(template_id)

    variables = template.prepare_variables(cli_options=kwargs, env_vars=get_env_vars())

    variables_stash = {}
    if debug:
        console_print_debug("[dim]Initial variables:[/dim]")
        for k, v in variables.items():
            if k != "builtin":
                console_print_debug(f"[green]{k}[/green] = [cyan]{v}[/cyan]")

    if template.steps:
        step_idx = 1
        last_output = ""
        last_step_return_exit_code = None
        skip_following_steps = False  # used with validate
        debug_user_selected_action = None  # used with debug
        while step_idx <= len(template.steps):
            if debug and debug_user_selected_action in ["r", "b", "c", "v"]:
                reload_template = None
                try:
                    reload_template = load_template_model(Path(template.file))
                except PydanticValidationError as e:
                    console_print_debug("[red]Exception during template load:[/red]")
                    found_issues = template_model_doctor(_load_yaml(Path(template.file)), e)
                    for found_issue in found_issues:
                        console_print_debug(f"[red]{found_issue}[/red]")
                except Exception as e:
                    console_print_debug("[red]Exception during template load:[/red]")
                    console_print_debug(f"[red]{str(e)}[/red]")
                if reload_template is not None and not models_equal(reload_template, template):
                    console_print_debug("[yellow]Template change detected[/yellow] [dim]- reloading[/dim]")
                    reload_variables = reload_template.prepare_variables(cli_options=kwargs, env_vars=get_env_vars())
                    console_print_debug("[dim]Updating stashed variables[/dim]")
                    for k,v in variables_stash.items():
                        v.update(reload_variables)
                    console_print_debug("[dim]Updating current variables[/dim]")
                    variables.update(reload_variables)
                    console_print_debug("[dim]Updating template[/dim]")
                    template = reload_template
            if debug and debug_user_selected_action in ["r", "b"]:
                console_print_debug(f"[dim]Restoring variables from before step {step_idx}[/dim]")
                variables = dict(variables_stash[step_idx])
            elif debug and debug_user_selected_action != "v":
                console_print_debug(f"[dim]Stash variables before step {step_idx}[/dim]")
                variables_stash[step_idx] = dict(variables)

            if not debug or (debug and debug_user_selected_action != "v"):
                if debug:
                    console_print_debug(f"[dim]--- Step {template.steps[step_idx-1].type} [/dim][cyan]{template.steps[step_idx-1].name}[/cyan] #{step_idx}")
                output, last_step_return_exit_code = run_step(
                    step_idx=step_idx,
                    config=config,
                    provider=provider,
                    template=template,
                    variables=variables
                )
                if output is not None:
                    last_output = output

            try:
                skip_following_steps = run_step_validation(
                    step=template.steps[step_idx-1],
                    step_output=last_output,
                    step_return_exit_code=last_step_return_exit_code,
                    variables=variables
                )
            except Exception as e:
                if not debug:
                    raise
                else:
                    console_print_debug(f"[red]Exception[/red] during validation, would be terminated here in non-debug mode: [red]{e}[/red]")
            if debug:
                debug_user_selected_action = None
                while not debug_user_selected_action:
                    console_print_debug(
                        f"[white]([cyan]c[/cyan])ontinue, ([cyan]r[/cyan])epeat step{', repeat ([cyan]v[/cyan])alidate' if template.steps[step_idx-1].validate_ else ''}, ([cyan]t[/cyan])erminate{', step ([cyan]b[/cyan])ack' if step_idx > 1 else ''}; show ([cyan]s[/cyan])tep, variab([cyan]l[/cyan])es, variables stas([cyan]h[/cyan]):[/white] ",
                        end="")
                    try:
                        user_input = None
                        accepted_keys = ['c', 'r', 't', 'l', 's', 'h']
                        if step_idx > 1:
                            accepted_keys.append('b')
                        if template.steps[step_idx-1].validate_:
                            accepted_keys.append('v')
                        while user_input not in accepted_keys:
                            user_input = click.getchar()  # returns a 1-char string
                            # user_input = input()  # used for debug
                    except KeyboardInterrupt:
                        user_input = "t"
                    console_print(f"[cyan]{user_input}[/cyan]")
                    if user_input in ["t", "terminate", "quit", "exit"]:
                        console_print("[red]Terminated during debug pause.[/red]")
                        exit(1)
                    elif step_idx > 1 and user_input == "b":
                        console_print_debug(f"[dim]Drop variables stash from step {step_idx}[/dim]")
                        variables_stash.pop(step_idx)
                        step_idx -= 1
                        console_print_debug(f"[dim]Return to step {step_idx}[/dim]")
                        debug_user_selected_action = "b"
                    elif user_input == "c":
                        debug_user_selected_action = "c"
                    elif user_input == "s":
                        console_print_debug(f"[dim]Step #{step_idx}:[/dim]")
                        tpl_model_dump = template.steps[step_idx-1].model_dump(exclude_none=True)
                        if tpl_model_dump.get("validate_"):
                            tpl_model_dump["validate"] = tpl_model_dump.get("validate_")
                            tpl_model_dump.pop("validate_")
                        console_print(f"[cyan]{yaml.safe_dump(tpl_model_dump, sort_keys=False)}[/cyan]")
                    elif user_input == "r":
                        debug_user_selected_action = "r"
                    elif user_input == "v":
                        debug_user_selected_action = "v"
                    elif user_input == "l":
                        if not variables:
                            console_print_debug("[green]no variables[/green]")
                        else:
                            console_print_debug("[dim]Variables:[/dim]")
                            for k,v in variables.items():
                                if k != "builtin":
                                    console_print_debug(f"[green]{k}[/green] = [cyan]{v}[/cyan]")
                    elif user_input == "h":
                        console_print_debug(f"[dim]Stashed variables[/dim]")
                        for stash, stash_vars in variables_stash.items():
                            console_print_debug(f"[dim]before step {template.steps[stash-1].type} {template.steps[stash-1].name} #{stash}:[/dim]")
                            for k,v in stash_vars.items():
                                if k != "builtin":
                                    console_print_debug(f"[green]{k}[/green] = [cyan]{v}[/cyan]")

            if skip_following_steps and not debug_user_selected_action in ["r", "b", "v"]:  # used with validate when skip matched
                break

            if debug_user_selected_action not in ["r", "b", "v"]:
                step_idx += 1

        # Save last step output if output file option added
        if output_file:
            with open(output_file, 'w') as final_output_file:
                final_output_file.write(last_output)
        # Print last step output if last option enabled
        if is_only_final_output() and not is_quiet():
            print(last_output, flush=True)
    else:
        raise click.ClickException(f"No steps found in template {template.id}.")
