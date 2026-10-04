import pandas as pd
import os

def read_stf_obd(wd, obd_file):
    return pd.read_csv(
        os.path.join(wd, obd_file),
        index_col=0,
        header=0,
        parse_dates=True,
        na_values=[-999, ""]
    )


def read_output_rch_data(wd, colNum=6):
    return pd.read_csv(
        os.path.join(wd, "output.rch"),
        sep="\\s+",
        skiprows=9,
        usecols=[1, 3, colNum],
        names=["date", "filter", "stf_sim"],
        index_col=0
    )


def read_gw_obd(wd, obd_file):
    return pd.read_csv(
        os.path.join(wd, obd_file),
        index_col=0,
        header=0,
        parse_dates=True,
        na_values=[-999, ""]
    )

def read_swatmf_out_MF_obs(wd):
    mf_obs = pd.read_csv(
                        os.path.join(wd, "modflow.obs"),
                        sep="\\s+",
                        skiprows = 2,
                        usecols = [3, 4],
                        index_col = 0,
                        names = ["grid_id", "mf_elev"],)
    # Convert dataframe into a list with string items inside list
    grid_id_lst = mf_obs.index.astype(str).values.tolist()  
    output_wt = pd.read_csv(
                        os.path.join(wd, "swatmf_out_MF_obs"),
                        sep="\\s+",
                        skiprows = 1,
                        names = grid_id_lst,)
    return mf_obs, output_wt


def update_index(df, startDate):
    df.index = pd.date_range(startDate, periods=len(df))
    return df


def time_cvt(df, ts):

    if ts == "Daily":
        df = df
    elif ts == "Monthly":
        df = df
        df = df.resample('M').mean()
    elif ts == "Annual":
        df = df.resample('A').mean()
    return df

def plot_gw_sim_obd(wd, obd_file, startDate, grid_id, ts):
    gw_obd = read_gw_obd(wd, obd_file)
    mf_obs, output_wt = read_swatmf_out_MF_obs(wd)
    # try:
    df = update_index(output_wt, startDate)
    df = time_cvt(df, ts)

    df = df[str(grid_id)] - float(mf_obs.loc[int(grid_id)])


    # ax.plot(df.index.values, df.values, c='limegreen', lw=1, label="Simulated")
    df2 = pd.concat([df, gw_obd[obd_col]], axis=1)
    df3 = df2.dropna()
    # plot_observed_data(ax, df3, grid_id, obd_col)
    return df3




if __name__ == "__main__":
    # wd = "/Users/seonggyu.park/Documents/projects/kokshila/analysis/koksilah_swatmf/SWAT-MODFLOW"
    wd = "D:/Projects/Watersheds/Koksilah/analysis/koksilah_swatmf/SWAT-MODFLOW"
    obd_col = "g_431"
    # outfd = "d:/Projects/Watersheds/Okavango/Analysis/2nd_cali"
    # get_rech_avg_m_df(wd).to_csv(os.path.join(outfd, 'test.csv'))
    obd_file = "dtw_day.obd.csv"
    startDate = "1/1/2009"
    strObd = read_gw_obd(wd, obd_file)
    # output_rch = read_output_rch_data(wd)
    # # try:
    # df = output_rch.loc[30]
    # df.index = pd.date_range(startDate, periods=len(df.stf_sim))
    # # df2 = pd.concat([df, strObd["sub03"]], axis=1)
    dff = plot_gw_sim_obd(wd, obd_file, startDate, 431, "Daily")
    # print(sum(dff[obd_col].values))
    # print((float(dff[obd_col])))
    print(sum(pd.to_numeric(dff[obd_col])))
    # print(strObd[strObd.index.duplicated()])
    # print(strObd.index)
    print(dff.index)
    # print(strObd.loc[strObd.index.duplicated()==True])

