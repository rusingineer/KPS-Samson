# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\projects\samson\UP_s11\client_pre_release\appendix\mes\ExchangeLocal\ImportXML.ui'
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

class Ui_ImportXML(object):
    def setupUi(self, ImportXML):
        ImportXML.setObjectName(_fromUtf8("ImportXML"))
        ImportXML.resize(475, 429)
        self.gridlayout = QtGui.QGridLayout(ImportXML)
        self.gridlayout.setMargin(4)
        self.gridlayout.setSpacing(4)
        self.gridlayout.setObjectName(_fromUtf8("gridlayout"))
        self.hboxlayout = QtGui.QHBoxLayout()
        self.hboxlayout.setMargin(0)
        self.hboxlayout.setSpacing(4)
        self.hboxlayout.setObjectName(_fromUtf8("hboxlayout"))
        self.btnImport = QtGui.QPushButton(ImportXML)
        self.btnImport.setEnabled(False)
        self.btnImport.setObjectName(_fromUtf8("btnImport"))
        self.hboxlayout.addWidget(self.btnImport)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.hboxlayout.addItem(spacerItem)
        self.btnAbort = QtGui.QPushButton(ImportXML)
        self.btnAbort.setEnabled(False)
        self.btnAbort.setObjectName(_fromUtf8("btnAbort"))
        self.hboxlayout.addWidget(self.btnAbort)
        self.btnClose = QtGui.QPushButton(ImportXML)
        self.btnClose.setObjectName(_fromUtf8("btnClose"))
        self.hboxlayout.addWidget(self.btnClose)
        self.gridlayout.addLayout(self.hboxlayout, 6, 0, 1, 1)
        self.progressBar = CProgressBar(ImportXML)
        self.progressBar.setProperty("value", 24)
        self.progressBar.setOrientation(QtCore.Qt.Horizontal)
        self.progressBar.setObjectName(_fromUtf8("progressBar"))
        self.gridlayout.addWidget(self.progressBar, 1, 0, 1, 1)
        self.lblStatus = QtGui.QLabel(ImportXML)
        self.lblStatus.setText(_fromUtf8(""))
        self.lblStatus.setObjectName(_fromUtf8("lblStatus"))
        self.gridlayout.addWidget(self.lblStatus, 5, 0, 1, 1)
        self.logBrowser = QtGui.QTextBrowser(ImportXML)
        self.logBrowser.setObjectName(_fromUtf8("logBrowser"))
        self.gridlayout.addWidget(self.logBrowser, 4, 0, 1, 1)
        self.chkFullLog = QtGui.QCheckBox(ImportXML)
        self.chkFullLog.setObjectName(_fromUtf8("chkFullLog"))
        self.gridlayout.addWidget(self.chkFullLog, 2, 0, 1, 1)
        self.chkUpdateMes = QtGui.QCheckBox(ImportXML)
        self.chkUpdateMes.setObjectName(_fromUtf8("chkUpdateMes"))
        self.gridlayout.addWidget(self.chkUpdateMes, 3, 0, 1, 1)
        self.hboxlayout1 = QtGui.QHBoxLayout()
        self.hboxlayout1.setMargin(0)
        self.hboxlayout1.setSpacing(4)
        self.hboxlayout1.setObjectName(_fromUtf8("hboxlayout1"))
        self.label = QtGui.QLabel(ImportXML)
        self.label.setObjectName(_fromUtf8("label"))
        self.hboxlayout1.addWidget(self.label)
        self.edtFileName = QtGui.QLineEdit(ImportXML)
        self.edtFileName.setObjectName(_fromUtf8("edtFileName"))
        self.hboxlayout1.addWidget(self.edtFileName)
        self.btnSelectFile = QtGui.QToolButton(ImportXML)
        self.btnSelectFile.setObjectName(_fromUtf8("btnSelectFile"))
        self.hboxlayout1.addWidget(self.btnSelectFile)
        self.gridlayout.addLayout(self.hboxlayout1, 0, 0, 1, 1)

        self.retranslateUi(ImportXML)
        QtCore.QMetaObject.connectSlotsByName(ImportXML)
        ImportXML.setTabOrder(self.edtFileName, self.btnSelectFile)
        ImportXML.setTabOrder(self.btnSelectFile, self.chkFullLog)
        ImportXML.setTabOrder(self.chkFullLog, self.chkUpdateMes)
        ImportXML.setTabOrder(self.chkUpdateMes, self.logBrowser)
        ImportXML.setTabOrder(self.logBrowser, self.btnImport)
        ImportXML.setTabOrder(self.btnImport, self.btnAbort)
        ImportXML.setTabOrder(self.btnAbort, self.btnClose)

    def retranslateUi(self, ImportXML):
        ImportXML.setWindowTitle(_translate("ImportXML", "Импорт МЭС", None))
        self.btnImport.setText(_translate("ImportXML", "Начать импорт", None))
        self.btnAbort.setText(_translate("ImportXML", "Прервать", None))
        self.btnClose.setText(_translate("ImportXML", "Закрыть", None))
        self.chkFullLog.setText(_translate("ImportXML", "Подробный отчет", None))
        self.chkUpdateMes.setText(_translate("ImportXML", "Обновлять совпадающие МЭСы", None))
        self.label.setText(_translate("ImportXML", "Загрузить из", None))
        self.btnSelectFile.setText(_translate("ImportXML", "...", None))

from library.ProgressBar import CProgressBar
