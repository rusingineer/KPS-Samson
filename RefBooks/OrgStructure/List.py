# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2020 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################
# Перенести в Orgs?

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QAbstractTableModel, QModelIndex, QVariant, pyqtSignature, SIGNAL, QDate, QDateTime

from library.crbcombobox        import CRBComboBox
from library.HierarchicalItemsListDialog import CHierarchicalItemsListDialog
from library.InDocTable         import CInDocTableModel, CEnumInDocTableCol, CFloatInDocTableCol, CInDocTableCol, CRBInDocTableCol, CTimeInDocTableCol, CIntInDocTableCol, CBoolInDocTableCol
from library.interchange        import getCheckBoxValue, getComboBoxValue, getLineEditValue, getRBComboBoxValue, getSpinBoxValue, setCheckBoxValue, setComboBoxValue, setLineEditValue, setRBComboBoxValue, setSpinBoxValue, getTextEditValue, setTextEditValue
from library.ItemEditorDialogWithIdentification import CItemEditorDialogWithIdentification
from library.naturalSort        import naturalSorted
from library.TableModel         import CTableModel, CDesignationCol, CTextCol, CCol
from library.TreeModel          import CDragDropDBTreeModel
from library.Utils              import forceInt, forceRef, forceString, forceStringEx, toVariant, variantEq, forceDate

from Events.ActionTypeComboBox  import CActionTypeTableCol
from InvoluteBedsModel          import CHospitalBedsModel, CInvoluteBedsModel
from KLADR.kladrComboxes        import CKLADRComboBox, CStreetComboBox
from KLADR.KLADRModel           import getCityName, getStreetName
from Orgs.EquipmentComboBox     import CEquipmentComboBox
from Orgs.Orgs                  import selectOrganisation
from Orgs.Utils import getOrgStructureFullName
from RefBooks.Tables            import rbNet
from Registry.Utils             import getHouseId
from Resources.OrgStructureJobs import COrgStructureJobsModel
from Stock.NomenclatureComboBox import CNomenclatureInDocTableCol

from .Ui_OrgStructureEditor import Ui_ItemEditorDialog


class COrgStructureList(CHierarchicalItemsListDialog):
    def __init__(self, parent):
        CHierarchicalItemsListDialog.__init__(self, parent, [
            CDesignationCol(u'ЛПУ',  ['organisation_id'], ('Organisation', 'infisCode'), 5),
            CTextCol(       u'Код',  ['code'], 40),
            CTextCol(       u'Наименование', ['name'], 40),
            ], 'OrgStructure', ['organisation_id', 'parent_id', 'code', 'name'])
        self.setWindowTitleEx(u'Структура ЛПУ')
        self.expandedItemsState = {}


    def preSetupUi(self):
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.addModels('Tree', CDragDropDBTreeModel(self, self.tableName, 'id', 'parent_id', 'code', self.order))
        self.addModels('Table',COrgStructureTableModel(self, self.cols, self.tableName))
        self.modelTree.setLeavesVisible(True)
        self.addObject('actDelete',    QtGui.QAction(u'Удалить', self))


    def postSetupUi(self):
        self.setModels(self.treeItems,  self.modelTree,  self.selectionModelTree)
        self.setModels(self.tblItems,   self.modelTable, self.selectionModelTable)
        self.treeItems.header().hide()
        idList = self.select(self.props)
        self.modelTable.setIdList(idList)
        self.tblItems.selectRow(0)
        self.btnSelect.setEnabled(self.forSelect)
        self.btnSelect.setVisible(self.forSelect)
        self.btnSelect.setDefault(self.forSelect)
        self.btnFilter.setEnabled(bool(self.filterClass))
        self.btnFilter.setVisible(bool(self.filterClass))
        self.btnFind.setEnabled(bool(self.findClass))
        self.btnFind.setVisible(bool(self.findClass))
        self.btnEdit.setDefault(not self.forSelect)
        self.tblItems.addPopupDelRow()
        self.tblItems.setFocus(Qt.OtherFocusReason)
        #drag-n-drop support
        self.treeItems.dragEnabled()
        self.treeItems.acceptDrops()
        self.treeItems.showDropIndicator()
        self.treeItems.setDragDropMode(QtGui.QAbstractItemView.InternalMove)
        # tree popup menu
        self.treeItems.createPopupMenu([self.actDelete])
        self.connect(self.treeItems.popupMenu(), SIGNAL('aboutToShow()'), self.popupMenuAboutToShow)
        self.connect(self.tblItems.popupMenu(), SIGNAL('aboutToShow()'), self.popupTableMenuAboutToShow)
        #self.connect(self.modelTree, SIGNAL('modelAboutToBeReset()'),  self.treeModelAboutToBeReset)
        #self.connect(self.modelTree, SIGNAL('modelReset()'),  self.treeModelReset)
        self.connect(self.modelTree, SIGNAL('saveExpandedState()'),  self.saveExpandedState)
        self.connect(self.modelTree, SIGNAL('restoreExpandedState()'),  self.restoreExpandedState)
        prefes = QtGui.qApp.preferences
        properts = prefes.appPrefs
        expand_1 = forceInt(properts.get('treeOrgStructureExpand', QVariant()))
        if not expand_1:
            self.treeItems.expandToDepth(0)
        elif expand_1 == 1:
            self.treeItems.expandAll()
        else:
            expandLevel = forceInt(properts.get('treeOrgStructureExpandLevel', QVariant(1)))
            self.treeItems.expandToDepth(expandLevel)
        


    def popupMenuAboutToShow(self):
        currentItemId = self.currentTreeItemId()
        self.actDelete.setEnabled(bool(currentItemId) and not self.orgStructureIdIsUsed(currentItemId))


    def popupTableMenuAboutToShow(self):
        currentItemId = self.currentItemId()
        self.tblItems._actDeleteRow.setEnabled(bool(currentItemId) and not self.orgStructureIdIsUsed(currentItemId))


    def orgStructureIdIsUsed(self, orgStructureId):
        db = QtGui.qApp.db
        if db.translate('BlankActions_Moving', 'orgStructure_id', orgStructureId, 'id'):
            return True
        if db.translate('BlankTempInvalid_Moving', 'orgStructure_id', orgStructureId, 'id'):
            return True
        if db.translate('OrgStructure', 'parent_id', orgStructureId, 'id'):
            return True
        if db.translate('Person', 'orgStructure_id', orgStructureId, 'id'):
            return True
        if db.translate('StockRequisition', 'recipient_id', orgStructureId, 'id'):
            return True
        if db.translate('StockRequisition', 'supplier_id', orgStructureId, 'id'):
            return True
        if db.translate('StockTrans', 'creOrgStructure_id', orgStructureId, 'id'):
            return True
        if db.translate('StockTrans', 'debOrgStructure_id', orgStructureId, 'id'):
            return True
        return False


    def currentTreeItemId(self):
        idx = self.treeItems.currentIndex()
        if idx.isValid():
            return self.modelTree.itemId(idx)

        return None


    def select(self, props):
        table = self.modelTable.table()
        groupId = self.currentGroupId()
        return QtGui.qApp.db.getIdList(table.name(),
                                       'id',
                                       [table['parent_id'].eq(groupId),
                                        table['deleted'].eq(0)],
                                       self.order)


    def currentGroupId(self):
        return self.modelTree.itemId(self.treeItems.currentIndex())


    @pyqtSignature('')
    def on_btnNew_clicked(self):
        dialog = self.getItemEditor()
        try:
            dialog.setGroupId(self.currentGroupId())
            if dialog.exec_():
                itemId = dialog.itemId()
                self.modelTree.cachedRecords = {}
                self.modelTree.update()
                self.renewListAndSetTo(itemId)
        finally:
            dialog.deleteLater()


    def getCurrentItemID(self):
        return self.currentItemId()


    @pyqtSignature('')
    def on_btnEdit_clicked(self):
        itemId = self.currentItemId()
        if itemId:
            dialog = self.getItemEditor()
            try:
                dialog.load(itemId)
                if dialog.exec_():
                    itemId = dialog.itemId()
                    self.modelTree.cachedRecords = {}
                    self.modelTree.update()
                    self.renewListAndSetTo(itemId)
            finally:
                dialog.deleteLater()
        else:
            self.on_btnNew_clicked()


    def getItemEditor(self):
        return COrgStructureEditor(self)


    @pyqtSignature('')
    def on_actDelete_triggered(self):
        def deleteCurrentInternal(item):
            if item:
                children = item.items()
                if children:
                    for x in children:
                        deleteCurrentInternal(x)
                orgStructureId = item.id()
                if orgStructureId:
                    db = QtGui.qApp.db
                    table = db.table('OrgStructure')
                    tableOSHB = db.table('OrgStructure_HospitalBed')
                    hospitalBedIdList = db.getDistinctIdList(tableOSHB, [tableOSHB['id']], [tableOSHB['master_id'].eq(orgStructureId), tableOSHB['deleted'].eq(0)])
                    if hospitalBedIdList:
                        tableOSHBInvolution = db.table('OrgStructure_HospitalBed_Involution')
                        filter = [tableOSHBInvolution['master_id'].inlist(hospitalBedIdList), tableOSHBInvolution['deleted'].eq(0)]
                        db.deleteRecord(tableOSHBInvolution, filter)
                        filter = [tableOSHB['master_id'].eq(orgStructureId), tableOSHB['deleted'].eq(0)]
                        db.deleteRecord(tableOSHB, filter)
                    db.deleteRecord(table, table['id'].eq(orgStructureId))

        if QtGui.QMessageBox.question(self, u'Подтверждение удаления',
                                    u'Удалить элемент и все его дочерние элементы?',
                                    QtGui.QMessageBox.Yes|QtGui.QMessageBox.No,
                                    QtGui.QMessageBox.No
                                    ) == QtGui.QMessageBox.Yes:
            currentIndex = self.treeItems.currentIndex()
            idx = self.modelTree.parent(currentIndex)
            self.saveExpandedState()
            rc = QtGui.qApp.call(self, deleteCurrentInternal,
                (currentIndex.internalPointer(), ))[0]
            if rc:
                self.modelTree.reset()
                self.modelTree.cachedRecords = {}
                self.modelTree.update()
                self.renewListAndSetTo()
                self.restoreExpandedState()
                self.treeItems.setCurrentIndex(idx)


class COrgStructureEditor(Ui_ItemEditorDialog, CItemEditorDialogWithIdentification):
    def __init__(self,  parent):
        self.orgStructureID = parent.getCurrentItemID()
        CItemEditorDialogWithIdentification.__init__(self, parent, 'OrgStructure')
        self.setWindowTitleEx(u'Подразделение')
        self.on_cmbAreaType_currentIndexChanged(0)
        self.on_chkHasHospitalBeds_toggled(False)
        self.cmbParent.setNameField('name')
        self.cmbParent.setAddNone(True)
        self.cmbParent.setFilter('False')
        self.cmbParent.setTable('OrgStructure')
        specialValues = [(-2, u'не определен', u'не определен'),
                         (-1, u'определен',    u'определен')]
        self.cmbService.setTable('rbService', addNone=True, specialValues=specialValues)
        self.cmbQuotaType.setTable('QuotaType', addNone=True, specialValues=specialValues)
        self.cmbTissueType.setTable('rbTissueType', addNone=True, specialValues=specialValues)
        self.cmbOrganisation.setValue(QtGui.qApp.currentOrgId())
        self.cmbNet.setTable(rbNet, True)
        self.cmbChief.setSpecialityPresent(True)
        self.cmbHeadNurse.setSpecialityPresent(None)
        self.KLADRDelegate = CKLADRItemDelegate(self)
        self.StreetDelegate = CStreetItemDelegate(self)
        self.tblAddress.setItemDelegateForColumn(0, self.KLADRDelegate)
        self.tblAddress.setItemDelegateForColumn(1, self.StreetDelegate)
        self.modelHospitalBeds.setInvoluteBedsModel(self.modelInvoluteBeds)
        self.setModels(self.tblAddress, self.modelAddress, self.selectionModelAddress)
        self.setModels(self.tblHospitalBeds, self.modelHospitalBeds, self.selectionModelHospitalBeds)
        self.setModels(self.tblInvoluteBeds, self.modelInvoluteBeds, self.selectionModelInvoluteBeds)
        self.setModels(self.tblJobs, self.modelJobs, self.selectionModelJobs)
        self.setModels(self.tblGaps, self.modelGaps, self.selectionModelGaps)
        self.setModels(self.tblEventTypes, self.modelEventTypes, self.selectionModelEventTypes)
        self.setModels(self.tblActionTypes, self.modelActionTypes, self.selectionModelActionTypes)
        self.setModels(self.tblDisabledAttendance, self.modelDisabledAttendance, self.selectionModelDisabledAttendance)
        self.setModels(self.tblStocks, self.modelStocks, self.selectionModelStocks)
        self.setModels(self.tblEquipments, self.modelEquipments, self.selectionModelEquipments)
        self.setModels(self.tblPlacements, self.modelPlacements, self.selectionModelPlacements)
        self.tblAddress.createPopupMenu([self.actAddEmpty, self.actDuplicate, '-', self.actUp, self.actDown, '-', self.actPopulate,  '-', self.actPrintAddressList])
        self.tblAddress.addPopupDelRow()
        self.tblDisabledAttendance.createPopupMenu([self.actGetParentDisabledAttendance, '-'])

        for tbl in (self.tblHospitalBeds, self.tblInvoluteBeds,
                    self.tblGaps, self.tblEventTypes,
                    self.tblActionTypes, self.tblDisabledAttendance,
                    self.tblStocks, self.tblEquipments):
            tbl.addMoveRow()
            tbl.addPopupSeparator()
            tbl.addPopupDuplicateCurrentRow()
            tbl.addPopupSeparator()
            tbl.addPopupDelRow()
        self.cmbParent.setNameField('name')
        self.cmbParent.setAddNone(True)
        self.cmbParent.setTable('OrgStructure')
        self.cmbOrganisation.setValue(QtGui.qApp.currentOrgId())
        self.cmbNet.setTable(rbNet, True)
        self.cmbChief.setSpecialityPresent(True)
        self.cmbHeadNurse.setSpecialityPresent(None)
        self.KLADRDelegate = CKLADRItemDelegate(self)
        self.StreetDelegate = CStreetItemDelegate(self)
        self.tblAddress.setItemDelegateForColumn(0, self.KLADRDelegate)
        self.tblAddress.setItemDelegateForColumn(1, self.StreetDelegate)
        self.on_cmbAreaType_currentIndexChanged(0)
        self.on_chkHasHospitalBeds_toggled(False)
        self.on_chkHasStocks_toggled(False)
        #WTF?
#        self.connect(self.selectionModelHospitalBeds, SIGNAL('currentChanged(QModelIndex,QModelIndex)'), self.changedInvoluteBeds)


    def preSetupUi(self):
        CItemEditorDialogWithIdentification.preSetupUi(self)
        self.addModels('Address',  CAddressModel(self))
        self.addModels('HospitalBeds',  CHospitalBedsModel(self))
        self.addModels('InvoluteBeds',  CInvoluteBedsModel(self))
        self.addModels('Jobs',  COrgStructureJobsModel(self))
        self.addModels('Gaps',  CGapsModel(self))
        self.addModels('EventTypes',  CEventTypesModel(self))
        self.addModels('ActionTypes',  CActionTypesModel(self))
        self.addModels('DisabledAttendance', CDisabledAttendanceModel(self))
        self.addModels('Stocks', CStocksModel(self))
        self.addModels('Equipments', CEquipmentsModel(self))
        self.addModels('Placements', CPlacementsModel(self))

        self.addObject('actAddEmpty', QtGui.QAction(u'Вставить пустую запись', self))
        self.addObject('actDuplicate', QtGui.QAction(u'Дублировать', self))
        self.addObject('actUp', QtGui.QAction(u'Поднять строку', self))
        self.addObject('actDown', QtGui.QAction(u'Опустить строку', self))
        self.addObject('actPopulate', QtGui.QAction(u'Добавить все подходящие', self))
        self.addObject('actGetParentDisabledAttendance', QtGui.QAction(u'Копировать ограничения из вышестоящего подразделения', self))
        self.addObject('actPrintAddressList', QtGui.QAction(u'Печать', self))


    def postSetupUi(self):
        CItemEditorDialogWithIdentification.postSetupUi(self)
        self.cmbServiceType.insertSpecialValue('-', None)


    def setRecord(self, record):
        CItemEditorDialogWithIdentification.setRecord(self, record)
        self.cmbChief.setOrgStructureId(self.itemId())
        self.cmbHeadNurse.setOrgStructureId(self.itemId())

        setRBComboBoxValue(self.cmbOrganisation, record, 'organisation_id')
        setRBComboBoxValue(self.cmbParent, record, 'parent_id')
        setLineEditValue(self.edtAddress, record, 'address')
        setLineEditValue(self.edtPhone, record, 'phone')
        setComboBoxValue(self.cmbType, record, 'type')
        setRBComboBoxValue(self.cmbNet, record, 'net_id')
        setRBComboBoxValue(self.cmbChief, record, 'chief_id')
        setRBComboBoxValue(self.cmbHeadNurse, record, 'headNurse_id')
        setLineEditValue(self.edtInfisCode, record, 'infisCode')
        setLineEditValue(self.edtBookkeeperCode, record, 'bookkeeperCode')
        setLineEditValue(self.edtInfisInternalCode, record, 'infisInternalCode')
        setLineEditValue(self.edtInfisDepTypeCode, record, 'infisDepTypeCode')
        setLineEditValue(self.edtInfisTariffCode,  record, 'infisTariffCode')
        setLineEditValue(self.edtTfomsCode,  record, 'tfomsCode')
        setComboBoxValue(self.cmbAreaType, record, 'areaType')
        setCheckBoxValue(self.chkHasHospitalBeds, record, 'hasHospitalBeds')
        setLineEditValue(self.edtEmsProfileCode, record, 'emsProfileCode')
        setCheckBoxValue(self.chkHasStocks, record, 'hasStocks')
        setCheckBoxValue(self.chkMainStocks, record, 'mainStocks')
        setCheckBoxValue(self.chkWarnAboutExpirationDateDrugStock, record, 'hasWarnAboutExpirationDateDrug')
        setSpinBoxValue(self.edtWarnAboutExpirationDateDrugStock, record, 'warnAboutExpirationDateDrugDays')
        setCheckBoxValue(self.chkAvailableForExternal, record, 'availableForExternal')
        setTextEditValue(self.edtNote, record, 'note')
        setCheckBoxValue(self.chkInheritEventTypes, record, 'inheritEventTypes')
        setCheckBoxValue(self.chkInheritGaps, record, 'inheritGaps')
        setCheckBoxValue(self.chkInheritActionTypes, record, 'inheritActionTypes')
        setComboBoxValue(self.cmbJobTimelinePeriod,       record, 'timelinePeriod')
        setSpinBoxValue( self.edtJobTimelineCustomLength, record, 'timelineCustomLength')
        setCheckBoxValue(self.chkJobFillRedDays,    record, 'fillRedDays')
        setCheckBoxValue(self.chkFAP, record, 'isFAP')
        self.modelAddress.loadData(self.itemId())
        self.modelHospitalBeds.loadItems(self.itemId())
        self.modelJobs.loadItems(self.itemId(), self.cmbJobTimelinePeriod.currentIndex(), self.edtJobTimelineCustomLength.value())
        self.modelGaps.loadItems(self.itemId())
        self.modelEventTypes.loadItems(self.itemId())
        self.modelActionTypes.loadItems(self.itemId())
        self.modelDisabledAttendance.loadItems(self.itemId())
        self.modelStocks.loadItems(self.itemId())
        self.modelEquipments.loadItems(self.itemId())
        self.modelPlacements.loadItems(self.itemId())


    def getRecord(self):
        record = CItemEditorDialogWithIdentification.getRecord(self)
        getRBComboBoxValue(self.cmbOrganisation, record, 'organisation_id')
        getRBComboBoxValue(self.cmbParent, record, 'parent_id')
        getLineEditValue(self.edtAddress, record, 'address')
        getLineEditValue(self.edtPhone, record, 'phone')
        getComboBoxValue(self.cmbType, record, 'type')
        getRBComboBoxValue(self.cmbNet, record, 'net_id')
        getRBComboBoxValue(self.cmbChief, record, 'chief_id')
        getRBComboBoxValue(self.cmbHeadNurse, record, 'headNurse_id')
        getLineEditValue(self.edtInfisCode, record, 'infisCode')
        getLineEditValue(self.edtBookkeeperCode, record, 'bookkeeperCode')
        getLineEditValue(self.edtInfisInternalCode, record, 'infisInternalCode')
        getLineEditValue(self.edtInfisDepTypeCode, record, 'infisDepTypeCode')
        getLineEditValue(self.edtInfisTariffCode,  record, 'infisTariffCode')
        getLineEditValue(self.edtTfomsCode,  record, 'tfomsCode')
        getComboBoxValue(self.cmbAreaType, record, 'areaType')
        getCheckBoxValue(self.chkHasHospitalBeds, record, 'hasHospitalBeds')
        getLineEditValue(self.edtEmsProfileCode, record, 'emsProfileCode')
        getCheckBoxValue(self.chkHasStocks, record, 'hasStocks')
        getCheckBoxValue(self.chkMainStocks, record, 'mainStocks')
        getCheckBoxValue(self.chkWarnAboutExpirationDateDrugStock, record, 'hasWarnAboutExpirationDateDrug')
        getSpinBoxValue(self.edtWarnAboutExpirationDateDrugStock, record, 'warnAboutExpirationDateDrugDays')
        getCheckBoxValue(self.chkAvailableForExternal, record, 'availableForExternal')
        getTextEditValue(self.edtNote, record, 'note')
        getCheckBoxValue(self.chkInheritEventTypes, record, 'inheritEventTypes')
        getCheckBoxValue(self.chkInheritGaps, record, 'inheritGaps')
        getCheckBoxValue(self.chkInheritActionTypes, record, 'inheritActionTypes')
        getComboBoxValue(self.cmbJobTimelinePeriod,       record, 'timelinePeriod')
        getSpinBoxValue( self.edtJobTimelineCustomLength, record, 'timelineCustomLength')
        getCheckBoxValue(self.chkJobFillRedDays,    record, 'fillRedDays')
        getCheckBoxValue(self.chkFAP, record, 'isFAP')
        return record


    def saveInternals(self, id):
        CItemEditorDialogWithIdentification.saveInternals(self, id)
        self.modelAddress.saveData(id)
        self.modelHospitalBeds.saveItems(id)
        self.modelJobs.saveItems(id)
        self.modelGaps.saveItems(id)
        self.modelEventTypes.saveItems(id)
        self.modelActionTypes.saveItems(id)
        self.modelDisabledAttendance.saveItems(id)
        self.modelStocks.saveItems(id)
        self.modelEquipments.saveItems(id)
        self.modelPlacements.saveItems(id)


    def checkDataEntered(self):
        result = CItemEditorDialogWithIdentification.checkDataEntered(self)
        result = result and (self.cmbOrganisation.value()
                             or self.checkInputMessage(u'организацию', False, self.cmbOrganisation))
        result = result and self.checkDisabledAttendance()
        return result


    def checkDisabledAttendance(self):
        attachTypeIdList = []
        for row, record in enumerate(self.modelDisabledAttendance.items()):
            attachTypeId = forceRef(record.value('attachType_id'))
            if attachTypeId not in attachTypeIdList:
                attachTypeIdList.append(attachTypeId)
            else:
                QtGui.QMessageBox.warning( self,
                                           u'Внимание!',
                                           u'Тип прикрепления повторяется!',
                                           QtGui.QMessageBox.Ok,
                                           QtGui.QMessageBox.Ok)
                self.setFocusToWidget(self.tblDisabledAttendance, row, record.indexOf('attachType_id'))
                return False
        return True


    def setGroupId(self, id):
        if id:
            orgId = forceRef(QtGui.qApp.db.translate('OrgStructure', 'id', id, 'organisation_id'))
            self.groupId = id
            self.cmbOrganisation.setValue(orgId)
            self.cmbParent.setValue(forceRef(id))


    def updateAvailableIdList(self):
        cond = self.filterConditions()
        self.loadActionTypesItems(cond)


    def loadActionTypesItems(self, filter):
        model = self.tblActionTypes.model()
        db = QtGui.qApp.db
        table = db.table('ActionType')
        tableOSAT = db.table('OrgStructure_ActionType')
        queryTable = table.innerJoin(tableOSAT, tableOSAT['actionType_id'].eq(table['id']))
        cols = []
        for col in model._cols:
            if not col.external():
                cols.append('OrgStructure_ActionType.' + col.fieldName())
        cols.append('OrgStructure_ActionType.' + model._idFieldName)
        cols.append('OrgStructure_ActionType.' + model._masterIdFieldName)
        if model._idxFieldName:
            cols.append('OrgStructure_ActionType.' + model._idxFieldName)
        table = model._table
        if table.hasField('deleted'):
            filter.append(table['deleted'].eq(0))
        if model._idxFieldName:
            order = ['OrgStructure_ActionType.' + model._idxFieldName, 'OrgStructure_ActionType.' + model._idFieldName]
        else:
            order = ['OrgStructure_ActionType.' + model._idFieldName]
        model._items = db.getRecordList(queryTable, cols, filter, order)
        model.reset()


    def filterConditions(self):
        db = QtGui.qApp.db
        tables = [(db.table('ActionType_Service'), 'service_id'),
                  (db.table('ActionType_QuotaType'), 'quotaType_id'),
                  (db.table('ActionType_TissueType'), 'tissueType_id')]
        serviceId = self.cmbService.value()
        quotaTypeId = self.cmbQuotaType.value()
        tissueTypeId = self.cmbTissueType.value()
        tableActionType = db.table('ActionType')
        tableOSAT = db.table('OrgStructure_ActionType')
        cond = [tableOSAT['master_id'].eq(self._id)]
        for idx, id in enumerate([serviceId, quotaTypeId, tissueTypeId]):
            table, fieldName = tables[idx]
            condTmp = [table['master_id'].eq(tableActionType['id'])]
            if id > 0:
                condTmp.append(table[fieldName].eq(id))
                cond.append(db.existsStmt(table, condTmp))
            elif id == -1:
                cond.append(db.existsStmt(table, condTmp))
            elif id == -2:
                cond.append(db.notExistsStmt(table, condTmp))

        serviceType = self.cmbServiceType.value()
        actionTypeCode = self.edtActionTypeCode.text()
        actionTypeName = self.edtActionTypeName.text()
        if serviceType:
            cond.append(tableActionType['serviceType'].eq(serviceType))
        if actionTypeCode:
            cond.append(tableActionType['code'].contain(actionTypeCode))
        if actionTypeName:
            cond.append(tableActionType['name'].contain(actionTypeName))
        return cond


    @pyqtSignature('int')
    def on_cmbService_currentIndexChanged(self, index):
        self.updateAvailableIdList()


    @pyqtSignature('int')
    def on_cmbQuotaType_currentIndexChanged(self, index):
        self.updateAvailableIdList()


    @pyqtSignature('int')
    def on_cmbTissueType_currentIndexChanged(self, index):
        self.updateAvailableIdList()


    @pyqtSignature('int')
    def on_cmbServiceType_currentIndexChanged(self, index):
        self.updateAvailableIdList()


    @pyqtSignature('QString')
    def on_edtActionTypeCode_textChanged(self, text):
        self.updateAvailableIdList()


    @pyqtSignature('QString')
    def on_edtActionTypeName_textChanged(self, text):
        self.updateAvailableIdList()


    @pyqtSignature('int')
    def on_cmbOrganisation_currentIndexChanged(self, index):
        orgId = self.cmbOrganisation.value()
        if orgId:
            self.cmbParent.setEnabled(False)
            self.cmbParent.setFilter('organisation_id=%d'%orgId)
        else:
            self.cmbParent.setEnabled(False)
            self.cmbParent.setFilter('organisation_id IS NULL')


    @pyqtSignature('')
    def on_btnSelectOrganisation_clicked(self):
        orgId = selectOrganisation(self, self.cmbOrganisation.value(), False)
        self.cmbOrganisation.updateModel()
        if orgId:
            self.cmbOrganisation.setValue(orgId)


    @pyqtSignature('int')
    def on_cmbAreaType_currentIndexChanged(self, index):
        isArea = index > 0
        self.tabWidget.setTabEnabled(1, isArea)
        self.tblAddress.setEnabled(isArea)


    @pyqtSignature('bool')
    def on_chkHasHospitalBeds_toggled(self, checked):
        self.tabWidget.setTabEnabled(3, checked)
        self.tblHospitalBeds.setEnabled(checked)
        self.tblInvoluteBeds.setEnabled(checked)


    @pyqtSignature('bool')
    def on_chkHasStocks_toggled(self, checked):
        self.tabWidget.setTabEnabled(self.tabWidget.indexOf(self.tabStocks), checked)
        self.tblStocks.setEnabled(checked)
        self.chkMainStocks.setEnabled(checked)


    def updateSchedulePeriod(self):
        period       = self.cmbJobTimelinePeriod.currentIndex()
        customLength = self.edtJobTimelineCustomLength.value()
        self.modelJobs.setPeriod(period, customLength)


    @pyqtSignature('int')
    def on_cmbJobTimelinePeriod_currentIndexChanged(self, index):
        enableCustomLength = index == 2
        self.lblJobTimelineCustomLength.setEnabled(enableCustomLength)
        self.edtJobTimelineCustomLength.setEnabled(enableCustomLength)
        self.updateSchedulePeriod()


    @pyqtSignature('int')
    def on_edtJobTimelineCustomLength_valueChanged(self, i):
        self.updateSchedulePeriod()


    @pyqtSignature('')
    def on_tblAddress_popupMenuAboutToShow(self):
        currentIndex = self.tblAddress.currentIndex()
        row = currentIndex.row()
        rows = len(self.modelAddress.items)
        self.actAddEmpty.setEnabled(rows>0 and row>=0)
        self.actDuplicate.setEnabled(rows>0 and row>=0)
        self.actUp.setEnabled(rows>0 and row>0)
        self.actDown.setEnabled(rows>0 and row>=0 and row<rows-1)
        self.actPopulate.setEnabled(self.modelAddress.canPopulate(row))
        self.actPrintAddressList.setEnabled(rows>0)


    @pyqtSignature('')
    def on_actAddEmpty_triggered(self):
        row = self.tblAddress.currentIndex().row()
        if row>=0:
            self.modelAddress.addEmptyRow(row)


    @pyqtSignature('')
    def on_actDuplicate_triggered(self):
        currentIndex = self.tblAddress.currentIndex()
        row = currentIndex.row()
        if row>=0:
            self.modelAddress.duplicateRow(row)
            self.tblAddress.setCurrentIndex(currentIndex.sibling(row+1, currentIndex.column()))


    @pyqtSignature('')
    def on_actUp_triggered(self):
        currentIndex = self.tblAddress.currentIndex()
        row = currentIndex.row()
        if row>=1:
            self.modelAddress.upRow(row)
            self.tblAddress.setCurrentIndex(currentIndex.sibling(row-1, currentIndex.column()))


    @pyqtSignature('')
    def on_actDown_triggered(self):
        currentIndex = self.tblAddress.currentIndex()
        row = currentIndex.row()
        if row>=0:
            self.modelAddress.downRow(row)
            self.tblAddress.setCurrentIndex(currentIndex.sibling(row+1, currentIndex.column()))


    @pyqtSignature('')
    def on_actPopulate_triggered(self):
        currentIndex = self.tblAddress.currentIndex()
        row = currentIndex.row()
        self.modelAddress.populate(row)


    @pyqtSignature('')
    def on_actPrintAddressList_triggered(self):
        self.tblAddress.setReportHeader(u'Список адресов Зоны обслуживания')
        self.tblAddress.setReportDescription(self.getDescription())
        self.tblAddress.printContent()


    @pyqtSignature('QModelIndex,QModelIndex')
    def on_selectionModelHospitalBeds_currentChanged(self, current, previous):
        row = current.row()
        involuteBeds = self.modelHospitalBeds.involuteBeds(row)
        self.modelInvoluteBeds.setItems(involuteBeds)
        if self.modelHospitalBeds._cols[current.column()]._fieldName == u'profile_id':
            items = self.modelHospitalBeds.items()
            if row >= 0 and row < len(items):
                record = items[row]
            else:
                record = None
            if record:
                begDate = forceDate(record.value('begDate'))
                endDate = forceDate(record.value('endDate'))
            else:
                begDate = None
                endDate = QDate.currentDate()
            if not begDate and not endDate:
                endDate = QDate.currentDate()
            filter = (u'(rbHospitalBedProfile.endDate IS NULL OR rbHospitalBedProfile.endDate >= %s)'%QtGui.qApp.db.formatDate(endDate if endDate else begDate)) if (begDate or endDate) else u''
            self.modelHospitalBeds._cols[current.column()].setFilter(filter)


    @pyqtSignature('')
    def on_actGetParentDisabledAttendance_triggered(self):
        QtGui.qApp.setWaitCursor()
        try:
            orgStructureId = self.itemId()
            if orgStructureId:
                db = QtGui.qApp.db
                tableOrgStructure = db.table('OrgStructure')
                tableOSDA = db.table('OrgStructure_DisabledAttendance')
                recordParentId = db.getRecordEx(tableOrgStructure, [tableOrgStructure['parent_id']], [tableOrgStructure['deleted'].eq(0), tableOrgStructure['id'].eq(orgStructureId)])
                if recordParentId:
                    parentId = forceRef(recordParentId.value('parent_id'))
                    if parentId:
                        attachTypeIdList = []
                        for row, recordItem in enumerate(self.modelDisabledAttendance.items()):
                            attachTypeId = forceRef(recordItem.value('attachType_id'))
                            if attachTypeId not in attachTypeIdList:
                                attachTypeIdList.append(attachTypeId)
                        records = db.getRecordList(tableOSDA, '*', [tableOSDA['master_id'].eq(parentId)])
                        for record in records:
                            attachTypeId = forceRef(record.value('attachType_id'))
                            if attachTypeId and (attachTypeId not in attachTypeIdList):
                                orgStructureId = forceRef(record.value('master_id'))
                                disabledType = forceInt(record.value('disabledType'))
                                self.addRowDisabledAttendance(orgStructureId, attachTypeId, disabledType)
        finally:
            QtGui.qApp.restoreOverrideCursor()


    def addRowDisabledAttendance(self, orgStructureId, attachTypeId, disabledType):
        newRecord = QtGui.qApp.db.table('OrgStructure_DisabledAttendance').newRecord()
        newRecord.setValue('master_id', QVariant(orgStructureId))
        newRecord.setValue('attachType_id', QVariant(attachTypeId))
        newRecord.setValue('disabledType', QVariant(disabledType))
        self.modelDisabledAttendance.items().append(newRecord)
        index = QModelIndex()
        cnt = len(self.modelDisabledAttendance.items())
        self.modelDisabledAttendance.beginInsertRows(index, cnt, cnt)
        self.modelDisabledAttendance.insertRows(cnt, 1, index)
        self.modelDisabledAttendance.endInsertRows()


    def getDescription(self):
        reportDescription = u'Подразделение: '+ getOrgStructureFullName(self._id) + u'\n'
        currentPersonId = QtGui.qApp.userId
        currentPerson = forceString(QtGui.qApp.db.translate('vrbPerson', 'id', currentPersonId, 'name'))
        reportDescription += u'Отчет составил: '+ currentPerson + u'\n'
        reportDescription += u'Отчет составлен: '+ forceString(QDateTime.currentDateTime()) + u'\n'
        return reportDescription


#############################################################################

class CAddressModel(QAbstractTableModel):
    headers = [ u'город', u'улица', u'дом', u'корпус', u'первая кв.', u'последняя кв.']
    def __init__(self, parent):
        QAbstractTableModel.__init__(self, parent)
        self.items = []


    def cols(self):
        self._cols = [CCol(u'Город',     ['KLADRCode'], 20, 'l'),
                      CCol(u'Улица',                ['KLADRStreetCode'], 20, 'l'),
                      CCol(u'Дом',               ['number'], 20, 'l'),
                      CCol(u'Корпус',               ['corpus'], 20, 'l'),
                      CCol(u'Первая Кв.',      ['firstFlat'], 20, 'l'),
                      CCol(u'Последняя Кв.',         ['lastFlat'], 20, 'l'),
                      ]
        return self._cols


    def columnCount(self, index = None):
        return 6


    def rowCount(self, index = None):
        return len(self.items)+1


    def flags(self, index):
#        column = index.column()
#        flags = self.__cols[column].flags()
#        if self.cellReadOnly(index):
#            flags = flags & (~Qt.ItemIsEditable) & (~Qt.ItemIsUserCheckable)
#        return flags
        return Qt.ItemIsSelectable|Qt.ItemIsEnabled|Qt.ItemIsEditable


    def canRemoveRow(self,  row):
        return True


    def confirmRemoveRow(self, view, row, multiple=False):
        return True


    def headerData(self, section, orientation, role = Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return QVariant(CAddressModel.headers[section])
        return QVariant()


    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        row = index.row()
        if row<len(self.items):
            if role == Qt.EditRole:
                return toVariant(self.items[row][column])

            if role == Qt.DisplayRole:
                if column == 0:
                    code = self.items[row][column]
                    return toVariant(getCityName(code) if code else None)
                if column == 1:
                    code = self.items[row][column]
                    return toVariant(getStreetName(code) if code else None)
                else:
                    return toVariant(self.items[row][column])
        elif row == len(self.items):
            if role == Qt.EditRole:
                if column == 0:
                    return toVariant(QtGui.qApp.defaultKLADR())
        return QVariant()


    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.EditRole:
            column = index.column()
            row = index.row()
            if row == len(self.items):
                if value.isNull():
                    return False
                self.items.append(self.getEmptyItem())
                itemsCnt = len(self.items)
                index = QModelIndex()
                self.beginInsertRows(index, itemsCnt, itemsCnt)
                self.insertRows(itemsCnt, 1, index)
                self.endInsertRows()
            item = self.items[row]
            if column in (0, 1, 2, 3):
                itemValue = forceStringEx(value)
            else:
                itemValue = forceInt(value)
            if item[column] != itemValue:
                item[column] = itemValue
                self.emitCellChanged(row, column)
                if column == 0:
                    item[1] = ''
                    self.emitCellChanged(row, 1)
                return True
        return False


    @classmethod
    def getEmptyItem(cls):
        return [ '',  '',  '',  '',  0,  0]


    def saveData(self, masterId):
        db = QtGui.qApp.db
        tableAddress = db.table('OrgStructure_Address')
        idList = []
        for item in self.items:
            houseInfo = {'KLADRCode':item[0],
                         'KLADRStreetCode':item[1],
                         'number':item[2],
                         'corpus':item[3],
                        }
            houseId = getHouseId(houseInfo)
            record = tableAddress.newRecord()
            record.setValue('master_id',  toVariant(masterId))
            record.setValue('house_id',   toVariant(houseId))
            record.setValue('firstFlat',  toVariant(item[4]))
            record.setValue('lastFlat',   toVariant(item[5]))
            idList.append(db.insertRecord(tableAddress, record))
        db.deleteRecord(tableAddress,
                 [ tableAddress['master_id'].eq(masterId),
                   'NOT ('+tableAddress['id'].inlist(idList)+')'])


    def loadData(self, masterId):
        if not masterId:
            return
        db = QtGui.qApp.db
        tableAddress = db.table('OrgStructure_Address')
        tableHouse   = db.table('AddressHouse')
        table = tableAddress.leftJoin(tableHouse, tableAddress['house_id'].eq(tableHouse['id']))
        records = db.getRecordList(table, [tableHouse['KLADRCode'],
                                           tableHouse['KLADRStreetCode'],
                                           tableHouse['number'],
                                           tableHouse['corpus'],
                                           tableAddress['firstFlat'],
                                           tableAddress['lastFlat']
                                           ], tableAddress['master_id'].eq(masterId), tableAddress['id'].name())
        for record in records:
            item = [ forceString(record.value('KLADRCode')),
                     forceString(record.value('KLADRStreetCode')),
                     forceString(record.value('number')),
                     forceString(record.value('corpus')),
                     forceInt(record.value('firstFlat')),
                     forceInt(record.value('lastFlat')),
                   ]
            self.items.append(item)
        self.reset()


    def canPopulate(self, row):
        if 0<=row<len(self.items):
            KLADRCode = self.items[row][0]
            KLADRStreetCode = self.items[row][1]
            if KLADRCode != '' and  KLADRStreetCode == '':
                db = QtGui.qApp.db
                table = db.table('kladr.STREET')
                count = db.getCount(table, where=table['CODE'].like(KLADRCode[:-2]+'%00'))
                if count > 10:
                    return False
            return True
        return False


    def addEmptyRow(self, row):
        self.beginInsertRows(QModelIndex(), row, row)
        self.items.insert(row, self.getEmptyItem())
        self.endInsertRows()


    def duplicateRow(self, row):
        self.beginInsertRows(QModelIndex(), row, row)
        self.items.insert(row, [x for x in self.items[row]])
        self.endInsertRows()


    def upRow(self, row):
        item = self.items[row]
        del self.items[row]
        self.items.insert(row-1, item)
        indexLT = self.index(row-1, 0)
        indexRB = self.index(row, self.columnCount()-1)
        self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), indexLT, indexRB)


    def downRow(self, row):
        item = self.items[row]
        del self.items[row]
        self.items.insert(row+1, item)
        indexLT = self.index(row, 0)
        indexRB = self.index(row+1, self.columnCount()-1)
        self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), indexLT, indexRB)


    def removeRows(self, row, count, parentIndex = QModelIndex()):
        if 0<=row and row+count<=len(self.items):
            self.beginRemoveRows(parentIndex, row, row+count-1)
            del self.items[row:row+count]
            self.endRemoveRows()
            return True
        else:
            return False


    def emitCellChanged(self, row, column):
        index = self.index(row, column)
        self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index, index)


    @classmethod
    def _populateCorpuses(cls, item, newItems):
        db = QtGui.qApp.db

        KLADRCode = item[0]
        KLADRStreetCode = item[1]
        number = item[2]
        KLADRHouseCodeMask = (KLADRStreetCode[:-2] or KLADRCode[:-2]).ljust(15, '0') + '%'

        table = db.table('kladr.DOMA')
        records = db.getRecordList(table,
                                   'KORP',
                                   [ table['NAME'].eq(number),
                                     table['CODE'].like(KLADRHouseCodeMask),
                                   ]
                                  )
        if records:
            corpuses = naturalSorted([ forceString(record.value('KORP')) for record in records ])
        else:
            corpuses = ['']

        for corpus in corpuses:
            newItem = [ KLADRCode, KLADRStreetCode, number,  corpus,  0,  0]
            newItems.append(newItem)


    @classmethod
    def _populateNumbers(cls, item, newItems):
        db = QtGui.qApp.db

        KLADRCode = item[0]
        KLADRStreetCode = item[1]
        KLADRHouseCodeMask = (KLADRStreetCode[:-2] or KLADRCode[:-2]).ljust(15, '0') + '%'

        table = db.table('kladr.DOMA')
        records = db.getRecordList(table,
                                   'flatHouseList',
                                   table['CODE'].like(KLADRHouseCodeMask),
                                  )
        if records:
            numbers = []
            for record in records:
                numbers.extend( forceString(record.value('flatHouseList')).split(',') )
        else:
            numbers = ['']

        for number in naturalSorted(numbers):
            partialItem = [KLADRCode, KLADRStreetCode, number, '',  0,  0]
            cls._populateCorpuses(partialItem, newItems)


    @classmethod
    def _populateStreets(cls, item, newItems):
        db = QtGui.qApp.db

        KLADRCode = item[0]

        table = db.table('kladr.STREET')
        records = db.getRecordList(table,
                                   'CODE',
                                   table['CODE'].like(KLADRCode[:-2]+'%00'),
                                   'NAME'
                                  )
        if records:
            for record in records:
                KLADRStreetCode = forceString(record.value('CODE'))
                partialItem = [KLADRCode, KLADRStreetCode, '', '',  0,  0]
                cls._populateNumbers(partialItem, newItems)
        else:
            newItems.append(item) # ничего нет, можно не париться...


    def populate(self, row):
        if not self.canPopulate(row):
            return
        item = self.items[row]
        KLADRStreetCode = item[1]
        number = item[2]
        corpus = item[3]
        newItems = []
        if KLADRStreetCode == '':
            self._populateStreets(item, newItems)
        elif number == '':
            self._populateNumbers(item, newItems)
        elif corpus == '':
            self._populateCorpuses(item, newItems)
        else:
            newItems = [item]
        if [item] == newItems:
            return
        else:
            self.beginInsertRows(QModelIndex(), row+1,  row+len(newItems))
            self.items[row+1:row+1] = newItems
            self.endInsertRows()
            self.beginRemoveRows(QModelIndex(), row, row)
            del self.items[row]
            self.endRemoveRows()


class CKLADRItemDelegate(QtGui.QItemDelegate):
    def __init__(self, parent=None):
        QtGui.QItemDelegate.__init__(self, parent)


    def createEditor(self, parent, option, index):
        editor = CKLADRComboBox(parent)
        return editor


    def setEditorData(self, editor, index):
        model  = index.model()
        KLADRCode = model.data(index, Qt.EditRole)
        editor.setCode(forceString(KLADRCode))


    def setModelData(self, editor, model, index):
        model.setData(index, toVariant(editor.code()))



class CStreetItemDelegate(QtGui.QItemDelegate):
    def __init__(self, parent=None):
        QtGui.QItemDelegate.__init__(self, parent)


    def createEditor(self, parent, option, index):
        editor = CStreetComboBox(parent)
        return editor


    def setEditorData(self, editor, index):
        model  = index.model()
        code = model.data(index.sibling(index.row(), index.column()-1), Qt.EditRole)
        streetCode = model.data(index, Qt.EditRole)
        editor.setCity(forceString(code))
        editor.setCode(forceString(streetCode))

    def setModelData(self, editor, model, index):
        model.setData(index, toVariant(editor.code()))


class CRBGapsInDocTableCol(CRBInDocTableCol):
    def setFilter(self, filter):
        self.filter  = filter


class CGapsModel(CInDocTableModel):
    def __init__(self, parent):
        self.orgStructureID = parent.orgStructureID
        CInDocTableModel.__init__(self, 'OrgStructure_Gap', 'id', 'master_id', parent)
        self.addCol(CTimeInDocTableCol(u'Начало',   'begTime', 15))
        self.addCol(CTimeInDocTableCol(u'Окончание', 'endTime', 15))
        self.addCol(CRBGapsInDocTableCol(u'Специальность', 'speciality_id', 10, 'rbSpeciality', preferredWidth=150))
        self.addCol(CRBGapsInDocTableCol(u'Сотрудник', 'person_id', 20, 'vrbPersonWithSpeciality', preferredWidth=150))
        self.cols()[2].setFilter(u'id in(select speciality_id from vrbPersonWithSpeciality where retireDate is null and orgStructure_id in(select id from OrgStructure where id=%s))' % self.orgStructureID)
        self.cols()[3].setFilter(u'retireDate is null and orgStructure_id = %s' % self.orgStructureID)


    def setData(self, index, value, role=Qt.EditRole):
        column = index.column()
        if not variantEq(self.data(index, role), value):
            if column == 2: # специальность
                specialityId = forceRef(value)
                if not specialityId:
                    self.cols()[3].setFilter(u'')
                else:
                    self.cols()[3].setFilter(u'retireDate is null and orgStructure_id = %s and speciality_id = %s' % (self.orgStructureID, specialityId))
                result = CInDocTableModel.setData(self, index, value, role)
                return result
            if column == 3: # сотрудник
                personId = forceRef(value)
                if not personId:
                    self.cols()[2].setFilter(u'')
                else:
                    self.cols()[2].setFilter(u'id in(select speciality_id from vrbPersonWithSpeciality where retireDate is null and orgStructure_id in(select id from OrgStructure where id=%s))' % self.orgStructureID)
                result = CInDocTableModel.setData(self, index, value, role)
                return result
            return CInDocTableModel.setData(self, index, value, role)
        else:
            return True


class CEventTypesModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'OrgStructure_EventType', 'id', 'master_id', parent)
        self.addCol(CEnumInDocTableCol(u'Первичность', 'isPrimary', 20, [u'Не задано', u'Первичный', u'Повторный', u'Актив']))
        self.addCol(CRBInDocTableCol(u'Тип', 'eventType_id', 20, 'EventType', filter="deleted=0 AND isActive = 1"))


class CActionTypesModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'OrgStructure_ActionType', 'id', 'master_id', parent)
        self.addCol(CActionTypeTableCol(u'Тип', 'actionType_id', 20, None, classesVisible=True))
        self.addCol(CBoolInDocTableCol(u'Предпочтение', 'isPreferable', 3))


    def getActionTypeCluster(self, actionTypeId):
        db = QtGui.qApp.db
        tableActionType = db.table('ActionType')
        result = db.getLeafes(tableActionType,
                              'group_id',
                              actionTypeId,
                              tableActionType['deleted'].eq(0)
                             )
        return sorted(result) if result else [actionTypeId]


    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.EditRole:
            noWriteList = True
            column = index.column()
            row = index.row()
            if row == len(self._items):
                if value.isNull():
                    return False
                if column == self.getColIndex('actionType_id'):
                    outWriteList, noWriteList = self.writeActionTypeIdList(forceRef(value), row, column)
                    if outWriteList:
                        return True
                self._items.append(self.getEmptyRecord())
                count = len(self._items)
                rootIndex = QModelIndex()
                self.beginInsertRows(rootIndex, count, count)
                self.insertRows(count, 1, rootIndex)
                self.endInsertRows()
            record = self._items[row]
            col = self._cols[column]
            record.setValue(col.fieldName(), value)
            self.emitCellChanged(row, column)
            if noWriteList and column == self.getColIndex('actionType_id'):
                outWriteList, noWriteList = self.writeActionTypeIdList(forceRef(value), row, column, True)
                if outWriteList:
                    return True
            return True
        return CInDocTableModel.setData(self, index, value, role)


    def writeActionTypeIdList(self, actionTypeId, row, column, these = False):
        if actionTypeId:
            actionTypeIdList = self.getActionTypeCluster(actionTypeId)
            if these:
                actionTypeIdList = list(set(actionTypeIdList)-set([actionTypeId]))
            else:
                if actionTypeId not in actionTypeIdList:
                    actionTypeIdList.insert(0, actionTypeId)
            if len(actionTypeIdList) > 1:
                if QtGui.QMessageBox.warning(None,
                   u'Внимание!',
                   u'Добавить группу действий?',
                   QtGui.QMessageBox.Ok|QtGui.QMessageBox.Cancel,
                   QtGui.QMessageBox.Cancel) == QtGui.QMessageBox.Ok:
                    for atId in actionTypeIdList:
                        self._items.append(self.getEmptyRecord())
                        count = len(self._items)
                        rootIndex = QModelIndex()
                        self.beginInsertRows(rootIndex, count, count)
                        self.insertRows(count, 1, rootIndex)
                        self.endInsertRows()
                        record = self._items[count-1]
                        col = self._cols[column]
                        record.setValue(col.fieldName(), toVariant(atId))
                        self.emitCellChanged(count-1, column)
                    return True, False
                else:
                    return False, False
            else:
                return False, False
        return False, False


class CDisabledAttendanceModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'OrgStructure_DisabledAttendance', 'id', 'master_id', parent)
        self.addCol(CRBInDocTableCol(u'Тип прикрепления', 'attachType_id', 20, 'rbAttachType', filter='temporary != 0', showFields=CRBComboBox.showCodeAndName))
        self.addCol(CEnumInDocTableCol(u'Способ ограничения', 'disabledType', 3, [u'мягко', u'строго', u'запрет']))


class CStocksModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'OrgStructure_Stock', 'id', 'master_id', parent)
        self.addCol(CNomenclatureInDocTableCol(u'ЛСиИМН', 'nomenclature_id', 50, showFields = CRBComboBox.showName))
        self.addCol(CRBInDocTableCol(    u'Тип финансирования', 'finance_id', 20, 'rbFinance'))
        self.addCol(CFloatInDocTableCol( u'Гарантийный запас',  'constrainedQnt', 20))
        self.addCol(CFloatInDocTableCol( u'Точка заказа',       'orderQnt', 20))


#############################################################################


class CRBEquipmentCol(CRBInDocTableCol):
    def createEditor(self, parent):
        editor = CEquipmentComboBox(parent)
        editor.setTable(self.tableName, addNone=self.addNone, filter=self.filter)
        editor.setShowFields(self.showFields)
        editor.setPreferredWidth(self.preferredWidth)
        return editor


class CEquipmentsModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'OrgStructure_Equipment', 'id', 'master_id', parent)
        self.addCol(CRBEquipmentCol(  u'Оборудование',  'equipment_id',   15, 'rbEquipment', showFields=CRBComboBox.showCodeAndName))
        self.addCol(CIntInDocTableCol(  u'Приоритет',  'priority',   5, low=0,  high=99))


#############################################################################


class CPlacementsModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'OrgStructure_Placement', 'id', 'master_id', parent)
        self.addCol(CInDocTableCol(u'Код помещения', 'code', 15))
        self.addCol(CInDocTableCol(u'Наименование помещения', 'name', 35))


class COrgStructureTableModel(CTableModel):
    def __init__(self, parent, cols, tableName):
        CTableModel.__init__(self, parent, cols, tableName)


    def removeItem(self, orgStructureId):
        if orgStructureId:
            if orgStructureId:
                db = QtGui.qApp.db
                table = db.table('OrgStructure')
                tableOSHB = db.table('OrgStructure_HospitalBed')
                hospitalBedIdList = db.getDistinctIdList(tableOSHB, [tableOSHB['id']], [tableOSHB['master_id'].eq(orgStructureId), tableOSHB['deleted'].eq(0)])
                if hospitalBedIdList:
                    tableOSHBInvolution = db.table('OrgStructure_HospitalBed_Involution')
                    filter = [tableOSHBInvolution['master_id'].inlist(hospitalBedIdList), tableOSHBInvolution['deleted'].eq(0)]
                    db.deleteRecord(tableOSHBInvolution, filter)
                    filter = [tableOSHB['master_id'].eq(orgStructureId), tableOSHB['deleted'].eq(0)]
                    db.deleteRecord(tableOSHB, filter)
                db.deleteRecord(table, table['id'].eq(orgStructureId))


    def removeRow(self, row, parent = QModelIndex()):
        if self._idList and 0<=row<len(self._idList):
            itemId = self._idList[row]
            if self.canRemoveItem(itemId):
                QtGui.qApp.setWaitCursor()
                try:
                    db = QtGui.qApp.db
                    table = self._table
                    db.transaction()
                    try:
                        self.removeItem(itemId)
                        db.commit()
                    except:
                        db.rollback()
                        raise
                    self.beginRemoveRows(parent, row, row)
                    del self._idList[row]
                    self.endRemoveRows()
                    self.emitItemsCountChanged()
                    return True
                finally:
                    QtGui.qApp.restoreOverrideCursor()
        return False
