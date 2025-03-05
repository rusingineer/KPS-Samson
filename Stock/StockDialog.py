# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2024 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

u"""Работа: складской учёт"""

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt, QDate, QDateTime, QTime, QVariant, pyqtSignature, QString
from PyQt4.QtGui import QColor

from library.crbcombobox              import CRBComboBox, CRBModelDataCache
from library.database                 import undotLikeMask
from library.DbComboBox               import CDbDataCache
from library.DialogBase               import CDialogBase
from library.InDocTable               import CRecordListModel, CInDocTableCol, CRBInDocTableCol, CFloatInDocTableCol, CDateInDocTableCol
from library.PrintInfo                import CInfoContext, CDateInfo
from library.PrintTemplates           import applyTemplate, CPrintAction, getPrintTemplates, getPrintButton
from library.TableModel               import CTableModel, CDateCol, CDateTimeCol, CRefBookCol, CTextCol, CCol, CSumCol, CBoolCol, CDoubleCol, CEnumCol
from library.Utils                    import forceDouble, forceInt, forceDate, forceDateTime, forceRef, forceString, forceStringEx, forceBool, formatRecordsCount, smartDict, toVariant
from library.Counter                  import CCounterController

from Orgs.Utils                       import getOrgStructureDescendants, getOrgStructureFullName
from Registry.Utils                   import getClientMiniInfo
from Reports.ReportBase               import CReportBase, createTable
from Reports.ReportView               import CReportViewDialog, CPageFormat
from Reports.Utils                    import dateRangeAsStr
from Reports.ReportStockM11           import CReportStockM11
from Stock.ClientInvoiceEditDialog    import CClientRefundInvoiceEditDialog
from Stock.FinTransferEditDialog      import CFinTransferEditDialog
from Stock.InventoryEditDialog        import CInventoryEditDialog
from Stock.IncomingInvoiceEditDialog  import CIncomingInvoiceEditDialog
from Stock.PurchaseInvoiceEditDialog  import CPurchaseInvoiceEditDialog
from Stock.InternalInvoiceEditDialog  import CInternalInvoiceEditDialog
from Stock.StockModel                 import CStockMotionType
from Stock.NomenclatureComboBox       import CNomenclatureInDocTableCol
from Stock.ProductionEditDialog       import CProductionEditDialog
from Stock.StockMotion                import CStockPurchaseType, editStockMotion, getDialogName, stockMotionType, openReadOnlyMotion
from Stock.StockRequisitionEditDialog import CStockRequisitionEditDialog
from Stock.PurchaseContractDialog     import CPurchaseContractEditDialog
from Stock.StockSupplierRefundEditDialog import CStockSupplierRefundEditDialog
from Stock.StockMotionInfo            import CStockMotionInfoList, CStockRemainingsInfoList, CStockRequisitionsInfoList
from Stock.StockChangeAgreementStatusDialog import CStockChangeAgreementStatusDialog
from Stock.Mdlp.connection            import CMdlpConnection
from Stock.Mdlp.Logger                import CLogger
from Stock.Mdlp.Stage                 import CMdlpStage
from Stock.Mdlp.ExchangeReport        import showMdlpExchangeReport
from Stock.Mdlp.Utils                 import processMotion
from Users.Rights                     import (urEditOwnMotions,
                                              urEditOtherMotions,
                                              urDeleteMotions,
                                              urStockPurchaseContract,
                                              urAccessStockAgreeRequirements,
                                              urAccessViewRequirementsForAllStock,
                                              urStockRequirementsToMe,
                                              urEditStockRequirementsToMe)
from Stock.Utils import (
    getStockMotionItemQuantityColumn,
    getRemainingHistory,
    showRemainingHistoryReport,
    tuneSatisfiedFilterCmb,
    CSatisifiedFilter,
    showRequisitionMotionsHistoryReport,
    getMotionRecordsByRequisition,
#    getInventoryLastDate
)

from Stock.Ui_StockDialog             import Ui_StockDialog


class CQntDoubleCol(CDoubleCol):
    def __init__(self, title, fields, defaultWidth, alignment='l'):
        CDoubleCol.__init__(self, title, fields, defaultWidth, alignment)

    def format(self, values):
        if values[0].isNull():
            return None
        s = QString()
        precision = QtGui.qApp.numberDecimalPlacesQnt()
        if precision is None:
            s.setNum(values[0].toDouble()[0])
        else:
            s.setNum(values[0].toDouble()[0], 'f', precision)
        return toVariant(s)

    def getValue(self, values):
        return forceDouble(values[0])


class CSorterData(object):
    def __init__(self):
        self._columnIndex = None
        self._ascending = False

    @property
    def columnIndex(self):
        return self._columnIndex

    @property
    def ascending(self):
        return self._ascending

    def apply(self, tableView, columnIndex):
        header = tableView.horizontalHeader()

        if self._columnIndex == columnIndex:
            self._ascending = not self._ascending
        else:
            self._columnIndex = columnIndex
            self._ascending = True
        header.setSortIndicatorShown(True)
        header.setSortIndicator(
            self._columnIndex, Qt.AscendingOrder if self._ascending else Qt.DescendingOrder
        )


class CTableViewSorter(object):
    def __init__(self):
        self._cache = {}

    def __call__(self, key, tableView, columnIndex):
        if key not in self._cache:
            self._cache[key] = CSorterData()

        self._cache[key].apply(tableView, columnIndex)

    def getData(self, key):
        return self._cache.get(key, None)


class CInMemoryStorageMixin(object):
    def setCopiedData(self, key, data):
        storage = self.__getStorage()
        storage[key] = data

    def getCopiedData(self, key, default=None):
        storage = self.__getStorage()
        return storage.get(key, default)

    def __getStorage(self):
        if not '_CInMemoryStorageMixin__storage' in self.__dict__:
            self.__dict__['_CInMemoryStorageMixin__storage'] = {}
        return self.__storage


class CStockDialog(CDialogBase, CInMemoryStorageMixin, Ui_StockDialog):
    realtimeStatusDict = {0: (u'Документ создан', ''),
                          1: (u'Документ редактируется Заказчиком', QColor(240, 248, 144)),
                          2: (u'Документ подготовлен Заказчиком', QColor(255, 228, 181)),
                          3: (u'Документ редактируется Поставщиком', QColor(240, 248, 144)),
                          4: (u'Документ обрабатывается Поставщиком', QColor(240, 248, 144)),
                          5: (u'Документ обработан Поставщиком', QColor(179, 228, 148))}

    def __init__(self, parent):
        CDialogBase.__init__(self, parent)
        self._tableViewSorter = CTableViewSorter()

        self.motionsFilter = smartDict()
        self.remainingsFilter = smartDict()
        self.MRsFilter = smartDict()
        self.RTMsFilter = smartDict()
        self.purchaseContractFilter = smartDict()

        self.addModels('Motions',   CMyMotionsModel(self))
        self.addModels('MotionsItems',   CMyMotionsItemsModel(self))
        self.addObject('mnuMotions',     QtGui.QMenu(self))
        self.addObject('mnuMotionsItems',       QtGui.QMenu(self))
        self.addObject('actAddIncomingInvoice', QtGui.QAction(u'Создать накладную от поставщика', self))
        self.addObject('actAddInternalInvoice', QtGui.QAction(u'Создать внутреннюю накладную', self))
        self.addObject('actAddInventory',       QtGui.QAction(u'Создать инвентаризацию', self))
        self.addObject('actAddFinTransfer',     QtGui.QAction(u'Создать фин.перенос', self))
        self.addObject('actAddProduction',      QtGui.QAction(u'Создать производство', self))
        self.addObject('actAddClientRefundInvoice',  QtGui.QAction(u'Создать возврат', self))
        self.addObject('actAddSupplierRefund',  QtGui.QAction(u'Создать возврат поставщику', self))
        self.addObject('actAddUtilization',     QtGui.QAction(u'Утилизация', self))
        self.addObject('actAddTransUtilization', QtGui.QAction(u'Передача на утилизацию', self))
        self.addObject('actAddInternalConsumption', QtGui.QAction(u'Внутреннее потребление', self))
        self.addObject('actAddResidualQuantityWriteDown', QtGui.QAction(u'Списание остаточных количеств', self))
        self.addObject('actEditMotion',        QtGui.QAction(u'Редактировать движение', self))
        self.addObject('actDeleteMotion',      QtGui.QAction(u'Удалить запись', self))
        self.addObject('actMdlpExchange',      QtGui.QAction(u'Выполнить обмен с МДЛП', self))
        self.addObject('actMdlpExchangeReport',QtGui.QAction(u'Отчёт об обмене с МДЛП', self))
        self.addObject('actPrintInvoice',      QtGui.QAction(u'Печать М11', self))
        self.addObject('actOpenMotion',        QtGui.QAction(u'Открыть накладную', self))

        self.mnuMotions.addAction(self.actAddIncomingInvoice)
        self.mnuMotions.addAction(self.actAddInternalInvoice)
        self.mnuMotions.addAction(self.actAddInventory)
        self.mnuMotions.addAction(self.actAddFinTransfer)
        self.mnuMotions.addAction(self.actAddProduction)
        self.mnuMotions.addAction(self.actAddClientRefundInvoice)
        self.mnuMotions.addAction(self.actAddSupplierRefund)
        self.mnuMotions.addAction(self.actAddUtilization)
        self.mnuMotions.addAction(self.actAddTransUtilization)
        self.mnuMotions.addAction(self.actAddInternalConsumption)
        self.mnuMotions.addAction(self.actAddResidualQuantityWriteDown)
        self.mnuMotions.addSeparator()
        self.mnuMotions.addAction(self.actEditMotion)
        self.mnuMotions.addAction(self.actDeleteMotion)
#        self.actDeleteMotion.setEnabled(QtGui.qApp.userHasAnyRight([urDeleteMotions]))
        self.mnuMotions.addSeparator()
        self.mnuMotions.addAction(self.actMdlpExchange)
        self.mnuMotions.addAction(self.actMdlpExchangeReport)

        self.mnuMotions.addAction(self.actPrintInvoice)

        self.mnuMotionsItems.addAction(self.actOpenMotion)

        self.addModels('Remainings', CRemainingsModel(self))

        self.addModels('MRs',       CMyRequisitionsModel(self))
        self.addObject('mnuMRs',    QtGui.QMenu(self))
        self.addObject('actAddRequisition', QtGui.QAction(u'Создать требование', self))
        self.addObject('actEditRequisition', QtGui.QAction(u'Редактировать требование', self))
        self.addObject('actRevokeRequisition', QtGui.QAction(u'Отменить требование', self))
        self.addObject('actShowOverhead', QtGui.QAction(u'Показать связанные накладные', self))
        self.mnuMRs.addAction(self.actAddRequisition)
        self.mnuMRs.addAction(self.actEditRequisition)
        self.mnuMRs.addAction(self.actRevokeRequisition)
        self.mnuMRs.addAction(self.actShowOverhead)
        self.mnuMRs.addAction(self.actPrintInvoice)
        self.addModels('MRContent', CRequisitionContentModel(self))

        self.addModels('RTMs',       CRequisitionsToMeModel(self))
        self.addObject('mnuRTMs', QtGui.QMenu(self))
#        self.addObject('actEditClient', QtGui.QAction(u'Открыть регистрационную карточку', self))
        self.addObject('actCreateMotionByRequisition', QtGui.QAction(u'Создать движение по требованию', self))
        self.addObject('actShowRTMOverhead', QtGui.QAction(u'Показать связанные накладные', self))
        self.addObject('actChangeAgreementStatus', QtGui.QAction(u'Изменить статус согласования', self))
#        self.addObject('actRejectRequisition', QtGui.QAction(u'Отказать в требование', self))
        self.addObject('actEditRTMsRequisition', QtGui.QAction(u'Редактировать требование', self))
        self.mnuRTMs.addAction(self.actCreateMotionByRequisition)
        self.mnuRTMs.addAction(self.actShowRTMOverhead)
        self.mnuRTMs.addAction(self.actChangeAgreementStatus)
        self.mnuRTMs.addAction(self.actEditRTMsRequisition)
#        self.mnuRTMs.addAction(self.actRejectRequisition)
        self.addModels('RTMContent', CRequisitionContentModel(self))

        self.addModels('PurchaseContract',          CPurchaseContractModel(self))
        self.addModels('PurchaseContractItems',     CPurchaseContractItemsModel(self))
        self.addObject('mnuPurchaseContract',       QtGui.QMenu(self))
        self.addObject('mnuPurchaseContractItems',  QtGui.QMenu(self))
        self.addObject('actAddPurchaseContract',    QtGui.QAction(u'Создать контракт на закупку', self))
        self.addObject('actEditPurchaseContract',   QtGui.QAction(u'Редактировать документ', self))
        self.addObject('actDeletePurchaseContract', QtGui.QAction(u'Удалить документ', self))
        self.addObject('actAddPurchaseInvoice',     QtGui.QAction(u'Создать заявку на поставку', self))
        self.mnuPurchaseContract.addAction(self.actAddPurchaseContract)
        self.mnuPurchaseContract.addAction(self.actEditPurchaseContract)
        self.mnuPurchaseContract.addAction(self.actDeletePurchaseContract)
        self.mnuPurchaseContract.addAction(self.actAddPurchaseInvoice)

        self.templateNames = {0:'StockMotions', 1:'StockRemainings', 2:'StockMyRequisitions', 3:'StockRequirementsToMe', 4:'StockPurchaseContract'}
        self.addObject('btnPrint', getPrintButton(self, ''))
        self.btnPrint.setShortcut('F6')
        self.setupUi(self)

        tuneSatisfiedFilterCmb(self.cmbMRsFilterSatisfied)
        tuneSatisfiedFilterCmb(self.cmbRTMsFilterSatisfied)

        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.buttonBox.addButton(self.btnPrint, QtGui.QDialogButtonBox.ActionRole)
        self.printMenu = {}
        self.preparePrintBtn(self.tabWidget.currentIndex())
        if QtGui.qApp.currentOrgStructureId():
            self.setWindowTitle(u'Склад ЛСиИМН: %s' % getOrgStructureFullName(QtGui.qApp.currentOrgStructureId()))

        self.bbxMotionsFilter.button(QtGui.QDialogButtonBox.Apply).setDefault(True)
        self.bbxRemainingsFilter.button(QtGui.QDialogButtonBox.Apply).setDefault(True)
        self.bbxMRsFilter.button(QtGui.QDialogButtonBox.Apply).setDefault(True)
        self.bbxRTMsFilter.button(QtGui.QDialogButtonBox.Apply).setDefault(True)
        self.bbxPurchaseContractFilter.button(QtGui.QDialogButtonBox.Apply).setDefault(True)

        self.edtMotionsFilterBegReasonDate.canBeEmpty(True)
        self.edtMotionsFilterEndReasonDate.canBeEmpty(True)

        if forceBool(QtGui.qApp.preferences.appPrefs.get('isShowOnlyCurrentAndDescendantsStock', QVariant())):
            stocksIdList = []
            orgId = QtGui.qApp.currentOrgId()
            orgStructureId = QtGui.qApp.currentOrgStructureId()
            if orgStructureId:
                db = QtGui.qApp.db
                tableOS = db.table('OrgStructure')
                cond = [tableOS['id'].eq(orgStructureId),
                        tableOS['deleted'].eq(0),
                        tableOS['mainStocks'].eq(1)]
                record = db.getRecordEx(tableOS, [tableOS['id']], cond)
                mainStocksId = forceRef(record.value('id')) if record else None
                if not mainStocksId:
                    orgStructureIdList = db.getDescendants('OrgStructure', 'parent_id', orgStructureId)
                    if orgStructureIdList:
                        cols = [tableOS['id']]
                        cond = [tableOS['deleted'].eq(0),
                                tableOS['id'].inlist(orgStructureIdList),
                                db.joinOr([tableOS['hasStocks'].eq(1), tableOS['mainStocks'].eq(1)])
                               ]
                        stocksIdList = db.getDistinctIdList(tableOS, cols, cond)
                        if stocksIdList:
                            self.cmbRemainingsFilterStorage.setFilter('''id IN (%s)'''%(u','.join(str(id) for id in stocksIdList if id)))
                        else:
                            self.cmbRemainingsFilterStorage.setFilter('''False''')
                elif orgId:
                    cols = [tableOS['id']]
                    cond = [tableOS['organisation_id'].eq(orgId),
                            tableOS['deleted'].eq(0),
                            db.joinOr([tableOS['hasStocks'].eq(1), tableOS['mainStocks'].eq(1)])
                            ]
                    stocksIdList = db.getDistinctIdList(tableOS, cols, cond)
                self.cmbRemainingsFilterStorage.setIsValidIdList(stocksIdList)

        self.cmbMotionsFilterNomenclature.setTable('rbNomenclature', order='name')
        self.cmbMotionsFilterNomenclature.setOnlyNomenclature(True)
        self.cmbMotionsFilterFinance.setTable('rbFinance', True)
        self.cmbMotionsFilterMedicalAidKind.setTable('rbMedicalAidKind', True)
        self.cmbMotionsFilterSupplierOrg.setFilter('isSupplier = 1')

        self.cmbRemainingsFilterNomenclature.setTable('rbNomenclature', order='name')
        self.cmbRemainingsFilterNomenclature.setOnlyNomenclature(True)
        self.cmbRemainingsFilterNomenclatureClass.setTable('rbNomenclatureClass', order='name')
        self.cmbRemainingsFilterNomenclatureKind.setTable('rbNomenclatureKind', order='name')
        self.cmbRemainingsFilterNomenclatureType.setTable('rbNomenclatureType', order='name')
        self.cmbRemainingsFilterFinance.setTable('rbFinance', True)
        self.cmbRemainingsMedicalAidKind.setTable('rbMedicalAidKind', True)
        self.cmbRemainingsFilterUnit.setTable('rbUnit', True)

        self.cmbMRsFilterNomenclature.setTable('rbNomenclature', order='name')
        self.cmbMRsFilterNomenclature.setOnlyNomenclature(True)
        self.cmbRTMsFilterNomenclature.setTable('rbNomenclature', order='name')
        self.cmbRTMsFilterNomenclature.setOnlyNomenclature(True)

        self.edtPurchaseContractFilterBegDate.canBeEmpty(True)
        self.edtPurchaseContractFilterEndDate.canBeEmpty(True)
        self.cmbPurchaseContractFilterSupplierOrg.setFilter('isSupplier = 1')

        self.tblMotions.setModel(self.modelMotions)
        self.tblMotions.setSelectionModel(self.selectionModelMotions)
        self.tblMotions.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.tblMotions.setPopupMenu(self.mnuMotions)

        self.tblMotionsItems.setModel(self.modelMotionsItems)
        self.tblMotionsItems.setSelectionModel(self.selectionModelMotionsItems)
        self.tblMotionsItems.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.tblMotionsItems.setPopupMenu(self.mnuMotionsItems)

        self.tblRemainings.setModel(self.modelRemainings)
        self.tblRemainings.setSelectionModel(self.selectionModelRemainings)

        self.tblMRs.setModel(self.modelMRs)
        self.tblMRs.setSelectionModel(self.selectionModelMRs)
        self.tblMRs.setPopupMenu(self.mnuMRs)
        self.tblMRContent.setModel(self.modelMRContent)
        self.tblMRContent.setSelectionModel(self.selectionModelMRContent)

        self.tblRTMs.setModel(self.modelRTMs)
        self.tblRTMs.setSelectionModel(self.selectionModelRTMs)
        self.tblRTMs.setPopupMenu(self.mnuRTMs)

        self.tblRTMContent.setModel(self.modelRTMContent)
        self.tblRTMContent.setSelectionModel(self.selectionModelRTMContent)

        self.tblPurchaseContract.setModel(self.modelPurchaseContract)
        self.tblPurchaseContract.setSelectionModel(self.selectionModelPurchaseContract)
        self.tblPurchaseContract.setPopupMenu(self.mnuPurchaseContract)

        self.tblPurchaseContractItems.setModel(self.modelPurchaseContractItems)
        self.tblPurchaseContractItems.setSelectionModel(self.selectionModelPurchaseContractItems)

        self.controlSplitter = None
        self._recordsIdDict = {}

        self.visitedMRs = False
        self.visitedRTMs = False
        self.visitedPurchaseContract = False

        # defaults
        self.edtRemainingsFilterBegShelfTime.setDate(QDate())
        self.edtRemainingsFilterEndShelfTime.setDate(QDate())

        self.chkRemainingsFilterGroupByBatch.setChecked(True)

        self.cmbRemainingsFilterStorage.setValue(QtGui.qApp.currentOrgStructureId())

        self.tblMotions.enableColsHide()
        self.tblMotions.enableColsMove()
        self.tblRemainings.enableColsHide()
        self.tblRemainings.enableColsMove()

        self.addObject('actRemainingsShowStockMotions', QtGui.QAction(u'Показать накладные', self))
        self.tblRemainings.addPopupAction(self.actRemainingsShowStockMotions)

        self.tabWidget.setTabEnabled(self.tabWidget.indexOf(self.tabPurchaseContract), QtGui.qApp.userHasRight(urStockPurchaseContract))
        self.tabWidget.setTabEnabled(self.tabWidget.indexOf(self.tabRequirementsToMe), QtGui.qApp.userHasRight(urStockRequirementsToMe))

        self.connect(self.actRemainingsShowStockMotions, QtCore.SIGNAL('triggered()'), self.on_actRemainingsShowStockMotions_triggered)

        self.connect(self.tblMotions.horizontalHeader(), QtCore.SIGNAL('sectionClicked(int)'), self.on_motionsSortByColumn)

        self.setMouseTracking(True)
        self.startTime = QTime.currentTime()

    @pyqtSignature('')
    def on_mnuRTMs_aboutToShow(self):
        isEnabled = False
        isChangeAgreementStatusEnabled = False
        isSupplierMainStocks = False
        currentIndex = self.tblRTMs.currentIndex()
        if currentIndex and currentIndex.isValid():
            row = currentIndex.row()
            if 0 <= row < len(self.modelRTMs._idList):
                isEnabled = True
                RTMsId = forceRef(self.modelRTMs._idList[row])
                if RTMsId:
                    db = QtGui.qApp.db
                    tableSR = db.table('StockRequisition')
                    record = db.getRecordEx(tableSR, '*', [tableSR['id'].eq(RTMsId), tableSR['deleted'].eq(0)])
                    if record:
                        isChangeAgreementStatusEnabled = True
                        accordingRequirementsStockType = forceInt(QtGui.qApp.preferences.appPrefs.get('accordingRequirementsStockType', QVariant()))
                        if forceBool(accordingRequirementsStockType):
                            if accordingRequirementsStockType == 1:
                                supplierId = forceRef(record.value('supplier_id'))
                                if supplierId:
                                    table = db.table('OrgStructure')
                                    recordOS = db.getRecordEx(table, table['id'], [table['id'].eq(supplierId), table['mainStocks'].eq(1), table['deleted'].eq(0)])
                                    isSupplierMainStocks = bool(recordOS and forceRef(recordOS.value('id')) == supplierId)
                                    if isSupplierMainStocks:
                                        agreementDate = forceDate(record.value('agreementDate'))
                                        agreementPersonId = forceRef(record.value('agreementPerson_id'))
                                        isEnabled = forceBool(agreementDate and agreementPersonId and forceInt(record.value('agreementStatus'))==1)
                                    isChangeAgreementStatusEnabled = isSupplierMainStocks
                                else:
                                    isEnabled = False
                                    isChangeAgreementStatusEnabled = False
                            elif accordingRequirementsStockType == 2:
                                agreementDate = forceDate(record.value('agreementDate'))
                                agreementPersonId = forceRef(record.value('agreementPerson_id'))
                                isEnabled = forceBool(agreementDate and agreementPersonId and forceInt(record.value('agreementStatus'))==1)
        self.actEditRTMsRequisition.setEnabled(currentIndex and currentIndex.isValid() and QtGui.qApp.userHasRight(urEditStockRequirementsToMe))
        self.actCreateMotionByRequisition.setEnabled(isEnabled and QtGui.qApp.userHasRight(urEditStockRequirementsToMe))
        self.actShowRTMOverhead.setEnabled(QtGui.qApp.userHasRight(urEditStockRequirementsToMe))
        self.actChangeAgreementStatus.setEnabled(isChangeAgreementStatusEnabled and QtGui.qApp.userHasRight(urAccessStockAgreeRequirements) and QtGui.qApp.userHasRight(urEditStockRequirementsToMe))


    def exec_(self):
        self.tabWidget.setCurrentIndex(0)
        self.resetMotionsFilter()
        self.applyMotionsFilter()
        CDialogBase.exec_(self)


    @pyqtSignature('')
    def on_mnuPurchaseContract_aboutToShow(self):
        enable = (len(self.tblPurchaseContract.model().idList()) > 0) and QtGui.qApp.userHasRight(urStockPurchaseContract)
        self.actAddPurchaseContract.setEnabled(QtGui.qApp.userHasRight(urStockPurchaseContract))
        self.actEditPurchaseContract.setEnabled(enable)
        self.actDeletePurchaseContract.setEnabled(enable)
        if enable:
            purchaseContractId = self.tblPurchaseContract.currentItemId()
            if purchaseContractId:
                db = QtGui.qApp.db
                tableSPC = db.table('StockPurchaseContract')
                record = db.getRecordEx(tableSPC, '*', [tableSPC['id'].eq(purchaseContractId), tableSPC['deleted'].eq(0)])
                if record and forceInt(record.value('type')) > 0:
                    enable = False
            else:
                enable = False
        self.actAddPurchaseInvoice.setEnabled(enable)

    def syncSplitters(self, nextSplitter):
        if self.controlSplitter and nextSplitter != self.controlSplitter:
            nextSplitter.setSizes(self.controlSplitter.sizes())
            self.controlSplitter = nextSplitter
        else:
            self.controlSplitter = nextSplitter


    def composeDateTime(self, date, time):
        if date:
            return QDateTime(date, time)
        else:
            return QDateTime()


    def getRequisitionItemIdList(self, requisitionId):
        if requisitionId:
            db = QtGui.qApp.db
            table = db.table('StockRequisition_Item')
            cond = table['master_id'].inlist(requisitionId)
            return db.getIdList(table, 'id', where=cond, order='idx, id')
        else:
            return []


    def preparePrintBtn(self,  index):
        btn = self.btnPrint
        enabled = True
        menu = self.getPrintBtnMenu(index)
        if not menu:
            menu = QtGui.QMenu()
            act = menu.addAction(u'Нет шаблонов печати')
            act.setEnabled(False)
            enabled = False
        btn.setMenu(menu)
        btn.setEnabled(enabled)
        self.printMenu[index] = menu


    def getPrintBtnMenu(self, index):
        self.reportFunc = {
                      -1:[u'Напечатать список', self.actPrintMotions]
                      }
        if index in self.printMenu:
            menu = self.printMenu[index]
        else:
            menu = QtGui.QMenu()
            subMenuDict={}
            templates = getPrintTemplates(self.templateNames[index])
            if templates:
                for i, template in enumerate(templates):
                    if template.group:
                        action = CPrintAction(template.name, template.id, self.btnPrint, self.btnPrint)
                        menu.addAction(action)
                    else:
                        subMenu = subMenuDict.get(template.group)
                        if not subMenu:
                            subMenu = QtGui.QMenu(template.group, self.parentWidget())
                            subMenuDict[template.group] = subMenu
                        action = CPrintAction(template.name, template.id, self.btnPrint, self.btnPrint)
                        subMenu.addAction(action)
                if subMenuDict:
                    for subMenuKey in sorted(subMenuDict.keys()):
                        menu.addMenu(subMenuDict[subMenuKey])
            else:
                act = menu.addAction(u'Нет шаблонов печати')
                act.setEnabled(False)
            menu.addSeparator()
            for key in sorted(self.reportFunc):
                menu.addAction( CPrintAction(self.reportFunc[key][0],  key,  self.btnPrint, self.btnPrint) )
        return menu

    @pyqtSignature('int')
    def on_btnPrint_printByTemplate(self, templateId):
        if templateId < 0:
            self.reportFunc[templateId][1]()
        else:
            context = forceString(QtGui.qApp.db.translate('rbPrintTemplate', 'id', templateId, 'context'))
            data = None
            if context == u'StockMotions':
                data = self.getContextData(self.tblMotions)
            elif context == u'StockRemainings':
                data = self.getContextData(self.tblRemainings)
            elif context == u'StockMyRequisitions':
                data = self.getContextData(self.tblMRContent)
            elif context == u'StockRequirementsToMe':
                data = self.getContextData(self.tblRTMContent)
            if data:
                QtGui.qApp.call(self, applyTemplate, (self, templateId, data))


    def getTableToWidget(self, widgetIndex):
        return [self.tblMotions, self.tblRemainings, self.tblMRContent, self.tblRTMContent, self.tblPurchaseContract][widgetIndex]


    def actPrintMotions(self):
        widget = self.getTableToWidget(self.tabWidget.currentIndex())
        if self.tabWidget.currentIndex() == 1:
            self.getRemainingsPrint()
        else:
            widget.setReportHeader(u'Список')
            widget.setReportDescription(self.getStockFilterAsText(self.tabWidget.currentIndex()))
            widget.printContent()


    def getContextData(self, table):
        context = CInfoContext()
        if self.tabWidget.currentIndex() == 0:
            idList = self.modelMotions.idList()
            selectedIdList = self.tblMotions.selectedItemIdList()
            data = { 'motionsList': CStockMotionInfoList(context, idList),
                          'selectedMotionsList' : CStockMotionInfoList(context, selectedIdList)}
        elif self.tabWidget.currentIndex() == 1:
            items = self.modelRemainings.items()
            data = { 'remainingsFilterDate' : CDateInfo(self.edtRemainingsFilterDate.date()),
                     'remainingsList'       : CStockRemainingsInfoList(context, items)}
        elif self.tabWidget.currentIndex() == 2:
            idList = self.modelMRs.idList()
            selectedIdList = self.tblMRs.selectedItemIdList()
            data = { 'requisitionsList': CStockRequisitionsInfoList(context, idList),
                         'selectedRequisitionsList': CStockRequisitionsInfoList(context, selectedIdList)}
        elif self.tabWidget.currentIndex() == 3:
            idList = self.modelRTMs.idList()
            selectedIdList = self.tblRTMs.selectedItemIdList()
            data = { 'requisitionsList': CStockRequisitionsInfoList(context, idList),
                        'selectedRequisitionsList': CStockRequisitionsInfoList(context, selectedIdList)}
        return data


    def dumpParams(self, cursor):
        db = QtGui.qApp.db
        description = []
        remainingsFilterDate = self.edtRemainingsFilterDate.date()
        if remainingsFilterDate:
            description.append(u'На дату ' + forceString(remainingsFilterDate))
        remainingsFilterStorage = self.cmbRemainingsFilterStorage.value()
        if remainingsFilterStorage:
            description.append(u'Склад %s'%forceString(db.translate('OrgStructure', 'id', remainingsFilterStorage, 'name')))
        remainingsFilterNomenclature = self.cmbRemainingsFilterNomenclature.value()
        if remainingsFilterNomenclature:
            description.append(u'Номенклатура %s'%forceString(db.translate('rbNomenclature', 'id', remainingsFilterNomenclature, 'name')))
        remainingsFilterNomenclatureClass = self.cmbRemainingsFilterNomenclatureClass.value()
        if remainingsFilterNomenclatureClass:
            description.append(u'Номенклатура Класс %s'%forceString(db.translate('rbNomenclatureClass', 'id', remainingsFilterNomenclatureClass, 'name')))
        remainingsFilterNomenclatureKind = self.cmbRemainingsFilterNomenclatureKind.value()
        if remainingsFilterNomenclatureKind:
            description.append(u'Номенклатура Вид %s'%forceString(db.translate('rbNomenclatureKind', 'id', remainingsFilterNomenclatureKind, 'name')))
        remainingsFilterNomenclatureType = self.cmbRemainingsFilterNomenclatureType.value()
        if remainingsFilterNomenclatureType:
            description.append(u'Номенклатура Тип %s'%forceString(db.translate('rbNomenclatureType', 'id', remainingsFilterNomenclatureType, 'name')))
        if self.chkRemainingsFilterGroupByBatch.isChecked():
            description.append(u'Разделять по партиям и годности')
        remainingsFilterBatch = self.edtRemainingsFilterBatch.text()
        if remainingsFilterBatch:
            description.append(u'Серия %s'%remainingsFilterBatch)
        begDate = self.edtRemainingsFilterBegShelfTime.date()
        endDate = self.edtRemainingsFilterEndShelfTime.date()
        if begDate or endDate:
            description.append(dateRangeAsStr(u'Годен', begDate, endDate))
        if self.chkRemainingsFilterFinishShelfTime.isChecked():
            finishShelfTimeDays = self.edtRemainingsFilterFinishShelfTimeDays.value()
            description.append(u'До истечения срока годности %d'%finishShelfTimeDays)
        remainingsFilterFinance = self.cmbRemainingsFilterFinance.value()
        if remainingsFilterFinance:
            description.append(u'Тип финансирования %s'%forceString(db.translate('rbFinance', 'id', id, 'name')))
        if self.chkRemainingsFilterConstrainedQnt.isChecked():
            description.append(u'Запас ниже точки заказа')
        if self.chkRemainingsFilterOrderQnt.isChecked():
            description.append(u'Запас ниже гантированного')
        if self.chkRemainingsFilterAvailable.isChecked():
            description.append(u'Имеющиеся в наличии')
        remainingsFilterUnit = self.cmbRemainingsFilterUnit.value()
        if remainingsFilterUnit:
            description.append(u'Ед. учета %s'%forceString(db.translate('rbUnit', 'id', id, 'name')))
        description.append(u'отчёт составлен: ' + forceString(QDateTime.currentDateTime()))
        columns = [ ('100%', [], CReportBase.AlignLeft) ]
        table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
        for i, row in enumerate(description):
            table.setText(i, 0, row)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()


    def getRemainingsPrint(self):
        model = self.tblRemainings.model()
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(u'Остатки\n')
        self.dumpParams(cursor)
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportBody)
        columnCount = model.columnCount()-1
        colWidths  = [ 90/columnCount for i in xrange(columnCount) ]
        colWidths.insert(0,10)
        totalWidth = sum(colWidths)
        tableColumns = []
        iColNumber = False
        for iCol, colWidth in enumerate(colWidths):
            widthInPercents = str(max(1, colWidth*90/totalWidth))+'%'
            if iColNumber == False:
                tableColumns.append((widthInPercents, [u'№'], CReportBase.AlignRight))
                iColNumber = True
            tableColumns.append((widthInPercents, [forceString(model._cols[iCol].title())], CReportBase.AlignLeft))
        table = createTable(cursor, tableColumns)
        for iModelRow in xrange(model.rowCount()):
            iTableRow = table.addRow()
            table.setText(iTableRow, 0, iModelRow+1)
            for iModelCol in xrange(model.columnCount()):
                index = model.createIndex(iModelRow, iModelCol)
                text = forceString(model.data(index))
                table.setText(iTableRow, iModelCol+1, text)
        html = doc.toHtml('utf-8')
        view = CReportViewDialog(self)
        view.pageFormat = CPageFormat(pageSize=CPageFormat.A4, orientation=CPageFormat.Landscape, leftMargin=1, topMargin=1, rightMargin=1,  bottomMargin=1)
        view.setText(html)
        view.exec_()


    def getStockFilterAsText(self, widget):
        db = QtGui.qApp.db
        if widget == 0:
            filter = self.motionsFilter
            tmpList = [('number', u'Номер', forceString),
                        ('begDate', u'Дата с', forceString),
                        ('endDate', u'Дата по', forceString),
                        ('reason',   u'Основание', forceString),
                        ('supplierId', u'Источник',
                            lambda id: forceString(db.translate('OrgStructure', 'id', id, 'name'))),
                        ('receiverId', u'Получатель',
                            lambda id: forceString(db.translate('OrgStructure', 'id', id, 'name'))),
                        ('clientId',   u'Код пациента', forceString),
                        ('note',   u'Примечание', forceString),
                        ('nomenclatureId', u'Номенклатура',
                            lambda id: forceString(db.translate('rbNomenclature', 'id', id, 'name'))),
                        ('batch', u'Серия', forceString),
                        ('begShelfTime',   u'Годен с', forceString),
                        ('endShelfTime',   u'Годен по', forceString),
                        ('financeId', u'Тип финансирования',
                            lambda id: forceString(db.translate('rbFinance', 'id', id, 'name'))),
                        ('medicalAidKindId', u'Вид медицинской помощи',
                            lambda id: forceString(db.translate('rbMedicalAidKind', 'id', id, 'name'))),
                        ('type', u'Тип документа', getDialogName),
                        ('groupMotions', u'Группировать накладные в рамках одного курса', getDialogName),
                        ]
        if widget == 1:
            filter = self.remainingsFilter
            tmpList = [('date', u'На дату', forceString),
                        ('storageId', u'Склад',
                            lambda id: forceString(db.translate('OrgStructure', 'id', id, 'name'))),
                        ('nomenclatureId', u'Номенклатура',
                            lambda id: forceString(db.translate('rbNomenclature', 'id', id, 'name'))),
                        ('nomenclatureClassId', u'Номенклатура Класс',
                            lambda id: forceString(db.translate('rbNomenclatureClass', 'id', id, 'name'))),
                        ('nomenclatureKindId', u'Номенклатура Вид',
                            lambda id: forceString(db.translate('rbNomenclatureKind', 'id', id, 'name'))),
                        ('nomenclatureTypeId', u'Номенклатура Тип',
                            lambda id: forceString(db.translate('rbNomenclatureType', 'id', id, 'name'))),
                        ('groupByBatch',  u'Разделять по партиям и годности', lambda dummy: u'+'),
                        ('batch', u'Серия', forceString),
                        ('begShelfTime',   u'Годен с', forceString),
                        ('endShelfTime',   u'Годен по', forceString),
                        ('financeId', u'Тип финансирования',
                            lambda id: forceString(db.translate('rbFinance', 'id', id, 'name'))),
                        ('medicalAidKindId', u'Вид медицинской помощи',
                            lambda id: forceString(db.translate('rbMedicalAidKind', 'id', id, 'name'))),
                        ('constrainedQnt',  u'Запас ниже точки заказа', lambda dummy: u'+'),
                        ('orderQnt',  u'Запас ниже гантированного', lambda dummy: u'+')
                        ]
        if widget == 2:
            filter = self.MRsFilter
            tmpList = [('onlyActive',   u'Только действующие', lambda dummy: u'+'),
                        ('begDate', u'Период с', forceString),
                        ('endDate', u'Период по', forceString),
                        ('begDeadline', u'В срок с', forceString),
                        ('endDeadline', u'В срок по', forceString),
                        ('orgStructureId', u'Получатель',
                            lambda id: forceString(db.translate('OrgStructure', 'id', id, 'name'))),
                        ('nomenclatureId', u'Номенклатура',
                            lambda id: forceString(db.translate('rbNomenclature', 'id', id, 'name')))
                        ]
        if widget == 3:
            filter = self.RTMsFilter
            tmpList = [('onlyActive',   u'Только действующие', lambda dummy: u'+'),
                        ('begDate', u'Период с', forceString),
                        ('endDate', u'Период по', forceString),
                        ('begDeadline', u'В срок с', forceString),
                        ('endDeadline', u'В срок по', forceString),
                        ('orgStructureId', u'Заказчик',
                            lambda id: forceString(db.translate('OrgStructure', 'id', id, 'name'))),
                        ('nomenclatureId', u'Номенклатура',
                            lambda id: forceString(db.translate('rbNomenclature', 'id', id, 'name')))
                        ]
        resList = [(u'Список', u'')]
        for (x, y, z) in tmpList:
            self.convertFilterToTextItem(resList, filter, x, y, z)
        return '\n'.join([ ': '.join(item) for item in resList])


    def convertFilterToTextItem(self, resList, filter, prop, propTitle, format=None):
        val = filter.get(prop, None)
        if val:
            if format:
                resList.append((propTitle, format(val)))
            else:
                resList.append((propTitle, val))


    # MR ##(my requests)########################################################

    def resetMRsFilter(self):
        self.chkMRsFilterOnlyActive.setChecked(True)
        self.edtMRsFilterBegDate.setDate(QDate())
        self.edtMRsFilterEndDate.setDate(QDate())
        self.edtMRsFilterBegDeadlineDate.setDate(QDate())
        self.edtMRsFilterEndDeadlineDate.setDate(QDate())
        self.edtMRsFilterBegDeadlineTime.setTime(QTime())
        self.edtMRsFilterEndDeadlineTime.setTime(QTime())
        self.cmbMRsFilterOrgStructure.setValue(None)
        self.cmbMRsFilterNomenclature.setValue(None)
        self.cmbMRsFilterSatisfied.setCurrentIndex(CSatisifiedFilter.ALL)
        self.cmbMRsFilterAgreement.setCurrentIndex(0)


    def applyMRsFilter(self):
        self.MRsFilter.onlyActive = self.chkMRsFilterOnlyActive.isChecked()
        self.MRsFilter.begDate = self.edtMRsFilterBegDate.date()
        self.MRsFilter.endDate = self.edtMRsFilterEndDate.date()
        self.MRsFilter.begDeadline = self.composeDateTime(self.edtMRsFilterBegDeadlineDate.date(), self.edtMRsFilterBegDeadlineTime.time())
        self.MRsFilter.endDeadline = self.composeDateTime(self.edtMRsFilterEndDeadlineDate.date(), self.edtMRsFilterEndDeadlineTime.time())
        self.MRsFilter.orgStructureId = self.cmbMRsFilterOrgStructure.value()
        self.MRsFilter.nomenclatureId = self.cmbMRsFilterNomenclature.value()
        self.MRsFilter.satisfiedFilter = self.cmbMRsFilterSatisfied.currentIndex()
        self.MRsFilter.agreementFilter = self.cmbMRsFilterAgreement.currentIndex()
        self.updateMRsList()


#    def setMRsSort(self, col):
#        self.order = col
#        header=self.tblItems.horizontalHeader()
#        header.setSortIndicatorShown(True)
#        header.setSortIndicator(col, Qt.AscendingOrder)
#        self.updateMRsList()

    def updateMRsList(self, currentId=None):
        filter = self.MRsFilter
        db = QtGui.qApp.db
        table = db.table('StockRequisition')
        tableItems = db.table('StockRequisition_Item')
        orgStructureId = QtGui.qApp.currentOrgStructureId()
        cond = [table['deleted'].eq(0)]
        if orgStructureId:
            cond.append(table['recipient_id'].inlist(getOrgStructureDescendants(orgStructureId)))
        if filter.orgStructureId:
            cond.append(table['supplier_id'].inlist(getOrgStructureDescendants(filter.orgStructureId)))
        if filter.onlyActive:
            cond.append(table['revoked'].eq(0))
        if filter.begDate:
            cond.append(table['date'].ge(filter.begDate))
        if filter.endDate:
            cond.append(table['date'].le(filter.endDate))
        if filter.begDeadline:
            cond.append(table['deadline'].ge(filter.begDeadline))
        if filter.endDeadline:
            cond.append(table['deadline'].le(filter.endDeadline))
        if filter.nomenclatureId:
            subcond = [tableItems['master_id'].eq(table['id']),
                       tableItems['nomenclature_id'].eq(filter.nomenclatureId),
                      ]
            if filter.onlyActive:
                subcond.append(tableItems['qnt'].ge(tableItems['satisfiedQnt']))
            cond.append(db.existsStmt(tableItems, subcond))
        if filter.satisfiedFilter:
            c = CSatisifiedFilter.getFilter(filter.satisfiedFilter, filter.nomenclatureId)
            if c is not None:
                if  filter.satisfiedFilter in (1, 2, 3, 4):
                    cond.append(u'StockRequisition.id in (%s)'%c)
                else:
                    cond.append(c)
        if filter.agreementFilter:
            cond.append(table['agreementStatus'].eq(filter.agreementFilter-1))
        idList = db.getIdList(table, idCol=table['id'], where=cond, order='date DESC, deadline')
        self.actEditRequisition.setEnabled(len(idList))
        self.tblMRs.setIdList(idList, currentId)
        self.lblMRs.setText(formatRecordsCount(len(idList)))

    def updateRealTimeStatus(self, itemId, status):
        db = QtGui.qApp.db
        table = db.table('StockRequisition')
        cond = [table['deleted'].eq(0), table['id'].eq(itemId)]
        db.updateRecords(table, [table['realtimeStatus'].eq(status)], cond)

    def getRealTimeStatus(self, id, items):
        stockRequsitionMotionsId = forceRef(QtGui.qApp.db.translate('StockRequisition_Motions', 'master_id', id, 'id'))
        stockRequsitionItemId = forceRef(QtGui.qApp.db.translate('StockRequisition_Item', 'master_id', id, 'id'))
        status = 0 if not stockRequsitionItemId else 5 if stockRequsitionMotionsId else 2
        return status

    def addRequisition(self):
        counterController = QtGui.qApp.counterController()
        if not counterController:
            QtGui.qApp.setCounterController(CCounterController(self))
        dialog = CStockRequisitionEditDialog(self, isAddRequisition=True)
        res = None
        try:
            dialog.setDefaults()
            dialog._generateStockMotionNumber()
            dialog.setAgreementRequirementsStock()
            res = dialog.exec_()
            if res:
                currentItemId = dialog.itemId()
                self.updateRealTimeStatus(currentItemId, 2 if dialog.tblItems.model().itemIdList() else 0)
                self.updateMRsList(currentItemId)
        finally:
            if res:
                QtGui.qApp.delAllCounterValueIdReservation()
            else:
                QtGui.qApp.resetAllCounterValueIdReservation()
            dialog.deleteLater()


    def editRequisition(self, id):
        dialog = CStockRequisitionEditDialog(self)
        try:
            self.updateRealTimeStatus(id, 1)
            dialog.load(id)
            res = dialog.exec_()
            if res:
                self.updateMRsList(id)
                QtGui.qApp.delAllCounterValueIdReservation()
            else:
                QtGui.qApp.resetAllCounterValueIdReservation()
        finally:
            status = self.getRealTimeStatus(id, dialog.tblItems.model().itemIdList())
            self.updateRealTimeStatus(id, status)
            dialog.deleteLater()

    def editRTMsRequisition(self, id, isEditRTMsRequisitionEnabled=True):
        dialog = CStockRequisitionEditDialog(self)
        try:
            self.updateRealTimeStatus(id, 3)
            dialog.setIsEditRTMsRequisitionEnabled(isEditRTMsRequisitionEnabled)
            dialog.load(id)
            res = dialog.exec_()
            if res:
                self.updateRTMsList(id)
                QtGui.qApp.delAllCounterValueIdReservation()
            else:
                QtGui.qApp.resetAllCounterValueIdReservation()
        finally:
            status = self.getRealTimeStatus(id, dialog.tblItems.model().itemIdList())
            self.updateRealTimeStatus(id, status)
            dialog.deleteLater()

    def updateMRContent(self, requisitionId):
        self.tblMRContent.setIdList(self.getRequisitionItemIdList([requisitionId]))


    # Motions ########################################################

    def on_motionsSortByColumn(self, columnIndex):
        self._tableViewSorter('motions', self.tblMotions, columnIndex)
        self.updateMotionsList()

    def resetMotionsFilter(self):
        self.cmbMotionsFilterType.setCurrentIndex(0)
        self.edtMotionsFilterNumber.setText('')
        self.edtMotionsFilterBegDate.setDate(QDate.currentDate().addDays(-7))
        self.edtMotionsFilterEndDate.setDate(QDate())
        self.edtMotionsFilterReason.setText('')
        self.edtMotionsFilterBegReasonDate.setDate(QDate())
        self.edtMotionsFilterEndReasonDate.setDate(QDate())
        self.cmbMotionsFilterSupplier.setValue(None)
        self.cmbMotionsFilterReceiver.setValue(None)
        self.cmbMotionsFilterNomenclature.setValue(None)
        self.edtMotionsFilterBatch.setText('')
        self.edtMotionsFilterBegShelfTime.setDate(QDate())
        self.edtMotionsFilterEndShelfTime.setDate(QDate())
        self.cmbMotionsFilterFinance.setValue(None)
        self.cmbMotionsFilterMedicalAidKind.setValue(None)
        self.edtMotionsClientFilterReceiver.setText('')
        self.edtMotionsFilterNote.setText('')
        self.cmbMotionsFilterSupplierOrg.setValue(None)
        self.cmbMotionFilterMdlpStage.setValue(None)
        self.chkGroupMotions.setChecked(True)


    def applyMotionsFilter(self):
        filter = self.motionsFilter
        filter.type = self.cmbMotionsFilterType.currentIndex()-1
        filter.number  = forceString(self.edtMotionsFilterNumber.text())
        filter.begDate = self.edtMotionsFilterBegDate.date()
        filter.endDate = self.edtMotionsFilterEndDate.date()
        filter.reason  = forceString(self.edtMotionsFilterReason.text())
        filter.begReasonDate = self.edtMotionsFilterBegReasonDate.date()
        filter.endReasonDate = self.edtMotionsFilterEndReasonDate.date()

        filter.supplierId = self.cmbMotionsFilterSupplier.value()
        filter.receiverId = self.cmbMotionsFilterReceiver.value()
        filter.clientId = forceString(self.edtMotionsClientFilterReceiver.text())
        filter.note = forceString(self.edtMotionsFilterNote.text())
        filter.nomenclatureId = self.cmbMotionsFilterNomenclature.value()
        filter.batch = forceStringEx(self.edtMotionsFilterBatch.text())
        filter.begShelfTime = self.edtMotionsFilterBegShelfTime.date()
        filter.endShelfTime = self.edtMotionsFilterEndShelfTime.date()
        filter.financeId = self.cmbMotionsFilterFinance.value()
        filter.medicalAidKindId = self.cmbMotionsFilterMedicalAidKind.value()
        filter.supplierOrgId = self.cmbMotionsFilterSupplierOrg.value()
        filter.mdlpStage = self.cmbMotionFilterMdlpStage.value()
        filter.groupMotions = self.chkGroupMotions.isChecked()
        self.updateMotionsList()


    def getCond(self):
        filter = self.motionsFilter
        db = QtGui.qApp.db
        table = db.table('StockMotion')
        tableItems = db.table('StockMotion_Item')
        cond = [
            table['deleted'].eq(0),
        ]
        if QtGui.qApp.currentOrgStructureId():
            cond.append(db.joinOr([ table['supplier_id'].inlist(getOrgStructureDescendants(QtGui.qApp.currentOrgStructureId())),
                                    table['receiver_id'].inlist(getOrgStructureDescendants(QtGui.qApp.currentOrgStructureId()))
                                  ]
                                 )
                       )
        if filter.type >=0:
            cond.append(table['type'].eq(filter.type))
        if filter.number:
            cond.append(table['number'].like(filter.number))
        if filter.begDate:
            cond.append(table['date'].ge(filter.begDate))
        if filter.endDate:
            cond.append(table['date'].lt(filter.endDate.addDays(1)))
        if filter.reason:
            cond.append('IFNULL((SELECT name FROM StockPurchaseContract WHERE StockPurchaseContract.id=reason_id), reason) like ' + table['reason'].formatValue(undotLikeMask(filter.reason)))
        if filter.begReasonDate:
            cond.append(table['reasonDate'].ge(filter.begReasonDate))
        if filter.endReasonDate:
            cond.append(table['reasonDate'].lt(filter.endReasonDate.addDays(1)))
        if not filter.supplierOrgId and filter.supplierId:
            cond.append(table['supplier_id'].eq(filter.supplierId))
        elif filter.supplierOrgId:
            cond.append(table['supplierOrg_id'].eq(filter.supplierOrgId))
        if filter.receiverId:
            cond.append(table['receiver_id'].eq(filter.receiverId))
        if filter.note:
            cond.append(table['note'].like(filter.note))
        if filter.clientId:
            cond.append(table['client_id'].eq(filter.clientId))
        if filter.nomenclatureId or filter.financeId or filter.batch or filter.begShelfTime or filter.endShelfTime or filter.medicalAidKindId:
            subcond = [tableItems['master_id'].eq(table['id']), tableItems['deleted'].eq(0)]
            if filter.nomenclatureId:
                subcond.append(tableItems['nomenclature_id'].eq(filter.nomenclatureId))
            if filter.financeId:
                subcond.append(tableItems['finance_id'].eq(filter.financeId))
            if filter.medicalAidKindId:
                subcond.append(tableItems['medicalAidKind_id'].eq(filter.medicalAidKindId))
            if filter.batch:
                subcond.append(tableItems['batch'].eq(filter.batch))
            if filter.begShelfTime:
                subcond.append(tableItems['shelfTime'].ge(filter.begShelfTime))
            if filter.endShelfTime:
                subcond.append(tableItems['shelfTime'].le(filter.endShelfTime))
            cond.append(db.existsStmt(tableItems, subcond))
        if filter.mdlpStage is not None:
            cond.append(table['mdlpStage'].eq(filter.mdlpStage))


        return cond


    def getCols(self): # что за хня?
        table = QtGui.qApp.db.table('StockMotion')
        return [u'IF(StockMotion.`client_id`, StockMotion.`client_id`, StockMotion.`id`) as ident',
                    table['id'],
                    table['type'],
                    table['number'],
                    table['date'],
#                    table['reason'],
                    'IFNULL((SELECT name FROM StockPurchaseContract WHERE StockPurchaseContract.id=reason_id), reason) AS reason',
                    table['supplierOrg_id'],
                    table['supplier_id'],
                    table['receiver_id'],
                    table['client_id'],
                    table['mdlpStage'],
                    table['note'],
                    u'''    (SELECT
                        GROUP_CONCAT(DISTINCT StockMotion_Item.`nomenclature_id`
                                ORDER BY StockMotion_Item.`nomenclature_id` ASC
                                SEPARATOR ', ')
                    FROM
                        StockMotion_Item
                    WHERE
                        StockMotion_Item.`master_id` = StockMotion.`id`) AS motionItems'''
                    ]


    def updateMotionsList(self, currentId=None):
        filter = self.motionsFilter
        db = QtGui.qApp.db
        table = db.table('StockMotion')
        cond = self.getCond()

        sorterData = self._tableViewSorter.getData('motions')
        if sorterData is None:
            order = 'date DESC, id DESC'
        else:
            columnIndex = sorterData.columnIndex
            ascending = sorterData.ascending

            order = []
            if columnIndex in (4, 5):
                order.extend(['date', 'id'])
                ascending = False
            elif columnIndex == 0:
                data = sorted(stockMotionType.items(), key=lambda v: v[1][0])
                o = ['CASE']
                for idx, d in enumerate(data):
                    o.append('WHEN type = %s THEN %s' % (d[0], idx))
                o.append('ELSE 0 END')
                order.append(' '.join(o))
            elif columnIndex == 1:
                order.append('number')
            elif columnIndex == 2:
                order.append('date')
            elif columnIndex == 3:
                order.append('reason')
            elif columnIndex == 6:
                order.append('note')

            order = ', '.join(['{0} {1}'.format(v, ['DESC', 'ASC'][ascending]) for v in order])

        cols = self.getCols()

        if filter.groupMotions:
            cols.append(u'GROUP_CONCAT(DISTINCT StockMotion.`id` ORDER BY StockMotion.`id` ASC SEPARATOR \', \') as idList')
            cols.append(u'COUNT(DISTINCT StockMotion.id) as motionsCount')
            group = u'StockMotion.type, ident, StockMotion.reasonDate, motionItems'
            groupCond = cond[:]
            queryTable = table
            records = db.getRecordListGroupBy(queryTable, cols, where=groupCond, group=group, order=order)
            currentMotionId = self.tblMotions.currentItemId()
            for rec in records:
                self._recordsIdDict[forceInt(rec.value('id'))] = rec
            self.records = records
            self.setGroupedMotionsToTable(records, currentMotionId=currentMotionId if currentMotionId else 0)
            self.lblMotions.setText(formatRecordsCount(len(records)))
        else:
            cols.append(u'StockMotion.`id` as idList')
            records = db.getRecordList(table, cols, where=cond, order=order)
            for rec in records:
                self._recordsIdDict[forceInt(rec.value('id'))] = rec
            currentMotionId = self.tblMotions.currentItemId()
            self.lblMotions.setText(formatRecordsCount(len(records)))
            self.setGroupedMotionsToTable(records, currentMotionId if currentMotionId else None)
            if currentMotionId:
                self.tblMotionsItems.setCurrentItemId(currentMotionId)
        self.tblMotionsItems.setColumnHidden(0, not filter.groupMotions)


    def setGroupedMotionsToTable(self, records, currentMotionId=None):
        idList = []
        if records:
            for record in records:
                id = forceInt(record.value('id'))
                idList.append(id)
        self.modelMotions.setRecords(records)
        self.tblMotions.setIdList(idList, currentMotionId if currentMotionId else None)
        if currentMotionId:
            self.tblMotionsItems.setCurrentItemId(currentMotionId)


    def addMotion(self, dialogClass, requisitionIdList = None, isStockRequsition = False, id=None):
        dialog = dialogClass(self)
        try:
            self.updateRealTimeStatus(id, 4)
            dialog.setDefaults()
            if hasattr(dialog, 'setIsStockRequsition'):
                dialog.setIsStockRequsition(isStockRequsition)
            if dialog.objectName() == 'StockTransUtilizationDialog':
                dialog.tblItems.model().setItems(self.tblMotionsItems.model().recordCache().map.values())
            if requisitionIdList:
                dialog.setRequsitions(requisitionIdList)
            res = dialog.exec_()
            if res:
                self.updateMotionsList(id)
                QtGui.qApp.delAllCounterValueIdReservation()
            else:
                QtGui.qApp.resetAllCounterValueIdReservation()
        finally:
            if isinstance(dialog, CStockRequisitionEditDialog) or isinstance(dialog, CStockRequisitionEditDialog):
                status = self.getRealTimeStatus(id, dialog.tblItems.model().itemIdList())
                self.updateRealTimeStatus(id, status)
            dialog.deleteLater()


    def addIncomingInvoice(self, requisitionIdList = None):
        self.addMotion(CIncomingInvoiceEditDialog, requisitionIdList)

    def addPurchaseInvoice(self, requisitionIdList=None):
        purchaseContractId = self.tblPurchaseContract.currentItemId()
        if purchaseContractId:
            dialog = CPurchaseInvoiceEditDialog(self)
            try:
                db = QtGui.qApp.db
                tableSPC = db.table('StockPurchaseContract')
                record = db.getRecordEx(tableSPC, '*', [tableSPC['id'].eq(purchaseContractId), tableSPC['deleted'].eq(0)])
                type = forceInt(record.value('type')) if record else -1
                if type == 0:
                    dialog.setPurchaseContractInfo(record)
                    id = dialog.exec_()
                    if id:
                        self.applyPurchaseContractFilter()
                        QtGui.qApp.delAllCounterValueIdReservation()
                    else:
                        QtGui.qApp.resetAllCounterValueIdReservation()
            finally:
                dialog.deleteLater()
                
    def addInternalInvoice(self, requisitionIdList = None, isStockRequsition=False, id=None):
        self.addMotion(CInternalInvoiceEditDialog, requisitionIdList, isStockRequsition=isStockRequsition, id=id)


    def addPurchaseContract(self):
        dialog = CPurchaseContractEditDialog(self)
        try:
            id = dialog.exec_()
            if id:
                self.applyPurchaseContractFilter()
                QtGui.qApp.delAllCounterValueIdReservation()
            else:
                QtGui.qApp.resetAllCounterValueIdReservation()
        finally:
            dialog.deleteLater()


    def addInventory(self):
        self.addMotion(CInventoryEditDialog)


    def addFinTransfer(self):
        self.addMotion(CFinTransferEditDialog)


    def addProduction(self):
        self.addMotion(CProductionEditDialog)

    def addUtilization(self):
        from Stock.StockUtilizationEditDialog import CStockUtilizationEditDialog
        self.addMotion(CStockUtilizationEditDialog)

    def addTransUtilization(self):
        from Stock.StockTransUtilizationEditDialog import CStockTransUtilizationEditDialog
        self.addMotion(CStockTransUtilizationEditDialog)
        
    def addInternalConsumption(self):
        from Stock.StockUtilizationEditDialog import CStockInternalConsumptionEditDialog
        self.addMotion(CStockInternalConsumptionEditDialog)

    def addResidualQuantityWriteDown(self):
        from Stock.StockResidualQuantityWriteDownEditDialog import CStockResidualQuantityWriteDownEditDialog
        QtGui.qApp.setCounterController(CCounterController(self))
        res = False
        dialog = CStockResidualQuantityWriteDownEditDialog(self)
        try:
            dialog.setDefaults()
            countRecords = dialog.fill()
            if countRecords:
                res = dialog.exec_()
            else:
                res = False
                messageBox = QtGui.QMessageBox(QtGui.QMessageBox.Warning,
                                  u'Внимание',
                                  u'Отсутствуют остаточные количества. Создание документа невозможно.',
                                  QtGui.QMessageBox.Ok,
                                  self)
                messageBox.exec_()
            if res:
                self.updateMotionsList()
                QtGui.qApp.delAllCounterValueIdReservation()
            else:
                QtGui.qApp.resetAllCounterValueIdReservation()
        finally:
            dialog.deleteLater()

    def addAddClientRefundInvoice(self, clientInvoiceId):
        dialog = CClientRefundInvoiceEditDialog(self)
        try:
            dialog.setDefaults()
            if clientInvoiceId:
                dialog.loadDataFromClientInvoice(clientInvoiceId)
            id = dialog.exec_()
            if id:
                self.updateMotionsList(id)
                QtGui.qApp.delAllCounterValueIdReservation()
            else:
                QtGui.qApp.resetAllCounterValueIdReservation()
        finally:
            dialog.deleteLater()


    @pyqtSignature('')
    def on_actDeleteMotion_triggered(self):
        db = QtGui.qApp.db
        tableStockMotion = db.table('StockMotion')
        tableStockMotionItem = db.table('StockMotion_Item')
        idList = self.tblMotions.selectedItemIdList()
        if idList:
            buttons = QtGui.QMessageBox.Yes | QtGui.QMessageBox.No
            messageBox = QtGui.QMessageBox(QtGui.QMessageBox.Question,
                                           u'Внимание',
                                           u'Действительно удалить?',
                                           buttons,
                                           self)
            messageBox.setWindowFlags(messageBox.windowFlags() | Qt.WindowStaysOnTopHint)
            result = messageBox.exec_()
            if result == QtGui.QMessageBox.Yes:
                if self.motionsFilter.groupMotions:
                    additionalIdList = self.getAdditionalIdList(idList)
                    idList.extend(additionalIdList)
                db.markRecordsDeleted(tableStockMotion, [tableStockMotion['id'].inlist(idList)])
                db.markRecordsDeleted(tableStockMotionItem, [tableStockMotionItem['master_id'].inlist(idList)])
                self.updateMotionsList()


    def getAdditionalIdList(self, idList):
        additionalIdList = []
        if idList:
            for id in idList:
                db = QtGui.qApp.db
                table = db.table('StockMotion')
                cond = self.getCond()
                cols = self.getCols()
                cols.append(u'GROUP_CONCAT(DISTINCT StockMotion.`id` ORDER BY StockMotion.`id` ASC SEPARATOR \', \') as idList')
                cols.append(u'COUNT(DISTINCT StockMotion.id) as motionsCount')
                group = u'''StockMotion.type, ident, StockMotion.reasonDate, motionItems HAVING idList LIKE '%%%s%%' '''%id
                groupCond = cond[:]
                queryTable = table
                records = db.getRecordListGroupBy(queryTable, cols, where=groupCond, group=group, order=u'date DESC , id DESC')
                if records:
                    for record in records:
                        idListValue = forceString(record.value('idList'))
                        idListValue = idListValue.split(',')
                        additionalIdList.extend(idListValue)
        return additionalIdList


    # Remainings #####################################################

    def resetRemainingsFilter(self):
        self.edtRemainingsFilterDate.setDate(QDate())
        self.cmbRemainingsFilterStorage.setValue(QtGui.qApp.currentOrgStructureId())
        self.cmbRemainingsFilterNomenclature.setValue(None)
        self.cmbRemainingsFilterNomenclatureClass.setValue(None)
        self.cmbRemainingsFilterNomenclatureKind.setValue(None)
        self.cmbRemainingsFilterNomenclatureType.setValue(None)
        self.chkRemainingsFilterGroupByBatch.setChecked(False)
        self.edtRemainingsFilterBatch.setText('')
        self.edtRemainingsFilterBegShelfTime.setDate(QDate())
        self.edtRemainingsFilterEndShelfTime.setDate(QDate())
        self.chkRemainingsFilterFinishShelfTime.setChecked(False)
        self.edtRemainingsFilterFinishShelfTimeDays.setValue(0)
        self.edtRemainingsFilterFinishShelfTimeDays.setEnabled(False)
        self.cmbRemainingsFilterFinance.setValue(None)
        self.chkRemainingsFilterConstrainedQnt.setChecked(False)
        self.chkRemainingsFilterOrderQnt.setChecked(False)
        self.chkRemainingsFilterAvailable.setChecked(False)
        self.cmbRemainingsFilterUnit.setValue(None)
        self.edtMotionsClientFilterReceiver.setText('')
        self.edtMotionsFilterNote.setText('')


    def applyRemainingsFilter(self):
        filter = self.remainingsFilter
        filter.date = self.edtRemainingsFilterDate.date()
        filter.storageId = self.cmbRemainingsFilterStorage.value()
        filter.nomenclatureId = self.cmbRemainingsFilterNomenclature.value()
        filter.nomenclatureClassId = self.cmbRemainingsFilterNomenclatureClass.value()
        filter.nomenclatureKindId = self.cmbRemainingsFilterNomenclatureKind.value()
        filter.nomenclatureTypeId = self.cmbRemainingsFilterNomenclatureType.value()
        filter.groupByBatch = self.chkRemainingsFilterGroupByBatch.isChecked()
        filter.batch = forceStringEx(self.edtRemainingsFilterBatch.text())
        filter.begShelfTime = self.edtRemainingsFilterBegShelfTime.date()
        filter.endShelfTime = self.edtRemainingsFilterEndShelfTime.date()
        filter.isFinishShelfTime = self.chkRemainingsFilterFinishShelfTime.isChecked()
        filter.finishShelfTimeDays = self.edtRemainingsFilterFinishShelfTimeDays.value()
        filter.financeId = self.cmbRemainingsFilterFinance.value()
        filter.medicalAidKindId = self.cmbRemainingsMedicalAidKind.value()
        filter.constrainedQnt = self.chkRemainingsFilterConstrainedQnt.isChecked()
        filter.orderQnt = self.chkRemainingsFilterOrderQnt.isChecked()
        filter.available = self.chkRemainingsFilterAvailable.isChecked()
        filter.unit = self.cmbRemainingsFilterUnit.value()
        self.updateRemainingsList()


    def updateRemainingsList(self, currentId=None):
        filter = self.remainingsFilter
        warnAboutExpirationDateDrugDate = None
        orgStructureId = QtGui.qApp.currentOrgStructureId()
        if orgStructureId:
            db = QtGui.qApp.db
            tableOS = db.table('OrgStructure')
            cols = [tableOS['warnAboutExpirationDateDrugDays']]
            cond = [tableOS['deleted'].eq(0),
                    tableOS['id'].eq(orgStructureId),
                    db.joinOr([tableOS['hasStocks'].eq(1), tableOS['mainStocks'].eq(1)]),
                    tableOS['hasWarnAboutExpirationDateDrug'].eq(1)
                   ]
            record = db.getRecordEx(tableOS, cols, cond)
            if record:
                warnAboutExpirationDateDrugDays = forceInt(record.value('warnAboutExpirationDateDrugDays'))
                warnAboutExpirationDateDrugDate = QDate.currentDate().addDays(warnAboutExpirationDateDrugDays)
        self.modelRemainings.setWarnAboutExpirationDateDrugDays(warnAboutExpirationDateDrugDate)
        sortColumn = self.tblRemainings.getSortColumn()
        sortAscending = self.tblRemainings.getSortAscending()
        self.modelRemainings.loadData(filter.date,
                                      filter.storageId,
                                      filter.nomenclatureId,
                                      filter.nomenclatureClassId,
                                      filter.nomenclatureKindId,
                                      filter.nomenclatureTypeId,
                                      filter.groupByBatch,
                                      filter.batch,
                                      filter.begShelfTime,
                                      filter.endShelfTime,
                                      filter.financeId,
                                      filter.medicalAidKindId,
                                      filter.constrainedQnt,
                                      filter.orderQnt,
                                      filter.available,
                                      filter.unit,
                                      filter.isFinishShelfTime,
                                      filter.finishShelfTimeDays
                                      )
        if sortColumn is None and len(self.modelRemainings.items()) > 0:
            sortColumn = self.modelRemainings.items()[0].indexOf('nomenclature_id')
            sortAscending = True
        if sortColumn >= 0:
            self.tblRemainings.setSortColumn(sortColumn)
            self.tblRemainings.setSortAscending(not sortAscending)
            self.tblRemainings.on_sortByColumn(sortColumn)


    # RTMs ##(requests to me)####################################################

    def setRTMsFilterSupplier(self):
        stocksIdList = []
        isRightViewRequirementsForAllStock = QtGui.qApp.userHasRight(urAccessViewRequirementsForAllStock)
        orgStructureId = QtGui.qApp.currentOrgStructureId()
        db = QtGui.qApp.db
        tableOS = db.table('OrgStructure')
        if isRightViewRequirementsForAllStock:
            orgId = QtGui.qApp.currentOrgId()
            if orgId:
                cols = [tableOS['id']]
                cond = [tableOS['deleted'].eq(0),
                        tableOS['organisation_id'].eq(orgId),
                        db.joinOr([tableOS['hasStocks'].eq(1), tableOS['mainStocks'].eq(1)])
                       ]
                stocksIdList = db.getDistinctIdList(tableOS, cols, cond)
        elif orgStructureId:
            orgStructureIdList = db.getDescendants('OrgStructure', 'parent_id', orgStructureId)
            if orgStructureIdList:
                cols = [tableOS['id']]
                cond = [tableOS['deleted'].eq(0),
                        tableOS['id'].inlist(orgStructureIdList),
                        db.joinOr([tableOS['hasStocks'].eq(1), tableOS['mainStocks'].eq(1)])
                       ]
                stocksIdList = db.getDistinctIdList(tableOS, cols, cond)
        if stocksIdList:
            self.cmbRTMsFilterSupplier.setFilter('''id IN (%s)'''%(u','.join(str(id) for id in stocksIdList if id)))
        else:
            self.cmbRTMsFilterSupplier.setFilter('''False''')
        self.cmbRTMsFilterSupplier.setIsValidIdList(stocksIdList)


    def resetRTMsFilter(self):
        self.chkRTMsFilterOnlyActive.setChecked(True)
        self.edtRTMsFilterBegDate.setDate(QDate())
        self.edtRTMsFilterEndDate.setDate(QDate())
        self.edtRTMsFilterBegDeadlineDate.setDate(QDate())
        self.edtRTMsFilterEndDeadlineDate.setDate(QDate())
        self.edtRTMsFilterBegDeadlineTime.setTime(QTime())
        self.edtRTMsFilterEndDeadlineTime.setTime(QTime())
        self.setRTMsFilterSupplier()
        self.cmbRTMsFilterSupplier.setValue(QtGui.qApp.currentOrgStructureId())
        self.cmbRTMsFilterOrgStructure.setValue(None)
        self.cmbRTMsFilterNomenclature.setValue(None)
        self.cmbRTMsFilterSatisfied.setCurrentIndex(CSatisifiedFilter.ALL)
        self.cmbRTMsFilterAgreement.setCurrentIndex(0)


    def applyRTMsFilter(self):
        self.RTMsFilter.onlyActive = self.chkRTMsFilterOnlyActive.isChecked()
        self.RTMsFilter.begDate = self.edtRTMsFilterBegDate.date()
        self.RTMsFilter.endDate = self.edtRTMsFilterEndDate.date()
        self.RTMsFilter.begDeadline = self.composeDateTime(self.edtRTMsFilterBegDeadlineDate.date(), self.edtRTMsFilterBegDeadlineTime.time())
        self.RTMsFilter.endDeadline = self.composeDateTime(self.edtRTMsFilterEndDeadlineDate.date(), self.edtRTMsFilterEndDeadlineTime.time())
        self.RTMsFilter.orgStructureId = self.cmbRTMsFilterOrgStructure.value()
        self.RTMsFilter.supplierId = self.cmbRTMsFilterSupplier.value()
        self.RTMsFilter.nomenclatureId = self.cmbRTMsFilterNomenclature.value()
        self.RTMsFilter.satisfiedFilter = self.cmbRTMsFilterSatisfied.currentIndex()
        self.RTMsFilter.agreementFilter = self.cmbRTMsFilterAgreement.currentIndex()
        self.updateRTMsList()


    def updateRTMsList(self, currentId=None):
        filter = self.RTMsFilter
        db = QtGui.qApp.db
        table = db.table('StockRequisition')
        tableItems = db.table('StockRequisition_Item')
        cond = [table['deleted'].eq(0)
               ]
        if filter.supplierId:
            cond.append(table['supplier_id'].eq(filter.supplierId))
        if filter.orgStructureId:
            cond.append(table['recipient_id'].inlist(getOrgStructureDescendants(filter.orgStructureId)))
        if filter.onlyActive:
            cond.append(table['revoked'].eq(0))
        if filter.begDate:
            cond.append(table['date'].ge(filter.begDate))
        if filter.endDate:
            cond.append(table['date'].le(filter.endDate))
        if filter.begDeadline:
            cond.append(table['deadline'].ge(filter.begDeadline))
        if filter.endDeadline:
            cond.append(table['deadline'].le(filter.endDeadline))
        if filter.nomenclatureId:
            subcond = [tableItems['master_id'].eq(table['id']),
                       tableItems['nomenclature_id'].eq(filter.nomenclatureId),
                      ]
            if filter.onlyActive:
                subcond.append(tableItems['qnt'].ge(tableItems['satisfiedQnt']))
            cond.append(db.existsStmt(tableItems, subcond))
        if filter.satisfiedFilter:
            c = CSatisifiedFilter.getFilter(filter.satisfiedFilter, filter.nomenclatureId)
            if c is not None:
                cond.append(c)
        if filter.agreementFilter:
            cond.append(table['agreementStatus'].eq(filter.agreementFilter-1))
        idList = db.getIdList(table, idCol=table['id'], where=cond, order='date DESC, deadline')
        self.tblRTMs.setIdList(idList, currentId)
        self.lblRTMs.setText(formatRecordsCount(len(idList)))


    def updateRTMContent(self, requisitionId):
        self.tblRTMContent.setIdList(self.getRequisitionItemIdList(requisitionId))


    # slots ####################################################################

    def on_actRemainingsShowStockMotions_triggered(self):
        dialog = QtGui.QDialog(self)
        dialog.setWindowTitle(u'История по остаткам')
        buttonBox = QtGui.QDialogButtonBox()
        buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Ok|QtGui.QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(dialog.accept)
        buttonBox.rejected.connect(dialog.reject)
        cmbShowDeleted = QtGui.QComboBox()
        cmbShowDeleted.addItems([u'нет', u'да', u'только удаленные'])
        layout = QtGui.QGridLayout(dialog)
        layout.addWidget(QtGui.QLabel(u'Вывести информацию об удаленных документах'), 0, 0)
        layout.addWidget(cmbShowDeleted, 0, 1)
        layout.setRowStretch(1, 1)
        layout.addWidget(buttonBox, 2, 0, 1, 2)
        if not dialog.exec_():
            return

        args = {}
        showDeletedIndex = cmbShowDeleted.currentIndex()
        if showDeletedIndex == 1:
            args['showDeleted'] = True
        if showDeletedIndex == 2:
            args['onlyDeleted'] = True

        item = self.tblRemainings.currentItem()
        nomenclatureId = forceRef(item.value('nomenclature_id'))
        args['batch'] = forceString(item.value('batch'))
        args['financeId'] = forceRef(item.value('finance_id'))
        args['medicalAidKindId'] = forceRef(item.value('medicalAidKind_id'))
        args['orgStructureId'] = self.remainingsFilter.storageId
        records = getRemainingHistory(nomenclatureId, **args)
        showRemainingHistoryReport(records, self)


    @pyqtSignature('int')
    def on_tabWidget_currentChanged(self, index):
        if index == 0:
            self.syncSplitters(self.splitterMotions)
#            self.btnPrint.setEnabled(True)
#            self.btnCash.setEnabled(False)
            self.applyMotionsFilter()
        elif index == 1:
            self.syncSplitters(self.splitterRemainings)
            self.applyRemainingsFilter() # обновляем всегда
        elif index == 2:
            self.syncSplitters(self.splitterMRs)
            if not self.visitedMRs:
                self.resetMRsFilter()
                self.visitedMRs = True
            self.applyMRsFilter()
        elif index == 3:
            self.syncSplitters(self.splitterRTMs)
            if not self.visitedRTMs:
                self.resetRTMsFilter()
                self.visitedRTMs = True
            self.applyRTMsFilter()
        elif index == 4:
            self.syncSplitters(self.splitterPurchaseContract)
            if not self.visitedPurchaseContract:
                self.resetPurchaseContractFilter()
                self.visitedPurchaseContract = True
            self.applyPurchaseContractFilter()

        self.preparePrintBtn(index)


    # Motions ########################################################

    @pyqtSignature('int')
    def on_cmbMotionsFilterSupplierOrg_currentIndexChanged(self):
        value = self.cmbMotionsFilterSupplierOrg.value()
        self.cmbMotionsFilterSupplier.setEnabled(not value)

    @pyqtSignature('QAbstractButton*')
    def on_bbxMotionsFilter_clicked(self, button):
        buttonCode = self.bbxMotionsFilter.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.applyMotionsFilter()
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.resetMotionsFilter()
            self.applyMotionsFilter()


    @pyqtSignature('QModelIndex')
    def on_tblMotions_doubleClicked(self, index):
        self.on_actEditMotion_triggered()


    @pyqtSignature('')
    def on_mnuMotions_aboutToShow(self):
        enableSupplierRefund = False
        mdlpStage = None
        id = self.tblMotions.currentItemId()
        if id:
            record = self.tblMotions.model().getRecordById(id)
            if record:
                motionType    = forceInt(record.value('type'))
                supplierOrgId = forceRef(record.value('supplierOrg_id'))
                mdlpStage     = forceInt(record.value('mdlpStage'))
                enableSupplierRefund = (motionType in (CStockMotionType.invoice, CStockMotionType.incomingInvoice)) and bool(supplierOrgId)

        self.actAddSupplierRefund.setEnabled(enableSupplierRefund)

        self.actEditMotion.setEnabled(id is not None)
        self.actDeleteMotion.setEnabled(    id is not None
                                        and mdlpStage in [CMdlpStage.unnecessary, CMdlpStage.ready]
                                        and QtGui.qApp.userHasAnyRight([urDeleteMotions])
                                       )
        self.actMdlpExchange.setEnabled(    id is not None
                                        and mdlpStage in (
#                                                          CMdlpStage.ready, # для ready нужно ещё создать записи :(
                                                          CMdlpStage.inProgress,
                                                         )
                                       )
        self.actMdlpExchangeReport.setEnabled(    id is not None
                                              and mdlpStage >= CMdlpStage.inProgress
                                             )


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelMotions_currentRowChanged(self, current, previous):
        motionId = self.tblMotions.itemId(current)
        self.updateMotionsItemsList(motionId)


    @pyqtSignature('')
    def on_actAddIncomingInvoice_triggered(self):
        self.addIncomingInvoice()

    @pyqtSignature('')
    def on_actAddPurchaseInvoice_triggered(self):
        self.addPurchaseInvoice()

    @pyqtSignature('')
    def on_actAddInternalInvoice_triggered(self):
        self.addInternalInvoice()


    @pyqtSignature('')
    def on_actAddPurchaseContract_triggered(self):
        self.addPurchaseContract()


    @pyqtSignature('')
    def on_actAddInventory_triggered(self):
        self.addInventory()


    @pyqtSignature('')
    def on_actAddFinTransfer_triggered(self):
        self.addFinTransfer()


    @pyqtSignature('')
    def on_actAddProduction_triggered(self):
        self.addProduction()


    @pyqtSignature('')
    def on_actAddUtilization_triggered(self):
        self.addUtilization()
    
    @pyqtSignature('')
    def on_actAddTransUtilization_triggered(self):
        self.addTransUtilization()


    @pyqtSignature('')
    def on_actAddInternalConsumption_triggered(self):
        self.addInternalConsumption()
    
    @pyqtSignature('')
    def on_actAddResidualQuantityWriteDown_triggered(self):
        self.addResidualQuantityWriteDown()


    @pyqtSignature('')
    def on_actEditMotion_triggered(self):
        id = self.tblMotions.currentItemId()
        if id:
            record = self.tblMotions.model().getRecordById(id)
            mdlpStage = forceInt(record.value('mdlpStage'))
            personId = forceInt(QtGui.qApp.db.translate('StockMotion', 'id', id, 'createPerson_id'))
            if (    mdlpStage == CMdlpStage.unnecessary or mdlpStage == CMdlpStage.ready
                 and (
                         (QtGui.qApp.userHasRight(urEditOwnMotions) and QtGui.qApp.userId == personId)
                      or (QtGui.qApp.userHasRight(urEditOtherMotions) and  QtGui.qApp.userId != personId)
                     )
               ):
                if editStockMotion(self, id):
                    self.updateMotionsList(id)
            else:
                openReadOnlyMotion(self, id)
                self.updateMotionsList(id)


    @pyqtSignature('')
    def on_actMdlpExchange_triggered(self):
        id = self.tblMotions.currentItemId()
        if id and QtGui.qApp.isMdlpEnabled():
            connection = CMdlpConnection()
            with CLogger(self, u'Обмен с МДЛП') as logger:
                ok, status = QtGui.qApp.call(self, processMotion, (logger, id, connection))
                if ok:
                    self.updateMotionsList(id)


    @pyqtSignature('')
    def on_actMdlpExchangeReport_triggered(self):
        id = self.tblMotions.currentItemId()
        if id:
            showMdlpExchangeReport(self, id)


    @pyqtSignature('')
    def on_actAddClientRefundInvoice_triggered(self):
        id = self.tblMotions.currentItemId()
        if id:
            motionType = forceInt(QtGui.qApp.db.translate('StockMotion', 'id', id, 'type'))
            if motionType == 4:
                self.addAddClientRefundInvoice(id)


    @pyqtSignature('')
    def on_actAddSupplierRefund_triggered(self):
        id = self.tblMotions.currentItemId()
        if id:
            motionType = forceInt(QtGui.qApp.db.translate('StockMotion', 'id', id, 'type'))
            if motionType in (CStockMotionType.invoice, CStockMotionType.incomingInvoice):
                self.addAddSupplierRefund(id)


    @pyqtSignature('')
    def on_actPrintInvoice_triggered(self):
        currWidget = self.tabWidget.currentIndex()
        if currWidget == 0:
            tbl = self.tblMotions
        elif currWidget == 2:
            tbl = self.tblMRs
        elif currWidget == 3:
            tbl = self.tblRTMs
        id = tbl.currentItemId()
        if id:
            if currWidget == 0:
                motionType = forceInt(QtGui.qApp.db.translate('StockMotion', 'id', id, 'type'))
                if motionType == 0:
                    CReportStockM11(self, id, 0).exec_()
            elif currWidget in [2, ]:
                CReportStockM11(self, id, 1).exec_()


    def addAddSupplierRefund(self, invoiceId):
        dialog = CStockSupplierRefundEditDialog(self)
        try:
            dialog.setDefaults()
            if invoiceId:
                dialog.loadDataSupplierRefund(invoiceId)
            id = dialog.exec_()
            if id:
                self.updateMotionsList(id)
                QtGui.qApp.delAllCounterValueIdReservation()
            else:
                QtGui.qApp.resetAllCounterValueIdReservation()
        finally:
            dialog.deleteLater()


    def updateMotionsItemsList(self, motionId):
        db = QtGui.qApp.db
        motionIdList = []
        motionsString = None
        tableStockMotionItem = db.table('StockMotion_Item')

        if motionId:
            motionsString = forceString(self._recordsIdDict[motionId].value('idList')).split(",")

        if motionsString:
            for motion in motionsString:
                motionIdList.append(motion)

            queryTable = tableStockMotionItem
            cond = [queryTable['master_id'].inlist(motionIdList), queryTable['deleted'].eq(0)]
            filter = self.motionsFilter
            if filter.nomenclatureId:
                cond.append(queryTable['nomenclature_id'].eq(filter.nomenclatureId))
            if filter.financeId:
                cond.append(queryTable['finance_id'].eq(filter.financeId))
            if filter.medicalAidKindId:
                cond.append(queryTable['medicalAidKind_id'].eq(filter.medicalAidKindId))
            if filter.batch:
                cond.append(queryTable['batch'].eq(filter.batch))
            if filter.begShelfTime:
                cond.append(queryTable['shelfTime'].ge(filter.begShelfTime))
            if filter.endShelfTime:
                cond.append(queryTable['shelfTime'].le(filter.endShelfTime))
            idList = db.getIdList(queryTable, tableStockMotionItem['id'], cond)
            currentMotionItemId = self.tblMotions.currentItemId()
            self.modelMotionsItems.setIdList(idList)
            self.tblMotionsItems.setCurrentItemId(currentMotionItemId)
        else:
            self.modelMotionsItems.setIdList(None)


    @pyqtSignature('')
    def on_actOpenMotion_triggered(self):
        db = QtGui.qApp.db
        id = self.tblMotionsItems.currentItemId()
        motionId = db.translate('StockMotion_Item', 'id', id, 'master_id')
        if id:
            personId = forceInt(QtGui.qApp.db.translate('StockMotion', 'id', id, 'createPerson_id'))
            if (QtGui.qApp.userHasRight(urEditOwnMotions) and QtGui.qApp.userId == personId) or (QtGui.qApp.userHasRight(urEditOtherMotions) and  QtGui.qApp.userId != personId):
                if editStockMotion(self, motionId):
                    self.updateMotionsList(motionId)
            else:
                openReadOnlyMotion(self, motionId)


    # Remainings #####################################################


    @pyqtSignature('bool')
    def on_chkRemainingsFilterGroupByBatch_toggled(self, val):
        self.lblRemainingsFilterBatch.setEnabled(val)
        self.edtRemainingsFilterBatch.setEnabled(val)
        self.lblRemainingsFilterBegShelfTime.setEnabled(val)
        self.edtRemainingsFilterBegShelfTime.setEnabled(val)
        self.lblRemainingsFilterEndShelfTime.setEnabled(val)
        self.edtRemainingsFilterEndShelfTime.setEnabled(val)


    @pyqtSignature('QAbstractButton*')
    def on_bbxRemainingsFilter_clicked(self, button):
        buttonCode = self.bbxRemainingsFilter.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.applyRemainingsFilter()
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.resetRemainingsFilter()
            self.applyRemainingsFilter()


    # MR ##(my requests)########################################################

    @pyqtSignature('const QDate&')
    def on_edtMRsFilterBegDeadlineDate_dateChanged(self, date):
        self.edtMRsFilterBegDeadlineTime.setEnabled(bool(date))


    @pyqtSignature('const QDate&')
    def on_edtMRsFilterEndDeadlineDate_dateChanged(self, date):
        self.edtMRsFilterEndDeadlineTime.setEnabled(bool(date))


    @pyqtSignature('QAbstractButton*')
    def on_bbxMRsFilter_clicked(self, button):
        buttonCode = self.bbxMRsFilter.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.applyMRsFilter()
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.resetMRsFilter()
            self.applyMRsFilter()


    @pyqtSignature('')
    def on_actAddRequisition_triggered(self):
        self.addRequisition()


    @pyqtSignature('')
    def on_actEditRequisition_triggered(self):
        id = self.tblMRs.currentItemId()
        if id:
            self.editRequisition(id)
            self.updateMRContent(id)
    
    @pyqtSignature('QModelIndex')
    def on_tblMRs_doubleClicked(self, index):
        self.on_actEditRequisition_triggered()

    @pyqtSignature('QModelIndex')
    def on_tblRTMs_doubleClicked(self, index):
        self.on_actEditRTMsRequisition_triggered()

    def getIsEditRTMsRequisitionEnabled(self):
        isEditRTMsRequisitionEnabled = False
        currentIndex = self.tblRTMs.currentIndex()
        if currentIndex and currentIndex.isValid():
            row = currentIndex.row()
            if 0 <= row < len(self.modelRTMs._idList):
                RTMsId = forceRef(self.modelRTMs._idList[row])
                if RTMsId:
                    db = QtGui.qApp.db
                    tableSR = db.table('StockRequisition')
                    tableSRMotions = db.table('StockRequisition_Motions')
                    tableStockMotion = db.table('StockMotion')
                    queryTable = tableSR.innerJoin(tableSRMotions, tableSRMotions['master_id'].eq(tableSR['id']))
                    queryTable = queryTable.innerJoin(tableStockMotion, tableStockMotion['id'].eq(tableSRMotions['motion_id']))
                    record = db.getRecordEx(queryTable, [tableStockMotion['id']], [tableSR['id'].eq(RTMsId),tableStockMotion['deleted'].eq(0), tableSR['deleted'].eq(0)])
                    stockMotionId = forceRef(record.value('id')) if record else None
                    isEditRTMsRequisitionEnabled = False if stockMotionId else True
        return isEditRTMsRequisitionEnabled

    @pyqtSignature('')
    def on_actEditRTMsRequisition_triggered(self):
        id = self.tblRTMs.currentItemId()
        if id:
            self.editRTMsRequisition(id, isEditRTMsRequisitionEnabled=QtGui.qApp.userHasRight(urEditStockRequirementsToMe) and self.getIsEditRTMsRequisitionEnabled())
            self.updateRTMContent([id])


    @pyqtSignature('QAbstractButton*')
    def on_bbxPurchaseContractFilter_clicked(self, button):
        buttonCode = self.bbxPurchaseContractFilter.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.applyPurchaseContractFilter()
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.resetPurchaseContractFilter()
            self.applyPurchaseContractFilter()
    
    @pyqtSignature('QModelIndex')
    def on_tblPurchaseContract_doubleClicked(self, index):
        self.on_actEditPurchaseContract_triggered()


    @pyqtSignature('')
    def on_actEditPurchaseContract_triggered(self):
        id = self.tblPurchaseContract.currentItemId()
        if id:
            self.editPurchaseContract(id)
            self.updatePurchaseContractItems(id)


    def editPurchaseContract(self, id):
        if id:
            db = QtGui.qApp.db
            tableSPC = db.table('StockPurchaseContract')
            record = db.getRecordEx(tableSPC, [tableSPC['type']], [tableSPC['id'].eq(id), tableSPC['deleted'].eq(0)])
            type = forceInt(record.value('type')) if record else -1
            if type >= 0:
                dialog = CPurchaseInvoiceEditDialog(self) if type == 1 else CPurchaseContractEditDialog(self)
                try:
                    dialog.load(id)
                    id = dialog.exec_()
                    if id:
                        self.applyPurchaseContractFilter()
                        QtGui.qApp.delAllCounterValueIdReservation()
                    else:
                        QtGui.qApp.resetAllCounterValueIdReservation()
                finally:
                    dialog.deleteLater()


    def updatePurchaseContractItems(self, purchaseContractId):
        self.tblPurchaseContractItems.setIdList(self.getPurchaseContractItemIdList([purchaseContractId]))


    def getPurchaseContractItemIdList(self, purchaseContractId):
        if purchaseContractId:
            db = QtGui.qApp.db
            table = db.table('StockPurchaseContract_Item')
            cond = [table['master_id'].inlist(purchaseContractId),
                    table['deleted'].eq(0)
                   ]
            return db.getIdList(table, 'id', where=cond, order='idx, id')
        else:
            return []


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelPurchaseContract_currentRowChanged(self, current, previous):
        purchaseContractId = self.tblPurchaseContract.itemId(current)
        self.updatePurchaseContractItems(purchaseContractId)


    @pyqtSignature('')
    def on_actDeletePurchaseContract_triggered(self):
        id = self.tblPurchaseContract.currentItemId()
        if id:
            db = QtGui.qApp.db
            tablePurchaseContract = db.table('StockPurchaseContract')
            tablePurchaseContractItem = db.table('StockPurchaseContract_Item')
            buttons = QtGui.QMessageBox.Yes | QtGui.QMessageBox.No
            messageBox = QtGui.QMessageBox(QtGui.QMessageBox.Question,
                                           u'Внимание',
                                           u'Действительно удалить?',
                                           buttons,
                                           self)
            messageBox.setWindowFlags(messageBox.windowFlags() | Qt.WindowStaysOnTopHint)
            result = messageBox.exec_()
            if result == QtGui.QMessageBox.Yes:
                db.markRecordsDeleted(tablePurchaseContract, [tablePurchaseContract['id'].eq(id)])
                db.markRecordsDeleted(tablePurchaseContractItem, [tablePurchaseContractItem['master_id'].eq(id)])
                self.applyPurchaseContractFilter()


    def resetPurchaseContractFilter(self):
        self.cmbPurchasesFilterType.setCurrentIndex(0)
        self.edtPurchaseContractFilterNumber.setText(u'')
        self.edtPurchaseContractFilterName.setText(u'')
        self.edtPurchaseContractFilterDate.setDate(QDate.currentDate())
        self.edtPurchaseContractFilterBegDate.setDate(QDate())
        self.edtPurchaseContractFilterEndDate.setDate(QDate())
        self.cmbPurchaseContractFilterSupplierOrg.setValue(None)


    def applyPurchaseContractFilter(self):
        self.purchaseContractFilter.type = self.cmbPurchasesFilterType.currentIndex()
        self.purchaseContractFilter.number = self.edtPurchaseContractFilterNumber.text()
        self.purchaseContractFilter.date = self.edtPurchaseContractFilterDate.date()
        self.purchaseContractFilter.begDate = self.edtPurchaseContractFilterBegDate.date()
        self.purchaseContractFilter.endDate = self.edtPurchaseContractFilterEndDate.date()
        self.purchaseContractFilter.supplierOrgId = self.cmbPurchaseContractFilterSupplierOrg.value()
        self.purchaseContractFilter.name = self.edtPurchaseContractFilterName.text()
        self.updatePurchaseContractList()


    def updatePurchaseContractList(self, currentId=None):
        filter = self.purchaseContractFilter
        db = QtGui.qApp.db
        tablePurchaseContract = db.table('StockPurchaseContract')
        cond = [tablePurchaseContract['deleted'].eq(0)]
        if filter.type:
            cond.append(tablePurchaseContract['type'].eq(filter.type-1))
        if filter.supplierOrgId:
            cond.append(tablePurchaseContract['supplierOrg_id'].eq(filter.supplierOrgId))
        if filter.number:
            cond.append(tablePurchaseContract['number'].eq(filter.number))
        if filter.date:
            cond.append(db.joinOr([db.joinAnd([tablePurchaseContract['type'].eq(CStockPurchaseType.purchaseContract), tablePurchaseContract['begDate'].dateLe(filter.date), tablePurchaseContract['endDate'].dateGe(filter.date)]),
            db.joinAnd([tablePurchaseContract['type'].eq(CStockPurchaseType.purchaseInvoice), tablePurchaseContract['date'].dateGe(filter.date)])]))
        if filter.begDate:
            cond.append(db.joinOr([db.joinAnd([tablePurchaseContract['type'].eq(CStockPurchaseType.purchaseContract), tablePurchaseContract['endDate'].ge(filter.begDate)]),
            db.joinAnd([tablePurchaseContract['type'].eq(CStockPurchaseType.purchaseInvoice), tablePurchaseContract['date'].ge(filter.begDate)])]))
        if filter.endDate:
            cond.append(db.joinOr([db.joinAnd([tablePurchaseContract['type'].eq(CStockPurchaseType.purchaseContract), tablePurchaseContract['begDate'].le(filter.endDate)]),
            db.joinAnd([tablePurchaseContract['type'].eq(CStockPurchaseType.purchaseInvoice), tablePurchaseContract['date'].le(filter.endDate)])]))
        if filter.name:
            cond.append(tablePurchaseContract['name'].eq(filter.name))
        idList = db.getIdList(tablePurchaseContract, idCol=tablePurchaseContract['id'], where=cond, order='date DESC')
        self.tblPurchaseContract.setIdList(idList, currentId)
        self.lblPurchaseContract.setText(formatRecordsCount(len(idList)))


    @pyqtSignature('')
    def on_actRevokeRequisition_triggered(self):
        id = self.tblMRs.currentItemId()
        if id:
            db = QtGui.qApp.db
            record = self.modelMRs.getRecordById(id)
            record.setValue('revoked', QVariant(True))
            table = db.table('StockRequisition')
            db.updateRecord(table, record)
            self.applyMRsFilter()


    @pyqtSignature('')
    def on_actShowOverhead_triggered(self):
        id = self.tblMRs.currentItemId()
        if id:
            records = getMotionRecordsByRequisition(id)
            showRequisitionMotionsHistoryReport(records, self)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelMRs_currentRowChanged(self, current, previous):
        id = self.tblMRs.itemId(current)
        self.updateMRContent(id)


    # RTMs ##(requests to me)####################################################

    @pyqtSignature('const QDate&')
    def on_edtRTMsFilterBegDeadlineDate_dateChanged(self, date):
        self.edtRTMsFilterBegDeadlineTime.setEnabled(bool(date))


    @pyqtSignature('const QDate&')
    def on_edtRTMsFilterEndDeadlineDate_dateChanged(self, date):
        self.edtRTMsFilterEndDeadlineTime.setEnabled(bool(date))


    @pyqtSignature('QAbstractButton*')
    def on_bbxRTMsFilter_clicked(self, button):
        buttonCode = self.bbxRTMsFilter.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.applyRTMsFilter()
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.resetRTMsFilter()
            self.applyRTMsFilter()


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelRTMs_currentRowChanged(self, current, previous):
        id = self.tblRTMs.itemId(current)
        self.updateRTMContent([id])


    @pyqtSignature('')
    def on_actCreateMotionByRequisition_triggered(self):
        RTMsIdList = self.tblRTMs.selectedItemIdList()
        if RTMsIdList:
            self.addInternalInvoice(RTMsIdList, isStockRequsition=True, id=self.tblRTMs.currentItemId())
            self.updateRTMContent(RTMsIdList)


    @pyqtSignature('')
    def on_actChangeAgreementStatus_triggered(self):
        RTMsId = self.tblRTMs.currentItemId()
        if RTMsId:
            dialog = CStockChangeAgreementStatusDialog(self)
            try:
                dialog.loadData(RTMsId)
                if dialog.exec_():
                    self.updateRTMsList(RTMsId)
            finally:
                dialog.deleteLater()


    @pyqtSignature('')
    def on_actShowRTMOverhead_triggered(self):
        id = self.tblRTMs.currentItemId()
        if id:
            records = getMotionRecordsByRequisition(id)
            showRequisitionMotionsHistoryReport(records, self)

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_F5:
            if hasattr(self, 'tabWidget'):
                tabIndex = self.tabWidget.currentIndex()
                if tabIndex == 1:
                    self.updateRemainingsList()
                elif tabIndex == 2:
                    self.updateMRsList()
                elif tabIndex == 3:
                    self.updateRTMsList()
                elif tabIndex == 4:
                    self.updatePurchaseContractList()
                else:
                    self.updateMotionsList()
            event.accept()
        else:
            CDialogBase.keyPressEvent(self, event)
#
# ##############################################################################
#

class CReceiverCol(CRefBookCol):
    def __init__(self,  *args):
        CRefBookCol.__init__(self, *args)
        self.mapClientIdToText = {}


    def format(self, values):
        orgStructureId = forceRef(values[0])
        if orgStructureId:
            return CRefBookCol.format(self, values)
        clientId = forceRef(values[1])
        if clientId:
            text = self.mapClientIdToText.get(clientId, None)
            if text is None:
                text = getClientMiniInfo(clientId)
                self.mapClientIdToText[clientId] = text
            return QVariant(text)
        return QVariant()


    def invalidateRecordsCache(self):
        self.mapClientIdToText = {}
        CRefBookCol.invalidateRecordsCache(self)


class CMdlpStageCol(CCol):
    def __init__(self,  name, fields, defaultWidth=15, alignment='l'):
        CCol.__init__(self, name, fields, defaultWidth, alignment)


    def format(self, values):
        stage = forceInt(values[0])
        return toVariant(CMdlpStage.text(stage))



class CTypeCol(CCol):
    def __init__(self,  name, fields, defaultWidth=15, alignment='l'):
        CCol.__init__(self, name, fields, defaultWidth, alignment)


    def format(self, values):
        type = forceInt(values[0])
        if type in stockMotionType:
            return toVariant(stockMotionType[type][0])
        else:
            return toVariant('{%d}' % type)


class CMyMotionsModel(CTableModel):
    class CSupplierCol(CCol):
        def __init__(self):
            CCol.__init__(self, u'Поставщик', ['supplierOrg_id', 'supplier_id'], defaultWidth=15, alignment='l')
            self.orgStructureCache = CRBModelDataCache.getData('OrgStructure', True, '')
            self.organisationCache = CDbDataCache.getData('Organisation', 'shortName', filter='isSupplier=1', addNone=True, noneText='', order='id')

        def format(self, values):
            supplierOrgId, supplierId = forceRef(values[0]), forceRef(values[1])
            if supplierOrgId:
                if supplierOrgId in self.organisationCache.idList:
                    dataIndex = self.organisationCache.idList.index(supplierOrgId)
                    value = self.organisationCache.strList[dataIndex]
                else:
                    value = u'{ %d }' % supplierOrgId
                return toVariant(value)

            elif supplierId:
                return toVariant(self.orgStructureCache.getStringById(int(supplierId), CRBComboBox.showName))

            else:
                return CCol.invalid

        def invalidateRecordsCache(self):
            self.orgStructureCache = CRBModelDataCache.getData('OrgStructure', True, '')
            self.organisationCache = CDbDataCache.getData('Organisation', 'shortName', filter='isSupplier=1', addNone=True, noneText='', order='id')


    def __init__(self, parent):
        CTableModel.__init__(self, parent, [
            CTypeCol(     u'Тип',           ['type'],   20),
            CTextCol(      u'Номер',         ['number'], 20),
            CDateTimeCol(  u'Дата и время',  ['date'],   20),
            CTextCol(      u'Основание',     ['reason'], 20),
            CMyMotionsModel.CSupplierCol(),
            CReceiverCol( u'Получатель',     ['receiver_id', 'client_id'], 'OrgStructure', 15),
            CMdlpStageCol(u'Обмен с МДЛП',   ['mdlpStage'], 20),
            CTextCol(      u'Примечание',    ['note'],  20),
            ], 'StockMotion' )
        self._records = {}
        self._boldRows = {}


    def setRecords(self, records):
        self._records = {}
        self._boldRows = {}
        for row, record in enumerate(records):
            self._records[forceInt(record.value("id"))] = record
            if forceInt(record.value('motionsCount'))>1:
                self._boldRows[row] = True


    def getRecordValues(self, column, row):
        col = self._cols[column]
        if self._prevColumn != column or self._prevRow != row or self._prevData is None:
            recordId = self._idList[row]
            record = self._records.get(recordId)
            self._prevData   = col.extractValuesFromRecord(record)
            self._prevColumn = column
            self._prevRow    = row
        return col, self._prevData


    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        #column = index.column()
        row    = index.row()
        if role == Qt.FontRole:
            font = QtGui.QFont()
            if self._boldRows.get(row, False):
                font.setBold(True)
            return font
        else:
            return CTableModel.data(self, index, role)


class CMyMotionsItemsModel(CTableModel):
    class CDateCol(CCol):
        def __init__(self, title, fields, defaultWidth, alignment='l'):
            CCol.__init__(self, title, fields, defaultWidth, alignment)
            self.date = None

        def format(self, values):
            recordId = forceRef(values[1].value('master_id'))
            if recordId:
                if self.date:
                    return self.date
                else:
                    self.data = QtGui.qApp.db.translate('StockMotion',  'id', recordId, 'date')  #CRBModelDataCache.getData(tableName, True, '')
                    return self.data
            else:
                return CCol.invalid

        def invalidateRecordsCache(self):
            self.data = None

    def __init__(self, parent):
        CTableModel.__init__(self, parent, [
            CMyMotionsItemsModel.CDateCol( u'Дата и время',  ['master_id'],   20),
            CRefBookCol(  u'ЛСиИМН',    ['nomenclature_id'],  'rbNomenclature',  20),
            CTextCol(     u'Серия',     ['batch'], 20),
            CDateCol(     u'Годен до',  ['shelfTime'],   20),
            CRefBookCol(  u'Тип финансирования',     ['finance_id'], 'rbFinance',  20),
            CRefBookCol(  u'Вид медицинской помощи',     ['medicalAidKind_id'], 'rbMedicalAidKind',  20),
            CQntDoubleCol(u'Кол-во',    ['qnt'], 20),
            CRefBookCol(  u'Ед.Учета',  ['unit_id'], 'rbUnit', 20),
            CSumCol(      u'Сумма',     ['sum'], 20),
            ], 'StockMotion_Item' )


#
# ##############################################################################
#

class CRemainingsModel(CRecordListModel):
    class CSumCol(CFloatInDocTableCol):
        def _toString(self, value):
            if value.isNull():
                return None
            sum = forceDouble(value)
            if sum == -0:
                sum = 0.0
            return format(sum, '.2f')

#    class CPriceCol(CFloatInDocTableCol):
#        def _toString(self, value):
#            price = forceDouble(value)
#            return format(price, '.2f')

    class CBaseLocNomenclatureValuesCol(CInDocTableCol):
        def __init__(self, nomenclatureCache, *args, **params):
            CInDocTableCol.__init__(self, *args, **params)
            self._cache = {None: QVariant()}
            self._nomenclatureCache = nomenclatureCache

        def getNomenclatureValues(self, nomenclatureId):
            if nomenclatureId not in self._nomenclatureCache:
                record = QtGui.qApp.db.getRecord('rbNomenclature', 'lfForm_id, dosageValue', nomenclatureId)
                self._nomenclatureCache[nomenclatureId] = {'lfForm_id': record.value('lfForm_id'),
                                                           'dosageValue': record.value('dosageValue')}
            return self._nomenclatureCache[nomenclatureId]

    class CNomenclatureFormCol(CBaseLocNomenclatureValuesCol):
        def toString(self, val, record):
            nomenclatureId = forceRef(val)
            if not nomenclatureId in self._cache:
                nomenclatureValues = self.getNomenclatureValues(nomenclatureId)
                lfFormId = forceRef(nomenclatureValues['lfForm_id'])
                if lfFormId:
                    cache = CRBModelDataCache.getData('rbLfForm')
                    result = QVariant(cache.getStringById(lfFormId, CRBComboBox.showName))
                else:
                    result = QVariant()
                self._cache[nomenclatureId] = result
            return self._cache[nomenclatureId]

    class CNomenclatureDosageCol(CBaseLocNomenclatureValuesCol):
        def toString(self, val, record):
            nomenclatureId = forceRef(val)
            nomenclatureValues = self.getNomenclatureValues(nomenclatureId)
            return nomenclatureValues['dosageValue']


    def __init__(self, parent):
        CRecordListModel.__init__(self, parent)
        self._cacheNomenclatureValues = {}
        self.addCol(CRBInDocTableCol(u'Подразделение', 'orgStructure_id', 50, 'OrgStructure', showFields = CRBComboBox.showCode).setSortable())
        self.addCol(CNomenclatureInDocTableCol(u'ЛСиИМН', 'nomenclature_id', 50, showFields = CRBComboBox.showName).setSortable())
        self.addCol(CInDocTableCol(     u'Серия', 'batch', 16).setSortable())
        self.addCol(CDateInDocTableCol( u'Годен до', 'shelfTime', 12, canBeEmpty=True).setSortable())
        self.addCol(CRBInDocTableCol(   u'Тип финансирования', 'finance_id', 15, 'rbFinance').setSortable())
        self.addCol(CRBInDocTableCol(   u'Вид медицинской помощи', 'medicalAidKind_id', 15, 'rbMedicalAidKind').setSortable())
        self.addCol(getStockMotionItemQuantityColumn( u'Кол-во', 'qnt', 12).setSortable())
        self.addCol(CRBInDocTableCol(   u'Ед.Учета.', 'unitId', 15, 'rbUnit').setSortable())
        self.addCol(CFloatInDocTableCol(u'Цена', 'price', 12, precision=2).setSortable())
#        self.addCol(CRemainingsModel.CPriceCol(u'Цена', 'price', 12, precision=2).setSortable())
        self.addCol(CRemainingsModel.CSumCol( u'Сумма', 'sum', 12).setSortable())
        self.addCol(CFloatInDocTableCol(u'Гантированный запас', 'constrainedQnt', 12).setSortable())
        self.addCol(CFloatInDocTableCol(u'Точка заказа', 'orderQnt', 12).setSortable())
        self.addCol(CRemainingsModel.CNomenclatureDosageCol(
        self._cacheNomenclatureValues,  u'Дозировка', 'nomenclature_id', 12).setSortable())
        self.addCol(CRemainingsModel.CNomenclatureFormCol(
        self._cacheNomenclatureValues,  u'Форма выпуска', 'nomenclature_id', 12).setSortable())
        self._cachedRow = None
        self._cachedRowColor = None
        self.warnAboutExpirationDateDrugDate = None


    def setWarnAboutExpirationDateDrugDays(self, warnAboutExpirationDateDrugDate):
        self.warnAboutExpirationDateDrugDate = warnAboutExpirationDateDrugDate


    def flags(self, index):
        return Qt.ItemIsSelectable|Qt.ItemIsEnabled


    def getRowColor(self, row):
        if self._cachedRow != row:
            self._cachedRow = row
            record = self._items[row]
            varQnt = record.value('qnt')
            varConstrainedQnt = record.value('constrainedQnt')
            varOrderQnt = record.value('orderQnt')
            self._cachedRowColor = None
            if not (varConstrainedQnt.isNull() or varOrderQnt.isNull()):
                qnt = forceDouble(varQnt)
                constrainedQnt = forceDouble(varConstrainedQnt)
                orderQnt = forceDouble(varOrderQnt)
                if qnt<constrainedQnt:
                    self._cachedRowColor = QtGui.QColor(Qt.darkRed)
                elif qnt<orderQnt:
                    self._cachedRowColor = QtGui.QColor(Qt.darkGreen)
        return self._cachedRowColor


    def data(self, index, role=Qt.DisplayRole):
        row = index.row()
        if role == Qt.TextColorRole:
            if self.warnAboutExpirationDateDrugDate is not None:
                if row >= 0 and row < len(self._items):
                    record = self._items[row]
                    if forceDouble(record.value('qnt')) < 0:
                        return toVariant(QtGui.QColor(Qt.black))
                    shelfTime = forceDate(record.value('shelfTime'))
                    if shelfTime <= self.warnAboutExpirationDateDrugDate:
                        return toVariant(QtGui.QColor(Qt.red))
        elif role == Qt.ForegroundRole:
            return toVariant(self.getRowColor(row))
        elif role == Qt.BackgroundColorRole:
            record = self._items[row]
            if forceDouble(record.value('qnt'))<0:
                return toVariant(QtGui.QColor(Qt.red))
        else:
            return CRecordListModel.data(self, index, role)


    def loadData(self,
                date,
                orgStructureId,
                nomenclatureId,
                nomenclatureClassId,
                nomenclatureKindId,
                nomenclatureTypeId,
                groupByBatch,
                batch,
                begShelfTime,
                endShelfTime,
                financeId,
                medicalAidKindId,
                constrainedQnt,
                orderQnt,
                available, unit,
                isFinishShelfTime,
                finishShelfTimeDays):
        self._items = []
        db = QtGui.qApp.db
        tableStockTrans = db.table('StockTrans')
        tableSMI = db.table('StockMotion_Item')
        tableOrgStructureStock = db.table('OrgStructure_Stock')
        debCond = []
        creCond = []
        ossCond = []
#        inventoryLastDate = getInventoryLastDate(orgStructureId)
#        if inventoryLastDate:
#            debCond.append(tableStockTrans['date'].dateGe(inventoryLastDate))
#            creCond.append(tableStockTrans['date'].dateGe(inventoryLastDate))
        if date:
            debCond.append(tableStockTrans['date'].dateLe(date))
            creCond.append(tableStockTrans['date'].dateLe(date))
        if isFinishShelfTime:
            tGE = tableStockTrans['shelfTime'].ge(QDate.currentDate())
            debCond.append(tGE)
            creCond.append(tGE)
            tLE = tableStockTrans['shelfTime'].le(QDate.currentDate().addDays(finishShelfTimeDays))
            debCond.append(tLE)
            creCond.append(tLE)
        if orgStructureId:
            debCond.append(tableStockTrans['debOrgStructure_id'].eq(orgStructureId))
            creCond.append(tableStockTrans['creOrgStructure_id'].eq(orgStructureId))
            ossCond.append(tableOrgStructureStock['master_id'].eq(orgStructureId))
        else:
            debCond.append(tableStockTrans['debOrgStructure_id'].isNotNull())
            creCond.append(tableStockTrans['creOrgStructure_id'].isNotNull())
        if nomenclatureId:
            debCond.append(tableStockTrans['debNomenclature_id'].eq(nomenclatureId))
            creCond.append(tableStockTrans['creNomenclature_id'].eq(nomenclatureId))
            ossCond.append(tableOrgStructureStock['nomenclature_id'].eq(nomenclatureId))
        joinNomenclatureFilter = u''''''
        if nomenclatureClassId:
            joinNomenclatureFilter = u''' INNER JOIN rbNomenclatureType ON (rbNomenclature.type_id = rbNomenclatureType.id %s)
                                          INNER JOIN rbNomenclatureKind ON (rbNomenclatureType.kind_id = rbNomenclatureKind.id %s)
                                          INNER JOIN rbNomenclatureClass ON (rbNomenclatureKind.class_id = rbNomenclatureClass.id AND rbNomenclatureClass.id = %s)
            '''%((u'AND rbNomenclatureType.id = %s'%(nomenclatureTypeId)) if nomenclatureTypeId else u'',
                 (u'AND rbNomenclatureKind.id = %s'%(nomenclatureKindId)) if nomenclatureKindId else u'',
                  nomenclatureClassId)
        elif nomenclatureKindId:
            joinNomenclatureFilter = u''' INNER JOIN rbNomenclatureType ON (rbNomenclature.type_id = rbNomenclatureType.id %s)
                                          INNER JOIN rbNomenclatureKind ON (rbNomenclatureType.kind_id = rbNomenclatureKind.id AND rbNomenclatureKind.id = %s)
            '''%((u'AND rbNomenclatureType.id = %s'%(nomenclatureTypeId)) if nomenclatureTypeId else u'', nomenclatureKindId)
        elif nomenclatureTypeId:
            joinNomenclatureFilter = u''' INNER JOIN rbNomenclatureType ON (rbNomenclature.type_id = rbNomenclatureType.id AND rbNomenclatureType.id = %s)'''%(nomenclatureTypeId)
        if groupByBatch:
            batchFields = 'StockTrans.batch, StockTrans.shelfTime, StockTrans.price AS price, '
            sqlGroupByBatch = 'batch, shelfTime, price, '
            sqlGroupByBatchT = 'T.batch, T.shelfTime, T.price, '
            if batch:
                t = tableStockTrans['batch'].eq(batch)
                debCond.append(t)
                creCond.append(t)
            if begShelfTime:
                t = tableStockTrans['shelfTime'].ge(begShelfTime)
                debCond.append(t)
                creCond.append(t)
            if endShelfTime:
                t = tableStockTrans['shelfTime'].le(endShelfTime)
                debCond.append(t)
                creCond.append(t)
        else:
            batchFields = '\'\' AS batch, NULL AS shelfTime, NULL AS price, '
            sqlGroupByBatch = ''
            sqlGroupByBatchT = ''
        if financeId:
            debCond.append(tableStockTrans['debFinance_id'].eq(financeId))
            creCond.append(tableStockTrans['creFinance_id'].eq(financeId))
            ossCond.append(tableOrgStructureStock['finance_id'].eq(financeId))
        if medicalAidKindId:
            debCond.append(tableSMI['medicalAidKind_id'].eq(medicalAidKindId))
            creCond.append(tableSMI['medicalAidKind_id'].eq(medicalAidKindId))
        havCond = ['(`qnt` != 0 OR `sum` != 0 OR `constrainedQnt` IS NOT NULL)']
        if constrainedQnt:
            havCond.append('`qnt`<`constrainedQnt`')
        if orderQnt:
            havCond.append('`qnt`<`orderQnt`')

        if unit:
            unitId = unit
            unitCol = '%s AS unitId' %unitId
            unitParams = '''
    (SELECT
                rbNomenclature_UnitRatio.ratio
            FROM
                rbNomenclature_UnitRatio
            WHERE
                rbNomenclature_UnitRatio.sourceUnit_id = RBUSource.id
                    AND rbNomenclature_UnitRatio.targetUnit_id =  %(unitId)s
                    AND rbNomenclature_UnitRatio.master_id = rbNomenclature.id) AS `ratio`,
    (SELECT
            rbUnit.name
        FROM
            rbNomenclature_UnitRatio
                LEFT JOIN
            rbUnit ON rbUnit.id = rbNomenclature_UnitRatio.targetUnit_id
        WHERE
            rbNomenclature_UnitRatio.sourceUnit_id = RBUSource.id
                AND rbNomenclature_UnitRatio.targetUnit_id = %(unitId)s
                AND rbNomenclature_UnitRatio.master_id = rbNomenclature.id) AS `unitName`
            '''%{
            'unitId':unitId,
            }
        else:
            unitCol = 'RBUSource.id AS `unitId`'
            unitParams = '1'

        stmt = u'''
SELECT T.orgStructure_id,
       T.nomenclature_id,
       T.price,
       T.batch,
       T.shelfTime,
       T.medicalAidKind_id,
       T.finance_id,
       sum(T.qnt) AS `qnt`,
       sum(T.`sum`) AS `sum`,
       %(unitCol)s,
       %(unitParams)s,
       OrgStructure_Stock.constrainedQnt AS constrainedQnt,
       OrgStructure_Stock.orderQnt AS orderQnt
FROM
    (
    SELECT debOrgStructure_id AS orgStructure_id,
           debNomenclature_id AS nomenclature_id,
           %(batchFields)s
           StockMotion_Item.medicalAidKind_id,
           debFinance_id      AS finance_id,
           sum(StockTrans.qnt)           AS `qnt`,
           sum(StockTrans.`sum`)         AS `sum`
    FROM StockTrans
    LEFT JOIN StockMotion_Item ON StockMotion_Item.id = StockTrans.stockMotionItem_id
    LEFT JOIN StockMotion ON StockMotion.id = StockMotion_Item.master_id
    WHERE %(debCond)s AND (StockMotion.deleted=0) AND (StockMotion_Item.deleted=0) AND (StockMotion.type != 2)
    GROUP BY debOrgStructure_id, debNomenclature_id, %(groupByBatch)s debFinance_id, medicalAidKind_id

    UNION ALL
    SELECT creOrgStructure_id AS orgStructure_id,
           creNomenclature_id AS nomenclature_id,
           %(batchFields)s
           StockMotion_Item.medicalAidKind_id,
           creFinance_id      AS finance_id,
           -sum(StockTrans.qnt)          AS `qnt`,
           -sum(StockTrans.`sum`)        AS `sum`
    FROM StockTrans
    LEFT JOIN StockMotion_Item ON StockMotion_Item.id = StockTrans.stockMotionItem_id
    LEFT JOIN StockMotion ON StockMotion.id = StockMotion_Item.master_id
    WHERE %(creCond)s AND (StockMotion.deleted=0) AND (StockMotion_Item.deleted=0) AND (StockMotion.type != 2)
    GROUP BY creOrgStructure_id, creNomenclature_id, %(groupByBatch)s creFinance_id, medicalAidKind_id

    UNION ALL
        SELECT debOrgStructure_id AS orgStructure_id,
           debNomenclature_id AS nomenclature_id,
           %(batchFields)s
           StockMotion_Item.medicalAidKind_id,
           debFinance_id      AS finance_id,
           sum(StockTrans.qnt)           AS `qnt`,
           sum(StockTrans.`sum`)         AS `sum`
    FROM StockTrans
    LEFT JOIN StockMotion_Item ON StockMotion_Item.id = StockTrans.stockMotionItem_id
    LEFT JOIN StockMotion ON StockMotion.id = StockMotion_Item.master_id
    WHERE %(debCond)s AND (StockMotion.deleted=0) AND (StockMotion_Item.deleted=0) AND (StockMotion.type = 2)
    GROUP BY debOrgStructure_id, debNomenclature_id, %(groupByBatch)s debFinance_id, medicalAidKind_id

    UNION ALL
    SELECT creOrgStructure_id AS orgStructure_id,
           creNomenclature_id AS nomenclature_id,
           %(batchFields)s
           StockMotion_Item.oldMedicalAidKind_id AS medicalAidKind_id,
           StockMotion_Item.oldFinance_id      AS finance_id,
           -sum(StockTrans.qnt)          AS `qnt`,
           -sum(StockTrans.`sum`)        AS `sum`
    FROM StockTrans
    LEFT JOIN StockMotion_Item ON StockMotion_Item.id = StockTrans.stockMotionItem_id
    LEFT JOIN StockMotion ON StockMotion.id = StockMotion_Item.master_id
    WHERE %(creCond)s AND (StockMotion.deleted=0) AND (StockMotion_Item.deleted=0) AND (StockMotion.type = 2)
    GROUP BY creOrgStructure_id, creNomenclature_id, %(groupByBatch)s creFinance_id, medicalAidKind_id

    UNION ALL
    SELECT master_id          AS orgStructure_id,
           nomenclature_id    AS nomenclature_id,
           ''                 AS batch,
           NULL               AS shelfTime,
           0                  AS price,
           NULL               AS medicalAidKind_id,
           finance_id         AS finance_id,
           0                  AS `qnt`,
           0                  AS `sum`
    FROM OrgStructure_Stock
    WHERE %(ossCond)s
    GROUP BY master_id, nomenclature_id, finance_id
    ) AS T
    LEFT JOIN OrgStructure ON OrgStructure.id = T.orgStructure_id
    LEFT JOIN rbNomenclature ON rbNomenclature.id = T.nomenclature_id
    %(joinNomenclatureFilter)s
    LEFT JOIN rbUnit AS RBUSource ON rbNomenclature.defaultStockUnit_id = RBUSource.id
    LEFT JOIN rbFinance ON rbFinance.id = T.finance_id
    LEFT JOIN OrgStructure_Stock ON OrgStructure_Stock.master_id = T.orgStructure_id
          AND OrgStructure_Stock.nomenclature_id = T.nomenclature_id
          AND OrgStructure_Stock.finance_id = T.finance_id
GROUP BY orgStructure_id, nomenclature_id, %(groupByBatchT)s finance_id, medicalAidKind_id
HAVING (%(havCond)s)
ORDER BY OrgStructure.code, rbNomenclature.code, rbNomenclature.name, %(groupByBatchT)s rbFinance.code
''' % {
        'debCond' : db.joinAnd(debCond) if debCond else '1',
        'creCond' : db.joinAnd(creCond) if creCond else '1',
        'ossCond' : db.joinAnd(ossCond) if ossCond else '1',
        'joinNomenclatureFilter' : joinNomenclatureFilter,
        'havCond' : db.joinAnd(havCond),
        'groupByBatch' : sqlGroupByBatch,
        'groupByBatchT' : sqlGroupByBatchT,
        'batchFields'  : batchFields,
        'unitCol':unitCol,
        'unitParams':unitParams,
      }
        precision = QtGui.qApp.numberDecimalPlacesQnt()
        query = db.query(stmt)
        if available:
            while query.next():
                record = query.record()
                # Отображаем теперь только те которые в наличии, то есть положительное количество.
                qntRes = round(forceDouble(record.value('qnt')), precision)  # #0014352:0058274
                if qntRes > 0:
                    if unit:
                        if forceDouble(record.value('ratio')):
                            itemQnt = forceDouble(record.value('qnt'))*forceDouble(record.value('ratio'))
                            record.setValue('qnt', toVariant(itemQnt))
                            self._items.append(record)
                    else:
                        self._items.append(record)
        else:
            while query.next():
                record = query.record()
                qntRes = abs(round(forceDouble(record.value('qnt')), precision))  # #0014352:0058274
                if qntRes > 0:
                    if unit:
                        if forceDouble(record.value('ratio')):
                            itemQnt = forceDouble(record.value('qnt'))*forceDouble(record.value('ratio'))
                            record.setValue('qnt', toVariant(itemQnt))
                            self._items.append(query.record())
                    else:
                        self._items.append(query.record())
        self.reset()
#
# ##############################################################################
#

class CMyRequisitionsModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent, [
            CTextCol(     u'Номер',         ['number'], 20),
            CDateCol(     u'Дата',          ['date'],  20),
            CDateTimeCol( u'Срок',          ['deadline'], 20),
            CRefBookCol(  u'Поставщик',     ['supplier_id'], 'OrgStructure', 15),
            CDateCol(     u'Дата согласования', ['agreementDate'],  20),
            CEnumCol(   u'Статус согласования',['agreementStatus'],  (u'Не согласовано', u'Согласовано', u'Отклонено'), 20),
            CRefBookCol(  u'Согласовал',     ['agreementPerson_id'], 'vrbPersonWithSpeciality', 15),
            CTextCol(    u'Статус',            ['realtimeStatus'], 20),
            CTextCol(     u'Примечание',    ['note'],  20),
            ], '')
        self.loadField('revoked')
        self.setTable('StockRequisition')

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        else:
            statusText, statusColor = None, None
            row = index.row()
            column = index.column()
            record = self.getRecordByRow(row)
            realtimeStatus = forceInt(record.value('realtimeStatus'))
            if realtimeStatus in CStockDialog.realtimeStatusDict.keys():
                statusText, statusColor = CStockDialog.realtimeStatusDict[realtimeStatus]
            if role == Qt.DisplayRole:
                if column == 7:
                    return toVariant(statusText)
            elif role == Qt.BackgroundColorRole:
                if column == 5:
                    agreementStatus = forceInt(record.value('agreementStatus'))
                    if agreementStatus == 0:
                        return toVariant(QtGui.QBrush(QtGui.QColor(Qt.red).light(150)))
                    elif agreementStatus == 1:
                        return toVariant(QtGui.QBrush(QtGui.QColor(Qt.green).light(150)))
                    elif agreementStatus == 2:
                        return toVariant(QtGui.QBrush(QtGui.QColor(Qt.yellow).light(150)))
                elif column == 7 and statusColor:
                    return toVariant(QtGui.QBrush(QtGui.QColor(statusColor)))
        return CTableModel.data(self, index, role)

#
# ##############################################################################|
#

class CRequisitionsToMeModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent, [
            CTextCol(     u'Номер',         ['number'], 20),
            CDateCol(     u'Дата',          ['date'],  20),
            CDateTimeCol( u'Срок',          ['deadline'], 20),
            CRefBookCol(  u'Заказчик',      ['recipient_id'], 'OrgStructure', 15),
            CDateCol(     u'Дата согласования', ['agreementDate'],  20),
            CRefBookCol(  u'Согласовал',     ['agreementPerson_id'], 'vrbPersonWithSpeciality', 15),
            CTextCol(     u'Статус',            ['realtimeStatus'], 20),
            CTextCol(     u'Примечание',    ['note'],  20),
            ], 'StockRequisition' )

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        else:
            statusText, statusColor = None, None
            row = index.row()
            column = index.column()
            record = self.getRecordByRow(row)
            realtimeStatus = forceInt(record.value('realtimeStatus'))
            if realtimeStatus in CStockDialog.realtimeStatusDict.keys():
                statusText, statusColor = CStockDialog.realtimeStatusDict[realtimeStatus]
            if role == Qt.DisplayRole:
                if column == 6:
                    return QVariant(statusText)
            elif role == Qt.BackgroundColorRole:
                if column == 6 and statusColor:
                    return QVariant(QtGui.QBrush(QtGui.QColor(statusColor)))
        return CTableModel.data(self, index, role)

#
# ##############################################################################
#

class CRequisitionContentModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent, [
            CRefBookCol(  u'ЛСиИМН',             ['nomenclature_id'], 'rbNomenclature', 50),
            CRefBookCol(  u'Тип финансирования', ['finance_id'],      'rbFinance', 15),
            CRefBookCol(  u'Вид медицинской помощи', ['medicalAidKind_id'], 'rbMedicalAidKind',  20),
            CQntDoubleCol(u'Кол-во',             ['qnt'],  12),
            CQntDoubleCol(u'Отпущено',           ['satisfiedQnt'],  12),
            ], 'StockRequisition_Item' )


#
# ###################################################################################
#

class CPurchaseContractModel(CTableModel):
    class CSupplierCol(CCol):
        def __init__(self):
            CCol.__init__(self, u'Поставщик', ['supplierOrg_id'], defaultWidth=15, alignment='l')
            self.organisationCache = CDbDataCache.getData('Organisation', 'shortName', filter='isSupplier=1', addNone=True, noneText='', order='id')

        def format(self, values):
            supplierOrgId = forceRef(values[0])
            if supplierOrgId:
                if supplierOrgId in self.organisationCache.idList:
                    dataIndex = self.organisationCache.idList.index(supplierOrgId)
                    value = self.organisationCache.strList[dataIndex]
                else:
                    value = u'{ %d }' % supplierOrgId
                return toVariant(value)
            else:
                return CCol.invalid

        def invalidateRecordsCache(self):
            self.organisationCache = CDbDataCache.getData('Organisation', 'shortName', filter='isSupplier=1', addNone=True, noneText='', order='id')


    def __init__(self, parent):
        CTableModel.__init__(self, parent, [
            CEnumCol(     u'Тип',                     ['type'],  (u'Контракт на закупку', u'Заявка на поставку'), 20),
            CTextCol(     u'Номер',                   ['number'], 20),
            CDateTimeCol( u'Дата и время',            ['date'],   20),
            CTextCol(     u'Наименование',            ['name'], 20),
            CTextCol(     u'Наименование для печати', ['title'], 20),
            CPurchaseContractModel.CSupplierCol(),
            CDateCol(     u'Период действия с',       ['begDate'],   20),
            CDateCol(     u'Период действия по',      ['endDate'],   20),
            CRefBookCol(  u'Тип финансирования',      ['finance_id'], 'rbFinance',  20),
            CBoolCol(     u'Является государственным',['isState'], 10)
            ], 'StockPurchaseContract' )


    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        return CTableModel.data(self, index, role)


class CSmnnTableCol(CTextCol):
    def __init__(self, title, fields, defaultWidth, alignment='l'):
        CTextCol.__init__(self, title, fields, defaultWidth, alignment)
        self.smnnCaches = {}


    def format(self, values):
        name = u''
        smnnUUID = forceStringEx(values[0])
        if smnnUUID:
            name = self.smnnCaches.get(smnnUUID, u'')
            if not name:
                db = QtGui.qApp.db
                table = db.table('esklp.Smnn')
                record = db.getRecordEx(table, [table['code'], table['mnn'], table['form']], [table['UUID'].eq(smnnUUID)])
                if record:
                    name = forceStringEx(record.value('mnn'))
                    self.smnnCaches[smnnUUID] = name
        return toVariant(name)


    def invalidateRecordsCache(self):
        self.smnnCaches = {}

class CPurchaseContractItemsModel(CTableModel):
    class CDateCol(CCol):
        def __init__(self, title, fields, defaultWidth, alignment='l'):
            CCol.__init__(self, title, fields, defaultWidth, alignment)
            self.date = None

        def format(self, values):
            record = values[1]
            comparisonDate = forceDateTime(record.value('comparisonDate'))
            if comparisonDate:
                return QVariant(comparisonDate)
            else:
                return CCol.invalid

        def invalidateRecordsCache(self):
            self.data = None


    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self.addColumn(CPurchaseContractItemsModel.CDateCol( u'Дата и время сопоставления',  ['master_id'],   20))
        self.addColumn(CSmnnTableCol(u'МНН',         ['smnnUUID'], 20))
        self.addColumn(CRefBookCol(u'Форма выпуска', ['lfForm_id'], 'rbLfForm', 20))
        self.addColumn(CRefBookCol(u'ЛСиИМН',        ['nomenclature_id'],  'rbNomenclature',  20))
        #self.addColumn(CTextCol(   u'Серия',         ['batch'], 20))
        self.addColumn(CDateCol(   u'Годен до',      ['shelfTime'],   20))
        self.addColumn(CTextCol(   u'Кол-во',        ['qnt'], 20))
        self.addColumn(CRefBookCol(u'Ед.Учета',      ['unit_id'], 'rbUnit', 20))
        self.addColumn(CSumCol(    u'Сумма',         ['sum'], 20))
        self.loadField('comparisonDate')
        self.setTable('StockPurchaseContract_Item')


#
# ##############################################################################
#
