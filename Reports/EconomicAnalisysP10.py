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

class CEconomicAnalisysP10(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Форма П-10. Анализ причин и суммы возврата выставленных счетов за оказанные услуги')

    def selectData(self, params):
        stmt=u"""
    select CONCAT(q.refusecode,' | ',q.refusename) AS refusename, 
    count(distinct q.event_id) as cnt, sum(q.isMES) as mes, sum(q.isPos) as pos, round(sum(q.uet),2) as uet, 
    sum(q.KD) as kd, sum(q.PD) as pd, sum(q.isCallAmbulance) as callambulance, 
    sum(IF(q.isPos =0 and q.isMES = 0 and q.isCallAmbulance =0 and q.isObr = 0, 1, 0)) as usl
    , round(sum(q.sum),2) as sum
    from (select Event.client_id, Event.id as event_id, Contract.id as contract_id, rbFinance.id as finance_id, rbFinance.name as fin, Person.id as person_id, 
    rbPayRefuseType.name as refusename,
    rbPayRefuseType.code AS refusecode,
    Account.id as account_id,
    OrgStructure.id as OrgStructure_id, OrgStructure.name OrgStructure_name, rbSpeciality.name as specialityName,
    Person.speciality_id as speciality_id, Person.org_id as org_id,
    Person.lastName, Person.firstName, Person.patrName, Person.code as tabn, mt.regionalCode, mt.name as VPNAME,
    rbService.infis,  rbService.name, Event.execDate, 0 isMES, isPos(rbService.infis, mt.regionalCode, ifnull(Account_Item.price, ct.price)) as isPos,
    IF(rbService.name like 'Обращение по поводу заболевания к%%', 1, 0) as isObr,
    IF(substr(rbService.infis,1, 7) = 'B01.044', 1, 0) as isCallAmbulance,
    IF(substr(rbService.infis, 1, 1) = 'V', WorkDays(Event.setDate, Event.execDate, EventType.weekProfileCode, mt.regionalCode), 0) as KD, 0 as PD,
    IFNULL(Account_Item.uet, vAction.amount * ct.uet) as uet,
    IFNULL(Account_Item.amount, vAction.amount) as amount, IFNULL(Account_Item.price, ct.price) as price, 
    IFNULL(Account_Item.sum, vAction.amount * ct.price) as sum,
    (Account_Item.id IS NOT NULL) AS exposed,
    (Account_Item.id is not null and Account_Item.refuseType_id IS NULL) AS payed,
    (Account_Item.id IS NOT NULL AND Account_Item.refuseType_id IS NOT NULL) as refused
    from vAction
    left join Event on Event.id = vAction.event_id
    left join Account_Item on Account_Item.action_id = vAction.id and Account_Item.deleted = 0
    left join rbPayRefuseType on rbPayRefuseType.id = Account_Item.refuseType_id
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
    LEFT JOIN rbMedicalAidType mt ON mt.id = ifnull(rbService.medicalAidType_id, EventType.medicalAidType_id)
    left join rbFinance on  rbFinance.id = coalesce(vAction.finance_id, Contract.finance_id)
    left join Client on Client.id = Event.client_id
    left join ClientPolicy on ClientPolicy.id = getClientPolicyIdForDate(Client.id, 1, Event.execDate, Event.id)
    left join Organisation AS Insurer ON Insurer.id = ClientPolicy.insurer_id
    left join Organisation as Payer on Payer.id =
        IFNULL((select max(id) from Organisation o where o.OGRN = Insurer.OGRN and o.deleted = 0 and o.isInsurer = 1
        and o.OKATO = Insurer.OKATO and Insurer.OKATO = '03000' and o.head_id is null), Contract.payer_id)
    where vAction.deleted = 0 
    and Account_Item.refuseType_id is not null
    and Event.deleted = 0
    and rbService.id is not null
    and ifnull(Account_Item.price, ct.price) is not null
    and DATE(vAction.endDate) >= DATE(Event.setDate)
    /*and vAction.expose = 1*/
    and %(cond)s
    
    union all
    
    select Event.client_id, Event.id as event_id, Contract.id as contract_id, rbFinance.id as finance_id, rbFinance.name as fin, Person.id as person_id, 
    rbPayRefuseType.name as refusename,
    rbPayRefuseType.code AS refusecode,
    Account.id as account_id,
    OrgStructure.id as OrgStructure_id, OrgStructure.name OrgStructure_name, rbSpeciality.name as specialityName,
    Person.speciality_id as speciality_id, Person.org_id as org_id,
    Person.lastName, Person.firstName, Person.patrName, Person.code as tabn, mt.regionalCode, mt.name as VPNAME,
    rbService.infis,  rbService.name, Event.execDate, 0 isMES, isPos(rbService.infis, mt.regionalCode, ifnull(Account_Item.price, ct.price)) as isPos,
    IF(rbService.name like 'Обращение по поводу заболевания к%%', 1, 0) as isObr,
    IF(substr(rbService.infis,1, 7) = 'B01.044', 1, 0) as isCallAmbulance,
    0 as KD, 0 as PD,
    IFNULL(Account_Item.uet, ct.uet) as uet,
    IFNULL(Account_Item.amount, 1) as amount, IFNULL(Account_Item.price, ct.price) as price, 
    IFNULL(Account_Item.sum, ct.price) as sum,
    (Account_Item.id IS NOT NULL) AS exposed,
    (Account_Item.id is not null and Account_Item.refuseType_id IS NULL) AS payed,
    (Account_Item.id IS NOT NULL AND Account_Item.refuseType_id IS NOT NULL) as refused
    from Visit
    left join Event on Event.id = Visit.event_id
     
    left join Account_Item on Account_Item.event_id = Visit.event_id and Account_Item.visit_id = Visit.id 
        and Account_Item.action_id is null and Account_Item.deleted = 0
    left join rbPayRefuseType on rbPayRefuseType.id = Account_Item.refuseType_id
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
    left join rbFinance on rbFinance.id = coalesce(Visit.finance_id, Contract.finance_id)
    left join Client on Client.id = Event.client_id
    left join ClientPolicy on ClientPolicy.id = getClientPolicyIdForDate(Client.id, 1, Event.execDate, Event.id)
    left join Organisation AS Insurer ON Insurer.id = ClientPolicy.insurer_id
    left join Organisation as Payer on Payer.id =
        IFNULL((select max(id) from Organisation o where o.OGRN = Insurer.OGRN and o.deleted = 0 and o.isInsurer = 1
        and o.OKATO = Insurer.OKATO and Insurer.OKATO = '03000' and o.head_id is null), Contract.payer_id)
    where Event.deleted = 0 and Visit.deleted = 0 
    and Account_Item.refuseType_id is not null
    and DATE(Visit.date) >= DATE(Event.setDate)
    and rbService.id is not null
    and ifnull(Account_Item.price, ct.price) is not null
    and %(cond)s
    union all
    
    select Event.client_id, Event.id as event_id, Contract.id as contract_id, rbFinance.id as finance_id, rbFinance.name as fin, Person.id as person_id, 
    rbPayRefuseType.name as refusename,
    rbPayRefuseType.code AS refusecode,
    Account.id as account_id,
    OrgStructure.id as OrgStructure_id, OrgStructure.name OrgStructure_name, rbSpeciality.name as specialityName,
    Person.speciality_id as speciality_id, Person.org_id as org_id,
    Person.lastName, Person.firstName, Person.patrName, Person.code as tabn, mt.regionalCode, mt.name as VPNAME,
    rbService.infis,  rbService.name, Event.execDate, 
    1 isMES, 0 as isPos, 0 as isObr, 0 as isCallAmbulance, if(mt.regionalCode in ('11', '12', '301', '302'), WorkDays(Event.setDate, Event.execDate, EventType.weekProfileCode, mt.regionalCode), 0) as KD, 
    if(mt.regionalCode in ('41', '42', '43', '51', '52', '71', '72', '90', '411', '422', '511', '522'), WorkDays(Event.setDate, Event.execDate, EventType.weekProfileCode, mt.regionalCode), 0) as PD, 0 as uet,
    IFNULL(Account_Item.amount, 1) as amount, 
    
    IFNULL(Account_Item.price, CalcCSGTarif(Event.id, Event.execDate, rbService.infis, d.mkb, WorkDays(Event.setDate, Event.execDate, EventType.weekProfileCode, mt.regionalCode)
	, ct.frag1Start, ct.frag2Start, age(Client.birthDate, Event.setDate), mt.regionalCode, ct.master_id, ct.price)) as price,
    IFNULL(Account_Item.sum, CalcCSGTarif(Event.id, Event.execDate, rbService.infis, d.mkb, WorkDays(Event.setDate, Event.execDate, EventType.weekProfileCode, mt.regionalCode)
	, ct.frag1Start, ct.frag2Start, age(Client.birthDate, Event.setDate), mt.regionalCode, ct.master_id, ct.price)) as sum,
    (Account_Item.id IS NOT NULL) AS exposed,
    (Account_Item.id is not null and Account_Item.refuseType_id IS NULL) AS payed,
    (Account_Item.id IS NOT NULL AND Account_Item.refuseType_id IS NOT NULL) as refused
    from Event
    left join Client on Client.id = Event.client_id
    left join Account_Item on Account_Item.event_id = Event.id and Account_Item.visit_id is null and Account_Item.action_id is null and Account_Item.deleted = 0
    left join rbPayRefuseType on rbPayRefuseType.id = Account_Item.refuseType_id
    left join Account on Account.id = Account_Item.master_id and Account.deleted = 0
    left join mes.MES on MES.id = Event.MES_id
    LEFT JOIN EventType ON EventType.id = Event.eventType_id
     
    LEFT JOIN rbService ON (Account_Item.service_id is not null and rbService.id = Account_Item.service_id) or (Account_Item.service_id is null and rbService.infis = MES.code)

    left join Diagnosis d on d.id = getEventDiagnosis(Event.id) 
    LEFT JOIN rbMedicalAidType mt ON mt.id = ifnull(rbService.medicalAidType_id, EventType.medicalAidType_id)
    LEFT JOIN Contract ON Contract.id = coalesce(Account.contract_id, Event.contract_id)
    left join rbFinance on rbFinance.id = Contract.finance_id
    LEFT JOIN Contract_Tariff ct ON ct.master_id = IFNULL(Contract.priceList_id, Contract.id) 
        and ct.service_id = rbService.id and ct.deleted = 0
            and (ct.endDate is not null and DATE(Event.execDate) between ct.begDate and ct.endDate 
            or DATE(Event.execDate) >= ct.begDate and ct.endDate is null) 
            and ct.tariffType = 13 AND (ct.eventType_id = Event.eventType_id or ct.eventType_id is null)
    LEFT JOIN Person ON Person.id = Event.execPerson_id
    LEFT JOIN rbSpeciality ON rbSpeciality.id = Person.speciality_id
    left join OrgStructure on OrgStructure.id = Person.orgStructure_id
    left join ClientPolicy on ClientPolicy.id = getClientPolicyIdForDate(Client.id, 1, Event.execDate, Event.id)
    left join Organisation AS Insurer ON Insurer.id = ClientPolicy.insurer_id
    left join Organisation as Payer on Payer.id =
        IFNULL((select max(id) from Organisation o where o.OGRN = Insurer.OGRN and o.deleted = 0 and o.isInsurer = 1
        and o.OKATO = Insurer.OKATO and Insurer.OKATO = '03000' and o.head_id is null), Contract.payer_id)
    where Event.execDate is not null and Event.deleted = 0
    and Account_Item.refuseType_id is not null
    and substr(rbService.infis, 1, 1) = 'G' and ifnull(Account_Item.price, ct.price) is not null
    and %(cond)s) q
    group by q.refusename
    order by q.refusename
        """
        db = QtGui.qApp.db
        return db.query(stmt %{"cond": getCond(params)})

    def build(self, description, params):
        reportRowSize = 11
        reportData = {}

        def processQuery(query):
            while query.next():
                record = query.record() 
                refusename = forceString(record.value('refusename'))
                cnt = forceInt(record.value('cnt'))
                mes = forceInt(record.value('mes'))
                pos = forceInt(record.value('pos'))
                kd = forceInt(record.value('kd'))
                pd = forceInt(record.value('pd'))
                usl = forceInt(record.value('usl'))
                callambulance = forceInt(record.value('callambulance'))
                uet = forceDouble(record.value('uet'))
                sum = forceDouble(record.value('sum'))

                key = (cnt, refusename if refusename else u'---')
                reportLine = reportData.setdefault(key, [0]*reportRowSize)
                reportLine[0] += cnt
                reportLine[1] += mes
                reportLine[2] += kd
                reportLine[3] += pd
                reportLine[4] += pos
                reportLine[5] += uet
                reportLine[6] += usl
                reportLine[7] += callambulance                
                reportLine[8] += sum

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
            ('35%',  [ u'Причина возврата'], CReportBase.AlignLeft),
            ('5%',  [ u'Кол-во случаев'], CReportBase.AlignRight),
            ('5%',  [ u'Кол-во КСГ'], CReportBase.AlignRight),
            ('5%',  [ u'Кол-во койко-дней'], CReportBase.AlignRight),
            ('5%',  [ u'Кол-во дней лечения'], CReportBase.AlignRight),
            ('5%',  [ u'Кол-во посещений'], CReportBase.AlignRight),
            ('5%',  [ u'Кол-во УЕТ'], CReportBase.AlignRight), 
            ('5%',  [ u'Кол-во простых услуг'], CReportBase.AlignRight), 
            ('5%',  [ u'Кол-во вызовов СМП'], CReportBase.AlignRight), 
            ('25%',  [ u'Сумма'], CReportBase.AlignRight)
            ]

        table = createTable(cursor, tableColumns)
        totalByReport = [0]*reportRowSize
        colsShift = 1
        refusename = None
        
        keys = reportData.keys()
        keys.sort(reverse=True)
        
        for key in keys:
            refusename = key[1]
            row = table.addRow()
            table.setText(row, 0, refusename)
            reportLine = reportData[key]
            for col in xrange(reportRowSize-2):
                table.setText(row, col + colsShift, reportLine[col])
                totalByReport[col] = totalByReport[col] + reportLine[col]
            ###    
        row = table.addRow()
        table.setText(row, 0, u'Итого')
        for col in xrange(reportRowSize-2):
            table.setText(row, col + colsShift, totalByReport[col])

                
        return doc

class CEconomicAnalisysP10Ex(CEconomicAnalisysP10):
    def exec_(self, accountIdList=None):
        self.accountIdList = accountIdList
        CEconomicAnalisysP10.exec_(self)


    def getSetupDialog(self, parent):
        result = CEconomicAnalisysSetupDialog(parent)
        result.setTitle(self.title())
        result.shrink()
        result.loadPrefs()
        return result


    def build(self, params):
        params['accountIdList'] = self.accountIdList
        return CEconomicAnalisysP10.build(self, '\n'.join(self.getDescription(params)), params)
