from astropy.utils.data import download_file # fixes timeout bug
#from astropy.samp import SAMPIntegratedClient
try:
    from astropy.samp import SAMPIntegratedClient
except ImportError:
    from astropy.vo.samp import SAMPIntegratedClient
from astropy.table import Table
import threading#, time
import time as ttime
from qgis.core import *
import numpy as np
import tempfile
import geojson
import sys
from PyQt4.QtCore import QThread
import traceback

#from VOScriptReceiver_dialog import VOScriptReceiverDialog
from .clientRunnerDialog import ClientRunnerDialog

say= QgsMessageLog.logMessage

class Receiver(object):
    def __init__(self, client):
        self.client = client
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

class addWMSLayerQThread(QThread):
    def __init__(self,params,LayerTitle,iface,root):
        QThread.__init__(self)
        self.params=params
        self.LayerTitle=LayerTitle
        self.iface=iface
        self.root=root
#        self.setAttribute(Qt.WA_DeleteOnClose)
#    def __del__(self):
#        self.wait()
    def run(self):
        q=QgsRasterLayer(self.params,self.LayerTitle,"wms")
        QgsMapLayerRegistry.instance().addMapLayer(q)
        self.root.insertLayer(0,q)

class VOTableLoaderHelper():
#    def __init__(self):
#        pass
    @staticmethod
    def loadWMS(vot,iface,root):
        say("got a WMS!")
        genericPrefix="crs=EPSG:4326&format=image/png&styles="
        dc=vot['obs_id','access_url', 'granule_uid']
        dt=list(np.asarray(dc.as_array()))
        say("starting adding layers")
        say(str(len(dt)))
        iface.mapCanvas().freeze()
        for d in dt:
            GetCapURL=d[1]
            LayerName=d[0]
            LayerTitle=d[2]
            mapUrl=GetCapURL.split('?')[0]+'?'+[x for x in GetCapURL.split('?')[1].split('&') if 'map' in x][0]
            params="&".join([genericPrefix,"url="+mapUrl,"layers="+LayerName])
            say(params)
#            q=QgsRasterLayer(params,LayerTitle,"wms")
#            say(str(q.isValid()))
#            self.iface.mapCanvas().freeze()
#            iface.mapCanvas().freeze()
#            QgsMapLayerRegistry.instance().addMapLayer(q) # order is importaint here
#            root.insertLayer(0,q)
#            self.root.insertLayer(0,q)
#            QgsMapLayerRegistry.instance().reloadAllLayers()
#            iface.mapCanvas().freeze(False)
#            self.iface.mapCanvas().freeze(False)
#                QgsMapLayerRegistry.instance().addMapLayer(q) #<= why am i doing this twice??
#            return
            t=addWMSLayerQThread(params,LayerTitle,iface,root)
#            t.run()
            t.start()
            while True:
                if t.wait(100):
                    break
        QgsMapLayerRegistry.instance().reloadAllLayers()
        iface.mapCanvas().freeze(False)
    @staticmethod
    def getParts(sRegion):
        lon=sRegion.split(' ')[2:][0::2]
        lon=np.asarray([float(i) for i in lon])
        if (lon.max()-lon.min()) > 180:
            lon = [[x, x-360][x>180] for x in lon]
        lat=sRegion.split(' ')[2:][1::2]
        parts = [[    float(lon[i]),float(lat[i])] for i in range(len(lat))]
        if not (parts[0]==parts[-1]): parts.append(parts[0])
        return [parts]
    @staticmethod
    def makeComplFeat(vot, rowN):
        makeFeat      = lambda coords, props: {"type":"Feature","geometry": { "type": "Polygon", "coordinates": coords},"properties": props}
        makeMaskEmpty = lambda vot, rowN:     [str(q).replace('MASKED','') for q in vot[rowN]]
        return makeFeat( VOTableLoaderHelper.getParts(vot['s_region'][rowN]), dict(zip(vot.colnames, makeMaskEmpty(vot, rowN)))) 

class ClientRunner(object):
#class ClientRunner(QThread):
    def __init__(self, iface, pinstance):
        self.iface=iface
#        self.dlg = VOScriptReceiverDialog()
        self.dlg=ClientRunnerDialog()
        self.MSG=self.dlg.label.setText
        self.ProjInstance=pinstance
        self.root=self.ProjInstance.layerTreeRoot()
        self.connectionState=False
        self.dlg.connectBtn.clicked.connect(self.switchCState)

    def capCommand(self, *args, **kwargs):
        MSG=self.MSG 
        self.cli = SAMPIntegratedClient()
        self.cli.connect()
        self.r = Receiver(self.cli)
        MSG( 'Binding methods' )
        #=> case MTYPE: qgis.message
        def qMessage():
            MSG( 'Message: ' + self.r.params['script'])
        #=> case MTYPE: qgis.load.vectorlayer
        def qLoadVectorlayer(): # case MTYPE: qgis.load.vectorlayer
            self.LoadVectorLayer(self.r.params['url'], self.r.params['name'])
        #=> case MTYPE: table.load.votable
        def qLoadVotable():
            loadWMS       = lambda vot: VOTableLoaderHelper.loadWMS(vot, self.iface, self.root)
            makeComplFeat = VOTableLoaderHelper.makeComplFeat
            MSG('Loading VOtable\n from url: \n'+self.r.params['url']);say('SAMP Params are: ' + str(self.r.params))
            vot = Table.read(download_file(self.r.params['url'],timeout=200)) #fixes timeout bug
            if 'access_format' in vot.colnames:
                say(str(vot.columns['access_format'][0])) #<+===
                if b'application/x-wms'in vot.columns['access_format'][0]:
                    try:
                        loadWMS(vot)
                    except Exception:
                        self.MSG('OOPS something went wrong while loading WMS')
                        tb=traceback.format_exc()
                        say(tb)
                    finally:
                        return
            mURL = tempfile.mkdtemp()
            MSG("converting to GeoJSON");say('Number of features to write: '+ str(len(vot)) )
            featList=[]
            for i in range(len(vot)):
                self.MSG('writing number' + str(i))
                featList.append(makeComplFeat(vot, i))
            with open(mURL + '/vot.geojson', 'w') as f: f.write( geojson.dumps({"type":"FeatureCollection","features":featList} ))
            self.MSG('finished download, converting to SpatiaLite')
            try:
                vlayer = QgsVectorLayer(mURL + '/vot.geojson',"mygeojson","ogr")
            except Exception:
                self.MSG('OOPS something went wrong while creating a vector layer from geojson')
                return
            say("writing to SpatiaLite")
            try:
                QgsVectorFileWriter.writeAsVectorFormat(vlayer, mURL+r"/vot.sqlite","utf-8",None,"SpatiaLite")
            except Exception:
                self.MSG('OOPS something went wrong while writing SQLite')
                return
            say("loading SpatiaLite")
            try:
                vlayer = QgsVectorLayer(                        mURL+r"/vot.sqlite",str(self.r.params['name']),"ogr")
            except Exception:
                self.MSG('OOPS something went wrong while creating a vector Layer')
                return
#            say(vot.meta['description']) #description is not available with complex queries
#            vlayer = QgsVectorLayer(                        mURL+r"/vot.sqlite",str(vot.meta['description']),"ogr")
            say("adding layer to canvas")
            try:
                self.addVLayerToCanvas(vlayer)
            except Exception:
                self.MSG('OOPS something went wrong while trying to add layer to canvas')
                return
            say("done")
        mTypeDict={'qgis.message':qMessage,'qgis.load.vectorlayer':qLoadVectorlayer,'table.load.votable':qLoadVotable}
        map(self.bindSamp, mTypeDict.keys())
        MSG("Disconnected")
        while self.connectionState:
            MSG("starting")
            self.r.received = False
            while not self.r.received and self.connectionState:
                MSG("waiting"); ttime.sleep(2)
            if self.connectionState:
                mTypeDict[self.r.mtype]()
                ttime.sleep(2)

    def switchCState(self, *args, **kwargs):
        sys.stdout.write('switching state')
        say("Switching connection state")
        self.connectionState=not self.connectionState
        say("New state is " + str(self.connectionState))
        if self.connectionState:
            self.tc=threading.Thread(name="client", target=self.capCommand, args=(self,))
            self.tc.start()
        else:
            self.cli.disconnect()
            self.MSG('Disconnected')

    def bindSamp(self, MType):
        self.cli.bind_receive_call(         MType, self.r.receive_call         )
        self.cli.bind_receive_notification( MType, self.r.receive_notification )


    def addVLayerToCanvas(self,vlayer):
        self.iface.mapCanvas().freeze()
        QgsMapLayerRegistry.instance().addMapLayer(vlayer) # order is importaint here
#        self.root.addLayer(vlayer)
        self.root.insertLayer(0,vlayer)
        QgsMapLayerRegistry.instance().reloadAllLayers()
        self.iface.mapCanvas().freeze(False)

    def run(self):
        self.dlg.show()
#        self.MSG("hello")
        self.MSG("Disconnected")
        result = self.dlg.exec_()
        if self.connectionState: self.cli.disconnect() # if user closes window - call disconnect to make sure
