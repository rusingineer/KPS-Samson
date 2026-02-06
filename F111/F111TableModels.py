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
import json
from collections import OrderedDict

from PyQt4 import QtGui, QtSql
from PyQt4.QtCore import Qt, QDate, QVariant, QModelIndex, QRegExp, QObject, SIGNAL
from Events.Action import CAction

from library.ICDInDocTableCol import CICDExInDocTableCol
from library.InDocTable import (CInDocTableModel,
                                CDateInDocTableCol,
                                CInDocTableCol,
                                forcePyType,
                                CSelectStrInDocTableCol,
                                CRegExpedInDocTableCol)
from library.LineEditWithRegExpValidator import CLineEditWithRegExpValidatorMasked
from library.TableModel import CTableModel, CBoolCol, CCol
from library.Utils import (forceDate,
                        forceInt,
                        forceRef,
                        forceString,
                        forceStringEx,
                        trim,
                        toVariant
                        )

from Events.ActionPropertiesTable import CActionPropertiesTableModel
from Orgs.OrgComboBox import COrgIsMedicalBtnInDocTableCol


class CLocNumbeRowColumn(CInDocTableCol):
    def __init__(self, title, fieldName, width, **params):
        CInDocTableCol.__init__(self, title, fieldName, width, **params)

    def toString(self, val, record, row):
        return toVariant(row + 1)

    def toSortString(self, val, record, row):
        return forcePyType(self.toString(val, record, row))

    def toStatusTip(self, val, record, row):
        return self.toString(val, record, row)

    def alignment(self):
        return QVariant(Qt.AlignLeft + Qt.AlignTop)


class CSOPSvORNMTableModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'Client', 'id', 'id', parent)
        self.addExtCol(CDateInDocTableCol(u'Дата Операции', 'operationDate', 20, canBeEmpty=True), QVariant.Date).setReadOnly(False)
        self.addExtCol(COrgIsMedicalBtnInDocTableCol(u'Медицинская организация', 'org_id', 30), QVariant.Int).setReadOnly(False)
        self.addExtCol(CInDocTableCol(u'Название операции', 'operationName', 20), QVariant.String).setReadOnly(False)
        self.addExtCol(CInDocTableCol(u'При кесаревом сечении - срок беременности, показания', 'operationIndications', 20), QVariant.String).setReadOnly(False)
        self.addExtCol(CInDocTableCol(u'Локализация рубца на матке', 'localizationScar', 20), QVariant.String).setReadOnly(False)
        self.addExtCol(CInDocTableCol(u'Особенности операции, послеоперационного периода', 'operationFeatures', 20), QVariant.String).setReadOnly(False)
        self.readOnly = False
        self.action = None
        self.eventEditor = None
        self.oldItems = []


    def getEmptyRecord(self):
        result = QtSql.QSqlRecord()
        result.append(QtSql.QSqlField('operationDate', QVariant.Date))
        result.append(QtSql.QSqlField('org_id', QVariant.Int))
        result.append(QtSql.QSqlField('operationName', QVariant.String))
        result.append(QtSql.QSqlField('operationIndications', QVariant.String))
        result.append(QtSql.QSqlField('localizationScar', QVariant.String))
        result.append(QtSql.QSqlField('operationFeatures', QVariant.String))
        return result


    def clearItems(self):
        self._items = []
        self.saveItems()
        self.reset()


    def setOldItems(self, items):
        self.oldItems = []
        for item in items:
            self.oldItems.append(item)


    def loadOldItems(self):
        if self.oldItems and self.eventEditor and self.action:
            self._items = self.oldItems
            self.saveItems()
        self.reset()


    def setEventEditor(self, eventEditor):
        self.eventEditor = eventEditor


    def setAction(self, action):
        self.action = action


    def setReadOnly(self, value=True):
        self.readOnly = value


    def flags(self, index):
        if self.readOnly:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return CInDocTableModel.flags(self, index)


    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        row = index.row()
        if 0 <= row < len(self._items):
            if role == Qt.EditRole:
                col = self._cols[column]
                record = self._items[row]
                return record.value(col.fieldName())
            if role == Qt.DisplayRole:
                col = self._cols[column]
                record = self._items[row]
                return col.toString(record.value(col.fieldName()), record)
            if role == Qt.StatusTipRole:
                col = self._cols[column]
                record = self._items[row]
                return col.toStatusTip(record.value(col.fieldName()), record)
            if role == Qt.TextAlignmentRole:
                col = self._cols[column]
                return col.alignment()
            if role == Qt.CheckStateRole:
                col = self._cols[column]
                record = self._items[row]
                return col.toCheckState(record.value(col.fieldName()), record)
            if role == Qt.ForegroundRole:
                col = self._cols[column]
                record = self._items[row]
                return col.getForegroundColor(record.value(col.fieldName()), record)
        return QVariant()


    def setData(self, index, value, role=Qt.EditRole):
        row = index.row()
        if row > 4:
            return False
        result = CInDocTableModel.setData(self, index, value, role)
        return result


    def removeRows(self, row, count, parentIndex = QModelIndex()):
        if 0 <= row and row+count <= len(self._items):
            self.beginRemoveRows(parentIndex, row, row+count-1)
            del self._items[row:row+count]
            self.endRemoveRows()
            self.saveItems()
            return True
        else:
            return False


    def removeRow(self, row, parentIndex = QModelIndex()):
        return self.removeRows(row, 1, parentIndex)


    def loadItems(self, masterId):
        if not self.action or (self.action.getRecord() and not forceRef(self.action.getRecord().value('id'))):
            self.saveItems()
        else:
            if self.eventEditor and self.action:
                items = {}
                for property in self.action._propertiesById.itervalues():
                    propertyType = property.type()
                    shortName = trim(propertyType.shortName)
                    value = property._value
                    propertyValue = propertyType.convertQVariantToPyValue(value) if type(value) == QVariant else value
                    if isinstance(propertyValue, basestring) or propertyValue.__class__.__name__ == 'QString':
                        propertyValue = trim(propertyValue)
                    if propertyValue:
                        item = items.get(shortName, [])
                        if propertyValue and (isinstance(propertyValue, basestring) or propertyValue.__class__.__name__ == 'QString') and len(propertyValue) > 1:
                            propertyValue = propertyValue.split(u',')
                            item.extend(propertyValue)
                        else:
                            item.append(propertyValue)
                        items[shortName] = item
                if items:
                    self._items = []
                    for idx in xrange(5):
                        operationDate = self.eventEditor.getPropertyValue(items, u'СОП:СоРнМ:ДО:%s'%(forceString(idx+1)), QDate)
                        org_id = self.eventEditor.getPropertyValue(items, u'СОП:СоРнМ:МО:%s'%(forceString(idx+1)), int)
                        operationName = self.eventEditor.getPropertyValue(items, u'СОП:СоРнМ:НО:%s'%(forceString(idx+1)), unicode)
                        operationIndications = self.eventEditor.getPropertyValue(items, u'СОП:СоРнМ:СБП:%s'%(forceString(idx+1)), unicode)
                        localizationScar = self.eventEditor.getPropertyValue(items, u'СОП:СоРнМ:ЛРМ:%s'%(forceString(idx+1)), unicode)
                        operationFeatures = self.eventEditor.getPropertyValue(items, u'СОП:СоРнМ:ООПП:%s'%(forceString(idx+1)), unicode)
                        if operationDate or org_id or operationName or operationIndications or localizationScar or operationFeatures:
                            item = self.getEmptyRecord()
                            item.setValue('operationDate', toVariant(operationDate))
                            item.setValue('org_id', toVariant(org_id))
                            item.setValue('operationName', toVariant(operationName))
                            item.setValue('operationIndications', toVariant(operationIndications))
                            item.setValue('localizationScar', toVariant(localizationScar))
                            item.setValue('operationFeatures', toVariant(operationFeatures))
                            self._items.append(item)
        self.reset()


    def saveItems(self):
        if self.eventEditor and self.eventEditor.action:
            for idx, record in enumerate(self._items):
                self.eventEditor.setProperty(QVariant(forceDate(record.value('operationDate'))), u'СОП:СоРнМ:ДО:%s'%(forceString(idx+1)))
                self.eventEditor.setProperty(QVariant(forceRef(record.value('org_id'))), u'СОП:СоРнМ:МО:%s'%(forceString(idx+1)))
                self.eventEditor.setProperty(QVariant(forceStringEx(record.value('operationName'))), u'СОП:СоРнМ:НО:%s'%(forceString(idx+1)))
                self.eventEditor.setProperty(QVariant(forceStringEx(record.value('operationIndications'))), u'СОП:СоРнМ:СБП:%s'%(forceString(idx+1)))
                self.eventEditor.setProperty(QVariant(forceStringEx(record.value('localizationScar'))), u'СОП:СоРнМ:ЛРМ:%s'%(forceString(idx+1)))
                self.eventEditor.setProperty(QVariant(forceStringEx(record.value('operationFeatures'))), u'СОП:СоРнМ:ООПП:%s'%(forceString(idx+1)))
            rowCount = self.realRowCount()
            if rowCount < 5:
                noRows = 5 - rowCount
                idx = rowCount + 1
                while noRows > 0:
                    self.delProperty(u'СОП:СоРнМ:ДО:%s'%(forceString(idx)))
                    self.delProperty(u'СОП:СоРнМ:МО:%s'%(forceString(idx)))
                    self.delProperty(u'СОП:СоРнМ:НО:%s'%(forceString(idx)))
                    self.delProperty(u'СОП:СоРнМ:СБП:%s'%(forceString(idx)))
                    self.delProperty(u'СОП:СоРнМ:ЛРМ:%s'%(forceString(idx)))
                    self.delProperty(u'СОП:СоРнМ:ООПП:%s'%(forceString(idx)))
                    idx += 1
                    noRows -= 1
            self.action = self.eventEditor.action


    def delProperty(self, shortName):
        shortName = trim(shortName)
        if self.eventEditor.action and self.action and shortName:
            for propertyTypeName, property in self.action._propertiesByName.items():
                propertyType = property.type()
                if shortName == trim(propertyType.shortName):
                    del self.eventEditor.action[propertyType.name]


class CNVNBVARRSTableModel(CInDocTableModel):
    class CIndividualRiskInDocTableCol(CRegExpedInDocTableCol):
        def __init__(self, title, fieldName, width, **params):
            CRegExpedInDocTableCol.__init__(self, title, fieldName, width, **params)
            self.widget = params.get('widget', None)
            self.regExp = forceStringEx(u'[1]{1}[:]{1}[0-9]{1,6}')

        def setEditorData(self, editor, value, record):
            editor.setRegExp(self.regExp)
            editor.setText(forceStringEx(value))
            validator = self.getLocValidator(value, record)
            editor.setValidator(validator)
            if self._inputMask:
                editor.setInputMask(self._inputMask)

        def getForegroundColor(self, val, record):
            valueIndividualRisk = forceStringEx(val)
            if valueIndividualRisk:
                validator = self.getLocValidator(val, record)
                if validator:
                    regExp = validator.regExp()
                    if regExp and not regExp.exactMatch(forceString(valueIndividualRisk)):
                        return QVariant(QtGui.QColor(255, 0, 0))
            return QVariant()

        def getLocValidator(self, val, record):
            validator = None
            if self.regExp:
                rx = QRegExp(self.regExp, Qt.CaseSensitive, QRegExp.RegExp2)
                if not rx.isValid():
                    rx = QRegExp('', Qt.CaseSensitive, QRegExp.RegExp2)
                validator = QtGui.QRegExpValidator(rx, self.widget)
            return validator

        def createEditor(self, parent):
            editor = CLineEditWithRegExpValidatorMasked(parent)
            return editor

    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'Client', 'id', 'id', parent)
        self._parent = parent
        self.addExtCol(CInDocTableCol(u'Риски осложнений', 'risksComplications', 20), QVariant.String).setReadOnly(False)
        self.addExtCol(self.CIndividualRiskInDocTableCol(u'Значение индивидуального риска', 'valueIndividualRisk', 20, widget=self._parent, inputMask=u'9:999999;_'), QVariant.String).setReadOnly(False)
        self.addExtCol(CSelectStrInDocTableCol(u'Интерпретация', 'interpritation', 20, (u'', u'Низкий', u'Высокий')), QVariant.String).setReadOnly(False)
        self.risksComplicationsNames = [u'1. Риск задержки развития плода',
                                                          u'2. Риск преждевременных родов',
                                                          u'3. Риск преэклампсии ранней (до 34 недель)',
                                                          u'4. Риск преэклампсии поздней (до 37 недель)',
                                                          u'5. Риски трисомии 13',
                                                          u'6. Риски трисомии 18',
                                                          u'7. Риски трисомии 21'
                                                        ]
        self.readOnly = False
        self.action = None
        self.eventEditor = None
        self.oldItems = []


    def getEmptyRecord(self):
        result = QtSql.QSqlRecord()
        result.append(QtSql.QSqlField('risksComplications', QVariant.String))
        result.append(QtSql.QSqlField('valueIndividualRisk', QVariant.String))
        result.append(QtSql.QSqlField('interpritation', QVariant.String))
        return result


    def clearItems(self):
        self._items = []
        self.saveItems()
        self.reset()


    def setOldItems(self, items):
        self.oldItems = []
        for item in items:
            self.oldItems.append(item)


    def loadOldItems(self):
        if self.oldItems and self.eventEditor and self.action:
            self._items = self.oldItems
            self.saveItems()
        self.reset()


    def setEventEditor(self, eventEditor):
        self.eventEditor = eventEditor


    def setAction(self, action):
        self.action = action


    def setReadOnly(self, value=True):
        self.readOnly = value


    def flags(self, index):
        flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if self.readOnly:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        if index.column() != 0:
            flags |= Qt.ItemIsEditable
        return flags


    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        row = index.row()
        if 0 <= row < len(self._items):
            if role == Qt.EditRole:
                col = self._cols[column]
                record = self._items[row]
                return record.value(col.fieldName())
            if role == Qt.DisplayRole:
                col = self._cols[column]
                record = self._items[row]
                return col.toString(record.value(col.fieldName()), record)
            if role == Qt.StatusTipRole:
                col = self._cols[column]
                record = self._items[row]
                return col.toStatusTip(record.value(col.fieldName()), record)
            if role == Qt.TextAlignmentRole:
                col = self._cols[column]
                return col.alignment()
            if role == Qt.CheckStateRole:
                col = self._cols[column]
                record = self._items[row]
                return col.toCheckState(record.value(col.fieldName()), record)
            if role == Qt.ForegroundRole:
                col = self._cols[column]
                record = self._items[row]
                return col.getForegroundColor(record.value(col.fieldName()), record)
        return QVariant()


    def setData(self, index, value, role=Qt.EditRole):
        row = index.row()
        if row > 6:
            return False
        result = CInDocTableModel.setData(self, index, value, role)
        return result


    def removeRows(self, row, count, parentIndex = QModelIndex()):
        if 0 <= row and row+count <= len(self._items):
            self.beginRemoveRows(parentIndex, row, row+count-1)
            del self._items[row:row+count]
            self.endRemoveRows()
            self.saveItems()
            return True
        else:
            return False


    def removeRow(self, row, parentIndex = QModelIndex()):
        return self.removeRows(row, 1, parentIndex)


    def loadItems(self, masterId):
        if not self.action or (self.action.getRecord() and not forceRef(self.action.getRecord().value('id'))):
            self._items = []
            for idx in xrange(7):
                item = self.getEmptyRecord()
                item.setValue('risksComplications', toVariant(self.risksComplicationsNames[idx]))
                item.setValue('valueIndividualRisk', toVariant(''))
                item.setValue('interpritation', toVariant(''))
                self._items.append(item)
            self.saveItems()
        else:
            if self.eventEditor and self.action:
                items = {}
                for property in self.action._propertiesById.itervalues():
                    propertyType = property.type()
                    shortName = trim(propertyType.shortName)
                    value = property._value
                    propertyValue = propertyType.convertQVariantToPyValue(value) if type(value) == QVariant else value
                    if isinstance(propertyValue, basestring) or propertyValue.__class__.__name__ == 'QString':
                        propertyValue = trim(propertyValue)
                    if propertyValue:
                        item = items.get(shortName, [])
                        if propertyValue and (isinstance(propertyValue, basestring) or propertyValue.__class__.__name__ == 'QString') and len(propertyValue) > 1:
                            propertyValue = propertyValue.split(u',')
                            item.extend(propertyValue)
                        else:
                            item.append(propertyValue)
                        items[shortName] = item
                if items:
                    self._items = []
                    for idx in xrange(7):
                        risksComplications = self.eventEditor.getPropertyValue(items, u'НВНБ:ВАРпРС:РО:%s'%(forceString(idx+1)), unicode)
                        valueIndividualRisk = self.eventEditor.getPropertyValue(items, u'НВНБ:ВАРпРС:ЗИР:%s'%(forceString(idx+1)), unicode)
                        interpritation = self.eventEditor.getPropertyValue(items, u'НВНБ:ВАРпРС:И:%s'%(forceString(idx+1)), unicode)
                        if risksComplications or valueIndividualRisk:
                            item = self.getEmptyRecord()
                            item.setValue('risksComplications', toVariant(risksComplications))
                            item.setValue('valueIndividualRisk', toVariant(valueIndividualRisk))
                            item.setValue('interpritation', toVariant(interpritation))
                            self._items.append(item)
        self.reset()


    def saveItems(self):
        if self.eventEditor and self.eventEditor.action:
            for idx, record in enumerate(self._items):
                self.eventEditor.setProperty(QVariant(forceStringEx(record.value('risksComplications'))), u'НВНБ:ВАРпРС:РО:%s'%(forceString(idx+1)))
                self.eventEditor.setProperty(QVariant(forceStringEx(record.value('valueIndividualRisk'))), u'НВНБ:ВАРпРС:ЗИР:%s'%(forceString(idx+1)))
                self.eventEditor.setProperty(QVariant(forceStringEx(record.value('interpritation'))), u'НВНБ:ВАРпРС:И:%s'%(forceString(idx+1)))
            rowCount = self.realRowCount()
            if rowCount < 7:
                noRows = 7 - rowCount
                idx = rowCount + 1
                while noRows > 0:
                    self.delProperty(u'НВНБ:ВАРпРС:РО:%s'%(forceString(idx)))
                    self.delProperty(u'НВНБ:ВАРпРС:ЗИР:%s'%(forceString(idx)))
                    self.delProperty(u'НВНБ:ВАРпРС:И:%s'%(forceString(idx)))
                    idx += 1
                    noRows -= 1
            self.action = self.eventEditor.action


    def delProperty(self, shortName):
        shortName = trim(shortName)
        if self.eventEditor.action and self.action and shortName:
            for propertyTypeName, property in self.action._propertiesByName.items():
                propertyType = property.type()
                if shortName == trim(propertyType.shortName):
                    del self.eventEditor.action[propertyType.name]


class CNVNBARTableModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'Client', 'id', 'id', parent)
        self.addExtCol(CInDocTableCol(u'Риск осложнений', 'riskComplications', 20), QVariant.String).setReadOnly(False)
        self.addExtCol(CSelectStrInDocTableCol(u'При 1-й явке', 'firstVisit', 30, (u'низкий', u'высокий')), QVariant.String).setReadOnly(False)
        self.addExtCol(CSelectStrInDocTableCol(u'В 11-13 недель', 'weeks11_18', 30, (u'низкий', u'высокий')), QVariant.String).setReadOnly(False)
        self.addExtCol(CSelectStrInDocTableCol(u'В 18-20 недель', 'weeks18_20', 30, (u'низкий', u'высокий')), QVariant.String).setReadOnly(False)
        self.addExtCol(CSelectStrInDocTableCol(u'В 30-34 недели', 'weeks30_34', 30, (u'низкий', u'высокий')), QVariant.String).setReadOnly(False)
        self.risksComplicationsNames = [u'Тромбоэмболические осложнения',
                                        u'Другие']
        self.readOnly = False
        self.action = None
        self.eventEditor = None
        self.oldItems = []


    def getEmptyRecord(self):
        result = QtSql.QSqlRecord()
        result.append(QtSql.QSqlField('riskComplications', QVariant.String))
        result.append(QtSql.QSqlField('firstVisit', QVariant.String))
        result.append(QtSql.QSqlField('weeks11_18', QVariant.String))
        result.append(QtSql.QSqlField('weeks18_20', QVariant.String))
        result.append(QtSql.QSqlField('weeks30_34', QVariant.String))
        return result


    def clearItems(self):
        self._items = []
        self.saveItems()
        self.reset()


    def setOldItems(self, items):
        self.oldItems = []
        for item in items:
            self.oldItems.append(item)


    def loadOldItems(self):
        if self.oldItems and self.eventEditor and self.action:
            self._items = self.oldItems
            self.saveItems()
        self.reset()


    def setEventEditor(self, eventEditor):
        self.eventEditor = eventEditor


    def setAction(self, action):
        self.action = action


    def setReadOnly(self, value=True):
        self.readOnly = value


    def flags(self, index):
        if self.readOnly:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return CInDocTableModel.flags(self, index)


    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        row = index.row()
        if 0 <= row < len(self._items):
            if role == Qt.EditRole:
                col = self._cols[column]
                record = self._items[row]
                return record.value(col.fieldName())
            if role == Qt.DisplayRole:
                col = self._cols[column]
                record = self._items[row]
                return col.toString(record.value(col.fieldName()), record)
            if role == Qt.StatusTipRole:
                col = self._cols[column]
                record = self._items[row]
                return col.toStatusTip(record.value(col.fieldName()), record)
            if role == Qt.TextAlignmentRole:
                col = self._cols[column]
                return col.alignment()
            if role == Qt.CheckStateRole:
                col = self._cols[column]
                record = self._items[row]
                return col.toCheckState(record.value(col.fieldName()), record)
            if role == Qt.ForegroundRole:
                col = self._cols[column]
                record = self._items[row]
                return col.getForegroundColor(record.value(col.fieldName()), record)
        return QVariant()


    def setData(self, index, value, role=Qt.EditRole):
        row = index.row()
        if row > 4:
            return False
        result = CInDocTableModel.setData(self, index, value, role)
        return result


    def removeRows(self, row, count, parentIndex = QModelIndex()):
        if 0 <= row and row+count <= len(self._items):
            self.beginRemoveRows(parentIndex, row, row+count-1)
            del self._items[row:row+count]
            self.endRemoveRows()
            self.saveItems()
            return True
        else:
            return False


    def removeRow(self, row, parentIndex = QModelIndex()):
        return self.removeRows(row, 1, parentIndex)


    def loadItems(self, masterId):
        if not self.action or (self.action.getRecord() and not forceRef(self.action.getRecord().value('id'))):
            self._items = []
            for idx in xrange(2):
                item = self.getEmptyRecord()
                item.setValue('riskComplications', toVariant(self.risksComplicationsNames[idx]))
                self._items.append(item)
            self.saveItems()
        else:
            if self.eventEditor and self.action:
                items = {}
                for property in self.action._propertiesById.itervalues():
                    propertyType = property.type()
                    shortName = trim(propertyType.shortName)
                    value = property._value
                    propertyValue = propertyType.convertQVariantToPyValue(value) if type(value) == QVariant else value
                    if isinstance(propertyValue, basestring) or propertyValue.__class__.__name__ == 'QString':
                        propertyValue = trim(propertyValue)
                    if propertyValue:
                        item = items.get(shortName, [])
                        if propertyValue and (isinstance(propertyValue, basestring) or propertyValue.__class__.__name__ == 'QString') and len(propertyValue) > 1:
                            propertyValue = propertyValue.split(u',')
                            item.extend(propertyValue)
                        else:
                            item.append(propertyValue)
                        items[shortName] = item
                if items:
                    self._items = []
                    for idx in xrange(5):
                        riskComplications = self.eventEditor.getPropertyValue(items, u'НВНБ:АР:РО:%s'%(forceString(idx+1)), unicode)
                        firstVisit = self.eventEditor.getPropertyValue(items, u'НВНБ:АР:ППЯ:%s'%(forceString(idx+1)), unicode)
                        weeks11_18 = self.eventEditor.getPropertyValue(items, u'НВНБ:АР:11-13:%s'%(forceString(idx+1)), unicode)
                        weeks18_20 = self.eventEditor.getPropertyValue(items, u'НВНБ:АР:18-20:%s'%(forceString(idx+1)), unicode)
                        weeks30_34 = self.eventEditor.getPropertyValue(items, u'НВНБ:АР:30-34:%s'%(forceString(idx+1)), unicode)
                        if riskComplications or firstVisit or weeks11_18 or weeks18_20 or weeks30_34:
                            item = self.getEmptyRecord()
                            item.setValue('riskComplications', toVariant(riskComplications))
                            item.setValue('firstVisit', toVariant(firstVisit))
                            item.setValue('weeks11_18', toVariant(weeks11_18))
                            item.setValue('weeks18_20', toVariant(weeks18_20))
                            item.setValue('weeks30_34', toVariant(weeks30_34))
                            self._items.append(item)
        self.reset()


    def saveItems(self):
        if self.eventEditor and self.eventEditor.action:
            for idx, record in enumerate(self._items):
                self.eventEditor.setProperty(QVariant(forceStringEx(record.value('riskComplications'))), u'НВНБ:АР:РО:%s'%(forceString(idx+1)))
                self.eventEditor.setProperty(QVariant(forceStringEx(record.value('firstVisit'))), u'НВНБ:АР:ППЯ:%s'%(forceString(idx+1)))
                self.eventEditor.setProperty(QVariant(forceStringEx(record.value('weeks11_18'))), u'НВНБ:АР:11-13:%s'%(forceString(idx+1)))
                self.eventEditor.setProperty(QVariant(forceStringEx(record.value('weeks18_20'))), u'НВНБ:АР:18-20:%s'%(forceString(idx+1)))
                self.eventEditor.setProperty(QVariant(forceStringEx(record.value('weeks30_34'))), u'НВНБ:АР:30-34:%s'%(forceString(idx+1)))
            rowCount = self.realRowCount()
            if rowCount < 5:
                noRows = 5 - rowCount
                idx = rowCount + 1
                while noRows > 0:
                    self.delProperty(u'НВНБ:АР:РО:%s'%(forceString(idx)))
                    self.delProperty(u'НВНБ:АР:ППЯ:%s'%(forceString(idx)))
                    self.delProperty(u'НВНБ:АР:11-13:%s'%(forceString(idx)))
                    self.delProperty(u'НВНБ:АР:18-20:%s'%(forceString(idx)))
                    self.delProperty(u'НВНБ:АР:30-34:%s'%(forceString(idx)))
                    idx += 1
                    noRows -= 1
            self.action = self.eventEditor.action


    def delProperty(self, shortName):
        shortName = trim(shortName)
        if self.eventEditor.action and self.action and shortName:
            for propertyTypeName, property in self.action._propertiesByName.items():
                propertyType = property.type()
                if shortName == trim(propertyType.shortName):
                    del self.eventEditor.action[propertyType.name]


class CNVNBSGVBTableModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'Client', 'id', 'id', parent)
        self.addExtCol(CDateInDocTableCol(u'Дата поступления', 'begDate', 20, canBeEmpty=True), QVariant.Date).setReadOnly(False)
        self.addExtCol(CDateInDocTableCol(u'Дата выписки', 'endDate', 20, canBeEmpty=True), QVariant.Date).setReadOnly(False)
        self.addExtCol(CSelectStrInDocTableCol(u'Порядок', 'order', 30, (u'плановый', u'экстренный')), QVariant.String).setReadOnly(False)
        self.addExtCol(COrgIsMedicalBtnInDocTableCol(u'Медицинская организация', 'org_id', 30), QVariant.Int).setReadOnly(False)
        self.addExtCol(CICDExInDocTableCol(u'Диагноз', 'MKB', 7), QVariant.String).setReadOnly(False)
        self.readOnly = False
        self.action = None
        self.eventEditor = None
        self.oldItems = []


    def getEmptyRecord(self):
        result = QtSql.QSqlRecord()
        result.append(QtSql.QSqlField('begDate', QVariant.Date))
        result.append(QtSql.QSqlField('endDate', QVariant.Date))
        result.append(QtSql.QSqlField('order', QVariant.String))
        result.append(QtSql.QSqlField('org_id', QVariant.Int))
        result.append(QtSql.QSqlField('MKB', QVariant.String))
        return result


    def clearItems(self):
        self._items = []
        self.saveItems()
        self.reset()


    def setOldItems(self, items):
        self.oldItems = []
        for item in items:
            self.oldItems.append(item)


    def loadOldItems(self):
        if self.oldItems and self.eventEditor and self.action:
            self._items = self.oldItems
            self.saveItems()
        self.reset()


    def setEventEditor(self, eventEditor):
        self.eventEditor = eventEditor


    def setAction(self, action):
        self.action = action


    def setReadOnly(self, value=True):
        self.readOnly = value


    def flags(self, index):
        if self.readOnly:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return CInDocTableModel.flags(self, index)


    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        row = index.row()
        if 0 <= row < len(self._items):
            if role == Qt.EditRole:
                col = self._cols[column]
                record = self._items[row]
                return record.value(col.fieldName())
            if role == Qt.DisplayRole:
                col = self._cols[column]
                record = self._items[row]
                return col.toString(record.value(col.fieldName()), record)
            if role == Qt.StatusTipRole:
                col = self._cols[column]
                record = self._items[row]
                return col.toStatusTip(record.value(col.fieldName()), record)
            if role == Qt.TextAlignmentRole:
                col = self._cols[column]
                return col.alignment()
            if role == Qt.CheckStateRole:
                col = self._cols[column]
                record = self._items[row]
                return col.toCheckState(record.value(col.fieldName()), record)
            if role == Qt.ForegroundRole:
                col = self._cols[column]
                record = self._items[row]
                return col.getForegroundColor(record.value(col.fieldName()), record)
        return QVariant()


    def setData(self, index, value, role=Qt.EditRole):
        row = index.row()
        if row > 4:
            return False
        result = CInDocTableModel.setData(self, index, value, role)
        return result


    def removeRows(self, row, count, parentIndex = QModelIndex()):
        if 0 <= row and row+count <= len(self._items):
            self.beginRemoveRows(parentIndex, row, row+count-1)
            del self._items[row:row+count]
            self.endRemoveRows()
            self.saveItems()
            return True
        else:
            return False


    def removeRow(self, row, parentIndex = QModelIndex()):
        return self.removeRows(row, 1, parentIndex)


    def loadItems(self, masterId):
        if not self.action or (self.action.getRecord() and not forceRef(self.action.getRecord().value('id'))):
            self.saveItems()
        else:
            if self.eventEditor and self.action:
                items = {}
                for property in self.action._propertiesById.itervalues():
                    propertyType = property.type()
                    shortName = trim(propertyType.shortName)
                    value = property._value
                    propertyValue = propertyType.convertQVariantToPyValue(value) if type(value) == QVariant else value
                    if isinstance(propertyValue, basestring) or propertyValue.__class__.__name__ == 'QString':
                        propertyValue = trim(propertyValue)
                    if propertyValue:
                        item = items.get(shortName, [])
                        if propertyValue and (isinstance(propertyValue, basestring) or propertyValue.__class__.__name__ == 'QString') and len(propertyValue) > 1:
                            propertyValue = propertyValue.split(u',')
                            item.extend(propertyValue)
                        else:
                            item.append(propertyValue)
                        items[shortName] = item
                if items:
                    self._items = []
                    for idx in xrange(5):
                        begDate = self.eventEditor.getPropertyValue(items, u'НВНБ:СоГвВБ:ДП:%s'%(forceString(idx+1)), QDate)
                        endDate = self.eventEditor.getPropertyValue(items, u'НВНБ:СоГвВБ:ДВ:%s'%(forceString(idx+1)), QDate)
                        order = self.eventEditor.getPropertyValue(items, u'НВНБ:СоГвВБ:П:%s'%(forceString(idx+1)), unicode)
                        org_id = self.eventEditor.getPropertyValue(items, u'НВНБ:СоГвВБ:МО:%s'%(forceString(idx+1)), int)
                        MKB = self.eventEditor.getPropertyValue(items, u'НВНБ:СоГвВБ:Д:%s'%(forceString(idx+1)), unicode)
                        if begDate or endDate or order or org_id or MKB:
                            item = self.getEmptyRecord()
                            item.setValue('begDate', toVariant(begDate))
                            item.setValue('endDate', toVariant(endDate))
                            item.setValue('order', toVariant(order))
                            item.setValue('org_id', toVariant(org_id))
                            item.setValue('MKB', toVariant(MKB))
                            self._items.append(item)
        self.reset()


    def saveItems(self):
        if self.eventEditor and self.eventEditor.action:
            for idx, record in enumerate(self._items):
                self.eventEditor.setProperty(QVariant(forceDate(record.value('begDate'))), u'НВНБ:СоГвВБ:ДП:%s'%(forceString(idx+1)))
                self.eventEditor.setProperty(QVariant(forceDate(record.value('endDate'))), u'НВНБ:СоГвВБ:ДВ:%s'%(forceString(idx+1)))
                self.eventEditor.setProperty(QVariant(forceStringEx(record.value('order'))), u'НВНБ:СоГвВБ:П:%s'%(forceString(idx+1)))
                self.eventEditor.setProperty(QVariant(forceRef(record.value('org_id'))), u'НВНБ:СоГвВБ:МО:%s'%(forceString(idx+1)))
                self.eventEditor.setProperty(QVariant(forceStringEx(record.value('MKB'))), u'НВНБ:СоГвВБ:Д:%s'%(forceString(idx+1)))
            rowCount = self.realRowCount()
            if rowCount < 5:
                noRows = 5 - rowCount
                idx = rowCount + 1
                while noRows > 0:
                    self.delProperty(u'НВНБ:СоГвВБ:ДП:%s'%(forceString(idx)))
                    self.delProperty(u'НВНБ:СоГвВБ:ДВ:%s'%(forceString(idx)))
                    self.delProperty(u'НВНБ:СоГвВБ:П:%s'%(forceString(idx)))
                    self.delProperty(u'НВНБ:СоГвВБ:МО:%s'%(forceString(idx)))
                    self.delProperty(u'НВНБ:СоГвВБ:Д:%s'%(forceString(idx)))
                    idx += 1
                    noRows -= 1
            self.action = self.eventEditor.action


    def delProperty(self, shortName):
        shortName = trim(shortName)
        if self.eventEditor.action and self.action and shortName:
            for propertyTypeName, property in self.action._propertiesByName.items():
                propertyType = property.type()
                if shortName == trim(propertyType.shortName):
                    del self.eventEditor.action[propertyType.name]


class CPreviousPregnancyModel(CInDocTableModel):
    class CActionPropertyLocCInDocTableCol(CInDocTableCol):
        def __init__(self, title, fieldName, fieldNameCol, width, **params):
            CInDocTableCol.__init__(self, title, fieldName, width, **params)
            self.fieldNameCol = fieldNameCol
            self.cache = {}

        def toString(self, val, record):
            actionId = forceRef(val)
            if actionId:
                if self.cache.has_key(actionId):
                    action = self.cache[actionId]
                else:
                    action = CAction.getActionById(actionId)
                    if action:
                        self.cache[actionId] = action
                if action:
                    value = forceString(action.getPropertyByShortName(self.fieldNameCol).getValueScalar())
                    return toVariant(value)
            return QVariant()

        def invalidateRecordsCache(self):
            self.cache = {}
            
    class CActionPropertyTreeLocCInDocTableCol(CActionPropertyLocCInDocTableCol):
        def __init__(self, title, fieldName, fieldNameCol, width, treeParentCol, treeChildCol, treeFullTextCol, **params):
            CInDocTableCol.__init__(self, title, fieldName, width, **params)
            self.fieldNameCol = fieldNameCol
            self.actionCache = {}
            self.valueCache = {}
            self.treeParentCol = treeParentCol
            self.treeChildCol = treeChildCol
            self.treeFullTextCol = treeFullTextCol


        def toString(self, val, record):
            actionId = forceRef(val)
            if not actionId:
                return QVariant()

            action = None
            if self.actionCache.has_key(actionId):
                action = self.actionCache[actionId]
            else:
                action = CAction.getActionById(actionId)
                if action:
                    self.actionCache[actionId] = action

            if not action:
                return QVariant()

            rawVal = forceString(action.getPropertyByShortName(self.fieldNameCol).getValueScalar())
            if not rawVal:
                return QVariant()
            if self.valueCache.has_key(rawVal):
                return toVariant(self.valueCache[rawVal])

            try:
                domainTable = getattr(self, 'domainTable', None)
                if domainTable is None:
                    domainTable = '`v1.2.643.5.1.13.13.99.2.279`'

                if domainTable.replace('`', '').startswith('v1') or domainTable.replace('`', '').startswith('1'):
                    tableName = unicode(QtGui.qApp.db.db.databaseName()) + "." + domainTable
                else:
                    tableName = domainTable

                db = QtGui.qApp.db
                table = db.table(tableName)

                nameField = table.findField('name')
                nameField = 'name' if nameField else None

                parts = []
                currentId = rawVal
                seenCodes = set()

                if not self.treeParentCol or not self.treeChildCol:
                    translated = forceString(db.translate(forceString(unicode(QtGui.qApp.db.db.databaseName()) + '.' + domainTable), 'id', rawVal, 'name'))
                    self.valueCache[rawVal] = translated
                    return toVariant(translated)

                cols = [self.treeChildCol, self.treeParentCol]
                if nameField:
                    cols.insert(1, nameField)
                lookCol = 'id'
                while currentId:
                    records = db.getRecordList(table, cols, where=u'{}={}'.format(lookCol, currentId))
                    if not records:
                        break

                    record = records[0]
                    if nameField:
                        name = forceString(record.value(nameField))
                    else:
                        name = forceString(record.value(0))

                    parts.insert(0, name if name is not None else u'')
                    parentId = forceRef(record.value(self.treeParentCol))

                    if not self.treeFullTextCol:
                        break

                    if not parentId:
                        break

                    if parentId in seenCodes:
                        break
                    
                    seenCodes.add(parentId)
                    parentRecords = db.getRecordList(table, [self.treeChildCol], where=u"{}={}".format(self.treeChildCol, parentId))
                    if not parentRecords:
                        break
                    currentId = forceRef(parentRecords[0].value(self.treeChildCol))
                    lookCol = self.treeChildCol

                text = u': '.join([p for p in parts if p])
                self.valueCache[rawVal] = text
                return toVariant(text)
            except Exception:
                return QVariant()

        def invalidateRecordsCache(self):
            self.actionCache = {}
            self.valueCache = {}

    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'Action_ActionProperty', 'id', 'master_id', parent)
        self.treeParentCol = None
        self.treeChildCol = None
        self.treeFullTextCol = None
        domain = forceString(QtGui.qApp.db.translate(u'ActionPropertyType', u'shortName', u'СОП:ИПБ:И', u'valueDomain'))
        if domain and domain.lstrip().startswith('{'):
            obj = json.loads(domain, object_pairs_hook=OrderedDict)
            self.treeParentCol = obj.get(u'parent', None)
            self.treeChildCol = obj.get(u'child', None)
            self.treeFullTextCol = obj.get(u'fullText', None)
        self.addHiddenCol('action_id')
        self.addHiddenCol('actionProperty_id')
        self.addCol(self.CActionPropertyLocCInDocTableCol(u'Год', 'action_id', u'СОП:ИПБ:Г', 3)).setReadOnly()
        self.addCol(self.CActionPropertyLocCInDocTableCol(u'Наступила', 'action_id', u'СОП:ИПБ:Н', 3)).setReadOnly()
        self.addCol(self.CActionPropertyLocCInDocTableCol(u'Программа ВРТ', 'action_id', u'СОП:ИПБ:ВРТ', 3)).setReadOnly()
        self.addCol(self.CActionPropertyTreeLocCInDocTableCol(u'Исход', 'action_id', u'СОП:ИПБ:И', 3, self.treeParentCol, self.treeChildCol, self.treeFullTextCol)).setReadOnly()
        self.addCol(self.CActionPropertyLocCInDocTableCol(u'Дата исхода', 'action_id', u'СОП:ИПБ:ДР', 3)).setReadOnly()
        self.addCol(self.CActionPropertyLocCInDocTableCol(u'Срок беременности (нед)', 'action_id', u'СОП:ИПБ:СБ', 3)).setReadOnly()
        self.addCol(self.CActionPropertyLocCInDocTableCol(u'Вид операции', 'action_id', u'СОП:ИПБ:ВО', 3)).setReadOnly()
        self.addCol(self.CActionPropertyLocCInDocTableCol(u'Число родившихся', 'action_id', u'СОП:ИПБ:ЧР', 3)).setReadOnly()
        self.addCol(self.CActionPropertyLocCInDocTableCol(u'Осложнения', 'action_id', u'СОП:ИПБ:О', 3)).setReadOnly()
        self.setEnableAppendLine(False)
        self.readOnly = False
        self.action = None
        self.eventEditor = None
    
    
    def invalidateRecordsCache(self):
        for col in self.cols():
            if isinstance(col, self.CActionPropertyLocCInDocTableCol):
                col.invalidateRecordsCache()


    def getEmptyRecord(self):
        result = QtGui.qApp.db.table('Action_ActionProperty').newRecord()
        return result


    def getBasicAdditional(self, actionId):
        additional = 0
        if actionId:
            record = self.getItemToActionId(actionId)
            additional = forceInt(record.value('additional')) if record else 0
        return additional


    def addItem(self, item):
        self._items.append(item)


    def getItemToActionId(self, findActionId):
        if findActionId:
            for idx, record in enumerate(self._items):
                actionId = forceRef(record.value('action_id'))
                if actionId == findActionId:
                    return record
        return None


    def getRowToActionId(self, findActionId):
        if findActionId:
            for row, record in enumerate(self._items):
                actionId = forceRef(record.value('action_id'))
                if actionId == findActionId:
                    return row
        return -1


    def getActionIdToRow(self, findRow):
        for row, record in enumerate(self._items):
            if findRow == row:
                return forceRef(record.value('action_id'))
        return None


    def getActionIdList(self):
        actionIdList = []
        for idx, record in enumerate(self._items):
            actionId = forceRef(record.value('action_id'))
            if actionId and actionId not in actionIdList:
                actionIdList.append(actionId)
        return actionIdList


    def getPropertyIdList(self):
        propertyIdList = []
        for idx, record in enumerate(self._items):
            propertyId = forceRef(record.value('actionProperty_id'))
            if propertyId and propertyId not in propertyIdList:
                propertyIdList.append(propertyId)
        return propertyIdList


    def setEventEditor(self, eventEditor):
        self.eventEditor = eventEditor


    def setAction(self, action):
        self.action = action


    def removeRows(self, row, count, parentIndex = QModelIndex()):
        if 0<=row and row+count<=len(self._items):
            self.beginRemoveRows(parentIndex, row, row+count-1)
            actionId = forceRef(self._items[row].value('action_id'))
            del self._items[row:row+count]
            self.endRemoveRows()
            return actionId
        else:
            return False


    def removeRow(self, row, parentIndex = QModelIndex()):
        result = self.removeRows(row, 1, parentIndex)
        QObject.parent(self).deletedPregnancyRetrospectTable()
        return result


    def setReadOnly(self, value=True):
        self.readOnly = value


    def flags(self, index):
        if self.readOnly:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        column = index.column()
        flags = self._cols[column].flags()
        if self.cellReadOnly(index):
            flags = flags & (~Qt.ItemIsEditable) & (~Qt.ItemIsUserCheckable)
        return flags


    def emitRowsChanged(self, begRow, endRow):
        CInDocTableModel.emitRowsChanged(self, begRow, endRow)
        for idx, record in enumerate(self._items):
            record.setValue(self._idxFieldName, toVariant(idx))


    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.CheckStateRole:
            column = index.column()
            row = index.row()
            state = value.toInt()[0]
            if row >= 0 and row < len(self._items):
                record = self._items[row]
                col = self._cols[column]
                record.setValue(col.fieldName(), QVariant(0 if state == Qt.Unchecked else 2))
                self.emitCellChanged(row, column)
                return True
        return CInDocTableModel.setData(self, index, value, role)


    def loadItems(self, masterId):
        self._items = []
        if masterId:
            db = QtGui.qApp.db
            cols = []
            for col in self._cols:
                if not col.external():
                    cols.append(col.fieldName())
            cols.append(self._idFieldName)
            cols.append(self._masterIdFieldName)
            if self._idxFieldName:
                cols.append(self._idxFieldName)
            for col in self._hiddenCols:
                cols.append(col)
            table = self._table
            filter = [table[self._masterIdFieldName].eq(masterId),
                      table['actionProperty_id'].isNull()
                      ]
            if self._filter:
                filter.append(self._filter)
            if table.hasField('deleted'):
                filter.append(table['deleted'].eq(0))
            if self._idxFieldName:
                order = [self._idxFieldName, self._idFieldName]
            else:
                order = [self._idFieldName]
            self._items = db.getRecordList(table, '*', filter, order)
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
            for item in self._items:
                item.aboutChildrenProperties = CAboutChildrenPropertiesRegistry()
                item.aboutChildrenProperties.load(forceRef(item.value('master_id')), forceRef(item.value('action_id')))
        self.reset()


    def saveItems(self, masterId):
        if masterId and self._items is not None:
            aboutChildrenPropertiesIdList = []
            db = QtGui.qApp.db
            table = self._table
            masterId = toVariant(masterId)
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
                self.saveDependence(idx, id)
                aboutChildrenPropertiesIdList.extend(record.aboutChildrenProperties.save(forceRef(record.value('master_id'))))
            filter = [table[masterIdFieldName].eq(masterId),
                      'NOT ('+table[idFieldName].inlist(idList)+')']
            if aboutChildrenPropertiesIdList:
                filter.append(table[idFieldName].notInlist(aboutChildrenPropertiesIdList))
            if self._filter:
                filter.append(self._filter)
            db.deleteRecordSimple(table, filter)


class CPregnancyRetrospectModel(CTableModel):
    class CEnableCol(CBoolCol):
        def __init__(self, title, fields, defaultWidth, selector):
            CBoolCol.__init__(self, title, fields, defaultWidth)
            self.selector = selector

        def checked(self, values):
            id = forceRef(values[0])
            if self.selector.isSelected(id):
                return CBoolCol.valChecked
            else:
                return CBoolCol.valUnchecked

    
    class CActionPropertyLocCCol(CCol):
        def __init__(self, title, fields, fieldNameCol, defaultWidth):
            CCol.__init__(self, title, fields, defaultWidth, 'l')
            self.fieldNameCol = fieldNameCol
            self.cache = {}

        def format(self, values):
            actionId = forceRef(values[0])
            if actionId:
                if self.cache.has_key(actionId):
                    action = self.cache[actionId]
                else:
                    action = CAction.getActionById(actionId)
                    if action:
                        self.cache[actionId] = action
                if action:
                    value = forceString(action.getPropertyByShortName(self.fieldNameCol).getValueScalar())
                    return toVariant(value)
            return CCol.invalid

        def invalidateRecordsCache(self):
            self.cache = {}
            
    class CActionPropertyTreeLocCCol(CCol):
        def __init__(self, title, fields, fieldNameCol, defaultWidth, treeParentCol, treeChildCol, treeFullTextCol):
            CCol.__init__(self, title, fields, defaultWidth, 'l')
            self.fieldNameCol = fieldNameCol
            self.actionCache = {}
            self.valueCache = {}
            self.treeParentCol = treeParentCol
            self.treeChildCol = treeChildCol
            self.treeFullTextCol = treeFullTextCol

        def format(self, values):
            actionId = forceRef(values[0])
            if not actionId:
                return QVariant()

            action = None
            if self.actionCache.has_key(actionId):
                action = self.actionCache[actionId]
            else:
                action = CAction.getActionById(actionId)
                if action:
                    self.actionCache[actionId] = action

            if not action:
                return QVariant()

            rawVal = forceString(action.getPropertyByShortName(self.fieldNameCol).getValueScalar())
            if not rawVal:
                return QVariant()
            if self.valueCache.has_key(rawVal):
                return toVariant(self.valueCache[rawVal])

            try:
                domainTable = getattr(self, 'domainTable', None)
                if domainTable is None:
                    domainTable = '`v1.2.643.5.1.13.13.99.2.279`'

                if domainTable.replace('`', '').startswith('v1') or domainTable.replace('`', '').startswith('1'):
                    tableName = unicode(QtGui.qApp.db.db.databaseName()) + "." + domainTable
                else:
                    tableName = domainTable

                db = QtGui.qApp.db
                table = db.table(tableName)

                nameField = table.findField('name')
                nameField = 'name' if nameField else None

                parts = []
                currentId = rawVal
                seenCodes = set()

                if not self.treeParentCol or not self.treeChildCol:
                    translated = forceString(db.translate(forceString(unicode(QtGui.qApp.db.db.databaseName()) + '.' + domainTable), 'id', rawVal, 'name'))
                    self.valueCache[rawVal] = translated
                    return toVariant(translated)

                cols = [self.treeChildCol, self.treeParentCol]
                if nameField:
                    cols.insert(1, nameField)
                lookCol = 'id'
                while currentId:
                    records = db.getRecordList(table, cols, where=u'{}={}'.format(lookCol, currentId))
                    if not records:
                        break

                    record = records[0]
                    if nameField:
                        name = forceString(record.value(nameField))
                    else:
                        name = forceString(record.value(0))

                    parts.insert(0, name if name is not None else u'')
                    parentId = forceRef(record.value(self.treeParentCol))

                    if not self.treeFullTextCol:
                        break

                    if not parentId:
                        break

                    if parentId in seenCodes:
                        break
                    
                    seenCodes.add(parentId)
                    parentRecords = db.getRecordList(table, [self.treeChildCol], where=u"{}={}".format(self.treeChildCol, parentId))
                    if not parentRecords:
                        break
                    currentId = forceRef(parentRecords[0].value(self.treeChildCol))
                    lookCol = self.treeChildCol

                text = u': '.join([p for p in parts if p])
                self.valueCache[rawVal] = text
                return toVariant(text)
            except Exception:
                return QVariant()
            

        def invalidateRecordsCache(self):
            self.actionCache = {}
            self.valueCache = {}


    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self.enableIdList = []
        self.actionsPropertiesRegistry = {}
        self.includeItems = {}
        self.treeParentCol = None
        self.treeChildCol = None
        self.treeFullTextCol = None
        domain = forceString(QtGui.qApp.db.translate(u'ActionPropertyType', u'shortName', u'СОП:ИПБ:И', u'valueDomain'))
        if domain and domain.lstrip().startswith('{'):
            obj = json.loads(domain, object_pairs_hook=OrderedDict)
            self.treeParentCol = obj.get(u'parent', None)
            self.treeChildCol = obj.get(u'child', None)
            self.treeFullTextCol = obj.get(u'fullText', None)
        self.addColumn(CPregnancyRetrospectModel.CEnableCol(u'Выбрать', ['id'], 5, self))
        self.addColumn(self.CActionPropertyLocCCol(u'Год', ['id'], u'СОП:ИПБ:Г', 3))
        self.addColumn(self.CActionPropertyLocCCol(u'Наступила', ['id'], u'СОП:ИПБ:Н', 3))
        self.addColumn(self.CActionPropertyLocCCol(u'Программа ВРТ', ['id'], u'СОП:ИПБ:ВРТ', 3))
        self.addColumn(self.CActionPropertyTreeLocCCol(u'Исход', ['id'], u'СОП:ИПБ:И', 3, self.treeParentCol, self.treeChildCol, self.treeFullTextCol))
        self.addColumn(self.CActionPropertyLocCCol(u'Дата исхода', ['id'], u'СОП:ИПБ:ДР', 3))
        self.addColumn(self.CActionPropertyLocCCol(u'Срок беременности (нед)', ['id'], u'СОП:ИПБ:СБ', 3))
        self.addColumn(self.CActionPropertyLocCCol(u'Вид операции', ['id'], u'СОП:ИПБ:ВО', 3))
        self.addColumn(self.CActionPropertyLocCCol(u'Число родившихся', ['id'], u'СОП:ИПБ:ЧР', 3))
        self.addColumn(self.CActionPropertyLocCCol(u'Осложнения', ['id'], u'СОП:ИПБ:О', 3))
        self.addColumn(CCol(u'Тип действия', ['actionType_id'], 1, 'l', defaultHidden = True))
        self.setTable('Action')
        self.basicAdditionalDict = {}
        self.eventId = None
        self.eventIdDict = {}
            

    def setEventId(self, eventId):
        self.eventId = eventId


    def setEventIdDict(self, eventIdDict):
        self.eventIdDict = eventIdDict


    def flags(self, index):
        result = CTableModel.flags(self, index)
        if index.column() == 0:
            result |= Qt.ItemIsUserCheckable
        return result


    def getBasicAdditional(self, actionId):
        additional = 0
        if actionId:
            record = self.getRecordById(actionId)
            additional = forceInt(record.value('additional')) if record else 0
        return additional


    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        column = index.column()
        row    = index.row()
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
            if row >= 0 and row < len(self._idList):
                actionId = forceRef(self._idList[row])
                if self.eventId == self.eventIdDict.get(actionId, None):
                    result = QtGui.QFont()
                    result.setBold(True)
                    return QVariant(result)
        return QVariant()


    def setData(self, index, value, role=Qt.EditRole):
        row = index.row()
        column = index.column()
        id = self._idList[row]
        if role == Qt.CheckStateRole and column == 0:
            id = self._idList[row]
            if id:
                self.setSelected(id, forceInt(value) == Qt.Checked)
                self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index, index)
            return True
        return CTableModel.setData(self, index, value, role)


    def setSelected(self, id, value):
        present = self.isSelected(id)
        if value:
            if not present:
                self.enableIdList.append(id)
        else:
            if present:
                self.enableIdList.remove(id)


    def isSelected(self, id):
        return id in self.enableIdList


    def getSelectedIdList(self):
        return self.enableIdList


class CAboutChildrenPropertiesRegistry:
    def __init__(self):
        self.items = []


    def getEmptyRecordEx(self, masterId, actionId, actionProperyId):
        db = QtGui.qApp.db
        table = db.table('Action_ActionProperty')
        newRecord = table.newRecord()
        newRecord.setValue('id', toVariant(None))
        newRecord.setValue('master_id', toVariant(masterId))
        newRecord.setValue('action_id', toVariant(actionId))
        newRecord.setValue('actionProperty_id', toVariant(actionProperyId))
        return newRecord


    def addItem(self, masterId, actionId, actionProperyId):
        record = self.getEmptyRecordEx(masterId, actionId, actionProperyId)
        self.items.append(record)


    def loadEx(self, masterId, actionId, actionProperyId):
        self.items = []
        record = self.getEmptyRecordEx(masterId, actionId, actionProperyId)
        if record:
            self.items = [record]
    
    
    def loadPrevAction(self, prevActionMasterId, masterId, actionId):
        self.items = []
        db = QtGui.qApp.db
        table = db.table('Action_ActionProperty')
        prevRecords = db.getRecordList(table, '*', [table['master_id'].eq(prevActionMasterId), table['action_id'].eq(actionId), table['deleted'].eq(0), table['actionProperty_id'].isNotNull()], order = u'Action_ActionProperty.idx, Action_ActionProperty.id')
        for record in prevRecords:
            actionId = forceRef(record.value('action_id'))
            actionProperyId = forceRef(record.value('actionProperty_id'))
            additional = forceInt(record.value('additional'))
            newRecord = self.getEmptyRecordEx(masterId, actionId, actionProperyId)
            newRecord.setValue('additional', toVariant(additional))
            self.items.append(newRecord)
        return self.items


    def load(self, masterId, actionId):
        db = QtGui.qApp.db
        table = db.table('Action_ActionProperty')
        self.items = db.getRecordList(table, '*', [table['master_id'].eq(masterId), table['action_id'].eq(actionId), table['deleted'].eq(0), table['actionProperty_id'].isNotNull()], order = u'Action_ActionProperty.idx, Action_ActionProperty.id')
    
    
    def loadAll(self, actionId):
        db = QtGui.qApp.db
        table = db.table('Action_ActionProperty')
        self.items = db.getRecordList(table, '*', [table['action_id'].eq(actionId), table['deleted'].eq(0), table['actionProperty_id'].isNotNull()], order = u'Action_ActionProperty.idx, Action_ActionProperty.id')
        

    def save(self, masterId):
        db = QtGui.qApp.db
        table = db.table('Action_ActionProperty')
        idList = []
        for idx, record in enumerate(self.items):
            record.setValue('idx', toVariant(idx))
            record.setValue('master_id', toVariant(masterId))
            id = db.insertOrUpdate(table, record)
            idList.append(id)
        return idList


    def getItems(self):
        return self.items


    def setItems(self, items):
        self.items = items


    def getActionIdList(self):
        actionIdList = []
        for idx, record in enumerate(self.items):
            actionId = forceRef(record.value('action_id'))
            if actionId and actionId not in actionIdList:
                actionIdList.append(actionId)
        return actionIdList


    def getPropertyIdList(self):
        propertyIdList = []
        for idx, record in enumerate(self.items):
            propertyId = forceRef(record.value('actionProperty_id'))
            if propertyId and propertyId not in propertyIdList:
                propertyIdList.append(propertyId)
        return propertyIdList


class CPreviousPregnancyChildrenModel(CActionPropertiesTableModel):
    def __init__(self, parent):
        CActionPropertiesTableModel.__init__(self, parent)
        self._items = []
        self.masterId = None


    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled


    def getPropertyTypeRow(self, actionPropertyId):
        for row, propertyType in enumerate(self.propertyTypeList):
            property = self.action.getPropertyById(propertyType.id)
            if property:
                record = property.getRecord()
                if record:
                    propertyId = forceRef(record.value('id'))
                    if propertyId == actionPropertyId:
                        return row
        return -1


    def removeRows(self, row, count, parentIndex = QModelIndex()):
        if 0<=row and row+count<=len(self._items):
            self.beginRemoveRows(parentIndex, row, row+count-1)
            actionId = forceRef(self._items[row].value('action_id'))
            actionPropertyId = forceRef(self._items[row].value('actionProperty_id'))
            del self._items[row:row+count]
            if actionPropertyId:
                propertyTypeRow = self.getPropertyTypeRow(actionPropertyId)
                if propertyTypeRow >= 0 and propertyTypeRow < len(self.propertyTypeList):
                    del self.propertyTypeList[propertyTypeRow:propertyTypeRow+count]
            self.endRemoveRows()
            return actionId
        else:
            return False


    def getCurrentActionId(self):
        return self.action.getId() if self.action else None


    def removeRow(self, row, parentIndex = QModelIndex()):
        return self.removeRows(row, 1, parentIndex)
    
    def getPropertyTypeList(self, actionType):
        return [actionType.getPropertyTypeByShortName(x) for x in [u'СОП:ИПБ:П:1', u'СОП:ИПБ:Р:1', u'СОП:ИПБ:МТ:1',
                                                                   u'СОП:ИПБ:П:2', u'СОП:ИПБ:Р:2', u'СОП:ИПБ:МТ:2',
                                                                   u'СОП:ИПБ:П:3', u'СОП:ИПБ:Р:3', u'СОП:ИПБ:МТ:3']]
    
    
    def setAction(self, action, clientId, clientSex=None, clientAge=None, eventTypeId=None):
        propertyTypeListEx = []
        self.propertyTypeList = []
        self.action = action
        self.clientId = clientId
        self.clientNormalParameters = self.getClientNormalParameters()
        self.eventTypeId = eventTypeId
        if self.action:
            propertyTypeList = [(actionType.id, actionType) for actionType in self.getPropertyTypeList(actionType = action.getType())]
            propertyTypeList.sort(key=lambda x: (x[1].idx, x[0]))
            self.propertyTypeList = [x[1] for x in propertyTypeList if x[1].applicable(clientSex, clientAge) and self.visible(x[1]) and x[1].typeName!='PacsImages']
        else:
            self.propertyTypeList = []
        for propertyType in self.propertyTypeList:
            propertyType.shownUp(action, clientId)
        self.updateActionStatusTip()
        self.reset()
            

    def setChildrenAction(self, action, clientId, clientSex=None, clientAge=None, eventTypeId=None):
        self.includeRows = {}
        self.action = action
        self.clientId = clientId
        self.clientNormalParameters = self.getClientNormalParameters()
        self.eventTypeId = eventTypeId
        items = CAboutChildrenPropertiesRegistry()
        if self.action:
            propertyTypeList = [(actionType.id, actionType) for actionType in self.getPropertyTypeList(actionType = action.getType())]
            propertyTypeList.sort(key=lambda x: (x[1].idx, x[0]))
            self.propertyTypeList = [x[1] for x in propertyTypeList if x[1].applicable(clientSex, clientAge) and self.visible(x[1]) and x[1].typeName!='PacsImages']
        else:
            self.propertyTypeList = []
        for propertyType in self.propertyTypeList:
            propertyType.shownUp(action, clientId)
        items.loadAll(forceRef(action.getRecord().value('id')))
        self.setItems(items.getItems())
        self.updateActionStatusTip()
        self.reset()


    def getActionIdList(self):
        actionIdList = []
        for idx, record in enumerate(self._items):
            actionId = forceRef(record.value('action_id'))
            if actionId and actionId not in actionIdList:
                actionIdList.append(actionId)
        return actionIdList


    def getPropertyIdList(self):
        propertyIdList = []
        for idx, record in enumerate(self._items):
            propertyId = forceRef(record.value('actionProperty_id'))
            if propertyId and propertyId not in propertyIdList:
                propertyIdList.append(propertyId)
        return propertyIdList


    def getEmptyRecordEx(self, masterId, actionId, actionProperyId):
        db = QtGui.qApp.db
        table = db.table('Action_ActionProperty')
        newRecord = table.newRecord()
        newRecord.setValue('id', toVariant(None))
        newRecord.setValue('master_id', toVariant(masterId))
        newRecord.setValue('action_id', toVariant(actionId))
        newRecord.setValue('actionProperty_id', toVariant(actionProperyId))
        return newRecord


    def addItem(self, item):
        self._items.append(item)


    def setItems(self, items):
        self._items = items


    def clearItems(self):
        self._items = []
        self.propertyTypeList = []
        self.reset()


    def getItems(self):
        return self._items


    def setMasterId(self, masterId):
        self._items = []
        self.masterId = masterId


    def loadItems(self, masterId):
        self._items = []
        self.masterId = masterId
        if not self.masterId:
            return
        db = QtGui.qApp.db
        table = db.table('Action_ActionProperty')
        cond = [table['master_id'].eq(masterId),
                table['actionProperty_id'].isNotNull(),
                table['deleted'].eq(0)
                ]
        self._items = db.getRecordList(table, u'*', cond)
        self.reset()


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

    
class CPregnancyInfoAddModel(CInDocTableModel):
    class CActionPropertyLocCInDocTableCol(CInDocTableCol):
        def __init__(self, title, fieldName, fieldNameCol, width, **params):
            CInDocTableCol.__init__(self, title, fieldName, width, **params)
            self.fieldNameCol = fieldNameCol
            self.actions = {}

        def toString(self, val, record):
            action = None
            value = None
            if self.actions.has_key(record):
                action = self.actions[record]
            if action:
                value = forceString(action.getPropertyByShortName(self.fieldNameCol).getValueScalar())
            if value:
                return toVariant(value)
            return QVariant()
        
        def setActions(self, actions):
            self.actions = actions
            
    class CActionPropertyTreeLocCInDocTableCol(CActionPropertyLocCInDocTableCol):
        def __init__(self, title, fieldName, fieldNameCol, width, treeParentCol, treeChildCol, treeFullTextCol, **params):
            CInDocTableCol.__init__(self, title, fieldName, width, **params)
            self.fieldNameCol = fieldNameCol
            self.actions = {}
            self.valueCache = {}
            self.treeParentCol = treeParentCol
            self.treeChildCol = treeChildCol
            self.treeFullTextCol = treeFullTextCol

        def toString(self, val, record):
            action = None
            if self.actions.has_key(record):
                action = self.actions[record]
                
            if not action:
                return QVariant()

            rawVal = forceString(action.getPropertyByShortName(self.fieldNameCol).getValueScalar())
            if not rawVal:
                return QVariant()
            if self.valueCache.has_key(rawVal):
                return toVariant(self.valueCache[rawVal])

            try:
                domainTable = getattr(self, 'domainTable', None)
                if domainTable is None:
                    domainTable = '`v1.2.643.5.1.13.13.99.2.279`'

                if domainTable.replace('`', '').startswith('v1') or domainTable.replace('`', '').startswith('1'):
                    tableName = unicode(QtGui.qApp.db.db.databaseName()) + "." + domainTable
                else:
                    tableName = domainTable

                db = QtGui.qApp.db
                table = db.table(tableName)

                nameField = table.findField('name')
                nameField = 'name' if nameField else None

                parts = []
                currentId = rawVal
                seenCodes = set()

                if not self.treeParentCol or not self.treeChildCol:
                    translated = forceString(db.translate(forceString(unicode(QtGui.qApp.db.db.databaseName()) + '.' + domainTable), 'id', rawVal, 'name'))
                    self.valueCache[rawVal] = translated
                    return toVariant(translated)

                cols = [self.treeChildCol, self.treeParentCol]
                if nameField:
                    cols.insert(1, nameField)
                lookCol = 'id'
                while currentId:
                    records = db.getRecordList(table, cols, where=u'{}={}'.format(lookCol, currentId))
                    if not records:
                        break

                    record = records[0]
                    if nameField:
                        name = forceString(record.value(nameField))
                    else:
                        name = forceString(record.value(0))

                    parts.insert(0, name if name is not None else u'')
                    parentId = forceRef(record.value(self.treeParentCol))

                    if not self.treeFullTextCol:
                        break

                    if not parentId:
                        break

                    if parentId in seenCodes:
                        break
                    
                    seenCodes.add(parentId)
                    parentRecords = db.getRecordList(table, [self.treeChildCol], where=u"{}={}".format(self.treeChildCol, parentId))
                    if not parentRecords:
                        break
                    currentId = forceRef(parentRecords[0].value(self.treeChildCol))
                    lookCol = self.treeChildCol

                text = u': '.join([p for p in parts if p])
                self.valueCache[rawVal] = text
                return toVariant(text)
            except Exception:
                return QVariant()
        
        def setActions(self, actions):
            self.actions = actions

        def invalidateRecordsCache(self):
            self.valueCache = {}
            
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'Action', 'id', 'event_id', parent)
        self.treeParentCol = None
        self.treeChildCol = None
        self.treeFullTextCol = None
        domain = forceString(QtGui.qApp.db.translate(u'ActionPropertyType', u'shortName', u'СОП:ИПБ:И', u'valueDomain'))
        if domain and domain.lstrip().startswith('{'):
            obj = json.loads(domain, object_pairs_hook=OrderedDict)
            self.treeParentCol = obj.get(u'parent', None)
            self.treeChildCol = obj.get(u'child', None)
            self.treeFullTextCol = obj.get(u'fullText', None)
        self.addCol(self.CActionPropertyLocCInDocTableCol(u'Год', 'id', u'СОП:ИПБ:Г', 3)).setReadOnly()
        self.addCol(self.CActionPropertyLocCInDocTableCol(u'Наступила', 'id', u'СОП:ИПБ:Н', 3)).setReadOnly()
        self.addCol(self.CActionPropertyLocCInDocTableCol(u'Программа ВРТ', 'id', u'СОП:ИПБ:ВРТ', 3)).setReadOnly()
        self.addCol(self.CActionPropertyTreeLocCInDocTableCol(u'Исход', 'id', u'СОП:ИПБ:И', 3, self.treeParentCol, self.treeChildCol, self.treeFullTextCol)).setReadOnly()
        self.addCol(self.CActionPropertyLocCInDocTableCol(u'Дата исхода', 'id', u'СОП:ИПБ:ДР', 3)).setReadOnly()
        self.addCol(self.CActionPropertyLocCInDocTableCol(u'Срок беременности (нед)', 'id', u'СОП:ИПБ:СБ', 3)).setReadOnly()
        self.addCol(self.CActionPropertyLocCInDocTableCol(u'Вид операции', 'id', u'СОП:ИПБ:ВО', 3)).setReadOnly()
        self.addCol(self.CActionPropertyLocCInDocTableCol(u'Число родившихся', 'id', u'СОП:ИПБ:ЧР', 3)).setReadOnly()
        self.addCol(self.CActionPropertyLocCInDocTableCol(u'Осложнения', 'id', u'СОП:ИПБ:О', 3)).setReadOnly()
        self.setEnableAppendLine(False)
        self.readOnly = False
        self.actions = {}


    def cellReadOnly(self, index):
        row = index.row()
        if 0 <= row < len(self._items):
            record, action = self._items[row]
            if record:
                actionTypeId = forceRef(record.value('actionType_id'))
                if actionTypeId:
                    return False
        return True
    
    
    def setAction(self, action, record):
        self.actions[record] = action
        for col in self.cols():
            if isinstance(col, self.CActionPropertyLocCInDocTableCol):
                col.setActions(self.actions)


    def setReadOnly(self, value):
        self.readOnly = value


    def flags(self, index):
        if self.readOnly:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        column = index.column()
        flags = self._cols[column].flags()
        if self.cellReadOnly(index):
            flags = flags & (~Qt.ItemIsEditable) & (~Qt.ItemIsUserCheckable)
        return flags


    def getEmptyRecord(self):
        result = QtGui.qApp.db.table('Action').newRecord()
        return result


    def setItems(self, items):
        recordNew, actionNew = items
        record, action = self._items
        if id(record) != id(recordNew):
            self._items = items
            self.reset()


    def insertRecord(self, row, record, action):
        self.beginInsertRows(QModelIndex(), row, row)
        self._items.insert(row, (record, action))
        self.endInsertRows()


    def addRecord(self, record, action):
        self.insertRecord(len(self._items), record, action)


    def setValue(self, row, fieldName, value):
        if 0 <= row < len(self._items):
            record, action = self._items[row]
            valueAsVariant = toVariant(value)
            if record.value(fieldName) != valueAsVariant:
                record.setValue(fieldName, valueAsVariant)
                self.emitValueChanged(row, fieldName)


    def value(self, row, fieldName):
        if 0 <= row < len(self._items):
            record, action = self._items[row]
            return record.value(fieldName)
        return None


    def sortData(self, column, ascending):
        pass


    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        row = index.row()
        if 0 <= row < len(self._items):
            if role == Qt.EditRole:
                col = self._cols[column]
                record, action = self._items[row]
                return record.value(col.fieldName())

            if role == Qt.DisplayRole:
                col = self._cols[column]
                record, action = self._items[row]
                return col.toString(record.value(col.fieldName()), record)

            if role == Qt.StatusTipRole:
                col = self._cols[column]
                record, action = self._items[row]
                return col.toStatusTip(record.value(col.fieldName()), record)

            if role == Qt.TextAlignmentRole:
                col = self._cols[column]
                return col.alignment()

            if role == Qt.CheckStateRole:
                col = self._cols[column]
                record, action = self._items[row]
                return col.toCheckState(record.value(col.fieldName()), record)

            if role == Qt.ForegroundRole:
                col = self._cols[column]
                record, action = self._items[row]
                return col.getForegroundColor(record.value(col.fieldName()), record)

        return QVariant()


    def saveItems(self, masterId):
        if self._items is not None:
            masterId = toVariant(masterId)
            masterIdFieldName = self._masterIdFieldName
            idFieldName = self._idFieldName
            for idx, (record, action) in enumerate(self._items):
                action.getRecord().setValue(masterIdFieldName, masterId)
                if self._idxFieldName:
                    action.getRecord().setValue(self._idxFieldName, toVariant(idx))
                id = action.save(forceRef(masterId))
                action.getRecord().setValue(idFieldName, toVariant(id))

