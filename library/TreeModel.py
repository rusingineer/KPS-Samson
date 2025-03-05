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
from PyQt4.QtCore import Qt, SIGNAL, QAbstractItemModel, QMimeData, QModelIndex, QStringList, QVariant

from library.Utils import forceInt, forceRef, forceString, toVariant


class CTreeItem(object):
    def __init__(self, parent, name):
        self._parent = parent
        self._name   = name
        self._items  = None
        self._editable = False
        self._selectable = True


    def name(self):
        return self._name


    def child(self, row):
        items = self.items()
        if 0 <= row < len(items):
            return items[row]
        else:
            return None
#            print 'bad row %d from %d' % (row, len(items))


    def childCount(self):
        return len(self.items())


    def isLeaf(self):
        return not bool(self.items())


    def columnCount(self):
        return 1
    

    def setData(self, column, value):
        if column == 0:
            self._name = forceString(value)
            return True
        else:
            return False


    def data(self, column):
        if column == 0:
            return toVariant(self._name)
        else:
            return QVariant()


    def flags(self):
        result = Qt.ItemIsEnabled
        if self._selectable:
            result |= Qt.ItemIsSelectable
        if self._editable:
            result |= Qt.ItemIsEditable
        return result


    def parent(self):
        return self._parent


    def row(self):
        if self._parent:
            return self._parent._items.index(self)
        return 0


    def items(self):
        if self._items is None:
            self.cachedRecords = dict()
            self._items = self.loadChildren()
        return self._items


    def descendants(self, initLevel = 0): # все потомки и их уровни в порядке префиксного обхода в глубину
        result = [(self.name(), initLevel), ]
        for child in self.items():
            result += child.descendants(initLevel + 1)
        return result


    def loadChildren(self):
        assert False, 'pure virtual call'


    def findItem(self, predicat):
        if predicat(self):
            return self
        for item in self.items():
            result = item.findItem(predicat)
            if result:
                return result
        return None


    def removeChildren(self):
        self._items  = None



#class CRootTreeItem(CTreeItem):
#    def __init__(self):
#        CTreeItem.__init__(self, None, '-')


class CTreeItemWithId(CTreeItem):
    def __init__(self, parent, name, id):
        CTreeItem.__init__(self, parent, name)
        self._id = id


    def id(self):
        return self._id


    def findItemId(self, id):
        if self._id == id:
            return self
        for item in self.items():
            result = item.findItemId(id)
            if result:
                return result
        return None


    def appendItemIds(self, l):
        if self._id:
            l.append(self._id)
        for item in self.items():
            item.appendItemIds(l)


    def getItemIdList(self):
        result = []
        self.appendItemIds(result)
        return result


class CTreeModel(QAbstractItemModel):
    def __init__(self, parent, rootItem):
        QAbstractItemModel.__init__(self, parent)
        self._rootItem = rootItem
        self.rootItemVisible = True
        self.readOnly = False


    def setReadOnly(self, value=False):
        self.readOnly = value


    def isReadOnly(self):
        return self.readOnly


    def setRootItem(self, rootItem):
        self._rootItem = rootItem
        self.reset()


    def getRootItem(self):
        return self._rootItem


    def isRootIndex(self, index):
        if index.isValid():
            return index.internalPointer() == self.getRootItem()
        return False


    def setRootItemVisible(self, val):
        self.rootItemVisible = val
        self.reset()


    def columnCount(self, parent=None):
        return 1


    def index(self, row, column, parent = QModelIndex()):
        if parent and parent.isValid():
            parentItem = parent.internalPointer()
            childItem = parentItem.child(row)
            return self.createIndex(row, column, childItem)
        elif self.rootItemVisible:
            return self.createIndex(0, 0, self.getRootItem())
        else:
            parentItem = self.getRootItem()
            childItem = parentItem.child(row)
            return self.createIndex(row, column, childItem)


    def parent(self, index):
        if not index.isValid():
            return QModelIndex()
        childItem = index.internalPointer()
        return self.parentByItem(childItem)


    def parentByItem(self, childItem):
        parentItem = childItem.parent() if childItem and hasattr(childItem, '_parent') else None
        if not parentItem or (parentItem == self.getRootItem() and not self.rootItemVisible):
            return QModelIndex()
        return self.createIndex(parentItem.row(), 0, parentItem)


    def rowCount(self, parent):
        if parent and parent.isValid():
            parentItem = parent.internalPointer()
            return parentItem.childCount()
        elif self.rootItemVisible:
            return 1
        else:
            return self.getRootItem().childCount()


    def data(self, index, role):
        if index.isValid() and role in (Qt.DisplayRole, Qt.EditRole):
            item = index.internalPointer()
            if item:
                return item.data(index.column())
        return QVariant()
    

    def setData(self, index, value, role):
        if index.isValid() and role == Qt.EditRole:
            item = index.internalPointer()
            if item:
                return item.setData(index.column(), value)
        return False
    

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags
        item = index.internalPointer()
        if not item:
            return Qt.NoItemFlags
        if self.readOnly:
            return Qt.ItemIsEnabled
        return item.flags()


    def items(self):
        return self.getRootItem().descendants()


    def findItem(self, predicat):
        item = self.getRootItem().findItem(predicat)
        if item:
            return self.createIndex(item.row(), 0, item)
        else:
            return None


    def findItemId(self, id):
        item = self.getRootItem().findItemId(id)
        if item and (self.rootItemVisible or item != self.getRootItem()):
            return self.createIndex(item.row(), 0, item)
        else:
            return None


    def getItemById(self, id):
        return self.getRootItem().findItemId(id)

    def getItemByIdEx(self, id):
        return self.getItemById(id)

    def itemId(self, index):
        item = index.internalPointer()
        return item._id if item else None


    def getItemIdList(self, index):
        result = []
        item = index.internalPointer()
        if item:
            item.appendItemIds(result)
        return result


    def getItemIdListById(self, id):
        item = self.getItemById(id)
        if item:
            return item.getItemIdList()
        return []


    def isLeaf(self, index):
        if not index.isValid():
            return False
        item = index.internalPointer()
        return item.isLeaf()


    def updateItem(self, index):
        item = index.internalPointer()
        if item:
            item.update()


    def updateItemById(self, id):
        item = self.getRootItem().findItemId(id)
        if item:
            item.update()


class CDBTreeItem(CTreeItemWithId):
    def __init__(self, parent, name, id, model):
       CTreeItemWithId.__init__(self, parent, name, id)
       self.model = model


    def loadChildren(self):
        return self.model.loadChildrenItems(self)


    def update(self):
        if self._items is not None:
            newItems = self.loadChildren()
            if [ child._id for child in self._items ] == [ child._id for child in newItems ]:
                for i in xrange(len(self._items)):
                    if self._items[i]._name != newItems[i]._name:
                        self._items[i]._name = newItems[i]._name
                        self.model.dataChanged(self, i)
                    self._items[i].update()
            else:
                index = self.model.createIndex(self.row(), 0, self)
                if self._items:
                    self.model.beginRemoveRows(index, 0, len(self._items)-1)
                    self._items = []
                    self.model.endRemoveRows()
                if newItems:
                    self.model.beginInsertRows(index, 0, len(newItems)-1)
                    self._items = newItems
                    self.model.endInsertRows()


class CDBTreeModel(CTreeModel):
    def __init__(self, parent, tableName, idColName, groupColName, nameColName, order=None, filter=None):
        CTreeModel.__init__(self, parent, CDBTreeItem(None, u'все', None, self))
        self.tableName = tableName
        self.idColName    = idColName
        self.groupColName = groupColName
        self.nameColName  = nameColName
        self._filter      = filter
        self.order = order if order else nameColName
        self.leavesVisible = False
        self.cachedRecords = dict()

    def setFilter(self, filter):
        if self._filter != filter:
            self._filter = filter
            self.reset()


    def setLeavesVisible(self, value):
        if self.leavesVisible != value:
            self.leavesVisible = value
            self.reset()


    def setOrder(self, order):
        if self.order != order:
            self.order = order
            self.reset()


    def update(self):
        self.getRootItem().update()
        #self.reset()


    def loadChildrenItems(self, group):
        result = []
        if not self.cachedRecords:
            db = QtGui.qApp.db
            table = db.table(self.tableName)
            cond = []
            if self._filter:
                cond.append(self._filter)
            if table.hasField('deleted'):
                cond.append(table['deleted'].eq(0))
            if not self.leavesVisible:
                alias = table.alias(self.tableName+'2')
                cond.append(db.existsStmt(alias, alias[self.groupColName].eq(table[self.idColName])))
            recordList = db.getRecordList(table, [self.idColName, self.nameColName, self.groupColName], cond, self.order)

            for record in recordList:
                groupId = forceRef(record.value(2))
                if groupId is None:
                    groupId = -1
                self.cachedRecords.setdefault(groupId, []).append(record)
        groupId = group._id if group._id else -1
        records = self.cachedRecords.get(groupId, [])
        return self.getItemListByRecords(records, group)


    def getItemListByRecords(self, recordList, group):
        result = []
        for record in recordList:
            id   = forceRef(record.value(0))
            name = forceString(record.value(1))
            result.append(CDBTreeItem(group, name, id, self))
        return result


    def dataChanged(self, group, row):
        index = self.createIndex(row, 0, group._items[row])
        self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index, index)


class CDragDropDBTreeModel(CDBTreeModel):
    u""" Модель дерева с возможностью таскать листики с ветку на ветку"""
    __pyqtSignals__ = ('saveExpandedState()',
                       'restoreExpandedState()')

    def __init__(self, parent, tableName, idColName, groupColName, nameColName, order=None):
        CDBTreeModel.__init__(self, parent, tableName, idColName, groupColName, nameColName, order)
        self.mapItemToId = {}


    def getItemByIdEx(self, id):
        return self.mapItemToId.get(id, None)


    def getItemIdListById(self, id):
        item = self.getItem(id)
        result = []
        if item:
            item.appendItemIds(result)
        return result


    def getItem(self, id):
        item = self.getItemByIdEx(id)
        if not item:
            item = self.getItemById(id)
        return item


    def getItemListByRecords(self, recordList, group):
        result = []
        for record in recordList:
            id   = forceRef(record.value(0))
            name = forceString(record.value(1))
            item = CDBTreeItem(group, name, id, self)
            self.mapItemToId[id] = item
            result.append(item)
        return result


    def supportedDropActions(self):
        return Qt.CopyAction | Qt.MoveAction


    def flags(self, index):
        defaultFlags = CDBTreeModel.flags(self, index)

        if index.isValid():
            return Qt.ItemIsDragEnabled | \
                   Qt.ItemIsDropEnabled | defaultFlags
        else:
            return Qt.ItemIsDropEnabled | defaultFlags


    def mimeTypes(self):
        types = QStringList()
        # передаем id элементов дерева в текстовом виде
        types.append('text/plain')
        return types


    def mimeData(self, index):
        id = self.itemId(index[0])
        mimeData = QMimeData()
        mimeData.setText(forceString(id))
        return mimeData


    def dropMimeData(self, data, action, row, column, parentIndex):
        if action == Qt.IgnoreAction:
            return True

        if not data.hasText():
            return False

        dragId = forceRef(forceInt(data.text()))
        parentId = self.itemId(parentIndex)

        self.changeParent(dragId, parentId)
        self.emit(SIGNAL('dataChanged(QModelIndex,QModelIndex)'), parentIndex, parentIndex)
        return True


    def changeParent(self,  id,  parentId):
        u"""Меняем у записи id родителя на parentId"""

        # if parentId not in self.getItemIdListById(id):
        db = QtGui.qApp.db
        table = db.table(self.tableName)
        record = db.getRecord(table, [self.idColName, self.groupColName], id)

        if record:
            # при последующем вызове reset дерево свернется в корень,
            # поэтому сигналим о необходимости сохранить его вид
            self.emit(SIGNAL('saveExpandedState()'))
            record.setValue(self.groupColName, toVariant(parentId))
            db.updateRecord(table, record)
            self.reset()
            self.update()
            # сигналим о необходимости  восстановить вид дерева
            self.emit(SIGNAL('restoreExpandedState()'))

class CDBTreeItemWithClass(CDBTreeItem):
    def __init__(self, parent, name, id, className, model, isClass=False):
       CDBTreeItem.__init__(self, parent, name, id, model)
       self.className = className
       self.isClass = isClass


    def row(self):
        if self._parent and self in self._parent._items:
            return self._parent._items.index(self)
        return 0


class CDragDropDBTreeModelWithClassItems(CDragDropDBTreeModel):
    mapClassItemsSourceByExists = {}
    def __init__(self, parent, tableName, idColName, groupColName, nameColName, classColName, order=None, showInForm = None):
        CDragDropDBTreeModel.__init__(self, parent, tableName, idColName, groupColName, nameColName, order)
        self.classColName = classColName
        self.classItems = []
        self._classItemsSource = None
        self._availableItemIdList = None
        self.setRootItem(CDBTreeItemWithClass(None, u'Все', None, None, self, True))
        self.showInForm = showInForm


    def setShowInForm(self, showInForm):
        self.showInForm = showInForm


    def setAvailableItemIdList(self, idList):
        self._availableItemIdList = idList
        self.update()

    def setClassItems(self, items):
        self._classItemsSource = items
        rootItem = self.getRootItem()
        for name, val in items:
            self.classItems.append(CDBTreeItemWithClass(rootItem, name, None, val, self, True))

    def filterClassByExists(self, value):
        self.classItems = []
        if self._classItemsSource:
            if value:
                self.classItems = self._getClassItemsByExists()
            else:
                self.setClassItems(self._classItemsSource)
        self.reset()


    def _getClassItemsByExists(self):
        result = CDragDropDBTreeModelWithClassItems.mapClassItemsSourceByExists.get(self.tableName, None)
        if result is None:
            result = []
            for name, val in self._classItemsSource:
                if self._checkClassByExists(val):
                    result.append((name, val))
            CDragDropDBTreeModelWithClassItems.mapClassItemsSourceByExists[self.tableName] = tuple(result)

        rootItem = self.getRootItem()
        return [CDBTreeItemWithClass(rootItem, name, None, val, self, True) for name, val in result]


    def _checkClassByExists(self, _class):
        db = QtGui.qApp.db
        table = db.table(self.tableName)
        return bool(db.getCount(table, table['id'].name(), table['class'].eq(_class)))


    def loadChildrenItems(self, group):
        result = []
        if group == self.getRootItem():
            result = self.classItems
        else:
            db = QtGui.qApp.db
            table = db.table(self.tableName)
            cond = [ table[self.groupColName].eq(group._id) ]
            cond.append(table[self.classColName].eq(group.className))
            if self.showInForm:
                cond.append(table['showInForm'].eq(1))
            if table.hasField('deleted'):
                cond.append(table['deleted'].eq(0))
            if not self.leavesVisible:
                alias = table.alias(self.tableName+'2')
                cond.append(db.existsStmt(alias, alias[self.groupColName].eq(table[self.idColName])))
            for record in db.getRecordList(table, [self.idColName, self.nameColName], cond, self.order):
                id   = forceRef(record.value(0))
                if (self._availableItemIdList is not None) and (id not in self._availableItemIdList):
                    continue
                name = forceString(record.value(1))
                item = CDBTreeItemWithClass(group, name, id, group.className, self)
                self.mapItemToId[id] = item
                result.append(item)
        return result


    def itemClass(self, index):
        item = index.internalPointer()
        return item.className if item else None


    def flags(self, index):
        defaultFlags = CDBTreeModel.flags(self, index)
        item = index.internalPointer()
        if index.isValid() and not item.isClass:
            return Qt.ItemIsDragEnabled | \
                   Qt.ItemIsDropEnabled | defaultFlags
        else:
            return Qt.ItemIsDropEnabled | defaultFlags


    def dropMimeData(self, data, action, row, column, parentIndex):
        if action == Qt.IgnoreAction:
            return True

        if not data.hasText():
            return False

        dragId = forceRef(data.text())
        parentId = self.itemId(parentIndex)
        parentClass = self.itemClass(parentIndex)

        self.changeParent(dragId, parentId, parentClass)
        self.emit(SIGNAL('dataChanged(QModelIndex,QModelIndex)'), parentIndex, parentIndex)
        return True


    def changeParent(self,  id,  parentId, parentClass):
        # if parentId not in self.getItemIdListById(id):
        db = QtGui.qApp.db
        table = db.table(self.tableName)
        record = db.getRecord(table, [self.idColName, self.groupColName, self.classColName], id)
        if record:
            self.emit(SIGNAL('saveExpandedState()'))
            record.setValue(self.groupColName, toVariant(parentId))
            record.setValue(self.classColName, toVariant(parentClass))
            self.setClass(parentClass, id)
            db.updateRecord(table, record)
            self.reset()
            self.update()
            self.emit(SIGNAL('restoreExpandedState()'))


    def setClass(self, _class, itemId):
        db = QtGui.qApp.db
        table = db.table(self.tableName)
        idList = db.getDescendants(table, self.groupColName, itemId)
        if itemId in idList:
            idList.remove(itemId)
        if idList:
            expr = table[self.classColName].eq(_class)
            cond = table['id'].inlist(idList)
            stmt = 'UPDATE %s SET %s WHERE %s' % (self.tableName, expr, cond)
            db.query(stmt)
