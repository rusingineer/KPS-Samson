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
import os

from PyQt4 import QtGui
from PyQt4.QtCore import QDate, pyqtSignature, QDir

from Reports.Utils import dateRangeAsStr
from library import xlwt
from library.Utils import forceString, getPref, formatDate, getPrefDate, getPrefInt, getPrefBool, agreeNumberAndWord, \
    forceStringEx

from Reports.Report import CReport
from Reports.ReportBase import CReportBase, createTable

from Reports.Ui_DispReportSetup import Ui_DispReportSetupDialog


def getQuery(params):
    db = QtGui.qApp.db
    tableDiagnostic = db.table('Diagnostic').alias('d')
    tableClientAttach = db.table('ClientAttach').alias('Attach')
    cond = []

    begDate = params['begDate']
    endDate = params['endDate']
    ageFrom = params['ageFrom']
    ageTo = params['ageTo']
    hasAttachments = params['hasAttachments']
    considerWorkPost = params['considerWorkPost']
    considerWorkPostFilter = ''
    if begDate:
        cond.append(tableDiagnostic['endDate'].ge(begDate))
    if endDate:
        cond.append(tableDiagnostic['endDate'].le(endDate))
    if ageFrom <= ageTo:
        if ageFrom:
            cond.append("c.birthDate <= ADDDATE(%s, INTERVAL -%d year)" % (db.formatDate(endDate), ageFrom))
        if ageTo:
            cond.append("c.birthDate >= ADDDATE(%s, INTERVAL -%d year)" % (db.formatDate(endDate), ageTo))
    if hasAttachments:
        cond.append(tableClientAttach['id'].isNotNull())
    if considerWorkPost:
        considerWorkPostFilter = """and IFNULL(ClientWork.post, '') <> ''"""


    stmt = u"""
SELECT CONCAT_WS(' ', c.lastName, c.firstName, c.patrName) AS clientName,
       c.birthDate AS clientBirthDate,
       formatSNILS(c.SNILS) AS clientSnils, 
       getClientContacts(c.id) AS contacts,
       IF((ClientWork.org_id is not null or IFNULL(ClientWork.freeInput, '') <> '') {considerWorkPostFilter}, 1, 0) AS isWork,
       CASE WHEN ClientWork.org_id is NOT NULL {considerWorkPostFilter} THEN  o1.title
       ELSE IF(IFNULL(ClientWork.freeInput, '') <> '' {considerWorkPostFilter}, ClientWork.freeInput, '') END AS workPlace,
       d1.MKB AS diag,
       IFNULL(d2.observed, 0) AS observed,
       CASE WHEN d2.observed THEN IFNULL(s.name, '') ELSE '' END AS spec
FROM Event e
LEFT JOIN Client c ON e.client_id = c.id
LEFT JOIN ClientWork
    ON ClientWork.client_id = c.id
    AND ClientWork.id = (SELECT
        MAX(CW.id)
      FROM ClientWork AS CW
      WHERE CW.client_id = c.id
      AND CW.deleted = 0)
LEFT JOIN Organisation o1 ON ClientWork.org_id = o1.id
LEFT JOIN ClientAttach as Attach on Attach.id = (
                select max(Attach.id)
                from ClientAttach as Attach
                    left join rbAttachType as AttachType on AttachType.id = Attach.attachType_id
                where Attach.client_id = c.id
                    and Attach.deleted = 0
                    and AttachType.code in ('1', '2')
                    and Attach.endDate is null
            )
LEFT JOIN OrgStructure o ON o.id = Attach.orgStructure_id
LEFT JOIN Diagnostic d ON e.id = d.event_id AND d.deleted = 0
LEFT JOIN rbDiagnosisType dt ON dt.id = d.diagnosisType_id
LEFT JOIN Diagnosis d1 ON d.diagnosis_id = d1.id AND d1.deleted = 0
LEFT JOIN Person p ON p.id = d1.dispanserPerson_id
LEFT JOIN rbSpeciality s ON p.speciality_id = s.id
LEFT JOIN rbDispanser d2 ON d1.dispanser_id = d2.id
LEFT JOIN soc_DispNabMKB sd ON sd.code = d1.MKB
WHERE c.deleted = 0 AND e.deleted = 0 AND c.deathDate IS NULL
AND dt.code IN ('1', '9') 
AND (sd.code is NOT NULL OR d1.MKB LIKE 'E10%' OR d1.MKB LIKE 'E66%')
AND {cond}
GROUP BY e.client_id, d1.MKB, CASE WHEN d2.observed THEN IFNULL(s.name, '') ELSE '' END
ORDER BY clientName, clientBirthDate, d1.MKB""".format(considerWorkPostFilter=considerWorkPostFilter,cond=db.joinAnd(cond))
    return db.query(stmt)


class CDispReport(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Экспорт реестра пациентов с диагнозами ДН')

    def getSetupDialog(self, parent):
        result = CDispReportSetupDialog(parent)
        result.setTitle(self.title())
        return result

    def getDefaultParams(self):
        result = {}
        prefs = getPref(QtGui.qApp.preferences.reportPrefs, self.title(), {})
        result['begDate'] = getPrefDate(prefs, 'begDate', QDate(2020, 1, 1))
        result['endDate'] = getPrefDate(prefs, 'endDate', QDate().currentDate())
        result['ageFrom'] = getPrefInt(prefs, 'ageFrom', 18)
        result['ageTo'] = getPrefInt(prefs, 'ageTo', 150)
        result['hasAttachments'] = getPrefBool(prefs, 'hasAttachments', True)
        result['considerWorkPost'] = getPrefBool(prefs, 'considerWorkPost', True)
        return result

    def dumpParams(self, cursor, params, align=CReportBase.AlignLeft):
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        ageFrom = params.get('ageFrom', None)
        ageTo = params.get('ageTo', None)
        hasAttachments = params.get('hasAttachments', None)
        considerWorkPost = params.get('considerWorkPost', None)
        description = []
        description.append(dateRangeAsStr(u'за период', begDate, endDate))
        if ageFrom is not None and ageTo is not None and ageFrom <= ageTo:
            description.append(u'возраст: c %d по %d %s' % (ageFrom, ageTo, agreeNumberAndWord(ageTo, (u'год', u'года', u'лет'))))
        if hasAttachments:
            description.append(u'имеющие прикрепление')
        if considerWorkPost:
            description.append(u'учитывая наличие должности при определении места работы')
        columns = [('100%', [], CReportBase.AlignLeft)]
        table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
        for i, row in enumerate(description):
            table.setText(i, 0, row)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()

    def build(self, params):
        query = getQuery(params)
        workbook = xlwt.Workbook()
        pageNumber = 1
        sheet = workbook.add_sheet(u'ДН лист %s' % pageNumber)


        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)

        def printHeader(sheet, rowNumber):
            sheet.col(0).width = 256 * 5
            sheet.col(1).width = 256 * 50
            sheet.col(2).width = 256 * 70
            sheet.col(3).width = 256 * 12
            sheet.col(4).width = 256 * 15
            sheet.col(5).width = 256 * 70
            sheet.col(6).width = 256 * 10
            sheet.col(7).width = 256 * 50
            sheet.col(8).width = 256 * 10
            sheet.col(9).width = 256 * 10
            sheet.col(10).width = 256 * 50

            style = xlwt.Style.easyxf("align: horizontal center, wrap true; font: bold true, name Times New Roman, height 220; borders: top medium, bottom medium, left medium, right medium;")
            sheet.write(rowNumber, 0, u'№ п/п', style=style)
            sheet.write(rowNumber, 1, u'Наименование медицинской организации', style=style)
            sheet.write(rowNumber, 2, u'Ф.И.О.', style=style)
            sheet.write(rowNumber, 3, u'Дата рождения', style=style)
            sheet.write(rowNumber, 4, u'СНИЛС', style=style)
            sheet.write(rowNumber, 5, u'Контактный телефон', style=style)
            sheet.write(rowNumber, 6, u'Статус (1-работающий, 0-неработающий)', style=style)
            sheet.write(rowNumber, 7, u'Место работы', style=style)
            sheet.write(rowNumber, 8, u'Диагноз заболевания по МКБ-10', style=style)
            sheet.write(rowNumber, 9, u'Статус диспансерного наблюдения (1-состоит, 0-не состоит)', style=style)
            sheet.write(rowNumber, 10, u'Специальность врача', style=style)

        orgTitle = forceString(QtGui.qApp.db.translate('Organisation', 'id', QtGui.qApp.currentOrgId(), 'fullName'))
        rowsCount = query.size()
        rowNumber = 0
        if rowsCount:
            printHeader(sheet, rowNumber)
        style1 = xlwt.Style.easyxf("align: horizontal center; font: name Times New Roman; borders: top thin, bottom thin, left thin, right thin;")
        while query.next():
            record = query.record()
            rowNumber += 1
            if rowNumber == 65536:
                pageNumber += 1
                sheet = workbook.add_sheet(u'ДН лист %s' % pageNumber)
                rowNumber = 0
                printHeader(sheet, rowNumber)
                rowNumber += 1


            sheet.write(rowNumber, 0, rowNumber, style=style1)
            sheet.write(rowNumber, 1, orgTitle, style=style1)
            sheet.write(rowNumber, 2, forceString(record.value('clientName')), style=style1)
            sheet.write(rowNumber, 3, formatDate(record.value('clientBirthDate')), style=style1)
            sheet.write(rowNumber, 4, forceString(record.value('clientSnils')), style=style1)
            sheet.write(rowNumber, 5, forceString(record.value('contacts')), style=style1)
            sheet.write(rowNumber, 6, forceString(record.value('isWork')), style=style1)
            sheet.write(rowNumber, 7, forceString(record.value('workPlace')), style=style1)
            sheet.write(rowNumber, 8, forceString(record.value('diag')), style=style1)
            sheet.write(rowNumber, 9, forceString(record.value('observed')), style=style1)
            sheet.write(rowNumber, 10, forceString(record.value('spec')), style=style1)

        outDir = params.get('outDir', QtGui.qApp.getHomeDir())
        fileName = os.path.join(forceStringEx(outDir), u"Экспорт реестра пациентов с диагнозами ДН %s.xls" % unicode(QDate.currentDate().toString('dd_MM_yyyy')))
        workbook.save(fileName)

        cursor.insertBlock()
        cursor.insertText(u'Сформировано %s строк' % rowsCount)
        cursor.insertBlock()
        cursor.insertText(u'Путь к файлу %s' % fileName)

        return doc


class CDispReportSetupDialog(QtGui.QDialog, Ui_DispReportSetupDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)

    @pyqtSignature('QAbstractButton*')
    def on_buttonBox_clicked(self, button):
        buttonCode = self.buttonBox.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Ok:
            if not self.edtBegDate.date():
                QtGui.QMessageBox.information(self, u'Внимание', u'Необходимо указать дату начала периода!')
                return
            if not self.edtEndDate.date():
                QtGui.QMessageBox.information(self, u'Внимание', u'Необходимо указать дату окончания периода!')
                return
            QtGui.QDialog.accept(self)
        elif buttonCode == QtGui.QDialogButtonBox.Cancel:
            self.close()

    @pyqtSignature('')
    def on_btnSelectDir_clicked(self):
        path = QtGui.QFileDialog.getExistingDirectory(self,
                                                      u'Выберите директорий для сохранения файла выгрузки',
                                                      forceStringEx(self.edtDir.text()),
                                                      QtGui.QFileDialog.ShowDirsOnly)
        if forceString(path):
            self.edtDir.setText(QDir.toNativeSeparators(path))

    def setTitle(self, title):
        self.setWindowTitle(title)

    def setParams(self, params):
        self.edtBegDate.setDate(QDate(2020, 1, 1))
        self.edtEndDate.setDate(QDate().currentDate())
        self.edtAgeFrom.setValue(18)
        self.edtAgeTo.setValue(150)
        self.chkAttachment.setChecked(True)
        self.edtDir.setText(QtGui.qApp.getHomeDir())
        self.chkConsiderWorkPost.setChecked(True)

    def params(self):
        result = {}
        result['begDate'] = self.edtBegDate.date()
        result['endDate'] = self.edtEndDate.date()
        result['ageFrom'] = self.edtAgeFrom.value()
        result['ageTo'] = self.edtAgeTo.value()
        result['hasAttachments'] = self.chkAttachment.isChecked()
        result['outDir'] = forceStringEx(self.edtDir.text())
        result['considerWorkPost'] = self.chkConsiderWorkPost.isChecked()
        return result
