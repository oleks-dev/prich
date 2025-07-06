import os
import sys
import re
import click
from pathlib import Path
from prich.core.loaders import get_loaded_config
from rich.console import Console

console = Console()

def should_use_global_only() -> bool:
    """ Should only global config/templates used? """
    return any(flag in sys.argv for flag in ("-g", "--global"))

def should_use_local_only() -> bool:
    """ Should only local config/templates used? """
    return any(flag in sys.argv for flag in ("-l", "--local"))

def is_quiet() -> bool:
    """ Is Quiet mode enabled? """
    return any(flag in sys.argv for flag in ("-q", "--quiet"))

def console_print(message: str = "", end = "\n", markup = None):
    """ Print to console wrapper """
    if not is_quiet():
        console.print(message, end=end, markup=markup)

def is_valid_template_name(name):
    """ Validate Name Pattern: lowercase letters, numbers, hyphen, optional underscores, and no other characters"""
    pattern = r'^[a-z0-9-]+(_[a-z0-9-]+)*$'
    return bool(re.match(pattern, name))

def get_prich_dir() -> Path:
    parent_path = Path.home() if should_use_global_only() else Path.cwd()
    return parent_path / ".prich"

def get_prich_templates_dir() -> Path:
    return get_prich_dir() / "templates"

def replace_env_vars(text):
    """
    Replace $VAR or ${VAR} in a text string with environment variable values.

    Args:
        text (str): Input string containing $VAR or ${VAR} placeholders.

    Returns:
        str: String with environment variables expanded, or original text if no variables found.
    """

    def replace_match(match):
        """Replace $VAR or ${VAR} with the value from os.environ or empty string if not found."""
        var_name = match.group(1) if match.group(1) else match.group(2)
        config, _ = get_loaded_config()
        if config.security and config.security.allowed_environment_variables:
            if var_name in config.security.allowed_environment_variables:
                return os.getenv(var_name, "")
        raise click.ClickException(f"Environment variable {var_name} is not listed in allowed environment variables. Add it to config.security.allowed_environment_variables for usage.")

    if text is None:
        return text

    # Pattern for environment variables: $VAR or ${VAR}
    env_pattern = r'\$(?:\{([^}]+)\}|([a-zA-Z_][a-zA-Z0-9_]*))'
    return re.sub(env_pattern, replace_match, text)

def shorten_home_path(path: str) -> str:
    home = str(Path.home())
    path = str(path)
    if path.startswith(home):
        return path.replace(home, "~", 1)
    return path
