# -*- coding: utf-8 -*-

#############################################################################
##
## Copyright (C) 2017-2023 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

import locale
import logging
import os
import os.path
import shutil
import sys
import tempfile
import traceback

from logging.handlers import RotatingFileHandler

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QDir, QTimer, QVariant, qInstallMsgHandler, SIGNAL

import library.patches # noqa

from library                import database
from library.Calendar       import CCalendarInfo
from library.Preferences    import CPreferences
from library.getHostName    import getHostName

from library.Utils          import (
                                    anyToUnicode,
                                    exceptionToUnicode,
                                    forceBool,
                                    forceRef,
                                    forceString,
                                    forceStringEx,
                                    quote
                                   )
#from library.DialogBase  import CDialogBase


from Orgs.Utils             import getOrganisationInfo

#from preferences.connection import CConnectionDialog
#from preferences.decor      import CDecorDialog

#from Users.Login            import CLoginDialog
#from Users.tryKerberosAuth  import tryKerberosAuth
from Users.UserInfo         import CUserInfo

#from localPreferences.appPreferencesDialog import CAppPreferencesDialog
from Atol.AtolInterface     import CAtolInterface
from Shtrih.ShtrihInterface import CShtrihInterface


class CApp(QtGui.QApplication):
    __pyqtSignals__ = ('dbConnectionChanged(bool)',
                       'currentUserIdChanged()',
                       'deviceStateChaged()',
                      )

    try:
        from buildInfo import lastChangedRev  as lastChangedRev, \
                              lastChangedDate as lastChangedDate
    except:
        lastChangedRev  = 'unknown'
        lastChangedDate = 'unknown'


    title       = u'САМСОН-КАССА'
    titleLat    =  'SAMSON-ECR'
    version     =  '2.5'

    iniFileName = 'cashRegister.ini'
    logFileName = 'cashRegister_error.log'

    @classmethod
    def getLatVersion(cls):
        return u'%s, v.%s (rev. %s from %s)' % (cls.titleLat, cls.version, cls.lastChangedRev, cls.lastChangedDate)


    @classmethod
    def getAbout(cls):
        return u'Комплекс Программных Средств \n' \
               u'"Система Автоматизации Медико-Страхового Обслуживания Населения"\n' \
               u'«%s»\n'   \
               u'Версия %s (ревизия %s от %s)\n' \
               u'Copyright © 2017-2023 ООО "САМСОН Групп"\n' \
               u'распространяется под лицензией GNU GPL v.3 или выше\n' \
               u'телефон тех.поддержки: (812) 418-39-70' % ( cls.title, cls.version, cls.lastChangedRev, cls.lastChangedDate )


    # для работы CReportViewDialog
    @staticmethod
    def documentEditor():
        return None


    def __init__(self, args, logSql=False):
        QtGui.QApplication.__init__(self, args)
        self.defaultFont = self.font()
        self.logDir = os.path.join(unicode(QDir.toNativeSeparators(QDir.homePath())), '.samson-vista')
        self.initLogger()

        self.oldMsgHandler = qInstallMsgHandler(self.msgHandler)
        self.oldEexceptHook = sys.excepthook
        sys.excepthook = self.logException
        self.traceActive = True

        self.homeDir= None
        self.saveDir= None
        self.hostName = getHostName()
        self.userId = None
        self.userSpecialityId = None
        self.userOrgStructureId = None
        self.logSql = logSql
        self.db     = None
        self.mainWindow = None
        self.preferences = CPreferences(self.iniFileName)
        self.preferences.load()
        self.preferencesDir = self.preferences.getDir()
        self.calendarInfo = CCalendarInfo(self)
        self.registerDocumentTables()
        self._currentClientId = None
        self.userInfo = None
#        self.device = CAtolInterface()
        self.device = None
        self.deviceOk = False
        self.deviceNameOrMessage = ''
        self.ofdExchangeMessage  = ''

        self.deviceCheckTimer = QTimer(self)
        self.deviceCheckTimer.setInterval(2000)

        self.connect(self.deviceCheckTimer, SIGNAL('timeout()'), self.checkDevice)

        self.deviceCheckTimer.start()
#beep
#void QApplication::beep () [static]


    def __del__(self):
        self.closeDevice()


    def getLogFilePath(self):
        if not os.path.exists(self.logDir):
            os.makedirs(self.logDir)
        return os.path.join(self.logDir, self.logFileName)


    def initLogger(self):
        formatter = logging.Formatter(fmt     = '%(asctime)s %(message)s',
                                      datefmt = '%Y-%m-%d %H:%M:%S'
                                     )


        handler = RotatingFileHandler(self.getLogFilePath(),
                                      mode='a',
                                      maxBytes=1024*1024,
                                      backupCount=4,
                                      encoding=None,
                                      delay=0)

        handler.setFormatter(formatter)
        handler.setLevel(logging.INFO)

        logger = logging.getLogger()
        logger.setLevel(logging.INFO)

        oldHandlers = list(logger.handlers)
        logger.addHandler(handler)
        for oldHandler in oldHandlers:
            logger.removeHandler(self, oldHandler)

        self.logger = logger


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
            if self.preferences.useCustomFont:
                self.setFont(self.preferences.font)
            else:
                self.setFont(self.defaultFont)


    def registerDocumentTables(self):
        pass


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
        logString = u'%s: %s\n' % (title, message)
        if stack:
            try:
                logString += anyToUnicode(''.join(traceback.format_list(stack))) + '\n'
            except:
                logString += 'stack lost\n'
        self.logger.info(logString)


    def logException(self, exceptionType, exceptionValue, exceptionTraceback):
        title = repr(exceptionType)
        message = exceptionToUnicode(exceptionValue)
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

    def kerberosAuthEnabled(self):
        return True


    def passwordAuthEnabled(self):
        return True


    def setUserId(self, userId):
        assert userId

        self.userId = userId
        self.userSpecialityId = None
        self.userOrgStructureId = None

        db = self.db
        if db.isProcedureExists('registerUserLoginEx'):
            db.query(u'CALL registerUserLoginEx(%s, %s, %s)' % (str(userId) if userId else 'NULL',
                                                                quote(self.hostName),
                                                                quote(self.getLatVersion()),
                                                              )
                    )
        elif db.isProcedureExists('registerUserLogin'):
            db.query(u'CALL registerUserLogin(%s, %s)' % (str(userId) if userId else 'NULL',
                                                          quote(self.hostName))
                                                         )

        if userId:
            record = db.getRecord('Person', ['speciality_id', 'orgStructure_id'], userId)
            if record:
                self.userSpecialityId = forceRef(record.value('speciality_id'))
                self.userOrgStructureId = forceRef(record.value('orgStructure_id'))
        self.userInfo = CUserInfo(userId)
        self.emit(SIGNAL('currentUserIdChanged()'))


    def clearUserId(self, emitUserIdChanged=True):
        self.userId = None
        self.userSpecialityId = None
        self.userOrgStructureId = None
        self.userInfo = None

        db = self.db
        if db.isProcedureExists('registerUserLogout'):
            db.query('CALL registerUserLogout()')
        if emitUserIdChanged:
            self.emit(SIGNAL('currentUserIdChanged()'))


    def userName(self):
        if self.userInfo:
            orgId = self.getCurrentOrgId()
            orgInfo = getOrganisationInfo(orgId)
            if not orgInfo:
                QtGui.qApp.preferences.appPrefs['orgId'] = QVariant()
            shortName = orgInfo.get('shortName', u'ЛПУ в настройках не указано!')
            return u'%s (%s) %s' % (self.userInfo.name(), self.userInfo.login(), shortName)
        else:
            return u''


    def userHasRight(self, right):
        return self.userInfo is not None and self.userInfo.hasRight(right)


    def userHasAnyRight(self, rights):
        return self.userInfo is not None and self.userInfo.hasAnyRight(rights)


    def highlightInvalidDate(self):
        return True


    def getCurrentOrgId(self):
        return forceRef(QtGui.qApp.preferences.appPrefs.get('orgId', QVariant()))


    currentOrgId = getCurrentOrgId

    def getCurrentOrgStructureId(self):
        return forceRef(QtGui.qApp.preferences.appPrefs.get('orgStructureId', ''))
#        return forceRef(QtGui.qApp.preferences.appPrefs.get('orgStructureId', QVariant())) or self.userOrgStructureId

    def getAuthorId(self):
        if forceBool(QtGui.qApp.preferences.appPrefs.get('useCurrentUser', False)):
            return self.userId
        else:
            return None

    def getUserName(self):
        if self.userId:
            return forceString(QtGui.qApp.db.translate('vrbPerson', 'id', self.userId, 'name'))
        else:
            return 'demo'


    def getUserInn(self):
        if self.userId:
            return forceString(QtGui.qApp.db.translate('Person', 'id', self.userId, 'INN'))
        else:
            return ''


    def getContractNumberMask(self):
        return forceStringEx(QtGui.qApp.preferences.appPrefs.get('contractNumberMask', ''))


    def getContractResolutionMask(self):
        return forceStringEx(QtGui.qApp.preferences.appPrefs.get('contractResolutionMask', ''))


    def getContractGroupingMask(self):
        return forceStringEx(QtGui.qApp.preferences.appPrefs.get('contractGroupingMask', ''))


    def getAccountNumberMask(self):
        return forceStringEx(QtGui.qApp.preferences.appPrefs.get('accountNumberMask', QVariant()))


    def getPrintPayer(self):
        return forceBool(QtGui.qApp.preferences.appPrefs.get('printPayer', False))


    def getPrintAccountNumber(self):
        return forceBool(QtGui.qApp.preferences.appPrefs.get('printAccountNumber', False))


    def getPrintDuplicate(self):
        return forceBool(QtGui.qApp.preferences.appPrefs.get('printDuplicate', False))


    def getCashBox(self):
        return forceString(QtGui.qApp.preferences.appPrefs.get('cashBox', ''))


    def getEcrPassword(self):
        return forceString(QtGui.qApp.preferences.appPrefs.get('password', ''))


    def getEcrOperatorPassword(self):
        return forceString(QtGui.qApp.preferences.appPrefs.get('operatorPassword', ''))


    def getDeviceOk(self):
        return self.deviceOk


    def deviceHasMethod(self, methodName):
        #return isinstance(getattr(self.device, methodName,  None), types.MethodType)
        return callable(getattr(self.device, methodName,  None))


    def getDeviceNameOrMessage(self):
        return self.deviceNameOrMessage


    def getOfdExchangeMessage(self):
        return self.ofdExchangeMessage


    def openDatabase(self):
        self.db = None
        self.db = database.connectDataBase(self.preferences.dbDriverName,
                                     self.preferences.dbServerName,
                                     self.preferences.dbServerPort,
                                     self.preferences.dbDatabaseName,
                                     self.preferences.dbUserName,
                                     self.preferences.dbPassword,
                                     compressData = self.preferences.dbCompressData,
                                     logger = logging.getLogger('DB') if self.logSql else None)
        self.emit(SIGNAL('dbConnectionChanged(bool)'), True)
#        #QtGui.qApp.mainWindow.statusbar.showMessage(u'База данных подключена')
#        QtGui.qApp.mainWindow.status.setText(u'База данных %s подключена'%self.preferences.dbDatabaseName)
#        print "self.db=%r, QtGui.qApp.db=%r" % (self.db, QtGui.qApp.db)


    def closeDatabase(self):
        if self.db:
            self.db.close()
            self.db = None
            self.emit(SIGNAL('dbConnectionChanged(bool)'), False)
#            QtGui.qApp.mainWindow.statusbar.showMessage(u'')
#            QtGui.qApp.mainWindow.status.setText(u'')


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


    def setWaitCursor(self):
        self.setOverrideCursor(QtGui.QCursor(Qt.WaitCursor))


    def callWithWaitCursor(self, widget, func, *params, **kwparams):
        self.setOverrideCursor(QtGui.QCursor(Qt.WaitCursor))
        try:
            return func(*params, **kwparams)
        finally:
            self.restoreOverrideCursor()


    def highlightRedDate(self):
        return False


    def openDevice(self):
        if self.device and self.device.isOpen():
            self.device.close()
        try:
            self.device = None
            driverIdx = forceRef(self.preferences.appPrefs.get('driver', QVariant()))
            if driverIdx == 1:
                self.device = CAtolInterface()
            elif driverIdx == 2:
                self.device = CShtrihInterface()
            if self.device:
                self.device.setup(self.preferences.appPrefs)
                self.device.setOperatorName(self.getUserName())
                self.device.setOperatorVatin(self.getUserInn())
                self.device.open()
        except:
            pass


    def closeDevice(self):
        if self.device and self.device.isOpen():
            self.device.close()
        self.device = None


    def checkDevice(self):
        if not self.device or not self.device.isOpen():
            self.openDevice()

        if self.device:
            if self.device.isOpen():
                try:
                    dt = self.device.getModelInfo()
                    fn = self.device.getFactoryNumber()
    #                deviceName = u'%s %s' % ( dt['name'], dt['version'] )
                    deviceName = u'%s %s' % ( dt['name'], fn )
                    self.setDeviceName(deviceName)
                except Exception, e:
                    self.setDeviceError( unicode(e) )
            else:
                if self.device.driverLoaded():
                    self.setDeviceError( u'ККТ не подключена' )
                else:
                    self.setDeviceError( u'Драйвер ККТ не загружен' )
        else:
            self.setDeviceError( u'Не настроено подключение к ККТ ' )

        message = '-'
        if self.deviceOk:
            try:
                status = self.device.getOfdExchangeStatus()
                if status['unsentCount'] == 0:
                    message = u'Очередь пуста'
                else:
                    message = u'В очереди %d, %s' % ( status['unsentCount'],
                                                      u'есть соединение' if status['connected'] else u'нет соединения')
                self.setDeviceName(deviceName)
            except Exception, e:
                message = unicode(e)
        self.setOfdExchangeMessage(message)


    def setDeviceName(self, deviceName):
        if self.deviceNameOrMessage != deviceName or not self.deviceOk:
            self.deviceOk = True
            self.deviceNameOrMessage = deviceName
            self.emit(SIGNAL('deviceStateChaged()'))


    def setDeviceError(self, message):
        if self.deviceNameOrMessage != message or self.deviceOk:
            self.deviceOk = False
            self.deviceNameOrMessage = message
            self.emit(SIGNAL('deviceStateChaged()'))


    def setOfdExchangeMessage(self, message):
        if self.ofdExchangeMessage != message:
            self.ofdExchangeMessage = message
            self.emit(SIGNAL('deviceStateChaged()'))

