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

from PyQt4            import QtGui
from PyQt4.QtCore     import Qt, QAbstractItemModel, QAbstractListModel, QAbstractTableModel, QModelIndex, QSize, QVariant

from library.database import decorateString
from library.Utils    import forceInt, forceString, toVariant

from KLADR.Utils import prefixLen, fixLevel, checkIsActualSTREET, forceBit

tblKLADR  = 'kladr.KLADR'
tblSTREET = 'kladr.STREET'
tblDOMA   = 'kladr.DOMA'

class CKladrTreeItem(object):
    def __init__(self, code, name, status, level, index, parent, model):
        self._model  = model
        self._parent = parent
        self._code   = code
        self._name   = name
        self._status = status
        self._level  = fixLevel(code, level)
        self._index  = index
        self._items  = None
        self._itemsCount = None
        self._stmtCount = u'SELECT COUNT(CODE) FROM %s WHERE parent=\'%s\' AND RIGHT(CODE,2)=\'00\''
        self._stmtQ = u'SELECT CODE, NAME, SOCR, STATUS FROM %s WHERE parent=\'%s\' AND RIGHT(CODE,2)=\'00\' ORDER BY NAME, SOCR, CODE'
        self._stmtCode = u'SELECT parent FROM %s WHERE CODE LIKE \'%s%%\' LIMIT 1'



    def child(self, row):
        if self._items is None:
            self._items = self.loadChildren()
            self._itemsCount = len(self._items)
        if 0 <= row < self._itemsCount:
            return self._items[row]
        else:
#            print 'bad row %d from %d' % (row, self._itemsCount)
            return None

    def items(self):
        if self._items is None:
            self._items = self.loadChildren()
        return self._items


    def childCount(self):
        if self._itemsCount is None:
            self._itemsCount = self.countChildren()
        return self._itemsCount


    def columnCount(self):
        return 1


    def data(self, column):
        if column == 0:
            return QVariant(self._name)
        elif column == 1:
            return QVariant(self._code)
        elif column == 2:
            return QVariant(self.getPath())


    def flags(self):
        if ( self.childCount() > 0 and
             (self._status == 0 or self._status == 4)
             and not self._model.areaSelectable ):
            return Qt.ItemIsEnabled
        else:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable


    def parent(self):
        return self._parent


    def row(self):
        if self._parent:
            return self._parent._items.index(self)
        return 0


    def countChildren(self):
        result = 0
        if self._level < 4:
            pl = prefixLen(self._level)
            prefix = self._code[:pl]
            stmt   = self._stmtCount % (tblKLADR, prefix)
            query = QtGui.qApp.db.query(stmt)
###            print stmt
            if query.next():
                record = query.record()
                result = forceInt(record.value(0))
        return result


    def loadChildren(self):
        result = []
        if self._level < 4:
            pl = prefixLen(self._level)
            prefix = self._code[:pl]
            stmt   = self._stmtQ % (tblKLADR, prefix)
            query = QtGui.qApp.db.query(stmt)
###            print stmt
            i = 0
            while query.next():
                record = query.record()
                code   = forceString(record.value('CODE'))
                name   = forceString(record.value('NAME'))
                status = forceInt(record.value('STATUS'))
                socr   = forceString(record.value('SOCR'))
                # возможно, что правильнее анализировать ОКАТО:
                # "4" в третьем разряде или "5"|"6" в шестом.
                if status == 0 and (socr == u'г' or socr == u'пгт'):
                    status = 1
                item = CKladrTreeItem(code, name+' '+socr, status, self._level+1, i, self, self._model)
                item._stmtCount = self._stmtCount
                item._stmtQ = self._stmtQ
                item._stmtCode = self._stmtCode
                result.append(item)
                i += 1
        return result


    def getPath(self):
        path = []
        fox = self
        while fox._parent:
            path.insert(0, fox._name)
            if fox._status == 2:
                break
            fox = fox._parent
        return ', '.join(path)


    def findCode(self, code):
        shortCode = code[:11]
        stmt   = self._stmtCode % (tblKLADR, shortCode)
        query = QtGui.qApp.db.query(stmt)
        if query.next():
            record = query.record()
            parentCode =  forceString(record.value('parent')).ljust(11, '0')
            if parentCode == code or parentCode == '0'*11:
                parent = self
            else:
                parent = self.findCode(parentCode)
            n = parent.childCount()
            if n > 0:
                for i in xrange(n):
                    child = parent.child(i)
                    if child._code[:11] == shortCode:
                        return child
        return self


    def prefix(self):
        len = prefixLen(self._level)
        return self._code[:len]


    def keyboardSearch(self, search):
        search = search.lower().replace(u'ё', u'е')
        h = self.childCount()-1
        if h:
            l = 0
            while 0<=l<=h:
                m = (l+h)/2
                c = cmp(self.child(m)._name.lower().replace(u'ё', u'е'), search)
                if c<0:
                    l = m+1
                elif c>0:
                    h = m-1
                else:
                    return m
            return min(l, self.childCount()-1)
        else:
            return -1


class CKladrRootTreeItem(CKladrTreeItem):
    def __init__(self, model):
        CKladrTreeItem.__init__(self, '', '-', 0, 0, 0, None, model)

    def flags(self):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable


class CKladrTreeModel(QAbstractItemModel):
    def __init__(self, parent=None):
        QAbstractItemModel.__init__(self, parent)
        self._rootItem = CKladrRootTreeItem(self)
        self.areaSelectable = False
        self.isAllSelectable = False


    def getRootItem(self):
        return self._rootItem


    def setAllSelectable(self, val):
        self.isAllSelectable = val


    def columnCount(self, parent=None):
        return 1


    def data(self, index, role):
        if not index.isValid():
            return QVariant()

        if role != Qt.DisplayRole:
            return QVariant()

        item = index.internalPointer()
        return QVariant(item.data(index.column()))


    def flags(self, index):
        if not index.isValid():
            return 0
        item = index.internalPointer()
        if self.isAllSelectable:
            return item.flags() | Qt.ItemIsSelectable
        return item.flags()


    def headerData(self, section, orientation, role):
        return QVariant()


    def index(self, row, column, parent):
        if not parent or not parent.isValid():
            return self.createIndex(row, column, self.getRootItem())
        else:
            parentItem = parent.internalPointer()

        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QModelIndex()


    def parent(self, index):
        if not index.isValid():
            return QModelIndex()

        childItem = index.internalPointer()
        parentItem = childItem.parent()

        if parentItem is None:
            return QModelIndex()

        return self.createIndex(parentItem.row(), 0, parentItem)


    def rowCount(self, parent):
        if parent and parent.isValid():
            parentItem = parent.internalPointer()
            return parentItem.childCount()
        else:
            return 1


    def findCode(self, code):
        item = self.getRootItem().findCode(code)
        return self.createIndex(item._index, 0, item)


    def code(self, index):
        item = index.internalPointer()
        return item._code


    def getChildrenCodeList(self, code):
        def setChildrenColdeList(result, item):
            result.append(item._code)
            for item in item.items():
                setChildrenColdeList(result, item)
        result = []
        if code:
            index = self.findCode(code)
            if index and index.isValid():
                item = index.internalPointer()
                setChildrenColdeList(result, item)
        return result


    def keyboardSearch(self, parentIndex, search):
        parentItem = parentIndex.internalPointer() if parentIndex else None
        if not parentItem:
            parentItem = self.getRootItem()
        row = parentItem.keyboardSearch(search)
        return self.index(row, 0, parentIndex)


gKladrTreeModel = None
gAllSelectableKladrTreeModel = None


def getKladrTreeModel():
    global gKladrTreeModel
    if gKladrTreeModel is None:
        gKladrTreeModel = CKladrTreeModel(None)
    return gKladrTreeModel


def getAllSelectableKladrTreeModel():
    global gAllSelectableKladrTreeModel
    if gAllSelectableKladrTreeModel is None:
        gAllSelectableKladrTreeModel = CKladrTreeModel(None)
        gAllSelectableKladrTreeModel.setAllSelectable(True)
    return gAllSelectableKladrTreeModel


def getCityName(code):
    model = getKladrTreeModel()
    index = model.findCode(code)
    if index is not None:
        item = index.internalPointer()
        return item.getPath()
    else:
        return '{%s}' % code


def getExactCityName(code):
    model = getKladrTreeModel()
    index = model.findCode(code)
    if index is not None:
        item = index.internalPointer()
        return item._name
    else:
        return '{%s}' % code


def getMainRegionName(code):
    model = getKladrTreeModel()
    index = model.findCode(code)
    if index is not None:
        item = index.internalPointer()
        while item._parent and not isinstance(item._parent, CKladrRootTreeItem):
            item = item._parent
        return item._name
    else:
        return '{%s}' % code


def getRegionName(code):
    model = getKladrTreeModel()
    index = model.findCode(code[:5].ljust(11, '0'))
    if index is not None:
        item = index.internalPointer()
        return item._name
#        return item.getPath()
    else:
        return '{%s}' % code


def getOKATO(KLADRCode, KLADRStreetCode, number):
    db = QtGui.qApp.db
    stmt = 'SELECT `kladr`.`getOKATO`(%s, %s, %s)' % (
                decorateString(KLADRCode),
                decorateString(KLADRStreetCode),
                decorateString(number))
    try:
        query = db.query(stmt)
        if query.next():
            return forceString(query.record().value(0))
    except:
        pass
    return ''


def getDistrictName(KLADRCode, KLADRStreetCode, number):
    db = QtGui.qApp.db
    stmt = 'SELECT kladr.getDistrict(%s, %s, %s)' % (
                decorateString(KLADRCode),
                decorateString(KLADRStreetCode),
                decorateString(number))
    try:
        query = db.query(stmt)
        if query.next():
            return forceString(query.record().value(0))
    except:
        pass
    return ''


class CKLADRSearchModel(QAbstractTableModel):
    def __init__(self, parent):
        QAbstractListModel.__init__(self, parent)
        self.codes = []
        self.names = []
        self.rootCode = ''
        self.searchString = ''


    def columnCount(self, parent = None):
        return 1


    def rowCount(self, parent = None):
        return len(self.codes)


    def setFilter(self, rootCode, searchString):
        if self.rootCode != rootCode or self.searchString != searchString:
            db = QtGui.qApp.db
            table = db.table(tblKLADR)
            cond = ['RIGHT(CODE,2)=\'00\'']
            if rootCode:
                cond.append(table['CODE'].like(rootCode+'%'))
            if searchString:
                cond.append(table['NAME'].like(searchString+'%'))
            stmt = db.selectStmt(table,
                    'CODE, getTownName(CODE) AS NAMEEX',
                    cond,
                    'NAME, SOCR, CODE',
                    limit=500)
            self.codes = []
            self.names = []
            query = db.query(stmt)
            while query.next():
                record = query.record()
                self.codes.append(forceString(record.value(0)))
                self.names.append(forceString(record.value(1)))
            self.rootCode = rootCode
            self.searchString = searchString
            self.reset()


#    def headerData(self, section, orientation, role):
#        if role == Qt.DisplayRole:
#            return QVariant(u'Населённые пункты')
#        return QVariant()


    def data(self, index, role):
        if not index.isValid() or not self.names:
            return QVariant()
        elif role == Qt.DisplayRole or role == Qt.EditRole:
            row = index.row()
            return toVariant(self.names[row])
#        elif role == Qt.SizeHintRole:
#            return self.sizeHint
        return QVariant()


    def code(self, index):
        if self.codes and 0<=index<len(self.codes):
            return self.codes[index]
        else:
            return None


class CKLADRStreetSearchModel(QAbstractTableModel):
    def __init__(self, parent):
        QAbstractListModel.__init__(self, parent)
        self.codes = []
        self.names = []
        self.cities = []
        self.searchString = ''


    def columnCount(self, parent = None):
        if QtGui.qApp.getKladrResearch():
            return 2
        return 1


    def rowCount(self, parent = None):
        return len(self.codes)


    def setFilter(self, searchString, prefix, okato):
        if self.searchString != searchString:
            db = QtGui.qApp.db
            table = db.table(tblSTREET)
            tableKLADR = db.table(tblKLADR)
            table = table.leftJoin(tableKLADR, 'kladr.KLADR.code = CONCAT(kladr.STREET.level4,\'00\')')
            cond = ['actuality = \'00\' AND kladr.KLADR.CODE is not null', 'kladr.STREET.IS_ACTUAL = 1']
            if searchString:
                cond.append(u' CONCAT(kladr.STREET.NAME, \' \', kladr.STREET.SOCR) like \'{}\''.format('%'+searchString+'%'))
            if prefix:
                prefix = prefix.rstrip('0') if len(prefix.rstrip('0'))>2 and QtGui.qApp.getKladrResearch() else prefix
                cond.append(table['level4'].like(prefix+'%'))
            if okato:
                cond.append(db.joinOr([
                                       table[okato].eq(''), 
                                       table['OCATD'].like('%'+okato+'%'),
                                       '''kladr.STREET.OCATD = '' AND EXISTS(SELECT 1
                                                             FROM kladr.DOMA
                                                             WHERE kladr.DOMA.level5 = kladr.STREET.level5
                                                               AND kladr.DOMA.OCATD LIKE '%(okato)s%%'

                                                            )'''.format(okato)]))
            stmt = db.selectStmt(table,
                    'kladr.STREET.CODE, CONCAT(kladr.STREET.NAME, \' \', kladr.STREET.SOCR) AS NAMEEX, CONCAT(kladr.KLADR.NAME, \' \', kladr.KLADR.SOCR) AS CITYEX',
                    cond,
                    'kladr.STREET.NAME, kladr.STREET.SOCR, kladr.STREET.CODE',
                    limit=500)
            self.codes = []
            self.names = []
            self.cities = []
            query = db.query(stmt)
            while query.next():
                record = query.record()
                self.codes.append(forceString(record.value(0)))
                self.names.append(forceString(record.value(1)))
                self.cities.append(forceString(record.value(2)))
            self.searchString = searchString
            self.reset()


    def data(self, index, role):
        if not index.isValid() or not self.names:
            return QVariant()
        elif role == Qt.DisplayRole or role == Qt.EditRole:
            row = index.row()
            if index.column() == 0:
                return toVariant(self.names[row])
            else:
                return toVariant(self.cities[row])
        return QVariant()


    def code(self, index):
        if self.codes and 0<=index<len(self.codes):
            return self.codes[index]
        else:
            return None


class CStreetList(object):
    def __init__(self):
        self.prefix = ''
        self.okato = ''
        self.nameCmb = ''
        self.codes = []
        self.names = []
        self.noActualCode = []
        self.isLoaded = False
        self.filteredList = []
        self.oldSearchString = ''


    def load(self, prefix, okato, nameCmb):
        if self.prefix != prefix or self.okato != okato or self.nameCmb != nameCmb:
            self.prefix = prefix.rstrip('0') if len(prefix.rstrip('0'))>2  and QtGui.qApp.getKladrResearch() else prefix
            self.okato = okato
            self.nameCmb = nameCmb
            self.codes = []
            self.names = []
            if self.prefix or self.okato:
                db = QtGui.qApp.db
                stmt = '''SELECT kladr.STREET.CODE, CONCAT(kladr.STREET.NAME, ' ', kladr.STREET.SOCR) AS NAME, CONCAT(k.NAME, ' ', k.SOCR) AS CITY
                FROM kladr.STREET
                left join kladr.KLADR as k on k.code = CONCAT(kladr.STREET.level4,'00')
                WHERE kladr.STREET.level4 like '%(prefix)s%%'
                  AND kladr.STREET.actuality = '00' AND k.code is not null
                  AND kladr.STREET.IS_ACTUAL = 1
                  AND ('%(okato)s'=''
                       OR kladr.STREET.OCATD LIKE '%(okato)s%%'
                       OR kladr.STREET.OCATD = '' AND EXISTS(SELECT 1
                                                             FROM kladr.DOMA
                                                             WHERE kladr.DOMA.level5 = kladr.STREET.level5
                                                               AND kladr.DOMA.OCATD LIKE '%(okato)s%%'

                                                            )
                      )
                ORDER BY kladr.STREET.NAME, kladr.STREET.SOCR, kladr.STREET.CODE;''' % \
                {
                    'prefix': self.prefix,
                    'okato' : self.okato
                }
                querySTREET = db.query(stmt)
                while querySTREET.next():
                    record = querySTREET.record()
                    
                    self.codes.append(forceString(record.value(0)))
                    if QtGui.qApp.getKladrResearch():
                        self.names.append(forceString(record.value(1))+u'  ['+forceString(record.value(2))+u']')
                    else:
                        self.names.append(forceString(record.value(1)))
        self.isLoaded = True

    def clearNoActualStreet(self):
        if self.noActualCode:
            for i in self.noActualCode:
                idx = self.codes.index(i)
                self.codes.pop(idx)
                self.names.pop(idx)
        self.noActualCode = []

    def addStreet(self, code):
        db = QtGui.qApp.db
        stmt = """
        select kladr.STREET.CODE, CONCAT(kladr.STREET.NAME, ' ', kladr.STREET.SOCR) AS NAME, CONCAT(k.NAME, ' ', k.SOCR) AS CITY, kladr.STREET.IS_ACTUAL as isactual
FROM kladr.STREET
left join kladr.KLADR as k on k.code = CONCAT(kladr.STREET.level4,'00')
	where kladr.STREET.CODE = '{0}'; """.format(code)

        querySTREET = db.query(stmt)
        while querySTREET.next():
            record = querySTREET.record()
            isActualCode = forceBit(record.value(2))

            if isActualCode is not True:
                self.noActualCode.append(forceString(record.value(0)))
                
            self.codes.append(forceString(record.value(0)))
            if QtGui.qApp.getKladrResearch():
                self.names.append(forceString(record.value(1)) + u'  [' + forceString(record.value(2)) + u']')
            else:
                self.names.append(forceString(record.value(1)))


    def getLen(self):
        return len(self.codes)


    def indexByCode(self, code):
        try:
            return self.codes.index(code)
        except:
            return -1


    def searchStreet(self, streetName):
        h = len(self.names)-1
        if h<0:
            return -1, ''

        if not streetName:
            return 0, ''
        
        # cделал контекстный поиск   
        if self.filteredList and self.oldSearchString == streetName[:-1]:
            self.filteredList = sorted([(name[0], name[1], name[1].lower().find(streetName.lower())) for name in self.filteredList if name[1].lower().find(streetName.lower()) > -1], key=lambda x: x[2])
        else:
            self.filteredList = sorted([(i, name, name.lower().find(streetName.lower())) for i, name in enumerate(self.names) if name.lower().find(streetName.lower()) > -1], key=lambda x: x[2])
            
        self.oldSearchString = streetName
        if self.filteredList:
            return self.filteredList, streetName
        else:
            return 0, ''
#            
#        # т.к. улицы отсортированы по алфавиту есть резон искать двоичным поиским
#        l = 0
#        h = len(self.names)-1
#        findName = streetName.lower()
#
#        while l<h:
#            m = (l+h)/2
#            name = self.names[m].lower()
#            if name>findName:
#                h = m
#            else:
#                l = m+1
#
#        name = self.names[l].lower()
#        for i in range(min(len(name), len(findName))):
#            if name[i] != findName[i]:
#                return l, findName[:i-1]
#        return l, findName[:min(len(name), len(findName))]


class CStreetListCache(object):
    __shared_map = {}

    def __init__(self):
        self.map = self.__shared_map

    def getList(self, prefix, okato, cmbName):
        fixedPrefix = prefix or ''
        fixedOkato  = okato or ''
        fixedCmbName = cmbName or ''
        result = self.map.setdefault((fixedPrefix, fixedOkato, cmbName), CStreetList())
        if not result.isLoaded:
            result.load(fixedPrefix, fixedOkato, fixedCmbName)
        return result


class CStreetModel(QAbstractItemModel):
    def __init__(self, parent):
        QAbstractListModel.__init__(self, parent)
        self.stringList = None
        h = parent.fontMetrics().height() if parent else 14
        self.sizeHint = QVariant(QSize(h,h))
        self.addNone = False
        self._prefix = ''
        self._okato  = ''
        self._cmbName = ''

    
    def setAllSelectable(self, val):
        self.isAllSelectable = val
    

    def columnCount(self, index=None):
        return 1

    
    def headerData(self, section, orientation, role):
        return QVariant()
    

    def rowCount(self, index):
        if self.stringList is None:
            return 0
        else:
            return self.stringList.getLen() + (1 if self.addNone else 0)


    def setAddNone(self, flag):
        if self.addNone != flag:
            self.addNone = flag
            if self.stringList:
                self.reset()


    def setPrefix(self, prefix):
        self._prefix = prefix
        self.stringList = CStreetListCache().getList(self._prefix, self._okato, self._cmbName)
        self.reset()


    def setOkato(self, okato):
        self._okato = okato
        self.stringList = CStreetListCache().getList(self._prefix, self._okato, self._cmbName)
        self.reset()

    
    def parent(self, index):
        return QModelIndex()
    
    
    def index(self, row, column, parent):
        return self.createIndex(row, column, parent.internalPointer())
    

    def data(self, index, role):
        if not index.isValid() or self.stringList is None:
            return QVariant()
        elif role == Qt.SizeHintRole:
            return self.sizeHint
        elif role != Qt.DisplayRole:
            return QVariant()
        row = index.row()
        if self.addNone:
            if row == 0:
                return toVariant(u'не задано')
            elif row <= len(self.stringList.names):
                return toVariant(self.stringList.names[row-1])
            else:
                return QVariant()
        return toVariant(self.stringList.names[row])


    def code(self, index):
        if self.addNone:
            index -= 1
        if self.stringList is not None and index >= 0 and index < len(self.stringList.codes):
            return self.stringList.codes[index]
        else:
            return None

    def codeList(self):
        return list(self.stringList.codes)

    def clearNoActualStreet(self):
        if self.stringList:
            self.stringList.clearNoActualStreet()


    def indexByCode(self, code):
        if self.stringList is not None:
            if self.addNone:
                if code:
                    idx = self.stringList.indexByCode(code) + 1
                    if idx == 0 and code != '00':
                        self.stringList.addStreet(code)
                        return self.stringList.indexByCode(code) + 1
                    else:
                        return self.stringList.indexByCode(code) + 1
                else:
                    return 0
            else:
                return self.stringList.indexByCode(code)
        else:
            return -1


    def searchStreet(self, searchString):
        index = -1
        if self.stringList and searchString:
            searchList, searchString = self.stringList.searchStreet(searchString)
            if isinstance(searchList, list):
                index = searchList[0][0]     
        else:
            searchList, searchString = -1, ''
        if self.addNone:
            index += 1          
        return self.createIndex(index, 0, 0), searchString, len(searchList) if isinstance(searchList, list) else 0


def getStreetNameParts(code):
    stmt = 'SELECT NAME, SOCR FROM %s WHERE code =\'%s\' LIMIT 1' %(tblSTREET, code)
    query = QtGui.qApp.db.query(stmt)
    if query.next():
        record = query.record()
        return forceString(record.value(0)), forceString(record.value(1))
    else:
        return '{%s}' % code, ''


def getStreetName(code):
    if code:
        return ' '.join(getStreetNameParts(code))
    else:
        return ''