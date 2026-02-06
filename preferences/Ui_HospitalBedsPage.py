# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\projects\Samson\UP_s11\client\preferences\HospitalBedsPage.ui'
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
        HospitalBedsPage.resize(913, 487)
        self.gridLayout_2 = QtGui.QGridLayout(HospitalBedsPage)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.tabWidget = QtGui.QTabWidget(HospitalBedsPage)
        self.tabWidget.setObjectName(_fromUtf8("tabWidget"))
        self.tab = QtGui.QWidget()
        self.tab.setObjectName(_fromUtf8("tab"))
        self.gridLayout = QtGui.QGridLayout(self.tab)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.grpTabWidgets = QtGui.QGroupBox(self.tab)
        self.grpTabWidgets.setAlignment(QtCore.Qt.AlignCenter)
        self.grpTabWidgets.setObjectName(_fromUtf8("grpTabWidgets"))
        self.gridLayout_3 = QtGui.QGridLayout(self.grpTabWidgets)
        self.gridLayout_3.setMargin(2)
        self.gridLayout_3.setSpacing(2)
        self.gridLayout_3.setObjectName(_fromUtf8("gridLayout_3"))
        self.chkTabReadyToLeave = QtGui.QCheckBox(self.grpTabWidgets)
        self.chkTabReadyToLeave.setChecked(True)
        self.chkTabReadyToLeave.setObjectName(_fromUtf8("chkTabReadyToLeave"))
        self.gridLayout_3.addWidget(self.chkTabReadyToLeave, 6, 1, 1, 1)
        self.chkTabPresence = QtGui.QCheckBox(self.grpTabWidgets)
        self.chkTabPresence.setChecked(True)
        self.chkTabPresence.setObjectName(_fromUtf8("chkTabPresence"))
        self.gridLayout_3.addWidget(self.chkTabPresence, 3, 1, 1, 1)
        self.chkTabEmergency = QtGui.QCheckBox(self.grpTabWidgets)
        self.chkTabEmergency.setChecked(True)
        self.chkTabEmergency.setObjectName(_fromUtf8("chkTabEmergency"))
        self.gridLayout_3.addWidget(self.chkTabEmergency, 7, 1, 1, 1)
        self.chkTabDeath = QtGui.QCheckBox(self.grpTabWidgets)
        self.chkTabDeath.setChecked(True)
        self.chkTabDeath.setObjectName(_fromUtf8("chkTabDeath"))
        self.gridLayout_3.addWidget(self.chkTabDeath, 8, 1, 1, 1)
        self.chkTabTransfer = QtGui.QCheckBox(self.grpTabWidgets)
        self.chkTabTransfer.setChecked(True)
        self.chkTabTransfer.setObjectName(_fromUtf8("chkTabTransfer"))
        self.gridLayout_3.addWidget(self.chkTabTransfer, 5, 1, 1, 1)
        self.chkTabLeaved = QtGui.QCheckBox(self.grpTabWidgets)
        self.chkTabLeaved.setChecked(True)
        self.chkTabLeaved.setObjectName(_fromUtf8("chkTabLeaved"))
        self.gridLayout_3.addWidget(self.chkTabLeaved, 6, 0, 1, 1)
        self.chkTabFund = QtGui.QCheckBox(self.grpTabWidgets)
        self.chkTabFund.setChecked(True)
        self.chkTabFund.setObjectName(_fromUtf8("chkTabFund"))
        self.gridLayout_3.addWidget(self.chkTabFund, 3, 0, 1, 1)
        self.chkTabReceived = QtGui.QCheckBox(self.grpTabWidgets)
        self.chkTabReceived.setChecked(True)
        self.chkTabReceived.setObjectName(_fromUtf8("chkTabReceived"))
        self.gridLayout_3.addWidget(self.chkTabReceived, 5, 0, 1, 1)
        self.chkTabRenunciation = QtGui.QCheckBox(self.grpTabWidgets)
        self.chkTabRenunciation.setChecked(True)
        self.chkTabRenunciation.setObjectName(_fromUtf8("chkTabRenunciation"))
        self.gridLayout_3.addWidget(self.chkTabRenunciation, 8, 0, 1, 1)
        self.chkTabQueue = QtGui.QCheckBox(self.grpTabWidgets)
        self.chkTabQueue.setChecked(True)
        self.chkTabQueue.setObjectName(_fromUtf8("chkTabQueue"))
        self.gridLayout_3.addWidget(self.chkTabQueue, 7, 0, 1, 1)
        self.chkTabReanimation = QtGui.QCheckBox(self.grpTabWidgets)
        self.chkTabReanimation.setEnabled(True)
        self.chkTabReanimation.setObjectName(_fromUtf8("chkTabReanimation"))
        self.gridLayout_3.addWidget(self.chkTabReanimation, 9, 0, 1, 1)
        self.gridLayout.addWidget(self.grpTabWidgets, 0, 0, 1, 1)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, 1, 0, 1, 1)
        self.tabWidget.addTab(self.tab, _fromUtf8(""))
        self.tab_2 = QtGui.QWidget()
        self.tab_2.setObjectName(_fromUtf8("tab_2"))
        self.gridLayout_4 = QtGui.QGridLayout(self.tab_2)
        self.gridLayout_4.setObjectName(_fromUtf8("gridLayout_4"))
        self.tabWidget.addTab(self.tab_2, _fromUtf8(""))
        self.gridLayout_2.addWidget(self.tabWidget, 0, 0, 1, 1)

        self.retranslateUi(HospitalBedsPage)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(HospitalBedsPage)
        HospitalBedsPage.setTabOrder(self.chkTabFund, self.chkTabReceived)
        HospitalBedsPage.setTabOrder(self.chkTabReceived, self.chkTabLeaved)
        HospitalBedsPage.setTabOrder(self.chkTabLeaved, self.chkTabRenunciation)
        HospitalBedsPage.setTabOrder(self.chkTabRenunciation, self.chkTabQueue)

    def retranslateUi(self, HospitalBedsPage):
        HospitalBedsPage.setWindowTitle(_translate("HospitalBedsPage", "Стационарный монитор", None))
        self.grpTabWidgets.setTitle(_translate("HospitalBedsPage", "Визуализация: Вкладки", None))
        self.chkTabReadyToLeave.setText(_translate("HospitalBedsPage", "Вкладка Готовы к выбытию", None))
        self.chkTabPresence.setText(_translate("HospitalBedsPage", "Вкладка Присутствуют", None))
        self.chkTabEmergency.setText(_translate("HospitalBedsPage", "Вкладка СМП", None))
        self.chkTabDeath.setText(_translate("HospitalBedsPage", "Вкладка Умерло", None))
        self.chkTabTransfer.setText(_translate("HospitalBedsPage", "Вкладка Переведены (в отделение)", None))
        self.chkTabLeaved.setText(_translate("HospitalBedsPage", "Вкладка Выбыли", None))
        self.chkTabFund.setText(_translate("HospitalBedsPage", "Вкладка Коечный фонд", None))
        self.chkTabReceived.setText(_translate("HospitalBedsPage", "Вкладка Поступили", None))
        self.chkTabRenunciation.setText(_translate("HospitalBedsPage", "Вкладка Отказ от госпитализации", None))
        self.chkTabQueue.setText(_translate("HospitalBedsPage", "Вкладка В очереди", None))
        self.chkTabReanimation.setText(_translate("HospitalBedsPage", "Вкладка Реанимация", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _translate("HospitalBedsPage", "Настройки визуализации вкладок", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _translate("HospitalBedsPage", "Настройки видимости структуры организации", None))

