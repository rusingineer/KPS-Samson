# -*- coding: utf-8 -*-


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

class Ui_MedServiceProfilesDialog(object):
    def setupUi(self, MedServiceProfilesDialog):
        MedServiceProfilesDialog.setObjectName(_fromUtf8("MedServiceProfilesDialog"))
        MedServiceProfilesDialog.resize(563, 260)
        self.verticalLayout_2 = QtGui.QVBoxLayout(MedServiceProfilesDialog)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.tblViewMedProfiles = CTableView(MedServiceProfilesDialog)
        self.tblViewMedProfiles.setObjectName(_fromUtf8("tblViewMedProfiles"))
        self.horizontalLayout_2.addWidget(self.tblViewMedProfiles)
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.horizontalLayout_2.addLayout(self.verticalLayout)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.btnSend = QtGui.QPushButton(MedServiceProfilesDialog)
        self.btnSend.setObjectName(_fromUtf8("btnSend"))
        self.horizontalLayout.addWidget(self.btnSend)
        self.btnClose = QtGui.QPushButton(MedServiceProfilesDialog)
        self.btnClose.setObjectName(_fromUtf8("btnClose"))
        self.horizontalLayout.addWidget(self.btnClose)
        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.retranslateUi(MedServiceProfilesDialog)
        QtCore.QObject.connect(self.btnClose, QtCore.SIGNAL(_fromUtf8("clicked()")), MedServiceProfilesDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(MedServiceProfilesDialog)

    def retranslateUi(self, MedServiceProfilesDialog):
        MedServiceProfilesDialog.setWindowTitle(_translate("MedServiceProfilesDialog", "Отправить профиль", None))
        self.btnSend.setText(_translate("MedServiceProfilesDialog", "Передать", None))
        self.btnClose.setText(_translate("MedServiceProfilesDialog", "Закрыть", None))

from library.TableView import CTableView
