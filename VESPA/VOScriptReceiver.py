# -*- coding: utf-8 -*-
"""
/***************************************************************************
 VOScriptReceiver
                                 A QGIS plugin
 VOScriptReceiver
                              -------------------
        begin                : 2016-11-10
        git sha              : $Format:%H$
        copyright            : (C) 2016 by Mikhail Minin
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
from astropy.vo.samp import SAMPIntegratedClient
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from PyQt4.QtGui import QAction, QIcon
# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from VOScriptReceiver_dialog import VOScriptReceiverDialog
import os.path
import threading, time
from qgis.core import *
from astropy.table import Table
import shapefile
import numpy as np
import os
import tempfile
import geojson
#from qgis.gui import *
#import qgis.utils

class mvoid:
    pass

class VOScriptReceiver:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        self.r=mvoid()
        self.r.params={'script':''}
        self.dlg = VOScriptReceiverDialog()
        self.connectionState=False
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'VOScriptReceiver_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)


        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&VOScriptReceiver')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'VOScriptReceiver')
        self.toolbar.setObjectName(u'VOScriptReceiver')
        # Tie in connection button
        self.dlg.connectBtn.clicked.connect(self.switchCState)

    def switchCState(self, *args, **kwargs): 
        self.connectionState=not self.connectionState
        if self.connectionState:
            self.t=threading.Thread(name="vodka", target=self.capCommand, args=(self,))
            self.t.start()
        else:
            self.dlg.label.setText("Disconnected")

    def LoadVectorLayer(self):
        pass


    class Receiver(object):
        def __init__(self, client):
            self.client = SAMPIntegratedClient()
            self.received = False
        def receive_call(self, private_key, sender_id, msg_id, mtype, params, extra):
            self.params = params
            self.mtype = mtype
            self.received = True
            self.client.reply(msg_id, {"samp.status": "samp.ok", "samp.result": {}})
        def receive_notification(self, private_key, sender_id, mtype, params, extra):
            self.mtype = mtype
            self.params = params
            self.received = True

    def mLoadVectorLayer(self, mURL, mName):
        self.iface.mapCanvas().freeze() 
        self.dlg.label.setText('doing')
        #'/home/mminin/Documents/temp/shp/test.shp'
        self.mylayer=QgsVectorLayer(mURL, mName,'ogr')
        self.dlg.label.setText(str(self.mylayer))
        self.ProjInstance=QgsProject.instance()
        self.root=self.ProjInstance.layerTreeRoot()
        QgsMapLayerRegistry.instance().addMapLayer(self.mylayer)
        self.root.addLayer(self.mylayer)
        self.iface.mapCanvas().freeze(False) 

    def bindSamp(self, MType):
        self.cli.bind_receive_call(        MType, self.r.receive_call)
        self.cli.bind_receive_notification(MType, self.r.receive_notification)

    def convertVOTtoSHP(self, vot, destination):
        self.dlg.label.setText('init writer')
        w = shapefile.Writer(shapefile.POLYGON)
        self.dlg.label.setText('write fields')
        for colname in vot.colnames: 
            if colname=='s_region' or colname=='access_url' or colname=='thumbnail_url':
                w.field(colname, 'C', '254')
            else:
                w.field(colname)
        self.dlg.label.setText('define getParts')
        def getParts(sRegion):
            lon=sRegion.split(' ')[2:][0::2]
            llon=np.asarray([float(i) for i in lon])
            spread=llon.max()-llon.min() ###
            if spread > 180:
                lon = [[x, x-360][x>180] for x in llon]
            lat=sRegion.split(' ')[2:][1::2]
            return [[[360-float(lon[i]),float(lat[i])] for i in range(len(lat))]]
        self.dlg.label.setText('define writeRecord')
        def writeRecord(rowNumber):
            w.poly(getParts(vot['s_region'][rowNumber]))
            w.record(*list(vot[rowNumber].as_void()))
        self.dlg.label.setText('writeRecords')
        for i in range(len(vot)): writeRecord(i)
        self.dlg.label.setText('save file: ' + destination)
        w.save(destination)
        self.dlg.label.setText('saved at: ' + destination)


    def convertVOTtoGEOJSON(self, vot, destination):
        self.dlg.label.setText('defining getParts')
        def getParts(sRegion):
            lon=sRegion.split(' ')[2:][0::2]
            llon=np.asarray([float(i) for i in lon])
            spread=llon.max()-llon.min() ###
            if spread > 180:
                lon = [[x, x-360][x>180] for x in llon]
            lat=sRegion.split(' ')[2:][1::2]
            return [[[360-float(lon[i]),float(lat[i])] for i in range(len(lat))]]
        self.dlg.label.setText('making feature')
        makeFeature=lambda coords, props: {"type":"Feature","geometry": { "type": "Polygon", "coordinates": coords},"properties": props}
        self.dlg.label.setText('making dump')
        makeJSONdump=lambda featList: geojson.dumps({"type":"FeatureCollection","features":featList})
        self.dlg.label.setText('making path')
#        tempPath=destination+'vot.geojson'
#        mycoords=[[1,2],[3,4],[5,1]]
        self.dlg.label.setText('completing feature')
        makeCompleteFeature=lambda vot, rowN: makeFeature(getParts(vot['s_region'][rowN]),dict(zip(vot.colnames,[str(x).replace('MASKED','') for x in vot[rowN]])))
        self.dlg.label.setText('making list')
        self.dlg.label.setText('starting iter '+ str(len(vot)) )
        featList=[]
        for i in range(len(vot)):
            self.dlg.label.setText('writing number' + str(i))
            featList.append(makeCompleteFeature(vot, i))
        self.dlg.label.setText('dumping')
        d=makeJSONdump(featList)
        self.dlg.label.setText('writing')
        f=open(destination, 'w')
        f.write(d)
        f.close()
        self.dlg.label.setText('finished')

    def capCommand(self, *args, **kwargs):
        self.cli = SAMPIntegratedClient()
        self.cli.connect()
        self.r = self.Receiver(self.cli)
        self.dlg.label.setText("Binding methods")
        map(self.bindSamp,["qgis.message","qgis.load.vectorlayer","qgis.script", "table.load.votable"])
        while self.connectionState:
            self.dlg.label.setText("starting")
            self.r.received = False
            while not self.r.received and self.connectionState:
                self.dlg.label.setText("waiting")
                time.sleep(2)
            self.dlg.label.setText("Command recieved")
#            self.cli.disconnect()
            if self.r.mtype == 'qgis.message': 
                self.dlg.label.setText('Message: ' + self.r.params['script'])
            elif self.r.mtype == 'qgis.load.vectorlayer':
                self.dlg.label.setText('loading')
                self.mLoadVectorLayer(self.r.params['url'], self.r.params['name'])
                self.dlg.label.setText('done')
            elif self.r.mtype == 'qgis.script':
                self.dlg.label.setText('Exec: ' + self.r.params['script'])
                exec(self.r.params['script'])
            elif self.r.mtype == 'table.load.votable': #url, table-id, name
                self.dlg.label.setText('Votable url: '+self.r.params['url'])
                vot = Table.read(self.r.params['url'])
#                self.dlg.label.setText(str(len(vot))
#                self.dlg.label.setText('table captured')
#                vot.show_in_browser(jsviewer=True) #should open table in a browser
                destination=tempfile.mkdtemp()
#                destination+='/vot.shp'
                destination+='/vot.geojson'
#                destination='/home/mminin/Documents/temp/shp/crism01.shp'
                self.dlg.label.setText('converting to geojson')
#                self.convertVOTtoSHP(vot, destination)
                self.convertVOTtoGEOJSON(vot, destination)
                self.dlg.label.setText('loading to map')
#                if self.r.params
                self.mLoadVectorLayer(destination, self.r.params['name'])
                self.dlg.label.setText('loaded')
                time.sleep(5)
            time.sleep(2)
            self.dlg.label.setText("slept")
        self.cli.disconnect()
        self.dlg.label.setText("Disconnected")
        return

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        return QCoreApplication.translate('VOScriptReceiver', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):

        # Create the dialog (after translation) and keep reference
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/VOScriptReceiver/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'VO script receiver'),
            callback=self.run,
            parent=self.iface.mainWindow())


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&VOScriptReceiver'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar


    def run(self):
        """Run method that performs all the real work"""
        # show the dialog
        self.dlg.show()
        self.dlg.label.setText("hello")
        self.t=threading.Thread(name="hubClient", target=self.capCommand, args=(self,))
        self.t.start()
        # Run the dialog event loop
        result = self.dlg.exec_()
#        self.t.join()
        if self.connectionState: self.cli.disconnect()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass
