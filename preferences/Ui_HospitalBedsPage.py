# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\samson\preferences\HospitalBedsPage.ui'
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

class Ui_HospitalBedsPage(object):
    def setupUi(self, HospitalBedsPage):
        HospitalBedsPage.setObjectName(_fromUtf8("HospitalBedsPage"))
        HospitalBedsPage.resize(543, 148)
        self.gridLayout = QtGui.QGridLayout(HospitalBedsPage)
        self.gridLayout.setMargin(4)
        self.gridLayout.setSpacing(4)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, 12, 0, 1, 1)
        self.grpTabWidgets = QtGui.QGroupBox(HospitalBedsPage)
        self.grpTabWidgets.setAlignment(QtCore.Qt.AlignCenter)
        self.grpTabWidgets.setObjectName(_fromUtf8("grpTabWidgets"))
        self.gridLayout_3 = QtGui.QGridLayout(self.grpTabWidgets)
        self.gridLayout_3.setMargin(2)
        self.gridLayout_3.setSpacing(2)
        self.gridLayout_3.setObjectName(_fromUtf8("gridLayout_3"))
        self.chkTabPresence = QtGui.QCheckBox(self.grpTabWidgets)
        self.chkTabPresence.setChecked(True)
        self.chkTabPresence.setObjectName(_fromUtf8("chkTabPresence"))
        self.gridLayout_3.addWidget(self.chkTabPresence, 3, 1, 1, 1)
        self.chkTabReadyToLeave = QtGui.QCheckBox(self.grpTabWidgets)
        self.chkTabReadyToLeave.setChecked(True)
        self.chkTabReadyToLeave.setObjectName(_fromUtf8("chkTabReadyToLeave"))
        self.gridLayout_3.addWidget(self.chkTabReadyToLeave, 6, 1, 1, 1)
        self.chkTabDeath = QtGui.QCheckBox(self.grpTabWidgets)
        self.chkTabDeath.setChecked(True)
        self.chkTabDeath.setObjectName(_fromUtf8("chkTabDeath"))
        self.gridLayout_3.addWidget(self.chkTabDeath, 8, 1, 1, 1)
        self.chkTabEmergency = QtGui.QCheckBox(self.grpTabWidgets)
        self.chkTabEmergency.setChecked(True)
        self.chkTabEmergency.setObjectName(_fromUtf8("chkTabEmergency"))
        self.gridLayout_3.addWidget(self.chkTabEmergency, 7, 1, 1, 1)
        self.chkTabTransfer = QtGui.QCheckBox(self.grpTabWidgets)
        self.chkTabTransfer.setChecked(True)
        self.chkTabTransfer.setObjectName(_fromUtf8("chkTabTransfer"))
        self.gridLayout_3.addWidget(self.chkTabTransfer, 5, 1, 1, 1)
        self.chkTabQueue = QtGui.QCheckBox(self.grpTabWidgets)
        self.chkTabQueue.setChecked(True)
        self.chkTabQueue.setObjectName(_fromUtf8("chkTabQueue"))
        self.gridLayout_3.addWidget(self.chkTabQueue, 7, 0, 1, 1)
        self.chkTabRenunciation = QtGui.QCheckBox(self.grpTabWidgets)
        self.chkTabRenunciation.setChecked(True)
        self.chkTabRenunciation.setObjectName(_fromUtf8("chkTabRenunciation"))
        self.gridLayout_3.addWidget(self.chkTabRenunciation, 8, 0, 1, 1)
        self.chkTabReceived = QtGui.QCheckBox(self.grpTabWidgets)
        self.chkTabReceived.setChecked(True)
        self.chkTabReceived.setObjectName(_fromUtf8("chkTabReceived"))
        self.gridLayout_3.addWidget(self.chkTabReceived, 5, 0, 1, 1)
        self.chkTabLeaved = QtGui.QCheckBox(self.grpTabWidgets)
        self.chkTabLeaved.setChecked(True)
        self.chkTabLeaved.setObjectName(_fromUtf8("chkTabLeaved"))
        self.gridLayout_3.addWidget(self.chkTabLeaved, 6, 0, 1, 1)
        self.chkTabFund = QtGui.QCheckBox(self.grpTabWidgets)
        self.chkTabFund.setChecked(True)
        self.chkTabFund.setObjectName(_fromUtf8("chkTabFund"))
        self.gridLayout_3.addWidget(self.chkTabFund, 3, 0, 1, 1)
        self.chkTabReanimation = QtGui.QCheckBox(self.grpTabWidgets)
        self.chkTabReanimation.setEnabled(True)
        self.chkTabReanimation.setObjectName(_fromUtf8("chkTabReanimation"))
        self.gridLayout_3.addWidget(self.chkTabReanimation, 9, 0, 1, 1)
        self.gridLayout.addWidget(self.grpTabWidgets, 11, 0, 1, 2)

        self.retranslateUi(HospitalBedsPage)
        QtCore.QMetaObject.connectSlotsByName(HospitalBedsPage)
        HospitalBedsPage.setTabOrder(self.chkTabFund, self.chkTabReceived)
        HospitalBedsPage.setTabOrder(self.chkTabReceived, self.chkTabLeaved)
        HospitalBedsPage.setTabOrder(self.chkTabLeaved, self.chkTabRenunciation)
        HospitalBedsPage.setTabOrder(self.chkTabRenunciation, self.chkTabQueue)

    def retranslateUi(self, HospitalBedsPage):
        HospitalBedsPage.setWindowTitle(_translate("HospitalBedsPage", "Стационарный монитор", None))
        self.grpTabWidgets.setTitle(_translate("HospitalBedsPage", "Визуализация: Вкладки", None))
        self.chkTabPresence.setText(_translate("HospitalBedsPage", "Вкладка Присутствуют", None))
        self.chkTabReadyToLeave.setText(_translate("HospitalBedsPage", "Вкладка Готовы к выбытию", None))
        self.chkTabDeath.setText(_translate("HospitalBedsPage", "Вкладка Умерло", None))
        self.chkTabEmergency.setText(_translate("HospitalBedsPage", "Вкладка СМП", None))
        self.chkTabTransfer.setText(_translate("HospitalBedsPage", "Вкладка Переведены (в отделение)", None))
        self.chkTabQueue.setText(_translate("HospitalBedsPage", "Вкладка В очереди", None))
        self.chkTabRenunciation.setText(_translate("HospitalBedsPage", "Вкладка Отказ от госпитализации", None))
        self.chkTabReceived.setText(_translate("HospitalBedsPage", "Вкладка Поступили", None))
        self.chkTabLeaved.setText(_translate("HospitalBedsPage", "Вкладка Выбыли", None))
        self.chkTabFund.setText(_translate("HospitalBedsPage", "Вкладка Коечный фонд", None))
        self.chkTabReanimation.setText(_translate("HospitalBedsPage", "Вкладка Реанимация", None))

