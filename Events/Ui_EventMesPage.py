# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\Project\Samson\UP_s11\client_test\Events\EventMesPage.ui'
#
# Created: Fri Feb 27 16:56:08 2026
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

class Ui_EventMesPageWidget(object):
    def setupUi(self, EventMesPageWidget):
        EventMesPageWidget.setObjectName(_fromUtf8("EventMesPageWidget"))
        EventMesPageWidget.resize(1036, 631)
        self.gridLayout = QtGui.QGridLayout(EventMesPageWidget)
        self.gridLayout.setMargin(4)
        self.gridLayout.setSpacing(4)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.grpCSG = QtGui.QGroupBox(EventMesPageWidget)
        self.grpCSG.setObjectName(_fromUtf8("grpCSG"))
        self.verticalLayout = QtGui.QVBoxLayout(self.grpCSG)
        self.verticalLayout.setSpacing(4)
        self.verticalLayout.setMargin(4)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.splitter = QtGui.QSplitter(self.grpCSG)
        self.splitter.setOrientation(QtCore.Qt.Vertical)
        self.splitter.setObjectName(_fromUtf8("splitter"))
        self.tblCSGs = CInDocTableView(self.splitter)
        self.tblCSGs.setObjectName(_fromUtf8("tblCSGs"))
        self.tblCSGSubItems = CInDocTableView(self.splitter)
        self.tblCSGSubItems.setEnabled(False)
        self.tblCSGSubItems.setObjectName(_fromUtf8("tblCSGSubItems"))
        self.verticalLayout.addWidget(self.splitter)
        self.gridLayout.addWidget(self.grpCSG, 6, 0, 1, 3)
        self.cmbMesSpecification = CRBComboBox(EventMesPageWidget)
        self.cmbMesSpecification.setObjectName(_fromUtf8("cmbMesSpecification"))
        self.gridLayout.addWidget(self.cmbMesSpecification, 1, 1, 1, 2)
        self.lblMesSpecification = QtGui.QLabel(EventMesPageWidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblMesSpecification.sizePolicy().hasHeightForWidth())
        self.lblMesSpecification.setSizePolicy(sizePolicy)
        self.lblMesSpecification.setObjectName(_fromUtf8("lblMesSpecification"))
        self.gridLayout.addWidget(self.lblMesSpecification, 1, 0, 1, 1)
        self.cmbMes = CMESComboBox(EventMesPageWidget)
        self.cmbMes.setObjectName(_fromUtf8("cmbMes"))
        self.gridLayout.addWidget(self.cmbMes, 0, 1, 1, 2)
        self.btnShowMes = QtGui.QPushButton(EventMesPageWidget)
        self.btnShowMes.setEnabled(False)
        self.btnShowMes.setObjectName(_fromUtf8("btnShowMes"))
        self.gridLayout.addWidget(self.btnShowMes, 4, 1, 1, 1)
        self.lblMes = QtGui.QLabel(EventMesPageWidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblMes.sizePolicy().hasHeightForWidth())
        self.lblMes.setSizePolicy(sizePolicy)
        self.lblMes.setObjectName(_fromUtf8("lblMes"))
        self.gridLayout.addWidget(self.lblMes, 0, 0, 1, 1)
        self.btnCheckMes = QtGui.QPushButton(EventMesPageWidget)
        self.btnCheckMes.setEnabled(False)
        self.btnCheckMes.setObjectName(_fromUtf8("btnCheckMes"))
        self.gridLayout.addWidget(self.btnCheckMes, 3, 1, 1, 1)
        self.btnOpenSpr69 = QtGui.QPushButton(EventMesPageWidget)
        self.btnOpenSpr69.setEnabled(True)
        self.btnOpenSpr69.setCheckable(False)
        self.btnOpenSpr69.setObjectName(_fromUtf8("btnOpenSpr69"))
        self.gridLayout.addWidget(self.btnOpenSpr69, 5, 1, 1, 1)
        self.lblMesSpecification.setBuddy(self.cmbMesSpecification)
        self.lblMes.setBuddy(self.cmbMes)

        self.retranslateUi(EventMesPageWidget)
        QtCore.QMetaObject.connectSlotsByName(EventMesPageWidget)
        EventMesPageWidget.setTabOrder(self.cmbMes, self.cmbMesSpecification)
        EventMesPageWidget.setTabOrder(self.cmbMesSpecification, self.btnCheckMes)
        EventMesPageWidget.setTabOrder(self.btnCheckMes, self.btnShowMes)
        EventMesPageWidget.setTabOrder(self.btnShowMes, self.tblCSGs)

    def retranslateUi(self, EventMesPageWidget):
        EventMesPageWidget.setWindowTitle(_translate("EventMesPageWidget", "Form", None))
        self.grpCSG.setTitle(_translate("EventMesPageWidget", "КСГ", None))
        self.lblMesSpecification.setText(_translate("EventMesPageWidget", "Особенности выполнения МЭС", None))
        self.btnShowMes.setText(_translate("EventMesPageWidget", "Показать требования стандарта", None))
        self.lblMes.setText(_translate("EventMesPageWidget", "МЭС", None))
        self.btnCheckMes.setText(_translate("EventMesPageWidget", "Проверить выполнение стандарта", None))
        self.btnOpenSpr69.setText(_translate("EventMesPageWidget", "Просмотр группировщика КСГ (спр69)", None))

from library.InDocTable import CInDocTableView
from library.crbcombobox import CRBComboBox
from library.MES.MESComboBox import CMESComboBox
