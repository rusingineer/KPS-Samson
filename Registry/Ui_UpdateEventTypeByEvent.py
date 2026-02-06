# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\projects\Samson\UP_s11\client\Registry\UpdateEventTypeByEvent.ui'
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

class Ui_UpdateEventTypeByEvent(object):
    def setupUi(self, UpdateEventTypeByEvent):
        UpdateEventTypeByEvent.setObjectName(_fromUtf8("UpdateEventTypeByEvent"))
        UpdateEventTypeByEvent.resize(374, 83)
        UpdateEventTypeByEvent.setSizeGripEnabled(False)
        self.gridLayout = QtGui.QGridLayout(UpdateEventTypeByEvent)
        self.gridLayout.setMargin(4)
        self.gridLayout.setSpacing(4)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.label = QtGui.QLabel(UpdateEventTypeByEvent)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(UpdateEventTypeByEvent)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 3, 0, 1, 2)
        spacerItem = QtGui.QSpacerItem(103, 16, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, 2, 0, 1, 1)
        self.cmbEventType = CRBComboBox(UpdateEventTypeByEvent)
        self.cmbEventType.setObjectName(_fromUtf8("cmbEventType"))
        self.gridLayout.addWidget(self.cmbEventType, 0, 1, 1, 1)
        self.lblOrder = QtGui.QLabel(UpdateEventTypeByEvent)
        self.lblOrder.setObjectName(_fromUtf8("lblOrder"))
        self.gridLayout.addWidget(self.lblOrder, 1, 0, 1, 1)
        self.cmbOrder = QtGui.QComboBox(UpdateEventTypeByEvent)
        self.cmbOrder.setEnabled(False)
        self.cmbOrder.setObjectName(_fromUtf8("cmbOrder"))
        self.cmbOrder.addItem(_fromUtf8(""))
        self.cmbOrder.addItem(_fromUtf8(""))
        self.cmbOrder.addItem(_fromUtf8(""))
        self.cmbOrder.addItem(_fromUtf8(""))
        self.cmbOrder.addItem(_fromUtf8(""))
        self.cmbOrder.addItem(_fromUtf8(""))
        self.gridLayout.addWidget(self.cmbOrder, 1, 1, 1, 1)

        self.retranslateUi(UpdateEventTypeByEvent)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), UpdateEventTypeByEvent.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), UpdateEventTypeByEvent.reject)
        QtCore.QMetaObject.connectSlotsByName(UpdateEventTypeByEvent)
        UpdateEventTypeByEvent.setTabOrder(self.cmbEventType, self.buttonBox)

    def retranslateUi(self, UpdateEventTypeByEvent):
        UpdateEventTypeByEvent.setWindowTitle(_translate("UpdateEventTypeByEvent", "Типы события", None))
        self.label.setText(_translate("UpdateEventTypeByEvent", "Тип события", None))
        self.lblOrder.setText(_translate("UpdateEventTypeByEvent", "Порядок", None))
        self.cmbOrder.setItemText(0, _translate("UpdateEventTypeByEvent", "Плановый", None))
        self.cmbOrder.setItemText(1, _translate("UpdateEventTypeByEvent", "Экстренный", None))
        self.cmbOrder.setItemText(2, _translate("UpdateEventTypeByEvent", "Самотёком", None))
        self.cmbOrder.setItemText(3, _translate("UpdateEventTypeByEvent", "Принудительный", None))
        self.cmbOrder.setItemText(4, _translate("UpdateEventTypeByEvent", "Внутренний перевод", None))
        self.cmbOrder.setItemText(5, _translate("UpdateEventTypeByEvent", "Неотложная", None))

from library.crbcombobox import CRBComboBox
