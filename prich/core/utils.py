import os
import sys
import re
import click
from pathlib import Path
from rich.console import Console

console = Console()

def should_use_global_only() -> bool:
    """ Should only global config/templates used? """
    try:
        global_only_options = ["global_only", "global_init", "global_install"]
        for global_ in global_only_options:
            if click.get_current_context().params.get(global_):
                return True
    except:
        pass
    return any(flag in sys.argv for flag in ("-g", "--global"))

def should_use_local_only() -> bool:
    """ Should only local config/templates used? """
    try:
        local_only_options = ["local_only"]
        for global_ in local_only_options:
            if click.get_current_context().params.get(global_):
                return True
    except:
        pass
    return any(flag in sys.argv for flag in ("-l", "--local"))

def is_verbose() -> bool:
    """ Is Verbose mode enabled? """
    return any(flag in sys.argv for flag in ("-v", "--verbose"))

def is_quiet() -> bool:
    """ Is Quiet mode enabled? """
    return any(flag in sys.argv for flag in ("-q", "--quiet"))

def is_only_final_output() -> bool:
    """ Show only output of the last step? """
    if is_piped():
        return True
    return any(flag in sys.argv for flag in ("-f", "--only-final-output"))

def is_piped() -> bool:
    """ Check if prich executed with a piped command (should work only when not executed from pytest) """
    return not console.is_terminal and not os.getenv("PYTEST_CURRENT_TEST")

def console_print(message: str = "", end: str = "\n", markup = None, flush: bool = None):
    """ Print to console wrapper """
    if not is_quiet() and not is_only_final_output():
        console.print(message, end=end, markup=markup, crop=False)

def is_valid_template_id(template_id) -> bool:
    """ Validate Name Pattern: lowercase letters, numbers, hyphen, optional underscores, and no other characters"""
    pattern = r'^[a-z0-9-]+(_[a-z0-9-]+)*$'
    return bool(re.match(pattern, template_id))

def is_valid_variable_name(variable_name) -> bool:
    """ Validate Name Pattern: upper and lowercase letters, numbers, optional underscores, and no other characters"""
    pattern = r'^[A-Za-z0-9]+([_A-Za-z0-9]+)*$'
    return bool(re.match(pattern, variable_name))

def is_cli_option_name(option_name) -> bool:
    """ Validate CLI Option Name Pattern: lowercase letters, numbers, optional underscores, and no other characters"""
    pattern = r'^--[a-z0-9]+([-_a-z0-9]+)*$'
    return bool(re.match(pattern, option_name))

def get_prich_dir(global_only: bool = None) -> Path:
    """ Return current prich dir path based on global_only param or should_use_global_only() """
    parent_path = Path.home() if global_only or should_use_global_only() else Path.cwd()
    return parent_path / ".prich"

def get_prich_templates_dir(global_only: bool = None) -> Path:
    """ Return current prich templates folder path based on global_only param or should_use_global_only() """
    return get_prich_dir(global_only) / "templates"

def replace_env_vars(text: str, secure: bool = True) -> str:
    """
    Replace $VAR or ${VAR} in a text string with environment variable values.

    Args:
        text (str): Input string containing $VAR or ${VAR} placeholders.
        secure (bool): Check if env variable is listed in the allowed env variables

    Returns:
        str: String with environment variables expanded, or original text if no variables found.
    """
    from prich.core.loaders import get_loaded_config

    def replace_match(match):
        """Replace $VAR or ${VAR} with the value from os.environ or empty string if not found."""
        var_name = match.group(1) if match.group(1) else match.group(2)
        config, _ = get_loaded_config()
        if secure and config.security and config.security.allowed_environment_variables:
            if var_name in config.security.allowed_environment_variables:
                return os.getenv(var_name, "")
        elif not secure:
            return os.getenv(var_name, "")
        raise click.ClickException(f"Environment variable {var_name} is not listed in allowed environment variables. Add it to config.security.allowed_environment_variables for usage.")

    if text is None or type(text) != str:
        return text

    # Pattern for environment variables: $VAR or ${VAR}
    env_pattern = r'\$(?:\{([^}]+)\}|([a-zA-Z_][a-zA-Z0-9_]*))'
    return re.sub(env_pattern, replace_match, text)

def shorten_path(path: str | Path) -> str:
    """ Return short path using ~/... or ./... instead of a full absolute path """
    home = str(Path.home())
    cwd = str(Path.cwd())
    if type(path) == Path:
        path = str(path)
    if path.startswith(home):
        return path.replace(home, "~", 1)
    elif path.startswith(cwd):
        return path.replace(cwd, ".", 1)
    return path

def is_just_filename(filename: Path | str):
    """ Check if filename is just a basename, not a path """
    s = str(filename)
    if s in ("", ".", "..") or ("/" in s) or ("\\" in s):
        return False
    return True
