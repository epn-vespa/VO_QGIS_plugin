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
from qgis.core    import QgsProject
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from PyQt4.QtGui  import QAction,   QIcon,       QMenu,    QMessageBox
import resources
import threading

import Tkinter as tk
import tkMessageBox

from astropy.vo.samp import SAMPHubServer
from astropy.vo.samp.hub import WebProfileDialog

from .scriptReceiver import scriptReceiver

class TkWebProfileDialog(WebProfileDialog):
    def __init__(self, root):
        self.SampMESSAGE = "A Web application which declares to be\n\nName: {name}\n"+\
            "Origin: {origin}\n\nis requesting to be registered with the SAMP Hub.  "+\
            "Pay attention\nthat if you permit its registration, "+\
            "such application will acquire\nall current user privileges, like file "+\
            "read/write.\n\nDo you give your consent?"
        self.root = root
        self.root.wm_title("SAMP HUB")
        self.wait_for_dialog()

    def wait_for_dialog(self):
        self.handle_queue()
        self.root.after(100, self.wait_for_dialog)

    def show_dialog(self, samp_name, details, client, origin):
        SampMESSAGE="abc"
        text = self.SampMESSAGE.format(name=samp_name, origin=origin)
        if tkMessageBox.askyesno('SAMP Hub', text, default=tkMessageBox.NO): self.consent()
        else: self.reject()

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
            text      = u'start SAMP Hub',
            callback  = self.startReceiver)

    def startSampHub(self):
        def runSampHub():
            self.root=tk.Tk()
            tk.Label(self.root, text="HUB root window. \n Close this terminates \n SAMP Hub Server",
                     font=("Helvetica", 12), justify=tk.CENTER).pack(pady=5)
            self.root.geometry("200x110")
            self.root.update()
            self.h = SAMPHubServer(web_profile_dialog=TkWebProfileDialog(self.root))
            self.h.start()
            self.root.mainloop()
            try:self.root.mainloop() # Main GUI loop 
            except KeyboardInterrupt:pass ## DO I really NEED TRY HERE? How does one even interrupt it? it's a window...
            self.h.stop()
        t=threading.Thread(target=runSampHub)
        t.daemon=True
        t.start()

    def startReceiver(self):
        sr=scriptReceiver(self.iface, self.pinstance).run
##        t=threading.Thread(target=sr)
##        t.daemon=True
##        t.start()
        self.r=scriptReceiver(self.iface, self.pinstance)
        self.r.run()
