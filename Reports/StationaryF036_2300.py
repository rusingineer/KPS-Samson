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

import re
from PyQt4 import QtGui
from PyQt4.QtCore import QDate

from library.Utils             import forceInt, forceDate, forceString, forceBool
from library.DialogBase        import CDialogBase
from Reports.Report            import CReport
from Reports.ReportBase        import CReportBase, createTable
from Reports.ReportView        import CPageFormat
from library.DateEdit          import CDateEdit


def mapClientsData(query):
    clientsData = {}
    while (query.next()):
        rec = query.record()
        clientId = forceInt(rec.value('clientId'))
        data = {}
        data['flatCode'] = forceString(rec.value('flatCode'))
        data['endDate'] = forceDate(rec.value('endDate'))
        data['MKB'] = forceString(rec.value('MKB'))
        data['clientAge'] = forceInt(rec.value('clientAge'))
        data['isFirstInLife'] = forceBool(rec.value('isFirstInLife'))
        data['isInvoluntarily'] = forceBool(rec.value('isInvoluntarily'))

        if not clientsData.has_key(clientId):
            clientsData[clientId] = []
        clientsData[clientId].append(data)

    return clientsData


def selectData(params):
    db = QtGui.qApp.db
    tableEvent = db.table('Event')
    tableAction = db.table('Action')
    tableAT = db.table('ActionType')
    tableClient = db.table('Client')
    tableDiagnostic = db.table('Diagnostic')
    tableDiagnosis = db.table('Diagnosis')

    begDate = params.get('begDate')
    endDate = params.get('endDate')

    queryTable = tableEvent
    queryTable = queryTable.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
    queryTable = queryTable.innerJoin(tableAction, tableAction['event_id'].eq(tableEvent['id']))
    queryTable = queryTable.innerJoin(tableAT, tableAction['actionType_id'].eq(tableAT['id']))
    queryTable = queryTable.innerJoin(tableDiagnostic, tableDiagnostic['event_id'].eq(tableEvent['id']))
    queryTable = queryTable.innerJoin(tableDiagnosis, tableDiagnostic['diagnosis_id'].eq(tableDiagnosis['id']))

    cols = [ tableClient['id'].alias('clientId'),
             tableAT['flatCode'],
             tableAction['endDate'],
             tableDiagnosis['MKB'],
             'age(%s,%s) as `clientAge`' % (tableClient['birthDate'], tableAction['endDate']),

             u'''(SELECT (APS.`value` = 'Да')
             FROM ActionProperty_String APS
                 JOIN ActionProperty AP ON AP.id = APS.id
                 JOIN ActionPropertyType APT ON AP.type_id = APT.id
             WHERE AP.action_id = %s
                 AND AP.deleted = 0
                 AND APT.deleted = 0
                 AND APT.name = 'Поступает впервые в жизни'
             ) AS `isFirstInLife`''' % tableAction['id'],

             u'''(SELECT (APS.`value` = 'Да')
             FROM ActionProperty_String APS
                 JOIN ActionProperty AP ON AP.id = APS.id
                 JOIN ActionPropertyType APT ON AP.type_id = APT.id
             WHERE AP.action_id = %s
                 AND AP.deleted = 0
                 AND APT.deleted = 0
                 AND APT.name = 'Поступление по ст.29'
             ) AS `isInvoluntarily`''' % tableAction['id'],
           ]

    cond = [ tableEvent['deleted'].eq(0),
             tableAction['deleted'].eq(0),
             tableAT['deleted'].eq(0),
             tableClient['deleted'].eq(0),
             tableDiagnosis['deleted'].eq(0),
             tableDiagnostic['deleted'].eq(0),
             tableAT['flatCode'].inlist(['leaved', 'received']),
           ]
    if begDate:
        cond.append(tableAction['endDate'].ge(begDate))
    if endDate:
        cond.append(tableAction['endDate'].lt(endDate.addDays(1)))

    stmt = db.selectDistinctStmt(queryTable, cols, cond)
    query = db.query(stmt)
    return mapClientsData(query)



class CStationaryF036_2300(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Состав пациентов, больных психическими расстройствами (2300)')
        self.orientation = CPageFormat.Landscape


    def getSetupDialog(self, parent):
        result = CStationaryF036_2300_SetupDialog(parent)
        result.setWindowTitle(self.title())
        return result


    def getRowData(self, rowMKBFilter):
        received = 0
        receivedAge0_14 = 0
        receivedAge15_17 = 0
        receivedFirstInPeriod = 0
        receivedFirstInLife = 0
        receivedInvoluntarily = 0
        leaved = 0
        bedDays = 0
        inStat = 0
        inStatAge0_14 = 0
        inStatAge15_17 = 0

        for (clientId, dataList) in self.clientsData.items():
            dataList = filter(lambda i: rowMKBFilter(i['MKB']), dataList)
            if not dataList:
                continue

            try:
                maxLeavedDay = max([i['endDate'].toJulianDay() for i in dataList if i['flatCode'] == 'leaved'])
                minReceivedDay = min([i['endDate'].toJulianDay() for i in dataList if i['flatCode'] == 'received'])
            except ValueError:
                maxLeavedDay = 0
                minReceivedDay = 0
            bedDays += maxLeavedDay - minReceivedDay

            hasLeavedAction = any([i['flatCode'] == 'leaved' for i in dataList])

            receivedActionsCount = [i['flatCode'] == 'received' for i in dataList].count(True)
            if receivedActionsCount == 1:
                receivedFirstInPeriod += 1

            clientNotLeaved = receivedActionsCount > 0 and not hasLeavedAction
            if clientNotLeaved:
                inStat += 1

            for data in dataList:
                if data['flatCode'] == 'received':
                    received += 1
                    if 0 <= data['clientAge'] <= 14:
                        if clientNotLeaved:
                            inStatAge0_14 += 1
                        receivedAge0_14 += 1
                    elif 15 <= data['clientAge'] <= 17:
                        if clientNotLeaved:
                            inStatAge15_17 += 1
                        receivedAge15_17 += 1

                    if data['isFirstInLife']:
                        receivedFirstInLife += 1
                    if data['isInvoluntarily']:
                        receivedInvoluntarily += 1

                elif data['flatCode'] == 'leaved':
                    leaved += 1

        return [received, receivedAge0_14, receivedAge15_17, receivedFirstInPeriod,
                receivedFirstInLife, receivedInvoluntarily, leaved, bedDays,
                inStat, inStatAge0_14, inStatAge15_17,
               ]


    def build(self, params):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(u'Состав пациентов, больных психическими расстройствами, получивших медицинскую помощь в стационарных условиях')
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()

        tableColumns = [
            ('9%', [u'наименование', '', '', ''], CReportBase.AlignLeft),
            ('7%', [u'Код по МКБ-10(класс V, адаптированный для использования в РФ)', '', '', ''], CReportBase.AlignLeft),
            ('7%', [u'№ стр.', '', '', ''], CReportBase.AlignCenter),
            ('7%', [u'В отчетном периоде', u'поступило пациентов', u'всего', ''], CReportBase.AlignRight),
            ('7%', ['', '', u'из них детей', u'0-14 лет включительно'], CReportBase.AlignRight),
            ('7%', ['', '', '', u'15-17 лет'], CReportBase.AlignRight),
            ('7%', ['', u'из них поступило (из гр. 4)', u'впервые в данном периоде', ''], CReportBase.AlignRight),
            ('7%', ['', '', u'впервые в жизни', ''], CReportBase.AlignRight),
            ('7%', ['', '', u'недобровольно, соответственно ст.29', ''], CReportBase.AlignRight),
            ('7%', ['', u'выбыло пациентов', '', ''], CReportBase.AlignRight),
            ('7%', ['', u'число койко-дней, проведенных в стационаре выписанными и умершими', '', ''], CReportBase.AlignRight),
            ('7%', [u'Состоит на конец периода', u'всего', '', ''], CReportBase.AlignRight),
            ('7%', ['', u'из них детей', u'0-14 лет включительно', ''], CReportBase.AlignRight),
            ('7%', ['', '', u'15-17 лет', ''], CReportBase.AlignRight),
        ]

        table = createTable(cursor, tableColumns)
        row = table.addRow()
        for i in xrange(len(tableColumns)):
            table.setText(row, i, str(i+1), blockFormat=CReportBase.AlignCenter)

        table.mergeCells(0,0, 4,1)
        table.mergeCells(0,1, 4,1)
        table.mergeCells(0,2, 4,1)
        table.mergeCells(0,3, 1,8)
        table.mergeCells(0,11, 1,3)
        table.mergeCells(1,3, 1,3)
        table.mergeCells(1,6, 1,3)
        table.mergeCells(1,9, 3,1)
        table.mergeCells(1,10, 3,1)
        table.mergeCells(1,11, 3,1)
        table.mergeCells(1,12, 1,2)
        table.mergeCells(2,3, 2,1)
        table.mergeCells(2,4, 1,2)
        table.mergeCells(2,6, 2,1)
        table.mergeCells(2,7, 2,1)
        table.mergeCells(2,8, 2,1)
        table.mergeCells(2,12, 2,1)
        table.mergeCells(2,13, 2,1)

        self.clientsData = selectData(params)

        def insertRowTitle(row, rowName, rowMKB):
            table.setText(row, 0, rowName)
            table.setText(row, 1, rowMKB)
            table.setText(row, 2, row-4)

        def insertRowData(row, rowMKBFilter):
            for (i,data) in enumerate(self.getRowData(rowMKBFilter)):
                table.setText(row, 3+i, data)

        def insertRowDataAndAdd(row, sum, rowMKBFilter):
            for (i,data) in enumerate(self.getRowData(rowMKBFilter)):
                table.setText(row, 3+i, data)
                sum[i] += data

        sumPsychosis = [0] * 11
        sumNonPsychotic = [0] * 11

        row = table.addRow()
        insertRowTitle(row, u'Психические расстройства - всего', 'F00-F09, F20-F99')
        insertRowData(row, lambda d: 'F00' <= d <= 'F09' or 'F20' <= d <= 'F99')

        rowPsychosis = table.addRow()
        insertRowTitle(rowPsychosis, u'Психозы и состояния слабоумия', '')

        row = table.addRow()
        insertRowTitle(row, u'в том числе: органические психозы и (или) слабоумие', u'F00-F05, F06 (часть), F09')
        insertRowDataAndAdd(row, sumPsychosis, lambda d:('F00'<=d<='F05') or ('F06.0'<=d<='F06.2') or ('F06.30'<=d<='F06.33') or d in ('F09','F06.81','F06.91'))

        row = table.addRow()
        insertRowTitle(row, u'из них: сосудистая деменция', 'F01')
        insertRowData(row, lambda d: d == 'F01')

        row = table.addRow()
        insertRowTitle(row, u'другие формы старческого слабоумия', 'F00, F02.0, F02.2-3, F03')
        insertRowData(row, lambda d: d in ('F00', 'F02.0', 'F03') or 'F02.2' <= d <= 'F02.3')

        row = table.addRow()
        insertRowTitle(row, u'шизофрения', 'F20')
        insertRowDataAndAdd(row, sumPsychosis, lambda d: d == 'F20')

        row = table.addRow()
        insertRowTitle(row, u'шизотипические расстройства', 'F21')
        insertRowDataAndAdd(row, sumPsychosis, lambda d: d == 'F21')

        row = table.addRow()
        insertRowTitle(row, u'шизоаффективные психозы, аффективные психозы с неконгруентным аффекту бредом', 'F25, F3x.x4')
        insertRowDataAndAdd(row, sumPsychosis, lambda d: d == 'F25' or re.match(r'F3\d\.\d4', d) != None)

        row = table.addRow()
        insertRowTitle(row, u'острые и преходящие неорганические психозы', 'F23, F24')
        insertRowDataAndAdd(row, sumPsychosis, lambda d: d in ('F23', 'F24'))

        row = table.addRow()
        insertRowTitle(row, u'хронические неорганические психозы, детские психозы, неуточненные психотические расстройства', 'F22, F28, F29, F84.0-4, F99.1')
        insertRowDataAndAdd(row, sumPsychosis, lambda d: d in ('F22', 'F28', 'F29', 'F99.1') or ('F84.0' <= d <= 'F84.4'))

        row = table.addRow()
        insertRowTitle(row, u'из них: детский аутизм, атипичный аутизм', 'F84.0-1')
        insertRowData(row, lambda d: 'F84.0' <= d <= 'F84.1')

        row = table.addRow()
        insertRowTitle(row, u'аффективные психозы', u'F30-F39 (часть)')
        insertRowDataAndAdd(row, sumPsychosis, lambda d: d in ('F30.23','F30.28','F31.23','F31.28','F31.53','F31.58','F32.33','F32.38','F33.33','F33.38','F39'))

        row = table.addRow()
        insertRowTitle(row, u'из них биполярные расстройства', 'F31.23, F31.28, F31.53, 31.58')
        insertRowData(row, lambda d: d in ('F31.23', 'F31.28', 'F31.53', '31.58'))

        rowNonPsychotic = table.addRow()
        insertRowTitle(rowNonPsychotic, u'Непсихотические психические расстройства', '')

        row = table.addRow()
        insertRowTitle(row, u'в том числе: органические непсихотические расстройства', u'F06 (часть), F07')
        insertRowDataAndAdd(row, sumNonPsychotic, lambda d: ('F06.34'<=d<='F06.37') or ('F07.1'<=d<='F07.2') or ('F07.8'<=d<='F07.9') or d in ('F06.5','F06.6','F06.7','F06.82','F06.92','F06.99','F07.0'))

        row = table.addRow()
        insertRowTitle(row, u'аффективные непсихотические расстройства', u'F30-F39 (часть)')
        insertRowDataAndAdd(row, sumNonPsychotic, lambda d: ('F30.0'<=d<='F30.1') or ('F30.8'<=d<='F30.9') or ('F31.0'<=d<='F31.1') or \
            ('F31.30'<=d<='F31.34') or ('F31.6'<=d<='F31.9') or ('F32.00'<=d<='F23.02') or \
            ('F32.8'<=d<='F32.9') or ('F33.00'<=d<='F33.02') or ('F33.4'<=d<='F38.8'))

        row = table.addRow()
        insertRowTitle(row, u'из них биполярные расстройства', 'F31.0, F31.1, F31.3, F31.4, F31.6-F31.9')
        insertRowData(row, lambda d: d in ('F31.0','F31.1','F31.3','F31.4') or ('F31.6'<=d<='F31.9'))

        row = table.addRow()
        insertRowTitle(row, u'невротические, связанные со стрессом и соматоформные расстройства', 'F40-F48')
        insertRowDataAndAdd(row, sumNonPsychotic, lambda d: 'F40' <= d <= 'F48')

        row = table.addRow()
        insertRowTitle(row, u'другие непсихотические расстройства, поведенческие расстройства детского и подросткового возраста, неуточненные непсихотические расстройства', 'F50-F59, F80-F83, F84.5, F90-F98, F99.2, 9')
        insertRowDataAndAdd(row, sumNonPsychotic, lambda d: ('F50'<=d<='F59') or ('F80'<=d<='F83') or ('F90'<=d<='F98') or d in ('F84.5','F99.2', 'F99.9'))

        row = table.addRow()
        insertRowTitle(row, u'из них синдром Аспергера', 'F84.5')
        insertRowData(row, lambda d: d == 'F84.5')

        row = table.addRow()
        insertRowTitle(row, u'расстройства зрелой личности и поведения у взрослых', 'F60-F69')
        insertRowDataAndAdd(row, sumNonPsychotic, lambda d: 'F60' <= d <= 'F69')

        row = table.addRow()
        insertRowTitle(row, u'Умственная отсталость', 'F70,71-79')
        insertRowData(row, lambda d: d == 'F70' or ('F71' <= d <= 'F79'))

        row = table.addRow()
        insertRowTitle(row, u'Кроме того: пациенты с заболеваниями, связанными с потреблением психоактивных веществ', 'F10-F19')
        insertRowData(row, lambda d: 'F10' <= d <= 'F19')

        row = table.addRow()
        insertRowTitle(row, u'из них: больные алкогольными психозами', 'F10.4-F10.7')
        insertRowData(row, lambda d: 'F10.4' <= d <= 'F10.7')

        row = table.addRow()
        insertRowTitle(row, u'наркоманиями, токсикоманиями', 'F11-F19')
        insertRowData(row, lambda d: 'F11' <= d <= 'F19')

        row = table.addRow()
        insertRowTitle(row, u'признаны психически здоровыми и с заболеваниями, не вошедшими в стр. 1 и 22', '')
        insertRowData(row, lambda d: not ('F00' <= d <= 'F09' or 'F20' <= d <= 'F99'))

        for (i, data) in enumerate(sumPsychosis):
            table.setText(rowPsychosis, 3+i, data)
        for (i, data) in enumerate(sumNonPsychotic):
            table.setText(rowNonPsychotic, 3+i, data)

        return doc



class CStationaryF036_2300_SetupDialog(CDialogBase):
    def __init__(self, parent):
        CDialogBase.__init__(self, parent)
        buttonBox = QtGui.QDialogButtonBox(self)
        buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel | QtGui.QDialogButtonBox.Ok)
        self.edtBegDate = CDateEdit()
        self.edtEndDate = CDateEdit()

        layout = QtGui.QGridLayout(self)
        layout.addWidget(QtGui.QLabel(u'Дата начала периода'), 0, 0)
        layout.addWidget(self.edtBegDate, 0, 1)
        layout.addWidget(QtGui.QLabel(u'Дата окончания периода'), 1, 0)
        layout.addWidget(self.edtEndDate, 1, 1)
        layout.setRowStretch(2, 1)
        layout.addWidget(buttonBox, 3, 0, 1, 2)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)


    def params(self):
        result = {}
        result['begDate'] = self.edtBegDate.date()
        result['endDate'] = self.edtEndDate.date()
        return result


    def setParams(self, params):
        self.edtBegDate.setDate(params.get('begDate', QDate.currentDate()))
        self.edtEndDate.setDate(params.get('endDate', QDate.currentDate()))
