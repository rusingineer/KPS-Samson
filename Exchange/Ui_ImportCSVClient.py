# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\projects\samson\UP_s11\client_pre_release\Exchange\ImportCSVClient.ui'
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

class Ui_ImportCSVClient(object):
    def setupUi(self, ImportCSVClient):
        ImportCSVClient.setObjectName(_fromUtf8("ImportCSVClient"))
        ImportCSVClient.resize(472, 241)
        self.gridlayout = QtGui.QGridLayout(ImportCSVClient)
        self.gridlayout.setObjectName(_fromUtf8("gridlayout"))
        self.progressBar = CProgressBar(ImportCSVClient)
        self.progressBar.setProperty("value", 24)
        self.progressBar.setObjectName(_fromUtf8("progressBar"))
        self.gridlayout.addWidget(self.progressBar, 7, 0, 1, 2)
        self.lblElapsed = QtGui.QLabel(ImportCSVClient)
        self.lblElapsed.setText(_fromUtf8(""))
        self.lblElapsed.setObjectName(_fromUtf8("lblElapsed"))
        self.gridlayout.addWidget(self.lblElapsed, 8, 0, 1, 2)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.lblRevision = QtGui.QLabel(ImportCSVClient)
        self.lblRevision.setEnabled(False)
        self.lblRevision.setText(_fromUtf8(""))
        self.lblRevision.setObjectName(_fromUtf8("lblRevision"))
        self.horizontalLayout.addWidget(self.lblRevision)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.btnImportCSV = QtGui.QPushButton(ImportCSVClient)
        self.btnImportCSV.setObjectName(_fromUtf8("btnImportCSV"))
        self.horizontalLayout.addWidget(self.btnImportCSV)
        self.btnStart = QtGui.QPushButton(ImportCSVClient)
        self.btnStart.setObjectName(_fromUtf8("btnStart"))
        self.horizontalLayout.addWidget(self.btnStart)
        self.gridlayout.addLayout(self.horizontalLayout, 9, 0, 1, 2)
        self.formLayout = QtGui.QFormLayout()
        self.formLayout.setFieldGrowthPolicy(QtGui.QFormLayout.AllNonFixedFieldsGrow)
        self.formLayout.setObjectName(_fromUtf8("formLayout"))
        self.txtFileName = QtGui.QLabel(ImportCSVClient)
        self.txtFileName.setObjectName(_fromUtf8("txtFileName"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.txtFileName)
        self.fileName = QtGui.QLabel(ImportCSVClient)
        self.fileName.setObjectName(_fromUtf8("fileName"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.FieldRole, self.fileName)
        self.txtAllClients = QtGui.QLabel(ImportCSVClient)
        self.txtAllClients.setObjectName(_fromUtf8("txtAllClients"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.LabelRole, self.txtAllClients)
        self.numberAllClients = QtGui.QLabel(ImportCSVClient)
        self.numberAllClients.setObjectName(_fromUtf8("numberAllClients"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.FieldRole, self.numberAllClients)
        self.txtAddClients = QtGui.QLabel(ImportCSVClient)
        self.txtAddClients.setObjectName(_fromUtf8("txtAddClients"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.LabelRole, self.txtAddClients)
        self.numberAddClients = QtGui.QLabel(ImportCSVClient)
        self.numberAddClients.setObjectName(_fromUtf8("numberAddClients"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.FieldRole, self.numberAddClients)
        self.txtUpDateClients = QtGui.QLabel(ImportCSVClient)
        self.txtUpDateClients.setObjectName(_fromUtf8("txtUpDateClients"))
        self.formLayout.setWidget(3, QtGui.QFormLayout.LabelRole, self.txtUpDateClients)
        self.numberUpDateClients = QtGui.QLabel(ImportCSVClient)
        self.numberUpDateClients.setObjectName(_fromUtf8("numberUpDateClients"))
        self.formLayout.setWidget(3, QtGui.QFormLayout.FieldRole, self.numberUpDateClients)
        self.txtNoAddClients = QtGui.QLabel(ImportCSVClient)
        self.txtNoAddClients.setObjectName(_fromUtf8("txtNoAddClients"))
        self.formLayout.setWidget(4, QtGui.QFormLayout.LabelRole, self.txtNoAddClients)
        self.numberNoAddClients = QtGui.QLabel(ImportCSVClient)
        self.numberNoAddClients.setObjectName(_fromUtf8("numberNoAddClients"))
        self.formLayout.setWidget(4, QtGui.QFormLayout.FieldRole, self.numberNoAddClients)
        self.gridlayout.addLayout(self.formLayout, 5, 0, 1, 2)
        self.lblElapsed_2 = QtGui.QLabel(ImportCSVClient)
        self.lblElapsed_2.setText(_fromUtf8(""))
        self.lblElapsed_2.setObjectName(_fromUtf8("lblElapsed_2"))
        self.gridlayout.addWidget(self.lblElapsed_2, 6, 0, 1, 2)

        self.retranslateUi(ImportCSVClient)
        QtCore.QMetaObject.connectSlotsByName(ImportCSVClient)

    def retranslateUi(self, ImportCSVClient):
        ImportCSVClient.setWindowTitle(_translate("ImportCSVClient", "Form", None))
        self.btnImportCSV.setText(_translate("ImportCSVClient", "Обзор", None))
        self.btnStart.setText(_translate("ImportCSVClient", "Старт", None))
        self.txtFileName.setText(_translate("ImportCSVClient", "Выбран:", None))
        self.fileName.setText(_translate("ImportCSVClient", "-", None))
        self.txtAllClients.setText(_translate("ImportCSVClient", "Всего записей:", None))
        self.numberAllClients.setText(_translate("ImportCSVClient", "0", None))
        self.txtAddClients.setText(_translate("ImportCSVClient", "Добавили записей:", None))
        self.numberAddClients.setText(_translate("ImportCSVClient", "0", None))
        self.txtUpDateClients.setText(_translate("ImportCSVClient", "Уже имеется записей", None))
        self.numberUpDateClients.setText(_translate("ImportCSVClient", "0", None))
        self.txtNoAddClients.setText(_translate("ImportCSVClient", "Не добавленно записей", None))
        self.numberNoAddClients.setText(_translate("ImportCSVClient", "0", None))

from library.ProgressBar import CProgressBar
