# -*- coding: utf-8 -*-

from PyQt4 import QtGui

from Reports.Report import CReport, createTable
from Reports.ReportBase import CReportBase

from library.Utils import forceString, forceInt, forceDouble, forceDate
from EconomicAnalisysSetupDialog import CEconomicAnalisysSetupDialog
from EconomicAnalisys import (
    getStmt, colClient, colEvent, colParentOrgStructure, colOrgStructure, colClientName,
    colEventSetDate, colEventExecDate, colServiceInfis, colCSG, colPos, colObr, colSMP, colKD, colPD, colUET, colAmount,
    colSUM, colPerson, colExposedSum
)


class CEconomicAnalisysE19(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Э-19. Список услуг, оказанных пациентам')
        self.detailList = [u'отделениям', u'врачам']
        self.detailId = None
        self.accountIdList = None

    def selectData(self, params):
        self.detailId = params.get('detailTo', 0)
        detailCol = []
        detailColName = ''
        if self.detailId == 0:
            detailCol = [colParentOrgStructure, colOrgStructure]
            detailColName = u"concat(colParentOrgStructure,' - ',colOrgStructure)"
        elif self.detailId == 1:
            detailCol = [colPerson]
            detailColName = u"colPerson"
        cols = [colClient, colEvent, colClientName, colEventSetDate, colEventExecDate, colServiceInfis,
                colCSG, colPos, colObr, colSMP, colKD, colPD, colUET, colAmount, colSUM, colExposedSum]
        cols.extend(detailCol)
        colsStmt = u"""select
        %s as detailCol,
        colClient as clientId,
        colEvent as eventId,
        colClientName as fio,
        colEventSetDate as setDate,
        colEventExecDate as execDate,
        colServiceInfis as code,
        colAmount as amount,
        colCSG as mes,
        colPos as pos,
        colObr as obr,
        colUET as uet,
        colKD as kd,
        colPD as pd,
        colSMP as callambulance,
        IF(colPos = 0 and colCSG = 0 and colSMP = 0 and colObr = 0, colAmount, 0) as usl,
        colSUM as sum,
        colExposedSUM as exposedSum
        """ % detailColName
        groupCols = u''
        orderCols = u'%s, colClientName, colEventSetDate, colEventExecDate, colServiceInfis' % detailColName
        
        stmt = getStmt(colsStmt, cols, groupCols, orderCols, params)

        return QtGui.qApp.db.query(stmt)

    def build(self, params):
        needExposedSum = params.get('dataType', None) == 3
        reportRowSize = 10 if needExposedSum else 9

        reportData = {'keys': [],
                      'events': [],  
                      'total': {
                                'exposed': 0,
                                'mes': 0,
                                'uet': 0,
                                'kd': 0,
                                'pos': 0,
                                'usl': 0,
                                'sum': 0,
                                'exposedSum': 0,
                                }
                      }

        def processQuery(query):
            while query.next():
                record = query.record()
                detailCol = forceString(record.value('detailCol'))
                clientId = forceInt(record.value('clientId'))
                eventId = forceInt(record.value('eventId'))
                fio = forceString(record.value('fio'))
                setDate = forceDate(record.value('setDate'))
                execDate = forceDate(record.value('execDate'))
                code = forceString(record.value('code'))
                amount = forceInt(record.value('amount'))
                kd = forceInt(record.value('kd'))
                pd = forceInt(record.value('pd'))
                uet = forceDouble(record.value('uet'))
                sums = forceDouble(record.value('sum'))
                exposedSum = forceDouble(record.value('exposedSum'))
                mes = forceInt(record.value('mes'))
                pos = forceInt(record.value('pos'))
                usl = forceInt(record.value('usl'))
                exposed = 0

                if not detailCol:
                    detailCol = [u'Без подразделения', u'Без врача'][self.detailId]
                if detailCol not in reportData:
                    reportData[detailCol] = {}
                if detailCol not in reportData['keys']:
                    reportData['keys'].append(detailCol)

                if clientId not in reportData[detailCol]:
                    reportData[detailCol][clientId] = {'fio': fio, 'setDate': setDate, 'execDate': execDate}
                if 'keys' not in reportData[detailCol]:
                    reportData[detailCol]['keys'] = []
                if clientId not in reportData[detailCol]['keys']:
                    reportData[detailCol]['keys'].append(clientId)
                    
                if 'events' not in reportData[detailCol]:
                    reportData[detailCol]['events'] = []
                if eventId not in reportData[detailCol]['events']:
                    reportData[detailCol]['events'].append(eventId)
                    exposed = 1
                    
                if 'total' not in reportData[detailCol]:
                    reportData[detailCol]['total'] = {
                        'exposed': 0,
                        'mes': 0,
                        'uet': 0,
                        'kd': 0,
                        'pos': 0,
                        'usl': 0,
                        'sum': 0,
                        'exposedSum': 0,
                        }

                if reportData[detailCol][clientId]['setDate'] > setDate:
                    reportData[detailCol][clientId]['setDate'] = setDate

                if reportData[detailCol][clientId]['execDate'] < execDate:
                    reportData[detailCol][clientId]['execDate'] = execDate

                if 'usls' not in reportData[detailCol][clientId]:
                    reportData[detailCol][clientId]['usls'] = []

                reportData[detailCol][clientId]['usls'].append([code, amount, kd + pd, uet, sums, exposedSum])

                reportData[detailCol]['total']['exposed'] += exposed
                reportData[detailCol]['total']['mes'] += mes
                reportData[detailCol]['total']['uet'] += uet
                reportData[detailCol]['total']['kd'] += kd + pd
                reportData[detailCol]['total']['pos'] += pos
                reportData[detailCol]['total']['usl'] += usl
                reportData[detailCol]['total']['sum'] += sums
                reportData[detailCol]['total']['exposedSum'] += exposedSum
                reportData['total']['exposed'] += exposed
                reportData['total']['mes'] += mes
                reportData['total']['uet'] += uet
                reportData['total']['kd'] += kd + pd
                reportData['total']['pos'] += pos
                reportData['total']['usl'] += usl
                reportData['total']['sum'] += sums
                reportData['total']['exposedSum'] += exposedSum

        query = self.selectData(params)
        processQuery(query)

        # now text
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertText(u'по %s\n' % self.detailList[self.detailId])
        description = '\n'.join(self.getDescription(params))
        cursor.insertText(description)
        cursor.insertBlock()

        tableColumns = [
            ('10%',  [u'№ карты (ист. болезни)'], CReportBase.AlignCenter),
            ('15%',  [u'ФИО'], CReportBase.AlignCenter),
            ('10%',  [u'Период лечения', u'с'], CReportBase.AlignCenter),
            ('10%',  [u'', u'по'], CReportBase.AlignCenter),
            ('15%',  [u'Код услуги'], CReportBase.AlignCenter),
            ('10%',  [u'Кол-во услуг'], CReportBase.AlignCenter),
            ('10%',  [u'Кол-во койко-дней'], CReportBase.AlignCenter),
            ('10%',  [u'Кол-во УЕТ'], CReportBase.AlignCenter),
            ('5%',  [u'Сумма'], CReportBase.AlignCenter),
            ]
        if needExposedSum:
            tableColumns.append(('5%', [u'Выставленная сумма'], CReportBase.AlignRight))
        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 2, 1, 2)
        for i in range(reportRowSize):
            if i != 2 and i != 3:
                table.mergeCells(0, i, 2, 1)

        def drawTotal(totalTitle, table, total):
            originRow = table.addRow()
            table.setText(originRow, 0, totalTitle,  CReportBase.TableHeader,  CReportBase.AlignLeft)
            table.setText(originRow,  2,  u'кол-во персональных счетов:')
            table.mergeCells(originRow, 2, 1, 5)
            table.setText(originRow,  7,  total['exposed'])
            table.mergeCells(originRow, 7, 1, 2)
            pairs = [
                [u'кол-во стандартов:',  total['mes']],
                [u'кол-во койко-дней (дней лечения):',  total['kd']],
                [u'кол-во посещений:',  total['pos']],
                [u'кол-во простых услуг:',  total['usl']],
                [u'кол-во УЕТ:',  total['uet']],
                [u'сумма, р:',  total['sum']],
            ]
            if needExposedSum:
                pairs.append([u'выставленная сумма, р:',  total['exposedSum']])
            for title, val in pairs:
                row = table.addRow()
                table.setText(row,  2,  title)
                table.mergeCells(row, 2, 1, 5)
                table.setText(row,  7,  val)
                table.mergeCells(row, 7, 1, 2)

            table.mergeCells(originRow, 0, 7, 2)

        for osname in reportData['keys']:
            row = table.addRow()
            table.mergeCells(row, 0, 1, reportRowSize)
            table.setText(row, 0, osname,  CReportBase.TableHeader, CReportBase.AlignLeft)

            for clientId in reportData[osname]['keys']:
                originRow = table.addRow()

                table.setText(originRow, 0, clientId)
                table.setText(originRow, 1, reportData[osname][clientId]['fio'])
                table.setText(originRow, 2, reportData[osname][clientId]['setDate'].toString('yyyy-MM-dd'))
                table.setText(originRow, 3, reportData[osname][clientId]['execDate'].toString('yyyy-MM-dd'))
                firstRowWasSkipped = False
                for code, amount, kd, uet, sums, exposedSum in reportData[osname][clientId]['usls']:
                    if firstRowWasSkipped:
                        row = table.addRow()
                    else:
                        firstRowWasSkipped = True
                        row = originRow
                    table.setText(row, 4, code)
                    table.setText(row, 5, amount)
                    table.setText(row, 6, kd)
                    table.setText(row, 7, uet)
                    table.setText(row, 8, sums)
                    if needExposedSum:
                        table.setText(row, 9, exposedSum)
                mergeCnt = len(reportData[osname][clientId]['usls'])
                if not needExposedSum:
                    mergeCnt -= 1
                table.mergeCells(originRow, 0, mergeCnt, 1)
                table.mergeCells(originRow, 1, mergeCnt, 1)
                table.mergeCells(originRow, 2, mergeCnt, 1)
                table.mergeCells(originRow, 3, mergeCnt, 1)
            drawTotal(u'Итого по %s' % osname, table,  reportData[osname]['total'])
        drawTotal(u'Итого', table,  reportData['total'])
        return doc


class CEconomicAnalisysE19Ex(CEconomicAnalisysE19):
    def exec_(self, accountIdList=None):
        self.accountIdList = accountIdList
        CEconomicAnalisysE19.exec_(self)

    def getSetupDialog(self, parent):
        result = CEconomicAnalisysSetupDialog(parent)
        result.setDetailToVisible(True)
        result.setListDetailTo(self.detailList)
        result.setTitle(self.title())
        result.shrink()
        result.loadPrefs()
        return result

    def build(self, params):
        params['accountIdList'] = self.accountIdList
        return CEconomicAnalisysE19.build(self, params)
