#!/usr/bin/env python
# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2016-2022 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################
##
## Скрипт обмена данными с лабораториями и ЛИС по протоколам ASTM и FHIR
##
#############################################################################

import codecs
import locale
import os.path
import sys
import traceback
import json
from collections import namedtuple
from shutil import copyfile

from optparse import OptionParser

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import QDateTime

from Events.ActionStatus import CActionStatus
from library import database
from library.Attach.WebDAVInterface import CWebDAVInterface
from library.database import connectDataBase
from library.Preferences import CPreferences
from library.Utils import forceInt, forceString, forceRef, smartDict, setPref, quote, forceBool

from Exchange.Lab.AstmE1394.Message          import CMessage
from Exchange.Lab.AstmE1381.FileExchangeLoop import CFileExchangeLoop
from Registry.Utils                          import getClientInfo
from TissueJournal.ProbeWorkListPage         import CProbeSaver, probeSent2LIS
from TissueJournal.LabInterface              import bundleProbes
from TissueJournal.LabInterfaceFHIR          import ( sendOrdersOverFHIR    as sendOrdersOverFHIR050,
                                                      pickupResultsOverFHIR as pickupResultsOverFHIR050,
                                                    )
from TissueJournal.LabInterfaceFHIR102 import (sendOrdersOverFHIR as sendOrdersOverFHIR102,
                                               pickupResultsOverFHIR as pickupResultsOverFHIR102,
                                               importOrdersOverFhir, CFHIRExchange
                                               )
from TissueJournal.LabInterfaceASTM          import sendOrdersOverASTM
from TissueJournal.TissueJournalModels       import CSamplePreparationModel
from TissueJournal.ExportLocalLabResultsToUsish import exportLocalLabResultsToUsish, exportLabResultsToUsish, exportLocalLabResultsToUsishKK
from TissueJournal.Utils                     import getEquipmentInterface


globalProcessedItemList = []
defaultDays = 30


def openDatabase(preferences):
    return connectDataBase(preferences.dbDriverName,
                           preferences.dbServerName,
                           preferences.dbServerPort,
                           preferences.dbDatabaseName,
                           preferences.dbUserName,
                           preferences.dbPassword,
                           compressData=preferences.dbCompressData)


mapEquipmentIdToInterface = {}


def getEquipmentInterfaceCache(equipmentId):
    global mapEquipmentIdToInterface
    if equipmentId in mapEquipmentIdToInterface:
        return mapEquipmentIdToInterface[equipmentId]

    interface = getEquipmentInterface(equipmentId)
    mapEquipmentIdToInterface[equipmentId] = interface
    return interface


def testGetResult():
    pass
    # testFhir()


def sendTests(probeIdList, probeSaver=None):
    global globalProcessedItemList
    mapClientIdToInfo = {}


    def getClientInfoCache(clientId):
        if clientId in mapClientIdToInfo:
            return mapClientIdToInfo[clientId]
        clientInfo = getClientInfo(clientId)
        mapClientIdToInfo[clientId] = clientInfo
        return clientInfo


    def convertProbeIdListToString(idList):
        return ', '.join( str(id) for id in idList )

    try:
        bundles = bundleProbes(probeIdList)
        for bundleKey, probeIdSubList in bundles.iteritems():
            equipmentId = bundleKey.equipmentId
            equipmentInterface = getEquipmentInterfaceCache(equipmentId)

            try:
                if equipmentInterface:
                    clientInfo = getClientInfoCache(bundleKey.clientId)
                    if equipmentInterface.protocol == 1:
                        ok = sendOrdersOverASTM(None,
                                           equipmentInterface,
                                           clientInfo,
                                           probeIdSubList,
                                           probeSaver)
                    elif equipmentInterface.protocol == 3:
                        ok = sendOrdersOverFHIR050(None,
                                                   equipmentInterface,
                                                   clientInfo,
                                                   probeIdSubList,
                                                   probeSaver)
                    elif equipmentInterface.protocol == 4:
                        ok = sendOrdersOverFHIR102(None,
                                                   equipmentInterface,
                                                   clientInfo,
                                                   probeIdSubList,
                                                   probeSaver)
                    else:
                        ok = True
                    if ok:
                        log('ok',
                            'probe(s) %s successfully sended'% convertProbeIdListToString(probeIdSubList),
                            level=2)
                        globalProcessedItemList.append(probeIdSubList)
            except Exception as e:
                log('error',
                    'sending probe(s) %s failed: %s' % (convertProbeIdListToString(probeIdSubList),
                                                        anyToUnicode(e)),
                    level=1)
                globalProcessedItemList.append(probeIdSubList)
                logCurrentException()
    except Exception as e:
        log('error', 'preparing data failed: %s'%unicode(e), level=1)
        logCurrentException()


def save(item, status=None):
    global globalProcessedItemList
    item.setValue('status', QtCore.QVariant(status))
    db = QtGui.qApp.db
    id = db.updateRecord('Probe', item)
    globalProcessedItemList.append(id)


def anyToUnicode(s, encodingHint=None):
    if isinstance(s, unicode):
        return s
    if os.name == 'nt':
        encodingList = ( encodingHint,
                         locale.getpreferredencoding(), # по уставу
                         'utf8', # as fallback
                         'cp1251',
                         'cp866',
                       )
    else:
        encodingList = ( encodingHint,
                         locale.getpreferredencoding(), # по уставу
                         'utf8', # as fallback
                       )

    for encoding in encodingList:
        try:
            if encoding:
                return s.decode(encoding)
        except:
            pass
    return unicode(repr(s))


def log(title, message, stack=None, level=2):
    app = QtGui.qApp
    if level<=app.logLevel:
        try:
            if not os.path.exists(app.logDir):
                os.makedirs(app.logDir)
            dateString = unicode(QtCore.QDate().currentDate().toString(QtCore.Qt.ISODate))
            logFile = os.path.join(app.logDir, '%s.log' % dateString)
            timeString = unicode(QtCore.QDateTime().currentDateTime().toString(QtCore.Qt.SystemLocaleDate))
            logString = u'%s: %s(%s)\n' % (timeString, title, message)
            if stack:
                try:
                    logString += ''.join(traceback.format_list(stack)).decode('utf-8') + '\n'
                except:
                    logString += 'stack lost\n'
            file = codecs.open(logFile, mode='a', encoding=locale.getpreferredencoding())
            file.write(logString)
            file.close()
        except:
            pass


def logException(exceptionType, exceptionValue, exceptionTraceback):
    title = repr(exceptionType)
    #message = anyToUnicode(exceptionValue)
    message = exceptionValue
    log(title, message, traceback.extract_tb(exceptionTraceback))
    sys.__excepthook__(exceptionType, exceptionValue, exceptionTraceback)


def logCurrentException():
    logException(*sys.exc_info())


def checkGlobalPreference(code, chkValue, default=None):
    value = QtGui.qApp._globalPreferences.get(code, default)
    if value:
        return unicode(value).lower() == unicode(chkValue).lower()
    return False


def main():
    parser = OptionParser(usage="usage: %prog [options]")
    parser.add_option('-c', '--config',
                      dest='iniFile',
                      help='custom .ini file name',
                      metavar='iniFile',
                      default='/root/.config/samson-vista/autoLabExchange.ini'
                      )
    parser.add_option('-e', '--export',
                      action="store_true",
                      dest='export',
                      help='export data to configured destinations',
                      default=False
                      )
    parser.add_option('-a', '--astm',
                      action="store_true",
                      dest='importAstm',
                      help='import from astm',
                      default=False
                      )
    parser.add_option('-f', '--fhir',
                      action="store_true",
                      dest='importFhir',
                      help='import from fhir',
                      metavar='importFhir',
                      default=False
                      )
    parser.add_option('-o', '--orders',
                      action="store_true",
                      dest='importOrders',
                      help='import orders from fhir',
                      metavar='importOrders',
                      default=False
                      )
    parser.add_option('-l', '--exportLocalResults',
                      action="store_true",
                      dest='exportLocalResults',
                      help='export local results to usish',
                      metavar='exportLocalResults',
                      default=False
                      )
    parser.add_option('', '--exportODLIReferrals',
                      dest='exportODLIReferrals',
                      help='export referrals to ODLI',
                      metavar='exportODLIReferrals',
                      default=''
                      )
    parser.add_option('', '--importODLIResults',
                      dest='importODLIResults',
                      help='import results from ODLI',
                      metavar='importODLIResults',
                      default=''
                      )
    parser.add_option('-s', '--exportResults',
                      action="store_true",
                      dest='exportResults',
                      help='export results to usish',
                      metavar='exportResults',
                      default=False
                      )
    parser.add_option('-d', '--days',
                      dest='days',
                      type="int",
                      help='search probes for how much days?',
                      default='14'
                      )
    parser.add_option('-r', '--registrate',
                      action="store_true",
                      dest='registrateProbes',
                      help='registrate imported probes',
                      metavar='registrateProbes',
                      default=False
                      )
    parser.add_option('', '--registrateEquip',
                      dest='registrateProbesEquipment',
                      help='registrate imported probes',
                      metavar='registrateProbesEquipment',
                      default=None
                      )
    parser.add_option('', '--from',
                      dest='dateFrom',
                      help='beg date for probes pickup',
                      metavar='dateFrom'
                      )
    parser.add_option('', '--to',
                      dest='dateTo',
                      help='end date for probes pickup',
                      metavar='dateTo'
                      )

    (options, args) = parser.parse_args()
    parser.destroy()

    app = QtGui.QApplication(sys.argv, False)
    app.logLevel = 2
    app.userHasRight = lambda x: True
    app.font = lambda: None
    app.userSpecialityId = None
    app.showingAttach = lambda: False
    QtGui.qApp = app
    preferences = CPreferences(options.iniFile)
    iniFileName = preferences.getSettings().fileName()
    if not os.path.exists(iniFileName):
        print "ini file (%s) not exists" % iniFileName
        app.quit()
    preferences.load()
    settings = preferences.getSettings()
    settings.beginGroup('astmImportSettings')
    preferences.astmImportSettings = {}
    for prop in settings.childKeys():
        preferences.astmImportSettings[unicode(prop)] = settings.value(prop, QtCore.QVariant())
    for group in settings.childGroups():
        setPref(preferences.astmImportSettings, unicode(group), preferences.loadProp(settings, group))
    settings.endGroup()
    
    db = openDatabase(preferences)
    app.db = db
    app.userId = 1
    app.logLevel = forceInt(preferences.appPrefs.get('logLevel', 2))
    app.isAnonim = forceBool(preferences.appPrefs.get('isAnonim', 0))
    app.preferences = preferences
    app._globalPreferences = {}
    if app.db:
        try:
            recordList = app.db.getRecordList('GlobalPreferences')
        except:
            recordList = []
        for record in recordList:
            code = forceString(record.value('code'))
            value = forceString(record.value('value'))
            app._globalPreferences[code] = value

    app.checkGlobalPreference = checkGlobalPreference

    logDir = forceString(preferences.appPrefs.get('logDir', None))
    if not logDir:
        logDir = os.path.join(unicode(QtCore.QDir().toNativeSeparators(QtCore.QDir().homePath())), '.labExchange')
    app.logDir = logDir
    app.currentOrgId = lambda: forceRef(preferences.appPrefs.get('currentOrgId', None))
    app.controlSMFinance = lambda: 0
    app.currentOrgStructureId = lambda: None
    app.setJTR = lambda x: None
    app.unsetJTR = lambda x: None
    app.addJobTicketReservation = lambda x: x
    app.defaultKLADR = lambda: '2300000000000'
    app.provinceKLADR = lambda: '2300000000000'
    app.userOrgStructureId = None
    app.logCurrentException = logCurrentException
    app.practitionerOrganisationOnly = forceBool(preferences.appPrefs.get('practitionerOrganisationOnly', False))
    app.log = log
    QtGui.qApp = app
    app.webDAVInterface = None
    app.webDAVInterface = CWebDAVInterface()
    # --- url берем из настроек в БД
    url = unicode('')
    # url = forceString(preferences.appPrefs.get('WebDAVUrl', ''))
    rec_glb = app.db.getRecordEx('GlobalPreferences', 'value', 'code = \'WebDAV\'')
    if rec_glb:
        url = unicode(forceString(rec_glb.value(0)))
        url = url.replace('${dbServerName}', QtGui.qApp.preferences.dbServerName)
    # ---
    app.webDAVInterface.setWebDAVUrl(url)
    database.registerDocumentTable('Action')
    database.registerDocumentTable('ActionProperty')
    dateTo = QtCore.QDate().currentDate()
    dateFrom = dateTo.addDays(-1*defaultDays)
    if options.importFhir or options.registrateProbes or options.registrateProbesEquipment or options.importOrders:
        if options.dateTo:
            dateTo = QtCore.QDate.fromString(options.dateTo,  QtCore.Qt.ISODate)
            if not dateTo.isValid():
                log('fhir error', u'Неверно указана дата окончания: %s'%options.dateTo)
                return
            dateFrom = dateTo.addDays(-1*defaultDays)
        if options.days != defaultDays:
            try:
                dateFrom = dateTo.addDays((-1)*options.days)
            except Exception as e:
                log('fhir error',  unicode(e))
                return
        else:
            if options.dateFrom:
                dateFrom = QtCore.QDate.fromString(options.dateFrom, QtCore.Qt.ISODate)
                if not dateFrom.isValid():
                    log('import fhir',  u'Неверно указана дата начала: %s'%options.dateFrom)
                    return

    if options.export:
        log('log', 'starting export', level=3)
        export(options.days)
    if options.importAstm:
        log('log', 'starting import astm', level=3)
        importAstm()
    if options.importFhir:
        log('fhirLog', 'starting import fhir', level=3)
        importFhir(dateFrom, dateTo)
    if options.importOrders:
        log('fhirLog', 'starting import orders', level=3)
        importOrders(dateFrom, dateTo)
    if options.registrateProbes:
        registrateProbes(dateFrom, dateTo)
    if options.registrateProbesEquipment:
        registrateProbes(dateFrom, dateTo, options.registrateProbesEquipment)
    if options.exportLocalResults:
        log('log', 'starting export local results to usish', level=3)
        if QtGui.qApp.defaultKLADR()[:2] == u'23':
            exportLocalLabResultsToUsishKK()
        else:
            exportLocalLabResultsToUsish()
    if options.exportODLIReferrals:
        log('log', 'starting export referrals to ODLI', level=3)
        exportReferralsToODLI(options.exportODLIReferrals)
    if options.importODLIResults:
        log('log', 'starting import results from ODLI', level=3)
        importResultsFromODLI(options.importODLIResults)
    if options.exportResults:
        log('log', 'starting export results to usish', level=3)
        exportLabResultsToUsish()
    if app.db:
        app.db.close()
    app.quit()


def importOrders(dateFrom, dateTo):
    db = QtGui.qApp.db
    tableEquip = db.table('rbEquipment')
    equipmentIdList = db.getIdList(tableEquip, 'id', 'protocol=4 AND status=1 AND roleInIntegration=2')
    for equipmentId in equipmentIdList:
        equipmentInterface = getEquipmentInterfaceCache(equipmentId)
        importOrdersOverFhir(equipmentInterface, dateFrom, dateTo)


def importFhir(dateFrom, dateTo):
    db = QtGui.qApp.db
    tableEquip = db.table('rbEquipment')
    tableProbe = db.table('Probe')
    tableTTJ = db.table('TakenTissueJournal')
    table = tableProbe.leftJoin(tableTTJ, tableTTJ['id'].eq(tableProbe['takenTissueJournal_id']))
    equipmentIdList = db.getIdList(tableEquip, 'id', 'protocol in (3,4) AND status=1')
    for equipmentId in equipmentIdList:
        log('import fhir', u'id оборудования: %i'%equipmentId, level=2)
        cond = [ tableProbe['status'].eq(6),
#                 tableEquip['samplePreparationMode'].eq(1),
                 tableProbe['exportDatetime'].dateGe(dateFrom),
                 tableProbe['exportDatetime'].dateLe(dateTo),
                 tableProbe['equipment_id'].eq(equipmentId),
                 tableProbe['exportName'].ne(''),
                 tableTTJ['deleted'].eq(0)
               ]
        probeIdRecordList = db.getRecordList(table, 'Probe.*', where=cond, order='id')
        equipmentInterface = getEquipmentInterfaceCache(equipmentId)
        probeIdList = [forceRef(record.value('id')) for record in probeIdRecordList]
        if not probeIdList:
            log('import fhir', u'За указанный период нет проб', level=2)
            continue
        if len(probeIdList) > 20:
            log('import fhir', u'Запрос результатов по %i пробам с %s по %s'%(len(probeIdList),
                    db.formatDate(dateFrom),
                    db.formatDate(dateTo)), level=2)
        else:
            log('import fhir', u'Запрос результатов по пробам %s'%(', '.join([str(id) for id in probeIdList])), level=2)
        try:
            if equipmentInterface.protocol == 3:
                setOfPrecessedOrderIds = pickupResultsOverFHIR050(None, equipmentInterface, [], probeIdRecordList)
            elif equipmentInterface.protocol == 4:
                setOfPrecessedOrderIds = pickupResultsOverFHIR102(None, equipmentInterface, [], probeIdRecordList)
            else:
                assert False, u'invalid equipmentInterface.protocol for FHIR'
        except Exception as e:
            log('fhir error', u'%s' % anyToUnicode(e), level=1)
        else:
            cond = [tableProbe['equipment_id'].eq(equipmentId),
                tableProbe['exportName'].inlist(setOfPrecessedOrderIds),
                tableProbe['status'].eq(7)]
            receivedItemsList = db.getRecordList(tableProbe, '*', cond)
            if receivedItemsList:
                log('import fhir', u'Получены данные для %i проб'%len(receivedItemsList), level=2)
            else:
                log('import fhir', u'Сервер не вернул результатов', level=2)
    registrateProbes(dateFrom, dateTo)


def importAstm():
    mapResult2Text = {CSamplePreparationModel.importResultFullResultField:u'! ОШИБКА: Все поля результат заняты, некуда импортировать',
                     CSamplePreparationModel.importResultCannotFindProbe:u'! ОШИБКА: Не удалось идентифицировать пробу',
                     CSamplePreparationModel.importResultOk:u'Импорт прошел успешно!',
                     CSamplePreparationModel.importResultValueIsEmpty:u'Импортируемое значение не задано',
                     CSamplePreparationModel.importResultCannotFindTest: u'ОШИБКА: Тест не найден', 
                     CSamplePreparationModel.importResultExists: u'Предупреждение: повторное добавление'}
    def importAstmMessage(fileMessage, equipmentInterface):
        equipmentId = equipmentInterface.id
#        ownName = equipmentInterface.ownName
        message = CMessage()
        message.setRecords(fileMessage.body, fileMessage.encoding)
        #if message.header.receiverName == ownName:
        model = CSamplePreparationModel(None)
        model.importedItemsList = []
        model.receivedItemsList = []
        allOk = True
        log('import astm', u'Импорт результатов из %s'%fileMessage.dataFilePatch, level=1)
        for p in message.patients:
            for o in p.orders:
                for r in o.results:
                    arg = {'clientId'          : p.patientId,
                           'laboratoryPatientId'          : p.laboratoryPatientId,
                           'clientId3'         : p.reservedPatientId,
                           'externalId'        : o.specimenId,
                           'testId_like_code'  : r.testId,
                           'testCode'          : r.assayCode,
                           'testName'          : r.assayName,
                           'value'             : r.value.replace(',', '.'),
                           'referenceRange'    : r.referenceRange,
                           'abnormalFlags'     : r.abnormalFlags,
                           'unit'              : r.unit,
                           'resultStatus'      : r.status,
                           'assistantCode'     : r.operator1,
                           'personCode'        : r.operator2,
                           'rewrite'           : True,
                           'onlyFromModel'     : False,
                           'filterEquipmentId' : None,
                           'equipmentId'       : equipmentId,
                           'dataFileName'      : fileMessage.dataFilePatch,
                           'resultOnFact'      : equipmentInterface.resultOnFact,
                           'resultType'         : r.resultType,
                           'instrumentSpecimenId' : o.instrumentSpecimenId,
                           'instrumentSpecimenIndex' : o.instrumentSpecimenIndex}
                    result = model.setResult(arg)
                    if result == CSamplePreparationModel.importResultOk or result == CSamplePreparationModel.importResultExists:
                        log('import astm ok', u'%s: %s из задачи %s'%(r.testId or r.assayCode, mapResult2Text[result], fileMessage.dataFilePatch), level=2)
                        allOk = allOk and True
                    else:
                        log('import astm error', u'%s, %s: %s из задачи %s'%(r.testId or r.assayCode, r.testName, mapResult2Text[result], fileMessage.dataFilePatch), level=1)
                        allOk = False
        model.applayItemWithoutImportValue()
        if allOk:
            saveDir = equipmentInterface.opts.get('autoSaveDirOk', None)
            if saveDir:
                if os.path.exists(saveDir):
                    copyfile(fileMessage.dataFilePatch, os.path.join(saveDir, os.path.basename(fileMessage.dataFilePatch)))
                else:
                    log('import astm error', u'Директория %s не существует'%saveDir)
            fileMessage.dismiss()
        else:
            saveDir = equipmentInterface.opts.get('autoSaveDirFail', None)
            if saveDir:
                if os.path.exists(saveDir):
                    copyfile(fileMessage.dataFilePatch, os.path.join(saveDir, os.path.basename(fileMessage.dataFilePatch)))
                    fileMessage.dismiss()
                else:
                    log('import astm error', u'Директория %s не существует'%saveDir)

    def boolOpt(value):
        return value in (1, '1')
    
    if QtGui.qApp.preferences.astmImportSettings:
        opts = {}
        for key, qval in QtGui.qApp.preferences.astmImportSettings.iteritems():
            val = qval.toInt()
            opts[key] = val[0] if val[1] else forceString(qval)
        equipmentInterface = smartDict(**{"id": None,  "resultOnFact":False})
        equipmentInterface.opts = smartDict(**opts)
        fileLoop = CFileExchangeLoop(opts)
        fileLoop.setLogLevel(QtGui.qApp.logLevel)
        fileLoop.onMessageAccepted = lambda message: importAstmMessage(message,  equipmentInterface)
        fileLoop.onLog = lambda message: log('log', message, level=QtGui.qApp.logLevel)
        try:
            fileLoop._GetMessages()
        except Exception:
            #log('error', '%s'%unicode(e), 1)
            logCurrentException()
    else:
        db = QtGui.qApp.db
        tableEquip = db.table('rbEquipment')
        cond = [tableEquip['samplePreparationMode'].eq(1), tableEquip['protocol'].eq(1)]
        equipmentIdList = db.getIdList(tableEquip, 'id', where=cond)
        for equipmentId in equipmentIdList:
            equipmentInterface = getEquipmentInterfaceCache(equipmentId)
            opts = json.loads(equipmentInterface.address)
            opts['encoding'] = opts.get('encoding', 'utf-8')
            opts['inDir'] = opts.get('autoInDir', opts.get('inDir', ''))
            opts['processingId'] = opts.get('processingId', 'P')
            opts['extendedValues'] = boolOpt(opts.get('extendedValues', 0))
            opts['appendIbmIntoFileName'] = boolOpt(opts.get('appendIbmIntoFileName', 0))
            opts['uniTestId'] = boolOpt(opts.get('uniTestId', 1))
            opts['uniTestName'] = boolOpt(opts.get('uniTestName', 1))
            opts['testCode'] = boolOpt(opts.get('testCode', 1))
            equipmentInterface.opts = smartDict(**opts)
            fileLoop = CFileExchangeLoop(opts)
            fileLoop.setLogLevel(QtGui.qApp.logLevel)
            fileLoop.onMessageAccepted = lambda message: importAstmMessage(message,  equipmentInterface)
            fileLoop.onLog = lambda message: log('log', message, level=QtGui.qApp.logLevel)
            try:
                fileLoop._GetMessages()
            except Exception:
                #log('error', '%s'%unicode(e), 1)
                logCurrentException()
    registrateProbes()


def registrateProbes(dateFrom=None, dateTo=None, equipmentId=0):
    db = QtGui.qApp.db
    model = CSamplePreparationModel(None)
    model.receivedItemsList = []
    lockCache = {}
    loggedExtId = {}

    tableProbe = db.table('Probe')
    cond = [tableProbe['status'].eq(7), tableProbe['modifyDatetime'].ge('date_sub(current_date(), interval 1 month)')]
    if equipmentId:
        cond.append(tableProbe['equipment_id'].eq(equipmentId))
    if dateFrom:
        cond.append(tableProbe['importDatetime'].dateGe(dateFrom))
    if dateTo:
        cond.append(tableProbe['importDatetime'].dateLe(dateTo))
    recordList = db.getRecordList(tableProbe, '*', cond)
    if len(recordList) > 0:
        db.query('CALL getAppLock_prepare()')
    else:
        log('registrate', u'Нечего регистрировать', level=3)
    i = 0
    for item in recordList:
        externalId = forceString(item.value('externalId'))
        if externalId not in loggedExtId:
            log('registrate', u'Регистрация %s'%externalId, level=3)
            loggedExtId[externalId] = 1
        id = forceRef(item.value('id'))
        tissueJournalId = forceRef(item.value('takenTissueJournal_id'))
        lockId = lockCache.get(tissueJournalId, None)
        if lockId is None:
            tableAction = db.table('Action')
            eventIdList = db.getDistinctIdList(tableAction, tableAction['event_id'], [tableAction['takenTissueJournal_id'].eq(tissueJournalId)])
            for eventId in eventIdList:
                query = db.query('CALL getAppLock_(%s, %d, %d, %s, %s, @res)' % (quote('Event'), eventId, 0, 1, quote('autoexport')))
                query = db.query('SELECT @res')
                if query.next():
                    record = query.record()
                    s = forceString(record.value(0)).split()
                    isSuccess = False
                    if len(s)>1:
                        isSuccess = int(s[0])
                        if isSuccess:
                            lockId = int(s[1])
                            lockIdList = lockCache.setdefault(tissueJournalId, [])
                            lockIdList.append(lockId)
                        else:
                            lockCache[tissueJournalId] = False
                            externalId = forceString(item.value('externalId'))
                            log('registrate', u'Событие %i заблокировано'%eventId, level=1)
        if lockId:
            model.addRecord(item)
            model._checkedRowsList.append(i)
            model._mapIdToCheckedResults[id] = [True, 1, i]
            i += 1
    model.registrateProbe(True)
    for tjId, appLockIdList in lockCache.iteritems():
        if type(appLockIdList) is list:
            for appLockId in appLockIdList:
                db.query('CALL ReleaseAppLock(%d)' % appLockId)


def export(days=defaultDays):
    try:
        global globalProcessedItemList
        db = QtGui.qApp.db
        tableProbe = db.table('Probe')
        tableEquip = db.table('rbEquipment')
        tableTTJ = db.table('TakenTissueJournal')
        table = tableProbe.leftJoin(tableEquip, tableProbe['equipment_id'].eq(tableEquip['id']))
        table = table.leftJoin(tableTTJ, tableTTJ['id'].eq(tableProbe['takenTissueJournal_id']))
        cond = [tableProbe['status'].eq(1),
                'Probe.takenTissueJournal_id in (select takenTissueJournal_id from Probe as P where P.status=1)',
                tableEquip['samplePreparationMode'].eq(1),
                tableProbe['createDatetime'].dateGe(QtCore.QDate().currentDate().addDays(days*(-1))),
                tableTTJ['deleted'].eq(0)
                ]
        #cond.append(tableProbe['createDatetime'].dateEq(QtCore.QDate.currentDate()))
        recordList = db.getRecordList(table, 'Probe.*', where=cond, order='Probe.id')
        log('log', 'found %i ready to export probes'%len(recordList), level=3)
        idList = []
        externalIdList = {}
        for record in recordList:
            id = forceInt(record.value('id'))
            idList.append(id)
            externalIdList[id] = forceString(record.value('externalId'))
        probeSaver = CProbeSaver({'status':probeSent2LIS},
                                     recordList,
                                     save)
        sendTests(idList, probeSaver=probeSaver)
        for id in idList:
            if id not in globalProcessedItemList:
                log('warning', 'probe (%i,%s) was not processed'%(id, externalIdList[id]), level=1)
    except Exception as e:
        log('error', '%s'%unicode(e), level=1)
        logCurrentException()


def exportReferralsToODLI(numberOrder):
    u"""Выгрузка направлений в ОДЛИ"""

    def selectActionIdList(systemId, days=7, numberOrder='all'):
        db = QtGui.qApp.db
        tableAction = db.table('Action')
        tableActionType = db.table('ActionType')
        tableExport = db.table('Action_Export')
        tableEvent = db.table('Event')
        tableEventType = db.table('EventType')
        tableRbEventTypePurpose = db.table('rbEventTypePurpose')
        tableAPT = db.table('ActionPropertyType')
        tableAP = db.table('ActionProperty')
        tableAPS = db.table('ActionProperty_String')
        tableActionFileAttach = db.table('Action_FileAttach')

        table = tableAction.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
        table = table.leftJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
        table = table.leftJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
        table = table.leftJoin(tableRbEventTypePurpose, tableEventType['purpose_id'].eq(tableRbEventTypePurpose['id']))
        table = table.leftJoin(tableExport, db.joinAnd([tableExport['master_id'].eq(tableAction['id']), tableExport['system_id'].eq(systemId)]))
        table = table.leftJoin(tableAPT,
                               [tableAPT['actionType_id'].eq(tableActionType['id']), tableAPT['deleted'].eq(0),
                                tableAPT['shortName'].eq(u'directionNumber')])
        table = table.leftJoin(tableAP,
                               [tableAP['action_id'].eq(tableAction['id']), tableAP['type_id'].eq(tableAPT['id']),
                                tableAP['deleted'].eq(0)])
        table = table.leftJoin(tableAPS, tableAPS['id'].eq(tableAP['id']))
        cond = [tableActionType['deleted'].eq(0),
                tableActionType['class'].eq(1),  # диагностика
                db.joinOr([tableActionType['flatCode'].like('soc_odli%'),
                           # Для ННС необходимо наличие прикрепленной xml
                           db.joinAnd([tableActionType['code'].like('NNC'),
                                       db.existsStmt(tableActionFileAttach, [tableActionFileAttach['master_id'].eq(tableAction['id']),
                                                                             tableActionFileAttach['deleted'].eq(0),
                                                                             tableActionFileAttach['path'].like('%.sms')])])]),
                tableActionType['serviceType'].eq(10),  # лаб.исследование
                tableAction['deleted'].eq(0),
                'LENGTH(ActionProperty_String.value) > 0'  # номер направления обязателен!
                ]
        if numberOrder != 'all':
            cond.extend([tableAPS['value'].eq(numberOrder),
                         db.joinOr([tableExport['id'].isNull(),
                                    tableExport['success'].eq(0)])
                         ])
        else:
            cond.extend([tableAction['status'].eq(CActionStatus.appointed),
                         tableAction['directionDate'].ge(QDateTime().currentDateTime().addDays(-days)),
                         db.joinOr([tableExport['id'].isNull(),
                                    db.joinAnd([tableExport['success'].eq(0),
                                                tableExport['dateTime'].lt(
                                                    tableAction['modifyDatetime'])])])
                         ])
        return db.getDistinctIdList(table,
                                    tableAction['id'],
                                    db.joinAnd(cond),
                                    tableAction['id'].name()
                                    )

    db = QtGui.qApp.db
    # подготовительный этап
    systemId = forceRef(db.translate('rbExternalSystem', 'code', u'N3.ODLI', 'id'))
    # Определяем количество дней, за которые запрашивается результат, из кода в таблицу rbExchangePreferences
    export_count_days = db.translate('rbExchangePreferences', 'code', 'ODLI_export_days', 'value')
    if not export_count_days:
        export_count_days = 7
    export_count_days = forceInt(export_count_days)
    # выбрать подходящие действия, без группировки
    actionIdList = selectActionIdList(systemId, days=export_count_days, numberOrder=numberOrder)

    address = {}
    address["url"] = forceString(db.translate('GlobalPreferences', 'code', 'ODLI_URL', 'value'))
    address["authorization"] = forceString(db.translate('GlobalPreferences', 'code', 'ODLI_AUTH', 'value'))
    address['tests_urn'] = "urn:oid:1.2.643.5.1.13.13.11.1080"
    address['tests_version'] = "1"
    address['target'] = None
    address['terminology_url'] = 'http://10.0.1.179/nsi/fhir/term' #'http://r23-rc.zdrav.netrika.ru/nsi/fhir/term' #
    address['mis_oid'] = forceString(db.translate('GlobalPreferences', 'code', 'Netrika.MIS_OID', 'value'))

    equipmentInterface = smartDict(id=999,
                                   eachTestDetached=False,
                                   protocol=4,
                                   address=json.dumps(address),
                                   ownName=u'ODLI',
                                   ownCode=u'ODLI',
                                   labName=u'externalLab',
                                   labCode=u'external',
                                   specimenIdentifierMode=0,
                                   protocolVersion=4,
                                   resultOnFact=False
                                   )
    # в цикле передавать действия и отмечать как переданные
    opts = json.loads(equipmentInterface.address)
    orgId = QtGui.qApp.currentOrgId()
    interfaceObject = CFHIRExchange(opts, orgId)
    db.query('CALL getAppLock_prepare()')
    # actionIdList = [11657994]
    for actionId in actionIdList:
        try:
            interfaceObject.sendOrderWhithOutProbesOverFHIR(actionId)
        except:
            QtGui.qApp.logCurrentException()


def importResultsFromODLI(numberOrder):
    u"""Загрузка результатов из ОДЛИ"""

    def selectActionIdList(systemId, days=7, numberOrder='all'):
        db = QtGui.qApp.db
        tableAction = db.table('Action')
        tableActionType = db.table('ActionType')
        tableExport = db.table('Action_Export')
        tableEvent = db.table('Event')
        tableEventType = db.table('EventType')
        tableRbEventTypePurpose = db.table('rbEventTypePurpose')
        tableAPT = db.table('ActionPropertyType')
        tableAP = db.table('ActionProperty')
        tableAPS = db.table('ActionProperty_String')

        table = tableAction.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
        table = table.leftJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
        table = table.leftJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
        table = table.leftJoin(tableRbEventTypePurpose, tableEventType['purpose_id'].eq(tableRbEventTypePurpose['id']))
        table = table.leftJoin(tableExport, db.joinAnd(
            [tableExport['master_id'].eq(tableAction['id']), tableExport['system_id'].eq(systemId)]))
        cond = [tableActionType['deleted'].eq(0),
                tableActionType['class'].eq(1),  # диагностика
                db.joinOr([tableActionType['flatCode'].like('soc_odli%'), tableActionType['code'].like('NNC')]),
                tableActionType['serviceType'].eq(10),  # лаб.исследование
                tableAction['deleted'].eq(0),
                tableEventType['context'].notlike(u'inspection%'),
                tableEventType['context'].notlike(u'relatedAction%'),
                tableRbEventTypePurpose['code'].ne(u'0'),
                tableExport['success'].eq(1)]
        if numberOrder != 'all':
            table = table.leftJoin(tableAPT, [tableAPT['actionType_id'].eq(tableActionType['id']),
                                              tableAPT['deleted'].eq(0),
                                              tableAPT['name'].eq(u'Номер направления')])
            table = table.leftJoin(tableAP, [tableAP['action_id'].eq(tableAction['id']),
                                             tableAP['type_id'].eq(tableAPT['id']),
                                             tableAP['deleted'].eq(0)
                                             ])
            table = table.leftJoin(tableAPS, tableAPS['id'].eq(tableAP['id']))
            cond.append(tableAPS['value'].eq(numberOrder))
        else:
            cond.extend([tableAction['status'].eq(CActionStatus.wait),
                         db.joinOr([tableAction['directionDate'].ge(QDateTime().currentDateTime().addDays(-days)),
                                    db.joinAnd([tableActionType['code'].like('NNC'),
                                                tableAction['directionDate'].ge(QDateTime().currentDateTime().addDays(-30))])])
                         ])
        return db.getDistinctIdList(table,
                                    tableAction['id'],
                                    db.joinAnd(cond),
                                    tableAction['id'].name()
                                    )

    db = QtGui.qApp.db
    # подготовительный этап
    systemId = forceRef(db.translate('rbExternalSystem', 'code', u'N3.ODLI', 'id'))
    # Определяем количество дней, за которые выгружаются напрвления, из кода в таблицу rbExchangePreferences
    import_count_days = db.translate('rbExchangePreferences', 'code', 'ODLI_import_days', 'value')
    if not import_count_days:
        import_count_days = 7
    import_count_days = forceInt(import_count_days)
    # выбрать подходящие действия, без группировки
    actionIdList = selectActionIdList(systemId, days=import_count_days, numberOrder=numberOrder)

    address = {}
    address["url"] = forceString(db.translate('GlobalPreferences', 'code', 'ODLI_URL', 'value'))
    address["authorization"] = forceString(db.translate('GlobalPreferences', 'code', 'ODLI_AUTH', 'value'))
    address['tests_urn'] = "urn:oid:1.2.643.5.1.13.13.11.1080"
    address['tests_version'] = "1"
    address['target'] = None
    address['terminology_url'] = 'http://10.0.1.179/nsi/fhir/term '  # "http://r23-rc.zdrav.netrika.ru/nsi/fhir/term/"
    address['mis_oid'] = forceString(db.translate('GlobalPreferences', 'code', 'Netrika.MIS_OID', 'value'))

    equipmentInterface = smartDict(id=999,
                                   eachTestDetached=False,
                                   protocol=4,
                                   address=json.dumps(address),
                                   ownName=u'ODLI',
                                   ownCode=u'ODLI',
                                   labName=u'externalLab',
                                   labCode=u'external',
                                   specimenIdentifierMode=0,
                                   protocolVersion=4,
                                   resultOnFact=False
                                   )
    opts = json.loads(equipmentInterface.address)
    orgId = QtGui.qApp.currentOrgId()
    interfaceObject = CFHIRExchange(opts, orgId)
    for actionId in actionIdList:
        try:
            interfaceObject.getResultOverFHIR(actionId)
        except:
            QtGui.qApp.logCurrentException()

if __name__ == '__main__':
    main()
