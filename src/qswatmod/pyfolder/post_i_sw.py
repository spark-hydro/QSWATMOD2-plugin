# -*- coding: utf-8 -*-
from builtins import str
from qgis.PyQt import QtCore, QtGui, QtSql
from qgis.core import QgsProject
import datetime
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.dates as mdates
# import numpy as np
import glob
import shutil
import posixpath
import ntpath
import os
import pandas as pd
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMessageBox, QFileDialog
from qgis.PyQt.QtCore import QSettings, QFileInfo, QVariant
from datetime import datetime

# -----------------------------------
# NOTE: init settings
# -----------------------------------

def read_sub_no(self):
    for self.layer in list(QgsProject.instance().mapLayers().values()):
        if self.layer.name() == ("sub (SWAT)"):
            self.layer = QgsProject.instance().mapLayersByName("sub (SWAT)")[0]
            feats = self.layer.getFeatures()
            # get sub number as a list
            unsorted_subno = [str(f.attribute("Subbasin")) for f in feats]
            # Sort this list
            sorted_subno = sorted(unsorted_subno, key=int)
            ## a = sorted(a, key=lambda x: float(x)
            self.dlg.comboBox_sub_number.clear()
            # self.dlg.comboBox_sub_number.addItem('')
            self.dlg.comboBox_sub_number.addItems(sorted_subno) # in addItem list should contain string numbers

def check_stf_obd(self):
    if self.dlg.checkBox_stream_obd.isChecked():
        self.dlg.frame_sd_obd.setEnabled(True)
        self.dlg.radioButton_str_obd_line.setEnabled(True)
        self.dlg.radioButton_str_obd_pt.setEnabled(True)
        self.dlg.spinBox_str_obd_size.setEnabled(True)
        get_stf_obds(self)
        if self.dlg.comboBox_stf_obd.count()==0:
            msgBox = QMessageBox()
            msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
            msgBox.setWindowTitle("No 'streamflow.obd.csv' file found!")
            msgBox.setText("Please, provide streamflow measurement files!")
            msgBox.exec_()
            self.dlg.checkBox_stream_obd.setChecked(0)  
            self.dlg.frame_sd_obd.setEnabled(False)
            self.dlg.radioButton_str_obd_line.setEnabled(False)
            self.dlg.radioButton_str_obd_pt.setEnabled(False)
            self.dlg.spinBox_str_obd_size.setEnabled(False)
    else:
        self.dlg.comboBox_stf_obd.clear()
        self.dlg.comboBox_SD_obs_data.clear()
        self.dlg.frame_sd_obd.setEnabled(False)
        self.dlg.radioButton_str_obd_line.setEnabled(False)
        self.dlg.radioButton_str_obd_pt.setEnabled(False)
        self.dlg.spinBox_str_obd_size.setEnabled(False)


def get_stf_obds(self):
    QSWATMOD_path_dict = self.dirs_and_paths()
    stf_obd_files = [
        os.path.basename(file) for file in glob.glob(str(QSWATMOD_path_dict['SMfolder']) + '/stf*.obd.csv')
        ]
    self.dlg.comboBox_stf_obd.clear()
    self.dlg.comboBox_stf_obd.addItems(stf_obd_files)

def get_stf_cols(self):
    if self.dlg.checkBox_stream_obd.isChecked():
        QSWATMOD_path_dict = self.dirs_and_paths()
        wd = QSWATMOD_path_dict['SMfolder']
        stf_obd_nam = self.dlg.comboBox_stf_obd.currentText()
        stf_obd = pd.read_csv(
                        os.path.join(wd, stf_obd_nam),
                        index_col=0,
                        parse_dates=True)
        stf_obd_list = stf_obd.columns.tolist()
        self.dlg.comboBox_SD_obs_data.clear()
        self.dlg.comboBox_SD_obs_data.addItems(stf_obd_list)

# --------------------------------------------
# NOTE: plot
# --------------------------------------------

def plot_stf(self, ts):
    dark_theme = self.dlg.checkBox_darktheme.isChecked()
    plt.style.use('dark_background') if dark_theme else plt.style.use('default')

    QSWATMOD_path_dict = self.dirs_and_paths()
    stdate, eddate, stdate_warmup, eddate_warmup = self.define_sim_period()
    wd = QSWATMOD_path_dict['SMfolder']
    startDate = stdate_warmup.strftime("%m/%d/%Y")
    endDate = eddate_warmup.strftime("%m/%d/%Y")
    colNum = 6  # get flow_out
    subnum = int(self.dlg.comboBox_sub_number.currentText())
    obd_file = self.dlg.comboBox_stf_obd.currentText()
    # ts = self.dlg.comboBox_SD_timeStep.currentText()
    # plot
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.set_ylabel(r'Stream Discharge $[m^3/s]$', fontsize=8)
    ax.tick_params(axis='both', labelsize=8)
    if self.dlg.checkBox_stream_obd.isChecked():
        plot_stf_obd(self, ax, wd, obd_file, startDate, subnum, ts)
    else:
        plot_simulated(self, ax, wd, subnum, startDate, ts)
    plt.legend(fontsize=8, loc="lower right", ncol=2, bbox_to_anchor=(1, 1))
    plt.show()


def read_output_rch_data(self, wd, colNum=6):
    return pd.read_csv(
        os.path.join(wd, "output.rch"),
        sep="\\s+",
        skiprows=9,
        usecols=[1, 3, colNum],
        names=["date", "filter", "stf_sim"],
        index_col=0
    )


def read_stf_obd(self, wd, obd_file):
    return pd.read_csv(
        os.path.join(wd, obd_file),
        index_col=0,
        header=0,
        parse_dates=True,
        na_values=[-999, ""]
    )


def plot_stf_obd(self, ax, wd, obd_file, startDate, subnum, ts):
    strObd = read_stf_obd(self, wd, obd_file)
    output_rch = read_output_rch_data(self, wd)
    obd_col = self.dlg.comboBox_SD_obs_data.currentText()
    # try:
    df = output_rch.loc[subnum]
    df = update_index(self, df, startDate)
    df = time_cvt(self, df, ts)
    ax.plot(df.index.values, df.stf_sim.values, c='limegreen', lw=1, label="Simulated")
    df2 = pd.concat([df, strObd[obd_col]], axis=1)
    df3 = df2.dropna()
    plot_observed_data(self, ax, df3, obd_col)
    # except Exception as e:
    #     handle_exception(self, ax, str(e))

def plot_simulated(self, ax, wd, subnum, startDate, ts):
    
    output_rch = read_output_rch_data(self, wd)
    df = output_rch.loc[subnum]
    try:
        df = update_index(self, df, startDate)
        df = time_cvt(self, df, ts)
        ax.plot(df.index.values, df.stf_sim.values, c='g', lw=1, label="Simulated")
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b-%d\n%Y'))
    except Exception as e:
        handle_exception(self, ax, str(e))

def update_index(self, df, startDate):
    if self.dlg.radioButton_day.isChecked():
        df.index = pd.date_range(startDate, periods=len(df.stf_sim))
    elif self.dlg.radioButton_month.isChecked():
        df = df[df['filter'] < 13]
        df.index = pd.date_range(startDate, periods=len(df.stf_sim), freq="ME")
    else:
        df.index = pd.date_range(startDate, periods=len(df.stf_sim), freq="A")
    return df

def time_cvt(self, df, ts):
    if self.dlg.radioButton_day.isChecked(): # daily format given
        if ts == "Daily":
            self.df = df
        elif ts == "Monthly":
            self.df = df
            self.df = self.df.resample('M').mean()
        elif ts == "Annual":
            self.df = self.df.resample('A').mean()
        else:
            self.show_error_message()
        return self.df
    elif self.dlg.radioButton_month.isChecked(): # monthly given  
        if ts == "Monthly":
            self.df = df
        elif ts == "Annual":
            self.df = self.df.resample('A').mean()
        else:
            self.show_error_message()
        return self.df
    elif self.dlg.radioButton_year.isChecked() and ts == "Annual": # Annual given
        self.df = df
        return self.df
    else:
        msgBox = QMessageBox()
        msgBox.setText("There was a problem plotting the result!")
        msgBox.exec_()          

def plot_observed_data(self, ax, df3, obd_col):
    if self.dlg.radioButton_str_obd_pt.isChecked():
        size = float(self.dlg.spinBox_str_obd_size.value())
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
        calculate_metrics(self, ax, df3, obd_col)
    else:
        display_no_data_message(self, ax)

# NOTE: metrics =======================================================================================
def calculate_metrics(self, ax, df3, obd_col):
    r_squared = ((sum((df3[obd_col] - df3[obd_col].mean()) * (df3.stf_sim - df3.stf_sim.mean())))**2) / (
            (sum((df3[obd_col] - df3[obd_col].mean())**2) * (sum((df3.stf_sim - df3.stf_sim.mean())**2)))
    )
    dNS = 1 - (sum((df3.stf_sim - df3[obd_col])**2) / sum((df3[obd_col] - (df3[obd_col]).mean())**2))
    PBIAS = 100 * (sum(df3[obd_col] - df3.stf_sim) / sum(df3[obd_col]))
    display_metrics(self, ax, dNS, r_squared, PBIAS)

def display_metrics(self, ax, dNS, r_squared, PBIAS):
    ax.text(
        .01, 0.95, f'Nash-Sutcliffe: {dNS:.4f}',
        fontsize=8, horizontalalignment='left', color='limegreen', transform=ax.transAxes
    )
    ax.text(
        .01, 0.90, f'$R^2$: {r_squared:.4f}',
        fontsize=8, horizontalalignment='left', color='limegreen', transform=ax.transAxes
    )
    ax.text(
        .99, 0.95, f'PBIAS: {PBIAS:.4f}',
        fontsize=8, horizontalalignment='right', color='limegreen', transform=ax.transAxes
    )

def display_no_data_message(self, ax):
    ax.text(
        .01, .95, 'Nash-Sutcliffe: ---',
        fontsize=8, horizontalalignment='left', transform=ax.transAxes
    )
    ax.text(
        .01, 0.90, '$R^2$: ---',
        fontsize=8, horizontalalignment='left', color='limegreen', transform=ax.transAxes
    )
    ax.text(
        .99, 0.95, 'PBIAS: ---',
        fontsize=8, horizontalalignment='right', color='limegreen', transform=ax.transAxes
    )

def handle_exception(self, ax, exception_message):
    ax.text(
        .5, .5, exception_message,
        fontsize=12, horizontalalignment='center', weight='extra bold', color='y', transform=ax.transAxes
    )

# -----------------------------
# NOTE: export data
# -----------------------------
def export_stf(self, ts):
    QSWATMOD_path_dict = self.dirs_and_paths()
    stdate, eddate, stdate_warmup, eddate_warmup = self.define_sim_period()
    wd = QSWATMOD_path_dict['SMfolder']
    outfolder = QSWATMOD_path_dict['exported_files']
    startDate = stdate_warmup.strftime("%m/%d/%Y")
    endDate = eddate_warmup.strftime("%m/%d/%Y")
    colNum = 6  # get flow_out
    subnum = int(self.dlg.comboBox_sub_number.currentText())
    obd_file = self.dlg.comboBox_stf_obd.currentText()
    obd_col = self.dlg.comboBox_SD_obs_data.currentText()

    version = "version 2.10.1."
    ctime = datetime.now().strftime('- %m/%d/%y %H:%M:%S -')

    if self.dlg.checkBox_stream_obd.isChecked():
        stf_sim = read_output_rch_data(self, wd).loc[subnum]
        df3 = process_data(self, wd, stf_sim, ts, obd_file, obd_col, startDate)
        if len(df3[obd_col]) > 1:
            r_squared, dNS, PBIAS = calculate_statistics(self, df3, obd_col)
            export_data(
                self, outfolder, subnum, obd_col, ts, version, ctime, df3,
                r_squared, dNS, PBIAS
                )
    else:
        stf_sim = read_output_rch_data(self, wd).loc[subnum]
        df3 = process_data(self, wd, stf_sim, ts, None, "", startDate)
        export_data(self, outfolder, subnum, "", ts, version, ctime, df3)

def process_data(self, wd, stf_sim, ts, obd_file, obd_col, startDate):
    df = update_index(self, stf_sim, startDate)
    df = time_cvt(self, df, ts)
    if self.dlg.checkBox_stream_obd.isChecked():
        obd = read_stf_obd(self, wd, obd_file)
        df2 = pd.concat([df, obd[obd_col]], axis=1)
        df3 = df2.dropna()
    else:
        df3 = df
    return df3


def export_data(
        self, outfolder, subnum, obd_col, ts, version, ctime, df3, 
        r_squared=None, dNS=None, PBIAS=None
        ):
        try:
            file_name = f"swatmf_reach({subnum})_obd({obd_col})_{ts.lower()}.txt"
            with open(os.path.join(outfolder, file_name), 'w') as f:
                f.write(f"# {file_name} is created by QSWATMOD2 plugin {version}{ctime}\n")
                df3.drop('filter', axis=1).to_csv(
                    f, index_label="Date", sep='\t', float_format='%10.4f', 
                    lineterminator='\n', 
                    encoding='utf-8'
                )
                f.write('\n')
                f.write("# Statistics\n")
                if r_squared is not None:
                    f.write("Nash–Sutcliffe: " + str('{:.4f}'.format(dNS) + "\n"))
                    f.write("R-squared: " + str('{:.4f}'.format(r_squared) + "\n"))
                    f.write("PBIAS: " + str('{:.4f}'.format(PBIAS) + "\n"))
                else:
                    f.write("Nash–Sutcliffe: ---\n")
                    f.write("R-squared: ---\n")
                    f.write("PBIAS: ---\n")

            msgBox = QMessageBox()
            msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
            msgBox.setWindowTitle("Exported!")
            msgBox.setText(f"'{file_name}' file is exported to your 'exported_files' folder!")
            msgBox.exec_()

        except Exception as e:
            show_error_message(self, "Error exporting data", str(e))

def calculate_statistics(self, df3, obd_col):
    r_squared = (
        (sum((df3[obd_col] - df3[obd_col].mean()) * (df3.stf_sim - df3.stf_sim.mean()))) ** 2 /
        (sum((df3[obd_col] - df3[obd_col].mean()) ** 2) * sum((df3.stf_sim - df3.stf_sim.mean()) ** 2))
    )
    dNS = 1 - (sum((df3.stf_sim - df3[obd_col]) ** 2) / sum((df3[obd_col] - df3[obd_col].mean()) ** 2))
    PBIAS = 100 * (sum(df3[obd_col] - df3.stf_sim) / sum(df3[obd_col]))
    return r_squared, dNS, PBIAS

def show_error_message(self, title, message):
    msgBox = QMessageBox()
    msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
    msgBox.setWindowTitle(title)
    msgBox.setText(message)
    msgBox.exec_()

# NOTE: loading data
def load_str_obd(self):
    QSWATMOD_path_dict = self.dirs_and_paths()
    settings = QSettings()
    if settings.contains('/QSWATMOD2/LastInputPath'):
        path = str(settings.value('/QSWATMOD2/LastInputPath'))
    else:
        path = ''
    title = "Provide 'streamflow.obd' file!"
    inFileName, __ = QFileDialog.getOpenFileNames(
        None, title, path,
        "Observation data (*.obd *.OBD);; All files (*.*)"
        )
    if inFileName:
        settings.setValue('/QSWATMOD2/LastInputPath', os.path.dirname(str(inFileName)))
        output_dir = QSWATMOD_path_dict['SMfolder']
        inInfo = QFileInfo(inFileName[0])
        inFile = inInfo.fileName()
        pattern = os.path.splitext(inFileName[0])[0] + '.*'

        # inName = os.path.splitext(inFile)[0]
        inName = 'streamflow'
        for f in glob.iglob(pattern):
            suffix = os.path.splitext(f)[1]
            if os.name == 'nt':
                outfile = ntpath.join(output_dir, inName + '.obd')
            else:
                outfile = posixpath.join(output_dir, inName + '.obd')             
            shutil.copy(f, outfile)


def load_mf_obd(self):
    QSWATMOD_path_dict = self.dirs_and_paths()
    settings = QSettings()
    if settings.contains('/QSWATMOD2/LastInputPath'):
        path = str(settings.value('/QSWATMOD2/LastInputPath'))
    else:
        path = ''
    title = "Provide 'modflow.obd' file!"
    inFileName, __ = QFileDialog.getOpenFileNames(
        None, title, path,
        "Observation data (*.obd *.OBD);; All files (*.*)"
        )
    if inFileName:
        settings.setValue('/QSWATMOD2/LastInputPath', os.path.dirname(str(inFileName)))           
        output_dir = QSWATMOD_path_dict['SMfolder']
        inInfo = QFileInfo(inFileName[0])
        inFile = inInfo.fileName()
        pattern = os.path.splitext(inFileName[0])[0] + '.*'

        # inName = os.path.splitext(inFile)[0]
        inName = 'modflow'
        for f in glob.iglob(pattern):
            suffix = os.path.splitext(f)[1]
            if os.name == 'nt':
                outfile = ntpath.join(output_dir, inName + '.obd')
            else:
                outfile = posixpath.join(output_dir, inName + '.obd')             
            shutil.copy(f, outfile)


