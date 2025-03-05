# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/green/s11_trunk/Stock/Mdlp/DisposalOrder.ui'
#
# Created by: PyQt4 UI code generator 4.12.1
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

class Ui_DisposalOrderDialog(object):
    def setupUi(self, DisposalOrderDialog):
        DisposalOrderDialog.setObjectName(_fromUtf8("DisposalOrderDialog"))
        DisposalOrderDialog.resize(600, 500)
        self.gridLayout = QtGui.QGridLayout(DisposalOrderDialog)
        self.gridLayout.setMargin(4)
        self.gridLayout.setSpacing(4)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.lblSummaryInfo = QtGui.QLabel(DisposalOrderDialog)
        self.lblSummaryInfo.setText(_fromUtf8(""))
        self.lblSummaryInfo.setObjectName(_fromUtf8("lblSummaryInfo"))
        self.gridLayout.addWidget(self.lblSummaryInfo, 7, 0, 1, 5)
        self.edtBaseInvoiceTime = QtGui.QTimeEdit(DisposalOrderDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.edtBaseInvoiceTime.sizePolicy().hasHeightForWidth())
        self.edtBaseInvoiceTime.setSizePolicy(sizePolicy)
        self.edtBaseInvoiceTime.setReadOnly(True)
        self.edtBaseInvoiceTime.setObjectName(_fromUtf8("edtBaseInvoiceTime"))
        self.gridLayout.addWidget(self.edtBaseInvoiceTime, 0, 4, 1, 1)
        self.tblItems = CInDocTableView(DisposalOrderDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tblItems.sizePolicy().hasHeightForWidth())
        self.tblItems.setSizePolicy(sizePolicy)
        self.tblItems.setObjectName(_fromUtf8("tblItems"))
        self.gridLayout.addWidget(self.tblItems, 6, 0, 1, 5)
        self.edtBaseInvoiceDate = CDateEdit(DisposalOrderDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.edtBaseInvoiceDate.sizePolicy().hasHeightForWidth())
        self.edtBaseInvoiceDate.setSizePolicy(sizePolicy)
        self.edtBaseInvoiceDate.setReadOnly(True)
        self.edtBaseInvoiceDate.setObjectName(_fromUtf8("edtBaseInvoiceDate"))
        self.gridLayout.addWidget(self.edtBaseInvoiceDate, 0, 3, 1, 1)
        self.edtBaseInvoiceNumber = QtGui.QLineEdit(DisposalOrderDialog)
        self.edtBaseInvoiceNumber.setText(_fromUtf8(""))
        self.edtBaseInvoiceNumber.setReadOnly(True)
        self.edtBaseInvoiceNumber.setObjectName(_fromUtf8("edtBaseInvoiceNumber"))
        self.gridLayout.addWidget(self.edtBaseInvoiceNumber, 0, 1, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(DisposalOrderDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.NoButton)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 8, 0, 1, 5)
        self.lblBaseInvoiceDate = QtGui.QLabel(DisposalOrderDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblBaseInvoiceDate.sizePolicy().hasHeightForWidth())
        self.lblBaseInvoiceDate.setSizePolicy(sizePolicy)
        self.lblBaseInvoiceDate.setObjectName(_fromUtf8("lblBaseInvoiceDate"))
        self.gridLayout.addWidget(self.lblBaseInvoiceDate, 0, 2, 1, 1)
        self.lblBaseInvoiceNumber = QtGui.QLabel(DisposalOrderDialog)
        self.lblBaseInvoiceNumber.setObjectName(_fromUtf8("lblBaseInvoiceNumber"))
        self.gridLayout.addWidget(self.lblBaseInvoiceNumber, 0, 0, 1, 1)
        self.lblMdlpRequestIdValue = QtGui.QLabel(DisposalOrderDialog)
        self.lblMdlpRequestIdValue.setFrameShape(QtGui.QFrame.StyledPanel)
        self.lblMdlpRequestIdValue.setText(_fromUtf8(""))
        self.lblMdlpRequestIdValue.setTextFormat(QtCore.Qt.PlainText)
        self.lblMdlpRequestIdValue.setTextInteractionFlags(QtCore.Qt.TextSelectableByKeyboard|QtCore.Qt.TextSelectableByMouse)
        self.lblMdlpRequestIdValue.setObjectName(_fromUtf8("lblMdlpRequestIdValue"))
        self.gridLayout.addWidget(self.lblMdlpRequestIdValue, 3, 1, 1, 1)
        self.lblRvRequestId = QtGui.QLabel(DisposalOrderDialog)
        self.lblRvRequestId.setObjectName(_fromUtf8("lblRvRequestId"))
        self.gridLayout.addWidget(self.lblRvRequestId, 2, 0, 1, 1)
        self.lblMdlpRequestId = QtGui.QLabel(DisposalOrderDialog)
        self.lblMdlpRequestId.setObjectName(_fromUtf8("lblMdlpRequestId"))
        self.gridLayout.addWidget(self.lblMdlpRequestId, 3, 0, 1, 1)
        self.lblRvRequestIdValue = QtGui.QLabel(DisposalOrderDialog)
        self.lblRvRequestIdValue.setFrameShape(QtGui.QFrame.StyledPanel)
        self.lblRvRequestIdValue.setText(_fromUtf8(""))
        self.lblRvRequestIdValue.setTextFormat(QtCore.Qt.PlainText)
        self.lblRvRequestIdValue.setTextInteractionFlags(QtCore.Qt.TextSelectableByKeyboard|QtCore.Qt.TextSelectableByMouse)
        self.lblRvRequestIdValue.setObjectName(_fromUtf8("lblRvRequestIdValue"))
        self.gridLayout.addWidget(self.lblRvRequestIdValue, 2, 1, 1, 1)
        self.lblStatus = QtGui.QLabel(DisposalOrderDialog)
        self.lblStatus.setObjectName(_fromUtf8("lblStatus"))
        self.gridLayout.addWidget(self.lblStatus, 1, 0, 1, 1)
        self.lblStatusValue = QtGui.QLabel(DisposalOrderDialog)
        self.lblStatusValue.setFrameShape(QtGui.QFrame.StyledPanel)
        self.lblStatusValue.setText(_fromUtf8(""))
        self.lblStatusValue.setTextFormat(QtCore.Qt.PlainText)
        self.lblStatusValue.setTextInteractionFlags(QtCore.Qt.TextSelectableByKeyboard|QtCore.Qt.TextSelectableByMouse)
        self.lblStatusValue.setObjectName(_fromUtf8("lblStatusValue"))
        self.gridLayout.addWidget(self.lblStatusValue, 1, 1, 1, 4)
        self.lblBaseInvoiceDate.setBuddy(self.edtBaseInvoiceDate)
        self.lblBaseInvoiceNumber.setBuddy(self.edtBaseInvoiceNumber)

        self.retranslateUi(DisposalOrderDialog)
        QtCore.QMetaObject.connectSlotsByName(DisposalOrderDialog)
        DisposalOrderDialog.setTabOrder(self.edtBaseInvoiceNumber, self.edtBaseInvoiceDate)
        DisposalOrderDialog.setTabOrder(self.edtBaseInvoiceDate, self.edtBaseInvoiceTime)
        DisposalOrderDialog.setTabOrder(self.edtBaseInvoiceTime, self.tblItems)
        DisposalOrderDialog.setTabOrder(self.tblItems, self.buttonBox)

    def retranslateUi(self, DisposalOrderDialog):
        DisposalOrderDialog.setWindowTitle(_translate("DisposalOrderDialog", "Запрос к регистратору выбытия «Отчёт о выбытии»", None))
        self.edtBaseInvoiceTime.setDisplayFormat(_translate("DisposalOrderDialog", "HH:mm", None))
        self.lblBaseInvoiceDate.setText(_translate("DisposalOrderDialog", "Дата", None))
        self.lblBaseInvoiceNumber.setText(_translate("DisposalOrderDialog", "Номер накладной", None))
        self.lblRvRequestId.setText(_translate("DisposalOrderDialog", "Идентификатор запроса", None))
        self.lblMdlpRequestId.setText(_translate("DisposalOrderDialog", "Идентификатор МДЛП", None))
        self.lblStatus.setText(_translate("DisposalOrderDialog", "Состояние", None))

from library.DateEdit import CDateEdit
from library.InDocTable import CInDocTableView

if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    DisposalOrderDialog = QtGui.QDialog()
    ui = Ui_DisposalOrderDialog()
    ui.setupUi(DisposalOrderDialog)
    DisposalOrderDialog.show()
    sys.exit(app.exec_())

