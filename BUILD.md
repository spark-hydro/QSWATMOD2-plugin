# Building and testing the plugin

The plugin is Python only, so there is nothing to compile. A release is a ZIP with the
plugin folder (`src/qswatmod`, installed as `QSWATMOD2/`) and the SWAT-MODFLOW3 programs.

## Build the ZIP

```bash
scripts/fetch_swatmf3.sh               # Linux swatmf3 from the SWAT-MODFLOW3 release in swatmf3-version.txt
python3 scripts/package.py --xml       # dist/QSWATMOD2.<version>.zip + plugins.xml  (about 32 MB, with the Windows programs)
python3 scripts/package.py --linux --xml   # dist/QSWATMOD2.<version>-linux.zip + plugins-linux.xml (about 11 MB)
python3 scripts/package.py --check dist/QSWATMOD2.2.10.1.zip   # layout check only
```

- The version comes from `src/qswatmod/metadata.txt`. The ZIP has one top-level folder,
  `QSWATMOD2/`, with `metadata.txt` directly inside.
- **File name:** `QSWATMOD2.<version>[-linux].zip`. QGIS takes the plugin id from the file
  name up to the first dot, so `QSWATMOD2-2.10.1.zip` would be read as the plugin
  `QSWATMOD2-2` and updates would not be recognised.
- The ZIP is reproducible (fixed time stamps): the same files give the same checksum.
- QGIS "Install from ZIP" does not keep file permissions; the plugin sets the execute bit
  of `swatmf3` itself when it starts the model.
- `plugins.xml` points to `https://github.com/spark-hydro/QSWATMOD2-plugin/releases/download/v<version>/<zip>`;
  `--base-url` and `--tag` change that (for a mirror or a test).

## Install a local build

```bash
./install.sh --zip dist/QSWATMOD2.2.10.1-linux.zip                 # default QGIS profile
./install.sh --zip dist/QSWATMOD2.2.10.1-linux.zip --plugins-dir /tmp/plugins
./install.sh --uninstall
```

`install.sh` refuses to replace a symbolic link (a development install, e.g.
`ln -s $PWD/src/qswatmod ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/QSWATMOD2`)
unless you pass `--force`.

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
