# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012 SAMSON Group. All rights reserved.
## Copyright (C) 2015 Oskin A.
## Copyright (C) 2016 Oskin A. and Arkhipov S.
## Copyright (C) 2021 Arkhipov S.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################


from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import *

from Orgs.Utils import *
from library import xlwt
from library.database import *

from library.Utils import *
from Reports.Report import CReport
from Reports.ReportBase import *
from Reports.Ui_PeopleOfCancerSetupDialog import Ui_PeopleOfCancerSetupDialog
from Reports.ReportPeopleOfCancer import CPeopleOfCancerSetupDialog

def selectData(begDate, endDate, areaId, specialityId, invoice, personId, ageFrom, ageTo, eventTypeId):
    stmt = u"""
SELECT Organisation.infisCode, Organisation.fullName, Client.lastname,Client.firstname,Client.patrname, Client.birthDate, 
  IFNULL(ci.identifier, ClientPolicy.number) AS police, 
  formatSNILS(Client.SNILS) as SNILS, Diagnosis.MKB, rbSpeciality.name AS speciality_name,
   case when rbMedicalAidType.regionalCode in ("11","12","301","302","401","402") then "Стационар"
when rbMedicalAidType.regionalCode in ("41","42","411","422","51","52","511","522","71","72","90","43") then "Дневной стационар"
when rbMedicalAidType.regionalCode in ("21","22","31","32","60","80","01","02","111","112","222","201","202","232","211","241","242","252","261","262","271","272","281","282","233") then "Поликлиника" end as conition_names,
   CASE 
  WHEN rbMedicalAidType.regionalCode in ("11","12","301","302","401","402","41","42","411","422","51","52","511","522","71","72","90","43") THEN rbService.infis
  ELSE rbService.infis
END as name_service, date(Event.execDate) as begDate, date(Event.execDate) as endDate, Client.id
  FROM Event
  left JOIN Person ON Event.execPerson_id = Person.id
  LEFT JOIN rbSpeciality ON Person.speciality_id = rbSpeciality.id
  LEFT JOIN Diagnostic ON Event.id = Diagnostic.event_id
  LEFT JOIN Diagnosis ON Diagnostic.diagnosis_id = Diagnosis.id
  LEFT JOIN Client ON Event.client_id = Client.id
  LEFT JOIN ClientPolicy ON ClientPolicy.id = getClientPolicyId(Client.id, 1)
  LEFT JOIN ClientIdentification ci on ci.id = (SELECT cci.id from ClientIdentification cci 
      INNER JOIN rbAccountingSystem on rbAccountingSystem.id=cci.accountingSystem_id WHERE cci.deleted=0 and 
      cci.client_id=Client.id and rbAccountingSystem.code = 'ENP' LIMIT 1)  
  left JOIN Organisation ON Event.org_id = Organisation.id
  LEFT JOIN rbPolicyKind ON ClientPolicy.policyKind_id = rbPolicyKind.id
  LEFT JOIN EventType ON EventType.id=Event.eventType_id
  LEFT JOIN rbMedicalAidType ON rbMedicalAidType.id=EventType.medicalAidType_id
  LEFT JOIN ClientAttach ON ClientAttach.id = getClientAttachId(Client.id, 2)
  LEFT JOIN rbDispanser ON rbDispanser.id = Diagnostic.dispanser_id
  %(leftjoin1)s
WHERE
    %(cond)s %(cond2)s
    UNION
    SELECT Organisation.infisCode, Organisation.fullName, Client.lastname,Client.firstname,Client.patrname, Client.birthDate, 
  IFNULL(ci.identifier, ClientPolicy.number) AS police, 
  formatSNILS(Client.SNILS) as SNILS, Diagnosis.MKB, rbSpeciality.name AS speciality_name, 
  case when rbMedicalAidType.regionalCode in ("11","12","301","302","401","402") then "Стационар"
when rbMedicalAidType.regionalCode in ("41","42","411","422","51","52","511","522","71","72","90","43") then "Дневной стационар"
when rbMedicalAidType.regionalCode in ("21","22","31","32","60","80","01","02","111","112","222","201","202","232","211","241","242","252","261","262","271","272","281","282","233") then "Поликлиника" end as conition_names,
   CASE 
  WHEN rbMedicalAidType.regionalCode in ("11","12","301","302","401","402","41","42","411","422","51","52","511","522","71","72","90","43") THEN rbService.infis
  ELSE rbService.infis
END as name_service, date(Action.begDate) as begDate, date(Action.endDate) as endDate, Client.id
  
  FROM Event
  LEFT JOIN Action ON Event.id = Action.event_id
  left JOIN Person ON Action.person_id = Person.id
  LEFT JOIN rbSpeciality ON Person.speciality_id = rbSpeciality.id
  LEFT JOIN Diagnostic ON Event.id = Diagnostic.event_id
  LEFT JOIN Diagnosis ON Diagnostic.diagnosis_id = Diagnosis.id
  LEFT JOIN Client ON Event.client_id = Client.id
  LEFT JOIN ClientPolicy ON ClientPolicy.id = getClientPolicyId(Client.id, 1)
  LEFT JOIN ClientIdentification ci on ci.id = (SELECT cci.id from ClientIdentification cci 
      INNER JOIN rbAccountingSystem on rbAccountingSystem.id=cci.accountingSystem_id WHERE cci.deleted=0 and 
      cci.client_id=Client.id and rbAccountingSystem.code = 'ENP' LIMIT 1)
  left JOIN Organisation ON Event.org_id = Organisation.id
  LEFT JOIN rbPolicyKind ON ClientPolicy.policyKind_id = rbPolicyKind.id
  LEFT JOIN EventType ON EventType.id=Event.eventType_id
  LEFT JOIN rbMedicalAidType ON rbMedicalAidType.id=EventType.medicalAidType_id
  LEFT JOIN ClientAttach ON ClientAttach.id = getClientAttachId(Client.id, 2)
  LEFT JOIN rbDispanser ON rbDispanser.id = Diagnostic.dispanser_id
  %(leftjoin2)s
WHERE
    %(cond)s
"""
    db = QtGui.qApp.db
    tableDiagnosis = db.table('Diagnosis')
    tableRbService = db.table('rbService')
    tableClientAttach = db.table('ClientAttach')
    tableClientDispanser = db.table('rbDispanser')
    tablePerson = db.table('Person')
    tableEvent = db.table('Event')
    tableEventType = db.table('EventType')
    cond = []
    cond.append(tableDiagnosis['deleted'].eq(0))
    cond.append(tableEvent['deleted'].eq(0))
    cond.append(tableClientDispanser['observed'].eq(1))
    cond.append(tableDiagnosis['diagnosisType_id'].inlist([1, 2]))
    cond.append(tableEventType['form'].inlist(["025", "030", "003"]))

    addDateInRange(cond, tableEvent['execDate'], begDate, endDate)
    cond.append(db.joinOr([tableDiagnosis['MKB'].eq("E78")
                              , db.joinAnd([tableDiagnosis['MKB'].ge("I05"), tableDiagnosis['MKB'].le("I09")])
                              , db.joinAnd([tableDiagnosis['MKB'].ge("I10"), tableDiagnosis['MKB'].le("I15")])
                              , db.joinAnd([tableDiagnosis['MKB'].ge("I20"), tableDiagnosis['MKB'].le("I25")])
                              , tableDiagnosis['MKB'].eq("I26")
                              , tableDiagnosis['MKB'].eq("I27.0")
                              , tableDiagnosis['MKB'].eq("I27.2")
                              , tableDiagnosis['MKB'].eq("I27.8")
                              , tableDiagnosis['MKB'].eq("I28")
                              , tableDiagnosis['MKB'].eq("I33")
                              , db.joinAnd([tableDiagnosis['MKB'].ge("I34"), tableDiagnosis['MKB'].le("I37")])
                              , db.joinAnd([tableDiagnosis['MKB'].ge("I38"), tableDiagnosis['MKB'].le("I39")])
                              , tableDiagnosis['MKB'].eq("I40")
                              , tableDiagnosis['MKB'].eq("I41")
                              , tableDiagnosis['MKB'].eq("I42")
                              , db.joinAnd([tableDiagnosis['MKB'].ge("I44"), tableDiagnosis['MKB'].le("I49")])
                              , tableDiagnosis['MKB'].eq("I50.0")
                              , tableDiagnosis['MKB'].eq("I50.1")
                              , tableDiagnosis['MKB'].eq("I50.9")
                              , db.joinAnd([tableDiagnosis['MKB'].ge("I51.0"), tableDiagnosis['MKB'].le("I51.2")])
                              , tableDiagnosis['MKB'].eq("I51.4")
                              , tableDiagnosis['MKB'].eq("I65.2")
                              , tableDiagnosis['MKB'].eq("I67.8")
                              , db.joinAnd([tableDiagnosis['MKB'].ge("I69.0"), tableDiagnosis['MKB'].le("I69.4")])
                              , tableDiagnosis['MKB'].eq("I71")
                              , db.joinAnd([tableDiagnosis['MKB'].ge("Q20"), tableDiagnosis['MKB'].le("Q28")])
                              , tableDiagnosis['MKB'].eq("Z95.0")
                              , tableDiagnosis['MKB'].eq("Z95.1")
                              , db.joinAnd([tableDiagnosis['MKB'].ge("Z95.2"), tableDiagnosis['MKB'].le("I95.4")])
                              , tableDiagnosis['MKB'].eq("I95.5")
                              , tableDiagnosis['MKB'].eq("I95.8")
                              , tableDiagnosis['MKB'].eq("I95.9")
                           ]))

    if areaId:
        orgStructureIdList = getOrgStructureDescendants(areaId)
        cond.append(tableClientAttach['orgStructure_id'].inlist(orgStructureIdList))
    if ageFrom <= ageTo:
        cond.append('Diagnosis.endDate >= ADDDATE(Client.birthDate, INTERVAL %d YEAR)' % ageFrom)
        cond.append('Diagnosis.endDate < SUBDATE(ADDDATE(Client.birthDate, INTERVAL %d YEAR),1)' % (ageTo + 1))
    if specialityId:
        cond.append(tablePerson['speciality_id'].eq(specialityId))
    if personId:
        cond.append(tablePerson['id'].eq(personId))
    if invoice:
        join_smt_2 = '''LEFT JOIN Account_Item ON Action.id = Account_Item.action_id
                  LEFT JOIN rbService ON Account_Item.service_id = rbService.id'''
        join_smt_1 = '''LEFT JOIN Account_Item ON Event.id = Account_Item.event_id
                  LEFT JOIN rbService ON Account_Item.service_id = rbService.id'''
        cond2 = 'AND Account_Item.action_id is null and Account_Item.visit_id is null'
    else:
        join_smt_1 = '''LEFT JOIN Visit ON Visit.event_id = Event.id
        LEFT JOIN rbService ON rbService.id = IFNULL(Visit.service_id, EventType.service_id)'''
        join_smt_2 = '''LEFT JOIN ActionType on Action.actionType_id = ActionType.id
          LEFT JOIN ActionType_Service  ON ActionType.id = ActionType_Service.master_id
          LEFT JOIN rbService ON ActionType_Service.service_id = rbService.id'''
        cond2 = ' and Visit.deleted=0'
    cond.append(tableRbService['id'].isNotNull())
    cond.append(tableRbService['name'].like(u'%диспансер%'))
    cond.append(tableRbService['endDate'].ge(endDate))
    if eventTypeId:
        cond.append(tableClientDispanser['id'].eq(eventTypeId))
    return db.query(stmt % dict(leftjoin1=join_smt_1,
                                leftjoin2=join_smt_2,
                                cond=db.joinAnd(cond),
                                cond2=cond2))


class CPeopleWithDiseasesCirculatorySystem(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Список пациентов с болезнями системы кровообращения, состоящие на диспансерном учёте и '
                      u'получающие медицинскую помощь')

    def getSetupDialog(self, parent):
        result = CPeopleOfCancerSetupDialog(parent)
        result.setTitle(self.title())
        return result

    def build(self, params):
        def printHeader(sheet, rowNumber):
            #table header
            sheet.set_portrait(False)
            sheet.set_print_scaling(70)

            sheet.col(0).width = 256 * 5
            sheet.col(1).width = 256 * 10
            sheet.col(2).width = 256 * 30
            sheet.col(3).width = 256 * 20
            sheet.col(4).width = 256 * 20
            sheet.col(5).width = 256 * 20
            sheet.col(6).width = 256 * 10
            sheet.col(7).width = 256 * 15
            sheet.col(8).width = 256 * 15
            sheet.col(9).width = 256 * 5
            sheet.col(10).width = 256 * 15
            sheet.col(11).width = 256 * 15
            sheet.col(12).width = 256 * 10
            sheet.col(13).width = 256 * 10
            sheet.col(14).width = 256 * 10

            styleHeader = xlwt.Style.easyxf(
                "align: horizontal center, wrap true; font: bold true, name Times New Roman, height 220; borders: top thin, bottom thin, left thin, right thin;")
            sheet.write(rowNumber, 0, u'№ п/п', style=styleHeader)
            sheet.write(rowNumber, 1, u'Код юр. лица медицинской организации (SPR01)', style=styleHeader)
            sheet.write(rowNumber, 2, u'Наименование медицинской организации', style=styleHeader)
            sheet.write(rowNumber, 3, u'Фамилия', style=styleHeader)
            sheet.write(rowNumber, 4, u'Имя', style=styleHeader)
            sheet.write(rowNumber, 5, u'Отчество', style=styleHeader)
            sheet.write(rowNumber, 6, u'Дата рождения', style=styleHeader)
            sheet.write(rowNumber, 7, u'ЕНП', style=styleHeader)
            sheet.write(rowNumber, 8, u'СНИЛС', style=styleHeader)
            sheet.write(rowNumber, 9, u'МКБ-10 (SPR20)', style=styleHeader)
            sheet.write(rowNumber, 10, u'Состоит под диспансерным наблюдением по специальности врача', style=styleHeader)
            sheet.write(rowNumber, 11, u'Условие оказания помощи (SPR34)', style=styleHeader)
            sheet.write(rowNumber, 12, u'Оказанная услуга (SPR18, по ОМС)', style=styleHeader)
            sheet.write(rowNumber, 13, u'Дата начала оказания услуги', style=styleHeader)
            sheet.write(rowNumber, 14, u'Дата окончания оказания услуги', style=styleHeader)

        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        areaId = params.get('areaId', None)
        specialityId = params.get('specialityId', None)
        invoice = params.get('invoice', False)
        personId = params.get('personId', None)
        ageFrom = params.get('ageFrom', 0)
        ageTo = params.get('ageTo', 150)
        eventTypeId = params.get('eventTypeId', None)

        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportBody)

        query = selectData(begDate, endDate, areaId, specialityId, invoice, personId, ageFrom, ageTo, eventTypeId)
        dict_with_data = dict()
        while query.next():
            record = query.record()
            infisCode = forceString(record.value('infisCode'))
            fullName = forceString(record.value('fullName'))
            clientId = forceInt(record.value('id'))
            lastname = forceString(record.value('lastname'))
            firstname = forceString(record.value('firstname'))
            patrname = forceString(record.value('patrname'))
            birthDate = forceString(record.value('birthDate'))
            police = forceString(record.value('police'))
            SNILS = forceString(record.value('SNILS'))
            MKB = forceString(record.value('MKB'))
            speciality_name = forceString(record.value('speciality_name'))
            conition_names = forceString(record.value('conition_names'))
            begDate = forceString(record.value('begDate'))
            endDate = forceString(record.value('endDate'))
            name_service = forceString(record.value('name_service'))
            dict_with_data.setdefault(clientId, [])
            dict_with_data[clientId].append({
                'infisCode': infisCode,
                'fullName': fullName,
                'lastname': lastname,
                'firstname': firstname,
                'patrname': patrname,
                'birthDate': birthDate,
                'police': police,
                'SNILS': SNILS,
                'MKB': MKB,
                'speciality_name': speciality_name,
                'conition_names': conition_names,
                'begDate': begDate,
                'endDate': endDate,
                'name_service': name_service
            })

        workbook = xlwt.Workbook()
        pageNumber = 1
        sheet = workbook.add_sheet(u'Лист%d' % pageNumber)
        printHeader(sheet, 0)

        styleRow = xlwt.Style.easyxf(
            "align: horizontal center; font: name Times New Roman; borders: top thin, bottom thin, left thin, right thin;")
        rowNumber = 0
        rowsCount = 0
        for each_client in sorted(dict_with_data, key=lambda x: dict_with_data[x][0]["lastname"]):
            for each_act in dict_with_data[each_client]:
                rowNumber += 1
                if rowNumber == 65536:
                    pageNumber += 1
                    sheet = workbook.add_sheet(u'Лист%d' % pageNumber)
                    rowNumber = 0
                    printHeader(sheet, rowNumber)
                    rowNumber += 1

                sheet.write(rowNumber, 0, rowNumber, style=styleRow)
                sheet.write(rowNumber, 1, each_act['infisCode'], style=styleRow)
                sheet.write(rowNumber, 2, each_act['fullName'], style=styleRow)
                sheet.write(rowNumber, 3, each_act['lastname'], style=styleRow)
                sheet.write(rowNumber, 4, each_act['firstname'], style=styleRow)
                sheet.write(rowNumber, 5, each_act['patrname'], style=styleRow)
                sheet.write(rowNumber, 6, each_act['birthDate'], style=styleRow)
                # enp = u'\xa0' + each_act['police']
                sheet.write(rowNumber, 7, each_act['police'], style=styleRow)
                sheet.write(rowNumber, 8, each_act['SNILS'], style=styleRow)
                sheet.write(rowNumber, 9, each_act['MKB'], style=styleRow)
                sheet.write(rowNumber, 10, each_act['speciality_name'], style=styleRow)
                sheet.write(rowNumber, 11, each_act['conition_names'], style=styleRow)
                sheet.write(rowNumber, 12, each_act['name_service'], style=styleRow)
                sheet.write(rowNumber, 13, each_act['begDate'], style=styleRow)
                sheet.write(rowNumber, 14, each_act['endDate'], style=styleRow)

                rowsCount += 1

        outDir = params.get('outDir', QtGui.qApp.getHomeDir())
        fileName = os.path.join(forceStringEx(outDir), u"%s %s.xls" % (self.title(), unicode(
            QDate.currentDate().toString('dd_MM_yyyy'))))
        workbook.save(fileName)

        cursor.insertBlock()
        cursor.insertText(u'Сформировано %s строк' % rowsCount)
        cursor.insertBlock()
        cursor.insertText(u'Путь к файлу %s' % fileName)

        return doc