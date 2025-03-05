# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\projects\samson\UP_s11\client_pre_release\Reports\ReportView.ui'
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

class Ui_ReportViewDialog(object):
    def setupUi(self, ReportViewDialog):
        ReportViewDialog.setObjectName(_fromUtf8("ReportViewDialog"))
        ReportViewDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        ReportViewDialog.resize(651, 544)
        ReportViewDialog.setSizeGripEnabled(True)
        self.gridLayout = QtGui.QGridLayout(ReportViewDialog)
        self.gridLayout.setMargin(4)
        self.gridLayout.setSpacing(4)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.layoutFind = QtGui.QHBoxLayout()
        self.layoutFind.setObjectName(_fromUtf8("layoutFind"))
        self.lblFind = QtGui.QLabel(ReportViewDialog)
        self.lblFind.setObjectName(_fromUtf8("lblFind"))
        self.layoutFind.addWidget(self.lblFind)
        self.edtFind = QtGui.QLineEdit(ReportViewDialog)
        self.edtFind.setObjectName(_fromUtf8("edtFind"))
        self.layoutFind.addWidget(self.edtFind)
        self.btnFindNext = QtGui.QPushButton(ReportViewDialog)
        self.btnFindNext.setObjectName(_fromUtf8("btnFindNext"))
        self.layoutFind.addWidget(self.btnFindNext)
        self.btnFindPrev = QtGui.QPushButton(ReportViewDialog)
        self.btnFindPrev.setObjectName(_fromUtf8("btnFindPrev"))
        self.layoutFind.addWidget(self.btnFindPrev)
        self.chkCaseSensitive = QtGui.QCheckBox(ReportViewDialog)
        self.chkCaseSensitive.setObjectName(_fromUtf8("chkCaseSensitive"))
        self.layoutFind.addWidget(self.chkCaseSensitive)
        self.gridLayout.addLayout(self.layoutFind, 0, 0, 1, 1)
        self.txtReport = CReportBrowser(ReportViewDialog)
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("MS Shell Dlg 2"))
        font.setPointSize(10)
        self.txtReport.setFont(font)
        self.txtReport.setObjectName(_fromUtf8("txtReport"))
        self.gridLayout.addWidget(self.txtReport, 1, 0, 1, 1)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.checkBoxInterval = QtGui.QCheckBox(ReportViewDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.checkBoxInterval.sizePolicy().hasHeightForWidth())
        self.checkBoxInterval.setSizePolicy(sizePolicy)
        self.checkBoxInterval.setObjectName(_fromUtf8("checkBoxInterval"))
        self.horizontalLayout.addWidget(self.checkBoxInterval)
        self.lineEditInterval = QtGui.QLineEdit(ReportViewDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lineEditInterval.sizePolicy().hasHeightForWidth())
        self.lineEditInterval.setSizePolicy(sizePolicy)
        self.lineEditInterval.setObjectName(_fromUtf8("lineEditInterval"))
        self.horizontalLayout.addWidget(self.lineEditInterval)
        self.btnPreview = QtGui.QPushButton(ReportViewDialog)
        self.btnPreview.setObjectName(_fromUtf8("btnPreview"))
        self.horizontalLayout.addWidget(self.btnPreview)
        self.buttonBox = QtGui.QDialogButtonBox(ReportViewDialog)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Close|QtGui.QDialogButtonBox.Retry|QtGui.QDialogButtonBox.Save)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.horizontalLayout.addWidget(self.buttonBox)
        self.gridLayout.addLayout(self.horizontalLayout, 2, 0, 1, 1)

        self.retranslateUi(ReportViewDialog)
        QtCore.QObject.connect(self.checkBoxInterval, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), self.lineEditInterval.setEnabled)
        QtCore.QMetaObject.connectSlotsByName(ReportViewDialog)

    def retranslateUi(self, ReportViewDialog):
        ReportViewDialog.setWindowTitle(_translate("ReportViewDialog", "просмотр отчёта", None))
        self.lblFind.setText(_translate("ReportViewDialog", "Найти совпадение", None))
        self.btnFindNext.setText(_translate("ReportViewDialog", "Следующее", None))
        self.btnFindPrev.setText(_translate("ReportViewDialog", "Предыдущее", None))
        self.chkCaseSensitive.setText(_translate("ReportViewDialog", "Учитывать регистр", None))
        self.checkBoxInterval.setText(_translate("ReportViewDialog", "Добавить отступ сверху (мм)", None))
        self.btnPreview.setText(_translate("ReportViewDialog", "Предпросмотр", None))

from ReportBrowser import CReportBrowser
