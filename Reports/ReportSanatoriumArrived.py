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

from library.Utils             import forceString
from library.DialogBase        import CDialogBase

from Reports.Report            import CReport
from Reports.ReportBase        import CReportBase, createTable
from Reports.ReportView        import CPageFormat
from Reports.Utils             import dateRangeAsStr


from Reports.Ui_ReportSanatoriumSetupDialog import Ui_ReportSanatoriumSetupDialog

def selectData(params, relative=False):
    begDate = params.get('begDate', QDate())
    endDate = params.get('endDate', QDate())

    db = QtGui.qApp.db
    tableAction        = db.table('Action')
    tableActionType    = db.table('ActionType')
    tableEvent        = db.table('Event')
    tableClient = db.table('Client')
    tableEventType = db.table('EventType')
    tableRbMedicalAidType = db.table('rbMedicalAidType')
    tableEventVoucher = db.table('Event_Voucher')
    tableOrganisation = db.table('Organisation')


    cond = [tableAction['deleted'].eq(0),
            tableActionType['deleted'].eq(0),
            tableActionType['flatCode'].eq('received'),
            tableAction['begDate'].ge(begDate),
            tableAction['begDate'].lt(endDate.addDays(1)),
            tableRbMedicalAidType['code'].eq(8)] #Санаторно-курортная
    if relative:
        cond.append(tableEvent['relative_id'].isNotNull())

# планом выполнения такого запроса не поделитесь?
    cols = [    u'''CONCAT_WS(' ', Event_Voucher.serial, Event_Voucher.number) AS voucher''',
                    u'''CONCAT_WS(' ', Client.lastName, Client.firstName, Client.patrName) AS name''',
                    u'''GETCLIENTREGADDRESS(Client.id) AS regAddress''',
                    u'''GETCLIENTLOCADDRESS(Client.id) AS locAddress''',
                    tableClient['birthDate'].alias('birthDate'),
                    u'''GETCLIENTDOCUMENT(Client.id) AS document''',
                    u'''(SELECT ClientDocument.date FROM ClientDocument WHERE ClientDocument.id = GETCLIENTDOCUMENTID(Client.id)) AS documentDate''',
                    u'''(SELECT Organisation.title FROM Organisation
                    LEFT JOIN ClientPolicy ON ClientPolicy.insurer_id = Organisation.id
                    WHERE ClientPolicy.id = GETCLIENTPOLICYID(Client.id, 1)) AS policyOrg''',
                    u'''(SELECT ClientPolicy.serial FROM ClientPolicy
                    WHERE ClientPolicy.id = GETCLIENTPOLICYID(Client.id, 1)) AS policySerial''',
                    u'''(SELECT ClientPolicy.number FROM ClientPolicy
                    WHERE ClientPolicy.id = GETCLIENTPOLICYID(Client.id, 1)) AS policyNumber''',
                    u'''(SELECT ClientPolicy.begDate FROM ClientPolicy
                    WHERE ClientPolicy.id = GETCLIENTPOLICYID(Client.id, 1)) AS policyBegDate''',
                    u'''(SELECT ClientPolicy.endDate FROM ClientPolicy
                    WHERE ClientPolicy.id = GETCLIENTPOLICYID(Client.id, 1)) AS policyEndDate''',
                    u'''kladr.getOKATOName(Organisation.OKATO) as district''',
                    tableOrganisation['title'].alias('relegate'),
                    tableEventVoucher['begDate'].alias('voucherBegDate'),
                    tableEventVoucher['endDate'].alias('voucherEndDate')
                ]

    queryTable = tableAction
    queryTable = queryTable.leftJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
    queryTable = queryTable.leftJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))
    if relative:
        queryTable = queryTable.leftJoin(tableClient, tableClient['id'].eq(tableEvent['relative_id']))
    else:
        queryTable = queryTable.leftJoin(tableClient, tableClient['id'].eq(tableEvent['client_id']))
    queryTable = queryTable.leftJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
    queryTable = queryTable.leftJoin(tableRbMedicalAidType, tableRbMedicalAidType['id'].eq(tableEventType['medicalAidType_id']))
    queryTable = queryTable.leftJoin(tableEventVoucher, tableEventVoucher['event_id'].eq(tableEvent['id']))
    queryTable = queryTable.leftJoin(tableOrganisation, tableOrganisation['id'].eq(tableEvent['relegateOrg_id']))


    stmt = db.selectStmt(queryTable, cols, cond)
    query = db.query(stmt)
    return query


class CReportSanatoriumArrived(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Журнал прибывших')
        self.orientation = CPageFormat.Landscape

    def getSetupDialog(self, parent):
        result = CReportSanatoriumSetupDialog(parent)
        result.setTitle(self.title())
        result.setObjectName(self.title())
        return result

    def dumpParams(self, cursor, params):
        self.params = params
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        description = []
        if begDate and endDate:
            description.append(dateRangeAsStr(u'', begDate, endDate))
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertBlock(CReportBase.AlignCenter)
        cursor.movePosition(QtGui.QTextCursor.End)
        columns = [ ('100%', [], CReportBase.AlignCenter)]
        table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
        for i, row in enumerate(description):
            table.setText(i, 0, row)
        cursor.movePosition(QtGui.QTextCursor.End)

    def build(self, params):
        showAddress = params.get('showAddress', 0)
        patronage = params.get('patronage', False)
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.setBlockFormat(CReportBase.AlignCenter)
        cursor.insertText(self.title())
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        tableColumns = [
                        ('5%', [u'№ п/п',  u''],  CReportBase.AlignLeft),
                        ('10%', [u'Номер путевки',  u''],             CReportBase.AlignLeft),
                        ('10%', [u'Фамилия Имя Отчество',  u''],         CReportBase.AlignLeft),
                        ('15%', [u'Адрес', u''],        CReportBase.AlignLeft),
                        ('5%', [u'Дата рождения',  u''],            CReportBase.AlignLeft),
                        ('15%', [u'Документ',  u'' ], CReportBase.AlignLeft),
                        ('10%', [u'Полис ОМС',  u'' ], CReportBase.AlignLeft),
                        ('10%', [u'Кем направлен', u'' ], CReportBase.AlignLeft),
                        ('10%', [u'Сроки пребывания', u'С даты' ], CReportBase.AlignLeft),
                        ('10%', [u'', u'По дату' ], CReportBase.AlignLeft),
                        ]
        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 2, 1)
        table.mergeCells(0, 1, 2, 1)
        table.mergeCells(0, 2, 2, 1)
        table.mergeCells(0, 3, 2, 1)
        table.mergeCells(0, 4, 2, 1)
        table.mergeCells(0, 5, 2, 1)
        table.mergeCells(0, 6, 2, 1)
        table.mergeCells(0, 7, 2, 1)
        table.mergeCells(0, 8, 1, 2)
        query = selectData(params)
        cnt = 1
        if query is None:
            return doc
        while query.next():
            record = query.record()
            voucher      = forceString(record.value('voucher'))
            name        = forceString(record.value('name'))
            regAddress        = forceString(record.value('regAddress'))
            locAddress        = forceString(record.value('locAddress'))
            birthDate        = forceString(record.value('birthDate'))
            document = forceString(record.value('document'))
            documentDate = forceString(record.value('documentDate'))
            policyOrg        = forceString(record.value('policyOrg'))
            policySerial        = forceString(record.value('policySerial'))
            policyNumber        = forceString(record.value('policyNumber'))
            policyBegDate        = forceString(record.value('policyBegDate'))
            policyEndDate        = forceString(record.value('policyEndDate'))
            relegate        = forceString(record.value('relegate'))
            district        = forceString(record.value('district'))
            voucherBegDate        = forceString(record.value('voucherBegDate'))
            voucherEndDate        = forceString(record.value('voucherEndDate'))

            i = table.addRow()
            table.setText(i, 0, cnt)
            cnt+=1
            table.setText(i, 1, voucher)
            table.setText(i, 2, name)
            if showAddress:
                table.setText(i, 3, locAddress)
            else:
                table.setText(i, 3, regAddress)
            table.setText(i, 4, birthDate)
            if document:
                table.setText(i, 5, u'%s выдан: %s'%(document, documentDate))
            else:
                table.setText(i, 5, u'')
            if policyNumber:
                table.setText(i, 6, u'%s %s %s c: %s по: %s'%(policyOrg, policySerial if policySerial else u'ЕП', policyNumber, policyBegDate, policyEndDate))
            else:
                table.setText(i, 6, u'')
            if relegate:
                table.setText(i, 7, u'%s %s р-н'%(relegate, district))
            else:
                table.setText(i, 7, u'')
            table.setText(i, 8, voucherBegDate)
            table.setText(i, 9, voucherEndDate)

        if patronage:
            queryPatronage = selectData(params, patronage)
            while queryPatronage.next():
                record = queryPatronage.record()
                voucher      = forceString(record.value('voucher'))
                name        = forceString(record.value('name'))
                regAddress        = forceString(record.value('regAddress'))
                locAddress        = forceString(record.value('locAddress'))
                birthDate        = forceString(record.value('birthDate'))
                document = forceString(record.value('document'))
                documentDate = forceString(record.value('documentDate'))
                policyOrg        = forceString(record.value('policyOrg'))
                policySerial        = forceString(record.value('policySerial'))
                policyNumber        = forceString(record.value('policyNumber'))
                policyBegDate        = forceString(record.value('policyBegDate'))
                policyEndDate        = forceString(record.value('policyEndDate'))
                relegate        = forceString(record.value('relegate'))
                district        = forceString(record.value('district'))
                voucherBegDate        = forceString(record.value('voucherBegDate'))
                voucherEndDate        = forceString(record.value('voucherEndDate'))

                i = table.addRow()
                table.setText(i, 0, cnt)
                cnt+=1
                table.setText(i, 1, u'%s (по уходу)'%voucher)
                table.setText(i, 2, name)
                if showAddress:
                    table.setText(i, 3, locAddress)
                else:
                    table.setText(i, 3, regAddress)
                table.setText(i, 4, birthDate)
                if document:
                    table.setText(i, 5, u'%s выдан: %s'%(document, documentDate))
                else:
                    table.setText(i, 5, u'')
                if policyNumber:
                    table.setText(i, 6, u'%s %s %s c: %s по: %s'%(policyOrg, policySerial if policySerial else u'ЕП', policyNumber, policyBegDate, policyEndDate))
                else:
                    table.setText(i, 6, u'')
                if relegate:
                    table.setText(i, 7, u'%s %s р-н'%(relegate, district))
                else:
                    table.setText(i, 7, u'')
                table.setText(i, 8, voucherBegDate)
                table.setText(i, 9, voucherEndDate)

        return doc


class CReportSanatoriumSetupDialog(CDialogBase, Ui_ReportSanatoriumSetupDialog):
    def __init__(self, parent=None):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        self.showAddressVisible = True
        self.patronageVisible = True
        self.showBirthDateVisible = False
        self.setShowBirthDateVisible(False)
        self.setBuildByVisible(False)


    def setBuildByVisible(self, value):
        self.isBuildByVisible = value
        self.lblBuildBy.setVisible(value)
        self.cmbBuildBy.setVisible(value)


    def showEndDateVisible(self, value):
        self.endDateVisible = value
        self.edtEndDate.setVisible(value)
        self.lblEndDate.setVisible(value)


    def setShowAddressVisible(self, value):
        self.showAddressVisible = value
        self.lblShowAddress.setVisible(value)
        self.cmbShowAddress.setVisible(value)


    def setPatronageVisible(self, value):
        self.patronageVisible = value
        self.chkPatronage.setVisible(value)


    def setShowBirthDateVisible(self, value):
        self.showBirthDateVisible = value
        self.chkShowBirthDate.setVisible(value)


    def setTitle(self, title):
        self.setWindowTitle(title)


    def setParams(self, params):
        self.edtBegDate.setDate(params.get('begDate', QDate.currentDate()))
        self.edtEndDate.setDate(params.get('endDate', QDate.currentDate()))
        if self.showAddressVisible:
            self.cmbShowAddress.setCurrentIndex(params.get('showAddress', 0))
        if self.patronageVisible:
            self.chkPatronage.setChecked(params.get('patronage', False))
        if self.showBirthDateVisible:
            self.chkShowBirthDate.setChecked(params.get('showBirthDate', False))
        if self.isBuildByVisible:
            self.cmbBuildBy.setCurrentIndex(params.get('buildBy', 0))


    def params(self):
        result = {}
        result['begDate'] = self.edtBegDate.date()
        result['endDate'] = self.edtEndDate.date()
        if self.showAddressVisible:
            result['showAddress'] = self.cmbShowAddress.currentIndex()
        if self.patronageVisible:
            result['patronage'] = self.chkPatronage.isChecked()
        if self.showBirthDateVisible:
            result['showBirthDate'] = self.chkShowBirthDate.isChecked()
        if self.isBuildByVisible:
            result['buildBy'] = self.cmbBuildBy.currentIndex()
        return result

