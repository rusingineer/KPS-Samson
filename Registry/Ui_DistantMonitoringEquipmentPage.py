# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\projects\Samson\UP_s11\client\Registry\DistantMonitoringEquipmentPage.ui'
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

class Ui_DistantMonitoringEquipmentPage(object):
    def setupUi(self, DistantMonitoringEquipmentPage):
        DistantMonitoringEquipmentPage.setObjectName(_fromUtf8("DistantMonitoringEquipmentPage"))
        DistantMonitoringEquipmentPage.resize(1137, 824)
        self.horizontalLayout = QtGui.QHBoxLayout(DistantMonitoringEquipmentPage)
        self.horizontalLayout.setMargin(2)
        self.horizontalLayout.setSpacing(2)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.grpTables = QtGui.QWidget(DistantMonitoringEquipmentPage)
        self.grpTables.setObjectName(_fromUtf8("grpTables"))
        self.verticalLayout = QtGui.QVBoxLayout(self.grpTables)
        self.verticalLayout.setMargin(2)
        self.verticalLayout.setSpacing(2)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.tblEquipmentList = CTableView(self.grpTables)
        self.tblEquipmentList.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.tblEquipmentList.setObjectName(_fromUtf8("tblEquipmentList"))
        self.verticalLayout.addWidget(self.tblEquipmentList)
        self.lblRecordCount = QtGui.QLabel(self.grpTables)
        self.lblRecordCount.setObjectName(_fromUtf8("lblRecordCount"))
        self.verticalLayout.addWidget(self.lblRecordCount)
        self.horizontalLayout.addWidget(self.grpTables)
        self.grpFilter = QtGui.QGroupBox(DistantMonitoringEquipmentPage)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.grpFilter.sizePolicy().hasHeightForWidth())
        self.grpFilter.setSizePolicy(sizePolicy)
        self.grpFilter.setMinimumSize(QtCore.QSize(350, 0))
        self.grpFilter.setMaximumSize(QtCore.QSize(350, 16777215))
        self.grpFilter.setFlat(False)
        self.grpFilter.setObjectName(_fromUtf8("grpFilter"))
        self.gridLayout = QtGui.QGridLayout(self.grpFilter)
        self.gridLayout.setMargin(4)
        self.gridLayout.setSpacing(2)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.chkEquipmentType = QtGui.QCheckBox(self.grpFilter)
        self.chkEquipmentType.setObjectName(_fromUtf8("chkEquipmentType"))
        self.gridLayout.addWidget(self.chkEquipmentType, 2, 0, 1, 1)
        self.chkEquipmentStatus = QtGui.QCheckBox(self.grpFilter)
        self.chkEquipmentStatus.setObjectName(_fromUtf8("chkEquipmentStatus"))
        self.gridLayout.addWidget(self.chkEquipmentStatus, 4, 0, 1, 1)
        spacerItem = QtGui.QSpacerItem(591, 316, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, 8, 0, 1, 2)
        self.chkRegistrationStatus = QtGui.QCheckBox(self.grpFilter)
        self.chkRegistrationStatus.setObjectName(_fromUtf8("chkRegistrationStatus"))
        self.gridLayout.addWidget(self.chkRegistrationStatus, 6, 0, 1, 1)
        self.buttonBoxFilter = CApplyResetDialogButtonBox(self.grpFilter)
        self.buttonBoxFilter.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBoxFilter.setStandardButtons(QtGui.QDialogButtonBox.Apply|QtGui.QDialogButtonBox.Reset)
        self.buttonBoxFilter.setObjectName(_fromUtf8("buttonBoxFilter"))
        self.gridLayout.addWidget(self.buttonBoxFilter, 9, 0, 1, 2)
        self.chkEquipmentClass = QtGui.QCheckBox(self.grpFilter)
        self.chkEquipmentClass.setObjectName(_fromUtf8("chkEquipmentClass"))
        self.gridLayout.addWidget(self.chkEquipmentClass, 0, 0, 1, 2)
        self.cmbEquipmentClass = CRBComboBox(self.grpFilter)
        self.cmbEquipmentClass.setEnabled(False)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cmbEquipmentClass.sizePolicy().hasHeightForWidth())
        self.cmbEquipmentClass.setSizePolicy(sizePolicy)
        self.cmbEquipmentClass.setObjectName(_fromUtf8("cmbEquipmentClass"))
        self.gridLayout.addWidget(self.cmbEquipmentClass, 1, 0, 1, 2)
        self.cmbEquipmentStatus = QtGui.QComboBox(self.grpFilter)
        self.cmbEquipmentStatus.setEnabled(False)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cmbEquipmentStatus.sizePolicy().hasHeightForWidth())
        self.cmbEquipmentStatus.setSizePolicy(sizePolicy)
        self.cmbEquipmentStatus.setObjectName(_fromUtf8("cmbEquipmentStatus"))
        self.gridLayout.addWidget(self.cmbEquipmentStatus, 5, 0, 1, 1)
        self.cmbEquipmentType = CRBComboBox(self.grpFilter)
        self.cmbEquipmentType.setEnabled(False)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cmbEquipmentType.sizePolicy().hasHeightForWidth())
        self.cmbEquipmentType.setSizePolicy(sizePolicy)
        self.cmbEquipmentType.setObjectName(_fromUtf8("cmbEquipmentType"))
        self.gridLayout.addWidget(self.cmbEquipmentType, 3, 0, 1, 1)
        self.cmbRegistrationStatus = QtGui.QComboBox(self.grpFilter)
        self.cmbRegistrationStatus.setEnabled(False)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cmbRegistrationStatus.sizePolicy().hasHeightForWidth())
        self.cmbRegistrationStatus.setSizePolicy(sizePolicy)
        self.cmbRegistrationStatus.setObjectName(_fromUtf8("cmbRegistrationStatus"))
        self.gridLayout.addWidget(self.cmbRegistrationStatus, 7, 0, 1, 1)
        self.horizontalLayout.addWidget(self.grpFilter)

        self.retranslateUi(DistantMonitoringEquipmentPage)
        QtCore.QObject.connect(self.chkEquipmentClass, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), self.cmbEquipmentClass.setEnabled)
        QtCore.QObject.connect(self.chkEquipmentType, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), self.cmbEquipmentType.setEnabled)
        QtCore.QObject.connect(self.chkEquipmentStatus, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), self.cmbEquipmentStatus.setEnabled)
        QtCore.QObject.connect(self.chkRegistrationStatus, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), self.cmbRegistrationStatus.setEnabled)
        QtCore.QMetaObject.connectSlotsByName(DistantMonitoringEquipmentPage)
        DistantMonitoringEquipmentPage.setTabOrder(self.tblEquipmentList, self.buttonBoxFilter)

    def retranslateUi(self, DistantMonitoringEquipmentPage):
        DistantMonitoringEquipmentPage.setWindowTitle(_translate("DistantMonitoringEquipmentPage", "Регистрация оборудования", None))
        self.lblRecordCount.setText(_translate("DistantMonitoringEquipmentPage", "Список пуст", None))
        self.grpFilter.setTitle(_translate("DistantMonitoringEquipmentPage", "Фильтр", None))
        self.chkEquipmentType.setText(_translate("DistantMonitoringEquipmentPage", "Модель оборудования", None))
        self.chkEquipmentStatus.setText(_translate("DistantMonitoringEquipmentPage", "Статус оборудования", None))
        self.chkRegistrationStatus.setText(_translate("DistantMonitoringEquipmentPage", "Статус регистрации", None))
        self.chkEquipmentClass.setText(_translate("DistantMonitoringEquipmentPage", "Тип оборудования", None))

from library.DialogButtonBox import CApplyResetDialogButtonBox
from library.TableView import CTableView
from library.crbcombobox import CRBComboBox
