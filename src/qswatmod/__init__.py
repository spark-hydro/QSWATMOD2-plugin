# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QSWATMOD2
                                 A QGIS plugin
 This plugin helps link SWAT and MODFLOW model.
                             -------------------
        begin                : 2020-01-23
        copyright            : (C) 2020 by Seonggyu Park
        email                : seonggyu.park@brc.tamus.edu
        git sha              : https://github.com/spark-brc/QSWATMOD2
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load QSWATMOD2 class from file QSWATMOD2.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .QSWATMOD2 import QSWATMOD2
    return QSWATMOD2(iface)
