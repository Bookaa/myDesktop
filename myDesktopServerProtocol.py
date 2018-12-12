#!/usr/bin/python
from twisted.internet.protocol import Protocol, Factory, ClientFactory
from twisted.python import log
from message_defines import messageTypes as msgTypes
import sys, json
log.startLogging(sys.stdout)

flg_as_client = False

class RDCServerProtocol(Protocol):
    def __init__(self):
        self._packet       = ""
        self.state   = "UNREGISTERED"

    def dataReceived(self, data):
        self._packet += data

        while True:
            pos = self._packet.find('@')
            if pos == -1:
                break
            head, buf = self._packet[:pos], self._packet[pos+1:]
            assert head.startswith('B_')
            _, s1, s2 = head.split('_')
            key = int(s1); _expected_len = int(s2)
            if len(buf) < _expected_len:
                break
            s3, s4 = buf[:_expected_len], buf[_expected_len:]
            self._packet = s4

            args = json.loads(s3)
            self.handler(key, args)

    def handler(self, option, args):
        #log.msg('handler')
        if option == msgTypes.AUTHENTICATION:
            self._handleClientAuth(**args)

        elif option == msgTypes.INITIALIZATION: 
            self.serverInitialization( )

        elif option == msgTypes.FRAME_UPDATE:
            self.doFramebufferUpdate(**args)

        elif option == msgTypes.KEY_EVENT:
            self.doKeyEvent(**args)

        elif option == msgTypes.POINTER_EVENT:
            self.doPointerEvent(**args)

        elif option == msgTypes.COPY_TEXT:
            self.doCopyText( )

        elif option == msgTypes.CUT_TEXT:
            self.doClientCutText( )

    def serverInitialization(self):
        pass

    def handleScreenUpdate(self, **args):
        self.transport.write(self._pack(msgTypes.FRAME_UPDATE, **args))

    def connectionMade(self):
        log.msg('connectionMade')
        if not self.factory.password:
            self.state = 'REGISTERED'
            self.transport.write(self._pack(msgTypes.AUTHENTICATION, block=1))
        else: 
            self.transport.write(self._pack(msgTypes.AUTHENTICATION, block=2))
        #self.readyConnection(self)

    def _handleClientAuth(self, client_password):
        log.msg('_handleClientAuth')
        if self.factory.password == str(client_password):
            self.state = 'REGISTERED'
            self.transport.write(self._pack(msgTypes.AUTH_RESULT, block=0))

        elif self.factory.password != str(client_password):
            self.transport.write(self._pack(msgTypes.AUTH_RESULT, block=1))

        elif self._logTimes >= self.logMaxTimes: 
            self.transport.write(self._pack(msgTypes.AUTH_RESULT, block=2))

    def _pack(self, key, **kw):
        if key == msgTypes.FRAME_UPDATE:
            framebuffer = kw['framebuffer']
            del kw['framebuffer']
            message = json.dumps(kw)
            message_len = len(message) + 1 + len(framebuffer)
            message = "A_%s_%s" % (key, message_len) + '@' + message + '@' + framebuffer
            return message
        message = json.dumps(kw)
        message_len = len(message)
        message = "A_%s_%s" % (key, message_len) + '@' + message
        return message

    def doKeyEvent(self, key, flag=1):
        self.handleKeyEvent(key, flag)

    def doPointerEvent(self, x, y, buttonmask, flag): 
        self.handleMouseEvent(x, y, buttonmask, flag)

    def doCopyTextFromClient(self, text):
        """
        copy text from text
        """ 
        self.handleClientCopyText(text)

    #----------------------------#
    ## Server >> Client message ##
    #----------------------------#
    def sendCutTextToClient(self, text):
        """
        get server cut text to client
        """
        self.transport(self._pack(msgTypes.CUT_TEXT, text=text))
        
if flg_as_client:
    class RDCFactory(ClientFactory):
        protocol = RDCServerProtocol
        def __init__(self, password=None):
            self.password = password
else:
    class RDCFactory(Factory):
        protocol = RDCServerProtocol
        def __init__(self, password=None):
            self.password = password
