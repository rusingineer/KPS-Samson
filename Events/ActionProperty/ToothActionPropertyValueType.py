# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2017 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import QVariant, Qt

from library.StrComboBox    import CStrComboBox
from library.Utils          import forceString, trim

from ActionPropertyValueType       import CActionPropertyValueType
from StringActionPropertyValueType import CStringActionPropertyValueType


class CToothActionPropertyValueType(CActionPropertyValueType):
    name           = u'Зуб'
    variantType    = QVariant.String


    class CComboBoxPropEditor(CStrComboBox):
        def __init__(self, action, domain, parent, clientId, eventTypeId):
            CStrComboBox.__init__(self, parent)
            self.rbComboBoxMark = False
            self.setDomain(domain)

        def setRBComboBoxMark(self, value):
            self.rbComboBoxMark = value

        def text(self):
            curText = self.currentText()
            if self.rbComboBoxMark:
                return unicode(self.currentIndex())
            return unicode(curText)
    
        def keyPressEvent(self, event):
            if event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
                QtGui.QComboBox.keyPressEvent(self, event)
            else:
                CStrComboBox.keyPressEvent(self, event)

        value = text


    class CTextEditPropEditor(QtGui.QTextEdit):
        def __init__(self, action, domain, parent, clientId, eventTypeId):
            QtGui.QTextEdit.__init__(self, parent)

        def setValue(self, value):
            v = forceString(value)
            self.setPlainText(v)

        def value(self):
            return unicode(self.toPlainText())


    @staticmethod
    def convertDBValueToPyValue(value):
        return forceString(value)


    convertQVariantToPyValue = convertDBValueToPyValue

    @classmethod
    def getTableName(cls):
        return cls.tableNamePrefix+CStringActionPropertyValueType.name


    def getEditorClass(self):
        if bool(trim(self.domain)):
            return self.CComboBoxPropEditor
        else:
            return self.CTextEditPropEditor

