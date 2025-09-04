from pathlib import Path
from typing import Dict

import click

from prich.models.template import LLMStep
from prich.models.config import ConfigModel
from prich.core.state import _jinja_env


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
    if not _jinja_env.get(env_name):
        if conditional_expression_only:
            env = Environment(undefined=StrictUndefined)
            env.filters.clear()
        else:
            env = Environment(
                loader=FileSystemLoader(Path.cwd()),
                undefined=StrictUndefined
            )
            env.filters['include_file'] = include_file
            env.filters['include_file_with_line_numbers'] = include_file_with_line_numbers
        env.filters.update({
            "lower": str.lower,
            "upper": str.upper,
            "strip": str.strip,
            "length": len,
            "int": int,
            "float": float,
            "replace": lambda _old, _new, _count=None: str.replace(_old, _new, _count),
            "split": lambda _sep, _max_split: str.split(_sep, _max_split),
            "bool": lambda x: bool(x),
        })
        _jinja_env[env_name] = env
    return _jinja_env[env_name]


def render_template_text(template_text: str, variables: dict, jinja_env_name: str = "default"):
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
        rendered_text = get_jinja_env(jinja_env_name).from_string(template_text).render(**variables).strip()
    except Exception as e:
        raise click.ClickException(f"Render jinja error: {str(e)}")
    return rendered_text


def should_run_step(when_expr: str, variables: Dict[str, any]) -> bool:
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


def render_prompt(config: ConfigModel, llm_step: LLMStep, variables: Dict[str, str], mode: str):
    """ Render Prompt using provider mode prompt template (used for raw prompt construction) """
    if not llm_step.input:
        raise click.ClickException("There should be at least an 'input' field.")
    mode_prompt = [x for x in config.model_dump().get("provider_modes") if x.get("name")==mode]
    if len(mode_prompt) == 0:
        raise click.ClickException(f"Prompt mode {mode} is not found in the config.")
    prompt_fields = render_template_text(mode_prompt[0].get("prompt"), {"instructions": llm_step.instructions, "input": llm_step.input})
    llm_step.rendered_prompt = render_template_text(prompt_fields, variables)

def render_prompt_fields(llm_step: LLMStep, variables: Dict[str, str]):
    """ Render Prompt fields (used when provider supports prompt fields templates like system/user """
    if not llm_step.input:
        raise click.ClickException("There should be at least an 'input' field.")
    if llm_step.instructions:
        llm_step.rendered_instructions = render_template_text(llm_step.instructions, variables)
    llm_step.rendered_input = render_template_text(llm_step.input, variables)
