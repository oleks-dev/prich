import click
from prich.constants import RESERVED_RUN_TEMPLATE_CLI_OPTIONS
from prich.models.template import TemplateModel
from prich.core.loaders import load_global_config, load_local_config, load_merged_config, load_templates
from prich.core.engine import run_template
from prich.core.state import _loaded_templates
from prich.core.utils import should_use_global_only, should_use_local_only, is_verbose, console_print


class DynamicCommandGroup(click.Group):
    def list_commands(self, ctx):
        # Always load templates before showing help
        self._load_dynamic_commands(ctx)
        return super().list_commands(ctx)

    def get_command(self, ctx, name):
        # Ensure commands are loaded before command lookup
        self._load_dynamic_commands(ctx)
        return super().get_command(ctx, name)

    def _load_dynamic_commands(self, ctx):
        if getattr(self, "_commands_loaded", False):
            return

        global_only = ctx.params.get("global_only", False) or should_use_global_only()
        local_only = ctx.params.get("local_only", False) or should_use_local_only()
        try:
            config, _ = load_global_config() if global_only else load_local_config() if local_only else load_merged_config()
            templates = load_templates()
            for template in templates:
                self.add_command(create_dynamic_command(config, template))
                _loaded_templates[template.id] = template
        except Exception as e:
            raise click.ClickException(f"Failed to load dynamic parameters: {e}")

        self._commands_loaded = True


def get_variable_type(variable_type: str) -> click.types:
    type_mapping = {"str": click.STRING, "int": click.INT, "bool": click.BOOL, "path": click.Path}
    return type_mapping.get(variable_type.lower(), None)


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
            options.append(click.Option([cli_option], is_flag=True, default=arg.default or False, show_default=True,
                                        help=help_text))
        elif arg_type:
            options.append(
                click.Option([cli_option], type=arg_type, default=arg.default, required=arg.required, show_default=True,
                             help=help_text))
        elif arg.type.startswith("list["):
            list_type = get_variable_type(arg.type.split('[')[1][:-1])
            if not list_type:
                raise click.ClickException(f"Failed to parse list type for {arg.name}")
            options.append(
                click.Option([cli_option], type=list_type, multiple=True, default=arg.default, required=arg.required,
                             show_default=True, help=help_text))
        else:
            raise click.ClickException(f"Unsupported variable type: {arg.type}")

    options.extend([
        click.Option(["-g", "--global", "global_only"], is_flag=True, default=False,
                     help="Use global config and template"),
        click.Option(["-l", "--local", "local_only"], is_flag=True, default=False,
                     help="Use local config and template"),
        click.Option(["-o", "--output"], type=click.Path(), default=None, show_default=True,
                     help="Save final output to file"),
        click.Option(["-p", "--provider"], type=click.Choice(config.providers.keys()), show_default=True,
                     help="Override LLM provider"),
        click.Option(["-v", "--verbose"], is_flag=True, default=False, help="Verbose mode"),
        click.Option(["-q", "--quiet"], is_flag=True, default=False, help="Suppress all output"),
        click.Option(["-f", "--only-final-output"], is_flag=True, default=False,
                     help="Suppress output and show only the last step output")
    ])

    @click.pass_context
    def dynamic_command(ctx, **kwargs):
        if is_verbose():
            console_print(
                f"[dim]Template: [green]{template.name}[/green] ({template.version}), {template.source.value}, args: {', '.join([f'{k}={v}' for k, v in kwargs.items() if v])}[/dim]")
            console_print(f"[dim]{template.description}[/dim]")
        run_template(template.id, **kwargs)

    return click.Command(name=template.id, callback=dynamic_command, params=options,
                         help=f"{template.description if template.description else ''}",
                         epilog=f"{template.name} (ver: {template.version}, {template.source.value})")
