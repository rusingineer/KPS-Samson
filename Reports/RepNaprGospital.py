# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2025 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################
from PyQt4 import QtGui, QtSql
from PyQt4.QtCore import QDate, QDateTime
from Reports.Report import CReport
from Reports.Utils import dateRangeAsStr
from Reports.ReportBase import CReportBase, createTable
from ReportSetupDialog import CReportSetupDialog
from Orgs.Utils import getOrgStructurePersonIdList, getOrgStructureFullName
from library.Utils import forceString, forceDate, forceInt
from PyQt4.QtCore import *
    
class CNaprGosp(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Выгрузка направлений на госпитализацию')

    def getSetupDialog(self, parent):
        result = CFinReestrSetupDialog(parent)
        result.setTitle(self.title())
        for i in xrange(result.gridLayout.count()):
            spacer=result.gridLayout.itemAt(i)
            if isinstance(spacer, QtGui.QSpacerItem):
                itemposition=result.gridLayout.getItemPosition(i)
                if itemposition!=(29, 0, 1, 1)and itemposition!=(8, 1, 1, 3):
                    result.gridLayout.removeItem(spacer)
        result.resize(400, 10)
        return result


    def selectData(self, params): 
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        cond = self.getCond(params)
        chkDetailPerson   = params.get('detailPerson', False)
        if chkDetailPerson:
            dop1 = u''' ,IF(o.fullName IS NULL,'Не выбрано место выполнения',o.fullName) as org'''
            dop3 = u''' ,o.fullName'''
            dop2 = u''' left join ActionPropertyType apt9 on apt9.actionType_id = at.id and apt9.name = 'Куда направляется' and apt9.deleted = 0
    left join ActionProperty ap_dlit on ap_dlit.action_id = Action.id and ap_dlit.type_id = apt9.id
    left join ActionProperty_Organisation org on org.id = ap_dlit.id
  LEFT JOIN Organisation o ON org.value = o.id'''
        else:
            dop1 = u''' '''
            dop2 = u''' '''
            dop3 = u''' '''
        hospitalType = params.get('hospitalType', 0)
        if hospitalType == 1:
            if chkDetailPerson:
                order=u'o.fullName,date(Action.begDate), date(Action_Export.dateTime) desc'
            else:
                order=u'date(Action.begDate), date(Action_Export.dateTime) desc'
        else:
            order=u'date(Action.begDate), date(Action_Export.dateTime) desc'
        orgStructureId = params.get('orgStructureId', None)
        condOrgStructure = u''
        if orgStructureId:
            personIdList = getOrgStructurePersonIdList(orgStructureId)
            if personIdList:
                condOrgStructure = u''' AND p.id IN (%s)''' % (u','.join(str(personId) for personId in personIdList if personId))
            else: #Если нет врачей, то нечего выгружать
                return QtSql.QSqlQuery() #пустой QSqlQuery
        db = QtGui.qApp.db
        stmt = u'''SELECT date(Action.createDatetime) AS datvvod, date(Action.begDate) AS actionDate, date(Action_Export.dateTime) AS datvigr,
count(Action.`id`) AS vsego,
sum(CASE WHEN Action_Export.success = 1 THEN 1 ELSE 0 end) AS uspeh,
sum(CASE WHEN Action_Export.success = 0 THEN 1 ELSE 0 end) AS oshib,
GROUP_CONCAT(DISTINCT Action_Export.note) AS note
  %(dop1)s
FROM Action
  Left join Event e on e.id = Action.event_id
  left join Contract c ON c.id = e.contract_id
  left JOIN rbFinance f ON f.id = c.finance_id
  LEFT JOIN rbExternalSystem es ON es.code = 'ТФОМС:План.госп.'
  LEFT JOIN Action_Export
    ON (Action_Export.`master_id` = Action.`id`)
    AND (Action_Export.`system_id` = es.id)
  LEFT JOIN ActionType at on at.id = Action.actionType_id
  LEFT JOIN Person p ON e.execPerson_id=p.id
    %(dop2)s
  left join Action as Moving on Moving.id = getNextActionId(Action.event_id, Action.id, (select id from ActionType where flatCode = 'moving' and deleted = 0), Action.begDate)
  left join Action as Moving2 on Moving2.id = getPrevActionId(Action.event_id, Action.id, (select id from ActionType where flatCode = 'moving' and deleted = 0), Action.begDate)
WHERE Action.`deleted` = 0
AND (at.flatCode = 'received' and Moving.id is not null AND f.code = '2' AND (/*LENGTH(e.srcNumber) > 0
and*/ e.order = 1 OR e.order not in (1, 6)) or at.flatCode = 'leaved' and Moving2.id is not null AND f.code = '2'
 or at.flatCode = 'planning'  AND f.code = '2'  OR at.flatCode = 'hospitalDirection'  AND f.code in ('2', '4'))
AND %(cond)s
  AND DATE(Action.begDate) BETWEEN %(begDate)s AND %(endDate)s %(condOrgStructure)s
GROUP BY date(Action.begDate), date(Action_Export.dateTime) %(dop3)s
ORDER BY %(order)s;
        '''% dict(begDate=db.formatDate(begDate),
                    endDate=db.formatDate(endDate),
                    condOrgStructure=condOrgStructure, 
                    order=order, 
                    cond=cond, 
                    dop1=dop1, 
                    dop2=dop2, 
                    dop3=dop3)
        db = QtGui.qApp.db
        return db.query(stmt) 
        
    def selectData1(self, params): 
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        cond = self.getCond(params)
        chkDetailPerson   = params.get('detailPerson', False)
        if chkDetailPerson:
            dop1 = u''' ,o.fullName'''
            dop3 = u''' ,IF(q.fullName IS NULL,'Не выбрано место выполнения',q.fullName) as org'''
            dop2 = u''' left join ActionPropertyType apt9 on apt9.actionType_id = at.id and apt9.name = 'Куда направляется' and apt9.deleted = 0
    left join ActionProperty ap_dlit on ap_dlit.action_id = Action.id and ap_dlit.type_id = apt9.id
    left join ActionProperty_Organisation org on org.id = ap_dlit.id
  LEFT JOIN Organisation o ON org.value = o.id'''
        else:
            dop1 = u''' '''
            dop2 = u''' '''
            dop3 = u''' '''
        orgStructureId = params.get('orgStructureId', None)
        condOrgStructure = u''
        if orgStructureId:
            personIdList = getOrgStructurePersonIdList(orgStructureId)
            if personIdList:
                condOrgStructure = u''' AND p.id IN (%s)''' % (u','.join(str(personId) for personId in personIdList if personId))
            else: #Если нет врачей, то нечего выгружать
                return QtSql.QSqlQuery() #пустой QSqlQuery
        db = QtGui.qApp.db
        stmt = u'''SELECT q.externalId AS ev,c.id AS cl,c.lastName AS las,c.firstName AS fir,c.patrName AS pat,c.birthDate AS hap,et.name AS tip,
  CONCAT(q.datvvod,' / ',q.datvigr) AS dat,q.note AS osh 
 %(dop3)s
  FROM 
  (SELECT date(e.setDate) AS datvvod, date(Action_Export.dateTime) AS datvigr,
count(Action.`id`) AS vsego,
sum(CASE WHEN Action_Export.success = 1 THEN 1 ELSE 0 end) AS uspeh,
sum(CASE WHEN Action_Export.success = 0 THEN 1 ELSE 0 end) AS oshib,
Action_Export.note AS note,e.eventType_id AS eve,e.id as externalId,e.client_id
%(dop1)s
FROM Action
  Left join Event e on e.id = Action.event_id
  left join Contract c ON c.id = e.contract_id
  left JOIN rbFinance f ON f.id = c.finance_id
  LEFT JOIN rbExternalSystem es ON es.code = 'ТФОМС:План.госп.'
  LEFT JOIN Action_Export
    ON (Action_Export.`master_id` = Action.`id`)
    AND (Action_Export.`system_id` = es.id)
  LEFT JOIN ActionType at on at.id = Action.actionType_id  
  LEFT JOIN Person p ON e.execPerson_id=p.id
  %(dop2)s
  left join Action as Moving on Moving.id = getNextActionId(Action.event_id, Action.id, (select id from ActionType where flatCode = 'moving' and deleted = 0), Action.begDate)
  left join Action as Moving2 on Moving2.id = getPrevActionId(Action.event_id, Action.id, (select id from ActionType where flatCode = 'moving' and deleted = 0), Action.begDate)
WHERE Action.`deleted` = 0
AND (at.flatCode = 'received' and Moving.id is not null AND f.code = '2' AND (/*LENGTH(e.srcNumber) > 0
and*/ e.order = 1 OR e.order not in (1, 6)) or at.flatCode = 'leaved' and Moving2.id is not null AND f.code = '2'
 or at.flatCode = 'planning'  AND f.code = '2'  OR at.flatCode = 'hospitalDirection'  AND f.code in ('2', '4'))
AND %(cond)s
  AND DATE(Action.begDate) BETWEEN %(begDate)s AND %(endDate)s %(condOrgStructure)s
 GROUP BY e.id,e.client_id,Action_Export.note)q
  LEFT JOIN EventType et ON q.eve = et.id
  LEFT JOIN Client c ON q.client_id = c.id
WHERE q.oshib>0
  ORDER BY c.lastName,c.firstName,c.patrName
        '''% dict(begDate=db.formatDate(begDate),
                    endDate=db.formatDate(endDate),
                    condOrgStructure=condOrgStructure, 
                    cond=cond, 
                    dop1=dop1, 
                    dop2=dop2, 
                    dop3=dop3)
        db = QtGui.qApp.db
        return db.query(stmt)
        
    def selectData3(self, params): 
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        cond = self.getCond(params)
        chkDetailPerson   = params.get('detailPerson', False)
        if chkDetailPerson:
            dop1 = u''' ,IF(o.fullName IS NULL,'Не выбрано место выполнения',o.fullName) as org'''
            dop3 = u''' ,o.fullName'''
            dop2 = u''' left join ActionPropertyType apt9 on apt9.actionType_id = at.id and apt9.name = 'Куда направляется' and apt9.deleted = 0
    left join ActionProperty ap_dlit on ap_dlit.action_id = Action.id and ap_dlit.type_id = apt9.id
    left join ActionProperty_Organisation org on org.id = ap_dlit.id
  LEFT JOIN Organisation o ON org.value = o.id'''
        else:
            dop1 = u''' '''
            dop2 = u''' '''
            dop3 = u''' '''
        hospitalType = params.get('hospitalType', 0)
        if hospitalType == 1:
            if chkDetailPerson:
                order=u'o.fullName,date(Action.begDate), date(Action_Export.dateTime) desc'
            else:
                order=u'date(Action.begDate), date(Action_Export.dateTime) desc'
        else:
            order=u'date(Action.begDate), date(Action_Export.dateTime) desc'
        orgStructureId = params.get('orgStructureId', None)
        condOrgStructure = u''
        if orgStructureId:
            personIdList = getOrgStructurePersonIdList(orgStructureId)
            if personIdList:
                condOrgStructure = u''' AND p.id IN (%s)''' % (u','.join(str(personId) for personId in personIdList if personId))
            else: #Если нет врачей, то нечего выгружать
                return QtSql.QSqlQuery() #пустой QSqlQuery
        db = QtGui.qApp.db
        stmt = u'''SELECT date(Action.createDatetime) AS datvvod, date(Action.begDate) AS actionDate, date(Action_Export.dateTime) AS datvigr,
count(Action.`id`) AS vsego,
sum(CASE WHEN Action_Export.success = 1 THEN 1 ELSE 0 end) AS uspeh,
sum(CASE WHEN Action_Export.success = 0 THEN 1 ELSE 0 end) AS oshib,
GROUP_CONCAT(DISTINCT Action_Export.note) AS note,
  e.id AS event,CONCAT(e.setDate,' / ',IFNULL(e.execDate,'-')) AS dateEvent,e.client_id AS clien
  %(dop1)s
FROM Action
  Left join Event e on e.id = Action.event_id
  left join Contract c ON c.id = e.contract_id
  left JOIN rbFinance f ON f.id = c.finance_id
  LEFT JOIN rbExternalSystem es ON es.code = 'ТФОМС:План.госп.'
  LEFT JOIN Action_Export
    ON (Action_Export.`master_id` = Action.`id`)
    AND (Action_Export.`system_id` = es.id)
  LEFT JOIN ActionType at on at.id = Action.actionType_id
  LEFT JOIN Person p ON e.execPerson_id=p.id
    %(dop2)s
  left join Action as Moving on Moving.id = getNextActionId(Action.event_id, Action.id, (select id from ActionType where flatCode = 'moving' and deleted = 0), Action.begDate)
  left join Action as Moving2 on Moving2.id = getPrevActionId(Action.event_id, Action.id, (select id from ActionType where flatCode = 'moving' and deleted = 0), Action.begDate)
WHERE Action.`deleted` = 0
AND (at.flatCode = 'received' and Moving.id is not null AND f.code = '2' AND (/*LENGTH(e.srcNumber) > 0
and*/ e.order = 1 OR e.order not in (1, 6)) or at.flatCode = 'leaved' and Moving2.id is not null AND f.code = '2'
 or at.flatCode = 'planning'  AND f.code = '2'  OR at.flatCode = 'hospitalDirection'  AND f.code in ('2', '4'))
AND %(cond)s
and Action_Export.id is null
  AND DATE(Action.begDate) BETWEEN %(begDate)s AND %(endDate)s %(condOrgStructure)s
GROUP BY date(Action.begDate), date(Action_Export.dateTime),e.id  %(dop3)s
ORDER BY %(order)s;
        '''% dict(begDate=db.formatDate(begDate),
                    endDate=db.formatDate(endDate),
                    condOrgStructure=condOrgStructure, 
                    order=order, 
                    cond=cond, 
                    dop1=dop1, 
                    dop2=dop2, 
                    dop3=dop3)
        db = QtGui.qApp.db
        return db.query(stmt) 

    def getCond(self, params):
        db = QtGui.qApp.db
        cond = []
        hospitalType = params.get('hospitalType', 0)
        
            
        if hospitalType == 0:
            cond.append(u'at.flatCode in ("hospitalDirection", "received","planning") or at.flatCode = "leaved" and e.execDate is not null')
        if hospitalType == 1:
            cond.append(u'at.flatCode = "hospitalDirection"')
        if hospitalType == 2:
            cond.append(u'at.flatCode = "planning"')
        if hospitalType == 3:
            cond.append(u'at.flatCode = "received"')
        if hospitalType == 4:
            cond.append(u'at.flatCode = "leaved" and e.execDate is not null')
        return db.joinAnd(cond)

    def getDescription(self, params):
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        orgStructureId = params.get('orgStructureId', None)
        hospitalType = params.get('hospitalType', 0)
        rows = []
        rows.append(dateRangeAsStr(u'за период', begDate, endDate))
        if orgStructureId:
            rows.append(u'подразделение: ' + getOrgStructureFullName(orgStructureId))
        if hospitalType:
            rows.insert(10, u'типы реестров: %s' %
                          [u"не задано", u"Направление", u"Планирование", u"Госпитализация", u"Выписка"][
                              params.get("hospitalType", 0)])
        rows.append(u'отчёт составлен: ' + forceString(QDateTime.currentDateTime()))
        return rows


    def build(self, params):
        reportRowSize = 7
        reportData = {}
        chkDetailPerson   = params.get('detailPerson', False)
        secondTitle = u'Случаи не попадающие в выгрузку, или еще невыгруженные'

        def processQuery(query):
            while query.next():
                record = query.record()
                datvvod= forceDate(record.value('datvvod'))
                actionDate = forceDate(record.value('actionDate'))
                datvigr= forceDate(record.value('datvigr'))
                vsego = forceInt(record.value('vsego'))
                uspeh = forceInt(record.value('uspeh'))
                oshib = forceInt(record.value('oshib'))
                note = forceString(record.value('note'))
                org = forceString(record.value('org'))

                key = (datvvod, actionDate, datvigr, note, org)
                reportLine = reportData.setdefault(key, [0]*reportRowSize)
                reportLine[0] += vsego
                reportLine[1] += uspeh
                reportLine[2] += oshib


        query = self.selectData(params)
        processQuery(query)
        
        # now text
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertBlock()
        tableColumns = [
            ('10%',  [ u'Дата ввода'], CReportBase.AlignLeft),
            ('10%',  [ u'Дата мероприятия'], CReportBase.AlignLeft),
            ('10%',  [ u'Дата выгрузки'], CReportBase.AlignLeft),
            ('10%',  [ u'Всего введено результатов'], CReportBase.AlignLeft),
            ('10%',  [ u'Успешно выгружено'], CReportBase.AlignLeft),
            ('10%',  [ u'Выгружено с ошибками'], CReportBase.AlignLeft), 
            ('40%',  [ u'Ошибки'], CReportBase.AlignLeft)            
            ]


        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 6, 1, 3)
        for col in xrange(reportRowSize):
            table.mergeCells(0, col, 1, 1)


        totalByReport = [0]*reportRowSize
        colsShift = 3
        organisation = None
        
        keys = reportData.keys()
        keys.sort()
        def drawTotal(table, total, text): 
    
            row = table.addRow()

            table.setText(row, 0, text, CReportBase.TableHeader)
            table.mergeCells(row, 0, 1, 1)
            for col in xrange(reportRowSize):
                if (col<3):
                    table.setText(row, col + colsShift, total[col], fontBold=True)
        for key in keys:
            
            datvvod= key[0]
            actionDate = key[1]
            datvigr= key[2]
            note= key[3]
            org= key[4]
            
            reportLine = reportData[key]
            if chkDetailPerson and org!=organisation:
                row = table.addRow() 
                table.setText(row, 0, org)
                table.mergeCells(row, 0, 1, 7)
            
            row = table.addRow()          
            table.setText(row, 0, datvvod.toString("dd.MM.yyyy"))
            table.setText(row, 1, actionDate.toString("dd.MM.yyyy"))
            table.setText(row, 2, datvigr.toString("dd.MM.yyyy"))
            table.setText(row, 6, note)
            organisation = org
            for col in xrange(reportRowSize):
                if (col<3):
                    table.setText(row, col + colsShift, reportLine[col])
                totalByReport[col] = totalByReport[col] + reportLine[col]            
        #total
        drawTotal(table,  totalByReport, u'Итого');

        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertBlock()
        
        #2
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.setBlockFormat(CReportBase.AlignCenter)
    #    cursor.insertText(secondTitle)
        cursor.insertBlock()
        cursor.insertBlock()
        if chkDetailPerson:
            tableColumns = [
                ('5%',  [ u'Номер карточки'], CReportBase.AlignLeft),
                ('5%',  [ u'Код пациента'], CReportBase.AlignLeft),
                ('10%',  [ u'Фамилия'], CReportBase.AlignLeft),
                ('10%',  [ u'Имя'], CReportBase.AlignLeft),
                ('10%',  [ u'Отчество'], CReportBase.AlignLeft),
                ('10%',  [ u'Дата рождения'], CReportBase.AlignLeft),
                ('10%',  [ u'Тип события'], CReportBase.AlignLeft),
                ('10%',  [ u'Дата окончания действия/экспорта'], CReportBase.AlignLeft),
                ('10%',  [ u'Куда направлен'], CReportBase.AlignLeft),
                ('20%',  [ u'Ошибка'], CReportBase.AlignLeft)
                ]
        else:
            tableColumns = [
                ('5%',  [ u'Номер карточки'], CReportBase.AlignLeft),
                ('5%',  [ u'Код пациента'], CReportBase.AlignLeft),
                ('10%',  [ u'Фамилия'], CReportBase.AlignLeft),
                ('10%',  [ u'Имя'], CReportBase.AlignLeft),
                ('10%',  [ u'Отчество'], CReportBase.AlignLeft),
                ('10%',  [ u'Дата рождения'], CReportBase.AlignLeft),
                ('10%',  [ u'Тип события'], CReportBase.AlignLeft),
                ('15%',  [ u'Дата окончания действия/экспорта'], CReportBase.AlignLeft),
                ('25%',  [ u'Ошибка'], CReportBase.AlignLeft)
                ]

        table = createTable(cursor, tableColumns)
        query = self.selectData1(params)
        while query.next():
            record = query.record()
            ev = forceString(record.value('ev'))
            cl = forceInt(record.value('cl'))
            las = forceString(record.value('las'))
            fir = forceString(record.value('fir'))
            pat = forceString(record.value('pat'))
            hap = forceString(record.value('hap'))
            tip = forceString(record.value('tip'))
            dat = forceString(record.value('dat'))
            osh = forceString(record.value('osh'))
            org = forceString(record.value('org'))
            row = table.addRow()
            
            if chkDetailPerson:
                table.setHtml(row, 0,u"<a href='event_" + str(ev) + u"'><span style='color: rgb(FF, FF, FF);'>" + str(ev) + "</span></a>")
                table.setText(row, 1, cl)
                table.setText(row, 2, las)
                table.setText(row, 3, fir)
                table.setText(row, 4, pat)
                table.setText(row, 5, hap)
                table.setText(row, 6, tip)
                table.setText(row, 7, dat)
                table.setText(row, 8, org)
                table.setText(row, 9, osh)
            else:
                table.setHtml(row, 0,u"<a href='event_" + str(ev) + u"'><span style='color: rgb(FF, FF, FF);'>" + str(ev) + "</span></a>")
                table.setText(row, 1, cl)
                table.setText(row, 2, las)
                table.setText(row, 3, fir)
                table.setText(row, 4, pat)
                table.setText(row, 5, hap)
                table.setText(row, 6, tip)
                table.setText(row, 7, dat)
                table.setText(row, 8, osh)
                
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertBlock()
        
        #2
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.setBlockFormat(CReportBase.AlignCenter)
        cursor.insertText(secondTitle)
        cursor.insertBlock()
        cursor.insertBlock()
        tableColumns = [
            ('10%',  [ u'Дата ввода'], CReportBase.AlignLeft),
            ('10%',  [ u'Дата мероприятия'], CReportBase.AlignLeft),
            ('10%',  [ u'Дата выгрузки'], CReportBase.AlignLeft),
            ('10%',  [ u'Успешно выгружено'], CReportBase.AlignLeft),
            ('10%',  [ u'Выгружено с ошибками'], CReportBase.AlignLeft), 
            ('10%',  [ u'Код события'], CReportBase.AlignLeft),        
            ('30%',  [ u'Дата события'], CReportBase.AlignLeft),        
            ('10%',  [ u'Код пациента'], CReportBase.AlignLeft)       
            ]

        table = createTable(cursor, tableColumns)
        query = self.selectData3(params)
        while query.next():
            record = query.record()
            datvvod = forceString(record.value('datvvod'))
            actionDate = forceString(record.value('actionDate'))
            datvigr = forceString(record.value('datvigr'))
            uspeh = forceString(record.value('uspeh'))
            oshib = forceString(record.value('oshib'))
            event = forceString(record.value('event'))
            dateEvent = forceString(record.value('dateEvent'))
            clien = forceString(record.value('clien'))
            row = table.addRow()
            
            
            table.setText(row, 0, datvvod)
            table.setText(row, 1, actionDate)
            table.setText(row, 2, datvigr)
            table.setText(row, 3, uspeh)
            table.setText(row, 4, oshib)
            table.setText(row, 5, event)
            table.setText(row, 6, dateEvent)
            table.setText(row, 7, clien)
    
        return doc

class CFinReestrSetupDialog(CReportSetupDialog):
    def __init__(self, parent=None):
        CReportSetupDialog.__init__(self, parent)
        self.setEventTypeVisible(False)
        self.setOnlyPermanentAttachVisible(False)
        self.chkDetailPerson.setVisible(True)
        self.setOrgStructureVisible(True)
        


        #страховая организация
        # self.cmbInsurer = CInsurerComboBox(self)
        # self.cmbInsurer.setObjectName("cmbInsurer")
        # self.gridLayout.addWidget(self.cmbInsurer, 11, 2, 1, 2)
        # self.lblInsurer = QtGui.QLabel(self)
        # self.lblInsurer.setText(u'Страховая организация')
        # self.lblInsurer.setObjectName("lblInsurer")
        # self.gridLayout.addWidget(self.lblInsurer, 11, 0, 1, 2)
        # self.lblInsurer.setBuddy(self.cmbInsurer)
        #Типы реестров
        self.cmbhospitalType = QtGui.QComboBox(self)
        self.cmbhospitalType.setObjectName("cmbhospitalType")
        self.cmbhospitalType.addItems([u"не задано", u"Направление", u"Планирование", u"Госпитализация", u"Выписка"])
        #QWidget * widget, int fromRow, int fromColumn, int rowSpan, int columnSpan, Qt::Alignment alignment = 0
        self.gridLayout.addWidget(self.cmbhospitalType, 12, 1, 1, 1)
        self.lblhospitalType = QtGui.QLabel(self)
        self.lblhospitalType.setText(u'Тип госпитализации')
        self.chkDetailPerson.setEnabled(False)
        self.chkDetailPerson.setText(u'Детализовать по Целевым МО')
        self.lblhospitalType.setObjectName("lblhospitalType")
        self.gridLayout.addWidget(self.lblhospitalType, 12, 0, 1, 1)
        self.lblhospitalType.setBuddy(self.cmbhospitalType)
        #Детализировать по плательщикам
        
        self.cmbhospitalType.activated[str].connect(self.onActivated)
        

        #self.lblDetail.enterEvent = lambda self, event: self.chkDetail.enterEvent(self.chkDetail, event)
    def setTitle(self, title):
        self.setWindowTitle(title)

    def setParams(self, params):
        self.cmbhospitalType.setCurrentIndex(params.get('hospitalType', 0))
        self.chkDetailPerson.setChecked(params.get('detailPerson', False))
        #self.cmbInsurer.setValue(params.get('insurerId', None))
        CReportSetupDialog.setParams(self, params)

    def params(self):
        result = CReportSetupDialog.params(self)
        result['hospitalType'] = self.cmbhospitalType.currentIndex()
        result['detailPerson'] = self.chkDetailPerson.isChecked()
        return result
        
    def onActivated(self, text):
        if self.cmbhospitalType.currentIndex() == 1:
            self.chkDetailPerson.setEnabled(True)
        else:
            self.chkDetailPerson.setEnabled(False)
            self.chkDetailPerson.setChecked(False)
