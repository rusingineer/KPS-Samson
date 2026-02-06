#! /usr/bin/env python
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

from library.Utils      import forceDate, forceDateTime, forceDouble, forceInt, forceRef, forceString

from Orgs.Utils         import getOrgStructureFullName
from Reports.Report     import CReport, CReportEx
from Reports.ReportBase import CReportBase
from Reports.ReportView import CPageFormat
from Reports.ReportClientSummary import CReportClientSummarySetupDialog


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
    #actionTypeId = params.get('actionTypeId', None)
    actionTypeList = params.get('actionTypeList', [])

    db = QtGui.qApp.db
    tableEvent                = db.table('Event')
    tableContract             = db.table('Contract')
    tableAction               = db.table('Action')
    tableActionType           = db.table('ActionType')
    tableActionTypeService    = db.table('ActionType_Service')
    tableService              = db.table('rbService')
    tableClient               = db.table('Client')
    tablePerson               = db.table('vrbPersonWithSpeciality')
    tableSetPerson            = db.table('vrbPersonWithSpeciality').alias('SetVrbPersonSpeciality')
    tableAccountItem          = db.table('Account_Item')

    queryTable = tableEvent
    queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
    queryTable = queryTable.leftJoin(tableAction, tableAction['event_id'].eq(tableEvent['id']))
#    queryTable = queryTable.leftJoin(tableAP, tableAP['action_id'].eq(tableAction['id']))
#    queryTable = queryTable.leftJoin(tableAPJT, tableAPJT['id'].eq(tableAP['id']))
    queryTable = queryTable.leftJoin(tablePerson, tablePerson['id'].eq(tableAction['person_id']))
    queryTable = queryTable.leftJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
    queryTable = queryTable.leftJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))

#    actionTypeServiceJoinCond = [tableActionTypeService['master_id'].eq(tableActionType['id']),
#                                 tableAction['finance_id'].eq(tableActionTypeService['finance_id'])]
#    queryTable = queryTable.leftJoin(tableActionTypeService, db.joinAnd(actionTypeServiceJoinCond))

    queryTable = queryTable.leftJoin(tableActionTypeService,
                                     tableActionTypeService['master_id'].eq(tableActionType['id']))
    queryTable = queryTable.leftJoin(tableService, tableService['id'].eq(tableActionTypeService['service_id']))
#    queryTable = queryTable.leftJoin(tableClientIdentification,
#                                     tableClientIdentification['client_id'].eq(tableClient['id']))
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
        if actionTypeList:
            cond.append(tableActionType['id'].inlist(actionTypeList))
#        if actionTypeId:
#            cond.append(tableActionType['id'].inlist(getActionTypeDescendants(actionTypeId, actionTypeClass)))
    if setOrgStructureId or setSpecialityId:
        queryTable = queryTable.leftJoin(tableSetPerson, tableSetPerson['id'].eq(tableAction['setPerson_id']))
        if setOrgStructureId:
            setOrgStructureIdList = db.getDescendants('OrgStructure', 'parent_id', setOrgStructureId)
            cond.append(tableSetPerson['orgStructure_id'].inlist(setOrgStructureIdList))
        if setSpecialityId:
            cond.append(tableSetPerson['speciality_id'].eq(setSpecialityId))
    if orgStructureId:
        orgStructureIdList = db.getDescendants('OrgStructure', 'parent_id', orgStructureId)
        cond.append(tablePerson['orgStructure_id'].inlist(orgStructureIdList))
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
            tableEvent['execPerson_id'],
            tableAction['id'].alias('actionId'),
            tableAction['event_id'].alias('eventId'),
            tableActionType['id'].alias('actionTypeId'),
            tableActionType['code'].alias('actionTypeCode'),
            tableActionType['name'].alias('actionTypeName'),
            tableAction['amount'].alias('actionAmount'),
            tableAction['person_id'].alias('actionPersonId'),
            tableAction['endDate'].alias('actionEndDate'),
            tableAction['finance_id'].alias('actionFinanceId'),
            tableContract['finance_id'].alias('eventFinanceId'),
            tableActionTypeService['finance_id'].alias('serviceFinanceId'),
            tableActionTypeService['id'].alias('actionTypeServiceId'),
            tableService['id'].alias('serviceId'),
            tableService['code'].alias('serviceCode'),
            tableService['name'].alias('serviceName'),
            tablePerson['name'].alias('personName'),
            tablePerson['orgStructure_id'].alias('personOrgStructureId'),
            tableAction[dateFieldName].alias('actualDate'),
            fieldUetDoctor,
            tableClient['id'].alias('clientId'),
#            tableClientIdentification['identifier'].name(),
#            tableAPJT['value'].alias('jobTicketId')
            '''(SELECT ActionProperty_Job_Ticket.`value`
        FROM ActionProperty_Job_Ticket
        LEFT JOIN ActionProperty ON ActionProperty.`id`=ActionProperty_Job_Ticket.`id`
        LEFT JOIN Action AS ActionJobTicket ON ActionJobTicket.`id`=ActionProperty.`action_id`
        WHERE ActionJobTicket.`id`=Action.`id`) AS `jobTicketId` '''
           ]
#    order = (
#             tableAction[dateFieldName].name(),
#             tablePerson['id'].name()
#            )
#    order = u'`ActionProperty_Job_Ticket`.`value` DESC, `vrbPersonWithSpeciality`.`id` ASC'
    order = u'`jobTicketId` DESC, `vrbPersonWithSpeciality`.`id` ASC'
    stmt = db.selectStmt(queryTable, cols, cond, order)
    return db.query(stmt)


class CReportDoctorSummary(CReportEx):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self._mapFinanceIdToColumn = {}
        self._financeColumnNameList = []
        self._topOrgStructureIdList = None
        self._mapOrgStructureId2ActualTop = {}
        self._mapFinaceCoof = {}

        self._mapOrgStructureId2Name = {}

        self._columnName2Index = {'count':1, 'jobTicketCount':2, 'doneCount':3}

        self._defaultValues = {'count':0, 'actionCount':0, 'amount':0.0, 'uet':0.0, 'jobTicketCount':0, 'doneCount':0}


        self.setTitle(u'Общая сводка на врачей')

        db = QtGui.qApp.db
        table = db.table('rbFinance')
        recordList = db.getRecordList(table,
                                      'code, id, name',
                                      table['code'].inlist(['1', '2', '3', '4', '5']),
                                      'code, id')

        distinctCode = []
        for record in recordList:
            code = forceInt(record.value('code'))
            name = forceString(record.value('name'))
            id   = forceRef(record.value('id'))
            self._mapFinanceIdToColumn[id] = code-1
            if code not in distinctCode:
                distinctCode.append(code)
                self._financeColumnNameList.append(name)

        self.table_columns = [
                        ('%30',
                        [u'Исполнитель'], CReportBase.AlignLeft),
                        ('%10',
                        [u'Кол-во обращений'], CReportBase.AlignLeft),
                        ('%10',
                        [u'Кол-во работ'], CReportBase.AlignLeft),
                        ('%8',
                        [u'Обслужено'], CReportBase.AlignLeft),
                        ('%10',
                        [u'Код типа действия '], CReportBase.AlignLeft),
                        ('%10',
                        [u'Название типа Действия'], CReportBase.AlignLeft),
                        ('%5',
                        [u'Количество мероприятий'], CReportBase.AlignLeft),
                        ('%5',
                        [u'Количество'], CReportBase.AlignLeft),
                        ('%5',
                        [u'УЕТ'], CReportBase.AlignLeft)
                       ]
        self.orientation = CPageFormat.Landscape


    def getSetupDialog(self, parent):
        result = CReportClientSummarySetupDialog(parent)
        result.setVisibleDoctor(False)
        result.setVisibleIdentifierType(False)
        result.setVisibleTariffing(True)
        result.setVisibleActionType(True)
        result.setVisibleDetailFinance(True)
        result.setVisibleDetailFinanceEvent(True)
        result.setTitle(self.title())
        return result


    def getDescription(self, params):
        db = QtGui.qApp.db

        begDate                  = params.get('begDate', None)
        endDate                  = params.get('endDate', None)

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
        #actionTypeId = params.get('actionTypeId', None)
        chkDetailFinance = params.get('chkDetailFinance', False)
        chkDetailFinanceEvent = params.get('chkDetailFinanceEvent', False)

        rows = [u'Дата: %s'%dateFieldName]
        if begDate:
            rows.append(u'Начальная дата периода: %s'%forceString(begDate))
        if endDate:
            rows.append(u'Конечная дата периода: %s'%forceString(endDate))

        if chkDetailFinance and chkDetailFinanceEvent:
            rows.append(u'Определять тип финансирования по Договору События')

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
            actionTypeList = params.get('actionTypeList', [])
            if actionTypeList:
                db = QtGui.qApp.db
                table = db.table('ActionType')
                records = db.getRecordList(table, [table['code'], table['name']], [table['id'].inlist(actionTypeList)])
                nameList = []
                for record in records:
                    nameList.append(forceString(record.value('code')) + u' | ' + forceString(record.value('name')))
                rows.append(u'Тип действия: %s'%(u', '.join(name for name in nameList if name)))
            else:
                rows.append(u'Тип действия: не задано')

#            if actionTypeId:
#                rows.append(u'Тип действия: %s'%forceString(db.translate('ActionType', 'id', actionTypeId, 'CONCAT_WS(\' | \', code,name)')))

        if setOrgStructureId:
            rows.append(u'Подразделение назначившего: %s'%forceString(db.translate('OrgStructure', 'id', setOrgStructureId, 'CONCAT_WS(\' | \', code,name)')))

        if setPersonId:
            rows.append(u'Назначивший: %s'%forceString(db.translate('vrbPerson', 'id',        setPersonId, 'name')))

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
        self._mapOrgStructureId2Name.clear()
        self._topOrgStructureIdList = None
        self._mapOrgStructureId2ActualTop.clear()
        self._mapFinaceCoof.clear()
        if 'commonFinanceTypeAmount' in self._defaultValues:
            del self._defaultValues['commonFinanceTypeAmount']

    def getOrgStructureFullName(self, orgStructureId):
        orgStructureName = self._mapOrgStructureId2Name.get(orgStructureId, None)
        if orgStructureName is None:
            orgStructureName = getOrgStructureFullName(orgStructureId) if orgStructureId else u'Не определено'
            self._mapOrgStructureId2Name[orgStructureId] = orgStructureName
        return orgStructureName

    def getActualOrgStructureId(self, personOrgStructureId, condOrgStructureId):
        if not personOrgStructureId:
            return None
        db = QtGui.qApp.db
        table = db.table('OrgStructure')
        if self._topOrgStructureIdList is None:
            self._topOrgStructureIdList = db.getIdList(table, 'id', table['parent_id'].eq(condOrgStructureId))
            if self._topOrgStructureIdList:
                for orgStructureId in self._topOrgStructureIdList:
                    self._mapOrgStructureId2ActualTop[orgStructureId] = orgStructureId
            else:
                self._topOrgStructureIdList.append(condOrgStructureId)

            self._mapOrgStructureId2ActualTop[condOrgStructureId] = condOrgStructureId
        actualId = self._mapOrgStructureId2ActualTop.get(personOrgStructureId, None)
        if not actualId:
            checkListId = [personOrgStructureId]
            parentOrgStructureId = forceRef(db.translate(table, 'id', personOrgStructureId, 'parent_id'))
            checkListId.append(parentOrgStructureId)
            personOrgStructureId = parentOrgStructureId
            while parentOrgStructureId not in self._topOrgStructureIdList:
                parentOrgStructureId = forceRef(db.translate(table, 'id', personOrgStructureId, 'parent_id'))
                personOrgStructureId = parentOrgStructureId
                checkListId.append(parentOrgStructureId)
            actualId = parentOrgStructureId
            for orgStructureId in checkListId:
                self._mapOrgStructureId2ActualTop[orgStructureId] = parentOrgStructureId
        return actualId

    def translateActionTypeAmount2financeAmount(self, actionTypeId, amount, actionId=None):
        def locGetFinanceIdList(actionTypeId):
            db = QtGui.qApp.db
            table = db.table('ActionType_Service')
            idList = db.getIdList(table, 'finance_id', table['master_id'].eq(actionTypeId))
            return idList

    def setDefaultValues(self, item):
        for key, value in self._defaultValues.items():
            item[key] = value
        for financeName in self._financeColumnNameList:
            item[financeName] = 0.0

    def getReportData(self, query, params):
        self.resetHelpers()
        if self._chkDetailFinance and self._financeColumnNameList:
            self._defaultValues['commonFinanceTypeAmount'] = 0.0

        orgStructureId = params.get('orgStructureId', None)
        chkTariffing   = params.get('chkTariffing', False)
        isTariffing    = params.get('isTariffing', 0)
        chkDetailFinance = params.get('chkDetailFinance', False)
        chkDetailFinanceEvent = params.get('chkDetailFinanceEvent', False)

        fakeEventInDay = {}
        actionIdList = []
        actionTypeServiceActionIdList = []
        originalDoneKeys = []

        result = {}

        mapActionId2RecordForNotTariffing = {}

        while query.next():
            record = query.record()

            actionFinanceId = forceRef(record.value('actionFinanceId'))
            eventFinanceId  = forceRef(record.value('eventFinanceId'))
            if chkDetailFinance and chkDetailFinanceEvent:
                actualActionFinanceId = eventFinanceId
            else:
                actualActionFinanceId = actionFinanceId if actionFinanceId else eventFinanceId
            serviceFinanceId = forceRef(record.value('serviceFinanceId'))
            actionTypeServiceId = forceRef(record.value('actionTypeServiceId'))
            actionId        = forceRef(record.value('actionId'))

            if chkTariffing:
                if isTariffing:
                    if not actualActionFinanceId or serviceFinanceId != actualActionFinanceId:
                        continue
                else:
                    if actionTypeServiceId and serviceFinanceId == actualActionFinanceId:
                        if mapActionId2RecordForNotTariffing.get(actionId, True):
                            mapActionId2RecordForNotTariffing[actionId] = None
                    else:
                        if actionId not in mapActionId2RecordForNotTariffing.keys():
                            mapActionId2RecordForNotTariffing[actionId] = record
                    continue

            eventId         = forceRef(record.value('eventId'))
            execPersonId    = forceRef(record.value('execPerson_id'))
            clientId        = forceRef(record.value('clientId'))
            actionTypeId    = forceRef(record.value('actionTypeId'))
            actionTypeCode  = forceString(record.value('actionTypeCode'))
            actionTypeName  = forceString(record.value('actionTypeName'))
            actionPersonId  = forceRef(record.value('actionPersonId'))
            actionEndDate   = forceDateTime(record.value('actionEndDate'))

            personName      = forceString(record.value('personName'))
            personOrgStructureId = self.getActualOrgStructureId(forceRef(record.value('personOrgStructureId')),
                                                                orgStructureId)
            orgStructureName = self.getOrgStructureFullName(personOrgStructureId)
            actualDate      = forceDate(record.value('actualDate'))
            actionAmount    = forceDouble(record.value('actionAmount'))
            uetDoctor       = forceDouble(record.value('uetDoctor'))
            jobTicketId     = forceRef(record.value('jobTicketId'))

            dateKey = unicode(actualDate.toString('yyyy-MM-dd'))
            dateInfoList = result.setdefault('', {})
            orgStructureInfoList = dateInfoList.setdefault((personOrgStructureId, orgStructureName), {})
            personInfoList = orgStructureInfoList.setdefault((actionPersonId, personName), {})
            actionTypeInfo = personInfoList.get((actionTypeId, actionTypeCode, actionTypeName), None)
            if actionTypeInfo is None:
                actionTypeInfo = {}
                self.setDefaultValues(actionTypeInfo)
                personInfoList[(actionTypeId, actionTypeCode, actionTypeName)] = actionTypeInfo

            fakeEventList = fakeEventInDay.setdefault(dateKey, [])
            if execPersonId == actionPersonId and (eventId, actionPersonId) not in fakeEventList:
                fakeEventList.append((eventId, actionPersonId))
                actionTypeInfo['count'] += 1
            if actionId not in actionIdList:
                actionTypeInfo['actionCount'] += 1
                actionTypeInfo['amount'] += actionAmount
                actionTypeInfo['uet']    += uetDoctor
                if jobTicketId:
                    actionTypeInfo['jobTicketCount'] += 1
                if clientId and actionEndDate and actionEndDate:
                    doneKey = (clientId, actionPersonId, forceString(actionEndDate))
                    if doneKey not in originalDoneKeys:
                        actionTypeInfo['doneCount'] += 1
                        originalDoneKeys.append(doneKey)
                actionIdList.append(actionId)

            if ((actionTypeServiceId, actionId) not in actionTypeServiceActionIdList) and serviceFinanceId:
                actionTypeServiceActionIdList.append((actionTypeServiceId, actionId))
                financeColumn = self._mapFinanceIdToColumn.get(actualActionFinanceId, None)
                if financeColumn:
                    actionTypeInfo[self._financeColumnNameList[financeColumn]] += actionAmount
                    if 'commonFinanceTypeAmount' in actionTypeInfo:
                        actionTypeInfo['commonFinanceTypeAmount'] += actionAmount


            # мне так лень было все переписывать из-за этих тарифицируемых и нет что я сделал так.
        if chkTariffing and not isTariffing:
            fakeEventInDay = {}
            actionIdList = []
            actionTypeServiceActionIdList = []
            originalDoneKeys = []

            result = {}
            for record in mapActionId2RecordForNotTariffing.values():
                if not record:
                    continue

                actionFinanceId = forceRef(record.value('actionFinanceId'))
                eventFinanceId  = forceRef(record.value('eventFinanceId'))
                actualActionFinanceId = actionFinanceId if actionFinanceId else eventFinanceId
                serviceFinanceId = forceRef(record.value('serviceFinanceId'))
                actionTypeServiceId = forceRef(record.value('actionTypeServiceId'))
                actionId        = forceRef(record.value('actionId'))

                eventId         = forceRef(record.value('eventId'))
                execPersonId    = forceRef(record.value('execPerson_id'))
                clientId        = forceRef(record.value('clientId'))
                actionTypeId    = forceRef(record.value('actionTypeId'))
                actionTypeCode  = forceString(record.value('actionTypeCode'))
                actionTypeName  = forceString(record.value('actionTypeName'))
                actionPersonId  = forceRef(record.value('actionPersonId'))
                actionEndDate   = forceDateTime(record.value('actionEndDate'))

                personName      = forceString(record.value('personName'))
                personOrgStructureId = self.getActualOrgStructureId(forceRef(record.value('personOrgStructureId')),
                                                                    orgStructureId)
                orgStructureName = self.getOrgStructureFullName(personOrgStructureId)
                actualDate      = forceDate(record.value('actualDate'))
                actionAmount    = forceDouble(record.value('actionAmount'))
                uetDoctor       = forceDouble(record.value('uetDoctor'))
                jobTicketId     = forceRef(record.value('jobTicketId'))

                dateKey = unicode(actualDate.toString('yyyy-MM-dd'))
                dateInfoList = result.setdefault('', {})
                orgStructureInfoList = dateInfoList.setdefault((personOrgStructureId, orgStructureName), {})
                personInfoList = orgStructureInfoList.setdefault((actionPersonId, personName), {})
                actionTypeInfo = personInfoList.get((actionTypeId, actionTypeCode, actionTypeName), None)
                if actionTypeInfo is None:
                    actionTypeInfo = {}
                    self.setDefaultValues(actionTypeInfo)
                    personInfoList[(actionTypeId, actionTypeCode, actionTypeName)] = actionTypeInfo
                fakeEventList = fakeEventInDay.setdefault(dateKey, [])
                if execPersonId == actionPersonId and (eventId, actionPersonId) not in fakeEventList:
                    fakeEventList.append((eventId, actionPersonId))
                    actionTypeInfo['count'] += 1
                if actionId not in actionIdList:
                    actionTypeInfo['actionCount'] += 1
                    actionTypeInfo['amount'] += actionAmount
                    actionTypeInfo['uet']    += uetDoctor
                    if jobTicketId:
                        actionTypeInfo['jobTicketCount'] += 1
                    if clientId and actionEndDate:
                        doneKey = (clientId, actionPersonId, forceString(actionEndDate))
                        if doneKey not in originalDoneKeys:
                            actionTypeInfo['doneCount'] += 1
                            originalDoneKeys.append(doneKey)
                    actionIdList.append(actionId)

                if ((actionTypeServiceId, actionId) not in actionTypeServiceActionIdList) and serviceFinanceId:
                    actionTypeServiceActionIdList.append((actionTypeServiceId, actionId))
                    financeColumn = self._mapFinanceIdToColumn.get(actualActionFinanceId, None)
                    if financeColumn:
                        actionTypeInfo[self._financeColumnNameList[financeColumn]] += actionAmount
                        if 'commonFinanceTypeAmount' in actionTypeInfo:
                            actionTypeInfo['commonFinanceTypeAmount'] += actionAmount


        return result


    def getCoof(self, actionTypeId, financeId, actionTypeCode):
        u"""How many services ActionType has for financeId"""
        result = self._mapFinaceCoof.get(actionTypeId, None)
        if actionTypeCode == '01':
            pass
        if result is None:
            result = {}
            for name in self._financeColumnNameList:
                result[name] = 0
            db = QtGui.qApp.db
            table = db.table('ActionType_Service')
            idList = db.getIdList(table, 'finance_id', table['master_id'].eq(actionTypeId))
            for id in idList:
                financeColumn = self._mapFinanceIdToColumn[id]
                result[self._financeColumnNameList[financeColumn]] += 1
            self._mapFinaceCoof[actionTypeId] = result
        financeColumn = self._mapFinanceIdToColumn[financeId]
        return result[self._financeColumnNameList[financeColumn]]



    def buildInt(self, params, cursor):
        chkDetailActions = params.get('chkDetailActions', False)
        chkDetailOrgStructure = params.get('chkDetailOrgStructure', False)
        self._chkDetailFinance = chkDetailFinance = params.get('chkDetailFinance', False)

        query = selectData(params)
        reportData = self.getReportData(query, params)

        if not chkDetailActions:
            self.removeColumn(4)
            self.removeColumn(4)

            self._columnName2Index['actionCount'] = 4
            self._columnName2Index['amount'] = 5
            self._columnName2Index['uet'] = 6

        else:
            self._columnName2Index['actionCount'] = 6
            self._columnName2Index['amount'] = 7
            self._columnName2Index['uet'] = 8

        if chkDetailFinance:
            for name in self._financeColumnNameList:
                self.addColumn(('%5', [name], CReportBase.AlignLeft))
            if self._financeColumnNameList:
                self.addColumn(('%5', [u'Всего услуг'], CReportBase.AlignLeft))
            self._columnName2Index['commonFinanceTypeAmount'] = self.colCount()-1

        table = self.createTable(cursor)

        dateKeyList = reportData.keys()
        dateKeyList.sort()

        boldChars = QtGui.QTextCharFormat()
        boldChars.setFontWeight(QtGui.QFont.Bold)

        titleMergeLength = self.colCount()

        result = {}
        self.setDefaultValues(result)

        for dateIdx, dateKey in enumerate(dateKeyList):
            tableRow = table.addRow()

            dateInfoList = reportData[dateKey]

            orgStructureKeyList = dateInfoList.keys()
            orgStructureKeyList.sort(key=lambda item: item[1])

            lastOrgStructureIdx = len(orgStructureKeyList)-1

            for orgStructureIdx, orgStructureKey in enumerate(orgStructureKeyList):
                orgStructureId, orgStructureName = orgStructureKey

                if chkDetailOrgStructure:
                    table.setText(tableRow, 0, orgStructureName, charFormat=boldChars)
                    table.mergeCells(tableRow, 0, 1, titleMergeLength)
                    tableRow = table.addRow()

                orgStructureInfoList = dateInfoList[orgStructureKey]

                personKeyList = orgStructureInfoList.keys()
                personKeyList.sort(key=lambda item: item[1])

                orgStructureResult = {}
                self.setDefaultValues(orgStructureResult)

                lastPersonIdx = len(personKeyList) - 1

                for personIdx, personKey in enumerate(personKeyList):
                    personId, personName = personKey

                    if chkDetailActions:
                        table.setText(tableRow, 0, personName, charFormat=boldChars)
                        table.mergeCells(tableRow, 0, 1, titleMergeLength)
                        tableRow = table.addRow()
                    else:
                        table.setText(tableRow, 0, personName)

                    personInfoList = orgStructureInfoList[personKey]

                    actionTypeKeyList = personInfoList.keys()
                    actionTypeKeyList.sort(key=lambda item: (item[1], item[2]))

                    personResult = {}
                    self.setDefaultValues(personResult)

                    for actionTypeIdx, actionTypeKey in enumerate(actionTypeKeyList):
                        actionTypeId, actionTypeCode, actionTypeName = actionTypeKey

                        actionTypeValues = personInfoList[actionTypeKey]

                        if chkDetailActions:
                            if actionTypeIdx:
                                tableRow = table.addRow()
                            table.setText(tableRow, 4, actionTypeCode)
                            table.setText(tableRow, 5, actionTypeName)
                            self.printValuesWithCalcResult(tableRow, table, actionTypeValues, personResult)
                        else:
                            self.calcResult(personResult, actionTypeValues)

                    if chkDetailActions:
                        tableRow = table.addRow()
                        table.setText(tableRow, 0, u'Итого на врача', charFormat=boldChars)
                    self.printValuesWithCalcResult(tableRow, table, personResult, orgStructureResult)
                    if personIdx != lastPersonIdx:
                        tableRow = table.addRow()

                if chkDetailActions:
                    table.mergeCells(tableRow, 0, tableRow-personIdx, 1)

                if chkDetailOrgStructure:
                    tableRow = table.addRow()
                    table.setText(tableRow, 0, u'Итого на подразделение', charFormat=boldChars)
                    self.printValuesWithCalcResult(tableRow, table, orgStructureResult, result)
                    if orgStructureIdx != lastOrgStructureIdx:
                        tableRow = table.addRow()
                else:
                    if orgStructureIdx != lastOrgStructureIdx:
                        tableRow = table.addRow()
                    self.calcResult(result, orgStructureResult)

        tableRow = table.addRow()
        table.setText(tableRow, 0, u'Итого', charFormat=boldChars)
        self.printValues(tableRow, table, result)

        return result


    def getTableColumnByName(self, columnName):
        if columnName in self._financeColumnNameList:
            if self._chkDetailFinance:
                return self._columnName2Index['uet'] + 1 + self._financeColumnNameList.index(columnName)
            return None
        else:
            return self._columnName2Index[columnName]


