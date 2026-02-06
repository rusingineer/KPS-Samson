# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2025 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QEvent, QModelIndex, QVariant, QString, QAbstractTableModel

from library.Utils import forceString, trim


class CStandardItemModel(QtGui.QStandardItemModel):
    def __init__(self, parent = None):
        QtGui.QStandardItemModel.__init__(self)
        self._readOnly = False


    def setReadOnly(self, value=False):
        self._readOnly = value


    def isReadOnly(self):
        return self._readOnly


    def flags(self, index=QModelIndex()):
        result = QtGui.QStandardItemModel.flags(self, index)
        if self._readOnly:
            result = Qt.ItemIsEnabled
        return result


class CStandardItemModelEx(QAbstractTableModel):
    def __init__(self, parent = None):
        QAbstractTableModel.__init__(self, parent)
        self._readOnly = False


    def setReadOnly(self, value=False):
        self._readOnly = value


    def isReadOnly(self):
        return self._readOnly


    def flags(self, index=QModelIndex()):
        result = QAbstractTableModel.flags(self, index)
        if self._readOnly:
            result = Qt.ItemIsEnabled
        return result


class CROComboBox(QtGui.QComboBox):
    u"""ComboBox с ReadOnly"""

    def __init__(self, parent):
        QtGui.QComboBox.__init__(self, parent)
        self._model = CStandardItemModel(self)
        self.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToMinimumContentsLength)
        self.setModel(self._model)
        self.readOnly = False
        self.isWheel = True
        self.installEventFilter(self)


    def setWheel(self, value=False):
        self.isWheel = value


    def setReadOnly(self, value=False):
        self.readOnly = value
        self.model().setReadOnly(self.readOnly)


    def isReadOnly(self):
        return self.readOnly


    def showPopup(self):
        if not self.isReadOnly():
            QtGui.QComboBox.showPopup(self)


    def event(self, event):
        if event.type() == QEvent.KeyPress:
            if self.model().isReadOnly():
                event.accept()
                return False
        elif event.type() == QEvent.Wheel: # QWheelEvent
            if not self.isWheel:
                event.ignore() 
                return False
        return QtGui.QComboBox.event(self, event)


    def keyPressEvent(self, event):
        if self.model().isReadOnly():
            event.accept()
        else:
            key = event.key()
            if key in (Qt.Key_Delete, Qt.Key_Backspace):
                self.setCurrentIndex(-1)
                event.accept()
            else:
                QtGui.QComboBox.keyPressEvent(self, event)


    def eventFilter(self, watched, event):
        if self.model().isReadOnly():
            event.accept()
            return False
        return QtGui.QComboBox.eventFilter(self, watched, event)


class CEnumComboBox(CROComboBox):
    u"""Вариант комбо-бокса, значения которого хранятся в userData"""
    # Задуман как база для разных статусов и т.п.,
    # Когда номер выбранного элемента может быть уже неудобен.

    def addItem(self, name, value):
        CROComboBox.addItem(self, name, QVariant(value))


    def insertItem(self, idx, name, value):
        CROComboBox.insertItem(self, idx, name, QVariant(value))


    # для совместимости?
    def insertSpecialValue(self, name, value, idx=0):
        self.insertItem(idx, name, value)


    def setValue(self, value):
        idx = self.findData(QVariant(value))
        if idx >= 0:
            self.setCurrentIndex(idx)


    def value(self):
        idx = self.currentIndex()
        return self.itemData(idx).toPyObject()


class CROEditableComboBox(CROComboBox):
    __pyqtSignals__ = ('textChanged(QString)',
                       'textEdited(QString)'
                      )

    def __init__(self, parent = None):
        CROComboBox.__init__(self, parent)
        self.setEditable(True)
        self.lineEdit().setReadOnly(False)
        self._popup = None
        self.value = None


    def setValue(self, value):
        self.value = value
        self.setEditText(forceString(self.value))


    def value(self):
        return self.value


    def setText(self, text):
        self.lineEdit().setText(text)


    def setCursorPosition(self, position):
        self.lineEdit().setCursorPosition(position)


    def text(self):
        return self.lineEdit().text()


    def eventFilter(self, watched, event):
        if self.model().isReadOnly():
            event.accept()
            return False
        if event.type() == QEvent.KeyPress:
            if  event.key() == Qt.Key_Tab:
                self.editor.keyPressEvent(event)
                return True
        return QtGui.QComboBox.eventFilter(self, watched, event)


    def keyPressEvent(self, event):
        if self.model().isReadOnly():
            event.accept()
        else:
            key = event.key()
            if key == Qt.Key_Tab or key == Qt.Key_Backtab:
                self.setValue(forceString(self.text()))
                event.accept()
            elif key == Qt.Key_Delete:
                self.setValue(None)
                event.accept()
            elif key == Qt.Key_Backspace: # BS
                text = QString(self.text())
                if trim(text):
                    newText = text
                    selectedText = self.lineEdit().selectedText()
                    selectedTextCount = len(selectedText)
                    cursorPositionEdit = self.lineEdit().cursorPosition()
                    cursorPosition = cursorPositionEdit-(1 if (cursorPositionEdit > 0 or not selectedTextCount) else 0)
                    cursorPositionNew = cursorPosition
                    if cursorPosition >= 0:
                        if selectedTextCount >= len(text):
                            newText = u''
                            cursorPositionNew = 0
                        elif selectedTextCount > 0:
                            if text.mid(cursorPosition+1, selectedTextCount) == selectedText:
                                newText = text.remove(cursorPosition+1, selectedTextCount)
                                cursorPositionNew = cursorPosition+1
                            else:
                                newText = text.remove(cursorPosition+1-selectedTextCount, selectedTextCount)
                                cursorPositionNew = cursorPosition+1-selectedTextCount
                        else:
                            newText = text.remove(cursorPosition if cursorPosition < len(text) else (len(text)-1), 1)
                            cursorPositionNew = cursorPosition
                    self.setValue(newText)
                    self.lineEdit().setCursorPosition(cursorPositionNew)
                event.accept()
            else:
                CROComboBox.keyPressEvent(self, event)

