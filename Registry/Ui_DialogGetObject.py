# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\projects\Samson\UP_s11\client\Registry\DialogGetObject.ui'
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

class Ui_DialogGetObject(object):
    def setupUi(self, DialogGetObject):
        DialogGetObject.setObjectName(_fromUtf8("DialogGetObject"))
        DialogGetObject.resize(288, 170)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(DialogGetObject.sizePolicy().hasHeightForWidth())
        DialogGetObject.setSizePolicy(sizePolicy)
        DialogGetObject.setMaximumSize(QtCore.QSize(288, 170))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8(":/icons/Icon2.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        DialogGetObject.setWindowIcon(icon)
        self.gridLayout = QtGui.QGridLayout(DialogGetObject)
        self.gridLayout.setMargin(4)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.frame = QtGui.QFrame(DialogGetObject)
        self.frame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtGui.QFrame.Raised)
        self.frame.setObjectName(_fromUtf8("frame"))
        self.gridLayout_2 = QtGui.QGridLayout(self.frame)
        self.gridLayout_2.setContentsMargins(4, 4, 4, -1)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.lblObjectName = QtGui.QLabel(self.frame)
        self.lblObjectName.setObjectName(_fromUtf8("lblObjectName"))
        self.gridLayout_2.addWidget(self.lblObjectName, 0, 0, 1, 1)
        self.edtObjectName = QtGui.QLineEdit(self.frame)
        self.edtObjectName.setReadOnly(True)
        self.edtObjectName.setObjectName(_fromUtf8("edtObjectName"))
        self.gridLayout_2.addWidget(self.edtObjectName, 0, 1, 1, 1)
        self.lblObjectTable = QtGui.QLabel(self.frame)
        self.lblObjectTable.setObjectName(_fromUtf8("lblObjectTable"))
        self.gridLayout_2.addWidget(self.lblObjectTable, 1, 0, 1, 1)
        self.edtObjectTable = QtGui.QLineEdit(self.frame)
        self.edtObjectTable.setReadOnly(True)
        self.edtObjectTable.setObjectName(_fromUtf8("edtObjectTable"))
        self.gridLayout_2.addWidget(self.edtObjectTable, 1, 1, 1, 1)
        self.lblObjectId = QtGui.QLabel(self.frame)
        self.lblObjectId.setObjectName(_fromUtf8("lblObjectId"))
        self.gridLayout_2.addWidget(self.lblObjectId, 2, 0, 1, 1)
        self.edtObjectId = QtGui.QLineEdit(self.frame)
        self.edtObjectId.setReadOnly(True)
        self.edtObjectId.setObjectName(_fromUtf8("edtObjectId"))
        self.gridLayout_2.addWidget(self.edtObjectId, 2, 1, 1, 1)
        self.lblObjectDate = QtGui.QLabel(self.frame)
        self.lblObjectDate.setObjectName(_fromUtf8("lblObjectDate"))
        self.gridLayout_2.addWidget(self.lblObjectDate, 3, 0, 1, 1)
        self.edtObjectDate = QtGui.QLineEdit(self.frame)
        self.edtObjectDate.setReadOnly(True)
        self.edtObjectDate.setObjectName(_fromUtf8("edtObjectDate"))
        self.gridLayout_2.addWidget(self.edtObjectDate, 3, 1, 1, 1)
        self.gridLayout.addWidget(self.frame, 0, 0, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(DialogGetObject)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 1, 0, 1, 1)

        self.retranslateUi(DialogGetObject)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), DialogGetObject.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), DialogGetObject.reject)
        QtCore.QMetaObject.connectSlotsByName(DialogGetObject)

    def retranslateUi(self, DialogGetObject):
        DialogGetObject.setWindowTitle(_translate("DialogGetObject", "Dialog", None))
        self.lblObjectName.setText(_translate("DialogGetObject", "Объект", None))
        self.lblObjectTable.setText(_translate("DialogGetObject", "Таблица", None))
        self.lblObjectId.setText(_translate("DialogGetObject", "Id объекта", None))
        self.lblObjectDate.setText(_translate("DialogGetObject", "Дата создания", None))

import s11main_rc
