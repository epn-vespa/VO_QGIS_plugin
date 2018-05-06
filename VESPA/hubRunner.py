from PyQt4 import QtGui, QtCore
import resources
import threading
import sys
import os
#from astropy.samp import SAMPHubServer
#from astropy.samp.hub import WebProfileDialog
try:
    from astropy.samp import SAMPHubServer
    from astropy.samp.hub import WebProfileDialog
except ImportError:
    from astropy.vo.samp import SAMPHubServer
    from astropy.vo.samp.hub import WebProfileDialog
import threading
import time
from qgis.core    import QgsProject, QgsMessageLog

say= QgsMessageLog.logMessage

#class HUBrunner():
class HubRunner():
    def __init__(self, iface,pinstance):
        self.iface = iface
        self.pinstance = pinstance
    def run(self):
#        QgsMessageLog.logMessage('testerSH run', 'startSampHub')
        self.dlg = QtSampWidget()
        self.dlg.show()

class Communicate(QtCore.QObject):
    M = QtCore.pyqtSignal()

class QtWebProfileDialog(WebProfileDialog):
    def __init__(self,c):
        self.c=c
        self.running = True
        t=threading.Thread(target=self.wait_for_dialog)
        t.daemon=True
        t.start()
        say('QtWebProfileDialog init')
    def wait_for_dialog(self):
        say('Hello')
        while self.running:
#            say('QtWebProfileDialog wait_for_dialog')
            self.handle_queue()
            time.sleep(2)
    def show_dialog(self, samp_name, details, client, origin):
        say('QtWebProfileDialog show_dialog')
        self.samp_name = samp_name
        self.details   = details
        self.client    = client
        self.origin    = origin
        self.c.M.emit()

class HubMaster():
    def __init__(self,WPD):
        self.WPD = WPD
        self.isOpen=False
    def work(self):
        def runSampHub():
            self.h = SAMPHubServer(web_profile_dialog=self.WPD)
            self.isOpen=True
            self.h.start()
            say('samp hub started')
            while self.isOpen: 
#                say('samp hub running')
                time.sleep(1)
            self.h.stop()
            say('samp hub stopped')
        t=threading.Thread(target=runSampHub)
        t.daemon=True
        t.start()

class QtSampWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        self.SampMESSAGE = "A Web application which declares to be\n\nName: {name}\n"+\
            "Origin: {origin}\n\nis requesting to be registered with the SAMP Hub.  "+\
            "Pay attention\nthat if you permit its registration, "+\
            "such application will acquire\nall current user privileges, like file "+\
            "read/write.\n\nDo you give your consent?"
        super(QtSampWidget, self).__init__(parent)
#        self.setWindowIcon(QtGui.QIcon('web.png')) ## <= MM: What is this??
        self.setWindowIcon(QtGui.QIcon('iconVESPA.png'))
        self.initUI()
        self.setGeometry(300,300, 290,150)
        self.setWindowTitle('SAMP Root window')
        self.show()
    def initUI(self):
        self.lbl = QtGui.QLabel("HUB root window. \n Close this terminates \n SAMP Hub Server", self)
        self.lbl.move(20,20)
        self.c=Communicate()
        self.c.M.connect(self.showDialog)
        self.WPD = QtWebProfileDialog(self.c)
        self.mymaster=HubMaster(self.WPD)
        self.mymaster.work()
    def showDialog(self):
        text = self.SampMESSAGE.format(name=self.WPD.samp_name, origin=self.WPD.origin)
        reply = QtGui.QMessageBox.question(self, 'Continue?', text, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
        if reply == QtGui.QMessageBox.Yes: 
            print('accepted')
            self.WPD.consent()
        else: 
            print('rejected')
            self.WPD.reject()
    def closeEvent(self,event):
        self.mymaster.isOpen = False
        self.mymaster.h.stop()
        self.WPD.running = False
        say('dialog closed')



