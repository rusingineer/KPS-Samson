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

u'Расчёты: Журнал кассовых операций'

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QDate, QLocale, pyqtSignature, SIGNAL, QObject, QString, QDateTime

from Events.ContractTariffCache import CContractTariffCache
from Resources.JobTypeActionsSelector import CFakeEventEditor
from library.crbcombobox import CRBComboBox
from library.database import CTableRecordCache
from library.DialogBase import CDialogBase
from library.PrintInfo import CInfoContext, CDateInfo, CInfoList, CInfo
from library.PrintTemplates import (CPrintButton,
                                    customizePrintButton,
                                    getPrintAction,
                                    applyTemplate,
                                    )

from library.TableModel import (CTableModel,
                                CCol,
                                CDateCol,
                                CEnumCol,
                                CRefBookCol,
                                CSumCol,
                                CTextCol, 
                                CDateTimeCol,
                                )
from library.Utils import (smartDict, forceDate, forceDouble, forceInt, forceRef, forceString, forceStringEx,
                           formatName, formatSex, toVariant, forceBool, forceDateTime)
from Accounting.CashDialog import CashDialogEditor, printCashOrder
from Events.EditDispatcher import getEventFormClass
from Events.EventInfo import CEventInfo, CCashOperationInfo
from Events.Utils import (getEventName,
                          getEventContext,
                          getEventTypeForm,
                          getWorkEventTypeFilter,
                          orderTexts,
                          )
from Orgs.Utils import (getOrgStructureDescendants,
                        getOrgStructureFullName,
                        )
from Registry.ClientEditDialog  import CClientEditDialog
from Registry.RegistryTable import codeIsPrimary
from Registry.Utils import getClientBanner
from Reports.Report import convertFilterToString
from Users.Rights import (urAdmin,
                          urRegTabWriteEvents,
                          urRegTabWriteRegistry,
                          urRegTabReadRegistry,
                          urAccessCashBookOnlyJournal,
                          urAccessCashBook
                          )

from Accounting.Ui_CashBookDialog import Ui_CashBookDialog


class CCashBookDialog(CDialogBase, Ui_CashBookDialog):
    def __init__(self, parent):
        CDialogBase.__init__(self, parent)
        self.addModels('CashItems', CCashItemsModel(self))
        self.addObject('mnuCashItems', QtGui.QMenu(self))
        self.addObject('actEditClient', QtGui.QAction(u'Открыть регистрационную карточку', self))
        self.addObject('actOpenEvent', QtGui.QAction(u'Открыть первичный документ', self))
        self.addObject('actShowAccount', QtGui.QAction(u'Показать расчёт', self))

        self.mnuCashItems.addAction(self.actEditClient)
        self.mnuCashItems.addAction(self.actOpenEvent)
        self.mnuCashItems.addAction(self.actShowAccount)
        self.addObject('actPrintBook', QtGui.QAction(u'Печать журнала кассовых операций', self))
        self.addObject('actPrintCashBook', getPrintAction(self, 'cashBook', u'Печать журнала по шаблону'))
        self.addObject('actPrintCash', getPrintAction(self, 'cashOrder', u'Печать ордера'))
        self.addObject('mnuPrintCashBook', QtGui.QMenu(self))
        self.addObject('mnuPrintCash', QtGui.QMenu(self))
        self.mnuPrintCash.addAction(self.actPrintBook)
        self.mnuPrintCash.addAction(self.actPrintCashBook)
        self.mnuPrintCash.addAction(self.actPrintCash)
        self.mnuCashItems.addSeparator()
        self.mnuCashItems.addAction(self.actPrintBook)
        self.mnuCashItems.addAction(self.actPrintCashBook)
        self.mnuCashItems.addAction(self.actPrintCash)

        self.addModels('Clients', CClientsModel(self))
        self.addModels('Events', CEventsModel(self))
        self.addObject('actEditClient2', QtGui.QAction(u'Открыть регистрационную карточку', self))
        self.addObject('mnuClients', QtGui.QMenu(self))
        self.mnuClients.addAction(self.actEditClient2)

        self.addObject('actOpenEvent2', QtGui.QAction(u'Открыть первичный документ', self))
        self.addObject('actCash', QtGui.QAction(u'Принять оплату', self))
        self.addObject('mnuEvents', QtGui.QMenu(self))
        self.mnuEvents.addAction(self.actOpenEvent2)
        self.mnuEvents.addAction(self.actCash)
        self.addObject('btnPrintCash',  QtGui.QPushButton(u'Печать', self))
        self.addObject('btnPrintEvent', CPrintButton(self, u'Печать'))
        self.addObject('btnCash',       QtGui.QPushButton(u'Оплата', self))

        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.bbxFilter.button(QtGui.QDialogButtonBox.Apply).setDefault(True)
        self.bbxPaymentFilter.button(QtGui.QDialogButtonBox.Apply).setDefault(True)

        self.buttonBox.addButton(self.btnPrintCash,  QtGui.QDialogButtonBox.ActionRole)
        self.btnPrintCash.setMenu(self.mnuPrintCash)
        self.buttonBox.addButton(self.btnPrintEvent, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnCash, QtGui.QDialogButtonBox.ActionRole)
        self.btnPrintCash.setShortcut('F6')
#        self.btnPrintEvent.setShortcut('F6')
        self.btnCash.setShortcut('F9')

        self.btnPrintEvent.setVisible(False)
        self.btnCash.setEnabled(False)

        self.cmbFilterCashOperation.setTable('rbCashOperation', True)
        self.cmbFilterEventPurpose.setTable('rbEventTypePurpose', True, filter='code != \'0\'')
        self.cmbFilterEventType.setTable('EventType', True, filter=getWorkEventTypeFilter())
        self.cmbFilterPerson.setSpecialityPresent(True)
        self.cmbFilterAssistantPerson.setSpecialityPresent(True)

        self.tblCashItems.setModel(self.modelCashItems)
        self.tblCashItems.setSelectionModel(self.selectionModelCashItems)
        self.tblCashItems.setPopupMenu(self.mnuCashItems)
        QObject.connect(self.tblCashItems.horizontalHeader(), SIGNAL('sectionClicked(int)'), self.setCashItemsSort)

        self.cmbPaymentFilterAccountingSystem.setTable('rbAccountingSystem', True)
        self.txtClientInfoBrowser.actions.append(self.actEditClient2)
        self.tblClients.setModel(self.modelClients)
        self.tblClients.setSelectionModel(self.selectionModelClients)
        self.tblClients.setPopupMenu(self.mnuClients)

        self.tblEvents.setModel(self.modelEvents)
        self.tblEvents.setSelectionModel(self.selectionModelEvents)
        self.tblEvents.setPopupMenu(self.mnuEvents)

        self.filter = smartDict()
        self.paymentFilter = smartDict()
        self.reapplyFilterRequired = False
        self.lastAddedCashItemId = None
        self.isEnabledTabCash()


    def isEnabledTabCash(self):
        if QtGui.qApp.userHasRight(urAccessCashBookOnlyJournal) and not QtGui.qApp.userHasAnyRight((urAccessCashBook, urAdmin)):
            self.tabWidget.setTabEnabled(1, False)
        else:
            self.tabWidget.setTabEnabled(1, True)


    def setCashItemsSort(self, col):
        if col == 6: #ФИО
            headerSortingCol = self.tblCashItems.model().headerSortingCol.get(col, False)
            self.tblCashItems.model().headerSortingCol = {}
            self.tblCashItems.model().headerSortingCol[col] = not headerSortingCol
            self.tblCashItems.model().sortDataModel()


    def exec_(self):
        self.resetFilter()
        self.applyFilter()
        self.resetPaymentFilter()
        self.applyPaymentFilter()
        self.tabWidget.setCurrentIndex(0)
        CDialogBase.exec_(self)


    def resetFilter(self):
        self.edtFilterBegDate.setDate(QDate.currentDate())
        self.edtFilterEndDate.setDate(QDate.currentDate())
        self.edtFilterCashBox.setText(QtGui.qApp.cashBox())
        self.cmbFilterCashKeeper.setValue(None)
        self.cmbFilterCashOperation.setValue(None)
        self.cmbFilterPaymentType.setCurrentIndex(0)
        self.cmbFilterEventPurpose.setValue(None)
        self.cmbFilterEventType.setValue(None)
        self.cmbFilterOrgStructure.setValue(QtGui.qApp.currentOrgStructureId())
        self.cmbFilterPerson.setValue(None)
        self.cmbFilterAssistantPerson.setValue(None)


    def applyFilter(self, currentId=None):
        self.filter.begDate = self.edtFilterBegDate.date()
        self.filter.endDate = self.edtFilterEndDate.date()
        self.filter.cashBox = forceStringEx(self.edtFilterCashBox.text())
        self.filter.cashKeeperId = self.cmbFilterCashKeeper.value()
        self.filter.cashOperationId = self.cmbFilterCashOperation.value()
        paymentTypeIndex = self.cmbFilterPaymentType.currentIndex()
        self.filter.paymentType = paymentTypeIndex-1 if paymentTypeIndex else None
        self.filter.eventPurposeId = self.cmbFilterEventPurpose.value()
        self.filter.eventTypeId = self.cmbFilterEventType.value()
        self.filter.orgStructureId = self.cmbFilterOrgStructure.value()
        self.filter.personId = self.cmbFilterPerson.value()
        self.filter.assistantId = self.cmbFilterAssistantPerson.value()
        self.updateCashItemList(currentId)


    def getFilterAsText(self):
        db = QtGui.qApp.db
        return convertFilterToString(self.filter, [
            ('begDate',         u'Дата оплаты с', forceString),
            ('endDate',         u'Дата оплаты по', forceString),
            ('cashBox',         u'Касса',  forceString),
            ('cashKeeperId',    u'Кассир',
                                lambda id: forceString(db.translate('vrbPerson', 'id', id, 'name'))),
            ('cashOperationId', u'Кассовая операция',
                                lambda id: forceString(db.translate('rbCashOperation', 'id', id, 'name'))),
            ('eventPurposeId',  u'Назначение обращения',
                                lambda id: forceString(db.translate('rbEventTypePurpose', 'id', id, 'name'))),
            ('eventTypeId',     u'Тип обращения', lambda id: getEventName(id)),
            ('orgStructureId',  u'Подразделение врача',
                                lambda id: getOrgStructureFullName(id)),
            ('personId',        u'Врач',
                                lambda id: forceString(db.translate('vrbPersonWithSpeciality', 'id', id, 'name'))),
                   ])

    def getAmountAsText(self):
        return u'Позиций: %s\nПриход: %s\nРасход:%s' % (
                        self.edtCashItemsCount.text(),
                        self.edtIncome.text(),
                        self.edtOutcome.text(),
                        )


    def updateCashItemList(self, currentId=None):
        filter = self.filter
        db = QtGui.qApp.db
        table = db.table('Event_Payment')
        tableEvent = db.table('Event')
        tableEventType = db.table('EventType')
        tablePerson = db.table('Person')
        #tablePerson_E = db.table('Person') нигде вроде не используется
        tablePerson_E1 = tablePerson.alias('pe')
        tableClient = db.table('Client')
        tableEvent_JournalOfPerson = db.table('Event_JournalOfPerson')
        tableEx = table.leftJoin(tableEvent, tableEvent['id'].eq(table['master_id']))
        tableEx = tableEx.leftJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
        tableEx = tableEx.leftJoin(tableEvent_JournalOfPerson, tableEvent_JournalOfPerson['master_id'].eq(tableEvent['id']))
        tableEx = tableEx.leftJoin(tablePerson, tablePerson['id'].eq(tableEvent_JournalOfPerson['execPerson_id']))
        tableEx = tableEx.leftJoin(tablePerson_E1, tablePerson_E1['id'].eq(tableEvent['execPerson_id']))
        tableEx = tableEx.leftJoin(tableClient, tableClient['id'].eq(tableEvent['client_id'])) #tt1424

        cond = [tableEvent['deleted'].eq(0),
                table['deleted'].eq(0),
                table['dateTime'].ge(QDateTime(self.edtFilterBegDate.date())),
                table['dateTime'].lt(QDateTime(self.edtFilterEndDate.date().addDays(1))),
               ]
        cond.append('( Event_JournalOfPerson.id = ( SELECT MAX(id) FROM Event_JournalOfPerson AS ej WHERE Event_Payment.dateTime>=date(ej.setDate) AND ej.master_id = Event.id) OR Event_JournalOfPerson.id IS NULL)')
        if filter.cashBox:
            cond.append(table['cashBox'].eq(filter.cashBox))
        if filter.cashKeeperId:
            cond.append(table['createPerson_id'].eq(filter.cashKeeperId))
        if filter.cashOperationId:
            cond.append(table['cashOperation_id'].eq(filter.cashOperationId))
        if filter.paymentType is not None:
            cond.append(table['typePayment'].eq(filter.paymentType))
        if filter.eventTypeId:
            cond.append(tableEvent['eventType_id'].eq(filter.eventTypeId))
        elif filter.eventPurposeId:
            cond.append(tableEventType['purpose_id'].eq(filter.eventPurposeId))
        if filter.personId:
            cond.append(u'IF(Event_JournalOfPerson.execPerson_id IS NOT NULL AND EXISTS(SELECT * FROM GlobalPreferences gp  WHERE gp.code="26" AND value = "да"), Event_JournalOfPerson.execPerson_id, Event.execPerson_id) = %s' % filter.personId)
        elif filter.orgStructureId:
            orgst = getOrgStructureDescendants(filter.orgStructureId)
            orgst = str(orgst).replace('[', '')
            orgst = orgst.replace(']', '')
            cond.append(u'IF(Person.`orgStructure_id` IS NULL,pe.orgStructure_id,Person.`orgStructure_id`) in (%s)' %(orgst))
        if filter.assistantId:
            cond.append(tableEvent['assistant_id'].eq(filter.assistantId))


        idList = db.getIdList(tableEx, idCol=table['id'], where=cond, order='Client.lastName, Client.firstName, Client.patrName, Event_Payment.dateTime, Event_Payment.id') #tt1424
        record = db.getRecordEx(tableEx, 'COUNT(*), SUM(IF(`sum`>0, `sum`,0)) AS `income`, SUM(IF(`sum`<0,`sum`,0)) AS `outcome`', where=cond)
        if record:
            itemCount = forceInt(record.value(0))
            income    = forceDouble(record.value(1))
            outcome   = -forceDouble(record.value(2))

        self.tblCashItems.setIdList(idList, currentId)
        locale = QLocale()
        self.edtCashItemsCount.setText(locale.toString(itemCount))
        self.edtIncome.setText(locale.toString(income, 'f', 2))
        self.edtOutcome.setText(locale.toString(outcome, 'f', 2))


    def getCurrentClientIdByCashItem(self):
        eventId = self.getCurrentEventIdByCashItem()
        if eventId:
            eventRecord = self.modelCashItems.eventCache.get(eventId)
            if eventRecord:
                return forceRef(eventRecord.value('client_id'))
        return None


    def getCurrentEventIdByCashItem(self):
        itemId = self.tblCashItems.currentItemId()
        if itemId:
            itemRecord = self.modelCashItems.recordCache().get(itemId)
            if itemRecord:
                return forceRef(itemRecord.value('master_id'))
        return None


    def resetPaymentFilter(self):
        self.cmbPaymentFilterAccountingSystem.setValue(None)
        self.edtPaymentFilterClientCode.setText('')
        self.edtPaymentFilterLastName.setText('')
        self.edtPaymentFilterFirstName.setText('')
        self.edtPaymentFilterPatrName.setText('')
        self.edtPaymentFilterBirthDay.setDate(QDate())
        self.cmbPaymentFilterSex.setCurrentIndex(0)
        self.edtPaymentFilterEventId.setText('')
        self.edtPaymentFilterExternalEventId.setText('')


    def applyPaymentFilter(self, currentClientId=None, currentEventId=None):
        self.paymentFilter.accountingSystemId = self.cmbPaymentFilterAccountingSystem.value()
        self.paymentFilter.clientCode = forceStringEx(self.edtPaymentFilterClientCode.text())
        self.paymentFilter.lastName   = forceStringEx(self.edtPaymentFilterLastName.text())
        self.paymentFilter.firstName  = forceStringEx(self.edtPaymentFilterFirstName.text())
        self.paymentFilter.patrName   = forceStringEx(self.edtPaymentFilterPatrName.text())
        self.paymentFilter.birthDay   = self.edtPaymentFilterBirthDay.date()
        self.paymentFilter.sex        = self.cmbPaymentFilterSex.currentIndex()
        self.paymentFilter.eventId    = forceStringEx(self.edtPaymentFilterEventId.text())
        self.paymentFilter.externalEventId = forceStringEx(self.edtPaymentFilterExternalEventId.text())
        self.updateClientList(currentClientId)
        self.updateEventList(currentEventId)


    def updateClientList(self, currentClientId=None):
        filter = self.paymentFilter
        db = QtGui.qApp.db
        table = db.table('Client')
        tableEx = table

        cond = []
        if filter.clientCode:
            if filter.accountingSystemId:
                tableCI = db.table('ClientIdentification')
                tableEx = tableEx.leftJoin(tableCI, [tableCI['client_id'].eq(table['id']),
                                                     tableCI['deleted'].eq(0),
                                                     tableCI['accountingSystem_id'].eq(filter.accountingSystemId),
                                                    ])
                cond.append(tableCI['identifier'].eq(filter.clientCode))
            else:
                cond.append(table['id'].eq(filter.clientCode))

        if filter.lastName:
            cond.append(table['lastName'].like(filter.lastName))
        if filter.firstName:
            cond.append(table['firstName'].like(filter.firstName))
        if filter.patrName:
            cond.append(table['patrName'].like(filter.patrName))
        if filter.birthDay:
            cond.append(table['birthDate'].eq(filter.birthDay))
        if filter.sex:
            cond.append(table['sex'].eq(filter.sex))
        if filter.eventId or filter.externalEventId:
            tableEvent = db.table('Event')
            tableEx = tableEx.leftJoin(tableEvent, [tableEvent['client_id'].eq(table['id']),
                                                    tableEvent['deleted'].eq(0),
                                                ])
            if filter.eventId:
                cond.append(tableEvent['id'].eq(filter.eventId))
            if filter.externalEventId:
                cond.append(tableEvent['externalId'].eq(filter.externalEventId))
        if cond:
            idList = db.getIdList(tableEx, idCol=table['id'], where=cond, order='Client.lastName, Client.firstName, Client.patrName, Client.birthDate, Client.id', limit=10000)
        else:
            idList = []
        self.tblClients.setIdList(idList, currentClientId)
        self.showClientInfo(self.getCurrentClientId())


    def updateEventList(self, currentEventId=None):
        filter = self.paymentFilter
        db = QtGui.qApp.db
        tableEvent = db.table('Event')
        table = tableEvent
        clientId = self.getCurrentClientId()
        if clientId:
            tableEventType = db.table('EventType')
            table = table.leftJoin(tableEventType,  tableEventType['id'].eq(tableEvent['eventType_id']))
            cond = [tableEvent['client_id'].eq(clientId),
                    tableEvent['deleted'].eq(0),
                    getWorkEventTypeFilter()
                   ]
            if filter.eventId:
                cond.append(tableEvent['id'].eq(filter.eventId))
            if filter.externalEventId:
                cond.append(tableEvent['externalId'].eq(filter.externalEventId))
            idList = db.getIdList(table, idCol=tableEvent['id'], where=cond, order='setDate DESC', limit=100)
        else:
            idList = []
        self.tblEvents.setIdList(idList, currentEventId)
        self.btnCash.setEnabled(self.tabWidget.currentIndex()==1 and bool(idList))


    def getCurrentClientId(self):
        return self.tblClients.currentItemId()


    def getCurrentEventId(self):
        return self.tblEvents.currentItemId()


    def openClient(self, clientId):
        if clientId and QtGui.qApp.userHasAnyRight([urAdmin, urRegTabWriteRegistry, urRegTabReadRegistry]):
            dialog = CClientEditDialog(self)
            try:
                dialog.load(clientId)
                self.reapplyFilterRequired = True
                return dialog.exec_()
            finally:
                dialog.deleteLater()


    def openEvent(self, eventId):
        if eventId and QtGui.qApp.userHasAnyRight([urAdmin, urRegTabWriteEvents]):
            formClass = getEventFormClass(eventId)
            dialog = formClass(self)
            try:
                self.reapplyFilterRequired = True
                dialog.load(eventId)
                if dialog.restrictToPayment():
                    dialog.exec_()
            finally:
                dialog.deleteLater()


    def showClientInfo(self, id):
        self.txtClientInfoBrowser.setHtml(getClientBanner(id) if id else '')
        self.actEditClient2.setEnabled(bool(id))
        # QtGui.qApp.setCurrentClientId(id)


    def calcCashSum(self, eventId):
        ## расчет суммы
        eventEditor = CFakeEventEditor(self, eventId)
        query = QtGui.qApp.db.query('select * from Action where event_id = {0}'.format(eventId))
        sum = 0.0
        while query.next():
            record = query.record()
            if forceBool(record.value('account')):
                actionEndDate = forceDate(record.value('endDate'))
                actionTypeId = forceRef(record.value('actionType_id'))
                if actionTypeId:
                    personId = forceRef(record.value('person_id'))
                    tariffCategoryId = eventEditor.getPersonTariffCategoryId(personId)
                    contractId = forceRef(record.value('contract_id'))
                    if contractId:
                        financeId = forceRef(QtGui.qApp.db.translate('Contract', 'id', contractId, 'finance_id'))
                    else:
                        contractId = eventEditor.contractId
                        financeId = eventEditor.eventFinanceId
                    serviceIdList = eventEditor.getActionTypeServiceIdList(actionTypeId, financeId)
                    if serviceIdList:
                        tariffMap = eventEditor.contractTariffCache.getTariffDate(contractId, eventEditor, eventEditor.eventSetDateTime, financeId)
                        price = CContractTariffCache.getPriceToDate(tariffMap.dateTariffMap, serviceIdList, tariffCategoryId, actionEndDate)
                    else:
                        price = 0.0
                else:
                    price = 0.0
                sum += price * forceDouble(record.value('amount'))
        return sum


    def cashEvent(self, eventId):
        if eventId:
            dialog = CashDialogEditor(self)
            try:
                dialog.setEventId(eventId)
                dialog.setCashBox(QtGui.qApp.cashBox())
                dialog.setEventSum(self.calcCashSum(eventId))
                cashItemId = dialog.exec_()
                if cashItemId:
                    self.reapplyFilterRequired = True
                    self.lastAddedCashItemId = cashItemId
            finally:
                dialog.deleteLater()


    @pyqtSignature('int')
    def on_tabWidget_currentChanged(self, index):
        if index == 0:
            self.btnPrintCash.setVisible(True)
            self.btnPrintEvent.setVisible(False)
            self.btnCash.setEnabled(False)
            self.splitterBook.setSizes(self.splitterPayment.sizes())
            if self.reapplyFilterRequired:
                self.applyFilter(self.lastAddedCashItemId)
                self.reapplyFilterRequired = False
                self.lastAddedCashItemId = None
        elif index == 1:
            self.btnPrintCash.setVisible(False)
            self.btnPrintEvent.setVisible(True)
            self.btnCash.setEnabled(bool(self.modelEvents.idList()))
            self.splitterPayment.setSizes(self.splitterBook.sizes())
            if self.reapplyFilterRequired:
                self.applyPaymentFilter()
                self.reapplyFilterRequired = False


    @pyqtSignature('int')
    def on_cmbFilterEventPurpose_currentIndexChanged(self, index):
        eventPurposeId = self.cmbFilterEventPurpose.value()
        if eventPurposeId:
            filter = 'EventType.purpose_id =%d' % eventPurposeId
        else:
            filter = getWorkEventTypeFilter()
        self.cmbFilterEventType.setFilter(filter)


    @pyqtSignature('int')
    def on_cmbFilterOrgStructure_currentIndexChanged(self, index):
        orgStructureId = self.cmbFilterOrgStructure.value()
        self.cmbFilterPerson.setOrgStructureId(orgStructureId)
        self.cmbFilterAssistantPerson.setOrgStructureId(orgStructureId)


    @pyqtSignature('QAbstractButton*')
    def on_bbxFilter_clicked(self, button):
        buttonCode = self.bbxFilter.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.applyFilter()
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.resetFilter()
            self.applyFilter()


    @pyqtSignature('')
    def on_mnuCashItems_aboutToShow(self):
        currentRow = self.tblCashItems.currentIndex().row()
        itemPresent = currentRow>=0
        self.actEditClient.setEnabled(itemPresent and QtGui.qApp.userHasAnyRight([urAdmin, urRegTabWriteRegistry, urRegTabReadRegistry]))
        self.actOpenEvent.setEnabled(itemPresent and QtGui.qApp.userHasAnyRight([urAdmin, urRegTabWriteEvents]))
        self.actShowAccount.setEnabled(itemPresent)
        self.actPrintCash.setEnabled(itemPresent)


    @pyqtSignature('')
    def on_actEditClient_triggered(self):
        self.openClient(self.getCurrentClientIdByCashItem())
        self.modelCashItems.invalidateRecordsCache()


    @pyqtSignature('')
    def on_actOpenEvent_triggered(self):
        self.openEvent(self.getCurrentEventIdByCashItem())
        self.modelCashItems.invalidateRecordsCache()


    @pyqtSignature('')
    def on_actShowAccount_triggered(self):
        eventId = self.getCurrentEventIdByCashItem()
        self.resetPaymentFilter()
        self.edtPaymentFilterEventId.setText(str(eventId) if eventId else '')
        self.applyPaymentFilter()
        self.tabWidget.setCurrentIndex(1)


    @pyqtSignature('')
    def on_mnuPrintCash_aboutToShow(self):
        itemId = self.tblCashItems.currentItemId()
        self.actPrintCash.setEnabled(bool(itemId))


    @pyqtSignature('')
    def on_actPrintBook_triggered(self):
        self.tblCashItems.setReportHeader(u'Журнал кассовых операций')
        self.tblCashItems.setReportDescription(self.getFilterAsText()+'\n'+self.getAmountAsText())
        self.tblCashItems.printContent()


    @pyqtSignature('int')
    def on_actPrintCash_printByTemplate(self, templateId):
        itemId = self.tblCashItems.currentItemId()
        record = self.modelCashItems.recordCache().get(itemId)
        printCashOrder(self,
                       templateId,
                       forceRef(record.value('master_id')),
                       forceDateTime(record.value('dateTime')),
                       forceRef(record.value('cashOperation_id')),
                       forceDouble(record.value('sum')),
                       forceString(record.value('cashBox')))


    @pyqtSignature('int')
    def on_actPrintCashBook_printByTemplate(self, templateId):
        context = CInfoContext()
        idList = self.modelCashItems.idList()
        cashBookInfoList = context.getInstance(CCashBookInfoList, tuple(idList))
        begDate = CDateInfo(self.edtFilterBegDate.date())
        endDate = CDateInfo(self.edtFilterEndDate.date())
        data = { 'cashBook' : cashBookInfoList,
                        'filterBegDate' : begDate,
                        'filterEndDate' : endDate
               }
        applyTemplate(self, templateId, data)


    @pyqtSignature('QAbstractButton*')
    def on_bbxPaymentFilter_clicked(self, button):
        buttonCode = self.bbxPaymentFilter.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.applyPaymentFilter()
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.resetPaymentFilter()
            self.applyPaymentFilter()


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelClients_currentRowChanged(self, current, previous):
        self.showClientInfo(self.getCurrentClientId())
        self.updateEventList(self.getCurrentEventId())


    @pyqtSignature('')
    def on_mnuClients_aboutToShow(self):
        itemPresent = bool(self.getCurrentClientId())
        self.actEditClient2.setEnabled(itemPresent and QtGui.qApp.userHasAnyRight([urAdmin, urRegTabWriteRegistry, urRegTabReadRegistry]))


    @pyqtSignature('')
    def on_actEditClient2_triggered(self):
        self.openClient(self.getCurrentClientId())
        self.modelClients.invalidateRecordsCache()
        self.applyPaymentFilter()


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelEvents_currentRowChanged(self, current, previous):
        eventId = self.getCurrentEventId()
        if eventId:
            eventRecord = self.modelEvents.recordCache().get(eventId)
            eventTypeId = forceRef(eventRecord.value('eventType_id'))
            context = getEventContext(eventTypeId)
            if not context:
                context = 'f'+getEventTypeForm(eventTypeId)
        else:
            context = ''
        if context:
            customizePrintButton(self.btnPrintEvent, context)
            self.btnPrintEvent.setEnabled(True)
        else:
            self.btnPrintEvent.setEnabled(False)


    @pyqtSignature('')
    def on_mnuEvents_aboutToShow(self):
        itemPresent = bool(self.getCurrentEventId())
        self.actOpenEvent2.setEnabled(itemPresent and QtGui.qApp.userHasAnyRight([urAdmin, urRegTabWriteEvents]))
        self.actCash.setEnabled(itemPresent)


    @pyqtSignature('')
    def on_actOpenEvent2_triggered(self):
        self.openEvent(self.getCurrentEventId())
        self.modelEvents.invalidateRecordsCache()
        self.applyPaymentFilter()


    @pyqtSignature('')
    def on_actCash_triggered(self):
        self.cashEvent(self.getCurrentEventId())


    @pyqtSignature('')
    def on_btnCash_clicked(self):
        self.cashEvent(self.getCurrentEventId())


    @pyqtSignature('int')
    def on_btnPrintEvent_printByTemplate(self, templateId):
        context = CInfoContext()
        eventId = self.getCurrentEventId()
        eventInfo = context.getInstance(CEventInfo, eventId)
        tempInvalidInfo = None # self.getTempInvalidInfo(context)

        data = { 'event' : eventInfo,
                 'client': eventInfo.client,
                 'tempInvalid': tempInvalidInfo
               }
        applyTemplate(self, templateId, data)



class CCashItemsModel(CTableModel):
    def __init__(self, parent):
        eventTypeCol = CLocEventTypeColumn(  u'Обращение', ['master_id'], 20)
        eventSetDateCol = CLocEventSetDateColumn(  u'Назначено', ['master_id'], 20, eventTypeCol.eventCache)
        eventExecDateCol = CLocEventExecDateColumn(  u'Окончено', ['master_id'], 20, eventTypeCol.eventCache)
        eventPersonCol = CLocEventPersonColumn(  u'Врач', ['master_id', 'dateTime'], 20, eventTypeCol.eventCache)
        eventAssistantPersonCol = CLocEventAssistantPersonColumn(u'Ассистент', ['master_id'], 20, eventTypeCol.eventCache)

        clientCol = CLocClientColumn( u'Ф.И.О.', ['master_id'], 20, eventTypeCol.eventCache)
        clientBirthDateCol = CLocClientBirthDateColumn( u'Дата рожд.', ['master_id'], 10, eventTypeCol.eventCache, clientCol.clientCache)
        clientSexCol = CLocClientSexColumn(             u'Пол', ['master_id'], 3, eventTypeCol.eventCache, clientCol.clientCache)
        CTableModel.__init__(self, parent, [
            CDateTimeCol(u'Дата и время',  ['dateTime'], 15),
            CTextCol(u'Касса', ['cashBox'], 20),
            CRefBookCol(u'Кассир', ['createPerson_id'], 'vrbPerson', 20),
            CRefBookCol(u'Операция', ['cashOperation_id'], 'rbCashOperation', 20),
            CEnumCol(u'Тип оплаты', ['typePayment'], (u'Наличный', u'Безналичный', u'По реквизитам'), 20),
            CSumCol(u'Сумма', ['sum'], 10, 'r'),
            CTextCol(u'Документ об оплате', ['documentPayment'], 50),
            clientCol,
            clientBirthDateCol,
            clientSexCol,
            eventTypeCol,
            eventSetDateCol,
            eventExecDateCol,
            eventPersonCol,
            eventAssistantPersonCol
            ], 'Event_Payment' )
        self.eventCache = eventTypeCol.eventCache

    def sortDataModel(self):
        for col, value in self.headerSortingCol.items():
            self.idList().sort(key=lambda recordId: self.getRecordValueById(col, recordId), reverse=value)
        self.reset()


    def getRecordValueById(self, column, recordId):
        if column >= 0 and recordId:
            col = self._cols[column]
            if col:
                record = self.getRecordById(recordId)
                if record:
                    value = forceString(col.format([forceString(record.value('master_id'))]))
                    if value and isinstance(value, (QString, str, unicode)):
                        if isinstance(value, basestring):
                            return value.lower()
                        elif isinstance(value, QString):
                            return unicode(value).lower()
                    return value
        return None


class CLocEventTypeColumn(CCol):
    def __init__(self, title, fields, defaultWidth):
        CCol.__init__(self, title, fields, defaultWidth, 'l')
        db = QtGui.qApp.db
        self.eventCache     = CTableRecordCache(db, 'Event', 'eventType_id, client_id, setDate, execDate, execPerson_id')
        self.eventTypeCache = CTableRecordCache(db, 'EventType', 'name')


    def format(self, values):
        eventId = forceRef(values[0])
        if eventId:
            eventRecord = self.eventCache.get(eventId)
            if eventRecord:
                eventTypeId = forceRef(eventRecord.value('eventType_id'))
                eventTypeRecord = self.eventTypeCache.get(eventTypeId)
                if eventTypeRecord:
                    return eventTypeRecord.value('name')
        return CCol.invalid


    def invalidateRecordsCache(self):
        self.eventCache.invalidate()
        self.eventTypeCache.invalidate()


class CLocEventSetDateColumn(CCol):
    def __init__(self, title, fields, defaultWidth, eventCache):
        CCol.__init__(self, title, fields, defaultWidth, 'l')
        self.eventCache  = eventCache

    def format(self, values):
        eventId = forceRef(values[0])
        if eventId:
            eventRecord = self.eventCache.get(eventId)
            if eventRecord:
                return toVariant(forceString(forceDate(eventRecord.value('setDate'))))
        return CCol.invalid


class CLocEventExecDateColumn(CCol):
    def __init__(self, title, fields, defaultWidth, eventCache):
        CCol.__init__(self, title, fields, defaultWidth, 'l')
        self.eventCache  = eventCache

    def format(self, values):
        eventId = forceRef(values[0])
        if eventId:
            eventRecord = self.eventCache.get(eventId)
            if eventRecord:
                return toVariant(forceString(forceDate(eventRecord.value('execDate'))))
        return CCol.invalid


class CLocEventPersonColumn(CRefBookCol):
    def __init__(self, title, fields, defaultWidth, eventCache):
        CRefBookCol.__init__(self, title, fields, 'vrbPersonWithSpeciality', defaultWidth)
        self.eventCache  = eventCache

    def format(self, values):
        eventId = forceRef(values[0])
        date_ = forceDate(values[1])
        if eventId:
            eventRecord = self.eventCache.get(eventId)
            if eventRecord:
                db = QtGui.qApp.db
                stmt = u"""
                            SELECT IF(ejop.execPerson_id IS NOT NULL AND EXISTS(SELECT * FROM GlobalPreferences gp  WHERE gp.code='26' AND value = 'да'), ejop.execPerson_id, e.execPerson_id) as execPerson_id

                  FROM Event e 
                  LEFT JOIN Event_JournalOfPerson ejop ON e.id = ejop.master_id
                  LEFT JOIN Event_Payment ep ON e.id = ep.master_id  AND ep.dateTime >= ejop.setDate
                  WHERE e.id = %(event)s  
                AND
                  (ejop.id = ( SELECT MAX(id) FROM Event_JournalOfPerson 
                  WHERE ep.dateTime>=date(Event_JournalOfPerson.setDate)
                  and ep.dateTime = %(dat)s
                  AND Event_JournalOfPerson.master_id = %(event)s
                 ) OR ejop.id IS NULL)
                            """
                st = stmt % {"dat": db.formatDate(date_), "event": eventId}
                myqueryI = db.query(st)
                myqueryI.next()
                if myqueryI.value(0).toInt()[0]:
                    return CRefBookCol.format(self, [myqueryI.value(0).toInt()[0]])
                else:
                    return CRefBookCol.format(self, [eventRecord.value('execPerson_id')])
        return CCol.invalid


class CLocEventAssistantPersonColumn(CRefBookCol):
    def __init__(self, title, fields, defaultWidth, eventCache):
        CRefBookCol.__init__(self, title, fields, 'vrbPersonWithSpeciality', defaultWidth)
        self.eventCache  = eventCache

    def format(self, values):
        eventId = forceRef(values[0])
        if eventId:
            eventRecord = self.eventCache.get(eventId)
            if eventRecord:
                db = QtGui.qApp.db
                stmt = u"SELECT assistant_id FROM Event WHERE id = {0}""".format(eventId)
                myqueryI = db.query(stmt)
                myqueryI.next()
                if myqueryI.value(0).toInt()[0]:
                    return CRefBookCol.format(self, [myqueryI.value(0).toInt()[0]])
                else:
                    return CRefBookCol.format(self, [eventRecord.value('assistant_id')])
        return CCol.invalid


class CLocClientColumn(CCol):
    def __init__(self, title, fields, defaultWidth, eventCache):
        CCol.__init__(self, title, fields, defaultWidth, 'l')
        db = QtGui.qApp.db
        self.eventCache  = eventCache
        self.clientCache = CTableRecordCache(db, 'Client', 'lastName, firstName, patrName, birthDate, sex, SNILS')

    def format(self, values):
        val = values[0]
        eventId  = forceRef(val)
        eventRecord = self.eventCache.get(eventId)
        if eventRecord:
            clientId = forceRef(eventRecord.value('client_id'))
            clientRecord = self.clientCache.get(clientId)
            if clientRecord:
                name  = formatName(clientRecord.value('lastName'),
                                   clientRecord.value('firstName'),
                                   clientRecord.value('patrName'))
                return toVariant(name)
        return CCol.invalid


    def invalidateRecordsCache(self):
        self.clientCache.invalidate()


class CLocClientBirthDateColumn(CCol):
    def __init__(self, title, fields, defaultWidth, eventCache, clientCache):
        CCol.__init__(self, title, fields, defaultWidth, 'l')
        self.eventCache  = eventCache
        self.clientCache = clientCache

    def format(self, values):
        val = values[0]
        eventId  = forceRef(val)
        eventRecord = self.eventCache.get(eventId)
        if eventRecord:
            clientId = forceRef(eventRecord.value('client_id'))
            clientRecord = self.clientCache.get(clientId)
            if clientRecord:
                return toVariant(forceString(clientRecord.value('birthDate')))
        return CCol.invalid


class CLocClientSexColumn(CCol):
    def __init__(self, title, fields, defaultWidth, eventCache, clientCache):
        CCol.__init__(self, title, fields, defaultWidth, 'l')
        self.eventCache  = eventCache
        self.clientCache = clientCache

    def format(self, values):
        val = values[0]
        eventId  = forceRef(val)
        eventRecord = self.eventCache.get(eventId)
        if eventRecord:
            clientId = forceRef(eventRecord.value('client_id'))
            clientRecord = self.clientCache.get(clientId)
            if clientRecord:
                return toVariant(formatSex(clientRecord.value('sex')))
        return CCol.invalid


class CClientsModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent, [
            CTextCol(u'Фамилия',       ['lastName'],  20),
            CTextCol(u'Имя',           ['firstName'], 20),
            CTextCol(u'Отчество',      ['patrName'],  20),
            CDateCol(u'Дата рожд.', ['birthDate'], 12, highlightRedDate=False),
            CEnumCol(u'Пол',        ['sex'], (u'-', u'М', u'Ж'), 4, 'c'),
            ], 'Client' )


class CEventsModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent, [
            CDateCol(u'Назначен', ['setDate'],  10),
            CDateCol(u'Выполнен', ['execDate'], 10),
            CRefBookCol(u'Тип',  ['eventType_id'], 'EventType', 15),
            CRefBookCol(u'МЭС',  ['MES_id'], 'mes.MES', 15, CRBComboBox.showCode),
            CRefBookCol(u'Врач', ['execPerson_id'], 'vrbPersonWithSpeciality', 15),
            CEnumCol(u'Первичный', ['isPrimary'], codeIsPrimary, 8),
            CEnumCol(u'Порядок', ['order'], orderTexts, 8),
            CRefBookCol(u'Результат', ['result_id'], 'rbResult', 40),
            CTextCol(u'Номер документа', ['externalId'], 30),
            ], 'Event' )


class CCashBookInfoList(CInfoList):
    def __init__(self, context, idList):
        CInfoList.__init__(self, context)
        self.idList = idList


    def _load(self):
        self._items = [ self.getInstance(CCashBookInfo, id) for id in self.idList ]
        return True
        
class CCashBookInfo(CInfo):
    def __init__(self, context, id):
        CInfo.__init__(self, context)
        self.id = id
        self.itemIdList = []


    def _load(self):
        context = CInfoContext()
        db = QtGui.qApp.db
        record = db.getRecord('Event_Payment', '*', self.id)
        if record:
            result = True
        else:
            record = db.table('Event_Payment').newRecord()
            result = False
        eventId = forceRef(record.value('master_id'))
        eventInfo = context.getInstance(CEventInfo, eventId)
        self._event = eventInfo
        self._client = eventInfo.client
        self._date = CDateInfo(forceDate(record.value('dateTime')))
        cashOperationId = forceRef(record.value('cashOperation_id'))
        self._cashOperation = context.getInstance(CCashOperationInfo, cashOperationId)
        self._sum = forceDouble(record.value('sum'))
        self._cashBox = forceString(record.value('cashBox'))
        self._typePayment = forceInt(record.value('typePayment'))
        self._documentPayment = forceString(record.value('documentPayment'))
        return result
        
    event = property(lambda self: self.load()._event)
    client = property(lambda self: self.load()._client)
    date = property(lambda self: self.load()._date)
    typePayment = property(lambda self: self.load()._typePayment)
    cashOperation = property(lambda self: self.load()._cashOperation)
    sum = property(lambda self: self.load()._sum)
    cashBox = property(lambda self: self.load()._cashBox)
    documentPayment = property(lambda self: self.load()._documentPayment)
