# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Projects\Samson\UP_s11\client_test\preferences\UISComPage.ui'
#
# Created: Thu Sep 10 15:16:44 2026
#      by: PyQt4 UI code generator 4.11.3
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

class Ui_UISComPage(object):
    def setupUi(self, UISComPage):
        UISComPage.setObjectName(_fromUtf8("UISComPage"))
        UISComPage.resize(651, 405)
        self.gridLayout = QtGui.QGridLayout(UISComPage)
        self.gridLayout.setMargin(4)
        self.gridLayout.setSpacing(4)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.lblUISComEnabled = QtGui.QLabel(UISComPage)
        self.lblUISComEnabled.setObjectName(_fromUtf8("lblUISComEnabled"))
        self.gridLayout.addWidget(self.lblUISComEnabled, 2, 0, 1, 1)
        spacerItem = QtGui.QSpacerItem(400, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 2, 2, 1, 1)
        spacerItem1 = QtGui.QSpacerItem(20, 1, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem1, 4, 0, 1, 1)
        self.chkUISComEnabled = QtGui.QCheckBox(UISComPage)
        self.chkUISComEnabled.setText(_fromUtf8(""))
        self.chkUISComEnabled.setObjectName(_fromUtf8("chkUISComEnabled"))
        self.gridLayout.addWidget(self.chkUISComEnabled, 2, 1, 1, 1)
        self.label = QtGui.QLabel(UISComPage)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 3, 0, 1, 1)
        self.chkIncCallNotification = QtGui.QCheckBox(UISComPage)
        self.chkIncCallNotification.setText(_fromUtf8(""))
        self.chkIncCallNotification.setObjectName(_fromUtf8("chkIncCallNotification"))
        self.gridLayout.addWidget(self.chkIncCallNotification, 3, 1, 1, 1)
        self.lblUISComEnabled.setBuddy(self.chkUISComEnabled)

        self.retranslateUi(UISComPage)
        QtCore.QMetaObject.connectSlotsByName(UISComPage)

    def retranslateUi(self, UISComPage):
        UISComPage.setWindowTitle(_translate("UISComPage", "Настройки облачной телефонии \"UISCom\"", None))
        UISComPage.setToolTip(_translate("UISComPage", "Настройка облачной телефонии \"UISCom\"", None))
        self.lblUISComEnabled.setText(_translate("UISComPage", "Включено", None))
        self.label.setText(_translate("UISComPage", "Оповещения о вызовах", None))

