from builtins import zip
from builtins import str
from builtins import range
import os
import os.path
import processing
from qgis.core import (
                QgsVectorLayer, QgsField, QgsFeatureIterator, QgsVectorFileWriter,
                QgsProject, QgsLayerTreeLayer, QgsFeatureRequest)
from qgis.PyQt import QtCore, QtGui, QtSql
import glob
import posixpath
import ntpath
import shutil
from datetime import datetime
from qgis.PyQt.QtCore import QVariant, QSettings, QFileInfo, QCoreApplication
from PyQt5.QtWidgets import (
    QAction, QDialog, QFormLayout,
    QMessageBox, QFileDialog
)
# from QSWATMOD2.QSWATMOD2 import dirs_and_paths --> this is not working why?

def check_grid_size(self):  # Create fishnet based on MODFLOW dis file
    # Find .dis file and read number of rows, cols, x spacing, and y spacing (not allowed to change)
    QSWATMOD_path_dict = self.dirs_and_paths()
    for filename in glob.glob(str(QSWATMOD_path_dict['SMfolder'])+"/*.dis"):
        with open(filename, "r") as f:
            data = []
            for line in f.readlines():
                if not line.startswith("#"):
                    data.append(line.replace('\n', '').split())
        nrow = int(data[0][1])
        ncol = int(data[0][2])
        if data[2][0] == "INTERNAL":        
            delr = float(data[3][1])  # cell width along rows (y spacing)
            delc = float(data[4][1])  # cell width along columns (x spacing)
        else:
            delr = float(data[2][1])  # cell width along rows (y spacing)
            delc = float(data[3][1])  # cell width along columns (x spacing)        
        grid_size = delr * delc
    return grid_size


def MF_grid(self):  # Create fishnet based on MODFLOW dis file
    time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
    self.dlg.textEdit_sm_link_log.append(time+' -> ' + "Creating GRIDs ... processing")
    self.dlg.label_StepStatus.setText("Creating 'grid_id' ... ")
    self.dlg.progressBar_step.setValue(0)
    QCoreApplication.processEvents()

    QSWATMOD_path_dict = self.dirs_and_paths()
    layer = QgsProject.instance().mapLayersByName("hru (SWAT)")[0]
    crs = layer.crs()
    # User inputs for coordinate origins at North-West
    x_origin = self.dlg.lineEdit_x_coordinate.text()
    y_origin = self.dlg.lineEdit_y_coordinate.text()

    # Find .dis file and read number of rows, cols, x spacing, and y spacing (not allowed to change)
    for filename in glob.glob(str(QSWATMOD_path_dict['SMfolder'])+"/*.dis"):
        with open(filename, "r") as f:
            data = []
            for line in f.readlines():
                if not line.startswith("#"):
                    data.append(line.replace('\n', '').split())
        nrow = int(data[0][1])
        ncol = int(data[0][2])
        delr = float(data[2][1])  # cell width along rows (y spacing)
        delc = float(data[3][1])  # cell width along columns (x spacing)

        # Add_Subtract number of column, row
        n_row = self.dlg.spinBox_row.value()
        n_col = self.dlg.spinBox_col.value()

        # Calculate MODFLOW extent
        if self.dlg.groupBox_add_grid.isChecked():
            x_right = (float(x_origin) + (ncol * delc)) + (delc * n_col)
            y_lower = (float(y_origin) - (nrow * delr)) - (delr * n_row)
        else:
            x_right = (float(x_origin) + (ncol * delc))
            y_lower = (float(y_origin) - (nrow * delr))
        MF_extent = "{a},{b},{c},{d}".format(a=x_origin, b=x_right, c=y_lower, d=y_origin)

    # mf option 2
    name_ext = "mf_grid_.gpkg"
    output_dir = QSWATMOD_path_dict['org_shps']
    output_file_ = os.path.normpath(os.path.join(output_dir, name_ext))

    # running the acutal routine:
    params = {
        'TYPE': 2,
        'EXTENT': MF_extent,
        'HSPACING': delc,
        'VSPACING': delr,
        'CRS': crs,
        'OUTPUT': output_file_,
        'OVERWRITE': True
    }
    processing.run("native:creategrid", params)

    time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
    self.dlg.textEdit_sm_link_log.append(time+' -> ' + "Creating GRIDs ... passed")
    self.dlg.label_StepStatus.setText("Step Status: ")
    self.dlg.progressBar_step.setValue(100)
    QCoreApplication.processEvents()

    time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
    self.dlg.textEdit_sm_link_log.append(time+' -> ' + "Fixing starting index ... processing")
    self.dlg.label_StepStatus.setText("Step Status: ")
    self.dlg.progressBar_step.setValue(0)
    QCoreApplication.processEvents()

    # rasterize
    name_ext_r = 'mf_grid_.tif'
    output_file_r = os.path.normpath(os.path.join(output_dir, name_ext_r))
    params_r = {
        'INPUT': output_file_,
        'UNITS': 1,
        'WIDTH': delc,
        'HEIGHT': delr,
        'EXTENT': MF_extent,
        'NODATA': -9999,
        'DATA_TYPE': 5,
        'OUTPUT': output_file_r
    }
    processing.run("gdal:rasterize", params_r)

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
    # Define the outputfile to be loaded into the canvas
    mf_grid_shapefile = os.path.join(output_dir, name_ext_v)
    layer = QgsVectorLayer(mf_grid_shapefile, '{0} ({1})'.format("mf_grid","MODFLOW"), 'ogr')
    
    # Put in the group
    root = QgsProject.instance().layerTreeRoot()
    mf_group = root.findGroup("MODFLOW")
    QgsProject.instance().addMapLayer(layer, False)
    mf_group.insertChildNode(0, QgsLayerTreeLayer(layer))

    time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
    self.dlg.textEdit_sm_link_log.append(time+' -> ' + "Fixing starting index ... processing")
    self.dlg.label_StepStatus.setText("Step Status: ")
    self.dlg.progressBar_step.setValue(100)
    QCoreApplication.processEvents()



### I don't know how to retrieve values. 'NoneType' object is not iterable
# def read_dis_MF(self):
#   org_shps, SMshps, SMfolder, Table, SM_exes = self.dirs_and_paths()

#   # Find .dis file and read number of rows, cols, x spacing, and y spacing (not allowed to change)
#   for filename in glob.glob(str(SMfolder)+"/*.dis"):
#       with open(filename, "r") as f:
#           data = []
#           for line in f.readlines():
#               if not line.startswith("#"):
#                   data.append(line.replace('\n', '').split())
#       nrow = int(data[0][1])
#       ncol = int(data[0][2])
#       delr = float(data[2][1]) # is the cell width along rows (y spacing)
#       delc = float(data[3][1]) # is the cell width along columns (x spacing).
#       return nrow, ncol, delr, delc


def create_grid_id(self):
    time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
    self.dlg.textEdit_sm_link_log.append(time+' -> ' + "Creating 'grid_id' ... processing")
    self.dlg.label_StepStatus.setText("Creating 'grid_id' ... ")
    self.dlg.progressBar_step.setValue(0)
    QCoreApplication.processEvents()
    
    self.layer = QgsProject.instance().mapLayersByName("mf_grid (MODFLOW)")[0]
    provider = self.layer.dataProvider()
    if provider.fields().indexFromName("grid_id") == -1:
        field = QgsField("grid_id", QVariant.Int)
        provider.addAttributes([field])
        self.layer.updateFields()
        grid_id = provider.fields().indexFromName("grid_id")
        feats = self.layer.getFeatures()
        self.layer.startEditing()
        tot_feats = self.layer.featureCount()
        count = 0
        for i, f in enumerate(feats):
            self.layer.changeAttributeValue(f.id(), grid_id, i+1)
            count += 1
            provalue = round(count/tot_feats*100)
            self.dlg.progressBar_step.setValue(provalue)
            QCoreApplication.processEvents()
        self.layer.commitChanges()
        QCoreApplication.processEvents()
    else:
        time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
        self.dlg.textEdit_sm_link_log.append(time+' -> ' + "'grid_id' already exists ...")
    time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
    self.dlg.textEdit_sm_link_log.append(time+' -> ' + "Creating 'grid_id' ... passed")
    self.dlg.label_StepStatus.setText('Step Status: ')
    QCoreApplication.processEvents()


def create_row(self):
    time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
    self.dlg.textEdit_sm_link_log.append(time+' -> ' + "Creating 'row number' ... processing")
    self.dlg.label_StepStatus.setText("Creating 'row number' ... ")
    self.dlg.progressBar_step.setValue(0)
    QCoreApplication.processEvents()

    QSWATMOD_path_dict = self.dirs_and_paths()
    self.layer = QgsProject.instance().mapLayersByName("mf_grid (MODFLOW)")[0]
    provider = self.layer.dataProvider()
    if self.layer.dataProvider().fields().indexFromName("row") == -1:
        field = QgsField("row", QVariant.Int)
        provider.addAttributes([field])
        self.layer.updateFields()

        # Get the index numbers of the fields
        grid_id = self.layer.dataProvider().fields().indexFromName("grid_id")
        row = provider.fields().indexFromName("row")

        # Find .dis file and read number of rows, cols, x spacing, and y spacing (not allowed to change)
        for filename in glob.glob(str(QSWATMOD_path_dict['SMfolder'])+"/*.dis"):
            with open(filename, "r") as f:
                data = []
                for line in f.readlines():
                    if not line.startswith("#"):
                        data.append(line.replace('\n', '').split())
            nrows = int(data[0][1])
            ncols = int(data[0][2])

        # Get row and column lists
        iy = []  # row
        # ix = [] # col
        for i in range(1, nrows + 1):
            for j in range(1, ncols + 1):
                # ix.append(j)
                iy.append(i)
        # Get features (Find out a way to change attribute values using another field)
        tot_feats = self.layer.featureCount()
        count = 0

        feats = self.layer.getFeatures()
        self.layer.startEditing()
        # add row number
        for f, r in zip(feats, iy):
            self.layer.changeAttributeValue(f.id(), row, r)
            count += 1
            provalue = round(count/tot_feats*100)
            # self.layer.changeAttributeValue(f[grid_id] - 1, row, r)
            # self.layer.changeAttributeValue(f[grid_id] - 1, col, c)
            self.dlg.progressBar_step.setValue(provalue)
            QCoreApplication.processEvents()
        self.layer.commitChanges()
        QCoreApplication.processEvents()
    else:
        time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
        self.dlg.textEdit_sm_link_log.append(time+' -> ' + "'row number' already exists ...")
    time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
    self.dlg.textEdit_sm_link_log.append(time+' -> ' + "Creating 'row number' ... passed")
    self.dlg.label_StepStatus.setText('Step Status: ')
    QCoreApplication.processEvents()


def create_col(self):
    time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
    self.dlg.textEdit_sm_link_log.append(time+' -> ' + "Creating 'column number' ... processing")
    self.dlg.label_StepStatus.setText("Creating 'column number' ... ")
    self.dlg.progressBar_step.setValue(0)
    QCoreApplication.processEvents()

    QSWATMOD_path_dict = self.dirs_and_paths()
    self.layer = QgsProject.instance().mapLayersByName("mf_grid (MODFLOW)")[0]
    provider = self.layer.dataProvider()
    # Create Column field
    if self.layer.dataProvider().fields().indexFromName("col") == -1:
        field = QgsField("col", QVariant.Int)
        provider.addAttributes([field])
        self.layer.updateFields()

        # Get the index numbers of the fields
        grid_id = self.layer.dataProvider().fields().indexFromName("grid_id")
        col = provider.fields().indexFromName("col")

        # Find .dis file and read number of rows, cols, x spacing, and y spacing (not allowed to change)
        for filename in glob.glob(str(QSWATMOD_path_dict['SMfolder'])+"/*.dis"):
            with open(filename, "r") as f:
                data = []
                for line in f.readlines():
                    if not line.startswith("#"):
                        data.append(line.replace('\n', '').split())
            nrows = int(data[0][1])
            ncols = int(data[0][2])

        # Get row and column lists
        ix = []  # col
        for i in range(1, nrows + 1):
            for j in range(1, ncols + 1):
                ix.append(j)

        # Get features (Find out a way to change attribute values using another field)
        tot_feats = self.layer.featureCount()
        count = 0
        feats = self.layer.getFeatures()
        self.layer.startEditing()
        # add row number
        for f, c in zip(feats, ix):
            self.layer.changeAttributeValue(f.id(), col, c)
            count += 1
            provalue = round(count/tot_feats*100)
            self.dlg.progressBar_step.setValue(provalue)
            QCoreApplication.processEvents()
            # self.layer.changeAttributeValue(f[grid_id] - 1, row, r)
            # self.layer.changeAttributeValue(f[grid_id] - 1, col, c)
        self.layer.commitChanges()
        QCoreApplication.processEvents()
    else:
        time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
        self.dlg.textEdit_sm_link_log.append(time+' -> ' + "'column number' already exists ...")
    time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
    self.dlg.textEdit_sm_link_log.append(time+' -> ' + "Creating 'column number' ... passed")
    self.dlg.label_StepStatus.setText('Step Status: ')
    QCoreApplication.processEvents()


def create_top_elev(self):
    time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
    self.dlg.textEdit_sm_link_log.append(time+' -> ' + "Importing 'land surface elevation' ... processing")
    self.dlg.label_StepStatus.setText("Importing 'land surface elevation' ... ")
    self.dlg.progressBar_step.setValue(0)
    QCoreApplication.processEvents()

    QSWATMOD_path_dict = self.dirs_and_paths()
    self.layer = QgsProject.instance().mapLayersByName("mf_grid (MODFLOW)")[0]
    provider = self.layer.dataProvider()

    # Create Elevation field
    if self.layer.dataProvider().fields().indexFromName("top_elev") == -1:
        field = QgsField("top_elev", QVariant.Double, 'double', 20, 5)
        provider.addAttributes([field])
        self.layer.updateFields()

        # Get the index numbers of the fields
        grid_id = self.layer.dataProvider().fields().indexFromName("grid_id")
        top_elev = provider.fields().indexFromName("top_elev")

        # Find .dis file and read number of rows, cols, x spacing, and y spacing (not allowed to change)
        for filename in glob.glob(str(QSWATMOD_path_dict['SMfolder'])+"/*.dis"):
            with open(filename, "r") as f:
                data = []
                for line in f.readlines():
                    if not line.startswith("#"):
                        data.append(line.replace('\n', '').split())

        # Get an elevation list from discretiztion file
        ii = 5  # Starting line
        top_elevs = []
        while data[ii][0] != "INTERNAL":
            for jj in range(len(data[ii])):
                top_elevs.append(float(data[ii][jj]))
            ii += 1

        # Get features (Find out a way to change attribute values using another field)
        tot_feats = self.layer.featureCount()
        count = 0

        feats = self.layer.getFeatures()
        self.layer.startEditing()
        # add row number
        for f, elev in zip(feats, top_elevs):
            self.layer.changeAttributeValue(f.id(), top_elev, elev)
            count += 1
            provalue = round(count/tot_feats*100)
            self.dlg.progressBar_step.setValue(provalue)
            QCoreApplication.processEvents()
        self.layer.commitChanges()
        QCoreApplication.processEvents()
    else:
        time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
        self.dlg.textEdit_sm_link_log.append(time+' -> ' + "'top_elev' already exists ...")
    time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
    self.dlg.textEdit_sm_link_log.append(time+' -> ' + "Importing 'land surface elevation' ... passed")
    self.dlg.label_StepStatus.setText('Step Status: ')
    QCoreApplication.processEvents()

# Option 1
# Select river cells based on MODFLOW river package info
def mf_riv1(self):
    QSWATMOD_path_dict = self.dirs_and_paths()
    input1 = QgsProject.instance().mapLayersByName("mf_grid (MODFLOW)")[0]
    provider = input1.dataProvider()

    # Find .dis file and read number of river cells
    for filename in glob.glob(str(QSWATMOD_path_dict['SMfolder'])+"/*.riv"):
        with open(filename, "r") as f:
            data = []
            for line in f.readlines():
                if not line.startswith("#"):
                    data.append(line.replace('\n', '').split())
        nRiv = int(data[0][0])

    riv_pac_row = []
    riv_pac_col = []

    # Skip two lines in Riv package and get row and col
    for i in range(2, nRiv+2):
        riv_pac_row.append(int(data[i][1]))
        riv_pac_col.append(int(data[i][2]))

    #
    feats = input1.getFeatures()
    riv_matched = []

    for f in feats:
        rowNo = f.attribute("row")
        colNo = f.attribute("col")
        # rowNo = f.attribute["row"]
        # colNo = f.attribute["col"]
        for i in range(len(riv_pac_row)):
            if ((rowNo == riv_pac_row[i]) and (colNo == riv_pac_col[i])):
                riv_matched.append(f.id())
    input1.selectByIds(riv_matched)

    name = "mf_riv1"
    name_ext = "mf_riv1.gpkg"
    output_dir = QSWATMOD_path_dict['org_shps']

    # Save just the selected features of the target layer
    mf_riv_shapefile = os.path.join(output_dir, name_ext)

    # Extract selected features
    processing.run(
        "native:saveselectedfeatures",
        {'INPUT': input1, 'OUTPUT': mf_riv_shapefile}
    )

    # Deselect the features
    input1.removeSelection()
    layer = QgsVectorLayer(mf_riv_shapefile, '{0} ({1})'.format("mf_riv1","MODFLOW"), 'ogr')

    # Put in the group
    root = QgsProject.instance().layerTreeRoot()
    swat_group = root.findGroup("MODFLOW")  
    QgsProject.instance().addMapLayer(layer, False)
    swat_group.insertChildNode(0, QgsLayerTreeLayer(layer))
    layer = QgsProject.instance().addMapLayer(layer)


def create_riv_info(self):
    QSWATMOD_path_dict = self.dirs_and_paths()
    self.layer = QgsProject.instance().mapLayersByName("mf_riv1 (MODFLOW)")[0]
    provider = self.layer.dataProvider()

    # from qgis.core import QgsField, QgsExpression, QgsFeature
    if self.layer.dataProvider().fields().indexFromName("riv_stage") == -1:
        field = QgsField("riv_stage", QVariant.Double, 'double', 20, 5)
        provider.addAttributes([field])
        self.layer.updateFields()
    
    # Obtain col number
    if self.layer.dataProvider().fields().indexFromName("riv_cond") == -1:
        field = QgsField("riv_cond", QVariant.Double, 'double', 20, 5)
        provider.addAttributes([field])
        self.layer.updateFields()

    # Obtain col number
    if self.layer.dataProvider().fields().indexFromName( "riv_bot" ) == -1:
        field = QgsField("riv_bot", QVariant.Double, 'double', 20, 5)
        provider.addAttributes([field])
        self.layer.updateFields()

    # Get the index numbers of the fields
    riv_stage = provider.fields().indexFromName("riv_stage")
    riv_cond = provider.fields().indexFromName("riv_cond")
    riv_bot = provider.fields().indexFromName("riv_bot")

    # Find .riv file and read number of river cells
    for filename in glob.glob(str(QSWATMOD_path_dict['SMfolder'])+"/*.riv"):
        with open(filename, "r") as f:
            data = []
            for line in f.readlines():
                if not line.startswith("#"):
                    data.append(line.replace('\n', '').split())
        nRiv = int(data[0][0])

    riv_pac_row = []
    riv_pac_col = []
    riv_pac_stage = []
    riv_pac_cond = []
    riv_pac_bot = []

    # Skip two lines in Riv package and get row and col
    for i in range(2, nRiv+2):
        riv_pac_row.append(int(data[i][1]))
        riv_pac_col.append(int(data[i][2]))
        riv_pac_stage.append(float(data[i][3]))
        riv_pac_cond.append(float(data[i][4]))
        riv_pac_bot.append(float(data[i][5]))
    #
    feats = self.layer.getFeatures()
    self.layer.startEditing()

    # add riv_info based on row and column numbers
    for f in feats:
        rowNo = f.attribute("row")
        colNo = f.attribute("col")
        for i in range(len(riv_pac_row)):
            if ((rowNo == riv_pac_row[i]) and (colNo == riv_pac_col[i])):
                self.layer.changeAttributeValue(f.id(), riv_stage, riv_pac_stage[i])
                self.layer.changeAttributeValue(f.id(), riv_cond, riv_pac_cond[i])              
                self.layer.changeAttributeValue(f.id(), riv_bot, riv_pac_bot[i])
    self.layer.commitChanges()
    QCoreApplication.processEvents()

# Option 2
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
        {'INPUT': input1, 'OUTPUT':riv_swat_shp}
    )
    # Deselect the features
    input1.removeSelection()

    # layer = QgsVectorLayer(riv_swat_shp, '{0} ({1})'.format("mf_riv2", "MODFLOW"), 'ogr')
    # # Put in the group
    # root = QgsProject.instance().layerTreeRoot()
    # swat_group = root.findGroup("MODFLOW")  
    # QgsProject.instance().addMapLayer(layer, False)
    # swat_group.insertChildNode(0, QgsLayerTreeLayer(layer))
    # layer = QgsProject.instance().addMapLayer(layer)

    # ing: Tried to put it in "createMFmodel_dialog" but not working
    self.dlg.radioButton_mf_riv2.setChecked(1)


# def getElevfromDem_riv2(self):
#   from qgis.analysis import QgsZonalStatistics
#   input1 = QgsProject.instance().mapLayersByName("mf_riv2 (MODFLOW)")[0]
#   input2 = QgsProject.instance().mapLayersByName("DEM (SWAT)")[0]
#   provider = input2.dataProvider()
#   rpath = provider.dataSourceUri()
#   zoneStat = QgsZonalStatistics (input1, rpath, 'elev_', 1, QgsZonalStatistics.Mean)
#   zoneStat.calculateStatistics(None)

# Option 3
def mf_riv3(self):
    QSWATMOD_path_dict = self.dirs_and_paths()
    layer2 = QgsProject.instance().mapLayersByName("mf_riv2 (MODFLOW)")[0]
    layer1 = QgsProject.instance().mapLayersByName("mf_riv1 (MODFLOW)")[0]

    name1 = "mf_riv3_differ"
    name_ext1 = "mf_riv3_differ.gpkg"
    output_dir1 = QSWATMOD_path_dict['org_shps']

    # output_file = os.path.normpath(os.path.join(output_dir, name))
    # Select features by location
    params = { 
        'INPUT' : layer2,
        'PREDICATE': [0],
        'INTERSECT': layer1,
        'METHOD': 3,
    }
    processing.run('qgis:selectbylocation', params)
    layer2.invertSelection()

    # Save just the selected features of the target layer
    mf_riv3_differ = os.path.join(output_dir1, name_ext1)

    # Extract selected features
    processing.run(
        "native:saveselectedfeatures",
        {'INPUT': layer2, 'OUTPUT':mf_riv3_differ}
    )
    layer2.removeSelection()
    name2 = "mf_riv3"
    name_ext2 = "mf_riv3.gpkg"
    output_dir2 = QSWATMOD_path_dict['org_shps']
    output_file2 = os.path.normpath(output_dir2 + "/" + name2)

    # Input layers for merge need to be in list
    params = {
        'LAYERS': [mf_riv3_differ],
        'CRS': layer1.source(),
        'OUTPUT': output_file2
    }
    processing.run("qgis:mergevectorlayers", params)
    # processing.runalg("qgis:mergevectorlayers", [mf_riv3_differ, layer1.source()], output_file2)

    mf_riv3_shapefile = os.path.join(output_dir2, name_ext2)
    layer3 = QgsVectorLayer(mf_riv3_shapefile, '{0} ({1})'.format("mf_riv3","MODFLOW"), 'ogr')

    # Put in the group
    root = QgsProject.instance().layerTreeRoot()
    swat_group = root.findGroup("MODFLOW")  
    QgsProject.instance().addMapLayer(layer3, False)
    swat_group.insertChildNode(0, QgsLayerTreeLayer(layer3))
    layer3 = QgsProject.instance().addMapLayer(layer3)


def overwriteRivPac(self):
    import csv
    import numpy as np

    QSWATMOD_path_dict = self.dirs_and_paths()
    # try:
    if self.dlg.radioButton_mf_riv2.isChecked():
        self.layer = mf_riv2_layer(self)
    elif self.dlg.radioButton_mf_riv3.isChecked():
        self.layer = QgsProject.instance().mapLayersByName("mf_riv3 (MODFLOW)")[0]
    provider = self.layer.dataProvider()
    
    # Get the index numbers of the fields
    grid_id_idx = provider.fields().indexFromName("grid_id")
    row_idx = provider.fields().indexFromName("row")
    col_idx = provider.fields().indexFromName("col")
    riv_stage_idx = provider.fields().indexFromName("riv_stage")
    riv_cond_idx = provider.fields().indexFromName("riv_cond")
    riv_bot_idx = provider.fields().indexFromName("riv_bot")       

    # transfer the shapefile layer to a python list 
    l = []
    for i in self.layer.getFeatures():
        l.append(i.attributes())

    # then sort by grid_id
    import operator
    l_sorted = sorted(l, key=operator.itemgetter(grid_id_idx))

    # Extract grid_ids and layers as lists
    grid_ids = [g[grid_id_idx] for g in l_sorted]
    rows = [r[row_idx] for r in l_sorted]
    cols = [c[col_idx] for c in l_sorted]
    riv_stages = [rs[riv_stage_idx] for rs in l_sorted]
    riv_conds = [rc[riv_cond_idx] for rc in l_sorted]
    riv_bots = [rb[riv_bot_idx] for rb in l_sorted]

    info_number = len(grid_ids)

    # Combine lists into array
    riv_f = np.c_[rows, cols, riv_stages, riv_conds, riv_bots]

    msgBox = QMessageBox()
    msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
    # Find the name of the previous MODFLOW river package -------------- #
    riv_files = [f for f in glob.glob(str(QSWATMOD_path_dict['SMfolder'])+"/*.riv")]
    if len(riv_files) == 1:
        # ------------ Export Data to file -------------- #
        from datetime import datetime
        version = "version 2.10.1."
        time = datetime.now().strftime('- %m/%d/%y %H:%M:%S -')
        with open(riv_files[0], "w", newline='') as f:
            writer = csv.writer(f, delimiter='\t')
            first_row = ["# "+ os.path.basename(riv_files[0]) +" file is overwritten by QSWATMOD2 plugin " + version + time]
            second_row = [str(info_number), "0                # Number of river cells"]
            writer.writerow(first_row)
            writer.writerow(second_row)
            writer.writerow(second_row)
            for item in riv_f:
                writer.writerow(["1",
                    int(item[0]),
                    int(item[1]),
                    '{:f}'.format(item[2]),
                    '{:f}'.format(item[3]),
                    '{:f}'.format(item[4]),
                    "# Layer, Row, Col, Stage, Cond, Rbot"])

        msgBox.setWindowTitle("Great!")
        msgBox.setText(os.path.basename(riv_files[0]) +" file is overwritten successfully!")
        msgBox.exec_()
    elif len(riv_files) > 1:
        msgBox.setWindowTitle("Oops!")
        msgBox.setText(
                        "You have more than one River Package files!("+str(len(riv_files))+")"+"\n"
                        + str(riv_files)+"\n"
                        + "Solution: Keep only one file!")
        msgBox.exec_()
    else:
        msgBox.setWindowTitle("File Not Found!")
        msgBox.setText("We couldn't find your *.riv file.")
        msgBox.exec_()


# Used in Main ui
def rivInfoTo_mf_riv2(self): 
    import csv
    import pandas as pd
    import numpy as np

    QSWATMOD_path_dict = self.dirs_and_paths()
    # try:
    river_grid = QgsProject.instance().mapLayersByName("river_grid (SWAT-MODFLOW)")[0]
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

    data = pd.DataFrame(
        {
            "grid_id": grid_ids,
            "Wid2": widths,
            "Dep2": depths,
            "row": rows,
            "col": cols,
            "top_elev": elevs,
            "rgrid_len": lengths
        }
    )

    hk = self.dlg.lineEdit_riverbedK.text()
    rivBedthick = self.dlg.lineEdit_riverbedThick.text()


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
    self.layer = mf_riv2_layer(self)
    provider2 = self.layer.dataProvider()

    # from qgis.core import QgsField, QgsExpression, QgsFeature
    if self.layer.dataProvider().fields().indexFromName("riv_stage") == -1:
        field = QgsField("riv_stage", QVariant.Double, 'double', 20, 5)
        provider2.addAttributes([field])
        self.layer.updateFields()

    # Obtain col number
    if self.layer.dataProvider().fields().indexFromName("riv_cond" ) == -1:
        field = QgsField("riv_cond", QVariant.Double, 'double', 20, 5)
        provider2.addAttributes([field])
        self.layer.updateFields()

    # Obtain col number
    if self.layer.dataProvider().fields().indexFromName("riv_bot" ) == -1:
        field = QgsField("riv_bot", QVariant.Double, 'double', 20, 5)
        provider2.addAttributes([field])
        self.layer.updateFields()

    # Get the index numbers of the fields
    riv_stage = provider2.fields().indexFromName("riv_stage")
    riv_cond = provider2.fields().indexFromName("riv_cond")
    riv_bot = provider2.fields().indexFromName("riv_bot")  

    #
    feats = self.layer.getFeatures()
    self.layer.startEditing()

    # add riv_info based on row and column numbers
    for f in feats:
        rowNo = f.attribute("row")
        colNo = f.attribute("col")
        for ii in range(len(riv2_cond_lst)):
            if ((rowNo == (row_avg_lst[ii])) and (colNo == (col_avg_lst[ii]))):
                self.layer.changeAttributeValue(f.id(), riv_stage, float(riv2_stage_lst[ii])) # why without float is not working?
                self.layer.changeAttributeValue(f.id(), riv_cond, float(riv2_cond_lst[ii]))             
                self.layer.changeAttributeValue(f.id(), riv_bot, float(riv2_bot_lst[ii]))
    self.layer.commitChanges()
    QCoreApplication.processEvents()


def river_grid_layer(self):
    QSWATMOD_path_dict = self.dirs_and_paths()
    output_dir = QSWATMOD_path_dict['sm_shps']
    name_ext_v = 'river_grid.gpkg'
    output_file_v = os.path.normpath(os.path.join(output_dir, name_ext_v))
    layer = QgsVectorLayer(output_file_v, '{0} ({1})'.format("river_grid","SWAT-MODFLOW"), 'ogr')
    return layer   

def mf_riv2_layer(self):
    QSWATMOD_path_dict = self.dirs_and_paths()
    output_dir = QSWATMOD_path_dict['org_shps']
    name_ext_v = 'mf_riv2.gpkg'
    output_file_v = os.path.normpath(os.path.join(output_dir, name_ext_v))
    layer = QgsVectorLayer(output_file_v, '{0} ({1})'.format("mf_riv2","MODFLOW"), 'ogr')
    return layer


def rivInfoTo_mf_riv2_ii(self):
    import csv
    import pandas as pd
    import numpy as np

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
    self.layer = mf_riv2_layer(self)
    provider2 = self.layer.dataProvider()

    # from qgis.core import QgsField, QgsExpression, QgsFeature
    if self.layer.dataProvider().fields().indexFromName("riv_stage") == -1:
        field = QgsField("riv_stage", QVariant.Double, 'double', 20, 5)
        provider2.addAttributes([field])
        self.layer.updateFields()

    # Obtain col number
    if self.layer.dataProvider().fields().indexFromName( "riv_cond" ) == -1:
        field = QgsField("riv_cond", QVariant.Double, 'double', 20, 5)
        provider2.addAttributes([field])
        self.layer.updateFields()

    # Obtain col number
    if self.layer.dataProvider().fields().indexFromName( "riv_bot" ) == -1:
        field = QgsField("riv_bot", QVariant.Double, 'double', 20, 5)
        provider2.addAttributes([field])
        self.layer.updateFields()

    # Get the index numbers of the fields
    riv_stage = provider2.fields().indexFromName("riv_stage")
    riv_cond = provider2.fields().indexFromName("riv_cond")
    riv_bot = provider2.fields().indexFromName("riv_bot")  

    #
    feats = self.layer.getFeatures()
    self.layer.startEditing()

    # add riv_info based on row and column numbers
    for f in feats:
        rowNo = f.attribute("row")
        colNo = f.attribute("col")
        for ii in range(len(riv2_cond_lst)):
            if ((rowNo == (row_avg_lst[ii])) and (colNo == (col_avg_lst[ii]))):
                self.layer.changeAttributeValue(f.id(), riv_stage, float(riv2_stage_lst[ii])) # why without float is not working?
                self.layer.changeAttributeValue(f.id(), riv_cond, float(riv2_cond_lst[ii]))             
                self.layer.changeAttributeValue(f.id(), riv_bot, float(riv2_bot_lst[ii]))
    self.layer.commitChanges()
    QCoreApplication.processEvents()


def riv_cond_delete_NULL(self):
    if self.dlg.radioButton_mf_riv2.isChecked():
        layer = mf_riv2_layer(self)

    provider = layer.dataProvider()
    request =  QgsFeatureRequest().setFilterExpression("riv_cond IS NULL" )
    request.setSubsetOfAttributes([])
    request.setFlags(QgsFeatureRequest.NoGeometry)

    layer.startEditing()
    for f in layer.getFeatures(request):
        layer.deleteFeature(f.id())
    layer.commitChanges()


def defaultExtent(self):
    # from qgis.PyQt import QtCore, QtGui, QtSql
    try:
        self.layer = QgsProject.instance().mapLayersByName("sub (SWAT)")[0]
        provider = self.layer.dataProvider()
        if self.dlg.checkBox_default_extent.isChecked():
            extent = self.layer.extent()
            x_origin = extent.xMinimum()
            y_origin = extent.yMaximum()
            self.dlg.lineEdit_x_coordinate.setText(str(x_origin))
            self.dlg.lineEdit_y_coordinate.setText(str(y_origin))

    except:
        msgBox = QMessageBox()
        msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
        msgBox.setWindowTitle("?")
        msgBox.setText("There is no 'sub' shapefile!")
        msgBox.exec_()
        self.dlg.checkBox_default_extent.setChecked(0)


# Use observed well point shapefile
def use_obs_points(self):
    QSWATMOD_path_dict = self.dirs_and_paths()

    settings = QSettings()
    if settings.contains('/QSWATMOD2/LastInputPath'):
        path = str(settings.value('/QSWATMOD2/LastInputPath'))
    else:
        path = ''
    title = "Choose MODFLOW observation point shapefile"
    inFileName, __ = QFileDialog.getOpenFileName(None, title, path, "Shapefiles (*.shp);; All files (*.*)")

    if inFileName:
        settings.setValue('/QSWATMOD2/LastInputPath', os.path.dirname(str(inFileName)))
        Out_folder = QSWATMOD_path_dict['org_shps']
        inInfo = QFileInfo(inFileName)
        inFile = inInfo.fileName()
        pattern = os.path.splitext(inFileName)[0] + '.*'
        
        # inName = os.path.splitext(inFile)[0]
        inName = 'mf_obs_points'
        for f in glob.iglob(pattern):
            suffix = os.path.splitext(f)[1]
            if os.name == 'nt':
                outfile = ntpath.join(Out_folder, inName + suffix)
            else:
                outfile = posixpath.join(Out_folder, inName + suffix)
            shutil.copy(f, outfile) 
        if os.name == 'nt':
            mf_obs_points = ntpath.join(Out_folder, inName + ".shp")
        else:
            mf_obs_points = posixpath.join(Out_folder, inName + ".shp")
        
        layer = QgsVectorLayer(mf_obs_points, '{0} ({1})'.format("mf_obs_points","MODFLOW"), 'ogr')

        # Put in the group
        root = QgsProject.instance().layerTreeRoot()
        mf_group = root.findGroup("MODFLOW")    
        QgsProject.instance().addMapLayer(layer, False)
        mf_group.insertChildNode(0, QgsLayerTreeLayer(layer))
        self.dlg.lineEdit_mf_obs_points.setText(mf_obs_points)  


# select
def select_obs_grids(self):
    QSWATMOD_path_dict = self.dirs_and_paths()
    from qgis.PyQt import QtCore, QtGui, QtSql

    input1 = QgsProject.instance().mapLayersByName("mf_grid (MODFLOW)")[0]
    input2 = QgsProject.instance().mapLayersByName("mf_obs_points (MODFLOW)")[0]

    name = "mf_obs_grid"
    name_ext = "mf_obs_grid.shp"
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
    mf_obs_shapefile = os.path.join(output_dir, name_ext)
    QgsVectorFileWriter.writeAsVectorFormat(input1, mf_obs_shapefile,
        "utf-8", input1.crs(), "ESRI Shapefile", 1)

    # Deselect the features
    input1.removeSelection()
    layer = QgsVectorLayer(mf_obs_shapefile, '{0} ({1})'.format("mf_obs","SWAT-MODFLOW"), 'ogr')

    # Put in the group
    root = QgsProject.instance().layerTreeRoot()
    swat_group = root.findGroup("SWAT-MODFLOW") 
    QgsProject.instance().addMapLayer(layer, False)
    swat_group.insertChildNode(0, QgsLayerTreeLayer(layer))
    layer = QgsProject.instance().addMapLayer(layer)
    self.dlg.lineEdit_mf_obs_shapefile.setText(mf_obs_shapefile)  


# navigate to the shapefile of the point observation shapefile
def mf_obs_shapefile(self):
    QSWATMOD_path_dict = self.dirs_and_paths()        
    settings = QSettings()
    if settings.contains('/QSWATMOD2/LastInputPath'):
        path = str(settings.value('/QSWATMOD2/LastInputPath'))
    else:
        path = ''
    title = "choose MODFLOW observation shapefile"
    inFileName, __ = QFileDialog.getOpenFileName(None, title, path, "Shapefiles (*.shp);; All files (*.*)")

    if inFileName:
        settings.setValue('/QSWATMOD2/LastInputPath', os.path.dirname(str(inFileName)))
        Out_folder = QSWATMOD_path_dict['SMshps']
        inInfo = QFileInfo(inFileName)
        inFile = inInfo.fileName()
        pattern = os.path.splitext(inFileName)[0] + '.*'
        
        # inName = os.path.splitext(inFile)[0]
        inName = 'mf_obs_SM'
        for f in glob.iglob(pattern):
            suffix = os.path.splitext(f)[1]
            if os.name == 'nt':
                outfile = ntpath.join(Out_folder, inName + suffix)
            else:
                outfile = posixpath.join(Out_folder, inName + suffix)                    
            shutil.copy(f, outfile) 
        if os.name == 'nt':
            mf_obs_shp = ntpath.join(Out_folder, inName + ".shp")
        else:
            mf_obs_shp = posixpath.join(Out_folder, inName + ".shp")
        
        layer = QgsVectorLayer(mf_obs_shp, '{0} ({1})'.format("mf_obs","SWAT-MODFLOW"), 'ogr')

        # Put in the group
        root = QgsProject.instance().layerTreeRoot()
        sm_group = root.findGroup("SWAT-MODFLOW")   
        QgsProject.instance().addMapLayer(layer, False)
        sm_group.insertChildNode(0, QgsLayerTreeLayer(layer))
        self.dlg.lineEdit_mf_obs_shapefile.setText(mf_obs_shp)     


def create_modflow_obs(self):
    from qgis.PyQt import QtCore, QtGui, QtSql
    self.layer = QgsProject.instance().mapLayersByName("mf_obs (SWAT-MODFLOW)")[0]
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


def export_modflow_obs(self):
    from qgis.PyQt import QtCore, QtGui, QtSql
    import csv
    QSWATMOD_path_dict = self.dirs_and_paths()
    # try:
    self.layer = QgsProject.instance().mapLayersByName("mf_obs (SWAT-MODFLOW)")[0]
    provider = self.layer.dataProvider()

    # Get the index numbers of the fields
    grid_id_index = provider.fields().indexFromName("grid_id")
    layer_index = provider.fields().indexFromName("layer")
    top_elev_idx = provider.fields().indexFromName("top_elev")

    # transfer the shapefile layer to a python list 
    l = []
    for i in self.layer.getFeatures():
        l.append(i.attributes())

    # then sort by grid_id
    import operator
    l_sorted = sorted(l, key=operator.itemgetter(grid_id_index))

    # Extract grid_ids and layers as lists
    grid_ids = [int(g[grid_id_index]) for g in l_sorted]
    layers = [l[layer_index] for l in l_sorted]
    elevs_mf = ['{:.2f}'.format(l[top_elev_idx]) for l in l_sorted]

    info_number = len(grid_ids)
    # Find .dis file and read number of rows, cols, x spacing, and y spacing (not allowed to change)
    for filename in glob.glob(str(QSWATMOD_path_dict['SMfolder'])+"/*.dis"):
        with open(filename, "r") as f:
            data = []
            for line in f.readlines():
                if not line.startswith("#"):
                    data.append(line.replace('\n', '').split())
        nrows = int(data[0][1])
        ncols = int(data[0][2])

    # Generate row and col number for whole modflow grid
    iy = []
    ix = []
    for i in range(1, nrows + 1):
        for j in range(1, ncols + 1):
            ix.append(j)
            iy.append(i)

    # Select row and columns only chosen using grid_id
    nrow = []
    ncol = []
    for grid_id in grid_ids:
        nrow.append(iy[int(grid_id)-1])
        ncol.append(ix[int(grid_id)-1])
    data = list(zip(nrow, ncol, layers, grid_ids, elevs_mf))

    # ------------ Export Data to file -------------- #
    from datetime import datetime
    version = "version 2.10.1."
    time = datetime.now().strftime('- %m/%d/%y %H:%M:%S -')

    name = "modflow.obs"
    output_dir = QSWATMOD_path_dict['SMfolder']
    output_file = os.path.normpath(os.path.join(output_dir, name))
    with open(output_file, "w", newline='') as f:
        writer = csv.writer(f, delimiter = '\t')
        first_row = ["# modflow.obs file is created by QSWATMOD2 plugin " + version + time]
        second_row = [str(info_number), "                # Number of observation cells"]
        writer.writerow(first_row)
        writer.writerow(second_row)
        for item in data:
            writer.writerow([item[0], item[1], item[2], item[3], item[4],
                            "# Row, Col, Layer, grid_id, elevation "])

    # except:
    #     msgBox = QMessageBox()
    #     msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
    #     msgBox.setIconPixmap(QtGui.QPixmap(':/QSWATMOD2/pics/modflow_obs.png'))
    #     msgBox.setWindowTitle("Oops!")
    #     msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
    #     msgBox.exec_()


def import_mf_grid(self):
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

        time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
        self.dlg.textEdit_sm_link_log.append(time+' -> ' + "Importing MODFLOW object ... processing")
        self.dlg.label_StepStatus.setText("Importing 'MODFLOW object' ... ")
        self.dlg.progressBar_step.setValue(0)
        QCoreApplication.processEvents()

        # inName = os.path.splitext(inFile)[0]
        inName = 'mf_grid_org'
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
                mf_grid_obj = ntpath.join(output_dir, inName + ".gpkg")
            else:
                mf_grid_obj = posixpath.join(output_dir, inName + ".gpkg")
        else:
            if os.name == 'nt':
                mf_grid_obj = ntpath.join(output_dir, inName + ".shp")
            else:
                mf_grid_obj = posixpath.join(output_dir, inName + ".shp")    
        # convert to gpkg
        mf_grid_gpkg_file = 'mf_grid.gpkg'
        mf_grid_gpkg = os.path.join(output_dir, mf_grid_gpkg_file)
        params = {
            'INPUT': mf_grid_obj,
            'OUTPUT': mf_grid_gpkg
        }
        processing.run('native:fixgeometries', params)
        layer = QgsVectorLayer(mf_grid_gpkg, '{0} ({1})'.format("mf_grid","MODFLOW"), 'ogr')        

        # if there is an existing mf_grid shapefile, it will be removed
        for lyr in list(QgsProject.instance().mapLayers().values()):
            if lyr.name() == ("mf_grid (MODFLOW)"):
                QgsProject.instance().removeMapLayers([lyr.id()])

        # Put in the group
        root = QgsProject.instance().layerTreeRoot()
        swat_group = root.findGroup("MODFLOW")  
        QgsProject.instance().addMapLayer(layer, False)
        swat_group.insertChildNode(0, QgsLayerTreeLayer(layer))
        self.dlg.lineEdit_MODFLOW_grid_shapefile.setText(mf_grid_gpkg) 

        time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
        self.dlg.textEdit_sm_link_log.append(time+' -> ' + "Importing MODFLOW object ... passed")
        self.dlg.label_StepStatus.setText("Step Status: ")
        self.dlg.progressBar_step.setValue(100)
        QCoreApplication.processEvents()


# Create "modflow.mfn" file
def create_modflow_mfn(self):
    import datetime
    QSWATMOD_path_dict = self.dirs_and_paths()
    wd = QSWATMOD_path_dict['SMfolder']
    for filename in glob.glob(wd + "/*.nam"):
        version = "version 2.10.1."
        time = datetime.datetime.now().strftime(' - %m/%d/%y %H:%M:%S -')
        info = "# modflow.mfn file, generated by QSWATMOD2 plugin "+version+ time +'\n'
        lines = []
        lines.append(info)

        with open(filename) as infile:
            data = [x.strip() for x in infile if x.strip()]
        for line in data:
            if line.startswith("#"):
                lines.append(line + '\n')
            elif len(line.split()[1]) < 4:
                a = line.split()[1]
                b = int(line.split()[1]) + 5000
                line = line.split()[0] + "\t" + str(b) + "\t" + line.split()[2]
                lines.append(line + '\n')
                file = "modflow_EditLog.txt"
                time = datetime.datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
                with open(os.path.join(wd, file), 'a') as outfile:
                    outfile.write(str(time +' -> modflow.mfn: Unit number '+a+' -> '+str(b)+'\n'))
            else:
                lines.append(line + '\n')

        ''' It causes error with blank lines and ignore comment lines.
        # with open(filename) as infile:
        #     for line in infile:
        #         data = line.strip().split()
        #         if not line.startswith("#") and len(data[1]) != 4:  # filter unnecessary lines
        #             a = data[1] # read previous unit numbers
        #             b = int(data[1])+5000 # add 5000 to previous number
        #             data[1] = str(b)  # modify unit number
        #             data1 = "\t".join(data) + "\n" # change list to line
        #             lines.append(data1)
        #             file = "modflow_EditLog.txt"
        #             time = datetime.datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
        #             with open(os.path.join(wd, file), 'a') as outfile:
        #                 outfile.write(str(time +' -> modflow.mfn: Unit number '+a+' -> '+str(b)+'\n')) 
        #         else:
        #             lines.append(line)
        '''

        with open(os.path.join(wd, 'modflow.mfn'), 'w') as outfile:
            for line in lines:
                outfile.write(line)


# Modify *.oc file
def modify_modflow_oc(self):
    import datetime
    QSWATMOD_path_dict = self.dirs_and_paths()
    wd = QSWATMOD_path_dict['SMfolder']
    for filename in glob.glob(wd + "/*.oc"):
        version = "version 2.10.1."
        time = datetime.datetime.now().strftime(' - %m/%d/%y %H:%M:%S -')
        info = "# Output Control file, modified by QSWATMOD2 plugin "+version+ time +'\n'

        lines = []
        lines.append(info)
        with open(filename) as infile:
            for line in infile:
                data = line.strip().split()
                if line.startswith("HEAD SAVE UNIT") and len(data[3]) != 4: # filter unnecessary lines
                    a = data[3]  # read previous unit numbers
                    b = int(data[3])+5000  # add 5000 to previous number
                    data[3] = str(b)  # modify unit number
                    data1 = "\t".join(data) + "\n" # change list to line
                    lines.append(data1)
                    file = "modflow_EditLog.txt"
                    time = datetime.datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
                    with open(os.path.join(wd, file), 'a') as outfile:
                        outfile.write(str(time+' -> '+os.path.basename(filename)+': Unit number '+a+' -> '+str(b)+'\n')) 
                else:
                    lines.append(line)
        with open(os.path.join(wd, os.path.basename(filename)), 'w') as outfile:
            for line in lines:
                outfile.write(line)


def modflow_ss_to_tr(self):
    for filename in glob.glob(str(QSWATMOD_path_dict['SMfolder'])+"/*.dis"):
        # check whether it works
        # os.startfile(filename)
        lines = []
        with open(filename) as infile:
            for line in infile:
                data = line.strip().split()
                try:
                    a = data[3]
                    if a == 'ss' or a == 'SS':
                        line = line.replace(a, 'TR')
                        msgBox = QMessageBox()
                        msgBox.setText("Oops!!!" + str(a))
                        msgBox.exec_()
                        file = "editLog.txt"
                        with open(os.path.join(QSWATMOD_path_dict['SMfolder'], file), 'a') as outfile:
                            outfile.write(str("the .dis file was changed from "+ a+" to TR")) 
                    elif a == 'TR':
                        msgBox = QMessageBox()
                        msgBox.setText("Good job!")
                        msgBox.exec_()

                except IndexError:
                    a = 'null'
                lines.append(line)

        with open(filename, 'w') as outfile:
            for line in lines:
                outfile.write(line)

    self.dlg.pushButton_execute_linking.setEnabled(True)

###### this might be an option for MODFLOW-USG, but for now not used for efficiency
# def calculate_grid_area(self):
#   #layer = qgis.utils.iiface.activeLayer()
#   self.layer = QgsProject.instance().mapLayersByName("mf_grid (MODFLOW)")[0]
#   provider = self.layer.dataProvider()
#   from PyQt4.QtCore import QVariant
#   from qgis.core import QgsField, QgsExpression, QgsFeature

#   if self.layer.dataProvider().fields().indexFromName( "grid_area" ) == -1:
            
#       # field = QgsField("grid_area", QVariant.Double,'double', 20, 5)
#       field = QgsField("grid_area", QVariant.Int)        
#       provider.addAttributes([field])
#       self.layer.updateFields()
    
#   feats = self.layer.getFeatures()
#   self.layer.startEditing()

#   for feat in feats:
#      area = feat.geometry().area()
#      #score = scores[i]
#      feat['grid_area'] = area
#      self.layer.updateFeature(feat)
#   self.layer.commitChanges()
######


