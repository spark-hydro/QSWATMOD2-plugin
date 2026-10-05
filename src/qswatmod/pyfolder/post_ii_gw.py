# -*- coding: utf-8 -*-
from builtins import str
from qgis.core import QgsProject 
from qgis.PyQt import QtCore, QtGui, QtSql             
import datetime
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.dates as mdates
# import numpy as np
import pandas as pd
import os
from matplotlib import style
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMessageBox
from .utils import PlotUtils, ExportUtils
import glob
from datetime import datetime


# MODFLOW water table plot =======================================================================
def read_grid_id(self):
    for self.layer in list(QgsProject.instance().mapLayers().values()):
        if self.layer.name() == ("mf_obs (SWAT-MODFLOW)"):
            self.dlg.groupBox_plot_wt.setEnabled(True)
            self.layer = QgsProject.instance().mapLayersByName("mf_obs (SWAT-MODFLOW)")[0]
            feats = self.layer.getFeatures()
            # get grid_id as a list
            unsorted_grid_id = [int(f.attribute("grid_id")) for f in feats]
            # Sort this list
            sorted_grid_id = sorted(unsorted_grid_id, key=int)
            # a = sorted(a, key=lambda x: float(x))
            self.dlg.comboBox_grid_id.clear()
            # self.dlg.comboBox_sub_number.addItem('')
            sorted_grid_id = [str(i) for i in sorted_grid_id]
            self.dlg.comboBox_grid_id.addItems(sorted_grid_id) # in addItem list should contain string numbers
        else:
            self.dlg.groupBox_plot_wt.setEnabled(False)


def check_gw_obd(self):
    if self.dlg.checkBox_wt_obd.isChecked():
        self.dlg.frame_wt_obd.setEnabled(True)
        self.dlg.radioButton_wt_obd_line.setEnabled(True)
        self.dlg.radioButton_wt_obd_pt.setEnabled(True)
        self.dlg.spinBox_wt_obd_size.setEnabled(True)
        get_gwls_obds(self)
        if self.dlg.comboBox_dtw_obd.count()==0:
            msgBox = QMessageBox()
            msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
            msgBox.setWindowTitle("No 'modflow.obd' file found!")
            msgBox.setText("Please, groundwater measurement files!")
            msgBox.exec_()
            self.dlg.checkBox_wt_obd.setChecked(0)  
            self.dlg.frame_wt_obd.setEnabled(False)
            self.dlg.radioButton_wt_obd_line.setEnabled(False)
            self.dlg.radioButton_wt_obd_pt.setEnabled(False)
            self.dlg.spinBox_wt_obd_size.setEnabled(False)
    else:
        self.dlg.comboBox_dtw_obd.clear()
        self.dlg.comboBox_wt_obs_data.clear()
        self.dlg.frame_wt_obd.setEnabled(False)
        self.dlg.radioButton_wt_obd_line.setEnabled(False)
        self.dlg.radioButton_wt_obd_pt.setEnabled(False)
        self.dlg.spinBox_wt_obd_size.setEnabled(False)


def get_gwls_obds(self):
    if self.dlg.checkBox_wt_obd.isChecked():
        QSWATMOD_path_dict = self.dirs_and_paths()
        dtw_obd_files = [
            os.path.basename(file) for file in glob.glob(str(QSWATMOD_path_dict['SMfolder']) + '/dtw*.obd.csv')
            ]
        gwl_obd_files = [
            os.path.basename(file) for file in glob.glob(str(QSWATMOD_path_dict['SMfolder']) + '/gwl*.obd.csv')
            ]
        tot_gd_files= dtw_obd_files + gwl_obd_files
        self.dlg.comboBox_dtw_obd.clear()
        self.dlg.comboBox_dtw_obd.addItems(tot_gd_files)


def get_gwl_cols(self):
    if self.dlg.checkBox_wt_obd.isChecked():
        QSWATMOD_path_dict = self.dirs_and_paths()
        wd = QSWATMOD_path_dict['SMfolder']
        gd_obd_nam = self.dlg.comboBox_dtw_obd.currentText()
        gd_obd = pd.read_csv(
                        os.path.join(wd, gd_obd_nam),
                        index_col=0,
                        parse_dates=True,
                        na_values=[-999, ""])
        gd_obd_list = gd_obd.columns.tolist()
        self.dlg.comboBox_wt_obs_data.clear()
        self.dlg.comboBox_wt_obs_data.addItems(gd_obd_list)


def plot_gw(self, ts):
    dark_theme = self.dlg.checkBox_darktheme.isChecked()
    plt.style.use('dark_background') if dark_theme else plt.style.use('default')

    QSWATMOD_path_dict = self.dirs_and_paths()
    stdate, eddate, stdate_warmup, eddate_warmup = self.define_sim_period()
    wd = QSWATMOD_path_dict['SMfolder']
    startDate = stdate_warmup.strftime("%m/%d/%Y")
    endDate = eddate_warmup.strftime("%m/%d/%Y")

    obd_file = self.dlg.comboBox_dtw_obd.currentText()
    grid_id = self.dlg.comboBox_grid_id.currentText()
    fig, ax = plt.subplots(figsize=(9, 4))
    if self.dlg.checkBox_depthTowater.isChecked():
        ax.set_ylabel(r'Depth to water $[m]$', fontsize=8)
    else:
        ax.set_ylabel(r'Groundwater level $[m]$', fontsize=8)
    ax.tick_params(axis='both', labelsize=8)
    if self.dlg.checkBox_wt_obd.isChecked():
        plot_gw_sim_obd(self, ax, wd, obd_file, startDate, grid_id, ts)
    else:
        plot_simulated(self, ax, wd, grid_id, startDate, ts)
    plt.legend(fontsize=8, loc="lower right", ncol=2, bbox_to_anchor=(1, 1))
    plt.show()


def plot_gw_sim_obd(self, ax, wd, obd_file, startDate, grid_id, ts):
    gw_obd = read_gw_obd(self, wd, obd_file)
    mf_obs, output_wt = read_swatmf_out_MF_obs(self, wd)
    obd_col = self.dlg.comboBox_wt_obs_data.currentText()
    try:
        df = update_index(self, output_wt, startDate)
        df = time_cvt(self, df, ts)
        if self.dlg.checkBox_depthTowater.isChecked():
            df = df[str(grid_id)] - float(mf_obs.loc[int(grid_id)])
        else:
            df = df[str(grid_id)]
        ax.plot(df.index.values, df.values, c='limegreen', lw=1, label="Simulated")
        df2 = pd.concat([df, gw_obd[obd_col]], axis=1)
        df3 = df2.dropna()
        plot_observed_data(self, ax, df3, grid_id, obd_col)
    except Exception as e:
        pu = PlotUtils()
        pu.handle_exception(ax, str(e))


def plot_simulated(self, ax, wd, grid_id, startDate, ts):
    mf_obs, output_wt = read_swatmf_out_MF_obs(self, wd)
    df = update_index(self, output_wt, startDate)
    df = time_cvt(self, df, ts)
    try:
        if self.dlg.checkBox_depthTowater.isChecked():
            # Calculate depth to water (Simulated watertable - landsurface)
            df = df[str(grid_id)] - float(mf_obs.loc[int(grid_id)])
            ax.set_ylabel(r'Depth to Water $[m]$', fontsize = 8)
            ax.set_title(
                        u'Daily Depth to watertable' + u" @ Grid id: " + grid_id, fontsize = 10,
                        loc='left')
        else:
            df = df[str(grid_id)]
            ax.set_ylabel(r'Hydraulic Head $[m]$', fontsize = 8)
            ax.set_title(
                        u'Daily Watertable Elevation' + u" @ Grid id: " + grid_id, fontsize = 10,
                        loc='left')
        ax.plot(df.index.values, df.values, c = 'dodgerblue', lw = 1, label = "Simulated")
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b-%d\n%Y'))
    except Exception as e:
        pu = PlotUtils()
        pu.handle_exception(ax, str(e))

def plot_observed_data(self, ax, df3, grid_id, obd_col):
    pu = PlotUtils()
    if self.dlg.radioButton_wt_obd_pt.isChecked():
        size = float(self.dlg.spinBox_wt_obd_size.value())
        ax.scatter(
            df3.index.values, df3[obd_col].values, c='m', lw=1, alpha=0.5, s=size, marker='x',
            label="Observed", zorder=3
        )
    else:
        ax.plot(
            df3.index.values, df3[obd_col].values, c='m', lw=1.5, alpha=0.5,
            label="Observed", zorder=3
        )
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b-%d\n%Y'))
    if len(df3[obd_col]) > 1:
        pu.calculate_metrics(ax, df3, grid_id, obd_col)
    else:
        pu.display_no_data_message(ax)


def update_index(self, df, startDate):
    df.index = pd.date_range(startDate, periods=len(df))
    return df

def time_cvt(self, df, ts):
    try:
        if ts == "Daily":
            self.df = df
        elif ts == "Monthly":
            self.df = df
            self.df = self.df.resample('M').mean()
        elif ts == "Annual":
            self.df = self.df.resample('A').mean()
        return self.df
    except Exception as e:
        show_error_message(self, "Error converting time step", str(e))


def read_swatmf_out_MF_obs(self, wd):
    mf_obs = pd.read_csv(
                        os.path.join(wd, "modflow.obs"),
                        sep="\\s+",
                        skiprows = 2,
                        usecols = [3, 4],
                        index_col = 0,
                        names = ["grid_id", "mf_elev"],)
    # Convert dataframe into a list with string items inside list
    grid_id_lst = mf_obs.index.astype(str).values.tolist()  
    output_wt = pd.read_csv(
                        os.path.join(wd, "swatmf_out_MF_obs"),
                        sep="\\s+",
                        skiprows = 1,
                        names = grid_id_lst,)
    return mf_obs, output_wt

def read_gw_obd(self, wd, obd_file):
    return pd.read_csv(
        os.path.join(wd, obd_file),
        index_col=0,
        header=0,
        parse_dates=True,
        na_values=[-999, ""]
    )


def show_error_message(self, title, message):
    msgBox = QMessageBox()
    msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
    msgBox.setWindowTitle(title)
    msgBox.setText(message)
    msgBox.exec_()



# -----------------------------
# NOTE: export data
# -----------------------------
def export_gw(self, ts):
    QSWATMOD_path_dict = self.dirs_and_paths()
    stdate, eddate, stdate_warmup, eddate_warmup = self.define_sim_period()
    wd = QSWATMOD_path_dict['SMfolder']
    outfolder = QSWATMOD_path_dict['exported_files']
    startDate = stdate_warmup.strftime("%m/%d/%Y")
    endDate = eddate_warmup.strftime("%m/%d/%Y")
    
    obd_file = self.dlg.comboBox_dtw_obd.currentText()
    grid_id = self.dlg.comboBox_grid_id.currentText()
    obd_col = self.dlg.comboBox_wt_obs_data.currentText()
    
    version = "version 2.10.1."
    ctime = datetime.now().strftime('- %m/%d/%y %H:%M:%S -')

    if self.dlg.checkBox_wt_obd.isChecked():
        eu = ExportUtils()
        # gw_sim = read_swatmf_out_MF_obs(self, wd).loc[grid_id]
        df3 = process_data(self, wd, grid_id, ts, obd_file, obd_col, startDate)
        if len(df3[obd_col]) > 1:
            rsq, rmse, pbias = eu.calculate_statistics(df3, grid_id, obd_col)
            export_data(
                self, outfolder, grid_id, obd_col, ts, version, ctime, df3,
                rsq, rmse, pbias
                )
    else:
        # mf_obs, output_wt = read_swatmf_out_MF_obs(self, wd)
        # gw_sim = output_wt[str(grid_id)]
        df3 = process_data(self, wd, grid_id, ts, None, "", startDate)
        export_data(self, outfolder, grid_id, "", ts, version, ctime, df3)

def process_data(self, wd, grid_id, ts, obd_file, obd_col, startDate):
    mf_obs, output_wt = read_swatmf_out_MF_obs(self, wd)
    df = update_index(self, output_wt, startDate)
    df = time_cvt(self, df, ts)
    # df[str(grid_id)].to_csv(os.path.join(wd, 'test.csv'))
    if self.dlg.checkBox_depthTowater.isChecked():
        df = df[str(grid_id)] - float(mf_obs.loc[int(grid_id)])
    else:
        df = df[str(grid_id)]
    if self.dlg.checkBox_wt_obd.isChecked():
        obd = read_gw_obd(self, wd, obd_file)
        df2 = pd.concat([df, obd[obd_col]], axis=1)
        df3 = df2.dropna()
    else:
        df3 = df
    return df3


def export_data(
        self, outfolder, grid_id, obd_col, ts, version, ctime, df3, 
        rsq=None, rmse=None, pbias=None
        ):
    eu = ExportUtils()
    try:
        file_name = f"swatmf_gw({grid_id})_obd({obd_col})_{ts.lower()}.txt"
        with open(os.path.join(outfolder, file_name), 'w') as f:
            f.write(f"# {file_name} is created by QSWATMOD2 plugin {version}{ctime}\n")
            df3.to_csv(
                f, index_label="Date", sep='\t', float_format='%10.4f', 
                lineterminator='\n', 
                encoding='utf-8'
            )
            f.write('\n')
            f.write("# Statistics\n")
            if rsq is not None:
                f.write("R-squared: " + str('{:.4f}'.format(rsq) + "\n"))
                f.write("RMSE: " + str('{:.4f}'.format(rmse) + "\n"))
                f.write("PBIAS: " + str('{:.4f}'.format(pbias) + "\n"))
            else:
                f.write("R-squared: ---\n")
                f.write("RMSE: ---\n")
                f.write("PBIAS: ---\n")

        msgBox = QMessageBox()
        msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
        msgBox.setWindowTitle("Exported!")
        msgBox.setText(f"'{file_name}' file is exported to your 'exported_files' folder!")
        msgBox.exec_() 
                    
    except Exception as e:
        eu.show_error_message("Error exporting data", str(e))
