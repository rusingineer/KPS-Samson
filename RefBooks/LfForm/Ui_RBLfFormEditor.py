# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'RBLfFormEditor.ui'
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

class Ui_RBLfFormEditor(object):
    def setupUi(self, RBLfFormEditor):
        RBLfFormEditor.setObjectName(_fromUtf8("RBLfFormEditor"))
        RBLfFormEditor.resize(534, 142)
        RBLfFormEditor.setSizeGripEnabled(False)
        self.gridlayout = QtGui.QGridLayout(RBLfFormEditor)
        self.gridlayout.setMargin(4)
        self.gridlayout.setSpacing(4)
        self.gridlayout.setObjectName(_fromUtf8("gridlayout"))
        self.lblName = QtGui.QLabel(RBLfFormEditor)
        self.lblName.setObjectName(_fromUtf8("lblName"))
        self.gridlayout.addWidget(self.lblName, 1, 0, 1, 1)
        self.edtName = QtGui.QLineEdit(RBLfFormEditor)
        self.edtName.setObjectName(_fromUtf8("edtName"))
        self.gridlayout.addWidget(self.edtName, 1, 1, 1, 1)
        self.lblCode = QtGui.QLabel(RBLfFormEditor)
        self.lblCode.setObjectName(_fromUtf8("lblCode"))
        self.gridlayout.addWidget(self.lblCode, 0, 0, 1, 1)
        self.edtDosage = QtGui.QLineEdit(RBLfFormEditor)
        self.edtDosage.setObjectName(_fromUtf8("edtDosage"))
        self.gridlayout.addWidget(self.edtDosage, 2, 1, 1, 1)
        self.edtCode = QtGui.QLineEdit(RBLfFormEditor)
        self.edtCode.setObjectName(_fromUtf8("edtCode"))
        self.gridlayout.addWidget(self.edtCode, 0, 1, 1, 1)
        spacerItem = QtGui.QSpacerItem(103, 16, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridlayout.addItem(spacerItem, 4, 0, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(RBLfFormEditor)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridlayout.addWidget(self.buttonBox, 5, 0, 1, 2)
        self.lblDosage = QtGui.QLabel(RBLfFormEditor)
        self.lblDosage.setObjectName(_fromUtf8("lblDosage"))
        self.gridlayout.addWidget(self.lblDosage, 2, 0, 1, 1)
        self.lblIsESKLP = QtGui.QLabel(RBLfFormEditor)
        self.lblIsESKLP.setObjectName(_fromUtf8("lblIsESKLP"))
        self.gridlayout.addWidget(self.lblIsESKLP, 3, 0, 1, 1)
        self.chkIsESKLP = QtGui.QCheckBox(RBLfFormEditor)
        self.chkIsESKLP.setText(_fromUtf8(""))
        self.chkIsESKLP.setObjectName(_fromUtf8("chkIsESKLP"))
        self.gridlayout.addWidget(self.chkIsESKLP, 3, 1, 1, 1)
        self.lblName.setBuddy(self.edtName)
        self.lblCode.setBuddy(self.edtCode)

        self.retranslateUi(RBLfFormEditor)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), RBLfFormEditor.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), RBLfFormEditor.reject)
        QtCore.QMetaObject.connectSlotsByName(RBLfFormEditor)
        RBLfFormEditor.setTabOrder(self.edtCode, self.edtName)
        RBLfFormEditor.setTabOrder(self.edtName, self.edtDosage)
        RBLfFormEditor.setTabOrder(self.edtDosage, self.chkIsESKLP)
        RBLfFormEditor.setTabOrder(self.chkIsESKLP, self.buttonBox)

    def retranslateUi(self, RBLfFormEditor):
        RBLfFormEditor.setWindowTitle(_translate("RBLfFormEditor", "ChangeMe!", None))
        self.lblName.setText(_translate("RBLfFormEditor", "&Наименование", None))
        self.lblCode.setText(_translate("RBLfFormEditor", "&Код", None))
        self.lblDosage.setText(_translate("RBLfFormEditor", "Дозировка", None))
        self.lblIsESKLP.setText(_translate("RBLfFormEditor", "Относится к ЕСКЛП", None))

