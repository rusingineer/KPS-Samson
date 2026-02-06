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
from PyQt4.QtCore import QDate, QTime

from library.Utils              import forceDate, forceInt, forceRef, forceString, forceTime, pyDate
from Events.Utils               import getActionTypeIdListByFlatCode
from Orgs.Utils                 import getOrgStructurePersonIdList
from Reports.ReportBase         import CReportBase
from Reports.Report             import CReport, CReportEx
from Reports.Utils              import dateRangeAsStr, getStringPropertyCurrEvent

from Reports.Ui_SetupReportStomatF39_3  import Ui_SetupReportStomatF39_3Dialog


def selectData(params):
    begDate = params.get('begDate', QDate())
    endDate = params.get('endDate', QDate())
    orgStructureId = params.get('orgStructureId', None)
    personId = params.get('personId', None)
    sex = params.get('sex', 0)
    ageFrom = params.get('ageFrom', None)
    ageTo = params.get('ageTo', None)

    db = QtGui.qApp.db
    tablePerson = db.table('Person')
    tableIdentification = db.table('rbSpeciality_Identification')
    tableRBAccountingSystem = db.table('rbAccountingSystem')
    tableEvent = db.table('Event')
    tableClient = db.table('Client')
    tableContract = db.table('Contract')
    tableRBMedicalAidType = db.table('rbMedicalAidType')
    tableEventType = db.table('EventType')
    tableRBSpeciality = db.table('rbSpeciality')

    queryTable = tableEvent.innerJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
    queryTable = queryTable.innerJoin(tablePerson, tablePerson['id'].eq(tableEvent['execPerson_id']))
    queryTable = queryTable.innerJoin(tableIdentification, tablePerson['speciality_id'].eq(tableIdentification['master_id']))
    queryTable = queryTable.innerJoin(tableRBAccountingSystem, tableIdentification['system_id'].eq(tableRBAccountingSystem['id']))
    queryTable = queryTable.innerJoin(tableRBMedicalAidType, tableRBMedicalAidType['id'].eq(tableEventType['medicalAidType_id']))
    queryTable = queryTable.innerJoin(tableClient, tableClient['id'].eq(tableEvent['client_id']))
    queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
    queryTable = queryTable.leftJoin(tableRBSpeciality, tablePerson['speciality_id'].eq(tableRBSpeciality['id']))
    cond = [tableEvent['execDate'].ge(begDate),
            tableEvent['execDate'].lt(endDate.addDays(1)),
            tableRBMedicalAidType['code'].inlist(['9','6']),
            tableRBSpeciality['federalCode'].like(u'173'),
            tableEventType['deleted'].eq(0),
            tablePerson['deleted'].eq(0),
            tableEvent['deleted'].eq(0),
            tableIdentification['deleted'].eq(0),
            tableIdentification['value'].eq(u'140101'),
            tableRBAccountingSystem['urn'].eq(u'urn:oid:039-3y'),
           ]

    cols = [tableEvent['id'].alias('eventId'),
            tableClient['id'].alias('clientId'),
            u'IF(Event.order = 1, 1, 0) AS planEvent',
            u'DATE(Event.execDate) AS eventExecDate'
           ]

    cols.append('''EXISTS(SELECT D.id
                   FROM
                   Diagnostic AS D
                   INNER JOIN rbDispanser ON rbDispanser.id = D.dispanser_id
                   WHERE D.event_id = Event.id
                     AND D.deleted = 0
                     AND rbDispanser.code IN ('2', '6')
                  ) AS isObserved''')

    cols.append('''EXISTS(SELECT D.id
                   FROM
                   Diagnostic AS D
                   INNER JOIN rbDispanser ON rbDispanser.id = D.dispanser_id
                   WHERE D.event_id = Event.id
                     AND D.deleted = 0
                     AND rbDispanser.code IN ('3', '4', '5')
                  ) AS isNotObserved''')

    cols.append('''isClientVillager(Client.id) AS isClientRural''')

    cols.append('''IF(age(Client.birthDate, DATE(Event.setDate)) <= 14, 1, 0) AS isChildren''')

    cols.append('''(SELECT COUNT(DISTINCT Visit.id)
                    FROM Visit
                    WHERE Visit.event_id = Event.id AND Visit.deleted = 0) AS visitCount''')

    cols.append('''EXISTS(SELECT DS.id
           FROM
           Diagnosis AS DS
           INNER JOIN Diagnostic AS DC ON DC.diagnosis_id = DS.id
           WHERE DC.event_id = Event.id
             AND DC.deleted = 0 AND DS.deleted = 0
             AND (DS.MKB LIKE 'K00%%' OR DS.MKB LIKE 'K07%%' OR DS.MKB LIKE 'K08%%')
          ) AS isOrtodontCure''')


    cols.append('''(SELECT TIME(SUM(Schedule.doneTime))
                    FROM Schedule
                    WHERE Schedule.person_id = Event.execPerson_id
                    AND DATE(Schedule.date) >= DATE(Event.setDate)
                    AND DATE(Schedule.date) <= DATE(Event.execDate)
                    AND Schedule.deleted = 0
                    ) AS countDoneTime''')

    actionTypeIdList = set(getActionTypeIdListByFlatCode(u'dentitionInspection')) | set(getActionTypeIdListByFlatCode(u'parodentInsp'))
    cols.append(getStringPropertyCurrEvent(actionTypeIdList, u'Аппарат') + u' AS isApparatProps')
    cols.append(getStringPropertyCurrEvent(actionTypeIdList, u'Протезы') + u' AS isProtezesProps')
    cols.append(getStringPropertyCurrEvent(actionTypeIdList, u'Ортодонтическое лечение') + u' AS isOrtodontCureProps')

    if personId:
        cond.append(tableEvent['execPerson_id'].eq(personId))
    elif orgStructureId:
        personIdList = getOrgStructurePersonIdList(orgStructureId)
        if personIdList:
            cond.append(tableEvent['execPerson_id'].inlist(personIdList))
    if sex:
        cond.append(tableClient['sex'].eq(sex))
    if ageFrom is not None:
        cond.append('age(Client.`birthDate`, Event.`setDate`) >= %d'%ageFrom)
    if ageTo is not None:
        cond.append('age(Client.`birthDate`, Event.`setDate`) <= %d'%ageTo)

    stmt = db.selectStmt(queryTable, cols, cond, u'eventExecDate')
    return db.query(stmt)


class CReportStomatF39_3(CReportEx):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Форма №39_3у ортодонтия. ДНЕВНИК УЧЕТА РАБОТЫ ВРАЧА-СТОМАТОЛОГА ОРТОДОНТА', u'Форма №39_3у ортодонтия. ДНЕВНИК УЧЕТА РАБОТЫ ВРАЧА-СТОМАТОЛОГА ОРТОДОНТА')
        self.table_columns = self.getTableColumns()
        self.setOrientation(QtGui.QPrinter.Landscape)


    def getTableColumns(self):
        return [
            ('6%',   [u'Числа месяца', u'', u'', u'', u'1'], CReportBase.AlignLeft),
            ('4.4%', [u'Фактически отработано часов по графику', u'', u'', u'', u'2'], CReportBase.AlignLeft),
            ('3.2%', [u'Число посещений', u'всего', u'', u'', u'3'], CReportBase.AlignRight),
            ('3.2%', [u'', u'в том числе', u'городских жителей', u'взрослыми и подростками', u'4'], CReportBase.AlignRight),
            ('3.2%', [u'', u'', u'', u'детьми до 14 лет включительно', u'5'], CReportBase.AlignRight),
            ('3.2%', [u'', u'', u'сельских жителей', u'взрослыми и подростками', u'6'], CReportBase.AlignRight),
            ('3.2%', [u'', u'', u'', u'детьми до 14 лет включительно', u'7'], CReportBase.AlignRight),
            ('3.2%', [u'Число лиц, осмотренных в плановом порядке', u'всего', u'', u'', u'8'], CReportBase.AlignRight),
            ('3.2%', [u'', u'в том числе', u'городских жителей', u'взрослыми и подростками', u'9'], CReportBase.AlignRight),
            ('3.2%', [u'', u'', u'', u'детьми до 14 лет включительно', u'10'], CReportBase.AlignRight),
            ('3.2%', [u'', u'', u'сельских жителей', u'взрослыми и подростками', u'11'], CReportBase.AlignRight),
            ('3.2%', [u'', u'', u'', u'детьми до 14 лет включительно', u'12'], CReportBase.AlignRight),
            ('3.2%', [u'Число лиц, взятых под диспансер. наблюдение', u'всего', u'', u'', u'13'], CReportBase.AlignRight),
            ('3.2%', [u'', u'в т.ч. детей до 14 лет включительно', u'', u'', u'14'], CReportBase.AlignRight),
            ('3.2%', [u'Число лиц, нуждавшихся в ортодонтическом лечении ', u'всего', u'', u'', u'15'], CReportBase.AlignRight),
            ('3.2%', [u'', u'в т.ч. детей до 14 лет включительно', u'', u'', u'16'], CReportBase.AlignRight),
            ('3.2%', [u'Объем выполненной работы', u'внутриротовые несъемные аппараты', u'механического действия', u'', u'17'], CReportBase.AlignRight),
            ('3.2%', [u'', u'', u'функционального действия', u'', u'18'], CReportBase.AlignRight),
            ('3.2%', [u'', u'внутриротовые съемные аппараты', u'механического действия', u'', u'19'], CReportBase.AlignRight),
            ('3.2%', [u'', u'', u'функционального действия', u'', u'20'], CReportBase.AlignRight),
            ('3.2%', [u'', u'аппараты сочетанного действия', u'', u'', u'21'], CReportBase.AlignRight),
            ('3.2%', [u'', u'протезы', u'несъемные', u'', u'22'], CReportBase.AlignRight),
            ('3.2%', [u'', u'', u'съемные', u'', u'23'], CReportBase.AlignRight),
            ('3.2%', [u'Число лиц, которым закончено ортодонтическое лечение', u'всего', u'', u'', u'24'], CReportBase.AlignRight),
            ('3.2%', [u'', u'в том числе', u'с аномалиями отдельных зубов', u'', u'25'], CReportBase.AlignRight),
            ('3.2%', [u'', u'', u'с аномалиями зубных рядов', u'', u'26'], CReportBase.AlignRight),
            ('3.2%', [u'', u'', u'с сагитальными аномалиями прикуса', u'', u'27'], CReportBase.AlignRight),
            ('3.2%', [u'', u'', u'с трансверзальными аномалиями прикуса', u'', u'28'], CReportBase.AlignRight),
            ('3.2%', [u'', u'', u'с вертикальными аномалиями прикуса', u'', u'29'], CReportBase.AlignRight),
            ('3.2%', [u'Число лиц, снятых с диспансерного учета', u'', u'', u'', u'30'], CReportBase.AlignRight)
            ]


    def getSetupDialog(self, parent):
        result = CSetupReportStomatF39_3(parent)
        result.setTitle(self.title())
        return result


    def getPeriodName(self, params):
        begDate = params.get('begDate', QDate.currentDate())
        endDate = params.get('endDate', QDate.currentDate())
        return dateRangeAsStr(u' период', begDate, endDate)


    def getBufferReportData(self, params):
        bufferReportData = {}
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        while begDate <= endDate:
            bufferReportData[pyDate(begDate)] = [QTime()]+([0]*(len(self.table_columns)-2))
            begDate = begDate.addDays(1)
        return bufferReportData


    def getReportData(self, query, params):
        monthReportData = self.getBufferReportData(params)
        clientIdList = []
        eventIdList = []
        while query.next():
            record              = query.record()
            eventId             = forceRef(record.value('eventId'))
            if eventId and eventId not in eventIdList:
                eventIdList.append(eventId)
                clientId = forceRef(record.value('clientId'))
                if clientId and clientId not in clientIdList:
                    clientIdList.append(clientId)
                    planEvent           = forceInt(record.value('planEvent'))
                    eventExecDate       = forceDate(record.value('eventExecDate'))
                    isObserved          = forceInt(record.value('isObserved'))
                    isClientRural       = forceInt(record.value('isClientRural'))
                    isChildren          = forceInt(record.value('isChildren'))
                    visitCount          = forceInt(record.value('visitCount'))
                    isOrtodontCure      = forceInt(record.value('isOrtodontCure'))
                    isApparatProps      = forceString(record.value('isApparatProps'))
                    isProtezesProps     = forceString(record.value('isProtezesProps'))
                    isOrtodontCureProps = forceString(record.value('isOrtodontCureProps'))
                    isNotObserved       = forceInt(record.value('isNotObserved'))
                    countDoneTime       = forceTime(record.value('countDoneTime'))
                    reportData = monthReportData.get(pyDate(eventExecDate), None)
                    if reportData:
                        if not countDoneTime.isNull() and countDoneTime.isValid():
                            hour = countDoneTime.hour()
                            minute = countDoneTime.minute()
                            second = countDoneTime.second()
                            secondTime = hour*60*60 + minute*60 + second
                            reportData[0] = reportData[0].addSecs(max(0, secondTime))
                        reportData[1] += visitCount
                        if isClientRural:
                            if isChildren:
                                reportData[5] += visitCount
                            else:
                                reportData[4] += visitCount
                        else:
                            if isChildren:
                                reportData[3] += visitCount
                            else:
                                reportData[2] += visitCount
                        if planEvent:
                            reportData[6] += 1
                            if isClientRural:
                                if isChildren:
                                    reportData[10] += 1
                                else:
                                    reportData[9] += 1
                            else:
                                if isChildren:
                                    reportData[8] += 1
                                else:
                                    reportData[7] += 1
                        if isObserved:
                            reportData[11] += 1
                            if isChildren:
                                reportData[12] += 1
                        inIsApparatProps = isApparatProps and u'не требуется' not in isApparatProps.lower()
                        inIsProtezesProps = isProtezesProps and u'не требуется' not in isProtezesProps.lower()
                        inIsOrtodontCureProps = isOrtodontCureProps and u'не требуется' not in isOrtodontCureProps.lower()
                        if isOrtodontCure or inIsProtezesProps or inIsApparatProps or inIsOrtodontCureProps:
                            reportData[13] += 1
                            if isChildren:
                                reportData[14] += 1
                        if u'внутриротовые несъемные аппараты механического действия' in isApparatProps.lower():
                            reportData[15] += 1
                        elif u'внутриротовые несъемные аппараты функционального действия' in isApparatProps.lower():
                            reportData[16] += 1
                        elif u'внутриротовые съемные аппараты механического действия' in isApparatProps.lower():
                            reportData[17] += 1
                        elif u'внутриротовые съемные аппараты функционального действия' in isApparatProps.lower():
                            reportData[18] += 1
                        elif u'аппараты сочетанного действия' in isApparatProps.lower():
                            reportData[19] += 1
                        if u'несъемные' in isProtezesProps.lower():
                            reportData[20] += 1
                        elif u'съемные' in isProtezesProps.lower():
                            reportData[21] += 1
                        if inIsOrtodontCureProps:
                            if u'закончено' in isOrtodontCureProps.lower():
                                reportData[22] += 1
                            if u'закончено с аномалиями отдельных зубов' in isOrtodontCureProps.lower():
                                reportData[23] += 1
                            elif u'закончено с аномалиями зубных рядов' in isOrtodontCureProps.lower():
                                reportData[24] += 1
                            elif u'закончено с сагитальными аномалиями прикуса' in isOrtodontCureProps.lower():
                                reportData[25] += 1
                            elif u'закончено с трансверзальными аномалиями прикуса' in isOrtodontCureProps.lower():
                                reportData[26] += 1
                            elif u'закончено с вертикальными аномалиями прикуса' in isOrtodontCureProps.lower():
                                reportData[27] += 1
                        if isNotObserved:
                            reportData[28] += 1
        return monthReportData


    def buildInt(self, params, cursor):
        query = selectData(params)
        monthReportData = self.getReportData(query, params)
        table = self._getPersonTable(cursor)
        dateKeys = monthReportData.keys()
        dateKeys.sort()
        i = 0
        totalList = []
        isInsert = False
        for dateKey in dateKeys:
            reportData = monthReportData.get(dateKey, None)
            if reportData:
                currentPos = 0
                i = table.addRow()
                cnt = i
                table.setText(i, 0, QDate(dateKey).toString('dd.MM.yyyy'))
                table.setText(i, 1, reportData[0].toString('hh:mm:ss') if not reportData[0].isNull() else u'-')
                for col, repData in enumerate(reportData[1:]):
                    table.setText(i, col+2, repData)
                    if isInsert == False:
                        totalList.append(repData)
                    else:
                        totalList[currentPos]=totalList[currentPos]+repData
                    currentPos=currentPos+1
            isInsert = True
        i=i+1
        i = table.addRow()
        table.setText(i, 0, u'Итого')
        pos = 2
        for totalCurrent in totalList:
            table.setText(i, pos, totalCurrent)
            pos=pos+1

    def _getPersonTable(self, cursor):
        cursor.movePosition(QtGui.QTextCursor.End)
        table = self.createTable(cursor)
        table.mergeCells(0, 0, 4, 1)
        table.mergeCells(0, 1, 4, 1)
        table.mergeCells(0, 2, 1, 5)
        table.mergeCells(1, 2, 3, 1)
        table.mergeCells(1, 3, 1, 4)
        table.mergeCells(2, 3, 1, 2)
        table.mergeCells(2, 5, 1, 2)
        table.mergeCells(0, 7, 1, 5)
        table.mergeCells(1, 7, 3, 1)
        table.mergeCells(1, 8, 1, 4)
        table.mergeCells(2, 8, 1, 2)
        table.mergeCells(2, 10, 1, 2)
        table.mergeCells(0, 12, 1, 2)
        table.mergeCells(1, 12, 3, 1)
        table.mergeCells(1, 13, 3, 1)
        table.mergeCells(0, 14, 1, 2)
        table.mergeCells(1, 14, 3, 1)
        table.mergeCells(1, 15, 3, 1)
        table.mergeCells(0, 16, 1, 7)
        table.mergeCells(1, 16, 1, 2)
        table.mergeCells(2, 16, 2, 1)
        table.mergeCells(2, 17, 2, 1)
        table.mergeCells(1, 18, 1, 2)
        table.mergeCells(2, 18, 2, 1)
        table.mergeCells(2, 19, 2, 1)
        table.mergeCells(1, 20, 3, 1)
        table.mergeCells(1, 21, 1, 2)
        table.mergeCells(2, 21, 2, 1)
        table.mergeCells(2, 22, 2, 1)
        table.mergeCells(0, 23, 1, 6)
        table.mergeCells(1, 23, 3, 1)
        table.mergeCells(1, 24, 1, 5)
        table.mergeCells(2, 24, 2, 1)
        table.mergeCells(2, 25, 2, 1)
        table.mergeCells(2, 26, 2, 1)
        table.mergeCells(2, 27, 2, 1)
        table.mergeCells(2, 28, 2, 1)
        table.mergeCells(0, 29, 4, 1)
        return table


class CSetupReportStomatF39_3(QtGui.QDialog, Ui_SetupReportStomatF39_3Dialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.patientRequired = False
        self.setupUi(self)
        self.getPeriodDates()


    def getPeriodDates(self):
        currentDate = QDate.currentDate()
        currentYear = currentDate.year()
        currentMonth = currentDate.month()
        currentDay = currentDate.day()
        self.edtBegDate.setDate(QDate(currentYear, currentMonth, 1))
        self.edtEndDate.setDate(QDate(currentYear, currentMonth, currentDay))


    def setTitle(self, title):
        self.setWindowTitle(title)


    def setParams(self, params):
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        if begDate and endDate:
            self.edtBegDate.setDate(begDate)
            self.edtEndDate.setDate(endDate)
        else:
            self.getPeriodDates()

        chkOrgStructure = params.get('chkOrgStructure', False)
        self.chkOrgStructure.setChecked(chkOrgStructure)
        self.cmbOrgStructure.setValue(params.get('orgStructureId', None))

        chkPerson = params.get('chkPerson', False)
        self.chkPerson.setChecked(chkPerson)
        self.cmbPerson.setValue(params.get('personId', None))

        chkSex = params.get('chkSex', False)
        self.chkSex.setChecked(chkSex)
        self.cmbSex.setCurrentIndex(params.get('sex', 0))

        chkAge = params.get('chkAge', False)
        self.chkAge.setChecked(chkAge)
        self.edtAgeFrom.setValue(params.get('ageFrom', 0))
        self.edtAgeTo.setValue(params.get('ageTo', 150))


    def params(self):
        params = {}
        params['begDate'] = self.edtBegDate.date()
        params['endDate'] = self.edtEndDate.date()

        params['chkOrgStructure']    = self.chkOrgStructure.isChecked()
        if params['chkOrgStructure']:
            params['orgStructureId'] = self.cmbOrgStructure.value()

        params['chkPerson']    = self.chkPerson.isChecked()
        if params['chkPerson']:
            params['personId'] = self.cmbPerson.value()

        params['chkSex']    = self.chkSex.isChecked()
        if params['chkSex']:
            params['sex'] = self.cmbSex.currentIndex()

        params['chkAge']    = self.chkAge.isChecked()
        if params['chkAge']:
            params['ageFrom'] = self.edtAgeFrom.value()
            params['ageTo'] = self.edtAgeTo.value()
        return params

