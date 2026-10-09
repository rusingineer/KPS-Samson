# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Projects\Samson\UP_s11\client_test\RefBooks\PostOnAppointment\PostOnAppointmentList.ui'
#
# Created: Wed Aug 26 17:15:21 2026
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
        PostOnAppointmentList.resize(709, 430)
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
        self.tblItems = CTableView(self.tabCode12)
        self.tblItems.setObjectName(_fromUtf8("tblItems"))
        self.verticalLayout_2.addWidget(self.tblItems)
        self.label = QtGui.QLabel(self.tabCode12)
        self.label.setObjectName(_fromUtf8("label"))
        self.verticalLayout_2.addWidget(self.label)
        self.lblTab1Description = QtGui.QLabel(self.tabCode12)
        self.lblTab1Description.setWordWrap(True)
        self.lblTab1Description.setObjectName(_fromUtf8("lblTab1Description"))
        self.verticalLayout_2.addWidget(self.lblTab1Description)
        self.tabWidget.addTab(self.tabCode12, _fromUtf8(""))
        self.tabCode11 = QtGui.QWidget()
        self.tabCode11.setObjectName(_fromUtf8("tabCode11"))
        self.verticalLayout = QtGui.QVBoxLayout(self.tabCode11)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.tblItems_2 = CTableView(self.tabCode11)
        self.tblItems_2.setObjectName(_fromUtf8("tblItems_2"))
        self.verticalLayout.addWidget(self.tblItems_2)
        self.label_2 = QtGui.QLabel(self.tabCode11)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.verticalLayout.addWidget(self.label_2)
        self.lblTab2Description = QtGui.QLabel(self.tabCode11)
        self.lblTab2Description.setWordWrap(True)
        self.lblTab2Description.setObjectName(_fromUtf8("lblTab2Description"))
        self.verticalLayout.addWidget(self.lblTab2Description)
        self.tabWidget.addTab(self.tabCode11, _fromUtf8(""))
        self.tabCode13 = QtGui.QWidget()
        self.tabCode13.setObjectName(_fromUtf8("tabCode13"))
        self.verticalLayout_3 = QtGui.QVBoxLayout(self.tabCode13)
        self.verticalLayout_3.setObjectName(_fromUtf8("verticalLayout_3"))
        self.tblItems_3 = CTableView(self.tabCode13)
        self.tblItems_3.setObjectName(_fromUtf8("tblItems_3"))
        self.verticalLayout_3.addWidget(self.tblItems_3)
        self.label_3 = QtGui.QLabel(self.tabCode13)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.verticalLayout_3.addWidget(self.label_3)
        self.lblTab3Description = QtGui.QLabel(self.tabCode13)
        self.lblTab3Description.setObjectName(_fromUtf8("lblTab3Description"))
        self.verticalLayout_3.addWidget(self.lblTab3Description)
        self.tabWidget.addTab(self.tabCode13, _fromUtf8(""))
        self.tabCode14 = QtGui.QWidget()
        self.tabCode14.setObjectName(_fromUtf8("tabCode14"))
        self.verticalLayout_4 = QtGui.QVBoxLayout(self.tabCode14)
        self.verticalLayout_4.setObjectName(_fromUtf8("verticalLayout_4"))
        self.tblItems_4 = CTableView(self.tabCode14)
        self.tblItems_4.setObjectName(_fromUtf8("tblItems_4"))
        self.verticalLayout_4.addWidget(self.tblItems_4)
        self.label_4 = QtGui.QLabel(self.tabCode14)
        self.label_4.setObjectName(_fromUtf8("label_4"))
        self.verticalLayout_4.addWidget(self.label_4)
        self.lblTab4Description = QtGui.QLabel(self.tabCode14)
        self.lblTab4Description.setWordWrap(True)
        self.lblTab4Description.setObjectName(_fromUtf8("lblTab4Description"))
        self.verticalLayout_4.addWidget(self.lblTab4Description)
        self.tabWidget.addTab(self.tabCode14, _fromUtf8(""))
        self.tabCode15 = QtGui.QWidget()
        self.tabCode15.setObjectName(_fromUtf8("tabCode15"))
        self.verticalLayout_5 = QtGui.QVBoxLayout(self.tabCode15)
        self.verticalLayout_5.setObjectName(_fromUtf8("verticalLayout_5"))
        self.tblItems_5 = CTableView(self.tabCode15)
        self.tblItems_5.setObjectName(_fromUtf8("tblItems_5"))
        self.verticalLayout_5.addWidget(self.tblItems_5)
        self.label_5 = QtGui.QLabel(self.tabCode15)
        self.label_5.setObjectName(_fromUtf8("label_5"))
        self.verticalLayout_5.addWidget(self.label_5)
        self.lblTab5Description = QtGui.QLabel(self.tabCode15)
        self.lblTab5Description.setObjectName(_fromUtf8("lblTab5Description"))
        self.verticalLayout_5.addWidget(self.lblTab5Description)
        self.tabWidget.addTab(self.tabCode15, _fromUtf8(""))
        self.gridLayout.addWidget(self.tabWidget, 0, 0, 1, 1)

        self.retranslateUi(PostOnAppointmentList)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), PostOnAppointmentList.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), PostOnAppointmentList.reject)
        QtCore.QMetaObject.connectSlotsByName(PostOnAppointmentList)
        PostOnAppointmentList.setTabOrder(self.tblItems, self.buttonBox)

    def retranslateUi(self, PostOnAppointmentList):
        PostOnAppointmentList.setWindowTitle(_translate("PostOnAppointmentList", "Dialog", None))
        self.label.setText(_translate("PostOnAppointmentList", "Всего", None))
        self.lblTab1Description.setText(_translate("PostOnAppointmentList", "Должности, анализируемые при передаче сведений о врачах и расписании на ЕПГУ. Если указанная должность отсутствует в данном списке, информация на ЕПГУ не будет выведена", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabCode12), _translate("PostOnAppointmentList", "Должность", None))
        self.label_2.setText(_translate("PostOnAppointmentList", "Всего", None))
        self.lblTab2Description.setText(_translate("PostOnAppointmentList", "Cпециальности которым разрешена неоднократная запись", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabCode11), _translate("PostOnAppointmentList", "Специальность ср. мед. перс.", None))
        self.label_3.setText(_translate("PostOnAppointmentList", "Всего", None))
        self.lblTab3Description.setText(_translate("PostOnAppointmentList", "Перечень должностей к которым применяется основная логика записи", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabCode13), _translate("PostOnAppointmentList", "Основные должности", None))
        self.label_4.setText(_translate("PostOnAppointmentList", "Всего", None))
        self.lblTab4Description.setText(_translate("PostOnAppointmentList", "Перечень должностей, к которым применяется только межкабинетная запись (не предусматривается запись через другие источники)", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabCode14), _translate("PostOnAppointmentList", "Должности для МКЗ", None))
        self.label_5.setText(_translate("PostOnAppointmentList", "Всего", None))
        self.lblTab5Description.setText(_translate("PostOnAppointmentList", "Перечень должностей, к которым применяется контроль резервирования НКТ талонов для ТМК-записи", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabCode15), _translate("PostOnAppointmentList", "Должности для ТМК", None))

from library.TableView import CTableView
