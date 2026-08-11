# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2025 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################


from PyQt4 import QtGui, QtSql
from PyQt4.QtCore import Qt, QDate, QDateTime, QModelIndex, QString, QVariant, pyqtSignature, SIGNAL
from PyQt4.QtGui import QFont

from library.crbcombobox import CRBComboBox
from RefBooks.Service.RBServiceComboBox import CRBServiceInDocTableCol

from library.DateEdit import CDateEdit
from library.DialogBase import CDialogBase
from library.InDocTable             import (
                                            CRecordListModel,
                                            CInDocTableModel,
                                            CBoolInDocTableCol,
                                            CDateInDocTableCol,
                                            CEnumInDocTableCol,
                                            CFloatInDocTableCol,
                                            CInDocTableCol,
                                            CIntInDocTableCol,
                                            CRBInDocTableCol,
                                           )
from library.database import CTableRecordCache
from library.interchange            import (
                                            getCheckBoxValue,
                                            getComboBoxValue,
                                            getDateEditValue,
                                            getDoubleBoxValue,
                                            getLineEditValue,
                                            getRBComboBoxValue,
                                            getSpinBoxValue,
                                            getTextEditValue,
                                            setCheckBoxValue,
                                            setComboBoxValue,
                                            setDateEditValue,
                                            setDoubleBoxValue,
                                            setLineEditValue,
                                            setRBComboBoxValue,
                                            setSpinBoxValue,
                                            setTextEditValue,
                                           )
from library.ItemsListDialog import CItemsListDialog, CItemEditorBaseDialog
from library.TableModel import CTableModel, CDateCol, CRefBookCol, CSumCol, CTextCol
from library.PrintInfo              import CInfoContext
from library.PrintTemplates         import customizePrintButton,  getPrintButton,  applyTemplate
from library.Utils import (agreeNumberAndWord, copyFields, forceDate, forceDouble, forceInt, forceRef, forceString,
                           forceStringEx, formatNum, formatSex, toVariant, trim, )

from Accounting.FormProgressDialog import CContractFormProgressDialog, CFormProgressDialog
from Accounting.Tariff import CTariff
from Accounting.Utils import getContractDescr, packExposeDiscipline, unpackExposeDiscipline, roundMath
from Events.ActionsSelector import CEnableCol
from Events.EventInfo import CContractInfo, CContractInfoList, CTariffInfoList
from Exchange.ExportTariffsR23 import ExportTariffsR23
from Exchange.ExportTariffsXML import ExportTariffsXML
from Exchange.ImportTariffsCSV import ImportTariffsCSV
from Exchange.ImportTariffs import ImportTariffs
from Exchange.ImportTariffsINFIS import ImportTariffsINFIS
from Exchange.ImportTariffsR23 import ImportTariffsR23
from Exchange.ImportTariffsR29 import ImportTariffsR29
from Exchange.ImportTariffsR47 import ImportTariffsR47
from Exchange.ImportTariffsR51 import importTariffsR51
from Exchange.ImportTariffsR61 import importTariffsR61
from Exchange.ImportTariffsR67 import ImportTariffsR67
from Exchange.ImportTariffsR77 import ImportTariffsR77
from Exchange.ImportTariffsXML import ImportTariffsXML
from RefBooks.Tables import rbAccountExportFormat, rbFinance
from Reports.ReportBase import CReportBase, createTable
from Reports.Report import CReport
from Users.Rights import urAccessPriceCalculate

from OrgComboBox import COrgInDocTableCol, CInsurerInDocTableCol
from Orgs import selectOrganisation
from Exchange.ExportTariffsXLS import ExportTariffsXLS
from IntroducePercentDialog import CIntroducePercentDialog
from Utils import getAccountInfo, getOrganisationInfo

from TariffAddDialog import CTariffAddDialog
from Ui_ContractEditor import Ui_ContractEditorDialog
from Ui_ContractMultipleEditor     import Ui_ContractMultipleEditorDialog
from Ui_PriceCoefficientEditor import Ui_PriceCoefficientDialog
from Ui_PriceListDialog import Ui_PriceListDialog
from Ui_ParamsContractDialog import Ui_ParamsContractDialog
from Ui_ContractItemsListDialog import Ui_ContractItemsListDialog

def selectContract(parent, contractId, filterParams = {}):
    try:
        dialog = CContractsList(parent, forSelect = True)
        dialog.initFilterParams(filterParams)
        dialog.setCurrentItemId(contractId)
        if dialog.exec_():
            itemId = dialog.currentItemId()
            filterParams = dialog.setFilterParams()
            return (itemId, u'%s от %s'%(forceString(dialog.currentData(3)), forceString(dialog.currentData(4))), filterParams)
    finally:
        dialog.deleteLater()
    return None, u'', filterParams


class CContractItemsListDialog(Ui_ContractItemsListDialog, CItemsListDialog):

    def __init__(self, parent, forSelect = False):
        CItemsListDialog.__init__(self, parent, [
            CRefBookCol(u'Источник финансирования', ['finance_id'], 'rbFinance', 30),
            CTextCol(u'Группа',                  ['grouping'],  30),
            CTextCol(u'Основание',               ['resolution'],20),
            CTextCol(u'Номер',                   ['number'],    20),
            CDateCol(u'Дата',                    ['date'],      10),
            CDateCol(u'Нач.дата',                ['begDate'],   10),
            CDateCol(u'Кон.дата',                ['endDate'],   10),
            ], 'Contract', ['finance_id', 'grouping', 'resolution', 'number', 'date'], forSelect, multiSelect=True)
        self.setWindowTitleEx(u'Договоры')


    def exec_(self):
        self.applyFilterContract(self.order)
        return CDialogBase.exec_(self)


    def renewListAndSetTo(self, itemId=None):
        self.applyFilterContract(self.order, itemId)


class CDoubleSpinBoxEdit(QtGui.QDoubleSpinBox):
    def __init__(self, parent=None):
        QtGui.QDoubleSpinBox.__init__(self, parent)


class CCoefficientItemDelegate(QtGui.QItemDelegate):
    def __init__(self, parent=None):
        QtGui.QItemDelegate.__init__(self, parent)


    def createEditor(self, parent, option, index):
        editor = CDoubleSpinBoxEdit(parent)
        return editor


    def setEditorData(self, editor, index):
        model  = index.model()
        data = model.data(index, Qt.EditRole)
        editor.setValue(forceDouble(data))


    def setModelData(self, editor, model, index):
        model.setData(index, QVariant(editor.value()))


class CDateItemDelegate(QtGui.QItemDelegate):
    def __init__(self, parent=None):
        QtGui.QItemDelegate.__init__(self, parent)


    def createEditor(self, parent, option, index):
        editor = CDateEdit(parent)
        return editor


    def setEditorData(self, editor, index):
        model  = index.model()
        data = model.data(index, Qt.EditRole)
        editor.setDate(data.toDate())


    def setModelData(self, editor, model, index):
        model.setData(index, QVariant(editor.date()))


class CStringEdit(QtGui.QLineEdit):
    def __init__(self, parent=None):
        QtGui.QLineEdit.__init__(self, parent)


class CStringItemDelegate(QtGui.QItemDelegate):
    def __init__(self, parent=None):
        QtGui.QItemDelegate.__init__(self, parent)


    def createEditor(self, parent, option, index):
        editor = CStringEdit(parent)
        return editor


    def setEditorData(self, editor, index):
        model  = index.model()
        data = model.data(index, Qt.EditRole)
        editor.setText(forceString(data))


    def setModelData(self, editor, model, index):
        model.setData(index, QVariant(editor.text()))


class CContractsList(CContractItemsListDialog):
    def __init__(self, parent, forSelect = False):
        CContractItemsListDialog.__init__(self, parent, forSelect)
        self.tblItems.setPopupMenu(self.mnuItems)
        self.btnSynchronize.setEnabled(False)
        currentDate = QDate.currentDate()
        self.edtBegDate.setDate(QDate(currentDate.year(), 1, 1))
        self.edtEndDate.setDate(QDate(currentDate.year(), 12, 31))
        self.cmbFinanceSource.setTable('rbFinance', addNone=True)
        self.cmbEventType.setTable('EventType', addNone=True)
        self.getGroupingText()
        self.getResolutionText()
        self.filterParams = {}
        self.resetFilterContract()


    def setupUi(self, widget):
        self.setupPopupMenu()
        self.addObject('btnSynchronize',  QtGui.QPushButton(u'Синхронизация', self))
        CContractItemsListDialog.setupUi(self, widget)
        self.buttonBox.addButton(self.btnSynchronize, QtGui.QDialogButtonBox.ActionRole)
        self.btnEdit.clicked.disconnect()
        self.btnEdit.clicked.connect(self.on_btnEdit_clicked)


    def preSetupUi(self):
        self.addObject('btnPrint', getPrintButton(self, 'contracts'))
        self.addObject('btnNew',  QtGui.QPushButton(u'Вставка F9', self))
        self.addObject('btnEdit',  QtGui.QPushButton(u'Правка F4', self))
        self.addObject('btnFilter',  QtGui.QPushButton(u'Фильтр', self))
        self.addObject('btnSelect',  QtGui.QPushButton(u'Выбор', self))


    def setupPopupMenu(self):
        self.mnuItems = QtGui.QMenu(self)
        self.mnuItems.setObjectName('mnuItems')
        self.actRemoveContract = QtGui.QAction(u'Удалить', self)
        self.actRemoveContract.setObjectName('actRemoveContract')
        self.actDuplicateContract = QtGui.QAction(u'Дублировать', self)
        self.actDuplicateContract.setObjectName('actDuplicateContract')
        self.actDuplicateContractNoExpense = QtGui.QAction(u'Дублировать с тарифами без статей затрат', self)
        self.actDuplicateContractNoExpense.setObjectName('actDuplicateContractNoExpense')
        self.actDuplicateContractNoTariff = QtGui.QAction(u'Дублировать без тарифов', self)
        self.actDuplicateContractNoTariff.setObjectName('actDuplicateContractNoTariff')
        self.actSynchronizeContract = QtGui.QAction(u'Синхронизация', self)
        self.actSynchronizeContract.setObjectName('actSynchronizeContract')
        self.actDisableInAccounts = QtGui.QAction(u'Установить признак "Не отображать в разделе Счета"', self)
        self.actDisableInAccounts.setObjectName('actDisableInAccounts')
        self.actEnableInAccounts = QtGui.QAction(u'Убрать признак "Не отображать в разделе Счета"', self)
        self.actEnableInAccounts.setObjectName('actEnableInAccounts')

        self.mnuItems.addAction(self.actDuplicateContract)
        self.mnuItems.addSeparator()
        self.mnuItems.addAction(self.actDuplicateContractNoExpense)
        self.mnuItems.addSeparator()
        self.mnuItems.addAction(self.actDuplicateContractNoTariff)
        self.mnuItems.addSeparator()
        self.mnuItems.addAction(self.actRemoveContract)
        self.mnuItems.addSeparator()
        self.mnuItems.addAction(self.actSynchronizeContract)
        self.mnuItems.addSeparator()
        self.mnuItems.addAction(self.actDisableInAccounts)
        self.mnuItems.addAction(self.actEnableInAccounts)


    def getItemEditor(self):
        return CContractEditor(self)


    def on_btnEdit_clicked(self):
        selectionModel = self.tblItems.selectionModel()
        if len(selectionModel.selectedRows()) == 1:
            return CItemsListDialog.on_btnEdit_clicked(self)

        elif len(selectionModel.selectedRows()) > 1:
            dialog = CContractMultipleEditor(self)
            try:
                dialog.load(self.tblItems.selectedItemIdList())
                if dialog.exec_():
                    itemId = dialog.itemIdList()[0]
                    self.renewListAndSetTo(itemId)
            finally:
                dialog.deleteLater()

        else:
            self.on_btnNew_clicked()


    @pyqtSignature('')
    def on_mnuItems_aboutToShow(self):
        itemPresent = self.tblItems.currentIndex().row()>=0
        self.actDuplicateContract.setEnabled(itemPresent)
        self.actDuplicateContractNoTariff.setEnabled(itemPresent)
        self.actRemoveContract.setEnabled(itemPresent)
        self.actSynchronizeContract.setEnabled(itemPresent and bool(self.getPriceListId()))
        self.actDisableInAccounts.setEnabled(itemPresent)
        self.actEnableInAccounts.setEnabled(itemPresent)


    def getPriceListId(self):
        contractId = self.tblItems.currentItemId()
        priceListId = None
        if contractId:
            db = QtGui.qApp.db
            table = db.table('Contract')
            record = db.getRecordEx(table, [table['priceList_id']], [table['deleted'].eq(0), table['priceList_id'].eq(contractId)])
            priceListId = forceRef(record.value('priceList_id')) if record else None
        return priceListId


    @pyqtSignature('')
    def on_actDuplicateContract_triggered(self):
        self.duplicateContract()


    @pyqtSignature('')
    def on_actDisableInAccounts_triggered(self):
        self.setDisableInAccounts(1)


    @pyqtSignature('')
    def on_actEnableInAccounts_triggered(self):
        self.setDisableInAccounts(0)


    @pyqtSignature('')
    def on_btnPrint_clicked(self):
        pass

    @pyqtSignature('int')
    def on_btnPrint_printByTemplate(self,  templateId):
        context = CInfoContext()
        contract = context.getInstance(CContractInfo, self.tblItems.currentItemId())
        contractList = context.getInstance(CContractInfoList, tuple(self.model.idList()))
        data = {
                 'currentContract': contract,
                 'contractList': contractList
               }
        applyTemplate(self, templateId, data)


    def setDisableInAccounts(self, disableInAccounts=0):
        contractIdList = self.tblItems.selectedItemIdList()
        if contractIdList:
            db = QtGui.qApp.db
            table = db.table('Contract')
            db.transaction()
            try:
                records = db.getRecordList(table, '*', [table['id'].inlist(contractIdList), table['deleted'].eq(0)])
                for record in records:
                    record.setValue('disableInAccounts', toVariant(disableInAccounts))
                    db.updateRecord(table, record)
                db.commit()
            except:
                db.rollback()
                raise
            self.renewListAndSetTo()


    @pyqtSignature('')
    def on_actDuplicateContractNoExpense_triggered(self):
        self.duplicateContract(dupTariff=True, dupExpense=False)


    @pyqtSignature('')
    def on_actSynchronizeContract_triggered(self):
        self.on_btnSynchronize_clicked()


    @pyqtSignature('')
    def on_actDuplicateContractNoTariff_triggered(self):
        self.duplicateContract(dupTariff=False, dupExpense=False)


    def duplicateContract(self, dupTariff=True, dupExpense=True):
        contractId = self.tblItems.currentItemId()
        db = QtGui.qApp.db
        table = db.table('Contract')
        tableContractTariff = db.table('Contract_Tariff')
        tableContractExpense = db.table('Contract_CompositionExpense')
        db.transaction()
        try:
            record = db.getRecord(table, '*', contractId)
            record.setNull('id')
            record.setValue('number', toVariant(forceString(record.value('number'))+u'-копия'))
            newId = db.insertRecord(table, record)
            db.copyDepended(db.table('Contract_Contingent'), 'master_id', contractId, newId)
            db.copyDepended(db.table('Contract_Contragent'), 'master_id', contractId, newId)
            db.copyDepended(db.table('Contract_Specification'), 'master_id', contractId, newId)
            db.copyDepended(db.table('Contract_Attribute'),  'master_id', contractId, newId)
            db.copyDepended(db.table('Contract_Coefficient'),'master_id', contractId, newId)
            if dupTariff:
                stmt = db.selectStmt(tableContractTariff, '*', [tableContractTariff['master_id'].eq(contractId), tableContractTariff['deleted'].eq(0)], 'id')
                qquery = db.query(stmt)
                while qquery.next():
                    recordTariff = qquery.record()
                    tariffId = forceRef(recordTariff.value('id'))
                    recordTariff.setNull('id')
                    recordTariff.setValue('master_id', toVariant(newId))
                    newTariffId = db.insertRecord(tableContractTariff, recordTariff)
                    if dupExpense and tariffId and newTariffId:
                        recordExpenses = db.getRecordList(tableContractExpense, '*', [tableContractExpense['master_id'].eq(tariffId)])
                        for recordExpense in recordExpenses:
                            recordExpense.setNull('id')
                            recordExpense.setValue('master_id', toVariant(newTariffId))
                            db.insertRecord(tableContractExpense, recordExpense)
            db.commit()
        except:
            db.rollback()
            raise
        self.renewListAndSetTo(newId)


    @pyqtSignature('')
    def on_actRemoveContract_triggered(self):
        contractId = self.tblItems.currentItemId()
        db = QtGui.qApp.db
        table = db.table('Contract')
        db.transaction()
        try:
            db.deleteRecord(table, table['id'].eq(contractId))
            db.commit()
            self.tblItems.removeCurrentRow()
        except:
            db.rollback()
            QtGui.qApp.logCurrentException()
            raise


    @pyqtSignature('QModelIndex')
    def on_tblItems_clicked(self, index):
        self.btnSynchronize.setEnabled(bool(self.getPriceListId()))


    @pyqtSignature('')
    def on_btnSynchronize_clicked(self):
        contractId = self.tblItems.currentItemId()
        if contractId:
            CPriceListDialog(self, contractId).exec_()
        self.renewListAndSetTo(contractId)
#        self.applyFilterContract(self.order, contractId)


    @pyqtSignature('QAbstractButton*')
    def on_buttonBoxFilterContract_clicked(self, button):
        buttonCode = self.buttonBoxFilterContract.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.applyFilterContract(self.order, self.tblItems.currentItemId())
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.resetFilterContract()
            self.setFilterParams()
            self.getTblItemsIdList()
        self.btnSynchronize.setEnabled(bool(self.getPriceListId()))


    def applyFilterContract(self, order = None, itemId=None):
        self.setFilterParams()
        self.getTblItemsIdList(order, itemId)


    def initFilterParams(self, filterParams):
        if filterParams:
            self.filterParams = filterParams
            self.getFilterParams()


    def setFilterParams(self):
        self.filterParams = {}
        self.filterParams['financeId'] = self.cmbFinanceSource.value()
        self.filterParams['groupingIndex'] = self.cmbGrouping.currentIndex()
        self.filterParams['grouping'] = self.cmbGrouping.text()
        self.filterParams['resolutionIndex'] = self.cmbResolution.currentIndex()
        self.filterParams['resolution'] = self.cmbResolution.text()
        self.filterParams['priceList'] = self.cmbPriceList.currentIndex()
        self.filterParams['edtBegDate'] = self.edtBegDate.date()
        self.filterParams['edtEndDate'] = self.edtEndDate.date()
        self.filterParams['enableInAccounts'] = self.cmbEnableInAccounts.currentIndex()
        self.filterParams['eventType_id'] = self.cmbEventType.value()
        return self.filterParams


    def getFilterParams(self):
        self.cmbFinanceSource.setValue(self.filterParams.get('financeId', None))
        self.cmbGrouping.setCurrentIndex(self.filterParams.get('groupingIndex', 0))
        self.cmbGrouping.setValue(self.filterParams.get('grouping', u''))
        self.cmbResolution.setCurrentIndex(self.filterParams.get('resolutionIndex', 0))
        self.cmbResolution.setValue(self.filterParams.get('resolution', u''))
        self.cmbPriceList.setCurrentIndex(self.filterParams.get('priceList', 0))
        currentDate = QDate.currentDate()
        self.edtBegDate.setDate(self.filterParams.get('edtBegDate', QDate(currentDate.year(), 1, 1)))
        self.edtEndDate.setDate(self.filterParams.get('edtEndDate', QDate(currentDate.year(), 12, 31)))
        self.cmbEnableInAccounts.setCurrentIndex(self.filterParams.get('enableInAccounts', 0))
        self.cmbEventType.setValue(self.filterParams.get('eventType_id', None))

    def getGroupingText(self):
        domain = u'\'не определено\','
        domain = self.getTextStrComboBox(domain, u'grouping')
        self.cmbGrouping.setDomain(domain)


    def getResolutionText(self):
        domain = u'\'не определено\','
        domain = self.getTextStrComboBox(domain, u'resolution')
        self.cmbResolution.setDomain(domain)


    def getTextStrComboBox(self, domain, field):
        query = QtGui.qApp.db.query(u'''SELECT DISTINCT Contract.%s FROM Contract WHERE Contract.deleted = 0 ORDER BY Contract.%s ASC'''%(field, field))
        while query.next():
            record = query.record()
            grouping = forceString(record.value(field))
            if grouping:
               domain +=  u'\'' + grouping + u'\','
        return domain


    def resetFilterContract(self):
        # self.cmbFinanceSource.setCurrentIndex(0)
        self.cmbFinanceSource.setCode(0)
        self.cmbGrouping.setCurrentIndex(0)
        self.cmbResolution.setCurrentIndex(0)
        self.cmbPriceList.setCurrentIndex(0)
        currentDate = QDate.currentDate()
        self.edtBegDate.setDate(QDate(currentDate.year(), 1, 1))
        self.edtEndDate.setDate(QDate(currentDate.year(), 12, 31))
        self.cmbEventType.setCode(0)


    def getTblItemsIdList(self, order = None, itemId=None):
        financeId = self.filterParams.get('financeId', None)
        groupingIndex = self.filterParams.get('groupingIndex', 0)
        grouping = self.filterParams.get('grouping', u'')
        resolutionIndex = self.filterParams.get('resolutionIndex', 0)
        resolution = self.filterParams.get('resolution', u'')
        priceList = self.filterParams.get('priceList', 0)
        edtBegDate = self.filterParams.get('edtBegDate', None)
        edtEndDate = self.filterParams.get('edtEndDate', None)
        enableInAccounts = self.filterParams.get('enableInAccounts', 0)
        eventType_id = self.filterParams.get('eventType_id', None)

        db = QtGui.qApp.db
        tableContract = db.table('Contract')
        cond = [tableContract['deleted'].eq(0)]
        if enableInAccounts:
            cond.append(tableContract['disableInAccounts'].eq(enableInAccounts-1))
        if financeId:
            cond.append(tableContract['finance_id'].eq(financeId))
        if groupingIndex and grouping:
            cond.append(tableContract['grouping'].like(grouping))
        if resolutionIndex and resolution:
            cond.append(tableContract['resolution'].like(resolution))
        if priceList:
            priceListId = db.getDistinctIdList(tableContract, u'priceList_id', [tableContract['deleted'].eq(0), tableContract['priceList_id'].isNotNull()])
            if priceList == 1:
                cond.append(tableContract['id'].inlist(priceListId))
            elif priceList == 2:
                cond.append(tableContract['id'].notInlist(priceListId))
        if edtBegDate and edtEndDate:
            cond.append(u'''(Contract.begDate >= %s AND Contract.begDate < %s )
OR (Contract.begDate <= %s AND Contract.endDate > %s )'''%(db.formatDate(edtBegDate), db.formatDate(edtEndDate), db.formatDate(edtBegDate), db.formatDate(edtBegDate)))
        elif edtBegDate:
            cond.append(tableContract['begDate'].isNotNull())
            cond.append(db.joinOr([tableContract['begDate'].dateGe(edtBegDate), db.joinAnd([tableContract['begDate'].dateLe(edtBegDate), tableContract['endDate'].dateGe(edtBegDate)])]))
        elif edtEndDate:
            cond.append(tableContract['begDate'].isNotNull())
            cond.append(tableContract['begDate'].dateLe(edtEndDate))
        if eventType_id:
            cond.append(u'''Contract.id in (select master_id from Contract_Specification where eventType_id = %s and deleted = 0 )'''%eventType_id)
        if order:
            idList = db.getDistinctIdList(tableContract, u'id', cond, order)
        else:
            idList = db.getDistinctIdList(tableContract, u'id', cond)
        self.tblItems.setIdList(idList, itemId)
#        if idList:
#            self.tblItems.selectRow(0)
        self.label.setText(u'всего: %d' % len(idList))

#
# ##########################################################################
#

class CContractEditor(CItemEditorBaseDialog, Ui_ContractEditorDialog):
    def tariffchanged(self, lt=None, rb=None):
        row = self.tblTariffs.currentIndex().row()
        self.modelTariffs.items()[row].modified = True
    def attachchanged(self, lt=None, rb=None):
        row = self.tblTariffs.currentIndex().row()
        self.modelTariffs.items()[row].modified = True
    def __init__(self,  parent):
        CItemEditorBaseDialog.__init__(self, parent, 'Contract')
        self.addObject('modelSpecification', CSpecificationModel(self))
        self.addModels('Tariffs', CTariffModel(self))
        self.addObject('modelTariffExpense', CTariffExpenseModel(self))
        self.addObject('modelTariffAttach',  CTariffAttachModel(self))
        self.addObject('modelContingent',    CContingentModel(self))
        self.addObject('modelAttributes',    CAttributesModel(self))
        self.addObject('modelTariffCoefficients',  CTariffCoefficientsModel(self))
        self.addObject('actPriceCalculator', QtGui.QAction(u'Пересчитать цены для выбранных строк', self))
        self.addObject('actMultiplyPriceByUET',     QtGui.QAction(u'Умножить цену на УЕТ для выбранных строк', self))
        self.addObject('actEnableCoefficients',  QtGui.QAction(u'Установить флажок "Разрешить коэффициенты"', self))
        self.addObject('actDisableCoefficients', QtGui.QAction(u'Снять флажок "Разрешить коэффициенты"', self))
        self.addObject('actFillExpenses', QtGui.QAction(u'Заполнить затраты для выбранных строк', self))
        self.addObject('actAddExpenses',  QtGui.QAction(u'Добавить статьи затрат услуг', self))
        self.addObject('actCopyContractTariffAttach', QtGui.QAction(u'Копировать прикрепления', self))
        self.addObject('actPastContractTariffAttach', QtGui.QAction(u'Вставить прикрепления в выбранные строки', self))

        self.setupUi(self)
        btn = self.buttonBox.button(QtGui.QDialogButtonBox.Apply)
        btn.clicked.connect(self.applySaveData)

        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setWindowState(Qt.WindowMaximized)
        self.setWindowTitleEx(u'Договор')

        self.cmbRecipient.setAddNone(True, u'не задано')
        self.cmbPayer.setAddNone(True, u'не задано')

        self.tblSpecification.setModel(self.modelSpecification)
        self.setModels(self.tblTariffs, self.modelTariffs, self.selectionModelTariffs)
        self.tblTariffExpense.setModel(self.modelTariffExpense)
        self.tblTariffAttach.setModel(self.modelTariffAttach)

        self.connect(self.modelTariffExpense, SIGNAL('dataChanged(const QModelIndex&, const QModelIndex&)'),
                               self.tariffchanged)
        self.connect(self.modelTariffAttach,
                               SIGNAL('dataChanged(const QModelIndex&, const QModelIndex&)'),
                               self.attachchanged)
        self.tblContingent.setModel(self.modelContingent)
        self.tblAttributes.setModel(self.modelAttributes)
        self.tblTariffCoefficients.setModel(self.modelTariffCoefficients)

        self.cmbFinance.setTable(rbFinance, True)
        self.cmbDefaultExportFormat.setTable(rbAccountExportFormat, True)
        self.cmbDefaultExportFormat.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContentsOnFirstShow)
        self.tblSpecification.addPopupDelRow()

        self.tblTariffs.createPopupMenu([self.actPriceCalculator, # тарифы сами по себе
                                        self.actMultiplyPriceByUET,
                                        '-',
                                         self.actEnableCoefficients,
                                         self.actDisableCoefficients,
                                         '-',
                                        self.actFillExpenses,    # статьи затрат
                                        '-',
#                                        self.actCopyContractTariffAttach, # прикрепление
                                        self.actPastContractTariffAttach,
                                        '-'
                                        ])
        self.tblTariffs.setActionsWithCheckers(
                                    (
                                     (self.actPriceCalculator, self.actPriceCalculatorChecker ),
                                     (self.actMultiplyPriceByUET, self.actFillExpensesChecker ),
                                     (self.actFillExpenses, self.actFillExpensesChecker ),
                                     (self.actPastContractTariffAttach, self.actPastContractTariffAttachChecker),
                                    )
                                             )

        self.tblTariffs.addPopupDuplicateCurrentRow()
        self.tblTariffs.addPopupSeparator()
        self.tblTariffs.addPopupSelectAllRow()
        self.tblTariffs.addPopupClearSelectionRow()
        self.tblTariffs.addPopupSeparator()
        self.tblTariffs.addPopupDelRow()

        self.tblTariffExpense.createPopupMenu([self.actAddExpenses])
        self.tblTariffExpense.addPopupDuplicateCurrentRow()

        self.tblTariffAttach.createPopupMenu([self.actCopyContractTariffAttach, '-'])
        self.tblTariffAttach.setActionsWithCheckers(
                                    (
                                     (self.actCopyContractTariffAttach, self.actCopyContractTariffAttachChecker),
                                    )
                                             )

        self.tblTariffAttach.addPopupSeparator()
        self.tblTariffAttach.addPopupDuplicateCurrentRow()
        self.tblTariffAttach.addPopupSeparator()
        self.tblTariffAttach.addPopupSelectAllRow()
        self.tblTariffAttach.addPopupClearSelectionRow()
        self.tblTariffAttach.addPopupSeparator()
        self.tblTariffAttach.addPopupDelRow()

        self.tblAttributes.addPopupDuplicateCurrentRow()
        self.tblAttributes.addPopupSeparator()
        self.tblAttributes.addPopupSelectAllRow()
        self.tblAttributes.addPopupClearSelectionRow()
        self.tblAttributes.addPopupSeparator()
        self.tblAttributes.addPopupDelRow()

        self.tblTariffCoefficients.addPopupDuplicateCurrentRow()
        self.tblTariffCoefficients.addPopupSeparator()
        self.tblTariffCoefficients.addMoveRow()
        self.tblTariffCoefficients.addPopupSeparator()
        self.tblTariffCoefficients.addPopupSelectAllRow()
        self.tblTariffCoefficients.addPopupClearSelectionRow()
        self.tblTariffCoefficients.addPopupSeparator()
        self.tblTariffCoefficients.addPopupDelRow()

        self.tblContingent.addPopupDuplicateCurrentRow()
        self.tblContingent.addPopupDelRow()

        self.cmbRecipient.setValue(QtGui.qApp.currentOrgId())

        self.setupDirtyCather((self.edtFilterDate,  self.chkFilterDate))
        self.tabWidget.setCurrentIndex(0)
        self.cmbFinance.setFocus(Qt.OtherFocusReason)
        self._contractTariffAttachRecordsForPast = []

        importProc, dbImport = self.getImportProc()
        self.btnImport.setEnabled(bool(importProc))
        self.btnExport.setEnabled(QtGui.qApp.defaultKLADR().startswith('23'))

        self.__expenceIdListCache = None

        self.tblSpecification.setCurrentRow(0)
        self.tblTariffs.setCurrentRow(0)
        self.tblContingent.setCurrentRow(0)
        self.tabWidget.removeTab(self.tabWidget.indexOf(self.tabContragent))


        self.cmbEventType.setTable('EventType')
        self.cmbEventType.setValue(0)
        self.cmbService.setIndex(0)
        self.cmbTariffType.addItem(u'Не задано')
        self.cmbTariffType.addItems(CTariff.tariffTypeNames)

        self.cmbCounter.setTable('rbCounter')

        customizePrintButton(self.btnPrint, 'contract')
        self.chkExposeDisciplineByOncology.setVisible(False)

        self.lastAddDialogDate = None
        self.edtBegDate.setDateRange(QDate(1900, 1, 1), QDate(7999, 12, 31))
        self.edtEndDate.setDateRange(QDate(1900, 1, 1), QDate(7999, 12, 31))

    def freezeHeadFields(self):
        self.cmbFinance.setDisabled(True)
        self.edtNumber.setDisabled(True)
        self.edtGrouping.setDisabled(True)
        self.edtDate.setDisabled(True)
        self.edtResolution.setDisabled(True)
        self.edtBegDate.setDisabled(True)
        self.edtEndDate.setDisabled(True)
        self.cmbRecipient.setDisabled(True)
        self.btnSelectRecipient.setDisabled(True)
        self.tabWidget.setCurrentIndex(1)
        
    def getFilteredTariffItems(self):
        items = self.modelTariffs.items()
        filtered = []
        for i in xrange(len(items)):
            if not self.tblTariffs.isRowHidden(i):
                filtered.append(items[i])
        return filtered

    def setRecord(self, record):
        CItemEditorBaseDialog.setRecord(self, record)
        setRBComboBoxValue(self.cmbFinance,         record, 'finance_id')
        setLineEditValue(self.edtFinanceSubtypeCode,record, 'financeSubtypeCode')
        setLineEditValue(self.edtNumber,            record, 'number')
        setDateEditValue(self.edtDate,              record, 'date')
        setRBComboBoxValue(self.cmbRecipient,       record, 'recipient_id')
        setRBComboBoxValue(self.cmbRecipientAccount,record, 'recipientAccount_id')
        setLineEditValue(self.edtRecipientKBK,      record, 'recipientKBK')
        setRBComboBoxValue(self.cmbPayer,           record, 'payer_id')
        setRBComboBoxValue(self.cmbPayerAccount,    record, 'payerAccount_id')
        setLineEditValue(self.edtPayerKBK,          record, 'payerKBK')
        setDateEditValue(self.edtBegDate,           record, 'begDate')
        setDateEditValue(self.edtEndDate,           record, 'endDate')
        setLineEditValue(self.edtGrouping,          record, 'grouping')
        setLineEditValue(self.edtResolution,        record, 'resolution')
        setTextEditValue(self.edtNote,              record, 'note')
        setRBComboBoxValue(self.cmbDefaultExportFormat, record, 'format_id')
        setComboBoxValue(self.cmbDateOfVisitExposition,  record, 'dateOfVisitExposition')
        setComboBoxValue(self.cmbVisitExposition,        record, 'visitExposition')
        setComboBoxValue(self.cmbDateOfActionExposition, record, 'dateOfActionExposition')
        setComboBoxValue(self.cmbActionExposition,       record, 'actionExposition')
        setComboBoxValue(self.cmbDateOfCsgExposition,    record, 'dateOfCsgExposition')
        setCheckBoxValue(self.chkDisableInAccounts,      record, 'disableInAccounts')
        setCheckBoxValue(self.chkExposeExternalServices, record, 'exposeExternalServices')
        setCheckBoxValue(self.chkExposeIfContinuedEventFinished, record, 'exposeIfContinuedEventFinished')
        setCheckBoxValue(self.chkExposeByLastEventContract,      record, 'exposeByLastEventContract')
        setCheckBoxValue(self.chkOnlyEventsPassedExpertise, record, 'isOnlyEventsPassedExpertise')
        setCheckBoxValue(self.chkExposeByAccountType, record, 'isExposeByAccountType')
        setComboBoxValue(self.cmbPayType,  record, 'payType')
        setRBComboBoxValue(self.cmbCounter, record, 'counter_id')
        exposeDiscipline = forceInt(record.value('exposeDiscipline'))
        (
          exposeBySourceOrg,
          exposeByOncology,
          exposeByBatch,
          exposeByEvent,
          exposeByMonth,
          exposeByClient,
          exposeByInsurer,
        )                 = unpackExposeDiscipline(exposeDiscipline)
        self.chkExposeDisciplineByMonth.setChecked(exposeByMonth)
        self.cmbExposeDisciplineByInsurer.setCurrentIndex(exposeByInsurer)
        self.chkExposeDisciplineByBatch.setChecked(exposeByBatch)
        self.chkExposeDisciplineBySourceOrg.setChecked(exposeBySourceOrg)
        self.chkExposeDisciplineByClient.setChecked(exposeByClient)
        self.chkExposeDisciplineByEvent.setChecked(exposeByEvent)
        self.chkExposeDisciplineByOncology.setChecked(exposeByOncology)
        priceListId = forceRef(record.value('priceList_id'))
        contractId = self.itemId()
        if priceListId:
            self.cmbPriceList.setValue(priceListId)
        else:
            if contractId:
                db = QtGui.qApp.db
                tableContract = db.table('Contract')
                priceListRecord = db.getRecordEx(tableContract, [tableContract['id']], [tableContract['deleted'].eq(0), tableContract['priceList_id'].eq(contractId)])
                dependantId = forceRef(priceListRecord.value('id')) if priceListRecord else None
                if dependantId:
                    self.cmbPriceList.setValue(contractId)
        priceListExternalId = forceRef(record.value('priceListExternal_id'))
        self.cmbPriceListExternal.setValue(priceListExternalId)
        setDoubleBoxValue(self.edtCoefficient, record, 'coefficient')
        setDoubleBoxValue(self.edtCoefficientEx, record, 'coefficientEx')
        setDoubleBoxValue(self.edtCoefficientEx2, record, 'coefficientEx2')
        setDoubleBoxValue(self.edtLimitExceeding, record, 'limitExceeding')
        setDoubleBoxValue(self.edtLimitOfFinancing, record, 'limitOfFinancing')
        #setDoubleBoxValue(self.edtActualAmount, record, 'actualAmount')
        setLineEditValue(self.edtOrgCategory,  record,  'orgCategory')
        setDoubleBoxValue(self.edtRegionalTariffRegulationFactor, record,  'regionalTariffRegulationFactor')
        setSpinBoxValue(self.edtExpensePrecision, record, 'expensePrecision')
        setSpinBoxValue(self.edtPricePrecision, record, 'pricePrecision')
        setSpinBoxValue(self.edtTariffCoeffValuePrecision, record, 'valueTariffCoeffPrecision')
        self.modelTariffExpense.setPrecision(self.edtExpensePrecision.value())
        self.modelTariffs.setPricePrecision(self.edtPricePrecision.value())
        self.modelTariffCoefficients.setValuePrecision(self.edtTariffCoeffValuePrecision.value())
        self.modelSpecification.loadItems(contractId)
        self.modelTariffs.loadItems(contractId)
        self.modelContingent.loadItems(contractId)
        self.modelAttributes.loadItems(contractId)
        self.modelTariffCoefficients.loadItems(contractId)
        self.tblSpecification.setCurrentRow(0)
        self.tblTariffs.setCurrentRow(0)
        self.tblContingent.setCurrentRow(0)
        self.edtFilterDate.setDate(self.edtBegDate.date())
        model = self.tblTariffs.model()
        self.lblTariffStatus.setText (u'Кол-во записей: %s' % model.rowCount())

    def getRecord(self):
        record = CItemEditorBaseDialog.getRecord(self)
        getRBComboBoxValue(self.cmbFinance,         record, 'finance_id')
        getLineEditValue(self.edtFinanceSubtypeCode,record, 'financeSubtypeCode')
        getLineEditValue(self.edtNumber,            record, 'number')
        getDateEditValue(self.edtDate,              record, 'date')
        getRBComboBoxValue(self.cmbRecipient,       record, 'recipient_id')
        getRBComboBoxValue(self.cmbRecipientAccount,record, 'recipientAccount_id')
        getLineEditValue(self.edtRecipientKBK,      record, 'recipientKBK')
        getRBComboBoxValue(self.cmbPayer,           record, 'payer_id')
        getRBComboBoxValue(self.cmbPayerAccount,    record, 'payerAccount_id')
        getLineEditValue(self.edtPayerKBK,          record, 'payerKBK')
        getDateEditValue(self.edtBegDate,           record, 'begDate')
        getDateEditValue(self.edtEndDate,           record, 'endDate')
        getLineEditValue(self.edtGrouping,          record, 'grouping')
        getLineEditValue(self.edtResolution,        record, 'resolution')
        getTextEditValue(self.edtNote,              record, 'note')
        getRBComboBoxValue(self.cmbDefaultExportFormat, record, 'format_id')
#        getCheckBoxValue(self.chkExposeUnfinishedEventVisits, record, 'exposeUnfinishedEventVisits')
#        getCheckBoxValue(self.chkExposeUnfinishedEventActions, record, 'exposeUnfinishedEventActions')
        getComboBoxValue(self.cmbDateOfVisitExposition,  record, 'dateOfVisitExposition')
        getComboBoxValue(self.cmbVisitExposition,        record, 'visitExposition')
        getComboBoxValue(self.cmbDateOfActionExposition, record, 'dateOfActionExposition')
        getComboBoxValue(self.cmbActionExposition,       record, 'actionExposition')
        getComboBoxValue(self.cmbDateOfCsgExposition,    record, 'dateOfCsgExposition')
        getCheckBoxValue(self.chkOnlyEventsPassedExpertise, record, 'isOnlyEventsPassedExpertise')
        getCheckBoxValue(self.chkExposeByAccountType, record, 'isExposeByAccountType')

        getComboBoxValue(self.cmbPayType,  record, 'payType')
        getRBComboBoxValue(self.cmbCounter, record, 'counter_id')
        getCheckBoxValue(self.chkDisableInAccounts,      record, 'disableInAccounts')
        getCheckBoxValue(self.chkExposeExternalServices, record, 'exposeExternalServices')
        getCheckBoxValue(self.chkExposeIfContinuedEventFinished, record, 'exposeIfContinuedEventFinished')
        getCheckBoxValue(self.chkExposeByLastEventContract,      record, 'exposeByLastEventContract')
        exposeDiscipline = packExposeDiscipline( self.chkExposeDisciplineBySourceOrg.isChecked(),
                                                 self.chkExposeDisciplineByOncology.isChecked(),
                                                 self.chkExposeDisciplineByBatch.isChecked(),
                                                 self.chkExposeDisciplineByEvent.isChecked(),
                                                 self.chkExposeDisciplineByMonth.isChecked(),
                                                 self.chkExposeDisciplineByClient.isChecked(),
                                                 self.cmbExposeDisciplineByInsurer.currentIndex()
                                               )
        record.setValue('exposeDiscipline', toVariant(exposeDiscipline))
        getRBComboBoxValue(self.cmbPriceList, record, 'priceList_id')
        getRBComboBoxValue(self.cmbPriceListExternal, record, 'priceListExternal_id')
#        record.setValue('priceList_id', toVariant(self.cmbPriceList.value()))
        getDoubleBoxValue(self.edtCoefficient, record, 'coefficient')
        getDoubleBoxValue(self.edtCoefficientEx, record, 'coefficientEx')
        getDoubleBoxValue(self.edtCoefficientEx2, record, 'coefficientEx2')
        getDoubleBoxValue(self.edtLimitExceeding, record, 'limitExceeding')
        getDoubleBoxValue(self.edtLimitOfFinancing, record, 'limitOfFinancing')
        #getDoubleBoxValue(self.edtActualAmount, record, 'actualAmount')
        getLineEditValue(self.edtOrgCategory,  record,  'orgCategory')
        getDoubleBoxValue(self.edtRegionalTariffRegulationFactor, record,  'regionalTariffRegulationFactor')
        getSpinBoxValue(self.edtExpensePrecision, record, 'expensePrecision')
        getSpinBoxValue(self.edtPricePrecision, record, 'pricePrecision')
        getSpinBoxValue(self.edtTariffCoeffValuePrecision, record, 'valueTariffCoeffPrecision')
        return record


    def saveInternals(self, contractId):
        self.modelSpecification.saveItems(contractId)
        self.modelTariffs.saveItems(contractId)
        self.modelContingent.saveItems(contractId)
        self.modelAttributes.saveItems(contractId)
        self.modelTariffCoefficients.saveItems(contractId)


    def checkDataEntered(self):
        result = True
        result = result and (self.cmbFinance.value()          or  self.checkInputMessage(u'тип финансирования', False, self.cmbFinance))
        result = result and (forceStringEx(self.edtNumber.text()) or  self.checkInputMessage(u'номер', False, self.edtNumber))
        result = result and (self.edtDate.date().isValid()    or self.checkInputMessage(u'дату', False, self.edtDate))
        result = result and (self.cmbRecipient.value()        or self.checkInputMessage(u'получателя', False, self.cmbRecipient))
        result = result and (self.cmbRecipientAccount.value() or self.checkInputMessage(u'рассчетный счет получателя', False, self.cmbRecipientAccount))
        result = result and (self.cmbPayer.value()            or self.checkInputMessage(u'плательщика', False, self.cmbPayer))
        result = result and (self.cmbPayerAccount.value()     or  self.checkInputMessage(u'рассчетный счет плательщика', False, self.cmbPayerAccount))
        result = result and (forceStringEx(self.edtGrouping.text())   or self.checkInputMessage(u'группу договоров', True, self.edtGrouping))
        result = result and (forceStringEx(self.edtResolution.text()) or self.checkInputMessage(u'основание', True, self.edtResolution))
        result = result and self.checkExpensesPercents()
        return result


    def checkExpensesPercents(self):
        bugRow = self.modelTariffs.findRowWithBugInExpensesPercents()
        if bugRow>=0:
            self.tblTariffs.setCurrentRow(bugRow)
            return self.checkValueMessage(u'Сумма процентов больше 100', False, self.tblTariffExpense, 0, 1)
        return True

    def updateDateDependentFilters(self):
        begDate = self.edtBegDate.date()
        endDate = self.edtEndDate.date()
        self.modelTariffs.updateDateDependentFilters(begDate, endDate)

    def updateRecipientInfo(self):
        id = self.cmbRecipient.value()
        orgInfo = getOrganisationInfo(id)
        self.edtRecipientINN.setText(orgInfo.get('INN', ''))
        self.edtRecipientOGRN.setText(orgInfo.get('OGRN', ''))
        self.cmbRecipientAccount.setOrgId(id)


    def updateRecipientAccountInfo(self):
        id = self.cmbRecipientAccount.value()
        accountInfo = getAccountInfo(id)
        self.edtRecipientBank.setText(accountInfo.get('shortBankName', ''))


    def updatePayerInfo(self):
        id = self.cmbPayer.value()
        orgInfo = getOrganisationInfo(id)
        self.edtPayerINN.setText(orgInfo.get('INN', ''))
        self.edtPayerOGRN.setText(orgInfo.get('OGRN', ''))
        self.cmbPayerAccount.setOrgId(id)


    def updatePayerAccountInfo(self):
        id = self.cmbPayerAccount.value()
        accountInfo = getAccountInfo(id)
        self.edtPayerBank.setText(accountInfo.get('shortBankName', ''))




    def getExpensesIdList(self):
        if self.__expenceIdListCache is None:
            db = QtGui.qApp.db
            self.__expenceIdListCache = db.getIdList('rbExpenseServiceItem', order='code')
        return self.__expenceIdListCache


    def setupTariffDependedTables(self, row):
        items = self.modelTariffs.items()
        if 0<=row<len(items):
            self.tblTariffExpense.setEnabled(True)
            self.tblTariffAttach.setEnabled(True)
            item = self.modelTariffs.items()[row]
            self.modelTariffExpense.setParentItem(item)
            self.modelTariffExpense.setItems(self.modelTariffs.tariffExpense(row))
            self.modelTariffAttach.setItems(self.modelTariffs.tariffAttach(row))
        else:
            self.modelTariffExpense.setItems([])
            self.modelTariffAttach.setItems([])
            self.tblTariffExpense.setEnabled(False)
            self.tblTariffAttach.setEnabled(False)


    def afterMassiveTariffOperation(self):
        index = self.tblTariffs.currentIndex()
        self.tblTariffs.clearSelection()
        self.setupTariffDependedTables(index.row())
        self.tblTariffs.setCurrentIndex(index)


    def getPriceListId(self, contractId):
        if contractId:
            db = QtGui.qApp.db
            table = db.table('Contract')
            record = db.getRecordEx(table, [table['priceList_id']], [table['deleted'].eq(0), table['priceList_id'].eq(contractId)])
            return forceRef(record.value('priceList_id')) if record else None
        return None


    def getImportProc(self):
        dbImport = False
        importProc = None
        defaultKLADR = QtGui.qApp.defaultKLADR()
        if defaultKLADR.startswith('23'):
            importProc = ImportTariffsR23
        elif defaultKLADR.startswith('29'):
            importProc = ImportTariffsR29
        elif defaultKLADR.startswith('47'):
            importProc = ImportTariffsR47
        elif defaultKLADR.startswith('50'):
            dbImport = True
            importProc = ImportTariffsR77
        elif defaultKLADR.startswith('51'):
            importProc = importTariffsR51
        elif defaultKLADR.startswith('61'):
            importProc = importTariffsR61
        elif defaultKLADR.startswith('67'):
            importProc = ImportTariffsR67
        elif defaultKLADR.startswith('77'):
            dbImport = True
            importProc = ImportTariffsR77
        elif defaultKLADR.startswith('78'):
            if self.cmbDefaultExportFormat.code() == '6':
                importProc = ImportTariffsINFIS
            else:
                importProc = ImportTariffs
        return importProc, dbImport
    
    
    def applySaveData(self):
        if self.saveData():
            QtGui.QMessageBox.information( None, 
                                    u'Всё хорошо!',
                                    u'Сохранение данных выполнено.')
        else:
            QtGui.QMessageBox.information( None, 
                                    u'Ошибка!',
                                    u'Сохранение данных не выполнено.')


    @pyqtSignature('QDate')
    def on_edtBegDate_dateChanged(self, date):
        self.updateDateDependentFilters()


    @pyqtSignature('QDate')
    def on_edtEndDate_dateChanged(self, date):
        self.updateDateDependentFilters()


    @pyqtSignature('int')
    def on_cmbRecipient_currentIndexChanged(self, index):
        self.updateRecipientInfo()


    @pyqtSignature('')
    def on_modelTariffs_priceEdited(self):
        self.modelTariffExpense.reset()


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelTariffs_currentChanged(self, current, previous):
        self.setupTariffDependedTables(current.row())


    @pyqtSignature('')
    def on_btnSelectRecipient_clicked(self):
        orgId = selectOrganisation(self, self.cmbRecipient.value(), False)
        self.cmbRecipient.updateModel()
        self.cmbRecipientAccount.updateModel()
        if orgId:
          self.setIsDirty()
          self.cmbRecipient.setValue(orgId)

    @pyqtSignature('')
    def on_btnApplyFilter_clicked(self):
        self.modelTariffs.applyFilter(self)
        
    @pyqtSignature('int')
    def on_chkFilterDate_stateChanged(self,  val):
        if val==0:
            self.edtFilterDate.setEnabled(False)
        else:
            self.edtFilterDate.setEnabled(True)
        self.modelTariffs.applyFilter(self)
        
        
    @pyqtSignature('')
    def on_btnCalculation_clicked(self):
        self.edtActualAmount.setValue(0)
        contractId = self.itemId()
        if contractId:
            sumAction = 0
            sumItem = 0
            db = QtGui.qApp.db
            tableAction = db.table('Action')
            tableAccountItem = db.table('Account_Item')
        #  payStatus != 0
            cond = [tableAction['deleted'].eq(0),
                    tableAccountItem['deleted'].eq(0),
                    tableAction['contract_id'].eq(contractId),
                    tableAction['payStatus'].ne(0),
                    tableAccountItem['refuseType_id'].isNull()
                    ]
            table = tableAction.innerJoin(tableAccountItem, tableAction['id'].eq(tableAccountItem['action_id']))
            records = db.getRecordListGroupBy(table, u'SUM(Account_Item.sum) AS sumAction', cond, u'Action.contract_id')
            if records:
                record = records[0]
                sumAction += forceDouble(record.value('sumAction'))
        #  payStatus == 0
            tableActionTypeService = db.table('ActionType_Service')
            tableContractTariff = db.table('Contract_Tariff')
            tableEvent = db.table('Event')
            tableA = db.table('Action').alias('A')
            cols = u'''SUM(IF(A.amount > Contract_Tariff.amount AND Contract_Tariff.amount != 0, Contract_Tariff.amount * Contract_Tariff.price,
            A.amount * Contract_Tariff.price))'''
            cond = [tableContractTariff['deleted'].eq(0),
                    tableContractTariff['master_id'].eq(contractId),
                    tableContractTariff['tariffType'].eq(2)
                    ]
            cond.append(u'A.id = Action.id')
            cond.append(u'''ActionType_Service.`service_id`=(SELECT ATS.`service_id`
                            FROM ActionType_Service AS ATS
                            WHERE ATS.`master_id`=ActionType_Service.`master_id`
                            AND (ATS.`finance_id` IS NULL OR A.`finance_id`=ATS.`finance_id`)
                            ORDER BY ATS.`finance_id` DESC
                            LIMIT 1)''')
            table = tableA.innerJoin(tableActionTypeService, tableA['actionType_id'].eq(tableActionTypeService['master_id']))
            table = table.innerJoin(tableContractTariff, tableActionTypeService['service_id'].eq(tableContractTariff['service_id']))
            stmt = db.selectStmtGroupBy(table, cols, cond, u'A.contract_id')
            condQuery = [tableAction['deleted'].eq(0),
                        tableEvent['deleted'].eq(0),
                        tableAction['contract_id'].eq(contractId),
                        tableAction['payStatus'].eq(0)
                        ]
            tableQuery = tableEvent.innerJoin(tableAction, tableEvent['id'].eq(tableAction['event_id']))
            colsQuery = [u'(%s) AS sumItem'%stmt,
                         tableAction['contract_id']
                         ]
            records = db.getRecordList(tableQuery, colsQuery, condQuery)
            for newRecord in records:
                sumItem += forceDouble(newRecord.value('sumItem'))
            self.edtActualAmount.setValue(sumAction + sumItem)


    @pyqtSignature('int')
    def on_cmbRecipientAccount_currentIndexChanged(self, index):
        self.updateRecipientAccountInfo()


    @pyqtSignature('int')
    def on_cmbPayer_currentIndexChanged(self, index):
        self.updatePayerInfo()


    @pyqtSignature('')
    def on_btnSelectPayer_clicked(self):
        orgId = selectOrganisation(self, self.cmbPayer.value(), False)
        self.cmbPayer.updateModel()
        self.cmbPayerAccount.updateModel()
        if orgId:
            self.setIsDirty()
            self.cmbPayer.setValue(orgId)


    @pyqtSignature('int')
    def on_cmbPayerAccount_currentIndexChanged(self, index):
        self.updatePayerAccountInfo()
        
    @pyqtSignature('')
    def on_btnAdd_clicked(self):
        dialog = CTariffAddDialog(self)
        if dialog.exec_():
            for record in dialog.newRecords:
                record.setValue('id', None)    
                self.modelTariffs._items.append(record)
            updatedList = []
            for item in self.modelTariffs.items():
                if forceRef(item.value('id')) in dialog.updatedRecords.keys():
                    updatedList.append(dialog.updatedRecords[forceRef(item.value('id'))])
                else:
                    updatedList.append(item)
            self.modelTariffs.setItems(updatedList)
            self.modelTariffs.reset()
            self.modelTariffs.applyFilter(self)
        
        
    @pyqtSignature('')
    def on_btnImport_clicked(self):
        importProc, dbImport = self.getImportProc()
        if importProc:
            if dbImport:
                importProc(self, self.itemId())
                self.modelTariffs.loadItems(self.itemId())
            else:
                tariffExpenseItems = [self.modelTariffs.tariffExpense(x) for x in range(len(self.modelTariffs.items()))]
                ok, tariffList, expenseItems, coefficientItems = importProc(self, self.itemId(),
                                                          self.edtBegDate.date(),
                                                          self.edtEndDate.date(),
                                                          self.modelTariffs.items(),
                                                          tariffExpenseItems,
                                                          self.modelTariffCoefficients.items())
                if ok:
                    self.modelTariffs.setItems(tariffList)
                    self.modelTariffs.setAllExpenses(expenseItems)
                    self.modelTariffs.reset()
                    self.tblTariffs.setCurrentRow(0)
                    self.modelTariffCoefficients.setItems(coefficientItems)
                    self.modelTariffCoefficients.reset()
                    self.tblTariffCoefficients.setCurrentRow(0)


    @pyqtSignature('')
    def on_btnImportXML_clicked(self):
        tariffExpenseItems = [self.modelTariffs.tariffExpense(x) for x in range(len(self.modelTariffs.items()))]
        items, expenseItems = ImportTariffsXML(self, self.modelTariffs.items(), tariffExpenseItems)
        self.modelTariffs.setItems(items)
        self.modelTariffs.setAllExpenses(expenseItems)
        self.modelTariffs.reset()
        self.tblTariffs.setCurrentRow(0)


    @pyqtSignature('')
    def on_btnImportCSV_clicked(self):
        items = ImportTariffsCSV(self, self.modelTariffs.items())
        if items:
            self.modelTariffs.setItems(items)
            self.modelTariffs.reset()
            self.tblTariffs.setCurrentRow(0)

    @pyqtSignature('')
    def on_btnExportXML_clicked(self):
        expensesDict = {}
        items = self.modelTariffs.items()
#        filtered = []
#        filteredIdx = 0
        for i in xrange(len(items)):
            expensesDict[i] = self.modelTariffs.tariffExpense(i)
        ExportTariffsXML(self, items, expensesDict)


    @pyqtSignature('')
    def on_btnExportXLS_clicked(self):
        items = self.getFilteredTariffItems()
        ExportTariffsXLS(self, items)


    @pyqtSignature('')
    def on_btnExport_clicked(self):
        if QtGui.qApp.defaultKLADR().startswith('23'):
            tariffList = []
            items = self.modelTariffs.items()
            
            filter_date_valid = None
            if self.chkFilterDate.isChecked() and self.edtFilterDate.date().isValid():
                filter_date_valid = self.edtFilterDate.date()
                
            for i in xrange(len(items)):
                if not self.tblTariffs.isRowHidden(i):
                    tariffList.append(self.modelTariffs.items()[i])
            ExportTariffsR23(self, tariffList, filter_date_valid)


    @pyqtSignature('int')
    def on_btnPrint_printByTemplate(self,  templateId):
        context = CInfoContext()
        contract = context.getInstance(CContractInfo, self.itemId())
        notHiddenTariffs = context.getInstance(CTariffInfoList, contract.id, tuple(
            map(lambda item: forceRef(item.value('id')), self.getFilteredTariffItems())))
        data = {
                 'contract': contract,
                 'notHiddenTariffs': notHiddenTariffs,
               }
        applyTemplate(self, templateId, data)

    @pyqtSignature('QString')
    def on_cmbPriceList_editTextChanged(self, index):
        contractId = self.itemId()
        priceListId = self.cmbPriceList.value()
        if not priceListId:
            priceListId = self.getPriceListId(contractId)
            if priceListId and priceListId == contractId:
                self.cmbPriceList.setValue(priceListId)


    @pyqtSignature('')
    def on_actPriceCalculator_triggered(self):
        rows = self.tblTariffs.getSelectedRows()
        setupDialog = CPriceCoefficientEditor(self)
        setupDialog.prepare(len(rows))
        if setupDialog.exec_():
            coefficients = setupDialog.params()
            for coefficient, edt in zip(coefficients, (self.edtCoefficient, self.edtCoefficientEx, self.edtCoefficientEx2)):
                if coefficient is not None:
                    edt.setValue(coefficient)
            if any(coefficient is not None for coefficient in coefficients) and rows:
                QtGui.qApp.callWithWaitCursor(self, self.updatePricesInSelectedRecords, coefficients, rows)
            self.afterMassiveTariffOperation()


    def actPriceCalculatorChecker(self):
        return QtGui.qApp.userHasRight(urAccessPriceCalculate) and bool(self.tblTariffs.getSelectedRows())


    @pyqtSignature('')
    def on_actMultiplyPriceByUET_triggered(self):
        rows = self.tblTariffs.getSelectedRows()
        isDirty = False
        for row in rows:
            item = self.modelTariffs.items()[row]
            uet = forceDouble(item.value('uet'))
            if uet > 0.0:
                isDirty = True
                price = forceDouble(item.value('price'))
                price = roundMath(price*uet, self.edtPricePrecision.value())
                item.setValue('price', toVariant(price))
                self.modelTariffs.emitCellChanged(row, item.indexOf('price'))
                self.modelTariffs.items()[row].modified = True

        if isDirty:
            self.modelTariffs.emitAllChanged()
        self.afterMassiveTariffOperation()


    @pyqtSignature('')
    def on_actEnableCoefficients_triggered(self):
        rows = self.tblTariffs.getSelectedRows()
        for row in rows:
            self.modelTariffs.setValue(row, 'enableCoefficients', True)


    @pyqtSignature('')
    def on_actDisableCoefficients_triggered(self):
        rows = self.tblTariffs.getSelectedRows()
        for row in rows:
            self.modelTariffs.setValue(row, 'enableCoefficients', False)


    @pyqtSignature('')
    def on_actFillExpenses_triggered(self):
        rows = self.tblTariffs.getSelectedRows()
        if rows:
            setupDialog = CIntroducePercentDialog(self)
            setupDialog.prepare(len(rows))
            expenseIdAndPercentList = setupDialog.selectExpencesAndPercents()
            if expenseIdAndPercentList:
                for row in rows:
                    self.modelTariffs.setExpenses(row, expenseIdAndPercentList)
                self.afterMassiveTariffOperation()


    def actFillExpensesChecker(self):
        return bool(self.tblTariffs.getSelectedRows())


    @pyqtSignature('')
    def on_actAddExpenses_triggered(self):
        row = self.tblTariffs.currentIndex().row()
        self.modelTariffs.addExpenses(row, self.getExpensesIdList())
        self.setupTariffDependedTables(row)


    @pyqtSignature('')
    def on_actCopyContractTariffAttach_triggered(self):
        self._contractTariffAttachRecordsForPast = []
        recordList = [self.modelTariffAttach.items()[row] for row in self.tblTariffAttach.getSelectedRows()]
        for record in recordList:
            if record:
                record = QtSql.QSqlRecord(record)
                record.setNull('id')
                record.setNull('master_id')
                self._contractTariffAttachRecordsForPast.append(record)


    def actCopyContractTariffAttachChecker(self):
        return bool(self.tblTariffAttach.getSelectedRows())


    @pyqtSignature('')
    def on_actPastContractTariffAttach_triggered(self):
        for row in self.tblTariffs.getSelectedRows():
            tariffAttach = self.modelTariffs.tariffAttach(row)
            for record in self._contractTariffAttachRecordsForPast:
                tariffAttach.append(QtSql.QSqlRecord(record))
        self.afterMassiveTariffOperation()
        self.modelTariffAttach.reset()


    @pyqtSignature('int')
    def on_edtExpensePrecision_valueChanged(self, value):
        self.modelTariffExpense.setPrecision(value)


    @pyqtSignature('int')
    def on_edtPricePrecision_valueChanged(self, value):
        self.modelTariffs.setPricePrecision(value)


    @pyqtSignature('int')
    def on_edtTariffCoeffValuePrecision_valueChanged(self, value):
        self.modelTariffCoefficients.setValuePrecision(value)


    def actPastContractTariffAttachChecker(self):
        return bool(self.tblTariffs.getSelectedRows()) and bool(len(self._contractTariffAttachRecordsForPast))


    def updatePricesInSelectedRecords(self, coefficients, rows):
        for row in rows:
            record = self.modelTariffs.items()[row]
            CPriceListDialog.updateTariffToCoefficient(record, coefficients)
        self.modelTariffs.emitAllChanged()
        self.tblTariffs.clearSelection()
        self.tblTariffs.setCurrentRow(0)


    def getTariffFilterParams(self):
        params = {}
        params['eventType_id'] = self.cmbEventType.value()
        params['tariffType'] = self.cmbTariffType.currentIndex()
        params['tariffBatch'] = self.edtTariffBatch.text()
        params['service_id'] = self.cmbService.value()
        params['master_id'] = self.itemId()
        return params


    @pyqtSignature('int')
    def on_cmbEventType_currentIndexChanged(self, index):
        self.modelTariffs.applyFilter(self, params = self.getTariffFilterParams())


    @pyqtSignature('int')
    def on_cmbService_currentIndexChanged(self, index):
        self.modelTariffs.applyFilter(self, params = self.getTariffFilterParams())


    @pyqtSignature('int')
    def on_cmbTariffType_currentIndexChanged(self, index):
        self.modelTariffs.applyFilter(self, params = self.getTariffFilterParams())


    @pyqtSignature('QString')
    def on_edtTariffBatch_textChanged(self, text):
        self.modelTariffs.applyFilter(self, params = self.getTariffFilterParams())


#
# ###################################################################
#


class CContractMultipleEditor(CDialogBase, Ui_ContractMultipleEditorDialog):
    def __init__(self, parent):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        self.cmbRecipient.setAddNone(True, u'не задано')
        self.cmbPayer.setAddNone(True, u'не задано')
        self.setWindowTitle(u'Договор (несколько)')
        self._idList = []


    def load(self, itemIdList):
        self._idList = itemIdList
        record = QtGui.qApp.db.getRecord('Contract', '*', self._idList[0])
        setDateEditValue(  self.edtDate,      record, 'date')
        setDateEditValue(  self.edtBegDate,   record, 'begDate')
        setDateEditValue(  self.edtEndDate,   record, 'endDate')
        setRBComboBoxValue(self.cmbPriceList, record, 'priceList_id')
        setRBComboBoxValue(self.cmbPayer,     record, 'payer_id')
        setRBComboBoxValue(self.cmbRecipient, record, 'recipient_id')


    def itemIdList(self):
        return self._idList


    def accept(self):
        self._saveData()
        CDialogBase.accept(self)


    def _saveData(self):
        db = QtGui.qApp.db
        db.transaction()
        try:
            for id in self._idList:
                record = db.getRecord('Contract', '*', id)
                getDateEditValue(  self.edtDate,      record, 'date')
                getDateEditValue(  self.edtBegDate,   record, 'begDate')
                getDateEditValue(  self.edtEndDate,   record, 'endDate')
                getRBComboBoxValue(self.cmbPriceList, record, 'priceList_id')
                getRBComboBoxValue(self.cmbPayer,     record, 'payer_id')
                getRBComboBoxValue(self.cmbRecipient, record, 'recipient_id')
                record.setValue('modifyDatetime', QDateTime.currentDateTime())
                record.setValue('modifyPerson_id', QtGui.qApp.userId)
                db.updateRecord('Contract', record)
            db.commit()
        except:
            db.rollback()
            QtGui.qApp.logCurrentException()
            raise


#
# ###################################################################
#


class CSpecificationModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'Contract_Specification', 'id', 'master_id', parent)
        self.addCol(CRBInDocTableCol(u'Событие',  'eventType_id',  30, 'EventType', filter='deleted=0'))


#
# ###################################################################
#


class CEventResultInDocTableCol(CRBInDocTableCol):

    def setEditorData(self, editor, value, record):
        from Events.Utils import getEventPurposeId

        eventTypeId = forceRef(record.value('eventType_id'))
        eventPurposeId = getEventPurposeId(eventTypeId)
        editor.setFilter('eventPurpose_id=%d' % (eventPurposeId or 0) )
        editor.setValue(forceInt(value))


    def getEditorData(self, editor):
        return toVariant(editor.value())



class CTariffModel(CInDocTableModel):

    __pyqtSignals__ = ('priceEdited()',
                      )
    def sortData(self, column, ascending):
        col = self._cols[column]
        self._items.sort(key=lambda(item): col.toSortString(item.value(col.fieldName()), item), reverse=not ascending)
        self.applyFilter(self.parent)
        self.emitRowsChanged(0, len(self._items)-1)
        
    def applyFilter(self, parent, params = {}):
        filter_kusl = unicode(trim(forceString(parent.edtCode.text())).lower())
        filter_kusl_valid = filter_kusl != ''
        filter_date = parent.edtFilterDate.date()
        filter_date_valid = parent.chkFilterDate.isChecked() and parent.edtFilterDate.date().isValid()
        first_matched_row = -1
        count = 0
        kuslIdList = []
        if filter_kusl_valid:
            db = QtGui.qApp.db
            tableService = db.table("rbService")
            kuslIdList = db.getIdList(tableService, 'id', tableService['infis'].like(filter_kusl + '%'), 'id')
        for row in xrange(len(self._items)):
            item = self._items[row]
            match = True
            if filter_kusl_valid:
                kuslId = item.value('service_id').toInt()[0]
                match = match and (kuslId in kuslIdList)
            if filter_date_valid:
                data = QDate.fromString(self.index(row, self.getColIndex('endDate')).data().toString(), "dd.MM.yyyy") #9
                dataStart = QDate.fromString(self.index(row, self.getColIndex('begDate')).data().toString(), "dd.MM.yyyy") #8
                match = match and (not data or data >= filter_date) and dataStart <= filter_date  
            if params.get('eventType_id', None):
                match = match and forceInt(item.value('eventType_id')) == params['eventType_id']
            if params.get('tariffType', None):
                match = match and forceInt(item.value('tariffType')) == params['tariffType'] - 1
            if params.get('tariffBatch', None):
                match = match and params['tariffBatch'] in forceString(item.value('tariffBatch'))
            if params.get('service_id', None):
                match = match and forceInt(item.value('service_id')) == params['service_id']
                
            parent.tblTariffs.setRowHidden(row, not match)
            if match:
                count = count + 1
            if first_matched_row == -1 and match:
                first_matched_row = row
        parent.tblTariffs.setCurrentRow(first_matched_row)
        parent.lblTariffStatus.setText(u'Кол-во записей: %s' % count)
        
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'Contract_Tariff', 'id', 'master_id', parent)

        self.parent = parent  # wtf? скрывать Qt-шный parent - это плохая затея
        self.addCol(CBoolInDocTableCol(u'Внешний',          'isExternal', 5))
        self.addCol(CRBInDocTableCol(u'Событие',            'eventType_id',  30, 'EventType', filter='deleted=0')).setSortable(True)
        self.colCureMethod = self.addCol(CRBInDocTableCol(u'Метод лечения', 'cureMethod_id', 30, 'rbCureMethod'))
        self.colCureMethod.setSortable(True)
        self.addCol(CEventResultInDocTableCol(u'Результат', 'result_id',     30, 'rbResult')).setSortable(True)
        self.addCol(CEnumInDocTableCol(u'Тарифицируется',   'tariffType',     5, CTariff.tariffTypeNames)).setSortable(True)
        self.addHiddenCol('enableCoefficients')
        self.addCol(CInDocTableCol(     u'Группа',          'batch',    8)).setSortable(True)
        self.addCol(CRBServiceInDocTableCol(u'Услуга',      'service_id',    30, 'rbService', showFields=CRBComboBox.showCodeAndName)).setSortable(True)
        self.addCol(CRBInDocTableCol(u'Тарифная категория', 'tariffCategory_id',    30, 'rbTariffCategory')).setSortable(True)
        self.addCol(CInDocTableCol(u'Код по МКБ',           'MKB',           8)).setSortable(True)
        #self.addCol(CRBInDocTableCol(u'Фаза заболевания',   'phase_id',      20, 'rbDiseasePhases')).setSortable(True)
        self.addCol(CDateInDocTableCol(u'Дата начала',      'begDate',       10, canBeEmpty=True)).setSortable(True)
        self.addCol(CDateInDocTableCol(u'Дата окончания',   'endDate',       10, canBeEmpty=True)).setSortable(True)
        self.addCol(CEnumInDocTableCol(u'Пол',              'sex',            3, [u'', u'М', u'Ж']))
        self.addCol(CInDocTableCol(u'Возраст',              'age',           8))
        self.addCol(CEnumInDocTableCol( u'Период контроля','controlPeriod', 20, (u'Дата услуги', u'Начало года', u'Конец года')))
        self.addCol(CRBInDocTableCol(u'Ед.Уч.',             'unit_id',       8, 'rbMedicalAidUnit'))
        self.addCol(CFloatInDocTableCol(u'Кол-во',          'amount',        8))
        self.addCol(CFloatInDocTableCol(u'УЕТ',             'uet',           4, precision=2)).setSortable(True)
        self.addCol(CFloatInDocTableCol(u'Цена',            'price',         8, precision=4)).setSortable(True)
        self.addCol(CFloatInDocTableCol(u'НДС (%)',            'VAT',         4, precision=2))
        self.addCol(CFloatInDocTableCol(u'Второй тариф с',  'frag1Start', 8, precision=0))
        self.addCol(CFloatInDocTableCol(u'Сумма второго тарифа', 'frag1Sum',   8, precision=4))
        self.addCol(CFloatInDocTableCol(u'Цена второго тарифа',  'frag1Price',  8, precision=4))
        self.addCol(CFloatInDocTableCol(u'Третий тариф с',  'frag2Start', 8, precision=0))
        self.addCol(CFloatInDocTableCol(u'Сумма третьего тарифа', 'frag2Sum',   8, precision=4))
        self.addCol(CFloatInDocTableCol(u'Цена третьего тарифа',  'frag2Price',  8, precision=4))
        self.addCol(CFloatInDocTableCol(u'Фед.цена',        'federalPrice',        8, precision=4))
        self.addCol(CFloatInDocTableCol(u'Фед.предел',      'federalLimitation',   8))
        self.addCol(CFloatInDocTableCol(u'Рег.цена',        'regionalPrice',        8, precision=4))
        self.addCol(CFloatInDocTableCol(u'Рег.предел',      'regionalLimitation',   8))
        self.addCol(CEnumInDocTableCol(u'МЭС',              'mesStatus',            3, (u'-', u'нет или не выполнен', u'выполнен')))

        self.__expenseData = {}
        self.__attachData = {}
        self.serviceRecordCache = CTableRecordCache(QtGui.qApp.db, 'rbService', ['id', 'endDate'])
        
    def updateDateDependentFilters(self, begDate, endDate):
        db = QtGui.qApp.db
        tableCureMethod = db.table('rbCureMethod')
        cond = db.joinOr([ tableCureMethod['endDate'].isNull(),
                           tableCureMethod['endDate'].ge(begDate),
                         ]
                        )
        self.colCureMethod.setFilter(cond)


    # def filterRows(self, params):
    #     cond = []
    #     if params['eventType_id']:
    #         cond.append('eventType_id = %d' % params['eventType_id'])

    #     if params['tariffType']:
    #         cond.append('tariffType = %d' % (params['tariffType'] - 1))

    #     if params['tariffBatch']:
    #         cond.append("batch LIKE '%%%s%%'" % params['tariffBatch'])

    #     if params['service_id']:
    #         cond.append('service_id = %d' % params['service_id'])

    #     self.setFilter(' AND '.join(cond))
    #     self.loadItems(params['master_id'])


#    def serviceDisabled(self, row):
#        return 0 <= row < len(self.items()) and forceInt(self.items()[row].value('tariffType')) == 1

    def eventResultDisabled(self, row):
        return 0 <= row < len(self.items()) and not forceRef(self.items()[row].value('eventType_id'))


    def cellReadOnly(self, index):
        if index.isValid():
            row = index.row()
            column = index.column()
            if column == self.getColIndex('result_id') and self.eventResultDisabled(row): # 2
                return True
        return False


#    def data(self, index, role=Qt.DisplayRole):
##        if index.isValid() and role==Qt.DisplayRole:
##            row = index.row()
##            column = index.column()
##            if column == 3 and self.serviceDisabled(row):
##                    return QVariant()
#        return CInDocTableModel.data(self, index, role)
    def data(self, index, role=Qt.DisplayRole):
        if index.isValid() and role == Qt.FontRole:
            row = index.row()
            column = index.column()
            if 0 <= row < len(self._items):
                if column == self.getColIndex('service_id'): # 5
                    serviceId = forceInt(self.items()[row].value('service_id'))
                    serviceRecord = self.serviceRecordCache.get(serviceId) if serviceId else None
                    if serviceRecord:
                        if forceDate(serviceRecord.value('endDate')) <= QDate.currentDate():
                            font = QFont()
                            font.setItalic(True)
                            font.setBold(True)
                            return font
                        else:
                            return QVariant()

        if index.isValid() and role == Qt.ToolTipRole:
            row = index.row()
            column = index.column()
            if 0 <= row < len(self._items):
                if column == self.getColIndex('service_id'): # 5
                    serviceId = forceInt(self.items()[row].value('service_id'))
                    serviceRecord = self.serviceRecordCache.get(serviceId) if serviceId else None
                    if serviceRecord:
                        if forceDate(serviceRecord.value('endDate')) <= QDate.currentDate():
                            return u"Данная услуга не является актуальной"
                        else:
                            return u""

        return CInDocTableModel.data(self, index, role)


    def setData(self, index, value, role=Qt.EditRole):
        column = index.column()
        row = index.row()
        if column == self.getColIndex('eventType_id') and row<len(self.items()): #0
            record = self.items()[row]
            eventTypeId = forceRef(record.value('eventType_id'))
            newEventTypeId = forceRef(value)
            if newEventTypeId is None or newEventTypeId != eventTypeId:
                record.setValue('result_id', QVariant())
                self.emitCellChanged(row, self.getColIndex('result_id')) #2
        result = CInDocTableModel.setData(self, index, value, role)
        if result and column == self.getColIndex('price', -1):
            self.emit(SIGNAL('priceEdited()'))
        if result:
            self.items()[row].modified = True
        return result


    def tariffExpense(self, row):
        item = self.items()[row]
        return self.__expenseData.setdefault(item, [])


    def tariffAttach(self, row):
        item = self.items()[row]
        return self.__attachData.setdefault(item, [])


    def setAllExpenses(self, listOfList):
        self.__expenseData = dict(zip(self.items(), (subItemList if subItemList else [] for subItemList in listOfList)))
        for row, item in enumerate(self.items()):
            self.items()[row].modified = True


    def setAllAttaches(self, listOfList):
        self.__attachData = dict(zip(self.items(), (subItemList if subItemList else [] for subItemList in listOfList)))
        for row, item in enumerate(self.items()):
            self.items()[row].modified = True


    def addExpenses(self, row, expensesIdList):
        items = self.items()
        if 0<=row<len(items):
            item = items[row]

            presentExpensesIdList = []
            mapExpenceIdToPercent = {}
            for subItem in self.__expenseData.get(item, []):
                expenceId = forceRef(subItem.value('rbTable_id'))
                percent   = forceDouble(subItem.value('percent'))
                presentExpensesIdList.append(expenceId)
                mapExpenceIdToPercent[expenceId] = percent
            if presentExpensesIdList != expensesIdList:
                table = QtGui.qApp.db.table('Contract_CompositionExpense')
                newSubItemList = []
                for expenseId in expensesIdList:
                    subItem = table.newRecord()
                    subItem.setValue('rbTable_id',  toVariant(expenseId))
                    subItem.setValue('percent',     toVariant(mapExpenceIdToPercent.get(expenseId, 0)))
                    newSubItemList.append(subItem)
                self.__expenseData[item] = newSubItemList
            item.modified = True


    def setExpenses(self, row, expenseIdAndPercentList):
        items = self.items()
        if 0<=row<len(items):
            item = items[row]
            table = QtGui.qApp.db.table('Contract_CompositionExpense')
            newSubItemList = []
            for expenseId, percent in expenseIdAndPercentList:
                subItem = table.newRecord()
                subItem.setValue('rbTable_id',  toVariant(expenseId))
                subItem.setValue('percent',     toVariant(percent))
                newSubItemList.append(subItem)
            self.__expenseData[item] = newSubItemList
            item.modified = True


    def insertRecord(self, row, item):
        CInDocTableModel.insertRecord(self, row, item)
        self.__expenseData[item] = []
        self.__attachData[item] = []
        item.modified = True


    def removeRows(self, row, count, parentIndex = QModelIndex()):
        toRemove = self.items()[row:row+count-1]
        result = CInDocTableModel.removeRows(self, row, count, parentIndex)
        if result:
            for item in toRemove:
                if item in self.__expenseData:
                    del self.__expenseData[item]
                if item in self.__attachData:
                    del self.__attachData[item]
                item.modified = True
        return result


    def loadItems(self, masterId):
        def loadSubData(tableName, dataDict):
            mapItemIdToItems = {}
            for item in self.items():
                itemId = forceRef(item.value('id'))
                mapItemIdToItems[itemId] = item
            db = QtGui.qApp.db
            table = db.table(tableName)
            subItems = db.getRecordList(table, '*', table['master_id'].inlist(mapItemIdToItems.iterkeys()))
            for subItem in subItems:
                itemId = forceRef(subItem.value('master_id'))
                item = mapItemIdToItems.get(itemId)
                dataDict.setdefault(item, []).append(subItem)

        CInDocTableModel.loadItems(self, masterId)
        if self.items():
            loadSubData('Contract_CompositionExpense', self.__expenseData)
            loadSubData('ContractTariff_Attach',       self.__attachData)


    def saveItems(self, masterId):
        self.optimizedSave(masterId)

    def optimizedSave(self, masterId):
        def saveSubData(tableName, dataDict, recordsToProcess):
            db = QtGui.qApp.db
            table = db.table(tableName)
            itemIdList = []
            subItemIdList = []
            for idx, item in enumerate(recordsToProcess):
                if hasattr(item, 'modified') and item.modified:
                    itemId = item.value('id')
                    id = itemId.toInt()
                    id = id
                    itemIdList.append(forceRef(itemId))
                    for subItem in dataDict.get(item, []):
                        subItem.setValue('master_id',  itemId)
                        subItemId = db.insertOrUpdate(table, subItem)
                        subItem.setValue('id', toVariant(subItemId))
                        subItemIdList.append(subItemId)
            filter = [table['master_id'].inlist(itemIdList),
                      'NOT ('+table['id'].inlist(subItemIdList)+')']
            db.deleteRecord(table, filter)
        if self._items is not None:
            db = QtGui.qApp.db
            table = self._table
            masterId = toVariant(masterId)
            idList = []
            recordsToProcess = []
            for idx, record in enumerate(self._items):
                record.setValue('master_id', masterId)
                outRecord = record
                if outRecord.isNull('id'):
                    outRecord.modified = True
                    recordsToProcess.append(outRecord)
                else:
                    if hasattr(outRecord, 'modified') and outRecord.modified:
                        recordsToProcess.append(outRecord)
                    id = outRecord.value('id')
                    idList.append(id)
            filter = [table['master_id'].eq(masterId),
                      'NOT (' + table['id'].inlist(idList) + ')']
            if self._filter:
                filter.append(self._filter)
            if table.hasField('deleted'):
                db.markRecordsDeleted(table, filter)
            else:
                db.deleteRecord(table, filter)
            for idx, record in enumerate(recordsToProcess):
                id = db.insertOrUpdate(table, record)
                record.setValue('id', toVariant(id))
                recordsToProcess[idx] = record
            saveSubData('Contract_CompositionExpense', self.__expenseData, recordsToProcess)
            saveSubData('ContractTariff_Attach', self.__attachData, recordsToProcess)

    def findRowWithBugInExpensesPercents(self):
        db = QtGui.qApp.db
        table = db.table('rbExpenseServiceItem')
        baseExpensesIdList = db.getIdList(table, 'id', where = [table['isBase'].eq(1)])

        for row, item in enumerate(self.items()):
            subItems = self.__expenseData.get(item, [])
            total = 0.0

            # при расчете используются только базовые затраты
            for subItem in subItems:
                if forceRef(subItem.value('rbTable_id')) in baseExpensesIdList:
                    total += forceDouble(subItem.value('percent'))

            if total > 100.001:
                return row
        return -1


    def setPricePrecision(self, digits):
        col = self.getColIndex('price')

        if self.cols()[col].precision != digits:
            self.cols()[col].precision = digits

            for record in self.items():
                val = round(forceDouble(record.value('price')), digits)
                record.setValue('price', toVariant(val))

            self.emitAllChanged()

#
# ###################################################################
#

class CTariffExpenseModel(CInDocTableModel):
    expenseEditStyleGlobalPreferenceCode = '19'

    class CSumCol(CFloatInDocTableCol):
        def __init__(self, title, fieldName, width, **params):
            CFloatInDocTableCol.__init__(self, title, fieldName, width, **params)
            self.totalSum = 0.0


        def toString(self, value, record):
            if value.isNull():
                return toVariant(None)
            sum = forceDouble(value)*self.totalSum*0.01
            s = QString()
            if self.precision is None or not self.precision:
                s.setNum(sum)
            else:
                s.setNum(sum, 'f', self.precision)
            record.setValue('sum', toVariant(s))
            return toVariant(s)


        def setEditorData(self, editor, value, record):
            s = self.toString(value)
            editor.setText('' if s is None else s)
            editor.selectAll()


        def getEditorData(self, editor):
            sum = editor.text().toDouble()[0]
            percent = round(sum*100.0/self.totalSum, 6) if self.totalSum>0 else 0.0
            return toVariant(percent)


    class CPercentCol(CFloatInDocTableCol):
        def __init__(self, title, fieldName, width, **params):
            CFloatInDocTableCol.__init__(self, title, fieldName, width, **params)
            self.totalSum = 0.0


        def toString(self, value, record):
            if value.isNull():
                return toVariant(None)
            percent = forceDouble(value)*100.0/self.totalSum if self.totalSum>0 else 0.0
            s = QString()
            if self.precision is None or not self.precision:
                s.setNum(percent)
            else:
                s.setNum(percent, 'f', self.precision)
            record.setValue('percent', toVariant(s))
            return toVariant(s)


        def setEditorData(self, editor, value, record):
            s = self.toString(value)
            editor.setText('' if s is None else s)
            editor.selectAll()


        def getEditorData(self, editor):
            percent = editor.text().toDouble()[0]
            percent = round(percent,  6)
            return toVariant(percent)


    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'Contract_CompositionExpense', 'id', 'master_id', parent)
        self.parent = parent  #wtf? скрывать Qt-шный parent - это плохая затея
        self.percentColEditable = QtGui.qApp.getGlobalPreference(self.expenseEditStyleGlobalPreferenceCode) == u'относительное'

        self.addCol(CRBInDocTableCol(u'Затрата', 'rbTable_id',  30, 'rbExpenseServiceItem', showFields=CRBComboBox.showCodeAndName)).setReadOnly(True)

        if self.percentColEditable:
            self.percentCol = self.addCol(CFloatInDocTableCol(u'Процент', 'percent', 2, precision=6))
            self.sumCol = self.addCol(self.CSumCol(u'Сумма', 'percent', 8, precision=4)).setReadOnly(True)
        else:
            self.percentCol = self.addCol(self.CPercentCol(u'Процент', 'sum', 2, precision=6)).setReadOnly(True)
            self.sumCol = self.addCol(CFloatInDocTableCol(u'Сумма', 'sum', 8, precision=4))

        self.parentItem = None
        self.totalSum = 0


    def setParentItem(self, parentItem):
        totalSum = forceDouble(parentItem.value('price')) if parentItem else 0.0

        if self.percentColEditable:
            updateSum = self.parentItem == parentItem and self.sumCol.totalSum != totalSum
            self.parentItem = parentItem
            self.sumCol.totalSum = totalSum
            if updateSum:
                self.emitColumnChanged(2) # sum
        else:
            updatePercent = self.parentItem == parentItem and self.percentCol.totalSum != totalSum
            self.parentItem = parentItem
            self.percentCol.totalSum = totalSum
            if updatePercent:
                self.emitColumnChanged(1) # sum


    def setData(self, index, value, role=Qt.EditRole):
        CRecordListModel.setData(self, index, value, role)
        self.emitCellChanged(index.row(), 3-index.column()) # procent <-> sum


    def setPrecision(self, digits):
        self.sumCol.precision=digits

#
# ###################################################################
#


class CTariffAttachModel(CInDocTableModel):
    def __init__(self, parent):
        self._parent = parent
        CInDocTableModel.__init__(self, 'ContractTariff_Attach', 'id', 'master_id', parent)
        self.addCol(CRBInDocTableCol(u'Тип прикрепления', 'attachType_id', 30, 'rbAttachType'))
        self.addCol(CIntInDocTableCol(u'Количество', 'amount', 8))
        self.addCol(CBoolInDocTableCol(u'Согласование', 'agreement', 8))
        self.addCol(CBoolInDocTableCol(u'Исключение', 'exception', 8))
        self.setEnableAppendLine(True)


    def getEmptyRecord(self):
        return QtGui.qApp.db.table('ContractTariff_Attach').newRecord()


#
# ###################################################################
#

class CContingentModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'Contract_Contingent', 'id', 'master_id', parent)
        self.addCol(CRBInDocTableCol(u'Тип прикрепления', 'attachType_id', 30, 'rbAttachType'))
        self.addCol(CEnumInDocTableCol(u'ЛПУ прикрепления', 'attachOrg', 10,
                                       (u'Любое', u'Базовое', u'Любое кроме базового')))
        self.addCol(COrgInDocTableCol(u'Занятость', 'org_id', 30))
        self.addCol(CRBInDocTableCol(u'Соц.статус', 'socStatusType_id', 30, 'rbSocStatusType'))
        self.addCol(CInsurerInDocTableCol(u'СМО', 'insurer_id', 50))
        self.addCol(CRBInDocTableCol(u'Тип страхования', 'policyType_id', 30, 'rbPolicyType'))
        self.addCol(CEnumInDocTableCol(u'Зона обслуживания', 'serviceArea', 10, (u'Любая',
        u'Нас.пункт', u'Нас.пункт+область', u'Область', u'Область+Другие', u'Другие')))
        self.addCol(CEnumInDocTableCol(u'Пол', 'sex', 3, (u'', u'М', u'Ж')))
        self.addCol(CInDocTableCol(u'Возраст', 'age', 8))


    def getEmptyRecord(self):
        result = CInDocTableModel.getEmptyRecord(self)
        result.setValue('attachOrg', 1)
        return result

#
# ###################################################################
#

class CTariffsReport(CReport):
    def __init__(self, parent,  contractId):
        CReport.__init__(self, parent)
        self.contractDescr = getContractDescr(contractId)
        self.contractId = contractId
        contractNumber = self.contractDescr.number if self.contractDescr.number else '-'
        contractDate = self.contractDescr.date.toString('dd.MM.yyyy')
        self.setTitle(u'Сведения о тарифах для договора №%s от %s' % (contractNumber, contractDate))


    def getSetupDialog(self, parent):
        return None


    def build(self, params):
        query = self.createQuery()
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        tableColumns = [('5%', [u'№ строки',                        '1' ], CReportBase.AlignRight),
                    ('5%', [u'Событие',                         '2' ], CReportBase.AlignLeft),
                    ('7%', [u'Тарифицируется',                  '3' ], CReportBase.AlignLeft),
                    ('7%', [u'Группа',                          '4' ], CReportBase.AlignLeft),
                    ('10%',[u'Услуга',                          '5' ], CReportBase.AlignLeft),
                    ('10%',[u'Дата начала',                     '6' ], CReportBase.AlignCenter),
                    ('10%',[u'Дата окончания',                  '7' ], CReportBase.AlignCenter),
                    ('5%', [u'Пол',                             '8' ], CReportBase.AlignCenter),
                    ('10%',[u'Возраст',                         '9' ], CReportBase.AlignCenter),
                    ('10%',[u'Период контроля',                 '10'], CReportBase.AlignLeft),
                    ('5%', [u'Ед.уч.',                          '11'], CReportBase.AlignLeft),
                    ('5%', [u'Количество',                      '12'], CReportBase.AlignRight),
                    ('5%', [u'УЕТ',                             '13'], CReportBase.AlignRight),
                    ('5%', [u'Цена',                            '14'], CReportBase.AlignRight),
                    ('5%', [u'НДС',                             '15'], CReportBase.AlignRight),
                    ('10%',[u'Начало второго тарифа',           '16'], CReportBase.AlignRight),
                    ('10%',[u'Сумма второго тарифа',            '17'], CReportBase.AlignRight),
                    ('10%',[u'Цена второго тарифа',             '18'], CReportBase.AlignRight),

                    ('10%',[u'Начало третьего тарифа',          '19'], CReportBase.AlignRight),
                    ('10%',[u'Сумма третьего тарифа',           '20'], CReportBase.AlignRight),
                    ('10%',[u'Цена третьего тарифа',            '21'], CReportBase.AlignRight),
                    ('10%',[u'Разрешить коэффициенты',          '22'], CReportBase.AlignRight),
                   ]
        table = createTable(cursor, tableColumns)
        rowNum = 0

        while query.next():
            record = query.record()
            i = table.addRow()
            rowNum += 1
            eventTypeCode = forceString(record.value('eventType_code'))
            eventTypeName = forceString(record.value('eventType_name'))
            eventTypeStr = u'%s|%s' % (eventTypeCode,  eventTypeName) if eventTypeCode or eventTypeName else  u'не задано'
            serviceCode = forceString(record.value('service_code'))
            serviceName = forceString(record.value('service_name'))
            serviceStr = u'%s|%s' % (serviceCode,  serviceName) if serviceCode or serviceName else  u'не задано'

            table.setText(i, 0, rowNum)
            table.setText(i, 1, eventTypeStr)
            table.setText(i, 2, CTariff.tariffTypeNames[forceInt(record.value('tariffType'))])
            table.setText(i, 3, forceString(record.value('batch')))
            table.setText(i, 4, serviceStr)
            table.setText(i, 5, forceString(record.value('begDate')))
            table.setText(i, 6, forceString(record.value('endDate')))
            table.setText(i, 7, formatSex(forceInt(record.value('sex'))))
            table.setText(i, 8, forceString(record.value('age')))
            table.setText(i, 9, (u'Дата услуги', u'Начало года', u'Конец года')[forceInt(record.value('controlPeriod'))])
            table.setText(i, 10, forceString(record.value('unit_name')))
            table.setText(i, 11, forceString(record.value('amount')))
            table.setText(i, 12, forceString(record.value('uet')))
            table.setText(i, 13, forceString(record.value('price')))
            table.setText(i, 14, forceString(record.value('VAT')))
            table.setText(i, 15, forceString(record.value('frag1Start')))
            table.setText(i, 16, forceString(record.value('frag1Sum')))
            table.setText(i, 17, forceString(record.value('frag1Price')))
            table.setText(i, 18, forceString(record.value('frag2Start')))
            table.setText(i, 19, forceString(record.value('frag2Sum')))
            table.setText(i, 20, forceString(record.value('frag2Price')))
            table.setText(i, 21, forceString(record.value('enableCoefficients')))
        return doc


    def createQuery(self):
        db = QtGui.qApp.db
        stmt = """
        SELECT  Contract_Tariff.tariffType, Contract_Tariff.begDate, Contract_Tariff.endDate,
                Contract_Tariff.sex, Contract_Tariff.age, Contract_Tariff.amount, Contract_Tariff.uet, Contract_Tariff.price,
                Contract_Tariff.frag1Start, Contract_Tariff.frag1Sum, Contract_Tariff.frag1Price,
                Contract_Tariff.frag2Start, Contract_Tariff.frag2Sum, Contract_Tariff.frag2Price,
                EventType.code AS eventType_code,
                EventType.name AS eventType_name,
                rbService.code AS service_code,
                rbService.name AS service_name,
                rbMedicalAidUnit.code AS unit_code,
                rbMedicalAidUnit.name AS unit_name,
                Contract_Tariff.VAT AS VAT
        FROM Contract_Tariff
        LEFT JOIN EventType ON eventType_id=EventType.id AND EventType.deleted=0
        LEFT JOIN rbService ON rbService.id=Contract_Tariff.service_id
        LEFT JOIN rbMedicalAidUnit ON rbMedicalAidUnit.id=unit_id
        WHERE Contract_Tariff.master_id=%d AND Contract_Tariff.deleted=0
        """  % self.contractId
        query = db.query(stmt)
        return query


class CPriceCoefficientEditor(QtGui.QDialog, Ui_PriceCoefficientDialog):
        def __init__(self, parent=None):
            QtGui.QDialog.__init__(self, parent)
            self.setupUi(self)
            for edt in self.edtPriceCoefficient, self.edtPriceExCoefficient, self.edtPriceEx2Coefficient:
                edt.setMinimum(-9999.9999)
                edt.setMaximum(9999.9999)
                edt.setSingleStep(0.0001)


        def prepare(self, cnt):
            self.lblSelectionRows.setText(agreeNumberAndWord(cnt, (u'Выделена %d строка', u'Выделенo %d строки', u'Выделенo %d строк')) % cnt )


        def params(self):
            return (self.edtPriceCoefficient.value() if self.chkPriceCoefficient.isChecked() else None,
                    self.edtPriceExCoefficient.value() if self.chkPriceExCoefficient.isChecked() else None,
                    self.edtPriceEx2Coefficient.value() if self.chkPriceEx2Coefficient.isChecked() else None
                   )


class CParamsContractDialog(QtGui.QDialog, Ui_ParamsContractDialog):
        def __init__(self, parent=None):
            QtGui.QDialog.__init__(self, parent)
            self.setupUi(self)

        def params(self):
            result = {}
            if self.chkContractGroup.isChecked():
                result['grouping'] = self.edtContractGroup.text()
            if self.chkBase.isChecked():
                result['resolution'] = self.edtBase.text()
            if self.chkNumber.isChecked():
                result['number'] = self.edtNumber.text()
            if self.chkDate.isChecked():
                result['date'] = self.edtDate.date()
            if self.chkBegDate.isChecked():
                result['begDate'] = self.edtBegDate.date()
            if self.chkEndDate.isChecked():
                result['endDate'] = self.edtEndDate.date()
            if self.chkCoefficient.isChecked():
                result['coefficient'] = self.edtCoefficient.value()
            if self.chkCoefficientEx.isChecked():
                result['coefficientEx'] = self.edtCoefficientEx.value()
            if self.chkCoefficientEx2.isChecked():
                result['coefficientEx2'] = self.edtCoefficientEx2.value()
            return result


        def setParams(self, record):
            if record:
                self.edtContractGroup.setText(forceString(record.value('grouping')))
                self.edtBase.setText(forceString(record.value('resolution')))
                self.edtNumber.setText(forceString(record.value('number')))
                self.edtDate.setDate(forceDate(record.value('date')))
                self.edtBegDate.setDate(forceDate(record.value('begDate')))
                self.edtEndDate.setDate(forceDate(record.value('endDate')))
                self.edtCoefficient.setValue(forceDouble(record.value('coefficient')))
                self.edtCoefficientEx.setValue(forceDouble(record.value('coefficientEx')))
                self.edtCoefficientEx2.setValue(forceDouble(record.value('coefficientEx2')))



class CPriceListDialog(CDialogBase, Ui_PriceListDialog):
    def __init__(self,  parent, priceListId):
        CDialogBase.__init__(self, parent)
        self.setupPopupMenu()
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.modelContracts = CPriceListTableModel(self)
        self.modelContracts.setObjectName('modelContracts')
        self.tblContracts.setModel(self.modelContracts)
        self.parentPriceListId = priceListId
        self.priceListId = priceListId
        self.selectedContractsIdList = []
        self.cmbPriceList.setPriceListOnly(True)
        self.setRecord()
        self.stringItemDelegate = CStringItemDelegate()
        self.dateItemDelegate = CDateItemDelegate(self)
        self.coefficientItemDelegate = CCoefficientItemDelegate(self)
        self.tblContracts.setItemDelegateForColumn(2, self.stringItemDelegate)
        self.tblContracts.setItemDelegateForColumn(3, self.stringItemDelegate)
        self.tblContracts.setItemDelegateForColumn(4, self.stringItemDelegate)
        self.tblContracts.setItemDelegateForColumn(5, self.dateItemDelegate)
        self.tblContracts.setItemDelegateForColumn(6, self.dateItemDelegate)
        self.tblContracts.setItemDelegateForColumn(7, self.dateItemDelegate)
        self.tblContracts.setItemDelegateForColumn(8, self.coefficientItemDelegate)
        self.tblContracts.setItemDelegateForColumn(9, self.coefficientItemDelegate)
        if self.priceListId:
            self.btnSynchronization.setEnabled(True)
            self.btnRegistration.setEnabled(True)
            self.btnPeriodOnPriceList.setEnabled(True)
        self.tblContracts.setPopupMenu(self.mnuItems)


    def setupPopupMenu(self):
        self.mnuItems = QtGui.QMenu(self)
        self.mnuItems.setObjectName('mnuItems')
        self.actUpdateParamsContract = QtGui.QAction(u'Изменить параметры', self)
        self.actUpdateParamsContract.setObjectName('actUpdateParamsContract')
        self.mnuItems.addAction(self.actUpdateParamsContract)


    def updateSelectedCount(self):
        n = len(self.selectedContractsIdList)
        if n:
            msg = u'выбрано '+formatNum(n, (u'контракт', u'контракта', u'контрактов'))
        else:
            msg = u'ничего не выбрано'
        self.lblSelectedCount.setText(msg)


    def setSelected(self, contractId, value):
        present = self.isSelected(contractId)
        if value:
            if not present:
                self.selectedContractsIdList.append(contractId)
                self.updateSelectedCount()
        else:
            if present:
                self.selectedContractsIdList.remove(contractId)
                self.updateSelectedCount()


    def isSelected(self, contractId):
        return contractId in self.selectedContractsIdList

    @pyqtSignature('')
    def on_mnuItems_aboutToShow(self):
        itemPresent = self.tblContracts.currentIndex().row() >= 0
        self.actUpdateParamsContract.setEnabled(itemPresent)


    @pyqtSignature('')
    def on_actUpdateParamsContract_triggered(self):
        self.getParamsContract()


    def setRecord(self):
        if self.priceListId:
            db = QtGui.qApp.db
            table = db.table('Contract')
            record = db.getRecordEx(table, [table['priceList_id']], [table['deleted'].eq(0), table['priceList_id'].eq(self.priceListId)])
            if record:
                self.priceListId = forceRef(record.value('priceList_id'))
                if self.priceListId:
                    self.cmbPriceList.setValue(self.priceListId)
                    self.setPriceListCode(self.priceListId)
                else:
                    self.tblContracts.setIdList([], None)
            else:
                self.priceListId = None
                self.tblContracts.setIdList([], None)
        else:
            self.tblContracts.setIdList([], None)
        self.setWindowTitleEx(u'Синхронизация договоров с прайс-листом: %s'%(self.cmbPriceList.currentText()))


    def getPriceListIdList(self, id):
        idList = []
        if id:
            db = QtGui.qApp.db
            tableContract = db.table('Contract')
            idList = db.getDistinctIdList(tableContract, tableContract['id'].name(), [tableContract['deleted'].eq(0), tableContract['priceList_id'].eq(id), tableContract['id'].ne(id)], u'finance_id, grouping, resolution, number, date')
        return idList


    def setPriceListIdList(self, idList, posToId):
        if idList:
            self.tblContracts.setIdList(idList, posToId)
            self.tblContracts.setFocus(Qt.OtherFocusReason)


    def setPriceListCode(self, id):
        crIdList = self.getPriceListIdList(id)
        self.setPriceListIdList(crIdList, None)


    @pyqtSignature('QString')
    def on_cmbPriceList_editTextChanged(self, index):
        self.on_btnClearAll_clicked()
        priceListId = self.cmbPriceList.value()
        if priceListId:
            self.priceListId = priceListId
            self.btnEstablish.setEnabled(True)
            self.btnSynchronization.setEnabled(True)
            self.btnRegistration.setEnabled(True)
            self.btnPeriodOnPriceList.setEnabled(True)
            self.setRecord()
        else:
            self.priceListId = None
            self.tblContracts.setIdList([], None)
            self.btnEstablish.setEnabled(False)
            self.btnSynchronization.setEnabled(False)
            self.btnRegistration.setEnabled(False)
            self.btnPeriodOnPriceList.setEnabled(False)
        self.modelContracts.emitDataChanged()


    @pyqtSignature('')
    def on_btnSelectedAll_clicked(self):
        self.selectedContractsIdList = self.modelContracts.idList()
        self.modelContracts.emitDataChanged()
        self.updateSelectedCount()


    @pyqtSignature('')
    def on_btnClearAll_clicked(self):
        self.selectedContractsIdList = []
        self.modelContracts.emitDataChanged()
        self.updateSelectedCount()


    @pyqtSignature('')
    def on_btnEstablish_clicked(self):
        if self.checkDataEntered():
            if self.messageQuestion(u'Прайс-листы выделенных договоров будут заменены на текущий прайс-лист. Вы уверены, что хотите этого?'):
                QtGui.qApp.callWithWaitCursor(self, self.getEstablish)
                self.on_btnClearAll_clicked()
        else:
            self.on_btnClearAll_clicked()


    def getEstablish(self):
        if self.priceListId and self.parentPriceListId:
            db = QtGui.qApp.db
            db.transaction()
            try:
                tableContract = db.table('Contract')
                for selectedContractsId in self.selectedContractsIdList:
                    #recordCache = self.modelContracts._recordsCache.map.get(selectedContractsId, None)
                    recordCache = self.modelContracts._recordsCache.get(selectedContractsId)
                    if recordCache:
                        grouping = forceString(recordCache.value('grouping'))
                        number = forceString(recordCache.value('number'))
                        resolution = forceString(recordCache.value('resolution'))
                        date = forceDate(recordCache.value('date'))
                        begDate = forceDate(recordCache.value('begDate'))
                        endDate = forceDate(recordCache.value('endDate'))
                        coefficientPrice = forceDouble(recordCache.value('coefficient'))
                        coefficientPriceEx = forceDouble(recordCache.value('coefficientEx'))
                        coefficientPriceEx2 = forceDouble(recordCache.value('coefficientEx2'))
                        record = db.getRecordEx(tableContract, '*', [tableContract['id'].eq(selectedContractsId), tableContract['deleted'].eq(0)])
                        if number:
                            record.setValue('number', toVariant(number))
                        if grouping:
                            record.setValue('grouping', toVariant(grouping))
                        if resolution:
                            record.setValue('resolution', toVariant(resolution))
                        if date:
                            record.setValue('date', toVariant(date))
                        if begDate:
                            record.setValue('begDate', toVariant(begDate))
                        if endDate:
                            record.setValue('endDate', toVariant(endDate))
                        record.setValue('priceList_id', toVariant(self.parentPriceListId))
                        record.setValue('coefficient', toVariant(coefficientPrice))
                        record.setValue('coefficientEx', toVariant(coefficientPriceEx))
                        record.setValue('coefficientEx2', toVariant(coefficientPriceEx2))
                        db.updateRecord(tableContract, record)
                db.commit()
            except:
                db.rollback()
                QtGui.qApp.logCurrentException()
                raise
            self.priceListId = self.parentPriceListId
            self.setRecord()
            self.modelContracts.emitDataChanged()

    @staticmethod
    def updateTariffToCoefficient(record, coefficients):
        assert len(coefficients) == 3
        recordChanged = False
        if record:
            for coefficient, fieldName in zip(coefficients, ('price', 'priceEx', 'priceEx2')):
                if coefficient is not None:
                    value = forceDouble(record.value(fieldName))
                    newValue = value*coefficient if coefficient >= 0 else -value/coefficient
                    record.setValue(fieldName, newValue)
                    recordChanged = True
        return recordChanged


    @pyqtSignature('')
    def on_btnSynchronization_clicked(self):
        if self.checkDataEntered():
            if self.synchronizeContracts():
                if self.messageQuestion(u'Будет проведена синхронизация выделенных договоров в соответствии с текущим прайс-листом. Вы уверены, что хотите этого?'):
                    self.getSynchronizationTariff()
                    self.setRecord()
                    self.modelContracts.emitDataChanged()
        else:
            self.on_btnClearAll_clicked()


    def synchronizeContracts(self):
        if self.priceListId != self.parentPriceListId:
            return self.messageQuestion(u'Выбранный прайс-лист не соответствует текущему договору.\nХотите продолжить?')
        return True


    def getSynchronizationTariff(self, registration = False):
        if self.priceListId and self.selectedContractsIdList and self.parentPriceListId:
            QtGui.qApp.setWaitCursor()
            try:
                db = QtGui.qApp.db
                db.transaction()
                try:
                    progressDialog = CContractFormProgressDialog(self)
                    progressDialog.lblByContracts.setText(u'Тарифы')
                    progressDialog.setWindowTitle(u'Синхронизация договоров')
                    progressDialog.show()
                    tableContract = db.table('Contract')
                    tableContractTariff = db.table('Contract_Tariff')
                    table = tableContract.innerJoin(tableContractTariff, tableContract['id'].eq(tableContractTariff['master_id']))
                    records = db.getRecordListGroupBy(table, 'Contract_Tariff.*', [tableContractTariff['deleted'].eq(0), tableContract['deleted'].eq(0), tableContractTariff['master_id'].eq(self.parentPriceListId)], 'Contract_Tariff.id')
                    updateTariffIdList = []
                    progressDialog.setNumContracts(len(records))
                    for record in records:
                        progressDialog.prbContracts.setValue(progressDialog.prbContracts.value()+1)
#                        tariffId = forceRef(record.value('id'))
                        eventTypeId = forceRef(record.value('eventType_id'))
                        tariffType = forceInt(record.value('tariffType'))
                        serviceId = forceRef(record.value('service_id'))
                        tariffCategoryId = forceRef(record.value('tariffCategory_id'))
                        sex = forceInt(record.value('sex'))
                        age = forceString(record.value('age'))
                        MKB = forceString(record.value('MKB'))
                        #phaseId = forceRef(record.value('phase_id'))
                        cond = [tableContract['priceList_id'].eq(self.parentPriceListId),
                                tableContractTariff['master_id'].inlist(self.selectedContractsIdList),
                                tableContractTariff['master_id'].ne(self.parentPriceListId),
                                tableContract['deleted'].eq(0),
                                tableContractTariff['deleted'].eq(0),
                                tableContractTariff['eventType_id'].eq(eventTypeId),
                                tableContractTariff['tariffType'].eq(tariffType),
                                tableContractTariff['service_id'].eq(serviceId),
                                tableContractTariff['tariffCategory_id'].eq(tariffCategoryId),
                                tableContractTariff['MKB'].eq(MKB),
                                #tableContractTariff['phase_id'].eq(phaseId),
                                tableContractTariff['sex'].eq(sex),
                                tableContractTariff['age'].eq(age)
                                ]
                        if updateTariffIdList:
                            cond.append(tableContractTariff['id'].notInlist(updateTariffIdList))
                        oldRecords = db.getRecordListGroupBy(table, [tableContractTariff['id'].alias('contractTariffId'), tableContractTariff['master_id'], tableContract['id'].alias('contractId')], cond, 'Contract_Tariff.id')
                        updateTariffId = None
                        contractNameList = {}
                        if self.chkUpdate.isChecked():
                            progressDialog.setNumContractSteps(len(oldRecords))
                            for oldRecord in oldRecords:
                                progressDialog.step()
                                contractId = forceRef(oldRecord.value('contractId'))
                                recordCache = self.modelContracts._recordsCache.get(contractId)
                                if recordCache:
                                    coefficientPrice = forceDouble(recordCache.value('coefficient'))
                                    coefficientPriceEx = forceDouble(recordCache.value('coefficientEx'))
                                    coefficientPriceEx2 = forceDouble(recordCache.value('coefficientEx2'))
                                    coefficients = coefficientPrice, coefficientPriceEx, coefficientPriceEx2
                                    oldTariffId = forceRef(oldRecord.value('contractTariffId'))
                                    masterId = forceRef(oldRecord.value('master_id'))
                                    newRecord = tableContractTariff.newRecord()
                                    copyFields(newRecord, record)
                                    self.updateTariffToCoefficient(newRecord, coefficients)
                                    newRecord.setValue('master_id', toVariant(masterId))
                                    newRecord.setValue('id', toVariant(oldTariffId))
                                    updateTariffId = db.updateRecord(tableContractTariff, newRecord)
                                    if updateTariffId and updateTariffId not in updateTariffIdList:
                                        updateTariffIdList.append(updateTariffId)
                                    if not contractNameList.get(masterId, None):
                                        contractName = forceString(recordCache.value('number')) + ' ' + forceString(forceDate(recordCache.value('date')))
                                        contractNameList[masterId] = contractName
                                        progressDialog.setContractName(contractName)
                        if not oldRecords and self.chkInsert.isChecked():
                            progressDialog.setNumContractSteps(len(self.selectedContractsIdList))
                            for selectedContractsId in self.selectedContractsIdList:
                                progressDialog.step()
                                #recordCache = self.modelContracts._recordsCache.map.get(selectedContractsId, None)
                                recordCache = self.modelContracts._recordsCache.get(selectedContractsId)
                                if recordCache:
                                    coefficientPrice = forceDouble(recordCache.value('coefficient'))
                                    coefficientPriceEx = forceDouble(recordCache.value('coefficientEx'))
                                    coefficientPriceEx2 = forceDouble(recordCache.value('coefficientEx2'))
                                    coefficients = coefficientPrice, coefficientPriceEx, coefficientPriceEx2
                                    newRecord = tableContractTariff.newRecord()
                                    copyFields(newRecord, record)
                                    self.updateTariffToCoefficient(newRecord, coefficients)
                                    newRecord.setValue('master_id', toVariant(selectedContractsId))
                                    newRecord.setValue('id', toVariant(None))
                                    updateTariffId = db.insertRecord(tableContractTariff, newRecord)
                                    if updateTariffId and updateTariffId not in updateTariffIdList:
                                        updateTariffIdList.append(updateTariffId)
                                    if not contractNameList.get(selectedContractsId, None):
                                        contractName = forceString(recordCache.value('number')) + ' ' + forceString(forceDate(recordCache.value('date')))
                                        contractNameList[selectedContractsId] = contractName
                                        progressDialog.setContractName(contractName)
                    for selectedContractsId in self.selectedContractsIdList:
                        #recordContract = self.modelContracts._recordsCache.map.get(selectedContractsId, None)
                        recordContract = self.modelContracts._recordsCache.get(selectedContractsId)
                        if recordContract:
                            recordContract.setValue('priceList_id', toVariant(self.parentPriceListId))
                            db.updateRecord(tableContract, recordContract)
                    db.commit()
                except:
                    db.rollback()
                    QtGui.qApp.logCurrentException()
                    raise
            finally:
                QtGui.qApp.restoreOverrideCursor()
                if progressDialog:
                    progressDialog.close()
                    progressDialog.deleteLater()


    @pyqtSignature('')
    def on_btnRegistration_clicked(self):
        if self.checkDataEntered() and self.checkDataEnteredRegistration():
            if self.selectedContractsIdList and self.synchronizeContracts():
                if self.messageQuestion(u'Будет проведена регистрация выбранных договоров. Вы уверены, что хотите этого?'):
                    self.getRegistration()
                    if self.messageQuestion(u'Будет проведена синхронизация вновь созданных договоров  по текущему прайс-листу. Вы уверены, что хотите этого?'):
                        self.getSynchronizationTariff(True)
                    self.setRecord()
                    self.modelContracts.emitDataChanged()
        else:
            self.on_btnClearAll_clicked()


    @pyqtSignature('')
    def on_btnPeriodOnPriceList_clicked(self):
        if self.selectedContractsIdList and self.synchronizeContracts():
            if self.messageQuestion(u'Дата и период выбранных договоров будут установлены по текущему прайс-листу. Вы уверены, что хотите этого?'):
                QtGui.qApp.setWaitCursor()
                try:
                    db = QtGui.qApp.db
                    db.transaction()
                    try:
                        tableContract = db.table('Contract')
                        if self.parentPriceListId:
                            for selectedContractsId in self.selectedContractsIdList:
                                record = db.getRecordEx(tableContract, [tableContract['date'], tableContract['begDate'], tableContract['endDate']], [tableContract['deleted'].eq(0), tableContract['id'].eq(self.parentPriceListId)])
                                if record and selectedContractsId:
                                    date = forceDate(record.value('date'))
                                    begDate = forceDate(record.value('begDate'))
                                    endDate = forceDate(record.value('endDate'))
                                    db.updateRecords(tableContract, [tableContract['endDate'].eq(endDate), tableContract['begDate'].eq(begDate), tableContract['date'].eq(date)], [tableContract['id'].eq(selectedContractsId), tableContract['deleted'].eq(0)])
                        db.commit()
                    except:
                        db.rollback()
                        QtGui.qApp.logCurrentException()
                        raise
                finally:
                    QtGui.qApp.restoreOverrideCursor()
                    self.setRecord()
                    self.modelContracts.emitDataChanged()


    def getParamsContract(self):
        if self.selectedContractsIdList:
            selectedContractsId = self.selectedContractsIdList[0]
            if selectedContractsId:
                db = QtGui.qApp.db
                tableContract = db.table('Contract')
                record = db.getRecordEx(tableContract, '*', [tableContract['id'].eq(selectedContractsId), tableContract['deleted'].eq(0)])
            setupDialog = CParamsContractDialog(self)
            setupDialog.setParams(record)
            if setupDialog.exec_():
                params = setupDialog.params()
                for selectedContractsId in self.selectedContractsIdList:
                    #recordCache = self.modelContracts._recordsCache.map.get(selectedContractsId, None)
                    recordCache = self.modelContracts._recordsCache.get(selectedContractsId)
                    if recordCache:
                        for fieldName in ('grouping', 'resolution', 'number', 'date', 'begDate', 'endDate', 'coefficient', 'coefficientEx', 'coefficientEx2'):
                            value = params.get(fieldName, None)
                            if value is not None:
                                recordCache.setValue(fieldName, toVariant(value))


    def duplicateContract(self, contractId, recordCache, progressDialog):
        newId = None
        db = QtGui.qApp.db
        table = db.table('Contract')
        tableContractTariff = db.table('Contract_Tariff')
        tableContractExpense = db.table('Contract_CompositionExpense')
        db.transaction()
        try:
            grouping = forceString(recordCache.value('grouping'))
            number = forceString(recordCache.value('number'))
            resolution = forceString(recordCache.value('resolution'))
            date = forceDate(recordCache.value('date'))
            begDate = forceDate(recordCache.value('begDate'))
            endDate = forceDate(recordCache.value('endDate'))
            coefficientPrice = forceDouble(recordCache.value('coefficient'))
            coefficientPriceEx = forceDouble(recordCache.value('coefficientEx'))
            coefficientPriceEx2 = forceDouble(recordCache.value('coefficientEx2'))
            coefficients = coefficientPrice, coefficientPriceEx, coefficientPriceEx2
            record = db.getRecordEx(table, '*', [table['id'].eq(contractId), table['deleted'].eq(0)])
            record.setNull('id')
            numberRecord = forceString(record.value('number'))
            if number.lower() == numberRecord.lower():
                record.setValue('number', toVariant(numberRecord + u'-копия'))
            else:
                record.setValue('number', toVariant(number))
            if grouping:
                record.setValue('grouping', toVariant(grouping))
            if resolution:
                record.setValue('resolution', toVariant(resolution))
            if date:
                record.setValue('date', toVariant(date))
            if begDate:
                record.setValue('begDate', toVariant(begDate))
            if endDate:
                record.setValue('endDate', toVariant(endDate))
            record.setValue('priceList_id', toVariant(self.parentPriceListId))
            record.setValue('coefficient', toVariant(coefficientPrice))
            record.setValue('coefficientEx', toVariant(coefficientPriceEx))
            record.setValue('coefficientEx2', toVariant(coefficientPriceEx2))
            newId = db.insertRecord(table, record)
            db.copyDepended(db.table('Contract_Contingent'), 'master_id', contractId, newId)
            db.copyDepended(db.table('Contract_Contragent'), 'master_id', contractId, newId)
            db.copyDepended(db.table('Contract_Specification'), 'master_id', contractId, newId)
            stmt = db.selectStmt(tableContractTariff, '*', [tableContractTariff['master_id'].eq(contractId), tableContractTariff['deleted'].eq(0)], 'id')
            qquery = db.query(stmt)
            progressDialog.setContractName(number + ' ' + forceString(date))
            progressDialog.setNumContractSteps(qquery.size())
            while qquery.next():
                progressDialog.step()
                recordTariff = qquery.record()
                tariffId = forceRef(recordTariff.value('id'))
                newRecord = tableContractTariff.newRecord()
                newRecord.setNull('id')
                newRecord.setValue('master_id', toVariant(newId))
                copyFields(newRecord, recordTariff)
                self.updateTariffToCoefficient(newRecord, coefficients)
                newTariffId = db.insertRecord(tableContractTariff, newRecord)
                if self.chkInsertExpense.isChecked() and tariffId and newTariffId:
                    recordExpenses = db.getRecordList(tableContractExpense, '*', [tableContractExpense['master_id'].eq(tariffId)])
                    for recordExpense in recordExpenses:
                        recordExpense.setNull('id')
                        recordExpense.setValue('master_id', toVariant(newTariffId))
                        db.insertRecord(tableContractExpense, recordExpense)
            db.commit()
        except:
            db.rollback()
            raise
        return newId


    def getRegistration(self):
        if self.priceListId and self.selectedContractsIdList and self.parentPriceListId:
            QtGui.qApp.setWaitCursor()
            try:
                db = QtGui.qApp.db
                db.transaction()
                try:
                    progressDialog = CFormProgressDialog(self)
                    progressDialog.setWindowTitle(u'Регистрация договоров')
                    progressDialog.setNumContracts(len(self.selectedContractsIdList))
                    progressDialog.show()
                    tableContract = db.table('Contract')
                    duplicateContractIdList = []
                    for selectedContractsId in self.selectedContractsIdList:
                        recordCache = self.modelContracts._recordsCache.get(selectedContractsId)
                        if recordCache:
                            date = forceDate(recordCache.value('date'))
                            record = db.getRecordEx(tableContract, '*', [tableContract['id'].eq(selectedContractsId), tableContract['deleted'].eq(0)])
                            if record:
                                record.setValue('endDate', toVariant(date))
                                db.updateRecord(tableContract, record)
                                duplicateContractId = self.duplicateContract(selectedContractsId, recordCache, progressDialog)
                                if duplicateContractId and (duplicateContractId not in duplicateContractIdList):
                                    duplicateContractIdList.append(duplicateContractId)
                    db.commit()
                    self.selectedContractsIdList = duplicateContractIdList
                    self.setRecord()
                    self.modelContracts.emitDataChanged()
                except:
                    db.rollback()
                    QtGui.qApp.logCurrentException()
                    raise
            finally:
                QtGui.qApp.restoreOverrideCursor()
                if progressDialog:
                    progressDialog.close()
                    progressDialog.deleteLater()


    def messageQuestion(self, message):
        res = QtGui.QMessageBox.question( self,
                     u'Внимание!',
                     message,
                     QtGui.QMessageBox.Yes|QtGui.QMessageBox.No,
                     QtGui.QMessageBox.No)
        if res == QtGui.QMessageBox.Yes:
            return True
        return False


    def checkDataEnteredRegistration(self):
        result = True
        db = QtGui.qApp.db
        tableContract = db.table('Contract')
        for selectedContractsId in self.selectedContractsIdList:
            #recordCache = self.modelContracts._recordsCache.map.get(selectedContractsId, None)
            recordCache = self.modelContracts._recordsCache.get(selectedContractsId)
            if recordCache:
                endDate = forceDate(recordCache.value('date'))
                record = db.getRecordEx(tableContract, '*', [tableContract['id'].eq(selectedContractsId), tableContract['deleted'].eq(0)])
                if record:
                    dateContract = forceDate(record.value('date'))
                    begDateContract = forceDate(record.value('begDate'))
                    result = result and ((dateContract <= endDate and begDateContract <= endDate) or self.checkValueMessage(u'Дата окончания периода %s должна быть больше или равна дате начала периода %s'% (forceString(endDate), forceString(begDateContract)), False, self.tblContracts, self.modelContracts.findItemIdIndex(selectedContractsId), 5))
        return result


    def checkDataEntered(self):
        result = True
        for key in self.selectedContractsIdList:
            #recordCache = self.modelContracts._recordsCache.map.get(key, None)
            recordCache = self.modelContracts._recordsCache.get(key)
            if recordCache:
                row = self.modelContracts.findItemIdIndex(key)
                date = forceDate(recordCache.value('date'))
                begDate = forceDate(recordCache.value('begDate'))
                endDate = forceDate(recordCache.value('endDate'))
                result = result and (date or self.checkInputMessage(u'дату', False, self.tblContracts, row, 5))
                result = result and (begDate or self.checkInputMessage(u'начальную дату', False, self.tblContracts, row, 6))
                result = result and (endDate or self.checkInputMessage(u'конечную дату', False, self.tblContracts, row, 7))
                result = result and ((date <= begDate and date < endDate) or self.checkValueMessage(u'Период %s-%s не может начаться раньше даты %s'% (forceString(begDate), forceString(endDate), forceString(date)), False, self.tblContracts, row, 5))
                result = result and ((begDate <= endDate) or self.checkValueMessage(u'Дата начала периода %s должна быть меньше или равна дате окончания периода %s' % (forceString(begDate), forceString(endDate)), False, self.tblContracts, row, 6))
        return result


class CPriceListTableModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent, [
            CEnableCol(u'Выбрать',               ['id'], 5,  parent),
            CRefBookCol(u'Источник финансирования', ['finance_id'], 'rbFinance', 20),
            CTextCol(u'Группа',                  ['grouping'],  20),
            CTextCol(u'Основание',               ['resolution'],10),
            CTextCol(u'Номер',                   ['number'],    5),
            CDateCol(u'Дата',                    ['date'],      10),
            CDateCol(u'Нач.дата',                ['begDate'],   10),
            CDateCol(u'Кон.дата',                ['endDate'],   10),
            CSumCol(u'Коэффициент тарифа',              ['coefficient'], 5),
            CSumCol(u'Коэффициент расширенного тарифа', ['coefficientEx'], 5),
            CSumCol(u'Второй коэффициент расширенного тарифа', ['coefficientEx2'], 5)
            ], 'Contract' )
        self.parent = parent #wtf? скрывать Qt-шный parent - это плохая затея


    def flags(self, index):
        result = CTableModel.flags(self, index)
        if index.column() == 0:
            result |= Qt.ItemIsUserCheckable
        elif index.column() != 1:
            result |= Qt.ItemIsEditable
        return result


    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.BackgroundColorRole:
            row = index.row()
            column = index.column()
            contractId = self._idList[row]
            #record = self._recordsCache.map.get(contractId, None)
            record = self._recordsCache.get(contractId)
            if record and (    (column == 10 and not forceDouble(record.value('coefficientEx2')))
                            or (column == 9 and not forceDouble(record.value('coefficientEx')))
                            or (column == 8 and not forceDouble(record.value('coefficient')))
                            or (column == 7 and not forceDate(record.value('endDate')))
                            or (column == 6 and not forceDate(record.value('begDate')))
                            or (column == 5 and not forceDate(record.value('date')))
                            or (column == 4 and not forceString(record.value('number')))
                            or (column == 3 and not forceString(record.value('resolution')))
                            or (column == 2 and not forceString(record.value('grouping')))
                          ):
                   return toVariant(QtGui.QColor(255, 0, 0))
            return QVariant()
        elif role == Qt.FontRole:
            row = index.row()
            column = index.column()
            contractId = self._idList[row]
            #record = self._recordsCache.map.get(contractId, None)
            record = self._recordsCache.get(contractId)
            font = QtGui.QFont()
            if record and (   (column == 8  and not forceDouble(record.value('coefficient')))
                           or (column == 9  and not forceDouble(record.value('coefficientEx')))
                           or (column == 10 and not forceDouble(record.value('coefficientEx2')))
                          ):
                        font.setBold(True)
                        font.setItalic(True)
            return QVariant(font)
        elif role == Qt.EditRole:
            row = index.row()
            column = index.column()
            contractId = self._idList[row]
            #record = self._recordsCache.map.get(contractId, None)
            record = self._recordsCache.get(contractId)
            if record:
                if column == 2:
                    return toVariant(forceString(record.value('grouping')))
                elif column == 3:
                    return toVariant(forceString(record.value('resolution')))
                elif column == 4:
                    return toVariant(forceString(record.value('number')))
                elif column == 5:
                    return toVariant(forceDate(record.value('date')))
                elif column == 6:
                    return toVariant(forceDate(record.value('begDate')))
                elif column == 7:
                    return toVariant(forceDate(record.value('endDate')))
                elif column == 8:
                    return toVariant(forceDouble(record.value('coefficient')))
                elif column == 9:
                    return toVariant(forceDouble(record.value('coefficientEx')))
                elif column == 10:
                    return toVariant(forceDouble(record.value('coefficientEx2')))
            return QVariant()
        return CTableModel.data(self, index, role)


    def setData(self, index, value, role=Qt.EditRole):
        row = index.row()
        column = index.column()
        contractId = self._idList[row]
        if role == Qt.EditRole:
            if contractId:
                #record = self._recordsCache.map.get(contractId, None)
                record = self._recordsCache.get(contractId)
                if record:
                    if column == 2:
                        record.setValue('grouping', toVariant(value))
                    elif column == 3:
                        record.setValue('resolution', toVariant(value))
                    elif column == 4:
                        record.setValue('number', toVariant(value))
                    elif column == 5:
                        record.setValue('date', toVariant(value))
                    elif column == 6:
                        record.setValue('begDate', toVariant(value))
                    elif column == 7:
                        record.setValue('endDate', toVariant(value))
                    elif column == 8:
                        record.setValue('coefficient', toVariant(value))
                    elif column == 9:
                        record.setValue('coefficientEx', toVariant(value))
                    elif column == 10:
                        record.setValue('coefficientEx2', toVariant(value))
                    self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index, index)
            return True
        if role == Qt.CheckStateRole:
            if contractId and column == 0:
                self.parent.setSelected(contractId, forceInt(value) == Qt.Checked)
                self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index, index)
            return True
        return False

#
# ###################################################################
#

class CAttributesModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'Contract_Attribute', 'id', 'master_id', parent)
        self.addCol(CRBInDocTableCol(u'Тип', 'attributeType_id',  30,
            'rbContractAttributeType')).setSortable(True)
        self.addCol(CDateInDocTableCol(u'Дата введения', 'begDate',  10,
                                       precision=6)).setSortable(True)
        self.addCol(CInDocTableCol(u'Значение', 'value', 10, precision=2))

#
# ###################################################################
#

class CTariffCoefficientsModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'Contract_Coefficient', 'id', 'master_id', parent)
        self.addHiddenCol('matter')
        self.addCol(CRBInDocTableCol(u'Тип', 'coefficientType_id', 30, 'rbContractCoefficientType',showFields=CRBComboBox.showCodeAndName)).setSortable(True)
        self.addCol(CDateInDocTableCol(u'Дата введения', 'begDate',10, precision=6)).setSortable(True)
        self.addCol(CBoolInDocTableCol(u'Действующий', 'isActive',  4)).setSortable(True)
        self.addCol(CFloatInDocTableCol(u'Значение', 'value', 10, precision=2))
        self.addCol(CIntInDocTableCol(u'Группа', 'groupCode', 10, minVal=0, maxVal=99)).setSortable(True)
        self.addCol(CEnumInDocTableCol(u'Групповая операция', 'groupOp', 15, ('+', '*', u'первый подходящий', 'max')))
        self.addCol(CIntInDocTableCol(u'Точность группы', 'groupPrecision', 10, minVal=0, maxVal=12))
        self.addCol(CFloatInDocTableCol(u'Макс.предел', 'maxLimit', 10, precision=5))


    def getEmptyRecord(self):
        result = CInDocTableModel.getEmptyRecord(self)
        result.setValue('isActive',  True)
        result.setValue('groupPrecision', 2)
        result.setValue('maxLimit',       10000.0)
        return result


    def setData(self, index, value, role=Qt.EditRole):
        result = CInDocTableModel.setData(self, index, value, role)
        if role==Qt.EditRole and result:
            row = index.row()
            groupCode = forceInt(self.value(row, 'groupCode'))
            if groupCode != 0:
                column = index.column()
                col = self._cols[column]
                fieldName = col.fieldName()
                if fieldName in ('matter', 'groupOp', 'groupPrecision', 'maxLimit'):
                    for i, item in enumerate(self._items):
                        if i != row and groupCode == forceInt(item.value('groupCode')):
                            self.setValue(i, fieldName, value)
#                            item.setValue(fieldName, value)
        return result


    def setValuePrecision(self, digits):
        col = self.getColIndex('value')
        if self.cols()[col].precision != digits:
            self.cols()[col].precision = digits
            for record in self.items():
                val = round(forceDouble(record.value('value')), digits)
                record.setValue('value', toVariant(val))
            self.emitAllChanged()

