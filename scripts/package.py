#!/usr/bin/env python3
"""Build the QGIS plugin ZIP (and plugins.xml) from src/qswatmod.

    python3 scripts/package.py                 # dist/QSWATMOD2.<version>.zip
    python3 scripts/package.py --xml           # also dist/plugins.xml
    python3 scripts/package.py --linux --xml   # smaller ZIP for Linux: no Windows programs
    python3 scripts/package.py --check dist/QSWATMOD2.2.11.0.zip

The ZIP has one top-level folder, QSWATMOD2/ (QGIS needs the folder name to match the
plugin), with metadata.txt directly inside it. The Linux program (swatmf3) comes from
scripts/fetch_swatmf3.sh; the Windows programs are the ones kept in FOLDER_FOR_COPY.

The same ZIP works on Windows, Linux and macOS: QGIS "Install from ZIP" ignores file
permissions, so the plugin sets the execute bit itself when it runs the model.
"""
import argparse
import configparser
import fnmatch
import os
import sys
import zipfile
from datetime import datetime, timezone
from xml.sax.saxutils import escape

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "src", "qswatmod")
PLUGIN = "QSWATMOD2"
REPO = "https://github.com/spark-hydro/QSWATMOD2-plugin"
RAW = "https://raw.githubusercontent.com/spark-hydro/QSWATMOD2-plugin/main"

# not part of the installed plugin (paths relative to src/qswatmod, glob style)
EXCLUDE = [
    "__pycache__", "*.pyc", ".git", ".gitignore", ".DS_Store",
    "test", "scripts", "help", "Makefile", "compile.bat", "pb_tool.cfg", "pylintrc",
    "*.code-workspace", "plugin_upload.py", "dump.py", "README.md", "resources.qrc",
    "i18n/*.ts",
]
LINUX_EXE = "FOLDER_FOR_COPY/SWAT-MODFLOW/swatmf3"
WINDOWS_EXE = "FOLDER_FOR_COPY/*/*.exe"   # the Windows programs (about 50 MB)
# fixed time stamp: the same input gives the same ZIP (and the same checksum)
STAMP = (2000, 1, 1, 0, 0, 0)


def read_metadata():
    cp = configparser.ConfigParser(interpolation=None)
    with open(os.path.join(SRC, "metadata.txt"), encoding="utf-8") as f:
        cp.read_file(f)
    return dict(cp["general"])


def excluded(rel):
    parts = rel.split("/")
    return any(fnmatch.fnmatch(rel, pat) or any(fnmatch.fnmatch(p, pat) for p in parts)
               for pat in EXCLUDE)


def files(linux_only=False):
    out = []
    for dirpath, dirnames, filenames in os.walk(SRC):
        rel_dir = os.path.relpath(dirpath, SRC).replace(os.sep, "/")
        dirnames[:] = sorted(d for d in dirnames
                             if not excluded(d if rel_dir == "." else rel_dir + "/" + d))
        for name in sorted(filenames):
            rel = name if rel_dir == "." else rel_dir + "/" + name
            if not excluded(rel) and not (linux_only and fnmatch.fnmatch(rel, WINDOWS_EXE)):
                out.append(rel)
    return sorted(out)


def zip_name(meta, linux_only):
    # QGIS takes the plugin id from the file name up to the first dot, so the
    # name must be QSWATMOD2.<version>.zip (a dash after QSWATMOD2 gives a wrong id)
    return "{}.{}{}.zip".format(PLUGIN, meta["version"], "-linux" if linux_only else "")


def build(dist, need_linux=True, linux_only=False):
    meta = read_metadata()
    if need_linux and not os.path.isfile(os.path.join(SRC, LINUX_EXE)):
        sys.exit("Linux program missing: run scripts/fetch_swatmf3.sh first "
                 "(or --no-linux to build without it)")
    os.makedirs(dist, exist_ok=True)
    path = os.path.join(dist, zip_name(meta, linux_only))
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for rel in files(linux_only):
            info = zipfile.ZipInfo("{}/{}".format(PLUGIN, rel), STAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            mode = 0o755 if os.access(os.path.join(SRC, rel), os.X_OK) else 0o644
            info.external_attr = (0o100000 | mode) << 16
            with open(os.path.join(SRC, rel), "rb") as f:
                z.writestr(info, f.read())
    return path, meta


def check(path):
    """Layout checks; returns a list of problems (empty = fine)."""
    problems = []
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        tops = {n.split("/")[0] for n in names}
        if tops != {PLUGIN}:
            problems.append("top-level entries must be only '{}/', found {}".format(PLUGIN, sorted(tops)))
        for need in ("metadata.txt", "__init__.py", "QSWATMOD2.py", "icon.png",
                     "FOLDER_FOR_COPY/DB/DB_SM.db"):
            if "{}/{}".format(PLUGIN, need) not in names:
                problems.append("missing " + need)
        for n in names:
            if "__pycache__" in n or n.endswith(".pyc") or "/.git" in n:
                problems.append("should not be included: " + n)
        if z.testzip():
            problems.append("corrupt member: " + z.testzip())
        try:
            meta = configparser.ConfigParser(interpolation=None)
            meta.read_string(z.read("{}/metadata.txt".format(PLUGIN)).decode("utf-8"))
            for key in ("name", "version", "qgisMinimumVersion", "description", "author"):
                if not meta["general"].get(key):
                    problems.append("metadata.txt has no " + key)
        except KeyError:
            pass
    return problems


def plugins_xml(meta, zip_name, tag, base_url=None):
    """Repository file for QGIS: Plugins > Manage and Install > Settings > Add."""
    url = "{}/{}".format(base_url.rstrip("/") if base_url else
                         "{}/releases/download/{}".format(REPO, tag), zip_name)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def tag_(name, value):
        return "    <{0}>{1}</{0}>\n".format(name, escape(str(value)))

    body = "".join([
        tag_("description", meta.get("description", "")),
        tag_("about", meta.get("about", "")),
        tag_("changelog", meta.get("changelog", "").strip()),
        tag_("version", meta["version"]),
        tag_("qgis_minimum_version", meta["qgisminimumversion"]),
        tag_("qgis_maximum_version", meta.get("qgismaximumversion", "3.99.0")),
        tag_("homepage", meta.get("homepage") or REPO),
        tag_("file_name", zip_name),
        tag_("icon", RAW + "/src/qswatmod/" + meta.get("icon", "icon.png")),
        tag_("author_name", meta.get("author", "")),
        tag_("download_url", url),
        tag_("uploaded_by", "spark-hydro"),
        tag_("create_date", now),
        tag_("update_date", now),
        tag_("experimental", meta.get("experimental", "False")),
        tag_("deprecated", meta.get("deprecated", "False")),
        tag_("tracker", meta.get("tracker") or REPO + "/issues"),
        tag_("repository", meta.get("repository") or REPO),
        tag_("tags", meta.get("tags", "")),
        tag_("downloads", 0),
        tag_("average_vote", 0),
        tag_("rating_votes", 0),
        tag_("server", "False"),
    ])
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<plugins>\n'
            '  <pyqgis_plugin name="{}" version="{}">\n{}  </pyqgis_plugin>\n</plugins>\n'
            ).format(PLUGIN, escape(meta["version"]), body)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dist", default=os.path.join(ROOT, "dist"))
    ap.add_argument("--xml", action="store_true", help="also write plugins.xml")
    ap.add_argument("--tag", help="release tag used in the download URL (default v<version>)")
    ap.add_argument("--linux", action="store_true",
                    help="Linux ZIP: leave out the Windows programs (writes plugins-linux.xml)")
    ap.add_argument("--base-url", help="folder URL of the ZIP in plugins.xml (default: the GitHub "
                    "release of the tag; for tests or a mirror)")
    ap.add_argument("--no-linux", action="store_true", help="do not require the Linux program")
    ap.add_argument("--check", metavar="ZIP", help="only check an existing ZIP")
    args = ap.parse_args(argv)

    if args.check:
        problems = check(args.check)
        print("\n".join(problems) if problems else "{}: OK".format(args.check))
        return 1 if problems else 0

    path, meta = build(args.dist, need_linux=not args.no_linux, linux_only=args.linux)
    problems = check(path)
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1
    print("{} ({:.1f} MB)".format(path, os.path.getsize(path) / 1e6))
    if args.xml:
        xml = plugins_xml(meta, os.path.basename(path), args.tag or "v" + meta["version"],
                          args.base_url)
        out = os.path.join(args.dist, "plugins-linux.xml" if args.linux else "plugins.xml")
        with open(out, "w", encoding="utf-8") as f:
            f.write(xml)
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
