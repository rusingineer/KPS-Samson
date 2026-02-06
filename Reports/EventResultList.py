# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2021 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QDate

from library.Utils      import forceDateTime, forceInt, forceRef, forceString, trim
from Orgs.Utils         import getOrgStructureDescendants, getOrgStructures
from Reports.Report     import CReport
from Reports.ReportBase import CReportBase, createTable
from Reports.EventResultSurvey import CEventResultSetupDialog, STRICT_ADDRESS, NONRESIDENT_ADDRESS #, FOREIGN_ADDRESS


def selectData(params):
    begDate                 = params.get('begDate', QDate())
    endDate                 = params.get('endDate', QDate())
    eventPurposeId          = params.get('eventPurposeId', None)
    eventTypeList           = params.get('eventTypeList', [])
    orgStructureId          = params.get('orgStructureId', None)
    specialityList          = params.get('specialityList', [])
    personId                = params.get('personId', None)
    workOrgId               = params.get('workOrgId', None)
    sex                     = params.get('sex', 0)
    ageFrom                 = params.get('ageFrom', 0)
    ageTo                   = params.get('ageTo', 150)
    socStatusClassId        = params.get('socStatusClassId', None)
    socStatusTypeId         = params.get('socStatusTypeId', None)
    areaIdEnabled           = params.get('areaEnabled', False)
    chkOrgStructureArea     = params.get('chkOrgStructureArea', False)
    areaId                  = params.get('areaId', None)
    MKBFilter               = params.get('MKBFilter', 0)
    MKBFrom                 = params.get('MKBFrom', 'A00')
    MKBTo                   = params.get('MKBTo', 'Z99.9')
    MKBExFilter             = params.get('MKBExFilter', 0)
    MKBExFrom               = params.get('MKBExFrom', 'A00')
    MKBExTo                 = params.get('MKBExTo', 'Z99.9')
    chkPersonDetail         = params.get('chkPersonDetail', False)

    addressEnabled          = params.get('addressEnabled', False)
    addressType             = params.get('addressType', 0)
    clientAddressType       = params.get('clientAddressType', 0)
    clientAddressCityCode   = params.get('clientAddressCityCode', None)
    clientAddressCityCodeList = params.get('clientAddressCityCodeList', None)
    clientAddressStreetCode = params.get('clientAddressStreetCode', None)
    clientHouse             = params.get('clientHouse', '')
    clientCorpus            = params.get('clientCorpus', '')
    clientFlat              = params.get('clientFlat', '')

    order                   = params.get('order', 0)
    primary                 = params.get('primary', 0)
    resultId                = params.get('resultId', None)

    chkSocStatus            = params.get('chkSocStatus', False)
    chkPolicy               = params.get('chkPolicy', False)
    chkWork                 = params.get('chkWork', False)
#    chkAddionalAddress      = params.get('chkAddionalAddress', False)
    chkDocument             = params.get('chkDocument', False)

    db = QtGui.qApp.db

    tableClient = db.table('Client')
    tableEvent = db.table('Event')
    tableEventType = db.table('EventType')
    tableClientAddress = db.table('ClientAddress')
    tableAddress = db.table('Address')
    tableOrgStructureAddress = db.table('OrgStructure_Address')
    tableDiagnostic = db.table('Diagnostic')
    tableDiagnosis = db.table('Diagnosis')
    tableDiagnosisType = db.table('rbDiagnosisType')
    tablePerson = db.table('vrbPersonWithSpeciality')
    tableResult = db.table('rbResult')
    tableVisit = db.table('Visit')
    tableRBScene = db.table('rbScene')

    tableAddressHouseLoc = db.table('AddressHouse').alias('AddressHouseLoc')
    tableClientAddressForClientLoc = db.table('ClientAddress').alias('ClientAddressForClientLoc')
    tableAddressForClientLoc = db.table('Address').alias('AddressForClientLoc')

    tableAddressHouseReg = db.table('AddressHouse').alias('AddressHouseReg')
    tableClientAddressForClientReg = db.table('ClientAddress').alias('ClientAddressForClientReg')
    tableAddressForClientReg = db.table('Address').alias('AddressForClientReg')

    tableKLADRCodeReg = db.table('kladr.KLADR')
    tableKLADRStreetReg = db.table('kladr.STREET')
    tableKLADRCodeLoc = db.table('kladr.KLADR').alias('kladr_KLADRLoc')
    tableKLADRStreetLoc = db.table('kladr.STREET').alias('kladr_STREETLoc')

    tableClientContact = db.table('ClientContact')
    tableContactType = db.table('rbContactType')

    queryTable = tableEvent

    queryTable = queryTable.leftJoin(tableResult, tableResult['id'].eq(tableEvent['result_id']))
    queryTable = queryTable.leftJoin(tableClient, tableClient['id'].eq(tableEvent['client_id']))
    queryTable = queryTable.leftJoin(tableClientContact, tableClientContact['client_id'].eq(tableClient['id']))
    queryTable = queryTable.leftJoin(tableContactType, tableContactType['id'].eq(tableClientContact['contactType_id']))
    queryTable = queryTable.leftJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
    queryTable = queryTable.leftJoin(tableClientAddress, tableClientAddress['client_id'].eq(tableClient['id']))
    queryTable = queryTable.leftJoin(tableAddress, tableAddress['id'].eq(tableClientAddress['address_id']))
    queryTable = queryTable.leftJoin(tableVisit, db.joinAnd([tableVisit['event_id'].eq(tableEvent['id']), tableVisit['deleted'].eq(0)]))
    queryTable = queryTable.leftJoin(tableRBScene, tableRBScene['id'].eq(tableVisit['scene_id']))

    diagnosticJoinCond = '''Diagnostic.event_id = Event.id AND Diagnostic.id IN
                                (SELECT D1.id
                                    FROM Diagnostic AS D1
                                    LEFT JOIN rbDiagnosisType AS DT1 ON DT1.id = D1.diagnosisType_id
                                    WHERE D1.event_id = Event.id AND DT1.code =
                                        (SELECT MIN(DT2.code)
                                            FROM Diagnostic AS D2
                                            LEFT JOIN rbDiagnosisType AS DT2 ON DT2.id = D2.diagnosisType_id WHERE D2.event_id = Event.id
                                        )
                                 )'''
    queryTable = queryTable.leftJoin(tableDiagnostic, diagnosticJoinCond)
    queryTable = queryTable.leftJoin(tableDiagnosis, tableDiagnosis['id'].eq(tableDiagnostic['diagnosis_id']))
    queryTable = queryTable.leftJoin(tableDiagnosisType, tableDiagnosisType['id'].eq(tableDiagnosis['diagnosisType_id']))
    queryTable = queryTable.leftJoin(tablePerson, tablePerson['id'].eq(tableEvent['execPerson_id']))

    joinCondClientAddressForClientReg = 'ClientAddressForClientReg.client_id = Event.client_id AND ClientAddressForClientReg.id = (SELECT MAX(id) FROM ClientAddress AS CAReg WHERE CAReg.Type=0 and CAReg.client_id = Event.client_id)'
    queryTable = queryTable.leftJoin(tableClientAddressForClientReg, joinCondClientAddressForClientReg)
    queryTable = queryTable.leftJoin(tableAddressForClientReg, tableAddressForClientReg['id'].eq(tableClientAddressForClientReg['address_id']))
    queryTable = queryTable.leftJoin(tableAddressHouseReg, tableAddressHouseReg['id'].eq(tableAddressForClientReg['house_id']))

    queryTable = queryTable.leftJoin(tableKLADRCodeReg, tableKLADRCodeReg['CODE'].eq(tableAddressHouseReg['KLADRCode']))
    queryTable = queryTable.leftJoin(tableKLADRStreetReg, tableKLADRStreetReg['CODE'].eq(tableAddressHouseReg['KLADRStreetCode']))

    joinCondClientAddressForClientLoc = 'ClientAddressForClientLoc.client_id = Event.client_id AND ClientAddressForClientLoc.id = (SELECT MAX(id) FROM ClientAddress AS CALoc WHERE CALoc.Type=1 and CALoc.client_id = Event.client_id)'
    queryTable = queryTable.leftJoin(tableClientAddressForClientLoc, joinCondClientAddressForClientLoc)
    queryTable = queryTable.leftJoin(tableAddressForClientLoc, tableAddressForClientLoc['id'].eq(tableClientAddressForClientLoc['address_id']))
    queryTable = queryTable.leftJoin(tableAddressHouseLoc, tableAddressHouseLoc['id'].eq(tableAddressForClientLoc['house_id']))

    queryTable = queryTable.leftJoin(tableKLADRCodeLoc, tableKLADRCodeLoc['CODE'].eq(tableAddressHouseLoc['KLADRCode']))
    queryTable = queryTable.leftJoin(tableKLADRStreetLoc, tableKLADRStreetLoc['CODE'].eq(tableAddressHouseLoc['KLADRStreetCode']))

    cond = []
    cond.append(tableEvent['deleted'].eq(0))
    cond.append(tableEvent['execDate'].ge(begDate))
    cond.append(db.joinOr([tableEvent['execDate'].lt(endDate.addDays(1)), tableEvent['execDate'].isNull()]))
#    cond.append(tableClientContact['deleted'].eq(0))

    if eventTypeList:
        cond.append(tableEvent['eventType_id'].inlist(eventTypeList))
    elif eventPurposeId:
        cond.append(db.table('EventType')['purpose_id'].eq(eventPurposeId))
    if MKBFilter == 1:
        cond.append(tableDiagnosis['MKB'].ge(MKBFrom))
        cond.append(tableDiagnosis['MKB'].le(MKBTo))
    if MKBExFilter == 1:
        cond.append(tableDiagnosis['MKBEx'].ge(MKBExFrom))
        cond.append(tableDiagnosis['MKBEx'].le(MKBExTo))
    if personId:
        cond.append(tableDiagnostic['person_id'].eq(personId))
    elif orgStructureId:
        cond.append(tablePerson['orgStructure_id'].inlist(getOrgStructureDescendants(orgStructureId)))
    else:
        cond.append(tablePerson['org_id'].eq(QtGui.qApp.currentOrgId()))
    if specialityList:
        cond.append(tablePerson['speciality_id'].inlist(specialityList))
    if workOrgId:
        cond.append('EXISTS (SELECT * FROM ClientWork WHERE ClientWork.id = (SELECT MAX(id) FROM ClientWork AS CW WHERE CW.client_id = Client.id) and ClientWork.org_id=%d)' % (workOrgId))
    if sex:
        cond.append(tableClient['sex'].eq(sex))
    if ageFrom <= ageTo:
        date = str(QDate.currentDate().toString(Qt.ISODate))
        cond.append('IF(Diagnosis.endDate IS NOT NULL, Diagnosis.endDate, DATE(\'%s\')) >= ADDDATE(Client.birthDate, INTERVAL %d YEAR)'%(date, ageFrom))
        cond.append('IF(Diagnosis.endDate IS NOT NULL, Diagnosis.endDate, DATE(\'%s\')) <  SUBDATE(ADDDATE(Client.birthDate, INTERVAL %d YEAR),1)'%(date, ageTo+1))
    if socStatusTypeId or socStatusClassId or chkSocStatus:
        tableClientSocStatus = db.table('ClientSocStatus')
        if begDate:
            cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['endDate'].isNotNull(),
                                               tableClientSocStatus['endDate'].ge(begDate)
                                              ]),
                                   tableClientSocStatus['endDate'].isNull()
                                  ]))
        if endDate:
            cond.append(db.joinOr([db.joinAnd([tableClientSocStatus['begDate'].isNotNull(),
                                               tableClientSocStatus['begDate'].lt(endDate.addDays(1))
                                              ]),
                                   tableClientSocStatus['begDate'].isNull()
                                  ]))
        queryTable = queryTable.leftJoin(tableClientSocStatus,
                                         db.joinAnd([tableClientSocStatus['client_id'].eq(tableClient['id']), tableClientSocStatus['deleted'].eq(0)]) if chkSocStatus else tableClientSocStatus['client_id'].eq(tableClient['id']))
        if socStatusClassId:
            cond.append(tableClientSocStatus['socStatusClass_id'].eq(socStatusClassId))
        if socStatusTypeId:
            cond.append(tableClientSocStatus['socStatusType_id'].eq(socStatusTypeId))
        if not chkSocStatus:
            cond.append(tableClientSocStatus['deleted'].eq(0))
    if areaIdEnabled:
        if chkOrgStructureArea:
            if areaId:
                orgStructureIdList = getOrgStructureDescendants(areaId)
            else:
                orgStructureIdList = getOrgStructures(QtGui.qApp.currentOrgId())
            subCond = [ tableOrgStructureAddress['master_id'].inlist(orgStructureIdList),
                        tableOrgStructureAddress['house_id'].eq(tableAddress['house_id']),
                      ]
            cond.append(db.existsStmt(tableOrgStructureAddress, subCond))

    if addressEnabled:
        if addressType in (STRICT_ADDRESS, NONRESIDENT_ADDRESS):
            clientAddressType = clientAddressType if addressType == STRICT_ADDRESS else 0
            if clientAddressType == 0:
                tableAddressForClient = tableAddressForClientReg
                tableAddressHouse = tableAddressHouseReg
            else:
                tableAddressForClient = tableAddressForClientLoc
                tableAddressHouse = tableAddressHouseLoc
            if addressType == STRICT_ADDRESS:
                if clientFlat:
                    cond.append(tableAddressForClient['flat'].eq(clientFlat))
                if clientCorpus:
                    cond.append(tableAddressHouse['corpus'].eq(clientCorpus))
                if clientHouse:
                    cond.append(tableAddressHouse['number'].eq(clientHouse))
                if clientAddressCityCodeList:
                    cond.append(tableAddressHouse['KLADRCode'].inlist(clientAddressCityCodeList))
                else:
                    if clientAddressCityCode:
                        cond.append(tableAddressHouse['KLADRCode'].eq(clientAddressCityCode))
                if clientAddressStreetCode:
                    cond.append(tableAddressHouse['KLADRStreetCode'].eq(clientAddressStreetCode))
            else:
                props = QtGui.qApp.preferences.appPrefs
                kladrCodeList = [forceString(props.get('defaultKLADR', '')), forceString(props.get('provinceKLADR', ''))]
                cond.append(tableAddressHouse['KLADRCode'].notInlist(kladrCodeList))
        else:
            foreignDocumentTypeId = forceInt(db.translate('rbDocumentType', 'code', '9', 'id'))
            documentCond = 'EXISTS(SELECT ClientDocument.`id` FROM ClientDocument WHERE ClientDocument.`documentType_id`=%d AND ClientDocument.`client_id`=Client.`id`)'%foreignDocumentTypeId
            cond.append(documentCond)

    if order:
        cond.append(tableEvent['order'].eq(order))

    if primary:
        cond.append(tableEvent['isPrimary'].eq(primary))

    if resultId:
        cond.append(tableEvent['result_id'].eq(resultId))

    fields = ['CONCAT_WS(\' \', Client.`lastName`, Client.`firstName`, Client.`patrName`) AS fio',
              tableClient['sex'].name(),
              'IF(MONTH(Client.`birthDate`)>MONTH(CURRENT_DATE()) OR (MONTH(Client.`birthDate`) = MONTH(CURRENT_DATE()) AND DAYOFMONTH(Client.`birthDate`) > DAYOFMONTH(CURRENT_DATE())), YEAR(CURRENT_DATE())-YEAR(Client.`birthDate`)-1, YEAR(CURRENT_DATE())-YEAR(Client.`birthDate`)) AS clientAge',
              tableClient['id'].alias('clientId'),
              tableAddressForClientReg['flat'].alias('clientFlat') if not clientAddressType else tableAddressForClientLoc['flat'].alias('clientFlat'),
              tableAddressHouseReg['corpus'].alias('clientCorpus') if not clientAddressType else tableAddressHouseLoc['corpus'].alias('clientCorpus'),
              tableAddressHouseReg['number'].alias('clientNumber') if not clientAddressType else tableAddressHouseLoc['number'].alias('clientNumber'),
              tableKLADRCodeReg['NAME'].alias('kladrName') if not clientAddressType else tableKLADRCodeLoc['NAME'].alias('kladrName'),
              tableKLADRCodeReg['SOCR'].alias('kladrSocr') if not clientAddressType else tableKLADRCodeLoc['SOCR'].alias('kladrSocr'),
              tableKLADRStreetReg['NAME'].alias('kaldrStreetName') if not clientAddressType else tableKLADRStreetLoc['NAME'].alias('kaldrStreetName'),
              tableKLADRStreetReg['SOCR'].alias('kladrStreetSocr') if not clientAddressType else tableKLADRStreetLoc['SOCR'].alias('kladrStreetSocr'),
              tableClientContact['contact'].alias('clientContact'),
              tableContactType['name'].alias('contactTypeName'),
              tableDiagnosis['MKB'].name(),
              tableEventType['code'].alias('eventTypeCode'),
              tableEventType['name'].alias('eventTypeName'),
              tableEvent['setDate'].alias('eventSetDate'),
              tableEvent['execDate'].alias('eventExecDate'),
              tableEvent['id'].alias('eventId'),
              tableClientContact['id'].alias('clientContactId'),
              tableClientContact['deleted'].alias('contactDeleted'),
              tableVisit['id'].alias('visitId'),
              tableVisit['date'].alias('visitDate'),
              tableRBScene['name'].alias('sceneName'),
              tableEvent['execPerson_id'],
              tablePerson['name'].alias('personName')
              ]
    if chkPolicy:
        fields.append('getClientPolicy(Client.id,0) AS policyOMS')
        fields.append('getClientPolicy(Client.id,1) AS policyDMS')
    if chkDocument:
        fields.append('getClientDocument(Client.id) AS document')
    if chkSocStatus:
        fields.append('(SELECT SST.name FROM rbSocStatusType AS SST WHERE SST.id = ClientSocStatus.socStatusType_id) AS nameSocStatusType')
        fields.append('(SELECT SSC.name FROM rbSocStatusClass AS SSC WHERE SSC.id = ClientSocStatus.socStatusClass_id) AS nameSocStatusClass')
    if chkWork:
        fields.append('getClientWork(Client.id) AS work')

    stmt = db.selectStmt(queryTable, fields, cond, 'vrbPersonWithSpeciality.name, fio' if chkPersonDetail else 'fio')
    return db.query(stmt)


class CReportEventResultList(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Список пациентов')
        self._data = {}
        self.clientIdList = []

    def structData(self, query, chkSocStatus, chkPolicy, chkWork, chkAddionalAddress, chkDocument, chkPersonDetail):
        self.resetHelpers()
        eventIdList = []
        clientContactIdList = []
        while query.next():
            record = query.record()
            clientId = forceRef(record.value('clientId'))
            if chkPersonDetail:
                personId = forceRef(record.value('execPerson_id'))
                personName = forceString(record.value('personName'))
                clientDataDict = self._data.get((personName, personId), {})
                clientData = clientDataDict.get(clientId, None)
            else:
                clientData = self._data.get(clientId, None)
            if clientData is None:
                self.clientIdList.append(clientId)
                fio = forceString(record.value('fio'))
                clientAge = forceInt(record.value('clientAge'))
                clientSex = forceInt(record.value('sex'))
                if clientSex == 1:
                    clientSex = u'М'
                elif clientSex == 2:
                    clientSex = u'Ж'
                else:
                    clientSex = ''
                clientFlat = forceString(record.value('clientFlat'))
                clientFlat = u'кв.'+clientFlat if clientFlat else ''
                clientCorpus = forceString(record.value('clientCorpus'))
                clientCorpus = u'крп.'+clientCorpus if clientCorpus else ''
                clientNumber = forceString(record.value('clientNumber'))
                clientNumber = u'д. '+clientNumber if clientNumber else ''
                kladrName = forceString(record.value('kladrName'))
                kladrSocr = forceString(record.value('kladrSocr'))
                kaldrStreetName = forceString(record.value('kaldrStreetName'))
                kladrStreetSocr = forceString(record.value('kladrStreetSocr'))
                clientAddress = u', '.join([trim(val) for val in (kladrName+' '+kladrSocr,
                                                        kaldrStreetName+' '+kladrStreetSocr,
                                                        clientNumber, clientCorpus, clientFlat) if trim(val)])
                clientData = {'fio':fio,
                              'clientAge':clientAge,
                              'clientSex': clientSex,
                              'clientAddress': clientAddress,
                              'contactList': [],
                              'eventList': {}}
                if chkPolicy:
                    clientData['policyOMS'] = forceString(record.value('policyOMS'))
                    clientData['policyDMS'] = forceString(record.value('policyDMS'))
                if chkDocument:
                    clientData['document'] = forceString(record.value('document'))
                if chkSocStatus:
                    clientData['nameSocStatusType'] = forceString(record.value('nameSocStatusType'))
                    clientData['nameSocStatusClass'] = forceString(record.value('nameSocStatusClass'))
                if chkWork:
                    clientData['work'] = forceString(record.value('work'))
                if chkPersonDetail:
                    clientDataDict[clientId] = clientData
                    self._data[(personName, personId)] = clientDataDict
                else:
                    clientData['personName'] = forceString(record.value('personName'))
                    self._data[clientId] = clientData
            eventId = forceRef(record.value('eventId'))
            if eventId not in eventIdList:
                eventIdList.append(eventId)
                eventTypeCode = forceString(record.value('eventTypeCode'))
                eventTypeName = forceString(record.value('eventTypeName'))
                eventSetDate = forceString(record.value('eventSetDate'))
                eventExecDate = forceString(record.value('eventExecDate'))
                MKB = forceString(record.value('MKB'))
                eventDict = clientData.get('eventList', {})
                eventDict[eventId] = {'MKB':MKB, 'eventType': eventTypeCode+' | '+eventTypeName,
                                      'eventSetDate':eventSetDate, 'eventExecDate':eventExecDate}
                clientData['eventList'] = eventDict
            clientContactId = forceRef(record.value('clientContactId'))
            contactDeleted  = forceInt(record.value('contactDeleted'))
            if (clientContactId not in clientContactIdList) and contactDeleted == 0:
                clientContactIdList.append(clientContactId)
                clientContact = forceString(record.value('clientContact'))
                contactTypeName = forceString(record.value('contactTypeName'))
                clientData['contactList'].append(u': '.join((val for val in (contactTypeName, clientContact) if trim(val))))
            visitId   = forceRef(record.value('visitId'))
            eventDict = clientData.get('eventList', {})
            eventListLine = eventDict.get(eventId, {})
            visitDict = eventListLine.get('visitList', {})
            if visitId and visitId not in visitDict.keys():
                visitDate = forceDateTime(record.value('visitDate'))
                sceneName = forceString(record.value('sceneName'))
                visitDict[visitId] = (visitDate, sceneName)
            eventListLine['visitList'] = visitDict
            eventDict[eventId] = eventListLine
            clientData['eventList'] = eventDict


    def getSetupDialog(self, parent):
        result = CEventResultSetupDialog(parent)
        result.setVisibleResult(True)
        result.setVisiblePrimary(True)
        result.setVisibleOrder(True)
        result.setSocStatusTypeVisible(True)
        result.setAdditionalGraphsVisible(True)
        result.setTitle(self.title())
        return result


    def resetHelpers(self):
        self._data.clear()
        self.clientIdList = []


    def build(self, params):
        query = selectData(params)
        chkSocStatus       = params.get('chkSocStatus', False)
        chkPolicy          = params.get('chkPolicy', False)
        chkWork            = params.get('chkWork', False)
        chkAddionalAddress = params.get('chkAddionalAddress', False)
        chkDocument        = params.get('chkDocument', False)
        chkPersonDetail    = params.get('chkPersonDetail', False)
        self.structData(query, chkSocStatus, chkPolicy, chkWork, chkAddionalAddress, chkDocument, chkPersonDetail)

        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()

        tableColumns = [
            ('2%',  [u'№' ],                      CReportBase.AlignRight),
            ('12%', [u'ФИО'],                     CReportBase.AlignLeft),
            ('2%',  [u'Пол'],                     CReportBase.AlignLeft),
            ('4%',  [u'Возраст'],                 CReportBase.AlignRight),
            ('5%',  [u'Идентификатор пациента'],  CReportBase.AlignLeft),
            ('5%',  [u'Контакты'],                CReportBase.AlignLeft),
            ('2%',  [u'Номер обращения'],         CReportBase.AlignRight),
            ('5%',  [u'Закл. диагноз'],           CReportBase.AlignLeft),
            ('10%', [u'Событие'],                 CReportBase.AlignLeft),
            ('5%',  [u'Место визита'],            CReportBase.AlignLeft),
            ('7%',  [u'Дата визита'],             CReportBase.AlignLeft),
            ('3%',  [u'Количество визитов'],      CReportBase.AlignRight),
            ('9%',  [u'Дата начала'],             CReportBase.AlignLeft),
            ('9%',  [u'Дата окончания'],          CReportBase.AlignLeft),
            ]
        addionalCol = 5
        if chkAddionalAddress:
            tableColumns.insert(addionalCol, ('10%', [u'Адрес'], CReportBase.AlignLeft))
            addionalCol += 1
        if chkDocument:
            tableColumns.insert(addionalCol, ('10%', [u'Документ'], CReportBase.AlignLeft))
            addionalCol += 1
        if chkPolicy:
            tableColumns.insert(addionalCol, ('10%', [u'Полис'], CReportBase.AlignLeft))
            addionalCol += 1
        if chkWork:
            tableColumns.insert(addionalCol, ('10%', [u'Занятость'], CReportBase.AlignLeft))
            addionalCol += 1
        if chkSocStatus:
            tableColumns.insert(addionalCol, ('10%', [u'Соц.статус'], CReportBase.AlignLeft))
            addionalCol += 1
        if chkPersonDetail:
            table = createTable(cursor, tableColumns)
            personKeys = self._data.keys()
            personKeys.sort(key=lambda x: x[0])
            for personKey in personKeys:
                clientDataDict = self._data.get(personKey, {})
                i = table.addRow()
                table.setText(i, 0, personKey[0], charFormat=CReportBase.ReportSubTitle, blockFormat=CReportBase.AlignCenter)
                table.mergeCells(i, 0, 1, len(tableColumns))
                globalEventCount = 0
                clientKeys = clientDataDict.keys()
                for idx, clientId in enumerate(clientKeys):
                    clientData = clientDataDict.get(clientId, None)
                    i = table.addRow()
                    table.setText(i, 0, idx+1)
                    table.setText(i, 1, clientData['fio'])
                    table.setText(i, 2, clientData['clientSex'])
                    table.setText(i, 3, clientData['clientAge'])
                    table.setText(i, 4, clientId)
                    addionalCol = 5
                    if chkAddionalAddress:
                        table.setText(i, addionalCol, clientData['clientAddress'])
                        addionalCol += 1
                    if chkDocument:
                        table.setText(i, addionalCol, clientData['document'])
                        addionalCol += 1
                    if chkPolicy:
                        policyOMS = clientData['policyOMS']
                        policyDMS = clientData['policyDMS']
                        policy = ((u'ОМС: %s\n'%policyOMS) if policyOMS else u'') + ((u'ДМС: %s'%policyDMS) if policyDMS else u'')
                        table.setText(i, addionalCol, policy)
                        addionalCol += 1
                    if chkWork:
                        table.setText(i, addionalCol, clientData['work'])
                        addionalCol += 1
                    if chkSocStatus:
                        socStatusClass = clientData['nameSocStatusClass']
                        socStatusType  = clientData['nameSocStatusType']
                        socStatus = ((u'класс: %s\n'%socStatusClass) if socStatusClass else u'') + ((u'тип: %s'%socStatusType) if socStatusType else u'')
                        table.setText(i, addionalCol, socStatus)
                        addionalCol += 1
                    contact = []
                    contactList = clientData.get('contactList', [])
                    for val in contactList:
                        contact.append(val)
                    table.setText(i, addionalCol, u';\n'.join(contact))
                    addionalCol += 1
                    eventDict = clientData.get('eventList', {})
                    eventListLen = len(eventDict.keys())
                    eventListCnt = 1
                    evRow = i
                    for eventKey, eventListLine in eventDict.items():
                        addionalColNew = addionalCol
                        eventMKB = eventListLine['MKB']
                        eventType = eventListLine['eventType']
                        eventSetDate = eventListLine['eventSetDate']
                        eventExecDate = eventListLine['eventExecDate']
                        globalEventCount += 1
                        eventNumbers = unicode(globalEventCount)
                        visitDict = eventListLine.get('visitList', {})
                        visitLine = visitDict.values()
                        visitLine.sort()
                        visitDates = []
                        visitNames = []
                        for visitDate, sceneName in visitLine:
                            visitDates.append(unicode(visitDate.toString(u'dd.MM.yyyy HH:mm:ss')))
                            visitNames.append(sceneName)
                        table.setText(i, addionalColNew, eventNumbers)
                        addionalColNew += 1
                        table.setText(i, addionalColNew, eventMKB)
                        addionalColNew += 1
                        table.setText(i, addionalColNew, eventType)
                        addionalColNew += 1
                        table.setText(i, addionalColNew, u'\n'.join(visitNames))
                        addionalColNew += 1
                        table.setText(i, addionalColNew, u'\n'.join(visitDates))
                        addionalColNew += 1
                        table.setText(i, addionalColNew, len(visitLine))
                        addionalColNew += 1
                        table.setText(i, addionalColNew, eventSetDate)
                        addionalColNew += 1
                        table.setText(i, addionalColNew, eventExecDate)
                        if eventListLen > eventListCnt:
                            i = table.addRow()
                            eventListCnt += 1
                    for evCol in xrange(0, addionalCol):
                        table.mergeCells(evRow, evCol, i-evRow+1, 1)

        else:
            globalEventCount = 0
            tableColumns.insert(addionalCol, ('12%', [u'Врач'], CReportBase.AlignLeft))
            table = createTable(cursor, tableColumns)
            for idx, clientId in enumerate(self.clientIdList):
                clientData = self._data[clientId]
                i = table.addRow()
                table.setText(i, 0, idx+1)
                table.setText(i, 1, clientData['fio'])
                table.setText(i, 2, clientData['clientSex'])
                table.setText(i, 3, clientData['clientAge'])
                table.setText(i, 4, clientId)
                addionalCol = 5
                if chkAddionalAddress:
                    table.setText(i, addionalCol, clientData['clientAddress'])
                    addionalCol += 1
                if chkDocument:
                    table.setText(i, addionalCol, clientData['document'])
                    addionalCol += 1
                if chkPolicy:
                    policyOMS = clientData['policyOMS']
                    policyDMS = clientData['policyDMS']
                    policy = ((u'ОМС: %s\n'%policyOMS) if policyOMS else u'') + ((u'ДМС: %s'%policyDMS) if policyDMS else u'')
                    table.setText(i, addionalCol, policy)
                    addionalCol += 1
                if chkWork:
                    table.setText(i, addionalCol, clientData['work'])
                    addionalCol += 1
                if chkSocStatus:
                    socStatusClass = clientData['nameSocStatusClass']
                    socStatusType  = clientData['nameSocStatusType']
                    socStatus = ((u'класс: %s\n'%socStatusClass) if socStatusClass else u'') + ((u'тип: %s'%socStatusType) if socStatusType else u'')
                    table.setText(i, addionalCol, socStatus)
                    addionalCol += 1
                table.setText(i, addionalCol, clientData['personName'])
                addionalCol += 1
                contact = []
                contactList = clientData.get('contactList', [])
                for val in contactList:
                    contact.append(val)
                table.setText(i, addionalCol, u';\n'.join(contact))
                addionalCol += 1
                eventDict = clientData.get('eventList', {})
                eventListLen = len(eventDict.keys())
                eventListCnt = 1
                evRow = i
                for eventKey, eventListLine in eventDict.items():
                    addionalColNew = addionalCol
                    eventMKB = eventListLine['MKB']
                    eventType = eventListLine['eventType']
                    eventSetDate = eventListLine['eventSetDate']
                    eventExecDate = eventListLine['eventExecDate']
                    globalEventCount += 1
                    eventNumbers = unicode(globalEventCount)
                    visitDict = eventListLine.get('visitList', {})
                    visitLine = visitDict.values()
                    visitLine.sort()
                    visitDates = []
                    visitNames = []
                    for visitDate, sceneName in visitLine:
                        visitDates.append(unicode(visitDate.toString(u'dd.MM.yyyy HH:mm:ss')))
                        visitNames.append(sceneName)
                    table.setText(i, addionalColNew, eventNumbers)
                    addionalColNew += 1
                    table.setText(i, addionalColNew, eventMKB)
                    addionalColNew += 1
                    table.setText(i, addionalColNew, eventType)
                    addionalColNew += 1
                    table.setText(i, addionalColNew, u'\n'.join(visitNames))
                    addionalColNew += 1
                    table.setText(i, addionalColNew, u'\n'.join(visitDates))
                    addionalColNew += 1
                    table.setText(i, addionalColNew, len(visitLine))
                    addionalColNew += 1
                    table.setText(i, addionalColNew, eventSetDate)
                    addionalColNew += 1
                    table.setText(i, addionalColNew, eventExecDate)
                    if eventListLen > eventListCnt:
                        i = table.addRow()
                        eventListCnt += 1
                for evCol in xrange(0, addionalCol):
                    table.mergeCells(evRow, evCol, i-evRow+1, 1)
        return doc

