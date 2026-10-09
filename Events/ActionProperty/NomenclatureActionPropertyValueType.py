# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2026 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

import json
from PyQt4 import QtGui
from PyQt4.QtCore import QVariant

from Stock.NomenclatureComboBox import CNomenclatureComboBox
from library.Utils              import forceRef, forceString, forceInt, forceStringEx
from ActionPropertyValueType    import CActionPropertyValueType
from FeatureActionPropertyValueType import CFeatureActionPropertyValueType

from Stock.StockMotionInfo import CNomenclatureInfo


class CNomenclatureActionPropertyValueType(CActionPropertyValueType):
    variantType  = QVariant.Int
    name         = u'Номенклатура ЛСиИМН'
    cacheText = True

    class CPropEditor(CNomenclatureComboBox):
        def __init__(self, action, domain, parent, clientId, eventTypeId, eventEditor=None):
            CNomenclatureComboBox.__init__(self, parent)
            self.setUseClientUnitId()
            actionType = action.getType()
            actionTypeId = actionType.id
            self.action = action
            smnnUUID = None
            smnnGrlsLfId = None
            if self.action:
                propertyList = self.action.getProperties()
                for actionProperty in propertyList:
                    propertyType = actionProperty.type()
                    if propertyType.isNomenclatureActiveSubstanceValueType():
                        property = self.action.getPropertyById(propertyType.id)
                        self.setNomenclatureActiveSubstanceId(property.getValue())
                        break
                    elif propertyType.isNomenclatureSmnnActionPropertyValueType():
                        property = self.action.getPropertyById(propertyType.id)
                        self.setNomenclatureSmnnUUID(property.getValue())
                        smnnUUID = property.getValue()
                        self.setNomenclatureSmnnUUID(smnnUUID)
                        smnnName = property.getText()
                        self.setNomenclatureSmnnName(smnnName if smnnName is not None else '')
                    elif propertyType.isNomenclatureSmnnGrlsLfActionPropertyValueType():
                        property = self.action.getPropertyById(propertyType.id)
                        self.setLfFormId(property.getValue())
                        smnnGrlsLfId = property.getValue()
                        self.setLfFormId(smnnGrlsLfId)
            cols = ['nomenclatureClass_id', 'nomenclatureKind_id', 'nomenclatureType_id']  # wtf
            record = QtGui.qApp.db.getRecord('ActionType', cols, actionTypeId)

            nomenclatureClassId = forceRef(record.value('nomenclatureClass_id'))
            nomenclatureKindId  = forceRef(record.value('nomenclatureKind_id'))
            nomenclatureTypeId  = forceRef(record.value('nomenclatureType_id'))

            if domain:
                domainObj = json.loads(domain)
                featuresPropertyName = domainObj.get('featuresPropertyName', '')
                if featuresPropertyName:
                    featuresStr = action[featuresPropertyName]
                else:
                    featuresStr = ''
            else:
                featuresStr = ''

            self.setDefaultIds(nomenclatureClassId, nomenclatureKindId, nomenclatureTypeId)
            financeId = action.getFinanceId()
            if financeId:
                self.setFinanceId(financeId)

            medicalAidKindId = self.getMedicalAidKindId(eventTypeId)
            self.setMedicalAidKindId(medicalAidKindId)
            self.action.setMedicalAidKindId(self._medicalAidKindId)


            if featuresStr:
                try:
                    features = CFeatureActionPropertyValueType.parseValue(featuresStr)
                    self.setDefaultFeatures(features)
                except:
                    pass

            self.setOrgStructureId(QtGui.qApp.currentOrgStructureId())
            self.setIsOnlyMnnEsklpFormVisible(bool(smnnUUID) and bool(smnnGrlsLfId))
            self.setOnlyNomenclature(True)
            self.setOnlyExists(actionType.isNomenclatureExpense)
            self.setPreferredWidth(QtGui.QApplication.desktop().width() - self.mapToGlobal(self.rect().bottomLeft()).x())
            self.getFilterData()
            self.setFilter(self._filter)
            self.reloadData()

        def getMedicalAidKindId(self, eventTypeId):
            db = QtGui.qApp.db
            tableEvent = db.table('Event')
            tableEventType = db.table('EventType')
            cond = [tableEventType['id'].eq(eventTypeId)]
            queryTable = tableEvent
            queryTable = queryTable.leftJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
            record = db.getRecordEx(queryTable, tableEventType['medicalAidKind_id'], cond)
            if record:
                return forceInt(record.value('medicalAidKind_id'))
            return None

        def setValue(self, value):
            from Events.Utils import getLfFormIdList
            nomenclatureId = forceRef(value)
            self.setFilter('')
            oldNomenclatureId = None
            propertyListNC = self.action.getProperties()
            for actionPropertyNC in propertyListNC:
                propertyTypeNC = actionPropertyNC.type()
                if propertyTypeNC.isNomenclatureValueType():
                    propertyNC = self.action.getPropertyById(propertyTypeNC.id)
                    oldNomenclatureId = propertyNC.getValue()
                    break
            CNomenclatureComboBox.setValue(self, nomenclatureId)
            if self.action and nomenclatureId:
                propertyList = self.action.getProperties()
                for actionProperty in propertyList:
                    propertyType = actionProperty.type()
                    if propertyType.isNomenclatureSmnnActionPropertyValueType():
                        property = self.action.getPropertyById(propertyType.id)
                        propertyVal = property.getValue()
                        db = QtGui.qApp.db
                        tableEsklp_Smnn = db.table('esklp.Smnn')
                        tableNC = db.table('rbNomenclature')
                        tableESKLP_Klp = db.table('esklp.Klp')
                        cond = []
                        order = u'esklp.Smnn.code, esklp.Smnn.mnn, esklp.Smnn.form'
                        queryTable = tableNC.innerJoin(tableESKLP_Klp, tableESKLP_Klp['UUID'].eq(tableNC['esklpUUID']))
                        queryTable = queryTable.innerJoin(tableEsklp_Smnn, tableEsklp_Smnn['id'].eq(tableESKLP_Klp['smnn_id']))
                        cond.append(tableNC['id'].eq(nomenclatureId))
                        records = db.getRecordList(queryTable, [tableEsklp_Smnn['UUID']], cond, order=order)
                        UUID = ''
                        if len(records) == 1:
                            record = records[0]
                            UUID = forceStringEx(record.value('UUID')) if record else ''
                        if propertyVal != UUID or nomenclatureId != oldNomenclatureId:
                            property.setValue(UUID)
                            propertyListGrlsLf = self.action.getProperties()
                            for actionPropertyGrlsLf in propertyListGrlsLf:
                                propertyTypeGrlsLf = actionPropertyGrlsLf.type()
                                if propertyTypeGrlsLf.isNomenclatureSmnnGrlsLfActionPropertyValueType():
                                    propertyGrlsLf = self.action.getPropertyById(propertyTypeGrlsLf.id)
                                    if UUID:
                                        propertyValGrlsLf = propertyGrlsLf.getValue()
                                        lfFormIdList = getLfFormIdList(nomenclatureId = nomenclatureId, smnnUUID = UUID)
                                        if len(lfFormIdList) == 1:
                                            lfFormId = lfFormIdList[0]
                                            if propertyValGrlsLf != lfFormId:
                                                propertyGrlsLf.setValue(lfFormId)
                                        elif propertyValGrlsLf not in lfFormIdList:
                                            propertyGrlsLf.setValue(None)
                                    else:
                                        propertyGrlsLf.setValue(None)
                                    break
                        break

        def setFinanceMedicalAidKind(self, var):
            if (self._financeId != self._popup._financeId or self._medicalAidKindId != self._popup._medicalAidKindId):
                self.setFinanceId(self._popup._financeId)
                self.setMedicalAidKindId(self._popup._medicalAidKindId)
                self.action.setFinanceId(self._financeId)
                self.action.setMedicalAidKindId(self._medicalAidKindId)
                self.getFilterData()
                self._filier = self._filter
                self.reloadData()

    @staticmethod
    def convertDBValueToPyValue(value):
        return forceRef(value)


    convertQVariantToPyValue = convertDBValueToPyValue


    def toText(self, nomenclatureId):
        if not nomenclatureId:
            return ''

        db = QtGui.qApp.db
        fields = 'code, mnnLatin, originName, name, internationalNonproprietaryName, dosageValue'
        record = db.getRecord('rbNomenclature', fields, nomenclatureId)
        if record:
            code = forceString(record.value('code'))
            name = forceString(record.value('name'))
            mnnLatin = forceString(record.value('mnnLatin'))
            originName = forceString(record.value('originName'))
            internationalNonproprietaryName = forceString(record.value('internationalNonproprietaryName'))

            if name:
                result = name
            elif mnnLatin:
                result = mnnLatin
            elif originName:
                result = originName
            else:
                result = internationalNonproprietaryName
            result = ' | '.join([code, result]) if name else result
        else:
            result = ''

        return result


    def toInfo(self, context, v):
        return context.getInstance(CNomenclatureInfo, forceRef(v))


    @classmethod
    def getTableName(cls):
        return cls.tableNamePrefix+'rbNomenclature'

