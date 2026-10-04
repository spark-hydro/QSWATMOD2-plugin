# -*- coding: utf-8 -*-
from builtins import zip
from builtins import str
from builtins import range
from qgis.core import (
                        QgsProject, QgsLayerTreeLayer, QgsVectorFileWriter, QgsVectorLayer, QgsRasterLayer,
                        QgsField, QgsRasterBandStats, QgsColorRampShader, QgsRasterShader,
                        QgsSingleBandPseudoColorRenderer, QgsMapSettings, QgsMapRendererCustomPainterJob,
                        QgsRectangle)
from qgis.PyQt import QtCore, QtGui, QtSql
import datetime
import pandas as pd
import os
import glob
from PyQt5.QtGui import QIcon, QColor, QImage, QPainter, QPen, QFont
from PyQt5.QtWidgets import QMessageBox
from qgis.PyQt.QtCore import QVariant, QCoreApplication, QSize, Qt, QPoint, QRect
import calendar
import processing
from qgis.gui import QgsMapCanvas
import glob
from PIL import Image
import sqlite3
from ..pyfolder import linking_process


def save_grid_as_vl(self, outnam):
    self.delete_layers([outnam])

    layer = QgsProject.instance().mapLayersByName("mf_grid (MODFLOW)")[0]
    layer.selectAll()
    params = {
        'INPUT': layer,
        'OUTPUT': f"memory:{outnam}"
    }
    outlayer = processing.run("native:saveselectedfeatures", params)['OUTPUT']
    layer.removeSelection()

    # Put in the group
    for lyr in list(QgsProject.instance().mapLayers().values()):
        if lyr.name() == (outlayer):
            QgsProject.instance().removeMapLayers([lyr.id()])
    # Put in the group
    root = QgsProject.instance().layerTreeRoot()
    if root.findGroup("swatmf_results"):
        sm_group = root.findGroup("swatmf_results")
    else:
        sm_group = root.insertGroup(0, "swatmf_results")
    sm_group = root.findGroup("swatmf_results")
    QgsProject.instance().addMapLayer(outlayer, False)
    sm_group.insertChildNode(1, QgsLayerTreeLayer(outlayer))


def read_mf_recharge_dates(self):
    QSWATMOD_path_dict = self.dirs_and_paths()
    stdate, eddate, stdate_warmup, eddate_warmup = self.define_sim_period()
    wd = QSWATMOD_path_dict['SMfolder']
    startDate = stdate.strftime("%m-%d-%Y")
    try:
        if self.dlg.checkBox_recharge.isChecked() and self.dlg.radioButton_mf_results_d.isChecked():
            filename = "swatmf_out_MF_recharge"
            # Open "swatmf_out_MF_recharge" file
            y = ("MODFLOW", "--Calculated", "daily") # Remove unnecssary lines
            with open(os.path.join(wd, filename), "r") as f:
                data = [x.strip() for x in f if x.strip() and not x.strip().startswith(y)]  # Remove blank lines
            date = [x.strip().split() for x in data if x.strip().startswith("Day:")] # Collect only lines with dates
            onlyDate = [x[1] for x in date] # Only date
            # data1 = [x.split() for x in data] # make each line a list
            sdate = datetime.datetime.strptime(startDate, "%m-%d-%Y")  # Change startDate format
            # dateList = [(sdate + datetime.timedelta(days = int(i)-1)).strftime("%m-%d-%Y") for i in onlyDate]
            dateList = [(sdate + datetime.timedelta(days = int(i)-1)).strftime("%Y-%m-%d") for i in onlyDate]

        elif self.dlg.checkBox_recharge.isChecked() and self.dlg.radioButton_mf_results_m.isChecked():
            filename = "swatmf_out_MF_recharge_monthly"
            # Open "swatmf_out_MF_recharge" file
            y = ("Monthly") # Remove unnecssary lines
            with open(os.path.join(wd, filename), "r") as f:
                data = [x.strip() for x in f if x.strip() and not x.strip().startswith(y)] # Remove blank lines
            date = [x.strip().split() for x in data if x.strip().startswith("month:")] # Collect only lines with dates
            onlyDate = [x[1] for x in date] # Only date
            # data1 = [x.split() for x in data] # make each line a list
            dateList = pd.date_range(startDate, periods=len(onlyDate), freq='ME').strftime("%b-%Y").tolist()
     
        elif self.dlg.checkBox_recharge.isChecked() and self.dlg.radioButton_mf_results_y.isChecked():
            filename = "swatmf_out_MF_recharge_yearly"
            # Open "swatmf_out_MF_recharge" file
            y = ("Yearly") # Remove unnecssary lines
            with open(os.path.join(wd, filename), "r") as f:
                data = [x.strip() for x in f if x.strip() and not x.strip().startswith(y)] # Remove blank lines
            date = [x.strip().split() for x in data if x.strip().startswith("year:")] # Collect only lines with dates
            onlyDate = [x[1] for x in date] # Only date
            # data1 = [x.split() for x in data] # make each line a list
            dateList = pd.date_range(startDate, periods = len(onlyDate), freq = 'YE').strftime("%Y").tolist()
        self.dlg.comboBox_mf_results_sdate.clear()
        self.dlg.comboBox_mf_results_sdate.addItems(dateList)
        self.dlg.comboBox_mf_results_edate.clear()
        self.dlg.comboBox_mf_results_edate.addItems(dateList)
        self.dlg.comboBox_mf_results_edate.setCurrentIndex(len(dateList)-1)
    except ValueError:
        self.main_messageBox("Error!", "Please, select one of the time options!")
        self.dlg.comboBox_mf_results_sdate.clear()
        self.dlg.comboBox_mf_results_edate.clear()



def create_grid_result_tables(self, tablename, df):
    QSWATMOD_path_dict = self.dirs_and_paths()
    wd = QSWATMOD_path_dict['db_files']
    conn = sqlite3.connect(os.path.join(wd, 'mf.db'))
    cursor = conn.cursor()
    # Original table name
    original_table = 'mf_db'
    # New table name
    # Create the duplicate table with data
    query1 = f"""
    DROP TABLE IF EXISTS {tablename}
    """
    cursor.execute(query1)
    query2 = f"""
    CREATE TABLE {tablename} AS SELECT * FROM {original_table}
    """    
    cursor.execute(query2)
    conn.commit()

    query3 = f"""
    SELECT * FROM {tablename}
    """
    sqlite_df = pd.read_sql_query(query3, conn)
    merged_df = pd.merge(sqlite_df, df, on='grid_id', how='left')
    merged_df.to_sql(tablename, conn, if_exists='replace', index=False)
    # Close the connection
    conn.close()


def export_mf_recharge(self):
    self.dlg.progressBar_mf_results.setValue(0)
    if self.dlg.radioButton_mf_results_d.isChecked():
        layernam = "mf_recharge_day"
    elif self.dlg.radioButton_mf_results_m.isChecked():
        layernam = "mf_recharge_mon"
    elif self.dlg.radioButton_mf_results_y.isChecked():
        layernam = "mf_recharge_year"
    self.delete_layers([layernam])
    save_grid_as_vl(self, layernam)
    grid_result_tname = layernam
    df = get_grid_recharge_df(self)
    create_grid_result_tables(self, grid_result_tname, df)
    join_mf_grid_result(self, layernam, layernam)
    linking_process.cvt_vl_to_gpkg(
        self, layernam, f"{layernam}.gpkg", "swatmf_results")
    linking_process.delete_fields(self, layernam, "_2")
    self.dlg.progressBar_mf_results.setValue(100)
    self.main_messageBox(
        "Exported!", 
        f"'{layernam}' results were exported successfully!")


def get_rech_avg_m_df(self):
    self.dlg.progressBar_rch_head.setValue(0)
    self.main_messageBox("Reading in progress...", "We are going to read gridded recharge outputs ...")
    QSWATMOD_path_dict = self.dirs_and_paths()
    stdate, eddate, stdate_warmup, eddate_warmup = self.define_sim_period()
    wd = QSWATMOD_path_dict['SMfolder']
    exported_folder = QSWATMOD_path_dict["exported_files"]
    startDate = stdate.strftime("%m-%d-%Y")
    # Open "swatmf_out_MF_head" file
    y = ("Monthly", "Yearly") # Remove unnecssary lines
    filename = "swatmf_out_MF_recharge_monthly"
    # self.layer = QgsProject.instance().mapLayersByName("mf_nitrate_monthly")[0]
    with open(os.path.join(wd, filename), "r") as f:
        data = [x.strip() for x in f if x.strip() and not x.strip().startswith(y)] # Remove blank lines     
    date = [x.strip().split() for x in data if x.strip().startswith("month:")] # Collect only lines with dates  
    onlyDate = [x[1] for x in date] # Only date
    data1 = [x.split() for x in data] # make each line a list
    dateList = pd.date_range(startDate, periods=len(onlyDate), freq ='M').strftime("%b-%Y").tolist()

    selectedSdate = self.dlg.comboBox_mf_results_sdate.currentText()
    selectedEdate = self.dlg.comboBox_mf_results_edate.currentText()
    # Reverse step
    dateSidx = dateList.index(selectedSdate)
    dateEidx = dateList.index(selectedEdate)
    dateList_f = dateList[dateSidx:dateEidx+1]
    input1 = QgsProject.instance().mapLayersByName("mf_grid (MODFLOW)")[0] # Put this here to know number of features

    big_df = pd.DataFrame()
    datecount = 0
    for selectedDate in dateList_f:
        # Reverse step
        dateIdx = dateList.index(selectedDate)
        #only
        onlyDate_lookup = onlyDate[dateIdx]
        dt = datetime.datetime.strptime(selectedDate, "%b-%Y")
        year = dt.year
        layerN = self.dlg.comboBox_rt_layer.currentText()
        for num, line in enumerate(data1, 1):
            if ((line[0] == "month:" in line) and (line[1] == onlyDate_lookup in line) and (line[3] == str(year) in line)):
                ii = num # Starting line
        mf_rchs = []
        hdcount = 0
        while hdcount < input1.featureCount():
            for kk in range(len(data1[ii])):
                mf_rchs.append(float(data1[ii][kk]))
                hdcount += 1
            ii += 1
        s = pd.Series(mf_rchs, name=datetime.datetime.strptime(selectedDate, "%b-%Y").strftime("%Y-%m-%d"))
        big_df = pd.concat([big_df, s], axis=1)
        datecount +=1
        provalue = round(datecount/len(dateList_f)*100)
        self.dlg.progressBar_rch_head.setValue(provalue)
        QCoreApplication.processEvents()
        self.dlg.raise_()

    big_df = big_df.T
    big_df.index = pd.to_datetime(big_df.index)
    mbig_df = big_df.groupby(big_df.index.month).mean()
    mbig_df.to_csv(os.path.join(exported_folder, "mf_rch_avg_mon.csv"), index=False)


    msgBox = QMessageBox()
    msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
    msgBox.setWindowTitle("Exported!")
    msgBox.setText("'mf_rch_avg_mon.csv' was exported ...")
    msgBox.exec_()
    msgBox = QMessageBox()
    msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
    msgBox.setWindowTitle("Exporting ...")
    msgBox.setText("It will begin in exporting data to the shapefile.")
    msgBox.exec_()
    return mbig_df


def create_rech_avg_mon_shp(self):
    input1 = QgsProject.instance().mapLayersByName("mf_grid (MODFLOW)")[0]
    QSWATMOD_path_dict = self.dirs_and_paths()

    # Copy mf_grid shapefile to swatmf_results tree
    name = "mf_rch_avg_mon"
    name_ext = "mf_rch_avg_mon.shp"
    output_dir = QSWATMOD_path_dict['SMshps']
    # Check if there is an exsting mf_head shapefile
    if not any(lyr.name() == (name) for lyr in list(QgsProject.instance().mapLayers().values())):
        mf_rch_shp = os.path.join(output_dir, name_ext)
        QgsVectorFileWriter.writeAsVectorFormat(
            input1, mf_rch_shp,
            "utf-8", input1.crs(), "ESRI Shapefile")
        layer = QgsVectorLayer(mf_rch_shp, '{0}'.format(name), 'ogr')
        # Put in the group
        root = QgsProject.instance().layerTreeRoot()
        swatmf_results = root.findGroup("swatmf_results")
        QgsProject.instance().addMapLayer(layer, False)
        swatmf_results.insertChildNode(0, QgsLayerTreeLayer(layer))
        self.main_messageBox(
            "Created!", 
            "'mf_rch_avg_mon.shp' file has been created in 'swatmf_results' group!")
        
def selected_mf_mon(self):
    selected_months = []
    if self.dlg.checkBox_hr_jan.isChecked():
        selected_months.append(1)
    if self.dlg.checkBox_hr_feb.isChecked():
        selected_months.append(2)
    if self.dlg.checkBox_hr_mar.isChecked():
        selected_months.append(3)
    if self.dlg.checkBox_hr_apr.isChecked():
        selected_months.append(4)
    if self.dlg.checkBox_hr_may.isChecked():
        selected_months.append(5)
    if self.dlg.checkBox_hr_jun.isChecked():
        selected_months.append(6)
    if self.dlg.checkBox_hr_jul.isChecked():
        selected_months.append(7)
    if self.dlg.checkBox_hr_aug.isChecked():
        selected_months.append(8)
    if self.dlg.checkBox_hr_sep.isChecked():
        selected_months.append(9)
    if self.dlg.checkBox_hr_oct.isChecked():
        selected_months.append(10)
    if self.dlg.checkBox_hr_nov.isChecked():
        selected_months.append(11)    
    if self.dlg.checkBox_hr_dec.isChecked():
        selected_months.append(12)
    return selected_months


def export_mf_rch_avg_m(self):
    mbig_df = get_rech_avg_m_df(self)
    selected_months = selected_mf_mon(self)
    self.layer = QgsProject.instance().mapLayersByName("mf_rch_avg_mon")[0]
    per = 0
    self.dlg.progressBar_mf_results.setValue(0)
    for m in selected_months:
        m_vals = mbig_df.loc[m, :]
        QCoreApplication.processEvents()
        mon_nam = calendar.month_abbr[m]

        provider = self.layer.dataProvider()
        if self.layer.dataProvider().fields().indexFromName(mon_nam) == -1:
            field = QgsField(mon_nam, QVariant.Double, 'double', 20, 5)
            provider.addAttributes([field])
            self.layer.updateFields()
        mf_hds_idx = provider.fields().indexFromName(mon_nam)
        
        tot_feats = self.layer.featureCount()
        count = 0        
        # Get features (Find out a way to change attribute values using another field)
        feats = self.layer.getFeatures()
        self.layer.startEditing()
        # add row number
        for f, mf_hd in zip(feats, m_vals):
            self.layer.changeAttributeValue(f.id(), mf_hds_idx, mf_hd)
            count += 1
            provalue = round(count/tot_feats*100)
            self.dlg.progressBar_rch_head.setValue(provalue)
            QCoreApplication.processEvents()
        self.layer.commitChanges()
        QCoreApplication.processEvents()

        # Update progress bar 
        per += 1
        progress = round((per / len(selected_months)) *100)
        self.dlg.progressBar_mf_results.setValue(progress)
        QCoreApplication.processEvents()
        self.dlg.raise_()
    self.main_messageBox("Exported!", "'mf_rch_avg_mon' results were exported successfully!")


def get_grid_recharge_df(self):
    self.dlg.progressBar_rch_head.setValue(0)
    self.main_messageBox("Reading in progress...", "We are going to read gridded recharge outputs ...")
    QSWATMOD_path_dict = self.dirs_and_paths()
    stdate, eddate, stdate_warmup, eddate_warmup = self.define_sim_period()
    wd = QSWATMOD_path_dict['SMfolder']
    exported_folder = QSWATMOD_path_dict["exported_files"]
    startDate = stdate.strftime("%m-%d-%Y")
    # Open "swatmf_out_MF_head" file
    y = ("Monthly", "Yearly") # Remove unnecssary lines

    if self.dlg.radioButton_mf_results_d.isChecked():
        y = ("MODFLOW", "--Calculated", "daily", "Monthly", "Yearly") # Remove unnecssary lines
        filename = "swatmf_out_MF_recharge"
        with open(os.path.join(wd, filename), "r") as f:
            data = [x.strip() for x in f if x.strip() and not x.strip().startswith(y)] # Remove blank lines     
        date = [x.strip().split() for x in data if x.strip().startswith("Day:")] # Collect only lines with dates  
        onlyDate = [x[1] for x in date] # Only date
        data1 = [x.split() for x in data] # make each line a list
        sdate = datetime.datetime.strptime(startDate, "%m-%d-%Y") # Change startDate format
        # dateList = [(sdate + datetime.timedelta(days = int(i)-1)).strftime("%m-%d-%Y") for i in onlyDate]
        dateList = [(sdate + datetime.timedelta(days = int(i)-1)).strftime("%Y-%m-%d") for i in onlyDate]
    elif self.dlg.radioButton_mf_results_m.isChecked():
        filename = "swatmf_out_MF_recharge_monthly"
        with open(os.path.join(wd, filename), "r") as f:
            data = [x.strip() for x in f if x.strip() and not x.strip().startswith(y)] # Remove blank lines     
        date = [x.strip().split() for x in data if x.strip().startswith("month:")] # Collect only lines with dates  
        onlyDate = [x[1] for x in date] # Only date
        data1 = [x.split() for x in data] # make each line a list
        dateList = pd.date_range(startDate, periods=len(onlyDate), freq ='ME').strftime("%b-%Y").tolist()
    elif self.dlg.radioButton_mf_results_y.isChecked():
        filename = "swatmf_out_MF_recharge_yearly"
        with open(os.path.join(wd, filename), "r") as f:
            data = [x.strip() for x in f if x.strip() and not x.strip().startswith(y)] # Remove blank lines
        date = [x.strip().split() for x in data if x.strip().startswith("year:")] # Collect only lines with dates
        onlyDate = [x[1] for x in date] # Only date
        data1 = [x.split() for x in data] # make each line a list
        dateList = pd.date_range(startDate, periods=len(onlyDate), freq='YE').strftime("%Y").tolist()
    selectedSdate = self.dlg.comboBox_mf_results_sdate.currentText()
    selectedEdate = self.dlg.comboBox_mf_results_edate.currentText()
    # Reverse step
    dateSidx = dateList.index(selectedSdate)
    dateEidx = dateList.index(selectedEdate)
    dateList_f = dateList[dateSidx:dateEidx+1]
    input1 = QgsProject.instance().mapLayersByName("mf_grid (MODFLOW)")[0] # Put this here to know number of features
    big_df = pd.DataFrame()
    datecount = 0
    for selectedDate in dateList_f:
        # Reverse step
        dateIdx = dateList.index(selectedDate)
        onlyDate_lookup = onlyDate[dateIdx]
        if self.dlg.radioButton_mf_results_d.isChecked():
            dt = datetime.datetime.strptime(selectedDate, "%Y-%m-%d")
            year = dt.year
            for num, line in enumerate(data1, 1):
                if line[0] == "Day:" in line and line[1] == onlyDate_lookup in line:
                    ii = num # Starting line
        elif self.dlg.radioButton_mf_results_m.isChecked():
            dt = datetime.datetime.strptime(selectedDate, "%b-%Y")
            year = dt.year
            for num, line in enumerate(data1, 1):
                if ((line[0] == "month:" in line) and (line[1] == onlyDate_lookup in line) and (line[3] == str(year) in line)):
                    ii = num
        elif self.dlg.radioButton_mf_results_y.isChecked():
            dt = datetime.datetime.strptime(selectedDate, "%Y")
            year = dt.year
            for num, line in enumerate(data1, 1):
                if ((line[0] == "year:" in line) and (line[1] == onlyDate_lookup in line)):
                    ii = num # Starting line
        # Get the recharge values
        mf_rchs = []
        count = 0
        while count < input1.featureCount():
            for jj in range(len(data1[ii])):
                mf_rchs.append(float(data1[ii][jj]))
                count += 1
            ii += 1
        if self.dlg.radioButton_mf_results_d.isChecked():
            s = pd.Series(mf_rchs, name=datetime.datetime.strptime(selectedDate, "%Y-%m-%d").strftime("%Y-%m-%d"))
            big_df = pd.concat([big_df, s], axis=1)
        elif self.dlg.radioButton_mf_results_m.isChecked():
            s = pd.Series(mf_rchs, name=datetime.datetime.strptime(selectedDate, "%b-%Y").strftime("%b-%Y"))
            big_df = pd.concat([big_df, s], axis=1)
        elif self.dlg.radioButton_mf_results_y.isChecked():
            s = pd.Series(mf_rchs, name=datetime.datetime.strptime(selectedDate, "%Y").strftime("%Y"))
            big_df = pd.concat([big_df, s], axis=1)
        datecount +=1
        provalue = round(datecount/len(dateList_f)*100)
        self.dlg.progressBar_rch_head.setValue(provalue)
        QCoreApplication.processEvents()
        self.dlg.raise_()        
    big_df.insert(0, 'grid_id', value=range(1, len(big_df) + 1))
    if self.dlg.radioButton_mf_results_d.isChecked():
        big_df.to_csv(os.path.join(QSWATMOD_path_dict["exported_files"], "mf_recharge_day_table.csv"), index=False)
    if self.dlg.radioButton_mf_results_m.isChecked():
        big_df.to_csv(os.path.join(QSWATMOD_path_dict["exported_files"], "mf_recharge_mon_table.csv"), index=False)
    elif self.dlg.radioButton_mf_results_y.isChecked():
        big_df.to_csv(os.path.join(QSWATMOD_path_dict["exported_files"], "mf_recharge_year_table.csv"), index=False)
    return big_df


def join_mf_grid_result(self, layername, tablename):

    # get layer
    layer = QgsProject.instance().mapLayersByName(layername)[0]
    QSWATMOD_path_dict = self.dirs_and_paths()
    db_folder = QSWATMOD_path_dict["db_files"]

    # read mf_db
    conn = os.path.join(db_folder, 'mf.db')

    params = {
        'INPUT': layer,
        'FIELD': 'grid_id',
        'INPUT_2': conn + f"|layername={tablename}",
        'FIELD_2': 'grid_id',
        'FIELDS_TO_COPY': [],
        'METHOD':1,
        'DISCARD_NONMATCHING':False,
        'PREFIX':'',
        'OUTPUT': f"memory:{layername}",
        # 'OUTPUT': layer_source,
        # '--overwrite': True,
        }
    outlayer = processing.run("native:joinattributestable", params)['OUTPUT']
    self.delete_layers([layername])
    # Put in the group  
    root = QgsProject.instance().layerTreeRoot()
    mf_group = root.findGroup("swatmf_results")
    QgsProject.instance().addMapLayer(outlayer, False)
    mf_group.insertChildNode(0, QgsLayerTreeLayer(outlayer))
    # self.end_time(desc)



def read_vector_maps_hydrology(self):
    layers = [lyr.name() for lyr in list(QgsProject.instance().mapLayers().values())]
    available_layers = [
                'mf_head_day',
                'mf_head_mon',
                'mf_head_year',
                'mf_recharge_day',
                'mf_recharege_mon',
                'mf_recharge_year',
                'mf_recharge_avg_mon',
                'base_rd_avg_mon_rech_f'
                ]
    self.dlg.comboBox_vector_lyrs_mf.clear()
    self.dlg.comboBox_vector_lyrs_mf.addItems(available_layers)
    for i in range(len(available_layers)):
        self.dlg.comboBox_vector_lyrs_mf.model().item(i).setEnabled(False)
    for i in available_layers:
        for j in layers:
            if i == j:
                idx = available_layers.index(i)
                self.dlg.comboBox_vector_lyrs_mf.model().item(idx).setEnabled(True)
    self.dlg.mColorButton_min_rmap.defaultColor()
    self.dlg.mColorButton_max_rmap.defaultColor()


def cvt_vtr_hydrology(self):
    QSWATMOD_path_dict = self.dirs_and_paths()
    selectedVector = self.dlg.comboBox_vector_lyrs_mf.currentText()
    layer = QgsProject.instance().mapLayersByName(str(selectedVector))[0]

    # Find .dis file and read number of rows, cols, x spacing, and y spacing (not allowed to change)
    for filename in glob.glob(str(QSWATMOD_path_dict['SMfolder'])+"/*.dis"):
        with open(filename, "r") as f:
            data = []
            for line in f.readlines():
                if not line.startswith("#"):
                    data.append(line.replace('\n', '').split())
        nrow = int(data[0][1])
        ncol = int(data[0][2])
        delr = float(data[2][1]) # is the cell width along rows (y spacing)
        delc = float(data[3][1]) # is the cell width along columns (x spacing).

    # get extent
    ext = layer.extent()
    xmin = ext.xMinimum()
    xmax = ext.xMaximum()
    ymin = ext.yMinimum()
    ymax = ext.yMaximum()
    extent = "{a},{b},{c},{d}".format(a=xmin, b=xmax, c=ymin, d=ymax)

    fdnames = [
                field.name() for field in layer.dataProvider().fields() if not (
                field.name() == 'fid' or
                field.name() == 'id' or
                field.name() == 'xmin' or
                field.name() == 'xmax' or
                field.name() == 'ymin' or
                field.name() == 'ymax' or
                field.name() == 'grid_id' or
                field.name() == 'row' or
                field.name() == 'col' or
                field.name() == 'top_elev'
                )
                    ]

    # Create swatmf_results tree inside 
    root = QgsProject.instance().layerTreeRoot()
    if root.findGroup("swatmf_results"):
        swatmf_results = root.findGroup("swatmf_results")
    else:
        swatmf_results = root.insertGroup(0, "swatmf_results")
    
    if root.findGroup(selectedVector):
        rastergroup = root.findGroup(selectedVector)
    else:
        rastergroup = swatmf_results.insertGroup(0, selectedVector)
    per = 0
    self.dlg.progressBar_cvt_vtr_mf.setValue(0)
    for fdnam in fdnames:
        QCoreApplication.processEvents()
        nodata = float(self.dlg.lineEdit_nodata_mf.text())
        mincolor = self.dlg.mColorButton_min_map_mf.color().name()
        maxcolor = self.dlg.mColorButton_max_map_mf.color().name()
        name = fdnam
        name_ext = "{}.tif".format(name)
        output_dir = QSWATMOD_path_dict['SMshps']
        # create folder for each layer output
        rasterpath = os.path.join(output_dir, selectedVector)
        if not os.path.exists(rasterpath):
            os.makedirs(rasterpath)
        output_raster = os.path.join(rasterpath, name_ext)
        params = {
            'INPUT': layer,
            'FIELD': fdnam,
            'UNITS': 1,
            'WIDTH': delc,
            'HEIGHT': delr,
            'EXTENT': extent,
            'NODATA': nodata,
            'DATA_TYPE': 5, #Float32
            'OUTPUT': output_raster
        }
        processing.run("gdal:rasterize", params)
        rasterlayer = QgsRasterLayer(output_raster, '{0} ({1})'.format(fdnam, selectedVector))
        QgsProject.instance().addMapLayer(rasterlayer, False)
        rastergroup.insertChildNode(0, QgsLayerTreeLayer(rasterlayer))
        stats = rasterlayer.dataProvider().bandStatistics(1, QgsRasterBandStats.All)
        rmin = stats.minimumValue
        rmax = stats.maximumValue
        fnc = QgsColorRampShader()
        lst = [QgsColorRampShader.ColorRampItem(rmin, QColor(mincolor)), QgsColorRampShader.ColorRampItem(rmax, QColor(maxcolor))]
        fnc.setColorRampItemList(lst)
        fnc.setColorRampType(QgsColorRampShader.Interpolated)
        shader = QgsRasterShader()
        shader.setRasterShaderFunction(fnc)
        renderer = QgsSingleBandPseudoColorRenderer(rasterlayer.dataProvider(), 1, shader)
        rasterlayer.setRenderer(renderer)
        rasterlayer.triggerRepaint()

        # create image
        img = QImage(QSize(800, 800), QImage.Format_ARGB32_Premultiplied)
        # set background color
        # bcolor = QColor(255, 255, 255, 255)
        bcolor = QColor(255, 255, 255, 0)
        img.fill(bcolor.rgba())
        # create painter
        p = QPainter()
        p.begin(img)
        p.setRenderHint(QPainter.Antialiasing)
        # create map settings
        ms = QgsMapSettings()
        ms.setBackgroundColor(bcolor)
        # set layers to render
        flayer = QgsProject.instance().mapLayersByName(rasterlayer.name())
        ms.setLayers([flayer[0]])
        # set extent
        rect = QgsRectangle(ms.fullExtent())
        rect.scale(1.1)
        ms.setExtent(rect)
        # set ouptut size
        ms.setOutputSize(img.size())
        # setup qgis map renderer
        render = QgsMapRendererCustomPainterJob(ms, p)
        render.start()
        render.waitForFinished()
        # get timestamp
        p.drawImage(QPoint(), img)
        pen = QPen(Qt.red)
        pen.setWidth(2)
        p.setPen(pen)

        font = QFont()
        font.setFamily('Times')
        # font.setBold(True)
        font.setPointSize(18)
        p.setFont(font)
        # p.setBackground(QColor('sea green')) doesn't work    
        p.drawText(QRect(0, 0, 800, 800), Qt.AlignRight | Qt.AlignBottom, fdnam)
        p.end()

        # save the image
        img.save(os.path.join(rasterpath, '{:03d}_{}.jpg'.format(per, fdnam)))
        
        # Update progress bar         
        per += 1
        progress = round((per / len(fdnames)) *100)
        self.dlg.progressBar_cvt_vtr_mf.setValue(progress)
        QCoreApplication.processEvents()
        self.dlg.raise_()

    duration = self.dlg.doubleSpinBox_ani_mf_time.value()
    # filepaths
    fp_in = os.path.join(rasterpath, '*.jpg')
    fp_out = os.path.join(rasterpath, '{}.gif'.format(selectedVector))
    # https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#gif
    fimg, *fimgs = [Image.open(f) for f in sorted(glob.glob(fp_in))]
    fimg.save(fp=fp_out, format='GIF', append_images=fimgs,
            save_all=True, duration=duration*1000, loop=0, transparency=0)
    
    msgBox = QMessageBox()
    msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
    msgBox.setWindowTitle("Coverted!")
    msgBox.setText("Fields from {} were converted successfully!".format(selectedVector))
    msgBox.exec_()

    questionBox = QMessageBox()
    questionBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
    reply = QMessageBox.question(
                    questionBox, 'Open?', 
                    'Do you want to open the animated gif file?', QMessageBox.Yes, QMessageBox.No)
    if reply == QMessageBox.Yes:
        os.startfile(os.path.join(rasterpath, '{}.gif'.format(selectedVector)))
