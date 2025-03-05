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
from PyQt4.QtCore import Qt, QDateTime, pyqtSignature, QVariant, SIGNAL

from library.crbcombobox         import CRBComboBox
from library.InDocTable          import CDateInDocTableCol, CFloatInDocTableCol, CInDocTableCol, CRBInDocTableCol
from library.interchange         import getRBComboBoxValue
from library.PrintInfo           import CInfoContext
from library.PrintTemplates      import applyTemplate, CPrintAction, CPrintButton, getPrintTemplates
from library.Utils               import forceString, forceRef, forceDate, toVariant, forceDouble, pyDate

from Reports.ReportBase          import CReportBase, createTable
from Reports.ReportView          import CReportViewDialog
from Stock.NomenclatureComboBox  import CNomenclatureInDocTableCol
from Stock.StockMotionBaseDialog import CStockMotionBaseDialog, CStockMotionItemsCopyPasteMixin, CNomenclatureItemsBaseModel
from Stock.Service               import CStockService
from Stock.StockBatchEditor      import CStockBatchEditor
from Stock.Utils                 import CSummaryInfoModelMixin, CPriceItemDelegate, getStockMotionItemQuantityColumn, getBatchShelfTimeFinance, getExistsNomenclatureAmountEx, getStockMotionItemQntEx

from Stock.Ui_FinTransfer import Ui_FinTransferDialog


class CFinTransferEditDialog(CStockMotionBaseDialog, CStockMotionItemsCopyPasteMixin, Ui_FinTransferDialog):
    stockDocumentType = 2 #Финансовая переброска

    def __init__(self,  parent):
        CStockMotionBaseDialog.__init__(self, parent)
        CStockMotionItemsCopyPasteMixin.__init__(self, parent)
        self.addModels('Items', CItemsModel(self))
        self.addObject('btnPrint', CPrintButton(self, u'Печать'))
        self.addObject('actOpenStockBatchEditor', QtGui.QAction(u'Подобрать параметры', self))
        self.btnPrint.setShortcut('F6')
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
        self.prepareItemsPopupMenu(self.tblItems)
        self.tblItems.popupMenu().addSeparator()
        self.tblItems.popupMenu().addAction(self.actOpenStockBatchEditor)
        self.tblItems.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.tblItems.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.tblItems.setItemDelegateForColumn(CItemsModel.priceColumnIndex, CPriceItemDelegate(self.tblItems))
        self._initView()


    @pyqtSignature('')
    def on_actOpenStockBatchEditor_triggered(self):
        self.on_tblItems_doubleClicked(self.tblItems.currentIndex())


    @pyqtSignature('QModelIndex')
    def on_tblItems_doubleClicked(self, index):
        if index and index.isValid():
            col = index.column()
            if col in (CItemsModel.batchColumnIndex, CItemsModel.shelfTimeColumnIndex, CItemsModel.financeColumnIndex, CItemsModel.medicalAidKindColumnIndex):
                items = self.modelItems.items()
                currentRow = index.row()
                if 0 <= currentRow < len(items):
                    item = items[currentRow]
                    try:
                        params = {}
                        params['nomenclatureId'] = forceRef(item.value('nomenclature_id'))
                        params['batch'] = forceString(item.value('batch'))
                        params['financeId'] = forceRef(item.value('oldFinance_id'))
                        params['shelfTime'] = forceDate(item.value('shelfTime'))
                        params['medicalAidKindId'] = forceRef(item.value('oldMedicalAidKind_id'))
                        dialog = CStockBatchEditor(self, params)
                        dialog.loadData()
                        if dialog.exec_():
                            outBatch, outFinanceId, outShelfTime, outMedicalAidKindId, outPrice = dialog.getValue()
                            item.setValue('batch', toVariant(outBatch))
                            item.setValue('oldFinance_id', toVariant(outFinanceId))
                            item.setValue('shelfTime', toVariant(outShelfTime))
                            item.setValue('oldMedicalAidKind_id', toVariant(outMedicalAidKindId))
                            item.setValue('finance_id', toVariant(None))
                            item.setValue('medicalAidKind_id', toVariant(None))
                            if outPrice:
                                unitId = forceRef(item.value('unit_id'))
                                nomenclatureId = forceRef(item.value('nomenclature_id'))
                                ratio = self.modelItems.getRatio(nomenclatureId, unitId, None)
                                if ratio is not None:
                                    outPrice = outPrice*ratio
                            item.setValue('price', toVariant(outPrice))
                            try:
                                item.setValue('sum', toVariant(forceDouble(item.value('qnt')) * forceDouble(item.value('price'))))
                            except:
                                item.setValue('sum', toVariant(0.0))
                            self.modelItems.reset()
                    finally:
                        dialog.deleteLater()
            else:
                self.emit(SIGNAL('doubleClicked(QModelIndex)'), index)


    def _on_cmbSupplierChanged(self):
        if not self._record:
            self._record = self.getRecord()
            self.modelItems.setStockMotion(CStockService.getStockMotionByRecord(self._record))

        self._record.setValue('supplier_id', self.cmbSupplier.value())

    def setDefaults(self):
        CStockMotionBaseDialog.setDefaults(self)


    @pyqtSignature('int')
    def on_btnPrint_printByTemplate(self, templateId):
        self.actPrintMotions(templateId)


    def actPrintMotions(self, templateId):
        from Stock.StockMotionInfo import CStockMotionInfoList
        if templateId == -1:
            self.getNomenclaturePrint()
        else:
            idList = self.tblItems.model().itemIdList()
            context = CInfoContext()
            data = { 'FinTransferList': CStockMotionInfoList(context, idList)}
            QtGui.qApp.call(self, applyTemplate, (self, templateId, data))


    def getStockContext(self):
        return ['FinTransferList']


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


    def setRecord(self, record):
        CStockMotionBaseDialog.setRecord(self, record)
        self.modelItems.loadItems(self.itemId())
        self.modelItems.setStockMotion(CStockService.getStockMotionByRecord(record))
        self.setIsDirty(False)
        self.lblSummaryInfo.setText(self.modelItems.getSummaryInfo())


    def getRecord(self):
        record = CStockMotionBaseDialog.getRecord(self)
        getRBComboBoxValue( self.cmbSupplier, record, 'receiver_id')
        getRBComboBoxValue( self.cmbSupplierPerson, record, 'receiverPerson_id')
        record.setValue('type', 2)
        return record


    def saveInternals(self, id):
        self.modelItems.saveItems(id)


    def checkDataEntered(self):
        result = self._checkStockMotionItemsData(self.tblItems)
        result = result and self.checkItemsDataEntered()
        return result

    def checkItemsDataEntered(self):
        if hasattr(self, 'cmbSupplier'):
            supplierId = self.cmbSupplier.value()
            existsNomenclatureAmountDict = {}
            db = QtGui.qApp.db
            for row, item in enumerate(self.modelItems.items()):
                financeId = forceRef(item.value('oldFinance_id'))
                batch = forceString(item.value('batch'))
                shelfTime = pyDate(forceDate(item.value('shelfTime')))
                shelfTimeString = forceString(item.value('shelfTime'))
                medicalAidKindId = forceRef(item.value('oldMedicalAidKind_id'))
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
        else:
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
        existsQnt = getExistsNomenclatureAmountEx(nomenclatureId, financeId, batch, supplierId, stockUnitId, medicalAidKindId, shelfTime, exact=True, otherHaving=[u'qnt!=0'], price=price)
        if self._id:
            prevQnt = round(getStockMotionItemQntEx(nomenclatureId, stockMotionId=self._id, batch=batch, financeId=financeId, medicalAidKindId=medicalAidKindId, price=None, oldPrice=price, oldUnitId=stockUnitId, financeField='oldFinance_id', medicalAidKindField='oldMedicalAidKind_id'), QtGui.qApp.numberDecimalPlacesQnt()) if self._id else 0
        else:
            prevQnt = 0
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


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_modelItems_dataChanged(self,  topLeftIndex, bottomRightIndex):
        self.lblSummaryInfo.setText(self.modelItems.getSummaryInfo())


class CLocNomenclatureCol(CNomenclatureInDocTableCol):
    def createEditor(self, parent):
        editor = CNomenclatureInDocTableCol.createEditor(self, parent)
        editor.setOrgStructureId(QtGui.qApp.currentOrgStructureId())
        editor.setOnlyExists()
        return editor


class CSumCol(CFloatInDocTableCol):
    def _toString(self, value):
        if value.isNull():
            return None
        return format(forceDouble(value), '.2f')


class CItemsModel(CNomenclatureItemsBaseModel, CSummaryInfoModelMixin):
    batchColumnIndex = 1
    shelfTimeColumnIndex = 2
    financeColumnIndex = 3
    medicalAidKindColumnIndex = 4
    qntColumnIndex = 7
    priceColumnIndex = 9
    existsColumnIndex = 11

    class CExistsCol(CFloatInDocTableCol):
        def __init__(self, model):
            CFloatInDocTableCol.__init__(self, u'Остаток', 'existsColumn', 10, precision=QtGui.qApp.numberDecimalPlacesQnt())
            self.model = model
            self._cache = {}
            self.stockDocumentType = None
            self.isUpdateValue = False

        def setIsUpdateValue(self, isUpdateValue):
            self.isUpdateValue = isUpdateValue

        def setStockDocumentType(self, stockDocumentType):
            self.stockDocumentType = stockDocumentType

        def toString(self, val, record):
            price = forceDouble(record.value('price'))
            nomenclatureId = forceRef(record.value('nomenclature_id'))
            unitId = forceRef(record.value('unit_id'))
            ratio = self.model.getRatio(nomenclatureId, None, unitId)
            if ratio is not None:
                price = price*ratio
            financeId = forceRef(record.value('oldFinance_id'))
            batch = forceString(record.value('batch'))
            shelfTime = forceDate(record.value('shelfTime'))
            shelfTime = shelfTime.toPyDate() if bool(shelfTime) else None
            medicalAidKindId = forceRef(record.value('oldMedicalAidKind_id'))
#            qnt = forceDouble(record.value('qnt'))
#            prevQnt = forceDouble(record.value('prevQnt'))
#            deltaQnt = prevQnt - qnt
            key = (nomenclatureId, financeId, batch, unitId, shelfTime, medicalAidKindId, price)
            if self.isUpdateValue:
                existsQnt = getExistsNomenclatureAmountEx(nomenclatureId, financeId, batch, unitId=unitId, medicalAidKindId = medicalAidKindId, shelfTime=shelfTime, otherHaving=[u'(shelfTime>=curDate()) OR shelfTime is NULL'], exact=True, price=price)
                self._cache[key] = existsQnt# + deltaQnt
            else:
                if key not in self._cache:
                    existsQnt = getExistsNomenclatureAmountEx(nomenclatureId, financeId, batch, unitId=unitId, medicalAidKindId = medicalAidKindId, shelfTime=shelfTime, otherHaving=[u'(shelfTime>=curDate()) OR shelfTime is NULL'], exact=True, price=price)
                    self._cache[key] = existsQnt# + deltaQnt
            self.isUpdateValue = False
            return QVariant(self._toString(QVariant(self._cache[key])))

    def __init__(self, parent):
        CNomenclatureItemsBaseModel.__init__(self, parent)
        #CNomenclatureItemsBaseModel.__init__(self, 'StockMotion_Item', 'id', 'master_id', parent)
        self._nomenclatureColumn = CLocNomenclatureCol(u'ЛСиИМН', 'nomenclature_id', 50, showFields = CRBComboBox.showName)
        self.addCol(self._nomenclatureColumn)
        self.addCol(CInDocTableCol(    u'Серия', 'batch', 16).setReadOnly())
        self.addCol(CDateInDocTableCol(u'Годен до', 'shelfTime', 12, canBeEmpty=True).setReadOnly())
        self.addCol(CRBInDocTableCol(  u'Прежний тип финансирования', 'oldFinance_id', 15, 'rbFinance').setReadOnly())
        self.addCol(CRBInDocTableCol(  u'Прежний вид медицинской помощи', 'oldMedicalAidKind_id', 15, 'rbMedicalAidKind').setReadOnly())
        self.addCol(CRBInDocTableCol(  u'Новый тип финансирования', 'finance_id', 15, 'rbFinance'))
        self.addCol(CRBInDocTableCol(  u'Новый вид медицинской помощи', 'medicalAidKind_id', 15, 'rbMedicalAidKind'))
        self.addCol(getStockMotionItemQuantityColumn( u'Кол-во', 'qnt', 12))
        unitColumn = CRBInDocTableCol( u'Ед.Учета', 'unit_id', 12, 'rbUnit', addNone=False)
        self.addCol(unitColumn)
        self.addCol(CFloatInDocTableCol(u'Цена', 'price', 12, precision=2))
        sumCol = CSumCol( u'Сумма', 'sum', 12)
        self.addCol(sumCol.setReadOnly())
        existsCol = CItemsModel.CExistsCol(self)
        self.addExtCol(existsCol.setReadOnly(), QVariant.Double)
        self.priceCache = parent
        self._stockMotion = None
        self.setStockDocumentTypeExistsCol()

    def setStockMotion(self, stockMotion):
        self._stockMotion = stockMotion


    def getNomenclatureNameById(self, nomenclatureId):
        return forceString(self._nomenclatureColumn.toString(nomenclatureId, None))


    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid():
            return False
        col = index.column()
        row = index.row()
        if col in (self.getColIndex('qnt'), self.getColIndex('price')):
            if col == self.getColIndex('qnt'):
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
                existsColumn = forceDouble(self._cols[self.existsColumnIndex].toString(value, item))
                existsColumn = existsColumn + prevQnt
                if not self.isPriceLineEditable and forceDouble(item.value('price')) and (not existsColumn or existsColumn < 0):
                   return False
                if not self.isPriceLineEditable and forceDouble(item.value('price')) and existsColumn < forceDouble(value):
                    value = toVariant(existsColumn)
            result = CNomenclatureItemsBaseModel.setData(self, index, value, role)
            if result:
                self.setIsUpdateValue(True)
                item = self._items[row]
                if col == self.getColIndex('qnt'):
                    item.setValue('prevQnt', prevQnt)
                item.setValue('sum', toVariant(forceDouble(item.value('qnt')) * forceDouble(item.value('price'))))
                self.emitRowChanged(row)
            return result
        elif col == self.getColIndex('nomenclature_id'):
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
                    batch, shelfTime, financeId, medicalAidKind, price = getBatchShelfTimeFinance(forceRef(value), medicalAidKind=forceRef(item.value('medicalAidKind_id')))
                    result = CNomenclatureItemsBaseModel.setData(self, index, value, role)
                    item.setValue('batch', toVariant(batch))
                    item.setValue('oldFinance_id', toVariant(financeId)) if financeId else item.setNull('oldFinance_id')
                    item.setValue('oldMedicalAidKind_id', toVariant(medicalAidKind)) if medicalAidKind else item.setNull('oldMedicalAidKind_id')
                    item.setValue('shelfTime', toVariant(shelfTime))
                    if price:
                        unitId = forceRef(item.value('unit_id'))
                        ratio = self.getRatio(nomenclatureId, unitId, None)
                        if ratio is not None:
                            price = price*ratio
                    item.setValue('price', toVariant(price))
                    self.emitRowChanged(row)
            return result
        elif col == self.getColIndex('unit_id'):
            if not (0 <= row < len(self._items)):
                return False
            item = self._items[row]
            oldUnitId = forceRef(item.value('unit_id'))
            result = CNomenclatureItemsBaseModel.setData(self, index, value, role)
            if result:
                self.setIsUpdateValue(True)
                newUnitId = forceRef(item.value('unit_id'))
#                self._applySumRatio(item, oldUnitId, newUnitId)
                self._applyQntRatio(item, oldUnitId, newUnitId)
                newPrice = self.updatePriceByRatio(item, oldUnitId)
                item.setValue('price', toVariant(newPrice))
                item.setValue('sum', toVariant(forceDouble(item.value('qnt')) * forceDouble(item.value('price'))))
                self.emitRowChanged(row)
        else:
            return CNomenclatureItemsBaseModel.setData(self, index, value, role)


#    def _applySumRatio(self, item, oldUnitId, newUnitId, sumCol='sum', qntCol='qnt'):
#        sum = forceDouble(item.value(sumCol))
#        qnt = forceDouble(item.value(qntCol))
#        if not qnt:
#            return
#        nomenclatureId = forceRef(item.value('nomenclature_id'))
#        ratio = self.getApplySumRatio(nomenclatureId, oldUnitId, newUnitId)
#        if ratio is None or not sum:
#            sumRes = self.getApplyCalcSum(item, batch=forceString(item.value('batch')))
#        else:
#            sumRes = sum/ratio
#        item.setValue(sumCol, toVariant(sumRes))


    def getApplyCalcSum(self, item, qntCol='qnt', batch=None):
        nomenclatureId = forceRef(item.value('nomenclature_id'))
        price = forceDouble(item.value('price'))
        qnt = forceDouble(item.value(qntCol))
        unit_id = forceRef(item.value('unit_id'))
        stockUnitId = self.getDefaultStockUnitId(nomenclatureId)
        ratio = self.getApplySumRatio(nomenclatureId, unit_id, stockUnitId)
        if ratio is None:
            return 0.0
        stockQnt = qnt*ratio
        return stockQnt*price


#    def calcSum(self, item, qntCol='qnt', batch=None):
#        nomenclatureId = forceRef(item.value('nomenclature_id'))
#        price = forceDouble(item.value('price'))
#        qnt = forceDouble(item.value(qntCol))
#        unit_id = forceRef(item.value('unit_id'))
#        stockUnitId = self.getDefaultStockUnitId(nomenclatureId)
#        ratio = self.getRatio(nomenclatureId, unit_id, stockUnitId)
#        stockQnt = qnt*ratio
#        return stockQnt*price

