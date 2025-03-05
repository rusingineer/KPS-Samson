# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2024 SAMSON Group. All rights reserved.
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

from Orgs.Utils import getOrgStructureDescendants, getOrgStructureFullName
from library.Utils import forceString, getPref, getPrefInt, forceDate, formatDate, getPrefDate, formatSex, getPrefString

from Reports.Report import CReport
from Reports.ReportBase import CReportBase, createTable
from Reports.Utils import dateRangeAsStr

from Ui_DiagnosisDispansPlanedList import Ui_DiagnosisDispansPlanedListDialog


def getQuery(params):
    db = QtGui.qApp.db
    table = db.table('ProphylaxisPlanning').alias('pp')
    tablePPT = db.table('rbProphylaxisPlanningType').alias('ppt')
    tableDiagnosis = db.table('Diagnosis')
    tableClient = db.table('Client')
    tablePerson = db.table('vrbPersonWithSpeciality')
    tableClientAttach = db.table('ClientAttach').alias('ca')

    begDate = params['begDate']
    endDate = params['endDate']
    personId = params['personId']
    MKBFilter = params.get('MKBFilter', 0)
    MKBFrom = params.get('MKBFrom', 'A00')
    MKBTo = params.get('MKBTo', 'Z99.9')
    noVisit = params.get('noVisit')

    socStatusClassId = params.get('socStatusClassId', None)
    socStatusTypeId = params.get('socStatusTypeId', None)
    orgStructureId = params.get('orgStructureId', None)
    specialityId = params.get('specialityId', None)
    attachOrgStructureId = params.get('attachOrgStructureId', None)

    cond = [table['deleted'].eq(0),
            table['parent_id'].isNotNull(),
            tablePPT['code'].eq(u'ДН'),
            tableClient['deathDate'].isNull(),
            ]

    if begDate and endDate:
        cond.append(db.joinOr([table['begDate'].between(begDate, endDate),
                               table['endDate'].between(begDate, endDate)]))

    if personId:
        cond.append(tableDiagnosis['dispanserPerson_id'].eq(personId))
    elif orgStructureId:
        cond.append(tablePerson['orgStructure_id'].inlist(getOrgStructureDescendants(orgStructureId)))
    else:
        cond.append(tablePerson['org_id'].eq(QtGui.qApp.currentOrgId()))
    if specialityId:
        cond.append(tablePerson['speciality_id'].eq(specialityId))

    if noVisit:
        cond.append(table['visit_id'].isNull())

    if MKBFilter == 1:
        cond.append(tableDiagnosis['MKB'].ge(MKBFrom))
        cond.append(tableDiagnosis['MKB'].le(MKBTo))

    if socStatusTypeId:
        subStmt = ('SELECT ClientSocStatus.id FROM ClientSocStatus WHERE '
                  +'ClientSocStatus.deleted=0 AND ClientSocStatus.client_id=Client.id AND '
                  +'ClientSocStatus.socStatusType_id=%d' % socStatusTypeId)
        cond.append('EXISTS('+subStmt+')')
    elif socStatusClassId:
        subStmt = ('SELECT ClientSocStatus.id FROM ClientSocStatus WHERE '
                  +'ClientSocStatus.deleted=0 AND ClientSocStatus.client_id=Client.id AND '
                  +'ClientSocStatus.socStatusClass_id=%d' % socStatusClassId)
        cond.append('EXISTS('+subStmt+')')

    if attachOrgStructureId:
        orgStructureList = getOrgStructureDescendants(attachOrgStructureId)
        cond.append(tableClientAttach['orgStructure_id'].inlist(orgStructureList))


    stmt = u"""
SELECT CONCAT_WS(' ', Client.lastName, Client.firstName, Client.patrName) AS clientName,
       Client.birthDate AS clientBirthDate,
       Client.sex AS clientSex,
       getClientContacts(Client.id) as contacts,
       coalesce(getClientLocAddress(Client.id), getClientRegAddress(Client.id)) as address,
       formatPersonName(Diagnosis.dispanserPerson_id) as personName,
       pp.MKB,
       Diagnosis.dispanserBegDate,
       (SELECT v.date
        FROM ProphylaxisPlanning pp2
        LEFT JOIN Visit v ON v.id = pp2.visit_id
        WHERE pp2.parent_id = pp.parent_id AND pp2.deleted = 0 AND pp2.visit_id IS NOT NULL
        AND pp2.begDate < pp.begDate
        ORDER BY v.date DESC LIMIT 1) AS lastVisitDate,
       CONCAT_WS(' - ', DATE_FORMAT(pp.begDate, '%d.%m.%Y'), DATE_FORMAT(pp.endDate, '%d.%m.%Y')) as curPeriod,
       Visit.date AS visitDate,
       (SELECT CONCAT_WS(' - ', DATE_FORMAT(pp3.begDate, '%d.%m.%Y'), DATE_FORMAT(pp3.endDate, '%d.%m.%Y'))
        FROM ProphylaxisPlanning pp3
        WHERE pp3.parent_id = pp.parent_id AND pp3.deleted = 0 AND pp3.begDate >= CURDATE()
        ORDER BY pp3.begDate ASC LIMIT 1) AS nextVisitDate
FROM ProphylaxisPlanning pp
LEFT JOIN rbProphylaxisPlanningType ppt ON ppt.id = pp.prophylaxisPlanningType_id
LEFT JOIN Client on Client.id = pp.client_id
left JOIN ClientAttach ca ON ca.id = (
              SELECT MAX(ClientAttach.id)
                    FROM ClientAttach
                    INNER JOIN rbAttachType ON rbAttachType.id = ClientAttach.attachType_id
                    WHERE client_id = Client.id
                      AND ClientAttach.deleted = 0
                      AND NOT rbAttachType.TEMPORARY)
INNER JOIN Diagnosis ON Diagnosis.id = (SELECT d.id FROM Diagnosis d 
                                       LEFT JOIN rbDispanser ON rbDispanser.id = d.dispanser_id
                                       WHERE d.MKB = pp.MKB
                                       AND d.`deleted`=0
                                       AND pp.client_id = d.client_id
                                       AND d.`mod_id` IS NULL
                                       AND rbDispanser.observed = 1
                                       ORDER BY d.id DESC LIMIT 1)
LEFT JOIN Visit ON Visit.id = pp.visit_id
LEFT JOIN vrbPersonWithSpeciality ON vrbPersonWithSpeciality.id = Diagnosis.dispanserPerson_id
WHERE {cond}
ORDER BY clientName""".format(cond=db.joinAnd(cond))
    return db.query(stmt)


class CDiagnosisDispansPlanedListDialog(QtGui.QDialog, Ui_DiagnosisDispansPlanedListDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.cmbSocStatusType.setTable('vrbSocStatusType', True)
        self.cmbOrgStructure.setOrgId(QtGui.qApp.currentOrgId())
        self.cmbOrgStructure.setValue(QtGui.qApp.currentOrgStructureId())
        self.cmbSpeciality.setTable('rbSpeciality', True)
        # self.cmbPerson.addNotSetValue()

    @pyqtSignature('QAbstractButton*')
    def on_buttonBox_clicked(self, button):
        buttonCode = self.buttonBox.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Ok:
            if not all([self.edtEndDate.date(), self.edtBegDate.date()]) or self.edtEndDate.date() < self.edtBegDate.date():
                QtGui.QMessageBox.information(self, u'Внимание', u'Необходимо указать корректный период!')
                return
            QtGui.QDialog.accept(self)
        elif buttonCode == QtGui.QDialogButtonBox.Cancel:
            self.close()

    def setTitle(self, title):
        self.setWindowTitle(title)

    def setParams(self, params):
        self.edtBegDate.setDate(params.get('begDate', QDate().currentDate()))
        self.edtEndDate.setDate(params.get('endDate', QDate().currentDate()))
        self.cmbOrgStructure.setValue(params.get('orgStructureId', None))
        self.cmbSpeciality.setValue(params.get('specialityId', None))
        self.cmbPerson.setValue(params.get('personId', None))
        MKBFilter = params.get('MKBFilter', 0)
        self.cmbMKBFilter.setCurrentIndex(MKBFilter if MKBFilter else 0)
        self.edtMKBFrom.setText(params.get('MKBFrom', 'A00'))
        self.edtMKBTo.setText(params.get('MKBTo', 'Z99.9'))
        self.cmbSocStatusClass.setValue(params.get('socStatusClassId', None))
        self.cmbSocStatusType.setValue(params.get('socStatusTypeId', None))
        self.cmbOrgStructureAttach.setValue(params.get('attachOrgStructureId', None))

    def params(self):
        result = {'begDate': self.edtBegDate.date(),
                  'endDate': self.edtEndDate.date(),
                  'orgStructureId': self.cmbOrgStructure.value(),
                  'specialityId': self.cmbSpeciality.value(),
                  'personId': self.cmbPerson.value(),
                  'MKBFilter': self.cmbMKBFilter.currentIndex(),
                  'MKBFrom': unicode(self.edtMKBFrom.text()),
                  'MKBTo': unicode(self.edtMKBTo.text()),
                  'socStatusClassId': self.cmbSocStatusClass.value(),
                  'socStatusTypeId': self.cmbSocStatusType.value(),
                  'attachOrgStructureId': self.cmbOrgStructureAttach.value()}
        return result

    @pyqtSignature('int')
    def on_cmbMKBFilter_currentIndexChanged(self, index):
        self.edtMKBFrom.setEnabled(index == 1)
        self.edtMKBTo.setEnabled(index == 1)

    @pyqtSignature('int')
    def on_cmbSocStatusClass_currentIndexChanged(self, index):
        socStatusClassId = self.cmbSocStatusClass.value()
        filter = ('class_id=%d' % socStatusClassId) if socStatusClassId else ''
        self.cmbSocStatusType.setFilter(filter)

    @pyqtSignature('int')
    def on_cmbOrgStructure_currentIndexChanged(self, index):
        orgStructureId = self.cmbOrgStructure.value()
        self.cmbPerson.setOrgStructureId(orgStructureId)

    @pyqtSignature('int')
    def on_cmbSpeciality_currentIndexChanged(self, index):
        specialityId = self.cmbSpeciality.value()
        self.cmbPerson.setSpecialityId(specialityId)



class CDiagnosisDispansPlanedListReport(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)                         
        self.setTitle(u'Отчет по запланированным на диспансерное наблюдение')

    def getSetupDialog(self, parent):
        result = CDiagnosisDispansPlanedListDialog(parent)
        result.edtBegDate.canBeEmpty(False)
        result.edtEndDate.canBeEmpty(False)
        result.setTitle(self.title())
        return result
    
    def getDefaultParams(self):
        prefs = getPref(QtGui.qApp.preferences.reportPrefs, self.title(), {})
        result = {'begDate': getPrefDate(prefs, 'begDate', QDate().currentDate()),
                  'endDate': getPrefDate(prefs, 'endDate', QDate().currentDate()),
                  'personId': getPrefInt(prefs, 'personId', None),
                  'MKBFilter': getPrefInt(prefs, 'MKBFilter', 0),
                  'MKBFrom': getPrefString(prefs, 'MKBFrom', 'A00'),
                  'MKBTo': getPrefString(prefs, 'MKBTo', 'Z99.9')}
        return result

    def dumpParams(self, cursor, params, align=CReportBase.AlignLeft):
        db = QtGui.qApp.db
        begDate = params['begDate']
        endDate = params['endDate']
        personId = params['personId']
        MKBFilter = params.get('MKBFilter', 0)
        MKBFrom = params.get('MKBFrom', '')
        MKBTo = params.get('MKBTo', '')
        socStatusClassId = params.get('socStatusClassId', None)
        socStatusTypeId = params.get('socStatusTypeId', None)
        orgStructureId = params.get('orgStructureId', None)
        specialityId = params.get('specialityId', None)
        attachOrgStructureId = params.get('attachOrgStructureId', None)

        description = [dateRangeAsStr(u'за период', begDate, endDate)]
        if orgStructureId:
            description.append(u'Подразделение: ' + getOrgStructureFullName(orgStructureId))
        else:
            description.append(u'Подразделение: ЛПУ')
        if specialityId:
            description.append(u'Специальность: ' + forceString(db.translate('rbSpeciality', 'id', specialityId, 'name')))
        if personId:
            personName = forceString(db.translate('vrbPersonWithSpeciality', 'id', personId, 'name'))
            description.append(u'врач: %s' % personName)
        if MKBFilter == 1:
            description.append(u'код МКБ с "%s" по "%s"' % (MKBFrom, MKBTo))
        elif MKBFilter == 2:
            description.append(u'код МКБ пуст')
        if socStatusTypeId:
            description.append(u'Тип соц.статуса: ' + forceString(db.translate('vrbSocStatusType', 'id', socStatusTypeId, 'name')))
        if socStatusClassId:
            description.append(u'Класс соц.статуса: ' + forceString(db.translate('rbSocStatusClass', 'id', socStatusClassId, 'name')))
        if attachOrgStructureId:
            description.append(u'Прикрепление к участку: ' + getOrgStructureFullName(attachOrgStructureId))
        columns = [('100%', [], CReportBase.AlignLeft)]
        table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
        for i, row in enumerate(description):
            table.setText(i, 0, row)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()

    def build(self, params):
        query = getQuery(params)

        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()

        tableColumns = [
            ('3%',  [u'№ п/п'], CReportBase.AlignLeft),
            ('12%', [u'ФИО пациента'], CReportBase.AlignLeft),
            ('5%', [u'Дата рождения'], CReportBase.AlignLeft),
            ('2%', [u'Пол'], CReportBase.AlignLeft),
            ('15%', [u'Телефон'], CReportBase.AlignLeft),
            ('15%', [u'Адрес'], CReportBase.AlignLeft),
            ('10%', [u'Врач'], CReportBase.AlignLeft),
            ('3%', [u'МКБ'], CReportBase.AlignLeft),
            ('5%', [u'Дата взятия на Д-учет'], CReportBase.AlignLeft),
            ('5%', [u'Дата предыдущей явки'], CReportBase.AlignLeft),
            ('10%',  [u'Запланированный период'], CReportBase.AlignLeft),
            ('5%', [u'Дата явки'], CReportBase.AlignLeft),
            ('10%',  [u'Период следующей явки'], CReportBase.AlignLeft)
        ]

        table = createTable(cursor, tableColumns)
        rowNumber = 0
        while query.next():
            record = query.record()
            row = table.addRow()
            rowNumber += 1
            table.setText(row, 0, rowNumber)
            table.setText(row, 1, forceString(record.value('clientName')))
            table.setText(row, 2, formatDate(record.value('clientBirthDate')))
            table.setText(row, 3, formatSex(record.value('clientSex')))
            table.setText(row, 4, forceString(record.value('contacts')))
            table.setText(row, 5, forceString(record.value('address')))
            table.setText(row, 6, forceString(record.value('personName')))
            table.setText(row, 7, forceString(record.value('MKB')))
            table.setText(row, 8, formatDate(forceDate(record.value('dispanserBegDate'))))
            table.setText(row, 9, formatDate(forceDate(record.value('lastVisitDate'))))
            table.setText(row, 10, forceString(record.value('curPeriod')))
            table.setText(row, 11, formatDate(forceDate(record.value('visitDate'))))
            table.setText(row, 12, forceString(record.value('nextVisitDate')))

        return doc


class CDiagnosisDispansNoVisitReport(CDiagnosisDispansPlanedListReport):
    def __init__(self, parent):
        CDiagnosisDispansPlanedListReport.__init__(self, parent)
        self.setTitle(u'Отчет по не явившимся на диспансерный осмотр')

    def build(self, params):
        params['noVisit'] = True
        query = getQuery(params)
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        tableColumns = [
            ('3%', [u'№ п/п'], CReportBase.AlignLeft),
            ('12%', [u'ФИО пациента'], CReportBase.AlignLeft),
            ('5%', [u'Дата рождения'], CReportBase.AlignLeft),
            ('2%', [u'Пол'], CReportBase.AlignLeft),
            ('15%', [u'Телефон'], CReportBase.AlignLeft),
            ('15%', [u'Адрес'], CReportBase.AlignLeft),
            ('10%', [u'Врач'], CReportBase.AlignLeft),
            ('3%', [u'МКБ'], CReportBase.AlignLeft),
            ('5%', [u'Дата взятия на Д-учет'], CReportBase.AlignLeft),
            ('5%', [u'Дата предыдущей явки'], CReportBase.AlignLeft),
            ('10%', [u'Запланированный период'], CReportBase.AlignLeft),
            ('10%', [u'Период следующей явки'], CReportBase.AlignLeft)
        ]
        table = createTable(cursor, tableColumns)
        rowNumber = 0
        while query.next():
            record = query.record()
            row = table.addRow()
            rowNumber += 1
            table.setText(row, 0, rowNumber)
            table.setText(row, 1, forceString(record.value('clientName')))
            table.setText(row, 2, formatDate(record.value('clientBirthDate')))
            table.setText(row, 3, formatSex(record.value('clientSex')))
            table.setText(row, 4, forceString(record.value('contacts')))
            table.setText(row, 5, forceString(record.value('address')))
            table.setText(row, 6, forceString(record.value('personName')))
            table.setText(row, 7, forceString(record.value('MKB')))
            table.setText(row, 8, formatDate(forceDate(record.value('dispanserBegDate'))))
            table.setText(row, 9, formatDate(forceDate(record.value('lastVisitDate'))))
            table.setText(row, 10, forceString(record.value('curPeriod')))
            table.setText(row, 11, forceString(record.value('nextVisitDate')))
        return doc
