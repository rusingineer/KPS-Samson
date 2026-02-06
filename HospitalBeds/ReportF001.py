# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2023 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################


from PyQt4                          import QtGui
from PyQt4.QtCore                   import QDateTime
from library.ICDUtils import getMKBName
from library.Utils                  import (forceRef,
                                            forceInt,
                                            forceString,
                                            forceDate,
                                            forceTime,
                                            forceDateTime,
                                            getPref,
                                            setPref,
                                            getAgeRangeCond,
                                            formatDate,
                                            formatTime,
                                            formatName,
                                            formatSex,
                                            calcAge,
                                            getMKB)
from Events.Utils                   import getActionTypeIdListByFlatCode
from Reports.Utils                  import getStringPropertyValue
from Registry.Utils                 import getClientInfoEx, getClientPhonesEx
from Orgs.Utils         import getPersonInfo
from Reports.ReportBase             import CReportBase, createTable
from HospitalBeds.HospitalBedsModel import CReportF001SetupDialog
from Reports.ReportView             import CReportViewDialog


def queryProperty(clientId,
                  records,
                  flatCode,
                  colsVal=u'',
                  condVal=u'',
                  flag=None,
                  actionIdLeaved=None,
                  condOrgStructure=None):
    db = QtGui.qApp.db
    tableAPT = db.table('ActionPropertyType')
    tableAP = db.table('ActionProperty')
    tableActionType = db.table('ActionType')
    tableAction = db.table('Action')
    tableEvent = db.table('Event')
    tableClient = db.table('Client')
    tableAPS = db.table('ActionProperty_String')
    tableAPO = db.table('ActionProperty_Organisation')
    tableOrg = db.table('Organisation')
    tableAPOS = db.table('ActionProperty_OrgStructure')
    tableOS = db.table('OrgStructure')

    colsClientId = []
    condClientId = [
        tableAction['actionType_id'].inlist(getActionTypeIdListByFlatCode(flatCode)),
        tableAction['deleted'].eq(0),
        tableEvent['deleted'].eq(0),
        tableAP['deleted'].eq(0),
        tableAPT['deleted'].eq(0),
        tableClient['deleted'].eq(0),
        tableAP['action_id'].eq(tableAction['id']),
    ]
    condClientId.append(tableAction['event_id'].eq(forceRef(records.value('eventId'))))
    condClientId.append(tableEvent['client_id'].eq(clientId))
    if flag != 3:
        if actionIdLeaved is not None:
            condClientId.append(tableAction['id'].eq(actionIdLeaved))
        else:
            condClientId.append(tableAction['id'].eq(forceRef(records.value('id'))))
        condClientId.append(tableAPT['name'].like(condVal))
    queryTableClientId = tableAction.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
    queryTableClientId = queryTableClientId.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
    queryTableClientId = queryTableClientId.leftJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
    queryTableClientId = queryTableClientId.innerJoin(tableAPT, tableAPT['actionType_id'].eq(tableActionType['id']))
    queryTableClientId = queryTableClientId.innerJoin(tableAP, tableAP['type_id'].eq(tableAPT['id']))
    if flag == 0:
        queryTableClientId = queryTableClientId.innerJoin(tableAPO, tableAPO['id'].eq(tableAP['id']))
        queryTableClientId = queryTableClientId.innerJoin(tableOrg, tableOrg['id'].eq(tableAPO['value']))
        colsClientId.append(tableOrg['shortName'].alias(colsVal))
        condClientId.append(tableOrg['deleted'].eq(0))
    elif flag == 1:
        queryTableClientId = queryTableClientId.innerJoin(tableAPOS, tableAPOS['id'].eq(tableAP['id']))
        queryTableClientId = queryTableClientId.innerJoin(tableOS, tableOS['id'].eq(tableAPOS['value']))
        colsClientId.append(tableOS['code'].alias(colsVal) if condOrgStructure else tableOS['name'].alias(colsVal))
    elif flag == 3:
          colsClientId.append(tableAction['id'].alias('actionIdLeaved'))
          colsClientId.append(tableAction['begDate'].alias('begDateLeaved'))
          colsClientId.append(tableAction['note'].alias('noteLeaved'))
    else:
        queryTableClientId = queryTableClientId.innerJoin(tableAPS, tableAPS['id'].eq(tableAP['id']))
        colsClientId.append(tableAPS['value'].alias(colsVal))
    stmt = db.selectDistinctStmt(queryTableClientId, colsClientId, condClientId, u'')
    return db.query(stmt)


def execStationaryReportF001_2(hospitalBedsDialog):
    orgStructureId = hospitalBedsDialog.treeOrgStructure.currentIndex()
    begDate = hospitalBedsDialog.edtFilterBegDate.date()
    endDate = hospitalBedsDialog.edtFilterEndDate.date()
    sexIndex = hospitalBedsDialog.cmbSex.currentIndex()
    ageFor = hospitalBedsDialog.spbAgeFor.value()
    ageTo = hospitalBedsDialog.spbAgeTo.value()
    begTime = hospitalBedsDialog.edtFilterBegTime.time()
    endTime = hospitalBedsDialog.edtFilterEndTime.time()
    begDateTime = QDateTime(begDate, begTime)
    endDateTime = QDateTime(endDate, endTime)

    params = QtGui.qApp.preferences.reportPrefs.get(u'stationaryreportf001_2', {})
    setupDialog = CReportF001SetupDialog(hospitalBedsDialog)
    setupDialog.setParams(params)
    if not setupDialog.exec_():
        return
    params = setupDialog.params()
    QtGui.qApp.preferences.reportPrefs[u'stationaryreportf001_2'] = params
    condSort = getPref(params, 'condSort', 0)
    condOrgStructure = getPref(params, 'condOrgStructure', 0)

    doc = QtGui.QTextDocument()
    cursor = QtGui.QTextCursor(doc)
    cursor.setCharFormat(CReportBase.ReportTitle)
    cursor.insertText(u'Информация о поступивших в стационар и исходы госпитализации вакцинированных от COVID-19')
    cursor.insertBlock()
    cols = [
        ('2%', [u'№', u'', u'1'], CReportBase.AlignRight),
        ('5%', [u'Поступление', u'дата', u'2'], CReportBase.AlignLeft),
        ('5%', [u'', u'час', u'3'], CReportBase.AlignLeft),
        ('5%', [u'Фамилия, И., О.', u'', u'4'], CReportBase.AlignLeft),
        ('5%', [u'Дата рождения', u'', u'5'], CReportBase.AlignLeft),
        ('8%', [u'Постоянное место жительства или адрес родственников, близких и № телефона', u'', u'6'], CReportBase.AlignLeft),
        ('5%', [u'Каким учреждением был направлен или доставлен', u'', u'7'], CReportBase.AlignLeft),
        ('5%', [u'Отделение, в которое помещен больной', u'', u'8'], CReportBase.AlignLeft),
        ('5%', [u'№ карты стационарного больного', u'', u'9'], CReportBase.AlignLeft),
        ('5%', [u'Диагноз направившего учреждения', u'', u'10'], CReportBase.AlignLeft),
        ('5%', [u'Эпид.', u'', u'11'], CReportBase.AlignLeft),
        ('5%', [u'Дата и время выбытия', u'дата', u'12'], CReportBase.AlignLeft),
        ('5%', [u'', u'час', u'13'], CReportBase.AlignLeft),
        ('5%', [u'Выписан, переведен в другой стационар, умер', u'', u'14'], CReportBase.AlignLeft),
        ('5%', [u'Диагноз при выписке', u'', u'15'], CReportBase.AlignLeft),
        ('5%', [u'Отметка о сообщении родственникам или учреждению', u'', u'16'], CReportBase.AlignLeft),
        ('5%', [u'Если не был госпитализирован', u'причина и принятые меры', u'', u'17'], CReportBase.AlignLeft),
        ('5%', [u'', u'отказ в приеме первичный, повторный', u'', u'18'], CReportBase.AlignLeft),
        ('5%', [u'Данные о вакцинации от COVID19', u'Вакцина', u'19'], CReportBase.AlignLeft),
        ('5%', [u'', u'Этап', u'20'], CReportBase.AlignLeft),
        ('5%', [u'', u'Дата', u'21'], CReportBase.AlignLeft),
        ('5%', [u'Примечание', u'22'], CReportBase.AlignLeft),
    ]
    table = createTable(cursor, cols)
    table.mergeCells(0,0, 2,1)
    table.mergeCells(0,1, 1,2)
    table.mergeCells(0,3, 2,1)
    table.mergeCells(0,4, 2,1)
    table.mergeCells(0,5, 2,1)
    table.mergeCells(0,6, 2,1)
    table.mergeCells(0,7, 2,1)
    table.mergeCells(0,8, 2,1)
    table.mergeCells(0,9, 2,1)
    table.mergeCells(0,10, 2,1)
    table.mergeCells(0,11, 1,2)
    table.mergeCells(0,12, 2,1)
    table.mergeCells(0,13, 2,1)
    table.mergeCells(0,14, 2,1)
    table.mergeCells(0,15, 2,1)
    table.mergeCells(0,16, 1,2)
    table.mergeCells(0,18, 1,3)
    table.mergeCells(0,21, 2,1)

    cnt = 0
    db = QtGui.qApp.db
    tableAPT = db.table('ActionPropertyType')
    tableAP = db.table('ActionProperty')
    tableActionType = db.table('ActionType')
    tableAction = db.table('Action')
    tableEvent = db.table('Event')
    tableClient = db.table('Client')
    tableAPOS = db.table('ActionProperty_OrgStructure')
    tableOS = db.table('OrgStructure')
    tableDiagnosis = db.table('Diagnosis')
    tableMKB = db.table('MKB')
    tableDiagnostic = db.table('Diagnostic')
    tableRBDiagnosisType = db.table('rbDiagnosisType')
    cols = [
        tableAction['id'],
        tableEvent['id'].alias('eventId'),
        tableEvent['eventType_id'],
        tableEvent['client_id'],
        tableEvent['externalId'],
        tableClient['lastName'],
        tableClient['firstName'],
        tableClient['patrName'],
        tableClient['sex'],
        tableClient['birthDate'],
        tableAction['begDate'],
        tableAction['note'],
        tableAction['finance_id'],
        tableEvent['contract_id'],

        (u'(SELECT MAX(A.endDate)'
         u' FROM Action A JOIN ActionType AType ON A.actionType_id = AType.id'
         u' WHERE A.event_id = Event.id AND A.deleted = 0 AND AType.deleted = 0'
         u' AND AType.flatCode = "leaved"'
         u') AS endDate'),

        getStringPropertyValue(u'Вакцинация от COVID-19') + ' AS vaccine',

        ('(SELECT rbVaccine.name'
         ' FROM ClientVaccination CV'
         ' JOIN rbVaccine ON CV.vaccine_id = rbVaccine.id'
         ' JOIN rbVaccine_Identification rbVI ON rbVI.master_id = rbVaccine.id'
         ' JOIN rbAccountingSystem rbAS ON rbVI.system_id = rbAS.id'
         ' WHERE CV.client_id = Client.id AND CV.deleted = 0 AND rbVI.deleted = 0'
         ' AND rbVI.value = "covid" AND rbAS.urn = "urn:oid:PrivOtchet"'
         ' ORDER BY CV.id DESC LIMIT 1) AS vaccine2'),

        'IFNULL(%s, %s) AS vaccineStage' % (getStringPropertyValue(u'Этап'), getStringPropertyValue(u'Введение компонентов вакцины')),

        ('(SELECT CV.vaccinationType'
         ' FROM ClientVaccination CV'
         ' JOIN rbVaccine ON CV.vaccine_id = rbVaccine.id'
         ' JOIN rbVaccine_Identification rbVI ON rbVI.master_id = rbVaccine.id'
         ' JOIN rbAccountingSystem rbAS ON rbVI.system_id = rbAS.id'
         ' WHERE CV.client_id = Client.id AND CV.deleted = 0 AND rbVI.deleted = 0'
         ' AND rbVI.value = "covid" AND rbAS.urn = "urn:oid:PrivOtchet"'
         ' ORDER BY CV.id DESC LIMIT 1) AS vaccineStage2'),

        (u'(SELECT APS.value'
        u' FROM ActionPropertyType AS APT'
        u' INNER JOIN ActionProperty AS AP ON AP.type_id = APT.id'
        u' INNER JOIN ActionProperty_String AS APS ON APS.id = AP.id'
        u' WHERE Action.id IS NOT NULL AND APT.actionType_id = Action.actionType_id'
        u' AND AP.action_id = Action.id AND AP.deleted = 0'
        u' AND APT.deleted = 0 AND APT.name = "Дата вакцинации") AS vaccineDate'),

        ('(SELECT CV.`datetime`'
         ' FROM ClientVaccination CV'
         ' JOIN rbVaccine ON CV.vaccine_id = rbVaccine.id'
         ' JOIN rbVaccine_Identification rbVI ON rbVI.master_id = rbVaccine.id'
         ' JOIN rbAccountingSystem rbAS ON rbVI.system_id = rbAS.id'
         ' WHERE CV.client_id = Client.id AND CV.deleted = 0 AND rbVI.deleted = 0'
         ' AND rbVI.value = "covid" AND rbAS.urn = "urn:oid:PrivOtchet"'
         ' ORDER BY CV.id DESC LIMIT 1) AS vaccineDate2'),
    ]

    queryTable = tableAction.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
    queryTable = queryTable.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
    queryTable = queryTable.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
    queryTable = queryTable.innerJoin(tableAPT, tableAPT['actionType_id'].eq(tableActionType['id']))
    queryTable = queryTable.innerJoin(tableAP, tableAP['type_id'].eq(tableAPT['id']))
    cond = [
        tableAction['actionType_id'].inlist(getActionTypeIdListByFlatCode(u'received%')),
        tableAction['deleted'].eq(0),
        tableEvent['deleted'].eq(0),
        tableAP['deleted'].eq(0),
        tableAPT['deleted'].eq(0),
        tableClient['deleted'].eq(0),
        tableAP['action_id'].eq(tableAction['id']),
    ]
    if begDateTime.date():
        cond.append(db.joinOr([tableAction['begDate'].isNull(), tableAction['begDate'].ge(begDateTime)]))
    if endDateTime.date():
        cond.append(db.joinOr([tableAction['begDate'].isNull(), tableAction['begDate'].le(endDateTime)]))
    if sexIndex > 0:
        cond.append(tableClient['sex'].eq(sexIndex))
    if ageFor <= ageTo:
        cond.append(getAgeRangeCond(ageFor, ageTo))
    if orgStructureId:
        if hospitalBedsDialog.getOrgStructureId(orgStructureId):
            orgStructureIdList = hospitalBedsDialog.getOrgStructureIdList(orgStructureId)
            queryTable = queryTable.innerJoin(tableAPOS, tableAPOS['id'].eq(tableAP['id']))
            queryTable = queryTable.innerJoin(tableOS, tableOS['id'].eq(tableAPOS['value']))
            cond.append(tableOS['id'].inlist(orgStructureIdList))
    stmt = db.selectDistinctStmt(queryTable, cols, cond, [
        u'Client.lastName, Client.firstName, Client.patrName',
        u'Action.begDate',
        u'CAST(Event.externalId AS SIGNED)'][condSort])
    query = db.query(stmt)
    summaryVaccines = {}
    vaccineNames = set()
    vaccineStages = {}
    while query.next():
        records = query.record()
        clientId = forceRef(records.value('client_id'))
        eventId = forceRef(records.value('eventId'))
        begDate = forceDate(records.value('begDate'))
        begTime = forceTime(records.value('begDate'))
        endDate = forceDate(records.value('endDate'))
        endTime = forceTime(records.value('endDate'))
        note = forceString(records.value('note'))
        contractId = forceRef(records.value('contract_id'))
        financeId = forceRef(records.value('finance_id'))
        vaccine = forceString(records.value('vaccine')) or forceString(records.value('vaccine2'))
        vaccineStage = forceString(records.value('vaccineStage')) or forceString(records.value('vaccineStage2'))
        vaccineDate = forceString(records.value('vaccineDate')) or forceString(records.value('vaccineDate2'))
        vaccineNames.add(vaccine)
        vaccineStages.setdefault(vaccine, set()).add(vaccineStage)
        noteText = u''
        if note != u'':
            noteText = note + u'. '
        if clientId:
            clientInfo = getClientInfoEx(clientId)
            clientInfo['phones'] = getClientPhonesEx(clientId)
            adress = u''
            if clientInfo['locAddress']:
                adress += u'проживание: ' + clientInfo['locAddress']
            if clientInfo['phones']:
                adress += u', телефон: ' + clientInfo['phones']
            i = table.addRow()
            cnt += 1
            table.setText(i, 0, cnt)
            table.setText(i, 1, begDate.toString('dd.MM.yyyy'))
            table.setText(i, 2, begTime.toString('hh:mm:ss'))
            table.setText(i, 3, clientInfo['fullName'])
            table.setText(i, 4, formatDate(clientInfo['birthDate']) + u'(' + clientInfo['age'] + u')')
            table.setText(i, 5, adress)
            table.setText(i, 11, endDate.toString('dd.MM.yyyy'))
            table.setText(i, 12, endTime.toString('hh:mm:ss'))
            table.setText(i, 18, vaccine)
            table.setText(i, 19, vaccineStage)
            table.setText(i, 20, vaccineDate)
            numberCardStr = u''
            numberCardList = []
            numberCardList.append(forceRef(records.value('externalId')))
            numberCardStr = ','.join(str(numberCard) for numberCard in numberCardList if numberCardList)
            table.setText(i, 8, numberCardStr)
            whoDirecting = u''
            queryClientId = queryProperty(clientId, records, u'received%', u'whoDirecting', u'Кем направлен%', 0, condOrgStructure=condOrgStructure)
            if queryClientId.first():
                record = queryClientId.record()
                whoDirecting = u'Направлен: ' + forceString(record.value('whoDirecting')) + u' '
            queryClientId = queryProperty(clientId, records, u'received%', u'whoDelivered', u'Кем доставлен%', condOrgStructure=condOrgStructure)
            if queryClientId.first():
                record = queryClientId.record()
                whoDirecting += u'Доставлен: ' + forceString(record.value('whoDelivered'))
            table.setText(i, 6, whoDirecting)
            nameOSTypeEventList = []
            queryClientId = queryProperty(clientId, records, u'received%', u'orgStructure', u'Направлен в отделение%', 1, condOrgStructure=condOrgStructure)
            if queryClientId.first():
                record = queryClientId.record()
                nameOSTypeEventList.append(forceString(record.value('orgStructure')))
            table.setText(i, 7, u'; '.join(nameOSTypeEvent for nameOSTypeEvent in nameOSTypeEventList if nameOSTypeEvent))
            diagnosisList = []
            finalDiagnosisList = []
            queryTableMKB = tableEvent.innerJoin(tableDiagnostic, tableEvent['id'].eq(tableDiagnostic['event_id']))
            queryTableMKB = queryTableMKB.innerJoin(tableDiagnosis, tableDiagnostic['diagnosis_id'].eq(tableDiagnosis['id']))
            queryTableMKB = queryTableMKB.innerJoin(tableRBDiagnosisType, tableDiagnostic['diagnosisType_id'].eq(tableRBDiagnosisType['id']))
            queryTableMKB = queryTableMKB.innerJoin(tableMKB, tableMKB['DiagID'].eq(tableDiagnosis['MKB']))
            condMKB = [
                tableEvent['deleted'].eq(0),
                tableEvent['id'].eq(eventId),
                tableDiagnosis['deleted'].eq(0),
                tableDiagnostic['deleted'].eq(0),
                # 0013377:0059294 - выводить все диагнозы?
                # tableRBDiagnosisType['code'].inlist([1, 7]),
            ]
            colsMKB = [
                tableRBDiagnosisType['code'],
                tableDiagnosis['MKB'],
                tableMKB['DiagName']
            ]
            stmt = db.selectDistinctStmt(queryTableMKB, colsMKB, condMKB)
            queryClientId = db.query(stmt)
            while queryClientId.next():
                record = queryClientId.record()
                diagName = forceString(record.value('DiagName'))
                mkb = forceString(record.value('MKB'))
                code = forceString(record.value('code'))
                value = diagName + '(' + mkb + ')'

                if code == 1:
                    finalDiagnosisList.append(value)
                else:
                    diagnosisList.append(value)
            queryClientId = queryProperty(clientId, records, u'received%', u'diagnosis', u'Диагноз направителя%', condOrgStructure=condOrgStructure)
            while queryClientId.next():
                record = queryClientId.record()
                diagnosisList.append(forceString(record.value('DiagName'))+u'('+forceString(record.value('MKB'))+u')')
            table.setText(i, 9, u', '.join(diagnos for diagnos in diagnosisList if diagnos))
            table.setText(i, 14, u', '.join(diagnos for diagnos in finalDiagnosisList if diagnos))
            queryClientId = queryProperty(clientId, records, u'received%', u'nameRenuncReason', u'Причина отказа%', condOrgStructure=condOrgStructure)
            nameRenunciate = u''
            if queryClientId.first():
                record = queryClientId.record()
                nameRenunciate = u'Причина: ' + forceString(record.value('nameRenuncReason')) + u' '
            queryClientId = queryProperty(clientId, records, u'received%', u'nameRenuncMeasure', u'Принятые меры при отказе%', condOrgStructure=condOrgStructure)
            if queryClientId.first():
                record = queryClientId.record()
                nameRenunciate += u'Меры: ' + forceString(record.value('nameRenuncMeasure'))
            table.setText(i, 16, nameRenunciate)
            queryClientId = queryProperty(clientId, records, u'received%', u'refusal', u'Отказ в приеме%', condOrgStructure=condOrgStructure)
            if queryClientId.first():
                record = queryClientId.record()
                table.setText(i, 17, forceString(record.value('refusal')))
            queryClientId = queryProperty(clientId, records, u'leaved%', u'', u'', 3, condOrgStructure=condOrgStructure)
            if queryClientId.first():
                record = queryClientId.record()
                actionIdLeaved = forceRef(record.value('actionIdLeaved'))
                noteText += forceString(record.value('noteLeaved'))
                if actionIdLeaved:
                    result = u''
                    queryClientId = queryProperty(clientId, records, u'leaved%', u'resultHaspital', u'Исход госпитализации%', None, actionIdLeaved, condOrgStructure=condOrgStructure)
                    if queryClientId.first():
                        record = queryClientId.record()
                        resultHaspital = forceString(record.value('resultHaspital'))
                        result = resultHaspital + u' '
                        begDateLeaved = forceDate(record.value('begDateLeaved'))
                        if begDateLeaved:
                            result += begDateLeaved.toString('dd.MM.yyyy') + u' '
                    queryClientId = queryProperty(clientId, records, u'leaved%', u'transferOrganisation', u'Переведен в стационар%', None, actionIdLeaved, condOrgStructure=condOrgStructure)
                    if queryClientId.first():
                        record = queryClientId.record()
                        transferOrganisation = forceString(record.value('transferOrganisation'))
                        result += u'Перевод: ' + transferOrganisation
                    table.setText(i, 13, result)
                    if result.lower().startswith(u'переведен'):
                        result = u'Переведен в другой стационар'
                    summaryVaccines.setdefault(result, {})
                    summaryVaccines[result].setdefault(vaccine, {})
                    summaryVaccines[result][vaccine].setdefault(vaccineStage, 0)
                    summaryVaccines[result][vaccine][vaccineStage] += 1
                    queryClientId = queryProperty(clientId, records, u'leaved%', u'messageRelative', u'Сообщение родственникам%', None, actionIdLeaved, condOrgStructure=condOrgStructure)
                    if queryClientId.first():
                        record = queryClientId.record()
                        table.setText(i, 15, forceString(record.value('messageRelative')))
            table.setText(i, 21, noteText)

    reportView = CReportViewDialog(hospitalBedsDialog)
    reportView.setWindowTitle(u'Журнал 2')
    reportView.setOrientation(QtGui.QPrinter.Landscape)
    reportView.setText(doc)
    reportView.exec_()


class CStationaryReportF001(CReportBase):
    def __init__(self, hospitalBedsDialog):
        CReportBase.__init__(self, hospitalBedsDialog)
        self.hospitalBedsDialog = hospitalBedsDialog
        self.setTitle(u'Журнал учета приема пациентов и отказов. Ф001 Приказ 530н')


    def getSetupDialog(self, parent):
        setupDialog = CReportF001SetupDialog(parent)
        return setupDialog


    def getDefaultParams(self):
        return getPref(QtGui.qApp.preferences.reportPrefs, u'StationaryReportF001', {})


    def saveDefaultParams(self, params):
        setPref(QtGui.qApp.preferences.reportPrefs, u'StationaryReportF001', params)


    def selectData(self, params):
        orgStructureId = self.hospitalBedsDialog.treeOrgStructure.currentIndex()
        begDate = self.hospitalBedsDialog.edtFilterBegDate.date()
        endDate = self.hospitalBedsDialog.edtFilterEndDate.date()
        sexIndex = self.hospitalBedsDialog.cmbSex.currentIndex()
        ageFor = self.hospitalBedsDialog.spbAgeFor.value()
        ageTo = self.hospitalBedsDialog.spbAgeTo.value()
        begTime = self.hospitalBedsDialog.edtFilterBegTime.time()
        endTime = self.hospitalBedsDialog.edtFilterEndTime.time()
        begDateTime = QDateTime(begDate, begTime)
        endDateTime = QDateTime(endDate, endTime)
        condSort = getPref(params, 'condSort', 0)

        db = QtGui.qApp.db
        tableActionType = db.table('ActionType')
        tableAction = db.table('Action')
        tableEvent = db.table('Event')
        tableClient = db.table('Client')
        tableAPOS = db.table('ActionProperty_OrgStructure')
        tableOS = db.table('OrgStructure')
        cols = [
            tableAction['id'].alias('actionId'),
            tableAction['begDate'],
            tableAction['note'],
            tableAction['finance_id'],

            tableEvent['id'].alias('eventId'),
            tableEvent['externalId'],
            tableEvent['contract_id'],
            tableEvent['execPerson_id'],

            tableClient['id'].alias('clientId'),
            tableClient['birthDate'],
            tableClient['lastName'],
            tableClient['firstName'],
            tableClient['patrName'],
            tableClient['sex'],
            tableClient['SNILS'],

            'getClientLocAddress(Client.id) AS locAddress',
            'getClientRegAddress(Client.id) AS regAddress',
            'IF(Event.relative_id is Null, getClientContacts(Client.id), getClientContacts(Event.relative_id)) AS contacts',
            'getClientWork(Client.id) AS work',
            'getClientPolicy(Client.id, 1) AS policy',
            'getClientDocument(Client.id) AS document',

            u'(SELECT \
                rbSocStatusType.name \
              FROM \
                ClientSocStatus CSS \
                JOIN rbSocStatusType ON CSS.socStatusType_id = rbSocStatusType.id \
                JOIN rbSocStatusClass ON CSS.socStatusClass_id = rbSocStatusClass.id \
              WHERE \
                CSS.deleted = 0 \
                AND CSS.client_id = Client.id \
                AND rbSocStatusClass.name LIKE "%гражданств%" \
              LIMIT 1 \
            ) AS citizenship',

            getMKB(),
            getStringPropertyValue(u'Доставлен в состоянии опьянения') + ' AS receivedDrunk',
        ]
        queryTable = tableAction.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
        queryTable = queryTable.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
        queryTable = queryTable.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
        cond = [
            tableActionType['flatCode'].like(u'received%'),
            tableAction['deleted'].eq(0),
            tableEvent['deleted'].eq(0),
            tableClient['deleted'].eq(0),
        ]
        if begDateTime.date():
            cond.append(tableAction['begDate'].ge(begDateTime))
        if endDateTime.date():
            cond.append(tableAction['begDate'].le(endDateTime))
        if sexIndex > 0:
            cond.append(tableClient['sex'].eq(sexIndex))
        if ageFor <= ageTo:
            cond.append(getAgeRangeCond(ageFor, ageTo))
        if orgStructureId:
            if self.hospitalBedsDialog.getOrgStructureId(orgStructureId):
                orgStructureIdList = self.hospitalBedsDialog.getOrgStructureIdList(orgStructureId)
                tableAPT = db.table('ActionPropertyType')
                tableAP = db.table('ActionProperty')
                queryTable = queryTable.innerJoin(tableAPT, tableAPT['actionType_id'].eq(tableActionType['id']))
                queryTable = queryTable.innerJoin(tableAP, tableAP['type_id'].eq(tableAPT['id']))
                queryTable = queryTable.innerJoin(tableAPOS, tableAPOS['id'].eq(tableAP['id']))
                queryTable = queryTable.innerJoin(tableOS, tableOS['id'].eq(tableAPOS['value']))
                cond.extend([
                    tableOS['id'].inlist(orgStructureIdList),
                    tableAP['action_id'].eq(tableAction['id']),
                    tableAP['deleted'].eq(0),
                    tableAPT['deleted'].eq(0),
                ])
        cond.append(tableAction['endDate'].isNotNull())
        stmt = db.selectDistinctStmt(queryTable, cols, cond, [
            u'Client.lastName, Client.firstName, Client.patrName',
            u'Action.begDate',
            u'CAST(Event.externalId AS SIGNED)'][condSort])
        return db.query(stmt)


    def getPreliminaryDiagnosis(self, record, condOrgStructure, actionId, isMain):
        db = QtGui.qApp.db
        eventId = forceRef(record.value('eventId'))
        clientId = forceRef(record.value('clientId'))
        diagnosisList = []
        tableEvent = db.table('Event')
        tableDiagnosis = db.table('Diagnosis')
        tableDiagnostic = db.table('Diagnostic')
        tableMKB = db.table('MKB')
        tableRBDiagnosisType = db.table('rbDiagnosisType')

        queryTableMKB = tableEvent.innerJoin(tableDiagnostic, tableEvent['id'].eq(tableDiagnostic['event_id']))
        queryTableMKB = queryTableMKB.innerJoin(tableDiagnosis, tableDiagnostic['diagnosis_id'].eq(tableDiagnosis['id']))
        queryTableMKB = queryTableMKB.innerJoin(tableRBDiagnosisType, tableDiagnostic['diagnosisType_id'].eq(tableRBDiagnosisType['id']))
        queryTableMKB = queryTableMKB.innerJoin(tableMKB, tableMKB['DiagID'].eq(tableDiagnosis['MKB']))

        condMKB = [
            tableEvent['deleted'].eq(0),
            tableEvent['id'].eq(eventId),
            tableDiagnosis['deleted'].eq(0),
            tableDiagnostic['deleted'].eq(0),
            tableRBDiagnosisType['code'].eq(isMain),
        ]
        stmt = db.selectDistinctStmt(queryTableMKB, u'Diagnosis.MKBEx, MKB.DiagName', condMKB)
        queryClientId = db.query(stmt)

        while queryClientId.next():
            rec = queryClientId.record()
            diagnosisList.append(forceString(rec.value('DiagName'))+' '+forceString(rec.value('MKBEx')))
              
        return u', '.join(i for i in diagnosisList if i)


    def getReceivedToOrgStructure(self, record, condOrgStructure, actionId):
        db = QtGui.qApp.db
        clientId = forceRef(record.value('clientId'))
        nameOSTypeEventList = []
        contractId = forceRef(record.value('contract_id'))
        financeId = forceRef(record.value('finance_id'))

        queryClientId = queryProperty(clientId, record, u'received%', u'orgStructure', u'Направлен в отделение%', flag=1, actionIdLeaved=actionId, condOrgStructure=condOrgStructure)
        if queryClientId.first():
            rec = queryClientId.record()
            nameOSTypeEventList.append(forceString(rec.value('orgStructure')))
        tableRBFinance = db.table('rbFinance')
        if financeId:
            recordFinance = db.getRecordEx(tableRBFinance, [tableRBFinance['name']], [tableRBFinance['id'].eq(financeId)])
            nameOSTypeEventList.append(u'\n' + forceString(recordFinance.value('name')) if recordFinance else '')
        else:
            if contractId:
                tableContract = db.table('Contract')
                tableFinanceQuery = tableContract.innerJoin(tableRBFinance, tableContract['finance_id'].eq(tableRBFinance['id']))
                recordFinance = db.getRecordEx(tableFinanceQuery, tableRBFinance['name'], [
                    tableContract['id'].eq(contractId),
                    tableContract['deleted'].eq(0)])
                nameOSTypeEventList.append(u'\n' + forceString(recordFinance.value('name')) if recordFinance else '')
        return u'; '.join(nameOSTypeEvent for nameOSTypeEvent in nameOSTypeEventList if nameOSTypeEvent)


    def getLeavedInfo(self, record, condOrgStructure):
        clientId = forceRef(record.value('clientId'))

        result = u''
        # noteText = u''
        messageRelative = u''

        queryClientId = queryProperty(clientId, record, u'leaved%', u'', u'', 3, condOrgStructure=condOrgStructure)
        if queryClientId.first():
            rec = queryClientId.record()
            actionIdLeaved = forceRef(rec.value('actionIdLeaved'))
            # noteText += forceString(rec.value('noteLeaved'))
            if actionIdLeaved:
                queryClientId = queryProperty(clientId, record, u'leaved%', u'resultHaspital', u'Исход госпитализации%', None, actionIdLeaved, condOrgStructure=condOrgStructure)
                if queryClientId.first():
                    rec = queryClientId.record()
                    resultHaspital = forceString(rec.value('resultHaspital'))
                    result = resultHaspital + u' '
                    begDateLeaved = forceDate(rec.value('begDateLeaved'))
                    if begDateLeaved:
                        result += begDateLeaved.toString('dd.MM.yyyy') + u' '
                queryClientId = queryProperty(clientId, record, u'leaved%', u'transferOrganisation', u'Переведен в стационар%', None, actionIdLeaved, condOrgStructure=condOrgStructure)
                if queryClientId.first():
                    rec = queryClientId.record()
                    transferOrganisation = forceString(rec.value('transferOrganisation'))
                    result += u'Перевод: ' + transferOrganisation
                queryClientId = queryProperty(clientId, record, u'leaved%', u'messageRelative', u'Сообщение родственникам%', None, actionIdLeaved, condOrgStructure=condOrgStructure)
                if queryClientId.first():
                    rec = queryClientId.record()
                    messageRelative = forceString(rec.value('messageRelative'))

        return result, messageRelative


    def build(self, params):
        condOrgStructure = getPref(params, 'condOrgStructure', 0)

        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(u'Журнал учета приема пациентов и отказов. Ф001 Приказ 530н')
        cursor.insertBlock()

        tableColumns = [
            ('', [u'№', u'', u'1'], CReportBase.AlignCenter),
            ('', [u'Поступление', u'дата', u'2'], CReportBase.AlignCenter),
            ('', [u'', u'час', u'3'], CReportBase.AlignCenter),
            ('', [u'Фамилия, И., О.', u'', u'4'], CReportBase.AlignLeft),
            ('', [u'Дата рождения', u'', u'5'], CReportBase.AlignLeft),
            ('', [u'Пол', u'', u'6'], CReportBase.AlignLeft),
            ('', [u'Серия и номер паспорта или иного документа, удостоверяющего личность', u'', u'7'], CReportBase.AlignLeft),
            ('', [u'Гражданство', u'', u'8'], CReportBase.AlignLeft),
            ('', [u'Регистрация по месту жительства', u'', u'9'], CReportBase.AlignLeft),
            ('', [u'Регистрация по месту пребывания пациента, номер телефона законного представителя, лица, которому может быть передана информация о состоянии здоровья пациента', u'', u'10'], CReportBase.AlignLeft),
            ('', [u'СНИЛС', u'', u'11'], CReportBase.AlignLeft),
            ('', [u'Полис ОМС', u'', u'12'], CReportBase.AlignLeft),
            ('', [u'Пациент доставлен (направлен) полицией, выездной бригадой скорой медицинской помощи, другой медицинской организацией, обратился самостоятельно', u'', u'13'], CReportBase.AlignLeft),
            ('', [u'Номер медицинской карты', u'', u'14'], CReportBase.AlignLeft),
            ('', [u'Диагноз заболевания (состояния), поставленный направившей медицинской организацией, выездной бригадой скорой медицинской помощи (код по МКБ)', u'', u'15'], CReportBase.AlignLeft),
            ('', [u'Причина и обстоятельства травмы (в том числе при дорожно-транспортных происшествиях), отравления (код по МКБ)', u'', u'16'], CReportBase.AlignLeft),
            ('', [u'Факт употребления алкоголя и иных психоактивных веществ, установление наличия или отсутствия признаков состояния опьянения при поступлении пациента в медицинскую организацию, дата и время взятия пробы и результаты лабораторных исследований', u'', u'17'], CReportBase.AlignLeft),
            ('', [u'Отделение медицинской организации, в которое направлен пациент', u'', u'18'], CReportBase.AlignLeft),
            ('', [u'Исход госпитализации (выписан, переведен в другую медицинскую организацию, умер), дата и время исхода, наименование МО, куда переведен пациент', u'', u'19'], CReportBase.AlignLeft),
            ('', [u'Дата и время сообщения законному представителю, иному лицу или МО, направившей пациента, о госпитализации (отказе в госпитализации) пациента, ее исходе', u'', u'20'], CReportBase.AlignLeft),
            ('', [u'Причина отказа в госпитализации (отказался пациент, отсутствие показаний, помощь оказана в приемном отделении медицинской организации, направлен в другую медицинскую организацию, иная причина)', u'', u'21'], CReportBase.AlignLeft),
            ('', [u'Фамилия, имя, отчество (при наличии) медицинского работника, зафиксировавшего причину отказа в госпитализации', u'', u'22'], CReportBase.AlignLeft),
            ('', [u'Дополнительные сведения', u'', u'23'], CReportBase.AlignLeft),
        ]
        table = createTable(cursor, tableColumns, duplicateHeaderOnNewPage=False)
        for i, col in enumerate(tableColumns):
            if i == 1:  # поступление
                table.mergeCells(0,i, 1,2)
            elif i == 2:
                continue
            else:
                table.mergeCells(0,i, 2,1)

        query = self.selectData(params)
        n = 1
        while query.next():
            record = query.record()
            actionId = forceRef(record.value('actionId'))
            clientId = forceRef(record.value('clientId'))
            lastName = forceString(record.value('lastName'))
            firstName = forceString(record.value('firstName'))
            patrName = forceString(record.value('patrName'))
            sex = forceInt(record.value('sex'))
            document = forceString(record.value('document'))
            birthDate = forceDate(record.value('birthDate'))
            citizenship = forceString(record.value('citizenship'))
            regAddress = forceString(record.value('regAddress'))
            locAddress = forceString(record.value('locAddress'))
            contacts = forceString(record.value('contacts'))
            snils = forceString(record.value('SNILS'))
            policy = forceString(record.value('policy'))
            begDateTime = forceDateTime(record.value('begDate'))
            personId = forceRef(record.value('execPerson_id'))
            #MKB = forceString(record.value('MKB')) + ' ' + getMKBName(forceString(record.value('MKB')))
            receivedDrunk = forceString(record.value('receivedDrunk'))
            note = forceString(record.value('note'))

            addressAndContact = u''
            if locAddress:
                addressAndContact += u'проживание: ' + locAddress
            if contacts:
                addressAndContact += u', телефон: ' + contacts

            MKB = u''
            queryClientId = queryProperty(clientId, record, u'received%', u'MKB', u'Диагноз направителя%', actionIdLeaved=actionId, condOrgStructure=condOrgStructure)
            if queryClientId.first():
                rec = queryClientId.record()
                MKB = forceString(rec.value('MKB'))
            
            whoDirecting = u''
            queryClientId = queryProperty(clientId, record, u'received%', u'whoDirecting', u'Кем направлен%', 0, actionIdLeaved=actionId, condOrgStructure=condOrgStructure)
            if queryClientId.first():
                rec = queryClientId.record()
                whoDirecting = u'Направлен: ' + forceString(rec.value('whoDirecting')) + u' '
            queryClientId = queryProperty(clientId, record, u'received%', u'whoDelivered', u'Кем доставлен%', actionIdLeaved=actionId, condOrgStructure=condOrgStructure)
            if queryClientId.first():
                rec = queryClientId.record()
                whoDirecting += u'Доставлен: ' + forceString(rec.value('whoDelivered'))

            numberCardList = []
            numberCardList.append(forceString(record.value('externalId')))
            numberCardStr = ', '.join(numberCard for numberCard in numberCardList if numberCard)

            nameRenunciate = u''
            queryClientId = queryProperty(clientId, record, u'received%', u'nameRenuncReason', u'Причина отказа%', actionIdLeaved=actionId, condOrgStructure=condOrgStructure)
            if queryClientId.first():
                rec = queryClientId.record()
                nameRenunciate = u'Причина: ' + forceString(rec.value('nameRenuncReason')) + u' '
            queryClientId = queryProperty(clientId, record, u'received%', u'nameRenuncMeasure', u'Принятые меры при отказе%', actionIdLeaved=actionId, condOrgStructure=condOrgStructure)
            if queryClientId.first():
                rec = queryClientId.record()
                nameRenunciate += u'Меры: ' + forceString(rec.value('nameRenuncMeasure'))

            refusal = u''
            if personId:
                personInfo = getPersonInfo(personId)
                refusal = personInfo['shortName']+', '+personInfo['specialityName']
            #queryClientId = queryProperty(clientId, record, u'received%', u'refusal', u'Отказ в приеме%', actionIdLeaved=actionId, condOrgStructure=condOrgStructure)
            #if queryClientId.first():
            #    rec = queryClientId.record()
            #    refusal = forceString(rec.value('refusal'))

            leavedResult, leavedMessageRelative = self.getLeavedInfo(record, condOrgStructure)

            row = table.addRow()
            table.setText(row, 0, n)
            table.setText(row, 1, formatDate(begDateTime.date()))
            table.setText(row, 2, formatTime(begDateTime.time()))
            table.setText(row, 3, formatName(lastName, firstName, patrName))
            table.setText(row, 4, formatDate(birthDate) + ' (' + calcAge(birthDate) + ')')
            table.setText(row, 5, formatSex(sex))
            table.setText(row, 6, document)
            table.setText(row, 7, citizenship)
            table.setText(row, 8, regAddress)
            table.setText(row, 9, addressAndContact)
            table.setText(row, 10, snils)
            table.setText(row, 11, policy)
            table.setText(row, 12, whoDirecting)
            table.setText(row, 13, numberCardStr if numberCardStr else u'')
            if MKB:
                table.setText(row, 14, MKB)
                table.setText(row, 15, self.getPreliminaryDiagnosis(record, condOrgStructure, actionId, 7))
            table.setText(row, 16, receivedDrunk)
            table.setText(row, 17, self.getReceivedToOrgStructure(record, condOrgStructure, actionId))
            table.setText(row, 18, leavedResult)
            table.setText(row, 19, leavedMessageRelative)
            if nameRenunciate:
                table.setText(row, 20, nameRenunciate)
                table.setText(row, 21, refusal)
            table.setText(row, 22, note)
            n += 1

        return doc


def execStationaryReportF001(hospitalBedsDialog):
    CStationaryReportF001(hospitalBedsDialog).exec_()
