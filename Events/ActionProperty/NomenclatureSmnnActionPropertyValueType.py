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

from library.ESKLP.SmnnComboBoxEx import CSmnnComboBoxEx
from library.Utils           import forceStringEx
from ActionPropertyValueType import CActionPropertyValueType
from library.ESKLP.SmnnInfo  import CSmnnInfo
from Stock.Utils             import getExistsNomenclatureIdList

class CNomenclatureSmnnActionPropertyValueType(CActionPropertyValueType):
    variantType  = QVariant.Int
    name         = u'Стандартизованное МНН'
    cacheText    = True

    class CPropEditor(CSmnnComboBoxEx):
        def __init__(self, action, domain, parent, clientId, eventTypeId, eventEditor=None):
            CSmnnComboBoxEx.__init__(self, parent)
            self.setOrgStructureId(QtGui.qApp.currentOrgStructureId())
            self.action = action
            self.nomenclatureIdList = []
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
                        self.setNomenclatureId(property.getValue())
                        break

        def setValue(self, value):
            from Events.Utils import getLfFormIdList, getNomenclatureSmnnToLfFormIdList
            smnnUUID = forceStringEx(value)
            oldSmnnUUID = ''
            if self.action:
                propertyListSmnn = self.action.getProperties()
                for actionPropertySmnn in propertyListSmnn:
                    propertyTypeSmnn = actionPropertySmnn.type()
                    if propertyTypeSmnn.isNomenclatureSmnnActionPropertyValueType():
                        propertySmnn = self.action.getPropertyById(propertyTypeSmnn.id)
                        oldSmnnUUID = propertySmnn.getValue()
                        break
            CSmnnComboBoxEx.setValue(self, smnnUUID)
            if self.action:
                propertyListSmnn = self.action.getProperties()
                for actionPropertySmnn in propertyListSmnn:
                    propertyTypeSmnn = actionPropertySmnn.type()
                    if propertyTypeSmnn.isNomenclatureSmnnActionPropertyValueType():
                        propertySmnn = self.action.getPropertyById(propertyTypeSmnn.id)
                        oldSmnnUUID = propertySmnn.getValue()
                        if oldSmnnUUID != smnnUUID:
                            propertyList = self.action.getProperties()
                            for actionProperty in propertyList:
                                propertyType = actionProperty.type()
                                if propertyType.isNomenclatureSmnnGrlsLfActionPropertyValueType():
                                    property = self.action.getPropertyById(propertyType.id)
                                    if smnnUUID:
                                        lfFormId = None
                                        propertyVal = property.getValue()
                                        lfFormIdList = getLfFormIdList(smnnUUID = smnnUUID, nomenclatureIdList = self.nomenclatureIdList)
                                        if len(lfFormIdList) == 1:
                                            lfFormId = lfFormIdList[0]
                                            if propertyVal != lfFormId:
#                                                property.setValue(lfFormId)
                                                property.setValue(None)
                                        if propertyVal not in lfFormIdList:
                                            property.setValue(None)
#                                        if lfFormId:
                                        nomenclatureSmnnIdList = getNomenclatureSmnnToLfFormIdList(smnnUUID, lfFormIdList, nomenclatureIdList = self.nomenclatureIdList)
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
                                                        self.setNomenclatureIdList(nomenclatureSmnnIdList)
#                                                        propertyNC.setValue(nomenclatureSmnnId)
#                                                        propertyNC.setValue(None)
                                                if nomenclatureId not in nomenclatureSmnnIdList:
                                                    propertyNC.setValue(None)
                                                    self.setNomenclatureId(None)
                                    else:
                                        property.setValue(None)
                                    break
                        break


    @staticmethod
    def convertDBValueToPyValue(value):
        return forceStringEx(value)


    convertQVariantToPyValue = convertDBValueToPyValue


    def toText(self, UUID):
        if not UUID:
            return ''
        result = u''
        db = QtGui.qApp.db
        table = db.table('esklp.Smnn')
        if UUID:
            record = db.getRecordEx(table, [table['code'], table['mnn'], table['form']], [table['UUID'].eq(UUID)])
            if record:
                result = forceStringEx(record.value('mnn'))
        return result


    def toInfo(self, context, v):
        return context.getInstance(CSmnnInfo, forceStringEx(v))


    @classmethod
    def getTableName(cls):
        return cls.tableNamePrefix+'esklp_Smnn'

