# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Projects\Samson\UP_s11\client_test\Exchange\ExportVMPCases.ui'
#
# Created: Thu Oct 16 15:28:53 2025
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

class Ui_ExportVMPCases(object):
    def setupUi(self, ExportVMPCases):
        ExportVMPCases.setObjectName(_fromUtf8("ExportVMPCases"))
        ExportVMPCases.resize(479, 361)
        self.gridlayout = QtGui.QGridLayout(ExportVMPCases)
        self.gridlayout.setObjectName(_fromUtf8("gridlayout"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.label_2 = QtGui.QLabel(ExportVMPCases)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.horizontalLayout.addWidget(self.label_2)
        self.edtBegDate = CDateEdit(ExportVMPCases)
        self.edtBegDate.setObjectName(_fromUtf8("edtBegDate"))
        self.horizontalLayout.addWidget(self.edtBegDate)
        self.lblEndDate = QtGui.QLabel(ExportVMPCases)
        self.lblEndDate.setObjectName(_fromUtf8("lblEndDate"))
        self.horizontalLayout.addWidget(self.lblEndDate)
        self.edtEndDate = CDateEdit(ExportVMPCases)
        self.edtEndDate.setObjectName(_fromUtf8("edtEndDate"))
        self.horizontalLayout.addWidget(self.edtEndDate)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.gridlayout.addLayout(self.horizontalLayout, 2, 0, 1, 1)
        self.statusLabel = QtGui.QLabel(ExportVMPCases)
        self.statusLabel.setText(_fromUtf8(""))
        self.statusLabel.setObjectName(_fromUtf8("statusLabel"))
        self.gridlayout.addWidget(self.statusLabel, 6, 0, 1, 1)
        spacerItem1 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridlayout.addItem(spacerItem1, 7, 0, 1, 1)
        self.logBrowser = QtGui.QTextBrowser(ExportVMPCases)
        self.logBrowser.setObjectName(_fromUtf8("logBrowser"))
        self.gridlayout.addWidget(self.logBrowser, 5, 0, 1, 1)
        self.progressBar = CProgressBar(ExportVMPCases)
        self.progressBar.setProperty("value", 24)
        self.progressBar.setOrientation(QtCore.Qt.Horizontal)
        self.progressBar.setObjectName(_fromUtf8("progressBar"))
        self.gridlayout.addWidget(self.progressBar, 4, 0, 1, 1)
        self.hboxlayout = QtGui.QHBoxLayout()
        self.hboxlayout.setSpacing(6)
        self.hboxlayout.setMargin(0)
        self.hboxlayout.setObjectName(_fromUtf8("hboxlayout"))
        self.label = QtGui.QLabel(ExportVMPCases)
        self.label.setObjectName(_fromUtf8("label"))
        self.hboxlayout.addWidget(self.label)
        self.edtDirPath = QtGui.QLineEdit(ExportVMPCases)
        self.edtDirPath.setObjectName(_fromUtf8("edtDirPath"))
        self.hboxlayout.addWidget(self.edtDirPath)
        self.btnSelectDir = QtGui.QToolButton(ExportVMPCases)
        self.btnSelectDir.setObjectName(_fromUtf8("btnSelectDir"))
        self.hboxlayout.addWidget(self.btnSelectDir)
        self.gridlayout.addLayout(self.hboxlayout, 0, 0, 1, 1)
        self.hboxlayout1 = QtGui.QHBoxLayout()
        self.hboxlayout1.setSpacing(6)
        self.hboxlayout1.setMargin(0)
        self.hboxlayout1.setObjectName(_fromUtf8("hboxlayout1"))
        self.btnExport = QtGui.QPushButton(ExportVMPCases)
        self.btnExport.setEnabled(False)
        self.btnExport.setObjectName(_fromUtf8("btnExport"))
        self.hboxlayout1.addWidget(self.btnExport)
        spacerItem2 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.hboxlayout1.addItem(spacerItem2)
        self.btnAbort = QtGui.QPushButton(ExportVMPCases)
        self.btnAbort.setEnabled(False)
        self.btnAbort.setObjectName(_fromUtf8("btnAbort"))
        self.hboxlayout1.addWidget(self.btnAbort)
        self.btnClose = QtGui.QPushButton(ExportVMPCases)
        self.btnClose.setObjectName(_fromUtf8("btnClose"))
        self.hboxlayout1.addWidget(self.btnClose)
        self.gridlayout.addLayout(self.hboxlayout1, 8, 0, 1, 1)

        self.retranslateUi(ExportVMPCases)
        QtCore.QMetaObject.connectSlotsByName(ExportVMPCases)

    def retranslateUi(self, ExportVMPCases):
        ExportVMPCases.setWindowTitle(_translate("ExportVMPCases", "Экспорт талонов ВМП", None))
        self.label_2.setText(_translate("ExportVMPCases", "Дата начала периода:", None))
        self.lblEndDate.setText(_translate("ExportVMPCases", "Дата окончания периода:", None))
        self.label.setText(_translate("ExportVMPCases", "Сохранить в", None))
        self.btnSelectDir.setText(_translate("ExportVMPCases", "...", None))
        self.btnExport.setText(_translate("ExportVMPCases", "Начать экспорт", None))
        self.btnAbort.setText(_translate("ExportVMPCases", "Прервать", None))
        self.btnClose.setText(_translate("ExportVMPCases", "Закрыть", None))

from library.ProgressBar import CProgressBar
from library.DateEdit import CDateEdit
