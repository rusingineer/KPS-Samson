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
from PyQt4.QtCore import QDate

from library.crbcombobox import CRBModelDataCache
from library.Utils      import forceDate, forceRef, forceString

from Orgs.Utils         import getOrgStructureFullName

from Reports.Report     import CReport
from Reports.ReportBase import CReportBase, createTable
from Reports.Utils      import dateRangeAsStr

from Reports.Ui_ReportSMOClientsSetup import Ui_ReportSMOClientsSetupDialog

def selectEventActionData(params):
    begDate          = params.get('begDate', None)
    endDate          = params.get('endDate', None)
    db = QtGui.qApp.db
    tableEvent          = db.table('Event')
    tableAction         = db.table('Action')

    queryTable = tableEvent
    queryTable = queryTable.leftJoin(tableAction,  tableAction['event_id'].eq(tableEvent['id']))

    cond = [
#            tableEvent['client_id'].inlist(clientIdList),
            tableEvent['setDate'].ge(begDate),
            tableEvent['execDate'].lt(endDate.addDays(1)),
            tableEvent['deleted'].eq(0),
            tableAction['deleted'].eq(0),
            'EXISTS (SELECT ActionType_Service.id FROM ActionType_Service WHERE ActionType_Service.master_id = Action.actionType_id) OR Action.id IS NULL'
           ]

    cols = [
            tableEvent['client_id'].alias('clientId'),
            tableEvent['id'].alias('eventId'),
            tableAction['id'].alias('actionId'),
            tableEvent['setDate'].alias('eventBegDate'),
            tableEvent['execDate'].alias('eventEndDate')
           ]

    stmt = db.selectStmt(queryTable, cols, cond)
#    print stmt
    return db.query(stmt)


def selectEventVisitData(params):
    begDate          = params.get('begDate', None)
    endDate          = params.get('endDate', None)
    db = QtGui.qApp.db
    tableEvent          = db.table('Event')
    tableVisit          = db.table('Visit')

    queryTable = tableEvent
    queryTable = queryTable.leftJoin(tableVisit, tableVisit['event_id'].eq(tableEvent['id']))

    cond = [
#            tableEvent['client_id'].inlist(clientIdList),
            tableEvent['setDate'].ge(begDate),
            tableEvent['execDate'].lt(endDate.addDays(1)),
            tableEvent['deleted'].eq(0),
            tableVisit['deleted'].eq(0),
            'DATE(Event.setDate) <= DATE(Visit.date)'
           ]

    cols = [
            tableEvent['client_id'].alias('clientId'),
            tableEvent['id'].alias('eventId'),
            tableVisit['id'].alias('visitId'),
            tableEvent['setDate'].alias('eventBegDate'),
            tableEvent['execDate'].alias('eventEndDate')
           ]

    stmt = db.selectStmt(queryTable, cols, cond)
#    print stmt
    return db.query(stmt)


def selectClientPolicyData(params):
    begDate          = params.get('begDate', None)
    endDate          = params.get('endDate', None)
    policyTypeId     = params.get('policyTypeId', None)

    db = QtGui.qApp.db

    tableClientPolicy   = db.table('ClientPolicy')

    queryTable = tableClientPolicy

    cpEndDateCond = [
                     tableClientPolicy['endDate'].ge(begDate),
                     db.joinAnd([tableClientPolicy['endDate'].isNull(),
                     'NOT EXISTS(SELECT CP.id FROM ClientPolicy AS CP WHERE CP.begDate > ClientPolicy.begDate AND CP.client_id = ClientPolicy.client_id)'])
                    ]

    cond = [
             tableClientPolicy['deleted'].eq(0),
             tableClientPolicy['begDate'].lt(endDate.addDays(1)),
             db.joinOr(cpEndDateCond)
           ]

    if policyTypeId:
        if policyTypeId == -1:
            data = CRBModelDataCache.getData('rbPolicyType')
            policyTypeIdList = [data.getIdByCode(code) for code in ('1', '2')]
            cond.append(tableClientPolicy['policyType_id'].inlist(policyTypeIdList))
        else:
            cond.append(tableClientPolicy['policyType_id'].eq(policyTypeId))

    cols = [
            tableClientPolicy['insurer_id'].alias('insurerId'),
            tableClientPolicy['client_id'].alias('clientId'),
            tableClientPolicy['id'].alias('clientPolicyId'),
            tableClientPolicy['begDate'].alias('clientPolicyBegDate'),
            tableClientPolicy['endDate'].alias('clientPolicyEndDate'),
            tableClientPolicy['policyType_id'].alias('policyTypeId')
           ]

    stmt = db.selectStmt(queryTable, cols, cond)
#    print stmt
    return db.query(stmt)




class CReportSMOClients(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Сводка по СМО об обслуживании пациентов')
        self._mapInsurerId2Info = {}
        self._mapClientId2Policy = {}
        self._mapInsurerId2Name = {}


    def getSetupDialog(self, parent):
        result = CReportSMOClientsSetupDialog(parent)
        result.setTitle(self.title())
        return result


    def getDescription(self, params):
        begDate        = params.get('begDate', QDate())
        endDate        = params.get('endDate', QDate())
        orgStructureId = params.get('orgStructureId', None)
        speciality     = params.get('specialityText', None)
        person         = params.get('personText', None)
        purpose        = params.get('purposeText', None)
        medicalAidKind = params.get('medicalAidKindText', None)
        eventType      = params.get('eventTypeText', None)
        paying         = params.get('payingText', None)
        policyType     = params.get('policyTypeText', None)
        rows = []
        if begDate or endDate:
            rows.append(dateRangeAsStr(u'за период', begDate, endDate))
        if orgStructureId:
            rows.append(u'подразделение: ' + getOrgStructureFullName(orgStructureId))
        if speciality:
            rows.append(u'специальность: ' + forceString(speciality))
        if person:
            rows.append(u'врач: ' + forceString(person))
        if purpose:
            rows.append(u'назначение события: ' + forceString(purpose))
        if medicalAidKind:
            rows.append(u'вид медицинской помощи: ' + forceString(medicalAidKind))
        if eventType:
            rows.append(u'тип события: ' + forceString(eventType))
        if paying:
            rows.append(u'оплата: ' + forceString(paying))
        if policyType:
            rows.append(u'тип полиса: ' + forceString(policyType))
        return rows


    def resetHelpers(self):
        self._mapInsurerId2Info.clear()
        self._mapClientId2Policy.clear()

    def build(self, params):
        self.resetHelpers()

        currentDate = QDate.currentDate()
        begDate                  = params.get('begDate', currentDate)
        endDate                  = params.get('endDate', currentDate)

        clientPolicyQuery = selectClientPolicyData(params)
        self.structClientPolicyInfo(clientPolicyQuery, begDate, endDate)

        self.structInfo(selectEventActionData(params), begDate, endDate)
        self.structInfo(selectEventVisitData(params), begDate, endDate)

        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()

        tableColumns = [
                        ('%2',
                        [u'№'], CReportBase.AlignRight),
                        ('%15',
                        [u'СМО'], CReportBase.AlignLeft),
                        ('%10',
                        [u'Кол-во полисов'], CReportBase.AlignLeft),
                        ('%10',
                        [u'Кол-во пациентов'], CReportBase.AlignLeft),
                        ('%10',
                        [u'Кол-во обращений'], CReportBase.AlignLeft),
                        ('%10',
                        [u'Кол-во визитов'], CReportBase.AlignLeft),
                        ('%10',
                        [u'Кол-во услуг'], CReportBase.AlignLeft),
                        ('%10',
                        [u'Прикреплено'], CReportBase.AlignLeft),
                        ('%10',
                        [u'Откреплено'], CReportBase.AlignLeft)
                       ]

        table = createTable(cursor, tableColumns)

        for insurerId, insurerInfo in self._mapInsurerId2Info.items():
            i = table.addRow()
            table.setText(i, 0, i)
            table.setText(i, 1, insurerInfo['insurerName'])
            table.setText(i, 2, len(insurerInfo['clientIdList']))
            table.setText(i, 3, len(insurerInfo['clientPolicyIdList']))
            table.setText(i, 4, len(insurerInfo['eventIdList']))
            table.setText(i, 5, len(insurerInfo['visitIdList']))
            table.setText(i, 6, len(insurerInfo['actionIdList']))
            table.setText(i, 7, insurerInfo['clientPolicyInCount'])
            table.setText(i, 8, insurerInfo['clientPolicyOutCount'])
        return doc


    def structClientPolicyInfo(self, query, begDate, endDate):
        while query.next():
            record = query.record()
            insurerId           = record.value('insurerId').toInt()[0]
            clientId            = record.value('clientId').toInt()[0]
            clientPolicyBegDate = record.value('clientPolicyBegDate').toDate()
            clientPolicyEndDate = record.value('clientPolicyEndDate').toDate()
            policyTypeId        = record.value('policyTypeId').toInt()[0]
            clientPolicyId      = record.value('clientPolicyId').toInt()[0]

            clientPolicyList = self._mapClientId2Policy.setdefault(clientId, [])
            clientPolicyList.append((clientPolicyId, insurerId, clientPolicyBegDate, clientPolicyEndDate, policyTypeId))

            insurerName = self.getInsurerName(insurerId)

            insurerInfo = self._mapInsurerId2Info.setdefault(
                                                             insurerId, {
                                                                         'insurerName'          : insurerName,
                                                                         'clientIdList'         : [],
                                                                         'eventIdList'          : [],
                                                                         'actionIdList'         : [],
                                                                         'visitIdList'          : [],
                                                                         'clientPolicyIdList'   : [],
                                                                         'clientPolicyInCount'  : 0,
                                                                         'clientPolicyOutCount' : 0
                                                                        }
                                                            )

            if clientPolicyId not in insurerInfo['clientPolicyIdList']:
                insurerInfo['clientPolicyIdList'].append(clientPolicyId)

                if clientPolicyBegDate:
                    if begDate <=clientPolicyBegDate <= endDate:
                        insurerInfo['clientPolicyInCount'] += 1

                if clientPolicyEndDate:
                    if begDate <=clientPolicyEndDate <= endDate:
                        insurerInfo['clientPolicyOutCount'] += 1


    def getPolicyInfo(self, clientId, eventBegDate, eventEndDate):
        clientPolicyList = self._mapClientId2Policy.get(clientId, None)
        if not clientPolicyList:
            return None
        for clientPolicy in clientPolicyList:
            clientPolicyId, insurerId, clientPolicyBegDate, clientPolicyEndDate, policyTypeId = clientPolicy
            if clientPolicyBegDate <= eventBegDate:
                if  eventBegDate and (eventBegDate <= clientPolicyEndDate or not clientPolicyEndDate):
                    insurerName = self.getInsurerName(insurerId)
                    return insurerId, insurerName, clientPolicyId, clientPolicyBegDate, clientPolicyEndDate
        return None


    def getInsurerName(self, insurerId):
        insurerName = self._mapInsurerId2Name.get(insurerId, None)
        if insurerName is None:
            insurerName = forceString(QtGui.qApp.db.translate('Organisation', 'id', insurerId, 'shortName'))
            self._mapInsurerId2Name[insurerId] = insurerName
        return insurerName


    def structInfo(self, query, begDate, endDate):
        while query.next():
            record = query.record()
            actionId     = forceRef(record.value('actionId'))
            eventId      = forceRef(record.value('eventId'))
            visitId      = forceRef(record.value('visitId'))
            clientId     = forceRef(record.value('clientId'))
            eventBegDate = forceDate(record.value('eventBegDate'))
            eventEndDate = forceDate(record.value('eventEndDate'))
            info = self.getPolicyInfo(clientId, eventBegDate, eventEndDate)
            if not info:
                continue
            insurerId, insurerName, clientPolicyId, clientPolicyBegDate, cientPolicyEndDate = info

#            insurerId          = forceRef(record.value('insurerId'))
#            insurerName        = forceString(record.value('insurerName'))

#            insurerInfo = self._mapInsurerId2Info.setdefault(
#                                                             insurerId, {
#                                                                         'insurerName'          : insurerName,
#                                                                         'clientIdList'         : [],
#                                                                         'eventIdList'          : [],
#                                                                         'actionIdList'         : [],
#                                                                         'visitIdList'          : [],
#                                                                         'clientPolicyIdList'   : [],
#                                                                         'clientPolicyInCount'  : 0,
#                                                                         'clientPolicyOutCount' : 0
#                                                                        }
#                                                            )

            insurerInfo = self._mapInsurerId2Info.get(insurerId, None)
            if insurerInfo is None:
                continue

            eventId            = forceRef(record.value('eventId'))
            if eventId not in insurerInfo['eventIdList']:
                insurerInfo['eventIdList'].append(eventId)

            actionId           = forceRef(record.value('actionId'))
            if actionId and actionId not in insurerInfo['actionIdList']:
                insurerInfo['actionIdList'].append(actionId)

            visitId            = forceRef(record.value('visitId'))
            if visitId and visitId not in insurerInfo['visitIdList']:
                insurerInfo['visitIdList'].append(visitId)

            clientId           = forceRef(record.value('clientId'))
            if clientId not in insurerInfo['clientIdList']:
                insurerInfo['clientIdList'].append(clientId)


class CReportSMOClientsSetupDialog(QtGui.QDialog, Ui_ReportSMOClientsSetupDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)

        self.setupUi(self)

        self.cmbPolicyType.setTable('rbPolicyType', addNone=True, specialValues=((-1, u'ОМС', u'ОМС'), ))

        self.cmbSpeciality.setTable('rbSpeciality', addNone=True)

        self.cmbPurpose.setTable('rbEventTypePurpose', addNone=True)

        self.cmbMedicalAidKind.setTable('rbMedicalAidKind', addNone=True)

        self.cmbEventType.setTable('EventType', addNone=True)


    def setTitle(self, title):
        self.setWindowTitle(title)

    def params(self):
        params = {}

        params['begDate'] = self.edtBegDate.date()
        params['endDate'] = self.edtEndDate.date()
        params['orgStructureId'] = self.cmbOrgStructure.value()
        params['specialityId'] = self.cmbSpeciality.value()
        params['personId'] = self.cmbPerson.value()
        params['purposeId'] = self.cmbPurpose.value()
        params['medicalAidKindId'] = self.cmbMedicalAidKind.value()
        params['eventTypeId'] = self.cmbEventType.value()
        params['paying'] = self.cmbPaying.currentIndex()
        params['policyTypeId'] = self.cmbPolicyType.value()

        params['orgStructureText'] = self.cmbOrgStructure.currentText()
        params['specialityText'] = self.cmbSpeciality.currentText()
        params['personText'] = self.cmbPerson.currentText()
        params['purposeText'] = self.cmbPurpose.currentText()
        params['medicalAidKindText'] = self.cmbMedicalAidKind.currentText()
        params['eventTypeText'] = self.cmbEventType.currentText()
        params['payingText'] = unicode(self.cmbPaying.currentText())
        params['policyTypeText'] = self.cmbPolicyType.currentText()

        return params

    def setParams(self, params):
        currentDate = QDate.currentDate()
        self.edtBegDate.setDate(params.get('begDate', currentDate))
        self.edtEndDate.setDate(params.get('endDate', currentDate))
        self.cmbOrgStructure.setValue(params.get('orgStructureId', None))
        self.cmbSpeciality.setValue(params.get('specialityId', None))
        self.cmbPerson.setValue(params.get('personId', None))
        self.cmbPurpose.setValue(params.get('purposeId', None))
        self.cmbMedicalAidKind.setValue(params.get('medicalAidKindId', None))
        self.cmbEventType.setValue(params.get('eventTypeId', None))
        self.cmbPaying.setCurrentIndex(params.get('paying', 0))
        self.cmbPolicyType.setValue(params.get('policyTypeId', None))
















