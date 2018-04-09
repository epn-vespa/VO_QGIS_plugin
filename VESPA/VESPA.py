# -*- coding: utf-8 -*-
"""
/***************************************************************************
 VESPA
                                 A QGIS plugin
 Interfaces with VESPA Virtual Observatory
                              -------------------
        begin                : 2017-03-23
        git sha              : $Format:%H$
        copyright            : (C) 2017 by Mikhail Minin
        email                : m.minin@jacobs-university.de
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.core    import QgsProject, QgsMessageLog
#from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from PyQt4.QtGui  import QAction,   QIcon,       QMenu,    QMessageBox
from PyQt4 import QtCore
from PyQt4 import QtGui
import resources
#import threading as tthreading

#from astropy.samp import SAMPHubServer
#from astropy.samp.hub import WebProfileDialog

#from .scriptReceiver import scriptReceiver
#from .myHUB import *

from .hubRunner import HubRunner
from .clientRunner import ClientRunner


class VESPA:
    def __init__(self, iface):
        self.iface     = iface
        self.actions   = []
        self.myMenu    = self.iface.mainWindow().menuBar().findChild(QMenu, 'mWebMenu')
        self.toolbar   = self.iface.addToolBar(u'VESPA')
        self.toolbar.setObjectName(u'VESPA')
        self.pinstance=QgsProject.instance()

    def create_action(self, icon_path, text, callback):
        """Create new action to add to the menu"""
        action = QAction(QIcon(icon_path), text, self.iface.mainWindow())
        action.triggered.connect( callback   )
        action.setEnabled(        True       )
        self.toolbar.addAction(   action     )
        self.myMenu.addAction(    action     )
        self.actions.append(      action     )

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.myMenu.removeAction(  action )
            self.iface.removeToolBarIcon( action )
        del self.toolbar

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        self.create_action(
            icon_path = ':/plugins/VESPA/iconVESPA.png',
            text      = u'start SAMP Hub',
            callback  = self.startSampHub)
        self.create_action(
            icon_path = ':/plugins/VESPA/iconReceiver.png',
            text      = u'start SAMP Client',
#            callback  = self.startReceiver)
            callback  = self.startSampClient)

    def startSampHub(self):
#        self.sh=HUBrunner(self.iface, self.pinstance)
        self.sh=HubRunner(self.iface, self.pinstance)
        self.sh.run()

#    def startReceiver(self):
    def startSampClient(self):
#        self.r=scriptReceiver(self.iface, self.pinstance)
        self.r=ClientRunner(self.iface, self.pinstance)
        self.r.run()
