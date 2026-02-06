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
from PyQt4.QtCore import QDate

from library.Utils       import forceInt, forceDate, forceString, formatDate, forceBool, formatSNILS
from library.DialogBase  import CDialogBase
from Reports.Report      import CReport
from Reports.ReportBase  import CReportBase, createTable

from Ui_ReportEventCasesVerificationSetup import Ui_ReportEventCasesVerificationSetup

# Комбобокс "Тип медицинской помощи"
AID_TYPE_NOT_SET = 0
AID_TYPE_AMB = 1
AID_TYPE_STAT = 2


def selectData(params):
    db = QtGui.qApp.db
    tableEvent = db.table('Event')
    tablePerson = db.table('Person')
    tableEventType = db.table('EventType')
    tableMedicalAidType = db.table('rbMedicalAidType')
    tableEventExport = db.table('Event_Export')
    tableFinance = db.table('rbFinance')

    begDate = params.get('begDate')
    endDate = params.get('endDate')
    aidType = params.get('aidType')
    sendIEMK = params.get('sendIEMK')
    onlyOMC = params.get('onlyOMC')
    compareUsishCode = params.get('compareUsishCode')

    queryTable = tableEvent
    queryTable = queryTable.innerJoin(tablePerson, tableEvent['execPerson_id'].eq(tablePerson['id']))
    queryTable = queryTable.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
    queryTable = queryTable.innerJoin(tableMedicalAidType, tableEventType['medicalAidType_id'].eq(tableMedicalAidType['id']))
    if onlyOMC:
        queryTable = queryTable.leftJoin (tableFinance, tableEventType['finance_id'].eq(tableFinance['id']))
    if sendIEMK:
        queryTable = queryTable.leftJoin(tableEventExport, tableEventExport['master_id'].eq(tableEvent['id']))

    cond = [ tableEvent['deleted'].eq(0),
             tableEventType['deleted'].eq(0),
             tablePerson['deleted'].eq(0),
           ]
    if begDate:
        cond.append(tableEvent['setDate'].ge(begDate))
    if endDate:
        cond.append(tableEvent['setDate'].lt(endDate.addDays(1)))
    if onlyOMC:
        cond.append(tableFinance['code'].eq(2))
    if compareUsishCode:
        cond.append(tableEventType['usishCode'].inlist([str(i) for i in xrange(13)]))

    if aidType == AID_TYPE_AMB:
        cond.append(db.joinOr([
            tableMedicalAidType['name'].like(u'%амбулаторн%'),
            tableMedicalAidType['name'].like(u'%стоматолог%')]))
    elif aidType == AID_TYPE_STAT:
        cond.append(tableMedicalAidType['name'].like(u'%стационар%'))
    else:
        cond.append(db.joinOr([
            tableMedicalAidType['name'].like(u'%амбулаторн%'),
            tableMedicalAidType['name'].like(u'%стоматолог%'),
            tableMedicalAidType['name'].like(u'%стационар%')]))

    cols = [ tableEvent['externalId'],
             tableEvent['id'].alias('eventId'),
             tableEvent['setDate'],
             tablePerson['SNILS'],
             u"(%s) AS `isStat`" % tableMedicalAidType['name'].like(u'%стационар%'),
           ]
    if sendIEMK:
        cols.append(tableEventExport['success'])

    stmt = db.selectStmt(queryTable, cols, cond, order=tableEvent['id'].name())
    query = db.query(stmt)
    while query.next():
        record = query.record()
        result = {}
        eventId = forceInt(record.value('eventId'))
        externalId = forceInt(record.value('externalId'))
        result['medicalHistory'] = externalId if externalId != 0 else eventId
        result['setDate'] = forceDate(record.value('setDate'))
        result['SNILS'] = forceString(record.value('SNILS'))
        result['isStat'] = forceBool(record.value('isStat'))
        if sendIEMK:
            result['success'] = forceBool(record.value('success'))
        yield result


class CReportEventCasesVerification(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Отчет для сверки случаев обслуживания')


    def getSetupDialog(self, parent):
        result = CReportEventCasesVerificationSetupDialog(parent)
        result.setWindowTitle(self.title())
        return result


    def getDescription(self, params):
        rows = CReport.getDescription(self, params)
        aidType = params.get('aidType')
        if aidType:
            rows.append(u'Тип медицинской помощи: ' +
                (u'амбулаторный' if aidType == AID_TYPE_AMB else u'стационарный'))
        if params.get('sendIEMK'):
            rows.append(u'Передано в ИЭМК')
        if params.get('onlyOMC'):
            rows.append(u'Только ОМС')
        if params.get('compareUsishCode'):
            rows.append(u'Учитывать код ЕГИСЗ Типа События')
        return rows


    def build(self, params):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        sendIEMK = params.get('sendIEMK')
        hideHeader = params.get('hideHeader')
        if not hideHeader:
            cursor.setCharFormat(CReportBase.ReportTitle)
            cursor.insertText(self.title())
            cursor.insertBlock()
            self.dumpParams(cursor, params)
            cursor.insertBlock()

        tableColumns = [
            ('', [u'Номер истории болезни'],     CReportBase.AlignCenter),
            ('', [u'Дата открытия СМО'],         CReportBase.AlignCenter),
            ('', [u'Признак амбулаторного СМО'], CReportBase.AlignCenter),
            ('', [u'СНИЛС врача'],               CReportBase.AlignCenter),
        ]
        if sendIEMK:
            tableColumns.append(('', [u'Передано в ИЭМК'], CReportBase.AlignCenter))

        table = createTable(cursor, tableColumns)
        fmt = table.table.format()
        fmt.setWidth(QtGui.QTextLength(QtGui.QTextLength.PercentageLength, 100))
        table.table.setFormat(fmt)

        for rowdata in selectData(params):
            row = table.addRow()
            table.setText(row, 0, rowdata['medicalHistory'])
            table.setText(row, 1, formatDate(rowdata['setDate']))
            table.setText(row, 2, (u'Нет' if rowdata['isStat'] else u'Да'))
            if not rowdata['isStat']:
                table.setText(row, 3, formatSNILS(rowdata['SNILS']))
            if sendIEMK:
                table.setText(row, 4, (u'Передано' if rowdata['success'] else u'Не передано'))

        return doc



class CReportEventCasesVerificationSetupDialog(CDialogBase, Ui_ReportEventCasesVerificationSetup):
    def __init__(self, parent=None):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)


    def params(self):
        result = {}
        result['begDate'] = self.edtBegDate.date()
        result['endDate'] = self.edtEndDate.date()
        result['aidType'] = self.cmbAidType.currentIndex()
        result['sendIEMK'] = self.chkSendIEMK.isChecked()
        result['hideHeader'] = self.chkHideHeader.isChecked()
        result['compareUsishCode'] = self.chkCompareUsishCode.isChecked()
        result['onlyOMC'] = self.chkOnlyOMC.isChecked()
        return result


    def setParams(self, params):
        self.edtBegDate.setDate(params.get('begDate', QDate.currentDate()))
        self.edtEndDate.setDate(params.get('endDate', QDate.currentDate().addDays(1)))
        self.cmbAidType.setCurrentIndex(params.get('aidType', AID_TYPE_NOT_SET))
        self.chkSendIEMK.setChecked(params.get('sendIEMK', False))
        self.chkHideHeader.setChecked(params.get('hideHeader', False))

