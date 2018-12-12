#!/usr/bin/python
from twisted.internet.protocol import Protocol, Factory, ClientFactory
from twisted.python import log
from PyQt4.QtGui import *
from PyQt4.QtCore import *
import myDesktopClientProtocol as clientProtocol
use_pip_install_qt4reactor = True
if use_pip_install_qt4reactor:
    from qtreactor import pyqt4reactor
else:
    import qt4reactor
import os, sys

log.startLogging(sys.stdout)

app = QApplication(sys.argv)

__applib__  = os.path.dirname(os.path.realpath(__file__))
__appicon__ = os.path.dirname(os.path.realpath(__file__))

if use_pip_install_qt4reactor:
    pyqt4reactor.install()
else:
    qt4reactor.install( )

class RDCToGUI(clientProtocol.rdc):
    def __init__(self):
        clientProtocol.rdc.__init__(self)

    def connectionMade(self):
        self.factory.readyConnection(self)

    def vncRequestPassword(self):
        password = self.factory.password
        if not password:
            password = inputbox( )
        self.sendPassword(password)

    def commitFramebufferUpdate(self, framebuffer, no, ref, width, height):
        no = self.factory.display.updateFramebuffer(framebuffer, no, ref, width, height)
        self.framebufferUpdateRequest(no)


class RDCFactory(clientProtocol.RDCFactory):
    def __init__(self, display=None, password=None, shared=0):
        clientProtocol.RDCFactory.__init__(self, password, shared)
        self.display  = display
        self.protocol = RDCToGUI

    def buildProtocol(self, addr):
        return clientProtocol.RDCFactory.buildProtocol(self, addr)

    def readyConnection(self, client):
        self.display.readyDisplay(client)
        
    def clientConnectionFailed(self, connector, reason):
        log.msg("Client connection failed!. (%s)" % reason.getErrorMessage( ))
        reactor.stop( )

    def clientConnectionLost(self, connector, reason):
        log.msg("Client connection lost!. (%s)" % reason.getErrorMessage( ))
        reactor.stop( )


class Display(QWidget):
    """
    this class for display remoteframebuffer and get the client events
    and then send the events to server, the include keyEvent, pointerEvent,
    mouseMoveEvent, clipboardEvent.
    """
    def __init__(self, parent=None):
        super(Display, self).__init__(parent)
        self.resize(1390, 780)
        self._clipboard = QApplication.clipboard( )
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.clientProtocol = None
        self.parent = parent
        self.his = []

    def readyDisplay(self, protocol):
        self.clientProtocol = protocol

    def paintEvent(self, event):
        """
        paint frame buffer in widget
        """
        if self.his:
            no, img = self.his[-1]
            painter = QPainter(self)
            painter.drawImage(0, 0, img)

        self.update( )

    def updateFramebuffer(self, pixelmap, no, ref, width, height):
        import zlib
        bytes = zlib.decompress(pixelmap)
        img2 = QImage(bytes, width, height, width * 3, QImage.Format_RGB888)

        if ref == -1:
            print('gen img with no ref', no)
        else:
            img1 = None
            while self.his:
                no1, img = self.his[0]
                if no1 == ref:
                    img1 = img
                    break
                self.his.pop(0)
            if img1 is None:
                print('fail to find ref', no)
                self.his[:] = 0
                return -1
            assert img2.bytesPerLine() == img2.width() * 3
            assert (img2.width(), img2.height()) == (img1.width(), img1.height())

            pbuf1 = img1.bits().__int__()
            pbuf2 = img2.bits().__int__()

            #import hello
            #hello.imgadd(pbuf1, pbuf2, img2.width(), img2.height())
            #print('img ref success', no, ref)

        self.his.append((no, img2))
        if len(self.his) > 8:
            self.his.pop(0)
        return no

    def keyPressEvent(self, event):
        key  = event.key( )
        flag = event.type( )
        print('key press %x=%d' % (key, key), flag) # flag = 6
        if self.clientProtocol is None: return
        self.clientProtocol.keyEvent(key, flag)
        self.update( )

    def keyReleaseEvent(self, event):
        key  = event.key( )
        flag = event.type( )
        print('key release %x=%d' % (key, key), flag) # flag = 7
        if self.clientProtocol is None: return
        self.clientProtocol.keyEvent(key, flag)
        self.update( )

    def mousePressEvent(self, event):
        x, y   = (event.pos( ).x( ), event.pos( ).y( ))

        print('mouse press', self.width, self.height, self.size())
        width = self.width # * 4 / 5
        height = self.height # * 4 / 5
        width -= width % 8
        height -= height % 8

        if x >= width or y >= height:
            return

        button = event.button( )
        print('mouse button', button)
        flag   = event.type( )
        if self.clientProtocol is None: return #self.clientProtocol = self.parent.client.clientProto
        self.clientProtocol.pointerEvent(x, y, button, flag)
        print(self.clientProtocol.pointerEvent)

    def mouseReleaseEvent(self, event):
        x, y   = (event.pos( ).x( ), event.pos( ).y( ))

        width = self.width # * 4 / 5
        height = self.height # * 4 / 5
        width -= width % 8
        height -= height % 8

        if x >= width or y >= height:
            return

        button = event.button( )
        flag   = event.type( )
        if self.clientProtocol is None: return #self.clientProtocol = self.parent.client.clientProto
        self.clientProtocol.pointerEvent(x, y, button, flag)

    def mouseMoveEvent(self,  event):
        x, y   = (event.pos( ).x( ), event.pos( ).y( ))

        width = self.width # * 4 / 5
        height = self.height # * 4 / 5
        width -= width % 8
        height -= height % 8

        if x >= width or y >= height:
            return

        button = event.button( )
        flag   = event.type( )
        if self.clientProtocol is None: return #self.clientProtocol = self.parent.client.clientProto
        self.clientProtocol.pointerEvent(x, y, button, flag)

    def resizeEvent(self, event):
        """
        the remote framebuffer's size is according the client viewer size
        this may reduce the size of the images can be
        """
        size = event.size( )
        self.width, self.height = (size.width(), size.height())


class myDesktopViewer(QMainWindow):
    def __init__(self,  parent=None):
        super(myDesktopViewer, self).__init__(parent)
        self.display = Display(self)
        self.setupUI( )

    def setupUI(self):
        self.setWindowTitle('myDesktop (viewer)')
        self.resize(800, 600)
        QApplication.setStyle(QStyleFactory.create('cleanlooks'))
        QApplication.setPalette(QApplication.style( ).standardPalette())

        # add adction on application
        self.startAction = QAction(QIcon(os.path.join(__appicon__, 'icons', 'Start.png')), 'Start', self)
        self.stopAction  = QAction(QIcon(os.path.join(__appicon__, 'icons', 'Stop.png')),  'Stop',  self)
        self.startAction.setToolTip('Start connection')
        self.stopAction.setToolTip('Stop connection')
        self.startAction.triggered.connect(self.connectionStart)
        self.stopAction.triggered.connect(self.connectionStop)

        # add a toolbar
        self.toolbar = self.addToolBar('')
        self.toolbar.addAction(self.stopAction)
        self.toolbar.addAction(self.startAction)

        displayWidget = QWidget( )
        vbox   = QVBoxLayout(displayWidget)
        vbox.addWidget(self.display)
        vbox.setMargin(0)
        self.setCentralWidget(displayWidget)

    def connectionStart(self):
        client = RDCFactory(display=self.display, password='1234')
        reactor.connectTCP('127.0.0.1', 5000, client)
        #reactor.connectTCP('192.168.0.101', 5000, client)

    def connectionStop(self):
        reactor.stop( )

    def closeEvent(self, event):
        self.connectionStop( )
        exit( )

if __name__ == '__main__':
    from twisted.internet import reactor
    mydesktop = myDesktopViewer( )
    mydesktop.show( )
    reactor.run( ) # enter mainloop
