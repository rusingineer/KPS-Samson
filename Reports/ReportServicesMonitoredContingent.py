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

from library.database   import addDateInRange
from library.Utils      import agreeNumberAndWord, forceInt, forceRef, forceString, formatShortName

from Events.ActionServiceType import CActionServiceType
from Orgs.Utils         import getOrgStructureDescendants, getOrgStructureFullName, getPersonInfo
from Registry.Utils     import formatClientContingentType

from Reports.Report     import CReport
from Reports.ReportBase import CReportBase, createTable
from Reports.Utils      import dateRangeAsStr
from Reports.Utils      import appendContingentTypeCond


def selectData(params):
    stmt="""
SELECT
   event_id,
   visitId,
   person_id,
   client_id,
   consentYes,
   visitFinanceType,
   clientContingentType,
   %(groupIdDef)s,
   %(groupNameDef)s,
   Person.lastName,
   Person.firstName,
   Person.patrName,
   serviceTypeCount,
   directionsCount
   FROM (
SELECT
    Visit.person_id,
    Visit.scene_id,
    Visit.event_id,
    %(visitFinanceType)s
    Visit.id AS visitId,
   %(groupContingentType)s
    Event.client_id,
    EXISTS(SELECT ClientConsent.id FROM ClientConsent
    WHERE ClientConsent.deleted = 0 AND ClientConsent.client_id = clientCT.id
    AND ClientConsent.value = 1
    AND (ClientConsent.date <= DATE(Visit.date)
    AND (ClientConsent.endDate IS NULL OR ClientConsent.endDate >= DATE(Visit.date)))
    ORDER BY ClientConsent.date DESC LIMIT 1) AS consentYes,
   (SELECT COUNT(Action.id)
   FROM Action INNER JOIN ActionType ON ActionType.id = Action.actionType_id
   WHERE Action.event_id = Event.id AND Action.deleted = 0 AND ActionType.deleted = 0
   AND (ActionType.serviceType IN (%(initialInspection)d, %(reinspection)d))) AS serviceTypeCount,
   (SELECT COUNT(ActionProperty_Job_Ticket.value)
    FROM Action
    INNER JOIN ActionType ON ActionType.id = Action.actionType_id
    INNER JOIN ActionPropertyType AS APT ON APT.actionType_id = ActionType.id
    INNER JOIN ActionProperty AS AP ON AP.action_id = Action.id
    INNER JOIN ActionProperty_Job_Ticket ON ActionProperty_Job_Ticket.id = AP.id
    WHERE Action.event_id = Event.id AND AP.type_id = APT.id
    AND APT.typeName = 'JobTicket'
    AND Action.deleted = 0 AND ActionType.deleted = 0
    AND APT.deleted = 0 AND AP.deleted = 0) AS directionsCount
FROM Visit
LEFT JOIN Event     ON Event.id = Visit.event_id
LEFT JOIN Client AS clientCT ON clientCT.id = Event.client_id
LEFT JOIN Person    ON Person.id = Visit.person_id
%(attacheJoins)s
WHERE Visit.deleted = 0
AND Event.deleted = 0
AND DATE(Event.setDate) <= DATE(Visit.date)
AND %(cond)s
) AS T
LEFT JOIN Person ON Person.id = T.person_id
LEFT JOIN rbPost ON rbPost.id = Person.post_id
%(externalJoins)s
GROUP BY visitId
ORDER BY specialityName, Person.lastName, Person.firstName, Person.patrName
    """
    begDate        = params.get('begDate', QDate())
    endDate        = params.get('endDate', QDate())
    orgStructureId = params.get('orgStructureId', None)
    ageFrom        = params.get('ageFrom', 0)
    ageTo          = params.get('ageTo', 150)
    contingentTypeId = params.get('contingentTypeId', None)
    personId       = params.get('personId', None)
    specialityId   = params.get('specialityId', None)
    financeId      = params.get('financeId', None)
    isAttache      = params.get('isAttache', False)
    orgId          = params.get('orgId', None)
    db = QtGui.qApp.db
    tableVisit  = db.table('Visit')
#    tableEvent  = db.table('Event')
#    tableClient = db.table('Client').alias('clientCT')
    tablePerson = db.table('Person')
    cond = []
    addDateInRange(cond, tableVisit['date'], begDate, endDate)

    visitFinanceType = u'IF(Visit.id IS NOT NULL, 1, 0) AS visitFinanceType,'
    if financeId:
        visitFinanceType = u'IF(Visit.finance_id = %s, 1, 0) AS visitFinanceType,'%(financeId)
    if personId:
        cond.append(tablePerson['id'].eq(personId))
    if specialityId:
        cond.append(tablePerson['speciality_id'].eq(specialityId))
    if orgStructureId:
        cond.append(tablePerson['orgStructure_id'].inlist(getOrgStructureDescendants(orgStructureId)))
    if ageFrom <= ageTo:
        cond.append('age(clientCT.birthDate, Event.setDate) >= %s'%ageFrom)
        cond.append('age(clientCT.birthDate, Event.setDate) < %s'%(ageTo+1))
    attacheJoins = u''
    if isAttache and orgId:
        tableClientAttach = db.table('ClientAttach')
        tableAttachType = db.table('rbAttachType')
        attacheJoins = '''INNER JOIN ClientAttach ON ClientAttach.client_id = clientCT.id
                          INNER JOIN rbAttachType ON rbAttachType.id = ClientAttach.attachType_id'''
        cond.append(tableClientAttach['LPU_id'].eq(orgId))
        cond.append(tableClientAttach['deleted'].eq(0))
        cond.append(tableAttachType['temporary'].eq(0))
        cond.append(db.joinOr([tableClientAttach['begDate'].isNull(), tableClientAttach['begDate'].lt(tableVisit['date'].addDays(1))]))
        cond.append(db.joinOr([tableClientAttach['endDate'].isNull(), tableClientAttach['endDate'].ge(tableVisit['date'])]))
    groupContingentType = 'NULL AS clientContingentType,'
    if contingentTypeId:
        groupContingentType = '(%s) AS clientContingentType, '%(appendContingentTypeCond(contingentTypeId))
    groupIdDef    = 'Person.speciality_id AS specialityId'
    groupNameDef  = 'rbSpeciality.name AS specialityName'
    externalJoins = 'LEFT JOIN rbSpeciality ON rbSpeciality.id = Person.speciality_id'
    return db.query(stmt
                    % dict(visitFinanceType = visitFinanceType,
                           groupContingentType = groupContingentType,
                           groupIdDef    = groupIdDef,
                           groupNameDef  = groupNameDef,
                           attacheJoins  = attacheJoins,
                           cond          = db.joinAnd(cond),
                           externalJoins = externalJoins,
                           initialInspection = CActionServiceType.initialInspection,
                           reinspection      = CActionServiceType.reinspection
                          )
                   )


class CReportMonitoredContingentBase(CReport):
    def getSetupDialog(self, parent):
        result = CReportMonitoredContingentSetupDialog(parent)
        result.setTitle(self.title())
        return result


    def produceTotalLine(self, table, title, total, add1):
        i = table.addRow()
        table.setText(i, 0, title, CReportBase.TableTotal)
        if add1 == 1:
            table.setText(i, 1, i-1)
        for j in xrange(len(total)):
            table.setText(i, j+1+add1, total[j], CReportBase.TableTotal)


class CReportServicesMonitoredContingent(CReportMonitoredContingentBase):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setPayPeriodVisible(False)
        self.setTitle(u'Контроль обслуживания наблюдаемого контингента', u'Контроль обслуживания наблюдаемого контингента')


    def dumpParams(self, cursor, params):
        db = QtGui.qApp.db
        description = []
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        if begDate or endDate:
           description.append(dateRangeAsStr(u'за период', begDate, endDate))
        contingentTypeId = params.get('contingentTypeId', None)
        ageFrom          = params.get('ageFrom', None)
        ageTo            = params.get('ageTo', None)
        orgStructureId   = params.get('orgStructureId', None)
        specialityId     = params.get('specialityId', None)
        financeId        = params.get('financeId', None)
        personId         = params.get('personId', None)
        isAttache        = params.get('isAttache', False)
        orgId            = params.get('orgId', None)
        if ageFrom is not None and ageTo is not None and ageFrom <= ageTo:
            description.append(u'возраст: c %d по %d %s' % (ageFrom, ageTo, agreeNumberAndWord(ageTo, (u'год', u'года', u'лет'))))
        if orgStructureId:
            description.append(u'подразделение: ' + getOrgStructureFullName(orgStructureId))
        if contingentTypeId:
            description.append(u'тип контингента: ' + forceString(db.translate('rbContingentType', 'id', contingentTypeId, 'name')))
        if financeId:
            description.append(u'тип финансирования визитов: ' + forceString(db.translate('rbFinance', 'id', financeId, 'name')))
        if specialityId:
            description.append(u'специальность: ' + forceString(db.translate('rbSpeciality', 'id', specialityId, 'name')))
        if personId:
            personInfo = getPersonInfo(personId)
            description.append(u'врач: ' + personInfo['shortName']+', '+personInfo['specialityName'])
        if isAttache:
            description.append(u'прикрепление к ЛПУ: ' + forceString(db.translate('Organisation', 'id', orgId, 'shortName')))
        description.append(u'отчёт составлен: ' + forceString(QDateTime.currentDateTime()))
        columns = [ ('100%', [], CReportBase.AlignLeft) ]
        table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
        for i, row in enumerate(description):
            table.setText(i, 0, row)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()


    def build(self, params):
        reportRowSize = 9
        query = selectData(params)
        reportData = {}
        personInfoList = []
        eventIdList = []
        clientIdList = {}
        clientCTIdList = {}
        contingentTypeId = params.get('contingentTypeId', None)
        while query.next():
            record  = query.record()
            clientId         = forceRef(record.value('client_id'))
            personId         = forceRef(record.value('person_id'))
            specialityId     = forceRef(record.value('specialityId'))
            visitFinanceType = forceInt(record.value('visitFinanceType'))
            eventId          = forceRef(record.value('event_id'))
            serviceTypeCount = forceInt(record.value('serviceTypeCount'))
            directionsCount  = forceInt(record.value('directionsCount'))
            reportRow = reportData.get((specialityId, personId), None)
            if not reportRow:
                reportRow = [0]*reportRowSize
                reportData[specialityId, personId] = reportRow
                specialityName = forceString(record.value('specialityName'))
                lastName = forceString(record.value('lastName'))
                firstName = forceString(record.value('firstName'))
                patrName = forceString(record.value('patrName'))
                personName = formatShortName(lastName, firstName, patrName)
                personInfoList.append((specialityName, personName, specialityId, personId))
            reportRow[0] += visitFinanceType
            if eventId and eventId not in eventIdList:
                reportRow[7] += directionsCount
                reportRow[8] += serviceTypeCount
                eventIdList.append(eventId)
            repClientIdList = clientIdList.get((specialityId, personId), [])
            if clientId and clientId not in repClientIdList:
                repClientIdList.append(clientId)
                clientIdList[(specialityId, personId)]= repClientIdList
                clientContingentType  = forceRef(record.value('clientContingentType'))
                reportRow[1] += 1
                reportRow[3] += forceInt(record.value('consentYes'))
                repClientCTIdList = clientCTIdList.get((specialityId, personId), [])
                if clientContingentType and clientContingentType not in repClientCTIdList:
                    repClientCTIdList.append(clientContingentType)
                    clientCTIdList[(specialityId, personId)] = repClientCTIdList
                    reportRow[2] += 1
                    if contingentTypeId:
                        contingentTypeCode, color = formatClientContingentType(clientId, contingentTypeId)
                        if color == u'#FF0000':
                            reportRow[4] += 1
                        elif color == u'#FFFF00':
                            reportRow[5] += 1
                        elif color == u'#00FF00':
                            reportRow[6] += 1
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        tableColumns = [
            ('30%', [u'ФИО врача', u'1'], CReportBase.AlignLeft),
            ( '7%', [u'Количество визитов', u'2'], CReportBase.AlignRight),
            ( '7%', [u'Всего принято пациентов', u'3'], CReportBase.AlignRight),
            ( '7%', [u'В т.ч. относящихся к наблюдаемому контингенту', u'4'], CReportBase.AlignRight),
            ( '7%', [u'Согласие', u'5'], CReportBase.AlignRight),
            ( '7%', [u'Не имеет требуемых Событий', u'6'], CReportBase.AlignRight),
            ( '7%', [u'Имеет Открытое Событие', u'7'], CReportBase.AlignRight),
            ( '7%', [u'Имеет Закрытое Событие', u'8'], CReportBase.AlignRight),
            ( '7%', [u'Кол-во выданных эл.направлений на сдачу анализов', u'9'], CReportBase.AlignRight),
            ( '7%', [u'Колво осмотров (заполненных Эл.карт)', u'10'], CReportBase.AlignRight),
            ( '7%', [u'Контроль', u'11'], CReportBase.AlignRight)
            ]
        table = createTable(cursor, tableColumns)
        prevGroupName = None
        total = None
        grandTotal = [0]*reportRowSize
        for groupName, personName, groupId, personId in personInfoList:
            if prevGroupName != groupName:
                if total:
                    self.produceTotalLine(table, u'всего', total, 0)
                total = [0]*reportRowSize
                i = table.addRow()
                table.mergeCells(i, 0, 1, reportRowSize+1)
                table.setText(i, 0, groupName, CReportBase.TableHeader)
                prevGroupName = groupName
            row = reportData[groupId, personId]
            i = table.addRow()
            table.setText(i, 0, personName)
            for j in xrange(reportRowSize):
                table.setText(i, j+1, row[j])
                total[j] += row[j]
                grandTotal[j] += row[j]
        if total:
            self.produceTotalLine(table, u'всего', total, 0)
        self.produceTotalLine(table, u'итого', grandTotal, 0)
        return doc


from Ui_ReportMonitoredContingentSetup import Ui_ReportMonitoredContingentSetupDialog

class CReportMonitoredContingentSetupDialog(QtGui.QDialog, Ui_ReportMonitoredContingentSetupDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.patientRequired = False
        self.setupUi(self)
        self.cmbOrgStructure.setOrgId(QtGui.qApp.currentOrgId())
        self.cmbOrgStructure.setValue(QtGui.qApp.currentOrgStructureId())
        self.cmbFilterContingentType.setTable('rbContingentType', addNone=True)
        self.cmbSpeciality.setTable('rbSpeciality')
        self.cmbFinance.setTable('rbFinance', addNone=True)
        self.flag = None


    def setTitle(self, title):
        self.setWindowTitle(title)


    def setParams(self, params):
        self.edtBegDate.setDate(params.get('begDate', QDate.currentDate()))
        self.edtEndDate.setDate(params.get('endDate', QDate.currentDate()))
        self.cmbOrgStructure.setValue(params.get('orgStructureId', None))
        self.edtAgeFrom.setValue(params.get('ageFrom', 0))
        self.edtAgeTo.setValue(params.get('ageTo', 150))
        self.cmbFilterContingentType.setValue(params.get('contingentTypeId', None)),
        self.cmbPerson.setValue(params.get('personId', None))
        self.cmbSpeciality.setValue(params.get('specialityId', None))
        self.cmbFinance.setValue(params.get('financeId', None))
        self.chkAttache.setChecked(params.get('isAttache', True))


    def params(self):
        params = {}
        params['begDate'] = self.edtBegDate.date()
        params['endDate'] = self.edtEndDate.date()
        params['orgStructureId'] = self.cmbOrgStructure.value()
        params['ageFrom'] = self.edtAgeFrom.value()
        params['ageTo'] = self.edtAgeTo.value()
        params['contingentTypeId'] = self.cmbFilterContingentType.value()
        params['personId'] = self.cmbPerson.value()
        params['specialityId'] = self.cmbSpeciality.value()
        params['financeId'] = self.cmbFinance.value()
        params['isAttache'] = self.chkAttache.isChecked()
        params['orgId'] = self.cmbOrgStructure.model().orgId
        return params

