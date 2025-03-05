# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/aeiklorvy/samson/Events/NomenclatureExpense/UpdateDoseNomenclatureExpenseEditor.ui'
#
# Created by: PyQt4 UI code generator 4.12.1
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

class Ui_UpdateDoseNomenclatureExpenseEditor(object):
    def setupUi(self, UpdateDoseNomenclatureExpenseEditor):
        UpdateDoseNomenclatureExpenseEditor.setObjectName(_fromUtf8("UpdateDoseNomenclatureExpenseEditor"))
        UpdateDoseNomenclatureExpenseEditor.resize(201, 130)
        self.gridLayout = QtGui.QGridLayout(UpdateDoseNomenclatureExpenseEditor)
        self.gridLayout.setMargin(4)
        self.gridLayout.setSpacing(4)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.chkIncrease = QtGui.QRadioButton(UpdateDoseNomenclatureExpenseEditor)
        self.chkIncrease.setObjectName(_fromUtf8("chkIncrease"))
        self.gridLayout.addWidget(self.chkIncrease, 0, 1, 1, 2)
        self.buttonBox = QtGui.QDialogButtonBox(UpdateDoseNomenclatureExpenseEditor)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 3, 0, 1, 3)
        self.edtProcent = CSpinBox(UpdateDoseNomenclatureExpenseEditor)
        self.edtProcent.setMinimum(1)
        self.edtProcent.setMaximum(100)
        self.edtProcent.setObjectName(_fromUtf8("edtProcent"))
        self.gridLayout.addWidget(self.edtProcent, 1, 1, 1, 1)
        self.chkReduce = QtGui.QRadioButton(UpdateDoseNomenclatureExpenseEditor)
        self.chkReduce.setObjectName(_fromUtf8("chkReduce"))
        self.gridLayout.addWidget(self.chkReduce, 0, 0, 1, 1)
        self.lblProcent = QtGui.QLabel(UpdateDoseNomenclatureExpenseEditor)
        self.lblProcent.setObjectName(_fromUtf8("lblProcent"))
        self.gridLayout.addWidget(self.lblProcent, 1, 0, 1, 1)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 1, 2, 1, 1)
        spacerItem1 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem1, 2, 0, 1, 1)

        self.retranslateUi(UpdateDoseNomenclatureExpenseEditor)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), UpdateDoseNomenclatureExpenseEditor.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), UpdateDoseNomenclatureExpenseEditor.reject)
        QtCore.QMetaObject.connectSlotsByName(UpdateDoseNomenclatureExpenseEditor)

    def retranslateUi(self, UpdateDoseNomenclatureExpenseEditor):
        UpdateDoseNomenclatureExpenseEditor.setWindowTitle(_translate("UpdateDoseNomenclatureExpenseEditor", "Изменить дозу", None))
        self.chkIncrease.setText(_translate("UpdateDoseNomenclatureExpenseEditor", "Увеличить", None))
        self.chkReduce.setText(_translate("UpdateDoseNomenclatureExpenseEditor", "Уменьшить", None))
        self.lblProcent.setText(_translate("UpdateDoseNomenclatureExpenseEditor", "Процент", None))

from library.SpinBox import CSpinBox

if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    UpdateDoseNomenclatureExpenseEditor = QtGui.QDialog()
    ui = Ui_UpdateDoseNomenclatureExpenseEditor()
    ui.setupUi(UpdateDoseNomenclatureExpenseEditor)
    UpdateDoseNomenclatureExpenseEditor.show()
    sys.exit(app.exec_())

