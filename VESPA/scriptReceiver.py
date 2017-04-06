from astropy.vo.samp import SAMPIntegratedClient
from astropy.table import Table
import threading, time
from qgis.core import *
import numpy as np
import tempfile
import geojson

from VOScriptReceiver_dialog import VOScriptReceiverDialog

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

class scriptReceiver(object):
    def __init__(self, iface, pinstance):
        self.iface=iface
        self.dlg = VOScriptReceiverDialog()
        self.MSG=self.dlg.label.setText
        self.ProjInstance=pinstance
        self.root=self.ProjInstance.layerTreeRoot()
        self.connectionState=False
        self.dlg.connectBtn.clicked.connect(self.switchCState)

    def switchCState(self, *args, **kwargs):
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

    def capCommand(self, *args, **kwargs):
        MSG=self.MSG 
        self.cli = SAMPIntegratedClient()
        self.cli.connect()
        self.r = Receiver(self.cli)
        MSG( 'Binding methods' )
        ### CASE START ###  # using f-dict instead of elif because later binding keys
        mTypeDict={}
        def q(): # case MTYPE: qgis.message
            MSG( 'Message: ' + self.r.params['script'])
        mTypeDict['qgis.message']=q; del q
        def q(): # case MTYPE: qgis.load.vectorlayer
            MSG( 'loading')
            self.LoadVectorLayer(self.r.params['url'], self.r.params['name'])
            MSG( 'done')
        mTypeDict['qgis.load.vectorlayer']=q; del q
        def q(): # case MTYPE: table.load.votable
            say('SAMP Params are: ' + str(self.r.params))
            MSG('Loading VOtable\n from url: \n'+self.r.params['url'])
            vot  = Table.read(self.r.params['url'])
            mURL = tempfile.mkdtemp()
            MSG("converting to GeoJSON")
            def getParts(sRegion):
                lon=sRegion.split(' ')[2:][0::2]
                lon=np.asarray([float(i) for i in lon])
                if (lon.max()-lon.min()) > 180:
                    lon = [[x, x-360][x>180] for x in lon]
                lat=sRegion.split(' ')[2:][1::2]
                parts = [[360-float(lon[i]),float(lat[i])] for i in range(len(lat))]
                if not (parts[0]==parts[-1]): parts.append(parts[0])
                return [parts]
            makeFeat      = lambda coords, props: {"type":"Feature","geometry": { "type": "Polygon", "coordinates": coords},"properties": props}
            makeMaskEmpty = lambda vot, rowN:     [str(q).replace('MASKED','') for q in vot[rowN]]
            makeComplFeat = lambda vot, rowN:     makeFeat( getParts(vot['s_region'][rowN]), dict(zip(vot.colnames, makeMaskEmpty(vot, rowN)))) 
            say('Number of features to write: '+ str(len(vot)) )
            featList=[]
            for i in range(len(vot)):
                self.MSG('writing number' + str(i))
                featList.append(makeComplFeat(vot, i))
            with open(mURL + '/vot.geojson', 'w') as f: f.write( geojson.dumps({"type":"FeatureCollection","features":featList} ))
            self.MSG('finished download, converting to SpatiaLite')
            vlayer = QgsVectorLayer(mURL + '/vot.geojson',"mygeojson","ogr")
            say("writing to SpatiaLite")
            QgsVectorFileWriter.writeAsVectorFormat(vlayer, mURL+r"/vot.sqlite","utf-8",None,"SpatiaLite")
            say("loading SpatiaLite")
            vlayer = QgsVectorLayer(                        mURL+r"/vot.sqlite",str(self.r.params['name']),"ogr")
            say("adding layer to canvas")
            self.addVLayerToCanvas(vlayer)
            say("done")
        mTypeDict['table.load.votable']=q; del q
        ### CASE END ###
        map(self.bindSamp, mTypeDict.keys())
        MSG("Disconnected")
        while self.connectionState:
            MSG("starting")
            self.r.received = False
            while not self.r.received and self.connectionState:
                MSG("waiting"); time.sleep(2)
            if self.connectionState:
                mTypeDict[self.r.mtype]()
                time.sleep(2)

    def addVLayerToCanvas(self,vlayer):
        self.iface.mapCanvas().freeze()
        QgsMapLayerRegistry.instance().addMapLayer(vlayer) # order is importaint here
        self.root.addLayer(vlayer)
        QgsMapLayerRegistry.instance().reloadAllLayers()
        self.iface.mapCanvas().freeze(False)

    def run(self):
        self.dlg.show()
        self.MSG("hello")
        result = self.dlg.exec_()
        if self.connectionState: self.cli.disconnect() # if user closes window - call disconnect to make sure
