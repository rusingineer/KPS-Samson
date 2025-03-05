# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Rabota\s11\RefBooks\StockMotionNumber\RBStockMotionNumberEditor.ui'
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

class Ui_StockMotionNumberEditorDialog(object):
    def setupUi(self, StockMotionNumberEditorDialog):
        StockMotionNumberEditorDialog.setObjectName(_fromUtf8("StockMotionNumberEditorDialog"))
        StockMotionNumberEditorDialog.resize(333, 170)
        StockMotionNumberEditorDialog.setSizeGripEnabled(True)
        self.gridLayout = QtGui.QGridLayout(StockMotionNumberEditorDialog)
        self.gridLayout.setMargin(4)
        self.gridLayout.setSpacing(4)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.lblStockMotionType = QtGui.QLabel(StockMotionNumberEditorDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblStockMotionType.sizePolicy().hasHeightForWidth())
        self.lblStockMotionType.setSizePolicy(sizePolicy)
        self.lblStockMotionType.setObjectName(_fromUtf8("lblStockMotionType"))
        self.gridLayout.addWidget(self.lblStockMotionType, 2, 0, 1, 1)
        spacerItem = QtGui.QSpacerItem(103, 16, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, 5, 0, 1, 1)
        self.edtName = QtGui.QLineEdit(StockMotionNumberEditorDialog)
        self.edtName.setObjectName(_fromUtf8("edtName"))
        self.gridLayout.addWidget(self.edtName, 1, 1, 1, 1)
        self.lblCounter = QtGui.QLabel(StockMotionNumberEditorDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblCounter.sizePolicy().hasHeightForWidth())
        self.lblCounter.setSizePolicy(sizePolicy)
        self.lblCounter.setObjectName(_fromUtf8("lblCounter"))
        self.gridLayout.addWidget(self.lblCounter, 4, 0, 1, 1)
        self.lblStockMotionType_2 = QtGui.QLabel(StockMotionNumberEditorDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblStockMotionType_2.sizePolicy().hasHeightForWidth())
        self.lblStockMotionType_2.setSizePolicy(sizePolicy)
        self.lblStockMotionType_2.setObjectName(_fromUtf8("lblStockMotionType_2"))
        self.gridLayout.addWidget(self.lblStockMotionType_2, 1, 0, 1, 1)
        self.edtCode = QtGui.QLineEdit(StockMotionNumberEditorDialog)
        self.edtCode.setObjectName(_fromUtf8("edtCode"))
        self.gridLayout.addWidget(self.edtCode, 0, 1, 1, 1)
        self.cmbStockMotionType = QtGui.QComboBox(StockMotionNumberEditorDialog)
        self.cmbStockMotionType.setObjectName(_fromUtf8("cmbStockMotionType"))
        self.cmbStockMotionType.addItem(_fromUtf8(""))
        self.cmbStockMotionType.addItem(_fromUtf8(""))
        self.cmbStockMotionType.addItem(_fromUtf8(""))
        self.cmbStockMotionType.addItem(_fromUtf8(""))
        self.cmbStockMotionType.addItem(_fromUtf8(""))
        self.cmbStockMotionType.addItem(_fromUtf8(""))
        self.cmbStockMotionType.addItem(_fromUtf8(""))
        self.cmbStockMotionType.addItem(_fromUtf8(""))
        self.cmbStockMotionType.addItem(_fromUtf8(""))
        self.cmbStockMotionType.addItem(_fromUtf8(""))
        self.cmbStockMotionType.addItem(_fromUtf8(""))
        self.cmbStockMotionType.addItem(_fromUtf8(""))
        self.gridLayout.addWidget(self.cmbStockMotionType, 2, 1, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(StockMotionNumberEditorDialog)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 6, 0, 1, 2)
        self.cmbCounter = CRBComboBox(StockMotionNumberEditorDialog)
        self.cmbCounter.setObjectName(_fromUtf8("cmbCounter"))
        self.gridLayout.addWidget(self.cmbCounter, 4, 1, 1, 1)
        self.lblStockMotionType_3 = QtGui.QLabel(StockMotionNumberEditorDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblStockMotionType_3.sizePolicy().hasHeightForWidth())
        self.lblStockMotionType_3.setSizePolicy(sizePolicy)
        self.lblStockMotionType_3.setObjectName(_fromUtf8("lblStockMotionType_3"))
        self.gridLayout.addWidget(self.lblStockMotionType_3, 0, 0, 1, 1)
        self.lblOrgStructure = QtGui.QLabel(StockMotionNumberEditorDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblOrgStructure.sizePolicy().hasHeightForWidth())
        self.lblOrgStructure.setSizePolicy(sizePolicy)
        self.lblOrgStructure.setObjectName(_fromUtf8("lblOrgStructure"))
        self.gridLayout.addWidget(self.lblOrgStructure, 3, 0, 1, 1)
        self.cmbOrgStructure = COrgStructureComboBox(StockMotionNumberEditorDialog)
        self.cmbOrgStructure.setObjectName(_fromUtf8("cmbOrgStructure"))
        self.gridLayout.addWidget(self.cmbOrgStructure, 3, 1, 1, 1)

        self.retranslateUi(StockMotionNumberEditorDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), StockMotionNumberEditorDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), StockMotionNumberEditorDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(StockMotionNumberEditorDialog)

    def retranslateUi(self, StockMotionNumberEditorDialog):
        StockMotionNumberEditorDialog.setWindowTitle(_translate("StockMotionNumberEditorDialog", "ChangeMe!", None))
        self.lblStockMotionType.setText(_translate("StockMotionNumberEditorDialog", "Тип накладной", None))
        self.lblCounter.setText(_translate("StockMotionNumberEditorDialog", "Счетчик", None))
        self.lblStockMotionType_2.setText(_translate("StockMotionNumberEditorDialog", "Наименование", None))
        self.cmbStockMotionType.setItemText(0, _translate("StockMotionNumberEditorDialog", "Внутренняя накладная", None))
        self.cmbStockMotionType.setItemText(1, _translate("StockMotionNumberEditorDialog", "Инвентаризация", None))
        self.cmbStockMotionType.setItemText(2, _translate("StockMotionNumberEditorDialog", "Финансовая переброска", None))
        self.cmbStockMotionType.setItemText(3, _translate("StockMotionNumberEditorDialog", "Производство", None))
        self.cmbStockMotionType.setItemText(4, _translate("StockMotionNumberEditorDialog", "Списание на пациента", None))
        self.cmbStockMotionType.setItemText(5, _translate("StockMotionNumberEditorDialog", "Возврат от пациента", None))
        self.cmbStockMotionType.setItemText(6, _translate("StockMotionNumberEditorDialog", "Резервирование на пациента", None))
        self.cmbStockMotionType.setItemText(7, _translate("StockMotionNumberEditorDialog", "Утилизация", None))
        self.cmbStockMotionType.setItemText(8, _translate("StockMotionNumberEditorDialog", "Внутреннее потребление", None))
        self.cmbStockMotionType.setItemText(9, _translate("StockMotionNumberEditorDialog", "Требование", None))
        self.cmbStockMotionType.setItemText(10, _translate("StockMotionNumberEditorDialog", "Накладная от поставщика", None))
        self.cmbStockMotionType.setItemText(11, _translate("StockMotionNumberEditorDialog", "Списание остаточных количеств", None))
        self.lblStockMotionType_3.setText(_translate("StockMotionNumberEditorDialog", "Код", None))
        self.lblOrgStructure.setText(_translate("StockMotionNumberEditorDialog", "Подразделение", None))

from Orgs.OrgStructComboBoxes import COrgStructureComboBox
from library.crbcombobox import CRBComboBox

if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    StockMotionNumberEditorDialog = QtGui.QDialog()
    ui = Ui_StockMotionNumberEditorDialog()
    ui.setupUi(StockMotionNumberEditorDialog)
    StockMotionNumberEditorDialog.show()
    sys.exit(app.exec_())

