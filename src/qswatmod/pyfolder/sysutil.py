"""Small helpers that behave the same on Windows, Linux and macOS."""
import os
import re
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


def _natural_key(name):
    # v1.2.10 sorts after v1.2.9
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", name)]


def find_swatmf_exe(folder, platform=None):
    """Return the SWAT-MODFLOW executable in `folder`, or None.

    Windows: swatmf_rel230818.exe, else SWAT-MODFLOW3.exe (same order as before).
    Linux/macOS: `swatmf3`, else the newest `swatmf3-*` build, e.g. the file name
    inside the SWAT-MODFLOW3 release zip (swatmf3-v1.2.5-gnu-lin_x86_64-Rel).
    """
    platform = platform or sys.platform
    if platform.startswith("win"):
        names = ["swatmf_rel230818.exe", "SWAT-MODFLOW3.exe"]
    else:
        names = ["swatmf3"]
        skip = (".zip", ".exe", ".txt", ".log")
        names += sorted(
            (n for n in os.listdir(folder)
             if n.startswith("swatmf3-") and not n.endswith(skip)),
            key=_natural_key, reverse=True)
    for name in names:
        path = os.path.join(folder, name)
        if os.path.isfile(path):
            return os.path.normpath(path)
    return None


def ensure_executable(path):
    """Set the execute bit (a zip or a copy can lose it). Does nothing on Windows."""
    if not sys.platform.startswith("win"):
        mode = os.stat(path).st_mode
        os.chmod(path, mode | 0o111)
