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

from PyQt4 import QtGui #, QtSql
from PyQt4 import QtCore
from PyQt4.QtCore import Qt, QDateTime, pyqtSignature, QVariant, QStringList, QString

from library.ItemsListDialog import CItemEditorBaseDialog
from library.interchange     import (getDateEditValue, getDatetimeEditValue, getLineEditValue, getRBComboBoxValue,
                                     setDateEditValue, setDatetimeEditValue, setLineEditValue, setRBComboBoxValue)
from library.InDocTable      import CInDocTableModel, CFloatInDocTableCol
from library.Utils           import forceDouble, forceRef, toVariant, forceDate, forceString, forceBool
from library.Counter         import CCounterController
from Stock.StockModel        import CStockMotionType
from Stock.Utils             import getPriceNomenclatureStmt, getNomenclatureUnitRatio, CStockCache, getStockMotionNumberCounterId, getExistsNomenclatureAmountEx, UTILIZATION, INTERNAL_CONSUMPTION


class CStockMotionItemsCopyPasteMixin(object):
    fieldsNotToPaste = ('qnt', 'sum')

    def __init__(self, parent):
        self._parent = parent

    def _initView(self):
        self.addObject('actCopyItems', QtGui.QAction(u'Копировать выделенное', self))
        self.addObject('actPasteItems', QtGui.QAction(u'Вставить из буфера', self))

        self.tblItems.addPopupAction(self.actCopyItems)
        self.tblItems.addPopupAction(self.actPasteItems)

        self.tblItems.setActionsWithCheckers(((self.actCopyItems, self._checkActionCopyItemsEnabled),
                                              (self.actPasteItems, self._checkActionPasteItemsEnabled)))

        self.connect(self.actCopyItems, QtCore.SIGNAL('triggered()'), self.on_actCopyItems)
        self.connect(self.actPasteItems, QtCore.SIGNAL('triggered()'), self.on_actPasteItems)

    def _checkActionCopyItemsEnabled(self):
        return len(self.tblItems.model().items()) > 0

    def _checkActionPasteItemsEnabled(self):
        return len(self._parent.getCopiedData('stockMotionItems', [])) > 0

    def on_actCopyItems(self):
        model = self.tblItems.model()
        notToCopyFields = (model.idFieldName, model.masterIdFieldName)
        result = []
        for item in self.tblItems.getSelectedItems():
            newRecord = model.getEmptyRecord()
            for fieldIndex in xrange(item.count()):
                fieldName = item.fieldName(fieldIndex)
                if fieldName in notToCopyFields:
                    continue
                # Создам новый объект QVariant. Вот не знаю может ли где изменится
                # его значение по ссылке в оригинальном наборе записей.
                newRecord.setValue(fieldName, QtCore.QVariant(item.value(fieldName)))
            result.append(newRecord)
        self._parent.setCopiedData('stockMotionItems', result)

    def on_actPasteItems(self):
        itemsToPast = self._parent.getCopiedData('stockMotionItems', [])
        if not itemsToPast:
            return

        model = self.tblItems.model()
        items = model.items()

        notToPasteFields = self.fieldsNotToPaste + (model.idFieldName, model.masterIdFieldName)

        for item in itemsToPast:
            newRecord = model.getEmptyRecord()
            for fieldIndex in xrange(newRecord.count()):
                fieldName = newRecord.fieldName(fieldIndex)
                if fieldName in notToPasteFields:
                    continue
                # Создам новый объект QVariant. Вот не знаю может ли где изменится
                # его значение по ссылке в оригинальном наборе записей.
                newRecord.setValue(fieldName, QtCore.QVariant(item.value(fieldName)))
            items.append(newRecord)

        rootIndex = QtCore.QModelIndex()
        begin = len(items)
        count = len(itemsToPast)
        model.beginInsertRows(rootIndex, begin, begin + count - 1)
        model.insertRows(begin, count, rootIndex)
        model.endInsertRows()

        model.emitAllChanged()


class CStockMotionBaseDialog(CItemEditorBaseDialog, CStockCache):
    def __init__(self,  parent):
        CItemEditorBaseDialog.__init__(self, parent, 'StockMotion')
        CStockCache.__init__(self)


    def prepareItemsPopupMenu(self, tblWidget):
        tblWidget.addPopupDuplicateCurrentRow()
        tblWidget.addPopupSeparator()
        tblWidget.addMoveRow()
        tblWidget.addPopupDelRow()


    def setDefaults(self):
        now = QDateTime.currentDateTime()
        self.edtDate.setDate(now.date())
        self.edtTime.setTime(now.time())
        self.cmbSupplier.setValue(QtGui.qApp.currentOrgStructureId())


    def getPrice(self, nomenclatureId, financeId, batch=None, medicalAidKindId=None, shelfTime=None):
        return CStockCache.getPrice(self, self.cmbSupplier.value(), nomenclatureId, financeId, batch, medicalAidKindId, shelfTime)


    def setRecord(self, record):
        CItemEditorBaseDialog.setRecord(self, record)
        setLineEditValue(self.edtNumber, record, 'number')
        if hasattr(self, 'edtTime'):
            setDatetimeEditValue(self.edtDate, self.edtTime, record, 'date')
        else:
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


    def getRecord(self):
        record = CItemEditorBaseDialog.getRecord(self)
        getLineEditValue(self.edtNumber, record, 'number')
        if hasattr(self, 'edtTime'):
            getDatetimeEditValue(self.edtDate, self.edtTime, record, 'date', True)
        else:
            getDateEditValue(self.edtDate, record, 'date')
        if hasattr(self, 'edtReason'):
            getLineEditValue(   self.edtReason, record, 'reason')
        if hasattr(self, 'edtReasonDate'):
            getDateEditValue(self.edtReasonDate, record, 'reasonDate')
        if hasattr(self, 'cmbSupplier'):
            getRBComboBoxValue( self.cmbSupplier,       record, 'supplier_id')
            getRBComboBoxValue( self.cmbSupplierPerson, record, 'supplierPerson_id')
        getLineEditValue(self.edtNote, record, 'note')
        return record


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
#        if orgStructureId:
        self.cmbSupplierPerson.setOrgStructureId(orgStructureId)
        if hasattr(self, 'modelItems'):
            self.modelItems.setSupplierId(orgStructureId)
        self._on_cmbSupplierChanged()


    def _on_cmbSupplierChanged(self):
        pass


    @pyqtSignature('const QDate&')
    def on_edtDate_dateChanged(self, date):
        self.edtTime.setEnabled(bool(date) if self.edtDate.isEnabled() else False)


    def _generateStockMotionNumber(self):
        if unicode(self.edtNumber.text()):
            return
        counterId = getStockMotionNumberCounterId(self.stockDocumentType)
        if not counterId:
            return
        number = QtGui.qApp.getDocumentNumber(None, counterId, date=QtCore.QDate.currentDate())
        self.edtNumber.setText(number)


    def resetCounterNumber(self):
        return False


    def exec_(self):
        counterController = QtGui.qApp.counterController()
        if not counterController:
            QtGui.qApp.setCounterController(CCounterController(self))
        result = None
        try:
            if not self._id or (not self._id and not hasattr(self, 'requisitionIdList')):
                self._generateStockMotionNumber()
            result = CItemEditorBaseDialog.exec_(self)
        finally:
            if not counterController:
                if result:
                    self.parent().applyMotionsFilter()
                    QtGui.qApp.delAllCounterValueIdReservation()
                else:
                    QtGui.qApp.resetAllCounterValueIdReservation()
            elif self.resetCounterNumber() and counterController.lastReservationId:
                QtGui.qApp.resetCounterValueIdReservation(counterController.lastReservationId)
        if not counterController:
            QtGui.qApp.setCounterController(None)
        return result


class CNomenclatureItemsBaseModel(CInDocTableModel):
    class CExistsCol(CFloatInDocTableCol):
        def __init__(self, model):
            CFloatInDocTableCol.__init__(self, u'Остаток', 'existsColumn', 10, precision=QtGui.qApp.numberDecimalPlacesQnt())
            self.model = model
            self._cache = {}
            self.stockDocumentType = None
            self.isUpdateValue = False
            self.isStockRequsition = False

        def setIsStockRequsition(self, value):
            self.isStockRequsition = value

        def setIsUpdateValue(self, isUpdateValue):
            self.isUpdateValue = isUpdateValue


        def setStockDocumentType(self, stockDocumentType):
            self.stockDocumentType = stockDocumentType


        def getExistsValue(self, record):
            price = forceDouble(record.value('price'))
            nomenclatureId = forceRef(record.value('nomenclature_id'))
            unitId = forceRef(record.value('unit_id'))
            ratio = self.model.getRatio(nomenclatureId, None, unitId)
            if ratio is not None:
                price = price*ratio
            financeId = forceRef(record.value('finance_id'))
            batch = forceString(record.value('batch'))
            shelfTime = forceDate(record.value('shelfTime'))
            shelfTime = shelfTime.toPyDate() if bool(shelfTime) else None
            medicalAidKindId = forceRef(record.value('medicalAidKind_id'))
            key = (nomenclatureId, financeId, batch, unitId, shelfTime, medicalAidKindId, price)
            return self._cache.get(key, 0)


        def toString(self, val, record):
            price = forceDouble(record.value('price'))
            nomenclatureId = forceRef(record.value('nomenclature_id'))
            unitId = forceRef(record.value('unit_id'))
            ratio = self.model.getRatio(nomenclatureId, None, unitId)
            if ratio is not None:
                price = price*ratio
            financeId = forceRef(record.value('finance_id'))
            batch = forceString(record.value('batch'))
            shelfTime = forceDate(record.value('shelfTime'))
            shelfTime = shelfTime.toPyDate() if bool(shelfTime) else None
            medicalAidKindId = forceRef(record.value('medicalAidKind_id'))
            otherHaving=[u'(shelfTime>=curDate()) OR shelfTime is NULL'] if self.stockDocumentType != CStockMotionType.utilization else []
#            qnt = forceDouble(record.value('qnt'))
#            prevQnt = forceDouble(record.value('prevQnt'))
#            deltaQnt = prevQnt - qnt
            key = (nomenclatureId, financeId, batch, unitId, shelfTime, medicalAidKindId, price)
            if self.isUpdateValue:
                existsQnt = getExistsNomenclatureAmountEx(nomenclatureId, financeId, batch, unitId=unitId, medicalAidKindId = medicalAidKindId, shelfTime=shelfTime, otherHaving=otherHaving, exact=True, price=price, isStockUtilization=self.stockDocumentType == CStockMotionType.utilization, isStockRequsition=self.isStockRequsition)
                self._cache[key] = existsQnt# + deltaQnt
            else:
                if key not in self._cache:
                    existsQnt = getExistsNomenclatureAmountEx(nomenclatureId, financeId, batch, unitId=unitId, medicalAidKindId = medicalAidKindId, shelfTime=shelfTime, otherHaving=otherHaving, exact=True, price=price, isStockUtilization=self.stockDocumentType == CStockMotionType.utilization, isStockRequsition=self.isStockRequsition)
                    self._cache[key] = existsQnt# + deltaQnt
            self.isUpdateValue = False
            return QVariant(self._toString(QVariant(self._cache[key])))

    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'StockMotion_Item', 'id', 'master_id', parent)
        self.stockDocumentType = parent.stockDocumentType
        self.isPriceLineEditable = False
        self.isUpdateValue = False
        self._mapNomenclatureIdToUnitId = {}
        self._supplierOrgId = None
        self._receiverId = None
        self._supplierId = None
        self.precision = None


    def getEmptyRecord(self):
        record = CInDocTableModel.getEmptyRecord(self)
        record.setValue('prevQnt', QVariant(1))
        return record


    def setIsUpdateValue(self, isUpdateValue):
        self.isUpdateValue = isUpdateValue
        self._cols[self.existsColumnIndex].setIsUpdateValue(self.isUpdateValue)


    def setStockDocumentTypeExistsCol(self):
        self._cols[self.existsColumnIndex].setStockDocumentType(self.stockDocumentType)


    def setSupplierOrgId(self, orgId):
        self._supplierOrgId = orgId


    def setReceiverId(self, orgStructureId):
        self._receiverId = orgStructureId


    def setSupplierId(self, orgStructureId):
        self._supplierId = orgStructureId


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


    def createPriceEditor(self, row, column, parent):
        editor = QtGui.QComboBox(parent)
        currentColumn = self.cols()[column]
        self.lineEdit = CPriceLineEdit(parent, currentColumn)
        editor.setLineEdit(self.lineEdit)
        self.isPriceLineEditable = False
        oldPrice = None
        if row >= 0 and row < len(self._items):
            item = self._items[row]
            oldPrice = self._toString(item.value('price'))
#            if self.stockDocumentType in (CStockMotionType.invoice, CStockMotionType.inventory, CStockMotionType.finTransfer, CStockMotionType.production):
            if self.stockDocumentType in (CStockMotionType.invoice, CStockMotionType.inventory, CStockMotionType.production):
                if self.stockDocumentType == CStockMotionType.inventory:
                    self.isPriceLineEditable = True
                elif self.stockDocumentType == CStockMotionType.invoice:
                    if self._receiverId and self._receiverId == QtGui.qApp.currentOrgStructureId():
                        self.isPriceLineEditable = True
                    elif self._supplierOrgId:
                        self.isPriceLineEditable = True
                    elif self._supplierId and self._supplierId != QtGui.qApp.currentOrgStructureId():
                        self.isPriceLineEditable = True
#                elif self.stockDocumentType == CStockMotionType.finTransfer:
#                    self.isPriceLineEditable = True
                elif self.stockDocumentType == CStockMotionType.production:
                    self.isPriceLineEditable = not forceBool(item.value('isOut'))
        if self.isPriceLineEditable:
            editor.setEditable(self.isPriceLineEditable)
            editor.lineEdit().setReadOnly(not self.isPriceLineEditable)
        editor.clear()
        editor.addItems(self._getPriceEditorItemsByRow(row))
        if oldPrice is not None:
#            currentIndex = editor.findText('%.2f'%(oldPrice), Qt.MatchFixedString)
            currentIndex = editor.findText('%s'%(self._toString(oldPrice)), Qt.MatchFixedString)
            editor.setCurrentIndex(currentIndex)
        editor.lineEdit().selectAll()
        return editor


    def setPriceEditorData(self, row, editor, value, record):
#        index = editor.findText('%.2f'%(forceDouble(value)), Qt.MatchFixedString)
        index = editor.findText('%s'%(self._toString(value)), Qt.MatchFixedString)
        if index < 0:
            editor.setCurrentIndex(0)
        else:
            editor.setCurrentIndex(index)


#    def getPriceEditorData(self, row, editor):
#        return toVariant(editor.currentText())


    def getPriceEditorData(self, row, editor):
        return toVariant(editor.currentText().toDouble()[0])


    def _getPriceEditorItemsByRow(self, row):
        priceList = QStringList(u'')
        priceTemp = []
        if 0 <= row < len(self._items):
            item = self._items[row]
            if item:
                oldPrice = self._toString(item.value('price'))
                if oldPrice and self.isPriceLineEditable:
                    priceTemp.append(oldPrice)
                if self.stockDocumentType == CStockMotionType.utilization:
                    isStockUtilization = True
                    filterFor = UTILIZATION
                elif self.stockDocumentType == CStockMotionType.internalConsumption:
                    isStockUtilization = False
                    filterFor = INTERNAL_CONSUMPTION
                else:
                    isStockUtilization = False
                    filterFor = None
                stmt = getPriceNomenclatureStmt(item, exact=True, isStockUtilization=isStockUtilization, filterFor=filterFor, isStrictMedicalAidKindId = True, isFinTransfer=(self.stockDocumentType == CStockMotionType.finTransfer))
                query = QtGui.qApp.db.query(stmt)
                while query.next():
                    record = query.record()
                    price = self._toString(record.value('price'))
                    price = self.calcPriceByRatio(forceDouble(price), item)
                    if price and price not in priceTemp:
                        priceTemp.append(price)
        priceTemp.sort()
        for price in priceTemp:
#            priceList.append('%.2f'%(price))
            priceList.append('%s'%(price))
        return priceList


    def _toString(self, value):
        s = QString()
        if value.isNull():
            return s
        if self.precision is None:
            s.setNum(value.toDouble()[0])
        else:
            s.setNum(value.toDouble()[0], 'f', self.precision)
        return s


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
        result = self._mapNomenclatureIdToUnitId.get(nomenclatureId)
        if result is None:
            record = QtGui.qApp.db.getRecord('rbNomenclature',
                                             ('defaultStockUnit_id', 'defaultClientUnit_id'),
                                             nomenclatureId
                                            )
            if record:
                defaultStockUnitId = forceRef(record.value('defaultStockUnit_id'))
                defaultClientUnitId = forceRef(record.value('defaultClientUnit_id'))
            else:
                defaultStockUnitId = defaultClientUnitId = None
            result = {
                       'defaultStockUnitId' : defaultStockUnitId,
                       'defaultClientUnitId': defaultClientUnitId
                     }
            self._mapNomenclatureIdToUnitId[nomenclatureId] = result
        return result


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
        financeId = forceRef(item.value('finance_id'))
        medicalAidKindId = forceRef(item.value('medicalAidKind_id'))
        shelfTime = forceDate(item.value('shelfTime'))
        stockPrice = self.priceCache.getPrice(nomenclatureId, financeId, batch, medicalAidKindId, shelfTime)
        qnt = forceDouble(item.value(qntCol))
        unit_id = forceRef(item.value('unit_id'))
        stockUnitId = self.getDefaultStockUnitId(nomenclatureId)
        ratio = self.getApplySumRatio(nomenclatureId, unit_id, stockUnitId)
        if ratio is None:
            return 0.0
        stockQnt = qnt*ratio
        return stockQnt*stockPrice


    def getApplySumRatio(self, nomenclatureId, oldUnitId, newUnitId):
        if oldUnitId is None:
            oldUnitId = self.getDefaultStockUnitId(nomenclatureId)
        if newUnitId is None:
            newUnitId = self.getDefaultStockUnitId(nomenclatureId)
        if oldUnitId == newUnitId:
            return 1
        return getNomenclatureUnitRatio(nomenclatureId, oldUnitId, newUnitId)


    def _applyQntRatio(self, item, oldUnitId, newUnitId,  qntCol='qnt'):
        qnt = forceDouble(item.value(qntCol))
        if not qnt:
            return
        nomenclatureId = forceRef(item.value('nomenclature_id'))
        ratio = self.getRatio(nomenclatureId, oldUnitId, newUnitId)
        item.setValue(qntCol, toVariant(qnt*ratio))


    def getRatio(self, nomenclatureId, oldUnitId, newUnitId):
        if oldUnitId is None:
            oldUnitId = self.getDefaultStockUnitId(nomenclatureId)
        if newUnitId is None:
            newUnitId = self.getDefaultStockUnitId(nomenclatureId)
        if oldUnitId == newUnitId:
            return 1
        ratio = getNomenclatureUnitRatio(nomenclatureId, oldUnitId, newUnitId)
        return ratio


    def calcSum(self, item, qntCol='qnt', batch=None, priceCol='price'):
        nomenclatureId = forceRef(item.value('nomenclature_id'))
        qnt = forceDouble(item.value(qntCol))
        price = forceDouble(item.value(priceCol))
        unitId = forceRef(item.value('unit_id'))
        stockUnitId = self.getDefaultStockUnitId(nomenclatureId)
        ratio = self.getRatio(nomenclatureId, unitId, stockUnitId)
        stockQnt = qnt*ratio
        return stockQnt*price


    def calcPriceByRatio(self, price, item):
        if price:
            unitId = forceRef(item.value('unit_id'))
            nomenclatureId = forceRef(item.value('nomenclature_id'))
            stockUnitId = self.getDefaultStockUnitId(nomenclatureId)
            ratio = self.getRatio(nomenclatureId, unitId, stockUnitId)
            if ratio is not None:
                price = price*ratio
        return price


    def updatePriceByRatio(self, item, oldUnitId, priceCol='price'):
        price = forceDouble(item.value(priceCol))
        if price:
            newUnitId = forceRef(item.value('unit_id'))
            nomenclatureId = forceRef(item.value('nomenclature_id'))
            ratio = self.getRatio(nomenclatureId, newUnitId, oldUnitId)
            if ratio is not None:
                price = price*ratio
        return price


#    def calcSum(self, item, qntCol='qnt', batch=None):
#        nomenclatureId = forceRef(item.value('nomenclature_id'))
#        financeId = forceRef(item.value('finance_id'))
#        medicalAidKindId = forceRef(item.value('medicalAidKind_id'))
#        shelfTime = forceDate(item.value('shelfTime'))
#        stockPrice = self.priceCache.getPrice(nomenclatureId, financeId, batch, medicalAidKindId, shelfTime)
#
#        qnt = forceDouble(item.value(qntCol))
#        unit_id = forceRef(item.value('unit_id'))
#        stockUnitId = self.getDefaultStockUnitId(nomenclatureId)
#        ratio = self.getRatio(nomenclatureId, unit_id, stockUnitId)
#        stockQnt = qnt*ratio
#        return stockQnt*stockPrice


class CDoubleValidator(QtGui.QDoubleValidator):
    def __init__(self, parent, currentColumn):
        QtGui.QDoubleValidator.__init__(self, parent)
        self.precision = None
        self.setRange(currentColumn.low, currentColumn.high) #, currentColumn.precision)
        self.decimalPoints = [u',', u'.', u',', u'.']


#    def validate(self, value, pos):
#        if unicode(QString(value.at(pos-1))) in self.decimalPoints:
#            for point in self.decimalPoints:
#                value = value.replace(QString(point), QString(self.locale().decimalPoint()))
#        return QtGui.QDoubleValidator.validate(self, value, pos)


class CPriceLineEdit(QtGui.QLineEdit):
    def __init__(self, parent, currentColumn):
        QtGui.QLineEdit.__init__(self, parent)
#        self._validator = CDoubleValidator(self, currentColumn)
#        self.setValidator(self._validator)
#        self.setCursorPosition(0)
        self.selectAll()


    def setValue(self, value):
        v = forceDouble(value)
        self.setText(str(v))


    def value(self):
        return self.text().toDouble()[0]

