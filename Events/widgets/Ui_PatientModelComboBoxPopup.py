# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'PatientModelComboBoxPopup.ui'
#
# Created by: PyQt4 UI code generator 4.12.1
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

class Ui_PatientModelComboBoxPopup(object):
    def setupUi(self, PatientModelComboBoxPopup):
        PatientModelComboBoxPopup.setObjectName(_fromUtf8("PatientModelComboBoxPopup"))
        PatientModelComboBoxPopup.resize(795, 338)
        self.gridlayout = QtGui.QGridLayout(PatientModelComboBoxPopup)
        self.gridlayout.setMargin(0)
        self.gridlayout.setSpacing(0)
        self.gridlayout.setObjectName(_fromUtf8("gridlayout"))
        self.tabWidget = QtGui.QTabWidget(PatientModelComboBoxPopup)
        self.tabWidget.setTabPosition(QtGui.QTabWidget.South)
        self.tabWidget.setTabShape(QtGui.QTabWidget.Rounded)
        self.tabWidget.setObjectName(_fromUtf8("tabWidget"))
        self.tabPatientModel = QtGui.QWidget()
        self.tabPatientModel.setObjectName(_fromUtf8("tabPatientModel"))
        self.vboxlayout = QtGui.QVBoxLayout(self.tabPatientModel)
        self.vboxlayout.setMargin(4)
        self.vboxlayout.setSpacing(4)
        self.vboxlayout.setObjectName(_fromUtf8("vboxlayout"))
        self.tblPatientModel = CTableView(self.tabPatientModel)
        self.tblPatientModel.setObjectName(_fromUtf8("tblPatientModel"))
        self.vboxlayout.addWidget(self.tblPatientModel)
        self.tabWidget.addTab(self.tabPatientModel, _fromUtf8(""))
        self.tabSearch = QtGui.QWidget()
        self.tabSearch.setObjectName(_fromUtf8("tabSearch"))
        self.gridlayout1 = QtGui.QGridLayout(self.tabSearch)
        self.gridlayout1.setMargin(4)
        self.gridlayout1.setSpacing(4)
        self.gridlayout1.setObjectName(_fromUtf8("gridlayout1"))
        self.chkFinalMKB = QtGui.QCheckBox(self.tabSearch)
        self.chkFinalMKB.setChecked(True)
        self.chkFinalMKB.setObjectName(_fromUtf8("chkFinalMKB"))
        self.gridlayout1.addWidget(self.chkFinalMKB, 4, 1, 1, 2)
        self.buttonBox = QtGui.QDialogButtonBox(self.tabSearch)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.buttonBox.sizePolicy().hasHeightForWidth())
        self.buttonBox.setSizePolicy(sizePolicy)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Apply|QtGui.QDialogButtonBox.Reset)
        self.buttonBox.setCenterButtons(False)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridlayout1.addWidget(self.buttonBox, 7, 2, 1, 1)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridlayout1.addItem(spacerItem, 7, 1, 1, 1)
        self.cmbQuoting = CClientQuotingModelPatientComboBox(self.tabSearch)
        self.cmbQuoting.setObjectName(_fromUtf8("cmbQuoting"))
        self.gridlayout1.addWidget(self.cmbQuoting, 0, 1, 1, 2)
        self.lblQuoting = QtGui.QLabel(self.tabSearch)
        self.lblQuoting.setObjectName(_fromUtf8("lblQuoting"))
        self.gridlayout1.addWidget(self.lblQuoting, 0, 0, 1, 1)
        self.chkPreviousMKB = QtGui.QCheckBox(self.tabSearch)
        self.chkPreviousMKB.setChecked(True)
        self.chkPreviousMKB.setObjectName(_fromUtf8("chkPreviousMKB"))
        self.gridlayout1.addWidget(self.chkPreviousMKB, 3, 1, 1, 2)
        spacerItem1 = QtGui.QSpacerItem(20, 141, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridlayout1.addItem(spacerItem1, 6, 1, 1, 1)
        self.chkQuotingPatientOnly = QtGui.QCheckBox(self.tabSearch)
        self.chkQuotingPatientOnly.setObjectName(_fromUtf8("chkQuotingPatientOnly"))
        self.gridlayout1.addWidget(self.chkQuotingPatientOnly, 2, 1, 1, 2)
        self.chkQuotingEvent = QtGui.QCheckBox(self.tabSearch)
        self.chkQuotingEvent.setChecked(True)
        self.chkQuotingEvent.setObjectName(_fromUtf8("chkQuotingEvent"))
        self.gridlayout1.addWidget(self.chkQuotingEvent, 5, 1, 1, 2)
        self.edtName = QtGui.QLineEdit(self.tabSearch)
        self.edtName.setObjectName(_fromUtf8("edtName"))
        self.gridlayout1.addWidget(self.edtName, 1, 1, 1, 2)
        self.lblName = QtGui.QLabel(self.tabSearch)
        self.lblName.setObjectName(_fromUtf8("lblName"))
        self.gridlayout1.addWidget(self.lblName, 1, 0, 1, 1)
        self.tabWidget.addTab(self.tabSearch, _fromUtf8(""))
        self.gridlayout.addWidget(self.tabWidget, 0, 0, 1, 1)

        self.retranslateUi(PatientModelComboBoxPopup)
        self.tabWidget.setCurrentIndex(1)
        QtCore.QMetaObject.connectSlotsByName(PatientModelComboBoxPopup)
        PatientModelComboBoxPopup.setTabOrder(self.tabWidget, self.buttonBox)
        PatientModelComboBoxPopup.setTabOrder(self.buttonBox, self.tblPatientModel)

    def retranslateUi(self, PatientModelComboBoxPopup):
        PatientModelComboBoxPopup.setWindowTitle(_translate("PatientModelComboBoxPopup", "Form", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabPatientModel), _translate("PatientModelComboBoxPopup", "Результат поиска", None))
        self.chkFinalMKB.setText(_translate("PatientModelComboBoxPopup", "Учитывать заключительный диагноз", None))
        self.lblQuoting.setText(_translate("PatientModelComboBoxPopup", "Квота", None))
        self.chkPreviousMKB.setText(_translate("PatientModelComboBoxPopup", "Учитывать предварительный диагноз", None))
        self.chkQuotingPatientOnly.setText(_translate("PatientModelComboBoxPopup", "Учитывать только квоты пациента", None))
        self.chkQuotingEvent.setText(_translate("PatientModelComboBoxPopup", "Учитывать квоту, определенную в Событии", None))
        self.lblName.setText(_translate("PatientModelComboBoxPopup", "Наименование", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabSearch), _translate("PatientModelComboBoxPopup", "&Поиск", None))

from Quoting.QuotaTypeComboBox import CClientQuotingModelPatientComboBox
from library.TableView import CTableView
