# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2016-2020 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################
##
## Взаимодейсивие с лабораторной системой по протоколу FHIR:
## - отправка заказов
## - получение результатов
## - отправка результатов локальных лабораторий с целью "интерграции"
##
#############################################################################

import isodate
import json
import uuid
import xml.sax
import base64
import os
from StringIO import StringIO
from collections import namedtuple

from PyQt4 import QtGui, QtSql
from PyQt4.QtCore import Qt, QDate, QDateTime, QEventLoop, QTemporaryFile

from Events.ActionInfo import CActionInfo
from Events.ActionStatus import CActionStatus
from Events.Utils import getEventDiagnosis
from Exchange.FHIRClient.models102.parameters import Parameters, ParametersParameter
from ODIIExchange import fmtDate, unFmtDate
from library.Attach.AttachedFile import CAttachedFilesLoader
from library.Attach.WebDAVInterface import CWebDAVInterface
from library.Utils import (
    exceptionToUnicode,
    forceBool,
    forceDouble,
    forceInt,
    forceRef,
    forceString,
    forceDate,
    forceDateTime,
    formatNameInt,
    toVariant, quote, anyToUnicode
)
from library.Identification import (
                                    getIdentification,
                                    getIdentificationEx,
                                    findByIdentification,
                                    addIdentification,
                                    CIdentificationException,
                                   )
from library.PrintTemplates import getTemplate, compileAndExecTemplate
from library.PrintInfo import CInfoContext, CDateInfo

from Events.Action          import CAction
from Orgs.Utils             import getOrgStructureIdentification
from Registry.Utils         import (
                                     CClientInfo,
#                                     getClientIdentification,
                                     setClientIdentification,
                                     findClientByIdentification,
                                     getClientInfo
                                   )

from Orgs.Utils             import getOrganisationShortName

from Exchange.FHIRClient import client, server
from Exchange.FHIRClient.models102.address          import Address
from Exchange.FHIRClient.models102.annotation       import Annotation
from Exchange.FHIRClient.models102.attachment       import Attachment
from Exchange.FHIRClient.models102.binary           import Binary
from Exchange.FHIRClient.models102.bundle           import Bundle, BundleEntry, BundleEntryRequest
from Exchange.FHIRClient.models102.codeableconcept  import CodeableConcept
from Exchange.FHIRClient.models102.coding           import Coding
from Exchange.FHIRClient.models102.condition        import Condition
#from Exchange.FHIRClient.models102.conformance      import Conformance
from Exchange.FHIRClient.models102.contactpoint     import ContactPoint
from Exchange.FHIRClient.models102.diagnosticorder  import DiagnosticOrder, DiagnosticOrderItem
from Exchange.FHIRClient.models102.diagnosticreport import DiagnosticReport
from Exchange.FHIRClient.models102.encounter        import Encounter
from Exchange.FHIRClient.models102.extension        import Extension
from Exchange.FHIRClient.models102.fhirdate         import FHIRDate
from Exchange.FHIRClient.models102.fhirreference    import FHIRReference
from Exchange.FHIRClient.models102.humanname        import HumanName
from Exchange.FHIRClient.models102.identifier       import Identifier
from Exchange.FHIRClient.models102.meta             import Meta
from Exchange.FHIRClient.models102.observation      import Observation, ObservationReferenceRange
from Exchange.FHIRClient.models102.order            import Order, OrderWhen
from Exchange.FHIRClient.models102.orderresponse    import OrderResponse
from Exchange.FHIRClient.models102.organization     import Organization
from Exchange.FHIRClient.models102.patient          import Patient, PatientLink, PatientContact
from Exchange.FHIRClient.models102.period           import Period
from Exchange.FHIRClient.models102.practitioner     import Practitioner, PractitionerPractitionerRole
from Exchange.FHIRClient.models102.reference        import Reference
from Exchange.FHIRClient.models102.quantity         import Quantity
from Exchange.FHIRClient.models102.specimen         import Specimen, SpecimenCollection, SpecimenContainer

__all__ = ( 'sendOrdersOverFHIR',
            'pickupResultsOverFHIR',
            'sendLocalResultsOverFHIR',
#            'sendLISResultsOverFHIR',
            'importOrdersOverFhir'
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


def pickupResultsOverFHIR(widget, equipmentInterface, probeIdList, recordList = []):
    if not recordList:
        db = QtGui.qApp.db
        tableProbe = db.table('Probe')
        cond = [ tableProbe['status'].eq(6),  # Передано в ЛИС
                 tableProbe['equipment_id'].eq(equipmentInterface.id), # и ЛИС тот самый
                 tableProbe['exportName'].ne(''), # exportName заполнен
                 tableProbe['exportDatetime'].ge(QDateTime.currentDateTime().addDays(-7)), # прошло не более недели с заказа
                 tableProbe['id'].inlist(probeIdList) if probeIdList else '1'
               ]
        recordList = db.getRecordList(tableProbe,
                                      [ '*' ],
                                      cond
                                     )
    opts = json.loads(equipmentInterface.address)
    orgId = QtGui.qApp.currentOrgId()
    interfaceObject = CFHIRExchange(opts, orgId)
    setOfProcessedOrderIds = set()
    for record in recordList:
        fhirOrderId = forceString(record.value('exportName'))
        tissueJournalId = forceRef(record.value('takenTissueJournal_id'))
        pdfFileName = 'report'
        if tissueJournalId:
            clientId = forceRef(QtGui.qApp.db.translate('TakenTissueJournal', 'id', tissueJournalId, 'client_id'))
            firstExecDate = forceDateTime(QtGui.qApp.db.translate('TakenTissueJournal', 'id', tissueJournalId, 'firstExecDatetime'))
            pdfFileName = formatPdfFileName(tissueJournalId)
        if fhirOrderId not in setOfProcessedOrderIds:
            if widget:
                QtGui.qApp.processEvents(QEventLoop.ExcludeUserInputEvents)
            try:
                fhirResult = interfaceObject.requestResultOverFHIR(fhirOrderId, pdfFileName)
                fhirResult.storeToProbes(equipmentInterface.id)
                fhirResult.addEpidCase(clientId)
                fhirResult.storeExecDate(firstExecDate, tissueJournalId)
                setOfProcessedOrderIds.add(fhirOrderId)
            except Exception, e:
                QtGui.qApp.log('importFhir', u'при получении результата по заказу %s произошла ошибка:\n%s' % (
                    fhirOrderId, exceptionToUnicode(e)))
    return setOfProcessedOrderIds


def sendLocalResultsOverFHIR(equipmentInterface, clientInfo, serviceId, results, actionId, orgStructureDescr, sourceOrgStructureDescr):
    opts = json.loads(equipmentInterface.address)
    orgId = QtGui.qApp.currentOrgId()
    interfaceObject = CFHIRExchange(opts, orgId, orgStructureDescr, sourceOrgStructureDescr)
    interfaceObject.sendLocalResultsOverFHIR(clientInfo, serviceId, results, actionId)


def sendResultsOverFHIR(equipmentInterface, clientInfo, serviceId, results):
    opts = json.loads(equipmentInterface.address)
    orgId = QtGui.qApp.currentOrgId()
    interfaceObject = CFHIRExchange(opts, orgId)
    return interfaceObject.sendLISResultsOverFHIR(clientInfo, serviceId, results)


def importOrdersOverFhir(equipmentInterface, dateFrom, dateTo):
    opts = json.loads(equipmentInterface.address)
    orgId = QtGui.qApp.currentOrgId()
    interfaceObject = CFHIRExchange(opts, orgId)
    interfaceObject.getOrders(dateFrom, dateTo, opts.get('source', None))


# ##############################################################################

def formatPdfFileName(tissueJournalId):
    db = QtGui.qApp.db
    tableAction = db.table('Action')
    tableActionType = db.table('ActionType')
    tableClient = db.table('Client')
    tableEvent = db.table('Event')
    table = tableAction.leftJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))
    table = table.leftJoin(tableClient, tableClient['id'].eq(tableEvent['client_id']))
    table = table.leftJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
    cols = [
        tableClient['id'].alias('clientId'),
        tableClient['lastName'].alias('lastName'),
        tableClient['firstName'].alias('firstName'),
        tableActionType['code'].alias('typeCode'),
        tableAction['endDate'].alias('endDate')
    ]
    record = db.getRecordEx(table, cols, [tableAction['takenTissueJournal_id'].eq(tissueJournalId)])
    clientFIO = u"%s%s"%(forceString(record.value('lastName')), forceString(record.value('firstName')))
    clientId = forceRef(record.value('clientId'))
    actionTypeName = forceString(record.value('typeCode'))
    actionEndDate = forceDate(record.value('endDate')).toString('yyyyMMdd')
    return "%s_%s_%s_%s"%(clientFIO, clientId, actionTypeName, actionEndDate)

# ##############################################################################


class COrderDto:
    u'Заказ, состоит из событий'
    def __init__(self):
        self.takenDatetime = None
#        self.takenTissueJournalId = None
        self.jobTicketId = None
        self.mapEventIdtoEvent = {}
        self.probeIdSet = set([])

        self.params = COrderParams()

        self.__menopause = False
        self.__menstrualDay         = 0 # может быть взято из разных записей, беру макс.значение
        self.__pregnancyWeek        = 0 # может быть взято из разных записей, беру макс.значение
        self.__lastMenstruationDate = None # решения пока нет: это вводится или вычисляется как self.takenDatetime - self.__menstrualDay


    def updateParams(self):
        commonParams = {}
        if self.__menopause:
            commonParams['Condition:Menopause'] = True
        else:
            if self.__menstrualDay:
                commonParams['Observation:MenstrualDay'] = self.__menstrualDay
                commonParams['Condition:LastMenstruationDate'] = self.takenDatetime.date().addDays(-self.__menstrualDay)
            elif self.__pregnancyWeek:
                commonParams['Observation:PregnancyWeek'] = self.__pregnancyWeek
        self.params.update(commonParams)
        for event in self.mapEventIdtoEvent.itervalues():
            event.updateParams(self.params)


    def getEventList(self):
        return self.mapEventIdtoEvent.values()


    def addProbe(self,
                 eventId,
                 eventExternalId,
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
                 collectorId,
                 externalId,
                 specimenTypeId,
                 containerTypeId,
                 probeId,
                 financeId,
                 note,
                 menopause,
                 pregnancyWeek,
                 menstrualDay,
                 financeIdByActionType
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
        self.takenDatetime = max(self.takenDatetime, takenDatetime)
        self.__menopause   = menopause
        self.__pregnancyWeek = max(self.__pregnancyWeek, pregnancyWeek)
        self.__menstrualDay  = max(self.__menstrualDay,  menstrualDay)
        event = self.mapEventIdtoEvent.get(eventId)
        if event is None:
            event = self.mapEventIdtoEvent[eventId] = CEventDto(eventId, eventExternalId, eventTypeId, eventPurposeId)
        action = event.getAction(actionId,
                                 actionTypeId,
                                 directionDatetime,
                                 orgStructureId,
                                 setPersonId,
                                 MKB,
                                 serviceId,
                                 financeId,
                                 note,
                                 financeIdByActionType)
        action.addSpecimen(specimenTypeId,
                           containerTypeId,
                           externalId,
                           takenTissueJournalId,
                           takenDatetime,
                           collectorId,
                           probeId)


class CEventDto:
    u'описание события, во fhir превращается в encounter'
    def __init__(self, eventId, externalId, eventTypeId, eventPurposeId):
        self.eventId = eventId
        self.externalId = externalId
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
                  serviceId,
                  financeId,
                  note,
                  financeIdByActionType
                 ):
        action = self.mapActionIdToAction.get(actionId)
        if action is None:
            action = self.mapActionIdToAction[actionId] = CActionDto(actionId,
                                                                      actionTypeId,
                                                                      directionDatetime,
                                                                      orgStructureId,
                                                                      setPersonId,
                                                                      diagnosis,
                                                                      serviceId,
                                                                     financeId,
                                                                     note,
                                                                     financeIdByActionType)
        return action

    def updateParams(self, orderParams):
        for action in self.mapActionIdToAction.itervalues():
            action.updateParams(orderParams)


class CActionDto:
    u'описание события, во fhir совокупность CActionDto превращается в diagnosticOrder'
    def  __init__(self,
                  actionId,
                  actionTypeId,
                  directionDatetime,
                  orgStructureId,
                  setPersonId,
                  diagnosis,
                  serviceId,
                  financeId,
                  note,
                  financeIdByActionType
                 ):
        self.actionId = actionId
        self.actionTypeId = actionTypeId
        self.directionDatetime = directionDatetime
        self.orgStructureId = orgStructureId
        self.setPersonId = setPersonId
        self.diagnosis = diagnosis
        self.serviceId = serviceId
        self.financeId = financeId
        self.note      = note
        self.financeIdByActionType = financeIdByActionType
        self.specimenList = []


    def addSpecimen(self, specimenTypeId,
                          containerTypeId,
                          externalId,
                          takenTissueJournalId,
                          takenDatetime,
                          collectorId,
                          probeId):
        self.specimenList.append(CSpecimenDto(specimenTypeId,
                                              containerTypeId,
                                              externalId,
                                              takenTissueJournalId,
                                              takenDatetime,
                                              collectorId,
                                              probeId))


    def getSpecimenList(self):
        return self.specimenList


    def getParams(self):
        db = QtGui.qApp.db
        tableAction = db.table('Action')
        tableActionPropertyType = db.table('ActionPropertyType')
        tableActionProperty = db.table('ActionProperty')
        tableActionPropertyDate    = db.table('ActionProperty_Date')
        tableActionPropertyDouble  = db.table('ActionProperty_Double')
        tableActionPropertyInteger = db.table('ActionProperty_Integer')
        tableActionPropertyString  = db.table('ActionProperty_String')
        tableActionPropertyBoolean = db.table('ActionProperty_Boolean')

        table = tableAction
        table = table.innerJoin(tableActionPropertyType,
                                [ tableActionPropertyType['deleted'].eq(0),
                                  tableActionPropertyType['actionType_id'].eq(tableAction['actionType_id'])
                                ]
                               )
        table = table.innerJoin(tableActionProperty,
                                [ tableActionProperty['deleted'].eq(0),
                                  tableActionProperty['action_id'].eq(tableAction['id']),
                                  tableActionProperty['type_id'].eq(tableActionPropertyType['id']),
                                ]
                               )
        table = table.leftJoin( tableActionPropertyDate,
                                [
                                  tableActionPropertyDate['id'].eq(tableActionProperty['id']),
                                  tableActionPropertyDate['index'].eq(0),
                                ]
                              )
        table = table.leftJoin( tableActionPropertyDouble,
                                [
                                  tableActionPropertyDouble['id'].eq(tableActionProperty['id']),
                                  tableActionPropertyDouble['index'].eq(0),
                                ]
                              )
        table = table.leftJoin( tableActionPropertyInteger,
                                [
                                  tableActionPropertyInteger['id'].eq(tableActionProperty['id']),
                                  tableActionPropertyInteger['index'].eq(0),
                                ]
                              )

        table = table.leftJoin( tableActionPropertyString,
                                [
                                  tableActionPropertyString['id'].eq(tableActionProperty['id']),
                                  tableActionPropertyString['index'].eq(0),
                                ]
                              )

        table = table.leftJoin( tableActionPropertyBoolean,
                                [
                                    tableActionPropertyBoolean['id'].eq(tableActionProperty['id']),
                                    tableActionPropertyBoolean['index'].eq(0),
                                ]
                              )

        recordList = db.getRecordList(table,
                                      [ tableActionPropertyType['descr'],
                                        tableActionPropertyType['typeName'],
                                        tableActionProperty['unit_id'],
                                        tableActionPropertyDate['value'].alias('valDate'),
                                        tableActionPropertyDouble['value'].alias('valDouble'),
                                        tableActionPropertyInteger['value'].alias('valInteger'),
                                        tableActionPropertyString['value'].alias('valString'),
                                        tableActionPropertyBoolean['value'].alias('valBool')
                                      ],
                                      db.joinAnd([tableAction['id'].eq(self.actionId),
                                                  tableActionPropertyType['descr'].like('#ODLI%'),
                                                 ]
                                                )
                                     )
        props = {}
        for record in recordList:
            descr = forceString(record.value('descr'))
            typeName = forceString(record.value('typeName'))
            unitId = forceRef(record.value('unit_id'))
            if typeName == 'Date':
                value = forceDate(record.value('valDate'))
            elif typeName == 'Double':
                value = forceDouble(record.value('valDouble'))
                if unitId:
                    value = (value, unitId)
            elif typeName == 'Integer':
                value = forceInt(record.value('valInteger'))
                if unitId:
                    value = (value, unitId)
            elif typeName == 'String':
                value = forceString(record.value('valString'))
            elif typeName == 'Boolean':
                value = forceInt(record.value('valBool'))
            else:
                value = None
            if value:
                key = (descr[5:].split('#')[0]).strip()
                props[key] = value
        return props


    def updateParams(self, orderParams):
        orderParams.update(self.getParams())


CSpecimenDto = namedtuple('CSpecimenDto',
                          ('specimenTypeId',
                           'containerTypeId',
                           'externalId',
                           'takenTissueJournalId',
                           'takenDatetime',
                           'collectorId',
                           'probeId',
                          )
                         )

class COrderParams:
    def __init__(self):
        self.data = {}

    def update(self, partParams):
        self.data.update(partParams)

    def getCode(self, key):
        val = self.data.get(key, None)
        if isinstance(val, unicode):
            code = val.split()[0]
            if code:
                return code
        return None


    def getString(self, key):
        val = self.data.get(key, None)
        if isinstance(val, unicode):
            return val
        return None


    def getValue(self, key):
        return self.data.get(key, None)



class CFHIRResultValue:
    def __init__(self, code):
        self.code  = code
        self.value = None
        self.unitId  = None
        self.referenceRange = None
        self.referenceRangeText = ''
        self.issuedTime = None


class CFHIRServiceResult:
    def __init__(self, code, issued, conclusion, identifier=None):
        self.code = code
        self.issued = issued
        self.conclusion = conclusion
        self.values = []
        self.identifier = identifier
        self.category = None
        self.diagnosticEffectivePeriod = (None, None)
        self.histologyConclusion = None


class CFHIRResult:
    def __init__(self, fhirOrderId):
        self.fhirOrderId = fhirOrderId
        self.probeIdSet = set()
        self.finished = False # результатов больше не будет
        self.errorMessage  = ''
        self.note          = ''
        self.serviceResults = []
        self.conclusionHardwareTestCode = 'conclImportHist'
        self.dateStartHardwareTestCode = 'dateStartHist'
        self.dateEndHardwareTestCode = 'dateEndHist'
        self.histology1DateHardwareTestCode = 'histology:1date'
        #self.orderResponseIdentifierTestCode = 'orderIdentHist'
        #self.histologyCategory = 'categoryHist'
        self.execDates = []


    def addProbeId(self, probeId):
        self.probeIdSet.add(probeId)


    def addServiceResult(self, serviceResult):
        self.serviceResults.append(serviceResult)


    @staticmethod
    def getMapTestCodeToTestAndSpecimenTypePairs(eqipmentId):
        db = QtGui.qApp.db
        table = db.table('rbEquipment_Test')
        records = db.getRecordList(table,
                                   ['test_id', 'hardwareTestCode', 'specimenType_id'],
                                   db.joinAnd([table['equipment_id'].eq(eqipmentId),
                                               table['type'].inlist((1, 2)),
                                               table['test_id'].isNotNull()
                                              ])
                                  )
        result = {}
        for record in records:
            code   = forceString(record.value('hardwareTestCode'))
            specimenTypeId = forceRef(record.value('specimenType_id'))
            testId = forceRef(record.value('test_id'))
            result.setdefault(code, []).append((testId, specimenTypeId))
        return result


    @staticmethod
    def determineTypeName(value):
        return 'String' if isinstance(value, basestring) else 'Double'


    @staticmethod
    def updateOrAddProbe(eqipmentId, exportName, testAndSpecimenTypePairs, value, unitName, unitId, referenceRangeAsStr, note):
        db = QtGui.qApp.db

        tableProbe = db.table('Probe')
        specimenTypeAndTestCond = []
        for (testId, specimenTypeId) in testAndSpecimenTypePairs:
            specimenTypeAndTestCond.append(db.joinAnd([ tableProbe['test_id'].eq(testId),
                                                        tableProbe['specimenType_id'].eq(specimenTypeId)
                                                      ]
                                                     )
                                            )
        probeList = db.getRecordList(tableProbe,
                                     '*',
                                     db.joinAnd([tableProbe['equipment_id'].eq(eqipmentId),
                                                 tableProbe['exportName'].eq(exportName),
                                                 db.joinOr(specimenTypeAndTestCond),
                                                ]
                                               )
                                    )
        if probeList:
            for record in probeList:
                status  = forceInt(record.value('status'))
                if status in (6, 7):
                    record.setValue('status',          7)
                    record.setValue('resultIndex',     1)
                    record.setValue('result1',         value)
                    record.setValue('typeName',        CFHIRResult.determineTypeName(value))
                    record.setValue('unit_id',         unitId)
                    record.setValue('externalUnit',    unitName)
                    record.setValue('norm',            referenceRangeAsStr)
                    record.setValue('externalNote',    note)
                    record.setValue('externalNorm',    referenceRangeAsStr)
                    record.setValue('importDatetime',  QDateTime.currentDateTime())
                    record.setValue('importPerson_id', QtGui.qApp.userId)
                    db.updateRecord(tableProbe, record)
        else:
            takenTissueJournalIdList = db.getDistinctIdList(tableProbe,
                                                            'takenTissueJournal_id',
                                                            db.joinAnd([tableProbe['equipment_id'].eq(eqipmentId),
                                                                        tableProbe['exportName'].eq(exportName),
                                                                       ]
                                                                      )
                                                           )
            for (testId, specimenTypeId) in testAndSpecimenTypePairs:
                record = tableProbe.newRecord()
                record.setValue('equipment_id',    eqipmentId)
                record.setValue('exportName',      exportName)
                record.setValue('test_id',         testId)
                record.setValue('workTest_id',     testId)
                record.setValue('specimenType_id', specimenTypeId)
                record.setValue('takenTissueJournal_id', takenTissueJournalIdList[0])
                record.setValue('status',          7)
                record.setValue('resultIndex',     1)
                record.setValue('result1',         value)
                record.setValue('typeName',        CFHIRResult.determineTypeName(value))
                record.setValue('unit_id',         unitId)
                record.setValue('externalUnit',    unitName)
                record.setValue('norm',            referenceRangeAsStr)
                record.setValue('externalNorm',    referenceRangeAsStr)
                record.setValue('externalNote',    note)
                record.setValue('importDatetime',  QDateTime.currentDateTime())
                record.setValue('importPerson_id', QtGui.qApp.userId)
                db.insertRecord(tableProbe, record)


    @staticmethod
    def getReferenceRangeAsStr(referenceRange, referenceRangeText):
        if referenceRange and referenceRange != (None, None):
            low, high = referenceRange
            if low is None:
                low = 0.0
            if high is None:
                high = 999.99
            return str(low) + ' - ' + str(high)
        else:
            return referenceRangeText


    @staticmethod
    def markRemainedProbesAsAcceptedWithoutResult(eqipmentId, exportName, message):
        db = QtGui.qApp.db
        tableProbe = db.table('Probe')
        record = tableProbe.newRecord(['status', 'result1', 'resultIndex', 'importDatetime', 'importPerson_id'])
        record.setValue('status',          7)
        record.setValue('result1',         message)
        record.setValue('resultIndex',     4)
        record.setValue('importDatetime',  QDateTime.currentDateTime())
        record.setValue('importPerson_id', QtGui.qApp.userId)

        cond = db.joinAnd([tableProbe['equipment_id'].eq(eqipmentId),
                           tableProbe['exportName'].eq(exportName),
                           tableProbe['status'].eq(6),
                          ]
                         )
        db.updateRecords(tableProbe, record,  cond)


    def storeToProbes(self, eqipmentId):
        freeResuts = {}
        mapTestCodeToTestAndSpecimenTypePairs = self.getMapTestCodeToTestAndSpecimenTypePairs(eqipmentId)
        db = QtGui.qApp.db
        db.transaction()
        try:
            histologyConclusion = ''
            for serviceResult in self.serviceResults:
                for value in serviceResult.values:
                    testAndSpecimenTypePairs = mapTestCodeToTestAndSpecimenTypePairs.get(value.code)
                    unit = forceString(db.translate('rbUnit', 'id', value.unitId, 'code'))
                    referenceRangeAsStr = self.getReferenceRangeAsStr(value.referenceRange, value.referenceRangeText)
                    if testAndSpecimenTypePairs:
                        self.updateOrAddProbe(eqipmentId, self.fhirOrderId, testAndSpecimenTypePairs, value.value, unit, value.unitId, referenceRangeAsStr, self.note)
                    if value.issuedTime:
                        testAndSpecimenTypePairsHistology1Date = mapTestCodeToTestAndSpecimenTypePairs.get(self.histology1DateHardwareTestCode)
                        #histology1Date = QDateTime.fromString(value.issuedTime, Qt.ISODate)
                        self.updateOrAddProbe(eqipmentId,
                                              self.fhirOrderId,
                                              testAndSpecimenTypePairsHistology1Date,
                                              value.issuedTime,
                                              '',
                                              None,
                                              '',
                                              self.note)
                    else:
                        freeResuts[value.code] = { 'value' : value.value,
                                                   'unit'  : unit,
                                                   'referenceRange': referenceRangeAsStr
                                                 }
                if serviceResult.histologyConclusion:
                    histologyConclusion += serviceResult.histologyConclusion
                if len(self.serviceResults) == 1:
                    if serviceResult.diagnosticEffectivePeriod[0]:
                        #dateStartHistology = QDateTime.fromString(serviceResult.diagnosticEffectivePeriod[0], Qt.ISODate)
                        dateStartHistology = serviceResult.diagnosticEffectivePeriod[0].replace('T', ' ')
                        testAndSpecimenTypePairsDateStart = mapTestCodeToTestAndSpecimenTypePairs.get(self.dateStartHardwareTestCode)
                        if testAndSpecimenTypePairsDateStart:
                            self.updateOrAddProbe(eqipmentId,
                                                  self.fhirOrderId,
                                                  testAndSpecimenTypePairsDateStart,
                                                  dateStartHistology,
                                                  '',
                                                  None,
                                                  '',
                                                  self.note)
                    if serviceResult.diagnosticEffectivePeriod[1]:
                        #dateEndHistology = QDateTime.fromString(serviceResult.diagnosticEffectivePeriod[1], Qt.ISODate)
                        dateEndHistology = serviceResult.diagnosticEffectivePeriod[1].replace('T', ' ')
                        testAndSpecimenTypePairsDateEnd = mapTestCodeToTestAndSpecimenTypePairs.get(self.dateEndHardwareTestCode)
                        if testAndSpecimenTypePairsDateEnd:
                            self.updateOrAddProbe(eqipmentId,
                                                  self.fhirOrderId,
                                                  testAndSpecimenTypePairsDateEnd,
                                                  dateEndHistology,
                                                  '',
                                                  None,
                                                  '',
                                                  self.note)    
                
            if histologyConclusion:
                testAndSpecimenTypePairsConclusion = mapTestCodeToTestAndSpecimenTypePairs.get(self.conclusionHardwareTestCode)
                if testAndSpecimenTypePairsConclusion:
                    self.updateOrAddProbe(eqipmentId,
                                          self.fhirOrderId,
                                          testAndSpecimenTypePairsConclusion,
                                          histologyConclusion,
                                          '',
                                          None,
                                          '',
                                          self.note)
            if freeResuts:
                testAndSpecimenTypePairs = mapTestCodeToTestAndSpecimenTypePairs.get('blank')
                if testAndSpecimenTypePairs:
                    self.updateOrAddProbe(eqipmentId, self.fhirOrderId, testAndSpecimenTypePairs, json.dumps(freeResuts), '', None, '', self.note)

            if self.finished:
                self.markRemainedProbesAsAcceptedWithoutResult(eqipmentId, self.fhirOrderId, self.errorMessage)
            db.commit()
        except:
            db.rollback()
            raise


    def addEpidCase(self, clientId):
        for serviceResult in self.serviceResults:
            if serviceResult.identifier:
                db = QtGui.qApp.db

                identifier = serviceResult.identifier
                externalEpidCaseNumber = identifier.value

                tableEpidCase = db.table('Client_EpidCase')
                clientEpidCaseList = db.getRecordList(tableEpidCase,
                                                        '*',
                                                        db.joinAnd([ tableEpidCase['master_id'].eq(clientId),
                                                                     tableEpidCase['number'].eq(externalEpidCaseNumber) ]
                                                                  )
                                                     )
                if clientEpidCaseList:
                    return None

                orgName = u'неизвестная организация'
                if hasattr(identifier.assigner, 'reference'):
                    orgName = identifier.assigner.reference.split('/')[-1]

                record = tableEpidCase.newRecord()
                record.setValue('master_id', clientId)
                record.setValue('number', externalEpidCaseNumber)
                record.setValue('regDate', QDate.currentDate())
                record.setValue('note', u'Получен от организации c идентификатором %s' % orgName)
                newEpidCaseId = db.insertRecord(tableEpidCase, record)
                if newEpidCaseId:
                    QtGui.qApp.log('epidCase', u'Заведена новая запись эпидномера с id %i для пациента с id %i' % (newEpidCaseId, clientId))
    

    def storeExecDate(self, firstExecDate, takenTissueJournalId):
        db = QtGui.qApp.db
        if not self.execDates:
            return None
        currDatetime = self.execDates[0]
        currFirstDatetime = self.execDates[0]
        for execDate in self.execDates:
            if firstExecDate.isNull():
                if currFirstDatetime.secsTo(execDate) < 0:
                    currFirstDatetime = execDate
        for execDate in self.execDates:
            if currDatetime.secsTo(execDate) >= 0:
                currDatetime = execDate
        
        tableTissueJournal = db.table('TakenTissueJournal')
        ttjRecord = db.getRecord(tableTissueJournal,
                                 ('firstExecDatetime','execDatetime','id'),
                                 takenTissueJournalId
                                )
        if firstExecDate.isNull():
            ttjRecord.setValue('firstExecDatetime', toVariant(currFirstDatetime))
        ttjRecord.setValue('execDatetime', toVariant(currDatetime))
        db.updateRecord(tableTissueJournal, ttjRecord)


def getArkhangelskEncounterData(actionId):
    db = QtGui.qApp.db
    tableAction = db.table('Action')
    tableEvent = db.table('Event')
    tableEventType = db.table('EventType')
    tablePerson = db.table('Person')
    tableSpec = db.table('rbSpeciality')
    tableSpecMAP = db.table('rbSpeciality_MedicalAidProfile')
    tableKind = db.table('rbMedicalAidKind')
    tableProfile = db.table('rbMedicalAidProfile')
    tableAidType = db.table('rbMedicalAidType')
    table = tableAction.leftJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))
    table = table.leftJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
    table = table.leftJoin(tablePerson, tablePerson['id'].eq(tableAction['setPerson_id']))
    table = table.leftJoin(tableSpec, tableSpec['id'].eq(tablePerson['speciality_id']))
    table = table.leftJoin(tableSpecMAP, tableSpecMAP['master_id'].eq(tableSpec['id']))

    table = table.leftJoin(tableKind,  tableKind['id'].eq(tableEventType['medicalAidKind_id']))
    table = table.leftJoin(tableProfile,  tableProfile['id'].eq(tableSpecMAP['medicalAidProfile_id']))
    table = table.leftJoin(tableAidType,  tableAidType['id'].eq(tableEventType['medicalAidType_id']))

    cols = [tableKind['code'].alias('kind'),  tableProfile['federalCode'].alias('profile'),  tableAidType['regionalCode'].alias('type')]
    cond = [tableAction['id'].eq(actionId)]
    record = db.getRecordEx(table,  cols,  cond)
    if record:
        return (forceString(record.value('kind')),  forceString(record.value('profile')),  forceString(record.value('type')))
    return (None, None, None)


def selectFHIROrders(probeIdList):
    db = QtGui.qApp.db
    tableProbe = db.table('Probe')
    tableTakenTissueJournal = db.table('TakenTissueJournal')
    tableAction = db.table('Action')
    tableActionContract = db.table('Contract').alias('ActionContract')
    tableActionType = db.table('ActionType')
    tableActionPropertyType = db.table('ActionPropertyType')
    tablePerson = db.table('Person')
    tableDiagnosis = db.table('Diagnosis')
    tableEvent = db.table('Event')
    tableEventContract = db.table('Contract').alias('EventContract')
    tableEventType = db.table('EventType')
    tableClient = db.table('Client')

    tableActionPropertyTypeJT = db.table('ActionPropertyType').alias('ActionPropertyTypeJT')
    tableActionPropertyJT     = db.table('ActionProperty').alias('ActionPropertyJT')
    tableActionPropertyVJT    = db.table('ActionProperty_Job_Ticket').alias('ActionPropertyVJT')

    tableActionTypeService = db.table('ActionType_Service')
    tableFinance           = db.table('rbFinance')

    table = tableProbe
    table = table.innerJoin(tableTakenTissueJournal, tableTakenTissueJournal['id'].eq(tableProbe['takenTissueJournal_id']))
    table = table.innerJoin(tableAction,     tableAction['takenTissueJournal_id'].eq(tableProbe['takenTissueJournal_id']))
    table = table.innerJoin(tableEvent,      tableEvent['id'].eq(tableAction['event_id']))
    table = table.innerJoin(tableClient,     tableClient['id'].eq(tableEvent['client_id']))
    table = table.innerJoin(tableEventType,  tableEventType['id'].eq(tableEvent['eventType_id']))
    table = table.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
    table = table.innerJoin(tableActionPropertyType, db.joinAnd([ tableActionPropertyType['actionType_id'].eq(tableActionType['id']),
                                                                  tableActionPropertyType['test_id'].eq(tableProbe['test_id']),
                                                                  tableActionPropertyType['deleted'].eq(0)
                                                                ]
                                                               )
                           )
    table = table.innerJoin(tableActionPropertyTypeJT, db.joinAnd([ tableActionPropertyTypeJT['actionType_id'].eq(tableActionType['id']),
                                                                    tableActionPropertyTypeJT['typeName'].eq('JobTicket'),
                                                                    tableActionPropertyTypeJT['deleted'].eq(0)
                                                                  ]
                                                                 )
                           )
    table = table.innerJoin(tableActionPropertyJT, db.joinAnd([ tableActionPropertyJT['action_id'].eq(tableAction['id']),
                                                                tableActionPropertyJT['type_id'].eq(tableActionPropertyTypeJT['id']),
                                                                tableActionPropertyJT['deleted'].eq(0)
                                                              ]
                                                             )
                           )
    table = table.innerJoin(tableActionPropertyVJT, db.joinAnd([ tableActionPropertyVJT['id'].eq(tableActionPropertyJT['id']),
                                                                 tableActionPropertyVJT['index'].eq(0)
                                                               ]
                                                              )
                           )

    table = table.leftJoin(tablePerson,     tablePerson['id'].eq(tableAction['setPerson_id']))
    table = table.leftJoin(tableDiagnosis,   'Diagnosis.id = getEventDiagnosis(Action.event_id)')
    table = table.leftJoin(tableActionContract,  tableActionContract['id'].eq(tableAction['contract_id']))
    table = table.leftJoin(tableEventContract,   tableEventContract['id'].eq(tableEvent['contract_id']))

    cond = [ tableProbe['id'].inlist(probeIdList)
           ]

    financeIdDef = 'COALESCE(%s.finance_id, %s.finance_id, %s.finance_id) AS finance_id' % (
                    tableAction.tableName,
                    tableActionContract.tableName,
                    tableEventContract.tableName )

    recordList = db.getRecordList(table,
                                  [ tableProbe['id'].alias('probe_id'),
                                    tableProbe['externalId'],
                                    tableProbe['takenTissueJournal_id'],
                                    tableProbe['specimenType_id'],
                                    tableProbe['containerType_id'],
                                    tableTakenTissueJournal['datetimeTaken'],
                                    tableTakenTissueJournal['execPerson_id'],
                                    tableAction['id'].alias('action_id'),
                                    tableAction['actionType_id'],
                                    tableActionType['nomenclativeService_id'].alias('service_id'),
                                    tableAction['directionDate'].alias('directionDatetime'),
                                    tableAction['event_id'],
                                    tableEvent['externalId'].alias('eventExternalId'),
                                    tableEvent['eventType_id'],
                                    tableEventType['purpose_id'].alias('eventPurpose_id'),
                                    tablePerson['orgStructure_id'],
                                    tableAction['setPerson_id'],
                                    tableAction['MKB'].alias('actionMKB'),
                                    tableDiagnosis['MKB'].alias('eventMKB'),
                                    financeIdDef,
                                    tableAction['note'],
                                    tableClient['menoPausa'],
                                    tableEvent['pregnancyWeek'],
                                    tableTakenTissueJournal['menstrualDay'],
                                    tableActionPropertyVJT['value'].alias('jobTicket_id'),
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
        collectorId          = forceRef(record.value('execPerson_id'))
        actionId             = forceRef(record.value('action_id'))
        actionTypeId         = forceRef(record.value('actionType_id'))
        serviceId            = forceRef(record.value('service_id'))
        directionDatetime    = forceDateTime(record.value('directionDatetime'))
        eventId              = forceRef(record.value('event_id'))
        eventExternalId      = forceString(record.value('eventExternalId'))
        eventTypeId          = forceRef(record.value('eventType_id'))
        eventPurposeId       = forceRef(record.value('eventPurpose_id'))
        orgStructureId       = forceRef(record.value('orgStructure_id'))
        setPersonId          = forceRef(record.value('setPerson_id'))
        MKB                  = forceString(record.value('actionMKB')) or forceString(record.value('eventMKB')) or 'Z00'
        financeId            = forceRef(record.value('finance_id'))
        note                 = forceString(record.value('note'))
        menopause            = forceBool(record.value('menoPausa'))
        pregnancyWeek        = forceInt(record.value('pregnancyWeek'))
        menstrualDay         = forceInt(record.value('menstrualDay'))
        jobTicketId          = forceRef(record.value('jobTicket_id'))

#        key = (takenTissueJournalId, externalId)
        orderKey = takenTissueJournalId
        order = orderDict.get(orderKey)
        if order is None:
            orderDict[orderKey] = order = COrderDto()
#            order.takenTissueJournalId = takenTissueJournalId
#            order.takenDatetime        = takenDatetime
            order.jobTicketId = jobTicketId

        # Задача 12223. Начало
        tableATS = tableActionTypeService.innerJoin(tableFinance,
                                                    db.joinAnd([tableActionTypeService['master_id'].eq(actionTypeId),
                                                                tableFinance['id'].eq(tableActionTypeService['finance_id'])
                                                               ]
                                                              )
                                                   )

        ActionTypeServiceCond = tableATS['code'].eq('1') # источник финансирования - бюджет
        financeSourceRecord = db.getRecordEx(tableATS,
                                             [tableActionTypeService['id'],
                                              tableFinance['id'].alias('financeIdByActionType')
                                             ],
                                             ActionTypeServiceCond
                                            )
        financeIdByActionType = forceRef(financeSourceRecord.value('financeIdByActionType')) if financeSourceRecord else None
        # Задача 12223. Конец

        order.addProbe(eventId,
                       eventExternalId,
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
                       collectorId,
                       externalId,
                       specimenTypeId,
                       containerTypeId,
                       probeId,
                       financeId,
                       note,
                       menopause,
                       pregnancyWeek,
                       menstrualDay,
                       financeIdByActionType
                      )
    for order in orderDict.itervalues():
        order.updateParams()
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


def dateTimeToFHIRDateNoTZ(dateTime):
    result = FHIRDate()
    if dateTime:
        pdt = dateTime.toPyDateTime()
        result.date = pdt
    return result


class CFHIRExchange:
    misIdentifierUrn  = 'urn:oid:1.2.643.5.1.13.2.7.100.5'  # OID для идентификатора в МИС/ЛИС
    documentTypeUrn   = 'urn:oid:1.2.643.2.69.1.1.1.6'      # OID для разных документов
    documentProviderUrn='urn:netrika:documentProvider'      # УФМС, ЗАГС и т.п.
    snilsUrn          = 'urn:oid:1.2.643.2.69.1.1.1.6.223'  # OID ПФР для СНИЛСа
    oldPolicyUrn      = 'urn:oid:1.2.643.2.69.1.1.1.6.226'  # OID для страхового полиса ОМС старого образца
    TempPolicyUrn      = 'urn:oid:1.2.643.2.69.1.1.1.6.227'  # OID для временного свидетельства
    newPolicyUrn      = 'urn:oid:1.2.643.2.69.1.1.1.6.228'  # OID для страхового полиса ОМС единого образца
    volPolicyUrn      = 'urn:oid:1.2.643.2.69.1.1.1.6.240'  # OID для страхового полиса ДМС

    orgUrn            = 'urn:oid:1.2.643.2.69.1.1.1.64'     # кодификатор организаций
    hicRegistryUrn    = 'urn:oid:1.2.643.5.1.13.2.1.1.635'  # Реестр СМО (ФФОМС)
    hicRegistryOid    = '1.2.643.5.1.13.2.1.1.635'          # Реестр СМО (ФФОМС)

    specialityUrn     = 'urn:oid:1.2.643.5.1.13.13.11.1066' # Специальности
    socStatusUrn      = 'urn:oid:1.2.643.5.1.13.13.11.1038' # Занятость
    baseReferalBioResearchUrn = 'urn:oid:1.2.643.2.69.1.1.1.175'  # Основание для направления биоматериала на исследование
    fhirIdentifierTypes = 'urn:oid:1.2.643.2.69.1.1.1.122'  # Типы идентификаторов FHIR
    namespaceEpidCaseIdent = 'urn:oid:1.2.643.5.1.13.2.7.100.6' # Пространство имен идентификатора для эпидномера
    roleUrn           = 'urn:oid:1.2.643.5.1.13.13.11.1002' # Роли (Должности)
    reasonUrn         = 'urn:oid:1.2.643.2.69.1.1.1.19'     # Назначение события
    serviceUrn        = 'urn:oid:1.2.643.2.69.1.1.1.31'     # Услуги
    specimenTypeUrn   = 'urn:oid:1.2.643.5.1.13.13.11.1081' # типы образцов
    containerTypeUrn  = 'urn:oid:1.2.643.2.69.1.1.1.34'     # типы контейнеров
    # ppch: pathological process character
    ppchUrn           = 'urn:oid:1.2.643.5.1.13.13.99.2.34' # характер патологического процесса в биопсийном (операционном) материале для прижизненного патолого-анатомического исследования
    ppchVersion       = '1'
    # ppl: pathological process localization
    pplUrn            = 'urn:oid:1.2.643.2.69.1.1.1.102'    # локализация патологического процесса
    pplVersion        = '2'
    # cmfc: collection method for cytology
    cmfcUrn           = 'urn:oid:1.2.643.2.69.1.1.1.152'    # Способ получения материала для цитологического исследования
    cmfcVersion       = '1'
    # cmfg: collection method for histology
    cmfgUrn           = 'urn:oid:1.2.643.5.1.13.13.99.2.33' # Способ получения биопсийного (операционного) материала для прижизненного патолого-анатомического исследования
    cmfgVersion       = '1'

    sampleProcessingFeaturesUrn = 'urn:oid:1.2.643.2.69.1.1.1.97'   # Особенности обработки при сборе, транспортировке или хранении образца
    spfVersion                  = '3'

    typesOfSRDForPAOUrn     = 'urn:oid:1.2.643.5.1.13.13.99.2.35' # Виды окрасок, реакций, определений для патолого-анатомических исследований
    typesOfSRDForPAOVersion = '2'

    PAOMaterialCategoriesUrn = 'urn:oid:1.2.643.5.1.13.13.99.2.36' # Категории сложности прижизненного патолого-анатомического исследования биопсийного (операционного) материала
    PAOMaterialCategoriesVersion = '1'

    caseTypeUrn        = 'urn:oid:1.2.643.2.69.1.1.1.35'    # Тип случая обслуживания
    caseTypeVersion    = '1'
    caseTypePolyclinic      = '2'
    caseTypeDispObservation = '4'

    conditionUrn      = 'urn:oid:1.2.643.2.69.1.1.1.36'     # типы Condition
    conditionDiagnosis= 'diagnosis'
    conditionFinding  = 'finding'
    conditionVersion  = '1'

    ICDUrn            = 'urn:oid:1.2.643.2.69.1.1.1.2'      # Коды диагнозов по МКБ
    ICDVersion        = ''

    ICDOncoMorphologyUrn     = 'urn:oid:1.2.643.5.1.13.13.11.1486' # МКБ – Онкология (3 издание). Морфологические коды
    ICDOncoMorphologyVersion = ''

    ICDOncoTopologyUrn     = 'urn:oid:1.2.643.5.1.13.13.11.1487'   # МКБ – Онкология (3 издание). Топографические коды
    ICDOncoTopologyVersion = ''

    findingUrn                  = 'urn:oid:1.2.643.2.69.1.1.1.39'     # Condition категории finding
    findingMenopause            = '1'
    findingLastMenstruationDate = '2'
    findingVersion              = '2'

#
    interpretationUrn = 'urn:oid:1.2.643.5.1.13.13.11.1381'
    interpretationVersion = ''
    mapEvaluationToInterpretation = { None: 'IND',
                                      -2  : 'LU',
                                      -1  : 'L',
                                       0  : 'N',
                                      +1  : 'H',
                                      +2  : 'HU',
                                    }

    unitUrn           = 'urn:oid:1.2.643.5.1.13.13.11.1358' # Единицы измерения
    financeUrn        = 'urn:oid:1.2.643.2.69.1.1.1.32'     # Источники финансирования
    financeDefault    = '6'
    financeVersion    = ''

    orderParamUrn          = 'urn:oid:1.2.643.2.69.1.1.1.37'# Разные параметры заказа, Observation
    orderParamVersion      = '2'
    orderParamHeight                       = '1' # Рост
    orderParamWeight                       = '2' # Вес
    orderParamPregnancyWeek                = '3' # Неделя беременности
    orderParamMenstrualDay                 = '4' # День цикла
    orderParamTaskPAO                      = '5' # Задача паталого-анатомического исследования
    orderParamAnamnesis                    = '6' # Дополнительные клинические сведения
    orderParamnstrumentalInvestigationData = '7' # Результаты предыдущих исследований
    orderParamPAOData                      = '7' # Результаты предыдущих паталого-анатомических исследований
    orderParamTreatment                    = '8' # Проведенное лечение
    orderParamPreoperativeTreatment        = '8' # Проведенное предоперационное лечение
    orderParamEpidAnamnesis                = '9' # Эпид. анамнез
    orderParamORVISymptomsDate             = '11' # Дата появления симптомов респираторного заболевания
    orderParamAskForMedicineDate           = '12' # Дата обращения за медицинской помощью по данному заболеванию
    orderParamConditionBeforeMedicineDate  = '13' # Состояние при обращении за медицинской помощью по данному заболеванию
    orderParamComplications                = '14' # Осложнения
    orderParamHospitalizationDate          = '15' # Дата госпитализации при обращении за медицинской помощью по данному заболеванию
    orderParamMultipleBirths               = '166.380' # Номер новорожденного в родах
    orderParamNewbornWeight                = '166.410' # Масса тела ребёнка при рождении
    orderParamGestationalAge               = '166.6077' # Срок беременности (в днях)
    orderParamTransDateFlag                = '166.12415.1' # Факт переливания крови новорожденному
    orderParamTransDate                    = '166.12415.2' # Дата переливания крови новорожденному
    orderParamRepeatReason                 = '166.12520.1' # Причина повторного исследования


    cytologyResultUrn         = 'urn:oid:1.2.643.2.69.1.1.1.151'
    histologyResultUrn        = 'urn:oid:1.2.643.2.69.1.1.1.101' # Справочник результатов гистологических исследований
    histologyResultVersion    = '1'
#    histologyResultCutting    = '1'
#    histologyResultMacroDescr = '3'

    aidProfileUrn = 'urn:oid:1.2.643.2.69.1.1.1.156' # Профиль мед помощи
    aidTypeUrn = 'urn:oid:1.2.643.2.69.1.1.1.157' # Классификатор условий оказания медицинской помощи
    aidKindUrn = 'urn:oid:1.2.643.2.69.1.1.1.158' # Классификатор видов медицинской помощи
    aidFormUrn = 'urn:oid:1.2.643.2.69.1.1.1.159' # Классификатор форм оказания медицинской помощи

    codeN3PatientIdentification = 'n3.patient'
    orderProfile       = 'StructureDefinition/cd45a667-bde0-490f-b602-8d780acf4aa2'
    resultProfile      = 'StructureDefinition/21f687dd-0b3b-4a7b-af8f-04be625c0201'

    # Разрешенные диапазоны кодов документов по справочнику нетрики 1.2.643.2.69.1.1.1.6
    validDocCodesN3 = {'validID':    [1, 18],    # это диапазон: числа от 1 до 18
                       'validOMS':   [226, 228], # это диапазон: числа от 226 до 228
                       'validDMS':   [240, 240], # это диапазон: числа от 240 до 240
                       'validSNILS': [223, 223], # это диапазон: числа от 223 до 223
                       'validBirthDoc': [249, 249]
                     }

    def __init__(self, opts, orgId, orgStructureDescr=None, sourceOrgStructureDescr=None):
        self.url            = self.getOpt(opts, 'url',  u'URL Сервиса ОДЛИ')
        self.terminologyUrl = self.getOpt(opts, 'terminology_url',  u'URL Сервиса терминологии') # , 'http://r78-rc.zdrav.netrika.ru/Terminology/term')
        self.authorization  = self.getOpt(opts, 'authorization',  u'Значение заголовка авторизации')
#        self.terminologyAuthorization  = self.getOpt(opts, 'terminologyAuthorization',  u'Значение заголовка авторизации',  '')
        target              = self.getOpt(opts, 'target',  u'GUID лаборатории')
        self.SAMSON         = self.getOpt(opts, 'mis_oid', u'OID МИС')
        self.testUrn        = self.getOpt(opts, 'tests_urn', u'URN справочника тестов')
        self.testVersion    = self.getOpt(opts, 'tests_version', u'Версия справочника тестов', '')
        self.arkhangelskEncounter = opts.get('arkhangelskEncounter',  False)

        self._createParams = None
        if 'createParams' in opts:
            self._createParams = opts['createParams']

        if not sourceOrgStructureDescr:
            self.sourceOrgShortCode = forceString(QtGui.qApp.db.translate('Organisation', 'id', orgId, 'infisCode'))
            self.sourceOrgCode  = getIdentification('Organisation', orgId, self.orgUrn)
            self.sourceOrg = self.createOrganization(self.sourceOrgCode)
        else:
            self.sourceOrgShortCode = sourceOrgStructureDescr.code
            self.sourceOrgCode = sourceOrgStructureDescr.identification
            self.sourceOrg = self.createOrganization(self.sourceOrgCode)
        self.sourceOrgReference = self.createReference(self.sourceOrg)

        if not orgStructureDescr:
            self.orgShortCode = forceString(QtGui.qApp.db.translate('Organisation', 'id', orgId, 'infisCode'))
            self.orgCode  = getIdentification('Organisation', orgId, self.orgUrn)
            self.org = self.createOrganization(self.orgCode)
        else:
            self.orgShortCode = orgStructureDescr.code
            self.orgCode = orgStructureDescr.identification
            self.org = self.createOrganization(self.orgCode)

        self.mainOrgShortCode = forceString(QtGui.qApp.db.translate('Organisation', 'id', orgId, 'infisCode'))
        self.mainOrgCode = getIdentification('Organisation', orgId, self.orgUrn)
        self.mainOrg = self.createOrganization(self.mainOrgCode)
        if target:
            self.lab = self.createOrganization(target)
        else:
            self.lab = None

        settings = { 'api_base': self.url,
                     'app_id'  : 'samson/0.1',
                     'headers' : { 'Authorization' : self.authorization,},
#                     'conformance' : Conformance,
                     'conformance' : None,
                   }

        self.smart = client.FHIRClient(settings=settings)
        self.smart.prepare()

        self._terminologyClient = None

        self.orgReference = self.createReference(self.org)
        self.mainOrgReference = self.createReference(self.mainOrg)
        if self.lab:
            self.labReference = self.createReference(self.lab)
        else:
            self.labReference = None

        self._mapPolicyTypeIdToComp = {}
        self._mapPolicyTypeCompToId = {}
        self._mapPolicyKindIdToCode = {}
        self._mapPolicyKindCodeToId = {}
        self._mapUnitIdentificationToId = {}
        self._mapUriToVersion = downloadVersionsOfDictionaries(self.getTerminologyClient())

        self.isInsurerCodeIs99 = None
        self.isDMSInsurerCodeIs99 = None

        self.mapPersonIdToPractitionerReference = {}
        self.orgCache = {}


    def getOpt(self, opts, param, title, default=None):
        if param in opts:
            result = opts.get(param)
            return result
        if default is None:
            raise Exception(u'Не задано значение параметра %s (%s)' % (param, title))
        return default


    def getTerminologyClient(self):
        if self._terminologyClient is None:
            settings = { 'api_base': self.terminologyUrl,
                         'app_id'  : 'samson/0.1',
                         'headers' : { 'Authorization' : self.authorization,},
#                 'conformance' : Conformance,
                         'conformance' : None,
                       }
#            if self.terminologyAuthorization:
#                settings['headers'] = { 'Authorization' : self.terminologyAuthorization,}

            self._terminologyClient = client.FHIRClient(settings=settings)
            self._terminologyClient.prepare()
        return self._terminologyClient


    def _getPolicyTypeComp(self, policyTypeId):
        result = self._mapPolicyTypeIdToComp.get(policyTypeId)
        if result is None:
            result = forceBool(QtGui.qApp.db.translate('rbPolicyType', 'id', policyTypeId, 'isCompulsory'))
            self._mapPolicyTypeIdToComp[policyTypeId] = result
        return result


    def _getPolicyTypeId(self, isComp):
        result = self._mapPolicyTypeCompToId.get(isComp)
        if result is None:
            result = forceRef(QtGui.qApp.db.translate('rbPolicyType', 'isCompulsory', isComp, 'id'))
            self._mapPolicyTypeCompToId[isComp] = result
        return result


    def _getPolicyKindCode(self, policyKindId):
        code = self._mapPolicyKindIdToCode.get(policyKindId)
        if code is None:
            code = forceString(QtGui.qApp.db.translate('rbPolicyKind', 'id', policyKindId, 'code'))
            self._mapPolicyKindIdToCode[policyKindId] = code
        return code


    def _getPolicyKindId(self, policyKindCode):
        code = self._mapPolicyKindCodeToId.get(policyKindCode)
        if code is None:
            policyKindId = forceRef(QtGui.qApp.db.translate('rbPolicyKind', 'code', policyKindCode, 'id'))
            if policyKindId is None:
                raise Exception(u'В справочнике rbPolicyKind не найдена запись с кодом «%s»' % policyKindCode)

            self._mapPolicyKindCodeToId[policyKindCode] = policyKindId
        return code

    def _guessPolicyKindCode(self, serial, number):
        if number.isdigit():
            if ( not serial or serial.upper() == u'ЕП') and len(number) == 16:
                return '3'
            if ( not serial or serial.upper() == u'ВР') and len(number) == 9:
                return '2'
            if len(serial)>1 and len(number)>=6:
                return '1'
        return None


    def createReference(self, resource):
        if resource.id is None:
            resp = resource.create(self.smart.server)
            resource.update_with_json(resp)
        reference = FHIRReference()
        reference.reference =  '%s/%s' % (resource.resource_name, resource.id)
        return reference


    def createDispReference(self, display):
        reference = FHIRReference()
        reference.display = display
        return reference


    def newBundleReference(self, url):
        reference = FHIRReference()
        reference.reference = url
        return reference


    def createIdentifier(self, system, value, assigner=None, use=None):
        identifier = Identifier()
        identifier.system = system
        identifier.value  = value
        identifier.assigner = assigner
        if use:
            identifier.use = use
        return identifier


    def createPPMisIdentifier(self, value):
        return self.createIdentifier(self.misIdentifierUrn,
                                     'SAMSON:%s:%s' % (self.mainOrgShortCode, value),
                                     self.createDispReference(self.SAMSON)
                                    )


    def createPerformerMisIdentifier(self, value):
         return self.createIdentifier(self.misIdentifierUrn,
                                     'SAMSON:%s:%s' % (self.orgShortCode, value),
                                     self.createDispReference(self.SAMSON)
                                    )


    def createMisIdentifier(self, value):
        return self.createIdentifier('urn:oid:%s' % self.SAMSON,
                                     '%s:%s' % (self.orgShortCode, value),
                                     self.orgReference
                                    )


    def createEpidNumberIdentifier(self, epidCase):
        identifier = Identifier()
        identifier.type = self.createCodeableConcept(self.fhirIdentifierTypes, 'RRI', '1')
        identifier.system = self.namespaceEpidCaseIdent
        identifier.value = epidCase['epidNumber']
        identifier.assigner = self.createOrganizationReference(epidCase['regOrgId'])
        return identifier


    def createCoding(self, system, code, version):
        coding = Coding()
        coding.system=system
        coding.code=code
#        coding.version=version
#        coding.version=''
        coding.version = self._mapUriToVersion.get(system, version)
        return coding


    def createCodeableConcept(self, system, code, version):
        codeableConcept = CodeableConcept()
        codeableConcept.coding = [ self.createCoding(system,
                                                     code,
                                                     version
                                                    )
                                 ]
        return codeableConcept


    def createContactPoint(self, system, use, value):
        contactPoint = ContactPoint()
        contactPoint.system = system
        contactPoint.use = use
        contactPoint.value = value
        return contactPoint


    def getUnitCodeAndName(self, unitId):
        unitCode, unitVersion = getIdentificationEx('rbUnit', unitId, self.unitUrn)
        unitName = forceString(QtGui.qApp.db.translate('rbUnit', 'id', unitId, 'code'))
        return unitCode, unitName


    def createQuantity(self, quantity):
        result = Quantity()
        if isinstance(quantity, tuple):
            value, unitId = quantity
        else:
            value, unitId = quantity, None

        result.value = float(value)
        if unitId:
            result.system = self.unitUrn
            result.code, result.unit = self.getUnitCodeAndName(unitId)
        return result


    def createOrganization(self, fhirId):
        org = Organization()
        org.id = fhirId
        return org


    def createOrgStructureReference(self, orgStructureId):
        if orgStructureId:
            fhirId = getOrgStructureIdentification(orgStructureId, self.orgUrn)
            return self.createReference(self.createOrganization(fhirId))
        return self.orgReference


    def createOrganizationReference(self, orgId):
        if orgId:
            try:
                fhirId = getOrganizationIdentification(self.orgUrn, orgId)
            except CIdentificationException:
                QtGui.qApp.logCurrentException()
                fhirId = ''
        else:
            fhirId = ''
        reference = self.createReference(self.createOrganization(fhirId))
        reference.display = u'Эпидномер'
        return reference


##проверить!
#    def searchByIdentifier(self, cls, identifier):
#        identifierStr = ('%s|%s' % (identifier.system,identifier.value)).encode('utf8')
#        searchObject = cls.where({'identifier': identifierStr})
#        searchBundle = searchObject.perform(self.smart.server)
#        return searchBundle


    def checkDocCode(self, code):
        if self.validDocCodesN3['validID'][0] <= int(code) <= self.validDocCodesN3['validID'][1]:
            return code
        elif self.validDocCodesN3['validOMS'][0] <= int(code) <= self.validDocCodesN3['validOMS'][1]:
            return code
        elif self.validDocCodesN3['validDMS'][0] <= int(code) <= self.validDocCodesN3['validDMS'][1]:
            return code
        elif self.validDocCodesN3['validSNILS'][0] <= int(code) <= self.validDocCodesN3['validSNILS'][1]:
            return code
        elif self.validDocCodesN3['validBirthDoc'][0] <= int(code) <= self.validDocCodesN3['validBirthDoc'][1]:
            return code
        else:
            return None


    def documentAsIdentifier(self, documentRecord):
        serial = forceString(documentRecord.value('serial'))
        number = forceString(documentRecord.value('number'))
        documentTypeId = forceString(documentRecord.value('documentType_id'))
        date = forceDate(documentRecord.value('date'))
        code = None
        try:
            code, version = getIdentificationEx('rbDocumentType', documentTypeId, self.documentTypeUrn, True)
        except:
            QtGui.qApp.logCurrentException()

        if code:
            code = self.checkDocCode(code)
            if code is None:
                return None

        if serial and number and code:
            # provider, version = getIdentificationEx('rbDocumentType', documentTypeId, self.documentProviderUrn, False)
            # if provider is None:
            if code == '14':
                provider = u'УФМС'
            elif code == '3':
                provider = u'ЗАГС'
            else:
                provider = u'-'
            number = number.replace(' ','').replace('-','')
            serial = serial.replace(' ','').replace('-','')
            document = ('%s:%s' % (serial, number)) if serial else number
            identifier = self.createIdentifier('%s.%s' % (self.documentTypeUrn, code),
                                               document,
                                               self.createDispReference(provider))
            if date:
                identifier.period = Period()
                identifier.period.start = dateToFHIRDate(date)
            return identifier
        return None


    def snilsAsIdentifier(self, snils):
        identifier = self.createIdentifier(self.snilsUrn,
                                           snils,
                                           self.createDispReference(u'ПФР'))
        return identifier


    def policyAsIdentifier(self, clientId, policyRecord):
        insurerId = forceRef(policyRecord.value('insurer_id'))
        serial    = forceString(policyRecord.value('serial'))
        number    = forceString(policyRecord.value('number'))
        begDate   = forceDate(policyRecord.value('begDate'))
        endDate   = forceDate(policyRecord.value('endDate'))
        # if insurerId is None:
        #     raise Exception(u'У пациента Client.id=%s\n'
        #                     u'в полисе серия:«%s», номер: «%s»\n'
        #                     u'не указана страховая компания' % (clientId, serial, number))
        #     return None
        insurerCode = getIdentification('Organisation', insurerId, self.hicRegistryUrn) if insurerId else None
        policyTypeComp = self._getPolicyTypeComp(forceRef(policyRecord.value('policyType_id')))
        if policyTypeComp:
            policyKindCode = self._getPolicyKindCode(forceRef(policyRecord.value('policyKind_id')))
            if not policyKindCode:
                policyKindCode = self._guessPolicyKindCode(serial, number)
            if policyKindCode == '1':  # старый
                system = self.oldPolicyUrn
            elif policyKindCode == '2':  # временный
                system = self.newPolicyUrn
            elif policyKindCode == '3':  # новый
                system = self.newPolicyUrn
            else:
                return None
            # Задача 12223. Код 99 по идентификации для СМО существуют для того,
            # чтобы можно было отделить забытую идентификацию(ненастроенную) от идентификации для пациента с полисом СМО, которой нет в реестре
            if insurerCode == '99':
                self.isInsurerCodeIs99 = True
                return None
            # Задача 12223: также у пациента может быть номер и дата выдачи полиса, но при этом СМО может не быть указанной(нет insurer_id).
            # В таком случае должно выполняться то же условие - у такого пациента заявки должны уходить с финансовым кодом 'бюджет'.
            # Оно выполниться при том же условии self.isInsurerCodeIs99 = True
            if not insurerId:
                if number and begDate:
                    self.isInsurerCodeIs99 = True
                    return None
                if not number or not begDate:
                    raise Exception(u'У пациента Client.id=%s\n'
                                    u'в полисе серия:«%s», номер: «%s»\n'
                                    u'не указана страховая компания, номер или дата выдачи' % (clientId, serial, number))
        else:
            if insurerCode == '99':
                self.isDMSInsurerCodeIs99 = True
                return None
            if not insurerId:
                if number and begDate:
                    self.isDMSInsurerCodeIs99 = True
                    return None
                if not number or not begDate:
                    raise Exception(u'У пациента Client.id=%s\n'
                                    u'в полисе серия:«%s», номер: «%s»\n'
                                    u'не указана страховая компания, номер или дата выдачи' % (clientId, serial, number))
            system = self.volPolicyUrn

        value = number if system == self.newPolicyUrn else '%s:%s' % (serial, number)
        if value[0] == ':':
            value = value[1:]
        identifier = self.createIdentifier(system,
                                           value,
                                           self.createDispReference('%s.%s' % (self.hicRegistryOid, insurerCode)))
        if begDate or endDate:
            identifier.period = Period()
            if begDate:
                identifier.period.start = dateToFHIRDate(begDate)
            if endDate:
                identifier.period.end = dateToFHIRDate(endDate)
        return identifier


    def createPatientContact(self, workRelationship):
        contact = PatientContact()
        code = ''
        socStatusRecord = None
        workRecord = None
        if 'workRecord' in workRelationship:
            workRecord = workRelationship['workRecord']
        if 'socStatusRecord' in workRelationship:
            socStatusRecord = workRelationship['socStatusRecord']
        if socStatusRecord:
            socStatusTypeId = forceRef(socStatusRecord.value('socStatusType_id'))
            try:
                identValue = getIdentification('rbSocStatusType', socStatusTypeId, self.socStatusUrn)
                if workRecord or identValue == '5':
                    code = 5
                elif identValue == '3':
                    code = 3
                elif identValue == '4':
                    code = 4
                else:
                    code = ''
            except CIdentificationException:
                QtGui.qApp.logCurrentException()
                code = 5 if workRecord else ''

        if code:
            relationship = self.createCodeableConcept(self.socStatusUrn, str(code), '1')
            socStatusName = QtGui.qApp.db.translate('rbSocStatusType', 'id', socStatusTypeId, 'name').toString()
            relationship.text = unicode(socStatusName) if socStatusName else ''
            contact.relationship = [ relationship ]

        if workRecord:
            orgId = forceRef(workRecord.value('org_id'))
            freeInput = forceString(workRecord.value('freeInput'))
            if orgId:
                orgShortName = getOrganisationShortName(orgId)
                workAddress = unicode(QtGui.qApp.db.translate('Organisation', 'id', orgId, 'Address').toString())
                contact.address = self.createClientWorkAddress(workAddress)
                contact.organization = self.createDispReference(orgShortName)
            elif freeInput:
                contact.address = self.createClientWorkAddress(freeInput)
                contact.organization = self.createDispReference(freeInput)

        return contact


    def createClientWorkAddress(self, workAddress):
        address = Address()
        address.text = workAddress
        address.use = 'work'
        return address


    def createPatientTelecom(self, contacts):
        result = []
        for contactValueList in contacts:
            contactValue = contactValueList[1]
            cotactTypeCode = contactValueList[3]
            if cotactTypeCode in ['1', '2', '3'] and contactValue:
                system = 'phone'
                value = contactValue
                if cotactTypeCode == '1':
                    use = 'home'
                elif cotactTypeCode == '2':
                    use = 'work'
                elif cotactTypeCode == '3':
                    use = 'mobile'
                contactPoint = self.createContactPoint(system, use, value)
                result.append(contactPoint)

            if cotactTypeCode == '4' and contactValue:
                system = 'email'
                value = contactValue
                use = 'work'
                contactPoint = self.createContactPoint(system, use, value)
                result.append(contactPoint)

        return result


    def createPatient(self, clientInfo, representativeInfo=None, isNeonatal=False):
        patient = Patient()
        patient.active = True
        name = HumanName()
        name.family = [clientInfo.lastName]
        if clientInfo.patrName:
            name.family.append(clientInfo.patrName)
        if isNeonatal:
            name.given = [u'Новорожденный']
            name.text = formatNameInt(clientInfo.lastName, u'Новорожденный', u'')
        else:
            name.given = [clientInfo.firstName or '-']
            name.text = formatNameInt(clientInfo.lastName, clientInfo.firstName, clientInfo.patrName)
        name.use = 'official'
        patient.name = [name]
        patient.gender = {1: 'male', 2: 'female'}.get(clientInfo.sexCode, 'undefined')
        patient.birthDate = dateToFHIRDate(clientInfo.birthDate)

        patient.identifier = [self.createPPMisIdentifier(clientInfo.id)]
        if clientInfo.documentRecord:
            documentAsIdentifier = self.documentAsIdentifier(clientInfo.documentRecord)
            if documentAsIdentifier is not None:
                patient.identifier.append(documentAsIdentifier)
        if clientInfo.SNILS:
            snils = clientInfo.SNILS.replace('-', '').replace(' ', '')
            patient.identifier.append(self.snilsAsIdentifier(snils))
        if clientInfo.compulsoryPolicyRecord:
            policyAsIdentifier = self.policyAsIdentifier(clientInfo.id, clientInfo.compulsoryPolicyRecord)
            if policyAsIdentifier:
                patient.identifier.append(policyAsIdentifier)
        if clientInfo.voluntaryPolicyRecord:
            policyAsIdentifier = self.policyAsIdentifier(clientInfo.id, clientInfo.voluntaryPolicyRecord)
            if policyAsIdentifier:
                patient.identifier.append(policyAsIdentifier)
        # if clientInfo.workRelationship:
        #     patientContact = self.createPatientContact(clientInfo.workRelationship)
        #     if patientContact:
        #         patient.contact = [ patientContact ]
        if clientInfo.epidCase:
            epidCaseIdentifier = self.createEpidNumberIdentifier(clientInfo.epidCase)
            patient.identifier.append(epidCaseIdentifier)

        if clientInfo.contacts:
            telecom = self.createPatientTelecom(clientInfo.contacts)
            if telecom:
                patient.telecom = telecom

        locAddressText = clientInfo.get('locAddress')
        regAddressText = clientInfo.get('regAddress')

        patient.address = []
        if locAddressText:
            locAddress = Address({'use': 'home', 'text': locAddressText})
            patient.address.append(locAddress)
        if regAddressText:
            regAddress = Address({'use': 'temp', 'text': regAddressText})
            patient.address.append(regAddress)
        patient.managingOrganization = self.mainOrgReference
        if representativeInfo:
            name.use = 'temp'
            e = Extension()
            e.url = 'http://hl7.org/fhir/StructureDefinition/patient-birthTime'
            e.valueDateTime = dateTimeToFHIRDateNoTZ(QDateTime(clientInfo.get('birthDate'), clientInfo.get('birthTime')))
            patient.extension = [e]
            relatedPatient = self.createPatient(representativeInfo)
            link = PatientLink()
            link.other = self.createReference(relatedPatient)
            link.type = 'refer'
            patient.link = [link]
        if not patient.id:
            resp = patient.create(self.smart.server)
            assert resp['resourceType'] == 'Patient'
            patient.update_with_json(resp)
        else:
            patient.update(self.smart.server)

        return patient


    def createAnonimPatient(self, clientInfo):
        patient = Patient()
        patient.active = True
        name = HumanName()
        name.family = [u'Анонимный', u'Анонимный']
        name.given = [u'Анонимный']
        name.text = u'Анонимный'
        name.use = 'anonymous'
        patient.name = [name]
        patient.gender = {1: 'male', 2: 'female'}.get(clientInfo.sexCode, 'undefined')
        patient.birthDate = dateToFHIRDate(clientInfo.birthDate)

        patient.identifier = [self.createPPMisIdentifier(clientInfo.id),  # идентификатор в МИС
                              #                               self.createMisIdentifier(clientInfo.id),
                              ]

        patient.managingOrganization = self.mainOrgReference
        # resp = patient.create(self.smart.server)
        # assert resp['resourceType'] == 'Patient'
        # patient.update_with_json(resp)
        return patient


    def newPractitioner(self, personId):
        db = QtGui.qApp.db
        record = db.getRecord('Person',
                             ('lastName','firstName','patrName','SNILS','post_id', 'code','speciality_id','orgStructure_id'),
                             personId
                             )
        lastName  = forceString(record.value('lastName'))
        firstName = forceString(record.value('firstName'))
        patrName  = forceString(record.value('patrName'))
        snils     = forceString(record.value('SNILS'))
        postId    = forceRef(record.value('post_id'))
        pcode     = forceString(record.value('code'))
        specialityId = forceRef(record.value('speciality_id'))
        if QtGui.qApp.practitionerOrganisationOnly:
            orgStructureId = None
        else:
            orgStructureId = forceRef(record.value('orgStructure_id'))
            if orgStructureId is None:
                raise Exception(u'Для Person.id=%d (код: %s) не указано подразделение' % (personId, pcode))
        specialityCode, specialityVersion = getIdentificationEx('rbSpeciality',
                                                                specialityId,
                                                                self.specialityUrn,
                                                                raiseIfNonFound=False
                                                               )
        postCode,       postVersion       = getIdentificationEx('rbPost',
                                                                postId,
                                                                self.roleUrn,
                                                                raiseIfNonFound=False
                                                               )
        practitioner = Practitioner()
        practitioner.active = True
        name = HumanName()
        name.family = [ lastName or '-', patrName or '-' ]
        name.given  = [ firstName or '-' ]
        name.text   = formatNameInt(lastName, firstName, patrName)
        practitioner.name = name

        practitioner.identifier = [ self.createPerformerMisIdentifier(personId),  # идентификатор в МИС
#                                    self.createMisIdentifier(personId),
                                  ]
        if snils:
            practitioner.identifier.append(self.snilsAsIdentifier(snils))

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

        practitioner.practitionerRole = [ ppr ]
        return practitioner


    def newConditionFromLastMenstruationDate(self, patientReference, date):
        condition = Condition()
        condition.patient = patientReference
        condition.category = self.createCodeableConcept(self.conditionUrn,
                                                        self.conditionFinding,
                                                        self.conditionVersion
                                                       )
        condition.code = self.createCodeableConcept(self.findingUrn,
                                                    self.findingLastMenstruationDate,
                                                    self.findingVersion
                                                   )
        condition.dateRecorded = dateToFHIRDate(date)
        condition.verificationStatus = 'confirmed'
        return condition


    def newConditionFromMenopause(self, patientReference):
        condition = Condition()
        condition.patient = patientReference
        condition.category = self.createCodeableConcept(self.conditionUrn,
                                                        self.conditionFinding,
                                                        self.conditionVersion
                                                       )
        condition.code = self.createCodeableConcept(self.findingUrn,
                                                    self.findingMenopause,
                                                    self.findingVersion
                                                   )
        condition.verificationStatus = 'confirmed'
        return condition


    def newConditionFromDiagnosis(self, patientReference, diagnosisCode):
        condition = Condition()
        condition.patient = patientReference
        condition.category = self.createCodeableConcept(self.conditionUrn,
                                                        self.conditionDiagnosis,
                                                        self.conditionVersion
                                                       )
        condition.code = self.createCodeableConcept(self.ICDUrn,
                                                    diagnosisCode,
                                                    self.ICDVersion
                                                   )
        condition.verificationStatus = 'confirmed'
        return condition


    def newEncounter(self, patientReference, eventId, externalId, eventTypeId, eventPurposeId, orgStructureId, diagnosisList, medicalAidTypeId=None):
        u"""
        Ресурс Encounter предназначен для передачи информации о случае обслуживания и ссылок на диагнозы пациента.
        """
        if medicalAidTypeId:
            typeCode, typeVersion = getIdentificationEx('rbMedicalAidType', medicalAidTypeId, self.caseTypeUrn, False)
        else:
            typeCode, typeVersion = getIdentificationEx('EventType', eventTypeId, self.caseTypeUrn, False)
            if typeCode is None:
                typeCode, typeVersion = getIdentificationEx('rbEventTypePurpose', eventPurposeId, self.caseTypeUrn, False)
        if typeCode is None:
            typeCode, typeVersion = self.caseTypePolyclinic, self.caseTypeVersion

        reasonCode, reasonVersion = getIdentificationEx('EventType', eventTypeId, self.reasonUrn, False)
        if reasonCode is None:
            reasonCode, reasonVersion = getIdentificationEx('rbEventTypePurpose',
                                                            eventPurposeId,
                                                            self.reasonUrn,
                                                            False
                                                            )

        encounter = Encounter()
        # Идентификатор случая обслуживания в МИС
        identifier = self.createIdentifier('urn:oid:%s' % self.SAMSON,
                                           '%s:%s' % (self.orgShortCode, eventId),
                                           )
        identifier.assigner = self.orgReference
        identifier.assigner.display = externalId or eventId
        encounter.identifier = [identifier]
        encounter.status = 'in-progress'  # Статус случая обслуживания
        encounter.class_fhir = 'ambulatory'  # Класс случая обслуживания !!!
        encounter.type = [self.createCodeableConcept(self.caseTypeUrn, typeCode, typeVersion)]  # Тип случая обслуживания
        encounter.patient = patientReference  # Соотнесение с пациентом
        if reasonCode:  # Цель посещения
            encounter.reason = [self.createCodeableConcept(self.reasonUrn, reasonCode, reasonVersion)]
        encounter.indication = diagnosisList  # Соотнесение с диагнозами пациента
        encounter.serviceProvider = self.createOrgStructureReference(orgStructureId)  # Соотнесение с кодом МО (или отделения).
        return encounter


    def newSpecimen(self,
                       patientReference,
                       specimenTypeId,
                       containerTypeId,
                       externalId,
                       takenDatetime,
                    collectorReference,
                    probeId,
                    orderParams
                      ):
        containerTypeCode, containerTypeVersion = getIdentificationEx('rbContainerType',
                                                                      containerTypeId,
                                                                      self.containerTypeUrn,
                                                                     )
        specimenTypeCode, specimenTypeVersion = getIdentificationEx('rbSpecimenType',
                                                                    specimenTypeId,
                                                                    self.specimenTypeUrn
                                                                   )
        specimen = Specimen()
#        specimen.identifier = [ self.createMisIdentifier(probeId) ]
        specimen.subject = patientReference
        ppchCode = orderParams.getCode('Specimen:type')
        if ppchCode: # Характер патологического процесса
            specimen.type = self.createCodeableConcept(self.ppchUrn,
                                                       ppchCode,
                                                       self.ppchVersion)
        else: # тип биоматериала
            specimen.type = self.createCodeableConcept(self.specimenTypeUrn,
                                                   specimenTypeCode,
                                                   specimenTypeVersion)

        specimen.collection = collection = SpecimenCollection()
        collection.collectedDateTime = dateTimeToFHIRDate(takenDatetime)
        collection.collector = collectorReference
        volume = orderParams.getValue('Specimen:Volume')
        if volume:
            collection.quantity = self.createQuantity(volume)
        macroscopicDescription = orderParams.getValue('Specimen:MacroscopicDescription')
        if macroscopicDescription:
            collection.comment = [ macroscopicDescription ]
        # ppl: pathological process localization
        pplCode = orderParams.getCode('Specimen:bodySite')
        if pplCode:
            collection.bodySite = self.createCodeableConcept(self.pplUrn, pplCode, self.pplVersion)
        # cmfc: collection method for cytology
        cmfcCode = orderParams.getCode('Specimen:method:cytologic')
        if cmfcCode:
            collection.method = self.createCodeableConcept(self.cmfcUrn, cmfcCode, self.cmfcVersion)
        # cmfg: collection method for histology
        cmfgCode = orderParams.getCode('Specimen:method:gistologic')
        if cmfgCode:
            collection.method = self.createCodeableConcept(self.cmfgUrn, cmfgCode, self.cmfgVersion)
        extensionCode = str(orderParams.getValue('Specimen:extension:formalin'))
        if extensionCode == '1':
            e = Extension()
            e.url = 'http://hl7.org/fhir/StructureDefinition/specimen-specialHandling'
            e.valueCodeableConcept = self.createCodeableConcept(self.sampleProcessingFeaturesUrn,
                                                                extensionCode,
                                                                self.spfVersion)
            specimen.extension = [ e ]

        specimenIdentifier = orderParams.getString('Specimen.identifier')
        if specimenIdentifier:
            specimen.identifier = [ self.createIdentifier('urn:uuid:'+ self.orgCode,
                                                          specimenIdentifier,
                                                          self.orgReference
                                                         )
                                  ]
        container = SpecimenContainer()
        specimen.container = [ container ]
        container.identifier = [ self.createIdentifier('urn:uuid:'+ self.lab.id,
                                                              externalId,
                                                              self.labReference
                                                             )
                                           ]
        container.type = self.createCodeableConcept(self.containerTypeUrn, containerTypeCode, containerTypeVersion)
        specimen._key = (specimenTypeCode, containerTypeCode, externalId) # а гистология?
        return specimen


    def newSpecimenShort(self, patientReference, specimenTypeId, container=None):
        specimenTypeCode, specimenTypeVersion = getIdentificationEx('rbTissueType',
                                                                    specimenTypeId,
                                                                    self.specimenTypeUrn,
                                                                    raiseIfNonFound=False
                                                                    )
        specimen = Specimen()
        specimen.subject = patientReference
        specimen.type = self.createCodeableConcept(self.specimenTypeUrn,
                                                   specimenTypeCode,
                                                   specimenTypeVersion)
        if container:
            specimen.container = [container]
        return specimen


    def newDiagnosticOrderItem(self,
                               serviceCode,
                               serviceVersion,
                               financeCode,
                               financeVersion
                              ):
        diagnosticOrderItem  = DiagnosticOrderItem()
        diagnosticOrderItem.code = self.createCodeableConcept(self.serviceUrn,
                                                              serviceCode,
                                                              serviceVersion)

        e = Extension()
        e.url = 'urn:oid:1.2.643.2.69.1.100.1'
        e.valueCodeableConcept = self.createCodeableConcept(self.financeUrn,
                                                            financeCode,
                                                            financeVersion)

        diagnosticOrderItem.code.extension = [ e ]
        return diagnosticOrderItem


    def newDiagnosticOrderReason(self,
                                 paramsData
                                ):
        if 'DiagnosticOrder.reason' in paramsData:
            code, textValue = paramsData['DiagnosticOrder.reason'].split(" ", 1)
        else:
            return None
        codeableConcept = self.createCodeableConcept(self.baseReferalBioResearchUrn, code, '1')

        codeableConcept.text = textValue
        result = [ codeableConcept ]
        return result


    def newDiagnosticOrder(self,
                           patientReference,
                           practitionerReference,
                           encounterReference,
                           observationReferenceList,
                           specimenReferenceList,
                           serviceCodeList,
                           financeId,
                           note,
                           paramsData):
        diagnosticOrder = DiagnosticOrder()
        diagnosticOrder.subject   = patientReference
        diagnosticOrder.orderer   = practitionerReference
        diagnosticOrder.encounter = encounterReference
        if observationReferenceList:
            diagnosticOrder.supportingInformation = observationReferenceList
        diagnosticOrder.specimen = specimenReferenceList
        diagnosticOrder.status    = 'requested'
        # diagnosticOrder.priority  = 'routine'
        diagnosticOrderReason = self.newDiagnosticOrderReason(paramsData)
        if diagnosticOrderReason:
            diagnosticOrder.reason = diagnosticOrderReason
        diagnosticOrder.item = []
        # serviceCodeSet = set(getIdentificationEx('rbService', serviceId, self.serviceUrn)
        #                      for serviceId in serviceIdList
        #                     )
        # serviceCodeList = list(serviceCodeSet)
        serviceCodeList.sort()
        if financeId:
            financeCode, financeVersion = getIdentificationEx('rbFinance', financeId, self.financeUrn, True)
        else:
            financeCode, financeVersion = self.financeDefault, self.financeVersion

        if note:
            annotation = Annotation()
            annotation.text = note
            diagnosticOrder.note = [ annotation ]

        serviceVersion = '43'
        for serviceCode in serviceCodeList:
            item = self.newDiagnosticOrderItem(serviceCode,
                                               serviceVersion,
                                               financeCode,
                                               financeVersion
                                              )
            diagnosticOrder.item.append(item)
        return diagnosticOrder


    def newOrderObservation(self, urn, code, value):
        observation = Observation()
        observation.code = self.createCodeableConcept(urn, code, '')
        observation.status = 'final'
        if type(value) == bool:
            observation.valueBoolean = value
        elif isinstance(value, (float, int, long)):
            observation.valueQuantity = Quantity()
            observation.valueQuantity.value = value
        elif isinstance(value, unicode):
            observation.valueString = value
        elif isinstance(value, QDate) and code == '11':
            observation.valueString = unicode(value.toString(Qt.ISODate))
        elif isinstance(value, QDate):
            observation.valueDateTime = unicode(value.toString(Qt.ISODate))
        elif isinstance(value, QDateTime):
            observation.valueDateTime = unicode(value.toString(Qt.ISODate))
        else:
            assert False
        return observation


    def newOrder(self,
                 orderIdentifier,
                 orderDatetime,
                 patientReference,
                 practitionerReference,
                 diagnosticOrderReferenceList,
                 serviceProvider,
                 isUrgent=False,
                 binaryData=None
                ):
        order = Order()
        order.identifier = [ orderIdentifier ]
        if binaryData:
            e = Extension()
            e.url = 'http://hl7.org/fhir/StructureDefinition/communication-media'
            a = Attachment()
            a.url = binaryData['urn']
            a.contentType = binaryData['contentType']
            e.valueAttachment = a
            order.extension = [e]
        order.date = dateTimeToFHIRDate(orderDatetime)
#        order.date = dateTimeToFHIRDate(QDateTime.currentDateTime())
        order.subject = patientReference
        order.source = practitionerReference
        order.target = serviceProvider
        order.when = OrderWhen()
        whenCode = 'asap' if isUrgent else 'Routine'
        order.when.code = self.createCodeableConcept('urn:oid:1.2.643.2.69.1.1.1.30', whenCode, version='1')
        order.detail = diagnosticOrderReferenceList
        return order


    def createEmptyTransactionBundle(self, profile):
        result = Bundle()
        result.meta  = Meta( dict(profile = [ profile ] ))
        result.type  = 'transaction'
        result.entry = []
        return result


    def addBundleEntry(self, bundle, resource):
        entry = BundleEntry()
        entry.fullUrl = 'urn:uuid:%s' % (resource.id if resource.id else uuid.uuid4())
        entry.resource = resource
        entry.request = BundleEntryRequest()
        entry.request.method = 'POST'
        entry.request.url    = resource.resource_name
        bundle.entry.append(entry)
        return self.newBundleReference(entry.fullUrl)


    def newOrderBundle(self,
                       order,
                       orderIdentifierValue,
                       patientReference,
                       clientInfo
                      ):
        bundle = self.createEmptyTransactionBundle(self.orderProfile)
        mapPersonIdToPractitionerReference = {}
        mapSpecimenKeyToSpecimenReference = {}
        mapDiagnosisToConditionReference = {}
#        mapEventIdToEncounterReference = {}
        mapActionToSpecimenReference = {}
        diagnosticOrderReferenceList = []
        orderDatetime = order.takenDatetime or QDateTime.currentDateTime()
        isNeonatal = False
        conditionReferenceList = []
        lastMenstruationDate = order.params.getValue('Condition:LastMenstruationDate')
        if order.params.getValue('Condition:Menopause'):
            condition = self.newConditionFromMenopause(patientReference)
            conditionReferenceList.append( self.addBundleEntry(bundle, condition) )
        elif lastMenstruationDate:
            condition = self.newConditionFromLastMenstruationDate(patientReference, lastMenstruationDate)
            conditionReferenceList.append( self.addBundleEntry(bundle, condition) )
        observationReferenceList = []
        for param, urn, code in ( ('Observation:PregnancyWeek',                 self.orderParamUrn, self.orderParamPregnancyWeek),
                                  ('Observation:MenstrualDay',                  self.orderParamUrn, self.orderParamMenstrualDay),
                                  ('Observation:Anamnesis',                     self.orderParamUrn, self.orderParamAnamnesis),
                                  ('Observation:InstrumentalInvestigationData', self.orderParamUrn, self.orderParamnstrumentalInvestigationData),
                                  ('Observation:Treatment',                     self.orderParamUrn, self.orderParamTreatment),
                                  ('Observation:ORVISymptomsDate',              self.orderParamUrn, self.orderParamORVISymptomsDate),
                                  ('Observation:AskForMedicineDate',            self.orderParamUrn, self.orderParamAskForMedicineDate),
                                  ('Observation:ConditionBeforeMedicineDate',   self.orderParamUrn, self.orderParamConditionBeforeMedicineDate),
                                  ('Observation:Complications',                 self.orderParamUrn, self.orderParamComplications),
                                  ('Observation:HospitalizationDate',           self.orderParamUrn, self.orderParamHospitalizationDate),
                                  ('Observation:EpidAnamnesis',                 self.orderParamUrn, self.orderParamEpidAnamnesis),
                                  ('Observation:TaskPAO',                       self.orderParamUrn, self.orderParamTaskPAO),
                                  ('Observation:PAOData',                       self.orderParamUrn, self.orderParamPAOData),
                                  ('Observation:PreoperativeTreatment',         self.orderParamUrn, self.orderParamPreoperativeTreatment),
                                  (':neonatal:gestationalAge',                  self.orderParamUrn, self.orderParamGestationalAge),
                                  (':neonatal:bloodTrans',                      self.orderParamUrn, self.orderParamTransDateFlag),
                                  (':neonatal:transDate',                       self.orderParamUrn, self.orderParamTransDate),
                                  (':neonatal:repeatReason',                    self.orderParamUrn, self.orderParamRepeatReason),
                                  (':neonatal:multipleBirths',                  self.orderParamUrn, self.orderParamMultipleBirths),
                                ):
            value = order.params.getValue(param)
            if value:
                if param == ':neonatal:gestationalAge' and clientInfo.birthWeight:
                    isNeonatal = True
                    observation = self.newOrderObservation(self.orderParamUrn, self.orderParamNewbornWeight, clientInfo.birthWeight)
                    observationReferenceList.append(self.addBundleEntry(bundle, observation))
                if param == ':neonatal:transDate':
                    time = order.params.getValue(':neonatal:transTime')
                    if time:
                        value = QDateTime(value, time)
                observation = self.newOrderObservation(urn, code, value)
                observationReferenceList.append( self.addBundleEntry(bundle, observation) )
        orderBinaryData = None
        if isNeonatal:
            webdav = CWebDAVInterface()
            webdav.setWebDAVUrl(QtGui.qApp.webdavUrl)
            actionIdList = []
            for event in order.mapEventIdtoEvent.values():
                actionIdList.extend(event.mapActionIdToAction.keys())
            fileListWithSigns = self.getSignedFile(webdav, actionIdList)
            fileListWithSigns = filter(lambda file: file.newName[-4:] == '.xml', fileListWithSigns)
            if len(fileListWithSigns) != 1:
                raise Exception(
                    u'Событие %i интерпретируется как неонатальный скрининг, но отсутствует подписанный xml файл' %
                    order.mapEventIdtoEvent.keys()[0])
            attachmentList = []
            if fileListWithSigns:
                for file in fileListWithSigns:
                    try:
                        (binary, binRespSign, binaryOrgSign) = self.binarySigned(webdav, file, isNeonatal)
                    except:
                        raise Exception(u'Проблемы с получением документа с подписью')
                    binaryReference = self.addBundleEntry(bundle, binary)
                    orderBinaryData = {'urn': binaryReference.reference, 'contentType': 'application/x-akineo'}

        orderSetPersonId = None
        for event in order.getEventList():
            eventDiagnosisSet = set()
            orgStructureId = None
            for action in event.getActionList():
                setPersonId = action.setPersonId
                if not orderSetPersonId:
                    orderSetPersonId = setPersonId
                if setPersonId not in mapPersonIdToPractitionerReference:
                    practitioner = self.newPractitioner(setPersonId)
                    reference = self.addBundleEntry(bundle, practitioner)
                    mapPersonIdToPractitionerReference[setPersonId] = reference
                mapSpecimenKeyToSpecimenReferenceInAction = {}
                for sp in action.specimenList:
                    collectorId = sp.collectorId
                    if collectorId and collectorId not in mapPersonIdToPractitionerReference:
                        collector = self.newPractitioner(collectorId)
                        reference = self.addBundleEntry(bundle, collector)
                        mapPersonIdToPractitionerReference[collectorId] = reference
                    specimen = self.newSpecimen(patientReference,
                                                sp.specimenTypeId,
                                                sp.containerTypeId,
                                                sp.externalId,
                                                sp.takenDatetime,
                                                mapPersonIdToPractitionerReference.get(sp.collectorId),
                                                sp.probeId,
                                                order.params
                                               )
                    specimenKey = specimen._key
                    if specimenKey not in mapSpecimenKeyToSpecimenReference:
                        reference = self.addBundleEntry(bundle, specimen)
                        mapSpecimenKeyToSpecimenReference[specimenKey] = reference
                    else:
                        reference = mapSpecimenKeyToSpecimenReference[specimenKey]
                    mapSpecimenKeyToSpecimenReferenceInAction[specimenKey] = reference
                mapActionToSpecimenReference[id(action)] = mapSpecimenKeyToSpecimenReferenceInAction.values()

                diagnosis = action.diagnosis[:5]
                if diagnosis not in mapDiagnosisToConditionReference:
                   condition = self.newConditionFromDiagnosis(patientReference, diagnosis)
                   reference = self.addBundleEntry(bundle, condition)
                   mapDiagnosisToConditionReference[diagnosis] = reference
                eventDiagnosisSet.add(diagnosis)

                if not orgStructureId:
                    orgStructureId = action.orgStructureId

            if orgStructureId is None:
                raise Exception(u'Для Event.id=%d не удалось определить подразделение выполнения' % event.eventId)

            encounter = self.newEncounter(patientReference,
                                          event.eventId,
                                          event.externalId,
                                          event.eventTypeId,
                                          event.eventPurposeId,
                                          orgStructureId,
                                          [ mapDiagnosisToConditionReference[ds]
                                            for ds in eventDiagnosisSet
                                          ] + conditionReferenceList
                                         )
            if self.arkhangelskEncounter: # WFT?
                aidProfile = aidKind = aidType = None
                for action in event.getActionList():
                    aidKind, aidProfile, aidType = getArkhangelskEncounterData(action.actionId)
                    if aidProfile and aidKind and aidType:
                        break
                eventOrder = forceInt(QtGui.qApp.db.translate('Event', 'id', event.eventId, '`order`'))
                aidForm = '3'
                if eventOrder == 2:
                    aidForm = '1'
                elif eventOrder == 6:
                    aidForm = '2'
                else:
                    tableEventType = QtGui.qApp.db.table('EventType')
                    tableKind = QtGui.qApp.db.table('rbMedicalAidKind')
                    table = tableEventType.innerJoin(tableKind,  tableKind['id'].eq(tableEventType['medicalAidKind_id']))
                    record = QtGui.qApp.db.getRecordEx(table, [tableKind['code']],  [tableEventType['id'].eq(event.eventTypeId)] )
                    if record:
                        eventAidTypeCode = forceString(record.value(0))
                        if eventAidTypeCode == '12':
                            aidForm = '2'
                if aidProfile and aidKind and aidType and eventOrder:
                    encounter.type.append( self.createCodeableConcept(self.aidProfileUrn, aidProfile, '1') )
                    encounter.type.append( self.createCodeableConcept(self.aidKindUrn, aidKind, '1') )
                    encounter.type.append( self.createCodeableConcept(self.aidTypeUrn, aidType, '1') )
                    encounter.type.append( self.createCodeableConcept(self.aidFormUrn, aidForm, '1') )
            encounterReference = self.addBundleEntry(bundle, encounter)
#            mapEventIdToEncounterReference[event.eventId] = encounterReference


            for action in event.getActionList():
                # finalFinanceId = action.financeIdByActionType if QtGui.qApp.financeCodeByActionType else action.financeId
                # if not finalFinanceId:
                #     finalFinanceId = action.financeId
                # if self.isInsurerCodeIs99 and action.financeId == '2':
                #     finalFinanceId = forceRef(QtGui.qApp.db.translate('rbFinance', 'code', '1', 'id')) # rbFinance.id с кодом типа финансирования 'бюджет'
                # if self.isDMSInsurerCodeIs99 and action.financeId == '3':
                #     finalFinanceId = action.financeId
                # Задача 12223. Выбираем id типа финансирования по наличию настройки в autoLabExchange.ini
                # id при этом может получится только для бюджета(см. запрос в selectFHIROrders), если есть записи в ActionType_Service с кодм 'бюджет'
                # В остальных случаях:
                # Если значение идентификации для страховой организации пациента = 99 для обязательного полиса или СМО у него не указан,
                # а номер и дата выдачи указаны и при этом тип финансирования в заявке - ОМС, то такие действия отправляем с типом финансирования 'бюджет'.
                # В остальных случаях отправляем как ранее - action.financeId
                # Аналогично для заявок отправляемых как ДМС, только для них проверяется СМО полиса ДМС.
                # А также, если есть корректный полис ОМС, то заявка отправистя по ОМС.(в случае, если ДМС не корректен)
                if action.financeIdByActionType and QtGui.qApp.financeCodeByActionType:
                    finalFinanceId = action.financeIdByActionType
                else:
                    actionFinanceCode = forceInt(QtGui.qApp.db.translate('rbFinance', 'id', action.financeId, 'code'))
                    if self.isInsurerCodeIs99 and actionFinanceCode == 2:
                        finalFinanceId = forceRef(QtGui.qApp.db.translate('rbFinance', 'code', '1', 'id')) # rbFinance.id с кодом типа финансирования 'бюджет'
                    elif self.isDMSInsurerCodeIs99 and actionFinanceCode == 3:
                        finalFinanceId = forceRef(QtGui.qApp.db.translate('rbFinance', 'code', '1', 'id')) # rbFinance.id с кодом типа финансирования 'бюджет'
                    else:
                        finalFinanceId = action.financeId

                diagnosticOrder = self.newDiagnosticOrder(patientReference,
                                                          mapPersonIdToPractitionerReference[action.setPersonId],
                                                          encounterReference,
                                                          observationReferenceList,
                                                          mapActionToSpecimenReference.get(id(action), []),
                                                          [action.serviceId],
                                                          finalFinanceId,
                                                          action.note,
                                                          action.getParams()
                                                         )

                diagnosticOrderReference = self.addBundleEntry(bundle, diagnosticOrder)
                diagnosticOrderReferenceList.append(diagnosticOrderReference)
        orderIdentifier = self.createIdentifier('urn:oid:%s' % self.SAMSON,
                                                '%s.%s' % (self.orgShortCode, orderIdentifierValue.rjust(9, '0')),
                                                self.createOrgStructureReference(orgStructureId)
                                               )
        use = order.params.getCode('Order.identifier.use')
        if use:
            orderIdentifier.use = use

        orderObj = self.newOrder(orderIdentifier,
                                 orderDatetime,
                                 patientReference,
                                 mapPersonIdToPractitionerReference[orderSetPersonId],
                                 diagnosticOrderReferenceList,
                                 orderBinaryData
                                 )
        self.addBundleEntry(bundle, orderObj)
        return bundle


    def sendOrderOverFHIR(self, clientInfo, order):
        patient           = self.createPatient(clientInfo)
        patientReference  = self.createReference(patient)
        orderIdentifierValue = str(min(order.probeIdSet))

        bundle = self.newOrderBundle(order,
                                     orderIdentifierValue,
                                     patientReference,
                                     clientInfo)
        try:
            res = self.smart.server.post_json('', bundle.as_json())
        except server.FHIRErrorException as e:
            jsn = bundle.as_json()
            for entry in jsn['entry']:
                if entry['resource']['resourceType'] == 'Binary':
                    entry['resource']['content'] = 'binary data'
            QtGui.qApp.log('send order', u'Ошибка отправки заявки по пациенту %i, код ответа %i,\n%s\n%s' % (
            clientInfo.id, e.response.status_code, unicode(e), json.dumps(jsn, ensure_ascii=False)), level=1)
            raise e
        else:
            resAsJson = res.json()
            orderFullUrl = resAsJson['entry'][-1]['fullUrl']
            if orderFullUrl.startswith('Order/'):
                identifier = orderFullUrl.partition('/')[2]
                if identifier:
                    return identifier
        return orderIdentifierValue


    def newObservation(self, res, mapPersonIdToPractitionerReference):
        observation = Observation()
        observation.code = self.createCodeableConcept(self.testUrn,
                                                      res.testCode,
                                                      self.testVersion
                                                    )
        observation.status = 'final'
        observation.issued = dateTimeToFHIRDate(res.datetime)
        if res.personId:
            observation.performer = [ mapPersonIdToPractitionerReference.get(res.personId)
                                    ]
        if isinstance(res.value, (float, int, long)):
            unitCode, unitName = self.getUnitCodeAndName(res.unitId)
            observation.valueQuantity = Quantity()
            observation.valueQuantity.value = float(res.value)
            observation.valueQuantity.system = self.unitUrn
            observation.valueQuantity.code  = unitCode
            observation.valueQuantity.unit  = unitName
            if res.norm != (None, None):
                observation.referenceRange = [ ObservationReferenceRange() ]
                if res.norm[0] is not None:
                    quantity = Quantity()
                    quantity.value = float(res.norm[0])
                    quantity.system = observation.valueQuantity.system
                    quantity.code   = observation.valueQuantity.code
                    quantity.unit   = observation.valueQuantity.unit
                    observation.referenceRange[0].low = quantity
                if res.norm[1] is not None:
                    quantity = Quantity()
                    quantity.value = float(res.norm[1])
                    quantity.system = observation.valueQuantity.system
                    quantity.code   = observation.valueQuantity.code
                    quantity.unit   = observation.valueQuantity.unit
                    observation.referenceRange[0].high = quantity
            else:
                observation.referenceRange = [ ObservationReferenceRange(jsondict=dict(text='-')) ]
            observation.interpretation = self.createCodeableConcept(self.interpretationUrn,
                                                                    self.mapEvaluationToInterpretation.get(res.evaluation, 'E'),
                                                                    self.interpretationVersion
                                                                   )
        else:
            observation.valueString = unicode(res.value)
            observation.referenceRange = [ ObservationReferenceRange(jsondict=dict(text='-')) ]
            observation.interpretation = self.createCodeableConcept(self.interpretationUrn,
                                                                    self.mapEvaluationToInterpretation.get(res.evaluation, 'E'),
                                                                    self.interpretationVersion
                                                                   )
        return observation


    def newBinary(self, clientId, results):
        db = QtGui.qApp.db
        templateId = forceRef(db.translate('rbPrintTemplate', 'context', 'fhirPdf', 'id'))
        if not templateId:
            raise Exception(u'Контекст печати fhirPdf не найден')

        context = CInfoContext()
        clientInfo = context.getInstance(CClientInfo, clientId)
        data = {'client':  clientInfo,
                'results': results
               }
        name, template, templateType, printBlank = getTemplate(templateId)
        pageFormat = None
        templateResult = compileAndExecTemplate(name, template, data, pageFormat)
        pdf = None
        printer = QtGui.QPrinter()
        printer.setOutputFormat(printer.PdfFormat)
        tmpFile = QTemporaryFile()
        if tmpFile.open():
            printer.setOutputFileName(tmpFile.fileName())
            doc = QtGui.QTextDocument()
            doc.setHtml(templateResult.content)
            doc.print_(printer)
            pdf = tmpFile.readAll()

        if not pdf:
            raise Exception(u'Ошибка формирования pdf')

        binary = Binary()
        binary.contentType = 'application/pdf'
        binary.content = base64.b64encode(pdf)
        return binary


    def binarySigned(self, interface, file, isNeonatal=False):
        binary = respSign = orgSign = None
        extList = ['.pdf', '.xml', '.sms']
        typeList = ['application/pdf', 'application/x-akineo', 'application/x-akineo'] if isNeonatal else ['application/pdf', 'application/xml', 'application/xml']
        userSignList = ['application/x-pkcs7-practitioner', 'application/x-pkcs7-practitioner-xml', 'application/x-pkcs7-practitioner-xml']
        orgSignList = ['application/x-pkcs7-organization', 'application/x-pkcs7-organization-xml', 'application/x-pkcs7-organization-xml']
        xmlCoding = self.createCoding('urn:oid:1.2.643.5.1.13.13.11.1520', '75', '9.9')
        neonatalCoding = self.createCoding('urn:oid:1.2.643.5.1.13.13.99.2.592', 'SMSV27', '2.7')
        metaList = [None, neonatalCoding, neonatalCoding] if isNeonatal else [None, xmlCoding, xmlCoding]
        try:
            i = extList.index(file.newName[-4:])
        except:
            raise Exception(u'Расширение файла (%s) не поддерживается' % file.newName[-4:])
        if file:
            bytes = interface.downloadBytes(file)

            binary = Binary()
            binary.contentType = typeList[i]
            binary.content = base64.b64encode(bytes)
            if metaList[i]:
                binary.meta = Meta()
                binary.meta.tag = [metaList[i]]
        if file.respSignature:
            respSign = Binary()
            respSign.contentType = userSignList[i]
            respSign.content = base64.b64encode(file.respSignature.signatureBytes)

        if file.orgSignature:
            orgSign = Binary()
            orgSign.contentType = orgSignList[i]
            orgSign.content = base64.b64encode(file.orgSignature.signatureBytes)

        return (binary, respSign, orgSign)


    def newDiagnosticReport(self, patientReference, issued, serviceId, performer, observationReferences, attachmentReference, diagnosticOrderReference = None):
        serviceCode, serviceVersion = getIdentificationEx('rbService', serviceId, self.serviceUrn)

        diagnosticReport = DiagnosticReport()
#        diagnosticReport.conclusion = u'Value should be no empty string on DiagnosticReport'
        if diagnosticOrderReference:
            diagnosticReport.request = diagnosticOrderReference
        diagnosticReport.issued     = issued
        diagnosticReport.effectiveDateTime = issued
        diagnosticReport.code       = self.createCodeableConcept(self.serviceUrn,
                                                                 serviceCode,
                                                                 serviceVersion)
        diagnosticReport.performer  = performer
        diagnosticReport.result     = observationReferences
        diagnosticReport.status     = 'final'
        diagnosticReport.subject    = patientReference
        diagnosticReport.presentedForm = [ Attachment(jsondict=dict(url=attachmentReference.reference))
                                         ]
        diagnosticReport.meta = Meta()
        diagnosticReport.meta.security = [ self.createCoding('urn:oud:1.2.643.5.1.13.13.11.1116', 'N', '1')
                                         ]
        return diagnosticReport


    def newOrderResponse(self, orderReference, diagnosticReportReference, actionId):
        orderResponse = OrderResponse()
        orderResponse.who  = self.orgReference
        orderResponse.date = dateTimeToFHIRDate(QDateTime.currentDateTime())
        orderResponse.fulfillment = [ diagnosticReportReference ]
        #orderResponse.identifier = [ createPPMisIdentifier(str(actionId)) ]
        orderResponse.identifier = [ self.createMisIdentifier(actionId) ]
        orderResponse.orderStatus = 'completed'
        #orderResponse.orderStatus = 'accepted'
        orderResponse.request = orderReference
        return orderResponse


    def getSignedFile(self, interface, actionIdList):
        fileList = []
        processed = []
        for actionId in actionIdList:
            files = CAttachedFilesLoader.loadItems(interface, 'Action_FileAttach', actionId)
            for file in files:
                if file and (file.respSignature or file.orgSignature) and file.id not in processed:
                    fileList.append(file)
                    processed.append(file.id)
        return fileList

    def getAttachedFile(self, interface, actionIdList):
        fileList = []
        processed = []
        for actionId in actionIdList:
            files = CAttachedFilesLoader.loadItems(interface, 'Action_FileAttach', actionId)
            for file in files:
                if file and file.id not in processed:
                    fileList.append(file)
                    processed.append(file.id)
        return fileList

    def newResultBundle(self, clientId, patientReference, serviceId, results, isLIS = False):
        orderId = None
        diagOrderId = None
        if isLIS:
            db = QtGui.qApp.db
            #eventId = forceRef(db.translate('Action', 'id', results[0].actionId, 'event_id')
            actionRecord = db.getRecord('Action', ['event_id', 'externalId'], results[0].actionId)
            orderId = forceString(db.translate('Event', 'id', forceInt(actionRecord.value(0)), 'srcNumber'))
            diagOrderId = forceString(actionRecord.value(1))
            if patientReference is None:
                order = Order.read(orderId, self.smart.server)
                patientReference  = order.subject
        else:
            assert patientReference is not None
        bundle = self.createEmptyTransactionBundle(self.resultProfile)
        mapPersonIdToPractitionerReference = {}
        personIdSet = set(res.personId for res in results if res.personId)
        datetime = max(res.datetime for res in results) or QDateTime.currentDateTime()

        for personId in personIdSet:
            practitioner = self.newPractitioner(personId)
            reference = self.addBundleEntry(bundle, practitioner)
            mapPersonIdToPractitionerReference[personId] = reference

        practitionerReference = mapPersonIdToPractitionerReference.values()[0] if personIdSet else None

        observationReferences = []
        for res in results:
            observation = self.newObservation(res, mapPersonIdToPractitionerReference)
            reference = self.addBundleEntry(bundle, observation)
            observationReferences.append(reference)

        binary = self.newBinary(clientId, results)
        binaryReference = self.addBundleEntry(bundle, binary)

        diagnosticOrderReference = None
        if isLIS and diagOrderId:
            diagOrder = DiagnosticOrder()
            diagOrder.id = diagOrderId
            diagnosticOrderReference = [self.createReference(diagOrder)]

        diagnosticReport = self.newDiagnosticReport(patientReference,
                                                    dateTimeToFHIRDate(datetime),
                                                    serviceId,
                                                    practitionerReference,
                                                    observationReferences,
                                                    binaryReference,
                                                    diagnosticOrderReference)
        diagnosticReportReference = self.addBundleEntry(bundle, diagnosticReport)

        order = Order()
#        order.subject = patientReference
#        order.source  = practitionerReference
        order.source  = self.sourceOrgReference
        order.target  = self.orgReference
        if isLIS and orderId:
            order.id = orderId
            orderReference = self.createReference(order)
        else:
            order.detail  = [Reference(jsondict=dict(reference=''))]
            orderReference = self.addBundleEntry(bundle, order)


        orderResponse = self.newOrderResponse(orderReference, diagnosticReportReference, results[0].actionId)
        self.addBundleEntry(bundle, orderResponse)
        bundle.entry[-1].fullUrl = '' # стираю fullUrl в entry для orderResponse
        return bundle


    def sendLocalResultsOverFHIR(self, clientInfo, serviceId, results, actionId):
        if QtGui.qApp.isAnonim:
            patient = self.createAnonimPatient(clientInfo)
        else:
            patient = self.createPatient(clientInfo)
        patientReference  = self.createReference(patient)
        resultBundle = self.newResultBundle(clientInfo.id, patientReference, serviceId, results)
        res = self.smart.server.post_json('$addresults', resultBundle.as_json(), actionId=actionId, raiseIfstatusError=False)
        jsn = resultBundle.as_json()
        for entry in jsn['entry']:
            if entry['resource']['resourceType'] == 'Binary':
                entry['resource']['content'] = 'no pdf in log pls'
        QtGui.qApp.log('local results', u'Отправлены данные по пациенту %i, код ответа %i,\n%s'%(clientInfo.id, res.status_code, json.dumps(resultBundle.as_json())), level=3)
        if res.status_code == 200:
            resAsJson = res.json()
            for entry in resAsJson['entry']:
                if entry['fullUrl'].startswith('Order/'):
                    identifier = entry['fullUrl'].partition('/')[2]
                    if identifier:
                        return identifier
        return None


    def createOrderBundle(self, actionId):
        context = CInfoContext()
        action = CActionInfo(context, actionId)
        personId = action.setPerson.personId
        orgStructureId = action.setPerson.orgStructure.id
        event = action.getEventInfo()
        eventId = event.id
        clientId = event.client.id
        externalId = event.externalId
        clientInfo = getClientInfo(clientId)
        eventTypeId = event.eventType.id
        medicalAidTypeId = event.eventType.medicalAidType.id
        eventPurposeId = event.eventType.purpose.id
        financeId = event.contract.finance.id
        serviceCodeList = []
        specimenId = None
        height = weight = None
        diagnosticOrderReferenceList = []
        orderDatetime = QDateTime().currentDateTime()
        serviceProviderOrgId = None
        orderIdentifierValue = ''

        mapPersonIdToPractitionerReference = {}
        orderIdentifierValue = action._action.getPropertyByShortName(u'directionNumber').getValue()

        serviceProviderOrgId = action._action.getPropertyByShortName(u'externalLab').getInfo(context).id
        serviceCodeList = [val.code for val in action._action.getPropertyByShortName(u'orderService').getInfo(context)]
        height = action._action.getPropertyByShortName(u'height')
        weight = action._action.getPropertyByShortName(u'weight')
        pregweek = action._action.getPropertyByShortName(u'pregWeek')
        cycleday = action._action.getPropertyByShortName(u'cycleDay')
        specimenId = action._action.getPropertyByShortName(u'biomaterial').getValue()
        isNeonatal = True if action._action.getType().code == 'NNC' else False
        if isNeonatal:
            financeId = forceRef(QtGui.qApp.db.translate('rbFinance', 'code', '1', 'id'))
        blankNumber = None
        reexaminationProp = action._action.getPropertyByShortName(u'reexamination')
        if reexaminationProp and reexaminationProp.getValue():
            reexamination = reexaminationProp.getValue()
        else:
            reexamination = False
        representativeInfo = None
        if isNeonatal:
            blankNumber = action._action.getPropertyByShortName(u'directionNumber').getValue()
            prop = action._action.getPropertyByShortName(u'representative')
            if prop:
                representativeInfo = getClientInfo(prop.getInfo(context).client.id)

        bundle = self.createEmptyTransactionBundle(self.orderProfile)
        # пациент
        if QtGui.qApp.isAnonim:
            patient = self.createAnonimPatient(clientInfo)
        else:
            patient = self.createPatient(clientInfo, representativeInfo=representativeInfo, isNeonatal=isNeonatal)
        patientReference = self.createReference(patient)

        # назначивший врач
        practitioner = self.newPractitioner(personId)
        reference = self.addBundleEntry(bundle, practitioner)
        mapPersonIdToPractitionerReference[personId] = reference

        # информация о состоянии пациента
        mkb = action.MKB.__str__() if action.MKB.__str__() else getEventDiagnosis(eventId)
        condition = self.newConditionFromDiagnosis(patientReference, mkb)
        conditionReferences = self.addBundleEntry(bundle, condition)

        #
        conditionReferenceList = []
        # признак менопаузы и дата начала последней менструации
        # lastMenstruationDate = order.params.getValue('Condition:LastMenstruationDate')
        # if order.params.getValue('Condition:Menopause'):
        #     condition = self.newConditionFromMenopause(patientReference)
        #     conditionReferenceList.append(self.addBundleEntry(bundle, condition))
        # elif lastMenstruationDate:
        #     condition = self.newConditionFromLastMenstruationDate(patientReference, lastMenstruationDate)
        #     conditionReferenceList.append(self.addBundleEntry(bundle, condition))
        #

        # сведения о случае обслуживания
        encounter = self.newEncounter(patientReference,
                                      eventId,
                                      externalId,
                                      eventTypeId,
                                      eventPurposeId,
                                      orgStructureId,
                                      [conditionReferences] + conditionReferenceList,
                                      medicalAidTypeId
                                      )
        encounterReference = self.addBundleEntry(bundle, encounter)

        observationReferenceList = []
        if isNeonatal:
            birthNumber = clientInfo.birthNumber or 1
            observation = self.newOrderObservation(self.orderParamUrn, self.orderParamMultipleBirths, birthNumber)
            observationReferenceList.append(self.addBundleEntry(bundle, observation))

            birthWeight = clientInfo.birthWeight
            if birthWeight:
                observation = self.newOrderObservation(self.orderParamUrn, self.orderParamNewbornWeight, birthWeight)
                observationReferenceList.append(self.addBundleEntry(bundle, observation))

            gestationAgeProp = action._action.getPropertyByShortName(u'due_date')
            if gestationAgeProp and gestationAgeProp.getValue():
                gestationAge = forceInt(gestationAgeProp.getValue()) * 7
                observation = self.newOrderObservation(self.orderParamUrn, self.orderParamGestationalAge, gestationAge)
                observationReferenceList.append(self.addBundleEntry(bundle, observation))

            facttransfusionProp = action._action.getPropertyByShortName(u'facttransfusion')
            if facttransfusionProp:
                facttransfusion = forceBool(facttransfusionProp.getValue())
                observation = self.newOrderObservation(self.orderParamUrn, self.orderParamTransDateFlag, facttransfusion)
                observationReferenceList.append(self.addBundleEntry(bundle, observation))
                if facttransfusion:
                    datetransfusionProp = action._action.getPropertyByShortName(u'datetransfusion')
                    timetransfusionProp = action._action.getPropertyByShortName(u'timetransfusion')
                    if datetransfusionProp:
                        datetransfusion = facttransfusionProp.getValue()
                        if datetransfusion:
                            if timetransfusionProp and timetransfusionProp.getValue():
                                timetransfusion = timetransfusionProp.getValue()
                                datetimeTransfusion = QDateTime(datetransfusion, timetransfusion)
                            else:
                                datetimeTransfusion = QDateTime(datetransfusion)
                            observation = self.newOrderObservation(self.orderParamUrn, self.orderParamTransDate, datetimeTransfusion)
                            observationReferenceList.append(self.addBundleEntry(bundle, observation))

            if reexamination:
                reasonProp = action._action.getPropertyByShortName(u'reason')
                if reasonProp and reasonProp.getValue():
                    reason = reasonProp.getValue()
                    observation = self.newOrderObservation(self.orderParamUrn, self.orderParamRepeatReason, reason)
                    observationReferenceList.append(self.addBundleEntry(bundle, observation))
        else:
            if height and height.getValue() and height.getValue() > 0:
                observation = self.newOrderObservation(self.orderParamUrn, '1', height.getValue())
                observationReferenceList.append(self.addBundleEntry(bundle, observation))
            if weight and weight.getValue() and weight.getValue() > 0:
                observation = self.newOrderObservation(self.orderParamUrn, '2', weight.getValue())
                observationReferenceList.append(self.addBundleEntry(bundle, observation))
            if pregweek and pregweek.getValue() and pregweek.getValue() > 0:
                observation = self.newOrderObservation(self.orderParamUrn, '3', pregweek.getValue())
                observationReferenceList.append(self.addBundleEntry(bundle, observation))
            if cycleday and cycleday.getValue() and cycleday.getValue() > 0:
                observation = self.newOrderObservation(self.orderParamUrn, '4', cycleday.getValue())
                observationReferenceList.append(self.addBundleEntry(bundle, observation))

        fhirId = getOrganizationIdentification('urn:odliExternalLabGUID', serviceProviderOrgId)
        serviceProviderOrgReference = self.createReference(self.createOrganization(fhirId))

        # информация о забранном биоматериале
        specimenReferences = []
        if specimenId:
            container = None
            if blankNumber:
                container = SpecimenContainer()
                container.identifier = [self.createIdentifier('urn:uuid:' + fhirId, blankNumber, serviceProviderOrgReference)]
            specimen = self.newSpecimenShort(patientReference, specimenId, container)
            specimenReferences.append(self.addBundleEntry(bundle, specimen))

        orderBinaryData = None
        if isNeonatal:
            fileList = self.getAttachedFile(QtGui.qApp.webDAVInterface, [action.id])
            fileList = filter(lambda file: file.newName[-4:] == '.sms', fileList)
            if fileList:
                filelist = sorted(fileList, key=lambda x: x.lastModified, reverse=True)
                for file in fileList:
                    try:
                        (binary, binRespSign, binaryOrgSign) = self.binarySigned(QtGui.qApp.webDAVInterface, file, isNeonatal)
                        binaryReference = self.addBundleEntry(bundle, binary)
                        orderBinaryData = {'urn': binaryReference.reference, 'contentType': 'application/x-akineo'}
                        break
                    except:
                        raise Exception(u'Проблемы с получением документа с подписью')
            if orderBinaryData is None:
                action = CAction.getActionById(actionId)
                action.getRecord().setValue('note', toVariant(u'Нет прикрепленного Cda документа'))
                action.save(idx=-1)
                return None

        diagnosticOrder = self.newDiagnosticOrder(patientReference,
                                                  reference,
                                                  encounterReference,
                                                  observationReferenceList,
                                                  specimenReferences,
                                                  serviceCodeList,
                                                  financeId,
                                                  action.note,
                                                  dict()
                                                  )

        diagnosticOrderReference = self.addBundleEntry(bundle, diagnosticOrder)
        diagnosticOrderReferenceList.append(diagnosticOrderReference)
        orderIdentifier = self.createIdentifier('urn:oid:%s' % self.SAMSON,
                                                '%s_%s' % (self.orgShortCode, orderIdentifierValue),
                                                self.createOrgStructureReference(orgStructureId),
                                                use='secondary' if reexamination else None
                                                )


        orderObj = self.newOrder(orderIdentifier,
                                 orderDatetime,
                                 patientReference,
                                 mapPersonIdToPractitionerReference[personId],
                                 diagnosticOrderReferenceList,
                                 serviceProvider=serviceProviderOrgReference,
                                 isUrgent=action.isUrgent,
                                 binaryData=orderBinaryData
                                 )
        self.addBundleEntry(bundle, orderObj)
        return bundle


    def sendOrderWhithOutProbesOverFHIR(self, actionId):
        lockId = None
        db = QtGui.qApp.db
        try:
            eventId = forceRef(db.translate('Action', 'id', actionId, 'event_id'))
            db.query('CALL getAppLock_(%s, %d, %d, %s, %s, @res)' % (quote('Event'), eventId, 0, 1, quote('SOC_ODLI')))
            query = db.query('SELECT @res')

            if query.next():
                record = query.record()
                s = forceString(record.value(0)).split()
                if len(s) > 1:
                    isSuccess = int(s[0])
                    if isSuccess:
                        lockId = int(s[1])
                    else:
                        QtGui.qApp.log(u'Выгрузка направления', u'Событие %i заблокировано' % eventId, level=1)
            if lockId:
                bundle = self.createOrderBundle(actionId)
                if bundle:
                    res = self.smart.server.post_json('', bundle.as_json(), actionId=actionId, raiseIfstatusError=False)
                    resAsJson = res.json()
                    QtGui.qApp.log('soc_odli', u'Отправлены данные по заявке %i, код ответа %i,\n%s' % (actionId, res.status_code, resAsJson), level=1)
                    if res.status_code == 200:
                        note = u'Заказ успешно выгружен в ОДЛИ {0}'.format(fmtDate(QtGui.qApp.db.getCurrentDatetime()))
                        action = CAction.getActionById(actionId)
                        action.getRecord().setValue('status', toVariant(CActionStatus.wait))
                        action.getRecord().setValue('note', toVariant(note))
                        action.save(idx=-1)
        except Exception as e:
            QtGui.qApp.log('error', anyToUnicode(e), 1)
        finally:
            if lockId:
                db.query('CALL ReleaseAppLock(%d)' % lockId)


    def getResultOverFHIR(self, actionId):
        path = '$getresult'
        params = Parameters()
        params.parameter = []
        context = CInfoContext()
        action = CActionInfo(context, actionId)
        orderIdentifierValue = action._action.getPropertyByShortName(u'directionNumber').getValue()
        serviceProviderOrgId = action._action.getPropertyByShortName(u'externalLab').getInfo(context).id
        targetCode = getOrganizationIdentification('urn:odliExternalLabGUID', serviceProviderOrgId)
        orgStructureId = action.setPerson.orgStructure.id
        sourceCode = getOrgStructureIdentification(orgStructureId, self.orgUrn)
        orderMisID = '%s_%s' % (self.orgShortCode, orderIdentifierValue)

        param = ParametersParameter()
        param.name = 'SourceCode'
        param.valueString = sourceCode
        params.parameter.append(param)

        param = ParametersParameter()
        param.name = 'TargetCode'
        param.valueString = targetCode
        params.parameter.append(param)

        param = ParametersParameter()
        param.name = 'OrderMisID'
        param.valueString = orderMisID
        params.parameter.append(param)

        res = self.smart.server.post_json(path, params.as_json())
        QtGui.qApp.log(u'soc_odli Получение результата actionId={0} запрос'.format(actionId), params.as_json(), level=1)
        QtGui.qApp.log(u'soc_odli Получение результата actionId={0} ответ'.format(actionId), res.content.decode('utf-8'), level=1)
        responseParameters = Parameters(jsondict=json.loads(res.content))
        if responseParameters.parameter:
            orderResponse = responseParameters.parameter[0].resource
            action = CAction(record=QtGui.qApp.db.getRecord('Action', '*', actionId))
            binaryUrls = set()
            textResult = []
            who = self.getResource(Organization, orderResponse.who.reference)
            for identifier in who.identifier:
                if identifier.system == u'spr01':
                    omsCode = identifier.value
                    orgId = self.findOrgByInfis(omsCode)
                    action.getRecord().setValue('org_id', toVariant(orgId))
            for item in orderResponse.fulfillment:
                diagnosticReference = item.reference
                diagnosticReport = self.getResource(DiagnosticReport, diagnosticReference)
                if diagnosticReport and diagnosticReport.status in ['final', 'appended']:
                    issueDate = unFmtDate(diagnosticReport.issued.isostring)
                    action.getRecord().setValue('endDate', toVariant(issueDate))
                    action.getRecord().setValue('status', toVariant(CActionStatus.finished))
                    note = u'Результат успешно загружен из ОДЛИ {0}'.format(fmtDate(QtGui.qApp.db.getCurrentDatetime()))
                    action.getRecord().setValue('note', toVariant(note))
                    if diagnosticReport.performer:
                        practitioner = self.getResource(Practitioner, diagnosticReport.performer.reference)
                        if practitioner:
                            code = practitioner.practitionerRole[0].role.coding[0].code
                            urn = practitioner.practitionerRole[0].role.coding[0].system
                            roleName = self.lookupInTerminology(urn, code).get('display')
                            action[u'Внешний исполнитель'] = practitioner.name.family[0] + u' ' + practitioner.name.given[0] + u' ' + practitioner.name.family[1] + u', ' + roleName
                    if diagnosticReport.result:
                        for obs in diagnosticReport.result:
                            observation = self.getResource(Observation, obs.reference)
                            if observation:
                                refObservation = observation.relativePath()
                                code = observation.code.coding[0].code
                                urn = observation.code.coding[0].system
                                testName = self.lookupInTerminology(urn, code).get('display')
                                if observation.valueQuantity is not None:
                                    referenceRange = None
                                    referenceRangeText = None
                                    valueQuantity = observation.valueQuantity
                                    value = float(valueQuantity.value)
                                    unit = self.lookupInTerminology(self.unitUrn, valueQuantity.code).get('SHORTNAME')
                                    if observation.referenceRange:
                                        for rr in observation.referenceRange:
                                            if not referenceRange or referenceRange == (None, None):
                                                rrLow = None
                                                if hasattr(rr, 'low'):
                                                    if (rr.low is not None
                                                            and (rr.low.code and rr.low.code != valueQuantity.code)
                                                    ):
                                                        pass  # raise Exception(u'разные единицы измерения observation.valueQuantity и observation.referenceRange[0].low в %s' % refObservation)
                                                    rrLow = rr.low.value if rr.low else None
                                                rrHigh = None
                                                if hasattr(rr, 'high'):
                                                    if (rr.high is not None
                                                            and (rr.high.code and rr.high.code != valueQuantity.code)
                                                    ):
                                                        pass  # raise Exception(u'разные единицы измерения observation.valueQuantity и observation.referenceRange[0].high в %s' % refObservation)
                                                    rrHigh = rr.high.value if rr.high else None
                                                referenceRange = (rrLow, rrHigh)
                                                if referenceRange and referenceRange != (None, None):
                                                    referenceRangeText = u'(%s - %s)' % referenceRange
                                                    break
                                        if not referenceRange or referenceRange == (None, None):
                                            for rrt in observation.referenceRange:
                                                if hasattr(rrt, 'text') and rrt.text:
                                                    referenceRangeText = rrt.text or ''
                                    if referenceRangeText:
                                        testText = u'%s: %s %s %s' % (testName, value, unit, referenceRangeText)
                                    else:
                                        testText = u'%s: %s %s' % (testName, value, unit)
                                    textResult.append(testText)
                                elif observation.valueString is not None:
                                    value = unicode(observation.valueString)
                                    referenceRangeText = None
                                    # if observation.referenceRange:
                                    #     for rrt in observation.referenceRange:
                                    #         if hasattr(rrt, 'text') and rrt.text:
                                    #             referenceRangeText = rrt.text or ''
                                    #             break
                                    if referenceRangeText:
                                        testText = u'%s: %s %s' % (testName, value, referenceRangeText)
                                    else:
                                        testText = u'%s: %s' % (testName, value)
                                    textResult.append(testText)

                    if diagnosticReport.presentedForm:
                        pdfFile = cdaFile = None
                        for binary in diagnosticReport.presentedForm:
                            if binary.contentType == 'application/pdf':
                                pdfFile = self.loadBinary(action, None, binary.url, binary.contentType)
                            elif binary.contentType == 'application/xml':
                                cdaFile = self.loadBinary(action, None, binary.url, binary.contentType)
                            elif binary.contentType in ['application/x-pkcs7-organization',
                                                        'application/x-pkcs7-practitioner']:
                                self.loadSign(pdfFile, None, binary.url, binary.contentType)
                            elif binary.contentType in ['application/x-pkcs7-organization-xml',
                                                        'application/x-pkcs7-practitioner-xml']:
                                self.loadSign(cdaFile, None, binary.url, binary.contentType)
                            binaryUrls.add(binary.url)
            action[u'Результат'] = u';\n'.join(textResult)
            action.save(idx=-1)


    def findOrgByInfis(self, infis):
        u"""Возвращает id организации по спр01"""
        if not infis:
            return None

        db = QtGui.qApp.db
        result = self.orgCache.get(infis, -1)

        if result == -1:
            result = None
            table = db.table('Organisation')
            record = db.getRecordEx(table, 'id', [table['deleted'].eq(0), table['infisCode'].eq(infis)], 'id')
            if record:
                result = forceRef(record.value(0))
                self.orgCache[infis] = result

        return result


    def getResource(self, resourceClass, resId, logResponse=True):
        resource = None
        res = self.smart.server._get(resId)
        if logResponse:
            QtGui.qApp.log(u'Получение ресурса {0}'.format(resId), res.content.decode('utf-8'), level=1)
        if res.status_code == 200:
            resource = resourceClass(jsondict=json.loads(res.content))
        return resource


    def loadBinary(self, action, personId, resourceId, contentType):
        binary = self.getResource(Binary, resourceId, logResponse=False)
        if binary and hasattr(QtGui.qApp, 'webDAVInterface'):
            storageInterface = QtGui.qApp.webDAVInterface
            if storageInterface:
                name = u'ODLIResult_' + binary.id + u'.{0}'.format(contentType[-3:])
                _file = storageInterface.uploadBytes(name, binary.content.decode('base64'))
                _file.setAuthorId(personId)
                action._attachedFileItemList.append(_file)
                return _file
        return None


    def loadSign(self, _file, personId, resourceId, contentType):
        binary = self.getResource(Binary, resourceId, logResponse=False)
        if binary and _file:
            if contentType in ['application/x-pkcs7-practitioner', 'application/x-pkcs7-practitioner-xml']:
                _file.setRespSignature(binary.content.decode('base64'), personId, QDateTime.currentDateTime())
            else:
                _file.setOrgSignature(binary.content.decode('base64'), personId, QDateTime.currentDateTime())


    def sendLISResultsOverFHIR(self, clientInfo, serviceId, results):
#        patient = Patient()
#        patient.id = getClientIdentification(self.codeN3PatientIdentification, clientInfo.id)
#        assert patient.id
#        patientReference  = self.createReference(patient)
        resultBundle = self.newResultBundle(clientInfo.id, None, serviceId, results, True)
        answer = self.smart.server.post_json('$addresults', resultBundle.as_json())
        QtGui.qApp.log('results', u'Отправлены данные по пациенту %i, код ответа %s'%(clientInfo.id, answer.status_code), level=3)
        if answer.status_code == 200:
            resAsJson = answer.json()
            for entry in resAsJson['entry']:
                if entry['fullUrl'].startswith('Order/'):
                    identifier = entry['fullUrl'].partition('/')[2]
                    if identifier:
                        return identifier
        return None


    def getOrders(self, begDate, endDate = None, source = None):
        if not self._createParams:
            raise Exception(u'Нет настроек создания события')
#        systemId = forceRef(QtGui.qApp.db.translate('rbAccountingSystem', 'code', 'n3.patient', 'id'))
#        if not systemId:
#            raise Exception(u'В rbAccountingSystem отсутсвует код n3.patient')
        request = { 'resourceType': 'Parameters',
                    'parameter': [
                                    { 'name': 'TargetCode',
                                      'valueString': self.lab.id
                                    },
                                    { 'name': 'StartDate',
                                      'valueString': str(begDate.toString('yyyy-MM-dd'))
                                    }
                                 ]
                  }
        if endDate:
            request['parameter'].append({'name': 'EndDate', 'valueString': str(endDate.toString('yyyy-MM-dd'))})
        if source:
            request['parameter'].append({'name': 'SourceCode', 'valueString': source})
        responce = self.smart.server.post_json('$getorders', request).json()
        found = False
        for orderResp in responce['parameter']:
            order = Order(orderResp['resource'])
            if order.subject and order.identifier and order.identifier[0].assigner.reference != order.target.reference:
                eventId = findEvent(order.id)
                if not eventId:
                    patient = Patient.read_from(order.subject.reference, self.smart.server)
                    clientId = self.findOrCreateClient(patient)
                    if not clientId:
                        continue
                    for detail in order.detail:
                        diagOrder = DiagnosticOrder.read_from(detail.reference, self.smart.server)
                        try:
                            specimen = Specimen.read_from(diagOrder.specimen[0].reference, self.smart.server)
                            specimenValue = specimen.identifier[0].value
                        except:
                            specimenValue = None
                        aidType = aidProfile = aidKind = aidForm = diag = financeId = None
                        if self.arkhangelskEncounter:
                            encounter = Encounter.read_from(diagOrder.encounter.reference, self.smart.server)
                            for encType in encounter.type:
                                for c in encType.coding:
                                    if c.system.lower() == self.aidTypeUrn:
                                        aidType = c.code
                                    elif c.system.lower() == self.aidProfileUrn:
                                        aidProfile = c.code
                                    elif c.system.lower() == self.aidKindUrn:
                                        aidKind = c.code
                                    elif c.system.lower() == self.aidFormUrn:
                                        aidForm = c.code
                            diag = None
                            if encounter.indication and len(encounter.indication) > 0:
                                condition = Condition.read_from(encounter.indication[0].reference, self.smart.server)
                                diag = self.extractCode(condition.code.coding, self.ICDUrn, condition.relativePath(), 'diagnosis')

                        found = True
                        extClientId = self.getMisClientId(patient)
                        eventId = createEvent(clientId, extClientId, order, self._createParams,  aidType)
                        QtGui.qApp.log(u'fhir orders', u'Заявка на %s от %s'%(patient.name[0].text, order.date.isostring), level=3)
                        for item in diagOrder.item:
                            code = self.extractCode(diagOrder.item[0].code.coding, self.serviceUrn, diagOrder.relativePath(), 'diagnosticOrder.name.coding')
                            if self.arkhangelskEncounter:
                                try:
                                    financeCode = self.extractCode(diagOrder.item[0].code.extension[0].valueCodeableConcept.coding, self.financeUrn, diagOrder.relativePath(), 'finance')
                                    financeId = findByIdentification('rbFinance', self.financeUrn, financeCode, False)
                                except:
                                    financeId = None
                            serviceId = findByIdentification('rbService', self.serviceUrn, item.code.coding[0].code, False)
                            createAction(QDate(order.date.date), eventId, clientId, serviceId, code, self._createParams, diagOrder.id, (aidType, aidProfile, aidKind, aidForm, diag, financeId) if self.arkhangelskEncounter else None, diagOrder.reason, specimenValue)
        if not found:
            QtGui.qApp.log('orders', u'Заявок не найдено', level=3)


    def getMisClientId(self, patient):
        for ident in patient.identifier:
            if ident.system == CFHIRExchange.misIdentifierUrn:
                val = ident.value.split(':')
                if len(val) == 3 and val[0] == 'SAMSON':
                    return val[2]
                return ident.value
        return None


    def extractCode(self, coding, uri, ref, path):
        if not coding:
            raise Exception(u'%s в %s пуст' % (path, ref))
        for c in coding:
            if c.system.lower() == uri:
                return c.code
        raise Exception(u'%s в %s не имеет кода для %s' % (path, ref, uri))


    def extractSystemAndDisplay(self, coding, uri, ref, path):
        if not coding:
            raise Exception(u'%s в %s пуст' % (path, ref))
        for c in coding:
            if c.system.lower() == uri:
                display = c.display if hasattr(c, 'display') else None
                return c.system, display
        raise Exception(u'%s в %s не имеет system для %s' % (path, ref, uri))


    def extractCodeEx(self, coding, uriList, ref, path):
        if not coding:
            raise Exception(u'%s в %s пуст' % (path, ref))
        for uri in uriList:
            for c in coding:
                if c.system.lower() == uri:
                    return uri, c.code
        raise Exception(u'%s в %s не имеет кода для %s' % (path, ref, ', '.join(uriList)))



    def lookupInTerminology(self, urn, code):
        request = { 'resourceType': 'Parameters',
                    'parameter': [
                                    { 'name': 'system',
                                      'valueString': urn
                                    },
                                    { 'name': 'code',
                                      'valueString': code
                                    }
                                 ]
                  }

        response = self.getTerminologyClient().server.post_json('ValueSet/$lookup', request).json()
        if 'parameter' not in response:
            raise Exception('Lookup "%s" in %s failed.' % ( code, urn))

        result = {}
        for item in response['parameter']:
            name = item['name']
            value = item['valueString']
            result[name] = value
        return result


    def lookupUnitInTerminology(self, code):
        shortName = u'краткое наименование'
        longName  = u'display'

        d = self.lookupInTerminology(self.unitUrn, code)
        try:
            return d[shortName], d[longName]
        except:
            raise Exception('Lookup "%s" in %s returned unexpected result.' % (code, self.unitUrn))


    def registerUnit(self, code, name, identification):
        # если нужно - добавить ед.изм.
        # и добавить идентификацию...
        db = QtGui.qApp.db
        tableUnit = db.table('rbUnit')
        unitId = forceRef(db.translate(tableUnit, 'code', code, 'id'))
        if unitId is None:
            unitId = forceRef(db.translate(tableUnit, 'name', name, 'id'))
        if unitId is None:
            record = tableUnit.newRecord()
            record.setValue('code',  code)
            record.setValue('name',  name)
            unitId = db.insertRecord(tableUnit, record)
        addIdentification('rbUnit', unitId, self.unitUrn, identification)


    def getUnitId(self, identification):
        # получить rbUnit.id по коду в справочнике self.unitUrn
        # key = (code, shortName if not code else None)
        unitId = self._mapUnitIdentificationToId.get(identification, False)
        if unitId is not False:
            return unitId
        if identification:
            unitId = findByIdentification('rbUnit', self.unitUrn, identification, False)
            if unitId is None:
                unitShortName, unitLongName = self.lookupUnitInTerminology(identification)
                unitId = self.registerUnit(unitShortName, unitLongName, identification)
        else:
            unitId = None
        self._mapUnitIdentificationToId[identification] = unitId
        return unitId


    def getMKBCodes(self, diagnosticReport, refDiagnosticReport):
        result = ''
        if not diagnosticReport.codedDiagnosis:
            return result
        for coding in diagnosticReport.codedDiagnosis:
            uriMKB, codeMKB = self.extractCodeEx(coding.coding,
                                                 [self.ICDUrn,
                                                  self.ICDOncoMorphologyUrn,
                                                  self.ICDOncoTopologyUrn],
                                                  refDiagnosticReport,
                                                  'diagnosticReport.codedDiagnosis.coding'
                                                )
            result = result + codeMKB + ', '
        return result[:-2] if result else ''


    def processDiagnosticReport(self, result, diagnosticReport):
        refDiagnosticReport = diagnosticReport.relativePath()
        serviceCode = self.extractCode(diagnosticReport.code.coding,
                                       self.serviceUrn,
                                       refDiagnosticReport,
                                       'diagnosticReport.name.coding'
                                      )
        issued      = QDateTime.fromString(diagnosticReport.issued.isostring, Qt.ISODate)
        conclusion  = diagnosticReport.conclusion
        categoryCode = None
        categorySystem = None
        if diagnosticReport.category:
            categoryCode = self.extractCode(diagnosticReport.category.coding,
                                            self.PAOMaterialCategoriesUrn,
                                            refDiagnosticReport,
                                            'diagnosticReport.category.coding'
                                           )
            categorySystem, categoryDisplay = self.extractSystemAndDisplay(diagnosticReport.category.coding,
                                                                           self.PAOMaterialCategoriesUrn,
                                                                           refDiagnosticReport,
                                                                           'diagnosticReport.category.coding'
                                                                          )
        serviceResult = CFHIRServiceResult(serviceCode, issued, conclusion)
        if categorySystem:
            MKBCodes = self.getMKBCodes(diagnosticReport, refDiagnosticReport)
            serviceResult.diagnosisMKBCodes = MKBCodes
            serviceResult.category = categoryCode
            displayCategory = ', ' + categoryDisplay if categoryDisplay else ''
            effectivePeriod = (diagnosticReport.effectivePeriod.start.isostring, diagnosticReport.effectivePeriod.end.isostring)
            serviceResult.diagnosticEffectivePeriod = effectivePeriod
            serviceResult.histologyConclusion = '\n'.join([u'Заключение: ' + conclusion,
                                                           u'Диагноз: ' + MKBCodes, 
                                                           u'Дата регистрации биопсийного (операционного) материала: ' + effectivePeriod[0].replace('T', ' '),
                                                           u'Дата проведения прижизненного патолого-анатомического исследования: ' + effectivePeriod[1].replace('T', ' '),
                                                           u'Категория сложности: ' + categoryCode + displayCategory,
                                                           u'\n'
                                                          ]
                                                         )
        if diagnosticReport.identifier:
            identifier = diagnosticReport.identifier
            for ident in identifier:
                if ident.system == self.namespaceEpidCaseIdent:
                    if hasattr(ident.assigner, 'display') and ident.assigner.display == u'Эпидномер':
                        if (    ident.type
                            and hasattr(ident.type, 'coding')
                            and ident.type.coding[0].system == self.fhirIdentifierTypes
                            and ident.type.coding[0].code == 'RRI'
                        ):
                            serviceResult.identifier = ident
                            break
        for item in diagnosticReport.result or []:
            observation = Observation.read_from(item.reference, self.smart.server)
            refObservation = observation.relativePath()
            urn, code = self.extractCodeEx(observation.code.coding,
                                           [ self.testUrn,
                                             self.cytologyResultUrn,
                                             self.histologyResultUrn,
                                           ],
                                        refObservation,
                                           'observation.code.coding',
                                   )
            if urn == self.testUrn:
                testCode = code
            elif urn == self.cytologyResultUrn:
                testCode = 'cytology'
                observation.valueString = self.lookupInTerminology(urn, code).get('display')
            elif urn == self.histologyResultUrn:
                testCode = 'histology:' + code
            else:
                assert False, 'unknown URN'
            value = CFHIRResultValue(testCode)
            if testCode == 'histology:1':
                issuedTime = observation.issued.date
                value.issuedTime = issuedTime.strftime('%Y-%m-%d %H:%M:%S')
            if observation.valueQuantity is not None:
                valueQuantity = observation.valueQuantity
                value.value = float(valueQuantity.value)
                value.unitId = self.getUnitId(valueQuantity.code)
                if observation.referenceRange:
                    if len(observation.referenceRange) not in (1,2):
                        raise Exception(u'неожиданный observation.referenceRange в %s' % refObservation)
                    for rr in observation.referenceRange:
                        if not value.referenceRange or value.referenceRange == (None, None):
                            rrLow = None
                            if hasattr(rr, 'low'):
                                if ( rr.low is not None
                                    and (rr.low.code  and rr.low.code  != valueQuantity.code)
                                ):
                                    raise Exception(u'разные единицы измерения observation.valueQuantity и observation.referenceRange[0].low в %s' % refObservation)
                                rrLow = rr.low.value if rr.low else None
                            rrHigh = None
                            if hasattr(rr, 'high'):
                                if ( rr.high is not None
                                    and (rr.high.code  and rr.high.code  != valueQuantity.code)
                                ):
                                    raise Exception(u'разные единицы измерения observation.valueQuantity и observation.referenceRange[0].high в %s' % refObservation)
                                rrHigh = rr.high.value if rr.high else None
                            value.referenceRange = (rrLow, rrHigh)
                            if value.referenceRange and value.referenceRange != (None, None):
                                break
                    if not value.referenceRange or value.referenceRange == (None, None):
                        for rrt in observation.referenceRange:
                            if hasattr(rrt, 'text') and rrt.text:
                                value.referenceRangeText = rrt.text or ''
            elif observation.valueString is not None:
                value.value = unicode(observation.valueString)
                if observation.referenceRange:
                    for rrt in observation.referenceRange:
                        if hasattr(rrt, 'text') and rrt.text:
                            value.referenceRangeText = rrt.text or ''
                            break
            else:
                raise Exception(u'неожиданный тип observation.value в %s' % refObservation)
            serviceResult.values.append(value)
        result.addServiceResult(serviceResult)


    def requestResultOverFHIR(self, fhirOrderId, pdfFileName):
        try:
#            params = { 'request:Order.id': fhirOrderId }
            params = { 'request': 'Order/%s' % fhirOrderId }
            searchObject = OrderResponse.where(params)
            searchBundle = searchObject.perform(self.smart.server)
            result = CFHIRResult(fhirOrderId)
            if searchBundle and searchBundle.entry is not None:
                orderFinished = False
                orderErrorMessage = ''
                for entry in searchBundle.entry:
                    orderResponse = entry.resource
                    # orderExecDate = QDateTime.fromString(orderResponse.date.isostring, Qt.ISODate)
                    orderExecDate = QDateTime(orderResponse.date.date)
                    result.execDates.append(orderExecDate)
                    orderFinished = orderFinished or orderResponse.orderStatus in ('completed', 'rejected', 'error', 'cancelled', 'replaced', 'aborted')
                    if orderResponse.fulfillment:
                        for item in orderResponse.fulfillment:
                            diagnosticReport = DiagnosticReport.read_from(item.reference, self.smart.server)
                            self.processDiagnosticReport(result, diagnosticReport)
                            pdfDir = QtGui.qApp.importPDFDir
                            if pdfDir:
                                for index, attachment in enumerate(diagnosticReport.presentedForm if diagnosticReport.presentedForm else []):
                                    binary = Binary.read_from(attachment.url, self.smart.server)
                                    if binary and binary.contentType == 'application/pdf':
                                        fileName = os.path.join(pdfDir, fhirOrderId, "%s_%i.pdf"%(pdfFileName, index))
                                        if not os.path.exists(os.path.dirname(fileName)):
                                            os.makedirs(os.path.dirname(fileName))
                                        with open(fileName, "wb") as f:
                                            f.write(base64.b64decode(binary.content))
                                            QtGui.qApp.log('pdf',
                                                           u'Импортируется pdf из ордера %s' % fhirOrderId,
                                                           level=3)
                    if orderResponse.orderStatus in ('rejected', 'error', 'cancelled'):
                        orderErrorMessage = orderResponse.description
                    else:
                        result.note = orderResponse.description
                if result.serviceResults or orderErrorMessage:
                    result.finished = orderFinished
                    result.errorMessage = orderErrorMessage
            return result
        except Exception as e:
            raise Exception(u'при получении результата по заказу %s произошла ошибка:\n%s' % (fhirOrderId, exceptionToUnicode(e)))


    def findClient(self, patient):
        db = QtGui.qApp.db
        tableClient = db.table('Client')
        tablePolicy = db.table('ClientPolicy')

        clientId = findClientByIdentification(self.codeN3PatientIdentification, patient.id)
#        print 'findClientByIdentification(%r, %r) -> %r' % ( self.codeN3PatientIdentification, patient.id, clientId)
        if not clientId:
            for ident in patient.identifier:
                if ident.system == CFHIRExchange.snilsUrn:
                    cond = [tableClient['SNILS'].eq(ident.value)]
                    record = db.getRecordEx(tableClient, [tableClient['id']], cond)
                    if record:
                        clientId = forceRef(record.value(0))
                        break
                elif (ident.system == CFHIRExchange.oldPolicyUrn or ident.system == CFHIRExchange.volPolicyUrn) and ':' in ident.value:
                    (ser,num) = ident.value.split(':')
                    cond = [tablePolicy['serial'].eq(ser),
                            tablePolicy['number'].eq(num)]
                    record = db.getRecordEx(tablePolicy, [tablePolicy['client_id']], cond)
                    if record:
                        clientId = forceRef(record.value(0))
                        break
                elif ident.system == CFHIRExchange.newPolicyUrn:
                    cond = [tablePolicy['serial'].eq(''),
                            tablePolicy['number'].eq(ident.value)]
                    record = db.getRecordEx(tablePolicy, [tablePolicy['client_id']], cond)
                    if record:
                        clientId = forceRef(record.value(0))
                        break
            if clientId:
#                print 'setClientIdentification(%r, %r, %r)' % (clientId, self.codeN3PatientIdentification, patient.id )
                setClientIdentification(clientId, self.codeN3PatientIdentification, patient.id)
        return clientId


    def createClient(self, patient):
        db = QtGui.qApp.db
        tableClient = db.table('Client')
        tableClientAddress = db.table('ClientAddress')
        tableClientContacts = db.table('ClientContact')
        tablePolicy = db.table('ClientPolicy')
        tableDocument = db.table('ClientDocument')
#        canWeMake = any( ident.system in (CFHIRExchange.oldPolicyUrn, CFHIRExchange.volPolicyUrn, CFHIRExchange.newPolicyUrn, CFHIRExchange.snilsUrn)
#                         for ident in patient.identifier
#                       )
#
#        if canWeMake:
        db.transaction()
        try:
            clientRecord = tableClient.newRecord()
            clientRecord.setValue('lastName', patient.name[0].family[0])
            clientRecord.setValue('firstName', patient.name[0].given[0])
            clientRecord.setValue('patrName', patient.name[0].family[1])
            clientRecord.setValue('birthDate', QDate(patient.birthDate.date))
            clientRecord.setValue('sex', { 'male': 1, 'female': 2 }.get(patient.gender, 0))
            clientId = db.insertRecord(tableClient, clientRecord)
            QtGui.qApp.log('orders', u'Заведена новая запись пациента с id %i'%clientId, level=3)

            for address in (patient.address if patient.address else []):
                if address.use in ['home', 'temp']:
                    addressRecord = tableClientAddress.newRecord()
                    addressRecord.setValue('type',  1 if address.use == 'home' else 0)
                    addressRecord.setValue('client_id', clientId)
                    addressRecord.setValue('freeInput', address.text)
                    db.insertRecord(tableClientAddress, addressRecord)

            for telecom in (patient.telecom if patient.telecom else []):
                if telecom.system == 'phone':
                    contactName = {'home': u'домашний телефон', 'work': u'рабочий телефон',
                                   'mobile': u'мобильный телефон'}.get(telecom.use, None)
                    if contactName:
                        contactRecord = tableClientContacts.newRecord()
                        contactRecord.setValue('contactType_id', forceRef(db.translate('rbContactType', 'name', contactName, 'id')))
                        contactRecord.setValue('client_id', clientId)
                        contactRecord.setValue('contact', telecom.value)
                        contactRecord.setValue('notes', u'Загружен из одли')
                        db.insertRecord(tableClientContacts, contactRecord)

            for ident in patient.identifier:
                if ident.system == CFHIRExchange.snilsUrn:
                    clientRecord.setValue('id', clientId)
                    clientRecord.setValue('SNILS', ident.value)
                    db.updateRecord(tableClient, clientRecord)
                elif ident.system in (CFHIRExchange.oldPolicyUrn, CFHIRExchange.volPolicyUrn, CFHIRExchange.newPolicyUrn):
                    insurerId = findByIdentification('Organisation', CFHIRExchange.hicRegistryUrn, ident.assigner.display.split('.')[-1], False)
                    if insurerId:
                        serialAndNumber = ident.value.rsplit(':',1)
                        serial = serialAndNumber[0] if len(serialAndNumber)>1 else ''
                        number = serialAndNumber[-1]
                        policyRecord = tablePolicy.newRecord()
                        policyRecord.setValue('client_id', clientId)
                        policyRecord.setValue('insurer_id', insurerId)
                        if ident.system == CFHIRExchange.oldPolicyUrn:
                            policyRecord.setValue('policyType_id', self._getPolicyTypeId(True))
                            policyRecord.setValue('policyKind_id', self._getPolicyKindId('1'))
                            policyRecord.setValue('serial', serial)
                            policyRecord.setValue('number', number)
                        elif ident.system == CFHIRExchange.newPolicyUrn:
                            policyRecord.setValue('policyType_id', self._getPolicyTypeId(True))
                            policyRecord.setValue('policyKind_id', self._getPolicyKindId('3'))
                            policyRecord.setValue('number', number)
                        elif ident.system == CFHIRExchange.volPolicyUrn:
                            policyRecord.setValue('policyType_id', self._getPolicyTypeId(False))
                            policyRecord.setValue('serial', serial)
                            policyRecord.setValue('number', number)
                        if ident.period:
                            policyRecord.setValue('begDate', QDate(ident.period.start.date) if ident.period.start else QDate.currentDate())
                            if ident.period.end:
                                policyRecord.setValue('endDate', QDate(ident.period.end.date))
                        else:
                            policyRecord.setValue('begDate', QDate.currentDate())
                        db.insertRecord(tablePolicy, policyRecord)
                    else:
                        QtGui.qApp.log('orders', u'Страховая «%s» не найдена в базе данных' % ident.assigner.display)

                elif ident.system.startswith(CFHIRExchange.documentTypeUrn):
                    documentTypeCode = ident.system[len(CFHIRExchange.documentTypeUrn)+1:]
                    documentTypeId   = findByIdentification('rbDocumentType', CFHIRExchange.documentTypeUrn, documentTypeCode, False)
                    if documentTypeId:
                        serialAndNumber = ident.value.rsplit(':',1)
                        serial = serialAndNumber[0] if len(serialAndNumber)>1 else ''
                        number = serialAndNumber[-1]
                        if ident.system == u'urn:oid:1.2.643.2.69.1.1.1.6.14' and len(serial) == 4:
                            serial = serial[:2] + ' ' + serial[2:]
                        if ident.system == u'urn:oid:1.2.643.2.69.1.1.1.6.3' and (len(serial) == 3 or len(serial) == 4):
                            serial = serial[:-2] + '-' + serial[-2:]
                        documentRecord = tableDocument.newRecord()
                        documentRecord.setValue('client_id', clientId)
                        documentRecord.setValue('documentType_id', documentTypeId)
                        documentRecord.setValue('serial',          serial)
                        documentRecord.setValue('number',          number)
                        documentRecord.setValue('date',            QDate(ident.period.start.date) if  ident.period and ident.period.start else QDate())
                        documentRecord.setValue('origin',          ident.assigner.display if ident.assigner else '')
                        db.insertRecord(tableDocument, documentRecord)

            setClientIdentification(clientId, self.codeN3PatientIdentification, patient.id)
            db.commit()
            return clientId

        except Exception as e:
            db.rollback()
            print e
        return None


    def findOrCreateClient(self, patient):
        clientId = self.findClient(patient)
        if not clientId:
            clientId = self.createClient(patient)
        return clientId


#def getOrgStructureIdentification(orgStructureId, urn):
#    db = QtGui.qApp.db
#    table = db.table('OrgStructure')
#    tmpOrgStructureId = orgStructureId
#    while tmpOrgStructureId:
#        code, version = getIdentificationEx('OrgStructure', tmpOrgStructureId, urn, False)
#        if code:
#            return code
#        tmpOrgStructureId = forceRef(db.translate(table, 'id', tmpOrgStructureId, 'parent_id'))
#    raise CIdentificationException(u'Для %s.id=%s не задан код в системе %s' % ('OrgStructure', orgStructureId, urn))


def getOrganizationIdentification(urn, orgId):
#    db = QtGui.qApp.db
    code, version = getIdentificationEx('Organisation', orgId, urn, False)
    if code:
        return code
    raise CIdentificationException(u'Для %s.id=%s не задан код в системе %s' % ('Organisation', orgId, urn))


def downloadVersionsOfDictionaries(terminologyClient):
    request = { 'resourceType': 'Parameters',
                'parameter': [
                    { 'name': 'objectGUID',
                      'valueString': ''
                    }
                ]
              }
    response = terminologyClient.server.post_json('$dictionaries', request).json()

    assert response['parameter'][0]['name'] == 'result'
    dictionaries = response['parameter'][0]['valueString']

    parser = xml.sax.make_parser()
    handler = ArrayOfDictionaryContractHandler()
    parser.setContentHandler(handler)
    parser.setFeature(xml.sax.handler.feature_namespaces, True)
    parser.parse(StringIO(dictionaries.encode('utf-8')))
    return handler.mapUriToVersion


class ArrayOfDictionaryContractHandler(xml.sax.handler.ContentHandler):
    nsNetrika = 'http://schemas.datacontract.org/2004/07/Netrika.TS.Contracts.Contracts'
    nsXml     = 'http://www.w3.org/2001/XMLSchema-instance'

    ArrayOfDictionaryContract = (nsNetrika, 'ArrayOfDictionaryContract')
    DictionaryContract        = (nsNetrika, 'DictionaryContract')
    Comment                   = (nsNetrika, 'Comment')
    Id                        = (nsNetrika, 'Id')
    IsModify                  = (nsNetrika, 'IsModify')
    LastUpdate                = (nsNetrika, 'LastUpdate')
    Name                      = (nsNetrika, 'Name')
    ParentName                = (nsNetrika, 'ParentName')
    SystemName                = (nsNetrika, 'SystemName')
    Uri                       = (nsNetrika, 'Uri')
    Version                   = (nsNetrika, 'Version')

    structure = { None                      : set([ArrayOfDictionaryContract]),
                  ArrayOfDictionaryContract : set([DictionaryContract]),
                  DictionaryContract        : set([Comment, Id, IsModify, LastUpdate, Name, ParentName, SystemName, Uri, Version]),
                }

    xmlNil = ( nsXml, 'nil' )

    def __init__(self):
        self.path = [None]
        self.mapUriToVersion = {}
        self.dictDef = {}


    def startElementNS(self, name, qname, attrs):
        assert name in self.structure[self.path[-1]]
        if name in self.structure[self.DictionaryContract]:
            if attrs.get(self.xmlNil) == 'true':
                self.dictDef.setdefault(name, None)
            else:
                self.dictDef.setdefault(name, '')
        self.path.append(name)


    def endElementNS(self, name, qname):
        self.path.pop()

        if name == self.DictionaryContract:
            uri = self.dictDef.get(self.Uri)
            if ':' not in uri:
                uri = 'urn:oid:' + uri
            version = self.dictDef.get(self.Version)
            version = version.replace('"','')
            self.mapUriToVersion[uri] = version
            self.dictDef.clear()


    def characters(self, content):
        el = self.path[-1]
#        if el in ( self.Uri, self.Version ):
        self.dictDef[el] = content


def findEvent(externalId):
    db = QtGui.qApp.db
    tableEvent = db.table('Event')
    record = db.getRecordEx(tableEvent, [tableEvent['id']], [tableEvent['srcNumber'].eq(externalId), tableEvent['deleted'].eq(0)])
    return forceRef(record.value(0)) if record else None


def createEvent(clientId, extClientId, order, params,  aidType = None):
    eventId = None
    externalId = order.id
    orderDate = forceDate(order.date.date)
    orgId = findByIdentification('Organisation', CFHIRExchange.orgUrn, order.identifier[0].assigner.reference.split('/')[1], False)
    db = QtGui.qApp.db
    tableEvent = db.table('Event')
    if aidType:
        eventTypeDict = params.get('eventTypeByAID', {})
        eventTypeId = eventTypeDict.get(aidType, None)
    else:
        eventTypeId = params.get('eventTypeId', None)
    contractId = params.get('contractId', None)
#    currentOrgId = QtGui.qApp.currentOrgId()
    try:
        db.transaction()
        eventRecord = tableEvent.newRecord()
        eventRecord.setValue('eventType_id', eventTypeId)
        eventRecord.setValue('contract_id', contractId)
        eventRecord.setValue('setDate', QDate(order.date.date))
        eventRecord.setValue('personId', 1)
        eventRecord.setValue('externalId', extClientId)
        eventRecord.setValue('srcNumber', externalId)
        eventRecord.setValue('srcDate', orderDate)
        eventRecord.setValue('relegateOrg_id', orgId if orgId else None)
        eventRecord.setValue('client_id', clientId)
        eventRecord.setValue('isPrimary', 1)
        eventRecord.setValue('order', 1)
        eventRecord.setValue('note', '')
        eventRecord.setValue('totalCost', 0)
        eventId = db.insertRecord(tableEvent, eventRecord)
        db.commit()
    except Exception as e:
        db.rollback()
        QtGui.qApp.log(u'fhir orders error', e)
    return eventId


class CFakeCmbPerson(object): ### WFT
    def value(self):
        return 1


class CFakeEditor(object):  ### WFT
    eventDate = QDate.currentDate()
    eventSetDateTime = QDateTime.currentDateTime()
    eventTypeId = None
    contractId = None
    orgId = None
    personId = 1
    def __init__(self, eventId, clientId, params, date):
        self.cmbSetPerson = CFakeCmbPerson()
        self._id = eventId
        self.clientId = clientId
        self.orgId = QtGui.qApp.currentOrgId()
        self.clientSex = None
        self.clientAge = None
        self.clientWorkOrgId = None
        self.clientPolicyInfoList = []
        self.eventTypeId = params.get('eventTypeId', None) # 101
        self.contractId = params.get('contractId', None) #1270
        self.actionFinance = params.get('actionFinance', 1)
        self.uet = params.get('uet', 1)
        self.personId = params.get('personId', 1)
        self.eventSetDateTime = date
        self.eventDate = date


    def getSuggestedPersonId(self):
        return self.personId


    def getActionFinanceId(self, record):
        return self.actionFinance


    def getUet(self, actionTypeId, personId, financeId, contractId):
        return self.uet


def createAction(date, eventId, clientId, serviceId, code, params, externalId, arkhProps = None, reason = None, specimen = None):
    db = QtGui.qApp.db
    tableAction = db.table('Action')
    tableActionType = db.table('ActionType')
    actionTypeId = forceRef(db.translate(tableActionType, 'nomenclativeService_id', serviceId, 'id'))
    if not actionTypeId:
        actionTypeId = forceRef(db.translate(tableActionType, 'code', code, 'id'))
    if actionTypeId:
        actionRecord = tableAction.newRecord()
        actionRecord.append( QtSql.QSqlField('externalId') )
        actionRecord.setValue('externalId', externalId)
        editor = CFakeEditor(eventId, clientId, params, date) ### WTF
        action = CAction.getFilledAction(editor, actionRecord, actionTypeId) ### WFT
        if arkhProps:
            (aidType, aidProfile, aidKind, aidForm, diag, financeId) = arkhProps
            for ptId,  pt in action.getType().getPropertiesById().items():
                if pt.descr == 'PROFIL':
                    action[pt.name] = aidProfile
                elif pt.descr == 'USL_OK':
                    action[pt.name] = aidType
                elif pt.descr == 'VIDPOM':
                    action[pt.name] = aidKind
                elif pt.descr == 'FOR_POM':
                    action[pt.name] = aidForm
                elif pt.descr == '#ODLI DiagnosticOrder.reason' and type(reason) == list and len(reason) > 0:
                    action[pt.name] = reason[0].text
                elif pt.descr == 'ORD_NO' and specimen:
                    action[pt.name] = specimen
            action.setFinanceId(financeId)
            action._record.setValue('MKB', toVariant(diag))
        action.save()
