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
from PyQt4.QtCore import QDate, QDateTime

from library.Utils      import forceDate, forceInt, forceRef, forceString

from Events.Utils       import getActionTypeIdListByFlatCode
from Orgs.Utils         import getOrgStructureFullName
from Reports.Report     import CReport
from Reports.ReportBase import CReportBase, createTable
from Reports.ReportView import CPageFormat
from Reports.Utils      import dateRangeAsStr, getDataOrgStructure, getKladrClientAddressRural, getKladrClientDefaultCity, getPropertyHospitalBedProfile, getStringProperty


from Ui_AnaliticReportsChildrenLeaved import Ui_AnaliticReportsChildrenLeavedDialog

class CAnaliticReportsChildrenLeavedDialog(QtGui.QDialog, Ui_AnaliticReportsChildrenLeavedDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.cmbProfileBed.setTable('rbHospitalBedProfile', True)
        self.cmbOrgStructure.setOrgId(QtGui.qApp.currentOrgId())
        self.cmbOrgStructure.setValue(QtGui.qApp.currentOrgStructureId())


    def setTitle(self, title):
        self.setWindowTitle(title)


    def setParams(self, params):
        self.edtBegDate.setDate(params.get('begDate', QDate.currentDate()))
        self.edtEndDate.setDate(params.get('endDate', QDate.currentDate()))
        self.cmbOrgStructure.setValue(params.get('orgStructureId', None))
        self.cmbProfileBed.setValue(params.get('profileBed', None))


    def params(self):
        result = {}
        result['begDate'] = forceDate(self.edtBegDate.date())
        result['endDate'] = forceDate(self.edtEndDate.date())
        result['orgStructureId'] = forceRef(self.cmbOrgStructure.value())
        result['profileBed'] = forceRef(self.cmbProfileBed.value())
        return result


class CAnaliticReportsChildrenLeaved(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Отчет по выписанным детям')
        self.analiticReportsChildrenLeavedDialog = None
        self.orientation = CPageFormat.Landscape
        self.clientDeath = 8


    def getSetupDialog(self, parent):
        result = CAnaliticReportsChildrenLeavedDialog(parent)
        self.analiticReportsChildrenLeavedDialog = result
        return result


    def dumpParams(self, cursor, params):
        description = []
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        if begDate and endDate:
            description.append(dateRangeAsStr(u'за период', begDate, endDate))
        db = QtGui.qApp.db
        orgStructureId = params.get('orgStructureId', None)
        if orgStructureId:
            description.append(u'подразделение: ' + getOrgStructureFullName(orgStructureId))
        else:
            description.append(u'подразделение: ЛПУ')
        profileBedId = params.get('profileBed', None)
        if profileBedId:
            description.append(u'профиль %s'%(forceString(db.translate('rbHospitalBedProfile', 'id', profileBedId, 'name'))))
        description.append(u'отчёт составлен: '+forceString(QDateTime.currentDateTime()))
        columns = [ ('100%', [], CReportBase.AlignLeft) ]
        table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
        for i, row in enumerate(description):
            table.setText(i, 0, row)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()


    def getCaptionReport(self, cursor):
        cols = [('8%', [u'Месяц', u'', ], CReportBase.AlignLeft),
                ('4%', [u'Выписано', u'Всего'], CReportBase.AlignLeft),
                ('4%', [u'', u'Плановых'], CReportBase.AlignLeft),
                ('4%', [u'', u'Экстренных'], CReportBase.AlignLeft),
                ('4%', [u'', u'Переведены в др. стац.'], CReportBase.AlignLeft),
                ('4%', [u'', u'Выписаны по требованию'], CReportBase.AlignLeft),
                ('4%', [u'', u'Поступили из др. стац.'], CReportBase.AlignLeft),
                ('4%', [u'Исход', u'Выздоровление'], CReportBase.AlignLeft),
                ('4%', [u'', u'Улучшение'], CReportBase.AlignLeft),
                ('4%', [u'', u'Без перемен'], CReportBase.AlignLeft),
                ('4%', [u'Состояние при поступлении', u'Без уточнения'], CReportBase.AlignLeft),
                ('4%', [u'', u'Легкое'], CReportBase.AlignLeft),
                ('4%', [u'', u'Среднее'], CReportBase.AlignLeft),
                ('4%', [u'', u'Тяжелое'], CReportBase.AlignLeft),
                ('4%', [u'Возраст', u'До 28 дней'], CReportBase.AlignLeft),
                ('4%', [u'', u'До 1 года'], CReportBase.AlignLeft),
                ('4%', [u'', u'1-3 года'], CReportBase.AlignLeft),
                ('4%', [u'', u'4-6 лет'], CReportBase.AlignLeft),
                ('4%', [u'', u'7-14 лет'], CReportBase.AlignLeft),
                ('4%', [u'', u'15-17 лет'], CReportBase.AlignLeft),
                ('4%', [u'', u'от 18 лет'], CReportBase.AlignLeft),
                ('4%', [u'Место жительства', u'НП'], CReportBase.AlignLeft),
                ('4%', [u'', u'Село'], CReportBase.AlignLeft),
                ('4%', [u'', u'Иногородние'], CReportBase.AlignLeft)
               ]
        table = createTable(cursor, cols)
        table.mergeCells(0, 0, 2, 1)
        table.mergeCells(0, 1, 1, 6)
        table.mergeCells(0, 7, 1, 3)
        table.mergeCells(0, 10, 1, 4)
        table.mergeCells(0, 14, 1, 7)
        table.mergeCells(0, 21, 1, 3)
        return table


    def build(self, params):
        db = QtGui.qApp.db
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(u'Отчет по выписанным детям')
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertBlock()
        table = self.getCaptionReport(cursor)
        mapCodesToRowIdx, reportDataTotalAll, monthLeavedList = self.getLeavedInfoGroupingOS(params)
        orgStructureKeys = mapCodesToRowIdx.keys()
        if None in orgStructureKeys:
            setOrgStructureKeys = set(orgStructureKeys)
            setOrgStructureKeys ^= set([None])
            orgStructureKeys = list(setOrgStructureKeys)
        orgStructureKeys.sort()
        recordsOS = db.getRecordList('OrgStructure', 'id, name', '', 'name')
        orgStructureNameList = {}
        for recordOS in recordsOS:
            osId = forceRef(recordOS.value('id'))
            osName = forceString(recordOS.value('name'))
            orgStructureNameList[osId] = osName
        reportName = {1:u'январь', 2:u'февраль', 3:u'март', 'kv1':u'I квартал', 4:u'апрель', 5:u'май',  6:u'июнь',
        'kv2':u'II квартал', 7:u'июль', 8:u'август', 9:u'сентябрь', 'kv3':u'III квартал', 10:u'октябрь', 11:u'ноябрь', 12:u'декабрь', 'kv4':u'IV картал', 'year1':u'Год'}
        monthKeys = [1, 2, 3, 'kv1', 4, 5,  6, 'kv2', 7, 8, 9, 'kv3', 10, 11, 12, 'kv4', 'year1']
        for orgStructureKey in orgStructureKeys:
            reportDataMonths = mapCodesToRowIdx.get(orgStructureKey, {})
            i = table.addRow()
            table.mergeCells(i, 0, 1, 23)
            table.setText(i, 0, orgStructureNameList.get(orgStructureKey, u'не определено'))
            for monthKey in monthKeys:
                if monthKey in monthLeavedList:
                    reportLineData = reportDataMonths.get(monthKey, [0]*23)
                    i = table.addRow()
                    table.setText(i, 0, reportName.get(monthKey, u'не определено'))
                    for col, val in enumerate(reportLineData):
                        table.setText(i, col+1, val)
        i = table.addRow()
        for col, val in enumerate(reportDataTotalAll):
            table.setText(i, col, forceString(val))
        return doc


    def getLeavedInfoGroupingOS(self, params):
        db = QtGui.qApp.db
        orgStructureId = params.get('orgStructureId', None)
        orgStructureIdList = db.getDescendants('OrgStructure', 'parent_id', orgStructureId) if orgStructureId else []
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        profileBedId = params.get('profileBed', None)
        defaultKLADRCode = QtGui.qApp.defaultKLADR()

        if (not begDate) and (not endDate):
            currentDate = QDate.currentDate()
            begDate = QDate(currentDate.year(), 1, 1)
            endDate = currentDate
        elif not begDate:
            currentDate = QDate.currentDate()
            if currentDate > endDate:
                begDate = QDate(endDate.year(), 1, 1)
            else:
                begDate = currentDate
        elif not endDate:
            currentDate = QDate.currentDate()
            if currentDate > begDate:
                endDate = QDate(begDate.year(), 1, 1)
            else:
                endDate = currentDate
        self.analiticReportsChildrenLeavedDialog.edtBegDate.setDate(begDate)
        self.analiticReportsChildrenLeavedDialog.edtEndDate.setDate(endDate)
        tableEvent = db.table('Event')
        tableAction = db.table('Action')
        tableActionType = db.table('ActionType')
        tableClient = db.table('Client')
        tableDiagnosis = db.table('Diagnosis')
        tableDiagnostic = db.table('Diagnostic')
        tableDiagnosisType = db.table('rbDiagnosisType')
        tableMKB = db.table('MKB')
        table = tableEvent.innerJoin(tableAction, tableAction['event_id'].eq(tableEvent['id']))
        table = table.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
        table = table.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
        leavedIdList = getActionTypeIdListByFlatCode('leaved%')
        receivedIdList = getActionTypeIdListByFlatCode('received%')
        cols = [tableAction['event_id'],
                tableAction['person_id'],
                tableEvent['setDate'],
                tableEvent['execDate'],
                tableAction['begDate'],
                tableAction['endDate'],
                tableEvent['order'],
                tableClient['birthDate'],
                tableEvent['client_id']
                ]
        cols.append('''age(Client.birthDate, Action.endDate) AS clientAge''')
        cols.append('''EXISTS(SELECT rbDiagnosticResult.id
        FROM rbDiagnosticResult
        WHERE Diagnostic.diagnosis_id = Diagnosis.id AND  rbDiagnosticResult.id = Diagnostic.result_id
        AND (rbDiagnosticResult.name LIKE '%s')) AS recovery'''%(u'Выздоровление%'))
        cols.append('''EXISTS(SELECT rbDiagnosticResult.id
        FROM rbDiagnosticResult
        WHERE Diagnostic.diagnosis_id = Diagnosis.id AND rbDiagnosticResult.id = Diagnostic.result_id
        AND (rbDiagnosticResult.name LIKE '%s')) AS improvement'''%(u'Улучшение%'))
        cols.append('''EXISTS(SELECT rbDiagnosticResult.id
        FROM rbDiagnosticResult
        WHERE Diagnostic.diagnosis_id = Diagnosis.id AND rbDiagnosticResult.id = Diagnostic.result_id
        AND (rbDiagnosticResult.name NOT LIKE '%s'
        AND rbDiagnosticResult.name NOT LIKE '%s')) AS worsening'''%(u'Выздоровление%',u'Улучшение%'))
        cols.append(u'''(SELECT APS.value
                    FROM Action AS A
                    INNER JOIN ActionPropertyType AS APT ON APT.actionType_id=A.actionType_id
                    INNER JOIN ActionProperty AS AP ON AP.type_id=APT.id
                    INNER JOIN ActionProperty_String AS APS ON APS.id=AP.id
                    WHERE A.`event_id` = getFirstEventId(Event.id) AND A.`deleted`=0
                    AND A.actionType_id IN (%s) AND AP.deleted=0
                    AND A.begDate IS NOT NULL AND AP.action_id=A.id
                    AND APT.deleted=0 AND APT.name = '%s' AND APS.value != ''
                    LIMIT 1) AS statusReceived'''%(','.join(str(receivedId) for receivedId in receivedIdList), u'Состояние при поступлении'))
        cols.append('''(SELECT APOS2.value
                FROM Action AS A
                INNER JOIN ActionType AS AT ON A.`actionType_id`= AT.`id`
                INNER JOIN ActionProperty AS AP2 ON AP2.action_id=A.id
                INNER JOIN ActionPropertyType AS APT2 ON AP2.type_id=APT2.id
                INNER JOIN ActionProperty_OrgStructure AS APOS2 ON APOS2.id=AP2.id
                INNER JOIN OrgStructure AS OS2 ON OS2.id=APOS2.value
                WHERE A.`event_id` = Event.id AND A.id = Action.id AND A.`deleted`=0
                AND AT.`deleted`=0 AND A.begDate IS NOT NULL AND APT2.actionType_id=A.actionType_id
                AND APT2.deleted=0 AND APT2.name = '%s'
                -- AND OS2.type != 0
                AND OS2.deleted=0
                LIMIT 1) AS orgStructureId'''%(u'Отделение'))
        cols.append(u'''EXISTS(SELECT O.isHospital
                    FROM Action AS A
                    INNER JOIN Event AS EROrg ON EROrg.id=A.event_id
                    INNER JOIN Organisation AS O ON O.id=EROrg.relegateOrg_id
                    WHERE A.`event_id` = getFirstEventId(Event.id) AND A.`deleted`=0
                    AND A.actionType_id IN (%s) AND A.begDate IS NOT NULL
                    AND EROrg.relegateOrg_id IS NOT NULL
                    AND O.isHospital = 1 AND O.deleted = 0 AND EROrg.deleted = 0
                    LIMIT 1) AS transStatReceived'''%(','.join(str(receivedId) for receivedId in receivedIdList)))
        cols.append(u'%s AS resultHospitalStat'%(getStringProperty(u'Исход госпитализации', u'(APS.value LIKE \'%стационар%\' )')))
        cols.append(u'%s AS resultHospitalTreb'%(getStringProperty(u'Исход госпитализации', u'(APS.value LIKE \'%выписан по требованию%\' )')))
        cols.append('''%s AS clientRural'''%(getKladrClientAddressRural()))
        cols.append('''%s AS clientCity'''%(getKladrClientDefaultCity(defaultKLADRCode)))
        cond = [tableAction['actionType_id'].inlist(leavedIdList),
                tableEvent['deleted'].eq(0),
                tableAction['begDate'].isNotNull(),
                tableAction['deleted'].eq(0),
                tableActionType['deleted'].eq(0),
                tableClient['deleted'].eq(0)
                ]
        if orgStructureIdList:
            cond.append(getDataOrgStructure(u'Отделение', orgStructureIdList, False))
        if profileBedId:
            cond.append(getPropertyHospitalBedProfile(u'Профиль', profileBedId))
        if bool(begDate):
            cond.append(tableAction['endDate'].ge(begDate))
        if bool(endDate):
            cond.append(tableAction['endDate'].lt(endDate.addDays(1)))
        table = table.innerJoin(tableDiagnostic, tableEvent['id'].eq(tableDiagnostic['event_id']))
        table = table.innerJoin(tableDiagnosis, tableDiagnosis['id'].eq(tableDiagnostic['diagnosis_id']))
        table = table.innerJoin(tableDiagnosisType, tableDiagnosisType['id'].eq(tableDiagnostic['diagnosisType_id']))
        table = table.join(tableMKB, 'MKB.DiagID=LEFT(Diagnosis.MKB,5)')
        cond.append(tableDiagnostic['deleted'].eq(0))
        cond.append(tableDiagnosis['deleted'].eq(0))
        cond.append('''(rbDiagnosisType.code = '1'
OR (rbDiagnosisType.code = '2' AND Diagnostic.person_id = Event.execPerson_id
AND (NOT EXISTS (SELECT DC.id FROM Diagnostic AS DC
INNER JOIN rbDiagnosisType AS DT ON DT.id = DC.diagnosisType_id WHERE DT.code = '1'
AND DC.event_id = Event.id))))''')
        records = db.getRecordListGroupBy(table, cols, cond, 'Event.id')
        reportDataTotal = {}
        reportDataTotalAll = [0]*24
        reportDataTotalAll[0] = u'Итого'
        eventIdList = []
        monthLeavedList = set(['year1'])
        for record in records:
            eventId = forceRef(record.value('event_id'))
            orderEvent = forceInt(record.value('order'))
            transStatReceived = forceInt(record.value('transStatReceived'))
            nameOSId = forceRef(record.value('orgStructureId'))
            begDate = forceDate(record.value('begDate'))
            endDate = forceDate(record.value('endDate'))
            monthLeaved = endDate.month()
            recovery = forceInt(record.value('recovery'))
            improvement = forceInt(record.value('improvement'))
            worsening = forceInt(record.value('worsening'))
            statusReceived = forceString(record.value('statusReceived'))
            clientRural = forceInt(record.value('clientRural'))
            clientCity = forceInt(record.value('clientCity'))
            resultHospitalStat = forceInt(record.value('resultHospitalStat'))
            resultHospitalTreb = forceInt(record.value('resultHospitalTreb'))
            clientAge = forceInt(record.value('clientAge'))
            birthDate = forceDate(record.value('birthDate'))
            reportDataMonths = reportDataTotal.get(nameOSId, {1:[0]*23, 2:[0]*23, 3:[0]*23, 'kv1':[0]*23, 4:[0]*23, 5:[0]*23,  6:[0]*23, 'kv2':[0]*23, 7:[0]*23, 8:[0]*23, 9:[0]*23, 'kv3':[0]*23, 10:[0]*23, 11:[0]*23, 12:[0]*23, 'kv4':[0]*23, 'year1':[0]*23})
            reportDataTotalYear = reportDataMonths.get('year1', [0]*23)
            reportLineData = reportDataMonths.get(monthLeaved, [0]*23)
            KV = None
            if monthLeaved in [1, 2, 3]:
                KV = 'kv1'
            elif monthLeaved in [4, 5, 6]:
                KV = 'kv2'
            elif monthLeaved in [7, 8, 9]:
                KV = 'kv3'
            elif monthLeaved in [10, 11, 12]:
                KV = 'kv4'
            reportLineDataKV = reportDataMonths.get(KV,  [0]*23)
            monthLeavedList |= set([monthLeaved])
            monthLeavedList |= set([KV])
            if eventId and eventId not in eventIdList:
                reportLineData[0] += 1
                reportDataTotalYear[0] += 1
                reportDataTotalAll[1] += 1
                reportLineDataKV[0] += 1
                if orderEvent == 1:
                    reportLineData[1] += 1
                    reportDataTotalYear[1] += 1
                    reportDataTotalAll[2] += 1
                    reportLineDataKV[1] += 1
                elif orderEvent == 2:
                    reportLineData[2] += 1
                    reportDataTotalYear[2] += 1
                    reportDataTotalAll[3] += 1
                    reportLineDataKV[2] += 1
                reportLineData[3] += resultHospitalStat
                reportDataTotalYear[3] += resultHospitalStat
                reportDataTotalAll[4] += resultHospitalStat
                reportLineDataKV[3] += resultHospitalStat
                reportLineData[4] += resultHospitalTreb
                reportDataTotalAll[5] += resultHospitalTreb
                reportDataTotalYear[4] += resultHospitalTreb
                reportLineDataKV[4] += resultHospitalTreb
                reportLineData[5] += transStatReceived
                reportLineData[6] += recovery
                reportLineData[7] += improvement
                reportLineData[8] += worsening
                reportDataTotalYear[5] += transStatReceived
                reportDataTotalYear[6] += recovery
                reportDataTotalYear[7] += improvement
                reportDataTotalYear[8] += worsening
                reportDataTotalAll[6] += transStatReceived
                reportDataTotalAll[7] += recovery
                reportDataTotalAll[8] += improvement
                reportDataTotalAll[9] += worsening
                reportLineDataKV[5] += transStatReceived
                reportLineDataKV[6] += recovery
                reportLineDataKV[7] += improvement
                reportLineDataKV[8] += worsening
                if not statusReceived or u'Без уточнения'.lower() in statusReceived.lower() or statusReceived == u'' or statusReceived == u' ':
                    reportLineData[9] += 1
                    reportDataTotalYear[9] += 1
                    reportDataTotalAll[10] += 1
                    reportLineDataKV[9] += 1
                elif u'Лёгк'.lower() in statusReceived.lower():
                    reportLineData[10] += 1
                    reportDataTotalAll[11] += 1
                    reportDataTotalYear[10] += 1
                    reportLineDataKV[10] += 1
                elif u'Средн'.lower()  in statusReceived.lower():
                    reportLineData[11] += 1
                    reportDataTotalYear[11] += 1
                    reportDataTotalAll[12] += 1
                    reportLineDataKV[11] += 1
                elif u'Тяжел'.lower() in statusReceived.lower() or u'Тяжёл'.lower() in statusReceived.lower():
                    reportLineData[12] += 1
                    reportDataTotalYear[12] += 1
                    reportDataTotalAll[13] += 1
                    reportLineDataKV[12] += 1
                if clientAge < 1:
                    reportLineData[14] += 1
                    reportDataTotalYear[14] += 1
                    reportDataTotalAll[15] += 1
                    reportLineDataKV[14] += 1
                    if birthDate <= endDate:
                        dateAge = birthDate.daysTo(begDate)
                        if dateAge <= 28:
                            reportLineData[13] += 1
                            reportDataTotalYear[13] += 1
                            reportDataTotalAll[14] += 1
                            reportLineDataKV[13] += 1
                elif clientAge >= 1 and clientAge <= 3:
                    reportLineData[15] += 1
                    reportDataTotalYear[15] += 1
                    reportDataTotalAll[16] += 1
                    reportLineDataKV[15] += 1
                elif clientAge >= 4 and clientAge <= 6:
                    reportLineData[16] += 1
                    reportDataTotalYear[16] += 1
                    reportDataTotalAll[17] += 1
                    reportLineDataKV[16] += 1
                elif clientAge >= 7 and clientAge <= 14:
                    reportLineData[17] += 1
                    reportDataTotalYear[17] += 1
                    reportDataTotalAll[18] += 1
                    reportLineDataKV[17] += 1
                elif clientAge >= 15 and clientAge <= 17:
                    reportLineData[18] += 1
                    reportDataTotalYear[18] += 1
                    reportDataTotalAll[19] += 1
                    reportLineDataKV[18] += 1
                elif clientAge >= 18:
                    reportLineData[19] += 1
                    reportDataTotalYear[19] += 1
                    reportDataTotalAll[20] += 1
                    reportLineDataKV[19] += 1
                reportLineData[20] += clientCity
                reportDataTotalYear[20] += clientCity
                reportDataTotalAll[21] += clientCity
                reportLineDataKV[20] += clientCity
                if not clientCity and not clientRural:
                    reportLineData[22] += 1
                    reportDataTotalYear[22] += 1
                    reportDataTotalAll[23] += 1
                    reportLineDataKV[22] += 1
                reportLineData[21] += clientRural
                reportDataTotalYear[21] += clientRural
                reportDataTotalAll[22] += clientRural
                reportLineDataKV[21] += clientRural
                eventIdList.append(eventId)
            reportDataMonths[monthLeaved] = reportLineData
            reportDataMonths[KV] = reportLineDataKV
            reportDataMonths['year1'] = reportDataTotalYear
            reportDataTotal[nameOSId] = reportDataMonths
        return reportDataTotal , reportDataTotalAll , monthLeavedList

