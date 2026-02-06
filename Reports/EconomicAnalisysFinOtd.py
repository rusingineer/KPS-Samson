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

from Reports.Report     import *
from Reports.ReportBase import *

from library.Utils      import *
from EconomicAnalisysSetupDialog import *


class CEconomicAnalisysFinOtd(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Финансовая сводка по отделениям.')

    def selectData(self, params):
        stmt=u"""
     select q.OrgStructure_name as orgname, q.osname, q.account_number, 
	count(q.client_id) as exposedFL, sum(IF(q.exposed = 1, q.isPos, 0)) as exposedPos, sum(IF(q.exposed = 1, q.KD, 0)) as exposedKD, sum(IF(q.exposed = 1, q.PD, 0)) as exposedPD, round(sum(IF(q.exposed = 1, q.sum, 0)), 2) as exposedSUM,
    count(q.ref_client_id) as refusedFL, sum(IF(q.refused = 1, q.isPos, 0)) as refusedPos, sum(IF(q.refused = 1, q.KD, 0)) as refusedKD, sum(IF(q.refused = 1, q.PD, 0)) as refusedPD, round(sum(IF(q.refused = 1, q.sum, 0)), 2) as refusedSUM,
    count(q.pay_client_id) as payedFL, sum(IF(q.payed = 1, q.isPos, 0)) as payedPos, sum(IF(q.payed = 1, q.KD, 0)) as payedKD, sum(IF(q.payed = 1, q.PD, 0)) as payedPD, round(sum(IF(q.payed = 1, q.sum, 0)), 2) as payedSUM
    from (select Account.id as account_id, Event.client_id, Event.id as event_id, Account.number as account_number,
    OrgStructure.name OrgStructure_name, Payer.shortName as osname,
    IF(substr(rbService.infis, 1, 1) = 'V', WorkDays(Event.setDate, Event.execDate, EventType.weekProfileCode, mt.regionalCode), 0) as KD, 0 as PD, ref.id as ref_client_id, pay.id as pay_client_id,
    isPos(rbService.infis, mt.regionalCode, ifnull(Account_Item.price, ct.price)) as isPos,
    Account_Item.sum as sum,
    (Account_Item.id IS NOT NULL) AS exposed,
    (Account_Item.id IS NOT NULL AND Account_Item.refuseType_id IS NULL) AS payed,
    (Account_Item.id IS NOT NULL AND Account_Item.refuseType_id IS NOT NULL) as refused
    from Account_Item
    left join Contract_Tariff ct on ct.id = Account_Item.tariff_id
    left join Event on Event.id = Account_Item.event_id
    left join Client on Client.id = Event.client_id
    left join Client ref on ref.id = Event.client_id and Account_Item.refuseType_id IS NOT NULL
    left join Client pay on pay.id = Event.client_id and Account_Item.refuseType_id IS NULL
    left join vAction on vAction.id = Account_Item.action_id
    left join Account on Account.id = Account_Item.master_id and Account.deleted = 0
    LEFT JOIN rbService ON rbService.id = Account_Item.service_id
    LEFT JOIN EventType       ON EventType.id = Event.eventType_id
    LEFT JOIN Contract        ON Contract.id = Account.contract_id
    LEFT JOIN Person          ON Person.id = vAction.person_id
    LEFT JOIN rbSpeciality ON rbSpeciality.id = Person.speciality_id
    left join OrgStructure on OrgStructure.id = Person.orgStructure_id
    LEFT JOIN rbMedicalAidType mt ON mt.id = ifnull(rbService.medicalAidType_id, EventType.medicalAidType_id)
    left join rbFinance on  rbFinance.id = coalesce(vAction.finance_id, Contract.finance_id)
    left join ClientPolicy on ClientPolicy.id = getClientPolicyIdForDate(Client.id, 1, Event.execDate, Event.id)
    left join Organisation AS Insurer ON Insurer.id = ClientPolicy.insurer_id
    left join Organisation as Payer on Payer.id =
        IFNULL((select max(id) from Organisation o where o.OGRN = Insurer.OGRN and o.deleted = 0 and o.isInsurer = 1
        and o.OKATO = Insurer.OKATO and Insurer.OKATO = '03000' and o.head_id is null), Contract.payer_id)
    where Account_Item.deleted = 0 and Account_Item.action_id is not null and Account_Item.visit_id is null
    and %(cond)s
    
    union all
    
    select Account.id as account_id, Event.client_id, Event.id as event_id, Account.number as account_number,
    OrgStructure.name OrgStructure_name, Payer.shortName as osname,
    0 as KD, 0 as PD, ref.id as ref_client_id, pay.id as pay_client_id,
    isPos(rbService.infis, mt.regionalCode, ifnull(Account_Item.price, ct.price)) as isPos,
    Account_Item.sum as sum,
    (Account_Item.id IS NOT NULL) AS exposed,
    (Account_Item.id is not null and Account_Item.refuseType_id IS NULL) AS payed,
    (Account_Item.id IS NOT NULL AND Account_Item.refuseType_id IS NOT NULL) as refused
    from Account_Item
    left join Contract_Tariff ct on ct.id = Account_Item.tariff_id
    left join Visit on Visit.id = Account_Item.visit_id
    left join Event on Event.id = Visit.event_id
    left join Client on Client.id = Event.client_id
	left join Client ref on ref.id = Event.client_id and Account_Item.refuseType_id IS NOT NULL
    left join Client pay on pay.id = Event.client_id and Account_Item.refuseType_id IS NULL
    left join Account on Account.id = Account_Item.master_id and Account.deleted = 0
    LEFT JOIN rbService ON rbService.id = Account_Item.service_id
	LEFT JOIN EventType ON EventType.id = Event.eventType_id
    LEFT JOIN Contract ON Contract.id = coalesce(Account.contract_id, Event.contract_id)
    LEFT JOIN Person ON Person.id = Visit.person_id
    LEFT JOIN rbSpeciality ON rbSpeciality.id = Person.speciality_id
    left join OrgStructure on OrgStructure.id = Person.orgStructure_id
    LEFT JOIN rbMedicalAidType mt ON mt.id = ifnull(rbService.medicalAidType_id, EventType.medicalAidType_id)
    left join rbFinance on rbFinance.id = coalesce(Visit.finance_id, Contract.finance_id)
    left join ClientPolicy on ClientPolicy.id = getClientPolicyIdForDate(Client.id, 1, Event.execDate, Event.id)
    left join Organisation AS Insurer ON Insurer.id = ClientPolicy.insurer_id
    left join Organisation as Payer on Payer.id =
        IFNULL((select max(id) from Organisation o where o.OGRN = Insurer.OGRN and o.deleted = 0 and o.isInsurer = 1
        and o.OKATO = Insurer.OKATO and Insurer.OKATO = '03000' and o.head_id is null), Contract.payer_id)
    where Account_Item.deleted = 0 and Account_Item.action_id is null and Account_Item.visit_id is not null
    and %(cond)s
    union all
    
    select Account.id as account_id, Event.client_id, Event.id as event_id, Account.number as account_number,
    OrgStructure.name OrgStructure_name, Payer.shortName as osname,
    if(mt.regionalCode in ('11', '12', '301', '302'), WorkDays(Event.setDate, Event.execDate, EventType.weekProfileCode, mt.regionalCode), 0) as KD, 
    if(mt.regionalCode in ('41', '42', '43', '51', '52', '71', '72', '90', '411', '422', '511', '522'), WorkDays(Event.setDate, Event.execDate, EventType.weekProfileCode, mt.regionalCode), 0) as PD, ref.id as ref_client_id, pay.id as pay_client_id,
    isPos(rbService.infis, mt.regionalCode, ifnull(Account_Item.price, ct.price)) as isPos,
    Account_Item.sum as sum,
    (Account_Item.id IS NOT NULL) AS exposed,
    (Account_Item.id is not null and Account_Item.refuseType_id IS NULL) AS payed,
    (Account_Item.id IS NOT NULL AND Account_Item.refuseType_id IS NOT NULL) as refused
    from Account_Item
    left join Contract_Tariff ct on ct.id = Account_Item.tariff_id
    left join Event on Event.id = Account_Item.event_id
    left join Client on Client.id = Event.client_id
	left join Client ref on ref.id = Event.client_id and Account_Item.refuseType_id IS NOT NULL
    left join Client pay on pay.id = Event.client_id and Account_Item.refuseType_id IS NULL
    left join Account on Account.id = Account_Item.master_id and Account.deleted = 0
    LEFT JOIN rbService ON rbService.id = Account_Item.service_id
    LEFT JOIN EventType ON EventType.id = Event.eventType_id
    left join Diagnosis d on d.id = getEventDiagnosis(Event.id) 
    LEFT JOIN rbMedicalAidType mt ON mt.id = ifnull(rbService.medicalAidType_id, EventType.medicalAidType_id)
    LEFT JOIN Contract ON Contract.id = coalesce(Account.contract_id, Event.contract_id)
    left join rbFinance on rbFinance.id = Contract.finance_id
    LEFT JOIN Person ON Person.id = Event.execPerson_id
    LEFT JOIN rbSpeciality ON rbSpeciality.id = Person.speciality_id
    left join OrgStructure on OrgStructure.id = Person.orgStructure_id
    left join ClientPolicy on ClientPolicy.id = getClientPolicyIdForDate(Client.id, 1, Event.execDate, Event.id)
    left join Organisation AS Insurer ON Insurer.id = ClientPolicy.insurer_id
    left join Organisation as Payer on Payer.id =
        IFNULL((select max(id) from Organisation o where o.OGRN = Insurer.OGRN and o.deleted = 0 and o.isInsurer = 1
        and o.OKATO = Insurer.OKATO and Insurer.OKATO = '03000' and o.head_id is null), Contract.payer_id)
    where Account_Item.event_id is not null and Account_Item.action_id is null and Account_Item.visit_id is null and Account_Item.deleted = 0 and Event.MES_id is not null
    and %(cond)s
   ) q
    group by q.OrgStructure_name, q.osname, q.account_id, q.account_number
    order by q.OrgStructure_name, q.osname, q.account_number
        """
        db = QtGui.qApp.db
        return db.query(stmt %{"cond": getCond(params)})

    def build(self, description, params):
        reportRowSize = 15
        colsShift = 3
        reportData = {}

        def processQuery(query):
            while query.next():
                record = query.record()
                orgname = forceString(record.value('orgname'))
                osname = forceString(record.value('osname'))
                account_number = forceString(record.value('account_number'))
                exposedFL = forceInt(record.value('exposedFL'))
                exposedPos = forceInt(record.value('exposedPos'))
                exposedKD = forceInt(record.value('exposedKD'))
                exposedPD = forceInt(record.value('exposedPD'))
                exposedSUM = forceDouble(record.value('exposedSUM'))
                refusedFL = forceInt(record.value('refusedFL'))
                refusedPos = forceInt(record.value('refusedPos'))
                refusedKD = forceInt(record.value('refusedKD'))
                refusedPD = forceInt(record.value('refusedPD'))
                refusedSUM = forceDouble(record.value('refusedSUM'))
                payedFL = forceInt(record.value('payedFL'))
                payedPos = forceInt(record.value('payedPos'))
                payedKD = forceInt(record.value('payedKD'))
                payedPD = forceInt(record.value('payedPD'))
                payedSUM = forceDouble(record.value('payedSUM'))
                payedFL = forceInt(record.value('payedFL'))

                key = (orgname if orgname else u'Не задан',  osname if osname else u'Не задан',  account_number)
                reportLine = reportData.setdefault(key, [0]*reportRowSize)
                reportLine[0] += exposedFL
                reportLine[1] += exposedKD + exposedPD
                reportLine[2] += exposedPos
                reportLine[3] += exposedSUM
                reportLine[4] += refusedFL
                reportLine[5] += refusedKD + refusedPD
                reportLine[6] += refusedPos
                reportLine[7] += refusedSUM
                reportLine[8] += payedFL
                reportLine[9] += payedKD + payedPD
                reportLine[10] += payedPos
                reportLine[11] += payedSUM

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
            ('10%',  [ u'Наимен. отделения',   u''], CReportBase.AlignLeft),
            ('10%',  [ u'Плательщик',  u''], CReportBase.AlignLeft),
            ('7%',  [  u'№ счета',  u''], CReportBase.AlignLeft),
            ('5%',  [ u'Выставлено',  u'чел.'], CReportBase.AlignRight), 
            ('5%',  [ u'',  u'КД(ДЛ)'], CReportBase.AlignRight),
            ('5%',  [ u'', u'пос.'], CReportBase.AlignRight),
            ('7%',  [ u'',  u'Сумма'], CReportBase.AlignRight), 
            ('5%',  [ u'Отклонено',  u'чел.'], CReportBase.AlignRight), 
            ('5%',  [ u'',  u'КД(ДЛ)'], CReportBase.AlignRight),
            ('5%',  [ u'', u'пос.'], CReportBase.AlignRight),
            ('7%',  [ u'',  u'Сумма'], CReportBase.AlignRight), 
            ('5%',  [ u'Оплачено',  u'чел.'], CReportBase.AlignRight), 
            ('5%',  [ u'',  u'КД(ДЛ)'], CReportBase.AlignRight),
            ('5%',  [ u'', u'пос.'], CReportBase.AlignRight),
            ('7%',  [ u'',  u'Сумма'], CReportBase.AlignRight), 
            ]

        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 2, 1)
        table.mergeCells(0, 1, 2, 1)
        table.mergeCells(0, 2, 2, 1)
        table.mergeCells(0, 3, 1, 4)
        table.mergeCells(0, 7, 1, 4)
        table.mergeCells(0, 11, 1, 4)
        totalByOrg = [0]*reportRowSize
        totalByReport = [0]*reportRowSize
        PrevOrg = None
        orgname = None
        prevRow = 2
        
        keys = reportData.keys()
        keys.sort()
        for key in keys:            
            orgname = key[0]
            osname = key[1]
            account_number = key[2]          
            if PrevOrg !=orgname:
                if PrevOrg != None:
                    row = table.addRow()
                    table.setText(row, 1, u'Итого',  CReportBase.TableHeader)
                    table.mergeCells(row, 1, 1, 2)
                    table.mergeCells(prevRow, 0, row-prevRow +1, 1)
                    for col in xrange(reportRowSize-colsShift):
                        table.setText(row, col + colsShift, totalByOrg[col],  CReportBase.TableHeader)
                        totalByReport[col] = totalByReport[col] + totalByOrg[col]
                    totalByOrg = [0]*reportRowSize
                    
                row = table.addRow()
                table.setText(row, 0, orgname,  CReportBase.TableHeader)
                prevRow = row
                PrevOrg = orgname
                table.setText(row, 1, osname)
                table.setText(row, 2, account_number)
                reportLine = reportData[key]
                for col in xrange(reportRowSize-colsShift):
                    table.setText(row, col + colsShift, reportLine[col])
                    totalByOrg[col] = totalByOrg[col] + reportLine[col]
            else:
                row = table.addRow()
                table.setText(row, 1, osname)
                table.setText(row, 2, account_number)
                reportLine = reportData[key]
                for col in xrange(reportRowSize-colsShift):
                    table.setText(row, col + colsShift, reportLine[col])
                    totalByOrg[col] = totalByOrg[col] + reportLine[col]
        if orgname != None:        
            row = table.addRow()
            table.setText(row, 1, u'Итого',  CReportBase.TableHeader)
            table.mergeCells(row, 1, 1, 2)
            table.mergeCells(prevRow, 0, row-prevRow+1, 1)
            for col in xrange(reportRowSize-colsShift):
                table.setText(row, col + colsShift, totalByOrg[col],  CReportBase.TableHeader)
                totalByReport[col] = totalByReport[col] + totalByOrg[col]
        row = table.addRow()
        table.setText(row, 0, u'Итого',  CReportBase.TableHeader)
        table.mergeCells(row, 0, 1, 3)
        for col in xrange(reportRowSize-colsShift):
            table.setText(row, col + colsShift, totalByReport[col],  CReportBase.TableHeader)
                
        return doc

class CEconomicAnalisysFinOtdEx(CEconomicAnalisysFinOtd):
    def exec_(self, accountIdList=None):
        self.accountIdList = accountIdList
        CEconomicAnalisysFinOtd.exec_(self)


    def getSetupDialog(self, parent):
        result = CEconomicAnalisysSetupDialog(parent)
        result.setTitle(self.title())
        result.shrink()
        result.loadPrefs()
        return result


    def build(self, params):
        params['accountIdList'] = self.accountIdList
        return CEconomicAnalisysFinOtd.build(self, '\n'.join(self.getDescription(params)), params)
