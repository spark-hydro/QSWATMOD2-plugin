# -*- coding: utf-8 -*-
from builtins import str
from qgis.core import QgsProject              
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
import glob

# try:
#     import deps.pandas as pd
# except AttributeError:
#     msgBox = QMessageBox()
#     msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
#     msgBox.setWindowTitle("QSWATMOD2")
#     msgBox.setText("Please, restart QGIS to initialize QSWATMOD2 properly.")
#     msgBox.exec_()

# MODFLOW water table plot =======================================================================
def read_grid_id(self):
    for self.layer in list(QgsProject.instance().mapLayers().values()):
        if self.layer.name() == ("mf_obs (SWAT-MODFLOW)"):
            self.dlg.groupBox_plot_wt.setEnabled(True)
            self.layer = QgsProject.instance().mapLayersByName("mf_obs (SWAT-MODFLOW)")[0]
            feats = self.layer.getFeatures()

            # get grid_id as a list
            unsorted_grid_id = [str(f.attribute("grid_id")) for f in feats]

            # Sort this list
            sorted_grid_id = sorted(unsorted_grid_id, key = int)
            # a = sorted(a, key=lambda x: float(x))
            self.dlg.comboBox_grid_id.clear()
            # self.dlg.comboBox_sub_number.addItem('')
            self.dlg.comboBox_grid_id.addItems(sorted_grid_id) # in addItem list should contain string numbers
        else:
            self.dlg.groupBox_plot_wt.setEnabled(False)


def read_wtObd(self):
    from qgis.PyQt import QtCore, QtGui, QtSql
    QSWATMOD_path_dict = self.dirs_and_paths()
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
        self.dlg.comboBox_wt_obs_data.clear()
        self.dlg.frame_wt_obd.setEnabled(False)
        self.dlg.radioButton_wt_obd_line.setEnabled(False)
        self.dlg.radioButton_wt_obd_pt.setEnabled(False)
        self.dlg.spinBox_wt_obd_size.setEnabled(False)


def get_gwls_obds(self):
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

def wt_plot_daily(self):
    if self.dlg.checkBox_darktheme.isChecked():
        plt.style.use('dark_background')
    else:
        plt.style.use('default')        
    QSWATMOD_path_dict = self.dirs_and_paths()
    stdate, eddate, stdate_warmup, eddate_warmup = self.define_sim_period() 
    wd = QSWATMOD_path_dict['SMfolder']
    startDate = stdate.strftime("%m/%d/%Y")
    endDate = eddate.strftime("%m/%d/%Y")

    mf_obs = pd.read_csv(
                        os.path.join(wd, "modflow.obs"),
                        sep="\\s+",
                        skiprows = 2,
                        usecols = [3, 4],
                        index_col = 0,
                        names = ["grid_id", "mf_elev"],)

    # Convert dataframe into a list with string items inside list
    grid_id_lst = mf_obs.index.astype(str).values.tolist()
    grid_id = self.dlg.comboBox_grid_id.currentText()
    gd_obd_nam = self.dlg.comboBox_dtw_obd.currentText()

    fig, ax = plt.subplots(figsize = (9,4))
    ax.tick_params(axis='both', labelsize=8)
    if self.dlg.checkBox_wt_obd.isChecked():
        gd_obd = pd.read_csv(
                    os.path.join(wd, gd_obd_nam),
                    index_col=0,
                    parse_dates=True,
                    na_values=[-999, ""])
        output_wt = pd.read_csv(
                            os.path.join(wd, "swatmf_out_MF_obs"),
                            sep="\\s+",
                            skiprows = 1,
                            names = grid_id_lst,)
        
        # get observed watertable
        wt_ob = self.dlg.comboBox_wt_obs_data.currentText()

        # try:
            # Make a variable for depth to water
        if self.dlg.checkBox_depthTowater.isChecked():
            # Calculate depth to water (Simulated watertable - landsurface)
            df = output_wt[str(grid_id)] - float(mf_obs.loc[int(grid_id)])
            ax.set_ylabel(r'Depth to Water $[m]$', fontsize = 8)
            ax.set_title(
                        u'Daily Depth to watertable' + u" @ Grid id: " + 
                        grid_id, fontsize=10, loc='left')  # Title can be different based on condition
        else:
            df = output_wt[str(grid_id)]
            ax.set_ylabel(r'Hydraulic Head $[m]$', fontsize = 8)
            ax.set_title(
                        u'Daily Watertable Elevation' + u" @ Grid id: " + 
                        grid_id, fontsize=10, loc='left')

        df.index = pd.date_range(startDate, periods=len(df))
        ax.plot(df.index, df, c='dodgerblue', lw=1, label="Simulated")
        df2 = pd.concat([df, gd_obd[wt_ob]], axis=1)
        df3 = df2.dropna()
        if self.dlg.radioButton_wt_obd_pt.isChecked():
            size = float(self.dlg.spinBox_wt_obd_size.value())
            ax.scatter(
                        df3.index, df3[wt_ob], edgecolors='m', alpha=0.5, s=size, marker='o',
                        facecolors='none', label="Observed", zorder=3)
        else:
            ax.plot(
                    df3.index, df3[wt_ob], c='m', lw=1.5, alpha=0.5,
                    label="Observed", zorder=3)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b-%d\n%Y'))

        if (len(df3[wt_ob]) > 1):

            ## R-squared
            r_squared = (
                (
                    (sum((df3[wt_ob] - df3[wt_ob].mean())*(df3[grid_id]-df3[grid_id].mean())))**2
                ) 
                /
                (
                    (sum((df3[wt_ob] - df3[wt_ob].mean())**2)* (sum((df3[grid_id]-df3[grid_id].mean())**2))
                ))
            )

            ##Nash–Sutcliffe (E) model efficiency coefficient ---used up in the class
            dNS = 1 - (
                sum((df3[grid_id] - df3[wt_ob])**2) /
                sum((df3[wt_ob] - (df3[wt_ob]).mean())**2))

            ## PBIAS
            PBIAS =  100*(sum(df3[wt_ob] - df3[grid_id]) / sum(df3[wt_ob]))

            ####
            ax.text(
                .01, 0.95, u'Nash–Sutcliffe: '+ "%.4f" % dNS,
                fontsize = 8,
                horizontalalignment='left',
                color='lime',
                transform=ax.transAxes)

            ax.text(
                .01, 0.90, r'$R^2$: '+ "%.4f" % r_squared,
                fontsize = 8,
                horizontalalignment='left',
                color='lime',
                transform=ax.transAxes)

            ax.text(
                .99, 0.95, u'PBIAS: '+ "%.4f" % PBIAS,
                fontsize = 8,
                horizontalalignment='right',
                color='lime',
                transform=ax.transAxes)

        else:
            ax.text(
                .01,.95, u'Nash–Sutcliffe: '+ u"---",
                fontsize = 8,
                horizontalalignment='left',
                transform=ax.transAxes)

            ax.text(
                .01, 0.90, r'$R^2$: '+ u"---",
                fontsize = 8,
                horizontalalignment='left',
                color='lime',
                transform=ax.transAxes)

            ax.text(
                .99, 0.95, u'PBIAS: ' + u"---",
                fontsize = 8,
                horizontalalignment='right',
                color='lime',
                transform=ax.transAxes)

    else:
        output_wt = pd.read_csv(
                            os.path.join(wd, "swatmf_out_MF_obs"),
                            sep="\\s+",
                            skiprows = 1,
                            names = grid_id_lst,)
        try:
            if self.dlg.checkBox_depthTowater.isChecked():
                # Calculate depth to water (Simulated watertable - landsurface)
                df = output_wt[str(grid_id)] - float(mf_obs.loc[int(grid_id)])
                ax.set_ylabel(r'Depth to Water $[m]$', fontsize = 8)
                ax.set_title(
                            u'Daily Depth to watertable' + u" @ Grid id: " + grid_id, fontsize = 10,
                            loc='left')
            else:
                df = output_wt[str(grid_id)]
                ax.set_ylabel(r'Hydraulic Head $[m]$', fontsize = 8)
                ax.set_title(
                            u'Daily Watertable Elevation' + u" @ Grid id: " + grid_id, fontsize = 10,
                            loc='left')

            df.index = pd.date_range(startDate, periods=len(df))
            ax.plot(df.index, df, c = 'dodgerblue', lw = 1, label = "Simulated")
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b-%d\n%Y'))

        except:
            ax.text(.5,.5, u"Running the simulation for a warm-up period!",
                    fontsize = 12,
                    horizontalalignment='center',
                    weight = 'extra bold',
                    color = 'y',
                    transform=ax.transAxes,)

    plt.legend(fontsize = 8,  loc = "lower right", ncol=2, bbox_to_anchor = (1, 1)) # edgecolor="w",
    # plt.tight_layout(rect=[0,0,0.75,1])
    plt.show()


def wt_plot_monthly(self):
    if self.dlg.checkBox_darktheme.isChecked():
        plt.style.use('dark_background')
    else:
        plt.style.use('default')        
    QSWATMOD_path_dict = self.dirs_and_paths()
    stdate, eddate, stdate_warmup, eddate_warmup = self.define_sim_period() 
    wd = QSWATMOD_path_dict['SMfolder']
    startDate = stdate.strftime("%m/%d/%Y")
    endDate = eddate.strftime("%m/%d/%Y")

    mf_obs = pd.read_csv(os.path.join(wd, "modflow.obs"),
                   sep="\\s+",
                   skiprows = 2,
                   usecols = [3, 4],
                   index_col = 0,
                   names = ["grid_id", "mf_elev"],)

    # Convert dataframe into a list with string items inside list
    grid_id_lst = mf_obs.index.astype(str).values.tolist()
    grid_id = self.dlg.comboBox_grid_id.currentText()
    gd_obd_nam = self.dlg.comboBox_dtw_obd.currentText()
    fig, ax = plt.subplots(figsize = (9,4))
    ax.tick_params(axis='both', labelsize=8)

    if self.dlg.checkBox_wt_obd.isChecked():
        gd_obd = pd.read_csv(
                    os.path.join(wd, gd_obd_nam),
                    index_col=0,
                    parse_dates=True,
                    na_values=[-999, ""])

        output_wt = pd.read_csv(os.path.join(wd, "swatmf_out_MF_obs"),
                           sep="\\s+",
                           skiprows = 1,
                           names = grid_id_lst,)
        
        # get observed watertable
        wt_ob = self.dlg.comboBox_wt_obs_data.currentText()

        try:
            # Make a variable for depth to water
            if self.dlg.checkBox_depthTowater.isChecked():
                # Calculate depth to water (Simulated watertable - landsurface)
                df = output_wt[str(grid_id)] - float(mf_obs.loc[int(grid_id)])
                df.index = pd.date_range(startDate, periods=len(df))
                dfm = df.resample('M').mean()
                wtObdm = gd_obd.resample('M').mean()
                ax.set_ylabel(r'Depth to Water $[m]$', fontsize = 8)
                ax.set_title(u'Monthly Depth to watertable' + u" @ Grid id: " + grid_id, fontsize = 10,
                            loc='left')
            else:
                df = output_wt[str(grid_id)]
                df.index = pd.date_range(startDate, periods=len(df))
                dfm = df.resample('M').mean()
                wtObdm = gd_obd.resample('M').mean()
                ax.set_ylabel(r'Hydraulic Head $[m]$', fontsize = 8)
                ax.set_title(u'Monthly Watertable Elevation' + u" @ Grid id: " + grid_id, fontsize = 10,
                            loc='left')

            ax.plot(dfm.index, dfm, c = 'dodgerblue', lw = 1, label = "Simulated")
            df2 = pd.concat([dfm, wtObdm[wt_ob]], axis = 1)
            df3 = df2.dropna()
            if self.dlg.radioButton_wt_obd_pt.isChecked():
                size = float(self.dlg.spinBox_wt_obd_size.value())
                ax.scatter(
                            df3.index, df3[wt_ob], edgecolors='m', alpha=0.5, s=size, marker='o',
                            facecolors='none', label="Observed", zorder=3)
            else:
                ax.plot(
                        df3.index, df3[wt_ob], c='m', lw=1.5, alpha=0.5,
                        label="Observed", zorder=3)
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b-%d\n%Y'))

            if (len(df3[wt_ob]) > 1):

                ## R-squared
                r_squared = (
                    (
                        (sum((df3[wt_ob] - df3[wt_ob].mean())*(df3[grid_id]-df3[grid_id].mean())))**2
                    ) 
                    /
                    (
                        (sum((df3[wt_ob] - df3[wt_ob].mean())**2)* (sum((df3[grid_id]-df3[grid_id].mean())**2))
                    ))
                )

                ##Nash–Sutcliffe (E) model efficiency coefficient ---used up in the class
                dNS = 1 - (sum((df3[grid_id] - df3[wt_ob])**2) / 
                    sum((df3[wt_ob] - (df3[wt_ob]).mean())**2))

                ## PBIAS
                PBIAS =  100*(sum(df3[wt_ob] - df3[grid_id]) / sum(df3[wt_ob]))

                ####
                ax.text(.01, 0.95, u'Nash–Sutcliffe: '+ "%.4f" % dNS,
                    fontsize = 8,
                    horizontalalignment='left',
                    color='lime',
                    transform=ax.transAxes)

                ax.text(.01, 0.90, r'$R^2$: '+ "%.4f" % r_squared,
                    fontsize = 8,
                    horizontalalignment='left',
                    color='lime',
                    transform=ax.transAxes)

                ax.text(.99, 0.95, u'PBIAS: '+ "%.4f" % PBIAS,
                    fontsize = 8,
                    horizontalalignment='right',
                    color='lime',
                    transform=ax.transAxes)

            else:
                ax.text(.01,.95, u'Nash–Sutcliffe: '+ u"---",
                    fontsize = 8,
                    horizontalalignment='left',
                    transform=ax.transAxes)

                ax.text(.01, 0.90, r'$R^2$: '+ u"---",
                    fontsize = 8,
                    horizontalalignment='left',
                    color='lime',
                    transform=ax.transAxes)

                ax.text(.99, 0.95, u'PBIAS: ' + u"---",
                    fontsize = 8,
                    horizontalalignment='right',
                    color='lime',
                    transform=ax.transAxes)

        except:          
            ax.text(.5,.5, u"Running the simulation for a warm-up period!",
                    fontsize = 12,
                    horizontalalignment='center',
                    weight = 'extra bold',
                    color = 'y',
                    transform=ax.transAxes,)
                    # color = colors[i%4])
    else:
        output_wt = pd.read_csv(os.path.join(wd, "swatmf_out_MF_obs"),
                           sep="\\s+",
                           skiprows = 1,
                           names = grid_id_lst,)

        try:
            if self.dlg.checkBox_depthTowater.isChecked():
                # Calculate depth to water (Simulated watertable - landsurface)
                df = output_wt[str(grid_id)] - float(mf_obs.loc[int(grid_id)])
                df.index = pd.date_range(startDate, periods=len(df))                
                dfm = df.resample('M').mean()
                ax.set_ylabel(r'Depth to Water $[m]$', fontsize = 8)
                ax.set_title(u'Monthly Depth to watertable' + u" @ Grid id: " + grid_id, fontsize = 10,
                            loc='left')
            else:
                df = output_wt[str(grid_id)]
                df.index = pd.date_range(startDate, periods=len(df))
                dfm = df.resample('M').mean()
                ax.set_ylabel(r'Hydraulic Head $[m]$', fontsize = 8)
                ax.set_title(u'Monthly Watertable Elevation' + u" @ Grid id: " + grid_id, fontsize = 10,
                            loc='left')

            ax.plot(dfm.index, dfm, c = 'dodgerblue', lw = 1, label = "Simulated")
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b-%d\n%Y'))

        except:
            ax.text(.5,.5, u"Running the simulation for a warm-up period!",
                    fontsize = 12,
                    horizontalalignment='center',
                    weight = 'extra bold',
                    color = 'y',
                    transform=ax.transAxes,)

    plt.legend(fontsize = 8,  loc = "lower right", ncol=2, bbox_to_anchor = (1, 1)) # edgecolor="w",
    # plt.tight_layout(rect=[0,0,0.75,1])
    plt.show()


def wt_plot_annual(self):
    if self.dlg.checkBox_darktheme.isChecked():
        plt.style.use('dark_background')
    else:
        plt.style.use('default')        
    QSWATMOD_path_dict = self.dirs_and_paths()
    stdate, eddate, stdate_warmup, eddate_warmup = self.define_sim_period() 
    wd = QSWATMOD_path_dict['SMfolder']
    startDate = stdate.strftime("%m/%d/%Y")
    endDate = eddate.strftime("%m/%d/%Y")

    mf_obs = pd.read_csv(os.path.join(wd, "modflow.obs"),
                   sep="\\s+",
                   skiprows = 2,
                   usecols = [3, 4],
                   index_col = 0,
                   names = ["grid_id", "mf_elev"],)

    # Convert dataframe into a list with string items inside list
    grid_id_lst = mf_obs.index.astype(str).values.tolist()
    grid_id = self.dlg.comboBox_grid_id.currentText()
    gd_obd_nam = self.dlg.comboBox_dtw_obd.currentText()
    fig, ax = plt.subplots(figsize = (9,4))
    ax.tick_params(axis='both', labelsize=8)

    if self.dlg.checkBox_wt_obd.isChecked():
        gd_obd = pd.read_csv(
                    os.path.join(wd, gd_obd_nam),
                    index_col=0,
                    parse_dates=True,
                    na_values=[-999, ""])

        output_wt = pd.read_csv(os.path.join(wd, "swatmf_out_MF_obs"),
                           sep="\\s+",
                           skiprows = 1,
                           names = grid_id_lst,)
        
        # get observed watertable
        wt_ob = self.dlg.comboBox_wt_obs_data.currentText()

        try:
            # Make a variable for depth to water
            if self.dlg.checkBox_depthTowater.isChecked():
                # Calculate depth to water (Simulated watertable - landsurface)
                df = output_wt[str(grid_id)] - float(mf_obs.loc[int(grid_id)])
                df.index = pd.date_range(startDate, periods=len(df))
                dfm = df.resample('A').mean()
                wtObdm = gd_obd.resample('A').mean()
                ax.set_ylabel(r'Depth to Water $[m]$', fontsize = 8)
                ax.set_title(u'Annual Depth to watertable' + u" @ Grid id: " + grid_id, fontsize = 10,
                            loc='left')
            else:
                df = output_wt[str(grid_id)]
                df.index = pd.date_range(startDate, periods=len(df))
                dfm = df.resample('A').mean()
                wtObdm = gd_obd.resample('A').mean()
                ax.set_ylabel(r'Hydraulic Head $[m]$', fontsize = 8)
                ax.set_title(u'Annual Watertable Elevation' + u" @ Grid id: " + grid_id, fontsize = 10,
                            loc='left')

            ax.plot(dfm.index, dfm, c = 'dodgerblue', lw = 1, label = "Simulated")
            df2 = pd.concat([dfm, wtObdm[wt_ob]], axis = 1)
            df3 = df2.dropna()
            if self.dlg.radioButton_wt_obd_pt.isChecked():
                size = float(self.dlg.spinBox_wt_obd_size.value())
                ax.scatter(
                            df3.index, df3[wt_ob], edgecolors='m', alpha=0.5, s=size, marker='o',
                            facecolors='none', label="Observed", zorder=3)
            else:
                ax.plot(
                        df3.index, df3[wt_ob], c='m', lw=1.5, alpha=0.5,
                        label="Observed", zorder=3)
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b-%d\n%Y'))

            if (len(df3[wt_ob]) > 1):

                ## R-squared
                r_squared = (
                    (
                        (sum((df3[wt_ob] - df3[wt_ob].mean())*(df3[grid_id]-df3[grid_id].mean())))**2
                    ) 
                    /
                    (
                        (sum((df3[wt_ob] - df3[wt_ob].mean())**2)* (sum((df3[grid_id]-df3[grid_id].mean())**2))
                    ))
                )

                ##Nash–Sutcliffe (E) model efficiency coefficient ---used up in the class
                dNS = 1 - (sum((df3[grid_id] - df3[wt_ob])**2) / 
                    sum((df3[wt_ob] - (df3[wt_ob]).mean())**2))

                ## PBIAS
                PBIAS =  100*(sum(df3[wt_ob] - df3[grid_id]) / sum(df3[wt_ob]))

                ####
                ax.text(.01, 0.95, u'Nash–Sutcliffe: '+ "%.4f" % dNS,
                    fontsize = 8,
                    horizontalalignment='left',
                    color='lime',
                    transform=ax.transAxes)

                ax.text(.01, 0.90, r'$R^2$: '+ "%.4f" % r_squared,
                    fontsize = 8,
                    horizontalalignment='left',
                    color='lime',
                    transform=ax.transAxes)

                ax.text(.99, 0.95, u'PBIAS: '+ "%.4f" % PBIAS,
                    fontsize = 8,
                    horizontalalignment='right',
                    color='lime',
                    transform=ax.transAxes)

            else:
                ax.text(.01,.95, u'Nash–Sutcliffe: '+ u"---",
                    fontsize = 8,
                    horizontalalignment='left',
                    transform=ax.transAxes)

                ax.text(.01, 0.90, r'$R^2$: '+ u"---",
                    fontsize = 8,
                    horizontalalignment='left',
                    color='lime',
                    transform=ax.transAxes)

                ax.text(.99, 0.95, u'PBIAS: '+ u"---",
                    fontsize = 8,
                    horizontalalignment='right',
                    color='lime',
                    transform=ax.transAxes)

        except:         
            ax.text(.5,.5, u"Running the simulation for a warm-up period!",
                    fontsize = 12,
                    horizontalalignment='center',
                    weight = 'extra bold',
                    color = 'y',
                    transform=ax.transAxes,)
                    # color = colors[i%4])
    else:
        output_wt = pd.read_csv(os.path.join(wd, "swatmf_out_MF_obs"),
                           sep="\\s+",
                           skiprows = 1,
                           names = grid_id_lst,)

        try:
            if self.dlg.checkBox_depthTowater.isChecked():
                # Calculate depth to water (Simulated watertable - landsurface)
                df = output_wt[str(grid_id)] - float(mf_obs.loc[int(grid_id)])
                df.index = pd.date_range(startDate, periods=len(df))                
                dfm = df.resample('A').mean()
                ax.set_ylabel(r'Depth to Water $[m]$', fontsize = 8)
                ax.set_title(u'Annual Depth to watertable' + u" @ Grid id: " + grid_id, fontsize = 10,
                            loc='left')
            else:
                df = output_wt[str(grid_id)]
                df.index = pd.date_range(startDate, periods=len(df))
                dfm = df.resample('A').mean()
                ax.set_ylabel(r'Hydraulic Head $[m]$', fontsize = 8)
                ax.set_title(u'Annual Watertable Elevation' + u" @ Grid id: " + grid_id, fontsize = 10,
                            loc='left')

            ax.plot(dfm.index, dfm, c = 'dodgerblue', lw = 1, label = "Simulated")
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b-%d\n%Y'))

        except:
            ax.text(.5,.5, u"Running the simulation for a warm-up period!",
                    fontsize = 12,
                    horizontalalignment='center',
                    weight = 'extra bold',
                    color = 'y',
                    transform=ax.transAxes,)

    plt.legend(fontsize = 8,  loc = "lower right", ncol=2, bbox_to_anchor = (1, 1)) # edgecolor="w",
    # plt.tight_layout(rect=[0,0,0.75,1])
    plt.show()


"""
Export data only selected
"""

def export_wt_daily(self):
    from qgis.PyQt import QtCore, QtGui, QtSql
    QSWATMOD_path_dict = self.dirs_and_paths()
    stdate, eddate, stdate_warmup, eddate_warmup = self.define_sim_period() 
    wd = QSWATMOD_path_dict['SMfolder']
    outfolder = QSWATMOD_path_dict['exported_files']
    startDate = stdate.strftime("%m/%d/%Y")
    endDate = eddate.strftime("%m/%d/%Y")

    # Add info
    from datetime import datetime
    version = "version 2.10.1."
    time = datetime.now().strftime('- %m/%d/%y %H:%M:%S -')

    mf_obs = pd.read_csv(
                        os.path.join(wd, "modflow.obs"),
                        sep="\\s+",
                        skiprows = 2,
                        usecols = [3, 4],
                        index_col = 0,
                        names = ["grid_id", "mf_elev"],)

    # Convert dataframe into a list with string items inside list
    grid_id_lst = mf_obs.index.astype(str).values.tolist()
    gd_obd_nam = self.dlg.comboBox_dtw_obd.currentText()
    grid_id = self.dlg.comboBox_grid_id.currentText()


    if self.dlg.checkBox_wt_obd.isChecked():
        gd_obd = pd.read_csv(
                    os.path.join(wd, gd_obd_nam),
                    index_col=0,
                    parse_dates=True,
                    na_values=[-999, ""])

        output_wt = pd.read_csv(
                                os.path.join(wd, "swatmf_out_MF_obs"),
                                sep="\\s+",
                                skiprows=1,
                                names=grid_id_lst,)

        # get observed watertable
        wt_ob = self.dlg.comboBox_wt_obs_data.currentText()

        try:
            # Make a variable for depth to water
            if self.dlg.checkBox_depthTowater.isChecked():
                # Calculate depth to water (Simulated watertable - landsurface)
                df = output_wt[str(grid_id)] - float(mf_obs.loc[int(grid_id)])
                df.index = pd.date_range(startDate, periods=len(df))
                df2 = pd.concat([df, gd_obd[wt_ob]], axis = 1)
                df3 = df2.dropna()

                if (len(df3[wt_ob]) > 1):

                    ## R-squared
                    r_squared = (
                        (
                            (sum((df3[wt_ob] - df3[wt_ob].mean())*(df3[grid_id]-df3[grid_id].mean())))**2
                        ) 
                        /
                        (
                            (sum((df3[wt_ob] - df3[wt_ob].mean())**2)* (sum((df3[grid_id]-df3[grid_id].mean())**2))
                        ))
                    )

                    ##Nash–Sutcliffe (E) model efficiency coefficient ---used up in the class
                    dNS = 1 - (sum((df3[grid_id] - df3[wt_ob])**2) / 
                        sum((df3[wt_ob] - (df3[wt_ob]).mean())**2))

                    ## PBIAS
                    PBIAS =  100*(sum(df3[wt_ob] - df3[grid_id]) / sum(df3[wt_ob]))

                    # ------------ Export Data to file -------------- #
                    with open(
                            os.path.join(
                                outfolder, "swatmf_grid_id(" + str(grid_id) + ")"+
                                "_ob("+ str(wt_ob)+")_d_dtw.txt"), 'w') as f:
                        f.write("# swatmf_grid_id(" + str(grid_id) + ")"+"_ob("+ str(wt_ob)
                                +")_d_dtw.txt is created by QSWATMOD2 plugin "+ version + time + "\n")
                        df3.to_csv(f, index_label = "Date", sep = '\t', float_format='%10.4f', line_terminator='\n', encoding='utf-8')
                        f.write('\n')
                        f.write("# Statistics\n")
                        f.write("Nash–Sutcliffe: " + str('{:.4f}'.format(dNS) + "\n"))
                        f.write("R-squared: " + str('{:.4f}'.format(r_squared) + "\n"))
                        f.write("PBIAS: " + str('{:.4f}'.format(PBIAS) + "\n"))

                    msgBox = QMessageBox()
                    msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
                    msgBox.setWindowTitle("Exported!")
                    msgBox.setText(
                                "'swatmf_grid_id(" + str(grid_id) + ")"+"_ob("+ str(wt_ob)
                                +")_d_dtw.txt' file is exported to your 'exported_files' folder!")
                    msgBox.exec_()

            else:
                df = output_wt[str(grid_id)]
                df.index = pd.date_range(startDate, periods=len(df))
                df2 = pd.concat([df, gd_obd[wt_ob]], axis = 1)
                df3 = df2.dropna()

                if (len(df3[wt_ob]) > 1):

                    ## R-squared
                    r_squared = (
                        (
                            (sum((df3[wt_ob] - df3[wt_ob].mean())*(df3[grid_id]-df3[grid_id].mean())))**2
                        ) 
                        /
                        (
                            (sum((df3[wt_ob] - df3[wt_ob].mean())**2)* (sum((df3[grid_id]-df3[grid_id].mean())**2))
                        ))
                    )

                    ##Nash–Sutcliffe (E) model efficiency coefficient ---used up in the class
                    dNS = 1 - (sum((df3[grid_id] - df3[wt_ob])**2) / 
                        sum((df3[wt_ob] - (df3[wt_ob]).mean())**2))

                    ## PBIAS
                    PBIAS =  100*(sum(df3[wt_ob] - df3[grid_id]) / sum(df3[wt_ob]))

                    # ------------ Export Data to file -------------- #
                    with open(os.path.join(outfolder, "swatmf_grid_id(" + str(grid_id) + ")"+
                        "_ob("+ str(wt_ob)+")_d_wt.txt"), 'w') as f:
                        f.write("# swatmf_grid_id(" + str(grid_id) + ")"+"_ob("+ str(wt_ob)
                                +")_d_wt.txt is created by QSWATMOD2 plugin "+ version + time + "\n")
                        df3.to_csv(f, index_label = "Date", sep = '\t', float_format='%10.4f', line_terminator='\n', encoding='utf-8')
                        f.write('\n')
                        f.write("# Statistics\n")
                        f.write("Nash–Sutcliffe: " + str('{:.4f}'.format(dNS) + "\n"))
                        f.write("R-squared: " + str('{:.4f}'.format(r_squared) + "\n"))
                        f.write("PBIAS: " + str('{:.4f}'.format(PBIAS) + "\n"))

                    msgBox = QMessageBox()
                    msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
                    msgBox.setWindowTitle("Exported!")
                    msgBox.setText("'swatmf_grid_id(" + str(grid_id) + ")"+"_ob("+ str(wt_ob)
                                +")_d_wt.txt' file is exported to your 'exported_files' folder!")
                    msgBox.exec_()

        except:
            msgBox = QMessageBox()
            msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
            msgBox.setWindowTitle("Not Ready!")
            msgBox.setText("Running the simulation for a warm-up period!")
            msgBox.exec_()

    else:
        output_wt = pd.read_csv(os.path.join(wd, "swatmf_out_MF_obs"),
                           sep="\\s+",
                           skiprows = 1,
                           names = grid_id_lst,)

        try:
            if self.dlg.checkBox_depthTowater.isChecked():
                # Calculate depth to water (Simulated watertable - landsurface)
                df = output_wt[str(grid_id)] - float(mf_obs.loc[int(grid_id)])
                df.index = pd.date_range(startDate, periods=len(df))

                # ------------ Export Data to file -------------- #
                with open(os.path.join(outfolder, "swatmf_grid_id(" + str(grid_id) + ")_d_dtw.txt"), 'w') as f:
                    f.write("# swatmf_grid_id(" + str(grid_id) + ")_d_dtw.txt is created by QSWATMOD2 plugin "
                        + version + time + "\n")
                    df.to_csv(f, index_label = "Date", sep = '\t', float_format='%10.4f', line_terminator='\n', encoding='utf-8')
                    f.write('\n')
                    f.write("# Statistics\n")
                    f.write("Nash–Sutcliffe: ---\n")
                    f.write("R-squared: ---\n")
                    f.write("PBIAS: ---\n")

                msgBox = QMessageBox()
                msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
                msgBox.setWindowTitle("Exported!")
                msgBox.setText("'swatmf_grid_id(" + str(grid_id) 
                    + ")_d_dtw.txt' file is exported to your 'exported_files' folder!")
                msgBox.exec_()


            else:
                df = output_wt[str(grid_id)]
                df.index = pd.date_range(startDate, periods=len(df))

                with open(os.path.join(outfolder, "swatmf_grid_id(" + str(grid_id) + ")_d_wt.txt"), 'w') as f:
                    f.write("# swatmf_grid_id(" + str(grid_id) + ")_d_wt.txt is created by QSWATMOD2 plugin "
                        + version + time + "\n")
                    df.to_csv(f, index_label = "Date", sep = '\t', float_format='%10.4f', line_terminator='\n', encoding='utf-8')
                    f.write('\n')
                    f.write("# Statistics\n")
                    f.write("Nash–Sutcliffe: ---\n")
                    f.write("R-squared: ---\n")
                    f.write("PBIAS: ---\n")

                msgBox = QMessageBox()
                msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
                msgBox.setWindowTitle("Exported!")
                msgBox.setText("'swatmf_grid_id(" + str(grid_id) 
                    + ")_d_wt.txt' file is exported to your 'exported_files' folder!")
                msgBox.exec_()

        except:
            msgBox = QMessageBox()
            msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
            msgBox.setWindowTitle("Not Ready!")
            msgBox.setText("Nothing to write down right now!")
            msgBox.exec_()


def export_wt_monthly(self):
    from qgis.PyQt import QtCore, QtGui, QtSql
    QSWATMOD_path_dict = self.dirs_and_paths()
    stdate, eddate, stdate_warmup, eddate_warmup = self.define_sim_period() 
    wd = QSWATMOD_path_dict['SMfolder']
    outfolder = QSWATMOD_path_dict['exported_files']
    startDate = stdate.strftime("%m/%d/%Y")
    endDate = eddate.strftime("%m/%d/%Y")

    # Add info
    from datetime import datetime
    version = "version 2.10.1."
    time = datetime.now().strftime('- %m/%d/%y %H:%M:%S -')

    mf_obs = pd.read_csv(os.path.join(wd, "modflow.obs"),
                   sep="\\s+",
                   skiprows = 2,
                   usecols = [3, 4],
                   index_col = 0,
                   names = ["grid_id", "mf_elev"],)

    # Convert dataframe into a list with string items inside list
    grid_id_lst = mf_obs.index.astype(str).values.tolist()
    grid_id = self.dlg.comboBox_grid_id.currentText()
    gd_obd_nam = self.dlg.comboBox_dtw_obd.currentText()
    if self.dlg.checkBox_wt_obd.isChecked():
        gd_obd = pd.read_csv(
                    os.path.join(wd, gd_obd_nam),
                    index_col=0,
                    parse_dates=True,
                    na_values=[-999, ""])
        output_wt = pd.read_csv(os.path.join(wd, "swatmf_out_MF_obs"),
                           sep="\\s+",
                           skiprows = 1,
                           names = grid_id_lst,)
        
        # get observed watertable
        wt_ob = self.dlg.comboBox_wt_obs_data.currentText()

        try:
            # Make a variable for depth to water
            if self.dlg.checkBox_depthTowater.isChecked():
                # Calculate depth to water (Simulated watertable - landsurface)
                df = output_wt[str(grid_id)] - float(mf_obs.loc[int(grid_id)])
                df.index = pd.date_range(startDate, periods=len(df))
                dfm = df.resample('M').mean()
                wtObdm = gd_obd.resample('M').mean()             
                df2 = pd.concat([dfm, wtObdm[wt_ob]], axis = 1)
                df3 = df2.dropna()

                if (len(df3[wt_ob]) > 1):

                    ## R-squared
                    r_squared = (
                        (
                            (sum((df3[wt_ob] - df3[wt_ob].mean())*(df3[grid_id]-df3[grid_id].mean())))**2
                        ) 
                        /
                        (
                            (sum((df3[wt_ob] - df3[wt_ob].mean())**2)* (sum((df3[grid_id]-df3[grid_id].mean())**2))
                        ))
                    )

                    ##Nash–Sutcliffe (E) model efficiency coefficient ---used up in the class
                    dNS = 1 - (sum((df3[grid_id] - df3[wt_ob])**2) / 
                        sum((df3[wt_ob] - (df3[wt_ob]).mean())**2))

                    ## PBIAS
                    PBIAS =  100*(sum(df3[wt_ob] - df3[grid_id]) / sum(df3[wt_ob]))
                # ------------ Export Data to file -------------- #
                with open(os.path.join(outfolder, "swatmf_grid_id(" + str(grid_id) + ")"+
                    "_ob("+ str(wt_ob)+")_m_dtw.txt"), 'w') as f:
                    f.write("# swatmf_grid_id(" + str(grid_id) + ")"+"_ob("+ str(wt_ob)
                            +")_m_dtw.txt is created by QSWATMOD2 plugin "+ version + time + "\n")
                    df3.to_csv(f, index_label = "Date", sep = '\t', float_format='%10.4f', line_terminator='\n', encoding='utf-8')
                    f.write('\n')
                    f.write("# Statistics\n")
                    f.write("Nash–Sutcliffe: " + str('{:.4f}'.format(dNS) + "\n"))
                    f.write("R-squared: " + str('{:.4f}'.format(r_squared) + "\n"))
                    f.write("PBIAS: " + str('{:.4f}'.format(PBIAS) + "\n"))

                msgBox = QMessageBox()
                msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
                msgBox.setWindowTitle("Exported!")
                msgBox.setText("'swatmf_grid_id(" + str(grid_id) + ")"+"_ob("+ str(wt_ob)
                            +")_m_dtw.txt' file is exported to your 'exported_files' folder!")
                msgBox.exec_()

            else:
                df = output_wt[str(grid_id)]
                df.index = pd.date_range(startDate, periods=len(df))
                dfm = df.resample('M').mean()
                wtObdm = gd_obd.resample('M').mean()             
                df2 = pd.concat([dfm, wtObdm[wt_ob]], axis = 1)
                df3 = df2.dropna()

                if (len(df3[wt_ob]) > 1):

                    ## R-squared
                    r_squared = (
                        (
                            (sum((df3[wt_ob] - df3[wt_ob].mean())*(df3[grid_id]-df3[grid_id].mean())))**2
                        ) 
                        /
                        (
                            (sum((df3[wt_ob] - df3[wt_ob].mean())**2)* (sum((df3[grid_id]-df3[grid_id].mean())**2))
                        ))
                    )

                    ##Nash–Sutcliffe (E) model efficiency coefficient ---used up in the class
                    dNS = 1 - (sum((df3[grid_id] - df3[wt_ob])**2) / 
                        sum((df3[wt_ob] - (df3[wt_ob]).mean())**2))

                    ## PBIAS
                    PBIAS =  100*(sum(df3[wt_ob] - df3[grid_id]) / sum(df3[wt_ob]))

                # ------------ Export Data to file -------------- #
                with open(os.path.join(outfolder, "swatmf_grid_id(" + str(grid_id) + ")"+
                    "_ob("+ str(wt_ob)+")_m_wt.txt"), 'w') as f:
                    f.write("# swatmf_grid_id(" + str(grid_id) + ")"+"_ob("+ str(wt_ob)
                            +")_m_wt.txt is created by QSWATMOD2 plugin "+ version + time + "\n")
                    df3.to_csv(f, index_label = "Date", sep = '\t', float_format='%10.4f', line_terminator='\n', encoding='utf-8')
                    f.write('\n')
                    f.write("# Statistics\n")
                    f.write("Nash–Sutcliffe: " + str('{:.4f}'.format(dNS) + "\n"))
                    f.write("R-squared: " + str('{:.4f}'.format(r_squared) + "\n"))
                    f.write("PBIAS: " + str('{:.4f}'.format(PBIAS) + "\n"))

                msgBox = QMessageBox()
                msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
                msgBox.setWindowTitle("Exported!")
                msgBox.setText("'swatmf_grid_id(" + str(grid_id) + ")"+"_ob("+ str(wt_ob)
                            +")_m_wt.txt' file is exported to your 'exported_files' folder!")
                msgBox.exec_()

        except:
            msgBox = QMessageBox()
            msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
            msgBox.setWindowTitle("Not Ready!")
            msgBox.setText("Running the simulation for a warm-up period!")
            msgBox.exec_()

    else:
        output_wt = pd.read_csv(os.path.join(wd, "swatmf_out_MF_obs"),
                           sep="\\s+",
                           skiprows = 1,
                           names = grid_id_lst,)

        try:
            if self.dlg.checkBox_depthTowater.isChecked():
                # Calculate depth to water (Simulated watertable - landsurface)
                df = output_wt[str(grid_id)] - float(mf_obs.loc[int(grid_id)])
                df.index = pd.date_range(startDate, periods=len(df))
                dfm = df.resample('M').mean()

                # ------------ Export Data to file -------------- #
                with open(os.path.join(outfolder, "swatmf_grid_id(" + str(grid_id) + ")_m_dtw.txt"), 'w') as f:
                    f.write("# swatmf_grid_id(" + str(grid_id) + ")_m_dtw.txt is created by QSWATMOD2 plugin "
                        + version + time + "\n")
                    dfm.to_csv(f, index_label = "Date", sep = '\t', float_format='%10.4f', line_terminator='\n', encoding='utf-8')
                    f.write('\n')
                    f.write("# Statistics\n")
                    f.write("Nash–Sutcliffe: ---\n")
                    f.write("R-squared: ---\n")
                    f.write("PBIAS: ---\n")

                msgBox = QMessageBox()
                msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
                msgBox.setWindowTitle("Exported!")
                msgBox.setText("'swatmf_grid_id(" + str(grid_id) 
                    + ")_m_dtw.txt' file is exported to your 'exported_files' folder!")
                msgBox.exec_()


            else:
                df = output_wt[str(grid_id)]
                df.index = pd.date_range(startDate, periods=len(df))
                dfm = df.resample('M').mean()

                with open(os.path.join(outfolder, "swatmf_grid_id(" + str(grid_id) + ")_m_wt.txt"), 'w') as f:
                    f.write("# swatmf_grid_id(" + str(grid_id) + ")_m_wt.txt is created by QSWATMOD2 plugin "
                        + version + time + "\n")
                    dfm.to_csv(f, index_label = "Date", sep = '\t', float_format='%10.4f', line_terminator='\n', encoding='utf-8')
                    f.write('\n')
                    f.write("# Statistics\n")
                    f.write("Nash–Sutcliffe: ---\n")
                    f.write("R-squared: ---\n")
                    f.write("PBIAS: ---\n")

                msgBox = QMessageBox()
                msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
                msgBox.setWindowTitle("Exported!")
                msgBox.setText("'swatmf_grid_id(" + str(grid_id) 
                    + ")_m_wt.txt' file is exported to your 'exported_files' folder!")
                msgBox.exec_()

        except:
            msgBox = QMessageBox()
            msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
            msgBox.setWindowTitle("Not Ready!")
            msgBox.setText("Nothing to write down right now!")
            msgBox.exec_()


def export_wt_annual(self):
    from qgis.PyQt import QtCore, QtGui, QtSql
    QSWATMOD_path_dict = self.dirs_and_paths()
    stdate, eddate, stdate_warmup, eddate_warmup = self.define_sim_period() 
    wd = QSWATMOD_path_dict['SMfolder']
    outfolder = QSWATMOD_path_dict['exported_files']
    startDate = stdate.strftime("%m/%d/%Y")
    endDate = eddate.strftime("%m/%d/%Y")

    # Add info
    from datetime import datetime
    version = "version 2.10.1."
    time = datetime.now().strftime('- %m/%d/%y %H:%M:%S -')

    mf_obs = pd.read_csv(os.path.join(wd, "modflow.obs"),
                   sep="\\s+",
                   skiprows = 2,
                   usecols = [3, 4],
                   index_col = 0,
                   names = ["grid_id", "mf_elev"],)

    # Convert dataframe into a list with string items inside list
    grid_id_lst = mf_obs.index.astype(str).values.tolist()
    grid_id = self.dlg.comboBox_grid_id.currentText()
    gd_obd_nam = self.dlg.comboBox_dtw_obd.currentText()
    if self.dlg.checkBox_wt_obd.isChecked():
        gd_obd = pd.read_csv(
                    os.path.join(wd, gd_obd_nam),
                    index_col=0,
                    parse_dates=True,
                    na_values=[-999, ""])

        output_wt = pd.read_csv(os.path.join(wd, "swatmf_out_MF_obs"),
                           sep="\\s+",
                           skiprows = 1,
                           names = grid_id_lst,)
        
        # get observed watertable
        wt_ob = self.dlg.comboBox_wt_obs_data.currentText()

        try:
            # Make a variable for depth to water
            if self.dlg.checkBox_depthTowater.isChecked():
                # Calculate depth to water (Simulated watertable - landsurface)
                df = output_wt[str(grid_id)] - float(mf_obs.loc[int(grid_id)])
                df.index = pd.date_range(startDate, periods=len(df))
                dfa = df.resample('A').mean()
                wtObda = gd_obd.resample('A').mean()             
                df2 = pd.concat([dfa, wtObda[wt_ob]], axis = 1)
                df3 = df2.dropna()

                if (len(df3[wt_ob]) > 1):

                    ## R-squared
                    r_squared = (
                        (
                            (sum((df3[wt_ob] - df3[wt_ob].mean())*(df3[grid_id]-df3[grid_id].mean())))**2
                        ) 
                        /
                        (
                            (sum((df3[wt_ob] - df3[wt_ob].mean())**2)* (sum((df3[grid_id]-df3[grid_id].mean())**2))
                        ))
                    )

                    ##Nash–Sutcliffe (E) model efficiency coefficient ---used up in the class
                    dNS = 1 - (sum((df3[grid_id] - df3[wt_ob])**2) / 
                        sum((df3[wt_ob] - (df3[wt_ob]).mean())**2))

                    ## PBIAS
                    PBIAS =  100*(sum(df3[wt_ob] - df3[grid_id]) / sum(df3[wt_ob]))


                # ------------ Export Data to file -------------- #
                with open(os.path.join(outfolder, "swatmf_grid_id(" + str(grid_id) + ")"+
                    "_ob("+ str(wt_ob)+")_a_dtw.txt"), 'w') as f:
                    f.write("# swatmf_grid_id(" + str(grid_id) + ")"+"_ob("+ str(wt_ob)
                            +")_a_dtw.txt is created by QSWATMOD2 plugin "+ version + time + "\n")
                    df3.to_csv(f, index_label = "Date", sep = '\t', float_format='%10.4f', line_terminator='\n', encoding='utf-8')
                    f.write('\n')
                    f.write("# Statistics\n")
                    f.write("Nash–Sutcliffe: " + str('{:.4f}'.format(dNS) + "\n"))
                    f.write("R-squared: " + str('{:.4f}'.format(r_squared) + "\n"))
                    f.write("PBIAS: " + str('{:.4f}'.format(PBIAS) + "\n"))

                msgBox = QMessageBox()
                msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
                msgBox.setWindowTitle("Exported!")
                msgBox.setText("'swatmf_grid_id(" + str(grid_id) + ")"+"_ob("+ str(wt_ob)
                            +")_a_dtw.txt' file is exported to your 'exported_files' folder!")
                msgBox.exec_()

            else:
                df = output_wt[str(grid_id)]
                df.index = pd.date_range(startDate, periods=len(df))
                dfa = df.resample('A').mean()
                wtObda = gd_obd.resample('A').mean()             
                df2 = pd.concat([dfa, wtObda[wt_ob]], axis = 1)
                df3 = df2.dropna()

                if (len(df3[wt_ob]) > 1):

                    ## R-squared
                    r_squared = (
                        (
                            (sum((df3[wt_ob] - df3[wt_ob].mean())*(df3[grid_id]-df3[grid_id].mean())))**2
                        ) 
                        /
                        (
                            (sum((df3[wt_ob] - df3[wt_ob].mean())**2)* (sum((df3[grid_id]-df3[grid_id].mean())**2))
                        ))
                    )

                    ##Nash–Sutcliffe (E) model efficiency coefficient ---used up in the class
                    dNS = 1 - (sum((df3[grid_id] - df3[wt_ob])**2) / 
                        sum((df3[wt_ob] - (df3[wt_ob]).mean())**2))

                    ## PBIAS
                    PBIAS =  100*(sum(df3[wt_ob] - df3[grid_id]) / sum(df3[wt_ob]))

                # ------------ Export Data to file -------------- #
                with open(os.path.join(outfolder, "swatmf_grid_id(" + str(grid_id) + ")"+
                    "_ob("+ str(wt_ob)+")_a_wt.txt"), 'w') as f:
                    f.write("# swatmf_grid_id(" + str(grid_id) + ")"+"_ob("+ str(wt_ob)
                            +")_a_wt.txt is created by QSWATMOD2 plugin "+ version + time + "\n")
                    df3.to_csv(f, index_label = "Date", sep = '\t', float_format='%10.4f', line_terminator='\n', encoding='utf-8')
                    f.write('\n')
                    f.write("# Statistics\n")
                    f.write("Nash–Sutcliffe: " + str('{:.4f}'.format(dNS) + "\n"))
                    f.write("R-squared: " + str('{:.4f}'.format(r_squared) + "\n"))
                    f.write("PBIAS: " + str('{:.4f}'.format(PBIAS) + "\n"))

                msgBox = QMessageBox()
                msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
                msgBox.setWindowTitle("Exported!")
                msgBox.setText("'swatmf_grid_id(" + str(grid_id) + ")"+"_ob("+ str(wt_ob)
                            +")_a_wt.txt' file is exported to your 'exported_files' folder!")
                msgBox.exec_()

        except:
            msgBox = QMessageBox()
            msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
            msgBox.setWindowTitle("Not Ready!")
            msgBox.setText("Running the simulation for a warm-up period!")
            msgBox.exec_()

    else:
        output_wt = pd.read_csv(os.path.join(wd, "swatmf_out_MF_obs"),
                           sep="\\s+",
                           skiprows = 1,
                           names = grid_id_lst,)

        try:
            if self.dlg.checkBox_depthTowater.isChecked():
                # Calculate depth to water (Simulated watertable - landsurface)
                df = output_wt[str(grid_id)] - float(mf_obs.loc[int(grid_id)])
                df.index = pd.date_range(startDate, periods=len(df))
                dfa = df.resample('A').mean()

                # ------------ Export Data to file -------------- #
                with open(os.path.join(outfolder, "swatmf_grid_id(" + str(grid_id) + ")_a_dtw.txt"), 'w') as f:
                    f.write("# swatmf_grid_id(" + str(grid_id) + ")_a_dtw.txt is created by QSWATMOD2 plugin "
                        + version + time + "\n")
                    dfa.to_csv(f, index_label = "Date", sep = '\t', float_format='%10.4f', line_terminator='\n', encoding='utf-8')
                    f.write('\n')
                    f.write("# Statistics\n")
                    f.write("Nash–Sutcliffe: ---\n")
                    f.write("R-squared: ---\n")
                    f.write("PBIAS: ---\n")

                msgBox = QMessageBox()
                msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
                msgBox.setWindowTitle("Exported!")
                msgBox.setText("'swatmf_grid_id(" + str(grid_id) 
                    + ")_a_dtw.txt' file is exported to your 'exported_files' folder!")
                msgBox.exec_()

            else:
                df = output_wt[str(grid_id)]
                df.index = pd.date_range(startDate, periods=len(df))
                dfa = df.resample('A').mean()

                with open(os.path.join(outfolder, "swatmf_grid_id(" + str(grid_id) + ")_a_wt.txt"), 'w') as f:
                    f.write("# swatmf_grid_id(" + str(grid_id) + ")_a_wt.txt is created by QSWATMOD2 plugin "
                        + version + time + "\n")
                    dfa.to_csv(f, index_label = "Date", sep = '\t', float_format='%10.4f', line_terminator='\n', encoding='utf-8')
                    f.write('\n')
                    f.write("# Statistics\n")
                    f.write("Nash–Sutcliffe: ---\n")
                    f.write("R-squared: ---\n")
                    f.write("PBIAS: ---\n")

                msgBox = QMessageBox()
                msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
                msgBox.setWindowTitle("Exported!")
                msgBox.setText("'swatmf_grid_id(" + str(grid_id) 
                    + ")_a_wt.txt' file is exported to your 'exported_files' folder!")
                msgBox.exec_()

        except:
            msgBox = QMessageBox()
            msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
            msgBox.setWindowTitle("Not Ready!")
            msgBox.setText("Nothing to write down right now!")
            msgBox.exec_()