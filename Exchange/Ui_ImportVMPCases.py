# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Projects\Samson\UP_s11\client_test\Exchange\ImportVMPCases.ui'
#
# Created: Thu Oct 16 15:29:00 2025
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

class Ui_ImportVMPCases(object):
    def setupUi(self, ImportVMPCases):
        ImportVMPCases.setObjectName(_fromUtf8("ImportVMPCases"))
        ImportVMPCases.resize(480, 377)
        self.gridlayout = QtGui.QGridLayout(ImportVMPCases)
        self.gridlayout.setObjectName(_fromUtf8("gridlayout"))
        self.statusLabel = QtGui.QLabel(ImportVMPCases)
        self.statusLabel.setText(_fromUtf8(""))
        self.statusLabel.setObjectName(_fromUtf8("statusLabel"))
        self.gridlayout.addWidget(self.statusLabel, 4, 0, 1, 1)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridlayout.addItem(spacerItem, 5, 0, 1, 1)
        self.vboxlayout = QtGui.QVBoxLayout()
        self.vboxlayout.setObjectName(_fromUtf8("vboxlayout"))
        self.gridlayout.addLayout(self.vboxlayout, 1, 0, 1, 1)
        self.progressBar = CProgressBar(ImportVMPCases)
        self.progressBar.setProperty("value", 24)
        self.progressBar.setOrientation(QtCore.Qt.Horizontal)
        self.progressBar.setObjectName(_fromUtf8("progressBar"))
        self.gridlayout.addWidget(self.progressBar, 2, 0, 1, 1)
        self.hboxlayout = QtGui.QHBoxLayout()
        self.hboxlayout.setSpacing(6)
        self.hboxlayout.setMargin(0)
        self.hboxlayout.setObjectName(_fromUtf8("hboxlayout"))
        self.label = QtGui.QLabel(ImportVMPCases)
        self.label.setObjectName(_fromUtf8("label"))
        self.hboxlayout.addWidget(self.label)
        self.edtFileName = QtGui.QLineEdit(ImportVMPCases)
        self.edtFileName.setObjectName(_fromUtf8("edtFileName"))
        self.hboxlayout.addWidget(self.edtFileName)
        self.btnSelectFile = QtGui.QToolButton(ImportVMPCases)
        self.btnSelectFile.setObjectName(_fromUtf8("btnSelectFile"))
        self.hboxlayout.addWidget(self.btnSelectFile)
        self.gridlayout.addLayout(self.hboxlayout, 0, 0, 1, 1)
        self.logBrowser = QtGui.QTextBrowser(ImportVMPCases)
        self.logBrowser.setObjectName(_fromUtf8("logBrowser"))
        self.gridlayout.addWidget(self.logBrowser, 3, 0, 1, 1)
        self.hboxlayout1 = QtGui.QHBoxLayout()
        self.hboxlayout1.setSpacing(6)
        self.hboxlayout1.setMargin(0)
        self.hboxlayout1.setObjectName(_fromUtf8("hboxlayout1"))
        self.btnImport = QtGui.QPushButton(ImportVMPCases)
        self.btnImport.setEnabled(False)
        self.btnImport.setObjectName(_fromUtf8("btnImport"))
        self.hboxlayout1.addWidget(self.btnImport)
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.hboxlayout1.addItem(spacerItem1)
        self.btnAbort = QtGui.QPushButton(ImportVMPCases)
        self.btnAbort.setEnabled(False)
        self.btnAbort.setObjectName(_fromUtf8("btnAbort"))
        self.hboxlayout1.addWidget(self.btnAbort)
        self.btnClose = QtGui.QPushButton(ImportVMPCases)
        self.btnClose.setObjectName(_fromUtf8("btnClose"))
        self.hboxlayout1.addWidget(self.btnClose)
        self.gridlayout.addLayout(self.hboxlayout1, 6, 0, 1, 1)

        self.retranslateUi(ImportVMPCases)
        QtCore.QMetaObject.connectSlotsByName(ImportVMPCases)

    def retranslateUi(self, ImportVMPCases):
        ImportVMPCases.setWindowTitle(_translate("ImportVMPCases", "Импорт талонов ВМП", None))
        self.label.setText(_translate("ImportVMPCases", "Загрузить из", None))
        self.btnSelectFile.setText(_translate("ImportVMPCases", "...", None))
        self.btnImport.setText(_translate("ImportVMPCases", "Начать импорт", None))
        self.btnAbort.setText(_translate("ImportVMPCases", "Прервать", None))
        self.btnClose.setText(_translate("ImportVMPCases", "Закрыть", None))

from library.ProgressBar import CProgressBar
