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

u"""
Расчёты: создание/просмотр/печать/etc счетов
"""

from PyQt4                           import QtGui
from PyQt4.QtCore                     import ( Qt,
                                               QDate,
                                               QLocale,
                                               QObject,
                                               SIGNAL,
                                               pyqtSignature,
                                             )

from library.crbcombobox              import CRBModelDataCache, CRBComboBox
from library.database                 import addDateInRange
from library.DialogBase               import CDialogBase
from library.PrintInfo                import CInfoContext, CDateInfo
from library.PrintTemplates           import ( applyTemplate,
                                               additionalCustomizePrintButton,
                                               getPrintTemplates,
                                             )
from library.Counter import CCounterController
from library.Utils import (agreeNumberAndWord,
                           firstYearDay,
                           foldText,
                           forceBool,
                           forceDate,
                           forceDouble,
                           forceInt,
                           forceRef,
                           forceString,
                           forceStringEx,
                           formatList,
                           formatNum,
                           formatNum1,
                           lastYearDay,
                           toVariant,
                           trim)

from Accounting.AccountBuilder       import CAccountPool, CAccountBuilder
from Accounting.AccountCheckDialog   import CAccountCheckDialog
from Accounting.AccountEditDialog    import CAccountEditDialog
from Accounting.AccountInfo          import CAccountInfo, CAccountInfoList
from Accounting.ExposeConfirmationDialog import CExposeConfirmationDialog
from Accounting.FormProgressDialog    import ( CFormProgressCanceled,
                                               CFormProgressDialog,
                                             )
from Accounting.PayStatusDialog       import CPayStatusDialog
from Accounting.Tariff               import CTariff
from Accounting.Utils import (CAccountItemsModel, CAccountsModel, CContractTreeModel, CLocClientBirthDateColumn,
                              CLocClientColumn, CLocClientSexColumn, CLocEventCodeColumn, CLocEventColumn,
                              clearPayStatus, getAccountExportFormat, getContractDescr, selectActions, selectEvents,
                              selectVisits, selectReexposableAccountItems, selectReexposableEvents,
                              updateAccount, updateAccounts, updateAccountTotals, updateDocsPayStatus, CLocMKBColumn,
                              canRemoveAccount, CLocRKEYCol, CLocFKEYCol, selectCsgs, beforeUpdateAccounts)
from Events.EditDispatcher            import getEventFormClass
from Events.EventInfo                 import CContractInfoList
from Events.Utils                     import CFinanceType, CPayStatus
from Exchange.ExportAccountRegister   import exportRegister
from Exchange.ExportEISOMS           import exportEISOMS
from Exchange.ExportINFISOMS         import exportINFISOMS
from Exchange.ExportLOFOMS           import exportLOFOMS
from Exchange.ExportR01Native                  import exportR01Native
from Exchange.ExportR08Emergency               import exportR08Emergency
from Exchange.ExportR08EmergencyV59            import exportR08EmergencyV59
from Exchange.ExportR08EmergencyV200           import exportR08EmergencyV200
from Exchange.ExportR08Hospital                import exportR08Hospital
from Exchange.ExportR08HospitalV59             import exportR08HospitalV59
from Exchange.ExportR08HospitalV200            import exportR08HospitalV200
from Exchange.ExportR08HospitalV173            import exportR08HospitalV173
from Exchange.ExportR08Native                  import exportR08Native
from Exchange.ExportR08NativeHealthExamination import exportR08NativeHealthExamination
from Exchange.ExportR08NativeHealthExaminationV59 import exportR08NativeHealthExaminationV59
from Exchange.ExportR08NativeHealthExaminationV200 import exportR08NativeHealthExaminationV200
from Exchange.ExportR08NativeHealthExaminationV173 import exportR08NativeHealthExaminationV173
from Exchange.ExportR23Native        import exportR23Native
from Exchange.ExportR29VMPv312                 import exportR29VMPv312
from Exchange.ExportR29v312                    import exportR29v312
from Exchange.ExportR29DDv312                  import exportR29DDv312
from Exchange.ExportR29v312Stomotology         import exportR29v312Stomotology
from Exchange.ExportR45Native        import exportR45Native
from Exchange.ExportR47D1                      import exportR47D1
from Exchange.ExportR47D1V59                   import exportR47D1V59
from Exchange.ExportR47D3                      import exportR47D3
from Exchange.ExportR51DD2013         import exportR51DD2013
from Exchange.ExportR51Emergency      import exportR51Emergency
from Exchange.ExportR51EmergencyXml      import exportR51EmergencyXml
from Exchange.ExportR51Hospital      import exportR51Hospital
from Exchange.ExportR51NativeAmbulance         import exportR51Ambulance
from Exchange.ExportR51NativeHealthExamination import exportR51HealthExamination
from Exchange.ExportR51FMO                     import exportR51FMO
from Exchange.ExportR51OMS                     import exportR51OMS
from Exchange.ExportR51Stomatology             import exportR51Stomatology
from Exchange.ExportR53_2012                   import exportR53_2012
from Exchange.ExportR53Native                  import exportR53Native
from Exchange.ExportR61Native                  import exportR61Native
from Exchange.ExportR61TFOMSNative             import exportR61TFOMSNative
from Exchange.ExportR67DP                      import exportR67DP
from Exchange.ExportR67Native                  import exportR67Native
from Exchange.ExportR69DD                      import exportR69DD
from Exchange.ExportR69OMS                     import exportR69OMS
from Exchange.ExportR74NATIVE                  import exportR74NATIVE
from Exchange.ExportR77Native                  import exportR77Native
from Exchange.ExportR80Hospital                import exportR80Hospital
from Exchange.ExportR80NativeHealthExaminationV173 import exportR80NativeHealthExaminationV173
from Exchange.ExportR80_v200XML                import exportR80_v200
from Exchange.ImportPayRefuseR01 import ImportPayRefuseR01Native
from Exchange.ImportPayRefuseR23      import ImportPayRefuseR23Native
from Exchange.ImportFLKTFOMSR61 import importFLKTFOMSR61Native
from Orgs.Contracts                  import CContractEditor
from Orgs.Utils                       import getOrgStructurePersonIdList
from Registry.ClientEditDialog       import CClientEditDialog
from Reports.AccountRegistry         import CAccountRegistry
from Reports.AccountSummary          import CAccountSummary
from Reports.PolyclinicAccountSummary import CPolyclinicAccountSummary
from Reports.StationaryAccountSummary import CStationaryAccountSummary
from Reports.ReportAccountTotal import CReportAccountingTotal
from Reports.ReportBase               import CReportBase
from Reports.ClientsListByRegistry   import CClientsListByRegistry
from Reports.FinanceReportByAidProfileAndSocStatus import CFinanceReportByAidProfileAndSocStatus
from Reports.FinanceSummaryByDoctors  import ( CFinanceSummaryByDoctors,
                                               CFinanceSummaryByDoctorsEx,
                                             )
from Reports.FinanceSummaryByServices import ( CFinanceSummaryByServices,
                                               CFinanceSummaryByServicesEx,
                                               CDetailedFinanceSummaryByServices,
                                             )
from Reports.FinanceSumByServicesExpenses import CDetailedFinanceSumByServicesExpenses
from Reports.FinanceServiceByDoctors      import CFinanceServiceByDoctors
from Reports.ReportView              import CReportViewDialog
from Reports.RegistryStructure.DistributionOfCostAndDuration import CDistributionOfCostAndDurationReport, CDistributionOfCostAndDurationKSGReport
from Reports.RegistryStructure.KMU import CKMUReport
from Reports.RegistryStructure.KMUBySpeciality import CKMUBySpecialityReport
from Reports.RegistryStructure.KMUByVisitType import CKMUByVisitTypeReport
from Reports.RegistryStructure.Summary import CSummaryReport
from Reports.RegistryStructure.MedicalCareProvided import CMedicalCareProvidedReport
from Reports.RegistryStructure.StructureBy import CStructureByServiceReport, CStructureByEventReport
from Users.Rights                     import ( urAccessAccountInfo,
                                               urAccessAccounting,
                                               urAccessAccountingBudget,
                                               urAccessAccountingCash,
                                               urAccessAccountingCMI,
                                               urAccessAccountingTargeted,
                                               urAccessAccountingVMI,
                                               urAdmin,
                                               urDeleteAccount,
                                               urDeleteAccountBudget,
                                               urDeleteAccountCMI,
                                               urDeleteAccountVMI,
                                               urDeleteAccountCash,
                                               urDeleteAccountTargeted,
                                               urDeleteAccountItem,
                                               urRegTabReadRegistry,
                                               urRegTabWriteRegistry,
                                               urDeleteAccountsAtOnce,
                                               urDeleteRKEY,
                                               canRightForCreateAccounts,
                                               urAccessChangeEventExpose
                                             )

from Accounting.Ui_AccountingDialog    import Ui_AccountingDialog
from Accounting.Ui_CuredSetupDialog    import Ui_CuredSetupDialog
from Accounting.Ui_InsurerFilterDialog import Ui_InsurerFilterDialog

accountantRightList =   (urAdmin,
                         urAccessAccountInfo,
                         urAccessAccounting,
                         urAccessAccountingBudget,
                         urAccessAccountingCMI,
                         urAccessAccountingVMI,
                         urAccessAccountingCash,
                         urAccessAccountingTargeted
                        )

accountantDeleteRightList = {1: urDeleteAccountBudget,
                             2: urDeleteAccountCMI,
                             3: urDeleteAccountVMI,
                             4: urDeleteAccountCash,
                             5: urDeleteAccountTargeted,
}


def getAvailableFinanceTypeCodeList():
    app = QtGui.qApp
    if app.userHasAnyRight([urAdmin, urAccessAccountInfo, urAccessAccounting]):
        return None
    result = []
    for right, code in ((urAccessAccountingBudget,   CFinanceType.budget),
                        (urAccessAccountingCMI,      CFinanceType.CMI),
                        (urAccessAccountingVMI,      CFinanceType.VMI),
                        (urAccessAccountingCash,     CFinanceType.cash),
                        (urAccessAccountingTargeted, CFinanceType.targeted),
                       ):
        if app.userHasRight(right):
            result.append(code)
    return result


class CCuredSetupDialog(QtGui.QDialog, Ui_CuredSetupDialog):
    def __init__(self, parent, contractIndex = None, begDate = None,  endDate = None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.edtBegDate.setDate(begDate if begDate else  QDate.currentDate())
        self.edtEndDate.setDate(endDate if endDate else  QDate.currentDate())
        if contractIndex:
            self.cmbContract.setCurrentModelIndex(contractIndex)

    def getBegDate(self):
        return forceDate(self.edtBegDate.date())

    def getEndDate(self):
        return forceDate(self.edtEndDate.date())

    def getContractIndex(self):
        return self.cmbContract.currentModelIndex()


class CAccountingDialog(CDialogBase, Ui_AccountingDialog, CAccountBuilder):
    def __init__(self, parent):
        CDialogBase.__init__(self, parent)
        CAccountBuilder.__init__(self)

        self.addModels('Contracts', CContractTreeModel(self, getAvailableFinanceTypeCodeList()))
        self.addModels('Accounts', CAccountsModel(self))
        self.addModels('AccountItems', CAccountItemsModel(self))

        self.setupAccountsEconomicAnalisysMenu()
        self.setupAccountsMenu()
        self.setupAccountItemsMenu()
        self.setupBtnPrintMenu()
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)

        self.treeContracts.setModel(self.modelContracts)
        self.treeContracts.setSelectionModel(self.selectionModelContracts)
        self.treeContracts.setRootIsDecorated(False)
        self.treeContracts.setAlternatingRowColors(True)
        self.treeContracts.header().hide()
#        self.treeContracts.expandAll()

        self.cmbAnalysisPayRefuseType.setTable('rbPayRefuseType', addNone=True)
        self.cmbAnalysisPayRefuseType.setShowFields(CRBComboBox.showCodeAndName)
        self.cmbHistoryPayRefuseType.setTable('rbPayRefuseType', addNone=True)
        self.cmbHistoryPayRefuseType.setShowFields(CRBComboBox.showCodeAndName)
        self.cmbAnalysisClientCodeType.setTable('rbAccountingSystem', True)
        self.cmbAnalysisService.setTable('rbService',  True)
        self.cmbAnalysisAccountType.setTable('rbAccountType', addNone=True, order='code')
        self.cmbAnalysisAccountType.setShowFields(CRBComboBox.showCodeAndName)
        self.cmbGroupId.addItems([u'Не задано', u'Койко-день', u'Посещение', u'День лечения', u'Вызов бригады СМП', u'Услуга'])
        self.cmbGroupId.setCurrentIndex(0)

        self.tblAccounts.setModel(self.modelAccounts)
        self.tblAccounts.setSelectionModel(self.selectionModelAccounts)
        self.tblAccounts.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.tblAccounts.setPopupMenu(self.mnuAccounts)
        self.tblAccounts.addPopupRecordProperies()
        self.tblAccounts.enableColsMove()
        self.sortAscendingList = {}
#        self.tblAccounts.addPopupDelRow()
        self.tblAccountItems.setModel(self.modelAccountItems)
        self.tblAccountItems.setSelectionModel(self.selectionModelAccountItems)
        self.tblAccountItems.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.tblAccountItems.setPopupMenu(self.mnuAccountItems)
        self.tblAccountItems.enableColsMove()
        self.btnPrint.setMenu(self.mnuBtnPrint)
        additionalCustomizePrintButton(self, self.btnPrint, 'account', self._printActions)

# defaults
        self.cmbCalcOrgStructure.setExpandAll(False)
        self.cmbAnalysisOrgStructure.setExpandAll(False)
        self.cmbHistoryOrgStructure.setExpandAll(False)
        yesterday = QDate.currentDate().addDays(-1)
        self.clnCalcCalendar.setSelectedDate(yesterday)
        if QtGui.qApp.filterPaymentByOrgStructure():
            self.cmbCalcOrgStructure.setEnabled(True)
            self.cmbCalcOrgStructure.setValue(QtGui.qApp.currentOrgStructureId())
        else:
            self.cmbCalcOrgStructure.setEnabled(False)
            self.cmbCalcOrgStructure.setValue(None)
        self.resetAnalysisPage()
        self.on_cmbAnalysisAccountItems_currentIndexChanged(0)
        self.resetHistoryPage()
        self.on_cmbHistoryAccountItems_currentIndexChanged(0)
        self.payParams = {}
        self.historyFilter = {}
        self.currentAccountId = None
        self.currentFinanceId = None
        self.tabWorkType.setTabEnabled(2,False)
##        self.modelAccounts.setIdList(QtGui.qApp.db.getIdList('Account', order='id'))
        # Поля заполненность которых сигнализирует о том, что мы закрываем
        # возможность редактирования, и просто ищем счета по этим данным.
        self.eventIdWatching  = None
        self.actionIdWatching = None
        self.visitIdWatching  = None
        self.watchingAccountItemIdList = None
        self.isAscendingAccountItems = False
        self.isAscendingAccount = False
        self.accountItemOrder = None
        self.accountOrder = None
        self.updateFilterAccountsEtc(order=self.accountOrder)

        self.tblAccounts.enableColsHide()
        self.tblAccountItems.enableColsHide()

        # сканирование штрих кода
        self.addBarcodeScanAction('actScanBarcode')
        self.tabAnalysis.addAction(self.actScanBarcode)
        self.connect(self.actScanBarcode, SIGNAL('triggered()'), self.on_actScanBarcode_triggered)

        QObject.connect(self.tblAccountItems.horizontalHeader(), SIGNAL('sectionClicked(int)'), self.setAccountItemsSort)
        # QObject.connect(self.tblAccounts.horizontalHeader(), SIGNAL('sectionClicked(int)'), self.setSortAccounts)
        self.setSortable(self.tblAccounts, self.setSortAccounts)
        self.tblContragents.setVisible(False)

        if not QtGui.qApp.userHasRight(canRightForCreateAccounts):
            self.btnForm.setEnabled(False)
        if QtGui.qApp.defaultKLADR()[:2] == u'23':
            self.tabWorkType.removeTab(2)
            self.btnRefresh.setVisible(False)
            
            
    def setSortable(self, tbl, update_function=None):
        def on_click(col):
            model = tbl.model()
            sortingCol = model.headerSortingCol.get(col, False)
            model.headerSortingCol = {}
            if col != tbl.currentIndex().column():
                tbl.setCurrentItemId(tbl.currentItemId(), col)
            model.headerSortingCol[col] = not sortingCol
            if update_function:
                update_function()
            else:
                model.loadData()
            self.setSortingIndicator(tbl, col, not sortingCol)
        header = tbl.horizontalHeader()
        header.setClickable(True)
        QObject.connect(header, SIGNAL('sectionClicked(int)'), on_click)
        
    def getSortAscendingList(self):
        return self.sortAscendingList
        
    def setSortAscendingList(self, col, check):
        self.sortAscendingList[col] = check
        
    def setSortingIndicator(self, tbl, col, asc):
        tbl.setSortingEnabled(True)
        tbl.horizontalHeader().setSortIndicator(col, Qt.AscendingOrder if asc else Qt.DescendingOrder)
        
    def setSortAccounts(self):
        table = self.tblAccounts
        orderBy = ''
        for key, value in table.model().headerSortingCol.items():
            if value:
                ASC = u'ASC'
            else:
                ASC = u'DESC'
            if key in [1, 2, 3, 4, 8, 9, 10, 11, 12, 13, 14, 15, 17]:
                nameField = table.model().cols()[key].fields()[0]
                orderBy = table.model().table()[str(nameField)].name() + u" " + ASC
            elif key == 0:
                orderBy = u'(select code from vrbContract where id = contract_id) %s' % ASC
            elif key == 5:
                orderBy = u'(select CONCAT(infisCode, \' | \', shortName) from Organisation where id = payer_id) %s' % ASC
            elif key == 6:
                orderBy = u'(select CONCAT(regionalCode, \' | \', name) from rbAccountType where id = type_id) %s' % ASC
            elif key == 7:
                orderBy = u"""case when group_id in (1, 2, 9) then 'Койко-день' 
                    when group_id in (3, 4, 5, 6, 11, 12, 13, 14, 15, 16, 17, 24, 25, 26, 27, 28, 29, 31, 32, 33) then 'Посещение'
                    when group_id in (7, 10, 22) then 'День лечения' 
                    when group_id in (18, 19, 20, 21, 23, 30) then 'Услуга' 
                    when group_id = 8 then 'Вызов бригады СМП'
                    else '' end %s
                """ % ASC
            elif key == 16:
                orderBy = u'(select name from OrgStructure where id = orgStructure_id) %s' % ASC
            self.accountOrder = [orderBy]
            self.updateFilterAccountsEtc(None, [orderBy])
 

    def setAccountItemsSort(self, col):
        header = self.tblAccountItems.horizontalHeader()
        header.setSortIndicatorShown(True)
        self.isAscendingAccountItems = not self.isAscendingAccountItems
        if col != self.tblAccountItems.currentIndex().column():
            self.tblAccountItems.setCurrentItemId(self.tblAccountItems.currentItemId(), col)
        header.setSortIndicator(col, Qt.AscendingOrder if self.isAscendingAccountItems else Qt.DescendingOrder)
        if self.isAscendingAccountItems:
            order = u' ASC'
        else:
            order = u' DESC'
        db = QtGui.qApp.db
        table = db.table('Account_Item')
        tableClient = db.table('Client')
        if isinstance(self.modelAccountItems.cols()[col], CLocClientColumn):
            self.accountItemOrder = ', '.join([ tableClient['lastName'].name()+order,
                                                tableClient['firstName'].name()+order,
                                                tableClient['patrName'].name()+order
                                             ])
        elif isinstance(self.modelAccountItems.cols()[col], CLocClientBirthDateColumn):
            self.accountItemOrder = ', '.join([ tableClient['birthDate'].name()+order
                                             ])
        elif isinstance(self.modelAccountItems.cols()[col], CLocClientSexColumn):
            self.accountItemOrder = ', '.join([ tableClient['sex'].name()+order
                                             ])
        elif isinstance(self.modelAccountItems.cols()[col], CLocEventColumn):
            resIdList = self.modelAccountItems.getEventColFormat(self.modelAccountItems.idList())
            nameKeys = resIdList.keys()
            nameKeys.sort(reverse= not self.isAscendingAccountItems)
            orderAIIdList = []
            for nameKey in nameKeys:
                dataIdList = resIdList.get(nameKey, [])
                for dataId in dataIdList:
                    if dataId and dataId not in orderAIIdList:
                        orderAIIdList.append(dataId)
            if orderAIIdList:
                self.accountItemOrder = u'FIELD(Account_Item.`id`, %s)'%(', '.join(str(orderAIId) for orderAIId in orderAIIdList))
        elif isinstance(self.modelAccountItems.cols()[col], CLocEventCodeColumn):
            resIdList = self.modelAccountItems.getEventCodeColFormat(self.modelAccountItems.idList())
            nameKeys = resIdList.keys()
            nameKeys.sort(reverse= not self.isAscendingAccountItems)
            orderAIIdList = []
            for nameKey in nameKeys:
                dataIdList = resIdList.get(nameKey, [])
                for dataId in dataIdList:
                    if dataId and dataId not in orderAIIdList:
                        orderAIIdList.append(dataId)
            if orderAIIdList:
                self.accountItemOrder = u'FIELD(Account_Item.`id`, %s)'%(', '.join(str(orderAIId) for orderAIId in orderAIIdList))
        elif isinstance(self.modelAccountItems.cols()[col], CLocMKBColumn):
            resIdList = self.modelAccountItems.getMKBColFormat(self.modelAccountItems.idList())
            nameKeys = resIdList.keys()
            nameKeys.sort(reverse= not self.isAscendingAccountItems)
            orderAIIdList = []
            for nameKey in nameKeys:
                dataIdList = resIdList.get(nameKey, [])
                for dataId in dataIdList:
                    if dataId and dataId not in orderAIIdList:
                        orderAIIdList.append(dataId)
            if orderAIIdList:
                self.accountItemOrder = u'FIELD(Account_Item.`id`, %s)'%(', '.join(str(orderAIId) for orderAIId in orderAIIdList))
        elif self.modelAccountItems.cols()[col].fields()[0] == u'note':
            self.accountItemOrder = table['note'].name()+order
        elif isinstance(self.modelAccountItems.cols()[col], CLocRKEYCol):
            resIdList = self.modelAccountItems.getRKEYColFormat(self.modelAccountItems.idList())
            nameKeys = resIdList.keys()
            nameKeys.sort(reverse= not self.isAscendingAccountItems)
            orderAIIdList = []
            for nameKey in nameKeys:
                dataIdList = resIdList.get(nameKey, [])
                for dataId in dataIdList:
                    if dataId and dataId not in orderAIIdList:
                        orderAIIdList.append(dataId)
            if orderAIIdList:
                self.accountItemOrder = u'FIELD(Account_Item.`id`, %s)' % (
                    ', '.join(str(orderAIId) for orderAIId in orderAIIdList))
        elif isinstance(self.modelAccountItems.cols()[col], CLocFKEYCol):
            resIdList = self.modelAccountItems.getFKEYColFormat(self.modelAccountItems.idList())
            nameKeys = resIdList.keys()
            nameKeys.sort(reverse= not self.isAscendingAccountItems)
            orderAIIdList = []
            for nameKey in nameKeys:
                dataIdList = resIdList.get(nameKey, [])
                for dataId in dataIdList:
                    if dataId and dataId not in orderAIIdList:
                        orderAIIdList.append(dataId)
            if orderAIIdList:
                self.accountItemOrder = u'FIELD(Account_Item.`id`, %s)' % (
                    ', '.join(str(orderAIId) for orderAIId in orderAIIdList))
        else:
            self.accountItemOrder = self.modelAccountItems.cols()[col].fields()[0]+order
        self.updateAccountInfo()
        self.accountItemOrder = None


    # def setAccountSort(self, col):
    #     header = self.tblAccounts.horizontalHeader()
    #     header.setSortIndicatorShown(True)
    #     self.isAscendingAccount = not self.isAscendingAccount
    #     header.setSortIndicator(col, Qt.AscendingOrder if self.isAscendingAccount else Qt.DescendingOrder)
    #     if self.isAscendingAccount:
    #         order = u' ASC'
    #     else:
    #         order = u' DESC'
    #     db = QtGui.qApp.db
    #     table = db.table('Account')
    #     self.accountOrder = table[self.modelAccounts.cols()[col].fields()[0]].name()+order
    #     self.updateFilterAccountsEtc(order=self.accountOrder)
    #     self.accountOrder = None


    def exec_(self):
        if self.eventIdWatching or self.actionIdWatching or self.visitIdWatching:
            self.setWatchingMode()
        else:
            self.selectionModelContracts.setCurrentIndex(self.modelContracts.index(0, 0), QtGui.QItemSelectionModel.SelectCurrent)
        result = CDialogBase.exec_(self)
        return result


    def on_actScanBarcode_triggered(self):
        self.chkAnalysisAccountId.setChecked(True)
        self.edtAnalysisAccountId.clear()
        self.edtAnalysisAccountId.setFocus(Qt.OtherFocusReason)
        self.edtAnalysisAccountId.startHearingPoint()


    def setWatchingContent(self):
        if self.eventIdWatching:
            cond = 'event_id = %d' % self.eventIdWatching
        elif self.actionIdWatching:
            cond = 'action_id = %d' % self.actionIdWatching
        elif self.visitIdWatching:
            cond = 'visit_id = %d' % self.visitIdWatching
        else:
            return
        accountIdList = []
        accountItemIdList = []
        stmt = 'SELECT id, master_id FROM Account_Item WHERE deleted = 0 AND %s'
        query = QtGui.qApp.db.query(stmt%cond)
        while query.next():
            record = query.record()
            accountId = forceRef(record.value('master_id'))
            if accountId not in accountIdList:
                accountIdList.append(accountId)
            accountItemId = forceRef(record.value('id'))
            if accountItemId not in accountItemIdList:
                accountItemIdList.append(accountItemId)
        self.watchingAccountItemIdList = accountItemIdList
        currentAccountId = self.tblAccounts.currentItemId()
        self.tblAccounts.setIdList(accountIdList, currentAccountId)
        self.updateAccountsPanel(accountIdList)


    def setWatchingMode(self):
        self.splitter_3.widget(0).setVisible(False)
        self.btnForm.setEnabled(False)
        self.btnRefresh.setEnabled(False)
        self.btnExport.setEnabled(False)
        self.btnImport.setEnabled(False)
        self.tabWidget_2.setTabEnabled(1, False)
        if not QtGui.qApp.userHasAnyRight(accountantRightList):
            self.tblAccounts.setPopupMenu(None)
            self.tblAccountItems.setPopupMenu(None)
        self.setWatchingContent()


    def setWatchingFields(self, eventId=None, actionId=None, visitId=None):
        self.eventIdWatching  = eventId
        self.actionIdWatching = actionId
        self.visitIdWatching  = visitId


    def setupAccountsMenu(self):
        self.addObject('mnuAccounts', QtGui.QMenu(self))
        self.addObject('actEditAccount', QtGui.QAction(u'Изменить счёт', self))
        self.addObject('actPrintAccount', QtGui.QAction(u'Напечатать счёт (бланк)', self))
        self.addObject('actPrintAccountSummary',  QtGui.QAction(u'Напечатать сводный счёт', self))
        self.addObject('actPrintAccountInsurer',  QtGui.QAction(u'Счёт на СМО', self))
        self.addObject('actPrintAccountRegistry', QtGui.QAction(u'Напечатать реестр счёта (бланк)', self))
        self.addObject('actReportServiceByDoctors', QtGui.QAction(u'Финансовая сводка по врачам по услугам', self))
        self.addObject('actReportByDoctorsEx', QtGui.QAction(u'Финансовая сводка по врачам за период', self))
        self.addObject('actReportByServicesEx', QtGui.QAction(u'Финансовая сводка по услугам за период', self))
        self.addObject('actCheckMesInAccount', QtGui.QAction(u'Проверить счёт на соответствие МЭС', self))
        self.addObject('actSelectAllAccounts', QtGui.QAction(u'Выбрать все', self))
        self.addObject('actDeleteAccountItemsWithoutRKEY', QtGui.QAction(u'Удалить из реестра счета без RKEY', self))
        self.addObject('actDeleteAccountItemsWithoutFKEY', QtGui.QAction(u'Удалить из реестра счета без FKEY', self))
        self.addObject('actDeleteAccountItemsAllRKEY', QtGui.QAction(u'Удалить из счетов реестра RKEY', self))
        self.addObject('actDeleteAccountItemsAllFKEY', QtGui.QAction(u'Удалить из счетов реестра FKEY', self))
        self.addObject('actDeleteAccounts', QtGui.QAction(u'Удалить', self))
        self.addObject('actDeleteAccountsAtOnce', QtGui.QAction(u'Удалить все', self))
        self.addObject('actPrintPolyclinicSummary',  QtGui.QAction(u'Напечатать сводку по амбулаторной помощи', self))
        self.addObject('actPrintStationarySummary',  QtGui.QAction(u'Напечатать сводку по стационарной помощи', self))
        self.addObject('actPrintFinanceReportByAidProfileAndSocStatus',  QtGui.QAction(u'Напечатать отчет по профилю мед. помощи и соц. статуса', self))
        self.addObject('actPrintDistributionOfCostAndDuration',  QtGui.QAction(u'Распределение стоимости и длительности СБО в реестре по подразделениям', self))
        self.addObject('actPrintDistributionOfCostAndDurationKSG',  QtGui.QAction(u'Распределение стоимости и длительности СБО в реестре по КСГ', self))
        self.addObject('actPrintKMU',  QtGui.QAction(u'Структура КМУ', self))
        self.addObject('actPrintKMUBySpeciality',  QtGui.QAction(u'Структура КМУ по специальностям', self))
        self.addObject('actPrintKMUByVisitType',  QtGui.QAction(u'Структура КМУ по типам визитов', self))
        self.addObject('actPrintSummary',  QtGui.QAction(u'Общая сводка по статьям затрат', self))
        self.addObject('actPrintMedicalCareProvided',  QtGui.QAction(u'Сведения об оказанной медицинской помощи', self))
        self.addObject('actPrintStructureByService',  QtGui.QAction(u'Структура реестра по мероприятиям', self))
        self.addObject('actPrintStructureByEvent',  QtGui.QAction(u'Структура реестра по профилактическим осмотрам по типам событий', self))
        self.mnuAccounts.addAction(self.actEditAccount)
        self.mnuAccounts.addAction(self.actPrintAccount)
        self.mnuAccounts.addAction(self.actPrintAccountSummary)
        self.mnuAccounts.addAction(self.actPrintAccountInsurer)
        self.mnuAccounts.addAction(self.actPrintAccountRegistry)
        self.mnuAccounts.addAction(self.actReportServiceByDoctors)
        self.mnuAccounts.addAction(self.actReportByDoctorsEx)
        self.mnuAccounts.addAction(self.actReportByServicesEx)
        self.mnuAccounts.addSeparator()
        self.mnuAccounts.addAction(self.actCheckMesInAccount)
        self.mnuAccounts.addSeparator()
        self.mnuAccounts.addAction(self.actSelectAllAccounts)
        self.mnuAccounts.addSeparator()
        self.mnuAccounts.addAction(self.actDeleteAccountItemsWithoutFKEY)
        self.mnuAccounts.addAction(self.actDeleteAccountItemsWithoutRKEY)
        self.mnuAccounts.addSeparator()
        self.mnuAccounts.addAction(self.actDeleteAccountItemsAllFKEY)
        self.mnuAccounts.addAction(self.actDeleteAccountItemsAllRKEY)
        self.mnuAccounts.addSeparator()
        self.mnuAccounts.addAction(self.actDeleteAccounts)
        self.mnuAccounts.addSeparator()
        self.mnuAccounts.addAction(self.actDeleteAccountsAtOnce)
        self.mnuAccounts.addSeparator()


    def setupAccountItemsMenu(self):
        self.addObject('mnuAccountItems', QtGui.QMenu(self))
        self.addObject('actEditClient', QtGui.QAction(u'Открыть регистрационную карточку', self))
        self.addObject('actOpenEvent',  QtGui.QAction(u'Открыть первичный документ', self))
        self.addObject('actSetPayment', QtGui.QAction(u'Подтверждение оплаты', self))
        self.addObject('actEditPayment', QtGui.QAction(u'Изменение подтверждения оплаты', self))
        self.addObject('actSelectExposed', QtGui.QAction(u'Выбрать без подтверждения', self))
        self.addObject('actSelectAll', QtGui.QAction(u'Выбрать все', self))
        self.addObject('actReportByDoctors', QtGui.QAction(u'Финансовая сводка по врачам', self))
        self.addObject('actReportByServices', QtGui.QAction(u'Финансовая сводка по услугам', self))
        self.addObject('actDetailedReportByServices', QtGui.QAction(u'Финансовая сводка по услугам с детализацией', self))
        self.addObject('actDetailedReportByServicesExpenses', QtGui.QAction(u'Финансовая сводка по услугам с нормативным составом затрат', self))
        self.addObject('actReportByClients', QtGui.QAction(u'Список пациентов по реестру', self))
        self.addObject('actReportByRegistry', QtGui.QAction(u'Реестр счёта', self))
        self.addObject('actCured', QtGui.QAction(u'Реестр пролеченных больных сотрудников', self))
        #self.addObject('actPrintAccountByTemplate', getPrintAction(self, 'account', u'Ещё печать'))
        self.addObject('actDeleteAccountItemsRKEY', QtGui.QAction(u'Удалить RKEY', self))
        self.addObject('actDeleteAccountItemsFKEY', QtGui.QAction(u'Удалить FKEY', self))
        self.addObject('actDeleteAccountItems', QtGui.QAction(u'Удалить', self))
        self.addObject('actDeleteAccountItemsPersonalAccount', QtGui.QAction(u'Удалить персональный счет из реестра', self))
        self.addObject('actShowAccountItemInfo', QtGui.QAction(u'Свойства записи', self))
        self.addObject('actReportAccountTotal', QtGui.QAction(u'Счет итоговый', self))
        self.addObject('actChangeEventExpose', QtGui.QAction(u'Снять отметку "Выставлять в счет"', self))

        self.mnuAccountItems.addAction(self.actEditClient)
        self.mnuAccountItems.addAction(self.actOpenEvent)
        self.mnuAccountItems.addSeparator()
        self.mnuAccountItems.addAction(self.actSetPayment)
        self.mnuAccountItems.addAction(self.actEditPayment)
        self.mnuAccountItems.addSeparator()
        self.mnuAccountItems.addAction(self.actSelectExposed)
        self.mnuAccountItems.addAction(self.actSelectAll)
        self.mnuAccountItems.addSeparator()
        #self.mnuAccountItems.addAction(self.actPrintAccountByTemplate)
        self.mnuAccountItems.addSeparator()
        self.mnuAccountItems.addAction(self.actReportByRegistry)
        self.mnuAccountItems.addAction(self.actReportByClients)
        self.mnuAccountItems.addAction(self.actReportByDoctors)
        self.mnuAccountItems.addAction(self.actReportByServices)
        self.mnuAccountItems.addAction(self.actDetailedReportByServices)
        self.mnuAccountItems.addAction(self.actDetailedReportByServicesExpenses)
        self.mnuAccountItems.addSeparator()
        self.mnuAccountItems.addAction(self.actShowAccountItemInfo)
        self.mnuAccountItems.addSeparator()
        self.mnuAccountItems.addAction(self.actDeleteAccountItemsFKEY)
        self.mnuAccountItems.addAction(self.actDeleteAccountItemsRKEY)
        self.mnuAccountItems.addSeparator()
        self.mnuAccountItems.addAction(self.actDeleteAccountItems)
        self.mnuAccountItems.addAction(self.actDeleteAccountItemsPersonalAccount)
        self.mnuAccountItems.addAction(self.actChangeEventExpose)

    def setupAccountsEconomicAnalisysMenu(self):
        self.addObject('actAccountE1', QtGui.QAction(u'Э-1 Нагрузка на врача', self))
        self.addObject('actAccountE2', QtGui.QAction(u'Э-2 Выполненные объемы услуг в разрезе диагнозов', self))
        self.addObject('actAccountE3', QtGui.QAction(u'Э-3 Анализ нагрузки на врачей', self))
        self.addObject('actAccountE4', QtGui.QAction(u'Э-4 Нагрузка на врачей по видам финансирования', self))
        self.addObject('actAccountE5', QtGui.QAction(u'Э-5 Нагрузка на отделение в разрезе выполненных услуг', self))
        self.addObject('actAccountE6', QtGui.QAction(u'Э-6 Анализ нагрузки на отделение по видам финансирования', self))
        self.addObject('actAccountE7', QtGui.QAction(u'Э-7 Анализ нагрузки на подразделения', self))
        self.addObject('actAccountE8',
                       QtGui.QAction(u'Э-8 Анализ нагрузки на подразделения по видам финансирования', self))
        self.addObject('actAccountE9', QtGui.QAction(u'Э-9 Сводка о выполненных медицинских услугах по врачам', self))
        self.addObject('actAccountE10',
                       QtGui.QAction(u'Э-10 Сводка о выполненных медицинских услугах по отделениям', self))
        self.addObject('actAccountE11', QtGui.QAction(
            u'Э-11 Сводка о выполненных медицинских услугах по видам финансирования в разрезе плательщиков', self))
        self.addObject('actAccountE12',
                       QtGui.QAction(u'Э-12 Отчет по введенным услугам, отсутствующим в договоре', self))
        self.addObject('actAccountE13', QtGui.QAction(u'Э-13 Реестр счетов за пролеченных больных', self))
        self.addObject('actAccountE14', QtGui.QAction(
            u'Э-14 Отчет о пролеченных больных, застрахованных на территории Краснодарского края, в разрезе страховщиков',
            self))
        self.addObject('actAccountE15', QtGui.QAction(u'Э-15 Отчет о работе отделений в разрезе плательщиков', self))
        self.addObject('actAccountE16', QtGui.QAction(u'Э-16 Отчет о работе врачей в разрезе плательщиков', self))
        self.addObject('actAccountE17', QtGui.QAction(u'Э-17 Выполненные объемы услуг по врачам', self))
        self.addObject('actAccountE19', QtGui.QAction(u'Э-19 Список услуг, оказанных пациентам', self))
        self.addObject('actAccountE23',
                       QtGui.QAction(u'Э-23 Выполненные объемы посещений в разрезе специальностей', self))
        self.addObject('actAccountE24', QtGui.QAction(u'Э-24 Нагрузка на отделение в разрезе профилей коек', self))
        self.addObject('actAccountE26', QtGui.QAction(
            u'Э-26 Сведения о численности застрахованных лиц обратившихся в организацию для оказания медицинской помощи',
            self))

        self.addObject('mnuAccountEconomicAnalisys', QtGui.QMenu(self))
        self.mnuAccountEconomicAnalisys.setTitle(u'Экономический анализ')
        for idx in range(1, 27):
            if hasattr(self, 'actAccountE%d' % idx):
                self.mnuAccountEconomicAnalisys.addAction(getattr(self, 'actAccountE%d' % idx))

    def setupBtnPrintMenu(self):
        self.addObject('mnuBtnPrint', QtGui.QMenu(self))
        self._printActions = (
        {'action': self.actPrintAccount, 'slot': self.on_actPrintAccount_triggered},
        {'action': self.actPrintAccountSummary, 'slot': self.on_actPrintAccountSummary_triggered},
        {'action': self.actPrintAccountInsurer, 'slot': self.on_actPrintAccountInsurer_triggered},
        {'action': self.actPrintAccountRegistry, 'slot': self.on_actPrintAccountRegistry_triggered},
        {'action': self.actReportByRegistry, 'slot': self.on_actReportByRegistry_triggered},
        {'action': self.actReportByClients, 'slot': self.on_actReportByClients_triggered},
        {'action': self.actReportByDoctors, 'slot': self.on_actReportByDoctors_triggered},
        {'action': self.actReportServiceByDoctors, 'slot': self.on_actReportServiceByDoctors_triggered},
        {'action': self.actReportByDoctorsEx, 'slot': self.on_actReportByDoctorsEx_triggered},
        {'action': self.actReportByServices, 'slot': self.on_actReportByServices_triggered},
        {'action': self.actDetailedReportByServices, 'slot': self.on_actDetailedReportByServices_triggered},
        {'action': self.actDetailedReportByServicesExpenses, 'slot': self.on_actDetailedReportByServicesExpenses_triggered},
        {'action': self.actReportByServicesEx, 'slot': self.on_actReportByServicesEx_triggered},
        {'action': self.actCured, 'slot': self.on_actCured_triggered},
        {'action': self.actPrintPolyclinicSummary, 'slot': self.on_actPrintPolyclinicSummary_triggered},
        {'action': self.actPrintStationarySummary, 'slot': self.on_actPrintStationarySummary_triggered},
        {'action': self.actPrintFinanceReportByAidProfileAndSocStatus, 'slot': self.on_actPrintFinanceReportByAidProfileAndSocStatus_triggered},
        {'action': self.actReportAccountTotal, 'slot': self.on_actReportAccountTotal},
        )
        for act in self._printActions:
            self.mnuBtnPrint.addAction(act['action'])
        subMenu = self.mnuBtnPrint.addMenu(u'Структура реестра')
        subMenu.addAction(self.actPrintDistributionOfCostAndDuration)
        subMenu.addAction(self.actPrintDistributionOfCostAndDurationKSG)
        subMenu.addAction(self.actPrintKMU)
        subMenu.addAction(self.actPrintKMUBySpeciality)
        subMenu.addAction(self.actPrintKMUByVisitType)
        subMenu.addAction(self.actPrintSummary)
        subMenu.addAction(self.actPrintMedicalCareProvided)
        subMenu.addAction(self.actPrintStructureByService)
        subMenu.addAction(self.actPrintStructureByEvent)

        # хотела добавить в конец меню, но всегда будет в списке до экшенов в основном меню
        # тк все меню будет перерисовано функцией additionalCustomizePrintButton
        self.mnuBtnPrint.insertMenu(self.mnuBtnPrint.actions()[len(self.mnuBtnPrint.actions()) - 1],
                                    self.mnuAccountEconomicAnalisys)

    def resetAnalysisPage(self):
        yesterday = QDate.currentDate().addDays(-1)
        self.edtAnalysisBegDate.setDate(firstYearDay(yesterday))
        self.edtAnalysisEndDate.setDate(lastYearDay(yesterday))
        self.edtAnalysisNumber.setText('')
        if QtGui.qApp.filterPaymentByOrgStructure():
            orgStructureId = self.cmbCalcOrgStructure.value()
        else:
            orgStructureId = None
        self.cmbAnalysisOrgStructure.setValue(orgStructureId)
        self.cmbAnalysisAccountItems.setCurrentIndex(0)
        self.edtAnalysisDocument.setText('')
        self.cmbAnalysisPayRefuseType.setValue(0)
        self.edtAnalysisNote.setText('')
        self.chkAnalysisClientCode.setChecked(False)
        self.edtAnalysisClientCode.setText('')
        self.cmbAnalysisClientCodeType.setValue(None)
        self.chkAnalysisEventCode.setChecked(False)
        self.chkAnalysisService.setChecked(False)
        self.chkAnalysisCreateDate.setChecked(False)
        self.edtAnalysisCreateBegDate.setDate(firstYearDay(yesterday))
        self.edtAnalysisCreateEndDate.setDate(lastYearDay(yesterday))
        self.edtAnalysisEventCode.setText('')
        self.cmbAnalysisEventCodeType.setCurrentIndex(0)
        self.cmbAnalysisService.setCurrentIndex(0)


    def resetHistoryPage(self):
        self.edtHistoryBegDate.setDate(self.edtAnalysisBegDate.date())
        self.edtHistoryEndDate.setDate(self.edtAnalysisEndDate.date())
        self.edtHistoryNumber.setText(self.edtAnalysisNumber.text())
        self.cmbHistoryOrgStructure.setValue(self.cmbAnalysisOrgStructure.value())
        self.cmbHistoryAccountItems.setCurrentIndex(self.cmbAnalysisAccountItems.currentIndex())
        self.edtHistoryDocument.setText(self.edtAnalysisDocument.text())
        self.cmbHistoryPayRefuseType.setValue(self.cmbAnalysisPayRefuseType.value())
        self.edtHistoryNote.setText(self.edtAnalysisNote.text())
        self.chkHistoryOnlyCurrentService.setChecked(False)


    def getContractIdList(self, treeIndex):
        treeItem = treeIndex.internalPointer() if treeIndex.isValid() else None
        return treeItem.idList if treeItem else []


    def updateFilterAccountsEtc(self, newAccountId=None, order=None):
        self.edtAnalysisAccountId.stopHearingPoint()
        isWatchMode = (self.eventIdWatching or self.actionIdWatching or self.visitIdWatching)
        currentAccountId = newAccountId if newAccountId else self.tblAccounts.currentItemId()
        if isWatchMode:
            self.modelAccounts.invalidateRecordsCache()
            self.tblAccounts.setCurrentItemId(currentAccountId )
        else:
            db = QtGui.qApp.db
            table            = db.table('Account')
            tableAccountItem = db.table('Account_Item')
            tableEvent       = db.table('Event')
            tableRbService       = db.table('rbService')
            tableClient      = db.table('Client')
            tableClientIdentification = db.table('ClientIdentification')
            tableEx = table

            workIndex = self.tabWorkType.currentIndex()

            if workIndex == 1 and self.chkAnalysisAccountId.isChecked():
                self.selectionModelContracts.setCurrentIndex(self.modelContracts.index(0, 0),
                                                             QtGui.QItemSelectionModel.ClearAndSelect)

            contractIdList = self.getContractIdList(self.treeContracts.currentIndex())
            enableBtnForm = False
            cond = [table['deleted'].eq(0)]
            if contractIdList:
                cond.append(table['contract_id'].inlist(contractIdList))
                if workIndex == 0:
                    enableBtnForm = True
                    begDate = QDate.currentDate()
                    addDateInRange(cond, table['createDatetime'], begDate, begDate)
                elif workIndex == 1:
                    if self.chkAnalysisAccountId.isChecked():
                        cond.append(table['id'].eq(trim(self.edtAnalysisAccountId.text())))
                    else:
                        begDate = self.edtAnalysisBegDate.date()
                        endDate = self.edtAnalysisEndDate.date()
                        addDateInRange(cond, table['date'], begDate, endDate)
                        number  = unicode(self.edtAnalysisNumber.text())
                        payerId = self.cmbAnalysisPayer.value()
                        accountTypeId = self.cmbAnalysisAccountType.value()
                        groupId = self.cmbGroupId.currentIndex()
                        groupIdList = {1: [1, 2, 9],
                                       2: [3, 4, 5, 6, 11, 12, 13, 14, 15, 16, 17, 24, 25, 26, 27, 28, 29, 31, 32],
                                       3: [7, 10, 22],
                                       4: [8],
                                       5: [18, 19, 20, 21, 23, 30]}
                        if groupId:
                            cond.append(table['group_id'].inlist(groupIdList[groupId]))
                        if payerId:
                            cond.append(table['payer_id'].eq(payerId))
                        if accountTypeId:
                            cond.append(table['type_id'].eq(accountTypeId))
                        if number:
                            cond.append(table['number'].like(number))
                        orgStructureId = self.cmbAnalysisOrgStructure.value()
                        if orgStructureId:
                            cond.append(table['orgStructure_id'].eq(orgStructureId))
                        filterChkClientCode = self.chkAnalysisClientCode.isChecked()
                        filterClientCode = forceStringEx(self.edtAnalysisClientCode.text()) if filterChkClientCode else ''
                        filterChkEventCode = self.chkAnalysisEventCode.isChecked()
                        filterEventCode = forceStringEx(self.edtAnalysisEventCode.text()) if filterChkEventCode else ''
                        filterChkService = self.chkAnalysisService.isChecked()

                        if filterClientCode or filterEventCode or filterChkService:
                            tableEx = tableEx.leftJoin(tableAccountItem, db.joinAnd([tableAccountItem['master_id'].eq(tableEx['id']), tableAccountItem['deleted'].eq(0)]))
                            tableEx = tableEx.leftJoin(tableEvent, db.joinAnd([tableEvent['id'].eq(tableAccountItem['event_id']), tableEvent['deleted'].eq(0)]))

                        if filterClientCode:
                            filterClientCodeType = self.cmbAnalysisClientCodeType.value()
                            if bool(filterClientCode):
                                tableEx = tableEx.leftJoin(tableClient, db.joinAnd([tableClient['id'].eq(tableEvent['client_id']), tableClient['deleted'].eq(0)]))
                                if filterClientCodeType:
                                    tableEx = tableEx.innerJoin(tableClientIdentification,
                                                                db.joinAnd([tableClientIdentification['client_id'].eq(tableClient['id']), tableClientIdentification['deleted'].eq(0)]))
                                    cond.append(tableClientIdentification['accountingSystem_id'].eq(filterClientCodeType))
                                    cond.append(tableClientIdentification['identifier'].eq(filterClientCode))
                                else:
                                    cond.append(tableClient['id'].eq(filterClientCode))

                        if filterEventCode:
                            filterEventCodeType = self.cmbAnalysisEventCodeType.currentIndex()
                            if filterEventCode:
                                if filterEventCodeType == 1:
                                    cond.append(tableEvent['externalId'].eq(filterEventCode))
                                else:
                                    cond.append(tableEvent['id'].eq(filterEventCode))

                        if filterChkService:
                            filterService= self.cmbAnalysisService.value()
                            if bool(filterService):
                                tableEx = tableEx.leftJoin(tableRbService, tableRbService['id'].eq(tableAccountItem['service_id']))
                                cond.append(tableRbService['id'].eq(filterService))

                        if self.chkAnalysisCreateDate.isChecked():
                            createDateBeg = self.edtAnalysisCreateBegDate.date()
                            createDateEnd = self.edtAnalysisCreateEndDate.date()
                            addDateInRange(cond, table['createDatetime'], createDateBeg, createDateEnd)
                elif workIndex == 2:
                    begDate = self.edtHistoryBegDate.date()
                    endDate = self.edtHistoryEndDate.date()
                    addDateInRange(cond, table['date'], begDate, endDate)
                    number  = unicode(self.edtHistoryNumber.text())
                    if number:
                        cond.append(table['number'].like(number))
                    orgStructureId = self.cmbHistoryOrgStructure.value()
                    if orgStructureId:
                        cond.append(table['orgStructure_id'].eq(orgStructureId))
                    itemQueryTable, itemCond = self.formAccountItemQueryParts()
    #                tableAccountItem = db.table('Account_Item')
                    itemCond.append(tableAccountItem['master_id'].eq(table['id']))
                    cond.append(db.existsStmt(itemQueryTable, itemCond))
                if not order:
                    order = [table['date'].name(),
                             table['number'].name(),
                             table['id'].name()]
                accountIdList = db.getDistinctIdList(tableEx, idCol='Account.`id`', where=cond, order=order)
            else:
                accountIdList = []
            self.tblAccounts.setIdList(accountIdList, currentAccountId)
            self.updateAccountsPanel(accountIdList)
            if QtGui.qApp.userHasRight(canRightForCreateAccounts):
                self.btnForm.setEnabled(enableBtnForm)


    def updateAccountsPanel(self, idList):
        count      = len(idList)
        sum        = 0.0
        exposed    = 0.0
        payedSum   = 0.0
        refusedSum = 0.0
        if idList:
            db = QtGui.qApp.db
            table = db.table('Account')
            record = db.getRecordEx(
                table, 'SUM(`sum`), SUM(`exposedSum`), SUM(`payedSum`), SUM(`refusedSum`)', table['id'].inlist(idList))
            if record:
                sum        = forceDouble(record.value(0))
                exposed    = forceDouble(record.value(1))
                payedSum   = forceDouble(record.value(2))
                refusedSum = forceDouble(record.value(3))
        locale = QLocale()
        self.edtTotalAccounts.setText(locale.toString(count))
        self.edtTotalSum.setText(     locale.toString(sum, 'f', 2))
        self.edtTotalExposed.setText( locale.toString(exposed, 'f', 2))
        self.edtTotalPayed.setText(   locale.toString(payedSum, 'f', 2))
        self.edtTotalRefused.setText( locale.toString(refusedSum, 'f', 2))


    def updateAccountItemsPanel(self, idList):
        count, totalSum, exposedSum, payedSum, refusedSum, totalPayed, totalRefused, \
        totalClientsCount, totalEventsCount, totalActionsCount, totalVisitsCount = getAccountItemsTotals(idList)
        locale = QLocale()
        self.edtAccountItemsCount.setText(locale.toString(count))
        self.edtAccountItemsSum.setText(     locale.toString(totalSum, 'f', 2))
        self.edtAccountItemsExposed.setText(     locale.toString(exposedSum, 'f', 2))
        self.edtAccountItemsPayed.setText(   locale.toString(totalPayed, 'f', 2))
        self.edtAccountItemsRefused.setText( locale.toString(totalRefused, 'f', 2))
        self.edtAccountItemsClientsCount.setText(str(totalClientsCount))
        self.edtAccountItemsEventsCount.setText(str(totalEventsCount))
        self.edtAccountItemsActionsCount.setText(str(totalActionsCount))
        self.edtAccountItemsVisitsCount.setText(str(totalVisitsCount))
        if QtGui.qApp.defaultKLADR()[:2] != u'23':
            self.tabWorkType.setTabEnabled(2,self.tabWorkType.currentIndex() == 2 or bool(idList))


    def updateAccountItemInfo(self, accountItemId):
        text = '\n'
        if accountItemId:
            itemRecord = self.modelAccountItems.recordCache().get(accountItemId)
            if itemRecord:
                document       = forceString(itemRecord.value('number'))
                date           = forceString(itemRecord.value('date'))
                refuseTypeId   = forceRef(itemRecord.value('refuseType_id'))
                reexposeItemId = forceRef(itemRecord.value('reexposeItem_id'))
                note           = forceString(itemRecord.value('note'))
                if document and date:
                    if refuseTypeId:
                        data = CRBModelDataCache.getData('rbPayRefuseType', True, '')
                        refuseText = u'причина отказа: '+data.getStringById(refuseTypeId, CRBComboBox.showCodeAndName)
                        if reexposeItemId:
                            text = u'перевыставлен'
                        else:
                            text = u'отказан: %s от %s, %s' % (document, date, refuseText)
                    else:
                        text = u'оплачен: %s от %s' % (document, date)
                else:
                    text = u'без подтверждения'
                if note:
                    text = text + u'\nПримечание:' + note
                else:
                    text = text + u'\n'
        self.lblAccountItemInfo.setText(text)


    def formAccountItemQueryParts(self):
        db = QtGui.qApp.db
        table = db.table('Account_Item')
        tableEvent  = db.table('Event')
        tableVisit  = db.table('Visit')
        tableAction = db.table('Action')
        tableClient = db.table('Client')
        tableClientIdentification = db.table('ClientIdentification')
        tableRbService = db.table('rbService')

        queryTable = table
        workIndex = self.tabWorkType.currentIndex()
        cond = [table['deleted'].eq(0)]
        filterCode = 0
        filterDocument = ''
        filterNote = ''
        filterChkClientCode = filterClientCodeType = False
        filterChkEventCode = filterEventCodeType = False
        filterChkService = filterService = False
        if workIndex == 0:
            pass
        elif workIndex == 1:
            filterCode = self.cmbAnalysisAccountItems.currentIndex()
            filterDocument = forceStringEx(self.edtAnalysisDocument.text())
            filterRefuseType = self.cmbAnalysisPayRefuseType.value()
            filterNote = forceStringEx(self.edtAnalysisNote.text())
            filterChkClientCode = self.chkAnalysisClientCode.isChecked()
            if filterChkClientCode:
                filterClientCode = forceStringEx(self.edtAnalysisClientCode.text())
                filterClientCodeType = self.cmbAnalysisClientCodeType.value()
            filterChkEventCode = self.chkAnalysisEventCode.isChecked()
            if filterChkEventCode:
                filterEventCode = forceStringEx(self.edtAnalysisEventCode.text())
                filterEventCodeType = self.cmbAnalysisEventCodeType.currentIndex()
            filterChkService = self.chkAnalysisService.isChecked()
            if filterChkService:
                filterService = self.cmbAnalysisService.value()
        elif workIndex == 2:
            filterCode = self.cmbHistoryAccountItems.currentIndex()
            filterDocument = forceStringEx(self.edtHistoryDocument.text())
            filterRefuseType = self.cmbHistoryPayRefuseType.value()
            filterNote = forceStringEx(self.edtHistoryNote.text())

        if filterCode == 0:  #0:Все
            pass
        elif filterCode == 1: #1:Без подтверждения
            cond.append(db.joinOr([table['date'].isNull(), table['number'].eq('')]))
            self.__appendNoteCondition(cond, table['note'], filterNote)
        elif filterCode == 2: #2:Подтверждённые
            cond.append(table['date'].isNotNull())
            self.__appendDocCondition(cond, table['number'], filterDocument)
            self.__appendNoteCondition(cond, table['note'], filterNote)
        elif filterCode == 3: #3:Оплаченные
            cond.append(table['date'].isNotNull())
            self.__appendDocCondition(cond, table['number'], filterDocument)
            cond.append(table['refuseType_id'].isNull())
            self.__appendNoteCondition(cond, table['note'], filterNote)
        elif filterCode == 4: #4:Отказанные
            cond.append(table['date'].isNotNull())
            self.__appendDocCondition(cond, table['number'], filterDocument)
            self.__appendPayStatusCondition(cond, table['refuseType_id'], filterRefuseType)
            self.__appendNoteCondition(cond, table['note'], filterNote)
        elif filterCode == 5: #5:Перевыставляемые
            cond.append(table['date'].isNotNull())
            self.__appendDocCondition(cond, table['number'], filterDocument)
            self.__appendPayStatusCondition(cond, table['refuseType_id'], filterRefuseType)
            tablePayRefuseType = db.table('rbPayRefuseType')
            cond.append(tablePayRefuseType['rerun'].ne(0))
            queryTable = queryTable.leftJoin(
                tablePayRefuseType, table['refuseType_id'].eq(tablePayRefuseType['id']))
            self.__appendNoteCondition(cond, table['note'], filterNote)
        elif filterCode == 6: #6:Неперевыставляемые
            cond.append(table['date'].isNotNull())
            self.__appendDocCondition(cond, table['number'], filterDocument)
            self.__appendPayStatusCondition(cond, table['refuseType_id'], filterRefuseType)
            tablePayRefuseType = db.table('rbPayRefuseType')
            cond.append(tablePayRefuseType['rerun'].eq(0))
            queryTable = queryTable.leftJoin(
                tablePayRefuseType, table['refuseType_id'].eq(tablePayRefuseType['id']))
            self.__appendNoteCondition(cond, table['note'], filterNote)

        queryTable = queryTable.leftJoin(tableEvent, db.joinAnd([tableEvent['id'].eq(table['event_id']), tableEvent['deleted'].eq(0)]))
        queryTable = queryTable.leftJoin(tableClient, db.joinAnd([tableClient['id'].eq(tableEvent['client_id']), tableClient['deleted'].eq(0)]))
        queryTable = queryTable.leftJoin(tableRbService, tableRbService['id'].eq(table['service_id']))
        if filterChkClientCode:
            if filterClientCodeType and filterClientCode:
                queryTable = queryTable.innerJoin(tableClientIdentification,
                                                  db.joinAnd([tableClientIdentification['client_id'].eq(tableClient['id']), tableClientIdentification['deleted'].eq(0)]))
                cond.append(tableClientIdentification['accountingSystem_id'].eq(filterClientCodeType))
                cond.append(tableClientIdentification['identifier'].eq(filterClientCode))
            else:
                if filterClientCode:
                    try:
                        i_filterClientCode = int(filterClientCode)
                        cond.append(tableClient['id'].eq(i_filterClientCode))
                    except ValueError:
                        pass
        if filterChkEventCode:
            if filterEventCodeType == 1 and filterEventCode:
                s_filterEventCode = unicode(filterEventCode)
                cond.append(tableEvent['externalId'].eq(s_filterEventCode))
            else:
                if filterEventCode:
                    try:
                        i_filterEventCode = int(filterEventCode)
                        cond.append(tableEvent['id'].eq(i_filterEventCode))
                    except ValueError:
                        pass
        if filterChkService and filterService:
            cond.append(tableRbService['id'].eq(filterService))

        if workIndex == 2:
            clientId     = self.historyFilter.get('client_id', None)
            actionTypeId = self.historyFilter.get('actionType_id', None)
            serviceId    = self.historyFilter.get('service_id', None)
            eventTypeId  = self.historyFilter.get('eventType_id', None)
            cond.append(tableEvent['client_id'].eq(clientId))
            if self.chkHistoryOnlyCurrentService.isChecked():
                queryTable = queryTable.leftJoin(tableVisit,  db.joinAnd([tableVisit['id'].eq(table['visit_id']), tableVisit['deleted'].eq(0)]))
                queryTable = queryTable.leftJoin(tableAction, db.joinAnd([tableAction['id'].eq(table['action_id']), tableAction['deleted'].eq(0)]))
                condActionEq = [
                    table['action_id'].isNotNull(), tableAction['actionType_id'].eq(actionTypeId) ]
                condVisitEq = [ table['visit_id'].isNotNull(),  tableVisit['service_id'].eq(serviceId) ]
                condEventEq = [
                    table['action_id'].isNull(), table['visit_id'].isNull(),
                    tableEvent['eventType_id'].eq(eventTypeId), tableEvent['deleted'].eq(0)]
                cond.append(db.joinOr([
                    db.joinAnd(condActionEq), db.joinAnd(condVisitEq), db.joinAnd(condEventEq)]))
        return queryTable, cond


    def __appendDocCondition(self, cond, field, document):
        if document:
            cond.append(field.like(document))
        else:
            cond.append(field.ne(''))


    def __appendNoteCondition(self, cond, field, note):
        if note:
            cond.append(field.like(note))


    def __appendPayStatusCondition(self, cond, field, id):
        if id:
            cond.append(field.eq(id))
        else:
            cond.append(field.isNotNull())


    def formAccountItemReportDescription(self):
        accountRecord = self.modelAccounts.recordCache().get(self.tblAccounts.currentItemId())
        if accountRecord:
            accountNumber = forceString(accountRecord.value('number'))
            accountDate = forceString(accountRecord.value('date'))
            descr = [ u'к счету № %s от %s' % (
                        accountNumber if accountNumber else u'б/н',
                        accountDate if accountDate else u'б/д') ]
        else:
            descr = [ u'к неуказанному счёту' ]
        workIndex = self.tabWorkType.currentIndex()
        if workIndex == 0:
            filterCode = 0
            filterDocument = ''
            filterRefuseType = ''
            filterNote = ''
        elif workIndex == 1:
            filterCode = self.cmbAnalysisAccountItems.currentIndex()
            filterDocument = forceStringEx(self.edtAnalysisDocument.text())
            filterRefuseType = self.cmbAnalysisPayRefuseType.currentText()
            filterNote = forceStringEx(self.edtAnalysisNote.text())
        elif workIndex == 2:
            filterCode = self.cmbHistoryAccountItems.currentIndex()
            filterDocument = forceStringEx(self.edtHistoryDocument.text())
            filterRefuseType = self.cmbHistoryPayRefuseType.currentText()
            filterNote = forceStringEx(self.edtHistoryNote.text())
        if filterDocument:
            filterDocument = u'С подтверждающим документом «%s»' % filterDocument
        if filterRefuseType:
            filterRefuseType = u'С причиной отказа %s' % filterRefuseType
        if filterNote:
            filterNote = u'С примечанием «%s»' % filterNote
        if filterCode == 0:  #0:Все
            descr.append(u'Все позиции')
        elif filterCode == 1: #1:Без подтверждения
            descr.append(u'Позиции без подтверждения')
        elif filterCode == 2: #2:Подтверждённые
            descr.append(u'Подтверждённые позиции')
            if filterDocument:
                descr.append(filterDocument)
            if filterNote:
                descr.append(filterNote)
        elif filterCode == 3: #3:Оплаченные
            descr.append(u'Оплаченные позиции')
            if filterDocument:
                descr.append(filterDocument)
            if filterNote:
                descr.append(filterNote)
        elif filterCode == 4: #4:Отказанные
            descr.append(u'Отказанные позиции')
            if filterDocument:
                descr.append(filterDocument)
            if filterRefuseType:
                descr.append(filterRefuseType)
            if filterNote:
                descr.append(filterNote)
        elif filterCode == 5: #5:Перевыставляемые
            descr.append(u'Перевыставляемые позиции')
            if filterDocument:
                descr.append(filterDocument)
            if filterRefuseType:
                descr.append(filterRefuseType)
            if filterNote:
                descr.append(filterNote)
        elif filterCode == 6: #6:Неперевыставляемые
            descr.append(u'Неперевыставляемые позиции')
            if filterDocument:
                descr.append(filterDocument)
            if filterRefuseType:
                descr.append(filterRefuseType)
            if filterNote:
                descr.append(filterNote)
        if workIndex == 2:
            descr.append(u'Фильтр по текущему пациенту')
        return u'\n'.join(descr)


    def updateAccountInfo(self):
        db = QtGui.qApp.db
        queryTable, cond = self.formAccountItemQueryParts()
        table = db.table('Account_Item')
        cond.append(table['master_id'].eq(self.currentAccountId))
        cond.append(table['deleted'].eq(0))
        if self.watchingAccountItemIdList:
            cond.append(table['id'].inlist(self.watchingAccountItemIdList))

        tableClient = db.table('Client')

        if self.edtFioFilter.text():
            fio = unicode(self.edtFioFilter.text()).split(' ')
            if len(fio) >= 1:
                cond.append(tableClient['lastName'].like(fio[0]+'%'))
            if len(fio) >= 2:
                cond.append(tableClient['firstName'].like(fio[1]+'%'))
            if len(fio) >= 3:
                cond.append(tableClient['patrName'].like(fio[2]+'%'))


        if not self.accountItemOrder:
            self.accountItemOrder = ', '.join([ tableClient['lastName'].name(),
                  tableClient['firstName'].name(),
                  tableClient['patrName'].name(),
                  tableClient['birthDate'].name(),
                  tableClient['sex'].name(),
                  table['id'].name()
                                             ])
        idList = db.getIdList(queryTable, table['id'].name(), cond, self.accountItemOrder)
        currentAccountItemId = self.tblAccountItems.currentItemId()
        curColumn = self.tblAccountItems.currentIndex().column()
        self.modelAccountItems.setIdList(idList)
        self.tblAccountItems.setCurrentItemId(currentAccountItemId, curColumn)
        self.updateAccountItemsPanel(idList)


    def form(self, contractIdList, begDate, endDate, orgStructureId, reexpose, reexposeInSeparateAccount, checkMes, onlyDispCOVID, onlyResearchOnCOVID, onlyTFOMS=False, exposeByOrgStruct=False):
        progressDialog = None
        self.resetBuilder()
        QtGui.qApp.setWaitCursor()
        try:
            if orgStructureId:
                personIdList = getOrgStructurePersonIdList(orgStructureId)
            else:
                personIdList = None
            try:
                progressDialog = CFormProgressDialog(self)
                progressDialog.setNumContracts(len(contractIdList))
                progressDialog.show()
                allAccountIdList = []
                self.mapOrgStructToBookkeeper = dict()
                if exposeByOrgStruct:
                    db = QtGui.qApp.db
                    stmt = "SELECT id, name, getBookkeeperId(id) as bookkeeperId FROM OrgStructure;"
                    query = db.query(stmt)
                    while query.next():
                        record = query.record()
                        self.mapOrgStructToBookkeeper[forceRef(record.value('id'))] = forceRef(record.value('bookkeeperId'))
                for contractId in contractIdList:
                    accountIdList = self.formByContract(
                        progressDialog, contractId, orgStructureId, personIdList, begDate, endDate, reexpose, reexposeInSeparateAccount, checkMes, onlyDispCOVID, onlyResearchOnCOVID, onlyTFOMS)
                    allAccountIdList.extend(accountIdList)
                    accountId = accountIdList[-1] if accountIdList else None
                    self.updateFilterAccountsEtc(accountId, order=self.accountOrder)
                # если по договорам не сформировано ни одного счета - выводим сообщение
                if QtGui.qApp.defaultKLADR()[:2] == u'23' and not allAccountIdList:
                    QtGui.QMessageBox().warning(self,
                                                u'Внимание!',
                                                u'Счёт не создан, информации нет!',
                                                QtGui.QMessageBox.Ok,
                                                QtGui.QMessageBox.Ok)
            except CFormProgressCanceled:
                pass
        finally:
            QtGui.qApp.restoreOverrideCursor()
            if progressDialog:
                progressDialog.close()
                progressDialog.deleteLater()


    def formByContract(self, progressDialog, contractId, orgStructureId, personIdList, begDate, endDate, reexpose, reexposeInSeparateAccount, checkMes, onlyDispCOVID, onlyResearchOnCOVID, onlyTFOMS):
        counterController = QtGui.qApp.counterController()
        if not counterController:
            QtGui.qApp.setCounterController(CCounterController(self))
        db = QtGui.qApp.db
        db.transaction()
        try:
            contractDescr = getContractDescr(contractId)
            progressDialog.setContractName(contractDescr.number+' '+forceString(contractDescr.date))
            accountPool = CAccountPool(contractDescr, QtGui.qApp.currentOrgId(), orgStructureId, endDate, reexposeInSeparateAccount, self.mapOrgStructToBookkeeper)
            accountFactory = accountPool.getAccount
            
            eventIdList = selectEvents(contractDescr, personIdList, begDate, endDate, reexpose, onlyDispCOVID, onlyResearchOnCOVID, onlyTFOMS)
            # mapServiceIdToVisitIdList = selectVisitsByActionServices(contractDescr, personIdList, nextDate, reexpose, onlyDispCOVID, onlyTFOMS)
            visitIdList = selectVisits(contractDescr, personIdList, begDate, endDate, reexpose, onlyDispCOVID, onlyResearchOnCOVID, onlyTFOMS)
            actionIdList = selectActions(contractDescr, personIdList, begDate, endDate, reexpose, onlyDispCOVID, onlyResearchOnCOVID, onlyTFOMS)
            # actionPropertyIdList = selectHospitalBedActionProperties(contractDescr, personIdList, nextDate, reexpose, onlyDispCOVID, onlyTFOMS)
            # eventIdServiceIdPairList = selectEventServicePairsForVisits(contractDescr, personIdList, nextDate) # пока невкурил как это перевыставлять(если это вообще используется)
            csgIdList = selectCsgs(contractDescr, personIdList, begDate, endDate, reexpose, onlyDispCOVID, onlyResearchOnCOVID, onlyTFOMS)
            if reexpose and QtGui.qApp.defaultKLADR()[:2] != u'23':
                reexposableIdList = selectReexposableAccountItems(contractDescr, endDate.addDays(1), onlyDispCOVID, onlyResearchOnCOVID)
                reexposableEventIdList = []
            else:
                reexposableEventIdList = selectReexposableEvents(contractDescr, begDate, endDate, onlyTFOMS=onlyTFOMS)
                reexposableIdList = []

            progressDialog.setNumContractSteps(len(eventIdList) +
                                               # sum(len(idList) for idList in mapServiceIdToVisitIdList.values()) +
                                               len(visitIdList) +
                                               len(actionIdList) +
                                               # len(actionPropertyIdList) +
                                               # len(eventIdServiceIdPairList) +
                                               len(reexposableIdList) +
                                               len(reexposableEventIdList) +
                                               len(csgIdList)
                                               )

            self.exposeByVisits(progressDialog, contractDescr, accountFactory, visitIdList, reexposableEventIdList)
            self.exposeByActions(progressDialog, contractDescr, accountFactory, actionIdList, reexposableEventIdList)
            self.exposeByEvents(progressDialog, contractDescr, accountFactory, eventIdList, checkMes, reexposableEventIdList)
            self.exposeByCsgs(progressDialog, contractDescr, accountFactory, csgIdList, reexposableEventIdList)
        
            if reexpose and QtGui.qApp.defaultKLADR()[:2] != u'23':
                self.reexpose(progressDialog, contractDescr, accountFactory, reexposableIdList)
            if contractDescr.exposeDiscipline != 2 and QtGui.qApp.defaultKLADR()[:2] != u'23':
                accountPool.addAccountIfEmpty(reexpose)
            accountPool.updateDetails()
            accountIdList = accountPool.getAccountIdList()
            beforeUpdateAccounts(accountIdList)
            updateAccounts(accountIdList)
            QtGui.qApp.delAllCounterValueIdReservation()
            db.commit()
            return accountIdList
        except:
            db.rollback()
            QtGui.qApp.resetAllCounterValueIdReservation()
            QtGui.qApp.logCurrentException()
            raise
        finally:
            if not counterController:
                QtGui.qApp.setCounterController(None)


    def getEventRecord(self, eventId):
        # for CAccountBuilder, we need eventType_id, client_id, exec_date
        return self.modelAccountItems.eventCache.get(eventId)


    def getClientRecord(self, clientId):
        # for CAccountBuilder, we need sex and birthDate
        return self.modelAccountItems.clientCache.get(clientId)


    def getCurrentEventId(self):
        itemId = self.tblAccountItems.currentItemId()
        if itemId:
            itemRecord = self.modelAccountItems.recordCache().get(itemId)
            if itemRecord:
                return forceRef(itemRecord.value('event_id'))
        return None


    def getCurrentIds(self):
        clientId = None
        eventId  = None
        visitId  = None
        actionId = None
        eventTypeId  = None
        serviceId    = None
        actionTypeId = None

        itemId = self.tblAccountItems.currentItemId()
        if itemId:
            itemRecord = self.modelAccountItems.recordCache().get(itemId)
            if itemRecord:
                eventId = forceRef(itemRecord.value('event_id'))
                visitId = forceRef(itemRecord.value('visit_id'))
                actionId = forceRef(itemRecord.value('action_id'))
                if eventId:
                    eventRecord = self.modelAccountItems.eventCache.get(eventId)
                    if eventRecord:
                        clientId = forceRef(eventRecord.value('client_id'))
                        eventTypeId = forceRef(eventRecord.value('eventType_id'))
                if visitId:
                    visitRecord = self.modelAccountItems.visitCache.get(visitId)
                    if visitRecord:
                        serviceId = forceRef(visitRecord.value('service_id'))
                if actionId:
                    actionRecord = self.modelAccountItems.actionCache.get(actionId)
                    if actionRecord:
                        actionTypeId = forceRef(actionRecord.value('actionType_id'))
        return (clientId, eventTypeId, serviceId, actionTypeId)


    def getCurrentClientId(self):
        eventId = self.getCurrentEventId()
        if eventId:
            eventRecord = self.modelAccountItems.eventCache.get(eventId)
            if eventRecord:
                return forceRef(eventRecord.value('client_id'))
        return None


    def prepareHistoryFilterParameters(self):
        clientId, eventTypeId, serviceId, actionTypeId = self.getCurrentIds()
        self.historyFilter = {}
        self.historyFilter['client_id']    = clientId
        self.historyFilter['eventType_id'] = eventTypeId
        self.historyFilter['service_id']   = serviceId
        self.historyFilter['actionType_id']   = actionTypeId


    def setPayStatus(self, contractDescr, accountItemIdList, payParams):
        date = toVariant(payParams.get('date', QDate()))
        number = toVariant(payParams.get('number', ''))
        note = toVariant(payParams.get('note', ''))
        accepted = forceBool(payParams.get('accepted', False))
        factPayed = forceBool(payParams.get('factPayed', False))
        dateQDate = forceDate(date)
        numberString = forceString(number)
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
                'id, master_id, event_id, visit_id, action_id, date, number, refuseType_id, reexposeItem_id, note, payedSum, sum',
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
            self.updateFilterAccountsEtc(order=self.accountOrder)
            self.modelAccountItems.invalidateRecordsCache()
            self.tblAccountItems.setCurrentItemId(currentAccountItemId)
        except:
            db.rollback()
            QtGui.qApp.logCurrentException()
            raise

    def updateDocsPayStatus(self,  accountItem, contractDescr, bits):
        updateDocsPayStatus(accountItem, contractDescr.payStatusMask, bits)


    def execAccountItemsReport(self, reportClass):
        def execAccountItemsReportInt():
            report = reportClass(self)
            descr = self.formAccountItemReportDescription()
            params = { 'accountId': self.currentAccountId,
                        'selectedAccountIdList': [self.modelAccounts.idList()[index.row()] for index in self.selectionModelAccounts.selectedRows()] if len(self.selectionModelAccounts.selectedRows())>1 else None,
                       'accountItemIdList': self.modelAccountItems.idList()
                     }
            reportTxt = report.build(descr, params)
            view = CReportViewDialog(self)
            view.setWindowTitle(report.title())
            view.setText(reportTxt)
            if report.pageFormat:
                view.setPageFormat(report.pageFormat)
            return view
        view = QtGui.qApp.callWithWaitCursor(self, execAccountItemsReportInt)
        view.exec_()


    def execAccountItemsReportInsurer(self, reportClass, orgInsurerId = None):
        def execAccountItemsReportInsurerInt():
            report = reportClass(self)
            descr = self.formAccountItemReportDescription()
            params = {'accountId'    : self.currentAccountId,
                      'accountItemIdList': self.modelAccountItems.idList(),
                      'selectedAccountIdList': [self.modelAccounts.idList()[index.row()] for index in self.selectionModelAccounts.selectedRows()] if len(self.selectionModelAccounts.selectedRows())>1 else None,
                      'orgInsurerId' : orgInsurerId
                     }
            if orgInsurerId:
                reportTxt = report.build(descr, params)
            view = CReportViewDialog(self)
            view.setWindowTitle(report.title())
            view.setText(reportTxt)
            return view
        view = QtGui.qApp.callWithWaitCursor(self, execAccountItemsReportInsurerInt)
        view.exec_()


    def execAccountItemsReportDetailedPolyclinicSummary(self, reportClass, detailed = None):
        def execAccountItemsDetailedPolyclinicSummaryInt():
            report = reportClass(self)
            descr = self.formAccountItemReportDescription()
            params = {'accountId'    : self.currentAccountId,
                      'accountItemIdList': self.modelAccountItems.idList(),
                      'selectedAccountIdList' : [self.modelAccounts.idList()[index.row()] for index in self.selectionModelAccounts.selectedRows()] if len(self.selectionModelAccounts.selectedRows())>1 else None,
                      'detailed' : detailed if detailed else False
                     }
            reportTxt = report.build(descr, params)
            view = CReportViewDialog(self)
            view.setWindowTitle(report.title())
            view.setText(reportTxt)
            if report.pageFormat:
                view.setPageFormat(report.pageFormat)
            return view
        view = QtGui.qApp.callWithWaitCursor(self, execAccountItemsDetailedPolyclinicSummaryInt)
        view.exec_()


    def __setupDocumentAndPayRefuseType(self, index, edtDocument, cmbPayRefuseType, edtNote):
        edtEnabled = index != 0 # index not in (0, 1)
        edtDocument.setEnabled(edtEnabled)
        edtNote.setEnabled(edtEnabled)
        if index == 4:
            cmbPayRefuseType.setFilter('')
            cmbPayRefuseType.setEnabled(True)
        elif index == 5:
            cmbPayRefuseType.setFilter('rerun!=0 AND finance_id=\'%s\'' % self.currentFinanceId)
            cmbPayRefuseType.setEnabled(True)
        elif index == 6:
            cmbPayRefuseType.setFilter('rerun=0 AND finance_id=\'%s\'' % self.currentFinanceId)
            cmbPayRefuseType.setEnabled(True)
        else:
            cmbPayRefuseType.setEnabled(False)


    def runGenRep(self, formatName):
        if formatName:
            queryTable, cond = self.formAccountItemQueryParts()
#                cond.append(db.table('Account_Item')['master_id'].eq(self.currentAccountId))
            if cond:
                cond = QtGui.qApp.db.joinAnd(cond)
            else:
                cond = ''
            descr = self.formAccountItemReportDescription()
            (started, error, exitCode) = QtGui.qApp.execProgram('genrep', [formatName, self.currentAccountId, cond, descr])


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelContracts_currentChanged(self, current, previous):
        self.updateFilterAccountsEtc(order=self.accountOrder)


    @pyqtSignature('QModelIndex')
    def on_treeContracts_doubleClicked(self, index):
        contractIdList = self.getContractIdList(self.treeContracts.currentIndex())
        if contractIdList and len(contractIdList) == 1:
            dialog = CContractEditor(self)
            try:
                dialog.freezeHeadFields()
                dialog.load(contractIdList[0])
                dialog.exec_()
            finally:
                dialog.deleteLater()


    @pyqtSignature('int')
    def on_tabWorkType_currentChanged(self, index):
        if index == 2:
            self.prepareHistoryFilterParameters()
        self.updateFilterAccountsEtc(order=self.accountOrder)


    @pyqtSignature('int')
    def on_cmbAnalysisAccountItems_currentIndexChanged(self, index):
        self.__setupDocumentAndPayRefuseType(
            index, self.edtAnalysisDocument, self.cmbAnalysisPayRefuseType, self.edtAnalysisNote)


    @pyqtSignature('QAbstractButton*')
    def on_bbxAnalysis_clicked(self, button):
        buttonCode = self.bbxAnalysis.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.updateFilterAccountsEtc(order=self.accountOrder)
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.resetAnalysisPage()
            self.updateFilterAccountsEtc(order=self.accountOrder)


    @pyqtSignature('int')
    def on_cmbHistoryAccountItems_currentIndexChanged(self, index):
        self.__setupDocumentAndPayRefuseType(
            index, self.edtHistoryDocument, self.cmbHistoryPayRefuseType, self.edtHistoryNote)


    @pyqtSignature('QAbstractButton*')
    def on_bbxHistory_clicked(self, button):
        buttonCode = self.bbxHistory.standardButton(button)
###        self.prepareHistoryFilterParameters()
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.updateFilterAccountsEtc(order=self.accountOrder)
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.resetHistoryPage()
            self.updateFilterAccountsEtc(order=self.accountOrder)


    def editCurrentAccount(self):
        isAccountant = QtGui.qApp.userHasAnyRight(accountantRightList)
        if isAccountant:
            dialog = CAccountEditDialog(self)
            try:
                id = self.tblAccounts.currentItemId()
                if id:
                    dialog.load(id)
                    if dialog.exec_():
                        self.updateFilterAccountsEtc(order=self.accountOrder)
            finally:
                dialog.deleteLater()


    @pyqtSignature('QModelIndex')
    def on_tblAccounts_doubleClicked(self, index):
        self.editCurrentAccount()


    @pyqtSignature('QModelIndex')
    def on_tblAccountItems_doubleClicked(self, index):
        self.on_actOpenEvent_triggered()


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelAccounts_currentRowChanged(self, current, previous):
        self.currentAccountId = self.tblAccounts.itemId(current)
        self.currentFinanceId = None
        if self.currentAccountId:
            contractId = forceRef(QtGui.qApp.db.translate(
                'Account',  'id', self.currentAccountId, 'contract_id'))
            if contractId:
                self.currentFinanceId = forceRef(QtGui.qApp.db.translate(
                    'Contract', 'id', contractId, 'finance_id'))
        self.updateAccountInfo()
        if self.tblAccountItems.horizontalHeader().isSortIndicatorShown():
            # если уже производилась сортировка таблицы перс. счетов
            # чтобы setAccountItemsSort не менял сортировку
            self.isAscendingAccountItems = not self.isAscendingAccountItems
            self.setAccountItemsSort(self.tblAccountItems.horizontalHeader().sortIndicatorSection())

    @pyqtSignature('')
    def on_btnApplyFilter_clicked(self):
        self.updateAccountInfo()

    @pyqtSignature('')
    def on_mnuAccounts_aboutToShow(self):
        isWatchMode = (self.eventIdWatching or self.actionIdWatching or self.visitIdWatching)
        isAccountant = QtGui.qApp.userHasAnyRight(accountantRightList)
        currentRow = self.tblAccounts.currentIndex().row()
        itemPresent = currentRow>=0 and isAccountant
        enablePrint = False
        if itemPresent:
            exportInfo = getAccountExportFormat(self.currentAccountId).split()
            if exportInfo:
#                enablePrint = exportInfo[0] in ('RD1', 'RD2', 'RD3', 'RD4', 'RD-DS', 'RD5',  'RD6', 'R51DD2010')
                enablePrint = bool(exportInfo[0])
        else:
            enablePrint = False

        self.actEditAccount.setEnabled(itemPresent)
        self.actPrintAccount.setEnabled(enablePrint and not isWatchMode)
        self.actPrintAccountRegistry.setEnabled(enablePrint and not isWatchMode)
        self.actPrintAccountSummary.setEnabled(itemPresent and not isWatchMode)
        self.actPrintAccountInsurer.setEnabled(itemPresent and not isWatchMode)
        self.actReportServiceByDoctors.setEnabled(itemPresent and not isWatchMode)
        self.actReportByDoctorsEx.setEnabled(itemPresent and not isWatchMode)
        self.actReportByServicesEx.setEnabled(itemPresent and not isWatchMode)
        self.actCheckMesInAccount.setEnabled(itemPresent and not isWatchMode)
        self.actSelectAllAccounts.setEnabled(itemPresent)
        self.actDeleteAccounts.setEnabled(itemPresent and self.checkDeleteRights())
        self.actDeleteAccountsAtOnce.setEnabled(itemPresent and ((QtGui.qApp.userHasAnyRight([urDeleteAccountsAtOnce]) and self.checkDeleteRights()) or QtGui.qApp.userHasRight(urAdmin)))
        self.actDeleteAccountItemsWithoutRKEY.setEnabled(itemPresent and ((QtGui.qApp.userHasAnyRight([urDeleteAccountItem]) and self.checkDeleteRights()) or QtGui.qApp.userHasRight(urAdmin)))
        self.actDeleteAccountItemsWithoutFKEY.setEnabled(itemPresent and ((QtGui.qApp.userHasAnyRight([urDeleteAccountItem]) and self.checkDeleteRights()) or QtGui.qApp.userHasRight(urAdmin)))
        self.actDeleteAccountItemsAllRKEY.setEnabled(itemPresent and QtGui.qApp.userHasRight(urDeleteRKEY))
        self.actDeleteAccountItemsAllFKEY.setEnabled(itemPresent and QtGui.qApp.userHasRight(urDeleteRKEY))
        
    
    def checkDeleteRights(self):
        if QtGui.qApp.userHasAnyRight([urAdmin, urDeleteAccount]):
            return True
        selectedRowList = self.tblAccounts.selectedRowList()
        model = self.tblAccounts.model()
        contractIds = []
        contracts = []
        for row in selectedRowList:
            record = model.getRecordByRow(row)
            contractId = forceInt(record.value('contract_id'))
            if contractId not in contractIds:
                contractIds.append(contractId)
        for row in contractIds:
            contract = forceRef(QtGui.qApp.db.translate(
                'Contract', 'id', row, 'finance_id'))
            if contract not in contracts:
                contracts.append(contract)
        if contracts:
            for contract in contracts:
                if not QtGui.qApp.userHasRight(accountantDeleteRightList[contract]):
                    return False
            return True
        return False
        

    @pyqtSignature('')
    def on_actEditAccount_triggered(self):
        self.editCurrentAccount()


    @pyqtSignature('')
    def on_actPrintAccount_triggered(self):
        if self.currentAccountId:
            formatName = ''
            exportInfo = getAccountExportFormat(self.currentAccountId).split()
            if exportInfo:
                if exportInfo[0] == 'RD1':
                    formatName = 'CH1'
                elif exportInfo[0] == 'RD2':
                    formatName = 'CH2'
                elif exportInfo[0] in ('RD3', 'RD-DS'):
                    formatName = 'CH3'
                elif exportInfo[0] == 'RD4':
                    formatName = 'CH4'
                elif exportInfo[0] in ('RD5', 'RD6'):
                    formatName = 'CH5'
                elif exportInfo[0] == 'RD7':
                    formatName = 'CH7'
                elif exportInfo[0] == 'R51DD2010':
                    formatName = 'CH51DD2010'
                else:
                    formatName = 'CH' + exportInfo[0]
            self.runGenRep(formatName)


    @pyqtSignature('')
    def on_actPrintAccountSummary_triggered(self):
        if self.currentAccountId:
            self.execAccountItemsReport(CAccountSummary)


    @pyqtSignature('')
    def on_actPrintFinanceReportByAidProfileAndSocStatus_triggered(self):
        CFinanceReportByAidProfileAndSocStatus(self).exec_()


    @pyqtSignature('')
    def on_actPrintPolyclinicSummary_triggered(self):
        if self.currentAccountId:
            if QtGui.QMessageBox.question( self,
                                       u'Внимание!',
                                       u'Детализировать по врачам?',
                                       QtGui.QMessageBox.Yes|QtGui.QMessageBox.No,
                                       QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes:
                self.execAccountItemsReportDetailedPolyclinicSummary(CPolyclinicAccountSummary, detailed = True)
            else:
                self.execAccountItemsReportDetailedPolyclinicSummary(CPolyclinicAccountSummary)


    @pyqtSignature('')
    def on_actPrintStationarySummary_triggered(self):
        if self.currentAccountId:
            self.execAccountItemsReport(CStationaryAccountSummary)

    # @pyqtSignature('')
    def on_actReportAccountTotal(self):
        self.edtFioFilter.clear()
        self.updateAccountInfo()
        accountItemIdList = self.modelAccountItems.idList()
        if len(self.tblAccounts.selectedItemIdList()) > 0:
            report = CReportAccountingTotal(self, self.currentAccountId, accountItemIdList, self.tblAccounts.selectedItemIdList())

            report.exec_()


    @pyqtSignature('')
    def on_actCured_triggered(self):
        dialog = CCuredSetupDialog(self, self.treeContracts.currentIndex())
        templates = getPrintTemplates('accountList')
        if not templates:
            QtGui.QMessageBox.warning( self,
                                       u'Внимание!',
                                       u'Не найден шаблон печати с контекстом accountList',
                                       QtGui.QMessageBox.Close)
            return
        if not dialog.exec_():
            return
        templateId = templates[0].id
        begDate = dialog.getBegDate()
        endDate = dialog.getEndDate()
        contractIndex = dialog.getContractIndex()
        contractIdList = self.getContractIdList(contractIndex)
        idList = []
        db = QtGui.qApp.db
        tableAccountItem = db.table('Account_Item')
        tableEvent = db.table('Event')
        tableAccount = db.table('Account')
        table = tableAccountItem.leftJoin(tableEvent, tableEvent['id'].eq(tableAccountItem['event_id']))
        table = table.leftJoin(tableAccount, tableAccount['id'].eq(tableAccountItem['master_id']))
        cond = [ tableEvent['execDate'].ge(begDate),
            tableEvent['execDate'].le(endDate),
            tableAccount['contract_id'].inlist(contractIdList)
        ]
        order = [tableAccount['date'].name(),
                 tableAccount['number'].name(),
                 tableAccount['id'].name()
               ]

        idList = db.getDistinctIdList(table,
                                      idCol=tableAccountItem['master_id'].name(),
                                      where=cond,
                                      order=order
                                     )

        context = CInfoContext()
        accountInfoList = context.getInstance(CAccountInfoList, tuple(idList))
        contractList = context.getInstance(CContractInfoList, tuple(contractIdList))
        begDate = CDateInfo(begDate)
        endDate = CDateInfo(endDate)
        data = { 'accountList' : accountInfoList,
                        'filterBegDate' : begDate,
                        'filterEndDate' : endDate,
                        'filterContractList' : contractList
               }
        applyTemplate(self, templateId, data)


    @pyqtSignature('')
    def on_actPrintAccountInsurer_triggered(self):
        if self.currentAccountId:
            ok, orgInsurerId = self.selectInsurer(True)
            if orgInsurerId:
                self.execAccountItemsReportInsurer(CAccountSummary, orgInsurerId)


    def selectInsurer(self, strict):
        ok = False
        orgId = None
        filterDialog = CInsurerFilterDialog(self, strict)
        try:
            ok = filterDialog.exec_()
            if ok:
                orgId = filterDialog.orgId()
        finally:
            filterDialog.deleteLater()
        return ok, orgId


    @pyqtSignature('')
    def on_actPrintAccountRegistry_triggered(self):
        if self.currentAccountId:
            formatName = ''
            exportInfo = getAccountExportFormat(self.currentAccountId).split()
            if exportInfo:
                if exportInfo[0] == 'RD-DS':
                    formatName = 'RD3'
#                if exportInfo[0] in ('RD1', 'RD2', 'RD3', 'RD4', 'RD5', 'RD6', 'R51DD2010'):
#                    formatName = exportInfo[0]
                else:
                    formatName = exportInfo[0]
            self.runGenRep(formatName)


    @pyqtSignature('')
    def on_actCheckMesInAccount_triggered(self):
        if self.currentAccountId:
            self.resetBuilder()
            db = QtGui.qApp.db
            contractId = forceRef(db.translate('Account',  'id', self.currentAccountId, 'contract_id'))
            contractDescr = getContractDescr(contractId)
            financeId    = contractDescr.financeId
            # фишка в sum для списков; по определению это reduce(operator.add, a, [])
            tariffList = dict([(tariff.id, tariff) for tariff in sum(contractDescr.tariffVisitsByMES.values(), [])])
            semifinishedMesRefuseTypeId = self.getSemifinishedMesRefuseTypeId(financeId)
            itemIdList = self.tblAccountItems.selectedItemIdList()
            tableAccountItem = db.table('Account_Item')
            tableContractTariff = db.table('Contract_Tariff')
            table = tableAccountItem.leftJoin(tableContractTariff, tableContractTariff['id'].eq(tableAccountItem['tariff_id']))
            cond = [tableAccountItem['id'].inlist(itemIdList),
                    db.joinOr([tableAccountItem['date'].isNull(),
                              tableAccountItem['refuseType_id'].eq(semifinishedMesRefuseTypeId)]),
                    tableContractTariff['tariffType'].eq(CTariff.ttVisitsByMES)
                   ]
            modifiedItemCount = 0
            amountModified = False
            for accountItem in db.getRecordList(table, 'Account_Item.*', cond):
                itemModified = False
                eventId = forceRef(accountItem.value('event_id'))
                mesId = forceRef(db.translate('Event', 'id', eventId, 'MES_id'))
                tariffId = forceRef(accountItem.value('tariff_id'))
                tariff = tariffList.get(tariffId, None)
                if tariff:
                    amount = float(getMesAmount(eventId, mesId))
                    amount, price, sum_ = tariff.evalAmountPriceSum(amount)
                    norm = self.getMesNorm(mesId)
                    if amount<norm and accountItem.value('refuseType_id').isNull():
                        self.rejectAccountItemBySemifinishedMes(accountItem, financeId)
                        itemModified = True
                    if amount != forceDouble(accountItem.value('amount')): # верую, что небольшие целые числа не портятся
                        accountItem.setValue('amount', toVariant(amount))
                        accountItem.setValue('price',  toVariant(price))
                        accountItem.setValue('sum',    toVariant(sum_))
                        itemModified = True
                        amountModified = True
                    if itemModified:
                        db.updateRecord(tableAccountItem, accountItem)
                        modifiedItemCount+=1
            if amountModified:
                updateAccountTotals(self.currentAccountId)
                self.updateFilterAccountsEtc(order=self.accountOrder)
            currentAccountItemId = self.tblAccountItems.currentItemId()
            if modifiedItemCount:
                self.modelAccountItems.invalidateRecordsCache()
                self.tblAccountItems.setCurrentItemId(currentAccountItemId)
            QtGui.QMessageBox.information( self,
                                    u'Проверка счёта',
                                    u'Проверка счёта на соответствие МЭС закончена.'
                                    +(('\n'
                                       + agreeNumberAndWord(modifiedItemCount, (u'Измененa', u'Изменено', u'Изменено'))
                                       + ' '
                                       + formatNum(modifiedItemCount, (u'позиция', u'позиции', u'позиций'))
                                       +u' счёта')
                                      if modifiedItemCount
                                      else ''),
                                     QtGui.QMessageBox.Ok,
                                     QtGui.QMessageBox.Ok)


    @pyqtSignature('')
    def on_actSelectAllAccounts_triggered(self):
        self.tblAccounts.selectAll()


    @pyqtSignature('')
    def on_actDeleteAccounts_triggered(self):
#        self.tblAccounts.removeCurrentRow()
        self.tblAccounts.removeSelectedRows()
        self.updateAccountsPanel(self.modelAccounts.idList())


    @pyqtSignature('')
    def on_actDeleteAccountsAtOnce_triggered(self):
        currentRow = self.tblAccounts.currentIndex().row()
        newSelection = []
        deletedCount = 0
        rows = self.tblAccounts.selectedRowList()
        rows.sort()
        idToRemove = {}
        cnt = 0
        for row in rows:
            id = self.tblAccounts.model()._idList[row]
            idToRemove[id] = canRemoveAccount(id)
            cnt += idToRemove[id]

        buttons = QtGui.QMessageBox.Yes | QtGui.QMessageBox.No
        if QtGui.QMessageBox.question(self.tblAccounts, u'Внимание!', u'Выбрано реестров: {0}\nБудет удалено: {1}\nВыбранные реестры будут удалены все сразу без дополнительных предупреждений!'.format(len(rows), cnt),
                                              buttons, QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes:
            QtGui.qApp.setWaitCursor()
            for row in rows:
                actualRow = row - deletedCount
                self.tblAccounts.setCurrentRow(actualRow)
                if idToRemove[id]:
                    self.tblAccounts.model().removeRow(actualRow)
                    deletedCount += 1
                    if currentRow > row:
                        currentRow -= 1
                else:
                    newSelection.append(actualRow)
            if newSelection:
                self.tblAccounts.setSelectedRowList(newSelection)
            else:
                self.tblAccounts.setCurrentRow(currentRow)

            self.updateAccountsPanel(self.modelAccounts.idList())
            QtGui.qApp.restoreOverrideCursor()


    @pyqtSignature('')
    def on_actDeleteAccountItemsWithoutRKEY_triggered(self):
        db = QtGui.qApp.db
        tableAccountItem = db.table('Account_Item')
        tableSARK = db.table('soc_Account_RowKeys')
        table = tableAccountItem.leftJoin(tableSARK, db.joinAnd([tableAccountItem['event_id'].eq(tableSARK['event_id']), 'soc_Account_RowKeys.row_id = coalesce(Account_Item.action_id, Account_Item.visit_id, Account_Item.eventCSG_id, Account_Item.event_id)', tableSARK['typeFile'].eq('U')]))
        cond = [tableAccountItem['master_id'].inlist(self.tblAccounts.selectedItemIdList()), tableAccountItem['deleted'].eq(0), db.joinOr([tableSARK['key'].isNull(), tableSARK['key'].eq('')])]
        itemIdList = db.getIdList(table, idCol='Account_Item.id', where=cond)
        n = len(itemIdList)
        m = len(self.tblAccounts.selectedItemIdList())
        message = u'Вы действительно хотите удалить {0} без RKEY из {1}?'.format(formatNum1(n, (u'запись', u'записи', u'записей')),
                                                                                 formatNum1(m, (u'реестра', u'реестров', u'реестров')))
        if n == 0:
            QtGui.QMessageBox.question(self,
                                       u'Внимание!',
                                       u"Удаление невозможно. В {0} 0 записей без RKEY".format(formatNum1(m, (u'выбранном реестре', u'выбранных реестрах', u'выбранных реестрах'))),
                                       QtGui.QMessageBox.Ok,
                                       QtGui.QMessageBox.Ok)
        elif QtGui.QMessageBox.question(self,
                                      u'Внимание!',
                                      message,
                                      QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                      QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes:

            QtGui.qApp.setWaitCursor()
            try:
                db.transaction()
                try:
                    for accountId in self.tblAccounts.selectedItemIdList():
                        clearPayStatus(accountId, itemIdList)
                    db.deleteRecordSimple(tableAccountItem, tableAccountItem['id'].inlist(itemIdList))
                    for accountId in self.tblAccounts.selectedItemIdList():
                        updateAccount(accountId)
                    db.commit()
                except:
                    db.rollback()
                    QtGui.qApp.logCurrentException()
                    raise
                self.updateAccountInfo()
                self.updateFilterAccountsEtc(self.currentAccountId, order=self.accountOrder)
            finally:
                QtGui.qApp.restoreOverrideCursor()
    
    
    @pyqtSignature('')
    def on_actDeleteAccountItemsAllRKEY_triggered(self):
        db = QtGui.qApp.db
        tableAccountItem = db.table('Account_Item')
        tableSARK = db.table('soc_Account_RowKeys')
        cond = [tableAccountItem['master_id'].inlist(self.tblAccounts.selectedItemIdList()), tableAccountItem['deleted'].eq(0)]
        itemIdList = db.getIdList(tableAccountItem, idCol='Account_Item.event_id', where=cond)
        
        message = u'Вы действительно хотите удалить ранее импортированные RKEY для всех выбранных реестров?'
        if QtGui.QMessageBox.question(self, u'Внимание!', message, QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                        QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes:
            QtGui.qApp.setWaitCursor()
            try:
                db.transaction()
                try:
                    db.updateRecords(tableSARK, 'soc_Account_RowKeys.`key` = NULL', db.joinAnd([tableSARK['event_id'].inlist(itemIdList), tableSARK['typeFile'].ne('F')]))
                    db.commit()
                except:
                    db.rollback()
                    QtGui.qApp.logCurrentException()
                    raise
                self.updateFilterAccountsEtc(self.currentAccountId, order=self.accountOrder)
            finally:
                QtGui.qApp.restoreOverrideCursor()


    @pyqtSignature('')
    def on_actDeleteAccountItemsWithoutFKEY_triggered(self):
        db = QtGui.qApp.db
        tableAccountItem = db.table('Account_Item')
        tableSARK = db.table('soc_Account_RowKeys')
        table = tableAccountItem.leftJoin(tableSARK, db.joinAnd([tableAccountItem['event_id'].eq(tableSARK['event_id']), tableSARK['typeFile'].eq('F')]))
        cond = [tableAccountItem['master_id'].inlist(self.tblAccounts.selectedItemIdList()), tableAccountItem['deleted'].eq(0),
                db.joinOr([tableSARK['key'].isNull(), tableSARK['key'].eq('')])]
        itemIdList = db.getIdList(table, idCol='Account_Item.id', where=cond)
        n = len(itemIdList)
        m = len(self.tblAccounts.selectedItemIdList())
        message = u'Вы действительно хотите удалить {0} без FKEY из {1}?'.format(formatNum1(n, (u'запись', u'записи', u'записей')),
                                                                                 formatNum1(m, (u'реестра', u'реестров', u'реестров')))
        if n == 0:
            QtGui.QMessageBox.question(self, u'Внимание!', u"Удаление невозможно. В {0} 0 записей без FKEY".format(
                formatNum1(m, (u'выбранном реестре', u'выбранных реестрах', u'выбранных реестрах'))),
                                       QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ok)
        elif QtGui.QMessageBox.question(self, u'Внимание!', message, QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                        QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes:

            QtGui.qApp.setWaitCursor()
            try:
                db.transaction()
                try:
                    for accountId in self.tblAccounts.selectedItemIdList():
                        clearPayStatus(accountId, itemIdList)
                    db.deleteRecordSimple(tableAccountItem, tableAccountItem['id'].inlist(itemIdList))
                    for accountId in self.tblAccounts.selectedItemIdList():
                        updateAccount(accountId)
                    db.commit()
                except:
                    db.rollback()
                    QtGui.qApp.logCurrentException()
                    raise
                self.updateAccountInfo()
                self.updateFilterAccountsEtc(self.currentAccountId, order=self.accountOrder)
            finally:
                QtGui.qApp.restoreOverrideCursor()
    
    
    @pyqtSignature('')
    def on_actDeleteAccountItemsAllFKEY_triggered(self):
        db = QtGui.qApp.db
        tableAccountItem = db.table('Account_Item')
        tableSARK = db.table('soc_Account_RowKeys')
        cond = [tableAccountItem['master_id'].inlist(self.tblAccounts.selectedItemIdList()), tableAccountItem['deleted'].eq(0)]
        itemIdList = db.getIdList(tableAccountItem, idCol='Account_Item.event_id', where=cond)
        
        message = u'Вы действительно хотите удалить ранее импортированные FKEY для всех выбранных реестров?'
        if QtGui.QMessageBox.question(self, u'Внимание!', message, QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                      QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes:
            QtGui.qApp.setWaitCursor()
            try:
                db.transaction()
                try:
                    db.updateRecords(tableSARK, 'soc_Account_RowKeys.`key` = NULL',
                                     [tableSARK['event_id'].inlist(itemIdList),
                                     tableSARK['typeFile'].eq('F')])
                    db.commit()
                except:
                    db.rollback()
                    QtGui.qApp.logCurrentException()
                    raise
                self.updateFilterAccountsEtc(self.currentAccountId, order=self.accountOrder)
            finally:
                QtGui.qApp.restoreOverrideCursor()


    @pyqtSignature('')
    def on_actDeleteAccountItemsRKEY_triggered(self):
        db = QtGui.qApp.db
        selectedItemIdList = self.tblAccountItems.selectedItemIdList()
        tableAccountItem = db.table('Account_Item')
        tableSARK = db.table('soc_Account_RowKeys')
        cond = [tableAccountItem['id'].inlist(selectedItemIdList)]
        itemIdList = db.getIdList(tableAccountItem, idCol='Account_Item.event_id', where=cond)
        message = u'Вы действительно хотите удалить ранее импортированные RKEY для выбранных персональных счетов?'
        if QtGui.QMessageBox.question(self, u'Внимание!', message, QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                        QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes:
            QtGui.qApp.setWaitCursor()
            try:
                db.transaction()
                try:
                    db.updateRecords(tableSARK, 'soc_Account_RowKeys.`key` = NULL', db.joinAnd([tableSARK['event_id'].inlist(itemIdList), tableSARK['typeFile'].ne('F')]))
                    db.commit()
                except:
                    db.rollback()
                    QtGui.qApp.logCurrentException()
                    raise
                self.updateFilterAccountsEtc(self.currentAccountId, order=self.accountOrder)
            finally:
                QtGui.qApp.restoreOverrideCursor()


    @pyqtSignature('')
    def on_actDeleteAccountItemsFKEY_triggered(self):
        db = QtGui.qApp.db
        selectedItemIdList = self.tblAccountItems.selectedItemIdList()
        tableAccountItem = db.table('Account_Item')
        tableSARK = db.table('soc_Account_RowKeys')
        cond = [tableAccountItem['id'].inlist(selectedItemIdList)]
        itemIdList = db.getIdList(tableAccountItem, idCol='Account_Item.event_id', where=cond)
        message = u'Вы действительно хотите удалить ранее импортированные FKEY для выбранных персональных счетов?'
        if QtGui.QMessageBox.question(self, u'Внимание!', message, QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                      QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes:
            QtGui.qApp.setWaitCursor()
            try:
                db.transaction()
                try:
                    db.updateRecords(tableSARK, 'soc_Account_RowKeys.`key` = NULL',
                                     [tableSARK['event_id'].inlist(itemIdList),
                                     tableSARK['typeFile'].eq('F')])
                    db.commit()
                except:
                    db.rollback()
                    QtGui.qApp.logCurrentException()
                    raise
                self.updateFilterAccountsEtc(self.currentAccountId, order=self.accountOrder)
            finally:
                QtGui.qApp.restoreOverrideCursor()


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelAccountItems_currentRowChanged(self, current, previous):
        currentAccountItemId = self.tblAccountItems.itemId(current)
        self.updateAccountItemInfo(currentAccountItemId)


    @pyqtSignature('')
    def on_mnuAccountItems_aboutToShow(self):
        isWatchMode = (self.eventIdWatching or self.actionIdWatching or self.visitIdWatching)
        isAccountant = QtGui.qApp.userHasAnyRight(accountantRightList)
        currentRow = self.tblAccountItems.currentIndex().row()
        itemPresent = currentRow>=0 and isAccountant
        self.actEditClient.setEnabled(itemPresent and QtGui.qApp.userHasAnyRight([urAdmin, urRegTabWriteRegistry, urRegTabReadRegistry]) and not isWatchMode)
        self.actOpenEvent.setEnabled(itemPresent and not isWatchMode)
        self.actSetPayment.setEnabled(itemPresent)
        self.actEditPayment.setEnabled(itemPresent)
        self.actSelectExposed.setEnabled(itemPresent and not isWatchMode)
        self.actSelectAll.setEnabled(itemPresent and not isWatchMode)
        self.actReportByRegistry.setEnabled(itemPresent and not isWatchMode)
        self.actReportByClients.setEnabled(itemPresent and not isWatchMode)
        self.actReportByDoctors.setEnabled(itemPresent and not isWatchMode)
        self.actReportByServices.setEnabled(itemPresent and not isWatchMode)
        self.actDetailedReportByServices.setEnabled(itemPresent and not isWatchMode)
        self.actDetailedReportByServicesExpenses.setEnabled(itemPresent and not isWatchMode)
        self.actDeleteAccountItemsRKEY.setEnabled(itemPresent and QtGui.qApp.userHasRight(urDeleteRKEY))
        self.actDeleteAccountItemsFKEY.setEnabled(itemPresent and QtGui.qApp.userHasRight(urDeleteRKEY))
        self.actDeleteAccountItems.setEnabled(itemPresent and ((QtGui.qApp.userHasAnyRight([urDeleteAccountItem]) and self.checkDeleteRights()) or QtGui.qApp.userHasRight(urAdmin)))
        self.actDeleteAccountItemsPersonalAccount.setEnabled(itemPresent and ((QtGui.qApp.userHasAnyRight([urDeleteAccountItem]) and self.checkDeleteRights()) or QtGui.qApp.userHasRight(urAdmin)))
        self.actShowAccountItemInfo.setEnabled(itemPresent)
        self.actChangeEventExpose.setEnabled(QtGui.qApp.userHasRight(urAccessChangeEventExpose))


    @pyqtSignature('')
    def on_actEditClient_triggered(self):
        clientId = self.getCurrentClientId()
        if clientId and QtGui.qApp.userHasAnyRight([urAdmin, urRegTabWriteRegistry, urRegTabReadRegistry]):
            dialog = CClientEditDialog(self)
            try:
                dialog.load(clientId)
                if dialog.exec_():
                    self.modelAccountItems.invalidateRecordsCache()
            finally:
                dialog.deleteLater()


    @pyqtSignature('')
    def on_actOpenEvent_triggered(self):
        eventId = self.getCurrentEventId()
        if eventId:
            formClass = getEventFormClass(eventId)
            dialog = formClass(self)
            try:
                dialog.load(eventId)
                dialog.exec_()
                # вставка обращений
                if QtGui.qApp.checkGlobalPreference(u'23:obr', u'да'):
                    QtGui.qApp.db.query('CALL InsertObr(%d);' % eventId)
            finally:
                dialog.deleteLater()
                self.modelAccounts.invalidateRecordsCache()
                self.updateAccountInfo()


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
            contractId = forceRef(QtGui.qApp.db.translate('Account',  'id', self.currentAccountId, 'contract_id'))
            financeId = forceRef(QtGui.qApp.db.translate('Contract', 'id', contractId, 'finance_id'))
            accountItemId = self.tblAccountItems.currentItemId()
            itemIdList = self.tblAccountItems.selectedItemIdList()
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
                    dialog.setAccountItemsCount(len(itemIdList))
                    dialog.setParams(payParams)
                    if dialog.exec_():
                        self.payParams = dialog.params()
                        self.setPayStatus(getContractDescr(contractId), itemIdList, self.payParams)
                finally:
                    dialog.deleteLater()


    @pyqtSignature('')
    def on_actSelectExposed_triggered(self):
        db = QtGui.qApp.db
        table = db.table('Account_Item')
        idList = self.modelAccountItems.idList()
        cond = []
        cond.append(table['id'].inlist(idList))
        cond.append(db.joinOr([table['date'].isNull(), table['number'].eq('')]))
        exposedIdList = db.getIdList(table, where=cond)
        selectionModel = self.tblAccountItems.selectionModel()
        if not (QtGui.qApp.keyboardModifiers() & Qt.ControlModifier):
            selectionModel.clear()
        rows = []
        for id in exposedIdList:
            row = idList.index(id)
            rows.append(row)
        rows.sort()
        lastIndex = None
        for row in rows:
            index = self.modelAccountItems.index(row, 0)
#            selectionModel.select(index, QtGui.QItemSelectionModel.Select|QtGui.QItemSelectionModel.Columns)
            selectionModel.select(index, QtGui.QItemSelectionModel.Select|QtGui.QItemSelectionModel.Rows)
            lastIndex = index
        if lastIndex:
            selectionModel.setCurrentIndex(lastIndex, QtGui.QItemSelectionModel.NoUpdate)


    @pyqtSignature('')
    def on_actSelectAll_triggered(self):
        self.tblAccountItems.selectAll()


    @pyqtSignature('')
    def on_actReportByRegistry_triggered(self):
        ok, orgInsurerId = self.selectInsurer(False)
        if ok:
            if orgInsurerId:
                self.execAccountItemsReportInsurer(CAccountRegistry, orgInsurerId)
            else:
                self.execAccountItemsReport(CAccountRegistry)


    @pyqtSignature('')
    def on_actReportByClients_triggered(self):
        self.execAccountItemsReport(CClientsListByRegistry)


    @pyqtSignature('')
    def on_actReportByDoctors_triggered(self):
        self.execAccountItemsReport(CFinanceSummaryByDoctors)


    @pyqtSignature('')
    def on_actReportByDoctorsEx_triggered(self):
        CFinanceSummaryByDoctorsEx(self).exec_(self.modelAccounts.idList())


    @pyqtSignature('')
    def on_actReportServiceByDoctors_triggered(self):
        CFinanceServiceByDoctors(self, self.modelAccounts.idList()).exec_()


    @pyqtSignature('')
    def on_actReportByServices_triggered(self):
        self.execAccountItemsReport(CFinanceSummaryByServices)


    @pyqtSignature('')
    def on_actDetailedReportByServices_triggered(self):
        CDetailedFinanceSummaryByServices(self).exec_(self.modelAccounts.idList())


    @pyqtSignature('')
    def on_actDetailedReportByServicesExpenses_triggered(self):
        self.execAccountItemsReport(CDetailedFinanceSumByServicesExpenses)
        #CDetailedFinanceSumByServicesExpenses(self).exec_(self.modelAccounts.idList())


    @pyqtSignature('')
    def on_actReportByServicesEx_triggered(self):
        CFinanceSummaryByServicesEx(self).exec_(self.modelAccounts.idList())


    @pyqtSignature('int')
    def on_btnPrint_printByTemplate(self, templateId):
    #def on_actPrintAccountByTemplate_printByTemplate(self, templateId):
        context = CInfoContext()
        accountInfo = context.getInstance(CAccountInfo, self.currentAccountId)
        accountInfo.selectedItemIdList = self.modelAccountItems.idList()
        accountInfoList = context.getInstance(CAccountInfoList, tuple(self.tblAccounts.selectedItemIdList()))
        contractIdList = self.getContractIdList(self.treeContracts.currentIndex())
        contractList = context.getInstance(CContractInfoList, tuple(contractIdList))
        workIndex = self.tabWorkType.currentIndex()
        begDate = CDateInfo(self.edtAnalysisBegDate.date() if workIndex == 1 else None)
        endDate = CDateInfo(self.edtAnalysisEndDate.date() if workIndex == 1 else None)
        data = { 'account' : accountInfo,
                        'accountList' : accountInfoList,
                        'filterBegDate' : begDate,
                        'filterEndDate' : endDate,
                        'filterContractList' : contractList,
                        'clientId' : self.getCurrentClientId()
               }
        applyTemplate(self, templateId, data)

    
    @pyqtSignature('')
    def on_actDeleteAccountItemsPersonalAccount_triggered(self):
        db = QtGui.qApp.db
        table = db.table('Account_Item')
        model = self.tblAccountItems.model()
        selectedItemRowList = self.tblAccountItems.selectedRowList()
        personalAccounts = []
        for row in selectedItemRowList:
            record = model.getRecordByRow(row)
            personalAccount = forceInt(record.value('event_id'))
            if personalAccount not in personalAccounts:
                personalAccounts.append(personalAccount)
        selectedItemIdList = []
        for row in xrange(model.rowCount()):
            record = model.getRecordByRow(row)
            accId = forceInt(record.value('id'))
            personalAccount = forceInt(record.value('event_id'))
            if personalAccount in personalAccounts:
                selectedItemIdList.append(accId)
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
                        db.deleteRecordSimple(table, table['id'].inlist(selectedItemIdList))
                        updateAccount(self.currentAccountId)
                        db.commit()
                    except:
                        db.rollback()
                        QtGui.qApp.logCurrentException()
                        raise
                    self.updateAccountInfo()
                    self.updateFilterAccountsEtc(self.currentAccountId, order=self.accountOrder)
                finally:
                    QtGui.qApp.restoreOverrideCursor()


    @pyqtSignature('')
    def on_actChangeEventExpose_triggered(self):
        db = QtGui.qApp.db
        table = db.table('Event')
        selectedRowList = self.tblAccountItems.selectedRowList()
        eventsIdToChange = [forceInt(self.tblAccountItems.model().getRecordByRow(row).value('event_id')) for row in selectedRowList]
        eventsIdToChange = set(eventsIdToChange) # оставляем только уникальные event_id
        n = len(eventsIdToChange)
        message = u'Вы действительно хотите снять отметку "Выставлять в счет" для %s?' % formatNum1(n, (u'события', u'событий'))
        message += u'\nВнимание! Случаи обслуживания без данной отметки не будут выставляться в счета. Вернуть отметку можно только отдельно из каждого случая вручную!'
        if QtGui.QMessageBox.question(self,
                                      u'Внимание!',
                                      message,
                                      QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                      QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes:
            QtGui.qApp.setWaitCursor()
            try:
                for eventId in eventsIdToChange:
                    try:
                        db.transaction()
                        cond = [table['id'].eq(eventId)]
                        record = db.getRecordEx(table, 'id, expose', cond)
                        record.setValue('expose', toVariant(0))
                        db.updateRecord(table, record)
                        db.commit()
                    except:
                        db.rollback()
                        QtGui.qApp.logCurrentException()
                        raise
            finally:
                QtGui.qApp.restoreOverrideCursor()
    

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
                        db.deleteRecordSimple(table, table['id'].inlist(selectedItemIdList))
                        updateAccount(self.currentAccountId)
                        db.commit()
                    except:
                        db.rollback()
                        QtGui.qApp.logCurrentException()
                        raise
                    self.updateAccountInfo()
                    self.updateFilterAccountsEtc(self.currentAccountId, order=self.accountOrder)
                finally:
                    QtGui.qApp.restoreOverrideCursor()


    @pyqtSignature('')
    def on_actShowAccountItemInfo_triggered(self):
        db = QtGui.qApp.db
        currentAccountItemId = self.tblAccountItems.currentItemId()
        if currentAccountItemId:
            accountItem = db.getRecord('Account_Item', '*', currentAccountItemId)
            account     = db.getRecord('Account', '*', accountItem.value('master_id'))

            createDatetime = forceString(account.value('createDatetime'))
            createPersonId = forceRef(account.value('createPerson_id'))
            modifyDatetime = forceString(account.value('modifyDatetime'))
            modifyPersonId = forceRef(account.value('modifyPerson_id'))
            eventId        = forceRef(accountItem.value('event_id'))
            externalId     = forceString(db.translate('Event', 'id', eventId, 'externalId'))
            clientId       = forceRef(db.translate('Event', 'id', eventId, 'client_id'))
            tariffId       = forceRef(accountItem.value('tariff_id'))
            tariffType     = forceInt(db.translate('Contract_Tariff', 'id', tariffId, 'tariffType'))
            tariffTypeName = CTariff.tariffTypeNames[tariffType] if 0<=tariffType<len(CTariff.tariffTypeNames) else '{%d}' % tariffType
            usedCoefficients = forceString(accountItem.value('usedCoefficients'))

            createPerson = forceString(db.translate('vrbPersonWithSpeciality', 'id', createPersonId, 'name'))
            modifyPerson = forceString(db.translate('vrbPersonWithSpeciality', 'id', modifyPersonId, 'name'))

            doc = QtGui.QTextDocument()
            cursor = QtGui.QTextCursor(doc)

            cursor.setCharFormat(CReportBase.ReportTitle)
            cursor.insertText(u'Свойства записи')
            cursor.insertBlock()
            cursor.setCharFormat(CReportBase.ReportBody)
            cursor.insertText(u'Позиция счёта (%d)\n' % currentAccountItemId)
            cursor.insertText(u'Тарифицируется: %s\n' % tariffTypeName)
            cursor.insertText(u'Создатель счёта: %s\n' % createPerson)
            cursor.insertText(u'Дата создания счёта: %s\n' % createDatetime)
            cursor.insertText(u'Редактор счёта: %s\n' % modifyPerson)
            cursor.insertText(u'Дата редактирования счёта: %s\n\n' % modifyDatetime)

            cursor.insertText(u'Код карточки: %d\n' % eventId)
            cursor.insertText(u'Номер документа: %s\n' % externalId)
            cursor.insertText(u'Код пациента: %d\n' % clientId)
            cursor.insertText(u'Коэффициенты: %s\n' % usedCoefficients)

            cursor.insertBlock()
            reportView = CReportViewDialog(self)
            reportView.setWindowTitle(u'Свойства записи')
            reportView.setText(doc)
            reportView.exec_()


    @pyqtSignature('')
    def on_btnForm_clicked(self):
        QtGui.qApp._timeoutLogout.stop()
        contractIdList = self.getContractIdList(self.treeContracts.currentIndex())
        if not contractIdList:
            QtGui.QMessageBox().warning(self, u'Внимание!',
                                        u'Для формирования счёта необходимо выбрать договор',
                                        QtGui.QMessageBox.Close)
            QtGui.qApp._timeoutLogout.setup(QtGui.qApp.getConnectionTimeout() * 60000, timeoutFunc=QtGui.qApp.mainWindow.logoutAndLogin)
            return
        date = self.clnCalcCalendar.selectedDate()
        message = u'Подтвердите, что Вы действительно хотите сформировать счета\nпо %s %s' % \
                  ((u'договору № ' if len(contractIdList) == 1 else u'договорам №№ '),
                   formatList([self.modelContracts.contracts[contractId] for contractId in contractIdList]),
                   )
        orgStructureId = self.cmbCalcOrgStructure.value()
        dialog = CExposeConfirmationDialog(self, foldText(message, [100]), orgStructureId, date)
        try:
            if dialog.exec_():
                begDate, endDate, filterPaymentByOrgStructure, reexpose, reexposeInSeparateAccount, checkMes, onlyDispCOVID, onlyResearchOnCOVID, onlyTFOMS, exposeByOrgStruct = dialog.options()
                if not filterPaymentByOrgStructure:
                    orgStructureId = None
                self.form(contractIdList, begDate, endDate, orgStructureId, reexpose, reexposeInSeparateAccount, checkMes, onlyDispCOVID, onlyResearchOnCOVID, onlyTFOMS, exposeByOrgStruct=exposeByOrgStruct)
        finally:
            dialog.deleteLater()
            QtGui.qApp._timeoutLogout.setup(QtGui.qApp.getConnectionTimeout() * 60000, timeoutFunc=QtGui.qApp.mainWindow.logoutAndLogin)


    @pyqtSignature('')
    def on_mnuBtnPrint_aboutToShow(self):
        self.on_mnuAccounts_aboutToShow()
        self.on_mnuAccountItems_aboutToShow()


    @pyqtSignature('')
    def on_btnExport_clicked(self):
        accountItemIdWithException = None
        exportInfo = getAccountExportFormat(self.currentAccountId).split()
        if exportInfo:
            exportFormat = exportInfo[0]
            if exportFormat in ('RD1', 'RD2', 'RD3', 'RD4', 'RD-DS', 'RD5', 'RD6', 'RD7'):
                accountItemIdList=self.modelAccountItems.idList()
                accountItemIdWithException = exportEISOMS(self, self.currentAccountId, accountItemIdList)
            elif exportFormat == 'INFISOMS':
                accountItemIdList=self.modelAccountItems.idList()
                exportINFISOMS(self, self.currentAccountId, accountItemIdList)
            elif exportFormat == 'LOFOMS':
                accountItemIdList=self.modelAccountItems.idList()
                exportLOFOMS(self, self.currentAccountId, accountItemIdList)
            elif exportFormat == 'R01NATIVE':
                accountItemIdList=self.modelAccountItems.idList()
                exportR01Native(self, self.currentAccountId, accountItemIdList, self.tblAccounts.selectedItemIdList())
            elif exportFormat == 'R08DD':
                accountItemIdList=self.modelAccountItems.idList()
                exportR08NativeHealthExamination(self, self.currentAccountId,
                    accountItemIdList,self.tblAccounts.selectedItemIdList())
            elif exportFormat == 'R08DDV59':
                accountItemIdList=self.modelAccountItems.idList()
                exportR08NativeHealthExaminationV59(self, self.currentAccountId,
                    accountItemIdList,self.tblAccounts.selectedItemIdList())
            elif exportFormat == 'R08D3V173':
                accountItemIdList=self.modelAccountItems.idList()
                exportR08NativeHealthExaminationV173(self, self.currentAccountId,
                    accountItemIdList, self.tblAccounts.selectedItemIdList())
            elif exportFormat == 'R08DDV200':
                accountItemIdList=self.modelAccountItems.idList()
                exportR08NativeHealthExaminationV200(self, self.currentAccountId,
                    accountItemIdList, self.tblAccounts.selectedItemIdList())
            elif exportFormat == 'R08EMERG':
                accountItemIdList=self.modelAccountItems.idList()
                exportR08Emergency(self, self.currentAccountId,
                    accountItemIdList, self.tblAccounts.selectedItemIdList())
            elif exportFormat == 'R08EMERGV59':
                accountItemIdList=self.modelAccountItems.idList()
                exportR08EmergencyV59(self, self.currentAccountId,
                    accountItemIdList, self.tblAccounts.selectedItemIdList())
            elif exportFormat == 'R08EMERGV200':
                accountItemIdList=self.modelAccountItems.idList()
                exportR08EmergencyV200(self, self.currentAccountId,
                    accountItemIdList, self.tblAccounts.selectedItemIdList())
            elif exportFormat == 'R08HOSP':
                accountItemIdList=self.modelAccountItems.idList()
                exportR08Hospital(self, self.currentAccountId,
                    accountItemIdList, self.tblAccounts.selectedItemIdList())
            elif exportFormat == 'R08HOSPV59':
                accountItemIdList=self.modelAccountItems.idList()
                exportR08HospitalV59(self, self.currentAccountId,
                    accountItemIdList, self.tblAccounts.selectedItemIdList())
            elif exportFormat == 'R08D1V173':
                accountItemIdList=self.modelAccountItems.idList()
                exportR08HospitalV173(self, self.currentAccountId,
                    accountItemIdList, self.tblAccounts.selectedItemIdList())
            elif exportFormat == 'R08HOSPV200':
                accountItemIdList=self.modelAccountItems.idList()
                exportR08HospitalV200(self, self.currentAccountId,
                    accountItemIdList, self.tblAccounts.selectedItemIdList())
            elif exportFormat == 'R08NATIVE':
                accountItemIdList=self.modelAccountItems.idList()
                exportR08Native(self, self.currentAccountId,
                    accountItemIdList, self.tblAccounts.selectedItemIdList())
            elif exportFormat == 'R23NATIVE':
                self.edtFioFilter.clear()
                self.updateAccountInfo()
                accountItemIdList=self.modelAccountItems.idList()
                exportR23Native(self, self.currentAccountId, accountItemIdList, self.tblAccounts.selectedItemIdList())
            elif exportFormat == 'R80_v200':
                accountItemIdList=self.modelAccountItems.idList()
                exportR80_v200(self, self.currentAccountId, accountItemIdList)
            elif exportFormat == 'R29DDv3.1.2':
                accountItemIdList=self.modelAccountItems.idList()
                exportR29DDv312(self, self.currentAccountId, accountItemIdList)
            elif exportFormat == 'R29v3.1.2Stomatology':
                accountItemIdList=self.modelAccountItems.idList()
                exportR29v312Stomotology(self, self.currentAccountId, accountItemIdList)
            elif exportFormat == 'R29VMPv3.1.2':
                accountItemIdList=self.modelAccountItems.idList()
                exportR29VMPv312(self, self.currentAccountId, accountItemIdList)
            elif exportFormat == 'R29v3.1.2':
                accountItemIdList=self.modelAccountItems.idList()
                exportR29v312(self, self.currentAccountId, accountItemIdList)
            elif exportFormat == 'R45NATIVE':
                accountItemIdList=self.modelAccountItems.idList()
                exportR45Native(self, self.currentAccountId, accountItemIdList,
                                self.tblAccounts.selectedItemIdList())
            elif exportFormat == 'R47D1':
                accountItemIdList=self.modelAccountItems.idList()
                exportR47D1(self, self.currentAccountId, accountItemIdList)
            elif exportFormat == 'R47D1V59':
                accountItemIdList=self.modelAccountItems.idList()
                exportR47D1V59(self, self.currentAccountId, accountItemIdList)
            elif exportFormat == 'R47D3':
                accountItemIdList=self.modelAccountItems.idList()
                exportR47D3(self, self.currentAccountId, accountItemIdList)
            elif exportFormat == 'R51FMO':
                accountItemIdList=self.modelAccountItems.idList()
                exportR51FMO(self, self.currentAccountId, accountItemIdList)
            elif exportFormat == 'R51OMS':
                accountItemIdList=self.modelAccountItems.idList()
                exportR51OMS(self, self.currentAccountId, accountItemIdList)
            elif exportFormat == 'R51DD2013':
                accountItemIdList=self.modelAccountItems.idList()
                exportR51DD2013(self, self.currentAccountId, accountItemIdList)
            elif exportFormat == 'R51SMP':
                accountItemIdList=self.modelAccountItems.idList()
                exportR51Emergency(self, self.currentAccountId, accountItemIdList)
            elif exportFormat == 'R51SMPXML':
                accountItemIdList=self.modelAccountItems.idList()
                exportR51EmergencyXml(self, self.currentAccountId, accountItemIdList)
            elif exportFormat == 'R51Hospital':
                accountItemIdList=self.modelAccountItems.idList()
                exportR51Hospital(self, self.currentAccountId, accountItemIdList)
            elif exportFormat == 'R51Stomatology':
                accountItemIdList=self.modelAccountItems.idList()
                exportR51Stomatology(self, self.currentAccountId, accountItemIdList)
            elif exportFormat == 'R51NATIVE_Ambulance':
                accountIdList=self.modelAccounts.idList()
                accountItemIdList=self.modelAccountItems.idList()
                exportR51Ambulance(self, self.currentAccountId, accountItemIdList, accountIdList)
            elif exportFormat == 'R51NATIVE_HealthExamination':
                accountIdList=self.modelAccounts.idList()
                accountItemIdList=self.modelAccountItems.idList()
                exportR51HealthExamination(self, self.currentAccountId, accountItemIdList, accountIdList)
            elif exportFormat == 'R53NATIVE':
                accountItemIdList=self.modelAccountItems.idList()
                exportR53Native(self, self.currentAccountId, accountItemIdList)
            elif exportFormat == 'R53-2012':
                accountItemIdList=self.modelAccountItems.idList()
                exportR53_2012(self, self.currentAccountId, accountItemIdList)
            elif exportFormat == 'R61NATIVE':
                accountItemIdList=self.modelAccountItems.idList()
                exportR61Native(self, self.currentAccountId, accountItemIdList)
            elif exportFormat == 'R61TFOMSNATIVE':
                accountItemIdList=self.modelAccountItems.idList()
                exportR61TFOMSNative(self, self.currentAccountId, accountItemIdList, self.tblAccounts.selectedItemIdList())
            elif exportFormat == 'R67NATIVE':
                accountItemIdList=self.modelAccountItems.idList()
                exportR67Native(self, self.currentAccountId, accountItemIdList)
            elif exportFormat == 'R67DP':
                accountItemIdList=self.modelAccountItems.idList()
                exportR67DP(self, self.currentAccountId, accountItemIdList)
            elif exportFormat == 'R69DD':
                accountItemIdList=self.modelAccountItems.idList()
                exportR69DD(self, self.currentAccountId, accountItemIdList)
            elif exportFormat == 'R69OMS':
                accountItemIdList=self.modelAccountItems.idList()
                exportR69OMS(self, self.currentAccountId, accountItemIdList)
            elif exportFormat == 'R74NATIVE':
                accountItemIdList=self.modelAccountItems.idList()
                exportR74NATIVE(self, self.currentAccountId, accountItemIdList)
            elif exportFormat == 'R77NATIVE':
                accountItemIdList=self.modelAccountItems.idList()
                exportR77Native(self, self.currentAccountId, accountItemIdList)
            elif exportFormat == 'R80Hospital':
                accountItemIdList=self.modelAccountItems.idList()
                exportR80Hospital(self, self.currentAccountId, accountItemIdList)
            elif exportFormat == 'R80NativeHealthExaminationV173':
                accountItemIdList=self.modelAccountItems.idList()
                exportR80NativeHealthExaminationV173(
                    self, self.currentAccountId, accountItemIdList)
            elif exportFormat == 'Register':
                accountIdList=self.tblAccounts.selectedItemIdList()
                exportRegister(self, self.currentAccountId, accountIdList)
            self.modelAccounts.invalidateRecordsCache()

        if accountItemIdWithException:
            self.tblAccountItems.setCurrentItemId(accountItemIdWithException)
#            self.tblAccountItems.setSelectedItemIdList(accountItemIdsWithException)


    @pyqtSignature('')
    def on_btnImport_clicked(self):

        def updateData():
            CRBModelDataCache.reset('rbPayRefuseType')
            self.modelAccountItems.invalidateRecordsCache()
            self.cmbAnalysisPayRefuseType.reloadData()
            self.cmbHistoryPayRefuseType.reloadData()
            self.updateFilterAccountsEtc(order=self.accountOrder)

        exportInfo = getAccountExportFormat(self.currentAccountId).split()
        if exportInfo:
            exportFormat = exportInfo[0]
            if exportFormat == 'R23NATIVE':
                ImportPayRefuseR23Native(self, self.currentAccountId, self.modelAccountItems.idList())
                updateData()
            elif exportFormat == 'R01NATIVE':
                ImportPayRefuseR01Native(self)
                updateData()
            elif exportFormat == 'R61TFOMSNATIVE':
                importFLKTFOMSR61Native(self)
                updateData()


    @pyqtSignature('')
    def on_btnCheck_clicked(self):
        currentAccountId = self.tblAccounts.currentItemId()
        selectedIds = self.tblAccounts.selectedItemIdList()
        accountRecords = [self.modelAccounts.recordCache().get(accountId) for accountId in selectedIds]
        dialog = CAccountCheckDialog(self, accountRecords)
        try:
            dialog.exec_()
            self.updateAccountInfo()
            self.updateFilterAccountsEtc(currentAccountId, order=self.accountOrder)
        finally:
            dialog.deleteLater()


    @pyqtSignature('')
    def on_actPrintDistributionOfCostAndDuration_triggered(self):
        CDistributionOfCostAndDurationReport(self, self.tblAccounts.selectedItemIdList()).exec_()


    @pyqtSignature('')
    def on_actPrintDistributionOfCostAndDurationKSG_triggered(self):
        CDistributionOfCostAndDurationKSGReport(self, self.tblAccounts.selectedItemIdList()).exec_()


    @pyqtSignature('')
    def on_actPrintKMU_triggered(self):
        CKMUReport(self, self.tblAccounts.selectedItemIdList()).exec_()


    @pyqtSignature('')
    def on_actPrintKMUBySpeciality_triggered(self):
        CKMUBySpecialityReport(self, self.tblAccounts.selectedItemIdList()).exec_()


    @pyqtSignature('')
    def on_actPrintKMUByVisitType_triggered(self):
        CKMUByVisitTypeReport(self, self.tblAccounts.selectedItemIdList()).exec_()


    @pyqtSignature('')
    def on_actPrintSummary_triggered(self):
        CSummaryReport(self, self.tblAccounts.selectedItemIdList()).exec_()


    @pyqtSignature('')
    def on_actPrintMedicalCareProvided_triggered(self):
        CMedicalCareProvidedReport(self, self.tblAccounts.selectedItemIdList()).exec_()


    @pyqtSignature('')
    def on_actPrintStructureByService_triggered(self):
        CStructureByServiceReport(self, self.tblAccounts.selectedItemIdList()).exec_()


    @pyqtSignature('')
    def on_actPrintStructureByEvent_triggered(self):
        CStructureByEventReport(self, self.tblAccounts.selectedItemIdList()).exec_()

    @pyqtSignature('')
    def on_actAccountE1_triggered(self):
        from Reports.EconomicAnalisysE1 import CEconomicAnalisysE1Ex
        CEconomicAnalisysE1Ex(self).exec_(accountIdList=self.tblAccounts.selectedItemIdList())

    @pyqtSignature('')
    def on_actAccountE2_triggered(self):
        from Reports.EconomicAnalisysE2 import CEconomicAnalisysE2Ex
        CEconomicAnalisysE2Ex(self).exec_(accountIdList=self.tblAccounts.selectedItemIdList())

    @pyqtSignature('')
    def on_actAccountE3_triggered(self):
        from Reports.EconomicAnalisysE3 import CEconomicAnalisysE3Ex
        CEconomicAnalisysE3Ex(self).exec_(accountIdList=self.tblAccounts.selectedItemIdList())

    @pyqtSignature('')
    def on_actAccountE4_triggered(self):
        from Reports.EconomicAnalisysE4 import CEconomicAnalisysE4Ex
        CEconomicAnalisysE4Ex(self).exec_(accountIdList=self.tblAccounts.selectedItemIdList())

    @pyqtSignature('')
    def on_actAccountE5_triggered(self):
        from Reports.EconomicAnalisysE5 import CEconomicAnalisysE5Ex
        CEconomicAnalisysE5Ex(self).exec_(accountIdList=self.tblAccounts.selectedItemIdList())

    @pyqtSignature('')
    def on_actAccountE6_triggered(self):
        from Reports.EconomicAnalisysE6 import CEconomicAnalisysE6Ex
        CEconomicAnalisysE6Ex(self).exec_(accountIdList=self.tblAccounts.selectedItemIdList())

    @pyqtSignature('')
    def on_actAccountE7_triggered(self):
        from Reports.EconomicAnalisysE7 import CEconomicAnalisysE7Ex
        CEconomicAnalisysE7Ex(self).exec_(accountIdList=self.tblAccounts.selectedItemIdList())

    @pyqtSignature('')
    def on_actAccountE8_triggered(self):
        from Reports.EconomicAnalisysE8 import CEconomicAnalisysE8Ex
        CEconomicAnalisysE8Ex(self).exec_(accountIdList=self.tblAccounts.selectedItemIdList())

    @pyqtSignature('')
    def on_actAccountE9_triggered(self):
        from Reports.EconomicAnalisysE9 import CEconomicAnalisysE9Ex
        CEconomicAnalisysE9Ex(self).exec_(accountIdList=self.tblAccounts.selectedItemIdList())

    @pyqtSignature('')
    def on_actAccountE10_triggered(self):
        from Reports.EconomicAnalisysE10 import CEconomicAnalisysE10Ex
        CEconomicAnalisysE10Ex(self).exec_(accountIdList=self.tblAccounts.selectedItemIdList())

    @pyqtSignature('')
    def on_actAccountE11_triggered(self):
        from Reports.EconomicAnalisysE11 import CEconomicAnalisysE11Ex
        CEconomicAnalisysE11Ex(self).exec_(accountIdList=self.tblAccounts.selectedItemIdList())

    @pyqtSignature('')
    def on_actAccountE12_triggered(self):
        from Reports.EconomicAnalisysE12 import CEconomicAnalisysE12Ex
        CEconomicAnalisysE12Ex(self).exec_(accountIdList=self.tblAccounts.selectedItemIdList())

    @pyqtSignature('')
    def on_actAccountE13_triggered(self):
        from Reports.EconomicAnalisysE13 import CEconomicAnalisysE13Ex
        CEconomicAnalisysE13Ex(self).exec_(accountIdList=self.tblAccounts.selectedItemIdList())

    @pyqtSignature('')
    def on_actAccountE14_triggered(self):
        from Reports.EconomicAnalisysE14 import CEconomicAnalisysE14Ex
        CEconomicAnalisysE14Ex(self).exec_(accountIdList=self.tblAccounts.selectedItemIdList())

    @pyqtSignature('')
    def on_actAccountE15_triggered(self):
        from Reports.EconomicAnalisysE15 import CEconomicAnalisysE15Ex
        CEconomicAnalisysE15Ex(self).exec_(accountIdList=self.tblAccounts.selectedItemIdList())

    @pyqtSignature('')
    def on_actAccountE16_triggered(self):
        from Reports.EconomicAnalisysE16 import CEconomicAnalisysE16Ex
        CEconomicAnalisysE16Ex(self).exec_(accountIdList=self.tblAccounts.selectedItemIdList())

    @pyqtSignature('')
    def on_actAccountE17_triggered(self):
        from Reports.EconomicAnalisysE17 import CEconomicAnalisysE17Ex
        CEconomicAnalisysE17Ex(self).exec_(accountIdList=self.tblAccounts.selectedItemIdList())

    @pyqtSignature('')
    def on_actAccountE19_triggered(self):
        from Reports.EconomicAnalisysE19 import CEconomicAnalisysE19Ex
        CEconomicAnalisysE19Ex(self).exec_(accountIdList=self.tblAccounts.selectedItemIdList())

    @pyqtSignature('')
    def on_actAccountE23_triggered(self):
        from Reports.EconomicAnalisysE23 import CEconomicAnalisysE23Ex
        CEconomicAnalisysE23Ex(self).exec_(accountIdList=self.tblAccounts.selectedItemIdList())

    @pyqtSignature('')
    def on_actAccountE24_triggered(self):
        from Reports.EconomicAnalisysE24 import CEconomicAnalisysE24Ex
        CEconomicAnalisysE24Ex(self).exec_(accountIdList=self.tblAccounts.selectedItemIdList())

    @pyqtSignature('')
    def on_actAccountE26_triggered(self):
        from Reports.EconomicAnalisysE26 import CEconomicAnalisysE26Ex
        CEconomicAnalisysE26Ex(self).exec_(accountIdList=self.tblAccounts.selectedItemIdList())

class CInsurerFilterDialog(QtGui.QDialog, Ui_InsurerFilterDialog):
    def __init__(self, parent, strict):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.cmbInsurerFilterDialog.setAddNone(not strict, u'все')
        self.cmbInsurerFilterDialog.setCurrentIndex(0)


    def orgId(self):
        return self.cmbInsurerFilterDialog.value()


def getMesAmount(eventId, mesId):
    result = 0
    db = QtGui.qApp.db
    stmt = u'''
        SELECT
        mMV.groupCode  AS prvsGroup,
        mMV.averageQnt AS averageQnt,
        Visit.id       AS visit_id,
        IF(mMV.visitType_id=mVT.id, 0, 1) AS visitTypeErr
        FROM Visit
        LEFT JOIN Person ON Person.id  = Visit.person_id
        LEFT JOIN rbSpeciality ON rbSpeciality.id = Person.speciality_id
        LEFT JOIN rbVisitType  ON rbVisitType.id = Visit.visitType_id
        LEFT JOIN mes.mrbVisitType  AS mVT  ON rbVisitType.code = mVT.code
        LEFT JOIN mes.mrbSpeciality AS mS   ON mS.regionalCode = rbSpeciality.regionalCode
        LEFT JOIN mes.MES_visit     AS mMV  ON mMV.speciality_id = mS.id AND mMV.deleted = 0
        WHERE Visit.deleted = 0 AND Visit.event_id = %d AND mMV.master_id = %d AND mVT.code in ('Л','К')
        ORDER BY visitTypeErr, mMV.groupCode, Visit.date
    ''' % (eventId, mesId)

    query = db.query(stmt)
    groupAvailable = {}
    countedVisits = set()
    while query.next():
        record = query.record()
        visitId = forceRef(record.value('visit_id'))
        if visitId not in countedVisits:
            prvsGroup = forceInt(record.value('prvsGroup'))
            averageQnt = forceInt(record.value('averageQnt'))
            available = groupAvailable.get(prvsGroup, averageQnt)
            if available > 0:
                groupAvailable[prvsGroup] = available-1
                result+=1
                countedVisits.add(visitId)
    return result


def getAccountItemsTotals(idList):
    count      = len(idList)
    totalExposedSum = 0.0
    totalSum   = 0.0
    payedSum   = 0.0
    refusedSum = 0.0
    factRefused = 0.0
    factPayed = 0.0
    totalPayed = 0.0
    totalRefused = 0.0
    totalClientsCount = 0
    totalEventsCount  = 0
    totalActionsCount = 0
    totalVisitsCount  = 0
    if idList:
        db = QtGui.qApp.db
        table = db.table('Account_Item')
        stmt = u'''
        SELECT
            SUM(sum) AS sum,
            SUM(exposedSum) AS exposedSum,
            (date IS NOT NULL AND number != '') AS confirmed,
            IF((payedSum)=0,1,0) AS refused,
            SUM(payedSum) AS factPayed,
            IF(DATE(date),IF(SUM(sum - payedSum)>0,SUM(sum - payedSum),0),0) as factRefused,
            COUNT(DISTINCT visit_id) AS visitCount,
            COUNT(DISTINCT action_id) AS actionCount,
            COUNT(DISTINCT event_id) AS eventCount
        FROM Account_Item
        WHERE %s
        AND Account_Item.deleted = 0
        GROUP BY `confirmed`, `refused`''' % table['id'].inlist(idList)
        query = db.query(stmt)
        while query.next():
            record = query.record()
            sum       = forceDouble(record.value('sum'))
            exposedSum = forceDouble(record.value('exposedSum'))
            confirmed = forceBool(record.value('confirmed'))
            refused   = forceBool(record.value('refused'))
            factPayed = forceDouble(record.value('factPayed'))
            factRefused = forceDouble(record.value('factRefused'))
            totalActionsCount += forceInt(record.value('actionCount'))
            totalVisitsCount += forceInt(record.value('visitCount'))
            totalEventsCount += forceInt(record.value('eventCount'))
            totalSum += sum
            totalExposedSum += exposedSum
            totalPayed += factPayed
            if factRefused > 0:
                totalRefused += factRefused
            if confirmed:
                if refused:
                    refusedSum += sum
                else:
                    payedSum += sum

        event = db.table('Event')
        countTable = event.innerJoin(table, table['event_id'].eq(event['id']))
        totalClientsCount = db.getDistinctCount(countTable, 'client_id', table['id'].inlist(idList))

    return count, totalSum, totalExposedSum, payedSum, refusedSum, totalPayed, totalRefused, \
        totalClientsCount, totalEventsCount, totalActionsCount, totalVisitsCount
