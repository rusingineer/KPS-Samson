# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\projects\Samson\UP_s11\client\Registry\DistantMonitoringWindow.ui'
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

class Ui_DistantMonitoringWindow(object):
    def setupUi(self, DistantMonitoringWindow):
        DistantMonitoringWindow.setObjectName(_fromUtf8("DistantMonitoringWindow"))
        DistantMonitoringWindow.resize(1511, 1025)
        self.horizontalLayout = QtGui.QHBoxLayout(DistantMonitoringWindow)
        self.horizontalLayout.setMargin(4)
        self.horizontalLayout.setSpacing(4)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.tabWidget = QtGui.QTabWidget(DistantMonitoringWindow)
        self.tabWidget.setObjectName(_fromUtf8("tabWidget"))
        self.tabEventPage = CDistantMonitoringEventPage()
        self.tabEventPage.setObjectName(_fromUtf8("tabEventPage"))
        self.tabWidget.addTab(self.tabEventPage, _fromUtf8(""))
        self.tabPersonPage = CDistantMonitoringPersonPage()
        self.tabPersonPage.setObjectName(_fromUtf8("tabPersonPage"))
        self.tabWidget.addTab(self.tabPersonPage, _fromUtf8(""))
        self.tabEquipmentPage = CDistantMonitoringEquipmentPage()
        self.tabEquipmentPage.setObjectName(_fromUtf8("tabEquipmentPage"))
        self.tabWidget.addTab(self.tabEquipmentPage, _fromUtf8(""))
        self.horizontalLayout.addWidget(self.tabWidget)

        self.retranslateUi(DistantMonitoringWindow)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(DistantMonitoringWindow)

    def retranslateUi(self, DistantMonitoringWindow):
        DistantMonitoringWindow.setWindowTitle(_translate("DistantMonitoringWindow", "Сервис дистанционного наблюдения", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabEventPage), _translate("DistantMonitoringWindow", "Программы ДН", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabPersonPage), _translate("DistantMonitoringWindow", "Регистрация врача", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabEquipmentPage), _translate("DistantMonitoringWindow", "Регистрация оборудования", None))

from Registry.DistantMonitoringEquipmentPage import CDistantMonitoringEquipmentPage
from Registry.DistantMonitoringEventPage import CDistantMonitoringEventPage
from Registry.DistantMonitoringPersonPage import CDistantMonitoringPersonPage
