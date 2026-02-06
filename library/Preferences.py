# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2021 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

import os.path
from PyQt4 import QtGui

from PyQt4.QtCore import QDir, QSettings, QVariant

from library.Utils import exceptionToUnicode, setPref, toVariant

from Users.DirtyCrypt import encryptPassword, decryptPassword
from Users.Tables  import demoUserName


class CPreferences(object):
    defaultDriverName = 'mysql'
    defaultServerName = 'localhost'
    defaultServerPort = 0
    defaultDatabaseName = 's11'
    defaultUserName   = 'dbuser'
    defaultPassword   = 'dbpassword'
    defaultAppUserName= demoUserName

    def __init__(self, iniFileName='preferences'):

        self.iniFileName = iniFileName

        self.decorStyle = 'Plastique'
        self.decorStandardPalette = True
        self.decorMaximizeMainWindow = True
        self.decorFullScreenMainWindow = False
        self.useCustomFont = False
        self.font = QtGui.qApp.font()
        self.propertyColor = u''
        self.propertyColorTest = '#FF5E5E'

        self.dbDriverName   = CPreferences.defaultDriverName
        self.dbServerName   = CPreferences.defaultServerName
        self.dbServerPort   = CPreferences.defaultServerPort
        self.dbDatabaseName = CPreferences.defaultDatabaseName
        self.dbCompressData = False
        self.dbUserName     = CPreferences.defaultUserName
        self.dbPassword     = CPreferences.defaultPassword
        self.dbAutoLogin    = True
        self.appUserName    = CPreferences.defaultAppUserName

        self.windowPrefs = {}
        self.reportPrefs = {}
        self.appPrefs    = {}
        self.settings    = None

        self.onlineLpuIsOn = None
        self.currentInfisCodeEncrypted = None
        self.iPPhoneDataBasePath = None
        self.confirmInstantly = None
        self.daysForResearchConfirm = None
        self.logSQL = None
        self.webDavServerName = None

        self.smsUrl = None
        self.smsToken = None
        self.smsSender = None
        self.smsttl = None
        self.smsReport = None
        self.smsStatusUrl = None

        self.hunterEnabled = False
        self.traceFilenamePattern = '^(?:(?!library|Ui_|site-packages).)*$' #Не проверять Ui, функции из library и сторонних модулей
        self.traceFunctionPattern = '^(?:(?!notify|__init__|^data$|headerData|asRight|asAnyRight|eventFilter|sort).)*$'# Не проверять Notify, Init, data и headerData, и все hasRight/hasAnyRight
        self.kind = 'call'
        self.stdlib = False


    def getSettings(self):
        if self.settings is None:
            head, tail = os.path.split(self.iniFileName)
    #        root, ext = os.path.splitext(tail)
            if head:
                iniFileName = os.path.abspath(self.iniFileName)
            else:
                tmpSettings = QSettings(QSettings.IniFormat, QSettings.UserScope, 'samson-vista', 'tmp')
                dir = os.path.dirname(unicode(QDir.toNativeSeparators(tmpSettings.fileName())))
                iniFileName = os.path.join(dir, self.iniFileName)
            self.settings = QSettings(iniFileName, QSettings.IniFormat)

            # попытка угадать базу данных и сервер по имени конфига
            if not os.path.exists(iniFileName):
                name = os.path.basename(iniFileName)
                parts = name.split('@')
                if len(parts) == 2:
                    self.dbDatabaseName = parts[0]
                    self.dbServerName   = parts[1]
        return self.settings


    def getDir(self):
        settings = self.getSettings()
        fileName = settings.fileName()
        return os.path.dirname(unicode(QDir.toNativeSeparators(fileName)))


    def load(self):
        try:
            settings = self.getSettings()

            settings.beginGroup('decor')
            self.decorStyle = settings.value('style', QVariant(self.decorStyle) ).toString()
            self.decorStandardPalette = settings.value('standardPalette', QVariant(self.decorStandardPalette)).toBool()
            self.decorMaximizeMainWindow = settings.value('maximizeMainWindow', QVariant(self.decorMaximizeMainWindow)).toBool()
            self.decorFullScreenMainWindow = settings.value('fullScreenMainWindow', QVariant(self.decorFullScreenMainWindow)).toBool()
            self.propertyColor = settings.value('propertyColor', QVariant(self.propertyColor)).toString()
            self.propertyColorTest = settings.value('propertyColorTest', QVariant(self.propertyColorTest)).toString()
            self.useCustomFont = settings.value('useCustomFont', QVariant(self.useCustomFont)).toBool()
            fontDescr = settings.value('font', QVariant('')).toString()
            self.font = QtGui.QFont()
            if not fontDescr or not self.font.fromString(fontDescr):
                self.font = QtGui.qApp.font()
            settings.endGroup()

            settings.beginGroup('db')
            self.dbDriverName = unicode(settings.value('driverName', QVariant(CPreferences.defaultDriverName)).toString()).strip()
            self.dbServerName = unicode(settings.value('serverName', QVariant(self.dbServerName)).toString()).strip()
            self.dbServerPort = settings.value('serverPort', QVariant(CPreferences.defaultServerPort)).toInt()[0]
            self.dbDatabaseName = unicode(settings.value('database', QVariant(self.dbDatabaseName)).toString()).strip()
            self.dbCompressData = settings.value('compressData', QVariant(False)).toBool()
            self.dbUserName = unicode(settings.value('userName', QVariant(CPreferences.defaultUserName)).toString()).strip()
            self.dbEncryptedPassword = ''
            try:
                encryptedPassword = unicode(settings.value('encryptedPassword', QVariant()).toString())
                self.dbPassword = decryptPassword(encryptedPassword)
                self.dbEncryptedPassword = encryptedPassword
            except:
                self.dbPassword = unicode(settings.value('password', QVariant(CPreferences.defaultPassword)).toString())
                self.dbEncryptedPassword = ''
            self.dbAutoLogin = settings.value('autoLogin', QVariant(True)).toBool()
            self.appUserName = unicode(settings.value('appUserName', QVariant(CPreferences.defaultAppUserName)).toString()).strip()
            settings.endGroup()

            settings.beginGroup('org')
            self.onlineLpuIsOn = settings.value('onlineLpuIsOn', QVariant(self.onlineLpuIsOn)).toBool()
            self.currentInfisCodeEncrypted = unicode(settings.value('currentInfisCodeEncrypted', QVariant(self.currentInfisCodeEncrypted)).toString()).strip()
            self.iPPhoneDataBasePath = unicode(settings.value('iPPhoneDataBasePath', QVariant(self.iPPhoneDataBasePath)).toString()).strip()
            self.confirmInstantly = settings.value('confirmInstantly', QVariant(self.confirmInstantly)).toBool()
            self.daysForResearchConfirm = settings.value('daysForResearchConfirm', QVariant(self.daysForResearchConfirm)).toInt()[0]
            self.logSQL = settings.value('logSQL', QVariant(False)).toBool()
            self.webDavServerName = unicode(settings.value('webDavServerName', QVariant(self.webDavServerName)).toString()).strip()
            settings.endGroup()

            settings.beginGroup('sms')
            self.smsUrl = unicode(settings.value('smsUrl', QVariant(self.smsUrl)).toString()).strip()
            self.smsToken = unicode(settings.value('smsToken', QVariant(self.smsToken)).toString()).strip()
            self.smsSender = unicode(settings.value('smsSender', QVariant(self.smsSender)).toString()).strip()
            self.smsttl = unicode(settings.value('smsttl', QVariant(self.smsttl)).toString()).strip()
            self.smsReport = unicode(settings.value('smsReport', QVariant(self.smsReport)).toString()).strip()
            self.smsStatusUrl = unicode(settings.value('smsStatusUrl', QVariant(self.smsStatusUrl)).toString()).strip()
            settings.endGroup()

            settings.beginGroup('hunter')
            self.hunterEnabled = settings.value('hunterEnabled', QVariant(self.hunterEnabled)).toBool()
            self.traceFilenamePattern = unicode(settings.value('traceFilenamePattern', QVariant(self.traceFilenamePattern)).toString()).strip()
            self.traceFunctionPattern = unicode(settings.value('traceFunctionPattern', QVariant(self.traceFunctionPattern)).toString()).strip()
            self.kind = unicode(settings.value('kind', QVariant(self.kind)).toString()).strip()
            self.stdlib = settings.value('stdlib', QVariant(self.stdlib)).toBool()
            settings.endGroup()

            settings.beginGroup('windowPrefs')
            self.windowPrefs = {}
            windows = settings.childGroups()
            for windowName in windows:
                setPref(self.windowPrefs, windowName, self.loadProp(settings, windowName))
            settings.endGroup()

            settings.beginGroup('reportPrefs')
            self.reportPrefs = {}
            for reportName in settings.childGroups():
                setPref(self.reportPrefs, reportName, self.loadProp(settings, reportName))
            settings.endGroup()

            settings.beginGroup('appPrefs')
            self.appPrefs = {}
            for prop in settings.childKeys():
                self.appPrefs[unicode(prop)] = settings.value(prop, QVariant())
            for group in settings.childGroups():
                setPref(self.appPrefs, unicode(group), self.loadProp(settings, group))
            settings.endGroup()
        except:
            QtGui.qApp.logCurrentException()
            QtGui.QMessageBox.critical( self,
                                        u'',
                                        exceptionToUnicode(e),
                                        QtGui.QMessageBox.Close)


    def loadProp(self, settings, propName):
        settings.beginGroup(propName)
        result = {}
        props = settings.childKeys()
        for prop in props:
            setPref(result, prop, settings.value(prop, QVariant()))
        groups = settings.childGroups()
        for group in groups:
            setPref(result, group, self.loadProp(settings, group))
        settings.endGroup()
        return result


    def save(self):
        try:
            settings = self.getSettings()

            settings.beginGroup('decor')
            settings.setValue('style', QVariant(self.decorStyle))
            settings.setValue('standardPalette', QVariant(self.decorStandardPalette))
            settings.setValue('maximizeMainWindow', QVariant(self.decorMaximizeMainWindow))
            settings.setValue('fullScreenMainWindow', QVariant(self.decorFullScreenMainWindow))
            settings.setValue('propertyColor', QVariant(self.propertyColor))
            settings.setValue('propertyColorTest', QVariant(self.propertyColorTest))
            settings.setValue('useCustomFont', QVariant(self.useCustomFont))
            settings.setValue('font', QVariant(self.font.toString()))
            settings.endGroup()

            settings.beginGroup('db')
            settings.setValue('driverName', QVariant(self.dbDriverName))
            settings.setValue('serverName', QVariant(self.dbServerName))
            settings.setValue('serverPort', QVariant(self.dbServerPort))
            settings.setValue('database',   QVariant(self.dbDatabaseName))
            settings.setValue('compressData', QVariant(self.dbCompressData))
            settings.setValue('userName',   QVariant(self.dbUserName))
            settings.remove('password')
            if not self.dbEncryptedPassword or decryptPassword(self.dbEncryptedPassword) != self.dbPassword:
                self.dbEncryptedPassword = encryptPassword(self.dbPassword)
                settings.setValue('encryptedPassword', QVariant(self.dbEncryptedPassword))
            settings.setValue('autoLogin',  QVariant(self.dbAutoLogin))
            settings.setValue('appUserName',QVariant(self.appUserName))
            settings.endGroup()

            settings.beginGroup('windowPrefs')
            for windowName in self.windowPrefs:
                self.saveProp(settings, windowName, self.windowPrefs[windowName])
            settings.endGroup()

            settings.beginGroup('hunter')
            settings.setValue('hunterEnabled', QVariant(self.hunterEnabled))
            settings.setValue('traceFilenamePattern', QVariant(self.traceFilenamePattern))
            settings.setValue('traceFunctionPattern', QVariant(self.traceFunctionPattern))
            settings.setValue('kind', QVariant(self.kind))
            settings.setValue('stdlib', QVariant(self.stdlib))
            settings.endGroup()

            settings.beginGroup('reportPrefs')
            for reportName in self.reportPrefs:
                self.saveProp(settings, reportName, self.reportPrefs[reportName])
            settings.endGroup()

            self.saveProp(settings, 'appPrefs', self.appPrefs)

            settings.sync()
        except:
            pass


    def saveProp(self, settings, propName, propVal):
        if type(propVal) == dict:
            settings.beginGroup(propName)
            for subPropName in propVal:
                self.saveProp(settings, subPropName, propVal[subPropName])
            settings.endGroup()
        else:
            settings.setValue(propName, toVariant(propVal))
