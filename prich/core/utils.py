import os
import sys
import re
import click
from pathlib import Path
from rich.console import Console
from prich.constants import PRICH_DIR_NAME

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
    return False

def should_use_local_only() -> bool:
    """ Should only local config/templates used? """
    try:
        if click.get_current_context().params.get("local_only"):
            return True
    except:
        pass
    return False

def is_verbose() -> bool:
    """ Is Verbose mode enabled? """
    try:
        if click.get_current_context().params.get("verbose"):
            return True
    except:
        pass
    return False

def is_quiet() -> bool:
    """ Is Quiet mode enabled? """
    try:
        if click.get_current_context().params.get("quiet"):
            return True
    except:
        pass
    return False

def is_only_final_output() -> bool:
    """ Show only output of the last step? """
    if is_piped():
        return True
    try:
        if click.get_current_context().params.get("only_final_output"):
            return True
    except:
        pass
    return False

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

def get_cwd_dir() -> Path:
    """Return current directory, prefer $PWD if set (symlink-preserving)."""
    pwd = os.environ.get("PWD")
    if pwd:
        try:
            return Path(pwd)
        except Exception:
            pass
    return Path.cwd()

def get_home_dir() -> Path:
    """Return home directory, prefer $HOME if set (common CLI convention)."""
    home = os.environ.get("HOME")
    if home:
        try:
            return Path(home)
        except Exception:
            pass
    return Path.home()

def get_prich_dir(global_only: bool = None) -> Path:
    """ Return current prich dir path based on global_only param or should_use_global_only() """
    parent_path = get_home_dir() if global_only or should_use_global_only() else get_cwd_dir()
    return parent_path / PRICH_DIR_NAME

def get_prich_templates_dir(global_only: bool = None) -> Path:
    """ Return current prich templates folder path based on global_only param or should_use_global_only() """
    return get_prich_dir(global_only) / "templates"

def shorten_path(path: str | Path) -> str:
    """ Return short path using ~/... or ./... instead of a full absolute path """
    home = str(Path.home())
    cwd = str(get_cwd_dir())
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
