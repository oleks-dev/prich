import io
import sys


def capture_stdout(func, *args, **kwargs):
    # Save the original stdout
    old_stdout = sys.stdout
    buffer = io.StringIO()
    sys.stdout = buffer

    try:
        result = func(*args, **kwargs)  # Call method
        output = buffer.getvalue()
    finally:
        # Always restore stdout
        sys.stdout = old_stdout

    return result, output