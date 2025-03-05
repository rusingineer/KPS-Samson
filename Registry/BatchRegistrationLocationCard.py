# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2024 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QDate, QObject, QTime, pyqtSignature

from library.crbcombobox import CRBComboBox
from library.Utils import exceptionToUnicode, forceBool, forceString,forceInt,getPref, getPrefBool, getPrefInt, getPrefRef, getPrefString, setPref, toVariant
from Registry.Ui_BatchRegLocationCardDialog import Ui_BatchRegLocationCardDialog


class CSetParamsBatchRegistrationLocationCard(QtGui.QDialog, Ui_BatchRegLocationCardDialog):
    def __init__(self,  parent):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.preferences = 'BatchRegLocatCardParams'
        self.cmbDocumentTypeForTracking.setTable('rbDocumentTypeForTracking', True)
        self.cmbDocumentTypeForTracking.setShowFields(CRBComboBox.showCodeAndName)
        self.cmbDocumentLocation.setTable('rbDocumentTypeLocation', True)
        self.cmbDocumentLocation.setShowFields(CRBComboBox.showCodeAndName)
        self.cmbPerson.setSpecialityIndependents()
        self.cmbPerson.setChkSpecialityDefaultStatus(False)
        self.parent = parent
        self.setParams()


    def setParams(self):
        params = {}
        # params = getPref(QtGui.qApp.preferences.reportPrefs, self.preferences, {})
        self.btnStart.setVisible(not QtGui.qApp.batchRegLocatCardProcess)
        self.btnRetry.setVisible(QtGui.qApp.batchRegLocatCardProcess)
        self.cmbDocumentNumber.setCurrentIndex(getPrefInt(params, 'numberPreferences', 0))
        self.cmbDocumentTypeForTracking.setValue(getPrefRef(params, 'documentTypeForTrackingId', None))
        self.cmbDocumentLocation.setValue(getPrefRef(params, 'documentLocationId', None))
        self.cmbPerson.setValue(getPrefRef(params, 'personId', None))
        self.edtNotesPage.setPlainText(getPrefString(params, 'notesPage', ''))


    def params(self, batchRegLocatCardProcess = True):
        QtGui.qApp.batchRegLocatCardProcess = batchRegLocatCardProcess
        result = {}
        result['BatchRegLocatCardProcess'] = batchRegLocatCardProcess
        result['numberPreferences'] = self.cmbDocumentNumber.currentIndex()
        result['documentTypeForTrackingId'] = self.cmbDocumentTypeForTracking.value()
        result['documentLocationId'] = self.cmbDocumentLocation.value()
        result['personId'] = self.cmbPerson.value()
        result['notesPage'] = self.edtNotesPage.toPlainText()
        return result


    def saveDefaultParams(self, params):
        prefs = {}
        for param, value in params.iteritems():
            setPref(prefs, param, value)
        setPref(QtGui.qApp.preferences.reportPrefs, self.preferences, prefs)


    def getDefaultParams(self):
        result = {}
        prefs = getPref(QtGui.qApp.preferences.reportPrefs, 'BatchRegLocatCardClientUpdateInfo', {})
        result['numberPreferences'] = getPref(prefs, 'numberPreferences', 0)
        result['documentTypeForTrackingId'] = getPrefRef(prefs, 'documentTypeForTrackingId', None)
        result['documentLocationId'] = getPrefRef(prefs, 'documentLocationId', None)
        result['personId']  = getPrefRef(prefs, 'personId', None)
        result['notesPage'] = getPrefString(prefs, 'notesPage', '')
        result['clientId'] = getPrefRef(prefs, 'clientId', None)
        # result['lastMasterId'] = getPrefRef(prefs, 'lastMasterId', None)
        # result['lastItemId'] = getPrefRef(prefs, 'lastItemId', None)
        result['lastMasterIdList'] = getPrefString(prefs, 'lastMasterIdList', '')
        result['lastItemIdList'] = getPrefString(prefs, 'lastItemIdList', '')
        return result


    def saveParams(self, batchRegLocatCardProcess = True):
        localParams = self.params(batchRegLocatCardProcess)
        self.saveDefaultParams(localParams)


    def checkDataEntered(self):
        result = True
        documentType = forceBool(self.cmbDocumentTypeForTracking.value())
        if not documentType:
            QtGui.QMessageBox.warning( self, u'Внимание!', u'Необходимо указать вид документа!', QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ok)
            self.cmbDocumentTypeForTracking.setFocus()
            return False
        documentLocation = forceBool(self.cmbDocumentLocation.value())
        if not documentLocation:
            res = QtGui.QMessageBox.warning( self, u'Внимание!', u'Необходимо указать место нахождения карты!\nИначе этот параметр не будет задан!', QtGui.QMessageBox.Ok | QtGui.QMessageBox.Ignore, QtGui.QMessageBox.Ok)
            if res == QtGui.QMessageBox.Ok:
                self.cmbDocumentLocation.setFocus()
                return False
        return result


    @pyqtSignature('')
    def on_btnStart_clicked(self):
        if self.checkDataEntered():
            self.saveParams()
            self.parent.on_buttonBoxClient_reset()
            self.parent.tblClients.setIdList([])
            self.parent.on_actClientIdBarcodeScan_triggered()
            self.getFontInfoLabel(True)
            QtGui.qApp.batchRegLocatCardProcess = True
            self.parent.lblClientsCount.setText(u'ВЫ НАХОДИТЕСЬ В РЕЖИМЕ ИЗМЕНЕНИЯ МЕСТА НАХОЖДЕНИЯ КАРТЫ! ДЛЯ ВЫХОДА ИЗ РЕЖИМА НАЖМИТЕ F5.')
            self.close()


    def getFontInfoLabel(self, maxSize = False):
        font = QtGui.QFont()
        font.setPointSize(12 if maxSize else 8)
        font.setWeight(75 if maxSize else 50)
        font.setItalic(True if maxSize else False)
        font.setBold(True if maxSize else False)
        self.parent.lblClientsCount.setFont(font)


    @pyqtSignature('')
    def on_btnRetry_clicked(self):
        params = self.getDefaultParams()
        # lastMasterId = params.get('lastMasterId', None)
        # lastItemId = params.get('lastItemId', None)
        lastMasterIdList = params.get('lastMasterIdList', None)
        lastItemIdList = params.get('lastItemIdList', None)
        # if lastItemId:
        #     db = QtGui.qApp.db
        #     table = db.table('Client_DocumentTrackingItem')
        #     db.deleteRecord(table, table['id'].eq(lastItemId))
        # if lastMasterId:
        #     db = QtGui.qApp.db
        #     table = db.table('Client_DocumentTracking')
        #     db.deleteRecord(table, table['id'].eq(lastMasterId))
        if lastItemIdList:
            listItemId = lastItemIdList.split(',')
            if listItemId[-1] == '':
                listItemId.pop()
            db = QtGui.qApp.db
            table = db.table('Client_DocumentTrackingItem')
            for itemId in listItemId:
                itemId = itemId.replace("'", '')
                db.deleteRecord(table, table['id'].eq(forceInt(itemId)))
        if lastMasterIdList:
            listMasterId = lastMasterIdList.split(',')
            if listMasterId[-1] == '':
                listMasterId.pop()
            db = QtGui.qApp.db
            table = db.table('Client_DocumentTracking')
            for masterId in listMasterId:
                masterId = masterId.replace("'", "")
                db.deleteRecord(table, table['id'].eq(forceInt(masterId)))
                
        self.close()


    @pyqtSignature('')
    def on_btnClose_clicked(self):
        # prefs = getPref(QtGui.qApp.preferences.reportPrefs, self.preferences, {})
        batchRegLocatCardProcess = QtGui.qApp.batchRegLocatCardProcess
        if batchRegLocatCardProcess:
            self.getFontInfoLabel()
            self.parent.lblClientsCount.setText('')
            self.saveParams(not batchRegLocatCardProcess)
            self.parent.on_buttonBoxClient_reset()
            self.parent.on_buttonBoxClient_apply()
        self.close()


class CGetParamsBatchRegistrationLocationCard(QtGui.QDialog, Ui_BatchRegLocationCardDialog):
    def __init__(self,  parent, clientId):
        QObject.__init__(self, parent)
        self.clientId = clientId
        self.record = None
        self.preferences = 'BatchRegLocatCardParams'
        self.clientUpdateInfo = []
        self.updateMainTable = False
        self.params = self.getDefaultParams()


    def registrationLocationCard(self):
        #self.clientUpdateInfo = self.setRecord()
        #self.saveDefaultParams(self.clientUpdateInfo)
        return self.save()

#
#    def setRecord(self):
#        result = {}
#        if self.clientId:
#            db = QtGui.qApp.db
#            table = db.table('Client_DocumentTracking')
#            rbTable = db.table('rbDocumentTypeForTracking')
#            self.record = db.getRecordEx(table.innerJoin(rbTable, table['documentTypeForTracking_id'].eq(rbTable['id'])), 'Client_DocumentTracking.*', [table['deleted'].eq(0), table['client_id'].eq(self.clientId)], 'Client_DocumentTracking.id DESC')
#            if self.record:
#                result['id'] = forceRef(self.record.value('id'))
#            else:
#                result['clientId']  = self.clientId
#                result['documentDate'] = QDate.currentDate()
#        return result


    def getRecord(self):
        if self.clientId:
            db = QtGui.qApp.db
            table = db.table('Client_DocumentTracking')
            rbTable = db.table('rbDocumentTypeForTracking')
            resultTable = table.innerJoin(rbTable, table['documentTypeForTracking_id'].eq(rbTable['id']))
            # self.record = db.getRecordEx(table.innerJoin(rbTable, table['documentTypeForTracking_id'].eq(rbTable['id'])),
            #  'Client_DocumentTracking.*', [table['deleted'].eq(0), table['client_id'].eq(self.clientId),
            #                                table['documentTypeForTracking_id'].eq(self.params.get('documentTypeForTrackingId', None))
            #                                ],
            #                              'Client_DocumentTracking.id DESC')
            cond = [table['deleted'].eq(0), table['client_id'].eq(self.clientId),table['documentTypeForTracking_id'].eq(self.params.get('documentTypeForTrackingId', None))]
            numberPreferences = self.params.get('numberPreferences', None)
            order = 'Client_DocumentTracking.id DESC'
            if numberPreferences == 1:
                cond.append(table['documentNumber'].eq(self.clientId))
            self.record = db.getDistinctRecordList(resultTable,'Client_DocumentTracking.*', cond, order)
            if not self.record:
                # numberPreferences = self.params.get('numberPreferences', None)
                if self.params.get('BatchRegLocatCardProcess', False):
                    db = QtGui.qApp.db
                    self.record = []
                    self.record.append(db.record('Client_DocumentTracking'))
                    self.record[0].setValue('client_id', toVariant(self.clientId))
                    self.record[0].setValue('documentTypeForTracking_id', toVariant(self.params.get('documentTypeForTrackingId', None)))
                    self.record[0].setValue('documentDate', toVariant(QDate.currentDate()))
                    if numberPreferences==1:
                        self.record[0].setValue('documentNumber', toVariant(self.clientId))
                    else:
                        self.record[0].setValue('documentNumber', toVariant(None))
                self.updateMainTable = True
            return self.record
        return None


    def getRecordItem(self, masterId):
        if masterId:
            db = QtGui.qApp.db
            record = db.record('Client_DocumentTrackingItem')
            record.setValue('master_id', toVariant(masterId))
            record.setValue('documentLocation_id', toVariant(self.params.get('documentLocationId', None)))
            record.setValue('documentLocationDate', toVariant(QDate.currentDate()))
            record.setValue('documentLocationTime', toVariant(QTime.currentTime()))
            record.setValue('person_id', toVariant(self.params.get('personId', None)))
            record.setValue('note', toVariant(self.params.get('notesPage', None)))
            return record
        return None


    def getDefaultParams(self):
        result = {}
        prefs = getPref(QtGui.qApp.preferences.reportPrefs, self.preferences, {})
        result['numberPreferences'] = getPref(prefs, 'numberPreferences', 0)
        result['documentTypeForTrackingId'] = getPrefRef(prefs, 'documentTypeForTrackingId', None)
        result['documentLocationId'] = getPrefRef(prefs, 'documentLocationId', None)
        result['personId']  = getPrefRef(prefs, 'personId', None)
        result['notesPage'] = getPrefString(prefs, 'notesPage', '')
        result['BatchRegLocatCardProcess'] = QtGui.qApp.batchRegLocatCardProcess
        return result


    def saveDefaultParams(self, params):
        prefs = {}
        for param, value in params.iteritems():
            setPref(prefs, param, value)
        setPref(QtGui.qApp.preferences.reportPrefs, 'BatchRegLocatCardClientUpdateInfo', prefs)


    def save(self):
        records = self.getRecord()
        if records:
            if records.__len__() > 0:
                try:
                    db = QtGui.qApp.db
                    db.transaction()
                    try:
                        # if records.__len__ == 1:
                            # id = db.insertOrUpdate('Client_DocumentTracking', records[0])
                            # recordItem = self.getRecordItem(id)
                            # itemId = db.insertRecord('Client_DocumentTrackingItem', recordItem)
                            # db.commit()
                            # self.params['lastMasterId'] = id if self.updateMainTable else None
                            # self.params['lastItemId'] = itemId
                            # self.saveDefaultParams(self.params)
                        # else:
                        idList = []
                        for record in records:
                            id = db.insertOrUpdate('Client_DocumentTracking', record)
                            recordItem = self.getRecordItem(id)
                            itemId = db.insertRecord('Client_DocumentTrackingItem', recordItem)
                            db.commit()
                            # self.params['lastMasterId'] = id if self.updateMainTable else None
                            if self.updateMainTable:
                                if not 'lastMasterIdList' in self.params.keys():
                                    self.params['lastMasterIdList'] = ''
                                    self.params['lastMasterIdList'] = "'" + forceString(id) + "',"
                                else:
                                    if self.params['lastMasterIdList'] == '':
                                        self.params['lastMasterIdList'] = "'" + forceString(id) + "',"           # Не факт что нужны
                                    else:
                                        self.params['lastMasterIdList'] = self.params['lastMasterIdList'] + "'"+ forceString(id) + "',"
                            # self.params['lastItemId'] = itemId
                            if not 'lastItemIdList' in self.params.keys():
                                self.params['lastItemIdList'] = ''
                                self.params['lastItemIdList'] = "'"+forceString(itemId)+"',"
                            else:
                                if self.params['lastItemIdList'] == '':
                                    self.params['lastItemIdList'] = "'"+forceString(itemId)+"',"
                                else:
                                    self.params['lastItemIdList'] = self.params['lastItemIdList']+ "'"+forceString(itemId)+"',"
                            self.saveDefaultParams(self.params)
                            idList.append(id)
                    except:
                        db.rollback()
                        raise
                    return idList
                    # return id
                except Exception, e:
                    QtGui.qApp.logCurrentException()
                    QtGui.QMessageBox.critical( self,
                                                u'',
                                                exceptionToUnicode(e),
                                                QtGui.QMessageBox.Close)
        return None

