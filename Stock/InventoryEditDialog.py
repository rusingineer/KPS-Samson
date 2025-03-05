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

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QDateTime, pyqtSignature

from library.crbcombobox         import CRBComboBox
from library.InDocTable          import CDateInDocTableCol, CFloatInDocTableCol, CInDocTableCol, CRBInDocTableCol, CEnumInDocTableCol, CInDocTableModel
from library.interchange         import getRBComboBoxValue
from library.PrintInfo           import CInfoContext
from library.PrintTemplates      import applyTemplate, CPrintAction, CPrintButton, getPrintTemplates
from library.Utils               import forceDouble, forceString, forceRef, toVariant
from Reports.ReportBase          import CReportBase, createTable
from Reports.ReportView          import CReportViewDialog
from Stock.NomenclatureComboBox  import CNomenclatureInDocTableCol
from Stock.InventoryFillDialog   import CInventoryFillDialog
from Stock.StockMotionBaseDialog import CStockMotionBaseDialog, CStockMotionItemsCopyPasteMixin, CNomenclatureItemsBaseModel
from Stock.Utils                 import CSummaryInfoModelMixin, CPriceItemDelegate, getStockMotionItemQuantityColumn, getExistsNomenclatureStmt, getExistsNomenclatureAmount, findFinanceBatchShelfTime, getBatchShelfTimeFinance, FILTER_FOR_BATCH_FOR_COMBOBOX

from Stock.Ui_Inventory          import Ui_InventoryDialog


class CInventoryEditDialog(CStockMotionBaseDialog, CStockMotionItemsCopyPasteMixin, Ui_InventoryDialog):
    stockDocumentType = 1 #Инвентаризация

    def __init__(self,  parent):
        CStockMotionBaseDialog.__init__(self, parent)
        CStockMotionItemsCopyPasteMixin.__init__(self, parent)
        self.addModels('Items', CItemsModel(self))
        self.addModels('Commission', CStockInventoryCommissionModel(self))
        self.addObject('actDuplicate', QtGui.QAction(u'Дублировать', self))
        self.addObject('btnFill', QtGui.QPushButton(u'Заполнить', self))
        self.btnFill.setShortcut('F9')
        self.addObject('btnPrint', CPrintButton(self, u'Печать'))
        self.btnPrint.setShortcut('F6')
        self.setupBtnFillMenu()
        self.setupUi(self)
        self.cmbSupplierPerson.setSpecialityIndependents()
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setupDirtyCather()
        self.buttonBox.addButton(self.btnPrint, QtGui.QDialogButtonBox.ActionRole)
        templates = getPrintTemplates(self.getStockContext())
        if not templates:
            self.btnPrint.setId(-1)
        else:
            for template in templates:
                action = CPrintAction(template.name, template.id, self.btnPrint, self.btnPrint)
                self.btnPrint.addAction(action)
            self.btnPrint.menu().addSeparator()
            self.btnPrint.addAction(CPrintAction(u'Напечатать список', -1, self.btnPrint, self.btnPrint))
        self.tblItems.setModel(self.modelItems)
        self.tblCommission.setModel(self.modelCommission)
        self.prepareItemsPopupMenu(self.tblItems)
        self.tblItems.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.tblItems.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.buttonBox.addButton(self.btnFill, QtGui.QDialogButtonBox.ActionRole)
        self.btnFill.setMenu(self.mnuBtnFill)
        self.tblItems.setItemDelegateForColumn(CItemsModel.priceColumnIndex, CPriceItemDelegate(self.tblItems))
        self.tblCommission.addPopupDelRow()
        self.tblCommission.addMoveRow()
        self._initView()
        self.tblItems.enableColsMove()


    def setupBtnFillMenu(self):
        self.addObject('mnuBtnFill', QtGui.QMenu(self))
        self.addObject('actFill', QtGui.QAction(u'По остаткам', self))
        self.addObject('actFillFilter', QtGui.QAction(u'По отбору', self))
        self.mnuBtnFill.addAction(self.actFill)
        self.mnuBtnFill.addAction(self.actFillFilter)


    @pyqtSignature('')
    def on_mnuBtnFill_aboutToShow(self):
        self.actFill.setEnabled(True)
        self.actFillFilter.setEnabled(True)


    @pyqtSignature('')
    def on_actFill_triggered(self):
        self.on_btnFill(isFilter=False)


    @pyqtSignature('')
    def on_actFillFilter_triggered(self):
        self.on_btnFill(isFilter=True)


    @pyqtSignature('int')
    def on_btnPrint_printByTemplate(self, templateId):
        self.actPrintMotions(templateId)


    def actPrintMotions(self, templateId):
        from Stock.StockMotionInfo import CStockMotionCommissionInfo, CStockMotionItemInfo, CStockMotionInfo
        if templateId == -1:
            self.getNomenclaturePrint()
        else:
            context = CInfoContext()
            record = self.getRecord()
            inventory = CStockMotionInfo(context, forceRef(record.value('id')))
            inventory.setRecord(record)
            inventory.setOkLoaded()
            inventoryList = []
            for recordItem in self.modelItems.items():
                item = CStockMotionItemInfo(context, forceRef(recordItem.value('id')))
                item.setRecord(recordItem)
                item.setOkLoaded()
                inventoryList.append(item)
            inventory._items = inventoryList
            commissionList = []
            for recordCommission in self.modelCommission.items():
                item = CStockMotionCommissionInfo(context, forceRef(recordCommission.value('id')))
                item.setRecord(recordCommission)
                item.setOkLoaded()
                commissionList.append(item)
            data = { 'Inventory'     : inventory,
                     'InventoryList' : inventoryList,
                     'CommissionList': commissionList
                   }
            QtGui.qApp.call(self, applyTemplate, (self, templateId, data))


    def getStockContext(self):
        return ['InventoryList']


    def dumpParams(self, cursor):
        db = QtGui.qApp.db
        description = []
        number = self.edtNumber.text()
        if number:
            description.append(u'Номер %s'%forceString(number))
        date = QDateTime(self.edtDate.date(), self.edtTime.time())
        if date:
           description.append(u'Дата %s'%forceString(date))
        reason = self.edtReason.text()
        if reason:
            description.append(u'Основание %s'%forceString(reason))
        reasonDate = self.edtReasonDate.date()
        if reasonDate:
           description.append(u'Дата основания %s'%forceString(reasonDate))
        supplier = self.cmbSupplier.value()
        if supplier:
            description.append(u'Подразделение %s'%forceString(db.translate('OrgStructure', 'id', supplier, 'name')))
        supplierPerson = self.cmbSupplierPerson.value()
        if supplierPerson:
            description.append(u'Ответственный %s'%forceString(db.translate('vrbPersonWithSpeciality', 'id', supplierPerson, 'name')))
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
#        title = self.windowTitle()
        model = self.tblItems.model()
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.windowTitle())
        self.dumpParams(cursor)
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertText(u'ЛСиИМН.')
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
        cursor.insertText(u'Состав комиссии.')
        cursor.insertBlock()
        colWidths  = [ self.tblCommission.columnWidth(i) for i in xrange(self.modelCommission.columnCount()-1) ]
        colWidths.insert(0,10)
        totalWidth = sum(colWidths)
        tableColumns = []
        iColNumber = False
        for iCol, colWidth in enumerate(colWidths):
            widthInPercents = str(max(1, colWidth*90/totalWidth))+'%'
            if iColNumber == False:
                tableColumns.append((widthInPercents, [u'№'], CReportBase.AlignRight))
                iColNumber = True
            tableColumns.append((widthInPercents, [forceString(self.modelCommission._cols[iCol].title())], CReportBase.AlignLeft))
        table = createTable(cursor, tableColumns)
        for iModelRow in xrange(self.modelCommission.rowCount()-1):
            iTableRow = table.addRow()
            table.setText(iTableRow, 0, iModelRow+1)
            for iModelCol in xrange(self.modelCommission.columnCount()):
                index = self.modelCommission.createIndex(iModelRow, iModelCol)
                text = forceString(self.modelCommission.data(index))
                table.setText(iTableRow, iModelCol+1, text)
        html = doc.toHtml('utf-8')
        view = CReportViewDialog(self)
        view.setText(html)
        view.exec_()


    def setDefaults(self):
        CStockMotionBaseDialog.setDefaults(self)


    def setRecord(self, record):
        CStockMotionBaseDialog.setRecord(self, record)
        self.modelItems.loadItems(self.itemId())
        self.modelCommission.loadItems(self.itemId())
        self.setIsDirty(False)
        self.lblSummaryInfo.setText(self.modelItems.getSummaryInfo())


    def getRecord(self):
        record = CStockMotionBaseDialog.getRecord(self)
        getRBComboBoxValue( self.cmbSupplier, record, 'receiver_id')
        getRBComboBoxValue( self.cmbSupplierPerson, record, 'receiverPerson_id')
        record.setValue('type', 1)
        return record


    def saveInternals(self, id):
        self.modelItems.saveItems(id)
        self.modelCommission.saveItems(id)


    def checkDataEntered(self):
        result = self._checkStockMotionItemsData(self.tblItems)
#        result = result and (self.cmbPurpose.value() or self.checkInputMessage(u'назначение', False, self.cmbPurpose))
#        result = result and self.checkItemsDataEntered()
        return result

    def _checkStockMotionItemsData(self, tblItems):
        return True
#    def checkItemsDataEntered(self):
#        for row, item in enumerate(self.modelItems.items()):
#            if not self.checkItemDataEntered(row, item):
#                return False
#        return True
#
#
#    def checkItemDataEntered(self, row, item):
#        nomenclatureId = forceString(item.value('nomenclature_id'))
#        qnt            = forceDouble(item.value('qnt'))
#        result = nomenclatureId or self.checkInputMessage(u'лекарственное средство или изделие медицинского назначения', False, self.tblProperties, row, 0)
#        result = result and (qnt or self.checkInputMessage(u'количество', False, self.tblProperties, row, 2))
#        return result

    @pyqtSignature('')
    def on_cmbSupplier_valueChanged(self):
        self.btnFill.setEnabled(self.cmbSupplier.value() is not None)


#    @pyqtSignature('')
    def on_btnFill(self, isFilter):
        filter = {}
        if isFilter:
            dialog = None
            try:
                dialog = CInventoryFillDialog(self)
                if dialog.exec_():
                    filter = dialog.getFilter()
            finally:
                if dialog:
                    dialog.deleteLater()
        orgStructureId = self.cmbSupplier.value()
        if orgStructureId:
            self.modelItems.fill(orgStructureId, filter)
            self.lblSummaryInfo.setText(self.modelItems.getSummaryInfo())


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_modelItems_dataChanged(self,  topLeftIndex, bottomRightIndex):
        self.lblSummaryInfo.setText(self.modelItems.getSummaryInfo())


class CItemsModel(CNomenclatureItemsBaseModel, CSummaryInfoModelMixin):
    batchColumnIndex = 1
    priceColumnIndex = 10

    class CLocNomenclatureCol(CNomenclatureInDocTableCol):
        def __init__(self, title, fieldName, width, **params):
            CNomenclatureInDocTableCol.__init__(self, title, fieldName, width, **params)

        def createEditor(self, parent):
            editor = CNomenclatureInDocTableCol.createEditor(self, parent)
            editor.setOnlyNomenclature(True)
            return editor

    class CLocFloatCol(CFloatInDocTableCol):
        def _toString(self, value):
            if value.isNull():
                return None
            return format(forceDouble(value), '.2f')

    def __init__(self, parent):
        CNomenclatureItemsBaseModel.__init__(self, parent)
        #CNomenclatureItemsBaseModel.__init__(self, 'StockMotion_Item', 'id', 'master_id', parent)
        self.priceCache = parent
        self._unitColumn = CRBInDocTableCol(u'Ед.Учета', 'unit_id', 12, 'rbUnit', addNone=False)
        self.addCol(
            self.CLocNomenclatureCol(
                u'ЛСиИМН', 'nomenclature_id', 50, showFields=CRBComboBox.showName, showLfForm=True
            )
        )
        self.addCol(CInDocTableCol( u'Серия', 'batch', 16))
        self.addCol(CDateInDocTableCol( u'Годен до', 'shelfTime', 12, canBeEmpty=True))
        self.addCol(CRBInDocTableCol(   u'Тип финансирования', 'finance_id', 15, 'rbFinance'))
        self.addCol(CRBInDocTableCol(   u'Вид медицинской помощи', 'medicalAidKind_id', 15, 'rbMedicalAidKind'))
        self.addCol(getStockMotionItemQuantityColumn( u'Кол-во по документам', 'oldQnt', 12))
        self.addCol(CFloatInDocTableCol(u'Цена по документам', 'oldPrice', 12, precision=2).setReadOnly())
        self.addCol(CItemsModel.CLocFloatCol(u'Сумма по документам', 'oldSum', 12).setReadOnly())
        self.addCol(self._unitColumn)
        self.addCol(getStockMotionItemQuantityColumn(u'Фактическое кол-во', 'qnt', 12))
        self.addCol(CFloatInDocTableCol(u'Фактическая цена', 'price', 12, precision=2))
        self.addCol(CItemsModel.CLocFloatCol(u'Фактическая сумма', 'sum', 12))
        self.addCol(CInDocTableCol( u'Примечание', 'note', 15))
        self._batchCache = {}


    def _getBatchEditorItems(self, nomenclatureId, financeId, batch, unitId):
        if nomenclatureId not in self._batchCache:
            result = [u'']
            nomenclatureAmount = getExistsNomenclatureAmount(nomenclatureId, financeId, batch, unitId=unitId)
            if nomenclatureAmount <= 0:
                return result
            batchList = findFinanceBatchShelfTime(QtGui.qApp.currentOrgStructureId(), nomenclatureId, qnt=None, filterFor=FILTER_FOR_BATCH_FOR_COMBOBOX, financeId=financeId, first=False)
            batchKeys = []
            for financeId, batch, shelfTime, medicalAidKindId, price, reservationClient in batchList:
                batchKey = (financeId, batch, shelfTime, medicalAidKindId)
                if batchKey not in batchKeys:
                    batchKeys.append(batchKey)
                    result.append(batch)
            self._batchCache[nomenclatureId] = result
        return self._batchCache[nomenclatureId]


    def _getBatchEditorItemsByRow(self, row):
        if 0 <= row < len(self._items):
            item = self._items[row]
            nomenclatureId = forceRef(item.value('nomenclature_id'))
            financeId = forceRef(item.value('finance_id'))
            batch = forceString(item.value('batch'))
            unitId = forceRef(item.value('unit_id'))
            return self._getBatchEditorItems(nomenclatureId, financeId, batch, unitId)
        return [u'']


    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid():
            return False

        if role == Qt.EditRole:

            col = index.column()
            row = index.row()

            if col == self.getColIndex('nomenclature_id'):
                if 0 <= row < len(self._items):
                    oldNomenclatureId = forceRef(self._items[row].value('nomenclature_id'))
                else:
                    oldNomenclatureId = None
                result = CNomenclatureItemsBaseModel.setData(self, index, value, role)
                if result:
                    item = self._items[row]
                    nomenclatureId = forceRef(item.value('nomenclature_id'))
                    if oldNomenclatureId != nomenclatureId:
                        unitId = self.getDefaultStockUnitId(nomenclatureId)
                        item.setValue('unit_id', toVariant(unitId))
                        self.emitRowChanged(row)
                return result
            elif col == self.getColIndex('batch'):
                result = CNomenclatureItemsBaseModel.setData(self, index, value, role)
                if not result:
                    return False
                item = self._items[row]
                nomenclatureId = forceRef(item.value('nomenclature_id'))
                financeId = forceRef(item.value('finance_id'))# if QtGui.qApp.controlSMFinance() in (1, 2) else None
                batch = forceString(item.value('batch'))
                if batch:
                    batch, shelfTime, finance, medicalAidKind, price = getBatchShelfTimeFinance(nomenclatureId, financeId, batch=batch)
                else:
                    shelfTime, finance, medicalAidKind, price = (None, None, None, 0)
                item.setValue('shelfTime', toVariant(shelfTime))
                item.setValue('finance_id', toVariant(finance))
                item.setValue('medicalAidKind_id', toVariant(medicalAidKind))
                if price:
                    unitId = forceRef(item.value('unit_id'))
                    ratio = self.getRatio(nomenclatureId, unitId, None)
                    if ratio is not None:
                        price = price*ratio
                item.setValue('price', toVariant(price))
                if batch:
                    item.setValue('sum', toVariant(forceDouble(item.value('qnt')) * forceDouble(item.value('price'))))
                    item.setValue('oldSum', toVariant(forceDouble(item.value('oldQnt')) * forceDouble(item.value('oldPrice'))))
                    #item.setValue('oldSum', toVariant(self.calcSum(item, qntCol='oldQnt', batch=forceString(item.value('batch')), priceCol='oldPrice')))
                else:
                    item.setValue('sum', toVariant(0.0))
                    item.setValue('oldSum', toVariant(0.0))
                self.emitRowChanged(row)
                return result
            elif col == self.getColIndex('unit_id'):
                if not (0 <= row < len(self._items)):
                    return False
                item = self._items[row]
                oldUnitId = forceRef(item.value('unit_id'))
                result = CNomenclatureItemsBaseModel.setData(self, index, value, role)
                if result:
                    newUnitId = forceRef(item.value('unit_id'))
                    self._applyQntRatio(item, oldUnitId, newUnitId)
                    newPrice = self.updatePriceByRatio(item, oldUnitId)
                    item.setValue('price', toVariant(newPrice))
                    newOldPrice = self.updatePriceByRatio(item, oldUnitId, priceCol='oldPrice')
                    item.setValue('oldPrice', toVariant(newOldPrice))
                    item.setValue('sum', toVariant(forceDouble(item.value('qnt')) * forceDouble(item.value('price'))))
                    item.setValue('oldSum', toVariant(forceDouble(item.value('oldQnt')) * forceDouble(item.value('oldPrice'))))
                    self.emitRowChanged(row)
            elif col in (self.getColIndex('qnt'), self.getColIndex('price')):
                result = CNomenclatureItemsBaseModel.setData(self, index, value, role)
                if result:
                    item = self._items[row]
                    item.setValue('sum', toVariant(forceDouble(item.value('qnt')) * forceDouble(item.value('price'))))
                    #item.setValue('sum', toVariant(self.calcSum(item, qntCol='qnt', batch=forceString(item.value('batch')))))
            elif col == self.getColIndex('oldQnt'):
                result = CNomenclatureItemsBaseModel.setData(self, index, value, role)
                if result:
                    item = self._items[row]
                    item.setValue('oldSum', toVariant(forceDouble(item.value('oldQnt')) * forceDouble(item.value('oldPrice'))))
                    #item.setValue('oldSum', toVariant(self.calcSum(item, qntCol='oldQnt', batch=forceString(item.value('batch')), priceCol='oldPrice')))
            elif col == self.getColIndex('sum'):
                result = CNomenclatureItemsBaseModel.setData(self, index, value, role)
                if result:
                    item = self._items[row]
                    qnt = forceDouble(item.value('qnt'))
                    item.setValue('price', toVariant(forceDouble(item.value('sum'))/qnt) if qnt else 0.0)
            else:
                return CNomenclatureItemsBaseModel.setData(self, index, value, role)
        else:
            return CNomenclatureItemsBaseModel.setData(self, index, value, role)
        return result


    def _applyQntRatio(self, item, oldUnitId, newUnitId, sumCol='sum', qntCol='qnt'):
        CNomenclatureItemsBaseModel._applyQntRatio(self, item, oldUnitId, newUnitId, qntCol='qnt')
        CNomenclatureItemsBaseModel._applyQntRatio(self, item, oldUnitId, newUnitId, qntCol='oldQnt')


    def fill(self, orgStructureId, filter):
        stmt = getExistsNomenclatureStmt(orderBy = u'rbNomenclature.name', otherHaving=[u'qnt!=0'], inventoryFillFilter=filter)
        query = QtGui.qApp.db.query(stmt)
        while query.next():
            record = query.record()
            nomenclatureId = forceRef(record.value('nomenclature_id'))
            unitId = self.getDefaultStockUnitId(nomenclatureId)
            myItem = self.getEmptyRecord()
            myItem.setValue('nomenclature_id', toVariant(nomenclatureId))
            myItem.setValue('unit_id',         toVariant(unitId))
            myItem.setValue('finance_id',      record.value('finance_id'))
            myItem.setValue('medicalAidKind_id',      record.value('medicalAidKind_id'))
            myItem.setValue('batch',           record.value('batch'))
            myItem.setValue('shelfTime',       record.value('shelfTime'))
            myItem.setValue('qnt',             record.value('qnt'))
            myItem.setValue('price',           record.value('price'))
            myItem.setValue('sum',             record.value('sum'))
            myItem.setValue('oldQnt',          record.value('qnt'))
            myItem.setValue('oldPrice',        record.value('price'))
            myItem.setValue('oldSum',          record.value('sum'))
            self.items().append(myItem)
        self.reset()


class CStockInventoryCommissionModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self,
            'StockMotion_CommissionComposition', 'id', 'master_id', parent)
        self.addCol(CInDocTableCol(u'№', 'idx', 5).setReadOnly())
        self.addCol(CEnumInDocTableCol(u'Должность', 'post', 25,
            [u'Утверждающий', u'Председатель', u'Член комиссии']))
        self.addCol(CRBInDocTableCol(u'Сотрудник', 'person_id', 35,
            'vrbPersonWithSpecialityAndOrgStr', filter='code != ""'))
        self.dataChanged.connect(self.enumerateItems)


    def loadItems(self, masterId):
        CInDocTableModel.loadItems(self, masterId)
        self.enumerateItems(None, None)


    def enumerateItems(self, topLeft, bottomRight, roles=None):
        for i, record in enumerate(self._items):
            record.setValue('idx', toVariant(i + 1))
