#!/usr/bin/env python
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
import gc
import os
import sys
from optparse import OptionParser

from PyQt4 import QtGui, QtCore, QtSql
from PyQt4.QtCore import QDir, qInstallMsgHandler, QVariant, pyqtSignature, Qt, QTime, QDateTime

from library import database
from library.BaseApp import CBaseApp
from library.DialogBase import CConstructHelperMixin
from library.InDocTable import CRecordListModel, CInDocTableCol
from library.Utils import setPref, forceString, forceRef, toVariant, forceDate, pyDate, forceInt, calcAgeInYears
from library.dbfpy.dbf import Dbf

from appPreferencesDialog import CAppPreferencesDialog
from preferences.connection import CConnectionDialog
from preferences.decor import CDecorDialog
from s11main import parseGCDebug, parseGCThreshold

from Events.Utils import getAvailableCharacterIdByMKB

from Users.Login import CLoginDialog
from Users.tryKerberosAuth import tryKerberosAuth

from Ui_importCOVID import Ui_MainWindow


class CMyApp(CBaseApp):
    __pyqtSignals__ = ('dbConnectionChanged(bool)',
                       'currentUserIdChanged()',
                       )

    def __init__(self, appargs):
        CBaseApp.__init__(self, appargs, 'importCOVID.ini')
        self.logDir = os.path.join(unicode(QDir().toNativeSeparators(QDir().homePath())), '.samson-vista')
        self.oldMsgHandler = qInstallMsgHandler(self.msgHandler)
        self.oldExceptHook = sys.excepthook
        sys.excepthook = self.logException
        self.traceActive = True
        self.homeDir = None
        self.saveDir = None
        self.userId = None
        self.userSpecialityId = None
        self.userOrgStructureId = None
        self.db = None
        self.mainWindow = None
        self.registerDocumentTables()
        self._currentClientId = None
        self.userInfo = None
        self.demoModeRequested = True
        self.serviceName = 'SamsonImportCOVID'
        self.demoModePosible = lambda: False
        # self.defaultIsManualSwitchDiagnosis = lambda: False
        # self.defaultMorphologyMKBIsVisible = lambda: False
        # self.isExSubclassMKBVisible = lambda: False
        # self.isTNMSVisible = lambda: False

        self._highlightRedDate = None

    def registerDocumentTables(self):
        database.registerDocumentTable('Action')
        database.registerDocumentTable('Client')
        database.registerDocumentTable('ClientDocument')
        database.registerDocumentTable('Diagnosis')
        database.registerDocumentTable('Diagnostic')
        database.registerDocumentTable('Event')
        database.registerDocumentTable('ClientDocument')
        database.registerDocumentTable('ClientPolicy')

    def userName(self):
        if self.userInfo:
            return u'%s (%s)' % (self.userInfo.name(), self.userInfo.login())
        else:
            return ''

    def callWithWaitCursor(self, widget, func, *params, **kwparams):
        self.setWaitCursor()
        try:
            return func(*params, **kwparams)
        finally:
            self.restoreOverrideCursor()

    def startProgressBar(self, steps, fmt=u'%v из %m'):
        progressBar = self.mainWindow.getProgressBar()
        progressBar.setFormat(fmt)
        progressBar.setMinimum(0)
        progressBar.setMaximum(steps)
        progressBar.setValue(0)

    def stepProgressBar(self, step=1):
        progressBar = self.mainWindow.getProgressBar()
        progressBar.setValue(progressBar.value()+step)

    def stopProgressBar(self):
        self.mainWindow.hideProgressBar()


class CMainWindow(QtGui.QMainWindow, Ui_MainWindow, CConstructHelperMixin):
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.setupUi(self)
        self.progressBar = None
        self.progressBarVisible = False
        self.OMSPolicy = None
        self.oldPolicy = None
        self.tempPolicy = None
        self.newPolicy = None
        self.recordList = []
        self.clientMap = {}
        self.eventMap = {}
        self.mapCharacters = {}
        self.specialityMap = {}
        self.actionTypeMap = {}
        self.mapOMSCodeToOrgId = {}
        self.actionMap = {}
        self.sexMap = {u'Ж': 2, u'ж': 2, u'М': 1, u'м': 1}
        self.documentTypeMap = {}
        self.dbfProcessed = False

        self.addModels('DBF', CDBFModel(self))
        self.tblDBF.setModel(self.modelDBF)
        self.prepareStatusBar()
        # self.addObject('actEventEditClient', QtGui.QAction(u'Открыть регистрационную карточку', self))
        # self.addObject('actEditActionEvent', QtGui.QAction(u'Редактировать обращение', self))
        # self.tblDBF.addPopupAction(self.actEventEditClient)
        # self.tblDBF.addPopupAction(self.actEditActionEvent)
        # # self.tblDBF.createPopupMenu([self.actEventEditClient, self.actEditActionEvent])
        # self.connect(self.actEditActionEvent, SIGNAL('triggered()'), self.on_actEditActionEvent_triggered)

    @pyqtSignature('')
    def on_actLogin_triggered(self):
        try:
            userId = None
            login = ''
            if not QtGui.qApp.db:
                QtGui.qApp.openDatabase()
            if QtGui.qApp.demoModePosible() and QtGui.qApp.demoModeRequested:
                ok, userId, demoMode, login = True, None, True, 'demo'
            else:
                ok = False
                if QtGui.qApp.kerberosAuthEnabled():
                    userId = tryKerberosAuth()
                    if userId:
                        ok, demoMode = True, False
                        login = forceString(QtGui.qApp.db.translate('Person', 'id', userId, 'login'))
                if not ok and QtGui.qApp.passwordAuthEnabled():
                    dialog = CLoginDialog(self)
                    dialog.setLoginName(QtGui.qApp.preferences.appUserName)
                    if dialog.exec_():
                        ok, userId, demoMode, login = True, dialog.userId(), dialog.demoMode(), dialog.loginName()
                    else:
                        ok, userId, demoMode, login = False, None, False, ''
            if ok:
                QtGui.qApp.setUserId(userId)
                QtGui.qApp.preferences.appUserName = login
                self.setUserName(QtGui.qApp.userName())
                self.updateActionsState()
                return
        except database.CDatabaseException as e:
            QtGui.QMessageBox.critical(
                QtGui.QMessageBox(),
                u'Ошибка открытия базы данных',
                unicode(e),
                QtGui.QMessageBox.Close)
        except Exception as e:
            QtGui.QMessageBox.critical(
                QtGui.QMessageBox(),
                u'Ошибка открытия базы данных',
                u'Невозможно установить соединение с базой данных\n' + unicode(e),
                QtGui.QMessageBox.Close)
            QtGui.qApp.logCurrentException()
        QtGui.qApp.closeDatabase()

    @pyqtSignature('')
    def on_actLogout_triggered(self):
        if QtGui.qApp.db:
            QtGui.qApp.clearUserId(True)
            QtGui.qApp.closeDatabase()
        self.setUserName('')
        self.updateActionsState()

    @pyqtSignature('')
    def on_actQuit_triggered(self):
        self.close()

    @QtCore.pyqtSignature('')
    def on_actPreferences_triggered(self):
        application = QtGui.qApp
        dialog = CAppPreferencesDialog(self)
        dialog.setProps(application.preferences.appPrefs)
        if dialog.exec_():
            application.preferences.appPrefs.update(dialog.props())
            application.preferences.save()
            self.setUserName(application.userName())

    @QtCore.pyqtSignature('')
    def on_actConnection_triggered(self):
        dlg = CConnectionDialog(self)
        preferences = QtGui.qApp.preferences
        dlg.setDriverName(preferences.dbDriverName)
        dlg.setServerName(preferences.dbServerName)
        dlg.setServerPort(preferences.dbServerPort)
        dlg.setDatabaseName(preferences.dbDatabaseName)
        dlg.setUserName(preferences.dbUserName)
        dlg.setPassword(preferences.dbPassword)
        if dlg.exec_():
            preferences.dbDriverName = dlg.driverName()
            preferences.dbServerName = dlg.serverName()
            preferences.dbServerPort = dlg.serverPort()
            preferences.dbDatabaseName = dlg.databaseName()
            preferences.dbUserName = dlg.userName()
            preferences.dbPassword = dlg.password()
            preferences.save()

    @QtCore.pyqtSignature('')
    def on_actDecor_triggered(self):
        dlg = CDecorDialog(self)
        preferences = QtGui.qApp.preferences
        dlg.setStyle(preferences.decorStyle)
        dlg.setStandardPalette(preferences.decorStandardPalette)
        dlg.setMaximizeMainWindow(preferences.decorMaximizeMainWindow)
        dlg.setFullScreenMainWindow(preferences.decorFullScreenMainWindow)
        if dlg.exec_():
            preferences.decorStyle = dlg.style()
            preferences.decorStandardPalette = dlg.standardPalette()
            preferences.decorMaximizeMainWindow = dlg.maximizeMainWindow()
            preferences.decorFullScreenMainWindow = dlg.fullScreenMainWindow()
            preferences.save()
            QtGui.qApp.applyDecorPreferences()

    def savePreferences(self):
        preferences = {}
        setPref(preferences, 'geometry', QVariant(self.saveGeometry()))
        setPref(preferences, 'state', QVariant(self.saveState()))
        setPref(QtGui.qApp.preferences.windowPrefs, self.objectName(), preferences)

    def prepareStatusBar(self):
        self.progressBar = QtGui.QProgressBar()
        self.progressBar.setMaximumWidth(200)
        self.progressBar.setMaximumHeight(self.statusBar().height()/2)
        self.progressBarVisible = False

    def getProgressBar(self):
        if not self.progressBarVisible:
            self.progressBarVisible = True
            self.statusBar().addWidget(self.progressBar)
            self.progressBar.show()
        return self.progressBar

    def hideProgressBar(self):
        self.statusBar().removeWidget(self.progressBar)
        self.progressBarVisible = False

    def updateActionsState(self):
        application = QtGui.qApp
        loggedIn = bool(application.db) and application.userId is not None

        # Меню Сессия
        self.actLogin.setEnabled(not loggedIn)
        self.actLogout.setEnabled(loggedIn)
        self.actQuit.setEnabled(True)

        # Меню Настройки
        self.actPreferences.setEnabled(loggedIn)

        self.btnProcessDBF.setEnabled(loggedIn and self.dbfProcessed)
        self.btnImport.setEnabled(loggedIn and self.dbfProcessed)

    def setUserName(self, userName):
        title = u'Импорт COVID'
        if userName:
            self.setWindowTitle(title + u': ' + userName)
        else:
            self.setWindowTitle(title)

    def checkServiceName(self):
        self.btnProcessDBF.setEnabled(self.edtDBFFileName.text() != '')

    # @pyqtSignature('')
    # def on_tblDBF_popupMenuAboutToShow(self):
    #     index = self.tblDBF.currentIndex()
    #     if index.isValid():
    #         row = index.row()
    #         item = self.tblDBF.model()._items[row]
    #         eventId = forceInt(item.value('eventId'))
    #
    #     notEmpty = self.modelDBF.rowCount() > 0
    #     self.actEditActionEvent.setEnabled(notEmpty and eventId > 0)
    #
    # @pyqtSignature('')
    # def on_actEditActionEvent_triggered(self):
    #     index = self.tblDBF.currentIndex()
    #     if index.isValid():
    #         row = index.row()
    #         item = self.tblDBF.model()._items[row]
    #         eventId = forceInt(item.value('eventId'))
    #         if eventId > 0:
    #             editEvent(self, eventId)

    @pyqtSignature('QString')
    def on_edtDBFFileName_textChanged(self, text):
        self.checkServiceName()

    @pyqtSignature('')
    def on_btnSelectDBFFile_clicked(self):
        fileName = QtGui.QFileDialog.getOpenFileName(
            self, u'Укажите файл с данными', self.edtDBFFileName.text(), u'Файлы DBF (*.dbf)')
        if fileName != '':
            self.edtDBFFileName.setText(QDir.toNativeSeparators(fileName))
            self.checkServiceName()

    @pyqtSignature('')
    def on_btnProcessDBF_clicked(self):
        if not all([forceRef(QtGui.qApp.preferences.appPrefs.get('eventTypeId', None)),
                    forceRef(QtGui.qApp.preferences.appPrefs.get('eventTypeIdChild', None)),
                    forceRef(QtGui.qApp.preferences.appPrefs.get('orgId', None)),
                    forceRef(QtGui.qApp.preferences.appPrefs.get('personId', None)),
                    forceRef(QtGui.qApp.preferences.appPrefs.get('contractId', None)),
                    forceRef(QtGui.qApp.preferences.appPrefs.get('resultId', None)),
                    forceRef(QtGui.qApp.preferences.appPrefs.get('diagnosticResultId', None))]):
            buttons = QtGui.QMessageBox.Ok
            messageBox = QtGui.QMessageBox()
            messageBox.setWindowTitle(u'Внимание!')
            messageBox.setText(u'Перед загрузкой файла нужно заполнить настройки в умолчаниях!')
            messageBox.setStandardButtons(buttons)
            messageBox.setDefaultButton(QtGui.QMessageBox.Ok)
            return messageBox.exec_()
        QtGui.qApp.callWithWaitCursor(self, self.processDBF)

    @pyqtSignature('')
    def on_btnImport_clicked(self):
        QtGui.qApp.callWithWaitCursor(self, self.importData)

    def processDBF(self):
        encoding = ['cp1251', 'cp866'][forceInt(QtGui.qApp.preferences.appPrefs.get('encoding', 0))]
        self.recordList = []
        self.OMSPolicy = forceRef(QtGui.qApp.db.translate('rbPolicyType', 'code', '1', 'id'))
        self.oldPolicy = forceRef(QtGui.qApp.db.translate('rbPolicyKind', 'regionalCode', '1', 'id'))
        self.tempPolicy = forceRef(QtGui.qApp.db.translate('rbPolicyKind', 'regionalCode', '2', 'id'))
        self.newPolicy = forceRef(QtGui.qApp.db.translate('rbPolicyKind', 'regionalCode', '3', 'id'))
        fileName = forceString(self.edtDBFFileName.text())
        cnt = 0
        self.dbfProcessed = False
        if os.path.isfile(fileName):
            dbf = Dbf(fileName, readOnly=True, encoding=encoding)
            cnt += len(dbf)
            QtGui.qApp.startProgressBar(cnt)

            for rec in dbf:
                try:
                    QtGui.qApp.stepProgressBar()
                    QtGui.qApp.processEvents()
                    record = QtSql.QSqlRecord()
                    for name in CDBFModel.fieldList:
                        record.append(QtSql.QSqlField(name, CDBFModel.fieldTypeDict[name]))
                        record.setValue(name, toVariant(rec[name]))
                    record.append(QtSql.QSqlField('clientId', QVariant.Int))
                    record.append(QtSql.QSqlField('eventId', QVariant.Int))
                    record.append(QtSql.QSqlField('actionId', QVariant.Int))
                    record.setValue('clientId', toVariant(self.getClientId(record, addClient=False)))
                    record.setValue('eventId', toVariant(self.getEventId(record, addEvent=False)))
                    record.setValue('actionId', toVariant(self.getActionId(record, addAction=False)))
                    self.recordList.append(record)
                except:
                    pass
            self.dbfProcessed = True
            QtGui.qApp.stopProgressBar()
            dbf.close()
            self.modelDBF.setItems(self.recordList)
            self.updateActionsState()

    def importData(self):
        QtGui.qApp.startProgressBar(self.modelDBF.realRowCount())
        for item in self.modelDBF.items():
            try:
                QtGui.qApp.stepProgressBar()
                QtGui.qApp.processEvents()
                if forceInt(item.value('clientId')) <= 0:
                    item.setValue('clientId', self.getClientId(item))
                if forceInt(item.value('eventId')) <= 0:
                    item.setValue('eventId', self.getEventId(item))
                if forceInt(item.value('actionId')) <= 0:
                    item.setValue('actionId', self.getActionId(item))
            except:
                pass
        QtGui.qApp.stopProgressBar()

    def getClientId(self, item, addClient=True):
        lastName = forceString(item.value('FIO'))
        firstName = forceString(item.value('IMA'))
        patrName = forceString(item.value('OTCH'))
        sex = self.sexMap.get(forceString(item.value('POL')), 0)
        birthDate = forceDate(item.value('DATR'))
        clientId = self.clientMap.get((lastName, firstName, patrName, sex, pyDate(birthDate)), -1)
        if clientId == -1:
            db = QtGui.qApp.db
            clientTable = db.table('Client')
            cond = [clientTable['lastName'].eq(lastName),
                    clientTable['sex'].eq(sex),
                    clientTable['birthDate'].eq(birthDate),
                    clientTable['deleted'].eq(0)
                    ]
            if len(firstName) == 1 and len(patrName) == 1:
                cond.append(clientTable['firstName'].like(firstName + '...'))
                cond.append(clientTable['patrName'].like(patrName + '...'))
            else:
                cond.append(clientTable['firstName'].eq(firstName))
                cond.append(clientTable['patrName'].eq(patrName))

            record = db.getRecordEx(clientTable, 'id', where=cond, order='id desc')
            if not record and addClient:
                # добавляем пациента
                newRecord = clientTable.newRecord()
                newRecord.setValue('lastName', toVariant(lastName))
                newRecord.setValue('firstName', toVariant(firstName))
                newRecord.setValue('patrName', toVariant(patrName))
                newRecord.setValue('birthDate', toVariant(birthDate))
                newRecord.setValue('birthTime', toVariant(QTime()))
                newRecord.setValue('sex', toVariant(sex))
                newRecord.setValue('SNILS', toVariant(''))
                newRecord.setValue('birthGestationalAge', toVariant(0))
                newRecord.setValue('menarhe', toVariant(0))
                newRecord.setValue('menoPausa', toVariant(0))
                newRecord.setValue('notes', toVariant(
                    u'добавлен через importCOVID {0}'.format(QDateTime.currentDateTime().toString("dd.MM.yyyy hh:mm"))))
                clientId = db.insertRecord(clientTable, newRecord)

                # добавляем полис
                policyNumber = forceString(item.value('SPN'))
                if policyNumber:
                    policySerial = forceString(item.value('SPS'))
                    if policySerial:
                        policyKind = self.oldPolicy
                    elif len(policyNumber) == 9:
                        policyKind = self.tempPolicy
                    else:
                        policyKind = self.newPolicy
                    clientPolicyTable = db.table('ClientPolicy')
                    newRecord = clientPolicyTable.newRecord()
                    newRecord.setValue('client_id', toVariant(clientId))
                    # newRecord.setValue('insurer_id', toVariant(None))  # страховую не почем определять
                    newRecord.setValue('policyType_id', toVariant(self.OMSPolicy))
                    newRecord.setValue('policyKind_id', toVariant(policyKind))
                    newRecord.setValue('serial', toVariant(policySerial))
                    newRecord.setValue('number', toVariant(policyNumber))
                    newRecord.setValue('begDate', toVariant(item.value('0000-00-00')))  #
                    db.insertRecord(clientPolicyTable, newRecord)

                # добавляем УДЛ
                docNumber = forceString(item.value('N_DOC'))
                if docNumber:
                    docSerial = forceString(item.value('S_DOC'))

                    docType = forceInt(item.value('C_DOC'))
                    docType = 14 if docType == 0 else docType
                    docTypeId = self.documentTypeMap.get(docType, None)
                    if docTypeId is None:
                        rbDocumentTypeTable = db.table('rbDocumentType')
                        rec = db.getRecordEx(rbDocumentTypeTable, 'id', [rbDocumentTypeTable['group_id'].eq(1),
                                                                         rbDocumentTypeTable['regionalCode'].eq(
                                                                             docType)])
                        if rec:
                            docTypeId = forceRef(rec.value('id'))
                        self.documentTypeMap[docType] = docTypeId


                    clientDocumentTable = db.table('ClientDocument')
                    newRecord = clientDocumentTable.newRecord()
                    newRecord.setValue('client_id', toVariant(clientId))
                    newRecord.setValue('documentType_id', toVariant(docTypeId))
                    newRecord.setValue('serial', toVariant(docSerial))
                    newRecord.setValue('number', toVariant(docNumber))
                    newRecord.setValue('date', toVariant('0000-00-00'))  #
                    newRecord.setValue('origin', toVariant(''))
                    db.insertRecord(clientDocumentTable, newRecord)

            elif record:
                clientId = forceRef(record.value('id'))

            self.clientMap[(lastName, firstName, patrName, sex, pyDate(birthDate))] = clientId
        return clientId

    def getEventId(self, item, addEvent=True):
        db = QtGui.qApp.db
        tableOrg = db.table('Organisation')
        eventDate = forceDate(item.value('NAPR_D'))
        naprMO = forceString(item.value('NAPR_MO'))[:5]
        relegateOrg_id = None
        if naprMO:
            relegateOrg_id = self.mapOMSCodeToOrgId.get(naprMO, -1)
            if relegateOrg_id == -1:
                rec = db.getRecordEx(tableOrg, 'id', [tableOrg['infisCode'].eq(naprMO),
                                                      tableOrg['deleted'].eq(0),
                                                      tableOrg['isActive'].eq(1)])
                if rec:
                    relegateOrg_id = forceRef(rec.value('id'))
                else:
                    relegateOrg_id = None
                self.mapOMSCodeToOrgId['naprMO'] = relegateOrg_id

        clientId = forceRef(item.value('clientId'))
        age = calcAgeInYears(forceDate(item.value('DATR')), eventDate)
        eventTypeId = QtGui.qApp.preferences.appPrefs.get('eventTypeId', None) if age >= 18 else QtGui.qApp.preferences.appPrefs.get('eventTypeIdChild', None)
        eventOrder = forceInt(QtGui.qApp.db.translate('EventType', 'id', eventTypeId, 'EventType.order'))
        orgId = QtGui.qApp.preferences.appPrefs.get('orgId', None)
        contractId = QtGui.qApp.preferences.appPrefs.get('contractId', None)
        resultId = QtGui.qApp.preferences.appPrefs.get('resultId', None)
        diagnosticResultId = QtGui.qApp.preferences.appPrefs.get('diagnosticResultId', None)
        personId = QtGui.qApp.preferences.appPrefs.get('personId', None)
        specialityId = self.specialityMap.get(personId, None)
        if not specialityId:
            specialityId = forceRef(db.translate('Person', 'id', personId, 'speciality_id'))
            self.specialityMap[personId] = specialityId

        eventId = self.eventMap.get((clientId, eventTypeId, pyDate(eventDate)), -1)
        if eventId == -1:
            eventTable = db.table('Event')
            cond = [eventTable['client_id'].eq(clientId),
                    eventTable['execDate'].eq(eventDate),
                    eventTable['eventType_id'].eq(eventTypeId),
                    eventTable['deleted'].eq(0)
                    ]
            record = db.getRecordEx(eventTable, 'id', where=cond)
            if not record and addEvent:
                newRecord = eventTable.newRecord()
                newRecord.setValue('externalId', toVariant(''))
                newRecord.setValue('eventType_id', toVariant(eventTypeId))
                newRecord.setValue('org_id', toVariant(orgId))
                newRecord.setValue('client_id', toVariant(clientId))
                newRecord.setValue('contract_id', toVariant(contractId))
                newRecord.setValue('setDate', toVariant(eventDate))
                newRecord.setValue('setPerson_id', toVariant(personId))
                newRecord.setValue('execDate', toVariant(eventDate))
                newRecord.setValue('execPerson_id', toVariant(personId))
                newRecord.setValue('isPrimary', toVariant(1))  # Признак первичности 1-первичный
                newRecord.setValue('order', toVariant(eventOrder+1))
                newRecord.setValue('result_id', toVariant(resultId))
                newRecord.setValue('payStatus', toVariant(0))
                newRecord.setValue('note', toVariant(u'добавлено через importCOVID {0} Номер направления {1} от {2}'.format(QDateTime.currentDateTime().toString("dd.MM.yyyy hh:mm"),
                                                     forceString(item.value('SN')),
                                                     forceDate(eventDate).toString("dd.MM.yyyy")
                                                     )))
                newRecord.setValue('totalCost', toVariant(0))
                newRecord.setValue('isClosed', toVariant(1))
                if relegateOrg_id:
                    newRecord.setValue('relegateOrg_id', toVariant(relegateOrg_id))
                    newRecord.setValue('srcDate', toVariant(eventDate))
                    number = forceString(item.value('SN'))
                    newRecord.setValue('srcNumber', toVariant(number[:-6] + number[-4:]))
                eventId = db.insertRecord(eventTable, newRecord)

                # добавление диагноза
                diagnosisTable = db.table('Diagnosis')
                newRecord = diagnosisTable.newRecord()
                newRecord.setValue('client_id', toVariant(clientId))
                newRecord.setValue('diagnosisType_id', toVariant(1))  # заключительный
                mkb = forceString(item.value('MKB'))

                characterId = self.mapCharacters.get(mkb, -1)
                if characterId == -1:
                    characterId = None
                    codeIdList = getAvailableCharacterIdByMKB(mkb)
                    if codeIdList:
                        characterId = codeIdList[0]
                    self.mapCharacters[mkb] = characterId

                newRecord.setValue('character_id', toVariant(characterId))
                newRecord.setValue('MKB', toVariant(mkb))
                newRecord.setValue('MKBEx', toVariant(''))
                newRecord.setValue('morphologyMKB', toVariant(''))
                newRecord.setValue('endDate', toVariant(eventDate))
                diagnosisId = db.insertRecord(diagnosisTable, newRecord)

                diagnosticTable = db.table('Diagnostic')
                newRecord = diagnosticTable.newRecord()
                newRecord.setValue('event_id', toVariant(eventId))
                newRecord.setValue('diagnosis_id', toVariant(diagnosisId))
                newRecord.setValue('diagnosisType_id', toVariant(1))  # заключительный
                newRecord.setValue('character_id', toVariant(characterId))
                newRecord.setValue('sanatorium', toVariant(0))
                newRecord.setValue('hospital', toVariant(0))
                newRecord.setValue('speciality_id', toVariant(specialityId))
                newRecord.setValue('person_id', toVariant(personId))
                newRecord.setValue('result_id', toVariant(diagnosticResultId))
                newRecord.setValue('setDate', toVariant(eventDate))
                newRecord.setValue('endDate', toVariant(eventDate))
                newRecord.setValue('notes', toVariant(''))
                db.insertRecord(diagnosticTable, newRecord)
            elif record:
                eventId = forceRef(record.value('id'))
            self.eventMap[(clientId, eventTypeId, pyDate(eventDate))] = eventId
        return eventId

    def getActionId(self, item, addAction=True):
        db = QtGui.qApp.db
        eventDate = forceDate(item.value('NAPR_D'))
        eventId = forceRef(item.value('eventId'))
        actionId = None
        serviceCode = forceString(item.value('KUSL'))
        actionTypeId = self.actionTypeMap.get(serviceCode, None)
        personId = QtGui.qApp.preferences.appPrefs.get('personId', None)

        if not actionTypeId:
            actionTypeTable = db.table('ActionType')
            rbServiceTable = db.table('rbService')
            table = actionTypeTable.leftJoin(rbServiceTable, rbServiceTable['id'].eq(actionTypeTable['nomenclativeService_id']))
            cond = [rbServiceTable['infis'].eq(serviceCode),
                    actionTypeTable['showInForm'].eq(1),
                    actionTypeTable['deleted'].eq(0),
                    actionTypeTable['flatCode'].eq('importCOVID')
                    ]
            record = db.getRecordEx(table, actionTypeTable['id'], where=cond, order='ActionType.id desc')
            if record:
                actionTypeId = forceRef(record.value('id'))
                self.actionTypeMap[serviceCode] = actionTypeId

        if actionTypeId and eventId > 0:
            actionId = self.actionMap.get((eventId, actionTypeId), -1)
            if actionId == -1:
                actionTable = db.table('Action')
                cond = [actionTable['event_id'].eq(eventId),
                        actionTable['actionType_id'].eq(actionTypeId),
                        actionTable['deleted'].eq(0)]
                record = db.getRecordEx(actionTable, actionTable['id'], where=cond)
                if not record and addAction:
                    newRecord = actionTable.newRecord()
                    newRecord.setValue('actionType_id', toVariant(actionTypeId))
                    newRecord.setValue('event_id', toVariant(eventId))
                    newRecord.setValue('directionDate', toVariant(eventDate))
                    newRecord.setValue('status', toVariant(2))
                    newRecord.setValue('setPerson_id', toVariant(personId))
                    newRecord.setValue('begDate', toVariant(eventDate))
                    newRecord.setValue('endDate', toVariant(eventDate))
                    newRecord.setValue('note', toVariant(toVariant(u'добавлено через importCOVID {0}'.format(QDateTime.currentDateTime().toString("dd.MM.yyyy hh:mm")))))
                    newRecord.setValue('person_id', toVariant(personId))
                    newRecord.setValue('office', toVariant(''))
                    newRecord.setValue('amount', toVariant(1))
                    newRecord.setValue('payStatus', toVariant(0))
                    newRecord.setValue('account', toVariant(1))
                    newRecord.setValue('MKB', toVariant(''))
                    newRecord.setValue('morphologyMKB', toVariant(''))
                    newRecord.setValue('coordText', toVariant(''))
                    actionId = db.insertRecord(actionTable, newRecord)
                elif record:
                    actionId = forceRef(record.value('id'))
                self.actionMap[(eventId, actionTypeId)] = actionId
        return actionId


class CDBFModel(CRecordListModel):
    u"""Данные загруженные из дбф"""

    fieldList = (
        'SN', 'FIO', 'IMA', 'OTCH', 'NAPR_MO', 'SUMMA_I', 'NAPR_N', 'NAPR_D',
        'LPUNAME', 'MKB', 'KUSL', 'USLNAME', 'LAB', 'OTD', 'DOC', 'IS_VNESH',
        'POL', 'DATR', 'KAT', 'SPV', 'SPS', 'SPN', 'C_DOC', 'S_DOC', 'N_DOC')

    fieldTypeDict = {'SN': QVariant.Int, 'FIO': QVariant.String, 'IMA': QVariant.String, 'OTCH': QVariant.String,
                     'NAPR_MO': QVariant.String, 'SUMMA_I': QVariant.Double, 'NAPR_N': QVariant.String,
                     'NAPR_D': QVariant.Date, 'LPUNAME': QVariant.String, 'MKB': QVariant.String,
                     'KUSL': QVariant.String, 'USLNAME': QVariant.String, 'LAB': QVariant.String,
                     'OTD': QVariant.String, 'DOC': QVariant.String, 'IS_VNESH': QVariant.Int, 'POL': QVariant.String,
                     'DATR': QVariant.Date, 'KAT': QVariant.String, 'SPV': QVariant.Int, 'SPS': QVariant.String,
                     'SPN': QVariant.String, 'C_DOC': QVariant.Int, 'S_DOC': QVariant.String, 'N_DOC': QVariant.String}

    def __init__(self, parent):
        CRecordListModel.__init__(self, parent)
        for fieldName in CDBFModel.fieldList:
            self.addCol(CInDocTableCol(fieldName, fieldName, 30)).setReadOnly()
        self.addHiddenCol(CInDocTableCol('clientId', 'clientId', 30))
        self.addHiddenCol(CInDocTableCol('eventId', 'eventId', 30))
        self.addHiddenCol(CInDocTableCol('actionId', 'actionId', 30))

    def data(self, index, role=Qt.DisplayRole):
        row = index.row()
        item = self._items[row]
        if role == Qt.BackgroundColorRole:
            if forceInt(item.value('clientId')) <= 0:
                return QVariant(QtGui.QBrush(QtGui.QColor(255, 94, 94)))
            elif forceRef(item.value('actionId')) > 0:
                return QVariant(QtGui.QBrush(QtGui.QColor(94, 255, 94)))
        return CRecordListModel.data(self, index, role)


if __name__ == '__main__':
    parser = OptionParser(usage="usage: %prog [options]")
    parser.add_option('--gc-debug',
                      dest='gcDebug',
                      help='gc debug flags, chars S(stat), C(collectable), U(uncollectable), I(instances), '
                           'O(objects), for details see gc.set_debug',
                      metavar='[S][C][U][I][O]',
                      default=''
                      )
    parser.add_option('--gc-threshold',
                      dest='gcThreshold',
                      help='gc thresholds list, see gc.set_threshold ',
                      metavar='threshold0[,threshold1[,threshold2]]',
                      default=''
                      )
    parser.add_option('--version',
                      dest='version',
                      help='print version and exit',
                      action='store_true',
                      default=False)
    (options, args) = parser.parse_args()

    if options.version:
        print '%s v.0.1' % (sys.argv[0] if sys.argv else '')
    else:
        gcDebug = parseGCDebug(options.gcDebug)
        gcThreshold = parseGCThreshold(options.gcThreshold)
        if gcDebug:
            gc.set_debug(gcDebug)
            print 'debug set to ', gcDebug
        if gcThreshold:
            gc.set_threshold(*gcThreshold)
            print 'threshold set to ', gcThreshold

        app = CMyApp(sys.argv)
        stdTtranslator = QtCore.QTranslator()
        path = os.path.join(os.path.realpath(sys.argv[0].split('appendix')[0]), 'i18n', 'std_ru.qm')
        stdTtranslator.load(path)
        app.installTranslator(stdTtranslator)

        QtGui.qApp = app
        app.applyDecorPreferences()  # Надеюсь, что это поможет немного сэкономить при создании главного окна
        mainWindow = CMainWindow()
        app.mainWindow = mainWindow
        app.applyDecorPreferences()  # Применение максимизации/полноэкранного режима к главному окну

        if app.preferences.dbAutoLogin:
            mainWindow.actLogin.activate(QtGui.QAction.Trigger)
        mainWindow.show()
        res = app.exec_()
        mainWindow.savePreferences()
        app.preferences.save()
        app.closeDatabase()
        app.doneTrace()
        QtGui.qApp = None
