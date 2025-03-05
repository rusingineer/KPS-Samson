# -*- coding: utf-8 -*-

from __future__ import print_function

import datetime
import logging
import os
import platform
import sys
import traceback
from logging.handlers import RotatingFileHandler
from optparse import OptionParser
# import socket

from PyQt4.QtCore import QDir, QDateTime, QDate
from PyQt4 import QtGui, QtCore

from Events.ActionStatus import CActionStatus
from Exchange.RISExchange.CHL7Client import CHl7Client
from library import database
from library.Preferences import CPreferences
from library.Utils import forceInt, toVariant, anyToUnicode


class CRISManageOrders(QtCore.QCoreApplication):
    iniFileName = '/root/.config/samson-vista/RISExchange.ini'

    def __init__(self, args):
        parser = OptionParser(usage="usage: %prog [options]")
        parser.add_option('-e', '--event', dest='idEvent', help='', metavar='idEvent', default='')
        parser.add_option('-a', '--action', dest='idAction', help='', metavar='idAction', default='')
        parser.add_option('-c', '--config', dest='iniFile', help='custom .ini file name', metavar='iniFile',
                          default=CRISManageOrders.iniFileName)
        (options, _args) = parser.parse_args()
        parser.destroy()

        QtCore.QCoreApplication.__init__(self, args)
        self.options = options
        self.logger = None
        self.db = None
        self.preferences = None
        self.mainWindow = None
        self.userHasRight = lambda x: True
        self.connectionName = 'RISExchange'
        if self.options.iniFile:
            self.iniFileName = self.options.iniFile
        elif platform.system() != 'Windows':
            self.iniFileName = '/root/.config/samson-vista/RISExchange.ini'
        else:
            self.iniFileName = 'RISExchange.ini'
        QtGui.qApp = self
        self.userId = 1
        self.font = lambda: None
        self.logLevel = 2
        if platform.system() != 'Windows':
            self.logDir = '/var/log/RISExchange'
        else:
            self.logDir = os.path.join(unicode(QDir().toNativeSeparators(QDir().homePath())), '.RISExchange')
        self.initLogger()

        self.Hl7Client = None
        self.days = 7

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
        formatter = logging.Formatter(fmt='%(asctime)s %(message)s',
                                      datefmt='%Y-%m-%d %H:%M:%S'
                                      )

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
        self.preferences = CPreferences(self.iniFileName)
        self.preferences.load()
        self.days = forceInt(self.preferences.appPrefs.get('days', 7))

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
                try:
                    self.Hl7Client = CHl7Client()
                    self.Hl7Client.initConnection()
                    self.manageOrders(actionId=self.options.idAction if self.options.idAction else None,
                                      eventId=self.options.idEvent if self.options.idEvent else None)
                except:
                    self.logCurrentException()

            self.closeDatabase()



    def manageOrders(self, eventId=None, actionId=None):
        self.createNewOrders(eventId, actionId)
        self.sendOrders(eventId, actionId)
        self.cancelOrders(eventId, actionId)
        
    def createNewOrders(self, eventId=None, actionId=None):
        db = QtGui.qApp.db
        # Исключаем из выборки ТД для локальных результатов
        tableAT = db.table('ActionType')
        tableAS = db.table('rbAccountingSystem')
        tableATI = db.table('ActionType_Identification')
        tableLR = tableAT.innerJoin(tableATI, [tableATI['master_id'].eq(tableAT['id']), tableATI['deleted'].eq(0)])
        tableLR = tableLR.innerJoin(tableAS, tableAS['id'].eq(tableATI['system_id']))
        actionTypeIdLocalResultList = db.getDistinctIdList(tableLR, idCol=[tableAT['id']], where=[tableAS['code'].eq('ODII_export')])

        tableEvent = db.table('Event')
        tableAction = db.table('Action')
        tableAP = db.table('ActionProperty')
        tableAPT = db.table('ActionPropertyType')
        tableAPDS = db.table('ActionProperty_Integer')
        tableDS = db.table('rbDiagnosticService')
        tablePacsOrder = db.table('PacsOrder')
        tableActionExport = db.table('Action_Export')
        tableExternalSystem = db.table('rbExternalSystem')

        table = tableEvent.leftJoin(tableAction, tableEvent['id'].eq(tableAction['event_id']))
        table = table.leftJoin(tableAP, tableAP['action_id'].eq(tableAction['id']))
        table = table.leftJoin(tableAPT, db.joinAnd([tableAPT['id'].eq(tableAP['type_id']),
                                                     tableAPT['shortName'].eq(u'researchKind')]))
        table = table.leftJoin(tableExternalSystem, tableExternalSystem['code'].eq(u'N3.РЕГИСЗ.ОДИИ'))
        table = table.leftJoin(tableActionExport, [tableActionExport['master_id'].eq(tableAction['id']),
                                                   tableActionExport['system_id'].eq(tableExternalSystem['id'])
                                                   ])

        table = table.innerJoin(tableAPDS, tableAPDS['id'].eq(tableAP['id']))
        table = table.innerJoin(tableDS, tableDS['id'].eq(tableAPDS['value']))
        table = table.leftJoin(tablePacsOrder, tablePacsOrder['action_id'].eq(tableAction['id']))

        cols = [
            tableEvent['id'].alias('event_id'),
            tableAction['id'].alias('action_id'),
        ]

        cond = [
            tableEvent['deleted'].eq(0),
            tableAction['deleted'].eq(0),
            tableAPT['deleted'].eq(0),
            tableAP['deleted'].eq(0),
            tableDS['deleted'].eq(0),
            tablePacsOrder['status'].isNull(),
            tableAction['actionType_id'].notInlist(actionTypeIdLocalResultList),
            tableActionExport['id'].isNull()
        ]
        if not eventId and not actionId:
            cond.append(tableAction['status'].inlist([CActionStatus.started, CActionStatus.wait, CActionStatus.appointed]))
            cond.append(tableAction['begDate'].lt(datetime.date.today() + datetime.timedelta(days=1)))
            cond.append(tableAction['begDate'].ge(datetime.datetime.now() - datetime.timedelta(days=self.days)))

        if eventId:
            cond.append(tableEvent['id'].eq(eventId))
        if actionId:
            cond.append(tableAction['id'].eq(actionId))

        records = db.getDistinctRecordList(table, cols, cond)
        for record in records:
            recPacs = tablePacsOrder.newRecord()
            recPacs.setValue('event_id', record.value('event_id'))
            recPacs.setValue('action_id', record.value('action_id'))
            recPacs.setValue('status', toVariant(0))
            db.insertRecord(tablePacsOrder, recPacs)


    def sendOrders(self, eventId=None, actionId=None):
        db = QtGui.qApp.db
        tableEvent = db.table('Event')
        tableAction = db.table('Action')
        tablePacsOrder = db.table('PacsOrder')

        table = tablePacsOrder.leftJoin(tableAction, tablePacsOrder['action_id'].eq(tableAction['id']))
        table = table.leftJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))

        cond = [
            tablePacsOrder['deleted'].eq(0),
            tablePacsOrder['status'].eq(0),
        ]
        if eventId:
            cond.append(tableEvent['id'].eq(eventId))
        if actionId:
            cond.append(tableAction['id'].eq(actionId))
            
        records = db.getDistinctRecordList(table, [tablePacsOrder['id'].alias('order_id')], cond)
        for record in records:
            self.Hl7Client.newOrder(forceInt(record.value('order_id')))


    def cancelOrders(self, eventId=None, actionId=None):
        # Обработка удаленных действий (action.deleted=1)
        db = QtGui.qApp.db
        tableEvent = db.table('Event')
        tableAction = db.table('Action')
        tableAP = db.table('ActionProperty')
        tableAPT = db.table('ActionPropertyType')
        tableAPDS = db.table('ActionProperty_Integer')
        tableDS = db.table('rbDiagnosticService')
        tablePacsOrder = db.table('PacsOrder')

        table = tableEvent.leftJoin(tableAction, tableEvent['id'].eq(tableAction['event_id']))
        table = table.leftJoin(tableAP, tableAP['action_id'].eq(tableAction['id']))
        table = table.leftJoin(tableAPT, db.joinAnd(
            [tableAPT['id'].eq(tableAP['type_id']), tableAPT['shortName'].eq(u'researchKind')]))
        table = table.innerJoin(tableAPDS, tableAPDS['id'].eq(tableAP['id']))
        table = table.innerJoin(tableDS, tableDS['id'].eq(tableAPDS['value']))
        table = table.innerJoin(tablePacsOrder, tablePacsOrder['action_id'].eq(tableAction['id']))
        colsActionId = [
            tableAction['id'].alias('action_id'),
        ]
        condActionId = []
        if eventId:
            condActionId.append(tableEvent['id'].eq(eventId))
        if actionId:
            condActionId.append(tableAction['id'].eq(actionId))

        cols = [tablePacsOrder['action_id'], tablePacsOrder['id'].alias('order_id')]
        cond = [
            tablePacsOrder['action_id'].notInlist(map(lambda x: forceInt(x.value('action_id')),
                                                      db.getRecordList(table, colsActionId, condActionId))),
            tablePacsOrder['deleted'].eq(0),
            tablePacsOrder['status'].ne(3),
        ]
        if eventId:
            cond.append(tablePacsOrder['event_id'].eq(eventId))
        if actionId:
            cond.append(tablePacsOrder['action_id'].eq(actionId))
        records = db.getDistinctRecordList(tablePacsOrder, cols, cond)

        actionIdList = []
        for record in records:
            actionIdList.append(forceInt(record.value('action_id')))
            self.Hl7Client.cancelOrder(forceInt(record.value('order_id')))

        #исторически заполняется
        for item in actionIdList:
            recHl7List = db.getRecordList(tablePacsOrder, '*', tablePacsOrder['action_id'].eq(item))
            for recHl7 in recHl7List:
                recHl7.setValue('deleted', toVariant(1))
                db.updateRecord(tablePacsOrder, recHl7)

def fmtDateShort(date):
    if isinstance(date, QDateTime):
        date = date.toPyDateTime()
    elif isinstance(date, QDate):
        date = date.toPyDate()
    return date.strftime("%Y-%m-%d")

if __name__ == '__main__':
    app = CRISManageOrders(sys.argv)
    app.main()