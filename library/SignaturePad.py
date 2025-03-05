# -*- coding: utf-8 -*-
try:
    import hid
except:
    pass
import binascii

from library.Utils import anyToUnicode
from PyQt4.QtCore import pyqtSignal, QObject, QByteArray, QTimer

ReportSize = 512

class Language:
    Chinese = 0
    English = 1
    Clear = 2

class Command:
    SetLanguage = 0x81
    GetImageSize = 0xB1
    GetImageData = 0x13

class Message:
    ImageSize = 0xB0
    ConfirmSignature = 0x10

class ImageBuffer:
    def __init__(self, size):
        self.size = size
        self.buffer = bytearray()
    
    def add(self, report):
        remainingBytes = self.size - len(self.buffer)
        self.buffer += report[:remainingBytes]
    
    def isComplete(self):
        return len(self.buffer) >= self.size

class CSignaturePad(QObject):
    imageReceived = pyqtSignal(bytearray)

    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        self.device = None
        self.readTimer = QTimer(self)
        self.readTimer.timeout.connect(self.getMessage)
        self.reset()
        self.readTimer.start()
    
    def reset(self):
        self.readTimer.setInterval(2000)
        try:
            self.device = hid.Device(vid=0x0416, pid=0x5031)
            self.device.nonblocking = True
            self.receivingImageData = False
            self.imageBuffer = None
            self.readTimer.setInterval(10)
            return True
        except hid.HIDException as e:
            self.printErrorAndClose(e)
            return False
    
    def close(self):
        self.readTimer.stop()
        if self.device:
            try:
                self.device.close()
            except hid.HIDException as e:
                self.printErrorAndClose(e)
    
    def checkDevice(self):
        if self.device or self.reset():
            return True
        else:
            return False

    def printErrorAndClose(self, exception):
        print(u'Ошибка подключения к планшету: ' + anyToUnicode(exception))
        self.device = None
    
    def writeReport(self, report):
        if not self.checkDevice():
            return
        assert(len(report) == ReportSize)
        #print 'send: ', binascii.hexlify(report)
        data = b'0' + bytes(report)
        try:
            self.device.write(data)
        except hid.HIDException as e:
            self.printErrorAndClose(e)
    
    def readReport(self):
        if not self.checkDevice():
            return
        try:
            data = self.device.read(ReportSize)
            if not data:
                return None
            report = bytearray(data)
            #print 'get: ', binascii.hexlify(bytearray(report))
            assert(len(report) == ReportSize)
            return report
        except hid.HIDException as e:
            self.printErrorAndClose(e)
    
    def sendCommand(self, commandCode, param1, param2, param3, param4):
        report = bytearray(ReportSize)
        report[0] = 0xA4
        report[1] = commandCode
        report[2] = param1
        report[3] = param2
        report[4] = param3
        report[5] = param4
        report[6] = commandCode ^ param1 ^ param2 ^ param3  ^ param4
        report[7] = 0xB5
        self.writeReport(report)
    
    def getMessage(self):
        report = self.readReport()
        if not report:
            return
        if self.receivingImageData:
            self.imageBuffer.add(report)
            if self.imageBuffer.isComplete():
                self.imageReceived.emit(self.imageBuffer.buffer)
                self.receivingImageData = False
        else:
            messageCode, param1, param2, param3, param4 = report[1:6]
            if messageCode == Message.ImageSize:
                size = (param2 << 16) | (param3 << 8) | param4
                self.getImageData(size)

    def getImageData(self, size):
        self.receivingImageData = True
        self.imageBuffer = ImageBuffer(size)
        self.sendCommand(commandCode = Command.GetImageData, param1 = 0x11, param2 = 0x12, param3 = 0xAA, param4 = 0xAB)
    
    def setLanguage(self, language):
        self.sendCommand(commandCode = Command.SetLanguage, param1 = language, param2 = 0x12, param3 = 0xAA, param4 = 0xAB)
    
    def clearScreen(self):
        self.setLanguage(Language.Clear)
    
    def getImage(self):
        self.sendCommand(commandCode = Command.GetImageSize, param1 = 0x11, param2 = 0x12, param3 = 0xAA, param4 = 0xAB)


if __name__ == '__main__':
    import sys
    from PyQt4.QtGui import QApplication
    app = QApplication(sys.argv)
    def saveImage(imageData):
        with open("test.jpg", "wb") as file:
            file.write(imageData)
        app.exit(0)
    pad = CSignaturePad(app)
    #pad.setLanguage(Language.Clear)
    pad.imageReceived.connect(saveImage)
    pad.getImage()
    app.exec_()
    pad.close()
