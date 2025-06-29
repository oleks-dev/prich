import click
from prich.core.loaders import load_global_config, load_merged_config, load_template_models
from prich.core.engine import create_dynamic_command
from prich.core.state import _loaded_templates
from prich.core.utils import should_use_global_only


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
        try:
            config, _ = load_global_config() if global_only else load_merged_config()
            templates = load_template_models(global_only=global_only)
            for template in templates:
                self.add_command(create_dynamic_command(config, template))
                _loaded_templates[template.name] = template
        except Exception as e:
            raise click.ClickException(f"Failed to load dynamic parameters: {e}")

        self._commands_loaded = True