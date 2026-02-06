# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\projects\Samson\UP_s11\client_pre_release\Reports\TMKInfo.ui'
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

class Ui_tmkInfo(object):
    def setupUi(self, tmkInfo):
        tmkInfo.setObjectName(_fromUtf8("tmkInfo"))
        tmkInfo.resize(400, 300)
        self.gridLayout = QtGui.QGridLayout(tmkInfo)
        self.gridLayout.setMargin(4)
        self.gridLayout.setSpacing(4)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.edtInfo = QtGui.QTextEdit(tmkInfo)
        self.edtInfo.setReadOnly(True)
        self.edtInfo.setObjectName(_fromUtf8("edtInfo"))
        self.gridLayout.addWidget(self.edtInfo, 0, 0, 1, 2)
        spacerItem = QtGui.QSpacerItem(308, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 1, 0, 1, 1)
        self.btnClose = QtGui.QPushButton(tmkInfo)
        self.btnClose.setObjectName(_fromUtf8("btnClose"))
        self.gridLayout.addWidget(self.btnClose, 1, 1, 1, 1)

        self.retranslateUi(tmkInfo)
        QtCore.QObject.connect(self.btnClose, QtCore.SIGNAL(_fromUtf8("clicked()")), tmkInfo.close)
        QtCore.QMetaObject.connectSlotsByName(tmkInfo)

    def retranslateUi(self, tmkInfo):
        tmkInfo.setWindowTitle(_translate("tmkInfo", "Dialog", None))
        self.btnClose.setText(_translate("tmkInfo", "Закрыть", None))

