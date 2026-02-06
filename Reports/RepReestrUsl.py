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
from Reports.Report import *
from Reports.ReportBase import *
from library.AmountToWords import amountToWords
from library.Utils import *
from EconomicAnalisysSetupDialog import *


class CRepReestrUsl(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Реестр выполненных услуг')

    def selectData(self, params):
        stmt = u"""
   select     
       q.dat,q.kvit, q.fioP,q.fio,%(cond2)s
      q.cli_,
      SUM(isPos) AS pos,
      SUM(isObr) AS obr,
      SUM(isProf) AS prof,
      SUM(q.usl) as usl,
			round(sum(q.uet),2) as uet, 
			round(sum(q.sum),2) as sum,
            round(q.sum1,2) as sum1,q.event_id as event_id
    from 
      (select Event.id as event_id,Client.id as cli_,Event.externalId AS kvit,date(Event.execDate) AS dat,
      concat(Person.lastName,' ',Person.firstName,' ',Person.patrName) AS fioP,
        concat(Client.lastName,' ',Client.firstName,' ',Client.patrName) AS fio,
       %(os)s 
      isPos(rbService.infis, rbService.name, mt.regionalCode) as isPos,
      IF(rbService.name like 'Обращение%%', 1, 0) AS isObr,
      IF(rbService.infis LIKE 'B04%%', 1, 0) as isProf,
      IFNULL(Account_Item.uet, vAction.amount * ct.uet) as uet,
		  IFNULL(Account_Item.sum, vAction.amount * ct.price) as sum,
          sum(Event_Payment.sum) as sum1,
        vAction.amount AS usl
    from vAction
    left join Event on Event.id = vAction.event_id
    left join Account_Item on Account_Item.action_id = vAction.id and Account_Item.deleted = 0
    left join Account on Account.id = Account_Item.master_id and Account.deleted = 0
    LEFT JOIN ActionType   ON ActionType.id = vAction.actionType_id
    LEFT JOIN rbService    ON rbService.id = IFNULL(Account_Item.service_id, ActionType.nomenclativeService_id)
    LEFT JOIN EventType       ON EventType.id = Event.eventType_id
    LEFT JOIN Contract ON Contract.id = coalesce(Account.contract_id, vAction.contract_id, Event.contract_id)
    LEFT JOIN Contract_Tariff ct ON ct.master_id = IFNULL(Contract.priceList_id, Contract.id) and ct.service_id = rbService.id and ct.deleted = 0
            and (ct.endDate is not null and DATE(vAction.endDate) between ct.begDate and ct.endDate 
            or DATE(vAction.endDate) >= ct.begDate and ct.endDate is null)
            and ct.tariffType in (2,5)
    LEFT JOIN Person          ON Person.id = vAction.person_id
    LEFT JOIN rbSpeciality ON rbSpeciality.id = Person.speciality_id
    left join OrgStructure on OrgStructure.id = Person.orgStructure_id
    left join Client on Client.id = Event.client_id
    LEFT JOIN rbMedicalAidType mt ON mt.id = ifnull(rbService.medicalAidType_id, EventType.medicalAidType_id)
    left join rbFinance on  rbFinance.id = vAction.finance_id
    left join ClientPolicy on ClientPolicy.id = getClientPolicyIdForDate(Client.id, 1, Event.execDate, Event.id)
    left join Organisation AS Insurer ON Insurer.id = ClientPolicy.insurer_id
    left join Organisation as Payer on Payer.id =
        IFNULL((select max(id) from Organisation o where o.OGRN = Insurer.OGRN and o.deleted = 0 and o.isInsurer = 1
        and o.OKATO = Insurer.OKATO and Insurer.OKATO = '03000' and o.head_id is null), Contract.payer_id)
    left JOIN Event_Payment ON Event.id = Event_Payment.master_id AND Event_Payment.deleted=0
    where vAction.deleted = 0 
    and Event.deleted = 0
    and rbService.id is not null
    and ifnull(Account_Item.price, ct.price) is not null
    and DATE(vAction.endDate) >= DATE(Event.setDate)
    /*and vAction.expose = 1*/
    and %(cond)s 
    GROUP BY vAction.id

      union all
    select Event.id as event_id,Client.id as cli_,Event.externalId AS kvit,
      concat(Person.lastName,' ',Person.firstName,' ',Person.patrName) AS fioP,
    concat(Client.lastName,' ',Client.firstName,' ',Client.patrName) AS fio,
    %(os)s 
    date(Event.execDate) AS dat,
       isPos(rbService.infis, rbService.name, mt.regionalCode) as isPos,
       IF(rbService.name like 'Обращение%%', 1, 0) as isObr,
       IF(rbService.infis LIKE 'B04%%', 1, 0) as isProf,
       IFNULL(Account_Item.uet, ct.uet) as uet,
		   IFNULL(Account_Item.sum, ct.price) as sum,Event_Payment.sum as sum1,0
    from Visit
    left join Event on Event.id = Visit.event_id
    left join Account_Item on Account_Item.event_id = Visit.event_id and Account_Item.visit_id = Visit.id 
        and Account_Item.action_id is null and Account_Item.deleted = 0
    left join Account on Account.id = Account_Item.master_id and Account.deleted = 0
    LEFT JOIN rbService  ON rbService.id = IF(Account_Item.service_id IS NULL, Visit.service_id, Account_Item.service_id)
    LEFT JOIN EventType       ON EventType.id = Event.eventType_id
    LEFT JOIN Contract ON Contract.id = coalesce(Account.contract_id, Event.contract_id)
    LEFT JOIN Contract_Tariff ct ON ct.master_id = IFNULL(Contract.priceList_id, Contract.id) 
    and ct.tariffType = 0
        and ct.service_id = rbService.id and ct.deleted = 0
            and (ct.endDate is not null and DATE(Visit.date) between ct.begDate and ct.endDate 
            or DATE(Visit.date) >= ct.begDate and ct.endDate is null) 
    LEFT JOIN Person          ON Person.id = Visit.person_id
    LEFT JOIN rbSpeciality ON rbSpeciality.id = Person.speciality_id
    left join OrgStructure on OrgStructure.id = Person.orgStructure_id
    LEFT JOIN rbMedicalAidType mt ON mt.id = ifnull(rbService.medicalAidType_id, EventType.medicalAidType_id)
    left join rbFinance on  rbFinance.id = Visit.finance_id
    left join Client on Client.id = Event.client_id
    left join ClientPolicy on ClientPolicy.id = getClientPolicyIdForDate(Client.id, 1, Event.execDate, Event.id)
    left join Organisation AS Insurer ON Insurer.id = ClientPolicy.insurer_id
    left join Organisation as Payer on Payer.id =
        IFNULL((select max(id) from Organisation o where o.OGRN = Insurer.OGRN and o.deleted = 0 and o.isInsurer = 1
        and o.OKATO = Insurer.OKATO and Insurer.OKATO = '03000' and o.head_id is null), Contract.payer_id)
    left JOIN Event_Payment ON Event.id = Event_Payment.master_id AND Event_Payment.deleted=0
    where Event.deleted = 0 and Visit.deleted = 0 
    and DATE(Visit.date) >= DATE(Event.setDate)
    and rbService.id is not null
    and ifnull(Account_Item.price, ct.price) is not null
    and %(cond)s 
      ) q
    group by q.dat %(os1)s 
    order by q.dat ASC, CAST(q.kvit as int) ASC, q.fio ASC
    """
        db = QtGui.qApp.db
        cond2, os, os1 = getusl(params)
        st = stmt % {"cond2": cond2, "os": os, "os1": os1, "cond": getCond(params)}
        return db.query(st)

    def build(self, description, params):
        reportRowSize = 7
        reportData = {}

        # osname = forceString(record.value('osname'))
        #              fin = forceString(record.value('fin'))
        #                infis = forceString(record.value('infis'))
        # name = forceString(record.value('name'))
        #   amount = forceInt(record.value('amount'))
        #     kd = forceInt(record.value('kd'))
        #       pd = forceInt(record.value('pd'))
        #         uet = forceDouble(record.value('uet'))
        #           sum = forceDouble(record.value('sum'))
        #             cnt = forceInt(record.value('cnt'))
        #               pos = forceInt(record.value('pos'))

        # key = (osname, fin,   infis,  name)
        #  reportLine = reportData.setdefault(key, [0]*reportRowSize)
        #    reportLine[0] += amount
        #      reportLine[1] += kd
        #        reportLine[2] += pd
        #          reportLine[3] += uet
        #            reportLine[4] += sum
        #              reportLine[5] += cnt
        #                 reportLine[6] += pos

        def processQuery(query):
            num = 1
            prevnum = 1
            while query.next():
                record = query.record()
                event_id = forceString(record.value('event_id'))  # name
                cli = forceString(record.value('cli_'))  # name
                kvit = forceString(record.value('kvit'))  # name
                fio = forceString(record.value('fio'))  # name
                fiop = forceString(record.value('fiop'))  # name
                nam = forceString(record.value('nam'))  # name
                a = params.get('typePay', None)
                if a == 2:
                    sum = forceDouble(record.value('sum'))  # +
                else:
                    sum = forceDouble(record.value('sum1'))  # +
                usl = forceInt(record.value('usl'))  # +
                dat = forceString(record.value('dat'))  # +
                if prevnum != dat:
                    num = 1
                    prevnum = dat
                else:
                    num += 1

                key = (dat, num, kvit, fiop, fio, usl, sum, nam, event_id, cli)
                reportLine = reportData.setdefault(key)
            #   reportLine[0] += kd
            #   reportLine[1] += sum
            #  reportLine[2] += cnt

        query = self.selectData(params)
        processQuery(query)
        a = params.get('typePay', None)
        s = params.get('without0usl', None)
        currentPersonId = QtGui.qApp.userId
        currentPerson = forceString(QtGui.qApp.db.translate('vrbPerson', 'id', currentPersonId, 'name'))
        lpuCode = forceString(QtGui.qApp.db.translate('Organisation', 'id', QtGui.qApp.currentOrgId(), 'infisCode'))
        if forceString(QtGui.qApp.preferences.appPrefs.get('provinceKLADR', '00'))[:2] == '23' and lpuCode == '07541':
            if a == 0:
                buh = u'Щетникова Н.В.'
            elif a == 1:
                buh = u'Мухоед С.А.'
            else:
                buh = u''
            #   mat = u' Туний Т.А.'
            mat = u' Ахмеджанова Д.М.'
            org = u'Государственное бюджетное учреждение здравоохранения "Краевой центр Охраны здоровья семьи и репродукции" министерства здравоохранения Краснодарского края'
            #   mat2=u' Т.А Туний'
            mat2 = currentPerson
        else:
            mat = ''
            mat2 = ''
            org = lpuCode = forceString(
                QtGui.qApp.db.translate('Organisation', 'id', QtGui.qApp.currentOrgId(), 'fullName'))
            buh = ''

        # now text
        doc = QtGui.QTextDocument()
        doc.setDefaultStyleSheet("body{font-size: 10pt}")
        # doc.set
        cursor = QtGui.QTextCursor(doc)
        rt = CReportBase.ReportTitle
        rt.setFontWeight(QtGui.QFont.Normal)
        cursor.setCharFormat(rt)
        cursor.setBlockFormat(CReportBase.AlignCenter)
        cursor.insertHtml(u'''<table width="100%">
<tr>
<td width="25%">
</td>
<td width="25%">
<br>
Реестр № __________
</td>
<td width="25%">
</td>
<td width="25%">
</td>
</tr>
<tr>
<td width="25%">
</td>
<td width="25%">

</td>
<td width="25%">
</td>
<td width="25%" align="right">
<table border="1">
<tr><td></td><td>КОДЫ</td></tr>
<tr><td>Форма 442 по ОКУД</td><td>504842</td></tr>
<tr><td>по ОКПО</td><td></td></tr>
<tr><td>по КСП</td><td></td></tr>
</table>
</td>
</tr>
</table>''')
        cursor.setBlockFormat(CReportBase.AlignRight)
        cursor.insertText(u'''%s 
''' % description)
        pixelTwoCM = (QtGui.qApp.desktop().logicalDpiX() * 20)/25.4 - 10 # pixel = dpi*mm/25.4 - defaultMargin (1 inch)
        cursor.insertHtml(u'''<div style="margin-left:{};"><td><br><table><tr><td>Материально-Ответственное лицо: {}'''.format(pixelTwoCM, mat2))
        cursor.insertHtml(u'''<div style="margin-left:{};"><td><br>Учреждение: {}</td></tr></table>'''.format(pixelTwoCM, org))
        cursor.setBlockFormat(CReportBase.AlignCenter)
        cursor.insertBlock()
        cursor.insertBlock()
        
        if s:
            tableColumns = [
                ('10%', [u'№'], CReportBase.AlignLeft),
                ('10%', [u'Квитанция №'], CReportBase.AlignLeft),
                ('20%', [u'ФИО врача'], CReportBase.AlignLeft),
                ('20%', [u'ФИО'], CReportBase.AlignLeft),
                ('20%', [u'Услуга'], CReportBase.AlignLeft),
                ('10%', [u'Кол-во услуг'], CReportBase.AlignLeft),
                ('10%', [u'Сумма'], CReportBase.AlignRight),
            ]
        else:
            tableColumns = [
                ('10%', [u'№'], CReportBase.AlignLeft),
                ('10%', [u'Квитанция №'], CReportBase.AlignLeft),
                ('30%', [u'ФИО врача'], CReportBase.AlignLeft),
                ('30%', [u'ФИО'], CReportBase.AlignLeft),
                ('10%', [u'Кол-во услуг'], CReportBase.AlignLeft),
                ('10%', [u'Сумма'], CReportBase.AlignRight),
            ]

        table = createTable(cursor, tableColumns, leftMargin=pixelTwoCM)
        table.mergeCells(0, 0, 1, 1)
        for col in xrange(reportRowSize):
            table.mergeCells(0, col, 2, 1)

        totalBynum = [0] * reportRowSize
        # totalByReport = [0]*reportRowSize
        prevnum = None
        prevsum = 0
        kolusl = 0
        prevdat = 0
        cnt = None
        ttt = None
        event = None
        ct = 0
        t = None
        cliCNT = 0
        cliCNTALL = 0
        clien = None

        keys = reportData.keys()
        keys.sort()

        def drawTotal(table, total, text):

            row = table.addRow()

            table.setText(row, 1, text, CReportBase.TableHeader)
            table.mergeCells(row, 0, 1, 7)

        for key in keys:
            # key = (osname, fin,   infis,  name)key = (dat, kvit, fio, sum, num)
            cli = key[9]
            event_id = key[8]
            nam = key[7]
            sum = key[6]
            usl = key[5]
            fio = key[4]
            fiop = key[3]
            kvit = key[2]
            dat = key[0]
            num = key[1]

            if prevnum is not None and prevnum != dat:
                drawTotal(table, totalBynum,
                          u'Количество случаев - %(order)s, пациентов - %(ord)s ' % dict(order=cnt,
                                                                                             ord=cliCNT));
                totalBynum = [0] * reportRowSize

            if ttt == (dat):
                prevdat += 1
                cnt = cnt + 1
                if s:
                    if t != event_id:
                        prevsum += sum
                        t = event_id
                else:
                    prevsum += sum
                kolusl += usl
            else:
                prevdat += 1
                cnt = 0
                cliCNT = 0
                cnt = cnt + 1
                if s:
                    t = event_id
                prevsum += sum
                kolusl += usl

            if cli != clien:
                cliCNTALL += 1
                cliCNT += 1
                clien = cli

            # mergeCells(int row, int column, int numRows, int numCols)
            if prevnum != dat:
                row = table.addRow()
                table.setText(row, 0, dat, CReportBase.TableHeader)
                table.mergeCells(row, 0, 1, 6)

            row = table.addRow()
            table.setText(row, 0, num)
            table.setText(row, 1, kvit)
            table.setText(row, 2, fiop)
            table.setText(row, 3, fio)
            if s:
                table.setText(row, 4, nam)
                table.setText(row, 5, usl)
                if event == event_id:
                    ct += 1
                    table.mergeCells(str, 6, ct, 1)
                else:
                    str = row
                    event = event_id
                    ct = 1
                    table.setText(row, 6, sum)
            else:
                table.setText(row, 4, usl)
                table.setText(row, 5, sum)

            # total
            # drawTotal(table,  totalBynum, u'%s итого' % prevnum);
            # drawTotal(table,  totalByReport, u'Итого');
            prevnum = dat
            ttt = (dat)
            # tt =   (dat)

        drawTotal(table, totalBynum, u'Количество случаев - %(order)s, пациентов - %(ord)s ' % dict(order=cnt,
                                                                                                        ord=cliCNT));
        drawTotal(table, totalBynum, u'Итого случаев - %(order)s, пациентов - %(ord)s' % dict(order=prevdat,ord=cliCNTALL));
        row = table.addRow()
        if s:
            table.mergeCells(row, 0, 1, 5)
        else:
            table.mergeCells(row, 0, 1, 4)
        table.setText(row, 0, u' Итого сумма')
        if s:
            table.setText(row, 5, kolusl)
            table.setText(row, 6, prevsum)
        else:
            table.setText(row, 4, kolusl)
            table.setText(row, 5, prevsum)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertHtml(u'''<br><div style="margin-left:{};"><b> Итого: <u><i>{}</i></u></b>'''.format(pixelTwoCM, amountToWords(prevsum)))
        cursor.insertHtml(
            u'''<div style="margin-left:{};"><table><tr><td><br>Сдал администратор ____________________________________________ {} <br>Принял:</td>'''.format(pixelTwoCM,mat2))
        cursor.insertHtml(
            u'''<div style="margin-left:{};"><td>Бухгалтер ЦБ ДЗ _______________________________________________ {}</td></tr></table>'''.format(pixelTwoCM,buh))
        return doc


class CRepReestrUslEx(CRepReestrUsl):
    def exec_(self, accountIdList=None):
        self.accountIdList = accountIdList
        CRepReestrUsl.exec_(self)

    def setParams(self, params):
        typePayment = params.get('typePayment', None)
        if typePayment is None:
            self.cmbTypePayment.setCurrentIndex(0)
        else:
            self.cmbTypePayment.setCurrentIndex(params['typePayment'] + 1)

    def params(self):
        result = {}
        result['eventTypeId'] = self.cmbEventType.value()
        return result

    def getSetupDialog(self, parent):
        result = CEconomicAnalisysSetupDialog(parent)
        result.setTitle(self.title())
        result.setuslVisible(True)
        result.settypePayVisible(True)
        result.setPriceVisible(False)
        result.loadPrefs()
        return result

    def build(self, params):
        params['accountIdList'] = self.accountIdList
        return CRepReestrUsl.build(self, '\n'.join(self.getDescription(params)), params)
