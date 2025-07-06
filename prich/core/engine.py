import click
from pathlib import Path
from typing import Dict, List

from prich.models.config import ConfigModel
from prich.models.template import TemplateModel, PromptFields, PipelineStep, LLMStep, PythonStep, RenderStep, CommandStep
from prich.core.utils import console_print, is_quiet, replace_env_vars, shorten_home_path

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
                return f"Error: File '{filename}' is outside the current working directory"
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

def run_command_step(template: TemplateModel, step: PythonStep | CommandStep, variables: Dict[str, str], config: ConfigModel, template_name: str, template_source: str) -> str:
    import subprocess
    from rich.console import Console
    console = Console()

    method = step.call
    prich_dir = (Path.cwd() if template_source == "local" else Path.home()) / ".prich"
    try:
        template_dir = Path(template.folder)
    except Exception as e:
        raise click.ClickException(f"Template folder was not detected properly: {e}")

    if type(step) == PythonStep and step.type == "python":
        method_path = template_dir / "scripts" / method
        if not method_path.exists():
            raise click.ClickException(f"Script not found: {method_path}")

        use_venv = True
        cmd = [str(method_path)]

        if template.venv == "shared":
            shared_venv = prich_dir / "venv"
            python_path = shared_venv / "bin/python"
            if use_venv and method.endswith(".py") and python_path.exists():
                cmd = [str(python_path), str(method_path)]
        elif template.venv == "isolated" and use_venv and method.endswith(".py"):
            isolated_venv = template_dir / "scripts" / "venv"
            if not isolated_venv.exists():
                raise click.ClickException(f"Isolated venv not found: {isolated_venv}")
            cmd = [str(isolated_venv / "bin/python"), str(method_path)]
        else:
            raise click.ClickException(f"Script with venv {template.venv} is not defined.")
    elif type(step) == CommandStep and step.type == "command":
        cmd = [method]
    else:
        raise click.ClickException(f"Template command step type {step.type} is not supported.")

    # Inputs / Variables List
    expanded_args = expand_vars(step.args, variables)
    [cmd.append(arg) for arg in expanded_args]

    try:
        console_print(f"Execute {step.type} [green]{' '.join(cmd)}[/green]")
        if not is_quiet():
            with console.status(f"Waiting"):
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            console_print(result.stdout)
        else:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise click.ClickException(f"Script error in {method}: {e.stderr}")
    except Exception as e:
        raise click.ClickException(f"Unexpected error in {method}: {str(e)}")

def render_template(template_dir: str, template_text: str, variables: dict = Dict[str, str]) -> str:
    if not template_text:
        return ""

    rendered_text = get_jinja_env("template").from_string(template_text).render(**variables).strip()
    return rendered_text

def render_prompt(fields: PromptFields, variables: Dict[str, str], template_dir: str, mode: str) -> str:
    import re
    system = render_template(template_dir, fields.system, variables)
    user = render_template(template_dir, fields.user, variables)
    prompt_string = render_template(template_dir, fields.prompt, variables)

    if system and not re.search(r"[.:?!…]$|```$", system.strip()):
        system += "."

    if mode in ["chatml", "anthropic", "flat", "mistral-instruct", "llama2-chat"]:
        if prompt_string:
            console_print("[yellow]Warning: 'prompt_string' field is ignored in non-plain modes.[/yellow]")

    if mode == "chatml":
        if not user:
            raise click.ClickException(f"Empty prompt: {mode} requires at least 'user' prompt.")
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": user})
        prompt = messages
    elif mode == "flat":
        if re.match(r"^(human|user|system|assistant):", user.strip(), re.IGNORECASE):
            prompt = user
        elif system and user:
            prompt = f"### System:\n{system}\n\n### User:\n{user}\n\n### Assistant:"
        elif user:
            prompt = f"### User:\n{user}\n\n### Assistant:"
        else:
            raise click.ClickException(f"Empty prompt: {mode} requires at least 'user' prompt.")
    elif mode == "plain":
        if not prompt_string:
            raise click.ClickException(f"Empty prompt: {mode} requires at least 'prompt_string' prompt.")
        prompt = prompt_string
    elif mode in ["mistral-instruct", "llama2-chat"]:
        if not user:
            raise click.ClickException(f"Empty prompt: {mode} requires at least 'user' prompt.")
        prompt = f"<s>[INST]\n{system}\n\n{user}\n[/INST]" if system else f"<s>[INST]\n{user}\n[/INST]"
    elif mode == "anthropic":
        if not user:
            raise click.ClickException(f"Empty prompt: {mode} requires at least 'user' prompt.")
        prompt = f"Human: {system}\n\n{user}\n\nAssistant:" if system else f"Human: {user}\n\nAssistant:"
    else:
        raise click.ClickException(f"Prompt mode {mode} is not supported.")

    return prompt

def get_variable_type(variable_type):
    TYPE_MAPPING = {"str": click.STRING, "int": click.INT, "bool": click.BOOL, "path": click.Path}
    return TYPE_MAPPING.get(variable_type, None)

def create_dynamic_command(config, template: TemplateModel):
    options = []
    for arg in template.variables if template.variables else []:
        arg_name = arg.name
        arg_type = get_variable_type(arg.type)
        help_text = arg.description or f"{arg_name} option"
        cli_option = arg.cli_option or f"--{arg_name}"
        reserved_options = ['-g', '--global', "-q", "--quiet", "-o", "--output", "-p", "--provider"]
        if cli_option in reserved_options:
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
        click.Option(["-g", "--global"], is_flag=True, default=False, help="Use global template"),
        click.Option(["-q", "--quiet"], is_flag=True, default=False, help="Suppress output except final prompt or LLM response"),
        click.Option(["--skip-llm"], is_flag=True, default=False, help="Skip sending prompt to LLM"),
        click.Option(["-o", "--output"], type=click.Path(), default=None, show_default=True, help="Save LLM output to file"),
        click.Option(["-p", "--provider"], type=click.Choice(config.providers.keys()), show_default=True, help="Select LLM provider")
    ])

    @click.pass_context
    def dynamic_command(ctx, **kwargs):
        console_print(f"Template: [green]{template.name}[/green], Args: {', '.join([f'[blue]{k}[/blue]=[blue]{v}[/blue]' for k,v in kwargs.items() if v])}")
        run_template(template.name, **kwargs)

    return click.Command(name=template.name, callback=dynamic_command, params=options, help=template.description, epilog=f"Template file: {shorten_home_path(template.file)}")

def send_to_llm(template, step, provider, config, variables, skip_llm, output):
    import json
    import sys
    from prich.llm_providers.get_llm_provider import get_llm_provider

    if not step.prompt or (not step.prompt.system and not step.prompt.user):
        raise click.ClickException("Prompt template must define 'system' and/or 'user' fields")
    # Use Provider from arg overload
    if provider:
        selected_provider_name = provider
    # Use LLM Step Provider assignment from template
    elif step.provider:
        selected_provider_name = step.provider
    # Use Provider to template assignment from config settings
    elif config.settings.provider_assignments and template.name in config.settings.provider_assignments.keys():
        selected_provider_name = config.settings.provider_assignments[template.name]
    # Use default provider from config
    else:
        selected_provider_name = config.settings.default_provider
    selected_provider = config.providers[selected_provider_name]

    prompt = render_prompt(step.prompt, variables, template.source, selected_provider.mode)
    if not prompt:
        raise click.ClickException("Prompt is empty.")

    if skip_llm:
        if type(prompt) is not str:
            prompt = json.dumps(prompt)
        if not is_quiet():
            console_print(prompt, markup=False)
        else:
            sys.stdout.write(prompt)
        return ""

    llm_provider = get_llm_provider(selected_provider_name, selected_provider)
    if is_quiet() and llm_provider.show_response:
        # Override show response when quiet mode
        llm_provider.show_response = False

    console_print(f"[bold]Sending prompt to LLM [/bold][blue]({llm_provider.name})[/blue][bold]:[/bold]")
    console_print(prompt, markup=False)

    if llm_provider.show_response:
        console_print("[bold]LLM Response:[/bold]")
    try:
        response = llm_provider.send_prompt(prompt)
        step_output = response.strip()
        if not llm_provider.show_response and not is_quiet():
            console_print("\n[bold]LLM Response:[/bold]")
            console_print(step_output, markup=False)
        elif is_quiet():
            sys.stdout.write(step_output)
        if output:
            with open(output, "w") as f:
                f.write(str(step_output))
            console_print(f"Response saved to [green]{output}[/green]")
    except Exception as e:
        raise click.ClickException(f"Failed to get LLM response: {str(e)}")
    return step_output

def run_template(template_name, **kwargs):
    from prich.core.loaders import get_loaded_config, get_loaded_template

    config, _ = get_loaded_config()
    skip_llm = kwargs.get('skip_llm')
    provider = kwargs.get('provider')
    output = kwargs.get('output')

    template = get_loaded_template(template_name)

    variables = {}
    for var in template.variables:
        cli_option = var.cli_option
        if cli_option:
            option_name = cli_option.lstrip("-").replace("-", "_")
            variables[var.name] = replace_env_vars(kwargs.get(option_name, var.default))
        else:
            variables[var.name] = replace_env_vars(var.default)
        if var.required and variables.get(var.name) is None:
            raise click.ClickException(f"Missing required variable {var.name}")

    if template.steps:
        step_idx = 0
        for step in template.steps:
            step_idx += 1
            # Set output variable to None
            if step.output_variable:
                variables[step.output_variable] = None
            step_brief = f"Step #{step_idx}: {step.name}"
            should_run = should_run_step(step.when, variables)
            console_print(f"{step_brief}{' - Skipped' if not should_run else ''} (\"when\" expression \"{step.when}\" is {should_run})")
            if not should_run:
                continue
            output_var = step.output_variable
            if type(step) in [PythonStep, CommandStep]:
                step_output = run_command_step(template, step, variables, config, template_name, template.source)
            elif type(step) == RenderStep:
                step_output = render_template(template.folder, step.template, variables)
            elif type(step) == LLMStep:
                step_output = send_to_llm(template, step, provider, config, variables, skip_llm, output)
            else:
                raise click.ClickException(f"Step {step.type} type is not supported.")

            if output_var:
                variables[output_var] = step_output
            if step.output_file:
                if step.output_file.startswith('.'):
                    save_to_file = step.output_file.replace('.', str(Path.cwd()), 1)
                elif step.output_file.startswith('~'):
                    save_to_file = step.output_file.replace('~', str(Path.home()), 1)
                else:
                    save_to_file = step.output_file
                write_mode = step.output_file_mode[:1] if step.output_file_mode else 'w'
                try:
                    with open(save_to_file, write_mode) as output_file:
                        console_print(f"{'Save' if write_mode == 'w' else 'Append'} output to file: {save_to_file}")
                        output_file.write(step_output)
                except Exception as e:
                    raise click.ClickException(f"Failed to save output to file {save_to_file}: {e}")
