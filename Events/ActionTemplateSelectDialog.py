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
from PyQt4.QtCore import Qt, QAbstractTableModel, QVariant, pyqtSignature, SIGNAL

from library.Utils                 import forceRef, toVariant, formatNum1, forceInt, forceBool
from library.DialogBase            import CDialogBase
from library.StrComboBox         import CStrComboBox
#from library.AgeSelector           import checkAgeSelector, parseAgeSelector
from Events.Action                 import CAction
from Events.ActionTemplateSaveDialog import CActionTemplateTreeModel
from RefBooks.ActionTemplate.List   import CActionTemplateEditor
from Users.Rights import urAccessRefDeletedActionTemplate, urAccessRefUpdateOwnerActionTemplate

from Events.Ui_ActionTemplateSelectDialog   import Ui_ActionTemplateSelectDialog


class CActionTemplateSelectDialog(CDialogBase, Ui_ActionTemplateSelectDialog):
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
                 showTypeTemplate,
                 model=None
                ):
        CDialogBase.__init__(self, parent)
        actionTypeId = action.getType().id
        modelEx = model if model else CActionTemplateTreeModel(self, actionTypeId, personId, orgStructureId, specialityId, SNILS, clientSex, clientAge, removeEmptyNodes=True, showTypeTemplate=showTypeTemplate, typeDialog=1)
        self.action = action.clone()
        self.addModels('Tree', modelEx)
#        self.addModels('Tree',  CActionTemplateTreeModel(self, actionTypeId, personId, orgStructureId, specialityId, SNILS, clientSex, clientAge, removeEmptyNodes=True, showTypeTemplate=showTypeTemplate, typeDialog=1))
        self.modelTree.setRootItemVisible(True)
        self.addModels('Properties', CPropertiesTableModel(self))
        self.addObject('actDelete', QtGui.QAction(u'Удалить', self))
        self.addObject('actEdit', QtGui.QAction(u'Редактировать', self))
        self.setupUi(self)
        self.setWindowTitleEx(u'Загрузка шаблона действия')
        self.treeItems.header().hide()
        self.setModels(self.treeItems, self.modelTree,  self.selectionModelTree)
        self.setModels(self.tblProperties, self.modelProperties, self.selectionModelProperties)
        self.treeItems.createPopupMenu([self.actDelete, self.actEdit])
        self.connect(self.treeItems.popupMenu(), SIGNAL('aboutToShow()'), self.popupMenuAboutToShow)
        self.actionTypeId = actionTypeId
        self.orgStructureId = orgStructureId
        self.clientSex = clientSex
        self.clientAge = clientAge
        self.personId = personId
        self.SNILS = SNILS
        self.specialityId = specialityId
        pref = QtGui.qApp.preferences
        props = pref.appPrefs
        self.expand = forceInt(props.get('actionTemplateTreeExpand',  QVariant()))
        self.expandLevel = forceInt(props.get('actionTemplateTreeExpandLevel',  QVariant(1)))
        self.actionTemplatePriorityLoad = forceBool(props.get('actionTemplatePriorityLoad', True))
        self.showTypeTemplate = showTypeTemplate if not model else model.getShowTypeTemplate()
        self.showTypeTemplateFirst = True
        self.cmbShowTypeFilter.setCurrentIndex(self.showTypeTemplate) if self.showTypeTemplate else self.on_cmbShowTypeFilter_currentIndexChanged(0)
        self.chkFillProperties.setChecked(self.actionTemplatePriorityLoad)
        self.chkAddProperties.setChecked(not self.actionTemplatePriorityLoad)
        self.addObject('actSelectAllProperies', QtGui.QAction(u'Выделить все', self))
        self.addObject('actDeselectAllProperies', QtGui.QAction(u'Отменить выделения', self))
        self.tblProperties.addPopupActions([self.actSelectAllProperies, self.actDeselectAllProperies])
        self.connect(self.actSelectAllProperies, SIGNAL('triggered()'), self.on_actSelectAllProperies)
        self.connect(self.actDeselectAllProperies, SIGNAL('triggered()'), self.on_actDeselectAllProperies)
        self.connect(self.tblProperties.popupMenu(), SIGNAL('aboutToShow()'), self.on_properiesAboutToShow)
        self.saveProps()


    def popupMenuAboutToShow(self):
        actionEnabled = False
        app = QtGui.qApp
        currentUserId = app.userId
        if currentUserId:
            currentItemId = self.getCurrentItemId()
            if currentItemId:
                isAdmin = app.isAdmin()
                db = QtGui.qApp.db
                table = db.table('ActionTemplate')
                record = db.getRecordEx(table, [table['createPerson_id'], table['owner_id']],
                                        [table['id'].eq(currentItemId), table['deleted'].eq(0)])
                createPersonId = forceRef(record.value('createPerson_id')) if record else None
                ownerId = forceRef(record.value('owner_id')) if record else None
                actionEnabled = bool(currentItemId) and (isAdmin or (app.userHasAnyRight(
                    [urAccessRefDeletedActionTemplate]) and createPersonId == currentUserId) or (app.userHasAnyRight(
                    [urAccessRefUpdateOwnerActionTemplate]) and ownerId == currentUserId))
        self.actDelete.setEnabled(actionEnabled)
        self.actEdit.setEnabled(actionEnabled)


    @pyqtSignature('')
    def on_actDelete_triggered(self):
        def deleteCurrentInternal():
            currentItemId = self.getCurrentItemId()
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
                    self.modelTree.reset()
                    self.renewListAndSetTo()
        QtGui.qApp.call(self, deleteCurrentInternal)


    def getItemEditor(self):
        return CActionTemplateEditor(self)


    @pyqtSignature('')
    def on_actEdit_triggered(self):
        itemId = self.getCurrentItemId()
        if itemId:
            QtGui.qApp.setWaitCursor()
            dialog = self.getItemEditor()
            try:
                dialog.load(itemId)
                QtGui.qApp.restoreOverrideCursor()
                if dialog.exec_():
                    itemId = dialog.itemId()
                    self.modelTree.reset()
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
                self.modelTree.reset()
                self.renewListAndSetTo(itemId)
        finally:
            dialog.deleteLater()


    @pyqtSignature('bool')
    def on_chkFillProperties_toggled(self, checked):
        self.chkAddProperties.setChecked(not checked)


    @pyqtSignature('bool')
    def on_chkAddProperties_toggled(self, checked):
        self.chkFillProperties.setChecked(not checked)


    def getMethodRecording(self):
        if self.chkFillProperties.isChecked():
            return CAction.actionFillProperties
        if self.chkAddProperties.isChecked():
            return CAction.actionAddProperties


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


    def renewListAndSetTo(self, itemId=None):
        if not itemId:
            itemId = self.getCurrentItemId()
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
        self.resetProperties()


    def getSelectAction(self):
        self.modelProperties.apply()
        return self.action


    def getCurrentActionId(self):
        return self.modelTree.getItemById(self.modelTree.itemId(self.treeItems.currentIndex()))._actionId


    def getCurrentItemId(self):
        return self.modelTree.itemId(self.treeItems.currentIndex())


    @pyqtSignature('QModelIndex')
    def on_treeItems_doubleClicked(self, index):
        self.accept()


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelTree_currentChanged(self, current, previous):
        self.resetProperties()


    def resetProperties(self):
        self.action = None
        actionId = self.getCurrentActionId()
        if actionId:
            self.action = CAction.getActionById(actionId)
        self.modelProperties.setActionProperties(self.action)


    @pyqtSignature('int')
    def on_cmbShowTypeFilter_currentIndexChanged(self, index):
        if self.showTypeTemplateFirst:
            if not self.expand:
                self.treeItems.expandToDepth(0)
            elif self.expand == 1:
                self.treeItems.expandAll()
            else:
                self.treeItems.expandToDepth(self.expandLevel)
        else:
            QtGui.qApp.callWithWaitCursor(self, self.renewListAndSetTo, None)
        self.showTypeTemplateFirst = False


class CPropertiesTableModel(QAbstractTableModel):
    checkColumn = 0
    nameColumn  = 1
    valueColumn = 2
    def __init__(self, parent):
        QAbstractTableModel.__init__(self, parent)
        self._action = None
        self._propertyList = []
        self._notCopyableList = []
        self._columnList = (u'Включить', u'Свойство', u'Значение')


    def setActionProperties(self, action):
        """
        Загрузка свойств Действия из шаблона
        Заполнение списков _propertyList, _notCopyableList на основе данных из свойств действия
        :param action: Действие, для которого загружаются свойства
        :type action: CAction
        """
        def normalizeString(string):
             return string.strip().lower().replace(u'ё', u'е') if string else string
        self._action = action
        self._propertyList = []
        self._notCopyableList = []
        if self._action:
            for id in self._action._propertiesById:
                propertyApplicable = True
                property = self._action.getPropertyById(id)
                if property.type().valueType.isCopyable:
                    value = property.getValue()
                    if property.type().typeName == 'String':
                        applicableValues, regexps, err, methods = CStrComboBox.parse(property.type().valueDomain)
                        if not err and applicableValues:
                            tmpValue = normalizeString(value)
                            for i, val in enumerate(applicableValues):
                                chkVal = normalizeString(val)
                                if chkVal == tmpValue:
                                    property.setValue(val)
                                applicableValues[i] = chkVal
                            if tmpValue not in applicableValues:
                                value = u''
                                propertyApplicable = False
                    checked = Qt.Unchecked if (value is None or value == u'') else Qt.Checked
                    #if property.type().canChangeOnlyOwner and checked:
                    #    record = action.getRecord()
                    #    if record:
                    #        checked = forceRef(record.value('setPerson_id')) == QtGui.qApp.userId
                    self._propertyList.append([property, checked, propertyApplicable])
                else:
                    self._notCopyableList.append(property)
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
            property, checked, applicable = propertyValue
            if not checked:
                property.setValue(None)
                self._action.__delitem__(property.type().name)
        for property in self._notCopyableList:
            property.setValue(None)
            self._action.__delitem__(property.type().name)


    def getPropertyByRow(self, row):
        return self._propertyList[row][0]


    def getCheckedByRow(self, row):
        return self._propertyList[row][1]
    
    
    def getApplicableByRow(self, row):
        return self._propertyList[row][2]


    def setCheckedByRow(self, row, state):
        self._propertyList[row][1] = state


    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        column = index.column()
        row    = index.row()
        if role == Qt.DisplayRole:
            if column == CPropertiesTableModel.nameColumn:
                property = self.getPropertyByRow(row)
                return toVariant(property.type().name)
            elif column == CPropertiesTableModel.valueColumn:
                return toVariant(self.getPropertyByRow(row).getText())
        elif role == Qt.CheckStateRole:
            if column == CPropertiesTableModel.checkColumn:
                return toVariant(self.getCheckedByRow(row))
        elif role == Qt.FontRole:
            if column == CPropertiesTableModel.valueColumn:
                applicable = self.getApplicableByRow(row)
                if not applicable:
                    font = QtGui.QFont()
                    font.setStrikeOut(True)
                    return font
        return QVariant()


    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.CheckStateRole:
            column = index.column()
            if column == CPropertiesTableModel.checkColumn:
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
        if index.column() == CPropertiesTableModel.checkColumn:
            result |= Qt.ItemIsUserCheckable
        return result


    def emitCellChanged(self, row, column):
        index = self.index(row, column)
        self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index, index)


    def emitDataChanged(self):
        bIndex = self.index(0, 0)
        eIndex = self.index(self.rowCount(), self.columnCount())
        self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), bIndex, eIndex)

