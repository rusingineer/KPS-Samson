# -*- coding: utf-8 -*-

from PyQt4 import QtGui

from Reports.Report import CReport, createTable
from Reports.ReportBase import CReportBase

from library.Utils import forceString, forceInt
from EconomicAnalisysSetupDialog import CEconomicAnalisysSetupDialog
from EconomicAnalisys import getStmt, colInsurerCodeName, colEvent, colAge, colClientSex


class CEconomicAnalisysE26(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Форма Э-26. Сведения о численности застрахованных лиц обратившихся в организацию для оказания медицинской помощи.')

    def selectData(self, params):
        cols = [colInsurerCodeName, colEvent, colAge, colClientSex]
        colsStmt = u"""select colInsurerCodeName as insurer,
        count(distinct colEvent) as cnt,
        colAge as age,
        colClientSex as sex
        """
        groupCols = u'colInsurerCodeName, colAge, colClientSex'
        orderCols = u'colInsurerCodeName, colAge'

        stmt = getStmt(colsStmt, cols, groupCols, orderCols, params)

        db = QtGui.qApp.db
        return db.query(stmt)


    def build(self, description, params):

        reportData = {'keys': []}

        def processQuery(query):
            while query.next():
                record = query.record()
                insurer = forceString(record.value('insurer'))
                if not insurer:
                    insurer = u'Без страховщика'
                cnt = forceInt(record.value('cnt'))
                sex = forceInt(record.value('sex'))
                age = forceInt(record.value('age'))

                if insurer not in reportData['keys']:
                    reportData['keys'].append(insurer)

                reportline = reportData.setdefault(insurer,  {
                                    'total': 0,
                                    'grp1': {'m': 0, 'f': 0},
                                    'grp2': {'m': 0, 'f': 0},
                                    'grp3': {'m': 0, 'f': 0},
                                    'grp4': {'m': 0, 'f': 0},
                                })

                reportline['total'] += cnt
                #1-М, 2-Ж
                if 0 <= age <= 4:
                    if sex == 1:
                        reportline['grp1']['m'] += cnt
                    if sex == 2:
                        reportline['grp1']['f'] += cnt
                if 5 <= age <= 17:
                    if sex == 1:
                        reportline['grp2']['m'] += cnt
                    if sex == 2:
                        reportline['grp2']['f'] += cnt
                if (18 <= age <= 59) and sex == 1:
                    reportline['grp3']['m'] += cnt
                if (18 <= age <= 54) and sex == 2:
                    reportline['grp3']['f'] += cnt
                if age >= 60 and sex == 1:
                    reportline['grp4']['m'] += cnt
                if age >= 55 and sex == 2:
                    reportline['grp4']['f'] += cnt

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
            ('36%', [u'Число застрахованных лиц, чел.'], CReportBase.AlignCenter),
            ('8%', [u'В том числе по группам застрахованных лиц', u'Дети', u'0-4 лет', u'муж.'], CReportBase.AlignCenter),
            ('8%', ['', '', '', u'жен.'], CReportBase.AlignCenter),
            ('8%', ['', '', u'5-17 лет', u'муж.'], CReportBase.AlignCenter),
            ('8%', ['', '', '', u'жен.'], CReportBase.AlignCenter),
            ('8%', ['', u'Трудоспособный возраст', u'18-59 лет', u'муж.'], CReportBase.AlignCenter),
            ('8%', ['', '', u'18-54 лет', u'жен.'], CReportBase.AlignCenter),
            ('8%', ['', u'пенсионеры', u'60 лет и старше', u'муж.'], CReportBase.AlignCenter),
            ('8%', ['', '', u'55 лет и старше', u'жен.'], CReportBase.AlignCenter),
            ]

        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 4, 1)
        table.mergeCells(0, 1, 1, 8)
        table.mergeCells(1, 1, 1, 4)

        table.mergeCells(2, 1, 1, 2)
        table.mergeCells(2, 3, 1, 2)

        table.mergeCells(1, 5, 1, 2)
        table.mergeCells(1, 7, 1, 2)

        for insurer in reportData['keys']:
            row = table.addRow()
            table.mergeCells(row, 0, 1, 9)
            table.setText(row, 0, insurer,  blockFormat=CReportBase.AlignLeft, charFormat=CReportBase.TableHeader)
            i = 0
            row = table.addRow()
            for key in ['total', 'grp1',  'grp2',  'grp3',  'grp4']:
                if key == 'total':
                    table.setText(row, i, reportData[insurer][key])
                    i += 1
                else:
                    for key2 in ['m', 'f']:
                        table.setText(row, i, reportData[insurer][key][key2])
                        i += 1

        return doc


class CEconomicAnalisysE26Ex(CEconomicAnalisysE26):
    def exec_(self, accountIdList=None):
        self.accountIdList = accountIdList
        CEconomicAnalisysE26.exec_(self)

    def getSetupDialog(self, parent):
        result = CEconomicAnalisysSetupDialog(parent)
        result.setTitle(self.title())
        result.shrink()
        result.loadPrefs()
        return result

    def build(self, params):
        params['accountIdList'] = self.accountIdList
        return CEconomicAnalisysE26.build(self, '\n'.join(self.getDescription(params)), params)
