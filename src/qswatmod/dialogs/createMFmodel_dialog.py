# -*- coding: utf-8 -*-
#******************************************************************************
#
# Freewat
# ---------------------------------------------------------
# Copyright (C) 2014 - 2015 Iacopo Borsi (iacopo.borsi@tea-group.com)
#
# This source is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 2 of the License, or (at your option)
# any later version.
#
# This code is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# A copy of the GNU General Public License is available on the World Wide Web
# at <http://www.gnu.org/licenses/>. You can also obtain it by writing
# to the Free Software Foundation, 51 Franklin Street, Suite 500 Boston,
# MA 02110-1335 USA.
#
#******************************************************************************
from builtins import zip
from builtins import str
from builtins import range
import pandas as pd
import time
import sqlite3
import csv
import os
import os.path
import posixpath
import ntpath
import shutil
import glob
import processing
from qgis.utils import iface
from qgis.PyQt.QtSql import QSqlDatabase, QSqlQuery
from qgis.PyQt.QtCore import QCoreApplication, QVariant, QSettings, QFileInfo
from qgis.PyQt import QtGui, uic, QtCore, QtSql
import numpy as np
# import pandas as pd
from qgis.core import QgsProject, QgsFeatureRequest, QgsProcessingException
import distutils.dir_util
from datetime import datetime

from osgeo import gdal
from QSWATMOD2.QSWATMOD2 import *
from QSWATMOD2.QSWATMOD_dialog import QSWATMODDialog
from QSWATMOD2.pyfolder import modflow_functions
from QSWATMOD2.pyfolder import writeMF
from QSWATMOD2.pyfolder import db_functions
from QSWATMOD2.pyfolder import linking_process
from PyQt5.QtWidgets import (
            QInputDialog, QLineEdit, QDialog, QFileDialog,
            QMessageBox
)
from qgis.core import (
                    QgsProject, QgsVectorLayer, QgsVectorFileWriter, QgsField, 
                    QgsLayerTreeLayer, QgsRasterLayer
                    )
from PyQt5.QtCore import QTimer

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'ui/createMFmodel.ui'))
class createMFmodelDialog(QDialog, FORM_CLASS):
    def __init__(self, iface):
        QDialog.__init__(self)
        self.iface = iface
        self.setupUi(self)
        #------------------------------------------------------------------------------------------------
        # self.checkBox_ratio.setCheckState(self.Checked)
        self.pushButton_createMFfolder.clicked.connect(self.createMFfolder)
        self.pushButton_loadDEM.clicked.connect(self.loadDEM)
        self.pushButton_boundary.clicked.connect(self.import_mf_bd)
        self.checkBox_use_sub.toggled.connect(self.use_sub_shapefile)
        self.pushButton_create_MF_shps.clicked.connect(self.create_MF_shps)

        # -----------------------------------------------------------------------------------------------
        self.radioButton_aq_thic_single.toggled.connect(self.aqufierThickness_option)
        self.radioButton_aq_thic_uniform.toggled.connect(self.aqufierThickness_option)  
        self.radioButton_aq_thic_raster.toggled.connect(self.aqufierThickness_option)
        self.pushButton_aq_thic_raster.clicked.connect(self.loadBotElev)
        self.radioButton_hk_single.toggled.connect(self.hk_option)
        self.radioButton_hk_raster.toggled.connect(self.hk_option)
        self.pushButton_hk_raster.clicked.connect(self.loadHK)
        self.comboBox_layerType.clear()
        self.comboBox_layerType.addItems([' - Convertible - ', ' - Confined - '])
        self.radioButton_ss_single.toggled.connect(self.ss_option)
        self.radioButton_ss_raster.toggled.connect(self.ss_option)
        self.pushButton_ss_raster.clicked.connect(self.loadSS)
        self.radioButton_sy_single.toggled.connect(self.sy_option)
        self.radioButton_sy_raster.toggled.connect(self.sy_option)
        self.pushButton_sy_raster.clicked.connect(self.loadSY)
        self.radioButton_initialH_single.toggled.connect(self.initialH_option)
        self.radioButton_initialH_uniform.toggled.connect(self.initialH_option)
        self.radioButton_initialH_raster.toggled.connect(self.initialH_option)
        self.pushButton_initialH_raster.clicked.connect(self.loadInitialH)
        self.radioButton_evt_single.toggled.connect(self.evt_option)
        self.radioButton_evt_raster.toggled.connect(self.evt_option)
        self.pushButton_evt_raster.clicked.connect(self.loadEVT)
        self.pushButton_writeMF.clicked.connect(self.writeMF)
        self.DB_Pull_mf_inputs()  # instant call
        self.pushButton_reset.clicked.connect(self.DB_resetTodefaultVal)
        self.pushButton_create_mf_riv_shapefile.clicked.connect(self.create_mf_riv)
        # Retrieve info
        self.retrieve_ProjHistory_mf()
        # ----------------------------------------------------------------------
        self.doubleSpinBox_delc.valueChanged.connect(self.esti_ngrids)
        self.doubleSpinBox_delr.valueChanged.connect(self.esti_ngrids)
        self.doubleSpinBox_delc.valueChanged.connect(self.set_delr)
        # ----------------------------------------------------------------------
    # NOTE: QUESTIONS!! Is this function should be here too? ######
    def dirs_and_paths(self):
        global QSWATMOD_path_dict
        # project places
        Projectfolder = QgsProject.instance().readPath("./") 
        proj = QgsProject.instance() 
        Project_Name = QFileInfo(proj.fileName()).baseName()

        # definition of folders
        org_shps = os.path.normpath(Projectfolder + "/" + Project_Name + "/" + "GIS/org_shps")
        SMshps = os.path.normpath(Projectfolder + "/" + Project_Name + "/" + "GIS/SMshps")
        SMfolder = os.path.normpath(Projectfolder + "/" + Project_Name + "/" + "SWAT-MODFLOW")
        Table = os.path.normpath(Projectfolder + "/" + Project_Name + "/" + "GIS/Table")
        SM_exes = os.path.normpath(Projectfolder + "/" + Project_Name + "/" + "SM_exes")
        exported_files = os.path.normpath(Projectfolder + "/" + Project_Name + "/" + "exported_files")
        scn_folder = os.path.normpath(Projectfolder + "/" + Project_Name + "/" + "Scenarios")
        db_files = os.path.normpath(Projectfolder + "/" + Project_Name + "/" + "DB")  
        QSWATMOD_path_dict = {
                                'org_shps': org_shps,
                                'SMshps': SMshps,
                                'SMfolder': SMfolder,
                                'Table': Table,
                                'SM_exes': SM_exes,
                                'exported_files': exported_files,
                                'Scenarios': scn_folder,
                                'db_files': db_files}
        return QSWATMOD_path_dict

    # TODO: we are going to use sqlite for MODFLOW parameter settings
    def DB_Pull_mf_inputs(self):
        db = db_functions.db_variable(self)      
        query = QtSql.QSqlQuery(db)
        query.exec_("SELECT user_val FROM mf_inputs WHERE parNames = 'ss' ")
        LK = str(query.first()) # What does LK do?
        self.lineEdit_ss_single.setText(str(query.value(0)))

    # ...
    def DB_push_mf_userVal(self):
        db = db_functions.db_variable(self)
        query = QtSql.QSqlQuery(db)
        query.prepare("UPDATE mf_inputs SET user_val = :UP1 WHERE parNames = 'ss'")
        query.bindValue (":UP1", self.lineEdit_ss_single.text())
        query.exec_() 

    def DB_resetTodefaultVal(self):
        msgBox = QMessageBox()
        msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
        response = msgBox.question(
            self, 'Set to default?',
            "Are you sure you want to reset the current aquifer property settings to the default values?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if response == QMessageBox.Yes:
            db = db_functions.db_variable(self)      
            query = QtSql.QSqlQuery(db)
            query.exec_("SELECT default_val FROM mf_inputs WHERE parNames = 'ss' ")
            LK = str(query.first())
            self.lineEdit_ss_single.setText(str(query.value(0)))
            self.DB_push_mf_userVal()

    def retrieve_ProjHistory_mf(self):
        QSWATMOD_path_dict = self.dirs_and_paths()
        # Define folders and files
        SMfolder = QSWATMOD_path_dict['SMfolder']
        org_shps = QSWATMOD_path_dict['org_shps']
        SMshps = QSWATMOD_path_dict['SMshps']
        # retrieve DEM
        if os.path.isfile(os.path.join(org_shps, 'DEM.tif')):
            self.lineEdit_loadDEM.setText(os.path.join(org_shps, 'DEM.tif'))
        else:
            self.textEdit_mf_log.append("* Provide DEM raster file.")

    def start_time(self, desc):
        time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
        self.textEdit_mf_log.append(time+' -> ' + f"{desc} ... processing")
        self.label_mf_status.setText(f"{desc} ... ")
        self.progressBar_mf_status.setValue(0)
        QCoreApplication.processEvents()

    def end_time(self, desc):
        time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
        self.textEdit_mf_log.append(time+' -> ' + f"{desc} ... passed")
        self.label_mf_status.setText('Step Status: ')
        self.progressBar_mf_status.setValue(100)
        QCoreApplication.processEvents()

    def createMFfolder(self):
        settings = QSettings()
        if settings.contains('/QSWATMOD2/LastInputPath'):
            path = str(settings.value('/QSWATMOD2/LastInputPath'))
        else:
            path = ''
        options = QFileDialog.DontResolveSymlinks | QFileDialog.ShowDirsOnly
        title = "create MODFLOW folder"
        mffolder = QFileDialog.getExistingDirectory(None, title, path, options)
        mffolder_path = self.lineEdit_createMFfolder.setText(mffolder)

        return mffolder_path

    # navigate to the DEM raster from SWAT
    def loadDEM(self):
        geovar_path = writeMF.load_geovar_raster(self, geovar='top_elev')
        self.lineEdit_loadDEM.setText(geovar_path)

    def loadHK(self):
        # writeMF.loadHK(self)
        geovar_path = writeMF.load_geovar_raster(self, geovar='hk')
        self.lineEdit_hk_raster.setText(geovar_path)

    def loadBotElev(self):
        geovar_path = writeMF.load_geovar_raster(self, geovar='bot_elev')
        self.lineEdit_aq_thic_raster.setText(geovar_path)

    def loadSS(self):
        geovar_path = writeMF.load_geovar_raster(self, geovar='ss')
        self.lineEdit_ss_raster.setText(geovar_path)

    def loadSY(self):
        geovar_path = writeMF.load_geovar_raster(self, geovar='sy')
        self.lineEdit_sy_raster.setText(geovar_path)

    def loadInitialH(self):
        geovar_path = writeMF.load_geovar_raster(self, geovar='ih')
        self.lineEdit_initialH_raster.setText(geovar_path)

    def loadEVT(self):
        geovar_path = writeMF.load_geovar_raster(self, geovar='evt')
        self.lineEdit_evt_raster.setText(geovar_path)

    def import_mf_bd(self):
    # Initiate function
        QSWATMOD_path_dict = self.dirs_and_paths()
        settings = QSettings()
        if settings.contains('/QSWATMOD2/LastInputPath'):
            path = str(settings.value('/QSWATMOD2/LastInputPath'))
        else:
            path = ''
        title = "Choose MODFLOW Grid Geopackage or Shapefile!"
        inFileName, __ = QFileDialog.getOpenFileNames(
            None, title, path,
            "Geopackages or Shapefiles (*.gpkg *.shp);;All files (*.*)"
            )
        if inFileName:
            settings.setValue('/QSWATMOD2/LastInputPath', os.path.dirname(str(inFileName)))
            output_dir = QSWATMOD_path_dict['org_shps']
            inInfo = QFileInfo(inFileName[0])
            inFile = inInfo.fileName()
            pattern = os.path.splitext(inFileName[0])[0] + '.*'

            # inName = os.path.splitext(inFile)[0]
            inName = 'mf_bd_org'
            for f in glob.iglob(pattern):
                suffix = os.path.splitext(f)[1]
                if os.name == 'nt':
                    outfile = ntpath.join(output_dir, inName + suffix)
                else:
                    outfile = posixpath.join(output_dir, inName + suffix)
                shutil.copy(f, outfile)
            # check suffix whether .gpkg or .shp
            if suffix == ".gpkg":
                if os.name == 'nt':
                    mf_bd_obj = ntpath.join(output_dir, inName + ".gpkg")
                else:
                    mf_bd_obj = posixpath.join(output_dir, inName + ".gpkg")
            else:
                if os.name == 'nt':
                    mf_bd_obj = ntpath.join(output_dir, inName + ".shp")
                else:
                    mf_bd_obj = posixpath.join(output_dir, inName + ".shp")    
            # convert to gpkg
            mf_bd_gpkg_file = 'mf_bd.gpkg'
            mf_bd_gpkg = os.path.join(output_dir, mf_bd_gpkg_file)
            params = {
                'INPUT': mf_bd_obj,
                'OUTPUT': mf_bd_gpkg
            }
            processing.run('native:fixgeometries', params)
            layer = QgsVectorLayer(mf_bd_gpkg, '{0} ({1})'.format("mf_boundary","MODFLOW"), 'ogr')        

            # if there is an existing mf_grid shapefile, it will be removed
            for lyr in list(QgsProject.instance().mapLayers().values()):
                if lyr.name() == ("mf_boundary (MODFLOW)"):
                    QgsProject.instance().removeMapLayers([lyr.id()])

            # Put in the group
            root = QgsProject.instance().layerTreeRoot()
            swat_group = root.findGroup("MODFLOW")  
            QgsProject.instance().addMapLayer(layer, False)
            swat_group.insertChildNode(0, QgsLayerTreeLayer(layer))
            self.lineEdit_boundary.setText(mf_bd_gpkg)

    # NOTE: clear about gpkg or shp
    def use_sub_shapefile(self):
        QSWATMOD_path_dict = self.dirs_and_paths()

        try:
            input1 = QgsProject.instance().mapLayersByName("sub (SWAT)")[0]
            #provider = layer.dataProvider()
            if self.checkBox_use_sub.isChecked():
                name = "mf_boundary"
                name_ext = "mf_boundary.shp"
                output_dir = QSWATMOD_path_dict['org_shps']
                mf_boundary = os.path.join(output_dir, name_ext)
                params = {
                    'INPUT': input1,
                    'OUTPUT': mf_boundary
                }
                processing.run("native:dissolve", params)

                # defining the outputfile to be loaded into the canvas
                layer = QgsVectorLayer(mf_boundary, '{0} ({1})'.format("mf_boundary","MODFLOW"), 'ogr')

                # Put in the group
                root = QgsProject.instance().layerTreeRoot()
                mf_group = root.findGroup("MODFLOW")    
                QgsProject.instance().addMapLayer(layer, False)
                mf_group.insertChildNode(0, QgsLayerTreeLayer(layer))
                #subpath = layer.source()
                self.lineEdit_boundary.setText(mf_boundary)

        except:
            msgBox = QMessageBox()
            msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
            msgBox.setWindowTitle("Error!")
            msgBox.setText("There is no 'sub' shapefile!")
            msgBox.exec_()
            # self.dlg.checkBox_default_extent.setChecked(0)
        # return layer


    def get_attribute_to_dataframe(self, layer):
        #List all columns you want to include in the dataframe. I include all with:
        cols = [f.name() for f in layer.fields()] #Or list them manually: ['kommunnamn', 'kkod', ... ]
        #A generator to yield one row at a time
        datagen = ([f[col] for col in cols] for f in layer.getFeatures())
        df = pd.DataFrame.from_records(data=datagen, columns=cols)
        return df

    def delete_layers(self, layer_names):
        for lyr in list(QgsProject.instance().mapLayers().values()):
            if lyr.name() in layer_names:
                lyr_source = lyr.source()
                QgsProject.instance().removeMapLayers([lyr.id()])
                time.sleep(1)
                if os.path.exists(lyr_source):
                    os.remove(lyr_source)
                self.iface.mapCanvas().refreshAllLayers()
                self.iface.mapCanvas().refresh()
                

    def create_MF_grid(self):
        # Create fishnet based on user inputs
        desc = "Creating MODFLOW grids"
        self.start_time(desc) 
        QSWATMOD_path_dict = self.dirs_and_paths()
        input1 = QgsProject.instance().mapLayersByName("mf_boundary (MODFLOW)")[0]
        ext = input1.extent()
        xmin = ext.xMinimum()
        xmax = ext.xMaximum()
        ymin = ext.yMinimum()
        ymax = ext.yMaximum()
        delc = float(self.doubleSpinBox_delc.value())
        delr = float(self.doubleSpinBox_delr.value())
        # Add_Subtract number of column, row
        n_row = self.spinBox_row.value()
        n_col = self.spinBox_col.value()
        if self.groupBox_mf_add.isChecked():
            xmax = xmax + (delc * n_col)
            ymin = ymin - (delr * n_row)
            nx = round(abs(abs(xmax) - abs(xmin)) / delc)
            ny = round(abs(abs(ymax) - abs(ymin)) / delr)            
        else:
            nx = round(abs(abs(xmax) - abs(xmin)) / delc)
            ny = round(abs(abs(ymax) - abs(ymin)) / delr)
        ngrid = abs(int(nx*ny))
        MF_extent = "{a},{b},{c},{d}".format(a=xmin, b=xmax, c=ymin, d=ymax)
        crs = input1.crs()
        # running the acutal routine:
        outnam = 'mf_grid (MODFLOW)'
        params_ = {
            'TYPE': 2,
            'EXTENT': MF_extent,
            'HSPACING': delc,
            'VSPACING': delr,
            'CRS': crs,
            'OUTPUT': f"memory:{outnam}"
        }

        mf_grid_lyr = processing.run("native:creategrid", params_)
        mf_grid_lyr = mf_grid_lyr['OUTPUT']

        # Put in the group  
        root = QgsProject.instance().layerTreeRoot()
        mf_group = root.findGroup("MODFLOW")
        QgsProject.instance().addMapLayer(mf_grid_lyr, False)
        mf_group.insertChildNode(0, QgsLayerTreeLayer(mf_grid_lyr))
        self.end_time(desc)

        desc = "Fixing starting index"
        self.start_time(desc)
        # rasterize
        # rasterize
        name_ext_r = 'mf_grid_.tif'
        output_dir = QSWATMOD_path_dict['org_shps']
        output_file_r = os.path.normpath(os.path.join(output_dir, name_ext_r))
        params_r = {
            'INPUT': mf_grid_lyr.source(),
            'UNITS': 1,
            'WIDTH': delc,
            'HEIGHT': delr,
            'EXTENT': MF_extent,
            'NODATA': -9999,
            'DATA_TYPE': 5,
            'OUTPUT': output_file_r
        }
        processing.run("gdal:rasterize", params_r)
        for lyr in list(QgsProject.instance().mapLayers().values()):
            if lyr.name() == ("mf_grid (MODFLOW)"):
                QgsProject.instance().removeMapLayers([lyr.id()])
        # vecterize
        name_ext_v = 'mf_grid.gpkg'
        output_file_v = os.path.normpath(os.path.join(output_dir, name_ext_v))
        #
        params_v = {
            'INPUT_RASTER': output_file_r,
            'RASTER_BAND': 1,
            'FIELD': 'VALUE',
            'OUTPUT': output_file_v
        }
        processing.run("native:pixelstopolygons", params_v)
        self.end_time(desc)

    def mf_grid_layer(self):
        output_dir = QSWATMOD_path_dict['org_shps']
        name_ext_v = 'mf_grid.gpkg'
        output_file_v = os.path.normpath(os.path.join(output_dir, name_ext_v))
        layer = QgsVectorLayer(output_file_v, '{0} ({1})'.format("mf_grid","MODFLOW"), 'ogr')
        return layer

    def get_numb_of_colunm(self):
        layer = self.mf_grid_layer()
        x_cords = []
        for feat in layer.getFeatures():
            # Get the geometry of the feature
            geom = feat.geometry()
            polygon = geom.asPolygon()

            for i, point in enumerate(polygon[0]):
                if i == 0:
                    x_cords.append(point.x())
        unique_list = list(set(x_cords))
        numb_of_col = len(unique_list)
        return numb_of_col

    def create_mf_db(self):
        layer = self.mf_grid_layer()
        numb_of_col = self.get_numb_of_colunm()
        df = self.get_attribute_to_dataframe(layer)
        tot_feats = len(df)
        df["grid_id"] = df.iloc[:, 0]
        numb_of_row = int(tot_feats / numb_of_col)
        # Get row and column lists
        iy = [] # row
        ix = [] # col
        for nrow in range(numb_of_row):
            for ncol in range(numb_of_col):
                iy.append(nrow+1)
                ix.append(ncol+1)
        df["row"] = iy
        df["col"] = ix
        output_dir = QSWATMOD_path_dict['db_files']
        if os.path.exists(os.path.join(output_dir, 'mf.db')):
            os.remove(os.path.join(output_dir, 'mf.db'))
        connection = sqlite3.connect(os.path.join(output_dir, 'mf.db')) # Creates a new file if it doesn't exist
        df.to_sql('mf_db', connection, if_exists='replace', index=False)
        connection.close()

    def join_mf_grid_db(self):
        layer = self.mf_grid_layer()
        output_dir = QSWATMOD_path_dict['org_shps']
        db_dir = QSWATMOD_path_dict['db_files']
        mf_grid_join = os.path.join(output_dir, 'mf_grid_f.gpkg')

        params = {
            'INPUT': layer.source(),
            'FIELD': 'fid',
            'INPUT_2': os.path.join(db_dir, "mf.db|layername=mf_db"),
            'FIELD_2': 'grid_id',
            'FIELDS_TO_COPY': ['grid_id', 'row', 'col'],
            'METHOD': 1,
            'DISCARD_NONMATCHING': False,
            'PREFIX': '',
            'OUTPUT': mf_grid_join
        }
        processing.run("native:joinattributestable", params)

    def mf_grid_layer_f(self):
        output_dir = QSWATMOD_path_dict['org_shps']
        name_ext_v = 'mf_grid_f.gpkg'
        output_file_v = os.path.normpath(os.path.join(output_dir, name_ext_v))
        layer = QgsVectorLayer(output_file_v, '{0} ({1})'.format("mf_grid","MODFLOW"), 'ogr')
        return layer


    #  ======= Update automatically when 1:1 ratio is checked
    def set_delr(self, value):
        if self.checkBox_ratio.isChecked():
            self.doubleSpinBox_delr.setValue(value)

    # ======= Estimate number of grid cells
    def esti_ngrids(self):
        import math
        input1 = QgsProject.instance().mapLayersByName("mf_boundary (MODFLOW)")[0]

        try:
            ext = input1.extent()
            xmin = ext.xMinimum()
            xmax = ext.xMaximum()
            ymin = ext.yMinimum()
            ymax = ext.yMaximum()

            delc = float(self.doubleSpinBox_delc.value())
            delr = float(self.doubleSpinBox_delr.value())
            if delc != 0 and delr != 0:
                nx = math.ceil(abs(abs(xmax) - abs(xmin)) / delc)
                ny = math.ceil(abs(abs(ymax) - abs(ymin)) / delr) 
                ngrid = abs(int(nx*ny))
            else:
                ngrid = ' '
        except:
            ngrid = ' '
        self.lcdNumber_numberOfgrids.display(str(ngrid))

    # ========== createMF_active
    def create_mf_act_grid(self):
        desc = "Creating active MODFLOW grids"
        self.start_time(desc)
        # self.delete_layer("mf_act_grid (MODFLOW)")
        QSWATMOD_path_dict = self.dirs_and_paths()
        input1 = self.mf_grid_layer_f()
        input2 = QgsProject.instance().mapLayersByName("mf_boundary (MODFLOW)")[0]

        name = "mf_grid_act"
        name_ext = "mf_grid_act.gpkg"
        output_dir = QSWATMOD_path_dict['org_shps']

        # output_file = os.path.normpath(os.path.join(output_dir, name))
        # Select features by location
        params = { 
            'INPUT' : input1,
            'PREDICATE': [0],
            'INTERSECT': input2,
            'METHOD': 0,
        }
        processing.run('qgis:selectbylocation', params)        
        # Save just the selected features of the target layer
        mf_grid_act = os.path.join(output_dir, name_ext)

        # Extract selected features
        processing.run(
            "native:saveselectedfeatures",
            {'INPUT': input1, 'OUTPUT':mf_grid_act}
        )
        # Deselect the features
        input1.removeSelection()
        self.end_time(desc)
        
    def mf_act_grid_layer(self):
        output_dir = QSWATMOD_path_dict['org_shps']
        name_ext_v = 'mf_grid_act.gpkg'
        output_file_v = os.path.normpath(os.path.join(output_dir, name_ext_v))
        layer = QgsVectorLayer(output_file_v, '{0} ({1})'.format("mf_act_grid","MODFLOW"), 'ogr')
        return layer


    def only_mf_grid_fields(self):
        layer = self.mf_grid_layer_f()
        fields = layer.dataProvider()
        fdname = [
                fields.fields().indexFromName(field.name()) for field in fields.fields() if not (
                    (field.name() == 'fid') or
                    (field.name() == 'grid_id') or
                    (field.name() == 'row') or
                    (field.name() == 'col') or
                    (field.name() == 'top_elev')
                    )
                ]
        fields.deleteAttributes(fdname)
        layer.updateFields()

    def create_MF_shps(self):
        layer_names = ["mf_grid (MODFLOW)", "top_elev (MODFLOW)", "mf_act_grid (MODFLOW)"]
        self.delete_layers(layer_names)
        self.iface.mapCanvas().refreshAllLayers()
        self.progressBar_mf.setValue(0)
        self.create_MF_grid()
        # self.check_mf_grid()
        self.progressBar_mf.setValue(30)
        QCoreApplication.processEvents()
        # Extract elevation

        # it works as F5 !! Be careful to use this for long geoprocessing
        self.create_mf_db()
        self.join_mf_grid_db()
        # Extract elevation
        self.progressBar_mf.setValue(50)
        QCoreApplication.processEvents()
        self.only_mf_grid_fields()
        writeMF.getElevfromDem(self)
        # Get active cells
        self.create_mf_act_grid()
        writeMF.cvt_geovarToR(self, 'top_elev', geovar_group='DATA')
        self.progressBar_mf.setValue(70)
        QCoreApplication.processEvents()
        self.mf_act_grid_delete_NULL()
        QCoreApplication.processEvents()

        QCoreApplication.processEvents()
        # Put in the group

        layer = self.mf_grid_layer_f()
        root = QgsProject.instance().layerTreeRoot()
        mf_group = root.findGroup("MODFLOW")    
        QgsProject.instance().addMapLayer(layer, False)
        mf_group.insertChildNode(0, QgsLayerTreeLayer(layer))
        layer_act = self.mf_act_grid_layer()
        QgsProject.instance().addMapLayer(layer_act, False)
        mf_group.insertChildNode(0, QgsLayerTreeLayer(layer_act))

        time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
        self.textEdit_mf_log.append(time+' -> ' + 'Done!')
        self.progressBar_mf.setValue(100)
        QCoreApplication.processEvents()
        '''
        ''' 
        self.iface.mapCanvas().refreshAllLayers()
        self.iface.mapCanvas().refresh()
        msgBox = QMessageBox()
        msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
        msgBox.setWindowTitle("Created!")
        msgBox.setText("MODFLOW grids and rasters were created!")
        msgBox.exec_()
        self.iface.mapCanvas().refreshAllLayers()

    def mf_act_grid_delete_NULL(self):
        desc = "Deleting nulls"
        self.start_time(desc)
        ## old way
        # layer = QgsProject.instance().mapLayersByName("mf_act_grid (MODFLOW)")[0]
        # params = {
        #     'INPUT': layer,
        #     'EXPRESSION': '"top_elev" is NULL',
        #     'METHOD': 0
        # }
        # processing.run(
        #     "qgis:selectbyexpression", 
        #     params)
        ## ---

        layer = self.mf_act_grid_layer()
        request =  QgsFeatureRequest().setFilterExpression('"top_elev" IS NULL' )
        request.setSubsetOfAttributes([])
        request.setFlags(QgsFeatureRequest.NoGeometry)
        listOfIds = [f.id() for f in layer.getFeatures(request)]
        # layer.deleteFeature(listOfIds)
        layer.startEditing()
        layer.dataProvider().deleteFeatures( listOfIds )
        # for f in layer.getFeatures(request):
        #     layer.deleteFeature(f.id())
        #     count += 1
        #     provalue = round(count/tot_feats*100)
        #     self.progressBar_mf_status.setValue(provalue)
        #     QCoreApplication.processEvents()
        layer.commitChanges()
        self.end_time(desc)


    def create_mf_riv_old(self):
        layer_names = ["mf_riv2 (MODFLOW)", "river_grid (SWAT-MODFLOW)"]
        self.delete_layers(layer_names)
        output_dir = QSWATMOD_path_dict['org_shps']
        name_ext_v = 'mf_riv2.gpkg'
        if os.path.exists(os.path.join(output_dir, name_ext_v)):
            os.remove(os.path.join(output_dir, name_ext_v))
        ### ============================================ why!!!!!!!!!!!!!!!!!!!!!!!!
        self.dlg = QSWATMODDialog()
        self.dlg.groupBox_river_cells.setEnabled(True) # not working
        self.dlg.radioButton_mf_riv2.setChecked(1) # not working
        ### ============================================        
        modflow_functions.mf_riv2(self)
        linking_process.river_grid(self)
        linking_process.river_grid_delete_NULL(self)
        linking_process.rgrid_len(self)
        linking_process.delete_river_grid_with_threshold(self)
        modflow_functions.rivInfoTo_mf_riv2_ii(self)
        modflow_functions.riv_cond_delete_NULL(self)
        writeMF.create_layer_inRiv(self)
        linking_process.export_rgrid_len(self)
        QCoreApplication.processEvents()

        msgBox = QMessageBox()
        msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
        msgBox.setWindowTitle("Identified!")
        msgBox.setText("River cells have been identified!")
        msgBox.exec_()

    # CREATE MF_RIV
    def create_mf_riv(self):
        layer_names = ["mf_riv2 (MODFLOW)", "river_grid (SWAT-MODFLOW)"]
        self.delete_layers(layer_names)
        self.iface.mapCanvas().refreshAllLayers()
        self.mf_riv2()
        self.river_grid()
        self.river_grid_delete_NULL()
        self.rgrid_len()
        self.delete_river_grid_with_threshold()
        self.rivInfoTo_mf_riv2_ii()
        self.riv_cond_delete_NULL()
        self.create_layer_inRiv()
        self.export_rgrid_len()
        QCoreApplication.processEvents()

        root = QgsProject.instance().layerTreeRoot()
        mf_riv2_layer = self.mf_riv2_layer()
        mf_group = root.findGroup("MODFLOW")
        QgsProject.instance().addMapLayer(mf_riv2_layer, False)
        mf_group.insertChildNode(0, QgsLayerTreeLayer(mf_riv2_layer))
        river_grid_layer = self.river_grid_layer()
        sm_group = root.findGroup("SWAT-MODFLOW")
        QgsProject.instance().addMapLayer(river_grid_layer, False)
        sm_group.insertChildNode(0, QgsLayerTreeLayer(river_grid_layer))
        self.iface.mapCanvas().refreshAllLayers()
        msgBox = QMessageBox()
        msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
        msgBox.setWindowTitle("Identified!")
        msgBox.setText("River cells have been identified!")
        msgBox.exec_()


    def mf_riv2(self):  
        QSWATMOD_path_dict = self.dirs_and_paths()
        input1 = QgsProject.instance().mapLayersByName("mf_grid (MODFLOW)")[0]
        input2 = QgsProject.instance().mapLayersByName("riv (SWAT)")[0]
        name = "mf_riv2"
        name_ext = "mf_riv2.gpkg"
        output_dir = QSWATMOD_path_dict['org_shps']
        # Select features by location
        params = { 
            'INPUT' : input1,
            'PREDICATE': [0],
            'INTERSECT': input2,
            'METHOD': 0,
        }
        processing.run('qgis:selectbylocation', params)

        # Save just the selected features of the target layer
        riv_swat_shp = os.path.join(output_dir, name_ext)

        # Extract selected features
        processing.run(
            "native:saveselectedfeatures",
            {'INPUT': input1, 'OUTPUT':riv_swat_shp, 'OVERWRITE': True}
        )
        # Deselect the features
        input1.removeSelection()

    def mf_riv2_layer(self):
        QSWATMOD_path_dict = self.dirs_and_paths()
        output_dir = QSWATMOD_path_dict['org_shps']
        name_ext_v = 'mf_riv2.gpkg'
        output_file_v = os.path.normpath(os.path.join(output_dir, name_ext_v))
        layer = QgsVectorLayer(output_file_v, '{0} ({1})'.format("mf_riv2","MODFLOW"), 'ogr')
        return layer

    def river_grid(self):
        input1 = QgsProject.instance().mapLayersByName("riv (SWAT)")[0]
        input2 = self.mf_riv2_layer()
        name = "river_grid"
        name_ext = "river_grid.gpkg"
        output_dir = QSWATMOD_path_dict['SMshps']
        output_file = os.path.normpath(os.path.join(output_dir, name_ext))
        # runinng the actual routine:
        params = { 
            'INPUT' : input1,
            'OVERLAY' : input2, 
            'OUTPUT' : output_file,
            'OVERWRITE': True
        }
        processing.run('qgis:intersection', params)

    def river_grid_layer(self):
        QSWATMOD_path_dict = self.dirs_and_paths()
        output_dir = QSWATMOD_path_dict['SMshps']
        name_ext_v = 'river_grid.gpkg'
        output_file_v = os.path.normpath(os.path.join(output_dir, name_ext_v))
        layer = QgsVectorLayer(output_file_v, '{0} ({1})'.format("river_grid","SWAT-MODFLOW"), 'ogr')
        return layer   

    def river_grid_delete_NULL(self):
        layer = self.river_grid_layer()
        provider = layer.dataProvider()
        request =  QgsFeatureRequest().setFilterExpression("grid_id IS NULL" )
        request.setSubsetOfAttributes([])
        request.setFlags(QgsFeatureRequest.NoGeometry)
        request2 = QgsFeatureRequest().setFilterExpression("subbasin IS NULL" )
        request2.setSubsetOfAttributes([])
        request2.setFlags(QgsFeatureRequest.NoGeometry)

        layer.startEditing()
        for f in layer.getFeatures(request):
            layer.deleteFeature(f.id())
        for f in layer.getFeatures(request2):
            layer.deleteFeature(f.id())
        layer.commitChanges()

    def rgrid_len(self):
        layer = self.river_grid_layer()
        provider = layer.dataProvider()
        field = QgsField("rgrid_len", QVariant.Int)
        provider.addAttributes([field])
        layer.updateFields()
        feats = layer.getFeatures()
        layer.startEditing()
        for feat in feats:
            length = feat.geometry().length()
            #score = scores[i]
            feat['rgrid_len'] = length
            layer.updateFeature(feat)
        layer.commitChanges()

    def delete_river_grid_with_threshold(self):
        layer = self.river_grid_layer()
        provider = layer.dataProvider()
        request =  QgsFeatureRequest().setFilterExpression('"rgrid_len" < 0.5')
        request.setSubsetOfAttributes([])
        request.setFlags(QgsFeatureRequest.NoGeometry)
        layer.startEditing()
        for f in layer.getFeatures(request):
            layer.deleteFeature(f.id())
        layer.commitChanges()

    def rivInfoTo_mf_riv2_ii(self):
        QSWATMOD_path_dict = self.dirs_and_paths()
        # try:
        river_grid = self.river_grid_layer()
        provider1 = river_grid.dataProvider()

        # Get the index numbers of the fields
        grid_id_idx = provider1.fields().indexFromName("grid_id")
        width_idx = provider1.fields().indexFromName("Wid2")
        depth_idx = provider1.fields().indexFromName("Dep2")
        row_idx = provider1.fields().indexFromName("row")
        col_idx = provider1.fields().indexFromName("col")
        elev_idx = provider1.fields().indexFromName("top_elev")
        length_idx = provider1.fields().indexFromName("rgrid_len")         

        # transfer the shapefile layer to a python list 
        l = []
        for i in river_grid.getFeatures():
            l.append(i.attributes())

        # then sort by grid_id
        import operator
        l_sorted = sorted(l, key=operator.itemgetter(grid_id_idx))

        # Extract grid_ids and layers as lists
        grid_ids = [g[grid_id_idx] for g in l_sorted]
        widths = [w[width_idx] for w in l_sorted]
        depths = [d[depth_idx] for d in l_sorted]
        rows = [r[row_idx] for r in l_sorted]
        cols = [c[col_idx] for c in l_sorted]
        elevs = [e[elev_idx] for e in l_sorted]
        lengths = [leng[length_idx] for leng in l_sorted]

        data = pd.DataFrame({
            "grid_id" : grid_ids,
            "Wid2" : widths,
            "Dep2" : depths,
            "row" : rows,
            "col" : cols,
            "top_elev" : elevs,
            "rgrid_len" : lengths
            })
        hk = self.lineEdit_riverbedK2.text()
        rivBedthick = self.lineEdit_riverbedThick2.text()
        width_sum = data.groupby(["grid_id"])["Wid2"].sum()
        depth_avg = data.groupby(["grid_id"])["Dep2"].mean()
        row_avg = data.groupby(["grid_id"])["row"].mean().astype(int)   
        col_avg = data.groupby(["grid_id"])["col"].mean().astype(int)   
        elev_avg = data.groupby(["grid_id"])["top_elev"].mean()
        length_sum = data.groupby(["grid_id"])["rgrid_len"].sum()

        riv2_cond = float(hk)*length_sum*width_sum / float(rivBedthick)
        riv2_stage = elev_avg + depth_avg + float(rivBedthick)
        riv2_bot = elev_avg + float(rivBedthick)

        # Convert dataframe to lists
        row_avg_lst = row_avg.values.tolist()
        col_avg_lst = col_avg.tolist()
        riv2_cond_lst = riv2_cond.tolist()
        riv2_stage_lst = riv2_stage.tolist()
        riv2_bot_lst = riv2_bot.tolist()

        # Part II ---------------------------------------------------------------
        layer = self.mf_riv2_layer()
        provider2 = layer.dataProvider()

        # from qgis.core import QgsField, QgsExpression, QgsFeature
        if layer.dataProvider().fields().indexFromName("riv_stage") == -1:
            field = QgsField("riv_stage", QVariant.Double, 'double', 20, 5)
            provider2.addAttributes([field])
            layer.updateFields()

        # Obtain col number
        if layer.dataProvider().fields().indexFromName( "riv_cond" ) == -1:
            field = QgsField("riv_cond", QVariant.Double, 'double', 20, 5)
            provider2.addAttributes([field])
            layer.updateFields()

        # Obtain col number
        if layer.dataProvider().fields().indexFromName( "riv_bot" ) == -1:
            field = QgsField("riv_bot", QVariant.Double, 'double', 20, 5)
            provider2.addAttributes([field])
            layer.updateFields()

        # Get the index numbers of the fields
        riv_stage = provider2.fields().indexFromName("riv_stage")
        riv_cond = provider2.fields().indexFromName("riv_cond")
        riv_bot = provider2.fields().indexFromName("riv_bot")  

        feats = layer.getFeatures()
        layer.startEditing()

        # add riv_info based on row and column numbers
        for f in feats:
            rowNo = f.attribute("row")
            colNo = f.attribute("col")
            for ii in range(len(riv2_cond_lst)):
                if ((rowNo == (row_avg_lst[ii])) and (colNo == (col_avg_lst[ii]))):
                    layer.changeAttributeValue(f.id(), riv_stage, float(riv2_stage_lst[ii])) # why without float is not working?
                    layer.changeAttributeValue(f.id(), riv_cond, float(riv2_cond_lst[ii]))             
                    layer.changeAttributeValue(f.id(), riv_bot, float(riv2_bot_lst[ii]))
        layer.commitChanges()
        QCoreApplication.processEvents()

    def riv_cond_delete_NULL(self):
        layer = self.mf_riv2_layer()
        provider = layer.dataProvider()
        request =  QgsFeatureRequest().setFilterExpression("riv_cond IS NULL" )
        request.setSubsetOfAttributes([])
        request.setFlags(QgsFeatureRequest.NoGeometry)
        layer.startEditing()
        for f in layer.getFeatures(request):
            layer.deleteFeature(f.id())
        layer.commitChanges()

    def create_layer_inRiv(self):
        layer = self.mf_riv2_layer()
        provider = layer.dataProvider()
        if layer.dataProvider().fields().indexFromName( "layer" ) == -1:
            field = QgsField("layer", QVariant.Int)
            provider.addAttributes([field])
            layer.updateFields()
        feats = layer.getFeatures()
        layer.startEditing()
        for feat in feats:
            layer_num = 1
            feat['layer'] = layer_num
            layer.updateFeature(feat)
        layer.commitChanges()

    def export_rgrid_len(self):
        QSWATMOD_path_dict = self.dirs_and_paths()  
        ### sort by dhru_id and then by grid and save down ### 
        #read in the dhru shapefile
        layer = self.river_grid_layer()
        # Get the index numbers of the fields
        grid_id_index = layer.dataProvider().fields().indexFromName("grid_id")
        subbasin_index = layer.dataProvider().fields().indexFromName("Subbasin")
        ol_length_index = layer.dataProvider().fields().indexFromName("ol_length")
        
        # transfer the shapefile layer to a python list
        l = []
        for i in layer.getFeatures():
            l.append(i.attributes())
        
        # then sort by columns
        import operator
        l_sorted = sorted(l, key=operator.itemgetter(grid_id_index))
        
        info_number = len(l_sorted) # number of lines
        #-----------------------------------------------------------------------#
        # exporting the file 
        name = "river_grid"
        output_dir = QSWATMOD_path_dict['Table']   
        output_file = os.path.normpath(os.path.join(output_dir, name))

        with open(output_file, "w", newline='') as f:
            writer = csv.writer(f, delimiter = '\t')
            first_row = [str(info_number)] # prints the dhru number to the file
            second_row = ["grid_id subbasin rgrid_len"]
            writer.writerow(first_row)
            writer.writerow(second_row)
            for item in l_sorted:
                # Write item to outcsv. the order represents the output order
                writer.writerow([item[grid_id_index], item[subbasin_index], item[ol_length_index]])

    #-------------------------------------------------------------------------------
    def aqufierThickness_option(self):
        # Single
        if self.radioButton_aq_thic_single.isChecked():
            self.lineEdit_aq_thic_single.setEnabled(True)
            self.lineEdit_aq_thic_uniform.setEnabled(False)
            self.lineEdit_aq_thic_raster.setEnabled(False)
            self.pushButton_aq_thic_raster.setEnabled(False)

        # Uniform
        elif self.radioButton_aq_thic_uniform.isChecked():
            self.lineEdit_aq_thic_uniform.setEnabled(True)
            self.lineEdit_aq_thic_single.setEnabled(False)
            self.lineEdit_aq_thic_raster.setEnabled(False)
            self.pushButton_aq_thic_raster.setEnabled(False)

        # Raster
        elif self.radioButton_aq_thic_raster.isChecked():
            self.lineEdit_aq_thic_raster.setEnabled(True)
            self.pushButton_aq_thic_raster.setEnabled(True) 
            self.lineEdit_aq_thic_single.setEnabled(False)
            self.lineEdit_aq_thic_uniform.setEnabled(False)

        # else:
        #   self.lineEdit_aq_thic_single.setEnabled(False)
        #   self.lineEdit_aq_thic_uniform.setEnabled(False)
        #   self.lineEdit_aq_thic_raster.setEnabled(False)
        #   self.pushButton_aq_thic_raster.setEnabled(False)    

    def hk_option(self):
        if self.radioButton_hk_single.isChecked():
            self.lineEdit_hk_single.setEnabled(True)
            self.lineEdit_vka.setEnabled(True)
            self.comboBox_layerType.setEnabled(True)
            self.lineEdit_hk_raster.setEnabled(False)
            self.pushButton_hk_raster.setEnabled(False)

        elif self.radioButton_hk_raster.isChecked():
            self.lineEdit_hk_raster.setEnabled(True)
            self.pushButton_hk_raster.setEnabled(True)
            self.lineEdit_vka.setEnabled(True)
            self.comboBox_layerType.setEnabled(True)
            self.lineEdit_hk_single.setEnabled(False)
        # else:
        #   self.lineEdit_hk_single.setEnabled(False)

    def ss_option(self):
        if self.radioButton_ss_single.isChecked():
            self.lineEdit_ss_single.setEnabled(True)
            self.lineEdit_ss_raster.setEnabled(False)
            self.pushButton_ss_raster.setEnabled(False)
        elif self.radioButton_ss_raster.isChecked():
            self.lineEdit_ss_raster.setEnabled(True)
            self.pushButton_ss_raster.setEnabled(True)
            self.lineEdit_ss_single.setEnabled(False)           

    def sy_option(self):
        if self.radioButton_sy_single.isChecked():
            self.lineEdit_sy_single.setEnabled(True)
            self.lineEdit_sy_raster.setEnabled(False)
            self.pushButton_sy_raster.setEnabled(False)
        else:
            self.lineEdit_sy_raster.setEnabled(True)
            self.pushButton_sy_raster.setEnabled(True)
            self.lineEdit_sy_single.setEnabled(False)           

    def initialH_option(self):
        if self.radioButton_initialH_single.isChecked():
            self.lineEdit_initialH_single.setEnabled(True)
            self.lineEdit_initialH_uniform.setEnabled(False)
            self.lineEdit_initialH_raster.setEnabled(False)
            self.pushButton_initialH_raster.setEnabled(False)
        elif self.radioButton_initialH_uniform.isChecked():
            self.lineEdit_initialH_single.setEnabled(False)
            self.lineEdit_initialH_uniform.setEnabled(True)
            self.lineEdit_initialH_raster.setEnabled(False)
            self.pushButton_initialH_raster.setEnabled(False)           
        else:
            self.lineEdit_initialH_single.setEnabled(False)
            self.lineEdit_initialH_uniform.setEnabled(False)
            self.lineEdit_initialH_raster.setEnabled(True)
            self.pushButton_initialH_raster.setEnabled(True)

    def evt_option(self):
        if self.radioButton_evt_single.isChecked():
            self.lineEdit_evt_single.setEnabled(True)
            self.lineEdit_evt_raster.setEnabled(False)
            self.pushButton_evt_raster.setEnabled(False)
        else:
            self.lineEdit_evt_single.setEnabled(False)
            self.lineEdit_evt_raster.setEnabled(True)
            self.pushButton_evt_raster.setEnabled(True)

    def writeMF(self):
        self.DB_push_mf_userVal()
        from QSWATMOD2.pyfolder.writeMF import extentlayer
        self.textEdit_mf_log.append(" ")
        self.textEdit_mf_log.append("- Exporting MODFLOW input files...")
        self.checkBox_mfPrepared.setChecked(0)
        self.progressBar_mf.setValue(0)

        # bottom elevation
        if (self.radioButton_aq_thic_single.isChecked() or self.radioButton_aq_thic_uniform.isChecked()):
            writeMF.createBotElev(self)
            writeMF.cvt_geovarToR(self, geovar="bot_elev")
        elif (self.radioButton_aq_thic_raster.isChecked() and self.lineEdit_aq_thic_raster.text()):
            writeMF.get_geovar_fromR(self, geovar="bot_elev")
            writeMF.cvt_geovarToR(self, geovar="bot_elev")
        else:
            self.progressBar_mf.setValue(5)
            QCoreApplication.processEvents()
        self.progressBar_mf.setValue(10)
        QCoreApplication.processEvents()

        # Bottom
        # if (self.radioButton_aq_thic_single.isChecked() or self.radioButton_aq_thic_uniform.isChecked()):
        #     writeMF.createBotElev(self) # create bottom elevation in mf_act_grid_layer
        #     self.progressBar_mf.setValue(10)
        #     QCoreApplication.processEvents()
        #     writeMF.cvtBotElevToR(self) # convert bottom elevation to raster
        #     self.progressBar_mf.setValue(20)
        #     QCoreApplication.processEvents()
            
        # HK
        if (self.radioButton_hk_single.isChecked() and self.lineEdit_hk_single.text()):
            writeMF.createHK(self)
            writeMF.cvt_geovarToR(self, geovar="hk")
        elif (self.radioButton_hk_raster.isChecked() and self.lineEdit_hk_raster.text()):
            writeMF.get_geovar_fromR(self, geovar="hk")
            writeMF.cvt_geovarToR(self, geovar="hk")
        else:
            self.progressBar_mf.setValue(25)
            QCoreApplication.processEvents()
        self.progressBar_mf.setValue(30)
        QCoreApplication.processEvents()

        # SS
        if (self.radioButton_ss_single.isChecked() and self.lineEdit_ss_single.text()):
            writeMF.createSS(self)
            writeMF.cvt_geovarToR(self, geovar="ss")
        elif (self.radioButton_ss_raster.isChecked() and self.lineEdit_ss_raster.text()):
            writeMF.get_geovar_fromR(self, geovar="ss")
            writeMF.cvt_geovarToR(self, geovar="ss")
        else:
            self.progressBar_mf.setValue(45)
            QCoreApplication.processEvents()
        self.progressBar_mf.setValue(50)
        QCoreApplication.processEvents()

        # SY
        if (self.radioButton_sy_single.isChecked() and self.lineEdit_sy_single.text()):
            writeMF.createSY(self)
            writeMF.cvt_geovarToR(self, geovar="sy")
        elif (self.radioButton_sy_raster.isChecked() and self.lineEdit_sy_raster.text()):
            writeMF.get_geovar_fromR(self, geovar="sy")
            writeMF.cvt_geovarToR(self, geovar="sy")
        else:
            self.progressBar_mf.setValue(65)
            QCoreApplication.processEvents()
        self.progressBar_mf.setValue(70)
        QCoreApplication.processEvents()        
        # IH
        if (self.radioButton_initialH_single.isChecked() or self.radioButton_initialH_uniform.isChecked()):
            writeMF.createInitialH(self)
            writeMF.cvt_geovarToR(self, geovar="ih")
        elif (self.radioButton_initialH_raster.isChecked() and self.lineEdit_initialH_raster.text()):
            writeMF.get_geovar_fromR(self, geovar="ih")
            writeMF.cvt_geovarToR(self, geovar="ih")        
        else:
            self.progressBar_mf.setValue(80)
            QCoreApplication.processEvents()
        self.progressBar_mf.setValue(85)
        QCoreApplication.processEvents()
        # EVT
        if self.groupBox_evt.isChecked():
            if (self.radioButton_evt_single.isChecked() and self.lineEdit_evt_single.text()):
                writeMF.createEVT(self)
                writeMF.cvt_geovarToR(self, geovar="evt")
            elif (self.radioButton_evt_raster.isChecked() and self.lineEdit_evt_raster.text()):
                writeMF.get_geovar_fromR(self, geovar="evt")
                writeMF.cvt_geovarToR(self, geovar="evt")
                self.progressBar_mf.setValue(80)
                QCoreApplication.processEvents()
            else:
                self.progressBar_mf.setValue(85)
                QCoreApplication.processEvents()           
        writeMF.writeMFmodel(self)
        self.progressBar_mf.setValue(100)
        self.checkBox_mfPrepared.setChecked(1)


