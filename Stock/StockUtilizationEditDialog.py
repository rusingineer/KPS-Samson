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
from PyQt4.QtCore import Qt, QVariant, pyqtSignature, SIGNAL, QString

from library.crbcombobox            import CRBComboBox
from library.InDocTable             import CDateInDocTableCol, CInDocTableCol, CRBInDocTableCol, CInDocTableModel, CFloatInDocTableCol, CEnumInDocTableCol
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
from Stock.Utils                    import CSummaryInfoModelMixin, CPriceItemDelegate, getStockMotionItemQntEx, getExistsNomenclatureAmountEx, UTILIZATION, INTERNAL_CONSUMPTION
from Stock.Service                  import CStockService
from Stock.StockModel               import CStockMotionType

import StockMotionInfo
from Stock.Ui_StockUtilizationDialog import Ui_StockUtilizationDialog


class CStockUtilizationEditDialog(CStockMotionBaseDialog, Ui_StockUtilizationDialog):
    stockDocumentType = CStockMotionType.utilization

    def __init__(self, parent):
        CStockMotionBaseDialog.__init__(self, parent)
        self.addModels('Items', CStockUtilizationItemsModel(self))
        self.addModels('Commission', CStockUtilizationCommissionModel(self))
        self.addObject('btnPrint', getPrintButton(self, 'StockUtilization'))
        self.addObject('actOpenStockBatchEditor', QtGui.QAction(u'Подобрать параметры', self))
        self.addObject('actFillExistsAmountEditor', QtGui.QAction(u'Заполнить количество по остатку', self))
        self.actFillExistsAmountEditor.setShortcut('F3')
        self.btnPrint.setShortcut('F6')
        self.setupUi(self)
        self.cmbSupplierPerson.setSpecialityIndependents()
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setupDirtyCather()
        self.buttonBox.addButton(self.btnPrint, QtGui.QDialogButtonBox.ActionRole)
        self.tblItems.setModel(self.modelItems)
        self.addObject('qshcFillExistsAmountEditor', QtGui.QShortcut('F3', self.tblItems, self.on_actFillExistsAmountEditor_triggered))
        self.qshcFillExistsAmountEditor.setContext(Qt.WidgetShortcut)
        self.prepareItemsPopupMenu(self.tblItems)
        self.tblItems.popupMenu().addSeparator()
        self.tblItems.popupMenu().addAction(self.actOpenStockBatchEditor)
        self.tblItems.popupMenu().addAction(self.actFillExistsAmountEditor)
        self.tblItems.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.tblItems.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.setWindowTitleEx(u'Утилизация')
        self.tblItems.setItemDelegateForColumn(CStockUtilizationItemsModel.priceColumnIndex, CPriceItemDelegate(self.tblItems))
        self.tblCommission.setModel(self.modelCommission)
        self.tblCommission.addPopupDelRow()
        self.tblCommission.addMoveRow()
        self.tblItems.enableColsMove()

    @pyqtSignature('int')
    def on_btnPrint_printByTemplate(self, templateId):
        data = self.getStockUtilizationInfo()
        QtGui.qApp.call(self, applyTemplate, (self, templateId, data))


    def getStockUtilizationInfo(self):
        itemsList = []
        commissionList = []
        context = CInfoContext()
        if hasattr(self, 'modelItems'):
            for record in self.modelItems.items():
                item = StockMotionInfo.CStockMotionItemInfo(context, forceRef(record.value('id')))
                item.loadFromRecord(record)
                itemsList.append(item)
        if hasattr(self, 'modelCommission'):
            for record in self.modelCommission.items():
                item = StockMotionInfo.CStockMotionCommissionInfo(context, forceRef(record.value('id')))
                item.setRecord(record)
                item.setOkLoaded()
                commissionList.append(item)
        data = {'rows': itemsList,
                'commission': commissionList,
                'number': unicode(self.edtNumber.text()),
                'date': CDateInfo(self.edtDate.date()),
                'time': CTimeInfo(self.edtTime.time()),
                'supplier': COrgStructureInfo(context, self.cmbSupplier.value()),
                'supplierPerson': CPersonInfo(context, self.cmbSupplierPerson.value()),
                'note': unicode(self.edtNote.text()),
                }
        return data

    @pyqtSignature('')
    def on_actOpenStockBatchEditor_triggered(self):
        self.on_tblItems_doubleClicked(self.tblItems.currentIndex())

    @pyqtSignature('')
    def on_actFillExistsAmountEditor_triggered(self):
        selectedRows = []
        items = self.modelItems.items()
        for index in self.tblItems.selectedIndexes():
            if index and index.isValid():
                selectedRow = index.row()
                if 0 <= selectedRow < len(items) and selectedRow not in selectedRows:
                    selectedRows.append(selectedRow)
        for row in selectedRows:
            record = items[row]
            existsValue = self.modelItems.getExistsValue(record)
            self.modelItems.items()[row].setValue('qnt', toVariant(existsValue))
        self.modelItems.reset()

    @pyqtSignature('QModelIndex')
    def on_tblItems_doubleClicked(self, index):
        if index and index.isValid():
            col = index.column()
            if col in (CStockUtilizationItemsModel.batchColumnIndex, CStockUtilizationItemsModel.shelfTimeColumnIndex, CStockUtilizationItemsModel.financeColumnIndex, CStockUtilizationItemsModel.medicalAidKindColumnIndex):
                items = self.modelItems.items()
                currentRow = index.row()
                if 0 <= currentRow < len(items):
                    item = items[currentRow]
                    params = {'nomenclatureId': forceString(item.value('nomenclature_id')),
                              'batch': forceString(item.value('batch')),
                              'financeId': forceRef(item.value('finance_id')),
                              'shelfTime': forceDate(item.value('shelfTime')),
                              'medicalAidKindId': forceRef(item.value('medicalAidKind_id')),
                              'filterFor': UTILIZATION}
                    dialog = CStockBatchEditor(self, params)
                    try:
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
                                ratio = self.modelItems.getRatio(nomenclatureId, unitId, None)
                                if ratio is not None:
                                    outPrice = outPrice*ratio
                            item.setValue('price', toVariant(outPrice))
                            item.setValue('sum', toVariant(forceDouble(item.value('qnt')) * forceDouble(item.value('price'))))
                            self.modelItems.reset()
                    finally:
                        dialog.deleteLater()
            else:
                self.emit(SIGNAL('doubleClicked(QModelIndex)'), index)


    def checkDataEntered(self):
        result = self._checkStockMotionItemsData(self.tblItems)
        result = result and self.checkItemsDataEntered()
        return result


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
        existsQnt = getExistsNomenclatureAmountEx(nomenclatureId, financeId, batch, supplierId, stockUnitId, medicalAidKindId, shelfTime, exact=True, otherHaving=[u'qnt!=0'], price=price)
        prevQnt = round(getStockMotionItemQntEx(nomenclatureId, stockMotionId=self._id, batch=batch, financeId=financeId, medicalAidKindId=medicalAidKindId, price=None, oldPrice=price, oldUnitId=stockUnitId), QtGui.qApp.numberDecimalPlacesQnt()) if self._id else 0
        if (round(existsQnt, QtGui.qApp.numberDecimalPlacesQnt()) + prevQnt) - round(qnt, QtGui.qApp.numberDecimalPlacesQnt()) < 0:
            nomenclatureName = self.modelItems.getNomenclatureNameById(nomenclatureId)
            if existsQnt > 0:
                message = u'На складе {0} {7} {1} партии "{3}" годный до "{4}" типа финансирования "{5}" вида мед помощи "{6}", а списание на {2}'.format(
                    existsQnt,
                    nomenclatureName,
                    qnt,
                    batch if batch else u'не указано',
                    shelfTimeString if shelfTime else u'не указано',
                    forceString(db.translate('rbFinance', 'id', financeId, 'name')) if financeId else u'не указано',
                    medicalAidKindName if medicalAidKindName else u'не указано',
                    forceString(db.translate('rbUnit', 'id', stockUnitId, 'name')))
            else:
                message = u'На складе отсутствует "{0}" партии "{1}" годный до "{2}" типа финансирования "{3}" вида мед помощи "{4} - {5} {6}"'.format(
                    nomenclatureName,
                    batch if batch else u'не указано',
                    shelfTimeString if shelfTime else u'не указано',
                    forceString(db.translate('rbFinance', 'id', financeId, 'name')) if financeId else u'не указано',
                    medicalAidKindName if medicalAidKindName else u'не указано')
            return self.checkValueMessage(message, False, self.tblItems, row, self.modelItems.qntColumnIndex)
        return True


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
        self.modelCommission.loadItems(self.itemId())


    def getRecord(self):
        record = CItemEditorBaseDialog.getRecord(self)
        getLineEditValue(   self.edtNumber,         record, 'number')
        getDatetimeEditValue(self.edtDate, self.edtTime, record, 'date', True)
        getRBComboBoxValue( self.cmbSupplier,       record, 'supplier_id')
        getRBComboBoxValue( self.cmbSupplierPerson, record, 'supplierPerson_id')
        getLineEditValue(   self.edtNote,           record, 'note')
        record.setValue('type', self.stockDocumentType)
        return record


    def saveInternals(self, id):
        self.modelItems.saveItems(id)
        self.modelCommission.saveItems(id)


    def _on_cmbSupplierChanged(self):
        if not self._record:
            self._record = self.getRecord()
            self.modelItems.setStockMotion(CStockService.getStockMotionByRecord(self._record))

        self._record.setValue('supplier_id', self.cmbSupplier.value())


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_modelItems_dataChanged(self,  topLeftIndex, bottomRightIndex):
        self.lblSummaryInfo.setText(self.modelItems.getSummaryInfo())


# #####################################################################################################################

class CStockInternalConsumptionEditDialog(CStockUtilizationEditDialog, Ui_StockUtilizationDialog):
    stockDocumentType = CStockMotionType.internalConsumption

    def __init__(self,  parent):
        #CStockUtilizationEditDialog.__init__(self, parent)
        CStockMotionBaseDialog.__init__(self, parent)
        self.addModels('Items', CInternalConsumptionItemsModel(self))
        self.addObject('btnPrint', getPrintButton(self, 'StockInternalConsumption'))
        self.addObject('actOpenStockBatchEditor', QtGui.QAction(u'Подобрать параметры', self))
        self.addObject('actFillExistsAmountEditor', QtGui.QAction(u'Заполнить количество по остатку', self))
        self.actFillExistsAmountEditor.setShortcut('F3')
        self.btnPrint.setShortcut('F6')
        self.setupUi(self)
        self.cmbSupplierPerson.setSpecialityIndependents()
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setupDirtyCather()
        self.buttonBox.addButton(self.btnPrint, QtGui.QDialogButtonBox.ActionRole)
        self.tblItems.setModel(self.modelItems)
        self.addObject('qshcFillExistsAmountEditor', QtGui.QShortcut('F3', self.tblItems, self.on_actFillExistsAmountEditor_triggered))
        self.qshcFillExistsAmountEditor.setContext(Qt.WidgetShortcut)
        self.prepareItemsPopupMenu(self.tblItems)
        self.tblItems.popupMenu().addSeparator()
        self.tblItems.popupMenu().addAction(self.actOpenStockBatchEditor)
        self.tblItems.popupMenu().addAction(self.actFillExistsAmountEditor)
        self.tblItems.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.tblItems.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.setWindowTitleEx(u'Внутреннее потребление')
        self.tblItems.setItemDelegateForColumn(CInternalConsumptionItemsModel.priceColumnIndex, CPriceItemDelegate(self.tblItems))
        # удаление вкладки "Состав комиссии"
        self.tabWidget.widget(1).deleteLater()
        self.tabWidget.removeTab(1)
        self.tblItems.enableColsMove()
        #self.cmbSupplier.setFilter(u'isQuarantineStorage=1') Зачем?
        self.cmbSupplier.setCurrentIndex(0)


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


    @pyqtSignature('')
    def on_actOpenStockBatchEditor_triggered(self):
        self.on_tblItems_doubleClicked(self.tblItems.currentIndex())

    @pyqtSignature('')
    def on_actFillExistsAmountEditor_triggered(self):
        selectedRows = []
        items = self.modelItems.items()
        for index in self.tblItems.selectedIndexes():
            if index and index.isValid():
                selectedRow = index.row()
                if 0 <= selectedRow < len(items) and selectedRow not in selectedRows:
                    selectedRows.append(selectedRow)
        for row in selectedRows:
            record = items[row]
            existsValue = self.modelItems.getExistsValue(record)
            self.modelItems.items()[row].setValue('qnt', toVariant(existsValue))
        self.modelItems.reset()

    @pyqtSignature('QModelIndex')
    def on_tblItems_doubleClicked(self, index):
        if index and index.isValid():
            col = index.column()
            if col in (CInternalConsumptionItemsModel.batchColumnIndex, CInternalConsumptionItemsModel.shelfTimeColumnIndex, CInternalConsumptionItemsModel.financeColumnIndex, CInternalConsumptionItemsModel.medicalAidKindColumnIndex):
                items = self.modelItems.items()
                currentRow = index.row()
                if 0 <= currentRow < len(items):
                    item = items[currentRow]
                    params = {'nomenclatureId': forceRef(item.value('nomenclature_id')),
                              'batch': forceString(item.value('batch')),
                              'financeId': forceRef(item.value('finance_id')),
                              'shelfTime': forceDate(item.value('shelfTime')),
                              'medicalAidKindId': forceRef(item.value('medicalAidKind_id')),
                              'filterFor': INTERNAL_CONSUMPTION}
                    dialog = CStockBatchEditor(self, params)
                    try:
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
                                ratio = self.modelItems.getRatio(nomenclatureId, unitId, None)
                                if ratio is not None:
                                    outPrice = outPrice*ratio
                            item.setValue('price', toVariant(outPrice))
                            item.setValue('sum', toVariant(forceDouble(item.value('qnt')) * forceDouble(item.value('price'))))
                            self.modelItems.reset()
                    finally:
                        dialog.deleteLater()
            else:
                self.emit(SIGNAL('doubleClicked(QModelIndex)'), index)


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
        existsQnt = getExistsNomenclatureAmountEx(nomenclatureId, financeId, batch, supplierId, stockUnitId,
                                                  medicalAidKindId, shelfTime, exact=True, price=price)
        prevQnt = round(getStockMotionItemQntEx(nomenclatureId, stockMotionId=self._id, batch=batch,
                                                financeId=financeId, medicalAidKindId=medicalAidKindId, price=None,
                                                oldPrice=price, oldUnitId=stockUnitId), QtGui.qApp.numberDecimalPlacesQnt()) if self._id else 0
        if (round(existsQnt, QtGui.qApp.numberDecimalPlacesQnt()) + prevQnt) - round(qnt, QtGui.qApp.numberDecimalPlacesQnt()) < 0:
            nomenclatureName = self.modelItems.getNomenclatureNameById(nomenclatureId)
            if existsQnt > 0:
                message = u'На складе {0} {7} {1} партии "{3}" годный до "{4}" типа финансирования "{5}" вида мед помощи "{6}", а списание на {2}'.format(
                    existsQnt,
                    nomenclatureName,
                    qnt,
                    batch if batch else u'не указано',
                    shelfTimeString if shelfTime else u'не указано',
                    forceString(db.translate('rbFinance', 'id', financeId, 'name')) if financeId else u'не указано',
                    medicalAidKindName if medicalAidKindName else u'не указано',
                    forceString(db.translate('rbUnit', 'id', stockUnitId, 'name')))
            else:
                message = u'На складе отсутствует "{1}" партии "{3}" годный до "{4}" типа финансирования "{5}" вида мед помощи "{6}"'.format(
                    existsQnt,
                    nomenclatureName,
                    qnt,
                    batch if batch else u'не указано',
                    shelfTimeString if shelfTime else u'не указано',
                    forceString(db.translate('rbFinance', 'id', financeId, 'name')) if financeId else u'не указано',
                    medicalAidKindName if medicalAidKindName else u'не указано')
            return self.checkValueMessage(message, False, self.tblItems, row, self.modelItems.qntColumnIndex)
        return True


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
    qntColumnIndex = 5
    unitColumnIndex = 6
    priceColumnIndex = 7
    sumColumnIndex = 8

    class CSumCol(CFloatInDocTableCol):
        def _toString(self, value):
            if value.isNull():
                return None
            return format(forceDouble(value), '.2f')

    def __init__(self, parent, showExists=False):
        CNomenclatureItemsBaseModel.__init__(self, parent)
        self.priceCache = parent
        self._financeCache = {}
        self._shelfTimeCache = {}
        self._setterHandlers = {
            self.nomenclatureColumnIndex: self._handleNomenclatureSet,
            self.unitColumnIndex: self._handleUnitIdSet,
            self.qntColumnIndex: self._handleQntSet,
            self.priceColumnIndex: self._handlePriceSet
        }
        self._stockMotion = None


    def setStockMotion(self, stockMotion):
        self._stockMotion = stockMotion


    def _handleNomenclatureSet(self, stockMotionItem, value):
        previousValue = stockMotionItem.nomenclature_id
        stockMotionItem.nomenclature_id = value
        if previousValue != stockMotionItem.nomenclature_id:
            if type(self) == CInternalConsumptionItemsModel:
                CStockService.setFinanceBatchShelfTime(stockMotionItem, setShelfTimeCond=True, isInternalConsumption=True)
            else:
                CStockService.setFinanceBatchShelfTime(stockMotionItem, setShelfTimeCond=False)
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
                    recordPrevQnt = db.getRecordEx(tableSMI, [tableSMI['qnt']],
                                                   [tableSMI['id'].eq(id), tableSMI['deleted'].eq(0)])
                    prevQnt = forceDouble(recordPrevQnt.value('qnt')) if recordPrevQnt else 0
                existsColumn = forceDouble(self._cols[self.existsColumnIndex].getExistsValue(item))
                existsColumn = existsColumn + prevQnt
                if not self.isPriceLineEditable and forceDouble(item.value('price')) and (
                        not existsColumn or existsColumn < 0):
                    return False
                if not self.isPriceLineEditable and forceDouble(item.value('price')) and existsColumn < forceDouble(
                        value):
                    value = toVariant(existsColumn)
            if self._setterHandlers[columnIndex](stockMotionItem, value):
                self.setIsUpdateValue(True)
                if 0 <= row < len(self._items):
                    item = self._items[row]
                    if columnIndex == self.getColIndex('qnt'):
                        item.setValue('prevQnt', prevQnt)
                self.emitRowChanged(index.row())
                return True
            return False
        elif columnIndex in (
        self.batchColumnIndex, self.shelfTimeColumnIndex, self.financeColumnIndex, self.medicalAidKindColumnIndex):
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
        column = index.column()
        if column in (
        self.batchColumnIndex, self.shelfTimeColumnIndex, self.financeColumnIndex, self.medicalAidKindColumnIndex):
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        elif column == self.unitColumnIndex:
            row = index.row()
            if 0 <= row < len(self._items):
                item = self._items[row]
                if not forceRef(item.value('nomenclature_id')):
                    return Qt.ItemIsSelectable | Qt.ItemIsEnabled
            else:
                return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return CNomenclatureItemsBaseModel.flags(self, index)


class CStockUtilizationItemsModel(CLocItemsModel):
    reasonColumnIndex = 9
    existsColumnIndex = 11

    class CUtilizationNomenclatureCol(CNomenclatureInDocTableCol):
        def __init__(self, title, fieldName, width, **params):
            CNomenclatureInDocTableCol.__init__(self, title, fieldName, width, **params)

        def createEditor(self, parent):
            editor = CNomenclatureInDocTableCol.createEditor(self, parent)
            editor.setOrgStructureId(QtGui.qApp.currentOrgStructureId())
            editor.setOnlyExists(False)
            editor.setOnlyNomenclature(False)
            return editor

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

    def __init__(self, parent, showExists=False):
        CLocItemsModel.__init__(self, parent)
        self._nomenclatureColumn = self.CUtilizationNomenclatureCol(u'ЛСиИМН', 'nomenclature_id', 50,
                                                                    showFields=CRBComboBox.showName)
        self._batchCol = CInDocTableCol(u'Серия', 'batch', 16).setReadOnly()
        self._unitColumn = CRBInDocTableCol(u'Ед.Учета', 'unit_id', 12, 'rbUnit', addNone=False)
        self.addCol(self._nomenclatureColumn)
        self.addCol(self._batchCol)
        self.addCol(CDateInDocTableCol(u'Годен до', 'shelfTime', 12, canBeEmpty=True).setReadOnly())
        self.addCol(CRBInDocTableCol(u'Тип финансирования', 'finance_id', 15, 'rbFinance').setReadOnly())
        self.addCol(
            CRBInDocTableCol(u'Вид медицинской помощи', 'medicalAidKind_id', 15, 'rbMedicalAidKind').setReadOnly())
        self.addCol(self.CQuantityCol(u'Количество бракованных ЛСиИМН', 'qnt', 12, low=1, high=65535,
                                      precision=QtGui.qApp.numberDecimalPlacesQnt()))
        self.addCol(self._unitColumn)
        self.addCol(CFloatInDocTableCol(u'Цена', 'price', 12, precision=2))
        self.addCol(self.CSumCol(u'Сумма', 'sum', 12).setReadOnly())
        self.addCol(CRBInDocTableCol(u'Причина утилизации', 'reason_id', 12, 'rbStockMotionItemReason',
                                     filter='stockMotionType=%s' % CStockMotionType.utilization))
        self.addCol(CRBInDocTableCol(u'Способ утилизации', 'disposalMethod_id', 12, 'rbDisposalMethod'))
        self.existsCol = self.CExistsCol(self)
        self.addExtCol(self.existsCol.setReadOnly(), QVariant.Double)
        self.setStockDocumentTypeExistsCol()

    def getExistsValue(self, record):
        if not record:
            return 0
        return self.existsCol.getExistsValue(record)

    def createEditor(self, index, parent):
        editor = CInDocTableModel.createEditor(self, index, parent)
        column = index.column()
        if column == self.nomenclatureColumnIndex:
            editor.setOnlyExists(False)
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


class CInternalConsumptionItemsModel(CLocItemsModel):
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

    def __init__(self, parent, showExists=False):
        CLocItemsModel.__init__(self, parent)
        self._nomenclatureColumn = CLocNomenclatureCol(u'ЛСиИМН', 'nomenclature_id', 50,
                                                       showFields=CRBComboBox.showName)
        self._batchCol = CInDocTableCol(u'Серия', 'batch', 16).setReadOnly()
        self._unitColumn = CRBInDocTableCol(u'Ед.Учета', 'unit_id', 12, 'rbUnit', addNone=False)
        self.addCol(self._nomenclatureColumn)
        self.addCol(self._batchCol)
        self.addCol(CDateInDocTableCol(u'Годен до', 'shelfTime', 12, canBeEmpty=True).setReadOnly())
        self.addCol(CRBInDocTableCol(u'Тип финансирования', 'finance_id', 15, 'rbFinance').setReadOnly())
        self.addCol(
            CRBInDocTableCol(u'Вид медицинской помощи', 'medicalAidKind_id', 15, 'rbMedicalAidKind').setReadOnly())
        self.addCol(self.CQuantityCol(u'Количество ЛСиИМН', 'qnt', 12, low=1, high=65535,
                                      precision=QtGui.qApp.numberDecimalPlacesQnt()))
        self.addCol(self._unitColumn)
        self.addCol(CFloatInDocTableCol(u'Цена', 'price', 12, precision=2))
        sumCol = self.CSumCol(u'Сумма', 'sum', 12)
        self.addCol(sumCol.setReadOnly())
        self.existsCol = self.CExistsCol(self)
        self.addExtCol(self.existsCol.setReadOnly(), QVariant.Double)
        self.setStockDocumentTypeExistsCol()

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


class CStockUtilizationCommissionModel(CInDocTableModel):
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
