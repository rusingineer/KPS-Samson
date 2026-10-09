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

from PyQt4.QtCore import QDir, QDateTime, QDate
from PyQt4 import QtGui, QtCore

from Events.ActionStatus import CActionStatus
from Exchange.RISExchange.CHL7Client import CGRPCClient, CMllpClient
from library import database
from library.Preferences import CPreferences
from library.Utils import forceInt, toVariant, anyToUnicode, forceString


class CRISManageOrders(QtCore.QCoreApplication):
    _RIS_ORDER_CODES = ['XO', 'OC', 'SP/IP', 'RE', 'SC', 'IP']

    iniFileName = '/root/.config/samson-vista/RISExchange.ini'
    def __init__(self, args):
        parser = OptionParser(usage="usage: %prog [options]")
        parser.add_option('-e', '--event', dest='idEvent', help='', metavar='idEvent', default='')
        parser.add_option('-a', '--action', dest='idAction', help='', metavar='idAction', default='')
        parser.add_option('-m', '--reload-message', dest='idMessage', help='', metavar='idMessage', default='')
        parser.add_option('-c', '--config', dest='iniFile', help='custom .ini file name', metavar='iniFile',
                          default=CRISManageOrders.iniFileName)
        parser.add_option('--SQL', dest='logSql', help='log sql queries', action='store_true', default=False)
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
        self.logSql = self.options.logSql
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

        self.days = 7
        self.reloadLimit = 50
        self.sendLimit = 50

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
                                               connectionName=self.connectionName,
                                               logger=logging.getLogger('DB') if self.logSql else None)
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
        QtGui.qApp.log(u'Путь к файлу конфигурации', self.iniFileName, level=1)
        self.preferences = CPreferences(self.iniFileName)
        self.preferences.load()
        self.days = forceInt(self.preferences.appPrefs.get('days', 7))
        self.reloadLimit = forceInt(self.preferences.appPrefs.get('reloadLimit', 50))
        self.sendLimit = forceInt(self.preferences.appPrefs.get('sendLimit', 50))
        self.logLevel = forceInt(self.preferences.appPrefs.get('logLevel', 2))

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
                    self.grpcClient = CGRPCClient()
                    self.grpcClient.initConnection()
                    self.mllpClient = CMllpClient()
                    self.manageOrders(actionId=self.options.idAction if self.options.idAction else None,
                                      eventId=self.options.idEvent if self.options.idEvent else None,
                                      messageId=self.options.idMessage if self.options.idMessage else None)
                except:
                    self.logCurrentException()
            self.closeDatabase()



    def manageOrders(self, eventId=None, actionId=None, messageId=None):
        if eventId or actionId or messageId:
            self.log(u'Ключи запуска',
                     u'Event.id=%s, Action.id=%s, PacsMessages.id=%s' % (eventId, actionId, messageId), 2)
        if messageId:
            self.sendMessage(messageId)
        else:
            self.createNewOrders(eventId, actionId)
            self.sendOrders(eventId, actionId)
            self.cancelOrders(eventId, actionId)
            self.reloadMessages(eventId, actionId)
        
    def createNewOrders(self, eventId=None, actionId=None):
        db = QtGui.qApp.db
        # Исключаем из выборки ТД для локальных результатов
        tableAT = db.table('ActionType')
        tableAS = db.table('rbAccountingSystem')
        tableATI = db.table('ActionType_Identification')
        tableLR = tableAT.innerJoin(tableATI, [tableATI['master_id'].eq(tableAT['id']), tableATI['deleted'].eq(0)])
        tableLR = tableLR.innerJoin(tableAS, tableAS['id'].eq(tableATI['system_id']))
        actionTypeIdLocalResultList = db.getDistinctIdList(tableLR, idCol=[tableAT['id']], where=[tableAS['code'].eq('ODII_export')])

        tableAPT = db.table('ActionPropertyType')
        actionTypeIIList = db.getDistinctIdList(tableAT.innerJoin(tableAPT, [tableAPT['actionType_id'].eq(tableAT['id'])]),
                                                            idCol=[tableAT['id']],
                                                            where=[tableAPT['shortName'].eq('researchKind'),
                                                                   tableAPT['deleted'].eq(0),
                                                                   tableAT['id'].notInlist(actionTypeIdLocalResultList),
                                                                   tableAT['flatCode'].eq('hl7_ris')
                                                                   ]
                                                )

        tableEvent = db.table('Event')
        tableAction = db.table('Action')
        tableAP = db.table('ActionProperty')
        tableAPDS = db.table('ActionProperty_Integer')
        tableDS = db.table('rbDiagnosticService')
        tablePacsOrder = db.table('PacsOrder')
        tableActionExport = db.table('Action_Export')
        tableExternalSystem = db.table('rbExternalSystem')

        table = tableAction.leftJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))
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

        cond = [
            tableEvent['deleted'].eq(0),
            tableAction['deleted'].eq(0),
            tableAPT['deleted'].eq(0),
            tableAP['deleted'].eq(0),
            tableDS['deleted'].eq(0),
            tablePacsOrder['status'].isNull(),
            tableAction['actionType_id'].inlist(actionTypeIIList),
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

        # обход Using temporary, возникающее из-за distinct. Инцедент с ГБ Анапа
        actionIdList = db.getIdList(table, [tableAction['id']], cond)
        cols = [
            tableAction['event_id'].alias('event_id'),
            tableAction['id'].alias('action_id'),
        ]
        records = db.getRecordList(tableAction, cols, where=[tableAction['id'].inlist(actionIdList)])

        self.log(u'Поиск исследований для создания новых заказов', u'Найдено записей %d' % len(records), 2)
        for record in records:
            recPacs = tablePacsOrder.newRecord()
            recPacs.setValue('event_id', record.value('event_id'))
            recPacs.setValue('action_id', record.value('action_id'))
            recPacs.setValue('status', toVariant(0))
            id = db.insertRecord(tablePacsOrder, recPacs)
            if id:
                self.log(u'     В таблицу PacsOrder добавлен новый заказ', u'PacsOrder.id=%d Action.id=%d Event.id=%d' % (
                id, forceInt(recPacs.value('action_id')), forceInt(recPacs.value('event_id'))), 2)
            else:
                self.log(u'     Не удалось добавить новый заказ', u'Action.id=%d Event.id=%d' % (
                    forceInt(recPacs.value('action_id')), forceInt(recPacs.value('event_id'))), 2)

    def sendOrders(self, eventId=None, actionId=None):
        db = QtGui.qApp.db
        tableEvent = db.table('Event')
        tableAction = db.table('Action')
        tablePacsOrder = db.table('PacsOrder')

        table = tablePacsOrder.innerJoin(tableAction, tablePacsOrder['action_id'].eq(tableAction['id']))
        table = table.innerJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))

        cond = [
            tablePacsOrder['deleted'].eq(0),
            tablePacsOrder['status'].eq(0),
            tablePacsOrder['event_id'].isNotNull(),
        ]
        if eventId:
            cond.append(tableEvent['id'].eq(eventId))
        if actionId:
            cond.append(tableAction['id'].eq(actionId))

        records = db.getRecordList(table, [tablePacsOrder['id'].alias('order_id'), tablePacsOrder['action_id'],
                                                   tablePacsOrder['event_id']], cond, limit=self.sendLimit)
        self.log(u'Поиск новых заказов для отправки в РИС', u'Найдено записей %d' % len(records), 2)
        for record in records:
            self.grpcClient.newOrder(forceInt(record.value('order_id')))
            self.log(u'     Заказ отправлен в сервис hl7server (orderCode=NW)', u'Заказ PacsOrder.id=%d Action.id=%d Event.id=%d' % (
            forceInt(record.value('order_id')), forceInt(record.value('action_id')),
            forceInt(record.value('event_id'))), 2)


    def cancelOrders(self, eventId=None, actionId=None):
        # Обработка удаленных действий (action.deleted=1 or action.status==ActionStatus.cancelled)
        db = QtGui.qApp.db
        tableAction = db.table('Action')
        tablePacsOrder = db.table('PacsOrder')
        table = tablePacsOrder.innerJoin(tableAction, tableAction['id'].eq(tablePacsOrder['action_id']))

        cols = [tablePacsOrder['action_id'], tablePacsOrder['id'].alias('order_id'), tablePacsOrder['event_id']]
        cond = [
            tablePacsOrder['deleted'].eq(0),
            tablePacsOrder['status'].eq(1),
            db.joinOr([tableAction['status'].eq(CActionStatus.canceled), tableAction['deleted'].ne(0)]),
            tablePacsOrder['event_id'].isNotNull(),
        ]
        if eventId:
            cond.append(tablePacsOrder['event_id'].eq(eventId))
        if actionId:
            cond.append(tablePacsOrder['action_id'].eq(actionId))
        records = db.getRecordList(table, cols, cond)
        self.log(u'Поиск удаленных (отмененных) заказов для отправки в РИС', u'Найдено записей %d' % len(records), 2)
        for record in records:
            self.grpcClient.cancelOrder(forceInt(record.value('order_id')))
            self.log(u'     Заказ отправлен в сервис hl7server (orderCode=CA)',  u'Заказ PacsOrder.id=%d Action.id=%d Event.id=%d' % (
                forceInt(record.value('order_id')), forceInt(record.value('action_id')),
                forceInt(record.value('event_id'))), 2)

    def reloadMessages(self, eventId=None, actionId=None):
        db = QtGui.qApp.db
        tableMessages = db.table('PacsMessages')
        tablePacsOrder = db.table('PacsOrder')
        tableMessagesInner = db.table('PacsMessages').alias('PacsMessagesInner')

        table = tableMessages.innerJoin(tablePacsOrder, tablePacsOrder['id'].eq(tableMessages['pacsOrder_id']))

        cond = [
            tablePacsOrder['deleted'].eq(0),
            tableMessages['deleted'].eq(0),
            tableMessages['loaded'].eq(0),
            # инцидент ГБ1 Сочи. Запросом удалены ивенты.
            tablePacsOrder['event_id'].isNotNull(),
        ]
        innerCond = tableMessages['id'].eqEx(
            '(%s)' % db.selectStmt(tableMessagesInner, 'MAX(%s)' % tableMessagesInner['id'].name(),
                                   [tableMessagesInner['pacsOrder_id'].eqEx(tableMessages['pacsOrder_id'].name()),
                                    tableMessagesInner['deleted'].eq(0)]))
        cond.append(innerCond)
        if eventId:
            cond.append(tablePacsOrder['event_id'].eq(eventId))
        if actionId:
            cond.append(tablePacsOrder['action_id'].eq(actionId))

        cols = [
            tableMessages['id'].alias('message_id'),
            tableMessages['orderCode'],
            tablePacsOrder['id'].alias('order_id'),
            tablePacsOrder['action_id'],
            tablePacsOrder['event_id'],
        ]

        records = db.getRecordList(table, cols, cond, limit=self.reloadLimit)
        self.log(u'Поиск сообщений РИС, требующих повторной загрузки', u'Найдено записей %d' % len(records), 2)
        for record in records:
            self.sendMessage(forceInt(record.value('message_id')))
            self.log(u'     ', u'Сообщение PacsMessages.id = %d (orderCode=%s) Заказ PacsOrder.id=%d Action.id=%d Event.id=%d' % (
                forceRef(record.value('message_id')), forceString(record.value('orderCode')),
                forceRef(record.value('order_id')), forceRef(record.value('action_id')),
                forceRef(record.value('event_id'))), 2)

    def sendMessage(self, idMessage):
        tmpStr = u'Сообщение не найдено'
        tableMessages = QtGui.qApp.db.table('PacsMessages')

        rec = QtGui.qApp.db.getRecordEx(tableMessages, [tableMessages['orderCode'], tableMessages['request']],
                                      tableMessages['id'].eq(idMessage))
        if rec and forceString(rec.value('orderCode') in CRISManageOrders._RIS_ORDER_CODES):
            msg = forceString(rec.value('request'))
            if msg:
                self.mllpClient.sendMessage(msg)
                tmpStr = u'Сообщение отправлено в сервис hl7server'
        self.log(u'     Поиск сообщения PacsMessages.id=%s' % idMessage, tmpStr, 2)

def fmtDateShort(date):
    if isinstance(date, QDateTime):
        date = date.toPyDateTime()
    elif isinstance(date, QDate):
        date = date.toPyDate()
    return date.strftime("%Y-%m-%d")

if __name__ == '__main__':
    app = CRISManageOrders(sys.argv)
    app.main()