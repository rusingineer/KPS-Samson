# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\projects\Samson\UP_s11\client\Users\InformerEditor.ui'
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

class Ui_InformerMessageEditorDialog(object):
    def setupUi(self, InformerMessageEditorDialog):
        InformerMessageEditorDialog.setObjectName(_fromUtf8("InformerMessageEditorDialog"))
        InformerMessageEditorDialog.resize(514, 356)
        InformerMessageEditorDialog.setSizeGripEnabled(False)
        self.gridLayout = QtGui.QGridLayout(InformerMessageEditorDialog)
        self.gridLayout.setMargin(4)
        self.gridLayout.setSpacing(4)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.edtSubject = QtGui.QLineEdit(InformerMessageEditorDialog)
        self.edtSubject.setObjectName(_fromUtf8("edtSubject"))
        self.gridLayout.addWidget(self.edtSubject, 0, 1, 1, 1)
        self.lblText = QtGui.QLabel(InformerMessageEditorDialog)
        self.lblText.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.lblText.setObjectName(_fromUtf8("lblText"))
        self.gridLayout.addWidget(self.lblText, 1, 0, 1, 1)
        self.lblSubject = QtGui.QLabel(InformerMessageEditorDialog)
        self.lblSubject.setObjectName(_fromUtf8("lblSubject"))
        self.gridLayout.addWidget(self.lblSubject, 0, 0, 1, 1)
        self.edtText = QtGui.QTextEdit(InformerMessageEditorDialog)
        self.edtText.setObjectName(_fromUtf8("edtText"))
        self.gridLayout.addWidget(self.edtText, 1, 1, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(InformerMessageEditorDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 3, 0, 1, 2)
        self.chkIsConstant = QtGui.QCheckBox(InformerMessageEditorDialog)
        self.chkIsConstant.setObjectName(_fromUtf8("chkIsConstant"))
        self.gridLayout.addWidget(self.chkIsConstant, 2, 0, 1, 2)
        self.lblText.setBuddy(self.edtText)
        self.lblSubject.setBuddy(self.edtSubject)

        self.retranslateUi(InformerMessageEditorDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), InformerMessageEditorDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), InformerMessageEditorDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(InformerMessageEditorDialog)
        InformerMessageEditorDialog.setTabOrder(self.edtSubject, self.edtText)
        InformerMessageEditorDialog.setTabOrder(self.edtText, self.buttonBox)

    def retranslateUi(self, InformerMessageEditorDialog):
        InformerMessageEditorDialog.setWindowTitle(_translate("InformerMessageEditorDialog", "ChangeMe!", None))
        self.lblText.setText(_translate("InformerMessageEditorDialog", "&Сообщение", None))
        self.lblSubject.setText(_translate("InformerMessageEditorDialog", "&Тема", None))
        self.chkIsConstant.setText(_translate("InformerMessageEditorDialog", "Является постоянным", None))

