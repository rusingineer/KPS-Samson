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
from PyQt4.QtCore import QVariant

from library.Utils         import forceRef, forceString

from ActionPropertyValueType       import CActionPropertyValueType
from StringActionPropertyValueType import CStringActionPropertyValueType

from library.Utils import forceInt



class CCounterActionPropertyValueType(CActionPropertyValueType):
    name              = u'Счетчик'
    variantType       = QVariant.String
    isCopyable        = False
    initPresetValue   = True

    class CPropEditor(QtGui.QLineEdit):
        def __init__(self, action, domain, parent, clientId, eventTypeId):
            QtGui.QLineEdit.__init__(self, parent)
            self.setReadOnly(bool(forceInt(QtGui.qApp.db.translate('rbCounter', 'code', domain, 'sequenceFlag'))))

        def setValue(self, value):
            v = forceString(value)
            self.setText(v)

        def value(self):
            return unicode(self.text())


    @staticmethod
    def convertDBValueToPyValue(value):
        return forceString(value)


    @staticmethod
    def convertQVariantToPyValue(value):
        return forceString(value)


    @classmethod
    def getTableName(cls):
        return cls.tableNamePrefix+CStringActionPropertyValueType.name


    def getCounterValue(self, clientId):
        counterId = self.getCounterId()
        value = None
        if counterId:
            try:
                value = QtGui.qApp.getDocumentNumber(clientId, counterId)
            except Exception, e:
                QtGui.QMessageBox.critical(QtGui.qApp.mainWindow,
                                           u'Внимание!',
                                           u'Произошла ошибка при получении значения счетчика\n%s' % e,
                                           QtGui.QMessageBox.Ok)
        return value


    def getCounterId(self):
        domain = self.domain
        if not domain:
            return None
        return forceRef(QtGui.qApp.db.translate('rbCounter', 'code', domain, 'id'))


    def getEditorClass(self):
        return self.CPropEditor


    def getPresetValue(self, action):
        return self.getCounterValue(action.presetValuesConditions.get('clientId'))
