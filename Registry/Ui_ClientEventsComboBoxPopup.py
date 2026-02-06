# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\projects\Samson\UP_s11\client\Registry\ClientEventsComboBoxPopup.ui'
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

class Ui_ClientEventsComboBoxPopup(object):
    def setupUi(self, ClientEventsComboBoxPopup):
        ClientEventsComboBoxPopup.setObjectName(_fromUtf8("ClientEventsComboBoxPopup"))
        ClientEventsComboBoxPopup.resize(455, 344)
        self.gridLayout = QtGui.QGridLayout(ClientEventsComboBoxPopup)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.tblClientEvents = CTableView(ClientEventsComboBoxPopup)
        self.tblClientEvents.setObjectName(_fromUtf8("tblClientEvents"))
        self.gridLayout.addWidget(self.tblClientEvents, 0, 0, 1, 2)

        self.retranslateUi(ClientEventsComboBoxPopup)
        QtCore.QMetaObject.connectSlotsByName(ClientEventsComboBoxPopup)

    def retranslateUi(self, ClientEventsComboBoxPopup):
        ClientEventsComboBoxPopup.setWindowTitle(_translate("ClientEventsComboBoxPopup", "Form", None))

from library.TableView import CTableView
