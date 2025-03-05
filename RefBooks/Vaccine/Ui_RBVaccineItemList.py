# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\Samson\UP_s11\client\RefBooks\Vaccine\RBVaccineItemList.ui'
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

class Ui_RBVaccineItemList(object):
    def setupUi(self, RBVaccineItemList):
        RBVaccineItemList.setObjectName(_fromUtf8("RBVaccineItemList"))
        RBVaccineItemList.resize(556, 499)
        self.verticalLayout_5 = QtGui.QVBoxLayout(RBVaccineItemList)
        self.verticalLayout_5.setObjectName(_fromUtf8("verticalLayout_5"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.label_2 = QtGui.QLabel(RBVaccineItemList)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.horizontalLayout.addWidget(self.label_2)
        self.edtCode = QtGui.QLineEdit(RBVaccineItemList)
        self.edtCode.setObjectName(_fromUtf8("edtCode"))
        self.horizontalLayout.addWidget(self.edtCode)
        self.label_3 = QtGui.QLabel(RBVaccineItemList)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.horizontalLayout.addWidget(self.label_3)
        self.edtName = QtGui.QLineEdit(RBVaccineItemList)
        self.edtName.setObjectName(_fromUtf8("edtName"))
        self.horizontalLayout.addWidget(self.edtName)
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.verticalLayout_5.addLayout(self.horizontalLayout)
        self.splitter = QtGui.QSplitter(RBVaccineItemList)
        self.splitter.setOrientation(QtCore.Qt.Vertical)
        self.splitter.setObjectName(_fromUtf8("splitter"))
        self.pnlItems = QtGui.QWidget(self.splitter)
        self.pnlItems.setObjectName(_fromUtf8("pnlItems"))
        self.verticalLayout = QtGui.QVBoxLayout(self.pnlItems)
        self.verticalLayout.setMargin(0)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.tblItems = CTableView(self.pnlItems)
        self.tblItems.setObjectName(_fromUtf8("tblItems"))
        self.verticalLayout.addWidget(self.tblItems)
        self.pnlInfections = QtGui.QWidget(self.splitter)
        self.pnlInfections.setObjectName(_fromUtf8("pnlInfections"))
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.pnlInfections)
        self.verticalLayout_2.setMargin(0)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.tblVaccineInfections = CTableView(self.pnlInfections)
        self.tblVaccineInfections.setObjectName(_fromUtf8("tblVaccineInfections"))
        self.verticalLayout_2.addWidget(self.tblVaccineInfections)
        self.pnlVaccineSchemes = QtGui.QWidget(self.splitter)
        self.pnlVaccineSchemes.setObjectName(_fromUtf8("pnlVaccineSchemes"))
        self.verticalLayout_3 = QtGui.QVBoxLayout(self.pnlVaccineSchemes)
        self.verticalLayout_3.setMargin(0)
        self.verticalLayout_3.setSpacing(0)
        self.verticalLayout_3.setObjectName(_fromUtf8("verticalLayout_3"))
        self.tblVaccineSchemes = CTableView(self.pnlVaccineSchemes)
        self.tblVaccineSchemes.setObjectName(_fromUtf8("tblVaccineSchemes"))
        self.verticalLayout_3.addWidget(self.tblVaccineSchemes)
        self.pnlVaccineSchemaTransitions = QtGui.QWidget(self.splitter)
        self.pnlVaccineSchemaTransitions.setObjectName(_fromUtf8("pnlVaccineSchemaTransitions"))
        self.verticalLayout_4 = QtGui.QVBoxLayout(self.pnlVaccineSchemaTransitions)
        self.verticalLayout_4.setMargin(0)
        self.verticalLayout_4.setSpacing(0)
        self.verticalLayout_4.setObjectName(_fromUtf8("verticalLayout_4"))
        self.tblVaccineSchemaTransitions = CTableView(self.pnlVaccineSchemaTransitions)
        self.tblVaccineSchemaTransitions.setObjectName(_fromUtf8("tblVaccineSchemaTransitions"))
        self.verticalLayout_4.addWidget(self.tblVaccineSchemaTransitions)
        self.verticalLayout_5.addWidget(self.splitter)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.label = QtGui.QLabel(RBVaccineItemList)
        self.label.setObjectName(_fromUtf8("label"))
        self.horizontalLayout_2.addWidget(self.label)
        self.buttonBox = QtGui.QDialogButtonBox(RBVaccineItemList)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Close)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.horizontalLayout_2.addWidget(self.buttonBox)
        self.verticalLayout_5.addLayout(self.horizontalLayout_2)

        self.retranslateUi(RBVaccineItemList)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), RBVaccineItemList.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), RBVaccineItemList.reject)
        QtCore.QMetaObject.connectSlotsByName(RBVaccineItemList)
        RBVaccineItemList.setTabOrder(self.tblItems, self.tblVaccineInfections)
        RBVaccineItemList.setTabOrder(self.tblVaccineInfections, self.tblVaccineSchemes)
        RBVaccineItemList.setTabOrder(self.tblVaccineSchemes, self.tblVaccineSchemaTransitions)
        RBVaccineItemList.setTabOrder(self.tblVaccineSchemaTransitions, self.buttonBox)

    def retranslateUi(self, RBVaccineItemList):
        RBVaccineItemList.setWindowTitle(_translate("RBVaccineItemList", "Dialog", None))
        self.label_2.setText(_translate("RBVaccineItemList", "код содержит", None))
        self.label_3.setText(_translate("RBVaccineItemList", "название содержит", None))
        self.label.setText(_translate("RBVaccineItemList", "Всего", None))

from library.TableView import CTableView
