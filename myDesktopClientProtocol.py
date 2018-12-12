#!/usr/bin/python
"""
This is RDC(Remote Desktop Control) protocol
"""
from twisted.internet.protocol import Protocol, Factory, ClientFactory 
from twisted.python import log
from message_defines import messageTypes as msgTypes
import os, sys, json
import time


class rdc(Protocol): 
    def __init__(self): 
        self._packet       = ""

    def _doClientInitialization(self):
        self.framebufferUpdateRequest(-1)

    def dataReceived(self, data):
        self._packet += data

        while True:
            pos = self._packet.find('@')
            if pos == -1:
                break
            head, buf = self._packet[:pos], self._packet[pos+1:]
            assert head.startswith('A_')
            _, s1, s2 = head.split('_')
            key = int(s1); _expected_len = int(s2)
            if len(buf) < _expected_len:
                break
            s3, s4 = buf[:_expected_len], buf[_expected_len:]
            self._packet = s4

            if key == msgTypes.FRAME_UPDATE:
                pos = s3.find('@')
                assert pos != -1
                s5, s6 = s3[:pos], s3[pos+1:]
                args = json.loads(s5)
                args['framebuffer'] = s6
            else:
                args = json.loads(s3)
            self.handler(key, args)

    def _pack(self, key_, **kw):
        s = json.dumps(kw)
        message_len = len(s)
        return "B_%s_%s" % (key_, message_len) + '@' + s

    def handler(self, option, args): 
        #log.msg('handler')
        if option == msgTypes.AUTHENTICATION:
            print('Auth   ', args)
            self._handleAuth(**args)

        elif option == msgTypes.FRAME_UPDATE:
            self.commitFramebufferUpdate(**args)

        elif option == msgTypes.COPY_TEXT:
            self.handleCopyText(**args)

        elif option == msgTypes.CUT_TEXT:
            self._handleServerCutText(**args)

        elif option == msgTypes.TEXT_MESSAGE: 
            self.handleServerTextMessage(**args)

        elif option == msgTypes.AUTH_RESULT:
            self._handleVNCAuthResult(**args)

    #--------------------------#
    ## Handle server messages ##
    #--------------------------#
    def _handleAuth(self, block): 
        if block == 0:  # fail
            pass 

        elif block == 1:
            self._doClientInitialization( )

        elif block == 2:
            self._handleVNCAuth( )

    def _handleVNCAuth(self): 
        self.vncRequestPassword( )

    def _handleVNCAuthResult(self, block): 
        if block == 0:   # OK 
            self._doClientInitialization( )

        elif block == 1: # Failed
            self.vncAuthFailed("autenthication failed")
            #self.transport.loseConnection( )

        elif block == 2: # Too many
            self.vncAuthFailed("too many tries to log in")
            self.transport.loseConnection( )
        
        else:
            log.msg("unknown auth response (%d)\n" % auth)

    def vncAuthFailed(self, reason):
        log.msg('Cannot connect: %s' % reason) 

    #-----------------------------#
    ## Client >> Server messages ##
    #-----------------------------#
    def framebufferUpdateRequest(self, no):
        s = self._pack(msgTypes.FRAME_UPDATE, no=no)
        print('send complete', s)
        self.transport.write(s)
        
    def keyEvent(self, key, flag):
        self.transport.write(self._pack(msgTypes.KEY_EVENT, key=key, flag=flag))

    def pointerEvent(self, x, y, buttonmask, flag=None):
        self.transport.write(self._pack(msgTypes.POINTER_EVENT, x=x, y=y, buttonmask=buttonmask, flag=flag))

    def clientCutText(self, text): 
        log.msg("clientCutText; text=%s" % (text))
        self.transport.write(self._pack(msgTypes.CUT_TEXT, text=text))

    def sendPassword(self, password):
        self.transport.write(self._pack(msgTypes.AUTHENTICATION, client_password=password))

    #----------------------------#
    ## Overiding on application ##
    #----------------------------#
    def commitFramebufferUpdate(self, framebuffer, no, ref, width, height):
        pass

class RDCFactory(ClientFactory):
    protocol = rdc
    def __init__(self, password=None, shared=0):
        self.password = password
        self.shared   = shared
