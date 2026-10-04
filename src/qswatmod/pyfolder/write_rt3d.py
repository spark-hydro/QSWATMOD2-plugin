import os
import glob
import posixpath
import ntpath
import shutil
import numpy as np
import pandas as pd
import math
from datetime import datetime
from PyQt5.QtWidgets import QMessageBox, QFileDialog
from PyQt5.QtGui import QIcon
from qgis.core import(
                    QgsProject, QgsVectorFileWriter, QgsLayerTreeLayer, QgsVectorLayer,
                    QgsField, QgsRasterLayer
                    )
from qgis.PyQt.QtCore import(
                            QVariant, QCoreApplication, QSettings, QFileInfo
                            )
import processing
from .utils import DefineTime


def get_nrows_ncols(self):
    QSWATMOD_path_dict = self.dirs_and_paths()
    # Find .dis file and read number of rows, cols, x spacing, and y spacing (not allowed to change)
    for filename in glob.glob(str(QSWATMOD_path_dict['SMfolder'])+"/*.dis"):
        with open(filename, "r") as f:
            data = []
            for line in f.readlines():
                if not line.startswith("#"):
                    data.append(line.replace('\n', '').split())
        nrows_ = int(data[0][1])
        ncols_ = int(data[0][2])
    return nrows_, ncols_
    
def create_porosity(self):
    des = "Creating Porosity"
    self.time_stamp_start(des)
    QSWATMOD_path_dict = self.dirs_and_paths()
    self.layer = QgsProject.instance().mapLayersByName("rt3d_grid (RT3D)")[0]
    provider = self.layer.dataProvider()
    # Create Elevation field
    if self.layer.dataProvider().fields().indexFromName("porosity") == -1:
        field = QgsField("porosity", QVariant.Double, 'double', 5, 2)
        provider.addAttributes([field])
        self.layer.updateFields()
        # Get the index numbers of the fields
        icbund_idx = provider.fields().indexFromName("porosity")
        # Find .dis file and read number of rows, cols, x spacing, and y spacing (not allowed to change)
        # read bas first
        for filename in glob.glob(str(QSWATMOD_path_dict['SMfolder'])+"/*.bas"):
            with open(filename, "r") as f:
                data = []
                for line in f.readlines():
                    if not line.startswith("#"):
                        data.append(line.replace('\n', '').split())
        # Get an elevation list from discretiztion file
        ii = 2  # Starting line
        icbunds = []
        while float(data[ii][0]) > -2:
            for jj in range(len(data[ii])):
                icbunds.append(int(data[ii][jj]))
            ii += 1
        # Get features (Find out a way to change attribute values using another field)
        tot_feats = self.layer.featureCount()
        count = 0
        feats = self.layer.getFeatures()
        self.layer.startEditing()
        # add row number
        self.progressBar_rt3d_status.setValue(0)
        val_ = self.lineEdit_porosity_s.text()
        for f, elev in zip(feats, icbunds):
            self.layer.changeAttributeValue(f.id(), icbund_idx, int(elev)*float(val_))
            count += 1
            provalue = round(count/tot_feats*100)
            self.progressBar_rt3d_status.setValue(provalue)
            QCoreApplication.processEvents()
        self.layer.commitChanges()
        QCoreApplication.processEvents()
        self.time_stamp_end(des)
    else:
        time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
        self.textEdit_rt3d_log.append(time+' -> ' + "'porosity' already exists ...")

def create_porosity_array2(self):
    nrows, ncols = get_nrows_ncols(self)
    val_ = self.lineEdit_porosity_s.text()
    colnam = "icbund"
    layer = QgsProject.instance().mapLayersByName("rt3d_grid (RT3D)")[0]
    por = [(int(i.attribute(colnam))*float(val_)) for i in layer.getFeatures()]
    por_df_ = pd.DataFrame(np.reshape(por, (nrows, ncols)), dtype="float")
    return por_df_


def create_icbund(self):
    des = "Creating ICBUND"
    self.time_stamp_start(des)
    QSWATMOD_path_dict = self.dirs_and_paths()
    self.layer = QgsProject.instance().mapLayersByName("rt3d_grid (RT3D)")[0]
    provider = self.layer.dataProvider()
    # Create Elevation field
    if self.layer.dataProvider().fields().indexFromName("icbund") == -1:
        field = QgsField("icbund", QVariant.Int)
        provider.addAttributes([field])
        self.layer.updateFields()
        # Get the index numbers of the fields
        icbund_idx = provider.fields().indexFromName("icbund")
        # Find .dis file and read number of rows, cols, x spacing, and y spacing (not allowed to change)
        for filename in glob.glob(str(QSWATMOD_path_dict['SMfolder'])+"/*.bas"):
            with open(filename, "r") as f:
                data = []
                for line in f.readlines():
                    if not line.startswith("#"):
                        data.append(line.replace('\n', '').split())
        # Get an elevation list from discretiztion file
        ii = 2  # Starting line
        icbunds = []
        # while float(data[ii][0]) > -2: BUG: ValueError: could not convert string to float: 'internal'
        while data[ii][0] != "internal":
            if float(data[ii][0]) < -2:
                break
            for jj in range(len(data[ii])):
                icbunds.append(int(data[ii][jj]))
            ii += 1
        # Get features (Find out a way to change attribute values using another field)
        tot_feats = self.layer.featureCount()
        count = 0
        feats = self.layer.getFeatures()
        self.layer.startEditing()
        # add row number
        self.progressBar_rt3d_status.setValue(0)
        for f, elev in zip(feats, icbunds):
            self.layer.changeAttributeValue(f.id(), icbund_idx, elev)
            count += 1
            provalue = round(count/tot_feats*100)
            self.progressBar_rt3d_status.setValue(provalue)
            QCoreApplication.processEvents()
        self.layer.commitChanges()
        QCoreApplication.processEvents()
        self.time_stamp_end(des)
    else:
        time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
        self.textEdit_rt3d_log.append(time+' -> ' + "'icbund' already exists ...")

def create_icbund_array(self):
    nrows, ncols = get_nrows_ncols(self)
    colnam = "icbund"
    layer = QgsProject.instance().mapLayersByName("rt3d_grid (RT3D)")[0]
    icb = [i.attribute(colnam) for i in layer.getFeatures()]
    icb_df_ = pd.DataFrame(np.reshape(icb, (nrows, ncols)), dtype="Int64")
    return icb_df_


# porosity
def create_porosity_s_org(self): # current exe dislike single constant value
    des = "Creating Porosity"
    self.time_stamp_start(des)
    val_ = self.lineEdit_porosity_s.text()
    self.time_stamp_end(des)
    return val_

def create_porosity_s(self):
    nrows, ncols = get_nrows_ncols(self)
    des = "Creating Porosity"
    self.time_stamp_start(des)
    val_ = self.lineEdit_porosity_s.text()
    self.time_stamp_end(des)
    return val_

def loadPorosity(self):
    QSWATMOD_path_dict = self.dirs_and_paths()
    settings = QSettings()
    if settings.contains('/QSWATMOD2/LastInputPath'):
        path = str(settings.value('/QSWATMOD2/LastInputPath'))
    else:
        path = ''
    title = "Choose Porosity Rasterfile"
    inFileName, __ = QFileDialog.getOpenFileName(None, title, path, "Rasterfiles (*.tif);; All files (*.*)")

    if inFileName:
        settings.setValue('/QSWATMOD2/LastInputPath', os.path.dirname(str(inFileName)))
        Out_folder = QSWATMOD_path_dict['org_shps']
        inInfo = QFileInfo(inFileName)
        inFile = inInfo.fileName()
        pattern = os.path.splitext(inFileName)[0] + '.*'
        baseName = inInfo.baseName()

        # inName = os.path.splitext(inFile)[0]
        inName = 'porosity'
        for f in glob.iglob(pattern):
            suffix = os.path.splitext(f)[1]
            if os.name == 'nt':
                outfile = ntpath.join(Out_folder, inName + suffix)
            else:
                outfile = posixpath.join(Out_folder, inName + suffix)
            shutil.copy(f, outfile)
    
        if os.name == 'nt':
            porosity = ntpath.join(Out_folder, inName + ".tif")
        else:
            porosity = posixpath.join(Out_folder, inName + ".tif")
        # Delete existing "bot_elev (SMfolder)" raster file"
        for lyr in list(QgsProject.instance().mapLayers().values()):
            if lyr.name() == ("porosity (DATA)"):
                QgsProject.instance().removeMapLayers([lyr.id()])

        layer = QgsRasterLayer(porosity, '{0} ({1})'.format("porosity", "DATA"))
        # Put in the group
        root = QgsProject.instance().layerTreeRoot()
        mf_group = root.findGroup("RT3D")
        QgsProject.instance().addMapLayer(layer, False)
        mf_group.insertChildNode(0, QgsLayerTreeLayer(layer))
        self.lineEdit_porosity_r.setText(porosity)

    des = 'Extracting Porosity from Raster'
    self.time_stamp_start(des)
    input1 = QgsProject.instance().mapLayersByName("rt3d_grid (RT3D)")[0]
    input2 = QgsProject.instance().mapLayersByName("porosity (DATA)")[0]
    provider1 = input1.dataProvider()
    provider2 = input2.dataProvider()
    rpath = provider2.dataSourceUri()

    if provider1.fields().indexFromName("porosity") != -1:
        attrIdx = provider1.fields().indexFromName("porosity")
        provider1.deleteAttributes([attrIdx])
    if provider1.fields().indexFromName("pr_mean") != -1:
        attrIdx = provider1.fields().indexFromName("pr_mean")
        provider1.deleteAttributes([attrIdx])
    params = {
        'INPUT_RASTER': input2,
        'RASTER_BAND':1,
        'INPUT_VECTOR': input1,
        'COLUMN_PREFIX':'pr_',
        'STATS':[2]            
        }    
    processing.run("qgis:zonalstatistics", params)
    self.time_stamp_end(des)

def create_porosity_array(self):
    nrows, ncols = get_nrows_ncols(self)
    colnam = "pr_mean"
    layer = QgsProject.instance().mapLayersByName("rt3d_grid (RT3D)")[0]
    pr = [0 if i.attribute(colnam) < 0 else i.attribute(colnam) for i in layer.getFeatures()]
    pr_df_ = pd.DataFrame(np.reshape(pr, (nrows, ncols)))
    return pr_df_


# NO3
def create_no3_s(self):
    des = "Creating Nitrate Initial Conc."
    self.time_stamp_start(des)
    val_ = self.lineEdit_no3_s.text()
    self.time_stamp_end(des)
    return val_

# navigate to the hk raster
def loadNO3(self):
    QSWATMOD_path_dict = self.dirs_and_paths()
    settings = QSettings()
    if settings.contains('/QSWATMOD2/LastInputPath'):
        path = str(settings.value('/QSWATMOD2/LastInputPath'))
    else:
        path = ''
    title = "Choose Initial NO3 Rasterfile"
    inFileName, __ = QFileDialog.getOpenFileName(None, title, path, "Rasterfiles (*.tif);; All files (*.*)")
    if inFileName:
        settings.setValue('/QSWATMOD2/LastInputPath', os.path.dirname(str(inFileName)))
        Out_folder = QSWATMOD_path_dict['org_shps']
        inInfo = QFileInfo(inFileName)
        inFile = inInfo.fileName()
        pattern = os.path.splitext(inFileName)[0] + '.*'
        baseName = inInfo.baseName()
        # inName = os.path.splitext(inFile)[0]
        inName = 'no3'
        for f in glob.iglob(pattern):
            suffix = os.path.splitext(f)[1]
            if os.name == 'nt':
                outfile = ntpath.join(Out_folder, inName + suffix)
            else:
                outfile = posixpath.join(Out_folder, inName + suffix)
            shutil.copy(f, outfile)
        if os.name == 'nt':
            shp = ntpath.join(Out_folder, inName + ".tif")
        else:
            shp = posixpath.join(Out_folder, inName + ".tif")
        # Delete existing "bot_elev (SMfolder)" raster file"
        for lyr in list(QgsProject.instance().mapLayers().values()):
            if lyr.name() == ("no3 (DATA)"):
                QgsProject.instance().removeMapLayers([lyr.id()])
        layer = QgsRasterLayer(shp, '{0} ({1})'.format("no3", "DATA"))
        # Put in the group
        root = QgsProject.instance().layerTreeRoot()
        mf_group = root.findGroup("RT3D")
        QgsProject.instance().addMapLayer(layer, False)
        mf_group.insertChildNode(0, QgsLayerTreeLayer(layer))
        self.lineEdit_no3_r.setText(shp)

    des = 'Extracting NO3 CONC from Raster'
    self.time_stamp_start(des)
    input1 = QgsProject.instance().mapLayersByName("rt3d_grid (RT3D)")[0]
    input2 = QgsProject.instance().mapLayersByName("no3 (DATA)")[0]
    provider1 = input1.dataProvider()
    provider2 = input2.dataProvider()
    rpath = provider2.dataSourceUri()
    if provider1.fields().indexFromName("no3_mean") != -1:
        attrIdx = provider1.fields().indexFromName("no3_mean")
        provider1.deleteAttributes([attrIdx])
    params = {
        'INPUT_RASTER': input2,
        'RASTER_BAND':1,
        'INPUT_VECTOR': input1,
        'COLUMN_PREFIX':'no3_',
        'STATS':[2]            
        }    
    processing.run("qgis:zonalstatistics", params)
    self.time_stamp_end(des)


def create_no3_array(self):
    nrows, ncols = get_nrows_ncols(self)
    no3colnam = "no3_mean"
    layer = QgsProject.instance().mapLayersByName("rt3d_grid (RT3D)")[0]
    no3 = [0 if i.attribute(no3colnam) < 0 else i.attribute(no3colnam) for i in layer.getFeatures()]
    no3_df_ = pd.DataFrame(np.reshape(no3, (nrows, ncols)))
    return no3_df_


# P
def create_p_s(self):
    des = "Creating Phosphorus Conc."
    self.time_stamp_start(des)
    val_ = self.lineEdit_p_s.text()
    self.time_stamp_end(des)
    return val_

# navigate to the P raster
def loadP(self):
    QSWATMOD_path_dict = self.dirs_and_paths()
    settings = QSettings()
    if settings.contains('/QSWATMOD2/LastInputPath'):
        path = str(settings.value('/QSWATMOD2/LastInputPath'))
    else:
        path = ''
    title = "Choose Initial P Rasterfile"
    inFileName, __ = QFileDialog.getOpenFileName(None, title, path, "Rasterfiles (*.tif);; All files (*.*)")
    if inFileName:
        settings.setValue('/QSWATMOD2/LastInputPath', os.path.dirname(str(inFileName)))
        Out_folder = QSWATMOD_path_dict['org_shps']
        inInfo = QFileInfo(inFileName)
        inFile = inInfo.fileName()
        pattern = os.path.splitext(inFileName)[0] + '.*'
        baseName = inInfo.baseName()
        # inName = os.path.splitext(inFile)[0]
        inName = 'p'
        for f in glob.iglob(pattern):
            suffix = os.path.splitext(f)[1]
            if os.name == 'nt':
                outfile = ntpath.join(Out_folder, inName + suffix)
            else:
                outfile = posixpath.join(Out_folder, inName + suffix)
            shutil.copy(f, outfile)
        if os.name == 'nt':
            shp = ntpath.join(Out_folder, inName + ".tif")
        else:
            shp = posixpath.join(Out_folder, inName + ".tif")
        # Delete existing "bot_elev (SMfolder)" raster file"
        for lyr in list(QgsProject.instance().mapLayers().values()):
            if lyr.name() == ("p (DATA)"):
                QgsProject.instance().removeMapLayers([lyr.id()])
        layer = QgsRasterLayer(shp, '{0} ({1})'.format("p", "DATA"))
        # Put in the group
        root = QgsProject.instance().layerTreeRoot()
        mf_group = root.findGroup("RT3D")
        QgsProject.instance().addMapLayer(layer, False)
        mf_group.insertChildNode(0, QgsLayerTreeLayer(layer))
        self.lineEdit_p_r.setText(shp)

    des = 'Extracting P CONC from Raster'
    self.time_stamp_start(des)
    input1 = QgsProject.instance().mapLayersByName("rt3d_grid (RT3D)")[0]
    input2 = QgsProject.instance().mapLayersByName("p (DATA)")[0]
    provider1 = input1.dataProvider()
    provider2 = input2.dataProvider()
    rpath = provider2.dataSourceUri()
    if provider1.fields().indexFromName("p_mean") != -1:
        attrIdx = provider1.fields().indexFromName("p_mean")
        provider1.deleteAttributes([attrIdx])
    params = {
        'INPUT_RASTER': input2,
        'RASTER_BAND':1,
        'INPUT_VECTOR': input1,
        'COLUMN_PREFIX':'p_',
        'STATS':[2]            
        }    
    processing.run("qgis:zonalstatistics", params)
    self.time_stamp_end(des)

def create_p_array(self):
    nrows, ncols = get_nrows_ncols(self)
    pcolnam = "p_mean"
    layer = QgsProject.instance().mapLayersByName("rt3d_grid (RT3D)")[0]
    p = [0 if i.attribute(pcolnam) < 0 else i.attribute(pcolnam) for i in layer.getFeatures()]
    p_df_ = pd.DataFrame(np.reshape(p, (nrows, ncols)))
    return p_df_


# ouput options
# Use observed well point shapefile
def use_obs_points(self):
    QSWATMOD_path_dict = self.dirs_and_paths()

    settings = QSettings()
    if settings.contains('/QSWATMOD2/LastInputPath'):
        path = str(settings.value('/QSWATMOD2/LastInputPath'))
    else:
        path = ''
    title = "Choose RT3D observation point shapefile"
    inFileName, __ = QFileDialog.getOpenFileName(None, title, path, "Shapefiles (*.shp);; All files (*.*)")

    if inFileName:
        settings.setValue('/QSWATMOD2/LastInputPath', os.path.dirname(str(inFileName)))
        Out_folder = QSWATMOD_path_dict['org_shps']
        inInfo = QFileInfo(inFileName)
        inFile = inInfo.fileName()
        pattern = os.path.splitext(inFileName)[0] + '.*'
        
        # inName = os.path.splitext(inFile)[0]
        inName = 'rt3d_obs_points'
        for f in glob.iglob(pattern):
            suffix = os.path.splitext(f)[1]
            if os.name == 'nt':
                outfile = ntpath.join(Out_folder, inName + suffix)
            else:
                outfile = posixpath.join(Out_folder, inName + suffix)
            shutil.copy(f, outfile) 
        if os.name == 'nt':
            rt3d_obs_points = ntpath.join(Out_folder, inName + ".shp")
        else:
            rt3d_obs_points = posixpath.join(Out_folder, inName + ".shp")
        
        layer = QgsVectorLayer(rt3d_obs_points, '{0} ({1})'.format("rt3d_obs_points","RT3D"), 'ogr')

        # Put in the group
        root = QgsProject.instance().layerTreeRoot()
        rt3d_group = root.findGroup("RT3D")    
        QgsProject.instance().addMapLayer(layer, False)
        rt3d_group.insertChildNode(0, QgsLayerTreeLayer(layer))
        self.lineEdit_rt3d_obs_points.setText(rt3d_obs_points)  

# select
def select_obs_grids(self):
    QSWATMOD_path_dict = self.dirs_and_paths()

    input1 = QgsProject.instance().mapLayersByName("rt3d_grid (RT3D)")[0]
    input2 = QgsProject.instance().mapLayersByName("rt3d_obs_points (RT3D)")[0]

    name = "rt3d_obs_grid"
    name_ext = "rt3d_obs_grid.shp"
    output_dir = QSWATMOD_path_dict['SMshps']

    # output_file = os.path.normpath(os.path.join(output_dir, name))
    # Select features by location
    params = { 
        'INPUT' : input1,
        'PREDICATE': [0],
        'INTERSECT': input2,
        'METHOD': 0,
    }
    processing.run('qgis:selectbylocation', params)
    # processing.run('qgis:selectbylocation', input1, input2, ['intersects'], 0, 0)

    # Save just the selected features of the target layer
    rt3d_obs_shapefile = os.path.join(output_dir, name_ext)
    QgsVectorFileWriter.writeAsVectorFormat(input1, rt3d_obs_shapefile,
        "utf-8", input1.crs(), "ESRI Shapefile", 1)

    # Deselect the features
    input1.removeSelection()
    layer = QgsVectorLayer(rt3d_obs_shapefile, '{0} ({1})'.format("rt3d_obs","RT3D"), 'ogr')

    # Put in the group
    root = QgsProject.instance().layerTreeRoot()
    swat_group = root.findGroup("RT3D") 
    QgsProject.instance().addMapLayer(layer, False)
    swat_group.insertChildNode(0, QgsLayerTreeLayer(layer))
    layer = QgsProject.instance().addMapLayer(layer)
    self.lineEdit_rt3d_obs_shapefile.setText(rt3d_obs_shapefile)  


def create_rt3d_obs(self):
    self.layer = QgsProject.instance().mapLayersByName("rt3d_obs (RT3D)")[0]
    provider = self.layer.dataProvider()

    if self.layer.dataProvider().fields().indexFromName("layer") == -1:
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
    QCoreApplication.processEvents()

# navigate to the shapefile of the point observation shapefile
def rt3d_obs_shapefile(self):
    QSWATMOD_path_dict = self.dirs_and_paths()        
    settings = QSettings()
    if settings.contains('/QSWATMOD2/LastInputPath'):
        path = str(settings.value('/QSWATMOD2/LastInputPath'))
    else:
        path = ''
    title = "Choose MODFLOW observation shapefile"
    inFileName, __ = QFileDialog.getOpenFileName(None, title, path, "Shapefiles (*.shp);; All files (*.*)")
    if inFileName:
        settings.setValue('/QSWATMOD2/LastInputPath', os.path.dirname(str(inFileName)))
        Out_folder = QSWATMOD_path_dict['SMshps']
        inInfo = QFileInfo(inFileName)
        inFile = inInfo.fileName()
        pattern = os.path.splitext(inFileName)[0] + '.*'
        
        # inName = os.path.splitext(inFile)[0]
        inName = 'rt3d_obs_swatmf'
        for f in glob.iglob(pattern):
            suffix = os.path.splitext(f)[1]
            if os.name == 'nt':
                outfile = ntpath.join(Out_folder, inName + suffix)
            else:
                outfile = posixpath.join(Out_folder, inName + suffix)                    
            shutil.copy(f, outfile) 
        if os.name == 'nt':
            rt3d_obs_shp = ntpath.join(Out_folder, inName + ".shp")
        else:
            rt3d_obs_shp = posixpath.join(Out_folder, inName + ".shp")
        
        layer = QgsVectorLayer(rt3d_obs_shp, '{0} ({1})'.format("rt3d_obs","RT3D"), 'ogr')
        # Put in the group
        root = QgsProject.instance().layerTreeRoot()
        sm_group = root.findGroup("RT3D")   
        QgsProject.instance().addMapLayer(layer, False)
        sm_group.insertChildNode(0, QgsLayerTreeLayer(layer))
        self.lineEdit_rt3d_obs_shapefile.setText(rt3d_obs_shp)     

def export_rt3d_obs(self):
    # try:
    self.layer = QgsProject.instance().mapLayersByName("rt3d_obs (RT3D)")[0]
    provider = self.layer.dataProvider()

    # Get the index numbers of the fields
    row_id_idx = provider.fields().indexFromName("row")
    col_id_idx = provider.fields().indexFromName("col")
    layer_idx = provider.fields().indexFromName("layer")
    
    # transfer the shapefile layer to a python list 
    l = []
    for i in self.layer.getFeatures():
        l.append(i.attributes())

    # then sort by grid_id
    import operator
    l_sorted = sorted(l, key=operator.itemgetter(row_id_idx))

    # Extract grid_ids and layers as lists
    row_ids = [int(g[row_id_idx]) for g in l_sorted]
    col_ids = [int(g[col_id_idx]) for g in l_sorted]
    layer_ids = [int(g[layer_idx]) for g in l_sorted]
    df_ = pd.DataFrame({0:row_ids, 1:col_ids, 2:layer_ids})
    info_number_ = len(row_ids)

    return df_, info_number_


# DSP
def write_dispersivity(self):
    des = "Writing Aquifer Dispersivity"
    self.time_stamp_start(des)
    ld_ = self.lineEdit_ld.text()
    hld_ = self.lineEdit_ratio_hld.text()
    vld_ = self.lineEdit_ratio_vld.text()
    emcd_ = self.lineEdit_emdc.text()
    self.time_stamp_end(des)
    return ld_, hld_, vld_, emcd_




# obtain time step
def freq_writing(self):
    # Obtain time step
    sim_period = DefineTime.define_sim_period(self)
    step = self.spinBox_freq_rt3d_output.value()
    ts_ = []
    if step != 1:
        # ts_.append(str(int(math.floor(sim_period / step) + 1))+"\n")
        ts_.append(1)  # force to include the first day
        for i in range(step, sim_period+1, step):
            ts_.append(i)
    else:
        # ts_.append(str(int(math.floor(sim_period / step)))+"\n")
        for i in range(step, sim_period+1, step):
            ts_.append(i)
    # because list horizontal doesn't work... let's put it in datframe column
    # df_ = pd.DataFrame(ts_)

    return ts_


def write_rt3d_inputs(self):
    QSWATMOD_path_dict = self.dirs_and_paths()
    outfd = QSWATMOD_path_dict['SMfolder']
    rt3d_name = self.lineEdit_rt3d_name.text()
    rt3d_name_ext = rt3d_name + ".btn"
    # write btn
    with open(
                os.path.join(outfd, rt3d_name_ext), 'w',
                newline=''
                ) as f:
        f.write("'PACKAGES USED: ADV,DSP,SSM,RCT,GCG,SALT---------------------------------------'\n")
        f.write("T T T F T F F F F F\n")
        f.write("'NCOMP, MCOMP -----------------------------------------------------------------'\n")
        f.write("2 2\n")
        f.write("'TYPE OF WRITING FOR OUTPUT FILES (0=ASCII/1=BINARY/2=BOTH) -------------------'\n")
        f.write("0\n")
        f.write("'SPECIES (MOBILE/IMMOBILE) ----------------------------------------------------'\n")
        f.write("'NO3' 1 1\n")
        f.write("'P' 1 1\n")
        f.write("'d'  'm'  'g'\n")
        # porosity
        f.write("'POROSITY FOR EACH LAYER ------------------------------------------------------'\n")
        # if self.radioButton_porosity_s.isChecked() and self.lineEdit_porosity_s.text():
        #     f.write("0 {}\n".format(create_porosity_s(self)))
        # elif self.radioButton_porosity_r.isChecked() and self.lineEdit_porosity_r.text():
        #     f.write("1 0.00 Porosity\n")
        #     pr_df = create_porosity_array(self)
        #     pr_df.to_csv(
        #             f, sep=' ', index=False, header=None, float_format='%.5e',
        #             lineterminator='\n', encoding='utf-8')
        create_icbund(self)
        icb_df = create_icbund_array(self)
        por_df_ = create_porosity_array2(self)
        por_df_.to_csv(f, sep='\t', index=False, header=None, lineterminator='\n', encoding='utf-8')
        # ICBUND
        f.write("'ICBUND ARRAY -----------------------------------------------------------------'\n")
        # create_icbund(self)
        # icb_df = create_icbund_array(self)
        icb_df.to_csv(f, sep='\t', index=False, header=None, lineterminator='\n', encoding='utf-8')
        f.write("'INITIAL CONCENTRATIONS: EACH SPECIES -----------------------------------------'\n")
        # NO3
        if self.radioButton_no3_s.isChecked() and self.lineEdit_no3_s.text():
            f.write("0 {} CNO3\n".format(create_no3_s(self)))
        elif self.radioButton_no3_r.isChecked() and self.lineEdit_no3_r.text():
            f.write("1 0.00 CNO3\n")
            no3_df = create_no3_array(self)
            no3_df.to_csv(
                    f, sep=' ', index=False, header=None, float_format='%.5e',
                    lineterminator='\n', encoding='utf-8')
        # P
        if self.radioButton_p_s.isChecked() and self.lineEdit_p_s.text():
            f.write("0 {} P\n".format(create_p_s(self)))
        elif self.radioButton_p_r.isChecked() and self.lineEdit_p_r.text():
            f.write("1 0.00 P\n")
            p_df = create_p_array(self)
            p_df.to_csv(
                    f, sep=' ', index=False, header=None, float_format='%.5e',
                    lineterminator='\n', encoding='utf-8')
        # options
        f.write("'VALUE INDICATING INACTIVE CELL CONCENTRATION ---------------------------------'\n")
        f.write(" -999.0000\n")
        f.write("'IFMTCN(print), IFMTNP(particle), IFMTRF(R), IFMTDP(D), SAVUCN(binary) --------'\n")
        f.write("6	0	0	0	F\n")
        f.write("'NUMBER OF OUTPUT TIMES -------------------------------------------------------'\n")
        freq = freq_writing(self)
        f.write("{}\n".format(len(freq)))
        f.write("'OUTPUT TIMES	----------------------------------------------------------------'\n")
        # NOTE: list horizonal doesn't work with lambda
        f.write(" ".join(map(lambda x: str(x), freq)))
        f.write("\n")
        f.write("'OBSERVATION CELLS: I,J,K	----------------------------------------------------'\n")
        obs_df, obs_info = export_rt3d_obs(self)
        f.write("{} 1\n".format(obs_info))
        obs_df.to_csv(
                f, sep=' ', index=False, header=None,
                lineterminator='\n', encoding='utf-8')        
        f.write("'OUTPUT MASS BUDGET FILES	----------------------------------------------------'\n")
        f.write("F\n")

    # write dsp
    dsp_name_ext = rt3d_name + ".dsp"
    with open(
                os.path.join(outfd, dsp_name_ext), 'w',
                newline=''
                ) as f:
        ld_, hld_, vld_, emcd_ = write_dispersivity(self)
        f.write(" 'LONGITUDINAL DISPERSIVITY ---------------------------------------------------'\n")
        f.write("       0 {}\n".format(ld_))
        f.write(" 'RATIO OF HORIZ. TRANSVERSE TO LONG. DISP. -----------------------------------'\n")
        f.write("       0 {}\n".format(hld_))
        f.write(" 'RATIO OF VERTIC. TRANSVERSE TO LONG. DISP. ----------------------------------'\n")
        f.write("       0 {}\n".format(vld_))
        f.write(" 'EFFECTIVE MOLECULAR DIFFUSION COEFFICIENT -----------------------------------'\n")
        f.write("       0 {}\n".format(emcd_))
    
    # write rct
    rct_name_ext = rt3d_name + ".rct"
    with open(
                os.path.join(outfd, rct_name_ext), 'w',
                newline=''
                ) as f:
        f.write("'ISOTHM,IREACT,NCRXNDATA,NVRXNDATA,ISOLVER,IRCTOP -----------------------------'\n")
        f.write("1 10 2 0 1 0\n".format(ld_))
        f.write("'Bulk density ------------------------------------------'\n")
        f.write("0  {}\n".format(self.lineEdit_bd.text()))
        f.write("'Sorption parameters -----------------------------------'\n")
        f.write("0  {}  partition coefficient for NO3  (linear sorption)\n".format(self.lineEdit_no3_sorp.text()))
        f.write("0  {}  partition coefficient for PO4  (linear sorption)\n".format(self.lineEdit_po4_sorp.text()))
        f.write("0  0.0  second parameter for NO3  (not used for linear sorption)\n")
        f.write("0  0.0  second parameter for PO4  (not used for linear sorption)\n")
        f.write("'Spatially Constant Values for reaction rates' --------------------------------'\n")
        f.write("{}  First-Order Rate Constant of Denitrification\n".format(self.lineEdit_kden.text()))
        f.write("{}  Monod Half-Saturation Term for Denitrification\n".format(self.lineEdit_kno3.text()))
    # write gcg
    gcg_name_ext = rt3d_name + ".gcg"
    with open(
                os.path.join(outfd, gcg_name_ext), 'w',
                newline=''
                ) as f:
        f.write("50 1 3 0				       ITER1,MXITER,ISOLVE,NCRS\n")
        f.write("1.000 0.00001 0			       ACCL,CCLOSE,IPRGCG\n")

    # write adv
    adv_name_ext = rt3d_name + ".adv"
    with open(
                os.path.join(outfd, adv_name_ext), 'w',
                newline=''
                ) as f:
        f.write("         0 1.0000000         1\n")
    # write ssm
    ssm_name_ext = rt3d_name + ".ssm"
    with open(
                os.path.join(outfd, ssm_name_ext), 'w',
                newline=''
                ) as f:
        f.write(" Flag for constasnt concentration cells\n F\n")
    # write rt3d_filenams
    file_name_ext = "rt3d_filenames"
    with open(
                os.path.join(outfd, file_name_ext), 'w',
                newline=''
                ) as f:
        f.write("'{}'           INBTN=1			Basic Transport Package\n".format(rt3d_name+'.btn'))
        f.write("'{}'			INADV=2			Advection Package\n".format(rt3d_name+'.adv'))
        f.write("'{}'			INDSP=3			Dispersion Package\n".format(rt3d_name+'.dsp'))
        f.write("'{}'			INSSM=4			Source/Sink Mixing Package\n".format(rt3d_name+'.ssm'))
        f.write("'{}'			INRCT=5			Reaction Package\n".format(rt3d_name+'.rct'))
        f.write("'{}'			INGCG=6			Implicit Solver Package\n".format(rt3d_name+'.gcg'))
        f.write("'{}'		    OUTRES=10		Restart File\n".format(rt3d_name+'.restart'))
    msgBox = QMessageBox()
    msgBox.setWindowIcon(QIcon(':/QSWATMOD2/pics/sm_icon.png'))
    msgBox.setWindowTitle("Created!")
    msgBox.setText("RT3D model has been created!")
    msgBox.exec_()