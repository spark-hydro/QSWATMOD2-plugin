import pandas as pd
import os
import glob

def dummpy(wd):

    output_rch = pd.read_csv(
        os.path.join(wd, "output.rch"),
        sep="\\s+",
        skiprows=9,
        usecols=[1, 3, 6],
        names=["date", "filter", "stf_sim"],
        index_col=0
    )
    # try:
    df = output_rch.loc[58]
    # df = df[df['filter'] < 13]
    # print(len(df))
    date_range_freq(df, "1/1/1980")
    # print(df.index)
    # print(df.stf_sim)


def date_range_freq(df, startDate):
    # if self.dlg.radioButton_day.isChecked():
    #     return pd.date_range(startDate, periods=len(df.stf_sim))
    # elif self.dlg.radioButton_month.isChecked():
    df = df[df['filter'] < 13]
    df.index = pd.date_range(startDate, periods=len(df.stf_sim), freq="ME")
    print(df)
    # else:
    #     return pd.date_range(startDate, periods=len(df.stf_sim), freq="A")


def check_bas(wd):

    for filename in glob.glob(wd+"/*.bas"):
        with open(filename, "r") as f:
            data = []
            for line in f.readlines():
                if not line.startswith("#"):
                    data.append(line.replace('\n', '').split())
    # Get an elevation list from discretiztion file
    ii = 2  # Starting line
    icbunds = []
    # while float(data[ii][0]) > -2:
    #     print(ii)
    #     for jj in range(len(data[ii])):
    #         icbunds.append(int(data[ii][jj]))
    #     ii += 1
    while data[ii][0] != "internal":
        if float(data[ii][0]) < -2:
            break
        for jj in range(len(data[ii])):
            icbunds.append(int(data[ii][jj]))
        ii += 1
    print(icbunds)




if __name__ == "__main__":
    wd = "D:\\Projects\\Watersheds\\minjing\\swmf_v2\\swmf2\\SWAT-MODFLOW"
    check_bas(wd)