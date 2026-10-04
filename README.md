# <img src="./imgs/icon.png" style="float" width="60" align="center"> &nbsp; QSWATMOD2

#### :exclamation: ***Note:*** `QSWATMOD2 is compatible with QGIS3.`

[QSWATMOD](https://swat.tamu.edu/software/swat-modflow/) is a QGIS-based graphical user interface that facilitates linking SWAT and MODFLOW, running SWAT-MODFLOW simulations, and viewing results.  

This repository contains source codes and an executable for the new version of QSWATMOD.
All other materials: example dataset and tutorial document can be downloaded from the old version of QSWATMOD repository.
- **[Installer](https://github.com/spark-brc/QSWATMOD2/raw/main/Installer/QSWATMOD2.exe):** QSWATMOD.exe
- **[Inputs](https://github.com/spark-brc/QSWATMOD2/tree/master/Inputs):** ExampleDataset.zip
- **[Source Code](https://github.com/spark-brc/qswatmod)**
- **[QSWATMOD Tutorial Document](https://github.com/spark-brc/QSWATMOD2/blob/main/docs/QSWATMOD_tutorial.pdf)**
- [SWAT-MODFLOW Tutorial Document](https://github.com/spark-brc/QSWATMOD2/blob/main/docs/SWAT-MODFLOW.Tutorial_v3.pdf)

-----
# Installation
The QGIS3 software must be installed on the system prior to the installation of QSWATMOD2. **On Linux, see [Installation on Linux](#installation-on-linux) below.** We've tested QSWATMOD2 with the “long term release (LTR)” (3.28.12) and "latest release (RC)" (3.34.0) versions of QGIS3 (long term release version recommended). On Linux it is tested with QGIS 3.44 LTR (3.44.14). Download the [QGIS](https://www.qgis.org/en/site/forusers/download.html)

- Install one of the versions of QGIS. It can be downloaded from https://qgis.org/en/site/forusers/download.html.
- Download [the QSWATMOD installer](https://github.com/spark-brc/QSWATMOD2/raw/main/Installer/QSWATMOD2.exe) and install it by running QSWATMOD 2.x.exe. The QSWATMOD2 is installed into the user's home directory *(~\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\QSWATMOD2)*, which we will refer to as the QSWATMOD2 plugin directory.

<p align="center">
    <img src="./imgs/fig_01.png" width="200" align="center">
</p>
<p align="center">
    <img src="./imgs/fig_02.png" width="500">
</p>

QSWATMOD2 includes all dependencies ([FloPy](https://www.usgs.gov/software/flopy-python-package-creating-running-and-post-processing-modflow-based-models) ([Bakker et al., 2016](https://onlinelibrary.wiley.com/doi/abs/10.1002/hyp.10933)) and [PyShp](https://pypi.org/project/pyshp/)) directly in the plugin to avoid user-installation.  
- Open QGIS3 after the installation of QSWATMOD2 is finished.

If you don't see QSWAMOD2 icon on the toolbar,
- Go to Plugins menu and open Manage and Install Plugins
<p align="center">
    <img src="./imgs/fig_03.png" width="700">
</p>

- Click the installed tab and check QSWATMOD2 box to activate the plugin.
<p align="center">
    <img src="./imgs/fig_04.png" width="450">

Now, you will see the QSWATMOD2 icon on the toolbar.
<p align="center">
    <img src="./imgs/fig_05.png" width="300">
</p>

<br>

# Installation on Linux

QSWATMOD2 needs **QGIS 3** (Qt5). QGIS 4 (Qt6) is not supported yet, and most rolling distributions (Arch, for example) now ship QGIS 4 or a Qt6 build of QGIS 3.x. The easiest way to get QGIS 3.44 LTR on any distribution is conda-forge:

```bash
conda create -n qgis-ltr -c conda-forge --override-channels qgis=3.44 python=3.12 pandas matplotlib scipy pillow
conda activate qgis-ltr
qgis
```

Other QGIS 3 installs (the [Ubuntu/Debian QGIS repositories](https://qgis.org/resources/installation-guide/#debian--ubuntu), the Flatpak) should work too if they provide Python with pandas, matplotlib, scipy and Pillow, but they are **not tested** yet. Only the conda install above was tested.

The Linux version of SWAT-MODFLOW3 (`swatmf3`, from [spark-hydro/SWAT-MODFLOW3](https://github.com/spark-hydro/SWAT-MODFLOW3)) is inside the plugin; the **Run** button uses it. There is nothing else to install, and the linking step no longer needs a Windows program.

Pick one way to install the plugin:

**1. Script** (installs into the default QGIS profile)

```bash
curl -fsSL https://raw.githubusercontent.com/spark-hydro/QSWATMOD2-plugin/main/install.sh | bash
```

Options: `--version v2.11.0`, `--flatpak` (installs into the Flatpak profile folder; untested), `--profile NAME`, `--plugins-dir DIR`, `--uninstall`. Run `./install.sh --help` after downloading it. Restart QGIS, then tick QSWATMOD2 in *Plugins > Manage and Install Plugins > Installed*.

**2. ZIP file.** Download `QSWATMOD2.<version>-linux.zip` (about 11 MB) from the [Releases page](https://github.com/spark-hydro/QSWATMOD2-plugin/releases), then in QGIS: *Plugins > Manage and Install Plugins > Install from ZIP*. (`QSWATMOD2.<version>.zip` also contains the Windows programs and is three times larger; it installs on every system.)

**3. Plugin repository** (QGIS then offers updates): *Plugins > Manage and Install Plugins > Settings > Add...*, and enter

```
https://github.com/spark-hydro/QSWATMOD2-plugin/releases/latest/download/plugins-linux.xml
```

The plugin is marked experimental, so tick *Show also experimental plugins* on the same Settings tab before searching for QSWATMOD2.

Building the ZIP yourself and running the tests: [BUILD.md](BUILD.md).

# New features added to QSWATMOD2

There are two additional features in QSWATMOD2.
- ### Add or subtract rows and columns  
    The "Create grid" algorithm in QGIS uses a given spatial extent and not the number of rows and columns. Thus, the algorithm occasionally creates more number of column or row, or less number of them. Once a MODFLOW grid is created, first check the number of columns and rows by labeling 'col' or 'row' on the 'mf_grid' layer. <br>
    For example, I want to create a MODFLOW grid with 700 m by 700 m grid cells for a given subbasin extent (**same as MODFLOW option 2** in linking process), resulting in one column too few in the MODFLOW grid. I can then use the “Add or Subtract Row and Column” option to add one column.
    <p align="center">
        <img src="./imgs/fig_06.png" width="1200">
    </p>

- ### Threshold setting on DHRU size

    During the linking process, disaggregating HRUs often generates a large number of very small DHRUs. These DHRUs then are intersected with the MODFLOW grid cells, to provide a connection between HRU variables and MODFLOW grid cells during the SWAT-MODFLOW simulation ([Bailey et al., 2016](https://onlinelibrary.wiley.com/doi/abs/10.1002/hyp.10933)). For a large SWAT-MODFLOW models, these small DHRUs are insignificant in terms of passing data (e.g. recharge) from SWAT HRUs to MODFLOW grid cells,  but can slow down the linkage process and SWAT-MODFLOW simulation speed.
    <br>
    
    Therefore, QSWATMOD now has the option to limit the size of DHRUs. The threshold setting on DRHU size option has been tested with an example data set. We tested several threshold settings on DHRU size using full DHRUs (no threshold), and DHRUs that must be > 9000, > 30000, > 60000, and > 125000 m<sup>2</sup>. The following figures show differences in spatial coverage that results in using different threshold settings. A proper threshold setting on DHRU size may speed up the linking process and the SWAT-MODFLOW simulation without losing information (e.g. recharge rate).
    <br>
    <p align="center">
        <img src="./imgs/fig_07.png" width="1200">
    </p>

<br>
<br>

In addition, [documentation and the SWAT-MODFLOW executable](https://swat.tamu.edu/software/swat-modflow/) are available as downloads. QSWATMOD and SWAT-MODFLOW have been tested in several watersheds. However, no warranty is given that either the model or tool is error-free. If you encounter problems with the model, tool or have suggestions for improvement, please comment at [the SWAT-MODFLOW Google group](https://groups.google.com/forum/?hl=en#!forum/swat-modflow) or [QSWATMOD github](https://github.com/spark-brc/QSWATMOD2/issues).

A publication documenting QSWATMOD and an example application can be found here:  
[https://doi.org/10.1016/j.envsoft.2018.10.017](https://doi.org/10.1016/j.envsoft.2018.10.017)

# References
[Bailey, R.T., Wible, T.C., Arabi, M., Records, R.M. and Ditty, J., 2016. Assessing regional‐scale spatio‐temporal patterns of groundwater–surface water interactions using a coupled SWAT‐MODFLOW model. Hydrological processes, 30(23), pp.4420-4433, https://doi.org/10.1002/hyp.10933.](https://onlinelibrary.wiley.com/doi/abs/10.1002/hyp.10933)

[Bakker, M., Post, V., Langevin, C. D., Hughes, J. D., White, J. T., Starn, J. J. and Fienen, M. N., 2016, Scripting MODFLOW Model Development Using Python and FloPy: Groundwater, v. 54, p. 733–739, doi:10.1111/gwat.12413.](https://ngwa.onlinelibrary.wiley.com/doi/full/10.1111/gwat.12413)