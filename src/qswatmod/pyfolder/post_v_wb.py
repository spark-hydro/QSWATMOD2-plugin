# -*- coding: utf-8 -*-
from builtins import str
from builtins import range
from qgis.core import (
    QgsProject, QgsLayerTreeLayer, QgsVectorFileWriter, QgsVectorLayer,
    QgsField)
from qgis.PyQt import QtCore, QtGui, QtSql
from qgis.PyQt.QtCore import QCoreApplication
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np
import pandas as pd
import os
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMessageBox


# try:
#     import deps.pandas as pd
# except AttributeError:
#     msgBox = QMessageBox()
#     msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
#     msgBox.setWindowTitle("QSWATMOD2")
#     msgBox.setText("Please, restart QGIS to initialize QSWATMOD2 properly.")
#     msgBox.exec_()


def read_std_dates(self):
    QSWATMOD_path_dict = self.dirs_and_paths()
    stdate, eddate, stdate_warmup, eddate_warmup = self.define_sim_period()
    wd = QSWATMOD_path_dict['SMfolder']
    startDate = stdate_warmup.strftime("%m-%d-%Y")
    startDate = stdate_warmup
    eYear = self.dlg.lineEdit_end_y.text()
    if self.dlg.radioButton_day.isChecked():
        with open(os.path.join(wd, "output.std"), "r") as infile:
            lines = []
            y = ("TIME", "UNIT", "SWAT", "(mm)")
            for line in infile:
                data = line.strip()
                if len(data) > 100 and not data.startswith(y):  # 1st filter
                    lines.append(line)
        dates = []
        for line in lines:  # 2nd filter
            try:
                date = line.split()[0]
                if (date == eYear):  # Stop looping
                    break
                elif(len(str(date)) == 4):  # filter years
                    continue
                else:
                    dates.append(line)
            except:
                pass
        date_f = []
        for i in range(len(dates)):  # 3rd filter and obtain necessary data
            if (int(dates[i].split()[0]) == 1) and (int(dates[i].split()[0]) - int(dates[i - 1].split()[0]) == -30):
                continue
            elif (int(dates[i].split()[0]) < int(dates[i-1].split()[0])) and (int(dates[i].split()[0]) != 1):
                continue
            else:
                date_f.append(int(dates[i].split()[0]))
        if self.dlg.radioButton_std_day.isChecked():
            self.dlg.doubleSpinBox_std_w_exag.setEnabled(False)
            dateList = pd.date_range(startDate, periods=len(date_f)).strftime("%m-%d-%Y").tolist()
            self.dlg.comboBox_std_sdate.clear()
            self.dlg.comboBox_std_sdate.addItems(dateList)
            self.dlg.comboBox_std_edate.clear()
            self.dlg.comboBox_std_edate.addItems(dateList)
            self.dlg.comboBox_std_edate.setCurrentIndex(len(dateList)-1)
        elif self.dlg.radioButton_std_month.isChecked():
            self.dlg.doubleSpinBox_std_w_exag.setEnabled(True)
            data = pd.DataFrame(date_f)
            data.index = pd.date_range(startDate, periods=len(date_f))
            dfm = data.resample('ME').mean()
            dfmList = dfm.index.strftime("%b-%Y").tolist()
            self.dlg.comboBox_std_sdate.clear()
            self.dlg.comboBox_std_sdate.addItems(dfmList)
            self.dlg.comboBox_std_edate.clear()
            self.dlg.comboBox_std_edate.addItems(dfmList)
            self.dlg.comboBox_std_edate.setCurrentIndex(len(dfmList)-1)
        elif self.dlg.radioButton_std_year.isChecked():
            self.dlg.doubleSpinBox_std_w_exag.setEnabled(True)
            data = pd.DataFrame(date_f)
            data.index = pd.date_range(startDate, periods=len(date_f))
            dfa = data.resample('A').mean()
            dfaList = dfa.index.strftime("%Y").tolist()
            self.dlg.comboBox_std_sdate.clear()
            self.dlg.comboBox_std_sdate.addItems(dfaList)
            self.dlg.comboBox_std_edate.clear()
            self.dlg.comboBox_std_edate.addItems(dfaList)
            self.dlg.comboBox_std_edate.setCurrentIndex(len(dfaList)-1)
    elif self.dlg.radioButton_month.isChecked():
        self.dlg.doubleSpinBox_std_w_exag.setEnabled(True)
        lines = []
        y = ("TIME", "UNIT", "SWAT", "(mm)")
        with open(os.path.join(wd, "output.std"), "r") as infile:
            for line in infile:
                data = line.strip()
                if len(data) > 100 and not data.startswith(y):
                    lines.append(line)
        dates = []
        for line in lines:
            try:
                date = line.split()[0]
                if (date == str(eYear)):  # Stop looping
                    break
                elif(len(str(date)) == 4):  # filter years
                    continue
                else:
                    dates.append(date)
            except:
                pass
        if self.dlg.radioButton_std_month.isChecked():
            dateList = pd.date_range(startDate, periods=len(dates), freq='ME').strftime("%b-%Y").tolist()
            self.dlg.comboBox_std_sdate.clear()
            self.dlg.comboBox_std_sdate.addItems(dateList)
            self.dlg.comboBox_std_edate.clear()
            self.dlg.comboBox_std_edate.addItems(dateList)
            self.dlg.comboBox_std_edate.setCurrentIndex(len(dateList)-1)
        elif self.dlg.radioButton_std_year.isChecked():
            data = pd.DataFrame(dates)
            data.index = pd.date_range(startDate, periods=len(dates), freq='ME')
            dfa = data.resample('A').sum()  # .mean() doesn't work!
            dfaList = dfa.index.strftime("%Y").tolist()
            self.dlg.comboBox_std_sdate.clear()
            self.dlg.comboBox_std_sdate.addItems(dfaList)
            self.dlg.comboBox_std_edate.clear()
            self.dlg.comboBox_std_edate.addItems(dfaList)
            self.dlg.comboBox_std_edate.setCurrentIndex(len(dfaList)-1)
    elif self.dlg.radioButton_year.isChecked():
        self.dlg.doubleSpinBox_std_w_exag.setEnabled(True)
        lines = []
        y = ("TIME", "UNIT", "SWAT", "(mm)")
        with open(os.path.join(wd, "output.std"), "r") as infile:
            for line in infile:
                data = line.strip()
                if len(data) > 100 and not data.startswith(y):
                    lines.append(line)
        dates = []
        bword = "HRU"
        for line in lines:
            try:
                date = line.split()[0]
                if (date == bword):  # Stop looping
                    break
                else:
                    dates.append(date)
            except:
                pass
        dateList = pd.date_range(startDate, periods=len(dates), freq='A').strftime("%Y").tolist()
        self.dlg.comboBox_std_sdate.clear()
        self.dlg.comboBox_std_sdate.addItems(dateList)
        self.dlg.comboBox_std_edate.clear()
        self.dlg.comboBox_std_edate.addItems(dateList)
        self.dlg.comboBox_std_edate.setCurrentIndex(len(dateList)-1)


def plot_wb_day(self):
    QSWATMOD_path_dict = self.dirs_and_paths()
    stdate, eddate, stdate_warmup, eddate_warmup = self.define_sim_period()
    wd = QSWATMOD_path_dict['SMfolder']
    startDate = stdate_warmup
    with open(os.path.join(wd, "output.std"), "r") as infile:
        lines = []
        y = ("TIME", "UNIT", "SWAT", "(mm)")
        for line in infile:
            data = line.strip()
            if len(data) > 100 and not data.startswith(y):  # 1st filter
                lines.append(line)
    eYear = self.dlg.lineEdit_end_y.text()
    dates = []
    for line in lines:  # 2nd filter
        try:
            date = line.split()[0]
            if (date == eYear):  # Stop looping
                break
            elif(len(str(date)) == 4):  # filter years
                continue
            else:
                dates.append(line)
        except:
            pass
    date_f, prec, surq, latq, gwq, swgw, perco, tile, sw, gw = [], [], [], [], [], [], [], [], [], []
    for i in range(len(dates)): # 3rd filter and obtain necessary data
        if (int(dates[i].split()[0]) == 1) and (int(dates[i].split()[0]) - int(dates[i - 1].split()[0]) == -30):
            continue
        elif (int(dates[i].split()[0]) < int(dates[i-1].split()[0])) and (int(dates[i].split()[0]) != 1):
            continue
        else:
            date_f.append(int(dates[i].split()[0]))
            prec.append(float(dates[i].split()[1]))
            surq.append(float(dates[i].split()[2]))
            latq.append(float(dates[i].split()[3]))
            gwq.append(float(dates[i].split()[4]))
            swgw.append(float(dates[i].split()[5]))
            # perco.append(float(dates[i].split()[6]))
            perco.append(float(dates[i].split()[7]))  # SM3 uses reach !SP
            tile.append(float(dates[i].split()[8]))  # not use it for now
            sw.append(float(dates[i].split()[10]))
            gw.append(float(dates[i].split()[11]))
    names = ["prec", "surq", "latq", "gwq", "swgw", "perco", "tile", "sw", "gw"]
    data = pd.DataFrame(
        np.column_stack([prec, surq, latq, gwq, swgw, perco, tile, sw, gw]),
        columns=names)
    data.index = pd.date_range(startDate, periods=len(data))
    ssdate = self.dlg.comboBox_std_sdate.currentText()
    sedate = self.dlg.comboBox_std_edate.currentText()
    dff = data[ssdate:sedate]
    if self.dlg.checkBox_darktheme.isChecked():
        plt.style.use('dark_background')
    else:
        plt.style.use('default')
    fig, axes = plt.subplots(
        nrows=4, figsize=(14, 7), sharex=True,
        gridspec_kw={
                    'height_ratios': [0.2, 0.2, 0.4, 0.2],
                    'hspace': 0.1
                    })
    plt.subplots_adjust(left=0.06, right=0.98, top=0.83, bottom=0.05)
    # == Precipitation ============================================================
    axes[0].stackplot(dff.index, dff.prec, color='slateblue')
    axes[0].set_ylim((dff.prec.max() + dff.prec.max() * 0.1), 0)
    axes[0].xaxis.tick_top()
    axes[0].spines['bottom'].set_visible(False)
    axes[0].tick_params(axis='both', labelsize=8)
    # Title
    if self.dlg.checkBox_std_title.isChecked():
        axes[0].set_title('Water Balance - Daily [mm]', fontsize=12, fontweight='semibold')
        ttl = axes[0].title
        ttl.set_position([0.5, 1.8])
    # == Soil Water ===============================================================
    axes[1].spines['top'].set_visible(False)
    axes[1].spines['bottom'].set_visible(False)
    axes[1].get_xaxis().set_visible(False)
    axes[1].stackplot(dff.index, dff.sw, color='lightgreen')
    axes[1].set_ylim(
        (dff.gwq + dff.latq + dff.surq).max(),
        (dff.gwq + dff.latq + dff.surq + dff.sw).max()
        )
    axes[1].tick_params(axis='both', labelsize=8)
    # == Interaction ============================================================
    axes[2].spines['top'].set_visible(False)
    axes[2].spines['bottom'].set_visible(False)
    axes[2].get_xaxis().set_visible(False)
    axes[2].stackplot(
        dff.index, dff.gwq, dff.latq, dff.surq, dff.sw,
        colors=['darkgreen', 'forestgreen', 'limegreen', 'lightgreen', 'b', 'dodgerblue', 'skyblue'])
    axes[2].axhline(y=0, xmin=0, xmax=1, lw=0.3, ls='--', c='grey')
    axes[2].stackplot(dff.index, (dff.swgw*-1), (dff.perco*-1), (dff.gw*-1))
    axes[2].set_ylim(
        -1*(dff.swgw + dff.perco).max(),
        (dff.gwq + dff.latq + dff.surq).max())
    axes[2].tick_params(axis='both', labelsize=8)
    axes[2].set_yticklabels([float(abs(x)) for x in axes[2].get_yticks()])
    # ===
    axes[3].stackplot(dff.index, dff.gw + dff.perco + dff.swgw, color=['skyblue'])
    # axes[3].set_yticklabels([int(abs(x)) for x in axes[3].get_yticks()])
    axes[3].set_ylim(
        ((dff.gw + dff.perco + dff.swgw).max()),
        ((dff.gw + dff.perco + dff.swgw).min())
        )
    axes[3].spines['top'].set_visible(False)
    axes[3].tick_params(axis='both', labelsize=8)
    # this is for a broken y-axis  ##################################
    d = .003  # how big to make the diagonal lines in axes coordinates
    # arguments to pass to plot, just so we don't keep repeating them
    if self.dlg.checkBox_darktheme.isChecked():
        cutcolor = 'w'
    else:
        cutcolor = 'k'
    kwargs = dict(transform=axes[1].transAxes, color=cutcolor, clip_on=False)
    axes[1].plot((-d, +d), (-d, +d), **kwargs)        # top-left diagonal
    axes[1].plot((1 - d, 1 + d), (-d, +d), **kwargs)  # top-right diagonal
    kwargs.update(transform=axes[2].transAxes)  # switch to the bottom axes
    axes[2].plot((-d, +d), (-d, +d), **kwargs)        # top-left diagonal
    axes[2].plot((1 - d, 1 + d), (-d, +d), **kwargs)  # top-right diagonal
    axes[2].plot((-d, +d), (1 - d, 1 + d), **kwargs)  # bottom-left diagonal
    axes[2].plot((1 - d, 1 + d), (1 - d, 1 + d), **kwargs)  # bottom-right diagonal
    kwargs.update(transform=axes[3].transAxes)  # switch to the bottom axes
    axes[3].plot((-d, +d), (1 - d, 1 + d), **kwargs)  # bottom-left diagonal
    axes[3].plot((1 - d, 1 + d), (1 - d, 1 + d), **kwargs)  # bottom-right diagonal
    if self.dlg.checkBox_std_legend.isChecked():
        names = (
            'Precipitation', 'Soil Water', 'Surface Runoff', 'Lateral Flow',
            'Groundwater Flow to Stream',
            'Seepage from Stream to Aquifer',
            'Deep Percolation to Aquifer',
            'Groundwater Volume')
        colors = (
            'slateblue', 'lightgreen', 'limegreen', 'forestgreen', 'darkgreen',
            'b',
            'dodgerblue',
            'skyblue')
        ps = []
        for c in colors:
            ps.append(Rectangle((0, 0), 0.1, 0.1, fc=c, alpha=1))
        legend = axes[0].legend(
            ps, names,
            loc='upper left',
            title="EXPLANATION",
            edgecolor='none',
            fontsize=8,
            bbox_to_anchor=(-0.02, 1.8),
            ncol=8)
        legend._legend_box.align = "left"
        # legend text centered
        for t in legend.texts:
            t.set_multialignment('left')
        plt.setp(legend.get_title(), fontweight='bold', fontsize=10)
    plt.show()


def plot_wb_dToM_A(self):
    QSWATMOD_path_dict = self.dirs_and_paths()
    stdate, eddate, stdate_warmup, eddate_warmup = self.define_sim_period()
    wd = QSWATMOD_path_dict['SMfolder']
    startDate = stdate_warmup
    with open(os.path.join(wd, "output.std"), "r") as infile:
        lines = []
        y = ("TIME", "UNIT", "SWAT", "(mm)")
        for line in infile:
            data = line.strip()
            if len(data) > 100 and not data.startswith(y):  # 1st filter
                lines.append(line)
    eYear = self.dlg.lineEdit_end_y.text()
    dates = []
    for line in lines:  # 2nd filter
        try:
            date = line.split()[0]
            if (date == eYear):  # Stop looping
                break
            elif(len(str(date)) == 4):  # filter years
                continue
            else:
                dates.append(line)
        except:
            pass
    date_f, prec, surq, latq, gwq, swgw, perco, tile, sw, gw = [],[],[],[],[],[],[],[],[],[]
    for i in range(len(dates)): # 3rd filter and obtain necessary data
        if (int(dates[i].split()[0]) == 1) and (int(dates[i].split()[0]) - int(dates[i - 1].split()[0]) == -30):
            continue
        elif (int(dates[i].split()[0]) < int(dates[i-1].split()[0])) and (int(dates[i].split()[0]) != 1):
            continue
        else:
            date_f.append(int(dates[i].split()[0]))
            prec.append(float(dates[i].split()[1]))
            surq.append(float(dates[i].split()[2]))
            latq.append(float(dates[i].split()[3]))
            gwq.append(float(dates[i].split()[4]))
            swgw.append(float(dates[i].split()[5]))
            # perco.append(float(dates[i].split()[6]))
            perco.append(float(dates[i].split()[7]))  # SM3 uses reach !SP
            tile.append(float(dates[i].split()[8]))  # not use it for now
            sw.append(float(dates[i].split()[10]))
            gw.append(float(dates[i].split()[11]))
    names = ["prec", "surq", "latq", "gwq", "swgw", "perco", "tile", "sw", "gw"]
    data = pd.DataFrame(
        np.column_stack([prec, surq, latq, gwq, swgw, perco, tile, sw, gw]),
        columns=names)
    data.index = pd.date_range(startDate, periods=len(data))
    ssdate = self.dlg.comboBox_std_sdate.currentText()
    sedate = self.dlg.comboBox_std_edate.currentText()
    if self.dlg.radioButton_std_month.isChecked():
        dfm = data.resample('ME').mean()
        dff = dfm[ssdate:sedate]
    elif self.dlg.radioButton_std_year.isChecked():
        dfa = data.resample('A').mean()
        dff = dfa[ssdate:sedate]
    if self.dlg.checkBox_darktheme.isChecked():
        plt.style.use('dark_background')
    else:
        plt.style.use('default')
    fig, axes = plt.subplots(
        nrows=4, figsize=(14, 7), sharex=True,
        gridspec_kw={
                    'height_ratios': [0.2, 0.2, 0.4, 0.2],
                    'hspace': 0.1
                    })
    plt.subplots_adjust(left=0.06, right=0.98, top=0.83, bottom=0.05)
    width = -20
    widthExg = float(self.dlg.doubleSpinBox_std_w_exag.value())
    # == Precipitation ============================================================
    axes[0].bar(
        dff.index, dff.prec, width * widthExg,
        # edgecolor = 'w',
        align='edge',
        # linewidth = 0.1,
        color='slateblue')
    axes[0].set_ylim((dff.prec.max() + dff.prec.max() * 0.1), 0)
    axes[0].xaxis.tick_top()
    axes[0].spines['bottom'].set_visible(False)
    axes[0].tick_params(axis='both', labelsize=8)
    if self.dlg.checkBox_std_title.isChecked():
        if self.dlg.radioButton_std_month.isChecked():
            axes[0].set_title('Water Balance - Monthly Average [mm]', fontsize=12, fontweight='semibold')
        elif self.dlg.radioButton_std_year.isChecked():
            axes[0].set_title('Water Balance - Annual Average [mm]', fontsize=12, fontweight='semibold')
        ttl = axes[0].title
        ttl.set_position([0.5, 1.8])
    # == Soil Water ===============================================================
    axes[1].spines['top'].set_visible(False)
    axes[1].spines['bottom'].set_visible(False)
    axes[1].get_xaxis().set_visible(False)
    axes[1].bar(
        dff.index, dff.sw, width * widthExg,
        bottom=dff.gwq + dff.latq + dff.surq,
        # edgecolor = 'w',
        align='edge',
        # linewidth = 0.3,
        color='lightgreen')
    axes[1].set_ylim(
        (dff.gwq + dff.latq + dff.surq).max(),
        (dff.gwq + dff.latq + dff.surq + dff.sw).max()
        )
    axes[1].tick_params(axis='both', labelsize=8)
    # == Interaction ============================================================
    axes[2].spines['top'].set_visible(False)
    axes[2].spines['bottom'].set_visible(False)
    axes[2].get_xaxis().set_visible(False)
    # gwq -> Groundwater discharge to stream
    axes[2].bar(
        dff.index, dff.gwq, width * widthExg,
        # edgecolor = 'w',
        align='edge',
        # linewidth = 0.3,
        color='darkgreen')
    # latq -> lateral flow to stream
    axes[2].bar(
        dff.index, dff.latq, width * widthExg,
        bottom=dff.gwq,
        # edgecolor='w',
        align='edge',
        # linewidth=0.3,
        color='forestgreen')
    # surq -> surface runoff to stream
    axes[2].bar(
        dff.index, dff.surq, width * widthExg,
        bottom=dff.latq + dff.gwq,
        # edgecolor='w',
        align='edge',
        # linewidth=0.3,
        color='limegreen')
    # Soil water
    axes[2].bar(
        dff.index, dff.sw, width * widthExg,
        bottom=dff.gwq + dff.latq + dff.surq,
        # edgecolor='w',
        align='edge',
        # linewidth=0.3,
        color='lightgreen')
    axes[2].axhline(y=0, xmin=0, xmax=1, lw=0.3, ls='--', c='grey')
    # swgw -> seepage to aquifer
    axes[2].bar(
        dff.index, dff.swgw*-1, width * widthExg,
        # bottom = df.latq,
        # edgecolor='w',
        align='edge',
        # linewidth=0.8,
        color='b')
    # perco -> recharge to aquifer
    axes[2].bar(
        dff.index, dff.perco*-1, width * widthExg,
        bottom=dff.swgw*-1,
        # edgecolor='w',
        align='edge',
        # linewidth=0.8,
        color='dodgerblue')
    # gw -> groundwater volume
    axes[2].bar(
        dff.index, dff.gw*-1, width * widthExg,
        bottom=(dff.perco*-1) + (dff.swgw*-1),
        # edgecolor='w',
        color=['skyblue'],
        align='edge',
        # linewidth=0.8
        )
    axes[2].set_ylim(
        -1*(dff.swgw + dff.perco).max(),
        (dff.gwq + dff.latq + dff.surq).max())
    axes[2].tick_params(axis='both', labelsize=8)
    axes[2].set_yticklabels([float(abs(x)) for x in axes[2].get_yticks()])
    # ===
    axes[3].bar(
        dff.index, dff.gw, width * widthExg,
        bottom=(dff.perco) + (dff.swgw),
        # edgecolor='w',
        color=['skyblue'],
        align='edge',
        # linewidth=0.8
        )
    # axes[3].set_yticklabels([int(abs(x)) for x in axes[3].get_yticks()])
    axes[3].set_ylim(
        ((dff.gw + dff.perco + dff.swgw).max()),
        ((dff.gw + dff.perco + dff.swgw).min())
        )
    axes[3].spines['top'].set_visible(False)
    axes[3].tick_params(axis='both', labelsize=8)
    # this is for a broken y-axis  ##################################
    d = .003  # how big to make the diagonal lines in axes coordinates
    # arguments to pass to plot, just so we don't keep repeating them
    if self.dlg.checkBox_darktheme.isChecked():
        cutcolor = 'w'
    else:
        cutcolor = 'k'
    kwargs = dict(transform=axes[1].transAxes, color=cutcolor, clip_on=False)
    axes[1].plot((-d, +d), (-d, +d), **kwargs)        # top-left diagonal
    axes[1].plot((1 - d, 1 + d), (-d, +d), **kwargs)  # top-right diagonal
    kwargs.update(transform=axes[2].transAxes)  # switch to the bottom axes
    axes[2].plot((-d, +d), (-d, +d), **kwargs)        # top-left diagonal
    axes[2].plot((1 - d, 1 + d), (-d, +d), **kwargs)  # top-right diagonal
    axes[2].plot((-d, +d), (1 - d, 1 + d), **kwargs)  # bottom-left diagonal
    axes[2].plot((1 - d, 1 + d), (1 - d, 1 + d), **kwargs)  # bottom-right diagonal
    kwargs.update(transform=axes[3].transAxes)  # switch to the bottom axes
    axes[3].plot((-d, +d), (1 - d, 1 + d), **kwargs)  # bottom-left diagonal
    axes[3].plot((1 - d, 1 + d), (1 - d, 1 + d), **kwargs)  # bottom-right diagonal
    if self.dlg.checkBox_std_legend.isChecked():
        names = (
            'Precipitation', 'Soil Water', 'Surface Runoff', 'Lateral Flow',
            'Groundwater Flow to Stream',
            'Seepage from Stream to Aquifer',
            'Deep Percolation to Aquifer',
            'Groundwater Volume')
        colors = (
            'slateblue', 'lightgreen', 'limegreen', 'forestgreen', 'darkgreen',
            'b',
            'dodgerblue',
            'skyblue')
        ps = []
        for c in colors:
            ps.append(
                Rectangle(
                    (0, 0), 0.1, 0.1, fc=c,
                    # ec = 'k',
                    alpha=1))
        legend = axes[0].legend(
            ps, names,
            loc='upper left',
            title="EXPLANATION",
            # ,handlelength = 3, handleheight = 1.5,
            edgecolor='none',
            fontsize=8,
            bbox_to_anchor=(-0.02, 1.8),
            # labelspacing = 1.5,
            ncol=8)
        legend._legend_box.align = "left"
        # legend text centered
        for t in legend.texts:
            t.set_multialignment('left')
        plt.setp(legend.get_title(), fontweight='bold', fontsize=10)
    plt.show()


def plot_wb_m_mToA(self):
    QSWATMOD_path_dict = self.dirs_and_paths()
    stdate, eddate, stdate_warmup, eddate_warmup = self.define_sim_period()
    wd = QSWATMOD_path_dict['SMfolder']
    startDate = stdate_warmup
    with open(os.path.join(wd, "output.std"), "r") as infile:
        lines = []
        y = ("TIME", "UNIT", "SWAT", "(mm)")
        for line in infile:
            data = line.strip()
            if len(data) > 100 and not data.startswith(y):  # 1st filter
                lines.append(line)
    eYear = self.dlg.lineEdit_end_y.text()
    dates = []
    for line in lines:  # 2nd filter
        try:
            date = line.split()[0]
            if (date == eYear):  # Stop looping
                break
            elif(len(str(date)) == 4):  # filter years
                continue
            else:
                dates.append(line)
        except:
            pass
    date_f, prec, surq, latq, gwq, swgw, perco, tile, sw, gw = [], [], [], [], [], [], [], [], [], []
    for i in range(len(dates)):
        date_f.append(int(dates[i].split()[0]))
        prec.append(float(dates[i].split()[1]))
        surq.append(float(dates[i].split()[2]))
        latq.append(float(dates[i].split()[3]))
        gwq.append(float(dates[i].split()[4]))
        swgw.append(float(dates[i].split()[5]))
        # perco.append(float(dates[i].split()[6]))
        perco.append(float(dates[i].split()[7]))  # SM3 uses reach !SP
        tile.append(float(dates[i].split()[8]))  # not use it for now
        sw.append(float(dates[i].split()[10]))
        gw.append(float(dates[i].split()[11]))
    names = ["prec", "surq", "latq", "gwq", "swgw", "perco", "tile", "sw", "gw"]
    data = pd.DataFrame(
        np.column_stack([prec, surq, latq, gwq, swgw, perco, tile, sw, gw]),
        columns=names)
    data.index = pd.date_range(startDate, periods=len(data), freq='ME')
    ssdate = self.dlg.comboBox_std_sdate.currentText()
    sedate = self.dlg.comboBox_std_edate.currentText()
    if self.dlg.radioButton_std_month.isChecked():
        dff = data[ssdate:sedate]
    elif self.dlg.radioButton_std_year.isChecked():
        dfa = data.resample('A').mean()
        dff = dfa[ssdate:sedate]
    if self.dlg.checkBox_darktheme.isChecked():
        plt.style.use('dark_background')
    else:
        plt.style.use('default')
    fig, axes = plt.subplots(
        nrows=4, figsize=(14, 7), sharex=True,
        gridspec_kw={
                    'height_ratios': [0.2, 0.2, 0.4, 0.2],
                    'hspace': 0.1
                    })
    plt.subplots_adjust(left=0.06, right=0.98, top=0.83, bottom=0.05)
    width = -20
    widthExg = float(self.dlg.doubleSpinBox_std_w_exag.value())
    # == Precipitation ============================================================
    axes[0].bar(
        dff.index, dff.prec,
        width * widthExg,
        # edgecolor = 'w',
        align='edge',
        # linewidth = 0.1,
        color='slateblue')
    axes[0].set_ylim((dff.prec.max() + dff.prec.max() * 0.1), 0)
    axes[0].xaxis.tick_top()
    axes[0].spines['bottom'].set_visible(False)
    axes[0].tick_params(axis='both', labelsize=8)
    if self.dlg.checkBox_std_title.isChecked():
        if self.dlg.radioButton_std_month.isChecked():
            axes[0].set_title('Water Balance - Monthly Total [mm]', fontsize=10, fontweight='semibold')
        elif self.dlg.radioButton_std_year.isChecked():
            axes[0].set_title('Water Balance - Annual Average Monthly Total [mm]', fontsize=10, fontweight='semibold')
        ttl = axes[0].title
        ttl.set_position([0.5, 1.8])
    # == Soil Water ===============================================================
    axes[1].spines['top'].set_visible(False)
    axes[1].spines['bottom'].set_visible(False)
    axes[1].get_xaxis().set_visible(False)
    axes[1].bar(
        dff.index, dff.sw, width * widthExg,
        bottom=dff.gwq + dff.latq + dff.surq,
        # edgecolor = 'w',
        align='edge',
        # linewidth = 0.3,
        color='lightgreen')
    axes[1].set_ylim(
        (dff.gwq + dff.latq + dff.surq).max(),
        (dff.gwq + dff.latq + dff.surq + dff.sw).max()
        )
    axes[1].tick_params(axis='both', labelsize=8)
    # == Interaction ============================================================
    axes[2].spines['top'].set_visible(False)
    axes[2].spines['bottom'].set_visible(False)
    axes[2].get_xaxis().set_visible(False)
    # gwq -> Groundwater discharge to stream
    axes[2].bar(
        dff.index, dff.gwq, width * widthExg,
        # edgecolor = 'w',
        align='edge',
        # linewidth = 0.3,
        color='darkgreen')
    # latq -> lateral flow to stream
    axes[2].bar(
        dff.index, dff.latq, width * widthExg,
        bottom=dff.gwq,
        # edgecolor='w',
        align='edge',
        # linewidth=0.3,
        color='forestgreen')
    # surq -> surface runoff to stream
    axes[2].bar(
        dff.index, dff.surq, width * widthExg,
        bottom=dff.latq + dff.gwq,
        # edgecolor='w',
        align='edge',
        # linewidth=0.3,
        color='limegreen')
    # Soil water
    axes[2].bar(
        dff.index, dff.sw, width * widthExg,
        bottom=dff.gwq + dff.latq + dff.surq,
        # edgecolor='w',
        align='edge',
        # linewidth=0.3,
        color='lightgreen')
    axes[2].axhline(y=0, xmin=0, xmax=1, lw=0.3, ls='--', c='grey')
    # swgw -> seepage to aquifer
    axes[2].bar(
        dff.index, dff.swgw*-1, width * widthExg,
        # bottom = df.latq,
        # edgecolor='w',
        align='edge',
        # linewidth=0.8,
        color='b')
    # perco -> recharge to aquifer
    axes[2].bar(
        dff.index, dff.perco*-1, width * widthExg,
        bottom=dff.swgw*-1,
        # edgecolor='w',
        align='edge',
        # linewidth=0.8,
        color='dodgerblue')
    # gw -> groundwater volume
    axes[2].bar(
        dff.index, dff.gw*-1, width * widthExg,
        bottom=(dff.perco*-1) + (dff.swgw*-1),
        # edgecolor='w',
        color=['skyblue'],
        align='edge',
        # linewidth=0.8
        )
    axes[2].set_ylim(
        -1*(dff.swgw + dff.perco).max(),
        (dff.gwq + dff.latq + dff.surq).max())
    axes[2].tick_params(axis='both', labelsize=8)
    axes[2].set_yticklabels([float(abs(x)) for x in axes[2].get_yticks()])
    # ===
    axes[3].bar(
        dff.index, dff.gw, width * widthExg,
        bottom=(dff.perco) + (dff.swgw),
        # edgecolor='w',
        color=['skyblue'],
        align='edge',
        # linewidth=0.8
        )
    # axes[3].set_yticklabels([int(abs(x)) for x in axes[3].get_yticks()])
    axes[3].set_ylim(
        ((dff.gw + dff.perco + dff.swgw).max()),
        ((dff.gw + dff.perco + dff.swgw).min())
        )
    axes[3].spines['top'].set_visible(False)
    axes[3].tick_params(axis='both', labelsize=8)
    # this is for a broken y-axis  ##################################
    d = .003  # how big to make the diagonal lines in axes coordinates
    # arguments to pass to plot, just so we don't keep repeating them
    if self.dlg.checkBox_darktheme.isChecked():
        cutcolor = 'w'
    else:
        cutcolor = 'k'
    kwargs = dict(transform=axes[1].transAxes, color=cutcolor, clip_on=False)
    axes[1].plot((-d, +d), (-d, +d), **kwargs)        # top-left diagonal
    axes[1].plot((1 - d, 1 + d), (-d, +d), **kwargs)  # top-right diagonal
    kwargs.update(transform=axes[2].transAxes)  # switch to the bottom axes
    axes[2].plot((-d, +d), (-d, +d), **kwargs)        # top-left diagonal
    axes[2].plot((1 - d, 1 + d), (-d, +d), **kwargs)  # top-right diagonal
    axes[2].plot((-d, +d), (1 - d, 1 + d), **kwargs)  # bottom-left diagonal
    axes[2].plot((1 - d, 1 + d), (1 - d, 1 + d), **kwargs)  # bottom-right diagonal
    kwargs.update(transform=axes[3].transAxes)  # switch to the bottom axes
    axes[3].plot((-d, +d), (1 - d, 1 + d), **kwargs)  # bottom-left diagonal
    axes[3].plot((1 - d, 1 + d), (1 - d, 1 + d), **kwargs)  # bottom-right diagonal
    if self.dlg.checkBox_std_legend.isChecked():
        names = (
            'Precipitation', 'Soil Water', 'Surface Runoff', 'Lateral Flow',
            'Groundwater Flow to Stream',
            'Seepage from Stream to Aquifer',
            'Deep Percolation to Aquifer',
            'Groundwater Volume')
        colors = (
            'slateblue', 'lightgreen', 'limegreen', 'forestgreen', 'darkgreen',
            'b',
            'dodgerblue',
            'skyblue')
        ps = []
        for c in colors:
            ps.append(
                Rectangle(
                    (0, 0), 0.1, 0.1, fc=c,
                    # ec = 'k',
                    alpha=1))
        legend = axes[0].legend(
            ps, names,
            loc='upper left',
            title="EXPLANATION",
            # ,handlelength = 3, handleheight = 1.5,
            edgecolor='none',
            fontsize=8,
            bbox_to_anchor=(-0.02, 1.8),
            # labelspacing = 1.5,
            ncol=8)
        legend._legend_box.align = "left"
        # legend text centered
        for t in legend.texts:
            t.set_multialignment('left')
        plt.setp(legend.get_title(), fontweight='bold', fontsize=10)
    plt.show()


def plot_wb_year(self):
    QSWATMOD_path_dict = self.dirs_and_paths()
    stdate, eddate, stdate_warmup, eddate_warmup = self.define_sim_period()
    wd = QSWATMOD_path_dict['SMfolder']
    startDate = stdate_warmup
    with open(os.path.join(wd, "output.std"), "r") as infile:
        lines = []
        y = ("TIME", "UNIT", "SWAT", "(mm)")
        for line in infile:
            data = line.strip()
            if len(data) > 100 and not data.startswith(y):  # 1st filter
                lines.append(line)
    dates = []
    bword = "HRU"
    for line in lines:
        try:
            date = line.split()[0]
            if (date == bword):  # Stop looping
                break
            else:
                dates.append(line)
        except:
            pass
    date_f, prec, surq, latq, gwq, swgw, perco, tile, sw, gw = [], [], [], [], [], [], [], [], [], []
    for i in range(len(dates)): # 3rd filter and obtain necessary data
        date_f.append(int(dates[i].split()[0]))
        prec.append(float(dates[i].split()[1]))
        surq.append(float(dates[i].split()[2]))
        latq.append(float(dates[i].split()[3]))
        gwq.append(float(dates[i].split()[4]))
        swgw.append(float(dates[i].split()[5]))
        # perco.append(float(dates[i].split()[6]))
        perco.append(float(dates[i].split()[7]))  # SM3 uses reach !SP
        tile.append(float(dates[i].split()[8]))  # not use it for now
        sw.append(float(dates[i].split()[10]))
        gw.append(float(dates[i].split()[11]))
    names = ["prec", "surq", "latq", "gwq", "swgw", "perco", "tile", "sw", "gw"]
    data = pd.DataFrame(
        np.column_stack([prec, surq, latq, gwq, swgw, perco, tile, sw, gw]),
        columns=names)
    data.index = pd.date_range(startDate, periods=len(data), freq="A")
    ssdate = self.dlg.comboBox_std_sdate.currentText()
    sedate = self.dlg.comboBox_std_edate.currentText()
    dff = data[ssdate:sedate]
    if self.dlg.checkBox_darktheme.isChecked():
        plt.style.use('dark_background')
    else:
        plt.style.use('default')
    fig, axes = plt.subplots(
        nrows=4, figsize=(14, 7), sharex=True,
        gridspec_kw={
                    'height_ratios': [0.2, 0.2, 0.4, 0.2],
                    'hspace': 0.1
                    })
    plt.subplots_adjust(left=0.06, right=0.98, top=0.83, bottom=0.05)
    width = -20
    widthExg = float(self.dlg.doubleSpinBox_std_w_exag.value())
    # == Precipitation ============================================================
    axes[0].bar(
        dff.index, dff.prec, width * widthExg,
        # edgecolor = 'w',
        align='edge',
        # linewidth = 0.1,
        color='slateblue')
    axes[0].set_ylim((dff.prec.max() + dff.prec.max() * 0.1), 0)
    axes[0].xaxis.tick_top()
    axes[0].spines['bottom'].set_visible(False)
    axes[0].tick_params(axis='both', labelsize=8)
    if self.dlg.checkBox_std_title.isChecked():
        axes[0].set_title('Water Balance - Annual Total [mm]', fontsize=10, fontweight='semibold')
        ttl = axes[0].title
        ttl.set_position([0.5, 1.8])
    # == Soil Water ===============================================================
    axes[1].spines['top'].set_visible(False)
    axes[1].spines['bottom'].set_visible(False)
    axes[1].get_xaxis().set_visible(False)
    axes[1].bar(
        dff.index, dff.sw, width * widthExg,
        bottom=dff.gwq + dff.latq + dff.surq,
        # edgecolor = 'w',
        align='edge',
        # linewidth = 0.3,
        color='lightgreen')
    axes[1].set_ylim(
        (dff.gwq + dff.latq + dff.surq).max(),
        (dff.gwq + dff.latq + dff.surq + dff.sw).max()
        )
    axes[1].tick_params(axis='both', labelsize=8)
    # == Interaction ============================================================
    axes[2].spines['top'].set_visible(False)
    axes[2].spines['bottom'].set_visible(False)
    axes[2].get_xaxis().set_visible(False)
    # gwq -> Groundwater discharge to stream
    axes[2].bar(
        dff.index, dff.gwq, width * widthExg,
        # edgecolor = 'w',
        align='edge',
        # linewidth = 0.3,
        color='darkgreen')
    # latq -> lateral flow to stream
    axes[2].bar(
        dff.index, dff.latq, width * widthExg,
        bottom=dff.gwq,
        # edgecolor='w',
        align='edge',
        # linewidth=0.3,
        color='forestgreen')
    # surq -> surface runoff to stream
    axes[2].bar(
        dff.index, dff.surq, width * widthExg,
        bottom=dff.latq + dff.gwq,
        # edgecolor='w',
        align='edge',
        # linewidth=0.3,
        color='limegreen')
    # Soil water
    axes[2].bar(
        dff.index, dff.sw, width * widthExg,
        bottom=dff.gwq + dff.latq + dff.surq,
        # edgecolor='w',
        align='edge',
        # linewidth=0.3,
        color='lightgreen')
    axes[2].axhline(y=0, xmin=0, xmax=1, lw=0.3, ls='--', c='grey')
    # swgw -> seepage to aquifer
    axes[2].bar(
        dff.index, dff.swgw*-1, width * widthExg,
        # bottom = df.latq,
        # edgecolor='w',
        align='edge',
        # linewidth=0.8,
        color='b')
    # perco -> recharge to aquifer
    axes[2].bar(
        dff.index, dff.perco*-1, width * widthExg,
        bottom=dff.swgw*-1,
        # edgecolor='w',
        align='edge',
        # linewidth=0.8,
        color='dodgerblue')
    # gw -> groundwater volume
    axes[2].bar(
        dff.index, dff.gw*-1, width * widthExg,
        bottom=(dff.perco*-1) + (dff.swgw*-1),
        # edgecolor='w',
        color=['skyblue'],
        align='edge',
        # linewidth=0.8
        )
    axes[2].set_ylim(
        -1*(dff.swgw + dff.perco).max(),
        (dff.gwq + dff.latq + dff.surq).max())
    axes[2].tick_params(axis='both', labelsize=8)
    axes[2].set_yticklabels([float(abs(x)) for x in axes[2].get_yticks()])
    # ===
    axes[3].bar(
        dff.index, dff.gw, width * widthExg,
        bottom=(dff.perco) + (dff.swgw),
        # edgecolor='w',
        color=['skyblue'],
        align='edge',
        # linewidth=0.8
        )
    # axes[3].set_yticklabels([int(abs(x)) for x in axes[3].get_yticks()])
    axes[3].set_ylim(
        ((dff.gw + dff.perco + dff.swgw).max()),
        ((dff.gw + dff.perco + dff.swgw).min())
        )
    axes[3].spines['top'].set_visible(False)
    axes[3].tick_params(axis='both', labelsize=8)
    # this is for a broken y-axis  ##################################
    d = .003  # how big to make the diagonal lines in axes coordinates
    # arguments to pass to plot, just so we don't keep repeating them
    if self.dlg.checkBox_darktheme.isChecked():
        cutcolor = 'w'
    else:
        cutcolor = 'k'
    kwargs = dict(transform=axes[1].transAxes, color=cutcolor, clip_on=False)
    axes[1].plot((-d, +d), (-d, +d), **kwargs)        # top-left diagonal
    axes[1].plot((1 - d, 1 + d), (-d, +d), **kwargs)  # top-right diagonal
    kwargs.update(transform=axes[2].transAxes)  # switch to the bottom axes
    axes[2].plot((-d, +d), (-d, +d), **kwargs)        # top-left diagonal
    axes[2].plot((1 - d, 1 + d), (-d, +d), **kwargs)  # top-right diagonal
    axes[2].plot((-d, +d), (1 - d, 1 + d), **kwargs)  # bottom-left diagonal
    axes[2].plot((1 - d, 1 + d), (1 - d, 1 + d), **kwargs)  # bottom-right diagonal
    kwargs.update(transform=axes[3].transAxes)  # switch to the bottom axes
    axes[3].plot((-d, +d), (1 - d, 1 + d), **kwargs)  # bottom-left diagonal
    axes[3].plot((1 - d, 1 + d), (1 - d, 1 + d), **kwargs)  # bottom-right diagonal
    if self.dlg.checkBox_std_legend.isChecked():
        names = (
            'Precipitation', 'Soil Water', 'Surface Runoff', 'Lateral Flow',
            'Groundwater Flow to Stream',
            'Seepage from Stream to Aquifer',
            'Deep Percolation to Aquifer',
            'Groundwater Volume')
        colors = (
            'slateblue', 'lightgreen', 'limegreen', 'forestgreen', 'darkgreen',
            'b',
            'dodgerblue',
            'skyblue')
        ps = []
        for c in colors:
            ps.append(
                Rectangle(
                    (0, 0), 0.1, 0.1, fc=c,
                    # ec = 'k',
                    alpha=1))
        legend = axes[0].legend(
            ps, names,
            loc='upper left',
            title="EXPLANATION",
            # ,handlelength = 3, handleheight = 1.5,
            edgecolor='none',
            fontsize=8,
            bbox_to_anchor=(-0.02, 1.8),
            # labelspacing = 1.5,
            ncol=8)
        legend._legend_box.align = "left"
        # legend text centered
        for t in legend.texts:
            t.set_multialignment('left')
        plt.setp(legend.get_title(), fontweight='bold', fontsize=10)
    plt.show()


def export_wb_d(self):
    QSWATMOD_path_dict = self.dirs_and_paths()
    stdate, eddate, stdate_warmup, eddate_warmup = self.define_sim_period()
    wd = QSWATMOD_path_dict['SMfolder']
    outfolder = QSWATMOD_path_dict['exported_files']
    startDate = stdate_warmup
    with open(os.path.join(wd, "output.std"), "r") as infile:
        lines = []
        y = ("TIME", "UNIT", "SWAT", "(mm)")
        for line in infile:
            data = line.strip()
            if len(data) > 100 and not data.startswith(y):  # 1st filter
                lines.append(line)
    eYear = self.dlg.lineEdit_end_y.text()
    dates = []
    for line in lines:  # 2nd filter
        try:
            date = line.split()[0]
            if (date == eYear):  # Stop looping
                break
            elif(len(str(date)) == 4):  # filter years
                continue
            else:
                dates.append(line)
        except:
            pass
    date_f, prec, surq, latq, gwq, swgw, perco, tile, sw, gw = [], [], [], [], [], [], [], [], [], []
    for i in range(len(dates)): # 3rd filter and obtain necessary data
        if (int(dates[i].split()[0]) == 1) and (int(dates[i].split()[0]) - int(dates[i - 1].split()[0]) == -30):
            continue
        elif (int(dates[i].split()[0]) < int(dates[i-1].split()[0])) and (int(dates[i].split()[0]) != 1):
            continue
        else:
            date_f.append(int(dates[i].split()[0]))
            prec.append(float(dates[i].split()[1]))
            surq.append(float(dates[i].split()[2]))
            latq.append(float(dates[i].split()[3]))
            gwq.append(float(dates[i].split()[4]))
            swgw.append(float(dates[i].split()[5]))
            # perco.append(float(dates[i].split()[6]))
            perco.append(float(dates[i].split()[7]))  # SM3 uses reach !SP
            tile.append(float(dates[i].split()[8]))  # not use it for now
            sw.append(float(dates[i].split()[10]))
            gw.append(float(dates[i].split()[11]))
    names = ["prec", "surq", "latq", "gwq", "swgw", "perco", "tile", "sw", "gw"]
    data = pd.DataFrame(
        np.column_stack([prec, surq, latq, gwq, swgw, perco, tile, sw, gw]),
        columns=names)
    data.index = pd.date_range(startDate, periods=len(data))
    ssdate = self.dlg.comboBox_std_sdate.currentText()
    sedate = self.dlg.comboBox_std_edate.currentText()
    # Add info
    from datetime import datetime
    version = "version 2.10.1."
    time = datetime.now().strftime('- %m/%d/%y %H:%M:%S -')
    msgBox = QMessageBox()
    msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
    msgBox.setWindowTitle("Exported!")
    if self.dlg.radioButton_std_day.isChecked():
        dff = data[ssdate:sedate]
        with open(os.path.join(outfolder, "wb_daily.txt"), 'w') as f:
            f.write("# Daily water balance [mm] - QSWATMOD2 Plugin " + version + time + "\n")
            dff.to_csv(f, index_label="Date", sep='\t', float_format='%.2f', lineterminator='\n', encoding='utf-8')
        msgBox.setText("'wb_daily.txt' file is exported to your 'exported_files' folder!")
    elif self.dlg.radioButton_std_month.isChecked():
        dfm = data.resample('ME').mean()
        dff = dfm[ssdate:sedate]
        with open(os.path.join(outfolder, "wb_monthly_average.txt"), 'w') as f:
            f.write("# Monthly average water balance [mm] - QSWATMOD2 Plugin " + version + time + "\n")
            dff.to_csv(f, index_label="Date", sep='\t', float_format='%.2f', lineterminator='\n', encoding='utf-8')
        msgBox.setText("'wb_monthly_average.txt' file is exported to your 'exported_files' folder!")
    elif self.dlg.radioButton_std_year.isChecked():
        dfa = data.resample('A').mean()
        dff = dfa[ssdate:sedate]
        with open(os.path.join(outfolder, "wb_annual_average.txt"), 'w') as f:
            f.write("# Annual average water balance [mm] - QSWATMOD2 Plugin " + version + time + "\n")
            dff.to_csv(f, index_label="Date", sep='\t', float_format='%.2f', lineterminator='\n', encoding='utf-8')
        msgBox.setText("'wb_annual_average.txt' file is exported to your 'exported_files' folder!")
    msgBox.exec_()


def export_wb_m(self):
    QSWATMOD_path_dict = self.dirs_and_paths()
    stdate, eddate, stdate_warmup, eddate_warmup = self.define_sim_period()
    wd = QSWATMOD_path_dict['SMfolder']
    outfolder = QSWATMOD_path_dict['exported_files']
    startDate = stdate_warmup
    with open(os.path.join(wd, "output.std"), "r") as infile:
        lines = []
        y = ("TIME", "UNIT", "SWAT", "(mm)")
        for line in infile:
            data = line.strip()
            if len(data) > 100 and not data.startswith(y):  # 1st filter
                lines.append(line)
    eYear = self.dlg.lineEdit_end_y.text()
    dates = []
    for line in lines:  # 2nd filter
        try:
            date = line.split()[0]
            if (date == eYear):  # Stop looping
                break
            elif(len(str(date)) == 4):  # filter years
                continue
            else:
                dates.append(line)
        except:
            pass
    date_f, prec, surq, latq, gwq, swgw, perco, tile, sw, gw = [], [], [], [], [], [], [], [], [], []
    for i in range(len(dates)):
        date_f.append(int(dates[i].split()[0]))
        prec.append(float(dates[i].split()[1]))
        surq.append(float(dates[i].split()[2]))
        latq.append(float(dates[i].split()[3]))
        gwq.append(float(dates[i].split()[4]))
        swgw.append(float(dates[i].split()[5]))
        # perco.append(float(dates[i].split()[6]))
        perco.append(float(dates[i].split()[7]))  # SM3 uses reach !SP
        tile.append(float(dates[i].split()[8]))  # not use it for now
        sw.append(float(dates[i].split()[10]))
        gw.append(float(dates[i].split()[11]))
    names = ["prec", "surq", "latq", "gwq", "swgw", "perco", "tile", "sw", "gw"]
    data = pd.DataFrame(
        np.column_stack([prec, surq, latq, gwq, swgw, perco, tile, sw, gw]),
        columns=names)
    data.index = pd.date_range(startDate, periods=len(data), freq='ME')
    ssdate = self.dlg.comboBox_std_sdate.currentText()
    sedate = self.dlg.comboBox_std_edate.currentText()
    # Add info
    from datetime import datetime
    version = "version 2.10.1."
    time = datetime.now().strftime('- %m/%d/%y %H:%M:%S -')
    msgBox = QMessageBox()
    msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
    msgBox.setWindowTitle("Exported!")
    if self.dlg.radioButton_std_month.isChecked():
        dff = data[ssdate:sedate]
        with open(os.path.join(outfolder, "wb_monthly_total.txt"), 'w') as f:
            f.write("# Monthly total water balance [mm] - QSWATMOD2 Plugin " + version + time + "\n")
            dff.to_csv(f, index_label="Date", sep='\t', float_format='%.2f', lineterminator='\n', encoding='utf-8')
        msgBox.setText("'wb_monthly_total.txt' file is exported to your 'exported_files' folder!")
    elif self.dlg.radioButton_std_year.isChecked():
        dfa = data.resample('A').mean()
        dff = dfa[ssdate:sedate]
        with open(os.path.join(outfolder, "wb_annual_avg_monthly_total.txt"), 'w') as f:
            f.write("# Annual average monthly total water balance [mm] - QSWATMOD2 Plugin " + version + time + "\n")
            dff.to_csv(f, index_label="Date", sep='\t', float_format='%.2f', lineterminator='\n', encoding='utf-8')
        msgBox.setText("'wb_annual_avg_monthly_total.txt' file is exported to your 'exported_files' folder!")
    msgBox.exec_()

    
def export_wb_a(self):
    QSWATMOD_path_dict = self.dirs_and_paths()
    stdate, eddate, stdate_warmup, eddate_warmup = self.define_sim_period()
    wd = QSWATMOD_path_dict['SMfolder']
    outfolder = QSWATMOD_path_dict['exported_files']
    startDate = stdate_warmup
    with open(os.path.join(wd, "output.std"), "r") as infile:
        lines = []
        y = ("TIME", "UNIT", "SWAT", "(mm)")
        for line in infile:
            data = line.strip()
            if len(data) > 100 and not data.startswith(y):  # 1st filter
                lines.append(line)
    dates = []
    bword = "HRU"
    for line in lines:
        try:
            date = line.split()[0]
            if (date == bword):  # Stop looping
                break
            else:
                dates.append(line)
        except:
            pass
    date_f, prec, surq, latq, gwq, swgw, perco, tile, sw, gw = [], [], [], [], [], [], [], [], [], []
    for i in range(len(dates)): # 3rd filter and obtain necessary data
        date_f.append(int(dates[i].split()[0]))
        prec.append(float(dates[i].split()[1]))
        surq.append(float(dates[i].split()[2]))
        latq.append(float(dates[i].split()[3]))
        gwq.append(float(dates[i].split()[4]))
        swgw.append(float(dates[i].split()[5]))
        # perco.append(float(dates[i].split()[6]))
        perco.append(float(dates[i].split()[7]))  # SM3 uses reach !SP
        tile.append(float(dates[i].split()[8]))  # not use it for now
        sw.append(float(dates[i].split()[10]))
        gw.append(float(dates[i].split()[11]))
    names = ["prec", "surq", "latq", "gwq", "swgw", "perco", "tile", "sw", "gw"]
    data = pd.DataFrame(
        np.column_stack([prec, surq, latq, gwq, swgw, perco, tile, sw, gw]),
        columns=names)
    data.index = pd.date_range(startDate, periods=len(data), freq="A")
    ssdate = self.dlg.comboBox_std_sdate.currentText()
    sedate = self.dlg.comboBox_std_edate.currentText()
    dff = data[ssdate:sedate]
    # Add info
    from datetime import datetime
    version = "version 2.10.1."
    time = datetime.now().strftime('- %m/%d/%y %H:%M:%S -')
    with open(os.path.join(outfolder, "wb_annual_total.txt"), 'w') as f:
        f.write("# Annual total water balance [mm] - QSWATMOD2 Plugin " + version + time + "\n")
        dff.to_csv(f, index_label="Date", sep='\t', float_format='%.2f', lineterminator='\n', encoding='utf-8')
    msgBox = QMessageBox()
    msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
    msgBox.setWindowTitle("Exported!")
    msgBox.setText("'wb_annual_total.txt' file is exported to your 'exported_files' folder!")
    msgBox.exec_()
