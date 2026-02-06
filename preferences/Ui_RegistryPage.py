# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\projects\Samson\UP_s11\client\preferences\RegistryPage.ui'
#
# Created by: PyQt4 UI code generator 4.11.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_registryPage(object):
    def setupUi(self, registryPage):
        registryPage.setObjectName(_fromUtf8("registryPage"))
        registryPage.resize(542, 155)
        registryPage.setToolTip(_fromUtf8(""))
        self.gridLayout = QtGui.QGridLayout(registryPage)
        self.gridLayout.setMargin(4)
        self.gridLayout.setSpacing(4)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.cmbDoubleClickQueueClient = QtGui.QComboBox(registryPage)
        self.cmbDoubleClickQueueClient.setObjectName(_fromUtf8("cmbDoubleClickQueueClient"))
        self.cmbDoubleClickQueueClient.addItem(_fromUtf8(""))
        self.cmbDoubleClickQueueClient.setItemText(0, _fromUtf8(""))
        self.cmbDoubleClickQueueClient.addItem(_fromUtf8(""))
        self.cmbDoubleClickQueueClient.addItem(_fromUtf8(""))
        self.cmbDoubleClickQueueClient.addItem(_fromUtf8(""))
        self.cmbDoubleClickQueueClient.addItem(_fromUtf8(""))
        self.gridLayout.addWidget(self.cmbDoubleClickQueueClient, 0, 1, 1, 2)
        spacerItem = QtGui.QSpacerItem(20, 1, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, 8, 0, 1, 1)
        self.lblDoubleClickQueueClient = QtGui.QLabel(registryPage)
        self.lblDoubleClickQueueClient.setObjectName(_fromUtf8("lblDoubleClickQueueClient"))
        self.gridLayout.addWidget(self.lblDoubleClickQueueClient, 0, 0, 1, 1)
        self.lblOnSingleClientInSearchResult = QtGui.QLabel(registryPage)
        self.lblOnSingleClientInSearchResult.setObjectName(_fromUtf8("lblOnSingleClientInSearchResult"))
        self.gridLayout.addWidget(self.lblOnSingleClientInSearchResult, 3, 0, 1, 1)
        self.chkExternalNotificationOnlyAttach = QtGui.QCheckBox(registryPage)
        self.chkExternalNotificationOnlyAttach.setObjectName(_fromUtf8("chkExternalNotificationOnlyAttach"))
        self.gridLayout.addWidget(self.chkExternalNotificationOnlyAttach, 6, 0, 1, 1)
        self.chkExternalNotificationAuto = QtGui.QCheckBox(registryPage)
        self.chkExternalNotificationAuto.setObjectName(_fromUtf8("chkExternalNotificationAuto"))
        self.gridLayout.addWidget(self.chkExternalNotificationAuto, 5, 0, 1, 1)
        self.cmbOnSingleClientInSearchResult = QtGui.QComboBox(registryPage)
        self.cmbOnSingleClientInSearchResult.setObjectName(_fromUtf8("cmbOnSingleClientInSearchResult"))
        self.cmbOnSingleClientInSearchResult.addItem(_fromUtf8(""))
        self.cmbOnSingleClientInSearchResult.setItemText(0, _fromUtf8(""))
        self.cmbOnSingleClientInSearchResult.addItem(_fromUtf8(""))
        self.cmbOnSingleClientInSearchResult.addItem(_fromUtf8(""))
        self.gridLayout.addWidget(self.cmbOnSingleClientInSearchResult, 3, 1, 1, 2)
        self.edtClientsLimit = QtGui.QSpinBox(registryPage)
        self.edtClientsLimit.setMinimum(1)
        self.edtClientsLimit.setMaximum(100000000)
        self.edtClientsLimit.setProperty("value", 10000)
        self.edtClientsLimit.setObjectName(_fromUtf8("edtClientsLimit"))
        self.gridLayout.addWidget(self.edtClientsLimit, 4, 1, 1, 1)
        self.lblClientsLimit = QtGui.QLabel(registryPage)
        self.lblClientsLimit.setObjectName(_fromUtf8("lblClientsLimit"))
        self.gridLayout.addWidget(self.lblClientsLimit, 4, 0, 1, 1)
        self.lblUserNotificationsMode = QtGui.QLabel(registryPage)
        self.lblUserNotificationsMode.setObjectName(_fromUtf8("lblUserNotificationsMode"))
        self.gridLayout.addWidget(self.lblUserNotificationsMode, 7, 0, 1, 1)
        self.rbnUserNotificationsModeStandard = QtGui.QRadioButton(registryPage)
        self.rbnUserNotificationsModeStandard.setObjectName(_fromUtf8("rbnUserNotificationsModeStandard"))
        self.gridLayout.addWidget(self.rbnUserNotificationsModeStandard, 7, 1, 1, 1)
        self.rbnUserNotificationsModeExtended = QtGui.QRadioButton(registryPage)
        self.rbnUserNotificationsModeExtended.setObjectName(_fromUtf8("rbnUserNotificationsModeExtended"))
        self.gridLayout.addWidget(self.rbnUserNotificationsModeExtended, 7, 2, 1, 1)
        self.lblClientsLimit.setBuddy(self.edtClientsLimit)
        self.lblUserNotificationsMode.setBuddy(self.edtClientsLimit)

        self.retranslateUi(registryPage)
        QtCore.QMetaObject.connectSlotsByName(registryPage)

    def retranslateUi(self, registryPage):
        registryPage.setWindowTitle(_translate("registryPage", "Картотека", None))
        self.cmbDoubleClickQueueClient.setItemText(1, _translate("registryPage", "Новое обращение", None))
        self.cmbDoubleClickQueueClient.setItemText(2, _translate("registryPage", "Изменить жалобы/примечания", None))
        self.cmbDoubleClickQueueClient.setItemText(3, _translate("registryPage", "Напечатать приглашение", None))
        self.cmbDoubleClickQueueClient.setItemText(4, _translate("registryPage", "Перейти в график", None))
        self.lblDoubleClickQueueClient.setText(_translate("registryPage", "Двойной щелчок в листе предварительной записи пациента", None))
        self.lblOnSingleClientInSearchResult.setText(_translate("registryPage", "После успешного поиска единственного пациента", None))
        self.chkExternalNotificationOnlyAttach.setText(_translate("registryPage", "Показывать только уведомления на прикрепленных пациентов", None))
        self.chkExternalNotificationAuto.setText(_translate("registryPage", "Автоматически открывать вкладку внешних уведомлений", None))
        self.cmbOnSingleClientInSearchResult.setItemText(1, _translate("registryPage", "Новое обращение", None))
        self.cmbOnSingleClientInSearchResult.setItemText(2, _translate("registryPage", "Открыть прививочную карту", None))
        self.lblClientsLimit.setText(_translate("registryPage", "Лимит списка пациентов в картотеке", None))
        self.lblUserNotificationsMode.setText(_translate("registryPage", "Режим отображения вкладки \"Уведомления\"", None))
        self.rbnUserNotificationsModeStandard.setText(_translate("registryPage", "Стандартный", None))
        self.rbnUserNotificationsModeExtended.setText(_translate("registryPage", "Расширенный", None))

