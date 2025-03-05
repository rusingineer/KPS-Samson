# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\projects\samson\UP_s11\client_pre_release\appendix\mes\ExchangeLocal\ExportXML_Wizard_2.ui'
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

class Ui_ExportXML_Wizard_2(object):
    def setupUi(self, ExportXML_Wizard_2):
        ExportXML_Wizard_2.setObjectName(_fromUtf8("ExportXML_Wizard_2"))
        ExportXML_Wizard_2.resize(400, 271)
        self.gridLayout = QtGui.QGridLayout(ExportXML_Wizard_2)
        self.gridLayout.setMargin(0)
        self.gridLayout.setSpacing(4)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setSpacing(4)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.lblFileName = QtGui.QLabel(ExportXML_Wizard_2)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblFileName.sizePolicy().hasHeightForWidth())
        self.lblFileName.setSizePolicy(sizePolicy)
        self.lblFileName.setObjectName(_fromUtf8("lblFileName"))
        self.horizontalLayout.addWidget(self.lblFileName)
        self.edtFileName = QtGui.QLineEdit(ExportXML_Wizard_2)
        self.edtFileName.setObjectName(_fromUtf8("edtFileName"))
        self.horizontalLayout.addWidget(self.edtFileName)
        self.btnSelectFile = QtGui.QToolButton(ExportXML_Wizard_2)
        self.btnSelectFile.setObjectName(_fromUtf8("btnSelectFile"))
        self.horizontalLayout.addWidget(self.btnSelectFile)
        self.gridLayout.addLayout(self.horizontalLayout, 0, 0, 1, 3)
        self.checkRAR = QtGui.QCheckBox(ExportXML_Wizard_2)
        self.checkRAR.setCheckable(True)
        self.checkRAR.setObjectName(_fromUtf8("checkRAR"))
        self.gridLayout.addWidget(self.checkRAR, 1, 0, 1, 3)
        spacerItem = QtGui.QSpacerItem(397, 79, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, 2, 0, 1, 3)
        self.progressBar = CProgressBar(ExportXML_Wizard_2)
        self.progressBar.setProperty("value", 24)
        self.progressBar.setOrientation(QtCore.Qt.Horizontal)
        self.progressBar.setObjectName(_fromUtf8("progressBar"))
        self.gridLayout.addWidget(self.progressBar, 3, 0, 1, 3)
        spacerItem1 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem1, 4, 0, 1, 3)
        spacerItem2 = QtGui.QSpacerItem(278, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem2, 5, 0, 1, 2)
        self.btnExport = QtGui.QPushButton(ExportXML_Wizard_2)
        self.btnExport.setEnabled(False)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btnExport.sizePolicy().hasHeightForWidth())
        self.btnExport.setSizePolicy(sizePolicy)
        self.btnExport.setObjectName(_fromUtf8("btnExport"))
        self.gridLayout.addWidget(self.btnExport, 5, 2, 1, 1)

        self.retranslateUi(ExportXML_Wizard_2)
        QtCore.QMetaObject.connectSlotsByName(ExportXML_Wizard_2)
        ExportXML_Wizard_2.setTabOrder(self.edtFileName, self.btnSelectFile)
        ExportXML_Wizard_2.setTabOrder(self.btnSelectFile, self.checkRAR)

    def retranslateUi(self, ExportXML_Wizard_2):
        ExportXML_Wizard_2.setWindowTitle(_translate("ExportXML_Wizard_2", "Выбор файла и процесс", None))
        self.lblFileName.setText(_translate("ExportXML_Wizard_2", "Экспортировать в", None))
        self.btnSelectFile.setText(_translate("ExportXML_Wizard_2", "...", None))
        self.checkRAR.setText(_translate("ExportXML_Wizard_2", "Архивировать rar", None))
        self.btnExport.setText(_translate("ExportXML_Wizard_2", "Начать экспорт", None))

from library.ProgressBar import CProgressBar
