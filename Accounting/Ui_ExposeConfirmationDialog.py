# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'E:\projects\Samson\UP_s11\client\Accounting\ExposeConfirmationDialog.ui'
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

class Ui_ExposeConfirmationDialog(object):
    def setupUi(self, ExposeConfirmationDialog):
        ExposeConfirmationDialog.setObjectName(_fromUtf8("ExposeConfirmationDialog"))
        ExposeConfirmationDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        ExposeConfirmationDialog.resize(500, 336)
        ExposeConfirmationDialog.setSizeGripEnabled(True)
        self.gridLayout = QtGui.QGridLayout(ExposeConfirmationDialog)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.chkExposeByChildOrgStruct = QtGui.QCheckBox(ExposeConfirmationDialog)
        self.chkExposeByChildOrgStruct.setObjectName(_fromUtf8("chkExposeByChildOrgStruct"))
        self.gridLayout.addWidget(self.chkExposeByChildOrgStruct, 9, 0, 1, 1)
        self.chkFilterPaymentByOrgStructure = QtGui.QCheckBox(ExposeConfirmationDialog)
        self.chkFilterPaymentByOrgStructure.setObjectName(_fromUtf8("chkFilterPaymentByOrgStructure"))
        self.gridLayout.addWidget(self.chkFilterPaymentByOrgStructure, 2, 0, 1, 2)
        self.chkSeparateReExpose = QtGui.QCheckBox(ExposeConfirmationDialog)
        self.chkSeparateReExpose.setEnabled(False)
        self.chkSeparateReExpose.setChecked(True)
        self.chkSeparateReExpose.setObjectName(_fromUtf8("chkSeparateReExpose"))
        self.gridLayout.addWidget(self.chkSeparateReExpose, 4, 0, 1, 1)
        self.chkReExpose = QtGui.QCheckBox(ExposeConfirmationDialog)
        self.chkReExpose.setObjectName(_fromUtf8("chkReExpose"))
        self.gridLayout.addWidget(self.chkReExpose, 3, 0, 1, 2)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.lblBegDate = QtGui.QLabel(ExposeConfirmationDialog)
        self.lblBegDate.setObjectName(_fromUtf8("lblBegDate"))
        self.horizontalLayout.addWidget(self.lblBegDate)
        self.edtBegDate = CDateEdit(ExposeConfirmationDialog)
        self.edtBegDate.setObjectName(_fromUtf8("edtBegDate"))
        self.horizontalLayout.addWidget(self.edtBegDate)
        self.lblEndDate = QtGui.QLabel(ExposeConfirmationDialog)
        self.lblEndDate.setObjectName(_fromUtf8("lblEndDate"))
        self.horizontalLayout.addWidget(self.lblEndDate)
        self.edtEndDate = CDateEdit(ExposeConfirmationDialog)
        self.edtEndDate.setObjectName(_fromUtf8("edtEndDate"))
        self.horizontalLayout.addWidget(self.edtEndDate)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.gridLayout.addLayout(self.horizontalLayout, 1, 0, 1, 2)
        spacerItem1 = QtGui.QSpacerItem(20, 61, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem1, 10, 1, 1, 1)
        self.chkOnlyResearchOnCOVID = QtGui.QCheckBox(ExposeConfirmationDialog)
        self.chkOnlyResearchOnCOVID.setObjectName(_fromUtf8("chkOnlyResearchOnCOVID"))
        self.gridLayout.addWidget(self.chkOnlyResearchOnCOVID, 7, 0, 1, 2)
        self.buttonBox = QtGui.QDialogButtonBox(ExposeConfirmationDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 11, 0, 1, 1)
        self.chkMesCheck = QtGui.QCheckBox(ExposeConfirmationDialog)
        self.chkMesCheck.setObjectName(_fromUtf8("chkMesCheck"))
        self.gridLayout.addWidget(self.chkMesCheck, 5, 0, 1, 1)
        self.chkOnlyDispCOVID = QtGui.QCheckBox(ExposeConfirmationDialog)
        self.chkOnlyDispCOVID.setObjectName(_fromUtf8("chkOnlyDispCOVID"))
        self.gridLayout.addWidget(self.chkOnlyDispCOVID, 6, 0, 1, 2)
        self.scrollArea = QtGui.QScrollArea(ExposeConfirmationDialog)
        self.scrollArea.setLineWidth(0)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName(_fromUtf8("scrollArea"))
        self.scrollAreaWidgetContents = QtGui.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 480, 69))
        self.scrollAreaWidgetContents.setObjectName(_fromUtf8("scrollAreaWidgetContents"))
        self.verticalLayout = QtGui.QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.lblMessage = QtGui.QLabel(self.scrollAreaWidgetContents)
        self.lblMessage.setAlignment(QtCore.Qt.AlignCenter)
        self.lblMessage.setTextInteractionFlags(QtCore.Qt.TextBrowserInteraction)
        self.lblMessage.setObjectName(_fromUtf8("lblMessage"))
        self.verticalLayout.addWidget(self.lblMessage)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.gridLayout.addWidget(self.scrollArea, 0, 0, 1, 2)
        self.chkOnlyTFOMS = QtGui.QCheckBox(ExposeConfirmationDialog)
        self.chkOnlyTFOMS.setObjectName(_fromUtf8("chkOnlyTFOMS"))
        self.gridLayout.addWidget(self.chkOnlyTFOMS, 8, 0, 1, 1)

        self.retranslateUi(ExposeConfirmationDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), ExposeConfirmationDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), ExposeConfirmationDialog.reject)
        QtCore.QObject.connect(self.chkReExpose, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), self.chkSeparateReExpose.setEnabled)
        QtCore.QMetaObject.connectSlotsByName(ExposeConfirmationDialog)
        ExposeConfirmationDialog.setTabOrder(self.chkFilterPaymentByOrgStructure, self.chkReExpose)
        ExposeConfirmationDialog.setTabOrder(self.chkReExpose, self.chkSeparateReExpose)
        ExposeConfirmationDialog.setTabOrder(self.chkSeparateReExpose, self.chkMesCheck)
        ExposeConfirmationDialog.setTabOrder(self.chkMesCheck, self.buttonBox)

    def retranslateUi(self, ExposeConfirmationDialog):
        ExposeConfirmationDialog.setWindowTitle(_translate("ExposeConfirmationDialog", "Внимание!", None))
        self.chkExposeByChildOrgStruct.setText(_translate("ExposeConfirmationDialog", "При выставлении счетов разбивать по подразделениям", None))
        self.chkFilterPaymentByOrgStructure.setText(_translate("ExposeConfirmationDialog", "При выставлении счетов учитывать текущее подразделение", None))
        self.chkSeparateReExpose.setText(_translate("ExposeConfirmationDialog", "Перевыставлять в отдельный счет", None))
        self.chkReExpose.setText(_translate("ExposeConfirmationDialog", "Выполнять перевыставление по имеющимся отказам", None))
        self.lblBegDate.setText(_translate("ExposeConfirmationDialog", "За период с", None))
        self.lblEndDate.setText(_translate("ExposeConfirmationDialog", "по", None))
        self.chkOnlyResearchOnCOVID.setText(_translate("ExposeConfirmationDialog", "Выставлять только исследования на covid", None))
        self.chkMesCheck.setText(_translate("ExposeConfirmationDialog", "Проверять на соответствие МЭС", None))
        self.chkOnlyDispCOVID.setText(_translate("ExposeConfirmationDialog", "Выставлять только углубленную диспансеризацию", None))
        self.lblMessage.setText(_translate("ExposeConfirmationDialog", "message", None))
        self.chkOnlyTFOMS.setText(_translate("ExposeConfirmationDialog", "Выставлять только инокраевые счета", None))

from library.DateEdit import CDateEdit
