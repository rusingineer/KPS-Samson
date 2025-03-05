# -*- coding: utf-8 -*-
import sys
import os
import codecs
from time import localtime, strftime
from PyQt4 import QtCore, QtSql

from library import database
from library.Preferences import CPreferences
from library.Utils import forceString, forceRef, toVariant, exceptionToUnicode

from suds.client import Client, WebFault
from suds.cache import NoCache
import logging
logging.disable(logging.CRITICAL)

class CWarrantNumberUpdater(QtCore.QCoreApplication):
       
    def __init__(self, args):
        QtCore.QCoreApplication.__init__(self, args)
        self.db = None
        self.preferences = None
        self.connectionName = 'WarrantNumberUpdater'
        self.iniFileName = '/root/.config/samson-vista/WarrantNumberUpdater.ini'
        self.SOAP = None
        self.auth = None

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
            print exceptionToUnicode(e)

    def closeDatabase(self):
        if self.db:
            self.db.close()
            self.db = None
            if QtSql.QSqlDatabase.contains(self.connectionName):
                QtSql.QSqlDatabase.removeDatabase(self.connectionName)
        
    def loadPreferences(self):
        self.preferences = CPreferences(self.iniFileName)
        iniFileName = self.preferences.getSettings().fileName()
        if not os.path.exists(iniFileName):
            print u"ini file ({0:s}) not exists".format(iniFileName)
            app.quit()
        self.preferences.load()
               
    def connectService(self):
        url = forceString(self.preferences.appPrefs.get('url', None))
        user = forceString(self.preferences.appPrefs.get('user', None))
        password = forceString(self.preferences.appPrefs.get('pass', None))
        try:
            self.SOAP = Client(url, cache=NoCache())
        except Exception as e:
            print exceptionToUnicode(e)
        self.auth = self.SOAP.factory.create('authInfo')
        self.auth._userName = user
        self.auth._pass = password
        
    def main(self):
        print u'====start {0:s}==='.format(self.currentTime())
        self.loadPreferences()
        if self.preferences:
            self.openDatabase()
            if self.db:
                self.connectService()
                if self.SOAP:
                    self.downloadWarrantNumbers()
        self.closeDatabase()
        print u'====end {0:s}==='.format(self.currentTime())

    def getActionTypeAndPropType(self):
        """Выбираем тип действия и тип свойства направления"""
        stmt = u"""SELECT apt.id as propTypeId, apt2.id as propTypeId2, at.id as actionTypeId
        FROM ActionType at
        LEFT JOIN ActionPropertyType apt on apt.actionType_id = at.id and apt.deleted = 0 AND apt.name = 'Внутренний номер направления'
        LEFT JOIN ActionPropertyType apt2 on apt2.actionType_id = at.id and apt2.deleted = 0 AND apt2.name = 'warrantNum'
        WHERE at.code = 'soc001' AND at.name LIKE 'Направление СОЦ-Лаборатория'
            AND at.deleted = 0 AND showInForm = 1 AND apt.id is not null"""
        query = self.db.query(stmt)
        if query.next():
            record = query.record()
            return forceRef(record.value('actionTypeId')), forceRef(record.value('propTypeId')), forceRef(record.value('propTypeId2'))
        return None, None, None
        
    def getData(self, actionType, propType, propType2):
        stmt = u"""
SELECT 
  apNumber.id AS apNumber,
  apInternalNumber.id AS apInternalNumber,
  CONCAT_WS(':', 'web', o.infisCode, InternalNumber.value) as InternalNumber,
  a.id as actionId
  FROM Action a
  left JOIN Event e on e.id = a.event_id
  left JOIN Person p ON p.id = e.execPerson_id
  LEFT JOIN Organisation o ON o.id = p.org_id
  left JOIN ActionType at on at.id = a.actionType_id
  left JOIN ActionProperty apNumber ON apNumber.action_id = a.id AND apNumber.type_id = {propType2} AND apNumber.deleted = 0
  left JOIN ActionProperty apInternalNumber ON apInternalNumber.action_id = a.id AND apInternalNumber.type_id = {propType} AND apInternalNumber.deleted = 0
  left JOIN ActionProperty_String Number ON Number.id = apNumber.id
  left JOIN ActionProperty_String InternalNumber ON InternalNumber.id = apInternalNumber.id
  WHERE a.actionType_id = {actionType} AND a.begDate >= SUBDATE(NOW(),INTERVAL 30 DAY) AND a.status <> 2 AND a.deleted = 0
  AND LENGTH(IFNULL(Number.value, '')) = 0
""".format(actionType=actionType, propType=propType, propType2=propType2)
        return self.db.query(stmt)
        
    def fillActionProperty(self, id, typeId, table, actionId, value):
        db = self.db
        if id:
            item = db.getRecordEx(table, '*', table['id'].eq(id))
            item.setValue('value', toVariant(value))
            db.updateRecord(table, item)
        else:
            mainItem = self.tableActionProperty.newRecord()
            item = table.newRecord()
            mainItem.setValue('action_id', toVariant(actionId))
            mainItem.setValue('type_id', toVariant(typeId))
            id = db.insertRecord(self.tableActionProperty, mainItem)
            item.setValue('id', toVariant(id))
            item.setValue('value', toVariant(value))
            db.insertRecord(table, item)

    def downloadWarrantNumbers(self):
        actionType, propType, propType2 = self.getActionTypeAndPropType()
        query = self.getData(actionType, propType, propType2)
        print 'count warrants: {0:d}'.format(query.size())
        if query.size() > 0:
            db = self.db
            cntWarrantNumberUpdates = 0
            cntErrors = 0
            self.tableActionProperty = db.table(u'ActionProperty')
            tableActionProperty_String = db.table('ActionProperty_String')
            print u'{0:s}: start exchange'.format(self.currentTime())
            while query.next():
                record = query.record()
                actionId = forceRef(record.value('actionId'))
                requestTime = None
                try:
                    InternalNumber = forceString(record.value('InternalNumber'))
                    if InternalNumber:
                        requestTime = self.currentTime()
                        res = self.SOAP.service.getWarrantByIdMIS(self.auth, InternalNumber)
                        if res:
                            cntWarrantNumberUpdates += 1
                            apNumber = forceRef(record.value('apNumber'))
                            self.fillActionProperty(apNumber, propType2, tableActionProperty_String, actionId, forceString(res))
                except WebFault as e:
                    cntErrors += 1
                    print exceptionToUnicode(e)
                    print u'{0:s}: request'.format(requestTime)
                    if hasattr(self.SOAP, 'last_sent'):
                        print unicode(self.SOAP.last_sent())
                    else:
                        print u'Action.id: {0:d}, internalNumber: {1}'.format(actionId, InternalNumber)
                    print u'{0:s}: error'.format(self.currentTime())
                except Exception as e:
                    cntErrors += 1
                    print exceptionToUnicode(e)
            print u'Warrant Number Updates: {0:d}'.format(cntWarrantNumberUpdates)
            print u'Warrant Number Errors: {0:d}'.format(cntErrors)
            print u'{0:s}: exchange completed'.format(self.currentTime())
    
    def currentTime(self):
        return strftime("%Y-%m-%d %H:%M:%S", localtime())


if __name__ == '__main__':
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout)
    app = CWarrantNumberUpdater(sys.argv)
    app.main()
