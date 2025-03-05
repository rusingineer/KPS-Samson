# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/aeiklorvy/samson/Events/NomenclatureExpense/ExtendAppointmentNomenclatureDialog.ui'
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

class Ui_ExtendAppointmentNomenclatureDialog(object):
    def setupUi(self, ExtendAppointmentNomenclatureDialog):
        ExtendAppointmentNomenclatureDialog.setObjectName(_fromUtf8("ExtendAppointmentNomenclatureDialog"))
        ExtendAppointmentNomenclatureDialog.resize(400, 116)
        self.gridLayout = QtGui.QGridLayout(ExtendAppointmentNomenclatureDialog)
        self.gridLayout.setMargin(4)
        self.gridLayout.setSpacing(4)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, 3, 0, 1, 1)
        self.chkLastDayCourse = QtGui.QCheckBox(ExtendAppointmentNomenclatureDialog)
        self.chkLastDayCourse.setObjectName(_fromUtf8("chkLastDayCourse"))
        self.gridLayout.addWidget(self.chkLastDayCourse, 2, 0, 1, 2)
        self.lblSkipAfterLastDayCourse = QtGui.QLabel(ExtendAppointmentNomenclatureDialog)
        self.lblSkipAfterLastDayCourse.setObjectName(_fromUtf8("lblSkipAfterLastDayCourse"))
        self.gridLayout.addWidget(self.lblSkipAfterLastDayCourse, 1, 0, 1, 1)
        self.lblQuantityDay = QtGui.QLabel(ExtendAppointmentNomenclatureDialog)
        self.lblQuantityDay.setObjectName(_fromUtf8("lblQuantityDay"))
        self.gridLayout.addWidget(self.lblQuantityDay, 0, 0, 1, 1)
        self.edtQuantityDay = CSpinBox(ExtendAppointmentNomenclatureDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.edtQuantityDay.sizePolicy().hasHeightForWidth())
        self.edtQuantityDay.setSizePolicy(sizePolicy)
        self.edtQuantityDay.setMinimum(1)
        self.edtQuantityDay.setProperty("value", 1)
        self.edtQuantityDay.setObjectName(_fromUtf8("edtQuantityDay"))
        self.gridLayout.addWidget(self.edtQuantityDay, 0, 1, 1, 1)
        self.edtSkipAfterLastDayCourse = CSpinBox(ExtendAppointmentNomenclatureDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.edtSkipAfterLastDayCourse.sizePolicy().hasHeightForWidth())
        self.edtSkipAfterLastDayCourse.setSizePolicy(sizePolicy)
        self.edtSkipAfterLastDayCourse.setObjectName(_fromUtf8("edtSkipAfterLastDayCourse"))
        self.gridLayout.addWidget(self.edtSkipAfterLastDayCourse, 1, 1, 1, 1)
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem1, 0, 2, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(ExtendAppointmentNomenclatureDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 4, 0, 1, 3)

        self.retranslateUi(ExtendAppointmentNomenclatureDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), ExtendAppointmentNomenclatureDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), ExtendAppointmentNomenclatureDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(ExtendAppointmentNomenclatureDialog)
        ExtendAppointmentNomenclatureDialog.setTabOrder(self.edtQuantityDay, self.edtSkipAfterLastDayCourse)
        ExtendAppointmentNomenclatureDialog.setTabOrder(self.edtSkipAfterLastDayCourse, self.chkLastDayCourse)
        ExtendAppointmentNomenclatureDialog.setTabOrder(self.chkLastDayCourse, self.buttonBox)

    def retranslateUi(self, ExtendAppointmentNomenclatureDialog):
        ExtendAppointmentNomenclatureDialog.setWindowTitle(_translate("ExtendAppointmentNomenclatureDialog", "Продление назначения", None))
        self.chkLastDayCourse.setText(_translate("ExtendAppointmentNomenclatureDialog", "По последнему дню курса", None))
        self.lblSkipAfterLastDayCourse.setText(_translate("ExtendAppointmentNomenclatureDialog", "После последнего дня курса пропустить:", None))
        self.lblQuantityDay.setText(_translate("ExtendAppointmentNomenclatureDialog", "Количество дней:", None))

from library.SpinBox import CSpinBox

if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    ExtendAppointmentNomenclatureDialog = QtGui.QDialog()
    ui = Ui_ExtendAppointmentNomenclatureDialog()
    ui.setupUi(ExtendAppointmentNomenclatureDialog)
    ExtendAppointmentNomenclatureDialog.show()
    sys.exit(app.exec_())

