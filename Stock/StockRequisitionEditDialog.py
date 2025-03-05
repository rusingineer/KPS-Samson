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

from PyQt4 import QtGui, QtSql, QtCore
from PyQt4.QtCore import Qt, QDate, QDateTime, QVariant, pyqtSignature

from library.crbcombobox         import CRBComboBox
from library.InDocTable          import CInDocTableModel, CFloatInDocTableCol, CRBInDocTableCol
from library.interchange         import getCheckBoxValue, getDateEditValue, getDatetimeEditValue, getLineEditValue, getRBComboBoxValue, setCheckBoxValue, setDateEditValue, setDatetimeEditValue, setLineEditValue, setRBComboBoxValue, setComboBoxValue, getComboBoxValue
from library.ItemsListDialog     import CItemEditorBaseDialog
from library.PrintInfo           import CInfoContext
from library.PrintTemplates      import applyTemplate, CPrintAction, CPrintButton, getPrintTemplates
from library.Utils               import forceBool, forceDouble, forceString, forceRef, forceInt, toVariant

from Reports.ReportBase          import CReportBase, createTable
from Reports.ReportView          import CReportViewDialog
from Stock.NomenclatureComboBox  import CNomenclatureInDocTableCol

from Stock.StockMotionBaseDialog import CNomenclatureItemsBaseModel
from Stock.Utils                 import getStockMotionNumberCounterId, setAgreementRequirementsStock, getStockMotionItemQuantityColumn
from Users.Rights                import urAccessStockAgreeRequirements

from Stock.Ui_StockRequisitionEditDialog import Ui_StockRequisitionDialog


class CStockRequisitionEditDialog(CItemEditorBaseDialog, Ui_StockRequisitionDialog):
    stockDocumentType = 9

    def __init__(self,  parent, isAddRequisition=False):
        CItemEditorBaseDialog.__init__(self, parent, 'StockRequisition')
        self.setupUi(self)
        self.cmbRecipientPerson.setSpecialityIndependents()
        self._stockOrgStructureId = None
        self.isEditRTMsRequisitionEnabled = True
        self.addModels('Items', CItemsModel(self, isAddRequisition))
        self.addObject('actDuplicate', QtGui.QAction(u'Дублировать', self))
        self.addObject('btnPrint', CPrintButton(self, u'Печать'))
        self.btnPrint.setShortcut('F6')
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        if forceBool(QtGui.qApp.preferences.appPrefs.get('isPermitRequisitionsOnlyParentStock', QVariant())):
            orgStructureId = QtGui.qApp.currentOrgStructureId()
            self.setCMBSupplierFilter(orgStructureId)
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
        self.tblItems.createPopupMenu([self.actDuplicate, '-'])
        self.tblItems.popupMenu().addSeparator()
        self.tblItems.addMoveRow()
        self.tblItems.addPopupDelRow()
        self.tblItems.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.tblItems.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.connect(self.actDuplicate, QtCore.SIGNAL('triggered()'), self.on_duplicateItems)
        self.tblItems.enableColsMove()

    def setIsEditRTMsRequisitionEnabled(self, isEditRTMsRequisitionEnabled):
        self.isEditRTMsRequisitionEnabled = isEditRTMsRequisitionEnabled

    def setAgreementRequirementsStock(self):
        isEnabled = setAgreementRequirementsStock(self.cmbSupplier.value())
        self.cmbAgreementStatus.setEnabled(isEnabled)
        self.edtAgreementDate.setEnabled(isEnabled)
        self.cmbAgreementPerson.setEnabled(isEnabled)
        self.edtAgreementNote.setEnabled(isEnabled)


    def setCMBSupplierFilter(self, orgStructureId):
        orgId = QtGui.qApp.currentOrgId()
        stocksIdList = []
        mainStocksIdList = []
        db = QtGui.qApp.db
        tableOS = db.table('OrgStructure')
        if orgStructureId:
            parentId = orgStructureId
            isTheseOrgStructure = True
            while parentId:
                cols = [tableOS['id'],
                        tableOS['parent_id'],
                        tableOS['hasStocks'],
                        tableOS['mainStocks']
                        ]
                cond = [tableOS['deleted'].eq(0),
                        tableOS['id'].eq(parentId)
                       ]
                record = db.getRecordEx(tableOS, cols, cond)
                if record:
                    parentId = forceRef(record.value('parent_id'))
                    hasStocks = forceInt(record.value('hasStocks'))
                    mainStocks = forceInt(record.value('mainStocks'))
                    if hasStocks == 1 or mainStocks == 1:
                        nextOrgStructureId = forceRef(record.value('id'))
                        if nextOrgStructureId and nextOrgStructureId not in stocksIdList:
                            stocksIdList.append(nextOrgStructureId)
                            if not isTheseOrgStructure:
                                break
                            isTheseOrgStructure = False
                else:
                    parentId = None
        if not stocksIdList or (len(stocksIdList) == 1 and stocksIdList[0] == orgStructureId):
            cols = [tableOS['id']]
            cond = [tableOS['deleted'].eq(0)]
            if orgId:
                cond.append(tableOS['organisation_id'].eq(orgId))
            cond.append(tableOS['mainStocks'].eq(1))
            mainStocksIdList = db.getDistinctIdList(tableOS, cols, cond)
            stocksIdList = list(set(stocksIdList) | set(mainStocksIdList))
            if mainStocksIdList:
                mainStocksIdList = db.getTheseAndParents('OrgStructure', 'parent_id', mainStocksIdList)
        if stocksIdList:
            self.cmbSupplier.setFilter('''id IN (%s)'''%(u','.join(str(id) for id in list(set(stocksIdList) | set(mainStocksIdList)) if id)))
        else:
            self.cmbSupplier.setFilter('''False''')
        self.cmbSupplier.setIsValidIdList(stocksIdList)


    def setDefaults(self):
        self.edtDate.setDate(QDate.currentDate())
        self.edtDeadlineDate.setDate(QDate())
        self.cmbRecipient.setValue(QtGui.qApp.currentOrgStructureId())
        self.cmbRecipientPerson.setValue(QtGui.qApp.userId)


    def setReadOnly(self):
        isRequisitionSatisfied = False
        db = QtGui.qApp.db
        table = db.table('StockRequisition_Item')
        records = db.getRecordList(table, 'satisfiedQnt', where=table['master_id'].eq(self._id))
        for record in records:
            satisfiedQnt = forceDouble(record.value('satisfiedQnt'))
            if satisfiedQnt>0:
                isRequisitionSatisfied = True
        if isRequisitionSatisfied or not self.isEditRTMsRequisitionEnabled:
            self.edtDate.setReadOnly(True)
            self.edtDeadlineDate.setReadOnly(True)
            self.chkRevoked.setEnabled(False)
            self.edtDeadlineTime.setReadOnly(True)
            self.edtNumber.setReadOnly(True)
            self.cmbSupplier.setReadOnly(True)
            self.cmbRecipient.setReadOnly(True)
            self.cmbRecipientPerson.setReadOnly(True)
            self.edtNote.setReadOnly(True)
            self.modelItems.setReadOnly(True)
            self.actDuplicate.setEnabled(False)

    def _generateStockMotionNumber(self):
        if unicode(self.edtNumber.text()):
            return

        counterId = getStockMotionNumberCounterId(self.stockDocumentType)
        if not counterId:
            return

        number = QtGui.qApp.getDocumentNumber(None, counterId, date=QtCore.QDate.currentDate())
        if number:
            self.edtNumber.setText(number)

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
            data = { 'StockRequisitionList': CStockMotionInfoList(context, idList)}
            QtGui.qApp.call(self, applyTemplate, (self, templateId, data))


    def getStockContext(self):
        return ['StockRequisitionList']


    def dumpParams(self, cursor):
        db = QtGui.qApp.db
        description = []
        date = self.edtDate.date()
        if date:
           description.append(u'Дата %s'%forceString(date))
        Deadline = QDateTime(self.edtDeadlineDate.date(), self.edtDeadlineTime.time())
        if Deadline:
           description.append(u'Срок исполнения %s'%forceString(Deadline))
        revoked = forceBool(self.chkRevoked.isChecked())
        if revoked:
            description.append(u'Отменено')
        supplier = self.cmbSupplier.value()
        if supplier:
            description.append(u'Поставщик %s'%forceString(db.translate('OrgStructure', 'id', supplier, 'name')))
        recipient = self.cmbRecipient.value()
        if recipient:
            description.append(u'Заказчик %s'%forceString(db.translate('OrgStructure', 'id', recipient, 'name')))
        receiverPerson = self.cmbRecipientPerson.value()
        if receiverPerson:
            description.append(u'Ответственный %s' % forceString(
                db.translate('vrbPersonWithSpeciality', 'id', receiverPerson, 'name')))
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


#    def setRequestMode(self):
#        self.edtDate.setEnabled(False)
#        self.cmbRecipient.setEnabled(False)


    def setRecord(self, record):
        CItemEditorBaseDialog.setRecord(self, record)
        setLineEditValue(   self.edtNumber,         record, 'number')
        setDateEditValue(   self.edtDate,           record, 'date')
        setDatetimeEditValue(self.edtDeadlineDate, self.edtDeadlineTime, record, 'deadline')
        setCheckBoxValue(   self.chkRevoked,        record, 'revoked')
        setRBComboBoxValue( self.cmbSupplier,       record, 'supplier_id')
        setRBComboBoxValue( self.cmbRecipient,      record, 'recipient_id')
        setRBComboBoxValue(self.cmbRecipientPerson, record, 'recipientPerson_id')
        setLineEditValue(   self.edtNote,           record, 'note')
        setComboBoxValue(   self.cmbAgreementStatus, record, 'agreementStatus')
        setDateEditValue(   self.edtAgreementDate,  record, 'agreementDate')
        setRBComboBoxValue( self.cmbAgreementPerson,record, 'agreementPerson_id')
        setLineEditValue(   self.edtAgreementNote,  record, 'agreementNote')
        self.modelItems.loadItems(self.itemId())
        self.setIsDirty(False)
        self.setReadOnly()


    def getRecord(self):
        record = CItemEditorBaseDialog.getRecord(self)
        getLineEditValue(   self.edtNumber,         record, 'number')
        getDateEditValue(   self.edtDate,           record, 'date')
        getDatetimeEditValue(self.edtDeadlineDate, self.edtDeadlineTime, record, 'deadline', True)
        getCheckBoxValue(   self.chkRevoked,        record, 'revoked')
        getRBComboBoxValue( self.cmbSupplier,       record, 'supplier_id')
        getRBComboBoxValue( self.cmbRecipient,      record, 'recipient_id')
        getRBComboBoxValue(self.cmbRecipientPerson, record, 'recipientPerson_id')
        getLineEditValue(   self.edtNote,           record, 'note')
        getComboBoxValue(   self.cmbAgreementStatus, record, 'agreementStatus')
        getDateEditValue(   self.edtAgreementDate,  record, 'agreementDate')
        getRBComboBoxValue( self.cmbAgreementPerson,record, 'agreementPerson_id')
        getLineEditValue(   self.edtAgreementNote,  record, 'agreementNote')
        return record


    def saveInternals(self, id):
        self.modelItems.saveItems(id)


    def checkDataEntered(self):
        result = True
        isRightAgreeRequirementsStock = QtGui.qApp.userHasRight(urAccessStockAgreeRequirements)
        accordingRequirementsStockType = forceInt(QtGui.qApp.preferences.appPrefs.get('accordingRequirementsStockType', QVariant()))
        if isRightAgreeRequirementsStock and forceBool(accordingRequirementsStockType):
            if accordingRequirementsStockType == 1:
                supplierId = self.cmbSupplier.value()
                if supplierId:
                    db = QtGui.qApp.db
                    table = db.table('OrgStructure')
                    record = db.getRecordEx(table, table['id'], [table['id'].eq(supplierId), table['mainStocks'].eq(1), table['deleted'].eq(0)])
                    if record and forceRef(record.value('id')) == supplierId:
                        result = result and (self.edtAgreementDate.date() or self.checkInputMessage(u'дату согласования', False, self.edtAgreementDate))
                        result = result and (self.cmbAgreementPerson.value() or self.checkInputMessage(u'согласовавшего сотрудника', False, self.cmbAgreementPerson))
            elif accordingRequirementsStockType == 2:
                result = result and (self.edtAgreementDate.date() or self.checkInputMessage(u'дату согласования', False, self.edtAgreementDate))
                result = result and (self.cmbAgreementPerson.value() or self.checkInputMessage(u'согласовавшего сотрудника', False, self.cmbAgreementPerson))
#        result = result and (self.cmbPurpose.value() or self.checkInputMessage(u'назначение', False, self.cmbPurpose))
        result = result and self.checkItemsDataEntered()
        return result


    def checkItemsDataEntered(self):
        existsFN = set()
        for row, item in enumerate(self.modelItems.items()):
            if not self.checkItemDataEntered(row, item, existsFN):
                return False
        return True


    def checkItemDataEntered(self, row, item, existsFN):
        nomenclatureId = forceRef(item.value('nomenclature_id'))
        qnt            = forceDouble(item.value('qnt'))
        financeId      = forceRef(item.value('finance_id'))
        medicalAidKindId      = forceRef(item.value('medicalAidKind_id'))
        result = nomenclatureId or self.checkInputMessage(u'лекарственное средство или изделие медицинского назначения', False, self.tblItems, row, 0)
        result = result and (qnt or self.checkInputMessage(u'количество', False, self.tblItems, row, 2))
        fnKey = (financeId, nomenclatureId, medicalAidKindId)
        if fnKey in existsFN:
            self.checkValueMessage(u'ЛСиИМН с таким типом финансирования уже указан', False, self.tblItems, row, 0)
        existsFN.add(fnKey)
        return result


    @pyqtSignature('const QDate&')
    def on_edtDeadlineDate_dateChanged(self, date):
        self.edtDeadlineTime.setEnabled(bool(date))


    def on_duplicateItems(self):
        index = self.tblItems.currentIndex()
        row = index.row()
        items = self.modelItems.items()
        if 0<=row<len(items):
            newItem = QtSql.QSqlRecord(items[row])
            newItem.setValue('id', QVariant())
            self.modelItems.insertRecord(row+1, newItem)


    @pyqtSignature('')
    def on_cmbSupplier_valueChanged(self):
        self._stockOrgStructureId = self.cmbSupplier.value()
        self.modelItems._stockOrgStructureId = self.cmbSupplier.value()
        self.modelItems.nomenclatureColumn.setOrgStructureId(self._stockOrgStructureId)
        self.setAgreementRequirementsStock()


    @pyqtSignature('')
    def on_cmbRecipient_valueChanged(self):
        orgStructureId = self.cmbRecipient.value()
        self.cmbRecipientPerson.setOrgStructureId(orgStructureId)
        if forceBool(QtGui.qApp.preferences.appPrefs.get('isPermitRequisitionsOnlyParentStock', QVariant())):
            self.setCMBSupplierFilter(orgStructureId)


class CItemsModel(CNomenclatureItemsBaseModel):
    class CLocNomenclatureCol(CNomenclatureInDocTableCol):
        def __init__(self, title, fieldName, width, _stockOrgStructureId, **params):
            CNomenclatureInDocTableCol.__init__(self, title, fieldName, width, **params)
            self._stockOrgStructureId = _stockOrgStructureId
            self.isAddRequisition = params.get('isAddRequisition', False)

        def createEditor(self, parent):
            editor = CNomenclatureInDocTableCol.createEditor(self, parent)
            if self.isAddRequisition: #0013272
                editor.setIsFinanceVisible(2)
            if QtGui.qApp.isSMNomenclatureColFilter() and self._stockOrgStructureId:
                editor.setOrgStructureId(self._stockOrgStructureId)
                editor.setOnlyExists()
            return editor

        def setOrgStructureId(self, _stockOrgStructureId):
            self._stockOrgStructureId = _stockOrgStructureId

    def __init__(self, parent, isAddRequisition=False):
        CInDocTableModel.__init__(self, 'StockRequisition_Item', 'id', 'master_id', parent)
        self.stockDocumentType = parent.stockDocumentType
        self.isAddRequisition = isAddRequisition
        self.isPriceLineEditable = False
        self.isUpdateValue = False
        self._mapNomenclatureIdToUnitId = {}
        self._supplierOrgId = None
        self._receiverId = None
        self._supplierId = None
        self._stockOrgStructureId = parent._stockOrgStructureId
        self.editor = None
        self.nomenclatureColumn = self.CLocNomenclatureCol(u'ЛСиИМН', 'nomenclature_id', 50, self._stockOrgStructureId, isAddRequisition=self.isAddRequisition, showFields = CRBComboBox.showName)
        self.addCol(self.nomenclatureColumn)
        self.addCol(CRBInDocTableCol(    u'Тип финансирования', 'finance_id', 15, 'rbFinance'))
        self.addCol(CRBInDocTableCol(    u'Вид медицинской помощи', 'medicalAidKind_id', 15, 'rbMedicalAidKind'))
        self.addCol(getStockMotionItemQuantityColumn(u'Кол-во', 'qnt', 12))
        self.addCol(CRBInDocTableCol(u'Ед.Учета', 'unit_id', 12, 'rbUnit', addNone=False))
        self.addCol(CFloatInDocTableCol( u'Отпущено', 'satisfiedQnt', 12, precision=2)).setReadOnly()


    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid():
            return False
        col = index.column()
        row = index.row()
        if col == self.getColIndex('nomenclature_id'):
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
                    self.emitRowChanged(row)
            return result
        else:
            return CNomenclatureItemsBaseModel.setData(self, index, value, role)

