# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\samson\Stock\ClientInvoice.ui'
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

class Ui_ClientInvoiceDialog(object):
    def setupUi(self, ClientInvoiceDialog):
        ClientInvoiceDialog.setObjectName(_fromUtf8("ClientInvoiceDialog"))
        ClientInvoiceDialog.resize(600, 500)
        self.gridLayout = QtGui.QGridLayout(ClientInvoiceDialog)
        self.gridLayout.setMargin(4)
        self.gridLayout.setSpacing(4)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.txtClientInfoBrowser = CTextBrowser(ClientInvoiceDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.txtClientInfoBrowser.sizePolicy().hasHeightForWidth())
        self.txtClientInfoBrowser.setSizePolicy(sizePolicy)
        self.txtClientInfoBrowser.setMinimumSize(QtCore.QSize(0, 100))
        self.txtClientInfoBrowser.setMaximumSize(QtCore.QSize(16777215, 130))
        self.txtClientInfoBrowser.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.txtClientInfoBrowser.setObjectName(_fromUtf8("txtClientInfoBrowser"))
        self.gridLayout.addWidget(self.txtClientInfoBrowser, 0, 0, 1, 5)
        self.lblNumber = QtGui.QLabel(ClientInvoiceDialog)
        self.lblNumber.setObjectName(_fromUtf8("lblNumber"))
        self.gridLayout.addWidget(self.lblNumber, 1, 0, 1, 1)
        self.edtNumber = QtGui.QLineEdit(ClientInvoiceDialog)
        self.edtNumber.setObjectName(_fromUtf8("edtNumber"))
        self.gridLayout.addWidget(self.edtNumber, 1, 1, 1, 1)
        self.lblDate = QtGui.QLabel(ClientInvoiceDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblDate.sizePolicy().hasHeightForWidth())
        self.lblDate.setSizePolicy(sizePolicy)
        self.lblDate.setObjectName(_fromUtf8("lblDate"))
        self.gridLayout.addWidget(self.lblDate, 1, 2, 1, 1)
        self.edtDate = CDateEdit(ClientInvoiceDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.edtDate.sizePolicy().hasHeightForWidth())
        self.edtDate.setSizePolicy(sizePolicy)
        self.edtDate.setObjectName(_fromUtf8("edtDate"))
        self.gridLayout.addWidget(self.edtDate, 1, 3, 1, 1)
        self.edtTime = QtGui.QTimeEdit(ClientInvoiceDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.edtTime.sizePolicy().hasHeightForWidth())
        self.edtTime.setSizePolicy(sizePolicy)
        self.edtTime.setObjectName(_fromUtf8("edtTime"))
        self.gridLayout.addWidget(self.edtTime, 1, 4, 1, 1)
        self.lblReason = QtGui.QLabel(ClientInvoiceDialog)
        self.lblReason.setObjectName(_fromUtf8("lblReason"))
        self.gridLayout.addWidget(self.lblReason, 2, 0, 1, 1)
        self.edtReason = QtGui.QLineEdit(ClientInvoiceDialog)
        self.edtReason.setObjectName(_fromUtf8("edtReason"))
        self.gridLayout.addWidget(self.edtReason, 2, 1, 1, 1)
        self.lblReasonDate = QtGui.QLabel(ClientInvoiceDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblReasonDate.sizePolicy().hasHeightForWidth())
        self.lblReasonDate.setSizePolicy(sizePolicy)
        self.lblReasonDate.setObjectName(_fromUtf8("lblReasonDate"))
        self.gridLayout.addWidget(self.lblReasonDate, 2, 2, 1, 1)
        self.edtReasonDate = CDateEdit(ClientInvoiceDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.edtReasonDate.sizePolicy().hasHeightForWidth())
        self.edtReasonDate.setSizePolicy(sizePolicy)
        self.edtReasonDate.setObjectName(_fromUtf8("edtReasonDate"))
        self.gridLayout.addWidget(self.edtReasonDate, 2, 3, 1, 1)
        self.lblSupplier = QtGui.QLabel(ClientInvoiceDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblSupplier.sizePolicy().hasHeightForWidth())
        self.lblSupplier.setSizePolicy(sizePolicy)
        self.lblSupplier.setObjectName(_fromUtf8("lblSupplier"))
        self.gridLayout.addWidget(self.lblSupplier, 3, 0, 1, 1)
        self.cmbSupplier = CStorageComboBox(ClientInvoiceDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cmbSupplier.sizePolicy().hasHeightForWidth())
        self.cmbSupplier.setSizePolicy(sizePolicy)
        self.cmbSupplier.setObjectName(_fromUtf8("cmbSupplier"))
        self.gridLayout.addWidget(self.cmbSupplier, 3, 1, 1, 4)
        self.lblSupplierPerson = QtGui.QLabel(ClientInvoiceDialog)
        self.lblSupplierPerson.setObjectName(_fromUtf8("lblSupplierPerson"))
        self.gridLayout.addWidget(self.lblSupplierPerson, 4, 0, 1, 1)
        self.cmbSupplierPerson = CPersonComboBoxEx(ClientInvoiceDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cmbSupplierPerson.sizePolicy().hasHeightForWidth())
        self.cmbSupplierPerson.setSizePolicy(sizePolicy)
        self.cmbSupplierPerson.setObjectName(_fromUtf8("cmbSupplierPerson"))
        self.gridLayout.addWidget(self.cmbSupplierPerson, 4, 1, 1, 4)
        self.lblNote = QtGui.QLabel(ClientInvoiceDialog)
        self.lblNote.setObjectName(_fromUtf8("lblNote"))
        self.gridLayout.addWidget(self.lblNote, 5, 0, 1, 1)
        self.edtNote = QtGui.QLineEdit(ClientInvoiceDialog)
        self.edtNote.setObjectName(_fromUtf8("edtNote"))
        self.gridLayout.addWidget(self.edtNote, 5, 1, 1, 4)
        self.tblItems = CInDocTableView(ClientInvoiceDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tblItems.sizePolicy().hasHeightForWidth())
        self.tblItems.setSizePolicy(sizePolicy)
        self.tblItems.setObjectName(_fromUtf8("tblItems"))
        self.gridLayout.addWidget(self.tblItems, 6, 0, 1, 5)
        self.lblSummaryInfo = QtGui.QLabel(ClientInvoiceDialog)
        self.lblSummaryInfo.setText(_fromUtf8(""))
        self.lblSummaryInfo.setObjectName(_fromUtf8("lblSummaryInfo"))
        self.gridLayout.addWidget(self.lblSummaryInfo, 7, 0, 1, 5)
        self.buttonBox = QtGui.QDialogButtonBox(ClientInvoiceDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 8, 0, 1, 5)
        self.lblNumber.setBuddy(self.edtNumber)
        self.lblDate.setBuddy(self.edtDate)
        self.lblReason.setBuddy(self.edtReason)
        self.lblReasonDate.setBuddy(self.edtReasonDate)
        self.lblSupplier.setBuddy(self.cmbSupplier)
        self.lblSupplierPerson.setBuddy(self.cmbSupplierPerson)
        self.lblNote.setBuddy(self.edtNote)

        self.retranslateUi(ClientInvoiceDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), ClientInvoiceDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), ClientInvoiceDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(ClientInvoiceDialog)
        ClientInvoiceDialog.setTabOrder(self.edtNumber, self.edtDate)
        ClientInvoiceDialog.setTabOrder(self.edtDate, self.edtTime)
        ClientInvoiceDialog.setTabOrder(self.edtTime, self.edtReason)
        ClientInvoiceDialog.setTabOrder(self.edtReason, self.edtReasonDate)
        ClientInvoiceDialog.setTabOrder(self.edtReasonDate, self.cmbSupplier)
        ClientInvoiceDialog.setTabOrder(self.cmbSupplier, self.cmbSupplierPerson)
        ClientInvoiceDialog.setTabOrder(self.cmbSupplierPerson, self.edtNote)
        ClientInvoiceDialog.setTabOrder(self.edtNote, self.tblItems)
        ClientInvoiceDialog.setTabOrder(self.tblItems, self.buttonBox)

    def retranslateUi(self, ClientInvoiceDialog):
        ClientInvoiceDialog.setWindowTitle(_translate("ClientInvoiceDialog", "Накладная на передачу ЛСиИМН пациенту", None))
        self.txtClientInfoBrowser.setWhatsThis(_translate("ClientInvoiceDialog", "Описание пациента", None))
        self.txtClientInfoBrowser.setHtml(_translate("ClientInvoiceDialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Liberation Sans\'; font-size:9pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'MS Shell Dlg 2\'; font-size:8pt;\"><br /></p></body></html>", None))
        self.lblNumber.setText(_translate("ClientInvoiceDialog", "Номер", None))
        self.lblDate.setText(_translate("ClientInvoiceDialog", "Дата", None))
        self.edtTime.setDisplayFormat(_translate("ClientInvoiceDialog", "HH:mm", None))
        self.lblReason.setText(_translate("ClientInvoiceDialog", "Основание", None))
        self.lblReasonDate.setText(_translate("ClientInvoiceDialog", "Дата основания", None))
        self.lblSupplier.setText(_translate("ClientInvoiceDialog", "Поставщик", None))
        self.lblSupplierPerson.setText(_translate("ClientInvoiceDialog", "Ответственный", None))
        self.lblNote.setText(_translate("ClientInvoiceDialog", "Примечания", None))

from Orgs.OrgStructComboBoxes import CStorageComboBox
from Orgs.PersonComboBoxEx import CPersonComboBoxEx
from library.DateEdit import CDateEdit
from library.InDocTable import CInDocTableView
from library.TextBrowser import CTextBrowser
