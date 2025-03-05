# -*- coding: utf-8 -*-
import re

import grpc
import socket

from PyQt4 import QtGui

from Exchange.RISExchange.Protos import hl7server_pb2, hl7server_pb2_grpc
from library.Utils import forceString


class CgRPCClient:
    def __init__(self, url, stubObject):
        self.serviceName = 'gRPC Client'
        self.url = url
        self.stubObject = stubObject
        self.stub = None


    def connect(self):
        if not self.stub:
            channel = grpc.insecure_channel(self.url)
            self.stub = self.stubObject(channel)
        return self.stub

    def initConnection(self):
        self.validateUrl()

        err = CgRPCClient.isHostAvailable(self.url)
        if isinstance(err, Exception):
            raise Exception("%s Can't connect to %s %s" % (self.serviceName, self.url, err.message))
        if not self.connect():
            raise Exception("%s Can't init connection to gRPC service %s" % (self.serviceName, self.url))

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

class CHl7Client(CgRPCClient):
    def __init__(self):
        url, stubObject = self.getInitParams()
        CgRPCClient.__init__(self, url, stubObject)
        self.serviceName = 'Hl7 Client'

    def getInitParams(self):
        return forceString(QtGui.qApp.db.translate('GlobalPreferences', 'code', '23:RISExchangeUrl',
                                                   'value')), hl7server_pb2_grpc.CommunicationStub

    def execCommand(self, command, messageId):
        stub = self.connect()
        try:
            stub.ExecCommand(hl7server_pb2.MessageRequest(command=command, messageID=messageId))
        except grpc.RpcError:
            raise Exception("%s (ExecCommand) Can't connect to %s" % (self.serviceName, self.url))
        except Exception as e:
            raise Exception(e.message)

    def newOrder(self, orderId):
        return self.execCommand("NW", orderId)

    def cancelOrder(self, orderId):
        return self.execCommand("CA", orderId)

    def updateOrder(self, orderId):
        return self.execCommand("XO", orderId)
