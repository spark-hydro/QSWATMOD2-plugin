# -*- coding: utf-8 -*-
from builtins import zip
from builtins import str
from builtins import range
from qgis.PyQt.QtCore import QVariant
from qgis.core import (
                        QgsProject, QgsLayerTreeLayer, QgsVectorFileWriter, QgsVectorLayer,
                        QgsField)
from qgis.PyQt import QtCore, QtGui, QtSql
from qgis.PyQt.QtCore import QCoreApplication
import datetime
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
import os
import processing
from PyQt5.QtWidgets import QMessageBox
from QSWATMOD2.modules import shapefile_sm
from matplotlib.colors import Normalize


# try:
#     import deps.pandas as pd
# except AttributeError:
#     msgBox = QMessageBox()
#     msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
#     msgBox.setWindowTitle("QSWATMOD2")
#     msgBox.setText("Please, restart QGIS to initialize QSWATMOD2 properly.")
#     msgBox.exec_()


def read_mf_gwsw_dates(self):
    if self.dlg.groupBox_gwsw.isChecked():
        QSWATMOD_path_dict = self.dirs_and_paths()
        stdate, eddate, stdate_warmup, eddate_warmup = self.define_sim_period()
        wd = QSWATMOD_path_dict['SMfolder']
        startDate = stdate.strftime("%m-%d-%Y")
        y = ("for", "Positive:", "Negative:", "Daily", "Monthly", "Annual", "Layer,") # Remove unnecssary lines
        if self.dlg.radioButton_gwsw_day.isChecked():
            filename = "swatmf_out_MF_gwsw"
            # Open "swatmf_out_MF_gwsw" file

            with open(os.path.join(wd, filename), "r") as f:
                data = [x.strip() for x in f if x.strip() and not x.strip().startswith(y)] # Remove blank lines
            date = [x.strip().split() for x in data if x.strip().startswith("Day:")] # Collect only lines with dates
            onlyDate = [x[1] for x in date] # Only date
            # data1 = [x.split() for x in data] # make each line a list
            sdate = datetime.datetime.strptime(startDate, "%m-%d-%Y") # Change startDate format
            dateList = [(sdate + datetime.timedelta(days = int(i)-1)).strftime("%m-%d-%Y") for i in onlyDate]
            self.dlg.comboBox_gwsw_dates.clear()
            self.dlg.comboBox_gwsw_dates.addItems(dateList)
            self.dlg.comboBox_gwsw_sdate.clear()
            self.dlg.comboBox_gwsw_sdate.addItems(dateList)
            self.dlg.comboBox_gwsw_edate.clear()
            self.dlg.comboBox_gwsw_edate.addItems(dateList)
            self.dlg.comboBox_gwsw_edate.setCurrentIndex(len(dateList)-1)
        elif self.dlg.radioButton_gwsw_month.isChecked():
            filename = "swatmf_out_MF_gwsw_monthly"
            with open(os.path.join(wd, filename), "r") as f:
                data = [x.strip() for x in f if x.strip() and not x.strip().startswith(y)]  
            date = [x.strip().split() for x in data if x.strip().startswith("month:")]
            data1 = [x.split() for x in data]
            onlyDate = [x[1] for x in date] 
            #dateList = [(sdate + datetime.timedelta(months = int(i)-1)).strftime("%m-%Y") for i in onlyDate]
            dateList = pd.date_range(startDate, periods=len(onlyDate), freq='M').strftime("%b-%Y").tolist()
            self.dlg.comboBox_gwsw_dates.clear()
            self.dlg.comboBox_gwsw_dates.addItems(dateList)
            self.dlg.comboBox_gwsw_sdate.clear()
            self.dlg.comboBox_gwsw_sdate.addItems(dateList)
            self.dlg.comboBox_gwsw_edate.clear()
            self.dlg.comboBox_gwsw_edate.addItems(dateList)
            self.dlg.comboBox_gwsw_edate.setCurrentIndex(len(dateList)-1)
        elif self.dlg.radioButton_gwsw_year.isChecked():
            filename = "swatmf_out_MF_gwsw_yearly"
            with open(os.path.join(wd, filename), "r") as f:
                data = [x.strip() for x in f if x.strip() and not x.strip().startswith(y)]  
            date = [x.strip().split() for x in data if x.strip().startswith("year:")]
            data1 = [x.split() for x in data]
            onlyDate = [x[1] for x in date] 
            #dateList = [(sdate + datetime.timedelta(months = int(i)-1)).strftime("%m-%Y") for i in onlyDate]
            dateList = pd.date_range(startDate, periods = len(onlyDate), freq='A').strftime("%Y").tolist()
            self.dlg.comboBox_gwsw_dates.clear()
            self.dlg.comboBox_gwsw_dates.addItems(dateList)
            self.dlg.comboBox_gwsw_sdate.clear()
            self.dlg.comboBox_gwsw_sdate.addItems(dateList)
            self.dlg.comboBox_gwsw_edate.clear()
            self.dlg.comboBox_gwsw_edate.addItems(dateList)
            self.dlg.comboBox_gwsw_edate.setCurrentIndex(len(dateList)-1)
    else:
        self.dlg.comboBox_gwsw_dates.clear()


def readExtentSub(self):
    self.layer = QgsProject.instance().mapLayersByName("sub (SWAT)")[0]
    # get extent
    ext = self.layer.extent()
    ymin = ext.yMinimum()
    ymax = ext.yMaximum()
    self.dlg.lineEdit_gwsw_y_min.setText(str(ymin))
    self.dlg.lineEdit_gwsw_y_max.setText(str(ymax))


def dissolvedSub(self):
    QSWATMOD_path_dict = self.dirs_and_paths()
    if not any(lyr.name() == ("mf_boundary (MODFLOW)") for lyr in list(QgsProject.instance().mapLayers().values())):
        input1 = QgsProject.instance().mapLayersByName("sub (SWAT)")[0]
        name = "mf_boundary"
        name_ext = "mf_boundary.shp"
        output_dir = QSWATMOD_path_dict['org_shps']
        # output_file = os.path.normpath(os.path.join(output_dir, name_ext))
        mf_boundary = os.path.join(output_dir, name_ext)
        params = {
            'INPUT': input1,
            'OUTPUT':mf_boundary
        }
        processing.run("native:dissolve", params)

        # defining the outputfile to be loaded into the canvas
        layer = QgsVectorLayer(mf_boundary, '{0} ({1})'.format("mf_boundary","MODFLOW"), 'ogr')

        # Put in the group
        root = QgsProject.instance().layerTreeRoot()
        mf_group = root.findGroup("MODFLOW")    
        QgsProject.instance().addMapLayer(layer, False)
        mf_group.insertChildNode(0, QgsLayerTreeLayer(layer))


def create_sm_riv(self):
    QSWATMOD_path_dict = self.dirs_and_paths()
    if not any(lyr.name() == ("sm_riv") for lyr in list(QgsProject.instance().mapLayers().values())):
        # Create swatmf_results tree inside 
        root = QgsProject.instance().layerTreeRoot()
        if root.findGroup("swatmf_results"):
            sm_results_group = root.findGroup("swatmf_results")
        else:
            sm_results_group = root.insertGroup(0, "swatmf_results")

        input1 = QgsProject.instance().mapLayersByName("mf_grid (MODFLOW)")[0]
        input2 = QgsProject.instance().mapLayersByName("river_grid (SWAT-MODFLOW)")[0]
        feats_mf_grid = input1.getFeatures()
        feats = input2.getFeatures()
        grid_id = set([f.attribute('grid_id') for f in feats])
        #hm = set(grid_id)

        riv_mat = []
        for f in feats_mf_grid:
            grid_no = f.attribute("grid_id")
            for i in grid_id:
                if grid_no == i:
                    riv_mat.append(f.id())

        input1.selectByIds(riv_mat)
        name_ext = "sm_riv.shp"
        output_dir = QSWATMOD_path_dict['SMshps']

        # Save just the selected features of the target layer
        sm_riv_shapefile = os.path.join(output_dir, name_ext)
        # Extract selected features
        processing.run(
            "native:saveselectedfeatures",
            {'INPUT': input1, 'OUTPUT':sm_riv_shapefile}
        )
        
        # Deselect the features
        input1.removeSelection()
        layer = QgsVectorLayer(sm_riv_shapefile, '{0}'.format("sm_riv"), 'ogr')

        # Put in the group
        root = QgsProject.instance().layerTreeRoot()
        sm_results_group = root.findGroup("swatmf_results")  
        QgsProject.instance().addMapLayer(layer, False)
        sm_results_group.insertChildNode(0, QgsLayerTreeLayer(layer))
        layer = QgsProject.instance().addMapLayer(layer)


def plot_gwsw_org(self):
    import scipy.stats as ss
    import operator
    import numpy as np

    QSWATMOD_path_dict = self.dirs_and_paths()
    stdate, eddate, stdate_warmup, eddate_warmup = self.define_sim_period()
    wd = QSWATMOD_path_dict['SMfolder']
    startDate = stdate.strftime("%m-%d-%Y")
    # Open "swatmf_out_MF_gwsw" file
    y = ("for", "Positive:", "Negative:", "Daily", "Monthly", "Annual", "Layer,")  # Remove unnecssary lines
    selectedDate = self.dlg.comboBox_gwsw_dates.currentText()

    if self.dlg.radioButton_gwsw_day.isChecked():
        filename = "swatmf_out_MF_gwsw"
        with open(os.path.join(wd, filename), "r") as f:
            data = [x.strip() for x in f if x.strip() and not x.strip().startswith(y)] # Remove blank lines
        date = [x.strip().split() for x in data if x.strip().startswith("Day:")] # Collect only lines with dates
        onlyDate = [x[1] for x in date]  # Only date
        data1 = [x.split() for x in data]  # make each line a list
        sdate = datetime.datetime.strptime(startDate, "%m-%d-%Y") # Change startDate format
        dateList = [(sdate + datetime.timedelta(days=int(i)-1)).strftime("%m-%d-%Y") for i in onlyDate]

        # Reverse step
        dateIdx = dateList.index(selectedDate)
        #only
        onlyDate_lookup = onlyDate[dateIdx]
        for num, line in enumerate(data1, 1):
            if line[0] == "Day:" in line and line[1] == onlyDate_lookup in line:
                ii = num # Starting line
    elif self.dlg.radioButton_gwsw_month.isChecked():
        filename = "swatmf_out_MF_gwsw_monthly"
        with open(os.path.join(wd, filename), "r") as f:
            data = [x.strip() for x in f if x.strip() and not x.strip().startswith(y)]  
        date = [x.strip().split() for x in data if x.strip().startswith("month:")]
        data1 = [x.split() for x in data]
        onlyDate = [x[1] for x in date] 
        dateList = pd.date_range(startDate, periods = len(onlyDate), freq = 'M').strftime("%b-%Y").tolist()
        # Reverse step
        dateIdx = dateList.index(selectedDate)
        # Find year 
        dt = datetime.datetime.strptime(selectedDate, "%b-%Y")
        year = dt.year
        # only
        onlyDate_lookup = onlyDate[dateIdx]
        for num, line in enumerate(data1, 1):
            if ((line[0] == "month:" in line) and (line[1] == onlyDate_lookup in line) and (line[3] == str(year) in line)):
                ii = num # Starting line
    elif self.dlg.radioButton_gwsw_year.isChecked():
        filename = "swatmf_out_MF_gwsw_yearly"
        with open(os.path.join(wd, filename), "r") as f:
            data = [x.strip() for x in f if x.strip() and not x.strip().startswith(y)]  
        date = [x.strip().split() for x in data if x.strip().startswith("year:")]
        data1 = [x.split() for x in data]
        onlyDate = [x[1] for x in date] 
        dateList = pd.date_range(startDate, periods=len(onlyDate), freq='A').strftime("%Y").tolist()

        # Reverse step
        dateIdx = dateList.index(selectedDate)
        #only
        onlyDate_lookup = onlyDate[dateIdx]
        for num, line in enumerate(data1, 1):
            if line[0] == "year:" in line and line[1] == onlyDate_lookup in line:
                ii = num # Starting line
    else:
        msgBox = QMessageBox()
        msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
        msgBox.setWindowTitle("Oops!")
        msgBox.setText("Please, select one of the time options!")
        msgBox.exec_()

    #### Layer
    orgGIS = QSWATMOD_path_dict['org_shps']
    smGIS = QSWATMOD_path_dict['SMshps']
    river = shapefile_sm.Reader(os.path.join(orgGIS, "riv_SM.shp" )) # River
    sub = shapefile_sm.Reader(os.path.join(orgGIS, "mf_boundary.shp" )) # dissolved sub
    sm_riv = shapefile_sm.Reader(os.path.join(smGIS, "sm_riv.shp"))

    # ------------------------------------------------------------------------------
    sr = sm_riv.shapes() # property of sm_river
    coords = [sr[i].bbox for i in range(len(sr))] # get coordinates for each river cell
    width = abs(coords[0][2] - coords[0][0]) # get width for bar plot
    nSM_riv = len(sr) # Get number of river cells
    mf_gwsws = [data1[i][3] for i in range(ii, ii + nSM_riv)] # get gwsw data ranging from ii to 

    # Sort coordinates by row
    c_sorted = sorted(coords, key=operator.itemgetter(0))
    c_sorted = sorted(c_sorted, key=operator.itemgetter(1), reverse=True)

    # Put coordinates and gwsw data in Dataframe together
    f_c = pd.DataFrame(c_sorted, columns=['x_min', 'y_min', 'x_max', 'y_max'])
    f_c['gwsw'] = mf_gwsws
    f_c['gwsw'] = f_c['gwsw'].astype('float') 

    #### ==========================================================================
    gwsw_f = f_c['gwsw'].astype('float') 
    # gwsw_f = f_c['gwsw'].values

    # gwsw_ff = gwsw_f.astype('int')
    ranks = ss.rankdata(gwsw_f, method = 'dense')

    # colored bar with their ranks
    if self.dlg.checkBox_color_reverse.isChecked():
        color = self.dlg.comboBox_colormaps.currentText() + '_r'
    else:
        color = self.dlg.comboBox_colormaps.currentText()
    colormap = plt.cm.get_cmap(color)
    # colors = plt.cm.autumn(gwsw_f/gwsw_f.max())

    colors = [colormap(i) for i in np.linspace(0, 10, len(gwsw_f))] # Okay, 10 is weird.
    recols = [colors[(int(rank)-1)] for rank in ranks]

    if self.dlg.checkBox_darktheme.isChecked():
        plt.style.use('dark_background')
    else:
        plt.style.use('default')    

    fig, ax = plt.subplots()
    fig.subplots_adjust(left = 0.1, right = 0.9, top = 0.9, bottom = 0.2, hspace=0.2, wspace=0.1)
    ax1 = fig.add_subplot(111, frameon=False)
    ax1.tick_params(labelcolor='none', top=False, bottom=False, left=False, right=False)

    # NOTE: temp: gives max and min for a paper
    ax1 = plt.imshow(np.array([[-450, 450]]), cmap = plt.cm.get_cmap(color))
    # ax1 = plt.imshow(np.array([[gwsw_f.max(), gwsw_f.min()]]), cmap = plt.cm.get_cmap(color))
    ax1.set_visible(False)
    ax.tick_params(axis='both', labelsize=6)

    ### Get extent
    self.layer = QgsProject.instance().mapLayersByName("sub (SWAT)")[0]
    extent = self.layer.extent()
    x_min = extent.xMinimum()
    x_max = extent.xMaximum()
    y_min = extent.yMinimum()
    y_max = extent.yMaximum()

    ### User inputs ===========================================================================
    widthExg = float(self.dlg.doubleSpinBox_w_exag.value())
    verExg = float(self.dlg.doubleSpinBox_h_exag.value())

    # Title
    if self.dlg.checkBox_gwsw_title.isChecked():
        ax.set_title('- {} -'.format(selectedDate), loc = 'left', fontsize = 8, fontweight = 'bold' )

    # frame
    if self.dlg.checkBox_gwsw_frame.isChecked():
        ax.axis('on') # -> takes ticks too.
    else:
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        # ax.axis('off')

    # coordinates
    if not self.dlg.checkBox_gwsw_coords.isChecked():
        ax.tick_params(labelcolor='none', top=False, bottom=False, left=False, right=False)        
    else:
        # ax.tick_params(top='off', bottom='on', left='on', right='off')
        ax.tick_params(top=False, bottom=True, left=True, right=False)
    # colorbar
    if self.dlg.checkBox_gwsw_colorbar.isChecked():
        cbaxes = fig.add_axes([0.3, 0.08, 0.4, 0.02])
        cb = plt.colorbar(cax=cbaxes, orientation="horizontal")
        cb.ax.tick_params(labelsize= 7)
        # cb.ax.invert_yaxis()
        cb.ax.set_title(' - To Stream   |   + To Aquifer\n[$m^3/day$]', fontsize=8,
                        # position=(1.05, 0.17),
                        horizontalalignment='center',
                        # y = 1.05,
                        # fontweight='semibold',
                        # transform=axes[0,0].transAxes
                        )
        
    if self.dlg.checkBox_gwsw_river.isChecked():
        for rv in (river.shapeRecords()):
            rx = [i[0] for i in rv.shape.points[:]]
            ry = [i[1] for i in rv.shape.points[:]]
            ax.plot(rx, ry, lw = 1, c = 'b')
    # Boundary
    if self.dlg.checkBox_gwsw_boundary.isChecked():     
        for sb in (sub.shapeRecords()):
            sx = [i[0] for i in sb.shape.points[:]]
            sy = [i[1] for i in sb.shape.points[:]]
            ax.plot(sx, sy, lw = 0.5, c = 'grey')

    # ----------------------------------------------------------------------------------------
    if self.dlg.checkBox_gwsw_yaxes.isChecked():
        y_axis_min = float(self.dlg.lineEdit_gwsw_y_min.text())
        y_axis_max = float(self.dlg.lineEdit_gwsw_y_max.text())
        ax.set_ylim([y_axis_min, y_axis_max])
    # set size!
    ax.imshow(np.random.random((10, 10)), extent=[x_min, x_max, y_min, y_max], alpha=0)
    ax.bar(f_c.x_min, (gwsw_f*-1*verExg),
           bottom=f_c.y_min,
           width=width * widthExg, align='center',
           alpha=0.7, color=recols, zorder=3)
    plt.show()

def plot_gwsw(self):
    import scipy.stats as ss
    import operator
    import numpy as np

    QSWATMOD_path_dict = self.dirs_and_paths()
    stdate, eddate, stdate_warmup, eddate_warmup = self.define_sim_period()
    wd = QSWATMOD_path_dict['SMfolder']
    startDate = stdate.strftime("%m-%d-%Y")
    # Open "amf_MF_gwsw.out" file
    y = ("for", "Positive:", "Negative:", "Daily", "Monthly", "Annual", "Layer,")  # Remove unnecssary lines
    selectedDate = self.dlg.comboBox_gwsw_dates.currentText()

    if self.dlg.radioButton_gwsw_day.isChecked():
        filename = "swatmf_out_MF_gwsw"
        with open(os.path.join(wd, filename), "r") as f:
            data = [x.strip() for x in f if x.strip() and not x.strip().startswith(y)] # Remove blank lines
        date = [x.strip().split() for x in data if x.strip().startswith("Day:")] # Collect only lines with dates
        onlyDate = [x[1] for x in date]  # Only date
        data1 = [x.split() for x in data]  # make each line a list
        sdate = datetime.datetime.strptime(startDate, "%m-%d-%Y") # Change startDate format
        dateList = [(sdate + datetime.timedelta(days=int(i)-1)).strftime("%m-%d-%Y") for i in onlyDate]

        # Reverse step
        dateIdx = dateList.index(selectedDate)
        #only
        onlyDate_lookup = onlyDate[dateIdx]
        for num, line in enumerate(data1, 1):
            if line[0] == "Day:" in line and line[1] == onlyDate_lookup in line:
                ii = num # Starting line
    elif self.dlg.radioButton_gwsw_month.isChecked():
        filename = "swatmf_out_MF_gwsw_monthly"
        with open(os.path.join(wd, filename), "r") as f:
            data = [x.strip() for x in f if x.strip() and not x.strip().startswith(y)]  
        date = [x.strip().split() for x in data if x.strip().startswith("month:")]
        data1 = [x.split() for x in data]
        onlyDate = [x[1] for x in date] 
        dateList = pd.date_range(startDate, periods=len(onlyDate), freq='M').strftime("%b-%Y").tolist()
        # Reverse step
        dateIdx = dateList.index(selectedDate)
        # Find year 
        dt = datetime.datetime.strptime(selectedDate, "%b-%Y")
        year = dt.year
        # only
        onlyDate_lookup = onlyDate[dateIdx]
        for num, line in enumerate(data1, 1):
            if ((line[0] == "month:" in line) and (line[1] == onlyDate_lookup in line) and (line[3] == str(year) in line)):
                ii = num # Starting line
    elif self.dlg.radioButton_gwsw_year.isChecked():
        filename = "swatmf_out_MF_gwsw_yearly"
        with open(os.path.join(wd, filename), "r") as f:
            data = [x.strip() for x in f if x.strip() and not x.strip().startswith(y)]  
        date = [x.strip().split() for x in data if x.strip().startswith("year:")]
        data1 = [x.split() for x in data]
        onlyDate = [x[1] for x in date] 
        dateList = pd.date_range(startDate, periods=len(onlyDate), freq='A').strftime("%Y").tolist()

        # Reverse step
        dateIdx = dateList.index(selectedDate)
        #only
        onlyDate_lookup = onlyDate[dateIdx]
        for num, line in enumerate(data1, 1):
            if line[0] == "year:" in line and line[1] == onlyDate_lookup in line:
                ii = num # Starting line
    else:
        msgBox = QMessageBox()
        msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
        msgBox.setWindowTitle("Oops!")
        msgBox.setText("Please, select one of the time options!")
        msgBox.exec_()

    #### Layer
    orgGIS = QSWATMOD_path_dict['org_shps']
    smGIS = QSWATMOD_path_dict['SMshps']
    river = shapefile_sm.Reader(os.path.join(orgGIS, "riv_SM.shp" )) # River
    sub = shapefile_sm.Reader(os.path.join(orgGIS, "mf_boundary.shp" )) # dissolved sub
    sm_riv = shapefile_sm.Reader(os.path.join(smGIS, "sm_riv.shp"))

    # ------------------------------------------------------------------------------
    sr = sm_riv.shapes() # property of sm_river
    coords = [sr[i].bbox for i in range(len(sr))] # get coordinates for each river cell
    width = abs(coords[0][2] - coords[0][0]) # get width for bar plot
    nSM_riv = len(sr) # Get number of river cells
    mf_gwsws = [data1[i][3] for i in range(ii, ii + nSM_riv)] # get gwsw data ranging from ii to 

    # Sort coordinates by row
    # c_sorted = sorted(coords, key=operator.itemgetter(1), reverse=True)
    # c_sorted = sorted(c_sorted, key=operator.itemgetter(0))

    c_sorted = sorted(coords, key=operator.itemgetter(0))
    c_sorted = sorted(c_sorted, key=operator.itemgetter(1), reverse=True)



    # Put coordinates and gwsw data in Dataframe together
    f_c = pd.DataFrame(c_sorted, columns=['x_min', 'y_min', 'x_max', 'y_max'])
    f_c['gwsw'] = mf_gwsws
    f_c['gwsw'] = f_c['gwsw'].astype('float') 

    #### ==========================================================================
    gwsw_f = f_c['gwsw'].astype('float') 
    # gwsw_f = f_c['gwsw'].values

    # gwsw_ff = gwsw_f.astype('int')
    ranks = ss.rankdata(gwsw_f, method='dense')

    # colored bar with their ranks
    if self.dlg.checkBox_color_reverse.isChecked():
        color = self.dlg.comboBox_colormaps.currentText() + '_r'
    else:
        color = self.dlg.comboBox_colormaps.currentText()
    colormap = plt.cm.get_cmap(color)


    if self.dlg.checkBox_darktheme.isChecked():
        plt.style.use('dark_background')
    else:
        plt.style.use('default')
    
    fig, ax = plt.subplots()
    fig.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.2, hspace=0.2, wspace=0.1)
    ax1 = fig.add_subplot(111, frameon=False)
    ax1.tick_params(labelcolor='none', top=False, bottom=False, left=False, right=False)
    
    # NOTE: temp: gives max and min for a paper
    ax1 = plt.imshow(np.array([[-1020, 1020]]), cmap = plt.cm.get_cmap(color))
    # my_norm = Normalize(vmin=-1020, vmax=15)
    # ax1 = plt.imshow(np.array([[gwsw_f.max(), gwsw_f.min()]]), cmap = plt.cm.get_cmap(color))
    ax1.set_visible(False)
    ax.tick_params(axis='both', labelsize=6)

    ### Get extent
    self.layer = QgsProject.instance().mapLayersByName("sub (SWAT)")[0]
    extent = self.layer.extent()
    x_min = extent.xMinimum()
    x_max = extent.xMaximum()
    y_min = extent.yMinimum()
    y_max = extent.yMaximum()

    ### User inputs ===========================================================================
    widthExg = float(self.dlg.doubleSpinBox_w_exag.value())
    verExg = float(self.dlg.doubleSpinBox_h_exag.value())*0.01
    # verExg = float(0.01)

    # Title
    if self.dlg.checkBox_gwsw_title.isChecked():
        ax.set_title('- {} -'.format(selectedDate), loc = 'left', fontsize = 8, fontweight = 'bold' )

    # frame
    if self.dlg.checkBox_gwsw_frame.isChecked():
        ax.axis('on') # -> takes ticks too.
    else:
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        # ax.axis('off')

    # coordinates
    if not self.dlg.checkBox_gwsw_coords.isChecked():
        ax.tick_params(labelcolor='none', top=False, bottom=False, left=False, right=False)        
    else:
        # ax.tick_params(top='off', bottom='on', left='on', right='off')
        ax.tick_params(top=False, bottom=True, left=True, right=False)
    # colorbar
    if self.dlg.checkBox_gwsw_colorbar.isChecked():
        cbaxes = fig.add_axes([0.3, 0.05, 0.4, 0.02])
        cb = plt.colorbar(cax=cbaxes, orientation="horizontal")
        cb.ax.tick_params(labelsize=7)
        # cb.ax.invert_yaxis()
        cb.ax.set_title(' - To Stream   |   + To Aquifer\n[$m^3/day$]', fontsize=8,
                        # position=(1.05, 0.17),
                        horizontalalignment='center',
                        # y = 1.05,
                        # fontweight='semibold',
                        # transform=axes[0,0].transAxes
                        )
    # River
    if self.dlg.checkBox_gwsw_river.isChecked():
        for rv in (river.shapeRecords()):
            rx = [i[0] for i in rv.shape.points[:]]
            ry = [i[1] for i in rv.shape.points[:]]
            ax.plot(rx, ry, lw=1, c='b', alpha=0.5)
    # Boundary
    if self.dlg.checkBox_gwsw_boundary.isChecked():     
        for sb in (sub.shapeRecords()):
            sx = [i[0] for i in sb.shape.points[:]]
            sy = [i[1] for i in sb.shape.points[:]]
            ax.plot(sx, sy, lw = 0.5, c = 'grey')

    # ----------------------------------------------------------------------------------------
    if self.dlg.checkBox_gwsw_yaxes.isChecked():
        y_axis_min = float(self.dlg.lineEdit_gwsw_y_min.text())
        y_axis_max = float(self.dlg.lineEdit_gwsw_y_max.text())
        ax.set_ylim([y_axis_min, y_axis_max])
    # set size!
    ax.imshow(np.random.random((10, 10)), extent=[x_min, x_max, y_min, y_max], alpha=0)

    # NOTE: TEMP
    # dicharge = f_c[f_c['gwsw'] < 0]
    # seepage = f_c[f_c['gwsw'] > 0]


    # # recols = [colors[(int(rank)-1)] for rank in ranks]
    # ax.bar(
    #         dicharge.x_min, (dicharge.gwsw.astype('float')*-1*verExg),
    #         bottom=dicharge.y_min,
    #         width=width * widthExg, align='center',
    #         alpha=0.7, color='red', zorder=3,)
    # ax.bar(
    #         seepage.x_min, (seepage.gwsw.astype('float')*-1*verExg),
    #         bottom=seepage.y_min,
    #         width=width * widthExg, align='center',
    #         alpha=0.7, color='b', zorder=3,)
    # get normalize function (takes data in range [vmin, vmax] -> [0, 1])
    # my_norm = Normalize(vmin=gwsw_f.min(), vmax=gwsw_f.max())
    my_norm = Normalize(vmin=-1020, vmax=1020)
    ax.bar(
            f_c.x_min, (gwsw_f*-1*verExg),
            bottom=f_c.y_min,
            width=width * widthExg, align='center',
            alpha=0.7, color=colormap(my_norm(np.array(gwsw_f))), zorder=3,)    

    # NOTE:
    plt.savefig(os.path.join(wd, 'fig_{}.png'.format(selectedDate)), transparent=True, dpi=300)
    plt.show()







def plot_gwsw_ani (self):
    import scipy.stats as ss
    import operator
    import numpy as np

    self.dlg.progressBar_gwsw.setValue(0)
    QSWATMOD_path_dict = self.dirs_and_paths()
    stdate, eddate, stdate_warmup, eddate_warmup = self.define_sim_period()

    # Assign Paths
    wd = QSWATMOD_path_dict['SMfolder']
    orgGIS = QSWATMOD_path_dict['org_shps']
    smGIS = QSWATMOD_path_dict['SMshps']
    exported = QSWATMOD_path_dict['exported_files']
    river = shapefile_sm.Reader(os.path.join(orgGIS, "riv_SM.shp" )) # River
    sub = shapefile_sm.Reader(os.path.join(orgGIS, "mf_boundary.shp" )) # dissolved sub
    sm_riv = shapefile_sm.Reader(os.path.join(smGIS, "sm_riv.shp"))

    # Define inputs
    sr = sm_riv.shapes() # property of sm_river
    coords = [sr[i].bbox for i in range(len(sr))] # get coordinates for each river cell
    c_sorted = sorted(coords, key=operator.itemgetter(0))
    f_c = pd.DataFrame(c_sorted, columns=['x_min', 'y_min', 'x_max', 'y_max'])
    width = abs(coords[0][2] - coords[0][0]) # get width for bar plot
    nSM_riv = len(sr) # Get number of river cells
    startDate = stdate.strftime("%m-%d-%Y")

    # Open "swatmf_out_MF_gwsw" file
    if self.dlg.radioButton_gwsw_day.isChecked():
        filename = "swatmf_out_MF_gwsw"
        y = ("for", "Positive:", "Negative:", "Daily", "Monthly", "Annual", "Layer,")  # Remove unnecssary lines
        with open(os.path.join(wd, filename), "r") as f:
            data = [x.strip() for x in f if x.strip() and not x.strip().startswith(y)] # Remove blank lines
        date = [x.strip().split() for x in data if x.strip().startswith("Day:")] # Collect only lines with dates
        onlyDate = [x[1] for x in date]  # Only date
        sdate = datetime.datetime.strptime(startDate, "%m-%d-%Y") # Change startDate format
        dateList = [(sdate + datetime.timedelta(days=int(i)-1)).strftime("%m-%d-%Y") for i in onlyDate]

        data = np.loadtxt(
                            os.path.join(wd, filename),
                            skiprows=5,
                            comments=["Day:", "Layer"])
        df = np.reshape(data[:, 3], (int(len(data)/nSM_riv), nSM_riv))
        df2 = pd.DataFrame(df)
        df2.index = dateList

        scdate = self.dlg.comboBox_gwsw_sdate.currentText()
        ecdate = self.dlg.comboBox_gwsw_edate.currentText()
        df3 = df2[scdate:ecdate]
    elif self.dlg.radioButton_gwsw_month.isChecked():
        filename = "swatmf_out_MF_gwsw_monthly"
        data = np.loadtxt(
                        os.path.join(wd, filename),
                        skiprows=2,
                        comments=["month:", "Layer"])

        df = np.reshape(data[:, 3], (int(len(data)/nSM_riv), nSM_riv))
        df2 = pd.DataFrame(df)
        df2.index = pd.date_range(startDate, periods=len(df[:,0]), freq='M').strftime("%b-%Y")

        scdate = self.dlg.comboBox_gwsw_sdate.currentText()
        ecdate = self.dlg.comboBox_gwsw_edate.currentText()
        df3 = df2[scdate:ecdate]
    elif self.dlg.radioButton_gwsw_year.isChecked():
        filename = "swatmf_out_MF_gwsw_yearly"
        data = np.loadtxt(os.path.join(wd, filename),
                          skiprows=2,
                          comments=["year:", "Layer"])

        df = np.reshape(data[:, 3], (int(len(data)/nSM_riv), nSM_riv))
        df2 = pd.DataFrame(df)
        df2.index = pd.date_range(startDate, periods=len(df[:,0]), freq='A').strftime("%Y")

        scdate = self.dlg.comboBox_gwsw_sdate.currentText()
        ecdate = self.dlg.comboBox_gwsw_edate.currentText()
        df3 = df2[scdate:ecdate]
    else:
        msgBox = QMessageBox()
        msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
        msgBox.setWindowTitle("Oops!")
        msgBox.setText("Please, select one of the time options!")
        msgBox.exec_()

    # find min and max values in dataframe
    gwsw_min, gwsw_max = df3.values.min(), df3.values.max()

    if self.dlg.checkBox_color_reverse.isChecked():
        color = self.dlg.comboBox_colormaps.currentText() + '_r'
    else:
        color = self.dlg.comboBox_colormaps.currentText()

    colormap = plt.cm.get_cmap(color)

    if self.dlg.checkBox_darktheme.isChecked():
        plt.style.use('dark_background')
    else:
        plt.style.use('default')    

    ### Get extent
    self.layer = QgsProject.instance().mapLayersByName("sub (SWAT)")[0]
    extent = self.layer.extent()
    x_min = extent.xMinimum()
    x_max = extent.xMaximum()
    y_min = extent.yMinimum()
    y_max = extent.yMaximum()

    ### User inputs ===========================================================================
    widthExg = float(self.dlg.doubleSpinBox_w_exag.value())
    verExg = float(self.dlg.doubleSpinBox_h_exag.value())
    totalDate = len(df3)

    count = 0
    self.dlg.progressBar_gwsw.setValue(0)
    for i in range(totalDate):
        gwsw_f = df3.iloc[i]

        # colored bar with their ranks

        colors = [colormap(j) for j in np.linspace(0, 10*gwsw_f.max()/gwsw_max, len(gwsw_f))] # Okay, 10 is weird.
        # gwsw_ff = gwsw_f.astype('int')
        ranks = ss.rankdata(gwsw_f, method = 'dense')
        recols = [colors[(int(rank)-1)] for rank in ranks]

        # fig, ax = plt.subplots(figsize = (7,5))
        fig, ax = plt.subplots()
        fig.subplots_adjust(left = 0.1, right = 0.9, top = 0.9, bottom = 0.2, hspace=0.2, wspace=0.1)
        ax1 = fig.add_subplot(111, frameon=False)
        ax1.tick_params(labelcolor='none', top=False, bottom=False, left=False, right=False)
        ax1 = plt.imshow(np.array([[gwsw_min, gwsw_max]]), cmap = plt.cm.get_cmap(color))
        ax1.set_visible(False)
        ax.tick_params(axis='both', labelsize=6)

        # Title
        if self.dlg.checkBox_gwsw_title.isChecked():
            ax.set_title('- {} -'.format(df3.iloc[i].name), loc = 'left', fontsize = 8, fontweight = 'bold' )

        # frame
        if self.dlg.checkBox_gwsw_frame.isChecked():
            ax.axis('on') # -> takes ticks too.
        else:
            ax.spines['right'].set_visible(False)
            ax.spines['top'].set_visible(False)
            ax.spines['left'].set_visible(False)
            ax.spines['bottom'].set_visible(False)      
            # ax.axis('off')

        # coordinates
        if not self.dlg.checkBox_gwsw_coords.isChecked():
            ax.tick_params(labelcolor='none', top=False, bottom=False, left=False, right=False)       
        else:
            ax.tick_params(top=False, bottom=True, left=True, right=False)

        # colorbar
        if self.dlg.checkBox_gwsw_colorbar.isChecked():
            cbaxes = fig.add_axes([0.3, 0.08, 0.4, 0.02])
            cb = plt.colorbar(cax = cbaxes, orientation="horizontal")
            cb.ax.tick_params(labelsize= 7)
            # cb.ax.invert_yaxis()
            cb.ax.set_title('Groundwater Discharge [$m^3/day$]', fontsize = 8,
                            # position=(1.05, 0.17),
                            horizontalalignment = 'center',
                            )       

        # River
        if self.dlg.checkBox_gwsw_river.isChecked():
            for rv in (river.shapeRecords()):
                rx = [i[0] for i in rv.shape.points[:]]
                ry = [i[1] for i in rv.shape.points[:]]
                ax.plot(rx, ry, lw = 1, c = 'b')
        # Boundary
        if self.dlg.checkBox_gwsw_boundary.isChecked():     
            for sb in (sub.shapeRecords()):
                sx = [i[0] for i in sb.shape.points[:]]
                sy = [i[1] for i in sb.shape.points[:]]
                ax.plot(sx, sy, lw = 0.5, c = 'grey')
        if self.dlg.checkBox_gwsw_yaxes.isChecked():
            y_axis_min = float(self.dlg.lineEdit_gwsw_y_min.text())
            y_axis_max = float(self.dlg.lineEdit_gwsw_y_max.text())
            ax.set_ylim([y_axis_min, y_axis_max])

        # ----------------------------------------------------------------------------------------
        # set size!
        ax.imshow(np.random.random((10,10)), extent=[x_min, x_max, y_min, y_max], alpha = 0)

        ax.bar(f_c.x_min, (gwsw_f*-1*verExg),
                bottom=f_c.y_min,
                width=width * widthExg, align='center',
                alpha=0.7, color=recols, zorder=3)

        if self.dlg.checkBox_gwsw_toVideo.isChecked():
            dpi = int(self.dlg.lineEdit_gwsw_dpi.text())
        else:
            dpi = None

        if self.dlg.radioButton_gwsw_day.isChecked():
            if not os.path.exists(exported + "\\gwsw_day"):
                os.makedirs(exported + "\\gwsw_day")
            plt.savefig(os.path.join(
                exported + "\\gwsw_day", ('daily_{:03d}'.format(count)+'.png')),
                dpi=dpi)
        elif self.dlg.radioButton_gwsw_month.isChecked():
            if not os.path.exists(exported + "\\gwsw_month"):
                os.makedirs(exported + "\\gwsw_month")
            plt.savefig(
                os.path.join(exported + "\\gwsw_month", ('monthly_{:03d}'.format(count)+'.png')),
                dpi=dpi)
        elif self.dlg.radioButton_gwsw_year.isChecked():
            if not os.path.exists(exported + "\\gwsw_annual"):
                os.makedirs(exported + "\\gwsw_annual")
            plt.savefig(
                os.path.join(exported + "\\gwsw_annual", ('yearly_{:03d}'.format(count)+'.png')),
                dpi=dpi)

        plt.clf()
        plt.close()

        # Update progress bar 
        count += 1
        progress = (100*count) / totalDate

        ### Why the following eq not working? =================================================
        # progress = ((count/totalDate) * 100) why? --> got it!!

        self.dlg.progressBar_gwsw.setValue(progress)
        QCoreApplication.processEvents()

    msgBox = QMessageBox()
    msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
    msgBox.setWindowTitle("Exported!")
    msgBox.setText("GWSW plots were created successfully!")
    msgBox.exec_()


def export_gwsw(self):
    import scipy.stats as ss
    import operator
    import numpy as np

    QSWATMOD_path_dict = self.dirs_and_paths()
    stdate, eddate, stdate_warmup, eddate_warmup = self.define_sim_period()
    wd = QSWATMOD_path_dict['SMfolder']
    outfolder = QSWATMOD_path_dict['exported_files']
    startDate = stdate.strftime("%m-%d-%Y")
    msgBox = QMessageBox()
    msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))

    # Open "swatmf_out_MF_gwsw" file
    y = ("for", "Positive:", "Negative:", "Daily", "Monthly", "Annual", "Layer,")  # Remove unnecssary lines
    selectedDate = self.dlg.comboBox_gwsw_dates.currentText()

    if self.dlg.radioButton_gwsw_day.isChecked():
        filename = "swatmf_out_MF_gwsw"
        with open(os.path.join(wd, filename), "r") as f:
            data = [x.strip() for x in f if x.strip() and not x.strip().startswith(y)] # Remove blank lines
        date = [x.strip().split() for x in data if x.strip().startswith("Day:")] # Collect only lines with dates
        onlyDate = [x[1] for x in date] # Only date
        data1 = [x.split() for x in data] # make each line a list
        sdate = datetime.datetime.strptime(startDate, "%m-%d-%Y") # Change startDate format
        dateList = [(sdate + datetime.timedelta(days = int(i)-1)).strftime("%m-%d-%Y") for i in onlyDate]

        # Reverse step
        dateIdx = dateList.index(selectedDate)
        #only
        onlyDate_lookup = onlyDate[dateIdx]
        for num, line in enumerate(data1, 1):
            if line[0] == "Day:" in line and line[1] == onlyDate_lookup in line:
                ii = num # Starting line
    elif self.dlg.radioButton_gwsw_month.isChecked():
        filename = "swatmf_out_MF_gwsw_monthly"
        with open(os.path.join(wd, filename), "r") as f:
            data = [x.strip() for x in f if x.strip() and not x.strip().startswith(y)]  
        date = [x.strip().split() for x in data if x.strip().startswith("month:")]
        data1 = [x.split() for x in data]
        onlyDate = [x[1] for x in date] 
        #dateList = [(sdate + datetime.timedelta(months = int(i)-1)).strftime("%m-%Y") for i in onlyDate]
        dateList = pd.date_range(startDate, periods = len(onlyDate), freq = 'M').strftime("%b-%Y").tolist()
        # Reverse step
        dateIdx = dateList.index(selectedDate)
        # Find year 
        dt = datetime.datetime.strptime(selectedDate, "%b-%Y")
        year = dt.year
        #only
        onlyDate_lookup = onlyDate[dateIdx]
        for num, line in enumerate(data1, 1):
            if ((line[0] == "month:" in line) and (line[1] == onlyDate_lookup in line) and (line[3] == str(year) in line)):
                ii = num # Starting line
    elif self.dlg.radioButton_gwsw_year.isChecked():
        filename = "swatmf_out_MF_gwsw_yearly"
        with open(os.path.join(wd, filename), "r") as f:
            data = [x.strip() for x in f if x.strip() and not x.strip().startswith(y)]  
        date = [x.strip().split() for x in data if x.strip().startswith("year:")]
        data1 = [x.split() for x in data]
        onlyDate = [x[1] for x in date] 
        #dateList = [(sdate + datetime.timedelta(months = int(i)-1)).strftime("%m-%Y") for i in onlyDate]
        dateList = pd.date_range(startDate, periods = len(onlyDate), freq = 'A').strftime("%Y").tolist()

        # Reverse step
        dateIdx = dateList.index(selectedDate)
        #only
        onlyDate_lookup = onlyDate[dateIdx]
        for num, line in enumerate(data1, 1):
            if line[0] == "year:" in line and line[1] == onlyDate_lookup in line:
                ii = num # Starting line
    else:
        msgBox.setWindowTitle("Oops!")
        msgBox.setText("Please, select one of the time options!")
        msgBox.exec_()
    #### Layer
    orgGIS = QSWATMOD_path_dict['org_shps']
    smGIS = QSWATMOD_path_dict['SMshps']
    river = shapefile_sm.Reader(os.path.join(orgGIS, "riv_SM.shp" )) # River
    sub = shapefile_sm.Reader(os.path.join(orgGIS, "mf_boundary.shp" )) # dissolved sub
    sm_riv = shapefile_sm.Reader(os.path.join(smGIS, "sm_riv.shp"))
    # ------------------------------------------------------------------------------
    sr = sm_riv.shapes() # property of sm_river
    coords = [sr[i].bbox for i in range(len(sr))] # get coordinates for each river cell
    width = abs(coords[0][2] - coords[0][0]) # get width for bar plot
    nSM_riv = len(sr) # Get number of river cells
    mf_gwsws = [data1[i][3] for i in range(ii, ii + nSM_riv)] # get gwsw data ranging from ii to 

    # Sort coordinates by row
    c_sorted = sorted(coords, key=operator.itemgetter(0))
    c_sorted = sorted(c_sorted, key=operator.itemgetter(1), reverse=True)

    # Put coordinates and gwsw data in Dataframe together
    f_c = pd.DataFrame(c_sorted, columns=['x_coord', 'y_coord', 'x_max', 'y_max'])
    f_c['gwsw'] = mf_gwsws
    df = f_c.drop(['x_max', 'y_max'], axis=1)

    # Add info
    version = "version 2.10.1."
    time = datetime.datetime.now().strftime('- %m/%d/%y %H:%M:%S -')

    # msgBox = QMessageBox()
    # msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))   
    if self.dlg.radioButton_gwsw_day.isChecked():
        with open(os.path.join(outfolder, "GWSW(" + str(selectedDate) + ")_daily.txt"), 'w') as f:
            f.write("# GWSW(" + str(selectedDate) + ")_daily - QSWATMOD2 Plugin " + version + time + "\n")
            df.to_csv(
                f,
                # index_label="Date",
                index=False,
                sep='\t', float_format='%.2f', lineterminator='\n', encoding='utf-8')
        msgBox.setWindowTitle("Exported!") 
        msgBox.setText(
            "'GWSW"+"(" + str(selectedDate) + 
            ")_daily.txt' file is exported to your 'exported_files' folder!")
        msgBox.exec_()
    elif self.dlg.radioButton_gwsw_month.isChecked():
        with open(os.path.join(outfolder, "GWSW(" + str(selectedDate) + ")_monthly.txt"), 'w') as f:
            f.write("# GWSW(" + str(selectedDate) + ")_monthly - QSWATMOD2 Plugin " + version + time + "\n")
            df.to_csv(
                f,
                # index_label="Date",
                index=False,
                sep='\t', float_format='%.2f', lineterminator='\n', encoding='utf-8')
        msgBox.setWindowTitle("Exported!") 
        msgBox.setText(
            "'GWSW"+"(" + str(selectedDate) + 
            ")_monthly.txt' file is exported to your 'exported_files' folder!")
        msgBox.exec_()
    elif self.dlg.radioButton_gwsw_year.isChecked():
        with open(os.path.join(outfolder, "GWSW(" + str(selectedDate) + ")_annual.txt"), 'w') as f:
            f.write("# GWSW(" + str(selectedDate) + ")_annual - QSWATMOD2 Plugin " + version + time + "\n")
            df.to_csv(
                f,
                # index_label="Date",
                index=False,
                sep='\t', float_format='%.2f', lineterminator='\n', encoding='utf-8')
        msgBox.setWindowTitle("Exported!") 
        msgBox.setText(
            "'GWSW"+"(" + str(selectedDate) + 
            ")_annual.txt' file is exported to your 'exported_files' folder!")
        msgBox.exec_()


def create_gwsw_shp(self):
    QSWATMOD_path_dict = self.dirs_and_paths()
    stdate, eddate, stdate_warmup, eddate_warmup = self.define_sim_period()
    # wd = QSWATMOD_path_dict['SMfolder']
    # startDate = stdate.strftime("%m-%d-%Y")

    msgBox = QMessageBox()
    msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))

    # Create swatmf_results tree inside 
    root = QgsProject.instance().layerTreeRoot()
    if root.findGroup("swatmf_results"):
        swatmf_results = root.findGroup("swatmf_results")
    else:
        swatmf_results = root.insertGroup(0, "swatmf_results")
    sm_riv = QgsProject.instance().mapLayersByName("sm_riv")[0]

    if self.dlg.radioButton_gwsw_day.isChecked():
        # Copy mf_riv shps to swatmf_results tree
        name = "gwsw_day"
        name_ext = "gwsw_day.shp"
        output_dir = QSWATMOD_path_dict['SMshps']

        # Check if there is an exsting mf_head shapefile
        if not any(lyr.name() == (name) for lyr in list(QgsProject.instance().mapLayers().values())):
            gwsw_day_shp = os.path.join(output_dir, name_ext)
            QgsVectorFileWriter.writeAsVectorFormat(
                sm_riv, gwsw_day_shp,
                "utf-8", sm_riv.crs(), "ESRI Shapefile")
            layer = QgsVectorLayer(gwsw_day_shp, '{0}'.format("gwsw_day"), 'ogr')
            # Put in the group
            root = QgsProject.instance().layerTreeRoot()
            swatmf_results = root.findGroup("swatmf_results")
            QgsProject.instance().addMapLayer(layer, False)
            swatmf_results.insertChildNode(0, QgsLayerTreeLayer(layer))

            msgBox.setWindowTitle("Created!")
            msgBox.setText("'gwsw_day.shp' file has been created in 'swatmf_results' group!")
            msgBox.exec_()
    elif self.dlg.radioButton_gwsw_month.isChecked():
        # Copy mf_riv shps to swatmf_results tree
        name = "gwsw_monthly"
        name_ext = "gwsw_monthly.shp"
        output_dir = QSWATMOD_path_dict['SMshps']

        # Check if there is an exsting mf_head shapefile
        if not any(lyr.name() == (name) for lyr in list(QgsProject.instance().mapLayers().values())):
            gwsw_monthly_shp = os.path.join(output_dir, name_ext)
            QgsVectorFileWriter.writeAsVectorFormat(
                sm_riv, gwsw_monthly_shp,
                "utf-8", sm_riv.crs(), "ESRI Shapefile")
            layer = QgsVectorLayer(gwsw_monthly_shp, '{0}'.format("gwsw_monthly"), 'ogr')

            # Put in the group
            root = QgsProject.instance().layerTreeRoot()
            swatmf_results = root.findGroup("swatmf_results")
            QgsProject.instance().addMapLayer(layer, False)
            swatmf_results.insertChildNode(0, QgsLayerTreeLayer(layer))

            msgBox.setWindowTitle("Created!")
            msgBox.setText("'gwsw_monthly.shp' file has been created in 'swatmf_results' group!")
            msgBox.exec_()
    elif self.dlg.radioButton_gwsw_year.isChecked():
        # Copy mf_riv shps to swatmf_results tree
        name = "gwsw_yearly"
        name_ext = "gwsw_yearly.shp"
        output_dir = QSWATMOD_path_dict['SMshps']

        # Check if there is an exsting mf_head shapefile
        if not any(lyr.name() == (name) for lyr in list(QgsProject.instance().mapLayers().values())):
            gwsw_yearly_shp = os.path.join(output_dir, name_ext)
            QgsVectorFileWriter.writeAsVectorFormat(
                sm_riv, gwsw_yearly_shp,
                "utf-8", sm_riv.crs(), "ESRI Shapefile")
            layer = QgsVectorLayer(gwsw_yearly_shp, '{0}'.format("gwsw_yearly"), 'ogr')

            # Put in the group
            root = QgsProject.instance().layerTreeRoot()
            swatmf_results = root.findGroup("swatmf_results")
            QgsProject.instance().addMapLayer(layer, False)
            swatmf_results.insertChildNode(0, QgsLayerTreeLayer(layer))

            msgBox.setWindowTitle("Created!")
            msgBox.setText("'gwsw_yearly.shp' file has been created in 'swatmf_results' group!")
            msgBox.exec_()
    else:
        msgBox.setWindowTitle("Oops!")
        msgBox.setText("Please, select one of time steps!")
        msgBox.exec_()
        self.dlg.checkBox_export_gwsw_shp.setChecked(False)


def export_gwswToShp(self):
    QSWATMOD_path_dict = self.dirs_and_paths()
    stdate, eddate, stdate_warmup, eddate_warmup = self.define_sim_period()
    wd = QSWATMOD_path_dict['SMfolder']
    startDate = stdate.strftime("%m-%d-%Y")

    if self.dlg.radioButton_gwsw_day.isChecked():
        filename = "swatmf_out_MF_gwsw"
        self.layer = QgsProject.instance().mapLayersByName("gwsw_day")[0]
        nSM_riv = self.layer.featureCount()
        # Rmove unnecessary lines
        y = ("Groundwater/Surface", "for", "Positive:", "Negative:", "Layer,", "Monthly", "Yearly")
        with open(os.path.join(wd, filename), "r") as f:
            data = [x.strip() for x in f if x.strip() and not x.strip().startswith(y)] # Remove blank lines
        date = [x.strip().split() for x in data if x.strip().startswith("Day:")] # Collect only lines with dates
        onlyDate = [x[1] for x in date]  # Only date
        data1 = [x.split() for x in data]  # make each line a list
        sdate = datetime.datetime.strptime(startDate, "%m-%d-%Y") # Change startDate format
        dateList = [(sdate + datetime.timedelta(days=int(i)-1)).strftime("%m-%d-%Y") for i in onlyDate]
        # numpy loadtxt is the best way?
        data = np.loadtxt(
                            os.path.join(wd, filename),
                            skiprows=5,
                            comments=["Day:", "Layer"])
        # row and col numbers are required to match gwsw results with shapefile
        # I hate to use f.id(). Is there another way to update field?
        rows = data[:nSM_riv, 1]  # get rows from results
        cols = data[:nSM_riv, 2]  # get cols from results
        df = np.reshape(data[:, 3], (int(len(data)/nSM_riv), nSM_riv))
        df2 = pd.DataFrame(df)
        df2.index = dateList
        scdate = self.dlg.comboBox_gwsw_sdate.currentText()
        ecdate = self.dlg.comboBox_gwsw_edate.currentText()
        df3 = df2[scdate:ecdate]
    elif self.dlg.radioButton_gwsw_month.isChecked():
        filename = "swatmf_out_MF_gwsw_monthly"
        self.layer = QgsProject.instance().mapLayersByName("gwsw_monthly")[0]
        nSM_riv = self.layer.featureCount()
        data = np.loadtxt(
                        os.path.join(wd, filename),
                        skiprows=2,
                        comments=["month:", "Layer"])
        # row and col numbers are required to match gwsw results with shapefile
        # I hate to use f.id(). Is there another way to update field?
        rows = data[:nSM_riv, 1]  # get rows from results
        cols = data[:nSM_riv, 2]  # get cols from results
        df = np.reshape(data[:, 3], (int(len(data)/nSM_riv), nSM_riv))
        df2 = pd.DataFrame(df)
        df2.index = pd.date_range(startDate, periods=len(df[:,0]), freq='M').strftime("%b-%Y")

        scdate = self.dlg.comboBox_gwsw_sdate.currentText()
        ecdate = self.dlg.comboBox_gwsw_edate.currentText()
        df3 = df2[scdate:ecdate]
    elif self.dlg.radioButton_gwsw_year.isChecked():
        filename = "swatmf_out_MF_gwsw_yearly"
        self.layer = QgsProject.instance().mapLayersByName("gwsw_yearly")[0]
        nSM_riv = self.layer.featureCount()
        data = np.loadtxt(os.path.join(wd, filename),
                          skiprows=2,
                          comments=["year:", "Layer"])
        # row and col numbers are required to match gwsw results with shapefile
        # I hate to use f.id(). Is there another way to update field?
        rows = data[:nSM_riv, 1]  # get rows from results
        cols = data[:nSM_riv, 2]  # get cols from results
        df = np.reshape(data[:, 3], (int(len(data)/nSM_riv), nSM_riv))
        df2 = pd.DataFrame(df)
        df2.index = pd.date_range(startDate, periods=len(df[:,0]), freq='A').strftime("%Y")

        scdate = self.dlg.comboBox_gwsw_sdate.currentText()
        ecdate = self.dlg.comboBox_gwsw_edate.currentText()
        df3 = df2[scdate:ecdate]
    else:
        msgBox = QMessageBox()
        msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
        msgBox.setWindowTitle("Oops!")
        msgBox.setText("Please, select one of the time options!")
        msgBox.exec_()

    # Reverse step
    dateList_f = df3.index
    provider = self.layer.dataProvider()

    totalDate = df3.size
    count = 0
    self.dlg.progressBar_gwsw.setValue(0)
    for i in dateList_f:
        gwsw_f = df3.loc[i]
        if provider.fields().indexFromName(i) == -1:
            field = QgsField(i, QVariant.Double, 'double', 20, 5)
            provider.addAttributes([field])
            self.layer.updateFields()
        date_idx = provider.fields().indexFromName(i)

        feats = self.layer.getFeatures()
        self.layer.startEditing()
        for f in feats:
            for r, c, gs in zip(rows, cols, gwsw_f):
                if f.attribute("row") == r and f.attribute("col") == c:
                    self.layer.changeAttributeValue(f.id(), date_idx, gs)
                    # Update progress bar 
                    count += 1
                    progress = (100*count) / totalDate
                    self.dlg.progressBar_gwsw.setValue(int(progress))
                    QCoreApplication.processEvents()
    self.layer.commitChanges()
    msgBox = QMessageBox()
    msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
    msgBox.setWindowTitle("Exported!")
    msgBox.setText("GWSW results have been exported to the GWSW shapefile!")
    msgBox.exec_()

def export_avg_mgwsw(self):
    import scipy.stats as ss
    import operator
    import numpy as np

    QSWATMOD_path_dict = self.dirs_and_paths()
    stdate, eddate, stdate_warmup, eddate_warmup = self.define_sim_period()
    wd = QSWATMOD_path_dict['SMfolder']
    outfolder = QSWATMOD_path_dict['exported_files']
    startDate = stdate.strftime("%m-%d-%Y")
    msgBox = QMessageBox()
    msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))

    # Open "swatmf_out_MF_gwsw" file
    y = ("for", "Positive:", "Negative:", "Daily", "Monthly", "Annual", "Layer,")  # Remove unnecssary lines
    
    
    
    
    selectedDate = self.dlg.comboBox_gwsw_dates.currentText()

    filename = "swatmf_out_MF_gwsw_monthly"
    with open(os.path.join(wd, filename), "r") as f:
        data = [x.strip() for x in f if x.strip() and not x.strip().startswith(y)]  
    date = [x.strip().split() for x in data if x.strip().startswith("month:")]
    data1 = [x.split() for x in data]
    onlyDate = [x[1] for x in date] 
    #dateList = [(sdate + datetime.timedelta(months = int(i)-1)).strftime("%m-%Y") for i in onlyDate]
    dateList = pd.date_range(startDate, periods = len(onlyDate), freq = 'M').strftime("%b-%Y").tolist()
    
    
    # Reverse step
    dateIdx = dateList.index(selectedDate)
    # Find year 
    dt = datetime.datetime.strptime(selectedDate, "%b-%Y")
    year = dt.year
    #only
    onlyDate_lookup = onlyDate[dateIdx]
    for num, line in enumerate(data1, 1):
        if ((line[0] == "month:" in line) and (line[1] == onlyDate_lookup in line) and (line[3] == str(year) in line)):
            ii = num # Starting line

    #### Layer
    orgGIS = QSWATMOD_path_dict['org_shps']
    smGIS = QSWATMOD_path_dict['SMshps']
    river = shapefile_sm.Reader(os.path.join(orgGIS, "riv_SM.shp" )) # River
    sub = shapefile_sm.Reader(os.path.join(orgGIS, "mf_boundary.shp" )) # dissolved sub
    sm_riv = shapefile_sm.Reader(os.path.join(smGIS, "sm_riv.shp"))
    # ------------------------------------------------------------------------------
    sr = sm_riv.shapes() # property of sm_river
    coords = [sr[i].bbox for i in range(len(sr))] # get coordinates for each river cell
    width = abs(coords[0][2] - coords[0][0]) # get width for bar plot
    nSM_riv = len(sr) # Get number of river cells
    mf_gwsws = [data1[i][3] for i in range(ii, ii + nSM_riv)] # get gwsw data ranging from ii to 

    # Sort coordinates by row
    c_sorted = sorted(coords, key=operator.itemgetter(0))
    c_sorted = sorted(c_sorted, key=operator.itemgetter(1), reverse=True)

    # Put coordinates and gwsw data in Dataframe together
    f_c = pd.DataFrame(c_sorted, columns=['x_coord', 'y_coord', 'x_max', 'y_max'])
    f_c['gwsw'] = mf_gwsws
    df = f_c.drop(['x_max', 'y_max'], axis=1)

    # Add info
    version = "version 2.10.1."
    time = datetime.datetime.now().strftime('- %m/%d/%y %H:%M:%S -')

    # msgBox = QMessageBox()
    # msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))   
    if self.dlg.radioButton_gwsw_day.isChecked():
        with open(os.path.join(outfolder, "GWSW(" + str(selectedDate) + ")_daily.txt"), 'w') as f:
            f.write("# GWSW(" + str(selectedDate) + ")_daily - QSWATMOD2 Plugin " + version + time + "\n")
            df.to_csv(
                f,
                # index_label="Date",
                index=False,
                sep='\t', float_format='%.2f', lineterminator='\n', encoding='utf-8')
        msgBox.setWindowTitle("Exported!") 
        msgBox.setText(
            "'GWSW"+"(" + str(selectedDate) + 
            ")_daily.txt' file is exported to your 'exported_files' folder!")
        msgBox.exec_()
    elif self.dlg.radioButton_gwsw_month.isChecked():
        with open(os.path.join(outfolder, "GWSW(" + str(selectedDate) + ")_monthly.txt"), 'w') as f:
            f.write("# GWSW(" + str(selectedDate) + ")_monthly - QSWATMOD2 Plugin " + version + time + "\n")
            df.to_csv(
                f,
                # index_label="Date",
                index=False,
                sep='\t', float_format='%.2f', lineterminator='\n', encoding='utf-8')
        msgBox.setWindowTitle("Exported!") 
        msgBox.setText(
            "'GWSW"+"(" + str(selectedDate) + 
            ")_monthly.txt' file is exported to your 'exported_files' folder!")
        msgBox.exec_()
    elif self.dlg.radioButton_gwsw_year.isChecked():
        with open(os.path.join(outfolder, "GWSW(" + str(selectedDate) + ")_annual.txt"), 'w') as f:
            f.write("# GWSW(" + str(selectedDate) + ")_annual - QSWATMOD2 Plugin " + version + time + "\n")
            df.to_csv(
                f,
                # index_label="Date",
                index=False,
                sep='\t', float_format='%.2f', lineterminator='\n', encoding='utf-8')
        msgBox.setWindowTitle("Exported!") 
        msgBox.setText(
            "'GWSW"+"(" + str(selectedDate) + 
            ")_annual.txt' file is exported to your 'exported_files' folder!")
        msgBox.exec_()