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

import os
import os.path
from qgis.PyQt import QtGui, uic

# import numpy as np
import distutils.dir_util
from QSWATMOD2.QSWATMOD2 import *
from PyQt5.QtWidgets import QDialog

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'ui/helpdialog.ui'))

class showhelpdialog(QDialog, FORM_CLASS):
	def __init__(self, iface):
		QDialog.__init__(self)
		self.iface = iface
		self.setupUi(self)

		#------------------------------------------------------------------------------------------------
		# self.pushButton_next_page.clicked.connect(lambda : self.stackedWidget.setCurrentIndex(0))
		self.pushButton_next_page.clicked.connect(self.help_next_page)
		self.pushButton_back_page.clicked.connect(self.help_back_page)	
	# 	self.ui.wgtbtnB.clicked.connect(lambda : self.stackedWidget.setCurrentIndex(0))

	def help_next_page(self):
		self.stackedWidget.setCurrentIndex(self.stackedWidget.currentIndex()+1)

	def help_back_page(self):
		self.stackedWidget.setCurrentIndex(self.stackedWidget.currentIndex()-1)	



