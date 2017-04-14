# -*- coding: utf-8 -*-
"""
/***************************************************************************
 polyToAladin
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
    """Load polyToAladin class from file polyToAladin.

    :param iface: A QGIS interface instance.
    :type iface: polyToAladin
    """
    #
    from .polyToAladin import polyToAladin
    return polyToAladin(iface)
