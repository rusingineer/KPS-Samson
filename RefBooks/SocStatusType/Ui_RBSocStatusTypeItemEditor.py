# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './RBSocStatusTypeItemEditor.ui'
#
# Created: Thu Mar 06 09:18:20 2025
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

class Ui_SocStatusTypeItemEditorDialog(object):
    def setupUi(self, SocStatusTypeItemEditorDialog):
        SocStatusTypeItemEditorDialog.setObjectName(_fromUtf8("SocStatusTypeItemEditorDialog"))
        SocStatusTypeItemEditorDialog.resize(484, 334)
        SocStatusTypeItemEditorDialog.setSizeGripEnabled(True)
        self.gridLayout_2 = QtGui.QGridLayout(SocStatusTypeItemEditorDialog)
        self.gridLayout_2.setSpacing(4)
        self.gridLayout_2.setMargin(4)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.tabWidget = QtGui.QTabWidget(SocStatusTypeItemEditorDialog)
        self.tabWidget.setObjectName(_fromUtf8("tabWidget"))
        self.tabMain = QtGui.QWidget()
        self.tabMain.setObjectName(_fromUtf8("tabMain"))
        self.gridLayout = QtGui.QGridLayout(self.tabMain)
        self.gridLayout.setSpacing(4)
        self.gridLayout.setMargin(4)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.edtRegionalCode = QtGui.QLineEdit(self.tabMain)
        self.edtRegionalCode.setEnabled(True)
        self.edtRegionalCode.setObjectName(_fromUtf8("edtRegionalCode"))
        self.gridLayout.addWidget(self.edtRegionalCode, 3, 1, 1, 1)
        self.lblShortName = QtGui.QLabel(self.tabMain)
        self.lblShortName.setObjectName(_fromUtf8("lblShortName"))
        self.gridLayout.addWidget(self.lblShortName, 2, 0, 1, 1)
        self.lblRegionalCode = QtGui.QLabel(self.tabMain)
        self.lblRegionalCode.setEnabled(True)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblRegionalCode.sizePolicy().hasHeightForWidth())
        self.lblRegionalCode.setSizePolicy(sizePolicy)
        self.lblRegionalCode.setObjectName(_fromUtf8("lblRegionalCode"))
        self.gridLayout.addWidget(self.lblRegionalCode, 3, 0, 1, 1)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 3, 2, 1, 1)
        spacerItem1 = QtGui.QSpacerItem(20, 120, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem1, 5, 0, 1, 1)
        self.edtShortName = QtGui.QLineEdit(self.tabMain)
        self.edtShortName.setObjectName(_fromUtf8("edtShortName"))
        self.gridLayout.addWidget(self.edtShortName, 2, 1, 1, 1)
        self.lblDocumentType = QtGui.QLabel(self.tabMain)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblDocumentType.sizePolicy().hasHeightForWidth())
        self.lblDocumentType.setSizePolicy(sizePolicy)
        self.lblDocumentType.setObjectName(_fromUtf8("lblDocumentType"))
        self.gridLayout.addWidget(self.lblDocumentType, 4, 0, 1, 1)
        self.cmbDocumentType = CRBComboBox(self.tabMain)
        self.cmbDocumentType.setObjectName(_fromUtf8("cmbDocumentType"))
        self.gridLayout.addWidget(self.cmbDocumentType, 4, 1, 1, 1)
        self.edtName = QtGui.QLineEdit(self.tabMain)
        self.edtName.setObjectName(_fromUtf8("edtName"))
        self.gridLayout.addWidget(self.edtName, 1, 1, 1, 2)
        self.lblName = QtGui.QLabel(self.tabMain)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblName.sizePolicy().hasHeightForWidth())
        self.lblName.setSizePolicy(sizePolicy)
        self.lblName.setObjectName(_fromUtf8("lblName"))
        self.gridLayout.addWidget(self.lblName, 1, 0, 1, 1)
        self.edtCode = QtGui.QLineEdit(self.tabMain)
        self.edtCode.setObjectName(_fromUtf8("edtCode"))
        self.gridLayout.addWidget(self.edtCode, 0, 1, 1, 2)
        self.lblCode = QtGui.QLabel(self.tabMain)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblCode.sizePolicy().hasHeightForWidth())
        self.lblCode.setSizePolicy(sizePolicy)
        self.lblCode.setObjectName(_fromUtf8("lblCode"))
        self.gridLayout.addWidget(self.lblCode, 0, 0, 1, 1)
        self.tabWidget.addTab(self.tabMain, _fromUtf8(""))
        self.tabIdentification = QtGui.QWidget()
        self.tabIdentification.setObjectName(_fromUtf8("tabIdentification"))
        self.gridLayout_3 = QtGui.QGridLayout(self.tabIdentification)
        self.gridLayout_3.setSpacing(4)
        self.gridLayout_3.setMargin(4)
        self.gridLayout_3.setObjectName(_fromUtf8("gridLayout_3"))
        self.tblIdentification = CInDocTableView(self.tabIdentification)
        self.tblIdentification.setObjectName(_fromUtf8("tblIdentification"))
        self.gridLayout_3.addWidget(self.tblIdentification, 0, 0, 1, 1)
        self.tabWidget.addTab(self.tabIdentification, _fromUtf8(""))
        self.gridLayout_2.addWidget(self.tabWidget, 2, 0, 1, 2)
        self.buttonBox = QtGui.QDialogButtonBox(SocStatusTypeItemEditorDialog)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout_2.addWidget(self.buttonBox, 3, 0, 1, 2)
        self.lblRegionalCode.setBuddy(self.edtRegionalCode)
        self.lblDocumentType.setBuddy(self.cmbDocumentType)
        self.lblName.setBuddy(self.edtName)
        self.lblCode.setBuddy(self.edtCode)

        self.retranslateUi(SocStatusTypeItemEditorDialog)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), SocStatusTypeItemEditorDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), SocStatusTypeItemEditorDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(SocStatusTypeItemEditorDialog)
        SocStatusTypeItemEditorDialog.setTabOrder(self.tabWidget, self.edtCode)
        SocStatusTypeItemEditorDialog.setTabOrder(self.edtCode, self.edtName)
        SocStatusTypeItemEditorDialog.setTabOrder(self.edtName, self.edtShortName)
        SocStatusTypeItemEditorDialog.setTabOrder(self.edtShortName, self.edtRegionalCode)
        SocStatusTypeItemEditorDialog.setTabOrder(self.edtRegionalCode, self.cmbDocumentType)
        SocStatusTypeItemEditorDialog.setTabOrder(self.cmbDocumentType, self.tblIdentification)
        SocStatusTypeItemEditorDialog.setTabOrder(self.tblIdentification, self.buttonBox)

    def retranslateUi(self, SocStatusTypeItemEditorDialog):
        SocStatusTypeItemEditorDialog.setWindowTitle(_translate("SocStatusTypeItemEditorDialog", "ChangeMe!", None))
        self.lblShortName.setText(_translate("SocStatusTypeItemEditorDialog", "Краткое наименование", None))
        self.lblRegionalCode.setText(_translate("SocStatusTypeItemEditorDialog", "Код для отчетов", None))
        self.lblDocumentType.setText(_translate("SocStatusTypeItemEditorDialog", "&Тип документа", None))
        self.lblName.setText(_translate("SocStatusTypeItemEditorDialog", "&Наименование", None))
        self.lblCode.setText(_translate("SocStatusTypeItemEditorDialog", "&Код", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabMain), _translate("SocStatusTypeItemEditorDialog", "&Основная информация", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabIdentification), _translate("SocStatusTypeItemEditorDialog", "&Идентификация", None))

from library.InDocTable import CInDocTableView
from library.crbcombobox import CRBComboBox

if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    SocStatusTypeItemEditorDialog = QtGui.QDialog()
    ui = Ui_SocStatusTypeItemEditorDialog()
    ui.setupUi(SocStatusTypeItemEditorDialog)
    SocStatusTypeItemEditorDialog.show()
    sys.exit(app.exec_())

