# -*- coding: utf-8 -*-
import sys
import os
from time import gmtime, strftime
from PyQt4 import QtCore, QtSql, QtGui

from Events.Action import CAction
from Events.ActionStatus import CActionStatus
from Registry.Utils import CClientInfo
from library import database
from library.Preferences import CPreferences
from library.PrintInfo import CInfoContext
from library.Utils import forceString, forceInt, forceRef, toVariant, anyToUnicode, quote

from suds.client import Client, WebFault
import logging
logging.basicConfig(level=logging.INFO)


class CHolterExchanger(QtCore.QCoreApplication):
    
    mapStatusCodeToName = {0: u'Заявка без вложений',
                           1: u'Заявка подана',
                           2: u'Заявка взята в работу',
                           3: u'Заявка выполнена',
                           4: u'Заявка аннулирована'}
    
    def __init__(self, args):
        QtCore.QCoreApplication.__init__(self, args)
        self.db = None
        self.preferences = None
        QtGui.qApp = self
        self.font = lambda: None
        self.userId = 1
        self.connectionName = 'HolterDB'
        self.iniFileName = '/root/.config/samson-vista/HolterExchanger.ini'
        self.SOAP = None
        self.auth = None
        self._orgStructBookkeeperCodeCache = {}

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
            print(anyToUnicode(e))

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
            print(u"ini file ({0:s}) not exists".format(iniFileName))
            app.quit()
        self.preferences.load()

    def connectService(self):
        url = forceString(self.preferences.appPrefs.get('url', None))
        user = forceString(self.preferences.appPrefs.get('user', None))
        password = forceString(self.preferences.appPrefs.get('pass', None))
        try:
            self.SOAP = Client(url, timeout=180)
        except WebFault as e:
            print anyToUnicode(e)
        except Exception as e:
            print(anyToUnicode(e))
        self.auth = self.SOAP.factory.create('authInfo')
        self.auth._userName = user
        self.auth._pass = password

    def createRequestInfo(self, record, begDate):
        clientId = forceRef(record.value('clientId'))
        orgStructId = forceRef(record.value('orgStructId'))
        context = CInfoContext()
        client = context.getInstance(CClientInfo, clientId)
        requestInfo = self.SOAP.factory.create('requestInfo')
        requestInfo.datR = client.birthDate.date.toString('yyyy-MM-dd')
        requestInfo.omsCode = self.getOrgStructureBookkeeperCode(orgStructId)
        requestInfo.fam = client.lastName
        requestInfo.im = client.firstName
        requestInfo.otch = client.patrName
        requestInfo.pol = client.sex
        if client.document and client.document.documentTypeRegionalCode in ['3', '9', '13', '14']:
            requestInfo.docTypeId = client.document.documentTypeRegionalCode
            requestInfo.pS = client.document.serial
            requestInfo.pN = client.document.number
        requestInfo.snils = client.SNILS
        if client.compulsoryPolicy and client.compulsoryPolicy.number:
            if client.compulsoryPolicy.kind:
                requestInfo.polisTypeId = client.compulsoryPolicy.kind.regionalCode
            if client.compulsoryPolicy.serial:
                requestInfo.polisS = client.compulsoryPolicy.serial
            requestInfo.polisN = client.compulsoryPolicy.number
        requestInfo.dInput = begDate.toString('yyyy-MM-dd')
        requestInfo.prRab = 0
        requestInfo.registrId = clientId
        return requestInfo

    def main(self):
        self.loadPreferences()
        if self.preferences:
            self.openDatabase()
            if self.db:
                self.connectService()
                if self.SOAP:
                    self.uploadRequests()
        self.closeDatabase()

    def getData(self):
        stmt = u"""
SELECT a.id AS actionId, e.id AS eventId, c.id AS clientId, p.orgStructure_id AS orgStructId
FROM Action a
LEFT JOIN ActionType at ON at.id = a.actionType_id
LEFT JOIN Event e ON e.id = a.event_id
LEFT JOIN Person p ON p.id = COALESCE(a.person_id, a.setPerson_id, e.execPerson_id)
LEFT JOIN Client c ON c.id = e.client_id
WHERE at.flatCode = 'holter' AND a.deleted = 0 AND at.deleted = 0 
    AND a.status IN (0,1,5)
    AND c.SNILS <> ''
    AND a.begDate >= CURDATE() - INTERVAL 90 DAY;
"""
        return self.db.query(stmt)
        
    def uploadRequests(self):
        query = self.getData()
        print('count requests: {0:d}'.format(query.size()))
        if query.size() > 0:
            cntNewRequests = 0
            cntNoChange = 0
            cntUpdateStatus = 0
            cntResults = 0
            print(u'{0:s}: start exchange'.format(strftime("%Y-%m-%d %H:%M:%S", gmtime())))
            self.db.query('CALL getAppLock_prepare()')
            while query.next():
                record = query.record()
                lockId = None
                actionId = forceRef(record.value('actionId'))
                eventId = forceRef(record.value('eventId'))
                try:
                    self.db.query('CALL getAppLock_(%s, %d, %d, %s, %s, @res)' % (quote('Event'), eventId, 0, 1, quote('HolterExchanger')))
                    lockQuery = self.db.query('SELECT @res')
                    if lockQuery.next():
                        lockRecord = lockQuery.record()
                        s = forceString(lockRecord.value(0)).split()
                        if len(s) > 1:
                            isSuccess = int(s[0])
                            if isSuccess:
                                lockId = int(s[1])
                            else:
                                print(u'{0:s}: Событие {1} заблокировано'.format(strftime("%Y-%m-%d %H:%M:%S", gmtime()), eventId))
                                self.log(u'Выгрузка направления', u'Событие %i заблокировано' % eventId, level=1)
                    if lockId:
                        action = CAction(record=self.db.getRecord('Action', '*', actionId))
                        prop = action.getProperty(u'Номер заявки')
                        if prop:
                            Number = forceInt(prop.getValue())
                            if Number:
                                # если уже есть номер заявки, то запрашиваем ее статус
                                res = self.SOAP.service.getRequestsCustomer(self.auth, Number)
                                if res:
                                    prop = action.getProperty(u'Статус заявки')
                                    oldStatus = ''
                                    if prop:
                                        oldStatus = forceString(prop.getValue())
                                    status = self.mapStatusCodeToName[res[0].status]
                                    # если статус изменился
                                    if status != oldStatus or status == u'Заявка аннулирована':
                                        prop.setValue(status)
                                        if 'executive' in res[0]:
                                            executive = unicode(res[0].executive)
                                            prop = action.getProperty(u'Исполнитель')
                                            if prop:
                                                prop.setValue(executive)
                                        if res[0].status == 3:
                                            # если статус заявки 'Заявка выполнена' - то склеиваем урл к пдф результата
                                            cntResults += 1
                                            param = u'mis?user={0:s}&pass={1:s}&request={2:d}'.format(self.auth._userName, self.auth._pass, Number)
                                            url = forceString(self.preferences.appPrefs.get('url', ''))
                                            result = url.replace(u'soap?wsdl', param)
                                            prop = action.getProperty(u'Результат заявки')
                                            if prop:
                                                prop.setValue(result)

                                            curDateTime = strftime("%Y-%m-%d %H:%M:%S", gmtime())
                                            action.getRecord().setValue('status', toVariant(CActionStatus.finished))
                                            action.getRecord().setValue('endDate', toVariant(curDateTime))
                                            action.save(idx=-1)
                                        else:
                                            # иначе обновляем статус заявки
                                            cntUpdateStatus += 1

                                            if res[0].status == 2:
                                                action.getRecord().setValue('status', toVariant(CActionStatus.wait))
                                                action.save(idx=-1)
                                            elif res[0].status == 4:
                                                action.getRecord().setValue('status', toVariant(CActionStatus.canceled))
                                                action.save(idx=-1)
                                    else:
                                        cntNoChange += 1
                            else:
                                # номера заявки нет - создаем заявку
                                res = self.SOAP.service.createRequest(self.auth, self.createRequestInfo(record, action.getBegDate()))
                                if res:
                                    cntNewRequests += 1
                                    prop.setValue(res)

                                    prop = action.getProperty(u'Статус заявки')
                                    if prop:
                                        prop.setValue(self.mapStatusCodeToName[0])
                                    action.save(idx=-1)
                except WebFault as e:
                    print anyToUnicode(e)
                except Exception as e:
                    print(anyToUnicode(e))
                finally:
                    if lockId:
                        self.db.query('CALL ReleaseAppLock(%d)' % lockId)
            print(u'created: {0:d}\nupdated: {1:d}\ncompleted: {2:d}\nwithout changes: {3:d}'.format(
                 cntNewRequests, cntUpdateStatus, cntResults, cntNoChange))
            print(u'{0:s}: exchange completed'.format(strftime("%Y-%m-%d %H:%M:%S", gmtime())))

    def getOrgStructureBookkeeperCode(self, _id):
        u"""Получает код для бухгалтерии по id отделения"""
        result = self._orgStructBookkeeperCodeCache.get(_id, -1)

        if result == -1:
            stmt = u"""select IF(length(trim(os.bookkeeperCode))=5, os.bookkeeperCode,
                        IF(length(trim(destParent1.bookkeeperCode))=5, destParent1.bookkeeperCode,
                          IF(length(trim(destParent2.bookkeeperCode))=5, destParent2.bookkeeperCode,
                            IF(length(trim(destParent3.bookkeeperCode))=5, destParent3.bookkeeperCode,
                              IF(length(trim(destParent4.bookkeeperCode))=5, destParent4.bookkeeperCode, destParent5.bookkeeperCode)))))
                        FROM OrgStructure as os
                        left join OrgStructure as destParent1 on destParent1.id = os.parent_id
                        left join OrgStructure as destParent2 on destParent2.id = destParent1.parent_id
                        left join OrgStructure as destParent3 on destParent3.id = destParent2.parent_id
                        left join OrgStructure as destParent4 on destParent4.id = destParent3.parent_id
                        left join OrgStructure as destParent5 on destParent5.id = destParent4.parent_id
                        where os.id = {0}""".format(_id)
            query = self.db.query(stmt)
            if query.first():
                record = query.record()
                if record:
                    result = record.value(0)
            self._orgStructBookkeeperCodeCache[_id] = result
        return forceString(result)


if __name__ == '__main__':
    app = CHolterExchanger(sys.argv)
    app.main()
