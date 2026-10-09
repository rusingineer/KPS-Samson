# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2026 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################


from PyQt4 import QtGui, QtSql
from PyQt4.QtCore import Qt, QMimeData, QObject, QVariant, pyqtSignature, SIGNAL, QModelIndex, QEvent, QDate, QPoint
from PyQt4.QtGui import QFont

from library.AgeSelector                   import composeAgeSelector, parseAgeSelector
from library.calc                          import checkExpr, isIdentifier
from library.crbcombobox                   import CRBModelDataCache, CRBComboBox, CRBModel
from library.DialogBase                    import CDialogBase
from library.HierarchicalItemsListDialog   import CHierarchicalItemsListDialog
from library.IdentificationModel           import CIdentificationModel, checkIdentification
from library.InDocTable                    import CInDocTableModel, CBoolInDocTableCol, CEnumInDocTableCol, CFloatInDocTableCol, CInDocTableCol, CIntInDocTableCol, CRBInDocTableCol, CSelectStrInDocTableCol, CRBSearchInDocTableCol, CRBTestSearchInDocTableCol
from library.database import CTableRecordCache
from library.interchange                   import setDateEditValue, getDateEditValue, getCheckBoxValue, getComboBoxValue, getLineEditValue, getRBComboBoxValue, getSpinBoxValue, setCheckBoxValue, setComboBoxValue, setLineEditValue, setRBComboBoxValue, setSpinBoxValue, getDoubleBoxValue, setDoubleBoxValue
from library.ItemsListDialog               import CItemEditorBaseDialog
from library.TableModel                    import CTableModel, CEnumCol, CRefBookCol, CTextCol, CDateCol
from library.TreeModel                     import CDragDropDBTreeModelWithClassItems
from library.Utils                         import addDotsEx, forceBool, forceDouble, forceInt, forceRef, forceString, forceStringEx, \
    formatRecordsCount, formatRecordsCountInt, toVariant, trim, formatNum, formatNum1, agreeNumberAndWord, forceDate, \
    ActionTypeServiceMixin

from Events.Action                         import CActionType, CActionTypeCache
from Events.ActionProperty                 import CActionPropertyValueTypeRegistry
from Events.ActionPropertyTemplateComboBox import CActionPropertyTemplateComboBox
from Events.ActionTypeComboBox             import CActionTypeTableCol
from Orgs.OrgStructureCol                  import COrgStructureInDocTableCol
from RefBooks.Service.SelectService        import selectService
from Stock.NomenclatureComboBox            import CNomenclatureInDocTableCol
from Users.Rights                          import urDeleteActionTypeProperties
from library.IdentificationModel           import CAccountingSystemComboBox
import types
from RefBooks.Service.RBServiceComboBox    import CRBServiceInDocTableCol
from library.ClientRecordProperties import CRecordProperties

from .ActionPropertyTypeInDocTableView     import actionPropertyTypeIsUsed

from .GroupActionTypeEditor                import CGroupActionTypeEditor


from .Ui_ActionTypeListDialog import Ui_ActionTypeListDialog
from .Ui_ActionTypeEditor     import Ui_ActionTypeEditorDialog
from .Ui_ActionTypeFindDialog import Ui_ActionTypeFindDialog


SexList = ['', u'М', u'Ж']


def formatCountSelectedRows(count):
    return u';  выделено ' + formatRecordsCountInt(count)


def isSelectable(modelIndex):
    flags = modelIndex.flags()
    return flags & Qt.ItemIsEnabled and flags & Qt.ItemIsSelectable


class CActionTypeList(Ui_ActionTypeListDialog, CHierarchicalItemsListDialog):
    mimeTypeActionPropertyIdList = 'application/x-s11/actionpropertyidlist'

    unitNameTuple = (u'строка', u'строки', u'строк')
    propNameTuple = (u'свойство', u'свойства', u'свойств')

    def __init__(self, parent=None):
        CHierarchicalItemsListDialog.__init__(self, parent, [
            CEnumCol(u'Класс', ['class'], [u'статус', u'диагностика', u'лечение', u'прочие мероприятия'], 10),
            CRefBookCol(u'Группа',   ['group_id'], 'ActionType', 10),
            CTextCol(   u'Код',          ['code'], 20),
            CTextCol(   u'Наименование', ['name'], 40),
            CEnumCol(   u'Пол',          ['sex'], SexList, 10),
            CTextCol(   u'Возраст',      ['age'], 10),
            CTextCol(   u'Каб',          ['office'], 5),
            CTextCol(   u'Код для отчётов', ['flatCode'], 20),
            CRefBookCol(u'Номенклатурная услуга', ['nomenclativeService_id'], 'rbService', 10, showFields=CRBComboBox.showCodeAndName),
            CDateCol(   u'Дата начала',           ['begDate'], 10),
            CDateCol(   u'Дата окончания',        ['endDate'], 10),
            CTextCol(   u'Контекст печати', ['context'], 20),
            CEnumCol(   u'Вид услуги', ['serviceType'], [u'Прочие', u'Первичный осмотр', u'Повторный осмотр',
                                                         u'Процедура/манип', u'Операция', u'Исследование',
                                                         u'Лечение', u'Профилактика', u'Анестезия',
                                                         u'Реанимация', u'Лаб.исследование'], 20),
            ], 'ActionType', ['class', 'group_id', 'code', 'name', 'id'], findClass=CFindDialog)
        self.setWindowTitleEx(u'Типы действий')
        self.expandedItemsState = {}
        self.setSettingsTblItems()
        self.additionalPostSetupUi()
        self.copyList = []
        self.cutList = []
        self.filterCmbCurrentIndexChanged()
        self.headerATCol = self.tblItems.horizontalHeader()
        self.headerATCol.setClickable(True)
        QObject.connect(self.headerATCol,
                               SIGNAL('sectionClicked(int)'),
                               self.onHeaderATColClicked)
        self.tblItems.showRecordProperties = self.showRecordProperties
        self.tblItems.addPopupRecordProperies()
        self.tblItems.installEventFilter(self)
        self.cmbShowInForm.setCurrentIndex(1)


    def showRecordProperties(self):
        table = self.tblItems.model().table()
        itemId = self.tblItems.currentItemId()
        CRecordProperties(self.tblItems, table, itemId, showRecordId=True).exec_()


    def onHeaderATColClicked(self, col):
        headerSortingCol = self.modelTable.headerSortingCol.get(col, False)
        self.modelTable.headerSortingCol = {}
        self.modelTable.headerSortingCol[col] = not headerSortingCol
        self.modelTable.sortDataModel()


    def setSettingsTblItems(self):
        self.tblItems.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)


    def preSetupUi(self):
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        showInForm = True
        self.addModels('Tree', CDragDropDBTreeModelWithClassItems(self, self.tableName, 'id', 'group_id', "CONCAT_WS(' | ', code, name)", 'class', self.order, showInForm))
        self.addModels('Table', CActionTypeTableModel(self, self.cols, self.tableName))
        self.modelTree.setLeavesVisible(True)
        self.modelTree.setClassItems((
                                     (u'Статус', 0),
                                     (u'Диагностика', 1),
                                     (u'Лечение', 2),
                                     (u'Прочие мероприятия', 3)))
        # дерево
        self.addObject('actDelete',    QtGui.QAction(u'Удалить', self))
        self.addObject('actDuplicate', QtGui.QAction(u'Дублировать', self))
        # список
        self.addObject('actSelectAllRow', QtGui.QAction(u'Выделить все строки', self))
        self.addObject('actClearSelection', QtGui.QAction(u'Снять выделение', self))
        self.addObject('actDelSelectedRows', QtGui.QAction(u'Удалить выделенные строки', self))
        self.addObject('actCopyCurrentItem', QtGui.QAction(u'Копировать', self))
        self.addObject('actCutCurrentItem', QtGui.QAction(u'Вырезать', self))
        self.addObject('actPasteCurrentItem', QtGui.QAction(u'Вставить', self))
        self.addObject('actCopyCurrentItemProperties', QtGui.QAction(u'Копировать все свойства', self))
        self.addObject('actPasteProperties', QtGui.QAction(u'Вставить свойства', self))
        self.addObject('actGroupEditor', QtGui.QAction(u'Групповой редактор', self))
        self.addObject('actRemoveProperties', QtGui.QAction(u'Удалить все свойства', self))


    def postSetupUi(self):
        #comboboxes

        specialValues = [(-2, u'не определен', u'не определен'),
                         (-1, u'определен',    u'определен')]
        self.cmbService.setTable('rbService', addNone=True, specialValues=specialValues)
        self.cmbQuotaType.setTable('QuotaType', addNone=True, specialValues=specialValues)
        self.cmbTissueType.setTable('rbTissueType', addNone=True, specialValues=specialValues)
#        bs = self.cmbServiceType.blockSignals(True)
        self.cmbServiceType.insertSpecialValue('-', None)
        CHierarchicalItemsListDialog.postSetupUi(self)

        self.tblItems.addPopupActions([self.actSelectAllRow,
                                       self.actClearSelection,
                                       self.actDelSelectedRows,
                                       self.actDuplicate,
                                       '-',
                                       self.actCopyCurrentItem,
                                       self.actCutCurrentItem,
                                       self.actPasteCurrentItem,
                                       '-',
                                       self.actCopyCurrentItemProperties,
                                       self.actPasteProperties,
                                       self.actRemoveProperties,
                                       '-',
                                       self.actGroupEditor,
                                      ]
                                     )


    def additionalPostSetupUi(self):
        self.treeItems.expand(self.modelTree.index(0, 0))
        #drag-n-drop support
        self.treeItems.setDragDropMode(QtGui.QAbstractItemView.InternalMove)
        # tree popup menu
        self.treeItems.createPopupMenu([self.actDelete])
        self.connect(self.treeItems.popupMenu(), SIGNAL('aboutToShow()'), self.popupMenuAboutToShow)
#        self.connect(self.tblItems.popupMenu(), SIGNAL('aboutToShow()'), self.itemsPopupMenuAboutToShow)

        self.connect(self.modelTree, SIGNAL('saveExpandedState()'),  self.saveExpandedState)
        self.connect(self.modelTree, SIGNAL('restoreExpandedState()'),  self.restoreExpandedState)

        pref=QtGui.qApp.preferences
        props = pref.appPrefs
        expand = forceInt(props.get('actionTypeTreeExpand',  QVariant()))
        if not expand:
            self.treeItems.expandToDepth(0)
        elif expand == 1:
            self.treeItems.expandAll()
        else:
            expandLevel = forceInt(props.get('actionTypeTreeExpandLevel',  QVariant(1)))
            self.treeItems.expandToDepth(expandLevel)


    def insertGroupIdDescendants(self, id, firstGroupId, className):
        db = QtGui.qApp.db
        db.checkdb()
        table = db.forceTable('ActionType')
        group = table['group_id']
        result = set([id])
        parents = [id]
        groupIdList = {id:firstGroupId}
        while parents:
            children = set(db.getIdList(table, where=group.inlist(parents)))
            records = db.getRecordList(table, '*', [table['group_id'].inlist(parents), table['deleted'].eq(0)])
            for record in records:
                actionTypeId = forceRef(record.value('id'))
                groupId = forceRef(record.value('group_id'))
                updateGroupId = groupIdList.get(groupId, firstGroupId)
                record.setNull('id')
                record.setValue('group_id', toVariant(updateGroupId))
                record.setValue('class', toVariant(className))
                newId = db.insertRecord(table.name(), record)
                groupIdList[actionTypeId] = newId
            newChildren = children-result
            result |= newChildren
            parents = newChildren
        return list(result)


    def updateGroupIdDescendants(self, id, firstGroupId, className):
        db = QtGui.qApp.db
        db.checkdb()
        table = db.forceTable('ActionType')
        group = table['group_id']
        result = set([id])
        parents = [id]
        groupIdList = {id:firstGroupId}
        while parents:
            children = set(db.getIdList(table, where=group.inlist(parents)))
            records = db.getRecordList(table, '*', [table['group_id'].inlist(parents), table['deleted'].eq(0)])
            for record in records:
                actionTypeId = forceRef(record.value('id'))
                groupId = forceRef(record.value('group_id'))
                updateGroupId = groupIdList.get(groupId, firstGroupId)
                record.setValue('group_id', toVariant(updateGroupId))
                record.setValue('class', toVariant(className))

                newId = db.updateRecord(table.name(), record)
                groupIdList[actionTypeId] = newId
            newChildren = children-result
            result |= newChildren
            parents = newChildren
        return list(result)


    def select(self, props=None):
        table = self.modelTable.table()
        groupId = self.currentGroupId()
        className = self.currentClass()
        cond = [ table['group_id'].eq(groupId) ]
        cond.append(table['deleted'].eq(0))
        cond.append(table['class'].eq(className))

        filterCond = self.filterConditions()
        if filterCond:
            cond.extend(filterCond)

        list = QtGui.qApp.db.getIdList(table.name(),
                           'id',
                           cond,
                           self.order)
        self.lblCountRows.setText(formatRecordsCount(len(list)))
        selectedRows = 1 if len(list) > 0 else 0
        self.lblCountSelectedRows.setText(formatCountSelectedRows(selectedRows))
        return list


    @pyqtSignature('QModelIndex')
    def on_tblItems_clicked(self, index):
        self.lblCountSelectedRows.setText(formatCountSelectedRows(len(self.tblItems.selectedItemIdList())))


    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress and obj == self.tblItems:
            key = event.key()
            index = self.tblItems.currentIndex()
            if key in (Qt.Key_Select, Qt.Key_Down, Qt.Key_PageDown) and isSelectable(index):
                event.accept()
                countRow = len(self.tblItems.selectedItemIdList())
                self.lblCountSelectedRows.setText(formatCountSelectedRows(countRow+(1 if countRow < len(self.tblItems.model().idList()) else 0)))
            if key in (Qt.Key_Up, Qt.Key_PageUp) and isSelectable(index):
                event.accept()
                countRow = len(self.tblItems.selectedItemIdList())
                self.lblCountSelectedRows.setText(formatCountSelectedRows(countRow-(1 if countRow > 1 else 0)))
        return CDialogBase.eventFilter(self, obj, event)


    def updateAvailableTreeIdList(self):
        filterCond = self.filterConditions()
        cond = filterCond if filterCond else '1'
        table = self.modelTable.table()
        list = QtGui.qApp.db.getIdList(table.name(),
                          'id',
                           cond)
        allList = QtGui.qApp.db.getTheseAndParents(table, 'group_id', list)
        self.modelTree.setAvailableItemIdList(allList)


    def filterConditions(self):
        db = QtGui.qApp.db
        tables = [(db.table('ActionType_Service'), 'service_id'),
                  (db.table('ActionType_QuotaType'), 'quotaType_id'),
                  (db.table('ActionType_TissueType'), 'tissueType_id')]
        serviceId = self.cmbService.value()
        quotaTypeId = self.cmbQuotaType.value()
        tissueTypeId = self.cmbTissueType.value()

        tableActionType = db.table('ActionType')
        cond = []
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
        if serviceType is not None:
            cond.append(self.modelTable.table()['serviceType'].eq(serviceType))

        showInForm = self.cmbShowInForm.currentText()
        if showInForm != '':
            cond.append(self.modelTable.table()['showInForm'].eq(int(showInForm == u'Да')))

        isPreferable = self.cmbIsPreferable.currentText()
        if isPreferable != '':
            cond.append(self.modelTable.table()['isPreferable'].eq(int(isPreferable == u'Да')))

        inContract = self.cmbContract.currentIndex()
        if inContract:
            tableATS = db.table('ActionType_Service')
            tableTariff = db.table('Contract_Tariff')
            tableContract = db.table('Contract')
            tableJoin = tableATS.leftJoin(tableTariff, [tableATS['service_id'].eq(tableTariff['service_id']),
                                                        tableTariff['deleted'].eq(0),
                                                        db.joinOr([tableTariff['begDate'].le(QDate().currentDate()),
                                                                   tableTariff['begDate'].isNull()]),
                                                        db.joinOr([tableTariff['endDate'].ge(QDate().currentDate()),
                                                                   tableTariff['endDate'].isNull()])])
            tableJoin = tableJoin.leftJoin(tableContract, [tableTariff['master_id'].eq(tableContract['id']),
                                                       tableContract['deleted'].eq(0),
                                                       db.joinOr([tableContract['begDate'].le(QDate().currentDate()),
                                                                  tableContract['begDate'].isNull()]),
                                                       db.joinOr([tableContract['endDate'].ge(QDate().currentDate()),
                                                                  tableContract['endDate'].isNull()])])
            condContract = [tableATS['master_id'].eq(tableActionType['id']), tableTariff['id'].isNotNull(), tableContract['id'].isNotNull()]
            cond.append(db.existsStmt(tableJoin, condContract) if self.cmbContract.currentText() == u'Да' else db.notExistsStmt(tableJoin, condContract))
        return cond


    def currentClass(self):
        return self.modelTree.itemClass(self.treeItems.currentIndex())


    def currentItem(self):
        return self.treeItems.currentIndex().internalPointer()


    def actionTypeIsUsed(self, actionTypeId):
        db = QtGui.qApp.db
        actionTypeIdList = db.getDescendants('ActionType', 'group_id', actionTypeId, 'deleted=0')
        tableEvent  = db.table('Event')
        tableAction = db.table('Action')
        table = tableAction.leftJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))
        record = db.getRecordEx( table,
                                 tableAction['id'],
                                 [ tableAction['actionType_id'].inlist(actionTypeIdList),
                                   tableAction['deleted'].eq(0),
                                   db.joinOr([ tableAction['event_id'].isNull(),
                                               tableEvent['deleted'].eq(0)
                                             ]
                                            )
                                 ]
                               )
        return bool(record)


    def currentTreeItemId(self):
        idx = self.treeItems.currentIndex()
        if idx.isValid():
            return self.modelTree.itemId(idx)
        return None


    def getItemEditor(self):
        return CActionTypeEditor(self)


    def getSelectedWithDescendants(self):
        db = QtGui.qApp.db
        tableActionType = db.table('ActionType')
        selectedIdList = self.tblItems.selectedItemIdList()
        result = set()
        for actionTypeId in selectedIdList:
            actionTypeIdList = db.getDescendants(tableActionType, 'group_id', actionTypeId, 'deleted=0')
            result.update(actionTypeIdList)
        self.lblCountSelectedRows.setText(formatCountSelectedRows(len(list(result))))
        return list(result)


    def copyInternals(self, newItemId, oldItemId):
        self.copyDependedTableData('ActionPropertyType',
                                   'actionType_id',
                                   newItemId,
                                   oldItemId)
        for tableName in ( 'ActionType_Equipment',
                           'ActionType_Nomenclature',
                           'ActionType_PFOrgStructure',
                           'ActionType_PFSpeciality',
                           'ActionType_QuotaType',
                           'ActionType_Service',
                           'ActionType_Testator',
                           'ActionType_TissueType',
                           'ActionType_Identification',
                         ):
            self.copyDependedTableData(tableName,
                                       'master_id',
                                       newItemId,
                                       oldItemId)


    def filterCmbCurrentIndexChanged(self):
        id = self.currentItemId()
        self.updateAvailableTreeIdList()
        self.findById(id)


    def dataInTableChanged(self, newItemId=None):
        path = []
        index = self.treeItems.currentIndex()
        rootIndex = self.modelTree.index(0,0)
        while index != rootIndex:
            path.append(index.row())
            index = index.parent()
        self.saveExpandedState()
        CRBModelDataCache.reset('ActionType')
        self.modelTree.update()
        self.modelTree.reset()
        self.restoreExpandedState()

        index = self.modelTree.index(0,0)
        for row in reversed(path):
            rowCount = self.modelTree.rowCount(index)
            if rowCount>0:
                index = self.modelTree.index(min(row, rowCount-1),0, index)
            else:
                break

        self.treeItems.setCurrentIndex(index)
        self.modelTable.invalidateRecordsCache()
        self.renewListAndSetTo(newItemId)


    def popupMenuAboutToShow(self):
        currentItemId = self.currentTreeItemId()
        self.actDelete.setEnabled(bool(currentItemId) and not self.actionTypeIsUsed(currentItemId))


    @pyqtSignature('')
    def on_actDelete_triggered(self):
        actionTypeId = self.currentTreeItemId()
        if not actionTypeId:
            return

        db = QtGui.qApp.db
        tableActionType = db.table('ActionType')
        actionTypeIdList = db.getDescendants(tableActionType, 'group_id', actionTypeId, 'deleted=0')
        if actionTypeIdList == [actionTypeId] :
            question = u'Вы действительно хотите удалить данную группу действий?'
        else:
            question = u'Вы действительно хотите удалить данную группу действий\nи %s?' %\
                formatNum1(len(actionTypeIdList)-1,
                           (u'входящий в неё элемент',
                            u'входящих в неё элемента',
                            u'входящих в неё элементов',
                           )
                          )
        answer = QtGui.QMessageBox.question(self,
                                            u'Внимание!',
                                            question,
                                            QtGui.QMessageBox.Yes|QtGui.QMessageBox.No,
                                            QtGui.QMessageBox.No
                                           )
        if answer == QtGui.QMessageBox.Yes:
            db.markRecordsDeleted(tableActionType, tableActionType['id'].inlist(actionTypeIdList))
            self.dataInTableChanged()


    @pyqtSignature('int')
    def on_cmbService_currentIndexChanged(self, index):
        self.filterCmbCurrentIndexChanged()


    @pyqtSignature('int')
    def on_cmbQuotaType_currentIndexChanged(self, index):
        self.filterCmbCurrentIndexChanged()


    @pyqtSignature('int')
    def on_cmbTissueType_currentIndexChanged(self, index):
        self.filterCmbCurrentIndexChanged()


    @pyqtSignature('int')
    def on_cmbServiceType_currentIndexChanged(self, index):
        self.filterCmbCurrentIndexChanged()
        

    @pyqtSignature('int')
    def on_cmbIsPreferable_currentIndexChanged(self, index):
        self.filterCmbCurrentIndexChanged()


    @pyqtSignature('int')
    def on_cmbContract_currentIndexChanged(self, index):
        self.filterCmbCurrentIndexChanged()


    @pyqtSignature('int')
    def on_cmbShowInForm_currentIndexChanged(self, index):
        showInForm = self.cmbShowInForm.currentText()
        if showInForm == u'Да':
            self.treeItems.model().setShowInForm(True)
        else:
            self.treeItems.model().setShowInForm(False)  
        self.filterCmbCurrentIndexChanged()


    @pyqtSignature('QModelIndex')
    def on_treeItems_doubleClicked(self, index):
        item = self.currentItem()
        if not item.isClass:
            itemId = item._id
            if itemId:
                dialog = self.getItemEditor()
                try:
                    dialog.load(itemId)
                    if dialog.exec_():
                        itemId = dialog.itemId()
                        self.dataInTableChanged(itemId)
                finally:
                    dialog.deleteLater()
            else:
                self.on_btnNew_clicked()


    @pyqtSignature('')
    def on_tblItems_popupMenuAboutToShow(self):
        selectedItemIdList = self.tblItems.selectedItemIdList()
        selectionNotEmpty = bool(selectedItemIdList)

        self.actClearSelection.setEnabled(selectionNotEmpty)
        self.actDelSelectedRows.setEnabled(selectionNotEmpty
                                           and all(not self.actionTypeIsUsed(actionTypeId)
                                                   for actionTypeId in selectedItemIdList
                                                  )
                                          )
        self.actDuplicate.setEnabled(len(selectedItemIdList)==1)
        self.actCopyCurrentItem.setEnabled(selectionNotEmpty)
        self.actCutCurrentItem.setEnabled(selectionNotEmpty)
        self.actPasteCurrentItem.setEnabled(bool(self.copyList or self.cutList))

        self.actCopyCurrentItemProperties.setEnabled(len(selectedItemIdList)==1)
        self.actPasteProperties.setEnabled(selectionNotEmpty
                                           and QtGui.qApp.clipboard().mimeData().hasFormat(self.mimeTypeActionPropertyIdList)
                                           )
        isRemoveProperties = selectionNotEmpty and QtGui.qApp.userHasRight(urDeleteActionTypeProperties)
        if isRemoveProperties:
            if selectedItemIdList:
                db = QtGui.qApp.db
                table = db.table('ActionPropertyType')
                records = db.getRecordList(table, [table['id'], table['actionType_id']], [table['actionType_id'].inlist(selectedItemIdList)])
                for record in records:
                    actionPropertyTypeId = forceRef(record.value('id'))
                    actionTypeId = forceRef(record.value('actionType_id'))
                    if not actionPropertyTypeIsUsed(actionPropertyTypeId, actionTypeId):
                        isRemoveProperties = False
                        break
        self.actRemoveProperties.setEnabled(isRemoveProperties)
        self.actGroupEditor.setEnabled(selectionNotEmpty),


    @pyqtSignature('')
    def on_actSelectAllRow_triggered(self):
        self.tblItems.selectAll()
        self.lblCountSelectedRows.setText(formatCountSelectedRows(len(self.tblItems.selectedItemIdList())))


    @pyqtSignature('')
    def on_actClearSelection_triggered(self):
        self.tblItems.clearSelection()
        self.lblCountSelectedRows.setText(formatCountSelectedRows(len(self.tblItems.selectedItemIdList())))


    @pyqtSignature('')
    def on_actDelSelectedRows_triggered(self):
        db = QtGui.qApp.db
        selectedIdList = self.tblItems.selectedItemIdList()
        actionTypeIdList = []
        for actionTypeId in selectedIdList:
            actionTypeIdList += db.getDescendants('ActionType', 'group_id', actionTypeId, 'deleted=0')
        question = u'Вы действительно хотите удалить %s?' % \
                   formatNum1(len(actionTypeIdList),
                              (u'строку',
                               u'строки',
                               u'строк',
                               )
                              )
        if QtGui.QMessageBox.question(self, u'Внимание!',
                                      question,
                                      QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                      QtGui.QMessageBox.No
                                      ) == QtGui.QMessageBox.Yes:
            tableActionType = db.table('ActionType')
            db.markRecordsDeleted(tableActionType, tableActionType['id'].inlist(actionTypeIdList))
        self.dataInTableChanged()

    #        self.modelTable.setIdList(self.select())


    @pyqtSignature('')
    def on_actDuplicate_triggered(self):
        self.duplicateCurrentRow()


    @pyqtSignature('')
    def on_actCopyCurrentItem_triggered(self):
        selectedIdList = self.tblItems.selectedItemIdList()
        if selectedIdList:
            self.copyList = selectedIdList
            self.cutList = []
            self.statusBar.showMessage(u'Готово к копированию %s'% formatNum(len(selectedIdList), self.unitNameTuple),
                                       5000)


    @pyqtSignature('')
    def on_actCutCurrentItem_triggered(self):
        selectedIdList = self.tblItems.selectedItemIdList()
        if selectedIdList:
            self.copyList = []
            self.cutList = selectedIdList
            self.statusBar.showMessage(u'Готово к перемещению %s'% formatNum(len(selectedIdList), self.unitNameTuple),
                                       5000)
            self.actPasteCurrentItem.setEnabled(1)


    @pyqtSignature('')
    def on_actPasteCurrentItem_triggered(self):
        db = QtGui.qApp.db
        tableActionType = db.table('ActionType')
        tableActionPropertyType = db.table('ActionPropertyType')
        tableActionTypeService = db.table('ActionType_Service')
        tableActionTypeIdentification = db.table('ActionType_Identification')
        currentGroup = self.treeItems.currentIndex().internalPointer()._id
        className = self.currentClass()
        if self.copyList:
            self.statusBar.showMessage(u'Подождите, подготовка к копированию',  5000)
            listLength = len(self.copyList)
            count = 0
            for id in self.copyList:
                db.transaction()
                try:
                    self.statusBar.showMessage(u'Подождите, идет копирование %d из %s'% \
                                                ( count+1,
                                                  formatNum(listLength, (u'строки', u'строк', u'строк')),
                                                ),
                                               5000)
                    recordActionType = db.getRecordEx(tableActionType, '*', [tableActionType['id'].eq(id), tableActionType['deleted'].eq(0)])
                    recordActionType.setNull('id')
                    recordActionType.setValue('group_id', toVariant(currentGroup))
                    recordActionType.setValue('class', toVariant(className))
                    newItemId = db.insertRecord(tableActionType, recordActionType)
                    records = db.getRecordList(
                        tableActionPropertyType, '*',
                        tableActionPropertyType['actionType_id'].eq(id))
                    for record in records:
                        record.setNull('id')
                        record.setValue('actionType_id', toVariant(newItemId))
                        db.insertRecord(tableActionPropertyType, record)
                    records = db.getRecordList(
                        tableActionTypeService, '*',
                        tableActionTypeService['master_id'].eq(id))
                    for record in records:
                        record.setNull('id')
                        record.setValue('master_id', toVariant(newItemId))
                        db.insertRecord(tableActionTypeService, record)
                    records = db.getRecordList(tableActionTypeIdentification, '*',
                        tableActionTypeIdentification['master_id'].eq(id))
                    for record in records:
                        record.setNull('id')
                        record.setValue('master_id', toVariant(newItemId))
                        db.insertRecord(tableActionTypeIdentification, record)
                    self.insertGroupIdDescendants(id, newItemId, className)
                    db.commit()
                    count += 1
                except:
                    db.rollback()
                    QtGui.qApp.logCurrentException()
                    raise
            self.dataInTableChanged(newItemId)
            self.statusBar.showMessage(agreeNumberAndWord(count,
                                                          (u'Скопирована %s',
                                                           u'Скопированo %s',
                                                           u'Скопированo %s',
                                                          )
                                                         ) % formatNum(count, self.unitNameTuple),
                                       5000)
        elif self.cutList:
            self.statusBar.showMessage(u'Подождите, подготовка к перемещению',  5000)
            listLength = len(self.cutList)
            count = 0
            for id in self.cutList:
                db.transaction()
                try:
                    self.statusBar.showMessage(u'Подождите, идет перемещение %d из %s'%\
                                                ( count+1,
                                                  formatNum(listLength, (u'строки', u'строк', u'строк')),
                                                ),
                                               5000)
                    recordActionType = db.getRecord(tableActionType, '*', id)
                    actionTypeId = forceRef(recordActionType.value('id'))
                    recordActionType.setValue('group_id', toVariant(currentGroup))
                    recordActionType.setValue('class', toVariant(className))
                    newItemId = db.updateRecord(tableActionType, recordActionType)
                    self.updateGroupIdDescendants(actionTypeId, newItemId, className)
                    db.commit()
                    count += 1
                except:
                    db.rollback()
                    QtGui.qApp.logCurrentException()
                    raise
            self.cutList = []
            self.dataInTableChanged(newItemId)
            self.statusBar.showMessage(agreeNumberAndWord(count,
                                                          (u'Перемещена %s',
                                                           u'Перемещенo %s',
                                                           u'Перемещенo %s',
                                                          )
                                                         ) % formatNum(count, self.unitNameTuple),
                                       5000)


    @pyqtSignature('')
    def on_actGroupEditor_triggered(self):
        selectedIdList = self.getSelectedWithDescendants()
        itemId = self.tblItems.currentItemId()
        if CGroupActionTypeEditor(self, selectedIdList, itemId).exec_():
            self.dataInTableChanged(itemId)


    @pyqtSignature('')
    def on_actCopyCurrentItemProperties_triggered(self):
        currentItemId = self.tblItems.currentItemId()
        if currentItemId:
            db = QtGui.qApp.db
            tableActionPropertyType = db.table('ActionPropertyType')
            idList= db.getIdList(tableActionPropertyType, '*',
                        [tableActionPropertyType['actionType_id'].eq(currentItemId),
                         tableActionPropertyType['deleted'].eq(0)])
            if idList != []:
                strList = ','.join(str(id) for id in idList if id)
                mimeData = QMimeData()
                v = toVariant(strList)
                mimeData.setData(self.mimeTypeActionPropertyIdList, v.toByteArray())
                QtGui.qApp.clipboard().setMimeData(mimeData)
                self.statusBar.showMessage(u'Скопировано %s' % (formatNum(len(idList), self.propNameTuple)),
                                           5000)
            else:
                self.statusBar.showMessage(u'Нет свойств для копирования',  5000)


    @pyqtSignature('')
    def on_actPasteProperties_triggered(self):
        def propertiesAreEqualInternal(x, y):
            if x.count() == y.count():
                # сравниваем только имя, пол и возраст
                for name in ('name',  'sex',  'age'):
                    if x.value(name) != y.value(name):
                        return False

            return True

        def propertyExistInListInternal(property, propertyList):
            for x in propertyList:
                if propertiesAreEqualInternal(property,  x):
                    return True
            return False

        selectedIdList = self.getSelectedWithDescendants()
        if selectedIdList:
            mimeData = QtGui.qApp.clipboard().mimeData()
            if mimeData.hasFormat(self.mimeTypeActionPropertyIdList):
                strList = forceString(mimeData.data(self.mimeTypeActionPropertyIdList)).split(',')
                db = QtGui.qApp.db
                tableActionPropertyType = db.table('ActionPropertyType')

                propertyList = db.getRecordList(tableActionPropertyType, where=[
                        tableActionPropertyType['id'].inlist(strList), tableActionPropertyType['deleted'].eq(0)])
                nInsert = 0
                nTotal = len(strList)*len(selectedIdList)

                if propertyList:
                    for currentItemId in selectedIdList:
                        currentPropertyList= db.getRecordList(tableActionPropertyType, '*',
                            [tableActionPropertyType['actionType_id'].eq(currentItemId),
                             tableActionPropertyType['deleted'].eq(0)])

                        for newProperty in propertyList:
                            if not propertyExistInListInternal(newProperty,  currentPropertyList):
                                newProperty.setNull('id')
                                newProperty.setValue('actionType_id', toVariant(currentItemId))
                                db.insertRecord(tableActionPropertyType, newProperty)
                                nInsert += 1

                    self.statusBar.showMessage(u'Вставлено %s из %s' % (
                                                    formatNum(nInsert, self.propNameTuple),
                                                    formatNum(nTotal,  (u'возможного', u'возможных', u'возможных')),
                                                    ),
                                               5000)
                else:
                    self.statusBar.showMessage(u'Нечего вставлять',  5000)
            else:
                self.statusBar.showMessage(u'Ошибка: неизвестный формат данных в буфере обмена',  5000)


    @pyqtSignature('')
    def on_actRemoveProperties_triggered(self):
        selectedIdList = self.tblItems.selectedItemIdList()
        if selectedIdList:
            question = u'Вы действительно хотите удалить свойства %s? ' % \
                       formatNum1(len(selectedIdList),
                                  (u'типа действия',
                                   u'типов действий',
                                   u'типов действий'
                                  )
                                 )
            if QtGui.QMessageBox.question( self,
                                       u'Внимание!',
                                       question,
                                       QtGui.QMessageBox.Yes|QtGui.QMessageBox.No,
                                       QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes:
                db = QtGui.qApp.db
                table = db.table('ActionPropertyType')
                db.deleteRecord(table, table['actionType_id'].inlist(selectedIdList))


    @pyqtSignature('')
    def on_btnNew_clicked(self):
        dialog = self.getItemEditor()
        try:
            currentClass = self.currentClass()
            if currentClass is not None:
                dialog.setClass(currentClass)
                dialog.setGroupId(self.currentGroupId())
                if dialog.exec_():
                    itemId = dialog.itemId()
                    self.dataInTableChanged(itemId)
        finally:
           dialog.deleteLater()


class COrgStructureModel(CInDocTableModel):
    def __init__(self, parent = None):
        CInDocTableModel.__init__(self, 'ActionType_PFOrgStructure', 'id', 'master_id', parent)
        self.addCol(COrgStructureInDocTableCol(u'Подразделение',  'orgStructure_id',  100))


class CSpecialityModel(CInDocTableModel):
    def __init__(self, parent = None):
        CInDocTableModel.__init__(self, 'ActionType_PFSpeciality', 'id', 'master_id', parent)
        self.addCol(CRBInDocTableCol(u'Специальность', 'speciality_id', 30, 'rbSpeciality'))


class CFunctionalEquipmentModel(CInDocTableModel):
    def __init__(self, parent=None):
        CInDocTableModel.__init__(self, 'ActionType_Equipment', 'id', 'master_id', parent)
        equipmentTypeId = forceInt(QtGui.qApp.db.translate('rbEquipmentType', 'code', '02', 'id'))
        self.addCol(CRBInDocTableCol(u'Оборудование', 'equipment_id', 100, 'rbEquipment', filter='equipmentType_id = %d'%(equipmentTypeId)))


class CActionExpansionModel(CInDocTableModel):
    def __init__(self, parent = None):
        CInDocTableModel.__init__(self, 'ActionType_Expansion', 'id', 'master_id', parent)
        # self.addCol(CActionTypeTableCol(u'Функция', 'actionType_id', 20, None, classesVisible=False, filter=''' ActionType.flatCode LIKE '%%direction%%' '''))
        # self.cols()[0].setLeavesVisible(False)
        self.addCol(CRBInDocTableCol(u'Функция', 'actionType_id', 100, 'ActionType', filter='''ActionType.deleted = 0 and ActionType.flatCode LIKE '%%direction%%' '''))


class CActionTypeEditor(CItemEditorBaseDialog, Ui_ActionTypeEditorDialog):
    tabNomenclatureExpenseIndex = None
    def __init__(self,  parent):
        CItemEditorBaseDialog.__init__(self, parent, 'ActionType')
        self._parent = parent

        self.addModels('Properties',           CPropertiesModel(self))
        self.addModels('Testators',            CTestatorsModel(self))
        self.addModels('Relations', CRelationsModel(self))
        self.addModels('ServiceByFinanceType', CServiceByFinanceTypeModel(self))
        self.addModels('QuotaType',            CQuotaTypeModel(self))
        self.addModels('UETandActionSpecification',            CUETandActionSpecificationModel(self))
        self.addModels('TissueType',           CTissueTypeModel(self))
        self.addModels('Nomenclature',         CNomenclatureModel(self))
        self.addModels('OrgStructure',      COrgStructureModel(self))
        self.addModels('Speciality',      CSpecialityModel(self))
        self.addModels('Equipment',      CFunctionalEquipmentModel(self))
        self.addModels('ActionFunctions', CActionExpansionModel(self))
        self.addModels('Identification',       CIdentificationModel(self, 'ActionType_Identification', 'ActionType'))

        self.addObject('actDuplicate', QtGui.QAction(u'Дублировать', self))
        self.addObject('actCopy', QtGui.QAction(u'Копировать выделенные свойства', self))

        self.setupUi(self)

        CActionTypeEditor.tabNomenclatureExpenseIndex = self.tabWidget.indexOf(self.tabNomenclatureExpense)

        self.tabWidget.setTabEnabled(CActionTypeEditor.tabNomenclatureExpenseIndex, False)

        self.cmbAmountEvaluation.addItems(CActionType.amountEvaluation)
        self.setWindowTitleEx(u'Тип действия')

        self.edtAmount.setValue(1)

        self.edtBegDate.setDate(QDate())
        self.endEndDate.setDate(QDate())

        # comboboxes
        self.cmbGroup.setTable('ActionType')
        self.cmbNomenclativeService.setModel(CRBServiceComboBoxModel(self))
        self.cmbNomenclativeService.setTable('rbService')
        self.cmbNomenclativeService.setShowFields(CRBComboBox.showCodeAndName)
        self.cmbQuotaType.setTable('QuotaType')
        self.cmbQuotaType.setShowFields(CRBComboBox.showCodeAndName)
        self.cmbPrescribedType.setTable('ActionType')
        self.cmbShedule.setTable('rbActionShedule')
        self.cmbAddVisitScene.setTable('rbScene')
        self.cmbAddVisitType.setTable('rbVisitType')
        self.cmbNomenclatureNumberCounter.setTable('rbCounter')


        self.on_cmbClass_currentIndexChanged(self.cmbClass.currentIndex())
        self.setupDirtyCather()
        self.tblProperties.setModel(self.modelProperties)
        self.tblTestators.setModel(self.modelTestators)
        self.tblRelations.setModel(self.modelRelations)

#        self.domainDelegate = CDomainItemDelegate(self)
#        self.tblProperties.setItemDelegateForColumn(6, self.domainDelegate)

        self.tblProperties.createPopupMenu([self.actDuplicate, '-'])
        self.tblProperties.addPopupSelectAllRow()
        self.tblProperties.addPopupClearSelectionRow()
        self.tblProperties.popupMenu().addAction(self.actCopy)
        self.tblProperties.addPopupSeparator()
        self.tblProperties.addMoveRow()
        self.tblProperties.addPopupDelRow()
        self.tblProperties.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.tblProperties.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.tblProperties.setSettingDelegate(self.modelProperties.getColIndex('valueDomain'))

        self.tblTestators.addPopupSelectAllRow()
        self.tblTestators.addPopupClearSelectionRow()
        self.tblTestators.addPopupSeparator()
        self.tblTestators.addMoveRow()
        self.tblTestators.addPopupDelRow()
        self.tblTestators.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.tblTestators.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        
        self.tblRelations.addPopupSelectAllRow()
        self.tblRelations.addPopupClearSelectionRow()
        self.tblRelations.addPopupSeparator()
        self.tblRelations.addMoveRow()
        self.tblRelations.addPopupDelRow()
        self.tblRelations.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.tblRelations.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)

        self.tblServiceByFinanceType.setModel(self.modelServiceByFinanceType)
        self.tblServiceByFinanceType.addPopupDuplicateCurrentRow()
        self.tblServiceByFinanceType.addMoveRow()
        self.tblServiceByFinanceType.addPopupDelRow()
        self.tblQuotaType.setModel(self.modelQuotaType)
        self.tblQuotaType.addPopupDuplicateCurrentRow()
        self.tblQuotaType.addMoveRow()
        self.tblQuotaType.addPopupDelRow()

        self.tblUETandActionSpecification.setModel(self.modelUETandActionSpecification)
        self.tblUETandActionSpecification.addPopupDelRow()

        self.tblTissueType.setModel(self.modelTissueType)
        self.tblTissueType.addPopupDelRow()

        self.setModels(self.tblNomenclature, self.modelNomenclature, self.selectionModelNomenclature)
        self.tblNomenclature.addPopupDelRow()
        self.tblNomenclature.setSortingEnabled(True)

        self.cmbGroup.setEnabled(False)
        self.cmbClass.setEnabled(False)

        self.cmbNomenclatureClass.setTable('rbNomenclatureClass', True)
        self.cmbNomenclatureKind.setTable('rbNomenclatureKind',   True)
        self.cmbNomenclatureType.setTable('rbNomenclatureType',   True)
        self.cmbNomenclatureOrgStructure.setOrgId(QtGui.qApp.currentOrgId())
        self.tblPFSpeciality.setModel(self.modelSpeciality)
        self.tblPFOrgStructure.setModel(self.modelOrgStructure)
        self.tblActionFunctions.setModel(self.modelActionFunctions)

        self.tblPFSpeciality.addPopupDelRow()
        self.tblPFOrgStructure.addPopupDelRow()
        self.tblActionFunctions.addPopupDelRow()

        self.tblPACS.setModel(self.modelEquipment)
        self.tblPACS.addPopupDelRow()
        # db = QtGui.qApp.db
        # parentGroupId = forceRef(db.translate('rbTestGroup', 'name', u'СОЦ-Лаборатория', 'id'))
        # tableRbTest = db.table('rbTest')
        # groupIdList = db.getDescendants('rbTestGroup', 'group_id', parentGroupId)
        # self.socFilter = tableRbTest['testGroup_id'].inlist(groupIdList)

        self.setModels(self.tblIdentification, self.modelIdentification, self.selectionModelIdentification)
        self.tblIdentification.addPopupDelRow()
        self.tblIdentification.setDelRowsChecker(self.modelIdentification.delRowsChecker)
        self.tabWidget.setTabEnabled(CActionTypeEditor.tabNomenclatureExpenseIndex, True)

        self.addObject('btnApply', QtGui.QPushButton(u'Применить', self))
        self.buttonBox.addButton(self.btnApply, QtGui.QDialogButtonBox.ActionRole)
        self.connect(self.btnApply, SIGNAL('clicked()'), self.saveAndUpDate)


    def saveAndUpDate(self):
        if self.saveData():
            self.parent().modelTree.update()
            self.parent().renewListAndSetTo(self.itemId())
            buttons = QtGui.QMessageBox.Ok
            messageBox = QtGui.QMessageBox()
            messageBox.setWindowFlags(messageBox.windowFlags() | Qt.WindowStaysOnTopHint)
            messageBox.setWindowTitle(u'Внимание!')
            messageBox.setText(u'Данные сохранены')
            messageBox.setStandardButtons(buttons)
            messageBox.setDefaultButton(QtGui.QMessageBox.Ok)
            return messageBox.exec_()


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelProperties_currentChanged(self, current, previous):
        if current.column() in (self.modelProperties.ciSetting,):
            self.tblProperties.resizeRowsToContents()


    def setRecord(self, record):
        CItemEditorBaseDialog.setRecord(self, record)
        setLineEditValue(   self.edtCode,                      record, 'code')
        setLineEditValue(   self.edtName,                      record, 'name')
        setLineEditValue(   self.edtTitle,                     record, 'title')
        setLineEditValue(   self.edtFlatCode,                  record, 'flatCode')
        setCheckBoxValue(   self.chkIsMES,                     record, 'isMES')
        setCheckBoxValue(   self.chkIsPreferable,              record, 'isPreferable')
        setRBComboBoxValue( self.cmbNomenclativeService,       record, 'nomenclativeService_id')
        setRBComboBoxValue( self.cmbShedule,                   record, 'shedule_id')
        setRBComboBoxValue( self.cmbServiceType,               record, 'serviceType')
        setComboBoxValue(   self.cmbExposeDateSelector,        record, 'exposeDateSelector')
        setComboBoxValue(   self.cmbSex,                       record, 'sex')
        setCheckBoxValue(   self.chkNomenclatureExpense,       record, 'isNomenclatureExpense')
        setCheckBoxValue(   self.chkDoesNotInvolveExecutionCourse, record, 'isDoesNotInvolveExecutionCourse')
        setCheckBoxValue(   self.chkGenerateStockMotionReason, record, 'generateStockMotionReason')
        setCheckBoxValue(   self.chkGenerateAfterEventExecDate, record, 'generateAfterEventExecDate')
        setRBComboBoxValue( self.cmbDefaultStatus,             record, 'defaultStatus')
        setComboBoxValue(   self.cmbDefaultDirectionDate,      record, 'defaultDirectionDate')
        setComboBoxValue(   self.cmbDefaultPlannedEndDate,     record, 'defaultPlannedEndDate')
        setComboBoxValue(   self.cmbPlannedEndDateRequired,    record, 'isPlannedEndDateRequired')
        setComboBoxValue(   self.cmbDefaultBegDate,            record, 'defaultBegDate')
        setComboBoxValue(   self.cmbDefaultEndDate,            record, 'defaultEndDate')
        setComboBoxValue(   self.cmbDefaultSetPersonInEvent,      record, 'defaultSetPersonInEvent')
        setRBComboBoxValue( self.cmbDefaultExecPerson,         record, 'defaultExecPerson_id')
        setComboBoxValue(   self.cmbDefaultPersonInEvent,      record, 'defaultPersonInEvent')
        setComboBoxValue(   self.cmbDefaultPersonInEditor,     record, 'defaultPersonInEditor')
        setComboBoxValue(   self.cmbExecPersonRequired,        record, 'isExecPersonRequired')
        setComboBoxValue(   self.cmbDefaultMKB,                record, 'defaultMKB')
        setComboBoxValue(   self.cmbMKBRequired,               record, 'isMKBRequired')
        setComboBoxValue(   self.cmbIsMorphologyRequired,      record, 'isMorphologyRequired')
        setComboBoxValue(   self.cmbNeedAttachFile,            record, 'isNeedAttachFile')
        setLineEditValue(   self.edtOffice,                    record, 'office')
        setSpinBoxValue(    self.edtActualAppointmentDuration, record, 'actualAppointmentDuration')
        setSpinBoxValue(    self.edtExpirationDate,            record, 'expirationDate')
        setCheckBoxValue(   self.chkRestrictExpirationDate,    record, 'isRestrictExpirationDate')
        setCheckBoxValue(   self.chkShowInForm,                record, 'showInForm')
        setCheckBoxValue(   self.chkEditStatus,                record, 'editStatus')
        setCheckBoxValue(   self.chkEditBegDate,               record, 'editBegDate')
        setCheckBoxValue(   self.chkEditEndDate,               record, 'editEndDate')
        setCheckBoxValue(   self.chkEditExecPers,              record, 'editExecPers')
        setCheckBoxValue(   self.chkEditNote,                  record, 'editNote')
        setCheckBoxValue(   self.chkRequiredActionSpecification, record, 'requiredActionSpecification')
        setCheckBoxValue(   self.chkUsesCycles,                record, 'isUsesCycles')
        setDateEditValue(   self.edtBegDate,                   record, 'begDate')
        setDateEditValue(   self.endEndDate,                   record, 'endDate')
        setCheckBoxValue(   self.chkShowBegDate,               record, 'showBegDate')
        setCheckBoxValue(   self.chkDuplication,               record, 'duplication')
        setCheckBoxValue(   self.chkIgnoreVisibleRights,       record, 'ignoreVisibleRights')
        setCheckBoxValue(   self.chkEditSetPerson,             record, 'editSetPerson')
        setCheckBoxValue(   self.chkEditOrg,                   record, 'editOrg')
        setCheckBoxValue(   self.chkEditOrgStructure,          record, 'editOrgStructure')
        setCheckBoxValue(   self.chkGenTimetable,              record, 'genTimetable')
        setCheckBoxValue(   self.chkShowTime,                  record, 'showTime')
        setCheckBoxValue(   self.chkRequiredCoordination,      record, 'isRequiredCoordination')
        setCheckBoxValue(   self.chkHasAssistant,              record, 'hasAssistant')
        setLineEditValue(   self.edtContext,                   record, 'context')
        setSpinBoxValue(    self.edtAmount,                    record, 'amount')
        setComboBoxValue(   self.cmbAmountEvaluation,          record, 'amountEvaluation')
        setSpinBoxValue(    self.edtMaxOccursInEvent,          record, 'maxOccursInEvent')
        setSpinBoxValue(    self.edtTicketDuration,            record, 'ticketDuration')
        setCheckBoxValue(   self.chkPropertyAssignedVisible,   record, 'propertyAssignedVisible')
        self.chkPropertyAssignedRequired.setVisible(self.chkPropertyAssignedVisible.isChecked())
        setCheckBoxValue(   self.chkPropertyAssignedRequired,  record, 'propertyAssignedRequired')
        setCheckBoxValue(   self.chkPropertyUnitVisible,       record, 'propertyUnitVisible')
        setCheckBoxValue(   self.chkPropertyNormVisible,       record, 'propertyNormVisible')
        setCheckBoxValue(   self.chkPropertyEvaluationVisible, record, 'propertyEvaluationVisible')
        setCheckBoxValue(   self.chkPropertyCommentVisible,    record, 'propertyCommentVisible')
        setComboBoxValue(   self.cmbClass,                     record, 'class')

        setRBComboBoxValue( self.cmbNomenclatureOrgStructure,  record, 'nomenclatureOrgStructure_id')
        setRBComboBoxValue( self.cmbNomenclatureClass,         record, 'nomenclatureClass_id')
        setRBComboBoxValue( self.cmbNomenclatureKind,          record, 'nomenclatureKind_id')
        setRBComboBoxValue( self.cmbNomenclatureType,          record, 'nomenclatureType_id')
        setRBComboBoxValue( self.cmbNomenclatureNumberCounter, record, 'nomenclatureCounter_id')

        setCheckBoxValue(   self.chkCloseEvent,                record, 'closeEvent')

        setCheckBoxValue(   self.chkAddVisit,                  record, 'addVisit')
        setRBComboBoxValue( self.cmbAddVisitScene,             record, 'addVisitScene_id')
        setRBComboBoxValue( self.cmbAddVisitType,              record, 'addVisitType_id')

        setDoubleBoxValue(    self.edtUetAdultDoctor,                    record, 'adultUetDoctor')
        setDoubleBoxValue(    self.edtUetChildDoctor,                    record, 'childUetDoctor')
        setDoubleBoxValue(    self.edtUetAdultAvarageMedWorker,                    record, 'adultUetAverageMedWorker')
        setDoubleBoxValue(    self.edtUetChildAvarageMedWorker,                    record, 'childUetAverageMedWorker')

        setDoubleBoxValue(    self.edtAssistantUetAdultDoctor,                    record, 'assistantAdultUetDoctor')
        setDoubleBoxValue(    self.edtAssistantUetChildDoctor,                    record, 'assistantChildUetDoctor')
        setDoubleBoxValue(    self.edtAssistantUetAdultAvarageMedWorker,                    record, 'assistantAdultUetAverageMedWorker')
        setDoubleBoxValue(    self.edtAssistantUetChildAvarageMedWorker,                    record, 'assistantChildUetAverageMedWorker')

        self.on_cmbClass_currentIndexChanged(self.cmbClass.currentIndex())
        setRBComboBoxValue(self.cmbPrescribedType, record, 'prescribedType_id')
        setRBComboBoxValue( self.cmbGroup,                     record, 'group_id')
        self.cmbDefaultOrg.setValue(forceRef(record.value('defaultOrg_id')))
        (begUnit, begCount, endUnit, endCount) = parseAgeSelector(forceString(record.value('age')))
        self.cmbBegAgeUnit.setCurrentIndex(begUnit)
        self.edtBegAgeCount.setText(str(begCount))
        self.cmbEndAgeUnit.setCurrentIndex(endUnit)
        self.edtEndAgeCount.setText(str(endCount))

        itemId = self.itemId()
        
        self.modelProperties.loadItems(itemId)
        self.modelTestators.loadItems(itemId)
        self.modelRelations.loadItems(itemId)
        setRBComboBoxValue( self.cmbQuotaType,      record, 'quotaType_id')
        self.modelServiceByFinanceType.loadItems(itemId)
        self.modelQuotaType.loadItems(itemId)
        self.modelUETandActionSpecification.loadItems(itemId)
        self.modelTissueType.loadItems(itemId)
        self.modelNomenclature.loadItems(itemId)
        self.modelSpeciality.loadItems(itemId)
        self.modelOrgStructure.loadItems(itemId)
        self.modelEquipment.loadItems(itemId)
        self.modelActionFunctions.loadItems(itemId)
        self.modelIdentification.loadItems(itemId)
        self.setIsDirty(False)
#        self.on_modelProperties_dataChanged(self.modelProperties.index(0, self.modelProperties.ciSetting), self.modelProperties.index(0, self.modelProperties.ciSetting))


    def getRecord(self):
        record = CItemEditorBaseDialog.getRecord(self)
        getLineEditValue(   self.edtCode,                      record, 'code')
        getLineEditValue(   self.edtName,                      record, 'name')
        getLineEditValue(   self.edtTitle,                     record, 'title')
        getComboBoxValue(   self.cmbClass,                     record, 'class')
        getRBComboBoxValue( self.cmbGroup,                     record, 'group_id')
        getLineEditValue(   self.edtFlatCode,                  record, 'flatCode')
        getCheckBoxValue(   self.chkIsMES,                     record, 'isMES')
        getCheckBoxValue(   self.chkIsPreferable,              record, 'isPreferable')
        getRBComboBoxValue( self.cmbNomenclativeService,       record, 'nomenclativeService_id')
        getRBComboBoxValue( self.cmbPrescribedType,            record, 'prescribedType_id')
        getRBComboBoxValue( self.cmbShedule,                   record, 'shedule_id')
        getRBComboBoxValue( self.cmbServiceType,               record, 'serviceType')
        getComboBoxValue(   self.cmbExposeDateSelector,        record, 'exposeDateSelector')
        getComboBoxValue(   self.cmbSex,                       record, 'sex')
        getCheckBoxValue(   self.chkNomenclatureExpense,       record, 'isNomenclatureExpense')
        getCheckBoxValue(   self.chkDoesNotInvolveExecutionCourse, record, 'isDoesNotInvolveExecutionCourse')
        getCheckBoxValue(   self.chkGenerateStockMotionReason, record, 'generateStockMotionReason')
        getCheckBoxValue(   self.chkGenerateAfterEventExecDate, record, 'generateAfterEventExecDate')
        getRBComboBoxValue( self.cmbDefaultStatus,             record, 'defaultStatus')
        getComboBoxValue(   self.cmbDefaultDirectionDate,      record, 'defaultDirectionDate')
        getComboBoxValue(   self.cmbDefaultPlannedEndDate,     record, 'defaultPlannedEndDate')
        getComboBoxValue(   self.cmbPlannedEndDateRequired,    record, 'isPlannedEndDateRequired')
        getComboBoxValue(   self.cmbDefaultBegDate,            record, 'defaultBegDate')
        getComboBoxValue(   self.cmbDefaultEndDate,            record, 'defaultEndDate')
        getComboBoxValue(   self.cmbDefaultSetPersonInEvent,      record, 'defaultSetPersonInEvent')
        getRBComboBoxValue( self.cmbDefaultExecPerson,         record, 'defaultExecPerson_id')
        getComboBoxValue(   self.cmbDefaultPersonInEvent,      record, 'defaultPersonInEvent')
        getComboBoxValue(   self.cmbDefaultPersonInEditor,     record, 'defaultPersonInEditor')
        getComboBoxValue(   self.cmbExecPersonRequired,        record, 'isExecPersonRequired')
        getComboBoxValue(   self.cmbDefaultMKB,                record, 'defaultMKB')
        getComboBoxValue(   self.cmbMKBRequired,               record, 'isMKBRequired')
        getComboBoxValue(   self.cmbIsMorphologyRequired,      record, 'isMorphologyRequired')
        getComboBoxValue(   self.cmbNeedAttachFile,            record, 'isNeedAttachFile')
        getLineEditValue(   self.edtOffice,                    record, 'office')
        getSpinBoxValue(    self.edtActualAppointmentDuration, record, 'actualAppointmentDuration')
        getSpinBoxValue(    self.edtExpirationDate,            record, 'expirationDate')
        getCheckBoxValue(   self.chkRestrictExpirationDate,    record, 'isRestrictExpirationDate')
        getCheckBoxValue(   self.chkShowInForm,                record, 'showInForm')
        getCheckBoxValue(   self.chkEditStatus,                record, 'editStatus')
        getCheckBoxValue(   self.chkEditBegDate,               record, 'editBegDate')
        getCheckBoxValue(   self.chkEditEndDate,               record, 'editEndDate')
        getCheckBoxValue(   self.chkEditExecPers,              record, 'editExecPers')
        getCheckBoxValue(   self.chkEditNote,                  record, 'editNote')
        getCheckBoxValue(   self.chkRequiredActionSpecification, record, 'requiredActionSpecification')
        getCheckBoxValue(   self.chkUsesCycles,                record, 'isUsesCycles')
        getDateEditValue(   self.edtBegDate,                   record, 'begDate')
        getDateEditValue(   self.endEndDate,                   record, 'endDate')
        getCheckBoxValue(   self.chkShowBegDate,               record, 'showBegDate')
        getCheckBoxValue(   self.chkDuplication,               record, 'duplication')
        getCheckBoxValue(   self.chkIgnoreVisibleRights,       record, 'ignoreVisibleRights')
        getCheckBoxValue(   self.chkEditSetPerson,             record, 'editSetPerson')
        getCheckBoxValue(   self.chkEditOrg,                   record, 'editOrg')
        getCheckBoxValue(   self.chkEditOrgStructure,          record, 'editOrgStructure')
        getCheckBoxValue(   self.chkGenTimetable,              record, 'genTimetable')
        getCheckBoxValue(   self.chkShowTime,                  record, 'showTime')
        getCheckBoxValue(   self.chkRequiredCoordination,      record, 'isRequiredCoordination')
        getCheckBoxValue(   self.chkHasAssistant,              record, 'hasAssistant')
        getLineEditValue(   self.edtContext,                   record, 'context')
        getSpinBoxValue(    self.edtAmount,                    record, 'amount')
        getComboBoxValue(   self.cmbAmountEvaluation,          record, 'amountEvaluation')
        getSpinBoxValue(    self.edtMaxOccursInEvent,          record, 'maxOccursInEvent')
        getSpinBoxValue(    self.edtTicketDuration,            record, 'ticketDuration')
        getRBComboBoxValue( self.cmbQuotaType,                 record, 'quotaType_id')
        getCheckBoxValue(   self.chkPropertyAssignedVisible,   record, 'propertyAssignedVisible')
        getCheckBoxValue(   self.chkPropertyAssignedRequired,  record, 'propertyAssignedRequired')
        getCheckBoxValue(   self.chkPropertyUnitVisible,       record, 'propertyUnitVisible')
        getCheckBoxValue(   self.chkPropertyNormVisible,       record, 'propertyNormVisible')
        getCheckBoxValue(   self.chkPropertyEvaluationVisible, record, 'propertyEvaluationVisible')
        getCheckBoxValue(   self.chkPropertyCommentVisible,    record, 'propertyCommentVisible')

        getRBComboBoxValue( self.cmbNomenclatureOrgStructure,  record, 'nomenclatureOrgStructure_id')
        getRBComboBoxValue( self.cmbNomenclatureClass,         record, 'nomenclatureClass_id')
        getRBComboBoxValue( self.cmbNomenclatureKind,          record, 'nomenclatureKind_id')
        getRBComboBoxValue( self.cmbNomenclatureType,          record, 'nomenclatureType_id')
        getRBComboBoxValue( self.cmbNomenclatureNumberCounter, record, 'nomenclatureCounter_id')

        getCheckBoxValue(   self.chkCloseEvent,                record, 'closeEvent')

        getCheckBoxValue(   self.chkAddVisit,                  record, 'addVisit')
        getRBComboBoxValue( self.cmbAddVisitScene,             record, 'addVisitScene_id')
        getRBComboBoxValue( self.cmbAddVisitType,              record, 'addVisitType_id')

        getDoubleBoxValue(    self.edtUetAdultDoctor,                    record, 'adultUetDoctor')
        getDoubleBoxValue(    self.edtUetChildDoctor,                    record, 'childUetDoctor')
        getDoubleBoxValue(    self.edtUetAdultAvarageMedWorker,                    record, 'adultUetAverageMedWorker')
        getDoubleBoxValue(    self.edtUetChildAvarageMedWorker,                    record, 'childUetAverageMedWorker')

        getDoubleBoxValue(    self.edtAssistantUetAdultDoctor,                    record, 'assistantAdultUetDoctor')
        getDoubleBoxValue(    self.edtAssistantUetChildDoctor,                    record, 'assistantChildUetDoctor')
        getDoubleBoxValue(    self.edtAssistantUetAdultAvarageMedWorker,                    record, 'assistantAdultUetAverageMedWorker')
        getDoubleBoxValue(    self.edtAssistantUetChildAvarageMedWorker,                    record, 'assistantChildUetAverageMedWorker')

        record.setValue('defaultOrg_id', QVariant(self.cmbDefaultOrg.value()))

        record.setValue('age',        toVariant(composeAgeSelector(
                    self.cmbBegAgeUnit.currentIndex(),  forceStringEx(self.edtBegAgeCount.text()),
                    self.cmbEndAgeUnit.currentIndex(),  forceStringEx(self.edtEndAgeCount.text())
                        )))
        return record


    def saveInternals(self, id):
        self.modelProperties.saveItems(id)
        self.modelTestators.saveItems(id)
        self.modelRelations.saveItems(id)
        self.modelServiceByFinanceType.saveItems(id)
        self.modelQuotaType.saveItems(id)
        self.modelUETandActionSpecification.saveItems(id)
        self.modelTissueType.saveItems(id)
        self.modelNomenclature.saveItems(id)
        self.modelSpeciality.saveItems(id)
        self.modelOrgStructure.saveItems(id)
        self.modelEquipment.saveItems(id)
        self.modelActionFunctions.saveItems(id)
        self.modelIdentification.saveItems(id)


    def setClass(self, _class):
        if _class:
            self.cmbClass.setCurrentIndex(_class)


    def setGroupId(self, groupId):
        self.cmbGroup.setValue(groupId)


    def checkDataEntered(self):
        result = CItemEditorBaseDialog.checkDataEntered(self)
#        result = result and (self.cmbPurpose.value() or self.checkInputMessage(u'назначение', False, self.cmbPurpose))
        result = result and self.checkPropertiesDataEntered()
        result = result and self.checkUETandActionSpecificationDataEntered()
        result = result and checkIdentification(self, self.tblIdentification)
        result = result and self.checkNomenclatureDataEntered()
        return result


    def checkNomenclatureDataEntered(self):
        def getFirstRow(currentGroup):
            records = self.modelNomenclature.items()
            for i, record in enumerate(records):
                if currentGroup == forceInt(record.value('selectionGroup')):
                    return i
            return None
        result = True
        self.modelNomenclature.items().sort(key = lambda item: (forceInt(item.value('selectionGroup')), forceBool(item.value('available'))))
        self.modelNomenclature.reset()
        group = 0
        isAvailable = False
        if len(self.modelNomenclature.items()) > 0:
            for row, item in enumerate(self.modelNomenclature.items()):
                nomenclatureId = forceRef(item.value('nomenclature_id'))
                if not nomenclatureId:
                    return self.checkValueMessage(u'Не выбрано ЛСиИМН', False, self.tblNomenclature, row, item.indexOf('nomenclature_id'))
                available = forceBool(item.value('available'))
                selectionGroup = forceInt(item.value('selectionGroup'))
                if available and not selectionGroup:
                    return self.checkValueMessage(u'У ЛСиИМН, доступного для выбора, должна быть задана группа.', False, self.tblNomenclature, row, item.indexOf('selectionGroup'))
                if group != selectionGroup and row > 0 and group > 0:
                    if not isAvailable:
                        return self.checkValueMessage(u'Группа не может быть образована из недоступных для выбора ЛСиИМН.', False, self.tblNomenclature, getFirstRow(group), item.indexOf('available'))
                    else:
                        isAvailable = available
                else:
                    if available:
                        isAvailable = available
                group = selectionGroup
            if not isAvailable:
                items = self.modelNomenclature.items()
                item = items[-1]
                selectionGroup = forceInt(item.value('selectionGroup'))
                if bool(selectionGroup):
                    return self.checkValueMessage(u'Группа не может быть образована из недоступных для выбора ЛСиИМН.', False, self.tblNomenclature, getFirstRow(selectionGroup), item.indexOf('available'))
        return result


    def checkUETandActionSpecificationDataEntered(self):
        if len(self.modelUETandActionSpecification.items()):
            for row, item in enumerate(self.modelUETandActionSpecification.items()):
                if not forceInt(item.value('actionSpecification_id')):
                    return self.checkValueMessage(u'Укажите особенность выполнения действия',
                                              False, self.tblUETandActionSpecification, row, item.indexOf('actionSpecification_id'))
            return True
        else:
            return True


    def checkPropertiesDataEntered(self):
        toCheckCourse = []
        variables = set()
        for row, item in enumerate(self.modelProperties.items()):
            if not self.checkPropertyDataEntered(row, item):
                return False
            var = forceString(item.value('var'))
            if var:
                if var in variables:
                    self.checkValueMessage(u'Необходимо указать уникальное имя переменной', False, self.tblProperties, row, item.indexOf('var'))
                    return False
                variables.add(var)
            toCheckCourse.append((row, item))
        for row, item in enumerate(self.modelProperties.items()):
            expr = forceString(item.value('expr'))
            if expr:
                ok, message = checkExpr(expr, variables)
                if not ok:
                    self.checkValueMessage(message, False, self.tblProperties, row, item.indexOf('expr'))
                    return False

        prevCourse = None
        for row, item in sorted(toCheckCourse, key=lambda x: forceInt(x[1].value('course'))):
            course = forceInt(item.value('course'))
            if prevCourse is None:
                if course != 1:
                    return self.checkValueMessage(u'Курс должен начинаться с `1`',
                                                  False, self.tblProperties, row, item.indexOf('course'))
            elif course-prevCourse > 1:
                return self.checkValueMessage(u'В последовательности курса пропущен курс `%s`' % (course - 1),
                                              False, self.tblProperties, row, item.indexOf('course'))
            prevCourse = course
        return True


    def checkPropertyDataEntered(self, row, item):
        name = forceString(item.value('name'))
        var  = forceString(item.value('var'))
        typeName = forceString(item.value('typeName'))

        result = name or self.checkInputMessage(u'наименование свойства', False, self.tblProperties, row, item.indexOf('name'))
        result = result and (typeName or self.checkInputMessage(u'тип свойства', False, self.tblProperties, row, item.indexOf('typeName')))
        result = result and (not var or isIdentifier(var) or self.checkValueMessage(u'Необходимо указать допустимое имя переменной', False, self.tblProperties, row, item.indexOf('var')))
        return result


    def setCmbNomenclatureTypeFilter(self):
        nomenclatureKindId = self.cmbNomenclatureKind.value()
        if nomenclatureKindId:
            self.cmbNomenclatureType.setFilter('kind_id=%d'%nomenclatureKindId)
        else:
            nomenclatureClassId = self.cmbNomenclatureClass.value()
            if nomenclatureClassId:
                db = QtGui.qApp.db
                nomenclatureKindIdList = db.getIdList('rbNomenclatureKind', 'id', 'class_id=%d'%nomenclatureClassId)
                if nomenclatureKindIdList:
                    table = db.table('rbNomenclatureType')
                    self.cmbNomenclatureType.setFilter(table['kind_id'].inlist(nomenclatureKindIdList))
                else:
                    self.cmbNomenclatureType.setFilter('')
            else:
                self.cmbNomenclatureType.setFilter('')


    @pyqtSignature('int')
    def on_cmbNomenclatureClass_currentIndexChanged(self, index):
        nomenclatureClassId = self.cmbNomenclatureClass.value()
        if nomenclatureClassId:
            self.cmbNomenclatureKind.setFilter('class_id=%d'%nomenclatureClassId)
        else:
            self.cmbNomenclatureKind.setFilter('')

        self.setCmbNomenclatureTypeFilter()


    @pyqtSignature('int')
    def on_cmbNomenclatureKind_currentIndexChanged(self, index):
        self.setCmbNomenclatureTypeFilter()


    # @pyqtSignature('bool')
    # def on_chkNomenclatureExpense_toggled(self, value):
    #     self.tabWidget.setTabEnabled(CActionTypeEditor.tabNomenclatureExpenseIndex, value)



    @pyqtSignature('')
    def on_btnSelectService_clicked(self):
        serviceId = selectService(self, self.cmbNomenclativeService)
        if serviceId:
            self.cmbNomenclativeService.setValue(serviceId)


    @pyqtSignature('int')
    def on_cmbNomenclativeService_currentIndexChanged(self, index):
        self.btnSetName.setEnabled(bool(self.cmbNomenclativeService.value()))


    @pyqtSignature('')
    def on_btnSetName_pressed(self):
        index = self.cmbNomenclativeService.currentIndex()
        name = self.cmbNomenclativeService.model().getName(index)
        self.edtName.setText(name)
        self.edtTitle.setText(name)


    @pyqtSignature('int')
    def on_cmbClass_currentIndexChanged(self, classCode):
        fiter = 'class=%d and deleted = 0' % classCode
        self.cmbGroup.setFilter(fiter)
        self.cmbPrescribedType.setFilter(fiter)
        # self.modelActionFunctions.cols()[0].setFilter(''' ActionType.flatCode LIKE '%%direction%%' AND ActionType.class = %d AND ActionType.deleted = 0''' % (classCode))


    @pyqtSignature('int')
    def on_cmbPrescribedType_currentIndexChanged(self, index):
        self.cmbShedule.setEnabled(bool(self.cmbPrescribedType.value()))


    # @pyqtSignature('QString')
    # def on_edtFlatCode_textChanged(self, text):
    #     if text and text[0] == 's':
    #         newFilter = self.socFilter
    #     else:
    #         newFilter = ''
    #     self.modelProperties._cols[self.modelProperties._mapFieldNameToCol['test_id']].filter = newFilter


    @pyqtSignature('')
    def on_actDuplicate_triggered(self):
        index = self.tblProperties.currentIndex()
        row = index.row()
        items = self.modelProperties.items()
        if 0<=row<len(items):
            newItem = QtSql.QSqlRecord(items[row])
            newItem.setValue('id', QVariant())
#            nameDubl = forceString(newItem.value('name'))
#            countDubl = nameDubl.count(u'*')
#            copyCountMax = countDubl
#            for item in items:
#                name = forceString(item.value('name'))
#                if name.replace(u'*', '') == nameDubl.replace(u'*', ''):
#                    copyCountMax = max(name.count(u'*'), copyCountMax)
#            newItem.setValue('name', QVariant((u'*'*(copyCountMax-countDubl+1))+nameDubl))
            newItem.setValue('name', QVariant(u'*'+forceString(newItem.value('name'))))
            self.modelProperties.insertRecord(row+1, newItem)


    @pyqtSignature('')
    def on_actCopy_triggered(self):
        rows = self.tblProperties.getSelectedRows()

        if rows != []:
            strList = ','.join(forceString(self.modelProperties.value(row, 'id')) for row in rows)
            mimeData = QMimeData()
            v = toVariant(strList)
            mimeData.setData(self.parentWidget().mimeTypeActionPropertyIdList, v.toByteArray())
            QtGui.qApp.clipboard().setMimeData(mimeData)


    @pyqtSignature('')
    def on_actSelectAll_triggered(self):
        self.tblProperties.selectAll()


    @pyqtSignature('')
    def on_actClearSelection_triggered(self):
        self.tblProperties.clearSelection()


class CActionPropertyTemplateCol(CInDocTableCol):
    tableName = 'ActionPropertyTemplate'

    def toString(self, val, record):
        cache = CRBModelDataCache.getData(self.tableName, True)
        id = forceRef(val)
        if id:
            text = cache.getStringById(id, CRBComboBox.showName)
        else:
            text = ''
        return toVariant(text)


    def toStatusTip(self, val, record):
        cache = CRBModelDataCache.getData(self.tableName, True)
        id = forceRef(val)
        if id:
            code = cache.getStringById(id, CRBComboBox.showCode)
            name = cache.getStringById(id, CRBComboBox.showName)
            text = name + ' ('+code+')'
        else:
            text = ''
        return toVariant(text)


    def createEditor(self, parent):
        editor = CActionPropertyTemplateComboBox(parent)
        return editor


    def setEditorData(self, editor, value, record):
        editor.setValue(forceRef(value))


    def getEditorData(self, editor):
        return toVariant(editor.value())
        

class CPropertiesModel(CInDocTableModel):
    # ciSetting = 9

    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'ActionPropertyType', 'id', 'actionType_id', parent)
#        self.addCol(CBoolInDocTableCol( u'Удалено',        'deleted',  3))
        self.addCol(CActionPropertyTemplateCol(u'Шаблон',  'template_id', 40))
        self.addCol(CInDocTableCol(     u'Наименование',   'name',    12))
        self.addCol(CInDocTableCol(     u'Короткое наименование', 'shortName', 32, maxLength=32))
        self.addCol(CInDocTableCol(     u'Комментарий',    'comment',   30))
        self.addCol(CInDocTableCol(     u'Описание',       'descr',   12))
        self.addCol(CInDocTableCol(u'Секция CDA', 'sectionCDA', 12, maxLength=255))
        self.addCol(CInDocTableCol(     u'Переменная',     'var',     12))
        self.addCol(CInDocTableCol(     u'Выражение',      'expr',    12))
        self.addCol(CSelectStrInDocTableCol(
            u'Тип', 'typeName', 9,
            sorted(CActionPropertyValueTypeRegistry.nameList),
            ))
        self.addCol(CRBInDocTableCol(   u'Ед.изм.',        'unit_id', 6, 'rbUnit'))
        self.addCol(CInDocTableCol(     u'Настройка',      'valueDomain', 25))
        self.addCol(CInDocTableCol(     u'Наследование',      'dataInheritance', 25))
#        self.addCol(CDomainInDocTableCol(     u'Настройка',      'valueDomain', 25))
        self.addCol(CInDocTableCol(     u'Штраф',          'penalty',    4))
        self.addCol(CBoolInDocTableCol( u'Заполнение',     'isFill',     6))
        self.addCol(CInDocTableCol(     u'Значение по умолчанию', 'defaultValue', 25))
        self.addCol(CBoolInDocTableCol( u'Вектор',         'isVector', 6))
        self.addCol(CInDocTableCol(     u'Норматив',       'norm',    12))
        self.addCol(CEnumInDocTableCol( u'Пол',            'sex',  5, SexList))
        self.addCol(CInDocTableCol(     u'Возраст',        'age',  12))
        self.addCol(CBoolInDocTableCol( u'Видимость при выполнении работ',  'visibleInJobTicket',  12))
        self.addCol(CEnumInDocTableCol( u'Видимость в табличном редакторе',
                                        u'visibleInTableEditor',  12,
                                       [u'Не видно',
                                        u'Режим редактирования',
                                        u'Без редактирования']))
        self.addCol(CEnumInDocTableCol( u'Право редактирования',
                                        u'canChangeOnlyOwner',  12,
                                       [u'Все',
                                        u'Назначивший действие',
                                        u'Исполнитель действия',
                                        u'Никто',]))
        self.addCol(CBoolInDocTableCol( u'Назначаемый',     'isAssignable', 6))
        self.addCol(CRBTestSearchInDocTableCol(u'Тест', 'test_id', 20, 'rbTest', showFields = CRBComboBox.showNameAndCode, prefferedWidth=600))
        self.addCol(CEnumInDocTableCol( u'Оценка',          'defaultEvaluation', 10, [u'не определять',
                                                                                     u'автомат',
                                                                                     u'полуавтомат',
                                                                                     u'ручное']))
        self.addCol(CBoolInDocTableCol( u'Задаёт наименование действия', 'isActionNameSpecifier', 10))
        self.addCol(CInDocTableCol(     u'Лаб. Калькулятор', 'laboratoryCalculator', 5))
        self.addCol(CEnumInDocTableCol( u'В таблице выбираемых Действий', 'inActionsSelectionTable', 15, [u'Не определено',
                                                                                                          u'Recipe',
                                                                                                          u'Doses',
                                                                                                          u'Signa',
                                                                                                          u'ActiveSubstance',
                                                                                                          u'Reaction',
                                                                                                          u'CancelDate']))
        self.addCol(CEnumInDocTableCol( u'В Плане операционного дня', 'inPlanOperatingDay', 15, [u'не определено',
                                                                                                 u'ассистент',
                                                                                                 u'анестезиолог',
                                                                                                 u'ассистент анестезиолога',
                                                                                                 u'особые отметки',
                                                                                                 u'длительность операции',
                                                                                                 u'номер по порядку',
                                                                                                 u'работа',
                                                                                                 u'предоперационный диагноз']))
        self.addCol(CEnumInDocTableCol( u'Во врачебной формулировке диагноза', 'inMedicalDiagnosis', 15, [u'не определено',
                                                                                                          u'Основной',
                                                                                                          u'Осложнения',
                                                                                                          u'Сопутствующие']))
        self.addCol(CIntInDocTableCol( u'Коэффициент размера', 'editorSizeFactor', 10, low=-5, high=5))
        self.addCol(CIntInDocTableCol(u'Курс', 'course', 10, low=1, high=255))
        self.addCol(CFloatInDocTableCol(u'Минимальное значение', 'lowValue', 10, precision=2))   # Для построения графиков
        self.addCol(CFloatInDocTableCol(u'Максимальное значение', 'highValue', 10, precision=2)) # Для построения графиков


    def getEmptyRecord(self):
        record = CInDocTableModel.getEmptyRecord(self)
        record.setValue('course', toVariant(1))
        return record


#    def afterUpdateEditorGeometry(self, editor, index):
#        if index.column() in (self.ciSetting,):
#            editor.resize(editor.width(), 12*editor.height())
##            QObject.parent(self).tblProperties.resizeRowsToContents()


    def setData(self, index, value, role=Qt.EditRole):
        column = index.column()
        row = index.row()
        col = self._cols[column]
        if role == Qt.EditRole:
            if len(self._items) > 0 and len(self._items) > row:
                if column == self.getColIndex('typeName'):
                    record = self._items[row]
                    typeName = forceString(record.value(col.fieldName()))
                    typeId = forceRef(record.value('id'))
                    newTypeName = forceString(value)
                    textPropertyTypes = ['Text', 'String', 'Constructor', u'Счетчик', u'Жалобы']
                    refereceColumnsTypes = ['ReferenceColumns', 'ReferenceColumnsTree']
                    if not (newTypeName in textPropertyTypes and typeName in textPropertyTypes) and \
                       not (newTypeName in refereceColumnsTypes and typeName in refereceColumnsTypes):
                        if newTypeName != typeName and typeId:
                            valueDomain = forceString(record.value('valueDomain'))
                            templateId = forceRef(record.value('template_id'))
                            testId = forceRef(record.value('test_id'))
                            if not self.checkEditTypeProperty(typeName, typeId, valueDomain, templateId, testId):
                                QtGui.QMessageBox.critical(QObject.parent(self),
                                                           u'Внимание!',
                                                           u'''Изменение типа данных невозможно, т.к. существуют Действия с соответствующим типом данных. Используйте утилиту "Корректор свойств".''',
                                                           QtGui.QMessageBox.Close,
                                                           QtGui.QMessageBox.Close)
                                return False
        result = CInDocTableModel.setData(self, index, value, role)
        if result and role == Qt.EditRole:
            column = index.column()
            row = index.row()
            if column == 0:
                name = forceStringEx(self.data(index.sibling(row, 1)))
                # descr = forceStringEx(self.data(index.sibling(row, 2)))
                if not name:
                    template = forceStringEx(self.data(index))
                    CInDocTableModel.setData(self, index.sibling(row, 1), QVariant(template))
                    CInDocTableModel.setData(self, index.sibling(row, 2), QVariant(template))
                    self.emitCellChanged(row, 1)
                    self.emitCellChanged(row, 2)
        return result


    def checkEditTypeProperty(self, typeName, typeId, valueDomain, templateId, testId):
        if not typeId and not typeName:
            return True
        if testId:
            return False
        db = QtGui.qApp.db
        if templateId:
            tableAPTemplate = db.table('ActionPropertyTemplate')
            record = db.getRecordEx(tableAPTemplate, [tableAPTemplate['id']], [tableAPTemplate['id'].eq(templateId), tableAPTemplate['deleted'].eq(0)])
            if record and forceBool(record.value('id')):
                return False
        classTypeName = CActionPropertyValueTypeRegistry.mapNameToValueType.get(typeName.lower(), None)
        if not classTypeName:
            return False
        tableAP = db.table('ActionProperty')
        tableAPT = db.table('ActionPropertyType')
        tableAPP = db.table(classTypeName(valueDomain).getTableName())
        table = tableAP.innerJoin(tableAPP, tableAPP['id'].eq(tableAP['id']))
        table = table.innerJoin(tableAPT, tableAPT['id'].eq(tableAP['type_id']))
        cond = [tableAP['deleted'].eq(0),
                tableAPT['deleted'].eq(0),
                tableAPT['id'].eq(typeId),
                tableAPP['value'].isNotNull(),
                tableAPT['typeName'].like(typeName)]
        record = db.getRecordEx(table, [tableAPP['id']], cond)
        if record and forceBool(record.value('id')):
            return False
        return True


class CTestatorsModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'ActionType_Testator', 'id', 'master_id', parent)
        self.addCol(CActionTypeTableCol(u'Предшественник',   'testator_id',20, None, classesVisible=True))


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
                if column == self.getColIndex('testator_id'):
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
            if noWriteList and column == self.getColIndex('testator_id'):
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


class CServiceByFinanceTypeModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'ActionType_Service', 'id', 'master_id', parent)
        self.addCol(CRBInDocTableCol(   u'Тип финансирования', 'finance_id', 15, 'rbFinance'))
        self.addCol(
            CRBSearchInDocTableCol(u'Услуга', 'service_id', 15, 'rbService', showFields=CRBComboBox.showNameAndCode,
                                   filter='current_date() between begDate and endDate'))
        self.serviceRecordCache = CTableRecordCache(QtGui.qApp.db, 'rbService', ['id', 'endDate'])

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid() and role == Qt.FontRole:
            row = index.row()
            column = index.column()
            if 0 <= row < len(self._items):
                if column == 1:
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
                if column == 1:
                    serviceId = forceInt(self.items()[row].value('service_id'))
                    serviceRecord = self.serviceRecordCache.get(serviceId) if serviceId else None
                    if serviceRecord:
                        if forceDate(serviceRecord.value('endDate')) <= QDate.currentDate():
                            return u"Данная услуга не является актуальной"
                        else:
                            return u""

        return CInDocTableModel.data(self, index, role)


class CQuotaTypeModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'ActionType_QuotaType', 'id', 'master_id', parent)
        self.addCol(CRBInDocTableCol(   u'Тип финансирования',  'finance_id',   15, 'rbFinance'))
        self.addCol(CEnumInDocTableCol( u'Класс квоты',           'quotaClass', 10, [u'ВТМП']))
        self.addCol(CRBInDocTableCol(   u'Вид квоты',           'quotaType_id', 15, 'QuotaType'))


class CUETandActionSpecificationModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'ActionType_UETActionSpecification', 'id', 'master_id', parent)
        self.addCol(CRBInDocTableCol(   u'Особенность выполнения действия',  'actionSpecification_id',   15, 'rbActionSpecification'))
        self.addCol(CBoolInDocTableCol( u'Для ассистента',            'isAssistant', 10, precision=2))
        self.addCol(CFloatInDocTableCol( u'Взрослый УЕТ для врача',            'adultUetDoctor', 10, precision=2))
        self.addCol(CFloatInDocTableCol( u'Детский УЕТ для врача',            'childUetDoctor', 10, precision=2))
        self.addCol(CFloatInDocTableCol( u'Взрослый УЕТ для среднего мед. персонала',            'adultUetAverageMedWorker', 10, precision=2))
        self.addCol(CFloatInDocTableCol( u'Детский УЕТ для среднего мед. персонала',            'childUetAverageMedWorker', 10, precision=2))


class CTissueTypeModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'ActionType_TissueType', 'id', 'master_id', parent)
        self.addCol(CRBInDocTableCol(  u'Тип работы',            'jobType_id', 15, 'rbJobType', showFields=CRBComboBox.showNameAndCode))
        self.addCol(CRBInDocTableCol(  u'Тип биоматериала',      'tissueType_id', 15, 'rbTissueType'))
        self.addCol(CIntInDocTableCol( u'Количество',            'amount', 10))
        self.addCol(CRBInDocTableCol(  u'Ед. измерения',         'unit_id', 13, 'rbUnit'))
        self.addCol(CRBInDocTableCol(  u'Тип контейнера',        'containerType_id', 10, 'rbContainerType', showFields=CRBComboBox.showNameAndCode))
        self.addCol(CIntInDocTableCol( u'Курс',                  'course', 10, low=1, high=255))


    def getEmptyRecord(self):
        record = CInDocTableModel.getEmptyRecord(self)
        record.setValue('course', toVariant(1))
        return record


class CNomenclatureModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'ActionType_Nomenclature', 'id', 'master_id', parent)
        self.addCol(CNomenclatureInDocTableCol(u'ЛСиИМН', 'nomenclature_id', 15, showFields = CRBComboBox.showName))
        self.addCol(CEnumInDocTableCol(u'Время списания', 'writeoffTime', 15, [u'По назначению действия', u'По закрытию действия']))
        self.addCol(CFloatInDocTableCol(u'Количество', 'amount', 10, precision=2))
        self.addCol(CBoolInDocTableCol( u'Доступно для выбора', 'available', 3))
        self.addCol(CIntInDocTableCol(  u'Группа выбора',  'selectionGroup', 15, low=-100, high=100))


    def sort(self, col, order=Qt.AscendingOrder):
        reverse = order == Qt.DescendingOrder
        if col == 0:
            self.items().sort(key=lambda x: forceString(self.cols()[col].toString(x.value(self.cols()[col].fieldName()), x)) if x else None, reverse=reverse)
        else:
            self.items().sort(key=lambda x: forceDouble(x.value(col)) if x else None, reverse=reverse)  
        self.reset()


class CRelationsModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'ActionType_Relations', 'id', 'master_id', parent)
        self.addCol(CActionTypeTableCol(u'Подчиненный',   'related_id',40, None, classesVisible=True)).setSortable(True)
        self.addCol(CBoolInDocTableCol(u'Обязательность', 'isRequired', 10)).setSortable(True)
        self.masterId = None

    
    def loadItems(self, masterId):
        self.masterId = masterId
        super(CRelationsModel, self).loadItems(masterId)
        
    
    def getActionTypeCluster(self, actionTypeId):
        db = QtGui.qApp.db
        tableActionType = db.table('ActionType')
        result = db.getLeafes(tableActionType,
                              'group_id',
                              actionTypeId,
                              tableActionType['deleted'].eq(0)
                             )
        return sorted(result) if result else [actionTypeId]

    
    def checkAvailability(self, actionType_id):
        if actionType_id == self.masterId:
            QtGui.QMessageBox.warning(None,
                    u'Внимание!',
                    u'Тип действия совпадает с подчиненным типом действием! Невозможно добавить!',
                    QtGui.QMessageBox.Cancel,
                    QtGui.QMessageBox.Cancel)
            return False
        db = QtGui.qApp.db
        tableATR = db.table('ActionType_Relations')
        tableAT = db.table('ActionType')
        table = tableATR.leftJoin(tableAT, tableATR['master_id'].eq(tableAT['id']))
        result = db.query(db.selectStmt(table,
                        'ActionType_Relations.master_id, ActionType.name',
                        'ActionType_Relations.related_id = {}'.format(self.masterId),
                        ))
        if result.next():
            message = forceString(result.record().value('master_id')) + u': ' + forceString(result.record().value('name'))
            QtGui.QMessageBox.warning(None,
                    u'Внимание!',
                    u'Невозможно добавить подчиненные типы действия!\nТекущее действие подчинено типу действия {}!'.format(message),
                    QtGui.QMessageBox.Cancel,
                    QtGui.QMessageBox.Cancel)
            return False 
        table = tableATR.leftJoin(tableAT, tableATR['master_id'].eq(tableAT['id']))
        result = db.query(db.selectStmt(table,
                        'ActionType_Relations.master_id, ActionType.name',
                        'ActionType_Relations.master_id = {}'.format(actionType_id),
                        ))
        if result.next():
            message = u'Тип действия {} имеет подчиненные действия.\nОн не может быть подчинен другому типу действия!'.format(forceString(result.record().value('master_id')) + u': ' + forceString(result.record().value('name')))
            QtGui.QMessageBox.warning(None,
                    u'Внимание!',
                    message,
                    QtGui.QMessageBox.Cancel,
                    QtGui.QMessageBox.Cancel)
            return False 
        return True

    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.EditRole:
            noWriteList = True
            column = index.column()
            row = index.row()
            if row == len(self._items):
                if value.isNull():
                    return False
                if not self.checkAvailability(forceRef(value)):
                    return False
                if column == self.getColIndex('related_id'):
                    outWriteList, noWriteList = self.writeActionTypeIdList(forceRef(value), row, column)
                    if outWriteList:
                        return True
                self._items.append(self.getEmptyRecord())
                count = len(self._items)
                rootIndex = QModelIndex()
                self.beginInsertRows(rootIndex, count, count)
                self.insertRows(count, 1, rootIndex)
                self.endInsertRows()
            if not self.checkAvailability(forceRef(value)):
                return False
            record = self._items[row]
            col = self._cols[column]
            record.setValue(col.fieldName(), value)
            self.emitCellChanged(row, column)
            if noWriteList and column == self.getColIndex('related_id'):
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

class CActionTypeTableModel(CTableModel, ActionTypeServiceMixin):
    def __init__(self, parent, cols, tableName):
        CTableModel.__init__(self, parent, cols=cols, tableName=tableName)
        ActionTypeServiceMixin.__init__(self)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        column = index.column()
        if role == Qt.FontRole and column == 3:
            record = self.getRecordByRow(index.row())
            if not record:
                return QVariant()
            actionTypeId = forceRef(record.value('id'))
            actionTypeCache = CActionTypeCache.getById(actionTypeId)
            code = actionTypeCache.code
            numService = actionTypeCache.nomenclativeServiceId
            if not self.checkActionTypeService(actionTypeId, code, numService):
                font = QFont()
                font.setItalic(True)
                font.setBold(True)
                return font

        if role == Qt.ToolTipRole and column == 3:
            record = self.getRecordByRow(index.row())
            if not record:
                return QVariant()
            actionTypeId = forceRef(record.value('id'))
            actionTypeCache = CActionTypeCache.getById(actionTypeId)
            code = actionTypeCache.code
            numService = actionTypeCache.nomenclativeServiceId
            if not self.checkActionTypeService(actionTypeId, code, numService):
                return u"Услуга в типе действия не является актуальной"
            else:
                return u""
        return CTableModel.data(self, index, role)


class CRBServiceComboBoxModel(CRBModel):
    def  __init__(self, parent):
        CRBModel.__init__(self, parent)
        self.serviceRecordCache = CTableRecordCache(QtGui.qApp.db, 'rbService', ['id', 'endDate'])

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return CRBModel.data(self, index, role)
        row = index.row()
        column = index.column()
        if row < self.d.getCount():
            if column == 1:
                serviceId = self.getId(row)
                if role == Qt.ToolTipRole:
                    serviceRecord = self.serviceRecordCache.get(serviceId) if serviceId else None
                    if serviceRecord:
                        if forceDate(serviceRecord.value('endDate')) <= QDate.currentDate():
                            return u"Данная услуга не является актуальной"
                        else:
                            return u""
                    else:
                        return u""
                if role == Qt.FontRole:
                    serviceRecord = self.serviceRecordCache.get(serviceId) if serviceId else None
                    if serviceRecord:
                        font = QFont()
                        if forceDate(serviceRecord.value('endDate')) <= QDate.currentDate():
                            font.setItalic(True)
                            font.setBold(True)
                            return font
                        else:
                            return font
        return CRBModel.data(self, index, role)

# ############################################################


class CFindDialog(CDialogBase, Ui_ActionTypeFindDialog):
    def __init__(self, parent):
        cols = [CEnumCol(   u'Класс',              ['class'], [u'статус', u'диагностика', u'лечение', u'прочие мероприятия'], 10),
                CTextCol(   u'Код',                ['code'], 20),
                CTextCol(   u'Наименование',       ['name'], 30),
                CRefBookCol(u'Номенклатурный код', ['nomenclativeService_id'], 'rbService', 10, 2),
                CRefBookCol(u'Группа',             ['group_id'], 'ActionType', 10),
                CTextCol(   u'Контекст печати',    ['context'], 10),
                CTextCol(   u'Код для отчетов',    ['flatCode'], 10)]
        CDialogBase.__init__(self, parent)
        self.addModels('ActionTypeFound', CFindActionsTableModel(self, cols, 'ActionType'))
        self.setupUi(self)
        self.setModels(self.tblActionTypeFound,   self.modelActionTypeFound, self.selectionModelActionTypeFound)
        self.cmbService.setTable('rbService')
        self.cmbTissueType.setTable('rbTissueType')
        self.setWindowTitle(u'Поиск типа действия')
        self.foundId = None
        self.props = {}
        self.tableActionType = QtGui.qApp.db.table('ActionType')
        self.tableService    = QtGui.qApp.db.table('rbService')
        self.setFocusToWidget(self.edtCode)
        self.buttonBox.button(QtGui.QDialogButtonBox.Apply).setDefault(True)
        self.buttonBox.button(QtGui.QDialogButtonBox.Apply).setShortcut(Qt.Key_Return)
        self.connect(self.tblActionTypeFound.horizontalHeader(), SIGNAL('sectionClicked(int)'), self._setActionsOrderByColumn)
        noneRecord = QtGui.qApp.db.record('rbAccountingSystem')
        noneRecord.setValue('id', QVariant())
        noneRecord.setValue('name', u'не задано')
        noneRecord.setValue('urn', QVariant())
        noneRecord.setValue('code', QVariant())
        accountingSystemItems = []
        accountingSystemItems.append(noneRecord)
        accountingSystemItems.extend(self._getAccountingSystemItems())
        self.cmbIdentificationAccountingSystem.setItems(accountingSystemItems)
        self.cmbIdentificationAccountingSystem.showPopup = types.MethodType(self._showPopup, self.cmbIdentificationAccountingSystem)
        self.cmbIdentificationAccountingSystem.setMinimumWidth(200)
        # self.cmbIdentificationAccountingSystem.setMaximumWidth(350)
        self.leIdentificationValue.setMinimumWidth(400)
        self.leIdentificationValue.setMaximumWidth(400)
        self.cmbIdentificationAccountingSystem.setCurrentIndex(0)


    def _getAccountingSystemItems(self):
        return  QtGui.qApp.db.getRecordList('rbAccountingSystem', 'id,code,name,urn,isEditable,isDeletable'," FIND_IN_SET('ActionType', REPLACE(domain, ' ', ''))>0 OR domain='' ")


    def _showPopup(self, *args, **kwargs):
        width = self.cmbIdentificationAccountingSystem.width()
        view = self.cmbIdentificationAccountingSystem.view()
        view.setMinimumWidth(width)
        view.setMaximumWidth(width)
        view.setMinimumHeight(view.rowHeight(0)*15)
        view.setMaximumHeight(view.rowHeight(0)*15)
        view.window().setFixedSize(width, view.rowHeight(0)*15 + 40)
        pos = self.cmbIdentificationAccountingSystem.mapToGlobal(QPoint(0, self.cmbIdentificationAccountingSystem.height()))
        super(CAccountingSystemComboBox, self.cmbIdentificationAccountingSystem).showPopup()
        view.window().move(pos)


    def _setActionsOrderByColumn(self, column):
        self.tblActionTypeFound.setOrder(column)
        self.findActionType(self.tblActionTypeFound.currentItemId())


    def id(self):
        return self.foundId


    def findActionType(self, posToId = None):
        tableActionType  = self.tableActionType
        tableService     = self.tableService
        code             = trim(self.edtCode.text())
        nomenclativeCode = trim(self.edtNomenclativeCode.text())
        name             = trim(self.edtName.text())
        tissyeTypeId     = self.cmbTissueType.value()
        serviceId        = self.cmbService.value()
        context          = trim(self.edtContext.text())
        codeReports      = trim(self.edtCodeReports.text())
        accountingSystemId = self.cmbIdentificationAccountingSystem.value().toString() if not self.cmbIdentificationAccountingSystem.value().isNull() else None
        identificationValue = trim(self.leIdentificationValue.text())
        table = tableActionType
        cond = [tableActionType['deleted'].eq(0)]
        order = self.tblActionTypeFound.order() if self.tblActionTypeFound.order() else ['ActionType.class, ActionType.code, ActionType.name']
        if code:
            cond.append(tableActionType['code'].like(addDotsEx(code)))
        if name:
            cond.append(tableActionType['name'].like(addDotsEx(name)))
        if context:
            cond.append(tableActionType['context'].like(addDotsEx(context)))
        if codeReports:
            cond.append(tableActionType['flatCode'].contain(codeReports))
        if nomenclativeCode:
            cond.append(tableService['code'].like(addDotsEx(nomenclativeCode)))
            table = tableActionType.innerJoin(tableService, tableActionType['nomenclativeService_id'].eq(tableService['id']))
        elif 'rbService.code' in order:
            table = tableActionType.leftJoin(tableService, tableActionType['nomenclativeService_id'].eq(tableService['id']))
        if tissyeTypeId:
            cond.append('EXISTS (SELECT id FROM ActionType_TissueType WHERE master_id=ActionType.`id` AND tissueType_id=%d)'%tissyeTypeId)
        if serviceId:
            cond.append('EXISTS (SELECT * FROM ActionType_Service WHERE master_id=ActionType.`id` AND service_id=%d)'%serviceId)
        if accountingSystemId and identificationValue:
            cond.append(u"EXISTS (SELECT * FROM ActionType_Identification WHERE master_id=ActionType.`id` AND deleted = 0 AND system_id=" + forceString(accountingSystemId) + u" AND value like '" + forceString(identificationValue) + u"') ")
        elif accountingSystemId or identificationValue:
            if accountingSystemId:
                cond.append(u"EXISTS (SELECT * FROM ActionType_Identification WHERE master_id=ActionType.`id` AND deleted = 0 AND system_id=" + forceString(accountingSystemId) + u") ")
            elif identificationValue:
                cond.append(u"EXISTS (SELECT * FROM ActionType_Identification WHERE master_id=ActionType.`id` AND deleted = 0  AND value like '" + forceString(identificationValue) + u"') ")

        idList = QtGui.qApp.db.getIdList(table, 'ActionType.`id`', cond, order)
        idCount = len(idList)
        self.tblActionTypeFound.setIdList(idList, posToId)
        self.lblRecordsCount.setText(formatRecordsCount(idCount))
        if idCount == 0:
            self.setFocusToWidget(self.edtCode)
        elif idCount == 1:
            self.foundId = idList[0]
            self.accept()


    def setProps(self, props):
        self.props = props
        self.edtCode.setText(props.get('code', ''))
        self.edtNomenclativeCode.setText(props.get('nomenclativeCode', ''))
        self.edtName.setText(props.get('name', ''))
        self.cmbTissueType.setValue(props.get('tissueType', None))
        self.cmbService.setValue(props.get('service', None))
        self.edtContext.setText(props.get('context', ''))
        self.edtCodeReports.setText(props.get('codeReports', ''))


    def getProps(self):
        return self.props


    def saveProps(self):
        self.props['code'] = trim(self.edtCode.text())
        self.props['nomenclativeCode'] = trim(self.edtNomenclativeCode.text())
        self.props['name'] = trim(self.edtName.text())
        self.props['tissueType'] = self.cmbTissueType.value()
        self.props['service'] = self.cmbService.value()
        self.props['context'] = trim(self.edtContext.text())
        self.props['codeReports'] = trim(self.edtCodeReports.text())


    def resetFindingValues(self):
        self.edtCode.clear()
        self.edtNomenclativeCode.clear()
        self.edtName.clear()
        self.cmbTissueType.setValue(None)
        self.cmbService.setValue(None)
        self.edtContext.clear()
        self.edtCodeReports.clear()
        self.cmbIdentificationAccountingSystem.setCurrentIndex(0)
        self.leIdentificationValue.clear()


    @pyqtSignature('QModelIndex')
    def on_tblActionTypeFound_doubleClicked(self, index=None):
        index = self.tblActionTypeFound.currentIndex()
        self.foundId = self.tblActionTypeFound.itemId(index)
        self.accept()


    @pyqtSignature('QAbstractButton*')
    def on_buttonBox_clicked(self, button):
        buttonCode = self.buttonBox.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Close:
            self.reject()
        elif buttonCode == QtGui.QDialogButtonBox.Apply:
            self.saveProps()
            self.findActionType()
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.resetFindingValues()


    @pyqtSignature('')
    def on_btnSelectService_clicked(self):
        serviceId = selectService(self, self.cmbService)
        if serviceId:
            self.cmbService.setValue(serviceId)


class CFindActionsTableModel(CTableModel):
    def __init__(self, parent, cols, tableName):
        CTableModel.__init__(self, parent, cols, tableName)
        self._mapColumnOrder = {'class'                  :'ActionType.class',
                                'code'                   :'ActionType.code',
                                'name'                   :'ActionType.name',
                                'nomenclativeService_id' :'rbService.code',
                                'group_id'               :'ActionType.group_id',
                                 }


    def getOrder(self, fieldName, column):
        if hasattr(self._cols[column], 'extraFields'):
            if len(self._cols[column].extraFields) > 0:
                fieldName = self._cols[column].extraFields[0]
        return self._mapColumnOrder[fieldName]

