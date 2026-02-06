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
from PyQt4.QtCore import pyqtSignature, QDate

from library.PrintInfo  import CInfoContext
from library.Utils      import firstMonthDay, forceDate, forceDouble, forceRef, forceString, lastMonthDay
from Events.ActionInfo  import CActionInfo
from Events.EventTypeListEditorDialog   import CEventTypeListEditorDialog
from Events.FinanceTypeListEditorDialog import CFinanceTypeListEditorDialog
from Events.Utils       import getActionTypeDescendants
from Reports.ReportBase import CReportBase

from Reports.ReportDoctorSummary import CReportDoctorSummary

from Reports.Ui_ReportDoctorPreCalcSetup import Ui_ReportDoctorPreCalcSetupDialog


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
    financeTypeList = params.get('financeTypeList', None)
    confirmation = params.get('confirmation', False)
    confirmationBegDate = params.get('confirmationBegDate', None)
    confirmationEndDate = params.get('confirmationEndDate', None)
    confirmationType = params.get('confirmationType', 0)
    eventTypeList = params.get('eventTypeList', None)
    chkActionTypeClass = params.get('chkActionTypeClass', False)
    actionTypeClass = params.get('actionTypeClass', None)
    actionTypeId = params.get('actionTypeId', None)

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
    if financeTypeList:
        cond.append(tableAction['finance_id'].inlist(financeTypeList))
    if eventTypeList:
        cond.append(tableEvent['eventType_id'].inlist(eventTypeList))
    if chkActionTypeClass:
        if actionTypeClass is not None:
            cond.append(tableActionType['class'].eq(actionTypeClass))
        if actionTypeId:
            cond.append(tableActionType['id'].inlist(getActionTypeDescendants(actionTypeId, actionTypeClass)))
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
#    print stmt
    return db.query(stmt)


class CReportDoctorPreCalc(CReportDoctorSummary):
    def __init__(self, parent):
        CReportDoctorSummary.__init__(self, parent)
        self._columnName2Index = {'count':1, 'jobTicketCount':-1, 'doneCount':-1}
        self.setTitle(u'Сводка на врачей с предварительным подсчетом стоимости')
        self._financeColumnNameList = []
        self._defaultValues = {'count':0, 'actionCount':0, 'amount':0.0, 'uet':0.0, 'summa':0.0}
        self.table_columns = [
                        ('%30',
                        [u'Исполнитель'], CReportBase.AlignLeft),
                        ('%10',
                        [u'Кол-во обращений'], CReportBase.AlignLeft),
                        ('%10',
                        [u'Код услуги'], CReportBase.AlignLeft),
                        ('%10',
                        [u'Название услуги'], CReportBase.AlignLeft),
                        ('%5',
                        [u'Количество мероприятий'], CReportBase.AlignLeft),
                        ('%5',
                        [u'Количество'], CReportBase.AlignLeft),
                        ('%5',
                        [u'УЕТ'], CReportBase.AlignLeft),
                        ('%10',
                        [u'Сумма'], CReportBase.AlignLeft)
                       ]


    def getSetupDialog(self, parent):
        result = CReportDoctorPreCalcSetupDialog(parent)
        result.setVisibleDoctor(True)
        result.setVisibleIdentifierType(False)
        result.setVisibleTariffing(True)
        result.chkDetailFinance.hide()
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
        confirmation = params.get('confirmation', False)
        confirmationBegDate = params.get('confirmationBegDate', None)
        confirmationEndDate = params.get('confirmationEndDate', None)
        confirmationType = params.get('confirmationType', 0)
        accountingSystemId = params.get('accountingSystemId', None)
        chkActionTypeClass = params.get('chkActionTypeClass', False)
        actionTypeClass = params.get('actionTypeClass', None)
        actionTypeId = params.get('actionTypeId', None)
        rows = [u'Дата: %s'%dateFieldName]
        if begDate:
            rows.append(u'Начальная дата периода: %s'%forceString(begDate))
        if endDate:
            rows.append(u'Конечная дата периода: %s'%forceString(endDate))
        financeTypeList = params.get('financeTypeList', None)
        if financeTypeList:
            db = QtGui.qApp.db
            tableFC = db.table('rbFinance')
            records = db.getRecordList(tableFC, [tableFC['name']], [tableFC['id'].inlist(financeTypeList)])
            nameList = []
            for record in records:
                nameList.append(forceString(record.value('name')))
            rows.append(u'Тип финансирования:  %s'%(u','.join(name for name in nameList if name)))
        else:
            rows.append(u'Тип финансирования:  не задано')
        eventTypeList = params.get('eventTypeList', None)
        if eventTypeList:
            db = QtGui.qApp.db
            tableET = db.table('EventType')
            records = db.getRecordList(tableET, [tableET['name']], [tableET['deleted'].eq(0), tableET['id'].inlist(eventTypeList)])
            nameList = []
            for record in records:
                nameList.append(forceString(record.value('name')))
            rows.append(u'Тип события:  %s'%(u','.join(name for name in nameList if name)))
        else:
            rows.append(u'Тип события:  не задано')
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


    def getTableColumnByName(self, columnName):
        return self._columnName2Index[columnName]


    def getReportData(self, query, params):
#        print "getReportData: begin: %f"%time.clock()
        self.resetHelpers()
        orgStructureId = params.get('orgStructureId', None)
        fakeEventInDay = {}
        actionTypeServiceActionIdList = []
        result = {}
        context = CInfoContext()
        while query.next():
            record = query.record()
            actionFinanceId = forceRef(record.value('actionFinanceId'))
            eventFinanceId  = forceRef(record.value('eventFinanceId'))
            actualActionFinanceId = actionFinanceId if actionFinanceId else eventFinanceId
            serviceFinanceId = forceRef(record.value('serviceFinanceId'))
            actionTypeServiceId = forceRef(record.value('actionTypeServiceId'))
            serviceId = forceRef(record.value('serviceId'))
            if actionTypeServiceId and serviceFinanceId != actualActionFinanceId:
                continue
            actionId        = forceRef(record.value('actionId'))
            eventId         = forceRef(record.value('eventId'))
            serviceCode     = forceString(record.value('serviceCode'))
            serviceName     = forceString(record.value('serviceName'))
            actionPersonId  = forceRef(record.value('actionPersonId'))
            personName      = forceString(record.value('personName'))
            personOrgStructureId = self.getActualOrgStructureId(forceRef(record.value('personOrgStructureId')),
                                                                orgStructureId)
            orgStructureName = self.getOrgStructureFullName(personOrgStructureId)
            actualDate      = forceDate(record.value('actualDate'))
            actionAmount    = forceDouble(record.value('actionAmount'))
            uetDoctor       = forceDouble(record.value('uetDoctor'))
            dateKey = unicode(actualDate.toString('yyyy-MM-dd'))
            # по дате не группируем!!!
            #dateInfoList = result.setdefault('', {})
            orgStructureInfoList = result.setdefault((personOrgStructureId, orgStructureName), {})
            personInfoList = orgStructureInfoList.setdefault((actionPersonId, personName), {})
            # может быть, нужно сделать еще один уровень иерархии: по ActionType, а потом по Service????????????????????
            actionInfo = context.getInstance(CActionInfo, actionId)
            serviceInfo = personInfoList.get((serviceId, serviceCode, serviceName), None)
            if serviceInfo is None:
                serviceInfo = {}
                self.setDefaultValues(serviceInfo)
                # может быть, нужно сделать еще один уровень иерархии: по ActionType, а потом по Service????????????????????
                #personInfoList[(actionTypeId, actionTypeCode, actionTypeName)] = actionTypeInfo
                personInfoList[(serviceId, serviceCode, serviceName)] = serviceInfo
            fakeEventList = fakeEventInDay.setdefault(dateKey, [])
            if (eventId, actionPersonId) not in fakeEventList:
                fakeEventList.append((eventId, actionPersonId))
                serviceInfo['count'] += 1
            if ((actionTypeServiceId, actionId) not in actionTypeServiceActionIdList) and serviceFinanceId:
                serviceInfo['actionCount'] += 1
                serviceInfo['amount'] += actionAmount
                serviceInfo['uet']    += uetDoctor
                #TODO: getServicePrice медленно работает, надо оптимизировать
                serviceInfo['summa']  += actionInfo.getServicePrice(serviceId)
                actionTypeServiceActionIdList.append((actionTypeServiceId, actionId))
        return result


    def buildInt(self, params, cursor):
        chkDetailActions = params.get('chkDetailActions', False)
        chkDetailOrgStructure = params.get('chkDetailOrgStructure', False)
        query = selectData(params)
        reportData = self.getReportData(query, params)
        if not chkDetailActions:
            self.removeColumn(2)
            self.removeColumn(2)
            self._columnName2Index['actionCount'] = 2
            self._columnName2Index['amount'] = 3
            self._columnName2Index['uet'] = 4
            self._columnName2Index['summa'] = 5
        else:
            self._columnName2Index['code'] = 2
            self._columnName2Index['name'] = 3
            self._columnName2Index['actionCount'] = 4
            self._columnName2Index['amount'] = 5
            self._columnName2Index['uet'] = 6
            self._columnName2Index['summa'] = 7
        self._columnName2Index['commonFinanceTypeAmount'] = self.colCount()-1
        table = self.createTable(cursor)
        # не будем отбирать по дате
        #dateKeyList = reportData.keys()
        #dateKeyList.sort()
        boldChars = QtGui.QTextCharFormat()
        boldChars.setFontWeight(QtGui.QFont.Bold)
        titleMergeLength = self.colCount()
        result = {}
        self.setDefaultValues(result)
        #for dateIdx, dateKey in enumerate(dateKeyList):
        tableRow = table.addRow()
        #    dateInfoList = reportData[dateKey]
        orgStructureKeyList = reportData.keys()
        orgStructureKeyList.sort(key=lambda item: item[1])
        lastOrgStructureIdx = len(orgStructureKeyList)-1
        for orgStructureIdx, orgStructureKey in enumerate(orgStructureKeyList):
            # tableRow = table.addRow() ???
            orgStructureId, orgStructureName = orgStructureKey
            if chkDetailOrgStructure:
                table.setText(tableRow, 0, orgStructureName, charFormat=boldChars)
                table.mergeCells(tableRow, 0, 1, titleMergeLength)
                tableRow = table.addRow()
            orgStructureInfoList = reportData[orgStructureKey] #dateInfoList[orgStructureKey]
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
                serviceKeyList = personInfoList.keys()
                serviceKeyList.sort(key=lambda item: (item[1], item[2]))
                personResult = {}
                self.setDefaultValues(personResult)
                for serviceIdx, serviceKey in enumerate(serviceKeyList):
                    serviceId, serviceCode, serviceName = serviceKey
                    serviceValues = personInfoList[serviceKey]
                    if chkDetailActions:
                        if serviceIdx:
                            tableRow = table.addRow()
                        self.printColumn('code', tableRow, table, serviceCode)
                        self.printColumn('name', tableRow, table, serviceName)
                        self.printValuesWithCalcResult(tableRow, table, serviceValues, personResult)
                    else:
                        self.calcResult(personResult, serviceValues)
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


class CReportDoctorPreCalcSetupDialog(QtGui.QDialog, Ui_ReportDoctorPreCalcSetupDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.cmbSetSpeciality.setTable('rbSpeciality', addNone=True)
        self.cmbSpeciality.setTable('rbSpeciality', addNone=True)
        self.cmbIdentifierType.setTable('rbAccountingSystem', addNone=True)
        self.eventTypeList = []
        self.financeTypeList = []
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
        self._visibleTariffing = False
        self.setVisibleTariffing(self._visibleTariffing)


    def setVisibleTariffing(self, value):
        self._visibleTariffing = value
        self.chkTariffing.setVisible(value)
        self.cmbTariffing.setVisible(value)


    def setVisibleDetailFinance(self, value):
        self._visibleDetailFinance = value
        self.chkDetailFinance.setVisible(value)


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
        self.financeTypeList =  params.get('financeTypeList', [])
        if self.financeTypeList:
            db = QtGui.qApp.db
            table = db.table('rbFinance')
            records = db.getRecordList(table, [table['name']], [table['id'].inlist(self.financeTypeList)])
            nameList = []
            for record in records:
                nameList.append(forceString(record.value('name')))
            self.lblFinanceTypeList.setText(u','.join(name for name in nameList if name))
        else:
            self.lblFinanceTypeList.setText(u'не задано')
        self.chkConfirmation.setChecked(params.get('confirmation', False))
        self.edtConfirmationBegDate.setDate(params.get('confirmationBegDate', firstMonthDay(date)))
        self.edtConfirmationEndDate.setDate(params.get('confirmationEndDate', lastMonthDay(date)))
        self.cmbConfirmationType.setCurrentIndex(params.get('confirmationType', 0))
        self.cmbIdentifierType.setValue(params.get('accountingSystemId', None))
        self.eventTypeList =  params.get('eventTypeList', [])
        if self.eventTypeList:
            db = QtGui.qApp.db
            tableET = db.table('EventType')
            records = db.getRecordList(tableET, [tableET['name']], [tableET['deleted'].eq(0), tableET['id'].inlist(self.eventTypeList)])
            nameList = []
            for record in records:
                nameList.append(forceString(record.value('name')))
            self.lblEventTypeList.setText(u','.join(name for name in nameList if name))
        else:
            self.lblEventTypeList.setText(u'не задано')
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
        self.chkDetailFinance.setChecked(params.get('chkDetailFinance', False))
        if self._visibleTariffing:
            chkTariffing = params.get('chkTariffing', False)
            self.chkTariffing.setChecked(chkTariffing)
            self.cmbTariffing.setCurrentIndex(params.get('isTariffing', 0))
            self.cmbTariffing.setEnabled(chkTariffing)


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
        result['financeTypeList'] = self.financeTypeList
        result['confirmation'] = self.chkConfirmation.isChecked()
        result['confirmationType'] = self.cmbConfirmationType.currentIndex()
        result['confirmationBegDate'] = self.edtConfirmationBegDate.date()
        result['confirmationEndDate'] = self.edtConfirmationEndDate.date()
        if self._visibleIdentifierType:
            result['accountingSystemId'] = self.cmbIdentifierType.value()
        result['eventTypeList'] = self.eventTypeList
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
        if self._visibleTariffing:
            result['chkTariffing'] = self.chkTariffing.isChecked()
            result['isTariffing'] = self.cmbTariffing.currentIndex()
        return result


    @pyqtSignature('int')
    def on_cmbActionTypeClass_currentIndexChanged(self, classCode):
        self.cmbActionType.setClassesPopup([classCode])
        self.cmbActionType.setClass(classCode)


    @pyqtSignature('')
    def on_btnEventTypeList_clicked(self):
        self.eventTypeList = []
        self.lblEventTypeList.setText(u'не задано')
        dialog = CEventTypeListEditorDialog(self)
        if dialog.exec_():
            self.eventTypeList = dialog.values()
            if self.eventTypeList:
                db = QtGui.qApp.db
                tableET = db.table('EventType')
                records = db.getRecordList(tableET, [tableET['name']], [tableET['deleted'].eq(0), tableET['id'].inlist(self.eventTypeList)])
                nameList = []
                for record in records:
                    nameList.append(forceString(record.value('name')))
                self.lblEventTypeList.setText(u','.join(name for name in nameList if name))


    @pyqtSignature('')
    def on_btnFinanceTypeList_clicked(self):
        self.financeTypeList = []
        self.lblFinanceTypeList.setText(u'не задано')
        dialog = CFinanceTypeListEditorDialog(self)
        if dialog.exec_():
            self.financeTypeList = dialog.values()
            if self.financeTypeList:
                db = QtGui.qApp.db
                table = db.table('rbFinance')
                records = db.getRecordList(table, [table['name']], [table['id'].inlist(self.financeTypeList)])
                nameList = []
                for record in records:
                    nameList.append(forceString(record.value('name')))
                self.lblFinanceTypeList.setText(u','.join(name for name in nameList if name))

