# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2016 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

import isodate
import json
import uuid
from collections import namedtuple

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QDateTime, QEventLoop

from library.Utils import forceRef, forceString, forceDate, forceDateTime, forceDouble, toVariant
from library.Identification import getIdentification, getIdentificationEx
from Registry.Utils import getClientInfo
from Orgs.Utils             import getOrgStructureIdentification

from Exchange.FHIRClient import client

#from Exchange.FHIRClient.models.address          import Address
from Exchange.FHIRClient.models.bundle           import Bundle, BundleEntry, BundleEntryTransaction
from Exchange.FHIRClient.models.codeableconcept  import CodeableConcept
from Exchange.FHIRClient.models.coding           import Coding
from Exchange.FHIRClient.models.condition        import Condition
from Exchange.FHIRClient.models.coverage         import Coverage
from Exchange.FHIRClient.models.diagnosticorder  import DiagnosticOrder, DiagnosticOrderItem
from Exchange.FHIRClient.models.diagnosticreport import DiagnosticReport
from Exchange.FHIRClient.models.encounter        import Encounter
from Exchange.FHIRClient.models.extension        import Extension
from Exchange.FHIRClient.models.fhirdate         import FHIRDate
from Exchange.FHIRClient.models.fhirreference    import FHIRReference
from Exchange.FHIRClient.models.humanname        import HumanName
from Exchange.FHIRClient.models.identifier       import Identifier
from Exchange.FHIRClient.models.meta             import Meta
from Exchange.FHIRClient.models.observation      import Observation, ObservationReferenceRange
from Exchange.FHIRClient.models.order            import Order, OrderWhen
from Exchange.FHIRClient.models.orderresponse    import OrderResponse
from Exchange.FHIRClient.models.organization     import Organization
from Exchange.FHIRClient.models.patient          import Patient
from Exchange.FHIRClient.models.period           import Period
from Exchange.FHIRClient.models.practitioner     import Practitioner, PractitionerPractitionerRole
from Exchange.FHIRClient.models.specimen         import Specimen, SpecimenCollection, SpecimenContainer
from Exchange.FHIRClient.models.quantity         import Quantity
from Exchange.FHIRClient.models.attachment       import Attachment

__all__ = ( 'sendOrdersOverFHIR',
            'sendResultsOverFHIR',
            'pickupResultsOverFHIR',
            'sendLocalResultsOverFHIR'
          )


# обнаружено, что разные протоколы могут предусматривать разные
# способы группировки проб по заданиям.
# поэтому мы должны самостоятельно группировать пробы в задания
def sendOrdersOverFHIR(widget, equipmentInterface, clientInfo, probeIdList, probeSaver=None):
    opts = json.loads(equipmentInterface.address)
    orgId = QtGui.qApp.currentOrgId()
    interfaceObject = CFHIRExchange(opts, orgId)

    orderList = selectFHIROrders(probeIdList)
    for order in orderList:
        if probeSaver:
            probeSaver.clear()
        identifier = interfaceObject.sendOrderOverFHIR(clientInfo, order)
        if probeSaver:
            for probeId in order.probeIdSet:
                probeSaver.append(probeId)
            probeSaver.save(identifier)
    return bool(orderList)
    
    
def sendResultsOverFHIR(equipmentInterface, actionIdList):
    opts = json.loads(equipmentInterface)
    orgId = QtGui.qApp.currentOrgId()
    interfaceObject = CFHIRExchange(opts, orgId)
    for actionId in actionIdList:
        try:
            interfaceObject.sendResultOverFHIR(actionId)
        except Exception:
            pass
    
    return bool(actionIdList)


def pickupResultsOverFHIR(widget, equipmentInterface, probeIdList):
    db = QtGui.qApp.db
    opts = json.loads(equipmentInterface.address)
    orgId = QtGui.qApp.currentOrgId()
    interfaceObject = CFHIRExchange(opts, orgId)
    tableProbe = db.table('Probe')
    cond = [ tableProbe['status'].eq(6),  # Передано в ЛИС
             tableProbe['equipment_id'].eq(equipmentInterface.id), # и ЛИС тот самый
             tableProbe['exportName'].ne(''), # exportName заполнен
             tableProbe['exportDatetime'].ge(QDateTime.currentDateTime().addDays(-7)), # прошло не более недели с заказа
             tableProbe['id'].inlist(probeIdList) if probeIdList else '1'
           ]
    recordList = db.getRecordList(tableProbe,
                                  [ 'exportName' ],
                                  cond
                                 )
    setOfPrecessedOrderIds = set()
    for record in recordList:
        fhirOrderId = forceString(record.value('exportName'))
        if fhirOrderId not in setOfPrecessedOrderIds:
            if widget:
                QtGui.qApp.processEvents(QEventLoop.ExcludeUserInputEvents)
            fhirResult = interfaceObject.requestResultOverFHIR(fhirOrderId)
            if fhirResult.completed:
                fhirResult.storeToProbes(equipmentInterface.id)
            setOfPrecessedOrderIds.add(fhirOrderId)


def sendLocalResultsOverFHIR(equipmentInterface, clientInfo, serviceId, results):
    opts = json.loads(equipmentInterface.address)
    orgId = QtGui.qApp.currentOrgId()
    interfaceObject = CFHIRExchange(opts, orgId)
    return interfaceObject.sendLocalResultsOverFHIR(clientInfo, serviceId, results)


class COrderDto:
    u'Заказ, состоит из событий'
    def __init__(self):
        self.mapEventIdtoEvent = {}
        self.probeIdSet = set([])


    def getEventList(self):
        return self.mapEventIdtoEvent.values()


    def addProbe(self,
                 eventId,
                 eventTypeId,
                 eventPurposeId,
                 actionId,
                 actionTypeId,
                 directionDatetime,
                 orgStructureId,
                 setPersonId,
                 MKB,
                 serviceId,
                 takenTissueJournalId,
                 takenDatetime,
                 externalId,
                 specimenTypeId,
                 containerTypeId,
                 probeId
                ):
        if not externalId:
            raise Exception(u'В пробe Probe.id=%d пустой externalId' % probeId )
        if not specimenTypeId:
            raise Exception(u'В пробe Probe.id=%d пустой specimenType_id' % probeId)
        if not containerTypeId:
            raise Exception(u'В пробe Probe.id=%d пустой containerType_id' % probeId)
        if not takenTissueJournalId:
            raise Exception(u'В пробe Probe.id=%d пустой takenTissueJournal_id' % probeId)
        if not actionId:
            raise Exception(u'Для TakenTissueJournal.id=%d упомянутого в Probe.id=%d не найдено ни одного действия' % (takenTissueJournalId, probeId))
        if not actionTypeId:
            raise Exception(u'В действии Action.id=%d упомянутого в Probe.id=%d указан пустой actionType_id' % (actionId, probeId))
        if not serviceId:
            raise Exception(u'В типе действия ActionType.id=%d упомянутого в пробе Probe.id=%d не задана номенклатурная услуга' % (actionTypeId, probeId))
        if not setPersonId:
            raise Exception(u'В действии Action.id=%d упомянутого в пробе Probe.id=%d пустой setPerson_id' % (actionId, probeId))

        self.probeIdSet.add(probeId)

        event = self.mapEventIdtoEvent.get(eventId)
        if event is None:
            event = self.mapEventIdtoEvent[eventId] = CEventDto(eventId, eventTypeId, eventPurposeId)

        action = event.getAction(actionId,
                                 actionTypeId,
                                 directionDatetime,
                                 orgStructureId,
                                 setPersonId,
                                 MKB,
                                 serviceId)
        action.addSpecimen(specimenTypeId,
                           containerTypeId,
                           externalId,
                           takenTissueJournalId,
                           takenDatetime,
                           probeId)


class CEventDto:
    u'описание события, во fhir превращается в encounter'
    def __init__(self, eventId, eventTypeId, eventPurposeId):
        self.eventId = eventId
        self.eventTypeId = eventTypeId
        self.eventPurposeId = eventPurposeId
        self.mapActionIdToAction = {}


    def getActionList(self):
        return self.mapActionIdToAction.values()


    def getAction(self,
                  actionId,
                  actionTypeId,
                  directionDatetime,
                  orgStructureId,
                  setPersonId,
                  diagnosis,
                  serviceId):
        action = self.mapActionIdToAction.get(actionId)
        if action is None:
            action = self.mapActionIdToAction[actionId] = CActionDto(actionId,
                                                                      actionTypeId,
                                                                      directionDatetime,
                                                                      orgStructureId,
                                                                      setPersonId,
                                                                      diagnosis,
                                                                      serviceId)
        return action


class CActionDto:
    u'описание события, во fhir совокупность CActionDto превращается в diagnosticOrder'
    def  __init__(self,
                  actionId,
                  actionTypeId,
                  directionDatetime,
                  orgStructureId,
                  setPersonId,
                  diagnosis,
                  serviceId):
        self.actionId = actionId
        self.actionTypeId = actionTypeId
        self.directionDatetime = directionDatetime
        self.orgStructureId = orgStructureId
        self.setPersonId = setPersonId
        self.diagnosis = diagnosis
        self.serviceId = serviceId
        self.specimenList = []


    def addSpecimen(self, specimenTypeId,
                          containerTypeId,
                          externalId,
                          takenTissueJournalId,
                          takenDatetime,
                          probeId):
        self.specimenList.append(CSpecimenDto(specimenTypeId,
                                              containerTypeId,
                                              externalId,
                                              takenTissueJournalId,
                                              takenDatetime,
                                              probeId))


    def getSpecimenList(self):
        return self.specimenList


CSpecimenDto = namedtuple('CSpecimenDto',
                          ('specimenTypeId',
                           'containerTypeId',
                           'externalId',
                           'takenTissueJournalId',
                           'takenDatetime',
                           'probeId',
                          )
                         )


class CFHIRResultValue:
    def __init__(self, code):
        self.code  = code
        self.value = None
        self.unit  = None
        self.referenceRange = None


class CFHIRServiceResult:
    def __init__(self, code, issued, conclusion):
        self.code = code
        self.issued = issued
        self.conclusion = conclusion
        self.values = []


class CFHIRResult:
    def __init__(self, fhirOrderId):
        self.fhirOrderId = fhirOrderId
        self.probeIdSet = set()
        self.completed  = False
        self.serviceResults = []


    def addProbeId(self, probeId):
        self.probeIdSet.add(probeId)


    def addServiceResult(self, serviceResult):
        self.serviceResults.append(serviceResult)


    @staticmethod
    def getMapTestCodeToTestId(eqipmentId):
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
            result[code] = testId
        return result


    @staticmethod
    def determineTypeName(value):
        return 'String' if isinstance(value, basestring) else 'Double'


    @staticmethod
    def updateOrAddProbe(eqipmentId, exportName, testId, value, unitName, unitId, referenceRangeAsStr):
        db = QtGui.qApp.db

        tableProbe = db.table('Probe')
        probeIdList = db.getIdList(tableProbe,
                                   'id',
                                   db.joinAnd([tableProbe['equipment_id'].eq(eqipmentId),
                                               tableProbe['exportName'].eq(exportName),
                                               tableProbe['test_id'].eq(testId),
                                               tableProbe['status'].eq(6)
                                              ]
                                             )
                                  )
        if probeIdList:
            for probeId in probeIdList:
                record = tableProbe.newRecord(['id', 'resultIndex', 'result1', 'typeName', 'unit_id', 'externalUnit', 'norm', 'externalNorm'])
                record.setValue('id', probeId)
                record.setValue('resultIndex', 1)
                record.setValue('result1', value)
                record.setValue('typeName', CFHIRResult.determineTypeName(value))
                record.setValue('unit_id', unitId)
                record.setValue('externalUnit', unitName)
                record.setValue('norm', referenceRangeAsStr)
                record.setValue('externalNorm', referenceRangeAsStr)
                db.updateRecord(tableProbe, record)
        else:
            takenTissueJournalIdList = db.getDistinctIdList(tableProbe,
                                                            'takenTissueJournal_id',
                                                            db.joinAnd([tableProbe['equipment_id'].eq(eqipmentId),
                                                                        tableProbe['exportName'].eq(exportName),
                                                                       ]
                                                                      )
                                                           )

            record = tableProbe.newRecord()
            record.setValue('equipment_id', eqipmentId)
            record.setValue('status',       7)
            record.setValue('test_id',      testId)
            record.setValue('workTest_id',  testId)
            record.setValue('takenTissueJournal_id', takenTissueJournalIdList[0])
            record.setValue('resultIndex', 1)
            record.setValue('result1', value)
            record.setValue('typeName', CFHIRResult.determineTypeName(value))
            record.setValue('unit_id', unitId)
            record.setValue('externalUnit', unitName)
            record.setValue('norm', referenceRangeAsStr)
            record.setValue('externalNorm', referenceRangeAsStr)
            record.setValue('exportName', exportName)
            db.insertRecord(tableProbe, record)


    @staticmethod
    def getUnitId(unitCode):
        if unitCode:
            db = QtGui.qApp.db
            tableUnit = db.table('rbUnit')
            result = forceRef(db.translate(tableUnit, 'code', unitCode, 'id'))
            if result is None:
                record = tableUnit.newRecord()
                record.setValue('code', unitCode)
                record.setValue('name', unitCode)
                result = db.insertRecord(tableUnit, record)
            return result
        return None


    @staticmethod
    def getReferenceRangeAsStr(referenceRange):
        if referenceRange:
            low, high = referenceRange
            if low is None:
                low = 0.0
            if high is None:
                high = 999.99
            return str(low) + ' - ' + str(high)
        else:
            return ''


    @staticmethod
    def markProbesAsAccepted(eqipmentId, exportName):
        db = QtGui.qApp.db
        tableProbe = db.table('Probe')
        record = tableProbe.newRecord(['status', 'importDatetime', 'importPerson_id'])
        record.setValue('status', 7)
        record.setValue('importDatetime',  QDateTime.currentDateTime())
        record.setValue('importPerson_id', QtGui.qApp.userId)

        cond = db.joinAnd([tableProbe['equipment_id'].eq(eqipmentId),
                           tableProbe['exportName'].eq(exportName),
                          ]
                         )

        db.updateRecords(tableProbe, record,  cond)


    def storeToProbes(self, eqipmentId):
        freeResuts = {}
        mapTestCodeToTestId = self.getMapTestCodeToTestId(eqipmentId)
        db = QtGui.qApp.db
        db.transaction()
        try:
            for serviceResult in self.serviceResults:
                for value in serviceResult.values:
                    testId = mapTestCodeToTestId.get(value.code)
                    if testId:
                        unitId = self.getUnitId(value.unit)
                        referenceRangeAsStr = self.getReferenceRangeAsStr(value.referenceRange)
                        self.updateOrAddProbe(eqipmentId, self.fhirOrderId, testId, value.value, value.unit, unitId, referenceRangeAsStr)
                    else:
                        freeResuts[value.code] = { 'value' : value.value,
                                                   'unit'  : value.unit,
                                                   'referenceRange' : value.referenceRange
                                                 }
            if freeResuts:
                testId = mapTestCodeToTestId.get('blank')
                if testId:
                    self.updateOrAddProbe(eqipmentId, self.fhirOrderId, testId, json.dumps(freeResuts), '', None, '')

            self.markProbesAsAccepted(eqipmentId, self.fhirOrderId)
            db.commit()
        except:
            db.rollback()
            raise


def selectFHIROrders(probeIdList):
    db = QtGui.qApp.db
    tableProbe = db.table('Probe')
    tableTakenTissueJournal = db.table('TakenTissueJournal')
    tableAction = db.table('Action')
    tableActionType = db.table('ActionType')
    tableActionPropertyType = db.table('ActionPropertyType')
    tablePerson = db.table('Person')
    tableDiagnosis = db.table('Diagnosis')
    tableEvent = db.table('Event')
    tableEventType = db.table('EventType')

    table = tableProbe
    table = table.leftJoin(tableTakenTissueJournal, tableTakenTissueJournal['id'].eq(tableProbe['takenTissueJournal_id']))
    table = table.innerJoin(tableAction,     tableAction['takenTissueJournal_id'].eq(tableProbe['takenTissueJournal_id']))
    table = table.innerJoin(tableEvent,      tableEvent['id'].eq(tableAction['event_id']))
    table = table.innerJoin(tableEventType,  tableEventType['id'].eq(tableEvent['eventType_id']))
    table = table.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
    table = table.innerJoin(tableActionPropertyType, db.joinAnd([ tableActionPropertyType['actionType_id'].eq(tableActionType['id']),
                                                                  tableActionPropertyType['test_id'].eq(tableProbe['test_id']),
                                                                  tableActionPropertyType['deleted'].eq(0)
                                                                ]
                                                               )
                           )
    table = table.leftJoin(tablePerson,     tablePerson['id'].eq(tableAction['setPerson_id']))
    table = table.leftJoin(tableDiagnosis,   'Diagnosis.id = getEventDiagnosis(Action.event_id)')

    cond = [ tableProbe['id'].inlist(probeIdList)
           ]

    recordList = db.getRecordList(table,
                                  [ tableProbe['id'].alias('probe_id'),
                                    tableProbe['externalId'],
                                    tableProbe['takenTissueJournal_id'],
                                    tableProbe['specimenType_id'],
                                    tableProbe['containerType_id'],
                                    tableTakenTissueJournal['datetimeTaken'],
                                    tableAction['id'].alias('action_id'),
                                    tableAction['actionType_id'],
                                    tableActionType['nomenclativeService_id'].alias('service_id'),
                                    tableAction['directionDate'].alias('directionDatetime'),
                                    tableAction['event_id'],
                                    tableEvent['eventType_id'],
                                    tableEventType['purpose_id'].alias('eventPurpose_id'),
                                    tablePerson['orgStructure_id'],
                                    tableAction['setPerson_id'],
                                    tableAction['MKB'].alias('actionMKB'),
                                    tableDiagnosis['MKB'].alias('eventMKB'),
                                  ],
                                  cond
                                 )

    orderDict = {}
    for record in recordList:
        probeId              = forceRef(record.value('probe_id'))
        externalId           = forceString(record.value('externalId'))
        takenTissueJournalId = forceRef(record.value('takenTissueJournal_id'))
        specimenTypeId       = forceRef(record.value('specimenType_id'))
        containerTypeId      = forceRef(record.value('containerType_id'))
        takenDatetime        = forceDateTime(record.value('datetimeTaken'))
        actionId             = forceRef(record.value('action_id'))
        actionTypeId         = forceRef(record.value('actionType_id'))
        serviceId            = forceRef(record.value('service_id'))
        directionDatetime    = forceDateTime(record.value('directionDatetime'))
        eventId              = forceRef(record.value('event_id'))
        eventTypeId          = forceRef(record.value('eventType_id'))
        eventPurposeId       = forceRef(record.value('eventPurpose_id'))
        orgStructureId       = forceRef(record.value('orgStructure_id'))
        setPersonId          = forceRef(record.value('setPerson_id'))
        MKB                  = forceString(record.value('actionMKB')) or forceString(record.value('eventMKB')) or 'Z00'
#        key = (takenTissueJournalId, externalId)
        orderKey = takenTissueJournalId
        order = orderDict.get(orderKey)
        if order is None:
            orderDict[orderKey] = order = COrderDto()
        order.addProbe(eventId,
                       eventTypeId,
                       eventPurposeId,
                       actionId,
                       actionTypeId,
                       directionDatetime,
                       orgStructureId,
                       setPersonId,
                       MKB,
                       serviceId,
                       takenTissueJournalId,
                       takenDatetime,
                       externalId,
                       specimenTypeId,
                       containerTypeId,
                       probeId
                      )
    return orderDict.values()


def dateToFHIRDate(date):
    result = FHIRDate()
    if date:
        if isinstance(date, QDateTime):
            date = date.date()
        pd = date.toPyDate()
        result.date = pd
    return result


def dateTimeToFHIRDate(dateTime):
    result = FHIRDate()
    if dateTime:
#        pdt = dateTime.toPyDateTime().replace(microsecond=0)
        pdt = dateTime.toPyDateTime()
        if pdt.tzinfo is None:
            pdt = pdt.replace(tzinfo=isodate.LOCAL)
        result.date = pdt
    return result


class CFHIRExchange:
    # SAMSON           = 'urn:oid:1.2.643.2.69.1.2.5'  # идентификатор САМСОНа в сервисе #Переехало в GlobalPreferences.Code == Netrika.MIS_OID
    orgUrn           = 'urn:oid:1.2.643.2.69.1.1.1.64'   # кодификатор организаций
    documentTypeUrn  = 'urn:oid:1.2.643.5.1.34'          # паспорт или свид. о рождении
    snilsUrn         = 'urn:oid:1.2.643.3.9'             # СНИЛС
    hicRegistryUrn   = 'urn:oid:1.2.643.5.1.13.2.1.1.635'# Реестр СМО (ФФОМС)
    policyKindUrn    = 'urn:oid:1.2.643.2.69.1.1.1.48'   # Типы/виды полисов
    specialityUrn    = 'urn:oid:1.2.643.5.1.13.2.1.1.181'# Специальности
    roleUrn          = 'urn:oid:1.2.643.5.1.13.2.1.1.607'# Роли (Должности)
    reasonUrn        = 'urn:oid:1.2.643.2.69.1.1.1.19'   # Назначение события
    serviceUrn       = 'urn:oid:1.2.643.2.69.1.1.1.31'   # Услуги
    specimenTypeUrn  = 'urn:oid:1.2.643.2.69.1.1.1.33'   # типы образцов
    containerTypeUrn = 'urn:oid:1.2.643.2.69.1.1.1.34'   # типы контейнеров

    conditionUrn     = 'urn:oid:1.2.643.2.69.1.1.1.36'   # типы Condition
    conditionCode    = 'diagnosis'
    conditionVersion = '1'

    loincUrn         = 'urn:oid:1.2.643.2.69.1.1.1.1'
    loincVersion     = ''
    ICDUrn           = 'urn:oid:1.2.643.2.69.1.1.1.2'    # Коды диагнозов по МКБ
    ICDVersion       = '1'


    def __init__(self, opts, orgId):
        url           = opts['url']
        authorization = opts['authorization']
        target        = opts.get('target', None)
        self.SAMSON = 'urn:oid:' + forceString(
            QtGui.qApp.db.translate('GlobalPreferences', 'code', 'Netrika.MIS_OID', 'value'))
        self.misCode  = opts.get('misCode', self.SAMSON)
        self.orgShortCode = forceString(QtGui.qApp.db.translate('Organisation', 'id', orgId, 'infisCode'))
        self.externalSystemId = forceRef(QtGui.qApp.db.translate('rbExternalSystem', 'code', 'N3.ODLI', 'id'))
        self.mapClientIdToPatientReference = {}
        self.mapClientIdToInfo = {}
        self.lab = None
        self.labReference = None
        self.orgCode  = getIdentification('Organisation', orgId, self.orgUrn)

        self.org = self.createOrganization(self.orgCode)
        if target:
            self.lab = self.createOrganization(target)

        settings = { 'api_base': url,
                     'app_id'  : 'samson/0.1',
                     'headers' : { 'Authorization' : authorization}
                   }

        self.smart = client.FHIRClient(settings=settings)
        self.smart.prepare()

        self.orgReference = self.createReference(self.org)
        if self.lab:
            self.labReference = self.createReference(self.lab)


    def createReference(self, resource):
        if resource.id is None:
            resp = resource.create(self.smart.server)
            resource.update_with_json(resp)
        reference = FHIRReference()
        reference.reference =  '%s/%s' % (resource.resource_name, resource.id)
        return reference
        
    def createEmptyReference(self, code=''):
        reference = FHIRReference()
        reference.reference = code
        return reference
        
    
    def createBundleReference(self, resource):
        if resource.id is None:
            resource.id = str(uuid.uuid4())
            resource.is_bundle_local = True
        if getattr(resource, 'is_bundle_local', False):
            reference = FHIRReference()
            reference.reference = resource.id
            return reference
        else:
            return self.createReference(resource)


    def createIdentifier(self, system, value, assigner=None):
        identifier = Identifier()
        identifier.system = system
        identifier.value  = value
        identifier.assigner = assigner
        return identifier


    def createMisIdentifier(self, value):
        identifier = Identifier()
        identifier.system = self.misCode
        identifier.value  = '%s:%s' % (self.orgShortCode, value)
        identifier.assigner = self.orgReference
        return identifier


    def createCoding(self, system, code, version):
        coding = Coding()
        coding.system=system
        coding.code=code
        #coding.version=version
        return coding


    def createCodeableConcept(self, system, code, version):
        codeableConcept = CodeableConcept()
        codeableConcept.coding = [ self.createCoding(system,
                                                     code,
                                                     version=version
                                                    )
                                 ]
        return codeableConcept


    def createOrganization(self, fhirId):
        org = Organization()
        org.id = fhirId
        return org


    def createOrgStructureReference(self, orgStructureId):
        if orgStructureId:
            fhirId = getOrgStructureIdentification(orgStructureId, self.orgUrn)
            return self.createReference(self.createOrganization(fhirId))
        else:
            return self.orgReference


    def searchByIdentifier(self, cls, identifier):
        identifierStr = ('%s|%s' % (identifier.system,identifier.value)).encode('utf8')
        searchObject = cls.where({'identifier': identifierStr})
        searchBundle = searchObject.perform(self.smart.server)
        return searchBundle


    def createPatient(self, clientInfo, isBundle=False):
       # db = QtGui.qApp.db
        mainId = self.createMisIdentifier(clientInfo.id)
        searchBundle = self.searchByIdentifier(Patient, mainId)
        if searchBundle.entry:
            patient = searchBundle.entry[-1].resource
        else:
            patient = Patient()
            
        patient.active = True
        name = HumanName()
        name.family = [ clientInfo.lastName, ]
        name.given  = [ clientInfo.firstName, clientInfo.patrName, ]
        patient.name = [ name ]
        patient.name[0].use    = 'official'
        patient.gender = {  1: 'male', 2:'female' }.get(clientInfo.sexCode, 'undefined')
        patient.birthDate = dateToFHIRDate(clientInfo.birthDate)
       
        #адрес  пока не будем выгружать, т.к. он не обязателен
#        address = clientInfo.locAddress
#        if address:
#            patient.address = [ Address( { 'use' : 'home',
#                                           'text': address
#                                         }
#                                       )
#                              ]
        if not isBundle:
            if patient.id:
                resp = patient.update(self.smart.server)
            else:
                resp = patient.create(self.smart.server)
                patient.update_with_json(resp)
            patient.update_with_json(resp)
        else:
            patient.identifier = [ mainId,  # идентификатор в МИС
        
                     ]
            if clientInfo.documentRecord:
                serial = forceString(clientInfo.documentRecord.value('serial'))
                number = forceString(clientInfo.documentRecord.value('number'))
                if serial and number:
                    document = ('%s:%s' % (serial, number)).replace(' ','')
                    patient.identifier.append(self.createIdentifier(self.documentTypeUrn, document))
            if clientInfo.SNILS:
                SNILS = clientInfo.SNILS.replace('-', '').replace(' ', '')
                patient.identifier.append(self.createIdentifier(self.snilsUrn, SNILS))


    def createAnonimousPatient(self, clientInfo):
        mainId = self.createMisIdentifier(clientInfo.id)  # идентификатор в МИС
        patient = Patient()

        patient.active = True
        name = HumanName()
        name.use = 'anonymous'
        name.family = [u'Анонимный', ]
        name.given = [u'Анонимный', u'Анонимный', ]
        patient.name = [name]
        patient.gender = {1: 'male', 2: 'female'}.get(clientInfo.sexCode, 'undefined')
        patient.birthDate = dateToFHIRDate(clientInfo.birthDate)
        patient.identifier = [mainId, ]
        return patient

    def createCoverage(self, clientInfo, patientReference):
        record = clientInfo.compulsoryPolicyRecord
        if record is None:
            raise Exception(u'У пациента Client.id=%s нет полиса ОМС' % clientInfo.id)
        insurerId = forceRef(record.value('insurer_id'))
        serial    = forceString(record.value('serial'))
        number    = forceString(record.value('number'))
        begDate   = forceDate(record.value('begDate'))
        endDate   = forceDate(record.value('endDate'))
        if insurerId is None:
            raise Exception(u'У пациента Client.id=%s\n'
                            u'в полисе ОМС (серия:«%s», номер: «%s»)\n'
                            u'не указана страховая компания' % (clientInfo.id, serial, number))

#        policyKind_id
#        policyType_id
        insurerCode = getIdentification('Organisation', insurerId, self.hicRegistryUrn)
        mainId = self.createIdentifier('%s.%s' % (self.hicRegistryUrn, insurerCode),
                                       '%s:%s' % (serial, number)
                                      )
        searchBundle = self.searchByIdentifier(Coverage, mainId)
        if searchBundle.entry:
            for item in searchBundle.entry:
                if item.resource.subscriber.reference == patientReference.reference:
                    return item.resource

        coverage = Coverage()
        mainId.period = period = Period()
        if begDate:
            period.start = dateToFHIRDate(begDate)
        if endDate:
            period.end = dateToFHIRDate(endDate)
        coverage.identifier = [ mainId ]
        coverage.subscriber = patientReference
        coverage.type       = self.createCoding(self.policyKindUrn, '2', version='1') # тип/вид полиса
        resp = coverage.create(self.smart.server)
        coverage.update_with_json(resp)
        return coverage


    def createPractitioner(self, personId, isBundle=False):
        db = QtGui.qApp.db
        record = db.getRecord('Person',
                             ('lastName','firstName','patrName','post_id','speciality_id','orgStructure_id'),
                             personId
                             )
        lastName  = forceString(record.value('lastName'))
        firstName = forceString(record.value('firstName'))
        patrName  = forceString(record.value('patrName'))
        postId    = forceRef(record.value('post_id'))
        specialityId = forceRef(record.value('speciality_id'))
        orgStructureId = forceRef(record.value('orgStructure_id'))
        specialityCode, specialityVersion = getIdentificationEx('rbSpeciality',
                                                                specialityId,
                                                                self.specialityUrn
                                                               )
        postCode,       postVersion       = getIdentificationEx('rbPost',
                                                                postId,
                                                                self.roleUrn
                                                               )
        mainId = self.createMisIdentifier(personId)
        searchBundle = self.searchByIdentifier(Practitioner, mainId)
        if searchBundle.entry:
            practitioner = searchBundle.entry[-1].resource
        else:
            practitioner = Practitioner()
        name = name = HumanName()
        name.family = [ lastName, ]
        name.given  = [ firstName, patrName ]
        ppr =  PractitionerPractitionerRole()
        ppr.managingOrganization = self.createOrgStructureReference(orgStructureId)
        ppr.specialty = [ self.createCodeableConcept(self.specialityUrn,
                                                     specialityCode,
                                                     specialityVersion
                                                   )
                        ]
        ppr.role      = self.createCodeableConcept(self.roleUrn,
                                                   postCode,
                                                   postVersion
                                                  )
        practitionerRole = [ ppr ]
        if practitioner.name == name and practitioner.practitionerRole == practitionerRole:
            return practitioner
        practitioner.name = name
        practitioner.practitionerRole = practitionerRole
        
        if not isBundle:
            if practitioner.id:
                resp = practitioner.update(self.smart.server)
            else:
                practitioner.identifier  = [ mainId ]
                resp = practitioner.create(self.smart.server)
            practitioner.update_with_json(resp)
        else:
            practitioner.identifier  = [ mainId ]
        return practitioner


    def createCondition(self, patientReference, diagnosisCode):
        condition = Condition()
        condition.category = self.createCodeableConcept(self.conditionUrn,
                                                        self.conditionCode,
                                                        self.conditionVersion
                                                       )
        condition.clinicalStatus = 'confirmed' # 0.5.0
        #condition.clinicalStatus = 'working' # 1.0.2
        condition.code = self.createCodeableConcept(self.ICDUrn,
                                                    diagnosisCode,
                                                    self.ICDVersion
                                                   )
        condition.patient = patientReference
        return condition


    def createEncounter(self, patientReference, eventId, eventTypeId, eventPurposeId, orgStructureId, conditionList):
        encounter = Encounter()
        encounter.class_fhir = 'ambulatory'
        encounter.type       = [ self.createCodeableConcept('urn:oid:1.2.643.2.69.1.1.1.35', '2', version='1') ]
        # encounter.identifier = [ self.createMisIdentifier(eventId) ]
        # обходим "Повторное добавление случая обслуживания"
        encounter.identifier = [ self.createMisIdentifier(str(uuid.uuid1())) ]
        encounter.indication = [ self.createBundleReference(condition)
                                 for condition in conditionList
                               ]
        encounter.patient    = patientReference

        reasonCode, reasonVersion = getIdentificationEx('EventType',
                                                        eventTypeId,
                                                        self.reasonUrn,
                                                        False
                                                       )
        if reasonCode is None:
            reasonCode, reasonVersion = getIdentificationEx('rbEventTypePurpose',
                                                            eventPurposeId,
                                                            self.reasonUrn,
                                                            True
                                                           )

        encounter.reason     = [ self.createCodeableConcept(self.reasonUrn, reasonCode, reasonVersion) ]
        encounter.serviceProvider = self.createOrgStructureReference(orgStructureId)
        encounter.status     = 'in-progress'
        return encounter


    def createSpecimen(self,
                       patientReference,
                       specimenTypeId,
                       containerTypeId,
                       externalId,
                       takenDatetime,
                       probeId
                      ):
        specimenTypeCode, specimenTypeVersion = getIdentificationEx('rbSpecimenType',
                                                                    specimenTypeId,
                                                                    self.specimenTypeUrn
                                                                   )
        containerTypeCode, containerTypeVersion = getIdentificationEx('rbContainerType',
                                                                      containerTypeId,
                                                                      self.containerTypeUrn,
                                                                     )
        specimen = Specimen()
        specimen.identifier = [ self.createMisIdentifier(probeId) ]
        specimen.subject = patientReference
        specimen.type = self.createCodeableConcept(self.specimenTypeUrn,
                                                   specimenTypeCode,
                                                   specimenTypeVersion)

        specimen.collection = SpecimenCollection()
        # сервис по непонятным причинам не принимает дату со временем.
#        specimen.collection.collectedDateTime = dateToFHIRDate(takenDatetime.date())
        specimen.collection.collectedDateTime = dateTimeToFHIRDate(takenDatetime)
        specimen.container = [ SpecimenContainer() ]
        specimen.container[0].identifier = [ self.createIdentifier('urn:uuid:'+ self.lab.id,
                                                              externalId,
                                                              self.createReference(self.lab)
                                                             )
                                           ]
        specimen.container[0].type = self.createCodeableConcept(self.containerTypeUrn, containerTypeCode, containerTypeVersion)
        specimen._key = (specimenTypeCode, containerTypeCode, externalId)
        return specimen


    def createDiagnosticOrderItem(self,
                                  serviceCode,
                                  serviceVersion,
                                  financeCode,
                                  financeVersion,
                                  coverageReference
                                 ):
        diagnosticOrderItem  = DiagnosticOrderItem()
        diagnosticOrderItem.code = self.createCodeableConcept(self.serviceUrn,
                                                              serviceCode,
                                                              serviceVersion)

        e1 = Extension()
        e1.url = 'urn:oid:1.2.643.2.69.1.100.1'
        e1.valueCodeableConcept = self.createCodeableConcept('urn:oid:1.2.643.2.69.1.1.1.32',
                                                             financeCode,
                                                             financeVersion)

        e2 = Extension()
        e2.url = 'urn:oid:1.2.643.2.69.1.100.2'
        e2.valueReference = coverageReference

        diagnosticOrderItem.code.extension = [ e1, e2 ]
        return diagnosticOrderItem


    def createDiagnosticOrder(self,
                              patientReference,
                              coverageReference,
                              practitionerReference,
                              encounter,
                              observations,
                              serviceIdList,
                              specimenList):
        diagnosticOrder = DiagnosticOrder()
        diagnosticOrder.subject   = patientReference
        diagnosticOrder.status    = 'requested'
        diagnosticOrder.orderer   = practitionerReference
        diagnosticOrder.specimen  = [ self.createBundleReference(specimen) for specimen in specimenList ]
        diagnosticOrder.encounter = self.createBundleReference(encounter)
        diagnosticOrder.supportingInformation = encounter.indication
        diagnosticOrder.item = []
        serviceCodeSet = set(getIdentificationEx('rbService', serviceId, self.serviceUrn)
                             for serviceId in serviceIdList
                            )
        serviceCodeList = list(serviceCodeSet)
        serviceCodeList.sort()
        for serviceCode, serviceVersion in serviceCodeList:
            financeCode, financeVersion = '1', '1'
            item = self.createDiagnosticOrderItem(serviceCode,
                                                  serviceVersion,
                                                  financeCode,
                                                  financeVersion,
                                                  coverageReference
                                                 )
            diagnosticOrder.item.append(item)
        return diagnosticOrder


    def createOrder(self,
                    orderIdentifier,
                    directionDatetime,
                    patientReference,
                    practitionerReference,
                    diagnosticOrderList
                   ):
        order = Order()
        order.identifier = [ orderIdentifier ]
#        order.date = dateTimeToFHIRDate(directionDatetime)
        order.date = dateTimeToFHIRDate(QDateTime.currentDateTime())
        order.subject = patientReference
        order.source = practitionerReference
        order.target = self.labReference
        order.detail = [ self.createBundleReference(diagnosticOrder)
                         for diagnosticOrder in diagnosticOrderList
                       ]
        order.when = OrderWhen()
        order.when.code = self.createCodeableConcept('urn:oid:1.2.643.2.69.1.1.1.30', 'Routine', version='1')
        return order

        
    def createObservation(self,
                    patientReference,
                    practitionerReference, 
                    observationRecord
                   ):
        #Observation предназначен для передачи результата теста
        observation = Observation()
        #Код теста, для которого передается результат в Observation (региональный справочник тестов):
        #В параметре system указывается OID справочника в сервисе Терминологии (1.2.643.2.69.1.1.1.1),
        #В параметре version указывается версия справочника в сервисе Терминологии,
        #В параметре code указывается код значения из справочника
        observation.code = self.createCodeableConcept(self.urnLoinc, forceString(observationRecord.value('testCode')), version='1')
        #Комментарий к результату теста (пока хз откуда заполнять)
        #observation.comments = u"Комментарий к результату теста"
        #Дата-время результата теста
        observation.issued = dateTimeToFHIRDate(forceDateTime(observationRecord.value('issued')))
        #Статус ресурса (справочник FHIR. OID справочника в сервисе Терминологии: 1.2.643.2.69.1.1.1.47)
        observation.status = u"final"
        #Методика исследования:
        #В параметре system указывается OID передающей системы
        #В параметре code указывается наименование методики
        #(пока хз откуда заполнять)
        #observation.method = self.createCodeableConcept(self.SAMSON, u'Химический', version='1')
        #Ссылка. Соотнесение с врачом-исполнителем. Должен передаваться ресурс Practitioner в Bundle 
        #или указываться ссылка на существующий Practitioner
        observation.performer = practitionerReference
        #Результат теста. Единицы измерения. Результат теста. Числовой результат. Должно передаваться или valueQuantity или valueString
        strValue = forceString(observationRecord.value('strValue'))
        intValue = forceDouble(observationRecord.value('intValue'))
        if strValue:
            observation.valueString = strValue
        else:
            observation.valueQuantity = Quantity()
            observation.valueQuantity.value = intValue
            unitCode = forceString(observationRecord.value('unitCode'))
            observation.valueQuantity.units = unitCode
        #Рефферентные значения для полученного результата (с применением типа Quantity)
        #В параметре value указывается количественный показатель,
        #В параметре units - единица измерения
        referenceValue = forceString(observationRecord.value('norm'))
        observation.referenceRange = ObservationReferenceRange()
        if referenceValue:
            observation.referenceRange = ObservationReferenceRange()
            if strValue:
                observation.referenceRange.text = referenceValue
            else:
                parts = referenceValue.split('-')
                observation.referenceRange.low = Quantity()
                observation.referenceRange.low.value = forceDouble(parts[0].replace(',', '.'))
                observation.referenceRange.low.units = unitCode
                if len(parts) == 2:
                    observation.referenceRange.high = Quantity()
                    observation.referenceRange.high.value = forceDouble(parts[1].replace(',', '.'))
                    observation.referenceRange.high.units = unitCode
        else:
            observation.referenceRange.text = "-"
        return observation


    def createTransactionBundle(self, resources, StructureDefinition):
        result = Bundle()
        result.meta  = Meta( dict(profile = [ StructureDefinition ] ))
        result.type  = 'transaction'
        result.entry = []
        for resurce in resources:
            bundleEntry = BundleEntry()
            bundleEntry.transaction = BundleEntryTransaction()
            bundleEntry.transaction.method = 'POST'
            bundleEntry.transaction.url = resurce.resource_name
            bundleEntry.resource = resurce
            result.entry.append(bundleEntry)
        return result


    def createLisOrderBundle(self,
                             order,
                             orderIdentifier,
                             patientReference,
                             coverageReference
                            ):
        conditionList = []
        StructureDefinition = u'StructureDefinition/cd45a667-bde0-490f-b602-8d780acf4aa2'
        mapDiagnosisToCondition = {}
        encounter = None
        practitionerList = []
        mapPersonIdToPractitionerReference = {}
        directionDatetime = None

        mapSpecimenKeyToSpecimen = {}
        mapSpecimenKeyToActions = {}
        diagnosticOrderList = []

        for event in order.getEventList():
            # принимается только один encounter :(
            if not encounter:
                eventDiagnosisSet = set()
                orgStructureId = None
                for action in event.getActionList():
                    diagnosis = action.diagnosis
                    condition = mapDiagnosisToCondition.get(diagnosis)
                    if condition is None:
                        condition = self.createCondition(patientReference, diagnosis)
                        conditionList.append(condition)
                        mapDiagnosisToCondition[diagnosis] = condition
                    eventDiagnosisSet.add(diagnosis)
                    if orgStructureId is None:
                        orgStructureId = action.orgStructureId
                    if action.setPersonId not in mapPersonIdToPractitionerReference:
                        practitioner = self.createPractitioner(action.setPersonId, isBundle=True)
                        if not practitioner.id:
                            practitionerList.append(practitioner)
                            mapPersonIdToPractitionerReference[action.setPersonId] = self.createBundleReference(practitioner)
                        else:
                            mapPersonIdToPractitionerReference[action.setPersonId] = self.createReference(practitioner)
                    if directionDatetime is None:
                        directionDatetime = action.directionDatetime

                encounter = self.createEncounter(patientReference,
                                                 event.eventId,
                                                 event.eventTypeId,
                                                 event.eventPurposeId,
                                                 orgStructureId,
                                                 [ mapDiagnosisToCondition[diag]
                                                   for diag in eventDiagnosisSet
                                                 ]
                                                )

            for action in event.getActionList():
                for sp in action.specimenList:
                    specimen = self.createSpecimen(patientReference,
                                                   sp.specimenTypeId,
                                                   sp.containerTypeId,
                                                   sp.externalId,
                                                   sp.takenDatetime,
                                                   sp.probeId
                                                  )
                    specimen = mapSpecimenKeyToSpecimen.setdefault(specimen._key,
                                                                   specimen
                                                                  )
                    mapSpecimenKeyToActions.setdefault(specimen._key, []).append(action)

        specimenList = mapSpecimenKeyToSpecimen.values()
        for specimenKey, specimenSources in mapSpecimenKeyToActions.iteritems():
            # теперь specimenSources - список action
            serviceIdList = [ action.serviceId for action in specimenSources
                            ]
            action = specimenSources[0]
            diagnosticOrder = self.createDiagnosticOrder(patientReference,
                                                         coverageReference,
                                                         mapPersonIdToPractitionerReference[action.setPersonId],
                                                         encounter,
                                                         None,
                                                         serviceIdList,
                                                         [mapSpecimenKeyToSpecimen[specimenKey]]
                                                        )
            diagnosticOrderList.append(diagnosticOrder)

        order = self.createOrder(orderIdentifier,
                                 directionDatetime,
                                 patientReference,
                                 mapPersonIdToPractitionerReference[action.setPersonId],
                                 diagnosticOrderList
                                )

        lisOrderBundle = self.createTransactionBundle( conditionList
                                                       + [ encounter ]
                                                       + practitionerList
                                                       + specimenList
                                                       + diagnosticOrderList
                                                       + [order], 
                                                       StructureDefinition
                                                     )
        return lisOrderBundle
        
        
    def createLisResultBundle(self, actionId):           
        practitionerList = []
        diagnosticReportList = []
        mapPersonIdToPractitionerReference = {}
        observationList = []
        patientList = []
        actionIdentifier = self.createMisIdentifier(actionId)
        StructureDefinition = u'StructureDefinition/21f687dd-0b3b-4a7b-af8f-04be625c0201'
        
        db = QtGui.qApp.db
        tableAction = db.table('Action')
        tableEvent = db.table('Event')
        tableActionType = db.table('ActionType')
        tableActionProperty = db.table('ActionProperty')
        tableActionPropertyType = db.table('ActionPropertyType')
        tableActionProperty_String = db.table('ActionProperty_String')
        tableActionProperty_Double = db.table('ActionProperty_Double')
        tableRbTest = db.table('rbTest')
        tableRbUnit = db.table('rbUnit')
        queryTable = tableAction.leftJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
        queryTable = queryTable.leftJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))
        queryTable = queryTable.leftJoin(tableActionProperty, tableActionProperty['action_id'].eq(tableAction['id']))
        queryTable = queryTable.leftJoin(tableActionPropertyType, db.joinAnd([
                tableActionPropertyType['actionType_id'].eq(tableActionType['id']),
                tableActionPropertyType['id'].eq(tableActionProperty['type_id'])]))
        queryTable = queryTable.leftJoin(tableActionProperty_String, tableActionProperty_String['id'].eq(tableActionProperty['id']))
        queryTable = queryTable.leftJoin(tableActionProperty_Double, tableActionProperty_Double['id'].eq(tableActionProperty['id']))
        queryTable = queryTable.leftJoin(tableRbTest, tableRbTest['id'].eq(tableActionPropertyType['test_id']))
        queryTable = queryTable.leftJoin(tableRbUnit, 'rbUnit.id = IFNULL(ActionProperty.unit_id, ActionPropertyType.unit_id)')
        cond = [ tableAction['id'].eq(actionId),
                 tableActionProperty['deleted'].eq(0),
                 tableActionPropertyType['test_id'].isNotNull(), # проблема в охране, не отправлялись анализы с пустым значением, 'ActionProperty_String.value!=""'
                 'ActionProperty_String.value!=""'
               ]
        cols = [tableAction['id'].alias('actionId'),
                tableEvent['client_id'],
                tableAction['endDate'],
                tableAction['person_id'].alias('execPersonId'),
                tableEvent['execPerson_id'].alias('execEventPersonId'),
                tableActionProperty['norm'],
                tableActionProperty['modifyDatetime'].alias('issued'),
                tableActionProperty_String['value'].alias('strValue'),
                tableActionProperty_Double['value'].alias('intValue'),
                tableRbUnit['code'].alias('unitCode'),
                tableRbTest['regionalCode'].alias('testCode'), 
                tableAction['modifyDatetime'].alias('resultDate'),
                tableActionType['nomenclativeService_id'].alias('serviceId'),
                'COALESCE( ActionProperty_String.value,  ActionProperty_Double.value) IS NOT null'
                ]
        stmt = db.selectStmt(queryTable, cols, cond)
        query = db.query(stmt)
        execEventPersonId = None
        execPersonId = None
        clientId = None
        patientReference = None
        resultDate = None
        serviceId = None
        lisResultBundle = None
        if query.size() > 0:
            while query.next():
                record = query.record()
                if not execEventPersonId:
                    execEventPersonId = forceRef(record.value('execEventPersonId'))
                if not resultDate:
                    resultDate = forceDateTime(record.value('resultDate'))
                if not execPersonId:
                    execPersonId = forceRef(record.value('execPersonId'))
                    if not execPersonId:
                        execPersonId = execEventPersonId
                    if execPersonId not in mapPersonIdToPractitionerReference:
                        practitioner = self.createPractitioner(execPersonId, isBundle=True)
                        if not practitioner.id:
                            practitionerList.append(practitioner)
                            mapPersonIdToPractitionerReference[execPersonId] = self.createBundleReference(practitioner)
                        else:
                            mapPersonIdToPractitionerReference[execPersonId] = self.createReference(practitioner)
                if not clientId:
                    clientId = forceRef(record.value('client_id'))                
                    if clientId not in self.mapClientIdToPatientReference:
                        clientInfo = getClientInfo(clientId)
                        if QtGui.qApp.isAnonim:
                            patient = self.createAnonimousPatient(clientInfo)
                        else:
                            patient = self.createPatient(clientInfo, isBundle=True)
                        if not patient.id:
                            patientList.append(patient)
                            patientReference = self.createBundleReference(patient)
                        else:
                            self.mapClientIdToPatientReference[clientId] = self.createReference(patient)
                            patientReference = self.mapClientIdToPatientReference[clientId]
                    else:
                        patientReference = self.mapClientIdToPatientReference[clientId]
                        
                observation = self.createObservation(patientReference,
                            mapPersonIdToPractitionerReference[execPersonId], 
                            record)
                observationList.append(observation)
                if not serviceId:
                    serviceId = forceRef(record.value('serviceId'))
            
    
            diagnosticReport = self.createDiagnosticReport(serviceId,
                    resultDate,
                    patientReference,
                    mapPersonIdToPractitionerReference[execPersonId],
                    observationList
                   )
            diagnosticReportList.append(diagnosticReport)
                
            orderResponse = self.createOrderResponse(actionIdentifier, diagnosticReportList, resultDate)
            
            lisResultBundle = self.createTransactionBundle(
                                                            [orderResponse]
                                                            + diagnosticReportList
                                                            + observationList
                                                            + practitionerList
                                                            + patientList,
                                                            StructureDefinition
                                                         )
        return lisResultBundle


    def sendOrderOverFHIR(self, clientInfo, order):
        patient           = self.createPatient(clientInfo)
        patientReference  = self.createReference(patient)
        coverage          = self.createCoverage(clientInfo, patientReference)
        coverageReference = self.createReference(coverage)
        probeId = min(order.probeIdSet)
        orderIdentifier = self.createMisIdentifier(probeId)
#        orderIdentifier = self.createMisIdentifier(str(uuid.uuid1()))
        lisOrderBundle = self.createLisOrderBundle(order,
                                                   orderIdentifier,
                                                   patientReference,
                                                   coverageReference)
        self.smart.server.post_json('', lisOrderBundle.as_json())
        return orderIdentifier.value
        
        
    def sendResultOverFHIR(self, actionId):
        lisResultBundle = self.createLisResultBundle(actionId)
        if lisResultBundle:
            res = self.smart.server.post_json(u'$addresults', lisResultBundle.as_json(), raiseIfstatusError=False)
            db = QtGui.qApp.db
            tableAction_Export = db.table('Action_Export')   
            actionExport = db.getRecordEx(tableAction_Export, '*', 'master_id = %d and system_id = %d' % (actionId, self.externalSystemId))
            if not actionExport:
                actionExport = tableAction_Export.newRecord()
            actionExport.setValue('master_id',  toVariant(actionId))
            #actionExport.setValue('masterDatetime', toVariant(QDateTime.currentDateTime()))
            actionExport.setValue('system_id', toVariant(self.externalSystemId))
            if res.status_code >= 400:
                actionExport.setValue('success', toVariant(0))
                actionExport.setValue('note', toVariant(res.request.body + res._content))
            else:
                actionExport.setValue('success', toVariant(1))
                actionExport.setValue('note', toVariant(None))
            actionExport.setValue('dateTime', toVariant(QDateTime.currentDateTime()))
            #actionExport.setValue('externalId', toVariant(actionIdentifier.value))
            db.insertOrUpdate(tableAction_Export, actionExport)

        return actionId



    def createDiagnosticReport(self, patientReference, serviceId, observations):
        serviceCode, serviceVersion = getIdentificationEx('rbService', serviceId, self.serviceUrn)

        diagnosticReport = DiagnosticReport()
        diagnosticReport.conclusion = u'Value should be no empty string on DiagnosticReport'
        diagnosticReport.issued     = observations[0].issued
        diagnosticReport.name       = self.createCodeableConcept(self.serviceUrn,
                                                                 serviceCode,
                                                                serviceVersion)
        diagnosticReport.performer  = observations[0].performer[0]
        diagnosticReport.result     = [ self.createBundleReference(observation)
                                        for observation in observations
                                      ]
        diagnosticReport.status     = 'final'
        diagnosticReport.subject    = patientReference
        fakeAttachment              = Attachment()
        fakeAttachment.data = 'eyJkYXRhIjoiIiwiU2lnbiI6IiIsImhhc2giOiIiLCJwdWJsaWNfa2V5IjoiIn0='
        diagnosticReport.presentedForm = [ fakeAttachment ]
        return diagnosticReport


    def createOrderResponse(self, diagnosticReport, actionId):
        orderResponse = OrderResponse()
        orderResponse.who  = self.orgReference
        orderResponse.date = dateTimeToFHIRDate(QDateTime.currentDateTime())
        orderResponse.fulfillment = [ self.createBundleReference( diagnosticReport ) ]
        orderResponse.identifier = [ self.createMisIdentifier(str(actionId)) ]
        orderResponse.orderStatus = 'accepted'
#        orderResponse.request = FHIRReference()
#        orderResponse.request.reference = ''
        return orderResponse


    def createResultBundle(self, patientReference, serviceId, results):
        mapPersonIdToPractitionerReference = {}
        personIdSet = set(res.personId for res in results)
        for personId in personIdSet:
            if personId:
                practitioner = self.createPractitioner(personId)
                mapPersonIdToPractitionerReference[personId] = self.createReference(practitioner)

        observations = []
        for res in results:
            observation = self.createObservation(res, mapPersonIdToPractitionerReference)
            if observation:
                observations.append( observation )
        if not observations:
            return None

        diagnosticReport = self.createDiagnosticReport(patientReference, serviceId, observations)
        orderResponse = self.createOrderResponse(diagnosticReport, results[0].actionId)
        resultBundle = self.createTransactionBundle( self.resultProfile,
                                                     observations
                                                     + [ diagnosticReport ]
                                                     + [ orderResponse ]
                                              )
        return resultBundle


    def sendLocalResultsOverFHIR(self, clientInfo, serviceId, results):
        patient           = self.createPatient(clientInfo)
        patientReference  = self.createReference(patient)
#        coverage          = self.createCoverage(clientInfo, patientReference)
#        coverageReference = self.createReference(coverage)
        resultBundle = self.createResultBundle(patientReference, serviceId, results)
        if resultBundle:
            self.smart.server.post_json('$addresults', resultBundle.as_json())
            return True
        else:
            return False


    def extractCode(self, coding, uri, ref, path):
        if not coding:
            raise Exception(u'%s в %s пуст' % (path, ref))
        for c in coding:
            if c.system.lower() == uri:
                return c.code
        raise Exception(u'%s в %s не имеет кода для %s' % (path, ref, uri))


    def processDiagnosticReport(self, result, diagnosticReport):
        refDiagnosticReport = diagnosticReport.relativePath()
        serviceCode = self.extractCode(diagnosticReport.name.coding,
                                       self.serviceUrn,
                                       refDiagnosticReport,
                                       'diagnosticReport.name.coding'
                                      )
        issued      = QDateTime.fromString(diagnosticReport.issued.isostring, Qt.ISODate)
        conclusion  = diagnosticReport.conclusion
        serviceResult = CFHIRServiceResult(serviceCode, issued, conclusion)
        for item in diagnosticReport.result:
            observation = Observation.read_from(item.reference, self.smart.server)
            refObservation = observation.relativePath()
            testCode = self.extractCode(observation.code.coding,
                                        self.loincUrn,
                                        refObservation,
                                        'observation.code.coding'
                                   )
            value = CFHIRResultValue(testCode)
            if observation.valueQuantity is not None:
                value.value = float(observation.valueQuantity.value)
                value.unit  = observation.valueQuantity.units
                if observation.referenceRange:
                    if len(observation.referenceRange) != 1:
                        raise Exception(u'неожиданный observation.referenceRange в %s' % refObservation)
                    rr = observation.referenceRange[0]
                    if rr.low is not None and rr.low.units and rr.low.units != value.unit:
                        raise Exception(u'разные единицы измерения observation.valueQuantity.units != observation.referenceRange[0].low.units в %s' % refObservation)
                    if rr.high is not None and rr.high.units and rr.high.units != value.unit:
                        raise Exception(u'разные единицы измерения observation.valueQuantity.units != observation.referenceRange[0].high.units в %s' % refObservation)
                    value.referenceRange = ( rr.low.value  if rr.low else None,
                                             rr.high.value if rr.high else None
                                           )
            elif observation.valueString is not None:
                value.value = unicode(observation.valueString)
            else:
                raise Exception(u'неожиданный тип observation.value в %s' % refObservation)
            serviceResult.values.append(value)
        result.addServiceResult(serviceResult)


    def requestResultOverFHIR(self, fhirOrderId):
        try:
            params = { 'request:Order.identifier':
                        ('%s|%s' % (self.SAMSON, fhirOrderId)).encode('utf8'),
                   }
            searchObject = OrderResponse.where(params)
            searchBundle = searchObject.perform(self.smart.server)
            result = CFHIRResult(fhirOrderId)
            if searchBundle and searchBundle.entry is not None:
                orderFinished = False
                for entry in searchBundle.entry:
                    orderResponse = entry.resource
                    orderFinished = orderFinished or orderResponse.orderStatus in ('completed', 'rejected', 'error', 'cancelled', 'replaced', 'aborted')
                    for item in orderResponse.fulfillment:
                        diagnosticReport = DiagnosticReport.read_from(item.reference, self.smart.server)
                        self.processDiagnosticReport(result, diagnosticReport)
                if result.serviceResults:
                    result.completed = orderFinished
            return result
        except Exception, e:
            raise Exception(u'при получении результата по заказу %s произошла ошибка:\n%s' % (fhirOrderId, e.message or unicode(e)))
