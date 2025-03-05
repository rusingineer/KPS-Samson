#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime
import json
import logging
import os
import sys
import traceback
from logging.handlers import RotatingFileHandler

import requests
from collections import namedtuple

from PyQt4 import QtGui
from PyQt4.QtCore import QDir, QDate, QDateTime

from Events.Action import CAction
from Events.ActionInfo import CActionInfo
from Exchange.AriadnaModels.AdditionalForm import AdditionalForm
from Exchange.AriadnaModels.BirthCertificate import BirthCertificate
from Exchange.AriadnaModels.Cellular import Cellular
from Exchange.AriadnaModels.Certificate import Certificate
from Exchange.AriadnaModels.Company import Company
from Exchange.AriadnaModels.Email import Email
from Exchange.AriadnaModels.InternationalPassport import InternationalPassport
from Exchange.AriadnaModels.Observation import Observation
from Exchange.AriadnaModels.OrderInfo import OrderInfo
from Exchange.AriadnaModels.Passport import Passport
from Exchange.AriadnaModels.Phone import Phone
from Exchange.AriadnaModels.Physician import Physician
from Exchange.AriadnaModels.Province import Province
from Exchange.AriadnaModels.Snils import Snils
from Registry.Utils import CClientInfo

from library.PrintInfo import CInfoContext
from library.PrintTemplates import escape
from library.Utils import anyToUnicode, forceString, forceInt, forceRef, toVariant, quote, forceBool, unformatSNILS
from library.Attach.WebDAVInterface import CWebDAVInterface
import platform

_referral = namedtuple('referral', ('actionId', 'eventId', 'clientId', 'exportId'))
_service = namedtuple('service', ('testCode', 'serviceCode', 'serviceName'))


class CAriadnaExchangeClient():

    datetimeFormat = "yyyy-MM-ddTHH:mm:ss.000"

    def __init__(self, args):
        self.numberOrder = self.numberResult = ''
        if len(args) > 1:
            if args[1] == '-o':
                self.numberOrder = args[2]
            elif args[1] == '-r':
                self.numberResult = args[2]

        self.db = QtGui.qApp.db
        self.preferences = None
        self.mainWindow = None
        self.userHasRight = lambda x: True
        self.userSpecialityId = None
        self.userId = 1
        self.font = lambda: None
        self.logLevel = 2
        self.mapVerifiers = {}
        self.mapUnits = {}
        self.mapUnitsByIdentification = {}
        self.mapTestFederalCodeToId = {}
        self.reloading = False
        self.updateJobTicketStatus = False
        self.resultCount = 50
        self.expirationDays = 14
        self.transferConsent = False
        self.apikey = ''
        self.icmid = ''
        self.url = ''
        self.encoding = ''
        self.timeout = 120
        self.externalSystemId = None
        self.mapTestIdToServices = {}
        if platform.system() != 'Windows':
            self.logDir = '/var/log/AriadnaExchange'
        else:
            self.logDir = os.path.join(unicode(QDir().toNativeSeparators(QDir().homePath())), '.AriadnaExchange')
        self.initLogger()
        self.typeReports = 0
        self.webDAVInterface = CWebDAVInterface()

    def getLogFilePath(self):
        if not os.path.exists(self.logDir):
            os.makedirs(self.logDir)
        s = forceString(QDir().homePath()).split('/')
        homeDir = forceString(s[2]) if len(s) > 1 else ''
        dateString = unicode(fmtDateShort(QDate().currentDate()))
        return os.path.join(self.logDir, '%s_%s.log' % (dateString, homeDir))

    def initLogger(self):
        formatter = logging.Formatter(fmt='%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        handler = RotatingFileHandler(self.getLogFilePath(), maxBytes=1024*1024*50, backupCount=10, encoding='UTF-8')
        handler.setFormatter(formatter)
        handler.setLevel(logging.INFO)
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        oldHandlers = list(logger.handlers)
        logger.addHandler(handler)
        for oldHandler in oldHandlers:
            logger.removeHandler(oldHandler)
        self.logger = logger

    def loadPreferences(self):
        self.preferences = QtGui.qApp.preferences
        self.apikey = forceString(self.db.translate('rbExchangePreferences', 'code', 'LISapikey', 'value'))
        self.icmid = forceString(self.db.translate('rbExchangePreferences', 'code', 'LISicmid', 'value'))
        self.url = forceString(self.db.translate('rbExchangePreferences', 'code', 'LISExchangeUrl', 'value'))

        self.encoding = forceString(self.preferences.appPrefs.get('encoding', 'UTF-8'))
        self.timeout = forceInt(self.preferences.appPrefs.get('timeout', 120))
        self.logDir = forceString(self.preferences.appPrefs.get('logDir', None))
        if not self.logDir:
            if platform.system() != 'Windows':
                self.logDir = '/var/log/AriadnaExchange'
            else:
                self.logDir = os.path.join(unicode(QDir().toNativeSeparators(QDir().homePath())), '.AriadnaExchange')
        self.reloading = forceBool(self.preferences.appPrefs.get('reloading', False))
        self.updateJobTicketStatus = forceBool(self.preferences.appPrefs.get('updateJobTicketStatus', False))
        self.resultCount = forceInt(self.preferences.appPrefs.get('LISResultCount', 50))
        self.expirationDays = forceInt(self.preferences.appPrefs.get('LISExpirationDays', 14))
        self.transferConsent = forceBool(self.preferences.appPrefs.get('transferConsent', False))
        self.typeReports = forceInt(self.preferences.appPrefs.get('typeReports', 0))

    def logException(self, exceptionType, exceptionValue, exceptionTraceback):
        title = repr(exceptionType)
        message = anyToUnicode(exceptionValue)
        QtGui.qApp.log(title, message, 0, traceback.extract_tb(exceptionTraceback))
        sys.__excepthook__(exceptionType, exceptionValue, exceptionTraceback)

    def logCurrentException(self):
        self.logException(*sys.exc_info())

    def main(self):
        if self.db:
            self.externalSystemId = forceRef(self.db.translate('rbExternalSystem', 'code', 'AriadnaLIS', 'id'))
            self.loadPreferences()
            if self.preferences:
                self.initLogger()
                self.mappingTestToServices()
                self.loadUnitsByIdentification()
                self.db.query('CALL getAppLock_prepare()')
                if self.numberResult:
                    self.getResults(number=self.numberResult, count=self.resultCount)
                elif self.numberOrder:
                    if self.numberOrder != 'all':
                        referrals = []
                        referrals.append(self.getReferralByNumber(self.numberOrder))
                    else:
                        referrals = self.getReferrals()
                    for referral in referrals:
                        try:
                            self.sendOrders(referral)
                        except Exception:
                            self.logCurrentException()
                # elif self.options.applyResult:
                #     self.applyResults(self.options.applyResult)
                else:
                    self.getResults(count=self.resultCount)
                    referrals = self.getReferrals()
                    for referral in referrals:
                        try:
                            self.sendOrders(referral)
                        except Exception:
                            self.logCurrentException()

    def mappingTestToServices(self):
        stmt = """SELECT t.id AS testId, st.baseServiceCode, st.testCode, st.serviceCode, st.serviceName
  FROM soc_mapTestToService st
  left JOIN rbTest t ON t.federalCode = st.testCode
  WHERE st.typeLIS = 0"""
        query = self.db.query(stmt)
        while query.next():
            record = query.record()
            testId = forceRef(record.value('testId'))
            testCode = forceString(record.value('testCode'))
            baseServiceCode = forceString(record.value('baseServiceCode'))
            serviceCode = forceString(record.value('serviceCode'))
            serviceName = forceString(record.value('serviceName'))
            self.mapTestIdToServices[(testId, baseServiceCode)] = _service(testCode, serviceCode, serviceName)

    def getReferrals(self):
        referrals = []
        stmt = u"""SELECT a.id as actionId, e.id AS eventId, e.client_id AS clientId, ae.id as exportId
FROM Action a
  left JOIN Event e on e.id = a.event_id
  LEFT JOIN ActionType at ON at.id= a.actionType_id
  left JOIN rbService s ON s.id = at.nomenclativeService_id
  left join Action_Export ae on ae.master_id = a.id and ae.system_id = {externalSystemId}
  WHERE at.flatCode LIKE '%ariadna%'
AND a.deleted = 0
and at.deleted = 0 
AND a.begDate >= NOW() - interval 5 DAY
AND a.begDate < CURDATE() + interval 1 DAY
AND a.status = 5
AND at.serviceType = 10
{reloading}
and e.deleted = 0
order by a.begDate desc
""".format(externalSystemId=self.externalSystemId,
           reloading='and ifnull(ae.success, 0) = 0' if not self.reloading else '')
        query = self.db.query(stmt)
        while query.next():
            record = query.record()
            actionId = forceRef(record.value('actionId'))
            eventId = forceRef(record.value('eventId'))
            clientId = forceRef(record.value('clientId'))
            exportId = forceRef(record.value('exportId'))
            referrals.append(_referral(actionId, eventId, clientId, exportId))
        return referrals

    def getReferralByNumber(self, number):
        referral = None
        if not number:
            return None
        stmt = u"""SELECT a.id as actionId, e.id AS eventId, e.client_id AS clientId, ae.id as exportId
FROM Action a
  left JOIN Event e on e.id = a.event_id
  LEFT JOIN ActionType at ON at.id= a.actionType_id
  left JOIN rbService s ON s.id = at.nomenclativeService_id
  left join Action_Export ae on ae.master_id = a.id and ae.system_id = {externalSystemId}
  left join ActionPropertyType apt on apt.actionType_id = at.id and apt.deleted = 0 and apt.name = 'Номер направления'
  left join ActionProperty ap on ap.action_id = a.id and ap.type_id = apt.id and ap.deleted = 0
  left join ActionProperty_String aps on aps.id = ap.id
  WHERE at.flatCode LIKE '%ariadna%'
AND a.deleted = 0
and at.deleted = 0 
AND at.serviceType = 10
and e.deleted = 0
and aps.value = '{number}'""".format(externalSystemId=self.externalSystemId, number=number)
        query = self.db.query(stmt)
        while query.next():
            record = query.record()
            actionId = forceRef(record.value('actionId'))
            eventId = forceRef(record.value('eventId'))
            clientId = forceRef(record.value('clientId'))
            exportId = forceRef(record.value('exportId'))
            referral = _referral(actionId, eventId, clientId, exportId)
        return referral

    def getHeaders(self):
        headers = {'Content-Type': 'application/json',
                   'ApiKey': self.apikey,
                   'icmid': self.icmid}
        return headers

    def sendOrders(self, referral):
        lockId = None
        response = None
        try:
            self.db.query('CALL getAppLock_(%s, %d, %d, %s, %s, @res)' % (quote('Event'), referral.eventId, 0, 1, quote('AriadnaExchange')))
            query = self.db.query('SELECT @res')

            if query.next():
                record = query.record()
                s = forceString(record.value(0)).split()
                if len(s) > 1:
                    isSuccess = int(s[0])
                    if isSuccess:
                        lockId = int(s[1])
                    else:
                        QtGui.qApp.log(u'Выгрузка направления', u'Событие %i заблокировано' % referral.eventId) #, level=1)
            if lockId:
                context = CInfoContext()
                client = context.getInstance(CClientInfo, referral.clientId)
                action = CActionInfo(context, referral.actionId)
                eventInfo = action.getEventInfo()
                observation = Observation()

                # заполняем данные пациента
                observation.patient.id = forceString(client.id)
                observation.patient.snils = client.SNILS
                if observation.patient.snils:
                    snils = Snils()
                    snils.number = unformatSNILS(client.SNILS)
                    observation.patient.identifications.append(snils)
                observation.patient.regCode = forceString(client.id)
                observation.patient.givenName = client.firstName
                observation.patient.familyName = client.lastName
                observation.patient.middleName = client.patrName

                if client.document and client.document.documentTypeRegionalCode in ['3', '9', '13', '14']:
                    identification = None
                    if client.document.documentTypeRegionalCode == '14':
                        identification = Passport()
                    elif client.document.documentTypeRegionalCode == '3':
                        identification = BirthCertificate()
                    elif client.document.documentTypeRegionalCode == '9':
                        identification = InternationalPassport()
                    elif client.document.documentTypeRegionalCode == '13':
                        identification = Certificate()
                    if client.document.documentTypeRegionalCode == '3':
                        identification.series = client.document.serial
                    else:
                        identification.series = client.document.serial.replace(' ', '').replace('-', '')
                    identification.number = client.document.number
                    if client.document.date.date:
                        try:
                            identification.issueDate = fmtDate(client.document.date.date)
                        except ValueError, e:
                            QtGui.qApp.log('warning', '{0} client.document.date {1}'.format(client.id, anyToUnicode(e))) #, 2)
                    if client.document.origin:
                        identification.issuer = client.document.origin
                    observation.patient.identifications.append(identification)

                observation.patient.address = client.locAddress.__str__()  # адрес проживания
                observation.patient.province = Province()

                for contact in client.contacts:
                    if contact[0].lower() == 'e-mail':
                        observation.patient.email = ' '.join([contact[1], contact[2]])
                        email = Email()
                        email.email = contact[1]
                        observation.patient.telecom.append(email)
                    elif contact[0].lower() == u'домашний телефон':
                        phone = Phone()
                        phone.phone = contact[1]
                        observation.patient.telecom.append(phone)
                        if not observation.patient.phoneNumber:
                            observation.patient.phoneNumber = contact[1]
                    elif contact[0].lower() == u'мобильный телефон':
                        cellular = Cellular()
                        cellular.cellular = contact[1]
                        observation.patient.telecom.append(cellular)
                        observation.patient.phoneNumber = contact[1]

                observation.patient.gender = formatSex(client.sexCode)
                if client.birthDate.date:
                    observation.patient.birthDate = fmtDate(client.birthDate.date)
                observation.patient.workPlace = client.work.__str__()
                observation.patient.externalID = forceString(client.id)
                observation.patient.markID = ''
                observation.patient.mark = ''
                observation.patient.notes = ''
                if client.begDate.date:
                    observation.patient.regDate = fmtDate(client.begDate.date)
                if client.compulsoryPolicy and client.compulsoryPolicy.number:
                    observation.patient.insurance.policyID = ''
                    if client.compulsoryPolicy.serial:
                        observation.patient.insurance.policyCode = ' '.join(
                        [client.compulsoryPolicy.serial, client.compulsoryPolicy.number])
                    else:
                        observation.patient.insurance.policyCode = client.compulsoryPolicy.number
                    if client.compulsoryPolicy.kind:
                        observation.patient.insurance.statusID = client.compulsoryPolicy.kind.regionalCode
                        observation.patient.insurance.statusCode = client.compulsoryPolicy.kind.regionalCode
                        observation.patient.insurance.status = client.compulsoryPolicy.kind.name

                    typCode = None
                    if action.finance:
                        typCode = action.finance.identify('lisAriadna')
                    elif eventInfo.contract.finance:
                        typCode = eventInfo.contract.finance.identify('lisAriadna')
                    if typCode:
                        observation.patient.insurance.typCode = typCode

                    if client.compulsoryPolicy.insurer:
                        observation.patient.insurance.company = Company()
                        observation.patient.insurance.company.id = forceString(client.compulsoryPolicy.insurer.id)
                        observation.patient.insurance.company.localName = client.compulsoryPolicy.insurer.shortName
                        observation.patient.insurance.company.fullName = client.compulsoryPolicy.insurer.fullName
                        observation.patient.insurance.company.code = client.compulsoryPolicy.insurer.tfomsCode
                        observation.patient.insurance.company.phone = client.compulsoryPolicy.insurer.phone
                        observation.patient.insurance.company.cellPhone = ''
                        observation.patient.insurance.company.email = ''
                        observation.patient.insurance.company.externalIdentification = []
                observation.patient.externalIdentification = []
                observation.patient.conditions = []

                action = CActionInfo(context, referral.actionId)

                observation.regDate = action.directionDate.toString(CAriadnaExchangeClient.datetimeFormat)
                observation.originalOrderIdentification.extId = forceString(action.id)
                observation.order.id = forceString(action[u'Номер направления'])
                observation.order.date = action.directionDate.toString(CAriadnaExchangeClient.datetimeFormat)
                observation.order.hisId = forceString(action.id)
                observation.order.medHistory = eventInfo.externalId

                identifySpecimenTypes = action._action.getProperty(u'Биоматериал').getInfo(context).identify('urn:oid:1.2.643.5.1.13.13.11.1081')
                if identifySpecimenTypes:
                    observation.specimenTypes.id = forceString(action._action.getProperty(u'Биоматериал').getInfo(context).id)
                    observation.specimenTypes.name = action._action.getProperty(u'Биоматериал').getInfo(context).name
                    observation.specimenTypes.code = identifySpecimenTypes
                if action.isUrgent:
                    observation.cito = True
                diagnosis = action.MKB.__str__() if action.MKB.__str__() else getEventDiagnosis(referral.eventId)
                # getEventDiagnosis(referral.eventId)
                if diagnosis:
                    observation.diagnosis = diagnosis

                # Передача согласий на выгрузку результатов в ИЕМК для психиатрий
                if self.transferConsent:
                    for consent in client.consents:
                        if consent.code == 'egisz' and (action.directionDate >= consent.date
                                                        and (consent.endDate.isNull() or action.directionDate < consent.endDate)
                                                        and consent.value == 1):
                            additionalForm = AdditionalForm()
                            additionalForm.code = '23001'
                            additionalForm.type = 'string'
                            additionalForm.value = u'да'
                            additionalForm.valueId = '1'
                            observation.additionalForm = [additionalForm]
                            break
                    else:
                        additionalForm = AdditionalForm()
                        additionalForm.code = '23001'
                        additionalForm.type = 'string'
                        additionalForm.value = u'нет'
                        additionalForm.valueId = '2'
                        observation.additionalForm = [additionalForm]

                # заполняем услуги
                services = {}
                baseServiceCode = action.nomenclativeService.code if action.nomenclativeService else ''
                for prop in action._action.getProperties():
                    if prop._type.testId:
                        if not prop._type.isAssignable or (prop._type.isAssignable and prop._isAssigned):
                            service = self.mapTestIdToServices.get((prop._type.testId, baseServiceCode),
                                                                   (None, None, None))
                            if service[0]:
                                services[service.serviceCode] = service
                for key in services:
                    service = services[key]
                    order = OrderInfo()
                    order.service.id = service.testCode
                    order.service.name = service.serviceName
                    order.service.code = service.serviceCode
                    observation.orderInfo.append(order)

                if not observation.orderInfo and action.nomenclativeService:
                    order = OrderInfo()
                    order.service.id = forceString(action._actionType.id)
                    order.service.name = action.nomenclativeService.name
                    order.service.code = action.nomenclativeService.code
                    observation.orderInfo.append(order)

                if not observation.orderInfo:
                    QtGui.qApp.log(u'В направлении отсутствуют коды услуг', observation.order.id) #, 2)
                    return

                person = action.setPerson

                observation.icmid = self.icmid
                observation.orderingInstitution.id = forceString(person.organisation.id)
                observation.orderingInstitution.localName = person.organisation.shortName
                observation.orderingInstitution.fullName = person.organisation.fullName
                if person:
                    observation.orderingInstitution.code = person.organisation.identify('urn:oid:1.2.643.2.69.1.1.1.64')

                observation.orderingInstitution.department = person.orgStructure.code
                if person:
                    observation.orderingInstitution.departmentCode = person.orgStructure.identifyInfoByCode('org.n3').value

                observation.orderingInstitution.phone = person.organisation.phone
                observation.orderingInstitution.icmid = self.icmid

                observation.orderingInstitution.physician = Physician()
                observation.orderingInstitution.physician.id = forceString(person.personId)
                observation.orderingInstitution.physician.regCode = forceString(person.personId)
                observation.orderingInstitution.physician.givenName = person.firstName
                observation.orderingInstitution.physician.familyName = person.lastName
                observation.orderingInstitution.physician.middleName = person.patrName

                headers = self.getHeaders()
                response = requests.post(self.url + '/orders', headers=headers, json=observation.as_json(), timeout=self.timeout)
                tableActionExport = self.db.table(u'Action_Export')
                actionExportRecord = tableActionExport.newRecord()
                actionExportRecord.setValue('id', toVariant(referral.exportId))
                actionExportRecord.setValue('master_id', toVariant(referral.actionId))
                actionExportRecord.setValue('system_id', toVariant(self.externalSystemId))
                actionExportRecord.setValue('dateTime', toVariant(QDateTime().currentDateTime()))
                actionExportRecord.setValue('note', toVariant(response.content.decode('utf-8')))
                if response.status_code == 200:
                    actionExportRecord.setValue('success', toVariant(1))
                    action = CAction(record=self.db.getRecord('Action', '*', referral.actionId))
                    action._record.setValue('status', toVariant(0))
                    action._record.setValue('note', toVariant(u'Заказ успешно выгружен в ЛИС {0}'.format(fmtDate(self.db.getCurrentDatetime()))))
                    action.save(idx=-1)
                else:
                    actionExportRecord.setValue('success', toVariant(0))
                self.db.insertOrUpdate(tableActionExport, actionExportRecord)

                QtGui.qApp.log('response code', anyToUnicode(response.status_code))#, 2)
                QtGui.qApp.log('Last sent', observation.as_json())#, 2)
                QtGui.qApp.log('Last received', anyToUnicode(response.content))#, 2)
        except Exception as e:
            QtGui.qApp.log('error', anyToUnicode(e))#, 1)
        finally:
            if lockId:
                self.db.query('CALL ReleaseAppLock(%d)' % lockId)
        return response

    def getResults(self, order='desc', number=None, count=None):
        params = {}
        headers = self.getHeaders()
        referral = None
        add_url = ''
        if self.typeReports == 0:
            add_url = '/results'
        elif self.typeReports == 1:
            add_url = '/reports/pdf'
        elif self.typeReports == 2:
            add_url = '/reports/semd'

        if (not number or number == 'all') and count:
            params = {'count': forceString(count), 'order': order}
        if number and number != 'all' and self.typeReports == 0:
            referral = self.getReferralByNumber(number)
            if not referral:
                QtGui.qApp.log(u'Загрузка результата {0}'.format(number), u'Направление не найдено в БД') #, level=1)
                return
            url = self.url + add_url + ('/{id}'.format(id=referral.actionId) if referral.actionId else '')
        else:
            url = self.url + add_url
        response = requests.get(url, headers=headers, params=params, timeout=self.timeout)
        jsonData = None
        QtGui.qApp.log(u'Загрузка результатов response code', anyToUnicode(response.status_code)) #, 2)
        QtGui.qApp.log(u'Загрузка результатов response content', response.content.decode('utf-8')) #, 2)

        if response.status_code == 200:
            try:
                jsonData = response.json()
            except Exception as e:
                QtGui.qApp.log('error', anyToUnicode(e)) #, 2)
            if isinstance(jsonData, dict):
                self.saveResults(jsonData, referral)
            elif isinstance(jsonData, list):
                for result in jsonData:
                    self.saveResults(result, referral)

    def saveResults(self, jsonResult, referral):
        context = CInfoContext()
        observation = None
        lockId = None
        try:
            observation = Observation(jsondict=jsonResult)
            # hisId = forceRef(observation.order.hisId)
            if not referral:
                referral = self.getReferralByNumber(observation.order.id)
            if not referral:
                QtGui.qApp.log(u'Загрузка результата {0}'.format(observation.order.id), u'Направление не найдено в БД') #, level=1)
                self.applyResults(observation.order.id)
                return
            if referral.actionId:
                self.db.query('CALL getAppLock_(%s, %d, %d, %s, %s, @res)' % (quote('Event'), referral.eventId, 0, 1, quote('AriadnaExchange')))
                query = self.db.query('SELECT @res')

                if query.next():
                    record = query.record()
                    s = forceString(record.value(0)).split()
                    if len(s) > 1:
                        isSuccess = int(s[0])
                        if isSuccess:
                            lockId = int(s[1])
                        else:
                            QtGui.qApp.log(u'Загрузка результата {0}'.format(observation.order.id),
                                     u'Событие %i заблокировано' % referral.eventId)#, level=1)
                if lockId:
                    action = CAction(record=self.db.getRecord('Action', '*', referral.actionId))
                    if action and action.actionType() and 'ariadna' in action.actionType().flatCode:
                        finishDate = observation.observationDates.finish
                        verifier = None
                        verifierSNILS = None
                        hasErrors = False
                        hasCancelingTest = False
                        isMicrobiology = False
                        testNotes = []
                        signerSNILS = None
                        labGUID = None
                        for ident in observation.orderingInstitution.externalIdentification:
                            if ident.value == 'MISID':
                                labGUID = ident.valueText
                                break

                        for rep in observation.reports:
                            for res in rep.results:
                                testCode = res.measurement.code
                                isTestFounding = False
                                if res.bacteria:
                                    mapSIR = {1: 'S', 2: 'I', 3: 'R'}
                                    antibioticList = []
                                    isMicrobiology = True
                                    if not finishDate:
                                        finishDate = rep.finishDate
                                    if not verifier:
                                        verifier = res.verifier
                                        verifierSNILS = res.verifier.code
                                        if res.verifierRef:
                                            for physician in observation.physicians:
                                                if res.verifierRef.ref == physician.uri:
                                                    for identification in physician.resource.identifications:
                                                        if identification.documentType == 'SNILS':
                                                            verifierSNILS = identification.number
                                    htmlText = u"""<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd"><html><body><table>
                                    <tr><td style="font-size: 10pt;">Выделенные микроорганизмы:</td></tr>"""
                                    subTable = u'''<tr><td>
                                    <table border="1" style=" margin-top:0px; margin-bottom:0px; margin-left:30px; margin-right:0px;" width="70%" cellspacing="0" cellpadding="0">
                                    <tr><th>Антибиотикограмма **</th>'''
                                    # первый проход
                                    i = 0
                                    for bacteria in res.bacteria:
                                        i += 1
                                        if u'1,0E+' in bacteria.resultValue:
                                            value = '10<sup>' + ('%d' % forceInt(bacteria.resultValue.replace(u'1,0E+', ''))) + '</sup>   ' + bacteria.unit
                                        else:
                                            value = bacteria.resultValue
                                        htmlText += u'<tr><td style="font-size: 10pt;"><b>[{0}]</b> {1}<hr></td><td style="font-size: 10pt;">{2}<hr></td></tr>'.format(i, bacteria.name, value)
                                        if bacteria.antibiotics:
                                            subTable += u'<th colspan="2">[{0}] МПК</th>'.format(i)
                                            for antibiotic in bacteria.antibiotics:
                                                if antibiotic.code not in antibioticList:
                                                    antibioticList.append(antibiotic.code)

                                    htmlText += u'<tr></tr>'
                                    if antibioticList:
                                        htmlText += subTable + u"</tr>"

                                    # второй проход
                                    for antibioticCode in antibioticList:
                                        rowText = u"<tr><td>{0}</td>"
                                        antibioticName = None
                                        for bacteria in res.bacteria:
                                            if bacteria.antibiotics:
                                                tmp = u'<td colspan=2><table width=100%><tr><td align="left"></td><td align="right"></td></tr></table></td>'
                                            else:
                                                tmp = ''
                                            for antibiotic in bacteria.antibiotics:
                                                if antibioticCode == antibiotic.code:
                                                    if not antibioticName:
                                                        antibioticName = antibiotic.name
                                                    tmp = u'<td colspan=2><table width=100%><tr><td align="left">{0}</td><td align="right">{1}</td></tr></table></td>'.format(mapSIR.get(antibiotic.sir, ''), escape(antibiotic.mic))
                                                    break
                                            rowText += tmp
                                        htmlText += rowText.format(antibioticName) + u'</tr>'
                                    htmlText += u'</table></td></tr>'
                                    if antibioticList:
                                        htmlText += u'<tr><td align="center">** S - Чувствительный при стандартном режиме дозирования  I - Чувствительный при увеличенной экспозиции  R - Резистентный</td></tr>'
                                    htmlText += u'</table></body></html>'

                                    prop = action.getPropertyByShortName(u'results')
                                    if prop:
                                        prop.setValue(htmlText)
                                elif 'MBIO' in res.resCode:
                                    isMicrobiology = True
                                    if not finishDate:
                                        finishDate = rep.finishDate
                                    if not verifier:
                                        verifier = res.verifier
                                        verifierSNILS = res.verifier.code
                                        if res.verifierRef:
                                            for physician in observation.physicians:
                                                if res.verifierRef.ref == physician.uri:
                                                    for identification in physician.resource.identifications:
                                                        if identification.documentType == 'SNILS':
                                                            verifierSNILS = identification.number
                                    prop = action.getPropertyByShortName(u'results')
                                    if prop:
                                        prop.setValue(res.description)
                                if res.notes:
                                    if isMicrobiology:
                                        testNotes.append(u'{notes}'.format(notes=res.notes))
                                    else:
                                        testNotes.append(u'{name} - {notes}'.format(name=res.measurement.name, notes=res.notes))

                                if res.description:
                                    prop = action.getPropertyByShortName(u'conclusion')
                                    if prop:
                                        prop.setValue(res.description)

                                if testCode == '770700113':  # код теста для Обработки материала
                                    hasCancelingTest = True
                                    action._record.setValue('note', toVariant(u'Исследование отменено: {0}'.format(res.resultValue)))
                                    if not finishDate:
                                        finishDate = rep.finishDate
                                    if not verifier:
                                        verifier = res.verifier
                                        verifierSNILS = res.verifier.code
                                        if res.verifierRef:
                                            for physician in observation.physicians:
                                                if res.verifierRef.ref == physician.uri:
                                                    for identification in physician.resource.identifications:
                                                        if identification.documentType == 'SNILS':
                                                            verifierSNILS = identification.number
                                    continue
                                if not isMicrobiology:
                                    try:
                                        testIds = self.getTestIds(testCode)
                                        for testId in testIds:
                                            unitId = None
                                            if testId:
                                                prop = action.getPropertyByTest(testId)
                                                if prop:
                                                    if res.resultValue:
                                                        prop.setValue(res.resultValue)
                                                    elif res.protocol:
                                                        protocolText = u''
                                                        for item in res.protocol:
                                                            protocolText += item.measurName + ' ' + item.resultText + '; '
                                                        prop.setValue(protocolText.strip())
                                                    if res.norm.text:
                                                        prop.setNorm(res.norm.text.replace('(', '').replace(')', ''))
                                                    # Единицы измерения сначала ищем по идентификатору urn:oid:1.2.643.5.1.13.13.11.1358
                                                    if res.unitCode:
                                                        unitId = self.mapUnitsByIdentification.get(res.unitCode)
                                                    # Если не нашли, ищем по коду ед. измерения
                                                    if not unitId and res.unit:
                                                        unitId = self.getUnitId(res.unit)
                                                    if unitId:
                                                        prop.setUnitId(unitId)

                                                    if not finishDate:
                                                        finishDate = rep.finishDate
                                                    if not verifier:
                                                        verifier = res.verifier
                                                        verifierSNILS = res.verifier.code
                                                        if res.verifierRef:
                                                            for physician in observation.physicians:
                                                                if res.verifierRef.ref == physician.uri:
                                                                    for identification in physician.resource.identifications:
                                                                        if identification.documentType == 'SNILS':
                                                                            verifierSNILS = identification.number
                                                    isTestFounding = True
                                                    break
                                    except:
                                        isTestFounding = False
                                    finally:
                                        if not isTestFounding:
                                            # ТТ 2884 При обмене в лис Ариадна необходимо импортировать доназначенные в лаборатории анализы в отдельное новое свойство
                                            prop = action.getPropertyByShortName(u'additional_research')
                                            if prop:
                                                oldValue = prop.getValue()
                                                if oldValue:
                                                    newValue = oldValue + u'\n' + res.measurement.code + ' ' + res.measurement.name + ' ' + res.resultText + ';'
                                                else:
                                                    newValue = res.measurement.code + ' ' + res.measurement.name + ' ' + res.resultText + ';'
                                                prop.setValue(newValue)
                                                if not finishDate:
                                                    finishDate = rep.finishDate
                                                if not verifier:
                                                    verifier = res.verifier
                                                    verifierSNILS = res.verifier.code
                                                    if res.verifierRef:
                                                        for physician in observation.physicians:
                                                            if res.verifierRef.ref == physician.uri:
                                                                for identification in physician.resource.identifications:
                                                                    if identification.documentType == 'SNILS':
                                                                        verifierSNILS = identification.number
                                            else:
                                                QtGui.qApp.log('error', u'Событие {0}. Направление: {1}. Отсутствует код теста {2}; name:{3}{4}{5}'.format(referral.eventId,
                                                    observation.order.id, testCode, res.measurement.name,
                                                    '; shortName: ' + res.measurement.shortName if res.measurement.shortName else '',
                                                    '; srvdepCode: ' + res.srvdepCode if res.srvdepCode else ''))
                                                hasErrors = True
                        if self.typeReports and hasattr(QtGui.qApp, 'webDAVInterface'):
                            storageInterface = QtGui.qApp.webDAVInterface
                            isFindSameFile = False
                            if observation.binary.pdf and self.typeReports == 1 and storageInterface:
                                name = u'ProtocolAriadna_' + observation.order.id + u'.pdf'
                                for attachedFile in action._attachedFileItemList:
                                    if attachedFile.oldName == name:
                                        if attachedFile.respSignature and attachedFile.respSignature.signatureBytes == observation.binary.practitioner.decode('base64'):
                                            isFindSameFile = True
                                if not isFindSameFile:
                                    _file = storageInterface.uploadBytes(name, observation.binary.pdf.decode('base64'))
                                    signerSNILS = observation.binary.signedDoctor.snils
                                    if signerSNILS:
                                        signerId = self.getVerifierId(labGUID, signerSNILS)
                                        if signerId:
                                            _file.setAuthorId(signerId)
                                            _file.setRespSignature(observation.binary.practitioner.decode('base64'),
                                                                   signerId, QDateTime.currentDateTime())
                                            _file.setOrgSignature(observation.binary.organization.decode('base64'),
                                                                  signerId, QDateTime.currentDateTime())
                                    action._attachedFileItemList.append(_file)
                            elif observation.semd.docData and self.typeReports == 2 and storageInterface:
                                name = u'ProtocolAriadna_' + observation.order.id + u'.xml'
                                for attachedFile in action._attachedFileItemList:
                                    if attachedFile.oldName == name:
                                        if attachedFile.respSignature and attachedFile.respSignature.signatureBytes == observation.binary.practitioner.decode('base64'):
                                            isFindSameFile = True
                                if not isFindSameFile:
                                    _file = storageInterface.uploadBytes(name, observation.semd.docData.decode('base64'))
                                    signerSNILS = observation.semd.signedDoctor.snils
                                    if signerSNILS:
                                        signerId = self.getVerifierId(labGUID, signerSNILS)
                                        if signerId:
                                            _file.setAuthorId(signerId)
                                            _file.setRespSignature(observation.semd.practitionerSig.decode('base64'),
                                                                   signerId, QDateTime.currentDateTime())
                                            _file.setOrgSignature(observation.binary.organizationSig.decode('base64'),
                                                                  signerId, QDateTime.currentDateTime())
                                    action._attachedFileItemList.append(_file)

                        if finishDate:
                            if hasCancelingTest:
                                action._record.setValue('status', toVariant(3))
                                action._record.setValue('endDate', toVariant(None))
                            else:
                                action._record.setValue('status', toVariant(2))
                                action._record.setValue('endDate', toVariant(unFmtDate(finishDate)))
                                action._record.setValue('note', toVariant(
                                    u'Результат загружен из ЛИС {0}'.format(fmtDate(self.db.getCurrentDatetime()))))
                            # Проставление статуса "Закончено" в номерке
                            if self.updateJobTicketStatus:
                                for prop in action._propertiesById.itervalues():
                                    if prop.type().isJobTicketValueType() and prop.getValue():
                                        recordJT = self.db.getRecord('Job_Ticket', '*', prop.getValue())
                                        if recordJT:
                                            recordJT.setValue('endDateTime', toVariant(unFmtDate(finishDate)))
                                            recordJT.setValue('status', toVariant(2))  # закончено
                                            self.db.updateRecord('Job_Ticket', recordJT)

                            if verifierSNILS:
                                verifierId = self.getVerifierId(labGUID, verifierSNILS)
                                if verifierId:
                                    action._record.setValue('person_id', toVariant(verifierId))
                            if testNotes:
                                prop = action.getPropertyByShortName(u'comments')
                                if prop:
                                    prop.setValue(u';'.join(testNotes))
                            action.save(idx=-1)
                            tableActionExport = self.db.table(u'Action_Export')
                            actionExportRecord = tableActionExport.newRecord()
                            actionExportRecord.setValue('id', toVariant(referral.exportId))
                            actionExportRecord.setValue('master_id', toVariant(referral.actionId))
                            actionExportRecord.setValue('system_id', toVariant(self.externalSystemId))
                            actionExportRecord.setValue('success', toVariant(1))
                            actionExportRecord.setValue('dateTime', toVariant(QDateTime().currentDateTime()))
                            actionExportRecord.setValue('note', toVariant(json.dumps(jsonResult)))
                            self.db.insertOrUpdate(tableActionExport, actionExportRecord)
                            if observation.order.id:
                                if not hasErrors:
                                    QtGui.qApp.log(u'Загрузка результата',
                                             u'Направление {0} успешно загружено. Событие {1}. Действие {2}'.format(
                                                                                                observation.order.id,
                                                                                                referral.eventId,
                                                                                                referral.actionId))
                                             #,                                                   level=1)
                                    self.applyResults(observation.order.id)
                                else:
                                    self.applyOnExpiration(observation.order.id, observation.observationDates.finish)


        except Exception as e:
            QtGui.qApp.log('error', anyToUnicode(e))#, 2)
            QtGui.qApp.log('error', u'ошибка при загрузке результата {0}'.format(observation.order.id))#, 2)
            self.applyOnExpiration(observation.order.id, observation.observationDates.finish)
        finally:
            # снимаем блокировку
            if lockId:
                self.db.query('CALL ReleaseAppLock(%d)' % lockId)

    def getVerifierId(self, labGUID, snils):
        result = self.mapVerifiers.get((labGUID, snils), None)
        if not result and labGUID and snils:
            stmt = """SELECT Person.id
FROM Person
LEFT JOIN OrgStructure os ON Person.orgStructure_id = os.id
LEFT JOIN OrgStructure_Identification osi ON os.id = osi.master_id AND osi.deleted = 0
LEFT JOIN rbAccountingSystem ON rbAccountingSystem.id = osi.system_id
WHERE osi.value = '{0}' AND rbAccountingSystem.urn = 'urn:oid:1.2.643.2.69.1.1.1.64' AND snils = '{1}';""".format(labGUID, snils)
            query = self.db.query(stmt)
            while query.next():
                record = query.record()
                result = forceRef(record.value('id'))
                self.mapVerifiers[(labGUID, snils)] = result
        return result

    def getUnitId(self, codeUnit):
        codeUnit = codeUnit.strip()
        result = None
        if codeUnit:
            result = self.mapUnits.get(codeUnit, None)
            if not result:
                stmt = u"select id from rbUnit WHERE code = '{0}' limit 1".format(codeUnit)
                query = self.db.query(stmt)
                while query.next():
                    record = query.record()
                    result = forceRef(record.value('id'))
                if not result:
                    tableUnit = self.db.table('rbUnit')
                    record_unit = tableUnit.newRecord()
                    record_unit.setValue('code', codeUnit)
                    record_unit.setValue('name', codeUnit)
                    result = self.db.insertOrUpdate(tableUnit, record_unit)
                self.mapUnits[codeUnit] = result
        return result

    def loadUnitsByIdentification(self):
        stmt = u"""SELECT u.id, ui.value
FROM rbUnit u
LEFT JOIN rbUnit_Identification ui ON u.id = ui.master_id AND ui.deleted = 0
LEFT JOIN rbAccountingSystem `as` ON ui.system_id = `as`.id
WHERE `as`.urn = 'urn:oid:1.2.643.5.1.13.13.11.1358'"""
        query = self.db.query(stmt)
        while query.next():
            record = query.record()
            unitId = forceRef(record.value('id'))
            value = forceString(record.value('value'))
            self.mapUnitsByIdentification[value] = unitId

    def getTestIds(self, testCode):
        result = self.mapTestFederalCodeToId.get(testCode, [])
        if not result:
            stmt = u"select id from rbTest WHERE federalCode = '{0}'".format(testCode)
            query = self.db.query(stmt)
            while query.next():
                record = query.record()
                result.append(forceRef(record.value('id')))
            self.mapTestFederalCodeToId[testCode] = result
        return result

    def applyResults(self, orderId):
        headers = self.getHeaders()
        json_data = {'orderId': forceString(orderId), 'delivered': True}
        response = requests.post(self.url + '/results', headers=headers, json=json_data, timeout=self.timeout)
        QtGui.qApp.log('applyResults response code', anyToUnicode(response.status_code)) #, 2)
        QtGui.qApp.log('applyResults  Last sent', json_data)#, 2)
        if response.status_code == 200:
            QtGui.qApp.log('applyResults  response content', response.content.decode('utf-8'))#, 2)
        return response

    def applyOnExpiration(self, orderId, finishDate):
        # помечаем успешно полученными незагруженные результаты по сроку давности
        if finishDate and unFmtDate(finishDate) < QDateTime().currentDateTime().addDays(-self.expirationDays):
            try:
                QtGui.qApp.log('expiration', u'Результат закрыт по сроку давности {0}'.format(orderId))#, 2)
                headers = self.getHeaders()
                json_data = {'orderId': forceString(orderId), 'delivered': True}
                response = requests.post(self.url + '/results', headers=headers, json=json_data, timeout=self.timeout)
                QtGui.qApp.log('expiration response code', anyToUnicode(response.status_code))#, 2)
                QtGui.qApp.log('expiration Last sent', json_data)#, 2)
                if response.status_code == 200:
                    QtGui.qApp.log('expiration response content', response.content.decode('utf-8'))#, 2)
                return response
            except Exception as e:
                QtGui.qApp.log('error', anyToUnicode(e))#, 2)


def formatSex(sex):
    sex = forceInt(sex)
    if sex == 1:
        return u'M'
    elif sex == 2:
        return u'F'
    else:
        return u'U'


def fmtDate(date):
    if isinstance(date, QDateTime):
        date = date.toPyDateTime()
    elif isinstance(date, QDate):
        date = date.toPyDate()
    if isinstance(date, datetime.datetime):
        if datetime.date(1981, 1, 1) <= date.date() <= datetime.date(1984, 12, 31):
            return date.strftime("%Y-%m-%dT01:%M:%S.%f")[:-3]
    elif isinstance(date, datetime.date):
        if datetime.date(1981, 1, 1) <= date <= datetime.date(1984, 12, 31):
            return date.strftime("%Y-%m-%dT01:%M:%S.%f")[:-3]
    return date.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]


def unFmtDate(date):
    return QDateTime().fromString(date[:-10] if len(date) == 29 else date[:-4], 'yyyy-MM-ddTHH:mm:ss')


def fmtDateShort(date):
    if isinstance(date, QDateTime):
        date = date.toPyDateTime()
    elif isinstance(date, QDate):
        date = date.toPyDate()
    return date.strftime("%Y-%m-%d")


def getEventDiagnosis(eventId):
    stmt = '''SELECT Diagnosis.MKB FROM Diagnostic
    INNER JOIN rbDiagnosisType ON rbDiagnosisType.id = diagnosisType_id
    LEFT JOIN Diagnosis ON Diagnosis.id = Diagnostic.diagnosis_id
    WHERE Diagnostic.event_id = %d
    AND Diagnostic.deleted = 0
    AND rbDiagnosisType.code = '7'
    LIMIT 1''' % eventId
    query = QtGui.qApp.db.query(stmt)
    if query.first():
        return forceString(query.record().value(0))
    else:
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
    app = CAriadnaExchangeClient(sys.argv)
    app.main()
