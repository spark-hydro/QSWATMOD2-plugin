# -*- coding: utf-8 -*-
"""
----------------------------------------------------------------------------
-----------------------databae features-------------------------------------
----------------------------------------------------------------------------
Functions relating connection, update, deletes and other changes of the 
SQLite database
"""


import os
import os.path
import processing
from qgis.core import (
					QgsVectorLayer, QgsField,
					QgsFeatureIterator, QgsVectorFileWriter,
					QgsProject, QgsLayerTreeLayer)
import glob
import posixpath
import ntpath
import shutil

from qgis.PyQt.QtCore import QVariant
from qgis.PyQt import QtCore, QtGui, QtSql
from qgis.PyQt.QtSql import QSqlDatabase, QSqlQuery
from PyQt5.QtCore import QFileInfo
from PyQt5.QtWidgets import QAction, QDialog, QFormLayout, QMessageBox

def DB_CreateConnection(self):
	
	global db
	db = QtSql.QSqlDatabase.addDatabase('QSQLITE')
	proj = QgsProject.instance()
	db_path = QgsProject.instance().readPath("./")
	db_folder = QFileInfo(proj.fileName()).baseName()	   
	db_subfolder = os.path.normpath(db_path + "/" + db_folder +  "/DB")
	db_file = os.path.join(db_subfolder, "DB_SM.db")
	db.setDatabaseName(db_file)
	# self.dlg.DB_Project_Database.setText(db_file)
	
	db.setHostName("localhost")
	db.setPort(5432)

	#db.setUserName("root")
	db.open()
	if db.open():
		msgBox = QMessageBox()
		msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
		msgBox.setWindowTitle("Ready!")
		msgBox.setText("Connected to Database")
		msgBox.exec_()
		self.dlg.raise_() # Pop the dialog after execution
		query = QtSql.QSqlQuery(db)
		#Th Keep track of the references in the scenarios the foreign key statement is activated:
		#https://pythonschool.net/databases/referential-integrity/
		query.exec_("PRAGMA foreign_keys = ON")
		self.dlg.groupBox_SWAT.setEnabled(True)
	else:
		QMessageBox.critical(None, "Database Error",
			db.lastError().text()) 
		return False
	

def db_variable(self):

	db_connection = db
	return db_connection
