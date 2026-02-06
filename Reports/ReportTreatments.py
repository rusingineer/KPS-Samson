# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2021 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import QDate, pyqtSignature

from library.Utils      import forceInt, forceRef, forceString, agreeNumberAndWord
from Orgs.Utils         import getOrgStructureFullName
from Reports.Report     import CReport
from Reports.ReportBase import CReportBase, createTable
from Timeline.Schedule  import CSchedule
from Events.Utils       import getWorkEventTypeFilter

from Reports.SelectPersonListDialog   import CPersonListDialog
from Events.EventTypeListEditorDialog import CEventTypeListEditorDialog, formatEventTypeIdList
from Reports.SpecialityListDialog     import CSpecialityListDialog, formatSpecialityIdList

from Reports.Ui_ReportTreatmentsSetup import Ui_ReportTreatmentsSetupDialog


def selectVisitsData(params):
    begDate          = params.get('begDate', None)
    endDate          = params.get('endDate', None)
    purposeId        = params.get('purposeId', None)
    eventTypeId      = params.get('eventTypeId', None)
    eventTypeList    = params.get('eventTypeList', [])
    medicalAidTypeId = params.get('medicalAidTypeId', None)
    orgStructureId   = params.get('orgStructureId', None)
    personIdList     = params.get('personIdList', None)
    specialityList   = params.get('specialityList', None)
    ageFrom          = params.get('ageFrom', 0)
    ageTo            = params.get('ageTo', 150)

    db = QtGui.qApp.db

    tableEventType    = db.table('EventType')
    tableEvent        = db.table('Event')
    tableClient       = db.table('Client')
    tableVisit        = db.table('Visit')
    tableScene        = db.table('rbScene')
    tableOrgStructure = db.table('OrgStructure')
    tablePerson       = db.table('vrbPersonWithSpeciality')

    queryTable = tableEvent
    queryTable = queryTable.leftJoin(tableVisit, tableVisit['event_id'].eq(tableEvent['id']))
    queryTable = queryTable.leftJoin(tableClient, tableClient['id'].eq(tableEvent['client_id']))
    queryTable = queryTable.leftJoin(tableScene, tableScene['id'].eq(tableVisit['scene_id']))
    queryTable = queryTable.leftJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
    queryTable = queryTable.leftJoin(tablePerson, tablePerson['id'].eq(tableVisit['person_id']))
    queryTable = queryTable.leftJoin(tableOrgStructure, tableOrgStructure['id'].eq(tablePerson['orgStructure_id']))

    cond = [ tableEvent['deleted'].eq(0),
             tableEventType['deleted'].eq(0),
             tableClient['deleted'].eq(0),
             tableVisit['deleted'].eq(0),
             tableOrgStructure['deleted'].eq(0),
             tableEvent['setDate'].lt(tableVisit['date'].addDays(1))
            ]

    if begDate:
        cond.append(tableEvent['execDate'].ge(begDate))
    if endDate:
        cond.append(tableEvent['execDate'].lt(endDate).addDays(1))
    if purposeId:
        cond.append(tableEventType['purpose_id'].eq(purposeId))
    if eventTypeId:
        cond.append(tableEventType['id'].eq(eventTypeId))
    elif eventTypeList:
        cond.append(tableEvent['eventType_id'].inlist(eventTypeList))
    if medicalAidTypeId:
        cond.append(tableEventType['medicalAidType_id'].eq(medicalAidTypeId))
    if ageFrom <= ageTo:
        cond.append('Event.setDate >= ADDDATE(Client.birthDate, INTERVAL %d YEAR)'%ageFrom)
        cond.append('Event.setDate < SUBDATE(ADDDATE(Client.birthDate, INTERVAL %d YEAR),1)'%(ageTo+1))
    if orgStructureId:
        orgStructureIdList = db.getDescendants('OrgStructure', 'parent_id', orgStructureId)
        cond.append(tableOrgStructure['id'].inlist(orgStructureIdList))
    if personIdList:
        cond.append(tablePerson['id'].inlist(personIdList))
    if specialityList:
        cond.append(tablePerson['speciality_id'].inlist(specialityList))

    fields = [tablePerson['code'].alias('personCode'),
              tablePerson['name'].alias('personName'),
              tablePerson['id'].alias('personId'),
              tableEvent['client_id'].alias('clientId'),
              tableEvent['id'].alias('eventId'),
              tableOrgStructure['id'].alias('orgStructureId'),
              tableScene['code'].alias('sceneCode')
              ]

    stmt = db.selectStmt(queryTable, fields, cond)
    return db.query(stmt)


def selectActionsData(params):
    begDate          = params.get('begDate', None)
    endDate          = params.get('endDate', None)
    purposeId        = params.get('purposeId', None)
    eventTypeId      = params.get('eventTypeId', None)
    eventTypeList    = params.get('eventTypeList', [])
    medicalAidTypeId = params.get('medicalAidTypeId', None)
    orgStructureId   = params.get('orgStructureId', None)
    personIdList     = params.get('personIdList', None)
    specialityList   = params.get('specialityList', None)
    ageFrom          = params.get('ageFrom', 0)
    ageTo            = params.get('ageTo', 150)

    db = QtGui.qApp.db

    tableEventType    = db.table('EventType')
    tableEvent        = db.table('Event')
    tableClient       = db.table('Client')
    tableActionType   = db.table('ActionType')
    tableAction       = db.table('Action')
    tableOrgStructure = db.table('OrgStructure')
    tablePerson       = db.table('vrbPersonWithSpeciality')

    queryTable = tableEvent
    queryTable = queryTable.leftJoin(tableAction, tableAction['event_id'].eq(tableEvent['id']))
    queryTable = queryTable.leftJoin(tableClient, tableClient['id'].eq(tableEvent['client_id']))
    queryTable = queryTable.leftJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
    queryTable = queryTable.leftJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
    queryTable = queryTable.leftJoin(tablePerson, tablePerson['id'].eq(tableAction['person_id']))
    queryTable = queryTable.leftJoin(tableOrgStructure, tableOrgStructure['id'].eq(tablePerson['orgStructure_id']))

    cond = [ tableEvent['deleted'].eq(0),
             tableEventType['deleted'].eq(0),
             tableClient['deleted'].eq(0),
             tableAction['deleted'].eq(0),
             tableActionType['deleted'].eq(0),
             tableOrgStructure['deleted'].eq(0)
           ]

    if begDate:
        cond.append(tableEvent['execDate'].ge(begDate))
    if endDate:
        cond.append(tableEvent['execDate'].lt(endDate.addDays(1)))
    if purposeId:
        cond.append(tableEventType['purpose_id'].eq(purposeId))
    if eventTypeId:
        cond.append(tableEventType['id'].eq(eventTypeId))
    elif eventTypeList:
        cond.append(tableEvent['eventType_id'].inlist(eventTypeList))
    if medicalAidTypeId:
        cond.append(tableEventType['medicalAidType_id'].eq(medicalAidTypeId))
    if ageFrom <= ageTo:
        cond.append('Event.setDate >= ADDDATE(Client.birthDate, INTERVAL %d YEAR)'%ageFrom)
        cond.append('Event.setDate < SUBDATE(ADDDATE(Client.birthDate, INTERVAL %d YEAR),1)'%(ageTo+1))
    if orgStructureId:
        orgStructureIdList = db.getDescendants('OrgStructure', 'parent_id', orgStructureId)
        cond.append(tableOrgStructure['id'].inlist(orgStructureIdList))
    if personIdList:
        cond.append(tablePerson['id'].inlist(personIdList))
    if specialityList:
        cond.append(tablePerson['speciality_id'].inlist(specialityList))

    fields = [tablePerson['code'].alias('personCode'),
              tablePerson['name'].alias('personName'),
              tablePerson['id'].alias('personId'),
              tableEvent['client_id'].alias('clientId'),
              tableEvent['id'].alias('eventId'),
              tableOrgStructure['id'].alias('orgStructureId'),
              tableActionType['class'].alias('actionClass')
              ]

    stmt = db.selectStmt(queryTable, fields, cond)
    return db.query(stmt)


class CReportTreatments(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Обращения по врачам')
        self._mapOrgStructureToInfo = {}
        self._mapPersonPlan = {}
        self._mapFullOrgStructureNameToId = {}
        self.resetHelpers()


    def resetHelpers(self):
        self._mapOrgStructureToInfo.clear()
        self._mapPersonPlan.clear()
        self._mapFullOrgStructureNameToId.clear()


    def getSetupDialog(self, parent):
        result = CReportTreatmentsSetup(parent)
        result.setTitle(self.title())
        return result


    def getDescription(self, params):
        begDate            = params.get('begDate', None)
        endDate            = params.get('endDate', None)
        financeText        = params.get('financeText', '')
        financeId          = params.get('financeId', None)
        purposeText        = params.get('purposeText', '')
        purposeId          = params.get('purposeId', None)
        eventTypeText      = params.get('eventTypeText', '')
        eventTypeId        = params.get('eventTypeId', None)
        medicalAidTypeText = params.get('medicalAidTypeText', '')
        medicalAidTypeId   = params.get('medicalAidTypeId', None)
        orgStructureText   = params.get('orgStructureText', '')
        orgStructureId     = params.get('orgStructureId', None)
        tariffingText      = params.get('tariffingText', '')
        ageFrom            = params.get('ageFrom', None)
        ageTo              = params.get('ageTo', None)

        rows = []
        if begDate:
            rows.append(u'Начальная дата периода: %s'%forceString(begDate))
        if endDate:
            rows.append(u'Конечная дата периода: %s'%forceString(endDate))
        if financeId:
            rows.append(u'Тип финансирования: %s' % financeText)
        if purposeId:
            rows.append(u'Назначение: %s' % purposeText)
        if eventTypeId:
            rows.append(u'Тип события: %s' % eventTypeText)
        else:
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
        if medicalAidTypeId:
            rows.append(u'Тип медицинской помощи: %s' % medicalAidTypeText)
        if orgStructureId:
            rows.append(u'Подразделение: %s' % orgStructureText)
        personList = params.get('personIdList', None)
        if personList:
            db = QtGui.qApp.db
            table = db.table('vrbPersonWithSpecialityAndOrgStr')
            records = db.getRecordList(table, [table['name']], [table['id'].inlist(personList)])
            nameList = []
            for record in records:
                nameList.append(forceString(record.value('name')))
            rows.append(u'Врач:  %s'%(u'; '.join(name for name in nameList if name)))
        else:
            rows.append(u'Врач:  не задано')
        if tariffingText:
            rows.append(u'Тарификация: %s' % tariffingText)
        if ageFrom is not None and ageTo is not None and ageFrom <= ageTo:
            rows.append(u'Возраст: c %d по %d %s' % (ageFrom, ageTo, agreeNumberAndWord(ageTo, (u'год', u'года', u'лет'))))
        return rows


    def build(self, params):
        visitsQuery = selectVisitsData(params)
        actionsQuery = selectActionsData(params)
        self.structInfo(visitsQuery, actionsQuery, params)

        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()

        tableColumns = [
                        ('2%', [u'№', u''], CReportBase.AlignRight),
                        ('5%', [u'Код врача', u''], CReportBase.AlignLeft),
                        ('15%',[u'ФИО врача', u''], CReportBase.AlignLeft),
                        ('6%', [u'Кол-во пациентов', u''], CReportBase.AlignLeft),
                        ('6%', [u'Кол-во обращений', u''], CReportBase.AlignLeft),
                        ('6%', [u'Визиты', u'План приема'], CReportBase.AlignLeft),
                        ('6%', [u'', u'План вызовы'], CReportBase.AlignLeft),
                        ('6%', [u'', u'Прием'], CReportBase.AlignLeft),
                        ('6%', [u'', u'Вызовы'], CReportBase.AlignLeft),
                        ('6%', [u'Услуги', u'Статус'], CReportBase.AlignLeft),
                        ('6%', [u'', u'Диагностика'], CReportBase.AlignLeft),
                        ('6%', [u'', u'Лечение'], CReportBase.AlignLeft),
                        ('6%', [u'', u'Прочие'], CReportBase.AlignLeft)
                       ]

        table = createTable(cursor, tableColumns)

        table.mergeCells(0, 0, 2, 1)
        table.mergeCells(0, 1, 2, 1)
        table.mergeCells(0, 2, 2, 1)
        table.mergeCells(0, 3, 2, 1)
        table.mergeCells(0, 4, 2, 1)

        table.mergeCells(0, 5, 1, 4)
        table.mergeCells(0, 9, 1, 4)

        boldChars = QtGui.QTextCharFormat()
        boldChars.setFontWeight(QtGui.QFont.Bold)

        keysList = self._mapFullOrgStructureNameToId.keys()
        keysList.sort()
        numShift = 0
        result = [0]*10
        resClientIdList = []
        resEventIdList  = []
        for key in keysList:
            orgClientIdList = []
            orgEventIdList  = []
            orgStructureResult = [0]*10
            personInfoDict = self._mapOrgStructureToInfo[self._mapFullOrgStructureNameToId[key]]
            i = table.addRow()
            table.setText(i, 1, key, charFormat=boldChars)
            table.mergeCells(i, 0, 1, 13)
            numShift += 1
            for personId, personInfoList in personInfoDict.items():
                i = table.addRow()
                table.setText(i, 0, i-numShift-1)
                personInfoHelper = personInfoList[-1]
                for idx, value in enumerate(personInfoList[:-1]):
                    if idx > 3:
                        orgStructureResult[idx-2] += value
                    table.setText(i, idx+1, value)
                orgClientIdList.extend(personInfoHelper['clientIdList'])
                orgEventIdList.extend(personInfoHelper['eventIdList'])
            for idx, value in enumerate(orgStructureResult):
                result[idx] += value
            orgStructureResult[0] = len(orgClientIdList)
            orgStructureResult[1] = len(orgEventIdList)
            self.printResult(table, orgStructureResult, boldChars)
            numShift += 1
            resClientIdList.extend(orgClientIdList)
            resEventIdList.extend(orgEventIdList)
        result[0] = len(resClientIdList)
        result[1] = len(resEventIdList)
        self.printResult(table, result, boldChars, name=u'Всего')
        return doc


    def printResult(self, table, result, boldChars, name=u'Итого'):
        i = table.addRow()
        table.setText(i, 0, name, charFormat=boldChars)
        for idx, value in enumerate(result):
            table.setText(i, 3+idx, value, charFormat=boldChars)
        table.mergeCells(i, 0, 1, 3)


    def structInfo(self, visitsQuery, actionsQuery, params):
        self.resetHelpers()

        self.structVisitsInfo(visitsQuery, params)
        self.structActionsInfo(actionsQuery)


    def structVisitsInfo(self, query, params):
        begDate = params.get('begDate', None)
        endDate = params.get('endDate', None)
        AMB_SCENE_CODE_LIST  = ['1']
        HOME_SCENE_CODE_LIST = ['2', '3']
        while query.next():
            record = query.record()

            orgStructureId = forceRef(record.value('orgStructureId'))
            personCode     = forceString(record.value('personCode'))
            personName     = forceString(record.value('personName'))
            clientId       = forceRef(record.value('clientId'))
            personId       = forceRef(record.value('personId'))
            eventId        = forceRef(record.value('eventId'))
            sceneCode      = forceString(record.value('sceneCode'))

            if not (sceneCode in AMB_SCENE_CODE_LIST or sceneCode in HOME_SCENE_CODE_LIST):
                continue

            if orgStructureId not in self._mapFullOrgStructureNameToId.values():
                if orgStructureId:
                    orgStructureFullName = getOrgStructureFullName(orgStructureId)
                else:
                    orgStructureFullName = u' Не определено'
                self._mapFullOrgStructureNameToId[orgStructureFullName] = orgStructureId

            personInfoDict = self._mapOrgStructureToInfo.setdefault(orgStructureId, {})
            personInfoList = personInfoDict.get(personId, None)
            if personInfoList is None:
                personInfoHelper = {'clientIdList':[], 'eventIdList':[]}
                personInfoList = [personCode, personName] + [0]*10 + [personInfoHelper]
                personInfoList[4] = self._getPersonPlan(personId, CSchedule.atAmbulance, begDate, endDate)
                personInfoList[5] = self._getPersonPlan(personId, CSchedule.atHome, begDate, endDate)
                personInfoDict[personId] = personInfoList

            personInfoHelper = personInfoList[-1]
            if clientId not in personInfoHelper['clientIdList']:
                personInfoList[2] += 1
                personInfoHelper['clientIdList'].append(clientId)
            if eventId not in personInfoHelper['eventIdList']:
                personInfoList[3] += 1
                personInfoHelper['eventIdList'].append(eventId)
            if sceneCode in AMB_SCENE_CODE_LIST:
                personInfoList[6] += 1
            elif sceneCode in HOME_SCENE_CODE_LIST:
                personInfoList[7] += 1


    def structActionsInfo(self, query):
        while query.next():
            record = query.record()

            orgStructureId = forceRef(record.value('orgStructureId'))
            personCode     = forceString(record.value('personCode'))
            personName     = forceString(record.value('personName'))
            clientId       = forceRef(record.value('clientId'))
            personId       = forceRef(record.value('personId'))
            eventId        = forceRef(record.value('eventId'))
            actionClass    = forceInt(record.value('actionClass'))

            if orgStructureId not in self._mapFullOrgStructureNameToId.values():
                orgStructureFullName = getOrgStructureFullName(orgStructureId)
                self._mapFullOrgStructureNameToId[orgStructureFullName] = orgStructureId

            personInfoDict = self._mapOrgStructureToInfo.setdefault(orgStructureId, {})
            personInfoList = personInfoDict.get(personId, None)
            if personInfoList is None:
                personInfoHelper = {'clientIdList':[], 'eventIdList':[]}
                personInfoList = [personCode, personName] + [0]*10 + [personInfoHelper]
                personInfoDict[personId] = personInfoList

            personInfoHelper = personInfoList[-1]
            personInfoList[8+actionClass] += 1
            if clientId not in personInfoHelper['clientIdList']:
                personInfoList[2] += 1
                personInfoHelper['clientIdList'].append(clientId)
            if eventId not in personInfoHelper['eventIdList']:
                personInfoList[3] += 1
                personInfoHelper['eventIdList'].append(eventId)


    def _getPersonPlan(self, personId, appointmentType, begDate, endDate):
        key = (personId, appointmentType)
        result = self._mapPersonPlan.get(key, None)
        if result is None:
            db = QtGui.qApp.db
            tableSchedule = db.table('Schedule')
            cond = [tableSchedule['deleted'].eq(0),
                    tableSchedule['appointmentType'].eq(appointmentType),
                    tableSchedule['date'].ge(begDate),
                    tableSchedule['date'].le(endDate),
                    tableSchedule['person_id'].eq(personId),
                   ]
            result = forceInt(db.getSum(tableSchedule, 'capacity', cond))
            self._mapPersonPlan[key] = result
        return result


class CReportTreatmentsSetup(QtGui.QDialog, Ui_ReportTreatmentsSetupDialog):
    def __init__(self, parent):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.cmbEventType.setTable('EventType', addNone=True)
        self.cmbPurpose.setTable('rbEventTypePurpose', addNone=True)
        self.cmbMedicalAidType.setTable('rbMedicalAidType', addNone=True)
        self.cmbFinance.setTable('rbFinance', addNone=True)
        self.personIdList = []
        self.eventTypeList = []
        self.specialityList = []
        self.setEventTypeIdVisible(False)


    def setEventTypeIdVisible(self, value):
        self.isEventTypeIdVisible = value
        self.cmbEventType.setVisible(value)
        self.lblEventType.setVisible(value)


    def setTitle(self, title):
        self.setWindowTitle(title)


    def setParams(self, params):
        self.edtBegDate.setDate(params.get('begDate', QDate.currentDate()))
        self.edtEndDate.setDate(params.get('endDate', QDate.currentDate()))
        self.cmbFinance.setValue(params.get('financeId', None))
        self.cmbPurpose.setValue(params.get('purposeId', None))
        if self.isEventTypeIdVisible:
            self.cmbEventType.setValue(params.get('eventTypeId', None))
        else:
            self.eventTypeList =  params.get('eventTypeList', [])
            if self.eventTypeList:
                self.lblEventTypeList.setText(formatEventTypeIdList(self.eventTypeList))
            else:
                self.lblEventTypeList.setText(u'не задано')
        self.cmbMedicalAidType.setValue(params.get('medicalAidTypeId', None))
        self.cmbOrgStructure.setValue(params.get('orgStructureId', None))
        self.cmbTariffing.setCurrentIndex(params.get('tariffing', 0))
        self.edtAgeFrom.setValue(params.get('ageFrom', 0))
        self.edtAgeTo.setValue(params.get('ageTo', 150))
        self.personIdList = params.get('personIdList', [])
        self.specialityList = params.get('specialityList', [])

        if self.personIdList:
            db = QtGui.qApp.db
            table = db.table('vrbPersonWithSpecialityAndOrgStr')
            records = db.getRecordList(table, [table['name']], [table['id'].inlist(self.personIdList)])
            self.lblPersonList.setText(u'; '.join(forceString(record.value('name')) for record in records if forceString(record.value('name'))))
        else:
            self.lblPersonList.setText(u'не задано')

        if self.specialityList:
            self.lblSpecialityList.setText(formatSpecialityIdList(self.specialityList))
        else:
            self.lblSpecialityList.setText(u'не задано')


    def params(self):
        return dict(
                    begDate = self.edtBegDate.date(),
                    endDate = self.edtEndDate.date(),
                    financeId   = self.cmbFinance.value(),
                    financeText = self.cmbFinance.currentText(),
                    purposeId   = self.cmbPurpose.value(),
                    purposeText = self.cmbPurpose.currentText(),
                    medicalAidTypeId = self.cmbMedicalAidType.value(),
                    medicalAidTypeText = self.cmbMedicalAidType.currentText(),
                    eventTypeList   = self.eventTypeList if not self.isEventTypeIdVisible else [],
                    eventTypeId = self.cmbEventType.value() if self.isEventTypeIdVisible else None,
                    eventTypeText = self.cmbEventType.currentText(),
                    orgStructureId = self.cmbOrgStructure.value(),
                    orgStructureText = self.cmbOrgStructure.currentText(),
                    personIdList = self.personIdList,
                    specialityList = self.specialityList,
                    tariffing = self.cmbTariffing.currentIndex(),
                    tariffingText = self.cmbTariffing.currentText(),
                    ageFrom = self.edtAgeFrom.value(),
                    ageTo = self.edtAgeTo.value()
                   )


    @pyqtSignature('')
    def on_btnPersonList_clicked(self):
        self.personIdList = []
        orgStructureId = self.cmbOrgStructure.value()
        self.lblPersonList.setText(u'не задано')
        dialog = CPersonListDialog(self, orgStructureId = orgStructureId if orgStructureId else None)
        if dialog.exec_():
            self.personIdList = dialog.values()
            if self.personIdList:
                db = QtGui.qApp.db
                table = db.table('vrbPersonWithSpecialityAndOrgStr')
                records = db.getRecordList(table, [table['name']], [table['id'].inlist(self.personIdList)])
                nameList = []
                for record in records:
                    nameList.append(forceString(record.value('name')))
                self.lblPersonList.setText(u', '.join(name for name in nameList if name))


    @pyqtSignature('')
    def on_btnEventTypeList_clicked(self):
        self.eventTypeList = []
        self.lblEventTypeList.setText(u'не задано')
        eventPurposeId = self.cmbPurpose.value()
        if eventPurposeId:
            filter = u'EventType.purpose_id =%d' % eventPurposeId
        else:
            filter = getWorkEventTypeFilter(isApplyActive=True)
        dialog = CEventTypeListEditorDialog(self, filter)
        if dialog.exec_():
            self.eventTypeList = dialog.values()
            if self.eventTypeList:
                self.lblEventTypeList.setText(formatEventTypeIdList(self.eventTypeList))


    @pyqtSignature('int')
    def on_cmbPurpose_currentIndexChanged(self, index):
        if self.isEventTypeIdVisible:
            eventPurposeId = self.cmbPurpose.value()
            if eventPurposeId:
                filter = 'EventType.purpose_id=%d' % eventPurposeId
            else:
                filter = getWorkEventTypeFilter(isApplyActive=True)
            self.cmbEventType.setFilter(filter)


    @pyqtSignature('')
    def on_btnSpecialityList_clicked(self):
        db = QtGui.qApp.db
        self.specialityList = []
        self.lblSpecialityList.setText(u'не задано')
        cond = None
        if self.personIdList:
            tablePerson = db.table('Person')
            stmt = tablePerson['id'].inlist(self.personIdList)
            cond = 'id IN (SELECT Person.speciality_id FROM Person WHERE %s)' % stmt
        dialog = CSpecialityListDialog(self, filter=cond)
        if dialog.exec_():
            self.specialityList = dialog.values()
            if self.specialityList:
                self.lblSpecialityList.setText(formatSpecialityIdList(self.specialityList))

