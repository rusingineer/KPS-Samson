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
## Модуль редактора шаблонов назначения действий
#############################################################################

from PyQt4 import QtGui, QtSql
from PyQt4.QtCore import pyqtSignature, QModelIndex, Qt, QVariant
from PyQt4.QtGui import QKeySequence, QDoubleSpinBox
from RefBooks.ActionTypeGroup.RBActionTypeSelectorDialog import CActionTypeSelector
from RefBooks.ActionTypeGroup.Ui_RBActionTypeGroupEditor import Ui_ActionTypeGroupEditorDialog
from library.Utils import forceBool, forceStringEx, toVariant, forceRef, forceInt, forceString
from library.ItemsListDialog import CItemEditorBaseDialog
from library.interchange import getComboBoxValue
from library.database import CTable, CSurrogateField
from library.crbcombobox import CRBComboBox
from library.ESKLP.SmnnComboBoxEx import CSmnnComboBoxEx
from library.ESKLP.SmnnGrlsLfComboBoxEx import CSmnnGrlsLfComboBoxEx
#from RefBooks.ActionTypeGroup.crbclassesMy import CRBModelDataCacheMod
from Events.Action import CActionTypeCache
from Events.ActionTemplateChoose import CActionTemplateComboBox
from RefBooks.NomenclatureActiveSubstance.ActiveSubstanceComboBox import CActiveSubstanceComboBox
from Stock.NomenclatureComboBox import CNomenclatureComboBox
#from Stock.NomenclatureComboBox import CNomenclatureInDocTableCol
from library.InDocTable import CRecordListModel, CInDocTableCol, CRBInDocTableCol, CIntInDocTableCol

_RECIPE = 1
_DOSES  = 2
_SIGNA  = 3
_ACTIVESUBSTANCE = 4


class CActionTypesList(CRecordListModel):
    """
    Модель данных для таблицы действий в редакторе
    Связанная таблица SQL должна иметь поле master_id
    """
    
    class CActionTemplateInDocTableCol(CInDocTableCol):
        def __init__(self, model):
            CInDocTableCol.__init__(self, u'Шаблон действия', 'actionTemplate_id', 20)
            self.model = model


        def toString(self, val, record):
            actionTemplateId = forceRef(val)
            if actionTemplateId:
                record = QtGui.qApp.db.getRecord('ActionTemplate', 'name', actionTemplateId)
                str = forceString(record.value('name'))
            else:
                str = u'не задано'
            return QVariant(str)


        def createEditor(self, parent):
            eventEditor = self.model.parentWidget.eventEditor
            editor = CActionTemplateComboBox(parent)
            return editor

        def getEditorData(self, editor):
            return QVariant(editor.value())


        def setEditorData(self, editor, value, record):
            eventEditor = self.model.parentWidget.eventEditor
            actionTypeId = forceRef(record.value('actionType_id'))
            editor.setFilter(actionTypeId, None, None, None, eventEditor.clientSex, eventEditor.clientAge)
            editor.setValue(forceRef(value))
            
            
    def __init__(self, tableName, idFieldName, masterIdFieldName, parent):
        super(CActionTypesList, self).__init__(parent)
        db = QtGui.qApp.db
        self._table = db.table(tableName)
        self._idFieldName = idFieldName
        self._masterIdFieldName = masterIdFieldName
        self._idxFieldName = ''
        self._tableFields = None
        self._extColsPresent = False
        self._filter = None
        self._propertyColsNames = []
        self._propertyColsIndexes = []
        self._mapActionPropertiesToActionTypeId = {}
        self._offsetEnabled = True
        self.dataChanged.connect(self.updateNomenclatureCol)

    def setOffsetEnabled(self, enable=True):
        self._offsetEnabled = forceBool(enable)
        if not self._offsetEnabled:
            for item in self.items():
                item.setValue('offset', QVariant(0))
        self.reset()

    def updateNomenclatureCol(self, index1, index2):
        """
        Обновление колонки с номенклатурой требует дополнительных действий, т.к. необходимо синхронно обновлять поля
        Doses и Signa. Обновление происходит только если текущий тип действия имеет свойство Nomenclature и было
        реальное изменение данных в поле Номенклатуры.
        """
        if index1 == index2:
            index = index1
            model = index.model()
            col = index.column()
            row = index.row()
            colNomenclatureIndex = model.getColIndex('nomenclature_id')
            colNomenclature = model.cols()[colNomenclatureIndex]
            if col == colNomenclatureIndex:
                record = model.getRecordByRow(row)
                actionTypeId = forceRef(record.value('actionType_id'))
                if colNomenclature.isRecordHaveProp(actionTypeId):
                    nomenclatureId = model.value(row, 'nomenclature_id')
                    prevNomenclatureId = colNomenclature.getNomenclatureIdBeforeEdit()
                    if nomenclatureId != prevNomenclatureId:
                        self.dataChanged.disconnect(self.updateNomenclatureCol)
                        # Сброс поля номенклатуры
                        if (nomenclatureId == None):
                            newindex = model.createIndex(row, model.getColIndex('doses'))
                            model.setData(newindex, None)
                            newindex = model.createIndex(row, model.getColIndex('signa'))
                            model.setData(newindex, None)
                        # Изменение поля номенклатуры
                        else:
                            db = QtGui.qApp.db
                            tableNomenclature = CTable('rbNomenclature', db)
                            rec = db.getRecord(tableNomenclature, 'dosageValue', nomenclatureId).value('dosageValue')
                            value = rec.toFloat()
                            dosageVal = None
                            if value[1] and value[0] != 0:
                                dosageVal = value[0]
                            newindex = model.createIndex(row, model.getColIndex('doses'))
                            model.setData(newindex, dosageVal)
                            newindex = model.createIndex(row, model.getColIndex('signa'))
                            model.setData(newindex, None)
                        self.dataChanged.connect(self.updateNomenclatureCol)

    def getTableFieldList(self):
        """Возвращает список колонок в модели"""
        if self._tableFields is None:
            fields = []
            for col in self._cols:
                if col.external():
                    field = CSurrogateField(col.fieldName(), col.valueType())
                else:
                    field = self._table[col.fieldName()]

                fields.append(field)

            fields.append(self._table[self._idFieldName])
            fields.append(self._table[self._masterIdFieldName])
            if self._idxFieldName:
                fields.append(self._table[self._idxFieldName])
            for col in self._hiddenCols:
                field = self._table[col]
                fields.append(field)

            self._tableFields = fields
        return self._tableFields

    def loadItems(self, masterId):
        """Загрузка данных из БД в модель"""
        db = QtGui.qApp.db
        cols = []
        for col in self._cols:
            if not col.external():
                if col.fieldName() not in cols:
                    cols.append(col.fieldName())
        cols.append(self._idFieldName)
        cols.append(self._masterIdFieldName)
        if self._idxFieldName:
            cols.append(self._idxFieldName)
        for col in self._hiddenCols:
            cols.append(col)
        table = self._table
        filter = [table[self._masterIdFieldName].eq(masterId)]
        if self._filter:
            filter.append(self._filter)
        if table.hasField('deleted'):
            filter.append(table['deleted'].eq(0))
        if self._idxFieldName:
            order = [self._idxFieldName, self._idFieldName]
        else:
            order = [self._idFieldName]
        self._items = db.getRecordList(table, cols, filter, order)
        if self._extColsPresent:
            extSqlFields = []
            for col in self._cols:
                if col.external():
                    fieldName = col.fieldName()
                    if fieldName not in cols:
                        extSqlFields.append(QtSql.QSqlField(fieldName, col.valueType()))
            if extSqlFields:
                for item in self._items:
                    for field in extSqlFields:
                        item.append(field)
        self.reset()

    def itemIdList(self):
        #idList = []
        pass

    def saveItems(self, masterId):
        """
        Сохранение данных модели в БД

        :param masterId: ID элемента в мастер-таблице
        :type masterId: Int
        """
        if self._items is not None:
            db = QtGui.qApp.db
            table = self._table
            masterIdFieldName = self._masterIdFieldName
            idFieldName = self._idFieldName
            idList = []
            for idx, record in enumerate(self._items):
                record.setValue(masterIdFieldName, masterId)
                if self._idxFieldName:
                    record.setValue(self._idxFieldName, toVariant(idx))
                if self._extColsPresent:
                    outRecord = self.removeExtCols(record)
                else:
                    outRecord = record
                id = db.insertOrUpdate(table, outRecord)
                record.setValue(idFieldName, toVariant(id))
                idList.append(id)

            filter = [table[masterIdFieldName].eq(masterId),
                      'NOT (' + table[idFieldName].inlist(idList) + ')']
            if self._filter:
                filter.append(self._filter)
            db.deleteRecord(table, filter)

    def removeExtCols(self, srcRecord):
        record = self._table.newRecord()
        for i in xrange(record.count()):
            record.setValue(i, srcRecord.value(record.fieldName(i)))
        return record

    def getEmptyRecord(self):
        """
        Генерирует пустую запись QSql с полями, соответствующими модели
        :return: Пустая запись QSql с полями, соответствующими модели
        :rtype: QSqlRecord
        """
        record = QtSql.QSqlRecord()
        fields = self.getTableFieldList()
        fieldNames = []
        for field in fields:
            name = field.name()
            if name not in fieldNames:
                fieldNames.append(name)
                record.append(QtSql.QSqlField(field.field))
        record.append(QtSql.QSqlField('ATItemClass', QVariant.Int)) # Здесь хранится класс типа действия при добавлении действий в шаблон
        record.append(QtSql.QSqlField('ExtItemIndex', QVariant.Int)) # Индекс записи, присваивается вне класса. Нужен для маппинга записей извне.
        return record

    def flags(self, index):
        col = index.column()
        offsetColIndex = self.getColIndex('offset')
        if col == offsetColIndex:
            if not self._offsetEnabled:
                return Qt.NoItemFlags
            else:
                return super(CActionTypesList, self).flags(index)
        else:
            return super(CActionTypesList, self).flags(index)


class CLocPropertyCol(CRBInDocTableCol):
    """
    Базовый класс для колонок свойств (Nomenclature, ActiveSubstance, Doses, Signa)
    Не должен использоватся напрямую для создания объектов, только для наследования
    """
    def __init__(self, title, fieldName, width, tableName, **params):
        super(CLocPropertyCol, self).__init__(title, fieldName, width, tableName, **params)
        self._propPresentCache = {}

    def toString(self, val, record):
        actionTypeId = forceRef(record.value('actionType_id'))
        if self.isRecordHaveProp(actionTypeId):
            return super(CLocPropertyCol, self).toString(val, record)
        else:
            return val

    def createEditor(self, parent):
        currentIndex = parent.parentWidget().currentIndex()
        model = currentIndex.model()
        row = currentIndex.row()
        record = model.getRecordByRow(row)
        actionTypeId = forceRef(record.value('actionType_id'))
        if self.isRecordHaveProp(actionTypeId):
            editor = self.setEditor(parent, row)
            return editor
        else:
            return None

    def isRecordHaveProp(self, actionTypeId):
        val = self._propPresentCache.get(actionTypeId, None)
        if val is not None:
            return val
        else:
            val = False
            actionType = CActionTypeCache.getById(actionTypeId)
            propList = actionType.getPropertiesById().values()
            for prop in propList:
                if prop.inActionsSelectionTable == self.inActionsSelectionTableVal:
                    val = True
            self._propPresentCache[actionTypeId] = val
            return val

    def resetPropPresentCache(self):
        self._propPresentCache.clear()

    def setEditor(self, parent, row):
        return None


class CLocNomenclatureCol(CLocPropertyCol):
    """
    Класс колонки Номенклатуры
    """
    def __init__(self, title, fieldName, width, tableName, **params):
        super(CLocNomenclatureCol, self).__init__(title, fieldName, width, tableName, **params)
        self.inActionsSelectionTableVal = _RECIPE
        self._nomenclatureIdBeforeEdit = None

    def setEditor(self, parent, row):
        currentIndex = parent.parentWidget().currentIndex()
        model = currentIndex.model()
        self._nomenclatureIdBeforeEdit = model.value(row, self.fieldName())
        editor = CNomenclatureComboBox(parent)
        editor.setOnlyNomenclature(True)
        editor.setNomenclatureActiveSubstanceId(model.value(row, 'activeSubstance_id'))
        return editor

    def getNomenclatureIdBeforeEdit(self):
        return self._nomenclatureIdBeforeEdit

    def setNomenclatureIdBeforeEdit(self, value):
        self._nomenclatureIdBeforeEdit = value


class CLocActiveSubstanceCol(CLocPropertyCol):
    """
    Класс колонки Действующего вещества
    """
    def __init__(self, title, fieldName, width, tableName, **params):
        super(CLocActiveSubstanceCol, self).__init__(title, fieldName, width, tableName, **params)
        self.inActionsSelectionTableVal = _ACTIVESUBSTANCE

    def setEditor(self, parent, row):
        currentIndex = parent.parentWidget().currentIndex()
        editor = CActiveSubstanceComboBox(parent)
        editor.setNomenclatureId(currentIndex.model().value(row, 'nomenclature_id'))
        return editor


class CLocSignaCol(CLocPropertyCol):
    """
    Класс колонки Signa
    """
    def __init__(self, title, fieldName, width, tableName, **params):
        super(CLocSignaCol, self).__init__(title, fieldName, width, tableName, **params)
        self.inActionsSelectionTableVal = _SIGNA

    def setEditor(self, parent, row):
        currentIndex = parent.parentWidget().currentIndex()
        nomenclatureId = forceInt(currentIndex.model().value(row, 'nomenclature_id'))
        editor = None
        if nomenclatureId != 0:
            usingTypeIdList = []
            db = QtGui.qApp.db
            tableUsingTypes = CTable('rbNomenclatureUsingType', db)
            tableNomenclatureUsingType = CTable('rbNomenclature_UsingType', db)
            where = tableNomenclatureUsingType['master_id'].eq(nomenclatureId)
            recList = db.getRecordList(tableNomenclatureUsingType, tableNomenclatureUsingType['usingType_id'].name(), where)
            for record in recList:
                usingTypeIdList.append(record.value('usingType_id'))
            editor = CRBComboBox(parent)
            editor.setTable(tableUsingTypes.name(), filter=tableUsingTypes['id'].inlist(usingTypeIdList))
        return editor


class CLocDosesCol(CLocPropertyCol):
    """
    Класс колонки Doses
    """
    def __init__(self, title, fieldName, width, tableName, **params):
        super(CLocDosesCol, self).__init__(title, fieldName, width, tableName, **params)
        self.inActionsSelectionTableVal = _DOSES

    def toString(self, val, record):
        return val

    def setEditor(self, parent, row):
        currentIndex = parent.parentWidget().currentIndex()
        nomenclatureId = forceInt(currentIndex.model().value(row, 'nomenclature_id'))
        editor = None
        if nomenclatureId != 0:
            editor = QDoubleSpinBox(parent)
            editor.setMinimum(0)
            editor.setMaximum(9999.99)
            editor.setSingleStep(0.1)
        return editor

    def setEditorData(self, editor, data, record):
        val = record.value('doses').toFloat()
        if val[1]:
            editor.setValue(val[0])
        else:
            editor.setValue(0.0)


class CLfFormInDocTableCol(CRBInDocTableCol):
    def __init__(self, title, fieldName, width, tableName, **params):
        CRBInDocTableCol.__init__(self, title, fieldName, width, tableName, **params)

    def createEditor(self, parent):
        editor = CSmnnGrlsLfComboBoxEx(parent)
        editor.setOnlySmnnUUID(True)
        editor.setOnlyExists(True)
        editor.setOnlySmnnUUID(True)
        return editor

    def setEditorData(self, editor, value, record):
        orgStructureId = forceRef(record.value('orgStructure_id'))
        nomenclatureId = forceRef(record.value('nomenclature_id'))
        smnnUUID = forceStringEx(record.value('smnnUUID'))
        editor.setOrgStructureId(orgStructureId if orgStructureId else QtGui.qApp.currentOrgStructureId())
        editor.setNomenclatureId(nomenclatureId)
        editor.setNomenclatureSmnnUUID(smnnUUID)
        editor.setValue(forceStringEx(value))


class CSmnnInDocTableCol(CInDocTableCol):
    def __init__(self, title, fieldName, width, **params):
        CInDocTableCol.__init__(self, title, fieldName, width, **params)
        self.smnnCaches = {}

    def toString(self, val, record):
        name = u''
        smnnUUID = forceStringEx(val)
        if smnnUUID:
            name = self.smnnCaches.get(smnnUUID, u'')
            if not name:
                db = QtGui.qApp.db
                table = db.table('esklp.Smnn')
                record = db.getRecordEx(table, [table['code'], table['mnn'], table['form']], [table['UUID'].eq(smnnUUID)])
                if record:
                    name = forceStringEx(record.value('mnn'))
                    self.smnnCaches[smnnUUID] = name
        return toVariant(name)

    def createEditor(self, parent):
        editor = CSmnnComboBoxEx(parent)
        editor.setOnlyExists(True)
        return editor

    def setEditorData(self, editor, value, record):
        orgStructureId = forceRef(record.value('orgStructure_id'))
        nomenclatureId = forceRef(record.value('nomenclature_id'))
        editor.setOrgStructureId(orgStructureId if orgStructureId else QtGui.qApp.currentOrgStructureId())
        editor.setNomenclatureId(nomenclatureId)
        editor.setValue(forceStringEx(value))


def getEditorData(self, editor):
        return toVariant(forceStringEx(editor.value()))


class ActionTypeGroupEditor(CItemEditorBaseDialog, Ui_ActionTypeGroupEditorDialog):
    """
    Диалог редактирования шаблона назначения действий.
    Задаём код, имя шаблона, доступность.
    Позволяет добавлять либо удалять действия из шаблона.
    """
            
    def __init__(self, parent, templateId, enableOffset=False):
        super(ActionTypeGroupEditor, self).__init__(parent, 'ActionTypeGroup')
        self._templateId = templateId
        self._class = -1
        self._updateOffsetOnInit = True
        self.addModels('ActionTypes', CActionTypesList('ActionTypeGroup_Item', 'id', 'master_id', self))
        self.modelActionTypes.addCol(CRBInDocTableCol(u'Код', 'actionType_id', 7, 'ActionType', **{'showFields': 0, 'readOnly': True}))
        self.modelActionTypes.addCol(CRBInDocTableCol(u'Наименование', 'actionType_id', 18, 'ActionType', **{'showFields': 1, 'readOnly': True}))
        self.modelActionTypes.addCol(CIntInDocTableCol(u'Количество', 'amount', 13, **{'maxLength': 2, 'inputMask': '000'}))
        self.modelActionTypes.addCol(CIntInDocTableCol(u'Длительность', 'duration', 13, **{'maxLength': 2, 'inputMask': '000'}))
        self.modelActionTypes.addCol(CIntInDocTableCol(u'Интервал', 'periodicity', 10, **{'maxLength': 2, 'inputMask': '000'}))
        self.modelActionTypes.addCol(CIntInDocTableCol(u'Кратность', 'aliquoticity', 10, **{'maxLength': 3, 'inputMask': '000'}))
        self.modelActionTypes.addCol(CLocNomenclatureCol(u'Recipe', 'nomenclature_id', 18, 'rbNomenclature'))
        self.modelActionTypes.addCol(CLocDosesCol(u'Doses', 'doses', 6, 'rbNomenclature'))
        self.modelActionTypes.addCol(CLocSignaCol(u'Signa', 'signa', 6, 'rbNomenclatureUsingType'))
        self.modelActionTypes.addCol(CLocActiveSubstanceCol(u'Действующее вещество', 'activeSubstance_id', 21, 'rbNomenclatureActiveSubstance'))
        self.modelActionTypes.addCol(CActionTypesList.CActionTemplateInDocTableCol(self))
        self.modelActionTypes.addCol(CSmnnInDocTableCol(u'МНН', 'smnnUUID', 22))
        self.modelActionTypes.addCol(CLfFormInDocTableCol(u'Форма выпуска', 'lfForm_id',  10, 'rbLfForm'))
        self.modelActionTypes.addCol(CRBInDocTableCol(u'Параметр расчета', 'actionPropertyTemplate_id', 10, 'ActionPropertyTemplate', showFields=CRBComboBox.showCodeAndName, filter=u'ActionPropertyTemplate.isCalcParamDoseNomenclatureExpense=1'))
        #self.modelActionTypes.addCol(CIntInDocTableCol(u'Смещение', 'offset', 10, **{'maxLength': 3, 'inputMask': '000'}))
        self.modelActionTypes.addHiddenCol('orgStructure_id')
        self.modelActionTypes.setExtColsPresent(True)
        self.editableCols = ['duration', 'periodicity', 'aliquoticity', 'nomenclature_id', 'doses', 'signa', 'activeSubstance_id', 'smnnUUID', 'lfForm_id', 'actionPropertyTemplate_id', 'offset']
        self.addObject('actAddAction', QtGui.QAction(u'Добавить', self))
        self.addObject('actDelAction', QtGui.QAction(u'Удалить', self))
        self.addObject('actClearField', QtGui.QAction(u'Очистить ячейку', self))
        self.actClearField.setShortcut(QKeySequence('DEL'))
        self.addAction(self.actClearField)
        self.setupUi(self)
        self.tblActionTypes.addPopupAction(self.actAddAction)
        self.tblActionTypes.addPopupAction(self.actDelAction)
        self.tblActionTypes.addPopupAction(self.actClearField)
        self.setModels(self.tblActionTypes, self.modelActionTypes, self.selectionModelActionTypes)

        self.codeDuplicateCheck = False # Флаг проверки дублирования кода шаблона в БД
        if self._templateId: # Редактируем шаблон
            self.load(self._templateId)
            self.modelActionTypes.loadItems(self._templateId)
        else: # Создаём новый шаблон
            self.codeDuplicateCheck = True

        index = self.modelActionTypes.index(self.modelActionTypes.rowCount() - 1, 0)
        if index.isValid():
            self.tblActionTypes.selectRow(index.row())
        self.tblActionTypesContrlosEnable(bool(self.modelActionTypes.rowCount()))
        if enableOffset:
            self.chkEnableOffset.setChecked(True)
        self.btnAddActions.clicked.connect(self.on_actAddAction_triggered)
        self.btnDelActions.clicked.connect(self.on_actDelAction_triggered)
        if not self._updateOffsetOnInit:
             self.chkEnableOffset.stateChanged.emit(self.chkEnableOffset.checkState())
             self._updateOffsetOnInit = False

    def setActionTypes(self, actionsList):
        """
        Создание списка Action Types на основе данных из внешней таблицы (списка QSqlRecord с требуемыми полями)
        Используется при создании шаблона из редактора события ('F9' либо 'Назначение ЛС')

        :param actionsList: список sql-записей для добавления в модель modelActionTypes
        :type actionsList: QSqlRecord
        """
        recordList = []
        numitems = len(actionsList)
        for action in actionsList:
            record = self.modelActionTypes.getEmptyRecord()
            record.setValue('actionType_id', action.value('actionType_id'))
            record.setValue('orgStructure_id', action.value('orgStructure_id'))
            record.setValue('duration', action.value('duration'))
            record.setValue('periodicity', action.value('periodicity'))
            record.setValue('aliquoticity', action.value('aliquoticity'))
            record.setValue('nomenclature_id', action.value('nomenclature_id'))
            record.setValue('doses', action.value('doses') if action.value('doses') != '----' else None)
            record.setValue('signa', action.value('signa') if action.value('signa') != '----' else None)
            record.setValue('activeSubstance_id', forceInt(action.value('activeSubstance_id')) if forceInt(action.value('activeSubstance_id')) > 0 else None)
            record.setValue('actionTemplate_id', action.value('actionTemplateId'))
            record.setValue('smnnUUID', action.value('smnnUUID'))
            record.setValue('lfForm_id', action.value('lfForm_id'))
            record.setValue('actionPropertyTemplate_id', action.value('actionPropertyTemplate_id'))
            record.setValue('offset', action.value('offset'))
            record.setValue('ATItemClass', forceInt(action.value('class')))
            record.setValue('extItemIndex', forceInt(action.value('proxyModelIndex')))
            record.setValue('amount', forceInt(action.value('amount')))
            recordList.append(record)
        lastrow = self.modelActionTypes.realRowCount()
        if numitems > 0:
            for i, record in enumerate(recordList):
                self.modelActionTypes.insertRecord(lastrow+i, record)
        # После заполнения таблицы - выбираем последний элемент и обновляем активность элементов управления в диалоге
        index = self.modelActionTypes.index(self.modelActionTypes.rowCount() - 1, 0)
        if index.isValid():
            self.tblActionTypes.selectRow(index.row())
        self.tblActionTypesContrlosEnable(bool(self.modelActionTypes.rowCount()))

    def tblActionTypesContrlosEnable(self, enable):
        self.btnDelActions.setEnabled(enable)
        self.actDelAction.setEnabled(enable)
        self.actClearField.setEnabled(enable)

    @pyqtSignature('')
    def on_actAddAction_triggered(self):
        """
        Добавление типов действия в список
        """
        recordList = []
        addActionsIdList = []
        dialog = CActionTypeSelector(self)
        if dialog.exec_():
            addActionsIdList = dialog.modelSelectBox._modelData
        dialog.deleteLater()

        numitems = len(addActionsIdList)
        for i, rec in enumerate(addActionsIdList):
            record = self.modelActionTypes.getEmptyRecord()
            record.setValue('actionType_id', rec.value('id'))
            record.setValue('ATItemClass', rec.value('class'))
            record.setValue('extItemIndex', None)
            record.setValue('amount', toVariant(1))
            recordList.append(record)
        lastrow = self.modelActionTypes.realRowCount()
        if numitems > 0:
            for i, record in enumerate(recordList):
                self.modelActionTypes.insertRecord(lastrow+i, record)
        index = self.modelActionTypes.index(self.modelActionTypes.rowCount() - 1, 0)
        if index.isValid():
            self.tblActionTypes.selectRow(index.row())
        self.tblActionTypesContrlosEnable(bool(self.modelActionTypes.rowCount()))

    @pyqtSignature('')
    def on_actDelAction_triggered(self):
        """
        Удаление типов действий из списка
        """
        rows = self.tblActionTypes.getSelectedRows()
        if rows:
            removeItemsCount = len(rows)
            tailItemRow = rows[-1]
            for row in reversed(rows):
                self.modelActionTypes.removeRows(row, 1, QModelIndex())
            rowToSelect = tailItemRow + 1 - removeItemsCount
            if (rowToSelect < self.modelActionTypes.rowCount()):
                self.tblActionTypes.selectRow(rowToSelect)
            else:
                self.tblActionTypes.selectRow(self.modelActionTypes.rowCount() - 1)
            self.tblActionTypesContrlosEnable(bool(self.modelActionTypes.rowCount()))

    @pyqtSignature('')
    def on_actClearField_triggered(self):
        """
        Очистка содержимого выбранной ячейки
        """
        index = self.tblActionTypes.currentIndex()
        if not index.isValid():
            return
        colIndex = index.column()
        rowIndex = index.row()
        col = self.modelActionTypes.cols()[colIndex]
        if not col.readOnly():
            # Перед очисткой колонки с номенклатурой нужно сохранить значение ячейки (для определения факта правки данных)
            if col.fieldName() == 'nomenclature_id':
                col.setNomenclatureIdBeforeEdit(self.modelActionTypes.value(rowIndex, col.fieldName()))
            self.modelActionTypes.setData(index, None)

    def getRecord(self):
        """
        Формирование sql-записи c данными шаблона для сохранения в БД. Определение класса шаблонов на основе добавленных действий
        :return: Подготовленная запись QSql для таблицы ActionTypeGroup
        :rtype: QSqlRecord
        """
        templateClasses = {0:u'статус', 1:u'диагностика', 2:u'лечение', 3:u'прочие мероприятия'}
        classesList = []
        record = CItemEditorBaseDialog.getRecord(self)

        for item in self.modelActionTypes.items():
            if item.value('ATItemClass').toInt()[1]:
                classesList.append(item.value('ATItemClass').toInt()[0])
            else: # Для ранее добавленных действий добавляем "магический" класс
                classesList.append(-1)

        classesSet = set(classesList)
        # Список классов пуст (нестандартная ситуация)
        if len(classesSet) == 0:
            record.setValue('class', toVariant(self._class))
        # В списке действий - действия одного класса - можно присваивать класс для шаблона, также учитываем ситуацию,
        # когда делается сохранение списка, который не менялся после открытия (все действия имеют класс -1)
        elif len(classesSet) == 1:
            templateNewClass = classesSet.pop()
            if templateNewClass != -1:
                if templateNewClass != self._class and self._class != -1:
                    QtGui.QMessageBox.warning(self, u'Предупреждение', u'Класс шаблона будет изменён, новый класс шаблона: %s' % templateClasses.get(templateNewClass, u'None'))
                record.setValue('class', toVariant(templateNewClass))
            else: # Если шаблон не редактировали и закрывают через сохранение - класс не меняем
                record.setValue('class', toVariant(self._class))
        # В списке действий - только прежде добавленные действия + вновь добавленные одного и того же класса, если вновь добавленный класс совпадает с
        # текущим классом шаблона - сохраняем текущий класс шаблона
        elif len(classesSet) == 2 and -1 in classesSet:
            classesSet.remove(-1)
            templateNewClass = classesSet.pop()
            if templateNewClass != self._class and self._class != -1:
                if self._class != None:
                    QtGui.QMessageBox.warning(self, u'Предупреждение', u'Класс шаблона будет изменён, новый класс шаблона "Не определено"')
                record.setValue('class', toVariant(None))
            else:
                record.setValue('class', toVariant(templateNewClass))
        # В список действий добавлены действия с разными классами - класс шаблона - None
        else:
            if not self._class is None and self._class != -1:
                QtGui.QMessageBox.warning(self, u'Предупреждение', u'Класс шаблона будет изменён, новый класс шаблона "Не определено"')
            record.setValue('class', toVariant(None))

        record.setValue('code', toVariant(forceStringEx(self.edtGroupCode.text())))
        record.setValue('name', toVariant(forceStringEx(self.edtGroupName.text())))
        record.setValue('isOffset', toVariant(self.chkEnableOffset.isChecked()))
        getComboBoxValue(self.cmbAvailability, record, 'availability')
        return record

    def checkDataBeforeOpen(self):
        rec = self.record()
        self.edtGroupCode.setText(rec.value('code').toString())
        self.edtGroupName.setText(rec.value('name').toString())
        self.cmbAvailability.setCurrentIndex(forceInt(rec.value('availability')))
        self.chkEnableOffset.setChecked(forceBool(rec.value('isOffset')))
        self._class = rec.value('class').toInt()[0] if not rec.value('class').isNull() else None
        return True

    def checkDataEntered(self):
        """
        Проверка данных перед сохранением в БД
        Нельзя создавать шаблоны:
            с пустым кодом
            с дублирующимся в БД кодом
            с пустым наименованием
            с пустым списком типов действий
        """
        db = QtGui.qApp.db
        codeField = db.table('ActionTypeGroup').findField('code')
        delField = db.table('ActionTypeGroup').findField('deleted')
        code = forceStringEx(self.edtGroupCode.text())
        where = db.joinAnd([codeField.eq(code), delField.eq(0)])
        # Код шаблона
        if code == '':
            QtGui.QMessageBox.warning(self, u'Предупреждение', u'Поле "Код" не должно быть пустым!')
            return False
        # Дублирование кода шаблона
        if self.codeDuplicateCheck:
            if db.getIdList('ActionTypeGroup', 'id', where):
                QtGui.QMessageBox.warning(self, u'Предупреждение', u'Шаблон с таким кодом уже есть в базе.\nЗадайте другой код!')
                return False
        # Имя шаблона
        if forceStringEx(self.edtGroupName.text()) == '':
            QtGui.QMessageBox.warning(self, u'Предупреждение', u'Поле "Наименование" не должно быть пустым!')
            return False
        # Список типов действий
        itemsList = self.modelActionTypes.items()
        if not itemsList:
            QtGui.QMessageBox.warning(self, u'Предупреждение', u'Список типов действий не должен быть пустым!')
            return False
        return True

    def afterSave(self):
        """
        Сохранение типов действий в ActionTypeGroup_Item
        """
        CItemEditorBaseDialog.afterSave(self)
        self._templateId = self.itemId()
        self.modelActionTypes.saveItems(self._templateId)

    def getTemplateId(self):
        return self._templateId

    @pyqtSignature('')
    def on_tblActionTypes_popupMenuAboutToShow(self):
        self.actClearField.setVisible(True) if self.modelActionTypes.cols()[self.tblActionTypes.currentIndex().column()].fieldName() in self.editableCols else self.actClearField.setVisible(False)

    @pyqtSignature('int')
    def on_chkEnableOffset_stateChanged(self, state):
        self.modelActionTypes.setOffsetEnabled(forceBool(state))
