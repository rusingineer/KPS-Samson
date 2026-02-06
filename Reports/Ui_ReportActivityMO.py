# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\projects\Samson\UP_s11\client\Reports\ReportActivityMO.ui'
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

class Ui_ReportActivityMO(object):
    def setupUi(self, ReportActivityMO):
        ReportActivityMO.setObjectName(_fromUtf8("ReportActivityMO"))
        ReportActivityMO.setWindowModality(QtCore.Qt.ApplicationModal)
        ReportActivityMO.resize(421, 125)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(ReportActivityMO.sizePolicy().hasHeightForWidth())
        ReportActivityMO.setSizePolicy(sizePolicy)
        ReportActivityMO.setSizeGripEnabled(True)
        self.gridlayout = QtGui.QGridLayout(ReportActivityMO)
        self.gridlayout.setMargin(4)
        self.gridlayout.setSpacing(4)
        self.gridlayout.setObjectName(_fromUtf8("gridlayout"))
        self.edtDate = CDateEdit(ReportActivityMO)
        self.edtDate.setCalendarPopup(True)
        self.edtDate.setObjectName(_fromUtf8("edtDate"))
        self.gridlayout.addWidget(self.edtDate, 0, 1, 1, 1)
        self.lblDate = QtGui.QLabel(ReportActivityMO)
        self.lblDate.setObjectName(_fromUtf8("lblDate"))
        self.gridlayout.addWidget(self.lblDate, 0, 0, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(ReportActivityMO)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridlayout.addWidget(self.buttonBox, 11, 0, 1, 3)
        self.lblDate.setBuddy(self.edtDate)

        self.retranslateUi(ReportActivityMO)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), ReportActivityMO.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), ReportActivityMO.reject)
        QtCore.QMetaObject.connectSlotsByName(ReportActivityMO)
        ReportActivityMO.setTabOrder(self.edtDate, self.buttonBox)

    def retranslateUi(self, ReportActivityMO):
        ReportActivityMO.setWindowTitle(_translate("ReportActivityMO", "Деятельность МО (оперативный отчёт)", None))
        self.lblDate.setText(_translate("ReportActivityMO", "Дата:", None))

from library.DateEdit import CDateEdit
