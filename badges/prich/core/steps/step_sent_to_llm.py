import click

from prich.core.template_utils import render_prompt, render_prompt_fields
from prich.core.utils import is_verbose, console_print, is_quiet, is_only_final_output
from prich.models.config import ConfigModel
from prich.models.template import TemplateModel, LLMStep


def send_to_llm(template: TemplateModel, step: LLMStep, provider: str, config: ConfigModel, variables: dict) -> str:
    from prich.llm_providers.get_llm_provider import get_llm_provider

    if not step.input:
        raise click.ClickException("llm step must define at least 'input' field.")
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
    selected_provider = config.providers.get(selected_provider_name)
    if not selected_provider:
        raise click.ClickException(f"Provider {selected_provider_name} configuration not found. Check your config.yaml file.")
    if is_verbose():
        console_print(f"Selected LLM provider: {selected_provider_name}")

    if selected_provider.mode:
        render_prompt(config, step, variables, selected_provider.mode)
    else:
        render_prompt_fields(step, variables)
    if not step.rendered_prompt and not step.rendered_input:
        raise click.ClickException(f"Prompt is empty in step {step.name}.")

    llm_provider = get_llm_provider(selected_provider_name, selected_provider)
    if ((not step.output_console and not is_verbose()) or is_quiet()) and llm_provider.show_response:
        # Override show response when quiet mode
        llm_provider.show_response = False

    # prompt lines
    prompt_lines = []
    if step.rendered_prompt:
        prompt_lines.append(step.rendered_prompt)
    else:
        if step.rendered_instructions:
            prompt_lines.append(step.rendered_instructions)
        if step.rendered_input:
            prompt_lines.append(step.rendered_input)
        if step.rendered_prompt:
            prompt_lines.append(step.rendered_prompt)
    prompt_full = '\n'.join(prompt_lines)

    if is_verbose():
        console_print(f"[dim]Sending prompt to LLM ([green]{llm_provider.name}[/green]), {len(prompt_full)} chars[/dim]")
        console_print(prompt_full, markup=False)
        console_print()
        console_print("[dim]LLM Response:[/dim]")
    try:
        if not is_quiet() and not is_only_final_output() and not llm_provider.show_response:
            from rich.console import Console
            console = Console()
            with console.status("Thinking..."):
                response = llm_provider.send_prompt(
                    prompt=step.rendered_prompt,
                    instructions=step.rendered_instructions,
                    input_=step.rendered_input
                )
        else:
            response = llm_provider.send_prompt(
                prompt=step.rendered_prompt,
                instructions=step.rendered_instructions,
                input_=step.rendered_input
            )
        step_output = selected_provider.postprocess_filter(response)
        if (is_verbose() or step.output_console) and not llm_provider.show_response and not is_quiet():
            console_print(step_output, markup=False)
    except Exception as e:
        raise click.ClickException(f"Failed to get LLM response: {str(e)}")
    return step_output
