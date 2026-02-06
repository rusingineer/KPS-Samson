# -*- coding: utf-8 -*-

from PyQt4 import QtGui

from Reports.Report import CReport, createTable
from Reports.ReportBase import CReportBase

from library.Utils import forceString, forceInt, forceDate, forceDouble
from EconomicAnalisysSetupDialog import CEconomicAnalisysSetupDialog, getCond


class CEconomicAnalisysP11(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'П11. Список персональных счетов, не принятых к оплате.')

    def selectData(self, params):
        stmt = u"""
            SELECT
            Event.id as eventid,
            Event.execDate as execdate,
            Client.id as clientid,
            concat_ws(' ',Client.lastName, Client.firstName, Client.patrName) as fio,
            Client.birthDate as birthdate,
            concat_ws(' ',Person.lastName, concat(substr(Person.firstName,1,1),'.'),
                concat(substr(Person.patrName,1,1),'.')) as wrach,
            rbPayRefuseType.code as refcode,
            rbPayRefuseType.name as refname,
            sum(Account_Item.sum) as sum
            FROM Event
            left join EventType on EventType.id = Event.eventType_id
            left join Account_Item on Account_Item.event_id = Event.id
            left join Account on Account.id = Account_Item.master_id
            left join Client on Client.id = Event.client_id
            left join Person on Person.id = Event.execPerson_id
            left join rbSpeciality on rbSpeciality.id = Person.speciality_id
            left join OrgStructure on OrgStructure.id = Person.orgStructure_id
            left join rbPayRefuseType on rbPayRefuseType.id = Account_Item.refuseType_id
            left join Action on Account_Item.action_id = Action.id
            LEFT JOIN Contract ON Contract.id = IFNULL(Action.contract_id, Event.contract_id)
                and Contract.deleted = 0 and Contract.finance_id = Action.finance_id
            left join ClientPolicy on ClientPolicy.id = getClientPolicyIdForDate(Client.id, 1, Event.execDate, Event.id)
            left join Organisation AS Insurer ON Insurer.id = ClientPolicy.insurer_id
            left join Organisation as Payer on Payer.id =
                IFNULL((select max(id) from Organisation o where o.OGRN = Insurer.OGRN and o.deleted = 0 and o.isInsurer = 1
                and o.OKATO = Insurer.OKATO and Insurer.OKATO = '03000' and o.head_id is null), Contract.payer_id)
            LEFT JOIN rbFinance on rbFinance.id = COALESCE(Action.finance_id, Contract.finance_id)
            where
            Account.deleted = 0 and Account_Item.deleted = 0 and Event.deleted = 0 and
            Account_Item.refuseType_id is not null and Account_Item.reexposeItem_id is null
            and {cond}
            group by Event.id
            order by Event.id ASC
        """
        db = QtGui.qApp.db
        return db.query(stmt.format(cond=getCond(params)))

    def build(self, description, params):
        reportData = {}
        columnCount = 8
        # склонение числительных

        def declOfNum(number, titles):
            cases = [2, 0, 1, 1, 1, 2]
            return titles[2 if (number % 100 > 4 and number % 100 < 20) else cases[number % 10 if (number % 10 < 5) else 5]]

        def processQuery(query):
            while query.next():
                record = query.record()
                eventid = forceInt(record.value('eventid'))
                execdate = forceDate(record.value('execdate'))
                clientid = forceInt(record.value('clientid'))
                fio = forceString(record.value('fio'))
                birthdate = forceDate(record.value('birthdate'))
                wrach = forceString(record.value('wrach'))
                refcode = forceString(record.value('refcode'))
                refname = forceString(record.value('refname'))
                sum = forceDouble(record.value('sum'))

                key = eventid
                reportLine = reportData.setdefault(key, [0] * columnCount)
                reportLine[0] = execdate
                reportLine[1] = clientid
                reportLine[2] = fio
                reportLine[3] = birthdate
                reportLine[4] = wrach
                reportLine[5] = refcode
                reportLine[6] = refname
                reportLine[7] = sum

        query = self.selectData(params)
        processQuery(query)

        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertText(description)
        cursor.insertBlock()
        boldChars = QtGui.QTextCharFormat()
        boldChars.setFontWeight(QtGui.QFont.Bold)
        tableColumns = [
            ('5%', [u'№ Талона'], CReportBase.AlignCenter),
            ('8%', [u'Дата талона'], CReportBase.AlignCenter),
            ('5%', [u'Код пациента'], CReportBase.AlignCenter),
            ('15%', [u'ФИО'], CReportBase.AlignLeft),
            ('8%', [u'Дата рождения'], CReportBase.AlignCenter),
            ('10%', [u'Ответственный врач'], CReportBase.AlignLeft),
            ('auto', [u'Причина возврата', u'Код'], CReportBase.AlignCenter),
            ('auto', [u'', u'Наименование'], CReportBase.AlignLeft),
            ('5%', [u'Сумма'], CReportBase.AlignLeft)
            ]

        table = createTable(cursor, tableColumns)

        table.mergeCells(0, 6, 1, 2)
        table.mergeCells(0, 0, 2, 1)
        table.mergeCells(0, 1, 2, 1)
        table.mergeCells(0, 2, 2, 1)
        table.mergeCells(0, 3, 2, 1)
        table.mergeCells(0, 4, 2, 1)
        table.mergeCells(0, 5, 2, 1)
        table.mergeCells(0, 8, 2, 1)
        colsShift = 1
        keys = reportData.keys()
        keys.sort()
        sum = 0
        for key in keys:
            eventid = key
            reportLine = reportData[key]
            row = table.addRow()
            table.setText(row, 0, eventid)
            for col in xrange(columnCount):
                # 0,3 - dates
                text = reportLine[col]
                if col == 0 or col == 3:
                    text = text.toString(u'dd.MM.yyyy')
                table.setText(row, col + colsShift, text)
            sum += reportLine[7]
        row = table.addRow()
        table.mergeCells(row, 0, 1, 9)
        text = declOfNum(len(keys), [u' возвращен {0:d} персональный счет',
                         u' возвращено {0:d} персональных счета',
                                     u' возвращено {0:d} персональных счетов'])
        text = u'Итого' + text + u' на сумму {1:0.2f}'
        text = text.format(len(keys), sum)
        table.setText(row, 0, text, charFormat=boldChars, blockFormat=CReportBase.AlignLeft)
        return doc


class CEconomicAnalisysP11Ex(CEconomicAnalisysP11):
    def exec_(self, accountIdList=None):
        self.accountIdList = accountIdList
        CEconomicAnalisysP11.exec_(self)

    def getSetupDialog(self, parent):
        result = CEconomicAnalisysSetupDialog(parent)
        result.lblScheta.hide()
        result.cmbScheta.hide()
        result.cbPrice.hide()
        result.setTitle(self.title())
        result.shrink()
        result.loadPrefs()
        return result

    def build(self, params):
        params['accountIdList'] = self.accountIdList
        return CEconomicAnalisysP11.build(self, '\n'.join(self.getDescription(params)), params)
