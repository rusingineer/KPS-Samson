# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2021 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

u"""Расчёты: создание счета по событию"""
from PyQt4                           import QtGui
from PyQt4.QtCore                    import Qt, QDate, QLocale, pyqtSignature

from library.DialogBase              import CDialogBase
from library.PrintInfo               import CInfoContext
from library.PrintTemplates          import ( getPrintAction,
                                              getPrintButton,
                                              applyTemplate,
                                              customizePrintButton,
                                            )
from library.Utils                   import forceRef, formatNum1, forceString, forceDate, forceDouble, toVariant, forceBool

from Accounting.AccountEditDialog    import CAccountEditDialog
from Accounting.AccountInfo          import CAccountInfo, CAccountInfoList
from Accounting.AccountBuilder       import CAccountPool, CAccountBuilder
from Accounting.AccountingDialog     import getAccountItemsTotals, accountantRightList
from Accounting.PayStatusDialog       import CPayStatusDialog
from Accounting.Utils                import ( CAccountsModel,
                                              CAccountItemsModel,
                                              getContractDescr,
                                              clearPayStatus,
                                              updateAccount,
                                              updateAccounts, 
                                              updateDocsPayStatus
                                            )

from Events.EventInfo                import CEventInfo
from Events.TempInvalidInfo          import CTempInvalidInfo
from Events.Utils                    import ( CFinanceType,
                                              getEventContext,
                                              getPayStatusMaskByCode,
                                              CPayStatus
                                            )

from Accounting.Ui_InstantAccountDialog import Ui_InstantAccountDialog



def createInstantAccount(eventId, onlyCash = True):
    # создать счёт по действиям события
    db = QtGui.qApp.db
    tableAction = db.table('Action')
    tableEvent = db.table('Event')
    tableContract = db.table('Contract')
    tableFinance = db.table('rbFinance')

    table = tableAction.leftJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))
    table = table.leftJoin(tableContract, 'Contract.id = IF(Action.contract_id IS NULL, Event.contract_id, Action.contract_id)')
    table = table.leftJoin(tableFinance, tableFinance['id'].eq(tableContract['finance_id']))
    cond = [ tableAction['deleted'].eq(0),
             tableAction['event_id'].eq(eventId),
             '(Action.payStatus & %d) = 0' % getPayStatusMaskByCode(CFinanceType.cash)
           ]
    if onlyCash:
        cond.append(tableFinance['code'].eq(CFinanceType.cash))
    mapContractIdToActionIdList = {}
    for record in db.getRecordList(table,
                                   [tableContract['id'].alias('contract_id'),
                                    tableAction['id'].alias('action_id')
                                   ],
                                   cond,
                                  ):
        contractId = forceRef(record.value('contract_id'))
        actionId = forceRef(record.value('action_id'))
        mapContractIdToActionIdList.setdefault(contractId, []).append(actionId)
    accountIdList = []
    db.transaction()
    try:
        today = QDate.currentDate()
        for contractId in sorted(mapContractIdToActionIdList.keys()):
            builder = CAccountBuilder()
            contractDescr = getContractDescr(contractId)
            accountPool = CAccountPool(contractDescr,
                                       QtGui.qApp.currentOrgId(),
                                       QtGui.qApp.currentOrgStructureId(),
                                       today,
                                       False,
                                       {})
            actionIdList = sorted(mapContractIdToActionIdList[contractId])
            builder.exposeByActions(None, contractDescr, accountPool.getAccount, actionIdList, [], today)
            accountPool.updateDetails()
            accountIdList += accountPool.getAccountIdList()
        db.commit()
    except:
        db.rollback()
        raise

    if accountIdList:
        dialog = CInstantAccountDialog(QtGui.qApp.mainWindow, eventId)
        try:
            dialog.setAccountIdList(accountIdList)
            dialog.exec_()
        finally:
            dialog.deleteLater()
    else:
        QtGui.QMessageBox.information( QtGui.qApp.mainWindow,
                                u'Создание счёта по событию',
                                u'Счёт не создан, так как нечего выставлять.',
                                 QtGui.QMessageBox.Ok,
                                 QtGui.QMessageBox.Ok)



class CInstantAccountDialog(CDialogBase, Ui_InstantAccountDialog):
    u"""Использует контекст печати eventAccount, унаследованный от соответствующего event'а и, вдобавок, содержащий переменную 'account' и PrintAction контекста 'account'"""
    def __init__(self, parent, eventId):
        CDialogBase.__init__(self, parent)

        self.currentAccountId = None

        self.setEventId(eventId)

        self.addModels('Accounts', CAccountsModel(self))
        self.addModels('AccountItems', CAccountItemsModel(self))

        self.setupAccountsMenu()
        self.setupAccountItemsMenu()
        self.setupBtnPrintMenu()
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.buttonBox.addButton(self.btnPrint, QtGui.QDialogButtonBox.ActionRole)

        self.tblAccounts.setModel(self.modelAccounts)
        self.tblAccounts.setSelectionModel(self.selectionModelAccounts)
        self.tblAccounts.setPopupMenu(self.mnuAccounts)
        self.tblAccountItems.setModel(self.modelAccountItems)
        self.tblAccountItems.setSelectionModel(self.selectionModelAccountItems)
        self.tblAccountItems.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.tblAccountItems.setPopupMenu(self.mnuAccountItems)
        
        self.payParams = {'date': QDate.currentDate()}



    def setupAccountsMenu(self):
        self.addObject('mnuAccounts', QtGui.QMenu(self))
        self.addObject('actEditAccount', QtGui.QAction(u'Изменить счёт', self))
        self.addObject('actPrintAccount', getPrintAction(self, 'account', u'Печать'))
        self.addObject('actDeleteAccount', QtGui.QAction(u'Удалить счёт', self))
        self.mnuAccounts.addAction(self.actEditAccount)
        self.mnuAccounts.addAction(self.actPrintAccount)
        self.mnuAccounts.addSeparator()
        self.mnuAccounts.addAction(self.actDeleteAccount)


    def setupAccountItemsMenu(self):
        self.addObject('mnuAccountItems', QtGui.QMenu(self))
        self.addObject('actSetPayment', QtGui.QAction(u'Подтверждение оплаты', self))
        self.addObject('actEditPayment', QtGui.QAction(u'Изменение подтверждения оплаты', self))
        self.addObject('actSelectAll', QtGui.QAction(u'Выбрать все', self))
        self.addObject('actDeleteAccountItems', QtGui.QAction(u'Удалить', self))
        self.mnuAccountItems.addAction(self.actSetPayment)
        self.mnuAccountItems.addAction(self.actEditPayment)
        self.mnuAccountItems.addSeparator()
        self.mnuAccountItems.addAction(self.actSelectAll)
        self.mnuAccountItems.addSeparator()
        self.mnuAccountItems.addAction(self.actPrintAccount)
        self.mnuAccountItems.addSeparator()
        self.mnuAccountItems.addAction(self.actDeleteAccountItems)


    def setupBtnPrintMenu(self):
        self.addObject('btnPrint', getPrintButton(self, 'account', u'Печать'))
        eventTypeId = QtGui.qApp.db.getRecord('Event', 'eventType_id', self.eventId).value(0)
        context = getEventContext(eventTypeId)
        customizePrintButton(self.btnPrint, context)


    def setAccountIdList(self, accountIdList):
        self.tblAccounts.setIdList(accountIdList)


    def setEventId(self, eventId):
        self.eventId = eventId


    def editCurrentAccount(self):
        dialog = CAccountEditDialog(self)
        try:
            id = self.tblAccounts.currentItemId()
            if id:
                dialog.load(id)
                if dialog.exec_():
                    self.modelAccounts.invalidateRecordsCache()
                    self.modelAccounts.reset()
        finally:
            dialog.deleteLater()


    def printCurrentAccount(self, templateId):
        context = CInfoContext()
        accountInfo = context.getInstance(CAccountInfo, self.currentAccountId)
        accountInfo.selectedItemIdList = self.modelAccountItems.idList()
        eventInfo = context.getInstance(CEventInfo, self.eventId)
        clientInfo = eventInfo.client
        tempInvalidInfo = context.getInstance(CTempInvalidInfo, None)
        data = { 'account' : accountInfo,
                 'event': eventInfo,
                 'client': clientInfo,
                 'tempInvalid': tempInvalidInfo
               }
        applyTemplate(self, templateId, data)


    def updateAccounts(self):
        accountId = self.currentAccountId
        self.modelAccounts.invalidateRecordsCache()
        self.modelAccounts.reset()
        self.tblAccounts.setCurrentItemId(accountId)


    def updateAccountInfo(self):
        db = QtGui.qApp.db
        table = db.table('Account_Item')
        idList = db.getIdList(table, 'id', table['master_id'].eq(self.currentAccountId), 'id')
        currentAccountItemId = self.tblAccountItems.currentItemId()
        self.modelAccountItems.setIdList(idList)
        self.tblAccountItems.setCurrentItemId(currentAccountItemId)
        self.updateAccountItemsPanel(idList)


    def updateAccountItemsPanel(self, idList):
        count, totalSum, exposedSum, payedSum, refusedSum, totalPayed, totalRefused, totalClientsCount, totalEventsCount, totalActionsCount, totalVisitsCount = getAccountItemsTotals(idList)
        locale = QLocale()
        self.edtAccountItemsCount.setText(locale.toString(count))
        self.edtAccountItemsSum.setText(     locale.toString(totalSum, 'f', 2))
        self.edtAccountItemsPayed.setText(   locale.toString(totalPayed, 'f', 2))
        self.edtAccountItemsRefused.setText( locale.toString(totalRefused, 'f', 2))


    @pyqtSignature('QModelIndex')
    def on_tblAccounts_doubleClicked(self, index):
        self.editCurrentAccount()


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelAccounts_currentRowChanged(self, current, previous):
        self.currentAccountId = self.tblAccounts.itemId(current)
        self.updateAccountInfo()


    @pyqtSignature('')
    def on_mnuAccounts_aboutToShow(self):
        currentRow = self.tblAccounts.currentIndex().row()
        itemPresent = currentRow >= 0
        self.actEditAccount.setEnabled(itemPresent)
        self.actPrintAccount.setEnabled(itemPresent)
        self.actDeleteAccount.setEnabled(itemPresent)


    @pyqtSignature('')
    def on_actEditAccount_triggered(self):
        self.editCurrentAccount()


    @pyqtSignature('int')
    def on_actPrintAccount_printByTemplate(self, templateId):
        self.printCurrentAccount(templateId)


    @pyqtSignature('')
    def on_mnuAccountItems_aboutToShow(self):
        currentRow = self.tblAccountItems.currentIndex().row()
        itemPresent = currentRow >= 0
        self.actSetPayment.setEnabled(itemPresent)
        self.actEditPayment.setEnabled(itemPresent)
        self.actSelectAll.setEnabled(self.currentAccountId is not None)
        self.actPrintAccount.setEnabled(itemPresent)
        self.actDeleteAccountItems.setEnabled(itemPresent)


    @pyqtSignature('')
    def on_actSetPayment_triggered(self):
        isAccountant = QtGui.qApp.userHasAnyRight(accountantRightList)
        if isAccountant:
            contractId = forceRef(QtGui.qApp.db.translate(
                'Account',  'id', self.currentAccountId, 'contract_id'))
            financeId  = forceRef(QtGui.qApp.db.translate('Contract', 'id', contractId, 'finance_id'))
            itemIdList = self.tblAccountItems.selectedItemIdList()
            if itemIdList:
                dialog = CPayStatusDialog(self, financeId)
                try:
                    dialog.setAccountItemsCount(len(itemIdList))
                    dialog.setParams(self.payParams)
                    if dialog.exec_():
                        self.payParams = dialog.params()
                        self.setPayStatus(getContractDescr(contractId), itemIdList, self.payParams)
                finally:
                    dialog.deleteLater()


    @pyqtSignature('')
    def on_actEditPayment_triggered(self):
        isAccountant = QtGui.qApp.userHasAnyRight(accountantRightList)
        if isAccountant:
            contractId = forceRef(QtGui.qApp.db.translate(
                'Account',  'id', self.currentAccountId, 'contract_id'))
            financeId  = forceRef(QtGui.qApp.db.translate('Contract', 'id', contractId, 'finance_id'))
            accountItemId = self.tblAccountItems.currentItemId()
            if accountItemId:
                itemRecord = self.modelAccountItems.recordCache().get(accountItemId)
                payParams = {}
                payParams['date'] = forceDate(itemRecord.value('date'))
                payParams['number'] = forceString(itemRecord.value('number'))
                payParams['refuseTypeId'] = forceRef(itemRecord.value('refuseType_id'))
                payParams['factPayedSum'] = forceDouble(itemRecord.value('payedSum'))
                payParams['accepted'] = payParams['refuseTypeId'] is None
                payParams['note'] = forceString(itemRecord.value('note'))
                dialog = CPayStatusDialog(self, financeId)
                try:
                    dialog.setAccountItemsCount(1)
                    dialog.setParams(payParams)
                    if dialog.exec_():
                        self.payParams = dialog.params()
                        self.setPayStatus(getContractDescr(contractId), [accountItemId], self.payParams)
                finally:
                    dialog.deleteLater()


    def setPayStatus(self, contractDescr, accountItemIdList, payParams):
        date = toVariant(payParams.get('date', QDate()))
        number = toVariant(payParams.get('number', ''))
        note = toVariant(payParams.get('note', ''))
        accepted = forceBool(payParams.get('accepted', False))
        factPayed = forceBool(payParams.get('factPayed', False))
        dateQDate = forceDate(date)
        numberString = forceString(number)
        factPayedSum = 0
        if payParams.get('accepted', True):
            refuseTypeId = toVariant(None)
            if date.isNull() or number.isNull():
                bits = CPayStatus.exposedBits
            else:
                bits = CPayStatus.payedBits
        else:
            if payParams.get('factPayed', True):
                refuseTypeId = toVariant(None)
                factPayedSum = toVariant(payParams.get('factPayedSum', 0))
                if date.isNull() or number.isNull():
                    bits = CPayStatus.exposedBits
                else:
                    bits = CPayStatus.payedBits
            else:
                refuseTypeId = toVariant(payParams.get('refuseTypeId', None))
                bits = CPayStatus.refusedBits

        db = QtGui.qApp.db
        table = db.table('Account_Item')
        tableAccount = db.table('Account')
        db.transaction()
        try:
            accountIdSet = set()
            items = db.getRecordList(
                table,
                'id, master_id, event_id, visit_id, action_id, eventCSG_id, date, number, refuseType_id, reexposeItem_id, note, payedSum, sum',
                where=table['id'].inlist(accountItemIdList))
            for item in items:
                reexposed = not item.isNull('reexposeItem_id')
                emptyDateOrNumber = item.isNull('date') or item.value('number').toString().isEmpty()
                if reexposed and not emptyDateOrNumber:
                    QtGui.QMessageBox.critical(self,
                        u'Внимание!',
                        u'Нельзя изменить данные о подтверждении для перевыставленных записей реестра.',
                        QtGui.QMessageBox.Ok,
                        QtGui.QMessageBox.Ok)
                else:
                    masterId = forceRef(item.value('master_id'))
                    settleDate = None
                    if masterId:
                        recordAccount = db.getRecordEx(tableAccount, [tableAccount['settleDate']], [tableAccount['deleted'].eq(0), tableAccount['id'].eq(masterId)])
                        settleDate = forceDate(recordAccount.value('settleDate')) if recordAccount else None
                    if (numberString or not accepted or dateQDate) and (settleDate and settleDate > dateQDate):
                        QtGui.QMessageBox.critical(self,
                        u'Внимание!',
                        u'Дата подтверждения оплаты (%s) не может быть раньше расчётной даты счёта (%s).'%(dateQDate.toString('dd.MM.yyyy'), settleDate.toString('dd.MM.yyyy')),
                        QtGui.QMessageBox.Ok,
                        QtGui.QMessageBox.Ok)
                        break
                    else:
                        if factPayed and (forceDouble(item.value('sum'))<forceDouble(factPayedSum)):
                            res = QtGui.QMessageBox.warning(None,
                            u'Внимание!',
                            u'Указанная оплаченая сумма превышает выставленную. Установить оплаченую сумму в %s руб?' %forceString(factPayedSum),
                            QtGui.QMessageBox.Ok|QtGui.QMessageBox.Cancel,
                            QtGui.QMessageBox.Cancel)
                            if res == QtGui.QMessageBox.Cancel:
                                break
                        item.setValue('date', date)
                        item.setValue('number', number)
                        if accepted and dateQDate:
                            item.setValue('payedSum', forceDouble(item.value('sum')))
                        else:
                            item.setValue('payedSum', 0)
                        if not reexposed and not factPayed:
                            item.setValue('refuseType_id', refuseTypeId)
                        if factPayed:
                            item.setValue('payedSum', factPayedSum)
                            item.setValue('refuseType_id', refuseTypeId)
                        self.updateDocsPayStatus(item, contractDescr, bits)
                        item.setValue('note', note)
                        db.updateRecord(table, item)
                        accountId = forceRef(item.value('master_id'))
                        accountIdSet.add(accountId)
            updateAccounts(accountIdSet)
            db.commit()
            currentAccountItemId = self.tblAccountItems.currentItemId()
            self.updateAccounts()
            self.updateAccountInfo()
            self.modelAccountItems.invalidateRecordsCache()
            self.tblAccountItems.setCurrentItemId(currentAccountItemId)
        except:
            db.rollback()
            QtGui.qApp.logCurrentException()
            raise


    def updateDocsPayStatus(self,  accountItem, contractDescr, bits):
        updateDocsPayStatus(accountItem, contractDescr.payStatusMask, bits)


    @pyqtSignature('')
    def on_actSelectAll_triggered(self):
        self.tblAccountItems.selectAll()


    @pyqtSignature('')
    def on_actDeleteAccount_triggered(self):
        self.tblAccounts.removeCurrentRow()


    @pyqtSignature('')
    def on_actDeleteAccountItems_triggered(self):
        db = QtGui.qApp.db
        table = db.table('Account_Item')
        selectedItemIdList = self.tblAccountItems.selectedItemIdList()
        cond=[table['id'].inlist(selectedItemIdList), table['date'].isNotNull(), table['number'].ne('')]
        itemIdList = db.getIdList(table, where=cond)
        if itemIdList:
            QtGui.QMessageBox.critical( self,
                                       u'Внимание!',
                                       u'Подтверждённые записи реестра не подлежат удалению',
                                       QtGui.QMessageBox.Close)
        else:
            n = len(selectedItemIdList)
            message = u'Вы действительно хотите удалить %s реестра? ' % formatNum1(n, (u'запись', u'записи', u'записей'))
            if QtGui.QMessageBox.question( self,
                                       u'Внимание!',
                                       message,
                                       QtGui.QMessageBox.Yes|QtGui.QMessageBox.No,
                                       QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes:

                QtGui.qApp.setWaitCursor()
                try:
                    db.transaction()
                    try:
                        clearPayStatus(self.currentAccountId, selectedItemIdList)
                        db.deleteRecord(table, table['id'].inlist(selectedItemIdList))
                        updateAccount(self.currentAccountId)
                        db.commit()
                    except:
                        db.rollback()
                        QtGui.qApp.logCurrentException()
                        raise
                    self.updateAccounts()
                finally:
                    QtGui.qApp.restoreOverrideCursor()


    @pyqtSignature('int')
    def on_btnPrint_printByTemplate(self, templateId):
        context = CInfoContext()
        accountInfo = context.getInstance(CAccountInfo, self.currentAccountId)
        accountInfo.selectedItemIdList = self.tblAccountItems.selectedItemIdList()
        accountInfoList = context.getInstance(CAccountInfoList, tuple(self.modelAccounts.idList()))
        data = { 'account' : accountInfo,
                    'accountList' : accountInfoList,
               }
        applyTemplate(self, templateId, data)
