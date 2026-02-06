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

from library.Utils       import forceString, forceDouble, formatName, formatDate, formatDateTime
from library.DialogBase  import CDialogBase
from Reports.Report      import CReport
from Reports.ReportBase  import CReportBase, createTable
from Orgs.Utils import getOrgStructureDescendants, getOrgStructureFullName
from Reports.Ui_ReportVaccineJournalSetup import Ui_ReportVaccineJournalSetup


def getVaccineTypes(vaccineId=None):
    stmt = """SELECT DISTINCT vaccinationType
              FROM rbVaccine_Schema
              WHERE vaccinationType != '' AND %s
              ORDER BY 1"""
    cond = 'FALSE'
    if vaccineId:
        cond = 'master_id = %d' % vaccineId
    query = QtGui.qApp.db.query(stmt % cond)
    items = [u'не задано']
    while query.next():
        items.append(forceString(query.value(0)))
    return items


def selectData(params):
    db = QtGui.qApp.db

    begDate = params.get('begDate')
    endDate = params.get('endDate')
    ageFrom = params.get('ageFrom', 0)
    ageTo   = params.get('ageTo', 150)
    sex     = params.get('sex')
    vaccineId = params.get('vaccineId')
    infectionId = params.get('infectionId')
    vaccineType = params.get('vaccineType')
    orgStructureId = params.get('orgStructureId')
    orgStructureIdPacient = params.get('orgStructureIdPacient')

    tableClient = db.table('Client')
    tableCV = db.table('ClientVaccination')
    tableCA = db.table('ClientAttach')
    tablePerson = db.table('Person')
    tableOrgStr = db.table('OrgStructure')
    tableVaccine = db.table('rbVaccine')
    tableOrgStrPac = db.table('OrgStructure').alias('OrgStrPac')

    table = tableClient
    table = table.innerJoin(tableCV, tableCV['client_id'].eq(tableClient['id']))
    table = table.innerJoin(tableVaccine, tableCV['vaccine_id'].eq(tableVaccine['id']))
    table = table.innerJoin(tablePerson, tableCV['person_id'].eq(tablePerson['id']))
    table = table.innerJoin(tableOrgStr, tablePerson['orgStructure_id'].eq(tableOrgStr['id']))

    cols = [
        tableClient['lastName'],
        tableClient['firstName'],
        tableClient['patrName'],
        tableClient['birthDate'],
        tableCV['vaccinationType'],
        tableCV['datetime'],
        tableCV['dose'],
        tableCV['seria'],
        tableVaccine['name'].alias('vaccineName'),
        tableOrgStr['name'].alias('orgName'),
        u'age(Client.birthDate, ClientVaccination.datetime) AS clientAge',
        u'getClientLocAddress(Client.id) AS clientAddress',
        u'getClientWork(Client.id) AS clientWork',
    ]

    cond = [
        tableClient['deleted'].eq(0),
        tableCV['deleted'].eq(0),
        tablePerson['deleted'].eq(0),
        tableOrgStr['deleted'].eq(0),
        u'age(Client.birthDate, ClientVaccination.datetime) BETWEEN %d AND %d' % (ageFrom, ageTo)
    ]

    if begDate:
        cond.append(tableCV['datetime'].ge(begDate))
    if endDate:
        cond.append(tableCV['datetime'].lt(endDate.addDays(1)))
    if sex:
        cond.append(tableClient['sex'].eq(sex))
    if orgStructureId:
        cond.append(tableOrgStr['id'].inlist(getOrgStructureDescendants(orgStructureId)))
    if vaccineType and vaccineType != u'не задано':
        cond.append(tableCV['vaccinationType'].eq(vaccineType))
    if vaccineId:
        cond.append(tableCV['vaccine_id'].eq(vaccineId))
    if infectionId:
        tableIV = db.table('rbInfection_rbVaccine')
        table = table.innerJoin(tableIV, tableIV['vaccine_id'].eq(tableVaccine['id']))
        cond.append(tableIV['infection_id'].eq(infectionId))
    if orgStructureIdPacient:
        table = table.leftJoin(tableCA, " ClientAttach.id =(SELECT MAX(ClientAttach.id) FROM ClientAttach INNER JOIN rbAttachType ON rbAttachType.id = ClientAttach.attachType_id \
                WHERE client_id = Client.id AND ClientAttach.deleted = 0 AND (ClientAttach.endDate is NULL OR ClientAttach.endDate>= '{date}') AND NOT rbAttachType.TEMPORARY)")
        table = table.leftJoin(tableOrgStrPac, tableCA['orgStructure_id'].eq(tableOrgStrPac['id']))
        cond.append(tableOrgStrPac['id'].inlist(getOrgStructureDescendants(orgStructureIdPacient)))

    stmt = db.selectStmt(table, cols, cond, order='1,2,3')
    stmt = stmt.format(date=db.formatDate(endDate)[1:11], cond=db.joinAnd(cond))
    return db.query(stmt)



class CReportVaccineJournal(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Журнал вакцинации')


    def getSetupDialog(self, parent):
        result = CReportVaccineJournalSetup(parent)
        result.setWindowTitle(self.title())
        return result


    def getDescription(self, params):
        rows = CReport.getDescription(self, params)
        vaccineType = params.get('vaccineType')
        vaccineId = params.get('vaccineId')
        infectionId = params.get('infectionId')
        orgStructureIdPacient = params.get('orgStructureIdPacient')

        if vaccineId:
            rows.insert(-1, u'вакцина: ' + forceString(
                QtGui.qApp.db.translate('rbVaccine', 'id', vaccineId, 'name')))
        if vaccineType and vaccineType != u'не задано':
            rows.insert(-1, u'тип прививки: ' + vaccineType)
        if infectionId:
            rows.insert(-1, u'инфекция: ' + forceString(
                QtGui.qApp.db.translate('rbInfection', 'id', infectionId, 'name')))
        if orgStructureIdPacient:
            rows.insert(-1, u'Прикрепление к участку: ' +  getOrgStructureFullName(orgStructureIdPacient))

        return rows


    def build(self, params):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()

        tableColumns = [
            ('5%',  [u'№'], CReportBase.AlignCenter),
            ('10%', [u'Фамилия, имя, отчетсво'], CReportBase.AlignLeft),
            ('10%', [u'Дата рождения'], CReportBase.AlignLeft),
            ('10%', [u'Домашний адрес'], CReportBase.AlignLeft),
            ('15%', [u'Название места работы или учебного заведения'], CReportBase.AlignLeft),
            ('10%', [u'Название препарата'], CReportBase.AlignLeft),
            ('10%', [u'Тип'], CReportBase.AlignLeft),
            ('10%', [u'Дата вакцинации'], CReportBase.AlignLeft),
            ('10%', [u'Доза'], CReportBase.AlignLeft),
            ('10%', [u'Серия'], CReportBase.AlignLeft),
        ]
        table = createTable(cursor, tableColumns)
        query = selectData(params)
        i = 1
        while query.next():
            record = query.record()
            row = table.addRow()
            table.setText(row, 0, i)
            table.setText(row, 1, formatName(record.value('lastName'), record.value('firstName'), record.value('patrName')))
            table.setText(row, 2, formatDate(record.value('birthDate')))
            table.setText(row, 3, forceString(record.value('clientAddress')))
            table.setText(row, 4, forceString(record.value('clientWork')))
            table.setText(row, 5, forceString(record.value('vaccineName')))
            table.setText(row, 6, forceString(record.value('vaccinationType')))
            table.setText(row, 7, formatDateTime(record.value('datetime')))
            table.setText(row, 8, forceDouble(record.value('dose')))
            table.setText(row, 9, forceString(record.value('seria')))
            i += 1

        return doc



class CReportVaccineJournalSetup(CDialogBase, Ui_ReportVaccineJournalSetup):
    __params = None
    def __init__(self, parent=None):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        self.cmbOrgStructure.setOrgId(QtGui.qApp.currentOrgId())
        self.cmbOrgStructure.setValue(QtGui.qApp.currentOrgStructureId())
        self.cmbVaccineType.addItems([u''] + getVaccineTypes())
        self.cmbVaccine.setTable('rbVaccine')
        self.cmbInfection.setTable('rbInfection')
        self.cmbOrgStructurePacient.setOrgId(QtGui.qApp.currentOrgId())
        self.cmbOrgStructurePacient.setValue(QtGui.qApp.currentOrgStructureId())


    def params(self):
        result = {}
        result['begDate'] = self.edtBegDate.date()
        result['endDate'] = self.edtEndDate.date()
        result['vaccineType'] = forceString(self.cmbVaccineType.currentText())
        result['vaccineId'] = self.cmbVaccine.value()
        result['infectionId'] = self.cmbInfection.value()
        result['ageFrom'] = self.edtAgeFrom.value()
        result['ageTo'] = self.edtAgeTo.value()
        result['orgStructureId'] = self.cmbOrgStructure.value()
        result['orgStructureIdPacient'] = self.cmbOrgStructurePacient.value()
        result['sex'] = self.cmbSex.currentIndex()
        CReportVaccineJournalSetup.__params = result
        return result


    def setParams(self, params):
        if CReportVaccineJournalSetup.__params:
            params = CReportVaccineJournalSetup.__params
        self.edtBegDate.setDate(params.get('begDate', QDate.currentDate()))
        self.edtEndDate.setDate(params.get('endDate', QDate.currentDate()))
        self.cmbOrgStructure.setValue(params.get('orgStructureId'))
        self.edtAgeFrom.setValue(params.get('ageFrom', 0))
        self.edtAgeTo.setValue(params.get('ageTo', 150))
        self.cmbVaccine.setValue(params.get('vaccineId', None))
        self.cmbInfection.setValue(params.get('infectionId', None))
        self.cmbSex.setCurrentIndex(params.get('sex', 0))

        vaccineType = params.get('vaccineType')
        if vaccineType and vaccineType != u'не задано':
            index = self.cmbVaccineType.findText(vaccineType)
            self.cmbVaccineType.setCurrentIndex(index)
        self.cmbOrgStructurePacient.setValue(params.get('orgStructureIdPacient'))


    @pyqtSignature('int')
    def on_cmbVaccine_currentIndexChanged(self, index):
        self.cmbVaccineType.clear()
        self.cmbVaccineType.addItems(getVaccineTypes(self.cmbVaccine.value()))

