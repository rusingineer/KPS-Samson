# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/work/kmivc-arch/Samson/client_test/preferences/ActionPage.ui'
#
# Created by: PyQt4 UI code generator 4.12.3
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

class Ui_actionPage(object):
    def setupUi(self, actionPage):
        actionPage.setObjectName(_fromUtf8("actionPage"))
        actionPage.resize(651, 405)
        actionPage.setToolTip(_fromUtf8(""))
        self.gridLayout = QtGui.QGridLayout(actionPage)
        self.gridLayout.setMargin(4)
        self.gridLayout.setSpacing(4)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        spacerItem = QtGui.QSpacerItem(20, 1, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, 3, 0, 1, 1)
        self.lblActionTemplatePriorityLoad = QtGui.QLabel(actionPage)
        self.lblActionTemplatePriorityLoad.setObjectName(_fromUtf8("lblActionTemplatePriorityLoad"))
        self.gridLayout.addWidget(self.lblActionTemplatePriorityLoad, 1, 0, 1, 1)
        self.cmbActionTemplatePriorityLoad = QtGui.QComboBox(actionPage)
        self.cmbActionTemplatePriorityLoad.setObjectName(_fromUtf8("cmbActionTemplatePriorityLoad"))
        self.cmbActionTemplatePriorityLoad.addItem(_fromUtf8(""))
        self.cmbActionTemplatePriorityLoad.addItem(_fromUtf8(""))
        self.gridLayout.addWidget(self.cmbActionTemplatePriorityLoad, 1, 1, 1, 1)
        self.chkOrgStructurePriorityForAddActions = QtGui.QCheckBox(actionPage)
        self.chkOrgStructurePriorityForAddActions.setObjectName(_fromUtf8("chkOrgStructurePriorityForAddActions"))
        self.gridLayout.addWidget(self.chkOrgStructurePriorityForAddActions, 0, 0, 1, 2)
        self.chkEnableUserDictionary = QtGui.QCheckBox(actionPage)
        self.chkEnableUserDictionary.setObjectName(_fromUtf8("chkEnableUserDictionary"))
        self.gridLayout.addWidget(self.chkEnableUserDictionary, 2, 0, 1, 1)

        self.retranslateUi(actionPage)
        QtCore.QMetaObject.connectSlotsByName(actionPage)

    def retranslateUi(self, actionPage):
        actionPage.setWindowTitle(_translate("actionPage", "Ввод действий", None))
        self.lblActionTemplatePriorityLoad.setText(_translate("actionPage", "Приоритет фокуса для загрузки шаблона действия", None))
        self.cmbActionTemplatePriorityLoad.setItemText(0, _translate("actionPage", "Добавить", None))
        self.cmbActionTemplatePriorityLoad.setItemText(1, _translate("actionPage", "Заполнить", None))
        self.chkOrgStructurePriorityForAddActions.setText(_translate("actionPage", "Приоритет подразделения для функции \"Добавить ...\"", None))
        self.chkEnableUserDictionary.setText(_translate("actionPage", "Включить отображение Словаря пользователя", None))

