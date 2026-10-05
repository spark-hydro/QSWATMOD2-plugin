# -*- coding: utf-8 -*-
from qgis.core import (
            QgsProject, QgsLayerTreeLayer, QgsVectorFileWriter,
            QgsVectorLayer, QgsField)
from qgis.PyQt import QtCore, QtGui, QtSql  
from qgis.PyQt.QtCore import QCoreApplication              
from PyQt5.QtWidgets import QMessageBox


def cvt_plotsToVideo(self):
    import os
    import argparse
    QSWATMOD_path_dict = self.dirs_and_paths()
    exported = QSWATMOD_path_dict['exported_files']

    # Construct the argument parser and parse the arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-ext", "--extension", required=False, default='png', help="extension name. default is 'png'.")
    ap.add_argument("-o", "--output", required=False, default='output.mp4', help="output video file")
    args = vars(ap.parse_args())

    if self.dlg.radioButton_gwsw_day.isChecked():
        dir_path = os.path.join(exported, "gwsw_day")
    elif self.dlg.radioButton_gwsw_month.isChecked():
        dir_path = os.path.join(exported, "gwsw_month")
    elif self.dlg.radioButton_gwsw_year.isChecked():
        dir_path = os.path.join(exported, "gwsw_annual")

    # Arguments
    ext = args['extension']
    output = args['output']
    images = []
    for f in os.listdir(dir_path):
        if f.endswith(ext):
            images.append(f)

    # Determine the width and height from the first image
    image_path = os.path.join(dir_path, images[0])
    frame = cv2.cv2.imread(image_path)
    cv2.imshow('video',frame)
    height, width, channels = frame.shape
    fps = int(self.dlg.lineEdit_gwsw_fps.text())

    # Define the codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'mp4v') # Be sure to use lower case
    out = cv2.VideoWriter(os.path.join(dir_path, output), fourcc, fps, (width, height))
    for image in images:
        image_path = os.path.join(dir_path, image)
        frame = cv2.imread(image_path)
        out.write(frame) # Write out frame to video
        # -- Preview --
        # cv2.imshow('video',frame)
        # if (cv2.waitKey(1) & 0xFF) == ord('q'): # Hit `q` to exit 
        #     break

    # Release everything if job is finished 
    out.release()
    cv2.destroyAllWindows()
    questionBox = QMessageBox()
    questionBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
    reply = QMessageBox.question(
                    questionBox, 'Play?', 
                    'Would you like to play the video?', QMessageBox.Yes, QMessageBox.No)
    if reply == QMessageBox.Yes:
        os.startfile(os.path.join(dir_path, "output.mp4"))
