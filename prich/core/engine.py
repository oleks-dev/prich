import click
from pathlib import Path
from typing import Dict, List

from click import ClickException
from prich.constants import RESERVED_RUN_TEMPLATE_CLI_OPTIONS
from prich.models.config import ConfigModel
from prich.models.template import TemplateModel, PromptFields, PipelineStep, LLMStep, PythonStep, RenderStep, \
    CommandStep, ValidateStepOutput
from prich.core.utils import console_print, replace_env_vars, shorten_path, is_quiet, is_only_final_output, \
    is_verbose, get_prich_dir, is_just_filename

jinja_env = {}

def expand_vars(args: List[str], internal_vars: Dict[str, str] = None):
    """
    Expand internal variables ({{VAR}}, {{ VAR }}) and environment variables ($VAR or ${VAR}) in a list of arguments.
    
    Args:
        args (list): List of argument strings, e.g., ["tool", "--path={{HOME_DIR}}", "--file=$FILE"].
        internal_vars (dict, optional): Dictionary of internal variable names to values, e.g., {"HOME_DIR": "/home/user"}.
    
    Returns:
        list: New list with variables expanded.
    """
    import re

    # Default to empty dict if no internal variables provided
    internal_vars = internal_vars or {}
    
    def replace_internal_var(match):
        """Replace {{VAR}} with the value from internal_vars or keep unchanged if not found."""
        var_name = match.group(1)
        return internal_vars.get(var_name, match.group(0))  # Keep original if not found
        
    # Patterns for internal ({{VAR}}) variables
    internal_pattern = r'\{\{\s*([^}\s]+)\s*\}\}'
    
    expanded_args = []
    for arg in args:
        if type(arg) == str:
            # First expand internal variables
            arg = re.sub(internal_pattern, replace_internal_var, arg)
            # Then expand environment variables ($VAR or ${VAR})
            arg = replace_env_vars(arg)
        expanded_args.append(arg)
    
    return expanded_args


def get_jinja_env(name: str, conditional_expression_only: bool = False):
    from jinja2 import Environment, StrictUndefined, FileSystemLoader

    def _read_file_contents(filename):
        try:
            cwd = Path.cwd()
            file_path = (cwd / filename).resolve()
            if cwd not in file_path.parents and cwd != file_path:
                raise click.ClickException(f"File is outside the current working directory")
            with file_path.open("r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            raise click.ClickException(f"File {filename} not found")
        except UnicodeDecodeError:
            return click.ClickException(f"Error: File '{filename}' is not a valid text file")
        except Exception as e:
            raise click.ClickException(f"Error reading file '{filename}': {e}")

    def include_file(filename):
        return _read_file_contents(filename)

    def include_file_with_line_numbers(filename):
        lines = _read_file_contents(filename).split('\n')
        return '\n'.join([f"{i+1} {line}" for i, line in enumerate(lines)])

    env_name = f"{name}{'_cond' if conditional_expression_only else ''}"
    if not jinja_env.get(env_name):
        if conditional_expression_only:
            env = Environment(undefined=StrictUndefined)
            env.filters.clear()
            # Add a safe whitelist
            env.filters.update({
                "lower": str.lower,
                "upper": str.upper,
                "strip": str.strip,
                "length": len,
                "int": int,
                "float": float,
                "bool": lambda x: bool(x),
            })
            jinja_env[env_name] = env
        else:
            env = Environment(
                loader=FileSystemLoader(Path.cwd()),
                undefined=StrictUndefined
            )
            env.filters['include_file'] = include_file
            env.filters['include_file_with_line_numbers'] = include_file_with_line_numbers
            jinja_env[env_name] = env
    return jinja_env[env_name]

def should_run_step(when_expr: str, variables: dict) -> bool:
    try:
        if when_expr in [None, ""]:
            return True
        if when_expr.startswith("{{") and when_expr.endswith("}}"):
            when_expr = when_expr[2:-2].strip()
        template = get_jinja_env("when", conditional_expression_only=True).from_string(f"{{{{ {when_expr} }}}}")
        rendered = template.render(variables).strip().lower()
        return rendered in ("true", "1", "yes")
    except Exception as e:
        raise ValueError(f"Invalid `when` expression: {when_expr} - {str(e)}")

def validate_step_output(validate_step: ValidateStepOutput, value: str)-> bool:
    import re
    matched = re.search(validate_step.match, value) if validate_step and validate_step.match else True
    not_matched = not re.search(validate_step.not_match, value) if validate_step and validate_step.not_match else True

    if matched and not_matched:
        return True  # validation passed
    return False

def run_command_step(template: TemplateModel, step: PythonStep | CommandStep, variables: Dict[str, str]) -> str:
    import subprocess
    from rich.console import Console
    console = Console()

    method = step.call
    try:
        template_dir = Path(template.folder)
    except Exception as e:
        raise click.ClickException(f"Template folder was not detected properly: {e}")

    if type(step) == PythonStep and step.type == "python":
        method_path = template_dir / "scripts" / method
        if not method_path.exists():
            raise click.ClickException(f"Python script not found: {method_path}")
        if not method.endswith(".py"):
            raise click.ClickException(f"Python script file should end with .py: {method_path}")

        if template.venv in ["shared", "isolated"]:
            if template.venv == "shared":
                venv_path = get_prich_dir() / "venv"
            else:
                venv_path = template_dir / "scripts" / "venv"
            python_path = venv_path / "bin" / "python"
            if not python_path.exists():
                raise click.ClickException(f"{template.venv.capitalize()} venv python not found: {python_path}")
            cmd = [str(python_path), str(method_path)]
        elif template.venv is None:
            cmd = ["python", str(method_path)]
        else:
            raise click.ClickException(f"Python script venv {template.venv} is not supported.")
    elif type(step) == CommandStep and step.type == "command":
        if is_just_filename(method) and (template_dir / "scripts" / method).exists():
            cmd = [str(template_dir / "scripts" / method)]
        else:
            cmd = [method]
    else:
        raise click.ClickException(f"Template command step type {step.type} is not supported.")

    # Inputs / Variables List
    expanded_args = expand_vars(step.args, variables)
    [cmd.append(arg) for arg in expanded_args]

    try:
        console_print(f"[dim]Execute {step.type} [green]{' '.join(cmd)}[/green][/dim]")
        if not is_quiet() and not is_only_final_output():
            with console.status("Processing..."):
                result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        else:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return result.stdout
    except subprocess.CalledProcessError as e:
        raise click.ClickException(f"Execution error in {method}: {e.stderr}")
    except Exception as e:
        raise click.ClickException(f"Unexpected error in {method}: {str(e)}")

def render_template(template_text: str, variables: dict = Dict[str, str]) -> str:
    import datetime
    import os
    import getpass
    import platform

    if not template_text:
        return ""

    builtin = {
        "now": datetime.datetime.now(),
        "now_utc": datetime.datetime.now(datetime.UTC),
        "today": datetime.datetime.today().date(),
        "cwd": os.getcwd(),
        "user": getpass.getuser(),
        "hostname": platform.node(),
    }
    variables["builtin"] = builtin
    try:
        rendered_text = get_jinja_env("template").from_string(template_text).render(**variables).strip()
    except Exception as e:
        raise click.ClickException(f"Render step error: {str(e)}")
    return rendered_text

def render_prompt(config: ConfigModel, fields: PromptFields, variables: Dict[str, str], mode: str) -> str:
    """ Render Prompt using provider mode prompt template (used for raw prompt construction) """
    if not fields.prompt and not fields.user:
        raise ClickException("There should be Prompt or User field at least.")
    mode_prompt = [x for x in config.model_dump().get("provider_modes") if x.get("name")==mode]
    if len(mode_prompt) == 0:
        raise click.ClickException(f"Prompt mode {mode} is not supported.")
    prompt_fields = render_template(mode_prompt[0].get("prompt"), fields.model_dump())
    prompt = render_template(prompt_fields, variables)
    return prompt

# TODO: Cross check if the change here makes sense with system and prompt
def render_prompt_fields(fields: PromptFields, variables: Dict[str, str]) -> PromptFields:
    """ Render Prompt fields (used when provider supports prompt fields templates like system/user """
    if not fields.prompt and not fields.user or (fields.prompt and fields.system):
        raise ClickException("There should be Prompt or User or System and User fields.")
    rendered_fields = PromptFields()
    if fields.system:
        rendered_fields.system = render_template(fields.system, variables)
    if fields.user:
        rendered_fields.user = render_template(fields.user, variables)
    if fields.prompt:
        rendered_fields.prompt = render_template(fields.prompt, variables)
    return rendered_fields


def get_variable_type(variable_type: str) -> click.types:
    TYPE_MAPPING = {"str": click.STRING, "int": click.INT, "bool": click.BOOL, "path": click.Path}
    return TYPE_MAPPING.get(variable_type.lower(), None)

def create_dynamic_command(config, template: TemplateModel) -> click.Command:
    options = []
    for arg in template.variables if template.variables else []:
        arg_name = arg.name
        arg_type = get_variable_type(arg.type)
        help_text = arg.description or f"{arg_name} option"
        cli_option = arg.cli_option or f"--{arg_name}"
        if cli_option in RESERVED_RUN_TEMPLATE_CLI_OPTIONS:
            raise click.ClickException(f"{arg_name} cli option uses a reserved option name: {cli_option}")

        if arg_type == click.BOOL:
            options.append(click.Option([cli_option], is_flag=True, default=arg.default or False, show_default=True, help=help_text))
        elif arg_type:
            options.append(click.Option([cli_option], type=arg_type, default=arg.default, required=arg.required, show_default=True, help=help_text))
        elif arg.type.startswith("list["):
            list_type = get_variable_type(arg.type.split('[')[1][:-1])
            if not list_type:
                raise click.ClickException(f"Failed to parse list type for {arg.name}")
            options.append(click.Option([cli_option], type=list_type, multiple=True, default=arg.default, required=arg.required, show_default=True, help=help_text))
        else:
            raise click.ClickException(f"Unsupported variable type: {arg.type}")

    options.extend([
        click.Option(["-g", "--global", "global_only"], is_flag=True, default=False, help="Use global config and template"),
        click.Option(["-l", "--local", "local_only"], is_flag=True, default=False, help="Use local config and template"),
        click.Option(["-o", "--output"], type=click.Path(), default=None, show_default=True, help="Save LLM output to file"),
        click.Option(["-p", "--provider"], type=click.Choice(config.providers.keys()), show_default=True, help="Override LLM provider"),
        click.Option(["-v", "--verbose"], is_flag=True, default=False, help="Verbose mode"),
        click.Option(["-q", "--quiet"], is_flag=True, default=False, help="Suppress all output"),
        click.Option(["-f", "--only-final-output"], is_flag=True, default=False, help="Suppress output and show only the last step output")
    ])

    @click.pass_context
    def dynamic_command(ctx, **kwargs):
        console_print(f"[dim]Template: [green]{template.name}[/green] ({template.version}), {template.source.value}, args: {', '.join([f'{k}={v}' for k,v in kwargs.items() if v])}[/dim]")
        if is_verbose():
            console_print(f"[dim]{template.description}[/dim]")
        run_template(template.id, **kwargs)

    return click.Command(name=template.id, callback=dynamic_command, params=options, help=f"{template.description if template.description else ''}", epilog=f"{template.name} (ver: {template.version}, {template.source.value})")

def send_to_llm(template: TemplateModel, step: LLMStep, provider: str, config: ConfigModel, variables: dict) -> str:
    from prich.llm_providers.get_llm_provider import get_llm_provider

    if not step.prompt and (not step.prompt.system and not step.prompt.user):
        raise click.ClickException("Prompt template must define 'system' and/or 'user' fields")
    # Use Provider from arg overload
    if provider:
        selected_provider_name = provider
    # Use LLM Step Provider assignment from template
    elif step.provider:
        selected_provider_name = step.provider
    # Use Provider to template assignment from config settings
    elif config.settings.provider_assignments and template.id in config.settings.provider_assignments.keys():
        selected_provider_name = config.settings.provider_assignments[template.id]
    # Use default provider from config
    else:
        selected_provider_name = config.settings.default_provider
    selected_provider = config.providers[selected_provider_name]

    prompt = None
    prompt_fields = None
    if selected_provider.mode:
        prompt = render_prompt(config, step.prompt, variables, selected_provider.mode)
    else:
        prompt_fields = render_prompt_fields(step.prompt, variables)
    if not prompt and not prompt_fields:
        raise click.ClickException(f"Prompt is empty in step {step.name}.")

    llm_provider = get_llm_provider(selected_provider_name, selected_provider)
    if ((not step.output_console and not is_verbose()) or is_quiet()) and llm_provider.show_response:
        # Override show response when quiet mode
        llm_provider.show_response = False

    # prompt lines
    prompt_lines = []
    if prompt:
        prompt_lines.append(prompt)
    else:
        if prompt_fields.system:
            prompt_lines.append(prompt_fields.system)
        if prompt_fields.user:
            prompt_lines.append(prompt_fields.user)
        if prompt_fields.prompt:
            prompt_lines.append(prompt_fields.prompt)
    prompt_full = '\n'.join(prompt_lines)

    console_print(f"[dim]Sending prompt to LLM ([green]{llm_provider.name}[/green]), {len(prompt_full)} chars[/dim]")
    if is_verbose():
        console_print(prompt_full, markup=False)
        console_print()
        console_print("[dim]LLM Response:[/dim]")
    try:
        if not is_quiet() and not is_only_final_output() and not llm_provider.show_response:
            from rich.console import Console
            console = Console()
            with console.status("Thinking..."):
                response = llm_provider.send_prompt(
                    prompt=prompt,
                    system=prompt_fields.system if prompt_fields else None,
                    user=prompt_fields.user if prompt_fields else None
                )
        else:
            response = llm_provider.send_prompt(
                prompt=prompt,
                system=prompt_fields.system if prompt_fields else None,
                user=prompt_fields.user if prompt_fields else None
            )
        step_output = selected_provider.postprocess_output(response)
        if (is_verbose() or step.output_console) and not llm_provider.show_response and not is_quiet():
            console_print(step_output, markup=False)
    except Exception as e:
        raise click.ClickException(f"Failed to get LLM response: {str(e)}")
    return step_output

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
            variables[var.name] = replace_env_vars(kwargs.get(option_name, var.default))
        else:
            variables[var.name] = replace_env_vars(kwargs.get(var.name, var.default))
        if var.required and variables.get(var.name) is None:
            raise click.ClickException(f"Missing required variable {var.name}")

    if template.steps:
        step_idx = 0
        last_output = ""
        for step in template.steps:
            step_idx += 1

            if not is_verbose() and step.name == template.steps[-1].name and step.output_console is None:
                # show final step output when non-verbose execution
                step.output_console = True

            step_brief = f"\nStep #{step_idx}: {step.name}"
            should_run = should_run_step(step.when, variables)
            when_expression = f" (\"when\" expression \"{step.when}\" is {should_run})" if step.when else ""
            if (not should_run and is_verbose()) or should_run:
                console_print(f"[dim]{step_brief}{' - Skipped' if not should_run else ''}{when_expression}[/dim]")
            if not should_run:
                continue

            # Set output variable to None
            if step.output_variable:
                variables[step.output_variable] = None

            output_var = step.output_variable
            if type(step) in [PythonStep, CommandStep]:
                step_output = run_command_step(template, step, variables)
            elif type(step) == RenderStep:
                if is_verbose():
                    console_print("[dim]Render template:[/dim]")
                    console_print(step.template)
                    console_print()
                    console_print("[dim]Result:[/dim]")
                step_output = render_template(step.template, variables)
            elif type(step) == LLMStep:
                step_output = send_to_llm(template, step, provider, config, variables)
            else:
                raise click.ClickException(f"Step {step.type} type is not supported.")

            if is_verbose():
                if step.extract_vars or step.output_regex or step.strip_output_prefix or step.slice_output_start or step.slice_output_end:
                    console_print(f"[dim]Output: '{step_output}'[/dim]")
            step.postprocess_extract_vars(output=step_output, variables=variables)
            step_output = step.postprocess_output(output=step_output)
            if is_verbose():
                if step.extract_vars:
                    for spec in step.extract_vars:
                        console_print(f"[dim]Inject \"{spec.regex}\" {f'({len(variables.get(spec.variable))} matches) ' if spec.multiple else ''}→ {spec.variable}: {f'{variables.get(spec.variable)}' if type(variables.get(spec.variable) == str) else variables.get(spec.variable)}[/dim]")
                if step.output_regex:
                    console_print(f"[dim]Apply regex: \"{step.output_regex}\"[/dim]")
                if step.strip_output_prefix:
                    console_print(f"[dim]Strip output prefix: \"{step.strip_output_prefix}\"[/dim]")
                if step.slice_output_start or step.slice_output_end:
                    console_print(f"[dim]Slice output text{f' from {step.slice_output_start}' if step.slice_output_start else ''}{f' to {step.slice_output_end}' if step.slice_output_end else ''}[/dim]")

            # Store last output
            last_output = step_output

            if output_var:
                variables[output_var] = step_output
            if step.output_file:
                if step.output_file.startswith('.'):
                    save_to_file = step.output_file.replace('.', str(Path.cwd()), 1)
                elif step.output_file.startswith('~'):
                    save_to_file = step.output_file.replace('~', str(Path.home()), 1)
                else:
                    save_to_file = step.output_file
                try:
                    write_mode = step.output_file_mode[:1] if step.output_file_mode else 'w'
                    with open(save_to_file, write_mode) as step_output_file:
                        console_print(f"[dim]{'Save' if write_mode == 'w' else 'Append'} output to file: {save_to_file}[/dim]")
                        step_output_file.write(step_output)
                except Exception as e:
                    raise click.ClickException(f"Failed to save output to file {save_to_file}: {e}")
            # Print step output to console
            if ((step.output_console or is_verbose()) and (type(step) != LLMStep)) and not is_only_final_output() and not is_quiet():
                console_print(step_output)
            # Validate
            if step.validate_:
                if type(step.validate_) == ValidateStepOutput:
                    step.validate_ = [step.validate_]
                idx = 0
                for validate in step.validate_:
                    idx += 1
                    validated = validate_step_output(validate, step_output)
                    if not validated:
                        action = validate.on_fail
                        failure_msg = validate.message or "Validation failed for step output"
                        if action == "warn":
                            console_print(f"[yellow]Warning: {failure_msg}![/yellow]")
                        elif action == "error":
                            raise click.ClickException(failure_msg)
                        elif action == "skip":
                            console_print(f"[yellow]{failure_msg} – skipping next steps.[/yellow]")
                            break
                        elif action == "continue":
                            console_print(f"[yellow]{failure_msg} – continue.[/yellow]")
                            pass
                        else:
                            raise click.ClickException(f"Validation type {action} is not supported.")
                    else:
                        if is_verbose() and len(step.validate_) > 1:
                            console_print(f"[dim]Validation #{idx} [green]passed[/green].[/dim]")
                console_print(f"[dim][green]Validation{'s' if len(step.validate_) > 1 else ''} completed.[/green][/dim]")
        # Save last step output if output file option added
        if output_file:
            with open(output_file, 'w') as final_output_file:
                final_output_file.write(last_output)
        # Print last step output if last option enabled
        if is_only_final_output() and not is_quiet():
            print(last_output, flush=True)
    else:
        raise click.ClickException(f"No steps found in template {template.id}.")
