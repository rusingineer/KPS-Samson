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

from PyQt4 import QtGui
from PyQt4.QtCore import QVariant

from library.Utils         import forceString
from library.SpellCheck import CSpellCheckTextEdit
from library.TextEditCompletionMixin import CTextEditCompletionMixin

from ActionPropertyValueType       import CActionPropertyValueType
from StringActionPropertyValueType import CStringActionPropertyValueType


class CTextActionPropertyValueType(CActionPropertyValueType):
    name         = 'Text'
    variantType  = QVariant.String
    preferredHeight = 10
    preferredHeightUnit = 1
    expandingHeight = True

    class CPropEditor(CSpellCheckTextEdit, CTextEditCompletionMixin):
        def __init__(self, action, domain, parent, clientId, eventTypeId):
            CSpellCheckTextEdit.__init__(self, parent)
            CTextEditCompletionMixin.__init__(self)

        def setValue(self, value):
            v = forceString(value)
            self.setPlainText(v)


        def value(self):
            return unicode(self.toPlainText())


    @staticmethod
    def convertDBValueToPyValue(value):
        return forceString(value)


    convertQVariantToPyValue = convertDBValueToPyValue


    def toInfo(self, context, v):
        return forceString(v) if v else ''


    @classmethod
    def getTableName(cls):
        return cls.tableNamePrefix+CStringActionPropertyValueType.name
