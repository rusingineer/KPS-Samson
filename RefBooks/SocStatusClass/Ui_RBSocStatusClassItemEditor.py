# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\samson\RefBooks\SocStatusClass\RBSocStatusClassItemEditor.ui'
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

class Ui_SocStatusClassItemEditorDialog(object):
    def setupUi(self, SocStatusClassItemEditorDialog):
        SocStatusClassItemEditorDialog.setObjectName(_fromUtf8("SocStatusClassItemEditorDialog"))
        SocStatusClassItemEditorDialog.resize(400, 302)
        SocStatusClassItemEditorDialog.setSizeGripEnabled(True)
        self.gridlayout = QtGui.QGridLayout(SocStatusClassItemEditorDialog)
        self.gridlayout.setMargin(4)
        self.gridlayout.setSpacing(4)
        self.gridlayout.setObjectName(_fromUtf8("gridlayout"))
        self.lblName = QtGui.QLabel(SocStatusClassItemEditorDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblName.sizePolicy().hasHeightForWidth())
        self.lblName.setSizePolicy(sizePolicy)
        self.lblName.setObjectName(_fromUtf8("lblName"))
        self.gridlayout.addWidget(self.lblName, 1, 0, 1, 1)
        self.edtCode = QtGui.QLineEdit(SocStatusClassItemEditorDialog)
        self.edtCode.setObjectName(_fromUtf8("edtCode"))
        self.gridlayout.addWidget(self.edtCode, 0, 1, 1, 1)
        self.tblTypes = CInDocTableView(SocStatusClassItemEditorDialog)
        self.tblTypes.setObjectName(_fromUtf8("tblTypes"))
        self.gridlayout.addWidget(self.tblTypes, 3, 1, 2, 1)
        self.lblTypes = QtGui.QLabel(SocStatusClassItemEditorDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblTypes.sizePolicy().hasHeightForWidth())
        self.lblTypes.setSizePolicy(sizePolicy)
        self.lblTypes.setObjectName(_fromUtf8("lblTypes"))
        self.gridlayout.addWidget(self.lblTypes, 3, 0, 1, 1)
        self.edtName = QtGui.QLineEdit(SocStatusClassItemEditorDialog)
        self.edtName.setMinimumSize(QtCore.QSize(200, 0))
        self.edtName.setObjectName(_fromUtf8("edtName"))
        self.gridlayout.addWidget(self.edtName, 1, 1, 1, 1)
        self.lblCode = QtGui.QLabel(SocStatusClassItemEditorDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblCode.sizePolicy().hasHeightForWidth())
        self.lblCode.setSizePolicy(sizePolicy)
        self.lblCode.setObjectName(_fromUtf8("lblCode"))
        self.gridlayout.addWidget(self.lblCode, 0, 0, 1, 1)
        spacerItem = QtGui.QSpacerItem(73, 171, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridlayout.addItem(spacerItem, 4, 0, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(SocStatusClassItemEditorDialog)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridlayout.addWidget(self.buttonBox, 5, 0, 1, 2)
        self.chkIsHolded = QtGui.QCheckBox(SocStatusClassItemEditorDialog)
        self.chkIsHolded.setText(_fromUtf8(""))
        self.chkIsHolded.setObjectName(_fromUtf8("chkIsHolded"))
        self.gridlayout.addWidget(self.chkIsHolded, 2, 1, 1, 1)
        self.lblIsHolded = QtGui.QLabel(SocStatusClassItemEditorDialog)
        self.lblIsHolded.setObjectName(_fromUtf8("lblIsHolded"))
        self.gridlayout.addWidget(self.lblIsHolded, 2, 0, 1, 1)
        self.lblName.setBuddy(self.edtName)
        self.lblTypes.setBuddy(self.tblTypes)
        self.lblCode.setBuddy(self.edtCode)
        self.lblIsHolded.setBuddy(self.chkIsHolded)

        self.retranslateUi(SocStatusClassItemEditorDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), SocStatusClassItemEditorDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), SocStatusClassItemEditorDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(SocStatusClassItemEditorDialog)
        SocStatusClassItemEditorDialog.setTabOrder(self.edtCode, self.edtName)
        SocStatusClassItemEditorDialog.setTabOrder(self.edtName, self.chkIsHolded)
        SocStatusClassItemEditorDialog.setTabOrder(self.chkIsHolded, self.tblTypes)
        SocStatusClassItemEditorDialog.setTabOrder(self.tblTypes, self.buttonBox)

    def retranslateUi(self, SocStatusClassItemEditorDialog):
        SocStatusClassItemEditorDialog.setWindowTitle(_translate("SocStatusClassItemEditorDialog", "ChangeMe!", None))
        self.lblName.setText(_translate("SocStatusClassItemEditorDialog", "На&именование", None))
        self.lblTypes.setText(_translate("SocStatusClassItemEditorDialog", "Льготы", None))
        self.lblCode.setText(_translate("SocStatusClassItemEditorDialog", "&Код", None))
        self.lblIsHolded.setText(_translate("SocStatusClassItemEditorDialog", "Закрепить соц.статус", None))

from library.InDocTable import CInDocTableView
