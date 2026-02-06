# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\projects\Samson\UP_s11\client\Surveillance\GroupChangeDispanserPerson.ui'
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

class Ui_ChangeDispanserPerson(object):
    def setupUi(self, ChangeDispanserPerson):
        ChangeDispanserPerson.setObjectName(_fromUtf8("ChangeDispanserPerson"))
        ChangeDispanserPerson.resize(382, 142)
        self.gridLayout = QtGui.QGridLayout(ChangeDispanserPerson)
        self.gridLayout.setMargin(4)
        self.gridLayout.setSpacing(4)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, 6, 0, 1, 1)
        self.lblPerson = QtGui.QLabel(ChangeDispanserPerson)
        self.lblPerson.setObjectName(_fromUtf8("lblPerson"))
        self.gridLayout.addWidget(self.lblPerson, 0, 0, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(ChangeDispanserPerson)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 7, 1, 1, 2)
        self.lblMKB = QtGui.QLabel(ChangeDispanserPerson)
        self.lblMKB.setObjectName(_fromUtf8("lblMKB"))
        self.gridLayout.addWidget(self.lblMKB, 1, 0, 1, 1)
        self.cmbPerson = CPersonComboBoxEx(ChangeDispanserPerson)
        self.cmbPerson.setObjectName(_fromUtf8("cmbPerson"))
        self.gridLayout.addWidget(self.cmbPerson, 0, 1, 1, 2)
        self.cmbMKB = CMultivalueComboBox(ChangeDispanserPerson)
        self.cmbMKB.setObjectName(_fromUtf8("cmbMKB"))
        self.gridLayout.addWidget(self.cmbMKB, 1, 1, 1, 2)
        self.lblClientCount = QtGui.QLabel(ChangeDispanserPerson)
        self.lblClientCount.setObjectName(_fromUtf8("lblClientCount"))
        self.gridLayout.addWidget(self.lblClientCount, 2, 0, 1, 3)
        self.lblMKBList = QtGui.QLabel(ChangeDispanserPerson)
        self.lblMKBList.setObjectName(_fromUtf8("lblMKBList"))
        self.gridLayout.addWidget(self.lblMKBList, 3, 0, 1, 3)
        self.lblCharacterList = QtGui.QLabel(ChangeDispanserPerson)
        self.lblCharacterList.setObjectName(_fromUtf8("lblCharacterList"))
        self.gridLayout.addWidget(self.lblCharacterList, 4, 0, 1, 3)

        self.retranslateUi(ChangeDispanserPerson)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), ChangeDispanserPerson.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), ChangeDispanserPerson.reject)
        QtCore.QMetaObject.connectSlotsByName(ChangeDispanserPerson)

    def retranslateUi(self, ChangeDispanserPerson):
        ChangeDispanserPerson.setWindowTitle(_translate("ChangeDispanserPerson", "Сервис массового изменение врача диспансерного наблюдения", None))
        self.lblPerson.setText(_translate("ChangeDispanserPerson", "Врач по ДН", None))
        self.lblMKB.setText(_translate("ChangeDispanserPerson", "МКБ", None))
        self.lblClientCount.setText(_translate("ChangeDispanserPerson", "Кол-во пациентов, у которых будет изменен врач по ДН:", None))
        self.lblMKBList.setText(_translate("ChangeDispanserPerson", "Диапазон диагнозов:", None))
        self.lblCharacterList.setText(_translate("ChangeDispanserPerson", "Характеры заболеваний:", None))

from Orgs.PersonComboBoxEx import CPersonComboBoxEx
from library.MultivalueComboBox import CMultivalueComboBox
