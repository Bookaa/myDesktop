#!/usr/bin/python
from twisted.internet.protocol import Factory, Protocol
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from getIPAddr import getIP
use_pip_install_qt4reactor = True
if use_pip_install_qt4reactor:
    from qtreactor import pyqt4reactor
else:
    import qt4reactor
import myDesktopServerProtocol as serverProtocol
import os, sys
import input_event as input

app = QApplication(sys.argv)
if use_pip_install_qt4reactor:
    pyqt4reactor.install()
else:
    qt4reactor.install( )

class rdcProtocol(serverProtocol.RDCServerProtocol):
    """
    this class is inheritance from RDCServerProtocol,
    the class be responsible for achieve some of functions
    include (
    making screen pixel,
    execute:
    mouse event,
    keyboard event,
    copy text,
    send cut text ) etc...
    """
    def __init__(self):
        serverProtocol.RDCServerProtocol.__init__(self)
        self._clipboard = QApplication.clipboard( )
        self._maxWidth  = QApplication.desktop( ).size( ).width( ) 
        self._maxHeight = QApplication.desktop( ).size( ).height( )
        self.keyboard   = input.Keyboard( )
        self.mouse      = input.Mouse( )

        self.complete_no = -1
        self.his = []
        self.no = 0

        self.timer = QTimer()
        self.timer.timeout.connect(self.sendScreen)
        self.timer.start(300)

        self.lasttime = 0


    def sendScreen(self):
        tim1 = time.time()
        s = ''
        if self.lasttime != 0:
            s = 'timer %.2f' % (tim1 - self.lasttime)
        self.lasttime = tim1
        if self.his:
            no, img = self.his[-1]
            if no != self.complete_no:
                print(s, 'skip for not complete')
                return
        no, no2, framebuffer, width, height = self._makeFramebuffer()
        print(s, 'send buf len =', len(framebuffer), 'no = %d' % no, 'ref = %d' % no2)
        self.handleScreenUpdate(framebuffer=framebuffer, no=no, ref=no2, width=width, height=height)

    def handleKeyEvent(self, key, flag):
        print('get keyevent', key, flag)
        if flag == 6:
            self.keyboard.press(key)
        elif flag == 7:
            self.keyboard.release(key)

    def handleMouseEvent(self, x, y, buttonmask=0, flag=None):
        print(x, y, buttonmask, flag)
        if flag == 5:   # move mouse event 
            self.mouse.move(x, y)
        
        elif flag == 2: # mouse button down
            self.mouse.press(x, y, buttonmask)

        elif flag == 3: # mouse button up
            self.mouse.release(x, y, buttonmask)

        elif flag == 4: # mouse button duble clicked
            self.mouse.press(x, y, buttonmask)
            self.mouse.release(x, y, buttonmask)

    def handleClientCopyText(self, text):
        """
        copy text from client, and then set the text in clipboard
        """
        self._clipboard.setText(text)

    def cutTextToClient(self):
        """
        cut text to client
        """
        text = self._clipboard.text( )
        self.sendCutTextToClient(text)

    def getlastimg(self):
        if self.complete_no == -1:
            return None, -1
        while self.his:
            no, img = self.his[0]
            if no == self.complete_no:
                return img, self.complete_no

            self.his.pop(0)
        return None, -1

    def _makeFramebuffer(self):
        self.no = (self.no + 1) % 800
        no = self.no
        import zlib

        if no % 10 == 0:
            lastimg, no2 = None, -1
        else:
            lastimg, no2 = self.getlastimg()

        pix = QPixmap.grabWindow(QApplication.desktop( ).winId( ))
        img = pix.toImage()
        img2 = img.convertToFormat(QImage.Format_RGB888)
        width, height = img2.width(), img2.height()
        if lastimg is not None:
            assert img2.bytesPerLine() == img2.width() * 3
            assert (img2.width(), img2.height()) == (lastimg.width(), lastimg.height())
            pbuf1 = lastimg.bits().__int__()
            pbuf2 = img2.bits().__int__()

            # import hello
            # hello.imgsub(pbuf1, pbuf2, img2.width(), img2.height())

        bytes = img2.bits().asstring(img2.numBytes())
        data_s = zlib.compress(bytes)

        img = QImage(bytes, width, height, width * 3, QImage.Format_RGB888)
        assert (img2.width(), img2.height()) == (img.width(), img.height())

        if lastimg is not None:
            pbuf3 = img.bits().__int__()
            # hello.imgadd(pbuf1, pbuf3, width, height)

        self.his.append((no, img))

        if len(self.his) > 8:
            self.his.pop(0)

        return no, no2, data_s, width, height

    def doFramebufferUpdate(self, no):
        print('get complete no', no)
        self.complete_no = no
        if no == -1:
            self.his[:] = []


class RDCFactory(serverProtocol.RDCFactory):
    def __init__(self, password=None):
        serverProtocol.RDCFactory.__init__(self, password)
        self.protocol = rdcProtocol

    def buildProtocol(self, addr):
        return serverProtocol.RDCFactory.buildProtocol(self, addr)

    def readyConnection(self, server):
        self.server = server 


#-----------------------#
## myDesktopServer GUI ##
#-----------------------#
class RDCServerGUI(QDialog):
    """
    The PyRDCServerGUI responsible provide GUI interface, operate
    the PyRDCServer.
    """
    def __init__(self, reactor, parent=None):
        super(RDCServerGUI, self).__init__(parent)
        self.setupUI( )

        mainLayout = QGridLayout( )
        mainLayout.addWidget(self.groupbox,  0, 0)
        mainLayout.addWidget(self.hostLab,   1, 0)
        mainLayout.addLayout(self.butLayout, 2, 0)
        mainLayout.setMargin(10)
        self.setLayout(mainLayout)

        self.reactor    = reactor
        self.running    = False

        QObject.connect(self.startStopBut, SIGNAL('clicked( )'), self.onStartStop)
        QObject.connect(self.quitBut,      SIGNAL('clicked( )'), self.quit)

        self.setWindowFlags(Qt.WindowStaysOnTopHint)

    def setupUI(self):
        #self.resize(300, 200)
        self.setFixedSize(300, 200)
        self.setWindowTitle('PyRDCServer')

        # Setting style
        QApplication.setStyle(QStyleFactory.create('cleanlooks'))
        QApplication.setPalette(QApplication.style().standardPalette())
        self.setStyleSheet(open(os.path.dirname(os.path.realpath(__file__)) + '/styleSheet.qss', 'r').read( ))

        # Label
        self.hostLab  = QLabel('')

        self.groupbox = QGroupBox( )
        formLayout    = QFormLayout( )

        # LineEdit
        self.portEdit   = QLineEdit( )
        self.portEdit.setText('5000')
        self.addrEdit   = QLineEdit( )
        self.addrEdit.setText( getIP())
        self.addrEdit.setEnabled(False)
        self.passwdEdit = QLineEdit( )
        self.passwdEdit.setText('1234')
        formLayout.addRow(QLabel('Address'),  self.addrEdit)
        formLayout.addRow(QLabel('Port'),     self.portEdit)
        formLayout.addRow(QLabel('Password'), self.passwdEdit)
        self.groupbox.setLayout(formLayout)

        # Create Button
        self.butLayout     = QHBoxLayout( )
        self.startStopBut  = QPushButton('Start')
        self.quitBut       = QPushButton('Quit')
        self.butLayout.addWidget(self.startStopBut)
        self.butLayout.addWidget(self.quitBut)

    def onStartStop(self):
        if not self.running:
            self._start( )
        else:
            self._stop( )

    def _start(self):
        port = int(self.portEdit.text( ))
        pwd  = str(self.passwdEdit.text( ))
        self.startStopBut.setText('Close')
        if serverProtocol.flg_as_client:
            self.reactor.connectTCP('a.bookaa.com', 5519, RDCFactory(password=pwd))
        else:
            self.reactor.listenTCP(port, RDCFactory(password=pwd))
        self.running = True

    def _stop(self):
        self.startStopBut.setText('Start')
        self.reactor.stop( )
        self.running = False

    def quit(self):
        # call reactor of stop method
        self.reactor.stop( )
        # call QDialog of method to close the gui window
        self.close( )

    def closeEvent(self, event):
        self.quit( )

if __name__ == '__main__':
    from twisted.internet import reactor
    rdcServerGUI = RDCServerGUI(reactor)
    rdcServerGUI.show( )
    reactor.run( )
