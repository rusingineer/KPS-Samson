# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2023 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################
from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QVariant, pyqtSignature, QString

from library.crbcombobox            import CRBComboBox
from library.InDocTable             import CDateInDocTableCol, CInDocTableCol, CRBInDocTableCol, CInDocTableModel, CFloatInDocTableCol
from library.interchange            import getDatetimeEditValue, getLineEditValue, getRBComboBoxValue, setDatetimeEditValue, setLineEditValue, setRBComboBoxValue
from library.ItemsListDialog        import CItemEditorBaseDialog
from library.PrintTemplates         import getPrintButton, applyTemplate
from library.PrintInfo              import CInfoContext, CDateInfo, CTimeInfo
from Orgs.Utils                     import COrgStructureInfo
from Orgs.PersonInfo                import CPersonInfo
from library.Utils                  import forceRef, forceString, toVariant, forceDate, forceDouble, pyDate
from Stock.NomenclatureComboBox     import CNomenclatureInDocTableCol
from Stock.StockMotionBaseDialog    import CStockMotionBaseDialog, CNomenclatureItemsBaseModel
from Stock.StockBatchEditor         import CStockBatchEditor
from Stock.Utils                    import CSummaryInfoModelMixin, getNomenclatureUnitRatio, getExistsNomenclatureStmt, getStockMotionItemQntEx, getExistsNomenclatureAmountEx
from Stock.Service                  import CStockService
from Stock.StockModel               import CStockMotionType
from Stock.StockMotionInfo          import CStockMotionItemInfo

from Stock.Ui_StockResidualQuantityWriteDownDialog import Ui_StockResidualQuantityWriteDownDialog


class CStockResidualQuantityWriteDownEditDialog(CStockMotionBaseDialog, Ui_StockResidualQuantityWriteDownDialog):
    stockDocumentType = CStockMotionType.residualQuantityWriteDown

    def __init__(self,  parent):
        CStockMotionBaseDialog.__init__(self, parent)
        self.addModels('Items', CResidualQuantityWriteDownItemsModel(self))
        self.addObject('btnPrint', getPrintButton(self, 'StockResidualQuantityWriteDown'))
        self.btnPrint.setShortcut('F6')
        self.setupUi(self)
        self.cmbSupplierPerson.setSpecialityIndependents()
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setupDirtyCather()
        self.buttonBox.addButton(self.btnPrint, QtGui.QDialogButtonBox.ActionRole)
        self.tblItems.setModel(self.modelItems)
        self.prepareItemsPopupMenu(self.tblItems)
        self.tblItems.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.tblItems.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.setWindowTitleEx(u'Списание остаточных количеств')
        self.tblItems.enableColsMove()


    def prepareItemsPopupMenu(self, tblWidget):
        tblWidget.addPopupDelRow()


    @pyqtSignature('int')
    def on_btnPrint_printByTemplate(self, templateId):
        data = self.getStockResidualQuantityWriteDownInfo()
        QtGui.qApp.call(self, applyTemplate, (self, templateId, data))


    def getStockResidualQuantityWriteDownInfo(self):
        itemsList = []
        context = CInfoContext()
        if hasattr(self, 'modelItems'):
            for record in self.modelItems.items():
                item = CStockMotionItemInfo(context, forceRef(record.value('id')))
                item.loadFromRecord(record)
                itemsList.append(item)
        data = {
            'rows': itemsList,
            'number': unicode(self.edtNumber.text()),
            'date': CDateInfo(self.edtDate.date()),
            'time': CTimeInfo(self.edtTime.time()),
            'supplier': COrgStructureInfo(context, self.cmbSupplier.value()),
            'supplierPerson' : CPersonInfo(context, self.cmbSupplierPerson.value()),
            'note': unicode(self.edtNote.text()),
        }
        return data



    def saveInternals(self, id):
        self.modelItems.saveItems(id)


    def setRecord(self, record):
        CItemEditorBaseDialog.setRecord(self, record)
        setLineEditValue(    self.edtNumber,          record, 'number')
        setDatetimeEditValue(self.edtDate, self.edtTime, record, 'date')
        setRBComboBoxValue(  self.cmbSupplier,        record, 'supplier_id')
        setRBComboBoxValue(  self.cmbSupplierPerson,  record, 'supplierPerson_id')
        setLineEditValue(    self.edtNote,            record, 'note')
        self.modelItems.loadItems(self.itemId())
        self.modelItems.setStockMotion(CStockService.getStockMotionByRecord(record))
        self.setIsDirty(False)
        self.lblSummaryInfo.setText(self.modelItems.getSummaryInfo())


    def getRecord(self):
        record = CItemEditorBaseDialog.getRecord(self)
        getLineEditValue(   self.edtNumber,         record, 'number')
        getDatetimeEditValue(self.edtDate, self.edtTime, record, 'date', True)
        getRBComboBoxValue( self.cmbSupplier,       record, 'supplier_id')
        getRBComboBoxValue( self.cmbSupplierPerson, record, 'supplierPerson_id')
        getLineEditValue(   self.edtNote,           record, 'note')
        record.setValue('type', self.stockDocumentType)
        return record


    def fill(self):
        orgStructureId = self.cmbSupplier.value()
        if orgStructureId:
            self.modelItems.fill(orgStructureId)
            self.lblSummaryInfo.setText(self.modelItems.getSummaryInfo())
        return len(self.modelItems.items())


#    @pyqtSignature('QModelIndex')
#    def on_tblItems_doubleClicked(self, index):
#        if index and index.isValid():
#            col = index.column()
#            if col in (CResidualQuantityWriteDownItemsModel.batchColumnIndex, CResidualQuantityWriteDownItemsModel.shelfTimeColumnIndex, CResidualQuantityWriteDownItemsModel.financeColumnIndex, CResidualQuantityWriteDownItemsModel.medicalAidKindColumnIndex):
#                items = self.modelItems.items()
#                currentRow = index.row()
#                if 0 <= currentRow < len(items):
#                    item = items[currentRow]
#                    try:
#                        params = {}
#                        params['nomenclatureId'] = forceRef(item.value('nomenclature_id'))
#                        params['batch'] = forceString(item.value('batch'))
#                        params['financeId'] = forceRef(item.value('finance_id'))
#                        params['shelfTime'] = forceDate(item.value('shelfTime'))
#                        params['medicalAidKindId'] = forceRef(item.value('medicalAidKind_id'))
#                        dialog = CStockBatchEditor(self, params)
#                        dialog.loadData()
#                        if dialog.exec_():
#                            outBatch, outFinanceId, outShelfTime, outMedicalAidKindId, outPrice = dialog.getValue()
#                            item.setValue('batch', toVariant(outBatch))
#                            item.setValue('finance_id', toVariant(outFinanceId))
#                            item.setValue('shelfTime', toVariant(outShelfTime))
#                            item.setValue('medicalAidKind_id', toVariant(outMedicalAidKindId))
#                            if outPrice:
#                                unitId = forceRef(item.value('unit_id'))
#                                nomenclatureId = forceRef(item.value('nomenclature_id'))
#                                ratio = self.modelItems.getRatio(nomenclatureId, unitId, None)
#                                if ratio is not None:
#                                    outPrice = outPrice*ratio
#                            item.setValue('price', toVariant(outPrice))
#                            item.setValue('sum', toVariant(forceDouble(item.value('qnt')) * forceDouble(item.value('price'))))
#                            self.modelItems.reset()
#                    finally:
#                        dialog.destroy()
#                        sip.delete(dialog)
#                        del dialog
#            else:
#                self.emit(SIGNAL('doubleClicked(QModelIndex)'), index)


    def checkDataEntered(self):
        result = self._checkStockMotionItemsData(self.tblItems)
        result = result and self.checkItemsDataEntered()
        return result


    def _checkStockMotionItemsData(self, tblItems):
        model = tblItems.model()
        items = model.items()
        for idx, item in enumerate(items):
            unitId = forceRef(item.value('unit_id'))
            if not unitId:
                return self.checkValueMessage(u'Необходимо указать Ед.Учета!', False, tblItems, idx, model.getColIndex('unit_id'))
        return True


    def checkItemsDataEntered(self):
        supplierId = self.cmbSupplier.value()
        existsNomenclatureAmountDict = {}
        db = QtGui.qApp.db
        for row, item in enumerate(self.modelItems.items()):
            financeId = forceRef(item.value('finance_id'))
            batch = forceString(item.value('batch'))
            shelfTime = pyDate(forceDate(item.value('shelfTime')))
            shelfTimeString = forceString(item.value('shelfTime'))
            medicalAidKindId = forceRef(item.value('medicalAidKind_id'))
            medicalAidKindName = forceString(db.translate('rbMedicalAidKind', 'id', medicalAidKindId, 'name'))
            nomenclatureId = forceRef(item.value('nomenclature_id'))
            unitId = forceRef(item.value('unit_id'))
            price = forceDouble(item.value('price'))
            qnt = forceDouble(item.value('qnt'))
            stockUnitId = self.modelItems.getDefaultStockUnitId(nomenclatureId)
            ratio = self.modelItems.getRatio(nomenclatureId, stockUnitId, unitId)
            if ratio is not None:
                price = price*ratio
                qnt = qnt / ratio
            existsNomenclatureAmountLine = existsNomenclatureAmountDict.get((nomenclatureId, financeId, batch, supplierId, stockUnitId, medicalAidKindId, shelfTime, price), [0, shelfTimeString, medicalAidKindName, []])
            existsNomenclatureAmountLine[0] = existsNomenclatureAmountLine[0]  + qnt
            existsNomenclatureAmountLine[3].append(row)
            existsNomenclatureAmountDict[(nomenclatureId, financeId, batch, supplierId, stockUnitId, medicalAidKindId, shelfTime, price)] = existsNomenclatureAmountLine
        for keys, item in existsNomenclatureAmountDict.items():
            if supplierId and not self.checkNomenclatureExists(keys, item, supplierId):
                return False
        return True


    def checkNomenclatureExists(self, keys, item, supplierId=None):
        db = QtGui.qApp.db
        nomenclatureId, financeId, batch, supplierId, stockUnitId, medicalAidKindId, shelfTimePyDate, price = keys
        shelfTime = forceDate(shelfTimePyDate)
        supplierId = supplierId or self.cmbSupplier.value()
        qnt = item[0]
        shelfTimeString = item[1]
        medicalAidKindName = item[2]
        rows = item[3]
        row = rows[0] if len(rows) > 0 else -1
        existsQnt = getExistsNomenclatureAmountEx(nomenclatureId, financeId, batch, supplierId, stockUnitId, medicalAidKindId, shelfTime, exact=True, price=price)
        prevQnt = round(getStockMotionItemQntEx(nomenclatureId, stockMotionId=self._id, batch=batch, financeId=financeId, medicalAidKindId=medicalAidKindId, price=None, oldPrice=price, oldUnitId=stockUnitId), QtGui.qApp.numberDecimalPlacesQnt()) if self._id else 0
        if (round(existsQnt, QtGui.qApp.numberDecimalPlacesQnt()) + prevQnt) - round(qnt, QtGui.qApp.numberDecimalPlacesQnt()) < 0:
            nomenclatureName = self.modelItems.getNomenclatureNameById(nomenclatureId)
            if existsQnt > 0:
                message = u'На складе {0} {7} {1} партии "{3}" годный до "{4}" типа финансирования "{5}" вида мед помощи "{6}", а списание на {2}'.format(   existsQnt,
                                                                                                                                                    nomenclatureName,
                                                                                                                                                    qnt,
                                                                                                                                                    batch if batch else u'не указано',
                                                                                                                                                    shelfTimeString if shelfTime else u'не указано',
                                                                                                                                                    forceString(db.translate('rbFinance', 'id', financeId, 'name')) if financeId else u'не указано',
                                                                                                                                                    medicalAidKindName if medicalAidKindName else u'не указано',
                                                                                                                                                    forceString(db.translate('rbUnit', 'id', stockUnitId, 'name')))
            else:
                message = u'На складе отсутствует "{1}" партии "{3}" годный до "{4}" типа финансирования "{5}" вида мед помощи "{6}"'.format(   existsQnt,
                                                                                                                                        nomenclatureName,
                                                                                                                                        qnt,
                                                                                                                                        batch if batch else u'не указано',
                                                                                                                                        shelfTimeString if shelfTime else u'не указано',
                                                                                                                                        forceString(db.translate('rbFinance', 'id', financeId, 'name')) if financeId else u'не указано',
                                                                                                                                        medicalAidKindName if medicalAidKindName else u'не указано')
            return self.checkValueMessage(message, False, self.tblItems, row, self.modelItems.qntColumnIndex)
        return True


    def _on_cmbSupplierChanged(self):
        if not self._record:
            self._record = self.getRecord()
            self.modelItems.setStockMotion(CStockService.getStockMotionByRecord(self._record))
        self._record.setValue('supplier_id', self.cmbSupplier.value())


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_modelItems_dataChanged(self,  topLeftIndex, bottomRightIndex):
        self.lblSummaryInfo.setText(self.modelItems.getSummaryInfo())


class CLocNomenclatureCol(CNomenclatureInDocTableCol):
    def __init__(self, title, fieldName, width, **params):
        CNomenclatureInDocTableCol.__init__(self, title, fieldName, width, **params)


    def createEditor(self, parent):
        editor = CNomenclatureInDocTableCol.createEditor(self, parent)
        editor.setOrgStructureId(QtGui.qApp.currentOrgStructureId())
        editor.setOnlyExists()
        return editor


class CLocItemsModel(CNomenclatureItemsBaseModel, CSummaryInfoModelMixin):
    nomenclatureColumnIndex = 0
    batchColumnIndex = 1
    shelfTimeColumnIndex = 2
    financeColumnIndex = 3
    medicalAidKindColumnIndex = 4
    oldQntColumnIndex = 5
    oldSumColumnIndex = 6
    unitColumnIndex = 7
    qntColumnIndex = 8
    sumColumnIndex = 9
    existsColumnIndex = 10

    class CSumCol(CFloatInDocTableCol):
        def _toString(self, value):
            if value.isNull():
                return None
            return format(forceDouble(value), '.2f')

    def __init__(self, parent, showExists=False):
        CNomenclatureItemsBaseModel.__init__(self, parent)
        self.setEnableAppendLine(False)
        self.priceCache = parent
        self._financeCache = {}
        self._shelfTimeCache = {}
        self._setterHandlers = {
            self.nomenclatureColumnIndex: self._handleNomenclatureSet,
            self.unitColumnIndex: self._handleUnitIdSet,
            self.qntColumnIndex: self._handleQntSet
        }
        self._stockMotion = None


    def setStockMotion(self, stockMotion):
        self._stockMotion = stockMotion


    def _handleNomenclatureSet(self, stockMotionItem, value):
        previousValue = stockMotionItem.nomenclature_id
        stockMotionItem.nomenclature_id = value
        if previousValue != stockMotionItem.nomenclature_id:
            CStockService.setFinanceBatchShelfTime(stockMotionItem, setShelfTimeCond = True)
            stockMotionItem.unit_id = self.getDefaultClientUnitId(stockMotionItem.nomenclature_id)
            price = stockMotionItem.price
            unitId = stockMotionItem.unit_id
            nomenclatureId = stockMotionItem.nomenclature_id
            if price and unitId and nomenclatureId:
                ratio = self.getRatio(nomenclatureId, unitId, None)
                if ratio is not None:
                    stockMotionItem.price = price*ratio
            stockMotionItem.qnt = 1.0
            stockMotionItem.setSum(stockMotionItem.qnt * stockMotionItem.price)
            return True
        return False


    def _handleUnitIdSet(self, stockMotionItem, value):
        previousValue = stockMotionItem.unit_id
        stockMotionItem.unit_id = value
        if previousValue != stockMotionItem.unit_id:
            ratio = self.getRatio(stockMotionItem.nomenclature_id, stockMotionItem.unit_id, previousValue)
            if ratio is not None:
                stockMotionItem.qnt = stockMotionItem.qnt / ratio
                newPrice = stockMotionItem.price * ratio
                stockMotionItem.price = newPrice
                stockMotionItem.setSum(stockMotionItem.qnt * stockMotionItem.price)
            else:
                stockMotionItem.unit_id = previousValue
            return True
        return False


    def _handleQntSet(self, stockMotionItem, value):
        result = stockMotionItem.setQnt(value)
        if result:
            stockMotionItem.setSum(stockMotionItem.qnt * stockMotionItem.price)
        return True


    def _handlePriceSet(self, stockMotionItem, value):
        result = stockMotionItem.setPrice(value)
        if result:
            stockMotionItem.setSum(stockMotionItem.qnt * stockMotionItem.price)
        return True


    def setData(self, index, value, role=Qt.EditRole):
        if role != Qt.EditRole:
            return CNomenclatureItemsBaseModel.setData(self, index, value, role)
        columnIndex = index.column()
        if columnIndex in self._setterHandlers.keys():
            row = index.row()
            if row == len(self._items):
                if value.isNull():
                    return False
                self._addEmptyItem()
            stockMotionItem = CStockService(self._stockMotion).getStockMotionItemByRecord(self._items[index.row()])
            if columnIndex == self.getColIndex('qnt'):
                if not (0 <= row < len(self._items)):
                    return False
                item = self._items[row]
                id = forceRef(item.value('id'))
                prevQnt = 0
                if id:
                    db = QtGui.qApp.db
                    tableSMI = db.table('StockMotion_Item')
                    recordPrevQnt = db.getRecordEx(tableSMI, [tableSMI['qnt']], [tableSMI['id'].eq(id), tableSMI['deleted'].eq(0)])
                    prevQnt = forceDouble(recordPrevQnt.value('qnt')) if recordPrevQnt else 0
                existsColumn = forceDouble(self._cols[self.existsColumnIndex].getExistsValue(item))
                existsColumn = existsColumn + prevQnt
                if not self.isPriceLineEditable and forceDouble(item.value('price')) and (not existsColumn or existsColumn < 0):
                   return False
                if not self.isPriceLineEditable and forceDouble(item.value('price')) and existsColumn < forceDouble(value):
                    value = toVariant(existsColumn)
            if self._setterHandlers[columnIndex](stockMotionItem, value):
                self.setIsUpdateValue(True)
                if (0 <= row < len(self._items)):
                    item = self._items[row]
                    if columnIndex == self.getColIndex('qnt'):
                        item.setValue('prevQnt', prevQnt)
                self.emitRowChanged(index.row())
                return True
            return False
        elif columnIndex in (self.batchColumnIndex, self.shelfTimeColumnIndex, self.financeColumnIndex, self.medicalAidKindColumnIndex):
            return False
        else:
            CNomenclatureItemsBaseModel.setData(self, index, value, role)


    def getNomenclatureNameById(self, nomenclatureId):
        return forceString(self._nomenclatureColumn.toString(nomenclatureId, None))


    def _getNomenclatureFinanceIdList(self, record, nomenclatureId):
        stockMotionItem = CStockService(self._stockMotion).getStockMotionItemByRecord(record)
        if stockMotionItem.id not in self._financeCache:
            financeIdList = CStockService.getFinanceIdListDependOnBatchAndShelfTime(stockMotionItem)
            self._financeCache[stockMotionItem.id] = financeIdList
        return self._financeCache[stockMotionItem.id]


    def _setSuitableFinanceValue(self, item, nomenclatureId, oldNomenclatureId):
        if nomenclatureId != oldNomenclatureId:
            for financeId in self._getNomenclatureFinanceIdList(item, nomenclatureId):
                if financeId:
                    item.setValue('finance_id', QVariant(financeId))
                    return True
            item.setValue('finance_id', QVariant(None))
            return True
        return False


    def getEmptyRecord(self):
        record = CNomenclatureItemsBaseModel.getEmptyRecord(self)
        record.setValue('qnt', QVariant(1))
        return record


    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled


class CResidualQuantityWriteDownItemsModel(CLocItemsModel):
    nomenclatureColumnIndex = 0
    batchColumnIndex = 1
    shelfTimeColumnIndex = 2
    financeColumnIndex = 3
    medicalAidKindColumnIndex = 4
    oldQntColumnIndex = 5
    oldSumColumnIndex = 6
    unitColumnIndex = 7
    qntColumnIndex = 8
    sumColumnIndex = 9
    existsColumnIndex = 10

    class CQuantityCol(CFloatInDocTableCol):
        def __init__(self, title, fieldName, width, **params):
            CFloatInDocTableCol.__init__(self, title, fieldName, width, **params)

        def _toString(self, value):
            s = QString()
            if value.isNull():
                return s
            if self.precision is None:
                s.setNum(value.toDouble()[0])
            else:
                s.setNum(value.toDouble()[0], 'f', self.precision)
            return s

        def createEditor(self, parent):
            editor = QtGui.QLineEdit(parent)
            validator = QtGui.QDoubleValidator(editor)
            validator.setRange(self.low, self.high)
            editor.setValidator(validator)
            return editor

        def setEditorData(self, editor, value, record):
            s = QString()
            if not value.isNull():
                s = value.toString()
            editor.setText('' if s is None else s)
            editor.selectAll()

    class CLocFloatCol(CFloatInDocTableCol):
        def _toString(self, value):
            if value.isNull():
                return None
            return format(forceDouble(value), '.2f')

    def __init__(self, parent, showExists=False):
        CLocItemsModel.__init__(self, parent)
        self._nomenclatureColumn = CLocNomenclatureCol(u'ЛСиИМН', 'nomenclature_id', 50, showFields = CRBComboBox.showName).setReadOnly()
        self._batchCol = CInDocTableCol(u'Серия', 'batch', 16).setReadOnly()
        self._unitColumn = CRBInDocTableCol(u'Ед.Учета', 'unit_id', 12, 'rbUnit', addNone=False).setReadOnly()
        self.addCol(self._nomenclatureColumn)
        self.addCol(self._batchCol)
        self.addCol(CDateInDocTableCol( u'Годен до', 'shelfTime', 12, canBeEmpty=True).setReadOnly())
        self.addCol(CRBInDocTableCol(   u'Тип финансирования', 'finance_id', 15, 'rbFinance').setReadOnly())
        self.addCol(CRBInDocTableCol(   u'Вид медицинской помощи', 'medicalAidKind_id', 15, 'rbMedicalAidKind').setReadOnly())
        self.addCol(CFloatInDocTableCol(u'Кол-во по документам', 'oldQnt', 12, low=1, high=65535).setReadOnly())
        self.addCol(self.CLocFloatCol(u'Сумма по документам', 'oldSum', 12).setReadOnly())
        self.addCol(self._unitColumn)
        self.addCol(self.CQuantityCol(  u'Фактическое кол-во', 'qnt', 12, low=1, high=65535, precision=QtGui.qApp.numberDecimalPlacesQnt()).setReadOnly())
        sumCol = self.CSumCol( u'Фактическая сумма', 'sum', 12)
        self.addCol(sumCol.setReadOnly())
        self.existsCol = self.CExistsCol(self)
        self.addExtCol(self.existsCol.setReadOnly(), QVariant.Double)
        self.setStockDocumentTypeExistsCol()
        self.addHiddenCol('price')
        self.addHiddenCol('oldPrice')


    def getExistsValue(self, record):
        if not record:
            return 0
        return self.existsCol.getExistsValue(record)


    def createEditor(self, index, parent):
        editor = CInDocTableModel.createEditor(self, index, parent)
        column = index.column()
        if column == self.nomenclatureColumnIndex:
            editor.setOnlyExists(True)
            filterSetter = getattr(editor, 'setOrgStructureId', None)
            if not filterSetter:
                return editor
            if not editor._stockOrgStructureId:
                filterSetter(getattr(self, '_supplierId', None))
            editor.getFilterData()
            editor.setFilter(editor._filter)
            editor.reloadData()
        elif column == self.unitColumnIndex:
            self._setUnitEditorFilter(index.row(), editor)
        return editor


    def fill(self, orgStructureId):
        minQntConsumable = QtGui.qApp.minQntConsumableUnitsStock()
        stmt = getExistsNomenclatureStmt(orderBy = u'rbNomenclature.name', otherHaving=[u'qnt!=0'])
        query = QtGui.qApp.db.query(stmt)
        while query.next():
            record = query.record()
            qnt = forceDouble(record.value('qnt'))
            defaultQntUnitId = qnt
            nomenclatureId = forceRef(record.value('nomenclature_id'))
            defaultStockUnitId = self.getDefaultStockUnitId(nomenclatureId)
            defaultClientUnitId = self.getDefaultClientUnitId(nomenclatureId)
            if defaultStockUnitId is not None and defaultClientUnitId is not None:
                ratio = getNomenclatureUnitRatio(nomenclatureId, defaultStockUnitId, defaultClientUnitId)
                if ratio not in (1, None):
                    defaultQntUnitId = defaultQntUnitId * ratio
                if minQntConsumable > abs(defaultQntUnitId):
                    myItem = self.getEmptyRecord()
                    myItem.setValue('nomenclature_id', toVariant(nomenclatureId))
                    myItem.setValue('unit_id',         toVariant(defaultStockUnitId))
                    myItem.setValue('finance_id',      record.value('finance_id'))
                    myItem.setValue('medicalAidKind_id', record.value('medicalAidKind_id'))
                    myItem.setValue('batch',           record.value('batch'))
                    myItem.setValue('shelfTime',       record.value('shelfTime'))
    #                myItem.setValue('qnt',             toVariant(qnt))
                    myItem.setValue('qnt',             toVariant(0))
                    myItem.setValue('price',           record.value('price'))
    #                myItem.setValue('sum',             record.value('sum'))
                    myItem.setValue('sum',             toVariant(0))
                    myItem.setValue('oldQnt',          toVariant(qnt))
                    myItem.setValue('oldPrice',        record.value('price'))
                    myItem.setValue('oldSum',          record.value('sum'))
                    self.items().append(myItem)
        self.reset()

