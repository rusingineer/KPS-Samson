# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2020 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

#
import re
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import QString, QVariant, Qt

from library.StrComboBox           import CStrComboBox
from library.Utils                 import forceString
from ActionPropertyValueType       import CActionPropertyValueType
from library.SpellCheck            import CSpellCheckTextEdit

class CStringActionPropertyValueType(CActionPropertyValueType):
    name         = 'String'
    variantType  = QVariant.String
    initPresetValue = True

    class CPlainPropEditor(CSpellCheckTextEdit):
        def __init__(self, action, domain, parent, clientId, eventTypeId):
            CSpellCheckTextEdit.__init__(self, parent)
            self.setTabChangesFocus(True)
            self.setWordWrapMode(QtGui.QTextOption.NoWrap)
            self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
            self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
            self.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
            self.regx = None
            self.cursor = None
            if domain.startswith('regexp'):
                self.regx = domain.replace('regexp', "", 1)
                self.validator = QtGui.QRegExpValidator(QtCore.QRegExp(self.regx))
                self.document().contentsChange.connect(self.on_ContentsChange)

        def keyPressEvent(self, event):
            if event.key() == QtCore.Qt.Key_Return or event.key() == QtCore.Qt.Key_Enter:
                event.ignore()
            elif event.key() == QtCore.Qt.Key_Down or event.key() == QtCore.Qt.Key_Up:
                event.ignore()
                event = QtGui.QKeyEvent(event.type(), QtCore.Qt.Key_Tab if event.key() == QtCore.Qt.Key_Down else QtCore.Qt.Key_Backtab, event.modifiers())
                QtGui.QTextEdit.keyPressEvent(self, event)
            else:
                QtGui.QTextEdit.keyPressEvent(self, event)

        def on_ContentsChange(self, position, charsRemoved, charsAdded):
            if charsAdded > 0 and self.regx:
                beforeText = self.toPlainText()[:position]
                text = self.toPlainText()[position:position+charsAdded]
                afterText = self.toPlainText()[position+charsAdded:]
                newText = QString()
                for letter in text:
                    newState = self.validator.validate(beforeText+newText+letter+afterText, 0)
                    if newState[0] in [QtGui.QValidator.Acceptable, QtGui.QValidator.Intermediate]:
                        newText += letter
                if not beforeText+newText+afterText == self.toPlainText():
                    oldState = self.document().blockSignals(True)
                    self.setValue(beforeText+newText+afterText)
                    self.document().blockSignals(oldState)

                    self.cursor = QtGui.QTextCursor(self.document())
                    self.cursor.movePosition(QtGui.QTextCursor.End)
                    self.setTextCursor(self.cursor)
        
        
        def on_CloseValidate(self):
            if self.regx and self.validator.validate(self.toPlainText(),0)[0] != QtGui.QValidator.Acceptable:
                self.setValue('')
            
        
        def wheelEvent(self, event):
            pass

        def setValue(self, value):
            v = forceString(value)
            self.setText(v)

        def value(self):
            return unicode(self.toPlainText())


    class CComboBoxPropEditor(CStrComboBox):
        def __init__(self, action, domain, parent, clientId, eventTypeId):
            CStrComboBox.__init__(self, parent)
            self.setDomain(domain)
            val = self._parse(domain)
    
        def keyPressEvent(self, event):
            if event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
                QtGui.QComboBox.keyPressEvent(self, event)
            else:
                CStrComboBox.keyPressEvent(self, event)


    @staticmethod
    def convertDBValueToPyValue(value):
        return forceString(value)


    convertQVariantToPyValue = convertDBValueToPyValue


    def getEditorClass(self):
        if self.domain and not self.domain.startswith('regexp'):
            return self.CComboBoxPropEditor
        else:
            return self.CPlainPropEditor

    def getPresetValue(self, action):
        if u'_urn_' in self.domain:
            return self.CComboBoxPropEditor(action,self.domain,None,None,None).value()
#    @staticmethod
#    def getDomainEditorClass():
#        return CStringDomainEditor
#
#
#class CStringDomainEditor(CDialogBase):


