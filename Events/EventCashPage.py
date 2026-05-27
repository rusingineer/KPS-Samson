# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2025 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QDate, QDateTime, QModelIndex, QTime, QVariant, pyqtSignature, SIGNAL

from library.interchange        import getDateEditValue, getLineEditValue, getRBComboBoxValue, getTextEditValue, setDateEditValue, setDatetimeEditValue, setLineEditValue, setRBComboBoxValue, setTextEditValue
from library.DialogBase         import CConstructHelperMixin
from library.InDocTable         import CDateTimeInDocTableCol, CEnumInDocTableCol, CFloatInDocTableCol, CInDocTableCol, CInDocTableModel, CRBInDocTableCol
from library.Utils              import forceBool, forceDouble, forceInt, forceRef, forceString, nameCase, splitDocSerial, toVariant, forceDate
from RefBooks.Tables            import rbCashOperation, rbDocumentType
from Events.Action              import CActionTypeCache
from Events.ActionStatus        import CActionStatus
from Events.ActionsSummaryModel import CAccActionsSummary
from Events.EventInfo           import CEventLocalContractInfo
from Events.Utils import CFinanceType
from Orgs.Orgs                  import CBankInDocTableCol, selectOrganisation
from Events.ClientPayersList    import CClientPayersList
from Registry.Utils import getClientDocument
from Users.Rights import urEditCoordinationAction, urAdmin, urRegTabWriteEventCash,urDeleteEventCashPayments

from Ui_EventCashPage import Ui_EventCashPageWidget


class CEventCashPage(QtGui.QWidget, Ui_EventCashPageWidget, CConstructHelperMixin):
    localContractTableName = 'Event_LocalContract'
    cashOperationTableName = 'rbCashOperation'

    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.addModels('AccActions', CAccActionsSummary(self, True))
        self.addModels('Payments',  CPaymentsModel(self))

        self.setupUi(self)

        self.setModels(self.tblAccActions, self.modelAccActions, self.selectionModelAccActions)
        self.setModels(self.tblPayments, self.modelPayments, self.selectionModelPayments)
        self.cmbDocType.setTable(rbDocumentType, True, 'group_id IN (SELECT id FROM rbDocumentTypeGroup WHERE code=\'1\')')
        self.cmbCustomerDocType.setTable(rbDocumentType, True, 'group_id IN (SELECT id FROM rbDocumentTypeGroup WHERE code=\'1\')')

        self.tabCoordination.setFocusProxy(self.grpLocalContract)
        self.tabActionsAndCash.setFocusProxy(self.tblAccActions)
        self.tblAccActions.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)

        if QtGui.qApp.userHasRight(urDeleteEventCashPayments):
            self.tblPayments.addPopupDelRow()
        self.tblAccActionsPrepareColumns()
        self.tblAccActions.enableColsHide()
        self.tblAccActions.enableColsMove()

        if QtGui.qApp.refundRegistrationEnabled():
            self.actRefund = QtGui.QAction(u'Оформить возврат', self)
            self.tblAccActions.addPopupAction(self.actRefund)
            self.actRefund.triggered.connect(self.on_actRefund)
            self.modelAccActions.setPaymentItems(self.modelPayments.items())
            self.connect(self.modelPayments, SIGNAL('sumChanged()'), self.on_sumChanged)
            self.connect(self.modelAccActions, SIGNAL('dataChanged(QModelIndex, QModelIndex)'), self.on_modelAccActionsChanged)
            self.modelAccActions.setPaymentItemsEmptyRecord(self.modelPayments.getEmptyRecord())
        
        self.actOpenAccounting = QtGui.QAction(u'Перейти к счетам', self)
        self.tblAccActions.addPopupAction(self.actOpenAccounting)
        self.actOpenAccounting.triggered.connect(self.on_actOpenAccounting)

        self.eventEditor = None
        self.localContractRecord = None
        self.windowTitle = u''
        self.setEnabled(QtGui.qApp.userHasRight(urAdmin) or QtGui.qApp.userHasRight(urRegTabWriteEventCash))
        self.edtDocDate.setDate(QDate())
        self.edtBirthDate.setDate(QDate())
        self.edtCustomerBirthDate.setDate(QDate())
        self.edtCustomerDocDate.setDate(QDate())
        self.isProtected = False


    def on_actOpenAccounting(self):
        items = self.tblAccActions.getSelectedItems()
        for item in items:
            eventId = forceInt(item.value('event_id'))
            break
        self.showAccountingDialog(eventId)


    def showAccountingDialog(self, eventId=None, actionId=None, visitId=None):
        QtGui.qApp.setWaitCursor()
        from Accounting.AccountingDialog            import CAccountingDialog
        dlg = CAccountingDialog(self)
        dlg.setWatchingFields(eventId, actionId, visitId)
        QtGui.qApp.restoreOverrideCursor()
        dlg.exec_()
        self.modelAccActions.emitAllChanged()


    def on_modelAccActionsChanged(self, index1, index2):
        self.modelPayments.setItems(self.modelAccActions.paymentItems)
        self.modelPayments.emitAllChanged()
        self.updatePaymentsSum()


    def on_sumChanged(self):
        self.modelAccActions.setPaymentItems(self.modelPayments.items())


    def on_actRefund(self):
        items = self.tblAccActions.getSelectedItems()
        paymentItems = self.modelPayments.items()
        if self.generateRefund():
            for item in items:
                financeId = forceInt(item.value('finance_id'))
                payStatus = forceInt(item.value('payStatus'))
                cashOperationId = self.getRefundCashOperationId()
                if payStatus and financeId == CFinanceType.getId(CFinanceType.cash):
                    paymentItemSum = None
                    refundSum = - forceDouble(item.value('sum'))
                    for paymentItem in paymentItems:
                        if forceDate(paymentItem.value('dateTime')) == QDate.currentDate() and forceDouble(paymentItem.value('sum')) < 0:
                            paymentItemSum = forceDouble(paymentItem.value('sum'))
                            break
                    if paymentItemSum:
                        newSum = refundSum + paymentItemSum
                        paymentItem.setValue('sum', toVariant(newSum))
                        if cashOperationId:
                            paymentItem.setValue('cashOperation_id', toVariant(cashOperationId))
                    else:
                        newRefundRecord = self.modelPayments.getEmptyRecord()
                        newRefundRecord.setValue('sum', toVariant(refundSum))
                        if cashOperationId:
                            newRefundRecord.setValue('cashOperation_id', toVariant(cashOperationId))
                        paymentItems.append(newRefundRecord)
                    item.setValue('status', toVariant(CActionStatus.canceled))
                    
                    widget = QtGui.qApp.activeModalWidget() or QtGui.qApp.mainWindow or None
                    buttons = QtGui.QMessageBox.Yes|QtGui.QMessageBox.No
                    
                    accountChanges = QtGui.QMessageBox.question(widget,
                       u'Внимание!',
                       u'Внести изменения в счет?',
                       buttons,
                       QtGui.QMessageBox.No)
                    if accountChanges == QtGui.QMessageBox.Yes:
                        actionId = forceInt(item.value('id'))
                        financeId = forceInt(item.value('finance_id'))
                        from Accounting.PayStatusDialog       import CPayStatusDialog
                        payStatusDialog = CPayStatusDialog(None, financeId)
                        payStatusDialog.edtNote.setVisible(False)
                        payStatusDialog.lblNote.setVisible(False)
                        payStatusDialog.edtFactPayed.setVisible(False)
                        payStatusDialog.rbnFactPayed.setVisible(False)
                        payStatusDialog.rbnRefused.setVisible(False)
                        payStatusDialog.rbnAccepted.setVisible(False)
                        payStatusDialog.edtNumber.setVisible(False)
                        payStatusDialog.lblNumber.setVisible(False)
                        payStatusDialog.edtDate.setVisible(False)
                        payStatusDialog.lblDate.setVisible(False)
                        payStatusDialog.lblPayRefuseType.setEnabled(True)
                        payStatusDialog.cmbRefuseType.setEnabled(True)
                        payStatusDialog.cmbRefuseType.setTable('rbPayRefuseType',
                                addNone=False,
                                filter='finance_id=\'%s\'' % financeId)
                        if payStatusDialog.exec_():
                            refuseTypeId = payStatusDialog.cmbRefuseType.value()
                            if refuseTypeId and actionId:
                                self.modelAccActions.changeAccountItemAmountAndSum(actionId, None, refuseTypeId)
                elif financeId != CFinanceType.getId(CFinanceType.cash):
                    QtGui.QMessageBox.critical( QtGui.qApp.activeModalWidget() or QtGui.qApp.mainWindow or None,
                       u'Внимание!',
                       u'Невозможно оформить возврат. Тип финансирования "%s" не является платными услугами'%(CFinanceType.getNameById(financeId)),
                       QtGui.QMessageBox.Close)
                elif not payStatus:
                    QtGui.QMessageBox.critical( QtGui.qApp.activeModalWidget() or QtGui.qApp.mainWindow or None,
                                   u'Внимание!',
                                   u'Невозможно оформить возврат. Действие не выставлено',
                                   QtGui.QMessageBox.Close)

            self.modelPayments.setItems(paymentItems)
            self.modelPayments.emitAllChanged()
            self.modelAccActions.emitAllChanged()
            self.updatePaymentsSum()


    def generateRefund(self):
        widget = QtGui.qApp.activeModalWidget() or QtGui.qApp.mainWindow or None
        buttons = QtGui.QMessageBox.Yes|QtGui.QMessageBox.No
        result = QtGui.QMessageBox.question(widget,
                                   u'Внимание!',
                                   u'Оформить возврат?',
                                   buttons,
                                   QtGui.QMessageBox.No)
        if result == QtGui.QMessageBox.Yes:
            return True
        else:
            return False

    def getRefundCashOperationId(self):
        cashOperationId = None
        db = QtGui.qApp.db
        table = db.table(self.cashOperationTableName)
        record = db.getRecordEx(table, 'id', table['name'].like(u'Возврат'))
        if record:
            cashOperationId = forceInt(record.value('id'))
        return cashOperationId

    def protectFromEdit(self, isProtected):
        self.isProtected = isProtected
        editWidgets = [self.edtAPCoordDate,
                       self.edtAPCoordTime,
                       self.edtAPCoordAgent,
                       self.edtAPCoordInspector,
                       self.edtAPCoordText,
                       self.edtCoordDate,
                       self.edtCoordAgent,
                       self.edtCoordAgent,
                       self.edtContractDate,
                       self.edtCoordInspector,
                       self.edtContractNumber,
                       self.edtSumLimit,
                       self.edtLastName,
                       self.edtFirstName,
                       self.edtPatrName,
                       self.edtBirthDate,
                       self.edtDocSerialLeft,
                       self.edtDocSerialRight,
                       self.edtDocNumber,
                       self.edtDocOrigin,
                       self.edtDocDate,
                       self.edtRegAddress,
                       self.edtEmail,
                       self.edtCoordText,
                       self.edtCustomerLastName,
                       self.edtCustomerFirstName,
                       self.edtCustomerPatrName,
                       self.edtCustomerBirthDate,
                       self.edtCustomerDocSerialLeft,
                       self.edtCustomerDocSerialRight,
                       self.edtCustomerDocNumber,
                       self.edtCustomerDocOrigin,
                       self.edtCustomerDocDate,
                       self.edtCustomerRegAddress,
                       self.edtCustomerEmail,
                       self.edtAPDirectionDate,
                       self.edtAPDirectionTime,
                       self.edtAPPlannedEndDate,
                       self.edtAPPlannedEndTime,
                       self.edtAPBegDate,
                       self.edtAPBegTime,
                       self.edtAPOffice,
                       self.edtAPNote,
                       self.edtAPEndDate,
                       self.edtAPEndTime,
                       self.cmbDocType,
                       self.cmbOrganisation,
                       self.cmbCustomerDocType,
                       self.cmbCustomerOrganisation,
                       self.cmbAPSetPerson,
                       self.cmbAPStatus,
                       self.cmbAPPerson
                      ]
        for widget in editWidgets:
            widget.setReadOnly(isProtected)
        editWidgets = [self.btnGetClientInfo,
                       self.btnPrevious,
                       self.btnSelectOrganisation,
                       self.btnPreviousCustomer,
                       self.btnSelectCustomerOrganisation,
                       self.btnGetExternalId,
                       self.chkAPIsUrgent
                      ]
        for widget in editWidgets:
            widget.setEnabled(not isProtected)
        self.modelAccActions.setReadOnly(isProtected)
        self.modelPayments.setReadOnly(isProtected)


    def tblAccActionsPrepareColumns(self):
        horizontalHeader = self.tblAccActions.horizontalHeader()
        #0: тип
        horizontalHeader.hideSection(1) # МКБ
        horizontalHeader.hideSection(2) # Срочный
        horizontalHeader.hideSection(3) # Назначено
        horizontalHeader.showSection(4) # Начато
        horizontalHeader.showSection(5) # Окончено
        horizontalHeader.showSection(6) # Состояние
        horizontalHeader.hideSection(7) # Назначил
        horizontalHeader.hideSection(8) # Выполнил
        horizontalHeader.hideSection(9) # Ассистент
        horizontalHeader.hideSection(10) # Каб
        #11: количество
        horizontalHeader.hideSection(12) # УЕТ
        #13: примечание
        horizontalHeader.moveSection(horizontalHeader.visualIndex(14), 0) # считать
        horizontalHeader.moveSection(horizontalHeader.visualIndex(0),  1) # тип
        horizontalHeader.moveSection(horizontalHeader.visualIndex(20), 2) # услуга
        horizontalHeader.moveSection(horizontalHeader.visualIndex(17), 3) # тип финансирования
        horizontalHeader.moveSection(horizontalHeader.visualIndex(18), 4) # договор
        horizontalHeader.moveSection(horizontalHeader.visualIndex(11), 5) # количество
        horizontalHeader.moveSection(horizontalHeader.visualIndex(15), 6) # цена
        horizontalHeader.moveSection(horizontalHeader.visualIndex(16), 7) # сумма
        horizontalHeader.moveSection(horizontalHeader.visualIndex(19), 8) # отметки финансирования
        horizontalHeader.moveSection(horizontalHeader.visualIndex(13), 9) # примечание


    def setEventEditor(self, eventEditor):
        self.eventEditor = eventEditor
        self.modelAccActions.setEventEditor(eventEditor)


    def addActionModel(self, model):
        self.modelAccActions.addModel(model)


    def destroy(self):
        self.tblAccActions.setModel(None)
        self.tblPayments.setModel(None)
        del self.modelAccActions
        del self.modelPayments


    def load(self, eventId):
        self.loadLocalContract(eventId)
        self.modelPayments.loadItems(eventId)
        self.modelAccActions.addExtColsFields()
        self.modelAccActions.setCountFlag()
        self.modelAccActions.updatePricesAndSums(0, len(self.modelAccActions.items())-1)


    def loadLocalContract(self, eventId):
        db = QtGui.qApp.db
        table = db.table(self.localContractTableName)
        record = db.getRecordEx(table, '*', table['master_id'].eq(eventId))
        if record:
            self.setLocalContractRecord(record)


    def setLocalContractRecord(self, record):
        self.localContractRecord = record
        self.grpLocalContract.setChecked(forceInt(record.value('deleted'))==0)
        setDateEditValue(self.edtCoordDate, record, 'coordDate')
        setLineEditValue(self.edtCoordAgent, record, 'coordAgent')
        setLineEditValue(self.edtCoordInspector, record, 'coordInspector')
        setTextEditValue(self.edtCoordText, record, 'coordText')
        setDateEditValue(self.edtContractDate, record, 'dateContract')
        setLineEditValue(self.edtContractNumber, record, 'numberContract')
        setLineEditValue(self.edtSumLimit, record, 'sumLimit')
        setLineEditValue(self.edtLastName, record, 'lastName')
        setLineEditValue(self.edtFirstName, record, 'firstName')
        setLineEditValue(self.edtPatrName, record, 'patrName')
        setDateEditValue(self.edtBirthDate, record, 'birthDate')
        setRBComboBoxValue(self.cmbDocType, record, 'documentType_id')
        setLineEditValue(self.edtDocSerialLeft, record, 'serialLeft')
        setLineEditValue(self.edtDocSerialRight, record, 'serialRight')
        setLineEditValue(self.edtDocNumber, record, 'number')
        setLineEditValue(self.edtDocOrigin, record, 'docOrigin')
        setDateEditValue(self.edtDocDate, record, 'docDate')
        setLineEditValue(self.edtRegAddress, record, 'regAddress')
        setRBComboBoxValue(self.cmbOrganisation, record, 'org_id')
        setLineEditValue(self.edtEmail, record, 'email')
        setLineEditValue(self.edtCustomerLastName, record, 'customerLastName')
        setLineEditValue(self.edtCustomerFirstName, record, 'customerFirstName')
        setLineEditValue(self.edtCustomerPatrName, record, 'customerPatrName')
        setDateEditValue(self.edtCustomerBirthDate, record, 'customerBirthDate')
        setRBComboBoxValue(self.cmbCustomerDocType, record, 'customerDocumentType_id')
        setLineEditValue(self.edtCustomerDocSerialLeft, record, 'customerSerialLeft')
        setLineEditValue(self.edtCustomerDocSerialRight, record, 'customerSerialRight')
        setLineEditValue(self.edtCustomerDocNumber, record, 'customerNumber')
        setLineEditValue(self.edtCustomerDocOrigin, record, 'customerDocOrigin')
        setDateEditValue(self.edtCustomerDocDate, record, 'customerDocDate')
        setLineEditValue(self.edtCustomerRegAddress, record, 'customerRegAddress')
        setRBComboBoxValue(self.cmbCustomerOrganisation, record, 'customerOrg_id')
        setLineEditValue(self.edtCustomerEmail, record, 'customerEmail')
        self.grpCustomer.setChecked(forceBool(record.value('customerEnabled')))


    def save(self, eventId):
        self.saveLocalContract(eventId)
        self.modelPayments.saveItems(eventId)


    def saveLocalContract(self, eventId):
        record = self.getLocalContractRecord(eventId)
        QtGui.qApp.db.insertOrUpdate(self.localContractTableName, record)
        self.localContractRecord = record

    def getLocalContractRecord(self, eventId):
        record = self.localContractRecord if self.localContractRecord else QtGui.qApp.db.record(self.localContractTableName)
        record.setValue('master_id', toVariant(eventId))
        record.setValue('deleted', QVariant(0 if self.grpLocalContract.isChecked() else 1))
        record.setValue('customerEnabled', self.grpCustomer.isChecked())

        getDateEditValue(self.edtCoordDate, record, 'coordDate')
        getLineEditValue(self.edtCoordAgent, record, 'coordAgent')
        getLineEditValue(self.edtCoordInspector, record, 'coordInspector')
        getTextEditValue(self.edtCoordText, record, 'coordText')

        getDateEditValue(self.edtContractDate, record, 'dateContract')
        getLineEditValue(self.edtContractNumber, record, 'numberContract')
        getLineEditValue(self.edtSumLimit, record, 'sumLimit')
        getLineEditValue(self.edtLastName, record, 'lastName')
        getLineEditValue(self.edtFirstName, record, 'firstName')
        getLineEditValue(self.edtPatrName, record, 'patrName')
        getDateEditValue(self.edtBirthDate, record, 'birthDate')
        getRBComboBoxValue(self.cmbDocType, record, 'documentType_id')
        getLineEditValue(self.edtDocSerialLeft, record, 'serialLeft')
        getLineEditValue(self.edtDocSerialRight, record, 'serialRight')
        getLineEditValue(self.edtDocNumber, record, 'number')
        getLineEditValue(self.edtDocOrigin, record, 'docOrigin')
        getDateEditValue(self.edtDocDate, record, 'docDate')
        getLineEditValue(self.edtRegAddress, record, 'regAddress')
        getRBComboBoxValue(self.cmbOrganisation, record, 'org_id')
        getLineEditValue(self.edtEmail, record, 'email')

        getLineEditValue(self.edtCustomerLastName, record, 'customerLastName')
        getLineEditValue(self.edtCustomerFirstName, record, 'customerFirstName')
        getLineEditValue(self.edtCustomerPatrName, record, 'customerPatrName')
        getDateEditValue(self.edtCustomerBirthDate, record, 'customerBirthDate')
        getRBComboBoxValue(self.cmbCustomerDocType, record, 'customerDocumentType_id')
        getLineEditValue(self.edtCustomerDocSerialLeft, record, 'customerSerialLeft')
        getLineEditValue(self.edtCustomerDocSerialRight, record, 'customerSerialRight')
        getLineEditValue(self.edtCustomerDocNumber, record, 'customerNumber')
        getLineEditValue(self.edtCustomerDocOrigin, record, 'customerDocOrigin')
        getDateEditValue(self.edtCustomerDocDate, record, 'customerDocDate')
        getLineEditValue(self.edtCustomerRegAddress, record, 'customerRegAddress')
        getRBComboBoxValue(self.cmbCustomerOrganisation, record, 'customerOrg_id')
        getLineEditValue(self.edtCustomerEmail, record, 'customerEmail')
        return record


    def setCashEx(self, externalId, assistantId, curatorId):
        pass


    def enableEditors(self, eventTypeId):
        pass


    def getCash(self, record, eventTypeId):
        pass


    @pyqtSignature('bool')
    def on_grpLocalContract_clicked(self,  checked):
        if checked:
            if not self.edtCoordAgent.text():
                self.edtCoordAgent.setText(getCurrentUserName())
            if not self.edtContractNumber.text():
                self.on_btnGetExternalId_clicked()


    def checkDataLocalContract(self):
        result = True
        if self.grpLocalContract.isChecked():
            eventEditor = self.eventEditor
            dateContract = self.edtContractDate.date()
            birthDate = self.edtBirthDate.date()
            result = result and (dateContract or eventEditor.checkInputMessage(u'дату договора', True, self.edtContractDate))
            result = result and (len(self.edtContractNumber.text()) > 0 or eventEditor.checkInputMessage(u'номер договора', True, self.edtContractNumber))
            result = result and (len(self.edtSumLimit.text()) > 0 or eventEditor.checkInputMessage(u'ограничение суммы', True, self.edtSumLimit))
#            if self.grpFaceJuridical.isChecked():
#                result = result and (len(self.edtNameOrg.text()) > 0 or eventEditor.checkInputMessage(u'название организации', False, self.edtNameOrg))
#                result = result and (len(self.edtOrgINN.text()) > 0 or eventEditor.checkInputMessage(u'ИНН организации', False, self.edtOrgINN))
            result = result and (len(self.edtLastName.text()) > 0 or eventEditor.checkInputMessage(u'фамилию плательщика', False, self.edtLastName))
            result = result and (len(self.edtFirstName.text()) > 0 or eventEditor.checkInputMessage(u'имя плательщика', False, self.edtFirstName))
            from F000.F000Dialog import CF000Dialog
            if type(self.eventEditor) != CF000Dialog:
                result = result and (len(self.edtPatrName.text()) > 0 or eventEditor.checkInputMessage(u'отчество плательщика', True, self.edtPatrName))
                result = result and (birthDate or eventEditor.checkInputMessage(u'дату рождения плательщика', True, self.edtBirthDate))
                result = result and (self.cmbDocType.value() or eventEditor.checkInputMessage(u'тип документа плательщика', True, self.cmbDocType))
                if self.cmbDocType.value():
                    result = result and (len(self.edtDocNumber.text()) > 0 or eventEditor.checkInputMessage(u'номер документа плательщика', True, self.edtDocNumber))
                    result = result and (len(self.edtDocSerialLeft.text()) > 0 or eventEditor.checkInputMessage(u'левую часть серии документа плательщика', True, self.edtDocSerialLeft))
                    result = result and (len(self.edtDocSerialRight.text()) > 0 or eventEditor.checkInputMessage(u'правую часть серии документа плательщика', True, self.edtDocSerialRight))
                result = result and (len(self.edtRegAddress.text()) > 0 or eventEditor.checkInputMessage(u'адрес плательщика', True, self.edtRegAddress))
            if self.grpCustomer.isChecked():
                result = result and (len(self.edtCustomerLastName.text()) > 0 or eventEditor.checkInputMessage(u'фамилию заказчика', False, self.edtCustomerLastName))
                result = result and (len(self.edtCustomerFirstName.text()) > 0 or eventEditor.checkInputMessage(u'имя заказчика', False, self.edtCustomerFirstName))
                if type(self.eventEditor) != CF000Dialog:
                   result = result and (len(self.edtCustomerPatrName.text()) > 0 or eventEditor.checkInputMessage(u'отчество заказчика', True, self.edtCustomerPatrName))
        return result


    def getLocalContractInfo(self, context, eventId):
        result = context.getInstance(CEventLocalContractInfo, eventId)
        if self.grpLocalContract.isChecked():
            result.initByRecord(self.getLocalContractRecord(eventId))
            result.setOkLoaded()
        else:
            result.initByRecord(QtGui.qApp.db.dummyRecord())
            result.setOkLoaded(False)
        return result


    def updatePaymentsSum(self):
        accSum = self.modelAccActions.sum()
        paymentsSum = self.modelPayments.sum()
        self.lblPaymentAccValue.setText('%.2f' % accSum)
        self.lblPaymentPayedSumValue.setText('%.2f' % paymentsSum)
        self.lblPaymentTotalValue.setText('%.2f' % (accSum-paymentsSum))
        palette = QtGui.QPalette()
        if accSum>paymentsSum:
            palette.setColor(QtGui.QPalette.WindowText, QtGui.QColor(255, 0, 0))
        self.lblPaymentTotalValue.setPalette(palette)
        paymentAccValue = self.lblPaymentAccValue.text()
        sumLimit = self.edtSumLimit.text()
        if sumLimit:
            sumLimitInt = sumLimit.toInt()
            if sumLimitInt[1] and sumLimitInt[0] > 0:
                self.eventEditor.setWindowTitle(u'(' + sumLimit + u'/' + paymentAccValue + u') ' + self.windowTitle)


    @pyqtSignature('QString')
    def on_edtSumLimit_textChanged(self, text):
        paymentAccValue = self.lblPaymentAccValue.text()
        sumLimit = self.edtSumLimit.text()
        if sumLimit:
            sumLimitInt = sumLimit.toInt()
            if sumLimitInt[1] and sumLimitInt[0] > 0:
                self.eventEditor.setWindowTitle(u'(' + sumLimit + u'/' + paymentAccValue + u') ' + self.windowTitle)


    def onActionDataChanged(self, name, value):
        model = self.tblAccActions.model()
        items = model.items()
        row = self.tblAccActions.currentIndex().row()
        if 0<=row<len(items):
            record = items[row]
            record.setValue(name, toVariant(value))


    def onCurrentActionChanged(self):
        model = self.modelAccActions
        items = model.items()
        row = self.tblAccActions.currentIndex().row()
        editWidgets = [self.edtAPCoordDate, self.edtAPCoordTime,
                       self.edtAPCoordAgent,
                       self.edtAPCoordInspector,
                       self.edtAPCoordText
                      ]
        if 0<=row<len(items):
            record = items[row]
#            canEdit = not action.isLocked() if action else True
            canEdit = True
            actionTypeId = forceRef(record.value('actionType_id')) if record else None
            actionType = CActionTypeCache.getById(actionTypeId) if actionTypeId else None
            canEdit = (    QtGui.qApp.userHasRight(urEditCoordinationAction)
                       and bool(actionType)
                       and actionType.isRequiredCoordination
                       and not self.isProtected
                      )
            for widget in editWidgets:
                widget.setEnabled(canEdit)
            try:
                for widget in editWidgets:
                    widget.blockSignals(True)
                showTime = actionType.showTime if actionType else False
                self.edtAPDirectionTime.setVisible(showTime)
                self.edtAPPlannedEndTime.setVisible(showTime)
                self.edtAPCoordTime.setVisible(showTime)
                self.edtAPBegTime.setVisible(showTime)
                self.edtAPEndTime.setVisible(showTime)
                setDatetimeEditValue(self.edtAPDirectionDate,    self.edtAPDirectionTime,    record, 'directionDate')
                setDatetimeEditValue(self.edtAPPlannedEndDate,   self.edtAPPlannedEndTime,   record, 'plannedEndDate')
                setDatetimeEditValue(self.edtAPCoordDate, self.edtAPCoordTime, record, 'coordDate')
                self.edtAPCoordAgent.setText(forceString(record.value('coordAgent')))
                self.edtAPCoordInspector.setText(forceString(record.value('coordInspector')))
                self.edtAPCoordText.setText(forceString(record.value('coordText')))
                setDatetimeEditValue(self.edtAPBegDate, self.edtAPBegTime, record, 'begDate')
                setDatetimeEditValue(self.edtAPEndDate, self.edtAPEndTime, record, 'endDate')
                self.cmbAPSetPerson.setValue(forceRef(record.value('setPerson_id')))
                self.cmbAPStatus.setValue(forceInt(record.value('status')))
                self.edtAPOffice.setText(forceString(record.value('office')))
                self.cmbAPPerson.setValue(forceRef(record.value('person_id')))
                self.edtAPNote.setText(forceString(record.value('note')))
            finally:
                for widget in editWidgets:
                    widget.blockSignals(False)
        else:
            for widget in editWidgets:
                widget.setEnabled(False)
            self.edtAPDirectionTime.setVisible(False)
            self.edtAPPlannedEndTime.setVisible(False)
            self.edtAPCoordTime.setVisible(False)
            self.edtAPBegTime.setVisible(False)
            self.edtAPEndTime.setVisible(False)


    @pyqtSignature('QString')
    def on_edtLastName_textChanged(self, str):
        cursorPos = self.edtLastName.cursorPosition()
        self.edtLastName.setText(nameCase(unicode(str)))
        self.edtLastName.setCursorPosition(cursorPos)


    @pyqtSignature('QString')
    def on_edtFirstName_textChanged(self, str):
        cursorPos = self.edtFirstName.cursorPosition()
        self.edtFirstName.setText(nameCase(unicode(str)))
        self.edtFirstName.setCursorPosition(cursorPos)


    @pyqtSignature('QString')
    def on_edtPatrName_textChanged(self, str):
        cursorPos = self.edtPatrName.cursorPosition()
        self.edtPatrName.setText(nameCase(unicode(str)))
        self.edtPatrName.setCursorPosition(cursorPos)


    @pyqtSignature('QString')
    def on_edtRegAddress_textChanged(self, str):
        str.replace(u'спб ',  u'Санкт-Петербург, ')
        if str.length() > 3:
            if str[-2] == ' ' and (str[-3] == ',' or str[-3] == '.'):
                str = str.mid(0,  str.size()-1)+ str[-1].toUpper()
        self.edtRegAddress.setText(str)

    @pyqtSignature('QString')
    def on_edtCustomerLastName_textChanged(self, str):
        cursorPos = self.edtCustomerLastName.cursorPosition()
        self.edtCustomerLastName.setText(nameCase(unicode(str)))
        self.edtCustomerLastName.setCursorPosition(cursorPos)


    @pyqtSignature('QString')
    def on_edtCustomerFirstName_textChanged(self, str):
        cursorPos = self.edtCustomerFirstName.cursorPosition()
        self.edtCustomerFirstName.setText(nameCase(unicode(str)))
        self.edtCustomerFirstName.setCursorPosition(cursorPos)


    @pyqtSignature('QString')
    def on_edtCustomerPatrName_textChanged(self, str):
        cursorPos = self.edtCustomerPatrName.cursorPosition()
        self.edtCustomerPatrName.setText(nameCase(unicode(str)))
        self.edtCustomerPatrName.setCursorPosition(cursorPos)


    @pyqtSignature('QString')
    def on_edtCustomerRegAddress_textChanged(self, str):
        str.replace(u'спб ',  u'Санкт-Петербург, ')
        self.edtCustomerRegAddress.setText(str)


    @pyqtSignature('QDate')
    def on_edtCoordDate_dateChanged(self, date):
        if not self.edtCoordAgent.text():
            self.edtCoordAgent.setText(getCurrentUserName())


    @pyqtSignature('')
    def on_btnGetExternalId_clicked(self):
        self.edtContractNumber.setText(self.eventEditor.getExternalId())


    @pyqtSignature('')
    def on_btnGetClientInfo_clicked(self):
        dialog = CClientPayersList(self, self.eventEditor.clientId, u'Связи')
        if dialog.getCount():
            if not dialog.exec_():
                record, payerOrCustomer = dialog.getSelectedRecord()
                if record:
                    setLineEditValue(self.edtLastName, record, 'lastName')
                    setLineEditValue(self.edtFirstName, record, 'firstName')
                    setLineEditValue(self.edtPatrName, record, 'patrName')
                    setDateEditValue(self.edtBirthDate, record, 'birthDate')
                    setRBComboBoxValue(self.cmbDocType, record, 'documentType_id')
                    serialLeft, serialRight = splitDocSerial(forceString(record.value('serial')))
                    self.edtDocSerialLeft.setText(serialLeft)
                    self.edtDocSerialRight.setText(serialRight)
                    setLineEditValue(self.edtDocNumber, record, 'number')
                    setLineEditValue(self.edtDocOrigin, record, 'origin')
                    setDateEditValue(self.edtDocDate, record, 'date')
                    setLineEditValue(self.edtRegAddress, record, 'regAddress')
        else:
            self.edtLastName.setText(self.eventEditor.clientLastName)
            self.edtFirstName.setText(self.eventEditor.clientFirstName)
            self.edtPatrName.setText(self.eventEditor.clientPatrName)
            self.edtBirthDate.setDate(self.eventEditor.clientBirthDate)

            regAddress = ''
            query = QtGui.qApp.db.query('SELECT getClientRegAddress({0}) AS regAddress'.format(self.eventEditor.clientId))
            while query.next():
                record = query.record()
                regAddress = forceString(record.value('regAddress'))
            self.edtRegAddress.setText(regAddress if regAddress else '')

            documentRecord = getClientDocument(self.eventEditor.clientId)
            if documentRecord:
                setRBComboBoxValue(self.cmbDocType, documentRecord, 'documentType_id')
                serialLeft, serialRight = splitDocSerial(forceString(documentRecord.value('serial')))
                self.edtDocSerialLeft.setText(serialLeft)
                self.edtDocSerialRight.setText(serialRight)
                setLineEditValue(self.edtDocNumber, documentRecord, 'number')
                setLineEditValue(self.edtDocOrigin, documentRecord, 'origin')
                setDateEditValue(self.edtDocDate, documentRecord, 'date')
            else:
                self.cmbDocType.setValue(None)
                self.edtDocSerialLeft.setText('')
                self.edtDocSerialRight.setText('')
                self.edtDocNumber.setText('')
                self.edtDocOrigin.setText('')
                self.edtDocDate.setDate(None)


    @pyqtSignature('')
    def on_btnSelectOrganisation_clicked(self):
        orgId = selectOrganisation(self, self.cmbOrganisation.value(), False)
        self.cmbOrganisation.updateModel()
        if orgId:
            self.cmbOrganisation.setValue(orgId)


    @pyqtSignature('')
    def on_btnSelectCustomerOrganisation_clicked(self):
        orgId = selectOrganisation(self, self.cmbCustomerOrganisation.value(), False)
        self.cmbCustomerOrganisation.updateModel()
        if orgId:
            self.cmbCustomerOrganisation.setValue(orgId)


    @pyqtSignature('')
    def on_btnPrevious_clicked(self):
        def setData(record, payerOrCustomer):
            if payerOrCustomer:
                setLineEditValue(self.edtLastName, record, 'customerLastName')
                setLineEditValue(self.edtFirstName, record, 'customerFirstName')
                setLineEditValue(self.edtPatrName, record, 'customerPatrName')
                setDateEditValue(self.edtBirthDate, record, 'customerBirthDate')
                setRBComboBoxValue(self.cmbDocType, record, 'customerDocumentType_id')
                setLineEditValue(self.edtDocSerialLeft, record, 'customerSerialLeft')
                setLineEditValue(self.edtDocSerialRight, record, 'customerSerialRight')
                setLineEditValue(self.edtDocNumber, record, 'customerNumber')
                setLineEditValue(self.edtDocOrigin, record, 'customerDocOrigin')
                setDateEditValue(self.edtDocDate, record, 'customerDocDate')
                setLineEditValue(self.edtRegAddress, record, 'customerRegAddress')
                setRBComboBoxValue(self.cmbOrganisation, record, 'customerOrg_id')
            else:
                setLineEditValue(self.edtLastName, record, 'lastName')
                setLineEditValue(self.edtFirstName, record, 'firstName')
                setLineEditValue(self.edtPatrName, record, 'patrName')
                setDateEditValue(self.edtBirthDate, record, 'birthDate')
                setRBComboBoxValue(self.cmbDocType, record, 'documentType_id')
                setLineEditValue(self.edtDocSerialLeft, record, 'serialLeft')
                setLineEditValue(self.edtDocSerialRight, record, 'serialRight')
                setLineEditValue(self.edtDocNumber, record, 'number')
                setLineEditValue(self.edtDocOrigin, record, 'docOrigin')
                setDateEditValue(self.edtDocDate, record, 'docDate')
                setLineEditValue(self.edtRegAddress, record, 'regAddress')
                setRBComboBoxValue(self.cmbOrganisation, record, 'org_id')
        dialog = CClientPayersList(self, self.eventEditor.clientId, u'Список плательщиков')
        if not dialog.exec_():
            record, payerOrCustomer = dialog.getSelectedRecord()
            if record:
                setData(record, payerOrCustomer)


    @pyqtSignature('')
    def on_btnPreviousCustomer_clicked(self):
        def setData(record, payerOrCustomer):
            if payerOrCustomer:
                setLineEditValue(self.edtCustomerLastName, record, 'customerLastName')
                setLineEditValue(self.edtCustomerFirstName, record, 'customerFirstName')
                setLineEditValue(self.edtCustomerPatrName, record, 'customerPatrName')
                setDateEditValue(self.edtCustomerBirthDate, record, 'customerBirthDate')
                setRBComboBoxValue(self.cmbCustomerDocType, record, 'customerDocumentType_id')
                setLineEditValue(self.edtCustomerDocSerialLeft, record, 'customerSerialLeft')
                setLineEditValue(self.edtCustomerDocSerialRight, record, 'customerSerialRight')
                setLineEditValue(self.edtCustomerDocNumber, record, 'customerNumber')
                setLineEditValue(self.edtCustomerDocOrigin, record, 'customerDocOrigin')
                setDateEditValue(self.edtCustomerDocDate, record, 'customerDocDate')
                setLineEditValue(self.edtCustomerRegAddress, record, 'customerRegAddress')
                setRBComboBoxValue(self.cmbCustomerOrganisation, record, 'customerOrg_id')
            else:
                setLineEditValue(self.edtCustomerLastName, record, 'lastName')
                setLineEditValue(self.edtCustomerFirstName, record, 'firstName')
                setLineEditValue(self.edtCustomerPatrName, record, 'patrName')
                setDateEditValue(self.edtCustomerBirthDate, record, 'birthDate')
                setRBComboBoxValue(self.cmbCustomerDocType, record, 'documentType_id')
                setLineEditValue(self.edtCustomerDocSerialLeft, record, 'serialLeft')
                setLineEditValue(self.edtCustomerDocSerialRight, record, 'serialRight')
                setLineEditValue(self.edtCustomerDocNumber, record, 'number')
                setLineEditValue(self.edtCustomerDocOrigin, record, 'docOrigin')
                setDateEditValue(self.edtCustomerDocDate, record, 'docDate')
                setLineEditValue(self.edtCustomerRegAddress, record, 'regAddress')
                setRBComboBoxValue(self.cmbCustomerOrganisation, record, 'org_id')

        dialog = CClientPayersList(self, self.eventEditor.clientId, u'Список заказчиков')
        if not dialog.exec_():
            record, payerOrCustomer = dialog.getSelectedRecord()
            setData(record, payerOrCustomer)



    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelAccActions_currentChanged(self, current, previous):
        self.onCurrentActionChanged()


    @pyqtSignature('')
    def on_modelAccActions_modelReset(self):
        if self.modelAccActions.rowCount():
            self.tblAccActions.setCurrentIndex(self.modelAccActions.index(0, 0))
        else:
            self.onCurrentActionChanged()


    @pyqtSignature('QDate')
    def on_edtAPCoordDate_dateChanged(self, date):
        self.edtAPCoordTime.setEnabled(bool(date))
        time = self.edtAPDirectionTime.time() if date and self.edtAPDirectionTime.isVisible() else QTime()
        self.onActionDataChanged('coordDate', QDateTime(date, time))
        if not self.edtAPCoordAgent.text():
            self.edtAPCoordAgent.setText(getCurrentUserName())


    @pyqtSignature('QTime')
    def on_edtAPCoordTime_timeChanged(self, time):
        date = self.edtAPCoordDate.date()
        self.onActionDataChanged('coordDate', QDateTime(date, time if date else QTime()))


    @pyqtSignature('QString')
    def on_edtAPCoordAgent_textChanged(self, text):
        self.onActionDataChanged('coordAgent', text)


    @pyqtSignature('QString')
    def on_edtAPCoordInspector_textChanged(self, text):
        self.onActionDataChanged('coordInspector', text)


    @pyqtSignature('')
    def on_edtAPCoordText_textChanged(self):
        text = self.edtAPCoordText.toPlainText()
        self.onActionDataChanged('coordText', text)


    @pyqtSignature('')
    def on_modelAPActions_amountChanged(self):
        self.updatePaymentsSum()


    @pyqtSignature('')
    def on_modelAccActions_sumChanged(self):
        self.updatePaymentsSum()


    @pyqtSignature('')
    def on_modelPayments_sumChanged(self):
        self.updatePaymentsSum()


class CPaymentsModel(CInDocTableModel):
    __pyqtSignals__ = ('sumChanged()',
                      )

    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'Event_Payment', 'id', 'master_id', parent)
        self._parent = parent
        self.addCol(CInDocTableCol( u'Касса',     'cashBox', 15)).setToolTip(u'').setReadOnly()
        self.addCol(CDateTimeInDocTableCol( u'Дата и время',  'dateTime',    15, canBeEmpty=True)).setToolTip(u'Дата и время платежа')
        self.addCol(CRBInDocTableCol(   u'Операция', 'cashOperation_id', 10, rbCashOperation, addNone=True, preferredWidth=150))
        self.addCol(CFloatInDocTableCol(u'Сумма', 'sum',     15, precision=2)).setToolTip(u'Сумма платежа')
        self.addCol(CEnumInDocTableCol(u'Тип оплаты', 'typePayment', 12,  [u'наличный', u'безналичный', u'по реквизитам']))
        self.addCol(CInDocTableCol(u'Документ об оплате', 'documentPayment', 50))
        self.addCol(CInDocTableCol(u'Расчетный счет',  'settlementAccount',    22))
        self.addCol(CBankInDocTableCol( u'Реквизиты банка', 'bank_id', 22))
        self.addCol(CInDocTableCol(u'Номер кредитной карты',  'numberCreditCard',    22))
        self.readOnly = False
        self.deleteIdList = []


    def setReadOnly(self, value):
        self.readOnly = value


    def flags(self, index):
        if self.readOnly:
           return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return CInDocTableModel.flags(self, index)


    def loadItems(self, eventId):
        CInDocTableModel.loadItems(self, eventId)
        self.emitSumChanged()


    def getEmptyRecord(self):
        result = CInDocTableModel.getEmptyRecord(self)
        result.setValue('cashBox',  toVariant(QtGui.qApp.cashBox()))
        result.setValue('dateTime',     toVariant(QDateTime.currentDateTime()))
        return result


    def setData(self, index, value, role=Qt.EditRole):
        result = CInDocTableModel.setData(self, index, value, role)
        if result and index.column() == 3:
            self.emitSumChanged()
        return result


    def removeRows(self, row, count, parentIndex = QModelIndex()):
        if 0 <= row and row+count <= len(self._items):
            deleteItems = self._items[row:row+count]
            for item in deleteItems:
                deleteItem = forceRef(item.value('id'))
                if deleteItem and deleteItem not in self.deleteIdList:
                    self.deleteIdList.append(deleteItem)
        result = CInDocTableModel.removeRows(self, row, count, parentIndex)
        self.emitSumChanged()
        return result


    def sum(self):
        result = 0.0
        for item in self.items():
            result += forceDouble(item.value('sum'))
        return result


    def emitSumChanged(self):
        self.emit(SIGNAL('sumChanged()'))


    def saveItems(self, masterId):
        if self._items is not None:
            db = QtGui.qApp.db
            table = self._table
            masterId = toVariant(masterId)
            masterIdFieldName = self._masterIdFieldName
            idFieldName = self._idFieldName
            idList = []
            for idx, record in enumerate(self._items):
                record.setValue(masterIdFieldName, masterId)
                if self._idxFieldName:
                    record.setValue(self._idxFieldName, toVariant(idx))
                if self._extColsPresent:
                    outRecord = self.removeExtCols(record)
                else:
                    outRecord = record
                id = db.insertOrUpdate(table, outRecord)
                record.setValue(idFieldName, toVariant(id))
                idList.append(id)
                self.saveDependence(idx, id)
            
            filter = [table[masterIdFieldName].eq(masterId), 
                      '('+table[idFieldName].inlist(self.deleteIdList)+')']
            if self._filter:
                filter.append(self._filter)
            db.deleteRecord(table, filter)


def getCurrentUserName():
    if QtGui.qApp.userInfo:
        return QtGui.qApp.userInfo.name()
    else:
        return ''
