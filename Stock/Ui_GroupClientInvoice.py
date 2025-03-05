# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\samson\Stock\GroupClientInvoice.ui'
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

class Ui_GroupClientInvoice(object):
    def setupUi(self, GroupClientInvoice):
        GroupClientInvoice.setObjectName(_fromUtf8("GroupClientInvoice"))
        GroupClientInvoice.resize(486, 391)
        self.gridLayout = QtGui.QGridLayout(GroupClientInvoice)
        self.gridLayout.setMargin(4)
        self.gridLayout.setSpacing(4)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setSpacing(4)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.lblDate = QtGui.QLabel(GroupClientInvoice)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblDate.sizePolicy().hasHeightForWidth())
        self.lblDate.setSizePolicy(sizePolicy)
        self.lblDate.setObjectName(_fromUtf8("lblDate"))
        self.horizontalLayout.addWidget(self.lblDate)
        self.edtDate = CCurrentDateEditEx(GroupClientInvoice)
        self.edtDate.setCalendarPopup(True)
        self.edtDate.setObjectName(_fromUtf8("edtDate"))
        self.horizontalLayout.addWidget(self.edtDate)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.gridLayout.addLayout(self.horizontalLayout, 0, 0, 1, 2)
        self.tabWidget = QtGui.QTabWidget(GroupClientInvoice)
        self.tabWidget.setObjectName(_fromUtf8("tabWidget"))
        self.tabClientNomenclatures = QtGui.QWidget()
        self.tabClientNomenclatures.setObjectName(_fromUtf8("tabClientNomenclatures"))
        self.gridLayout_2 = QtGui.QGridLayout(self.tabClientNomenclatures)
        self.gridLayout_2.setMargin(4)
        self.gridLayout_2.setSpacing(4)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.tblClientNomenclatures = CInDocTableView(self.tabClientNomenclatures)
        self.tblClientNomenclatures.setObjectName(_fromUtf8("tblClientNomenclatures"))
        self.gridLayout_2.addWidget(self.tblClientNomenclatures, 0, 0, 1, 1)
        self.tabWidget.addTab(self.tabClientNomenclatures, _fromUtf8(""))
        self.tabClientNomenclaturesControl = QtGui.QWidget()
        self.tabClientNomenclaturesControl.setObjectName(_fromUtf8("tabClientNomenclaturesControl"))
        self.gridLayout_3 = QtGui.QGridLayout(self.tabClientNomenclaturesControl)
        self.gridLayout_3.setMargin(4)
        self.gridLayout_3.setSpacing(4)
        self.gridLayout_3.setObjectName(_fromUtf8("gridLayout_3"))
        self.tblClientNomenclaturesControl = CInDocTableView(self.tabClientNomenclaturesControl)
        self.tblClientNomenclaturesControl.setObjectName(_fromUtf8("tblClientNomenclaturesControl"))
        self.gridLayout_3.addWidget(self.tblClientNomenclaturesControl, 0, 0, 1, 1)
        self.tabWidget.addTab(self.tabClientNomenclaturesControl, _fromUtf8(""))
        self.gridLayout.addWidget(self.tabWidget, 1, 0, 1, 2)
        self.statusBar = QtGui.QStatusBar(GroupClientInvoice)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.statusBar.sizePolicy().hasHeightForWidth())
        self.statusBar.setSizePolicy(sizePolicy)
        self.statusBar.setSizeGripEnabled(False)
        self.statusBar.setObjectName(_fromUtf8("statusBar"))
        self.gridLayout.addWidget(self.statusBar, 2, 0, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(GroupClientInvoice)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.buttonBox.sizePolicy().hasHeightForWidth())
        self.buttonBox.setSizePolicy(sizePolicy)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Close)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 2, 1, 1, 1)

        self.retranslateUi(GroupClientInvoice)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), GroupClientInvoice.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), GroupClientInvoice.reject)
        QtCore.QMetaObject.connectSlotsByName(GroupClientInvoice)
        GroupClientInvoice.setTabOrder(self.edtDate, self.tabWidget)
        GroupClientInvoice.setTabOrder(self.tabWidget, self.tblClientNomenclatures)
        GroupClientInvoice.setTabOrder(self.tblClientNomenclatures, self.tblClientNomenclaturesControl)
        GroupClientInvoice.setTabOrder(self.tblClientNomenclaturesControl, self.buttonBox)

    def retranslateUi(self, GroupClientInvoice):
        GroupClientInvoice.setWindowTitle(_translate("GroupClientInvoice", "Dialog", None))
        self.lblDate.setText(_translate("GroupClientInvoice", "Дата", None))
        self.edtDate.setDisplayFormat(_translate("GroupClientInvoice", "dd.MM.yyyy", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabClientNomenclatures), _translate("GroupClientInvoice", "Списание ЛСиИМН", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabClientNomenclaturesControl), _translate("GroupClientInvoice", "Контроль выполнения назначений", None))
        self.statusBar.setToolTip(_translate("GroupClientInvoice", "A status bar", None))
        self.statusBar.setWhatsThis(_translate("GroupClientInvoice", "A status bar.", None))

from library.DateEdit import CCurrentDateEditEx
from library.InDocTable import CInDocTableView
