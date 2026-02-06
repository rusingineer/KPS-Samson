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
from PyQt4.QtCore import SIGNAL ,QDate

from library.DialogBase import CDialogBase
from library.Utils      import forceString, formatName
from Events.ActionProperty.NomenclatureActionPropertyValueType import CNomenclatureActionPropertyValueType
from Events.ActionProperty.FeatureActionPropertyValueType      import CFeatureActionPropertyValueType
from Reports.ReportBase         import CReportBase, createTable
from Reports.Report             import CReport
from Stock.NomenclatureComboBox import getFeaturesAndValues

from Reports.Ui_ReportClientNomenclaturePlanSetup import Ui_ReportClientNomenclaturePlanSetupDialog

def selectData(params):
    begDate = params.get('begDate', None)
    endDate = params.get('endDate', None)

    dateFieldName = {
                     0 : 'endDate',
                     1 : 'directionDate',
                     2 : 'begDate',
                     3 : 'plannedEndDate'
                    }.get(params.get('actionDateType', 0), 'endDate')

    setOrgStructureId = params.get('setOrgStructureId', None)
    execOrgStructureId = params.get('orgStructureId', None)

    financeId = params.get('financeId', None)
    socStatusTypeId = params.get('socStatusTypeId', None)
    socStatusClassId = params.get('socStatusClassId', None)
    eventPurposeId = params.get('eventPurposeId', None)
    eventResultId = params.get('eventResultId', None)
    nomenclatureTypeId = params.get('nomenclatureTypeId', None)

    db = QtGui.qApp.db

    tableAction = db.table('Action')
    tableActionType = db.table('ActionType')
    tableActionPropertyTypeFeature = db.table('ActionPropertyType').alias('ActionPropertyTypeFeature')
    tableActionPropertyFeature = db.table('ActionProperty').alias('ActionPropertyFeature')
    tableActionPropertyTypeFeatureValue = db.table('ActionProperty_String')
    tableActionPropertyTypeNomenclature = db.table('ActionPropertyType').alias('ActionPropertyTypeNomenclature')
    tableActionPropertyNomenclature = db.table('ActionProperty').alias('ActionPropertyNomenclature')
    tableActionPropertyTypeNomenclatureValue = db.table('ActionProperty_rbNomenclature')
    tableNomenclature = db.table('rbNomenclature')
    tableEvent = db.table('Event')
    tableEventType = db.table('EventType')
    tableClient = db.table('Client')
    tableExecPerson = db.table('Person').alias('ExecPerson')
    tableSetPerson = db.table('Person').alias('SetPerson')
    tableClientRegAddress = db.table('ClientAddress').alias('ClientRegAddress')
    tableRegAddress = db.table('Address').alias('RegAddress')
    tableRegAddressHouse = db.table('AddressHouse').alias('RegAddressHouse')
    tableClientLocAddress = db.table('ClientAddress').alias('ClientLocAddress')
    tableLocAddress = db.table('Address').alias('LocAddress')
    tableLocAddressHouse = db.table('AddressHouse').alias('LocAddressHouse')

    queryTable = tableAction

    queryTable = queryTable.leftJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
    queryTable = queryTable.innerJoin(tableActionPropertyTypeFeature,
                                      [tableActionPropertyTypeFeature['actionType_id'].eq(tableActionType['id']),
                                       tableActionPropertyTypeFeature['typeName'].eq(CFeatureActionPropertyValueType.name)])
    queryTable = queryTable.leftJoin(tableActionPropertyFeature,
                                     [tableActionPropertyFeature['type_id'].eq(tableActionPropertyTypeFeature['id']),
                                      tableActionPropertyFeature['action_id'].eq(tableAction['id'])])
    queryTable = queryTable.leftJoin(tableActionPropertyTypeFeatureValue,
                                     tableActionPropertyTypeFeatureValue['id'].eq(tableActionPropertyFeature['id']))
    queryTable = queryTable.innerJoin(tableActionPropertyTypeNomenclature,
                                      [tableActionPropertyTypeNomenclature['actionType_id'].eq(tableActionType['id']),
                                       tableActionPropertyTypeNomenclature['typeName'].eq(CNomenclatureActionPropertyValueType.name)])
    queryTable = queryTable.leftJoin(tableActionPropertyNomenclature,
                                     [tableActionPropertyNomenclature['type_id'].eq(tableActionPropertyTypeNomenclature['id']),
                                      tableActionPropertyNomenclature['action_id'].eq(tableAction['id'])])
    queryTable = queryTable.leftJoin(tableActionPropertyTypeNomenclatureValue,
                                     tableActionPropertyTypeNomenclatureValue['id'].eq(tableActionPropertyNomenclature['id']))
    queryTable = queryTable.leftJoin(tableNomenclature, tableNomenclature['id'].eq(tableActionPropertyTypeNomenclatureValue['value']))
    queryTable = queryTable.leftJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))
    queryTable = queryTable.leftJoin(tableClient, tableClient['id'].eq(tableEvent['client_id']))
    queryTable = queryTable.leftJoin(tableClientRegAddress, 'ClientRegAddress.`id`=getClientRegAddressId(Client.`id`)')
    queryTable = queryTable.leftJoin(tableRegAddress, tableRegAddress['id'].eq(tableClientRegAddress['address_id']))
    queryTable = queryTable.leftJoin(tableRegAddressHouse, tableRegAddressHouse['id'].eq(tableRegAddress['house_id']))
    queryTable = queryTable.leftJoin(tableClientLocAddress, 'ClientLocAddress.`id`=getClientLocAddressId(Client.`id`)')
    queryTable = queryTable.leftJoin(tableLocAddress, tableLocAddress['id'].eq(tableClientLocAddress['address_id']))
    queryTable = queryTable.leftJoin(tableLocAddressHouse, tableLocAddressHouse['id'].eq(tableLocAddress['house_id']))


    cond = [tableAction['deleted'].eq(0),
            tableEvent['deleted'].eq(0),
            tableActionType['deleted'].eq(0),
            tableActionPropertyTypeNomenclature['deleted'].eq(0),
            tableActionType['isNomenclatureExpense'].eq(1),
#            db.joinOr([tableNomenclature['name'].isNotNull(),
#                       tableActionPropertyTypeFeatureValue['value'].isNotNull()])
            ]

    if begDate:
        cond.append(tableAction[dateFieldName].ge(begDate))

    if endDate:
        cond.append(tableAction[dateFieldName].lt(endDate.addDays(1)))

    if setOrgStructureId:
        queryTable = queryTable.leftJoin(tableSetPerson, tableSetPerson['id'].eq(tableEvent['setPerson_id']))
        cond.append(tableSetPerson['orgStructure_id'].inlist(db.getDescendants('OrgStructure', 'parent_id', setOrgStructureId)))

    if execOrgStructureId:
        queryTable = queryTable.leftJoin(tableExecPerson, tableExecPerson['id'].eq(tableEvent['setPerson_id']))
        cond.append(tableExecPerson['orgStructure_id'].inlist(db.getDescendants('OrgStructure', 'parent_id', execOrgStructureId)))

    if financeId:
        cond.append(tableAction['finance_id'].eq(financeId))

    if eventPurposeId:
        queryTable = queryTable.leftJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
        cond.append(tableEventType['purpose_id'].eq(eventPurposeId))

    if eventResultId:
        cond.append(tableEvent['result_id'].eq(eventResultId))

    if socStatusTypeId and socStatusClassId:
        cond.append(db.existsStmt('ClientSocStatus', 'ClientSocStatus.client_id=Client.id AND ClientSocStatus.socStatusType_id=%d AND ClientSocStatus.socStatusClass_id=%d'%(socStatusTypeId, socStatusClassId)))
    elif socStatusTypeId:
        cond.append(db.existsStmt('ClientSocStatus', 'ClientSocStatus.client_id=Client.id AND ClientSocStatus.socStatusType_id=%d'%socStatusTypeId))
    elif socStatusClassId:
        cond.append(db.existsStmt('ClientSocStatus', 'ClientSocStatus.client_id=Client.id AND ClientSocStatus.socStatusClass_id=%d'%socStatusClassId))

    if nomenclatureTypeId:
        cond.append(tableNomenclature['type_id'].eq(nomenclatureTypeId))

    fields = [tableAction['begDate'].alias('actionBegDate'),
              tableAction['endDate'].alias('actionEndDate'),
              tableClient['id'].alias('clientId'),
              tableClient['firstName'].name(),
              tableClient['lastName'].name(),
              tableClient['patrName'].name(),
              tableClient['birthDate'].name(),
              'kladr.`getDistrict`(RegAddressHouse.`KLADRCode`, RegAddressHouse.`KLADRStreetCode`, RegAddressHouse.`number`) AS regDistrict',
              'kladr.`getDistrict`(LocAddressHouse.`KLADRCode`, LocAddressHouse.`KLADRStreetCode`, LocAddressHouse.`number`) AS locDistrict',
              'getClientRegAddress(Client.`id`) AS clientRegAddress',
              'getClientLocAddress(Client.`id`) AS clientLocAddress',
              tableNomenclature['name'].alias('nomenclatureName'),
              tableActionPropertyTypeFeatureValue['value'].alias('feature')]

    order = [tableAction[dateFieldName].name()]

    stmt = db.selectStmt(queryTable, fields, cond, order)
#    print stmt
    return db.query(stmt)


class CReportClientNomenclaturePlan(CReport):
    def __init__(self, parent = None):
        CReport.__init__(self, parent)
        self.setTitle(u'Планирование выдачи ТМЦ')


    def getSetupDialog(self, parent):
        result = CReportClientNomenclaturePlanSetupDialog(parent)
        result.setTitle(self.title())
        return result

    def structQuery(self, query, params):
        featureName = params.get('nomenclatureFeatureName', '')
        featureValue = params.get('nomenclatureFeatureValue', '')
        featureNameIndex = params.get('nomenclatureFeatureNameIndex', 0)
        featureValueIndex = params.get('nomenclatureFeatureValueIndex', 0)

        def _featureValue2Text(feature):
            try:
                result = []
                nameList = []
                valueList = []
                listKeyValueMaps = CFeatureActionPropertyValueType.parseValue(feature)
                for name, value in listKeyValueMaps:
                    result.append(u'%s:%s' % (name, value))
                    nameList.append(name)
                    valueList.append(value)
                return '\n'.join(result), nameList, valueList
            except:
                return u'<ошибка формата данных>', [], []

        reportData = []
        while query.next():
            record = query.record()

            feature, nameList, valueList = _featureValue2Text(forceString(record.value('feature')))

            if featureNameIndex and featureName:
                if not featureName in nameList:
                    continue
            if featureValueIndex and featureValue:
                if not featureValue in valueList:
                    continue


            actionBegDate = forceString(record.value('actionBegDate'))
            actionEndDate = forceString(record.value('actionEndDate'))
            clientId = forceString(record.value('clientId'))
            clientName = formatName(record.value('lastName'),
                                    record.value('firstName'),
                                    record.value('patrName'))
            clientBirthDate = forceString(record.value('birthDate'))
            regDistrict = forceString(record.value('regDistrict'))
            locDistrict = forceString(record.value('locDistrict'))
            clientRegAddress = forceString(record.value('clientRegAddress'))
            clientLocAddress = forceString(record.value('clientLocAddress'))
            nomenclatureName = forceString(record.value('nomenclatureName'))

            if clientRegAddress:
                address = u', '.join([clientRegAddress, regDistrict])
            else:
                address = u', '.join([clientLocAddress, locDistrict])

            client = u', '.join([clientId, clientName, clientBirthDate, address])

            nomenclature = u'\n'.join([u'Название: %s\n'%nomenclatureName, u'Характеристика\n%s'%feature])

            reportData.append((actionBegDate, actionEndDate, client, nomenclature))

        return reportData


    def build(self, params):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()

        tableColumns = [
                        ('%2',
                        [u'№'], CReportBase.AlignRight),
                        ('%8',
                        [u'Дата назначения'], CReportBase.AlignLeft),
                        ('%8',
                        [u'Дата выдачи'], CReportBase.AlignLeft),
                        ('%30',
                        [u'Пациент'], CReportBase.AlignLeft),
                        ('%30',
                        [u'ТМЦ'], CReportBase.AlignLeft)
                       ]


        table = createTable(cursor, tableColumns)

        query = selectData(params)
        reportData = self.structQuery(query, params)

        for reportLine in reportData:
            reportRow = table.addRow()
            table.setText(reportRow, 0, reportRow)
            for valueIdx, reportValue in enumerate(reportLine):
                table.setText(reportRow, valueIdx+1, reportValue)

        return doc


class CReportClientNomenclaturePlanSetupDialog(CDialogBase, Ui_ReportClientNomenclaturePlanSetupDialog):
    def __init__(self, parent):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)

        self.cmbFinance.setTable('rbFinance', addNone=True)
        self.cmbSocStatusClass.setTable('rbSocStatusClass', addNone=True)
        self.cmbSocStatusType.setTable('vrbSocStatusType', addNone=True, filter='class_id IS NULL')
        self.cmbEventPurpose.setTable('rbEventTypePurpose', addNone=True)
        self.cmbEventResult.setTable('rbResult', addNone=True)
        self.cmbNomenclatureType.setTable('rbNomenclatureType', addNone=True)

        self.connect(self.cmbSocStatusClass, SIGNAL('currentIndexChanged(int)'), self.on_cmbSocStatusClassChanged)
        self.connect(self.cmbNomenclatureType, SIGNAL('currentIndexChanged(int)'), self.on_cmbNomenclatureType)
        self.connect(self.cmbNomenclatureFeatureName, SIGNAL('currentIndexChanged(int)'), self.on_cmbNomenclatureFeatureName)
        self.connect(self.cmbEventPurpose, SIGNAL('currentIndexChanged(int)'), self.on_cmbEventPurpose)

        self._mapType2FeatureValues = {}

        self.on_cmbNomenclatureType(self.cmbNomenclatureType.currentIndex())


    def _getFeatureValues(self, nomenclatureTypeId):
        if nomenclatureTypeId not in self._mapType2FeatureValues.keys():
            self._mapType2FeatureValues[nomenclatureTypeId] = getFeaturesAndValues(typeId=nomenclatureTypeId)
        return self._mapType2FeatureValues[nomenclatureTypeId]


    def _updateFeatureNameComboBox(self, featureNameList):
        self.cmbNomenclatureFeatureName.clear()
        self.cmbNomenclatureFeatureName.addItems([u'Не задано']+featureNameList)
        self.on_cmbNomenclatureFeatureName(self.cmbNomenclatureFeatureName.currentIndex())

    def on_cmbNomenclatureFeatureName(self, index):
        self.cmbNomenclatureFeatureValue.clear()
#        nomenclatureTypeId = self.cmbNomenclatureType.value()
#        if nomenclatureTypeId:
#            featureName = unicode(self.cmbNomenclatureFeatureName.itemText(index))
#            self.cmbNomenclatureFeatureValue.addItems([u'Не задано']+self._getFeatureValues(nomenclatureTypeId).get(featureName, []))
        featureName = unicode(self.cmbNomenclatureFeatureName.itemText(index))
        self.cmbNomenclatureFeatureValue.addItems([u'Не задано']+self._getFeatureValues(self.cmbNomenclatureType.value()).get(featureName, []))

    def on_cmbNomenclatureType(self, index):
#        nomenclatureTypeId = self.cmbNomenclatureType.value()
#        self.cmbNomenclatureFeatureName.setEnabled(bool(nomenclatureTypeId))
#        self.cmbNomenclatureFeatureValue.setEnabled(bool(nomenclatureTypeId))
#        if nomenclatureTypeId:
#            self._updateFeatureNameComboBox(self._getFeatureValues(nomenclatureTypeId).keys())
#        else:
#            self.cmbNomenclatureFeatureName.clear()
#            self.cmbNomenclatureFeatureValue.clear()
        self._updateFeatureNameComboBox(self._getFeatureValues(self.cmbNomenclatureType.value()).keys())

    def on_cmbEventPurpose(self, index):
        eventPurposeId = self.cmbEventPurpose.value()
        filter = u'eventPurpose_id=%d'%eventPurposeId if eventPurposeId else u''
        self.cmbEventResult.setFilter(filter)


    def on_cmbSocStatusClassChanged(self, index):
        socStatusClassId = self.cmbSocStatusClass.value()
        filter = 'class_id = %d' % socStatusClassId if socStatusClassId else 'class_id IS NULL'
        self.cmbSocStatusType.setFilter(filter)

    def setTitle(self, title):
        self.setWindowTitle(title)

    def setParams(self, params):
        date = QDate.currentDate()
        self.edtBegDate.setDate(params.get('begDate', date))
        self.edtEndDate.setDate(params.get('endDate', date))
        self.cmbDateType.setCurrentIndex(params.get('actionDateType', 0))
        self.cmbSetOrgStructure.setValue(params.get('setOrgStructureId', None))
        self.cmbOrgStructure.setValue(params.get('orgStructureId', None))
        self.cmbFinance.setValue(params.get('financeId', None))
        self.cmbSocStatusClass.setValue(params.get('socStatusClassId', None))
        self.cmbSocStatusType.setValue(params.get('socStatusTypeId', None))
        self.cmbEventPurpose.setValue(params.get('eventPurposeId', None))
        self.cmbEventResult.setValue(params.get('eventResultId', None))
        self.cmbNomenclatureType.setValue(params.get('nomenclatureTypeId'))
        self.cmbNomenclatureFeatureName.setCurrentIndex(params.get('nomenclatureFeatureNameIndex', 0))
        self.cmbNomenclatureFeatureValue.setCurrentIndex(params.get('nomenclatureFeatureValueIndex', 0))

    def params(self):
        result = {}
        result['begDate'] = self.edtBegDate.date()
        result['endDate'] = self.edtEndDate.date()
        result['actionDateType'] = self.cmbDateType.currentIndex()
        result['orgStructureId'] = self.cmbOrgStructure.value()
        result['setOrgStructureId'] = self.cmbSetOrgStructure.value()
        result['financeId'] = self.cmbFinance.value()
        result['socStatusClassId'] = self.cmbSocStatusClass.value()
        result['socStatusTypeId'] = self.cmbSocStatusType.value()
        result['eventPurposeId'] = self.cmbEventPurpose.value()
        result['eventResultId'] = self.cmbEventResult.value()
        result['nomenclatureTypeId'] = self.cmbNomenclatureType.value()
        result['nomenclatureFeatureNameIndex'] = self.cmbNomenclatureFeatureName.currentIndex()
        result['nomenclatureFeatureValueIndex'] = self.cmbNomenclatureFeatureValue.currentIndex()
        result['nomenclatureFeatureName'] = unicode(self.cmbNomenclatureFeatureName.currentText())
        result['nomenclatureFeatureValue'] = unicode(self.cmbNomenclatureFeatureValue.currentText())
        return result


