# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2023 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QAbstractTableModel, QVariant, pyqtSignature, SIGNAL

from library.Utils                 import forceInt, forceRef, forceString, forceStringEx, toVariant, formatNum1
from library.interchange           import getComboBoxValue, getLineEditValue
from library.DialogBase            import CDialogBase
from library.ItemsListDialog       import CItemEditorBaseDialog
from library.TableModel            import CTableModel, CEnumCol, CRefBookCol, CTextCol
from library.AgeSelector           import checkAgeSelector, composeAgeSelector, parseAgeSelector
from Registry.Utils                import CCheckNetMixin
from Events.ActionTemplateChoose   import CActionTemplateModel
from RefBooks.ActionTemplate.List  import CActionTypeCol, CActionTemplateEditor
from Users.Rights import urAccessRefDeletedActionTemplate, urAccessRefUpdateOwnerActionTemplate

from Events.Ui_ActionTemplateSaveDialog   import Ui_ActionTemplateSaveDialog
from Events.Ui_ActionTemplateCreateDialog import Ui_ActionTemplateCreateDialog


class CActionTemplateSaveDialog(CDialogBase, Ui_ActionTemplateSaveDialog):
    def __init__(self,
                 parent,
                 actionRecord,
                 action,
                 clientSex,
                 clientAge,
                 personId,
                 specialityId,
                 orgStructureId,
                 SNILS,
                 showTypeTemplate
                ):
        CDialogBase.__init__(self, parent)
        actionTypeId = action.getType().id
        self.action = action.clone()
        self.addModels('Tree',  CActionTemplateTreeModel(self, actionTypeId, personId, orgStructureId, specialityId, SNILS, clientSex, clientAge, removeEmptyNodes=True, showTypeTemplate=showTypeTemplate))
        self.modelTree.setRootItemVisible(True)
        self.addModels('Table', CActionTemplateTableModel(self, self.modelTree.filter()))
        self.addModels('Properties', CPropertiesModel(self, self.action))

        self.addObject('btnCreateGroup', QtGui.QPushButton(u'Создать группу', self))
        self.addObject('btnCreateTemplate', QtGui.QPushButton(u'Создать шаблон', self))
        self.addObject('btnUpdateTemplate', QtGui.QPushButton(u'Обновить шаблон', self))
        self.addObject('actDeleteTree', QtGui.QAction(u'Удалить', self))
        self.addObject('actDeleteTable', QtGui.QAction(u'Удалить', self))
        self.addObject('actEditTree', QtGui.QAction(u'Редактировать', self))
        self.addObject('actEditTable', QtGui.QAction(u'Редактировать', self))
        self.setupUi(self)
        self.buttonBox.addButton(self.btnCreateGroup,    QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnCreateTemplate, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnUpdateTemplate, QtGui.QDialogButtonBox.ActionRole)
        self.setWindowTitleEx(u'Сохранение шаблона действия')
        self.treeItems.header().hide()

        self.setModels(self.treeItems, self.modelTree,  self.selectionModelTree)
        self.setModels(self.tblItems,  self.modelTable, self.selectionModelTable)
        self.setModels(self.tblProperties, self.modelProperties, self.selectionModelProperties)
        self.tblItems.createPopupMenu([self.actDeleteTable, self.actEditTable])
        self.treeItems.createPopupMenu([self.actDeleteTree, self.actEditTree])
        self.connect(self.treeItems.popupMenu(), SIGNAL('aboutToShow()'), self.popupMenuAboutToShowTree)
        self.connect(self.tblItems.popupMenu(), SIGNAL('aboutToShow()'), self.popupMenuAboutToShowTable)
        self.actionTypeId = actionTypeId
        self.orgStructureId = orgStructureId
        self.clientSex = clientSex
        self.clientAge = clientAge
        self.personId = personId
        self.SNILS = SNILS
        self.specialityId = specialityId
        self.showTypeTemplate = showTypeTemplate
        pref = QtGui.qApp.preferences
        props = pref.appPrefs
        self.expand = forceInt(props.get('actionTemplateTreeExpand',  QVariant()))
        self.expandLevel = forceInt(props.get('actionTemplateTreeExpandLevel',  QVariant(1)))
        self.cmbShowTypeFilter.setCurrentIndex(showTypeTemplate) if showTypeTemplate else self.on_cmbShowTypeFilter_currentIndexChanged(0)
        self.addObject('actSelectAllProperies', QtGui.QAction(u'Выделить все', self))
        self.addObject('actDeselectAllProperies', QtGui.QAction(u'Отменить выделения', self))
        self.tblProperties.addPopupActions([self.actSelectAllProperies, self.actDeselectAllProperies])
        self.connect(self.actSelectAllProperies, SIGNAL('triggered()'), self.on_actSelectAllProperies)
        self.connect(self.actDeselectAllProperies, SIGNAL('triggered()'), self.on_actDeselectAllProperies)
        self.connect(self.tblProperties.popupMenu(), SIGNAL('aboutToShow()'), self.on_properiesAboutToShow)

    
    def popupMenuAboutToShow(self, currentItemId):
        app = QtGui.qApp
        currentUserId = app.userId
        if currentItemId and currentUserId:
            isAdmin = app.isAdmin()
            db = QtGui.qApp.db
            table = db.table('ActionTemplate')
            record = db.getRecordEx(table, [table['createPerson_id'], table['owner_id']],
                                    [table['id'].eq(currentItemId), table['deleted'].eq(0)])
            createPersonId = forceRef(record.value('createPerson_id')) if record else None
            ownerId = forceRef(record.value('owner_id')) if record else None
            return bool(currentItemId) and (isAdmin or (app.userHasAnyRight(
                [urAccessRefDeletedActionTemplate]) and createPersonId == currentUserId) or (app.userHasAnyRight(
                [urAccessRefUpdateOwnerActionTemplate]) and ownerId == currentUserId))
    

    def popupMenuAboutToShowTable(self):
        currentItemId = self.tblItems.currentItemId()
        actionEnabled = self.popupMenuAboutToShow(currentItemId)
        self.actDeleteTable.setEnabled(actionEnabled)
        self.actEditTable.setEnabled(actionEnabled)
    
    
    def popupMenuAboutToShowTree(self):
        currentItemId = self.modelTree.itemId(self.treeItems.currentIndex())
        actionEnabled = self.popupMenuAboutToShow(currentItemId)
        self.actDeleteTree.setEnabled(actionEnabled)
        self.actEditTree.setEnabled(actionEnabled)


    @pyqtSignature('')
    def on_actDeleteTable_triggered(self):
        def deleteCurrentInternal():
            currentItemId = self.tblItems.currentItemId()
            if currentItemId:
                db = QtGui.qApp.db
                table = db.table('ActionTemplate')
                actionTemplateIdList = db.getDescendants(table, 'group_id', currentItemId, 'deleted=0')
                if actionTemplateIdList == [currentItemId] :
                    question = u'Удалить данную группу шаблонов?'
                else:
                    question = u'Удалить группу со всеми вложенными шаблонами\nи %s?' %\
                        formatNum1(len(actionTemplateIdList)-1,
                                    (u'входящий в неё элемент',
                                     u'входящих в неё элемента',
                                     u'входящих в неё элементов',
                                    )
                                  )
                res = QtGui.QMessageBox.question(self,
                                                    u'Подтверждение удаления',
                                                    question,
                                                    QtGui.QMessageBox.Yes|QtGui.QMessageBox.No,
                                                    QtGui.QMessageBox.No
                                                   )
                if res == QtGui.QMessageBox.Yes:
                    row = self.tblItems.currentIndex().row()
                    db.deleteRecord(table, table['id'].inlist(actionTemplateIdList))
                    self.modelTree.update()
                    if not self.expand:
                        self.treeItems.expandToDepth(0)
                    elif self.expand == 1:
                        self.treeItems.expandAll()
                    else:
                        self.treeItems.expandToDepth(self.expandLevel)
                    self.renewListAndSetTo()
                    self.updateListAndSetTo()
                    self.tblItems.setCurrentRow(row)
        QtGui.qApp.call(self, deleteCurrentInternal)

    
    @pyqtSignature('')
    def on_actDeleteTree_triggered(self):
        def deleteCurrentInternal():
            currentItemId = self.modelTree.itemId(self.treeItems.currentIndex())
            if currentItemId:
                db = QtGui.qApp.db
                table = db.table('ActionTemplate')
                actionTemplateIdList = db.getDescendants(table, 'group_id', currentItemId, 'deleted=0')
                if actionTemplateIdList == [currentItemId] :
                    question = u'Удалить данную группу шаблонов?'
                else:
                    question = u'Удалить группу со всеми вложенными шаблонами\nи %s?' %\
                        formatNum1(len(actionTemplateIdList)-1,
                                    (u'входящий в неё элемент',
                                     u'входящих в неё элемента',
                                     u'входящих в неё элементов',
                                    )
                                  )
                res = QtGui.QMessageBox.question(self,
                                                    u'Подтверждение удаления',
                                                    question,
                                                    QtGui.QMessageBox.Yes|QtGui.QMessageBox.No,
                                                    QtGui.QMessageBox.No
                                                   )
                if res == QtGui.QMessageBox.Yes:
                    db.deleteRecord(table, table['id'].inlist(actionTemplateIdList))
                    self.renewListAndSetTo()
                    self.updateListAndSetTo()
                    index = self.modelTree.index(0,0)
                    self.treeItems.setCurrentIndex(index)
        QtGui.qApp.call(self, deleteCurrentInternal)
    

    def getItemEditor(self):
        return CActionTemplateEditor(self)


    @pyqtSignature('')
    def on_actEdit_triggered(self):
        itemId = self.tblItems.currentItemId()
        if itemId:
            QtGui.qApp.setWaitCursor()
            dialog = self.getItemEditor()
            try:
                dialog.load(itemId)
                QtGui.qApp.restoreOverrideCursor()
                if dialog.exec_():
                    itemId = dialog.itemId()
                    self.modelTree.update()
                    if not self.expand:
                        self.treeItems.expandToDepth(0)
                    elif self.expand == 1:
                        self.treeItems.expandAll()
                    else:
                        self.treeItems.expandToDepth(self.expandLevel)
                    self.renewListAndSetTo(itemId)
            finally:
                dialog.deleteLater()
        else:
            self.on_actNew_triggered()


    @pyqtSignature('')
    def on_actNew_triggered(self):
        dialog = self.getItemEditor()
        try:
            dialog.setGroupId(self.currentGroupId())
            if dialog.exec_():
                itemId = dialog.itemId()
                self.modelTree.update()
                if not self.expand:
                    self.treeItems.expandToDepth(0)
                elif self.expand == 1:
                    self.treeItems.expandAll()
                else:
                    self.treeItems.expandToDepth(self.expandLevel)
                self.renewListAndSetTo(itemId)
        finally:
            dialog.deleteLater()


    def on_actSelectAllProperies(self):
        self.modelProperties.checkAll(True)


    def on_actDeselectAllProperies(self):
        self.modelProperties.checkAll(False)


    def on_properiesAboutToShow(self):
        existChecked, existNotChecked = self.modelProperties.getCheckStateInfo()
        self.actSelectAllProperies.setEnabled(existNotChecked)
        self.actDeselectAllProperies.setEnabled(existChecked)


    def currentGroupId(self):
        return self.modelTree.itemId(self.treeItems.currentIndex())


    def setProps(self, props):
        self.props = props
        self.cmbShowTypeFilter.setCurrentIndex(props.get('showTypeTemplate', 0))


    def getProps(self):
        return self.props


    def saveProps(self):
        self.props = {}
        self.props['showTypeTemplate'] = self.cmbShowTypeFilter.currentIndex()


    def select(self, props):
        db = QtGui.qApp.db
        table = self.modelTable.table()
        tableAction = db.table('Action')
        groupId = self.currentGroupId()
        cond = [table['deleted'].eq(0)]
        if groupId is not None:
            cond.append(table['group_id'].eq(groupId))
        queryTable = table.leftJoin(tableAction, db.joinAnd([tableAction['id'].eq(table['action_id']), tableAction['deleted'].eq(0)]))
        showTypeTemplate = props.get('showTypeTemplate', 0)
        if showTypeTemplate == 1:
            cond.append(table['owner_id'].eq(self.personId))
        elif showTypeTemplate == 2:
            cond.append(table['SNILS'].eq(self.SNILS))
        else:
            if self.personId:
                cond.append(db.joinOr([table['owner_id'].eq(self.personId), table['owner_id'].isNull()]))
            else:
                cond.append(table['owner_id'].isNull())
            if self.SNILS:
                cond.append(db.joinOr([table['SNILS'].eq(self.SNILS), table['SNILS'].isNull()]))
            else:
                cond.append(table['SNILS'].isNull())
        filter = self.modelTree.filter()
        if filter.actionTypeIdList:
            cond.append(db.joinOr([tableAction['actionType_id'].inlist(filter.actionTypeIdList), table['action_id'].isNull()]))
        if self.specialityId:
            cond.append(db.joinOr([table['speciality_id'].eq(self.specialityId), table['speciality_id'].isNull()]))
        else:
            cond.append(table['speciality_id'].isNull())
        if self.orgStructureId:
            cond.append(db.joinOr([table['orgStructure_id'].eq(self.orgStructureId), table['orgStructure_id'].isNull()]))
        else:
            cond.append(table['orgStructure_id'].isNull())
        if self.clientSex:
            cond.append(table['sex'].inlist([self.clientSex, 0]))
        if self.clientAge:
            idList = []
            stmt = db.selectStmt(queryTable,
                               [table['id'], table['age']],
                               cond,
                               table['name'].name())
            query = db.query(stmt)
            while query.next():
                record = query.record()
                age = forceStringEx(record.value('age'))
                if not age or checkAgeSelector(parseAgeSelector(age), self.clientAge):
                    idList.append(record.value(0).toInt()[0])
            return idList
        else:
            return db.getIdList(queryTable,
                           table['id'].name(),
                           cond,
                           table['name'].name())


    def updateListAndSetTo(self, itemId=None):
        if not itemId:
            itemId = self.modelTree.itemId(self.treeItems.currentIndex())
        self.saveProps()
        showTypeTemplate = self.props.get('showTypeTemplate', 0)
        self.modelTree.setFilter(self.actionTypeId, self.personId, self.orgStructureId, self.specialityId, self.SNILS, self.clientSex, self.clientAge, removeEmptyNodes=True, showTypeTemplate=showTypeTemplate)
        self.modelTree.reset()
        if not self.expand:
            self.treeItems.expandToDepth(0)
        elif self.expand == 1:
            self.treeItems.expandAll()
        else:
            self.treeItems.expandToDepth(self.expandLevel)
        if itemId:
            index = self.modelTree.findItemId(itemId)
            if not (index and index.isValid()):
                index = self.modelTree.index(0,0)
            self.treeItems.setCurrentIndex(index)


    def renewListAndSetTo(self, itemId=None):
        if not itemId:
            itemId = self.tblItems.currentItemId()
        self.saveProps()
        idList = self.select(self.props)
        self.tblItems.setIdList(idList, itemId)


    def updateButtons(self):
        index = self.tblItems.currentIndex()
        if index.isValid():
            flags = self.modelTable.flags(index)
            enabled = int(flags) & Qt.ItemIsEnabled
        else:
            enabled = False
        self.btnUpdateTemplate.setEnabled(enabled)


    def updateTemplate(self):
        id = self.tblItems.currentItemId()
        if id:
            db = QtGui.qApp.db
            db.transaction()
            try:
                self.modelProperties.apply()
                actionId = self.action.save() if self.action else None
                record = db.getRecord('ActionTemplate', '*', id)
                oldActionId = forceRef(record.value('action_id'))
                record.setValue('action_id', toVariant(actionId))
                db.updateRecord('ActionTemplate', record)
                if oldActionId and oldActionId != actionId:
                    db.deleteRecord('Action', 'id=%d'%oldActionId)
                db.commit()
            except:
                db.rollback()
                QtGui.qApp.logCurrentException()
                raise


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelTree_currentChanged(self, current, previous):
        self.renewListAndSetTo(None)
        self.updateButtons()


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelTable_currentChanged(self, current, previous):
        self.updateButtons()


    @pyqtSignature('')
    def on_btnCreateGroup_clicked(self):
        name, ok = QtGui.QInputDialog.getText(self, u'Новая группа шаблонов действия', u'Наименование', QtGui.QLineEdit.Normal, '')
        name = forceStringEx(name)
        if name and ok:
            groupId = self.currentGroupId()
            db = QtGui.qApp.db
            record = db.record('ActionTemplate')
            record.setValue('group_id', toVariant(groupId))
            record.setValue('name', toVariant(name))
            showTypeTemplate = self.props.get('showTypeTemplate', 0)
            if showTypeTemplate == 1:
                record.setValue('owner_id', self.personId)
                SNILS = forceString(db.translate(db.table('Person'), 'id', self.personId, 'SNILS'))
                record.setValue('SNILS',  toVariant(SNILS))
            elif showTypeTemplate == 2:
                record.setValue('SNILS', toVariant(self.SNILS))
            id = db.insertRecord('ActionTemplate', record)
            if id:
                self.modelTree.updateItemById(groupId)
                self.renewListAndSetTo(id)
                self.updateListAndSetTo(id)


    @pyqtSignature('')
    def on_btnCreateTemplate_clicked(self):
        groupId = self.currentGroupId()
        self.modelProperties.apply()
        dlg = CActionTemplateCreateDialog(self, groupId, self.action, self.clientSex, self.clientAge, self.personId, self.specialityId)
        if dlg.exec_():
            self.modelTree.updateItemById(groupId)
            self.renewListAndSetTo(dlg.itemId())
            self.accept()


    @pyqtSignature('')
    def on_btnUpdateTemplate_clicked(self):
        currentItemId = self.tblItems.currentItemId()
        if currentItemId:
            actionTemplateIdList = QtGui.qApp.db.getDescendants('ActionTemplate', 'group_id', currentItemId, 'deleted=0')
        if actionTemplateIdList and len(actionTemplateIdList) == 1:
            self.updateTemplate()
            self.accept()
        else:
            QtGui.QMessageBox.warning( self,
                                         u'Внимание!',
                                         u'Сохранение невозможно. Выберите другой шаблон',
                                         QtGui.QMessageBox.Ok,
                                         QtGui.QMessageBox.Ok)


    @pyqtSignature('int')
    def on_cmbShowTypeFilter_currentIndexChanged(self, index):
        QtGui.qApp.callWithWaitCursor(self, self.updateListAndSetTo, None)
        QtGui.qApp.callWithWaitCursor(self, self.renewListAndSetTo, None)


class CActionTemplateTreeModel(CActionTemplateModel):
    pass


class CActionTemplateTableModel(CTableModel):
    def __init__(self, parent, filter):
        actionCol = CActionTypeCol(u'Действие',  ['action_id'], 10)
        CTableModel.__init__(self, parent, [
            CTextCol(   u'Наименование', ['name'],   40),
            CEnumCol(   u'Пол',          ['sex'], ['', u'М', u'Ж'], 10),
            CTextCol(   u'Возраст',      ['age'], 10),
            CRefBookCol(u'Врач',         ['owner_id'],      'vrbPersonWithSpeciality', 10),
            CRefBookCol(u'Специальность',['speciality_id'], 'rbSpeciality', 10),
            actionCol,
            ], 'ActionTemplate')
        self.actionCol = actionCol
        self.filter = filter
        self.enabled = []


    def setIdList(self, idList, realItemCount=None):
        CTableModel.setIdList(self, idList, realItemCount)
        self.enabled = [None]*len(idList)


    def _isEnabled(self, item):
        actionTypeId = self.actionCol.getActionTypeId(forceRef(item.value('action_id')))
        sex = forceInt(item.value('sex'))
        age = forceString(item.value('age'))
        personId = forceRef(item.value('owner_id'))
        specialityId = forceRef(item.value('speciality_id'))

        if actionTypeId and self.filter.actionTypeIdList and actionTypeId not in self.filter.actionTypeIdList:
            return False
        if self.filter.personId and personId and self.filter.personId != personId:
            return False
        if self.filter.specialityId and specialityId and self.filter.specialityId != specialityId:
            return False
        if self.filter.clientSex and sex and self.filter.clientSex != sex:
            return False
        if self.filter.clientAge and age and not checkAgeSelector(parseAgeSelector(age), self.filter.clientAge):
            return False
        return True


    def flags(self, index):
        row = index.row()
        if self.enabled[row] is None:
            self.enabled[row] = self._isEnabled(self.getRecordByRow(row))
        return (Qt.ItemIsSelectable|Qt.ItemIsEnabled) if self.enabled[row] else Qt.NoItemFlags


class CPropertiesModel(QAbstractTableModel):
    checkColumn = 0
    nameColumn  = 1
    valueColumn = 2
    def __init__(self, parent, action):
        QAbstractTableModel.__init__(self, parent)
        self._action = action

        self._propertyList = []
        self._notCopyableList = []

        for id in self._action._propertiesById:
            property = self._action.getPropertyById(id)
            if property.type().valueType.isCopyable:
                value = property.getValue()
                isAssigned = property.isAssigned()
                checked = Qt.Unchecked if ((value is None or value == u'') and not isAssigned) else Qt.Checked
                if property.type().canChangeOnlyOwner and checked:
                    record = action.getRecord()
                    if record:
                        checked = forceRef(record.value('setPerson_id')) == QtGui.qApp.userId
                self._propertyList.append([property, checked])
            else:
                self._notCopyableList.append(property)

        self._columnList = (u'Включить', u'Свойство', u'Значение')

        self.reset()


    def checkAll(self, value):
        state = Qt.Checked if value else Qt.Unchecked
        for propertyItem in self._propertyList:
            propertyItem[1] = state
        self.emitDataChanged()


    def getCheckStateInfo(self):
        existChecked = existNotChecked = False
        for propertyItem in self._propertyList:
            state = propertyItem[1]
            if not existChecked and state == Qt.Checked:
                existChecked = True
            if not existNotChecked and state == Qt.Unchecked:
                existNotChecked = True

            if existChecked and existNotChecked:
                break

        return existChecked, existNotChecked


    def columnCount(self, index=None):
        return len(self._columnList)


    def rowCount(self, index=None):
        return len(self._propertyList)


    def apply(self):
        for propertyValue in self._propertyList:
            property, checked = propertyValue
            if not checked:
                property.setValue(None)

        for property in self._notCopyableList:
            property.setValue(None)



    def getPropertyByRow(self, row):
        return self._propertyList[row][0]


    def getCheckedByRow(self, row):
        return self._propertyList[row][1]


    def setCheckedByRow(self, row, state):
        self._propertyList[row][1] = state

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()

        column = index.column()
        row    = index.row()

        if role == Qt.DisplayRole:
            if column == CPropertiesModel.nameColumn:
                property = self.getPropertyByRow(row)
                return toVariant(property.type().name)

            elif column == CPropertiesModel.valueColumn:
                return toVariant(self.getPropertyByRow(row).getText())

        elif role == Qt.CheckStateRole:
            if column == CPropertiesModel.checkColumn:
                return toVariant(self.getCheckedByRow(row))

        return QVariant()



    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.CheckStateRole:
            column = index.column()
            if column == CPropertiesModel.checkColumn:
                row = index.row()
                state = value.toInt()[0]
                self.setCheckedByRow(row, state)
                self.emitCellChanged(row, column)
                return True
        return False


    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if role in (Qt.DisplayRole, Qt.ToolTipRole, Qt.WhatsThisRole):
                return self._columnList[section]
        return QVariant()


    def flags(self, index):
        result = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        if index.column() == CPropertiesModel.checkColumn:
            result |= Qt.ItemIsUserCheckable
        return result


    def emitCellChanged(self, row, column):
        index = self.index(row, column)
        self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index, index)


    def emitDataChanged(self):
        bIndex = self.index(0, 0)
        eIndex = self.index(self.rowCount(), self.columnCount())
        self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), bIndex, eIndex)


class CActionTemplateCreateDialog(CItemEditorBaseDialog, Ui_ActionTemplateCreateDialog, CCheckNetMixin):
    def __init__(self, parent, groupId, action, clientSex, clientAge, personId, specialityId):
        CItemEditorBaseDialog.__init__(self, parent, 'ActionTemplate')
        CCheckNetMixin.__init__(self)
        self.setupUi(self)
        self.setWindowTitleEx(u'Создание шаблона действия')
        self.groupId = groupId
        self.personId = personId
        self.cmbSpeciality.setTable('rbSpeciality')
        self.cmbOrgStructure.setOrgId(QtGui.qApp.currentOrgId())
        self.cmbSex.setCurrentIndex(0)
        ageConstraint = self.getSpecialityConstraint(specialityId).age
        if not ageConstraint:
            ageConstraint = self.getPersonNet(self.personId).age
        if ageConstraint:
            (begUnit, begCount, endUnit, endCount) = ageConstraint
            self.cmbBegAgeUnit.setCurrentIndex(begUnit)
            self.edtBegAgeCount.setText(str(begCount))
            self.cmbEndAgeUnit.setCurrentIndex(endUnit)
            self.edtEndAgeCount.setText(str(endCount))
        self.cmbOwner.setValue(self.personId)
        self.cmbSpeciality.setValue(specialityId)
        self.action = action.clone()
        self.setupDirtyCather()


    def getRecord(self):
        record = CItemEditorBaseDialog.getRecord(self)
        record.setValue('group_id', toVariant(self.groupId))
#        getLineEditValue( self.edtCode, record, 'code')
        getLineEditValue( self.edtName, record, 'name')
        getComboBoxValue( self.cmbSex,  record, 'sex')
        record.setValue('age',        toVariant(composeAgeSelector(
                    self.cmbBegAgeUnit.currentIndex(),  forceStringEx(self.edtBegAgeCount.text()),
                    self.cmbEndAgeUnit.currentIndex(),  forceStringEx(self.edtEndAgeCount.text())
                        )))
        record.setValue('owner_id', self.cmbOwner.value() if self.rbVisibleToOwner.isChecked() else None)
        record.setValue('speciality_id', self.cmbSpeciality.value() if self.rbVisibleToSpeciality.isChecked() else None)
        record.setValue('orgStructure_id', self.cmbOrgStructure.value() if self.rbVisibleToOrgStructure.isChecked() else None)
        db = QtGui.qApp.db
        if self.rbVisibleToSNILS.isChecked():
            SNILS = forceString(db.translate(db.table('Person'), 'id', self.personId, 'SNILS'))
            record.setValue('SNILS',  toVariant(SNILS))
        else:
            ownerId = forceRef(record.value('owner_id'))
            if ownerId:
                SNILS = forceString(db.translate(db.table('Person'), 'id', ownerId, 'SNILS'))
                record.setValue('SNILS',  toVariant(SNILS))
        #record.setValue('SNILS',  SNILS if self.rbVisibleToSNILS.isChecked() else None)
        record.setValue('action_id', self.saveAction())
        return record


    def checkDataEntered(self):
        result = True
        result = result and (forceStringEx(self.edtName.text()) or self.checkInputMessage(u'наименование', False, self.edtName))
        result = result and (not self.rbVisibleToOwner.isChecked() or self.cmbOwner.value() or self.checkInputMessage(u'врача', False, self.cmbOwner))
        result = result and (not self.rbVisibleToSpeciality.isChecked() or self.cmbSpeciality.value() or self.checkInputMessage(u'специальность', False, self.cmbSpeciality))
        result = result and (not self.rbVisibleToOrgStructure.isChecked() or self.cmbOrgStructure.value() or self.checkInputMessage(u'подразделение', False, self.cmbOrgStructure))
        if forceString(QtGui.qApp.db.translate(QtGui.qApp.db.table('Person'), 'id', self.personId, 'SNILS')) == u'' and self.rbVisibleToSNILS.isChecked():
            res = QtGui.QMessageBox.warning( self,
                                         u'Внимание!',
                                         u'У Вас не указан СНИЛС. Выберите другой параметр для сохранения шаблона.',
                                         QtGui.QMessageBox.Ok,
                                         QtGui.QMessageBox.Ok)
            if res:
                result = False
        return result


    def saveAction(self):
        if self.action:
            return self.action.save()
        else:
            return None
