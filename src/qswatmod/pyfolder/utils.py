import numpy as np
import datetime
import os
from PyQt5.QtWidgets import QMessageBox
from qgis.PyQt import QtGui
import pandas as pd

class ObjFns:
    def __init__(self) -> None:
        pass
        
    # def obj_fns(obj_fn, sims, obds):
    #     return obj_fn(sims, obds)
    @staticmethod
    def nse(sims, obds):
        """Nash-Sutcliffe Efficiency (NSE) as per `Nash and Sutcliffe, 1970
        <https://doi.org/10.1016/0022-1694(70)90255-6>`_.

        :Calculation Details:
            .. math::
            E_{\\text{NSE}} = 1 - \\frac{\\sum_{i=1}^{N}[e_{i}-s_{i}]^2}
            {\\sum_{i=1}^{N}[e_{i}-\\mu(e)]^2}

            where *N* is the length of the *sims* and *obds*
            periods, *e* is the *obds* series, *s* is (one of) the
            *sims* series, and *μ* is the arithmetic mean.

        """
        nse_ = 1 - (
                np.sum((obds - sims) ** 2, axis=0, dtype=np.float64)
                / np.sum((obds - np.mean(obds)) ** 2, dtype=np.float64)
        )
        return nse_

    @staticmethod
    def rmse(sims, obds):
        """Root Mean Square Error (RMSE).

        :Calculation Details:
            .. math::
            E_{\\text{RMSE}} = \\sqrt{\\frac{1}{N}\\sum_{i=1}^{N}[e_i-s_i]^2}

            where *N* is the length of the *sims* and *obds*
            periods, *e* is the *obds* series, *s* is (one of) the
            *sims* series.

        """
        rmse_ = np.sqrt(np.mean((obds - sims) ** 2,
                                axis=0, dtype=np.float64))

        return rmse_

    @staticmethod
    def pbias(sims, obds):
        """Percent Bias (PBias).

        :Calculation Details:
            .. math::
            E_{\\text{PBias}} = 100 × \\frac{\\sum_{i=1}^{N}(e_{i}-s_{i})}{\\sum_{i=1}^{N}e_{i}}

            where *N* is the length of the *sims* and *obds*
            periods, *e* is the *obds* series, and *s* is (one of)
            the *sims* series.

        """
        pbias_ = (100 * np.sum(obds - sims, axis=0, dtype=np.float64)
                / np.sum(obds))

        return pbias_

    @staticmethod
    def rsq(sims, obds):
        ## R-squared
        rsq_ = (
            (
                (sum((obds - obds.mean())*(sims-sims.mean())))**2
            ) 
            /
            (
                (sum((obds - obds.mean())**2)* (sum((sims-sims.mean())**2))
            ))
        )
        return rsq_


class DefineTime:

    def __init__(self) -> None:
        pass

    def define_sim_period(self):
        import datetime
        QSWATMOD_path_dict = self.dirs_and_paths()
        wd = QSWATMOD_path_dict['SMfolder']
        if os.path.isfile(os.path.join(wd, "file.cio")):
            cio = open(os.path.join(wd, "file.cio"), "r")
            lines = cio.readlines()
            skipyear = int(lines[59][12:16])
            iprint = int(lines[58][12:16]) #read iprint (month, day, year)
            styear = int(lines[8][12:16]) #begining year
            styear_warmup = int(lines[8][12:16]) + skipyear #begining year with warmup
            edyear = styear + int(lines[7][12:16])-1 # ending year
            edyear_warmup = styear_warmup + int(lines[7][12:16])-1 - int(lines[59][12:16])#ending year with warmup
            if skipyear == 0:
                FCbeginday = int(lines[9][12:16])  #begining julian day
            else:
                FCbeginday = 1  #begining julian day
            FCendday = int(lines[10][12:16])  #ending julian day
            cio.close()

            stdate = datetime.datetime(styear, 1, 1) + datetime.timedelta(FCbeginday - 1)
            eddate = datetime.datetime(edyear, 1, 1) + datetime.timedelta(FCendday - 1)
            stdate_warmup = datetime.datetime(styear_warmup, 1, 1) + datetime.timedelta(FCbeginday - 1)
            eddate_warmup = datetime.datetime(edyear_warmup, 1, 1) + datetime.timedelta(FCendday - 1)
            startDate_warmup = stdate_warmup.strftime("%m/%d/%Y")
            endDate_warmup = eddate_warmup.strftime("%m/%d/%Y")
            startDate = stdate.strftime("%m/%d/%Y")
            endDate = eddate.strftime("%m/%d/%Y")
            duration_ = (eddate - stdate).days
            return duration_
        
class PlotUtils:
    def __init__(self) -> None:
        pass

    # NOTE: metrics =======================================================================================
    def calculate_metrics(self, ax, df3, grid_id, obd_col):
        # df3 = df3.astype({str(grid_id): float, obd_col: float})
        r_squared = ((sum((df3[obd_col] - df3[obd_col].mean()) * (df3[str(grid_id)] - df3[str(grid_id)].mean())))**2) / (
                (sum((df3[obd_col] - df3[obd_col].mean())**2) * (sum((df3[str(grid_id)] - df3[str(grid_id)].mean())**2)))
        )
        dNS = 1 - (sum((df3[str(grid_id)] - df3[obd_col])**2) / sum((df3[obd_col] - (df3[obd_col]).mean())**2))
        PBIAS = 100 * (sum(df3[obd_col] - df3[str(grid_id)]) / sum(df3[obd_col]))
        self.display_metrics(ax, dNS, r_squared, PBIAS)

    def display_metrics(self, ax, dNS, r_squared, PBIAS):
        ax.text(
            .01, 0.95, f'Nash-Sutcliffe: {dNS:.4f}',
            fontsize=8, horizontalalignment='left', color='limegreen', transform=ax.transAxes
        )
        ax.text(
            .01, 0.90, f'$R^2$: {r_squared:.4f}',
            fontsize=8, horizontalalignment='left', color='limegreen', transform=ax.transAxes
        )
        ax.text(
            .99, 0.95, f'PBIAS: {PBIAS:.4f}',
            fontsize=8, horizontalalignment='right', color='limegreen', transform=ax.transAxes
        )

    def display_no_data_message(self, ax):
        ax.text(
            .01, .95, 'Nash-Sutcliffe: ---',
            fontsize=8, horizontalalignment='left', transform=ax.transAxes
        )
        ax.text(
            .01, 0.90, '$R^2$: ---',
            fontsize=8, horizontalalignment='left', color='limegreen', transform=ax.transAxes
        )
        ax.text(
            .99, 0.95, 'PBIAS: ---',
            fontsize=8, horizontalalignment='right', color='limegreen', transform=ax.transAxes
        )

    def handle_exception(self, ax, exception_message):
        ax.text(
            .5, .5, exception_message,
            fontsize=12, horizontalalignment='center', weight='extra bold', color='y', transform=ax.transAxes
        )


class ExportUtils:
    def __init__(self) -> None:
        pass

    # NOTE: metrics =======================================================================================
    def calculate_statistics(self, df3, grid_id, obd_col):
        objf = ObjFns()
        sims = df3[str(grid_id)].to_numpy()
        obds = df3[str(obd_col)].to_numpy()
        nse = objf.nse(sims, obds)
        rmse = objf.rmse(sims, obds)
        pbias = objf.pbias(sims, obds)
        rsq = objf.rsq(sims, obds)
        return rsq, rmse, pbias

    def show_error_message(self, title, message):
        msgBox = QMessageBox()
        msgBox.setWindowIcon(QtGui.QIcon(':/QSWATMOD2/pics/sm_icon.png'))
        msgBox.setWindowTitle(title)
        msgBox.setText(message)
        msgBox.exec_()