# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\Samson\UP_s11\client\library\IdentificationComboBoxExPopup.ui'
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

class Ui_IdentificationComboBoxExPopup(object):
    def setupUi(self, IdentificationComboBoxExPopup):
        IdentificationComboBoxExPopup.setObjectName(_fromUtf8("IdentificationComboBoxExPopup"))
        IdentificationComboBoxExPopup.resize(584, 608)
        self.verticalLayout_2 = QtGui.QVBoxLayout(IdentificationComboBoxExPopup)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setSizeConstraint(QtGui.QLayout.SetMaximumSize)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.lblCode = QtGui.QLabel(IdentificationComboBoxExPopup)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblCode.sizePolicy().hasHeightForWidth())
        self.lblCode.setSizePolicy(sizePolicy)
        self.lblCode.setObjectName(_fromUtf8("lblCode"))
        self.horizontalLayout.addWidget(self.lblCode)
        self.leCode = QtGui.QLineEdit(IdentificationComboBoxExPopup)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.leCode.sizePolicy().hasHeightForWidth())
        self.leCode.setSizePolicy(sizePolicy)
        self.leCode.setObjectName(_fromUtf8("leCode"))
        self.horizontalLayout.addWidget(self.leCode)
        self.label_title = QtGui.QLabel(IdentificationComboBoxExPopup)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_title.sizePolicy().hasHeightForWidth())
        self.label_title.setSizePolicy(sizePolicy)
        self.label_title.setObjectName(_fromUtf8("label_title"))
        self.horizontalLayout.addWidget(self.label_title)
        self.edit_title = QtGui.QLineEdit(IdentificationComboBoxExPopup)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.edit_title.sizePolicy().hasHeightForWidth())
        self.edit_title.setSizePolicy(sizePolicy)
        self.edit_title.setAutoFillBackground(False)
        self.edit_title.setMaxLength(16777215)
        self.edit_title.setObjectName(_fromUtf8("edit_title"))
        self.horizontalLayout.addWidget(self.edit_title)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.tblSpr = CTableView(IdentificationComboBoxExPopup)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tblSpr.sizePolicy().hasHeightForWidth())
        self.tblSpr.setSizePolicy(sizePolicy)
        self.tblSpr.setObjectName(_fromUtf8("tblSpr"))
        self.verticalLayout.addWidget(self.tblSpr)
        self.buttonBox = QtGui.QDialogButtonBox(IdentificationComboBoxExPopup)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.buttonBox.sizePolicy().hasHeightForWidth())
        self.buttonBox.setSizePolicy(sizePolicy)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Apply|QtGui.QDialogButtonBox.Reset)
        self.buttonBox.setCenterButtons(False)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.verticalLayout.addWidget(self.buttonBox)
        self.verticalLayout_2.addLayout(self.verticalLayout)
        self.label_title.setBuddy(self.edit_title)

        self.retranslateUi(IdentificationComboBoxExPopup)
        QtCore.QMetaObject.connectSlotsByName(IdentificationComboBoxExPopup)

    def retranslateUi(self, IdentificationComboBoxExPopup):
        IdentificationComboBoxExPopup.setWindowTitle(_translate("IdentificationComboBoxExPopup", "Form", None))
        self.lblCode.setText(_translate("IdentificationComboBoxExPopup", "Код", None))
        self.label_title.setText(_translate("IdentificationComboBoxExPopup", "Наименование", None))

from library.TableView import CTableView
