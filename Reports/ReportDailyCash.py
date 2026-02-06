# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2013 Chuk&Gek and Vista Software. All rights reserved.
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
from PyQt4.QtCore import pyqtSignature, QDate

from library.Utils      import forceDouble, forceInt, forceRef, forceString, forceStringEx
from Reports.Report     import CReportEx
from Reports.ReportBase import CReportBase

from Reports.Ui_ReportPayersSetup import Ui_ReportPayersSetupDialog


def selectData(params):
    begDate                = params.get('begDate', None)
    endDate                = params.get('endDate', None)
    contractId             = params.get('contractId', None)
    isVAT                  = params.get('isVAT', False)
    servicesIsVAT          = params.get('servicesIsVAT', 0)
    db = QtGui.qApp.db
    tableAccount      = db.table('Account')
    tableContract     = db.table('Contract')
    tableAccountItem  = db.table('Account_Item')
    tableEvent        = db.table('Event')
    tableEventLocalContract = db.table('Event_LocalContract')
    tableOrganisation = db.table('Organisation')
    tableClient       = db.table('Client')
    tablePerson = db.table('Person')
    queryTable = tableAccount.innerJoin(tableContract, tableContract['id'].eq(tableAccount['contract_id']))
    queryTable = queryTable.leftJoin(tableAccountItem, tableAccountItem['master_id'].eq(tableAccount['id']))
    queryTable = queryTable.leftJoin(tableEvent, tableAccountItem['event_id'].eq(tableEvent['id']))
    queryTable = queryTable.leftJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
    queryTable = queryTable.leftJoin(tableEventLocalContract, tableEventLocalContract['master_id'].eq(tableEvent['id']))
    queryTable = queryTable.leftJoin(tableOrganisation, tableEventLocalContract['org_id'].eq(tableOrganisation['id']))
    queryTable = queryTable.leftJoin(tablePerson, tableEvent['createPerson_id'].eq(tablePerson['id']))
    cond = []
    if begDate:
        cond.append(tableAccountItem['date'].ge(begDate))
    if endDate:
        cond.append(tableAccountItem['date'].lt(endDate.addDays(1)))
    if contractId:
        cond.append(tableAccount['contract_id'].eq(contractId))
    cond = cond if cond else '1'
    fields = [tableContract['id'].alias('contractId'),
#              "CONCAT_WS(' ', Contract.`grouping`, Contract.`number`, DATE_FORMAT(Contract.`date`,\'%d:%m:%Y`\'), Contract.`resolution`) AS contractName",
              "CONCAT_WS(' ', Contract.`grouping`, Contract.`number`) AS contractName",
#              "CONCAT(Client.`lastName`, ' ', Client.`firstName`, ' ', Client.`patrName`, ' (', Client.id, ')') AS clientName",
              tableClient['id'].alias('clientId'),
              "CONCAT(Client.`lastName`, ' ', Client.`firstName`, ' ', Client.`patrName`) AS clientName",
              "IF((Event_LocalContract.id IS NOT NULL) AND ((LENGTH(Event_LocalContract.lastName) <> 0) OR (Event_LocalContract.org_id IS NOT NULL)), IF(LENGTH(Event_LocalContract.lastName) = 0, Organisation.shortName, CONCAT(Event_LocalContract.`lastName`, ' ', Event_LocalContract.`firstName`, ' ', Event_LocalContract.`patrName`)), CONCAT(Client.`lastName`, ' ', Client.`firstName`, ' ', Client.`patrName`)) AS payerName",
              tableEvent['externalId'].alias('eventExternalId'),
              tableAccount['id'].alias('accountId'),
              tableAccountItem['id'].alias('accountItemId'),
              tableAccountItem['amount'].alias('accountServicesAmount'),
              tableAccountItem['sum'].alias('accountSum'),
              tableAccountItem['refuseType_id'],
              "CONCAT(Person.`lastName`, ' ', Person.`firstName`,  ' ', Person.`patrName`) AS casirName"
             ]
    if isVAT:
        fields.append(tableAccountItem['VAT'])
    if servicesIsVAT == 1:
        cond.append(tableAccountItem['VAT'].eq(0))
    elif servicesIsVAT == 2:
        cond.append(tableAccountItem['VAT'].ne(0))
    order = [#tableContract['id'].name(),
             tableAccount['id'].name(),
             'clientName'
             ]
    stmt = db.selectStmt(queryTable, fields, cond, order)
    return db.query(stmt)


class CReportDailyCash(CReportEx):
    def __init__(self, parent):
        CReportEx.__init__(self, parent, title=u'Ежедневная книга кассира')
        self.table_columns = [
                        ('20%',
                        [u'Пациент, номер карты'], CReportBase.AlignRight),
                        ('20%',
                        [u'Плательщик'], CReportBase.AlignRight),
                        ('4%',
                        [u'Услуг'], CReportBase.AlignRight),
                        ('4%',
                        [u'Отказано'], CReportBase.AlignRight),
                        ('15%',
                        [u'Возврат, руб.'], CReportBase.AlignRight),
                        ('15%',
                        [u'Оплата, руб.'], CReportBase.AlignRight),
                        ('24%',
                        [u'Кассир'], CReportBase.AlignRight)
                       ]


    def getSetupDialog(self, parent):
        result = CReportDailyCashSetup(parent, self)
        result.setTitle(self.title())
        return result


    def getDescription(self, params):
        begDate                = params.get('begDate', None)
        endDate                = params.get('endDate', None)
        contractText           = params.get('contractText', None)
        contractId             = params.get('contractId', None)
        isVAT                  = params.get('isVAT', False)
        servicesIsVAT          = params.get('servicesIsVAT', 0)
        rows = []
        if begDate:
            rows.append(u'Начальная дата периода: %s'%forceString(begDate))
        if endDate:
            rows.append(u'Конечная дата периода: %s'%forceString(endDate))
        if contractId:
            rows.append(u'Договор: %s' % contractText)
        if servicesIsVAT:
            rows.append(u'Услуги %s' % ([u'без НДС', u'с НДС'][servicesIsVAT-1]))
        if servicesIsVAT:
            rows.append(u'Услуги %s' % ([u'без НДС', u'с НДС'][servicesIsVAT-1]))
        if isVAT:
            rows.append(u'Выводить колонку  НДС')
        return rows


    def buildInt(self, params, cursor):
        query = selectData(params)
        result = self.getReportData(query, params)
        isVAT = params.get('isVAT', False)
        shift = 0
        if params.get('printAccount', 0):
            self.addColumn(('8%', [u'Номер счета'], CReportBase.AlignRight), 0)
            shift += 1
        if params.get('printContract', 0):
            self.addColumn(('8%', [u'Номер договора'], CReportBase.AlignRight), 0)
            shift += 1
        if isVAT:
            self.addColumn(('15%', [u'В том числе НДС, руб.'], CReportBase.AlignRight), len(self.table_columns))
            shift += 1
        table = self.createTable(cursor)
        boldChars = QtGui.QTextCharFormat()
        boldChars.setFontWeight(QtGui.QFont.Bold)
        accounts = result.keys()
        accounts.sort()
        for accountId in accounts:
            clients = result[accountId].items()
            clients.sort(cmp = lambda i1, i2: (-1 if i1[1][1] < i2[1][1] else (0 if i1[1][1] == i2[1][1] else 1)))
            for (clientId, data) in clients:
                row = table.addRow()
                for i in xrange(shift+7):
                    table.setText(row, i, (unicode(round(result[accountId][clientId][i], 2))) if (isVAT and i in [shift+4, shift+5, shift+6]) or (not isVAT and i in [shift+4, shift+5]) else (unicode(result[accountId][clientId][i])))
        cursor.setCharFormat(CReportBase.TableTotal)
        if isVAT:
            shift -= 1
            shiftList = [shift+4, shift+5, shift+6]
        else:
            shiftList = [shift+4, shift+5]
        self.addSummary(table, result, shiftList, u"%.2f руб.")
        return result


    def addSummary(self, table, reportData, columns = [], format="%d"):
        def dict2Array(d):
            if type(d) == dict:
                array = [j for (i, j) in d.items()]
                d = []
                for elem in array:
                    (goodelem, subdict) = dict2Array(elem)
                    if subdict:
                        d = d + goodelem
                    else:
                        d = d + [goodelem, ]
                return (d, True)
            return (d, False)
        tableRow = table.addRow()
        table.setText(tableRow, 0, u'Итого:')
        (reportData, isdict) = dict2Array(reportData)
        rows = len(reportData)
        cols = len(reportData[0]) if rows else table.colCount()
        if len(columns) == 0:
            columns = xrange(1, cols)
        mincol = min(columns)
        table.mergeCells(tableRow, 0, 1, mincol)
        for i in columns:
            summa = sum([reportData[j][i] for j in xrange(rows)])
            table.setText(tableRow, i, format%(round(summa, 2)))


    def getReportData(self, query, params):
        printAccount  = params.get('printAccount', 0)
        printContract = params.get('printContract', 0)
        isVAT         = params.get('isVAT', False)
        result = {}
        while query.next():
            record = query.record()
            clientId = forceRef(record.value('clientId'))
            eventExternalId = forceRef(record.value('eventExternalId'))
            if not eventExternalId:
                eventExternalId = ''
            accountId = forceRef(record.value('accountId'))
            clientName = forceString(record.value('clientName'))
            payerName = forceString(record.value('payerName'))
            refuseTypeId = forceRef(record.value('refuseType_id'))
            accountServicesAmount = forceInt(record.value('accountServicesAmount'))
            accountSum = forceDouble(record.value('accountSum'))
            casirName = forceString(record.value('casirName'))
            if not accountId or not clientId:
                continue
            result.setdefault(accountId, dict())
            data = [clientName, payerName, 0, 0, 0, 0, casirName]
            if isVAT:
                data.append(0.0)
            if printAccount:
                data = [accountId, ] + data
            if printContract:
                data = [eventExternalId, ] + data
            result[accountId].setdefault(clientId, data)
            if refuseTypeId:
                result[accountId][clientId][printAccount + printContract + 3] += accountServicesAmount
                result[accountId][clientId][printAccount + printContract + 4] += accountSum
            else:
                result[accountId][clientId][printAccount + printContract + 2] += accountServicesAmount
                result[accountId][clientId][printAccount + printContract + 5] += accountSum
                if isVAT:
                    VAT = forceDouble(record.value('VAT'))
                    result[accountId][clientId][printAccount + printContract + 6] += ((accountSum/(100 + VAT))*VAT)
        return result


class CReportDailyCashSetup(QtGui.QDialog, Ui_ReportPayersSetupDialog):
    def __init__(self, parent, report):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self._report = report
        #self.cmbFinance.setTable('rbFinance', addNone=True)
        self.lblFinance.hide()
        self.cmbFinance.hide()
        #self.chkDetailContracts.hide()
        self.chkDetailContracts.setText(u'Выводить номер договора')
        self.lblClientOrganisation.hide()
        self.cmbClientOrganisation.hide()
        self.chkFreeInputWork.hide()
        self.edtFreeInputWork.hide()
        self.lblInsurer.hide()
        self.cmbInsurer.hide()
        #self.chkPrintPayerResult.hide()
        self.chkPrintPayerResult.setText(u'Выводить номер счета')


    def setTitle(self, title):
        self.setWindowTitle(title)


    def setParams(self, params):
        self.edtBegDate.setDate(params.get('begDate', QDate.currentDate()))
        self.edtEndDate.setDate(params.get('endDate', QDate.currentDate()))
        self.cmbContract.setValue(params.get('contractId', None))
        self.chkDetailContracts.setChecked(params.get('printContract', False))
        self.chkPrintPayerResult.setChecked(params.get('printAccount', False))
        self.cmbClientOrganisation.setValue(params.get('clientOrganisationId', None))
        self.cmbInsurer.setValue(params.get('insurerId'))
        self.chkFreeInputWork.setChecked(params.get('freeInputWork', False))
        self.edtFreeInputWork.setText(params.get('freeInputWorkValue', ''))
        self.chkIsVAT.setChecked(params.get('isVAT', False))
        self.cmbServicesIsVAT.setCurrentIndex(params.get('servicesIsVAT', 0))


    def params(self):
        params = {}
        params['contractId'] = self.cmbContract.value()
        params['contractText'] = forceString(self.cmbContract.currentText())
        params['begDate'] = self.edtBegDate.date()
        params['endDate'] = self.edtEndDate.date()
        params['printContract']  = self.chkDetailContracts.isChecked()
        params['printAccount'] = self.chkPrintPayerResult.isChecked()
        params['clientOrganisationId'] = self.cmbClientOrganisation.value()
        params['insurerId'] = self.cmbInsurer.value()
        params['freeInputWork'] = self.chkFreeInputWork.isChecked()
        params['freeInputWorkValue'] = forceStringEx(self.edtFreeInputWork.text())
        params['isVAT']  = self.chkIsVAT.isChecked()
        params['servicesIsVAT'] = forceInt(self.cmbServicesIsVAT.currentIndex())
        return params


    @pyqtSignature('QDate')
    def on_edtBegDate_dateChanged(self, date):
        self.cmbContract.setBegDate(date)


    @pyqtSignature('QDate')
    def on_edtEndDate_dateChanged(self, date):
        self.cmbContract.setEndDate(date)


    @pyqtSignature('int')
    def on_cmbFinance_currentChanged(self, index):
        financeId = self.cmbFinance.value()
        self.cmbContract.setFinanceId(financeId)


    @pyqtSignature('int')
    def on_cmbContract_currentChanged(self, index):
        contractId = self.cmbContract.value()
        self.chkDetailContracts.setEnabled(bool(contractId))
