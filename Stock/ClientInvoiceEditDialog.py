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
from PyQt4.QtCore import Qt, QDateTime, QVariant, pyqtSignature, SIGNAL

from library.crbcombobox    import CRBComboBox
from library.InDocTable        import CDateInDocTableCol, CFloatInDocTableCol, CInDocTableCol, CRBInDocTableCol
from library.interchange      import getDateEditValue, getDatetimeEditValue, getLineEditValue, getRBComboBoxValue, setDateEditValue, setDatetimeEditValue, setLineEditValue, setRBComboBoxValue
from library.ItemsListDialog import CItemEditorBaseDialog
from library.PrintInfo           import CInfoContext
from library.PrintTemplates import applyTemplate, CPrintAction, CPrintButton, getPrintTemplates
from library.Utils                  import forceDouble, forceRef, forceString, toVariant, forceDate, pyDate
from Registry.Utils               import getClientInfo, getClientString, getClientBanner
from Reports.ReportBase     import CReportBase, createTable
from Reports.ReportView     import CReportViewDialog
from Stock.NomenclatureComboBox import CNomenclatureInDocTableCol
from Stock.StockMotionBaseDialog import CStockMotionBaseDialog, CNomenclatureItemsBaseModel
from Stock.StockModel          import CStockMotionType
from Stock.StockBatchEditor import CStockBatchEditor
from Users.Rights                  import urAccessStockEditSupplier, urAccessStockEditSupplierPerson
from Stock.Utils                     import CPriceItemDelegate, getStockMotionItemQuantityColumn, getExistsNomenclatureAmountEx, getStockMotionItemQntEx, CStockCache, CSummaryInfoModelMixin

from Stock.Ui_ClientInvoice              import Ui_ClientInvoiceDialog
from Stock.Ui_ClientRefundInvoice   import Ui_ClientRefundInvoiceDialog


class CClientInvoiceEditDialog(CStockMotionBaseDialog, Ui_ClientInvoiceDialog):
    stockDocumentType = 4 # Списание на пациента

    def __init__(self,  parent, fromAction=False, isNotSuper = False):
        if isNotSuper:
            CStockMotionBaseDialog.__init__(self, parent)
        else:
            super(self.__class__, self).__init__(parent)
        self._fromAction = fromAction
        self.closeByOkButton = False
        self.addModels('Items', CItemsModel(self))
        self.addObject('btnPrint', CPrintButton(self, u'Печать'))
        self.addObject('actOpenStockBatchEditor', QtGui.QAction(u'Подобрать параметры', self))
        self.btnPrint.setShortcut('F6')
        self.setupUi(self)
        if hasattr(self, 'cmbSupplierPerson'):
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
        if fromAction:
#            self.tblItems.addPopupDelRow()
#             self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Close)
            self.edtDate.setReadOnly(True)
            self.edtTime.setReadOnly(True)
        else:
            self.setupDirtyCather()
#            self.prepareItemsPopupMenu(self.tblItems)
        self._clientId = None
        self._clientInfo = None
        self._supplierId = None
        self.getRightEditSupplier()
        self.tblItems.setItemDelegateForColumn(CItemsModel.priceColumnIndex, CPriceItemDelegate(self.tblItems))
        self.tblItems.enableColsMove()


    def done(self, result):
        if self._fromAction:
            # Когда мы работаем с накладной на списание из редакторов действия
            # логика сохранения данных вынесена в другие объекты
            # по этом здесь имитируем закрытие кнопкой отмены,
            # но информацию о том как азкрывали диалог сохраняем
            self.closeByOkButton = result > 0
            CStockMotionBaseDialog.done(self, 0)
        else:
            CStockMotionBaseDialog.done(self, result)


    def setSupplierId(self, value):
        self._supplierId = value
        if hasattr(self, 'cmbSupplier'):
            self.cmbSupplier.setValue(self._supplierId)
            record = CStockMotionBaseDialog.getRecord(self)
            getRBComboBoxValue(self.cmbSupplier, record, 'supplier_id')
            self.setRecord(record)


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
                    params = {}
                    params['nomenclatureId'] = forceRef(item.value('nomenclature_id'))
                    params['batch'] = forceString(item.value('batch'))
                    params['financeId'] = forceRef(item.value('finance_id'))
                    params['shelfTime'] = forceDate(item.value('shelfTime'))
                    params['medicalAidKindId'] = forceRef(item.value('medicalAidKind_id'))
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
                            try:
                                item.setValue('sum', toVariant(forceDouble(item.value('qnt')) * forceDouble(item.value('price'))))
                            except:
                                item.setValue('sum', toVariant(0.0))
                            self.modelItems.reset()
                    finally:
                        dialog.deleteLater()
            else:
                self.emit(SIGNAL('doubleClicked(QModelIndex)'), index)


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
        if hasattr(self, 'cmbSupplier'):
            supplier = self.cmbSupplier.value()
            if supplier:
                description.append(u'Получатель %s'%forceString(db.translate('OrgStructure', 'id', supplier, 'name')))
        if hasattr(self, 'cmbSupplierPerson'):
            supplierPerson = self.cmbSupplierPerson.value()
            if supplierPerson:
                description.append(u'Ответственный %s'%forceString(db.translate('vrbPersonWithSpeciality', 'id', supplierPerson, 'name')))
        if hasattr(self, 'cmbReceiver'):
            receiver = self.cmbReceiver.value()
            if receiver:
                description.append(u'Получатель %s'%forceString(db.translate('OrgStructure', 'id', receiver, 'name')))
        if hasattr(self, 'cmbReceiverPerson'):
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
        cursor.insertText(u'Пациент: %s' % (getClientString(self._clientId)))
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


    def getRightEditSupplier(self):
        app = QtGui.qApp
        isAdmin = app.isAdmin()
        self.cmbSupplier.setEnabled(app.userHasRight(urAccessStockEditSupplier) or isAdmin)
        self.cmbSupplierPerson.setEnabled(app.userHasRight(urAccessStockEditSupplierPerson) or isAdmin)


    def exec_(self):
        self.lblSummaryInfo.setText(self.modelItems.getSummaryInfo())
        return CStockMotionBaseDialog.exec_(self)


    def resetCounterNumber(self):
        result = not len(self.modelItems.items())
        if result:
            self.edtNumber.setText('')
        return result


    def setRecord(self, record):
        CStockMotionBaseDialog.setRecord(self, record)
        self.setClientId(forceRef(record.value('client_id')))
        self.modelItems.loadItems(self.itemId())
        self.lblSummaryInfo.setText(self.modelItems.getSummaryInfo())
        self.setIsDirty(False)


    def getRecord(self):
        record = CStockMotionBaseDialog.getRecord(self)
        record.setValue('type', self.stockDocumentType)
        record.setValue('client_id', self._clientId)
        return record


    def setClientId(self, clientId):
        if self._clientId != clientId:
            self._clientId = clientId
            self.setClientInfo()
            self.modelItems.setClientId(self._clientId)


    def setFinanceId(self, financeId):
        self.modelItems.setFinanceId(financeId)


    def setMedicalAidKindId(self, medicalAidKindId):
        self.modelItems.setMedicalAidKindId(medicalAidKindId)


    def setClientInfo(self):
        if not self._clientInfo and self._clientId:
            self._clientInfo = getClientInfo(self._clientId, date=self.edtDate.date())
        if self._clientInfo:
            self.txtClientInfoBrowser.setHtml(getClientBanner(self.clientId, self.edtDate.date()))


    def setStockMotionItems(self, items):
        for item in items:
            try:
                item.setValue('sum', toVariant(forceDouble(item.value('qnt')) * forceDouble(item.value('price'))))
            except:
                item.setValue('sum', toVariant(0.0))
        self.modelItems.setItems(items)


    def setData(self, data):
        if data:
            self.setRecord(data.stockMotionRecord())
            self.setStockMotionItems(data.stockMotionItems())


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
        else:
            return True


    def checkNomenclatureExists(self, keys, item, supplierId=None):
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
        if self.stockDocumentType != CStockMotionType.clientReservation:
            reservationQnt = round(getStockMotionItemQntEx(nomenclatureId, stockMotionId=None, batch=batch, financeId=financeId, clientId=self._clientId, medicalAidKindId=medicalAidKindId, price=None, oldPrice=price, oldUnitId=stockUnitId), QtGui.qApp.numberDecimalPlacesQnt())
            resQnt = (round(existsQnt, QtGui.qApp.numberDecimalPlacesQnt()) + reservationQnt + prevQnt) - round(qnt, QtGui.qApp.numberDecimalPlacesQnt())
        else:
            resQnt = (round(existsQnt, QtGui.qApp.numberDecimalPlacesQnt()) + prevQnt) - round(qnt, QtGui.qApp.numberDecimalPlacesQnt())
        if resQnt < 0:
            nomenclatureName = self.modelItems.getNomenclatureNameById(nomenclatureId)
            if existsQnt > 0:
                message = u'На складе {0} {3} {1}, а списание на {2}'.format(existsQnt, nomenclatureName, qnt, forceString(QtGui.qApp.db.translate('rbUnit', 'id', stockUnitId, 'name')))
            else:
                message = u'На складе отсутствует {1} партии {3} годный до {4} вида мед помощи "{5}"'.format(   existsQnt,
                                                                                                                nomenclatureName,
                                                                                                                qnt,
                                                                                                                batch if batch else u'не указано',
                                                                                                                shelfTimeString if shelfTime else u'не указано',
                                                                                                                medicalAidKindName if medicalAidKindName else u'не указано')
            return self.checkValueMessage(message, False, self.tblItems, row, self.modelItems.qntColumnIndex)
        return True


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_modelItems_dataChanged(self,  topLeftIndex, bottomRightIndex):
        self.lblSummaryInfo.setText(self.modelItems.getSummaryInfo())



class CClientRefundInvoiceEditDialog(Ui_ClientRefundInvoiceDialog, CClientInvoiceEditDialog):
    stockDocumentType = 5 # Возврат от пациента

    def __init__(self,  parent, fromAction=False):
        CClientInvoiceEditDialog.__init__(self,  parent, fromAction, isNotSuper=True)


    def getRightEditSupplier(self):
        pass


    def getPrice(self, nomenclatureId, financeId, batch=None, medicalAidKindId=None, shelfTime=None):
        return CStockCache.getPrice(self, QtGui.qApp.currentOrgStructureId(), nomenclatureId, financeId, batch, medicalAidKindId, shelfTime)


    def setDefaults(self):
        now = QDateTime.currentDateTime()
        self.edtDate.setDate(now.date())
        self.edtTime.setTime(now.time())
        self.cmbReceiver.setValue(QtGui.qApp.currentOrgStructureId())


    def setData(self, data):
        if data:
            self.setClientInvoiceRecord(data.stockMotionRecord())
            self.setStockMotionItems(data.stockMotionItems())


    def setClientInvoiceRecord(self, record):
        self.setClientId(forceRef(record.value('client_id')))
        setLineEditValue(   self.edtNumber,         record, 'number')
        # setDatetimeEditValue(self.edtDate, self.edtTime, record, 'date')
        setLineEditValue(   self.edtReason,    record, 'reason')
        setDateEditValue(   self.edtReasonDate,record, 'reasonDate')
        setRBComboBoxValue( self.cmbReceiver,       record, 'supplier_id')
        setRBComboBoxValue( self.cmbReceiverPerson, record, 'supplierPerson_id')
        setLineEditValue(   self.edtNote,           record, 'note')
        # дату и время нужно истановить текщие
        now = QDateTime.currentDateTime()
        self.edtDate.setDate(now.date())
        self.edtTime.setTime(now.time())


    def loadDataFromClientInvoice(self, clientInvoiceId):
        record = QtGui.qApp.db.getRecord('StockMotion', '*', clientInvoiceId)
        self.setClientInvoiceRecord(record)
        self.modelItems.loadItems(clientInvoiceId)
        self.modelItems.clearItemIds()
        self.lblSummaryInfo.setText(self.modelItems.getSummaryInfo())
        self.setIsDirty(False)


    def setRecord(self, record):
        CItemEditorBaseDialog.setRecord(self, record)
        self.setClientId(forceRef(record.value('client_id')))
        setLineEditValue(   self.edtNumber,         record, 'number')
        setDatetimeEditValue(self.edtDate, self.edtTime, record, 'date')
        setLineEditValue(   self.edtReason,    record, 'reason')
        setDateEditValue(   self.edtReasonDate,record, 'reasonDate')
        setRBComboBoxValue( self.cmbReceiver,       record, 'receiver_id')
        setRBComboBoxValue( self.cmbReceiverPerson, record, 'receiverPerson_id')
        setLineEditValue(   self.edtNote,           record, 'note')
        self.modelItems.loadItems(self.itemId())
        self.lblSummaryInfo.setText(self.modelItems.getSummaryInfo())
        self.setIsDirty(False)


    def getRecord(self):
        record = CItemEditorBaseDialog.getRecord(self)
        record.setValue('type',      self.stockDocumentType)
        record.setValue('client_id', self._clientId)
        getLineEditValue(   self.edtNumber,         record, 'number')
        getDatetimeEditValue(self.edtDate, self.edtTime, record, 'date', True)
        getLineEditValue(   self.edtReason,    record, 'reason')
        getDateEditValue(   self.edtReasonDate,record, 'reasonDate')
        getRBComboBoxValue( self.cmbReceiver,       record, 'receiver_id')
        getRBComboBoxValue( self.cmbReceiverPerson, record, 'receiverPerson_id')
        getLineEditValue(   self.edtNote,           record, 'note')
        return record


class CClientInvoiceReservationEditDialog(CClientInvoiceEditDialog):
    stockDocumentType = 6  # Резервирование на пациента

    def __init__(self,  parent, fromAction=False):
        CClientInvoiceEditDialog.__init__(self,  parent, fromAction, isNotSuper=True)


# ########################################################################
class CItemsModel(CNomenclatureItemsBaseModel, CSummaryInfoModelMixin):
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

    class CBatchCol(CInDocTableCol):
        def __init__(self):
            CInDocTableCol.__init__(self, u'Серия', 'batch', 16)

    class CSumCol(CFloatInDocTableCol):
        def _toString(self, value):
            if value.isNull():
                return None
            return format(forceDouble(value), '.2f')

    class CLocNomenclatureCol(CNomenclatureInDocTableCol):
        def createEditor(self, parent):
            editor = CNomenclatureInDocTableCol.createEditor(self, parent)
            editor.setOrgStructureId(QtGui.qApp.currentOrgStructureId())
            editor.setOnlyExists()
            return editor


    def __init__(self, parent, showExists=False):
        self.priceCache = parent
        CNomenclatureItemsBaseModel.__init__(self, parent)
        #CNomenclatureItemsBaseModel.__init__(self, 'StockMotion_Item', 'id', 'master_id', parent)
        self._unitColumn = CRBInDocTableCol(u'Ед.Учета', 'unit_id', 12, 'rbUnit', addNone=False)
        self._nomenclatureColumn = CItemsModel.CLocNomenclatureCol(u'ЛСиИМН', 'nomenclature_id', 50, showFields = CRBComboBox.showName)
        self.addCol(self._nomenclatureColumn)
        self.batchCol = CItemsModel.CBatchCol().setReadOnly()
        self.addCol(self.batchCol)
        self.addCol(CDateInDocTableCol(u'Годен до', 'shelfTime', 12, canBeEmpty=True).setReadOnly())
        self.addCol(CRBInDocTableCol(  u'Тип финансирования', 'finance_id', 15, 'rbFinance').setReadOnly())
        self.addCol(CRBInDocTableCol(  u'Вид медицинской помощи', 'medicalAidKind_id', 15, 'rbMedicalAidKind').setReadOnly())
        self.addCol(getStockMotionItemQuantityColumn( u'Кол-во', 'qnt', 12))
        self.addCol(self._unitColumn)
        self.addCol(CFloatInDocTableCol(u'Цена', 'price', 12, precision=2))
        self.addCol(CItemsModel.CSumCol( u'Сумма', 'sum', 12).setReadOnly())
        self.existsCol = CItemsModel.CExistsCol(self).setReadOnly()
        self.addExtCol(self.existsCol, QVariant.Double)
        self._financeCache = {}
        self._cachRow2CommonSum = {}
        self._financeId = None
        self._medicalAidKindId = None
        self._clientId = None
        self.setStockDocumentTypeExistsCol()


    def setFinanceId(self, financeId):
        self._financeId = financeId

    def setMedicalAidKindId(self, medicalAidKindId):
        self._medicalAidKindId = medicalAidKindId

    def getNomenclatureNameById(self, nomenclatureId):
        return forceString(self._nomenclatureColumn.toString(nomenclatureId, None))


    def setClientId(self, clientId):
        self._clientId = clientId


    def getEmptyRecord(self):
        record = CNomenclatureItemsBaseModel.getEmptyRecord(self)
        record.setValue('qnt', QVariant(1))
        return record


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
                if not result:
                    return False
                item = self._items[row]
                nomenclatureId = forceRef(self._items[row].value('nomenclature_id'))
                if nomenclatureId != oldNomenclatureId:
                    item.setValue('batch', QVariant(''))
                    item.setValue('finance_id', QVariant(None))
                    item.setValue('unit_id', toVariant(self.getDefaultClientUnitId(nomenclatureId)))
                    item.setValue('sum', QVariant(0.0))
                self.emitRowChanged(row)
            elif column == self.getColIndex('unit_id'):
                if not (0 <= row < len(self._items)):
                    return False
                item = self._items[row]
                oldUnitId = forceRef(item.value('unit_id'))
                result = CNomenclatureItemsBaseModel.setData(self, index, value, role)
                if result:
                    self.setIsUpdateValue(True)
                    newUnitId = forceRef(item.value('unit_id'))
#                    self._applySumRatio(item, oldUnitId, newUnitId)
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
                if not result:
                    return False
                self.setIsUpdateValue(True)
                item = self._items[row]
                if column == self.getColIndex('qnt'):
                    item.setValue('prevQnt', prevQnt)
                item.setValue('sum', toVariant(forceDouble(item.value('qnt')) * forceDouble(item.value('price'))))
                self.emitRowChanged(row)
            elif column in (self.batchColumnIndex, self.shelfTimeColumnIndex, self.financeColumnIndex, self.medicalAidKindColumnIndex):
                return False
            else:
                result = CNomenclatureItemsBaseModel.setData(self, index, value, role)
        else:
            result = CNomenclatureItemsBaseModel.setData(self, index, value, role)

        return result


#    def _countSum(self, row, item):
#        nomenclatureId = forceRef(item.value('nomenclature_id'))
#        _filter = { 'batch': forceString(item.value('batch')),
#                    'financeId': forceRef(item.value('finance_id')),
#                    'medicalAidKindId': forceRef(item.value('medicalAidKind_id')),
#                    'shelfTime': forceDate(item.value('shelfTime'))
#                  }
#        existsData = getExistsNomenclature([nomenclatureId], _filter)
#        syncNomenclature(existsData, item, unset=True, translateExistsQnt=True)


    def flags(self, index):
        column = index.column()
        if column in (self.batchColumnIndex, self.shelfTimeColumnIndex, self.financeColumnIndex, self.medicalAidKindColumnIndex):
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return CNomenclatureItemsBaseModel.flags(self, index)

