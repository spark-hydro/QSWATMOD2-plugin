# -*- coding: utf-8 -*-
from builtins import zip
from builtins import str
from builtins import range
import os
import os.path
import processing
from qgis.core import (
        QgsVectorLayer, QgsField,
        QgsFeatureIterator, QgsVectorFileWriter,
        QgsProject, QgsLayerTreeLayer
        )
import glob
from qgis.PyQt.QtCore import QVariant, QSettings, QFileInfo
from qgis.PyQt import QtCore, QtGui, QtSql
import datetime
import csv
import posixpath
import ntpath
import shutil
from PyQt5.QtWidgets import QMessageBox, QFileDialog

msgBox = QMessageBox()
msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))


def create_conv_runoff(self):
    QSWATMOD_path_dict = self.dirs_and_paths()

    # Create swatmf_results tree inside 
    root = QgsProject.instance().layerTreeRoot()
    if root.findGroup("SWAT-MODFLOW"):
        SM = root.findGroup("SWAT-MODFLOW")
        SM.insertGroup(0, "Scenarios")
        scenario_tree = root.findGroup("Scenarios")
        scenario_tree.addGroup("Pumping from MODFLOW")
        input1 = QgsProject.instance().mapLayersByName("sub (SWAT)")[0]

        # Copy sub shapefile to be under "p from mf"
        name = "conv_runoff"
        name_ext = "conv_runoff.shp"
        output_dir = QSWATMOD_path_dict['Scenarios']

        # Check if there is an exsting mf_head shapefile
        # if not any(lyr.name() == ("conv_runoff") for lyr in QgsProject.instance().mapLayers().values()):
        conv_runoff_shapfile = os.path.join(output_dir, name_ext)
        QgsVectorFileWriter.writeAsVectorFormat(
            input1, conv_runoff_shapfile,
            "utf-8", input1.crs(), "ESRI Shapefile")
        layer = QgsVectorLayer(conv_runoff_shapfile, '{0}'.format("conv_runoff"), 'ogr')

        # Put in the group
        # root = QgsProject.instance().layerTreeRoot()
        # conv_runoff = root.findGroup("Pumping from MODFLOW")
        QgsProject.instance().addMapLayer(layer, False)
        p_mf_tree = root.findGroup("Pumping from MODFLOW")
        p_mf_tree.insertChildNode(0, QgsLayerTreeLayer(layer))

        input2 = QgsProject.instance().mapLayersByName("conv_runoff")[0]
        fields = input2.dataProvider()

        fdname = [
                fields.fields().indexFromName(field.name()) for field in fields.fields()
                if not field.name() == 'Subbasin'
                ]
        fields.deleteAttributes(fdname)
        input2.updateFields()

        cvy = QgsField('Conveyance', QVariant.Double, 'double', 20, 5)
        runoff = QgsField('Runoff', QVariant.Double, 'double', 20, 5)
        fields.addAttributes([cvy, runoff])
        input2.updateFields()
        cvy_idx = fields.fields().indexFromName('Conveyance')
        runoff_idx = fields.fields().indexFromName('Runoff')
        feats = input2.getFeatures()
        input2.startEditing()

        for feat in feats:
            # attr = feat.attributes() #  this can be used for changing value based on value from other column
            input2.changeAttributeValue(feat.id(), cvy_idx, 1)
            input2.changeAttributeValue(feat.id(), runoff_idx, 0.05)
        input2.commitChanges()

        # msgBox = QMessageBox()
        # msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
        msgBox.setWindowTitle("Created!")
        msgBox.setText("'conv_runoff.shp' file has been created!")
        msgBox.exec_()

        # FIXME, TODO: require escapting code to check *.wel file.
        # Find *.wel file and read number of grid cells and set maximum grid cells
        # try:
        for filename in glob.glob(QSWATMOD_path_dict['SMfolder']+"/*.wel"):
            with open(filename, "r") as f:
                data = []
                for line in f.readlines():
                    if not line.startswith("#"):
                        data.append(line.replace('\n', '').split())
        wel_max = int(data[0][0])
        self.dlg.spinBox_irrig_mf.setMaximum(wel_max)
        self.dlg.spinBox_irrig_mf.setValue(wel_max)
        
        msgBox.setWindowTitle("Created!")
        msgBox.setText("{} file has been created!".format(wel_max))
        msgBox.exec_()
        
        
        # except:
        #     msgBox.setWindowTitle("No Well package found!")
        #     msgBox.setText("Please, provide a well package to your MODFLOW model first!")
        #     self.dlg.spinBox_irrig_mf.setEnabled(False)
        #     msgBox.exec_()
    else:
        msgBox.setWindowTitle("Error!")
        msgBox.setText("Your project couldn't be read.\nPlease, go back to the linking process!")
        msgBox.exec_()


def link_irrig_mf(self):
    QSWATMOD_path_dict = self.dirs_and_paths()
    self.layer = QgsProject.instance().mapLayersByName("mf_grid (MODFLOW)")[0]
    input1 = QgsProject.instance().mapLayersByName("mf_grid (MODFLOW)")[0]
    provider = self.layer.dataProvider()
    welnum = self.dlg.spinBox_irrig_mf.value()
    # Find *.wel file and read number of grid cells
    # try:
    for filename in glob.glob(str(QSWATMOD_path_dict['SMfolder'])+"/*.wel"):
        with open(filename, "r") as f:
            data = []
            for line in f.readlines():
                if not line.startswith("#"):
                    data.append(line.replace('\n', '').split())
    wel_row = []
    wel_col = []

    # Skip two lines in Riv package and get row and col
    for i in range(2, welnum+2):
        wel_row.append(int(data[i][1]))
        wel_col.append(int(data[i][2]))

    # Find grid cells according to the well package
    feats = self.layer.getFeatures()
    wel_matched = []

    for f in feats:
        rowNo = f.attribute("row")
        colNo = f.attribute("col")
        # rowNo = f.attribute["row"]
        # colNo = f.attribute["col"]
        for i in range(len(wel_row)):
            if ((rowNo == wel_row[i]) and (colNo == wel_col[i])):
                wel_matched.append(f.id())
    self.layer.selectByIds(wel_matched)

    name = "irrig_mf"
    name_ext = "irrig_mf.shp"
    output_dir = QSWATMOD_path_dict['Scenarios']

    # Save just the selected features of the target layer
    irrig_mf = os.path.join(output_dir, name_ext)

    # QgsVectorFileWriter.deleteShapeFile(irrig_mf)

    QgsVectorFileWriter.writeAsVectorFormat(
        input1, irrig_mf,
        "utf-8", input1.crs(), "ESRI Shapefile", 1)

    # Deselect the features
    self.layer.removeSelection()

    # Join sub and hru id
    n3_ext = "irrig_mf_s.shp"
    irrig_mf_s = os.path.join(output_dir, n3_ext)
    # QgsVectorFileWriter.deleteShapeFile(irrig_mf_s)
    sub_shp = QgsProject.instance().mapLayersByName("sub (SWAT)")[0]
    params = {
        'INPUT':irrig_mf,
        'JOIN': sub_shp,
        'PREDICATE': [0],
        'METHOD': 0,
        'DISCARD_NONMATCHING': False,
        'OUTPUT': irrig_mf_s,
    }
    processing.run("qgis:joinattributesbylocation", params)

    # Join sub id
    n4_ext = "irrig_mf_f.shp"
    irrig_mf_f = os.path.join(output_dir, n4_ext)
    # QgsVectorFileWriter.deleteShapeFile(irrig_mf_f)
    hru_shp = QgsProject.instance().mapLayersByName("hru (SWAT)")[0]

    params02 = {
        'INPUT':irrig_mf_s,
        'JOIN': hru_shp,
        'PREDICATE': [0],
        'METHOD': 0,
        'DISCARD_NONMATCHING': False,
        'OUTPUT': irrig_mf_f,
    }
    processing.run("qgis:joinattributesbylocation", params02)

    # delete unnecessary fields
    layer_mf = QgsVectorLayer(irrig_mf_f, '{0}'.format("irrig_mf"), 'ogr')
    QgsProject.instance().addMapLayer(layer_mf, False)
    root = QgsProject.instance().layerTreeRoot()
    p_mf_tree = root.findGroup("Pumping from MODFLOW")
    p_mf_tree.insertChildNode(0, QgsLayerTreeLayer(layer_mf))
    input2 = QgsProject.instance().mapLayersByName("irrig_mf")[0]
    fields = input2.dataProvider()
    fdname = [
            fields.fields().indexFromName(field.name()) for field in fields.fields() if not (
                field.name() == 'Subbasin' or
                field.name() == 'row' or
                field.name() == 'col' or
                field.name() == 'HRU_ID'
                )
            ]

    fields.deleteAttributes(fdname)
    input2.updateFields()

    msgBox.setWindowTitle("Created!")
    msgBox.setText(
                    "'irrig_mf.shp' file has been created!\n"+
                    "If you have multiple HRUs, open its Attribute table and modify it."
                    )
    msgBox.exec_()


def create_irrig_mf(self):
    import operator
    #read in the irrig_mf
    layer = QgsProject.instance().mapLayersByName("irrig_mf")[0]
    data = [i.attributes() for i in layer.getFeatures()]

    # Get the index numbers of the fields
    row_idx = layer.dataProvider().fields().indexFromName("row")
    col_idx = layer.dataProvider().fields().indexFromName("col")
    sub_idx = layer.dataProvider().fields().indexFromName("Subbasin")
    hru_idx = layer.dataProvider().fields().indexFromName("HRU_ID")

    # read conv_runoff 
    layer2 = QgsProject.instance().mapLayersByName("conv_runoff")[0]
    data2 = [i.attributes() for i in layer2.getFeatures()]

    # Get the index numbers of the fields
    sub2_idx = layer2.dataProvider().fields().indexFromName("Subbasin")
    cv_idx = layer2.dataProvider().fields().indexFromName("Conveyance")
    ro_idx = layer2.dataProvider().fields().indexFromName("Runoff")

    # Sort
    data2_sort = sorted(data2, key=operator.itemgetter(sub2_idx))

    # read HRUs that obtains water from MF well
    sub = []
    hru = []
    for row in data:
        for col in range(3, len(row)):
            if row[col] != None:  # if row[col] is not None: --> not working
                sub.append(row[2])
                hru.append(row[col])
    data_h = list(zip(sub, hru))

    # export file
    QSWATMOD_path_dict = self.dirs_and_paths()
    name = "swatmf_irrigate.txt"
    out_dir = QSWATMOD_path_dict['SMfolder']
    out_file = os.path.join(out_dir, name)

    # Add info
    version = "version 2.10.1"
    time = datetime.datetime.now().strftime('- %m/%d/%y %H:%M:%S -')

    # User inputs ===========================================================================
    welnum = int(self.dlg.spinBox_irrig_mf.value())
    L1 = [
        "# This file contains a listing of MODFLOW grid cells, and their associated SWAT sub-basins" +
        ", created by QSWATMOD2 plugin " + version + time]
    L2 = [str(welnum) + "       # Number of grid cells that provide irrigation water"]
    B1 = ["# Conveyance efficiency, Runoff Ratio for each sub-basin"]
    B2 = ["# Sub    Row    Col    HRU_ID"]
    B3 = ["# HRUs that receive irrigation water (Subbasin, HRU ID)"]
    B4 = [str(len(sub))]
    with open(out_file, "w", newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(L1)
        writer.writerow(L2)
        writer.writerow(B1)
        for item in data2_sort:
            writer.writerow([item[cv_idx], item[ro_idx]])
        writer.writerow(B2)
        for item in data:
            writer.writerow([item[sub_idx], item[row_idx], item[col_idx], item[hru_idx]])
        writer.writerow(B3)
        writer.writerow(B4)
        for item in data_h:
            writer.writerow([item[0], item[1]])
    msgBox.setWindowTitle("Created!")
    msgBox.setText(
                    "'swatmf_irrigate.txt' file has been created successfully!"
                    )
    msgBox.exec_()


def link_drain(self):
    # Create Scenarios tree inside 
    root = QgsProject.instance().layerTreeRoot()  
    if not root.findGroup("Scenarios"):
        sm_tree = root.findGroup("SWAT-MODFLOW")
        sm_tree.addGroup("Scenarios")
    if not root.findGroup("Drains to SWAT Channels"):
        scenario_tree = root.findGroup("Scenarios")
        scenario_tree.addGroup("Drains to SWAT Channels")

    try:
        QSWATMOD_path_dict = self.dirs_and_paths()
        self.layer = QgsProject.instance().mapLayersByName("mf_grid (MODFLOW)")[0]
        input1 = QgsProject.instance().mapLayersByName("mf_grid (MODFLOW)")[0]
        provider = self.layer.dataProvider()
        # Find *.drn file and read number of grid cells
        for filename in glob.glob(str(QSWATMOD_path_dict['SMfolder'])+"/*.drn"):
            with open(filename, "r") as f:
                data = []
                for line in f.readlines():
                    if not line.startswith("#"):
                        data.append(line.replace('\n', '').split())
        nDrain = int(data[0][0])
        drn_lyr = []
        drn_row = []
        drn_col = []

        # Skip two lines in Riv package and get row and col
        for i in range(2, nDrain+2):
            drn_lyr.append(int(data[i][0]))
            drn_row.append(int(data[i][1]))
            drn_col.append(int(data[i][2]))

        # Find grid cells according to the drnl package
        feats = self.layer.getFeatures()
        drn_matched = []

        for f in feats:
            rowNo = f.attribute("row")
            colNo = f.attribute("col")
            for i in range(len(drn_row)):
                if ((rowNo == drn_row[i]) and (colNo == drn_col[i])):
                    drn_matched.append(f.id())
        self.layer.selectByIds(drn_matched)

        name_ext = "drain2sub.shp"
        output_dir = QSWATMOD_path_dict['Scenarios']

        # Save just the selected features of the target layer
        drn_chn = os.path.join(output_dir, name_ext)
        QgsVectorFileWriter.writeAsVectorFormat(
            input1, drn_chn,
            "utf-8", input1.crs(), "ESRI Shapefile", 1)

        # Deselect the features
        self.layer.removeSelection()
        # Join sub and drn
        n2_ext = "drain2sub_f.shp"
        drn_chn_f = os.path.join(output_dir, n2_ext)
        # QgsVectorFileWriter.deleteShapeFile(irrig_mf_s)
        sub_shp = QgsProject.instance().mapLayersByName("sub (SWAT)")[0]
        parmas = {
            'INPUT': drn_chn,
            'JOIN': sub_shp,
            'PREDICATE': [0],
            'METHOD': 0,
            'DISCARD_NONMATCHING': False,
            'OUTPUT':drn_chn_f
            }
        processing.run(
                        "qgis:joinattributesbylocation",
                        parmas)

        # delete unnecessary fields
        layer_drn = QgsVectorLayer(drn_chn_f, '{0}'.format("drain2sub"), 'ogr')
        QgsProject.instance().addMapLayer(layer_drn, False)
        root = QgsProject.instance().layerTreeRoot()
        p_mf_tree = root.findGroup("Drains to SWAT Channels")
        p_mf_tree.insertChildNode(0, QgsLayerTreeLayer(layer_drn))

        input2 = QgsProject.instance().mapLayersByName("drain2sub")[0]
        input2_provider = input2.dataProvider()
        fdnames = [
                    input2_provider.fields().indexFromName(field.name()) for field in input2_provider.fields() if not (
                        field.name() == 'Subbasin' or
                        field.name() == 'row' or
                        field.name() == 'col' or
                        field.name() == 'layer')
                        ]
        input2_provider.deleteAttributes(fdnames)
        input2.updateFields()
        msgBox.setWindowTitle("Created!")
        msgBox.setText("'drain2sub.shp' file has been created!")
        msgBox.exec_()
    except:
        msgBox.setWindowTitle("No Drain package found!")
        msgBox.setText("Please, provide a drain package to your MODFLOW model first!")
        self.dlg.spinBox_irrig_mf.setEnabled(False)
        self.dlg.pushButton_irrig_mf.setEnabled(False)
        self.dlg.pushButton_irrig_mf_create.setEnabled(False)
        msgBox.exec_()


def create_drain2sub(self):
    # read drain2sub
    layer = QgsProject.instance().mapLayersByName("drain2sub")[0]
    data = [i.attributes() for i in layer.getFeatures()]

    # Get the index numbers of the fields
    row_idx = layer.dataProvider().fields().indexFromName("row")
    col_idx = layer.dataProvider().fields().indexFromName("col")
    sub_idx = layer.dataProvider().fields().indexFromName("Subbasin")

    # export file
    QSWATMOD_path_dict = self.dirs_and_paths()
    name = "swatmf_drain2sub.txt"
    out_dir = QSWATMOD_path_dict['SMfolder']
    out_file = os.path.join(out_dir, name)

    # Add info
    version = "version 2.10.1 "
    time = datetime.datetime.now().strftime('- %m/%d/%y %H:%M:%S -')

    # User inputs ===========================================================================
    L1 = [
        str(len(data)) + "  # Number of MODFLOW DRAIN cells that contribute water to SWAT subbasins"+
        ", created by QSWATMOD2 plugin " + version + time]
    L2 = ["# Row    Column    Subbasion"]
    with open(out_file, "w", newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(L1)
        writer.writerow(L2)
        for item in data:
            writer.writerow([item[row_idx], item[col_idx], item[sub_idx]])

    msgBox.setWindowTitle("Created!")
    msgBox.setText(
                    "'swatmf_drain2sub.txt' file has been created successfully!"
                    )
    msgBox.exec_()


def create_irrig_swat_tree(self):
    root = QgsProject.instance().layerTreeRoot()
    if not root.findGroup("Scenarios"):
        sm_tree = root.findGroup("SWAT-MODFLOW")
        sm_tree.addGroup("Scenarios")
    if not root.findGroup("Pumping from SWAT"):
        scenario_tree = root.findGroup("Scenarios")
        scenario_tree.addGroup("Pumping from SWAT")


# Use observed well point shapefile
def use_irrig_swat_pts(self):
    QSWATMOD_path_dict = self.dirs_and_paths()

    settings = QSettings()
    if settings.contains('/QSWATMOD2/LastInputPath'):
        path = str(settings.value('/QSWATMOD2/LastInputPath'))
    else:
        path = ''
    title = "Choose Pumping Well point shapefile"
    inFileName, __ = QFileDialog.getOpenFileName(None, title, path, "Shapefiles (*.shp);; All files (*.*)")

    if inFileName:
        settings.setValue('/QSWATMOD2/LastInputPath', os.path.dirname(str(inFileName)))
        Out_folder = QSWATMOD_path_dict['Scenarios']
        inInfo = QFileInfo(inFileName)
        inFile = inInfo.fileName()
        pattern = os.path.splitext(inFileName)[0] + '.*'

        # inName = os.path.splitext(inFile)[0]
        inName = 'irrig_swat_pts'
        for f in glob.iglob(pattern):
            suffix = os.path.splitext(f)[1]
            if os.name == 'nt':
                outfile = ntpath.join(Out_folder, inName + suffix)
            else:
                outfile = posixpath.join(Out_folder, inName + suffix)
            shutil.copy(f, outfile) 
        if os.name == 'nt':
            irrig_swat_pts = ntpath.join(Out_folder, inName + ".shp")
        else:
            irrig_swat_pts = posixpath.join(Out_folder, inName + ".shp")
        
        layer = QgsVectorLayer(irrig_swat_pts, '{0}'.format("irrig_swat_pts"), 'ogr')

        # Put in the group
        root = QgsProject.instance().layerTreeRoot()
        p_swat_group = root.findGroup("Pumping from SWAT")
        QgsProject.instance().addMapLayer(layer, False)
        p_swat_group.insertChildNode(0, QgsLayerTreeLayer(layer))
        self.dlg.lineEdit_irrig_swat_pts.setText(irrig_swat_pts)  


# select
def select_irrig_swat_grids(self):
    QSWATMOD_path_dict = self.dirs_and_paths()
    # from PyQt4 import QtCore, QtGui, QtSql

    input1 = QgsProject.instance().mapLayersByName("mf_grid (MODFLOW)")[0]
    input2 = QgsProject.instance().mapLayersByName("irrig_swat_pts")[0]

    # name = "mf_obs_grid"
    name_ext = "irrig_swat_grid.shp"
    output_dir = QSWATMOD_path_dict['Scenarios']

    # output_file = os.path.normpath(os.path.join(output_dir, name))
    # Select features by location

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
    irrig_swat_grid = os.path.join(output_dir, name_ext)
    QgsVectorFileWriter.writeAsVectorFormat(
        input1, irrig_swat_grid,
        "utf-8", input1.crs(), "ESRI Shapefile", 1)

    # Deselect the features
    input1.removeSelection()


# navigate to the shapefile of the irrig_swat_grid
def irrig_swat_selected(self):
    QSWATMOD_path_dict = self.dirs_and_paths()        
    settings = QSettings()
    if settings.contains('/QSWATMOD2/LastInputPath'):
        path = str(settings.value('/QSWATMOD2/LastInputPath'))
    else:
        path = ''
    title = "Select Irrig SWAT Grid shapefile"
    inFileName, __ = QFileDialog.getOpenFileName(None, title, path, "Shapefiles (*.shp);; All files (*.*)")

    if inFileName:
        settings.setValue('/QSWATMOD2/LastInputPath', os.path.dirname(str(inFileName)))
        Out_folder = QSWATMOD_path_dict['Scenarios']
        inInfo = QFileInfo(inFileName)
        inFile = inInfo.fileName()
        pattern = os.path.splitext(inFileName)[0] + '.*'

        # inName = os.path.splitext(inFile)[0]
        inName = 'irrig_swat_grid'
        for f in glob.iglob(pattern):
            suffix = os.path.splitext(f)[1]
            if os.name == 'nt':
                outfile = ntpath.join(Out_folder, inName + suffix)
            else:
                outfile = posixpath.join(Out_folder, inName + suffix)
            shutil.copy(f, outfile)


def link_irrig_swat(self):
    QSWATMOD_path_dict = self.dirs_and_paths()
    output_dir = QSWATMOD_path_dict['Scenarios']
    name_ext = "irrig_swat_grid.shp"
    irrig_swat_grid = os.path.join(output_dir, name_ext)

    # Create layer field
    layer_swat_col = QgsVectorLayer(irrig_swat_grid, '{0}'.format("irrig_swat_grid"), 'ogr')
    lyrProvider = layer_swat_col.dataProvider()
    if lyrProvider.fields().indexFromName('layer') == -1:
        lyr_field = QgsField('layer', QVariant.Int)
        lyrProvider.addAttributes([lyr_field])
        layer_swat_col.updateFields()

        # Get the index numbers of the fields
        lyrIdx = lyrProvider.fields().indexFromName('layer')

        # Get features (Find out a way to change attribute values using another field)
        feats = layer_swat_col.getFeatures()
        layer_swat_col.startEditing()

        # add layer number
        for f in feats:
            layer_swat_col.changeAttributeValue(f.id(), lyrIdx, 1)
        layer_swat_col.commitChanges()

    # Join sub and hru id
    n3_ext = "irrig_swat_grid_s.shp"
    irrig_swat_grid_s = os.path.join(output_dir, n3_ext)
    # QgsVectorFileWriter.deleteShapeFile(irrig_mf_s)
    sub_shp = QgsProject.instance().mapLayersByName("sub (SWAT)")[0]

    params = {
        'INPUT':irrig_swat_grid,
        'JOIN': sub_shp,
        'PREDICATE': [0],
        'METHOD': 0,
        'DISCARD_NONMATCHING': False,
        'OUTPUT': irrig_swat_grid_s,
    }
    processing.run("qgis:joinattributesbylocation", params)



    # processing.run(
    #                 "qgis:joinattributesbylocation",
    #                 irrig_swat_grid,
    #                 sub_shp,
    #                 ['intersects'],0,0,"sum,mean,min,max,median",0,
    #                 irrig_swat_grid_s)

    # Join sub id
    n4_ext = "irrig_swat_grid_f.shp"
    irrig_swat_grid_f = os.path.join(output_dir, n4_ext)
    # QgsVectorFileWriter.deleteShapeFile(irrig_mf_f)
    hru_shp = QgsProject.instance().mapLayersByName("hru (SWAT)")[0]

    params02 = {
        'INPUT':irrig_swat_grid_s,
        'JOIN': hru_shp,
        'PREDICATE': [0],
        'METHOD': 0,
        'DISCARD_NONMATCHING': False,
        'OUTPUT': irrig_swat_grid_f,
    }
    processing.run("qgis:joinattributesbylocation", params02)


    layer_swat = QgsVectorLayer(irrig_swat_grid_f, '{0}'.format("irrig_swat"), 'ogr')
    QgsProject.instance().addMapLayer(layer_swat, False)
    root = QgsProject.instance().layerTreeRoot()
    p_swat_tree = root.findGroup("Pumping from SWAT")
    p_swat_tree.insertChildNode(0, QgsLayerTreeLayer(layer_swat))
    self.dlg.lineEdit_irrig_swat_grids.setText(irrig_swat_grid_f)

    # delete unnecessary fields
    input2 = QgsProject.instance().mapLayersByName("irrig_swat")[0]
    fields = input2.dataProvider()
    fdname = [
                fields.fields().indexFromName(field.name()) for field in fields.fields() if not (
                    field.name() == 'Subbasin' or
                    field.name() == 'row' or
                    field.name() == 'col' or
                    field.name() == 'HRU_ID' or
                    field.name() == 'layer')]

    fields.deleteAttributes(fdname)
    input2.updateFields()
    msgBox.setWindowTitle("Created!")
    msgBox.setText(
                    "'irrig_swat.shp' file has been created!\n"+
                    "If you have multiple HRUs for a well, open its Attribute table and modify it."
                    )
    msgBox.exec_()


def write_irrig_swat(self):
    import operator
    # read in the irrig_mf
    layer = QgsProject.instance().mapLayersByName("irrig_swat")[0]
    data = [i.attributes() for i in layer.getFeatures()]

    # Get the index numbers of the fields
    row_idx = layer.dataProvider().fields().indexFromName("row")
    col_idx = layer.dataProvider().fields().indexFromName("col")
    sub_idx = layer.dataProvider().fields().indexFromName("Subbasin")
    hru_idx = layer.dataProvider().fields().indexFromName("HRU_ID")
    lyr_idx = layer.dataProvider().fields().indexFromName("layer")

    # Sort
    data_sort = sorted(data, key=operator.itemgetter(sub_idx))

    # read HRUs that obtains water from MF well
    sub = []
    row = []
    col = []
    lay = []
    hru = []
    for l in data_sort:
        for f in range(4, len(l)):
            if l[f] != None:
                sub.append(l[sub_idx])
                row.append(l[row_idx])
                col.append(l[col_idx])
                lay.append(l[lyr_idx])
                hru.append(l[f])
    data_f = list(zip(sub, row, col, lay, hru))

    # export file
    QSWATMOD_path_dict = self.dirs_and_paths()
    name = "swatmf_irrigate.txt"
    out_dir = QSWATMOD_path_dict['SMfolder']
    out_file = os.path.join(out_dir, name)

    # Add info
    version = "version 2.10.1 "
    time = datetime.datetime.now().strftime('- %m/%d/%y %H:%M:%S -')

    # User inputs ===========================================================================
    nhru = len(data_f)
    L1 = [
        "# Irrigation Pumping File for SWAT-MODFLOW" +
        ", created by QSWATMOD2 plugin " + version + time]
    L2 = [str(nhru) + "       # Number of HRUs that receive irrigation water"]
    L3 = ["# Sub    Row    Col    Layer    HRU_ID"]
    with open(out_file, "w", newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(L1)
        writer.writerow(L2)
        writer.writerow(L3)
        for item in data_f:
            writer.writerow([item[0], item[1], item[2], item[3], item[4]])

    msgBox.setWindowTitle("Created!")
    msgBox.setText(
                    "'swatmf_irrigate.txt' file has been created successfully!"
                    )
    msgBox.exec_()


def modify_wel(self):
    QSWATMOD_path_dict = self.dirs_and_paths()
    wd = QSWATMOD_path_dict['SMfolder']
    # Find the number of wel from irrig_swat
    layer = QgsProject.instance().mapLayersByName("irrig_swat")[0]
    nWel_swat = layer.featureCount()

    # Modify an exsiting Wel file
    version = "version 2.10.1."
    time = datetime.datetime.now().strftime(' - %m/%d/%y %H:%M:%S -')

    if any(inFile.endswith('.wel') for inFile in os.listdir(wd)):
        info = "# Well Package input file, modified by QSWATMOD2 plugin "+version + time + '\n' 
        for filename in glob.glob(wd + "/*.wel"):
            lines = []
            lines.append(info)

            # Get only filename
            fn = os.path.basename(filename)
            msgBox.setWindowTitle("Info!")
            msgBox.setText(
                        fn + ' already exists!\n' + fn + ' and modflow.mfn will be modified\n' +
                        'adding the number of well and its package.')
            msgBox.exec_()
            with open(filename) as infile1:
                data2 = [x.strip().split() for x in infile1 if x.strip() and not x.startswith("#")]
            nWel = int(data2[0][0])
            totWel = nWel + nWel_swat

            with open(filename) as infile2:
                # Get number of well
                data = [x.strip() for x in infile2 if x.strip()]

            count = 1
            for line in data:
                if line.startswith("#"):
                    lines.append(line + '\n')
                elif (count < 3) and (not line.startswith("#")):
                    count += 1
                    a = line.split()
                    a[0] = str(totWel)
                    line = '\t'.join(a)
                    # print(a)
                    lines.append(line + '\n')
                else:
                    lines.append(line + '\n')

            with open(os.path.join(wd, os.path.basename(filename)), 'w') as outfile:
                for line in lines:
                    outfile.write(line)
            break
            msgBox.setWindowTitle("Finished!")
            msgBox.setText('Done!')
            msgBox.exec_()
    else:
        msgBox.setWindowTitle("Info!")
        msgBox.setText(
                    "'modflow.wel' file will be created and added to 'modflow.mfn' file.")
        msgBox.exec_()
        lines = []
        info = "# Well Package input file, created by QSWATMOD2 plugin " + version + time + '\n'
        lines.append(info)
        data = [str(nWel_swat), '0', 'AUX', 'IFACE', 'NAME']
        data2 = ['0', '0']
        line1 = '\t'.join(data)
        line2 = '\t'.join(data2)
        lines.append(line1 + '\n')
        lines.append(line2 + '\n')

        with open(os.path.join(wd, 'modflow.wel'), 'w') as outfile:
            for line in lines:
                outfile.write(line)
        with open(os.path.join(wd, "modflow.mfn"), 'r') as outf:
            data = [int(x.strip().split()[1]) for x in outf if x.strip() and not x.startswith("#")]
        # Assign the unit number to wel package
        unitNwel = max(data) + 1
        with open(os.path.join(wd, "modflow.mfn"), 'a') as outf:
            outf.write('WEL' + '\t' + str(unitNwel) + '\t' + 'modflow.wel\n')
        msgBox.setWindowTitle("Finished!")
        msgBox.setText('Done!')
        msgBox.exec_()


def gw_delay(self):
    QSWATMOD_path_dict = self.dirs_and_paths()

    # Create swatmf_results tree inside 
    root = QgsProject.instance().layerTreeRoot()
    input1 = QgsProject.instance().mapLayersByName("hru (SWAT)")[0]

    # Copy sub shapefile to be under "p from mf"
    name = "gw_delay"
    name_ext = "gw_delay.shp"
    output_dir = QSWATMOD_path_dict['SMshps']

    # Check if there is an exsting mf_head shapefile
    # if not any(lyr.name() == ("conv_runoff") for lyr in QgsProject.instance().mapLayers().values()):
    gw_delay_shapefile = os.path.join(output_dir, name_ext)
    QgsVectorFileWriter.writeAsVectorFormat(
        input1, gw_delay_shapefile,
        "utf-8", input1.crs(), "ESRI Shapefile")
    layer = QgsVectorLayer(gw_delay_shapefile, '{0}'.format("gw_delay"), 'ogr')

    # Put in the group
    # root = QgsProject.instance().layerTreeRoot()
    # conv_runoff = root.findGroup("Pumping from MODFLOW")
    QgsProject.instance().addMapLayer(layer, False)

    sm = root.findGroup("SWAT-MODFLOW")
    sm.insertChildNode(0, QgsLayerTreeLayer(layer))

    input2 = QgsProject.instance().mapLayersByName("gw_delay")[0]
    fields = input2.dataProvider()
    fdname = [fields.fields().indexFromName(field.name()) for field in fields.fields() if not field.name() == 'HRU_ID']
    fields.deleteAttributes(fdname)
    input2.updateFields()
    gwd = QgsField('gw_delay',  QVariant.Int)
    fields.addAttributes([gwd])
    input2.updateFields()
    gwd_idx = fields.fields().indexFromName('gw_delay')

    feats = input2.getFeatures()
    input2.startEditing()

    delay_multi = self.dlg.spinBox_gw_delay_multi.value()
    for feat in feats:
        # attr = feat.attributes() #  this can be used for changing value based on value from other column
        input2.changeAttributeValue(feat.id(), gwd_idx, delay_multi)

    input2.commitChanges()

    msgBox.setWindowTitle("Created!")
    msgBox.setText("'gw_delay.shp' file has been created!")
    msgBox.exec_()
