# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2015 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################


from PyQt4.QtCore import QVariant
from PyQt4 import QtGui
from library.Utils           import forceString, forceRef
from library.ICDCodeEdit     import CICDCodeEditEx
from library.ICDUtils            import MKBwithoutSubclassification
from Events.MKBInfo import CMKBInfo

from ActionPropertyValueType import CActionPropertyValueType


class CMKBActionPropertyValueType(CActionPropertyValueType):
    name         = u'Код МКБ'
    variantType  = QVariant.String

    class CPropEditor(CICDCodeEditEx):
        def __init__(self, action, domain, parent, clientId, eventTypeId):
            CICDCodeEditEx.__init__(self, parent)
            
        def setValue(self, value):
            v = forceString(value)
            self.setText(v)

        def value(self):
            return self.checkMKB(self.text())

        def checkMKB(self, MKB):
            if unicode(MKB):
                db = QtGui.qApp.db
                tableMKB = db.table('MKB')

                record = db.getRecordEx(tableMKB, 'DiagName',
                                        tableMKB['DiagID'].eq(MKBwithoutSubclassification(unicode(MKB))))
                if not record:
                    message = u'Кода %s не существует, замените его.' % (unicode(MKB))
                    QtGui.QMessageBox.critical(None, u'Внимание!', message)

                    return unicode('')
                else:
                    return unicode(MKB)

    @staticmethod
    def convertDBValueToPyValue(value):
        return forceString(value)

    convertQVariantToPyValue = convertDBValueToPyValue
    
    def toInfo(self, context, v):
        return context.getInstance(CMKBInfo, forceRef(v))

    def getTableName(self):
        return self.tableNamePrefix + 'MKB'
