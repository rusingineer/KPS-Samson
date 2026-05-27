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

from Orgs.Utils import getOrgStructureFullName, getOrgStructureDescendants
from Reports.Ui_DispObservationPriorityListSetupDialog import Ui_DispObservationPriorityListSetupDialog
from library.Utils import forceString, getPref, formatDate, getPrefDate, formatSex, getPrefRef
from Reports.Report import CReport
from Reports.ReportBase import CReportBase, createTable


def getQuery(params):
    db = QtGui.qApp.db
    tableEvent = db.table('Event').alias('e')
    date = params['date']
    orgStructureId = params['orgStructureId']
    cond = [tableEvent['setDate'].ge(date)]
    if orgStructureId:
        orgStructList = ','.join(forceString(id) for id in getOrgStructureDescendants(orgStructureId))
        cond.append('o.id in ({0:s})'.format(orgStructList))

    stmt = u"""
SELECT CONCAT_WS(' ', c.lastName, c.firstName, c.patrName) AS clientName,
       c.birthDate AS clientBirthDate,
       c.sex AS clientSex,
       getClientContacts(c.id) as contacts,
       coalesce(getClientLocAddress(c.id), getClientRegAddress(c.id)) AS address,
       GROUP_CONCAT(DISTINCT cd.code) AS diagList,
       o.name as orgStructureName,
       (select max(e1.execDate) 
        FROM Event e1
        LEFT JOIN EventType et on et.id = e1.eventTYpe_id       
        LEFT JOIN rbEventTypePurpose etp on etp.id = et.purpose_id
        LEFT JOIN Diagnostic di ON e1.id = di.event_id AND di.deleted = 0 and di.diagnosisType_id in (1, 2)
        LEFT JOIN Diagnosis di1 ON di.diagnosis_id = di1.id AND di1.deleted = 0
        where e1.client_id = c.id and etp.purpose = 6
        and LOCATE(SUBSTRING(di1.MKB, 1, 3),  GROUP_CONCAT(DISTINCT cd.code), 1)>0 ) as dispDate
FROM Event e
LEFT JOIN Client c ON e.client_id = c.id
LEFT JOIN ClientAttach as Attach on Attach.id = (
                select max(Attach.id)
                from ClientAttach as Attach
                    left join rbAttachType as AttachType on AttachType.id = Attach.attachType_id
                where Attach.client_id = c.id
                    and Attach.deleted = 0
                    and AttachType.code in ('1', '2')
            )
LEFT JOIN OrgStructure o ON o.id = Attach.orgStructure_id
LEFT JOIN Diagnostic d ON e.id = d.event_id AND d.deleted = 0
LEFT JOIN rbDiagnosisType dt ON dt.id = d.diagnosisType_id
LEFT JOIN Diagnosis d1 ON d.diagnosis_id = d1.id AND d1.deleted = 0
INNER JOIN soc_comorbidDiagnosis cd ON cd.code LIKE CONCAT(d1.MKB, '%')
WHERE c.deleted = 0 AND e.deleted = 0 AND c.deathDate is NULL
      AND {cond}
GROUP BY e.client_id
HAVING COUNT(DISTINCT LEFT(d1.MKB,3)) >= 3 AND MAX(CASE WHEN cd.group_id IN (1,2,3) THEN 1 ELSE 0 END) = 1
ORDER BY orgStructureName, clientName, clientBirthDate""".format(cond=db.joinAnd(cond))
    return db.query(stmt)


class CDispObservationPriorityListReport(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Список лиц, приоритетных для проведения диспансерного наблюдения')

    def getSetupDialog(self, parent):
        result = CDispObservationPriorityListSetupDialog(parent)
        result.setTitle(self.title())
        return result

    def getDefaultParams(self):
        result = {}
        prefs = getPref(QtGui.qApp.preferences.reportPrefs, self.title(), {})
        result['date'] = getPrefDate(prefs, 'date', QDate().currentDate().addYears(-3))
        result['orgStructureId'] = getPrefRef(prefs, 'orgStructureId', None)
        return result

    def dumpParams(self, cursor, params, align=CReportBase.AlignLeft):
        date = params['date']
        orgStructureId = params['orgStructureId']
        description = [u'Начало периода c %s' % forceString(date)]
        if orgStructureId:
            description.append(u'Прикрепление: ' + getOrgStructureFullName(orgStructureId))
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
            ('30%', [u'ФИО пациента'], CReportBase.AlignLeft),
            ('7%', [u'Дата рождения'], CReportBase.AlignLeft),
            ('2%', [u'Пол'], CReportBase.AlignLeft),
            ('13%', [u'Телефон'], CReportBase.AlignLeft),
            ('28%', [u'Адрес'], CReportBase.AlignLeft),
            ('10%', [u'МКБ'], CReportBase.AlignLeft),
            ('7%', [u' Дата последней явки по ДН'], CReportBase.AlignLeft),
            ]

        table = createTable(cursor, tableColumns)
        rowNumber = 0
        lastOrgStructureName = None
        while query.next():
            record = query.record()
            orgStructureName = forceString(record.value('orgStructureName'))
            if lastOrgStructureName != orgStructureName:
                row = table.addRow()
                lastOrgStructureName = orgStructureName
                table.setText(row, 0, lastOrgStructureName)
                table.mergeCells(row, 0, 1, 8)
            row = table.addRow()
            rowNumber += 1
            table.setText(row, 0, rowNumber)
            table.setText(row, 1, forceString(record.value('clientName')))
            table.setText(row, 2, formatDate(record.value('clientBirthDate')))
            table.setText(row, 3, formatSex(record.value('clientSex')))
            table.setText(row, 4, forceString(record.value('contacts')))
            table.setText(row, 5, forceString(record.value('address')))
            table.setText(row, 6, forceString(record.value('diagList')))
            table.setText(row, 7, formatDate(record.value('dispDate')))

        return doc


class CDispObservationPriorityListSetupDialog(QtGui.QDialog, Ui_DispObservationPriorityListSetupDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)

    @pyqtSignature('QAbstractButton*')
    def on_buttonBox_clicked(self, button):
        buttonCode = self.buttonBox.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Ok:
            if not self.edtDate.date():
                QtGui.QMessageBox.information(self, u'Внимание', u'Необходимо указать дату!')
                return
            QtGui.QDialog.accept(self)
        elif buttonCode == QtGui.QDialogButtonBox.Cancel:
            self.close()

    def setTitle(self, title):
        self.setWindowTitle(title)

    def setParams(self, params):
        self.edtDate.setDate(QDate().currentDate().addYears(-3))
        self.cmbOrgStructure.setValue(params.get('orgStructureId', None))

    def params(self):
        result = {}
        result['date'] = self.edtDate.date()
        result['orgStructureId'] = self.cmbOrgStructure.value()
        return result
