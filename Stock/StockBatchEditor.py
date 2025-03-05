# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2019 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4                    import QtGui
from PyQt4.QtCore             import Qt, pyqtSignature, QVariant, QModelIndex, QAbstractTableModel, QDate

from library.DialogBase       import CDialogBase
from library.database         import CTableRecordCache
from library.PreferencesMixin import CDialogPreferencesMixin
from library.Utils            import forceRef, forceString, forceStringEx, forceDate, toVariant, forceDouble, formatDate
from Stock.Utils              import getBatchRecords, UTILIZATION, getBatchSGTINRecords #, INTERNAL_CONSUMPTION

from Stock.Ui_StockBatchListEditor import Ui_StockBatchListEditor


class CStockBatchEditor(CDialogBase, Ui_StockBatchListEditor, CDialogPreferencesMixin):
    def __init__(self, parent, params):
        CDialogBase.__init__(self, parent)
        self.tableModel = CStockBatchInDocTableModel(self)
        self.tableSelectionModel = QtGui.QItemSelectionModel(self.tableModel, self)
        self.tableSelectionModel.setObjectName('tableSelectionModel')
        self.tableStockSGTINCodesModel = CStockSGTINCodesInDocTableModel(self)
        self.tableStockSGTINCodesSelectionModel = QtGui.QItemSelectionModel(self.tableStockSGTINCodesModel, self)
        self.tableStockSGTINCodesSelectionModel.setObjectName('tableStockSGTINCodesSelectionModel')
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.tblStockBatchList.setModel(self.tableModel)
        self.tblStockBatchList.setSelectionModel(self.tableSelectionModel)
        self.tblStockBatchList.installEventFilter(self)
        self.tblStockSGTINCodes.setModel(self.tableStockSGTINCodesModel)
        self.tblStockSGTINCodes.setSelectionModel(self.tableStockSGTINCodesSelectionModel)
        self.tblStockSGTINCodes.installEventFilter(self)
        self.cmbFinance.setTable('rbFinance', True)
        self.cmbMedicalAidKind.setTable('rbMedicalAidKind', True)
        self.nomenclatureId = params.get('nomenclatureId', None)
        self.inBatch = params.get('batch', None)
        self.inFinanceId = params.get('financeId', None)
        self.inShelfTime = params.get('shelfTime', None)
        self.inMedicalAidKindId = params.get('medicalAidKindId', None)
        self.inFilterFor = params.get('filterFor', None)
        self.getWindowTitle()
        self.batchSGTINRecords = {}
        self.setFilter()
        self.setChkDetailBySGTINEnabled()
        self.tblStockSGTINCodes.setVisible(False)
        self.outSGTIN = None
        self.outBatch = None
        self.outFinanceId = None
        self.outShelfTime = None
        self.outMedicalAidKindId = None
        self.outPrice = 0
        self.loadDialogPreferences()
        self.setModelCaches()


    def setChkDetailBySGTINEnabled(self, isEnable=False):
        self.chkDetailBySGTIN.setEnabled(isEnable)


    @pyqtSignature('bool')
    def on_chkDetailBySGTIN_toggled(self, value):
        self.updateSGTINList(value)


    def updateSGTINList(self, isChecked):
        batchSGTINList = []
        if isChecked:
            currentIndex = self.tblStockBatchList.currentIndex()
            if currentIndex.isValid():
                row = currentIndex.row()
                items = self.tblStockBatchList.model().items
                if row >= 0 and row < len(items):
                    item = items[row]
                    if item:
                        outBatch = forceString(item.value('batch'))
                        outFinanceId = forceRef(item.value('finance_id'))
                        outShelfTime = forceDate(item.value('shelfTime'))
                        outMedicalAidKindId = forceRef(item.value('medicalAidKind_id'))
                        keyDict = (outBatch, outShelfTime.toPyDate() if bool(outShelfTime) else None, outFinanceId, outMedicalAidKindId)
                        batchSGTINList = self.batchSGTINRecords.get(keyDict, [])
        self.tblStockSGTINCodes.model().loadItems(batchSGTINList)
        self.tblStockSGTINCodes.setVisible(isChecked)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_tableSelectionModel_currentRowChanged(self, current, previous):
        isChecked = self.chkDetailBySGTIN.isChecked()
        if isChecked:
            self.updateSGTINList(isChecked)


    def setModelCaches(self):
        db = QtGui.qApp.db
        self.tblStockBatchList.model().setFinanceCaches(CTableRecordCache(db, db.forceTable('rbFinance'), u'*', capacity=None))
        self.tblStockBatchList.model().setMedicalAidKindCaches(CTableRecordCache(db, db.forceTable('rbMedicalAidKind'), u'*', capacity=None))


    def setFilter(self):
        self.edtBatch.setText(self.inBatch)
        self.cmbFinance.setValue(self.inFinanceId)
        self.cmbMedicalAidKind.setValue(self.inMedicalAidKindId)
        self.edtShelfTime.setDate(self.inShelfTime)


    def getWindowTitle(self):
        if self.nomenclatureId:
            self.setWindowTitle(u'ЛСиИМН: %s .\nВведите параметры фильтра для отбора "Серии"'%(forceStringEx(QtGui.qApp.db.translate('rbNomenclature', 'id', self.nomenclatureId, 'name'))))
        else:
            self.setWindowTitle(u'ЛСиИМН не выбран!')


    def getBatchRecords(self):
        outRecords = {}
        outResult = []
        if self.nomenclatureId:
            filter = self.getFilter()
            batch = filter.get('batch', None)
            financeId = filter.get('financeId', None)
            shelfTime = filter.get('shelfTime', None)
            medicalAidKind = filter.get('medicalAidKindId', None)
            records = getBatchRecords(self.nomenclatureId, financeId = financeId, shelfTime = shelfTime, batch = batch, medicalAidKind = medicalAidKind, isStockUtilization = (self.inFilterFor == UTILIZATION), filterFor = self.inFilterFor, isStrictMedicalAidKindId = True)
            records.sort(key=lambda item: (forceDate(item.value('shelfTime')), forceString(item.value('batch')), forceDouble(item.value('price'))))
            for record in records:
                outBatch = forceString(record.value('batch'))
                outFinanceId = forceRef(record.value('finance_id'))
                outShelfTime = forceDate(record.value('shelfTime'))
                outMedicalAidKindId = forceRef(record.value('medicalAidKind_id'))
                keyDict = (outBatch, outShelfTime.toPyDate() if bool(outShelfTime) else None, outFinanceId, outMedicalAidKindId)
                outRecord = outRecords.get(keyDict, None)
                if not outRecord:
                    outRecords[keyDict] = record
            outKeys = outRecords.keys()
            outKeys.sort(key=lambda x: (QDate(x[1]) if x[1] else QDate(), x[0]))
            for outKey in outKeys:
                outRecord = outRecords.get(outKey, None)
                if outRecord:
                    outResult.append(outRecord)
        return outResult


    def getBatchSGTINRecords(self):
        outRecords = {}
        outResult = []
        self.batchSGTINRecords = {}
        if self.nomenclatureId:
            tempBatchSGTINList = {}
            filter = self.getFilter()
            batch = filter.get('batch', None)
            financeId = filter.get('financeId', None)
            shelfTime = filter.get('shelfTime', None)
            medicalAidKind = filter.get('medicalAidKindId', None)
            records = getBatchSGTINRecords(self.nomenclatureId, financeId = financeId, shelfTime = shelfTime, batch = batch, medicalAidKind = medicalAidKind, isStockUtilization = (self.inFilterFor == UTILIZATION), filterFor = self.inFilterFor, isStrictMedicalAidKindId = True)
            records.sort(key=lambda item: (forceDate(item.value('shelfTime')), forceString(item.value('batch')), forceDouble(item.value('price'))))
            for record in records:
                outBatch = forceString(record.value('batch'))
                outFinanceId = forceRef(record.value('finance_id'))
                outShelfTime = forceDate(record.value('shelfTime'))
                outMedicalAidKindId = forceRef(record.value('medicalAidKind_id'))
                outSGTIN = forceString(record.value('sgtin'))
                keyDict = (outBatch, outShelfTime.toPyDate() if bool(outShelfTime) else None, outFinanceId, outMedicalAidKindId)
                outRecord = outRecords.get(keyDict, None)
                if not outRecord:
                    outRecords[keyDict] = record
                tempBatchSGTINLine = tempBatchSGTINList.get(keyDict, [])
                batchSGTINList = self.batchSGTINRecords.get(keyDict, [])
                if outSGTIN and outSGTIN not in tempBatchSGTINLine:
                    tempBatchSGTINLine.append(outSGTIN)
                    batchSGTINList.append(record)
                self.batchSGTINRecords[keyDict] = batchSGTINList
                tempBatchSGTINList[keyDict] = tempBatchSGTINLine
            outKeys = outRecords.keys()
            outKeys.sort(key=lambda x: (QDate(x[1]) if x[1] else QDate(), x[0]))
            for outKey in outKeys:
                outRecord = outRecords.get(outKey, None)
                if outRecord:
                    outResult.append(outRecord)
        return outResult


    @pyqtSignature('QModelIndex')
    def on_tblStockBatchList_doubleClicked(self, index):
        self.outBatch = None
        self.outFinanceId = None
        self.outShelfTime = None
        self.outMedicalAidKindId = None
        self.outPrice = None
        self.outSGTIN = None
        currentIndex = self.tblStockBatchList.currentIndex()
        if currentIndex.isValid():
            row = currentIndex.row()
            items = self.tblStockBatchList.model().items
            if row >= 0 and row < len(items):
                item = items[row]
                if item:
                    self.outBatch = forceString(item.value('batch'))
                    self.outFinanceId = forceRef(item.value('finance_id'))
                    self.outShelfTime = forceDate(item.value('shelfTime'))
                    self.outMedicalAidKindId = forceRef(item.value('medicalAidKind_id'))
                    self.outPrice = forceDouble(item.value('price'))
        QtGui.QDialog.accept(self)


    @pyqtSignature('QModelIndex')
    def on_tblStockSGTINCodes_doubleClicked(self, index):
        self.outBatch = None
        self.outFinanceId = None
        self.outShelfTime = None
        self.outMedicalAidKindId = None
        self.outPrice = None
        self.outSGTIN = None
        currentIndex = self.tblStockBatchList.currentIndex()
        if currentIndex.isValid():
            row = currentIndex.row()
            items = self.tblStockBatchList.model().items
            if row >= 0 and row < len(items):
                item = items[row]
                if item:
                    self.outBatch = forceString(item.value('batch'))
                    self.outFinanceId = forceRef(item.value('finance_id'))
                    self.outShelfTime = forceDate(item.value('shelfTime'))
                    self.outMedicalAidKindId = forceRef(item.value('medicalAidKind_id'))
                    self.outPrice = forceDouble(item.value('price'))
        currentIndex = self.tblStockSGTINCodes.currentIndex()
        if currentIndex.isValid():
            row = currentIndex.row()
            items = self.tblStockSGTINCodes.model().items
            if row >= 0 and row < len(items):
                item = items[row]
                if item:
                    self.outSGTIN = forceString(item.value('sgtin'))
        QtGui.QDialog.accept(self)


    def getBatchData(self):
        outBatch = None
        outFinanceId = None
        outShelfTime = None
        outMedicalAidKindId = None
        outPrice = None
        items = self.tblStockBatchList.model().items
        if len(items) > 0:
            item = items[0]
            if item:
                outBatch = forceString(item.value('batch'))
                outFinanceId = forceRef(item.value('finance_id'))
                outShelfTime = forceDate(item.value('shelfTime'))
                outMedicalAidKindId = forceRef(item.value('medicalAidKind_id'))
                outPrice = forceDouble(item.value('price'))
        return outBatch, outFinanceId, outShelfTime, outMedicalAidKindId, outPrice


    @pyqtSignature('QAbstractButton*')
    def on_buttonBoxFilter_clicked(self, button):
        buttonCode = self.buttonBoxFilter.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.on_buttonBox_apply()
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.on_buttonBox_reset()


    def on_buttonBox_reset(self):
        self.edtBatch.setText(u'')
        self.cmbFinance.setValue(None)
        self.cmbMedicalAidKind.setValue(None)
        self.edtShelfTime.setDate(QDate())
        self.outBatch = None
        self.outFinanceId = None
        self.outShelfTime = None
        self.outMedicalAidKindId = None
        self.outMedicalAidKindId = None
        self.outPrice = None
        self.loadData()


    def on_buttonBox_apply(self):
        self.loadData()


    def getFilter(self):
        filter = {}
        filter['batch'] = forceString(self.edtBatch.text())
        filter['financeId'] = forceRef(self.cmbFinance.value())
        filter['shelfTime'] = forceDate(self.edtShelfTime.date())
        filter['medicalAidKindId'] = forceRef(self.cmbMedicalAidKind.value())
        return filter


    def loadData(self):
        self.tblStockBatchList.model().items = []
        if not self.nomenclatureId:
            self.tblStockBatchList.model().reset()
            return
        if self.chkDetailBySGTIN.isEnabled():
            self.tblStockBatchList.model().loadItems(self.getBatchSGTINRecords())
        else:
            self.tblStockBatchList.model().loadItems(self.getBatchRecords())


    def getValue(self):
        if self.chkDetailBySGTIN.isEnabled():
            return self.outBatch, self.outFinanceId, self.outShelfTime, self.outMedicalAidKindId, self.outPrice, self.outSGTIN
        else:
            return self.outBatch, self.outFinanceId, self.outShelfTime, self.outMedicalAidKindId, self.outPrice


    def saveData(self):
        return True


class CStockSGTINCodesInDocTableModel(QAbstractTableModel):
    def __init__(self, parent):
        QAbstractTableModel.__init__(self, parent)
        self.headers = [u'Код вторичной упаковки']
        self.items = []


    def items(self):
        return self.items


    def columnCount(self, index = None):
        return len(self.headers)


    def rowCount(self, index = None):
        return len(self.items)


    def flags(self, index = QModelIndex()):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled


    def headerData(self, section, orientation, role = Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return QVariant(self.headers[section])
        return QVariant()


    def data(self, index, role=Qt.DisplayRole):
        row = index.row()
        if role == Qt.DisplayRole:
            if 0 <= row < len(self.items):
                item = self.items[row]
                if item:
                    return toVariant(item.value('sgtin'))
        return QVariant()


    def loadItems(self, records):
        self.items = records
        self.reset()


class CStockBatchInDocTableModel(QAbstractTableModel):
    def __init__(self, parent):
        QAbstractTableModel.__init__(self, parent)
        self.headers = [u'Серия', u'Срок годности', u'Тип финансирования', u'Вид мед. помощи']
        self.items = []
        self.financeCaches = {}
        self.medicalAidKindCaches = {}


    def items(self):
        return self.items


    def columnCount(self, index = None):
        return len(self.headers)


    def rowCount(self, index = None):
        return len(self.items)


    def flags(self, index = QModelIndex()):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled


    def headerData(self, section, orientation, role = Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return QVariant(self.headers[section])
        return QVariant()


    def setFinanceCaches(self, cache):
        self.financeCaches = cache


    def setMedicalAidKindCaches(self, cache):
        self.medicalAidKindCaches = cache


    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        row = index.row()
        if role == Qt.DisplayRole:
            if 0 <= row < len(self.items):
                item = self.items[row]
                if item:
                    if column == 0:
                        return toVariant(item.value('batch'))
                    elif column == 1:
                        return toVariant(formatDate(item.value('shelfTime')))
                    elif column == 2:
                        financeId = forceRef(item.value('finance_id'))
                        record = self.financeCaches.get(financeId) if financeId else None
                        if record:
                            return toVariant(record.value('name'))
                    elif column == 3:
                        medicalAidKindId = forceRef(item.value('medicalAidKind_id'))
                        record = self.medicalAidKindCaches.get(medicalAidKindId) if medicalAidKindId else None
                        if record:
                            return toVariant(record.value('name'))
        return QVariant()


    def loadItems(self, records):
        self.items = records
        self.reset()

