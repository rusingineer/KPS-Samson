# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2021 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

import json
from urllib import unquote_plus
import urllib2

from PyQt4 import QtGui
from PyQt4.QtCore import QByteArray, QVariant

from library.pdf417 import pdf417image
from library.Barcodes.qrcode import qrcodeImage
from library.Barcodes.datamatrix import datamatrixImage


class CResourceLoaderMixin:

    def __init__(self):
        self.images = {}
        self.printData = {}


    def setCanvases(self, canvases):
        for key,  val in canvases.iteritems():
            self.images[key] = val.image
    
    def setPrintData(self, printData):
        self.printData = printData

    def getPrintData(self):
        return self.printData

    def loadResource(self, type_, url):
        def decode(s):
            return unquote_plus(str(s))

        if type_ == 2:
            if url.scheme() == 'pdf417':
                return self.__generateImage(pdf417image, url)
            if url.scheme() == 'qrcode':
                return self.__generateImage(qrcodeImage, url)
            if url.scheme() == 'datamatrix':
                return self.__generateImage(datamatrixImage, url)
            elif url.scheme() == 'canvas':
                canvasName = str(url.host())
                result = self.images.get(canvasName, None)
                if not result:
                    result = getEmptyImage()
                    self.images[canvasName] = result
                return QVariant(result)
            elif url.scheme() == 'data':
                # в старых версиях Qt нет обработки <img src="data:image/png;base64, ..." />
                # делаю это "вручную", это жрёт память и, возможно, тормозит
                encodedUrl = url.toEncoded()
                knownEncoding = 'data:image/png;base64,'
                if encodedUrl.startsWith(knownEncoding):
                    encodedImage = encodedUrl.right( encodedUrl.length()-len(knownEncoding) )
                    data = QByteArray.fromBase64(encodedImage)
                    image = QtGui.QImage()
                    if image.loadFromData(data):
                        return QVariant(image)
            elif url.scheme() == 'http':
                encodedUrl = unicode(url.toString())
                request = urllib2.Request(encodedUrl)
                resp = urllib2.urlopen(request)
                content = QByteArray(resp.read())
                img = QtGui.QImage()
                if img.loadFromData(content):
                    return QVariant(img)
        # fallback
        if hasattr(self, 'qtLoadResource'):
            return self.qtLoadResource(type_, url)
        return QVariant()


    def __generateImage(self, imageGenerator, url):
        try:
            params = dict((unquote_plus(str(key)),
                           json.loads(unquote_plus(str(value)))
                          )
                          for (key, value) in url.encodedQueryItems()
                         )
            image = imageGenerator(**params)
            return QVariant(image)
        except:
            QtGui.qApp.logCurrentException()
            return QVariant()


class CTextDocument(CResourceLoaderMixin, QtGui.QTextDocument):
    def __init__(self, parent=None):
        QtGui.QTextDocument.__init__(self, parent)
        CResourceLoaderMixin.__init__(self)

    def qtLoadResource(self, type_, url):
        return QtGui.QTextDocument.loadResource(self, type_, url)


def getEmptyImage():
    image = QtGui.QImage(16, 16, QtGui.QImage.Format_RGB32)
    painter = QtGui.QPainter(image)
    painter.fillRect(0, 0, 16, 16, QtGui.QBrush(QtGui.QColor(255, 255, 255)))
    painter.setPen(QtGui.QPen(QtGui.QColor(0, 255, 0)))
    painter.drawEllipse(0, 0, 15, 15)
    painter.setPen(QtGui.QPen(QtGui.QColor(255, 0, 0)))
    painter.drawLine(0,  0, 15, 15)
    painter.drawLine(0, 15, 15, 0)
    return image
