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
from PyQt4.QtCore import pyqtSignature, QDate

from library.Utils      import firstMonthDay, forceDate, forceDateTime, forceDouble, forceRef, forceString, formatName, lastMonthDay
from Events.Utils       import getActionTypeDescendants
from Reports.Report     import CReport
from Reports.ReportBase import CReportBase, createTable
from Reports.ReportView import CPageFormat
from Reports.ActionTypeSelectionDialog import CActionTypeSelectionDialog

from Reports.Ui_ReportClientSummarySetup import Ui_ReportClientSummarySetupDialog


def selectData(params):
    begDate = params.get('begDate', None)
    endDate = params.get('endDate', None)
    dateFieldName = {
                     0 : 'endDate',
                     1 : 'directionDate',
                     2 : 'begDate',
                     3 : 'plannedEndDate'
                    }.get(params.get('dateType', 0), 'endDate')
    setOrgStructureId = params.get('setOrgStructureId', None)
    orgStructureId = params.get('orgStructureId', None)
    personId = params.get('personId', None)
    setPersonId = params.get('setPersonId', None)
    specialityId = params.get('specialityId', None)
    setSpecialityId = params.get('setSpecialityId', None)
    financeId = params.get('financeId', None)
    confirmation = params.get('confirmation', False)
    confirmationBegDate = params.get('confirmationBegDate', None)
    confirmationEndDate = params.get('confirmationEndDate', None)
    confirmationType = params.get('confirmationType', 0)
    eventTypeId = params.get('eventTypeId', None)
    chkActionTypeClass = params.get('chkActionTypeClass', False)
    actionTypeClass = params.get('actionTypeClass', None)
    actionTypeId = params.get('actionTypeId', None)
    db = QtGui.qApp.db
    tableEvent                = db.table('Event')
    tableAction               = db.table('Action')
    tableActionType           = db.table('ActionType')
    tableAP                   = db.table('ActionProperty')
    tableAPJT                 = db.table('ActionProperty_Job_Ticket')
    tableActionTypeService    = db.table('ActionType_Service')
    tableService              = db.table('rbService')
    tableClient               = db.table('Client')
    tableClientIdentification = db.table('ClientIdentification')
    tablePerson               = db.table('vrbPersonWithSpeciality')
    tableSetPerson            = db.table('vrbPersonWithSpeciality').alias('SetVrbPersonSpeciality')
    tableAccountItem          = db.table('Account_Item')
    queryTable = tableEvent
    queryTable = queryTable.leftJoin(tableAction, tableAction['event_id'].eq(tableEvent['id']))
    queryTable = queryTable.leftJoin(tableAP, tableAP['action_id'].eq(tableAction['id']))
    queryTable = queryTable.leftJoin(tableAPJT, tableAPJT['id'].eq(tableAP['id']))
    queryTable = queryTable.leftJoin(tablePerson, tablePerson['id'].eq(tableAction['person_id']))
    queryTable = queryTable.leftJoin(tableSetPerson, tableSetPerson['id'].eq(tableAction['setPerson_id']))
    queryTable = queryTable.leftJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
    queryTable = queryTable.leftJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
    actionTypeServiceJoinCond = [tableActionTypeService['master_id'].eq(tableActionType['id']),
                                 tableAction['finance_id'].eq(tableActionTypeService['finance_id'])]
    queryTable = queryTable.leftJoin(tableActionTypeService, db.joinAnd(actionTypeServiceJoinCond))
    queryTable = queryTable.leftJoin(tableService, tableService['id'].eq(tableActionTypeService['service_id']))
    queryTable = queryTable.leftJoin(tableClientIdentification,
                                     tableClientIdentification['client_id'].eq(tableClient['id']))
    cond = [
            tableEvent['deleted'].eq(0),
            tableAction['deleted'].eq(0),
            tableAction[dateFieldName].lt(endDate.addDays(1)),
            tableAction[dateFieldName].ge(begDate)
           ]
    if financeId:
        cond.append(tableAction['finance_id'].eq(financeId))
    if eventTypeId:
        cond.append(tableEvent['eventType_id'].eq(eventTypeId))
    if chkActionTypeClass:
        if actionTypeClass is not None:
            cond.append(tableActionType['class'].eq(actionTypeClass))
        if actionTypeId:
            cond.append(tableActionType['id'].inlist(getActionTypeDescendants(actionTypeId, actionTypeClass)))
    if setOrgStructureId or setPersonId or setSpecialityId:
        if setOrgStructureId:
            setOrgStructureIdList = db.getDescendants('OrgStructure', 'parent_id', setOrgStructureId)
            cond.append(tableSetPerson['orgStructure_id'].inlist(setOrgStructureIdList))
        if setPersonId:
            cond.append(tableSetPerson['id'].eq(setPersonId))
        if setSpecialityId:
            cond.append(tableSetPerson['speciality_id'].eq(setSpecialityId))
    if orgStructureId:
        orgStructureIdList = db.getDescendants('OrgStructure', 'parent_id', orgStructureId)
        cond.append(tablePerson['orgStructure_id'].inlist(orgStructureIdList))
    if personId:
        cond.append(tablePerson['id'].eq(personId))
    if specialityId:
        cond.append(tablePerson['speciality_id'].eq(specialityId))
    if confirmation:
        queryTable = queryTable.leftJoin(tableAccountItem, tableAccountItem['action_id'].eq(tableAction['id']))
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

        if confirmationBegDate:
            cond.append(tableAccountItem['date'].ge(confirmationBegDate))
        if confirmationEndDate:
            cond.append(tableAccountItem['date'].lt(confirmationEndDate.addDays(1)))
    fieldUetDoctor = 'IF(YEAR(FROM_DAYS(DATEDIFF(Action.`endDate`, Client.`birthDate`))) < 18, rbService.`childUetDoctor`, rbService.`adultUetDoctor`) AS uetDoctor'
    cols = [
            tableAction['id'].alias('actionId'),
            tableAction['event_id'].alias('eventId'),
            tableActionType['code'].alias('actionTypeCode'),
            tableActionType['name'].alias('actionTypeName'),
            tableAction['amount'].alias('actionAmount'),
            tableAction['person_id'].alias('actionPersonId'),
            tableSetPerson['name'].alias('setPersonName'),
            tableAction['endDate'].alias('actionEndDate'),
            tablePerson['name'].alias('personName'),
            tableClient['lastName'].name(),
            tableClient['firstName'].name(),
            tableClient['patrName'].name(),
            tableAction[dateFieldName].alias('actualDate'),
            fieldUetDoctor,
            tableClient['id'].alias('clientId'),
            tableClientIdentification['identifier'].name(),
            tableAPJT['value'].alias('jobTicketId')
           ]
#    order = (
##             tableAction[dateFieldName].name(),
#             tableClient['lastName'].name(),
#             tableClient['firstName'].name(),
#             tableClient['patrName'].name(),
#             tableClient['id'].name(),
#             tableAPJT['value'].name()
#            )
    order = u'`Client`.`lastName` ASC, `Client`.`firstName` ASC, `Client`.`firstName` ASC, `Client`.`id` DESC, `ActionProperty_Job_Ticket`.`value` DESC'
    stmt = db.selectStmt(queryTable, cols, cond, order)
    return db.query(stmt)


class CReportClientSummary(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self._mapDate2Info = {}
        self._mapDate2Date = {}
        self._mapActionId2JobTicketIdList = {}
        self.setTitle(u'Общая сводка на пациентов')
        self.orientation = CPageFormat.Landscape


    def getSetupDialog(self, parent):
        result = CReportClientSummarySetupDialog(parent)
        result.setVisibleDetailActions(False)
        result.setVisibleDetailOrgStructure(False)
        result.setVisibleDetailFinance(False)
        result.setTitle(self.title())
        return result


    def getDescription(self, params):
        db = QtGui.qApp.db

        begDate = params.get('begDate', None)
        endDate = params.get('endDate', None)

        dateFieldName = {
                     0 : u'окончания',
                     1 : u'назначения',
                     2 : u'начала',
                     3 : u'планируемая'
                    }.get(params.get('dateType', 0), u'Дата окончания')

        setOrgStructureId = params.get('setOrgStructureId', None)
        orgStructureId = params.get('orgStructureId', None)

        personId = params.get('personId', None)
        setPersonId = params.get('setPersonId', None)

        specialityId = params.get('specialityId', None)
        setSpecialityId = params.get('setSpecialityId', None)

        financeId = params.get('financeId', None)
        confirmation = params.get('confirmation', False)
        confirmationBegDate = params.get('confirmationBegDate', None)
        confirmationEndDate = params.get('confirmationEndDate', None)
        confirmationType = params.get('confirmationType', 0)
        accountingSystemId = params.get('accountingSystemId', None)
        eventTypeId = params.get('eventTypeId', None)

        chkActionTypeClass = params.get('chkActionTypeClass', False)
        actionTypeClass = params.get('actionTypeClass', None)
        actionTypeId = params.get('actionTypeId', None)

        rows = [u'Дата: %s'%dateFieldName]
        if begDate:
            rows.append(u'Начальная дата периода: %s'%forceString(begDate))
        if endDate:
            rows.append(u'Конечная дата периода: %s'%forceString(endDate))

        if financeId:
            rows.append(u'Тип финансирования: %s'%forceString(db.translate('rbFinance', 'id', financeId, 'CONCAT_WS(\' | \', code,name)')))

        if eventTypeId:
            rows.append(u'Тип события: %s'%forceString(db.translate('EventType', 'id', eventTypeId, 'CONCAT_WS(\' | \', code,name)')))

        if chkActionTypeClass:
            if actionTypeClass is not None:
                rows.append(u'Класс действия: %s'%{0: u'Статус',
                                                   1: u'Диагностика',
                                                   2: u'Лечение',
                                                   3: u'Прочие мероприятия'}.get(actionTypeClass, u'Статус'))

            if actionTypeId:
                rows.append(u'Тип действия: %s'%forceString(db.translate('ActionType', 'id', actionTypeId, 'CONCAT_WS(\' | \', code,name)')))

        if setOrgStructureId:
            rows.append(u'Подразделение назначившего: %s'%forceString(db.translate('OrgStructure', 'id', setOrgStructureId, 'CONCAT_WS(\' | \', code,name)')))

        if setPersonId:
            rows.append(u'Назначивший: %s'%forceString(db.translate('vrbPerson', 'id', setPersonId, 'name')))

        if setSpecialityId:
            rows.append(u'Специальность назначившего: %s'%forceString(db.translate('rbSpeciality', 'id', setSpecialityId, 'CONCAT_WS(\' | \', code,name)')))

        if orgStructureId:
            rows.append(u'Подразделение исполнителя: %s'%forceString(db.translate('OrgStructure', 'id', orgStructureId, 'CONCAT_WS(\' | \', code,name)')))

        if personId:
            rows.append(u'Исполнитель: %s'%forceString(db.translate('vrbPerson', 'id', personId, 'name')))

        if specialityId:
            rows.append(u'Специальность исполнителя: %s'%forceString(db.translate('rbSpeciality', 'id', specialityId, 'CONCAT_WS(\' | \', code,name)')))

        if accountingSystemId:
            rows.append(u'Тип идентификатора: %s'%forceString(db.translate('rbAccountingSystem', 'id', accountingSystemId, 'CONCAT_WS(\' | \', code,name)')))

        if confirmation:
            rows.append(u'Тип подтверждения: %s'%{0: u'не выставлено',
                                                  1: u'выставлено',
                                                  2: u'оплачено',
                                                  3: u'отказано'}.get(confirmationType, u'не выставлено'))



            if confirmationBegDate:
                rows.append(u'Начало периода подтверждения: %s'%forceString(confirmationBegDate))
            if confirmationEndDate:
                rows.append(u'Окончание периода подтверждения: %s'%forceString(confirmationEndDate))


        return rows

    def resetHelpers(self):
        self._mapDate2Info.clear()
        self._mapDate2Date.clear()
        self._mapActionId2JobTicketIdList.clear()

    def structQuery(self, query, params):
        self.resetHelpers()

        accountingSystemId = params.get('accountingSystemId', None)

        actionIdList = []

        mapDate2ClientJT = {}

        while query.next():
            record = query.record()

            actionId       = forceRef(record.value('actionId'))
#            jobTicketId    = forceRef(record.value('jobTicketId'))
#
#            if jobTicketId:
#                actionIdMap2JobTicketId = self._mapActionId2JobTicketIdList.setdefault(actionId, [])
#                if jobTicketId not in actionIdMap2JobTicketId:
#                    actionIdMap2JobTicketId.append(jobTicketId)

            if actionId in actionIdList:
                continue

            actionIdList.append(actionId)

            eventId        = forceRef(record.value('eventId'))
            clientId       = forceRef(record.value('clientId'))
            actionTypeCode = forceString(record.value('actionTypeCode'))
            actionTypeName = forceString(record.value('actionTypeName'))
            actionPersonId = forceRef(record.value('actionPersonId'))
            setPersonName  = forceString(record.value('setPersonName'))
            actionEndDate  = forceDateTime(record.value('actionEndDate'))
            personName     = forceString(record.value('personName'))
            lastName       = forceString(record.value('lastName'))
            firstName      = forceString(record.value('firstName'))
            patrName       = forceString(record.value('patrName'))
            fullName       = formatName(lastName, firstName, patrName)
            actualDate     = forceDate(record.value('actualDate'))
            actionAmount   = forceDouble(record.value('actionAmount'))
            uetDoctor      = forceDouble(record.value('uetDoctor'))
            totalUets      = uetDoctor * actionAmount
            identifier     = forceString(record.value('identifier'))
            jobTicketId    = forceRef(record.value('jobTicketId'))

            identifier     = identifier if accountingSystemId else clientId

            dateKey = unicode(actualDate.toString('yyyy-MM-dd'))
            clientInfoList = self._mapDate2Info.setdefault(dateKey, {})
            self._mapDate2Date[dateKey] = actualDate
            clientInfo = clientInfoList.setdefault((clientId, identifier, fullName), [])

            clientJTInfo = mapDate2ClientJT.setdefault(dateKey, {})
            clientJTList = clientJTInfo.setdefault((clientId, identifier, fullName), [])
            if jobTicketId in clientJTList:
                jobTicketId = None
            else:
                clientJTList.append(jobTicketId)

            clientInfo.append(
                              (
                               eventId,
                               actionPersonId,
                               bool(jobTicketId),
                               actionEndDate,
                               setPersonName,
                               personName,
                               actionTypeCode,
                               actionTypeName,
                               actionAmount,
                               uetDoctor,
                               totalUets
                              )
                             )




    def build(self, params):
        query = selectData(params)
        self.structQuery(query, params)

        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()

        accountingSystemId = params.get('accountingSystemId', None)
        if accountingSystemId:
            identifierColumnName = forceString(QtGui.qApp.db.translate('rbAccountingSystem', 'id', accountingSystemId, 'name'))
        else:
            identifierColumnName = u'Идентификатор клиента'

        tableColumns = [
                        ('%2',
                        [u'№'], CReportBase.AlignRight),
                        ('%5',
                        [u'Дата'], CReportBase.AlignLeft),
                        ('%8',
                        [identifierColumnName], CReportBase.AlignLeft),
                        ('%15',
                        [u'Пациент'], CReportBase.AlignLeft),
                        ('%7',
                        [u'Кол-во обращений'], CReportBase.AlignLeft),
                        ('%7',
                        [u'Кол-во работ'], CReportBase.AlignLeft),
                        ('%7',
                        [u'Обслужено'], CReportBase.AlignLeft),
                        ('%7',
                        [u'Назначил'], CReportBase.AlignLeft),
                        ('%7',
                        [u'Исполнитель'], CReportBase.AlignLeft),
                        ('%7',
                        [u'Код типа действия '], CReportBase.AlignLeft),
                        ('%7',
                        [u'Название типа Действия'], CReportBase.AlignLeft),
                        ('%7',
                        [u'Количество'], CReportBase.AlignLeft),
                        ('%7',
                        [u'УЕТ'], CReportBase.AlignLeft),
                        ('%7',
                        [u'Всего УЕТ'], CReportBase.AlignLeft)
                       ]

        eventCountCol = 4
        jobTicketCountCol = 5
        doneCountCol = 6

        table = createTable(cursor, tableColumns)

        dateKeyList = self._mapDate2Info.keys()
        dateKeyList.sort()

        boldChars = QtGui.QTextCharFormat()
        boldChars.setFontWeight(QtGui.QFont.Bold)

        columnShift = 2

        result = [0, 0.0, 0.0, 0.0, 0]
        resultEventIdCount = 0
        resultJobTicketsCount = 0
        resultDoneCount = 0
        for dateIdx, dateKey in enumerate(dateKeyList):
            tableRow = table.addRow()
            table.setText(tableRow, 0, dateIdx+1)
            table.setText(tableRow, 1, forceString(self._mapDate2Date[dateKey]))
            clientInfoList = self._mapDate2Info[dateKey]
            clientInfoKeyList = clientInfoList.keys()
            clientInfoKeyList.sort(key=lambda item: item[2])

            lastDI = len(clientInfoKeyList)

            mergeCount = lastDI

            dateResult = [0, 0.0, 0.0, 0.0, 0]
            dateEventIdCount = 0
            dateJobTicketsCount = 0
            dateDoneCount = 0
            for clientIdx, clientInfoKey in enumerate(clientInfoKeyList):
                clientResult = [0.0, 0.0, 0.0, 0.0]
                for idx, clientInfoKeyValue in enumerate(clientInfoKey[1:]):
                    column = columnShift+idx
                    table.setText(tableRow, column, clientInfoKeyValue)

                clientInfo = clientInfoList[clientInfoKey]
                lastCI = len(clientInfo)
                clientEventId2ActionPersonIdList = {}
                previousActionPersonId = 0
                personActionRowCount = 0
                clientJobTicketsCount = 0
                clientDoneCount = 0
                originalDoneKeys = []
                clientId = clientInfo[0]
                for infoIdx, info in enumerate(clientInfo):
                    eventId = info[0]
                    actionPersonId = info[1]
                    existsJobTicketId = info[2]
                    actionEndDate = info[3]

                    if existsJobTicketId:
                        clientJobTicketsCount += 1

                    if clientId and actionEndDate:
                        doneKey = (clientId, actionPersonId, forceString(actionEndDate))
                        if doneKey not in originalDoneKeys:
                            clientDoneCount += 1
                            originalDoneKeys.append(doneKey)

                    if previousActionPersonId in (0, actionPersonId):
                        personActionRowCount += 1
                    else:
                        personActionRowCount = 1

                    actionPersonIdList = clientEventId2ActionPersonIdList.setdefault(eventId, [])

                    for valueIdx, value in enumerate(info[4:]): # первое значение - это eventId
                        if valueIdx == 0:
                            if actionPersonId not in actionPersonIdList:
                                actionPersonIdList.append(actionPersonId)
                                table.setText(tableRow, column+columnShift+2+valueIdx, value)
                        else:
                            table.setText(tableRow, column+columnShift+2+valueIdx, value)
                            if valueIdx in (4, 5, 6):
                                clientResult[valueIdx-columnShift-1] += value
                    if infoIdx < lastCI-1:
                        tableRow = table.addRow()

                    previousActionPersonId = actionPersonId

                clientFakeVisits = sum([len(personIdList) for personIdList in clientEventId2ActionPersonIdList.values()])
                table.setText(tableRow-lastCI+1, eventCountCol, clientFakeVisits)
                table.setText(tableRow-lastCI+1, jobTicketCountCol, clientJobTicketsCount)
                table.setText(tableRow-lastCI+1, doneCountCol, clientDoneCount)

                dateEventIdCount += clientFakeVisits
                dateJobTicketsCount += clientJobTicketsCount
                dateDoneCount += clientDoneCount

                mergeCount += lastCI

                table.mergeCells(tableRow-lastCI+1, 2,  tableRow, 1)
                table.mergeCells(tableRow-lastCI+1, 3,  tableRow, 1)
                table.mergeCells(tableRow-lastCI+1, 4,  tableRow, 1)
                table.mergeCells(tableRow-lastCI+1, 5,  tableRow, 1)
                table.mergeCells(tableRow-lastCI+1, 6,  tableRow, 1)

                tableRow = table.addRow()

                table.setText(tableRow, column+1, u'Итого на пациента: ', charFormat=boldChars)
                table.setText(tableRow, column+8, clientResult[1], charFormat=boldChars)
                table.setText(tableRow, column+9, clientResult[2], charFormat=boldChars)
                table.setText(tableRow, column+10, clientResult[3], charFormat=boldChars)
                table.mergeCells(tableRow, 2, 1, 6)

                dateResult[0] += 1
                dateResult[1] += clientResult[1]
                dateResult[2] += clientResult[2]
                dateResult[3] += clientResult[3]

                if clientIdx < lastDI-1:
                    tableRow = table.addRow()

            resultEventIdCount += dateEventIdCount
            resultJobTicketsCount += dateJobTicketsCount
            resultDoneCount += dateDoneCount

            result[0] += dateResult[0]
            result[1] += dateResult[1]
            result[2] += dateResult[2]
            result[3] += dateResult[3]

            table.mergeCells(tableRow-mergeCount+1, 0,  tableRow, 1)
            table.mergeCells(tableRow-mergeCount+1, 1,  tableRow, 1)

            tableRow = table.addRow()
            txt = u'Итого на дату: пациенты - %d, обращений - %d, работ - %d, обслужено: %d'% (dateResult[0], dateEventIdCount, dateJobTicketsCount, dateDoneCount)
            table.setText(tableRow, 1, txt, charFormat=boldChars)
            table.setText(tableRow, 11, dateResult[1], charFormat=boldChars)
            table.setText(tableRow, 12, dateResult[2], charFormat=boldChars)
            table.setText(tableRow, 13, dateResult[3], charFormat=boldChars)
            table.mergeCells(tableRow, 0, 1, 8)

        tableRow = table.addRow()
        txt =  u'Итог: пациенты - %d, обращений - %d, работ - %d, обслужено: %d '% (result[0], resultEventIdCount, resultJobTicketsCount, resultDoneCount)
        table.setText(tableRow, 1, txt, charFormat=boldChars)
        table.setText(tableRow, 11, result[1], charFormat=boldChars)
        table.setText(tableRow, 12, result[2], charFormat=boldChars)
        table.setText(tableRow, 13, result[3], charFormat=boldChars)
        table.mergeCells(tableRow, 0, 1, 8)
        return doc


class CReportClientSummarySetupDialog(QtGui.QDialog, Ui_ReportClientSummarySetupDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)

        self.setupUi(self)

        self.cmbSetSpeciality.setTable('rbSpeciality', addNone=True)
        self.cmbSpeciality.setTable('rbSpeciality', addNone=True)
        self.cmbFinance.setTable('rbFinance', addNone=True)
        self.cmbEventType.setTable('EventType', addNone=True)
        self.cmbIdentifierType.setTable('rbAccountingSystem', addNone=True)

        self._visibleDoctor = True
        self.setVisibleDoctor(self._visibleDoctor)

        self._visibleIdentifierType = True
        self.setVisibleIdentifierType(self._visibleIdentifierType)

        self._visibleDetailActions = True
        self.setVisibleDetailActions(self._visibleDetailActions)

        self._visibleDetailOrgStructure = True
        self.setVisibleDetailOrgStructure(self._visibleDetailOrgStructure)
        self.setVisibleDetailSpeciality(False)

        self._visibleDetailFinance  =True
        self.setVisibleDetailFinance(self._visibleDetailFinance)
        self.setVisibleDetailFinanceEvent(False)

        self._visibleTariffing = False
        self.setVisibleTariffing(self._visibleTariffing)
        self.setVisibleActionType(False)


    def setVisibleActionType(self, value):
        self.actionTypeList = []
        self._visiblebtnActionType = value
        self.lblActionTypeList.setVisible(value)
        self.btnActionType.setVisible(value)
        self.lblActionType.setVisible(not value)
        self.cmbActionType.setVisible(not value)


    def setVisibleTariffing(self, value):
        self._visibleTariffing = value
        self.chkTariffing.setVisible(value)
        self.cmbTariffing.setVisible(value)


    def setVisibleDetailFinance(self, value):
        self._visibleDetailFinance = value
        self.chkDetailFinance.setVisible(value)


    def setVisibleDetailFinanceEvent(self, value):
        self._visibleDetailFinanceEvent = (value and self._visibleDetailFinance)
        self.chkDetailFinanceEvent.setVisible(value and self._visibleDetailFinance)


    def setVisibleDetailOrgStructure(self, value):
        self._visibleDetailOrgStructure = value
        self.chkDetailOrgStructure.setVisible(value)


    def setVisibleDetailSpeciality(self, value):
        self._visibleDetailSpeciality = value
        self.chkDetailSpeciality.setVisible(value)


    def setVisibleDetailActions(self, value):
        self._visibleDetailActions = value
        self.chkDetailActions.setVisible(value)


    def setVisibleIdentifierType(self, value):
        self._visibleIdentifierType = value
        self.cmbIdentifierType.setVisible(value)
        self.lblIdentifierType.setVisible(value)


    def setVisibleDoctor(self, value):
        self._visibleDoctor = value
        self.lblDoctor.setVisible(value)
        self.cmbPerson.setVisible(value)
        self.cmbSetPerson.setVisible(value)


    def setTitle(self, title):
        self.setWindowTitle(title)


    def setParams(self, params):
        date = QDate.currentDate()
        self.edtBegDate.setDate(params.get('begDate', date))
        self.edtEndDate.setDate(params.get('endDate', date))
        self.cmbDateType.setCurrentIndex(params.get('dateType', 0))
        self.cmbSetOrgStructure.setValue(params.get('setOrgStructureId', None))
        self.cmbOrgStructure.setValue(params.get('orgStructureId', None))

        self.cmbPerson.setValue(params.get('personId', None))
        self.cmbSetPerson.setValue(params.get('setPersonId', None))

        self.cmbSpeciality.setValue(params.get('specialityId', None))
        self.cmbSetSpeciality.setValue(params.get('setSpecialityId', None))

        self.cmbFinance.setValue(params.get('financeId', None))
        self.chkConfirmation.setChecked(params.get('confirmation', False))
        self.edtConfirmationBegDate.setDate(params.get('confirmationBegDate', firstMonthDay(date)))
        self.edtConfirmationEndDate.setDate(params.get('confirmationEndDate', lastMonthDay(date)))
        self.cmbConfirmationType.setCurrentIndex(params.get('confirmationType', 0))
        self.cmbIdentifierType.setValue(params.get('accountingSystemId', None))
        self.cmbEventType.setValue(params.get('eventTypeId', None))

        chkActionTypeClass = params.get('chkActionTypeClass', False)
        self.chkActionClass.setChecked(chkActionTypeClass)

        classCode = params.get('actionTypeClass', 0)
        self.cmbActionTypeClass.setCurrentIndex(classCode)
        self.cmbActionType.setClassesPopup([classCode])
        self.cmbActionType.setClass(classCode)
        self.cmbActionType.setValue(params.get('actionTypeId', None))

        self.chkDetailActions.setChecked(params.get('chkDetailActions', False))

        self.cmbActionType.setEnabled(chkActionTypeClass)
        self.cmbActionTypeClass.setEnabled(chkActionTypeClass)

        self.chkDetailOrgStructure.setChecked(params.get('chkDetailOrgStructure', False))
        self.chkDetailSpeciality.setChecked(params.get('chkDetailSpeciality', False))

        if self._visibleDetailFinance:
            self.chkDetailFinance.setChecked(params.get('chkDetailFinance', False))
            if self._visibleDetailFinanceEvent:
                self.chkDetailFinanceEvent.setChecked(params.get('chkDetailFinanceEvent', False))

        if self._visibleTariffing:
            chkTariffing = params.get('chkTariffing', False)
            self.chkTariffing.setChecked(chkTariffing)
            self.cmbTariffing.setCurrentIndex(params.get('isTariffing', 0))
            self.cmbTariffing.setEnabled(chkTariffing)

        if self._visiblebtnActionType:
            self.actionTypeList = params.get('actionTypeList', [])
            if self.actionTypeList:
                db = QtGui.qApp.db
                table = db.table('ActionType')
                records = db.getRecordList(table, [table['name']], [table['id'].inlist(self.actionTypeList)])
                nameList = []
                for record in records:
                    nameList.append(forceString(record.value('name')))
                self.lblActionTypeList.setText(u', '.join(name for name in nameList if name))
            else:
                self.lblActionTypeList.setText(u'не задано')


    def params(self):
        result = {}
        result['begDate'] = self.edtBegDate.date()
        result['endDate'] = self.edtEndDate.date()
        result['dateType'] = self.cmbDateType.currentIndex()
        result['orgStructureId'] = self.cmbOrgStructure.value()
        result['setOrgStructureId'] = self.cmbSetOrgStructure.value()

        if self._visibleDoctor:
            result['personId'] = self.cmbPerson.value()
            result['setPersonId'] = self.cmbSetPerson.value()

        result['specialityId'] = self.cmbSpeciality.value()
        result['setSpecialityId'] = self.cmbSetSpeciality.value()

        result['financeId'] = self.cmbFinance.value()
        result['confirmation'] = self.chkConfirmation.isChecked()
        result['confirmationType'] = self.cmbConfirmationType.currentIndex()
        result['confirmationBegDate'] = self.edtConfirmationBegDate.date()
        result['confirmationEndDate'] = self.edtConfirmationEndDate.date()

        if self._visibleIdentifierType:
            result['accountingSystemId'] = self.cmbIdentifierType.value()

        result['eventTypeId'] = self.cmbEventType.value()

        chkActionTypeClass = self.chkActionClass.isChecked()
        result['chkActionTypeClass'] = chkActionTypeClass
        if chkActionTypeClass:
            result['actionTypeClass'] = self.cmbActionTypeClass.currentIndex()
            result['actionTypeId'] = self.cmbActionType.value()
        else:
            result['actionTypeClass'] = 0
            result['actionTypeId'] = None

        if self._visibleDetailActions:
            result['chkDetailActions'] = self.chkDetailActions.isChecked()

        if self._visibleDetailOrgStructure:
            result['chkDetailOrgStructure'] = self.chkDetailOrgStructure.isChecked()

        if self._visibleDetailSpeciality:
            result['chkDetailSpeciality'] = self.chkDetailSpeciality.isChecked()

        if self._visibleDetailFinance:
            result['chkDetailFinance'] = self.chkDetailFinance.isChecked()
            if self._visibleDetailFinanceEvent:
                result['chkDetailFinanceEvent'] = self.chkDetailFinanceEvent.isChecked()

        if self._visibleTariffing:
            result['chkTariffing'] = self.chkTariffing.isChecked()
            result['isTariffing'] = self.cmbTariffing.currentIndex()

        if self._visiblebtnActionType:
            result['actionTypeList'] = self.actionTypeList

        return result


    @pyqtSignature('int')
    def on_cmbActionTypeClass_currentIndexChanged(self, classCode):
        self.cmbActionType.setClassesPopup([classCode])
        self.cmbActionType.setClass(classCode)


    @pyqtSignature('')
    def on_btnActionType_clicked(self):
        self.actionTypeList = []
        self.lblActionTypeList.setText(u'не задано')
        dialog = CActionTypeSelectionDialog(self, 'class=%s'%(self.cmbActionTypeClass.currentIndex()))
        if dialog.exec_():
            self.actionTypeList = dialog.values()
            if self.actionTypeList:
                db = QtGui.qApp.db
                table = db.table('ActionType')
                records = db.getRecordList(table, [table['name']], [table['id'].inlist(self.actionTypeList)])
                nameList = []
                for record in records:
                    nameList.append(forceString(record.value('name')))
                self.lblActionTypeList.setText(u', '.join(name for name in nameList if name))

