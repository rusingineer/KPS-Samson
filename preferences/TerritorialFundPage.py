# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2021 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################
##
## Страница настройки связи с сервисом проверки страховой принадлежности
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignature, QDate

from library.Utils import exceptionToUnicode, forceBool, forceString, toVariant
from Exchange.TFUnifiedIdent.Service import CTFUnifiedIdentService

from Ui_TerritorialFundPage import Ui_territorialFundPage


class CTerritorialFundPage(Ui_territorialFundPage, QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setupUi(self)


    def setProps(self, props):
        self.chkTFCheckPolicy.setChecked(forceBool(props.get('TFCheckPolicy', False)))
        self.edtTFCPUrl.setText(forceString(props.get('TFCPUrl', '')))
        if QtGui.qApp.checkGlobalPreference(u'23:useAttachWS', u'да'):
            self.chkSyncAttachmentsAfterSave.setEnabled(True)
            self.chkSyncAttachmentsAfterSave.setChecked(forceBool(props.get('SyncAttachmentsAfterSave', False)))
        else:
            self.chkSyncAttachmentsAfterSave.setEnabled(False)
            self.chkSyncAttachmentsAfterSave.setChecked(False)


    def getProps(self, props):
        props['TFCheckPolicy'] = toVariant(int(self.chkTFCheckPolicy.isChecked()))
        props['TFCPUrl'] = toVariant(self.edtTFCPUrl.text())
        props['SyncAttachmentsAfterSave'] = toVariant(int(self.chkSyncAttachmentsAfterSave.isChecked()))


    @pyqtSignature('')
    def on_btnTFCPTest_clicked(self):
        url = forceString(self.edtTFCPUrl.text())
        if not url:
            url = "http://%s/ident/handler.php" % forceString(QtGui.qApp.db.translate('GlobalPreferences', 'code', 'PHP_ServicesUrl', 'value'))
        service = CTFUnifiedIdentService(url)
        try:
            QtGui.qApp.callWithWaitCursor(self,
                                          service.getPolicyAndAttach,
                                          u'Неуловимый',      # firstName
                                          u'Джо',             # lastName
                                          u'',                # patrName
                                          0,                  # sex
                                          QDate(1900, 1, 1),  # birthDate
                                          '',                 # snils
                                          0,                  # policyType
                                          '',                 # policySerial
                                          '',                 # policyNumber
                                          None,               # docTypeId
                                          '',                 # docSerial
                                          ''                  # docNumber
                                         )
            message = u'Соединение успешно'
        except Exception, e:
            QtGui.qApp.logCurrentException()
            message = u'Соединение не удалось: %s' % exceptionToUnicode(e)

        QtGui.QMessageBox.information(self, u'Проверка соединения', message, QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ok)
