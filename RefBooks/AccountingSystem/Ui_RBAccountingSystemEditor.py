# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\Project\Samson\UP_s11\client_pre_release\RefBooks\AccountingSystem\RBAccountingSystemEditor.ui'
#
# Created: Thu Jul 30 16:32:21 2026
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

class Ui_ItemEditorDialog(object):
    def setupUi(self, ItemEditorDialog):
        ItemEditorDialog.setObjectName(_fromUtf8("ItemEditorDialog"))
        ItemEditorDialog.resize(393, 258)
        ItemEditorDialog.setSizeGripEnabled(True)
        self.gridlayout = QtGui.QGridLayout(ItemEditorDialog)
        self.gridlayout.setMargin(4)
        self.gridlayout.setSpacing(4)
        self.gridlayout.setObjectName(_fromUtf8("gridlayout"))
        self.chkEditable = QtGui.QCheckBox(ItemEditorDialog)
        self.chkEditable.setObjectName(_fromUtf8("chkEditable"))
        self.gridlayout.addWidget(self.chkEditable, 5, 1, 1, 1)
        self.edtName = QtGui.QLineEdit(ItemEditorDialog)
        self.edtName.setMaxLength(255)
        self.edtName.setObjectName(_fromUtf8("edtName"))
        self.gridlayout.addWidget(self.edtName, 1, 1, 1, 1)
        spacerItem = QtGui.QSpacerItem(103, 16, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridlayout.addItem(spacerItem, 9, 0, 1, 1)
        self.lblName = QtGui.QLabel(ItemEditorDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblName.sizePolicy().hasHeightForWidth())
        self.lblName.setSizePolicy(sizePolicy)
        self.lblName.setObjectName(_fromUtf8("lblName"))
        self.gridlayout.addWidget(self.lblName, 1, 0, 1, 1)
        self.chkIsUnique = QtGui.QCheckBox(ItemEditorDialog)
        self.chkIsUnique.setObjectName(_fromUtf8("chkIsUnique"))
        self.gridlayout.addWidget(self.chkIsUnique, 8, 1, 1, 1)
        self.lblCode = QtGui.QLabel(ItemEditorDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblCode.sizePolicy().hasHeightForWidth())
        self.lblCode.setSizePolicy(sizePolicy)
        self.lblCode.setObjectName(_fromUtf8("lblCode"))
        self.gridlayout.addWidget(self.lblCode, 0, 0, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(ItemEditorDialog)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridlayout.addWidget(self.buttonBox, 10, 0, 1, 2)
        self.edtCode = QtGui.QLineEdit(ItemEditorDialog)
        self.edtCode.setMaxLength(64)
        self.edtCode.setObjectName(_fromUtf8("edtCode"))
        self.gridlayout.addWidget(self.edtCode, 0, 1, 1, 1)
        self.lblUrn = QtGui.QLabel(ItemEditorDialog)
        self.lblUrn.setObjectName(_fromUtf8("lblUrn"))
        self.gridlayout.addWidget(self.lblUrn, 2, 0, 1, 1)
        self.chkShowInClientInfo = QtGui.QCheckBox(ItemEditorDialog)
        self.chkShowInClientInfo.setObjectName(_fromUtf8("chkShowInClientInfo"))
        self.gridlayout.addWidget(self.chkShowInClientInfo, 7, 1, 1, 1)
        self.edtUrn = QtGui.QLineEdit(ItemEditorDialog)
        self.edtUrn.setMaxLength(128)
        self.edtUrn.setObjectName(_fromUtf8("edtUrn"))
        self.gridlayout.addWidget(self.edtUrn, 2, 1, 1, 1)
        self.lblVersion = QtGui.QLabel(ItemEditorDialog)
        self.lblVersion.setObjectName(_fromUtf8("lblVersion"))
        self.gridlayout.addWidget(self.lblVersion, 3, 0, 1, 1)
        self.lblDomain = QtGui.QLabel(ItemEditorDialog)
        self.lblDomain.setObjectName(_fromUtf8("lblDomain"))
        self.gridlayout.addWidget(self.lblDomain, 4, 0, 1, 1)
        self.edtVersion = QtGui.QLineEdit(ItemEditorDialog)
        self.edtVersion.setMaxLength(4)
        self.edtVersion.setObjectName(_fromUtf8("edtVersion"))
        self.gridlayout.addWidget(self.edtVersion, 3, 1, 1, 1)
        self.edtDomain = QtGui.QLineEdit(ItemEditorDialog)
        self.edtDomain.setMaxLength(255)
        self.edtDomain.setObjectName(_fromUtf8("edtDomain"))
        self.gridlayout.addWidget(self.edtDomain, 4, 1, 1, 1)
        self.chkDeletable = QtGui.QCheckBox(ItemEditorDialog)
        self.chkDeletable.setObjectName(_fromUtf8("chkDeletable"))
        self.gridlayout.addWidget(self.chkDeletable, 6, 1, 1, 1)
        self.lblName.setBuddy(self.edtName)
        self.lblCode.setBuddy(self.edtCode)
        self.lblUrn.setBuddy(self.edtUrn)
        self.lblVersion.setBuddy(self.edtVersion)
        self.lblDomain.setBuddy(self.edtDomain)

        self.retranslateUi(ItemEditorDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), ItemEditorDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), ItemEditorDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(ItemEditorDialog)
        ItemEditorDialog.setTabOrder(self.edtCode, self.edtName)
        ItemEditorDialog.setTabOrder(self.edtName, self.edtUrn)
        ItemEditorDialog.setTabOrder(self.edtUrn, self.edtVersion)
        ItemEditorDialog.setTabOrder(self.edtVersion, self.edtDomain)
        ItemEditorDialog.setTabOrder(self.edtDomain, self.chkEditable)
        ItemEditorDialog.setTabOrder(self.chkEditable, self.chkShowInClientInfo)
        ItemEditorDialog.setTabOrder(self.chkShowInClientInfo, self.chkIsUnique)
        ItemEditorDialog.setTabOrder(self.chkIsUnique, self.buttonBox)

    def retranslateUi(self, ItemEditorDialog):
        ItemEditorDialog.setWindowTitle(_translate("ItemEditorDialog", "Тип внешней системы", None))
        self.chkEditable.setText(_translate("ItemEditorDialog", "&Разрешать изменение", None))
        self.lblName.setText(_translate("ItemEditorDialog", "&Наименование", None))
        self.chkIsUnique.setText(_translate("ItemEditorDialog", "Требует ввод уникального значения", None))
        self.lblCode.setText(_translate("ItemEditorDialog", "&Код", None))
        self.lblUrn.setText(_translate("ItemEditorDialog", "&URN", None))
        self.chkShowInClientInfo.setText(_translate("ItemEditorDialog", "Отображать в информации о пациенте", None))
        self.lblVersion.setText(_translate("ItemEditorDialog", "&Версия справочника", None))
        self.lblDomain.setText(_translate("ItemEditorDialog", "&Область применения", None))
        self.chkDeletable.setText(_translate("ItemEditorDialog", "&Разрешать удаление", None))

