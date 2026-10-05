# -*- coding: utf-8 -*-
from builtins import str
from qgis.PyQt.QtCore import QFileInfo
from qgis.core import QgsProject                      
import os

### Please, someone teaches me how to use a function in QSWATMOD2 main script file.
#  from QSWATMOD2.QSWATMOD2 import *
def retrieve_ProjHistory(self):
    QSWATMOD_path_dict = self.dirs_and_paths()
    # Define folders and files
    SMfolder = QSWATMOD_path_dict['SMfolder']
    org_shps = QSWATMOD_path_dict['org_shps']
    SMshps = QSWATMOD_path_dict['SMshps']
    # retrieve TxtInOut
    if os.path.isfile(os.path.join(SMfolder, "file.cio")):
        stdate, eddate, stdate_warmup, eddate_warmup = self.define_sim_period()
        self.dlg.tabWidget.setTabEnabled(1, True)
        ##### 
        start_month = stdate.strftime("%b")
        start_day = stdate.strftime("%d")
        start_year = stdate.strftime("%Y")
        end_month = eddate.strftime("%b")
        end_day = eddate.strftime("%d")
        end_year = eddate.strftime("%Y")
        # Put dates into the gui
        self.dlg.lineEdit_start_m.setText(start_month)
        self.dlg.lineEdit_start_d.setText(start_day)
        self.dlg.lineEdit_start_y.setText(start_year)
        self.dlg.lineEdit_end_m.setText(end_month)
        self.dlg.lineEdit_end_d.setText(end_day)
        self.dlg.lineEdit_end_y.setText(end_year)
        duration = (eddate - stdate).days
        self.dlg.lineEdit_duration.setText(str(duration))
        self.dlg.lineEdit_TxtInOut.setText(SMfolder)
    else:
        self.dlg.textEdit_sm_link_log.append("Missing -> Provide SWAT model.")
    # retrieve hru
    if os.path.isfile(os.path.join(org_shps, 'hru_SM.shp')):
        self.dlg.lineEdit_hru_shapefile.setText(os.path.join(org_shps, 'hru_SM.shp'))
    elif os.path.isfile(os.path.join(org_shps, 'hru_SM.gpkg')):
        self.dlg.lineEdit_hru_shapefile.setText(os.path.join(org_shps, 'hru_SM.gpkg'))
    else:
        self.dlg.textEdit_sm_link_log.append("Provide hru Shapefile.")
    # retrieve sub
    if os.path.isfile(os.path.join(org_shps, 'sub_SM.shp')):
        self.dlg.lineEdit_subbasin_shapefile.setText(os.path.join(org_shps, 'sub_SM.shp'))
    elif os.path.isfile(os.path.join(org_shps, 'sub_SM.gpkg')):
        self.dlg.lineEdit_subbasin_shapefile.setText(os.path.join(org_shps, 'sub_SM.gpkg'))
    else:
        self.dlg.textEdit_sm_link_log.append("Provide sub Shapefile.")
    # retrieve riv
    if os.path.isfile(os.path.join(org_shps, 'riv_SM.shp')):
        self.dlg.lineEdit_river_shapefile.setText(os.path.join(org_shps, 'riv_SM.shp'))
    elif os.path.isfile(os.path.join(org_shps, 'riv_SM.gpkg')):
        self.dlg.lineEdit_river_shapefile.setText(os.path.join(org_shps, 'riv_SM.gpkg'))
    else:
        self.dlg.textEdit_sm_link_log.append("Provide riv Shapefile.")      
    # retrieve MODFLOW model
    if any(file.endswith(".dis") for file in os.listdir(SMfolder)):
        self.dlg.lineEdit_MODFLOW.setText(SMfolder)
    else:
        self.dlg.textEdit_sm_link_log.append("Provide MODFLOW model")
    # retrieve MODFLOW grid shapefile (MODFLOW)
    for lyr in list(QgsProject.instance().mapLayers().values()):
        if lyr.name() == ("mf_grid (MODFLOW)"):
            # self.dlg.mGroupBox.setCollapsed(False)
            self.dlg.mf_option_1.setChecked(True)
            self.dlg.lineEdit_MODFLOW_grid_shapefile.setText(lyr.source())
    # retrieve mf_obs_points (MODFLOW)
    for lyr in list(QgsProject.instance().mapLayers().values()):
        if lyr.name() == ("mf_obs_points (MODFLOW)"):
            # self.dlg.mGroupBox.setCollapsed(False)
            self.dlg.groupBox_obs_points.setChecked(True)
            self.dlg.lineEdit_mf_obs_points.setText(lyr.source())
        elif lyr.name() == ("mf_obs (SWAT-MODFLOW)"):
            self.dlg.lineEdit_mf_obs_shapefile.setText(lyr.source())
    # retrieve MODFLOW model
    if any(file.endswith(".dis") for file in os.listdir(SMfolder)):
        self.dlg.lineEdit_MODFLOW.setText(SMfolder)
        self.dlg.groupBox_MF_options.setEnabled(True)
        self.dlg.mf_option_1.setEnabled(True)
        self.dlg.mf_option_2.setEnabled(True)           
        self.dlg.mf_option_3.setEnabled(False)
        self.dlg.groupBox_river_cells.setEnabled(True)
        self.dlg.river_frame.setEnabled(False)
        self.dlg.radioButton_mf_riv3.setEnabled(False)  
    else:
        self.dlg.mf_option_1.setEnabled(False)
        self.dlg.mf_option_2.setEnabled(False)          
        self.dlg.mf_option_3.setEnabled(True)   
        self.dlg.textEdit_sm_link_log.append("Provide MODFLOW model")
    # if os.path.isfile(os.path.join(SMfolder, "modflow.mfn")):
    # retrieve linkge files
    linkfiles = ["swatmf_dhru2grid.txt", "swatmf_dhru2hru.txt", "swatmf_grid2dhru.txt", "swatmf_river2grid.txt"]
    if all(os.path.isfile(os.path.join(SMfolder, x)) for x in linkfiles):
        self.dlg.pushButton_execute_linking.setEnabled(False)
        self.dlg.progressBar_sm_link.setValue(100)
        self.dlg.checkBox_filesPrepared.setChecked(1)
        self.dlg.tabWidget.setTabEnabled(2, True)
    else:
        self.dlg.pushButton_execute_linking.setEnabled(True)
        self.dlg.progressBar_sm_link.setValue(0)
        self.dlg.checkBox_filesPrepared.setChecked(0)
    # retrive SWAT-MODFLOW result files
    output_files = ["swatmf_link.txt", "output.rch"]
    if all(os.path.isfile(os.path.join(SMfolder, x)) for x in output_files):
        self.dlg.tabWidget.setTabEnabled(3, True)
    else:
        self.dlg.tabWidget.setTabEnabled(3, False)


def wt_act(self):
    QSWATMOD_path_dict = self.dirs_and_paths()
    # Define folders and files
    SMfolder = QSWATMOD_path_dict['SMfolder']
    # retrive swatmf_out_MF_obs
    if os.path.isfile(os.path.join(SMfolder, "modflow.obs")):
        self.dlg.checkBox_mf_obs.setChecked(True)
        self.dlg.groupBox_plot_wt.setEnabled(True)
    else:
        self.dlg.groupBox_plot_wt.setEnabled(False)
# def check_SMfolder_and_files(self):
#   check_txtinout = os.path.join(QSWATMOD_path_dict['SMfolder'], "file.cio")
#   if os.path.isfile(check_txtinout) is True:
#       self.dlg.lineEdit_TxtInOut.setText(QSWATMOD_path_dict['SMfolder'])
#   check_hrushp = os.path.join(QSWATMOD_path_dict['org_shps'], 'hru_SM.shp')
#   if os.path.isfile(check_hrushp) is True:
#       self.dlg.lineEdit_hru_shapefile.setText(check_hrushp)