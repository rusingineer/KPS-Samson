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

from PyQt4                import QtGui
from PyQt4.QtCore         import QDate

from library.Utils        import forceDate, forceInt, forceString
from Reports.Report       import CReport
from Reports.ReportBase   import CReportBase, createTable
from library.DialogBase   import CDialogBase
from library.DateEdit     import CDateEdit
from Reports.ReportView   import CPageFormat



def selectData(params):
    begDate = params.get('begDate', QDate())
    endDate = params.get('endDate', QDate())

    db = QtGui.qApp.db

    tableEvent = db.table('Event')
    tableClient = db.table('Client')
    tableDiagnostic = db.table('Diagnostic')
    tableDiagnosis = db.table('Diagnosis')
    tableMKB = db.table('MKB')

    queryTable = tableEvent
    queryTable = queryTable.innerJoin(tableClient, tableClient['id'].eq(tableEvent['client_id']))
    queryTable = queryTable.innerJoin(tableDiagnostic, tableDiagnostic['event_id'].eq(tableEvent['id']))
    queryTable = queryTable.innerJoin(tableDiagnosis, tableDiagnosis['id'].eq(tableDiagnostic['diagnosis_id']))
    queryTable = queryTable.innerJoin(tableMKB, tableDiagnosis['MKB'].eq(tableMKB['DiagID']))

    cond = [ tableEvent['deleted'].eq(0),
             tableClient['deleted'].eq(0),
             tableDiagnostic['deleted'].eq(0),
             tableDiagnosis['deleted'].eq(0),
             tableDiagnosis['MKB'].ge('C00.00'),
             tableDiagnosis['MKB'].le('C99.99'),
           ]
    if begDate:
        cond.append(tableDiagnostic['setDate'].ge(begDate))
    if endDate:
        cond.append(tableDiagnostic['setDate'].lt(endDate.addDays(1)))

    fields = [ tableDiagnosis['MKB'],
               'age(Client.birthDate, Diagnostic.setDate) AS `age`',
               tableClient['sex'],
               tableMKB['DiagName'],
               tableMKB['BlockName'],
               tableMKB['BlockID'],
             ]

    stmt = db.selectStmt(queryTable, fields, cond)
    query = db.query(stmt)
    while query.next():
        record = query.record()
        yield {'MKB': forceString(record.value('MKB')),
               'MKBName': forceString(record.value('DiagName')),
               'MKBBlock': forceString(record.value('BlockID')),
               'MKBBlockName': forceString(record.value('BlockName')),
               'age': forceInt(record.value('age')),
               'sex': forceInt(record.value('sex')),
              }




def buildData(params):
    def indexByAge(clientAge):
        if  0 <= clientAge <= 4:  return 0
        if  5 <= clientAge <= 9:  return 1
        if 10 <= clientAge <= 14: return 2
        if 15 <= clientAge <= 19: return 3
        if 20 <= clientAge <= 24: return 4
        if 25 <= clientAge <= 29: return 5
        if 30 <= clientAge <= 34: return 6
        if 35 <= clientAge <= 39: return 7
        if 40 <= clientAge <= 44: return 8
        if 45 <= clientAge <= 49: return 9
        if 50 <= clientAge <= 54: return 10
        if 55 <= clientAge <= 59: return 11
        if 60 <= clientAge <= 64: return 12
        if 65 <= clientAge <= 69: return 13
        if 70 <= clientAge <= 74: return 14
        if 75 <= clientAge <= 79: return 15
        if 80 <= clientAge <= 84: return 16
        if clientAge >= 85:       return 17
        return -1

    data = {}  # { MKBBlockName: { MKBBlock:str, diags: { MKB:str, male:list(int) female:list(int) } } }

    for row in selectData(params):
        if not data.has_key(row['MKBBlockName']):
            data[row['MKBBlockName']] = {'MKBBlock': row['MKBBlock'], 'diags': {}}
        diags = data[row['MKBBlockName']]['diags']

        if not diags.has_key(row['MKBName']):
            diags[row['MKBName']] = {'MKB':row['MKB'], 'male':[0]*19, 'female':[0]*19}
        diagnos = diags[row['MKBName']]

        diagnos['male' if row['sex']==1 else 'female'][indexByAge(row['age'])] += 1
        if 0 <= row['age'] <= 17:
            diagnos['male' if row['sex']==1 else 'female'][18] += 1

    return data



class CReportForm7_2000(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Форма 7 (Таблица 2000)')
        self.orientation = CPageFormat.Landscape


    def getSetupDialog(self, parent):
        result = CReportForm7_2000_SetupDialog(parent)
        result.setWindowTitle(self.title())
        return result


    def build(self, params):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(u'Сведения о впервые выявленных злокачественных новообразованиях (2000)')
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()

        tableColumns = [
            ('10%', [u'Нозологическая форма, локализация', '', '', '1'], CReportBase.AlignLeft),
            ('2%' , [u'Пол', '', '', '2'], CReportBase.AlignCenter),
            ('2%' , [u'№ стр', '', '', '3'], CReportBase.AlignCenter),
            ('6%' , [u'Код по МКБ-10', '', '', '4'], CReportBase.AlignCenter),
            ('4%' , [u'Число впервые в жизни выявленных злокачественных новообразований', u'Всего', '', '5'], CReportBase.AlignLeft),
            ('4%' , ['', u'В том числе в возрасте (лет)', '0-4', '6'], CReportBase.AlignRight),
            ('4%' , ['', '', '5-9'  , '7' ],   CReportBase.AlignRight),
            ('4%' , ['', '', '10-14', '8' ], CReportBase.AlignRight),
            ('4%' , ['', '', '15-19', '9' ], CReportBase.AlignRight),
            ('4%' , ['', '', '20-24', '10'], CReportBase.AlignRight),
            ('4%' , ['', '', '25-29', '11'], CReportBase.AlignRight),
            ('4%' , ['', '', '30-34', '12'], CReportBase.AlignRight),
            ('4%' , ['', '', '35-39', '13'], CReportBase.AlignRight),
            ('4%' , ['', '', '40-44', '14'], CReportBase.AlignRight),
            ('4%' , ['', '', '45-49', '15'], CReportBase.AlignRight),
            ('4%' , ['', '', '50-54', '16'], CReportBase.AlignRight),
            ('4%' , ['', '', '55-59', '17'], CReportBase.AlignRight),
            ('4%' , ['', '', '60-64', '18'], CReportBase.AlignRight),
            ('4%' , ['', '', '65-69', '19'], CReportBase.AlignRight),
            ('4%' , ['', '', '70-74', '20'], CReportBase.AlignRight),
            ('4%' , ['', '', '75-79', '21'], CReportBase.AlignRight),
            ('4%' , ['', '', '80-84', '22'], CReportBase.AlignRight),
            ('4%' , ['', '', u'85 и старше', '23'], CReportBase.AlignRight),
            ('4%' , ['', '', u'0-17 лет', '24'], CReportBase.AlignRight),
        ]

        table = createTable(cursor, tableColumns)
        table.mergeCells(0,4, 1,20)
        table.mergeCells(1,5, 1,19)

        charBold = QtGui.QTextCharFormat()
        charBold.setFontWeight(QtGui.QFont.Bold)

        N = 1  # № строки
        data = buildData(params)

        for blockName in sorted(data.keys()):
            blockTotalRow = table.addRow()
            table.setText(blockTotalRow, 0, blockName + u' — всего', charFormat=charBold)
            table.setText(blockTotalRow, 1, u'М', charFormat=charBold)
            table.setText(blockTotalRow, 2, N, charFormat=charBold)
            table.setText(blockTotalRow, 3, data[blockName]['MKBBlock'], charFormat=charBold)
            N += 1

            table.addRow()
            table.setText(blockTotalRow+1, 1, u'Ж', charFormat=charBold)
            table.setText(blockTotalRow+1, 2, N, charFormat=charBold)
            N += 1

            totalMale = [0] * 19
            totalFemale = [0] * 19

            for diag in sorted(data[blockName]['diags'].keys()):
                MKB = data[blockName]['diags'][diag]['MKB']
                male = data[blockName]['diags'][diag]['male']
                female = data[blockName]['diags'][diag]['female']

                row = table.addRow()
                table.setText(row, 0, diag)
                table.setText(row, 1, u'М')
                table.setText(row, 2, N)
                table.setText(row, 3, MKB)
                table.setText(row, 4, sum(male))
                for i,value in enumerate(male):
                    table.setText(row, 5+i, value)
                    totalMale[i] += value
                N += 1

                row = table.addRow()
                table.setText(row, 1, u'Ж')
                table.setText(row, 2, N)
                table.setText(row, 4, sum(female))
                for i,value in enumerate(female):
                    table.setText(row, 5+i, value)
                    totalFemale[i] += value
                N += 1

            table.setText(blockTotalRow, 4, sum(totalMale), charFormat=charBold)
            for i,value in enumerate(totalMale):
                table.setText(blockTotalRow, 5+i, value, charFormat=charBold)

            table.setText(blockTotalRow+1, 4, sum(totalFemale), charFormat=charBold)
            for i,value in enumerate(totalFemale):
                table.setText(blockTotalRow+1, 5+i, value, charFormat=charBold)

        return doc





class CReportForm7_2000_SetupDialog(CDialogBase):
    def __init__(self, parent=None):
        CDialogBase.__init__(self, parent)
        self.begDate = CDateEdit(self)
        self.endDate = CDateEdit(self)

        buttonBox = QtGui.QDialogButtonBox(self)
        buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel | QtGui.QDialogButtonBox.Ok)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        layout = QtGui.QGridLayout(self)
        layout.addWidget(QtGui.QLabel(u'Дата начала периода'), 0, 0)
        layout.addWidget(self.begDate, 0, 1)
        layout.addWidget(QtGui.QLabel(u'Дата окончания периода'), 1, 0)
        layout.addWidget(self.endDate, 1, 1)
        layout.addWidget(buttonBox, 2, 0, 1, 2)


    def setParams(self, params):
        self.begDate.setDate(params.get('begDate', QDate.currentDate()))
        self.endDate.setDate(params.get('endDate', QDate.currentDate()))


    def params(self):
        result = {}
        result['begDate'] = self.begDate.date()
        result['endDate'] = self.endDate.date()
        return result

