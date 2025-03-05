# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Rabota\s11\Events\PropertyValueToTemplateComboBoxPopup.ui'
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

class Ui_PropertyValueToTemplateComboBoxPopup(object):
    def setupUi(self, PropertyValueToTemplateComboBoxPopup):
        PropertyValueToTemplateComboBoxPopup.setObjectName(_fromUtf8("PropertyValueToTemplateComboBoxPopup"))
        PropertyValueToTemplateComboBoxPopup.resize(687, 453)
        self.gridLayout = QtGui.QGridLayout(PropertyValueToTemplateComboBoxPopup)
        self.gridLayout.setMargin(4)
        self.gridLayout.setSpacing(4)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.tblPropertyTemplate = CTableView(PropertyValueToTemplateComboBoxPopup)
        self.tblPropertyTemplate.setObjectName(_fromUtf8("tblPropertyTemplate"))
        self.gridLayout.addWidget(self.tblPropertyTemplate, 2, 0, 1, 2)

        self.retranslateUi(PropertyValueToTemplateComboBoxPopup)
        QtCore.QMetaObject.connectSlotsByName(PropertyValueToTemplateComboBoxPopup)

    def retranslateUi(self, PropertyValueToTemplateComboBoxPopup):
        PropertyValueToTemplateComboBoxPopup.setWindowTitle(_translate("PropertyValueToTemplateComboBoxPopup", "Form", None))

from library.TableView import CTableView

if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    PropertyValueToTemplateComboBoxPopup = QtGui.QWidget()
    ui = Ui_PropertyValueToTemplateComboBoxPopup()
    ui.setupUi(PropertyValueToTemplateComboBoxPopup)
    PropertyValueToTemplateComboBoxPopup.show()
    sys.exit(app.exec_())

