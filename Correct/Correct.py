# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2017 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

# WFT? если это отдельная утилита, она должа быть в appendix

import sys
import os
import platform

if platform.system() != 'Windows':
    pathtail = '/Correct/Correct.py'
    sys.path.insert(0, os.path.realpath(__file__).replace(pathtail, ''))

from PyQt4        import QtGui, QtSql
from PyQt4.QtCore import pyqtSignature, QVariant

from library                import database
from library.Preferences    import CPreferences
from library.Utils          import forceRef

from Users.Login            import CLoginDialog
from Users.UserInfo         import CUserInfo

from Orgs.Utils             import getOrganisationInfo

from Users.Rights           import urUsePropertyCorrector

from preferences.connection import CConnectionDialog

from CorrectWidget import CCorrectWidget

from Ui_Correct import Ui_Correct

title = u'САМСОН'
titleLat = 'SAMSON'

about = u'Комплекс Программных Средств \n' \
        u'"Система Автоматизации Медико-Страхового Обслуживания Населения"\n' \
        u'КПС «%s»\n'   \
        u'Версия 2.5 (ревизия %s от %s)\n' \
        u'Copyright © 2015 ООО "САМСОН Групп"\n' \
        u'распространяется под лицензией GNU GPL v.3 или выше\n' \
        u'Основано на КПС «САМСОН-ВИСТА» версии 2.0\n' \
        u'телефон тех.поддержки: (812) 418-39-70'\
        u'\n'\
        u'"Утилита преобразования типов данных значений свойств Действий"'

class CMyApp(QtGui.QApplication):
    def __init__(self, argv):
        QtGui.QApplication.__init__(self, argv)
        self.db = None
        self.mainWindow = None

        self.preferences   = CPreferences('S11PropertyCorrector.ini')
#        self.preferences   = CPreferences('S11App.ini')
        self.preferences.load()

    def openDatabase(self):
        self.closeDatabase()
        self.db = database.connectDataBase(self.preferences.dbDriverName,
                                           self.preferences.dbServerName,
                                           self.preferences.dbServerPort,
                                           self.preferences.dbDatabaseName,
                                           self.preferences.dbUserName,
                                           self.preferences.dbPassword,
                                           compressData = self.preferences.dbCompressData)

    def closeDatabase(self):
        if self.db:
            self.db.close()
            self.db = None
            if QtSql.QSqlDatabase.contains('qt_sql_default_connection'):
                QtSql.QSqlDatabase.removeDatabase('qt_sql_default_connection')

    def addLogMessage(self, msg, wait=False):
        self.mainWindow.addLogMessage(msg, wait)

    def setUserId(self, userId):
        self.userId = userId
        record = self.db.getRecord('Person', ['speciality_id', 'orgStructure_id'], userId) if userId else None
        if record:
            self.userSpecialityId = forceRef(record.value('speciality_id'))
            self.userOrgStructureId = forceRef(record.value('orgStructure_id'))
        else:
            self.userSpecialityId = None
            self.userOrgStructureId = None
        if userId:
            self.userInfo = CUserInfo(userId)
        else:
            self.userInfo = None

    def userName(self):
        if self.userInfo:
            orgId = self.currentOrgId()
            orgInfo = getOrganisationInfo(orgId)
            if not orgInfo:
                QtGui.qApp.preferences.appPrefs['orgId'] = QVariant()
            shortName = orgInfo.get('shortName', u'ЛПУ в настройках не указано!')
            return u'%s (%s) %s' % (self.userInfo.name(), self.userInfo.login(), shortName)
        else:
            return ''

    def userHasRight(self, right):
        return self.userInfo is not None and self.userInfo.hasRight(right)

    def userHasAnyRight(self, rights):
        return self.userInfo is not None and self.userInfo.hasAnyRight(rights)

    def currentOrgId(self):
        return forceRef(QtGui.qApp.preferences.appPrefs.get('orgId', QVariant()))

    def doneTrace(self):
        pass

class CCorrect(QtGui.QMainWindow, Ui_Correct):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.setupUi(self)
        self.setWindowTitle(title)

        self._centralWidget = None

        self.actLogout.setEnabled(False)
        self.actLogin.setEnabled(True)


    def setOverrideCursor(self, cursor):
        QtGui.qApp.setOverrideCursor(cursor)

    def restoreOverrideCursor(self):
        QtGui.qApp.restoreOverrideCursor()


    def addLogMessage(self, msg, wait=False):
        if self._centralWidget:
            self._centralWidget.addLogMessage(msg, wait)

    def setUserName(self, userName):
        if userName:
            self.setWindowTitle(u'%s: %s' % (title, userName))
        else:
            self.setWindowTitle(title)

    def setCentralWidgetEx(self):
        if not self._centralWidget:
            self._centralWidget = CCorrectWidget(self)
            self.setCentralWidget(self._centralWidget)

    def closeDatabase(self):
        self.setUserName('')
        self._centralWidget = None
        self.setCentralWidget(None)
        QtGui.qApp.closeDatabase()
        self.actLogout.setEnabled(False)
        self.actLogin.setEnabled(True)

    @pyqtSignature('')
    def on_actConnectSettings_triggered(self):
        dlg   = CConnectionDialog(self)
        preferences = QtGui.qApp.preferences
        dlg.setDriverName(preferences.dbDriverName)
        dlg.setServerName(preferences.dbServerName)
        dlg.setServerPort(preferences.dbServerPort)
        dlg.setDatabaseName(preferences.dbDatabaseName)
        dlg.setCompressData(preferences.dbCompressData)
        dlg.setUserName(preferences.dbUserName)
        dlg.setPassword(preferences.dbPassword)
        if dlg.exec_():
            preferences.dbDriverName = dlg.driverName()
            preferences.dbServerName = dlg.serverName()
            preferences.dbServerPort = dlg.serverPort()
            preferences.dbDatabaseName = dlg.databaseName()
            preferences.dbCompressData = dlg.compressData()
            preferences.dbUserName = dlg.userName()
            preferences.dbPassword = dlg.password()
            preferences.save()

    @pyqtSignature('')
    def on_actLogout_triggered(self):
        self.closeDatabase()

    @pyqtSignature('')
    def on_actLogin_triggered(self):
        try:
            QtGui.qApp.openDatabase()
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
                self.actLogout.setEnabled(True)
                self.actLogin.setEnabled(False)

                if QtGui.qApp.userHasRight(urUsePropertyCorrector):
                    self.setCentralWidgetEx()
                    return
                else:
                    QtGui.QMessageBox.information(
                        self,
                        u'Внимание!',
                        u'У вас не хватает прав на испольльзование этой программы!')
        except Exception, e:
            QtGui.QMessageBox.critical(
                self,
                u'Ошибка открытия базы данных',
                u'Невозможно установить соедиенение с базой данных\n' + unicode(e),
                QtGui.QMessageBox.Close)
        self.closeDatabase()


    @pyqtSignature('')
    def on_actAbout_triggered(self):
        global lastChangedRev
        global lastChangedDate
        try:
            from buildInfo import lastChangedRev, lastChangedDate
        except:
            lastChangedRev  = 'unknown'
            lastChangedDate = 'unknown'

        QtGui.QMessageBox.about(self, u'О программе', about % ( title, lastChangedRev, lastChangedDate))


    @pyqtSignature('')
    def on_actAboutQt_triggered(self):
        QtGui.QMessageBox.aboutQt(self, u'О Qt')



def main():
    app = CMyApp(sys.argv)
    mainWindow = CCorrect()
    QtGui.qApp = app
    app.mainWindow = mainWindow
    mainWindow.show()
    app.exec_()
    app.preferences.save()
    app.closeDatabase()
    QtGui.qApp = None

if __name__ == '__main__':
    main()
