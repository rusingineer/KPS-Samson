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
from Reports.ReportSetupDialog import CReportSetupDialog
  
    
class CRep060Y(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Журнал учета инфекционных заболеваний')
        
    def getSetupDialog(self, parent):
        result = CReportSetupDialog(parent)
        result.setEventTypeVisible(False)
        result.setTimePeriodVisible(True)
        result.setOnlyPermanentAttachVisible(False)
        result.setTitle(self.title())
        result.resize(result.minimumSize())
        return result
        
    def selectData(self, params):    
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        begTime = params.get('begTime', QTime())
        endTime = params.get('endTime', QTime())
        if not endDate or endDate.isNull():
            return None
        db = QtGui.qApp.db
        stmt = u'''
  SELECT 
    MAX(a.id),
    aps_noticeNumber.value AS noticeNumber,
    convert(CONCAT('Прием ', IFNULL(apd_noticePhoneDate.value, '-'), ', ', 
            IFNULL(apt_noticePhoneTime.value, '-'), ', отсылка ', 
            IFNULL(apd_noticeSendDate.value, '-'), ', передал ', 
            CONCAT(IFNULL(p.lastName, '-'), ' ', IFNULL(p.firstName, '-'), ' ', IFNULL(p.patrName, '-')), 
            ', принял ', IFNULL(aps_noticeGetPerson.value, '-')), char) AS noticeData, 
    o.fullName AS orgName,
    CONCAT(IFNULL(c.lastName, ''),' ',IFNULL(c.firstName, ''),' ',IFNULL(c.patrName, '')) AS clientFIO,
    if (age(c.birthDate,a.begDate)<3,
        c.birthDate,age(c.birthDate,a.begDate)) AS clientAge, 
    getClientLocAddress(c.id) AS clientAddress,
    if (cw.freeInput IS NULL OR cw.freeInput='','безработный',cw.freeInput) AS clientWork,
    IFNULL(apd_lastVisitWorkDate.value, '') as clientWorkDate,
    apd_dateIllness.value AS dateIllness,
    CONCAT(a.MKB,', ',apd_diagnosisDate.value) AS setDiagnosis,
    CONCAT(apd_hospitalDate.value, ', ', o_hospital.fullName) AS hospital,
    apd_firstVisit.value AS firstVisit,
    aps_diagnosis.value AS diagnosis,
    '' AS dateEpid,
    '' AS diagReport,
    aps_lab.value as lab,
    '' AS note
  FROM Action a 
    LEFT JOIN ActionType at ON a.actionType_id = at.id
    LEFT JOIN Event e ON a.event_id = e.id
    LEFT JOIN Client c ON e.client_id = c.id
    LEFT JOIN ClientWork cw ON c.id = cw.client_id and cw.id = (SELECT MAX(cl.id) FROM ClientWork cl WHERE cl.deleted=0 AND cl.client_id=c.id)
    LEFT JOIN Organisation o ON e.org_id = o.id   
    LEFT JOIN ActionProperty ap_lastVisitWorkDate on ap_lastVisitWorkDate.action_id = a.id and ap_lastVisitWorkDate.type_id in (select id from ActionPropertyType where name = 'Дата телефонограммы') AND ap_lastVisitWorkDate.deleted = 0
    LEFT JOIN ActionProperty_Date apd_lastVisitWorkDate on apd_lastVisitWorkDate.id = ap_lastVisitWorkDate.id  
    LEFT JOIN ActionProperty ap_noticeNumber on ap_noticeNumber.action_id = a.id and ap_noticeNumber.type_id in (select id from ActionPropertyType where name = 'Номер извещения') AND ap_noticeNumber.deleted = 0
    LEFT JOIN ActionProperty_String aps_noticeNumber on aps_noticeNumber.id = ap_noticeNumber.id  
    LEFT JOIN ActionProperty ap_noticePhoneDate on ap_noticePhoneDate.action_id = a.id and ap_noticePhoneDate.type_id in (select id from ActionPropertyType where name = 'Дата телефонограммы') AND ap_noticePhoneDate.deleted = 0
    LEFT JOIN ActionProperty_Date apd_noticePhoneDate on apd_noticePhoneDate.id = ap_noticePhoneDate.id  
    LEFT JOIN ActionProperty ap_noticePhoneTime on ap_noticePhoneTime.action_id = a.id and ap_noticePhoneTime.type_id in (select id from ActionPropertyType where name = 'Время телефонограммы') AND ap_noticePhoneTime.deleted = 0
    LEFT JOIN ActionProperty_Time apt_noticePhoneTime on apt_noticePhoneTime.id = ap_noticePhoneTime.id 
    LEFT JOIN ActionProperty ap_noticeSendDate on ap_noticeSendDate.action_id = a.id and ap_noticeSendDate.type_id in (select id from ActionPropertyType where name = 'Дата отправки извещения') AND ap_noticeSendDate.deleted = 0
    LEFT JOIN ActionProperty_Date apd_noticeSendDate on apd_noticeSendDate.id = ap_noticeSendDate.id   
    LEFT JOIN Person p ON p.id = a.person_id
    LEFT JOIN ActionProperty ap_noticeGetPerson on ap_noticeGetPerson.action_id = a.id and ap_noticeGetPerson.type_id in (select id from ActionPropertyType where name = 'Извещение принял') AND ap_noticeGetPerson.deleted = 0
    LEFT JOIN ActionProperty_String aps_noticeGetPerson on aps_noticeGetPerson.id = ap_noticeGetPerson.id
    LEFT JOIN ActionProperty ap_dateIllness on ap_dateIllness.action_id = a.id and ap_dateIllness.type_id in (select id from ActionPropertyType where name like 'Дата заболевания%') AND ap_dateIllness.deleted = 0
    LEFT JOIN ActionProperty_Date apd_dateIllness on apd_dateIllness.id = ap_dateIllness.id
    LEFT JOIN ActionProperty ap_diagnosisDate on ap_diagnosisDate.action_id = a.id and ap_diagnosisDate.type_id in (select id from ActionPropertyType where name = 'Дата установления диагноза') AND ap_diagnosisDate.deleted = 0
    LEFT JOIN ActionProperty_Date apd_diagnosisDate on apd_diagnosisDate.id = ap_diagnosisDate.id
    LEFT JOIN ActionProperty ap_hospital on ap_hospital.action_id = a.id and ap_hospital.type_id in (select id from ActionPropertyType where name = 'Госпитализирован') AND ap_hospital.deleted = 0
    LEFT JOIN ActionProperty_Organisation apo_hospital on apo_hospital.id = ap_hospital.id
    LEFT JOIN Organisation o_hospital ON apo_hospital.value = o_hospital.id 
    LEFT JOIN ActionProperty ap_hospitalDate on ap_hospitalDate.action_id = a.id and ap_hospitalDate.type_id in (select id from ActionPropertyType where name = 'Дата госпитализации') AND ap_hospitalDate.deleted = 0
    LEFT JOIN ActionProperty_Date apd_hospitalDate on apd_hospitalDate.id = ap_hospitalDate.id
    LEFT JOIN ActionProperty ap_firstVisit on ap_firstVisit.action_id = a.id and ap_firstVisit.type_id in (select id from ActionPropertyType where name = 'Дата первого обращения') AND ap_firstVisit.deleted = 0
    LEFT JOIN ActionProperty_Date apd_firstVisit on apd_firstVisit.id = ap_firstVisit.id
    LEFT JOIN ActionProperty ap_diagnosis on ap_diagnosis.action_id = a.id and ap_diagnosis.type_id in (select id from ActionPropertyType where name = 'Диагноз при обращении') AND ap_diagnosis.deleted = 0
    LEFT JOIN ActionProperty_String aps_diagnosis on aps_diagnosis.id = ap_diagnosis.id
    LEFT JOIN ActionProperty ap_lab on ap_lab.action_id = a.id and ap_lab.type_id in (select id from ActionPropertyType where name = 'Лабораторное обследование и его результат') AND ap_lab.deleted = 0
    LEFT JOIN ActionProperty_String aps_lab on aps_lab.id = ap_lab.id
  WHERE 
    at.flatCode='j_specsl'
    AND a.deleted=0 
    AND e.deleted=0 
    AND at.deleted=0 
    AND c.deleted=0 
    AND a.begDate BETWEEN {} AND {}
  GROUP BY e.id
  ORDER BY noticeNumber
        '''.format(("'"+ (db.formatDate(begDate).replace("'", "") + ' ' + db.formatTime(begTime).replace("'","") + "'")) ,
                   ("'"+ (db.formatDate(endDate).replace("'", "") + ' ' + db.formatTime(endTime).replace("'","") + "'")),)
        db = QtGui.qApp.db
        return db.query(stmt)
        
       
    def build(self, params):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        #рисуем первую табличку
        tableColumns = [
            ('3%',  [ u'N п/п', '1'], CReportBase.AlignLeft),
            ('9%',  [ u'Дата и часы сообщения (приема) по телефону и дата отсылки (получения) первичного экстренного извещения, кто передал, кто принял	', '2'], CReportBase.AlignRight),
            ('8%',  [ u'Наименование лечебного учреждения, сделавшего сообщение', '3'], CReportBase.AlignRight),
            ('7%',  [ u'Фамилия, имя, отчество больного', '4'], CReportBase.AlignRight), 
            ('3%',  [ u'Возраст (для детей до 3 лет указать месяц и год рождения)', '5'], CReportBase.AlignRight),
            ('6%',  [ u'Домашний адрес (город, село, улица, дом N, кв. N)', '6'], CReportBase.AlignRight),
            ('6%',  [ u'Наименование места работы, учебы, дошкольного детского учреждения, группа, класс, дата последнего посещения', '7'], CReportBase.AlignRight),
            ('4%',  [ u'Дата заболевания', '8'], CReportBase.AlignRight),
            ('6%',  [ u'Диагноз и дата его установления', '9'], CReportBase.AlignRight),
            ('8%',  [ u'Дата, место госпитализации', '10'], CReportBase.AlignRight),
            ('6%',  [ u'Дата первичного обращения', '11'], CReportBase.AlignRight),
            ('6%',  [ u'Измененный (уточненный) диагноз и дата его установления', '12'], CReportBase.AlignRight),
            ('6%',  [ u'Дата эпид. обследования Фамилия обследовавшего', '13'], CReportBase.AlignRight),
            ('6%',  [ u'Сообщено о заболеваниях (в СЭС по месту постоянного жительства, в детское учреждение, по месту учебы, работы и др.)', '14'], CReportBase.AlignRight),
            ('6%',  [ u'Лабораторное обследование и его результат', '15'], CReportBase.AlignRight),
            ('6%',  [ u'Примечание', '16'], CReportBase.AlignRight),
            ]

        table = createTable(cursor, tableColumns)
        query = self.selectData(params)
        while query.next():
            record = query.record()
            noticeNumber = forceString(record.value('noticeNumber'))
            noticeData = forceString(record.value('noticeData'))
            orgName = forceString(record.value('orgName'))
            clientFIO = forceString(record.value('clientFIO'))
            clientAge = forceString(record.value('clientAge'))
            clientAddress = forceString(record.value('clientAddress'))
            clientWork = forceString(record.value('clientWork'))
            clientWorkDate = forceString(record.value('clientWorkDate'))
            dateIllness = forceString(record.value('dateIllness'))
            setDiagnosis = forceString(record.value('setDiagnosis'))
            hospital = forceString(record.value('hospital'))
            firstVisit = forceString(record.value('firstVisit'))
            diagnosis = forceString(record.value('diagnosis'))
            dateEpid = forceString(record.value('dateEpid'))
            diagReport = forceString(record.value('diagReport'))
            lab = forceString(record.value('lab'))
            note = forceString(record.value('note'))
            row = table.addRow()
            #table.mergeCells(0, 0, 1, 1)
            table.setText(row, 0, noticeNumber)
            table.setText(row, 1, noticeData)
            table.setText(row, 2, orgName)  
            table.setText(row, 3, clientFIO)
            table.setText(row, 4, clientAge)
            table.setText(row, 5, clientAddress)  
            table.setText(row, 6, clientWork + ", {}".format(clientWorkDate) if clientWorkDate else '') 
            table.setText(row, 7, dateIllness)
            table.setText(row, 8, setDiagnosis)
            table.setText(row, 9, hospital)  
            table.setText(row, 10, firstVisit)
            table.setText(row, 11, diagnosis)
            table.setText(row, 12, dateEpid)  
            table.setText(row, 13, diagReport)
            table.setText(row, 14, lab)
            table.setText(row, 15, note)
        

        return doc
