#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import os
import sys
import traceback

from logging.handlers import RotatingFileHandler

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import QDir, QByteArray, QTime

from library import database
from library.Utils import anyToUnicode, forceString, forceRef


class CFileAttachCompress(QtCore.QCoreApplication):
    u""" Параметры IP_сервера, порт, имя_БД, имя_пользователя, пароль
         например: 10.2.94.17 3306 s11_23001 dbuser xxxxxxxx
    """
    def __init__(self, args):
        QtCore.QCoreApplication.__init__(self, args)
        self.db = None
        self.mainWindow = None
        self.userHasRight = lambda x: True
        self.userSpecialityId = None
        self.connectionName = 'FileAttachCompress'
        self.logLevel = 2
        if len(args) == 6:
            self.dbDriverName = 'mysql'
            self.dbServerName, self.dbServerPort, self.dbDatabaseName, self.dbUserName, self.dbPassword = args[1:6]
            self.dbServerPort = int(self.dbServerPort)
        else:
            return
        QtGui.qApp = self
        self.userId = 1
        self.font = lambda: None
        self.logLevel = 2
        self.logDir = os.path.join(unicode(QDir.toNativeSeparators(QDir.homePath())), '.samson-vista')
        self.initLogger()

    def openDatabase(self):
        self.db = None
        try:
            self.db = database.connectDataBase(self.dbDriverName,
                                               self.dbServerName,
                                               self.dbServerPort,
                                               self.dbDatabaseName,
                                               self.dbUserName,
                                               self.dbPassword,
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
        return os.path.join(QtGui.qApp.logDir, 'FileAttachCompress.log')

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
        self.initLogger()
        self.openDatabase()
        if self.db:
            import zlib
            offset = 0
            cnt = 1
            while cnt > 0:
                time = QTime.currentTime()
                if not (time > QTime(20, 0) or time < QTime(2, 0)):
                    break
                table = self.db.table('Action_FileAttach_PrintTemplate')
                table2 = self.db.table('Action_FileAttach')
                stmt = u"SELECT id, html FROM Action_FileAttach WHERE id between {0} and {1}".format(offset, offset+1000)
                query = self.db.query(stmt)
                offset += 1000
                cnt = query.size()
                idlist = []
                recordList = []
                try:
                    while query.next():
                        record = query.record()
                        _id = forceRef(record.value('id'))
                        value = forceString(record.value('html')).encode('utf8')
                        if value:
                            compData = zlib.compress(value)
                            compRecord = table.newRecord()
                            compRecord.setValue('id', _id)
                            compRecord.setValue('html', QByteArray(compData))
                            recordList.append(compRecord)
                            idlist.append(_id)
                            if len(recordList) == 100:
                                self.db.insertRecordList(table, recordList)
                                recordList = []
                    if recordList:
                        self.db.insertRecordList(table, recordList)
                except Exception as e:
                    self.log('error', anyToUnicode(e), 2)
                if idlist:
                    stmt2 = u"UPDATE Action_FileAttach SET html = NULL WHERE {0}".format(table2['id'].inlist(idlist))
                    self.db.query(stmt2)
        self.closeDatabase()


if __name__ == '__main__':
    app = CFileAttachCompress(sys.argv)
    app.main()
