# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\projects\Samson\UP_s11\client\preferences\InformerPage.ui'
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

class Ui_InformerPage(object):
    def setupUi(self, InformerPage):
        InformerPage.setObjectName(_fromUtf8("InformerPage"))
        InformerPage.resize(543, 256)
        self.gridLayout = QtGui.QGridLayout(InformerPage)
        self.gridLayout.setMargin(4)
        self.gridLayout.setSpacing(4)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.chkInformerShowPersonSNILS = QtGui.QCheckBox(InformerPage)
        self.chkInformerShowPersonSNILS.setObjectName(_fromUtf8("chkInformerShowPersonSNILS"))
        self.gridLayout.addWidget(self.chkInformerShowPersonSNILS, 12, 0, 1, 1)
        self.chkInformerShowByUserArea = QtGui.QCheckBox(InformerPage)
        self.chkInformerShowByUserArea.setObjectName(_fromUtf8("chkInformerShowByUserArea"))
        self.gridLayout.addWidget(self.chkInformerShowByUserArea, 14, 0, 1, 1)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, 17, 0, 1, 1)
        self.chkInformerShowNoSNILS = QtGui.QCheckBox(InformerPage)
        self.chkInformerShowNoSNILS.setObjectName(_fromUtf8("chkInformerShowNoSNILS"))
        self.gridLayout.addWidget(self.chkInformerShowNoSNILS, 13, 0, 1, 1)
        self.chkInformerShowByUserNotArea = QtGui.QCheckBox(InformerPage)
        self.chkInformerShowByUserNotArea.setObjectName(_fromUtf8("chkInformerShowByUserNotArea"))
        self.gridLayout.addWidget(self.chkInformerShowByUserNotArea, 15, 0, 1, 1)
        self.chkDisableCheckDB = QtGui.QCheckBox(InformerPage)
        self.chkDisableCheckDB.setObjectName(_fromUtf8("chkDisableCheckDB"))
        self.gridLayout.addWidget(self.chkDisableCheckDB, 16, 0, 1, 1)

        self.retranslateUi(InformerPage)
        QtCore.QMetaObject.connectSlotsByName(InformerPage)
        InformerPage.setTabOrder(self.chkInformerShowPersonSNILS, self.chkInformerShowNoSNILS)

    def retranslateUi(self, InformerPage):
        InformerPage.setWindowTitle(_translate("InformerPage", "Информатор", None))
        self.chkInformerShowPersonSNILS.setText(_translate("InformerPage", "Фильтровать уведомления по СНИЛСу пользователя", None))
        self.chkInformerShowByUserArea.setText(_translate("InformerPage", "Фильтровать уведомления по участку пользователя", None))
        self.chkInformerShowNoSNILS.setText(_translate("InformerPage", "Показывать уведомления без СНИЛС", None))
        self.chkInformerShowByUserNotArea.setText(_translate("InformerPage", "Фильтровать уведомления по пациентам без участка", None))
        self.chkDisableCheckDB.setText(_translate("InformerPage", "Отключить восстановление связи с БД", None))

