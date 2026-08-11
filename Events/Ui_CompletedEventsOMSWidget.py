# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\samson\Events\CompletedEventsOMSWidget.ui'
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

class Ui_CompletedEventsOMSWidget(object):
    def setupUi(self, CompletedEventsOMSWidget):
        CompletedEventsOMSWidget.setObjectName(_fromUtf8("CompletedEventsOMSWidget"))
        CompletedEventsOMSWidget.resize(560, 307)
        self.gridLayout = QtGui.QGridLayout(CompletedEventsOMSWidget)
        self.gridLayout.setMargin(4)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.buttonBox = QtGui.QDialogButtonBox(CompletedEventsOMSWidget)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 7, 0, 1, 3)
        self.lblInfo = QtGui.QLabel(CompletedEventsOMSWidget)
        self.lblInfo.setObjectName(_fromUtf8("lblInfo"))
        self.gridLayout.addWidget(self.lblInfo, 1, 0, 1, 3)
        spacerItem = QtGui.QSpacerItem(0, 0, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, 5, 1, 1, 1)
        self.lblActions = QtGui.QLabel(CompletedEventsOMSWidget)
        self.lblActions.setObjectName(_fromUtf8("lblActions"))
        self.gridLayout.addWidget(self.lblActions, 2, 0, 1, 1)
        self.tblActions = QtGui.QTableView(CompletedEventsOMSWidget)
        self.tblActions.setObjectName(_fromUtf8("tblActions"))
        self.gridLayout.addWidget(self.tblActions, 3, 0, 1, 3)
        self.lblCancel = QtGui.QLabel(CompletedEventsOMSWidget)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.lblCancel.setFont(font)
        self.lblCancel.setWordWrap(True)
        self.lblCancel.setObjectName(_fromUtf8("lblCancel"))
        self.gridLayout.addWidget(self.lblCancel, 4, 0, 1, 3)

        self.retranslateUi(CompletedEventsOMSWidget)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), CompletedEventsOMSWidget.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), CompletedEventsOMSWidget.reject)
        QtCore.QMetaObject.connectSlotsByName(CompletedEventsOMSWidget)

    def retranslateUi(self, CompletedEventsOMSWidget):
        CompletedEventsOMSWidget.setWindowTitle(_translate("CompletedEventsOMSWidget", "Контроль законченных случаев по ОМС", None))
        self.lblInfo.setText(_translate("CompletedEventsOMSWidget", "На пациента найдено аналогичное обращение, код карточки ", None))
        self.lblActions.setText(_translate("CompletedEventsOMSWidget", "Действия в найденном обращении:", None))
        self.lblCancel.setText(_translate("CompletedEventsOMSWidget", "Найденное событие заблокировано или не достаточно прав для его редактирования, попробуйте провести контроль позже", None))

