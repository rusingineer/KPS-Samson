# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'E:\projects\Samson\UP_s11\client\preferences\PrintPage.ui'
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

class Ui_printPage(object):
    def setupUi(self, printPage):
        printPage.setObjectName(_fromUtf8("printPage"))
        printPage.resize(512, 313)
        printPage.setToolTip(_fromUtf8(""))
        self.gridLayout = QtGui.QGridLayout(printPage)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.chkEnableFastPrint = QtGui.QCheckBox(printPage)
        self.chkEnableFastPrint.setText(_fromUtf8(""))
        self.chkEnableFastPrint.setObjectName(_fromUtf8("chkEnableFastPrint"))
        self.gridLayout.addWidget(self.chkEnableFastPrint, 0, 1, 1, 1)
        self.lblShowPageSetup = QtGui.QLabel(printPage)
        self.lblShowPageSetup.setObjectName(_fromUtf8("lblShowPageSetup"))
        self.gridLayout.addWidget(self.lblShowPageSetup, 1, 0, 1, 1)
        self.lblEnableFastPrint = QtGui.QLabel(printPage)
        self.lblEnableFastPrint.setObjectName(_fromUtf8("lblEnableFastPrint"))
        self.gridLayout.addWidget(self.lblEnableFastPrint, 0, 0, 1, 1)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 0, 3, 1, 1)
        self.lblPrintBlackWhite = QtGui.QLabel(printPage)
        self.lblPrintBlackWhite.setObjectName(_fromUtf8("lblPrintBlackWhite"))
        self.gridLayout.addWidget(self.lblPrintBlackWhite, 3, 0, 1, 1)
        self.cmbLabelPrinter = QtGui.QComboBox(printPage)
        self.cmbLabelPrinter.setObjectName(_fromUtf8("cmbLabelPrinter"))
        self.gridLayout.addWidget(self.cmbLabelPrinter, 2, 1, 1, 3)
        spacerItem1 = QtGui.QSpacerItem(49, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem1, 1, 3, 1, 1)
        self.lblLabelPrinter = QtGui.QLabel(printPage)
        self.lblLabelPrinter.setObjectName(_fromUtf8("lblLabelPrinter"))
        self.gridLayout.addWidget(self.lblLabelPrinter, 2, 0, 1, 1)
        self.chkShowPageSetup = QtGui.QCheckBox(printPage)
        self.chkShowPageSetup.setText(_fromUtf8(""))
        self.chkShowPageSetup.setObjectName(_fromUtf8("chkShowPageSetup"))
        self.gridLayout.addWidget(self.chkShowPageSetup, 1, 1, 1, 1)
        spacerItem2 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem2, 3, 3, 1, 1)
        spacerItem3 = QtGui.QSpacerItem(20, 1, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem3, 8, 0, 1, 1)
        self.lblEnablePreview = QtGui.QLabel(printPage)
        self.lblEnablePreview.setObjectName(_fromUtf8("lblEnablePreview"))
        self.gridLayout.addWidget(self.lblEnablePreview, 4, 0, 1, 1)
        self.chkEnablePreview = QtGui.QCheckBox(printPage)
        self.chkEnablePreview.setText(_fromUtf8(""))
        self.chkEnablePreview.setObjectName(_fromUtf8("chkEnablePreview"))
        self.gridLayout.addWidget(self.chkEnablePreview, 4, 1, 1, 1)
        self.chkPrintBlackWhite = QtGui.QCheckBox(printPage)
        self.chkPrintBlackWhite.setText(_fromUtf8(""))
        self.chkPrintBlackWhite.setChecked(True)
        self.chkPrintBlackWhite.setObjectName(_fromUtf8("chkPrintBlackWhite"))
        self.gridLayout.addWidget(self.chkPrintBlackWhite, 3, 1, 1, 1)
        spacerItem4 = QtGui.QSpacerItem(90, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem4, 4, 3, 1, 1)
        self.lblTemplateEdit = QtGui.QLabel(printPage)
        self.lblTemplateEdit.setObjectName(_fromUtf8("lblTemplateEdit"))
        self.gridLayout.addWidget(self.lblTemplateEdit, 5, 0, 1, 1)
        self.chkTemplateEdit = QtGui.QCheckBox(printPage)
        self.chkTemplateEdit.setText(_fromUtf8(""))
        self.chkTemplateEdit.setObjectName(_fromUtf8("chkTemplateEdit"))
        self.gridLayout.addWidget(self.chkTemplateEdit, 5, 1, 1, 1)
        self.chkPrintFullPage = QtGui.QCheckBox(printPage)
        self.chkPrintFullPage.setText(_fromUtf8(""))
        self.chkPrintFullPage.setChecked(True)
        self.chkPrintFullPage.setObjectName(_fromUtf8("chkPrintFullPage"))
        self.gridLayout.addWidget(self.chkPrintFullPage, 7, 1, 1, 1)
        spacerItem5 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem5, 7, 3, 1, 1)
        self.lblPrintFullPage = QtGui.QLabel(printPage)
        self.lblPrintFullPage.setObjectName(_fromUtf8("lblPrintFullPage"))
        self.gridLayout.addWidget(self.lblPrintFullPage, 7, 0, 1, 1)
        self.lblShowPageSetup.setBuddy(self.chkShowPageSetup)
        self.lblEnableFastPrint.setBuddy(self.chkEnableFastPrint)
        self.lblPrintBlackWhite.setBuddy(self.chkPrintBlackWhite)
        self.lblLabelPrinter.setBuddy(self.cmbLabelPrinter)
        self.lblEnablePreview.setBuddy(self.chkEnablePreview)
        self.lblPrintFullPage.setBuddy(self.chkPrintFullPage)

        self.retranslateUi(printPage)
        QtCore.QMetaObject.connectSlotsByName(printPage)
        printPage.setTabOrder(self.chkEnableFastPrint, self.cmbLabelPrinter)
        printPage.setTabOrder(self.cmbLabelPrinter, self.chkPrintBlackWhite)

    def retranslateUi(self, printPage):
        printPage.setWindowTitle(_translate("printPage", "Печать", None))
        self.lblShowPageSetup.setText(_translate("printPage", "Отображать окно настроек параметров страницы", None))
        self.lblEnableFastPrint.setText(_translate("printPage", "Разрешить печать без показа диалога настройки принтера", None))
        self.lblPrintBlackWhite.setText(_translate("printPage", "Отключать цвет при выводе на печать", None))
        self.lblLabelPrinter.setText(_translate("printPage", "Принтер для визиток пациентов и наклеек", None))
        self.lblEnablePreview.setText(_translate("printPage", "Разрешить печать с предпросмотром", None))
        self.lblTemplateEdit.setText(_translate("printPage", "Режим отладки шаблонов печати", None))
        self.lblPrintFullPage.setText(_translate("printPage", "Отключить границы печати по настройкам принтера", None))

