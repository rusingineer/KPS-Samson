# -*- coding: utf-8 -*-

#############################################################################
##
## Copyright (C) 2017-2023 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, SIGNAL, pyqtSignature, QDate, QDateTime, QMetaObject, QModelIndex, QTimer

from library.DialogBase       import CConstructHelperMixin
from library.PreferencesMixin import CDialogPreferencesMixin

from library.InDocTable       import CDateInDocTableCol, CInDocTableCol, CRecordListModel
from library.Utils            import forceDouble, forceString, forceRef, withWaitCursor, trim

from Accounting.Utils         import setActionPayStatus, updateAccounts
from Events.Utils             import getPayStatusMaskByCode, CFinanceType, CPayStatus
from Orgs.Utils               import getOrgStructureDescendants


from SumCol          import CSumCol
from Payment         import CPaymentDialog
from RetAccountItems import CRetAccountItemsDialog

from Ui_CashRegister import Ui_CCashRegister


class CCashRegisterWindow(QtGui.QMdiSubWindow, Ui_CCashRegister, CConstructHelperMixin, CDialogPreferencesMixin):
    u"""
    """
    def __init__(self, parent):
        QtGui.QMdiSubWindow.__init__(self, parent)

        self.addModels('Accounts', CAccountsTableModel(self, False))
        self.addModels('PayedAccounts', CAccountsTableModel(self, True))
        self.addObject('accountsUpdateTimer', QTimer(self))

        self.accountsFilter = {}
        self.payedAccountsFilter = {}

        self.internal = QtGui.QWidget(self)
        self.setWidget(self.internal)

        self.setupUi(self.internal)

        self.setModels(self.tblAccounts, self.modelAccounts, self.selectionModelAccounts)
        self.tblAccounts.setSelectionBehavior(self.tblAccounts.SelectRows)
        self.tblAccounts.setSelectionMode(self.tblAccounts.SingleSelection)

        self.setModels(self.tblPayedAccounts, self.modelPayedAccounts, self.selectionModelPayedAccounts)
        self.tblPayedAccounts.setSelectionBehavior(self.tblPayedAccounts.SelectRows)
        self.tblPayedAccounts.setSelectionMode(self.tblPayedAccounts.SingleSelection)

        QMetaObject.connectSlotsByName(self) # т.к. в setupUi параметр не self

        self.resetAccountsFilterWidgets()
        self.fillAccountsFilter()

        self.resetPayedAccountsFilterWidgets()
        self.fillPayedAccountsFilter()

        self.modelAccounts.loadData(self.accountsFilter) # перенести в exec_? или что соответствует exec_ у mdi окон...
        self.modelPayedAccounts.loadData(self.payedAccountsFilter)
        self.tblAccounts.setFocus(Qt.OtherFocusReason)

        self.connect(QtGui.qApp, SIGNAL('deviceStateChaged()'), self.showDeviceState)
        self.showDeviceState()

        self.resetAccountsFilterWidgets()
        self.fillAccountsFilter()
        self.updateAccountsList()


        self.resetPayedAccountsFilterWidgets()
        self.fillPayedAccountsFilter()

        self.accountsUpdateTimer.setInterval(2000)
        self.accountsUpdateTimer.start()


    def showDeviceState(self):
        self.lblModelValue.setText(QtGui.qApp.getDeviceNameOrMessage())
        self.lblOfdExchangeValue.setText(QtGui.qApp.getOfdExchangeMessage())
        self.updateSessionButtons()
        self.updateButtonState()


    def updateSessionButtons(self):
        if QtGui.qApp.getDeviceOk():
            sessionState = QtGui.qApp.device.getSessionState()
            sessionIsOpen = sessionState['state'] != QtGui.qApp.device.ssClosed
            self.btnOpenSession.setEnabled(not sessionIsOpen)
            self.btnCloseSession.setEnabled(sessionIsOpen)
            self.btnPrintDuplicate.setEnabled(True)
            self.tabCash.setEnabled(sessionIsOpen)
        else:
            self.btnOpenSession.setEnabled(False)
            self.btnCloseSession.setEnabled(False)
            self.btnPrintDuplicate.setEnabled(False)
            self.tabCash.setEnabled(False)


    def updateAccountsListExt(self, tblAccounts, accountsFilter):
        currentAccount = tblAccounts.currentItem()
        if currentAccount:
            currentAccountId       = forceRef(currentAccount.value('account_id'))
            currentLocalContractId = forceRef(currentAccount.value('localContract_id'))
            currentColumn          = tblAccounts.currentIndex().column()
        else:
            currentAccountId       = None
            currentLocalContractId = None
            currentColumn          = None

        modelAccounts = tblAccounts.model()
        modelAccounts.updateData(accountsFilter)
        newIndex = modelAccounts.getIndex(currentAccountId, currentLocalContractId, currentColumn)

        tblAccounts.setCurrentIndex( newIndex )
        self.updateButtonState()


    def setFirstAccountAsCurrentExt(self, tblAccounts):
        if tblAccounts.model().rowCount():
            tblAccounts.setCurrentIndex( tblAccounts.model().index(0,0) )
        self.updateButtonState()


    def updateButtonState(self):
        if QtGui.qApp.getDeviceOk():
            ci = self.tblAccounts.currentIndex()
            self.btnCashPayment.setEnabled(ci.isValid())
            self.btnCardPayment.setEnabled(ci.isValid())
            ci = self.tblPayedAccounts.currentIndex()
            self.btnCashRefund.setEnabled(ci.isValid())
            self.btnCardRefund.setEnabled(ci.isValid())
#            self.tabCash.setEnabled(True)
        else:
            self.btnCashPayment.setEnabled(False)
            self.btnCardPayment.setEnabled(False)
            self.btnCashRefund.setEnabled(False)
            self.btnCardRefund.setEnabled(False)
#            self.tabCash.setEnabled(False)


    def extractAccountItems(self, accountId, eventId, payed=False):
        db = QtGui.qApp.db
        tableAccountItem   = db.table('Account_Item')
        tableService       = db.table('rbService')

        table = tableAccountItem
        table = table.innerJoin(tableService, tableService['id'].eq(tableAccountItem['service_id']) )

        cols = [ tableAccountItem['id'].alias('accountItem_id'),
                 tableAccountItem['master_id'].alias('account_id'),
                 tableAccountItem['event_id'],
                 tableAccountItem['action_id'],
                 tableAccountItem['visit_id'],
                 tableAccountItem['serviceDate'],
                 tableService['code'].alias('serviceCode'),
                 tableService['name'].alias('serviceName'),
                 tableAccountItem['price'],
                 tableAccountItem['amount'],
                 tableAccountItem['sum'],
                 tableAccountItem['VAT'],
                 tableAccountItem['payedSum'],
               ]

        cond = [ tableAccountItem['master_id'].eq(accountId),
                 tableAccountItem['deleted'].eq(0),
                 tableAccountItem['reexposeItem_id'].isNull(),
                 tableAccountItem['refuseType_id'].isNull(),
                 tableAccountItem['event_id'].eq(eventId),
               ]

        if payed:
            cond.append( tableAccountItem['date'].isNotNull() )
            cond.append( tableAccountItem['payedSum'].ne(0.0) )
        else:
            cond.append( tableAccountItem['date'].isNull() )
        return db.getRecordList(table, cols = cols, where = cond, order = tableAccountItem['id'].name())


    def extractAccountItemsAndCalcAmount(self, accountId, eventId, payed=False):
        accountItems = self.extractAccountItems(accountId, eventId, payed)
        amount = 0.0
        for record in accountItems:
            amount += round(forceDouble( record.value('sum') ), 2)
        assert amount>=0, 'amount must be >= 0.0'
        return accountItems, amount

    # ##############################


    @withWaitCursor
    def openSession(self):
        self.ensureSessionOpen()
        self.ensureReceiptClosed()


    @withWaitCursor
    def closeSession(self):
        self.ensureReceiptClosed()
        self.ensureSessionClosed()


    @withWaitCursor
    def printDuplicate(self):
        self.ensureReceiptClosed()
        device = QtGui.qApp.device
        device.printLastDocument()
        device.cutReceipt()


    def setFirstAccountAsCurrent(self):
        self.setFirstAccountAsCurrentExt(self.tblAccounts)


    def resetAccountsFilterWidgets(self):
        app = QtGui.qApp
        self.edtAccountContractNumber.setText(app.getContractNumberMask())
        self.edtAccountContractResolution.setText(app.getContractResolutionMask())
        self.edtAccountContractGrouping.setText(app.getContractGroupingMask())
        self.edtAccountNumber.setText(app.getAccountNumberMask())
        today = QDate.currentDate()
        self.edtAccountBegDate.setDate(today.addDays(-31))
        self.edtAccountEndDate.setDate(today)
        self.cmbAccountOrgStructure.setValue(app.getCurrentOrgStructureId())
        self.cmbAccountAuthor.setValue(app.getAuthorId())



    def fillAccountsFilter(self):
        self.accountsFilter = {
                                'contractNumber'     : trim(self.edtAccountContractNumber.text()),
                                'contractResolution' : trim(self.edtAccountContractResolution.text()),
                                'contractGrouping'   : trim(self.edtAccountContractGrouping.text()),

                                'accountNumber'      : trim(self.edtAccountNumber.text()),
                                'begDate'            : self.edtAccountBegDate.date(),
                                'endDate'            : self.edtAccountEndDate.date(),
                                'orgStructureId'     : self.cmbAccountOrgStructure.value(),
                                'authorId'           : self.cmbAccountAuthor.value(),
                              }


    def applyAccountsFilter(self):
        self.fillAccountsFilter()
        self.updateAccountsList()


    def resetAccountsFilter(self):
        self.resetAccountsFilterWidgets()
        self.fillAccountsFilter()
        self.updateAccountsList()


    def updateAccountsList(self):
        self.updateAccountsListExt(self.tblAccounts, self.accountsFilter)


    def ensureReceiptClosed(self):
        device = QtGui.qApp.device
        if device.isReceiptOpen():
            device.cancelReceipt()


    def ensureSessionOpen(self):
        device = QtGui.qApp.device
        sessionState = device.getSessionState()

        if sessionState['state'] == device.ssExpired:
            # если смена просрочена, то закрываем её
            device.closeSession()
            sessionState = device.getSessionState()

        if sessionState['state'] == device.ssClosed:
#            device.setOperatorName(QtGui.qApp.userInfo.name())
            device.openSession()


    def ensureSessionClosed(self):
        device = QtGui.qApp.device
        sessionState = device.getSessionState()
        if sessionState['state'] != device.ssClosed:
            device.closeSession()


    def sell(self, useCard):
        db = QtGui.qApp.db

        currentAccount = self.tblAccounts.currentItem()
        if not currentAccount:
            return

        accountId     = forceRef(currentAccount.value('account_id'))
        eventId       = forceRef(currentAccount.value('event_id'))
        payerName     = forceString(currentAccount.value('payerName')) if QtGui.qApp.getPrintPayer() else None
        email         = forceString(currentAccount.value('email'))
        if QtGui.qApp.getPrintAccountNumber():
            accountDate   = forceString(currentAccount.value('date'))
            accountNumber = forceString(currentAccount.value('number'))
            account       = u'%s от %s' % (accountNumber, accountDate)
        else:
            account       = None
        accountItems, amount = self.extractAccountItemsAndCalcAmount(accountId, eventId)
        if not accountItems or amount == 0.0:
            QtGui.QMessageBox.information(self,
                                          u'Этот чек оплатить нельзя',
                                          u'Чек опустел,\nКасса не рада.\nПопробуй другой')
            return
        if useCard:
            fee = amount
        else:
            dlg = CPaymentDialog(self)
            dlg.setAmount(amount)
            if dlg.exec_() != dlg.Accepted:
                return
            fee = dlg.getFee()

        self.ensureSessionOpen()
        self.ensureReceiptClosed()

        device = QtGui.qApp.device
        device.openReceipt(device.rtSell,
                           payerEmail      = email,
                           payerName       = payerName,
                           customAttrName  = u'Счёт',
                           customAttrValue = account)
        try:
            for record in accountItems:
                serviceCode = forceString(record.value('serviceCode'))
                serviceName = forceString(record.value('serviceName'))
                price       = forceDouble(record.value('price'))
                quantity    = forceDouble(record.value('amount'))
                sum_        = round(forceDouble(record.value('sum')), 2)
                vatPercent  = forceDouble(record.value('VAT'))
                device.register(serviceCode + ' ' +serviceName,
                                price,
                                quantity      = quantity,
                                sum_          = sum_,
                                vatPercent    = vatPercent,
                                section       = 0,
                                paymentObject = device.poService,
                                paymentMethod = device.pmFullPayment, # if fee >= amount else device.pmPartialPayment,
                                checkCache    = True)

            device.pay(device.ptCard if useCard else device.ptCash, fee)

            factoryNumber = device.getFactoryNumber()
            info = device.getSessionInfo()

            db.transaction()
            try:
                self.__markAsPayed(accountItems, '%s.%d.%d' % (factoryNumber, info['sessionNumber'], info['receiptNumber']), useCard)
                device.closeReceipt()
                db.commit()
            except:
                db.rollback()
                raise
        except:
            device.cancelReceipt()
            raise
        if QtGui.qApp.getPrintDuplicate():
            device.printLastDocument()
            device.cutReceipt()
        self.updateSessionButtons()
#        QtGui.QMessageBox.information(self, ':)', ';)' )


    def __markAsPayed(self, accountItems, docNumber, useCard):
        db = QtGui.qApp.db
        tableAccountItem = db.table('Account_Item')
        today = QDate.currentDate()
        payStatusMask = getPayStatusMaskByCode(CFinanceType.cash)

        accountIdSet = set([])
        mapEventIdToSum = {}
        for record in accountItems:
            accountItem = tableAccountItem.newRecord( ['id', 'date', 'number', 'payedSum'] )
            accountItem.setValue('id',       record.value('accountItem_id'))
            accountItem.setValue('date',     today)
            accountItem.setValue('number',   docNumber)
            accountItem.setValue('payedSum', record.value('sum'))
            db.updateRecord(tableAccountItem, accountItem)
            actionId = forceRef(record.value('action_id'))
            if actionId:
               setActionPayStatus(actionId, payStatusMask, CPayStatus.payedBits)
            accountIdSet.add(forceRef(record.value('account_id')))
            eventId = forceRef(record.value('event_id'))
            mapEventIdToSum[eventId] = mapEventIdToSum.get(eventId, 0) + forceDouble(record.value('sum'))
        updateAccounts( accountIdSet )
        self.__addEventsPayment(mapEventIdToSum, False, useCard)


    def __addEventsPayment(self, mapEventIdToSum, isRefund, useCard):
        db = QtGui.qApp.db
        tableEventPayment = db.table('Event_Payment')
        now   = QDateTime.currentDateTime()
        operationId = self.__getCashOperation(isRefund)
        for eventId, sum in mapEventIdToSum.iteritems():
            if eventId and sum != 0:
                record = tableEventPayment.newRecord()
                record.setValue('createDatetime',   now)
                record.setValue('createPerson_id',  QtGui.qApp.userId)
                record.setValue('modifyDatetime',   now)
                record.setValue('modifyPerson_id',  QtGui.qApp.userId)
                record.setValue('master_id',        eventId)
                record.setValue('dateTime',         now)
                record.setValue('cashOperation_id', operationId)
                record.setValue('sum',              sum if not isRefund else -sum)
                record.setValue('typePayment',      1 if useCard else 0)
                record.setValue('cashBox',          QtGui.qApp.getCashBox())
                db.insertRecord(tableEventPayment, record)


    def __getCashOperation(self, isRefund):
        db = QtGui.qApp.db
        tableCashOperation = db.table('rbCashOperation')
        code = '2' if isRefund else '1'
        id = forceRef(db.translate(tableCashOperation, 'code', code, 'id'))
        if id:
            return id
        record = tableCashOperation.newRecord()
        record.setValue('code', code)
        record.setValue('name', u'Возврат' if isRefund else u'Оплата')
        return db.insertRecord(tableCashOperation, record)


# ######################

    def setFirstPayedAccountAsCurrent(self):
        self.setFirstAccountAsCurrentExt(self.tblPayedAccounts)


    def resetPayedAccountsFilterWidgets(self):
        app = QtGui.qApp
        self.edtPayedAccountContractNumber.setText(app.getContractNumberMask())
        self.edtPayedAccountContractResolution.setText(app.getContractResolutionMask())
        self.edtPayedAccountContractGrouping.setText(app.getContractGroupingMask())
        self.edtPayedAccountNumber.setText(app.getAccountNumberMask())
        today = QDate.currentDate()
        self.edtPayedAccountBegDate.setDate(today.addDays(-31))
        self.edtPayedAccountEndDate.setDate(today)
        self.cmbPayedAccountOrgStructure.setValue(app.getCurrentOrgStructureId())
        self.cmbPayedAccountAuthor.setValue(app.getAuthorId())


    def fillPayedAccountsFilter(self):
        self.payedAccountsFilter = {
                                    'contractNumber'     : trim(self.edtPayedAccountContractNumber.text()),
                                    'contractResolution' : trim(self.edtPayedAccountContractResolution.text()),
                                    'contractGrouping'   : trim(self.edtPayedAccountContractGrouping.text()),

                                    'accountNumber'      : trim(self.edtPayedAccountNumber.text()),
                                    'begDate'            : self.edtPayedAccountBegDate.date(),
                                    'endDate'            : self.edtPayedAccountEndDate.date(),
                                    'orgStructureId'     : self.cmbPayedAccountOrgStructure.value(),
                                    'authorId'           : self.cmbPayedAccountAuthor.value(),
                                   }


    def applyPayedAccountsFilter(self):
        self.fillPayedAccountsFilter()
        self.updatePayedAccountsList()


    def resetPayedAccountsFilter(self):
        self.resetPayedAccountsFilterWidgets()
        self.fillPayedAccountsFilter()
        self.updatePayedAccountsList()


    def updatePayedAccountsList(self):
        self.updateAccountsListExt(self.tblPayedAccounts, self.payedAccountsFilter)


    def refund(self, useCard):
        db = QtGui.qApp.db

        currentAccount = self.tblPayedAccounts.currentItem()
        if not currentAccount:
            return

        accountId     = forceRef( currentAccount.value('account_id') )
        eventId       = forceRef( currentAccount.value('event_id') )
        payerName     = forceString(currentAccount.value('payerName')) if QtGui.qApp.getPrintPayer() else None
        email         = forceString(currentAccount.value('email'))
        if QtGui.qApp.getPrintAccountNumber():
            accountDate   = forceString(currentAccount.value('date'))
            accountNumber = forceString(currentAccount.value('number'))
            account       = u'%s от %s' % (accountNumber, accountDate)
        else:
            account       = None

        accountItems = self.extractAccountItems(accountId, eventId, payed=True)
        d = CRetAccountItemsDialog(self)

        d.setAccountNumber( forceString(currentAccount.value('number'))     )
        d.setAccountDate(   forceString(currentAccount.value('date'))       )
        d.setClientName(    forceString(currentAccount.value('clientName')) )
        d.setPayerName(     forceString(currentAccount.value('payerName'))  )
        d.setAccountItems(accountItems)

        if not d.exec_():
            return

        modifiedAaccountItems = []
        amount = 0.0
        for record in accountItems:
            quantity = forceDouble( record.value('retAmount') )
            if quantity:
                amount += round(forceDouble( record.value('retSum') ), 2)
                modifiedAaccountItems.append(record)
        if amount <= 0:
            return


        self.ensureReceiptClosed()
        self.ensureSessionOpen()

        device = QtGui.qApp.device
        device.openReceipt(device.rtSellReturn,
                           payerEmail      = email,
                           payerName       = payerName,
                           customAttrName  = u'Счёт',
                           customAttrValue = account)
        try:
            for record in modifiedAaccountItems:
                serviceCode = forceString( record.value('serviceCode') )
                serviceName = forceString( record.value('serviceName') )
                price       = forceDouble( record.value('price') )
                quantity    = forceDouble( record.value('retAmount') )
                sum_        = round( forceDouble( record.value('retSum') ), 2)
                vatPercent  = forceDouble( record.value('VAT') )
                if quantity>0:
                    device.register(serviceCode + ' ' +serviceName,
                                    price,
                                    quantity      = quantity,
                                    sum_          = sum_,
                                    vatPercent    = vatPercent,
                                    section       = 0,
                                    paymentObject = device.poService,
                                    paymentMethod = device.pmFullPayment,
                                    checkCache    = False)
            device.pay(device.ptCard if useCard else device.ptCash, amount)
            factoryNumber = device.getFactoryNumber()
            info = device.getSessionInfo()
            db.transaction()
            try:
                self.__markAsRefused(modifiedAaccountItems, '%s.%d.%d' % (factoryNumber, info['sessionNumber'], info['receiptNumber']), useCard)
                device.closeReceipt()
                device.cutReceipt()
                db.commit()
            except:
                db.rollback()
                raise
        except:
            device.cancelReceipt()
            raise
        if QtGui.qApp.getPrintDuplicate():
            device.printLastDocument()
            device.cutReceipt()
        self.updateSessionButtons()
#        QtGui.QMessageBox.information(self, ':)', ';)' )


    def __getRefuseTypeId(self):
        db = QtGui.qApp.db
        tablePayRefuseType = db.table('rbPayRefuseType')

        name = u'Отказ от услуги'
        financeId = CFinanceType.getId(CFinanceType.cash)

        cond = [ tablePayRefuseType['name'].eq(name),
                 tablePayRefuseType['finance_id'].eq(financeId),
               ]
        idList = db.getIdList(tablePayRefuseType, 'id', where = cond, order = 'id', limit=1)
        if idList:
            return idList[0]
        record = tablePayRefuseType.newRecord()
        record.setValue('name',       name)
        record.setValue('finance_id', financeId)
        record.setValue('return',     False)
        return db.insertRecord(tablePayRefuseType, record)


    def __markAsRefused(self, accountItems, docNumber, useCard):
        db = QtGui.qApp.db
        tableAccountItem = db.table('Account_Item')
        today = QDate.currentDate()
        payStatusMask = getPayStatusMaskByCode(CFinanceType.cash)

        refuseTypeId = self.__getRefuseTypeId()
        accountIdSet = set([])
        mapEventIdToSum = {}
        for record in accountItems:
            payedSum = round( forceDouble(record.value('payedSum')) - forceDouble(record.value('retSum')), 2)
            if payedSum>0:
                accountItem = tableAccountItem.newRecord( ['id', 'payedSum'] )
            else:
                accountItem = tableAccountItem.newRecord( ['id', 'date', 'number', 'payedSum', 'refuseType_id'] )
                accountItem.setValue('date',          today)
                accountItem.setValue('number',        docNumber)
                accountItem.setValue('refuseType_id', refuseTypeId)
            accountItem.setValue('id',            record.value('accountItem_id'))
            accountItem.setValue('payedSum',      payedSum)
            db.updateRecord(tableAccountItem, accountItem)
            actionId = forceRef(record.value('action_id'))
            if actionId and payedSum<=0:
               setActionPayStatus(actionId, payStatusMask, CPayStatus.refusedBits)
            accountIdSet.add(forceRef(record.value('account_id')))
            eventId = forceRef(record.value('event_id'))
            mapEventIdToSum[eventId] = mapEventIdToSum.get(eventId, 0) + forceDouble(record.value('retSum'))
        updateAccounts( accountIdSet )
        self.__addEventsPayment(mapEventIdToSum, True, useCard)


    def updateCash(self):
        if QtGui.qApp.getDeviceOk():
            cash = QtGui.qApp.device.getCash()
            self.edtCashSum.setValue(cash)


    def putToCash(self):
        val, ok = QtGui.QInputDialog.getDouble(self, u'Внесение денег в кассу', u'Сумма', value=1000.0, min=0.01, max=9999999.99, decimals = 2)
        if ok:
            self.ensureSessionOpen()
            self.ensureReceiptClosed()
            device = QtGui.qApp.device
            device.putToCash(val)
#            device.cutReceipt()
            cash = device.getCash()
            self.edtCashSum.setValue(cash)


    def takeFromCash(self):
        val, ok = QtGui.QInputDialog.getDouble(self, u'Изъятие денег из кассы', u'Сумма', value=1000.0, min=0.01, max=min(9999999.99, self.edtCashSum.value()), decimals = 2)
        if ok:
            self.ensureSessionOpen()
            self.ensureReceiptClosed()
            device = QtGui.qApp.device
            device.takeFromCash(val)
#            device.cutReceipt()
            cash = device.getCash()
            self.edtCashSum.setValue(cash)


    # ######################

    @pyqtSignature('')
    def on_accountsUpdateTimer_timeout(self):
        currentPage = self.tabMain.currentWidget()
        if currentPage == self.tabAccounts:
            self.updateAccountsList()
        elif currentPage == self.tabPayedAccounts:
            self.updatePayedAccountsList()
        self.updateSessionButtons()

    # ######################


    @pyqtSignature('')
    def on_btnOpenSession_clicked(self):
        QtGui.qApp.call(self, self.openSession)


    @pyqtSignature('')
    def on_btnCloseSession_clicked(self):
        QtGui.qApp.call(self, self.closeSession)


    @pyqtSignature('')
    def on_btnPrintDuplicate_clicked(self):
        QtGui.qApp.call(self, self.printDuplicate)


    @pyqtSignature('int')
    def on_tabMain_currentChanged(self, pageIndex):
        currentPage = self.tabMain.currentWidget()
        if currentPage == self.tabAccounts:
            self.updateAccountsList()
            self.accountsUpdateTimer.start()
        elif currentPage == self.tabPayedAccounts:
            self.updatePayedAccountsList()
            self.accountsUpdateTimer.start()
        elif currentPage == self.tabCash:
            self.updateCash()
            self.accountsUpdateTimer.stop()


    # ######################


    @pyqtSignature('QAbstractButton*')
    def on_buttonBoxAccounts_clicked(self, button):
        buttonCode = self.buttonBoxAccounts.standardButton(button)
        if buttonCode == self.buttonBoxAccounts.Apply:
            self.applyAccountsFilter()
        elif buttonCode == self.buttonBoxAccounts.Reset:
            self.resetAccountsFilter()


    @pyqtSignature('')
    def on_modelAccounts_modelReset(self):
        self.setFirstAccountAsCurrent()


    @pyqtSignature('const QModelIndex&, const QModelIndex&')
    def on_selectionModelAccounts_currentChanged(self, current, previous):
        self.updateButtonState()



    @pyqtSignature('')
    def on_btnCashPayment_clicked(self):
        QtGui.qApp.call(self, self.sell, (0,))
#        self.sell(0)


    @pyqtSignature('')
    def on_btnCardPayment_clicked(self):
        QtGui.qApp.call(self, self.sell, (1,))
#        self.sell(1)


    # ######################

    @pyqtSignature('QAbstractButton*')
    def on_buttonBoxPayedAccounts_clicked(self, button):
        buttonCode = self.buttonBoxPayedAccounts.standardButton(button)
        if buttonCode == self.buttonBoxPayedAccounts.Apply:
            self.applyPayedAccountsFilter()
        elif buttonCode == self.buttonBoxPayedAccounts.Reset:
            self.resetPayedAccountsFilter()


    @pyqtSignature('')
    def on_modelPayedAccounts_modelReset(self):
        self.setFirstPayedAccountAsCurrent()


    @pyqtSignature('const QModelIndex&, const QModelIndex&')
    def on_selectionModelPayedAccounts_currentChanged(self, current, previous):
        self.updateButtonState()


    @pyqtSignature('')
    def on_btnCashRefund_clicked(self):
        QtGui.qApp.call(self, self.refund, (0,))


    @pyqtSignature('')
    def on_btnCardRefund_clicked(self):
        QtGui.qApp.call(self, self.refund, (1,))


    # ######################

    @pyqtSignature('')
    def on_btnPutToCash_clicked(self):
        QtGui.qApp.call(self, self.putToCash)


    @pyqtSignature('')
    def on_btnTakeFromCash_clicked(self):
        QtGui.qApp.call(self, self.takeFromCash)

    def closeEvent(self, event):
        self.accountsUpdateTimer.stop()
        self.parent().parent().parent().on_actLogout_triggered()
        pass
        # self._parent.on_actLogout_triggered()
        # QtGui.QWidget.closeEvent(self, event)


########################################################################
#
#
#
########################################################################


#class CSumCol(CFloatInDocTableCol):
#    def _toString(self, value):
#        if value.isNull():
#            return None
#        sum = forceDouble(value)
#        if sum == -0:
#            sum = 0.0
#        return format(sum, '.2f')
#
#
#    def alignment(self):
#        return QVariant(Qt.AlignRight + Qt.AlignVCenter)



class CAccountsTableModel( CRecordListModel ):
    def __init__(self, parent, showPayedItems=False):

        CRecordListModel.__init__(self, parent)
#        self.addCol(CInDocTableCol(     u'id',         'id',         12).setSortable())
        self.addCol(CInDocTableCol(     u'Автор',      'author',     30).setSortable())
        self.addCol(CDateInDocTableCol( u'Дата',       'date',       12, canBeEmpty=True).setSortable())
        self.addCol(CInDocTableCol(     u'Номер',      'number',     12).setSortable())
        self.addCol(CInDocTableCol(     u'Пациент',    'clientName', 40).setSortable())
        self.addCol(CInDocTableCol(     u'Плательщик', 'payerName',  40).setSortable())
        if showPayedItems:
            self.addCol(CSumCol(            u'Оплаченная сумма', 'sum', 12, precision=2).setSortable())
        else:
            self.addCol(CSumCol(            u'Сумма',            'sum', 12, precision=2).setSortable())
        self._lastSortColumn    = None
        self._lastSortAscending = None
        self._showPayedItems    = showPayedItems


    def flags(self, index):
        return Qt.ItemIsSelectable|Qt.ItemIsEnabled


    def __loadData(self, accountFilter):
        db = QtGui.qApp.db
        tableAccount       = db.table('Account')
        tableContract      = db.table('Contract')
        tableRbFinance     = db.table('rbFinance')
        tableAccountItem   = db.table('Account_Item')
        tableEvent         = db.table('Event')
        tableClient        = db.table('Client')
        tableLocalContract = db.table('Event_LocalContract')
        tablePerson        = db.table('vrbPerson')

        table = tableAccount
        table = table.innerJoin(tableContract,     tableContract['id'].eq(tableAccount['contract_id']) )
        table = table.innerJoin(tableRbFinance,    tableRbFinance['id'].eq(tableContract['finance_id']) )
        table = table.innerJoin(tableAccountItem,  tableAccountItem['master_id'].eq(tableAccount['id']) )
        table = table.innerJoin(tableEvent,        tableEvent['id'].eq(tableAccountItem['event_id']) )
        table = table.innerJoin(tableLocalContract,tableLocalContract['master_id'].eq(tableEvent['id']) )
        table = table.innerJoin(tableClient,       tableClient['id'].eq(tableEvent['client_id']) )
        table = table.leftJoin(tablePerson,        tablePerson['id'].eq(tableAccount['createPerson_id']))

        cols = [ tableAccount['id'].alias('account_id'),
                 tableEvent['id'].alias('event_id'),
                 tableLocalContract['id'].alias('localContract_id'),
                 tablePerson['name'].alias('author'),
                 tableAccount['date'],
                 tableAccount['number'],
                 'CONCAT(Client.lastName,\' \', Client.firstName, \' \', Client.patrName) AS clientName',
                 'CONCAT(Event_LocalContract.lastName,\' \', Event_LocalContract.firstName, \' \', Event_LocalContract.patrName) AS payerName',
                 'SUM(%s) AS sum' % tableAccountItem['payedSum' if self._showPayedItems else 'sum' ].name()
               ]
        if tableLocalContract.hasField('email'):
            cols.append( tableLocalContract['email'] )

        contractNumber     = accountFilter.get('contractNumber')
        contractResolution = accountFilter.get('contractResolution')
        contractGrouping   = accountFilter.get('contractGrouping')
        accountNumber      = accountFilter.get('accountNumber')
        endDate = accountFilter.get('endDate') or QDate.currentDate()
        begDate = accountFilter.get('begDate') or endDate
        orgStructureId     = accountFilter.get('orgStructureId')
        authorId           = accountFilter.get('authorId')

        cond = [ tableAccount['deleted'].eq(0),
                 tableAccountItem['deleted'].eq(0),
                 tableAccountItem['date'].isNotNull() if self._showPayedItems else tableAccountItem['date'].isNull(),
                 tableAccountItem['refuseType_id'].isNull(),
                 tableAccountItem['reexposeItem_id'].isNull(),
                 tableEvent['deleted'].eq(0),
                 tableLocalContract['deleted'].eq(0),
                 tableRbFinance['code'].eq( CFinanceType.cash ),
                 tableAccount['date'].ge( begDate  ),
                 tableAccount['date'].le( endDate  ),
               ]
        if self._showPayedItems:
            cond.append(tableAccountItem['payedSum'].ne(0.0))
        if contractNumber:
            cond.append( tableContract['number'].like(contractNumber) )
        if contractResolution:
            cond.append( tableContract['resolution'].like(contractResolution) )
        if contractGrouping:
            cond.append( tableContract['grouping'].like(contractGrouping) )
        if accountNumber:
            cond.append( tableAccount['number'].like(accountNumber) )
        if orgStructureId:
            cond.append( tableAccount['orgStructure_id'].inlist(getOrgStructureDescendants(orgStructureId)) )
        else:
            cond.append( tableAccount['orgStructure_id'].isNull() )
        if authorId:
            cond.append( tableAccount['createPerson_id'].eq(authorId) )

        return db.getRecordListGroupBy(table,
                                       cols = cols,
                                       where = cond,
                                       group = 'Account.id, Event_LocalContract.id',
                                       order = 'Account.date, Account.number'
                                      )

    def loadData(self, accountFilter={}):
        self._items = self.__loadData(accountFilter)
        self.reset()


    def __sortData(self, items, column, ascending):
        col = self._cols[column]
        items.sort(key = lambda(item): col.toSortString(item.value(col.fieldName()), item), reverse = not ascending)


    def sortData(self, column, ascending):
        self._lastSortColumn = column
        self._lastSortAscending = ascending
        self.__sortData(self._items, column, ascending)
        self.emitRowsChanged(0, len(self._items)-1)
#        CRecordListModel.sortData(self, self._lastSortColumn, self._lastSortAscending)


    def updateData(self, accountFilter={}):
        newItems = self.__loadData(accountFilter)
        if self._lastSortColumn is not None:
            self.__sortData(newItems, self._lastSortColumn, self._lastSortAscending)
        if self._items == newItems:
            return

        # качественный алгоритм сравнения последовательносей имеет сложнось n*m, и сравнимый расход памяти
        # попробуем сэкономить :)

        newAccountIdSet = set( forceRef(item.value('account_id')) for item in newItems )
        oldIdx = newIdx = 0
        while oldIdx<len(self._items) and newIdx<len(newItems):
            oldAccountId = forceRef(self._items[oldIdx].value('account_id'))
            newAccountId = forceRef(newItems[newIdx].value('account_id'))
            if oldAccountId == newAccountId: # оба совпали, пропускаем
                if self._items[oldIdx] != newItems[newIdx]:
                    self._items[oldIdx] = newItems[newIdx]
                    self.emitRowChanged(oldIdx)
                newAccountIdSet.discard(newAccountId)
                oldIdx += 1
                newIdx += 1
            elif oldAccountId in newAccountIdSet: # предполагаем, что в new - новый или перемещённый элемент
                self.insertRecord(oldIdx, newItems[newIdx])
                newAccountIdSet.discard(newAccountId)
                oldIdx += 1 # так как индекс текущей строки изменился
                newIdx += 1 # так как обработан
            else: # предполагаем что в old - выбывший элемент
                self.removeRows(oldIdx, 1)
                # индексы менять не нужно, они остались на месте
        if oldIdx<len(self._items):
            self.removeRows(oldIdx, len(self._items)-oldIdx)
        while newIdx<len(newItems):
            self.addRecord(newItems[newIdx])
            newIdx += 1
    # скрестим пальцы, да?


    def getIndex(self, accountId, localContractId, column):
        if accountId:
            for row, item in enumerate(self._items):
                if (     forceRef(item.value('account_id')) == accountId
                     and forceRef(item.value('localContract_id')) == localContractId
                   ):
                    return self.index(row, column)
        return QModelIndex()
