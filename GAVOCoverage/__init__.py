# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GAVOCovearage
                                 A QGIS plugin
 Get coverage from  preview_url
                             -------------------
        begin                : 2018-02-08
        copyright            : (C) 2018 by Mikhail Minin
        email                : m.minin@jacobs-university.de
        git sha              : $Format:%H$
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
    """Load GAVOCoverage class from file GAVOCoverage.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .gavo_coverage import GAVOCoverage
    return GAVOCoverage(iface)
