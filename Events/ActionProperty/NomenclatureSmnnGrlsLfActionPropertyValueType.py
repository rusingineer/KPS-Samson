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

from library.ESKLP.SmnnGrlsLfComboBoxEx import CSmnnGrlsLfComboBoxEx
from library.Utils           import forceStringEx, forceRef
from ActionPropertyValueType import CActionPropertyValueType
from Stock.StockMotionInfo   import CLFFormInfo
from Stock.Utils             import getExistsNomenclatureIdList


class CNomenclatureSmnnGrlsLfActionPropertyValueType(CActionPropertyValueType):
    variantType  = QVariant.Int
    name         = u'Форма выпуска МНН'
    cacheText    = True

    class CPropEditor(CSmnnGrlsLfComboBoxEx):
        def __init__(self, action, domain, parent, clientId, eventTypeId, eventEditor=None):
            CSmnnGrlsLfComboBoxEx.__init__(self, parent)
            self.setOnlySmnnUUID(True)
            self.setOrgStructureId(QtGui.qApp.currentOrgStructureId())
            self.action = action
            self.nomenclatureIdList = []
            isNomenclatureSmnnActionPropertyValueType = False
            if eventEditor and QtGui.qApp.controlSMFinance() in (1, 2):
                self.nomenclatureIdList = getExistsNomenclatureIdList(self.getOrgStructureId(), self.eventEditor.eventFinanceId, self.eventEditor.eventMedicalAidKindId)
            self.setNomenclatureIdList(self.nomenclatureIdList)
            if self.action:
                actionType = self.action.getType()
                self.setOnlyExists(actionType.isNomenclatureExpense)
                propertyList = self.action.getProperties()
                for actionProperty in propertyList:
                    propertyType = actionProperty.type()
                    if propertyType.isNomenclatureValueType():
                        property = self.action.getPropertyById(propertyType.id)
                        nomenclatureId = property.getValue()
                        self.setNomenclatureId(nomenclatureId)
                    if propertyType.isNomenclatureSmnnActionPropertyValueType():
                        property = self.action.getPropertyById(propertyType.id)
                        smnnUUID = property.getValue()
                        self.setNomenclatureSmnnUUID(smnnUUID)
                        isNomenclatureSmnnActionPropertyValueType = True
                self.setOnlySmnnUUID(isNomenclatureSmnnActionPropertyValueType)

        def setValue(self, value):
            from Events.Utils import getNomenclatureSmnnIdList
            lfFormId = forceRef(value)
            oldLfFormId = None
            if self.action:
                propertyListSmnnGrlsLf = self.action.getProperties()
                for actionPropertySmnnGrlsLf in propertyListSmnnGrlsLf:
                    propertyTypeSmnnGrlsLf = actionPropertySmnnGrlsLf.type()
                    if propertyTypeSmnnGrlsLf.isNomenclatureSmnnGrlsLfActionPropertyValueType():
                        propertySmnnGrlsLf = self.action.getPropertyById(propertyTypeSmnnGrlsLf.id)
                        oldLfFormId = propertySmnnGrlsLf.getValue()
                        break
            CSmnnGrlsLfComboBoxEx.setValue(self, lfFormId)
            if self.action and lfFormId != oldLfFormId:
                propertyList = self.action.getProperties()
                for actionProperty in propertyList:
                    propertyType = actionProperty.type()
                    if propertyType.isNomenclatureSmnnActionPropertyValueType():
                        property = self.action.getPropertyById(propertyType.id)
                        smnnUUID = property.getValue()
                        nomenclatureSmnnIdList = getNomenclatureSmnnIdList(smnnUUID, lfFormId, nomenclatureIdList = self.nomenclatureIdList)
                        propertyListNC = self.action.getProperties()
                        for actionPropertyNC in propertyListNC:
                            propertyTypeNC = actionPropertyNC.type()
                            if propertyTypeNC.isNomenclatureValueType():
                                propertyNC = self.action.getPropertyById(propertyTypeNC.id)
                                nomenclatureId = propertyNC.getValue()
                                self.setNomenclatureIdList(nomenclatureSmnnIdList)
                                if len(nomenclatureSmnnIdList) == 1:
                                    nomenclatureSmnnId = nomenclatureSmnnIdList[0]
                                    if nomenclatureId != nomenclatureSmnnId:
                                        self.setNomenclatureId(nomenclatureSmnnId)
#                                        propertyNC.setValue(nomenclatureSmnnId)
#                                        propertyNC.setValue(None)
                                if nomenclatureId not in nomenclatureSmnnIdList:
                                    propertyNC.setValue(None)
                                    self.setNomenclatureId(None)
                                break
                        break


    @staticmethod
    def convertDBValueToPyValue(value):
        return forceRef(value)


    convertQVariantToPyValue = convertDBValueToPyValue


    def toText(self, lfFormId):
        result = u''
        if lfFormId:
            db = QtGui.qApp.db
            table = db.table('rbLfForm')
            record = db.getRecordEx(table, [table['name'], table['dosage']], [table['id'].eq(lfFormId), table['isESKLP'].eq(1)])
            if record:
                result = forceStringEx(record.value('name'))
                dosage = forceStringEx(record.value('dosage'))
                if dosage:
                    result += u' ' + dosage
        return result


    def toInfo(self, context, v):
        return context.getInstance(CLFFormInfo, forceStringEx(v))


    @classmethod
    def getTableName(cls):
        return cls.tableNamePrefix+'rbLfForm'

