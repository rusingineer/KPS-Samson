# -*- coding: utf-8 -*-
import re

import grpc
import socket

from PyQt4 import QtGui

from Exchange.RISExchange.Protos import hl7server_pb2, hl7server_pb2_grpc
from library.Utils import forceString


class CBaseHl7Connect:
    def __init__(self):
        self.serviceName = ''
        self.url = ''

    def beforeInitConnection(self):
        self.validateUrl()

        err = CBaseHl7Connect.isHostAvailable(self.url)
        if isinstance(err, Exception):
            raise Exception("%s Can't connect to %s %s" % (self.serviceName, self.url, err.message))

    def validateUrl(self):
        if not re.match('^([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}:[0-9]{1,5})|(localhost:[0-9]{1,5})$',
                        self.url):
            raise Exception("%s Invalid URL (%s)" % (self.serviceName, self.url))

    @staticmethod
    def isHostAvailable(url, delay=1):
        ip, port = url.split(':')
        port = int(port)
        TCPsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        TCPsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        TCPsock.settimeout(delay)
        try:
            if str(ip) == 'localhost':
                ip = '127.0.0.1'
            TCPsock.connect((ip, port))
        except Exception as e:
            return e
        finally:
            TCPsock.close()


class CGRPCClient(CBaseHl7Connect):
    def __init__(self):
        CBaseHl7Connect.__init__(self)
        url, stubObject = self.getInitParams()
        self.url = url
        self.stubObject = stubObject
        self.serviceName = 'Hl7 gRPC Client'
        self.stub = None

    def connect(self):
        if not self.stub:
            channel = grpc.insecure_channel(self.url)
            self.stub = self.stubObject(channel)
        return self.stub

    def initConnection(self):
        self.beforeInitConnection()
        if not self.connect():
            raise Exception("%s Can't init connection to gRPC service %s" % (self.serviceName, self.url))

    def getInitParams(self):
        return forceString(QtGui.qApp.db.translate('GlobalPreferences', 'code', '23:RISExchangeUrl',
                                                   'value')), hl7server_pb2_grpc.CommunicationStub
        #test on mo
        # return "127.0.0.1:50052", hl7server_pb2_grpc.CommunicationStub

    def execCommand(self, command, messageId):
        stub = self.connect()
        try:
            stub.ExecCommand(hl7server_pb2.MessageRequest(command=command, messageID=messageId))
        except grpc.RpcError:
            raise Exception("%s (ExecCommand) RpcError on %s" % (self.serviceName, self.url))
        except Exception as e:
            return Exception(e.message)

    def newOrder(self, orderId):
        return self.execCommand("NW", orderId)

    def cancelOrder(self, orderId):
        return self.execCommand("CA", orderId)

    def updateOrder(self, orderId):
        return self.execCommand("XO", orderId)


class CMllpClient(CBaseHl7Connect):
    def __init__(self):
        CBaseHl7Connect.__init__(self)
        self.url = forceString(QtGui.qApp.db.translate('GlobalPreferences', 'code', '23:RISExchangeMllpUrl', 'value'))
        #test on mo
        # self.url = "127.0.0.1:8485"
        self.serviceName = 'Hl7 Mllp Client'

    def sendMessage(self, message):
        ip, port = self.url.split(':')
        port = int(port)
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((ip, port))
            # требуется экранирование амперсанта
            sock.sendall('\x0b' + message.replace("&", "\\&").encode('utf8') + '\r' + '\x1c\x0d\r')
        except Exception as e:
            return e
        finally:
            sock.close()
