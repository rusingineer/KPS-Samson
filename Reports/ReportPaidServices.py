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
from Reports.Report import CReport
from Reports.ReportBase import *
from Ui_ReportPaidServices import Ui_ReportPaidServicesDialog
from library.Utils import forceString, forceInt, forceDouble, forceDate
from Events.Utils import getWorkEventTypeFilter


class CReportPaidServicesSetupDialog(QtGui.QDialog, Ui_ReportPaidServicesDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.cmbEventType.setTable('EventType', True, filter=getWorkEventTypeFilter())

    def setParams(self, params):
        self.edtBegDate.setDate(params.get('begDate', QDate.currentDate()))
        self.edtEndDate.setDate(params.get('endDate', QDate.currentDate()))

        self.edtCustomDate.setDate(params.get('customDate', QDate.currentDate()))
        self.edtCustomTime.setTime(params.get('customTime', QTime.currentTime()))

        self.cmbPerson.setValue(params.get('personId', None))

        self.cmbEventType.setValue(params.get('eventTypeId', None))
        typePayment = params.get('typePayment', None)
        if typePayment is None:
            self.cmbTypePayment.setCurrentIndex(0)
        else:
            self.cmbTypePayment.setCurrentIndex(params['typePayment'] + 1)
        self.cmbPatient.setValue(params.get('clientId', None))

        reportType = params.get('reportType', 0)
        self.rbPayment.setChecked(0 == reportType)
        self.rbPatient.setChecked(1 == reportType)
        self.rbPerson.setChecked(2 == reportType)
        self.rbService.setChecked(3 == reportType)
        self.cmbService.setValue(params.get('serviceId', None))

    def params(self):
        result = {}
        result['begDate'] = self.edtBegDate.date()
        result['endDate'] = self.edtEndDate.date()
        result['customDate'] = self.edtCustomDate.date()
        result['customTime'] = self.edtCustomTime.time()
        result['personId'] = self.cmbPerson.value()
        result['eventTypeId'] = self.cmbEventType.value()
        result['typePayment'] = [None, 0, 1, 2][self.cmbTypePayment.currentIndex()]
        result['clientId'] = self.cmbPatient.value()
        result['reportType'] = [self.rbPayment.isChecked(), self.rbPatient.isChecked(), self.rbPerson.isChecked(), self.rbService.isChecked()].index(True)
        result['serviceId'] = self.cmbService.value()
        return result


class CReportPaidServices(CReport):
    def __init__(self, parent=None):
        CReport.__init__(self, parent)
        self.setTitle(u'Отчет по платным услугам')
        self.tableColumns = []

        # Выбираем нужные столбцы под каждую таблицу
        # можем указать свою колонку для которой будет отдельная обработка в processQuery() 'cust_summ'
        # В первую очередь указываем столбцы для таблицы, потом уже доп столбцы если нужны
        self.body_columns = [
            ['client', 'service', 'amount', 'cust_summ', 'sum', 'PaymentType'],
            ['client', 'birthDate', 'service', 'amount', 'sum', 'PaymentType', 'pAmountSumm'],
            ['person', 'service', 'amount', 'sum', 'PaymentType'],
            ['service', 'amount', 'cust_summ', 'sum', 'PaymentType'],
        ]

        # Указываем что какого типа нам нужно в processQuery()
        self.list_forceInt = ['amount']
        self.list_forceDouble = ['sum']
        self.list_forceDate = ['date', 'birthDate', 'pbirthDate']
        self.list_forceString = ['service', 'client', 'person', 'PaymentType']

    def getSetupDialog(self, parent):
        return CReportPaidServicesSetupDialog(parent)


    def selectData(self, params):
        db = QtGui.qApp.db
        reportType = params.get('reportType', 0)

        stmt = ''

        person = 'concat_ws(" ",p.lastName, p.firstName, p.patrName) as person, p.birthDate as pbirthDate,'
        personJoin = ' LEFT JOIN Person p ON p.id = Action.person_id'

        if reportType == 1:
            client = 'Client.birthDate AS birthDate,'
        else:
            client = ''
        if reportType == 0:
            number_Contract = 'Event_LocalContract.numberContract as numb_dogovor,'
        else:
            number_Contract = ''

        stmt += u'''
SELECT distinct
    Event.id,
    concat_ws(" ",{0}.lastName, {0}.firstName, {0}.patrName) as client,
    %(client)s
    %(person)s
    %(number_Contract)s
    IF(co.code = 2 ,sum(IF(Account_Item.refuseType_id IS NULL AND co.code = 1, 1, Account_Item.refuseType_id IS not NULL AND co.code = 2)), sum(Account_Item.amount)) as amount,
   -- IF(IF(co.name='Возврат', Event_Payment.sum, 0) = 0, IF(SUM(Account_Item.payedSum)=0,Account_Item.sum,SUM(Account_Item.payedSum)), ABS(Event_Payment.sum))    AS sum,
      IF(sum(IF (Account_Item.refuseType_id IS not NULL AND co.code = 2, Account_Item.sum, 0))=0, sum(Account_Item.sum), sum(IF (Account_Item.refuseType_id IS not NULL AND co.code = 2, Account_Item.sum, 0)))   AS sum,
    ifnull(Event_Payment.date, Account_Item.date) as date,
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
%(personJoin)s
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

''' % {
            'client' :client,
            'person' : person,
            'number_Contract': number_Contract,
            'personJoin': personJoin
        }

        stmt += [
            u'group by PaymentType, co.code, Event_LocalContract.id, Event_Payment.id HAVING amount>0 order by PaymentType, co.code, client, service',
            u'group by Client.id, rbService.id, co.id HAVING amount>0 order BY PaymentType, client, birthDate',
            u'group by service, rbService.id, co.id HAVING amount>0 order BY PaymentType, person, service',
            u'group by service, rbService.id,co.id HAVING amount>0 order by PaymentType, service, amount',
            ][reportType]

        cond = []
        cond.append(u'ifnull(Event_Payment.date, Account_Item.date) between "%s" and "%s"' %
                    (params['begDate'].toString('yyyy-MM-dd'), params['endDate'].toString('yyyy-MM-dd'))
                    )
        if params.get('eventTypeId', False):
            cond.append(u'Event.eventType_id IN (%s)' % params['eventTypeId'])
        if params.get('typePayment', False) is not None:
            cond.append(u'Event_Payment.typePayment IN (%s)' % params['typePayment'])
        if params.get('clientId', False) and reportType != 0:
            cond.append(u'Client.id = %s' % params['clientId'])
        if params.get('serviceId', False):
            cond.append(u'rbService.id = %s' % params['serviceId'])
        if params.get('personId', False):
            cond.append(u'p.id = %s' % params['personId'])

        st = stmt.format("Event_LocalContract" if reportType == 0 else "Client",
                         "Event_LocalContract on Event_LocalContract.master_id = Event.id" if reportType == 0 else "Client on Client.id = Event.client_id",
                         cond=" and ".join(cond))

        return db.query(st)


    def getTableColumns(self, reportType):
        # Тип оплаты
        if reportType == 0:
            tableColumns = [
                ('3%', u'№', CReportBase.AlignCenter),
                ('42%', [u'Тип оплаты/пациент'], CReportBase.AlignLeft),
                ('15%', [u'Кол-во услуг'], CReportBase.AlignLeft),
                ('20%', [u'Дата оплаты'], CReportBase.AlignLeft),
                ('20%', [u'Сумма'], CReportBase.AlignLeft),
            ]

        # Пациентам
        elif reportType == 1:
            tableColumns = [
                ('3%', u'№', CReportBase.AlignCenter),
                ('17%', [u'ФИО'], CReportBase.AlignLeft),
                ('5%',  [u'Дата рождения'], CReportBase.AlignLeft),
                ('65%', [u'Наименование услуги'], CReportBase.AlignLeft),
                ('5%',  [u'Кол-во услуг'], CReportBase.AlignLeft),
                ('5%',  [u'Сумма'], CReportBase.AlignLeft),
            ]

        # Исполнителю
        elif reportType == 2:
            tableColumns = [
                ('3%', [u'№'], CReportBase.AlignCenter),
                ('17%', [u'Исполнитель'], CReportBase.AlignLeft),
                ('70%', [u'Наименивание услуги'], CReportBase.AlignLeft),
                ('5%', [u'Кол-во услуг'], CReportBase.AlignLeft),
                ('5%', [u'Сумма'], CReportBase.AlignLeft),
            ]

        # Услугам
        elif reportType == 3:
            tableColumns = [
                ('3%', u'№', CReportBase.AlignCenter),
                ('82%', [u'Наименование услуги'], CReportBase.AlignLeft),
                ('5%',  [u'Кол-во услуг'], CReportBase.AlignLeft),
                ('5%',  [u'Стоимость'], CReportBase.AlignLeft),
                ('5%',  [u'Сумма'], CReportBase.AlignLeft),
            ]

        self.tableColumns = tableColumns
        return tableColumns


    def processQuery(self, query, reportType):
        report = []

        while query.next():
            reportLine = []

            for col in self.body_columns[reportType]:
                record = query.record()

                if col in self.list_forceInt:
                    val = forceInt(record.value(col))
                elif col in self.list_forceDouble:
                    val = forceDouble(record.value(col))
                elif col in self.list_forceDate:
                    val = forceDate(record.value(col)).toString('dd.MM.yyyy')
                elif col in self.list_forceString:
                    val = forceString(record.value(col))

                if col == 'cust_summ':
                    amount = forceInt(record.value('amount'))
                    sum = forceDouble(record.value('sum'))
                    if amount != 1:
                        val = float(sum) / float(amount)
                    else:
                        val = sum

                reportLine.append(val)

            if reportLine != []:
                report.append(reportLine)

        return report


    def getReportType1(self, table, report):
        all_sum      = 0    # Текущая сумма оплаты
        all_amount   = 0    # Текущее количество услуг

        person = ''         # Текущий человек ФИО

        all_sum2      = 0    # Общая сумма оплаты
        all_amount2   = 0    # Общая сумма услуг

        all_typeCash_sum2 = 0    # Общая сумма сумм которые вернули
        all_typeCash_amount2 = 0 # Общее количество услуг которые отменили

        PaymentType = ''  # Текущий тип оплаты


        # Вызываем указывая сколько нужно пустых строк
        def emptyLines(x):
            row = table.addRow()
            for i in xrange(x):
                table.setText(row, i, forceString(u"   "))


        # report - список со списками
        # list1 - список который должен совпасть с report[i] | к примеру ['Врач', 'Вакцина №1']
        # list2 - список того что нужно подсчитать (общую сумму)
        # l.append(i[self.body_columns[1].index(x)]) - 1 - индекс таблицы
        def giveMeTotal(report, list1, list2):
            memory = []
            for i in report:
                if all(element in i for element in list1):
                    l = []
                    for x in list2:
                        l.append(i[self.body_columns[1].index(x)])
                    memory.append(l)
            return memory


        x = 1 # Нумерация
        for r in report:

            if r[5] != PaymentType:
                if PaymentType != '':
                    row = table.addRow()
                    for _ in xrange(3): table.setText(row, _, forceString(u'  ')) # Пустые строки
                    table.setText(row, 3, forceString(u'{0} Итого:'.format(PaymentType)), fontBold=True)
                    table.setText(row, 4, forceString(all_amount), fontBold=True)
                    table.setText(row, 5, forceString(all_sum), fontBold=True)

                    emptyLines(5)

                x = 1
                all_sum = 0
                all_amount = 0
                PaymentType = r[5]

                row = table.addRow()
                table.setText(row, 0, forceString(u"   "))
                table.setText(row, 1, forceString(r[5]), fontBold=True)
                table.setText(row, 2, forceString(u"   "))
                table.setText(row, 3, forceString(u"   "))
                table.setText(row, 4, forceString(u"   "))
                table.setText(row, 5, forceString(u"   "))



            if r[0] != person:
                person = r[0]
                row = table.addRow()
                table.setText(row, 0, forceString(x))
                table.setText(row, 1, forceString(r[0]), fontBold=True)
                table.setText(row, 2, forceString(r[1]), fontBold=True)
                table.setText(row, 3, forceString(u"   "))

                li = giveMeTotal(report, [r[0], r[1], r[5]], ['amount', 'sum'])
                sums1 = sum(sublist[0] for sublist in li)
                sums2 = sum(sublist[1] for sublist in li)

                table.setText(row, 4, forceString(sums1), fontBold=True)
                table.setText(row, 5, forceString(sums2), fontBold=True)

                x+= 1

                row = table.addRow()
                for _ in xrange(3): table.setText(row, _, forceString(u'  ')) # Пустые строки
                table.setText(row, 3, forceString(r[2]))
                table.setText(row, 4, forceString(r[3]))
                table.setText(row, 5, forceString(r[4]))
            else:
                row = table.addRow()
                for _ in xrange(3): table.setText(row, _, forceString(u'  ')) # Пустые строки
                table.setText(row, 3, forceString(r[2]))
                table.setText(row, 4, forceString(r[3]))
                table.setText(row, 5, forceString(r[4]))

            all_sum += float(r[4])
            all_amount += int(r[3])

            if u'оплата' in r[5]:
                all_sum2 += float(r[4])
                all_amount2 += int(r[3])

            if u'возврат' in r[5]:
                all_typeCash_sum2 += float(r[4])
                all_typeCash_amount2 += int(r[3])


        row = table.addRow()
        for _ in xrange(3): table.setText(row, _, forceString(u'  ')) # Пустые строки
        table.setText(row, 3, forceString(u'{0} Итого:'.format(PaymentType)), fontBold=True)
        table.setText(row, 4, forceString(all_amount), fontBold=True)
        table.setText(row, 5, forceString(all_sum), fontBold=True)

        emptyLines(5)

        row = table.addRow()
        for _ in xrange(3): table.setText(row, _, forceString(u'  ')) # Пустые строки
        table.setText(row, 3, forceString(u'Всего:'), fontBold=True)
        table.setText(row, 4, forceString(all_amount2), fontBold=True)
        table.setText(row, 5, forceString(all_sum2), fontBold=True)

        emptyLines(5)

        row = table.addRow()
        for _ in xrange(3): table.setText(row, _, forceString(u'  ')) # Пустые строки
        table.setText(row, 3, forceString(u'Всего возврата:'), fontBold=True)
        table.setText(row, 4, forceString(all_typeCash_amount2), fontBold=True)
        table.setText(row, 5, forceString(all_typeCash_sum2), fontBold=True)

        emptyLines(5)

        row = table.addRow()
        table.setText(row, 0, forceString(u'  '))
        table.setText(row, 1, forceString(u'Итого:'), fontBold=True)
        table.setText(row, 2, forceString(u'   '))
        table.setText(row, 3, forceString(u'   '))
        table.setText(row, 4, forceString(int(all_amount2) - int(all_typeCash_amount2)), fontBold=True)
        table.setText(row, 5, forceString(float(all_sum2) - float(all_typeCash_sum2)), fontBold=True)

        return table


    def getReportType2(self, table, report):
        all_sum      = 0    # Текущая сумма оплаты
        all_amount   = 0    # Текущее количество услуг

        person = ''         # Текущий человек ФИО

        all_sum2      = 0    # Общая сумма оплаты
        all_amount2   = 0    # Общая сумма услуг

        all_typeCash_sum2 = 0    # Общая сумма сумм которые вернули
        all_typeCash_amount2 = 0 # Общее количество услуг которые отменили

        PaymentType = ''  # Текущий тип оплаты

        # описание в getReportType1()
        def emptyLines(x):
            row = table.addRow()
            for i in xrange(x):
                table.setText(row, i, forceString(u"   "))

        # описание в getReportType1()
        def giveMeTotal(report, list1, list2):
            memory = []
            for i in report:
                if all(element in i for element in list1):
                    l = []
                    for x in list2:
                        l.append(i[self.body_columns[2].index(x)])
                    memory.append(l)
            return memory

        x = 1 # Нумерация
        for r in report:

            if r[4] != PaymentType:
                if PaymentType != '':
                    row = table.addRow()
                    table.setText(row, 0, forceString(u'  '))
                    table.setText(row, 1, forceString(u'{0} Итого:'.format(PaymentType)), fontBold=True)
                    table.setText(row, 2, forceString(u'    '))
                    table.setText(row, 3, forceString(u'   '))
                    table.setText(row, 4, forceString(all_sum), fontBold=True)

                    emptyLines(5)

                x = 1
                all_sum = 0
                PaymentType = r[4]

                row = table.addRow()
                table.setText(row, 0, forceString(u"   "))
                table.setText(row, 1, forceString(r[4]), fontBold=True)
                table.setText(row, 2, forceString(u"   "))
                table.setText(row, 3, forceString(u"   "))
                table.setText(row, 4, forceString(u"   "))


            if r[0] != person:
                person = r[0]
                row = table.addRow()
                table.setText(row, 0, forceString(x))
                table.setText(row, 1, forceString(r[0]), fontBold=True)
                table.setText(row, 2, forceString(u"   "))

                li = giveMeTotal(report, [r[0], r[4]], ['amount', 'sum'])
                sums1 = sum(sublist[0] for sublist in li)
                sums2 = sum(sublist[1] for sublist in li)

                table.setText(row, 3, forceString(sums1), fontBold=True)
                table.setText(row, 4, forceString(sums2), fontBold=True)

                x += 1

                row = table.addRow()
                table.setText(row, 0, forceString(u"   "))
                table.setText(row, 1, forceString(u"   "))
                table.setText(row, 2, forceString(r[1]))
                table.setText(row, 3, forceString(r[2]))
                table.setText(row, 4, forceString(r[3]))
            else:
                row = table.addRow()
                table.setText(row, 0, forceString(u"   "))
                table.setText(row, 1, forceString(u"   "))
                table.setText(row, 2, forceString(r[1]))
                table.setText(row, 3, forceString(r[2]))
                table.setText(row, 4, forceString(r[3]))

            all_sum += float(r[3])
            all_amount += int(r[2])

            if u'оплата' in r[4]:
                all_sum2 += float(r[3])
                all_amount2 += int(r[2])

            if u'возврат' in r[4]:
                all_typeCash_sum2 += float(r[3])
                all_typeCash_amount2 += int(r[2])

        row = table.addRow()
        table.setText(row, 0, forceString(u'  '))
        table.setText(row, 1, forceString(u'{0} Итого:'.format(PaymentType)), fontBold=True)
        table.setText(row, 2, forceString(u'   '))
        table.setText(row, 3, forceString(u'   '))
        table.setText(row, 4, forceString(all_sum), fontBold=True)

        emptyLines(5)

        row = table.addRow()
        table.setText(row, 0, forceString(u'  '))
        table.setText(row, 1, forceString(u'Всего:'), fontBold=True)
        table.setText(row, 2, forceString(u'     '))
        table.setText(row, 3, forceString(all_amount2), fontBold=True)
        table.setText(row, 4, forceString(all_sum2), fontBold=True)

        emptyLines(5)

        row = table.addRow()
        table.setText(row, 0, forceString(u'  '))
        table.setText(row, 1, forceString(u'Всего возврата:'), fontBold=True)
        table.setText(row, 2, forceString(u'    '))
        table.setText(row, 3, forceString(all_typeCash_amount2), fontBold=True)
        table.setText(row, 4, forceString(all_typeCash_sum2), fontBold=True)

        emptyLines(5)

        row = table.addRow()
        table.setText(row, 0, forceString(u'  '))
        table.setText(row, 1, forceString(u'Итого:'), fontBold=True)
        table.setText(row, 2, forceString(u'   '))
        table.setText(row, 3, forceString(int(all_amount2) - int(all_typeCash_amount2)), fontBold=True)
        table.setText(row, 4, forceString(float(all_sum2) - float(all_typeCash_sum2)), fontBold=True)

        return table


    def getReportType3(self, table, report):
        all_sum      = 0    # Текущая сумма оплаты
        all_amount   = 0    # Текущее количество услуг

        all_sum2      = 0    # Общая сумма оплаты
        all_amount2   = 0    # Общая сумма услуг

        all_typeCash_sum2 = 0    # Общая сумма сумм которые вернули
        all_typeCash_amount2 = 0 # Общее количество услуг которые отменили

        PaymentType = ''  # Текущий тип оплаты

        # описание в getReportType1()
        def emptyLines(x):
            row = table.addRow()
            for i in xrange(x):
                table.setText(row, i, forceString(u"   "))

        x = 1 # Нумерация
        for r in report:

            if r[4] != PaymentType:
                if PaymentType != '':
                    row = table.addRow()
                    table.setText(row, 0, forceString(u'  '))
                    table.setText(row, 1, forceString(u'{0} Итого:'.format(PaymentType)), fontBold=True)
                    table.setText(row, 2, forceString(all_amount), fontBold=True)
                    table.setText(row, 3, forceString(u'   '))
                    table.setText(row, 4, forceString(all_sum), fontBold=True)

                    emptyLines(5)

                x = 1
                all_sum = 0
                all_amount = 0
                PaymentType = r[4]

                row = table.addRow()
                table.setText(row, 0, forceString(u"   "))
                table.setText(row, 1, forceString(r[4]), fontBold=True)
                table.setText(row, 2, forceString(u"   "))
                table.setText(row, 3, forceString(u"   "))
                table.setText(row, 4, forceString(u"   "))

            row = table.addRow()
            table.setText(row, 0, forceString(x))
            table.setText(row, 1, forceString(r[0]))
            table.setText(row, 2, forceString(r[1]))
            table.setText(row, 3, forceString(r[2]))
            table.setText(row, 4, forceString(r[3]))

            x += 1

            all_sum += float(r[3])
            all_amount += int(r[1])

            if u'оплата' in r[4]:
                all_sum2 += float(r[3])
                all_amount2 += int(r[1])

            if u'возврат' in r[4]:
                all_typeCash_sum2 += float(r[3])
                all_typeCash_amount2 += int(r[1])

        row = table.addRow()
        table.setText(row, 0, forceString(u'  '))
        table.setText(row, 1, forceString(u'{0} Итого:'.format(PaymentType)), fontBold=True)
        table.setText(row, 2, forceString(all_amount), fontBold=True)
        table.setText(row, 3, forceString(u'   '))
        table.setText(row, 4, forceString(all_sum), fontBold=True)

        emptyLines(5)

        row = table.addRow()
        table.setText(row, 0, forceString(u'  '))
        table.setText(row, 1, forceString(u'Всего оплаченно:'), fontBold=True)
        table.setText(row, 2, forceString(all_amount2), fontBold=True)
        table.setText(row, 3, forceString(u'   '))
        table.setText(row, 4, forceString(all_sum2), fontBold=True)

        emptyLines(5)

        row = table.addRow()
        table.setText(row, 0, forceString(u'  '))
        table.setText(row, 1, forceString(u'Всего возврата:'), fontBold=True)
        table.setText(row, 2, forceString(all_typeCash_amount2), fontBold=True)
        table.setText(row, 3, forceString(u'   '))
        table.setText(row, 4, forceString(all_typeCash_sum2), fontBold=True)

        emptyLines(5)

        row = table.addRow()
        table.setText(row, 0, forceString(u'  '))
        table.setText(row, 1, forceString(u'Итого:'), fontBold=True)
        table.setText(row, 2, forceString(int(all_amount2) - int(all_typeCash_amount2)), fontBold=True)
        table.setText(row, 3, forceString(u'   '))
        table.setText(row, 4, forceString(float(all_sum2) - float(all_typeCash_sum2)), fontBold=True)

        return table


    def build(self, params):
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
        tableColumns = self.getTableColumns(reportType)
        table = createTable(cursor, tableColumns)

        query = self.selectData(params)

        report = []

        if reportType != 0:
            report = self.processQuery(query, reportType)

        # Копипаст
        if reportType == 0:
            self.clientComing = 0
            self.clientRefund = 0
            self.reportType = params.get('reportType', 0)
            def processQuery(query):
                while query.next():
                    reportLine = []
                    for col in ['client', 'amount', 'date', 'sum', 'PaymentType', 'lab', 'service', 'service_id']:
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

            processQuery(query)

            # Код из PaidServices.py у Жени взял
            body_columns = [[0, 1, 2, 3]][0]
            header_column = [4, 0, 5][0]
            flagS = None
            flagSE = None
            sumNal = []
            sumEl = []
            sumVNal = []
            sumVEl = []

            def writeline(line, columns):
                for i, col in enumerate(columns):
                    text = line[col]
                    if i == 0:
                        text = u'  ' + line[col]
                    table.setText(row, i + 1, text)

            def writetotal(col, index, optionalCol=None):
                _report = report[:index]
                title = _report[-1][col]

                sum = [None] * len(report[0])
                if optionalCol:
                    optionalTitle = _report[-1][optionalCol]  # опциональная колонка для подсчета

                for i in reversed(_report):
                    if i[col] != title:  # считаем сумму пока строка соответсвтует заголовку, например "Наличная оплата"
                        break
                    if optionalCol and i[
                        optionalCol] != optionalTitle:  # дополнительный заголовок, например "Лаборатория такая-то"
                        break
                    for j, _col in enumerate(i):
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
                            table.setText(row, 0, u'  "%s" - всего' % title , blockFormat=CReportBase.AlignLeft)
                        elif title == u'Наличная оплата':
                            table.setText(row, 0, '"%s"' % title, blockFormat=CReportBase.AlignLeft)
                        else:
                            table.setText(row, 0, u'  "%s" - приход' % title , blockFormat=CReportBase.AlignLeft)
                    elif c != None:
                        if title == u'Наличная оплата':
                            sumNal.append(c)
                        elif title == u'Электронная оплата':
                            sumEl.append(c)
                        elif title == u'Наличный возврат':
                            sumVNal.append(c)
                        else:
                            sumVEl.append(c)
                        table.setText(row, i + 1, c)

            def writetotalf():
                if len(report) == 0:
                    return
                sumV1 = 0
                sumV2 = 0
                sum = [None] * len(report[0])
                for i in report:
                    for j, _col in enumerate(i):
                        if type(_col) in [float, int]:  # and u'возврат' not in i[4]:
                            if sum[j] is None:
                                sum[j] = 0
                            if u'возврат' not in i[4]:
                                sum[j] += _col
                            else:
                                if j == 1:
                                    sumV1 += _col
                                elif j == 3:
                                    sumV2 += _col
                                sum[j] -= _col

                row = table.addRow()
                table.setText(row, 0, u'Приход', blockFormat=CReportBase.AlignLeft)
                tempSumNC = sumNal[1] if sumNal else 0
                tempSumElC = sumEl[1] if sumEl else 0
                tempSumN = sumNal[2] if sumNal else 0
                tempSumEl = sumEl[2] if sumEl else 0
                table.setText(row, 2, tempSumNC + tempSumElC)
                table.setText(row, 4, tempSumN + tempSumEl)
                table.mergeCells(row, 0, 1, 2)
                row = table.addRow()
                table.setText(row, 0, u'Возврат', blockFormat=CReportBase.AlignLeft)
                table.setText(row, 2, sumV1)
                table.setText(row, 4, sumV2)
                table.mergeCells(row, 0, 1, 2)

                row = table.addRow()
                for i, c in enumerate(sum):
                    if i == 0:
                        table.mergeCells(row, 0, 1, 2)
                        # table.setText(row, 0, u'  Итого ' + h1 + u' ' + h2 + u' ' + h3 + u' ' + h4,
                        #               )
                        table.setText(row, 0, u'  Итого ', blockFormat=CReportBase.AlignLeft)

                    elif c != None:
                        table.mergeCells(row, 0, 1, 2)
                        table.setText(row, i + 1, c)

            def writeheader(header, isSubHeader=False):
                row = table.addRow()
                text = header
                if isSubHeader:
                    text = u" " + text
                table.mergeCells(row, 0, 1, 2)
                table.setText(row, 1, text)

            d = 0
            h1 = u'Наличная оплата 0'
            h2 = u'Наличный возврат 0'
            h3 = u'Электронная оплата 0'
            h4 = u'Электронный возврат 0'
            for i, line in enumerate(report):
                if i == 0 or report[i - 1][header_column] != report[i][header_column]:
                    if u'Наличн' not in line[header_column] and flagS is None:
                        if sumNal:
                            row = table.addRow()
                            table.setText(row, 0, sumNal[0], blockFormat=CReportBase.AlignLeft)
                            table.setText(row, 2, sumNal[1] - sumVNal[0] if sumVNal else sumNal[1] - 0)
                            table.setText(row, 4, sumNal[2] - sumVNal[1] if sumVNal else sumNal[2] - 0)
                            table.mergeCells(row, 0, 1, 2)
                        flagS = True
                    d = 0
                    writeheader(line[header_column])

                if reportType == 2:  # подкатегория "тип оплаты"
                    if i == 0 or report[i - 1][header_column] != report[i][header_column] or report[i - 1][4] != \
                            report[i][4]:
                        writeheader(line[4], True)

                row = table.addRow()
                d += 1
                table.setText(row, 0, d, blockFormat=CReportBase.AlignLeft)
                writeline(line, body_columns)

                if i == len(report) - 1 or report[i][header_column] != report[i + 1][header_column]:
                    writetotal(header_column, i + 1)

            if sumNal:
                h1 = u'Наличная оплата' + u' ' + str(sumNal[1])
            if sumVNal:
                h1 = u'Наличная оплата' + u' ' + str(sumNal[1] - sumVNal[0])
                h2 = u'Наличный возврат' + u' ' + str(sumVNal[0])
            if sumEl:
                h3 = u'Электронная оплата' + u' ' + str(sumEl[1])
            if sumVEl:
                h3 = u'Электронная оплата' + u' ' + str(sumEl[1] - sumVEl[0])
                h4 = u'Электронный возврат' + u' ' + str(sumVEl[0])

            if flagS is None and sumNal:
                row = table.addRow()
                table.setText(row, 0, sumNal[0], blockFormat=CReportBase.AlignLeft)
                table.setText(row, 2, sumNal[1] - sumVNal[0] if sumVNal else sumNal[1] - 0)
                table.setText(row, 4, sumNal[2] - sumVNal[1] if sumVNal else sumNal[2] - 0)
                table.mergeCells(row, 0, 1, 2)

            if flagSE is None and sumEl:
                row = table.addRow()
                table.setText(row, 0, sumEl[0], blockFormat=CReportBase.AlignLeft)
                table.setText(row, 2, sumEl[1] - sumVEl[0] if sumVEl else sumEl[1] - 0)
                table.setText(row, 4, sumEl[2] - sumVEl[1] if sumVEl else sumEl[2] - 0)
                table.mergeCells(row, 0, 1, 2)

            writetotalf()

        elif reportType == 1:
            table = self.getReportType1(table, report)
        elif reportType == 2:
            table = self.getReportType2(table, report)
        elif reportType == 3:
            table = self.getReportType3(table, report)

        return doc

