# -*- coding: utf-8 -*-

from PyQt4         import QtGui, QtCore
from library.Utils import forceInt, forceString
from collections   import OrderedDict


class CTreeWidgetItemOrgStructure(QtGui.QTreeWidgetItem):
    def __init__(self, parent, title, objectName, isGroup=False):
        title = title.replace('&', '')
        QtGui.QTreeWidgetItem.__init__(self, parent, [title])
        self._objectName = objectName
        self._isGroup = isGroup

    @property
    def objectName(self):
        return self._objectName

    @property
    def isGroup(self):
        return self._isGroup or self.childCount() > 0


class CCheckBoxDelegate(QtGui.QStyledItemDelegate):
    def __init__(self, parent=None):
        QtGui.QStyledItemDelegate.__init__(self, parent)

    def editorEvent(self, event, model, option, index):
        if event.type() == QtCore.QEvent.MouseButtonPress:
            tree = self.parent()
            tree.setCurrentIndex(index)
            itemRect = option.rect
            checkboxRect = QtCore.QRect(itemRect.topLeft(), QtCore.QSize(20, itemRect.height()))
            currentState = index.data(QtCore.Qt.CheckStateRole)
            newState = QtCore.Qt.Unchecked if currentState == tree.Checked else tree.Checked
            model.setData(index, newState, QtCore.Qt.CheckStateRole)
            if not checkboxRect.contains(event.pos()):
                return True
        return False


class CCheckedTreeWidgetOrgStructure(QtGui.QTreeWidget):
    u"""Данный класс создаёт дерево с чекбоксами содержащее иерархию структуры организации с возможностью делать
    подразделение активным/неактивным.

    Можно поменять таблицу из которой подтягиваются данные, если таблица имеет вид id, code, parent_id.

    exceptionUnchecked: По умолчанию true, по умолчанию все отделения которые находятся в exceptionIds неактивны, а остальные активны. При выставлении false - наоборот.
    table: Название таблицы из БД.
    """

    Checked = QtCore.Qt.Checked
    Unchecked = QtCore.Qt.Unchecked

    def __init__(self, parent=None, exceptionUnchecked=True, table='OrgStructure'):
        QtGui.QTreeWidget.__init__(self, parent)
        self.setHeaderHidden(True)
        self.orgsParents = dict()
        self.orgsChildren = []
        self.db = QtGui.qApp.db
        self.tableOrgStructure = self.db.table(table)
        self.itemClicked.connect(self.on_itemClicked)
        self.setItemDelegate(CCheckBoxDelegate(self))
        self.reverseCheckState = exceptionUnchecked

    def setupTree(self, exceptionIds):
        if exceptionIds:
            checkedIds = [forceInt(checkedId) for checkedId in exceptionIds.toList()]
        else:
            checkedIds = []
        self.addAllItemsOrgStructure(checkedIds, reverseCheckState=self.reverseCheckState, groupCheckable=True)
        for num in range(len(self.orgsParents)):
            self.invisibleRootItem().child(num).sortChildren(0, QtCore.Qt.AscendingOrder)

    def addAllItemsOrgStructure(self, checkedNames, reverseCheckState=False, groupCheckable=False):
        recordParents = self.db.getRecordList(self.tableOrgStructure,
                                           [self.tableOrgStructure['id'], self.tableOrgStructure['code'], self.tableOrgStructure['parent_id']],
                                           [self.tableOrgStructure['deleted'].eq(0), self.tableOrgStructure['parent_id'].eq(None)])
        for item in recordParents:
            self.orgsParents[forceInt(item.value('id'))] = forceString(item.value('code'))

        recordChildren = self.db.getRecordList(self.tableOrgStructure,
                                        [self.tableOrgStructure['id'], self.tableOrgStructure['code'], self.tableOrgStructure['parent_id']],
                                        self.tableOrgStructure['deleted'].eq(0),
                                        order='OrgStructure.code')
        for rec in recordChildren:
            orgId, code, parent_id = forceInt(rec.value('id')), forceString(rec.value('code')), forceInt(rec.value('parent_id'))
            self.orgsChildren.append({parent_id: [code, orgId]})
        items = self.setStructure(self.orgsParents)

        self.addItemsFromOrgStructure(items, self.invisibleRootItem(), checkedNames, reverseCheckState, groupCheckable)

    def setStructure(self, orgsParent):
        items = OrderedDict()
        for record in orgsParent:
            name = orgsParent[record]
            children = self.getChild(record)
            if children:
                key = (record, name)
                items[key] = self.setStructure(children)
            else:
                key = (record, name)
                items[key] = None
        return items

    def getChild(self, key):
        result = dict()
        for child in self.orgsChildren:
            if key == child.keys()[0]:
                childKey = child.get(child.keys()[0])[1]
                result[childKey] = child.get(child.keys()[0])[0]
        return result

    def getChildren(self, item=None):
        result = []
        if item is None:
            item = self.invisibleRootItem()
        else:
            result.append(item)
        for i in xrange(item.childCount()):
            child = item.child(i)
            result.append(child)
            result.extend(self.getChildren(child))
        return result

    def addItemsFromOrgStructure(self, items, parent, checkedNames, reverseCheckState=False, groupCheckable=False):
        for element, submenu in items.iteritems():
            eid, name = element
            if submenu is None:
                item = CTreeWidgetItemOrgStructure(parent, name, eid, isGroup=False)
                if reverseCheckState:
                    checked = eid not in checkedNames
                else:
                    checked = eid in checkedNames
                item.setCheckState(0, self.Checked if checked else QtCore.Qt.Unchecked)
            else:
                item = CTreeWidgetItemOrgStructure(parent, name, eid, isGroup=True)
                self.addItemsFromOrgStructure(submenu, item, checkedNames, reverseCheckState, groupCheckable)
                if groupCheckable:
                    if reverseCheckState:
                        checked = eid not in checkedNames
                    else:
                        checked = eid in checkedNames
                    item.setCheckState(0, self.Checked if checked else QtCore.Qt.Unchecked)

    def on_itemClicked(self, item, column):
        checkState = item.checkState(0)

        for i in xrange(item.childCount()):
            child = item.child(i)
            child.setCheckState(0, checkState)
            self.on_itemClicked(child, column)

        parent = item.parent()
        while parent:
            if checkState == self.Checked:
                parent.setCheckState(0, checkState)
            parent = parent.parent()

        childOf = item.parent()
        while childOf:
            allUnchecked = True
            for i in xrange(childOf.childCount()):
                child = childOf.child(i)
                if child.checkState(0) == self.Checked:
                    allUnchecked = False
                    break
            if allUnchecked:
                childOf.setCheckState(0, QtCore.Qt.Unchecked)
                childOf = childOf.parent()
            else:
                break

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Space:
            item = self.currentItem()
            if item:
                item.setCheckState(0, self.Checked if item.checkState(0) == QtCore.Qt.Unchecked else QtCore.Qt.Unchecked)
                self.on_itemClicked(item, 0)
        else:
            QtGui.QTreeWidget.keyPressEvent(self, event)

    def makeReportsToHideInsertValues(self):
        objectNames = []
        for item in self.getChildren():
            if item.checkState(0) == QtCore.Qt.Unchecked:
                if item.objectName:
                    objectNames.append(item.objectName)
        return objectNames
