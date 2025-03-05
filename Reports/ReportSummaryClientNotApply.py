#! /usr/bin/env python
# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012 SAMSON Group. All rights reserved.
## Copyright (C) 2015 Oskin A.
## Copyright (C) 2016 Oskin A. and Arkhipov S.
## Copyright (C) 2021 Arkhipov S.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import *

from library.Utils import *

from Orgs.Utils import *
from Registry.Utils import *

from Reports.Report import CReport
from Reports.ReportBase import *

from Ui_ReportSummaryClientNotApply import Ui_ReportSummaryClientNotApply


def selectData(params):
    begDate = params.get('begDate', None)
    endDate = params.get('endDate', None)

    orgStructureId = params.get('OrgStructureId', None)

    personId = params.get('personId', None)
    attached = params.get('attached', None)
    specialityId = params.get('specialityId')
    dn = params.get('dn')
    sex = params.get('sex', 0)
    ageFrom = params.get('ageFrom', 0)
    ageTo = params.get('ageTo', 150)

    db = QtGui.qApp.db

    tableEvent = db.table('Event').alias('e')
    tableClientAttach = db.table('ClientAttach').alias('ca')
    tableOrgStructure = db.table('OrgStructure').alias('os')
    tableClient = db.table('Client').alias('c')
    tableClientDocument = db.table('ClientDocument').alias('cd')
    tableAttachType = db.table('rbAttachType').alias('rat')
    tableDiagnostic = db.table('Diagnostic')
    tablerbDisp = db.table('rbDispanser')
    tablePerson = db.table('Person')

    cond = [
        tableEvent['client_id'].isNotNull(),
        tableClientAttach['deleted'].eq(0),
        tableClientAttach['endDate'].isNull(),
        "not rat.outcome"
    ]

    if orgStructureId or personId:
        if personId:
            cond.append(tableEvent['execPerson_id'].eq(personId))
        if orgStructureId:
            setOrgStructureIdList = db.getDescendants('OrgStructure', 'parent_id', orgStructureId)
            cond.append(tableOrgStructure['id'].inlist(setOrgStructureIdList))
    if specialityId:
        cond.append(tablePerson['speciality_id'].eq(specialityId))
    if attached == 2:
        cond.append(db.joinOr([tableAttachType['temporary'].ne(0), tableClientAttach['id'].isNull()]))
    elif attached == 1:
        cond.extend([tableAttachType['temporary'].eq(0), tableClientAttach['id'].isNotNull()])
    if dn:
        cond.append(tablerbDisp['id'].eq(dn))
    if sex:
        cond.append(tableClient['sex'].eq(sex))
    if ageFrom <= ageTo:
        # cond.append('Diagnostic.endDate >= ADDDATE(c.birthDate, INTERVAL %d YEAR)'%ageFrom)
        # cond.append('Diagnostic.endDate < SUBDATE(ADDDATE(c.birthDate, INTERVAL %d YEAR),1)'%(ageTo+1))
        cond.append('(e.execDate >= ADDDATE(c.birthDate, INTERVAL %d YEAR)) AND (e.execDate < ADDDATE(c.birthDate, INTERVAL %d YEAR))''' % (ageFrom, ageTo+1))

    queryTable = tableClient
    queryTable = queryTable.leftJoin(tableEvent, tableEvent['client_id'].eq(tableClient['id']))
    queryTable = queryTable.leftJoin(tablePerson, tableEvent['execPerson_id'].eq(tablePerson['id']))
    queryTable = queryTable.leftJoin(tableClientAttach, "ca.id = getClientAttachId(c.id,2)")
    queryTable = queryTable.leftJoin(tableAttachType, (tableClientAttach['attachType_id'].eq(tableAttachType['id'])))
    queryTable = queryTable.leftJoin(tableOrgStructure,
                                     tableOrgStructure['id'].eq(tableClientAttach['orgStructure_id']))
    queryTable = queryTable.leftJoin(tableClientDocument, "cd.id = getClientDocumentId(c.id)")
    queryTable = queryTable.leftJoin(tableDiagnostic, tableEvent['id'].eq(tableDiagnostic['event_id']))
    queryTable = queryTable.leftJoin(tablerbDisp, tableDiagnostic['dispanser_id'].eq(tablerbDisp['id']))


    cols = [
        tableClient['id'].alias('clientId'),
        tableClient['lastName'],
        tableClient['firstName'],
        tableClient['patrName'],
        tableClient['birthDate'],
        tableClient['sex'],
        'getClientContacts(c.id) AS contact',
        'getClientRegAddress(c.id) AS registry',
        'getClientLocAddress(c.id) AS live',
        'getOrgStructureInfisCode(os.id) AS attach',
        'getClientDocument(c.id) AS passport',
        tableClient['SNILS'],
        tableOrgStructure['infisInternalCode'].alias('area'),
        tableClientAttach['begDate'].alias('caBegDate'),
        tableClientDocument['originCode'],
        tableClientDocument['origin'],
        u'MAX(e.execDate) as maxdate'
    ]

    # querytable2 = tableEvent
    # cond2 = [tableEvent['client_id'].isNotNull(),
    #          tableEvent['execDate'].dateLe(begDate.addDays(-1))]
    # cols2 = tableEvent['client_id'].alias('clientId')
    # listClientId = readQuery(db.query(db.selectDistinctStmt(querytable2, cols2, cond2)))
    # cond.append(tableClient['id'].inlist(listClientId))
    querytable3 = tableEvent
    cond3 = [tableEvent['client_id'].isNotNull(),
             tableEvent['execDate'].dateGe(begDate),
             tableEvent['execDate'].dateLe(endDate)]
    cols3 = tableEvent['client_id'].alias('clientId')
    listClientId = readQuery(db.query(db.selectStmt(querytable3, cols3, cond3)))
    cond.append(tableClient['id'].notInlist(listClientId))
    stmt = db.selectStmtGroupBy(queryTable, cols, cond, group='clientId')
    return db.query(stmt)


def readQuery(query):
    listClientID = []
    while query.next():
        record = query.record()
        listClientID.append(forceInt(record.value('clientId')))
    return list(set(listClientID))


class CReportSummaryClientNotApply(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Сводка по пациентам (не обращавшиеся в МО)')

    def getSetupDialog(self, parent):
        result = CReportSummaryClientNotApplyDialog(parent)
        result.setTitle(self.title())

        return result

    def getDescription(self, params):
        db = QtGui.qApp.db

        begDate = params.get('begDate', None)
        endDate = params.get('endDate', None)
        setOrgStructureId = params.get('setOrgStructureId', None)
        personId = params.get('personId', None)

        rows = []
        if begDate:
            rows.append(u'Начальная дата периода: %s' % forceString(begDate))
        if endDate:
            rows.append(u'Конечная дата периода: %s' % forceString(endDate))
        if setOrgStructureId:
            rows.append(u'Подразделение: %s' % forceString(
                db.translate('OrgStructure', 'id', setOrgStructureId, 'CONCAT_WS(\' | \', code,name)')))
        if personId:
            rows.append(u'Исполнитель: %s' % forceString(db.translate('vrbPerson', 'id', personId, 'name')))

        return rows

    def build(self, params):
        query = selectData(params)

        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportSubTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()

        tableColumns = [
            ('%2', [u'№'], CReportBase.AlignRight),
            ('%6', [u'Код пациента'], CReportBase.AlignCenter),
            ('%20', [u'ФИО'], CReportBase.AlignLeft),
            ('%8', [u'Дата рождения'], CReportBase.AlignCenter),
            ('%3', [u'пол'], CReportBase.AlignCenter),
            ('%8', [u'СНИЛС'], CReportBase.AlignCenter),
            ('%8', [u'Контакты  '], CReportBase.AlignLeft),
            ('%8', [u'Адрес пациента'], CReportBase.AlignLeft),
            ('%6', [u'Код ОМС'], CReportBase.AlignCenter),
            ('%8', [u'Дата прикрепления'], CReportBase.AlignCenter),
            ('%8', [u'Паспорт '], CReportBase.AlignLeft),
            ('%8', [u'Код подразделения'], CReportBase.AlignLeft),
            ('%8', [u'Кем выдан'], CReportBase.AlignLeft),
            ('%8', [u'Последняя дата обращения'], CReportBase.AlignCenter)

        ]
        table = createTable(cursor, tableColumns)
        n = 1
        while query.next():
            record = query.record()

            tableRow = table.addRow()
            table.setText(tableRow, 0, n)
            table.setText(tableRow, 1, forceString(record.value('clientID')))
            table.setText(tableRow, 2, formatName(forceString(record.value('lastName')),
                                                  forceString(record.value('firstName')),
                                                  forceString(record.value('patrName'))))
            table.setText(tableRow, 3, forceString(record.value('birthDate')))
            if forceInt(record.value('sex')) == 2:
                sex = u'Ж'
            else:
                sex = u'М'
            table.setText(tableRow, 4, sex)
            table.setText(tableRow, 5, forceString(record.value('snils')))
            table.setText(tableRow, 6, forceString(record.value('contact')))
            table.setText(tableRow, 7, (forceString(record.value('registry')) + '\n' +
                                        forceString(record.value('life'))))
            table.setText(tableRow, 8, forceString(record.value('attach')))
            table.setText(tableRow, 9, forceString(record.value('caBegDate')))
            table.setText(tableRow, 10, forceString(record.value('passport')))
            table.setText(tableRow, 11, forceString(record.value('originCode')))
            table.setText(tableRow, 12, forceString(record.value('origin')))
            table.setText(tableRow, 13, forceString(record.value('maxdate')))

            n += 1

        return doc


class CReportSummaryClientNotApplyDialog(QtGui.QDialog, Ui_ReportSummaryClientNotApply):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)

        self.setupUi(self)

        self.cmbSpeciality.setTable('rbSpeciality', addNone=True)
        self.cmbdn.setTable('rbDispanser', addNone=True)
        self.cmbOrgStructure.setOrgId(QtGui.qApp.currentOrgId())
        self.cmbOrgStructure.setValue(QtGui.qApp.currentOrgStructureId())
        if QtGui.qApp.userSpecialityId:
            self.cmbPerson.setValue(QtGui.qApp.userId)
            self.cmbSpeciality.setValue(QtGui.qApp.userSpecialityId)

    def setTitle(self, title):
        self.setWindowTitle(title)

    def setParams(self, params):
        date = QDate.currentDate()
        self.edtBegDate.setDate(params.get('begDate', date))
        self.edtEndDate.setDate(params.get('endDate', date))
        self.cmbOrgStructure.setValue(params.get('OrgStructureId', None))
        self.cmbPerson.setValue(params.get('personId', None))
        self.cmbSpeciality.setValue(params.get('specialityId', None))
        self.cmbdn.setValue(params.get('dn', None))
        self.cmbSex.setCurrentIndex(params.get('sex', 0))
        self.edtAgeFrom.setValue(params.get('ageFrom', 0))
        self.edtAgeTo.setValue(params.get('ageTo', 150))

    def params(self):
        result = {}
        result['begDate'] = self.edtBegDate.date()
        result['endDate'] = self.edtEndDate.date()
        result['OrgStructureId'] = self.cmbOrgStructure.value()
        result['personId'] = self.cmbPerson.value()
        result['specialityId'] = self.cmbSpeciality.value()
        result['attached'] = self.cmbattached.currentIndex()
        result['dn'] = self.cmbdn.value()
        result['sex'] = self.cmbSex.currentIndex()
        result['ageFrom'] = self.edtAgeFrom.value()
        result['ageTo'] = self.edtAgeTo.value()
        return result

    @pyqtSignature('int')
    def on_cmbOrgStructure_currentIndexChanged(self, index):
        orgStructureId = self.cmbOrgStructure.value()
        self.cmbPerson.setOrgStructureId(orgStructureId)


    @pyqtSignature('int')
    def on_cmbSpeciality_currentIndexChanged(self, index):
        specialityId = self.cmbSpeciality.value()
        self.cmbPerson.setSpecialityId(specialityId)
