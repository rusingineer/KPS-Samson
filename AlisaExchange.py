# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2025 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################
import logging
import os
import platform
import sys
import traceback
import xml.etree.ElementTree as xml
from collections import namedtuple
from logging.handlers import RotatingFileHandler
from optparse import OptionParser

import requests
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import QDir, QVariant, QDate, QDateTime
from requests.auth import HTTPBasicAuth

from Events.Action import CAction
from Events.ActionInfo import CActionInfo
from Registry.Utils import CClientInfo
from library import database
from library.Preferences import CPreferences
from library.PrintInfo import CInfoContext
from library.PrintTemplates import escape
from library.Utils import anyToUnicode, forceString, forceInt, forceRef, toVariant, quote, forceBool

_referral = namedtuple('referral', ('actionId', 'eventId', 'clientId', 'exportId'))
_service = namedtuple('service', ('testCode', 'serviceCode', 'serviceName'))


class CAlisaExchange(QtCore.QCoreApplication):

    iniFileName = '/root/.config/samson-vista/AlisaExchange.ini'

    def __init__(self, args):
        parser = OptionParser(usage="usage: %prog [options]")
        parser.add_option('-r', '--result', dest='numberResult', help='', metavar='numberResult', default='')
        parser.add_option('-o', '--order', dest='numberOrder', help='', metavar='numberOrder', default='')
        parser.add_option('-c', '--config', dest='iniFile', help='custom .ini file name', metavar='iniFile',
                          default=CAlisaExchange.iniFileName)
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
        self.connectionName = 'AlisaExchange'
        if self.options.iniFile:
            self.iniFileName = self.options.iniFile
        elif platform.system() != 'Windows':
            self.iniFileName = '/root/.config/samson-vista/AlisaExchange.ini'
        else:
            self.iniFileName = None
        QtGui.qApp = self
        self.userId = 1
        self.font = lambda: None
        self.logLevel = 2
        self.mapVerifiers = {}
        self.logDir = None
        self.url = None
        self.externalSystemId = None
        self.encoding = 'UTF-8'
        self.timeout = 30
        self.mapUnits = {}
        self.mapTestIdToServices = {}
        self.auth = 0
        self.headers = {'content-type': 'application/soap+xml'}
        self.ns = {'soap': 'http://www.w3.org/2003/05/soap-envelope', 'xs': 'http://www.w3.org/2001/XMLSchema',
                   'xsi': 'http://www.w3.org/2001/XMLSchema-instance', 'm': 'http://lis-alisa.ru', 'tn': 'tN'}
        if platform.system() != 'Windows':
            self.logDir = os.path.join(unicode(QDir().toNativeSeparators(QDir().homePath())), '/var/log/AlisaExchange')
        else:
            self.logDir = os.path.join(unicode(QDir().toNativeSeparators(QDir().homePath())), '.AlisaExchange')
        self.logger = None
        self.transferConsent = False
        self.clientAddressType = 0
        self.initLogger()

    def openDatabase(self):
        self.db = None
        try:
            self.db = database.connectDataBase(self.preferences.dbDriverName, self.preferences.dbServerName,
                                               self.preferences.dbServerPort, self.preferences.dbDatabaseName,
                                               self.preferences.dbUserName, self.preferences.dbPassword,
                                               compressData=self.preferences.dbCompressData,
                                               connectionName=self.connectionName)
            database.registerDocumentTable('Action')
            database.registerDocumentTable('Action_ActionProperty')
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
        handler = RotatingFileHandler(self.getLogFilePath(),
                                      mode='a',
                                      maxBytes=1024*1024*50,
                                      backupCount=10,
                                      encoding='UTF-8',
                                      delay=False)

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
        self.preferences = CPreferences(self.iniFileName if self.iniFileName else 'AlisaExchange.ini')
        self.preferences.load()
        self.url = forceString(self.preferences.appPrefs.get('url', None))
        self.encoding = forceString(self.preferences.appPrefs.get('encoding', 'UTF-8'))
        self.timeout = forceInt(self.preferences.appPrefs.get('timeout', 30))
        logDir = forceString(self.preferences.appPrefs.get('logDir', None))
        if not logDir:
            if platform.system() != 'Windows':
                logDir = '/var/log/AlisaExchange'
            else:
                logDir = os.path.join(unicode(QDir().toNativeSeparators(QDir().homePath())), '.AlisaExchange')
        self.logDir = logDir
        self.logLevel = self.preferences.appPrefs.get('logLevel', 2)
        self.auth = forceBool(self.preferences.appPrefs.get('auth', False))
        self.transferConsent = forceBool(self.preferences.appPrefs.get('transferConsent', False))
        self.clientAddressType = forceInt(self.preferences.appPrefs.get('clientAddressType', 0))

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
            logString = u'%s: %s\n' % (title, message)
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
            self.openDatabase()
            if self.db:
                self.loadGlobalPreferences()
                self.externalSystemId = forceRef(self.db.translate('rbExternalSystem', 'code', 'AlisaLIS', 'id'))
                self.mappingTestToServices()
                self.db.query('CALL getAppLock_prepare()')
                if self.options.numberResult:
                    if self.options.numberResult == 'all':
                        self.requestResultsFromQueue()
                    # запрос результатов по направлениям без результатов за 30 дней
                    if self.options.numberResult == 'without_result':
                        referrals = self.getReferralsWithoutResults()
                        for referral in referrals:
                            try:
                                self.getResults(referral)
                            except Exception as e:
                                self.log('error', anyToUnicode(e), 1)
                    else:
                        self.getResults(self.options.numberResult)

                elif self.options.numberOrder:
                    if self.options.numberOrder != 'all':
                        referrals = [self.getReferralByNumber(self.options.numberOrder)]
                    else:
                        referrals = self.getReferrals()
                    for referral in referrals:
                        self.sendOrders(referral)
                else:
                    self.processLisExchangeQueue()
                    referrals = self.getReferrals()
                    for referral in referrals:
                        self.sendOrders(referral)
                    self.requestResultsFromQueue()
                    self.getResults()
            self.closeDatabase()

    def mappingTestToServices(self):
        stmt = """SELECT t.id AS testId, st.baseServiceCode, st.testCode, st.serviceCode, st.serviceName
    FROM soc_mapTestToService st
    left JOIN rbTest t ON t.code = st.testCode
    WHERE st.typeLIS = 1"""
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
  WHERE at.flatCode LIKE '%alisa%'
AND a.deleted = 0
AND at.serviceType = 10
and at.deleted = 0 
AND a.begDate >= NOW() - interval 5 DAY
AND a.begDate < CURDATE() + interval 1 DAY
AND a.status = 5
and ifnull(ae.success, 0) = 0
and e.deleted = 0""".format(externalSystemId=self.externalSystemId)
        query = self.db.query(stmt)
        while query.next():
            record = query.record()
            actionId = forceRef(record.value('actionId'))
            eventId = forceRef(record.value('eventId'))
            clientId = forceRef(record.value('clientId'))
            exportId = forceRef(record.value('exportId'))
            referrals.append(_referral(actionId, eventId, clientId, exportId))
        return referrals


    def getReferralsWithoutResults(self):
        referrals = []
        stmt = u"""SELECT aps.value as number
FROM Action a
  left JOIN Event e on e.id = a.event_id
  LEFT JOIN ActionType at ON at.id= a.actionType_id
  left join ActionPropertyType apt on apt.actionType_id = at.id and apt.deleted = 0 and apt.name = 'Номер направления'
  left join ActionProperty ap on ap.action_id = a.id and ap.type_id = apt.id and ap.deleted = 0
  left join ActionProperty_String aps on aps.id = ap.id
  left JOIN rbService s ON s.id = at.nomenclativeService_id
  left join Action_Export ae on ae.master_id = a.id and ae.system_id = {externalSystemId}
  WHERE at.flatCode LIKE '%alisa%'
AND a.deleted = 0
and at.deleted = 0
AND at.serviceType = 10
AND a.begDate >= NOW() - interval 30 DAY
AND a.status = 0
and ae.success = 1
and e.deleted = 0""".format(externalSystemId=self.externalSystemId)
        query = self.db.query(stmt)
        while query.next():
            record = query.record()
            number = forceString(record.value('number'))
            referrals.append(number)
        return referrals


    def getReferralByNumber(self, number):
        referral = None
        stmt = u"""SELECT a.id as actionId, e.id AS eventId, e.client_id AS clientId, ae.id as exportId
FROM Action a
  left JOIN Event e on e.id = a.event_id
  LEFT JOIN ActionType at ON at.id= a.actionType_id
  left JOIN rbService s ON s.id = at.nomenclativeService_id
  left join Action_Export ae on ae.master_id = a.id and ae.system_id = {externalSystemId}
  left join ActionPropertyType apt on apt.actionType_id = at.id and apt.deleted = 0 and apt.name = 'Номер направления'
  left join ActionProperty ap on ap.action_id = a.id and ap.type_id = apt.id and ap.deleted = 0
  left join ActionProperty_String aps on aps.id = ap.id
  WHERE at.flatCode LIKE '%alisa%'
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

    def sendOrders(self, referral):
        lockId = None
        response = None
        try:
            self.db.query('CALL getAppLock_(%s, %d, %d, %s, %s, @res)' % (
            quote('Event'), referral.eventId, 0, 1, quote('AlisaExchange')))
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

                bodyXml = u"""<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:lis="http://lis-alisa.ru" xmlns:tn="tN" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                   <soap:Header/>
                   <soap:Body>
                      <lis:SetOrders>
                         <lis:Sender>САМСОН</lis:Sender>
                         <lis:OrdersRequest>
                            <!--1 or more repetitions:-->
                            <tn:заказ>
                               <tn:номерЗаказа>{orderNumber}</tn:номерЗаказа>
                               <tn:датаЗаказа>{orderDate}</tn:датаЗаказа>
                               <tn:отправитель>САМСОН</tn:отправитель>
                               <tn:пациент>
                                  <tn:уникальныйКод>{clientId}</tn:уникальныйКод>
                                  <tn:номерИБ>{eventId}</tn:номерИБ>
                                  <tn:фамилия>{lastName}</tn:фамилия>
                                  <tn:имя>{firstName}</tn:имя>
                                  <tn:отчество>{patrName}</tn:отчество>
                                  <tn:датаРождения>{birthDate}</tn:датаРождения>
                                  <tn:пол>{sex}</tn:пол>
                                  <!--Optional:-->
                                  <tn:полис>
                                     <tn:тип>{policyType}</tn:тип>
                                     <tn:номер>{policyNumber}</tn:номер>
                                     <tn:серия>{policySerial}</tn:серия>
                                     <tn:страховаяКод>{insurerCode}</tn:страховаяКод>
                                     <tn:страховаяНаименование xsi:nil="true"/>
                                     <tn:страховаяОГРН xsi:nil="true"/>
                                     <tn:страховаяКодТерритории xsi:nil="true"/>
                                  </tn:полис>
                                  <!--Optional:-->
                                  <tn:ДУЛ>
                                     <tn:видДокумента>{docType}</tn:видДокумента>
                                     <tn:номер>{docNumber}</tn:номер>
                                     <tn:серия>{docSerial}</tn:серия>
                                  </tn:ДУЛ>
                                  <tn:адрес>
                                     {index_}
                                     {kladrCode}
                                     {district}
                                     {city}
                                     {exactCity}
                                     {street}
                                     {kladrStreetCode}
                                     {number}
                                     {corpus}
                                     {flat}
                                     <tn:GUID_ФИАС xsi:nil="true"/>
                                     {addressText}
                                  </tn:адрес>
                                  <tn:телефон xsi:nil="true"/>
                                  <tn:гражданство xsi:nil="true"/>
                                  <tn:Email xsi:nil="true"/>
                                  <tn:СНИЛС>{snils}</tn:СНИЛС>
                               </tn:пациент>
                               {dopParametrs}
                               <tn:контигентКод xsi:nil="true"/>
                               <tn:контингентНаименование xsi:nil="true"/>
                               <tn:категорияКод xsi:nil="true"/>
                               <tn:категорияНаименование xsi:nil="true"/>
                               <tn:местоРаботы xsi:nil="true"/>
                               <tn:фазаЦикла xsi:nil="true"/>
                               <tn:срокБеременности xsi:nil="true"/>
                               <tn:группаКрови xsi:nil="true"/>
                               <!--Optional:-->
                               <tn:резус xsi:nil="true"/>
                               <tn:вес xsi:nil="true"/>
                               <tn:рост xsi:nil="true"/>
                               <tn:объемМочи xsi:nil="true"/>
                               <tn:палата xsi:nil="true"/>
                               <!--1 or more repetitions:-->
                               <tn:Пробы>
                                  <tn:номерПробы xsi:nil="true"/>
                                  <tn:лаборатория></tn:лаборатория>
                                  <tn:экстренный>{isUrgent}</tn:экстренный>
                                  <tn:биоматериал></tn:биоматериал>
                                  <tn:биоконтейнер xsi:nil="true"/>
                                  {financeName}
                                  <tn:цельИсследования xsi:nil="true"/>
                                  <tn:локализацияКод xsi:nil="true"/>
                                  <tn:локализацияНаименование xsi:nil="true"/>
                                  <tn:заказчик>
                                     <tn:код>{orgStructureCode}</tn:код>
                                     <tn:наименование>{orgStructureName}</tn:наименование>
                                     <tn:ОГРН xsi:nil="true"/>
                                     <tn:Email xsi:nil="true"/>
                                     <tn:краткоеНаименование xsi:nil="true"/>
                                     <tn:отделениеКод xsi:nil="true"/>
                                     <tn:отделениеНаименование xsi:nil="true"/>
                                  </tn:заказчик>
                                  <!--1 or more repetitions:-->
                                  <tn:врачи код="{personCode}" наименование="{personName}" СНИЛС="{personSNILS}"/>
                                  <!--1 or more repetitions:-->
                                  {services}
                                  {datetimeTake}
                               </tn:Пробы>
                               {consent}
                            </tn:заказ>
                         </lis:OrdersRequest>
                         <lis:WEB_ServiceVersion>1.6</lis:WEB_ServiceVersion>
                      </lis:SetOrders>
                   </soap:Body>
                </soap:Envelope>
                """

                birthDate = fmtBirthDate(client.birthDate.date)
                sex = formatSex(client.sexCode)
                clientId = forceString(client.id)
                action = CActionInfo(context, referral.actionId)
                person = action.setPerson
                serviceList = []
                services = {}
                dopParametrs = {}
                dopParametrList = []
                baseServiceCode = action.nomenclativeService.code if action.nomenclativeService else ''
                # заполняем услуги
                for prop in action._action.getProperties():
                    if prop.type().shortName == 'dopParametr':
                        value = forceString(prop.getValue())
                        if value:
                            dopParametrs[prop.type().descr] = value
                    if prop.type().testId:
                        if not prop.type().isAssignable or prop.type().isAssignable and prop.isAssigned():
                            service = self.mapTestIdToServices.get((prop.type().testId, baseServiceCode),
                                                                   (None, None, None))
                            if service[0]:
                                services[service.serviceCode] = service
                if not services and action.nomenclativeService:
                    services[action.nomenclativeService.code] = _service(None,
                                                                         action.nomenclativeService.code,
                                                                         escape(action.nomenclativeService.name))
                for key in services:
                    service = services[key]
                    serviceList.append(u'<tn:услуга код="{serviceCode}" наименование="{serviceName}"/>'.format(
                                    serviceCode=service.serviceCode, serviceName=service.serviceName))

                for key in dopParametrs:
                    value = dopParametrs[key]
                    dopParametrList.append(u'<tn:дополнительныеПараметры параметр="{key}" значение="{value}"/>'.format(
                        key=key, value=value))

                policyType = client.compulsoryPolicy.kind.regionalCode if client.compulsoryPolicy.kind.regionalCode else ''
                orderNumber = forceString(action[u'Номер направления'])
                if action.event.contract and action.event.contract.finance and action.event.contract.finance.identifyInfoByCode('Alisa_vidopl').value:
                    financeName = u'<tn:видОплаты>{0}</tn:видОплаты>'.format(action.event.contract.finance.identifyInfoByCode('Alisa_vidopl').value)
                else:
                    financeName = u'<tn:видОплаты xsi:nil="true"/>'
                if action._action.getPropertyByShortName(u'datetimeTake'):
                    prop = action.getPropertyByShortName(u'datetimeTake')
                    if prop and prop.value:
                        datetimeTake = u'<tn:времяВзятия>{0}</tn:времяВзятия>'.format(fmtDate(prop.value.datetime))
                    else:
                        datetimeTake = u'<tn:времяВзятия xsi:nil="true"/>'
                else:
                    datetimeTake = u'<tn:времяВзятия xsi:nil="true"/>'
                clientAddress = client.regAddress if self.clientAddressType == 0 else client.locAddress
                if clientAddress and clientAddress.index_:
                    index_ = u'<tn:индекс>{0}</tn:индекс>'.format(clientAddress.index_)
                else:
                    index_ = u'<tn:индекс xsi:nil="true"/>'
                # if clientAddress and clientAddress.KLADRCode:
                #     kladrCode = u'<tn:кодТерритории>{0}</tn:кодТерритории>'.format(clientAddress.KLADRCode)
                # else:
                kladrCode = u'<tn:кодТерритории xsi:nil="true"/>'
                if clientAddress and clientAddress.district:
                    district = u'<tn:район>{0}</tn:район>'.format(clientAddress.district)
                else:
                    district = u'<tn:район xsi:nil="true"/>'
                if clientAddress and clientAddress.city:
                    city = u'<tn:город>{0}</tn:город>'.format(clientAddress.city)
                else:
                    city = u'<tn:город xsi:nil="true"/>'
                if clientAddress and clientAddress.exactCity:
                    exactCity = u'<tn:населенныйПункт>{0}</tn:населенныйПункт>'.format(clientAddress.exactCity)
                else:
                    exactCity = u'<tn:населенныйПункт xsi:nil="true"/>'
                if clientAddress and clientAddress.street:
                    street = u'<tn:улица>{0}</tn:улица>'.format(clientAddress.street)
                else:
                    street = u'<tn:улица xsi:nil="true"/>'
                # if clientAddress and clientAddress.KLADRStreetCode:
                #     kladrStreetCode = u'<tn:кодУлицы>{0}</tn:кодУлицы>'.format(clientAddress.KLADRStreetCode)
                # else:
                kladrStreetCode = u'<tn:кодУлицы xsi:nil="true"/>'
                if clientAddress and clientAddress.number:
                    number = u'<tn:дом>{0}</tn:дом>'.format(clientAddress.number)
                else:
                    number = u'<tn:дом xsi:nil="true"/>'
                if clientAddress and clientAddress.corpus:
                    corpus = u'<tn:корпус>{0}</tn:корпус>'.format(clientAddress.corpus)
                else:
                    corpus = u'<tn:корпус xsi:nil="true"/>'
                if clientAddress and clientAddress.flat:
                    flat = u'<tn:квартира>{0}</tn:квартира>'.format(clientAddress.flat)
                else:
                    flat = u'<tn:квартира xsi:nil="true"/>'
                if clientAddress:
                    addressText = u'<tn:адресСтрокой>{0}</tn:адресСтрокой>'.format(clientAddress.__str__())
                else:
                    addressText = u'<tn:адресСтрокой xsi:nil="true"/>'
                orgStructureCode = person.orgStructure.identifyInfoByCode('Orgstructure_Alisa').value
                if orgStructureCode is None:
                    orgStructureCode = person.orgStructure.code
                # Передача согласий на выгрузку результатов в ИЕМК
                consent = ''
                if self.transferConsent:
                    for consent in client.consents:
                        if consent.code == 'egisz' and (action.directionDate >= consent.date
                                                        and (consent.endDate.isNull() or action.directionDate < consent.endDate)
                                                        and consent.value == 1):
                            consent = u'<tn:ЕстьРазрешениеНаПерсДанные>true</tn:ЕстьРазрешениеНаПерсДанные>'
                            break
                    else:
                        consent = u'<tn:ЕстьРазрешениеНаПерсДанные>false</tn:ЕстьРазрешениеНаПерсДанные>'
                preparedBodyXml = bodyXml.format(clientId=clientId, eventId=referral.eventId, lastName=client.lastName,
                                                 firstName=client.firstName, patrName=client.patrName,
                                                 birthDate=birthDate, sex=sex, snils=client.SNILS,
                                                 policyType=policyType, policyNumber=client.compulsoryPolicy.number,
                                                 policySerial=client.compulsoryPolicy.serial,
                                                 insurerCode=client.compulsoryPolicy.insurer.tfomsCode,
                                                 docType=client.document.documentTypeRegionalCode,
                                                 docNumber=client.document.number, docSerial=client.document.serial,
                                                 orgStructureCode=orgStructureCode,
                                                 orgStructureName=person.orgStructure.name, personCode=person.code,
                                                 personName=person.getShortName(),
                                                 personSNILS=person.SNILS,
                                                 orderNumber=orderNumber,
                                                 orderDate=fmtDate(action.directionDate.date),
                                                 isUrgent='true' if action.isUrgent else 'false',
                                                 services=''.join(serviceList),
                                                 dopParametrs=''.join(dopParametrList),
                                                 financeName=financeName,
                                                 datetimeTake=datetimeTake,
                                                 index_=index_,
                                                 kladrCode=kladrCode,
                                                 district=district,
                                                 city=city,
                                                 exactCity=exactCity,
                                                 street=street,
                                                 kladrStreetCode=kladrStreetCode,
                                                 number=number,
                                                 corpus=corpus,
                                                 flat=flat,
                                                 addressText=addressText,
                                                 consent=consent)
                response = requests.post(self.url,
                                         data=preparedBodyXml.encode(self.encoding),
                                         headers=self.headers,
                                         auth=HTTPBasicAuth('ws', 'ws') if self.auth else None,
                                         timeout=self.timeout)
                parser = xml.XMLParser(encoding=self.encoding)
                message = xml.XML(response.content, parser=parser)


                tableActionExport = self.db.table(u'Action_Export')
                actionExportRecord = tableActionExport.newRecord()
                actionExportRecord.setValue('id', toVariant(referral.exportId))
                actionExportRecord.setValue('master_id', toVariant(referral.actionId))
                actionExportRecord.setValue('system_id', toVariant(self.externalSystemId))
                actionExportRecord.setValue('dateTime', toVariant(QDateTime().currentDateTime()))
                actionExportRecord.setValue('note', toVariant(response.content.decode('utf-8')))
                if response.status_code == 200:
                    hasErrors = False
                    errorsMessage = None
                    body = message.find('soap:Body', self.ns)
                    resultsRequestResponse = body.find('m:SetOrdersResponse', self.ns)
                    returnEl = resultsRequestResponse.find('m:return', self.ns)
                    for elResp in list(returnEl):
                        if elResp.tag == u'{tN}ответ':
                            for elRes in list(elResp):
                                if elRes.tag == u'{tN}результатПроверки' and elRes.text == 'ERROR':
                                    hasErrors = True
                                elif elRes.tag == u'{tN}ошибки':
                                    errorsMessage = elRes.text
                    action = CAction(record=self.db.getRecord('Action', '*', referral.actionId))
                    if hasErrors:
                        action.getRecord().setValue('note', toVariant(errorsMessage))
                        actionExportRecord.setValue('success', toVariant(0))
                    else:
                        actionExportRecord.setValue('success', toVariant(1))
                        action.getRecord().setValue('status', toVariant(0))
                        action.getRecord().setValue('note', toVariant(
                            u'Заказ успешно выгружен в ЛИС {0}'.format(fmtDate(self.db.getCurrentDatetime()))))
                    action.save(idx=-1)
                else:
                    actionExportRecord.setValue('success', toVariant(0))
                self.db.insertOrUpdate(tableActionExport, actionExportRecord)

                self.log(u'Выгрузка направления {0} response code'.format(orderNumber), response.status_code, 2)
                self.log(u'Выгрузка направления {0} запрос'.format(orderNumber), preparedBodyXml, 2)
                self.log(u'Выгрузка направления {0} Last received'.format(orderNumber), response.content.decode(self.encoding), 2)
        except Exception as e:
            self.log('error', anyToUnicode(e), 1)
        finally:
            if lockId:
                self.db.query('CALL ReleaseAppLock(%d)' % lockId)
        return response

    def getResults(self, number=''):
        if number == 'all':
            number = ''
        xmlBody = u"""<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:lis="http://lis-alisa.ru">
   <soap:Header/>
   <soap:Body>
      <lis:ResultsRequest>
         <lis:Sender>САМСОН</lis:Sender>
         <lis:OrderID>{orderNumber}</lis:OrderID>
         <lis:WithPDF>false</lis:WithPDF>
      </lis:ResultsRequest>
   </soap:Body>
</soap:Envelope>""".format(orderNumber=number)
        try:
            response = requests.post(self.url,
                                     data=xmlBody.encode(self.encoding),
                                     headers=self.headers,
                                     auth=HTTPBasicAuth('ws', 'ws') if self.auth else None,
                                     timeout=self.timeout)
            parser = xml.XMLParser(encoding=self.encoding)
            message = xml.XML(response.content, parser=parser)

            self.log(u'Загрузка результата response code', anyToUnicode(response.status_code), 2)
            self.log(u'Загрузка результата Last sent', xmlBody, 2)
            self.log(u'Загрузка результата response content', response.content.decode('utf-8'), 2)
        except Exception as e:
            self.log('error', anyToUnicode(e), 1)
            return

        if response.status_code == 200:
            body = message.find('soap:Body', self.ns)
            resultsRequestResponse = body.find('m:ResultsRequestResponse', self.ns)
            returnEl = resultsRequestResponse.find('m:return', self.ns)
            if not list(returnEl):
                self.log(u'Загрузка результата', u'Нет готовых результатов', level=1)
                return

            for order in list(returnEl):
                orderNumber = order.get(u'номерЗаказа')
                referral = self.getReferralByNumber(orderNumber)
                if referral:
                    lockId = None
                    try:
                        self.db.query('CALL getAppLock_(%s, %d, %d, %s, %s, @res)' % (
                            quote('Event'), referral.eventId, 0, 1, quote('AlisaExchange')))
                        query = self.db.query('SELECT @res')

                        if query.next():
                            record = query.record()
                            s = forceString(record.value(0)).split()
                            if len(s) > 1:
                                isSuccess = int(s[0])
                                if isSuccess:
                                    lockId = int(s[1])
                                else:
                                    self.log(u'Загрузка результата {0}'.format(orderNumber),
                                             u'Событие %i заблокировано' % referral.eventId, level=1)
                        if lockId:
                            self.saveReferralResults(order, referral)
                        else:
                            # в новую таблицу пихаем то что не можем сейчас загрузить
                            orderText = xml.tostring(order, encoding=self.encoding, method='xml')
                            orderText = orderText.decode('UTF-8')
                            tableAlisaQueue = self.db.table('AlisaQueue')
                            recordAlisaQueue = tableAlisaQueue.newRecord()
                            recordAlisaQueue.setValue('action_id', toVariant(referral.actionId))
                            recordAlisaQueue.setValue('event_id', toVariant(referral.eventId))
                            recordAlisaQueue.setValue('client_id', toVariant(referral.clientId))
                            recordAlisaQueue.setValue('export_id', toVariant(referral.exportId))
                            recordAlisaQueue.setValue('number', toVariant(orderNumber))
                            recordAlisaQueue.setValue('data', toVariant(orderText))
                            recordAlisaQueue.setValue('createDatetime', toVariant(self.db.getCurrentDatetime()))
                            self.db.insertOrUpdate(tableAlisaQueue, recordAlisaQueue)
                    except Exception as e:
                        self.log('error', anyToUnicode(e), 1)
                    finally:
                        if lockId:
                            self.db.query('CALL ReleaseAppLock(%d)' % lockId)
                else:
                    self.log(u'Загрузка результата', u'направление {0} не найдено в БД'.format(orderNumber), level=1)
        return True

    def saveReferralResults(self, order, referral):
        u"""Сохраняем результат исследования"""
        action = CAction(record=self.db.getRecord('Action', '*', referral.actionId))
        verifierCode = None
        for probe in list(order):
            cancelProbe = False
            validation = False
            finishDate = None
            microBiologyResult = ''
            for elProbe in list(probe):
                if elProbe.tag == u'{tN}отказПробы':
                    cancelProbe = elProbe.text == 'true'
                elif elProbe.tag == u'{tN}статусВыполнения':
                    validation = elProbe.text == u'Валидирована'
                elif elProbe.tag == u'{tN}услуги':
                    for res in list(elProbe):
                        testCode = res.get(u'тестКод')
                        isMicroBiology = res.get(u'родительПолноеНаименование') == u'Микробиология'
                        if isMicroBiology:
                            microBiologyResult = microBiologyResult + u'\r\n' if microBiologyResult else u''
                            microBiologyResult += u'|%s|%s|%s|%s|' % (
                                res.get(u'тестНаименование'), u'да' if res.get(u'результат') else u'нет', testCode,
                                res.get(u'результат'))
                            if list(res):
                                microBiologyResult += u'\r\n------------\r\nАнтибиотики'
                            for antibiotic in list(res):
                                microBiologyResult += u'\r\n{0} АЧ={1} MIC{2}'.format(antibiotic.get(u'абНаименование'),
                                    antibiotic.get(u'чувствительность'), antibiotic.get(u'MIC'))
                            microBiologyResult += u'\r\n========================'
                            if not verifierCode:
                                verifierCode = res.get(u'исполнительКод')
                        else:
                            try:
                                testId = forceRef(self.db.translate('rbTest', 'code', testCode, 'id'))
                                if testId:
                                    prop = action.getPropertyByTest(testId)
                                    if prop:
                                        if res.get(u'отказТеста') == u'false' and res.get(
                                                u'статусВыполнения') == u'Валидирован':
                                            prop.setValue(res.get(u'результат'))
                                        elif res.get(u'отказТеста') == u'true':
                                            if prop.type().shortName == 'deny':
                                                prop.setValue(
                                                    u', '.join([res.get(u'результат'), res.get(u'датаВыполнения')]))
                                            else:
                                                prop.setValue(u'Отказ')
                                        prop.setNorm(res.get(u'референсныйДиапазон'))
                                        prop.setUnitId(self.getUnitId(res.get(u'единицаИзмерения')))
                                        comment = res.get(u'примечание')
                                        if comment:
                                            prop.setComment(comment)
                                        if not verifierCode:
                                            verifierCode = res.get(u'исполнительКод')
                            except Exception:
                                self.log('error', u'Отсутствует код теста {0}'.format(testCode), 2)
                elif elProbe.tag == u'{tN}датаВыполнения':
                    finishDate = elProbe.text

                elif elProbe.tag == u'{tN}номерПробы':
                    if action.getType().hasProperty(u'Номер пробы'):
                        prop = action.getProperty(u'Номер пробы')
                        if prop:
                            prop.setValue(elProbe.text)
            if microBiologyResult:
                prop = action.getProperty(u'Результат')
                if prop:
                    prop.setValue(microBiologyResult)
            if finishDate and (validation or cancelProbe):
                if cancelProbe:
                    action.getRecord().setValue('status', toVariant(3))
                    action.getRecord().setValue('endDate', toVariant(None))
                    action.getRecord().setValue('begDate', toVariant(finishDate))
                else:
                    action.getRecord().setValue('status', toVariant(2))
                    action.getRecord().setValue('endDate', toVariant(unFmtDate(finishDate)))

                action.getRecord().setValue('note', toVariant(u'Результат загружен из ЛИС {0}'.format(fmtDate(self.db.getCurrentDatetime()))))
                tableActionExport = self.db.table(u'Action_Export')
                actionExportRecord = tableActionExport.newRecord()
                actionExportRecord.setValue('id', toVariant(referral.exportId))
                actionExportRecord.setValue('master_id', toVariant(referral.actionId))
                actionExportRecord.setValue('system_id', toVariant(self.externalSystemId))
                actionExportRecord.setValue('success', toVariant(1))
                actionExportRecord.setValue('dateTime', toVariant(QDateTime().currentDateTime()))
                orderText = xml.tostring(order, encoding=self.encoding, method='xml')
                actionExportRecord.setValue('note', toVariant(orderText))
                self.db.insertOrUpdate(tableActionExport, actionExportRecord)
                if verifierCode:
                    verifierId = self.getVerifierId(verifierCode)
                    if verifierId:
                        action.getRecord().setValue('person_id', toVariant(verifierId))
                action.save(idx=-1)

    def requestResultsFromQueue(self):
        records = []
        tableAlisaQueue = self.db.table('AlisaQueue')
        stmt = u"SELECT * FROM AlisaQueue WHERE createDatetime >= NOW() - INTERVAL 14 DAY ORDER BY createDatetime DESC"
        query = self.db.query(stmt)
        while query.next():
            records.append(query.record())

        for record in records:
            lockId = None
            try:
                _id = forceRef(record.value('id'))
                actionId = forceRef(record.value('action_id'))
                eventId = forceRef(record.value('event_id'))
                clientId = forceRef(record.value('client_id'))
                exportId = forceRef(record.value('export_id'))
                referral = _referral(actionId, eventId, clientId, exportId)
                orderNumber = forceString(record.value('number'))
                data = forceString(record.value('data')).encode('UTF-8')
                parser = xml.XMLParser(encoding=self.encoding)
                order = xml.XML(data, parser=parser)

                self.db.query('CALL getAppLock_(%s, %d, %d, %s, %s, @res)' % (quote('Event'), referral.eventId, 0, 1, quote('AlisaExchange')))
                query = self.db.query('SELECT @res')

                if query.next():
                    record = query.record()
                    s = forceString(record.value(0)).split()
                    if len(s) > 1:
                        isSuccess = int(s[0])
                        if isSuccess:
                            lockId = int(s[1])
                        else:
                            self.log(u'Загрузка результата {0}'.format(orderNumber), u'Событие %i заблокировано' % referral.eventId, level=1)
                if lockId:
                    self.saveReferralResults(order, referral)
                    self.db.deleteRecordSimple(tableAlisaQueue, tableAlisaQueue['id'].eq(_id))
            except Exception as e:
                self.log('error', anyToUnicode(e), 1)
            finally:
                if lockId:
                    self.db.query('CALL ReleaseAppLock(%d)' % lockId)

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
                        self.getResults(number)
                        ids_to_delete.append(qid)
                    else:
                        self.log(u'Очередь ЛИС', u'Неизвестный taskType={0} для {1}'.format(taskType, number), 1)
                        ids_to_delete.append(qid)
                except Exception as e:
                    self.log('error', anyToUnicode(e), 1)
                for qid in ids_to_delete:
                    try:
                        self.db.query(u'DELETE FROM LisExchangeQueue WHERE id = {0}'.format(int(qid)))
                    except Exception as e:
                        self.log('error', anyToUnicode(e), 1)
        except Exception as e:
            self.log('error', anyToUnicode(e), 1)


    def getVerifierId(self, codePerson):
        result = self.mapVerifiers.get(codePerson, None)
        if not result:
            stmt = u"select id from Person WHERE regionalCode = '{0}' AND deleted = 0".format(codePerson)
            query = self.db.query(stmt)
            while query.next():
                record = query.record()
                result = forceRef(record.value('id'))
                self.mapVerifiers[codePerson] = result
        return result

    def getUnitId(self, codeUnit):
        result = self.mapUnits.get(codeUnit, None)
        if not result:
            stmt = u"select id from rbUnit WHERE code = '{0}' limit 1".format(codeUnit)
            query = self.db.query(stmt)
            while query.next():
                record = query.record()
                result = forceRef(record.value('id'))
                self.mapUnits[codeUnit] = result
        return result


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
    return date.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]


def fmtDateShort(date):
    if isinstance(date, QDateTime):
        date = date.toPyDateTime()
    elif isinstance(date, QDate):
        date = date.toPyDate()
    return date.strftime("%Y-%m-%d")


def fmtBirthDate(date):
    if isinstance(date, QDateTime):
        date = date.toPyDateTime()
    elif isinstance(date, QDate):
        date = date.toPyDate()
    return date.strftime("%Y-%m-%d+03:00")


def unFmtDate(date):
    return QDateTime().fromString(date, 'yyyy-MM-ddTHH:mm:ss')


if __name__ == '__main__':
    app = CAlisaExchange(sys.argv)
    app.main()
