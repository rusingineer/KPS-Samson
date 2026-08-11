# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2012-2025 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################
from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignature, Qt, QVariant, SIGNAL, QDate

from library.DialogBase import CDialogBase
from library.TableModel import CTableModel, CBoolCol, CDateCol, CEnumCol, CRefBookCol, CTextCol
from library.Utils import forceRef, forceInt, forceString

from Events.Action import CAction
from Events.ActionStatus import CActionStatus
from Events.ActionTypeCol import CActionTypeCol
from Events.Utils import getActionTypeDescendants

from F088.F088ActionPropertiesCheckTable import CF088ActionPropertiesCheckTableModel

from Orgs.Utils import getOrgStructurePersonIdList

from Events.Ui_PropertyEditorAmbCardDialog import Ui_PropertyEditorAmbCardDialog
from library.crbcombobox import CRBModelDataCache


class CPropertyEditorAmbCard(CDialogBase, Ui_PropertyEditorAmbCardDialog):
    def __init__(self, parent, clientId, clientSex, clientAge, eventTypeId, actionProperty):
        CDialogBase.__init__(self, parent)
        self.clientId = clientId
        self.clientSex = clientSex
        self.clientAge = clientAge
        self.eventTypeId = eventTypeId
        self.actionProperty = actionProperty

        self.addModels('Actions', CAmbCardActionsCheckTableModel(self))
        self.addModels('ActionProperties', CF088ActionPropertiesCheckTableModel(self))
        self.addObject('actPrintActions', QtGui.QAction(u'Преобразовать в текст и вставить в блок', self))
        self.setupUi(self)
        self.unitData = CRBModelDataCache.getData('rbUnit', True)
        self.setWindowTitle(self.actionProperty.type().name)
        propValue = self.actionProperty.getValue()
        if propValue:
            self.edtPropertyText.setPlainText(propValue)
        self.setModels(self.tblActions, self.modelActions, self.selectionModelActions)
        self.setModels(self.tblActionProperties, self.modelActionProperties, self.selectionModelActionProperties)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)

        self.tblActions.createPopupMenu([self.actPrintActions])
        self.tblActionProperties.setEditTriggers(QtGui.QAbstractItemView.SelectedClicked | QtGui.QAbstractItemView.DoubleClicked)
        self.tblActionProperties.model().setReadOnly(True)
        self.tblActionProperties.addPopupCopyCell()
        self.tblActionProperties.addPopupSeparator()
        self.actInsertPropertyText = QtGui.QAction(u'Преобразовать в текст и вставить в блок', self)
        self.actInsertPropertyText.setObjectName('actInsertPropertyText')
        self.connect(self.actInsertPropertyText, SIGNAL('triggered()'), self.on_actInsertPropertyText_triggered)
        self.tblActionProperties.addPopupAction(self.actInsertPropertyText)

        self.cmbSpeciality.setTable('rbSpeciality')
        self.cmbGroup.setClasses([0, 1, 2, 3])
        self.cmbGroup.setClassesVisible(True)
        self.resetFilters()
        self.loadActions()


    def loadActions(self):
        db = QtGui.qApp.db
        tableAction = db.table('Action')
        tableEvent = db.table('Event')
        tablePerson = db.table('Person')
        tableActionType = db.table('ActionType')
        queryTable = tableAction.leftJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))
        queryTable = queryTable.leftJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))

        specialityId = self.cmbSpeciality.value()
        status = self.cmbStatus.value()
        begDate = self.edtBegDate.date()
        endDate = self.edtEndDate.date()
        actionGroupId = self.cmbGroup.value()
        orgStructureId = self.cmbOrgStructure.value()
        actionTypeclass = self.cmbGroup.getClass()
        hasAttachedFiles = self.chkHasAttachedFiles.isChecked()
        hasProperties = self.chkHasProperties.isChecked()
        cond = [tableAction['deleted'].eq(0),
                tableEvent['deleted'].eq(0),
                tableEvent['client_id'].eq(self.clientId)]
        if begDate:
            cond.append(tableAction['begDate'].dateGe(begDate))
        if endDate:
            cond.append(tableAction['begDate'].dateLe(endDate))
        if specialityId:
            queryTable = queryTable.leftJoin(tablePerson, tablePerson['id'].eq(tableAction['person_id']))
            cond.append(tablePerson['speciality_id'].eq(specialityId))
        if status is not None:
            cond.append(tableAction['status'].eq(status))
        if actionGroupId:
            actionClass = forceInt(db.translate("ActionType", "id", actionGroupId, "class"))
            cond.append(tableAction['actionType_id'].inlist(getActionTypeDescendants(actionGroupId, actionClass)))
        elif actionTypeclass is not None:
            cond.append(tableActionType['class'].eq(actionTypeclass))
        if orgStructureId:
            cond.append(tableAction['person_id'].inlist(getOrgStructurePersonIdList(orgStructureId)))
        if hasAttachedFiles:
            tableAFA = db.table('Action_FileAttach')
            cond.append(db.existsStmt(tableAFA, [tableAFA['master_id'].eq(tableAction['id']),
                                                 tableAFA['deleted'].eq(0)]))
        if hasProperties:
            tableAPT = db.table('ActionPropertyType')
            cond.append(db.existsStmt(tableAPT, [tableAPT['actionType_id'].eq(tableActionType['id']),
                                                 tableAPT['deleted'].eq(0)]))
        order = ['Action.endDate DESC', 'Action.begDate DESC', 'Action.id']
        try:
            QtGui.QApplication.setOverrideCursor(QtGui.QCursor(Qt.WaitCursor))
            idList = db.getIdList(queryTable, tableAction['id'].name(), cond, order)
            self.tblActions.setIdList(idList)
        finally:
            QtGui.QApplication.restoreOverrideCursor()


    @pyqtSignature('')
    def on_actPrintActions_triggered(self):
        selectedIdList = self.modelActions.getSelectedIdList()
        actionDictValues = self.getSelectedActionProperties(selectedIdList)
        if actionDictValues:
            oldValue = self.edtPropertyText.toPlainText()
            oldValue = oldValue.replace('\0', '')
            newValue = u'\n'.join((val[0] + val[1]) for val in actionDictValues if val)
            newValue = newValue.replace('\0', '')
            value = (oldValue + u'\n' + newValue) if oldValue else newValue
            self.edtPropertyText.setText(value)
            self.modelActionProperties.reset()
            self.modelActions.enableIdList = []


    @pyqtSignature('')
    def on_actInsertPropertyText_triggered(self):
        currentActionId = self.modelActionProperties.getCurrentActionId()
        selectedIdList = [currentActionId]
        actionDictValues = self.getSelectedActionProperties(selectedIdList)
        if actionDictValues:
            oldValue = self.edtPropertyText.toPlainText()
            oldValue = oldValue.replace('\0', '')
            newValue = u'\n'.join((val[1]) for val in actionDictValues if val)
            newValue = newValue.replace('\0', '')
            value = (oldValue + u'\n' + newValue) if oldValue else newValue
            self.edtPropertyText.setText(value)
            self.modelActionProperties.reset()
            if currentActionId in self.modelActions.enableIdList:
                self.modelActions.enableIdList.remove(currentActionId)


    def getSelectedActionProperties(self, selectedIdList):
        actionDict = {}
        db = QtGui.qApp.db
        table = db.table('Action')
        for actionId in selectedIdList:
            record = db.getRecordEx(table, '*', [table['id'].eq(actionId), table['deleted'].eq(0)])
            if record:
                action = CAction(record=record)
                if action:
                    endDate = action.getEndDate()
                    actionType = action.getType()
                    actionLine = [u'', u'']
                    valuePropertyList = []
                    actionLine[0] = unicode(endDate.toString('dd.MM.yyyy')) + u' ' + actionType.name + u': '
                    propertiesById = action.getPropertiesById()
                    properties = propertiesById.values()
                    properties.sort(key=lambda prop: prop.type().idx)

                    actionsPropertiesRegistry = self.modelActions.actionsPropertiesRegistry.get(actionId, None)
                    selectedProperties = actionsPropertiesRegistry.getItems() if actionsPropertiesRegistry else []
                    if selectedProperties:
                        actionsPropertiesRegistry.setItems([])
                    includeItems = self.modelActions.includeItems.get(actionId, {})
                    for key in includeItems.keys():
                        includeItems[key] = False

                    for prop in properties:
                        propType = prop.type()
                        propertyId = prop.getId()
                        if propertyId in selectedProperties or not selectedProperties:
                            if prop.getValue() and not propType.isJobTicketValueType():
                                propName = forceString(propType.name)
                                propValue = forceString(prop.getText()) if not propType.isBoolean() else (u'Да' if prop.getValue() else u'Нет')
                                propUnit = forceString(self.unitData.getNameById(prop.getUnitId())) if prop.getUnitId() else ''
                                valuePropertyList.append(u' '.join([propName, '-', propValue, propUnit]))
                    actionLine[1] = u'; '.join(val for val in valuePropertyList if val)
                    actionDict[actionId] = actionLine

        actionDictValues = actionDict.values()
        actionDictValues.sort(key=lambda x: x[0])
        return actionDictValues


    @pyqtSignature('')
    def on_tblActions_popupMenuAboutToShow(self):
        notEmpty = self.modelActions.rowCount() > 0
        self.actPrintActions.setEnabled(notEmpty)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelActions_currentRowChanged(self, current, previous):
        self.updateAmbCardPropertiesTable(current, self.tblActionProperties, previous)


    def updateAmbCardPropertiesTable(self, index, tbl, previous=None):
        if previous:
            tbl.savePreferencesLoc(previous.row())
        row = index.row()
        record = index.model().getRecordByRow(row) if row >= 0 else None
        if record:
            clientId = self.clientId
            clientSex = self.clientSex
            clientAge = self.clientAge
            action = CAction(record=record)
            tbl.model().setAction2(action, clientId, clientSex, clientAge, eventTypeId=self.eventTypeId)
            self.setActionPropertiesColumnVisible(action.actionType(), tbl)
            currentActionId = self.modelActionProperties.getCurrentActionId()
            if currentActionId:
                self.modelActionProperties.includeRows = self.modelActions.includeItems.get(currentActionId, {})
            tbl.resizeColumnsToContents()
            tbl.resizeRowsToContents()
            tbl.horizontalHeader().setStretchLastSection(True)
            tbl.loadPreferencesLoc(tbl.preferencesLocal, row)
        else:
            tbl.model().setAction2(None, None)

    def setActionPropertiesColumnVisible(self, actionType, propertiesView):
        propertiesView.setColumnHidden(1, not actionType.propertyAssignedVisible)
        propertiesView.setColumnHidden(3, not actionType.propertyUnitVisible)
        propertiesView.setColumnHidden(4, not actionType.propertyNormVisible)
        propertiesView.setColumnHidden(5, not actionType.propertyEvaluationVisible)


    @pyqtSignature('QAbstractButton*')
    def on_btnFiltersButtonBox_clicked(self, button):
        buttonCode = self.btnFiltersButtonBox.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.loadActions()
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.resetFilters()
            self.loadActions()


    @pyqtSignature('QAbstractButton*')
    def on_buttonBox_clicked(self, button):
        buttonCode = self.buttonBox.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Ok:
            self.actionProperty.setValue(self.edtPropertyText.toPlainText())
        elif buttonCode == QtGui.QDialogButtonBox.Cancel:
            self.close()


    def resetFilters(self):
        self.cmbSpeciality.setValue(None)
        self.cmbStatus.setValue(2)
        self.cmbGroup.setValue(None)
        self.cmbOrgStructure.setValue(None)
        self.edtBegDate.setDate(QDate.currentDate().addDays(-30))
        self.edtEndDate.setDate(None)
        self.chkHasAttachedFiles.setChecked(False)
        self.chkHasProperties.setChecked(False)


    def destroy(self):
        pass

    @pyqtSignature('QModelIndex, QModelIndex')
    def on_modelActionProperties_dataChanged(self, topLeft, bottomRight):
        indexAction = self.tblActions.currentIndex()
        if indexAction.isValid():
            rowAction = indexAction.row()
            if rowAction >= 0 and rowAction < len(self.modelActions.idList()):
                indexProperty = topLeft
                if indexProperty.isValid():
                    columnProperty = indexProperty.column()
                    if columnProperty == 0:
                        rowProperty = indexProperty.row()
                        if 0 <= rowProperty < len(self.modelActionProperties.propertyTypeList):
                            isChecked = self.modelActionProperties.includeRows[rowProperty]
                            actionId = self.modelActions._idList[rowAction]
                            actionsPropertiesRegistry = self.modelActions.actionsPropertiesRegistry.get(actionId, None)
                            if not actionsPropertiesRegistry:
                                actionsPropertiesRegistry = CActionsPropertiesRegistry()
                            property = self.modelActionProperties.getProperty(rowProperty)
                            if property:
                                record = property.getRecord()
                                if record:
                                    propertyId = forceRef(record.value('id'))
                                    if propertyId:
                                        if bool(isChecked):
                                            actionsPropertiesRegistry.addItem(propertyId)
                                            if actionId not in self.modelActions.enableIdList:
                                                self.modelActions.enableIdList.append(actionId)
                                        else:
                                            actionsPropertiesRegistry.removeItem(propertyId)
                                        self.modelActions.includeItems[actionId] = self.modelActionProperties.includeRows
                                        self.modelActions.actionsPropertiesRegistry[actionId] = actionsPropertiesRegistry
                                        if actionsPropertiesRegistry and len(actionsPropertiesRegistry.getItems()) > 0:
                                            self.modelActions.setData(indexAction, QVariant(Qt.Checked), role=Qt.CheckStateRole)
                                        else:
                                            self.modelActions.setData(indexAction, QVariant(Qt.Unchecked), role=Qt.CheckStateRole)


class CAmbCardActionsCheckTableModel(CTableModel):
    class CEnableCol(CBoolCol):
        def __init__(self, title, fields, defaultWidth, selector):
            CBoolCol.__init__(self, title, fields, defaultWidth)
            self.selector = selector

        def checked(self, values):
            _id = forceRef(values[0])
            if self.selector.isSelected(_id):
                return CBoolCol.valChecked
            else:
                return CBoolCol.valUnchecked


    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self.enableIdList = []
        self.actionsPropertiesRegistry = {}
        self.includeItems = {}
        self.addColumn(CAmbCardActionsCheckTableModel.CEnableCol(u'Выбрать', ['id'], 5, self))
        self.addColumn(CDateCol(u'Назначено', ['directionDate'], 15))
        self.addColumn(CActionTypeCol(u'Тип', 15))
        self.addColumn(CEnumCol(u'Состояние', ['status'], CActionStatus.names, 4))
        self.addColumn(CDateCol(u'Начато', ['begDate'], 15))
        self.addColumn(CDateCol(u'Окончено', ['endDate'], 15))
        self.addColumn(CRefBookCol(u'Назначил', ['setPerson_id'], 'vrbPersonWithSpeciality', 20))
        self.addColumn(CRefBookCol(u'Выполнил', ['person_id'], 'vrbPersonWithSpeciality', 20))
        self.addColumn(CTextCol(u'Примечания', ['note'], 6))
        self.setTable('Action')
        self._mapColumnToOrder = {u'directionDate': u'Action.directionDate',
                                  u'actionType_id': u'ActionType.name',
                                  u'status': u'Action.status',
                                  u'begDate': u'Action.begDate',
                                  u'endDate': u'Action.endDate',
                                  u'setPerson_id': u'vrbPersonWithSpeciality.name',
                                  u'person_id': u'vrbPersonWithSpeciality.name',
                                  u'note': u'Action.note'}
        self.basicAdditionalDict = {}
        self.eventId = None
        self.eventIdDict = {}
        self._idList = []

    def sort(self, col, sortOrder=Qt.AscendingOrder):
        if self._idList:
            db = QtGui.qApp.db
            table = db.table('Action')
            cond = [table['id'].inlist(self._idList)]
            colClass = self.cols()[col]
            colName = colClass.fields()[0]
            if col in [2, 9, 10]:
                tableSort = db.table('ActionType' if col == 2 else colClass.tableName).alias('fieldSort')
                table = table.leftJoin(tableSort, tableSort['id'].eq(table[colName]))
                colName = 'fieldSort.name'
            order = '{} {}'.format(colName, u'DESC' if sortOrder else u'ASC')
            self._idList = db.getIdList(table, table['id'].name(), where=cond, order=order)
            self.reset()

    def setEventId(self, eventId):
        self.eventId = eventId

    def setEventIdDict(self, eventIdDict):
        self.eventIdDict = eventIdDict

    def getOrder(self, fieldName, column):
        if hasattr(self._cols[column], 'extraFields'):
            if len(self._cols[column].extraFields) > 0:
                fieldName = self._cols[column].extraFields[0]
        return self._mapColumnToOrder[fieldName]

    def flags(self, index):
        result = CTableModel.flags(self, index)
        if index.column() == 0:
            result |= Qt.ItemIsUserCheckable
        return result

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        column = index.column()
        row = index.row()
        if role == Qt.DisplayRole:
            (col, values) = self.getRecordValues(column, row)
            return col.format(values)
        elif role == Qt.TextAlignmentRole:
            col = self._cols[column]
            return col.alignment()
        elif role == Qt.CheckStateRole:
            (col, values) = self.getRecordValues(column, row)
            return col.checked(values)
        elif role == Qt.ForegroundRole:
            (col, values) = self.getRecordValues(column, row)
            return col.getForegroundColor(values)
        elif role == Qt.BackgroundRole:
            (col, values) = self.getRecordValues(column, row)
            return col.getBackgroundColor(values)
        elif role == Qt.FontRole:
            if 0 <= row < len(self._idList):
                actionId = forceRef(self._idList[row])
                if self.eventId == self.eventIdDict.get(actionId, None):
                    result = QtGui.QFont()
                    result.setBold(True)
                    return QVariant(result)
        return QVariant()

    def setData(self, index, value, role=Qt.EditRole):
        row = index.row()
        column = index.column()
        if role == Qt.CheckStateRole and column == 0:
            _id = self._idList[row]
            if _id:
                self.setSelected(_id, forceInt(value) == Qt.Checked)
                self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index, index)
            return True
        return CTableModel.setData(self, index, value, role)

    def setSelected(self, _id, value):
        present = self.isSelected(_id)
        if value:
            if not present:
                self.enableIdList.append(_id)
        else:
            if present:
                self.enableIdList.remove(_id)

    def isSelected(self, _id):
        return _id in self.enableIdList

    def getSelectedIdList(self):
        return self.enableIdList


class CActionsPropertiesRegistry:
    def __init__(self):
        self.items = []

    def getItems(self):
        return self.items


    def setItems(self, items):
        self.items = items


    def addItem(self, item):
        if item and item not in self.items:
            self.items.append(item)


    def addItems(self, items):
        self.items.extend(items)


    def removeItem(self, item):
        if item and item in self.items:
            items = self.items
            self.items = list(set(items)-set([item]))
