# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2021 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, SIGNAL, QEvent, QSize

from library.Utils         import forceString, toVariant, forceRef, forceBool
from library.InDocTable    import CInDocTableCol, CInDocTableView

from Events.ActionProperty import CActionPropertyValueTypeRegistry


class CActionTypeBaseDelegate(QtGui.QItemDelegate):
    def __init__(self, lineHeight, parent=None):
        QtGui.QItemDelegate.__init__(self, parent)
        self.lineHeight = lineHeight


    def eventFilter(self, editor, event):
        if event.type() == QEvent.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter) and isinstance(editor, QtGui.QTextEdit):
                return False
        return QtGui.QItemDelegate.eventFilter(self, editor, event)


    def commit(self):
        editor = self.sender()
        self.emit(SIGNAL('commitData(QWidget *)'), editor)


    def commitAndCloseEditor(self):
        editor = self.sender()
        self.emit(SIGNAL('commitData(QWidget *)'), editor)
        self.emit(SIGNAL('closeEditor(QWidget *,QAbstractItemDelegate::EndEditHint)'), editor, QtGui.QAbstractItemDelegate.NoHint)


class CActionTypeDelegate(CActionTypeBaseDelegate):
    def __init__(self, lineHeight, parent, isValueDomain=False):
        CActionTypeBaseDelegate.__init__(self, lineHeight, parent)
        self.isValueDomain = isValueDomain


    def createEditor(self, parent, option, index):
        # model = index.model()
        # row = index.row()
        editor = CInDocTableCol( u'Настройка', 'valueDomain', 25).createEditor(parent)
        # if row >= 0 and row < len(model._items):
        #     record = model._items[row]
        #     typeName = forceString(record.value('typeName'))
        #     if typeName == 'Constructor':
        #         valueType = CActionPropertyValueTypeRegistry.get(typeName, None)
        #         editorClass = valueType.getEditorClass()
        #         if editorClass:
        #             editor = editorClass(None, None, parent, None, None, self.isValueDomain) # action, domain, parent, clientId, eventTypeId, isValueDomain
        #             editor.setStatusTip(forceString(model.data(index, Qt.StatusTipRole)))
        #             self.connect(editor, SIGNAL('commit()'), self.commit)
        #             self.connect(editor, SIGNAL('editingFinished()'), self.commitAndCloseEditor)
        return editor


    def setEditorData(self, editor, index):
        model = index.model()
        row = index.row()
        value = model.data(index, Qt.EditRole)
        if row >= 0 and row < len(model._items):
            record = model._items[row]
            typeName = forceString(record.value('typeName'))
            if typeName == 'Constructor':
                editor.setText(forceString(value))  # editor.setValue(value)
            else:
                editor.setText(forceString(value))
        else:
            editor.setText(forceString(value))


    def setModelData(self, editor, model, index):
        model = index.model()
        row = index.row()
        if row >= 0 and row < len(model._items):
            record = model._items[row]
            typeName = forceString(record.value('typeName'))
            if typeName == 'Constructor':
                value = editor.text() #value = editor.value()
            else:
                value = editor.text()
        else:
            value = editor.text()
        model.setData(index, toVariant(value))


    def sizeHint(self, option, index):
        model = index.model()
        row = index.row()
        result = QSize(10, self.lineHeight)
        if row >= 0 and row < len(model._items):
            record = model._items[row]
            typeName = forceString(record.value('typeName'))
            if typeName == 'Constructor':
                propertyType = CActionPropertyValueTypeRegistry.get(typeName, None)
                preferredHeightUnit = propertyType.preferredHeightUnit
                preferredHeight = propertyType.preferredHeight * 2
                result = QSize(10, self.lineHeight*preferredHeight if preferredHeightUnit == 1 else preferredHeight)
        return result


    def updateEditorGeometry(self, editor, option, index):
        QtGui.QItemDelegate.updateEditorGeometry(self, editor, option, index)
        index.model().afterUpdateEditorGeometry(editor, index)


class CActionPropertyTypeInDocTableView(CInDocTableView):

    def __init__(self, parent):
        CInDocTableView.__init__(self, parent)
        self.enableColsMove()
        self.ciSetting = None
        self.constructorDelegate = None

    def savePreferences(self): #Не сохранять измененный порядок столбцов
        self.horizontalHeader().setMovable(False)
        return CInDocTableView.savePreferences(self)
    
    
    def setSettingDelegate(self, column): #Устанавливать делегат только для нужного экземпляра
        self.constructorDelegate = CActionTypeDelegate(self.fontMetrics().height(), self, isValueDomain=True)
        self.setItemDelegateForColumn(column, self.constructorDelegate)
        self.ciSetting = column
        

    def setSettingDelegate(self, column):  # Устанавливать делегат только для нужного экземпляра
        self.constructorDelegate = CActionTypeDelegate(self.fontMetrics().height(), self, isValueDomain=True)
        self.setItemDelegateForColumn(column, self.constructorDelegate)
        self.ciSetting = column

    def sizeHintForRow(self, row):
        model = self.model()
        if model and self.ciSetting:
            index = model.index(row, self.ciSetting)
            return self.constructorDelegate.sizeHint(None, index).height()*1+1
        return -1


    def on_popupMenu_aboutToShow(self):
        CInDocTableView.on_popupMenu_aboutToShow(self)
        if self._CInDocTableView__actDeleteRows:
            row = self.currentIndex().row()
            rows = self.getSelectedRows()
            canDeleteRow = bool(rows)
            if canDeleteRow and self._CInDocTableView__delRowsChecker:
                canDeleteRow = self._CInDocTableView__delRowsChecker(rows)
            if len(rows) == 1 and rows[0] == row:
                self._CInDocTableView__actDeleteRows.setText(u'Удалить текущую строку')
            elif len(rows) == 1:
                self._CInDocTableView__actDeleteRows.setText(u'Удалить выделенную строку')
            else:
                self._CInDocTableView__actDeleteRows.setText(u'Удалить выделенные строки')
            if canDeleteRow and self._CInDocTableView__delRowsIsExposed:
                canDeleteRow = self._CInDocTableView__delRowsIsExposed(rows)
            if canDeleteRow:
                model = self.model()
                items = model._items
                if len(items) > 0 and len(items) > row:
                    record = items[row]
                    actionPropertyTypeId = forceRef(record.value('id'))
                    actionTypeId = forceRef(record.value('actionType_id'))
                    if actionPropertyTypeId and actionTypeId:
                        canDeleteRow = actionPropertyTypeIsUsed(actionPropertyTypeId, actionTypeId)
                else:
                    canDeleteRow = False
            self._CInDocTableView__actDeleteRows.setEnabled(canDeleteRow)


def actionPropertyTypeIsUsed(actionPropertyTypeId, actionTypeId):
    if not actionPropertyTypeId or not actionTypeId:
        return True
    db = QtGui.qApp.db
    table = db.table('ActionPropertyType')
    cols = [table['typeName'],
            table['valueDomain'],
            table['template_id'],
            table['test_id']
            ]
    records = db.getRecordList(table, cols, [table['id'].eq(actionPropertyTypeId), table['actionType_id'].eq(actionTypeId), table['deleted'].eq(0)])
    tableA = db.table('Action')
    tableAT = db.table('ActionType')
    tableAP = db.table('ActionProperty')
    queryTable = table.innerJoin(tableAP, tableAP['type_id'].eq(table['id']))
    queryTable = queryTable.innerJoin(tableA, tableA['id'].eq(tableAP['action_id']))
    queryTable = queryTable.innerJoin(tableAT, tableAT['id'].eq(tableA['actionType_id']))
    cond = [tableA['deleted'].eq(0),
            tableAP['deleted'].eq(0),
            table['deleted'].eq(0),
            tableAT['deleted'].eq(0),
            table['id'].eq(actionPropertyTypeId),
            table['actionType_id'].eq(actionTypeId)
           ]
    for record in records:
        templateId = forceRef(record.value('template_id'))
        if templateId:
            tableAPTemplate = db.table('ActionPropertyTemplate')
            recordAPT = db.getRecordEx(tableAPTemplate, [tableAPTemplate['id']], [tableAPTemplate['id'].eq(templateId), tableAPTemplate['deleted'].eq(0)])
            ammount = db.getCount(table, where='template_id = {} and deleted = 0'.format(templateId))
            if recordAPT and forceBool(recordAPT.value('id')) and ammount == 1:
                return False
        queryTableProperty = queryTable
        condProperty = cond
        typeName = forceString(record.value('typeName'))
        valueDomain = forceString(record.value('valueDomain'))
        propertyType = CActionPropertyValueTypeRegistry.get(typeName, valueDomain)
        if propertyType:
            tablePropertyType = db.table(propertyType.getTableName())
            queryTableProperty = queryTableProperty.innerJoin(tablePropertyType, tablePropertyType['id'].eq(tableAP['id']))
            condProperty.append(tablePropertyType['value'].trim()+' IS NOT NULL')
            record = db.getRecordEx(queryTableProperty, [tablePropertyType['id']], condProperty)
            if record and forceBool(record.value('id')):
                return False
    return True

