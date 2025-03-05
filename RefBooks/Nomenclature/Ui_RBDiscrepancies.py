# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\Samson\UP_s11\client_test\RefBooks\Nomenclature\RBDiscrepancies.ui'
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

class Ui_RBDiscrepancies(object):
    def setupUi(self, RBDiscrepancies):
        RBDiscrepancies.setObjectName(_fromUtf8("RBDiscrepancies"))
        RBDiscrepancies.resize(791, 563)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8(":/icons/Icon2.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        RBDiscrepancies.setWindowIcon(icon)
        self.gridLayout = QtGui.QGridLayout(RBDiscrepancies)
        self.gridLayout.setMargin(4)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.splitter = QtGui.QSplitter(RBDiscrepancies)
        self.splitter.setOrientation(QtCore.Qt.Vertical)
        self.splitter.setObjectName(_fromUtf8("splitter"))
        self.tblDiscrepancies = QtGui.QTableWidget(self.splitter)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tblDiscrepancies.sizePolicy().hasHeightForWidth())
        self.tblDiscrepancies.setSizePolicy(sizePolicy)
        self.tblDiscrepancies.setMidLineWidth(0)
        self.tblDiscrepancies.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.tblDiscrepancies.setObjectName(_fromUtf8("tblDiscrepancies"))
        self.tblDiscrepancies.setColumnCount(4)
        self.tblDiscrepancies.setRowCount(0)
        item = QtGui.QTableWidgetItem()
        self.tblDiscrepancies.setHorizontalHeaderItem(0, item)
        item = QtGui.QTableWidgetItem()
        self.tblDiscrepancies.setHorizontalHeaderItem(1, item)
        item = QtGui.QTableWidgetItem()
        self.tblDiscrepancies.setHorizontalHeaderItem(2, item)
        item = QtGui.QTableWidgetItem()
        self.tblDiscrepancies.setHorizontalHeaderItem(3, item)
        self.tblDiscrepancies.horizontalHeader().setDefaultSectionSize(150)
        self.tblDiscrepancies.horizontalHeader().setMinimumSectionSize(150)
        self.tblDiscrepancies.horizontalHeader().setStretchLastSection(True)
        self.buttonBox = QtGui.QDialogButtonBox(self.splitter)
        self.buttonBox.setMaximumSize(QtCore.QSize(16777215, 25))
        self.buttonBox.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(False)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.splitter, 0, 0, 1, 1)

        self.retranslateUi(RBDiscrepancies)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), RBDiscrepancies.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), RBDiscrepancies.reject)
        QtCore.QMetaObject.connectSlotsByName(RBDiscrepancies)

    def retranslateUi(self, RBDiscrepancies):
        RBDiscrepancies.setWindowTitle(_translate("RBDiscrepancies", "Расхождения между заполняемыми значениями", None))
        item = self.tblDiscrepancies.horizontalHeaderItem(0)
        item.setText(_translate("RBDiscrepancies", "Наименование поля", None))
        item = self.tblDiscrepancies.horizontalHeaderItem(1)
        item.setText(_translate("RBDiscrepancies", "Данные МИС", None))
        item = self.tblDiscrepancies.horizontalHeaderItem(2)
        item.setText(_translate("RBDiscrepancies", "Данные ЕСКЛП", None))
        item = self.tblDiscrepancies.horizontalHeaderItem(3)
        item.setText(_translate("RBDiscrepancies", "Заменить", None))

import s11main_rc
