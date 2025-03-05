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
from PyQt4.QtCore import QDate, QTime, QDateTime

from library.Utils      import calcAge, forceDate, forceInt, forceString

from Events.Utils       import getActionTypeIdListByFlatCode
from Orgs.Utils         import getOrgStructureDescendants, getOrgStructureFullName
from Reports.ReportBase import CReportBase, createTable
from Reports.Report     import CReport
from Reports.Utils      import dateRangeAsStr, getDataOrgStructure, updateLIKE


from Ui_ReportPersonSickListStationary import Ui_ReportPersonSickListStationary


def selectData(begDateTime, endDateTime, orgStructureId, MKBFrom, MKBTo, typeHospytal):
    stmt="""
SELECT Action.begDate, Action.id,
Event.id AS eventId, Event.externalId, Event.client_id, Event.setDate, Event.execDate,
Client.lastName, Client.firstName, Client.patrName, Client.birthDate, Diagnosis.MKB,
getClientRegAddress(Client.id) as regAddress, getClientLocAddress(Client.id) as locAddress ,
concat_ws(' ',dt.name, cd.serial, cd.number, date_format(cd.date, '%%d.%%m.%%Y'), cd.origin) as document
FROM Action
INNER JOIN ActionType ON ActionType.id=Action.actionType_id
INNER JOIN Event ON Action.event_id=Event.id
INNER JOIN Client ON Event.client_id=Client.id
INNER JOIN EventType ON Event.eventType_id=EventType.id
INNER JOIN Person ON Event.execPerson_id = Person.id
INNER JOIN Diagnostic ON Diagnostic.event_id=Event.id
INNER JOIN Diagnosis ON Diagnostic.diagnosis_id=Diagnosis.id
INNER JOIN rbDiagnosisType ON Diagnostic.diagnosisType_id=rbDiagnosisType.id
LEFT join ClientDocument cd on cd.client_id = Client.id and cd.id = getClientDocumentId(Client.id)
left join rbDocumentType dt on dt.id = cd.documentType_id
LEFT JOIN ClientPolicy cp on cp.id = getClientPolicyIdForDate(Client.id, 1, Event.execDate, Event.id)
WHERE Action.deleted=0 AND Event.deleted=0 AND Client.deleted=0 AND Person.deleted = 0 AND Event.execDate IS NOT NULL

AND ((EventType.medicalAidType_id IN (SELECT rbMedicalAidType.id from rbMedicalAidType where rbMedicalAidType.code
IN ('1', '2', '3', '7'))))
AND %s
AND (Diagnosis.deleted = 0 AND Diagnostic.deleted = 0
AND (rbDiagnosisType.code = '1'
OR (rbDiagnosisType.code = '2' AND Diagnostic.person_id = Event.execPerson_id
AND (NOT EXISTS (SELECT DC.id FROM Diagnostic AS DC
INNER JOIN rbDiagnosisType AS DT ON DT.id = DC.diagnosisType_id WHERE DT.code = '1'
AND DC.event_id = Event.id)))))

ORDER BY Client.lastName ASC
"""
    db = QtGui.qApp.db
    tableDiagnosis = db.table('Diagnosis')
    tableEvent  = db.table('Event')
    tableAction = db.table('Action')
    #tablePerson = db.table('Person')
    leavedActionTypeIdList = getActionTypeIdListByFlatCode(u'leaved')
    receivedActionTypeIdList = getActionTypeIdListByFlatCode(u'received')
    cond = [tableAction['actionType_id'].inlist(leavedActionTypeIdList),
            tableEvent['execDate'].isNotNull(),
            tableAction['endDate'].isNotNull()]
    if begDateTime:
        cond.append(tableEvent['execDate'].isNotNull())
        cond.append(tableEvent['execDate'].ge(begDateTime))
    if endDateTime:
        cond.append(tableEvent['execDate'].isNotNull())
        cond.append(tableEvent['execDate'].le(endDateTime))
    cond.append(tableDiagnosis['MKB'].ge(MKBFrom))
    cond.append(tableDiagnosis['MKB'].le(MKBTo))
    if orgStructureId:
        #cond.append(tablePerson['orgStructure_id'].inlist(getOrgStructureDescendants(orgStructureId)))
        cond.append(getDataOrgStructure(u'Отделение', getOrgStructureDescendants(orgStructureId)))
    cond.append(getPropertyAPOS(typeHospytal, u'Направлен в отделение', receivedActionTypeIdList))
    return db.query(stmt%(db.joinAnd(cond)))


def getPropertyAPOS(typeHospytal, nameProperty, actionTypeIdList):
    return u'''(%sEXISTS(SELECT APOS.value
    FROM Event AS E
    INNER JOIN Action AS A ON A.event_id = E.id
    INNER JOIN ActionType AS AT ON AT.id=A.actionType_id
    INNER JOIN ActionPropertyType AS APT ON AT.id = APT.actionType_id
    INNER JOIN ActionProperty AS AP ON AP.type_id=APT.id AND AP.action_id = A.id
    INNER JOIN ActionProperty_OrgStructure AS APOS ON APOS.id=AP.id
    WHERE E.client_id = Event.client_id AND E.deleted = 0 AND A.deleted = 0 AND AT.deleted = 0
    AND AP.deleted = 0 AND A.endDate IS NOT NULL AND (Action.plannedEndDate IS NULL
    OR (DATE(A.begDate) <= DATE(Action.plannedEndDate) AND DATE(Action.plannedEndDate) <= DATE(A.endDate)))
    AND APT.deleted=0 AND APT.name %s
    AND A.actionType_id IN (%s)))'''%(u'NOT ' if typeHospytal else u'', updateLIKE(nameProperty), ','.join(str(actionTypeId) for actionTypeId in actionTypeIdList if actionTypeId))


class CReportPersonSickListStationary(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setPayPeriodVisible(False)
        self.setTitle(u'Список пациентов по нозологиям')
        self.setOrientation(QtGui.QPrinter.Landscape)

    def getSetupDialog(self, parent):
        result = CReportPersonSickListSetupDialog(parent)
        result.setTitle(self.title())
        return result


    def dumpParams(self, cursor, params):
        description = []
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        begTime = params.get('begTime', None)
        endTime = params.get('endTime', None)
        if begTime and endTime:
            begDateTime = QDateTime(begDate, begTime)
            endDateTime = QDateTime(endDate, endTime)
            description.append(dateRangeAsStr(u'за период', begDateTime, endDateTime))
        elif begDate and endDate:
            description.append(dateRangeAsStr(u'за период', begDate, endDate))
        orgStructureId = params.get('orgStructureId', None)
        if orgStructureId:
            description.append(u'подразделение: ' + getOrgStructureFullName(orgStructureId))
        else:
            description.append(u'подразделение: ЛПУ')
        MKBFrom = params.get('MKBFrom', 'A00')
        MKBTo = params.get('MKBTo', 'Z99.9')
        description.append(u'диапазон шифров МКБ: ' + MKBFrom + u' - ' + MKBTo)
        typeHospytal = params.get('typeHospytal', 0)
        description.append(u'тип помощи: ' + [u'стационарно', u'амбулаторно'][typeHospytal])
        description.append(u'отчёт составлен: '+forceString(QDateTime.currentDateTime()))
        columns = [ ('100%', [], CReportBase.AlignLeft) ]
        table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
        for i, row in enumerate(description):
            table.setText(i, 0, row)
        cursor.movePosition(QtGui.QTextCursor.End)


    def build(self, params):
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        begTime = params.get('begTime', QTime())
        endTime = params.get('endTime', QTime())
        begDateTime = QDateTime(begDate, begTime)
        endDateTime = QDateTime(endDate, endTime)
        orgStructureId = params.get('orgStructureId', None)
        MKBFrom = params.get('MKBFrom', 'A00')
        MKBTo = params.get('MKBTo', 'Z99.9')
        typeHospytal = params.get('typeHospytal', 0)

        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()

        tableColumns = [
            ('5%', [u'№'],                  CReportBase.AlignRight),
            ('12%',[u'ФИО пациента'],       CReportBase.AlignLeft),
            ('8%', [u'дата рождения'],      CReportBase.AlignLeft),
            ('8%', [u'возраст'],            CReportBase.AlignLeft),
            ('8%', [u'внешний идентификатор/ внутренний идентификатор'], CReportBase.AlignLeft),
            ('10%', [u'Адрес регистрации'], CReportBase.AlignLeft),
            ('10%', [u'Адрес проживания'], CReportBase.AlignLeft),
            ('8%', [u'код по МКБ'],         CReportBase.AlignLeft),
            ('8%', [u'поступил'],           CReportBase.AlignLeft),
            ('8%', [u'выписался'],          CReportBase.AlignLeft),
            ('8%', [u'дней (койко дней)'],    CReportBase.AlignLeft),
            ('10%', [u'Документ'], CReportBase.AlignLeft),
            ]
        table = createTable(cursor, tableColumns)

        cnt = 0
        query = selectData(begDateTime, endDateTime, orgStructureId, MKBFrom, MKBTo, typeHospytal)
        while query.next():
            record = query.record()
#            clientId = forceInt(record.value('client_id'))
            MKB = forceString(record.value('MKB'))
            setDateString = forceString(record.value('setDate'))
            execDateString = forceString(record.value('execDate'))
            setDate = forceDate(record.value('setDate'))
            execDate = forceDate(record.value('execDate'))
            externalId = forceString(record.value('externalId'))
            eventId = forceString(record.value('eventId'))
            birthDate = forceString(record.value('birthDate'))
            clientName = forceString(record.value('lastName')) + u' ' + forceString(record.value('firstName')) + u' ' + forceString(record.value('patrName'))
            clientAge = forceString(calcAge(forceDate(record.value('birthDate')), setDate))
            regAddress = forceString(record.value('regAddress'))
            locAddress = forceString(record.value('locAddress'))
            document = forceString(record.value('document'))
            if not setDate:
                setDate = QDate.currentDate()
            if not execDate:
                execDate = QDate.currentDate()
            if execDate and setDate:
                if execDate == setDate:
                    bedDay = 1
                else:
                    bedDay = setDate.daysTo(execDate)
            else:
                bedDay = 0
            row = table.addRow()
            cnt += 1
            table.setText(row, 0, cnt)
            table.setText(row, 1, clientName)
            table.setText(row, 2, birthDate)
            table.setText(row, 3, clientAge)
            table.setText(row, 4, externalId + u'/' + eventId)
            table.setText(row, 5, regAddress)
            table.setText(row, 6, locAddress)
            table.setText(row, 7, MKB)
            table.setText(row, 8, setDateString)
            table.setText(row, 9, execDateString)
            table.setText(row, 10, bedDay)
            table.setText(row, 11, document)
        return doc


class CReportPersonSickListSetupDialog(QtGui.QDialog, Ui_ReportPersonSickListStationary):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.cmbOrgStructure.setOrgId(QtGui.qApp.currentOrgId())
        self.cmbOrgStructure.setValue(QtGui.qApp.currentOrgStructureId())


    def setTitle(self, title):
        self.setWindowTitle(title)


    def setParams(self, params):
        self.edtBegDate.setDate(params.get('begDate', QDate.currentDate()))
        self.edtEndDate.setDate(params.get('endDate', QDate.currentDate()))
        self.edtBegTime.setTime(params.get('begTime', QTime(0, 0, 0)))
        self.edtEndTime.setTime(params.get('endTime', QTime(23, 59, 59)))
        self.cmbOrgStructure.setValue(params.get('orgStructureId', None))
        self.edtMKBFrom.setText(params.get('MKBFrom', 'A00'))
        self.edtMKBTo.setText(params.get('MKBTo',   'Z99.9'))
        self.cmbTypeHospytal.setCurrentIndex(params.get('typeHospytal', 0))


    def params(self):
        result = {}
        result['begDate'] = self.edtBegDate.date()
        result['endDate'] = self.edtEndDate.date()
        result['begTime'] = self.edtBegTime.time()
        result['endTime'] = self.edtEndTime.time()
        result['orgStructureId'] = self.cmbOrgStructure.value()
        result['MKBFrom']   = unicode(self.edtMKBFrom.text())
        result['MKBTo']     = unicode(self.edtMKBTo.text())
        result['typeHospytal'] = forceInt(self.cmbTypeHospytal.currentIndex())
        return result

