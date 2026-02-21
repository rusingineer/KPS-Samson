# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\samson\Surveillance\SurveillanceRemoveAcute.ui'
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

class Ui_SurveillanceRemoveAcute(object):
    def setupUi(self, SurveillanceRemoveAcute):
        SurveillanceRemoveAcute.setObjectName(_fromUtf8("SurveillanceRemoveAcute"))
        SurveillanceRemoveAcute.resize(754, 282)
        self.gridLayout = QtGui.QGridLayout(SurveillanceRemoveAcute)
        self.gridLayout.setMargin(4)
        self.gridLayout.setSpacing(4)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, 4, 0, 1, 3)
        self.lblDiagnosis = QtGui.QLabel(SurveillanceRemoveAcute)
        self.lblDiagnosis.setObjectName(_fromUtf8("lblDiagnosis"))
        self.gridLayout.addWidget(self.lblDiagnosis, 0, 0, 1, 3)
        self.buttonBox = QtGui.QDialogButtonBox(SurveillanceRemoveAcute)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 5, 0, 1, 3)
        self.tblDiagnosis = CSurveillanceClientDiagnosisTableView(SurveillanceRemoveAcute)
        self.tblDiagnosis.setObjectName(_fromUtf8("tblDiagnosis"))
        self.gridLayout.addWidget(self.tblDiagnosis, 1, 0, 1, 3)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.label = QtGui.QLabel(SurveillanceRemoveAcute)
        self.label.setObjectName(_fromUtf8("label"))
        self.horizontalLayout.addWidget(self.label)
        self.cmbDispanser = CRBComboBox(SurveillanceRemoveAcute)
        self.cmbDispanser.setObjectName(_fromUtf8("cmbDispanser"))
        self.horizontalLayout.addWidget(self.cmbDispanser)
        self.gridLayout.addLayout(self.horizontalLayout, 2, 0, 1, 2)

        self.retranslateUi(SurveillanceRemoveAcute)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), SurveillanceRemoveAcute.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), SurveillanceRemoveAcute.reject)
        QtCore.QMetaObject.connectSlotsByName(SurveillanceRemoveAcute)

    def retranslateUi(self, SurveillanceRemoveAcute):
        SurveillanceRemoveAcute.setWindowTitle(_translate("SurveillanceRemoveAcute", "Сервис ретроспективного снятия с ДН по острым заболеваниям и факторам", None))
        self.lblDiagnosis.setText(_translate("SurveillanceRemoveAcute", "Отметьте диагнозы для снятия с ДН:", None))
        self.label.setText(_translate("SurveillanceRemoveAcute", "Укажите текущий статус ДН:", None))

from Surveillance.SurveillanceClientsTableView import CSurveillanceClientDiagnosisTableView
from library.crbcombobox import CRBComboBox
