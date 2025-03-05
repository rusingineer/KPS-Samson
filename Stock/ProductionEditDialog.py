# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2017 SAMSON Group. All rights reserved.
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

from library.crbcombobox                   import CRBComboBox
from library.DialogBase                    import CDialogBase
from library.InDocTable                    import CInDocTableModel, CDateInDocTableCol, CFloatInDocTableCol, CInDocTableCol, CRBInDocTableCol
from library.interchange                   import getRBComboBoxValue
from library.PrintInfo                     import CInfoContext
from library.PrintTemplates                import applyTemplate, CPrintAction, CPrintButton, getPrintTemplates
from library.Utils                         import forceInt, forceDouble, forceString, toVariant, forceRef, forceDate, pyDate
from Reports.ReportBase                    import CReportBase, createTable
from Reports.ReportView                    import CReportViewDialog
from Stock.StockBatchEditor              import CStockBatchEditor
from Stock.NomenclatureComboBox            import CNomenclatureInDocTableCol
from Stock.StockMotionBaseDialog           import CStockMotionBaseDialog, CNomenclatureItemsBaseModel
from Stock.Utils import getStockMotionItemQuantityColumn, getExistsNomenclatureAmountEx, getStockMotionItemQntEx, getBatchShelfTimeFinance
from Stock.Ui_Production                   import Ui_ProductionDialog
from Stock.Ui_SelectRecipeDialog           import Ui_Dialog as Ui_SelectRecipeDialog


class CProductionEditDialog(CStockMotionBaseDialog, Ui_ProductionDialog):
    stockDocumentType = 3

    def __init__(self,  parent):
        CStockMotionBaseDialog.__init__(self, parent)
        self.addObject('btnAddRecipe', QtGui.QPushButton(u'По рецепту', self))
        self.addModels('InItems', CItemsModel(self, False))
        self.addModels('OutItems', CItemsModel(self, True))
        self.addObject('btnPrint', CPrintButton(self, u'Печать'))
        self.btnPrint.setShortcut('F6')
        self.addObject('actOpenStockBatchEditor', QtGui.QAction(u'Подобрать параметры', self))
        self.addObject('actOpenStockBatchEditorOut', QtGui.QAction(u'Подобрать параметры', self))
        self.setupUi(self)
        self.cmbSupplierPerson.setSpecialityIndependents()
        self.buttonBox.addButton(self.btnAddRecipe, QtGui.QDialogButtonBox.ActionRole)
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
        self.tblInItems.setModel(self.modelInItems)
        self.prepareItemsPopupMenu(self.tblInItems)
        self.tblInItems.popupMenu().addSeparator()
        self.tblInItems.popupMenu().addAction(self.actOpenStockBatchEditor)
        self.tblInItems.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.tblInItems.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)

        self.tblOutItems.setModel(self.modelOutItems)
        self.prepareItemsPopupMenu(self.tblOutItems)
        self.tblOutItems.popupMenu().addAction(self.actOpenStockBatchEditorOut)
        self.tblOutItems.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.tblOutItems.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.tblInItems.enableColsMove()
        self.tblOutItems.enableColsMove()


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
            idList = self.tblInItems.model().itemIdList()
            context = CInfoContext()
            data = { 'InventoryList': CStockMotionInfoList(context, idList)}
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
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.windowTitle())
        self.dumpParams(cursor)
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertText(self.groupBoxIn.title())
        self.modelPrint(self.tblInItems, self.tblInItems.model(), cursor)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertText(self.groupBoxOut.title())
        self.modelPrint(self.tblOutItems, self.tblOutItems.model(), cursor)
        html = doc.toHtml('utf-8')
        view = CReportViewDialog(self)
        view.setText(html)
        view.exec_()


    def modelPrint(self, tblItems, model, cursor):
        colWidths  = [ tblItems.columnWidth(i) for i in xrange(model.columnCount()-1) ]
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


    def setRecord(self, record):
        CStockMotionBaseDialog.setRecord(self, record)
        self.modelInItems.loadItems(self.itemId())
        self.modelOutItems.loadItems(self.itemId())
        self.setIsDirty(False)


    def getRecord(self):
        record = CStockMotionBaseDialog.getRecord(self)
        getRBComboBoxValue( self.cmbSupplier, record, 'receiver_id')
        getRBComboBoxValue( self.cmbSupplierPerson, record, 'receiverPerson_id')
        record.setValue('type', 3)
        return record


    def saveInternals(self, id):
        self.modelInItems.saveItems(id)
        self.modelOutItems.saveItems(id)


    def checkDataEntered(self):
        result = True
        result = result and (len(self.modelInItems.items()) > 0 or self.checkInputMessage(u'данные таблицы "Исходные материалы"', False, self.tblInItems, 0, 0))
        result = result and (len(self.modelOutItems.items()) > 0 or self.checkInputMessage(u'данные таблицы "Результат"', False, self.tblOutItems, 0, 0))
        result = result and self._checkStockMotionItemsData(self.tblInItems)
        result = result and self._checkStockMotionItemsData(self.tblOutItems)
        result = result and self.checkItemsDataEntered(self.tblInItems, self.modelInItems)
        #result = result and self.checkItemsDataEntered(self.tblOutItems, self.modelOutItems)
        return result


    def checkItemsDataEntered(self, table, model):
        supplierId = self.cmbSupplier.value()
        existsNomenclatureAmountDict = {}
        db = QtGui.qApp.db
        for row, item in enumerate(model.items()):
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
            stockUnitId = model.getDefaultStockUnitId(nomenclatureId)
            ratio = model.getRatio(nomenclatureId, stockUnitId, unitId)
            if ratio is not None:
                price = price*ratio
                qnt = qnt / ratio
            existsNomenclatureAmountLine = existsNomenclatureAmountDict.get((nomenclatureId, financeId, batch, supplierId, stockUnitId, medicalAidKindId, shelfTime, price), [0, shelfTimeString, medicalAidKindName, []])
            existsNomenclatureAmountLine[0] = existsNomenclatureAmountLine[0]  + qnt
            existsNomenclatureAmountLine[3].append(row)
            existsNomenclatureAmountDict[(nomenclatureId, financeId, batch, supplierId, stockUnitId, medicalAidKindId, shelfTime, price)] = existsNomenclatureAmountLine
        for keys, item in existsNomenclatureAmountDict.items():
            if supplierId and not self.checkNomenclatureExists(keys, item, table, model, supplierId):
                return False
        return True


    def checkNomenclatureExists(self, keys, item, table, model, supplierId=None):
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
            nomenclatureName = model.getNomenclatureNameById(nomenclatureId)
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
            return self.checkValueMessage(message, False, table, row, model.qntColumnIndex)
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

    def addRecipe(self, recipeId, rate, financeId):
        db = QtGui.qApp.db
        table = db.table('rbStockRecipe')
        tableItem = db.table('rbStockRecipe_Item')
        queryTable = table.innerJoin(tableItem, tableItem['master_id'].eq(table['id']))
        records = db.getRecordList(queryTable, '*', [tableItem['master_id'].eq(recipeId), table['deleted'].eq(0)], tableItem['idx'].name())
        models = [self.modelInItems, self.modelOutItems]
        for record in records:
            model = models[forceInt(record.value('isOut'))]
            newRecord = model.getEmptyRecord()
            newRecord.setValue('nomenclature_id', record.value('nomenclature_id'))
            newRecord.setValue('finance_id',      toVariant(financeId))
            newRecord.setValue('qnt',             toVariant(rate*forceDouble(record.value('qnt'))))
            newRecord.setValue('unit_id',         record.value('unit_id'))
            params = {}
            params['nomenclatureId'] = forceRef(record.value('nomenclature_id'))
            params['batch'] = u''
            params['financeId'] = financeId
            dlg = CStockBatchEditor(self, params)
            try:
                dlg.loadData()
                outBatch, outFinanceId, outShelfTime, outMedicalAidKindId, outPrice = dlg.getBatchData()
                newRecord.setValue('batch', toVariant(outBatch))
                newRecord.setValue('finance_id', toVariant(outFinanceId))
                newRecord.setValue('shelfTime', toVariant(outShelfTime))
                newRecord.setValue('medicalAidKind_id', toVariant(outMedicalAidKindId))
                if outPrice:
                    unitId = forceRef(newRecord.value('unit_id'))
                    nomenclatureId = forceRef(newRecord.value('nomenclature_id'))
                    ratio = model.getRatio(nomenclatureId, unitId, None)
                    if ratio is not None:
                        outPrice = outPrice*ratio
                newRecord.setValue('price', toVariant(outPrice))
                newRecord.setValue('sum', toVariant(forceDouble(newRecord.value('qnt')) * forceDouble(newRecord.value('price'))))
            finally:
                dlg.deleteLater()
            model.addRecord(newRecord)


    @pyqtSignature('')
    def on_btnAddRecipe_clicked(self):
        dialog = CSelectRecipe(self)
        try:
            if dialog.exec_():
                recipeId, rate, financeId = dialog.getResult()
                if recipeId and rate:
                    self.addRecipe(recipeId, rate, financeId)
        finally:
            dialog.deleteLater()


    @pyqtSignature('')
    def on_actOpenStockBatchEditor_triggered(self):
        self.on_tblInItems_doubleClicked(self.tblInItems.currentIndex())


    @pyqtSignature('')
    def on_actOpenStockBatchEditorOut_triggered(self):
        self.openStockBatchEditor(self.modelOutItems, self.tblOutItems.currentIndex())


    @pyqtSignature('QModelIndex')
    def on_tblInItems_doubleClicked(self, index):
        self.openStockBatchEditor(self.modelInItems, index)


    def openStockBatchEditor(self, model, index):
        if index and index.isValid():
            col = index.column()
            if col in (CItemsModel.batchColumnIndex, CItemsModel.shelfTimeColumnIndex, CItemsModel.financeColumnIndex, CItemsModel.medicalAidKindColumnIndex):
                items = model.items()
                currentRow = index.row()
                if 0 <= currentRow < len(items):
                    item = items[currentRow]
                    try:
                        params = {}
                        params['nomenclatureId'] = forceRef(item.value('nomenclature_id'))
                        params['batch'] = forceString(item.value('batch'))
                        params['financeId'] = forceRef(item.value('finance_id'))
                        params['shelfTime'] = forceDate(item.value('shelfTime'))
                        params['medicalAidKindId'] = forceRef(item.value('medicalAidKind_id'))
                        dialog = CStockBatchEditor(self, params)
                        dialog.loadData()
                        if dialog.exec_():
                            outBatch, outFinanceId, outShelfTime, outMedicalAidKindId, outPrice = dialog.getValue()
                            item.setValue('batch', toVariant(outBatch))
                            item.setValue('finance_id', toVariant(outFinanceId))
                            item.setValue('shelfTime', toVariant(outShelfTime))
                            item.setValue('medicalAidKind_id', toVariant(outMedicalAidKindId))
                            if outPrice:
                                unitId = forceRef(item.value('unit_id'))
                                nomenclatureId = forceRef(item.value('nomenclature_id'))
                                ratio = model.getRatio(nomenclatureId, unitId, None)
                                if ratio is not None:
                                    outPrice = outPrice*ratio
                            item.setValue('price', toVariant(outPrice))
                            item.setValue('sum', toVariant(forceDouble(item.value('qnt')) * forceDouble(item.value('price'))))
                            model.reset()
                    finally:
                        dialog.deleteLater()
            else:
                self.emit(SIGNAL('doubleClicked(QModelIndex)'), index)


class CItemsModel(CNomenclatureItemsBaseModel):
    nomenclatureColumnIndex = 0
    batchColumnIndex = 1
    shelfTimeColumnIndex = 2
    financeColumnIndex = 3
    medicalAidKindColumnIndex = 4
    qntColumnIndex = 5
    unitColumnIndex = 6
    priceColumnIndex = 7
    sumColumnIndex = 8
    existsColumnIndex = 9

    class CSumCol(CFloatInDocTableCol):
        def _toString(self, value):
            if value.isNull():
                return None
            return format(forceDouble(value), '.2f')

    class CLocNomenclatureCol(CNomenclatureInDocTableCol):
        def __init__(self, title, fieldName, width, supplierId, isOut, **params):
            CNomenclatureInDocTableCol.__init__(self, title, fieldName, width, **params)
            self.supplierId = supplierId
            self.isOut = isOut
            self.setStockOrgStructureId(self.supplierId)

        def createEditor(self, parent):
            editor = CNomenclatureInDocTableCol.createEditor(self, parent)
            editor.setOnlyExists(not self.isOut)
            return editor

    def __init__(self, parent, isOut):
        CNomenclatureItemsBaseModel.__init__(self, parent)
        self.isOut = isOut
        self.supplierId = None
        self.isBatchReadOnly = True
        self._nomenclatureColumn = self.CLocNomenclatureCol(u'ЛСиИМН', 'nomenclature_id', 50, self.supplierId, isOut = self.isOut, showFields = CRBComboBox.showName)
        self._unitColumn = CRBInDocTableCol(u'Ед.Учета', 'unit_id', 12, 'rbUnit', addNone=False)
        self.addCol(self._nomenclatureColumn)
        self.addCol(CInDocTableCol( u'Серия', 'batch', 16))
        self.addCol(CDateInDocTableCol( u'Годен до', 'shelfTime', 12, canBeEmpty=True))
        self.addCol(CRBInDocTableCol(    u'Тип финансирования', 'finance_id', 15, 'rbFinance'))
        self.addCol(CRBInDocTableCol(    u'Вид медицинской помощи', 'medicalAidKind_id', 15, 'rbMedicalAidKind'))
        self.addCol(getStockMotionItemQuantityColumn( u'Кол-во', 'qnt', 12))
        self.addCol(self._unitColumn)
        self.addCol(CFloatInDocTableCol(u'Цена', 'price', 12, precision=2).setReadOnly(not self.isOut))
        self.addCol(self.CSumCol( u'Сумма', 'sum', 12).setReadOnly())
        self.existsCol = CItemsModel.CExistsCol(self).setReadOnly()
        self.addExtCol(self.existsCol, QVariant.Double)
        self.addHiddenCol('isOut')
        self.setFilter('isOut!=0' if isOut else 'isOut=0')


    def flags(self, index):
        column = index.column()
        if column in (self.batchColumnIndex, self.shelfTimeColumnIndex, self.financeColumnIndex, self.medicalAidKindColumnIndex) and not self.isOut:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return CNomenclatureItemsBaseModel.flags(self, index)


    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid():
            return False
        column = index.column()
        row = index.row()
        if role == Qt.EditRole:
            if column == CItemsModel.nomenclatureColumnIndex:
                if 0 <= row < len(self._items):
                    oldNomenclatureId = forceRef(self._items[row].value('nomenclature_id'))
                else:
                    oldNomenclatureId = None
                result = CNomenclatureItemsBaseModel.setData(self, index, value, role)
                if result:
                    item = self._items[row]
                    nomenclatureId = forceRef(item.value('nomenclature_id'))
                    if oldNomenclatureId != nomenclatureId:
                        unitId = self.getDefaultClientUnitId(nomenclatureId)
                        item.setValue('unit_id', toVariant(unitId))
                        if self.isOut != 1:
                            batch, shelfTime, financeId, medicalAidKind, price = getBatchShelfTimeFinance(forceRef(value))
                            #result = CNomenclatureItemsBaseModel.setData(self, index, value, role)
                            item.setValue('batch', toVariant(batch))
                            unitId = forceRef(item.value('unit_id'))
                            nomenclatureId = forceRef(item.value('nomenclature_id'))
                            if price and unitId and nomenclatureId:
                                ratio = self.getRatio(nomenclatureId, unitId, None)
                                if ratio is not None:
                                    price = price*ratio
                            item.setValue('price', toVariant(price))
                            if financeId:
                                item.setValue('finance_id', toVariant(financeId))
                            else:
                                item.setNull('finance_id')
                            item.setValue('shelfTime', toVariant(shelfTime))
                            if medicalAidKind:
                                item.setValue('medicalAidKind_id', toVariant(medicalAidKind))
                            else:
                                item.setNull('medicalAidKind_id')
                        self.emitRowChanged(row)
                return result
            elif column == self.getColIndex('unit_id'):
                if not (0 <= row < len(self._items)):
                    return False
                item = self._items[row]
                oldUnitId = forceRef(item.value('unit_id'))
                result = CNomenclatureItemsBaseModel.setData(self, index, value, role)
                if result:
                    self.setIsUpdateValue(True)
                    newUnitId = forceRef(item.value('unit_id'))
                    self._applyQntRatio(item, oldUnitId, newUnitId)
                    newPrice = self.updatePriceByRatio(item, oldUnitId)
                    item.setValue('price', toVariant(newPrice))
                    item.setValue('sum', toVariant(forceDouble(item.value('qnt')) * forceDouble(item.value('price'))))
                    self.emitRowChanged(row)
            elif column in (self.getColIndex('qnt'), self.getColIndex('price')):
                if column == self.getColIndex('qnt'):
                    if not (0 <= row < len(self._items)):
                        return False
                    item = self._items[row]
                    id = forceRef(item.value('id'))
                    if self.isOut != 1:
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
                    else:
                        prevQnt = forceDouble(item.value('qnt'))
                result = CNomenclatureItemsBaseModel.setData(self, index, value, role)
                if not result:
                    return False
                self.setIsUpdateValue(True)
                item = self._items[row]
                if column == self.getColIndex('qnt'):
                    item.setValue('prevQnt', prevQnt)
                item.setValue('sum', toVariant(forceDouble(item.value('qnt')) * forceDouble(item.value('price'))))
                self.emitRowChanged(row)
            elif column in (self.batchColumnIndex, self.shelfTimeColumnIndex, self.financeColumnIndex, self.medicalAidKindColumnIndex) and not self.isOut:
                return False
            else:
                result = CNomenclatureItemsBaseModel.setData(self, index, value, role)
        else:
            result = CNomenclatureItemsBaseModel.setData(self, index, value, role)
        return result


    def getNomenclatureNameById(self, nomenclatureId):
        return forceString(self._nomenclatureColumn.toString(nomenclatureId, None))


    def getEmptyRecord(self):
        record = CInDocTableModel.getEmptyRecord(self)
        record.setValue('isOut', toVariant(self.isOut))
        return record


class CSelectRecipe(CDialogBase, Ui_SelectRecipeDialog):
    def __init__(self, parent):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        self.cmbRecipe.setTable('rbStockRecipe', order='name', filter='deleted=0')
        self.cmbFinance.setTable('rbFinance', True)


    def getResult(self):
        return self.cmbRecipe.value(), self.edtRate.value(), self.cmbFinance.value()
