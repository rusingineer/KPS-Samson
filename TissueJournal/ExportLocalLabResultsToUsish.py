# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2016-2017 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

import re
import json
from collections import namedtuple

from PyQt4 import QtGui
from PyQt4.QtCore import QDateTime

from Orgs.Utils import getPersonOrgStructureId, getOrgStructureBookkeeperCode
from library.Utils import forceDateTime, forceRef, forceString, smartDict


from Events.Action                     import CAction
from Events.ActionStatus               import CActionStatus
from RefBooks.Equipment.Protocol          import CEquipmentProtocol
from RefBooks.Equipment.RoleInIntegration import CEquipmentRoleInIntegration

from Registry.Utils                    import getClientInfo

from TissueJournal.LabInterfaceFHIR    import sendLocalResultsOverFHIR as sendLocalResultsOverFHIR050
from TissueJournal.LabInterfaceFHIR102 import sendLocalResultsOverFHIR as sendLocalResultsOverFHIR102, \
    sendResultsOverFHIR, getOrgStructureIdentification, CFHIRExchange
from TissueJournal.Utils               import getEquipmentInterface

def exportLocalLabResultsToUsishKK(days=30):
    u"""Выгрузка результатов в ОДЛИ из локальной лаборатории в КК"""
    db = QtGui.qApp.db
    # подготовительный этап
    systemId = getExternalSystemId(u'N3.ODLI', u'Нетрика "Сервис обмена данными лабораторных исследований"')
    # выбрать подходящие действия, без группировки
    actionIdList = selectActionIdListKK(systemId, days)
    address = {}
    address["url"] = forceString(db.translate('GlobalPreferences', 'code', 'ODLI_URL', 'value'))
    address["authorization"] = forceString(db.translate('GlobalPreferences', 'code', 'ODLI_AUTH', 'value'))
    address['tests_urn'] = "urn:oid:1.2.643.5.1.13.13.11.1080"
    address['tests_version'] = "1"
    address['target'] = None
    address['terminology_url'] = 'http://10.0.1.179/nsi/fhir/term ' #"http://r23-rc.zdrav.netrika.ru/nsi/fhir/term/"
    address['mis_oid'] = forceString(db.translate('GlobalPreferences', 'code', 'Netrika.MIS_OID', 'value'))

    equipmentInterface = smartDict(id=999,
              eachTestDetached=False,
              protocol=4,
              address=json.dumps(address),
              ownName=u'ODLI',
              ownCode=u'ODLI',
              labName=u'localLab',
              labCode=u'local',
              specimenIdentifierMode=0,
              protocolVersion=4,
              resultOnFact=False
              )
    mapTestIdToCode = getMapTestIdToTestCodeKK()
    mapPersonToOrgStructureId = {}
    mapOrgStructureIdToDescr = {}
    COrgstructureDescr = namedtuple('COrgstructureDescr', ['code', 'identification'])
    # в цикле передавать действия и отмечать как переданные
    # actionIdList = [8726271]
    for actionId in actionIdList:
        try:
            testResults, eventId, serviceId, modifyDatetime = extractResultsEtc(mapTestIdToCode, actionId)
            if testResults and serviceId:
                tableEvent = db.table('Event')
                recEvent = db.getRecordEx(tableEvent, [tableEvent['client_id'], tableEvent['execPerson_id'], tableEvent['setPerson_id']], tableEvent['id'].eq(eventId))
                clientId = forceRef(recEvent.value('client_id')) if recEvent else None
                personId = testResults[0].personId
                # выгрузка результатов от подразделений
                orgStructureId = mapPersonToOrgStructureId.get(personId, None)
                if not orgStructureId:
                    orgStructureId = getPersonOrgStructureId(personId)
                    mapPersonToOrgStructureId[personId] = orgStructureId
                orgStructureDescr = mapOrgStructureIdToDescr.get(orgStructureId, None)
                if not orgStructureDescr and orgStructureId:
                    code = getOrgStructureBookkeeperCode(orgStructureId)
                    identification = getOrgStructureIdentification(CFHIRExchange.urnOrgs, orgStructureId)
                    orgStructureDescr = COrgstructureDescr(code, identification)
                    mapOrgStructureIdToDescr[orgStructureId] = orgStructureDescr

                personId = forceRef(recEvent.value('execPerson_id')) if recEvent else None
                if not personId:
                    personId = forceRef(recEvent.value('setPerson_id')) if recEvent else None
                if not personId:
                    personId = testResults[0].personId
                orgStructureId = mapPersonToOrgStructureId.get(personId, None)

                if not orgStructureId:
                    orgStructureId = getPersonOrgStructureId(personId)
                    mapPersonToOrgStructureId[personId] = orgStructureId
                sourceOrgStructureDescr = mapOrgStructureIdToDescr.get(orgStructureId, None)
                if not sourceOrgStructureDescr and orgStructureId:
                    code = getOrgStructureBookkeeperCode(orgStructureId)
                    identification = getOrgStructureIdentification(CFHIRExchange.urnOrgs, orgStructureId)
                    sourceOrgStructureDescr = COrgstructureDescr(code, identification)
                    mapOrgStructureIdToDescr[orgStructureId] = sourceOrgStructureDescr

                clientInfo = getClientInfo(clientId)
                if equipmentInterface.protocol == 3:
                    sendLocalResultsOverFHIR050(equipmentInterface, clientInfo, serviceId, testResults)
                elif equipmentInterface.protocol == 4:
                    sendLocalResultsOverFHIR102(equipmentInterface, clientInfo, serviceId, testResults, actionId, orgStructureDescr, sourceOrgStructureDescr)
                else:
                    assert False, 'Invalid equipmentInterface.protocol'
                # markActionAsExported(systemId, actionId, modifyDatetime)
            else:
                from library.Utils import toVariant
                externalSystemId = forceRef(QtGui.qApp.db.translate('rbExternalSystem', 'code', 'N3.ODLI', 'id'))
                tableAction_Export = db.table('Action_Export')
                actionExport = db.getRecordEx(tableAction_Export, '*',
                                              'master_id = %d and system_id = %d' % (actionId, externalSystemId))
                if not actionExport:
                    actionExport = tableAction_Export.newRecord()
                actionExport.setValue('master_id', toVariant(actionId))
                actionExport.setValue('system_id', toVariant(systemId))
                actionExport.setValue('success', toVariant(0))
                actionExport.setValue('note', u'Для этого действия не задана услуга или тесты')
                actionExport.setValue('dateTime', toVariant(QDateTime.currentDateTime()))
                # actionExport.setValue('externalId', toVariant(actionIdentifier.value))
                db.insertOrUpdate(tableAction_Export, actionExport)
                QtGui.qApp.log('export local results', u'Для действия %i не задан сервис или тесты' % actionId, level=1)
        except Exception:
            QtGui.qApp.logCurrentException()


def exportLocalLabResultsToUsish(dateFrom, dateTo, exportIbm = None):
    db = QtGui.qApp.db
    # подготовительный этап
    destEquipmentIdList = getDestEquipmentIdList()
    srcEquipmentIdList  = getSrcEquipmentIdList()

    systemId = getExternalSystemId(u'N3.РЕГИСЗ.ОДЛИ:доп', u'Нетрика, сервис «ОДЛИ», исследования проведённые в локальной лаборатории')

    if destEquipmentIdList:
        destEquipmentId = destEquipmentIdList[0]
        mapTestIdToCode = getMapTestIdToTestCode(destEquipmentId)
        equipmentInterface = getEquipmentInterface(destEquipmentId)

        # выбрать подходящие действия, без группировки
        if exportIbm:
            actionIdList = selectActionIdListByIbm(srcEquipmentIdList, systemId, exportIbm, True)
        else:
            actionIdList = selectActionIdList(srcEquipmentIdList, systemId, dateFrom, dateTo, True)
        # в цикле передавать действия и отмечать как переданные
        for actionId in actionIdList:
            try:
                testResults, eventId, serviceId, modifyDatetime = extractResultsEtc(mapTestIdToCode, actionId)
                if testResults and serviceId:
                    clientId   = forceRef(db.translate('Event', 'id', eventId, 'client_id'))
                    clientInfo = getClientInfo(clientId)
                    if equipmentInterface.protocol == CEquipmentProtocol.fhir050:
                        sendLocalResultsOverFHIR050(equipmentInterface, clientInfo, serviceId, testResults)
                        identifier = None
                    elif equipmentInterface.protocol == CEquipmentProtocol.fhir102:
                        identifier = sendLocalResultsOverFHIR102(equipmentInterface, clientInfo, serviceId, testResults)
                    else:
                        assert False, 'Invalid equipmentInterface.protocol'
                    markActionAsExported(systemId, actionId, modifyDatetime, identifier)
                else:
                    QtGui.qApp.log('export local results', u'Для действия %d не задан сервис или тесты'%actionId, level=1)
#            except CIdentificationException:
#                QtGui.qApp.logCurrentException()
#            except FHIRErrorException:
            except Exception:
                QtGui.qApp.logCurrentException()


def exportLabResultsToUsish(dateFrom, dateTo, exportIbm = None):
    db = QtGui.qApp.db
    # подготовительный этап
    destEquipmentIdList = getDestEquipmentIdList()
    srcEquipmentIdList  = getSrcEquipmentIdList()

    systemId = getExternalSystemId(u'N3.РЕГИСЗ.ОДЛИ:заявка', u'Нетрика, сервис «ОДЛИ», исследования проведённые в локальной лаборатории по заявке')
    if destEquipmentIdList:
        destEquipmentId = destEquipmentIdList[0]
        mapTestIdToCode = getMapTestIdToTestCode(destEquipmentId)
        equipmentInterface = getEquipmentInterface(destEquipmentId)

        # выбрать подходящие действия, без группировки
        actionIdList = selectActionIdList(srcEquipmentIdList, systemId, dateFrom, dateTo, False)
        if not actionIdList:
            QtGui.qApp.log('export results', u'Нет действий для выгрузки', level=3)
        # в цикле передавать действия и отмечать как переданные
        for actionId in actionIdList:
            try:
                testResults, eventId, serviceId, modifyDatetime = extractResultsEtc(mapTestIdToCode, actionId)
                if testResults and serviceId:
                    clientId   = forceRef(db.translate('Event', 'id', eventId, 'client_id'))
                    clientInfo = getClientInfo(clientId)
                    if equipmentInterface.protocol == CEquipmentProtocol.fhir102:
                        opts = json.loads(equipmentInterface.address)
                        if opts.get('arkhangelskEncounter', False):
                            createParams = opts.get('createParams', {})
                            setMKB = createParams.get('setMKB', None)
                            if setMKB is not None:
                                setDiagnostic(clientId, actionId, createParams.get('eventTypeId', None), setMKB)
                        identifier = sendResultsOverFHIR(equipmentInterface, clientInfo, serviceId, testResults)
                    else:
                        assert False, 'Invalid equipmentInterface.protocol'
                    markActionAsExported(systemId, actionId, modifyDatetime, identifier)
                else:
                    QtGui.qApp.log('export results', u'Для действия %i не задан сервис или тесты'%actionId, level=1)
#            except CIdentificationException:
#                QtGui.qApp.logCurrentException()
#            except FHIRErrorException:
            except Exception:
                QtGui.qApp.logCurrentException()

def setDiagnostic(clientId, actionId, optsEventTypeId, optsMKB):
    db = QtGui.qApp.db
    tableAction = db.table('Action')
    tableEvent = db.table('Event')
    tableDiagnosis = db.table('Diagnosis')
    tableDiagnostic = db.table('Diagnostic')
    tableDResult = db.table('rbDiagnosticResult')
    tableEType = db.table('EventType')
    tablePerson = db.table('Person')
    eventId = forceRef(db.translate(tableAction, 'id', actionId, tableAction['event_id']))
    eventTypeId = forceRef(db.translate(tableEvent, 'id', eventId, tableEvent['eventType_id']))
    if not optsEventTypeId or eventTypeId != optsEventTypeId:
        return

    if not db.getCount(tableDiagnostic, where=tableDiagnostic['event_id'].eq(eventId)):
        actionRecord = db.getRecord(tableAction, 'MKB, person_id', actionId)
        mkb = forceString(actionRecord.value('MKB')) if optsMKB == 'fromAction' else optsMKB
        personId = forceRef(actionRecord.value('person_id'))
        specialityId = forceRef(db.translate(tablePerson, 'id', personId, 'speciality_id'))

        table = tableEvent.leftJoin(tableEType, tableEType['id'].eq(tableEvent['eventType_id']))
        table = table.leftJoin(tableDResult, tableDResult['eventPurpose_id'].eq(tableEType['purpose_id']))
        cond = [tableEvent['id'].eq(eventId),
                tableDResult['federalCode'].eq('304')
                ]
        record = db.getRecordEx(table, tableDResult['id'], cond)
        resultId = None
        if record:
            resultId = forceRef(record.value(0))

        sisrecord = tableDiagnosis.newRecord()
        sisrecord.setValue('createDatetime', QDateTime.currentDateTime())
        sisrecord.setValue('client_id', clientId)
        sisrecord.setValue('diagnosisType_id', 1)
        sisrecord.setValue('MKB', mkb)
        sisrecord.setValue('setDate', actionRecord.value('begDate'))
        sisrecord.setValue('endDate', actionRecord.value('endDate'))
        sisId = db.insertRecord(tableDiagnosis, sisrecord)
        ticrecord = tableDiagnostic.newRecord()
        ticrecord.setValue('createDatetime', QDateTime.currentDateTime())
        ticrecord.setValue('event_id', eventId)
        ticrecord.setValue('diagnosis_id', sisId)
        ticrecord.setValue('diagnosisType_id', 1)
        ticrecord.setValue('result_id', resultId)
        ticrecord.setValue('speciality_id', specialityId)
        ticrecord.setValue('person_id', personId)
        ticrecord.setValue('setDate', actionRecord.value('begDate'))
        ticrecord.setValue('endDate', actionRecord.value('endDate'))
        db.insertRecord(tableDiagnostic, ticrecord)

def exportLocalLabResultsToUsishWithoutProbes(days=7):
    db = QtGui.qApp.db
    # подготовительный этап
    destEquipmentIdList = getDestEquipmentIdList()
    srcEquipmentIdList  = getSrcEquipmentIdList()

    systemId = getExternalSystemId(u'N3.РЕГИСЗ.ОДЛИ:доп', u'Нетрика, сервис «ОДЛИ», исследования проведённые в локальной лаборатории')
    if destEquipmentIdList:
        destEquipmentId = destEquipmentIdList[0]
        mapTestIdToCode = getMapTestIdToTestCode(destEquipmentId)
        equipmentInterface = getEquipmentInterface(destEquipmentId)

        # выбрать подходящие действия, без группировки
        actionIdList = selectActionIdListWithoutProbes(srcEquipmentIdList, systemId, days, True)
        # в цикле передавать действия и отмечать как переданные
        for actionId in actionIdList:
            try:
                testResults, eventId, serviceId, modifyDatetime = extractResultsEtc(mapTestIdToCode, actionId)
                if testResults and serviceId:
                    clientId   = forceRef(db.translate('Event', 'id', eventId, 'client_id'))
                    clientInfo = getClientInfo(clientId)
                    if equipmentInterface.protocol == CEquipmentProtocol.fhir050:
                        sendLocalResultsOverFHIR050(equipmentInterface, clientInfo, serviceId, testResults)
                    elif equipmentInterface.protocol == CEquipmentProtocol.fhir102:
                        sendLocalResultsOverFHIR102(equipmentInterface, clientInfo, serviceId, testResults)
                    else:
                        assert False, 'Invalid equipmentInterface.protocol'
                    markActionAsExported(systemId, actionId, modifyDatetime)
                else:
                    QtGui.qApp.log('export local results', u'Для действия %d не задан сервис или тесты'%actionId, level=1)
#            except CIdentificationException:
#                QtGui.qApp.logCurrentException()
#            except FHIRErrorException:
            except Exception:
                QtGui.qApp.logCurrentException()

def getDestEquipmentIdList():
    db = QtGui.qApp.db
    table = db.table('rbEquipment')
    return db.getIdList(table,
                        'id',
                        [ table['status'].eq(1),
                          table['protocol'].inlist([CEquipmentProtocol.fhir050, CEquipmentProtocol.fhir102]),
                          table['roleInIntegration'].eq(CEquipmentRoleInIntegration.gateway),
                        ]
                       )


def getSrcEquipmentIdList():
    db = QtGui.qApp.db
    table = db.table('rbEquipment')
    return db.getIdList(table,
                        'id',
                        [ table['status'].eq(1),
                          table['roleInIntegration'].eq(CEquipmentRoleInIntegration.internal),
                        ]
                       )


def getExternalSystemId(code, name):
    db = QtGui.qApp.db
    table = db.table('rbExternalSystem')
    result = db.translate(table, 'code', code, 'id')
    if not result:
        record = table.newRecord()
        record.setValue('code', code)
        record.setValue('name', name)
        candidate = db.insertRecord(table, record)
        if db.translate(table, 'code', code, 'id') == candidate:
            result = candidate
        else:
            db.deleteRecord(table, table['id'].eq(candidate))
            raise Exception(u'Невозможно добавить запись с кодом «%s» в rbExternalSystem' % code)
    return result


def getMapTestIdToTestCode(eqipmentId):
    db = QtGui.qApp.db
    table = db.table('rbEquipment_Test')
    records = db.getRecordList(table,
                               ['test_id', 'hardwareTestCode'],
                               db.joinAnd([table['equipment_id'].eq(eqipmentId),
                                           table['type'].inlist((1, 2)),
                                           table['test_id'].isNotNull()
                                          ])
                              )
    result = {}
    for record in records:
        code   = forceString(record.value('hardwareTestCode'))
        testId = forceRef(record.value('test_id'))
        result[testId] = code
    return result


def selectActionIdList(equipmentIdList, systemId, dateFrom, dateTo, localLab):
    db = QtGui.qApp.db
    tableAction = db.table('Action')
    tableActionType = db.table('ActionType')
    tableActionPropertyType = db.table('ActionPropertyType')
    tableEquipmentTest = db.table('rbEquipment_Test')
    tableEvent = db.table('Event')
    tableExport = db.table('Action_Export')
    tableProbe = db.table('Probe')

    table = tableAction
    table = table.innerJoin( tableActionType, tableActionType['id'].eq( tableAction['actionType_id'] ))
    table = table.innerJoin( tableActionPropertyType, db.joinAnd([
                                                                    tableActionPropertyType['actionType_id'].eq(tableAction['actionType_id']),
                                                                    tableActionPropertyType['deleted'].eq(0)
                                                                 ])
                           )
    table = table.innerJoin( tableEquipmentTest,      tableEquipmentTest['test_id'].eq( tableActionPropertyType['test_id'] ))
    table = table.innerJoin( tableEvent,              tableEvent['id'].eq( tableAction['event_id'] ))
    table = table.leftJoin (tableProbe,               tableProbe['takenTissueJournal_id'].eq(tableAction['takenTissueJournal_id']))
    table = table.leftJoin(tableExport, db.joinAnd([
                                                    tableExport['master_id'].eq(tableAction['id']),
                                                    tableExport['system_id'].eq(systemId)
                                                   ])
                          )
    if localLab:
        lisCond = db.joinAnd(['IFNULL(Action.org_id, Event.org_id) = %d' % QtGui.qApp.currentOrgId(),
                              tableEquipmentTest['equipment_id'].inlist(equipmentIdList),
                              db.joinOr([ tableProbe['id'].isNull(),
                                                         tableProbe['equipment_id'].inlist(equipmentIdList)
                                                       ]
                                                      ),
                             ])
    else:
        lisCond = db.joinAnd([tableEvent['srcNumber'].isNotNull(), tableAction['externalId'].isNotNull()])
    return db.getDistinctIdList( table,
                                 tableAction['id'],
                                 db.joinAnd([
                                             tableAction['status'].eq(CActionStatus.finished),
                                             tableAction['deleted'].eq(0),
                                             tableAction['endDate'].dateGe(dateFrom),
                                             tableAction['endDate'].dateLe(dateTo),
                                             tableActionType['class'].eq(1), # диагностика
                                             tableActionType['serviceType'].eq(10), # лаб.исследование
                                             tableEvent['deleted'].eq(0),
                                             lisCond,
                                             tableExport['id'].isNull()
                                            ]),
                                 tableAction['id'].name()
                               )


def selectActionIdListByIbm(equipmentIdList, systemId, exportIbm, localLab):
    db = QtGui.qApp.db
    tableAction = db.table('Action')
    tableActionType = db.table('ActionType')
    tableActionPropertyType = db.table('ActionPropertyType')
    tableEquipmentTest = db.table('rbEquipment_Test')
    tableEvent = db.table('Event')
    tableExport = db.table('Action_Export')
    tableProbe = db.table('Probe')

    table = tableAction
    table = table.innerJoin( tableActionType, tableActionType['id'].eq( tableAction['actionType_id'] ))
    table = table.innerJoin( tableActionPropertyType, db.joinAnd([
                                                                    tableActionPropertyType['actionType_id'].eq(tableAction['actionType_id']),
                                                                    tableActionPropertyType['deleted'].eq(0)
                                                                 ])
                           )
    table = table.innerJoin( tableEquipmentTest,      tableEquipmentTest['test_id'].eq( tableActionPropertyType['test_id'] ))
    table = table.innerJoin( tableEvent,              tableEvent['id'].eq( tableAction['event_id'] ))
    table = table.leftJoin (tableProbe,               tableProbe['takenTissueJournal_id'].eq(tableAction['takenTissueJournal_id']))
    table = table.leftJoin(tableExport, db.joinAnd([
                                                    tableExport['master_id'].eq(tableAction['id']),
                                                    tableExport['system_id'].eq(systemId)
                                                   ])
                          )
    if localLab:
        lisCond = db.joinAnd(['IFNULL(Action.org_id, Event.org_id) = %d' % QtGui.qApp.currentOrgId(),
                              tableEquipmentTest['equipment_id'].inlist(equipmentIdList),
                              db.joinOr([ tableProbe['id'].isNull(),
                                                         tableProbe['equipment_id'].inlist(equipmentIdList)
                                                       ]
                                                      ),
                             ])
    else:
        lisCond = db.joinAnd([tableEvent['srcNumber'].isNotNull(), tableAction['externalId'].isNotNull()])
    return db.getDistinctIdList( table,
                                 tableAction['id'],
                                 db.joinAnd([
                                             tableAction['status'].eq(CActionStatus.finished),
                                             tableAction['deleted'].eq(0),
                                             tableProbe['externalId'].eq(exportIbm),
                                             tableActionType['class'].eq(1), # диагностика
                                             tableActionType['serviceType'].eq(10), # лаб.исследование
                                             tableEvent['deleted'].eq(0),
                                             lisCond
                                            ]),
                                 tableAction['id'].name()
                               )


def selectActionIdListWithoutProbes(equipmentIdList, systemId, days, localLab):
    db = QtGui.qApp.db
    tableAction = db.table('Action')
    tableActionType = db.table('ActionType')
    tableActionPropertyType = db.table('ActionPropertyType')
    tableEquipmentTest = db.table('rbEquipment_Test')
    tableEvent = db.table('Event')
    tableExport = db.table('Action_Export')
    tableProbe = db.table('Probe')

    table = tableAction
    table = table.innerJoin( tableActionType, tableActionType['id'].eq( tableAction['actionType_id'] ))
    table = table.innerJoin( tableActionPropertyType, db.joinAnd([
                                                                    tableActionPropertyType['actionType_id'].eq(tableAction['actionType_id']),
                                                                    tableActionPropertyType['deleted'].eq(0)
                                                                 ])
                           )
    table = table.innerJoin( tableEquipmentTest,      tableEquipmentTest['test_id'].eq( tableActionPropertyType['test_id'] ))
    table = table.innerJoin( tableEvent,              tableEvent['id'].eq( tableAction['event_id'] ))
    table = table.leftJoin (tableProbe,               tableProbe['takenTissueJournal_id'].eq(tableAction['takenTissueJournal_id']))
    table = table.leftJoin(tableExport, db.joinAnd([
                                                    tableExport['master_id'].eq(tableAction['id']),
                                                    tableExport['system_id'].eq(systemId)
                                                   ])
                          )
    return db.getDistinctIdList( table,
                                 tableAction['id'],
                                 db.joinAnd([
                                             tableAction['status'].eq(CActionStatus.finished),
                                             tableAction['deleted'].eq(0),
                                             tableAction['endDate'].ge(QDateTime.currentDateTime().addDays(-days)), # совсем старые не берём
                                             tableActionType['class'].eq(1), # диагностика
                                             tableActionType['serviceType'].eq(10), # лаб.исследование
                                             tableEvent['deleted'].eq(0),
                                             tableExport['id'].isNull()
                                            ]),
                                 tableAction['id'].name()
                               )

def selectActionIdListKK(systemId, days):
    db = QtGui.qApp.db
    tableAction = db.table('Action')
    tableActionType = db.table('ActionType')
    tableExport = db.table('Action_Export')
    tableEvent = db.table('Event')
    tableEventType = db.table('EventType')
    tableRbEventTypePurpose = db.table('rbEventTypePurpose')

    table = tableAction.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
    table = table.leftJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
    table = table.leftJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
    table = table.leftJoin(tableRbEventTypePurpose, tableEventType['purpose_id'].eq(tableRbEventTypePurpose['id']))
    table = table.leftJoin(tableExport, db.joinAnd([tableExport['master_id'].eq(tableAction['id']), tableExport['system_id'].eq(systemId)]))
    return db.getDistinctIdList(table,
                                tableAction['id'],
                                db.joinAnd([tableActionType['deleted'].eq(0),
                                    tableActionType['class'].eq(1),  # диагностика
                                    tableActionType['flatCode'].like('s_lab%'),
                                    tableActionType['serviceType'].eq(10),  # лаб.исследование
                                    tableAction['deleted'].eq(0),
                                    tableEventType['context'].notlike(u'inspection%'),
                                    tableEventType['context'].notlike(u'relatedAction%'),
                                    tableRbEventTypePurpose['code'].ne(u'0'),
                                    tableAction['status'].eq(CActionStatus.finished),
                                    tableAction['endDate'].ge(QDateTime.currentDateTime().addDays(-days)),  # совсем старые не берём
                                    db.joinOr([tableExport['id'].isNull(),
                                               db.joinAnd([tableExport['success'].eq(0),
                                                           tableExport['dateTime'].lt(tableAction['modifyDatetime'])])])]),
                                tableAction['id'].name()
                                )

def getMapTestIdToTestCodeKK():
    db = QtGui.qApp.db
    tableTest = db.table('rbTest')
    tableGroup1 = db.table('rbTestGroup').alias('group1')
    tableGroup2 = db.table('rbTestGroup').alias('group2')
    table = tableTest.leftJoin(tableGroup1, tableGroup1['id'].eq(tableTest['testGroup_id']))
    table = table.leftJoin(tableGroup2, tableGroup2['id'].eq(tableGroup1['group_id']))
    records = db.getRecordList(table,
                               [tableTest['id'], tableTest['federalCode']],
                               tableGroup2['name'].eq(u'СОЦ-Лаборатория'),
                              )
    result = {}
    for record in records:
        code   = forceString(record.value('federalCode'))
        testId = forceRef(record.value('id'))
        result[testId] = code
    return result


def extractResultsEtc(mapTestIdToCode, actionId):
    testResults = []
    testCodesSet = set()
    QtGui.qApp.userSpecialityId = None
    action = CAction.getActionById(actionId)
    record = action.getRecord()
    personId = forceRef(record.value('person_id'))
    if not personId:
        personId = forceRef(record.value('setPerson_id'))
    eventId = action.getEventId()
    nomenclativeServiceId = action.getType().nomenclativeServiceId
    modifyDatetime = record.value('modifyDatetime')

    for prop in action.getProperties():
        propType = prop.type()
        if propType.testId:
            testCode = mapTestIdToCode.get(propType.testId)
            if testCode and testCode not in testCodesSet and prop.getValue():
                testResults.append(CResultDto(datetime = forceDateTime(record.value('endDate')),
                                              personId = personId,
                                              testCode = testCode,
                                              value    = prop.getValue(),
                                              unitId   = prop.getUnitId(),
                                              norm     = parseNorm(prop.getNorm()),
                                              evaluation = prop.getEvaluation(),
                                              actionId = actionId,
                                              propName = propType.name,
                                             )
                                  )
                testCodesSet.add(testCode)

    return testResults, eventId, nomenclativeServiceId, modifyDatetime


def parseNorm(norm):
# регулярное выражение: пара чисел с плав.точкой через минус
# впрочем, одно из чисел может отсутствовать
    f = r'([-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?|)'
    s = r'^\s*' + f + r'\s*-\s*' + f + r'\s*$'
    x = re.match(s, norm)
    if x:
        groups = x.groups()
        return ( float(groups[0]) if groups[0] else None,
                 float(groups[1]) if groups[1] else None
               )
    return (None, None)


def markActionAsExported(systemId, actionId, modifyDatetime, externalId = None):
    db = QtGui.qApp.db
    table = db.table('Action_Export')
    record = table.newRecord()
    record.setValue('master_id',      actionId)
    record.setValue('masterDatetime', modifyDatetime)
    record.setValue('system_id',      systemId)
    record.setValue('success',        True)
    record.setValue('dateTime',       QDateTime.currentDateTime())
    if externalId:
        record.setValue('externalId', externalId)
    db.insertRecord(table, record)


CResultDto = namedtuple('CResultDto',
                          ('datetime',
                           'personId',
                           'testCode',
                           'value',
                           'unitId',
                           'norm',
                           'evaluation',
                           'actionId',
                           'propName',
                          )
                        )
