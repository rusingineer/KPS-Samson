# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ObservationGroupEditor.ui'
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

class Ui_ObservationGroupEditor(object):
    def setupUi(self, ObservationGroupEditor):
        ObservationGroupEditor.setObjectName(_fromUtf8("ObservationGroupEditor"))
        ObservationGroupEditor.resize(438, 320)
        self.gridLayout = QtGui.QGridLayout(ObservationGroupEditor)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.lblBegDate = QtGui.QLabel(ObservationGroupEditor)
        self.lblBegDate.setObjectName(_fromUtf8("lblBegDate"))
        self.gridLayout.addWidget(self.lblBegDate, 2, 0, 1, 1)
        self.edtCode = QtGui.QLineEdit(ObservationGroupEditor)
        self.edtCode.setObjectName(_fromUtf8("edtCode"))
        self.gridLayout.addWidget(self.edtCode, 0, 1, 1, 1)
        self.lblCode = QtGui.QLabel(ObservationGroupEditor)
        self.lblCode.setObjectName(_fromUtf8("lblCode"))
        self.gridLayout.addWidget(self.lblCode, 0, 0, 1, 1)
        self.lblName = QtGui.QLabel(ObservationGroupEditor)
        self.lblName.setObjectName(_fromUtf8("lblName"))
        self.gridLayout.addWidget(self.lblName, 1, 0, 1, 1)
        self.edtName = QtGui.QLineEdit(ObservationGroupEditor)
        self.edtName.setObjectName(_fromUtf8("edtName"))
        self.gridLayout.addWidget(self.edtName, 1, 1, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(ObservationGroupEditor)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 5, 0, 1, 2)
        self.lblEndDate = QtGui.QLabel(ObservationGroupEditor)
        self.lblEndDate.setObjectName(_fromUtf8("lblEndDate"))
        self.gridLayout.addWidget(self.lblEndDate, 3, 0, 1, 1)
        self.edtBegDate = CDateEdit(ObservationGroupEditor)
        self.edtBegDate.setObjectName(_fromUtf8("edtBegDate"))
        self.gridLayout.addWidget(self.edtBegDate, 2, 1, 1, 1)
        self.edtEndDate = CDateEdit(ObservationGroupEditor)
        self.edtEndDate.setObjectName(_fromUtf8("edtEndDate"))
        self.gridLayout.addWidget(self.edtEndDate, 3, 1, 1, 1)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, 4, 0, 1, 2)

        self.retranslateUi(ObservationGroupEditor)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), ObservationGroupEditor.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), ObservationGroupEditor.reject)
        QtCore.QMetaObject.connectSlotsByName(ObservationGroupEditor)

    def retranslateUi(self, ObservationGroupEditor):
        self.lblBegDate.setText(_translate("ObservationGroupEditor", "Дата начала", None))
        self.lblCode.setText(_translate("ObservationGroupEditor", "Код", None))
        self.lblName.setText(_translate("ObservationGroupEditor", "Наименование", None))
        self.lblEndDate.setText(_translate("ObservationGroupEditor", "Дата окончания", None))

from library.DateEdit import CDateEdit

if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    ObservationGroupEditor = QtGui.QDialog()
    ui = Ui_ObservationGroupEditor()
    ui.setupUi(ObservationGroupEditor)
    ObservationGroupEditor.show()
    sys.exit(app.exec_())

