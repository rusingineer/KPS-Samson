# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2026 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import QDate, QVariant, SIGNAL, QDateTime, pyqtSignature

from library.AgeSelector import checkAgeSelector, parseAgeSelector
from library.Utils import calcAgeTuple, forceDate, forceInt, forceRef, forceString, formatDateTime

from Ui_CreateAttachClientsForAreaDialog import Ui_CreateAttachClientsForAreaDialog


class CCreateAttachClientsForAreaDialog(QtGui.QDialog, Ui_CreateAttachClientsForAreaDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.patientRequired = False
        self.setupUi(self)
        self.cmbOrgStructure.setOrgId(QtGui.qApp.currentOrgId())
        self.cmbOrgStructure.setValue(QtGui.qApp.currentOrgStructureId())
        self.cmbDeAttachType.setTable('rbDeAttachType', addNone=False)

        self.btnRun = QtGui.QPushButton(u'Начать', self)
        self.btnPauseOrStop = QtGui.QPushButton(u'Приостановить', self)

        self.btnPauseOrStop.setEnabled(False)

        self.btnClose = self.buttonBox.button(QtGui.QDialogButtonBox.Close)

        self.buttonBox.addButton(self.btnRun, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnPauseOrStop, QtGui.QDialogButtonBox.ActionRole)

        self._stoped = True
        self._run = False
        self._currentClientId = None

        self.connect(self.btnRun, SIGNAL('clicked()'), self.on_btnRun)
        self.connect(self.btnPauseOrStop, SIGNAL('clicked()'), self.on_btnPauseOrStop)

        self.progressBar.reset()
        self.progressBar.setText(u'')
        self.progressBar.setValue(0)

        self._currentClientIdx = 0
        self.mapHouseId2Info = {}
        self.clientIdList = []
        self.orgStructureIdList = []
        self.rbNet = self.cacheRbNet()
        self.cmbDeAttachType.setEnabled(self.chkUpdateData.isChecked())
        self.edtDate.setEnabled(self.chkUpdateData.isChecked())
        self.on_edtDate_dateChanged(self.edtDate.date())


    def cacheRbNet(self):
        result = {}
        db = QtGui.qApp.db
        recordList = db.getRecordList(db.table('rbNet'))
        for record in recordList:
            id = forceInt(record.value('id'))
            code = forceString(record.value('code'))
            result[id] = code
        return result


    def stop(self):
        self._stoped = True
        self._run = False


    def on_btnRun(self):
        if self.chkUpdateData.isChecked():
            if self.cmbDeAttachType.value() is None:
                QtGui.QMessageBox.warning(self,
                                           u'Внимание',
                                           u'Необходимо выбрать причину открепления!',
                                           QtGui.QMessageBox.Ok,
                                           QtGui.QMessageBox.Ok)
                return
            if not self.edtDate.date().isValid() or self.edtDate.date().isNull():
                QtGui.QMessageBox.warning(self,
                                           u'Внимание',
                                           u'Необходимо указать дату прикрепления!',
                                           QtGui.QMessageBox.Ok,
                                           QtGui.QMessageBox.Ok)
                return
        if self._stoped or not self._run:
            self.btnPauseOrStop.setText(u'Приостановить')
            self._stoped = False
            self._run = True
            self.setEnabledCondWidgets(False)
            self.createAttach()


    def on_btnPauseOrStop(self):
        self.btnRun.setEnabled(True)
        if self._run and not self._stoped:
            self.btnPauseOrStop.setText(u'Остановить')
            self.btnRun.setText(u'Продолжить')
            self._stoped = True
        else:
            self.btnPauseOrStop.setText(u'Приостановить')
            self.btnRun.setText(u'Начать')
            self._stoped = True
            self._run = False
            self._currentClientIdx = 0
            self.mapHouseId2Info.clear()
            self.clientIdList = []
            self.orgStructureIdList = []
            self.progressBar.setValue(0)
            self.progressBar.setText(u'')
            self.setEnabledCondWidgets(True)


    def setEnabledCondWidgets(self, value):
        self.cmbOrgStructure.setEnabled(value)
        self.cmbAreaAddressType.setEnabled(value)
        self.cmbAreaAddressType.setEnabled(value)
        self.chkUpdateData.setEnabled(value)
        self.chkAttach.setEnabled(value)
        self.chkSaveAttachType.setEnabled(value and self.chkAttach.isChecked() and self.chkUpdateData.isChecked())
        self.btnClose.setEnabled(value)
        self.btnRun.setEnabled(value)
        self.btnPauseOrStop.setEnabled(not value)


    def updateClients(self):
        return self.chkUpdateData.isChecked()


    def getOrgStructureIdList(self):
        cmbOrgStructureCurrentIndex   = self.cmbOrgStructure.currentIndex()
        cmbOrgStructureRootModelIndex = self.cmbOrgStructure.rootModelIndex()

        treeIndex = self.cmbOrgStructure._model.index(cmbOrgStructureCurrentIndex, 0, cmbOrgStructureRootModelIndex)

        treeItem = treeIndex.internalPointer() if treeIndex.isValid() else None
        return treeItem.getItemIdList() if treeItem else []


    def getHouseIdList(self, orgStructureIdList):
        db = QtGui.qApp.db

        tableOrgStructureAddress = db.table('OrgStructure_Address')

        return db.getDistinctIdList(tableOrgStructureAddress,
                                    tableOrgStructureAddress['house_id'],
                                    [tableOrgStructureAddress['master_id'].inlist(orgStructureIdList)])


    def getOrgStructureAddressRecordList(self, houseIdList, orgStructureIdList):
        db = QtGui.qApp.db

        tableOrgStructureAddress = db.table('OrgStructure_Address')
        tableOrgStructure = db.table('OrgStructure')
        tableNet = db.table('rbNet')

        queryTable = tableOrgStructureAddress.innerJoin(tableOrgStructure,
                                                        tableOrgStructureAddress['master_id'].eq(tableOrgStructure['id']))
        queryTable = queryTable.leftJoin(tableNet, tableNet['id'].eq(tableOrgStructure['net_id']))

        cols = [
                tableOrgStructureAddress['master_id'],
                tableOrgStructureAddress['house_id'],
                tableOrgStructure['organisation_id'],
                tableOrgStructure['net_id'],
                tableOrgStructure['areaType'],
                tableOrgStructure['parent_id'],
                tableNet['sex'],
                tableNet['age']
               ]

        cond = [tableOrgStructureAddress['house_id'].inlist(houseIdList), tableOrgStructureAddress['master_id'].inlist(orgStructureIdList)]

        return db.getRecordList(queryTable, cols, cond)



    def mapOrgStructureAddressRecords2Info(self, records):
        mapHouseId2Info = {}

        for record in records:

            houseId        = forceRef(record.value('house_id'))
            masterId       = forceRef(record.value('master_id'))
            parentId       = forceRef(record.value('parent_id'))
            organisationId = forceRef(record.value('organisation_id'))
            areaType       = forceInt(record.value('areaType'))
            sex                = forceRef(record.value('sex'))
            age                = forceString(record.value('age'))
            ageSelector = parseAgeSelector(age)

            houseMasterInfoList = {}

            houseMasterInfoList['masterId']       = masterId
            houseMasterInfoList['houseId']        = houseId
            houseMasterInfoList['parentId']       = parentId
            houseMasterInfoList['organisationId'] = organisationId
            houseMasterInfoList['areaType']       = areaType
            houseMasterInfoList['sex']            = sex
            houseMasterInfoList['ageSelector']    = None if ageSelector == (0, 0, 0, 0) else ageSelector

            netId = forceRef(record.value('net_id'))

            netId, parentId = self.getActualNetId(parentId, netId)
            houseMasterInfoList['netId'] = netId


            masterInfoList = mapHouseId2Info.get(houseId, {})
            if masterId not in masterInfoList.keys():
                masterInfoList[masterId] = houseMasterInfoList
                mapHouseId2Info[houseId] = masterInfoList

        return mapHouseId2Info


    def getActualNetId(self, parentId, netId):
        db = QtGui.qApp.db

        tableOrgStructure = db.table('OrgStructure')

        while parentId and not netId:
            cols = [tableOrgStructure['parent_id'], tableOrgStructure['net_id']]
            cond = [tableOrgStructure['id'].eq(parentId), tableOrgStructure['deleted'].eq(0)]
            recordParent = db.getRecordEx(tableOrgStructure, cols, cond)
            if recordParent:
                netId = forceRef(recordParent.value('net_id'))
                parentId = forceRef(recordParent.value('parent_id'))

        return netId, parentId


    def getClientIdList(self, mapHouseId2Info, areaAddressType):
        db = QtGui.qApp.db
        tableClient = db.table('Client')
        tableAddress = db.table('Address')
        tableClientAddress = db.table('ClientAddress')
        queryTable = tableAddress.innerJoin(tableClientAddress, tableClientAddress['address_id'].eq(tableAddress['id']))
        queryTable = queryTable.innerJoin(tableClient, tableClient['id'].eq(tableClientAddress['client_id']))
        col = tableClientAddress['client_id']
        cond = [
                tableClient['deathDate'].isNull(), 
                tableClient['deleted'].eq(0), 
                tableAddress['deleted'].eq(0), 
                tableClientAddress['deleted'].eq(0), 
                tableAddress['house_id'].inlist(mapHouseId2Info.keys()),
                tableAddress['deleted'].eq(0),
                tableClient['deleted'].eq(0),
                tableClient['deathDate'].isNull(),
                tableClientAddress['deleted'].eq(0),
                tableClientAddress['type'].eq(areaAddressType),
               ]
        return db.getDistinctIdList(queryTable, col, cond)


    def getAttachCodeCol(self, orgStructureIdList, isCheckedCondition):
        if isCheckedCondition:
            return u'IF((rbAttachType.code = 1 OR rbAttachType.code = 2) AND (ClientAttach.orgStructure_id IS NULL OR ClientAttach.orgStructure_id NOT IN (%s)), 1, 0) AS attachCode'%(u','.join(str(orgStructureId) for orgStructureId in orgStructureIdList if orgStructureId))
        else:
            return u'IF((rbAttachType.code = 1 AND (ClientAttach.orgStructure_id IS NULL OR ClientAttach.orgStructure_id NOT IN (%s))) OR (rbAttachType.code = 2 AND ClientAttach.orgStructure_id IS NULL), 1, 0) AS attachCode'%(u','.join(str(orgStructureId) for orgStructureId in orgStructureIdList if orgStructureId))


    def getClientRecord(self, clientId, isCheckedCondition, areaAddressType, currentDate, orgStructureIdList):
        db = QtGui.qApp.db

        tableClient = db.table('Client')
        tableClientAttach = db.table('ClientAttach')
        tableAttachType = db.table('rbAttachType')
        tableClientAddress = db.table('ClientAddress')
        tableAddress = db.table('Address')

        cols = [
                tableClient['birthDate'],
                tableClient['sex'],
                tableClientAttach['id'].alias('clientAttachId'),
                tableClientAttach['client_id'],
                tableClientAttach['orgStructure_id'],
                tableAddress['house_id'],
                tableAttachType['code']
                # self.getAttachCodeCol(orgStructureIdList, isCheckedCondition)
               ]

        cond = [
                tableClientAttach['client_id'].eq(clientId),
                tableClientAttach['deleted'].eq(0),
                tableClient['deleted'].eq(0),
                tableAddress['deleted'].eq(0),
                tableClientAddress['type'].eq(areaAddressType),
                tableAttachType['code'].inlist(['1', '2'])
               ]
        cond.append(db.joinOr([tableClientAttach['endDate'].isNull(), tableClientAttach['endDate'].ge(QDate.currentDate())]))

        table = tableClientAttach
        table = table.leftJoin(tableAttachType,     tableClientAttach['attachType_id'].eq(tableAttachType['id']))
        table = table.leftJoin(tableClient,         tableClientAttach['client_id'].eq(tableClient['id']))
        table = table.innerJoin(tableClientAddress, tableClientAddress['client_id'].eq(tableClient['id']))
        table = table.innerJoin(tableAddress,       tableClientAddress['address_id'].eq(tableAddress['id']))
        return db.getRecordEx(table, cols, cond, u'ClientAttach.begDate DESC, ClientAddress.id DESC')


    def getClientRecordEx(self, clientId, mapHouseId2Info, areaAddressType, currentDate):

        db = QtGui.qApp.db

        tableClient        = db.table('Client')
        tableClientAddress = db.table('ClientAddress')
        tableAddress       = db.table('Address')

        cols = [tableClient['birthDate'],
                tableClient['sex'],
                tableAddress['house_id']
               ]
        cond = [tableClient['id'].eq(clientId),
                tableClient['deleted'].eq(0),
                tableAddress['house_id'].inlist(mapHouseId2Info.keys()),
                tableAddress['deleted'].eq(0),
                tableClientAddress['type'].eq(areaAddressType)
               ]
        table = tableClient
        table = table.innerJoin(tableClientAddress, tableClientAddress['client_id'].eq(tableClient['id']))
        table = table.innerJoin(tableAddress,       tableClientAddress['address_id'].eq(tableAddress['id']))
        return db.getRecordEx(table, cols, cond, u'ClientAddress.id DESC')


    def getCreateOrUpdateClientRecord(self, clientId, currentDate, areaAddressType):
        db = QtGui.qApp.db

        tableClient = db.table('Client')
        tableClientAddress = db.table('ClientAddress')
        tableAddress = db.table('Address')

        cols = [tableAddress['house_id'],
                tableClient['birthDate'],
                tableClient['sex']
               ]

        cond = [tableClient['id'].eq(clientId),
                tableClient['deleted'].eq(0),
                tableAddress['deleted'].eq(0),
                tableClientAddress['deleted'].eq(0),
                tableClientAddress['type'].eq(areaAddressType)
               ]

        table = tableClient
        table = table.innerJoin(tableClientAddress, tableClientAddress['client_id'].eq(tableClient['id']))
        table = table.innerJoin(tableAddress,       tableClientAddress['address_id'].eq(tableAddress['id']))
        return db.getRecordEx(table, cols, cond, u'ClientAddress.id DESC')


#    def getCreateOrUpdateClientAttachRecord(self, clientId):
#        db = QtGui.qApp.db
##        stmt = '''SELECT * FROM ClientAttach
##        WHERE ClientAttach.client_id = %d
##        AND ClientAttach.id = (SELECT MAX(CA.id)
##                               FROM ClientAttach AS CA
##                               LEFT JOIN rbAttachType ON CA.attachType_id=rbAttachType.id
##                               WHERE CA.client_id = %d AND rbAttachType.temporary = 0
##                               AND CA.deleted=0)''' % (clientId, clientId)
#        stmt = '''SELECT * FROM ClientAttach
#        WHERE ClientAttach.client_id = %d
#        AND IF(getClientAttachIdForDate(%d, 0, %s), 0, ClientAttach.id = getClientAttachIdForDate(%d, 1, %s))''' % (clientId, clientId, db.formatDate(QDate.currentDate()), clientId, db.formatDate(QDate.currentDate()))
#        query = db.query(stmt)
#        if query.first():
#            return query.record()
#        else:
#            return None


    def getCreateOrUpdateClientAttachRecord(self, clientId):
        db = QtGui.qApp.db
        stmt = '''SELECT CA.*
            FROM ClientAttach AS CA
            WHERE CA.id = (SELECT MAX(ClientAttach.id)
            FROM ClientAttach
            LEFT JOIN rbAttachType ON ClientAttach.attachType_id = rbAttachType.id
            WHERE ClientAttach.client_id = %d AND ClientAttach.deleted = 0
            AND ClientAttach.id = getClientAttachId(%d, 0) AND rbAttachType.code in ('1', '2'))''' % (clientId, clientId)
        query = db.query(stmt)
        if query.first():
            return query.record()
        else:
            return None


    def createAttach(self):
        QtGui.qApp.setWaitCursor()
        updateClients = self.updateClients()
        areaAddressType = self.cmbAreaAddressType.currentIndex()
        currentDate = QDate.currentDate()
        if self._currentClientIdx == 0:
            self.progressBar.setValue(0)
            self.progressBar.setMaximum(1)
            self.orgStructureIdList = self.getOrgStructureIdList()
            houseIdList = self.getHouseIdList(self.orgStructureIdList)
            records = self.getOrgStructureAddressRecordList(houseIdList, self.orgStructureIdList)
            self.mapHouseId2Info = self.mapOrgStructureAddressRecords2Info(records)
            self.clientIdList = self.getClientIdList(self.mapHouseId2Info, areaAddressType)

        clientIdList = self.clientIdList
        mapHouseId2Info = self.mapHouseId2Info
        orgStructureIdList = self.orgStructureIdList

        QtGui.qApp.restoreOverrideCursor()

        if updateClients:
            self.createOrUpdateAttach(clientIdList, mapHouseId2Info, areaAddressType, currentDate, orgStructureIdList)
        else:
            self.createNewAttach(clientIdList, mapHouseId2Info, areaAddressType, currentDate, orgStructureIdList)

        if self._currentClientIdx == len(clientIdList) or len(clientIdList) == 0:
            self.btnPauseOrStop.setText(u'Приостановить')
            self.btnRun.setText(u'Начать')
            self._stoped = True
            self._run = False
            self._currentClientIdx = 0
            self.mapHouseId2Info.clear()
            self.clientIdList = []
            self.orgStructureIdList = []
            self.progressBar.setText(u'Готово')
            self.setEnabledCondWidgets(True)


    def createOrUpdateAttach(self, clientIdList, mapHouseId2Info, areaAddressType, currentDate, orgStructureIdList):
        db = QtGui.qApp.db
        tableClientAttach = db.table('ClientAttach')
        self.progressBar.setMaximum(len(clientIdList) if len(clientIdList) else 1)
        mapAttachId2Code = {}
        saveAttachType = self.chkSaveAttachType.isChecked()
        while self._currentClientIdx < len(clientIdList):
            clientId = clientIdList[self._currentClientIdx]
            if self._stoped:
                break
            QtGui.qApp.processEvents()
            self.stepCreateOrUpdateAttach(clientId, mapHouseId2Info, areaAddressType,
                                          currentDate, orgStructureIdList, tableClientAttach, db, mapAttachId2Code, saveAttachType)


    def stepCreateOrUpdateAttach(self, clientId, mapHouseId2Info, areaAddressType,
                                       currentDate, orgStructureIdList, tableClientAttach, db, mapAttachId2Code, saveAttachType):
        clientRecord = self.getCreateOrUpdateClientRecord(clientId, currentDate, areaAddressType)
        if clientRecord:
            houseId   = forceRef(clientRecord.value('house_id'))
            clientBirthDate = forceDate(clientRecord.value('birthDate'))
            clientSex = forceRef(clientRecord.value('sex'))
            masterId, organisationId = self.getMasterIdOrganisationId(mapHouseId2Info, houseId, clientId, clientBirthDate, clientSex)
            if masterId:
                clientAttachRecord = self.getCreateOrUpdateClientAttachRecord(clientId)
                attachTypeId = None
                notes = u'Сервис "прикрепление": {0}, пользователь {1}'.format(
                    formatDateTime(QDateTime.currentDateTime()), QtGui.qApp.userName())
                if clientAttachRecord:
                    clientAttachId = forceRef(clientAttachRecord.value('id'))
                    attachTypeId   = forceRef(clientAttachRecord.value('attachType_id'))
                    attachTypeCode = self.getAttachTypeCodeById(attachTypeId, mapAttachId2Code)
                    update = (((attachTypeCode == '1') or (attachTypeCode == '2' and self.chkAttach.isChecked()))
                              and forceRef(clientAttachRecord.value('orgStructure_id')) != masterId and forceDate(clientAttachRecord.value('endDate')).isNull()
                              and forceDate(clientAttachRecord.value('begDate')) <= forceDate(self.edtDate.date()).addDays(-1))
                    if update:

                        clientAttachRecord.setValue('deAttachType_id', QVariant(self.cmbDeAttachType.value()))
                        clientAttachRecord.setValue('endDate', QVariant(forceDate(self.edtDate.date()).addDays(-1)))
                        clientAttachRecord.setValue('notes', QVariant(notes))
                        db.updateRecords(tableClientAttach, clientAttachRecord, [tableClientAttach['id'].eq(clientAttachId)])
                        # отработает по следующему условию
                        # newRecord = tableClientAttach.newRecord()
                        # newRecord.setValue('client_id', QVariant(clientId))
                        # newRecord.setValue('attachType_id', QVariant(1))
                        # newRecord.setValue('LPU_id', QVariant(organisationId))
                        # newRecord.setValue('orgStructure_id', QVariant(masterId))
                        # newRecord.setValue('begDate', QVariant(self.edtDate.date()))
                        # newRecord.setValue('notes', QVariant(notes))
                        # db.insertRecord(tableClientAttach, newRecord)
                if not clientAttachRecord or (
                        clientAttachRecord and forceDate(clientAttachRecord.value('endDate')) and forceDate(
                        clientAttachRecord.value('endDate')) < self.edtDate.date()):
                    newRecord = tableClientAttach.newRecord()
                    newRecord.setValue('client_id', QVariant(clientId))
                    newRecord.setValue('attachType_id', QVariant(attachTypeId if saveAttachType and attachTypeId else 1))
                    newRecord.setValue('LPU_id', QVariant(organisationId))
                    newRecord.setValue('orgStructure_id', QVariant(masterId))
                    newRecord.setValue('begDate', QVariant(currentDate))
                    newRecord.setValue('notes', QVariant(notes))
                    db.insertRecord(tableClientAttach, newRecord)

        self.progressBar.step()
        self.progressBar.setText(u'%d/%d' % (self.progressBar.value(), self.progressBar.maximum()))
        self._currentClientIdx += 1


    def closeAttach(self, clientId, orgId):
        currentDate = QDate.currentDate()
        db = QtGui.qApp.db
        tableClientAttach = db.table('ClientAttach')
        #tableAttachType = db.table('rbAttachType')
        #table = tableClientAttach.leftJoin(tableAttachType, tableAttachType['id'].eq(tableClientAttach['attachType_id']))

        cond = [tableClientAttach['client_id'].eq(clientId),
            tableClientAttach['deleted'].eq(0),
            tableClientAttach['orgStructure_id'].eq(orgId),
            db.joinOr([tableClientAttach['endDate'].isNull(),
                        tableClientAttach['endDate'].ge(currentDate)])]

        recordList = db.getRecordList(tableClientAttach, '*', cond)
        for record in recordList:
            record.setValue('endDate', QVariant(currentDate.addDays(-1)))
            db.updateRecord(tableClientAttach, record)


    def createNewAttach(self, clientIdList, mapHouseId2Info, areaAddressType, currentDate, orgStructureIdList):
        db = QtGui.qApp.db
        tableClientAttach = db.table('ClientAttach')
        self.progressBar.setMaximum(len(clientIdList) if len(clientIdList) else 1)
        while self._currentClientIdx < len(clientIdList):
            clientId = clientIdList[self._currentClientIdx]
            if self._stoped:
                break
            QtGui.qApp.processEvents()
            self.stepNewAttach(clientId, mapHouseId2Info, areaAddressType,
                               currentDate, orgStructureIdList, tableClientAttach, db)


    def stepNewAttach(self, clientId, mapHouseId2Info, areaAddressType,
                      currentDate, orgStructureIdList, tableClientAttach, db):
        # record = self.getClientRecord(clientId, self.chkAttach.isChecked(),
        #                               areaAddressType, currentDate, orgStructureIdList)
        record = self.getCreateOrUpdateClientAttachRecord(clientId)
        notes = u'Сервис "прикрепление": {0}, пользователь {1}'.format(
            formatDateTime(QDateTime.currentDateTime()), QtGui.qApp.userName())
        mustCreateAttach = 1
        if record:
            endDate = forceDate(record.value('endDate'))
            if not (endDate and endDate < currentDate):
                mustCreateAttach = 0
        if not mustCreateAttach:
            pass
            # attachCode     = forceBool(record.value('attachCode'))
            # clientAttachId = forceRef(record.value('clientAttachId'))
            # houseId        = forceRef(record.value('house_id'))
            # clientBirthDate      = forceDate(record.value('birthDate'))
            # clientSex      = forceRef(record.value('clientSex'))
            # if attachCode:
            #     masterId, organisationId = self.getMasterIdOrganisationId(mapHouseId2Info, houseId, clientId, clientBirthDate, clientSex)
            #     if masterId:
            #         newRecord = db.getRecordEx(tableClientAttach, '*', [tableClientAttach['id'].eq(clientAttachId)])
            #
            #         newRecord.setValue('orgStructure_id', QVariant(masterId))
            #         newRecord.setValue('LPU_id', QVariant(organisationId))
            #         newRecord.setValue('begDate', QVariant(currentDate))
            #         newRecord.setValue('notes', QVariant(notes))
            #         db.updateRecords(tableClientAttach, newRecord, [tableClientAttach['id'].eq(clientAttachId)])
        else:
            recordClient = self.getClientRecordEx(clientId, mapHouseId2Info, areaAddressType, currentDate)
            if recordClient:
                clientBirthDate = forceDate(recordClient.value('birthDate'))
                houseId   = forceRef(recordClient.value('house_id'))
                masterId, organisationId = self.getMasterIdOrganisationId(mapHouseId2Info, houseId, clientId, clientBirthDate)
                if masterId:
                    newRecord = tableClientAttach.newRecord()
                    newRecord.setValue('client_id', QVariant(clientId))
                    newRecord.setValue('attachType_id', QVariant(1))
                    newRecord.setValue('LPU_id', QVariant(organisationId))
                    newRecord.setValue('orgStructure_id', QVariant(masterId))
                    newRecord.setValue('begDate', QVariant(currentDate))
                    newRecord.setValue('notes', QVariant(notes))
                    db.insertRecord(tableClientAttach, newRecord)

        self.progressBar.step()
        self.progressBar.setText(u'%d/%d' % (self.progressBar.value(), self.progressBar.maximum()))
        self._currentClientIdx += 1


    def getAttachTypeCodeById(self, attachTypeId, map):
        result = map.get(attachTypeId, None)
        if not result:
            result = forceString(QtGui.qApp.db.translate('rbAttachType', 'id', attachTypeId, 'code'))
            map[attachTypeId] = result
        return result


    def getMasterIdOrganisationId(self, mapHouseId2Info, houseId, clientId, clientBirthDate, clientSex = None):
        masterId = None
        organisationId = None
        houseMasterInfoList = mapHouseId2Info.get(houseId, {})
        for masterInfoList in houseMasterInfoList.values():
            ageSelector = masterInfoList.get('ageSelector', None)
            sex = masterInfoList.get('sex', None)
            clientAge = calcAgeTuple(clientBirthDate, None)
            if not clientAge:
                clientAge = (0, 0, 0, 0)
            if (not ageSelector or checkAgeSelector(ageSelector, clientAge)) and (not sex or sex == clientSex):
                masterId = masterInfoList.get('masterId', None)
                organisationId = masterInfoList.get('organisationId', None)
            elif self.updateClients():
                self.closeAttach(clientId, masterInfoList.get('masterId', None))

        return masterId, organisationId


    @pyqtSignature('bool')
    def on_chkUpdateData_toggled(self, value):
        self.cmbDeAttachType.setEnabled(value)
        self.edtDate.setEnabled(value)
        self.chkSaveAttachType.setEnabled(value and self.chkAttach.isChecked())

    @pyqtSignature('bool')
    def on_chkAttach_toggled(self, value):
        self.chkSaveAttachType.setEnabled(value and self.chkUpdateData.isChecked())


    @pyqtSignature('QDate')
    def on_edtDate_dateChanged(self, date):
        if date.isValid():
            db = QtGui.qApp.db
            rbDeAttachTypeTable = db.table('rbDeAttachType')
            filter = db.joinAnd([db.joinOr([rbDeAttachTypeTable['endDate'].ge(date),
                                            rbDeAttachTypeTable['endDate'].isNull()]),
                                 rbDeAttachTypeTable['begDate'].le(date)])
        else:
            filter = ''
        self.cmbDeAttachType.setFilter(filter)