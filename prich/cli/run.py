import click

from prich.cli.dynamic_command_group import DynamicCommandGroup


@click.group("run", cls=DynamicCommandGroup)
@click.option("-g", "--global", "global_only", is_flag=True, default=False, help="Only global config")
def run_group(global_only):
    """Run a template with dynamic arguments defined in templates.yaml."""
    # Register dynamic commands at module import
    # from prich.core.utils import should_use_global_only
    # initialize_template_commands(ctx, global_only or should_use_global_only())
    pass

# def initialize_template_commands(ctx: click.Context, global_only: bool):
#     from prich.core.state import _loaded_templates
#     from prich.core.engine import create_dynamic_command
#     from prich.core.loaders import load_global_config, load_merged_config, load_template_models
#
#     try:
#         config, _ = load_global_config() if global_only else load_merged_config()
#         templates = load_template_models(global_only=global_only)
#         for template in templates:
#             ctx.command.add_command(create_dynamic_command(config, template))
#             _loaded_templates[template.name] = template
#     except Exception as e:
#         raise click.ClickException(f"Failed to load dynamic parameters: {e}")

# # Register dynamic commands at module import
# from prich.core.utils import should_use_global_only
# initialize_template_commands(should_use_global_only())
