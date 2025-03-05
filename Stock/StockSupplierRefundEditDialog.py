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
from PyQt4.QtCore import Qt, pyqtSignature, QDateTime, QVariant

from Stock.Mdlp.ExchangePurpose import CMdplExchangePurpose
from library.Identification import getIdentification
from library.crbcombobox         import CRBComboBox
from library.InDocTable          import CDateInDocTableCol, CFloatInDocTableCol, CInDocTableCol, CRBInDocTableCol
from library.interchange         import getRBComboBoxValue, setRBComboBoxValue, getLineEditValue, setLineEditValue, setDatetimeEditValue, getDatetimeEditValue
from library.PrintInfo           import CInfoContext
from library.PrintTemplates      import applyTemplate, CPrintAction, CPrintButton, getPrintTemplates
from library.Utils               import forceDouble, forceRef, forceString, toVariant, forceInt, pyDate, forceDate
from library.ItemsListDialog     import CItemEditorBaseDialog
from Reports.ReportBase          import CReportBase, createTable
from Reports.ReportView          import CReportViewDialog
from Stock.StockModel            import CStockMotionType
from Stock.NomenclatureComboBox  import CNomenclatureInDocTableCol
from Stock.StockMotionBaseDialog import CStockMotionBaseDialog, CStockMotionItemsCopyPasteMixin, CNomenclatureItemsBaseModel
from Stock.Utils                 import (getNomenclatureAnalogies,
                                          getStockMotionItemQuantityColumn,
                                          getExistsNomenclatureAmount,
                                          getBatchShelfTimeFinance,
                                          checkNomenclatureExists,
                                          CPriceItemDelegate,
                                          CSummaryInfoModelMixin,
                                        )


from Stock.Mdlp.connection import CMdlpConnection

from Stock.Ui_StockSupplierRefundDialog import Ui_StockSupplierRefundDialog


class CStockSupplierRefundEditDialog(CStockMotionBaseDialog, CStockMotionItemsCopyPasteMixin, Ui_StockSupplierRefundDialog):
    stockDocumentType = CStockMotionType.supplierRefund #Возврат поставщику

    def __init__(self,  parent):
        CStockMotionBaseDialog.__init__(self, parent)
        CStockMotionItemsCopyPasteMixin.__init__(self, parent)
        self.addModels('Items', CItemsModel(self))
        self.addObject('btnPrint', CPrintButton(self, u'Печать'))
        self.btnPrint.setShortcut('F6')
        self.addObject('btnMDLPExchange', QtGui.QPushButton(u'Выполнить обмен с МДЛП', self))
        self.addObject('mnuMDLPExchange', QtGui.QMenu(self))
        self.addObject('actSendDocument417', QtGui.QAction(u'Отправить документ по схеме 417', self))
        self.addObject('actSendDocument4152', QtGui.QAction(u'Отправить документ по схеме 415-2', self))
        self.mnuMDLPExchange.addAction(self.actSendDocument4152)
        self.mnuMDLPExchange.addAction(self.actSendDocument417)
        self.btnMDLPExchange.setMenu(self.mnuMDLPExchange)
        self.btnMDLPExchange.setEnabled(QtGui.qApp.isMdlpEnabled())
        # self.actSendDocument4152.setEnabled(False)
        # self.actSendDocument417.setEnabled(False)
        self.setupUi(self)
        self.cmbReceiverPerson.setSpecialityIndependents()
        self.cmbSupplierOrg.setFilter('isSupplier = 1')
        self.cmbFinance.setTable('rbFinance')
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setupDirtyCather()
        self.buttonBox.addButton(self.btnPrint, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnMDLPExchange, QtGui.QDialogButtonBox.ActionRole)
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
        self.tblItems.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.tblItems.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.requisitionIdList = None
        self.protectFields()
        self.tblItems.setItemDelegateForColumn(CItemsModel.priceColumnIndex, CPriceItemDelegate(self.tblItems))
        self.tblItems.enableColsMove()
        self.cmbContractType.setItems()
        self.connection = None

    def protectFields(self, isEditable=True):
        self.edtInvoiceNumber.setReadOnly(isEditable)
        self.edtInvoiceDate.setReadOnly(isEditable)
        self.edtInvoiceTime.setReadOnly(isEditable)
        self.cmbSupplierOrg.setReadOnly(isEditable)
        self.cmbReceiver.setReadOnly(isEditable)
        self.cmbSupplier.setReadOnly(isEditable)


    def getStockContext(self):
        return ['StockSupplierRefund']


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
            data = { 'stockSupplierRefundList': CStockMotionInfoList(context, idList)}
            QtGui.qApp.call(self, applyTemplate, (self, templateId, data))


    def dumpParams(self, cursor):
        db = QtGui.qApp.db
        description = []
        number = self.edtNumber.text()
        if number:
            description.append(u'Номер %s'%forceString(number))
        date = QDateTime(self.edtDate.date(), self.edtTime.time())
        if date:
           description.append(u'Дата %s'%forceString(date))
        invoiceNumber = self.edtInvoiceNumber.text()
        if invoiceNumber:
            description.append(u'Номер накладной %s'%forceString(invoiceNumber))
        invoiceDate = QDateTime(self.edtInvoiceDate.date(), self.edtInvoiceTime.time())
        if invoiceDate:
           description.append(u'Дата накладной %s'%forceString(invoiceDate))
        supplierOrgId = self.cmbSupplierOrg.value()
        if supplierOrgId:
            description.append(u'Внешний Получатель %s'%forceString(db.translate('Organisation', 'id', supplierOrgId, 'fullName')))
            edtSupplierOrgPerson = self.edtSupplierOrgPerson.text()
            if edtSupplierOrgPerson:
                description.append(u'Внешний Получатель Ответственный %s'%forceString(edtSupplierOrgPerson))
        supplier = self.cmbSupplier.value()
        if supplier:
            description.append(u'Получатель %s'%forceString(db.translate('OrgStructure', 'id', supplier, 'name')))
        supplierPerson = self.cmbSupplierPerson.value()
        if supplierPerson:
            description.append(u'Получатель Ответственный %s'%forceString(db.translate('vrbPersonWithSpeciality', 'id', supplierPerson, 'name')))
        receiver = self.cmbReceiver.value()
        if receiver:
            description.append(u'Поставщик %s'%forceString(db.translate('OrgStructure', 'id', receiver, 'name')))
        receiverPerson = self.cmbReceiverPerson.value()
        if receiverPerson:
            description.append(u'Поставщик Ответственный %s'%forceString(db.translate('vrbPersonWithSpeciality', 'id', receiverPerson, 'name')))
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


    def setDefaults(self):
        now = QDateTime.currentDateTime()
        self.edtDate.setDate(now.date())
        self.edtTime.setTime(now.time())
        self.cmbReceiver.setValue(QtGui.qApp.currentOrgStructureId())


    def setRequsitions(self, requisitionIdList):
        if requisitionIdList:
            requisitionId = requisitionIdList[0]
            self.cmbReceiver.setValue(forceRef(QtGui.qApp.db.translate('StockRequisition', 'id', requisitionId, 'recipient_id')))
            number = forceString(QtGui.qApp.db.translate('StockRequisition', 'id', requisitionId, 'number'))
            stockMotionsCount = forceInt(QtGui.qApp.db.translate('StockRequisition', 'id', requisitionId, 'stockMotionsCount'))
            idx = forceString(stockMotionsCount + 1)
            self.edtNumber.setText(number + '/' + idx)
            self.cmbSupplier.setValue(QtGui.qApp.currentOrgStructureId())
            self.modelItems.setRequsitions(requisitionIdList)
            self.requisitionIdList = requisitionIdList


    def setSupplierRefundRecord(self, record):
        setLineEditValue(self.edtInvoiceNumber,     record, 'number')
        setDatetimeEditValue(self.edtInvoiceDate, self.edtInvoiceTime, record, 'date')
        setLineEditValue(self.edtNote,              record, 'note')
        setRBComboBoxValue( self.cmbReceiver,       record, 'receiver_id')
        setRBComboBoxValue( self.cmbReceiverPerson, record, 'receiverPerson_id')
        setRBComboBoxValue(self.cmbSupplierOrg,     record, 'supplierOrg_id')
        setLineEditValue(self.edtSupplierOrgPerson, record, 'supplierOrgPerson')
        setRBComboBoxValue(self.cmbSupplier,        record, 'supplier_id')
        setRBComboBoxValue(self.cmbSupplierPerson,  record, 'supplierPerson_id')
        now = QDateTime.currentDateTime()
        self.edtDate.setDate(now.date())
        self.edtTime.setTime(now.time())
        if forceInt(record.value('type')) != self.stockDocumentType:
            record.setValue('stockMotion_id', record.value('id'))
            record.setValue('id', toVariant(None))
            record.setValue('type', toVariant(self.stockDocumentType))
            CItemEditorBaseDialog.setRecord(self, record)


    def loadDataSupplierRefund(self, invoiceId):
        record = QtGui.qApp.db.getRecord('StockMotion', '*', invoiceId)
        self.setSupplierRefundRecord(record)
        self.modelItems.loadItems(invoiceId)
        self.modelItems.clearItemIds()
        self.lblSummaryInfo.setText(self.modelItems.getSummaryInfo())
        self.setIsDirty(False)


    def setRecord(self, record):
        CItemEditorBaseDialog.setRecord(self, record)
        setLineEditValue(self.edtNumber, record, 'number')
        setDatetimeEditValue(self.edtDate, self.edtTime, record, 'date')
        prevStockMotionId = forceRef(record.value('stockMotion_id'))
        if prevStockMotionId:
            prevRecord = QtGui.qApp.db.getRecord('StockMotion', 'number, date', prevStockMotionId)
            if prevRecord:
                setLineEditValue(self.edtInvoiceNumber, prevRecord, 'number')
                setDatetimeEditValue(self.edtInvoiceDate, self.edtInvoiceTime, prevRecord, 'date')
        setLineEditValue(self.edtNote,              record, 'note')
        setRBComboBoxValue(self.cmbReceiver,        record, 'supplier_id')
        setRBComboBoxValue(self.cmbReceiverPerson,  record, 'supplierPerson_id')
        setRBComboBoxValue(self.cmbSupplierOrg,     record, 'supplierOrg_id')
        setLineEditValue(self.edtSupplierOrgPerson, record, 'supplierOrgPerson')
        setRBComboBoxValue( self.cmbSupplier,       record, 'receiver_id')
        setRBComboBoxValue( self.cmbSupplierPerson, record, 'receiverPerson_id')
        self.cmbContractType.setCurrentIndex(forceInt(record.value('contractType')))
        self.modelItems.loadItems(self.itemId())
        self.lblSummaryInfo.setText(self.modelItems.getSummaryInfo())
        self.setIsDirty(False)


    def getRecord(self):
        record = CItemEditorBaseDialog.getRecord(self)
        getLineEditValue(self.edtNumber,            record, 'number')
        getDatetimeEditValue(self.edtDate, self.edtTime, record, 'date', True)
        getLineEditValue(self.edtNote,              record, 'note')
        getRBComboBoxValue(self.cmbReceiver,        record, 'supplier_id')
        getRBComboBoxValue(self.cmbReceiverPerson,  record, 'supplierPerson_id')
        getRBComboBoxValue(self.cmbSupplierOrg,     record, 'supplierOrg_id')
        getLineEditValue(self.edtSupplierOrgPerson, record, 'supplierOrgPerson')
        getRBComboBoxValue( self.cmbSupplier,       record, 'receiver_id')
        getRBComboBoxValue( self.cmbSupplierPerson, record, 'receiverPerson_id')
        if forceInt(record.value('type')) != self.stockDocumentType:
            record.setValue('stockMotion_id', toVariant(record.value('id')))
            record.setValue('id', toVariant(None))
            record.setValue('type', toVariant(self.stockDocumentType))
        record.setValue('contractType', toVariant(self.cmbContractType.currentIndex()))
        return record


    def saveInternals(self, id):
        self.modelItems.saveItems(id)
        if self.requisitionIdList:
            self.updateRequisition(motionId = id)


    def updateRequisition(self, motionId = None):
        db = QtGui.qApp.db
        tableSR = db.table('StockRequisition')
        tableSRI = db.table('StockRequisition_Item')
        if motionId:
            tableSRM = db.table('StockRequisition_Motions')
            for item in set(self.requisitionIdList):
                record = tableSRM.newRecord()
                record.setValue('master_id', toVariant(item))
                record.setValue('motion_id',  toVariant(motionId))
                db.insertOrUpdate(tableSRM, record)
        table = tableSRI.leftJoin(tableSR, tableSR['id'].eq(tableSRI['master_id']))
        requisitionItems = db.getRecordList(table,
                           'StockRequisition_Item.*',
                           [tableSRI['master_id'].inlist(self.requisitionIdList),
                            tableSR['recipient_id'].eq(self.cmbReceiver.value())
                           ],
                           'master_id, idx')

        fndict = self.modelItems.getDataAsFNDict()
        preciseGroupDict = {}
        masterId = None
        for item in requisitionItems:
            masterId = forceRef(item.value('master_id'))
            nomenclatureId = forceRef(item.value('nomenclature_id'))
            financeId = forceRef(item.value('finance_id'))
            #qnt = forceDouble(item.value('qnt'))
            satisfiedQnt = forceDouble(item.value('satisfiedQnt'))
            oldSatisfiedQnt = satisfiedQnt
            ndict = fndict.get(financeId, None)
            if ndict:
                if nomenclatureId in ndict:
                    nomenclatureIdList = [nomenclatureId]
                else:
                    nomenclatureIdList = preciseGroupDict.get(nomenclatureId, None)
                    if nomenclatureIdList is None:
                        nomenclatureIdList = getNomenclatureAnalogies(nomenclatureId)
                        preciseGroupDict[nomenclatureId] = nomenclatureIdList
                for nomenclatureId in nomenclatureIdList:
                    if nomenclatureId in ndict:
                        satisfiedQnt = ndict[nomenclatureId]
#                        outQnt = ndict[nomenclatureId]
#                        delta = min(max(0, qnt-satisfiedQnt), outQnt)
#                        if delta>0:
#                            ndict[nomenclatureId] -= delta
#                            satisfiedQnt += delta
#            if oldSatisfiedQnt != satisfiedQnt:
                        sumQnt = oldSatisfiedQnt + satisfiedQnt
                        item.setValue('satisfiedQnt', toVariant(sumQnt))
            db.updateRecord('StockRequisition_Item', item)
        if masterId:
            requisition = db.getRecordEx(table,
                   'StockRequisition.*',
                   [tableSR['id'].eq(masterId)
                   ])
            if requisition:
                stockMotionsCount = forceInt(requisition.value('stockMotionsCount'))
                stockMotionsCount += 1
                requisition.setValue('stockMotionsCount', toVariant(stockMotionsCount))
                db.updateRecord('StockRequisition', requisition)


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
            if supplierId and not checkNomenclatureExists(self, keys, item, supplierId):
                return False
        return True


    @pyqtSignature('int')
    def on_cmbSupplier_currentIndexChanged(self, val):
        orgStructureId = self.cmbReceiver.value()
        self.cmbSupplierPerson.setOrgStructureId(orgStructureId)
        self.modelItems.setSupplierId(self.cmbSupplier.value())


    @pyqtSignature('int')
    def on_cmbReceiver_currentIndexChanged(self, val):
        orgStructureId = self.cmbReceiver.value()
        self.cmbReceiverPerson.setOrgStructureId(orgStructureId)


    @pyqtSignature('int')
    def on_cmbSupplierOrg_currentIndexChanged(self, val):
        supplierOrgId = self.cmbSupplierOrg.value()
        currentOrgId = QtGui.qApp.currentOrgId()
        currentSupplierEnable = not supplierOrgId or (supplierOrgId and currentOrgId == supplierOrgId)
        self.cmbSupplier.setEnabled(currentSupplierEnable)
        self.cmbSupplierPerson.setEnabled(currentSupplierEnable)
        if not currentSupplierEnable:
            self.cmbSupplier.setValue(None)
            self.cmbSupplierPerson.setValue(None)
        self.edtSupplierOrgPerson.setEnabled(supplierOrgId and currentOrgId != supplierOrgId)


#    @pyqtSignature('QModelIndex')
#    def on_tblItems_doubleClicked(self, index):
#        self.emit(SIGNAL('doubleClicked(QModelIndex)'), index)


#    @pyqtSignature('QModelIndex')
#    def on_tblItems_clicked(self, index):
#        self.emit(SIGNAL('clicked(QModelIndex)'), index)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_modelItems_dataChanged(self,  topLeftIndex, bottomRightIndex):
        self.lblSummaryInfo.setText(self.modelItems.getSummaryInfo())

    def on_mnuMDLPExchange_aboutToShow(self):
        self.actSendDocument4152.setEnabled(QtGui.qApp.isMdlpEnabled() and bool(self.tblItems.model().items()))
        self.actSendDocument417.setEnabled(QtGui.qApp.isMdlpEnabled() and bool(self.tblItems.model().items()))

    def getConnection(self):
        if self.connection is None:
            self.connection = CMdlpConnection()
        return self.connection

    @pyqtSignature('')
    def on_actSendDocument4152_triggered(self):
        self.save()
        docNum = unicode(self.edtNumber.text())
        docDate = self.edtDate.date()
        sgtins = self.modelItems.getSgtins()
        supplierOrgId = self.cmbSupplierOrg.value()
        supplierMdlpId = getIdentification('Organisation', supplierOrgId, 'urn:mdlp:anyId', raiseIfNonFound=True)
        receiverId = self.cmbReceiver.value()
        receiverMdlpId = getIdentification('OrgStructure', receiverId, 'urn:mdlp:anyId', raiseIfNonFound=True)
        sourceType = self.cmbFinance.value()
        contractType = self.cmbContractType.currentIndex()
        # with CLogger(self, u'Обмен с МДЛП') as logger:
        #     QtGui.qApp.call(self,
        #                     iiroMoveProcess,
        #                     (logger, self._id, self.getConnection(), supplierMdlpId, receiverMdlpId, docNum, docDate,
        #                      sgtins, sgtins, CMdplExchangePurpose.iiroMoveOrder,
        #                      sourceType, contractType))

    @pyqtSignature('')
    def on_actSendDocument417_triggered(self):
        self.save()
        docNum = unicode(self.edtNumber.text())
        docDate = self.edtDate.date()
        sgtins = self.modelItems.getSgtins()
        supplierOrgId = self.cmbSupplierOrg.value()
        supplierMdlpId = getIdentification('Organisation', supplierOrgId, 'urn:mdlp:anyId', raiseIfNonFound=True)
        receiverId = self.cmbReceiver.value()
        receiverMdlpId = getIdentification('OrgStructure', receiverId, 'urn:mdlp:anyId', raiseIfNonFound=True)
        # with CLogger(self, u'Обмен с МДЛП') as logger:
        #     QtGui.qApp.call(self,
        #                     iiroMoveProcess,
        #                     (logger, self._id, self.getConnection(), supplierMdlpId,
        #                      receiverMdlpId, docNum, docDate, sgtins, sgtins, CMdplExchangePurpose.iiroMoveOrder)
        #                     )


class CItemsModel(CNomenclatureItemsBaseModel, CSummaryInfoModelMixin):
    priceColumnIndex = 8
    existsColumnIndex = 10

    class CSumCol(CFloatInDocTableCol):
        def _toString(self, value):
            if value.isNull():
                return None
            return format(forceDouble(value), '.2f')

    class CLocNomenclatureCol(CNomenclatureInDocTableCol):
        def __init__(self, title, fieldName, width, supplierId, **params):
            CNomenclatureInDocTableCol.__init__(self, title, fieldName, width, **params)
            self.supplierId = supplierId

        def setSupplierId(self, supplierId):
            self.supplierId = supplierId

        def createEditor(self, parent):
            editor = CNomenclatureInDocTableCol.createEditor(self, parent)
            editor.setOnlyNomenclature(True)
            return editor

    def __init__(self, parent, showExists=False):
        CNomenclatureItemsBaseModel.__init__(self, parent)

        isMdlpEnabled = QtGui.qApp.isMdlpEnabled()

        self.supplierId = None  # parent.cmbSupplier.value()

        self.addCol(CInDocTableCol(u'Код третичной упаковки', 'sscc', 18, readOnly=not isMdlpEnabled))
        self.addCol(CInDocTableCol(u'Код вторичной упаковки', 'sgtin', 50, readOnly=not isMdlpEnabled))

        self._nomenclatureColumn = self.CLocNomenclatureCol(u'ЛСиИМН', 'nomenclature_id', 50, self.supplierId, showFields = CRBComboBox.showName)
        self._unitColumn = CRBInDocTableCol(u'Ед.Учета', 'unit_id', 12, 'rbUnit', addNone=False).setReadOnly()
        self.addCol(self._nomenclatureColumn)
        self.addCol(CInDocTableCol( u'Серия', 'batch', 16).setReadOnly(True))
        self.addCol(CDateInDocTableCol( u'Годен до', 'shelfTime', 12, canBeEmpty=True).setReadOnly())
        # self.addCol(CRBInDocTableCol(u'Тип финансирования', 'finance_id', 15, 'rbFinance').setReadOnly())
        self.addCol(CRBInDocTableCol(u'Вид медицинской помощи', 'medicalAidKind_id', 15, 'rbMedicalAidKind').setReadOnly())
        self.addCol(getStockMotionItemQuantityColumn(u'Кол-во', 'qnt', 12).setReadOnly(False))
        self.addCol(self._unitColumn)
        self.addCol(CFloatInDocTableCol(u'Цена', 'price', 12, precision=2))
        sumCol = CItemsModel.CSumCol( u'Сумма', 'sum', 12).setReadOnly()
        self.addCol(sumCol.setReadOnly())
        existsCol = CItemsModel.CExistsCol(self)
        self.addExtCol(existsCol.setReadOnly(), QVariant.Double)
        self.priceCache = parent
        self.qntColumnIndex = self.getColIndex('qnt')
        self.requisitionItems = None
        self.setStockDocumentTypeExistsCol()


    def setSupplierId(self, supplierId):
        self.supplierId = supplierId
        self._cols[self.getColIndex('nomenclature_id')].setSupplierId(self.supplierId)


    def cellReadOnly(self, index):
        column = index.column()
        row = index.row()
        if 0 <= row < len(self._items):
            record = self._items[row]
            if record and column == record.indexOf('qnt'):
                return False
        return True


    def getNomenclatureNameById(self, nomenclatureId):
        return forceString(self._nomenclatureColumn.toString(nomenclatureId, None))


    def getEmptyRecord(self):
        record = CNomenclatureItemsBaseModel.getEmptyRecord(self)
        return record


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
        else:
            return CNomenclatureItemsBaseModel.setData(self, index, value, role)


    def setRequsitions(self, requisitionIdList):
        usedBatch = {}
        medicalAidKind = None
        db = QtGui.qApp.db
        table = db.table('StockRequisition_Item')
        tableSMI = db.table('StockMotion_Item')
        self.requisitionItems = db.getRecordList(table,
                           '*',
                           table['master_id'].inlist(requisitionIdList),
                           'master_id, idx')
        for item in self.requisitionItems:
            qnt = forceDouble(item.value('qnt'))-forceDouble(item.value('satisfiedQnt'))
            while qnt > 0:
                myItem = self.getEmptyRecord()
                nomenclatureId = forceRef(item.value('nomenclature_id'))
                if nomenclatureId not in usedBatch.keys():
                    usedBatch[nomenclatureId] = {}
                unitId = forceRef(item.value('unit_id'))
                medicalAidKindId = forceRef(item.value('medicalAidKind_id'))
                financeId = forceRef(item.value('finance_id'))
                if financeId not in usedBatch[nomenclatureId].keys():
                    usedBatch[nomenclatureId][financeId] = {}
                if medicalAidKindId not in usedBatch[nomenclatureId][financeId].keys():
                    usedBatch[nomenclatureId][financeId][medicalAidKindId] = []
                myItem.setValue('nomenclature_id', toVariant(nomenclatureId))
                batch, shelfTime, finance, medicalAidKind, price = getBatchShelfTimeFinance( nomenclatureId,
                                                                                             financeId,
                                                                                             filter = tableSMI['batch'].notInlist(usedBatch[nomenclatureId][financeId][medicalAidKindId]) if len(usedBatch[nomenclatureId][financeId][medicalAidKindId]) else None,
                                                                                             medicalAidKind = medicalAidKindId,
                                                                                             isStockRequsition=True)
                if batch is not None:
                    usedBatch[nomenclatureId][financeId][medicalAidKindId].append(batch)
                if batch or shelfTime or finance:
                    orgStructureId=QtGui.qApp.currentOrgStructureId()
                    existsQnt = getExistsNomenclatureAmount(nomenclatureId, financeId, batch, orgStructureId, unitId, medicalAidKind, shelfTime, exact=True, price=price, isStockRequsition=True)
                    if existsQnt > 0:
                        myItem.setValue('batch', toVariant(batch))
                        myItem.setValue('shelfTime', toVariant(shelfTime))
                        if finance:
                            myItem.setValue('finance_id', toVariant(finance))
                        if medicalAidKind:
                            myItem.setValue('medicalAidKind_id', toVariant(medicalAidKind))
                        myItem.setValue('unit_id', toVariant(unitId))
                        if 0<existsQnt<qnt:
                            myItem.setValue('qnt', toVariant(existsQnt))
                        else:
                            myItem.setValue('qnt', toVariant(qnt))
                        price = self.calcPriceByRatio(price, item)
                        myItem.setValue('price', toVariant(price))
                        myItem.setValue('sum', toVariant(forceDouble(myItem.value('price'))*forceDouble(myItem.value('qnt'))))
                        self.items().append(myItem)
                        if 0<existsQnt<qnt:
                            qnt = qnt - existsQnt
                        else:
                            break
                else:
                    break
        self.reset()


    def getDataAsFNDict(self):
        result = {}
        for item in self.items():
            financeId = forceRef(item.value('finance_id'))
            nomenclatureId = forceRef(item.value('nomenclature_id'))
            if nomenclatureId:
                ndict = result.setdefault(financeId, {})
                ndict[nomenclatureId]=ndict.get(nomenclatureId, 0) + forceDouble(item.value('qnt'))
        return result

    def getSgtins(self):
        sgtins = set()
        for item in self.items():
            sgtin = forceString(item.value('sgtin'))
            sgtins.add(sgtin)
        return list(sgtins)
