#!/usr/bin/env python
# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2022 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################


import codecs
import gc
import locale
import os
import os.path
import shutil
import sys
import tempfile
import traceback
from optparse import OptionParser

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import QDir, qInstallMsgHandler, Qt, QVariant, QDateTime, QDate, pyqtSignature, QTime

from Users.Login import CLoginDialog
from Users.UserInfo import CUserInfo, CDemoUserInfo
from Users.Tables import tblUser, usrLogin, usrPassword, usrRetired, demoUserName
from importCovid import CCovidImportDialog
from importDispSettings import CDispSettingsImportDialog
from library import database
from library.Preferences import CPreferences
from library.Utils import forceString, forceBool, forceRef, forceInt, anyToUnicode, getPrefString, getPrefBool, getPref, \
    setPref, nameCase

import Exchange.AttachService as AttachService

from preferences.connection import CConnectionDialog
from preferences.decor import CDecorDialog

from Progress import CProgressDialog
from importPrik import CPrikImportDialog
from importSnils import CSnilsImportDialog
from importMedpol import CMedpolImportDialog
from Ui_importRegistry import Ui_MainWindow
from library.Utils import firstMonthDay

class CMyApp(QtGui.QApplication):
    __pyqtSignals__ = ('dbConnectionChanged(bool)',
                       'currentUserIdChanged()',
                      )

    def __init__(self, args, demoModeRequest):
        QtGui.QApplication.__init__(self, args)
        self.logDir = os.path.join(unicode(QDir.toNativeSeparators(QDir.homePath())), '.samson-vista')
        self.oldMsgHandler = qInstallMsgHandler(self.msgHandler)
        self.oldEexceptHook = sys.excepthook
        sys.excepthook = self.logException
        self.traceActive = True
        self.homeDir= None
        self.saveDir= None
        self.userId = None
        self.userSpecialityId = None
        self.userOrgStructureId = None
        self.db     = None
        self.mainWindow = None
        self.preferences = CPreferences('r23ImportReestr.ini')
        self.preferences.load()
        self.preferencesDir = self.preferences.getDir()
        self.registerDocumentTables()
        self._currentClientId = None
        self.userInfo = None
        self.demoModeRequested = True


    def getGlobalPreference(self, code):
        return None


    def documentEditor(self):
        return forceString(QtGui.qApp.preferences.appPrefs.get('documentEditor', ''))

    def enableFastPrint(self):
        return forceBool(self.preferences.appPrefs.get('enableFastPrint', False))

    def doneTrace(self):
        self.traceActive = False
        qInstallMsgHandler(self.oldMsgHandler)
        sys.excepthook = self.oldEexceptHook


    def applyDecorPreferences(self):
        self.setStyle(self.preferences.decorStyle)
        if self.preferences.decorStandardPalette:
            self.setPalette(self.style().standardPalette())
        if self.mainWindow:
            state = Qt.WindowNoState
            if self.preferences.decorMaximizeMainWindow:
                state |= Qt.WindowMaximized
            if self.preferences.decorFullScreenMainWindow:
                state |= Qt.WindowFullScreen
            self.mainWindow.setWindowState(state)


    def registerDocumentTables(self):
        database.registerDocumentTable('Account')
        database.registerDocumentTable('Action')
        database.registerDocumentTable('ActionProperty')
        database.registerDocumentTable('ActionPropertyTemplate')
        database.registerDocumentTable('ActionTemplate')
        database.registerDocumentTable('ActionType')
        database.registerDocumentTable('Address')
        database.registerDocumentTable('AddressAreaItem')
        database.registerDocumentTable('AddressHouse')
        database.registerDocumentTable('Bank')
        database.registerDocumentTable('CalendarExceptions')
        database.registerDocumentTable('Client')
        database.registerDocumentTable('ClientAddress')
        database.registerDocumentTable('ClientAllergy')
        database.registerDocumentTable('ClientAttach')
        database.registerDocumentTable('ClientContact')
        database.registerDocumentTable('ClientIdentification')
        database.registerDocumentTable('ClientIntoleranceMedicament')
        database.registerDocumentTable('ClientDocument')
        database.registerDocumentTable('ClientPolicy')
        database.registerDocumentTable('ClientSocStatus')
        database.registerDocumentTable('ClientWork')
        database.registerDocumentTable('Contract')
        database.registerDocumentTable('Diagnosis')
        database.registerDocumentTable('Diagnostic')
        database.registerDocumentTable('Event')
        database.registerDocumentTable('EventType')
        database.registerDocumentTable('InformerMessage')
        database.registerDocumentTable('Licence')
        database.registerDocumentTable('Organisation')
        database.registerDocumentTable('OrgStructure')
        database.registerDocumentTable('Person')
        database.registerDocumentTable('SocStatus')
        database.registerDocumentTable('TempInvalid')
        database.registerDocumentTable('Visit')


    def getHomeDir(self):
        if not self.homeDir:
            homeDir = os.path.expanduser('~')
            if homeDir == '~':
                homeDir = unicode(QDir.homePath())
            if isinstance(homeDir, str):
                homeDir = unicode(homeDir, locale.getpreferredencoding())
            self.homeDir = homeDir
        return self.homeDir


    def getSaveDir(self):
        self.saveDir = forceString(self.preferences.appPrefs.get('saveDir', QVariant()))
        if not self.saveDir:
            self.saveDir = self.getHomeDir()
        return self.saveDir


    def setSaveDir(self, path):
#        mode = os.stat(path)[ST_MODE]
#        if if S_ISDIR(mode):
        saveDir = os.path.dirname(unicode(path))
        if saveDir and self.saveDir != saveDir:
            self.preferences.appPrefs['saveDir'] = QVariant(saveDir)


    def getTemplateDir(self):
        result = forceString(self.preferences.appPrefs.get('templateDir', None))
        if not result:
            result = os.path.join(self.logDir, 'templates')
        return result


    def getTmpDir(self, suffix=''):
        return unicode(tempfile.mkdtemp('','samson_%s_'%suffix), locale.getpreferredencoding())


    def removeTmpDir(self, dir):
        try:
            shutil.rmtree(dir, False)
        except:
            self.logCurrentException()


#    def setTemplateDir(self, path):
#        self.preferences.appPrefs.setdefault('templateDir', QVariant(path))


    def log(self, title, message, stack=None):
        try:
            if not os.path.exists(self.logDir):
                os.makedirs(self.logDir)
            logFile = os.path.join(self.logDir, 'error.log')
            timeString = unicode(QDateTime.currentDateTime().toString(Qt.SystemLocaleDate))
            logString = u'%s\n%s: %s(%s)\n' % ('='*72, timeString, title, message)
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


    def logException(self, exceptionType, exceptionValue, exceptionTraceback):
        title = repr(exceptionType)
        message = unicode(exceptionValue)
        self.log(title, message, traceback.extract_tb(exceptionTraceback))
        sys.__excepthook__(exceptionType, exceptionValue, exceptionTraceback)


    def logCurrentException(self):
        self.logException(*sys.exc_info())


    def msgHandler(self, type, msg):
        if type == 0: # QtMsgType.QtDebugMsg:
            typeName = 'QtDebugMsg'
        elif type == 1: # QtMsgType.QtWarningMsg:
            typeName = 'QtWarningMsg'
        elif type == 2: # QtMsgType.QtCriticalMsg:
            typeName = 'QtCriticalMsg'
        elif type == 3: # QtFatalMsg
            typeName = 'QtFatalMsg'
        else:
            typeName = 'QtUnknownMsg'

        self.log( typeName, msg, traceback.extract_stack()[:-1])
#        print typeName, msg


    def openDatabase(self):
        self.db = None
        self.db = database.connectDataBase(self.preferences.dbDriverName,
                                     self.preferences.dbServerName,
                                     self.preferences.dbServerPort,
                                     self.preferences.dbDatabaseName,
                                     self.preferences.dbUserName,
                                     self.preferences.dbPassword)
        self.emit(QtCore.SIGNAL('dbConnectionChanged(bool)'), True)


    def closeDatabase(self):
        if self.db:
            self.db.close()
            self.db = None
            self.emit(QtCore.SIGNAL('dbConnectionChanged(bool)'), False)


    def notify(self, receiver, event):
        try:
#            report = ["notify:: receiver.type=",unicode(type(receiver))," receiver.name=", unicode(receiver.objectName())," event.type=",unicode(type(event)), "event.type()=", unicode(event.type())]
#            print >>sys.stderr, ("".join(report)).encode('cp866')
            return QtGui.QApplication.notify(self, receiver, event)
        except Exception, e:
            if self.traceActive:
                self.logCurrentException()
                widget = self.activeModalWidget()
                if widget is None:
                    widget = self.mainWindow
                QtGui.QMessageBox.critical( widget,
                                            u'Произошла ошибка',
                                            unicode(e),
                                            QtGui.QMessageBox.Close)
            return False
        except:
            return False


    def call(self, widget, func, params = ()):
        try:
            return True, func(*params)
        except IOError, e:
            msg=''
            if hasattr(e, 'filename'):
                msg = u'%s:\n[Errno %s] %s' % (e.filename, e.errno, anyToUnicode(e.strerror))
            else:
                msg = u'[Errno %s] %s' % (e.errno, anyToUnicode(e.strerror))
            QtGui.QMessageBox.critical(widget,
                u'Произошла ошибка ввода-вывода', msg, QtGui.QMessageBox.Close)
        except Exception, e:
            self.logCurrentException()
            widget = widget or self.activeModalWidget() or self.mainWindow
            QtGui.QMessageBox.critical( widget,
                                        u'Произошла ошибка',
                                        unicode(e),
                                        QtGui.QMessageBox.Close)
        return False, None


    def callWithWaitCursor(self, widget, func, *params, **kwparams):
        self.setOverrideCursor(QtGui.QCursor(Qt.WaitCursor))
        try:
            return func(*params, **kwparams)
        finally:
            self.restoreOverrideCursor()

    def setWaitCursor(self):
        self.setOverrideCursor(QtGui.QCursor(Qt.WaitCursor))

    def demoModePosible(self):
        try:
            tableUser = self.db.table(tblUser)
            record = self.db.getRecordEx(tableUser, [usrPassword, usrRetired], tableUser[usrLogin].eq(demoUserName))
            return not record or (not forceString(record.value(usrPassword)) and not forceBool(record.value(usrRetired)))
        except:
            pass
        return False


    def setUserId(self, userId, demoMode = False):
        self.userId = userId
        record = self.db.getRecord('Person', ['speciality_id', 'orgStructure_id'], userId) if userId else None
        if record:
            self.userSpecialityId = forceRef(record.value('speciality_id'))
            self.userOrgStructureId = forceRef(record.value('orgStructure_id'))
        else:
            self.userSpecialityId = None
            self.userOrgStructureId = None
        self.demoMode = demoMode
        if demoMode:
            self.userInfo = CDemoUserInfo(userId)
        else:
            if userId:
                self.userInfo = CUserInfo(userId)
            else:
                self.userInfo = None
        self.emit(QtCore.SIGNAL('currentUserIdChanged()'))


    def userName(self):
        if self.userInfo:
#            orgId = self.currentOrgId()
#            orgInfo = getOrganisationInfo(orgId)
#            if not orgInfo:
#                QtGui.qApp.preferences.appPrefs['orgId'] = QVariant()
#            shortName = orgInfo.get('shortName', u'ЛПУ в настройках не указано!')
            return u'%s (%s)' % (self.userInfo.name(), self.userInfo.login())
        else:
            return ''


    def userHasRight(self, right):
        return self.userInfo is not None and self.userInfo.hasRight(right)


    def userHasAnyRight(self, rights):
        return self.userInfo is not None and self.userInfo.hasAnyRight(rights)



    def defaultKLADR(self):
        # возвращает код по умолчанию
        result = forceString(self.preferences.appPrefs.get('defaultKLADR', ''))
        if not result:
            result = '2300000000000'
        return result



# #############################################################


class CMainWindow(QtGui.QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
#        self.registryFileName = 'reestr.dbf'

#        self.accountingSystemId  = None
#        self.policyTypeId        = None
#        self.childDocumentTypeId = None
#        self.adultDocumentTypeId = None
#        self.contactTypeId       = None

        self.loadPreferences()
        self.prbAttachImport.setVisible(False)
        self.attachImportRunning = False
        self.edtImportAttachActDate.setDate(firstMonthDay(QDate.currentDate()))

    def loadPreferences(self):
        preferences = getPref(QtGui.qApp.preferences.windowPrefs, self.objectName(), {})
        geometry = getPref(preferences, 'geometry', None)
        if type(geometry) == QVariant and geometry.type() == QVariant.ByteArray and not geometry.isNull():
            self.restoreGeometry(geometry.toByteArray())
        state = getPref(preferences, 'state', None)
        if type(state) == QVariant and state.type() == QVariant.ByteArray and not geometry.isNull():
            self.restoreState(state.toByteArray())

        appPreferences = QtGui.qApp.preferences.appPrefs
        self.edtRBDirName.setText(getPrefString(appPreferences, 'rbDirName', ''))
        self.edtMainDataFileName.setText(getPrefString(appPreferences, 'mainDataFileName', ''))
        self.edtServiceFileName.setText(getPrefString(appPreferences, 'serviceFileName', ''))
        self.chkCopyToActionType.setChecked(getPrefBool(appPreferences, 'copyToActionType', False))
        self.chkImportClients.setChecked(getPrefBool(appPreferences, 'importClients', True))
        self.edtMainDataFileName.setEnabled(self.chkImportClients.isChecked())
        self.edtPrikFileName.setText(getPrefString(appPreferences, 'prikFileName', ''))
        self.edtSnilsFileName.setText(getPrefString(appPreferences, 'snilsFileName', ''))
        self.edtMedpolFileName.setText(getPrefString(appPreferences, 'medpolFileName', ''))
        self.edtAttachURL.setText(getPrefString(appPreferences, 'attachURL', ''))
        self.checkName()
        self.checkServiceName()


    def savePreferences(self):
        preferences = {}
        setPref(preferences,'geometry',QVariant(self.saveGeometry()))
        setPref(preferences,'state', QVariant(self.saveState()))
        setPref(QtGui.qApp.preferences.windowPrefs, self.objectName(), preferences)

        appPreferences = QtGui.qApp.preferences.appPrefs
        setPref(appPreferences, 'rbDirName', QVariant(self.edtRBDirName.text()))
        setPref(appPreferences, 'mainDataFileName', QVariant(self.edtMainDataFileName.text()))
        setPref(appPreferences, 'serviceFileName', QVariant(self.edtServiceFileName.text()))
        setPref(appPreferences, 'copyToActionType', QVariant(self.chkCopyToActionType.isChecked()))
        setPref(appPreferences, 'importClients', QVariant(self.chkImportClients.isChecked()))
        setPref(appPreferences, 'prikFileName', QVariant(self.edtPrikFileName.text()))
        setPref(appPreferences, 'snilsFileName', QVariant(self.edtSnilsFileName.text()))
        setPref(appPreferences, 'medpolFileName', QVariant(self.edtMedpolFileName.text()))
        setPref(appPreferences, 'attachURL', QVariant(self.edtAttachURL.text()))
        #setPref(appPreferences, 'fillSpecialityRegionalCode', QVariant(self.chkFillSpecialityRegionalCode.isChecked()))


    def setUserName(self, userName):
        title = u'Импорт реестра застрахованного населения для Краснодарского края'
        if userName:
            self.setWindowTitle(title + u': '+ userName)
        else:
            self.setWindowTitle(title)



    def updateStatus(self):
#        self.btnImport.setEnabled(self.registryOk and self.orgsOk and self.insurersOk)
        pass


    def checkName(self):
        self.btnImport.setEnabled(
            self.edtRBDirName.text()!='' and
            (self.edtMainDataFileName.text()!='' or not self.chkImportClients.isChecked()))


    def checkServiceName(self):
        self.btnImportService.setEnabled(self.edtServiceFileName.text() != '')


    def checkPrikName(self):
        self.btnImportPrik.setEnabled(self.edtPrikFileName.text() != '')


    def checkSnilsName(self):
        self.btnImportSnils.setEnabled(self.edtSnilsFileName.text() != '')

    def checkMedpolName(self):
        self.btnImportMedpol.setEnabled(self.edtMedpolFileName.text() != '')

    def checkDispSettingsName(self):
        self.btnImportDispSettings.setEnabled(self.edtDispSettingsFileName.text() != '')

    def checkCovidName(self):
        self.btnImportCovidReestr.setEnabled(self.edtCovidReestrFileName.text() != '')

    def checkAttachURL(self):
        isEnabled = self.edtAttachURL.text() != ''
        self.btnImportAttach.setEnabled(isEnabled)
        self.btnImportAttachAct.setEnabled(isEnabled)
        self.btnImportDeattachMO.setEnabled(isEnabled)

    def getServiceStandartFileName(self):
        return unicode(self.edtRBDirName.text()) + '/SPR19.DBF'


    def getMKBStandartFileName(self):
        return unicode(self.edtRBDirName.text()) + '/SPR38.DBF'


    def getMedicamentFileName(self):
        return unicode(self.edtRBDirName.text()) + '/SPR53.DBF'


    def getMedicamentStandartFileName(self):
        return unicode(self.edtRBDirName.text()) + '/SPR54.DBF'


    def importAttachment(self, actDate = None):
        if self.attachImportRunning:
            self.attachImportCanceled = True
            return

        if actDate:
            serviceMethodType = 2
            serviceMethod = 'getAttachListByRangeAct'
            params = {'date': forceString(actDate.toString('yyyy-MM-dd'))}
            self.btnImportAttachAct.setText(u'Отмена')
            self.btnImportAttach.setEnabled(False)
        else:
            serviceMethodType = 0
            serviceMethod = 'getAttachListByRange'
            params = {}
            self.btnImportAttach.setText(u'Отмена')
            self.btnImportAttachAct.setEnabled(False)

        self.edtImportAttachActDate.setEnabled(False)
        self.btnImportDeattachMO.setEnabled(False)
        self.attachImportRunning = True
        self.attachImportCanceled = False
        self.prbAttachImport.setMaximum(0)
        self.prbAttachImport.setValue(0)
        self.prbAttachImport.setVisible(True)
        self.lblAttachImport.setVisible(False)
        self.edtAttachURL.setVisible(False)


        try:
            url = forceString(self.edtAttachURL.text())
            db = QtGui.qApp.db
            db.transaction()
            db.query('delete from soc_attachments where coalesce(serviceMethod, 0) = %d' % serviceMethodType)
            soc_attachments = db.table('soc_attachments')
            startId = 1
            while startId != -1:
                if self.attachImportCanceled:
                    break
                self.prbAttachImport.setFormat(u'Получение данных с сервиса')
                QtGui.qApp.processEvents()
                try:
                    params['startId'] = startId
                    response = AttachService.callService(serviceMethod, params, url, timeout=600)
                except Exception, e:
                    raise Exception(u'Ошибка при запросе к сервису %s:\nМетод getAttachListByRange, startId = %d\n%s' % (url, startId, unicode(e)))

                attachList = response['attachlist']
                self.prbAttachImport.setMaximum(self.prbAttachImport.maximum() + len(attachList))
                self.prbAttachImport.setFormat(u'%v из %m')
                recordList = []
                for attachment in attachList:
                    if self.attachImportCanceled:
                        break
                    self.prbAttachImport.setValue(self.prbAttachImport.value() + 1)
                    QtGui.qApp.processEvents()
                    person = attachment['person']
                    info = attachment['info']
                    record = soc_attachments.newRecord()
                    for fieldName in ['lastName', 'firstName', 'patrName', 'sex', 'birthDate', 'policyType',
                                      'policySerial', 'policyNumber', 'enp', 'tsod', 'regArea', 'regCity',
                                      'regLocal', 'regStreet', 'regHouse', 'regBuilding', 'regAppartment',
                                      'livArea', 'livCity', 'livLocal', 'livStreet', 'livHouse', 'livBuilding',
                                      'livAppartment', 'attachOrigin', 'phone', 'udlSerial', 'udlNumber',
                                      'udlType', 'snils', 'smo','client_id']:
                        record.setValue(fieldName, nameCase(person.get(fieldName)) if fieldName in ['lastName', 'firstName', 'patrName'] and person.get(fieldName) else person.get(fieldName))
                    if info:
                        info = info[0]
                        for fieldName in ['date', 'snils', 'area', 'mo', 'type']:
                            record.setValue('attach_' + fieldName, actDate if actDate and fieldName == 'date' else info.get(fieldName))
                    record.setValue('serviceMethod', serviceMethodType)
                    recordList.append(record)
                    if len(recordList) == 1000:
                        db.insertRecordList(soc_attachments, recordList)
                        recordList = []
                if recordList:
                    db.insertRecordList(soc_attachments, recordList)

                startId = response['nextId']

            if self.attachImportCanceled:
                db.rollback()
            else:
                db.commit()
                QtGui.QMessageBox.information(
                    self,
                    u'Импорт регистра прикрепленного населения',
                    u'Импорт успешно завершен, загружено %d записей' % self.prbAttachImport.maximum(),
                    QtGui.QMessageBox.Ok)
        except Exception, e:
            db.rollback()
            QtGui.QMessageBox.critical(
                self,
                u'Ошибка при импорте регистра прикрепленного населения',
                unicode(e),
                QtGui.QMessageBox.Close)
        self.prbAttachImport.setVisible(False)
        self.lblAttachImport.setVisible(True)
        self.edtAttachURL.setVisible(True)
        self.btnImportAttach.setText(u'Импорт')
        self.btnImportAttachAct.setText(u'Импорт')
        self.attachImportRunning = False
        self.btnImportAttach.setEnabled(True)
        self.btnImportAttachAct.setEnabled(True)
        self.edtImportAttachActDate.setEnabled(True)
        self.btnImportDeattachMO.setEnabled(True)

    @QtCore.pyqtSignature('int')
    def on_chkImportClients_stateChanged(self, state):
        self.checkName()


    @pyqtSignature('QString')
    def on_edtRBDirName_textChanged(self, text):
        self.checkName()


    @pyqtSignature('QString')
    def on_edtMainDataFileName_textChanged(self, text):
        self.checkName()


    @pyqtSignature('QString')
    def on_edtServiceFileName_textChanged(self, text):
        self.checkServiceName()


    @pyqtSignature('QString')
    def on_edtPrikFileName_textChanged(self, text):
        self.checkPrikName()


    @pyqtSignature('QString')
    def on_edtSnilsFileName_textChanged(self, text):
        self.checkSnilsName()


    @pyqtSignature('QString')
    def on_edtMedpolFileName_textChanged(self, text):
        self.checkMedpolName()

    @pyqtSignature('QString')
    def on_edtDispSettingsFileName_textChanged(self, text):
        self.checkDispSettingsName()

    @pyqtSignature('QString')
    def on_edtAttachURL_textChanged(self, text):
        self.checkAttachURL()

    @pyqtSignature('')
    def on_btnSelectRBDir_clicked(self):
        dirName = forceString(QtGui.QFileDialog.getExistingDirectory(
            self, u'Укажите каталог', self.edtRBDirName.text()))
        if dirName != '':
            self.edtRBDirName.setText(QDir.toNativeSeparators(dirName))
            self.checkName()


    @pyqtSignature('')
    def on_btnSelectServiceFile_clicked(self):
        fileName = QtGui.QFileDialog.getOpenFileName(
            self, u'Укажите файл с данными', self.edtServiceFileName.text(), u'Файлы DBF (*.dbf)')
        if fileName != '':
            self.edtServiceFileName.setText(QDir.toNativeSeparators(fileName))
            self.checkServiceName()


    @pyqtSignature('')
    def on_btnSelectPrikFile_clicked(self):
        fileName = QtGui.QFileDialog.getOpenFileName(
            self, u'Укажите файл с данными', self.edtPrikFileName.text(), u'Файлы DBF (*.dbf)')
        if fileName != '':
            self.edtPrikFileName.setText(QDir.toNativeSeparators(fileName))
            self.checkPrikName()


    @pyqtSignature('')
    def on_btnSelectSnilsFile_clicked(self):
        fileName = QtGui.QFileDialog.getOpenFileName(
            self, u'Укажите архив с данными', self.edtSnilsFileName.text(), u'Файлы RAR (*.rar)')
        if fileName != '':
            self.edtSnilsFileName.setText(QDir.toNativeSeparators(fileName))
            self.checkSnilsName()

    @pyqtSignature('')
    def on_btnSelectMedpolFile_clicked(self):
        fileName = QtGui.QFileDialog.getOpenFileName(
            self, u'Укажите архив с данными', self.edtMedpolFileName.text(), u'Файлы ZIP (*.zip)')
        if fileName != '':
            self.edtMedpolFileName.setText(QDir.toNativeSeparators(fileName))
            self.checkMedpolName()

    @pyqtSignature('')
    def on_btnSelectImportDispFile_clicked(self):
        fileName = QtGui.QFileDialog.getOpenFileName(
            self, u'Укажите архив с данными', self.edtDispSettingsFileName.text(), u'Файлы ZIP (*.zip)')
        if fileName != '':
            self.edtDispSettingsFileName.setText(QDir.toNativeSeparators(fileName))
            self.checkDispSettingsName()

    @pyqtSignature('')
    def on_btnSelectImportCovidReestrFile_clicked(self):
        fileName = QtGui.QFileDialog().getOpenFileName(self, u'Укажите файл с данными',
                self.edtCovidReestrFileName.text(), u'Файлы xlsm (*.xlsx)')
        if fileName != '':
            self.edtCovidReestrFileName.setText(QDir.toNativeSeparators(fileName))
            self.checkCovidName()

    @pyqtSignature('')
    def on_btnSelectMainDataFile_clicked(self):
        fileName = QtGui.QFileDialog.getOpenFileName(
            self, u'Укажите файл с данными', self.edtMainDataFileName.text(), u'Файлы DBF (*.dbf)')
        if fileName != '':
            self.edtMainDataFileName.setText(QDir.toNativeSeparators(fileName))
            self.checkName()


    @pyqtSignature('')
    def on_btnImportService_clicked(self):
        def checkConstrain(cond, message):
            if not cond:
                QtGui.QMessageBox.critical(
                    self,
                    u'Импорт невозможен',
                    message,
                    QtGui.QMessageBox.Close)
            return cond

        process = CProgressDialog(self)

        parentGroup = None
#        if self.chkCopyToActionType.isChecked():
#            db = QtGui.qApp.db
#            record = db.getRecordEx('ActionType', 'id', 'code="r23" AND class="3"', 'id')
#            if record:
#                parentGroup = forceRef(record.value(0))
#
#            if not (checkConstrain(parentGroup,
#                u'В справочнике типов действий (ActionType)'
#                u' отсутствует запись с кодом r23, класс "прочее"'
#                u' (Группа для мед. услуг Краснодарского края)')):
#                return

        process.setOptions(parentGroup, self.chkCopyToMes.isChecked(), self.chkRecognizeNomenclature.isChecked(), self.chkfillEIS.isChecked())

        QtGui.qApp.call(self, process.exec_, (True, ))


    @pyqtSignature('')
    def on_btnImportPrik_clicked(self):
        process = CPrikImportDialog(self)
        QtGui.qApp.call(self, process.exec_, ())


    @pyqtSignature('')
    def on_btnImportSnils_clicked(self):
        process = CSnilsImportDialog(self)
        QtGui.qApp.call(self, process.exec_, ())

    @pyqtSignature('')
    def on_btnImportMedpol_clicked(self):
        process = CMedpolImportDialog(self)
        QtGui.qApp.call(self, process.exec_, ())

    @pyqtSignature('')
    def on_btnImportDispSettings_clicked(self):
        process = CDispSettingsImportDialog(self)
        QtGui.qApp.call(self, process.exec_, ())

    @pyqtSignature('')
    def on_btnImportCovidReestr_clicked(self):
        process = CCovidImportDialog(self)
        QtGui.qApp.call(self, process.exec_, ())


    @pyqtSignature('')
    def on_btnImportAttach_clicked(self):
        self.importAttachment()

    @pyqtSignature('')
    def on_btnImportAttachAct_clicked(self):
        self.importAttachment(self.edtImportAttachActDate.date())

    def setTFOMSButons(self, enabled):
        self.btnImportAttach.setEnabled(enabled)
        self.btnImportAttachAct.setEnabled(enabled)
        self.edtImportAttachActDate.setEnabled(enabled)
        self.btnImportDeattachMO.setEnabled(enabled)

    @pyqtSignature('')
    def on_btnImportDeattachMO_clicked(self):
        url = forceString(self.edtAttachURL.text())
        self.setTFOMSButons(False)

        try:
            response = AttachService.callService("getQueryForDeAttachForMO",
                                                 {'date': forceString(QDate.currentDate().toString('yyyy-MM-dd'))},
                                                 url, timeout=600)
            QtGui.QMessageBox.information(
                self,
                u'Импорт запросов на открепление из других МО',
                u'Импорт проведен успешно!\nЗагружено %d записей' % response["count"],
                QtGui.QMessageBox.Ok)
        except Exception, e:
            QtGui.QMessageBox.critical(
                self,
                u'Ошибка при импорте запросов на открепление из других МО',
                unicode(e),
                QtGui.QMessageBox.Close)
        self.setTFOMSButons(True)

    @pyqtSignature('')
    def on_btnUpdateParusPerson_clicked(self):
        try:
            QtGui.qApp.setWaitCursor()
            self.btnUpdateParusPerson.setEnabled(False)
            QtGui.qApp.processEvents()

            result = AttachService.updatePersonParus()
            QtGui.qApp.restoreOverrideCursor()
            if result['ok']:
                QtGui.QMessageBox.information(
                    self,
                    u'Импорт успешно завершен',
                    u'Импорт успешно завершен, загружено %d записей' % result['count'],
                    QtGui.QMessageBox.Ok)
            else:
                QtGui.QMessageBox.critical(
                    self,
                    u'Ошибка',
                    result['message'],
                    QtGui.QMessageBox.Close)
        except Exception, e:
            QtGui.qApp.restoreOverrideCursor()
            QtGui.QMessageBox.critical(
                self,
                u'Ошибка',
                unicode(e),
                QtGui.QMessageBox.Close)
        finally:
            self.btnUpdateParusPerson.setEnabled(True)
            
            
    @pyqtSignature('')
    def on_btnImportClient_clicked(self):
        try:
            QtGui.qApp.setWaitCursor()
            self.btnImportClient.setEnabled(False)
            QtGui.qApp.processEvents()
            query = QtGui.qApp.db.query('CALL ImportSoc_Attachment(%d, @count)' % self.cbSetAttach.isChecked())
            query = QtGui.qApp.db.query('select @count as cnt')
            query.first()
            result = query.record()
            QtGui.qApp.restoreOverrideCursor()
            QtGui.QMessageBox.information(
                self,
                u'Импорт успешно завершен',
                u'Импорт успешно завершен, загружено %d записей' % forceInt(result.value('cnt')),
                QtGui.QMessageBox.Ok)
        except Exception, e:
            QtGui.qApp.restoreOverrideCursor()
            QtGui.QMessageBox.critical(
                self,
                u'Ошибка',
                unicode(e),
                QtGui.QMessageBox.Close)
        finally:
            self.btnImportClient.setEnabled(True)
            

    @pyqtSignature('QDate')
    def on_edtImportAttachActDate_dateChanged(self):
        self.edtImportAttachActDate.setDate(
            firstMonthDay(self.edtImportAttachActDate.date())
        )


    @pyqtSignature('')
    def on_btnImport_clicked(self):
        def checkConstrain(cond, message):
            if not cond:
                QtGui.QMessageBox.critical(
                    self,
                    u'Импорт невозможен',
                    message,
                    QtGui.QMessageBox.Close)
            return cond


        process = CProgressDialog(self)
        db = QtGui.qApp.db
        process.policyTypeId = forceRef(db.translate('rbPolicyType', 'code', '1', 'id'))
        process.importClients = self.chkImportClients.isChecked()
        process.matureNetId = forceRef(db.translate('rbNet', 'code', '1', 'id'))

        if not (checkConstrain(process.policyTypeId, u'В справочнике типов полиса (rbPolicyType) отсутствует запись с кодом 1') or
            checkConstrain(process.matureNetId, u'В справочнике Сеть (rbNet) отсутствует запись с кодом 1')):
            return

        QtGui.qApp.call(self, process.exec_)


    @pyqtSignature('')
    def on_actLogin_triggered(self):
        try:
            QtGui.qApp.openDatabase()
            if QtGui.qApp.demoModePosible() and QtGui.qApp.demoModeRequested:
                QtGui.qApp.setUserId(None, True)
                self.setUserName(QtGui.qApp.userName())
#                self.updateActionsState()
            else:
                dialog = CLoginDialog(self)
                dialog.setLoginName(QtGui.qApp.preferences.appUserName)
                if dialog.exec_():
                    QtGui.qApp.setUserId(dialog.userId(), dialog.demoMode())
                    QtGui.qApp.preferences.appUserName = dialog.loginName()
                    self.setUserName(QtGui.qApp.preferences.appUserName)
#                    self.setUserName(QtGui.qApp.userName())
#                    self.updateActionsState()
            return
        except database.CDatabaseException, e:
            QtGui.QMessageBox.critical(
                self,
                u'Ошибка открытия базы данных',
                unicode(e),
                QtGui.QMessageBox.Close)
        except Exception, e:
            QtGui.QMessageBox.critical(
                self,
                u'Ошибка открытия базы данных',
                u'Невозможно установить соедиенение с базой данных\n' + unicode(e),
                QtGui.QMessageBox.Close)
            self.logCurrentException()
        QtGui.qApp.closeDatabase()


    @pyqtSignature('')
    def on_actLogout_triggered(self):
        QtGui.qApp.setUserId(None, False)
        QtGui.qApp.closeDatabase()
        #self.updateActionsState()
        self.setUserName('')


    @pyqtSignature('')
    def on_actQuit_triggered(self):
        self.close()


    @QtCore.pyqtSignature('')
    def on_actConnection_triggered(self):
        dlg   = CConnectionDialog(self)
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


#    @QtCore.pyqtSignature('bool')
#    def on_chkCopyToActionType_toggled(self, checked):
#        self.chkFillSpecialityRegionalCode.setEnabled(not checked)


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


#    @QtCore.pyqtSignature('')
#    def on_actAbout_triggered(self):
#        global lastChangedRev
#        global lastChangedDate
#        try:
#            from buildInfo import lastChangedRev, lastChangedDate
#        except:
#            lastChangedRev  = 'unknown'
#            lastChangedDate = 'unknown'
#
#        QtGui.QMessageBox.about(
#            self, u'О программе', about % ( title, lastChangedRev, lastChangedDate)
#            )


    @QtCore.pyqtSignature('')
    def on_actAboutQt_triggered(self):
        QtGui.QMessageBox.aboutQt(self, u'О Qt')


def parseGCDebug(val):
    result = 0
    for char in val.upper():
        if char == 'S':
            result |= gc.DEBUG_STATS
        elif char == 'C':
            result |= gc.DEBUG_COLLECTABLE
        elif char == 'U':
            result |= gc.DEBUG_UNCOLLECTABLE
        elif char == 'I':
            result |= gc.DEBUG_INSTANCES
        elif char == 'O':
            result |= gc.DEBUG_OBJECTS
    return result

def parseGCThreshold(val):
    result = []
    if val:
        for s in val.split(','):
            try:
                v = int(s)
            except:
                v = 0
            result.append(v)
        l = len(result)
        if l > 3:
            result = result[0:3]
    return result


if __name__ == '__main__':
##    gc.set_threshold(*[10*k for k in gc.get_threshold()])
    parser = OptionParser(usage = "usage: %prog [options]")
    parser.add_option('-d', '--demo',
                      dest='demo',
                      help='Login as demo',
                      action='store_true',
                      default=False)
    parser.add_option('--gc-debug',
                      dest='gcDebug',
                      help='gc debug flags, chars S(stat), C(collectable), U(uncollectable), I(instances), O(objects), for details see gc.set_debug',
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
#    parser.add_option("-q", "--quiet",   action="store_false", dest="verbose", default=True,  help="don't print status messages to stdout")
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

        app = CMyApp(sys.argv, options.demo)
        stdTtranslator = QtCore.QTranslator()
        stdTtranslator.load('i18n/std_ru.qm')
        app.installTranslator(stdTtranslator)

        QtGui.qApp = app
        app.applyDecorPreferences() # надеюсь, что это поможет немного сэкономить при создании гл.окна
        mainWindow = CMainWindow()
        app.mainWindow = mainWindow
        app.applyDecorPreferences() # применение максимизации/полноэкранного режима к главному окну

        if app.preferences.dbAutoLogin:
            mainWindow.actLogin.activate(QtGui.QAction.Trigger)
        mainWindow.show()
        res = app.exec_()
        mainWindow.savePreferences()
        app.preferences.save()
        app.closeDatabase()
        app.doneTrace()
        QtGui.qApp = None

#    sys.exit(res)
