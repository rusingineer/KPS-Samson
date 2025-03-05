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

from PyQt4 import QtGui, QtSql
from PyQt4.QtCore import Qt, pyqtSignature, QDate, QDateTime, QVariant, SIGNAL

from library.crbcombobox         import CRBComboBox
from library.InDocTable          import (
                                         CInDocTableModel,
                                         CDateInDocTableCol,
                                         CDateTimeInDocTableCol,
                                         CFloatInDocTableCol,
                                         CInDocTableCol,
                                         CRBInDocTableCol,
                                        )
from library.ItemsListDialog     import CItemEditorBaseDialog
from library.interchange         import (
                                         getComboBoxValue,
                                         setComboBoxValue,
                                         getRBComboBoxValue,
                                         setRBComboBoxValue,
                                         getLineEditValue,
                                         setLineEditValue,
                                         setCheckBoxValue,
                                         getCheckBoxValue,
                                         setDateEditValue,
                                         getDateEditValue,
                                        )
from library.PrintInfo           import CInfoContext
from library.PrintTemplates      import (
                                         applyTemplate,
                                         CPrintAction,
                                         CPrintButton,
                                         getPrintTemplates,
                                        )
from library.Utils               import forceDouble, forceRef, forceInt, forceString, forceStringEx, forceDateTime, forceBool, toVariant, forceDate, pyDate
from library.Counter             import CCounterController
from Reports.ReportBase          import CReportBase, createTable
from Reports.ReportView          import CReportViewDialog
from Stock.NomenclatureComboBox  import CNomenclatureInDocTableCol
from Stock.StockModel            import CStockMotionType
from Stock.Utils                 import (
                                         getStockMotionItemQuantityColumn,
                                         getBatchShelfTimeFinance,
                                         CSummaryInfoModelMixin,
                                        )
from Events.Utils                import getLfFormIdList, getNomenclatureSmnnToLfFormIdList, getNomenclatureSmnnNotLfFormIdList, getNomenclatureIdSmnnLfFormIdList
from RefBooks.Nomenclature.List  import CRBNomenclatureEditor
from Orgs.Orgs                   import selectOrganisation
from RefBooks.ActionTypeGroup.RBActionTypeGroupEditor import CSmnnInDocTableCol, CLfFormInDocTableCol
from library.ESKLP.SmnnGrlsLfNomenclatureExpenseEditorEx import CSmnnGrlsLfNomenclatureExpenseEditorEx
from Users.Rights              import urEditChkOnlyExistsNomenclature

from Stock.Ui_PurchaseContractDialog import Ui_PurchaseContractDialog


class CPurchaseContractEditDialog(Ui_PurchaseContractDialog, CItemEditorBaseDialog):
    purchaseDocumentType = 0  # Контракт на закупку

    def __init__(self,  parent):
        CItemEditorBaseDialog.__init__(self, parent, 'StockPurchaseContract')
        self.addModels('Items', CItemsModel(self))
        self.addModels('AdditionallyAgreement', CAdditionallyAgreementModel(self))
        self.addObject('btnPrint', CPrintButton(self, u'Печать'))
        self.addObject('btnComparison', QtGui.QPushButton(u'Сопоставить', self))
        self.addObject('actOpenNomenclatureEditor', QtGui.QAction(u'Редактировать', self))
        self.setupUi(self)
        self.setModels(self.tblItems, self.modelItems, self.selectionModelItems)
        self.tblAdditionallyAgreement.setModel(self.modelAdditionallyAgreement)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setupDirtyCather()
        self.tblItems.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.tblItems.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.tblItems.addPopupAction(self.actOpenNomenclatureEditor)
        self.tblItems.addPopupDelRow()
        self.tblAdditionallyAgreement.addPopupDelRow()
        self.isComparisonPressed = False
        self.cmbFinance.setTable('rbFinance', addNone=True)
        self.cmbFinanceSource.setTable('rbFinanceSource', addNone=True)
        self.cmbSupplierOrg.setFilter('isSupplier = 1')
        self.btnPrint.setShortcut('F6')
        self.buttonBox.addButton(self.btnPrint, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnComparison, QtGui.QDialogButtonBox.ActionRole)
        templates = getPrintTemplates(self.getStockContext())
        if not templates:
            self.btnPrint.setId(-1)
        else:
            for template in templates:
                action = CPrintAction(template.name, template.id, self.btnPrint, self.btnPrint)
                self.btnPrint.addAction(action)
            self.btnPrint.menu().addSeparator()
            self.btnPrint.addAction(CPrintAction(u'Напечатать список', -1, self.btnPrint, self.btnPrint))
        self.tblItems.enableColsMove()
        self.btnComparison.setEnabled(False)
        self.cmbContractType.setItems()

    def _checkStockMotionItemsData(self, tblItems):
        model = tblItems.model()
        items = model.items()
        for idx, item in enumerate(items):
            qnt = forceDouble(item.value('qnt'))
            if qnt <= 0:
                return self.checkValueMessage(
                    u'Количество должно быть больше нуля!', False, tblItems, idx, model.getColIndex('qnt')
                )
        return True


    def resetCounterNumber(self):
        return False


    def exec_(self):
        counterController = QtGui.qApp.counterController()
        if not counterController:
            QtGui.qApp.setCounterController(CCounterController(self))
        result = None
        try:
            result = CItemEditorBaseDialog.exec_(self)
        finally:
            if not counterController:
                if result:
                    QtGui.qApp.delAllCounterValueIdReservation()
                else:
                    QtGui.qApp.resetAllCounterValueIdReservation()
            elif self.resetCounterNumber() and counterController.lastReservationId:
                QtGui.qApp.resetCounterValueIdReservation(counterController.lastReservationId)
        if not counterController:
            QtGui.qApp.setCounterController(None)
        return result


    def getStockContext(self):
        return ['PurchaseContract']


    @pyqtSignature('int')
    def on_cmbFinance_currentIndexChanged(self, index):
        financeId = self.cmbFinance.value()
        if financeId:
            self.cmbFinanceSource.setFilter('master_id = %d' % financeId)
        else:
            self.cmbFinanceSource.setFilter('')


    @pyqtSignature('int')
    def on_btnPrint_printByTemplate(self, templateId):
        self.actPrintPurchaseContract(templateId)


    @pyqtSignature('')
    def on_btnSelectOrganisation_clicked(self):
        orgValueId = self.cmbSupplierOrg.value() or None
        orgId = selectOrganisation(self, None, True, params={'isActive': 2, 'isSupplier': 2, 'itemId': orgValueId}, forSelect=True)
        self.cmbSupplierOrg.model().update()
        if orgId:
            self.cmbSupplierOrg.setValue(orgId or orgValueId)


    @pyqtSignature('')
    def on_actOpenNomenclatureEditor_triggered(self):
        items = self.tblItems.getSelectedItems()
        if len(items) == 0:
            return
        nomenclatureId = forceInt(items[0].value('nomenclature_id'))
        record = QtGui.qApp.db.getRecord('rbNomenclature', '*', nomenclatureId)
        dialog = CRBNomenclatureEditor(self)
        dialog.setRecord(record)
        dialog.exec_()


    def actPrintPurchaseContract(self, templateId):
        from Stock.StockMotionInfo import CStockPurchaseContractInfo, CStockPurchaseContractItemInfoList, CStockPCAdditionallyAgreementInfoList
        if templateId == -1:
            self.getNomenclaturePrint()
        else:
            purchaseContractId = self.itemId()
            if purchaseContractId:
                context = CInfoContext()
                data = { 'purchaseContract':CStockPurchaseContractInfo(context, purchaseContractId), # Контракт на закупку
                         'purchaseContractList': CStockPurchaseContractItemInfoList(context, purchaseContractId), # Спецификация
                         'purchaseContractAAList': CStockPCAdditionallyAgreementInfoList(context, purchaseContractId) # Доп. соглашения
                        }
                QtGui.qApp.call(self, applyTemplate, (self, templateId, data))


    def dumpParams(self, cursor):
        db = QtGui.qApp.db
        description = []
        number = self.edtNumber.text()
        if number:
            description.append(u'Номер %s'%forceString(number))
        date = QDate(self.edtDate.date())
        if date:
           description.append(u'Дата %s'%forceString(date))
        name = self.edtName.text()
        if name:
            description.append(u'Наименование %s'%forceString(name))
        title = self.edtTitle.text()
        if title:
            description.append(u'Наименование для печати %s'%forceString(title))
        supplierId = self.cmbSupplierOrg.value()
        if supplierId:
            description.append(u'Поставщик %s'%forceString(db.translate('Organisation', 'id', supplierId, 'fullName')))
        begDate = self.edtBegDate.date()
        endDate = self.edtEndDate.date()
        if begDate or endDate:
           description.append(u'Период действия с %s по %s'%(forceString(begDate), forceString(endDate)))
        financeId = self.cmbFinance.value()
        if financeId:
            description.append(u'Тип финансирования %s'%forceString(db.translate('rbFinance', 'id', financeId, 'name')))
        description.append(u'Является государственным' if self.chkState.isChecked() else u'Не является государственным')
        description.append(u'Порядок подтверждения %s'%([u'не определено', u'прямой', u'обратный'][self.cmbConfirmationOrder.currentIndex()]))
        description.append(u'отчёт составлен: ' + forceString(QDateTime.currentDateTime()))
        columns = [ ('100%', [], CReportBase.AlignLeft) ]
        table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
        for i, row in enumerate(description):
            table.setText(i, 0, row)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()


    def getNomenclaturePrint(self):
        model = self.tblItems.model()
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.windowTitle())
        self.dumpParams(cursor)
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportSubTitle)
        cursor.insertText(u'Спецификация')
        cursor.setCharFormat(CReportBase.ReportBody)
        colWidths  = [ self.tblItems.columnWidth(i) for i in xrange(model.columnCount()-1) ]
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
        for iModelRow in xrange(model.rowCount()-1):
            iTableRow = table.addRow()
            table.setText(iTableRow, 0, iModelRow+1)
            for iModelCol in xrange(model.columnCount()):
                index = model.createIndex(iModelRow, iModelCol)
                text = forceString(model.data(index))
                table.setText(iTableRow, iModelCol+1, text)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertBlock()
        modelAA = self.modelAdditionallyAgreement
        cursor.setCharFormat(CReportBase.ReportSubTitle)
        cursor.insertText(u'Доп. соглашения')
        cursor.setCharFormat(CReportBase.ReportBody)
        colWidths  = [ self.tblItems.columnWidth(i) for i in xrange(modelAA.columnCount()-1) ]
        colWidths.insert(0,10)
        totalWidth = sum(colWidths)
        tableColumns = []
        iColNumber = False
        for iCol, colWidth in enumerate(colWidths):
            widthInPercents = str(max(1, colWidth*90/totalWidth))+'%'
            if iColNumber == False:
                tableColumns.append((widthInPercents, [u'№'], CReportBase.AlignRight))
                iColNumber = True
            tableColumns.append((widthInPercents, [forceString(modelAA._cols[iCol].title())], CReportBase.AlignLeft))
        table = createTable(cursor, tableColumns)
        for iModelRow in xrange(modelAA.rowCount()-1):
            iTableRow = table.addRow()
            table.setText(iTableRow, 0, iModelRow+1)
            for iModelCol in xrange(modelAA.columnCount()):
                index = modelAA.createIndex(iModelRow, iModelCol)
                text = forceString(modelAA.data(index))
                table.setText(iTableRow, iModelCol+1, text)
        cursor.movePosition(QtGui.QTextCursor.End)
        html = doc.toHtml('utf-8')
        view = CReportViewDialog(self)
        view.setText(html)
        view.exec_()

    def setRecord(self, record):
        self.btnComparison.setEnabled(False)
        CItemEditorBaseDialog.setRecord(self, record)
        setLineEditValue(  self.edtNumber,            record, 'number')
        setDateEditValue(  self.edtDate,              record, 'date')
        setLineEditValue(  self.edtName,              record, 'name')
        setLineEditValue(  self.edtTitle,             record, 'title')
        setRBComboBoxValue(self.cmbSupplierOrg,       record, 'supplierOrg_id')
        setDateEditValue(  self.edtBegDate,           record, 'begDate')
        setDateEditValue(  self.edtEndDate,           record, 'endDate')
        setRBComboBoxValue(self.cmbFinance,           record, 'finance_id')
        setRBComboBoxValue(self.cmbFinanceSource,     record, 'financeSource_id')
        setCheckBoxValue(  self.chkState,             record, 'isState')
        setComboBoxValue(  self.cmbConfirmationOrder, record, 'confirmationOrder')
        setComboBoxValue(  self.cmbContractType,      record, 'contractType')
        self.modelItems.loadItems(self.itemId())
        self.modelAdditionallyAgreement.loadItems(self.itemId())
        if len(self.modelItems._items) > 0:
            self.tblItems.setCurrentIndex(self.modelItems.index(0, 0))
        smnnUUID, lfFormId = self.getCurrentSmnnUUIDLfFormId()
        self.lblSummaryInfo.setText(self.modelItems.getSummaryInfo(smnnUUID, lfFormId))
        self.btnComparison.setEnabled(self.isBtnComparisonEnabled())


    def getRecord(self):
        record = CItemEditorBaseDialog.getRecord(self)
        getLineEditValue(  self.edtNumber,            record, 'number')
        getDateEditValue(  self.edtDate,              record, 'date')
        getLineEditValue(  self.edtName,              record, 'name')
        getLineEditValue(  self.edtTitle,             record, 'title')
        getRBComboBoxValue(self.cmbSupplierOrg,       record, 'supplierOrg_id')
        getDateEditValue(  self.edtBegDate,           record, 'begDate')
        getDateEditValue(  self.edtEndDate,           record, 'endDate')
        getRBComboBoxValue(self.cmbFinance,           record, 'finance_id')
        getRBComboBoxValue(self.cmbFinanceSource,     record, 'financeSource_id')
        getCheckBoxValue(  self.chkState,             record, 'isState')
        getComboBoxValue(  self.cmbConfirmationOrder, record, 'confirmationOrder')
        getComboBoxValue(  self.cmbContractType,      record, 'contractType')
        record.setValue('type', self.purchaseDocumentType)
        return record


    def saveInternals(self, id):
        self.modelItems.saveItems(id)
        self.modelAdditionallyAgreement.saveItems(id)


    def checkDataEntered(self):
        result = self._checkStockMotionItemsData(self.tblItems)
        return result


    def isBtnComparisonEnabled(self):
        if bool(self.cmbSupplierOrg.value() or self.itemId()):
            items = self.modelItems._items
            for item in items:
                smnnUUID = forceStringEx(item.value('smnnUUID'))
                lfFormId = forceRef(item.value('lfForm_id'))
                nomenclatureId = forceRef(item.value('nomenclature_id'))
                if smnnUUID and lfFormId and not nomenclatureId:
                    return True
        return False

    @pyqtSignature('int')
    def on_cmbSupplierOrg_currentIndexChanged(self, val):
        supplierOrgId = self.cmbSupplierOrg.value()
        supplierOrgExists = bool(supplierOrgId)
        self.modelItems.updateBatchShelfTimeFinance = not supplierOrgExists
        self.btnComparison.setEnabled(self.isBtnComparisonEnabled())

    def getCurrentSmnnUUIDLfFormId(self):
        smnnUUID = u''
        lfFormId = None
        rows = self.tblItems.getSelectedRows()
        if len(rows) == 1:
            currentIndex = self.tblItems.currentIndex()
            if currentIndex.isValid():
                currentRow = currentIndex.row()
                if currentRow >= 0 and currentRow not in rows:
                    rows.append(currentRow)
                if len(rows) == 1 and 0 <= currentRow < len(self.modelItems._items):
                    item = self.modelItems._items[currentRow]
                    if item:
                        smnnUUID = forceStringEx(item.value('smnnUUID'))
                        lfFormId = forceRef(item.value('lfForm_id'))
        return smnnUUID, lfFormId


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_modelItems_dataChanged(self,  topLeftIndex, bottomRightIndex):
        smnnUUID, lfFormId = self.getCurrentSmnnUUIDLfFormId()
        self.lblSummaryInfo.setText(self.modelItems.getSummaryInfo(smnnUUID, lfFormId))


    @pyqtSignature('QItemSelection, QItemSelection')
    def on_selectionModelItems_selectionChanged(self, selected, deselected):
        smnnUUID, lfFormId = self.getCurrentSmnnUUIDLfFormId()
        self.lblSummaryInfo.setText(self.modelItems.getSummaryInfo(smnnUUID, lfFormId))


    @pyqtSignature('QModelIndex')
    def on_tblItems_doubleClicked(self, index):
        if index and index.isValid():
            col = index.column()
            if col in (self.modelItems.SMNN_Column, self.modelItems.SMNN_GRLSLF_Column):
                currentRow = index.row()
                dialog = CSmnnGrlsLfNomenclatureExpenseEditorEx(self)
                try:
                    dialog.setBegDate(self.edtBegDate.date())
                    dialog.setEndDate(self.edtEndDate.date())
                    dialog.setIsType(1 if col == self.modelItems.SMNN_GRLSLF_Column else 0)
                    dialog.setOnlySmnnUUID(True)
                    dialog.setOnlyExists(False)
                    nomenclatureId = None
                    smnnUUID = None
                    dialog.setOrgStructureId(QtGui.qApp.currentOrgStructureId())
                    item = None
                    if 0 <= currentRow < len(self.modelItems._items):
                        item = self.modelItems._items[currentRow]
                    if item:
                        nomenclatureId = forceRef(item.value('nomenclature_id'))
                        smnnUUID = forceStringEx(item.value('smnnUUID'))
                        lfFormId = forceRef(item.value('lfForm_id'))
                        dialog.setUUID(smnnUUID)
                        dialog.setLfFormId(lfFormId)
                    dialog.setNomenclatureId(nomenclatureId)
                    if QtGui.qApp.controlSMFinance() in (1, 2):
                        dialog.setFinanceId(self.cmbFinance.value())
                    dialog.setNomenclatureSmnnUUID(smnnUUID)
                    if not QtGui.qApp.userHasRight(urEditChkOnlyExistsNomenclature):
                        dialog.setOnlyExistsEnabled(False)
                    dialog.on_buttonBox_apply()
                    if dialog.exec_():
                        UUID, lfFormId = dialog.getValue()
                        if UUID:
                            if currentRow == len(self.modelItems._items):
                                item = None
                                self.modelItems._addEmptyItem()
                                item = self.modelItems._items[currentRow]
                                if 0 <= currentRow < len(self.modelItems._items):
                                    item = self.modelItems._items[currentRow]
                            if item:
                                item.setValue('smnnUUID', toVariant(UUID))
                                item.setValue('lfForm_id', toVariant(lfFormId))
#                                if not nomenclatureId:
#                                    nomenclatureSmnnIdList = getNomenclatureSmnnToLfFormIdList(UUID, [lfFormId])
#                                    if len(nomenclatureSmnnIdList) == 1:
#                                        nomenclatureSmnnId = forceRef(nomenclatureSmnnIdList[0])
#                                        if nomenclatureSmnnId:
#                                            unitId = self.modelItems.getDefaultStockUnitId(nomenclatureSmnnId)
#                                            item.setValue('unit_id', toVariant(unitId))
                                self.modelItems.emitRowChanged(currentRow)
                finally:
                    dialog.deleteLater()
            else:
                self.emit(SIGNAL('doubleClicked(QModelIndex)'), index)


    @pyqtSignature('')
    def on_btnComparison_pressed(self):
        self.isComparisonPressed = True
        self.btnComparison.setEnabled(not self.isComparisonPressed)
#        supplierOrgId = self.cmbSupplierOrg.value()
        purchaseContractId = self.itemId()
        if not purchaseContractId:
            return
#        if not supplierOrgId:
#            return
        model = self.tblItems.model()
        items = model.items()
        db = QtGui.qApp.db
        tableStockMotion = db.table('StockMotion')
        tableStockMotionItem = db.table('StockMotion_Item')
        queryTable = tableStockMotion.innerJoin(tableStockMotionItem, tableStockMotionItem['master_id'].eq(tableStockMotion['id']))
        cols = [tableStockMotion['date'],
                tableStockMotionItem['nomenclature_id'],
                tableStockMotionItem['batch'],
                tableStockMotionItem['shelfTime'],
                tableStockMotionItem['unit_id'],
                tableStockMotionItem['price'],
                u'SUM(StockMotion_Item.qnt) AS qntSUM',
                u'SUM(StockMotion_Item.sum) AS sumSUM'
                ]
        group = [tableStockMotionItem['nomenclature_id'].name(),
                 tableStockMotionItem['batch'].name(),
                 tableStockMotionItem['shelfTime'].name(),
                 tableStockMotionItem['unit_id'].name(),
                 tableStockMotionItem['price'].name(),
                 tableStockMotion['date'].name(),
                 ]
        order = [tableStockMotion['date'].name(),
                 tableStockMotionItem['nomenclature_id'].name(),
                 tableStockMotionItem['batch'].name(),
                 tableStockMotionItem['shelfTime'].name(),
                 tableStockMotionItem['unit_id'].name(),
                 tableStockMotionItem['price'].name(),
                 ]
        nomenclatureSmnnToLfFormList = {}
        nomenclatureIdSmnnToLfFormList = {}
        nomenclatureSmnnToLfFormRecords = {}
        nomenclatureSmnnNotLfFormRecords = {}
        nomenclatureSmnnNotLfFormList = {}
        stockMotionRecords = []
        nomenclatureSmnnIdListEx = []
        nomenclatureSmnnIdNotListEx = []
        nomenclaturePCIdList = []
        for idx, item in enumerate(items):
            nomenclatureId = forceRef(item.value('nomenclature_id'))
            comparisonDate = forceDateTime(item.value('comparisonDate'))
            shelfTime = pyDate(forceDate(item.value('shelfTime')))
            price = forceDouble(item.value('price'))
            unitId = forceRef(item.value('unit_id'))
            if not nomenclatureId and not comparisonDate:
                smnnUUID = forceStringEx(item.value('smnnUUID'))
                lfFormId = forceRef(item.value('lfForm_id'))
                if smnnUUID and lfFormId:
                    nomenclatureSmnnToLfFormRecords[(smnnUUID, lfFormId)] = item
                    nomenclatureSmnnIdList = nomenclatureSmnnToLfFormList.get((smnnUUID, lfFormId), [])
                    if not nomenclatureSmnnIdList:
                        nomenclatureSmnnIdList = getNomenclatureSmnnToLfFormIdList(smnnUUID, [lfFormId])
                        if nomenclatureSmnnIdList:
                            nomenclatureSmnnToLfFormList[(smnnUUID, lfFormId)] = nomenclatureSmnnIdList
                            for nomenclatureSmnnToLfFormId in nomenclatureSmnnIdList:
                                nomenclatureIdSmnnToLfFormList[nomenclatureSmnnToLfFormId] = (smnnUUID, lfFormId)
                    if nomenclatureSmnnIdList:
                        nomenclatureSmnnIdListEx = list(set(nomenclatureSmnnIdListEx)|set(nomenclatureSmnnIdList))
                if smnnUUID:
                    nomenclatureSmnnNotLfFormRecords[smnnUUID] = item
                    nomenclatureSmnnIdNotList = nomenclatureSmnnNotLfFormList.get(smnnUUID, [])
                    if not nomenclatureSmnnIdNotList:
                        nomenclatureSmnnIdNotList = getNomenclatureSmnnNotLfFormIdList(smnnUUID)
                        if nomenclatureSmnnIdNotList:
                            nomenclatureSmnnNotLfFormList[smnnUUID] = nomenclatureSmnnIdNotList
                            for nomenclatureSmnnNotLfFormId in nomenclatureSmnnIdNotList:
                                nomenclatureSmnnIdNotList[nomenclatureSmnnNotLfFormId] = smnnUUID
                    if nomenclatureSmnnIdNotList:
                        nomenclatureSmnnIdNotListEx = list(set(nomenclatureSmnnIdNotListEx)|set(nomenclatureSmnnIdNotList))
                        if nomenclatureSmnnIdListEx:
                            nomenclatureSmnnIdNotListEx = list(set(nomenclatureSmnnIdNotListEx)-set(nomenclatureSmnnIdListEx))
            elif nomenclatureId and (nomenclatureId, shelfTime, price) not in nomenclaturePCIdList:
                nomenclaturePCIdList.append((nomenclatureId, shelfTime, price, unitId))
        if nomenclatureSmnnIdListEx:
            cond = [tableStockMotion['type'].eq(CStockMotionType.incomingInvoice),
                    tableStockMotionItem['nomenclature_id'].inlist(nomenclatureSmnnIdListEx),
                    tableStockMotionItem['nomenclature_id'].isNotNull(),
                    tableStockMotion['deleted'].eq(0),
                    tableStockMotionItem['deleted'].eq(0)
                    ]
            if purchaseContractId:
                cond.append(tableStockMotion['reason_id'].eq(purchaseContractId))
#            if supplierOrgId:
#                cond.append(tableStockMotion['supplierOrg_id'].eq(supplierOrgId))
            stockMotionRecords = db.getRecordListGroupBy(queryTable, cols, cond, group, order)

        for record in stockMotionRecords:
            nomenclatureSMId = forceRef(record.value('nomenclature_id'))
            if nomenclatureSMId:
                newSmnnUUID, newLfFormId = nomenclatureIdSmnnToLfFormList.get(nomenclatureSMId, ('', None))
                shelfTime = pyDate(forceDate(record.value('shelfTime')))
                price = forceDouble(record.value('price'))
                unitId = forceRef(record.value('unit_id'))
                if (nomenclatureSMId, shelfTime, price, unitId) not in nomenclaturePCIdList:
                    myItem = self.modelItems.getEmptyRecord()
                    myItem.setValue('comparisonDate',  toVariant(QDateTime.currentDateTime()))
                    myItem.setValue('nomenclature_id', toVariant(nomenclatureSMId))
                    myItem.setValue('smnnUUID',        toVariant(newSmnnUUID))
                    myItem.setValue('lfForm_id',       toVariant(newLfFormId))
                    myItem.setValue('unit_id',         record.value('unit_id'))
                    #myItem.setValue('batch',           record.value('batch'))
                    myItem.setValue('shelfTime',       record.value('shelfTime'))
                    myItem.setValue('qnt',             record.value('qntSUM'))
                    myItem.setValue('price',           record.value('price'))
                    myItem.setValue('sum',             record.value('sumSUM'))
                    myItem.setValue('isUpdate',        toVariant(1))
                    self.modelItems.items().append(myItem)
                    smnnToLfFormRecord = nomenclatureSmnnToLfFormRecords.get((newSmnnUUID, newLfFormId), None)
                    if smnnToLfFormRecord:
                        smnnToLfFormPrice = forceDouble(smnnToLfFormRecord.value('price'))
                        if smnnToLfFormPrice == price:
                            smnnToLfFormRecord.setValue('qnt', toVariant(forceDouble(smnnToLfFormRecord.value('qnt')) - forceDouble(record.value('qntSUM'))))
                            smnnToLfFormRecord.setValue('sum', toVariant(smnnToLfFormPrice*forceDouble(smnnToLfFormRecord.value('qnt'))))
                            nomenclatureSmnnToLfFormRecords[(newSmnnUUID, newLfFormId)] = smnnToLfFormRecord

        for record in stockMotionRecords:
            nomenclatureSMId = forceRef(record.value('nomenclature_id'))
            if nomenclatureSMId:
                newSmnnUUID, newLfFormId = nomenclatureIdSmnnToLfFormList.get(nomenclatureSMId, ('', None))
                newShelfTime = forceDate(record.value('shelfTime'))
                newPrice = forceDouble(record.value('price'))
                newUnitId = forceRef(record.value('unit_id'))
                for idx, item in enumerate(items):
                    isUpdate = forceBool(item.value('isUpdate'))
                    if not isUpdate:
                        nomenclatureId = forceRef(item.value('nomenclature_id'))
                        comparisonDate = forceDateTime(item.value('comparisonDate'))
                        smnnUUID = forceStringEx(item.value('smnnUUID'))
                        lfFormId = forceRef(item.value('lfForm_id'))
                        shelfTime = forceDate(item.value('shelfTime'))
                        price = forceDouble(item.value('price'))
                        unitId = forceRef(item.value('unit_id'))
                        if newSmnnUUID and newLfFormId and smnnUUID == newSmnnUUID and lfFormId == newLfFormId and (newShelfTime == shelfTime or not shelfTime) and (newPrice == price or not price) and (newUnitId == unitId or not unitId):
                            if comparisonDate and nomenclatureId == nomenclatureSMId and comparisonDate < QDateTime.currentDateTime():
                                date = forceDateTime(record.value('date'))
                                if comparisonDate < date:
                                    item.setValue('comparisonDate',  toVariant(QDateTime.currentDateTime()))
                                    item.setValue('qnt',             toVariant(forceDouble(item.value('qnt')) + forceDouble(record.value('qntSUM'))))
                                    item.setValue('sum',             toVariant(forceDouble(item.value('sum')) + forceDouble(record.value('sumSUM'))))
                                    itemQnt = forceDouble(item.value('qnt'))
                                    item.setValue('price',           toVariant((forceDouble(item.value('sum'))/itemQnt) if itemQnt != 0 else 0))
                                    item.setValue('isUpdate',        toVariant(1))
                                    smnnToLfFormRecord = nomenclatureSmnnToLfFormRecords.get((newSmnnUUID, newLfFormId), None)
                                    if smnnToLfFormRecord:
                                        smnnToLfFormPrice = forceDouble(smnnToLfFormRecord.value('price'))
                                        if smnnToLfFormPrice == price:
                                            smnnToLfFormRecord.setValue('qnt', toVariant(forceDouble(smnnToLfFormRecord.value('qnt')) - forceDouble(record.value('qntSUM'))))
                                            smnnToLfFormRecord.setValue('sum', toVariant(smnnToLfFormPrice*forceDouble(smnnToLfFormRecord.value('qnt'))))
                                            nomenclatureSmnnToLfFormRecords[(newSmnnUUID, newLfFormId)] = smnnToLfFormRecord
        if nomenclatureSmnnIdNotListEx:
            cond = [tableStockMotion['type'].eq(CStockMotionType.incomingInvoice),
                    tableStockMotionItem['nomenclature_id'].inlist(nomenclatureSmnnIdNotListEx),
                    tableStockMotionItem['nomenclature_id'].isNotNull(),
                    tableStockMotion['deleted'].eq(0),
                    tableStockMotionItem['deleted'].eq(0)
                    ]
            if purchaseContractId:
                cond.append(tableStockMotion['reason_id'].eq(purchaseContractId))
#            if supplierOrgId:
#                cond.append(tableStockMotion['supplierOrg_id'].eq(supplierOrgId))
            stockMotionRecords = db.getRecordListGroupBy(queryTable, cols, cond, group, order)

        for record in stockMotionRecords:
            nomenclatureSMId = forceRef(record.value('nomenclature_id'))
            if nomenclatureSMId:
                newSmnnUUIDLfFormId, newLfFormId = nomenclatureIdSmnnToLfFormList.get(nomenclatureSMId, ('', None))
                if newSmnnUUIDLfFormId and not newLfFormId:
                    newSmnnUUID = nomenclatureSmnnNotLfFormList.get(nomenclatureSMId, '')
                    shelfTime = pyDate(forceDate(record.value('shelfTime')))
                    price = forceDouble(record.value('price'))
                    unitId = forceRef(record.value('unit_id'))
                    if (nomenclatureSMId, shelfTime, price, unitId) not in nomenclaturePCIdList:
                        myItem = self.modelItems.getEmptyRecord()
                        myItem.setValue('comparisonDate',  toVariant(QDateTime.currentDateTime()))
                        myItem.setValue('nomenclature_id', toVariant(nomenclatureSMId))
                        myItem.setValue('smnnUUID',        toVariant(newSmnnUUID))
                        myItem.setValue('unit_id',         record.value('unit_id'))
                        #myItem.setValue('batch',           record.value('batch'))
                        myItem.setValue('shelfTime',       record.value('shelfTime'))
                        myItem.setValue('qnt',             record.value('qntSUM'))
                        myItem.setValue('price',           record.value('price'))
                        myItem.setValue('sum',             record.value('sumSUM'))
                        myItem.setValue('isUpdate',        toVariant(1))
                        self.modelItems.items().append(myItem)
                        smnnToLfFormRecord = nomenclatureSmnnNotLfFormRecords.get(newSmnnUUID, None)
                        if smnnToLfFormRecord:
                            smnnToLfFormPrice = forceDouble(smnnToLfFormRecord.value('price'))
                            if smnnToLfFormPrice == price:
                                smnnToLfFormRecord.setValue('qnt', toVariant(forceDouble(smnnToLfFormRecord.value('qnt')) - forceDouble(record.value('qntSUM'))))
                                smnnToLfFormRecord.setValue('sum', toVariant(smnnToLfFormPrice*forceDouble(smnnToLfFormRecord.value('qnt'))))
                                nomenclatureSmnnNotLfFormRecords[newSmnnUUID] = smnnToLfFormRecord

        for record in stockMotionRecords:
            nomenclatureSMId = forceRef(record.value('nomenclature_id'))
            if nomenclatureSMId:
                newSmnnUUIDLfFormId, newLfFormId = nomenclatureIdSmnnToLfFormList.get(nomenclatureSMId, ('', None))
                if newSmnnUUIDLfFormId and not newLfFormId:
                    newSmnnUUID = nomenclatureSmnnNotLfFormList.get(nomenclatureSMId, '')
                    newShelfTime = forceDate(record.value('shelfTime'))
                    newPrice = forceDouble(record.value('price'))
                    newUnitId = forceRef(record.value('unit_id'))
                    for idx, item in enumerate(items):
                        isUpdate = forceBool(item.value('isUpdate'))
                        if not isUpdate:
                            nomenclatureId = forceRef(item.value('nomenclature_id'))
                            comparisonDate = forceDateTime(item.value('comparisonDate'))
                            smnnUUID = forceStringEx(item.value('smnnUUID'))
                            lfFormId = forceRef(item.value('lfForm_id'))
                            shelfTime = forceDate(item.value('shelfTime'))
                            price = forceDouble(item.value('price'))
                            unitId = forceRef(item.value('unit_id'))
                            if newSmnnUUID and smnnUUID == newSmnnUUID and (newShelfTime == shelfTime or not shelfTime) and (newPrice == price or not price) and (newUnitId == unitId or not unitId):
                                if comparisonDate and nomenclatureId == nomenclatureSMId and comparisonDate < QDateTime.currentDateTime():
                                    date = forceDateTime(record.value('date'))
                                    if comparisonDate < date:
                                        item.setValue('comparisonDate',  toVariant(QDateTime.currentDateTime()))
                                        item.setValue('qnt',             toVariant(forceDouble(item.value('qnt'))+ forceDouble(record.value('qntSUM'))))
                                        item.setValue('sum',             toVariant(forceDouble(item.value('sum'))+ forceDouble(record.value('sumSUM'))))
                                        itemQnt = forceDouble(item.value('qnt'))
                                        item.setValue('price',           toVariant((forceDouble(item.value('sum'))/itemQnt) if itemQnt != 0 else 0))
                                        item.setValue('isUpdate',        toVariant(1))
                                        smnnToLfFormRecord = nomenclatureSmnnNotLfFormRecords.get(newSmnnUUID, None)
                                        if smnnToLfFormRecord:
                                            smnnToLfFormPrice = forceDouble(smnnToLfFormRecord.value('price'))
                                            if smnnToLfFormPrice == price:
                                                smnnToLfFormRecord.setValue('qnt', toVariant(forceDouble(smnnToLfFormRecord.value('qnt')) - forceDouble(record.value('qntSUM'))))
                                                smnnToLfFormRecord.setValue('sum', toVariant(smnnToLfFormPrice*forceDouble(smnnToLfFormRecord.value('qnt'))))
                                                nomenclatureSmnnNotLfFormRecords[newSmnnUUID] = smnnToLfFormRecord

        cond = [tableStockMotion['type'].eq(CStockMotionType.incomingInvoice),
                tableStockMotionItem['nomenclature_id'].isNotNull(),
                tableStockMotion['deleted'].eq(0),
                tableStockMotionItem['deleted'].eq(0)
                ]
        if nomenclatureSmnnIdNotListEx:
            cond.append(tableStockMotionItem['nomenclature_id'].notInlist(nomenclatureSmnnIdNotListEx))
        if nomenclatureSmnnIdListEx:
            cond.append(tableStockMotionItem['nomenclature_id'].notInlist(nomenclatureSmnnIdListEx))
        if purchaseContractId:
            cond.append(tableStockMotion['reason_id'].eq(purchaseContractId))
#        if supplierOrgId:
#            cond.append(tableStockMotion['supplierOrg_id'].eq(supplierOrgId))
        stockMotionRecords = db.getRecordListGroupBy(queryTable, cols, cond, group, order)
        for record in stockMotionRecords:
            nomenclatureSMId = forceRef(record.value('nomenclature_id'))
            if nomenclatureSMId:
                newSmnnUUID = ''
                newLfFormId = None
                if nomenclatureSMId not in nomenclatureIdSmnnToLfFormList.keys():
                    nomenclatureIdSmnnLfFormIdList = getNomenclatureIdSmnnLfFormIdList(nomenclatureSMId)
                    if len(nomenclatureIdSmnnLfFormIdList) > 0:
                        newSmnnUUID, newLfFormId = nomenclatureIdSmnnLfFormIdList[0]
                        nomenclatureIdSmnnToLfFormList[nomenclatureSMId] = (newSmnnUUID, newLfFormId)
                else:
                    newSmnnUUID, newLfFormId = nomenclatureIdSmnnToLfFormList.get(nomenclatureSMId, ('', None))
                shelfTime = pyDate(forceDate(record.value('shelfTime')))
                price = forceDouble(record.value('price'))
                unitId = forceRef(record.value('unit_id'))
                if (nomenclatureSMId, shelfTime, price, unitId) not in nomenclaturePCIdList:
                    myItem = self.modelItems.getEmptyRecord()
                    myItem.setValue('comparisonDate',  toVariant(QDateTime.currentDateTime()))
                    myItem.setValue('nomenclature_id', toVariant(nomenclatureSMId))
                    myItem.setValue('smnnUUID',        toVariant(newSmnnUUID))
                    myItem.setValue('lfForm_id',       toVariant(newLfFormId))
                    myItem.setValue('unit_id',         record.value('unit_id'))
                    #myItem.setValue('batch',           record.value('batch'))
                    myItem.setValue('shelfTime',       record.value('shelfTime'))
                    myItem.setValue('qnt',             record.value('qntSUM'))
                    myItem.setValue('price',           record.value('price'))
                    myItem.setValue('sum',             record.value('sumSUM'))
                    myItem.setValue('isUpdate',        toVariant(1))
                    self.modelItems.items().append(myItem)

        for record in stockMotionRecords:
            nomenclatureSMId = forceRef(record.value('nomenclature_id'))
            if nomenclatureSMId:
                newSmnnUUID = ''
                newLfFormId = None
                newShelfTime = forceDate(record.value('shelfTime'))
                newPrice = forceDouble(record.value('price'))
                newUnitId = forceRef(record.value('unit_id'))
                if nomenclatureSMId not in nomenclatureIdSmnnToLfFormList.keys():
                    nomenclatureIdSmnnLfFormIdList = getNomenclatureIdSmnnLfFormIdList(nomenclatureSMId)
                    if len(nomenclatureIdSmnnLfFormIdList) > 0:
                        newSmnnUUID, newLfFormId = nomenclatureIdSmnnLfFormIdList[0]
                        nomenclatureIdSmnnToLfFormList[nomenclatureSMId] = (newSmnnUUID, newLfFormId)
                else:
                    newSmnnUUID, newLfFormId = nomenclatureIdSmnnToLfFormList.get(nomenclatureSMId, ('', None))
                for idx, item in enumerate(items):
                    isUpdate = forceBool(item.value('isUpdate'))
                    if not isUpdate:
                        nomenclatureId = forceRef(item.value('nomenclature_id'))
                        comparisonDate = forceDateTime(item.value('comparisonDate'))
                        shelfTime = forceDate(item.value('shelfTime'))
                        price = forceDouble(item.value('price'))
                        unitId = forceRef(item.value('unit_id'))
                        if comparisonDate and nomenclatureId == nomenclatureSMId and comparisonDate < QDateTime.currentDateTime() and (newShelfTime == shelfTime or not shelfTime) and (newPrice == price or not price) and (newUnitId == unitId or not unitId):
                            date = forceDateTime(record.value('date'))
                            if comparisonDate < date:
                                item.setValue('comparisonDate',  toVariant(QDateTime.currentDateTime()))
                                item.setValue('qnt',             toVariant(forceDouble(item.value('qnt'))+ forceDouble(record.value('qntSUM'))))
                                item.setValue('sum',             toVariant(forceDouble(item.value('sum'))+ forceDouble(record.value('sumSUM'))))
                                itemQnt = forceDouble(item.value('qnt'))
                                item.setValue('price',           toVariant((forceDouble(item.value('sum'))/itemQnt) if itemQnt != 0 else 0))
                                item.setValue('isUpdate',        toVariant(1))
        self.modelItems.reset()


class CAdditionallyAgreementModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'StockPurchaseContract_AdditionallyAgreement', 'id', 'master_id', parent)
        self.addCol(CInDocTableCol(     u'Номер',      'number', 16))
        self.addCol(CDateInDocTableCol( u'Дата',       'date',   12))
        self.addCol(CInDocTableCol(     u'Примечание', 'note',   10))


class CItemsModel(CInDocTableModel, CSummaryInfoModelMixin):
    SMNN_Column = 1
    SMNN_GRLSLF_Column = 2

    class CPriceCol(CFloatInDocTableCol):
        def toString(self, value, record):
            qnt = forceDouble(record.value('qnt'))
            if qnt:
                sum = forceDouble(record.value('sum'))
                price = toVariant(self._toString(toVariant(sum/qnt)))
                record.setValue('price', price)
                return price
            record.setValue('price', QVariant(forceDouble(0)))
            return QVariant()

        def setEditorData(self, editor, value, record):
            price = forceDouble(record.value('price'))
            if price:
                s = self._toString(toVariant(price))
            else:
                s = ''
            editor.setText('' if s is None else s)
            editor.selectAll()

    class CSumCol(CFloatInDocTableCol):
        def _toString(self, value):
            if value.isNull():
                return None
            return format(forceDouble(value), '.2f')

    class CLocLfFormInDocTableCol(CLfFormInDocTableCol):
        def __init__(self, title, fieldName, width, tableName, **params):
            CRBInDocTableCol.__init__(self, title, fieldName, width, tableName, **params)
            self.cacheText = {}

        def toString(self, val, record):
            lfFormId = forceRef(val)
            text = self.cacheText.get(lfFormId, '')
            if lfFormId and not text:
                db = QtGui.qApp.db
                tableLfForm= db.table('rbLfForm')
                record = db.getRecordEx(tableLfForm, [tableLfForm['id'], tableLfForm['name'], tableLfForm['dosage']], [tableLfForm['id'].eq(lfFormId), tableLfForm['isESKLP'].eq(1)])
                if record:
                    id = forceRef(record.value('id'))
                    name = forceStringEx(record.value('name'))
                    dosage = forceStringEx(record.value('dosage'))
                    text = name + u' ' + dosage
                    self.cacheText[id] = text
            return toVariant(text)

    class CLocNomenclatureCol(CNomenclatureInDocTableCol):
        def __init__(self, title, fieldName, width, **params):
            CNomenclatureInDocTableCol.__init__(self, title, fieldName, width, **params)

        def createEditor(self, parent):
            editor = CNomenclatureInDocTableCol.createEditor(self, parent)
            editor.setOnlySmnn(True)
            editor.setOnlyNomenclature(True)
            return editor

        def setEditorData(self, editor, value, record):
            smnnGrlsLfId = forceRef(record.value('lfForm_id'))
            smnnUUID = forceStringEx(record.value('smnnUUID'))
            editor.setNomenclatureSmnnUUID(smnnUUID)
            editor.setLfFormId(smnnGrlsLfId)
            editor.setValue(forceRef(value))

    def __init__(self, parent, showExists=False):
        CInDocTableModel.__init__(self, 'StockPurchaseContract_Item', 'id', 'master_id', parent)
        self._nomenclatureColumn = self.CLocNomenclatureCol(u'ЛСиИМН', 'nomenclature_id', 50, showFields = CRBComboBox.showName)
        self._unitColumn = CRBInDocTableCol(u'Ед.Учета', 'unit_id', 12, 'rbUnit', addNone=False)
        self.addCol(CDateTimeInDocTableCol( u'Дата и время сопоставления', 'comparisonDate', 12, canBeEmpty=True).setReadOnly()).setSortable(True)
        self.addCol(CSmnnInDocTableCol(u'МНН', 'smnnUUID', 22).setReadOnly()).setSortable(True)
        self.addCol(self.CLocLfFormInDocTableCol(u'Форма выпуска', 'lfForm_id',  10, 'rbLfForm').setReadOnly()).setSortable(True)
        self.addCol(self._nomenclatureColumn).setSortable(True)
        self.addCol(CDateInDocTableCol( u'Годен до', 'shelfTime', 12, canBeEmpty=True))
        self.addCol(getStockMotionItemQuantityColumn(u'Кол-во', 'qnt', 12))
        self.addCol(self._unitColumn)
        sumCol = CItemsModel.CSumCol( u'Сумма', 'sum', 12)
        self.addCol(sumCol)
        self.addCol(CItemsModel.CPriceCol(u'Цена', 'id', 12, precision=2))
        self.addCol(CInDocTableCol(u'Примечание', 'note',   10))
        self.setExtColsPresent(True)
        self.priceColIndex = len(self.cols())-2
        self.priceCache = parent
        self.qntColumnIndex = self.getColIndex('qnt')
        self.updateBatchShelfTimeFinance = True
        self.addHiddenCol('batch')


    def getSummaryInfo(self, smnnUUID, lfFormId):
        totalQnt = 0.0
        totalSum = 0.0
        cnt = len(self._items)
        for item in self._items:
            totalQnt += forceDouble(item.value('qnt'))
            totalSum += forceDouble(item.value('sum'))
        countTotal = u'Количество позиций: %d, Количество: %.2f, Сумма: %.2f' % (cnt, totalQnt, totalSum)
        totalQnt = 0.0
        totalSum = 0.0
        cnt = 0
        countPosition = u''
        if smnnUUID and lfFormId:
            for item in self._items:
                newSmnnUUID = forceStringEx(item.value('smnnUUID'))
                newLfFormId = forceRef(item.value('lfForm_id'))
                if newSmnnUUID == smnnUUID and lfFormId == newLfFormId:
                    cnt += 1
                    totalQnt += forceDouble(item.value('qnt'))
                    totalSum += forceDouble(item.value('sum'))
            countPosition = u'\nПо МНН и Форме выпуска: Количество позиций: %d, Количество: %.2f, Сумма: %.2f' % (cnt, totalQnt, totalSum)
        return countTotal + (countPosition if countPosition else u'')


    def getNomenclatureNameById(self, nomenclatureId):
        return forceString(self._nomenclatureColumn.toString(nomenclatureId, None))


    def getEmptyRecord(self):
        record = CInDocTableModel.getEmptyRecord(self)
        record.append(QtSql.QSqlField('isUpdate', QVariant.Int))
        record.setValue('isUpdate', toVariant(0))
        record.append(QtSql.QSqlField('price', QVariant.Double))
        record.setValue('price', toVariant(0))
        return record


    def updateSmnn_SmnnGrlslf(self, record, nomenclatureId, oldNomenclatureId):
        if nomenclatureId and nomenclatureId != oldNomenclatureId:
            oldSmnnUUID = forceStringEx(record.value('smnnUUID'))
            db = QtGui.qApp.db
            tableEsklp_Smnn = db.table('esklp.Smnn')
            tableNC = db.table('rbNomenclature')
            tableESKLP_Klp = db.table('esklp.Klp')
            cond = []
            order = u'esklp.Smnn.code, esklp.Smnn.mnn, esklp.Smnn.form'
            queryTable = tableNC.innerJoin(tableESKLP_Klp, tableESKLP_Klp['UUID'].eq(tableNC['esklpUUID']))
            queryTable = queryTable.innerJoin(tableEsklp_Smnn, tableEsklp_Smnn['id'].eq(tableESKLP_Klp['smnn_id']))
            cond.append(tableNC['id'].eq(nomenclatureId))
            recordUUIDs = db.getRecordList(queryTable, [tableEsklp_Smnn['UUID']], cond, order=order)
            newSmnnUUID = ''
            if len(recordUUIDs) == 1:
                recordUUID = recordUUIDs[0]
                newSmnnUUID = forceStringEx(recordUUID.value('UUID')) if recordUUID else ''
            if oldSmnnUUID != newSmnnUUID:
                record.setValue('smnnUUID', toVariant(newSmnnUUID))
            if newSmnnUUID:
                oldSmnnGrlsLfId = forceRef(record.value('lfForm_id'))
                lfFormIdList = getLfFormIdList(nomenclatureId = nomenclatureId, smnnUUID = newSmnnUUID)
                if len(lfFormIdList) == 1:
                    newSmnnGrlsLfId = lfFormIdList[0]
                    if oldSmnnGrlsLfId != newSmnnGrlsLfId:
                        record.setValue('lfForm_id', toVariant(newSmnnGrlsLfId))
                elif oldSmnnGrlsLfId not in lfFormIdList:
                    record.setValue('lfForm_id', toVariant(None))
            else:
                record.setValue('lfForm_id', toVariant(None))
        return record


    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid():
            return False
        col = index.column()
        row = index.row()
        if col == self.getColIndex('shelfTime'):
            if not (0 <= row < len(self._items)):
                return False
            result = CInDocTableModel.setData(self, index, value, role)
            self.emitRowChanged(row)
            return result
        elif col == self.priceColIndex:
            if not (0 <= row < len(self._items)):
                return False
            item = self._items[row]
            qnt = forceDouble(item.value('qnt'))
            item.setValue('price', QVariant(forceDouble(value)))
            item.setValue('sum', QVariant(qnt*forceDouble(value)))
            self.emitRowChanged(row)
            return True
        elif col == self.getColIndex('qnt'):
            if not (0 <= row < len(self._items)):
                return False
            item = self._items[row]
            qnt = forceDouble(value)
            price = forceDouble(item.value('price'))
            item.setValue('qnt', QVariant(qnt))
            item.setValue('sum', QVariant(qnt*price))
            self.emitRowChanged(row)
        elif col == self.getColIndex('nomenclature_id'):
            if 0 <= row < len(self._items):
                oldNomenclatureId = forceRef(self._items[row].value('nomenclature_id'))
            else:
                oldNomenclatureId = None
            result = CInDocTableModel.setData(self, index, value, role)
            if result:
                item = self._items[row]
                nomenclatureId = forceRef(item.value('nomenclature_id'))
                if oldNomenclatureId != nomenclatureId:
                    unitId = self.getDefaultStockUnitId(nomenclatureId)
                    item.setValue('unit_id', toVariant(unitId))
                    item = self.updateSmnn_SmnnGrlslf(item, nomenclatureId, oldNomenclatureId)
                    self.emitRowChanged(row)
            return result
        elif col == self.getColIndex('unit_id'):
            if not (0 <= row < len(self._items)):
                return False
            result = CInDocTableModel.setData(self, index, value, role)
            return result
        else:
            return CInDocTableModel.setData(self, index, value, role)


    def createEditor(self, index, parent):
        editor = CInDocTableModel.createEditor(self, index, parent)
        column = index.column()
        if column == self.getColIndex('nomenclature_id'):
            filterSetter = getattr(editor, 'setOrgStructureId', None)
            if not filterSetter:
                return editor
            if not editor._stockOrgStructureId:
                filterSetter(getattr(self, '_supplierId', None))

            editor.getFilterData()
            editor.setFilter(editor._filter)
            editor.reloadData()
        elif column == self.getColIndex('unit_id'):
            self._setUnitEditorFilter(index.row(), editor)
        return editor


    def _setUnitEditorFilter(self, row, editor):
        if 0 <= row < len(self._items):
            item = self._items[row]
            nomenclatureId = forceRef(item.value('nomenclature_id'))
            if not nomenclatureId:
                return
            editor.setFilter(self._getNomenclatureUnitFilter(nomenclatureId))


    @staticmethod
    def _getNomenclatureUnitFilter(nomenclatureId):
        if not nomenclatureId:
            return None
        result = set()
        records = QtGui.qApp.db.getRecordList('rbNomenclature_UnitRatio', where='master_id=%d AND deleted=0' % nomenclatureId)
        for record in records:
            targetUnitId = forceRef(record.value('targetUnit_id'))
            sourceUnitId = forceRef(record.value('sourceUnit_id'))
            if targetUnitId:
                result.add(targetUnitId)
            if sourceUnitId:
                result.add(sourceUnitId)
        return QtGui.qApp.db.table('rbUnit')['id'].inlist(result)


    def cellReadOnly(self, index):
        row = index.row()
        if 0 <= row < len(self._items):
            column = index.column()
            if column == self.getColIndex('unit_id'):
                item = self._items[row]
                nomenclatureId = forceRef(item.value('nomenclature_id'))
                stockUnitId = self.getDefaultStockUnitId(nomenclatureId)
                return not bool(stockUnitId)

        return False


    def getDefaultStockUnitId(self, nomenclatureId):
        return self._getNomenclatureDefaultUnits(nomenclatureId).get('defaultStockUnitId')


    def getDefaultClientUnitId(self, nomenclatureId):
        return self._getNomenclatureDefaultUnits(nomenclatureId).get('defaultClientUnitId')


    def _getNomenclatureDefaultUnits(self, nomenclatureId):
        if not nomenclatureId:
            return {}
        if nomenclatureId not in self._getCache():
            record = QtGui.qApp.db.getRecord(
                'rbNomenclature', 'defaultStockUnit_id, defaultClientUnit_id', nomenclatureId
            )
            if record:
                defaultStockUnitId = forceRef(record.value('defaultStockUnit_id'))
                defaultClientUnitId = forceRef(record.value('defaultClientUnit_id'))
            else:
                defaultStockUnitId = defaultClientUnitId = None
            self._getCache()[nomenclatureId] = {
                'defaultStockUnitId': defaultStockUnitId,
                'defaultClientUnitId': defaultClientUnitId
            }
        return self._getCache()[nomenclatureId]


    def _getCache(self):
        if not hasattr(self, '_modelInfoCache'):
            self._modelInfoCache = {}
        return self._modelInfoCache


    def loadItems(self, masterId):
        db = QtGui.qApp.db
        cols = []
        for col in self._cols:
            if not col.external():
                cols.append(col.fieldName())
        cols.append(self._idFieldName)
        cols.append(self._masterIdFieldName)
        if self._idxFieldName:
            cols.append(self._idxFieldName)
        for col in self._hiddenCols:
            cols.append(col)
        table = self._table
        filter = [table[self._masterIdFieldName].eq(masterId)]
        if self._filter:
            filter.append(self._filter)
        if table.hasField('deleted'):
            filter.append(table['deleted'].eq(0))
        if self._idxFieldName:
            order = [self._idxFieldName, self._idFieldName]
        else:
            order = [self._idFieldName]
        self._items = db.getRecordList(table, cols, filter, order)
        if self._extColsPresent:
            extSqlFields = []
            for col in self._cols:
                if col.external():
                    fieldName = col.fieldName()
                    if fieldName not in cols:
                        extSqlFields.append(QtSql.QSqlField(fieldName, col.valueType()))
            if extSqlFields:
                for item in self._items:
                    for field in extSqlFields:
                        item.append(field)
        for item in self._items:
            item.append(QtSql.QSqlField('isUpdate', QVariant.Int))
            item.setValue('isUpdate', toVariant(0))
            price = 0
            qnt = forceDouble(item.value('qnt'))
            if qnt:
                sum = forceDouble(item.value('sum'))
                price = sum/qnt
            item.append(QtSql.QSqlField('price', QVariant.Double))
            item.setValue('price', toVariant(price))
        self.reset()

