import os
import pandas as pd
import datetime

def get_rech_avg_m_df(wd, ):
    os.chdir(wd)
    startDate = "01-01-2000"
    # Open "swatmf_out_MF_head" file
    y = ("Monthly", "Yearly") # Remove unnecssary lines
    filename = "swatmf_out_MF_recharge_monthly"
    # self.layer = QgsProject.instance().mapLayersByName("mf_nitrate_monthly")[0]
    with open(os.path.join(wd, filename), "r") as f:
        data = [x.strip() for x in f if x.strip() and not x.strip().startswith(y)] # Remove blank lines     
    date = [x.strip().split() for x in data if x.strip().startswith("month:")] # Collect only lines with dates  
    onlyDate = [x[1] for x in date] # Only date
    data1 = [x.split() for x in data] # make each line a list
    dateList = pd.date_range(startDate, periods=len(onlyDate), freq ='M').strftime("%b-%Y").tolist()


    selectedSdate = "Jan-2000"
    selectedEdate = "Dec-2000"
    # Reverse step
    dateSidx = dateList.index(selectedSdate)
    dateEidx = dateList.index(selectedEdate)
    dateList_f = dateList[dateSidx:dateEidx+1]
    print(dateList_f)
    # input1 = QgsProject.instance().mapLayersByName("mf_grid (MODFLOW)")[0] # Put this here to know number of features

    big_df = pd.DataFrame()
    datecount = 0
    for selectedDate in dateList_f:
        # Reverse step
        dateIdx = dateList.index(selectedDate)
        #only
        onlyDate_lookup = onlyDate[dateIdx]
        dt = datetime.datetime.strptime(selectedDate, "%b-%Y")
        year = dt.year
        # layerN = self.dlg.comboBox_rt_layer.currentText()
        for num, line in enumerate(data1, 1):
            if ((line[0] == "month:" in line) and (line[1] == onlyDate_lookup in line) and (line[3] == str(year) in line)):
                ii = num # Starting line
        
        # NOTE: when you have layer
        # count = 0
        # # while ((data1[count+ii][0] != 'layer:') and (data1[count+ii][1] != layer)):  # why not working?
        # while not ((data1[count+ii][0] == 'layer:') and (data1[count+ii][1] == layerN)):
        #     count += 1
        # stline = count+ii+1
        # -------------
        mf_hds = []
        hdcount = 0
        
        
        while hdcount < 74095:
            for kk in range(len(data1[ii])):
                mf_hds.append(float(data1[ii][kk]))
                hdcount += 1
            ii += 1
        s = pd.Series(mf_hds, name=datetime.datetime.strptime(selectedDate, "%b-%Y").strftime("%Y-%m-%d"))
        big_df = pd.concat([big_df, s], axis=1)
        datecount +=1
        provalue = round(datecount/len(dateList_f)*100)
        print(provalue)

        # self.dlg.progressBar_rt.setValue(provalue)
        # QCoreApplication.processEvents()
        # self.dlg.raise_()

    big_df = big_df.T
    big_df.index = pd.to_datetime(big_df.index)
    mbig_df = big_df.groupby(big_df.index.month).mean()

    # msgBox = QMessageBox()
    # msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
    # msgBox.setWindowTitle("Select!")
    # msgBox.setText("Please, select months then click EXPORT")
    # msgBox.exec_()


    return mbig_df

def comp_rech(wd):
    os.chdir(wd)
    base_df = pd.read_csv("base_mf_rech_avg_mon.csv")
    rd_df = pd.read_csv("rd_mf_rech_avg_mon.csv")
    b_r_df = base_df.subtract(rd_df)
    b_r_df = b_r_df.T
    b_r_df.columns =['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
    b_r_df['mf_grid'] = [i+1 for i in range(len(b_r_df))]

    print(b_r_df.max().max())
    print(b_r_df.min().min())
    b_r_df_stat =  b_r_df.describe(include='all')
    b_r_df.to_csv("b_r_df.csv", index=False)
    b_r_df_stat.to_csv("b_r_df_stat.csv", index=True)

if __name__ == "__main__":
    wd = "d:/Projects/Watersheds/Okavango/Analysis/CORB_swatmf_models/"
    # outfd = "d:/Projects/Watersheds/Okavango/Analysis/2nd_cali"
    # get_rech_avg_m_df(wd).to_csv(os.path.join(outfd, 'test.csv'))

    comp_rech(wd)
