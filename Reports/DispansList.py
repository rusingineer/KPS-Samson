# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2023 SAMSON Group. All rights reserved.
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

from Ui_DiagnosisDispans import Ui_DiagnosisDispansDialog


def getQuery(params):
    db = QtGui.qApp.db
    tableDiagnostic = db.table('Diagnostic')
    tableDiagnosis = db.table('Diagnosis')
    tableClient = db.table('Client')
    tablePerson = db.table('vrbPersonWithSpeciality')
    date = params['date']
    personId = params['personId']
    MKBFilter = params.get('MKBFilter', 0)
    MKBFrom = params.get('MKBFrom', 'A00')
    MKBTo = params.get('MKBTo', 'Z99.9')

    socStatusClassId = params.get('socStatusClassId', None)
    socStatusTypeId = params.get('socStatusTypeId', None)

    orgStructureId = params.get('orgStructureId', None)
    specialityId = params.get('specialityId', None)

    cond = ["rbDispanser.observed = 1",
            tableDiagnosis['deleted'].eq(0),
            tableClient['deathDate'].isNull(),
            tableDiagnosis['mod_id'].isNull()
            ]
    cond.append(u'''NOT EXISTS(SELECT DC.id
                              FROM Diagnostic AS DC
                              INNER JOIN rbDispanser AS rbDP ON rbDP.id = DC.dispanser_id
                              WHERE DC.diagnosis_id = Diagnosis.id AND DC.endDate <= %s AND DC.deleted = 0 AND rbDP.name LIKE '%s')
                       OR EXISTS(SELECT DC.id
                              FROM Diagnostic AS DC
                              INNER JOIN rbDispanser AS rbDP ON rbDP.id = DC.dispanser_id
                              WHERE DC.diagnosis_id = Diagnosis.id AND DC.endDate <= %s AND DC.deleted = 0 AND rbDP.name LIKE '%s')''' % (db.formatDate(date), u'%снят%', db.formatDate(date), u'%взят повторно%'))

    if date:
        cond.append(tableDiagnostic['endDate'].le(date))

    if personId:
        cond.append(tableDiagnosis['dispanserPerson_id'].eq(personId))
    elif orgStructureId:
        cond.append(tablePerson['orgStructure_id'].inlist(getOrgStructureDescendants(orgStructureId)))
    else:
        cond.append(tablePerson['org_id'].eq(QtGui.qApp.currentOrgId()))
    if specialityId:
        cond.append(tablePerson['speciality_id'].eq(specialityId))

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

    stmt = u"""
SELECT DISTINCT CONCAT_WS(' ', Client.lastName, Client.firstName, Client.patrName) AS clientName,
       Client.birthDate AS clientBirthDate,
       Client.sex AS clientSex,
       getClientContacts(Client.id) as contacts,
       coalesce(getClientLocAddress(Client.id), getClientRegAddress(Client.id)) as address,
       formatPersonName(Diagnosis.dispanserPerson_id) as personName,
       Diagnosis.MKB,
       Diagnosis.dispanserBegDate,
       (SELECT v.date
        FROM ProphylaxisPlanning pp2
        LEFT JOIN rbProphylaxisPlanningType ppt2 ON ppt2.id = pp2.prophylaxisPlanningType_id
        LEFT JOIN Visit v ON v.id = pp2.visit_id
        WHERE Diagnosis.MKB = pp2.MKB AND pp2.deleted = 0 AND pp2.client_id = Diagnosis.client_id
                                    AND pp2.parent_id IS NOT NULL AND pp2.visit_id IS NOT NULL
                                    AND ppt2.code = 'ДН'
        ORDER BY v.date DESC LIMIT 1) AS lastVisitDate,
       (SELECT CONCAT_WS(' - ', DATE_FORMAT(pp3.begDate, '%d.%m.%Y'), DATE_FORMAT(pp3.endDate, '%d.%m.%Y'))
        FROM ProphylaxisPlanning pp3
        LEFT JOIN rbProphylaxisPlanningType ppt3 ON ppt3.id = pp3.prophylaxisPlanningType_id
        WHERE Diagnosis.MKB = pp3.MKB AND pp3.deleted = 0 AND pp3.client_id = Diagnosis.client_id
                                    AND pp3.parent_id IS NOT NULL AND pp3.visit_id IS NULL
                                    AND (pp3.begDate >= CURDATE() OR pp3.endDate >= CURDATE())
                                    AND ppt3.code = 'ДН'
        ORDER BY pp3.begDate ASC LIMIT 1) AS nextVisitDate
FROM Diagnosis
LEFT JOIN Diagnostic ON Diagnostic.diagnosis_id = Diagnosis.id AND Diagnostic.deleted = 0
LEFT JOIN rbDispanser ON rbDispanser.ID = Diagnostic.dispanser_id
LEFT JOIN Client on Client.id = Diagnosis.client_id
LEFT JOIN vrbPersonWithSpeciality ON vrbPersonWithSpeciality.id = Diagnosis.dispanserPerson_id
WHERE {cond}
ORDER BY clientName""".format(cond=db.joinAnd(cond))
    return db.query(stmt)


class CDispansListDialog(QtGui.QDialog, Ui_DiagnosisDispansDialog):
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
            if not self.edtDate.date():
                QtGui.QMessageBox.information(self, u'Внимание', u'Необходимо указать дату!')
                return
            if not self.cmbOrgStructure.value() and not self.cmbPerson.value():
                QtGui.QMessageBox.information(self, u'Внимание', u'Необходимо выбрать подразделение или врача!')
                return
            QtGui.QDialog.accept(self)
        elif buttonCode == QtGui.QDialogButtonBox.Cancel:
            self.close()

    def setTitle(self, title):
        self.setWindowTitle(title)

    def setParams(self, params):
        self.edtDate.setDate(params.get('date', QDate().currentDate()))
        self.cmbOrgStructure.setValue(params.get('orgStructureId', None))
        self.cmbSpeciality.setValue(params.get('specialityId', None))
        self.cmbPerson.setValue(params.get('personId', None))
        MKBFilter = params.get('MKBFilter', 0)
        self.cmbMKBFilter.setCurrentIndex(MKBFilter if MKBFilter else 0)
        self.edtMKBFrom.setText(params.get('MKBFrom', 'A00'))
        self.edtMKBTo.setText(params.get('MKBTo', 'Z99.9'))
        self.cmbSocStatusClass.setValue(params.get('socStatusClassId', None))
        self.cmbSocStatusType.setValue(params.get('socStatusTypeId', None))

    def params(self):
        result = {}
        result['date'] = self.edtDate.date()
        result['orgStructureId'] = self.cmbOrgStructure.value()
        result['specialityId'] = self.cmbSpeciality.value()
        result['personId'] = self.cmbPerson.value()
        result['MKBFilter'] = self.cmbMKBFilter.currentIndex()
        result['MKBFrom'] = unicode(self.edtMKBFrom.text())
        result['MKBTo'] = unicode(self.edtMKBTo.text())
        result['socStatusClassId'] = self.cmbSocStatusClass.value()
        result['socStatusTypeId'] = self.cmbSocStatusType.value()
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


class CDispansListReport(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Отчет о состоящих на диспансерном наблюдении')

    def getSetupDialog(self, parent):
        result = CDispansListDialog(parent)
        result.setTitle(self.title())
        return result

    def getDefaultParams(self):
        result = {}
        prefs = getPref(QtGui.qApp.preferences.reportPrefs, self.title(), {})
        result['date'] = getPrefDate(prefs, 'date', QDate().currentDate())
        result['personId'] = getPrefInt(prefs, 'personId', None)
        result['MKBFilter'] = getPrefInt(prefs, 'MKBFilter', 0)  # 0-нет фильтра, 1-интервал, 2-нет кода
        result['MKBFrom'] = getPrefString(prefs, 'MKBFrom', 'A00')
        result['MKBTo'] = getPrefString(prefs, 'MKBTo', 'Z99.9')
        return result

    def dumpParams(self, cursor, params, align=CReportBase.AlignLeft):
        db = QtGui.qApp.db
        date = params['date']
        personId = params['personId']
        MKBFilter = params.get('MKBFilter', 0)
        MKBFrom = params.get('MKBFrom', '')
        MKBTo = params.get('MKBTo', '')
        socStatusClassId = params.get('socStatusClassId', None)
        socStatusTypeId = params.get('socStatusTypeId', None)
        orgStructureId = params.get('orgStructureId', None)
        specialityId = params.get('specialityId', None)

        description = [u'на дату %s' % forceString(date)]
        if orgStructureId:
            description.append(u'Подразделение: ' + getOrgStructureFullName(orgStructureId))
        else:
            description.append(u'Подразделение: ЛПУ')
        specialityId      = params.get('specialityId', None)
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
            ('3%', [u'№ п/п'], CReportBase.AlignLeft),
            ('12%', [u'ФИО пациента'], CReportBase.AlignLeft),
            ('5%', [u'Дата рождения'], CReportBase.AlignLeft),
            ('2%', [u'Пол'], CReportBase.AlignLeft),
            ('15%', [u'Телефон'], CReportBase.AlignLeft),
            ('15%', [u'Адрес'], CReportBase.AlignLeft),
            ('10%', [u'Врач'], CReportBase.AlignLeft),
            ('3%', [u'МКБ'], CReportBase.AlignLeft),
            ('5%', [u'Дата взятия на Д-учет'], CReportBase.AlignLeft),
            ('10%', [u'Запланированный период'], CReportBase.AlignLeft),
            ('5%', [u'Дата последней явки'], CReportBase.AlignLeft)
            ]
        cursor.beginEditBlock()
        table = createTable(cursor, tableColumns)
        if query.size():
            table.appendRows(query.size())
            row = 0
            while query.next():
                record = query.record()
                row += 1
                table.setText(row, 0, row)
                table.setText(row, 1, forceString(record.value('clientName')))
                table.setText(row, 2, formatDate(record.value('clientBirthDate')))
                table.setText(row, 3, formatSex(record.value('clientSex')))
                table.setText(row, 4, forceString(record.value('contacts')))
                table.setText(row, 5, forceString(record.value('address')))
                table.setText(row, 6, forceString(record.value('personName')))
                table.setText(row, 7, forceString(record.value('MKB')))
                table.setText(row, 8, formatDate(forceDate(record.value('dispanserBegDate'))))
                table.setText(row, 9, forceString(record.value('nextVisitDate')))
                table.setText(row, 10, formatDate(forceDate(record.value('lastVisitDate'))))
        cursor.endEditBlock()
        return doc
