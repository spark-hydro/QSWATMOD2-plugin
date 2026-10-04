# -*- coding: utf-8 -*-
from builtins import zip
from builtins import str
from builtins import range
from qgis.core import (
                        QgsProject, QgsLayerTreeLayer, QgsVectorFileWriter, QgsVectorLayer,
                        QgsField)
from qgis.PyQt import QtCore, QtGui, QtSql
import datetime
import pandas as pd
import os
import glob
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMessageBox
from qgis.PyQt.QtCore import QVariant, QCoreApplication
from ..pyfolder import post_iii_rch, linking_process
import calendar

def read_mf_nOflayers(self):
    QSWATMOD_path_dict = self.dirs_and_paths()
    # Find .dis file and read the number of layers
    for filename in glob.glob(str(QSWATMOD_path_dict['SMfolder'])+"/*.dis"):
        with open(filename, "r") as f:
            data = []
            for line in f.readlines():
                if not line.startswith("#"):
                    data.append(line.replace('\n', '').split())
        nlayer = int(data[0][0])
    lyList = [str(i+1) for i in range(nlayer)]
    self.dlg.comboBox_lyList.clear()
    self.dlg.comboBox_lyList.addItems(lyList)


def read_mf_head_dates(self):
    QSWATMOD_path_dict = self.dirs_and_paths()
    stdate, eddate, stdate_warmup, eddate_warmup = self.define_sim_period()
    wd = QSWATMOD_path_dict['SMfolder']
    startDate = stdate.strftime("%m-%d-%Y")

    try:
        if self.dlg.checkBox_head.isChecked() and self.dlg.radioButton_mf_results_d.isChecked():
            filename = "swatmf_out_MF_head"
            # Open "swatmf_out_MF_head" file
            y = ("MODFLOW", "--Calculated", "daily") # Remove unnecssary lines
            with open(os.path.join(wd, filename), "r") as f:
                data = [x.strip() for x in f if x.strip() and not x.strip().startswith(y)]  # Remove blank lines
            date = [x.strip().split() for x in data if x.strip().startswith("Day:")] # Collect only lines with dates
            onlyDate = [x[1] for x in date] # Only date
            # data1 = [x.split() for x in data] # make each line a list
            sdate = datetime.datetime.strptime(startDate, "%m-%d-%Y")  # Change startDate format
            dateList = [(sdate + datetime.timedelta(days = int(i)-1)).strftime("%m-%d-%Y") for i in onlyDate] 
        elif self.dlg.checkBox_head.isChecked() and self.dlg.radioButton_mf_results_m.isChecked():
            filename = "swatmf_out_MF_head_monthly"
            # Open "swatmf_out_MF_head" file
            y = ("Monthly") # Remove unnecssary lines
            with open(os.path.join(wd, filename), "r") as f:
                data = [x.strip() for x in f if x.strip() and not x.strip().startswith(y)] # Remove blank lines
            date = [x.strip().split() for x in data if x.strip().startswith("month:")]  # Collect only lines with dates
            onlyDate = [x[1] for x in date] # Only date
            # data1 = [x.split() for x in data] # make each line a list
            dateList = pd.date_range(startDate, periods=len(onlyDate), freq='M').strftime("%b-%Y").tolist()
        elif self.dlg.checkBox_head.isChecked() and self.dlg.radioButton_mf_results_y.isChecked():
            filename = "swatmf_out_MF_head_yearly"
            # Open "swatmf_out_MF_head" file
            y = ("Yearly") # Remove unnecssary lines
            with open(os.path.join(wd, filename), "r") as f:
                data = [x.strip() for x in f if x.strip() and not x.strip().startswith(y)] # Remove blank lines
            date = [x.strip().split() for x in data if x.strip().startswith("year:")] # Collect only lines with dates
            onlyDate = [x[1] for x in date] # Only date
            # data1 = [x.split() for x in data] # make each line a list
            dateList = pd.date_range(startDate, periods=len(onlyDate), freq='A').strftime("%Y").tolist()
        self.dlg.comboBox_mf_results_sdate.clear()
        self.dlg.comboBox_mf_results_sdate.addItems(dateList)
        self.dlg.comboBox_mf_results_edate.clear()
        self.dlg.comboBox_mf_results_edate.addItems(dateList)
        self.dlg.comboBox_mf_results_edate.setCurrentIndex(len(dateList)-1)
    except ValueError:
        self.main_messageBox("Error!", "Please, select one of the time options!")
        self.dlg.comboBox_mf_results_sdate.clear()
        self.dlg.comboBox_mf_results_edate.clear()

        
def get_grid_head_df(self):
    self.dlg.progressBar_rch_head.setValue(0)
    self.main_messageBox("Reading ...", "We are going to read head outputs ...")
    QSWATMOD_path_dict = self.dirs_and_paths()
    stdate, eddate, stdate_warmup, eddate_warmup = self.define_sim_period()
    wd = QSWATMOD_path_dict['SMfolder']
    startDate = stdate.strftime("%m-%d-%Y")
    # Open "swatmf_out_MF_head" file
    y = ("Monthly", "Yearly") # Remove unnecssary lines

    if self.dlg.radioButton_mf_results_m.isChecked():
        filename = "swatmf_out_MF_head_monthly"
        with open(os.path.join(wd, filename), "r") as f:
            data = [x.strip() for x in f if x.strip() and not x.strip().startswith(y)] # Remove blank lines     
        date = [x.strip().split() for x in data if x.strip().startswith("month:")] # Collect only lines with dates  
        onlyDate = [x[1] for x in date] # Only date
        data1 = [x.split() for x in data] # make each line a list
        dateList = pd.date_range(startDate, periods = len(onlyDate), freq = 'ME').strftime("%b-%Y").tolist()
    elif self.dlg.radioButton_mf_results_y.isChecked():
        filename = "swatmf_out_MF_head_yearly"
        with open(os.path.join(wd, filename), "r") as f:
            data = [x.strip() for x in f if x.strip() and not x.strip().startswith(y)] # Remove blank lines
        date = [x.strip().split() for x in data if x.strip().startswith("year:")] # Collect only lines with dates
        onlyDate = [x[1] for x in date] # Only date
        data1 = [x.split() for x in data] # make each line a list
        dateList = pd.date_range(startDate, periods = len(onlyDate), freq = 'YE').strftime("%Y").tolist()
    else:
        self.main_messageBox("Error!", "Please, select one of the time options!") 
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
        # if self.dlg.radioButton_mf_results_d.isChecked():
        #     for num, line in enumerate(data1, 1):
        #         if line[0] == "Day:" in line and line[1] == onlyDate_lookup in line:
        #             ii = num # Starting line
        if self.dlg.radioButton_mf_results_m.isChecked():
            # Find year 
            dt = datetime.datetime.strptime(selectedDate, "%b-%Y")
            year = dt.year
            layerN = self.dlg.comboBox_lyList.currentText()
            for num, line in enumerate(data1, 1):
                if ((line[0] == "month:" in line) and (line[1] == onlyDate_lookup in line) and (line[3] == str(year) in line)):
                    ii = num # Starting line
            count = 0
            # while ((data1[count+ii][0] != 'layer:') and (data1[count+ii][1] != layer)):  # why not working?
            while not ((data1[count+ii][0] == 'layer:') and (data1[count+ii][1] == layerN)):
                count += 1
            stline = count+ii+1
        elif self.dlg.radioButton_mf_results_y.isChecked():
            layerN = self.dlg.comboBox_lyList.currentText()
            for num, line in enumerate(data1, 1):
                if line[0] == "year:" in line and line[1] == onlyDate_lookup in line:
                    ii = num # Starting line
            count = 0
            while not ((data1[count+ii][0] == 'layer:') and (data1[count+ii][1] == layerN)):
                count += 1
            stline = count+ii+1
        mf_hds = []
        hdcount = 0
        while hdcount < input1.featureCount():
            for kk in range(len(data1[stline])):
                mf_hds.append(float(data1[stline][kk]))
                hdcount += 1
            stline += 1
        if self.dlg.radioButton_mf_results_m.isChecked():
            s = pd.Series(mf_hds, name=datetime.datetime.strptime(selectedDate, "%b-%Y").strftime("%b-%Y"))
            big_df = pd.concat([big_df, s], axis=1)
        elif self.dlg.radioButton_mf_results_y.isChecked():
            s = pd.Series(mf_hds, name=datetime.datetime.strptime(selectedDate, "%Y").strftime("%Y"))
            big_df = pd.concat([big_df, s], axis=1)
        datecount +=1
        provalue = round(datecount/len(dateList_f)*100)
        self.dlg.progressBar_rch_head.setValue(provalue)
        QCoreApplication.processEvents()
        self.dlg.raise_()        
    big_df.insert(0, 'grid_id', value=range(1, len(big_df) + 1))
    if self.dlg.radioButton_mf_results_m.isChecked():
        big_df.to_csv(os.path.join(QSWATMOD_path_dict["exported_files"], "mf_head_mon_table.csv"), index=False)
    elif self.dlg.radioButton_mf_results_y.isChecked():
        big_df.to_csv(os.path.join(QSWATMOD_path_dict["exported_files"], "mf_head_year_table.csv"), index=False)
    return big_df


def export_mf_head(self):
    self.dlg.progressBar_mf_results.setValue(0)
    if self.dlg.radioButton_mf_results_d.isChecked():
        layernam = "mf_head_day"
    elif self.dlg.radioButton_mf_results_m.isChecked():
        layernam = "mf_head_mon"
    elif self.dlg.radioButton_mf_results_y.isChecked():
        layernam = "mf_head_year"
    self.delete_layers([layernam])
    post_iii_rch.save_grid_as_vl(self, layernam)
    grid_result_tname = layernam
    df = get_grid_head_df(self)
    post_iii_rch.create_grid_result_tables(self, grid_result_tname, df)
    post_iii_rch.join_mf_grid_result(self, layernam, layernam)
    linking_process.cvt_vl_to_gpkg(
        self, layernam, f"{layernam}.gpkg", "swatmf_results")
    linking_process.delete_fields(self, layernam, "_2")
    self.dlg.progressBar_mf_results.setValue(100)
    self.main_messageBox(
        "Exported!", 
        f"'{layernam}' results were exported successfully!")        




def get_head_avg_m_df(self):
    msgBox = QMessageBox()
    msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
    msgBox.setWindowTitle("Reading ...")
    msgBox.setText("We are going to read the 'swatmf_out_MF_head_monthly file ...")
    msgBox.exec_()

    QSWATMOD_path_dict = self.dirs_and_paths()
    stdate, eddate, stdate_warmup, eddate_warmup = self.define_sim_period()
    wd = QSWATMOD_path_dict['SMfolder']
    exported_folder = QSWATMOD_path_dict["exported_files"]
    startDate = stdate.strftime("%m-%d-%Y")
    # Open "swatmf_out_MF_head" file
    y = ("Monthly", "Yearly") # Remove unnecssary lines
    filename = "swatmf_out_MF_head_monthly"
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
        layerN = self.dlg.comboBox_lyList.currentText()
        for num, line in enumerate(data1, 1):
            if ((line[0] == "month:" in line) and (line[1] == onlyDate_lookup in line) and (line[3] == str(year) in line)):
                ii = num # Starting line
        count = 0
        while not ((data1[count+ii][0] == 'layer:') and (data1[count+ii][1] == layerN)):
            count += 1
        stline =count+ii+1

        mf_rchs = []
        hdcount = 0
        while hdcount < input1.featureCount():
            for kk in range(len(data1[stline])):
                mf_rchs.append(float(data1[stline][kk]))
                hdcount += 1
            stline += 1
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
    mbig_df_t = mbig_df.T
    mbig_df_t["grid_id"] = mbig_df_t.index + 1
    mbig_df_t.to_csv(
        os.path.join(exported_folder, "mf_head_avg_mon.csv"), index=False)

    msgBox = QMessageBox()
    msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
    msgBox.setWindowTitle("Exported!")
    msgBox.setText("'mf_head_avg_mon.csv' was exported ...")
    msgBox.exec_()
    msgBox = QMessageBox()
    msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
    msgBox.setWindowTitle("Exporting ...")
    msgBox.setText("It will begin in exporting data to the shapefile.")
    msgBox.exec_()
    return mbig_df


def create_head_avg_mon_shp(self):
    input1 = QgsProject.instance().mapLayersByName("mf_grid (MODFLOW)")[0]
    QSWATMOD_path_dict = self.dirs_and_paths()

    # Copy mf_grid shapefile to swatmf_results tree
    name = "mf_head_avg_mon"
    name_ext = "mf_head_avg_mon.shp"
    output_dir = QSWATMOD_path_dict['SMshps']
    # Check if there is an exsting mf_head shapefile
    if not any(lyr.name() == (name) for lyr in list(QgsProject.instance().mapLayers().values())):
        mf_head_shp = os.path.join(output_dir, name_ext)
        QgsVectorFileWriter.writeAsVectorFormat(
            input1, mf_head_shp,
            "utf-8", input1.crs(), "ESRI Shapefile")
        layer = QgsVectorLayer(mf_head_shp, '{0}'.format(name), 'ogr')
        # Put in the group
        root = QgsProject.instance().layerTreeRoot()
        swatmf_results = root.findGroup("swatmf_results")
        QgsProject.instance().addMapLayer(layer, False)
        swatmf_results.insertChildNode(0, QgsLayerTreeLayer(layer))
        msgBox = QMessageBox()
        msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
        msgBox.setWindowTitle("Created!")
        msgBox.setText("'mf_head_avg_mon.shp' file has been created in 'swatmf_results' group!")
        msgBox.exec_()
        msgBox = QMessageBox()


def export_mf_head_avg_m(self):
    mbig_df = get_head_avg_m_df(self)
    # '''
    selected_months = post_iii_rch.selected_mf_mon(self)
    self.layer = QgsProject.instance().mapLayersByName("mf_head_avg_mon")[0]
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
    msgBox = QMessageBox()
    msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
    msgBox.setWindowTitle("Exported!")
    msgBox.setText("mf_head_avg_mon results were exported successfully!")
    msgBox.exec_()
    # '''