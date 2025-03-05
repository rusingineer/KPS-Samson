# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2022 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################


from PyQt4 import QtGui, QtSql
from PyQt4.QtCore import Qt, pyqtSignature, QDateTime, QDate, QVariant

from library.crbcombobox         import CRBComboBox
from library.InDocTable          import CInDocTableModel, CDateInDocTableCol, CFloatInDocTableCol, CRBInDocTableCol
from library.interchange         import getDateEditValue, setDateEditValue, getLineEditValue, setLineEditValue, getRBComboBoxValue, setRBComboBoxValue
from library.PrintInfo           import CInfoContext
from library.PrintTemplates      import applyTemplate, CPrintAction, CPrintButton, getPrintTemplates
from library.Counter             import CCounterController
from library.ItemsListDialog     import CItemEditorBaseDialog
from library.Utils               import forceDouble, forceRef, forceString, toVariant, forceInt, forceDate
from Reports.ReportBase          import CReportBase, createTable
from Reports.ReportView          import CReportViewDialog
from Stock.NomenclatureComboBox  import CNomenclatureInDocTableCol
from RefBooks.Nomenclature.List  import CRBNomenclatureEditor
from Stock.StockMotionBaseDialog import CStockMotionItemsCopyPasteMixin
from Stock.Utils                 import getStockMotionItemQuantityColumn, CSummaryInfoModelMixin, getBatchShelfTimeFinance, getStockMotionNumberCounterId, getRatio


from Ui_PurchaseInvoice import Ui_PurchaseInvoiceDialog


class CPurchaseInvoiceEditDialog(Ui_PurchaseInvoiceDialog, CItemEditorBaseDialog, CStockMotionItemsCopyPasteMixin):
    purchaseDocumentType = 1 # Заявка на закупку

    def __init__(self,  parent):
        CItemEditorBaseDialog.__init__(self, parent, 'StockPurchaseContract')
        CStockMotionItemsCopyPasteMixin.__init__(self, parent)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.addObject('btnPrint', CPrintButton(self, u'Печать'))
        self.btnPrint.setShortcut('F6')
        self.addObject('btnFill', QtGui.QPushButton(u'Заполнить', self))
        self.btnFill.setShortcut('F9')
        self.addObject('actOpenStockBatchEditor', QtGui.QAction(u'Подобрать параметры', self))
        self.addObject('actOpenNomenclatureEditor', QtGui.QAction(u'Редактировать', self))
        self.addModels('Items', CItemsModel(self))
        self.setupUi(self)
        self.cmbReceiverPerson.setSpecialityIndependents()
        self.cmbSupplierOrg.setFilter('isSupplier = 1')
        self.cmbFinance.setTable('rbFinance')
        self.tblItems.setModel(self.modelItems)
        self.prepareItemsPopupMenu(self.tblItems)
        self.tblItems.popupMenu().addSeparator()
        self.tblItems.popupMenu().addAction(self.actOpenNomenclatureEditor)
        self.tblItems.popupMenu().addAction(self.actOpenStockBatchEditor)
        self.tblItems.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.tblItems.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.buttonBox.addButton(self.btnPrint, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnFill, QtGui.QDialogButtonBox.ActionRole)
        self.btnFill.setEnabled(False)
        self.purchaseContractId = None
        templates = getPrintTemplates(self.getStockContext())
        if not templates:
            self.btnPrint.setId(-1)
        else:
            for template in templates:
                action = CPrintAction(template.name, template.id, self.btnPrint, self.btnPrint)
                self.btnPrint.addAction(action)
            self.btnPrint.menu().addSeparator()
            self.btnPrint.addAction(CPrintAction(u'Напечатать список', -1, self.btnPrint, self.btnPrint))
        self._initView()
        self.setupDirtyCather()
        self.tblItems.enableColsMove()


    def getStockContext(self):
        return ['PurchaseInvoice']


    def setPurchaseContractInfo(self, record):
        if record:
            self.purchaseContractId = forceRef(record.value('id'))
            setRBComboBoxValue(self.cmbSupplierOrg, record, 'supplierOrg_id')
            setRBComboBoxValue(self.cmbReason,      record, 'id')


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


    def actPrintPurchaseInvoice(self, templateId):
        from Stock.StockMotionInfo import CStockPurchaseContractInfo, CStockPurchaseContractItemInfoList
        if templateId == -1:
            self.getNomenclaturePrint()
        else:
            purchaseContractId = self.itemId()
            if purchaseContractId:
                context = CInfoContext()
                data = { 'purchaseInvoice':CStockPurchaseContractInfo(context, purchaseContractId), # Заявка на поставку
                         'purchaseInvoicetList': CStockPurchaseContractItemInfoList(context, purchaseContractId) # Спецификация
                        }
                QtGui.qApp.call(self, applyTemplate, (self, templateId, data))


    def dumpParams(self, cursor):
        db = QtGui.qApp.db
        description = []
        number = unicode(self.edtNumber.text())
        if number:
            description.append(u'Номер %s'%number)
        docDate = self.edtDocDate.date()
        if docDate:
           description.append(u'Дата документа %s'%forceString(docDate))
        reason = unicode(self.cmbReason.currentText())
        if reason:
           description.append(u'Основание %s'%reason)
        date = self.edtDate.date()
        if date:
            description.append(u'Дата приходования %s'%forceString(date))
        receiver = self.cmbReceiver.value()
        if receiver:
            description.append(u'Получатель %s'%forceString(db.translate('OrgStructure', 'id', receiver, 'name')))
        receiverPerson = self.cmbReceiverPerson.value()
        if receiverPerson:
            description.append(u'Ответственный %s'%forceString(db.translate('vrbPersonWithSpeciality', 'id', receiverPerson, 'name')))
        note = self.edtNote.text()
        if note:
            description.append(u'Примечания %s'%forceString(note))
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
        html = doc.toHtml('utf-8')
        view = CReportViewDialog(self)
        view.setText(html)
        view.exec_()


    def prepareItemsPopupMenu(self, tblWidget):
        tblWidget.addPopupDuplicateCurrentRow()
        tblWidget.addPopupSeparator()
        tblWidget.addMoveRow()
        tblWidget.addPopupDelRow()


    def _checkStockMotionItemsData(self, tblItems):
        model = tblItems.model()
        items = model.items()
        for idx, item in enumerate(items):
            qnt = forceDouble(item.value('qnt'))
            if qnt <= 0:
                return self.checkValueMessage(
                    u'Количество должно быть больше нуля!', False, tblItems, idx, model.getColIndex('qnt')
                )
            unitId = forceRef(item.value('unit_id'))
            if not unitId:
                return self.checkValueMessage(u'Необходимо указать Ед.Учета!', False, tblItems, idx, model.getColIndex('unit_id'))
        return True


    @pyqtSignature('int')
    def on_cmbSupplier_currentIndexChanged(self, val):
        orgStructureId = self.cmbSupplier.value()
        self.cmbSupplierPerson.setOrgStructureId(orgStructureId)
        if hasattr(self, 'modelItems'):
            self.modelItems.setSupplierId(orgStructureId)
        self._on_cmbSupplierChanged()


    def _on_cmbSupplierChanged(self):
        pass


    def _generateStockMotionNumber(self):
        if unicode(self.edtNumber.text()):
            return
        counterId = getStockMotionNumberCounterId(self.stockDocumentType)
        if not counterId:
            return
        number = QtGui.qApp.getDocumentNumber(None, counterId, date=QDate.currentDate())
        self.edtNumber.setText(number)


    def setDefaults(self):
        now = QDateTime.currentDateTime()
        self.edtDate.setDate(now.date())
        self.cmbReceiver.setValue(QtGui.qApp.currentOrgStructureId())


    def setRecord(self, record):
        CItemEditorBaseDialog.setRecord(self, record)
        setLineEditValue(self.edtNumber, record, 'number')
        setDateEditValue(self.edtDate, record, 'date')
        if hasattr(self, 'edtReason'):
            setLineEditValue(self.edtReason, record, 'reason')
        if hasattr(self, 'edtReasonDate'):
            setDateEditValue(self.edtReasonDate, record, 'reasonDate')
        if hasattr(self, 'cmbSupplier'):
            setRBComboBoxValue(self.cmbSupplier,       record, 'supplier_id')
            setRBComboBoxValue(self.cmbSupplierPerson, record, 'supplierPerson_id')
        setLineEditValue(    self.edtNote,            record, 'note')
        if hasattr(self, 'lblSummaryInfo') and hasattr(self, 'modelItems'):
            self.lblSummaryInfo.setText(self.modelItems.getSummaryInfo())
        setRBComboBoxValue(self.cmbSupplierOrg,       record, 'supplierOrg_id')
        setDateEditValue(  self.edtDocDate,           record, 'docDate')
        setRBComboBoxValue(self.cmbReason,            record, 'reason_id')
        setLineEditValue(  self.edtSupplierOrgPerson, record, 'supplierOrgPerson')
        setRBComboBoxValue(self.cmbReceiver,          record, 'receiver_id')
        setRBComboBoxValue(self.cmbReceiverPerson,    record, 'receiverPerson_id')
        self.modelItems.loadItems(self.itemId())
        self.lblSummaryInfo.setText(self.modelItems.getSummaryInfo())
        self.btnFill.setEnabled(self.cmbReason.value() is not None)
        self.setIsDirty(False)


    def getRecord(self):
        record = CItemEditorBaseDialog.getRecord(self)
        getLineEditValue(self.edtNumber, record, 'number')
        getDateEditValue(self.edtDate, record, 'date')
        if hasattr(self, 'edtReason'):
            getLineEditValue(   self.edtReason, record, 'reason')
        if hasattr(self, 'edtReasonDate'):
            setDateEditValue(self.edtReasonDate, record, 'reasonDate')
        if hasattr(self, 'cmbSupplier'):
            getRBComboBoxValue( self.cmbSupplier,       record, 'supplier_id')
            getRBComboBoxValue( self.cmbSupplierPerson, record, 'supplierPerson_id')
        getLineEditValue(self.edtNote, record, 'note')
        getRBComboBoxValue(self.cmbSupplierOrg,       record, 'supplierOrg_id')
        getDateEditValue(  self.edtDocDate,           record, 'docDate')
        getRBComboBoxValue(self.cmbReason,            record, 'reason_id')
        getLineEditValue(  self.edtSupplierOrgPerson, record, 'supplierOrgPerson')
        getRBComboBoxValue(self.cmbReceiver,          record, 'receiver_id')
        getRBComboBoxValue(self.cmbReceiverPerson,    record, 'receiverPerson_id')
        record.setValue('type', self.purchaseDocumentType)
        return record


    def saveInternals(self, id):
        financeId = self.cmbFinance.value()
        for item in self.modelItems.items():
            item.setValue('finance_id', financeId)
        self.modelItems.saveItems(id)


    def checkDataEntered(self):
        result = self._checkStockMotionItemsData(self.tblItems)
        result = result and (self.cmbReason.value() or self.checkInputMessage(u'основание', False, self.cmbReason))
        result = result and (self.cmbSupplierOrg.value() or self.checkInputMessage(u'поставщика', False, self.cmbSupplierOrg))
        result = result and self.checkItemsDataEntered()
        return result


    def checkItemsDataEntered(self):
        return True


    @pyqtSignature('int')
    def on_cmbSupplierOrg_currentIndexChanged(self, val):
        supplierOrgId = self.cmbSupplierOrg.value()
        supplierOrgAssigned = bool(supplierOrgId)
        for widget in ( self.lblSupplierOrgPerson, self.edtSupplierOrgPerson,
                        self.lblReason,            self.cmbReason,
                        self.lblFinance,           self.cmbFinance,
                      ):
            widget.setEnabled(supplierOrgAssigned)
        self.cmbReason.setSupplierOrgId(supplierOrgId)
        self.modelItems.setSupplierOrgId(supplierOrgId)


    @pyqtSignature('QDate')
    def on_edtDate_dateChanged(self, date):
        self.cmbReason.setDate(date)


    @pyqtSignature('int')
    def on_cmbReason_currentIndexChanged(self, index):
        purchaseContractId = self.cmbReason.value()
        self.btnFill.setEnabled(bool(purchaseContractId))
        if purchaseContractId:
            db = QtGui.qApp.db
            record = db.getRecord('StockPurchaseContract',
                                   ('finance_id',
                                    'confirmationOrder'
                                   ),
                                   purchaseContractId
                                 )
            self.cmbFinance.setValue(forceRef(record.value('finance_id')))
            self.cmbConfirmationOrder.setCurrentIndex(forceInt(record.value('confirmationOrder')))
        else:
            self.cmbFinance.setValue(None)
            self.cmbConfirmationOrder.setCurrentIndex(0)


    @pyqtSignature('int')
    def on_cmbReceiver_currentIndexChanged(self, index):
        receiverId = self.cmbReceiver.value()
        self.cmbReceiverPerson.setOrgStructureId(receiverId)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_modelItems_dataChanged(self, topLeftIndex, bottomRightIndex):
        self.lblSummaryInfo.setText(self.modelItems.getSummaryInfo())


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


    @pyqtSignature('')
    def on_actOpenStockBatchEditor_triggered(self):
        self.on_tblItems_doubleClicked(self.tblItems.currentIndex())


    @pyqtSignature('int')
    def on_btnPrint_printByTemplate(self, templateId):
        self.actPrintPurchaseInvoice(templateId)


    @pyqtSignature('')
    def on_btnFill_clicked(self):
        purchaseContractId = self.cmbReason.value()
        if purchaseContractId:
            self.modelItems.fill(purchaseContractId)


class CItemsModel(CInDocTableModel, CSummaryInfoModelMixin):
    class CSumCol(CFloatInDocTableCol):
        def _toString(self, value):
            if value.isNull():
                return None
            return format(forceDouble(value), '.2f')

    class CLocNomenclatureCol(CNomenclatureInDocTableCol):
        def __init__(self, title, fieldName, width, **params):
            CNomenclatureInDocTableCol.__init__(self, title, fieldName, width, **params)

        def createEditor(self, parent):
            editor = CNomenclatureInDocTableCol.createEditor(self, parent)
            editor.setOnlyNomenclature(True)
            return editor

    def __init__(self, parent, showExists=False):
        CInDocTableModel.__init__(self, 'StockPurchaseContract_Item', 'id', 'master_id', parent)
        self._nomenclatureColumn = self.CLocNomenclatureCol(u'ЛСиИМН', 'nomenclature_id', 50, showFields = CRBComboBox.showName)
        self._unitColumn = CRBInDocTableCol(u'Ед.Учета', 'unit_id', 12, 'rbUnit', addNone=False)
        self.addCol(self._nomenclatureColumn)
        self.addCol(CDateInDocTableCol( u'Годен до', 'shelfTime', 12, canBeEmpty=True))
        self.addCol(getStockMotionItemQuantityColumn(u'Кол-во', 'qnt', 12))
        self.addCol(getStockMotionItemQuantityColumn(u'Осталось для поставок', 'remainPurchaseQnt', 12).setReadOnly())
        self.addCol(self._unitColumn)
        sumCol = CItemsModel.CSumCol( u'Сумма', 'sum', 12)
        self.addCol(sumCol)
        self.addExtCol(CFloatInDocTableCol(u'Цена', 'price', 12, precision=2), QVariant.Double)
        self.priceColIndex = len(self.cols())-1
        self.addHiddenCol('purchaseContractQnt')
        self.priceCache = parent
        self.qntColumnIndex = self.getColIndex('qnt')
        self.updateBatchShelfTimeFinance = True
        self._supplierOrgId = None


    def getEmptyRecord(self):
        result = CInDocTableModel.getEmptyRecord(self)
        result.append(QtSql.QSqlField('price', QVariant.Double))
        return result


    def getNomenclatureNameById(self, nomenclatureId):
        return forceString(self._nomenclatureColumn.toString(nomenclatureId, None))


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
            price = 0
            qnt = forceDouble(item.value('qnt'))
            sum = forceDouble(item.value('sum'))
            if qnt > 0:
                price = sum/qnt
            item.setValue('price', toVariant(price))
        self.reset()


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
            result = CInDocTableModel.setData(self, index, value, role)
            if result:
                item = self._items[row]
                qnt = forceDouble(item.value('qnt'))
                item.setValue('sum', QVariant(qnt*forceDouble(value)))
                self.emitRowChanged(row)
            return result
        elif col == self.getColIndex('qnt'):
            result = CInDocTableModel.setData(self, index, value, role)
            if result:
                if 0 <= row < len(self._items):
                    item = self._items[row]
                    price = forceDouble(item.value('price'))
                    qnt = forceDouble(value)
                    item.setValue('sum', QVariant(qnt*price))
                    self.emitRowChanged(row)
            return result
        elif col == self.getColIndex('sum'):
            result = CInDocTableModel.setData(self, index, value, role)
            if result:
                if 0 <= row < len(self._items):
                    item = self._items[row]
                    sum = forceDouble(item.value('sum'))
                    qnt = forceDouble(item.value('qnt'))
                    item.setValue('price', QVariant(sum/qnt if qnt > 0 else 0))
                    self.emitRowChanged(row)
            return result
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
                    if self.updateBatchShelfTimeFinance:
                        batch, shelfTime, financeId, medicalAidKind, price = getBatchShelfTimeFinance(forceRef(value))
                        result = CInDocTableModel.setData(self, index, value, role)
                        item.setValue('shelfTime', toVariant(shelfTime))
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


    def fill(self, purchaseContractId):
        if purchaseContractId:
            db = QtGui.qApp.db
            tablePurchaseContract = db.table('StockPurchaseContract')
            tablePurchaseContractItem = db.table('StockPurchaseContract_Item')
            cols = [tablePurchaseContract['finance_id'],
                    tablePurchaseContractItem['idx'],
                    tablePurchaseContractItem['nomenclature_id'],
                    tablePurchaseContractItem['batch'],
                    tablePurchaseContractItem['shelfTime'],
                    tablePurchaseContractItem['qnt'],
                    tablePurchaseContractItem['unit_id'],
                    tablePurchaseContractItem['sum']
                    ]
            cond = [tablePurchaseContract['id'].eq(purchaseContractId),
                    tablePurchaseContract['deleted'].eq(0),
                    tablePurchaseContractItem['master_id'].eq(purchaseContractId),
                    tablePurchaseContractItem['deleted'].eq(0)
                    ]
            queryTable = tablePurchaseContract.innerJoin(tablePurchaseContractItem, tablePurchaseContractItem['master_id'].eq(tablePurchaseContract['id']))
            records = db.getRecordList(queryTable, cols, cond, order = [tablePurchaseContractItem['idx'].name()])
            if records:
                nomenclatureQnt = {}
                nomenclatureFill = {}
                cond = [tablePurchaseContract['deleted'].eq(0),
                        tablePurchaseContract['reason_id'].eq(purchaseContractId),
                        tablePurchaseContractItem['deleted'].eq(0)
                        ]
                recordInvoices = db.getRecordList(queryTable, cols, cond, order = [tablePurchaseContractItem['idx'].name()])
                for recordInvoice in recordInvoices:
                    nomenclatureId = forceRef(recordInvoice.value('nomenclature_id'))
                    defaultUnitId = self.getDefaultStockUnitId(nomenclatureId)
                    shelfTime = forceDate(recordInvoice.value('shelfTime'))
                    shelfTimeKey = shelfTime.toPyDate() if bool(shelfTime) else None
                    unitId = forceRef(recordInvoice.value('unit_id'))
                    smiQnt = nomenclatureQnt.get((nomenclatureId, shelfTimeKey), 0)
                    qnt = forceDouble(recordInvoice.value('qnt'))
                    if defaultUnitId != unitId:
                        ratio = getRatio(nomenclatureId, defaultUnitId, unitId)
                        if ratio is not None:
                            qnt = qnt/ratio
                    smiQnt += qnt
                    nomenclatureQnt[(nomenclatureId, shelfTimeKey)] = smiQnt
                for record in records:
                    nomenclatureId = forceRef(record.value('nomenclature_id'))
                    qnt = forceDouble(record.value('qnt'))
                    sum = forceDouble(record.value('sum'))
                    shelfTime = forceDate(record.value('shelfTime'))
                    shelfTimeKey = shelfTime.toPyDate() if bool(shelfTime) else None
                    defaultUnitId = self.getDefaultStockUnitId(nomenclatureId)
                    unitId = forceRef(record.value('unit_id'))
                    if not nomenclatureFill.get((nomenclatureId, shelfTimeKey), False):
                        smiQnt = nomenclatureQnt.get((nomenclatureId, shelfTimeKey), 0)
                        price = sum/qnt if qnt > 0 else 0
                        if defaultUnitId != unitId:
                            ratio = getRatio(nomenclatureId, unitId, defaultUnitId)
                            if ratio is not None:
                                smiQnt = smiQnt/ratio
                                price = price/ratio
                        qnt = qnt - smiQnt
                        if qnt > 0:
                            myItem = self.getEmptyRecord()
                            myItem.setValue('nomenclature_id', toVariant(nomenclatureId))
                            myItem.setValue('unit_id',         unitId)
                            myItem.setValue('batch',           record.value('batch'))
                            myItem.setValue('shelfTime',       record.value('shelfTime'))
                            myItem.setValue('qnt',             toVariant(0))
                            myItem.setValue('remainPurchaseQnt', toVariant(qnt))
                            myItem.setValue('purchaseContractQnt', toVariant(qnt))
                            myItem.setValue('sum',             toVariant(price*qnt))
                            myItem.setValue('price',           toVariant(price))
                            self.items().append(myItem)
                            nomenclatureFill[(nomenclatureId, shelfTimeKey)] = True
        self.reset()


    def setSupplierOrgId(self, orgId):
        self._supplierOrgId = orgId
