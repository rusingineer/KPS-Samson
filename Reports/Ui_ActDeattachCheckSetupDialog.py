# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './ActDeattachCheckSetupDialog.ui'
#
# Created: Thu Oct 02 09:59:20 2025
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

class Ui_ActDeattachCheckSetupDialog(object):
    def setupUi(self, ActDeattachCheckSetupDialog):
        ActDeattachCheckSetupDialog.setObjectName(_fromUtf8("ActDeattachCheckSetupDialog"))
        ActDeattachCheckSetupDialog.resize(435, 222)
        self.gridLayout = QtGui.QGridLayout(ActDeattachCheckSetupDialog)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.buttonBox = QtGui.QDialogButtonBox(ActDeattachCheckSetupDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 6, 0, 2, 3)
        self.lblEndDate = QtGui.QLabel(ActDeattachCheckSetupDialog)
        self.lblEndDate.setObjectName(_fromUtf8("lblEndDate"))
        self.gridLayout.addWidget(self.lblEndDate, 2, 0, 1, 1)
        spacerItem = QtGui.QSpacerItem(190, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 0, 2, 1, 1)
        spacerItem1 = QtGui.QSpacerItem(190, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem1, 2, 2, 1, 1)
        self.edtEndDate = CDateEdit(ActDeattachCheckSetupDialog)
        self.edtEndDate.setMinimumSize(QtCore.QSize(95, 0))
        self.edtEndDate.setCalendarPopup(True)
        self.edtEndDate.setObjectName(_fromUtf8("edtEndDate"))
        self.gridLayout.addWidget(self.edtEndDate, 2, 1, 1, 1)
        self.edtBegDate = CDateEdit(ActDeattachCheckSetupDialog)
        self.edtBegDate.setMinimumSize(QtCore.QSize(95, 0))
        self.edtBegDate.setCalendarPopup(True)
        self.edtBegDate.setObjectName(_fromUtf8("edtBegDate"))
        self.gridLayout.addWidget(self.edtBegDate, 0, 1, 1, 1)
        spacerItem2 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem2, 5, 0, 1, 1)
        self.lblBegDate = QtGui.QLabel(ActDeattachCheckSetupDialog)
        self.lblBegDate.setObjectName(_fromUtf8("lblBegDate"))
        self.gridLayout.addWidget(self.lblBegDate, 0, 0, 1, 1)
        self.groupBox = QtGui.QGroupBox(ActDeattachCheckSetupDialog)
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.verticalLayout = QtGui.QVBoxLayout(self.groupBox)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.rbActType1 = QtGui.QRadioButton(self.groupBox)
        self.rbActType1.setChecked(True)
        self.rbActType1.setObjectName(_fromUtf8("rbActType1"))
        self.verticalLayout.addWidget(self.rbActType1)
        self.rbActType2 = QtGui.QRadioButton(self.groupBox)
        self.rbActType2.setObjectName(_fromUtf8("rbActType2"))
        self.verticalLayout.addWidget(self.rbActType2)
        self.gridLayout.addWidget(self.groupBox, 4, 0, 1, 3)
        self.lblOrgStructure = QtGui.QLabel(ActDeattachCheckSetupDialog)
        self.lblOrgStructure.setObjectName(_fromUtf8("lblOrgStructure"))
        self.gridLayout.addWidget(self.lblOrgStructure, 3, 0, 1, 1)
        self.cmbOrgStructure = CAreaComboBox(ActDeattachCheckSetupDialog)
        self.cmbOrgStructure.setObjectName(_fromUtf8("cmbOrgStructure"))
        self.gridLayout.addWidget(self.cmbOrgStructure, 3, 1, 1, 2)
        self.lblEndDate.setBuddy(self.edtEndDate)
        self.lblBegDate.setBuddy(self.edtBegDate)

        self.retranslateUi(ActDeattachCheckSetupDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), ActDeattachCheckSetupDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), ActDeattachCheckSetupDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(ActDeattachCheckSetupDialog)

    def retranslateUi(self, ActDeattachCheckSetupDialog):
        ActDeattachCheckSetupDialog.setWindowTitle(_translate("ActDeattachCheckSetupDialog", "параметры отчета", None))
        self.lblEndDate.setText(_translate("ActDeattachCheckSetupDialog", "Дата &окончания периода", None))
        self.lblBegDate.setText(_translate("ActDeattachCheckSetupDialog", "Дата &начала периода", None))
        self.groupBox.setTitle(_translate("ActDeattachCheckSetupDialog", "Формировать отчет по", None))
        self.rbActType1.setText(_translate("ActDeattachCheckSetupDialog", "По отправленным уведомлениям", None))
        self.rbActType2.setText(_translate("ActDeattachCheckSetupDialog", "По полученным уведомлениям", None))
        self.lblOrgStructure.setText(_translate("ActDeattachCheckSetupDialog", "Участок", None))

from library.DateEdit import CDateEdit
from Orgs.OrgStructComboBoxes import CAreaComboBox

if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    ActDeattachCheckSetupDialog = QtGui.QDialog()
    ui = Ui_ActDeattachCheckSetupDialog()
    ui.setupUi(ActDeattachCheckSetupDialog)
    ActDeattachCheckSetupDialog.show()
    sys.exit(app.exec_())

