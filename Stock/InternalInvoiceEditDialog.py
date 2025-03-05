## -*- coding: utf-8 -*-
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
from PyQt4.QtGui import QMessageBox
from PyQt4.QtCore import Qt, QDate, QDateTime, QVariant, pyqtSignature, SIGNAL

from library.crbcombobox         import CRBComboBox
from library.InDocTable          import CDateInDocTableCol, CFloatInDocTableCol, CInDocTableCol, CRBInDocTableCol
from library.Identification      import getIdentification, findByIdentification
from library.interchange         import getRBComboBoxValue, setRBComboBoxValue
from library.PrintInfo           import CInfoContext
from library.PrintTemplates      import applyTemplate, CPrintAction, CPrintButton, getPrintTemplates
from library.Utils               import forceDouble, forceRef, forceString, toVariant, forceInt, forceDate, pyDate

from Reports.ReportBase          import CReportBase, createTable
from Reports.ReportView          import CReportViewDialog

from Stock.Mdlp.Logger           import CLogger
from Stock.Mdlp.Stage            import CMdlpStage
from Stock.Mdlp.connection       import CMdlpConnection
from Stock.Mdlp.iimProcess       import iimProcess
from Stock.Mdlp.iiwdProcess      import iiwdProcess
from Stock.Mdlp.selectWithdrawalsByRegisrar import selectWithdrawalsByRegisrar
from Stock.Mdlp.DisposalOrderEditDialog import CDisposalOrderEditDialog
from Stock.NomenclatureComboBox  import CNomenclatureInDocTableCol
from Stock.StockMotionBaseDialog import CStockMotionBaseDialog, CStockMotionItemsCopyPasteMixin, CNomenclatureItemsBaseModel
from Stock.StockBatchEditor      import CStockBatchEditor

from Stock.Utils                 import (
                                          getNomenclatureAnalogies,
                                          getStockMotionItemQuantityColumn,
                                          getExistsNomenclatureAmount,
                                          getBatchShelfTimeFinance,
                                          checkNomenclatureExists,
                                          CPriceItemDelegate,
                                          CSummaryInfoModelMixin,
                                        )

from Ui_InternalInvoice import Ui_InternalInvoiceDialog


class CInternalInvoiceEditDialog(CStockMotionBaseDialog, CStockMotionItemsCopyPasteMixin, Ui_InternalInvoiceDialog):
    stockDocumentType = 0 #Накладная
    # режимы обмена с МДЛП ( Mdlp Mode )
    mmNone         = 0 # без МДЛП
    mmMove         = 1 # перемещение
    mmDispByDoc    = 2 # выбытие по документу (без РВ)
    mmDispByReg1   = 3 # выбытие с РВ, первый вариант (данные сканируются РВ)
    mmDispByReg2   = 4 # выбытие с РВ, второй вариант (отсканированные данные передаются в РВ)
    mmNames        = { mmNone:         u'без МДЛП',
                       mmMove:         u'перемещение',
                       mmDispByDoc:    u'выбытие по документу',
                       mmDispByReg1:   u'выбытие сканированием РВ',
                       mmDispByReg2:   u'выбытие с передачей данных в РВ',
                     }

    def __init__(self,  parent):
        CStockMotionBaseDialog.__init__(self, parent)
        CStockMotionItemsCopyPasteMixin.__init__(self, parent)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)

        self.addModels('Items', CItemsModel(self))
        self.addObject('btnPrint', CPrintButton(self, u'Печать'))
        self.addObject('btnPrepareDispRequestToRegistrar', QtGui.QPushButton(u'Подготовить отчёт о выбытии для РВ', self))
        self.addObject('actReceiveDocument10531', QtGui.QAction(u'Принять документ по схеме 10531', self))
        self.addObject('actSendDocument531', QtGui.QAction(u'Отправить документ по схеме 531', self))
        self.addObject('actSendDocument431', QtGui.QAction(u'Отправить документ по схеме 431', self))
        self.addObject('btnMDLPExchange', QtGui.QPushButton(u'Выполнить обмен с МДЛП', self))
        self.addObject('mnuMDLPExchange', QtGui.QMenu(self))
        self.mnuMDLPExchange.addAction(self.actReceiveDocument10531)
        self.mnuMDLPExchange.addAction(self.actSendDocument531)
        self.mnuMDLPExchange.addAction(self.actSendDocument431)
        self.btnMDLPExchange.setMenu(self.mnuMDLPExchange)
        self.actReceiveDocument10531.setEnabled(False)
        self.actSendDocument531.setEnabled(False)
        self.actSendDocument431.setEnabled(False)

        self.addObject('btnProductionEditDialog', QtGui.QPushButton(u'Производство', self))
        self.btnPrint.setShortcut('F6')
        self.addObject('actOpenStockBatchEditor', QtGui.QAction(u'Подобрать параметры', self))

        self.setupUi(self)

        self.cmbReceiverPerson.setSpecialityIndependents()
        self.cmbSupplierPerson.setSpecialityIndependents()
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
        self.tblItems.popupMenu().addSeparator()
        self.tblItems.popupMenu().addAction(self.actOpenStockBatchEditor)
        self.tblItems.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.tblItems.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)

        self.buttonBox.addButton(self.btnPrepareDispRequestToRegistrar, QtGui.QDialogButtonBox.ActionRole)
        self.btnPrepareDispRequestToRegistrar.setEnabled(False)
        self.buttonBox.addButton(self.btnProductionEditDialog, QtGui.QDialogButtonBox.ActionRole)
        self.requisitionIdList = None
        self.isStockRequsition = False
        self.tblItems.setItemDelegateForColumn(CItemsModel.priceColumnIndex, CPriceItemDelegate(self.tblItems))
        self._initView()

        if QtGui.qApp.isMdlpEnabled():
            self.connect(QtGui.qApp, SIGNAL('sgtinReceived(QString)'), self.onSgtinReceived)
        else:
            self.btnMDLPExchange.setDisabled(True)
            self.actReceiveDocument10531.setDisabled(True)

#        self.connect(QtGui.qApp, SIGNAL('gtinReceived(QString)'),  self.onGtinReceived)

        self.mdlpStage  = None
        self.connection = None
        self.mdlpDocumentIds = None

        self.supplierMdlpId = None
        self.receiverMdlpId = None
        self.mdlpMode = self.mmNone

        self.updateMdlpMode()
        self._blockSgtinReceiving = False
        self.tblItems.enableColsMove()


    def save(self):
        id = CStockMotionBaseDialog.save(self)
        return id


    def evalMdlpMode(self, supplierMdlpId, receiverMdlpId):
        if not QtGui.qApp.isMdlpEnabled(): # МДЛП ненастроен
            return self.mmNone

        if not supplierMdlpId or not self.cmbReceiver.value():             # у поставщика нет идентификации либо получатель отсутствует вовсе
            return self.mmNone
        elif receiverMdlpId:               # 431 scheme движение move
            return self.mmMove
        elif self.documentDisposalOrder(): # ничего запрашивать и принимать не требуется
            return self.mmNone
        elif not self.modelItems.items(): # таблица пуста принять по 10531
            return self.mmDispByReg1
        elif not self.documentDisposalOrder() and self.modelItems.items():  # отправить по 531
            return self.mmDispByDoc


    def updateMdlpMode(self):
        self.mdlpMode = self.evalMdlpMode(self.supplierMdlpId, self.receiverMdlpId)
        self.setWindowTitle(u'Внутренняя накладная на передачу ЛСиИМН (%s)' % self.mmNames[self.mdlpMode])
        self.btnMDLPExchange.setEnabled(self.mdlpMode != self.mmNone)
        self.btnPrepareDispRequestToRegistrar.setEnabled(QtGui.qApp.isMdlpRetRegEnabled()) # Эта кнопка не зависит от состояния накладной


    # WFT?
    def getOrgStructureIdList(self):
        orgStructureIdList = []
        orgId = QtGui.qApp.currentOrgId()
        if orgId:
            orgId = QtGui.qApp.currentOrgId()
            supplierId = self.cmbSupplier.value()
            receiverId = self.cmbReceiver.value()
            if orgId and supplierId and receiverId:
                db = QtGui.qApp.db
                tableOS = db.table('OrgStructure')
                orgStructureIdList = db.getDistinctIdList(tableOS, [tableOS['id']], [tableOS['organisation_id'].eq(orgId), tableOS['deleted'].eq(0)])
        return orgStructureIdList


    def setIsStockRequsition(self, value):
        self.isStockRequsition = value
        self.modelItems.setIsStockRequsition(self.isStockRequsition)


    @pyqtSignature('')
    def on_actOpenStockBatchEditor_triggered(self):
        self.on_tblItems_doubleClicked(self.tblItems.currentIndex())


    @pyqtSignature('QModelIndex')
    def on_tblItems_doubleClicked(self, index):
        if index and index.isValid():
            col = index.column()
            if col in (CItemsModel.batchColumnIndex, CItemsModel.shelfTimeColumnIndex, CItemsModel.financeColumnIndex, CItemsModel.medicalAidKindColumnIndex):
#                supplierId = self.cmbSupplier.value()
#                receiverId = self.cmbReceiver.value()
#                if supplierId and receiverId:
#                    orgStructureIdList = self.getOrgStructureIdList()
#                    if orgStructureIdList and supplierId in orgStructureIdList and receiverId in orgStructureIdList:
                items = self.modelItems.items()
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
                        dialog.setChkDetailBySGTINEnabled(True)
                        dialog.loadData()
                        if dialog.exec_():
                            outBatch, outFinanceId, outShelfTime, outMedicalAidKindId, outPrice, outSGTIN = dialog.getValue()
                            item.setValue('batch', toVariant(outBatch))
                            item.setValue('finance_id', toVariant(outFinanceId))
                            item.setValue('shelfTime', toVariant(outShelfTime))
                            item.setValue('medicalAidKind_id', toVariant(outMedicalAidKindId))
                            if outSGTIN:
                                item.setValue('sgtin', toVariant(outSGTIN))
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


    def getStockContext(self):
        return ['InvoiceCreate']



    @pyqtSignature('int')
    def on_btnPrint_printByTemplate(self, templateId):
        self.actPrintMotions(templateId)

    def on_mnuMDLPExchange_aboutToShow(self):
        self.actSendDocument431.setEnabled(False)
        self.actReceiveDocument10531.setEnabled(False)
        self.actSendDocument531.setEnabled(False)

        self.mdlpMode = self.evalMdlpMode(self.supplierMdlpId, self.receiverMdlpId)
        if self.mdlpMode == self.mmMove:
            self.actSendDocument431.setEnabled(True)
        elif self.mdlpMode == self.mmDispByReg1:
            self.actReceiveDocument10531.setEnabled(True)
        elif self.mdlpMode == self.mmDispByDoc:
            self.actSendDocument531.setEnabled(True)


    def actPrintMotions(self, templateId):
        from Stock.StockMotionInfo import CStockMotionInfoList
        if templateId == -1:
            self.getNomenclaturePrint()
        else:
            idList = self.tblItems.model().itemIdList()
            context = CInfoContext()
            data = { 'invoicesList': CStockMotionInfoList(context, idList)}
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
        reason = self.edtReason.text()
        if reason:
            description.append(u'Основание %s'%forceString(reason))
        reasonDate = self.edtReasonDate.date()
        if reasonDate:
           description.append(u'Дата основания %s'%forceString(reasonDate))
        supplier = self.cmbSupplier.value()
        if supplier:
            description.append(u'Поставщик %s'%forceString(db.translate('OrgStructure', 'id', supplier, 'name')))
        supplierPerson = self.cmbSupplierPerson.value()
        if supplierPerson:
            description.append(u'Ответственный %s'%forceString(db.translate('vrbPersonWithSpeciality', 'id', supplierPerson, 'name')))
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


    def setDefaults(self):
        now = QDateTime.currentDateTime()
        self.edtDate.setDate(now.date())
        self.edtTime.setTime(now.time())
        self.cmbSupplier.setValue(QtGui.qApp.currentOrgStructureId())
        self.cmbSupplierPerson.setValue(QtGui.qApp.userId)


    def setRequsitions(self, requisitionIdList):
        if requisitionIdList:
            requisitionId = requisitionIdList[0]
            self.cmbReceiver.setValue(forceRef(QtGui.qApp.db.translate('StockRequisition', 'id', requisitionId, 'recipient_id')))
            self.cmbReceiverPerson.setValue(forceRef(QtGui.qApp.db.translate('StockRequisition', 'id', requisitionId, 'recipientPerson_id')))
            number = forceString(QtGui.qApp.db.translate('StockRequisition', 'id', requisitionId, 'number'))
            stockMotionsCount = forceInt(QtGui.qApp.db.translate('StockRequisition', 'id', requisitionId, 'stockMotionsCount'))
            idx = forceString(stockMotionsCount + 1)
            self.edtNumber.setText(number + '/' + idx)
            self.cmbSupplier.setValue(QtGui.qApp.currentOrgStructureId())
            self.modelItems.setRequsitions(requisitionIdList)
            self.requisitionIdList = requisitionIdList


    def setRecord(self, record):
        CStockMotionBaseDialog.setRecord(self, record)
        setRBComboBoxValue( self.cmbReceiver, record, 'receiver_id')
        setRBComboBoxValue( self.cmbReceiverPerson, record, 'receiverPerson_id')
        self.mdlpStage = forceInt(record.value('mdlpStage'))
        self.modelItems.loadItems(self.itemId())
        self.lblSummaryInfo.setText(self.modelItems.getSummaryInfo())
        self.setIsDirty(False)


    def getRecord(self):
        record = CStockMotionBaseDialog.getRecord(self)
        getRBComboBoxValue( self.cmbReceiver, record, 'receiver_id')
        getRBComboBoxValue( self.cmbReceiverPerson, record, 'receiverPerson_id')
        if self.mdlpStage in [None, 0]: # не задан или не нужен - тогда еще можем что-то изменить
            storedMdlpStage = CMdlpStage.unnecessary # нужно не storedMdlpStage а что-то другое...
            if self.mdlpMode in [self.mmMove, self.mmDispByDoc]:
                sgtins = self.modelItems.getSgtins()
                if sgtins:
                    storedMdlpStage = CMdlpStage.ready
            record.setValue('mdlpStage', storedMdlpStage)

        record.setValue('type', self.stockDocumentType)
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
        findFinanceGroupDict = {}
        notFinanceIdDict = {}
        for item in requisitionItems:
            nomenclatureId = forceRef(item.value('nomenclature_id'))
            financeId = forceRef(item.value('finance_id'))
            findFinanceLine = findFinanceGroupDict.get(nomenclatureId, [])
            if financeId and financeId not in findFinanceLine:
                findFinanceLine.append(financeId)
                findFinanceGroupDict[nomenclatureId] = findFinanceLine
        for item in requisitionItems:
            masterId = forceInt(item.value('master_id'))
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
            elif not financeId:
                findFinanceIdLine = findFinanceGroupDict.get(nomenclatureId, [])
                for nFinanceIdKey, ndictLine in fndict.items():
                    if nFinanceIdKey:
                        for nNomenclatureId, nSatisfiedQnt in ndictLine.items():
                            if nNomenclatureId == nomenclatureId and nFinanceIdKey not in findFinanceIdLine:
                                notFinanceIdLine = notFinanceIdDict.get(nNomenclatureId, [])
                                if nFinanceIdKey not in notFinanceIdLine:
                                    nSumQnt = forceDouble(item.value('satisfiedQnt')) + nSatisfiedQnt
                                    item.setValue('satisfiedQnt', toVariant(nSumQnt))
                                    notFinanceIdLine.append(nFinanceIdKey)
                                    notFinanceIdDict[nNomenclatureId] = notFinanceIdLine
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

    def documentDisposalOrder(self):
        documentNumber = unicode(self.edtNumber.text())
        documentDate = self.edtDate.date()
        # documetTime = self.edtTime.time()
        db = QtGui.qApp.db
        table = db.table('DisposalOrder')
        cond = [ table['baseInvoiceNumber'].eq(documentNumber),
                 table['baseInvoiceDate'].dateEq(documentDate)
               ]
        ids = db.getIdList(table, where=cond, order='id', limit=1)
        return ids[0] if ids else None



    # WTF?
    def setBatchReadOnly(self):
        self.modelItems.isBatchReadOnly = False
        supplierId = self.cmbSupplier.value()
        receiverId = self.cmbReceiver.value()
        if supplierId and receiverId:
            orgStructureIdList = self.getOrgStructureIdList()
            if orgStructureIdList and supplierId in orgStructureIdList and receiverId in orgStructureIdList:
                self.modelItems.isBatchReadOnly = True
        self.actOpenStockBatchEditor.setEnabled(self.modelItems.isBatchReadOnly)


    def getConnection(self):
        if self.connection is None:
            self.connection = CMdlpConnection()
        return self.connection


    def useNotificationMode(self):
        return QtGui.qApp.isMdlpEnabled() and self.getConnection().notificationMode


    def onSgtinReceived(self, sgtin):
        if self._blockSgtinReceiving:
            return
        row = self.modelItems.findRowWithSgtin(sgtin)
        if row is not None:
            self.tblItems.setCurrentIndex(self.modelItems.index(row, self.modelItems.sgtinColumnIndex))
            return
        if self.supplierMdlpId:
            connection = self.getConnection()
            succ, fail = connection.getPublicSgtinsByList([unicode(sgtin)])
            if succ:
                if (    self.useNotificationMode() # не известно у кого
                     or self.mdlpMode == self.mmDispByReg2 # для проверки выбытия mmDispByReg2
                     or succ[0].ownerId == self.supplierMdlpId # у поставщика
                   ):
                    row = self.modelItems.addSgtinObject(succ[0])
                    self.tblItems.setCurrentIndex(self.modelItems.index(row, self.modelItems.sgtinColumnIndex))
                else:
                    QMessageBox.information(self,
                                            u'Ошибка',
                                            u'В МДЛП у поставщика «%s» не найден sgtin «%s»' % (self.supplierMdlpId, sgtin),
                                            QMessageBox.Close,
                                            QMessageBox.Close
                                           )
            else:
                QMessageBox.information(self,
                                        u'Ошибка',
                                        u'В МДЛП не найден sgtin «%s»' % sgtin,
                                        QMessageBox.Close,
                                        QMessageBox.Close
                                       )


    def onGtinReceived(self, gtin):
        pass
#        modelItems = self.modelItems
#        if not modelItems.isMdlpRelatedGtinPresent(gtin):
#            nomenclatureId = findByIdentification('rbNomenclature', 'urn:gtin', gtin, raiseIfNonFound=False)
#            if not nomenclatureId:
#                QMessageBox.information(self,
#                                        u'ЛСиИМН не найдено',
#                                        u'Не удаётся найти ЛСиИМН с кодом GTIN «%s»' % gtin,
#                                        QMessageBox.Close,
#                                        QMessageBox.Close
#                                       )
#            row = modelItems.findMdlpIndependedNomemclature(nomenclatureId)
#            if row is not None:
#                qnt = forceInt(modelItems.value(row, 'qnt'))
#                modelItems.setValue(row, 'qnt', qnt+1)
#            else:
#                row = len(modelItems.items())
#                item = modelItems.getEmptyRecord()
#                item.setValue('nomenclature_id', nomenclatureId)
#                item.setValue('qnt', 1)
#                modelItems.addRecord(item)
#            self.tblItems.setCurrentIndex(self.modelItems.index(row, self.modelItems.nomenclatureColumnIndex))
#            self.lblSummaryInfo.setText(modelItems.getSummaryInfo())



    @pyqtSignature('int')
    def on_cmbReceiver_currentIndexChanged(self, val):
        receiverId = self.cmbReceiver.value()
        self.cmbReceiverPerson.setOrgStructureId(receiverId)
        self.receiverMdlpId = getIdentification('OrgStructure', receiverId, 'urn:mdlp:anyId', raiseIfNonFound=False)
        self.updateMdlpMode()

#        if hasattr(self, 'modelItems'):
#            self.modelItems.setReceiverId(orgStructureId)
#        self.setBatchReadOnly()


    @pyqtSignature('int')
    def on_cmbSupplier_currentIndexChanged(self, val):
        supplierId = self.cmbSupplier.value()
        self.cmbSupplierPerson.setOrgStructureId(supplierId)
        self.supplierMdlpId = getIdentification('OrgStructure', supplierId, 'urn:mdlp:anyId', raiseIfNonFound=False)
        self.updateMdlpMode()
#        self.setBatchReadOnly()
#        if hasattr(self, 'modelItems'):
#            self.modelItems.setSupplierId(self.cmbSupplier.value())
#        supplierId = self.cmbSupplier.value()


#    @pyqtSignature('QModelIndex')
#    def on_tblItems_clicked(self, index):
#        self.emit(SIGNAL('clicked(QModelIndex)'), index)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_modelItems_dataChanged(self,  topLeftIndex, bottomRightIndex):
        self.lblSummaryInfo.setText(self.modelItems.getSummaryInfo())


    @pyqtSignature('')
    def on_btnProductionEditDialog_clicked(self):
        from Stock.ProductionEditDialog import CProductionEditDialog
        productionId = None
        dialog = CProductionEditDialog(self)
        try:
            dialog.cmbSupplier.setValue(QtGui.qApp.currentOrgStructureId())
            currentDateTime = QDateTime.currentDateTime()
            dialog.edtDate.setDate(currentDateTime.date())
            dialog.edtTime.setTime(currentDateTime.time())
            if dialog.exec_():
                productionId = dialog.itemId()
                if productionId:
                    QtGui.qApp.delAllCounterValueIdReservation()
                else:
                    QtGui.qApp.resetAllCounterValueIdReservation()
        finally:
            dialog.deleteLater()
        if productionId:
            self.modelItems.fillProduction(productionId, isOut=True)
            self.lblSummaryInfo.setText(self.modelItems.getSummaryInfo())
            self.setIsDirty(True)


    @pyqtSignature('')
    def on_actReceiveDocument10531_triggered(self):
        self.save()
        date = self.edtDate.date() or QDate.currentDate()
        try:
            mdlpDocumentIds, itemsFromDocument = selectWithdrawalsByRegisrar(self,
                                                                             self.getConnection(),
                                                                             date,
                                                                             self.supplierMdlpId)
            if itemsFromDocument:
                items = []
                for itemFromDocument in itemsFromDocument:
                    item = self.modelItems.getEmptyRecord()
                    item.setValue('sgtin',           itemFromDocument.sgtin)
                    item.setValue('nomenclature_id', findByIdentification('rbNomenclature', 'urn:gtin', itemFromDocument.sgtin[:14], raiseIfNonFound=False))
                    item.setValue('batch',           itemFromDocument.batch)
                    item.setValue('shelfTime',       itemFromDocument.expirationDate)
                    item.setValue('qnt',             1)
                    items.append(item)
                self.mdlpDocumentIds = mdlpDocumentIds
                self.modelItems.setItems(items)
                self.lblSummaryInfo.setText(self.modelItems.getSummaryInfo())
                # после этого self.mdlpStage нужно бы перечитать?
        except Exception as e:
            messageBox = QtGui.QMessageBox(QtGui.QMessageBox.Warning, u'Внимание!',
                              e.message,
                              QtGui.QMessageBox.Ok)
            messageBox.exec_()

    @pyqtSignature('')
    def on_actSendDocument531_triggered(self):
        self.save()
        docNum = unicode(self.edtNumber.text())
        docDate = self.edtDate.date()
        sgtins = self.modelItems.getSgtins()
        with CLogger(self, u'Обмен с МДЛП') as logger:
            QtGui.qApp.call(self,
                            iiwdProcess,
                            (logger,
                             self._id,
                             self.getConnection(),
                             self.supplierMdlpId,
                             docNum,
                             docDate,
                             sgtins
                             )
                            )
        # после этого self.mdlpStage нужно бы перечитать?

    @pyqtSignature('')
    def on_actSendDocument431_triggered(self):
        self.save()
        docNum = unicode(self.edtNumber.text())
        docDate = self.edtDate.date()
        sgtins = self.modelItems.getSgtins()
        if self.mdlpMode == self.mmMove:
            with CLogger(self, u'Обмен с МДЛП') as logger:
                QtGui.qApp.call(self,
                                iimProcess,
                                (logger,
                                 self._id,
                                 self.getConnection(),
                                 self.supplierMdlpId,
                                 self.receiverMdlpId,
                                 docNum,
                                 docDate,
                                 sgtins
                                 )
                                )

    # после этого self.mdlpStage нужно бы перечитать?

    @pyqtSignature('')
    def on_btnPrepareDispRequestToRegistrar_clicked(self):
        number = unicode(self.edtNumber.text())
        if not self.edtDate.date():
            now = QDateTime.currentDateTime()
            self.edtDate.setDate(now.date())
            self.edtTime.setTime(now.time())
        date = QDateTime(self.edtDate.date(), self.edtTime.time())
        dlg = CDisposalOrderEditDialog(self)
        dlg.setAttrs(number, date)
        self._blockSgtinReceiving = True
        try:
            toAddSgtins = dlg.exec_()
        finally:
            self._blockSgtinReceiving = False
        if toAddSgtins:
            sgtins = dlg.getSgtins()
            for sgtin in sgtins:
                self.onSgtinReceived(sgtin)

    @pyqtSignature('bool')
    def on_chkOrgStructureQuarantineZone_toggled(self, checked):
        self.cmbReceiver.setFilter(u'isQuarantineStorage=%d' % int(checked))
        if checked:
            orgIdList = self.cmbReceiver.getItemIdList()
            if len(orgIdList) == 1 or len(orgIdList) > 2:
                self.cmbReceiver.setCurrentIndex(0)
            elif len(orgIdList) == 2:
                self.cmbReceiver.setValue(orgIdList[0])
        else:
            self.cmbReceiver.setCurrentIndex(0)
        self.cmbReceiverPerson.setOrgStructureId(self.cmbReceiver.value())


class CItemsModel(CNomenclatureItemsBaseModel, CSummaryInfoModelMixin):
    sgtinColumnIndex          = 0
    nomenclatureColumnIndex   = 1
    batchColumnIndex          = 2
    shelfTimeColumnIndex      = 3
    financeColumnIndex        = 4
    medicalAidKindColumnIndex = 5
    qntColumnIndex            = 6
    unitColumnIndex           = 7
    priceColumnIndex          = 8
    sumColumnIndex            = 9
    existsColumnIndex         = 10

    class CSumCol(CFloatInDocTableCol):
        def _toString(self, value):
            if value.isNull():
                return None
            return format(forceDouble(value), '.2f')

    class CLocNomenclatureCol(CNomenclatureInDocTableCol):
        def __init__(self, title, fieldName, width, supplierId, **params):
            CNomenclatureInDocTableCol.__init__(self, title, fieldName, width, **params)
            self.supplierId = supplierId
            self.setStockOrgStructureId(self.supplierId)

        def createEditor(self, parent):
            editor = CNomenclatureInDocTableCol.createEditor(self, parent)
            editor.setOnlyExists(True)
            return editor

    def __init__(self, parent, showExists=False):
        CNomenclatureItemsBaseModel.__init__(self, parent)
        #CNomenclatureItemsBaseModel.__init__(self, 'StockMotion_Item', 'id', 'master_id', parent)
        self.supplierId = None
        self.isBatchReadOnly = True
        self.isStockRequsition = False
        self._nomenclatureColumn = self.CLocNomenclatureCol(u'ЛСиИМН', 'nomenclature_id', 50, self.supplierId, showFields = CRBComboBox.showName)
        self._unitColumn = CRBInDocTableCol(u'Ед.Учета', 'unit_id', 12, 'rbUnit', addNone=False)
        self.addCol(CInDocTableCol(u'Код вторичной упаковки', 'sgtin', 50, readOnly=not QtGui.qApp.isMdlpEnabled()))
        self.addCol(self._nomenclatureColumn)
        self.addCol(CInDocTableCol( u'Серия', 'batch', 16).setReadOnly(self.isBatchReadOnly))
        self.addCol(CDateInDocTableCol( u'Годен до', 'shelfTime', 12, canBeEmpty=True).setReadOnly(self.isBatchReadOnly))
        self.addCol(CRBInDocTableCol(    u'Тип финансирования', 'finance_id', 15, 'rbFinance').setReadOnly(self.isBatchReadOnly))
        self.addCol(CRBInDocTableCol(    u'Вид медицинской помощи', 'medicalAidKind_id', 15, 'rbMedicalAidKind').setReadOnly(self.isBatchReadOnly))
        self.addCol(getStockMotionItemQuantityColumn(u'Кол-во', 'qnt', 12))
        self.addCol(self._unitColumn)
        self.addCol(CFloatInDocTableCol(u'Цена', 'price', 12, precision=2))
        sumCol = CItemsModel.CSumCol( u'Сумма', 'sum', 12)
        self.addCol(sumCol)
#        self.addCol(CItemsModel.CPriceCol(u'Цена', 'id', 12, precision=2))
        self.existsCol = CItemsModel.CExistsCol(self)
        self.existsCol.setIsStockRequsition(self.isStockRequsition)
        self.addExtCol(self.existsCol.setReadOnly(), QVariant.Double)
        self.priceCache = parent
#        self.qntColumnIndex = self.getColIndex('qnt')
        self.requisitionItems = None
        self.updateBatchShelfTimeFinance = True
        self.setStockDocumentTypeExistsCol()


    def setIsStockRequsition(self, value):
        self.isStockRequsition = value
        self.existsCol.setIsStockRequsition(self.isStockRequsition)


    def cellReadOnly(self, index):
        column = index.column()
        if self.isBatchReadOnly and column in (self.batchColumnIndex, self.shelfTimeColumnIndex, self.financeColumnIndex, self.medicalAidKindColumnIndex, self.sumColumnIndex):
            return True
        if column == self.sumColumnIndex:
            return True
        return False


    def getNomenclatureNameById(self, nomenclatureId):
        return forceString(self._nomenclatureColumn.toString(nomenclatureId, None))


#    def getEmptyRecord(self):
#        record = CNomenclatureItemsBaseModel.getEmptyRecord(self)
#        return record


    def setPriceLineEditable(self, item):
        isPriceLineEditable = False
        if self._receiverId and self._receiverId == QtGui.qApp.currentOrgStructureId():
            isPriceLineEditable = True
        elif self._supplierId and self._supplierId != QtGui.qApp.currentOrgStructureId():
            isPriceLineEditable = True
        return isPriceLineEditable


    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid():
            return False
        col = index.column()
        row = index.row()
        if not self.isBatchReadOnly and self.requisitionItems or self.updateBatchShelfTimeFinance:
            if col == self.shelfTimeColumnIndex:
                item = self._items[row]
                batch, shelfTime, financeId, medicalAidKind, price = getBatchShelfTimeFinance(forceRef(item.value('nomenclature_id')),
                                                                        shelfTime = forceDate(value))
                result = CNomenclatureItemsBaseModel.setData(self, index, value, role)
                if result:
                    if financeId:
                        item.setValue('finance_id', toVariant(financeId))
                    else:
                        item.setNull('finance_id')
                    item.setValue('batch', toVariant(batch))
                    unitId = forceRef(item.value('unit_id'))
                    nomenclatureId = forceRef(item.value('nomenclature_id'))
                    if price and unitId and nomenclatureId:
                        ratio = self.getRatio(nomenclatureId, unitId, None)
                        if ratio is not None:
                            price = price*ratio
                    item.setValue('price', toVariant(price))
                    if medicalAidKind:
                        item.setValue('medicalAidKind_id', toVariant(medicalAidKind))
                    else:
                        item.setNull('medicalAidKind_id')
            elif col == self.financeColumnIndex:
                item = self._items[row]
                batch, shelfTime, financeId, medicalAidKind, price = getBatchShelfTimeFinance(forceRef(item.value('nomenclature_id')),
                                                                        financeId= forceInt(value))
                result = CNomenclatureItemsBaseModel.setData(self, index, value, role)
                if result:
                    item.setValue('shelfTime', toVariant(shelfTime))
                    item.setValue('batch', toVariant(batch))
                    unitId = forceRef(item.value('unit_id'))
                    nomenclatureId = forceRef(item.value('nomenclature_id'))
                    if price and unitId and nomenclatureId:
                        ratio = self.getRatio(nomenclatureId, unitId, None)
                        if ratio is not None:
                            price = price*ratio
                    item.setValue('price', toVariant(price))
                    if medicalAidKind:
                        item.setValue('medicalAidKind_id', toVariant(medicalAidKind))
                    else:
                        item.setNull('medicalAidKind_id')
            elif col == self.batchColumnIndex:
                item = self._items[row]
                batch, shelfTime, financeId, medicalAidKind, price = getBatchShelfTimeFinance(forceRef(item.value('nomenclature_id')),
                                                                        batch = forceString(value))
                result = CNomenclatureItemsBaseModel.setData(self, index, value, role)
                if financeId:
                    item.setValue('finance_id', toVariant(financeId))
                else:
                    item.setNull('finance_id')
                item.setValue('shelfTime', toVariant(shelfTime))
                unitId = forceRef(item.value('unit_id'))
                nomenclatureId = forceRef(item.value('nomenclature_id'))
                if price and unitId and nomenclatureId:
                    ratio = self.getRatio(nomenclatureId, unitId, None)
                    if ratio is not None:
                        price = price*ratio
                item.setValue('price', toVariant(price))
                if medicalAidKind:
                    item.setValue('medicalAidKind_id', toVariant(medicalAidKind))
                else:
                    item.setNull('medicalAidKind_id')
            elif col == self.medicalAidKindColumnIndex:
                item = self._items[row]
                batch, shelfTime, financeId, medicalAidKind, price = getBatchShelfTimeFinance(forceRef(item.value('nomenclature_id')),
                                                                        financeId = forceRef(item.value('finance_id')),
                                                                        medicalAidKind = forceRef(value))
                result = CNomenclatureItemsBaseModel.setData(self, index, value, role)
                if financeId:
                    item.setValue('finance_id', toVariant(financeId))
                else:
                    item.setNull('finance_id')
                item.setValue('shelfTime', toVariant(shelfTime))
                item.setValue('batch', toVariant(batch))
                unitId = forceRef(item.value('unit_id'))
                nomenclatureId = forceRef(item.value('nomenclature_id'))
                if price and unitId and nomenclatureId:
                    ratio = self.getRatio(nomenclatureId, unitId, None)
                    if ratio is not None:
                        price = price*ratio
                item.setValue('price', toVariant(price))
                if medicalAidKind:
                    item.setValue('medicalAidKind_id', toVariant(medicalAidKind))
                else:
                    item.setNull('medicalAidKind_id')
        if col in (self.qntColumnIndex, self.priceColumnIndex):
            if col == self.qntColumnIndex:
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
                if self.setPriceLineEditable(item):
                    existsColumn = existsColumn + forceDouble(value)
                if not self.isPriceLineEditable and forceDouble(item.value('price')) and (not existsColumn or existsColumn < 0):
                   return False
                if not self.isPriceLineEditable and forceDouble(item.value('price')) and existsColumn < forceDouble(value):
                    value = toVariant(existsColumn)
            result = CNomenclatureItemsBaseModel.setData(self, index, value, role)
            if result:
                self.setIsUpdateValue(True)
                item = self._items[row]
                if col == self.qntColumnIndex:
                    item.setValue('prevQnt', prevQnt)
                item.setValue('sum', toVariant(forceDouble(item.value('qnt')) * forceDouble(item.value('price'))))
                self.emitRowChanged(row)
            return result
        elif col == self.nomenclatureColumnIndex:
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
                    if self.updateBatchShelfTimeFinance:
                        batch, shelfTime, financeId, medicalAidKind, price = getBatchShelfTimeFinance(forceRef(value))
                        result = CNomenclatureItemsBaseModel.setData(self, index, value, role)
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
        elif col == self.unitColumnIndex:
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
                                                                                      isStockRequsition = True)
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

    # WFT?
    def getDataAsFNDict(self):
        result = {}
        for item in self.items():
            financeId = forceRef(item.value('finance_id'))
            nomenclatureId = forceRef(item.value('nomenclature_id'))
            if nomenclatureId:
                ndict = result.setdefault(financeId, {})
                ndict[nomenclatureId]=ndict.get(nomenclatureId, 0) + forceDouble(item.value('qnt'))
        return result


    def findRowWithSgtin(self, sgtin):
        for row, item in enumerate(self.items()):
            if sgtin == forceString(item.value('sgtin')):
                return row
        return None


    def findRowWithNomenclatureAndWithoutSgtin(self, nomenclatureId):
        for row, item in enumerate(self.items()):
            if (     forceRef(item.value('nomenclature_id')) == nomenclatureId
                 and forceString(item.value('sgtin')) == ''
               ):
                return row
        return None


    def findInsertRowWithNomenclature(self, nomenclatureId):
        items = self.items()
        for row in reversed(xrange(len(items))):
            item = items[row]
            if ( forceRef(item.value('nomenclature_id')) == nomenclatureId ):
                return row+1
        return len(items)


    def addSgtinObject(self, sgtinObject):
        gtin = sgtinObject.sgtin[:14]
        nomenclatureId = findByIdentification('rbNomenclature', 'urn:gtin', gtin, raiseIfNonFound=False)
        row = self.findRowWithNomenclatureAndWithoutSgtin(nomenclatureId)
        if row is not None:
            qnt = forceDouble(self.value(row, 'qnt'))
            if abs(qnt-1)>0.001:
                self.setValue(row, 'qnt', qnt-1)
                row = None
                item = self.getEmptyRecord()
            else:
                item = self.items()[row]
        else:
            item = self.getEmptyRecord()

        item.setValue('sgtin',           sgtinObject.sgtin)
        item.setValue('nomenclature_id', nomenclatureId)
        item.setValue('batch',           sgtinObject.batch)
        item.setValue('shelfTime',       sgtinObject.expirationDate)
        item.setValue('qnt',             1)
        if row is None:
            row = self.findInsertRowWithNomenclature(nomenclatureId)
            self.insertRecord(row, item)
        else:
            self.emitRowChanged(row)
        return row


    def getSgtins(self):
        sgtins = set()
        for item in self.items():
            sgtin = forceString(item.value('sgtin'))
            sgtins.add(sgtin)
        return list(sgtins)


    def fillProduction(self, productionId, isOut):
        db = QtGui.qApp.db
        tableStockMotion = db.table('StockMotion')
        tableStockMotion_Item = db.table('StockMotion_Item')
        queryTable = tableStockMotion.innerJoin(tableStockMotion_Item, tableStockMotion_Item['master_id'].eq(tableStockMotion['id']))
        cond = [tableStockMotion['id'].eq(productionId),
                     tableStockMotion_Item['isOut'].eq(forceInt(isOut)),
                     tableStockMotion['deleted'].eq(0),
                     tableStockMotion_Item['deleted'].eq(0),
                    ]
        records = db.getRecordList(queryTable, u'*', cond, order = tableStockMotion_Item['idx'].name())
        for record in records:
            myItem = self.getEmptyRecord()
            myItem.setValue('nomenclature_id',    record.value('nomenclature_id'))
            myItem.setValue('unit_id',                  record.value('unit_id'))
            myItem.setValue('batch',                      record.value('batch'))
            myItem.setValue('shelfTime',               record.value('shelfTime'))
            myItem.setValue('finance_id',             record.value('finance_id'))
            myItem.setValue('medicalAidKind_id', record.value('medicalAidKind_id'))
            myItem.setValue('qnt',                          record.value('qnt'))
            myItem.setValue('price',                      record.value('price'))
            myItem.setValue('sum',                          record.value('sum'))
            self.items().append(myItem)
        self.reset()

