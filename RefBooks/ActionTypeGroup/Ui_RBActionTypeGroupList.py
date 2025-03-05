# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\projects\samson\UP_s11\client_pre_release\RefBooks\ActionTypeGroup\RBActionTypeGroupList.ui'
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

class Ui_RBActionTypeGroupList(object):
    def setupUi(self, RBActionTypeGroupList):
        RBActionTypeGroupList.setObjectName(_fromUtf8("RBActionTypeGroupList"))
        RBActionTypeGroupList.resize(694, 293)
        self.verticalLayout_3 = QtGui.QVBoxLayout(RBActionTypeGroupList)
        self.verticalLayout_3.setObjectName(_fromUtf8("verticalLayout_3"))
        self.splitter = QtGui.QSplitter(RBActionTypeGroupList)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName(_fromUtf8("splitter"))
        self.wgtActionTypeGroups = QtGui.QWidget(self.splitter)
        self.wgtActionTypeGroups.setObjectName(_fromUtf8("wgtActionTypeGroups"))
        self.verticalLayout = QtGui.QVBoxLayout(self.wgtActionTypeGroups)
        self.verticalLayout.setMargin(0)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.tblActionTypeGroups = CTableView(self.wgtActionTypeGroups)
        self.tblActionTypeGroups.setObjectName(_fromUtf8("tblActionTypeGroups"))
        self.verticalLayout.addWidget(self.tblActionTypeGroups)
        self.wgtActionTypeGroupItems = QtGui.QWidget(self.splitter)
        self.wgtActionTypeGroupItems.setObjectName(_fromUtf8("wgtActionTypeGroupItems"))
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.wgtActionTypeGroupItems)
        self.verticalLayout_2.setMargin(0)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.tblActionTypeGroupItems = CTableView(self.wgtActionTypeGroupItems)
        self.tblActionTypeGroupItems.setObjectName(_fromUtf8("tblActionTypeGroupItems"))
        self.verticalLayout_2.addWidget(self.tblActionTypeGroupItems)
        self.verticalLayout_3.addWidget(self.splitter)
        self.buttonBox = QtGui.QDialogButtonBox(RBActionTypeGroupList)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Close)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.verticalLayout_3.addWidget(self.buttonBox)

        self.retranslateUi(RBActionTypeGroupList)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), RBActionTypeGroupList.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), RBActionTypeGroupList.reject)
        QtCore.QMetaObject.connectSlotsByName(RBActionTypeGroupList)

    def retranslateUi(self, RBActionTypeGroupList):
        RBActionTypeGroupList.setWindowTitle(_translate("RBActionTypeGroupList", "Dialog", None))

from library.TableView import CTableView
