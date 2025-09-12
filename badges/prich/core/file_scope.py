import os
from pathlib import Path

from prich.core.utils import get_cwd_dir, get_home_dir
from prich.constants import PRICH_DIR_NAME
from prich.models.file_scope import FileScope


def _normalize(p: Path, *, cwd: Path) -> Path:
    """
    Expand ~, make absolute relative to cwd, and resolve as much as possible.
    Works for non-existent paths too (resolves the existing parent).
    """
    p = Path(p).expanduser()
    if not p.is_absolute():
        p = cwd / p
    try:
        return p.resolve(strict=True)  # best: true canonical path (incl. symlinks)
    except FileNotFoundError:
        try:
            return p.parent.resolve(strict=True) / p.name  # resolve existing parent
        except FileNotFoundError:
            return p.absolute()  # fallback: absolute, not fully resolved

def _is_under(path: Path, root: Path) -> bool:
    """
    Return True if 'path' is within 'root', with Windows-friendly
    case-insensitive behavior and cross-drive safety.
    """
    a = os.path.normcase(str(path))
    b = os.path.normcase(str(root))
    try:
        return os.path.commonpath([a, b]) == b
    except ValueError:
        # Happens on Windows when paths are on different drives/UNC roots
        return False

# TODO: See if such support is really needed, could become hard to relate what is where
# def find_nearest_local_root(start: Path, home: Path) -> Path | None:
#     cur = start.resolve()
#     global = home / PRICH_DIR_NAME
#     for p in [cur, *cur.parents]:
#         candidate = p / PRICH_DIR_NAME
#         if candidate.exists() and candidate != global:
#             return candidate
#     return None

def classify_path(
    file: Path,
    *,
    cwd: Path | None = None,
    home: Path | None = None,
    follow_symlinks: bool = True,
) -> FileScope:
    """
    Decide whether 'file' is a local or global path.

    - Local live in <cwd>/.prich
    - Global live in <home>/.prich
    - Returns EXTERNAL if neither matches.
    """
    cwd = cwd or get_cwd_dir()
    home = home or get_home_dir()

    local_root = cwd / PRICH_DIR_NAME
    global_root = home / PRICH_DIR_NAME

    if follow_symlinks:
        p = _normalize(file, cwd=cwd)
        lr = _normalize(local_root, cwd=cwd)
        gr = _normalize(global_root, cwd=cwd)
    else:
        # Don't resolve symlinks; still expand and absolutize
        p = (cwd / Path(file).expanduser()) if not Path(file).expanduser().is_absolute() else Path(file).expanduser()
        p = p.absolute()
        lr = local_root.expanduser().absolute()
        gr = global_root.expanduser().absolute()

    if _is_under(p, lr):
        return FileScope.LOCAL
    if _is_under(p, gr):
        return FileScope.GLOBAL
    return FileScope.EXTERNAL
