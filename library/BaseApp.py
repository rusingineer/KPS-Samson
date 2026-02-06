# -*- coding: utf-8 -*-

#############################################################################
##
## Copyright (C) 2018-2020 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################
##
## Базовый класс приложений
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

from logging.handlers       import RotatingFileHandler

from PyQt4                  import QtGui
from PyQt4.QtCore           import Qt, SIGNAL, qInstallMsgHandler, QDir, QVariant

from library                import database
from library.Calendar       import CCalendarInfo
from library.Preferences    import CPreferences
from library.database import CDatabaseException
from library.getHostName    import getHostName

from library.Utils import forceString, forceRef, anyToUnicode, exceptionToUnicode, quote, forceDate

from Orgs.Utils             import getOrganisationInfo

from Users.UserInfo         import CUserInfo


class CBaseApp(QtGui.QApplication):
    __pyqtSignals__ = ('dbConnectionChanged(bool)',
                       'currentUserIdChanged()',
                      )

    try:
        from buildInfo import lastChangedRev  as lastChangedRev, \
                              lastChangedDate as lastChangedDate
    except:
        lastChangedRev  = 'unknown'
        lastChangedDate = 'unknown'
    try:
        from buildInfo import socRev as socRev
    except:
        socRev = '-'


    title       = u'САМСОН'
    titleLat    =  'SAMSON'
    version     =  '2.7'

    iniFileName = 'samson.ini'
    logFileName = 'samson.log'

    @classmethod
    def getLatVersion(cls):
        return u'%s, v.%s (rev. %s from %s)' % (cls.titleLat, cls.version, cls.lastChangedRev, cls.lastChangedDate)


    @classmethod
    def getAbout(cls):
        ver23 = ''
        if QtGui.qApp.db:
            record = QtGui.qApp.db.getRecordEx('VersionControl', 'version, dateUpdate', 'name="baseVersion"')
            if record:
                try:
                    recordMod = QtGui.qApp.db.getRecordEx('VersionControlMod', 'version, dateUpdate', 'name="baseVersion"')
                    modernisationVersion = u'<a href="1">Версия модернизации</a><br/>' if recordMod else ''
                except CDatabaseException:
                    modernisationVersion = ''

                ver23 = (u'АИС «Конфигурация МИС КПС «САМСОН» (Краснодарский край)»<br/>'
                        u'Версия БД %s (от %s)<br/>'
                        u'Версия сборки: %s<br/>'
                        u'%s'
                        u'Copyright © 2015-2025 ООО "СОЦ-Информ"<br/>'
                        u'Создано при участии: ООО «КОРТИС Технологии», ООО «Виста», ГБУ "КМИАЦ".<br/>' % (
                    forceString(record.value('version')),
                    forceDate(record.value('dateUpdate')).toString("dd.MM.yyyy"),
                    cls.socRev,
                    modernisationVersion))

        return u'%s<br/>' \
               u'Комплекс Программных Средств<br/>' \
               u'"Система Автоматизации Медико-Страхового Обслуживания Населения"<br/>' \
               u'«%s»<br/>' \
               u'%s' \
               u'Версия %s (ревизия %s от %s)<br/>' \
               u'Copyright © 2012-2025 ООО "САМСОН Групп"<br/>' \
               u'распространяется под лицензией GNU GPL v.3 или выше<br/>' % (ver23, cls.title,
                   ((u'Версия сборки: '+ cls.socRev + u'<br/>') if ver23 == '' else u''), cls.version, cls.lastChangedRev, cls.lastChangedDate)


    def __init__(self, args, iniFileName):
        QtGui.QApplication.__init__(self, args)
        self.mainWindow = None
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
        self.db     = None
        self.preferences = CPreferences(iniFileName)
        self.preferences.load()
        self.preferencesDir = self.preferences.getDir()
        self.calendarInfo = CCalendarInfo(self)
        self.registerDocumentTables()
        self._currentClientId = None
        self.userInfo = None
        self.disableLock = False
        self.logSql = False
        if self.preferences.hunterEnabled:
            try:
                self.initTracer()
            except ImportError:
                self.logCurrentException()


    def getLogFilePath(self):
        if not os.path.exists(self.logDir):
            os.makedirs(self.logDir)
        return os.path.join(self.logDir, self.logFileName)

    
    def getFaultHandlerLogFilePath(self):
        if not os.path.exists(self.logDir):
            os.makedirs(self.logDir)
        return os.path.join(self.logDir, 'faulthandler.log')
    

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


    def initTracer(self):
        import hunter
        self.traceDir = self.getLogFilePath() + 'traceLog.txt'
        with open(self.traceDir, 'w') as file:
            file.truncate()
        hunter.trace(
            filename_regex=self.preferences.traceFilenamePattern,
            function_regex=self.preferences.traceFunctionPattern,
            kind=self.preferences.kind,
            stdlib=self.preferences.stdlib,
            action=hunter.CodePrinter(stream=self.traceDir))


#beep
#void QApplication::beep () [static]



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


    def getDocumentsDir(self):
        return unicode(QtGui.QDesktopServices.storageLocation(QtGui.QDesktopServices.DocumentsLocation))


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

    def getBrowserDir(self):
        result = forceString(self.preferences.appPrefs.get('browserDir', None))
        if not result:
            result = 'C:\Program Files\Google\Chrome\Application\chrome.exe'
        return result

    def getPathToDictionary(self):
        result = QtGui.qApp.pathToPersonalDict()
        if not os.path.isfile(result):
            result = self.getDefaultPathToDictionary()
            if not os.path.isfile(result):
                return None
        return result


    def getDefaultPathToDictionary(self):
        return os.path.join(self.logDir, 'Dicts', 'PersonalDictionary.txt')


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

        self.log(typeName, anyToUnicode(msg), traceback.extract_stack()[:-1])


    def kerberosAuthEnabled(self):
        return True


    def passwordAuthEnabled(self):
        return True


    def setUserId(self, userId):
        assert userId, 'userId must be not «%r»' % userId

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
        return forceRef(QtGui.qApp.preferences.appPrefs.get('orgId', None))



    currentOrgId = getCurrentOrgId

    def getCurrentOrgStructureId(self):
        return forceRef(QtGui.qApp.preferences.appPrefs.get('orgStructureId', ''))
#        return forceRef(QtGui.qApp.preferences.appPrefs.get('orgStructureId', QVariant())) or self.userOrgStructureId

    currentOrgStructureId = getCurrentOrgStructureId


    def openDatabase(self):
        self.db = None
        self.db = database.connectDataBase(self.preferences.dbDriverName,
                                           self.preferences.dbServerName,
                                           self.preferences.dbServerPort,
                                           self.preferences.dbDatabaseName,
                                           self.preferences.dbUserName,
                                           self.preferences.dbPassword,
                                           logger = logging.getLogger('DB') if self.logSql else None
                                          )
        if not self.disableLock:
            self.db.query('CALL getAppLock_prepare()')
        self.emit(SIGNAL('dbConnectionChanged(bool)'), True)


    def closeDatabase(self):
        if self.db:
            if not self.disableLock:
                self.db.query('CALL CleanupLocks()')
            self.db.close()
            self.db = None
            self.emit(SIGNAL('dbConnectionChanged(bool)'), False)


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
                                        exceptionToUnicode(e),
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


    def callWithProgressBar(self, widget, iterFunc, collection):
        """
            Вызывает функцию по элементам и показывает прогрессбар по центру
            экрана для визуализации хода выполнения с возможностью прервать
            выполнение. Результат работы такой же, как у фукнкции `map`, но
            при этом показывается прогрессбар. Важно отметить, что на одну
            итерацию прогрессбар не отображается. Если выполнение было
            отменено, то будет возвращено None.
        """
        if len(collection) == 1:
            return [iterFunc(collection[0])]
        else:
            from library.BackgroundProgressBar import CBackgroundProgressBar
            pbar = CBackgroundProgressBar(parent=widget or self.mainWindow)
            return pbar.run(iterFunc, collection)


    def highlightRedDate(self):
        return False


