# Building and testing the plugin

The plugin is Python only, so there is nothing to compile. A release is a ZIP with the
plugin folder (`src/qswatmod`, installed as `QSWATMOD2/`) and the SWAT-MODFLOW3 programs
(`swatmf3` for Linux and `swatmf3.exe` for Windows, both downloaded from the SWAT-MODFLOW3
release and not stored in git; only the old Intel debug build `SM_exes/swamf_deb230818.exe` is).

## Build the ZIP

```bash
SWATMF3_PLATFORM=all scripts/fetch_swatmf3.sh   # swatmf3 (Linux) and swatmf3.exe (Windows) from the
                                       # SWAT-MODFLOW3 release in swatmf3-version.txt (default: Linux only)
python3 scripts/package.py --xml       # dist/QSWATMOD2.<version>.zip + plugins.xml  (about 14 MB, both programs)
python3 scripts/package.py --linux --xml   # dist/QSWATMOD2.<version>-linux.zip + plugins-linux.xml (about 8 MB, Linux program only)
python3 scripts/package.py --check dist/QSWATMOD2.2.11.0.zip   # layout check only
```

- The version comes from `src/qswatmod/metadata.txt`. The ZIP has one top-level folder,
  `QSWATMOD2/`, with `metadata.txt` directly inside.
- **File name:** `QSWATMOD2.<version>[-linux].zip`. QGIS takes the plugin id from the file
  name up to the first dot, so `QSWATMOD2-2.11.0.zip` would be read as the plugin
  `QSWATMOD2-2` and updates would not be recognised.
- The ZIP is reproducible (fixed time stamps): the same files give the same checksum.
- QGIS "Install from ZIP" does not keep file permissions; the plugin sets the execute bit
  of `swatmf3` itself when it starts the model.
- `plugins.xml` points to `https://github.com/spark-hydro/QSWATMOD2-plugin/releases/download/v<version>/<zip>`;
  `--base-url` and `--tag` change that (for a mirror or a test).

## Install a local build

Windows: `.\install.ps1 -Zip dist\QSWATMOD2.2.11.0.zip` (`-PluginsDir DIR` for another folder, `-Uninstall`).
Linux:

```bash
./install.sh --zip dist/QSWATMOD2.2.11.0-linux.zip                 # default QGIS profile
./install.sh --zip dist/QSWATMOD2.2.11.0-linux.zip --plugins-dir /tmp/plugins
./install.sh --uninstall
```

`install.sh` refuses to replace a symbolic link (a development install, e.g.
`ln -s $PWD/src/qswatmod ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/QSWATMOD2`)
unless you pass `--force`.

## Releases and CI

- `.github/workflows/build.yml` (push to `main`, pull requests): unit tests on Linux and Windows;
  the ZIPs and `install.sh`; on Windows `install.ps1` (Windows PowerShell 5.1 and PowerShell 7) and the
  installed `swatmf3.exe` run on the SWAT-MODFLOW3 example model with its `regress.py`;
  and QGIS 3.44 (`qgis/qgis` image): installs the Linux ZIP with `install.sh`, loads the plugin,
  imports every module, runs the linking step and the Run button code on the SWAT-MODFLOW3 example
  model (`scripts/ci_qgis_check.py`).
- `.github/workflows/release.yml`: push a tag equal to `v` + `version=` in `metadata.txt`
  (`git tag v2.11.0 && git push origin v2.11.0`) to build both ZIPs, `plugins.xml`,
  `plugins-linux.xml` and `SHA256SUMS` and attach them, with `install.sh` and `install.ps1`, to a
  GitHub Release. Manual runs and pull requests build and upload workflow artifacts only.
- Both programs come from the SWAT-MODFLOW3 release named in `swatmf3-version.txt`
  (`scripts/fetch_swatmf3.sh`); change the file to ship another version.

## Tests

No QGIS needed (Python 3 with numpy for the second one):

```bash
python3 src/qswatmod/test/test_sysutil.py
python3 src/qswatmod/test/test_create_swatmf.py
python3 src/qswatmod/test/test_package.py
```

Loading the plugin needs QGIS 3 (see the README for a conda environment):

```bash
conda activate qgis-ltr
ln -s $PWD/src/qswatmod ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/QSWATMOD2
qgis
```
