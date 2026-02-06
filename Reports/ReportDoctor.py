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

    setOrgStructureId   = params.get('setOrgStructureId', None)
    orgStructureId      = params.get('orgStructureId', None)
    specialityId        = params.get('specialityId', None)
    setSpecialityId     = params.get('setSpecialityId', None)
    financeId           = params.get('financeId', None)
    confirmation        = params.get('confirmation', False)
    confirmationBegDate = params.get('confirmationBegDate', None)
    confirmationEndDate = params.get('confirmationEndDate', None)
    confirmationType    = params.get('confirmationType', 0)
    eventTypeId         = params.get('eventTypeId', None)
    chkActionTypeClass  = params.get('chkActionTypeClass', False)
    actionTypeClass     = params.get('actionTypeClass', None)
    #actionTypeId        = params.get('actionTypeId', None)
    actionTypeList      = params.get('actionTypeList', [])
    chkDetailSpeciality = params.get('chkDetailSpeciality', False)
    db = QtGui.qApp.db
    tableEvent                = db.table('Event')
    tableContract             = db.table('Contract')
    tableAction               = db.table('Action')
    tableActionType           = db.table('ActionType')
    tableActionTypeService    = db.table('ActionType_Service')
    tableActionFileAttach     = db.table('Action_FileAttach')
    tableService              = db.table('rbService')
    tableClient               = db.table('Client')
    tableVisit                = db.table('Visit')
    tableSpeciality           = db.table('rbSpeciality')
    tablePerson               = db.table('vrbPersonWithSpeciality')
    tableSetPerson            = db.table('vrbPersonWithSpeciality').alias('SetVrbPersonSpeciality')
    tableAccountItem          = db.table('Account_Item')
    queryTable = tableEvent
    queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
    queryTable = queryTable.leftJoin(tableAction, tableAction['event_id'].eq(tableEvent['id']))
    queryTable = queryTable.leftJoin(tableVisit, tableVisit['event_id'].eq(tableEvent['id']))
    queryTable = queryTable.leftJoin(tablePerson, tablePerson['id'].eq(tableAction['person_id']))
    queryTable = queryTable.leftJoin(tableActionFileAttach, db.joinAnd([tableActionFileAttach['master_id'].eq(tableAction['id']), tableActionFileAttach['respSigner_id'].eq(tableAction['person_id']), tableActionFileAttach['deleted'].eq(0)]))
    if chkDetailSpeciality:
        queryTable = queryTable.leftJoin(tableSpeciality, tableSpeciality['id'].eq(tablePerson['speciality_id']))
    queryTable = queryTable.leftJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
    queryTable = queryTable.leftJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
    actionTypeServiceJoinCond = db.joinAnd([tableActionTypeService['master_id'].eq(tableActionType['id']),
                                           tableActionTypeService['finance_id'].eq(tableAction['finance_id'])])
    queryTable = queryTable.leftJoin(tableActionTypeService,actionTypeServiceJoinCond)
    queryTable = queryTable.leftJoin(tableService, tableService['id'].eq(tableActionTypeService['service_id']))
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
            tableAction['id'].alias('actionId'),
            tableAction['event_id'].alias('eventId'),
            '''IF(Action_FileAttach.respSignatureBytes IS NOT NULL, 1, 0) AS isRespSignatureBytes''',
            tableActionType['id'].alias('actionTypeId'),
            tableActionType['code'].alias('actionTypeCode'),
            tableActionType['name'].alias('actionTypeName'),
            tableAction['amount'].alias('actionAmount'),
            tableVisit['id'].alias('visitId'),
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
            '''(SELECT ActionProperty_Job_Ticket.`value`
        FROM ActionProperty_Job_Ticket
        LEFT JOIN ActionProperty ON ActionProperty.`id`=ActionProperty_Job_Ticket.`id`
        LEFT JOIN Action AS ActionJobTicket ON ActionJobTicket.`id`=ActionProperty.`action_id`
        WHERE ActionJobTicket.`id`=Action.`id`) AS `jobTicketId` '''
           ]
    if chkDetailSpeciality:
        cols.append(tableSpeciality['id'].alias('specialityId'))
        cols.append(tableSpeciality['name'].alias('specialityName'))
    cond.append('Visit.id IS NULL OR Visit.`deleted`=0')
    order = u'jobTicketId DESC, vrbPersonWithSpeciality.id ASC, uetDoctor ASC'
    stmt = db.selectStmt(queryTable, cols, cond, order)
    return db.query(stmt)


class CReportDoctor(CReportEx):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self._mapFinanceIdToColumn = {}
        self._financeColumnNameList = []
        self._topOrgStructureIdList = None
        self._mapOrgStructureId2ActualTop = {}
        self._mapFinaceCoof = {}
        self._mapOrgStructureId2Name = {}
        self._columnName2Index = {'visitCount':1, 'eventCount':2}
        self._defaultValues = {'visitCount':0, 'eventCount':0, 'actionCount':0, 'amount':0.0, 'uet':0.0, 'respSignatureBytes':0}
        self.setTitle(u'Сводка на врачей')
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
                        ('%5',
                        [u'Кол-во Визитов'], CReportBase.AlignLeft),
                        ('%5',
                        [u'Кол-во обращений'], CReportBase.AlignLeft),
                        ('%11',
                        [u'Код типа действия '], CReportBase.AlignLeft),
                        ('%23',
                        [u'Название типа Действия'], CReportBase.AlignLeft),
                        ('%5',
                        [u'Количество мероприятий'], CReportBase.AlignLeft),
                        ('%5',
                        [u'Количество'], CReportBase.AlignLeft),
                        ('%5',
                        [u'УЕТ'], CReportBase.AlignLeft),
                        ('%11',
                        [u'ЭЦП'], CReportBase.AlignLeft)
                       ]
        self.orientation = CPageFormat.Landscape


    def getSetupDialog(self, parent):
        result = CReportClientSummarySetupDialog(parent)
        result.setVisibleDetailSpeciality(True)
        result.setVisibleDoctor(False)
        result.setVisibleIdentifierType(False)
        result.setVisibleTariffing(True)
        result.setVisibleActionType(True)
        result.setTitle(self.title())
        return result


    def getDescription(self, params):
        db = QtGui.qApp.db
        begDate                  = params.get('begDate', None)
        endDate                  = params.get('endDate', None)
        dateFieldName = {
                     0 : u'выполнения',
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
        rows = [u'Дата мероприятия: %s'%dateFieldName]
        if begDate:
            rows.append(u'Начальная дата периода: %s'%forceString(begDate))
        if endDate:
            rows.append(u'Конечная дата периода: %s'%forceString(endDate))
        rows.append(u'Обращения отбираются по дате выполнения')
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
        orgStructureId      = params.get('orgStructureId', None)
        chkTariffing        = params.get('chkTariffing', False)
        isTariffing         = params.get('isTariffing', 0)
        chkDetailSpeciality = params.get('chkDetailSpeciality', False)
        fakeEventInDay = {}
        actionIdList = []
        visitIdList = []

        actionTypeServiceActionIdList = []
        originalDoneKeys = []
        result = {}
        actionPersonIdList = []
        mapActionId2RecordForNotTariffing = {}
        while query.next():
            record = query.record()
            actionFinanceId = forceRef(record.value('actionFinanceId'))
            eventFinanceId  = forceRef(record.value('eventFinanceId'))
            actualActionFinanceId = actionFinanceId if actionFinanceId else eventFinanceId
            serviceFinanceId = forceRef(record.value('serviceFinanceId'))
            actionTypeServiceId = forceRef(record.value('actionTypeServiceId'))
            actionId        = forceRef(record.value('actionId'))
            visitId         = forceRef(record.value('visitId'))
            isRespSignatureBytes = forceInt(record.value('isRespSignatureBytes'))
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
            actualDate       = forceDate(record.value('actualDate'))
            actionAmount     = forceDouble(record.value('actionAmount'))
            uetDoctor        = forceDouble(record.value('uetDoctor'))

            dateKey = unicode(actualDate.toString('yyyy-MM-dd'))
            dateInfoList = result.setdefault('', {})
            orgStructureInfoList = dateInfoList.setdefault((personOrgStructureId, orgStructureName), {})
            if chkDetailSpeciality:
                specialityId   = forceRef(record.value('specialityId'))
                specialityName = forceString(record.value('specialityName')) if specialityId else u'Не определена'
                specialityInfoList = orgStructureInfoList.setdefault((specialityId, specialityName), {})
                personInfoList = specialityInfoList.setdefault((actionPersonId, personName), {})
            else:
                personInfoList = orgStructureInfoList.setdefault((actionPersonId, personName), {})
            actionTypeInfo = personInfoList.get((actionTypeId, actionTypeCode, actionTypeName), None)
            if actionTypeInfo is None:
                actionTypeInfo = {}
                self.setDefaultValues(actionTypeInfo)
                personInfoList[(actionTypeId, actionTypeCode, actionTypeName)] = actionTypeInfo
            fakeEventList = fakeEventInDay.setdefault(dateKey, [])
            if (eventId, actionPersonId) not in fakeEventList:
                fakeEventList.append((eventId, actionPersonId))
                actionTypeInfo['eventCount'] += 1
            if visitId not in visitIdList:
                visitIdList.append(visitId)
                actionTypeInfo['visitCount'] += 1
            if actionId not in actionIdList:
                actionTypeInfo['actionCount'] += 1
                actionTypeInfo['amount'] += actionAmount
                actionTypeInfo['uet']    += uetDoctor
                actionTypeInfo['respSignatureBytes'] += isRespSignatureBytes
                if clientId and actionEndDate:
                    doneKey = (clientId, actionPersonId, forceString(actionEndDate))
                    if doneKey not in originalDoneKeys:
                        originalDoneKeys.append(doneKey)
                actionIdList.append(actionId)
            if ((actionTypeServiceId, actionId) not in actionTypeServiceActionIdList) and serviceFinanceId:
                actionTypeServiceActionIdList.append((actionTypeServiceId, actionId))
                financeColumn = self._mapFinanceIdToColumn.get(actualActionFinanceId, None)
                if financeColumn:
                    actionTypeInfo[self._financeColumnNameList[financeColumn]] += actionAmount
                    if 'commonFinanceTypeAmount' in actionTypeInfo:
                        actionTypeInfo['commonFinanceTypeAmount'] += actionAmount
            if actionPersonId not in actionPersonIdList:
                actionPersonIdList.append(actionPersonId)

        if chkTariffing and not isTariffing:
            fakeEventInDay = {}
            actionIdList = []
            visitIdList = []
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
                visitId         = forceRef(record.value('visitId'))
                eventId         = forceRef(record.value('eventId'))
                clientId        = forceRef(record.value('clientId'))
                actionTypeId    = forceRef(record.value('actionTypeId'))
                actionTypeCode  = forceString(record.value('actionTypeCode'))
                actionTypeName  = forceString(record.value('actionTypeName'))
                actionPersonId  = forceRef(record.value('actionPersonId'))
                actionEndDate   = forceDateTime(record.value('actionEndDate'))
                personName      = forceString(record.value('personName'))
                isRespSignatureBytes = forceInt(record.value('isRespSignatureBytes'))
                personOrgStructureId = self.getActualOrgStructureId(forceRef(record.value('personOrgStructureId')),
                                                                    orgStructureId)
                orgStructureName = self.getOrgStructureFullName(personOrgStructureId)
                actualDate      = forceDate(record.value('actualDate'))
                actionAmount    = forceDouble(record.value('actionAmount'))
                uetDoctor       = forceDouble(record.value('uetDoctor'))

                dateKey = unicode(actualDate.toString('yyyy-MM-dd'))
                dateInfoList = result.setdefault('', {})
                orgStructureInfoList = dateInfoList.setdefault((personOrgStructureId, orgStructureName), {})
                if chkDetailSpeciality:
                    specialityId   = forceRef(record.value('specialityId'))
                    specialityName = forceString(record.value('specialityName')) if specialityId else u'Не определена'
                    specialityInfoList = orgStructureInfoList.setdefault((specialityId, specialityName), {})
                    personInfoList = specialityInfoList.setdefault((actionPersonId, personName), {})
                else:
                    personInfoList = orgStructureInfoList.setdefault((actionPersonId, personName), {})
                actionTypeInfo = personInfoList.get((actionTypeId, actionTypeCode, actionTypeName), None)
                if actionTypeInfo is None:
                    actionTypeInfo = {}
                    self.setDefaultValues(actionTypeInfo)
                    personInfoList[(actionTypeId, actionTypeCode, actionTypeName)] = actionTypeInfo
                fakeEventList = fakeEventInDay.setdefault(dateKey, [])
                if (eventId, actionPersonId) not in fakeEventList:
                    fakeEventList.append((eventId, actionPersonId))
                    actionTypeInfo['eventCount'] += 1
                if visitId not in visitIdList:
                    visitIdList.append(visitId)
                    actionTypeInfo['visitCount'] += 1
                if actionId not in actionIdList:
                    actionTypeInfo['actionCount'] += 1
                    actionTypeInfo['amount'] += actionAmount
                    actionTypeInfo['uet']    += uetDoctor
                    actionTypeInfo['respSignatureBytes'] += isRespSignatureBytes
                    if clientId and actionEndDate:
                        doneKey = (clientId, actionPersonId, forceString(actionEndDate))
                        if doneKey not in originalDoneKeys:
                            originalDoneKeys.append(doneKey)
                    actionIdList.append(actionId)
                if ((actionTypeServiceId, actionId) not in actionTypeServiceActionIdList) and serviceFinanceId:
                    actionTypeServiceActionIdList.append((actionTypeServiceId, actionId))
                    financeColumn = self._mapFinanceIdToColumn.get(actualActionFinanceId, None)
                    if financeColumn:
                        actionTypeInfo[self._financeColumnNameList[financeColumn]] += actionAmount
                        if 'commonFinanceTypeAmount' in actionTypeInfo:
                            actionTypeInfo['commonFinanceTypeAmount'] += actionAmount
                if actionPersonId not in actionPersonIdList:
                    actionPersonIdList.append(actionPersonId)
        visitListId = []
        visitPersonList = {}
        visitOrgStructureList = {}
        begDate = params.get('begDate', None)
        endDate = params.get('endDate', None)
        db = QtGui.qApp.db
        tableVisit = db.table('Visit')
        tablePerson = db.table('vrbPersonWithSpeciality')
        cols = [tableVisit['id'],
                tableVisit['event_id'],
                tableVisit['person_id'],
                tableVisit['date'],
                tablePerson['orgStructure_id'].alias('personOrgStructureId')
                ]
        cond = [tableVisit['deleted'].eq(0),
                tableVisit['date'].lt(endDate.addDays(1)),
                tableVisit['date'].ge(begDate),
                tableVisit['person_id'].inlist(actionPersonIdList)
                ]
        queryTable = tableVisit.leftJoin(tablePerson, tablePerson['id'].eq(tableVisit['person_id']))
        records = db.getRecordList(queryTable, cols, cond)
        for record in records:
            visitId = forceRef(record.value('id'))
            if visitId and visitId not in visitListId:
                visitListId.append(visitId)
            eventId = forceRef(record.value('event_id'))
            personId = forceRef(record.value('person_id'))
            personOrgStructureId = self.getActualOrgStructureId(forceRef(record.value('personOrgStructureId')),
                                                            orgStructureId)
            visitPersonListId = visitPersonList.get((personId, personOrgStructureId), 0)
            visitPersonListId += 1
            visitPersonList[(personId, personOrgStructureId)] = visitPersonListId
            visitOrgStructureListId = visitOrgStructureList.get(personOrgStructureId, 0)
            visitOrgStructureListId += 1
            visitOrgStructureList[personOrgStructureId] = visitOrgStructureListId
        eventListId = []
        eventPersonList = {}
        eventOrgStructureList = {}
        begDate = params.get('begDate', None)
        endDate = params.get('endDate', None)
        db = QtGui.qApp.db
        tableEvent = db.table('Event')
        tablePerson = db.table('vrbPersonWithSpeciality')
        cols = [tableEvent['id'],
                tableEvent['execPerson_id'],
                tablePerson['orgStructure_id'].alias('personOrgStructureId')
                ]
        cond = [tableEvent['deleted'].eq(0),
                tableEvent['execDate'].isNotNull(),
                tableEvent['execDate'].lt(endDate.addDays(1)),
                tableEvent['execDate'].ge(begDate),
                tableEvent['execPerson_id'].inlist(actionPersonIdList)
                ]
        queryTable = tableEvent.leftJoin(tablePerson, tablePerson['id'].eq(tableEvent['execPerson_id']))
        records = db.getRecordList(queryTable, cols, cond)
        for record in records:
            eventId = forceRef(record.value('id'))
            if eventId and eventId not in eventListId:
                eventListId.append(eventId)
                personId = forceRef(record.value('execPerson_id'))
                personOrgStructureId = self.getActualOrgStructureId(forceRef(record.value('personOrgStructureId')),
                                                                orgStructureId)
                eventPersonListId = eventPersonList.get((personId, personOrgStructureId), 0)
                eventPersonListId += 1
                eventPersonList[(personId, personOrgStructureId)] = eventPersonListId
                eventOrgStructureListId = eventOrgStructureList.get(personOrgStructureId, 0)
                eventOrgStructureListId += 1
                eventOrgStructureList[personOrgStructureId] = eventOrgStructureListId
        return result, visitPersonList, visitOrgStructureList, eventPersonList, eventOrgStructureList


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
        chkDetailActions       = params.get('chkDetailActions', False)
        chkDetailOrgStructure  = params.get('chkDetailOrgStructure', False)
        chkDetailSpeciality    = params.get('chkDetailSpeciality', False)
        self._chkDetailFinance = chkDetailFinance = params.get('chkDetailFinance', False)
        query = selectData(params)
        reportData, visitPersonList, visitOrgStructureList, eventPersonList, eventOrgStructureList = self.getReportData(query, params)
        if not chkDetailActions:
            self.removeColumn(3)
            self.removeColumn(3)
            self._columnName2Index['actionCount'] = 3
            self._columnName2Index['amount'] = 4
            self._columnName2Index['uet'] = 5
            self._columnName2Index['respSignatureBytes'] = 6
        else:
            self._columnName2Index['actionCount'] = 5
            self._columnName2Index['amount'] = 6
            self._columnName2Index['uet'] = 7
            self._columnName2Index['respSignatureBytes'] = 8
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
        if chkDetailSpeciality:
            for dateIdx, dateKey in enumerate(dateKeyList):
                tableRow = table.addRow()
                dateInfoList = reportData[dateKey]
                orgStructureKeyList = dateInfoList.keys()
                orgStructureKeyList.sort(key=lambda item: item[1])
                lastOrgStructureIdx = len(orgStructureKeyList)-1
                for orgStructureIdx, orgStructureKey in enumerate(orgStructureKeyList):
                    keyPOList = []
                    orgStructureId, orgStructureName = orgStructureKey
                    if chkDetailOrgStructure:
                        table.setText(tableRow, 0, orgStructureName, charFormat=boldChars)
                        table.mergeCells(tableRow, 0, 1, titleMergeLength)
                        tableRow = table.addRow()
                    specialityInfoList = dateInfoList.get(orgStructureKey, [])
                    specialityKeyList = specialityInfoList.keys()
                    orgStructureResult = {}
                    self.setDefaultValues(orgStructureResult)
                    specialityKeyList.sort(key=lambda item: item[1])
                    lastSpecialityIdx = len(specialityKeyList)-1
                    for specialityIdx, specialityKey in enumerate(specialityKeyList):
                        keyPSList = []
                        resultSP = {}
                        self.setDefaultValues(resultSP)
                        specialityId, specialityName = specialityKey
                        table.setText(tableRow, 0, specialityName, charFormat=boldChars)
                        table.mergeCells(tableRow, 0, 1, titleMergeLength)
                        tableRow = table.addRow()
                        personInfoList = specialityInfoList.get(specialityKey, [])
                        personKeyList = personInfoList.keys()
                        personKeyList.sort(key=lambda item: item[1])
                        specialityResult = {}
                        self.setDefaultValues(specialityResult)
                        lastPersonIdx = len(personKeyList) - 1
                        for personIdx, personKey in enumerate(personKeyList):
                            personId, personName = personKey
                            if chkDetailActions:
                                table.setText(tableRow, 0, personName, charFormat=boldChars)
                                table.mergeCells(tableRow, 0, 1, titleMergeLength)
                                tableRow = table.addRow()
                            else:
                                table.setText(tableRow, 0, personName)
                            actionInfoList = personInfoList.get(personKey, [])
                            actionTypeKeyList = actionInfoList.keys()
                            actionTypeKeyList.sort(key=lambda item: (item[1], item[2]))
                            personResult = {}
                            self.setDefaultValues(personResult)
                            for actionTypeIdx, actionTypeKey in enumerate(actionTypeKeyList):
                                actionTypeId, actionTypeCode, actionTypeName = actionTypeKey
                                actionTypeValues = actionInfoList.get(actionTypeKey, [])
                                if chkDetailActions:
                                    if actionTypeIdx:
                                        tableRow = table.addRow()
                                    table.setText(tableRow, 3, actionTypeCode)
                                    table.setText(tableRow, 4, actionTypeName)
                                    self.printValuesWithCalcResult(tableRow, table, actionTypeValues, personResult)
                                else:
                                    self.calcResult(personResult, actionTypeValues)
                            if chkDetailActions:
                                tableRow = table.addRow()
                                table.setText(tableRow, 0, u'Итого на врача', charFormat=boldChars)
                            keyPO = (personId, orgStructureId)
                            if keyPO not in keyPOList:
                                keyPOList.append(keyPO)
                            if keyPO not in keyPSList:
                                keyPSList.append(keyPO)
                            self.printValuesWithCalcResult(tableRow, table, personResult, orgStructureResult, visitPersonList.get(keyPO, 0), eventPersonList.get(keyPO, 0), charFormat=boldChars)
                            self.calcResult(specialityResult, personResult, visitPersonList, eventPersonList, [keyPO])
                            if personIdx != lastPersonIdx:
                                tableRow = table.addRow()
                        if chkDetailActions:
                            table.mergeCells(tableRow, 0, tableRow-personIdx, 1)
                        tableRow = table.addRow()
                        table.setText(tableRow, 0, u'Итого по специальности', charFormat=boldChars)
                        self.calcResult(resultSP, specialityResult, visitPersonList, eventPersonList, keyPSList)
                        for columnName, value in resultSP.items():
                            tableColumn = self.getTableColumnByName(columnName)
                            if tableColumn >= 0:
                                table.setText(tableRow, tableColumn, value, charFormat=boldChars)
                        if specialityIdx != lastSpecialityIdx:
                            tableRow = table.addRow()
                    if chkDetailOrgStructure:
                        tableRow = table.addRow()
                        table.setText(tableRow, 0, u'Итого на подразделение', charFormat=boldChars)
                        self.printValuesWithCalcResult(tableRow, table, orgStructureResult, result, visitOrgStructureList.get(orgStructureId, 0), eventOrgStructureList.get(orgStructureId, 0), charFormat=boldChars)
                    else:
                        self.calcResult(result, orgStructureResult, visitPersonList, eventPersonList, keyPOList)
                    if orgStructureIdx != lastOrgStructureIdx:
                        tableRow = table.addRow()
            tableRow = table.addRow()
            table.setText(tableRow, 0, u'Итого', charFormat=boldChars)
            for columnName, value in result.items():
                tableColumn = self.getTableColumnByName(columnName)
                if tableColumn >= 0:
                    table.setText(tableRow, tableColumn, value, charFormat=boldChars)
        else:
            for dateIdx, dateKey in enumerate(dateKeyList):
                tableRow = table.addRow()
                dateInfoList = reportData[dateKey]
                orgStructureKeyList = dateInfoList.keys()
                orgStructureKeyList.sort(key=lambda item: item[1])
                lastOrgStructureIdx = len(orgStructureKeyList)-1
                for orgStructureIdx, orgStructureKey in enumerate(orgStructureKeyList):
                    keyPOList = []
                    orgStructureId, orgStructureName = orgStructureKey
                    if chkDetailOrgStructure:
                        table.setText(tableRow, 0, orgStructureName, charFormat=boldChars)
                        table.mergeCells(tableRow, 0, 1, titleMergeLength)
                        tableRow = table.addRow()
                    if chkDetailSpeciality:
                        # table.setText(tableRow, 0, specialityName, charFormat=boldChars) # specialityId, specialityName
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
                                table.setText(tableRow, 3, actionTypeCode)
                                table.setText(tableRow, 4, actionTypeName)
                                self.printValuesWithCalcResult(tableRow, table, actionTypeValues, personResult)
                            else:
                                self.calcResult(personResult, actionTypeValues)
                        if chkDetailActions:
                            tableRow = table.addRow()
                            table.setText(tableRow, 0, u'Итого на врача', charFormat=boldChars)
                        keyPO = (personId, orgStructureId)
                        if keyPO not in keyPOList:
                            keyPOList.append(keyPO)
                        self.printValuesWithCalcResult(tableRow, table, personResult, orgStructureResult, visitPersonList.get(keyPO, 0), eventPersonList.get(keyPO, 0), charFormat=boldChars)
                        if personIdx != lastPersonIdx:
                            tableRow = table.addRow()
                    if chkDetailActions:
                        table.mergeCells(tableRow, 0, tableRow-personIdx, 1)
                    if chkDetailOrgStructure:
                        tableRow = table.addRow()
                        table.setText(tableRow, 0, u'Итого на подразделение', charFormat=boldChars)
                        self.printValuesWithCalcResult(tableRow, table, orgStructureResult, result, visitOrgStructureList.get(orgStructureId, 0), eventOrgStructureList.get(orgStructureId, 0), charFormat=boldChars)
                        if orgStructureIdx != lastOrgStructureIdx:
                            tableRow = table.addRow()
                    else:
                        if orgStructureIdx != lastOrgStructureIdx:
                            tableRow = table.addRow()
                        self.calcResult(result, orgStructureResult, visitPersonList, eventPersonList, keyPOList)
            tableRow = table.addRow()
            table.setText(tableRow, 0, u'Итого', charFormat=boldChars)
            for columnName, value in result.items():
                tableColumn = self.getTableColumnByName(columnName)
                if tableColumn >= 0:
                    table.setText(tableRow, tableColumn, value, charFormat=boldChars)
        return result


    def printValuesWithCalcResult(self, tableRow, table, item, result, valueVisit=None, valueEvent=None, charFormat=None):
        for columnName, value in item.items():
            if columnName not in u'visitCount' and columnName not in u'eventCount':
                self.printColumn(columnName, tableRow, table, value)
                result[columnName] += value
        if valueVisit is not None:
            tableColumn = self.getTableColumnByName('visitCount')
            result['visitCount'] += valueVisit
            table.setText(tableRow, tableColumn, valueVisit, charFormat)
        if valueEvent is not None:
            tableColumn = self.getTableColumnByName('eventCount')
            result['eventCount'] += valueEvent
            table.setText(tableRow, tableColumn, valueEvent, charFormat)


    def getTableColumnByName(self, columnName):
        if columnName in self._financeColumnNameList:
            if self._chkDetailFinance:
                return self._columnName2Index['respSignatureBytes'] + 1 + self._financeColumnNameList.index(columnName)
            return None
        else:
            return self._columnName2Index[columnName]


    def calcResult(self, result, item, visitPersonList={}, eventPersonList={}, keyPOList=[]):
        for columnName, value in item.items():
            if columnName not in u'visitCount' and columnName not in u'eventCount':
                result[columnName] += value
        for keyPO in keyPOList:
            result['visitCount'] += visitPersonList.get(keyPO, 0)
            result['eventCount'] += eventPersonList.get(keyPO, 0)

