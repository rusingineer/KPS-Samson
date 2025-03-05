# -*- coding: utf-8 -*-

#############################################################################
##
## Copyright (C) 2017-2022 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4                  import QtGui
from PyQt4.QtCore           import QDate
from library.Utils          import forceString, forceDouble
from Reports.ReportBase     import CReportBase, createTable
from Reports.Report         import CReport
from Reports.Utils          import dateRangeAsStr
from library.DateEdit       import CDateEdit
from library.crbcombobox    import CRBComboBox


def selectData(params):
    begDate = params.get('begDate')
    endDate = params.get('endDate')
    personId = params.get('personId')
    typePayment = params.get('typePayment', 0)
    cashOperationId = params.get('cashOperationId')

    db = QtGui.qApp.db
    tablePayment = db.table('Event_Payment')
    tablePerson = db.table('vrbPerson')
    tableCashOperation = db.table('rbCashOperation')

    table = tablePayment
    table = table.innerJoin(tablePerson, tablePayment['createPerson_id'].eq(tablePerson['id']))
    table = table.innerJoin(tableCashOperation, tablePayment['cashOperation_id'].eq(tableCashOperation['id']))

    cond = [
        tablePayment['deleted'].eq(0),
        db.joinOr([
            tableCashOperation['name'].like(u'оплата'),
            tableCashOperation['name'].like(u'возврат'),
        ]),
    ]
    if begDate:
        cond.append(tablePayment['dateTime'].dateGe(begDate))
    if endDate:
        cond.append(tablePayment['dateTime'].dateLe(endDate))
    if personId:
        cond.append(tablePerson['id'].eq(personId))
    if typePayment:
        cond.append(tablePayment['typePayment'].eq(typePayment - 1))
    if cashOperationId:
        cond.append(tablePayment['cashOperation_id'].eq(cashOperationId))

    payCond = tableCashOperation['name'].notlike(u'возврат')
    retCond = tableCashOperation['name'].like(u'возврат')
    cols = [
        tablePerson['name'],
        'SUM(IF(%s AND Event_Payment.typePayment = 0, Event_Payment.sum, 0)) AS `payedSumCash`' % payCond,
        'SUM(IF(%s AND Event_Payment.typePayment = 0, Event_Payment.sum, 0)) AS `returnedSumCash`' % retCond,
        'SUM(IF(%s AND Event_Payment.typePayment = 1, Event_Payment.sum, 0)) AS `payedSum`' % payCond,
        'SUM(IF(%s AND Event_Payment.typePayment = 1, Event_Payment.sum, 0)) AS `returnedSum`' % retCond,
    ]

    stmt = db.selectStmtGroupBy(table, cols, cond, group=tablePerson['id'].name())
    return db.query(stmt)


class CReportCashier(CReport):
    def __init__(self, parent=None):
        CReport.__init__(self, parent)
        self.setTitle(u'Отчет по кассирам')


    def getSetupDialog(self, parent):
        dialog = CSetupDialog(parent)
        dialog.setWindowTitle(self.title())
        return dialog


    def dumpParams(self, cursor, params):
        begDate = params.get('begDate')
        endDate = params.get('endDate')
        personId = params.get('personId')
        typePayment = params.get('typePayment', 0)
        cashOperationId = params.get('cashOperationId')

        db = QtGui.qApp.db
        rows = []
        if bool(begDate) or bool(endDate):
            rows.append(dateRangeAsStr(u'период', begDate, endDate))
        if personId:
            rows.append(u'врач: ' + forceString(db.translate('vrbPersonWithSpeciality', 'id', personId, 'name')))
        if typePayment:
            rows.append(u'тип оплаты: ' + ([u'наличный', u'безналичный'][typePayment - 1]))
        if cashOperationId:
            rows.append(u'кассовая операция: ' + forceString(db.translate('rbCashOperation', 'id', cashOperationId, 'name')))

        cursor.insertText('\n'.join(rows))
        cursor.insertBlock()


    def build(self, params):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportBody)
        self.dumpParams(cursor, params)
        cursor.insertBlock()

        tableColumns = [
            ('16%', [u'ФИО кассира', u''], CReportBase.AlignLeft),
            ('14%', [u'Наличный расчет', u'Оплачено'], CReportBase.AlignLeft),
            ('14%', [u'', u'Возврат'], CReportBase.AlignLeft),
            ('14%', [u'', u'Итого'], CReportBase.AlignLeft),
            ('14%', [u'Безналичный расчет', u'Оплачено'], CReportBase.AlignLeft),
            ('14%', [u'', u'Возврат'], CReportBase.AlignLeft),
            ('14%', [u'', u'Итого'], CReportBase.AlignLeft),
        ]
        table = createTable(cursor, tableColumns)
        table.mergeCells(0,0, 2,1)
        table.mergeCells(0,1, 1,3)
        table.mergeCells(0,4, 1,3)

        query = selectData(params)
        total = [0.0] * 6
        while query.next():
            record = query.record()
            name = forceString(record.value('name'))
            payedSumCash = forceDouble(record.value('payedSumCash'))
            returnedSumCash = abs(forceDouble(record.value('returnedSumCash')))
            payedSum = forceDouble(record.value('payedSum'))
            returnedSum = abs(forceDouble(record.value('returnedSum')))

            row = table.addRow()
            table.setText(row, 0, name)
            table.setText(row, 1, payedSumCash)
            table.setText(row, 2, returnedSumCash)
            table.setText(row, 3, payedSumCash - returnedSumCash)
            table.setText(row, 4, payedSum)
            table.setText(row, 5, returnedSum)
            table.setText(row, 6, payedSum - returnedSum)
            total[0] += payedSumCash
            total[1] += returnedSumCash
            total[2] += payedSumCash - returnedSumCash
            total[3] += payedSum
            total[4] += returnedSum
            total[5] += payedSum - returnedSum

        row = table.addRow()
        table.setText(row, 0, u'Итого', charFormat=CReportBase.TableTotal)
        for col, value in enumerate(total):
            table.setText(row, 1+col, value, charFormat=CReportBase.TableTotal)

        return doc



class CSetupDialog(QtGui.QDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.edtBegDate = CDateEdit(self)
        self.edtEndDate = CDateEdit(self)
        self.cmbTypePayment = QtGui.QComboBox(self)
        self.cmbPerson = CRBComboBox(self)
        self.cmbCashOperation = CRBComboBox(self)
        buttonBox = QtGui.QDialogButtonBox(self)

        self.cmbTypePayment.addItems([u'не задано', u'наличный', u'безналичный'])
        self.cmbCashOperation.setTable('rbCashOperation')
        self.cmbPerson.setTable('vrbPersonWithSpeciality')
        buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        layout = QtGui.QGridLayout(self)
        layout.addWidget(QtGui.QLabel(u'Дата начала'), 0, 0)
        layout.addWidget(QtGui.QLabel(u'Дата окончания'), 1, 0)
        layout.addWidget(QtGui.QLabel(u'Кассир'), 2, 0)
        layout.addWidget(QtGui.QLabel(u'Тип оплаты'), 3, 0)
        layout.addWidget(QtGui.QLabel(u'Кассовая операция'), 4, 0)

        layout.addWidget(self.edtBegDate, 0, 1)
        layout.addWidget(self.edtEndDate, 1, 1)
        layout.addWidget(self.cmbPerson, 2, 1)
        layout.addWidget(self.cmbTypePayment, 3, 1)
        layout.addWidget(self.cmbCashOperation, 4, 1)
        layout.setRowStretch(5, 1)
        layout.addWidget(buttonBox, 6, 0, 1, 2)


    def params(self):
        result = {}
        result['begDate'] = self.edtBegDate.date()
        result['endDate'] = self.edtEndDate.date()
        result['personId'] = self.cmbPerson.value()
        result['typePayment'] = self.cmbTypePayment.currentIndex()
        result['cashOperationId'] = self.cmbCashOperation.value()
        return result


    def setParams(self, params):
        self.edtBegDate.setDate(params.get('begDate', QDate()))
        self.edtEndDate.setDate(params.get('endDate', QDate()))
        self.cmbPerson.setValue(params.get('personId'))
        self.cmbCashOperation.setValue(params.get('cashOperationId'))
        self.cmbTypePayment.setCurrentIndex(params.get('typePayment', 0))

