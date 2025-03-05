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

from library.crbcombobox     import CRBComboBox
from library.Utils           import forceRef, forceString, forceDate
from ActionPropertyValueType import CActionPropertyValueType
from Events.ActionProperty   import CActionPropertyValueTypeRegistry


class CNomenclatureCalculationParamActionPropertyValueType(CActionPropertyValueType):
    variantType  = QVariant.Int
    name         = u'Шаблон свойства по значению'

    class CPropEditor(CRBComboBox):
        def __init__(self, action, domain, parent, clientId, eventTypeId):
            CRBComboBox.__init__(self, parent)
            self.headers = []
            self.items = {}
            self.clientId = clientId
            filter = u'ActionPropertyTemplate.isCalcParamDoseNomenclatureExpense = 1'
            if self.clientId:
                self.getValueProperties()
                actionPropertyTemplateIdList = self.items.keys()
                filter = u'0'
                if actionPropertyTemplateIdList:
                    filter += u' AND ActionPropertyTemplate.id IN (%s)'%(u','.join(str(id) for id in actionPropertyTemplateIdList if id))
                self.action = action
                if self.action:
                    propertyList = self.action.getProperties()
                    for actionProperty in propertyList:
                        propertyType = actionProperty.type()
                        if propertyType.isNomenclatureCalculationParamActionPropertyValueType():
                            property = self.action.getPropertyById(propertyType.id)
                            self.setValue(property.getValue())
                            break
            else:
                self.setTable('ActionPropertyTemplate', addNone = True, filter = filter)


        def getValueProperties(self):
            self.headers = []
            self.items = {}
            if not self.clientId:
                return
            if self.clientId:
                db = QtGui.qApp.db
                tableMonitoring = db.table('Client_Monitoring')
                tableAPTemplate = db.table('ActionPropertyTemplate')
                queryTable = tableMonitoring.innerJoin(tableAPTemplate, tableAPTemplate['id'].eq(tableMonitoring['propertyTemplate_id']))
                cond = [tableAPTemplate['isCalcParamDoseNomenclatureExpense'].eq(1),
                        tableMonitoring['deleted'].eq(0),
                        tableAPTemplate['deleted'].eq(0),
                        tableMonitoring['client_id'].eq(self.clientId)
                        ]
                cols = [tableAPTemplate['id'],
                        tableAPTemplate['name']
                        ]
                records = db.getRecordList(queryTable, cols, cond, order='ActionPropertyTemplate.code, ActionPropertyTemplate.name')
                for record in records:
                    templateId = forceRef(record.value('id'))
                    if templateId and templateId not in self.headers:
                        self.headers.append(templateId)
            if len(self.headers) > 1:
                db = QtGui.qApp.db
                tableEvent = db.table('Event')
                tableAction = db.table('Action')
                tableActionType = db.table('ActionType')
                tableActionProperty = db.table('ActionProperty')
                tableActionPropertyType = db.table('ActionPropertyType')
                tableMonitoring = db.table('Client_Monitoring')
                tableAPTemplate = db.table('ActionPropertyTemplate')
                queryTable = tableEvent.innerJoin(tableAction, tableAction['event_id'].eq(tableEvent['id']))
                queryTable = queryTable.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
                queryTable = queryTable.innerJoin(tableActionProperty, tableActionProperty['action_id'].eq(tableAction['id']))
                queryTable = queryTable.innerJoin(tableActionPropertyType, tableActionPropertyType['actionType_id'].eq(tableActionType['id']))
                queryTable = queryTable.innerJoin(tableAPTemplate, tableAPTemplate['id'].eq(tableActionPropertyType['template_id']))
                queryTable = queryTable.innerJoin(tableMonitoring, tableMonitoring['propertyTemplate_id'].eq(tableAPTemplate['id']))
                cond = [tableEvent['client_id'].eq(self.clientId),
                        tableAPTemplate['isCalcParamDoseNomenclatureExpense'].eq(1),
                        tableEvent['deleted'].eq(0),
                        tableAction['deleted'].eq(0),
                        tableAction['endDate'].isNotNull(),
                        tableActionPropertyType['template_id'].isNotNull(),
                        tableActionType['deleted'].eq(0),
                        tableActionPropertyType['deleted'].eq(0),
                        tableAPTemplate['deleted'].eq(0),
                        tableMonitoring['deleted'].eq(0),
                        tableActionProperty['deleted'].eq(0),
                        tableActionPropertyType['template_id'].inlist(self.headers),
                        tableActionProperty['type_id'].eq(tableActionPropertyType['id'])
                        ]
                cols = [u'DISTINCT ActionPropertyType.typeName, ActionPropertyType.valueDomain',]
                records = db.getRecordList(queryTable, cols, cond)
                cols = [tableAction['endDate'],
                        tableActionPropertyType['template_id'],
                        tableActionPropertyType['typeName'],
                        tableActionPropertyType['valueDomain']
                        ]
                for record in records:
                    queryTableProperty = queryTable
                    typeName = forceString(record.value('typeName'))
                    valueDomain = forceString(record.value('valueDomain'))
                    propertyType = CActionPropertyValueTypeRegistry.get(typeName, valueDomain)
                    if propertyType:
                        tablePropertyType = db.table(propertyType.getTableName())
                        queryTableProperty = queryTableProperty.leftJoin(tablePropertyType, db.joinAnd([tablePropertyType['id'].eq(tableActionProperty['id']), tablePropertyType['value'].trim()+' IS NOT NULL']))
                        cols.append(tablePropertyType['value'].alias('value'+typeName))
                        queryTable = queryTableProperty
                if len(cols) > 4:
                    order = [u'Action.endDate DESC']
                    records = db.getDistinctRecordList(queryTable, cols, cond, order)
                    for record in records:
                        templateId = forceRef(record.value('template_id'))
                        endDate = forceDate(record.value('endDate'))
                        if templateId and endDate:
                            typeName = forceString(record.value('typeName'))
                            valueDomain = forceString(record.value('valueDomain'))
                            value = record.value('value'+typeName)
                            propertyType = CActionPropertyValueTypeRegistry.get(typeName, valueDomain)
                            if propertyType:
                                valueProperty = propertyType.convertQVariantToPyValue(value) if type(value) == QVariant else value
                                if valueProperty:
                                    if type(valueProperty) is int:
                                        reportLine = self.items.setdefault(templateId, (0, None))
                                        if not reportLine[1] or reportLine[1] < endDate:
                                            reportLine = (valueProperty, endDate)
                                            self.items[templateId] = reportLine
                                    elif type(valueProperty) is float:
                                        reportLine = self.items.setdefault(templateId, (0.0, None))
                                        if not reportLine[1] or reportLine[1] < endDate:
                                            reportLine = (valueProperty, endDate)
                                            self.items[templateId] = reportLine


        def setValue(self, value):
            CRBComboBox.setValue(self, forceRef(value))


    @staticmethod
    def convertDBValueToPyValue(value):
        val = forceRef(value)
        if val:
            return val
        return None

    convertQVariantToPyValue = convertDBValueToPyValue


    def toText(self, v):
        return forceString(QtGui.qApp.db.translate('ActionPropertyTemplate', 'id', v, 'code'))


    def toInfo(self, context, v):
        from Events.ActionInfo import CActionPropertyTemplateInfo
        return CActionPropertyTemplateInfo(context, forceRef(v))


    @classmethod
    def getTableName(cls):
        return cls.tableNamePrefix + 'ActionPropertyTemplate'

