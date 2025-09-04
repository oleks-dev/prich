from typing import Dict

from prich.models.template import RenderStep
from prich.core.utils import is_verbose, console_print
from prich.core.template_utils import render_template_text


def render_template(step: RenderStep, variables: dict = Dict[str, str]) -> str:
    if is_verbose():
        console_print("[dim]Render template:[/dim]")
        console_print(step.template, markup=False)
        console_print()
        console_print("[dim]Result:[/dim]")
    rendered_text = render_template_text(step.template, variables, "params")
    return rendered_text
