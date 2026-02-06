# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2018-2026 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################
##
## Обнаружено, что разные платформы и разрые версии питона имеют
## серьёзные различия в реализации httplib.HTTPSConnection,
## поэтому проще завести свою реализацию чем настраивать существующую :(
##
## Плюс к этому обнаружено, что несмотря на то, что в стандартной библиотеке
## есть logger, ни ZSI ни httplib.HTTPConnection его не используют,
## а тупо гонят вывод в файлы.
##
## При этом ZSI не выводит всей интересующей информации,
## (url, заголовки http) зато выводит в произвольный файл
## тогда как httplib.HTTPConnection выводит заголовки и запрос - не не ответ
## да и выводит в sys.stdout :(
##
#############################################################################

import base64
import logging
import httplib
import ssl


def getConnectionClass(url):
    if url.lower().startswith('http://'):
        return CHttpConnection
    if url.lower().startswith('https://'):
        return CHttpsConnection
    return None


class CHttpConnection(httplib.HTTPConnection):
    def __init__(self, host, port=None, proxy={}):
        if ':' in host:
            host, portAsStr = host.split(':',1)
            if port is None:
                port = int(portAsStr)
        proxyAddress  = proxy.get('address', None)
        proxyPort     = proxy.get('port', None)
        proxyLogin    = proxy.get('login', None)
        proxyPassword = proxy.get('password', None) or ''
        if proxyAddress and proxyPort:
            httplib.HTTPConnection.__init__(self, proxyAddress, port=proxyPort)
            headers = {}
            if proxyLogin:
                headers['Proxy-Authorization'] = 'Basic ' + base64.b64encode('%s:%s' % (proxyLogin, proxyPassword))
            self.set_tunnel(host, port or self.default_port, headers)
        else:
            httplib.HTTPConnection.__init__(self, host, port=port or self.default_port)
        self.logger = logging.getLogger('soap')
        self.auto_open = False #


    def connect(self):
        try:
            self.logger.info('connect: %s:%s', self.host, self.port)
        except UnicodeDecodeError:
            pass
        httplib.HTTPConnection.connect(self)


    def send(self, data):
        try:
            self.logger.info('send: %s', data)
        except UnicodeDecodeError:
            pass
        httplib.HTTPConnection.send(self, data)


    def getresponse(self):
        result = httplib.HTTPConnection.getresponse(self)
        try:
            self.logger.info('resp: %s %s\n%s', result.status, result.reason, result.msg)
        except UnicodeDecodeError:
            pass
        origRead = result.read
        result.read = lambda amt=None: self.__read(origRead, amt)
        return result


    def __read(self, origRead, amt):
        result = origRead(amt)
        try:
            self.logger.info('read: %s', result)
        except UnicodeDecodeError:
            pass
        return result


class CHttpsConnection(httplib.HTTPSConnection):

    def __init__(self, host, port=None, proxy={}):
        if ':' in host:
            host, portAsStr = host.split(':',1)
            if port is None:
                port = int(portAsStr)
        proxyAddress  = proxy.get('address', None)
        proxyPort     = proxy.get('port', None)
        proxyLogin    = proxy.get('login', None)
        proxyPassword = proxy.get('password', None) or ''
        context       = ssl.create_default_context()
        context.check_hostname = False # запрещаем проверки сертификатов
        context.verify_mode = ssl.CERT_NONE # запрещаем проверки сертификатов
        if proxyAddress and proxyPort:
            httplib.HTTPSConnection.__init__(self, proxyAddress, port=proxyPort, context=context)
            headers = {}
            if proxyLogin:
                headers['Proxy-Authorization'] = 'Basic ' + base64.b64encode('%s:%s' % (proxyLogin, proxyPassword))
            self.set_tunnel(host, port or self.default_port, headers)
        else:
            httplib.HTTPSConnection.__init__(self, host, port=port or self.default_port, context=context)
        self.logger = logging.getLogger('soap')
        self.auto_open = False


    def connect(self):
        try:
            self.logger.info('connect: %s:%s', self.host, self.port)
        except UnicodeDecodeError:
            pass
        httplib.HTTPSConnection.connect(self)


    def send(self, data):
        try:
            self.logger.info('send: %s', data)
        except UnicodeDecodeError:
            pass
        httplib.HTTPSConnection.send(self, data)


    def getresponse(self):
        result = httplib.HTTPSConnection.getresponse(self)
        try:
            self.logger.info('resp: %s %s\n%s', result.status, result.reason, result.msg)
        except UnicodeDecodeError:
            pass
        origRead = result.read

        result.read = lambda amt=None: self.__read(origRead, amt)
        return result


    def __read(self, origRead, amt):
        result = origRead(amt)
        try:
            self.logger.info('read: %s', result)
        except UnicodeDecodeError:
            pass
        return result
