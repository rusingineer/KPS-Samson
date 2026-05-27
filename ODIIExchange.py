# -*- coding: utf-8 -*-
import base64
import re
import datetime
import json
import logging
import os
import sys
import traceback
import uuid
import xml.sax
import cStringIO as StringIO
from collections import namedtuple
from logging.handlers import RotatingFileHandler
from optparse import OptionParser
from hashlib import md5

import isodate
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import QDir, QDate, QDateTime, QVariant

from Events.Action import CAction
from Events.ActionInfo import CActionInfo
from Events.ActionStatus import CActionStatus
from Events.Utils import CFinanceType
from Exchange.FHIRClient4.models.annotation import Annotation
from Exchange.FHIRClient4.models.attachment import Attachment
from Exchange.FHIRClient4.models.binary import Binary
from Exchange.FHIRClient4 import client
from Exchange.FHIRClient4.models.address import Address

from Exchange.FHIRClient4.models.codeableconcept import CodeableConcept
from Exchange.FHIRClient4.models.coding import Coding
from Exchange.FHIRClient4.models.condition import Condition
from Exchange.FHIRClient4.models.diagnosticreport import DiagnosticReport
from Exchange.FHIRClient4.models.encounter import Encounter, EncounterDiagnosis
# from Exchange.FHIRClient4.models.endpoint import Endpoint
from Exchange.FHIRClient4.models.fhirdate import FHIRDate
from Exchange.FHIRClient4.models.fhirreference import FHIRReference
from Exchange.FHIRClient4.models.humanname import HumanName
from Exchange.FHIRClient4.models.identifier import Identifier
from Exchange.FHIRClient4.models.imagingstudy import ImagingStudy
from Exchange.FHIRClient4.models.meta import Meta
from Exchange.FHIRClient4.models.observation import Observation
from Exchange.FHIRClient4.models.organization import Organization
from Exchange.FHIRClient4.models.parameters import Parameters, ParametersParameter
from Exchange.FHIRClient4.models.patient import Patient
from Exchange.FHIRClient4.models.period import Period
from Exchange.FHIRClient4.models.practitioner import Practitioner
from Exchange.FHIRClient4.models.practitionerrole import PractitionerRole
from Exchange.FHIRClient4.models.bundle import BundleEntry, Bundle
from Exchange.FHIRClient4.models.quantity import Quantity
from Exchange.FHIRClient4.models.servicerequest import ServiceRequest
from Exchange.FHIRClient4.models.task import Task
from Exchange.FHIRClient4.server import FHIRUnprocessableEntityException, FHIRBadRequestException, \
    FHIRUnauthorizedException, FHIRPermissionDeniedException
from Orgs.Utils import getOrgStructureDescendants, getOrgStructures
from Registry.Utils import getClientInfo
from library import database
from library.Attach.AttachedFile import CAttachedFilesLoader
from library.Attach.WebDAVInterface import CWebDAVInterface
from library.Identification import getIdentificationEx, getIdentification, CIdentificationException
from library.Preferences import CPreferences
from library.PrintInfo import CInfoContext
from library.Utils import anyToUnicode, forceString, forceRef, forceBool, forceDate, toVariant, quote, \
    forceInt, nameCase, formatName
import platform

_referral = namedtuple('referral', ('actionId', 'eventId', 'exportId', 'externalId', 'exportHash'))


def createDispReference(display):
    reference = FHIRReference()
    reference.display = display
    return reference


def _guessPolicyKindCode(serial, number):
    if number.isdigit():
        if (not serial or serial.upper() == u'ЕП') and len(number) == 16:
            return '3'
        if (not serial or serial.upper() == u'ВР') and len(number) == 9:
            return '2'
        if len(serial) > 1 and len(number) >= 6:
            return '1'
    return None


def createOrganization(fhirId):
    org = Organization()
    org.id = fhirId
    return org


def createEmptyTransactionBundle():
    result = Bundle()
    result.type = 'transaction'
    result.entry = []
    return result


def createBundleReference(url):
    reference = FHIRReference()
    reference.reference = url
    return reference


def addBundleEntry(bundle, resource, namespace, ourId):
    entry = BundleEntry()
    entry.fullUrl = 'urn:uuid:%s' % (resource.id if resource.id else uuid.uuid5(namespace, repr(ourId)))
    entry.resource = resource
    bundle.entry.append(entry)
    return createBundleReference(entry.fullUrl)


def createIdentifier(system, value, assigner=None, use=None):
    identifier = Identifier()
    identifier.system = system
    identifier.value = value
    identifier.assigner = assigner
    if use:
        identifier.use = use
    return identifier


class CODIIExchange(QtCore.QCoreApplication):
    defaultFhirUrl = 'http://r23-rc.zdrav.netrika.ru/Imaging/exlab/api/fhir/'
    defaultTerminologyUrl = 'http://r23.zdrav.netrika.ru/nsi/fhir/term'
    defaultAuthorization = 'N3 8b986d46-773d-4a97-a197-59862d78b4fa'
    # defaultMisOid = '1.2.643.2.69.1.2.5'  # МИС ОИД #Переехало в GlobalPreferences.Code == Netrika.MIS_OID
    misIdentifierUrn = 'urn:oid:1.2.643.5.1.13.2.7.100.5'  # OID для идентификатора в МИС/ЛИС
    documentTypeUrn = 'urn:oid:1.2.643.2.69.1.1.1.6'  # OID для разных документов
    documentProviderUrn = 'urn:netrika:documentProvider'  # УФМС, ЗАГС и т.п.
    snilsUrn = 'urn:oid:1.2.643.2.69.1.1.1.6.223'  # OID ПФР для СНИЛСа
    oldPolicyUrn = 'urn:oid:1.2.643.2.69.1.1.1.6.226'  # OID для страхового полиса ОМС старого образца
    tmpPolicyUrn = 'urn:oid:1.2.643.2.69.1.1.1.6.227'  # OID для временного свидетельства
    newPolicyUrn = 'urn:oid:1.2.643.2.69.1.1.1.6.228'  # OID для страхового полиса ОМС единого образца
    volPolicyUrn = 'urn:oid:1.2.643.2.69.1.1.1.6.240'  # OID для страхового полиса ДМС
    #
    orgUrn = 'urn:oid:1.2.643.2.69.1.1.1.64'  # кодификатор организаций
    orgUrnExternal = 'urn:odiiExternalOtdGUID' # кодификатор внешних организаций (для выгрузки в конкретные отделения)
    hicRegistryUrn = 'urn:oid:1.2.643.5.1.13.2.1.1.635'  # Реестр СМО (ФФОМС)
    hicRegistryOid = '1.2.643.5.1.13.2.1.1.635'  # Реестр СМО (ФФОМС)

    specialityUrn = 'urn:oid:1.2.643.5.1.13.13.11.1066'  # Специальности
    roleUrn = 'urn:oid:1.2.643.5.1.13.13.11.1002'  # Роли (Должности)

    serviceUrn = 'urn:oid:1.2.643.5.1.13.13.11.1471'
    categoryUrn = 'urn:oid:1.2.643.5.1.13.13.11.1472'

    urnFinances = 'urn:oid:1.2.643.2.69.1.1.1.32'  # Источники финансирования
    urnResearchArea = 'urn:oid:1.2.643.5.1.13.13.11.1477'  # Анатомические локализации

    urnCaseClasses = 'urn:oid:2.16.840.1.113883.1.11.13955'
    urnCaseTypes = 'urn:oid:1.2.643.2.69.1.1.1.35'
    CaseTypeVersion = '6'
    CasePolyclinic = '2'
    urnReasons = 'urn:oid:1.2.643.2.69.1.1.1.19'

    urnDiagnosisStatus = 'urn:oid:2.16.840.1.113883.4.642.1.1075'
    urnCategory = 'urn:oid:1.2.643.2.69.1.1.1.36'
    urnMKB = 'urn:oid:1.2.643.5.1.13.13.11.1005'
    urnObservation = 'urn:oid:1.2.643.2.69.1.1.1.37'
    urnResultObservation = 'urn:oid:1.2.643.2.69.1.1.1.119'

    accessionNumberUrn = '1.2.643.2.69.1.1.1.122'

    # Появилась затея - для идентификаторов элементов bundle использовать не случайные guid-ы (uuid4),
    # а guid-ы, основанные на id записи. Это должно помочь при сравнении bundle, поскольку сходные
    # элементы получают сходные url-ы. Выбрал uuid5, вот для них пространства имён:
    NS_PATIENT = uuid.UUID(bytes='Patient'.ljust(16, '\0'))
    NS_PRACTITIONER = uuid.UUID(bytes='Practitioner'.ljust(16, '\0'))
    NS_PRACTITIONER_ROLE = uuid.UUID(bytes='PractitionerRole'.ljust(16, '\0'))
    NS_SERVICE_REQUEST = uuid.UUID(bytes='ServiceRequest'.ljust(16, '\0'))
    NS_DIAGNOSTIC_RESULT = uuid.UUID(bytes='DiagnosticResult'.ljust(16, '\0'))
    NS_ENCOUNTER = uuid.UUID(bytes='Encounter'.ljust(16, '\0'))
    NS_CONDITION = uuid.UUID(bytes='Condition'.ljust(16, '\0'))
    NS_OBSERVATION = uuid.UUID(bytes='Observation'.ljust(16, '\0'))
    NS_TASK = uuid.UUID(bytes='Task'.ljust(16, '\0'))
    NS_FILEATTACH = uuid.UUID(bytes='FAttach'.ljust(16, '\0'))
    NS_FILEATTACH_PERSON_SIGNATURE = uuid.UUID(bytes='Signature(P)'.ljust(16, '\0'))
    NS_FILEATTACH_ORG_SIGNATURE = uuid.UUID(bytes='Signature(O)'.ljust(16, '\0'))

    iniFileName = '/root/.config/samson-vista/ODIIExchange.ini'
    # Путь к инишнику для тестирования на Windows
    # iniFileName = 'C:\Users\prog5\AppData\Roaming\samson-vista\ODIIExchange.ini'

    def __init__(self, args):
        parser = OptionParser(usage="usage: %prog [options]")
        parser.add_option('-r', '--result', dest='idResult', help='', metavar='idResult', default='')
        parser.add_option('-o', '--order', dest='idOrder', help='', metavar='idOrder', default='')
        parser.add_option('-l', '--localResult', dest='idLocalResult', help='', metavar='idLocalResult', default='')
        parser.add_option('-b', '--logBinary', dest='logBinary', help='logging with binary', action='store_true', default=False)
        parser.add_option('-c', '--config', dest='iniFile', help='custom .ini file name', metavar='iniFile', default=CODIIExchange.iniFileName)
        (options, _args) = parser.parse_args()
        parser.destroy()

        QtCore.QCoreApplication.__init__(self, args)
        self.options = options
        self.db = None
        self.preferences = None
        self.mainWindow = None
        self.userHasRight = lambda x: True
        self.showingAttach = lambda: False
        self.userSpecialityId = None
        self.connectionName = 'ODIIExchange'
        if self.options.iniFile:
            self.iniFileName = self.options.iniFile
        elif platform.system() != 'Windows':
            self.iniFileName = '/root/.config/samson-vista/ODIIExchange.ini'
        else:
            self.iniFileName = None
        QtGui.qApp = self
        self.userId = 1
        self.font = lambda: None
        self.logLevel = 2
        if platform.system() != 'Windows':
            self.logDir = '/var/log/ODIIExchange'
        else:
            self.logDir = os.path.join(unicode(QDir().toNativeSeparators(QDir().homePath())), '.ODIIExchange')
        self.logger = self.initLogger(self.getLogFilePath())
        self.localLogger = self.initLogger(self.getLogFilePath(True))
        self.mapUriToVersion = {}
        self._mapPolicyTypeIdToComp = {}
        self._mapPolicyKindIdToCode = {}
        self.fhirUrl = None
        self.terminologyUrl = None
        self.fhirAuth = None
        self.misOid = None
        self.orgId = None
        self.orgCode = None
        self.orgOGRN = None
        self.fhirClient = None
        self.fhirServer = None
        self.days = 7
        self.logExchange = None
        self.mapVerifiers = {}
        self.externalMapVerifiers = {}
        self.externalSystemId = None
        self.webDAVInterface = None
        self.updateJobTicketStatus = False
        self.actionTypeIdLocalResultList = []
        self.exportPDF = True
        self.transferConsent = False
        self.directIntegration = False

    def openDatabase(self):
        self.db = None
        try:
            self.log(u'Запуск функции', u'openDatabase', 3)
            self.db = database.connectDataBase(self.preferences.dbDriverName,
                                               self.preferences.dbServerName,
                                               self.preferences.dbServerPort,
                                               self.preferences.dbDatabaseName,
                                               self.preferences.dbUserName,
                                               self.preferences.dbPassword,
                                               compressData=self.preferences.dbCompressData,
                                               connectionName=self.connectionName)
        except Exception as e:
            self.log('error', anyToUnicode(e), 2)

    def prepare(self):
        self.log(u'Запуск функции', u'prepare', 3)
        self.userId = forceRef(self.db.translate('Person', 'login', u'Админ СОЦ', 'id'))
        self.fhirUrl = forceString(self.preferences.appPrefs.get('url', self.defaultFhirUrl))
        self.terminologyUrl = forceString(self.preferences.appPrefs.get('terminology_url', self.defaultTerminologyUrl))
        self.fhirAuth = forceString(self.preferences.appPrefs.get('authorization', self.defaultAuthorization))
        self.misOid = forceString(self.preferences.appPrefs.get('misoid', self.db.translate('GlobalPreferences', 'code',
                                                                                            'Netrika.MIS_OID',
                                                                                            'value')))
        self.orgId = forceRef(self.preferences.appPrefs.get('orgId', None))
        orgRecord = self.db.getRecord('Organisation', 'infisCode, OGRN', self.orgId)
        if orgRecord:
            self.orgCode = forceString(orgRecord.value('infisCode'))
            self.orgOGRN = forceString(orgRecord.value('OGRN'))

        settings = {'api_base': self.fhirUrl,
                    'app_id': 'samson/0.1',
                    'headers': {'Authorization': self.fhirAuth},
                    'conformance': None,
                    }

        self.mapUriToVersion = self.loadVersionsOfDictionaries(self.terminologyUrl)
        self.fhirClient = client.FHIRClient(settings=settings)
        self.fhirServer = self.fhirClient.server
        self.externalSystemId = forceRef(self.db.translate('rbExternalSystem', 'code', u'N3.РЕГИСЗ.ОДИИ', 'id'))
        self.db.query('CALL getAppLock_prepare()')
        self.webDAVInterface = CWebDAVInterface()
        # --- url берем из настроек в БД
        url = unicode('')
        # url = forceString(self.preferences.appPrefs.get('WebDAVUrl', ''))
        rec_glb = self.db.getRecordEx('GlobalPreferences', 'value', 'code = \'WebDAV\'')
        if rec_glb:
            url = unicode(forceString(rec_glb.value(0)))
            url = url.replace('${dbServerName}', QtGui.qApp.preferences.dbServerName)
        # ---
        self.webDAVInterface.setWebDAVUrl(url)
        tableActionType = self.db.table('ActionType')
        tableAS = self.db.table('rbAccountingSystem')
        tableATI = self.db.table('ActionType_Identification')
        table = tableActionType.innerJoin(tableATI,
                                          [tableATI['master_id'].eq(tableActionType['id']), tableATI['deleted'].eq(0)])

        table = table.innerJoin(tableAS, tableAS['id'].eq(tableATI['system_id']))
        self.actionTypeIdLocalResultList = self.db.getDistinctIdList(table, idCol=[tableActionType['id']],
                                                                     where=[tableAS['code'].eq('ODII_export')])

    def createPractitioner(self, personId):
        u"""
        Ресурс Practitioner предназначен для передачи информации о враче.
        """
        tablePerson = self.db.table('Person')
        personRecord = self.db.getRecord(tablePerson, 'lastName, firstName, patrName, SNILS', personId)
        if not personRecord:
            return None, u'ОДИИ: Не заполнен врач, назначивший исследование'
        snils = forceString(personRecord.value('SNILS'))
        if not snils:
            return None, u'ОДИИ: У врача назначившего исследование не указан СНИЛС'

        lastName = nameCase(forceString(personRecord.value('lastName')))
        firstName = nameCase(forceString(personRecord.value('firstName')))
        patrName = nameCase(forceString(personRecord.value('patrName')))

        practitioner = Practitioner()
        practitioner.active = True
        name = HumanName()
        name.family = lastName or '-'
        name.given = [firstName or '-']
        if patrName:
            name.given.append(patrName)
        practitioner.name = [name]
        practitioner.identifier = [self.createPPMisIdentifierNoURN(personId),  # идентификатор в МИС
                                   ]
        practitioner.identifier.append(self.snilsAsIdentifier(snils))
        return practitioner, None

    def createPractitionerRole(self, personId, practitionerReference):
        u"""
        Ресурс PractitionerRole предназначен для передачи информации о квалификации врача.
        """
        tablePerson = self.db.table('Person')
        personRecord = self.db.getRecord(tablePerson, 'post_id, speciality_id, orgStructure_id', personId)
        if not personRecord:
            return None, u'ОДИИ: Не заполнен врач, назначивший исследование'

        postId = forceRef(personRecord.value('post_id'))
        specialityId = forceRef(personRecord.value('speciality_id'))
        orgStructureId = forceRef(personRecord.value('orgStructure_id'))

        if orgStructureId is None:
            return None, u'ОДИИ: Для врача назначившего исследование (Person.id={0}) не указано подразделение'.format(personId)

        if specialityId is None:
            return None, u'ОДИИ: Для врача назначившего исследование (Person.id={0}) не указана специальность'.format(personId)

        if postId is None:
            return None, u'ОДИИ: Для врача назначившего исследование (Person.id={0}) не указана должность'.format(personId)

        try:
            specialityCode, specialityVersion = getIdentificationEx('rbSpeciality', specialityId, self.specialityUrn)
            postCode, postVersion = getIdentificationEx('rbPost', postId, self.roleUrn)
        except CIdentificationException as e:
            return None, u'ОДИИ: {0}'.format(unicode(e))

        practitionerRole = PractitionerRole()
        practitionerRole.practitioner = practitionerReference
        practitionerRole.active = True
        practitionerRole.organization = self.createOrgStructureReference(orgStructureId)
        practitionerRole.code = [self.createCodeableConcept(self.roleUrn, postCode, postVersion)]
        practitionerRole.specialty = [self.createCodeableConcept(self.specialityUrn, specialityCode, specialityVersion)]

        return practitionerRole, None

    def createPatient(self, clientId, organisationReference, isOMS):
        u"""
        Ресурс Patient предназначен для передачи информации о пациенте.
        """
        clientInfo = getClientInfo(clientId)
        patient = Patient()
        patient.active = True
        name = HumanName()
        name.family = nameCase(clientInfo.lastName) or '-'
        name.given = [nameCase(clientInfo.firstName) or '-']
        if clientInfo.patrName:
            name.given.append(nameCase(clientInfo.patrName))
        name.text = formatName(clientInfo.lastName, clientInfo.firstName, clientInfo.patrName)
        name.use = 'official'
        patient.name = [name]
        patient.gender = {1: 'male', 2: 'female'}.get(clientInfo.sexCode, 'undefined')
        patient.birthDate = dateToFHIRDate(clientInfo.birthDate)

        patient.identifier = [self.createPPMisIdentifierNoURN(clientInfo.id),  # идентификатор в МИС
                              ]
        if clientInfo.documentRecord:
            documentAsIdentifier = self.documentAsIdentifier(clientInfo.documentRecord)
            if documentAsIdentifier is not None:
                patient.identifier.append(documentAsIdentifier)
        if clientInfo.SNILS:
            snils = clientInfo.SNILS.replace('-', '').replace(' ', '')
            patient.identifier.append(self.snilsAsIdentifier(snils))
        policyAsIdentifier = None
        if isOMS and clientInfo.compulsoryPolicyRecord:
            policyAsIdentifier = self.policyAsIdentifier(clientInfo.id, clientInfo.compulsoryPolicyRecord)
            if policyAsIdentifier:
                patient.identifier.append(policyAsIdentifier)
        isNoPolicy = True if isOMS and policyAsIdentifier is None else False

        if clientInfo.voluntaryPolicyRecord:
            policyAsIdentifier = self.policyAsIdentifier(clientInfo.id, clientInfo.voluntaryPolicyRecord)
            if policyAsIdentifier:
                patient.identifier.append(policyAsIdentifier)
        address = None
        if address:
            patient.address = [Address({'use': 'home', 'text': address})]
        patient.managingOrganization = organisationReference
        return patient, isNoPolicy

    def createPPMisIdentifier(self, value):
        return createIdentifier(self.misIdentifierUrn,
                                '%s:%s' % (self.orgCode, value),
                                createDispReference('urn:oid:'+self.misOid)
                                )

    def createMisIdentifier(self, value, use=None):
        return createIdentifier('urn:oid:'+self.misOid,
                                '%s:%s' % (self.orgCode, value),
                                use=use
                                )

    def createPPMisIdentifierNoURN(self, value):
        return createIdentifier(self.misIdentifierUrn,
                                '%s:%s' % (self.orgCode, value),
                                # self.createDispReference('urn:oid:'+self.misOid)
                                createDispReference(self.misOid)
                                )

    def createOrderBundle(self, actionId):
        context = CInfoContext()
        action = CActionInfo(context, actionId)
        personId = action.setPerson.personId
        event = action.getEventInfo()
        eventId = event.id
        clientId = event.client.id
        eventTypeId = event.eventType.id
        medicalAidTypeId = event.eventType.medicalAidType.id
        eventPurposeId = event.eventType.purpose.id
        financeId = event.contract.finance.id
        isPrimary = 'usual' if event.isPrimary == 1 else 'secondary'
        serviceCode = None
        bodySitCodes = []
        note = None
        height = weight = None
        serviceProviderOrgStructureId = None
        serviceExternalProviderOrganisationId = None
        for prop in action._action.getProperties():
            if prop.type().shortName == u'researchKind':
                serviceCode = prop.getInfo(context).code
            elif prop.type().shortName == u'anatomicalLocalizations':
                bodySitCodes = [val.code for val in prop.getInfo(context)]
            elif prop.type().shortName in [u'orgstructName', u'Office', u'externalOtd']:
                if prop.type().shortName == u'externalOtd':
                # 21.05.2025 if action.code == u'soc_odii' and prop.type().shortName == u'externalOtd':
                    serviceExternalProviderOrganisationId = prop.getInfo(context).id
                # 21.05.2025 elif not prop.type().shortName == u'externalOtd':
                else:
                    serviceProviderOrgStructureId = prop.getInfo(context).id
            elif prop.type().shortName == u'height':
                height = prop
            elif prop.type().shortName == u'weight':
                weight = prop
            elif prop.type().shortName == u'note':
                note = prop.getValue()

        mkb = action.MKB.__str__() if action.MKB.__str__() else getEventDiagnosis(eventId)
        if mkb and len(mkb) > 5:
            mkb = mkb[:5]

        bundle = createEmptyTransactionBundle()
        practitioner, actionNote = self.createPractitioner(personId)
        if practitioner is None:
            self.fillActionNoteAndWriteLog(actionId, actionNote)
            return None
        practitionerReference = addBundleEntry(bundle, practitioner, self.NS_PRACTITIONER, personId)
        practitionerRole, actionNote = self.createPractitionerRole(personId, practitionerReference)
        if practitionerRole is None:
            self.fillActionNoteAndWriteLog(actionId, actionNote)
            return None
        practitionerRoleReference = addBundleEntry(bundle, practitionerRole, self.NS_PRACTITIONER_ROLE, personId)
        organisationReference = practitionerRole.organization
        if serviceExternalProviderOrganisationId:
            serviceProviderReference = self.createOrganisationReference(serviceExternalProviderOrganisationId, self.orgUrnExternal)
        else:
            serviceProviderReference = self.createOrgStructureReference(serviceProviderOrgStructureId)
        isOMS = bool(event.contract and event.contract.finance and forceInt(event.contract.finance.code) == CFinanceType.CMI)
        patient, isNoPolicy = self.createPatient(clientId, organisationReference, isOMS)
        if isOMS and isNoPolicy:
            financeCode = '7'
        else:
            financeCode = getIdentification('rbFinance', financeId, self.urnFinances, False)
        patientReference = addBundleEntry(bundle, patient, self.NS_PATIENT, clientId)
        obsCondRefs = []
        condition = self.createCondition(mkb, patientReference)
        conditionReferences = addBundleEntry(bundle, condition, self.NS_CONDITION, eventId)
        obsCondRefs.append(conditionReferences)

        if height and height.getValue() and height.getValue() > 0:
            observation = self.createObservation('1', height.getValue())
            obsCondRefs.append(addBundleEntry(bundle, observation, self.NS_OBSERVATION, height.getId()))
        if weight and weight.getValue() and weight.getValue() > 0:
            observation = self.createObservation('2', weight.getValue())
            obsCondRefs.append(addBundleEntry(bundle, observation, self.NS_OBSERVATION, weight.getId()))

        encounter = self.createEncounter(eventId, eventTypeId, eventPurposeId, medicalAidTypeId,
                                         patientReference, conditionReferences, organisationReference)
        encounterReference = addBundleEntry(bundle, encounter, self.NS_ENCOUNTER, eventId)
        serviceRequest = self.createServiceRequest(serviceCode, bodySitCodes, financeCode, action.isUrgent,
                                                   patientReference, encounterReference, practitionerRoleReference,
                                                   obsCondRefs, note)
        serviceRequestReference = addBundleEntry(bundle, serviceRequest, self.NS_SERVICE_REQUEST, actionId)
        task = self.createTask(actionId, action.begDate.datetime, patientReference, organisationReference,
                               serviceRequestReference, serviceProviderReference, isPrimary)
        addBundleEntry(bundle, task, self.NS_TASK, actionId)

        return bundle

    def createResultBundle(self, actionId):
        context = CInfoContext()
        action = CActionInfo(context, actionId)
        personId = action.person.personId
        event = action.getEventInfo()
        eventId = event.id
        clientId = event.client.id
        eventTypeId = event.eventType.id
        medicalAidTypeId = event.eventType.medicalAidType.id
        eventPurposeId = event.eventType.purpose.id
        serviceCode = None
        categoryCode = None

        prop = action._action.getPropertyByShortName(u'research')
        if prop and prop.getValue():
            serviceCode = prop.getInfo(context).code
            category = prop.getInfo(context).method
            if category:
                if category[:2] == u'КТ' or category[:11] == u'Ангиография':
                    categoryCode = '1'
                elif category[:3] == u'МРТ':
                    categoryCode = '2'
                elif category[:3] == u'УЗД':
                    categoryCode = '3'
                elif category[:7] == u'Рентген':
                    categoryCode = '4'
                elif category[:3] == u'РНД':
                    categoryCode = '5'
                elif category[:2] == u'ФД':
                    categoryCode = '6'
                elif category[:10] == u'Эндоскопия':
                    categoryCode = '7'

        mkb = action.MKB.__str__() if action.MKB.__str__() else getEventDiagnosis(eventId)
        if mkb and len(mkb) > 5:
            mkb = mkb[:5]

        bundle = createEmptyTransactionBundle()
        practitioner, actionNote = self.createPractitioner(personId)
        if practitioner is None:
            self.fillActionNoteAndWriteLog(actionId, actionNote)
            return None
        practitionerReference = addBundleEntry(bundle, practitioner, self.NS_PRACTITIONER, personId)
        practitionerRole, actionNote = self.createPractitionerRole(personId, practitionerReference)
        if practitionerRole is None:
            self.fillActionNoteAndWriteLog(actionId, actionNote)
            return None
        practitionerRoleReference = addBundleEntry(bundle, practitionerRole, self.NS_PRACTITIONER_ROLE, personId)
        organisationReference = practitionerRole.organization

        isOMS = bool(event.contract and event.contract.finance and forceInt(event.contract.finance.code) == CFinanceType.CMI)
        patient, isNoPolicy = self.createPatient(clientId, organisationReference, isOMS)
        patientReference = addBundleEntry(bundle, patient, self.NS_PATIENT, clientId)

        observationReferenceList = []
        condition = self.createCondition(mkb, patientReference)
        conditionReferences = addBundleEntry(bundle, condition, self.NS_CONDITION, eventId)

        prop = action._action.getPropertyByShortName(u'protocol')
        if prop:
            if prop.getValue():
                observation = self.createResultObservation('1', prop.getValue(), action.endDate.datetime, practitionerRoleReference)
                observationReferenceList.append(addBundleEntry(bundle, observation, self.NS_OBSERVATION, prop.getId()))
        else:
            protocolText = u''
            propId = None
            for prop in action._action.getProperties():
                if prop.type().sectionCDA == u'protocol' and prop.getValue():
                    protocolText += prop.type().name + u': ' + forceString(prop.getValue()) + u'\n'
                    if not propId:
                        propId = prop.getId()
            if protocolText:
                observation = self.createResultObservation('1', protocolText, action.endDate.datetime, practitionerRoleReference)
                observationReferenceList.append(addBundleEntry(bundle, observation, self.NS_OBSERVATION, propId))

        prop = action._action.getPropertyByShortName(u'conclusion')
        if prop and prop.getValue():
            observation = self.createResultObservation('2', prop.getValue(), action.endDate.datetime, practitionerRoleReference)
            observationReferenceList.append(addBundleEntry(bundle, observation, self.NS_OBSERVATION, prop.getId()))
        prop = action._action.getPropertyByShortName(u'recommendations')
        if prop and prop.getValue():
            observation = self.createResultObservation('3', prop.getValue(), action.endDate.datetime, practitionerRoleReference)
            observationReferenceList.append(addBundleEntry(bundle, observation, self.NS_OBSERVATION, prop.getId()))

        encounter = self.createEncounter(eventId, eventTypeId, eventPurposeId, medicalAidTypeId,
                                         patientReference, conditionReferences, organisationReference)
        encounterReference = addBundleEntry(bundle, encounter, self.NS_ENCOUNTER, eventId)

        binaryReferenceList = []
        fileList = self.getAttachedFile(QtGui.qApp.webDAVInterface, [action.id])
        fileFilter = ['.xml', '.pdf'] if self.exportPDF else ['.xml']
        fileList = filter(lambda file: file.newName[-4:] in fileFilter, fileList)
        if fileList:
            hasPdf = False
            hasXMl = False
            for attachedFile in sorted(fileList, key=lambda x: x.id, reverse=True):
                try:
                    if attachedFile.newName[-4:] == '.xml' and hasXMl:
                        continue
                    if attachedFile.newName[-4:] == '.pdf' and hasPdf:
                        continue
                    (binary, binRespSign, binaryOrgSign) = self.binarySigned(QtGui.qApp.webDAVInterface, attachedFile)
                    binaryReferenceList.append((addBundleEntry(bundle, binary, self.NS_FILEATTACH, attachedFile.id), binary.contentType))
                    if binRespSign:
                        binaryReferenceList.append((addBundleEntry(bundle, binRespSign, self.NS_FILEATTACH_PERSON_SIGNATURE, attachedFile.id), binRespSign.contentType))
                    if binaryOrgSign:
                        binaryReferenceList.append((addBundleEntry(bundle, binaryOrgSign, self.NS_FILEATTACH_ORG_SIGNATURE, attachedFile.id), binaryOrgSign.contentType))
                    if attachedFile.newName[-4:] == '.xml':
                        hasXMl = True
                    else:
                        hasPdf = True
                except Exception as e:
                    self.log(u'Ошибка выгрузки Action.id={0}'.format(actionId), anyToUnicode(e), level=1)
                    raise Exception(u'Проблемы с получением документа с подписью')
        if not binaryReferenceList:
            action = CAction.getActionById(actionId)
            action.getRecord().setValue('note', toVariant(u'Нет прикрепленного Cda документа'))
            action.save(idx=-1)
            return None

        diagnosticReport = self.createDiagnosticReport(action.endDate.datetime,
                                                       categoryCode,
                                                       serviceCode,
                                                       patientReference,
                                                       practitionerRoleReference,
                                                       encounterReference,
                                                       observationReferenceList,
                                                       binaryReferenceList)
        diagnosticReportReference = addBundleEntry(bundle, diagnosticReport, self.NS_DIAGNOSTIC_RESULT, actionId)

        task = self.createResultTask(actionId, action.endDate.datetime, patientReference, organisationReference, diagnosticReportReference)
        addBundleEntry(bundle, task, self.NS_TASK, actionId)

        return bundle

    def getAttachedFile(self, interface, actionIdList):
        fileList = []
        processed = []
        for actionId in actionIdList:
            files = CAttachedFilesLoader.loadItems(interface, 'Action_FileAttach', actionId)
            for file in files:
                if file and file.id not in processed and file.respSignature:
                    fileList.append(file)
                    processed.append(file.id)
        return fileList

    def binarySigned(self, interface, file):
        binary = respSign = orgSign = None
        extList = ['.pdf', '.xml']
        typeList = ['application/pdf', 'application/xml']
        userSignList = ['application/x-pkcs7-practitioner', 'application/x-pkcs7-practitioner-xml']
        orgSignList = ['application/x-pkcs7-organization', 'application/x-pkcs7-organization-xml']
        xmlCoding = self.createCoding('urn:oid:1.2.643.5.1.13.13.11.1520', '110',)
        metaList = [None, xmlCoding]
        try:
            i = extList.index(file.newName[-4:])
        except:
            raise Exception(u'Расширение файла (%s) не поддерживается' % file.newName[-4:])
        if file:
            bytes = interface.downloadBytes(file)

            binary = Binary()
            binary.contentType = typeList[i]
            binary.data = base64.b64encode(bytes)
            if metaList[i]:
                binary.meta = Meta()
                binary.meta.tag = [metaList[i]]
        if file.respSignature:
            respSign = Binary()
            respSign.contentType = userSignList[i]
            respSign.data = base64.b64encode(file.respSignature.signatureBytes)

        if file.orgSignature:
            orgSign = Binary()
            orgSign.contentType = orgSignList[i]
            orgSign.data = base64.b64encode(file.orgSignature.signatureBytes)
        elif respSign:  # если нет подписи МО, то выгружаем подпись врача с ОГРН
            orgSign = Binary()
            orgSign.contentType = orgSignList[i]
            orgSign.data = respSign.data
        return (binary, respSign, orgSign)

    def fillActionNoteAndWriteLog(self, actionId, note):
        self.log(u'Ошибка выгрузки Action.id={0}'.format(actionId), note, level=1)
        action = CAction(record=self.db.getRecord('Action', '*', actionId))
        action.getRecord().setValue('note', toVariant(note))
        action.save(idx=-1)

    def snilsAsIdentifier(self, snils):
        identifier = createIdentifier(self.snilsUrn,
                                      snils,
                                      createDispReference(u'ПФР')
                                      )
        return identifier

    def _getPolicyTypeComp(self, policyTypeId):
        result = self._mapPolicyTypeIdToComp.get(policyTypeId)
        if result is None:
            result = forceBool(QtGui.qApp.db.translate('rbPolicyType', 'id', policyTypeId, 'isCompulsory'))
            self._mapPolicyTypeIdToComp[policyTypeId] = result
        return result

    def _getPolicyKindCode(self, policyKindId):
        code = self._mapPolicyKindIdToCode.get(policyKindId)
        if code is None:
            code = forceString(QtGui.qApp.db.translate('rbPolicyKind', 'id', policyKindId, 'code'))
            self._mapPolicyKindIdToCode[policyKindId] = code
        return code

    def createOrgStructureReference(self, orgStructureId):
        if orgStructureId is None:
            return None
        fhirId = getOrgStructureIdentification(self.orgUrn, orgStructureId)
        organization = createOrganization(fhirId)
        reference = FHIRReference()
        reference.reference = '%s/%s' % (organization.resource_type, organization.id)
        return reference

    def createOrganisationReference(self, orgId, urn):
        if orgId is None:
            return None
        fhirId = getIdentification('Organisation', orgId, urn)
        organization = createOrganization(fhirId)
        reference = FHIRReference()
        reference.reference = '%s/%s' % (organization.resource_type, organization.id)
        return reference

    def createCodeableConcept(self, system, code, version='', display=''):
        codeableConcept = CodeableConcept()
        codeableConcept.coding = [self.createCoding(system, code, version, display)]
        return codeableConcept

    def createCoding(self, system, code, version='', display=''):
        coding = Coding()
        coding.system = system
        coding.code = code
        coding.version = self.mapUriToVersion.get(system, version)
        if display:
            coding.display = display
        return coding

    ##################################################################
    #
    # Получение версий справочников
    #
    def loadVersionsOfDictionaries(self, terminologyUrl):
        settings = {'api_base': terminologyUrl, 'app_id': 'samson/0.1',
                    'headers': {'Authorization': self.fhirAuth}, 'conformance': None, }

        terminologyClient = client.FHIRClient(settings=settings)
        request = {'resourceType': 'Parameters', 'parameter': [{'name': 'objectGUID', 'valueString': ''}]}
        response = terminologyClient.server.post_json('$dictionaries', request).json()

        assert response['parameter'][0]['name'] == 'result'
        dictionaries = response['parameter'][0]['valueString']

        parser = xml.sax.make_parser()
        handler = ArrayOfDictionaryContractHandler()
        parser.setContentHandler(handler)
        parser.setFeature(xml.sax.handler.feature_namespaces, True)
        parser.parse(StringIO.StringIO(dictionaries.encode('utf-8')))
        return handler.mapUriToVersion

    def closeDatabase(self):
        if self.db:
            self.db.close()
            self.db = None

    def getLogFilePath(self, localLog = False):
        if not os.path.exists(self.logDir):
            os.makedirs(self.logDir)
        dateString = unicode(fmtDateShort(QDate().currentDate()))
        if localLog:
            dateString += u'_protocol'
        else:
            dateString += u'_direction'
        return os.path.join(QtGui.qApp.logDir, '%s.log' % dateString)

    def initLogger(self, logPath):
        formatter = logging.Formatter(fmt='%(asctime)s %(message)s',
                                      datefmt='%Y-%m-%d %H:%M:%S'
                                      )

        handler = RotatingFileHandler(logPath, maxBytes=1024*1024*50, backupCount=10, encoding='UTF-8')
        handler.setFormatter(formatter)
        handler.setLevel(logging.INFO)

        logger = logging.getLogger(logPath)
        logger.setLevel(logging.INFO)

        oldHandlers = list(logger.handlers)
        logger.addHandler(handler)
        for oldHandler in oldHandlers:
            logger.removeHandler(oldHandler)

        return logger

    def loadPreferences(self):
        self.preferences = CPreferences(self.iniFileName if self.iniFileName else 'ODIIExchange.ini')
        self.preferences.load()
        self.logLevel = forceInt(self.preferences.appPrefs.get('logLevel', 2))
        self.days = forceInt(self.preferences.appPrefs.get('days', 7))
        self.updateJobTicketStatus = forceBool(self.preferences.appPrefs.get('updateJobTicketStatus', False))
        self.exportPDF = forceBool(self.preferences.appPrefs.get('exportPDF', True))
        self.transferConsent = forceBool(self.preferences.appPrefs.get('transferConsent', False))
        self.directIntegration = forceBool(self.preferences.appPrefs.get('directIntegration', False))

    def currentOrgId(self):
        return forceRef(self.preferences.appPrefs.get('orgId', QVariant()))

    def log(self, title, message, level=2, stack=None, localLog=False):
        if level <= QtGui.qApp.logLevel:
            # если нет параметра запуска -b, то убираем из логов бинарные данные
            if not self.options.logBinary:
                if isinstance(message, dict) and 'entry' in message:
                    for entry in message['entry']:
                        resource = entry.get('resource', {})
                        if isinstance(resource, dict) and resource.get('resourceType') == 'Binary':
                            entry['resource'] = ''
                elif "entry" in message:
                    pattern = r'"resourceType"\s*:\s*"Binary"\s*,[\s\S]*?"data"\s*:\s*"[^"]+"'
                    message = re.sub(pattern, '"resourceType": "Binary"', message)
            logString = u'%s: %s\n' % (title, message)
            if stack:
                try:
                    logString += anyToUnicode(''.join(traceback.format_list(stack))).decode('utf-8') + '\n'
                except:
                    logString += 'stack lost\n'
            if not localLog:
                self.logger.info(logString)
            else:
                self.localLogger.info(logString)

    def logException(self, exceptionType, exceptionValue, exceptionTraceback):
        title = repr(exceptionType)
        message = anyToUnicode(exceptionValue)
        self.log(title, message, 0, traceback.extract_tb(exceptionTraceback))
        sys.__excepthook__(exceptionType, exceptionValue, exceptionTraceback)

    def logCurrentException(self):
        self.logException(*sys.exc_info())

    def main(self):
        self.loadPreferences()
        if self.preferences:
            self.log(u'Запуск функции', u'main (Начало процесса)', 3)
            self.openDatabase()
            if self.db:
                self.registerDocumentTables()
                self.prepare()
                if self.options.idOrder:
                    referrals = self.selectReferrals(self.options.idOrder)
                    for referral in referrals.values():
                        try:
                            self.sendOrder(referral)
                        except:
                            self.logCurrentException()
                elif self.options.idResult:
                    referrals, tasks = self.selectReferralsForResult(self.options.idResult)
                    try:
                        resultBundle = self.searchResultBatch(tasks)
                    except:
                        resultBundle = None
                        self.logCurrentException()
                    if resultBundle and resultBundle.total > 0:
                        for entry in resultBundle.entry:
                            try:
                                self.saveResult(entry, referrals)
                            except:
                                self.logCurrentException()
                elif self.options.idLocalResult:
                    results = self.selectResults(self.options.idLocalResult)
                    for result in results.values():
                        try:
                            self.sendLocalResult(result)
                        except:
                            self.logCurrentException()
                else:
                    # отправка заявок
                    referrals = self.selectReferrals()
                    for referral in referrals.values():
                        try:
                            res_mess = self.sendOrder(referral)
                            if not self.checkWebServiceConnect(res_mess):
                                self.log(u'main', u'(окончание процесса)', 3)
                                return
                        except:
                            self.logCurrentException()
                    # отправка локальных результатов
                    results = self.selectResults()
                    for result in results.values():
                        try:
                            res_mess = self.sendLocalResult(result)
                            if not self.checkWebServiceConnect(res_mess):
                                self.log(u'main', u'(окончание процесса)', 3)
                                return
                        except:
                            self.logCurrentException()
                    # загрузка результатов
                    referrals, tasks = self.selectReferralsForResult()
                    try:
                        resultBundle = self.searchResultBatch(tasks)
                    except:
                        resultBundle = None
                        self.logCurrentException()
                    if resultBundle and resultBundle.total > 0:
                        for entry in resultBundle.entry:
                            try:
                                self.saveResult(entry, referrals)
                            except:
                                self.logCurrentException()
        self.closeDatabase()
        self.log(u'main', u'(окончание процесса)', 3)

    def checkWebServiceConnect(self, res_mess):
        self.log(u'Запуск функции', u'checkWebServiceConnect', 3)
        if res_mess and (
                res_mess.find("Max retries exceeded with url") > 0 or
                res_mess.find("Gateway Time-out for url") > 0
        ):
            self.log('error', u"Web-сервис недоступен! Процесс прекращен", 2)
            self.closeDatabase()
            return False
        return True

    def getResource(self, resourceClass, resId, logResponse=True):
        path = '/imaging/exlab/api/fhir/' + resId
        resource = None
        res = self.fhirServer._get(path)
        if logResponse:
            self.log(u'Получение ресурса {0}'.format(resId), res.content.decode('utf-8'), level=1)
        if res.status_code == 200:
            resource = resourceClass(jsondict=json.loads(res.content))
        return resource

    def loadBinary(self, action, personId, resourceId, contentType):
        binary = self.getResource(Binary, resourceId, logResponse=False)
        if binary and hasattr(QtGui.qApp, 'webDAVInterface'):
            storageInterface = QtGui.qApp.webDAVInterface
            if storageInterface:
                name = u'ProtocolRIS_' + binary.id + u'.{0}'.format(contentType[-3:])
                _file = storageInterface.uploadBytes(name, binary.data.decode('base64'))
                _file.setAuthorId(personId)
                action._attachedFileItemList.append(_file)
                return _file
        return None

    def loadSign(self, _file, personId, resourceId, contentType):
        binary = self.getResource(Binary, resourceId, logResponse=False)
        if binary and _file:
            if contentType in ['application/x-pkcs7-practitioner', 'application/x-pkcs7-practitioner-xml']:
                _file.setRespSignature(binary.data.decode('base64'), personId, QDateTime.currentDateTime())
            else:
                _file.setOrgSignature(binary.data.decode('base64'), personId, QDateTime.currentDateTime())

    def sendOrder(self, referral):
        self.log(u'Запуск функции', u'sendOrder', 3)
        note = ''

        actionId = referral.actionId
        exportId = referral.exportId
        externalId = referral.externalId
        exportHash = referral.exportHash

        lockId = None
        try:
            self.db.query('CALL getAppLock_(%s, %d, %d, %s, %s, @res)' % (
            quote('Event'), referral.eventId, 0, 1, quote('ODIIExchange')))
            query = self.db.query('SELECT @res')

            if query.next():
                record = query.record()
                s = forceString(record.value(0)).split()
                if len(s) > 1:
                    isSuccess = int(s[0])
                    if isSuccess:
                        lockId = int(s[1])
                    else:
                        self.log(u'Отправка направления actionId={0} eventId={1}'.format(actionId, referral.eventId),
                                 u'Событие %i заблокировано' % referral.eventId, level=1)
            if lockId:
                bundle = self.createOrderBundle(actionId)
                if bundle is None:
                    # снимаем блокировку
                    if lockId:
                        self.db.query('CALL ReleaseAppLock(%d)' % lockId)
                    return None

                bundleJson = bundle.as_json()
                bundleStr = json.dumps(bundleJson)
                bundleHash = md5(bundleStr).hexdigest()
                if bundleHash == exportHash:
                    self.log(u'Направление не отправлено, ошибки не исправлены. actionId={0} eventId={1} запрос'.format(actionId, referral.eventId), bundleJson, level=1)
                    # снимаем блокировку
                    if lockId:
                        self.db.query('CALL ReleaseAppLock(%d)' % lockId)
                    return None
                self.log(u'Отправка направления actionId={0} eventId={1} запрос'.format(actionId, referral.eventId), bundleJson, level=1)
                resBundle = None
                try:
                    note = message = ''
                    res = self.fhirServer.post_json('',  bundle.as_json())
                    message = res.content.decode('utf-8')
                    note = u'Заказ успешно выгружен в ОДИИ {0}'.format(fmtDate(self.db.getCurrentDatetime()))
                    resBundle = Bundle(jsondict=json.loads(res.content))
                except FHIRBadRequestException as e:
                    try:
                        resBundle = None
                        response = e.response.json()
                        note = response['issue'][0]['diagnostics']
                        message = json.dumps(response, sort_keys=True, indent=4, ensure_ascii=False)
                    except:
                        note = 'Bad Request'
                        message = anyToUnicode(e.response.text)
                except FHIRUnauthorizedException:
                    resBundle = None
                    message = note = 'Unauthorized'
                except FHIRPermissionDeniedException:
                    resBundle = None
                    message = note = 'Permission Denied'
                except FHIRUnprocessableEntityException as e:
                    try:
                        resBundle = None
                        response = e.response.json()
                        note = u'Ошибка валидации.'
                        for issue in response['issue']:
                            note += u' ' + issue['diagnostics']
                            if u'Попытка повторного добавления Task' in issue['diagnostics']:
                                externalId = issue['diagnostics'][issue['diagnostics'].find(u'Task/') + 5:]
                                note = u'Заказ успешно выгружен в ОДИИ {0}'.format(fmtDate(self.db.getCurrentDatetime()))
                                break
                            if issue['diagnostics'] == u'Параметр обязательный и не должен быть пустым':
                                note += u': ' + ', '.join(issue['location']) + u';'
                            else:
                                note += u'.'
                        message = json.dumps(response, sort_keys=True, indent=4, ensure_ascii=False)
                    except:
                        note = 'Bad Request'
                        message = anyToUnicode(e.response.text)

                self.log(u'Отправка направления actionId={0} eventId={1} ответ'.format(actionId, referral.eventId), message, level=1)

                if resBundle:
                    for entry in resBundle.entry:
                        if entry.resource.resource_type == 'Task':
                            externalId = entry.fullUrl.replace('Task/', '')

                action = CAction(record=self.db.getRecord('Action', '*', actionId))
                if resBundle or externalId:
                    action.getRecord().setValue('status', toVariant(CActionStatus.wait))
                action.getRecord().setValue('note', toVariant(note))
                action.save(idx=-1)

                tableActionExport = self.db.table(u'Action_Export')
                actionExportRecord = tableActionExport.newRecord()
                actionExportRecord.setValue('id', toVariant(exportId))
                actionExportRecord.setValue('master_id', toVariant(actionId))
                actionExportRecord.setValue('system_id', toVariant(self.externalSystemId))
                actionExportRecord.setValue('success', toVariant(0))
                actionExportRecord.setValue('externalId', toVariant(externalId))
                actionExportRecord.setValue('dateTime', toVariant(QDateTime().currentDateTime()))
                actionExportRecord.setValue('note', toVariant(bundleHash))
                self.db.insertOrUpdate(tableActionExport, actionExportRecord)
        except Exception as e:
            self.log('error', anyToUnicode(e), 2)
            note = anyToUnicode(e)

        finally:
            # снимаем блокировку
            if lockId:
                self.db.query('CALL ReleaseAppLock(%d)' % lockId)

        return note

    def sendLocalResult(self, result):
        self.log(u'Запуск функции', u'sendLocalResult', 3)
        note = ""

        actionId = result.actionId
        exportId = result.exportId
        externalId = result.externalId
        exportHash = result.exportHash

        lockId = None
        try:
            self.db.query('CALL getAppLock_(%s, %d, %d, %s, %s, @res)' % (quote('Event'), result.eventId, 0, 1, quote('ODIIExchange')))
            query = self.db.query('SELECT @res')

            if query.next():
                record = query.record()
                s = forceString(record.value(0)).split()
                if len(s) > 1:
                    isSuccess = int(s[0])
                    if isSuccess:
                        lockId = int(s[1])
                    else:
                        self.log(u'Отправка результата actionId={0} eventId={1}'.format(actionId, result.eventId),
                                 u'Событие %i заблокировано' % result.eventId, level=1, localLog=True)
            if lockId:
                bundle = self.createResultBundle(actionId)
                if bundle is None:
                    # снимаем блокировку
                    if lockId:
                        self.db.query('CALL ReleaseAppLock(%d)' % lockId)
                    return None
                bundleJson = bundle.as_json()
                bundleHash = md5(str(bundleJson)).hexdigest()
                if bundleHash == exportHash:
                    self.log(u'Результат не отправлен, ошибки не исправлены. actionId={0} eventId={1} запрос'.format(actionId, result.eventId), bundleJson, level=1, localLog=True)
                    # снимаем блокировку
                    if lockId:
                        self.db.query('CALL ReleaseAppLock(%d)' % lockId)
                    return None
                self.log(u'Отправка результата actionId={0} eventId={1} запрос'.format(actionId, result.eventId), bundleJson, level=1, localLog=True)
                resBundle = None
                success = 0
                try:
                    note = message = ''
                    res = self.fhirServer.post_json('',  bundle.as_json())
                    message = res.content.decode('utf-8')
                    note = u'Результат успешно выгружен в ОДИИ {0}'.format(fmtDate(self.db.getCurrentDatetime()))
                    resBundle = Bundle(jsondict=json.loads(res.content))
                    success = 1
                except FHIRBadRequestException as e:
                    try:
                        resBundle = None
                        response = e.response.json()
                        note = response['issue'][0]['diagnostics']
                        message = json.dumps(response, sort_keys=True, indent=4, ensure_ascii=False)
                    except:
                        note = 'Bad Request'
                        message = anyToUnicode(e.response.text)
                except FHIRUnauthorizedException:
                    resBundle = None
                    message = note = 'Unauthorized'
                except FHIRPermissionDeniedException:
                    resBundle = None
                    message = note = 'Permission Denied'
                except FHIRUnprocessableEntityException as e:
                    try:
                        resBundle = None
                        response = e.response.json()
                        note = u'Ошибка валидации.'
                        for issue in response['issue']:
                            note += u' ' + issue['diagnostics']
                            if u'Попытка повторного добавления Task' in issue['diagnostics']:
                                externalId = issue['diagnostics'][issue['diagnostics'].find(u'Task/') + 5:]
                                note = u'Результат успешно выгружен в ОДИИ {0}'.format(fmtDate(self.db.getCurrentDatetime()))
                                break
                            if issue['diagnostics'] == u'Параметр обязательный и не должен быть пустым':
                                note += u': ' + ', '.join(issue['location']) + u';'
                            else:
                                note += u'.'
                        message = json.dumps(response, sort_keys=True, indent=4, ensure_ascii=False)
                    except:
                        note = 'Bad Request'
                        message = anyToUnicode(e.response.text)

                self.log(u'Отправка результат actionId={0} eventId={1} ответ'.format(actionId, result.eventId), message, level=1, localLog=True)

                if resBundle:
                    for entry in resBundle.entry:
                        if entry.resource.resource_type == 'Task':
                            externalId = entry.fullUrl.replace('Task/', '')

                action = CAction(record=self.db.getRecord('Action', '*', actionId))

                action.getRecord().setValue('note', toVariant(note))
                action.save(idx=-1)

                tableActionExport = self.db.table(u'Action_Export')
                actionExportRecord = tableActionExport.newRecord()
                actionExportRecord.setValue('id', toVariant(exportId))
                actionExportRecord.setValue('master_id', toVariant(actionId))
                actionExportRecord.setValue('system_id', toVariant(self.externalSystemId))
                actionExportRecord.setValue('success', toVariant(success))
                actionExportRecord.setValue('externalId', toVariant(externalId))
                actionExportRecord.setValue('dateTime', toVariant(QDateTime().currentDateTime()))
                actionExportRecord.setValue('note', toVariant(bundleHash))
                self.db.insertOrUpdate(tableActionExport, actionExportRecord)
        except Exception as e:
            self.log('error actionId={0}'.format(actionId), anyToUnicode(e), 2, localLog=True)
            note = anyToUnicode(e)
        finally:
            # снимаем блокировку
            if lockId:
                self.db.query('CALL ReleaseAppLock(%d)' % lockId)

        return note

    def searchResult(self, referral):
        actionId = referral.actionId
        taskId = referral.externalId
        exportId = referral.exportId

        path = '/imaging/exlab/api/fhir/Task/_search'
        params = Parameters()
        params.parameter = []

        param = ParametersParameter()
        param.name = 'intent'
        param.valueString = 'reflex-order'
        params.parameter.append(param)

        param = ParametersParameter()
        param.name = 'based-on'
        param.valueString = 'Task/' + taskId
        params.parameter.append(param)

        res = self.fhirServer.post_json(path, params.as_json())
        self.log(u'Получение результата actionId={0} eventId={1} запрос'.format(actionId, referral.eventId), params.as_json(), level=1)
        bundle = Bundle(jsondict=json.loads(res.content))
        self.log(u'Получение результата actionId={0} eventId={1} ответ'.format(actionId, referral.eventId), res.content.decode('utf-8'), level=1)
        if bundle.entry:
            entry = bundle.entry[0]
            diagnosticReference = entry.resource.focus.reference
            diagnostic = self.getResource(DiagnosticReport, diagnosticReference)
            if diagnostic and diagnostic.status in ['final', 'appended']:
                lockId = None
                try:
                    self.db.query('CALL getAppLock_(%s, %d, %d, %s, %s, @res)' %
                                  (quote('Event'), referral.eventId, 0, 1, quote('ODIIExchange')))
                    query = self.db.query('SELECT @res')

                    if query.next():
                        record = query.record()
                        s = forceString(record.value(0)).split()
                        if len(s) > 1:
                            isSuccess = int(s[0])
                            if isSuccess:
                                lockId = int(s[1])
                            else:
                                self.log(u'Загрузка результата {0}'.format(taskId),
                                         u'Событие %i заблокировано' % referral.eventId, level=1)
                    if lockId:
                        action = CAction(record=self.db.getRecord('Action', '*', actionId))
                        issueDate = unFmtDate(diagnostic.issued.isostring)
                        action.getRecord().setValue('endDate', toVariant(issueDate))
                        action.getRecord().setValue('status', toVariant(CActionStatus.finished))
                        note = u'Заказ успешно загружен из ОДИИ {0}'.format(fmtDate(self.db.getCurrentDatetime()))
                        action.getRecord().setValue('note', toVariant(note))
                        performerRole = self.getResource(PractitionerRole, diagnostic.performer[0].reference)
                        performer = self.getResource(Practitioner, performerRole.practitioner.reference)
                        snils = ''
                        context = CInfoContext()
                        orgStructureId = action.getProperty(u'Отделение исследования').getInfo(context).id 
                        orgId = action.getProperty(u'Внешнаяя лаборатория').getInfo(context).id
                        for ident in performer.identifier:
                            if ident.system == self.snilsUrn:
                                snils = ident.value
                        if orgId:
                            personId = self.getVerifierIdByOrg(orgId, snils)
                        else:
                            personId = self.getVerifierId(orgStructureId, snils)
                        if personId:
                            action.getRecord().setValue('person_id', toVariant(personId))
                        if diagnostic.result:
                            for result in diagnostic.result:
                                observation = self.getResource(Observation, result.reference)
                                if observation:
                                    if observation.code.coding[0].code == '1':
                                        action[u'Описание'] = observation.valueString
                                    elif observation.code.coding[0].code == '2':
                                        action[u'Заключение'] = observation.valueString
                        if diagnostic.imagingStudy:
                            for imag in diagnostic.imagingStudy:
                                imagingStudy = self.getResource(ImagingStudy, imag.reference)
                                if imagingStudy.description:
                                    action[u'Снимки'] = imagingStudy.description
                                # endpoint = self.getResource(Endpoint, imagingStudy.endpoint[0].reference)
                        if diagnostic.presentedForm:
                            pdfFile = cdaFile = None
                            for binary in diagnostic.presentedForm:
                                if binary.contentType == 'application/pdf':
                                    pdfFile = self.loadBinary(action, personId, binary.url, binary.contentType)
                                elif binary.contentType == 'application/xml':
                                    cdaFile = self.loadBinary(action, personId, binary.url, binary.contentType)
                                elif binary.contentType in ['application/x-pkcs7-organization', 'application/x-pkcs7-practitioner']:
                                    self.loadSign(pdfFile, personId, binary.url, binary.contentType)
                                elif binary.contentType in ['application/x-pkcs7-organization-xml', 'application/x-pkcs7-practitioner-xml']:
                                    self.loadSign(cdaFile, personId, binary.url, binary.contentType)
                        # Проставление статуса "Закончено" в номерке
                        if self.updateJobTicketStatus:
                            for prop in action._propertiesById.itervalues():
                                if prop.type().isJobTicketValueType() and prop.getValue():
                                    recordJT = self.db.getRecord('Job_Ticket', '*', prop.getValue())
                                    if recordJT:
                                        recordJT.setValue('endDateTime', toVariant(issueDate))
                                        recordJT.setValue('status', toVariant(2))  # закончено
                                        self.db.updateRecord('Job_Ticket', recordJT)

                        action.save(idx=-1)
                        tableActionExport = self.db.table(u'Action_Export')
                        actionExportRecord = tableActionExport.newRecord()
                        actionExportRecord.setValue('id', toVariant(exportId))
                        actionExportRecord.setValue('master_id', toVariant(actionId))
                        actionExportRecord.setValue('system_id', toVariant(self.externalSystemId))
                        actionExportRecord.setValue('success', toVariant(1))
                        actionExportRecord.setValue('externalId', toVariant(taskId))
                        actionExportRecord.setValue('dateTime', toVariant(QDateTime().currentDateTime()))
                        self.db.insertOrUpdate(tableActionExport, actionExportRecord)
                except Exception as e:
                    self.log('error', anyToUnicode(e), 2)
                finally:
                    # снимаем блокировку
                    if lockId:
                        self.db.query('CALL ReleaseAppLock(%d)' % lockId)
        return True

    def searchResultBatch(self, taskList):
        self.log(u'Запуск функции', u'searchResultBatch', 3)
        if not taskList:
            self.log(u'Запрос результатов', u'список номеров направлений пуст!', level=1)
            return None
        path = '/imaging/exlab/api/fhir/Task/_search'
        params = Parameters()
        params.parameter = []

        param = ParametersParameter()
        param.name = 'intent'
        param.valueString = 'reflex-order'
        params.parameter.append(param)

        param = ParametersParameter()
        param.name = 'status'
        param.valueString = 'completed'
        params.parameter.append(param)

        param = ParametersParameter()
        param.name = '_count'
        param.valueString = '500'
        params.parameter.append(param)

        param = ParametersParameter()
        param.name = 'based-on'
        param.valueString = taskList
        params.parameter.append(param)

        res = self.fhirServer.post_json(path, params.as_json())
        self.log(u'Получение результата запрос', params.as_json(), level=1)
        bundle = Bundle(jsondict=json.loads(res.content))
        self.log(u'Получение результата ответ', res.content.decode('utf-8'), level=1)
        return bundle

    def saveResult(self, entry, refferals):
        self.log(u'Запуск функции', u'saveResult', 3)
        for referral in refferals.values():
            if referral.externalId == entry.resource.basedOn[0].reference:
                break
        else:
            referral = None
        if referral:
            diagnosticReference = entry.resource.focus.reference
            diagnostic = self.getResource(DiagnosticReport, diagnosticReference)
            if diagnostic and diagnostic.status in ['final', 'appended']:
                lockId = None
                try:
                    self.db.query('CALL getAppLock_(%s, %d, %d, %s, %s, @res)' % (
                    quote('Event'), referral.eventId, 0, 1, quote('ODIIExchange')))
                    query = self.db.query('SELECT @res')

                    if query.next():
                        record = query.record()
                        s = forceString(record.value(0)).split()
                        if len(s) > 1:
                            isSuccess = int(s[0])
                            if isSuccess:
                                lockId = int(s[1])
                            else:
                                self.log(u'Загрузка результата {0}'.format(referral.externalId.replace('Task/', '')),
                                         u'Событие %i заблокировано' % referral.eventId, level=1)
                    if lockId:
                        action = CAction(record=self.db.getRecord('Action', '*', referral.actionId))
                        issueDate = unFmtDate(diagnostic.issued.isostring)
                        action.getRecord().setValue('endDate', toVariant(issueDate))
                        action.getRecord().setValue('status', toVariant(CActionStatus.finished))
                        note = u'Заказ успешно загружен из ОДИИ {0}'.format(fmtDate(self.db.getCurrentDatetime()))
                        action.getRecord().setValue('note', toVariant(note))
                        performerRole = self.getResource(PractitionerRole, diagnostic.performer[0].reference)
                        performer = self.getResource(Practitioner, performerRole.practitioner.reference)
                        snils = ''
                        context = CInfoContext()
                        orgStructureId = None
                        orgId = None
                        prop = action.getPropertyByShortName(u'orgstructName')
                        if not prop:
                            prop = action.getPropertyByShortName(u'Office')
                        if prop:
                            orgStructureId = prop.getInfo(context).id
                        if not prop:
                            prop = action.getPropertyByShortName(u'externalOtd')
                            if prop:
                                orgId = prop.getInfo(context).id
                        for ident in performer.identifier:
                            if ident.system == self.snilsUrn:
                                snils = ident.value
                        if orgId:
                            personId = self.getVerifierIdByOrg(orgId, snils)
                        else:
                            personId = self.getVerifierId(orgStructureId, snils)
                        if personId:
                            action.getRecord().setValue('person_id', toVariant(personId))
                        if performer and performer.name:
                            per = performer.name
                            executerOtd = ''
                            if per[0] and per[0].family:
                                executerOtd = per[0].family
                                if per[0].given and per[0].given[0]:
                                    executerOtd = executerOtd + u' ' + per[0].given[0]
                                    if per[0].given and per[0].given[1]:
                                        executerOtd = executerOtd + u' ' + per[0].given[1]
                            if executerOtd != '':
                                prop = action.getPropertyByShortName(u'executerOtd')
                                if prop:
                                    prop.setValue(executerOtd)
                        if diagnostic.result:
                            for result in diagnostic.result:
                                observation = self.getResource(Observation, result.reference)
                                if observation:
                                    if observation.code.coding[0].code == '1':
                                        prop = action.getPropertyByShortName(u'description')
                                        if not prop:
                                            prop = action.getPropertyByShortName(u'Description')
                                        if prop:
                                            prop.setValue(observation.valueString)
                                    elif observation.code.coding[0].code == '2':
                                        prop = action.getPropertyByShortName(u'conclusion')
                                        if not prop:
                                            prop = action.getPropertyByShortName(u'Conclusion')
                                        if prop:
                                            prop.setValue(observation.valueString)
                                    elif observation.code.coding[0].code == '3':
                                        prop = action.getPropertyByShortName(u'recommendations')
                                        if prop:
                                            prop.setValue(observation.valueString)
                                    elif observation.code.coding[0].code == '5':
                                        prop = action.getPropertyByShortName(u'eed')
                                        if not prop:
                                            prop = action.getPropertyByShortName(u'Dose')
                                        if prop:
                                            prop.setValue(observation.valueQuantity.value)

                        if diagnostic.imagingStudy:
                            for imag in diagnostic.imagingStudy:
                                imagingStudy = self.getResource(ImagingStudy, imag.reference)
                                if imagingStudy.description:
                                    prop = action.getPropertyByShortName(u'snapshots')
                                    if not prop:
                                        prop = action.getPropertyByShortName(u'RISDirectLink')
                                    if prop:
                                        prop.setValue(imagingStudy.description)
                        if diagnostic.presentedForm:
                            pdfFile = cdaFile = None
                            for binary in diagnostic.presentedForm:
                                if binary.contentType == 'application/pdf':
                                    pdfFile = self.loadBinary(action, personId, binary.url, binary.contentType)
                                elif binary.contentType == 'application/xml':
                                    cdaFile = self.loadBinary(action, personId, binary.url, binary.contentType)
                                elif binary.contentType in ['application/x-pkcs7-organization',
                                                            'application/x-pkcs7-practitioner']:
                                    self.loadSign(pdfFile, personId, binary.url, binary.contentType)
                                elif binary.contentType in ['application/x-pkcs7-organization-xml',
                                                            'application/x-pkcs7-practitioner-xml']:
                                    self.loadSign(cdaFile, personId, binary.url, binary.contentType)
                        # Проставление статуса "Закончено" в номерке
                        if self.updateJobTicketStatus:
                            for prop in action._propertiesById.itervalues():
                                if prop.type().isJobTicketValueType() and prop.getValue():
                                    recordJT = self.db.getRecord('Job_Ticket', '*', prop.getValue())
                                    if recordJT:
                                        recordJT.setValue('endDateTime', toVariant(issueDate))
                                        recordJT.setValue('status', toVariant(2))  # закончено
                                        self.db.updateRecord('Job_Ticket', recordJT)

                        action.save(idx=-1)
                        tableActionExport = self.db.table(u'Action_Export')
                        actionExportRecord = tableActionExport.newRecord()
                        actionExportRecord.setValue('id', toVariant(referral.exportId))
                        actionExportRecord.setValue('master_id', toVariant(referral.actionId))
                        actionExportRecord.setValue('system_id', toVariant(self.externalSystemId))
                        actionExportRecord.setValue('success', toVariant(1))
                        actionExportRecord.setValue('externalId', toVariant(referral.externalId.replace('Task/', '')))
                        actionExportRecord.setValue('dateTime', toVariant(QDateTime().currentDateTime()))
                        self.db.insertOrUpdate(tableActionExport, actionExportRecord)
                except Exception as e:
                    self.log('error', anyToUnicode(e), 2)
                finally:
                    # снимаем блокировку
                    if lockId:
                        self.db.query('CALL ReleaseAppLock(%d)' % lockId)


    #####################################################################################
    # select Actions
    def getVerifierId(self, orgStructureId, snils):
        personId = self.mapVerifiers.get((orgStructureId, snils), None)
        if not personId and orgStructureId and snils:
            orgStructureList = getOrgStructureDescendants(orgStructureId)
            tablePerson = self.db.table('Person')
            cond = [tablePerson['orgStructure_id'].inlist(orgStructureList),
                    tablePerson['SNILS'].eq(snils),
                    tablePerson['deleted'].eq(0),
                    tablePerson['retireDate'].isNull()
                    ]
            personIdList = self.db.getIdList(tablePerson, where=self.db.joinAnd(cond), limit=1)
            if personIdList:
                personId = personIdList[0]
                self.mapVerifiers[(orgStructureId, snils)] = personId
        return personId
    
    def getVerifierIdByOrg(self, orgId, snils):
        personId = self.externalMapVerifiers.get((orgId, snils), None)
        if not personId and orgId and snils:
            orgStructureList = getOrgStructures(orgId)
            tablePerson = self.db.table('Person')
            cond = [tablePerson['orgStructure_id'].inlist(orgStructureList),
                    tablePerson['SNILS'].eq(snils),
                    tablePerson['deleted'].eq(0),
                    tablePerson['retireDate'].isNull()
                    ]
            personIdList = self.db.getIdList(tablePerson, where=self.db.joinAnd(cond), limit=1)
            if personIdList:
                personId = personIdList[0]
                self.externalMapVerifiers[(orgId, snils)] = personId
        return personId

    def selectReferrals(self, actionId=None):
        self.log(u'Запуск функции', u'selectReferrals', 3)
        referrals = {}
        minDate = datetime.datetime.now() - datetime.timedelta(days=self.days)

        tableAction = self.db.table('Action')
        tableActionType = self.db.table('ActionType')
        tableAPT = self.db.table('ActionPropertyType')
        tableActionExport = self.db.table('Action_Export')

        table = tableAction.leftJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
        table = table.leftJoin(tableAPT, [tableActionType['id'].eq(tableAPT['actionType_id']),
                                          tableAPT['deleted'].eq(0),
                                          tableAPT['typeName'].eq(u'Инструментальные диагностические исследования')])
        table = table.leftJoin(tableActionExport, [tableActionExport['master_id'].eq(tableAction['id']),
                                                   tableActionExport['system_id'].eq(self.externalSystemId)])
        cond = [tableAction['deleted'].eq(0),
                # tableAction['note'].notlike(u"Ошибка валидации. В БД уже есть бандл с таким идентификатором МИС%"),
                tableActionType['serviceType'].eq(5),
                tableActionType['deleted'].eq(0),
                tableAPT['id'].isNotNull(),
                tableActionType['id'].notInlist(self.actionTypeIdLocalResultList),
                self.db.joinOr([tableActionExport['id'].isNull(), tableActionExport['externalId'].eq('')])
                ]

        # Если включена прямая интеграция, то в ОДИИ будем отправлять только внешние направления
        if self.directIntegration:
            cond.append(tableActionType['flatCode'].eq('ODII_outexportdirection'))

        fields = [tableAction['id'].alias('actionId'),
                  tableAction['event_id'].alias('eventId'),
                  tableActionExport['id'].alias('exportId'),
                  tableActionExport['note'].alias('exportHash')]

        if actionId:
            cond.append(tableAction['id'].eq(actionId))
        else:
            cond.append('Action.begDate < CURDATE() + interval 1 DAY')
            cond.append(tableAction['begDate'].ge(minDate))

            cond.append(tableAction['status'].inlist([CActionStatus.started, CActionStatus.wait, CActionStatus.appointed]))

        records = self.db.getRecordList(table, cols=fields, where=self.db.joinAnd(cond))
        for record in records:
            actionId = forceRef(record.value('actionId'))
            eventId = forceRef(record.value('eventId'))
            exportId = forceRef(record.value('exportId'))
            exportHash = forceString(record.value('exportHash'))
            externalId = ''
            referrals[actionId] = _referral(actionId, eventId, exportId, externalId, exportHash)
        return referrals

    def selectResults(self, actionId=None):
        self.log(u'Запуск функции', u'selectResults', 3)
        results = {}
        minDate = datetime.datetime.now() - datetime.timedelta(days=self.days+7)

        tableAction = self.db.table('Action')
        tableActionType = self.db.table('ActionType')
        tableAPT = self.db.table('ActionPropertyType')
        tableActionExport = self.db.table('Action_Export')
        tableAction_FileAttach = self.db.table('Action_FileAttach')

        table = tableAction.leftJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
        table = table.leftJoin(tableAPT, [tableActionType['id'].eq(tableAPT['actionType_id']),
                                          tableAPT['deleted'].eq(0),
                                          tableAPT['typeName'].eq(u'Инструментальные диагностические исследования')])
        table = table.leftJoin(tableActionExport, [tableActionExport['master_id'].eq(tableAction['id']),
                                                   tableActionExport['system_id'].eq(self.externalSystemId)])
        cond = [tableAction['deleted'].eq(0),
                # tableAction['note'].notlike(u"Ошибка валидации. В БД уже есть бандл с таким идентификатором МИС%"),
                tableActionType['serviceType'].eq(5),
                tableActionType['deleted'].eq(0),
                tableAPT['id'].isNotNull(),
                tableActionType['id'].inlist(self.actionTypeIdLocalResultList),
                self.db.joinOr([tableActionExport['id'].isNull(), tableActionExport['externalId'].eq('')])
                ]

        fields = [tableAction['id'].alias('actionId'),
                  tableAction['event_id'].alias('eventId'),
                  tableActionExport['id'].alias('exportId'),
                  tableActionExport['note'].alias('exportHash')]
        cond.append(self.db.existsStmt(tableAction_FileAttach,
                                       [tableAction_FileAttach['master_id'].eq(tableAction['id']),
                                        tableAction_FileAttach['deleted'].eq(0),
                                        tableAction_FileAttach['path'].like('%.xml'),
                                        tableAction_FileAttach['respSigner_id'].isNotNull(),
                                        self.db.joinOr([tableAction_FileAttach['orgSigner_id'].isNotNull(),
                                                        self.db.joinAnd([tableAction_FileAttach['orgSigner_id'].isNull(),
                                                                         tableAction_FileAttach['respSignatureBytes'].contain(self.orgOGRN)])])]))
        if actionId:
            cond.append(tableAction['id'].eq(actionId))
        else:
            cond.append('Action.begDate < CURDATE() + interval 1 DAY')
            cond.append(tableAction['begDate'].ge(minDate))

        cond.append(tableAction['status'].eq(CActionStatus.finished))

        if self.transferConsent:
            # Если включена настройка, то передаем протоколы исследований только по людям у которых есть согласие egisz
            tableEvent = self.db.table('Event')
            tableConsent = self.db.table('ClientConsent')
            tableConsentType = self.db.table('rbClientConsentType')
            table2 = tableEvent.leftJoin(tableConsent, tableConsent['client_id'].eq(tableEvent['client_id']))
            table2 = table2.leftJoin(tableConsentType, tableConsentType['id'].eq(tableConsent['clientConsentType_id']))
            cond2 = [tableEvent['id'].eq(tableAction['event_id']),
                     tableConsent['deleted'].eq(0),
                     tableConsent['value'].eq(1),
                     tableConsentType['code'].eq('egisz'),
                     tableAction['endDate'].ge(tableConsent['date']),
                     self.db.joinOr([tableConsent['endDate'].isNull(),
                                     tableAction['endDate'].lt(tableConsent['endDate'])])
                     ]
            cond.append(self.db.existsStmt(table2, cond2))

        records = self.db.getRecordList(table, cols=fields, where=self.db.joinAnd(cond))
        for record in records:
            actionId = forceRef(record.value('actionId'))
            eventId = forceRef(record.value('eventId'))
            exportId = forceRef(record.value('exportId'))
            exportHash = forceString(record.value('exportHash'))
            externalId = ''
            results[actionId] = _referral(actionId, eventId, exportId, externalId, exportHash)
        return results

    def selectReferralsForResult(self, actionId=None):
        self.log(u'Запуск функции', u'selectReferralsForResult', 3)
        minDate = datetime.datetime.now() - datetime.timedelta(90)
        referrals = {}
        taskList = set()
        tableAction = self.db.table('Action')
        tableActionType = self.db.table('ActionType')
        tableAPT = self.db.table('ActionPropertyType')
        tableActionExport = self.db.table('Action_Export')

        table = tableAction.leftJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
        table = table.leftJoin(tableAPT, [tableActionType['id'].eq(tableAPT['actionType_id']),
                                          tableAPT['deleted'].eq(0),
                                          tableAPT['typeName'].eq(u'Инструментальные диагностические исследования')])
        table = table.leftJoin(tableActionExport, [tableActionExport['master_id'].eq(tableAction['id']),
                                                   tableActionExport['system_id'].eq(self.externalSystemId)])
        cond = [tableAction['deleted'].eq(0),
                tableActionType['serviceType'].eq(5),
                tableActionType['deleted'].eq(0),
                tableAPT['id'].isNotNull(),
                tableActionType['id'].notInlist(self.actionTypeIdLocalResultList),
                tableActionExport['externalId'].ne('')
                ]

        if actionId:
            cond.append(tableAction['id'].eq(actionId))
        else:
            cond.append(tableActionExport['success'].eq(0))
            cond.append(tableAction['status'].inlist([CActionStatus.started, CActionStatus.wait, CActionStatus.appointed]))
            cond.append(tableAction['begDate'].ge(minDate))

        fields = [tableAction['id'].alias('actionId'),
                  tableAction['event_id'].alias('eventId'),
                  tableActionExport['id'].alias('exportId'),
                  tableActionExport['externalId'].name()]

        records = self.db.getRecordList(table, cols=fields, where=self.db.joinAnd(cond))
        for record in records:
            actionId = forceRef(record.value('actionId'))
            eventId = forceRef(record.value('eventId'))
            exportId = forceRef(record.value('exportId'))
            externalId = 'Task/' + forceString(record.value('externalId'))
            referrals[actionId] = _referral(actionId, eventId, exportId, externalId, None)
            taskList.add(externalId)
        tasks = ','.join(taskList)
        return referrals, tasks

    def createTask(self, actionId, refferalDateTime, patientReference, organizationRef, serviceRequestRef, serviceProviderRef, isPrimary):
        u"""
        Ресурс Task предназначен для передачи общей информации о заявке.
        """
        task = Task()
        task.identifier = [self.createMisIdentifier(actionId, use=isPrimary)]  # идентификатор в МИС
        task.intent = 'original-order'
        task.focus = serviceRequestRef
        task.for_fhir = patientReference
        task.authoredOn = dateTimeToFHIRDate(refferalDateTime)
        task.requester = organizationRef
        task.owner = serviceProviderRef
        return task

    def createResultTask(self, actionId, resultDateTime, patientReference, organizationRef, diagnosticReportRef):
        u"""
        Ресурс Task предназначен для передачи общей информации о результате исследований.
        """
        task = Task()
        task.identifier = [self.createMisIdentifier(actionId)]  # идентификатор в МИС
        task.intent = 'reflex-order'
        task.status = 'completed'
        task.focus = diagnosticReportRef
        task.authoredOn = dateTimeToFHIRDate(resultDateTime)
        task.for_fhir = patientReference
        task.requester = organizationRef
        task.owner = organizationRef
        return task

    def createDiagnosticReport(self, resultDateTime, categoryCode, serviceCode, patientReference,
                               practitionerRoleReference, encounterReference, observationReferenceList, binaryReferenceList):
        u"""
        Ресурс DiagnosticReport предназначен для передачи информации о результате исследования
        в разрезе видов исследований и содержит ссылки на результаты исследования.
        """
        diagnosticReport = DiagnosticReport()
        diagnosticReport.meta = Meta()
        diagnosticReport.meta.security = [self.createCoding('urn:oud:1.2.643.5.1.13.13.11.1116', 'N', '1')]
        diagnosticReport.status = 'final'
        diagnosticReport.category = [self.createCodeableConcept(self.categoryUrn, categoryCode)]
        diagnosticReport.code = self.createCodeableConcept(self.serviceUrn, serviceCode)
        diagnosticReport.subject = patientReference
        diagnosticReport.encounter = encounterReference
        diagnosticReport.effectiveDateTime = dateTimeToFHIRDate(resultDateTime)
        diagnosticReport.issued = dateTimeToFHIRDate(resultDateTime)
        diagnosticReport.performer = [practitionerRoleReference]
        diagnosticReport.result = observationReferenceList
        diagnosticReport.presentedForm = []
        for binaryReference, contentType in binaryReferenceList:
            attachment = Attachment()
            attachment.url = binaryReference.reference
            attachment.contentType = contentType
            diagnosticReport.presentedForm.append(attachment)
        return diagnosticReport

    def createCondition(self, mkb, patientReference):
        u"""
        Ресурс Condition предназначен для передачи информации о диагнозах пациента. В этом ресурсе указывается диагноз
        (основной диагноз, сопутствующее заболевание, осложнение). Содержание ресурса Condition определяется по значению
        параметра category. Для диагноза category == diagnosis.
        """
        condition = Condition()
        condition.verificationStatus = self.createCodeableConcept(self.urnDiagnosisStatus, 'confirmed', '')
        condition.category = [self.createCodeableConcept(self.urnCategory, 'diagnosis', '')]
        condition.code = self.createCodeableConcept(self.urnMKB, mkb, '')
        condition.subject = patientReference
        return condition

    def createObservation(self, code, value):
        u"""
        Ресурс Observation предназначен для передачи информации о состоянии пациента.
        В этом ресурсе может указываться рост (в сантиметрах), вес (в килограммах) пациента.
        """
        observation = Observation()
        observation.code = self.createCodeableConcept(self.urnObservation, code)
        observation.status = 'final'
        observation.valueQuantity = Quantity()
        observation.valueQuantity.value = value
        return observation

    def createResultObservation(self, code, value, resultDateTime, practitionerRoleReference):
        u"""
        Ресурс Observation предназначен для передачи результата исследования
        и для передачи дополнительной информации по результату для формирования СМС ВИМИС.
        """
        observation = Observation()
        observation.code = self.createCodeableConcept(self.urnResultObservation, code)
        observation.status = 'final'
        observation.issued = dateTimeToFHIRDate(resultDateTime)
        observation.performer = [practitionerRoleReference]
        observation.valueString = value
        return observation

    def createEncounter(self, eventId, eventTypeId, eventPurposeId, medicalAidTypeId, patientRef, conditionRef, orgRef):
        u"""
        Ресурс Encounter предназначен для передачи информации о случае обслуживания и ссылок на диагнозы пациента.
        """
        classCode = getIdentification('rbMedicalAidType', medicalAidTypeId, self.urnCaseClasses, False)
        typeCode = getIdentification('rbMedicalAidType', medicalAidTypeId, self.urnCaseTypes, False)

        reasonCode = getIdentification('EventType', eventTypeId, self.urnReasons, False)
        if reasonCode is None:
            reasonCode = getIdentification('rbEventTypePurpose', eventPurposeId, self.urnReasons, False)

        encounter = Encounter()
        encounter.identifier = [self.createMisIdentifier(eventId)]  # идентификатор в МИС
        encounter.status = 'in-progress'
        encounter.class_fhir = self.createCoding(self.urnCaseClasses, classCode)
        encounter.type = [self.createCodeableConcept(self.urnCaseTypes, typeCode)]
        encounter.subject = patientRef
        if reasonCode:
            encounter.reasonCode = [self.createCodeableConcept(self.urnReasons, reasonCode)]
        diag = EncounterDiagnosis()
        diag.condition = conditionRef
        encounter.diagnosis = [diag]
        encounter.serviceProvider = orgRef
        return encounter

    def createServiceRequest(self, serviceCode, bodySitCodes, financeCode, isUrgent, patientReference, encounterReference,
                             practitionerRoleReference, obsCondRefs, note):
        u"""
        Ресурс ServiceRequest предназначен для передачи информации о назначении (какие исследования назначены пациенту),
        ссылки на случай обслуживания, информации об источнике финансирования и ссылок на состояние пациента.
        """
        service = ServiceRequest()
        service.intent = 'filler-order'
        service.priority = 'urgent' if isUrgent else 'routine'
        service.code = self.createCodeableConcept(self.serviceUrn, serviceCode)
        service.orderDetail = [self.createCodeableConcept(self.urnFinances, financeCode)]
        service.subject = patientReference
        service.encounter = encounterReference
        service.requester = practitionerRoleReference
        service.supportingInfo = obsCondRefs
        service.bodySite = []
        for bodySiteCode in bodySitCodes:
            service.bodySite.append(self.createCodeableConcept(self.urnResearchArea, bodySiteCode))
        if note:
            service.note = [Annotation()]
            service.note[0].text = note
        return service

    def createReference(self, resource):
        if resource.id is None:
            resp = resource.create(self.smart.server)
            resource.update_with_json(resp)
        reference = FHIRReference()
        reference.reference = '%s/%s' % (resource.resource_type, resource.id)
        return reference

    def documentAsIdentifier(self, documentRecord):
        serial = forceString(documentRecord.value('serial'))
        number = forceString(documentRecord.value('number'))
        documentTypeId = forceString(documentRecord.value('documentType_id'))
        date = forceDate(documentRecord.value('date'))
        code = None
        try:
            code, version = getIdentificationEx('rbDocumentType', documentTypeId, self.documentTypeUrn, False)
        except:
            QtGui.qApp.logCurrentException()
        if serial and number and code:
            # provider, version = getIdentificationEx('rbDocumentType', documentTypeId, self.documentProviderUrn, False)
            # if provider is None:
            if code == '14':
                provider = u'УФМС'
            elif code == '3':
                provider = u'ЗАГС'
            else:
                provider = u'-'
            number = number.replace(' ', '').replace('-', '')
            serial = serial.replace(' ', '').replace('-', '')
            document = ('%s:%s' % (serial, number)) if serial else number
            identifier = createIdentifier('%s.%s' % (self.documentTypeUrn, code),
                                          document,
                                          createDispReference(provider))
            if date:
                identifier.period = Period()
                identifier.period.start = dateToFHIRDate(date)
            return identifier
        return None

    def policyAsIdentifier(self, clientId, policyRecord):
        insurerId = forceRef(policyRecord.value('insurer_id'))
        serial = forceString(policyRecord.value('serial'))
        number = forceString(policyRecord.value('number'))
        begDate = forceDate(policyRecord.value('begDate'))
        endDate = forceDate(policyRecord.value('endDate'))
        if insurerId is None:
            QtGui.qApp.log('ODII', u'У пациента Client.id=%s\n'
                           u'в полисе серия:«%s», номер: «%s»\n'
                           u'не указана страховая компания' % (clientId, serial, number))
            return None
        policyTypeComp = self._getPolicyTypeComp(forceRef(policyRecord.value('policyType_id')))
        if policyTypeComp:
            policyKindCode = self._getPolicyKindCode(forceRef(policyRecord.value('policyKind_id')))
            if not policyKindCode:
                policyKindCode = _guessPolicyKindCode(serial, number)
            if policyKindCode == '1':  # старый
                system = self.oldPolicyUrn
            elif policyKindCode == '2':  # временный
                system = self.tmpPolicyUrn
            elif policyKindCode in ['3', '4']:  # новый
                system = self.newPolicyUrn
            else:
                return None
        else:
            system = self.volPolicyUrn
        insurerCode = getIdentification('Organisation', insurerId, self.hicRegistryUrn, raiseIfNonFound=False)
        if not insurerCode:
            return None
        value = number if system in [self.newPolicyUrn, self.tmpPolicyUrn] else '%s:%s' % (serial, number)
        identifier = createIdentifier(system,
                                      value,
                                      createDispReference('%s.%s' % (self.hicRegistryOid, insurerCode)))
        if begDate or endDate:
            identifier.period = Period()
            if begDate:
                identifier.period.start = dateToFHIRDate(begDate)
            if endDate:
                identifier.period.end = dateToFHIRDate(endDate)
        return identifier

    def registerDocumentTables(self):
        self.log(u'Запуск функции', u'registerDocumentTables', 3)
        database.registerDocumentTable('Account')
        database.registerDocumentTable('Action')
        database.registerDocumentTable('Action_FileAttach')
        # database.registerDocumentTable('Action_FileAttach_Signature')
        database.registerDocumentTable('Action_ExecutionPlan')
        database.registerDocumentTable('Action_ActionProperty')
        database.registerDocumentTable('ActionExecutionPlan')
        database.registerDocumentTable('ActionProperty')
        database.registerDocumentTable('ActionPropertyTemplate')
        database.registerDocumentTable('ActionTemplate')
        database.registerDocumentTable('ActionType')
        database.registerDocumentTable('Address')
        database.registerDocumentTable('AddressHouse')
        database.registerDocumentTable('Bank')
        database.registerDocumentTable('BlankActions_Moving')
        database.registerDocumentTable('BlankActions_Party')
        database.registerDocumentTable('BlankTempInvalid_Moving')
        database.registerDocumentTable('BlankTempInvalid_Party')
        database.registerDocumentTable('CalendarException')
        database.registerDocumentTable('Client')
        database.registerDocumentTable('Client_FileAttach')
        database.registerDocumentTable('ClientAddress')
        database.registerDocumentTable('ClientAllergy')
        database.registerDocumentTable('ClientAttach')
        database.registerDocumentTable('ClientConsent')
        database.registerDocumentTable('ClientContact')
        database.registerDocumentTable('ClientDocument')
        database.registerDocumentTable('ClientIdentification')
        database.registerDocumentTable('ClientIntoleranceMedicament')
        database.registerDocumentTable('ClientPolicy')
        database.registerDocumentTable('Client_Quoting')
        database.registerDocumentTable('ClientRelation')
        database.registerDocumentTable('ClientResearch')
        database.registerDocumentTable('ClientActiveDispensary')
        database.registerDocumentTable('ClientDangerous')
        database.registerDocumentTable('ClientForcedTreatment')
        database.registerDocumentTable('ClientSuicide')
        database.registerDocumentTable('ClientContingentKind')
        database.registerDocumentTable('ClientSocStatus')
        database.registerDocumentTable('Client_StatusObservation')
        database.registerDocumentTable('ClientWork')
        database.registerDocumentTable('Client_StatusObservation')
        database.registerDocumentTable('Contract')
        database.registerDocumentTable('Diagnosis')
        database.registerDocumentTable('DiagnosisDispansPlaned')
        database.registerDocumentTable('Diagnostic')
        database.registerDocumentTable('EmergencyCall')
        database.registerDocumentTable('Event')
        database.registerDocumentTable('Event_Feed')
        database.registerDocumentTable('Event_FileAttach')
        database.registerDocumentTable('Event_JournalOfPerson')
        database.registerDocumentTable('Event_LocalContract')
        database.registerDocumentTable('Event_Payment')
        database.registerDocumentTable('EventType')
        database.registerDocumentTable('InformerMessage')
        database.registerDocumentTable('Job')
        database.registerDocumentTable('Licence')
        database.registerDocumentTable('Notification_Rule')
        database.registerDocumentTable('Organisation')
        database.registerDocumentTable('OrgStructure')
        database.registerDocumentTable('OrgStructure_HospitalBed')
        database.registerDocumentTable('OrgStructure_HospitalBed_Involution')
        database.registerDocumentTable('OrgStructure_PlanningHospitalBedProfile')
        database.registerDocumentTable('Person')
        database.registerDocumentTable('Person_Activity')
        database.registerDocumentTable('Person_Contact')
        database.registerDocumentTable('Person_Order')
        database.registerDocumentTable('Person_TimeTemplate')
        database.registerDocumentTable('Probe')
        database.registerDocumentTable('QuotaType')
        database.registerDocumentTable('Quoting')
        database.registerDocumentTable('Quoting_Region')
        database.registerDocumentTable('Schedule')
        database.registerDocumentTable('Schedule_Item')
        database.registerDocumentTable('StockMotion')
        database.registerDocumentTable('SuspendedAppointment')
        database.registerDocumentTable('TakenTissueJournal')
        database.registerDocumentTable('TempInvalid')
        database.registerDocumentTable('TempInvalidDocument')
        database.registerDocumentTable('Visit')
        database.registerDocumentTable('Event_CardLocation')
        database.registerDocumentTable('rbUserProfile') # это против правил :(
        database.registerDocumentTable('Client_DocumentTracking')
        database.registerDocumentTable('Client_DocumentTrackingItem')
        database.registerDocumentTable('rbService')
        database.registerDocumentTable('ActionTypeGroup')
        database.registerDocumentTable('ActionTypeGroup_Item')
        database.registerDocumentTable('Person_ActionProperty')
        database.registerDocumentTable('rbStockMotionItemReason')
        database.registerDocumentTable('rbTumor')
        database.registerDocumentTable('rbTumor_Identification')
        database.registerDocumentTable('rbNodus')
        database.registerDocumentTable('rbNodus_Identification')
        database.registerDocumentTable('rbMetastasis')
        database.registerDocumentTable('rbMetastasis_Identification')
        database.registerDocumentTable('rbTNMphase')
        database.registerDocumentTable('rbTNMphase_Identification')
        database.registerDocumentTable('ActionType_Expansion')
        database.registerDocumentTable('rbEquipmentType')
        database.registerDocumentTable('rbEquipmentClass')
        database.registerDocumentTable('Client_History')
        database.registerDocumentTable('rbNomenclature_Identification')
        database.registerDocumentTable('ProphylaxisPlanning')
        database.registerDocumentTable('Event_Voucher')
        database.registerDocumentTable('rbMKBExSubclass')
        database.registerDocumentTable('MKB_ExSubclass')
        database.registerDocumentTable('TreatmentType')
        database.registerDocumentTable('TreatmentScheme')
        database.registerDocumentTable('TreatmentScheme_Source')
        database.registerDocumentTable('TreatmentSchedule')
        database.registerDocumentTable('Client_Monitoring')
        database.registerDocumentTable('rbNomenclatureActiveSubstance')
        database.registerDocumentTable('rbNomenclatureActiveSubstance_Identification')
        database.registerDocumentTable('rbNomenclatureActiveSubstanceGroups')
        database.registerDocumentTable('rbNomenclatureActiveSubstance_Groups')
        database.registerDocumentTable('ClientVaccinationProbe')
        database.registerDocumentTable('rbReactionType_Identification')
        database.registerDocumentTable('rbReactionManifestation_Identification')
        database.registerDocumentTable('rbNomenclatureUsingType')
        database.registerDocumentTable('rbNomenclatureUsingType_Identification')
        database.registerDocumentTable('soc_prikCoefType')
        database.registerDocumentTable('soc_prikCoefItem')


# вспомогательный класс для разбора xml,
# полученого от сервиса терминологии и содержащего версии справочников

class ArrayOfDictionaryContractHandler(xml.sax.handler.ContentHandler):
    nsNetrika = 'http://schemas.datacontract.org/2004/07/Netrika.TS.Contracts.Contracts'
    nsXml = 'http://www.w3.org/2001/XMLSchema-instance'

    ArrayOfDictionaryContract = (nsNetrika, 'ArrayOfDictionaryContract')
    DictionaryContract = (nsNetrika, 'DictionaryContract')
    Comment = (nsNetrika, 'Comment')
    Id = (nsNetrika, 'Id')
    IsModify = (nsNetrika, 'IsModify')
    LastUpdate = (nsNetrika, 'LastUpdate')
    Name = (nsNetrika, 'Name')
    ParentName = (nsNetrika, 'ParentName')
    SystemName = (nsNetrika, 'SystemName')
    Uri = (nsNetrika, 'Uri')
    Version = (nsNetrika, 'Version')

    structure = {None: set([ArrayOfDictionaryContract]),
                 ArrayOfDictionaryContract: set([DictionaryContract]),
                 DictionaryContract: set([Comment, Id, IsModify, LastUpdate, Name, ParentName, SystemName, Uri, Version]),
                 }

    xmlNil = (nsXml, 'nil')

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
            version = version.replace('"', '')
            self.mapUriToVersion[uri] = version
            self.dictDef.clear()

    def characters(self, content):
        el = self.path[-1]
#        if el in ( self.Uri, self.Version ):
        self.dictDef[el] = content


def fmtDateShort(date):
    if isinstance(date, QDateTime):
        date = date.toPyDateTime()
    elif isinstance(date, QDate):
        date = date.toPyDate()
    return date.strftime("%Y-%m-%d")


def unFmtDate(date):
    return QDateTime().fromString(date[:-6], 'yyyy-MM-ddTHH:mm:ss')


def dateToFHIRDate(date):
    result = FHIRDate()
    if date:
        if isinstance(date, QDateTime):
            date = date.date()
        pd = date.toPyDate()
        result.date = pd
    return result


def fmtDate(date):
    if isinstance(date, QDateTime):
        date = date.toPyDateTime()
    elif isinstance(date, QDate):
        date = date.toPyDate()
    return date.strftime("%d.%m.%y %H:%M")


def dateTimeToFHIRDate(dateTime):
    result = FHIRDate()
    if dateTime:
#        pdt = dateTime.toPyDateTime().replace(microsecond=0)
        pdt = dateTime.toPyDateTime()
        if pdt.tzinfo is None:
            pdt = pdt.replace(tzinfo=isodate.LOCAL)
        result.date = pdt
    return result


def getOrgStructureIdentification(urn, orgStructureId):
    db = QtGui.qApp.db
    table = db.table('OrgStructure')
    # code = None
    while True:
        try:
            code, version = getIdentificationEx('OrgStructure', orgStructureId, urn, False)
            if code:
                return code
        except:
            pass
        parentId = forceRef(db.translate(table, 'id', orgStructureId, 'parent_id'))
        if parentId:
            orgStructureId = parentId
        else:
            orgId = forceRef(db.translate(table, 'id', orgStructureId, 'organisation_id'))
            return getIdentification('Organisation', orgId, urn)


def getEventDiagnosis(eventId):
    stmt = '''SELECT Diagnosis.MKB FROM Diagnostic
INNER JOIN rbDiagnosisType ON rbDiagnosisType.id = diagnosisType_id
LEFT JOIN Diagnosis ON Diagnosis.id = Diagnostic.diagnosis_id
WHERE Diagnostic.event_id = %d
AND Diagnostic.deleted = 0
ORDER BY CAST(rbDiagnosisType.code AS SIGNED)
LIMIT 1''' % eventId
    query = QtGui.qApp.db.query(stmt)
    if query.first():
        return forceString(query.record().value(0))
    else:
        return None


if __name__ == '__main__':
    app = CODIIExchange(sys.argv)
    app.main()
