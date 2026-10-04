from builtins import str
from builtins import range
import os
import os.path
import operator
import math, datetime
from qgis.core import (
                        QgsVectorLayer, QgsField,
                        QgsProject, QgsFeatureIterator, QgsVectorFileWriter,
                        QgsLayerTreeLayer)
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMessageBox


def create_swatmf_link(
                    self, mf_act_st, irrig_act_st,
                    irrig_act_swat_st, drain_act_st, rt3d_act_st):

    QSWATMOD_path_dict = self.dirs_and_paths() 
    stdate, eddate, stdate_warmup, eddate_warmup = self.define_sim_period()
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

    # definition of folders
    inFolder = QSWATMOD_path_dict['Table']
    outFolder = QSWATMOD_path_dict['SMfolder']
    file_to_change = "swatmf_link.txt"

    infile = os.path.join(inFolder, file_to_change)
    outfile = os.path.join(outFolder, file_to_change)

    if mf_act_st == 'Yes':
        mf_active = '1    SWAT-MODFLOW is activated\n'
    elif mf_act_st == 'No':
        mf_active = '0    SWAT-MODFLOW is activated\n'
    if irrig_act_st == 'Yes':
        irrig_act = '1    MODFLOW Pumping --> SWAT Irrigation\n'
    elif irrig_act_st == 'No':
        irrig_act = '0    MODFLOW Pumping --> SWAT Irrigation\n'
    if irrig_act_swat_st == 'Yes':
        irrig_act_swat = '1    SWAT Auto-Irrigation --> MODFLOW Pumping\n'
    elif irrig_act_swat_st == 'No':
        irrig_act_swat = '0    SWAT Auto-Irrigation --> MODFLOW Pumping\n'
    if drain_act_st == 'Yes':
        drain_act = '1    MODFLOW Drains --> SWAT subbasin channels\n'
    elif drain_act_st == 'No':
        drain_act = '0    MODFLOW Drains --> SWAT subbasin channels\n'
    if rt3d_act_st == 'Yes':
        rt3d_active = '1    RT3D is active (N and P groundwater reactive transport)\n'
    elif rt3d_act_st == 'No':
        rt3d_active = '0    RT3D is active (N and P groundwater reactive transport)\n'

    # # mf_interval
    # freq_mf = self.dlg.spinBox_freq_mf.value()

    # Read in mf_obs
    if self.dlg.checkBox_mf_obs.isChecked():
        mf_obs = '1    Read in observation cells from "modflow.obs"\n'
    else:
        mf_obs = '0    Read in observation cells from "modflow.obs"\n'       

    # Optional output for SWAT-MODFLOW output
    if self.dlg.checkBox_swat_dp_hru.isChecked():
        swat_dp = "1    SWAT Deep Percolation (mm) (for each HRU)\n"
    else:
        swat_dp = "0    SWAT Deep Percolation (mm) (for each HRU)\n"
    if self.dlg.checkBox_mf_recharge.isChecked():
        mf_rch = "1    MODFLOW Recharge (m3/day) (for each MODFLOW Cell)\n"
    else:
        mf_rch = "0    MODFLOW Recharge (m3/day) (for each MODFLOW Cell)\n"      
    if self.dlg.checkBox_channel_depth.isChecked():
        swat_ch_depth = "1    SWAT Channel Depth (m) (for each SWAT Subbasin)\n"
    else:
        swat_ch_depth = "0    SWAT Channel Depth (m) (for each SWAT Subbasin)\n"
    if self.dlg.checkBox_river_stage.isChecked():
        mf_riv_stage = "1    MODFLOW River Stage (m) (for each MODFLOW River Cell)\n"
    else:
        mf_riv_stage = "0    MODFLOW River Stage (m) (for each MODFLOW River Cell)\n"
    if self.dlg.checkBox_gw_sw_grid.isChecked():
        mf_gw_sw = "1    Groundwater/Surface Water Exchange (m3/day) (for each MODFLOW River Cell)\n"
    else:
        mf_gw_sw = "0    Groundwater/Surface Water Exchange (m3/day) (for each MODFLOW River Cell)\n"
    if self.dlg.checkBox_gw_sw_sub.isChecked():
        swat_gw_sw = "1    Groundwater/Surface Water Exchange (m3/day) (for each SWAT Subbasin)\n"
    else:
        swat_gw_sw = "0    Groundwater/Surface Water Exchange (m3/day) (for each SWAT Subbasin)\n"
    if self.dlg.checkBox_printing_m_a.isChecked():
        printing_m_a = "1    Print out average values for SWAT-MODFLOW and RT3D output variables\n"
    else:
        printing_m_a = "0    Print out average values for SWAT-MODFLOW and RT3D output variables\n"

    lines = []
    with open(infile, 'r') as f:
        for line in f:
            if line.strip().startswith('1    SWAT-MODFLOW'):
                line = mf_active
            if line.startswith('0    MODFLOW Pumping'):
                line = irrig_act
            if line.startswith('0    SWAT Auto-Irrigation'):
                line = irrig_act_swat
            if line.startswith('0    MODFLOW Drains'):
                line = drain_act
            if line.startswith('0    RT3D is active'):
                line = rt3d_active
            # if line.startswith('1    mf_interval'):
            #     line = str(freq_mf) + "    mf_interval: the number of days between MODFLOW runs\n"           
            if str(line).startswith('0    Read in observation'):
                line = str(mf_obs)
            if str(line).startswith('1    SWAT Deep'):
                line = swat_dp
            if str(line).startswith('1    MODFLOW Recharge'):
                line = mf_rch
            if str(line).startswith('1    SWAT Channel'):
                line = swat_ch_depth
            if str(line).startswith('1    MODFLOW River'):
                line = mf_riv_stage
            if line.startswith('1    Groundwater/Surface Water Exchange (m3/day) (for each MODFLOW River Cell)'):
                line = mf_gw_sw
            if line.startswith('1    Groundwater/Surface Water Exchange (m3/day) (for each SWAT Subbasin)'):
                line = swat_gw_sw
            if line.startswith('1    Print out'):
                line = printing_m_a

            lines.append(line)

        info = "# == Write SWAT-MODFLOW output only on specified days == \n"
        lines.append(info)

        # Obtain time step
        sim_period = duration
        step = self.dlg.spinBox_freq_sm_output.value()

        if step != 1:
            lines.append(str(int(math.floor(sim_period / step) + 1))+"\n")
            lines.append(str(1)+"\n")  # force to include the first day
            for i in range(step, sim_period+1, step):
                lines.append(str(i)+"\n")
        else:
            lines.append(str(int(math.floor(sim_period / step)))+"\n")
            for i in range(step, sim_period+1, step):
                lines.append(str(i)+"\n")

        info2 = "# == Groundwater delay == \n"
        lines.append(info2)

        if self.dlg.radioButton_gw_delay_multi.isChecked():
            lines.append("1    0 = read in a single value for all HRUs; 1 = read in one value for each HRU\n")
            input1 = QgsProject.instance().mapLayersByName("gw_delay")[0]
            data = [i.attributes() for i in input1.getFeatures()]
            hru_idx = input1.dataProvider().fields().indexFromName("HRU_ID")
            data_sort = sorted(data, key=operator.itemgetter(hru_idx))
            for i in data_sort:
                lines.append(str(i[1]) + "\n")
        else:
            gwd = self.dlg.spinBox_gw_delay_single.value()
            lines.append("0    0 = read in a single value for all HRUs; 1 = read in one value for each HRU\n")
            lines.append(str(gwd) + "    GW_DELAY : Groundwater delay [days]\n")

    with open(outfile, 'w') as outfile:
        for line in lines:
            outfile.write(str(line))

    msgBox = QMessageBox()
    msgBox.setWindowIcon(QIcon(':/QSWATMOD2/pics/sm_icon.png'))
    msgBox.setWindowTitle("Exported!")
    msgBox.setText("Your configuration settings have been exported to your SWAT-MODFLOW model!")
    msgBox.exec_()
