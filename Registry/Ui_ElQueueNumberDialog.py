# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\Samson\client_test\Registry\ElQueueNumberDialog.ui'
#
# Created: Mon Jul 13 17:34:44 2026
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

class Ui_ElQueueNumberDialog(object):
    def setupUi(self, ElQueueNumberDialog):
        ElQueueNumberDialog.setObjectName(_fromUtf8("ElQueueNumberDialog"))
        ElQueueNumberDialog.resize(437, 85)
        ElQueueNumberDialog.setMinimumSize(QtCore.QSize(0, 0))
        self.verticalLayout = QtGui.QVBoxLayout(ElQueueNumberDialog)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setMargin(0)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.frame = QtGui.QFrame(ElQueueNumberDialog)
        self.frame.setFrameShape(QtGui.QFrame.Panel)
        self.frame.setFrameShadow(QtGui.QFrame.Raised)
        self.frame.setLineWidth(1)
        self.frame.setObjectName(_fromUtf8("frame"))
        self.horizontalLayout = QtGui.QHBoxLayout(self.frame)
        self.horizontalLayout.setMargin(9)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.label = QtGui.QLabel(self.frame)
        self.label.setTextFormat(QtCore.Qt.PlainText)
        self.label.setWordWrap(False)
        self.label.setObjectName(_fromUtf8("label"))
        self.horizontalLayout.addWidget(self.label)
        spacerItem = QtGui.QSpacerItem(20, 20, QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.leQueueNumber = QtGui.QLineEdit(self.frame)
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.leQueueNumber.setFont(font)
        self.leQueueNumber.setInputMask(_fromUtf8(""))
        self.leQueueNumber.setText(_fromUtf8(""))
        self.leQueueNumber.setObjectName(_fromUtf8("leQueueNumber"))
        self.horizontalLayout.addWidget(self.leQueueNumber)
        self.verticalLayout.addWidget(self.frame)
        self.frame_2 = QtGui.QFrame(ElQueueNumberDialog)
        self.frame_2.setMinimumSize(QtCore.QSize(0, 40))
        self.frame_2.setMaximumSize(QtCore.QSize(16777215, 40))
        self.frame_2.setFrameShape(QtGui.QFrame.NoFrame)
        self.frame_2.setFrameShadow(QtGui.QFrame.Raised)
        self.frame_2.setLineWidth(0)
        self.frame_2.setObjectName(_fromUtf8("frame_2"))
        self.horizontalLayout_2 = QtGui.QHBoxLayout(self.frame_2)
        self.horizontalLayout_2.setMargin(6)
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem1)
        self.btnOK = QtGui.QPushButton(self.frame_2)
        self.btnOK.setObjectName(_fromUtf8("btnOK"))
        self.horizontalLayout_2.addWidget(self.btnOK)
        self.btnSkip = QtGui.QPushButton(self.frame_2)
        self.btnSkip.setObjectName(_fromUtf8("btnSkip"))
        self.horizontalLayout_2.addWidget(self.btnSkip)
        self.btnCancel = QtGui.QPushButton(self.frame_2)
        self.btnCancel.setObjectName(_fromUtf8("btnCancel"))
        self.horizontalLayout_2.addWidget(self.btnCancel)
        self.verticalLayout.addWidget(self.frame_2)

        self.retranslateUi(ElQueueNumberDialog)
        QtCore.QMetaObject.connectSlotsByName(ElQueueNumberDialog)

    def retranslateUi(self, ElQueueNumberDialog):
        ElQueueNumberDialog.setWindowTitle(_translate("ElQueueNumberDialog", "Введите номер талона ЭО если есть", None))
        self.label.setText(_translate("ElQueueNumberDialog", "Введите номер талона электронной очереди", None))
        self.btnOK.setText(_translate("ElQueueNumberDialog", "OK", None))
        self.btnSkip.setText(_translate("ElQueueNumberDialog", "Пропустить", None))
        self.btnCancel.setText(_translate("ElQueueNumberDialog", "Отменить", None))

