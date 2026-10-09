#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime
import json
import logging
import os
import re
import sys
import traceback
from logging.handlers import RotatingFileHandler
from optparse import OptionParser

import requests
from collections import namedtuple

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import QDir, QDate, QDateTime, QVariant

from Events.Action import CAction
from Events.ActionInfo import CActionInfo
from Exchange.AriadnaModels.AdditionalForm import AdditionalForm
from Exchange.AriadnaModels.AddressFias import AddressFias
from Exchange.AriadnaModels.BirthCertificate import BirthCertificate
from Exchange.AriadnaModels.BirthDate import BirthDate
from Exchange.AriadnaModels.Born import Born
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
from Exchange.AriadnaModels.Condition import Condition
from Registry.Utils import CClientInfo
from library import database
from library.Preferences import CPreferences
from library.PrintInfo import CInfoContext
from library.PrintTemplates import escape
from library.Utils import anyToUnicode, forceString, forceInt, forceRef, toVariant, quote, forceBool, unformatSNILS
from library.Attach.WebDAVInterface import CWebDAVInterface
import platform

_referral = namedtuple('referral', ('actionId', 'eventId', 'clientId', 'exportId'))
_service = namedtuple('service', ('testCode', 'serviceCode', 'serviceName'))


class CAriadnaExchange(QtCore.QCoreApplication):

    iniFileName = '/root/.config/samson-vista/AriadnaExchange.ini'
    datetimeFormat = "yyyy-MM-ddTHH:mm:ss.000"

    def __init__(self, args):
        parser = OptionParser(usage="usage: %prog [options]")
        parser.add_option('-r', '--result', dest='numberResult', help='', metavar='numberResult', default='')
        parser.add_option('-o', '--order', dest='numberOrder', help='', metavar='numberOrder', default='')
        parser.add_option('-a', '--applyresult', dest='applyResult', help='', metavar='applyResult', default='')
        parser.add_option('-c', '--config', dest='iniFile', help='custom .ini file name',
                          metavar='iniFile', default=CAriadnaExchange.iniFileName
                          )
        (options, _args) = parser.parse_args()
        parser.destroy()

        QtCore.QCoreApplication.__init__(self, args)
        self.options = options
        self.db = None
        self.preferences = None
        self._globalPreferences = {}
        self.mainWindow = None
        self.userHasRight = lambda x: True
        self.userSpecialityId = None
        self.connectionName = 'AriadnaExchange'
        if self.options.iniFile:
            self.iniFileName = self.options.iniFile
        elif platform.system() != 'Windows':
            self.iniFileName = '/root/.config/samson-vista/AriadnaExchange.ini'
        else:
            self.iniFileName = None
        QtGui.qApp = self
        self.userId = 1
        self.font = lambda: None
        self.disableCheckDB = lambda: True
        self.logLevel = 2
        self.mapVerifiers = {}
        self.mapUnits = {}
        self.mapUnitsByIdentification = {}
        self.mapTestFederalCodeToId = {}
        self.reloading = False
        self.updateJobTicketStatus = False
        self.resultCount = 40
        self.expirationDays = 7
        self.transferConsent = False
        self.apikey = ''
        self.icmid = ''
        self.url = ''
        self.encoding = ''
        self.timeout = 60
        self.externalSystemId = None
        if platform.system() != 'Windows':
            self.logDir = '/var/log/AriadnaExchange'
        else:
            self.logDir = os.path.join(unicode(QDir().toNativeSeparators(QDir().homePath())), '.AriadnaExchange')
        self.initLogger()
        self.typeReports = 0
        self.newImportConfirm = False
        self.webDAVInterface = CWebDAVInterface()


    def openDatabase(self):
        self.db = None
        try:
            self.db = database.connectDataBase(self.preferences.dbDriverName,
                                               self.preferences.dbServerName,
                                               self.preferences.dbServerPort,
                                               self.preferences.dbDatabaseName,
                                               self.preferences.dbUserName,
                                               self.preferences.dbPassword,
                                               compressData=self.preferences.dbCompressData,
                                               connectionName=self.connectionName)
            database.registerDocumentTable('rbUnit')
            database.registerDocumentTable('Action')
            database.registerDocumentTable('Action_ActionProperty')
            database.registerDocumentTable('Action_FileAttach')
        except Exception as e:
            self.log('error', anyToUnicode(e), 2)

    def closeDatabase(self):
        if self.db:
            self.db.close()
            self.db = None

    def getLogFilePath(self):
        if not os.path.exists(self.logDir):
            os.makedirs(self.logDir)
        dateString = unicode(fmtDateShort(QDate().currentDate()))
        return os.path.join(QtGui.qApp.logDir, '%s.log' % dateString)

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
        QtGui.qApp.log(u'Путь к файлу конфигурации', self.iniFileName if self.iniFileName else 'AriadnaExchange.ini', level=1)
        self.preferences = CPreferences(self.iniFileName if self.iniFileName else 'AriadnaExchange.ini')
        self.preferences.load()
        self.apikey = forceString(self.preferences.appPrefs.get('apikey', None))
        self.icmid = forceString(self.preferences.appPrefs.get('icmid', None))
        self.url = forceString(self.preferences.appPrefs.get('url', None))
        self.encoding = forceString(self.preferences.appPrefs.get('encoding', 'UTF-8'))
        self.timeout = forceInt(self.preferences.appPrefs.get('timeout', 60))
        self.logDir = forceString(self.preferences.appPrefs.get('logDir', None))
        if not self.logDir:
            if platform.system() != 'Windows':
                self.logDir = '/var/log/AriadnaExchange'
            else:
                self.logDir = os.path.join(unicode(QDir().toNativeSeparators(QDir().homePath())), '.AriadnaExchange')
        self.logLevel = self.preferences.appPrefs.get('logLevel', 2)
        self.reloading = forceBool(self.preferences.appPrefs.get('reloading', False))
        self.updateJobTicketStatus = forceBool(self.preferences.appPrefs.get('updateJobTicketStatus', False))
        self.resultCount = forceInt(self.preferences.appPrefs.get('resultCount', 40))
        self.expirationDays = forceInt(self.preferences.appPrefs.get('expirationDays', 7))
        self.transferConsent = forceBool(self.preferences.appPrefs.get('transferConsent', False))
        self.connectionName = forceString(self.preferences.appPrefs.get('connectionName', 'AriadnaExchange'))
        self.typeReports = forceInt(self.preferences.appPrefs.get('typeReports', 0))
        self.newImportConfirm = forceBool(self.preferences.appPrefs.get('newImportConfirm', False))

    def loadGlobalPreferences(self):
        if self.db:
            try:
                recordList = self.db.getRecordList('GlobalPreferences')
            except:
                recordList = []
            for record in recordList:
                code  = forceString(record.value('code'))
                value = forceString(record.value('value'))
                self._globalPreferences[code] = value


    def checkGlobalPreference(self, code, chkValue, default=None):
        value = self._globalPreferences.get(code, default)
        if value:
            return unicode(value).lower() == unicode(chkValue).lower()
        return False

    def currentOrgId(self):
        return forceRef(self.preferences.appPrefs.get('orgId', QVariant()))

    def log(self, title, message, level=2, stack=None):
        if level <= QtGui.qApp.logLevel:
            if isinstance(message, list):
                for item in message:
                    if "binary" in item:
                        item["binary"] = ''
            elif isinstance(message, dict):
                for item in message:
                    if "binary" in item:
                        item["binary"] = ''
            elif "binary" in message:
                pattern = r'"binary"\s*:\s*{[^}]*}'
                message = re.sub(pattern, '"binary" : {}', message)
            logString = u'%s: %s\n' % (title, str(message).decode(encoding="unicode_escape") if type(message) is dict else message)
            if stack:
                try:
                    logString += anyToUnicode(''.join(traceback.format_list(stack))).decode('utf-8') + '\n'
                except:
                    logString += 'stack lost\n'
            self.logger.info(logString)

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
            self.initLogger()
            self.openDatabase()
            if self.db:
                self.loadGlobalPreferences()
                self.externalSystemId = forceRef(self.db.translate('rbExternalSystem', 'code', 'AriadnaLIS', 'id'))

                # Путь к файлохранилищу берем из глобальных настроек в БД
                rec_glb = self.db.getRecordEx('GlobalPreferences', 'value', 'code = \'WebDAV\'')
                if rec_glb:
                    url = forceString(rec_glb.value(0))
                    url = url.replace('${dbServerName}', QtGui.qApp.preferences.dbServerName)
                    self.webDAVInterface.setWebDAVUrl(url)

                self.loadUnitsByIdentification()
                self.db.query('CALL getAppLock_prepare()')
                if self.options.numberResult:
                    i = 0
                    resCount = self.resultCount
                    while resCount == self.resultCount and i < 10: # ТТ 3299 Циклическая загрузка результатов
                        resCount = self.getResults(number=self.options.numberResult, count=self.resultCount)
                        i += 1
                elif self.options.numberOrder:
                    if self.options.numberOrder != 'all':
                        referrals = []
                        referrals.append(self.getReferralByNumber(self.options.numberOrder))
                    else:
                        referrals = self.getReferrals()
                    for referral in referrals:
                        try:
                            self.sendOrders(referral)
                        except Exception:
                            self.logCurrentException()
                elif self.options.applyResult:
                    self.applyResults(self.options.applyResult)
                else:
                    self.processLisExchangeQueue()
                    i = 0
                    resCount = self.resultCount
                    while resCount == self.resultCount and i < 10: # ТТ 3299 Циклическая загрузка результатов
                        resCount = self.getResults(count=self.resultCount)
                        i += 1

                    referrals = self.getReferrals()
                    for referral in referrals:
                        try:
                            self.sendOrders(referral)
                        except Exception:
                            self.logCurrentException()
        self.closeDatabase()


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
                        self.log(u'Выгрузка направления', u'Событие %i заблокировано' % referral.eventId, level=1)
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
                        except ValueError as e:
                            self.log('warning', '{0} client.document.date {1}'.format(client.id, anyToUnicode(e)), 2)
                    if client.document.origin:
                        identification.issuer = client.document.origin
                    observation.patient.identifications.append(identification)

                locAddress = client.locAddress.__str__()
                regAddress = client.regAddress.__str__()
                observation.patient.address = locAddress  # адрес проживания
                if regAddress:
                    regAddressFias = AddressFias()
                    regAddressFias.type = 'registry'
                    regAddressFias.string = regAddress
                    observation.patient.addressFias.append(regAddressFias)
                if locAddress:
                    locAddressFias = AddressFias()
                    locAddressFias.type = 'actual'
                    locAddressFias.string = locAddress
                    observation.patient.addressFias.append(locAddressFias)

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
                    observation.patient.born = Born()
                    observation.patient.born.birthDate = BirthDate()
                    observation.patient.born.birthDate.bDate = fmtDateShort(client.birthDate.date)
                    observation.patient.born.birthDate.bTime = client.birthTime.toString('HH:mm:ss:zzz')
                    # observation.patient.birthDate = fmtDate(client.birthDate.date)
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

                # необязательные свойства для observation.patient.conditions
                # в последствии можно будет расширять для новых property в действиях (учитывая что последующие будут
                # String и иметь ValueDomain: 'код.Название, ...')
                # 'shortName': код параметра для передачи (groupCode)
                patientConditionsType = {
                    u'trimester': u'1',
                    u'week': u'2',
                    u'cycle_phase': u'3'
                }

                for conditionShortName, groupCode in patientConditionsType.items():
                    prop = action._action.getPropertyByShortName(conditionShortName)
                    if prop and prop.getValue():
                        condition = Condition()
                        conditionId = forceString(prop.getValue()).split(u'.')
                        if conditionId and conditionId[0].isdigit():
                            condition.groupCode = groupCode
                            condition.id = conditionId[0]
                            condition.code = conditionId[0]
                            observation.patient.conditions.append(condition)

                action = CActionInfo(context, referral.actionId)

                observation.regDate = action.directionDate.toString(CAriadnaExchange.datetimeFormat)
                observation.originalOrderIdentification.extId = forceString(action.id)
                observation.order.id = forceString(action[u'Номер направления'])
                observation.order.date = action.directionDate.toString(CAriadnaExchange.datetimeFormat)
                observation.order.hisId = forceString(action.id)
                observation.order.medHistory = eventInfo.externalId if eventInfo.externalId else forceString(client.id)
                # комментарий к биоматериалу
                commentSpecimen = action._action.getPropertyByShortName('commentSpecimen')
                if commentSpecimen and commentSpecimen.getValue():
                    observation.order.commentSpecimen = forceString(commentSpecimen.getValue())

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
                services = set()
                for prop in action._action.getProperties():
                    if prop.type().testId:
                        if not prop.type().isAssignable or (prop.type().isAssignable and prop.isAssigned()):
                            serviceCode = prop.type().descr
                            if serviceCode:
                                services.add(serviceCode)
                for service in services:
                    order = OrderInfo()
                    order.service.code = service
                    observation.orderInfo.append(order)

                if not observation.orderInfo and action.nomenclativeService:
                    order = OrderInfo()
                    order.service.code = action.nomenclativeService.code
                    observation.orderInfo.append(order)

                if not observation.orderInfo:
                    self.log(u'В направлении отсутствуют коды услуг', observation.order.id, 2)
                    return None

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

                self.log('response code', anyToUnicode(response.status_code), 2)
                self.log('Last sent', observation.as_json(), 2)
                self.log('Last received', anyToUnicode(response.content), 2)
        except Exception as e:
            self.log('error', anyToUnicode(e), 1)
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
        resCount = 0
        if (not number or number == 'all') and count:
            params = {'count': forceString(count), 'order': order}
        if number and number != 'all' and self.typeReports == 0:
            referral = self.getReferralByNumber(number)
            if not referral:
                self.log(u'Загрузка результата {0}'.format(number), u'Направление не найдено в БД', level=1)
                return
            url = self.url + add_url + ('/{id}'.format(id=referral.actionId) if referral.actionId else '')
        else:
            url = self.url + add_url

        self.log(u'Загрузка результатов', url, 2)
        response = requests.get(url, headers=headers, params=params, timeout=self.timeout)
        jsonData = None

        self.log(u'Загрузка результатов response code', anyToUnicode(response.status_code), 2)
        self.log(u'Загрузка результатов response content', response.content.decode('utf-8'), 2)

        if response.status_code == 200:
            try:
                jsonData = response.json()
            except Exception as e:
                self.log('error', anyToUnicode(e), 2)
            if isinstance(jsonData, dict):
                resCount = 1
                self.saveResults(jsonData, referral)
            elif isinstance(jsonData, list):
                resCount = len(jsonData)
                for result in jsonData:
                    self.saveResults(result, referral)
        return resCount

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
                self.log(u'Загрузка результата {0}'.format(observation.order.id), u'Направление не найдено в БД', level=1)
                self.applyResults(observation.order.hisId if self.newImportConfirm else observation.order.id)
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
                            self.log(u'Загрузка результата {0}'.format(observation.order.id),
                                     u'Событие %i заблокировано' % referral.eventId, level=1)
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

                        # ТТ 2884 При обмене в лис Ариадна необходимо импортировать доназначенные в лаборатории анализы в отдельное новое свойство
                        prop = action.getPropertyByShortName(u'additional_research')
                        if prop:
                            # При загрузке результата повторно нужно очищать это свойство
                            prop.setValue(None)

                        for rep in observation.reports:
                            for res in rep.results:
                                testCode = res.measurement.code
                                isTestFounding = False
                                if res.bacteria:
                                    mapSIR = {1: 'S', 2: 'I', 3: 'R'}
                                    antibioticList = []
                                    phenotypeList = []
                                    resistanceMarkerList = []
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
                                    <tr><th>{0}</th>'''
                                    subTableAntibiotic= u''
                                    subTablePhenotype = u''
                                    subTableResistanceMarkers = u''
                                    # чтоб по названию искать номер для соотвествия бактерии к сообщению экспертной системы
                                    bacteriaToIndex = dict()
                                    # первый проход
                                    i = 0
                                    for bacteria in res.bacteria:
                                        i += 1
                                        try:
                                            if u'1,0E+' in bacteria.resultValue:
                                                value = '10<sup>' + ('%d' % forceInt(bacteria.resultValue.replace(u'1,0E+', ''))) + '</sup>   ' + bacteria.unit
                                            else:
                                                value = bacteria.resultValue
                                        except ValueError:
                                            value = bacteria.resultValue
                                        htmlText += u'<tr><td style="font-size: 10pt;"><b>[{0}]</b> {1}<hr></td><td style="font-size: 10pt;">{2}<hr></td></tr>'.format(i, bacteria.name, value)
                                        if bacteria.antibiotics:
                                            subTableAntibiotic += u'<th colspan="2">[{0}] МПК</th>'.format(i)
                                            for antibiotic in bacteria.antibiotics:
                                                if antibiotic.code not in antibioticList:
                                                    antibioticList.append(antibiotic.code)
                                        if bacteria.phenotypes:
                                            subTablePhenotype += u'<th colspan="2">[{0}]</th>'.format(i)
                                            for phenotype in bacteria.phenotypes:
                                                if phenotype.id not in phenotypeList:
                                                    phenotypeList.append(phenotype.id)
                                        if bacteria.resistanceMarkers:
                                            subTableResistanceMarkers += u'<th colspan="2">[{0}]</th>'.format(i)
                                            for resistanceMarker in bacteria.resistanceMarkers:
                                                if resistanceMarker.id not in resistanceMarkerList:
                                                    resistanceMarkerList.append(resistanceMarker.id)
                                        bacteriaToIndex[bacteria.name] = i

                                    htmlText += u'<tr></tr>'
                                    if antibioticList:
                                        htmlText += subTable.format(u'Антибиотикограмма **') + subTableAntibiotic + u"</tr>"

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

                                    if phenotypeList:
                                        htmlText += subTable.format(u'Фенотипические тесты') + subTablePhenotype + u"</tr>"

                                    for phenotypeCode in phenotypeList:
                                        rowText = u"<tr><td>{0}</td>"
                                        phenotypeName = None
                                        for bacteria in res.bacteria:
                                            if bacteria.phenotypes:
                                                tmp = u'<td colspan=2><table width=100%><tr><td align="center"></td></tr></table></td>'
                                            else:
                                                tmp = ''
                                            for phenotype in bacteria.phenotypes:
                                                if phenotypeCode == phenotype.id:
                                                    if not phenotypeName:
                                                        phenotypeName = phenotype.nameShort
                                                    tmp = u'<td colspan=2><table width=100%><tr><td align="center">{0}</td></tr></table></td>'.format(escape(phenotype.value))
                                                    break
                                            rowText += tmp
                                        htmlText += rowText.format(phenotypeName) + u'</tr>'
                                    htmlText += u'</table></td></tr>'

                                    if resistanceMarkerList:
                                        htmlText += subTable.format(u'Маркеры резистентности') + subTableResistanceMarkers + u"</tr>"

                                    for resistanceMarkerCode in resistanceMarkerList:
                                        rowText = u"<tr><td>{0}</td>"
                                        resistanceMarkerName = None
                                        for bacteria in res.bacteria:
                                            if bacteria.resistanceMarkers:
                                                tmp = u'<td colspan=2><table width=100%><tr><td align="center"></td></tr></table></td>'
                                            else:
                                                tmp = ''
                                            for resistanceMarker in bacteria.resistanceMarkers:
                                                if resistanceMarkerCode == resistanceMarker.id:
                                                    if not resistanceMarkerName:
                                                        resistanceMarkerName = resistanceMarker.name
                                                    tmp = u'<td colspan=2><table width=100%><tr><td align="center">{0}</td></tr></table></td>'.format(
                                                        "&#9679;")
                                                    break
                                            rowText += tmp
                                        htmlText += rowText.format(resistanceMarkerName) + u'</tr>'
                                    htmlText += u'</table></td></tr>'

                                    if antibioticList:
                                        htmlText += u'<tr><td align="center">** S - Чувствительный при стандартном режиме дозирования  I - Чувствительный при увеличенной экспозиции  R - Резистентный</td></tr>'
                                    htmlText += u'</table>'

                                    if res.xpsMessages:
                                        groups = []
                                        group = None

                                        for xpsMessage in res.xpsMessages:
                                            code = (xpsMessage.antibioticList, xpsMessage.bacteriaCode)

                                            if group is None or group['code'] != code:
                                                bacteriaIndex = bacteriaToIndex.get(xpsMessage.title.split(u'/')[0], 0)
                                                group = {
                                                    'code': code,
                                                    'title': u'[%i] %s' % (bacteriaIndex, xpsMessage.title),
                                                    'messages': [],
                                                }
                                                groups.append(group)

                                            group['messages'].append(xpsMessage.message)

                                        headerStyle = u'font-size: 14px; font-weight: bold; text-decoration: underline; margin: 10px 0 6px 0;'
                                        titleStyle = u'font-size: 12px; font-weight: bold; font-style: italic; margin: 6px 0 2px 0;'
                                        listStyle = u'margin: 0 0 4px 0; list-style-type: decimal; -qt-list-indent: 1;'
                                        itemStyle = u'font-size: 12px; font-style: italic; margin: 0; line-height: 140%;'

                                        groupsBlock = u'<div style="{style}">Сообщения экспертной системы</div>'.format(style=headerStyle)
                                        for group in groups:
                                            groupsBlock += u'<p style="{style}">{title}</p>'.format(style=titleStyle, title=group['title'])
                                            items = u''.join(
                                                u'<li style="{style}">{message}</li>'.format(style=itemStyle, message=message)
                                                for message in group['messages']
                                            )
                                            groupsBlock += u'<ol style="{style}">{items}</ol>'.format(style=listStyle, items=items)

                                        htmlText += groupsBlock

                                    htmlText += u'</body></html>'

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
                                    # ТТ 3757 "Ариадна. МБИО. Внести корректировки в импорт результата, когда нет выявленных отклонений"
                                    # prop = action.getPropertyByShortName(u'results')
                                    # if prop:
                                    #     prop.setValue(res.description)
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
                                                        # TT 4806 "Загрузка комментария из ЛИС"
                                                        # по задаче необходимо сохранять примечание к нормам,
                                                        # а если норм нет, то смысл вставлять
                                                        if res.description:
                                                            prop.setComment(res.description)
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
                                                self.log('error', u'Событие {0}. Направление: {1}. Отсутствует код теста {2}; name:{3}{4}{5}'.format(referral.eventId,
                                                    observation.order.id, testCode, res.measurement.name,
                                                    '; shortName: ' + res.measurement.shortName if res.measurement.shortName else '',
                                                    '; srvdepCode: ' + res.srvdepCode if res.srvdepCode else ''), 2)
                                                hasErrors = True
                        if self.typeReports in [1, 2] and hasattr(QtGui.qApp, 'webDAVInterface'):
                            storageInterface = QtGui.qApp.webDAVInterface
                            if storageInterface:
                                isFindSameFile = False
                                if self.typeReports == 1:
                                    binary = observation.binary.pdf
                                    practitionerSig = observation.binary.practitioner
                                    organizationSig = observation.binary.organization
                                    signerSNILS = observation.binary.signedDoctor.snils if observation.binary.signedDoctor else ''
                                    fileName = u'ProtocolAriadna_' + observation.order.id + u'.pdf'
                                else:
                                    binary = observation.semd.docData
                                    practitionerSig = observation.semd.practitionerSig
                                    organizationSig = observation.semd.organizationSig
                                    signerSNILS = observation.semd.signedDoctor.snils if observation.semd.signedDoctor else ''
                                    fileName = u'ProtocolAriadna_' + observation.order.id + u'.xml'

                                if binary and practitionerSig and signerSNILS:
                                    signerId = self.getVerifierId(labGUID, signerSNILS)
                                    if signerId:
                                        for attachedFile in action.getAttachedFileItemList():
                                            if attachedFile.oldName == fileName:
                                                if attachedFile.respSignature and attachedFile.respSignature.signatureBytes == practitionerSig.decode('base64'):
                                                    isFindSameFile = True
                                                    break
                                        if not isFindSameFile:
                                            _file = storageInterface.uploadBytes(fileName, binary.decode('base64'))
                                            _file.setAuthorId(signerId)
                                            _file.setRespSignature(practitionerSig.decode('base64'), signerId, QDateTime.currentDateTime())
                                            _file.setOrgSignature(organizationSig.decode('base64'), signerId, QDateTime.currentDateTime())
                                            action.getAttachedFileItemList().append(_file)

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
                                    self.log(u'Загрузка результата',
                                             u'Направление {0} успешно загружено. Событие {1}. Действие {2}'.format(
                                                                                                observation.order.id,
                                                                                                referral.eventId,
                                                                                                referral.actionId),
                                                                                            level=1)
                                    self.applyResults(observation.order.hisId if self.newImportConfirm else observation.order.id)
                                else:
                                    self.applyOnExpiration(observation.order.hisId if self.newImportConfirm else observation.order.id, observation.observationDates.finish)


        except Exception as e:
            self.log('error', anyToUnicode(e), 2)
            self.log('error', u'ошибка при загрузке результата {0}'.format(observation.order.id), 2)
            self.applyOnExpiration(observation.order.hisId if self.newImportConfirm else observation.order.id, observation.observationDates.finish)
        finally:
            # снимаем блокировку
            if lockId:
                self.db.query('CALL ReleaseAppLock(%d)' % lockId)

    def getVerifierId(self, labGUID, snils):
        result = self.mapVerifiers.get((labGUID, snils), None)
        if not result and labGUID and snils:
            stmt = u"""SELECT Person.id
FROM Person
LEFT JOIN OrgStructure os ON Person.orgStructure_id = os.id
LEFT JOIN OrgStructure_Identification osi ON os.id = osi.master_id AND osi.deleted = 0
LEFT JOIN rbAccountingSystem ON rbAccountingSystem.id = osi.system_id
WHERE Person.deleted = 0 AND osi.value = '{0}' AND rbAccountingSystem.urn = 'urn:oid:1.2.643.2.69.1.1.1.64' AND Person.snils = '{1}'
    AND os.deleted = 0 AND (Person.retireDate IS NULL OR Person.retireDate >= NOW());""".format(labGUID, snils)
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
        if self.newImportConfirm:
            url = self.url + '/results/delivered'
        else:
            url = self.url + '/results'
        response = requests.post(url, headers=headers, json=json_data, timeout=self.timeout)
        self.log('applyResults response code', anyToUnicode(response.status_code), 2)
        self.log('applyResults  Last sent', json_data, 2)
        self.log('applyResults  response content', response.content.decode('utf-8'), 2)
        return response

    def applyOnExpiration(self, orderId, finishDate):
        # помечаем успешно полученными незагруженные результаты по сроку давности
        if finishDate and unFmtDate(finishDate) < QDateTime().currentDateTime().addDays(-self.expirationDays):
            try:
                self.log('expiration', u'Результат закрыт по сроку давности {0}'.format(orderId), 2)
                headers = self.getHeaders()
                json_data = {'orderId': forceString(orderId), 'delivered': True}
                if self.newImportConfirm:
                    url = self.url + '/results/delivered'
                else:
                    url = self.url + '/results'
                response = requests.post(url, headers=headers, json=json_data, timeout=self.timeout)
                self.log('expiration response code', anyToUnicode(response.status_code), 2)
                self.log('expiration Last sent', json_data, 2)
                self.log('expiration response content', response.content.decode('utf-8'), 2)
                return response
            except Exception as e:
                self.log('error', anyToUnicode(e), 2)
        return None

    def processLisExchangeQueue(self):
        """
        обрабатывает очередь из LisExchangeQueue, как если бы запускали с ключами -o,-r
        """
        try:
            query = self.db.query(u"""
                SELECT id, taskType, number
                FROM LisExchangeQueue
                WHERE externalSystem_id = {extId}
                ORDER BY createDatetime
                """.format(extId=int(self.externalSystemId)))
            ids_to_delete = []
            while query.next():
                qid = forceRef(query.value(0))
                taskType = int(forceRef(query.value(1)) or 0)
                number = forceString(query.value(2))

                try:
                    if taskType == 1: # send -o
                        referral = self.getReferralByNumber(number)
                        if referral:
                            self.sendOrders(referral)
                        else:
                            self.log(u'Очередь ЛИС', u'направление {0} не найдено в БД'.format(number), 1)
                        ids_to_delete.append(qid)
                    elif taskType == 2: #result -r
                        processed = self.getResults(number, count=self.resultCount)
                        if processed and int(processed) > 0:
                            ids_to_delete.append(qid)
                    else:
                        self.log(u'Очередь ЛИС', u'Неизвестный taskType={0} для {1}'.format(taskType, number), 1)
                        ids_to_delete.append(qid)
                except Exception as e:
                    self.logCurrentException()
                for qid in ids_to_delete:
                    try:
                        self.db.query(u'DELETE FROM LisExchangeQueue WHERE id = {0}'.format(int(qid)))
                    except Exception as e:
                        self.logCurrentException()
        except Exception as e:
            self.logCurrentException()


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
    app = CAriadnaExchange(sys.argv)
    app.main()
