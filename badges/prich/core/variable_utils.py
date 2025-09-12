import re
from typing import List, Dict

from prich.core.template_utils import render_template_text


def replace_env_vars(text: str, env_vars: dict[str, str]) -> str:
    """
    Replace $VAR or ${VAR} in a text string with environment variable values.

    Args:
        text (str): Input string containing $VAR or ${VAR} placeholders.
        env_vars (dict): Environments variables to use

    Returns:
        str: String with environment variables expanded, or original text if no variables found.
    """
    def replace_match(match):
        """Replace $VAR or ${VAR} with the value from os.environ or empty string if not found."""
        var_name = match.group(1) if match.group(1) else match.group(2)
        return env_vars.get(var_name, "")

    if text is None or not isinstance(text, str):
        return text

    # Pattern for environment variables: $VAR or ${VAR}
    env_pattern = r'\$(?:\{([^}]+)\}|([a-zA-Z_][a-zA-Z0-9_]*))'
    return re.sub(env_pattern, replace_match, text)


def expand_vars(args: List[str], variables: Dict[str, any] = None, env_vars: Dict[str, str] = None) -> list:
    """
    Expand internal variables ({{VAR}}, {{ VAR }}) and environment variables ($VAR or ${VAR}) in a list of arguments.

    Args:
        args (list): List of argument strings, e.g., ["tool", "--path={{HOME_DIR}}", "--file=$FILE"].
        variables (dict, optional): Dictionary of internal variable names to values, e.g., {"HOME_DIR": "/home/user"}.
        env_vars (dict, optional): Dictionary of environment variables

    Returns:
        list: New list with variables expanded.
    """
    # Default to empty dict if no internal variables provided
    variables = variables or {}
    env_vars = env_vars or {}

    expanded_args = []
    for arg in args:
        if isinstance(arg, str):
            # First expand internal variables
            arg = render_template_text(arg, variables=variables)
            # Then expand environment variables ($VAR or ${VAR})
            arg = replace_env_vars(arg, env_vars=env_vars)
        expanded_args.append(arg)

    return expanded_args
