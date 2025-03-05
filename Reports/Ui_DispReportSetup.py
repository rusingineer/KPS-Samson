# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\Samson\UP_s11\client\Reports\DispReportSetup.ui'
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

class Ui_DispReportSetupDialog(object):
    def setupUi(self, DispReportSetupDialog):
        DispReportSetupDialog.setObjectName(_fromUtf8("DispReportSetupDialog"))
        DispReportSetupDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        DispReportSetupDialog.resize(578, 200)
        DispReportSetupDialog.setSizeGripEnabled(True)
        self.gridlayout = QtGui.QGridLayout(DispReportSetupDialog)
        self.gridlayout.setMargin(4)
        self.gridlayout.setSpacing(4)
        self.gridlayout.setObjectName(_fromUtf8("gridlayout"))
        self.frmAge = QtGui.QFrame(DispReportSetupDialog)
        self.frmAge.setFrameShape(QtGui.QFrame.NoFrame)
        self.frmAge.setFrameShadow(QtGui.QFrame.Raised)
        self.frmAge.setObjectName(_fromUtf8("frmAge"))
        self.hboxlayout = QtGui.QHBoxLayout(self.frmAge)
        self.hboxlayout.setMargin(0)
        self.hboxlayout.setSpacing(4)
        self.hboxlayout.setObjectName(_fromUtf8("hboxlayout"))
        self.edtAgeFrom = QtGui.QSpinBox(self.frmAge)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.edtAgeFrom.sizePolicy().hasHeightForWidth())
        self.edtAgeFrom.setSizePolicy(sizePolicy)
        self.edtAgeFrom.setMaximum(150)
        self.edtAgeFrom.setObjectName(_fromUtf8("edtAgeFrom"))
        self.hboxlayout.addWidget(self.edtAgeFrom)
        self.lblAgeTo = QtGui.QLabel(self.frmAge)
        self.lblAgeTo.setObjectName(_fromUtf8("lblAgeTo"))
        self.hboxlayout.addWidget(self.lblAgeTo)
        self.edtAgeTo = QtGui.QSpinBox(self.frmAge)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.edtAgeTo.sizePolicy().hasHeightForWidth())
        self.edtAgeTo.setSizePolicy(sizePolicy)
        self.edtAgeTo.setMaximum(150)
        self.edtAgeTo.setObjectName(_fromUtf8("edtAgeTo"))
        self.hboxlayout.addWidget(self.edtAgeTo)
        self.lblAgeYears = QtGui.QLabel(self.frmAge)
        self.lblAgeYears.setObjectName(_fromUtf8("lblAgeYears"))
        self.hboxlayout.addWidget(self.lblAgeYears)
        spacerItem = QtGui.QSpacerItem(21, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.hboxlayout.addItem(spacerItem)
        self.gridlayout.addWidget(self.frmAge, 3, 1, 1, 3)
        self.buttonBox = QtGui.QDialogButtonBox(DispReportSetupDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridlayout.addWidget(self.buttonBox, 12, 0, 1, 4)
        self.edtBegDate = CDateEdit(DispReportSetupDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.edtBegDate.sizePolicy().hasHeightForWidth())
        self.edtBegDate.setSizePolicy(sizePolicy)
        self.edtBegDate.setCalendarPopup(True)
        self.edtBegDate.setObjectName(_fromUtf8("edtBegDate"))
        self.gridlayout.addWidget(self.edtBegDate, 0, 1, 1, 2)
        self.lblBegDate = QtGui.QLabel(DispReportSetupDialog)
        self.lblBegDate.setObjectName(_fromUtf8("lblBegDate"))
        self.gridlayout.addWidget(self.lblBegDate, 0, 0, 1, 1)
        self.edtEndDate = CDateEdit(DispReportSetupDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.edtEndDate.sizePolicy().hasHeightForWidth())
        self.edtEndDate.setSizePolicy(sizePolicy)
        self.edtEndDate.setCalendarPopup(True)
        self.edtEndDate.setObjectName(_fromUtf8("edtEndDate"))
        self.gridlayout.addWidget(self.edtEndDate, 1, 1, 1, 2)
        self.lblEndDate = QtGui.QLabel(DispReportSetupDialog)
        self.lblEndDate.setObjectName(_fromUtf8("lblEndDate"))
        self.gridlayout.addWidget(self.lblEndDate, 1, 0, 1, 1)
        spacerItem1 = QtGui.QSpacerItem(111, 20, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridlayout.addItem(spacerItem1, 9, 0, 1, 1)
        self.lblAge = QtGui.QLabel(DispReportSetupDialog)
        self.lblAge.setObjectName(_fromUtf8("lblAge"))
        self.gridlayout.addWidget(self.lblAge, 3, 0, 1, 1)
        self.lblDir = QtGui.QLabel(DispReportSetupDialog)
        self.lblDir.setObjectName(_fromUtf8("lblDir"))
        self.gridlayout.addWidget(self.lblDir, 7, 0, 1, 1)
        self.chkAttachment = QtGui.QCheckBox(DispReportSetupDialog)
        self.chkAttachment.setObjectName(_fromUtf8("chkAttachment"))
        self.gridlayout.addWidget(self.chkAttachment, 6, 0, 1, 4)
        self.edtDir = QtGui.QLineEdit(DispReportSetupDialog)
        self.edtDir.setEnabled(False)
        self.edtDir.setObjectName(_fromUtf8("edtDir"))
        self.gridlayout.addWidget(self.edtDir, 7, 2, 1, 1)
        self.btnSelectDir = QtGui.QToolButton(DispReportSetupDialog)
        self.btnSelectDir.setObjectName(_fromUtf8("btnSelectDir"))
        self.gridlayout.addWidget(self.btnSelectDir, 7, 3, 1, 1)
        self.chkConsiderWorkPost = QtGui.QCheckBox(DispReportSetupDialog)
        self.chkConsiderWorkPost.setObjectName(_fromUtf8("chkConsiderWorkPost"))
        self.gridlayout.addWidget(self.chkConsiderWorkPost, 8, 0, 1, 3)
        self.lblAgeTo.setBuddy(self.edtAgeTo)
        self.lblAgeYears.setBuddy(self.edtAgeTo)
        self.lblBegDate.setBuddy(self.edtBegDate)
        self.lblEndDate.setBuddy(self.edtEndDate)
        self.lblAge.setBuddy(self.edtAgeFrom)

        self.retranslateUi(DispReportSetupDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), DispReportSetupDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), DispReportSetupDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(DispReportSetupDialog)
        DispReportSetupDialog.setTabOrder(self.edtBegDate, self.edtEndDate)
        DispReportSetupDialog.setTabOrder(self.edtEndDate, self.edtAgeFrom)
        DispReportSetupDialog.setTabOrder(self.edtAgeFrom, self.edtAgeTo)
        DispReportSetupDialog.setTabOrder(self.edtAgeTo, self.chkAttachment)
        DispReportSetupDialog.setTabOrder(self.chkAttachment, self.buttonBox)

    def retranslateUi(self, DispReportSetupDialog):
        DispReportSetupDialog.setWindowTitle(_translate("DispReportSetupDialog", "параметры отчёта", None))
        self.lblAgeTo.setText(_translate("DispReportSetupDialog", "по", None))
        self.lblAgeYears.setText(_translate("DispReportSetupDialog", "лет", None))
        self.lblBegDate.setText(_translate("DispReportSetupDialog", "Дата начала периода", None))
        self.lblEndDate.setText(_translate("DispReportSetupDialog", "Дата окончания периода", None))
        self.lblAge.setText(_translate("DispReportSetupDialog", "Во&зраст с", None))
        self.lblDir.setText(_translate("DispReportSetupDialog", "Сохранить в директории", None))
        self.chkAttachment.setText(_translate("DispReportSetupDialog", "Учитывать прикрепление", None))
        self.btnSelectDir.setText(_translate("DispReportSetupDialog", "...", None))
        self.chkConsiderWorkPost.setText(_translate("DispReportSetupDialog", "Учитывать наличие должности при определении места работы", None))

from library.DateEdit import CDateEdit
