# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Samson\UP_s11\client_test\RefBooks\PostOnAppointment\PostOnAppointmentList.ui'
#
# Created: Mon Apr 08 14:39:32 2024
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

class Ui_PostOnAppointmentList(object):
    def setupUi(self, PostOnAppointmentList):
        PostOnAppointmentList.setObjectName(_fromUtf8("PostOnAppointmentList"))
        PostOnAppointmentList.resize(582, 335)
        PostOnAppointmentList.setSizeGripEnabled(True)
        self.gridLayout = QtGui.QGridLayout(PostOnAppointmentList)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.buttonBox = QtGui.QDialogButtonBox(PostOnAppointmentList)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Close)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 1, 0, 1, 1)
        self.tabWidget = QtGui.QTabWidget(PostOnAppointmentList)
        self.tabWidget.setObjectName(_fromUtf8("tabWidget"))
        self.tabCode12 = QtGui.QWidget()
        self.tabCode12.setObjectName(_fromUtf8("tabCode12"))
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.tabCode12)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.lblDescription = QtGui.QLabel(self.tabCode12)
        self.lblDescription.setObjectName(_fromUtf8("lblDescription"))
        self.verticalLayout_2.addWidget(self.lblDescription)
        self.tblItems = CTableView(self.tabCode12)
        self.tblItems.setObjectName(_fromUtf8("tblItems"))
        self.verticalLayout_2.addWidget(self.tblItems)
        self.label = QtGui.QLabel(self.tabCode12)
        self.label.setObjectName(_fromUtf8("label"))
        self.verticalLayout_2.addWidget(self.label)
        self.tabWidget.addTab(self.tabCode12, _fromUtf8(""))
        self.tabCode11 = QtGui.QWidget()
        self.tabCode11.setObjectName(_fromUtf8("tabCode11"))
        self.verticalLayout = QtGui.QVBoxLayout(self.tabCode11)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.lblDescription_2 = QtGui.QLabel(self.tabCode11)
        self.lblDescription_2.setObjectName(_fromUtf8("lblDescription_2"))
        self.verticalLayout.addWidget(self.lblDescription_2)
        self.tblItems_2 = CTableView(self.tabCode11)
        self.tblItems_2.setObjectName(_fromUtf8("tblItems_2"))
        self.verticalLayout.addWidget(self.tblItems_2)
        self.label_2 = QtGui.QLabel(self.tabCode11)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.verticalLayout.addWidget(self.label_2)
        self.tabWidget.addTab(self.tabCode11, _fromUtf8(""))
        self.gridLayout.addWidget(self.tabWidget, 0, 0, 1, 1)

        self.retranslateUi(PostOnAppointmentList)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), PostOnAppointmentList.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), PostOnAppointmentList.reject)
        QtCore.QMetaObject.connectSlotsByName(PostOnAppointmentList)
        PostOnAppointmentList.setTabOrder(self.tblItems, self.buttonBox)

    def retranslateUi(self, PostOnAppointmentList):
        PostOnAppointmentList.setWindowTitle(_translate("PostOnAppointmentList", "Dialog", None))
        self.lblDescription.setText(_translate("PostOnAppointmentList", "Мини описание", None))
        self.label.setText(_translate("PostOnAppointmentList", "Всего", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabCode12), _translate("PostOnAppointmentList", "Должность", None))
        self.lblDescription_2.setText(_translate("PostOnAppointmentList", "Мини описание", None))
        self.label_2.setText(_translate("PostOnAppointmentList", "Всего", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabCode11), _translate("PostOnAppointmentList", "Специальность", None))

from library.TableView import CTableView
