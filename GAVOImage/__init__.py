# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GAVOImage
                                 A QGIS plugin
 Get image from  preview_url
                             -------------------
        begin                : 2016-11-21
        copyright            : (C) 2016 by Mikhail Minin
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
    """Load GAVOImage class from file GAVOImage.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .gavo_image import GAVOImage
    return GAVOImage(iface)
