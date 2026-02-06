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
from PyQt4.QtCore import QDate, QDateTime

from library.Utils      import forceInt, forceRef, forceString

from Reports.Report     import CReport
from Reports.ReportBase import CReportBase, createTable


def selectData(policyDate, policyType, policyKind, naselenie):
    stmt="""
SELECT
    COUNT(*) AS cnt,
    age(Client.birthDate, %s) AS clientAge,
    Client.sex AS clientSex,
    ClientPolicy.insurer_id,
    Organisation.shortName,
    Organisation.area as area
FROM Client
INNER JOIN ClientPolicy  ON ClientPolicy.client_id = Client.id
        AND ClientPolicy.id = (SELECT MAX(CP.id) FROM ClientPolicy AS CP
                               WHERE CP.deleted = 0
                               AND   CP.insurer_id = ClientPolicy.insurer_id
                               AND   CP.client_id = Client.id
                               %s
                               %s
                              )
INNER JOIN rbPolicyType ON rbPolicyType.id = ClientPolicy.policyType_id
INNER JOIN Organisation ON Organisation.id = ClientPolicy.insurer_id
WHERE Client.deleted = 0 AND ClientPolicy.deleted = 0 AND Organisation.deleted = 0
  %s
GROUP BY clientAge, clientSex, shortName
    """
    db = QtGui.qApp.db
    tableClient = db.table('Client')
    tableClientPolicy = db.table('ClientPolicy')
    tableRBPolicyType = db.table('rbPolicyType')
    cond = []
    if policyDate:
        cond.append(tableClientPolicy['begDate'].lt(policyDate.addDays(1)))
        cond.append(
                    db.joinOr(
                              [
                               tableClientPolicy['endDate'].ge(policyDate),
                               tableClientPolicy['endDate'].isNull()
                              ]
                             )
                   )
    stmtPolicyTypeId = u''
    stmtPolicyKindId = u''
    if policyType:
        if policyType == -1:
            cond.append(db.joinOr([tableRBPolicyType['code'].eq('1'), tableRBPolicyType['code'].eq('2')]))
        else:
            cond.append(tableClientPolicy['policyType_id'].eq(policyType))
        stmtPolicyTypeId = u'AND CP.policyType_id = ClientPolicy.policyType_id'
    if policyKind:
        cond.append(tableClientPolicy['policyKind_id'].eq(policyKind))
        stmtPolicyKindId = u'AND CP.policyKind_id = ClientPolicy.policyKind_id'

    # краевые/инокраевые
    if naselenie:
        region = QtGui.qApp.provinceKLADR()[:2]

        if naselenie == 1:  # Краевые
            cond.append("substr(area, 1, 2) = '{region}'".format(region=region))
        elif naselenie == 2:  # Инокраевые
            cond.append("substr(area, 1, 2) <> '{region}'".format(region=region))

    return db.query(stmt % (tableClient['birthDate'].formatValue(policyDate), stmtPolicyTypeId, stmtPolicyKindId, (u' AND %s'%(db.joinAnd(cond))) if cond else u''))


class CBySMOContingent(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setPayPeriodVisible(False)
        self.setTitle(u'Контингент по СМО')


    def getSetupDialog(self, parent):
        result = CBySMOContingentSetupDialog(parent)
        result.setTitle(self.title())
        return result


    def dumpParams(self, cursor, params):
        db = QtGui.qApp.db
        description = []
        policyDate = params.get('policyDate', QDate())
        policyType = params.get('policyType', None)
        policyKind = params.get('policyKind', None)
        description.append(u'на дату: ' + forceString(policyDate))
        if policyType:
            if policyType == -1:
                description.append(u'тип полиса: ОМС')
            else:
                description.append(u'тип полиса: ' + forceString(db.translate('rbPolicyType', 'id', policyType, 'name')))
        if policyKind:
            description.append(u'вид полиса: ' + forceString(db.translate('rbPolicyKind', 'id', policyKind, 'name')))
        description.append(u'отчёт составлен: ' + forceString(QDateTime.currentDateTime()))
        columns = [ ('100%', [], CReportBase.AlignLeft) ]
        table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
        for i, row in enumerate(description):
            table.setText(i, 0, row)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()


    def build(self, params):
        policyDate = params.get('policyDate', QDate())
        policyType = params.get('policyType', None)
        policyKind = params.get('policyKind', None)
        naselenie = params.get('naselenie', None)

        reportRowSize = 15
        keyNameTotal = (u'Итого', None)
        reportShortName = {}
        reportShortNameTotal = {(keyNameTotal): [0] * reportRowSize}
        query = selectData(policyDate, policyType, policyKind, naselenie)
        while query.next():
            record = query.record()
            cnt    = forceInt(record.value('cnt'))
            age    = forceInt(record.value('clientAge'))
            sex    = forceInt(record.value('clientSex'))
            shortName   = forceString(record.value('shortName'))
            insurerId   = forceRef(record.value('insurer_id'))
            keyName = (shortName, insurerId)
            reportData = reportShortName.get(keyName, [0] * reportRowSize)
            reportDataTotal = reportShortNameTotal.get(keyNameTotal, [0] * reportRowSize)
            if age < 1:
                colBase = 0
            elif age == 1:
                colBase = 2
            elif age <= 6:
                colBase = 4
            elif age <= 14:
                colBase = 6
            elif age <= 17:
                colBase = 8
            elif (sex==1 and age < 60) or (sex != 1 and age < 55):
                colBase = 10
            else:
                colBase = 12
            cols = [colBase+(0 if sex==1 else 1), 14]
            for col in cols:
                reportData[col] += cnt
                reportDataTotal[col] += cnt
            reportShortName[keyName] = reportData
            reportShortNameTotal[keyNameTotal] = reportDataTotal

        # now text
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()

        tableColumns = [
            ('15%', [u'Наименование страховой компании', u''], CReportBase.AlignLeft),
            ( '5%', [u'№ стр.', u''], CReportBase.AlignRight),
            ( '5%', [u'Численность прикреплённого населения по возрастному составу', u'дети', u'до 1 года', u'М'], CReportBase.AlignRight),
            ( '5%', [u'', u'', u'', u'Ж'], CReportBase.AlignRight),
            ( '5%', [u'', u'', u'1 год', u'М'], CReportBase.AlignRight),
            ( '5%', [u'', u'', u'', u'Ж'], CReportBase.AlignRight),
            ( '5%', [u'', u'', u'2-6 лет', u'М'], CReportBase.AlignRight),
            ( '5%', [u'', u'', u'', u'Ж'], CReportBase.AlignRight),
            ( '5%', [u'', u'', u'7-14 лет', u'М'], CReportBase.AlignRight),
            ( '5%', [u'', u'', u'', u'Ж'], CReportBase.AlignRight),
            ( '5%', [u'', u'', u'15-17 лет', u'М'], CReportBase.AlignRight),
            ( '5%', [u'', u'', u'', u'Ж'], CReportBase.AlignRight),
            ( '5%', [u'', u'взрослые', u'трудосп. возраста', u'М, 18-59 лет'], CReportBase.AlignRight),
            ( '5%', [u'', u'', u'', u'Ж, 18-54 лет'], CReportBase.AlignRight),
            ( '5%', [u'', u'', u'нетрудосп. возраста', u'М, 60 и ст.'], CReportBase.AlignRight),
            ( '5%', [u'', u'', u'', u'Ж, 55 и ст.'], CReportBase.AlignRight),
            ( '5%', [u'Всего', ], CReportBase.AlignRight),
            ]
        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 4, 1) # Категории населения
        table.mergeCells(0, 1, 4, 1) # № стр.
        table.mergeCells(0, 2, 1,14) # Численность...
        table.mergeCells(1, 2, 1,10) # дети
        table.mergeCells(2, 2, 1, 2) # <1
        table.mergeCells(2, 4, 1, 2) # 1
        table.mergeCells(2, 6, 1, 2) # 2-6
        table.mergeCells(2, 8, 1, 2) # 7-14
        table.mergeCells(2,10, 1, 2) # 15-17
        table.mergeCells(1,12, 1, 4) # взрослые
        table.mergeCells(2,12, 1, 2) # тр.
        table.mergeCells(2,14, 1, 2) # нетр.
        table.mergeCells(0,16, 4, 1) # всего

        keySortName = reportShortName.keys()
        keySortName.sort()
        for reportDataTotal in reportShortNameTotal.values():
            i = table.addRow()
            table.setText(i, 0, keyNameTotal[0])
            table.setText(i, 1, i-3)
            for j in xrange(len(reportDataTotal)):
                table.setText(i, 2+j, reportDataTotal[j])
        for keyName in keySortName:
            reportData = reportShortName.get(keyName, [0] * reportRowSize)
            i = table.addRow()
            table.setText(i, 0, keyName[0])
            table.setText(i, 1, i-3)
            for j in xrange(len(reportData)):
                table.setText(i, 2+j, reportData[j])
        return doc


from Ui_BySMOContingentSetup import Ui_BySMOContingentSetupDialog


class CBySMOContingentSetupDialog(QtGui.QDialog, Ui_BySMOContingentSetupDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.cmbPolicyType.setTable('rbPolicyType', True, specialValues=((-1, u'ОМС', u'ОМС'), ))
        self.cmbPolicyKind.setTable('rbPolicyKind', True)

    def setPayPeriodVisible(self, value):
        pass


    def setWorkTypeVisible(self, value):
        pass


    def setTitle(self, title):
        self.setWindowTitle(title)


    def setEventTypeVisible(self, visible=True):
        pass


    def setParams(self, params):
        self.edtPolicyDate.setDate(params.get('policyDate', QDate.currentDate()))
        self.cmbPolicyType.setValue(params.get('policyType', None))
        self.cmbPolicyKind.setValue(params.get('policyKind', None))
        self.cmbRazrNas.setCurrentIndex(params.get('naselenie', 0))


    def params(self):
        result = {}
        result['policyDate'] = self.edtPolicyDate.date()
        result['policyType'] = self.cmbPolicyType.value()
        result['policyKind'] = self.cmbPolicyKind.value()
        if self.cmbRazrNas.isEnabled():
            result['naselenie'] = self.cmbRazrNas.currentIndex()
        return result
