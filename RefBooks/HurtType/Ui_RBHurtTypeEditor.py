# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\Samson\UP_s11\client\RefBooks\HurtType\RBHurtTypeEditor.ui'
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

class Ui_RBHurtTypeEditor(object):
    def setupUi(self, RBHurtTypeEditor):
        RBHurtTypeEditor.setObjectName(_fromUtf8("RBHurtTypeEditor"))
        RBHurtTypeEditor.resize(502, 324)
        RBHurtTypeEditor.setSizeGripEnabled(False)
        self.gridLayout = QtGui.QGridLayout(RBHurtTypeEditor)
        self.gridLayout.setMargin(4)
        self.gridLayout.setSpacing(4)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.lblCode = QtGui.QLabel(RBHurtTypeEditor)
        self.lblCode.setObjectName(_fromUtf8("lblCode"))
        self.gridLayout.addWidget(self.lblCode, 0, 0, 1, 1)
        self.edtCode = QtGui.QLineEdit(RBHurtTypeEditor)
        self.edtCode.setObjectName(_fromUtf8("edtCode"))
        self.gridLayout.addWidget(self.edtCode, 0, 1, 1, 1)
        self.lblName = QtGui.QLabel(RBHurtTypeEditor)
        self.lblName.setObjectName(_fromUtf8("lblName"))
        self.gridLayout.addWidget(self.lblName, 1, 0, 1, 1)
        self.edtName = QtGui.QLineEdit(RBHurtTypeEditor)
        self.edtName.setObjectName(_fromUtf8("edtName"))
        self.gridLayout.addWidget(self.edtName, 1, 1, 1, 1)
        self.tabWidget = QtGui.QTabWidget(RBHurtTypeEditor)
        self.tabWidget.setObjectName(_fromUtf8("tabWidget"))
        self.tabDiagnosis = QtGui.QWidget()
        self.tabDiagnosis.setObjectName(_fromUtf8("tabDiagnosis"))
        self.gridLayout_2 = QtGui.QGridLayout(self.tabDiagnosis)
        self.gridLayout_2.setMargin(4)
        self.gridLayout_2.setSpacing(4)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.tblDiagnosis = CInDocTableView(self.tabDiagnosis)
        self.tblDiagnosis.setObjectName(_fromUtf8("tblDiagnosis"))
        self.gridLayout_2.addWidget(self.tblDiagnosis, 0, 0, 1, 1)
        self.tabWidget.addTab(self.tabDiagnosis, _fromUtf8(""))
        self.tabInfections = QtGui.QWidget()
        self.tabInfections.setObjectName(_fromUtf8("tabInfections"))
        self.gridLayout_3 = QtGui.QGridLayout(self.tabInfections)
        self.gridLayout_3.setMargin(4)
        self.gridLayout_3.setSpacing(4)
        self.gridLayout_3.setObjectName(_fromUtf8("gridLayout_3"))
        self.tblInfections = CInDocTableView(self.tabInfections)
        self.tblInfections.setObjectName(_fromUtf8("tblInfections"))
        self.gridLayout_3.addWidget(self.tblInfections, 0, 0, 1, 1)
        self.tabWidget.addTab(self.tabInfections, _fromUtf8(""))
        self.tabIdentification = QtGui.QWidget()
        self.tabIdentification.setObjectName(_fromUtf8("tabIdentification"))
        self.gridLayout_4 = QtGui.QGridLayout(self.tabIdentification)
        self.gridLayout_4.setMargin(4)
        self.gridLayout_4.setSpacing(4)
        self.gridLayout_4.setObjectName(_fromUtf8("gridLayout_4"))
        self.tblIdentification = CInDocTableView(self.tabIdentification)
        self.tblIdentification.setObjectName(_fromUtf8("tblIdentification"))
        self.gridLayout_4.addWidget(self.tblIdentification, 0, 0, 1, 1)
        self.tabWidget.addTab(self.tabIdentification, _fromUtf8(""))
        self.gridLayout.addWidget(self.tabWidget, 2, 0, 1, 2)
        self.buttonBox = QtGui.QDialogButtonBox(RBHurtTypeEditor)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 3, 0, 1, 2)
        self.lblCode.setBuddy(self.edtCode)
        self.lblName.setBuddy(self.edtName)

        self.retranslateUi(RBHurtTypeEditor)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), RBHurtTypeEditor.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), RBHurtTypeEditor.reject)
        QtCore.QMetaObject.connectSlotsByName(RBHurtTypeEditor)
        RBHurtTypeEditor.setTabOrder(self.edtCode, self.edtName)
        RBHurtTypeEditor.setTabOrder(self.edtName, self.tabWidget)
        RBHurtTypeEditor.setTabOrder(self.tabWidget, self.tblDiagnosis)
        RBHurtTypeEditor.setTabOrder(self.tblDiagnosis, self.tblInfections)
        RBHurtTypeEditor.setTabOrder(self.tblInfections, self.tblIdentification)
        RBHurtTypeEditor.setTabOrder(self.tblIdentification, self.buttonBox)

    def retranslateUi(self, RBHurtTypeEditor):
        RBHurtTypeEditor.setWindowTitle(_translate("RBHurtTypeEditor", "ChangeMe!", None))
        self.lblCode.setText(_translate("RBHurtTypeEditor", "&Код", None))
        self.lblName.setText(_translate("RBHurtTypeEditor", "&Наименование", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabDiagnosis), _translate("RBHurtTypeEditor", "Диагнозы", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabInfections), _translate("RBHurtTypeEditor", "Инфекции", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabIdentification), _translate("RBHurtTypeEditor", "Идентификация", None))

from library.InDocTable import CInDocTableView
