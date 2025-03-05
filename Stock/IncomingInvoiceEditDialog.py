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
import re

from PyQt4 import QtGui
from PyQt4.QtGui import QMessageBox
from PyQt4.QtCore import SIGNAL, Qt, pyqtSignature, QDate, QDateTime

from library.MSCAPI import MSCApi
from library.crbcombobox         import CRBComboBox
from library.Identification      import getIdentification, findByIdentification

from library.InDocTable          import (
                                          CBoolInDocTableCol,
                                          CDateInDocTableCol,
                                          CFloatInDocTableCol,
                                          CInDocTableCol,
                                          CRBInDocTableCol,
                                        )
from library.interchange import (
    getDateEditValue,
    setDateEditValue,
    getLineEditValue,
    setLineEditValue,
    getRBComboBoxValue,
    setRBComboBoxValue,
)
from library.PrintInfo           import CInfoContext
from library.PrintTemplates      import (
                                          applyTemplate,
                                          CPrintAction,
                                          CPrintButton,
                                          getPrintTemplates,
                                        )
from library.Utils import (
    forceBool,
    forceDouble,
    forceRef,
    forceString,
    toVariant,
    forceInt, anyToUnicode,
    #                                          forceDate,
    #                                          trim,
)
#from Orgs.Utils                  import getOrgStructureIdentification

from Reports.ReportBase          import CReportBase, createTable
from Reports.ReportView          import CReportViewDialog
from Stock.NomenclatureComboBox  import CNomenclatureInDocTableCol
from RefBooks.Nomenclature.List  import CRBNomenclatureEditor
from Orgs.Orgs import selectOrganisation
from Stock.StockMotionBaseDialog import (
                                          CStockMotionBaseDialog,
                                          CStockMotionItemsCopyPasteMixin,
                                          CNomenclatureItemsBaseModel,
                                        )
#from Stock.StockBatchEditor      import CStockBatchEditor
from Stock.Utils                 import (
                                          getStockMotionItemQuantityColumn,
#                                          CPriceItemDelegate,
                                          CSummaryInfoModelMixin,
                                        )

from Stock.Mdlp.Logger                 import CLogger
from Stock.Mdlp.Stage                  import CMdlpStage
from Stock.Mdlp.connection             import CMdlpConnection
from Stock.Mdlp.selectIncomingInvoice  import selectIncomingInvoiceFromMdlp
from Stock.Mdlp.iidoProcess            import iidoProcess
from Stock.Mdlp.iiroProcess            import iiroProcess
from Stock.Mdlp.iinmProcess            import iinmProcess

from Ui_IncomingInvoice import Ui_IncomingInvoiceDialog


class CIncomingInvoiceEditDialog(Ui_IncomingInvoiceDialog,
                                 CStockMotionBaseDialog,
                                 CStockMotionItemsCopyPasteMixin,
                                ):
    stockDocumentType = 10 # Накладная от поставщика

    def __init__(self,  parent):
        CStockMotionBaseDialog.__init__(self, parent)
        CStockMotionItemsCopyPasteMixin.__init__(self, parent)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)

        self.addObject('btnPrint', CPrintButton(self, u'Печать'))
        self.btnPrint.setShortcut('F6')
        self.addObject('btnFill', QtGui.QPushButton(u'Заполнить', self))
        self.btnFill.setShortcut('F9')
        self.addObject('actReceiveDocument601', QtGui.QAction(u'Принять документ по схеме 601', self))
        self.addObject('actSendDocument701', QtGui.QAction(u'Отправить документ по схеме 701', self))
        self.addObject('actSendDocument416', QtGui.QAction(u'Отправить документ по схеме 416', self))
        self.addObject('actSendDocument702', QtGui.QAction(u'Отправить документ по схеме 702', self))
        self.addObject('btnMDLPExchange', QtGui.QPushButton(u'Выполнить обмен с МДЛП', self))
        self.addObject('mnuMDLPExchange', QtGui.QMenu(self))
        self.mnuMDLPExchange.addAction(self.actReceiveDocument601)
        self.mnuMDLPExchange.addAction(self.actSendDocument701)
        self.mnuMDLPExchange.addAction(self.actSendDocument416)
        self.mnuMDLPExchange.addAction(self.actSendDocument702)
        self.btnMDLPExchange.setMenu(self.mnuMDLPExchange)
        self.btnMDLPExchange.setEnabled(False)
        #self.addObject('btnSelectDocumentFromMdlp', QtGui.QPushButton(u'Запросить в МДЛП', self))
        self.addObject('actOpenStockBatchEditor', QtGui.QAction(u'Подобрать параметры', self))
        self.addObject('actOpenNomenclatureEditor', QtGui.QAction(u'Редактировать', self))

        self.addObject('actConfirmAll',   QtGui.QAction(u'Подтвердить все', self))
        self.addObject('actUnconfirmAll', QtGui.QAction(u'Снять подтверждение со всех', self))
        self.addObject('actPropagatePriceEtc',QtGui.QAction(u'Распространить цену и т.п.', self))

        self.addModels('Items', CItemsModel(self))
        self.setupUi(self)
        #self.btnSelectDocumentFromMdlp.setEnabled(False)
        self.actConfirmAll.setEnabled(QtGui.qApp.userHasRight(u'canConfirmStockIncomingInvoice'))
        self.actUnconfirmAll.setEnabled(QtGui.qApp.userHasRight(u'canConfirmStockIncomingInvoice'))
        self.actPropagatePriceEtc.setEnabled(False)

        self.cmbReceiverPerson.setSpecialityIndependents() # Что это?
        self.cmbSupplierOrg.setFilter('isSupplier = 1')
        self.cmbSupplierOrg.setCurrentIndex(0)
        self.cmbFinance.setTable('rbFinance')

        self.tblItems.setModel(self.modelItems)
        self.prepareItemsPopupMenu(self.tblItems)
        self.tblItems.popupMenu().addSeparator()
        self.tblItems.popupMenu().addAction(self.actOpenNomenclatureEditor)
        self.tblItems.popupMenu().addAction(self.actOpenStockBatchEditor)
        self.tblItems.popupMenu().addAction(self.actConfirmAll)
        self.tblItems.popupMenu().addAction(self.actUnconfirmAll)
        self.tblItems.popupMenu().addAction(self.actPropagatePriceEtc)

        self.tblItems.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.tblItems.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)

        self.buttonBox.addButton(self.btnPrint, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnFill, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnMDLPExchange, QtGui.QDialogButtonBox.ActionRole)
        self.btnFill.setEnabled(False)

        templates = getPrintTemplates(self.getStockContext())
        if not templates:
            self.btnPrint.setId(-1)
        else:
            for template in templates:
                action = CPrintAction(template.name, template.id, self.btnPrint, self.btnPrint)
                self.btnPrint.addAction(action)
            self.btnPrint.menu().addSeparator()
            self.btnPrint.addAction(CPrintAction(u'Напечатать список', -1, self.btnPrint, self.btnPrint))

#        self.tblItems.setItemDelegateForColumn(CItemsModel.priceColumnIndex, CPriceItemDelegate(self.tblItems))
        self._initView()
        self.setupDirtyCather()

        if QtGui.qApp.isMdlpEnabled():
            self.connect(QtGui.qApp, SIGNAL('ssccReceived(QString)'),  self.onSsccReceived)
            self.connect(QtGui.qApp, SIGNAL('sgtinReceived(QString)'), self.onSgtinReceived)
            self.btnMDLPExchange.setEnabled(True)
            self.cmbPlaceOfBusiness.setEnabled(True)
        else:
            self.btnMDLPExchange.setEnabled(False)
            self.cmbPlaceOfBusiness.setEnabled(False)
        self.connect(QtGui.qApp, SIGNAL('gtinReceived(QString)'),  self.onGtinReceived)

        self.mdlpBaseDocumentUuid = None
        self.mdlpStage  = None
        self.connection = None
        self.exchangeInitiated = False
        self.tblItems.enableColsMove()
        self.cmbPlaceOfBusiness.popupShow.connect(self.onUpdatePlaceOfBusiness)
        self.cmbContractType.setItems()

    def save(self):
        id = CStockMotionBaseDialog.save(self)
        return id


    def getMdlpStage(self):
        storedMdlpStage = CMdlpStage.unnecessary  # нужно не storedMdlpStage а что-то другое...
        if self.modelItems.hasMdlpRelatedCiszs():
            if self.useDirectConfirmationOrder():
                confirmedSsccs, confirmedSgtins = self.modelItems.getConfirmedCiszs()
                refusedSsccs, refusedSgtins = self.modelItems.getRefusedCiszs()
                if confirmedSsccs or confirmedSgtins or refusedSsccs or refusedSgtins:
                    storedMdlpStage = CMdlpStage.ready
            elif self.useReverseConfirmationOrder() or self.useNotificationMode():
                confirmedSsccsWithSumAndVat, confirmedSgtinsWithSumAndVat = self.modelItems.getConfirmedCiszsWithSumAndVat()
                if confirmedSsccsWithSumAndVat or confirmedSgtinsWithSumAndVat:
                    storedMdlpStage = CMdlpStage.ready
        return storedMdlpStage

    def updateRecordMldpStage(self):
        mdlpStage = self.getMdlpStage()
        self._record.setValue('mdlpStage', mdlpStage)


    def getStockContext(self):
        return ['InvoiceCreate']

    def actPrintMotions(self, templateId):
        from Stock.StockMotionInfo import CStockMotionInfoList
        db = QtGui.qApp.db
        if templateId == -1:
            self.getNomenclaturePrint()
        else:
            idList = self.tblItems.model().itemIdList()
            codeTemplate = db.getRecord('rbPrintTemplate', 'code', templateId)
            if forceString(codeTemplate.value('code')) == u'3':
                name = db.getRecord('rbPrintTemplate', 'name', templateId)
                name = forceString(name.value('name'))
                idList = self.getGTINListPrint(idList)
                dataContext = [name, idList]
            else:
                context = CInfoContext()
                dataContext = CStockMotionInfoList(context, idList)
            data = {'invoicesList': dataContext}
            QtGui.qApp.call(self, applyTemplate, (self, templateId, data))

    def getGTINListPrint(self, idList):
        db = QtGui.qApp.db
        tableStockMotionItem = db.table('StockMotion_Item')
        tableNomenclature = db.table('rbNomenclature')
        tableNomenclatureIdentification = db.table('rbNomenclature_Identification')
        tableAccountingSystem = db.table('rbAccountingSystem')
        query = tableStockMotionItem.leftJoin(tableNomenclature, tableNomenclature['id'].eq(tableStockMotionItem['nomenclature_id']))
        query = query.join(tableNomenclatureIdentification, tableNomenclature['id'].eq(tableNomenclatureIdentification['master_id']))
        query = query.join(tableAccountingSystem, tableAccountingSystem['id'].eq(tableNomenclatureIdentification['system_id']))
        cols = [
            tableNomenclatureIdentification['value'],
            tableNomenclature['name'],
            u'SUM(StockMotion_Item.qnt) as qnt',
            # tableStockMotionItem['qnt'],
        ]
        cond = [
            tableStockMotionItem['id'].inlist(idList),
            tableAccountingSystem['code'].eq('gtin'),
        ]
        group = 'rbNomenclature_Identification.value'
        return db.getRecordListGroupBy(query, cols, cond, group)

    def dumpParams(self, cursor):
        db = QtGui.qApp.db
        description = []
        number = unicode(self.edtNumber.text())
        if number:
            description.append(u'Номер %s'%number)
        docDate = self.edtDocDate.date()
        if docDate:
           description.append(u'Дата документа %s'%forceString(docDate))

        reason = unicode(self.cmbReason.currentText())
        if reason:
           description.append(u'Основание %s'% reason)


        date = self.edtDate.date()
        if date:
            dateTime = QDateTime(date, self.edtTime.time())
            description.append(u'Дата приходования %s'%forceString(dateTime))

        invoice = unicode(self.edtInvoiceNumber.text())
        if invoice:
            description.append(u'Счет-фактура %s'%invoice)

        invoiceDate = self.edtInvoiceDate.date()
        if invoiceDate:
            description.append(u'Дата счета-фактуры %s'%forceString(invoiceDate))

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

    @pyqtSignature('')
    def on_btnSelectOrganisation_clicked(self):
        orgValueId = self.cmbSupplierOrg.value() or None
        orgId = selectOrganisation(self, None, True, params={'isActive': 2, 'isSupplier': 2, 'itemId': orgValueId}, forSelect=True)
        self.cmbSupplierOrg.model().update()
        self.cmbSupplierOrg.setValue(orgId or orgValueId)

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
            if not iColNumber:
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
        self.cmbReceiver.setValue(QtGui.qApp.currentOrgStructureId())


    def setMdlpBaseDocumentUuid(self, documentUuid):
        self.mdlpBaseDocumentUuid = documentUuid


    def setRecord(self, record):
        CStockMotionBaseDialog.setRecord(self, record)
        setRBComboBoxValue(self.cmbSupplierOrg,       record, 'supplierOrg_id')
        setDateEditValue(  self.edtDocDate,           record, 'docDate')
        setRBComboBoxValue(self.cmbReason,            record, 'reason_id')
        setLineEditValue(  self.edtSupplierOrgPerson, record, 'supplierOrgPerson')
        setRBComboBoxValue(self.cmbReceiver,          record, 'receiver_id')
        setRBComboBoxValue(self.cmbReceiverPerson,    record, 'receiverPerson_id')
        setLineEditValue(  self.edtInvoiceNumber,     record, 'invoiceNumber')
        setDateEditValue(  self.edtInvoiceDate,       record, 'invoiceDate')
        self.cmbPlaceOfBusiness.addItem(u'не задано')
        if forceString(record.value('placeOfBusiness')):
            self.cmbPlaceOfBusiness.addItem(forceString(record.value('placeOfBusiness')))
            self.cmbPlaceOfBusiness.setCurrentIndex(1)
        else:
            self.cmbPlaceOfBusiness.setCurrentIndex(0)
        self.setMdlpBaseDocumentUuid(forceString(record.value('mdplBaseDocumentUuid')))
        self.cmbContractType.setCurrentIndex(forceInt(record.value('contractType')))
        self.mdlpStage = forceInt(record.value('mdlpStage'))
#        self.mdplDone = forceBool(record.value('mdplDone'))
        self.modelItems.loadItems(self.itemId())

        self.lblSummaryInfo.setText(self.modelItems.getSummaryInfo())
        #self.btnFill.setEnabled(self.cmbReason.value() is not None)
        self.setIsDirty(False)
#        if self.mdlpStage != CMdlpStage.unnecessary:
#            self.setReadOnly()


    def getRecord(self):
        record = CStockMotionBaseDialog.getRecord(self)
        getRBComboBoxValue(self.cmbSupplierOrg,       record, 'supplierOrg_id')
        getDateEditValue(  self.edtDocDate,           record, 'docDate')
        getRBComboBoxValue(self.cmbReason,            record, 'reason_id')
        getLineEditValue(  self.edtSupplierOrgPerson, record, 'supplierOrgPerson')
        getRBComboBoxValue(self.cmbReceiver,          record, 'receiver_id')
        getRBComboBoxValue(self.cmbReceiverPerson,    record, 'receiverPerson_id')
        getLineEditValue(  self.edtInvoiceNumber,     record, 'invoiceNumber')
        getDateEditValue(  self.edtInvoiceDate,       record, 'invoiceDate')
        record.setValue('mdplBaseDocumentUuid', self.mdlpBaseDocumentUuid)
        record.setValue('contractType', toVariant(self.cmbContractType.currentIndex()))
        if self.mdlpStage is None or (not self.getExchangeInitiated() and self.mdlpStage < 1):
            storedMdlpStage = self.getMdlpStage()
            record.setValue('mdlpStage', storedMdlpStage)
        record.setValue('type', self.stockDocumentType)
        if self.cmbPlaceOfBusiness.currentIndex():
            record.setValue('placeOfBusiness', toVariant(self.cmbPlaceOfBusiness.currentText()))
        else:
            record.setNull('placeOfBusiness')
        return record


    def saveInternals(self, id):
        financeId = self.cmbFinance.value()
        for item in self.modelItems.items():
            item.setValue('finance_id', financeId)
        self.modelItems.saveItems(id)


    def checkDataEntered(self):
        result = self._checkStockMotionItemsData(self.tblItems)
        result = result and (self.cmbReason.value() or self.checkInputMessage(u'основание', False, self.cmbReason))
        result = result and (self.cmbSupplierOrg.value() or self.checkInputMessage(u'поставщика', False, self.cmbSupplierOrg))
        result = result and self.checkItemsDataEntered()
        return result


    def checkItemsDataEntered(self):
        return True


    def useDirectConfirmationOrder(self):
        return QtGui.qApp.isMdlpEnabled() and self.cmbConfirmationOrder.currentIndex() == 1 and not self.useNotificationMode()


    def useReverseConfirmationOrder(self):
        return QtGui.qApp.isMdlpEnabled() and self.cmbConfirmationOrder.currentIndex() == 2 and not self.useNotificationMode()


    def useNotificationMode(self):
        return QtGui.qApp.isMdlpEnabled() and QtGui.qApp.getMdlpPrefs()[-1] # Уведомительный режим


    def getConnection(self):
        if self.connection is None:
            self.connection = CMdlpConnection()
        return self.connection


    def onSsccReceived(self, sscc):
        if self.useDirectConfirmationOrder():
            rows = self.modelItems.confirmRowsWithSscc(sscc)
            if rows:
                self.tblItems.setCurrentIndex(self.modelItems.index(rows[0], self.modelItems.ssccColumnIndex))
            else:
                QMessageBox.information(self,
                                        u'Поставка не соответствует документу',
                                        u'В документе нет строк с кодом транспортной упаковки «%s»' % sscc,
                                        QMessageBox.Close,
                                        QMessageBox.Close
                                       )
        elif self.useReverseConfirmationOrder() or self.useNotificationMode():
            row = self.modelItems.findRowWithSscc(sscc)
            if row is not None:
                self.tblItems.setCurrentIndex(self.modelItems.index(row, self.modelItems.ssccColumnIndex))
            else:
                supplierOrgId = self.cmbSupplierOrg.value()
                supplierMdlpId = getIdentification('Organisation', supplierOrgId, 'urn:mdlp:anyId', raiseIfNonFound=True)

                connection = self.getConnection()
                fhs = connection.getSsccFullHierarchyByList([sscc])
                if not isinstance(fhs, list) or len(fhs) != 1:
                    QMessageBox.information(self,
                                            u'Ошибка',
                                            u'В МДЛП не удалось найти транспортную упаковку с кодом «%s»' % sscc,
                                            QMessageBox.Close,
                                            QMessageBox.Close
                                           )
                    return
                ownerId = fhs[0].up.ownerId
                if not self.useNotificationMode() and ownerId != supplierMdlpId:
                    QMessageBox.information(self,
                                            u'Ошибка',
                                            u'По данным МДЛП транспортная упаковка с кодом «%s» принадлежит организации «%s», а отправитель «%s»' % (sscc, ownerId, supplierMdlpId),
                                            QMessageBox.Close,
                                            QMessageBox.Close
                                           )
                    return
                rows = self.modelItems.addSgtins(sscc, fhs[0].sgtins)
                if rows:
                    self.tblItems.setCurrentIndex(self.modelItems.index(rows[0], self.modelItems.ssccColumnIndex))


    def onSgtinReceived(self, sgtin):
        if self.useDirectConfirmationOrder():
            rows = self.modelItems.confirmRowsWithSgtin(sgtin)
            if rows:
                self.tblItems.setCurrentIndex(self.modelItems.index(rows[0], self.modelItems.sgtinColumnIndex))
            else:
                QMessageBox.information(self,
                                        u'Поставка не соответствует документу',
                                        u'В документе нет строк с кодом вторичной упаковки «%s»' % sgtin,
                                        QMessageBox.Close,
                                        QMessageBox.Close
                                       )
        elif self.useReverseConfirmationOrder() or self.useNotificationMode():
            rows = self.modelItems.confirmRowsWithSgtin(sgtin)
            if rows:
                self.tblItems.setCurrentIndex(self.modelItems.index(rows[0], self.modelItems.sgtinColumnIndex))
                return
            supplierOrgId = self.cmbSupplierOrg.value()
            supplierMdlpId = getIdentification('Organisation', supplierOrgId, 'urn:mdlp:anyId', raiseIfNonFound=True)
            connection = self.getConnection()
            succ, fail = connection.getPublicSgtinsByList([unicode(sgtin)])
            if (     succ
                 and (    self.useNotificationMode() # не известно у кого
                       or succ[0].ownerId == supplierMdlpId # у поставщика

                     )
               ):
                row = self.modelItems.addSgtin('', succ[0])
                self.tblItems.setCurrentIndex(self.modelItems.index(row, self.modelItems.sgtinColumnIndex))
            else:
                QMessageBox.information(self,
                                        u'Ошибка',
                                        u'В МДЛП у поставщика «%s» не найден sgtin «%s»' % (supplierMdlpId, sgtin),
                                        QMessageBox.Close,
                                        QMessageBox.Close
                                       )


    def onGtinReceived(self, gtin):
        modelItems = self.modelItems
        if not modelItems.isMdlpRelatedGtinPresent(gtin):
            nomenclatureId = findByIdentification('rbNomenclature', 'urn:gtin', gtin, raiseIfNonFound=False)
            if nomenclatureId:
                row = modelItems.findMdlpIndependedNomemclature(nomenclatureId)
                if row is not None:
                    qnt = forceInt(modelItems.value(row, 'qnt'))
                    modelItems.setValue(row, 'qnt', qnt+1)
                else:
                    row = len(modelItems.items())
                    item = modelItems.getEmptyRecord()
                    item.setValue('nomenclature_id', nomenclatureId)
                    item.setValue('qnt', 1)
                    modelItems.addRecord(item)
                self.tblItems.setCurrentIndex(self.modelItems.index(row, self.modelItems.nomenclatureColumnIndex))
                self.lblSummaryInfo.setText(modelItems.getSummaryInfo())
            else:
                QMessageBox.information(self,
                                        u'ЛСиИМН не найдено',
                                        u'Не удаётся найти ЛСиИМН с кодом GTIN «%s»' % gtin,
                                        QMessageBox.Close,
                                        QMessageBox.Close
                                       )

    # slots

    @pyqtSignature('int')
    def on_cmbSupplierOrg_currentIndexChanged(self, val):
        supplierOrgId = self.cmbSupplierOrg.value()
        supplierOrgAssigned = bool(supplierOrgId)
        for widget in (
                self.lblSupplierOrgPerson, self.edtSupplierOrgPerson, self.lblReason,
                self.lblFinance, self.lblContractType, self.lblConfirmationOrder
        ):
            widget.setEnabled(supplierOrgAssigned)

        for widget in (self.lblPlaceOfBusiness, self.cmbPlaceOfBusiness):
            widget.setEnabled(QtGui.qApp.isMdlpEnabled() and supplierOrgAssigned)
        self.cmbReason.setSupplierOrgId(supplierOrgId)
        self.modelItems.setSupplierOrgId(supplierOrgId)
        if self.cmbPlaceOfBusiness.model().rowCount() > 1:
            self.cmbPlaceOfBusiness.clear()
            self.cmbPlaceOfBusiness.addItem(u'не задано')


    @pyqtSignature('QDate')
    def on_edtDate_dateChanged(self, date):
        self.cmbReason.setDate(date)


    @pyqtSignature('int')
    def on_cmbReason_currentIndexChanged(self, index):
        self.btnFill.setEnabled(False)
        purchaseContractId = self.cmbReason.value()
        if purchaseContractId:
            db = QtGui.qApp.db
            record = db.getRecord('StockPurchaseContract',
                                  ('finance_id', 'confirmationOrder', 'contractType'),
                                  purchaseContractId
                                  )
            self.cmbFinance.setValue(forceRef(record.value('finance_id')))
            self.cmbConfirmationOrder.setCurrentIndex(forceInt(record.value('confirmationOrder')))
            self.cmbContractType.setCurrentIndex(forceInt(record.value('contractType')))

            tablePurchaseContractItem = db.table('StockPurchaseContract_Item')
            conds = [
                tablePurchaseContractItem['master_id'].eq(purchaseContractId),
                tablePurchaseContractItem['deleted'].eq(0),
            ]
            isStockPurchaseContractItems = db.getRecordList(tablePurchaseContractItem, cols='id', where=conds)

            if isStockPurchaseContractItems and not self.isReadOnly():
                self.btnFill.setEnabled(True)

        else:
            self.cmbFinance.setCurrentIndex(0)
            self.cmbConfirmationOrder.setCurrentIndex(0)
            self.cmbContractType.setCurrentIndex(0)


    @pyqtSignature('int')
    def on_cmbConfirmationOrder_currentIndexChanged(self, index):
        directConfirmationOrder = self.useDirectConfirmationOrder()
        self.actConfirmAll.setEnabled(directConfirmationOrder and QtGui.qApp.userHasRight(u'canConfirmStockIncomingInvoice'))
        self.actUnconfirmAll.setEnabled(directConfirmationOrder and QtGui.qApp.userHasRight(u'canConfirmStockIncomingInvoice'))
        self.actPropagatePriceEtc.setEnabled(self.useReverseConfirmationOrder() or self.useNotificationMode())


    @pyqtSignature('int')
    def on_cmbReceiver_currentIndexChanged(self, index):
        receiverId = self.cmbReceiver.value()
        self.cmbReceiverPerson.setOrgStructureId(receiverId)
        self.modelItems.setReceiverId(receiverId)

    @pyqtSignature('int')
    def on_cmbContractType_currentIndexChanged(self, index):
        pass


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_modelItems_dataChanged(self, topLeftIndex, bottomRightIndex):
        self.lblSummaryInfo.setText(self.modelItems.getSummaryInfo())

    @pyqtSignature('')
    def on_actOpenNomenclatureEditor_triggered(self):
        items = self.tblItems.getSelectedItems()
        if len(items) == 0:
            return
        nomenclatureId = forceInt(items[0].value('nomenclature_id'))
        record = QtGui.qApp.db.getRecord('rbNomenclature', '*', nomenclatureId)
        dialog = CRBNomenclatureEditor(self)
        dialog.setRecord(record)
        dialog.exec_()


    @pyqtSignature('')
    def on_actOpenStockBatchEditor_triggered(self):
        self.on_tblItems_doubleClicked(self.tblItems.currentIndex())


    @pyqtSignature('')
    def on_actConfirmAll_triggered(self):
        if self.useDirectConfirmationOrder():
            self.modelItems.setConfirmAll(True)


    @pyqtSignature('')
    def on_actUnconfirmAll_triggered(self):
        if self.useDirectConfirmationOrder():
            self.modelItems.setConfirmAll(False)


    @pyqtSignature('')
    def on_actPropagatePriceEtc_triggered(self):
        if self.useReverseConfirmationOrder() or self.useNotificationMode():
            self.modelItems.propagatePriceEtc()


    @pyqtSignature('int')
    def on_btnPrint_printByTemplate(self, templateId):
        self.actPrintMotions(templateId)


    @pyqtSignature('')
    def on_btnFill_clicked(self):
        purchaseContractId = self.cmbReason.value()
        if purchaseContractId:
            self.modelItems.fill(purchaseContractId)

    def on_mnuMDLPExchange_aboutToShow(self):
        self.actReceiveDocument601.setEnabled(False)
        self.actSendDocument701.setEnabled(False)
        self.actSendDocument701.setText(u'Отправить документ по схеме 701')
        self.actSendDocument416.setEnabled(False)
        self.actSendDocument702.setEnabled(False)

        if QtGui.qApp.isMdlpEnabled() and self.cmbConfirmationOrder.currentIndex() != 0 and self.cmbSupplierOrg.currentIndex() != 0 and self.cmbReason.currentIndex() != 0 and self.cmbReceiver.value():

            directConfirmationOrder = self.useDirectConfirmationOrder()
            reverseConfirmationOrder = self.useReverseConfirmationOrder()
            modelHasItems = len(self.modelItems.items())
            hasMdlpRelatedCiszs = self.modelItems.hasMdlpRelatedCiszs()

            if directConfirmationOrder:
                if modelHasItems and hasMdlpRelatedCiszs and bool(self.mdlpBaseDocumentUuid):
                    self.actSendDocument701.setEnabled(True)
                    if self.modelItems.hasNoConfirmedCiszsOnly():
                        self.actSendDocument701.setText(u'Отправить документ по схеме 252')
                    elif self.modelItems.hasConfirmedCiszsOnly():
                        self.actSendDocument701.setText(u'Отправить документ по схеме 701')
                    else:
                        self.actSendDocument701.setText(u'Отправить документ по схемам 701 и 252')
                elif not modelHasItems:
                    self.actReceiveDocument601.setEnabled(True)
            if reverseConfirmationOrder:
                if not self.useNotificationMode() and hasMdlpRelatedCiszs:
                    self.actSendDocument416.setEnabled(True)

            self.actSendDocument702.setEnabled(self.useNotificationMode() and hasMdlpRelatedCiszs)


    @pyqtSignature('')
    def on_actReceiveDocument601_triggered(self):
        self.setExchangeInitiated(True)
        self.save()
        date = self.edtDocDate.date() or QDate.currentDate()
        supplierOrgId = self.cmbSupplierOrg.value()
        supplierMdlpId = getIdentification('Organisation', supplierOrgId, 'urn:mdlp:anyId', raiseIfNonFound=True)
        receiverId = self.cmbReceiver.value()
        receiverMdlpId = getIdentification('OrgStructure', receiverId, 'urn:mdlp:anyId', raiseIfNonFound=True)
        with CLogger(self, u'Обмен с МДЛП') as logger:
            QtGui.qApp.getCsp()
            QtGui.qApp.getUserCertSha1()
        mdlpDocumentId, itemsFromDocument = selectIncomingInvoiceFromMdlp(self,
                                                                          self.getConnection(),
                                                                          date,
                                                                          supplierMdlpId,
                                                                          receiverMdlpId)
        if mdlpDocumentId:
            items = []
            for itemFromDocument in itemsFromDocument:
                item = self.modelItems.getEmptyRecord()
                nomenclatureId = findByIdentification('rbNomenclature', 'urn:gtin', itemFromDocument.sgtin[:14], raiseIfNonFound=False)
                if nomenclatureId:
                    defaultStockUnitId = forceRef(QtGui.qApp.db.translate('rbNomenclature', 'id', nomenclatureId, 'defaultStockUnit_id'))
                    item.setValue('unit_id', toVariant(defaultStockUnitId))
                item.setValue('isMdlpRelated',   True)
                item.setValue('isConfirmed',     False)
                item.setValue('sscc',            itemFromDocument.sscc)
                item.setValue('sgtin',           itemFromDocument.sgtin)
                item.setValue('nomenclature_id', toVariant(nomenclatureId))
                item.setValue('batch',           itemFromDocument.batch)
                item.setValue('shelfTime',       itemFromDocument.expirationDate)
                item.setValue('qnt',             1)
                item.setValue('price',           itemFromDocument.sum)
                item.setValue('sum',             itemFromDocument.sum)
                item.setValue('vat',             itemFromDocument.vat)
                items.append(item)
            self.setMdlpBaseDocumentUuid(mdlpDocumentId)
            self.modelItems.setItems(items)
            self.lblSummaryInfo.setText(self.modelItems.getSummaryInfo())

    @pyqtSignature('')
    def on_actSendDocument701_triggered(self):
        self.setExchangeInitiated(True)
        self.save()
        if self._id and self.mdlpStage in (None, CMdlpStage.ready, CMdlpStage.inProgress):
            confirmedSsccs, confirmedSgtins = self.modelItems.getConfirmedCiszs()
            refusedSsccs, refusedSgtins = self.modelItems.getRefusedCiszs()
            with CLogger(self, u'Обмен с МДЛП') as logger:
                QtGui.qApp.call(self,
                                iidoProcess,
                                (logger,
                                 self._id,
                                 self.getConnection(),
                                 self.mdlpBaseDocumentUuid,
                                 confirmedSsccs,
                                 confirmedSgtins,
                                 refusedSsccs,
                                 refusedSgtins
                                 )
                                )
            # после этого self.mdlpStage нужно бы перечитать?

    @pyqtSignature('')
    def on_actSendDocument416_triggered(self):
        self.setExchangeInitiated(True)
        self.save()
        if self._id and self.mdlpStage in (None, CMdlpStage.ready, CMdlpStage.inProgress):
            supplierOrgId = self.cmbSupplierOrg.value()
            supplierMdlpId = getIdentification('Organisation', supplierOrgId, 'urn:mdlp:anyId', raiseIfNonFound=True)
            receiverId = self.cmbReceiver.value()
            receiverMdlpId = getIdentification('OrgStructure', receiverId, 'urn:mdlp:anyId', raiseIfNonFound=True)
            docNum = unicode(self.edtNumber.text())
            docDate = self.edtDocDate.date()
            confirmedSsccsWithSumAndVat, confirmedSgtinsWithSumAndVat = self.modelItems.getConfirmedCiszsWithSumAndVat()
            with CLogger(self, u'Обмен с МДЛП') as logger:
                QtGui.qApp.call(self,
                                iiroProcess,
                                (logger,
                                 self._id,
                                 self.getConnection(),
                                 supplierMdlpId,
                                 receiverMdlpId,
                                 docNum,
                                 docDate,
                                 confirmedSsccsWithSumAndVat,
                                 confirmedSgtinsWithSumAndVat,
                                 )
                                )
            # после этого self.mdlpStage нужно бы перечитать?

    @pyqtSignature('')
    def on_actSendDocument702_triggered(self):
        self.setExchangeInitiated(True)
        if not self.edtNumber.text():
            QtGui.QMessageBox.warning(self,
                                      u'Внимание!',
                                      u'Для выполнения обмена по 702 схеме необходимо указать номер документа',
                                      QtGui.QMessageBox.Ok,
                                      QtGui.QMessageBox.Ok)
            self.edtNumber.setFocus(Qt.OtherFocusReason)
            return

        self.save()
        if (self._id
                and self.useNotificationMode()
                and self.mdlpStage in (None, CMdlpStage.ready, CMdlpStage.inProgress)
        ):
            supplierOrgId = self.cmbSupplierOrg.value()
            supplierMdlpId = getIdentification('Organisation', supplierOrgId, 'urn:mdlp:anyId',
                                               raiseIfNonFound=True)
            supplierInn = forceString(QtGui.qApp.db.translate('Organisation', 'id', supplierOrgId, 'INN'))
            supplierKpp = forceString(QtGui.qApp.db.translate('Organisation', 'id', supplierOrgId, 'KPP'))
            receiverId = self.cmbReceiver.value()
            receiverMdlpId = getIdentification('OrgStructure', receiverId, 'urn:mdlp:anyId', raiseIfNonFound=True)
            docNum = unicode(self.edtNumber.text())
            docDate = self.edtDocDate.date()
            confirmedSsccsWithSumAndVat, confirmedSgtinsWithSumAndVat = self.modelItems.getConfirmedCiszsWithSumAndVat()
            with CLogger(self, u'Обмен с МДЛП') as logger:
                QtGui.qApp.call(self,
                                iinmProcess,
                                (logger,
                                 self._id,
                                 self.getConnection(),
                                 supplierMdlpId,
                                 supplierInn,
                                 supplierKpp,
                                 receiverMdlpId,
                                 docNum,
                                 docDate,
                                 confirmedSsccsWithSumAndVat,
                                 confirmedSgtinsWithSumAndVat,
                                 )
                                )

    def onUpdatePlaceOfBusiness(self):
        cert = None
        api = None
        msg = u''
        try:
            api = MSCApi(QtGui.qApp.getCsp())
        except Exception as e:
            msg = e.message
        if api and not msg:
            try:
                cert = QtGui.qApp.getUserCert(api)
            except Exception as e:
                msg = e.message
        if msg:
            QtGui.QMessageBox.warning(None, u'Ошибка получения сертификата', anyToUnicode(msg),
                                      QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ok)
            return
        if cert:
            connection = CMdlpConnection()
            searchRequsitesList = []
            supplierOrgId = self.cmbSupplierOrg.value()
            supplierMdlpId = None
            if supplierOrgId:
                try:
                    supplierMdlpId = getIdentification('Organisation', supplierOrgId, 'urn:mdlp:anyId', raiseIfNonFound=True)
                except:
                    supplierMdlpId = None
            inn = forceString(QtGui.qApp.db.translate('Organisation', 'id', supplierOrgId, 'inn')) or None
            ogrn = forceString(QtGui.qApp.db.translate('Organisation', 'id', supplierOrgId, 'ogrn')) or None
            if ogrn:
                if not re.match(r'\d{13}', ogrn):
                    QtGui.QMessageBox.warning(None,
                                              u'Внимание!',
                                              u'Необходимо указать корректное значение ОГРН поставщика в справочнике "Организации"',
                                              QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ok)
                    return
            result = None
            self.cmbPlaceOfBusiness.clear()
            self.cmbPlaceOfBusiness.addItem(u'не задано')
            response = None
            if supplierMdlpId:
                try:
                    response = connection.getPartners(sysId=supplierMdlpId)
                except:
                    searchRequsitesList.append(u'- <b>SysId</b> %s' % supplierMdlpId)
            if not response:
                if inn or ogrn:
                    try:
                        response = connection.getPartners(ogrn=ogrn, inn=inn)
                    except:
                        if inn:
                            searchRequsitesList.append(u'- <b>ИНН</b> %s' % inn)
                        if ogrn:
                            searchRequsitesList.append(u'- <b>ОГРН</b> %s' % ogrn)
            if response:
                from Orgs.Utils import synchronizePlaceOfBusiness
                result = response[0]
                for item in result.branches:
                    if item.status == 1:
                        self.cmbPlaceOfBusiness.addItem(u'%s | %s' % (item.id, item.address))
                synchronizePlaceOfBusiness(result, supplierOrgId, inn, ogrn)
            else:
                searchRequsitesString = u'<br>'.join(searchRequsitesList)
                QtGui.QMessageBox.warning(None,
                                          u'Внимание!',
                                          u'В сервисе МДЛП не найдено информации по указанным реквизитам:'
                                          u'<br><br>%s' % searchRequsitesString,
                                          QtGui.QMessageBox.Close, QtGui.QMessageBox.Close)


    def setExchangeInitiated(self, value=False):
        self.exchangeInitiated = value


    def getExchangeInitiated(self):
        return self.exchangeInitiated
# ############################################


class CItemsModel(CNomenclatureItemsBaseModel, CSummaryInfoModelMixin):
    isMdlpRelatedColumnIndex  = 0
    isConfirmedColumnIndex    = 1
    ssccColumnIndex           = 2
    sgtinColumnIndex          = 3
    nomenclatureColumnIndex   = 4
    batchColumnIndex          = 5
    shelfTimeColumnIndex      = 6
    medicalAidKindColumnIndex = 7
    qntColumnIndex            = 8
    unitColumnIndex           = 9
    priceColumnIndex          = 10
    sumColumnIndex            = 11
    vatColumnIndex            = 12
    noteColumnIndex           = 13

    class CSumCol(CFloatInDocTableCol):
        def _toString(self, value):
            if value.isNull():
                return None
            return format(forceDouble(value), '.2f')


    def __init__(self, parent, showExists=False):
        CNomenclatureItemsBaseModel.__init__(self, parent)
        #CNomenclatureItemsBaseModel.__init__(self, 'StockMotion_Item', 'id', 'master_id', parent)

        isMdlpEnabled = QtGui.qApp.isMdlpEnabled()

        self.addCol(CBoolInDocTableCol(u'МДЛП',   'isMdlpRelated', 5, readOnly=not isMdlpEnabled))
        self.addCol(CBoolInDocTableCol(u'Подтв.', 'isConfirmed',   5, readOnly=not isMdlpEnabled))

        self.addCol(CInDocTableCol(u'Код третичной упаковки', 'sscc', 18, readOnly=not isMdlpEnabled))
        self.addCol(CInDocTableCol(u'Код вторичной упаковки', 'sgtin', 50, readOnly=not isMdlpEnabled))

        self._nomenclatureColumn = CNomenclatureInDocTableCol(u'ЛСиИМН', 'nomenclature_id', 50, showFields = CRBComboBox.showName)
        self.addCol(self._nomenclatureColumn)
        self.addCol(CInDocTableCol( u'Серия', 'batch', 16))
        self.addCol(CDateInDocTableCol( u'Годен до', 'shelfTime', 12, canBeEmpty=True))
        self.addCol(CRBInDocTableCol(    u'Вид медицинской помощи', 'medicalAidKind_id', 15, 'rbMedicalAidKind'))
        self.addCol(getStockMotionItemQuantityColumn(u'Кол-во', 'qnt', 12))
        self.addCol(CRBInDocTableCol(u'Ед.Учета', 'unit_id', 12, 'rbUnit', addNone=False))
        self.addCol(CFloatInDocTableCol(u'Цена', 'price', 12, precision=2))
        self.addCol(CItemsModel.CSumCol( u'Сумма', 'sum', 12)).setReadOnly(True)
        self.addCol(CItemsModel.CSumCol( u'НДС', 'vat', 12))
        self.addCol(CInDocTableCol( u'Примечание', 'note', 15))
        self.addHiddenCol('finance_id')

    def getNomenclatureNameById(self, nomenclatureId):
        return forceString(self._nomenclatureColumn.toString(nomenclatureId, None))

    def setData(self, index, value, role=Qt.EditRole):
        col = index.column()
        row = index.row()
        result = CNomenclatureItemsBaseModel.setData(self, index, value, role)
        if role == Qt.EditRole:
            if result:
                if col == self.nomenclatureColumnIndex:
                    nomenclatureId = forceRef(value)
                    unitId = self._getNomenclatureDefaultUnits(nomenclatureId)['defaultStockUnitId']
                    self.setValue(row, 'unit_id', unitId)
                if col in (self.qntColumnIndex,  self.priceColumnIndex):
                    qnt   = forceDouble(self.value(row, 'qnt'))
                    price = forceDouble(self.value(row, 'price'))
                    self.setValue(row, 'sum', round(qnt*price, 2))
        return result

    def fill(self, purchaseContractId):
        if purchaseContractId:
            db = QtGui.qApp.db
            tablePurchaseContract = db.table('StockPurchaseContract')
            tablePurchaseContractItem = db.table('StockPurchaseContract_Item')
            cols = [tablePurchaseContract['finance_id'],
                    tablePurchaseContractItem['idx'],
                    tablePurchaseContractItem['nomenclature_id'],
                    tablePurchaseContractItem['batch'],
                    tablePurchaseContractItem['shelfTime'],
                    tablePurchaseContractItem['qnt'],
                    tablePurchaseContractItem['unit_id'],
                    tablePurchaseContractItem['sum']
                    ]
            cond = [tablePurchaseContract['id'].eq(purchaseContractId),
                    tablePurchaseContract['deleted'].eq(0),
                    tablePurchaseContractItem['master_id'].eq(purchaseContractId),
                    tablePurchaseContractItem['deleted'].eq(0),
                    tablePurchaseContractItem['nomenclature_id'].isNotNull(),
                    tablePurchaseContractItem['comparisonDate'].isNull()
                    ]
            queryTable = tablePurchaseContract.innerJoin(tablePurchaseContractItem, tablePurchaseContractItem['master_id'].eq(tablePurchaseContract['id']))
            records = db.getRecordList(queryTable, cols, cond, order = [tablePurchaseContractItem['idx'].name()])
            for record in records:
                nomenclatureId = forceRef(record.value('nomenclature_id'))
#                unitId = self.getDefaultStockUnitId(nomenclatureId)
                myItem = self.getEmptyRecord()
                myItem.setValue('nomenclature_id', toVariant(nomenclatureId))
                myItem.setValue('unit_id',         record.value('unit_id'))
                myItem.setValue('finance_id',      record.value('finance_id'))
                myItem.setValue('medicalAidKind_id', toVariant(None))
                myItem.setValue('batch',           record.value('batch'))
                myItem.setValue('shelfTime',       record.value('shelfTime'))
                myItem.setValue('qnt',             record.value('qnt'))
                myItem.setValue('sum',             record.value('sum'))
                myItem.setValue('price',           toVariant(forceDouble(record.value('sum'))/forceDouble(record.value('qnt'))))
                myItem.setValue('oldQnt',          record.value('qnt'))
                myItem.setValue('oldSum',          record.value('sum'))
                self.items().append(myItem)
        self.reset()


    def setConfirmAll(self, value):
        for row, item in enumerate(self.items()):
            if forceBool(item.value('isMdlpRelated')):
                self.setValue(row, 'isConfirmed', value)


    def confirmRowsWithSscc(self, sscc):
        # подтвердить строки с заданным sscc
        # вернуть номера подходящих строк
        # применяется для прямого порядка
        result = []
        for row, item in enumerate(self.items()):
            if forceBool(item.value('isMdlpRelated')) and forceString(item.value('sscc')) == sscc:
                self.setValue(row, 'isConfirmed', True)
                result.append(row)
        return result


    def findRowWithSscc(self, sscc):
        # найти строку с заданным sscc
        # вернуть номер подходящей строки
        # применяется для обратного порядка
        for row, item in enumerate(self.items()):
            if forceBool(item.value('isMdlpRelated')) and forceString(item.value('sscc')) == sscc:
                return row
        return None


    def addSgtin(self, sscc, sgtinObject):
        result = len(self.items())
        gtin = sgtinObject.sgtin[:14]
        nomenclatureId = findByIdentification('rbNomenclature', 'urn:gtin', gtin, raiseIfNonFound=False)
        prevItem = None
        if nomenclatureId is not None:
            for prevItem in reversed(self.items()):
                if forceRef(prevItem.value('nomenclature_id')) == nomenclatureId:
                    break
        item = self.getEmptyRecord()
        item.setValue('isMdlpRelated',   True)
        item.setValue('isConfirmed',     not sscc)
        item.setValue('sscc',            sscc)
        item.setValue('sgtin',           sgtinObject.sgtin)
        item.setValue('nomenclature_id', nomenclatureId)
        item.setValue('batch',           sgtinObject.batch)
        item.setValue('shelfTime',       sgtinObject.expirationDate)
        item.setValue('qnt',             1)
        if prevItem:
            item.setValue('price', prevItem.value('price'))
            item.setValue('sum', prevItem.value('sum'))
            item.setValue('vat', prevItem.value('vat'))

        self.addRecord(item)
        return result


    def addSgtins(self, sscc, sgtinObjects):
        # добавить sgtins
        # применяется при обратном порядке
        result = []
        for sgtinObject in sgtinObjects:
            result.append(self.addSgtin(sscc, sgtinObject))
        return result


    def confirmRowsWithSgtin(self, sgtin):
        # подтвердить строки с заданным sgtin
        # вернуть номера подходящих строк
        result = []
        for row, item in enumerate(self.items()):
            if forceBool(item.value('isMdlpRelated')) and forceString(item.value('sgtin')) == sgtin:
                self.setValue(row, 'isConfirmed', True)
                result.append(row)
        return result


    def propagatePriceEtc(self):
        # проставить цены и т.п. в строки, где цена не указана
        samples = {}
        for row, item in enumerate(self.items()):
            if forceBool(item.value('isMdlpRelated')):
                nomenclatureId = forceRef(item.value('nomenclature_id'))
                qnt   = forceDouble(item.value('qnt'))
                price = forceDouble(item.value('price'))
                vat   = forceDouble(item.value('vat'))
                if price > 0.005:
                    samples[nomenclatureId] = (price, vat/qnt if qnt>0 else 0.0)
                elif nomenclatureId in samples:
                    (price, vatPerUnit) = samples[nomenclatureId]
                    self.setValue(row, 'price', price)
                    self.setValue(row, 'sum',   price*qnt)
                    self.setValue(row, 'vat',   vatPerUnit*qnt)



    def isMdlpRelatedGtinPresent(self, gtin):
        for row, item in enumerate(self.items()):
            if forceBool(item.value('isMdlpRelated')) and forceString(item.value('sgtin'))[:14] == gtin:
                return True
        return False


    def findMdlpIndependedNomemclature(self, nomenclatureId):
        for row, item in enumerate(self.items()):
            if not forceBool(item.value('isMdlpRelated')) and forceRef(item.value('nomenclature_id')) == nomenclatureId:
                return row
        return None


    def hasMdlpRelatedCiszs(self):
        for item in self.items():
            if forceBool(item.value('isMdlpRelated')):
                return True
        return False

    def hasConfirmedCiszsOnly(self):
        for item in self.items():
            if forceBool(item.value('isConfirmed')):
                continue
            else:
                return False
        return True

    def hasNoConfirmedCiszsOnly(self):
        for item in self.items():
            if not forceBool(item.value('isConfirmed')):
                continue
            else:
                return False
        return True

    def getConfirmedCiszs(self):
        ssccs  = set()
        refusedSsccs = set()
        sgtins = set()
        for item in self.items():
            if forceBool(item.value('isMdlpRelated')):
                if forceBool(item.value('isConfirmed')):
                    sscc  = forceString(item.value('sscc'))
                    sgtin = forceString(item.value('sgtin'))
                    if sscc:
                        ssccs.add(sscc)
                    else:
                        sgtins.add(sgtin)
                else:
                    sscc  = forceString(item.value('sscc'))
                    if sscc:
                        refusedSsccs.add(sscc)

        return list(ssccs-refusedSsccs), list(sgtins)


    def getConfirmedCiszsWithSumAndVat(self):
        mapSsccsToData  = {}
        refusedSsccs = set()
        sgtins = set()
        for item in self.items():
            if forceBool(item.value('isMdlpRelated')):
                if forceBool(item.value('isConfirmed')):
                    confirmedSscc  = forceString(item.value('sscc'))
                    sgtin = forceString(item.value('sgtin'))
                    sum   = forceDouble(item.value('sum'))
                    vat   = forceDouble(item.value('vat'))
                    if confirmedSscc:
#                        ssccSumAndVat = mapSsccsToData.get(confirmedSscc)
                        if confirmedSscc not in mapSsccsToData:
                            mapSsccsToData[confirmedSscc] = [sum, vat]
                    else:
                        sgtins.add((sgtin, sum, vat))
                else:
                    refusedSscc  = forceString(item.value('sscc'))
                    if refusedSscc:
                        refusedSsccs.add(refusedSscc)
        return ([(sscc, ssccSumAndVat[0], ssccSumAndVat[1])
                 for sscc, ssccSumAndVat in mapSsccsToData.iteritems()
                 if sscc not in refusedSsccs
                ],
                list(sgtins)
               )


    def getRefusedCiszs(self):
        ssccs  = set()
        sgtins = set()
        for item in self.items():
            if forceBool(item.value('isMdlpRelated')) and not forceBool(item.value('isConfirmed')):
                sscc  = forceString(item.value('sscc'))
                sgtin = forceString(item.value('sgtin'))
                if sscc:
                    ssccs.add(sscc)
                else:
                    sgtins.add(sgtin)
        return list(ssccs), list(sgtins)
