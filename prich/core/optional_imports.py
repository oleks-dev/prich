def ensure_optional_dep(module_name: str, extra_name: str = None):
    """
    Raises a clear error if an optional dependency is missing.

    Args:
        module_name: Name to import, e.g. 'mlx_lm'
        extra_name: The extras key, e.g. 'mlx' (for prich[mlx])
    """
    try:
        __import__(module_name)
    except ImportError as e:
        raise RuntimeError(
            f"❌ Missing optional dependency '{module_name}'.\n"
            f"Install it with: pip install prich[{extra_name or module_name}]"
        ) from e
