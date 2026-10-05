"""Small helpers that behave the same on Windows, Linux and macOS."""
import os
import subprocess
import sys


def open_file(path):
    """Open a file with the default application of the operating system.

    Replaces os.startfile, which exists on Windows only.
    """
    path = os.path.normpath(path)
    if sys.platform.startswith("win"):
        os.startfile(path)  # noqa: pylint
    elif sys.platform == "darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])
