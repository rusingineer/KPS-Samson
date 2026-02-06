# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2015 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import *
from Reports.Report     import CReport
from Reports.ReportBase import *
from Ui_PaidServicesSetupDialog import Ui_PaidServicesSetupDialog
from library.Utils import forceString, forceInt, forceDouble, forceDate
from Events.Utils import getWorkEventTypeFilter

class CPaidServicesSetupDialog(QtGui.QDialog, Ui_PaidServicesSetupDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.cmbEventType.setTable('EventType', True, filter=getWorkEventTypeFilter())
        self.cmbLab.setTable('ActionType', True, filter=u'ActionType.class = 1 and group_id = (select id from ActionType where name = "Исследования Альфа-Лаборатория" limit 1) and deleted = 0')


    def setParams(self, params):
        self.edtBegDate.setDate(params.get('begDate', QDate.currentDate()))
        self.edtEndDate.setDate(params.get('endDate', QDate.currentDate()))
        # self.edtCustomDate.setDate(params.get('customDate', QDate.currentDate()))
        # self.edtCustomTime.setTime(params.get('customTime', QTime().currentTime()))

        self.edtCustomDate.setDate(params.get('customDate', QDate.currentDate()))
        self.edtCustomTime.setTime(params.get('customTime', QTime.currentTime()))

        self.cmbEventType.setValue(params.get('eventTypeId', None))
        typePayment = params.get('typePayment', None)
        if typePayment is None:
            self.cmbTypePayment.setCurrentIndex(0)
        else:
            self.cmbTypePayment.setCurrentIndex(params['typePayment'] + 1)
        self.cmbLab.setValue(params.get('lab', None))
        self.cmbPatient.setValue(params.get('clientId', None))

        reportType = params.get('reportType', 0)
        self.rbPayment.setChecked(0 == reportType)
        self.rbPatient.setChecked(1 == reportType)
        self.rbLab.setChecked(2 == reportType)
        self.cmbService.setValue(params.get('serviceId', None))


    def params(self):
        result = {}
        result['begDate'] = self.edtBegDate.date()
        result['endDate'] = self.edtEndDate.date()
        result['customDate'] = self.edtCustomDate.date()
        result['customTime'] = self.edtCustomTime.time()
        result['eventTypeId'] = self.cmbEventType.value()
        result['typePayment'] = [None, 0, 1, 2][self.cmbTypePayment.currentIndex()]
        result['lab'] = self.cmbLab.value()
        result['clientId'] = self.cmbPatient.value()
        result['reportType'] = [self.rbPayment.isChecked(), self.rbPatient.isChecked(), self.rbLab.isChecked()].index(True)
        result['serviceId'] = self.cmbService.value()
        return result

class CPaidServices(CReport):
    def __init__(self, parent=None):
        CReport.__init__(self, parent)
        self.setTitle(u'Анализ платных услуг')

    def getSetupDialog(self, parent):
        return CPaidServicesSetupDialog(parent)

    def selectData(self, params):
        reportType = params.get('reportType', 0)
        stmt = ''
        if reportType == 2:
            stmt += 'SELECT temp.date, temp.PaymentType, temp.typeCash, temp.lab, temp.service, temp.service_id, temp.templab, sum(temp.sum) as sum, sum(temp.amount) as amount from ('
        stmt += u'''
SELECT distinct
    Event.id,
    concat_ws(" ",{0}.lastName, {0}.firstName, {0}.patrName) as client,
    IF(co.code = 2 ,sum(IF(Account_Item.refuseType_id IS NULL AND co.code = 1, 1, Account_Item.refuseType_id IS not NULL AND co.code = 2)), sum(Account_Item.amount)) as amount,
   -- IF(IF(co.name='Возврат', Event_Payment.sum, 0) = 0, IF(SUM(Account_Item.payedSum)=0,Account_Item.sum,SUM(Account_Item.payedSum)), ABS(Event_Payment.sum))    AS sum,
      IF(sum(IF (Account_Item.refuseType_id IS not NULL AND co.code = 2, Account_Item.sum, 0))=0, sum(Account_Item.sum), sum(IF (Account_Item.refuseType_id IS not NULL AND co.code = 2, Account_Item.sum, 0)))   AS sum,
    ifnull(Event_Payment.dateTime, Account_Item.date) as date,
    IF(co.code = 1 AND Event_Payment.typePayment = 0 ,'Наличная оплата',IF(co.code = 1 AND Event_Payment.typePayment = 1,'Электронная оплата',IF(co.code = 2 AND Event_Payment.typePayment = 0 ,'Наличный возврат',IF(co.code = 2 AND Event_Payment.typePayment = 1,'Электронный возврат','1')))) as PaymentType,
    case when co.code = 1 then 'оплата' else 'возврат' end as typeCash,
    ifnull(laboratory.name, '---') as lab,
    rbService.name as service,
    rbService.id as service_id,
    laboratory.id as templab
    FROM Event_Payment
left join Event on Event.id = Event_Payment.master_id
left join rbCashOperation co ON Event_Payment.cashOperation_id = co.id
left join {1}
left join Account_Item on Account_Item.event_id = Event.id
left join rbService on rbService.id = Account_Item.service_id
left join Action on Action.id = Account_Item.action_id
left join ActionType on ActionType.id = Action.actionType_id
left join ActionType at1 on at1.id = ActionType.group_id
left join ActionType at2 on at2.id = at1.group_id
left join ActionType at3 on at3.id = at2.group_id
left join ActionType at4 on at4.id = at3.group_id
left join ActionType at5 on at5.id = at4.group_id
left join ActionType at6 on at6.id = at5.group_id
left join ActionType at7 on at7.id = at6.group_id
left join ActionType at8 on at8.id = at7.group_id
left join ActionType at9 on at9.id = at8.group_id
left join ActionType laboratory on laboratory.id in (
	select atl.id from ActionType atl where
    atl.class = 1
    and atl.group_id = (select id from ActionType where flatCode = "platnie" limit 1)
    and atl.deleted = 0
    ) and laboratory.id in (Action.actionType_id, at1.id, at2.id, at3.id, at4.id, at5.id, at6.id, at7.id, at8.id, at9.id)
where Event_Payment.deleted=0  and co.code in (1,2) and {cond}

'''
        stmt += [u'group by PaymentType, co.code, Event_LocalContract.id, Event_Payment.id HAVING amount>0 order by PaymentType, co.code, client, service',
                 u'group by Client.id, rbService.id,co.id HAVING amount>0 /*AND PaymentType like "%%оплата%%" */order by client, service',
                 u'group by laboratory.id, PaymentType, rbService.id, Event_Payment.id HAVING amount>0 order by lab, PaymentType, service) temp group by templab, PaymentType, temp.service_id order by temp.lab, temp.PaymentType, temp.service',
                 ][reportType]
        cond = []
        cond.append(u'ifnull(Event_Payment.dateTime, Account_Item.date) between "%s" and "%s"' %
                    (params['begDate'].toString('yyyy-MM-dd 00:00:00'), params['endDate'].toString('yyyy-MM-dd 23:59:59'))
                    )
        if params.get('eventTypeId', False):
            cond.append(u'Event.eventType_id = %s' % params['eventTypeId'])
        if params.get('typePayment', False) is not None:
            cond.append(u'Event_Payment.typePayment = %s' % params['typePayment'])
        if params.get('lab', False):
            cond.append(u'laboratory.id = %s' % params['lab'])
        if params.get('clientId', False) and reportType != 0:
            cond.append(u'Client.id = %s' % params['clientId'])
        if params.get('serviceId', False):
            cond.append(u'rbService.id = %s' % params['serviceId'])
        db = QtGui.qApp.db
        st = stmt.format("Event_LocalContract" if reportType == 0 else "Client",
                         "Event_LocalContract on Event_LocalContract.master_id = Event.id" if reportType == 0 else "Client on Client.id = Event.client_id",
                         cond = " and ".join(cond))
        return db.query(st)

    def dumpParams(self, cursor, params, align=CReportBase.AlignLeft):
        description = self.getDescription(params)
        columns = [ ('100%', [], align) ]
        table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
        for i, row in enumerate(description):
            if u'отчёт составлен' in row:
                begDate = params.get('customDate', QDate())
                begTime = params.get('customTime', QTime())
                begDateTime = QDateTime(begDate, begTime)
                row = u'отчёт составлен: %s' % forceString(begDateTime)
                table.setText(i, 0, row)
            else:
                table.setText(i, 0, row)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()

    def build(self, params):
        report = []
        self.clientComing = 0
        self.clientRefund = 0
        self.reportType = params.get('reportType', 0)
        def processQuery(query):
            while query.next():
                reportLine = []
                for col in ['client', 'amount', 'sum', 'date', 'PaymentType', 'lab', 'service', 'service_id']:
                    record = query.record()
                    if col == 'amount':
                        val = forceInt(record.value(col))
                    elif col == 'sum':
                        val = forceDouble(record.value(col))
                    elif col == 'date':
                        val = forceDate(record.value(col)).toString('dd.MM.yyyy')
                    else:
                        val = forceString(record.value(col))
                    if col == 'PaymentType':
                        if u'оплата' in forceString(record.value(col)):
                            self.clientComing += forceDouble(record.value('sum'))
                        else:
                            self.clientRefund += forceDouble(record.value('sum'))
                    reportLine.append(val)
                if self.reportType == 1 and u'оплата' in forceString(record.value('PaymentType')):
                    report.append(reportLine)
                elif self.reportType != 1:
                    report.append(reportLine)
        query = self.selectData(params)
        processQuery(query)
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.setBlockFormat(CReportBase.AlignCenter)
        cursor.insertText(self.title())
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportBody)
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        reportType = params.get('reportType', 0)
        firstcol = [u'Тип оплаты/пациент', u'Пациент/Услуга', u'Лаборатория/Тип оплаты/Услуга'][reportType]
        if reportType == 0:
            tableColumns = [
                ('3%', u'№', CReportBase.AlignLeft),
                ('42%', [firstcol], CReportBase.AlignCenter),
                ('15%', [u'кол-во услуг'], CReportBase.AlignRight),
                ('20%', [u'сумма'], CReportBase.AlignRight),
                ('20%', [u'дата оплаты'], CReportBase.AlignRight),
                ]
        elif reportType == 1:
            tableColumns = [
                ('3%', [u'№'], CReportBase.AlignLeft),
                ('47%', [firstcol], CReportBase.AlignCenter),
                ('25%', [u'кол-во услуг'], CReportBase.AlignRight),
                ('25%', [u'сумма'], CReportBase.AlignRight),
                ]
        else:
            tableColumns = [
                ('50%', [firstcol], CReportBase.AlignLeft),
                ('25%', [u'кол-во услуг'], CReportBase.AlignRight),
                ('25%', [u'сумма'], CReportBase.AlignRight),
                ]
        table = createTable(cursor, tableColumns)
        body_columns = [[0, 1, 2, 3], [6, 1, 2], [6, 1, 2]][reportType]
        header_column = [4, 0, 5][reportType]

        flagS= None
        flagSE= None
        sumNal = []
        sumEl = []
        sumVNal = []
        sumVEl = []

        
        
        if reportType == 0:
            def writeline(line, columns):
                for i, col in enumerate(columns):
                    text = line[col]
                    if i == 0:
                        text = u'  ' + line[col]
                    table.setText(row, i+1, text)

            def writetotal(col, index, optionalCol = None):
                _report = report[:index]
                title = _report[-1][col]

                sum = [None] * len(report[0])
                if optionalCol:
                    optionalTitle = _report[-1][optionalCol] #опциональная колонка для подсчета

                for i in reversed(_report):
                    if i[col] != title: #считаем сумму пока строка соответсвтует заголовку, например "Наличная оплата"
                        break
                    if optionalCol and i[optionalCol] != optionalTitle: #дополнительный заголовок, например "Лаборатория такая-то"
                        break
                    for j,_col in enumerate(i):
                        if type(_col) in [float, int]:
                            if sum[j] is None:
                                sum[j] = 0
                            sum[j] += _col

                row = table.addRow()
                for i, c in enumerate(sum):
                    if i == 0:
                        if title == u'Наличная оплата':
                            sumNal.append(u'Итого по "Наличная оплата"')
                        elif title == u'Электронная оплата':
                            sumEl.append(u'Итого по "Электронная оплата"')
                        table.mergeCells(row, 0, 1, 2)
                        if title == u'Электронный возврат':
                            table.setText(row, 0, u'  "%s" - всего' % title, CReportBase.TableTotal)
                        elif title == u'Наличная оплата':
                            table.setText(row, 0, '"%s"' % title, CReportBase.TableTotal)
                        else:
                            table.setText(row, 0, u'  "%s" - приход' % title, CReportBase.TableTotal)
                    elif c != None:
                        if title == u'Наличная оплата':
                            sumNal.append(c)
                        elif title == u'Электронная оплата':
                            sumEl.append(c)
                        elif title == u'Наличный возврат':
                            sumVNal.append(c)
                        else:
                            sumVEl.append(c)
                        table.setText(row, i+1, c)

            def writetotalf():
                if len(report) == 0:
                    return
                sumV1 = 0
                sumV2 = 0
                sum = [None] * len(report[0])
                for i in report:
                    for j,_col in enumerate(i):
                        if type(_col) in [float, int]: # and u'возврат' not in i[4]:
                            if sum[j] is None:
                                sum[j] = 0
                            if u'возврат' not in i[4]:
                                sum[j] += _col
                            else:
                                if j == 1:
                                    sumV1 += _col
                                elif  j == 2:
                                    sumV2 += _col
                                sum[j] -= _col

                row = table.addRow()
                table.setText(row, 0, u'Приход', CReportBase.TableTotal)
                tempSumNC = sumNal[1] if sumNal else 0
                tempSumElC = sumEl[1] if sumEl else 0
                tempSumN = sumNal[2] if sumNal else 0
                tempSumEl = sumEl[2] if sumEl else 0
                table.setText(row, 2, tempSumNC + tempSumElC, CReportBase.TableTotal)
                table.setText(row, 3, tempSumN + tempSumEl, CReportBase.TableTotal)
                table.mergeCells(row, 0, 1, 2)
                row = table.addRow()
                table.setText(row, 0, u'Возврат', CReportBase.TableTotal)
                table.setText(row, 2, sumV1, CReportBase.TableTotal)
                table.setText(row, 3, sumV2, CReportBase.TableTotal)
                table.mergeCells(row, 0, 1, 2)

                row = table.addRow()
                for i, c in enumerate(sum):
                    if i == 0:
                        table.mergeCells(row, 0, 1, 2)
                        table.setText(row, 0, u'  Итого ' + h1 + u' ' + h2 + u' ' + h3 + u' ' + h4, CReportBase.TableTotal)
                    elif c != None:
                        table.mergeCells(row, 0, 1, 2)
                        table.setText(row, i+1, c)

            def writeheader(header, isSubHeader = False):
                row = table.addRow()
                text = header
                if isSubHeader:
                    text = u" "+text
                table.mergeCells(row, 0, 1, 2)    
                table.setText(row, 1, text, CReportBase.TableTotal)
            
            d = 0
            h1 = u'Наличная оплата 0'
            h2 = u'Наличный возврат 0'
            h3 = u'Электронная оплата 0'
            h4 = u'Электронный возврат 0'
            for i, line in enumerate(report):
                if i == 0 or report[i-1][header_column] != report[i][header_column]:
                    if u'Наличн' not in line[header_column] and flagS is None:
                        if sumNal:
                            row = table.addRow()
                            table.setText(row, 0, sumNal[0], CReportBase.TableTotal)
                            table.setText(row, 2, sumNal[1] - sumVNal[0] if sumVNal else sumNal[1] - 0, CReportBase.TableTotal)
                            table.setText(row, 3, sumNal[2] - sumVNal[1] if sumVNal else sumNal[2] - 0, CReportBase.TableTotal)
                            table.mergeCells(row, 0, 1, 2)
                        flagS = True
                    d = 0
                    writeheader(line[header_column])

                if reportType == 2:#подкатегория "тип оплаты"
                    if i == 0 or report[i-1][header_column] != report[i][header_column] or report[i-1][4] != report[i][4]:
                        writeheader(line[4], True)
                
                
                row = table.addRow()
                d += 1
                table.setText(row, 0, d, CReportBase.TableTotal)
                writeline(line, body_columns)


                if i == len(report) - 1 or report[i][header_column] != report[i+1][header_column]:
                    writetotal(header_column, i+1)

            if sumNal:
                h1 = u'Наличная оплата' + u' ' + str(sumNal[1])
            if sumVNal:
                h1 = u'Наличная оплата' + u' ' + str(sumNal[1]-sumVNal[0])
                h2 = u'Наличный возврат' + u' ' + str(sumVNal[0])
            if sumEl:
                h3 = u'Электронная оплата' + u' ' + str(sumEl[1])
            if sumVEl:
                h3 = u'Электронная оплата' + u' ' + str(sumEl[1]-sumVEl[0])
                h4 = u'Электронный возврат' + u' ' + str(sumVEl[0])

            if flagS is None and sumNal:
                row = table.addRow()
                table.setText(row, 0, sumNal[0], CReportBase.TableTotal)
                table.setText(row, 2, sumNal[1] - sumVNal[0] if sumVNal else sumNal[1] - 0, CReportBase.TableTotal)
                table.setText(row, 3, sumNal[2] - sumVNal[1] if sumVNal else sumNal[2] - 0, CReportBase.TableTotal)
                table.mergeCells(row, 0, 1, 2)

            if flagSE is None and sumEl:
                row = table.addRow()
                table.setText(row, 0, sumEl[0], CReportBase.TableTotal)
                table.setText(row, 2, sumEl[1] - sumVEl[0] if sumVEl else sumEl[1] - 0, CReportBase.TableTotal)
                table.setText(row, 3, sumEl[2] - sumVEl[1] if sumVEl else sumEl[2] - 0, CReportBase.TableTotal)
                table.mergeCells(row, 0, 1, 2)

            writetotalf()
            
        elif reportType == 2:

            def writeline(line, columns):
                row = table.addRow()
                for i, col in enumerate(columns):
                    text = line[col]
                    if i == 0:
                        text = u'  ' + line[col]
                    table.setText(row, i, text)

            def writetotal(col, index, optionalCol = None, a = None):
                _report = report[:index]
                title = _report[-1][col]
                sum = [None] * len(report[0])
                if optionalCol:
                    optionalTitle = _report[-1][optionalCol] #опциональная колонка для подсчета

                for i in reversed(_report):
                    if i[col] != title: #считаем сумму пока строка соответсвтует заголовку, например "Наличная оплата"
                        break
                    if optionalCol and i[optionalCol] != optionalTitle: #дополнительный заголовок, например "Лаборатория такая-то"
                        break
                    for j,_col in enumerate(i):
                        if type(_col) in [float, int]:
                            if sum[j] is None:
                                sum[j] = 0
                            if a:
                                if u'возврат' in i[4]:
                                    sum[j] -= _col
                                else:
                                    sum[j] += _col
                            else:
                                sum[j] += _col

                row = table.addRow()
                for i, c in enumerate(sum):
                    if i == 0:
                        table.setText(row, 0, u'  Итого по "%s"' % title, CReportBase.TableTotal)
                    elif c != None:
                        table.setText(row, i, abs(round(c, 5)) if i == 2 else c)

            def writetotalf():
                if len(report) == 0:
                    return
                sum = [None] * len(report[0])
                sumV = [None] * len(report[0])
                sumP = [None] * len(report[0])
                for i in report:
                    for j,_col in enumerate(i):
                        if type(_col) in [float, int]: # and u'возврат' not in i[4]:
                            if sum[j] is None:
                                sum[j] = 0
                            if sumV[j] is None:
                                sumV[j] = 0
                            if sumP[j] is None:
                                sumP[j] = 0
                            if u'возврат' in i[4]:
                                sum[j] -= _col
                                sumV[j] += _col
                            else:
                                sum[j] += _col
                                sumP[j] += _col

                for i, c in enumerate(sum):
                    if i == 0:
                        row = table.addRow()
                        table.setText(row, 0, u'  Приход', CReportBase.TableTotal)
                        row = table.addRow()
                        table.setText(row, 0, u'  Возврат', CReportBase.TableTotal)
                        row = table.addRow()
                        table.setText(row, 0, u'  Итого', CReportBase.TableTotal)
                    elif c != None:
                        table.setText(row-2, i, sumP[i])
                        table.setText(row-1, i, sumV[i])
                        table.setText(row, i, c)

            def writeheader(header, isSubHeader = False):
                row = table.addRow()
                text = header
                if isSubHeader:
                    text = u" "+text
                table.setText(row, 0, text, CReportBase.TableTotal, CReportBase.AlignCenter)

            for i, line in enumerate(report):
                if i == 0 or report[i-1][header_column] != report[i][header_column]:
                    writeheader(line[header_column])

                if reportType == 2:#подкатегория "тип оплаты"
                    if i == 0 or report[i-1][header_column] != report[i][header_column] or report[i-1][4] != report[i][4]:
                        writeheader(line[4], True)

                writeline(line, body_columns)

                if reportType == 2:
                    if i == len(report) - 1 or report[i][header_column] != report[i+1][header_column] or report[i][4] != report[i + 1][4]:
                        writetotal(4, i+1, 5) #пишет итог по 4й и 5й колонке, т.е. Тип оплаты и Лаборатории


                if i == len(report) - 1 or report[i][header_column] != report[i+1][header_column]:
                    writetotal(header_column, i+1, None, True)

            writetotalf()
          
        else:    
            def writeline(line, columns):
                row = table.addRow()
                x=0
                for i, col in enumerate(columns):
                    text = line[col]
                    if i == 0:
                        text = u'  ' + line[col]
                    x += 1
                    table.mergeCells(row, 0, 1, 2)
                    table.setText(row, i+1, text)

            def writetotal(col, index, optionalCol = None):
                _report = report[:index]
                title = _report[-1][col]
                sum = [None] * len(report[0])
                a = 0
                if optionalCol:
                    optionalTitle = _report[-1][optionalCol] #опциональная колонка для подсчета
                for i in reversed(_report):
                    if i[col] != title: #считаем сумму пока строка соответсвтует заголовку, например "Наличная оплата"
                        break
                    if optionalCol and i[optionalCol] != optionalTitle: #дополнительный заголовок, например "Лаборатория такая-то"
                        break
                    for j,_col in enumerate(i):
                        if type(_col) in [float, int]:
                            if sum[j] is None:
                                sum[j] = 0
                            sum[j] += _col
                
                row = table.addRow()
                for i, c in enumerate(sum):
                    if i == 0:
                        table.mergeCells(row, 0, 1, 2)
                        table.setText(row, 1, u'  Итого по "%s"' % title, CReportBase.TableTotal)
                    elif c != None:
                        table.mergeCells(row, 0, 1, 2)
                        table.setText(row, i+1, c)

            def writetotalf():
                if len(report) == 0:
                    return
                test=d
                sum = [None] * len(report[0])
                for i in report:
                    for j,_col in enumerate(i):
                        if type(_col) in [float, int]:
                            if sum[j] is None:
                                sum[j] = 0
                            sum[j] += _col

                for i, c in enumerate(sum):
                    if i == 0:
                        row = table.addRow()
                        table.setText(row, 0, u'  Приход %s' % self.clientComing, CReportBase.TableTotal, CReportBase.AlignLeft)
                        table.mergeCells(row, 0, 1, 4)
                        row = table.addRow()
                        table.setText(row, 0, u'  Возврат %s' % self.clientRefund, CReportBase.TableTotal, CReportBase.AlignLeft)
                        table.mergeCells(row, 0, 1, 4)
                        row = table.addRow()
                        table.setText(row, 1, u'  Итого кол-во пациентов %s' % test, CReportBase.TableTotal)
                    elif c != None:
                        table.mergeCells(row, 0, 1, 2)
                        table.setText(row, i+1, c)

            def writeheader(header, isSubHeader = False):
                text = header
                if isSubHeader:
                    text = u" "+text      
                table.setText(row, 1, text, CReportBase.TableTotal)   
            
            d=0
            for i, line in enumerate(report):
                if i == 0 or report[i-1][header_column] != report[i][header_column]:
                    row = table.addRow()
                    d+=1
                    table.setText(row, 0, d, CReportBase.TableTotal)
                    writeheader(line[header_column])

                if reportType == 2:#подкатегория "тип оплаты"
                    if i == 0 or report[i-1][header_column] != report[i][header_column] or report[i-1][4] != report[i][4]:
                        writeheader(line[4], True)

                writeline(line, body_columns)

                if reportType == 2:
                    if i == len(report) - 1 or report[i][header_column] != report[i+1][header_column] or report[i][4] != report[i + 1][4]:
                        writetotal(4, i+1, 5) #пишет итог по 4й и 5й колонке, т.е. Тип оплаты и Лаборатории

                if i == len(report) - 1 or report[i][header_column] != report[i+1][header_column]:
                    writetotal(header_column, i+1)
            writetotalf()

        return doc
