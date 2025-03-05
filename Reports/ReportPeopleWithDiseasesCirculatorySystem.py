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

from library.Utils import *
from Orgs.Utils import *
from library.database import *

from library.Utils import *
from Reports.Report import CReport
from Reports.ReportBase import *
from Reports.Ui_PeopleOfCancerSetupDialog import Ui_PeopleOfCancerSetupDialog


def selectData(begDate, endDate, areaId, specialityId, invoice, personId, ageFrom, ageTo, eventTypeId):
    stmt = u"""
SELECT Organisation.infisCode, Organisation.fullName, Client.lastname,Client.firstname,Client.patrname, Client.birthDate, 
  ClientPolicy.number AS police, 
  Client.SNILS, Diagnosis.MKB, rbSpeciality.name AS speciality_name,
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
  ClientPolicy.number AS police, 
  Client.SNILS, Diagnosis.MKB, rbSpeciality.name AS speciality_name, 
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
    tableAction = db.table('Action')
    tableActionType = db.table('ActionType')
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

        cursor.setCharFormat(CReportBase.ReportTitle)
        # cursor.insertText(self.title())
        # cursor.insertBlock()
        # self.dumpParams(cursor, params)
        # cursor.insertBlock()

        tableColumns = [
            ('5%', [u'№ п/п'], CReportBase.AlignCenter),
            ('10%', [u'Код юр. лица медицинской организации'], CReportBase.AlignCenter),
            ('10%', [u'Наименование медицинской организации'], CReportBase.AlignCenter),
            ('10%', [u'Фамилия'], CReportBase.AlignCenter),
            ('10%', [u'Имя'], CReportBase.AlignCenter),
            ('10%', [u'Отчество'], CReportBase.AlignCenter),
            ('10%', [u'Дата рождения'], CReportBase.AlignCenter),
            ('10%', [u'ЕНП'], CReportBase.AlignCenter),
            ('10%', [u'СНИЛС'], CReportBase.AlignCenter),
            ('10%', [u'МКБ'], CReportBase.AlignCenter),
            ('10%', [u'Состоит под диспансерным наблюдением по специальности врача'], CReportBase.AlignCenter),
            ('10%', [u'Условие оказания помощи'], CReportBase.AlignCenter),
            ('10%', [u'Оказанная услуга'], CReportBase.AlignCenter),
            ('10%', [u'Дата начала оказания услуги'], CReportBase.AlignCenter),
            ('10%', [u'Дата окончания оказания услуги'], CReportBase.AlignCenter),
        ]

        table = createTable(cursor, tableColumns)

        query = selectData(begDate, endDate, areaId, specialityId, invoice, personId, ageFrom, ageTo, eventTypeId)
        counter = 1
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

        for each_client in sorted(dict_with_data, key=lambda x: dict_with_data[x][0]["lastname"]):
            # counter_line = 1
            for each_act in dict_with_data[each_client]:
                i = table.addRow()
                # if counter_line:
                table.setText(i, 0, counter)
                    # counter_line = 0
                table.setText(i, 1, each_act['infisCode'])
                table.setText(i, 2, each_act['fullName'])
                table.setText(i, 3, each_act['lastname'])
                table.setText(i, 4, each_act['firstname'])
                table.setText(i, 5, each_act['patrname'])
                table.setText(i, 6, each_act['birthDate'])
                table.setText(i, 7, each_act['police'])
                table.setText(i, 8, each_act['SNILS'][:3] + '-' + each_act['SNILS'][3:6] + '-' + each_act['SNILS'][6:9]
                              + ' ' + each_act['SNILS'][9:])
                table.setText(i, 9, each_act['MKB'])
                table.setText(i, 10, each_act['speciality_name'])
                table.setText(i, 11, each_act['conition_names'])
                table.setText(i, 12, each_act['name_service'])
                table.setText(i, 13, each_act['begDate'])
                table.setText(i, 14, each_act['endDate'])
            # table.mergeCells(i - len(dict_with_data[each_client]) + 1, 0, len(dict_with_data[each_client]), 1)
            counter += 1

        # for row, rowDescr in enumerate(MainRows):
        #     reportLine = reportMainData[row]
        #     i = table.addRow()
        #     table.setText(i, 0, rowDescr[0])
        #     table.setText(i, 1, rowDescr[1])
        #     table.setText(i, 2, rowDescr[2])
        #     table.setText(i, 3, reportLine[0])
        #     table.setText(i, 4, reportLine[1])
        #     table.setText(i, 5, reportLine[2])
        #     table.setText(i, 6, reportLine[3])

        return doc


class CPeopleOfCancerSetupDialog(QtGui.QDialog, Ui_PeopleOfCancerSetupDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.edtBegDate.canBeEmpty()
        self.cmbOrgStructure.setOrgId(QtGui.qApp.currentOrgId())
        self.cmbOrgStructure.setValue(QtGui.qApp.currentOrgStructureId())
        self.cmbSpeciality.setTable('rbSpeciality', addNone=True)
        self.cmbdn.setTable('rbDispanser', addNone=True)
        if QtGui.qApp.userSpecialityId:
            self.cmbPerson.setValue(QtGui.qApp.userId)
            self.cmbSpeciality.setValue(QtGui.qApp.userSpecialityId)

    def setTitle(self, title):
        self.setWindowTitle(title)

    def setParams(self, params):
        self.edtBegDate.setDate(params.get('begDate', QDate()))
        self.edtEndDate.setDate(params.get('endDate', QDate.currentDate()))
        self.cmbOrgStructure.setValue(params.get('areaId', None))
        self.cmbSpeciality.setValue(params.get('specialityId', None))
        self.cmbPerson.setValue(params.get('personId', None))
        invoice = bool(params.get('invoice', True))
        self.chkInvoice.setChecked(invoice)
        self.edtAgeFrom.setValue(params.get('ageFrom', 0))
        self.edtAgeTo.setValue(params.get('ageTo', 150))
        self.cmbdn.setValue(params.get('eventTypeId', None))

    def params(self):
        result = {}
        result['begDate'] = self.edtBegDate.date()
        result['endDate'] = self.edtEndDate.date()
        result['areaId'] = self.cmbOrgStructure.value()
        result['specialityId'] = self.cmbSpeciality.value()
        result['personId'] = self.cmbPerson.value()
        result['invoice'] = self.chkInvoice.isChecked()
        result['ageFrom'] = self.edtAgeFrom.value()
        result['ageTo'] = self.edtAgeTo.value()
        result['eventTypeId'] = self.cmbdn.value()
        return result
