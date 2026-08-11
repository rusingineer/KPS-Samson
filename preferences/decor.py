# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2023 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################
##
## Настройки внешнего вида
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, pyqtSignature

from Ui_decor import Ui_decorDialog


class CDecorDialog(QtGui.QDialog, Ui_decorDialog):
    def __init__(self, parent):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.cmbStyle.insertItems(0, QtGui.QStyleFactory.keys())
        self.cmbFont.setWritingSystem(QtGui.QFontDatabase.Cyrillic)
        self._propertyColor = QtGui.QColor(255, 255, 127)
        self.btnPropertyColor.setStyleSheet('background-color: #FFFF7F;')
        self._propertyColorTest = QtGui.QColor(255, 94, 94)
        self.btnPropertyColorTest.setStyleSheet('background-color: #FF5E5E;')


    def setStyle(self, style):
        index = self.cmbStyle.findText(style, Qt.MatchFixedString)
        if index < 0:
            index = 0
        self.cmbStyle.setCurrentIndex(index)


    def setStandardPalette(self, standardPalette):
        self.chkStandartPalette.setChecked(standardPalette)


    def setMaximizeMainWindow(self, maximizeMainWindow):
        self.chkMaximizeMainWindow.setChecked(maximizeMainWindow)


    def setFullScreenMainWindow(self, fullScreenMainWindow):
        self.chkFullScreenMainWindow.setChecked(fullScreenMainWindow)


    def setUseCustomFont(self, useCustomFont):
        self.chkUseCustomFont.setChecked(useCustomFont)


    def setFont(self, font):
        self.cmbFont.setCurrentFont(font)
        self.edtFontSize.setValue(font.pointSize())


    def setPropertyColor(self, colorHex):
        if not colorHex:
            self.chkPropertyColor.setChecked(False)
        else:
            self.chkPropertyColor.setChecked(True)
            self._propertyColor = QtGui.QColor(colorHex)
            self.btnPropertyColor.setStyleSheet('background-color: %s;' % colorHex)


    def setPropertyColorTest(self, colorHex):
        if not colorHex:
            self.chkPropertyColorTest.setChecked(False)
        else:
            self.chkPropertyColorTest.setChecked(True)
            self._propertyColorTest = QtGui.QColor(colorHex)
            self.btnPropertyColorTest.setStyleSheet('background-color: %s;' % colorHex)


    def style(self):
        return str(self.cmbStyle.currentText())


    def standardPalette(self):
        return self.chkStandartPalette.isChecked()


    def maximizeMainWindow(self):
        return self.chkMaximizeMainWindow.isChecked()


    def fullScreenMainWindow(self):
        return self.chkFullScreenMainWindow.isChecked()


    def useCustomFont(self):
        return self.chkUseCustomFont.isChecked()


    def font(self):
        result = QtGui.QFont(self.cmbFont.currentFont()) 
        result.setPointSize(self.edtFontSize.value())
        return result


    def propertyColor(self):
        if self.chkPropertyColor.isChecked():
            r = int(self._propertyColor.red()) & 0xFF
            g = int(self._propertyColor.green()) & 0xFF
            b = int(self._propertyColor.blue()) & 0xFF
            return u'#%02X%02X%02X' % (r, g, b)
        return u''


    @pyqtSignature('')
    def on_btnPropertyColor_clicked(self):
        dialog = QtGui.QColorDialog(self)
        dialog.setOptions(QtGui.QColorDialog.DontUseNativeDialog)
        dialog.setCurrentColor(self._propertyColor)
        if dialog.exec_():
            self._propertyColor = dialog.currentColor()
            r = int(self._propertyColor.red()) & 0xFF
            g = int(self._propertyColor.green()) & 0xFF
            b = int(self._propertyColor.blue()) & 0xFF
            colorHex = u'#%02X%02X%02X' % (r, g, b)
            self.btnPropertyColor.setStyleSheet('background-color: %s;' % colorHex)


    def propertyColorTest(self):
        if self.chkPropertyColorTest.isChecked():
            r = int(self._propertyColorTest.red()) & 0xFF
            g = int(self._propertyColorTest.green()) & 0xFF
            b = int(self._propertyColorTest.blue()) & 0xFF
            return u'#%02X%02X%02X' % (r, g, b)
        return u''


    @pyqtSignature('')
    def on_btnPropertyColorTest_clicked(self):
        dialog = QtGui.QColorDialog(self)
        dialog.setOptions(QtGui.QColorDialog.DontUseNativeDialog)
        dialog.setCurrentColor(self._propertyColorTest)
        if dialog.exec_():
            self._propertyColorTest = dialog.currentColor()
            r = int(self._propertyColorTest.red()) & 0xFF
            g = int(self._propertyColorTest.green()) & 0xFF
            b = int(self._propertyColorTest.blue()) & 0xFF
            colorHex = u'#%02X%02X%02X' % (r, g, b)
            self.btnPropertyColorTest.setStyleSheet('background-color: %s;' % colorHex)
