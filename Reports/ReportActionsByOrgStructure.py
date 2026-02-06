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
from PyQt4.QtCore import pyqtSignature, QDate, QDateTime

from library.Utils       import firstMonthDay, forceDate, forceDouble, forceInt, forceRef, forceString, formatName, lastMonthDay, smartDict
from Events.ActionStatus import CActionStatus
from Orgs.Utils          import getOrgStructureFullName

from Reports.Report      import CReport
from Reports.ReportBase  import CReportBase, createTable

from Ui_ReportSetupByOrgStructure import Ui_ReportSetupByOrgStructureDialog


def selectData(params):
    dateFieldsName     = {0:'directionDate', 1:'begDate', 2:'endDate'}.get(params.get('dateType', 0))
    begDate            = params.get('begDate', None)
    endDate            = params.get('endDate', None)
    chkStatus          = params.get('chkStatus', False)
    personId           = params.get('personId', None)
    chkPerson          = params.get('chkPerson', False)
    status             = params.get('status', None)
    reportType         = params.get('reportType', None)
    chkPatientInfo     = params.get('chkPatientInfo', False)
    chkExecDateInfo    = params.get('chkExecDateInfo', False)
    contractIdList     = params.get('contractIdList', [])
    financeId          = params.get('financeId', None)
    confirmation       = params.get('confirmation', False)
    confirmationBegDate = params.get('confirmationBegDate', None)
    confirmationEndDate = params.get('confirmationEndDate', None)
    confirmationType    = params.get('confirmationType', 0)
    confirmationPeriodType = params.get('confirmationType', 0)
    chkCoefficient      = params.get('chkCoefficient', False)
    if reportType is None:
        return None
    db = QtGui.qApp.db
    tableAction            = db.table('Action')
    tableActionType        = db.table('ActionType')
    tableActionTypeService = db.table('ActionType_Service')
    tablePerson            = db.table('Person')
    tableOrgStructure      = db.table('OrgStructure')
    tableOrgStructurePerson = db.table('OrgStructure').alias('OrgStructurePerson')
    tableContract          = db.table('Contract')
    tablePriceList          = db.table('Contract').alias('ContractPriceList')
    tableContractTariff    = db.table('Contract_Tariff')
    tableClient            = db.table('Client')
    tableEvent             = db.table('Event')
#    tableEventType         = db.table('EventType')
    tableSpeciality        = db.table('rbSpeciality')
    tableMedicalAidUnit    = db.table('rbMedicalAidUnit')
    tableOrgStructureActionType = db.table('OrgStructure_ActionType')
    contractTariffCond = 'IF(ActionType_Service.`finance_id`, ActionType_Service.`finance_id`=Contract.`finance_id`, ActionType_Service.`finance_id` IS NULL)'
    cond = [tableAction['deleted'].eq(0),
            tableEvent['deleted'].eq(0),
            u'Contract_Tariff.`service_id`=ActionType_Service.service_id',
            contractTariffCond
            ]
    if contractIdList:
        cond.append(tableContract['id'].inlist(contractIdList))
    if financeId:
        cond.append(tableContract['finance_id'].eq(financeId))
    cond.append(tableAction[dateFieldsName].isNotNull())
    cond.append(tableAction[dateFieldsName].lt(endDate.addDays(1)))
    cond.append(tableAction[dateFieldsName].ge(begDate))
    if chkStatus and status is not None:
        cond.append(tableAction['status'].eq(status))
    if chkStatus == CActionStatus.finished:
        cond.append(tableAction['endDate'].isNotNull())
        cond.append(tableAction['endDate'].ge(begDate))
    if personId and chkPerson:
        cond.append(tableAction['person_id'].eq(personId))
    fields = [tableAction['modifyDatetime'].name(),
              tableAction[dateFieldsName].alias('endDate'),
              tableAction['id'].name(),
              tableActionType['id'].alias('actionTypeId'),
              tableActionType['code'].name(),
              tableActionType['name'].name(),
              tableAction['amount'].name(),
              tableOrgStructure['id'].alias('orgStructureId'),
              tableOrgStructure['name'].alias('orgStructureName'),
              tableContractTariff['price'].name(),
              tableContractTariff['VAT'],
              tableMedicalAidUnit['id'].alias('medicalAidUnitId'),
              tableMedicalAidUnit['name'].alias('unitName'),
              tablePerson['id'].alias('personId'),
              tablePerson['code'].alias('personCode'),
              tablePerson['lastName'].alias('lastNamePerson'),
              tablePerson['firstName'].alias('firstNamePerson'),
              tablePerson['patrName'].alias('patrNamePerson'),
              tableSpeciality['id'].alias('specialityId'),
              tableSpeciality['name'].alias('specialityName'),
              tableOrgStructurePerson['code'].alias('orgStructureCode') if reportType else tableOrgStructure['code'].alias('orgStructureCode')
              ]
    if chkPatientInfo:
        clientFields = [tableClient['lastName'].name(),
                        tableClient['firstName'].name(),
                        tableClient['patrName'].name()]
        fields.append(tableClient['id'].alias('clientId'))
        fields.extend(clientFields)
        order = clientFields
        if chkExecDateInfo:
            order.insert(0, tableAction['endDate'].name())
    elif chkExecDateInfo:
        order = [tableAction['endDate'].name()]
    else:
        order = [tableAction['begDate'].name()]
    queryTable = tableAction.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
    queryTable = queryTable.innerJoin(tableActionTypeService, tableActionType['id'].eq(tableActionTypeService['master_id']))
    queryTable = queryTable.innerJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))
    queryTable = queryTable.innerJoin(tableContract, 'Contract.`id`=IF(Action.`contract_id`, Action.`contract_id`, Event.`contract_id`)')
    queryTable = queryTable.leftJoin(tablePriceList, tableContract['priceListExternal_id'].eq(tablePriceList['id']))
    queryTable = queryTable.innerJoin(tableContractTariff, '''(Contract_Tariff.id = (SELECT MIN(CT.id)
                                                                                    FROM Contract_Tariff AS CT
                                                                                    WHERE
                                                                                    CT.deleted = 0
                                                                                    AND (CT.master_id = Contract.id OR CT.master_id = ContractPriceList.id)
                                                                                    AND CT.service_id = ActionType_Service.service_id
                                                                                    AND ((Person.tariffCategory_id IS NULL AND CT.tariffCategory_id IS NULL)
                                                                                         OR (CT.tariffCategory_id = Person.tariffCategory_id OR CT.tariffCategory_id IS NULL))
                                                                                    AND (CT.eventType_id = Event.eventType_id
                                                                                         OR CT.eventType_id IS NULL)
                                                                                    AND ((CT.age IS NULL AND (CT.sex = 0 OR CT.sex = Client.sex))
                                                                                        OR (CT.age IS NOT NULL
                                                                                        AND (SELECT isSexAndAgeSuitable(Client.sex, Client.birthDate, CT.sex, CT.age, Action.begDate))))
                                                                                    AND ((CT.begDate IS NULL OR CT.begDate <= IF(Action.endDate IS NULL, Action.begDate,Action.endDate))
                                                                                    AND (CT.endDate IS NULL OR CT.endDate >= IF(Action.endDate IS NULL, Action.begDate,Action.endDate)))                                                                                                                                                         
                                                                                    AND ((CT.result_id = Event.result_id) OR (CT.result_id IS NULL OR Event.result_id IS NULL))
                                                                                    AND ((CT.MKB IS NULL OR ((Action.MKB IS NOT NULL AND CT.MKB = Action.MKB)
                                                                                        OR (Action.MKB IS NULL AND CT.MKB = (SELECT Diagnosis.MKB
                                                                                    FROM Diagnosis INNER JOIN Diagnostic ON Diagnostic.diagnosis_id=Diagnosis.id
                                                                                    INNER JOIN rbDiagnosisType ON Diagnostic.diagnosisType_id=rbDiagnosisType.id
                                                                                    WHERE Diagnostic.event_id = Event.id AND Diagnosis.deleted = 0 AND Diagnostic.deleted = 0
                                                                                    AND (rbDiagnosisType.code = '1'
                                                                                    OR (rbDiagnosisType.code = '2' AND Diagnostic.person_id = Event.execPerson_id
                                                                                    AND (NOT EXISTS (SELECT DC.id FROM Diagnostic AS DC
                                                                                    INNER JOIN rbDiagnosisType AS DT ON DT.id = DC.diagnosisType_id WHERE DT.code = '1'
                                                                                    AND DC.event_id = Event.id
                                                                                    LIMIT 1)))) LIMIT 1)))))
                                                                                    )
                                                              AND Contract_Tariff.deleted = 0)''')
    queryTable = queryTable.leftJoin(tableMedicalAidUnit, tableMedicalAidUnit['id'].eq(tableContractTariff['unit_id']))
    queryTable = queryTable.innerJoin(tableClient, tableClient['id'].eq(tableEvent['client_id']))
    if reportType == 0:
        queryTable = queryTable.leftJoin(tablePerson, tablePerson['id'].eq(tableAction['person_id']))
        queryTable = queryTable.leftJoin(tableOrgStructure, tableOrgStructure['id'].eq(tablePerson['orgStructure_id']))
    elif reportType == 1:
        queryTable = queryTable.leftJoin(tableOrgStructureActionType,
            tableOrgStructureActionType['actionType_id'].eq(tableActionType['id']))
        queryTable = queryTable.leftJoin(tableOrgStructure,
            tableOrgStructure['id'].eq(tableOrgStructureActionType['master_id']))
        queryTable = queryTable.leftJoin(tablePerson, db.joinAnd([tablePerson['id'].eq(tableAction['person_id']),
                                                                  tablePerson['deleted'].eq(0)]))
        queryTable = queryTable.leftJoin(tableOrgStructurePerson, db.joinAnd([tableOrgStructurePerson['id'].eq(tablePerson['orgStructure_id']),
                                                                              tableOrgStructurePerson['deleted'].eq(0)]))
    queryTable = queryTable.leftJoin(tableSpeciality, tableSpeciality['id'].eq(tablePerson['speciality_id']))
    if chkCoefficient:
        tableContractCoefficient = db.table('Contract_Coefficient')
        tableContractCoefficientType  = db.table('rbContractCoefficientType')
        queryTable = queryTable.leftJoin(tableContractCoefficient,
                                         (db.joinAnd([tableContractCoefficient['master_id'].eq(tableContract['id']),
                                                     tableContractCoefficient['deleted'].eq(0),
                                                     db.joinOr([tableContractCoefficient['begDate'].isNull(),
                                                                tableContractCoefficient['begDate'].le(endDate)])])))
        queryTable = queryTable.leftJoin(tableContractCoefficientType, tableContractCoefficientType['id'].eq(tableContractCoefficient['coefficientType_id']))
        fields.append(tableContractCoefficient['value'].alias('coefficientValue'))
        fields.append(tableContractCoefficientType['code'].alias('coefficientCode'))
        fields.append(tableContractCoefficientType['name'].alias('coefficientName'))
        fields.append(tableContractCoefficientType['id'].alias('coefficientTypeId'))
        order.append(tableActionType['code'].name())
        order.append(tableActionType['name'].name())
    if confirmation:
        tableAccountItem = db.table('Account_Item')
        queryTable = queryTable.leftJoin(tableAccountItem, tableAccountItem['action_id'].eq(tableAction['id']))
        cond.append(tableAccountItem['deleted'].eq(0))
        if confirmationType == 0:
            cond.append(tableAccountItem['id'].isNull())
        elif confirmationType == 1:
            cond.append(tableAccountItem['date'].isNotNull())
            cond.append(tableAccountItem['number'].ne(''))
        elif confirmationType == 2:
            cond.append(tableAccountItem['date'].isNotNull())
            cond.append(tableAccountItem['number'].ne(''))
            cond.append(tableAccountItem['refuseType_id'].isNull())
        elif confirmationType == 3:
            cond.append(tableAccountItem['date'].isNotNull())
            cond.append(tableAccountItem['number'].ne(''))
            cond.append(tableAccountItem['refuseType_id'].isNotNull())
        if confirmationPeriodType:
            if confirmationBegDate:
                cond.append(tableAccountItem['date'].ge(confirmationBegDate))
            if confirmationEndDate:
                cond.append(tableAccountItem['date'].lt(confirmationEndDate.addDays(1)))
        else:
            tableAccount = db.table('Account')
            queryTable = queryTable.leftJoin(tableAccount, tableAccount['id'].eq(tableAccountItem['master_id']))
            cond.append(tableAccount['deleted'].eq(0))
            if confirmationBegDate:
                cond.append(tableAccount['date'].ge(confirmationBegDate))
            if confirmationEndDate:
                cond.append(tableAccount['date'].lt(confirmationEndDate.addDays(1)))

    order.append(u'personCode')
    order.append(tablePerson['lastName'].name())
    order.append(tablePerson['firstName'].name())
    order.append(tablePerson['patrName'].name())
    order.append(u'specialityName')
    order.append(u'orgStructureCode')
    stmt = db.selectStmt(queryTable, fields, cond, order)
    query = db.query(stmt)
    return query


class CReportActionsByOrgStructure(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Отчет по отделениям')
        self.resetHelpers()
        self._orgStructureHelperModel = None

    def resetHelpers(self):
        self._mapRowValues = {}
        self._mapOrgStructureIdToFullName = {}
        self._actualOrgStructureIdListByStrongOrgStructure = []


    def getSetupDialog(self, parent):
        result = CSetupReport(parent)
        result.setDateTypeVisible(True)
        result.setSetupByOrgStructureVisible(True)
        result.setStrongOrgStructureVisible(True)
        result.setPersonVisible(True)
        result.setDetailExecPersonVisible(True)
        result.setTitle(self.title())
        self._orgStructureHelperModel = result.getOrgStructureModel()
        return result


    def build(self, params):
        self.resetHelpers()
        chkExecDateInfo = params.get('chkExecDateInfo', False)
        chkPatientInfo = params.get('chkPatientInfo', False)
        chkCoefficient = params.get('chkCoefficient', False)
        isDetailExecPerson = params.get('isDetailExecPerson', False)
        query = selectData(params)
        doc = QtGui.QTextDocument()
        if not query:
            doc
        self.makeStructAction(query, params)

        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()

        tableColumns = [
                        ('%2',
                        [u'№'], CReportBase.AlignRight),
                        ('%5',
                        [u'Код услуги'], CReportBase.AlignLeft),
                        ('%5',
                        [u'Наименование услуги'], CReportBase.AlignLeft),
                        ('%2',
                        [u'Ед.измерения'], CReportBase.AlignLeft),
                        ('%2',
                        [u'Количество'], CReportBase.AlignLeft),
#                        ('%3', [u'ФИО врача выполнившего услугу'], CReportBase.AlignLeft),
#                        ('%5', [u'Специальность врача'], CReportBase.AlignLeft),
#                        ('%3', [u'Отделение врача'], CReportBase.AlignLeft),
                        ('%5',
                        [u'Сумма'], CReportBase.AlignLeft)
                        ]
        if isDetailExecPerson:
            tableColumns.insert(5, ('%3', [u'ФИО врача выполнившего услугу'], CReportBase.AlignLeft))
            tableColumns.insert(6, ('%5', [u'Специальность врача'], CReportBase.AlignLeft))
            tableColumns.insert(7, ('%3', [u'Отделение врача'], CReportBase.AlignLeft))
        if chkPatientInfo:
            tableColumns.insert(4, ('%5', [u'Пациент'], CReportBase.AlignLeft))
            if chkExecDateInfo:
                tableColumns.insert(1, ('%5', [u'Дата исполнения'], CReportBase.AlignLeft))
        if chkExecDateInfo and not chkPatientInfo:
            tableColumns.insert(1, ('%5', [u'Дата исполнения'], CReportBase.AlignLeft))
        if chkCoefficient:
            tableColumns.append(('%5',[u'Наименование коэффициента'], CReportBase.AlignLeft))
            tableColumns.append(('%5',[u'Коэффициент'], CReportBase.AlignLeft))
            tableColumns.append(('%5',[u'Значение коэффициента'], CReportBase.AlignLeft))
            tableColumns.append(('%5',[u'Итого'], CReportBase.AlignLeft))

        table = createTable(cursor, tableColumns)

        boldChars = QtGui.QTextCharFormat()
        boldChars.setFontWeight(QtGui.QFont.Bold)

        if chkCoefficient:
            result = [0, 0, 0]
        else:
            result = [0, 0]

        keys = self._mapRowValues.keys()
        if chkPatientInfo:
            if chkExecDateInfo:
                keys.sort(key=lambda item: (item[0], item[len(keys)-1], item[3]))
            else:
                keys.sort(key=lambda item: (item[0], item[3]))
        elif chkExecDateInfo:
            keys.sort(key=lambda item: (item[0], item[len(keys)-1]))
        else:
            keys.sort(key=lambda item: item[0])

        previousOrgStructure = None
        rowShift = 1
        columnCount = len(tableColumns)
        needAddRowAfterOrgStructure = False
        if chkCoefficient:
            orgStructureResult = [0, 0, 0]
        else:
            orgStructureResult = [0, 0]
        noneOrgStructurePassed = False
        rowKeySum = 1
        prevKeySum = ()
        prevActionTypeId = None
        if isDetailExecPerson:
            for keyDict in keys:
                currentOrgStructure = keyDict[0]
                currentActionTypeId = keyDict[1]
                needWriteNoneOrgStructure = (currentOrgStructure is None and not noneOrgStructurePassed)
                if currentOrgStructure != previousOrgStructure or needWriteNoneOrgStructure:
                    if needWriteNoneOrgStructure:
                        noneOrgStructurePassed = True
                    result = map(lambda x, y: x+y, result, orgStructureResult)
                    if previousOrgStructure:
                        i = table.addRow()
                        table.setText(i, 6 if (chkPatientInfo and chkExecDateInfo) else (5 if (chkPatientInfo or chkExecDateInfo) else 4), orgStructureResult[0], charFormat=boldChars)
                        table.setText(i, 10 if chkPatientInfo and chkExecDateInfo else (9 if (chkPatientInfo or chkExecDateInfo) else 8), '%s'%(round(float(orgStructureResult[1]),2)), charFormat=boldChars)
                        table.mergeCells(i, 0, 1, 6 if chkPatientInfo and chkExecDateInfo else (5 if chkPatientInfo else 3))
                        if chkCoefficient:
                            table.setText(i, 14 if (chkPatientInfo and chkExecDateInfo) else (13 if chkPatientInfo else 12), orgStructureResult[2], charFormat=boldChars)
                    i = table.addRow()
                    table.setText(i, 0, self._mapOrgStructureIdToFullName[currentOrgStructure], charFormat=boldChars, blockFormat=CReportBase.AlignCenter)
                    table.mergeCells(i, 0, 1, columnCount)
                    previousOrgStructure = currentOrgStructure
                    needAddRowAfterOrgStructure = True
                    if chkCoefficient:
                        orgStructureResult = [0, 0, 0]
                    else:
                        orgStructureResult = [0, 0]
                actionValues = self._mapRowValues[keyDict]
                if chkExecDateInfo or (chkExecDateInfo and chkPatientInfo):
                    actionValues.items().sort(key=lambda item: item[0])
                if needAddRowAfterOrgStructure:
                    i = table.addRow()
                table.setText(i, 0, rowShift)
                rowShift += 1
                len_Values = len(actionValues.values)
                for idx, value in enumerate(actionValues.values):
                    if chkPatientInfo and chkExecDateInfo and not chkCoefficient:
                        if idx == 5:
                            orgStructureResult[0] += value
                        elif idx == 9:
                            orgStructureResult[1] += value
                    elif (chkPatientInfo or chkExecDateInfo) and not chkCoefficient:
                        if idx == 4:
                            orgStructureResult[0] += value
                        elif idx == 8:
                            orgStructureResult[1] += value
                    elif not chkCoefficient:
                        if idx == 3:
                            orgStructureResult[0] += value
                        elif idx == 7:
                            orgStructureResult[1] += value
                    if chkCoefficient:
                        if idx in [len_Values - 5, len_Values - 4, len_Values - 3]:
                            table.setText(i, idx+1, value)
                        elif idx == len_Values - 2:
                            keySum = actionValues.values[len_Values - 2]
                            if prevKeySum != keySum or prevActionTypeId != currentActionTypeId:
                                prevActionTypeId = currentActionTypeId
                                prevKeySum = keySum
                                rowKeySum = i
                                priceSumCoefficient = self.sumCoefficientList.get((currentActionTypeId, keySum), 0.0)
                                table.setText(i, idx+1, priceSumCoefficient)
                                for idx in range(0, len_Values - 5):
                                    if (chkPatientInfo and chkExecDateInfo) and idx == 9:
                                        table.setText(i, idx+1, '%s'%(round(float(actionValues.values[idx]),2)))
                                    elif (chkPatientInfo or chkExecDateInfo) and not (chkPatientInfo and chkExecDateInfo) and idx == 8:
                                        table.setText(i, idx+1, '%s'%(round(float(actionValues.values[idx]),2)))
                                    elif (not (chkPatientInfo and chkExecDateInfo) and not (chkPatientInfo or chkExecDateInfo)) and idx == 7:
                                        table.setText(i, idx+1, '%s'%(round(float(actionValues.values[idx]),2)))
                                    else:
                                        table.setText(i, idx+1, actionValues.values[idx])
                                orgStructureResult[2] += priceSumCoefficient
                                if chkPatientInfo and chkExecDateInfo:
                                    orgStructureResult[0] += actionValues.values[5]
                                    orgStructureResult[1] += actionValues.values[9]
                                elif chkPatientInfo or chkExecDateInfo:
                                    orgStructureResult[0] += actionValues.values[4]
                                    orgStructureResult[1] += actionValues.values[8]
                                else:
                                    orgStructureResult[0] += actionValues.values[3]
                                    orgStructureResult[1] += actionValues.values[7]
                    else:
                        if (chkPatientInfo and chkExecDateInfo) and idx == 9:
                            table.setText(i, idx+1, '%s'%(round(float(value),2)))
                        elif (chkPatientInfo or chkExecDateInfo) and not (chkPatientInfo and chkExecDateInfo) and idx == 8:
                            table.setText(i, idx+1, '%s'%(round(float(value),2)))
                        elif (not (chkPatientInfo and chkExecDateInfo) and not (chkPatientInfo or chkExecDateInfo))  and idx == 7:
                            table.setText(i, idx+1, '%s'%(round(float(value),2)))
                        else:
                            table.setText(i, idx+1, value)
                if chkCoefficient:
                    table.mergeCells(rowKeySum, len_Values-1, i-rowKeySum+1, 1)
                    for idx in range(0, len_Values - 5):
                        table.mergeCells(rowKeySum, idx+1, i-rowKeySum+1, 1)

            i = table.addRow()
            table.setText(i, 6 if (chkPatientInfo and chkExecDateInfo) else (5 if (chkPatientInfo or chkExecDateInfo) else 4), orgStructureResult[0], charFormat=boldChars)
            table.setText(i, 10 if (chkPatientInfo and chkExecDateInfo) else (9 if (chkPatientInfo or chkExecDateInfo) else 8), '%s'%(round(float(orgStructureResult[1]),2)), charFormat=boldChars)
            table.mergeCells(i, 0, 1, 6 if (chkPatientInfo and chkExecDateInfo) else (5 if (chkPatientInfo or chkExecDateInfo) else 3))
            if chkCoefficient:
                table.setText(i, 14 if (chkPatientInfo and chkExecDateInfo) else (13 if (chkPatientInfo or chkExecDateInfo) else 12), orgStructureResult[2], charFormat=boldChars)

            result = map(lambda x, y: x+y, result, orgStructureResult)
            i = table.addRow()
            table.setText(i, 0, u'Итого', charFormat=boldChars)
            table.setText(i, 6 if (chkPatientInfo and chkExecDateInfo) else (5 if (chkPatientInfo or chkExecDateInfo) else 4), result[0], charFormat=boldChars)
            table.setText(i, 10 if (chkPatientInfo and chkExecDateInfo) else (9 if (chkPatientInfo or chkExecDateInfo) else 8), '%s'%(round(float(result[1]),2)), charFormat=boldChars)
            table.mergeCells(i, 0, 1, 6 if (chkPatientInfo and chkExecDateInfo) else (5 if (chkPatientInfo or chkExecDateInfo) else 3))
            if chkCoefficient:
                table.setText(i, 14 if (chkPatientInfo and chkExecDateInfo) else (13 if (chkPatientInfo or chkExecDateInfo) else 12), result[2], charFormat=boldChars)
        else:
            for keyDict in keys:
                currentOrgStructure = keyDict[0]
                currentActionTypeId = keyDict[1]
                needWriteNoneOrgStructure = (currentOrgStructure is None and not noneOrgStructurePassed)
                if currentOrgStructure != previousOrgStructure or needWriteNoneOrgStructure:
                    if needWriteNoneOrgStructure:
                        noneOrgStructurePassed = True
                    result = map(lambda x, y: x+y, result, orgStructureResult)
                    if previousOrgStructure:
                        i = table.addRow()
                        table.setText(i, 6 if (chkPatientInfo and chkExecDateInfo) else (5 if (chkPatientInfo or chkExecDateInfo) else 4), orgStructureResult[0], charFormat=boldChars)
                        table.setText(i, 7 if chkPatientInfo and chkExecDateInfo else (6 if (chkPatientInfo or chkExecDateInfo) else 5), '%s'%(round(float(orgStructureResult[1]),2)), charFormat=boldChars)
                        table.mergeCells(i, 0, 1, 6 if chkPatientInfo and chkExecDateInfo else (5 if chkPatientInfo else 3))
                        if chkCoefficient:
                            table.setText(i, 11 if (chkPatientInfo and chkExecDateInfo) else (10 if chkPatientInfo else 9), orgStructureResult[2], charFormat=boldChars)
                    i = table.addRow()
                    table.setText(i, 0, self._mapOrgStructureIdToFullName[currentOrgStructure], charFormat=boldChars, blockFormat=CReportBase.AlignCenter)
                    table.mergeCells(i, 0, 1, columnCount)
                    previousOrgStructure = currentOrgStructure
                    needAddRowAfterOrgStructure = True
                    if chkCoefficient:
                        orgStructureResult = [0, 0, 0]
                    else:
                        orgStructureResult = [0, 0]
                actionValues = self._mapRowValues[keyDict]
                if chkExecDateInfo or (chkExecDateInfo and chkPatientInfo):
                    actionValues.items().sort(key=lambda item: item[0])
                if needAddRowAfterOrgStructure:
                    i = table.addRow()
                table.setText(i, 0, rowShift)
                rowShift += 1
                len_Values = len(actionValues.values)
                for idx, value in enumerate(actionValues.values):
                    if chkPatientInfo and chkExecDateInfo and not chkCoefficient:
                        if idx == 5:
                            orgStructureResult[0] += value
                        elif idx == 6:
                            orgStructureResult[1] += value
                    elif (chkPatientInfo or chkExecDateInfo) and not chkCoefficient:
                        if idx == 4:
                            orgStructureResult[0] += value
                        elif idx == 5:
                            orgStructureResult[1] += value
                    elif not chkCoefficient:
                        if idx == 3:
                            orgStructureResult[0] += value
                        elif idx == 4:
                            orgStructureResult[1] += value
                    if chkCoefficient:
                        if idx in [len_Values - 5, len_Values - 4, len_Values - 3]:
                            table.setText(i, idx+1, value)
                        elif idx == len_Values - 2:
                            keySum = actionValues.values[len_Values - 2]
                            if prevKeySum != keySum or prevActionTypeId != currentActionTypeId:
                                prevActionTypeId = currentActionTypeId
                                prevKeySum = keySum
                                rowKeySum = i
                                priceSumCoefficient = self.sumCoefficientList.get((currentActionTypeId, keySum), 0.0)
                                table.setText(i, idx+1, priceSumCoefficient)
                                for idx in range(0, len_Values - 5):
                                    if (chkPatientInfo and chkExecDateInfo) and idx == 6:
                                        table.setText(i, idx+1, '%s'%(round(float(actionValues.values[idx]),2)))
                                    elif (chkPatientInfo or chkExecDateInfo) and not (chkPatientInfo and chkExecDateInfo) and idx == 5:
                                        table.setText(i, idx+1, '%s'%(round(float(actionValues.values[idx]),2)))
                                    elif (not (chkPatientInfo and chkExecDateInfo) and not (chkPatientInfo or chkExecDateInfo)) and idx == 4:
                                        table.setText(i, idx+1, '%s'%(round(float(actionValues.values[idx]),2)))
                                    else:
                                        table.setText(i, idx+1, actionValues.values[idx])
                                orgStructureResult[2] += priceSumCoefficient
                                if chkPatientInfo and chkExecDateInfo:
                                    orgStructureResult[0] += actionValues.values[5]
                                    orgStructureResult[1] += actionValues.values[6]
                                elif chkPatientInfo or chkExecDateInfo:
                                    orgStructureResult[0] += actionValues.values[4]
                                    orgStructureResult[1] += actionValues.values[5]
                                else:
                                    orgStructureResult[0] += actionValues.values[3]
                                    orgStructureResult[1] += actionValues.values[4]
                    else:
                        if (chkPatientInfo and chkExecDateInfo) and idx == 6:
                            table.setText(i, idx+1, '%s'%(round(float(value),2)))
                        elif (chkPatientInfo or chkExecDateInfo) and not (chkPatientInfo and chkExecDateInfo) and idx == 5:
                            table.setText(i, idx+1, '%s'%(round(float(value),2)))
                        elif (not (chkPatientInfo and chkExecDateInfo) and not (chkPatientInfo or chkExecDateInfo))  and idx == 4:
                            table.setText(i, idx+1, '%s'%(round(float(value),2)))
                        else:
                            table.setText(i, idx+1, value)
                if chkCoefficient:
                    table.mergeCells(rowKeySum, len_Values-1, i-rowKeySum+1, 1)
                    for idx in range(0, len_Values - 5):
                        table.mergeCells(rowKeySum, idx+1, i-rowKeySum+1, 1)

            i = table.addRow()
            table.setText(i, 6 if (chkPatientInfo and chkExecDateInfo) else (5 if (chkPatientInfo or chkExecDateInfo) else 4), orgStructureResult[0], charFormat=boldChars)
            table.setText(i, 7 if (chkPatientInfo and chkExecDateInfo) else (6 if (chkPatientInfo or chkExecDateInfo) else 5), '%s'%(round(float(orgStructureResult[1]),2)), charFormat=boldChars)
            table.mergeCells(i, 0, 1, 6 if (chkPatientInfo and chkExecDateInfo) else (5 if (chkPatientInfo or chkExecDateInfo) else 3))
            if chkCoefficient:
                table.setText(i, 11 if (chkPatientInfo and chkExecDateInfo) else (10 if (chkPatientInfo or chkExecDateInfo) else 9), orgStructureResult[2], charFormat=boldChars)

            result = map(lambda x, y: x+y, result, orgStructureResult)
            i = table.addRow()
            table.setText(i, 0, u'Итого', charFormat=boldChars)
            table.setText(i, 6 if (chkPatientInfo and chkExecDateInfo) else (5 if (chkPatientInfo or chkExecDateInfo) else 4), result[0], charFormat=boldChars)
            table.setText(i, 7 if (chkPatientInfo and chkExecDateInfo) else (6 if (chkPatientInfo or chkExecDateInfo) else 5), '%s'%(round(float(result[1]),2)), charFormat=boldChars)
            table.mergeCells(i, 0, 1, 6 if (chkPatientInfo and chkExecDateInfo) else (5 if (chkPatientInfo or chkExecDateInfo) else 3))
            if chkCoefficient:
                table.setText(i, 11 if (chkPatientInfo and chkExecDateInfo) else (10 if (chkPatientInfo or chkExecDateInfo) else 9), result[2], charFormat=boldChars)
        return doc


    def makeStructAction(self, query, params):
        # chkAllOrgStructure:: если True - при структурировании по подразделениям к которым относится действие, действие может относится ко многим подразделениям, а если False мы учитываем только первое.
        chkAllOrgStructure   = params.get('chkAllOrgStructure', False)
        chkPatientInfo       = params.get('chkPatientInfo', False)
        chkOrgStructure      = params.get('chkOrgStructure', False)
        strongOrgStructureId = params.get('orgStructureId', None)
        chkCoefficient       = params.get('chkCoefficient', False)
        chkExecDateInfo      = params.get('chkExecDateInfo', False)
        isDetailExecPerson   = params.get('isDetailExecPerson', False)
        isVAT                = params.get('isVAT', False)
        existsOrgStructureActions = []
        self.sumCoefficientList = {}
        while query.next():
            record = query.record()

            modifyDatetime   = forceDate(record.value('modifyDatetime'))
            endDate          = forceDate(record.value('endDate'))
            actionId         = forceRef(record.value('id'))
            actionTypeId     = forceRef(record.value('actionTypeId'))
            actionTypeCode   = forceString(record.value('code'))
            actionTypeName   = forceString(record.value('name'))
            amount           = forceInt(record.value('amount'))
            orgStructureId   = forceRef(record.value('orgStructureId'))
            price            = forceDouble(record.value('price'))
            unitSize         = forceString(record.value('unitName'))

            if isDetailExecPerson:
                personName       = formatName(
                                              record.value('lastNamePerson'),
                                              record.value('firstNamePerson'),
                                              record.value('patrNamePerson')
                                             )
                specialityName   = forceString(record.value('specialityName'))
                orgStructureCode = forceString(record.value('orgStructureCode'))

            if chkCoefficient:
                coefficientTypeId = forceRef(record.value('coefficientTypeId'))
                coefficientValue = forceDouble(record.value('coefficientValue'))
                coefficientName = forceString(record.value('coefficientName'))

            if chkAllOrgStructure:
                if chkCoefficient:
                    if (orgStructureId, actionId, coefficientTypeId) in existsOrgStructureActions:
                        print actionId, coefficientTypeId
                        continue
                    existsOrgStructureActions.append((orgStructureId, actionId, coefficientTypeId))
                else:
                    if (orgStructureId, actionId) in existsOrgStructureActions:
                        continue
                    existsOrgStructureActions.append((orgStructureId, actionId))
            else:
                if chkCoefficient:
                    if (actionId, coefficientTypeId) in existsOrgStructureActions:
                        print actionId, coefficientTypeId
                        continue
                    existsOrgStructureActions.append((actionId, coefficientTypeId))
                else:
                    if actionId in existsOrgStructureActions:
                        continue
                    existsOrgStructureActions.append(actionId)

            result, orgStructureId = self.orgStructureFilterByParams(chkOrgStructure,
                                                                     strongOrgStructureId,
                                                                     orgStructureId)
            if not result:
                continue

            fullOrgStructureName = self._mapOrgStructureIdToFullName.get(orgStructureId, None)
            if not fullOrgStructureName:
                if not orgStructureId:
                    if chkOrgStructure:
                        fullOrgStructureName = u'Головное подразделение'
                    else:
                        fullOrgStructureName = u'Подразделение не определено'
                else:
                    fullOrgStructureName = getOrgStructureFullName(orgStructureId)
                self._mapOrgStructureIdToFullName[orgStructureId] = fullOrgStructureName

            actionValues = smartDict()
            actionValues.actionId         = actionId
            actionValues.orgStructureId   = orgStructureId

            sum = price*amount
            if isVAT:
                VAT             = forceDouble(record.value('VAT'))
                sumIsVat = sum - (((price*VAT)/(100+VAT))*amount)
            else:
                sumIsVat = sum
            if isDetailExecPerson:
                values = [actionTypeCode, actionTypeName, unitSize, amount, personName, specialityName, orgStructureCode, sumIsVat]
            else:
                values = [actionTypeCode, actionTypeName, unitSize, amount, sumIsVat]
            if chkPatientInfo:
                clientName = formatName(
                                      record.value('lastName'),
                                      record.value('firstName'),
                                      record.value('patrName')
                                     )
                clientId = forceRef(record.value('clientId'))
                values.insert(3, clientName)
            if chkExecDateInfo:
                endDate = endDate if endDate else modifyDatetime
                values.insert(0, forceString(endDate))

            if chkCoefficient:
                sumCoefficient = sumIsVat*coefficientValue/100.0
                values.append(coefficientName)
                values.append(coefficientValue)
                values.append(sumCoefficient)
                keySum = tuple(values)
                sumBuff = self.sumCoefficientList.get((actionTypeId, keySum), 0)
                values.append(keySum)
                sumBuff += (sumIsVat + sumCoefficient)
                values.append(sumBuff)
                self.sumCoefficientList[(actionTypeId, keySum)] = sumBuff

            actionValues.values = values
            if isDetailExecPerson:
                if chkPatientInfo:
                    actualKey = (orgStructureId, actionTypeId, actionTypeCode, actionTypeName, unitSize, amount, personName, specialityName, clientId)
                else:
                    actualKey = (orgStructureId, actionTypeId, actionTypeCode, actionTypeName, unitSize, amount, personName, specialityName)
            else:
                if chkPatientInfo:
                    actualKey = (orgStructureId, actionTypeId, actionTypeCode, actionTypeName, unitSize, amount, clientId)
                else:
                    actualKey = (orgStructureId, actionTypeId, actionTypeCode, actionTypeName, unitSize, amount)

            if chkCoefficient:
                medkey = list(actualKey)
                medkey.append(coefficientTypeId)
                actualKey = tuple(medkey)
            if chkExecDateInfo or (chkExecDateInfo and chkPatientInfo):
                dateKey = list(actualKey)
                dateKey.append(endDate)
                actualKey = tuple(dateKey)
            existActionValues = self._mapRowValues.setdefault(actualKey, None)
            if existActionValues:
                if isDetailExecPerson:
                    if chkPatientInfo and chkExecDateInfo:
                        existActionValues.values[5] += actionValues.values[5]
                        existActionValues.values[9] += actionValues.values[9]
                        if chkCoefficient:
                            existActionValues.values[10] = actionValues.values[10]
                            existActionValues.values[11] += actionValues.values[11]
                            existActionValues.values[12] += actionValues.values[12]
                            existActionValues.values[14] += actionValues.values[14]
                    elif chkPatientInfo:
                        existActionValues.values[4] += actionValues.values[4]
                        existActionValues.values[8] += actionValues.values[8]
                        if chkCoefficient:
                            existActionValues.values[9] = actionValues.values[9]
                            existActionValues.values[10] += actionValues.values[10]
                            existActionValues.values[11] += actionValues.values[11]
                            existActionValues.values[13] += actionValues.values[13]
                    elif chkExecDateInfo:
                        existActionValues.values[4] += actionValues.values[4]
                        existActionValues.values[8] += actionValues.values[8]
                        if chkCoefficient:
                            existActionValues.values[9] = actionValues.values[9]
                            existActionValues.values[10] += actionValues.values[10]
                            existActionValues.values[11] += actionValues.values[11]
                            existActionValues.values[13] += actionValues.values[13]
                    else:
                        existActionValues.values[3] += actionValues.values[3]
                        existActionValues.values[7] += actionValues.values[7]
                        if chkCoefficient:
                            existActionValues.values[8] = actionValues.values[8]
                            existActionValues.values[9] += actionValues.values[9]
                            existActionValues.values[10] += actionValues.values[10]
                            existActionValues.values[12] += actionValues.values[12]
                else:
                    if chkPatientInfo and chkExecDateInfo:
                        existActionValues.values[5] += actionValues.values[5]
                        existActionValues.values[6] += actionValues.values[6]
                        if chkCoefficient:
                            existActionValues.values[7] = actionValues.values[7]
                            existActionValues.values[8] += actionValues.values[8]
                            existActionValues.values[9] += actionValues.values[9]
                            existActionValues.values[11] += actionValues.values[11]
                    elif chkPatientInfo:
                        existActionValues.values[4] += actionValues.values[4]
                        existActionValues.values[5] += actionValues.values[5]
                        if chkCoefficient:
                            existActionValues.values[6] = actionValues.values[6]
                            existActionValues.values[7] += actionValues.values[7]
                            existActionValues.values[8] += actionValues.values[8]
                            existActionValues.values[10] += actionValues.values[10]
                    elif chkExecDateInfo:
                        existActionValues.values[4] += actionValues.values[4]
                        existActionValues.values[5] += actionValues.values[5]
                        if chkCoefficient:
                            existActionValues.values[6] = actionValues.values[6]
                            existActionValues.values[7] += actionValues.values[7]
                            existActionValues.values[8] += actionValues.values[8]
                            existActionValues.values[10] += actionValues.values[10]
                    else:
                        existActionValues.values[3] += actionValues.values[3]
                        existActionValues.values[4] += actionValues.values[4]
                        if chkCoefficient:
                            existActionValues.values[5] = actionValues.values[5]
                            existActionValues.values[6] += actionValues.values[6]
                            existActionValues.values[7] += actionValues.values[7]
                            existActionValues.values[9] += actionValues.values[9]
            else:
                self._mapRowValues[actualKey] = actionValues


    def orgStructureFilterByParams(self, chkOrgStructure, strongOrgStructureId, orgStructureId):
        if chkOrgStructure:
            if strongOrgStructureId:
                if not self._actualOrgStructureIdListByStrongOrgStructure:
                    predicatObject = CPredicat(condId=strongOrgStructureId)
                    strongOrgStructureItemIndex = self._orgStructureHelperModel.findItem(predicatObject.eq)
                    if strongOrgStructureItemIndex:
                        strongOrgStructureItem = strongOrgStructureItemIndex.internalPointer()
                        self._actualOrgStructureIdListByStrongOrgStructure = strongOrgStructureItem.getItemIdList()
                if orgStructureId in self._actualOrgStructureIdListByStrongOrgStructure:
                    return True, strongOrgStructureId
                else:
                    return False, strongOrgStructureId
            else:
                return True, strongOrgStructureId
        return True, orgStructureId


    def getDescription(self, params):
        begDate = params.get('begDate', None)
        endDate = params.get('endDate', None)
        chkStatus = params.get('chkStatus', False)
        status    = params.get('status', None)
        personId  = params.get('personId', None)
        reportType = params.get('reportType', None)
        chkPatientInfo = params.get('chkPatientInfo', False)
        chkExecDateInfo= params.get('chkExecDateInfo', False)
        chkAllOrgStructure = params.get('chkAllOrgStructure', False)
        contractText = params.get('contractText', None)
        financeText = params.get('financeText', None)
        confirmation = params.get('confirmation', False)
        confirmationBegDate = params.get('confirmationBegDate', None)
        confirmationEndDate = params.get('confirmationEndDate', None)
        confirmationType = params.get('confirmationType', 0)
        confirmationPeriodType = params.get('confirmationPeriodType', 0)
        isVAT = params.get('isVAT', False)
        rows = []
        if begDate:
            rows.append(u'Начальная дата периода: %s'%forceString(begDate))
        if endDate:
            rows.append(u'Конечная дата периода: %s'%forceString(endDate))
        if chkStatus and status is not None:
            rows.append(u'Статус: %s' %CActionStatus.text(status))
        if reportType is not None:
            rows.append(u'Отчет по: %s' %[u'отделениям выполнившего действие врача',
                                          u'отделениям за которым закрепленно действие'][reportType])
        if chkAllOrgStructure:
            rows.append(u'Действия связанны со всеми возможными подразделениями')
        if financeText:
            rows.append(u'Тип финансирования: %s' % financeText)
        if contractText:
            rows.append(u'Контракт: %s' % contractText)
        if confirmation:
            rows.append(u'Тип подтверждения: %s'%{0: u'не выставлено',
                                                  1: u'выставлено',
                                                  2: u'оплачено',
                                                  3: u'отказано'}.get(confirmationType, u'не выставлено'))
            rows.append(u'Период подтверждения: %s'%{0: u'по дате формирования счета',
                                                     1: u'по дате подтверждения оплаты'}.get(confirmationPeriodType, u'по дате формирования счета'))
            if confirmationBegDate:
                rows.append(u'Начало периода подтверждения: %s'%forceString(confirmationBegDate))
            if confirmationEndDate:
                rows.append(u'Окончание периода подтверждения: %s'%forceString(confirmationEndDate))
        if personId:
            rows.append(u'Исполнитель: %s' % forceRef(QtGui.qApp.db.translate('vrbPersonWithSpeciality', 'id', personId, 'name')))
        chkCoefficient = params.get('chkCoefficient', False)
        if chkCoefficient:
            rows.append(u'Учитывать коэффициенты')
        if chkExecDateInfo:
            rows.append(u'Детализировать по дате')
        if chkPatientInfo:
            rows.append(u'Информация о пациенте')
        if isVAT:
            rows.append(u'Без учёта НДС')
        rows.append(u'отчёт составлен: '+forceString(QDateTime.currentDateTime()))
        return rows


class CSetupReport(QtGui.QDialog, Ui_ReportSetupByOrgStructureDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.cmbFinance.setTable('rbFinance', addNone=True)
        self.patientRequired                = False
        self.groupByPatientVisible          = False
        self.setupByOrgStructureVisible     = False
        self.strongOrgStructureVisible      = False
        self.clientAgeCategoryVisible       = False
        self.onlyClientAsPersonInLPUVisible = False
        self.personVisible                  = False
        self.detailServiceVisible           = False
        self.eventIdentifierTypeVisible     = False
        self.dateTypeVisible                = False
        self.eventStatusVisible             = False

        self.setStrongOrgStructureVisible(      self.strongOrgStructureVisible      )
        self.setGroupByPatientVisible(          self.groupByPatientVisible          )
        self.setSetupByOrgStructureVisible(     self.setupByOrgStructureVisible     )
        self.setClientAgeCategoryVisible(       self.clientAgeCategoryVisible       )
        self.setOnlyClientAsPersonInLPUVisible( self.onlyClientAsPersonInLPUVisible )
        self.setPersonVisible(                  self.personVisible                  )
        self.setDetailServiceVisible(           self.detailServiceVisible           )
        self.setEventIdentifierTypeVisible(     self.eventIdentifierTypeVisible     )
        self.setDateTypeVisible(                self.dateTypeVisible                )
        self.setEventStatusVisible(             self.eventStatusVisible           )
        self.setDetailExecPersonVisible(False)


    def setDateTypeVisible(self, value):
        self.dateTypeVisible = value
        self.cmbDateType.setVisible(value)
        self.lblDateType.setVisible(value)


    def setEventIdentifierTypeVisible(self, value):
        self.eventIdentifierTypeVisible = value
        self.lblEventIdentifierType.setVisible(value)
        self.cmbEventIdentifierType.setVisible(value)


    def setDetailServiceVisible(self, value):
        self.detailServiceVisible = value
        self.chkDetailService.setVisible(value)


    def setDetailExecPersonVisible(self, value):
        self.detailExecPersonVisible = value
        self.chkDetailExecPerson.setVisible(value)


    def setPersonVisible(self, value):
        self.personVisible = value
        self.chkPerson.setVisible(value)
        self.cmbPerson.setVisible(value)

    def setStrongOrgStructureVisible(self, value):
        self.strongOrgStructureVisible = value
        self.chkOrgStructure.setVisible(value)
        self.cmbOrgStructure.setVisible(value)

    def setGroupByPatientVisible(self, value):
        self.groupByPatientVisible = value
        self.chkGroupByPatient.setVisible(value)

    def setSetupByOrgStructureVisible(self, value):
        self.setupByOrgStructureVisible = value
        self.lblReportType.setVisible(value)
        self.cmbReportType.setVisible(value)
        self.chkPatientInfo.setVisible(value)
        self.chkExecDateInfo.setVisible(value)
        self.chkAllOrgStructure.setVisible(value)


    def setClientAgeCategoryVisible(self, value):
        self.clientAgeCategoryVisible = value
        self.chkClientAgeCategory.setVisible(value)
        self.cmbClientAgeCategory.setVisible(value)

    def setOnlyClientAsPersonInLPUVisible(self, value):
        self.onlyClientAsPersonInLPUVisible = value
        self.chkOnlyClientAsPersonInLPU.setVisible(value)

    def setEventStatusVisible(self, value):
        self.eventStatusVisible = value
        self.chkEventStatus.setVisible(value)
        self.cmbEventStatus.setVisible(value)

    def setTitle(self, title):
        self.setWindowTitle(title)


    def setParams(self, params):
        if self.dateTypeVisible:
            self.cmbDateType.setCurrentIndex(params.get('dateType', 0))
        self.edtBegDate.setDate(params.get('begDate', QDate.currentDate()))
        self.edtEndDate.setDate(params.get('endDate', QDate.currentDate()))
        chkStatus = params.get('chkStatus', False)
        self.chkStatus.setChecked(chkStatus)
        self.cmbStatus.setValue(params.get('status', CActionStatus.started))
        self.chkCoefficient.setChecked(params.get('chkCoefficient', False))
        self.chkExecDateInfo.setChecked(params.get('chkExecDateInfo', False))
        self.cmbReportType.setCurrentIndex(params.get('reportType', 0))
        self.chkAllOrgStructure.setChecked(params.get('chkAllOrgStructure', False))
        self.chkPatientInfo.setChecked(params.get('chkPatientInfo', False))
#        self.cmbContract.setValue(params.get('contractId', None))
        self.cmbContract.setPath(params.get('contractPath', None))
        self.cmbFinance.setValue(params.get('financeId', None))
        self.chkConfirmation.setChecked(params.get('confirmation', False))
        date = QDate.currentDate()
        self.edtConfirmationBegDate.setDate(params.get('confirmationBegDate', firstMonthDay(date)))
        self.edtConfirmationEndDate.setDate(params.get('confirmationEndDate', lastMonthDay(date)))
        self.cmbConfirmationType.setCurrentIndex(params.get('confirmationType', 0))
        self.cmbConfirmationPeriodType.setCurrentIndex(params.get('confirmationPeriodType', 0))

        if self.eventIdentifierTypeVisible:
            self.cmbEventIdentifierType.setCurrentIndex(params.get('eventIdentifierType', 0))

        if self.strongOrgStructureVisible:
            chkOrgStructure = params.get('chkOrgStructure', False)
            self.chkOrgStructure.setChecked(chkOrgStructure)
            self.cmbOrgStructure.setValue(params.get('orgStructureId', None))

        if self.clientAgeCategoryVisible:
            chkClientAgeCategory = params.get('chkClientAgeCategory', False)
            self.chkClientAgeCategory.setChecked(chkClientAgeCategory)
            self.cmbClientAgeCategory.setCurrentIndex(params.get('clientAgeCategory', 0))
            self.cmbClientAgeCategory.setEnabled(chkClientAgeCategory)

        if self.onlyClientAsPersonInLPUVisible:
            self.chkOnlyClientAsPersonInLPU.setChecked(params.get('chkOnlyClientAsPersonInLPU', False))

        if self.personVisible:
            chkPerson = params.get('chkPerson', False)
            self.chkPerson.setChecked(chkPerson)
            self.cmbPerson.setValue(params.get('personId', None))

        if self.detailServiceVisible:
            self.chkDetailService.setChecked(params.get('chkDetailService', False))

        if self.groupByPatientVisible:
            chkGroupByPatient = params.get('chkGroupByPatient', False)
            self.chkGroupByPatient.setChecked(chkGroupByPatient)

        if self.eventStatusVisible:
            chkEventStatus = params.get('chkEventStatus', False)
            self.chkEventStatus.setChecked(chkEventStatus)
            self.cmbEventStatus.setCurrentIndex(params.get('eventStatus',  0))

        if self.detailExecPersonVisible:
            self.chkDetailExecPerson.setChecked(params.get('isDetailExecPerson', True))

        self.chkVAT.setChecked(params.get('isVAT', False))


    def params(self):
        params = {}

        if self.dateTypeVisible:
            params['dateType'] = self.cmbDateType.currentIndex()
        params['begDate']  = self.edtBegDate.date()
        params['endDate']  = self.edtEndDate.date()

        params['chkStatus'] = self.chkStatus.isChecked()
        params['status']    = self.cmbStatus.value()
        params['chkCoefficient'] = self.chkCoefficient.isChecked()
        params['chkExecDateInfo'] = self.chkExecDateInfo.isChecked()

#        params['contractId'] = self.cmbContract.value()
        params['contractPath'] = self.cmbContract.getPath()
        params['contractIdList'] = self.cmbContract.getIdList()
        params['contractText'] = forceString(self.cmbContract.currentText())
        params['financeId']  = self.cmbFinance.value()
        params['financeText'] = self.cmbFinance.currentText()
        params['confirmation'] = self.chkConfirmation.isChecked()
        params['confirmationType'] = self.cmbConfirmationType.currentIndex()
        params['confirmationPeriodType'] = self.cmbConfirmationPeriodType.currentIndex()
        params['confirmationBegDate'] = self.edtConfirmationBegDate.date()
        params['confirmationEndDate'] = self.edtConfirmationEndDate.date()

        if self.eventIdentifierTypeVisible:
            params['eventIdentifierType'] = self.cmbEventIdentifierType.currentIndex()

        if self.strongOrgStructureVisible:
            params['chkOrgStructure'] = self.chkOrgStructure.isChecked()
            params['orgStructureId'] = self.cmbOrgStructure.value()
            params['orgStructureIdList'] = self.getOrgStructureIdList()

        if self.setupByOrgStructureVisible:
            params['reportType'] = self.cmbReportType.currentIndex()
            if self.chkAllOrgStructure.isEnabled():
                params['chkAllOrgStructure'] = self.chkAllOrgStructure.isChecked()
            else:
                params['chkAllOrgStructure'] = False

            params['chkPatientInfo'] = self.chkPatientInfo.isChecked()

        if self.groupByPatientVisible:
            params['chkGroupByPatient'] = self.chkGroupByPatient.isChecked()


        if self.clientAgeCategoryVisible:
            params['chkClientAgeCategory'] = self.chkClientAgeCategory.isChecked()
            params['clientAgeCategory'] = self.cmbClientAgeCategory.currentIndex()

        if self.onlyClientAsPersonInLPUVisible:
            params['chkOnlyClientAsPersonInLPU'] = self.chkOnlyClientAsPersonInLPU.isChecked()

        if self.personVisible:
            params['chkPerson'] = self.chkPerson.isChecked()
            params['personId'] = self.cmbPerson.value()

        if self.detailServiceVisible:
            params['chkDetailService'] = self.chkDetailService.isChecked()

        if self.eventStatusVisible:
            params['chkEventStatus'] = self.chkEventStatus.isChecked()
            params['eventStatus'] = self.cmbEventStatus.currentIndex()

        if self.detailExecPersonVisible:
            params['isDetailExecPerson'] = self.chkDetailExecPerson.isChecked()

        params['isVAT']                 = self.chkVAT.isChecked()

        return params

    def getOrgStructureModel(self):
        return self.cmbOrgStructure.model()

    def getOrgStructureIdList(self):
        treeIndex = self.cmbOrgStructure._model.index(self.cmbOrgStructure.currentIndex(), 0, self.cmbOrgStructure.rootModelIndex())
        treeItem = treeIndex.internalPointer() if treeIndex.isValid() else None
        return treeItem.getItemIdList() if treeItem else []

    @pyqtSignature('int')
    def on_cmbReportType_currentIndexChanged(self, index):
        self.chkAllOrgStructure.setEnabled(index==1)


# ####################################

class CPredicat(object):
    def __init__(self, condId):
        self._condId = condId
    def eq(self, item):
        return item._id == self._condId

