# -*- coding: utf-8 -*-

from PyQt4 import QtGui

from Reports.Report import CReport, createTable
from Reports.ReportBase import CReportBase

from library.Utils import forceString, forceInt, forceDate
from EconomicAnalisysSetupDialog import CEconomicAnalisysSetupDialog
from EconomicAnalisys import getStmt, colClient, colEvent, colFinance, colContract, colEventSetDate, colEventExecDate, colServiceInfisName, colClientName


class CEconomicAnalisysE12(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Форма Э-12. Отчет по введенным услугам, отсутствующим в договоре')

    def selectData(self, params):
        cols = [colClient, colEvent, colFinance, colEventSetDate, colContract, colEventExecDate, colServiceInfisName, colClientName]
        colsStmt = u"""select colFinance as fin,
        colContract as contract,
        colServiceInfisName as code,
        colEvent as eventId,
        colEventSetDate as setDate,
        colEventExecDate as execDate,
        colClient as clientId,
        colClientName as person
        """
        groupCols = u''
        orderCols = u'colFinance, colContract, colServiceInfisName, colEventSetDate, colClientName'
        additionCond = u" and ct.id is null and rbService.infis REGEXP '^[ABGV][0-9]'"
        queryList = ['action']
        
        stmt = getStmt(colsStmt, cols, groupCols, orderCols, params, queryList, additionCond)

        return QtGui.qApp.db.query(stmt)

    def build(self, description, params):
        reportData = {}

        def processQuery(query):
            while query.next():
                record = query.record()
                finance = forceString(record.value('fin'))
                contract = forceString(record.value('contract'))
                code = forceString(record.value('code'))
                eventId = forceInt(record.value('eventId'))
                setDate = forceDate(record.value('setDate'))
                execDate = forceDate(record.value('execDate'))
                clientId = forceInt(record.value('clientId'))
                person = forceString(record.value('person'))

                reportLine = []
                reportLine.append(contract)
                reportLine.append(eventId)
                reportLine.append(setDate)
                reportLine.append(execDate)
                reportLine.append(clientId)
                reportLine.append(person)
                key = (finance, code)
                if key not in reportData:
                    reportData[key] = []
                reportData[key].append(reportLine)

        query = self.selectData(params)
        processQuery(query)

        # now text
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertText(description)
        cursor.insertBlock()

        tableColumns = [
            ('20%', [u'Код услуги/Договор'], CReportBase.AlignCenter),
            ('10%', [u'№ талона'], CReportBase.AlignLeft),
            ('10%', [u'Дата начала лечения'], CReportBase.AlignCenter),
            ('10%', [u'Дата окончания лечения'], CReportBase.AlignCenter),
            ('10%', [u'№ карты'], CReportBase.AlignCenter),
            ('25%', [u'Фамилия Имя Отчество'], CReportBase.AlignLeft)
            ]

        table = createTable(cursor, tableColumns)
        keys = reportData.keys()
        keys.sort()
        prevFinance = None

        for key in keys:
            if prevFinance != key[0]:
                prevFinance = key[0]
                row = table.addRow()
                table.setText(row, 0, u"Тип финансирования: %s" % key[0], CReportBase.TableHeader, CReportBase.AlignLeft)
                table.mergeCells(row, 0, 1, 5)
            row = table.addRow()
            table.setText(row, 0, u"    %s" % key[1], CReportBase.TableHeader, CReportBase.AlignLeft)
            table.mergeCells(row, 0, 1, 5)
            for contract, eventId, setDate, execDate, clientId, person in reportData[key]:
                row = table.addRow()
                table.setText(row, 0, contract)
                table.setText(row, 1, eventId)
                table.setText(row, 2, setDate.toString('dd.MM.yyyy'))
                table.setText(row, 3, execDate.toString('dd.MM.yyyy'))
                table.setText(row, 4, clientId)
                table.setText(row, 5, person)
        return doc


class CEconomicAnalisysE12Ex(CEconomicAnalisysE12):
    def exec_(self, accountIdList=None):
        self.accountIdList = accountIdList
        CEconomicAnalisysE12.exec_(self)

    def getSetupDialog(self, parent):
        result = CEconomicAnalisysSetupDialog(parent)
        result.setTitle(self.title())
        result.cbPrice.setChecked(False)
        result.cbPrice.setEnabled(False)
        result.shrink()
        result.loadPrefs()
        return result

    def build(self, params):
        params['accountIdList'] = self.accountIdList
        return CEconomicAnalisysE12.build(self, '\n'.join(self.getDescription(params)), params)
