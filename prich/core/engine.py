import click
from typing import Dict

from prich.core.template_utils import should_run_step
from prich.core.steps.step_render_template import render_template
from prich.core.steps.step_run_command import run_command_step
from prich.core.steps.step_sent_to_llm import send_to_llm

from prich.models.template import LLMStep, PythonStep, RenderStep, \
    CommandStep, ValidateStepOutput
from prich.core.utils import console_print, is_quiet, is_only_final_output, \
    is_verbose
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

def run_template(template_id, **kwargs):
    from prich.core.loaders import get_loaded_config, get_loaded_template

    config, _ = get_loaded_config()
    provider = kwargs.get('provider')
    output_file = kwargs.get('output')

    template = get_loaded_template(template_id)

    variables = {}
    for var in template.variables:
        cli_option = var.cli_option
        if cli_option:
            option_name = cli_option.lstrip("-").replace("-", "_")
            variables[var.name] = replace_env_vars(kwargs.get(option_name, var.default), get_env_vars())
        else:
            variables[var.name] = replace_env_vars(kwargs.get(var.name, var.default), get_env_vars())
        if var.required and variables.get(var.name) is None:
            raise click.ClickException(f"Missing required variable {var.name}")

    if template.steps:
        step_return_exit_code = None  # Used only for subprocess execute commands
        step_idx = 0
        last_output = ""
        skip_following_steps = True  # used with validate
        for step in template.steps:
            step_idx += 1

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
                console_print(f"[dim]{step_brief}{' - Skipped' if not should_run else ''}{when_expression if is_verbose() else ''}[/dim]")
            if not should_run:
                continue

            # Set output variable to None
            if step.output_variable:
                variables[step.output_variable] = None

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
                        console_print(f"""[dim]Inject {repr(spec.regex)} {f'({len(variables.get(spec.variable))} matches) ' if spec.multiple else ''}→ {spec.variable}: {f'{repr(variables.get(spec.variable))}' if isinstance(variables.get(spec.variable), str) else variables.get(spec.variable)}[/dim]""")
                if step.filter:
                    if step.filter.strip is not None:
                        console_print(f"[dim]Strip output spaces: {step.filter.strip}[/dim]")
                    if step.filter.strip_prefix:
                        console_print(f"[dim]Strip output prefix: \"{step.filter.strip_prefix}\"[/dim]")
                    if step.filter.slice_start or step.filter.slice_end:
                        console_print(f"[dim]Slice output text{f' from {step.filter.slice_start}' if step.filter.slice_start else ''}{f' to {step.filter.slice_end}' if step.filter.slice_end else ''}[/dim]")
                    if step.filter.regex_extract:
                        console_print(f"[dim]Apply regex: '{step.filter.regex_extract}'[/dim]")
                    if step.filter.regex_replace:
                        replace_details = '\n                     '.join([f"'{x}' → '{y}'" for x,y in step.filter.regex_replace])
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
                            console_print(f"[dim]{'Save' if write_mode == 'w' else 'Append'} output to file: {save_to_file}[/dim]")
                        step_output_file.write(step_output)
                except Exception as e:
                    raise click.ClickException(f"Failed to save output to file {save_to_file}: {e}")
            # Print step output to console
            if ((step.output_console or is_verbose()) and not (isinstance(step, LLMStep))) and not is_only_final_output() and not is_quiet():
                console_print(step_output, markup=False)
            # Validate
            if step.validate_:
                if isinstance(step.validate_, ValidateStepOutput):
                    step.validate_ = [step.validate_]
                idx = 0
                for validate in step.validate_:
                    idx += 1
                    if isinstance(step, (PythonStep, CommandStep)) and (validate.match_exit_code is not None or validate.not_match_exit_code is not None):
                        validated = validate_step_exit_code(validate, step_return_exit_code, variables)
                        if validated:
                            validated = validate_step_output(validate, step_output, variables)
                    elif validate.match_exit_code is not None or validate.not_match_exit_code is not None:
                        raise click.ClickException("Step validation using 'match_exitcode' and/or 'not_match_exitcode' supported only in 'python' and 'command' step types.")
                    else:
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
                        if is_verbose() and len(step.validate_) > 1:
                            console_print(f"[dim]Validation #{idx} [green]passed[/green].[/dim]")
                if is_verbose():
                    console_print(f"[dim][green]Validation{'s' if len(step.validate_) > 1 else ''} completed.[/green][/dim]")
                if skip_following_steps:  # used with validate when skip matched
                    break
        # Save last step output if output file option added
        if output_file:
            with open(output_file, 'w') as final_output_file:
                final_output_file.write(last_output)
        # Print last step output if last option enabled
        if is_only_final_output() and not is_quiet():
            print(last_output, flush=True)
    else:
        raise click.ClickException(f"No steps found in template {template.id}.")
