# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2019 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import SIGNAL

from ICDTree import CICDTreePopup
from library.ROComboBox import CROComboBox

# u"""Редакторы для кодов МКБ"""


rus = u'йцукенгшщзхъфывапролджэячсмитьбюё'
eng = u'qwertyuiop[]asdfghjkl;\'zxcvbnm,.`'
r2e = {}
e2r = {}
for i in range(len(rus)):
    r2e[rus[i]] = eng[i]
    e2r[eng[i]] = rus[i]


class CICDCodeEdit(QtGui.QLineEdit):
    u"""Редактор кодов МКБ"""

    def __init__(self, parent):
        QtGui.QLineEdit.__init__(self, parent)
        self.setInputMask('A99.Xn;_')


    def keyPressEvent(self, event):
        chr = unicode(event.text()).lower()
        if r2e.has_key(chr):
            engChr = r2e[chr].upper()
            myEvent = QtGui.QKeyEvent(event.type(), ord(engChr), event.modifiers(), engChr, event.isAutoRepeat(), event.count())
            QtGui.QLineEdit.keyPressEvent(self, myEvent)
        elif e2r.has_key(chr):
            engChr = chr.upper()
            myEvent = QtGui.QKeyEvent(event.type(), ord(engChr), event.modifiers(), engChr, event.isAutoRepeat(), event.count())
            QtGui.QLineEdit.keyPressEvent(self, myEvent)
        else:
            QtGui.QLineEdit.keyPressEvent(self, event)


    def text(self):
        # здесь намеренно работаем с QString, так как обычно предполагается что
        # editor.text() возвращает QString
        val = QtGui.QLineEdit.text(self).simplified()
        if val.endsWith('.'):
            val.chop(1)
        return val


class CICDCodeEditEx(CROComboBox):
    u"""Редактор кодов МКБ с выпадающим деревом"""

    __pyqtSignals__ = ('textChanged(QString)',
                       'textEdited(QString)',
                       'editingFinished()'
                      )

    def __init__(self, parent = None):
        CROComboBox.__init__(self, parent)
        self._lineEdit=CICDCodeEdit(self)
        self.setLineEdit(self._lineEdit)
        self._lineEdit.setCursorPosition(0)
        self.ICDTreePopup=None
        self.filter = u''
        self.findfilter = u''
        self.isLUDSelected = False
        self.isLUDEnabled = False
        self.clientId = None
        self.connect(self._lineEdit, SIGNAL('textEdited(QString)'), self.onTextEdited)
        self.connect(self._lineEdit, SIGNAL('textChanged(QString)'), self.onTextChanged)


    def sizeHint(self):
        style = self.style()
        option = QtGui.QStyleOptionComboBox()
        option.initFrom(self)
        size = option.fontMetrics.boundingRect('W06.98').size()
        result = style.sizeFromContents(style.CT_ComboBox, # ContentsType type,
                                        option,            # const QStyleOption * option
                                        size,              # const QSize & contentsSize,
                                        self)              # const QWidget * widget = 0
        return result


    def showPopup(self):
        if not self.isReadOnly():
            if not self.ICDTreePopup:
                self.ICDTreePopup = CICDTreePopup(self, self.filter, self.findfilter)
                self.connect(self.ICDTreePopup, SIGNAL('diagSelected(QString)'), self.setText)

            pos = self.rect().bottomLeft()
            pos2 = self.rect().topLeft()
            pos = self.mapToGlobal(pos)
            pos2 = self.mapToGlobal(pos2)
            size=self.ICDTreePopup.sizeHint()
            screen = QtGui.QApplication.desktop().availableGeometry(pos)
    #        size.setWidth(size.width()+20) # magic. похоже, что sizeHint считается неправильно. русские буквы виноваты?
            size.setWidth(screen.width()) # наименования длинные, распахиваем на весь экран
            pos.setX( max(min(pos.x(), screen.right()-size.width()), screen.left()) )
            pos.setY( max(min(pos.y(), screen.bottom()-size.height()), screen.top()) )
    #
    ##        if (pos.y() + size.height() > screen.bottom()):
    ##            pos.setY(pos2.y() - size.height())
    ##        elif (pos.y() < screen.top()):
    ##            pos.setY(screen.top())
    ##        if (pos.y() < screen.top()):
    ##            pos.setY(screen.top())
    ##        if (pos.y()+size.height() > screen.bottom()):
    ##            pos.setY(screen.bottom()-size.height())
            self.ICDTreePopup.move(pos)
            self.ICDTreePopup.resize(size)
            self.ICDTreePopup.setLUDEnabled(self.isLUDEnabled)
            self.ICDTreePopup.setLUDChecked(self.isLUDSelected, self.clientId)
            self.ICDTreePopup.setCurrentDiag(self.text())
            self.ICDTreePopup.show()


#    def focusInEvent(self, event):
#        QtGui.QComboBox.focusInEvent(event)
#        self.setCursorPosition(0)


    def setLUDChecked(self, isLUDSelected, clientId):
        self.isLUDSelected = isLUDSelected
        self.clientId = clientId


    def setLUDEnabled(self, value):
        self.isLUDEnabled = value


    def setFilter(self, filter):
        self.filter = filter


    def setFindFilter(self, findfilter):
        self.findfilter = findfilter


    def setText(self, text):
        self._lineEdit.setText(text)
        self._lineEdit.setCursorPosition(0)


    def selectAll(self):
        self._lineEdit.selectAll()
        self._lineEdit.setCursorPosition(0)


    def setCursorPosition(self,  pos=0):
        self._lineEdit.setCursorPosition(pos)


    def text(self):
        return self._lineEdit.text()


    def onTextChanged(self, text):
        self.emit(SIGNAL('textChanged(QString)'), text)


    def onTextEdited(self, text):
        self.emit(SIGNAL('textEdited(QString)'), text)


    def onEditingFinished(self):
        self.emit(SIGNAL('editingFinished()'))


class CICDCodeComboBoxEx(CICDCodeEditEx):
    u"""Редактор кодов МКБ ComboBox"""
    __pyqtSignals__ = ('textChanged(QString)',
                       'textEdited(QString)',
                       'editingFinished()'
                      )

    def __init__(self, parent = None):
        CICDCodeEditEx.__init__(self, parent)
        self.connect(self._lineEdit, SIGNAL('editingFinished()'), self.onEditingFinished)


    def onEditingFinished(self):
        newMKB = self.text()
        if newMKB and self.findText(newMKB) > -1:
            self.setText(newMKB)
        else:
            self.setText('')


class CICDCodeEditFocusEvent(CICDCodeEditEx):
    u"""Редактор кодов МКБ с выпадающим деревом"""

    __pyqtSignals__ = ('textChanged(QString)',
                       'textEdited(QString)',
                       'editingFinished()'
                      )

    def __init__(self, parent=None):
        CICDCodeEditEx.__init__(self, parent)


    def focusOutEvent(self, event):
        QtGui.QComboBox.focusOutEvent(self, event)
        self.emit(SIGNAL('editingFinished()'))
