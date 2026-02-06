# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\projects\Samson\UP_s11\client\Users\InformerFilter.ui'
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

class Ui_InformerFilterDialog(object):
    def setupUi(self, InformerFilterDialog):
        InformerFilterDialog.setObjectName(_fromUtf8("InformerFilterDialog"))
        InformerFilterDialog.resize(316, 173)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(InformerFilterDialog.sizePolicy().hasHeightForWidth())
        InformerFilterDialog.setSizePolicy(sizePolicy)
        InformerFilterDialog.setMaximumSize(QtCore.QSize(316, 173))
        self.gridLayout = QtGui.QGridLayout(InformerFilterDialog)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        spacerItem = QtGui.QSpacerItem(20, 0, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, 6, 1, 1, 1)
        self.cmbAuthor = CPersonComboBox(InformerFilterDialog)
        self.cmbAuthor.setEnabled(False)
        self.cmbAuthor.setObjectName(_fromUtf8("cmbAuthor"))
        self.gridLayout.addWidget(self.cmbAuthor, 1, 1, 1, 2)
        self.buttonBox = QtGui.QDialogButtonBox(InformerFilterDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 7, 0, 1, 3)
        self.chkDate = QtGui.QCheckBox(InformerFilterDialog)
        self.chkDate.setObjectName(_fromUtf8("chkDate"))
        self.gridLayout.addWidget(self.chkDate, 3, 0, 1, 1)
        self.edtBegDate = CDateEdit(InformerFilterDialog)
        self.edtBegDate.setEnabled(False)
        self.edtBegDate.setCalendarPopup(True)
        self.edtBegDate.setObjectName(_fromUtf8("edtBegDate"))
        self.gridLayout.addWidget(self.edtBegDate, 3, 1, 1, 1)
        self.chkAuthor = QtGui.QCheckBox(InformerFilterDialog)
        self.chkAuthor.setObjectName(_fromUtf8("chkAuthor"))
        self.gridLayout.addWidget(self.chkAuthor, 1, 0, 1, 1)
        self.edtEndDate = CDateEdit(InformerFilterDialog)
        self.edtEndDate.setEnabled(False)
        self.edtEndDate.setCalendarPopup(True)
        self.edtEndDate.setObjectName(_fromUtf8("edtEndDate"))
        self.gridLayout.addWidget(self.edtEndDate, 3, 2, 1, 1)
        self.cmbRevisionInfo = QtGui.QComboBox(InformerFilterDialog)
        self.cmbRevisionInfo.setEnabled(False)
        self.cmbRevisionInfo.setObjectName(_fromUtf8("cmbRevisionInfo"))
        self.cmbRevisionInfo.addItem(_fromUtf8(""))
        self.cmbRevisionInfo.addItem(_fromUtf8(""))
        self.gridLayout.addWidget(self.cmbRevisionInfo, 4, 2, 1, 1)
        self.chkRevisionInfo = QtGui.QCheckBox(InformerFilterDialog)
        self.chkRevisionInfo.setObjectName(_fromUtf8("chkRevisionInfo"))
        self.gridLayout.addWidget(self.chkRevisionInfo, 4, 0, 1, 2)
        self.edtSubject = QtGui.QLineEdit(InformerFilterDialog)
        self.edtSubject.setEnabled(False)
        self.edtSubject.setObjectName(_fromUtf8("edtSubject"))
        self.gridLayout.addWidget(self.edtSubject, 2, 1, 1, 2)
        self.chkSubject = QtGui.QCheckBox(InformerFilterDialog)
        self.chkSubject.setObjectName(_fromUtf8("chkSubject"))
        self.gridLayout.addWidget(self.chkSubject, 2, 0, 1, 1)
        self.chkConstant = QtGui.QCheckBox(InformerFilterDialog)
        self.chkConstant.setObjectName(_fromUtf8("chkConstant"))
        self.gridLayout.addWidget(self.chkConstant, 5, 0, 1, 2)
        self.cmbConstant = QtGui.QComboBox(InformerFilterDialog)
        self.cmbConstant.setEnabled(False)
        self.cmbConstant.setObjectName(_fromUtf8("cmbConstant"))
        self.cmbConstant.addItem(_fromUtf8(""))
        self.cmbConstant.addItem(_fromUtf8(""))
        self.gridLayout.addWidget(self.cmbConstant, 5, 2, 1, 1)

        self.retranslateUi(InformerFilterDialog)
        self.cmbConstant.setCurrentIndex(0)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), InformerFilterDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), InformerFilterDialog.reject)
        QtCore.QObject.connect(self.chkDate, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), self.edtBegDate.setEnabled)
        QtCore.QObject.connect(self.chkDate, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), self.edtEndDate.setEnabled)
        QtCore.QObject.connect(self.chkAuthor, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), self.cmbAuthor.setEnabled)
        QtCore.QObject.connect(self.chkRevisionInfo, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), self.cmbRevisionInfo.setEnabled)
        QtCore.QObject.connect(self.chkSubject, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), self.edtSubject.setEnabled)
        QtCore.QObject.connect(self.chkConstant, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), self.cmbConstant.setEnabled)
        QtCore.QMetaObject.connectSlotsByName(InformerFilterDialog)
        InformerFilterDialog.setTabOrder(self.chkAuthor, self.cmbAuthor)
        InformerFilterDialog.setTabOrder(self.cmbAuthor, self.chkSubject)
        InformerFilterDialog.setTabOrder(self.chkSubject, self.edtSubject)
        InformerFilterDialog.setTabOrder(self.edtSubject, self.chkDate)
        InformerFilterDialog.setTabOrder(self.chkDate, self.edtBegDate)
        InformerFilterDialog.setTabOrder(self.edtBegDate, self.edtEndDate)
        InformerFilterDialog.setTabOrder(self.edtEndDate, self.chkRevisionInfo)
        InformerFilterDialog.setTabOrder(self.chkRevisionInfo, self.cmbRevisionInfo)
        InformerFilterDialog.setTabOrder(self.cmbRevisionInfo, self.buttonBox)

    def retranslateUi(self, InformerFilterDialog):
        InformerFilterDialog.setWindowTitle(_translate("InformerFilterDialog", "Фильтр сообщений информатора", None))
        self.chkDate.setText(_translate("InformerFilterDialog", "Дата", None))
        self.chkAuthor.setText(_translate("InformerFilterDialog", "Автор", None))
        self.cmbRevisionInfo.setItemText(0, _translate("InformerFilterDialog", "Ревизии", None))
        self.cmbRevisionInfo.setItemText(1, _translate("InformerFilterDialog", "Прочие", None))
        self.chkRevisionInfo.setText(_translate("InformerFilterDialog", "Тип сообщений", None))
        self.chkSubject.setText(_translate("InformerFilterDialog", "Тема", None))
        self.chkConstant.setText(_translate("InformerFilterDialog", "Является постоянным", None))
        self.cmbConstant.setItemText(0, _translate("InformerFilterDialog", "Да", None))
        self.cmbConstant.setItemText(1, _translate("InformerFilterDialog", "Нет", None))

from Orgs.PersonComboBox import CPersonComboBox
from library.DateEdit import CDateEdit
