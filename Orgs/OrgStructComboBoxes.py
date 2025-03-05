# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2015 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from random                import randint

from PyQt4                 import QtGui
from PyQt4.QtCore          import Qt, QDateTime, QVariant

from library.DbEntityCache import CDbEntityCache
from library.TreeComboBox  import CTreeComboBox, CTreeComboBoxGetIdSetIdMixin
from library.TreeModel     import CTreeItemWithId, CTreeModel
from library.Utils import forceBool, forceInt, forceRef, forceString, forceLong


class COrgStructureTreeItem(CTreeItemWithId):
    def __init__(self, parent, id, code, areaType, hasStocks, hasHospitalBeds=False):
        CTreeItemWithId.__init__(self, parent, code, id)
        self._areaType = areaType
        self._hasStocks = hasStocks
        self._hasHospitalBeds = hasHospitalBeds


    def areaType(self):
        return self._areaType


class COrgStructureTreePurpose:
    general = None
    areaSelector = 1
    storageSelector = 2
    hospitalBedsSelector = 3


class COrgStructureRootTreeItem(COrgStructureTreeItem):
    def __init__(self, orgId, orgStructureId, emptyRootName, purpose, filter=None):
        if filter and isinstance(filter, (list, tuple)):
            filter = QtGui.qApp.db.joinAnd(filter)
        if emptyRootName is None:
           emptyRootName = u'ЛПУ'
        COrgStructureTreeItem.__init__(self, None, # parent
                                             orgStructureId, # id
                                             emptyRootName,
                                             False, False, False)
        self.orgId = orgId
        self.emptyRootName = emptyRootName
        self.purpose = purpose
        self.filter = filter
        self.timestamp = None
        self.checkSum  = None


    def getCheckSum(self):
        return QtGui.qApp.db.rbChecksum('OrgStructure')


    def isObsolete(self):
        if self.timestamp and self.timestamp.secsTo(QDateTime.currentDateTime()) > randint(300, 600): ## magic
            return self.checkSum != self.getCheckSum()
        else:
            return False


    def loadChildren(self):
        self.timestamp = QDateTime.currentDateTime()
        self.checkSum = self.getCheckSum()

        db = QtGui.qApp.db
        table = db.table('OrgStructure')

        cond = [table['deleted'].eq(0),
                table['organisation_id'].eq(self.orgId)
               ]
        if self.filter:
            cond.append(self.filter)

        mapIdToNodes = { None:(self.emptyRootName, False, False, False) }
        mapParentIdToIdList = {}
        query = db.query(db.selectStmt(table, 'parent_id, id, code, areaType, hasStocks, hasHospitalBeds', where=cond, order='code'))
        while query.next():
            record = query.record()
            parentId = forceRef(record.value('parent_id'))
            id   = forceInt(record.value('id'))
            code = forceString(record.value('code'))
            areaType = forceInt(record.value('areaType'))
            hasStocks = forceBool(record.value('hasStocks'))
            hasHospitalBeds = forceBool(record.value('hasHospitalBeds'))
            mapIdToNodes[id] = code, areaType, hasStocks, hasHospitalBeds
            idList = mapParentIdToIdList.setdefault(parentId, [])
            idList.append(id)

        if self.purpose == COrgStructureTreePurpose.areaSelector:
            filter = lambda node: node[1]
        elif self.purpose == COrgStructureTreePurpose.storageSelector:
            filter = lambda node: node[2]
        elif self.purpose == COrgStructureTreePurpose.hospitalBedsSelector:
            filter = lambda node: node[3]
        else:
            filter = None

        if filter:
            self._filterNodes(mapIdToNodes, mapParentIdToIdList, self._id, filter, set())

        self._code, self._areaType, self._hasStocks, self._hasHospitalBeds = mapIdToNodes[self._id]
        if not mapParentIdToIdList.get(self._id):
            keys = mapParentIdToIdList.keys()
            if keys:
                filteredKeys = []
                for key in keys:
                    add = True
                    for k in keys:
                        if key in mapParentIdToIdList[k]:
                            add = False
                    if add:
                        filteredKeys.append(key)
                mapParentIdToIdList[self._id] = filteredKeys
                cond = [table['id'].inlist(keys)]
                query = db.query(db.selectStmt(table, 'parent_id, id, code, areaType, hasStocks, hasHospitalBeds', where=cond, order='code'))
                while query.next():
                    record = query.record()
                    id   = forceInt(record.value('id'))
                    code = forceString(record.value('code'))
                    areaType = forceInt(record.value('areaType'))
                    hasStocks = forceBool(record.value('hasStocks'))
                    hasHospitalBeds = forceBool(record.value('hasHospitalBeds'))
                    mapIdToNodes[id] = code, areaType, hasStocks, hasHospitalBeds
        self._generateItems(mapIdToNodes, mapParentIdToIdList, self, set())
        return self._items


    @staticmethod
    def _filterNodes(mapIdToNodes, mapParentIdToIdList, id, filter, visitedIdSet):
        if id not in visitedIdSet:
            visitedIdSet.add(id)
            idList = mapParentIdToIdList.get(id, None)
            if idList:
                idList = [ childId
                           for childId in idList
                           if COrgStructureRootTreeItem._filterNodes(mapIdToNodes, mapParentIdToIdList, childId, filter, visitedIdSet)
                         ]
                mapParentIdToIdList[id] = idList
            return bool(idList) or filter(mapIdToNodes[id])
        else:
            return False


    @staticmethod
    def _generateItems(mapIdToNodes, mapParentIdToIdList, item, visitedIdSet):
        id = item._id
        if id not in visitedIdSet:
            visitedIdSet.add(id)
            code, areaType, hasStocks, hasHospitalBeds = mapIdToNodes[id]
            idList = mapParentIdToIdList.get(id, None)
            item._items = []
            if idList:
                for childId in idList:
                    code, areaType, hasStocks, hasHospitalBeds = mapIdToNodes[childId]
                    childItem = COrgStructureTreeItem(item, childId, code, areaType, hasStocks, hasHospitalBeds)
                    item._items.append(childItem)
                    COrgStructureRootTreeItem._generateItems(mapIdToNodes, mapParentIdToIdList, childItem, visitedIdSet)


class COrgStructureRootTreeItemsCache(CDbEntityCache):
    mapKeyToRootItem = {}

    @classmethod
    def purge(cls):
        cls.mapKeyToRootItem.clear()


    @classmethod
    def getItem(cls, orgId, orgStructureId, emptyRootName, purpose, filter=None):
        key = orgId, orgStructureId, emptyRootName, purpose
        result = cls.mapKeyToRootItem.get(key, None)
        if not result or result.isObsolete():
            result = COrgStructureRootTreeItem(orgId, orgStructureId, emptyRootName, purpose, filter)
            cls.connect()
            cls.mapKeyToRootItem[key] = result
        return result


    @classmethod
    def getItemFromFilter(cls, orgId, orgStructureId, emptyRootName, purpose, filter=None):
        result = COrgStructureRootTreeItem(orgId, orgStructureId, emptyRootName, purpose, filter)
        cls.connect()
        return result


class COrgStructureModel(CTreeModel):
    def __init__(self, parent, orgId=None, orgStructureId=None, emptyRootName=None, purpose=None, filter=None, headerName=u'Структура ЛПУ'):
        self.orgId = orgId
        self.orgStructureId = orgStructureId
        self.emptyRootName = emptyRootName
        self.purpose = purpose
        self.filter = filter
        self.headerName = headerName
        self._isValidIdList = []
        CTreeModel.__init__(self, parent, None)


    def setIsValidIdList(self, isValidIdList):
        self._isValidIdList = isValidIdList


    def getRootItem(self):
        result = self._rootItem
        if not result:
            if self.filter:
                result = COrgStructureRootTreeItemsCache.getItemFromFilter(self.orgId, self.orgStructureId, self.emptyRootName, self.purpose, self.filter)
            else:
                result = COrgStructureRootTreeItemsCache.getItem(self.orgId, self.orgStructureId, self.emptyRootName, self.purpose, self.filter)
            self._rootItem = result
        return result


    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            return QVariant(self.headerName)
#            return QVariant(u'Структура ЛПУ')
        return QVariant()


    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags
        item = index.internalPointer()
        if not item:
            return Qt.NoItemFlags
        if self.readOnly:
            return Qt.ItemIsEnabled
        if item and self._isValidIdList and item._id not in self._isValidIdList:
            return Qt.NoItemFlags
        return item.flags()


    def setOrgId(self, orgId=None, orgStructureId=None, emptyRootName=None):
        if ( self.orgId != orgId
             or self.orgStructureId != orgStructureId
             or self.emptyRootName != emptyRootName
           ):
            self.orgId = orgId
            self.orgStructureId = orgStructureId
            self.emptyRootName = emptyRootName
            if self._rootItem:
                self._rootItem = None
#                self.reset()


    def setPurpose(self, purpose=None):
        if self.purpose != purpose:
            self.purpose = purpose
            if self._rootItem:
                self._rootItem = None
                self.reset()


    def setFilter(self, filter=None):
        if self.filter != filter:
            self.filter = filter
            if self._rootItem:
                self._rootItem = None
                self.reset()


    def areaType(self, index):
        if not index.isValid():
            return False
        item = index.internalPointer()
        return item.areaType()


class COrgStructureComboBox(CTreeComboBoxGetIdSetIdMixin, CTreeComboBox):
    def __init__(self, parent, emptyRootName=None, purpose=None, filter=None):
        CTreeComboBox.__init__(self, parent)
        self.SizeAdjustPolicy(QtGui.QComboBox.AdjustToMinimumContentsLength)
#        self.__searchString = ''
        self._model = COrgStructureModel(self,
                                         orgId=QtGui.qApp.currentOrgId(),
                                         orgStructureId=None,
                                         emptyRootName=emptyRootName,
                                         purpose=purpose,
                                         filter=filter)
        self.setModel(self._model)
        self.setExpandAll(False)
        self.readOnly = False


    def setReadOnly(self, value=False):
        self.readOnly = value
        self._model.setReadOnly(self.readOnly)


    def isReadOnly(self):
        return self.readOnly


    def showPopup(self):
        if not self.isReadOnly():
            CTreeComboBox.showPopup(self)


#    def showPopup(self):
#        if not self.isReadOnly():
#            self._createPopup()
#            pos = self.rect().bottomLeft()
#            pos = self.mapToGlobal(pos)
#            size = self._popup.sizeHint()
#            screen = QtGui.QApplication.desktop().availableGeometry(pos)
#            size.setWidth(screen.width())
#            pos.setX( max(min(pos.x(), screen.right()-size.width()), screen.left()) )
#            pos.setY( max(min(pos.y(), screen.bottom()-size.height()), screen.top()) )
#            self._popup.move(pos)
#            self._popup.resize(size)
#            self._popup.show()


    def setOrgId(self, orgId, orgStructureId=None, emptyRootName=None):
        currValue = self.value()
        self._model.setOrgId(orgId, orgStructureId, emptyRootName)
        self.setValue(currValue)


    def setIsValidIdList(self, isValidIdList):
        self._model.setIsValidIdList(isValidIdList)


    def setFilter(self, filter):
        self._model.setFilter(filter)


    def setPurpose(self, purpose):
        currValue = self.value()
        self._model.setPurpose(purpose)
        self.setValue(currValue)


    def getItemIdList(self):
        return self._model.getItemIdListById(self.value())


    def keyPressEvent(self, event):
        if self._model.isReadOnly():
            event.accept()
        else:
            CTreeComboBox.keyPressEvent(self, event)


    def eventFilter(self, watched, event):
        if self._model.isReadOnly():
            event.accept()
            return False
        return CTreeComboBox.eventFilter(self, watched, event)


class CAreaComboBox(COrgStructureComboBox):
    def __init__(self, parent):
        COrgStructureComboBox.__init__(self, parent, emptyRootName='-', purpose=COrgStructureTreePurpose.areaSelector)


class CStorageComboBox(COrgStructureComboBox):
    def __init__(self, parent):
        COrgStructureComboBox.__init__(self, parent, emptyRootName='-', purpose=COrgStructureTreePurpose.storageSelector)


class COrgStructureHospitalBedsComboBox(COrgStructureComboBox):
    def __init__(self, parent):
        COrgStructureComboBox.__init__(self, parent, emptyRootName='-', purpose=COrgStructureTreePurpose.hospitalBedsSelector)


class COrgStructureHospitalBedsComboBoxEx(COrgStructureComboBox):
    def __init__(self, parent):
        COrgStructureComboBox.__init__(self, parent, emptyRootName='-', purpose=COrgStructureTreePurpose.hospitalBedsSelector)
        self.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToMinimumContentsLength)
        

class COrgStructureNodeDisableComboBox(COrgStructureComboBox):
    def __init__(self, parent, emptyRootName=None, purpose=None, filter=None):
        COrgStructureComboBox.__init__(self, parent, emptyRootName, purpose, filter)
        self.orgStructureIdList = []


    def setOrgStructureIdList(self, orgStructureIdList):
        self.orgStructureIdList = orgStructureIdList
        self.setIsValidIdList(orgStructureIdList)

