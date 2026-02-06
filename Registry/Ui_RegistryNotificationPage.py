# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\projects\Samson\UP_s11\client\Registry\RegistryNotificationPage.ui'
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

class Ui_RegistryNotificationPage(object):
    def setupUi(self, RegistryNotificationPage):
        RegistryNotificationPage.setObjectName(_fromUtf8("RegistryNotificationPage"))
        RegistryNotificationPage.resize(1137, 824)
        self.horizontalLayout = QtGui.QHBoxLayout(RegistryNotificationPage)
        self.horizontalLayout.setMargin(2)
        self.horizontalLayout.setSpacing(2)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.grpTables = QtGui.QWidget(RegistryNotificationPage)
        self.grpTables.setObjectName(_fromUtf8("grpTables"))
        self.verticalLayout = QtGui.QVBoxLayout(self.grpTables)
        self.verticalLayout.setMargin(2)
        self.verticalLayout.setSpacing(2)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.tblNotificationList = CTableView(self.grpTables)
        self.tblNotificationList.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.tblNotificationList.setObjectName(_fromUtf8("tblNotificationList"))
        self.verticalLayout.addWidget(self.tblNotificationList)
        self.lblRecordCount = QtGui.QLabel(self.grpTables)
        self.lblRecordCount.setObjectName(_fromUtf8("lblRecordCount"))
        self.verticalLayout.addWidget(self.lblRecordCount)
        self.horizontalLayout.addWidget(self.grpTables)

        self.retranslateUi(RegistryNotificationPage)
        QtCore.QMetaObject.connectSlotsByName(RegistryNotificationPage)

    def retranslateUi(self, RegistryNotificationPage):
        RegistryNotificationPage.setWindowTitle(_translate("RegistryNotificationPage", "Уведомления", None))
        self.lblRecordCount.setText(_translate("RegistryNotificationPage", "Список пуст", None))

from library.TableView import CTableView
