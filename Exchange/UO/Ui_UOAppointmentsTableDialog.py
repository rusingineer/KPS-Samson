# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\Samson\client_test\Exchange\UO\UOAppointmentsTableDialog.ui'
#
# Created: Tue Oct 22 17:33:03 2024
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

class Ui_UOAppointmentsTableDialog(object):
    def setupUi(self, UOAppointmentsTableDialog):
        UOAppointmentsTableDialog.setObjectName(_fromUtf8("UOAppointmentsTableDialog"))
        UOAppointmentsTableDialog.resize(716, 538)
        self.verticalLayout = QtGui.QVBoxLayout(UOAppointmentsTableDialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.label = QtGui.QLabel(UOAppointmentsTableDialog)
        self.label.setObjectName(_fromUtf8("label"))
        self.verticalLayout.addWidget(self.label)
        self.lvDoctors = QtGui.QListView(UOAppointmentsTableDialog)
        self.lvDoctors.setObjectName(_fromUtf8("lvDoctors"))
        self.verticalLayout.addWidget(self.lvDoctors)
        self.label_2 = QtGui.QLabel(UOAppointmentsTableDialog)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.verticalLayout.addWidget(self.label_2)
        self.tblAppointments = QtGui.QTableView(UOAppointmentsTableDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(3)
        sizePolicy.setHeightForWidth(self.tblAppointments.sizePolicy().hasHeightForWidth())
        self.tblAppointments.setSizePolicy(sizePolicy)
        self.tblAppointments.setObjectName(_fromUtf8("tblAppointments"))
        self.verticalLayout.addWidget(self.tblAppointments)
        self.lblStatus = QtGui.QLabel(UOAppointmentsTableDialog)
        self.lblStatus.setObjectName(_fromUtf8("lblStatus"))
        self.verticalLayout.addWidget(self.lblStatus)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.btnRegisterReferral = QtGui.QPushButton(UOAppointmentsTableDialog)
        self.btnRegisterReferral.setObjectName(_fromUtf8("btnRegisterReferral"))
        self.horizontalLayout_2.addWidget(self.btnRegisterReferral)
        self.btnUpdateList = QtGui.QPushButton(UOAppointmentsTableDialog)
        self.btnUpdateList.setObjectName(_fromUtf8("btnUpdateList"))
        self.horizontalLayout_2.addWidget(self.btnUpdateList)
        self.btnSetAppointment = QtGui.QPushButton(UOAppointmentsTableDialog)
        self.btnSetAppointment.setObjectName(_fromUtf8("btnSetAppointment"))
        self.horizontalLayout_2.addWidget(self.btnSetAppointment)
        self.btnClose = QtGui.QPushButton(UOAppointmentsTableDialog)
        self.btnClose.setObjectName(_fromUtf8("btnClose"))
        self.horizontalLayout_2.addWidget(self.btnClose)
        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.retranslateUi(UOAppointmentsTableDialog)
        QtCore.QMetaObject.connectSlotsByName(UOAppointmentsTableDialog)

    def retranslateUi(self, UOAppointmentsTableDialog):
        UOAppointmentsTableDialog.setWindowTitle(_translate("UOAppointmentsTableDialog", "Сервис Управления потоками пациентов (очередями)", None))
        self.label.setText(_translate("UOAppointmentsTableDialog", "Врач:", None))
        self.label_2.setText(_translate("UOAppointmentsTableDialog", "Доступные талоны:", None))
        self.lblStatus.setText(_translate("UOAppointmentsTableDialog", "Загрузка списка талонов...", None))
        self.btnRegisterReferral.setText(_translate("UOAppointmentsTableDialog", "Самостоятельная запись пациента через ЕПГУ", None))
        self.btnUpdateList.setText(_translate("UOAppointmentsTableDialog", "Обновить", None))
        self.btnSetAppointment.setText(_translate("UOAppointmentsTableDialog", "Записать", None))
        self.btnClose.setText(_translate("UOAppointmentsTableDialog", "Закрыть", None))

