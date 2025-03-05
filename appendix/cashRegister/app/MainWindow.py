#!/usr/bin/env python
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

#import shutil
#import tempfile

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, pyqtSignature, SIGNAL, QVariant

from library                import database
from library.Utils          import getPref, setPref, forceString, forceStringEx

from localPreferences.appPreferencesDialog import CAppPreferencesDialog

from preferences.connection import CConnectionDialog
from preferences.decor      import CDecorDialog

from Users.Login            import CLoginDialog
from Users.tryKerberosAuth  import tryKerberosAuth

from CashRegister           import CCashRegisterWindow
from ReportCashier          import CReportCashier
from Ui_MainWindow          import Ui_CMainWindow



class CMainWindow(QtGui.QMainWindow, Ui_CMainWindow):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.setCentralWidget(self.centralwidget)
        self.loadPreferences()
        self.status = QtGui.QLabel(self)
        self.statusbar.addPermanentWidget(self.status)
        self.cashRegisterWindow = None
        self.connect(QtGui.qApp, SIGNAL('deviceStateChaged()'), self.deviceStateChaged)


    def loadPreferences(self):
        preferences = getPref(QtGui.qApp.preferences.windowPrefs, self.objectName(), {})
        geometry = getPref(preferences, 'geometry', None)
        if type(geometry) == QVariant and geometry.type() == QVariant.ByteArray and not geometry.isNull():
            self.restoreGeometry(geometry.toByteArray())
        state = getPref(preferences, 'state', None)
        if type(state) == QVariant and state.type() == QVariant.ByteArray and not geometry.isNull():
            self.restoreState(state.toByteArray())


    def savePreferences(self):
        preferences = {}
        setPref(preferences,'geometry',QVariant(self.saveGeometry()))
        setPref(preferences,'state', QVariant(self.saveState()))
        setPref(QtGui.qApp.preferences.windowPrefs, self.objectName(), preferences)


    def setUserName(self, userName):
        app = QtGui.qApp
        if userName:
            orgStructureName = ''
            orgStructureId = QtGui.qApp.getCurrentOrgStructureId()
            if orgStructureId:
                db = QtGui.qApp.db
                orgStructureName = forceStringEx(db.translate('OrgStructure', 'id', orgStructureId, 'name'))
            self.setWindowTitle(u'%s: %s%s' % (app.title, userName, (u': %s'%(orgStructureName)) if orgStructureName else u''))
        else:
            self.setWindowTitle(app.title)


    def deviceStateChaged(self):
        app = QtGui.qApp
        reportsEnabled = app.getDeviceOk()
        self.setDeviceReportsEnabled(reportsEnabled)


    def setDeviceReportsEnabled(self, value):
        app = QtGui.qApp
        self.actReportX.setEnabled(value and app.deviceHasMethod('reportX'))
        self.actReportLastDocument.setEnabled(value and app.deviceHasMethod('reportLastDocument'))
        self.actReportOfdExchangeStatus.setEnabled(value and app.deviceHasMethod('reportOfdExchangeStatus'))
        self.actReportQuantity.setEnabled(value and app.deviceHasMethod('reportQuantity'))
        self.actReportOperators.setEnabled(value and app.deviceHasMethod('reportOperators'))
        self.actReportHours.setEnabled(value and app.deviceHasMethod('reportHours'))
        self.actReportShiftTotalCounters.setEnabled(value and app.deviceHasMethod('reportShiftTotalCounters'))
        self.actReportFnTotalCounters.setEnabled(value and app.deviceHasMethod('reportFnTotalCounters'))
        self.actReportOfdTest.setEnabled(value and app.deviceHasMethod('reportOfdTest'))
        self.actReportCashRegisterInfo.setEnabled(value and app.deviceHasMethod('reportCashRegisterInfo'))
        self.actReportRegistration.setEnabled(value and app.deviceHasMethod('reportRegistration'))


    def updateActionsState(self):
        app = QtGui.qApp
        loggedIn = bool(app.db and app.userId)

        self.actLogin.setEnabled(not loggedIn)
        self.actLogout.setEnabled(loggedIn)


    def findSubwindow(self, widget):
        for subwindow in self.centralwidget.subWindowList():
            if subwindow.widget() == widget:
                return subwindow
        return None


    @pyqtSignature('')
    def on_actLogin_triggered(self):
        ok = False
        try:
            QtGui.qApp.openDatabase()
            if QtGui.qApp.kerberosAuthEnabled():
                userId = tryKerberosAuth()
                if userId:
                    ok = True
                    login = forceString(QtGui.qApp.db.translate('Person', 'id', userId, 'login'))
            if not ok and QtGui.qApp.passwordAuthEnabled():
                dialog = CLoginDialog(self)
                dialog.setLoginName(QtGui.qApp.preferences.appUserName)
                if dialog.exec_():
                    ok, userId, login = True, dialog.userId(), dialog.loginName()
                else:
                    ok, userId, login = False, None, ''
                ok = ok and userId is not None
            if ok:
                QtGui.qApp.setUserId(userId)
                QtGui.qApp.preferences.appUserName = login
                self.setUserName(QtGui.qApp.userName())
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
            QtGui.qApp.logCurrentException()
        finally:
            self.updateActionsState()
            if ok:
                QtGui.qApp.openDevice()
                self.cashRegisterWindow = CCashRegisterWindow(self)
                self.centralWidget().addSubWindow(self.cashRegisterWindow, Qt.Window)
                self.cashRegisterWindow.setWindowState(Qt.WindowMaximized)
            else:
                QtGui.qApp.closeDatabase()
                QtGui.qApp.closeDevice()


    @pyqtSignature('')
    def on_actLogout_triggered(self):
        if self.cashRegisterWindow:
            self.cashRegisterWindow.accountsUpdateTimer.stop()

        for window in self.centralwidget.subWindowList():
            window.close()

        if QtGui.qApp.db:
            QtGui.qApp.clearUserId(True)
            QtGui.qApp.closeDatabase()

        self.updateActionsState()


    @pyqtSignature('')
    def on_actQuit_triggered(self):
        self.close()


    @pyqtSignature('')
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


    @pyqtSignature('')
    def on_actReportX_triggered(self):
        app = QtGui.qApp
        if app.getDeviceOk():
            app.call(self, app.device.reportX)


    @pyqtSignature('')
    def on_actReportLastDocument_triggered(self):
        app = QtGui.qApp
        if app.getDeviceOk():
            app.call(self, app.device.reportLastDocument)


    @pyqtSignature('')
    def on_actReportOfdExchangeStatus_triggered(self):
        app = QtGui.qApp
        if app.getDeviceOk():
            app.call(self, app.device.reportOfdExchangeStatus)


    @pyqtSignature('')
    def on_actReportQuantity_triggered(self):
        app = QtGui.qApp
        if app.getDeviceOk():
            app.call(self, app.device.reportQuantity)


    @pyqtSignature('')
    def on_actReportOperators_triggered(self):
        app = QtGui.qApp
        if app.getDeviceOk():
            app.call(self, app.device.reportOperators)


    @pyqtSignature('')
    def on_actReportCashier_triggered(self):
        CReportCashier(self).exec_()


    @pyqtSignature('')
    def on_actReportHours_triggered(self):
        app = QtGui.qApp
        if app.getDeviceOk():
            app.call(self, app.device.reportHours)


    @pyqtSignature('')
    def on_actReportShiftTotalCounters_triggered(self):
        app = QtGui.qApp
        if app.getDeviceOk():
            app.call(self, app.device.reportShiftTotalCounters)


    @pyqtSignature('')
    def on_actReportFnTotalCounters_triggered(self):
        app = QtGui.qApp
        if app.getDeviceOk():
            app.call(self, app.device.reportFnTotalCounters)


    @pyqtSignature('')
    def on_actReportOfdTest_triggered(self):
        app = QtGui.qApp
        if app.getDeviceOk():
            app.call(self, app.device.reportOfdTest)


    @pyqtSignature('')
    def on_actReportCashRegisterInfo_triggered(self):
        app = QtGui.qApp
        if app.getDeviceOk():
            app.call(self, app.device.reportCashRegisterInfo)


    @pyqtSignature('')
    def on_actReportRegistration_triggered(self):
        app = QtGui.qApp
        if app.getDeviceOk():
            app.call(self, app.device.reportRegistration)


    @pyqtSignature('')
    def on_actAppPreferences_triggered(self):
        qApp = QtGui.qApp
        prevOrgId = qApp.getCurrentOrgId()
        prevOrgStructureId = qApp.getCurrentOrgStructureId()
        dialog = CAppPreferencesDialog(self)
        dialog.setProps(qApp.preferences.appPrefs)
        if dialog.exec_():
            qApp.preferences.appPrefs.update(dialog.props())
            qApp.preferences.save()
            orgId = qApp.getCurrentOrgId()
            self.setUserName(qApp.userName())
            if orgId != prevOrgId:
                qApp.emit(SIGNAL('currentOrgIdChanged()'))
            if QtGui.qApp.getCurrentOrgStructureId() != prevOrgStructureId:
                qApp.emit(SIGNAL('currentOrgStructureIdChanged()'))
            QtGui.qApp.openDevice()


    @pyqtSignature('')
    def on_actDecor_triggered(self):
        dlg = CDecorDialog(self)
        preferences = QtGui.qApp.preferences
        dlg.setStyle(preferences.decorStyle)
        dlg.setStandardPalette(preferences.decorStandardPalette)
        dlg.setMaximizeMainWindow(preferences.decorMaximizeMainWindow)
        dlg.setFullScreenMainWindow(preferences.decorFullScreenMainWindow)
        dlg.setUseCustomFont(preferences.useCustomFont)
        dlg.setFont(preferences.font)
        if dlg.exec_():
            preferences.decorStyle = dlg.style()
            preferences.decorStandardPalette = dlg.standardPalette()
            preferences.decorMaximizeMainWindow = dlg.maximizeMainWindow()
            preferences.decorFullScreenMainWindow = dlg.fullScreenMainWindow()
            preferences.useCustomFont = dlg.useCustomFont()
            preferences.font = dlg.font()
            preferences.save()
            QtGui.qApp.applyDecorPreferences()


    @pyqtSignature('')
    def on_actAbout_triggered(self):
        QtGui.QMessageBox.about(self, u'О программе', QtGui.qApp.getAbout() )


    @pyqtSignature('')
    def on_actAboutQt_triggered(self):
        QtGui.QMessageBox.aboutQt(self, u'О Qt')

