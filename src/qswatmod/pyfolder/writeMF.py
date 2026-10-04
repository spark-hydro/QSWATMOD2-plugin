# -*- coding: utf-8 -*-

from builtins import str
import os
import os.path
from qgis.PyQt import QtCore, QtGui, QtSql
import processing
from qgis.core import (
                        QgsVectorLayer, QgsField,
                        QgsFeatureIterator, QgsVectorFileWriter,
                        QgsRasterLayer, QgsProject, QgsLayerTreeLayer
                        )
import glob
import posixpath
import ntpath
import shutil
from qgis.PyQt.QtCore import QVariant, QFileInfo, QSettings, QCoreApplication
from datetime import datetime
from PyQt5.QtWidgets import (
            QInputDialog, QLineEdit, QDialog, QFileDialog,
            QMessageBox
)
from QSWATMOD2.modules import flopy


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

def messageBox(self, title, message):
    msgBox = QMessageBox()
    msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))  
    msgBox.setWindowTitle(title)
    msgBox.setText(message)
    msgBox.exec_()

def extentlayer(self): # ----> why is not working T,.T
    extlayer = QgsProject.instance().mapLayersByName("mf_grid (MODFLOW)")[0]
    # get extent
    ext = extlayer.extent()
    xmin = ext.xMinimum()
    xmax = ext.xMaximum()
    ymin = ext.yMinimum()
    ymax = ext.yMaximum()
    extent = "{a},{b},{c},{d}".format(a=xmin, b=xmax, c=ymin, d=ymax)
    return extent

def createBotElev(self):
    desc = "Creating bottom elevation"
    start_time(self, desc)
    layer = self.mf_act_grid_layer()
    provider = layer.dataProvider()
    try:
        if provider.fields().indexFromName("bot_elev") != -1:
            attrIdx = provider.fields().indexFromName( "bot_elev" )
            provider.deleteAttributes([attrIdx])
            field = QgsField("bot_elev", QVariant.Double,'double', 20, 5)
        elif provider.fields().indexFromName("bot_elev" ) == -1:
            field = QgsField("bot_elev", QVariant.Double,'double', 20, 5)
        provider.addAttributes([field])
        layer.updateFields()
        feats = layer.getFeatures()
        layer.startEditing()

        # Single value
        if (self.radioButton_aq_thic_single.isChecked() and self.lineEdit_aq_thic_single.text()):
            depth = float(self.lineEdit_aq_thic_single.text())
            for f in feats:
                f['bot_elev'] = - depth + f['top_elev']
                layer.updateFeature(f)
            layer.commitChanges()
            self.time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
            self.textEdit_mf_log.append(self.time+' -> ' + 'Aquifer thickness is entered ...')
        # Uniform value
        elif (self.radioButton_aq_thic_uniform.isChecked() and self.lineEdit_aq_thic_uniform.text()):
            elev = float(self.lineEdit_aq_thic_uniform.text())
            for f in feats:
                f['bot_elev'] = elev
                layer.updateFeature(f)
            layer.commitChanges()
            self.time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
            self.textEdit_mf_log.append(self.time+' -> ' + 'Aquifer thickness is entered ...')
        else:
            messageBox(self, "Oops!", "Please, provide a value of the Aquifer thickness!")
        end_time(self, desc)
        QCoreApplication.processEvents()
    except:
        messageBox(self, "Oops!", "ERROR!!!")


def cvtBotElevToR(self):
    desc = "Converting bottom elevation to raster"
    start_time(self, desc)
    QSWATMOD_path_dict = self.dirs_and_paths()
    for lyr in list(QgsProject.instance().mapLayers().values()):
        if lyr.name() == ("bot_elev (MODFLOW)"):
            QgsProject.instance().removeMapLayers([lyr.id()])
    extlayer = self.mf_grid_layer()
    input1 = self.mf_act_grid_layer()
    input2 = QgsProject.instance().mapLayersByName("top_elev (MODFLOW)")[0]
    # Get pixel size from top_elev raster
    delc = input2.rasterUnitsPerPixelX()
    delr = input2.rasterUnitsPerPixelY()
    # get extent
    ext = extlayer.extent()
    xmin = ext.xMinimum()
    xmax = ext.xMaximum()
    ymin = ext.yMinimum()
    ymax = ext.yMaximum()
    extent = "{a},{b},{c},{d}".format(a=xmin, b = xmax, c = ymin, d = ymax)
    name = 'bot_elev'
    name_ext = "bot_elev.tif"
    output_dir = QSWATMOD_path_dict['org_shps']
    output_raster = os.path.join(output_dir, name_ext)

    if (self.radioButton_aq_thic_raster.isChecked() and self.lineEdit_aq_thic_raster.text()):
        params = {
            'INPUT': input1,
            'FIELD': "bot_mean",
            'UNITS': 1,
            'WIDTH': delc,
            'HEIGHT': delr,
            'EXTENT': extent,
            'NODATA': -9999,
            'DATA_TYPE': 5,
            'OUTPUT': output_raster
        }
    else:
        params = {
            'INPUT': input1,
            'FIELD': "bot_elev",
            'UNITS': 1,
            'WIDTH': delc,
            'HEIGHT': delr,
            'EXTENT': extent,
            'NODATA': -9999,
            'DATA_TYPE': 5,
            'OUTPUT': output_raster
        }
    processing.run("gdal:rasterize", params)
    layer = QgsRasterLayer(output_raster, '{0} ({1})'.format("bot_elev", "MODFLOW"))
        
    # Put in the group
    root = QgsProject.instance().layerTreeRoot()
    mf_group = root.findGroup("MODFLOW")    
    QgsProject.instance().addMapLayer(layer, False)
    mf_group.insertChildNode(0, QgsLayerTreeLayer(layer))
    end_time(self, desc)
    QCoreApplication.processEvents()

# navigate to the bot_elev raster
def loadBotElev(self):
    QSWATMOD_path_dict = self.dirs_and_paths()
    settings = QSettings()
    if settings.contains('/QSWATMOD2/LastInputPath'):
        path = str(settings.value('/QSWATMOD2/LastInputPath'))
    else:
        path = ''
    title = "Choose Bottom Elevation Rasterfile"
    inFileName, __ = QFileDialog.getOpenFileName(None, title, path, "Rasterfiles (*.tif);; All files (*.*)")

    if inFileName:
        settings.setValue('/QSWATMOD2/LastInputPath', os.path.dirname(str(inFileName)))
        Out_folder = QSWATMOD_path_dict['org_shps']
        inInfo = QFileInfo(inFileName)
        inFile = inInfo.fileName()
        pattern = os.path.splitext(inFileName)[0] + '.*'
        baseName = inInfo.baseName()

        # inName = os.path.splitext(inFile)[0]
        inName = 'bot_elev'
        for f in glob.iglob(pattern):
            suffix = os.path.splitext(f)[1]
            if os.name == 'nt':
                outfile = ntpath.join(Out_folder, inName + suffix)
            else:
                outfile = posixpath.join(Out_folder, inName + suffix)                    
            shutil.copy(f, outfile)
    
        if os.name == 'nt':
            bot_elev = ntpath.join(Out_folder, inName + ".tif")
        else:
            bot_elev = posixpath.join(Out_folder, inName + ".tif")

        # Delete existing "bot_elev (MODFLOW)" raster file"
        for lyr in list(QgsProject.instance().mapLayers().values()):
            if lyr.name() == ("bot_elev (DATA)"):
                QgsProject.instance().removeMapLayers([lyr.id()])
        layer = QgsRasterLayer(bot_elev, '{0} ({1})'.format("bot_elev", "DATA"))
        # Put in the group
        root = QgsProject.instance().layerTreeRoot()
        mf_group = root.findGroup("MODFLOW")    
        QgsProject.instance().addMapLayer(layer, False)
        mf_group.insertChildNode(0, QgsLayerTreeLayer(layer))
        self.lineEdit_aq_thic_raster.setText(bot_elev)

def getBotfromR(self):
    input1 = self.mf_act_grid_layer()
    input2 = QgsProject.instance().mapLayersByName("bot_elev (DATA)")[0]
    provider1 = input1.dataProvider()
    provider2 = input2.dataProvider()
    rpath = provider2.dataSourceUri()
    if provider1.fields().indexFromName("bot_mean") != -1:
        attrIdx = provider1.fields().indexFromName("bot_mean")
        provider1.deleteAttributes([attrIdx])
    params = {
        'INPUT_RASTER': input2,
        'RASTER_BAND':1,
        'INPUT_VECTOR': input1,
        'COLUMN_PREFIX':'elev_',
        'STATS':[2]            
    }    
    processing.run("qgis:zonalstatistics", params)
    time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
    self.textEdit_mf_log.append(time+' -> ' + 'Extrating Bottom Elevation from Raster has been finished...')

# ----------------------------------------------------------------------------------------------
def cvt_geovarToR(self, geovar, geovar_group="MODFLOW"):
    desc = f"Converting {geovar} to raster"
    start_time(self, desc)
    QSWATMOD_path_dict = self.dirs_and_paths()
    for lyr in list(QgsProject.instance().mapLayers().values()):
        if lyr.name() == f"{geovar} ({geovar_group})":
            QgsProject.instance().removeMapLayers([lyr.id()])
    extlayer = self.mf_grid_layer()
    input1 = self.mf_act_grid_layer()

    if geovar == "top_elev":
        delc = float(self.doubleSpinBox_delc.value())
        delr = float(self.doubleSpinBox_delr.value())
    else:
        input2 = QgsProject.instance().mapLayersByName(f"top_elev ({geovar_group})")[0]
        # Get pixel size from top_elev raster
        delc = input2.rasterUnitsPerPixelX()
        delr = input2.rasterUnitsPerPixelY()

    # get extent
    ext = extlayer.extent()
    xmin = ext.xMinimum()
    xmax = ext.xMaximum()
    ymin = ext.yMinimum()
    ymax = ext.yMaximum()
    extent = "{a},{b},{c},{d}".format(a=xmin, b=xmax, c=ymin, d=ymax)
    name = f'{geovar}'
    name_ext = f"{geovar}.tif"
    output_dir = QSWATMOD_path_dict['org_shps']
    output_raster = os.path.join(output_dir, name_ext)
    params = {
        'INPUT': input1,
        'FIELD': f"{geovar}",
        'UNITS': 1,
        'WIDTH': delc,
        'HEIGHT': delr,
        'EXTENT': extent,
        'NODATA': -9999,
        'DATA_TYPE': 5,
        'OUTPUT': output_raster
    }
    processing.run("gdal:rasterize", params)
    layer = QgsRasterLayer(output_raster, '{0} ({1})'.format(f"{geovar}","MODFLOW"))
    # Put in the group
    root = QgsProject.instance().layerTreeRoot()
    mf_group = root.findGroup("MODFLOW")    
    QgsProject.instance().addMapLayer(layer, False)
    mf_group.insertChildNode(0, QgsLayerTreeLayer(layer))
    self.iface.mapCanvas().refreshAllLayers()
    end_time(self, desc)    

def get_geovar_fromR(self, geovar):
    input1 = self.mf_act_grid_layer()
    input2 = QgsProject.instance().mapLayersByName(f"{geovar} (DATA)")[0]
    provider1 = input1.dataProvider()
    provider2 = input2.dataProvider()
    rpath = provider2.dataSourceUri()
    fields_to_delete = [
                    f"{geovar}_mean", f"{geovar}", f"{geovar}_count", 
                    f"{geovar}_sum", f"{geovar}_min", f"{geovar}_max"
                    ]
    for field in fields_to_delete:
        if provider1.fields().indexFromName(field) != -1:
            attrIdx = provider1.fields().indexFromName(field)
            provider1.deleteAttributes([attrIdx])    
    params = {
        'INPUT_RASTER': input2,
        'RASTER_BAND':1,
        'INPUT_VECTOR': input1,
        'COLUMN_PREFIX':f'{geovar}_',
        'STATS':[2]            
        }      
    processing.run("qgis:zonalstatistics", params)
    # Change name
    for field in input1.fields():
        if field.name() == f'{geovar}_mean':
            input1.startEditing()
            idx = provider1.fields().indexFromName(field.name())
            input1.renameAttribute(idx, f"{geovar}")
            input1.commitChanges()
    fields_to_delete = [
                f"{geovar}_mean", f"{geovar}_count", f"{geovar}_sum", 
                f"{geovar}_min", f"{geovar}_max"]
    for field in fields_to_delete:
        if provider1.fields().indexFromName(field) != -1:
            attrIdx = provider1.fields().indexFromName(field)
            provider1.deleteAttributes([attrIdx])    
    self.iface.mapCanvas().refreshAllLayers()
    time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
    self.textEdit_mf_log.append(time+' -> ' + f'Extrating {geovar} from Raster has been finished...')


def getElevfromDem(self):
    decs = "Extracting elevation from DEM"
    geovar = "top_elev"
    self.start_time(decs)

    input1 = self.mf_grid_layer_f()
    provider = input1.dataProvider()
    input2 = QgsProject.instance().mapLayersByName("top_elev (DATA)")[0]
    fields_to_delete = [
                    f"{geovar}_mean", f"{geovar}", f"{geovar}_count", 
                    f"{geovar}_sum", f"{geovar}_min", f"{geovar}_max"
                    ]
    for field in fields_to_delete:
        if provider.fields().indexFromName(field) != -1:
            attrIdx = provider.fields().indexFromName(field)
            provider.deleteAttributes([attrIdx])    
    params = {
        'INPUT_RASTER': input2,
        'RASTER_BAND':1,
        'INPUT_VECTOR': input1,
        'COLUMN_PREFIX':f'{geovar}_',
        'STATS':[2]            
    }
    processing.run("qgis:zonalstatistics", params)
    # Change name
    for field in input1.fields():
        if field.name() == f'{geovar}_mean':
            input1.startEditing()
            idx = provider.fields().indexFromName(field.name())
            input1.renameAttribute(idx, f"{geovar}")
            input1.commitChanges()
    fields_to_delete = [
                f"{geovar}_mean", f"{geovar}_count", f"{geovar}_sum", 
                f"{geovar}_min", f"{geovar}_max"]
    for field in fields_to_delete:
        if provider.fields().indexFromName(field) != -1:
            attrIdx = provider.fields().indexFromName(field)
            provider.deleteAttributes([attrIdx])    
    self.iface.mapCanvas().refreshAllLayers()
    self.end_time(decs)


def load_geovar_raster(self, geovar):
    QSWATMOD_path_dict = self.dirs_and_paths()
    settings = QSettings()
    if settings.contains('/QSWATMOD2/LastInputPath'):
        path = str(settings.value('/QSWATMOD2/LastInputPath'))
    else:
        path = ''
    title = f"Choose {geovar} Rasterfile"
    inFileName, __ = QFileDialog.getOpenFileName(None, title, path, "Rasterfiles (*.tif);; All files (*.*)")

    if inFileName:
        settings.setValue('/QSWATMOD2/LastInputPath', os.path.dirname(str(inFileName)))
        Out_folder = QSWATMOD_path_dict['org_shps']
        inInfo = QFileInfo(inFileName)
        inFile = inInfo.fileName()
        pattern = os.path.splitext(inFileName)[0] + '.*'
        baseName = inInfo.baseName()

        # inName = os.path.splitext(inFile)[0]
        inName = f'{geovar}'
        for f in glob.iglob(pattern):
            suffix = os.path.splitext(f)[1]
            if os.name == 'nt':
                outfile = ntpath.join(Out_folder, inName + suffix)
            else:
                outfile = posixpath.join(Out_folder, inName + suffix)
            shutil.copy(f, outfile)
        if os.name == 'nt':
            geovar_path = ntpath.join(Out_folder, inName + ".tif")
        else:
            hk = posixpath.join(Out_folder, inName + ".tif")

        # Delete existing "bot_elev (MODFLOW)" raster file"
        for lyr in list(QgsProject.instance().mapLayers().values()):
            if lyr.name() == (f"{geovar} (DATA)"):
                QgsProject.instance().removeMapLayers([lyr.id()])

        layer = QgsRasterLayer(geovar_path, '{0} ({1})'.format(f"{geovar}", "DATA"))
        # Put in the group
        root = QgsProject.instance().layerTreeRoot()
        mf_group = root.findGroup("MODFLOW")
        QgsProject.instance().addMapLayer(layer, False)
        mf_group.insertChildNode(0, QgsLayerTreeLayer(layer))
    return geovar_path
        
# ----------------------------------------------------------------------------------------------
def createHK(self):
    self.layer = self.mf_act_grid_layer()
    provider = self.layer.dataProvider()
    try:
        if provider.fields().indexFromName("hk") != -1:
            attrIdx = provider.fields().indexFromName("hk")
            provider.deleteAttributes([attrIdx])
        field = QgsField("hk", QVariant.Double,'double', 20, 5)
        provider.addAttributes([field])
        self.layer.updateFields()
        feats = self.layer.getFeatures()
        self.layer.startEditing()
        if (self.radioButton_hk_single.isChecked() and self.lineEdit_hk_single.text()):
            hk = float(self.lineEdit_hk_single.text())
            for f in feats:
                f['hk'] = hk
                self.layer.updateFeature(f)
            self.layer.commitChanges()
            self.time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
            self.textEdit_mf_log.append(self.time+' -> ' + 'Horizantal Hydraulic Conductivity is entered ...')
        else:
            messageBox(
                self, "Oops!", 
                "Please, provide a value of the Horizontal Hydraulic Conductivity!")
    except:
        messageBox(self, "Oops!", "ERROR!!!")

# ----------------------------------------------------------------------------------------------
def createSS(self):
    self.layer = self.mf_act_grid_layer()
    provider = self.layer.dataProvider()
    try:
        if provider.fields().indexFromName("ss") != -1:
            attrIdx = provider.fields().indexFromName("ss")
            provider.deleteAttributes([attrIdx])
        field = QgsField("ss", QVariant.Double,'double', 20, 5)
        provider.addAttributes([field])
        self.layer.updateFields()
        feats = self.layer.getFeatures()
        self.layer.startEditing()
        if (self.radioButton_ss_single.isChecked() and self.lineEdit_ss_single.text()):
            ss = float(self.lineEdit_ss_single.text())
            for f in feats:
                f['ss'] = ss
                self.layer.updateFeature(f)
            self.layer.commitChanges()
            time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
            self.textEdit_mf_log.append(time+' -> ' + 'Specific Storage is entered ...')
        else:
            messageBox(self, "Oops!", "Please, provide a value of the Specific Storage!")
    except:
        messageBox(self, "Oops!", "ERROR!!!")

# ----------------------------------------------------------------------------------------------
def createSY(self):
    self.layer = self.mf_act_grid_layer()
    provider = self.layer.dataProvider()
    try:
        if provider.fields().indexFromName("sy") != -1:
            attrIdx = provider.fields().indexFromName("sy")
            provider.deleteAttributes([attrIdx])
        field = QgsField("sy", QVariant.Double,'double', 20, 5)
        provider.addAttributes([field])
        self.layer.updateFields()
        feats = self.layer.getFeatures()
        self.layer.startEditing()
        if (self.radioButton_sy_single.isChecked() and self.lineEdit_sy_single.text()):
            sy = float(self.lineEdit_sy_single.text())
            for f in feats:
                f['sy'] = sy
                self.layer.updateFeature(f)
            self.layer.commitChanges()
            time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
            self.textEdit_mf_log.append(time+' -> ' + 'Specific Yield is entered ...')
        else:
            messageBox(self, "Oops!", "Please, provide a value of the Specific Yield!")
    except:
        messageBox(self, "Oops!", "ERROR!!!")

# ----------------------------------------------------------------------------------------------
def createInitialH(self):
    desc = "Creating Initial Hydraulic Head"
    start_time(self, desc)
    self.layer = QgsProject.instance().mapLayersByName("mf_act_grid (MODFLOW)")[0]
    provider = self.layer.dataProvider()
    try:
        if provider.fields().indexFromName("ih") != -1:
            attrIdx = provider.fields().indexFromName( "ih" )
            provider.deleteAttributes([attrIdx])
        field = QgsField("ih", QVariant.Double,'double', 20, 5)
        provider.addAttributes([field])
        self.layer.updateFields()
        feats = self.layer.getFeatures()
        self.layer.startEditing()
        # Single value
        if (self.radioButton_initialH_single.isChecked() and self.lineEdit_initialH_single.text()):
            depth = float(self.lineEdit_initialH_single.text())
            for f in feats:
                f['ih'] = - depth + f['top_elev']
                self.layer.updateFeature(f)
            self.layer.commitChanges()
        # Uniform value
        elif (self.radioButton_initialH_uniform.isChecked() and self.lineEdit_initialH_uniform.text()):
            elev = float(self.lineEdit_initialH_uniform.text())
            for f in feats:
                f['ih'] = elev
                self.layer.updateFeature(f)
            self.layer.commitChanges()
        else:
            messageBox(self, "Oops!", "Please, provide a value of the Initial Hydraulic Head!")
    except:
        messageBox(self, "Oops!", "ERROR!!!")
    end_time(self, desc)


def createEVT(self):
    desc = "Creating Evapotranspiration"
    start_time(self, desc)
    self.layer = QgsProject.instance().mapLayersByName("mf_act_grid (MODFLOW)")[0]
    provider = self.layer.dataProvider()
    try:
        if provider.fields().indexFromName("evt") != -1:
            attrIdx = provider.fields().indexFromName( "evt" )
            provider.deleteAttributes([attrIdx])
        field = QgsField("evt", QVariant.Double,'double', 20, 5)
        provider.addAttributes([field])
        self.layer.updateFields()
        feats = self.layer.getFeatures()
        self.layer.startEditing()
        if (self.radioButton_evt_single.isChecked() and self.lineEdit_evt_single.text()):
            evt = float(self.lineEdit_evt_single.text())
            for f in feats:
                f['evt'] = evt
                self.layer.updateFeature(f)
            self.layer.commitChanges()
            time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
            self.textEdit_mf_log.append(time+' -> ' + 'Evapotranspiration is entered ...')
        else:
            messageBox(self, "Oops!", "Please, provide a value of the Evapotranspiration!")
    except:
        messageBox(self, "Oops!", "ERROR!!!")


def mf_riv2_layer(self):
    QSWATMOD_path_dict = self.dirs_and_paths()
    output_dir = QSWATMOD_path_dict['org_shps']
    name_ext_v = 'mf_riv2.gpkg'
    output_file_v = os.path.normpath(os.path.join(output_dir, name_ext_v))
    layer = QgsVectorLayer(output_file_v, '{0} ({1})'.format("mf_riv2","MODFLOW"), 'ogr')
    return layer


def create_layer_inRiv(self):
    self.layer = mf_riv2_layer(self)
    provider = self.layer.dataProvider()
    if self.layer.dataProvider().fields().indexFromName( "layer" ) == -1:
        field = QgsField("layer", QVariant.Int)
        provider.addAttributes([field])
        self.layer.updateFields()
    feats = self.layer.getFeatures()
    self.layer.startEditing()
    for feat in feats:
        layer = 1
        feat['layer'] = layer
        self.layer.updateFeature(feat)
    self.layer.commitChanges()


# def extentlayer(self):
#   extlayer = QgsProject.instance().mapLayersByName("mf_grid (MODFLOW)")[0]

#   # get extent
#   ext = extlayer.extent()
#   xmin = ext.xMinimum()
#   xmax = ext.xMaximum()
#   ymin = ext.yMinimum()
#   ymax = ext.yMaximum()
#   extent = "{a},{b},{c},{d}".format(a = xmin, b = xmax, c = ymin, d = ymax)
#   return extent


# ----------------------------------------------------------------------------------------------
def createRch(self):
    if (self.radioButton_rch.isChecked() and self.lineEdit_rch.text()):
        rch = float(self.lineEdit_rch.text())

        self.layer = QgsProject.instance().mapLayersByName("mf_act_grid (MODFLOW)")[0]
        provider = self.layer.dataProvider()
        if self.layer.dataProvider().fields().indexFromName("rch") == -1:
            field = QgsField("rch", QVariant.Double,'double', 20, 5)
            provider.addAttributes([field])
            self.layer.updateFields()
        feats = self.layer.getFeatures()
        self.layer.startEditing()
        for f in feats:
            f['rch'] = rch
            self.layer.updateFeature(f)
        self.layer.commitChanges()

        time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
        self.textEdit_mf_log.append(time+' -> ' + 'Specific Yield is entered ...')
    else:
        messageBox(self, "Oops!", "Please, provide a value of the recharge rate!")

# def cvtRchtoR(self):
#     QSWATMOD_path_dict = self.dirs_and_paths()
#     extlayer = QgsProject.instance().mapLayersByName("mf_grid (MODFLOW)")[0]
#     input1 = QgsProject.instance().mapLayersByName("mf_act_grid (MODFLOW)")[0]
#     input2 = QgsProject.instance().mapLayersByName("top_elev (MODFLOW)")[0]
    
#     # Get pixel size from top_elev raster
#     delc = input2.rasterUnitsPerPixelX()
#     delr = input2.rasterUnitsPerPixelY()
    
#     # get extent
#     ext = extlayer.extent()
#     xmin = ext.xMinimum()
#     xmax = ext.xMaximum()
#     ymin = ext.yMinimum()
#     ymax = ext.yMaximum()
#     extent = "{a},{b},{c},{d}".format(a = xmin, b = xmax, c = ymin, d = ymax)

#     name = 'rch'
#     name_ext = "rch.tif"
#     output_dir = QSWATMOD_path_dict['org_shps']
#     output_raster = os.path.join(output_dir, name_ext)

#     processing.run(
#         "gdalogr:rasterize",
#         input1,
#         "rch",1, delc, delr,
#         extent,
#         False,5,"-9999",0,75,6,1,False,0,"",
#         output_raster)

#     layer = QgsRasterLayer(output_raster, '{0} ({1})'.format("rch","MODFLOW"))
        
#     # Put in the group
#     root = QgsProject.instance().layerTreeRoot()
#     mf_group = root.findGroup("MODFLOW")    
#     QgsProject.instance().addMapLayer(layer, False)
#     mf_group.insertChildNode(0, QgsLayerTreeLayer(layer))

#     time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
#     self.textEdit_mf_log.append(time+' -> ' + 'Specific Yield is converted to Raster ...')

# --------------------------------------------------------------------------------------------
def writeMFmodel(self):
    # import modules
    from QSWATMOD2.modules import flopy
    import os
    import numpy as np
    from osgeo import gdal
    from osgeo import osr
    import datetime

    msgBox = QMessageBox()
    msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))

    # set working directory and inputs -----------------------------------------------------
    # mffolder_path = self.createMFfolder()

    if not self.lineEdit_createMFfolder.text():
        msgBox = QMessageBox()
        msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
        msgBox.setWindowTitle("Oops!")
        msgBox.setText("Please, specify the path to your MODFLOW model working directory!")
        msgBox.exec_()
    elif not self.lineEdit_mname.text():
        msgBox = QMessageBox()
        msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
        msgBox.setWindowTitle("Oops!")
        msgBox.setText("Please, provide your MODFLOW model name!")
        msgBox.exec_()
    else:
        QSWATMOD_path_dict = self.dirs_and_paths()
        wd = QSWATMOD_path_dict['SMfolder']
        wd2 = QSWATMOD_path_dict['org_shps']
        mfwd = self.lineEdit_createMFfolder.text()
        mname = self.lineEdit_mname.text()

        ### =====================================================================
        cio = open(os.path.join(wd, "file.cio"), "r")
        lines = cio.readlines()
        skipyear = int(lines[59][12:16])
        iprint = int(lines[58][12:16]) #read iprint (month, day, year)
        styear = int(lines[8][12:16]) #begining year
        styear_warmup = int(lines[8][12:16]) + skipyear #begining year with warmup
        edyear = styear + int(lines[7][12:16])-1 # ending year
        edyear_warmup = styear_warmup + int(lines[7][12:16])-1 - int(lines[59][12:16])#ending year with warmup
        if skipyear == 0:
            FCbeginday = int(lines[9][12:16])  #begining julian day
        else:
            FCbeginday = 1  #begining julian day
        FCendday = int(lines[10][12:16])  #ending julian day
        cio.close()

        stdate = datetime.datetime(styear, 1, 1) + datetime.timedelta(FCbeginday - 1)
        eddate = datetime.datetime(edyear, 1, 1) + datetime.timedelta(FCendday - 1)

        startDate = stdate.strftime("%m/%d/%Y")
        endDate = eddate.strftime("%m/%d/%Y")
        duration = (eddate - stdate).days + 100 # add 100 days more ...considering leap years

        # ======================================================================
        mf = flopy.modflow.Modflow(
            mname, model_ws=mfwd,
            # exe_name = exe_name,
            version='mfnwt')

        # top_elev
        top_elev = QgsProject.instance().mapLayersByName("top_elev (MODFLOW)")[0]
        top_elev_Ds = gdal.Open(top_elev.source())
        top_elev_Data = top_elev_Ds.GetRasterBand(1).ReadAsArray()
        top_elev_nan = top_elev_Ds.GetRasterBand(1).GetNoDataValue()

        # bot_elev
        bot_elev = QgsProject.instance().mapLayersByName("bot_elev (MODFLOW)")[0]
        bot_elev_Ds = gdal.Open(bot_elev.source())
        bot_elev_Data = bot_elev_Ds.GetRasterBand(1).ReadAsArray()

        # Single HK
        if (self.radioButton_hk_single.isChecked() and self.lineEdit_hk_single.text()):
            hk_Data = float(self.lineEdit_hk_single.text())
            time = datetime.datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
            self.textEdit_mf_log.append(time+' -> ' + 'Single Hydraulic Conductivity is used...')
        elif (self.radioButton_hk_raster.isChecked() and self.lineEdit_hk_raster.text()):
            hk = QgsProject.instance().mapLayersByName("hk (MODFLOW)")[0]
            hk_Ds = gdal.Open(hk.source())
            hk_Data = hk_Ds.GetRasterBand(1).ReadAsArray()
        else:
            msgBox.setWindowTitle("Error!")
            msgBox.setText("Hydraulic Conductivity is NOT provided!")
            msgBox.exec_()

        # SS
        if (self.radioButton_ss_single.isChecked() and self.lineEdit_ss_single.text()):
            ss_Data = float(self.lineEdit_ss_single.text())
            time = datetime.datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
            self.textEdit_mf_log.append(time+' -> ' + 'Single Specific Storage is used...')
        elif (self.radioButton_ss_raster.isChecked() and self.lineEdit_ss_raster.text()):
            ss = QgsProject.instance().mapLayersByName("ss (MODFLOW)")[0]
            ss_Ds = gdal.Open(ss.source())
            ss_Data = ss_Ds.GetRasterBand(1).ReadAsArray()
        else:
            msgBox.setWindowTitle("Error!")
            msgBox.setText("Specific Storage is NOT provided!")
            msgBox.exec_()

        # SY
        if (self.radioButton_sy_single.isChecked() and self.lineEdit_sy_single.text()):
            sy_Data = float(self.lineEdit_sy_single.text())
            time = datetime.datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
            self.textEdit_mf_log.append(time+' -> ' + 'Single Specific Yield is used...')
        elif (self.radioButton_sy_raster.isChecked() and self.lineEdit_sy_raster.text()):
            sy = QgsProject.instance().mapLayersByName("sy (MODFLOW)")[0]
            sy_Ds = gdal.Open(sy.source())
            sy_Data = sy_Ds.GetRasterBand(1).ReadAsArray()
        else:
            msgBox.setWindowTitle("Error!")
            msgBox.setText("Specific Storage is NOT provided!")
            msgBox.exec_()

        # EVT
        if self.groupBox_evt.isChecked():
            if (self.radioButton_evt_single.isChecked() and self.lineEdit_evt_single.text()):
                evt_Data = float(self.lineEdit_evt_single.text())
                time = datetime.datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
                self.textEdit_mf_log.append(time+' -> ' + 'Single EVT value is used...')
            elif (self.radioButton_evt_raster.isChecked() and self.lineEdit_evt_raster.text()):
                evt = QgsProject.instance().mapLayersByName("evt (MODFLOW)")[0]
                evt_Ds = gdal.Open(evt.source())
                evt_Data = evt_Ds.GetRasterBand(1).ReadAsArray()
            else:
                msgBox.setWindowTitle("Error!")
                msgBox.setText("Evapotranspiration is NOT provided!")
                msgBox.exec_()

        # initialH
        initialH = QgsProject.instance().mapLayersByName("ih (MODFLOW)")[0]
        initialH_Ds = gdal.Open(initialH.source())
        initialH_Data = initialH_Ds.GetRasterBand(1).ReadAsArray()
        
        # have geo transform to set things up to match later that puts our outputs
        geot = top_elev_Ds.GetGeoTransform()
        
        # The following method cause a problem (None Type has no SetProjection)
        # Get ibound -------------------------------------------------------------------------
        iboundDs = gdal.GetDriverByName('GTiff').Create(
                        os.path.join(wd2, 'ibound.tiff'), top_elev_Ds.RasterXSize,
                        top_elev_Ds.RasterYSize, 1, gdal.GDT_Int32)
        # iboundDs = gdal.Open(os.path.join(wd2, 'ibound.tiff'), 1)
        iboundDs.SetProjection(top_elev_Ds.GetProjection())
        iboundDs.SetGeoTransform(geot)

        iboundData = np.zeros(top_elev_Data.shape, dtype = np.int32)
        iboundData[top_elev_Data != top_elev_nan] = 1

        # negative on is the value in the i bound that represents there's a value for the initial hydraulic head condition
        iboundData[top_elev_Data == top_elev_nan] = 0
        iboundDs.GetRasterBand(1).WriteArray(iboundData)

        # New Method from Luke to create Bas input file 9/23/2018
        # mf_dem = QgsProject.instance().mapLayersByName("top_elev (MODFLOW)")[0]
        # mf_demDs = gdal.Open(sy.source())
        # gs = mf_demDs.GetRasterBand(1).ReadAsArray()
        # geot_gs = mf_demDs.GetGeoTransform()
        # # gsData = top_elev_Ds.GetRasterBand(1).ReadAsArray()
        # gs_demNd = mf_demDs.GetRasterBand(1).GetNoDataValue()
        # ibound = np.zeros(gs.shape, dtype=np.int32)
        # ibound[(gs[:, :] > 0)] = 1

        # Model domain and grid definition ------------------------------------------------------
        ztop = top_elev_Data
        zbot = bot_elev_Data
        nlay = 1
        nrow = top_elev_Ds.RasterYSize
        ncol = top_elev_Ds.RasterXSize
        delr = geot[1]
        delc = abs(geot[5])

        # Create dis file -------------------------------------------------------------------
        dis = flopy.modflow.ModflowDis(
            mf, nlay, nrow, ncol,
            delr=delr, delc=delc, top=ztop, botm=zbot, itmuni = 4,
            perlen=duration, nstp=duration, steady=False)

        # write bas -------------------------------------------------------------------
        bas = flopy.modflow.ModflowBas(mf, ibound=iboundData, strt=initialH_Data)

        # NWT solver -------------------------------------------------------------------
        nwt = flopy.modflow.ModflowNwt(
                    mf, headtol=0.1, fluxtol=500, maxiterout=1000,
                    Continue=False, iprnwt=1, linmeth=2
                    )

        # Create upw -------------------------------------------------------------------
        vka = float(self.lineEdit_vka.text())
        if self.comboBox_layerType.currentText() == " - Convertible - ":
            laytype = 1
        else:
            laytype = 0
        upw = flopy.modflow.ModflowUpw(mf, hk=hk_Data, ss=ss_Data, sy=sy_Data, vka=vka, laytyp=laytype)

        # Create EVT -------------------------------------------------------------------
        if self.groupBox_evt.isChecked():
            evt = flopy.modflow.ModflowEvt(mf, nevtop=3, evtr=evt_Data)


        ### Riv package =========================================================
        riv = QgsProject.instance().mapLayersByName("mf_riv2 (MODFLOW)")[0]
        provider = riv.dataProvider()

        # Get the index numbers of the fields
        grid_id_idx = provider.fields().indexFromName("grid_id")
        layer_idx = provider.fields().indexFromName("layer")
        row_idx = provider.fields().indexFromName("row")
        col_idx = provider.fields().indexFromName("col")
        riv_stage = provider.fields().indexFromName("riv_stage")
        riv_cond = provider.fields().indexFromName("riv_cond")
        riv_bot = provider.fields().indexFromName("riv_bot")

        # transfer the shapefile riv to a python list   
        l = []
        for i in riv.getFeatures():
            l.append(i.attributes())

        # then sort by grid_id
        import operator
        l_sorted = sorted(l, key=operator.itemgetter(grid_id_idx))

        # Extract grid_ids and layers as lists
        layers = [(ly[layer_idx]-1) for ly in l_sorted] 
        rows = [(r[row_idx]-1) for r in l_sorted]
        cols = [(c[col_idx]-1) for c in l_sorted]
        riv_stages = [float(rs[riv_stage]) for rs in l_sorted]
        riv_conds = [float(rc[riv_cond]) for rc in l_sorted]
        riv_bots = [float(rb[riv_bot]) for rb in l_sorted]
        riv_f = np.c_[layers, rows, cols, riv_stages, riv_conds, riv_bots]
        lrcd = {}
        lrcd[0] = riv_f # This river boundary will be applied to all stress periods
        riv_pac = flopy.modflow.ModflowRiv(mf, stress_period_data=lrcd)
        ###  ===========================================================================================

        ### Recharge Package (Recharge rate / Deep peroclation is passed from SWAT simulation!)
        rch = flopy.modflow.ModflowRch(mf, rech=0)
        ###  ===========================================================================================

        # oc package
        oc = flopy.modflow.ModflowOc(mf, ihedfm=1)

        # write input files
        mf.write_input()

        # run model
        # success, mfoutput = mf.run_model(silent = False, pause = False)
        time = datetime.datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
        self.textEdit_mf_log.append(time + ' -> ' + 'Your MODFLOW model has been created in the working directory ...')

        msgBox = QMessageBox()
        msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
        msgBox.setWindowTitle("Created!")
        msgBox.setText("MODFLOW model has been created!")
        msgBox.exec_()




