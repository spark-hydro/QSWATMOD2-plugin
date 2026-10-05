#!/usr/bin/env python3
"""Check an installed QSWATMOD2 plugin inside QGIS, without a display.

    QT_QPA_PLATFORM=offscreen python3 scripts/ci_qgis_check.py \\
        --plugins-dir DIR [--tables DIR] [--model DIR]

--plugins-dir  folder that holds QSWATMOD2/ (for example after install.sh --plugins-dir DIR)
--tables       folder with hru_dhru, dhru_grid, grid_dhru, river_grid: runs the linking step
--model        a SWAT-MODFLOW3 model folder (for example data/MiddleBosque1000): runs the
               plugin's Run button code (run_SM) with the SWAT-MODFLOW3 program in the plugin

Exits with 1 if a step fails. Used by .github/workflows/build.yml in the qgis/qgis image.
"""
import argparse
import importlib
import os
import shutil
import sys
import tempfile
import time
import traceback

# modules of the bundled FloPy that import names the bundled FloPy does not have;
# the plugin does not use them
KNOWN_BROKEN = {
    "QSWATMOD2.modules.flopy.utils.compare",
    "QSWATMOD2.modules.flopy.utils.gridgen",
    "QSWATMOD2.modules.flopy.utils.mfgrdfile",
    "QSWATMOD2.modules.flopy.utils.triangle",
}
SKIP_DIRS = {"__pycache__", "test", "FOLDER_FOR_COPY", "help", "templates", "pics", "i18n", ".git"}
SKIP_FILES = {"dump.py", "plugin_upload.py", "temp_.py"}

failures = []


def step(name):
    def wrap(fn):
        def run(*args, **kwargs):
            try:
                result = fn(*args, **kwargs)
                print("ok    ", name, flush=True)
                return result
            except Exception:  # noqa: BLE001 - report every kind of failure
                failures.append(name)
                print("FAIL  ", name, flush=True)
                traceback.print_exc()
                return None
        return run
    return wrap


@step("load the plugin and run initGui()")
def load(plugins_dir):
    from qgis.testing.mocked import get_iface
    sys.path.insert(0, plugins_dir)
    import QSWATMOD2
    plugin = QSWATMOD2.classFactory(get_iface())
    plugin.initGui()
    return plugin


@step("import every module of the plugin")
def import_all(plugins_dir):
    base = os.path.join(plugins_dir, "QSWATMOD2")
    bad, count = [], 0
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in sorted(filenames):
            if not name.endswith(".py") or name in SKIP_FILES:
                continue
            rel = os.path.relpath(os.path.join(dirpath, name), plugins_dir)[:-3].replace(os.sep, ".")
            rel = rel[:-len(".__init__")] if rel.endswith(".__init__") else rel
            count += 1
            try:
                importlib.import_module(rel)
            except BaseException as err:  # noqa: BLE001
                if rel not in KNOWN_BROKEN:
                    bad.append("{}: {}: {}".format(rel, type(err).__name__, err))
    print("      {} modules, {} unexpected failures".format(count, len(bad)))
    assert not bad, "\n".join(bad)


def new_project(plugin):
    from qgis.core import QgsProject
    tmp = tempfile.mkdtemp()
    QgsProject.instance().setFileName(os.path.join(tmp, "proj.qgz"))
    paths = plugin.dirs_and_paths()
    for key in ("Table", "SMfolder"):
        os.makedirs(paths[key], exist_ok=True)
    return paths


@step("linking step (run_CreateSWATMF) and copy to the SWAT-MODFLOW folder")
def link(plugin, tables):
    from QSWATMOD2.pyfolder import linking_process
    paths = new_project(plugin)
    for name in ("hru_dhru", "dhru_grid", "grid_dhru", "river_grid"):
        shutil.copy(os.path.join(tables, name), paths["Table"])
    assert linking_process.run_CreateSWATMF(plugin) is True
    linking_process.copylinkagefiles(plugin)
    for name in ("river2grid", "dhru2hru", "dhru2grid", "grid2dhru"):
        out = os.path.join(paths["SMfolder"], "swatmf_{}.txt".format(name))
        assert os.path.getsize(out) > 0, out
    assert "river_grid" in plugin.dlg.textEdit_sm_link_log.toPlainText()


@step("Run button code (run_SM) runs the model with the program from the plugin")
def run_model(plugin, model, plugins_dir):
    paths = new_project(plugin)
    shutil.copytree(model, paths["SMfolder"], dirs_exist_ok=True)
    # a model from git has Tmp1.Tmp, the model asks for tmp1.tmp (Linux is case sensitive)
    upper = os.path.join(paths["SMfolder"], "Tmp1.Tmp")
    if os.path.exists(upper):
        os.rename(upper, os.path.join(paths["SMfolder"], "tmp1.tmp"))
    # the program as installed from the ZIP: no execute bit
    exe = os.path.join(plugins_dir, "QSWATMOD2", "FOLDER_FOR_COPY", "SWAT-MODFLOW", "swatmf3")
    assert os.path.isfile(exe), "the plugin has no Linux program: " + exe
    target = os.path.join(paths["SMfolder"], "swatmf3")
    shutil.copy(exe, target)
    os.chmod(target, 0o644)
    plugin.run_SM()
    log = os.path.join(paths["SMfolder"], "swatmf3_run.log")
    deadline = time.time() + 600
    text = ""
    while time.time() < deadline:
        time.sleep(1)
        if os.path.exists(log):
            with open(log) as f:
                text = f.read()
            if "Execution successfully completed" in text:
                break
    assert "Execution successfully completed" in text, "model did not finish:\n" + text[-1500:]
    assert os.path.exists(os.path.join(paths["SMfolder"], "output.std")), "no output.std"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--plugins-dir", required=True)
    ap.add_argument("--tables")
    ap.add_argument("--model")
    args = ap.parse_args()
    plugins_dir = os.path.abspath(args.plugins_dir)

    from qgis.testing import start_app
    start_app()
    from qgis.core import Qgis, QgsApplication
    # the QGIS GUI puts its own plugins (processing) on the path; a script has to do it
    sys.path.append(os.path.join(QgsApplication.pkgDataPath(), "python", "plugins"))
    import processing  # noqa: F401 - the plugin imports it
    print("QGIS", Qgis.QGIS_VERSION, "| Python", sys.version.split()[0], flush=True)

    plugin = load(plugins_dir)
    import_all(plugins_dir)
    if plugin is not None and args.tables:
        link(plugin, os.path.abspath(args.tables))
    if plugin is not None and args.model:
        run_model(plugin, os.path.abspath(args.model), plugins_dir)
    print("\n{} failed step(s){}".format(len(failures), ": " + ", ".join(failures) if failures else ""))
    sys.stdout.flush()
    os._exit(1 if failures else 0)  # QGIS can hang on exit in a container


if __name__ == "__main__":
    main()
