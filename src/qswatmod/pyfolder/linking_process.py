from builtins import str
import os
import os.path
from PyQt5.QtGui import QIcon
from qgis.PyQt import QtCore, QtGui, QtSql
from qgis.PyQt.QtCore import QVariant, QCoreApplication
import processing
from processing.tools import dataobjects
from qgis.core import (
                    QgsVectorLayer, QgsField, QgsProject, QgsFeatureIterator, QgsVectorFileWriter,
                    QgsFeatureRequest, QgsLayerTreeLayer, QgsExpression, QgsFeature,
                    QgsProcessingFeedback)
import glob
import subprocess
import shutil
from datetime import datetime
import csv
import pandas as pd
from PyQt5.QtWidgets import QMessageBox


def start_time(self, desc):
    time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
    self.dlg.textEdit_sm_link_log.append(time+' -> ' + f"{desc} ... processing")
    self.dlg.label_StepStatus.setText(f"{desc} ... ")
    self.dlg.progressBar_step.setValue(0)
    QCoreApplication.processEvents()

def end_time(self, desc):
    time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
    self.dlg.textEdit_sm_link_log.append(time+' -> ' + f"{desc} ... passed")
    self.dlg.label_StepStatus.setText('Step Status: ')
    self.dlg.progressBar_step.setValue(100)
    QCoreApplication.processEvents()

def get_attribute_to_dataframe(self, layer):
    #List all columns you want to include in the dataframe. I include all with:
    cols = [f.name() for f in layer.fields()] #Or list them manually: ['kommunnamn', 'kkod', ... ]
    #A generator to yield one row at a time
    datagen = ([f[col] for col in cols] for f in layer.getFeatures())
    df = pd.DataFrame.from_records(data=datagen, columns=cols)
    return df

def dissolve_field(self, layername, fieldname, outputname):
    start_time(self, f"Dissolving '{fieldname}'")
    layer = QgsProject.instance().mapLayersByName(f"{layername}")[0]
    # runinng the actual routine: 
    params = {
        'INPUT': layer,
        'FIELD':fieldname,
        'SEPARATE_DISJOINT':False,
        'OUTPUT': f"memory:{outputname}"
    }
    outlayer = processing.run('qgis:dissolve', params)
    outlayer = outlayer['OUTPUT']

    for lyr in list(QgsProject.instance().mapLayers().values()):
        if lyr.name() == (outputname):
            QgsProject.instance().removeMapLayers([lyr.id()])

    # Put in the group  
    root = QgsProject.instance().layerTreeRoot()
    mf_group = root.findGroup("SWAT-MODFLOW")
    QgsProject.instance().addMapLayer(outlayer, False)
    mf_group.insertChildNode(0, QgsLayerTreeLayer(outlayer))
    self.iface.mapCanvas().refreshAllLayers()
    end_time(self, f"Dissolving '{fieldname}'")

def delete_layers(self, layernames):
    for layername in layernames:
        for lyr in list(QgsProject.instance().mapLayers().values()):
            if lyr.name() == (layername):
                QgsProject.instance().removeMapLayers([lyr.id()])
    self.iface.mapCanvas().refreshAllLayers()

def delete_fields(self, layername, character):
    layer = QgsProject.instance().mapLayersByName(layername)[0]
    provider = layer.dataProvider()
    fdname = [
        provider.fields().indexFromName(field.name()) for field in provider.fields()
        if character in field.name()
        ]
    provider.deleteAttributes(fdname)
    layer.updateFields()


def calculate_area(self, input_layer, var_name, out_name):
    start_time(self, f"Calculating '{var_name}' areas")
    layer = QgsProject.instance().mapLayersByName(input_layer)[0]
    provider = layer.dataProvider()
    if provider.fields().indexFromName(var_name) != -1:
        provider.deleteAttributes([provider.fields().indexFromName(var_name)])
        # field = QgsField(var_name, QVariant.Double, 'double', 0, 2)
        # provider.addAttributes([field])
        # layer.updateFields()

    params = {
        'INPUT': layer,
        'FIELD_NAME': var_name,
        'FIELD_TYPE': 0,
        'FIELD_LENGTH': 0,
        'FIELD_PRECISION': 2,
        'FORMULA': '$area',
        'OUTPUT': f"memory:{out_name}"
    }
    outlayer = processing.run("native:fieldcalculator", params)
    outlayer = outlayer['OUTPUT']

    for lyr in list(QgsProject.instance().mapLayers().values()):
        if lyr.name() == (out_name):
            QgsProject.instance().removeMapLayers([lyr.id()])

    # Put in the group  
    root = QgsProject.instance().layerTreeRoot()
    mf_group = root.findGroup("SWAT-MODFLOW")
    QgsProject.instance().addMapLayer(outlayer, False)
    mf_group.insertChildNode(0, QgsLayerTreeLayer(outlayer))
    self.iface.mapCanvas().refreshAllLayers()
    end_time(self, f"Calculating '{var_name}' areas")


def filter_required_fields(self, layer, fields_required):
    layer = QgsProject.instance().mapLayersByName(layer)[0]
    prov = layer.dataProvider()
    field_names = [field.name() for field in prov.fields()]
    fields_filter = [i for i in field_names if i not in fields_required]
    fields_filter = [prov.fields().indexFromName(i) for i in fields_filter]
    prov.deleteAttributes(fields_filter)
    layer.updateFields()


def create_hru_id(self):
    desc = "Creating 'HRU_ID'"
    start_time(self, desc)
    time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
    self.layer = QgsProject.instance().mapLayersByName("hru (SWAT)")[0]
    provider = self.layer.dataProvider()
    if provider.fields().indexFromName("HRU_ID") == -1:
        field = QgsField("HRU_ID", QVariant.Int)
        provider.addAttributes([field])
        self.layer.updateFields()
        field1Id = self.layer.dataProvider().fields().indexFromName( "HRUGIS" )
        attrIdx = self.layer.dataProvider().fields().indexFromName( "HRU_ID" )
        aList = self.layer.getFeatures()

        featureList = sorted(aList, key=lambda f: f[field1Id])
        self.layer.startEditing()
        for i, f in enumerate(featureList):
        #    print (f.id())
            self.layer.changeAttributeValue(f.id(), attrIdx, i+1)
            QCoreApplication.processEvents()
        self.layer.commitChanges()
        QCoreApplication.processEvents()
    else:
        time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
        self.dlg.textEdit_sm_link_log.append(time+' -> ' + "Creating 'HRU_ID' already exists ...")        
    end_time(self, desc)


def calculate_hru_area(self):
    time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
    self.dlg.textEdit_sm_link_log.append(time+' -> ' + "Calculating 'HRU areas' ... processing")
    self.dlg.label_StepStatus.setText("Calculating 'HRU areas' ... ")
    self.dlg.progressBar_step.setValue(0)
    QCoreApplication.processEvents()

    self.layer = QgsProject.instance().mapLayersByName("hru (SWAT)")[0]
    provider = self.layer.dataProvider()
    if provider.fields().indexFromName("hru_area") == -1:
        # field = QgsField("hru_area", QVariant.Int)
        field = QgsField("hru_area", QVariant.Int)
        provider.addAttributes([field])
        self.layer.updateFields()
        tot_feats = self.layer.featureCount()
        count = 0
        feats = self.layer.getFeatures()
        self.layer.startEditing()
        for feat in feats:
            area = feat.geometry().area()
            feat['hru_area'] = round(area)
            self.layer.updateFeature(feat)
            count += 1
            provalue = round(count/tot_feats*100)
            self.dlg.progressBar_step.setValue(provalue)
            QCoreApplication.processEvents()
        self.layer.commitChanges()
        QCoreApplication.processEvents()
    else:
        time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
        self.dlg.textEdit_sm_link_log.append(time+' -> ' + "'hru_area' already exists ...")        
    time = datetime.now().strftime('[%m/%d/%y %H:%M:%S]')
    self.dlg.textEdit_sm_link_log.append(time+' -> ' + "Calculating 'HRU areas' ... passed")
    self.dlg.label_StepStatus.setText('Step Status: ')
    QCoreApplication.processEvents()

def multipart_to_singlepart(self):
    start_time(self, "Disaggregating HRUs")
    layer = QgsProject.instance().mapLayersByName("hru (link)")[0]
    # runinng the actual routine:
    outnam = "dhru (link)"
    params = {
        'INPUT': layer,
        'OUTPUT': f"memory:{outnam}"
    }
    outlayer = processing.run("qgis:multiparttosingleparts", params)
    outlayer = outlayer['OUTPUT']

    # Put in the group
    root = QgsProject.instance().layerTreeRoot()
    sm_group = root.findGroup("SWAT-MODFLOW")
    QgsProject.instance().addMapLayer(outlayer, False)
    sm_group.insertChildNode(1, QgsLayerTreeLayer(outlayer))
    end_time(self, "Disaggregating HRUs")

def create_temp_id(self):
    start_time(self, "Creating 'temporary ID'")
    layer = QgsProject.instance().mapLayersByName("dhru (link)")[0]
    outnam = "dhru (link)"
    params = {
        'INPUT': layer,
        'FIELD_NAME': 'tid',
        'FIELD_TYPE': 0,
        'FIELD_LENGTH': 0,
        'FIELD_PRECISION': 0,
        'FORMULA': '$id',
        'OUTPUT': f"memory:{outnam}"
    }
    outlayer = processing.run("native:fieldcalculator", params)
    outlayer = outlayer['OUTPUT']
    # Put in the group
    for lyr in list(QgsProject.instance().mapLayers().values()):
        if lyr.name() == ("dhru (link)"):
            QgsProject.instance().removeMapLayers([lyr.id()])
    # Put in the group
    root = QgsProject.instance().layerTreeRoot()
    sm_group = root.findGroup("SWAT-MODFLOW")
    QgsProject.instance().addMapLayer(outlayer, False)
    sm_group.insertChildNode(1, QgsLayerTreeLayer(outlayer))
    end_time(self, "Creating 'temporary ID'")
    self.iface.mapCanvas().refreshAllLayers()

def create_dhru_id(self):
    start_time(self, "Creating 'dhru ID'")
    layer = QgsProject.instance().mapLayersByName("dhru (link)")[0]
    data = get_attribute_to_dataframe(self, layer)
    data_sorted = data.sort_values(by=['HRU_ID'])
    data_sorted['dhru_id'] = range(1, len(data_sorted) + 1)
    vl = QgsVectorLayer("None", "tt", "memory") #Adjust this line if you dont want a temp table
    pr = vl.dataProvider()
    vl.startEditing()
    fieldlist = [QgsField(fieldname, QVariant.Double) for fieldname in data_sorted.columns]
    pr.addAttributes(fieldlist)
    vl.updateFields()

    for i in data_sorted.index.to_list():
        fet = QgsFeature()
        newrow = data_sorted[data_sorted.columns].iloc[i].tolist()
        fet.setAttributes(newrow)
        pr.addFeatures([fet])
    vl.commitChanges()
    QgsProject.instance().addMapLayer(vl)
    dhru_table = QgsProject.instance().mapLayersByName("tt")[0]
    outnam = "dhru (link)"
    params = {
        'INPUT': layer.source(),
        'FIELD': 'tid',
        'INPUT_2': dhru_table.source(),
        'FIELD_2': 'tid',
        'FIELDS_TO_COPY': ['dhru_id'],
        'METHOD': 1,
        'DISCARD_NONMATCHING': False,
        'PREFIX': '',
        'OUTPUT': f"memory:{outnam}"
    }
    outlayer = processing.run("native:joinattributestable", params)['OUTPUT']
    # Put in the group
    for lyr in list(QgsProject.instance().mapLayers().values()):
        if lyr.name() == ("dhru (link)"):
            QgsProject.instance().removeMapLayers([lyr.id()])
    # Put in the group
    root = QgsProject.instance().layerTreeRoot()
    sm_group = root.findGroup("SWAT-MODFLOW")
    QgsProject.instance().addMapLayer(outlayer, False)
    sm_group.insertChildNode(1, QgsLayerTreeLayer(outlayer))
    end_time(self, "Creating 'dhru ID'")
    self.iface.mapCanvas().refreshAllLayers()
    
def cvt_vl_to_gpkg(self, layernam, output_file, group="SWAT-MODFLOW"):
    QSWATMOD_path_dict = self.dirs_and_paths()
    output_dir = QSWATMOD_path_dict['SMshps']
    layer = QgsProject.instance().mapLayersByName(layernam)[0]
    layer_gpkg = os.path.normpath(os.path.join(output_dir, output_file))
    layer.selectAll()
    params = {
        'INPUT': layer,
        'OUTPUT': layer_gpkg,
        'OVERWRITE': True,
    }
    processing.run("native:saveselectedfeatures", params)
    layer.removeSelection()
    outlayer = QgsVectorLayer(layer_gpkg, f"{layernam}", 'ogr')     

    # if there is an existing mf_grid shapefile, it will be removed
    for lyr in list(QgsProject.instance().mapLayers().values()):
        if lyr.name() == (layernam):
            QgsProject.instance().removeMapLayers([lyr.id()])
    # Put in the group
    root = QgsProject.instance().layerTreeRoot()
    sm_group = root.findGroup(f"{group}")
    QgsProject.instance().addMapLayer(outlayer, False)
    sm_group.insertChildNode(1, QgsLayerTreeLayer(outlayer))
    self.iface.mapCanvas().refreshAllLayers()


# processing.run(
#     "native:savefeatures", 
#     {'INPUT':'memory://MultiPolygon?crs=EPSG:5070&field=HRU_ID:integer(0,0)&field=hru_area:double(0,2)&field=tid:double(0,0)&field=dhru_id:double(0,0)&field=dhru_area:double(0,2)&field=fid:long(0,0)&field=grid_id:integer(0,0)&field=row:integer(0,0)&field=col:integer(0,0)&field=top_elev:double(0,0)&field=ol_area:double(0,2)&uid={28f8f565-083f-4a9e-99fe-579a7743e332}','OUTPUT':'D:/Projects/temp_qswatmod/tttt.gpkg',
#      'LAYER_NAME':'testing','DATASOURCE_OPTIONS':'','LAYER_OPTIONS':'','ACTION_ON_EXISTING_FILE':0})


def hru_dhru(self):
    start_time(self, "Intersecting DHRUs by SUBs")
    input1 = QgsProject.instance().mapLayersByName("dhru (link)")[0]
    input2 = QgsProject.instance().mapLayersByName("sub (link)")[0]    

    # runinng the actual routine:
    outnam = "hru_dhru (SWAT-MODFLOW)"
    params = {
        'INPUT': input1,
        'OVERLAY': input2,
        'OUTPUT': f"memory:{outnam}"
    }
    outlayer = processing.run("native:intersection", params)
    outlayer = outlayer['OUTPUT']
    for lyr in list(QgsProject.instance().mapLayers().values()):
        if lyr.name() == ("hru_dhru (SWAT-MODFLOW)"):
            QgsProject.instance().removeMapLayers([lyr.id()])

    # Put in the group
    root = QgsProject.instance().layerTreeRoot()
    sm_group = root.findGroup("SWAT-MODFLOW")   
    QgsProject.instance().addMapLayer(outlayer, False)
    sm_group.insertChildNode(1, QgsLayerTreeLayer(outlayer))
    end_time(self, "Intersecting DHRUs by SUBs")


# Create a field for filtering rows on area
def create_hru_dhru_filter(self):
    dissolve_field(self, "hru_dhru (SWAT-MODFLOW)", "dhru_id", "hru_dhru (SWAT-MODFLOW)")
    calculate_area(self, "hru_dhru (SWAT-MODFLOW)", "area_f", "hru_dhru (SWAT-MODFLOW)")
    layer = QgsProject.instance().mapLayersByName("hru_dhru (SWAT-MODFLOW)")[0]
    layer.startEditing()
    params = {
        'INPUT': layer,
        'FIELD':'area_f','OPERATOR':4,'VALUE':'9','METHOD':0
    }
    processing.run("qgis:selectbyattribute", params)
    layer.deleteSelectedFeatures()
    layer.commitChanges()




def dhru_grid(self):
    start_time(self, "Intersecting DHRUs by GRIDs")
    input1 = QgsProject.instance().mapLayersByName("dhru (link)")[0]
    input2 = QgsProject.instance().mapLayersByName("mf_grid (MODFLOW)")[0]
    outnam = "dhru_grid (SWAT-MODFLOW)"
    params = {
        'INPUT': input1,
        'OVERLAY': input2,
        'OUTPUT': f"memory:{outnam}"
    }
    outlayer = processing.run("native:intersection", params)
    outlayer = outlayer['OUTPUT']
    for lyr in list(QgsProject.instance().mapLayers().values()):
        if lyr.name() == ("dhru_grid (SWAT-MODFLOW)"):
            QgsProject.instance().removeMapLayers([lyr.id()])
    # Put in the group
    root = QgsProject.instance().layerTreeRoot()
    sm_group = root.findGroup("SWAT-MODFLOW")
    QgsProject.instance().addMapLayer(outlayer, False)
    sm_group.insertChildNode(1, QgsLayerTreeLayer(outlayer))
    end_time(self, "Intersecting DHRUs by GRIDs")


def create_dhru_grid_filter(self):
    start_time(self, "Calculating overlapping sizes")
    calculate_area(self, "dhru_grid (SWAT-MODFLOW)", "ol_area", "dhru_grid (SWAT-MODFLOW)")
    layer = QgsProject.instance().mapLayersByName("dhru_grid (SWAT-MODFLOW)")[0]
    layer.startEditing()
    params = {
        'INPUT': layer,
        'FIELD':'ol_area','OPERATOR':4,'VALUE':'30','METHOD':0
    }
    processing.run("qgis:selectbyattribute", params)
    layer.deleteSelectedFeatures()
    layer.commitChanges()
    end_time(self, "Calculating overlapping sizes")

# deleting existing river_grid
def deleting_river_grid(self):
    for lyr in list(QgsProject.instance().mapLayers().values()):
        if lyr.name() == ("river_grid (SWAT-MODFLOW)"):
            QgsProject.instance().removeMapLayers([lyr.id()])

# Used for both SWAT and SWAT+

# def mf_riv2_layer(self):
#     QSWATMOD_path_dict = self.dirs_and_paths()
#     output_dir = QSWATMOD_path_dict['org_shps']
#     name_ext_v = 'mf_riv2.gpkg'
#     output_file_v = os.path.normpath(os.path.join(output_dir, name_ext_v))
#     layer = QgsVectorLayer(output_file_v, '{0} ({1})'.format("mf_riv2","MODFLOW"), 'ogr')
#     return layer   


def river_grid(self): #step 1
    QSWATMOD_path_dict = self.dirs_and_paths()

    # Initiate rive_grid shapefile
    # if there is an existing river_grid shapefile, it will be removed
    for self.lyr in list(QgsProject.instance().mapLayers().values()):
        if self.lyr.name() == ("river_grid (SWAT-MODFLOW)"):
            QgsProject.instance().removeMapLayers([self.lyr.id()])
    if self.dlg.radioButton_mf_riv1.isChecked():
        input1 = QgsProject.instance().mapLayersByName("riv (link)")[0]
        input2 = QgsProject.instance().mapLayersByName("mf_riv1 (MODFLOW)")[0]
    elif self.dlg.radioButton_mf_riv2.isChecked():
        input1 = QgsProject.instance().mapLayersByName("riv (link)")[0]
        input2 = QgsProject.instance().mapLayersByName("mf_riv2 (MODFLOW)")[0]
    elif self.dlg.radioButton_mf_riv3.isChecked():
        input1 = QgsProject.instance().mapLayersByName("riv (link)")[0]
        input2 = QgsProject.instance().mapLayersByName("mf_riv3 (MODFLOW)")[0]
    else:
        self.main_messageBox("Hello?", "Please, select one of the river options!")

    name = "river_grid"
    name_ext = "river_grid.gpkg"
    output_dir = QSWATMOD_path_dict['SMshps']
    output_file = os.path.normpath(os.path.join(output_dir, name_ext))

    # intersection syntax have been changed in QGIS 3.40
    processing.run("native:intersection",
                {'INPUT': input1,
                 'OVERLAY': input2,
                 'INPUT_FIELDS':[],
                 'OVERLAY_FIELDS':[],
                 'OVERLAY_FIELDS_PREFIX':'',
                 'OUTPUT': output_file,
                 'OVERWRITE': True,
                 'GRID_SIZE':None})


    # runinng the actual routine:
    # params = { 
    #     'INPUT' : input1,
    #     'OVERLAY' : input2, 
    #     'OUTPUT' : output_file,
    #     'OVERWRITE': True
    # }
    # processing.run('native:intersection', params)
    
    # defining the outputfile to be loaded into the canvas        
    # river_grid_shapefile = os.path.join(output_dir, name_ext)
    # self.layer = QgsVectorLayer(river_grid_shapefile, '{0} ({1})'.format("river_grid","SWAT-MODFLOW"), 'ogr')    
    # # Put in the group
    # root = QgsProject.instance().layerTreeRoot()
    # sm_group = root.findGroup("SWAT-MODFLOW")   
    # QgsProject.instance().addMapLayer(self.layer, False)
    # sm_group.insertChildNode(1, QgsLayerTreeLayer(self.layer))

# 
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


# SWAT+
# Create a field for filtering rows on area
def create_river_grid_filter(self):
    self.layer = self.river_grid_layer()
    provider = self.layer.dataProvider()
    field = QgsField("ol_length", QVariant.Int)
    #field = QgsField("ol_area", QVariant.Int)
    provider.addAttributes([field])
    self.layer.updateFields()

    feats = self.layer.getFeatures()
    self.layer.startEditing()

    for feat in feats:
        length = feat.geometry().length()
        #score = scores[i]
        feat['ol_length'] = length
        self.layer.updateFeature(feat)
    self.layer.commitChanges()


def delete_river_grid_with_threshold(self):
    self.layer = self.river_grid_layer()
    provider = self.layer.dataProvider()
    request =  QgsFeatureRequest().setFilterExpression('"rgrid_len" < 0.5')
    request.setSubsetOfAttributes([])
    request.setFlags(QgsFeatureRequest.NoGeometry)
    self.layer.startEditing()
    for f in self.layer.getFeatures(request):
        self.layer.deleteFeature(f.id())
    self.layer.commitChanges()


def rgrid_len(self):
    self.layer = self.river_grid_layer()
    provider = self.layer.dataProvider()
    field = QgsField("rgrid_len", QVariant.Int)
    provider.addAttributes([field])
    self.layer.updateFields()
    
    feats = self.layer.getFeatures()
    self.layer.startEditing()

    for feat in feats:
        length = feat.geometry().length()
        #score = scores[i]
        feat['rgrid_len'] = length
        self.layer.updateFeature(feat)
    self.layer.commitChanges()


# SWAT+
def river_sub(self):
    QSWATMOD_path_dict = self.dirs_and_paths()
    input1 = self.river_grid_layer()
    input2 = QgsProject.instance().mapLayersByName("sub (SWAT)")[0]
    name = "river_sub_union"
    name_ext = "river_sub_union.shp"
    output_dir = QSWATMOD_path_dict['SMshps']
    output_file = os.path.normpath(os.path.join(output_dir, name_ext))

    processing.run('qgis:union', input1, input2, output_file)

    # defining the outputfile to be loaded into the canvas        
    river_sub_union_shapefile = os.path.join(output_dir, name_ext)
    layer = QgsVectorLayer(river_sub_union_shapefile, '{0} ({1})'.format("river_sub","SWAT-MODFLOW"), 'ogr')
    layer = QgsProject.instance().addMapLayer(layer)   

# SWAT+
def river_sub_delete_NULL(self):
    layer = QgsProject.instance().mapLayersByName("river_sub (SWAT-MODFLOW)")[0]
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

# SWAT+
def _create_river_sub_filter(self):
    self.layer = QgsProject.instance().mapLayersByName("river_sub (SWAT-MODFLOW)")[0]
    provider = self.layer.dataProvider()
    field = QgsField("ol_length", QVariant.Int)
    #field = QgsField("ol_area", QVariant.Int)
    provider.addAttributes([field])
    self.layer.updateFields()

    feats = self.layer.getFeatures()
    self.layer.startEditing()

    for feat in feats:
        length = feat.geometry().length()
        #score = scores[i]
        feat['ol_length'] = length
        self.layer.updateFeature(feat)
    self.layer.commitChanges()

def _delete_river_sub_with_threshold(self):
    self.layer = QgsProject.instance().mapLayersByName("river_sub (SWAT-MODFLOW)")[0]
    provider = self.layer.dataProvider()
    request =  QgsFeatureRequest().setFilterExpression('"ol_length" < 1.0')
    request.setSubsetOfAttributes([])
    request.setFlags(QgsFeatureRequest.NoGeometry)
    self.layer.startEditing()
    for f in self.layer.getFeatures(request):
        self.layer.deleteFeature(f.id())
    self.layer.commitChanges()


def _rgrid_len(self):

    self.layer = QgsProject.instance().mapLayersByName("river_sub (SWAT-MODFLOW)")[0]
    provider = self.layer.dataProvider()
    from qgis.PyQt.QtCore import QVariant
    from qgis.core import QgsField, QgsExpression, QgsFeature

    field = QgsField("rgrid_len", QVariant.Int)
    provider.addAttributes([field])
    self.layer.updateFields()
    
    feats = self.layer.getFeatures()
    self.layer.startEditing()

    for feat in feats:
       length = feat.geometry().length()
       #score = scores[i]
       feat['rgrid_len'] = length
       self.layer.updateFeature(feat)
    self.layer.commitChanges()

""" 
/********************************************************************************************
 *                                                                                          *
 *                              Export GIS Table for original SWAT                          *
 *                                                                                          *
 *******************************************************************************************/
"""

def export_hru_dhru(self):
    QSWATMOD_path_dict = self.dirs_and_paths()
    #sort by hru_id and then by dhru_id and save down 
    #read in the hru_dhru shapefile
    layer = QgsProject.instance().mapLayersByName("hru_dhru (SWAT-MODFLOW)")[0]

    # Get the index numbers of the fields
    dhru_id_index = layer.dataProvider().fields().indexFromName("dhru_id")
    dhru_area_index = layer.dataProvider().fields().indexFromName("area_f")
    hru_id_index = layer.dataProvider().fields().indexFromName("HRU_ID")
    hru_area_index = layer.dataProvider().fields().indexFromName("hru_area")
    subbasin_index = layer.dataProvider().fields().indexFromName("Subbasin")

    # transfer the shapefile layer to a python list
    l = []
    for i in layer.getFeatures():
        l.append(i.attributes())

    # then sort by columns
    import operator
    l_sorted = sorted(l, key=operator.itemgetter(hru_id_index, dhru_id_index))
    dhru_number = len(l_sorted) # number of lines

    # Get hru number
    hru =[]
    # slice the column of interest in order to count the number of hrus
    for h in l:
        hru.append(h[hru_id_index])

    # Wow nice!!!
    hru_unique = []        
    for h in hru:
        if h not in hru_unique:
            hru_unique.append(h)
    hru_number = max(hru_unique)

    #-----------------------------------------------------------------------#
    # exporting the file 
    name = "hru_dhru"
    output_dir = QSWATMOD_path_dict['Table']
    output_file = os.path.normpath(os.path.join(output_dir, name))

    with open(output_file, "w", newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        first_row = [str(int(dhru_number))]  # prints the dhru number to the first row
        second_row = [str(int(hru_number))]  # prints the hru number to the second row
        third_row = ["dhru_id dhru_area hru_id subbasin hru_area"]
        writer.writerow(first_row)
        writer.writerow(second_row)
        writer.writerow(third_row)
        
        for item in l_sorted:
        
        # Write item to outcsv. the order represents the output order
            writer.writerow(
                [
                f"{int(item[dhru_id_index]):>10d}", 
                f"{int(item[dhru_area_index]):>14d}",
                f"{int(item[hru_id_index]):>7d}",
                f"{int(item[subbasin_index]):>7d}",
                f"{int(item[hru_area_index]):>14d}"
                ])

def export_dhru_grid(self):
    QSWATMOD_path_dict = self.dirs_and_paths()
    #read in the dhru shapefile
    layer = QgsProject.instance().mapLayersByName("dhru_grid (SWAT-MODFLOW)")[0]
    mflayer = QgsProject.instance().mapLayersByName("mf_grid (MODFLOW)")[0]

    # Get the index numbers of the fields
    dhru_id_index = layer.dataProvider().fields().indexFromName("dhru_id")
    dhru_area_index = layer.dataProvider().fields().indexFromName("dhru_area")
    grid_id_index = layer.dataProvider().fields().indexFromName("grid_id")
    grid_area_index = layer.dataProvider().fields().indexFromName("grid_area")
    overlap_area_index = layer.dataProvider().fields().indexFromName("ol_area")

    # transfer the shapefile layer to a python list
    l = []
    for i in layer.getFeatures():
        l.append(i.attributes())
    # then sort by columns
    import operator
    l_sorted = sorted(l, key=operator.itemgetter(grid_id_index, dhru_id_index))

    # BUG: flopy generates wrong number of rows and cols in the dis file

    # for filename in glob.glob(str(QSWATMOD_path_dict['SMfolder'])+"/*.dis"):
    #     with open(filename, "r") as f:
    #         data = []
    #         for line in f.readlines():
    #             if not line.startswith("#"):
    #                 data.append(line.replace('\n', '').split())
    #     nrow = int(data[0][1])
    #     ncol = int(data[0][2])
    #     delr = float(data[2][1]) # is the cell width along rows (x spacing)
    #     delc = float(data[3][1]) # is the cell width along columns (y spacing).
    number_of_grids = mflayer.featureCount()

    info_number = len(l_sorted) # number of lines with information
    #-----------------------------------------------------------------------#
    # exporting the file 
    name = "dhru_grid"
    output_dir = QSWATMOD_path_dict['Table'] 
    output_file = os.path.normpath(os.path.join(output_dir, name))

    with open(output_file, "w", newline='') as f:
        writer = csv.writer(f, delimiter = '\t')
        first_row = [str(int(info_number))] # prints the dhru number to the file
        second_row = [str(int(number_of_grids))] # prints the total number of grid cells
        third_row = ["grid_id grid_area dhru_id overlap_area dhru_area"]
        writer.writerow(first_row)
        writer.writerow(second_row)
        writer.writerow(third_row)

        for item in l_sorted:
        #Write item to outcsv. the order represents the output order
            writer.writerow([
                f"{int(item[grid_id_index]):>10d}",
                f"{int(item[grid_area_index]):>14d}",
                f"{int(item[dhru_id_index]):>10d}",
                f"{int(item[overlap_area_index]):>14d}",
                f"{int(item[dhru_area_index]):>14d}"
                ])


def export_grid_dhru(self):
    QSWATMOD_path_dict = self.dirs_and_paths()
    #read in the dhru shapefile
    layer = QgsProject.instance().mapLayersByName("dhru_grid (SWAT-MODFLOW)")[0]
    layer2 = QgsProject.instance().mapLayersByName("hru_dhru (SWAT-MODFLOW)")[0]

    # Get max number of dhru id
    dhrus2 = [f.attribute("dhru_id") for f in layer2.getFeatures()]

    # Get the index numbers of the fields
    dhru_id_index = layer.dataProvider().fields().indexFromName("dhru_id")
    dhru_area_index = layer.dataProvider().fields().indexFromName("dhru_area")
    grid_id_index = layer.dataProvider().fields().indexFromName("grid_id")
    grid_area_index = layer.dataProvider().fields().indexFromName("grid_area")
    overlap_area_index = layer.dataProvider().fields().indexFromName("ol_area")

    # transfer the shapefile layer to a python list
    l = []
    for i in layer.getFeatures():
        l.append(i.attributes())
    # then sort by columns
    import operator
    l_sorted = sorted(l, key=operator.itemgetter(dhru_id_index, grid_id_index))

    #l.sort(key=itemgetter(6))
    #add a counter as index for the dhru id
    for filename in glob.glob(str(QSWATMOD_path_dict['SMfolder'])+"/*.dis"):
        with open(filename, "r") as f:
            data = []
            for line in f.readlines():
                if not line.startswith("#"):
                    data.append(line.replace('\n', '').split())
        nrow = int(data[0][1])
        ncol = int(data[0][2])
        delr = float(data[2][1]) # is the cell width along rows (x spacing)
        delc = float(data[3][1]) # is the cell width along columns (y spacing).

    cell_size = delr * delc
    number_of_grids = nrow * ncol

    for i in l_sorted:
        i.append(str(int(cell_size))) # area of the grid
        
    # # It
    # dhru_id =[]
    # # slice the column of interest in order to count the number of grid cells
    # for h in l_sorted:
    #   dhru_id.append(h[dhru_id_index])

    # dhru_id_unique = []    
        
    # for h in dhru_id:
    #   if h not in dhru_id_unique:
    #     dhru_id_unique.append(h)


    # It seems we need just total number of DHRUs not the one used in study area
    # dhru_number = len(dhru_id_unique) # number of dhrus
    dhru_number = max(dhrus2) # number of dhrus
    info_number = len(l_sorted) # number of lines with information
    #-----------------------------------------------------------------------#
    # exporting the file 
    name = "grid_dhru"
    output_dir = QSWATMOD_path_dict['Table'] 
    output_file = os.path.normpath(os.path.join(output_dir, name))

    with open(output_file, "w", newline='') as f:
        writer = csv.writer(f, delimiter = '\t')
        first_row = [str(int(info_number))] # prints the dnumber of lines with information
        second_row = [str(int(dhru_number))] # prints the total number of dhru
        third_row = [str(nrow)] # prints the row number to the file
        fourth_row = [str(ncol)] # prints the column number to the file     
        fifth_row = ["grid_id grid_area dhru_id overlap_area dhru_area"]
        writer.writerow(first_row)
        writer.writerow(second_row)
        writer.writerow(third_row)
        writer.writerow(fourth_row)
        writer.writerow(fifth_row)

        for item in l_sorted:
        #Write item to outcsv. the order represents the output order
            writer.writerow([
                f"{int(item[grid_id_index]):>10d}",
                f"{int(item[grid_area_index]):>14d}",
                f"{int(item[dhru_id_index]):>10d}",
                f"{int(item[overlap_area_index]):>14d}",
                f"{int(item[dhru_area_index]):>14d}"
                ])


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
            writer.writerow([
                f"{int(item[grid_id_index]):>10d}",
                f"{int(item[subbasin_index]):>7d}",
                f"{int(item[ol_length_index]):>10d}"
                ])

def run_CreateSWATMF(self):
    QSWATMOD_path_dict = self.dirs_and_paths()
    output_dir = QSWATMOD_path_dict['Table']
    #Out_folder_temp = self.dlg.lineEdit_output_folder.text()
    #swatmf = os.path.normpath(output_dir + "/" + "SWATMF_files")
    name = "CreateSWATMF.exe"
    exe_file = os.path.normpath(os.path.join(output_dir, name))
    #os.startfile(File_Physical)    
    p = subprocess.Popen(exe_file , cwd = output_dir) # cwd -> current working directory    
    p.wait()

def copylinkagefiles(self):
    QSWATMOD_path_dict = self.dirs_and_paths()
    source_dir = QSWATMOD_path_dict['Table']
    dest_dir = QSWATMOD_path_dict['SMfolder']
    for filename in glob.glob(os.path.join(source_dir, '*.txt')):
        shutil.copy(filename, dest_dir)




'''
grid_id = []
for feat in features:
    attrs = feat.attributes()
    grid_id.append(attrs[grid_id_index])

info_number = len(l) # Number of observation cells



# ------------ Export Data to file -------------- #
name = "modflow.obs"
output_dir = SMfolder
output_file = os.path.normpath(os.path.join(output_dir, name)
with open(output_file, "w", newline='') as f:
    writer = csv.writer(f, delimiter = '\t')
    first_row = ["test"]
    second_row = [str(info_number)]
    for item in grid_id:
        writer.writerow([item])
'''

    
#*******************************************************************************************                                                                                        *
#                                                                                           *
#                               Export GIS Table for SWAT+ MODFLOW
#                          
#*******************************************************************************************/


def _export_hru_dhru(self): 
    #sort by hru_id and then by dhru_id and save down 
    #read in the hru_dhru shapefile
    layer = QgsProject.instance().mapLayersByName("hru_dhru (SWAT-MODFLOW)")[0]
    
    # transfer the shapefile layer to a python list
    l = []
    for i in layer.getFeatures():
        l.append(i.attributes())
    
    # then sort by columns
    import operator
    l_sorted = sorted(l, key=operator.itemgetter(2, 0))
    dhru_number = len(l_sorted) # number of lines


    # Get hru number
    hru =[]
    # slice the column of interest in order to count the number of hrus
    for h in l:
        hru.append(h[0])
 
    # Wow nice!!!
    hru_unique = []    
        
    for h in hru:
        if h not in hru_unique:
          hru_unique.append(h)
    hru_number =  max(hru_unique)


#-----------------------------------------------------------------------#
    # exporting the file 
    name = "hru_dhru"
    output_dir = QSWATMOD_path_dict['Table']
    output_file = os.path.normpath(os.path.join(output_dir, name))

    with open(output_file, "w", newline='') as f:
        writer = csv.writer(f, delimiter = '\t')
        first_row = [str(dhru_number)] # prints the dhru number to the first row
        second_row = [str(hru_number)] # prints the hru number to the second row
        
        third_row = ["dhru_id dhru_area hru_id subbasin hru_area"]
        
        writer.writerow(first_row)
        writer.writerow(second_row)
        writer.writerow(third_row)
        
        for item in l_sorted:
        
        #Write item to outcsv. the order represents the output order
            writer.writerow([item[2], item[3], item[0], item[4], item[1]])


def _export_dhru_grid(self):
    #read in the dhru shapefile
    layer = QgsProject.instance().mapLayersByName("dhru_grid (SWAT-MODFLOW)")[0]

    # transfer the shapefile layer to a python list
    l = []
    for i in layer.getFeatures():
        l.append(i.attributes())
    # then sort by columns
    import operator
    l_sorted = sorted(l, key=operator.itemgetter(9, 2))
    
    #l.sort(key=itemgetter(6))
    #add a counter as index for the dhru id
    for filename in glob.glob(str(QSWATMOD_path_dict['SMfolder'])+"/*.dis"):
        with open(filename, "r") as f:
            data = []
            for line in f.readlines():
                if not line.startswith("#"):
                    data.append(line.replace('\n', '').split())
        nrow = int(data[0][1])
        ncol = int(data[0][2])
        delr = float(data[2][1]) # is the cell width along rows (x spacing)
        delc = float(data[3][1]) # is the cell width along columns (y spacing).

    cell_size = delr * delc
    number_of_grids = nrow * ncol

    for i in l_sorted:     
        i.append(str(int(cell_size))) # area of the grid
        
    ''' I don't know what this is for
    gridcell =[]
    # slice the column of interest in order to count the number of grid cells
    for h in l_sorted:
        gridcell.append(h[6])
  
    gridcell_unique = []    
        
    for h in gridcell:
        if h not in gridcell_unique:
          gridcell_unique.append(h)
    
    gridcell_number = len(gridcell_unique) # number of hrus
    '''

    info_number = len(l_sorted) # number of lines with information
    #-----------------------------------------------------------------------#
    # exporting the file 
    name = "dhru_grid"
    output_dir = QSWATMOD_path_dict['Table'] 
    output_file = os.path.normpath(os.path.join(output_dir, name))

    with open(output_file, "w", newline='') as f:
        writer = csv.writer(f, delimiter = '\t')
        first_row = [str(info_number)] # prints the dhru number to the file
        second_row = [str(number_of_grids)] # prints the total number of grid cells
        third_row = ["grid_id grid_area dhru_id overlap_area dhru_area"]
        writer.writerow(first_row)
        writer.writerow(second_row)
        writer.writerow(third_row)

        for item in l_sorted:
        #Write item to outcsv. the order represents the output order
            writer.writerow([item[9], item[11], item[2], item[10], item[3]])



def _export_grid_dhru(self):    
    #read in the dhru shapefile
    layer = QgsProject.instance().mapLayersByName("dhru_grid (SWAT-MODFLOW)")[0]

    # transfer the shapefile layer to a python list
    l = []
    for i in layer.getFeatures():
        l.append(i.attributes())
    # then sort by columns
    import operator
    l_sorted = sorted(l, key=operator.itemgetter(2, 9))
    
    #l.sort(key=itemgetter(6))
    #add a counter as index for the dhru id
    for filename in glob.glob(str(QSWATMOD_path_dict['SMfolder'])+"/*.dis"):
        with open(filename, "r") as f:
            data = []
            for line in f.readlines():
                if not line.startswith("#"):
                    data.append(line.replace('\n', '').split())
        nrow = int(data[0][1])
        ncol = int(data[0][2])
        delr = float(data[2][1]) # is the cell width along rows (x spacing)
        delc = float(data[3][1]) # is the cell width along columns (y spacing).

    cell_size = delr * delc
    number_of_grids = nrow * ncol

    for i in l_sorted:     
        i.append(str(int(cell_size))) # area of the grid
        

    dhru_id =[]
    # slice the column of interest in order to count the number of grid cells
    for h in l_sorted:
        dhru_id.append(h[2])
  
    dhru_id_unique = []    
        
    for h in dhru_id:
        if h not in dhru_id_unique:
          dhru_id_unique.append(h)
    
    dhru_number = len(dhru_id_unique) # number of dhrus
    info_number = len(l_sorted) # number of lines with information
    #-----------------------------------------------------------------------#
    # exporting the file 
    name = "grid_dhru"
    output_dir = QSWATMOD_path_dict['Table'] 
    output_file = os.path.normpath(os.path.join(output_dir, name))

    with open(output_file, "w", newline='') as f:
        writer = csv.writer(f, delimiter = '\t')
        first_row = [str(info_number)] # prints the dnumber of lines with information
        second_row = [str(dhru_number)] # prints the total number of dhru
        third_row = [str(nrow)] # prints the row number to the file
        fourth_row = [str(ncol)] # prints the column number to the file     
        fifth_row = ["grid_id grid_area dhru_id overlap_area dhru_area"]
        writer.writerow(first_row)
        writer.writerow(second_row)
        writer.writerow(third_row)
        writer.writerow(fourth_row)
        writer.writerow(fifth_row)

        for item in l_sorted:
        #Write item to outcsv. the order represents the output order
            writer.writerow([item[9], item[11], item[2], item[10], item[3]])


def _export_rgrid_len(self): 

    """
    sort by dhru_id and then by grid and save down 
    """
    #read in the dhru shapefile
    layer = QgsProject.instance().mapLayersByName("river_sub (SWAT-MODFLOW)")[0]
    
    # transfer the shapefile layer to a python list
    l = []
    for i in layer.getFeatures():
        l.append(i.attributes())
    
    # then sort by columns
    import operator
    l_sorted = sorted(l, key=operator.itemgetter(22))
    
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
        
        #Write item to outcsv. the order represents the output order
            writer.writerow([item[22], item[23], item[25]])



'''
grid_id = []
for feat in features:
    attrs = feat.attributes()
    grid_id.append(attrs[grid_id_index])

info_number = len(l) # Number of observation cells



# ------------ Export Data to file -------------- #
name = "modflow.obs"
output_dir = QSWATMOD_path_dict['SMfolder']
output_file = os.path.normpath(os.path.join(output_dir, name_ext))
with open(output_file, "w", newline='') as f:
    writer = csv.writer(f, delimiter = '\t')
    first_row = ["test"]
    second_row = [str(info_number)]
    for item in grid_id:
        writer.writerow([item])
'''


def convert_r_v(self):
    input1 = QgsProject.instance().mapLayersByName("HRU_swat")[0]
    fieldName = "hru_id"
            
    name1 = "hru_S"
    name_ext1 = "hru_S.shp"
    output_dir = QSWATMOD_path_dict['SMshps']
    output_file1 = os.path.normpath(os.path.join(output_dir, name_ext1))

    # runinng the actual routine: 
    processing.run('gdalogr:polygonize', input1, fieldName, output_file1)

    # defining the outputfile to be loaded into the canvas        
    hru_shapefile = os.path.join(output_dir, name_ext1)
    layer = QgsVectorLayer(hru_shapefile, '{0} ({1})'.format("hru","--"), 'ogr')
    layer = QgsProject.instance().addMapLayer(layer)

def dissolve_hru(self):
    import ntpath
    import posixpath

    input2 = QgsProject.instance().mapLayersByName("hru (--)")[0]
    fieldName = "hru_id"
            
    name2 = "hru_SM"
    name_ext2 = "hru_SM.shp"
    output_dir = QSWATMOD_path_dict['SMshps']
    output_file2 = os.path.normpath(os.path.join(output_dir, name_ext2))

    # runinng the actual routine: 

    processing.run('qgis:dissolve', input2,False, fieldName, output_file2)
    # defining the outputfile to be loaded into the canvas        
    hru_shapefile = os.path.join(output_dir, name_ext2)
    layer = QgsVectorLayer(hru_shapefile, '{0} ({1})'.format("hru","SWAT"), 'ogr')
    layer = QgsProject.instance().addMapLayer(layer)

    if os.name == 'nt':
        hru_shp = ntpath.join(output_dir, name2 + ".shp")
    else:
        hru_shp = posixpath.join(output_dir, name2 + ".shp")
    self.dlg.lineEdit_hru_rasterfile.setText(hru_shp)

def create_rt3d_grid(self):
    QSWATMOD_path_dict = self.dirs_and_paths()
    # Create apexmf_results tree inside 
    root = QgsProject.instance().layerTreeRoot()
    if root.findGroup("RT3D"):
        rt3d_inputs = root.findGroup("RT3D")
    else:
        rt3d_inputs = root.insertGroup(0, "RT3D")
    input1 = QgsProject.instance().mapLayersByName("mf_grid (MODFLOW)")[0]
    name = 'rt3d_grid'
    name_ext = 'rt3d_grid.shp'
    output_dir = QSWATMOD_path_dict['SMshps']
    if not any(lyr.name() == ('rt3d_grid (RT3D)') for lyr in list(QgsProject.instance().mapLayers().values())):
        mf_hd_shapfile = os.path.join(output_dir, name_ext)
        QgsVectorFileWriter.writeAsVectorFormat(
            input1, mf_hd_shapfile,
            "utf-8", input1.crs(), "ESRI Shapefile")
        layer = QgsVectorLayer(mf_hd_shapfile, '{0} ({1})'.format(name, "RT3D"), 'ogr')
        # Put in the group
        root = QgsProject.instance().layerTreeRoot()
        rt3d_inputs = root.findGroup("RT3D")   
        QgsProject.instance().addMapLayer(layer, False)
        rt3d_inputs.insertChildNode(0, QgsLayerTreeLayer(layer))
        self.main_messageBox("Created!", "'rt3d_grid.shp' file has been created in 'RT3D' group!")
