# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2017 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

#import email.utils

from PyQt4              import QtGui
from PyQt4.QtCore import Qt, QDate, QEvent, pyqtSignature, SIGNAL, QVariant

from Orgs.Ui_ContractFindComboBoxPopup import Ui_ContractFindComboBoxPopup
from Orgs.Utils import getOrganisationInfo
from library.Utils      import forceInt
from Accounting.Utils   import CContractFindTreeModel


class CIndependentContractFindComboBoxPopup(QtGui.QFrame, Ui_ContractFindComboBoxPopup):
    __pyqtSignals__ = ('ContractFindCodeSelected(int)',
                      )
    def __init__(self, parent = None, filter={}):
        QtGui.QFrame.__init__(self, parent, Qt.Popup)
        self.mainDialog = parent.mainDialog
        self.setFrameShape(QtGui.QFrame.StyledPanel)
        self.setAttribute(Qt.WA_WindowPropagation)
        self.filter = filter
        self.tableModel = CContractFindTreeModel(self, None, self.filter)
        self.tableSelectionModel = QtGui.QItemSelectionModel(self.tableModel, self)
        self.tableSelectionModel.setObjectName('tableSelectionModel')
        self.setupUi(self)
        self.tblContractFind.setModel(self.tableModel)
        self.tblContractFind.setSelectionModel(self.tableSelectionModel)
        self.buttonBox.button(QtGui.QDialogButtonBox.Apply).setDefault(True)
        self.buttonBox.button(QtGui.QDialogButtonBox.Apply).setShortcut(Qt.Key_Return)
        self.tblContractFind.installEventFilter(self)
        self.cmbFinance.setTable('rbFinance', True)
        self.cmbPayer.setAddNone(True, u'не задано')
        self.setDate = self.filter.get('setDate', QDate())
        self.orgId = self.filter.get('orgId', None)
#        self.parent = parent #wtf? скрывать Qt-шный parent - это плохая затея
        pref = QtGui.qApp.preferences
        props = pref.appPrefs
        expand = forceInt(props.get('treeContractsExpand', QVariant()))
        if not expand:
            self.tblContractFind.expandToDepth(0)
        elif expand == 1:
            self.tblContractFind.expandAll()
        else:
            expandLevel = forceInt(props.get('treeContractsExpandLevel', QVariant(1)))
            self.tblContractFind.expandToDepth(expandLevel)

        self.initFilret()
        self.on_buttonBox_apply()


    def mousePressEvent(self, event):
        parent = self.parentWidget()
        if parent is not None:
            opt=QtGui.QStyleOptionComboBox()
            opt.init(parent)
            arrowRect = parent.style().subControlRect(
                QtGui.QStyle.CC_ComboBox, opt, QtGui.QStyle.SC_ComboBoxArrow, parent)
            arrowRect.moveTo(parent.mapToGlobal(arrowRect.topLeft()))
            if (arrowRect.contains(event.globalPos()) or self.rect().contains(event.pos())):
                self.setAttribute(Qt.WA_NoMouseReplay)
        QtGui.QFrame.mousePressEvent(self, event)


    def closeEvent(self, event):
        QtGui.QFrame.closeEvent(self, event)


    def eventFilter(self, watched, event):
        if watched == self.tblContractFind:
            if event.type() == QEvent.KeyPress and event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Select):
                event.accept()
                index = self.tblContractFind.currentIndex()
                self.tblContractFind.emit(SIGNAL('doubleClicked(QModelIndex)'), index)
                return True
        return QtGui.QFrame.eventFilter(self, watched, event)


    def getOrgStructureIdList(self, treeIndex):
        treeItem = treeIndex.internalPointer() if treeIndex.isValid() else None
        return treeItem.getItemIdList() if treeItem else []


    @pyqtSignature('int')
    def on_cmbPayer_currentIndexChanged(self, index):
        self.updatePayerInfo()


    def updatePayerInfo(self):
        id = self.cmbPayer.value()
        orgInfo = getOrganisationInfo(id)
        self.edtPayerINN.setText(orgInfo.get('INN', ''))
        self.edtPayerOGRN.setText(orgInfo.get('OGRN', ''))
        self.cmbPayerAccount.setOrgId(id)


    @pyqtSignature('QAbstractButton*')
    def on_buttonBox_clicked(self, button):
        buttonCode = self.buttonBox.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.on_buttonBox_apply()
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.on_buttonBox_reset()


    def initFilret(self):
        # self.cmbFinance.setValue(self.filter.get('financeId', None))
        self.cmbFinance.setValue(self.filter.get('financeId', self.mainDialog.cmbFinance.value()))
        self.cmbPayer.setValue(self.filter.get('payerId', None))
        self.cmbPayerAccount.setValue(self.filter.get('payerAccountId', None))
        self.edtNumber.setText(self.filter.get('number', ''))
        self.edtGrouping.setText(self.filter.get('grouping', ''))
        self.edtResolution.setText(self.filter.get('resolution', ''))
        self.edtPayerINN.setText(self.filter.get('payerINN', ''))
        self.edtPayerOGRN.setText(self.filter.get('payerOGRN', ''))
        self.edtPayerKBK.setText(self.filter.get('payerKBK', ''))
        self.edtPayerBank.setText(self.filter.get('payerBank', ''))
        currentDate = QDate.currentDate()
        # self.edtBegDate.setDate(self.filter.get('begDate', QDate(currentDate.year(), 1, 1)))
        # self.edtEndDate.setDate(self.filter.get('endDate', QDate(currentDate.year(), 12, 31)))
        self.edtBegDate.setDate(self.filter.get('begDate', self.mainDialog.edtBegDate.date()))
        self.edtEndDate.setDate(self.filter.get('endDate', self.mainDialog.edtEndDate.date()))
        self.cmbEnableInAccounts.setCurrentIndex(self.filter.get('enableInAccounts', 0))


    def on_buttonBox_reset(self):
        self.filter = {}
        currentDate = QDate.currentDate()
        self.cmbFinance.setValue(self.mainDialog.cmbFinance.value())
        self.cmbPayer.setValue(0)
        self.cmbPayerAccount.setValue(0)
        self.edtNumber.setText('')
        self.edtGrouping.setText('')
        self.edtResolution.setText('')
        self.edtPayerINN.setText('')
        self.edtPayerOGRN.setText('')
        self.edtPayerKBK.setText('')
        self.edtPayerBank.setText('')
        self.edtBegDate.setDate(self.mainDialog.edtBegDate.date())
        self.edtEndDate.setDate(self.mainDialog.edtEndDate.date())
        self.cmbEnableInAccounts.setCurrentIndex(0)
        self.tblContractFind.setModel(None)
        self.tableModel = None
        parent = self.parentWidget()
        parent.setModel(None)
        self.on_buttonBox_apply()


    def on_buttonBox_apply(self, id=None):
        self.mainDialog.cmbFinance.setValue(self.cmbFinance.value())
        self.mainDialog.edtBegDate.setDate(self.edtBegDate.date())
        self.mainDialog.edtEndDate.setDate(self.edtEndDate.date())
        self.filter = {}
        self.filter['financeId'] = self.cmbFinance.value()
        self.filter['payerId'] = self.cmbPayer.value()
        self.filter['payerAccountId'] = self.cmbPayerAccount.value()
        self.filter['number'] = self.edtNumber.text()
        self.filter['grouping'] = self.edtGrouping.text()
        self.filter['resolution'] = self.edtResolution.text()
        self.filter['payerINN'] = self.edtPayerINN.text()
        self.filter['payerOGRN'] = self.edtPayerOGRN.text()
        self.filter['payerKBK'] = self.edtPayerKBK.text()
        self.filter['payerBank'] = self.edtPayerBank.text()
        self.filter['orgId'] = self.orgId
        self.filter['begDate'] = self.edtBegDate.date()
        self.filter['endDate'] = self.edtEndDate.date()
        self.filter['enableInAccounts'] = self.cmbEnableInAccounts.currentIndex()
        self.filter['setDate'] = self.setDate
        self.tblContractFind.setModel(None)
        self.tableModel = CContractFindTreeModel(self, None, self.filter)
        self.tblContractFind.setModel(self.tableModel)
        self.tabWidget.setCurrentIndex(0)
        self.tblContractFind.setFocus(Qt.OtherFocusReason)
        parent = self.parentWidget()
        if parent:
            parent._model = self.tableModel
            parent.setModel(parent._model)
        pref = QtGui.qApp.preferences
        props = pref.appPrefs
        expand = forceInt(props.get('treeContractsExpand', QVariant()))
        if not expand:
            self.tblContractFind.expandToDepth(0)
        elif expand == 1:
            self.tblContractFind.expandAll()
        else:
            expandLevel = forceInt(props.get('treeContractsExpandLevel', QVariant(1)))
            self.tblContractFind.expandToDepth(expandLevel)


    @pyqtSignature('QModelIndex')
    def on_tblContractFind_doubleClicked(self, index):
        if index.isValid():
            if index.isValid() and (int(index.flags()) & Qt.ItemIsSelectable) != 0:
                item = index.internalPointer()
                parts = []
                while item:
                    if item.name.lower() != u'Все договоры'.lower():
                        parts.append(item.name)
                    item = item.parent
                path = '\\'.join(parts[::-1])
                parent = self.parentWidget()
                code = forceInt(parent.getIdByPath(path))
                self.emit(SIGNAL('ContractFindCodeSelected(int)'), code)
                self.close()

