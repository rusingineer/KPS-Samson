# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Samson\UP_s11\client_test\RefBooks\PostOnAppointment\PostOnAppointmentEditor.ui'
#
# Created: Mon Apr 08 14:35:29 2024
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

class Ui_PostOnAppointmentEditorDialog(object):
    def setupUi(self, PostOnAppointmentEditorDialog):
        PostOnAppointmentEditorDialog.setObjectName(_fromUtf8("PostOnAppointmentEditorDialog"))
        PostOnAppointmentEditorDialog.resize(306, 121)
        PostOnAppointmentEditorDialog.setSizeGripEnabled(True)
        self.gridLayout = QtGui.QGridLayout(PostOnAppointmentEditorDialog)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.edtCode = QtGui.QLineEdit(PostOnAppointmentEditorDialog)
        self.edtCode.setObjectName(_fromUtf8("edtCode"))
        self.gridLayout.addWidget(self.edtCode, 0, 1, 1, 1)
        self.edtName = QtGui.QLineEdit(PostOnAppointmentEditorDialog)
        self.edtName.setMinimumSize(QtCore.QSize(200, 0))
        self.edtName.setObjectName(_fromUtf8("edtName"))
        self.gridLayout.addWidget(self.edtName, 1, 1, 1, 1)
        self.lblName = QtGui.QLabel(PostOnAppointmentEditorDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblName.sizePolicy().hasHeightForWidth())
        self.lblName.setSizePolicy(sizePolicy)
        self.lblName.setObjectName(_fromUtf8("lblName"))
        self.gridLayout.addWidget(self.lblName, 1, 0, 1, 1)
        self.lblCode = QtGui.QLabel(PostOnAppointmentEditorDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblCode.sizePolicy().hasHeightForWidth())
        self.lblCode.setSizePolicy(sizePolicy)
        self.lblCode.setObjectName(_fromUtf8("lblCode"))
        self.gridLayout.addWidget(self.lblCode, 0, 0, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(PostOnAppointmentEditorDialog)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 2, 0, 1, 2)
        self.lblName.setBuddy(self.edtName)
        self.lblCode.setBuddy(self.edtCode)

        self.retranslateUi(PostOnAppointmentEditorDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), PostOnAppointmentEditorDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), PostOnAppointmentEditorDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(PostOnAppointmentEditorDialog)
        PostOnAppointmentEditorDialog.setTabOrder(self.edtCode, self.edtName)
        PostOnAppointmentEditorDialog.setTabOrder(self.edtName, self.buttonBox)

    def retranslateUi(self, PostOnAppointmentEditorDialog):
        PostOnAppointmentEditorDialog.setWindowTitle(_translate("PostOnAppointmentEditorDialog", "ChangeMe!", None))
        self.lblName.setText(_translate("PostOnAppointmentEditorDialog", "&Наименование", None))
        self.lblCode.setText(_translate("PostOnAppointmentEditorDialog", "&Код", None))

