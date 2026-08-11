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

import re
from collections              import namedtuple

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QAbstractItemModel, QDate, QModelIndex, QVariant

from library.AgeSelector      import checkAgeSelector, parseAgeSelector
from library.Calendar import wpFiveDays, wpSixDays, wpSevenDays
from library.crbcombobox import CRBComboBox
from library.database         import CTableRecordCache
from library.PreferencesMixin import CPreferencesMixin
from library.Series           import CBaseSeries, CDoubleSeries, CSeriesHolder
from library.TableModel       import ( CTableModel,
                                       CCol,
                                       CDateCol,
                                       CDesignationCol,
                                       CNumCol,
                                       CRefBookCol,
                                       CSumCol,
                                       CTextCol,
                                       CEnumCol
                                     )
from library.Utils            import ( calcAgeTuple,
                                       forceBool,
                                       forceDate,
                                       forceDouble,
                                       forceInt,
                                       forceRef,
                                       forceString,
                                       formatName,
                                       formatSex,
                                       getPref,
                                       quote,
                                       setPref,
                                       toVariant,
                                       firstMonthDay,
                                       lastMonthDay
                                     )

from Accounting.CCAlgorithm   import CCCAlgorithm
from Accounting.Tariff        import CTariff
from Events.ActionStatus      import CActionStatus
from Events.Utils             import CFinanceType, getExposed, getPayStatusMask

__all__ = ( 'getNextAccountNumber',
            'updateAccount',
            'updateAccounts',
            'beforeUpdateAccounts',
            'beforeUpdateAccount',
            'setEventPayStatus',
            'setEventVisitsPayStatus',
            'setVisitPayStatus',
            'setActionPayStatus',
            'setEventCsgPayStatus',
            'updateDocsPayStatus',
            'clearPayStatus',
            'canRemoveAccount',
            'getAccountExportFormat',
            'getStentOperationCount',

            'CContractTreeView',
            'CContractTreeModel',
            'CContractFindTreeModel',
            'CContractTreeItem',
            'CContractRootTreeItem',
            'CContractFindRootTreeItem',
            'CCoefficientTypeDescr',
            'CAccountsModel',
            'CAccountItemsModel',
            'CLocEventColumn',
            'CLocEventCodeColumn',
            'CLocClientColumn',
            'CLocClientBirthDateColumn',
            'CLocClientSexColumn',
            'CLocRKEYCol',
            'CLocFKEYCol',
            'CLocMKBColumn',

            'getContractDescr',
            'selectEvents',
            'selectVisitsByActionServices',
            'selectVisits',
            'selectActions',
            'selectCsgs',
            'selectHospitalBedActionProperties',
            'selectEventServicePairsForVisits',
            'selectReexposableEvents',
            'addTariffToDict',
            'sortTariffsInDict',
            'selectReexposableAccountItems',
            'getRefuseTypeId',
            'updateAccountTotals',
            'unpackExposeDiscipline',
            'packExposeDiscipline',
            'CAccountIdLineEdit',
            'roundMath',
          )


def getNextAccountNumber(contractNumber, counterId=None):
    if counterId:
        res = QtGui.qApp.getDocumentNumber(None, counterId)
    else:
        stmt = 'SELECT MAX(CAST(SUBSTR(number, %d) AS SIGNED)) AS seqNumber FROM Account WHERE number LIKE \'%s-%%\'' % (len(contractNumber)+2, contractNumber)       
        query = QtGui.qApp.db.query(stmt)
        if query.first():
            lastSeqNumber = forceInt(query.record().value('seqNumber'))
        else:
            lastSeqNumber = 0
        res = u'%s-%d' % (contractNumber, lastSeqNumber+1)
    return res


def updateAccount(accountId):
    QtGui.qApp.db.query('CALL updateAccount(%d);' % accountId)


def updateAccounts(accountIds):
    for accountId in accountIds:
        updateAccount(accountId)


def beforeUpdateAccount(accountId):
    QtGui.qApp.db.query('CALL beforeUpdateAccount(%d);' % accountId)


def beforeUpdateAccounts(accountIds):
    for accountId in accountIds:
        beforeUpdateAccount(accountId)


def setEventPayStatus(eventId, payStatusMask, bits):
    stmt = u'UPDATE Event SET payStatus = ((payStatus & ~%d) | %d) WHERE id=%d''' % \
           (payStatusMask, payStatusMask & bits, eventId)
    QtGui.qApp.db.query(stmt)


def setEventVisitsPayStatus(eventId, payStatusMask, bits):
    stmt = u'UPDATE Visit SET payStatus = ((payStatus & ~%d) | %d) WHERE event_id=%d''' % \
           (payStatusMask, payStatusMask & bits, eventId)
    QtGui.qApp.db.query(stmt)


def setVisitPayStatus(id, payStatusMask, bits):
    stmt = u'UPDATE Visit SET payStatus = ((payStatus & ~%d) | %d) WHERE id=%d''' % \
           (payStatusMask, payStatusMask & bits, id)
    QtGui.qApp.db.query(stmt)


def setActionPayStatus(id, payStatusMask, bits):
    stmt = u'UPDATE Action SET payStatus = ((payStatus & ~%d) | %d) WHERE id=%d''' % \
           (payStatusMask, payStatusMask & bits, id)
    QtGui.qApp.db.query(stmt)


def setEventCsgPayStatus(eventCsgId, payStatusMask, bits):
    stmt = u'UPDATE Event_CSG SET payStatus = ((payStatus & ~%d) | %d) WHERE id=%d''' % \
           (payStatusMask, payStatusMask & bits, eventCsgId)
    QtGui.qApp.db.query(stmt)


def updateDocsPayStatus(accountItem, payStatusMask, bits):
    actionId = forceRef(accountItem.value('action_id'))
    if actionId:
        setActionPayStatus(actionId, payStatusMask, bits)
        return

    visitId = forceRef(accountItem.value('visit_id'))
    if visitId:
        setVisitPayStatus(visitId, payStatusMask, bits)
        return

    eventId = forceRef(accountItem.value('event_id'))
    if eventId:
        setEventPayStatus(eventId, payStatusMask, bits)

    eventCsgId = forceRef(accountItem.value('eventCSG_id'))
    if eventCsgId:
        setEventCsgPayStatus(eventCsgId, payStatusMask, bits)


def clearPayStatus(accountId, accountItemIdList=[]):
    db = QtGui.qApp.db
    contractId = forceRef(db.translate('Account', 'id', accountId, 'contract_id'))
    financeId  = forceRef(db.translate('Contract', 'id', contractId,'finance_id'))
    payStatusMask = getPayStatusMask(financeId)
    table = db.table('Account_Item')
    cond = [ table['master_id'].eq(accountId) ]
    if accountItemIdList:
        cond.append(table['id'].inlist(accountItemIdList))
    cond = db.joinAnd(cond)
    stmt = u'''UPDATE Event, Account_Item
               SET Event.payStatus = (Event.payStatus & ~%s) |
                   IF(EXISTS (SELECT id FROM Account_Item AS AI WHERE AI.master_id != %d AND AI.event_id = Event.id AND AI.deleted = 0 AND AI.visit_id IS NULL AND AI.action_id IS NULL), %d, 0)
               WHERE %s AND Account_Item.event_id = Event.id AND Account_Item.deleted = 0 AND Account_Item.visit_id IS NULL AND Account_Item.action_id IS NULL''' \
           % (payStatusMask, accountId, getExposed(payStatusMask), cond)
    db.query(stmt)
    stmt = u'''UPDATE Action, Account_Item
               SET Action.payStatus = (Action.payStatus & ~%s) |
                   IF(EXISTS (SELECT id FROM Account_Item AS AI WHERE AI.master_id != %d AND AI.action_id = Action.id AND AI.deleted = 0), %d, 0)
               WHERE %s AND Account_Item.action_id = Action.id AND Account_Item.deleted = 0''' \
           % (payStatusMask, accountId, getExposed(payStatusMask), cond)
    db.query(stmt)
    stmt = u'''UPDATE Visit, Account_Item
               SET Visit.payStatus = (Visit.payStatus & ~%s) |
                   IF(EXISTS (SELECT id FROM Account_Item AS AI WHERE AI.master_id != %d AND AI.visit_id = Visit.id AND AI.deleted = 0), %d, 0)
               WHERE %s AND Account_Item.visit_id = Visit.id AND Account_Item.deleted = 0''' \
           % (payStatusMask, accountId, getExposed(payStatusMask), cond)
    db.query(stmt)

    stmt = u'''UPDATE Visit, Account_Item, Contract_Tariff
               SET Visit.payStatus = (Visit.payStatus & ~%s)
               WHERE %s AND Visit.event_id=Account_Item.event_id AND Account_Item.deleted = 0 AND Visit.service_id = Account_Item.service_id AND Contract_Tariff.id=Account_Item.tariff_id AND Contract_Tariff.tariffType=%d''' \
           % (payStatusMask, cond, CTariff.ttCoupleVisits)
    db.query(stmt)

    stmt = u'''UPDATE Event_CSG, Account_Item
               SET Event_CSG.payStatus = (Event_CSG.payStatus & ~%s) |
                   IF(EXISTS (SELECT id FROM Account_Item AS AI WHERE AI.master_id != %d AND AI.eventCSG_id = Event_CSG.id AND AI.deleted = 0), %d, 0)
               WHERE %s AND Account_Item.eventCSG_id = Event_CSG.id AND Account_Item.deleted = 0''' \
           % (payStatusMask, accountId, getExposed(payStatusMask), cond)
    db.query(stmt)


def canRemoveAccount(accountId):
    db = QtGui.qApp.db
    table = db.table('Account_Item')
    cond = []
    cond.append(table['master_id'].eq(accountId))
    cond.append(table['date'].isNotNull())
    cond.append(table['number'].ne(''))
    record = db.getRecordEx(table, 'COUNT(id)', cond)
    return record and forceInt(record.value(0)) == 0


def getAccountExportFormat(accountId):
    prog = u''
    db = QtGui.qApp.db
    formatId = forceRef(db.translate('Account', 'id', accountId, 'format_id'))
    if not formatId:
        contractId = forceRef(db.translate('Account', 'id', accountId, 'contract_id'))
        formatId = forceRef(db.translate('Contract', 'id', contractId, 'format_id'))
    if formatId:
        prog = forceString(db.translate('rbAccountExportFormat', 'id', formatId, 'prog'))
    return prog


def _getContractAttribute(accountId, attrCode):
    db = QtGui.qApp.db
    tableAccount  = db.table('Account')
    tableContract = db.table('Contract')
    tableContractAttribute = db.table('Contract_Attribute')
    tableAttributeType     = db.table('rbContractAttributeType')
    table = tableAccount
    table = table.innerJoin(tableContract, tableContract['id'].eq(tableAccount['contract_id']))
    table = table.innerJoin(tableContractAttribute, tableContractAttribute['master_id'].eq(tableContract['id']))
    table = table.innerJoin(tableAttributeType,     tableAttributeType['id'].eq(tableContractAttribute['attributeType_id']))

    record = db.getRecordEx(table,
                            tableContractAttribute['value'],
                            [ tableContractAttribute['deleted'].eq(0),
                              tableContractAttribute['begDate'].le(tableAccount['date']),
                              tableAttributeType['code'].eq(attrCode),
                              tableAccount['id'].eq(accountId)
                            ],
                            tableContractAttribute['begDate'].name()+' desc'
                           )
    if record:
        return record.value('value')
    else:
        return QVariant()


def getDoubleContractAttribute(accountId, attrCode):
    return forceDouble( _getContractAttribute(accountId, attrCode) )


def getIntContractAttribute(accountId, attrCode):
    return forceInt( _getContractAttribute(accountId, attrCode) )


class CContractTreeView(QtGui.QTreeView, CPreferencesMixin):
    def processPrefs(self,  model,  preferences,  load,  parent = QModelIndex(),  prefix = ''):
        for i in xrange(model.columnCount(parent)):
            for j in xrange(model.rowCount(parent)):
                index = model.index(j, i,  parent)
                if index.isValid():
                    prefix += index.internalPointer().name+'_'
                    if load:
                        self.setExpanded(index,  forceBool(getPref(preferences,
                            prefix+'col_'+str(i)+'_row_'+str(j), True)))
                    else:
                        setPref(preferences,
                            prefix+'col_'+str(i)+'_row_'+str(j),
                            QVariant(self.isExpanded(index)))
                if index.isValid():
                    self.processPrefs(model,  preferences,  load,  index, prefix)

        pref = QtGui.qApp.preferences
        props = pref.appPrefs
        expand = forceInt(props.get('treeContractsExpand',  QVariant()))
        if not expand:
            self.expandToDepth(0)
        elif expand == 1:
            self.expandAll()
        else:
            expandLevel = forceInt(props.get('treeContractsExpandLevel',  QVariant(1)))
            self.expandToDepth(expandLevel)


    def loadPreferences(self, preferences):
        model = self.model()

        if model and isinstance(model, CContractTreeModel):
            self.processPrefs(model,  preferences,  True)


    def savePreferences(self):
        preferences = {}
        model = self.model()

        if model and isinstance(model, CContractTreeModel):
            self.processPrefs(model,  preferences,  False)

        return preferences


class CContractTreeModel(QAbstractItemModel):
    def __init__(self, parent=None, financeTypeCodeList=None):
        QAbstractItemModel.__init__(self, parent)
        self.contracts = {}
        self._rootItem = CContractRootTreeItem(self.contracts, financeTypeCodeList)


    def items(self):
        return self.getRootItem().descendants()


    def getPathById(self, contractId):
        return self.getRootItem().getPathById(contractId)

    def getIdByPath(self, path):
        return self.getRootItem().getIdByPath(path)

    def getRootItem(self):
        return self._rootItem


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
        return item.flags()

#    def headerData(self, section, orientation, role):
#        return QVariant()

    def index(self, row, column, parent = QModelIndex()):
        if parent and parent.isValid():
            parentItem = parent.internalPointer()
            childItem = parentItem.child(row)
            return self.createIndex(row, column, childItem)
        else:
            return self.createIndex(0, 0, self.getRootItem())


    def parent(self, index):
        if not index.isValid():
            return QModelIndex()
        childItem = index.internalPointer()
        parentItem = childItem.parent
        if not parentItem:
            return QModelIndex()
        return self.createIndex(parentItem.row(), 0, parentItem)


    def rowCount(self, parent):
        if parent and parent.isValid():
            parentItem = parent.internalPointer()
            return parentItem.childCount()
        else:
            return 1


class CContractFindTreeModel(QAbstractItemModel):
    def __init__(self, parent=None, financeTypeCodeList=None, filter={}):
        QAbstractItemModel.__init__(self, parent)
        self.contracts = {}
        self.filter = filter
        self._rootItem = CContractFindRootTreeItem(self.contracts, financeTypeCodeList, self.filter)


    def getPathById(self, contractId):
        return self.getRootItem().getPathById(contractId)

    def getIdByPath(self, path):
        return self.getRootItem().getIdByPath(path)

    def getRootItem(self):
        return self._rootItem


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
        return item.flags()

#    def headerData(self, section, orientation, role):
#        return QVariant()

    def index(self, row, column, parent = QModelIndex()):
        if parent and parent.isValid():
            parentItem = parent.internalPointer()
            childItem = parentItem.child(row)
            return self.createIndex(row, column, childItem)
        else:
            return self.createIndex(0, 0, self.getRootItem())


    def parent(self, index):
        if not index.isValid():
            return QModelIndex()
        childItem = index.internalPointer()
        parentItem = childItem.parent
        if not parentItem:
            return QModelIndex()
        return self.createIndex(parentItem.row(), 0, parentItem)


    def rowCount(self, parent):
        if parent and parent.isValid():
            parentItem = parent.internalPointer()
            return parentItem.childCount()
        else:
            return 1


class CContractTreeItem(object):
    def __init__(self, name, parent):
        self.name = name
        self.items = []
        self.idList = []
        self.mapNameToItem = {}
        self.parent = parent

    def addItem(self, path, depth, contractId):
        self.idList.append(contractId)
        if depth<len(path):
            name = path[depth]
            if name in self.mapNameToItem:
                child = self.mapNameToItem[name]
            else:
                child = CContractTreeItem(name, self)
                self.items.append(child)
                self.mapNameToItem[name] = child
            child.addItem(path, depth+1, contractId)


    def descendants(self, initLevel = 0): # все потомки и их уровни в порядке префиксного обхода в глубину
        result = [(self.name, initLevel), ]
        for child in self.items:
            result += child.descendants(initLevel + 1)
        return result



    def child(self, row):
        return self.items[row]


    def childCount(self):
        return len(self.items)


    def columnCount(self):
        return 1


    def data(self, column):
        return QVariant(self.name)


    def flags(self):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable


    def row(self):
        if self.parent:
            return self.parent.items.index(self)
        return 0


class CContractRootTreeItem(CContractTreeItem):
    def __init__(self, contracts, financeTypeCodeList=None):
        CContractTreeItem.__init__(self, u'Все договоры', None)
        self._contractIdToPath = {}
        self._pathToContractId = {}
        db = QtGui.qApp.db
        table = db.table('Contract')
        cond = [table['recipient_id'].eq(QtGui.qApp.currentOrgId()),
                table['disableInAccounts'].eq(0),
                table['deleted'].eq(0)
                ]
        if financeTypeCodeList:
            cond.append(table['finance_id'].inlist([CFinanceType.getId(code) for code in financeTypeCodeList]))
        records = db.getRecordList(table,
                                   'id, finance_id, grouping, resolution, date, number',
                                   where=db.joinAnd(cond),
                                   order='finance_id, grouping, resolution, date, number, id')
        for record in records:
            contractId = forceRef(record.value('id'))
            contractName = forceString(record.value('number')) + u' от ' +forceString(record.value('date'))
            path = [ CFinanceType.getNameById(forceInt(record.value('finance_id'))),
                     forceString(record.value('grouping')),
                     forceString(record.value('resolution')),
                     contractName
                   ]
            self.addItem(path, 0, contractId)
            contracts[contractId] = contractName
            self._contractIdToPath[contractId] = path
            self._pathToContractId['\\'.join(path)] = contractId


    def getPathById(self, contractId):
        return self._contractIdToPath.get(contractId, '')


    def getIdByPath(self, path):
        return self._pathToContractId.get(path, None)


class CContractFindRootTreeItem(CContractTreeItem):
    def __init__(self, contracts, financeTypeCodeList=None, filter={}):
        CContractTreeItem.__init__(self, u'Все договоры', None)
        self._contractIdToPath = {}
        self._pathToContractId = {}
        self._mapFinanceName = {}
        self.filter = filter
        db = QtGui.qApp.db

        records = db.getRecordList('rbFinance', 'id, name')
        for record in records:
            financeId = forceString(record.value(0))
            financeName = forceString(record.value(1))
            self._mapFinanceName[financeId] = financeName

        tableContract = db.table('Contract')
        tableOrganisation = db.table('Organisation')
        tableOrganisationAccount = db.table('Organisation_Account')
        table = tableContract.leftJoin(tableOrganisation, tableOrganisation['id'].eq(tableContract['payer_id']))
        table = table.leftJoin(tableOrganisationAccount, tableOrganisation['id'].eq(tableOrganisationAccount['organisation_id']))
        cond = [tableOrganisation['deleted'].eq(0)]

        financeId = self.filter.get('financeId', None)
        payerId = self.filter.get('payerId', None)
        payerAccountId = self.filter.get('payerAccountId', None)
        number = self.filter.get('number', '')
        grouping = self.filter.get('grouping', '')
        resolution = self.filter.get('resolution', '')
        payerINN = self.filter.get('payerINN', '')
        payerOGRN = self.filter.get('payerOGRN', '')
        payerKBK = self.filter.get('payerKBK', '')
        #payerBank = self.filter.get('payerBank', '')
        enableInAccounts = self.filter.get('enableInAccounts', 0)
        orgId = self.filter.get('orgId', None)
        setDate = self.filter.get('setDate', QDate())
        if setDate:
            begDate = setDate
            endDate = setDate
        else:
            begDate = self.filter.get('begDate', QDate())
            endDate = self.filter.get('endDate', QDate())
        if orgId:
            cond.append(tableContract['payer_id'].eq(orgId))
        if financeId:
            cond.append(tableContract['finance_id'].eq(financeId))
        if enableInAccounts:
            cond.append(tableContract['disableInAccounts'].eq(enableInAccounts-1))
        if payerId:
            cond.append(tableContract['payer_id'].eq(payerId))
        if payerAccountId:
            cond.append(tableContract['payerAccount_id'].eq(payerAccountId))
        if payerINN:
            cond.append(tableOrganisation['INN'].eq(payerINN))
        if payerOGRN:
            cond.append(tableOrganisation['OGRN'].eq(payerOGRN))
        if number:
            cond.append(tableContract['number'].eq(number))
        if grouping:
            cond.append(tableContract['grouping'].eq(grouping))
        if resolution:
            cond.append(tableContract['resolution'].eq(resolution))
        if payerKBK:
            cond.append(tableOrganisation['payerKBK'].eq(payerKBK))
        if setDate:
            if begDate:
                cond.append(tableContract['begDate'].le(begDate))
            if endDate:
                cond.append(tableContract['endDate'].ge(endDate))
        else:
            if begDate:
                cond.append(tableContract['begDate'].le(endDate))
            if endDate:
                cond.append(tableContract['endDate'].ge(begDate))
        if financeTypeCodeList:
            cond.append(tableContract['finance_id'].inlist([CFinanceType.getId(code) for code in financeTypeCodeList]))
        records = db.getRecordList(table,
                                   'Contract.id, Contract.finance_id, Contract.grouping, Contract.resolution, Contract.date, Contract.number',
                                   where=db.joinAnd(cond),
                                   order='Contract.finance_id, Contract.grouping, Contract.resolution, Contract.date, Contract.number, Contract.id')
        for record in records:
            contractId = forceRef(record.value('id'))
            contractName = forceString(record.value('number')) + u' от ' +forceString(record.value('date'))
            path = [ CFinanceType.getNameById(forceInt(record.value('finance_id'))),
                     forceString(record.value('grouping')),
                     forceString(record.value('resolution')),
                     contractName
                   ]
            self.addItem(path, 0, contractId)
            contracts[contractId] = contractName
            self._contractIdToPath[contractId] = path
            self._pathToContractId['\\'.join(path)] = contractId


    def getPathById(self, contractId):
        return self._contractIdToPath.get(contractId, '')


    def getIdByPath(self, path):
        return self._pathToContractId.get(path, None)

    def getFinanceName(self, val):
        financeId = forceRef(val)
        name = self._mapFinanceName.get(financeId, '{%s}' % financeId)
        return name

class CAccountsModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent,  [
            CDesignationCol(u'Договор', ['contract_id'], ('vrbContract', 'code'), 20),
            CDateCol(u'Расчётная дата', ['settleDate'], 20),
            CDateCol(u'Дата создания', ['createDatetime'], 20),
            CTextCol(u'Номер', ['number'], 20),
            CDateCol(u'Дата', ['date'], 20),
            CDesignationCol(u'Плательщик', ['payer_id'], ('Organisation', 'CONCAT(infisCode, \' | \', shortName)'), 8),
            CDesignationCol(u'Тип реестра', ['type_id'], ('rbAccountType', 'CONCAT(regionalCode, \' | \', name)'), 8),
            CEnumCol(u'Ед. учета МП', ['group_id'], [u'', u'Койко-день', u'Койко-день', u'Посещение', u'Посещение',
                                                     u'Посещение', u'Посещение', u'День лечения', u'Вызов бригады СМП',
                                                     u'Койко-день', u'День лечения', u'Посещение', u'Посещение',
                                                     u'Посещение', u'Посещение', u'Посещение', u'Посещение',
                                                     u'Посещение', u'Услуга', u'Услуга', u'Услуга', u'Услуга',
                                                     u'День лечения', u'Услуга', u'Посещение', u'Посещение',
                                                     u'Посещение', u'Посещение', u'Посещение', u'Посещение', u'Услуга',
                                                     u'Посещение', u'Посещение', u'Посещение'], 20),
            CNumCol(u'Количество', ['amount'], 20, 'r'),
            CNumCol(u'Количество событий', ['amountEvents'], 20, 'r'),
            CNumCol(u'УЕТ', ['uet'], 20, 'r'),
            CSumCol(u'Сумма', ['sum'], 20, 'r'),
            CSumCol(u'Выставлено', ['exposedSum'], 20, 'r'),
            CSumCol(u'Оплачено', ['payedSum'], 20, 'r'),
            CSumCol(u'Отказано', ['refusedSum'], 20, 'r'),
            CDateCol(u'Дата выставления', ['exposeDate'], 20),
            CDesignationCol(u'Подразделение', ['orgStructure_id'], ('OrgStructure', 'name'), 8),
            CTextCol(u'Примечание', ['note'], 20),
            ], 'Account')
        self.parentWidget = parent
        self.headerSortingCol = {}


    def canRemoveItem(self, accountId):
        return canRemoveAccount(accountId)


    def confirmRemoveItem(self, view, accountId, multiple=False):
        if not canRemoveAccount(accountId):
            buttons = QtGui.QMessageBox.Ok
            if multiple:
                buttons |= QtGui.QMessageBox.Cancel
            mbResult = QtGui.QMessageBox.critical(view,
                                       u'Внимание!',
                                       u'Счёт имеет подтверждённые записи реестра и не подлежит удалению',
                                       buttons)
            return False if mbResult == QtGui.QMessageBox.Ok else None
        else:
            buttons = QtGui.QMessageBox.Yes|QtGui.QMessageBox.No
            if multiple:
                buttons |= QtGui.QMessageBox.Cancel
            mbResult = QtGui.QMessageBox.question(view,
                                       u'Внимание!',
                                       u'Вы действительно хотите удалить счёт?',
                                       buttons,
                                       QtGui.QMessageBox.No)
            return {QtGui.QMessageBox.Yes: True,
                    QtGui.QMessageBox.No: False}.get(mbResult, None)


    def beforeRemoveItem(self, accountId):
        clearPayStatus(accountId)


    def afterRemoveItem(self, itemId):
        if itemId:
            db = QtGui.qApp.db
            table = db.table('Account_Item')
            db.deleteRecordSimple(table, [table['master_id'].eq(itemId), table['deleted'].eq(0)])


    def deleteRecord(self, table, itemId):
        QtGui.qApp.db.deleteRecordSimple(table, table[self.idFieldName].eq(itemId))


class CAccountItemsModel(CTableModel):
    def __init__(self, parent):
        fieldList = ['event_id', 'visit_id', 'action_id', 'service_id', 'eventCSG_id']
        eventCol     = CLocEventColumn(                 u'Услуга',      fieldList, 20)
        eventCodeCol = CLocEventCodeColumn(             u'Код',         fieldList, 20, eventCol)
#        eventDateCol = CLocEventDateColumn(             u'Выполнено',   fieldList, 10, eventCol)
        clientCol   = CLocClientColumn( u'Ф.И.О.',      fieldList, 20, eventCol.eventCache)
        mkbCol = CLocMKBColumn(u'МКБ', fieldList, 7)
        clientBirthDateCol = CLocClientBirthDateColumn(
            u'Дата рожд.', fieldList, 10, eventCol.eventCache, clientCol.clientCache)
        clientSexCol = CLocClientSexColumn(
            u'Пол', fieldList, 3, eventCol.eventCache, clientCol.clientCache)

        CTableModel.__init__(self, parent, [
            CNumCol(u'№ п.счета',         ['event_id'],  12, 'r'),
            clientCol,
            clientBirthDateCol,
            clientSexCol,
            mkbCol, 
            eventCodeCol,
            eventCol,
#            eventDateCol,
            CDateCol(u'Выполнено',     ['serviceDate'], 10),
            CSumCol(u'Тариф',          ['price'],  10, 'r'),
            CRefBookCol(u'Ед.Уч.',     ['unit_id'],  'rbMedicalAidUnit', 10),
            CNumCol(u'Кол-во',         ['amount'], 10, 'r'),
            CNumCol(u'УЕТ',            ['uet'],    10, 'r'),
            CTextCol(u'КСЛП', ['usedCoefficients'], 10, 'r'),
            CSumCol(u'Сумма',          ['sum'],    10, 'r'),
            CSumCol(u'Выставлено',     ['exposedSum'], 10, 'r'),
            CSumCol(u'Оплачено',       ['payedSum'],    10, 'r'),
            CTextCol(u'Подтверждение', ['number'], 10),
            CDateCol(u'Дата',          ['date'],   10),
            CRefBookCol(u'Причина отказа', ['refuseType_id', 'reexposeItem_id'], 'rbPayRefuseType', 20, showFields=CRBComboBox.showCodeAndName),
            CTextCol(u'Примечание',    ['note'], 20),
            CLocFKEYCol(u'FKEY', ['event_id'], 40),
            CLocRKEYCol(u'RKEY', ['event_id', 'action_id', 'visit_id', 'eventCSG_id'], 40)
            ], 'Account_Item' )
        self.eventCache  = eventCol.eventCache
        self.eventTypeCache = eventCol.eventTypeCache
        self.serviceCache   = eventCol.serviceCache
        self.actionTypeCache= eventCol.actionTypeCache
        self.visitCache  = eventCol.visitCache
        self.actionCache = eventCol.actionCache
        self.clientCache = clientCol.clientCache
        self.MKBCache = mkbCol.MKBCache


    def getEventColFormat(self, accountItemsIdList):
        resIdList = {}
        for accountItemsId in accountItemsIdList:
            record = self.getRecordById(accountItemsId)
            if record:
                resName = False
                serviceId = forceRef(record.value('service_id'))
                if serviceId:
                    serviceRecord = self.serviceCache.get(serviceId)
                    if serviceRecord:
                        name = forceString(serviceRecord.value('name'))
                        dataIdList = resIdList.get(name, [])
                        dataIdList.append(accountItemsId)
                        resIdList[name] = dataIdList
                        resName = True
                if not resName:
                    actionId = forceRef(record.value('action_id'))
                    if actionId:
                        actionRecord = self.actionCache.get(actionId)
                        if actionRecord:
                            actionTypeId = forceRef(actionRecord.value('actionType_id'))
                            actionTypeRecord = self.actionTypeCache.get(actionTypeId)
                            if actionTypeRecord:
                                name = forceString(actionTypeRecord.value('name'))
                                dataIdList = resIdList.get(name, [])
                                dataIdList.append(accountItemsId)
                                resIdList[name] = dataIdList
                                resName = True
                if not resName:
                    visitId = forceRef(record.value('visit_id'))
                    if visitId:
                        visitRecord = self.visitCache.get(visitId)
                        if visitRecord:
                            serviceId = forceRef(visitRecord.value('service_id'))
                            serviceRecord = self.serviceCache.get(serviceId)
                            if serviceRecord:
                                name = forceString(serviceRecord.value('name'))
                                dataIdList = resIdList.get(name, [])
                                dataIdList.append(accountItemsId)
                                resIdList[name] = dataIdList
                                resName = True
                if not resName:
                    eventId = forceRef(record.value('event_id'))
                    if eventId:
                        eventRecord = self.eventCache.get(eventId)
                        if eventRecord:
                            eventTypeId = forceRef(eventRecord.value('eventType_id'))
                            eventTypeRecord = self.eventTypeCache.get(eventTypeId)
                            if eventTypeRecord:
                                name = forceString(eventTypeRecord.value('name'))
                                dataIdList = resIdList.get(name, [])
                                dataIdList.append(accountItemsId)
                                resIdList[name] = dataIdList
        return resIdList


    def getMKBColFormat(self, accountItemsIdList):
        resIdList = {}
        for accountItemsId in accountItemsIdList:
            record = self.getRecordById(accountItemsId)
            if record:
                eventId = forceRef(record.value('event_id'))
                actionId = forceRef(record.value('actionId'))
                if eventId:
                    code = None
                    if actionId:
                        stmt = u"""SELECT IF(ep.regionalCode in ('102', '103', '8008', '8009', '8010', '8011', '8012', '8013', '8014', '8015', '8016', '8017', '8018', '8019', '8020', '8021', '8022')
                                    or mt.regionalCode in ('31', '32'),
                                    IF(IFNULL(a.MKB, '') <> '', a.MKB, d.MKB), d.MKB) AS MKB
                                from Event e
                                left join EventType et on et.id = e.eventType_id
                                left join rbMedicalAidType mt on et.medicalAidType_id = mt.id
                                left join rbEventProfile ep on ep.id = et.eventProfile_id
                                left join Diagnosis d on d.id = getEventDiagnosis(e.id)
                                left join Action a on a.id = %d
                                WHERE e.id = %d""" % (actionId, eventId)
                        query = QtGui.qApp.db.query(stmt)
                        if query.first():
                            code = forceString(query.record().value(0))
                    else:
                        code = self.MKBCache.get(eventId, None)
                        if code is None:
                            stmt = 'SELECT MKB from Diagnosis WHERE id = getEventDiagnosis(%d) LIMIT 1' % eventId
                            query = QtGui.qApp.db.query(stmt)
                            if query.first():
                                code = forceString(query.record().value(0))
                                self.MKBCache[eventId] = code
                    dataIdList = resIdList.get(code, [])
                    dataIdList.append(accountItemsId)
                    resIdList[code] = dataIdList
        return resIdList


    def getEventCodeColFormat(self, accountItemsIdList):
        resIdList = {}
        for accountItemsId in accountItemsIdList:
            record = self.getRecordById(accountItemsId)
            if record:
                resName = False
                serviceId = forceRef(record.value('service_id'))
                if serviceId:
                    serviceRecord = self.serviceCache.get(serviceId)
                    if serviceRecord:
                        code = forceString(serviceRecord.value('code'))
                        dataIdList = resIdList.get(code, [])
                        dataIdList.append(accountItemsId)
                        resIdList[code] = dataIdList
                        resName = True
                if not resName:
                    visitId = forceRef(record.value('visit_id'))
                    if visitId:
                        visitRecord = self.visitCache.get(visitId)
                        if visitRecord:
                            serviceId = forceRef(visitRecord.value('service_id'))
                            if serviceId:
                                serviceRecord = self.serviceCache.get(serviceId)
                                if serviceRecord:
                                    code = forceString(serviceRecord.value('code'))
                                    dataIdList = resIdList.get(code, [])
                                    dataIdList.append(accountItemsId)
                                    resIdList[code] = dataIdList
                                    resName = True
                if not resName:
                    eventId = forceRef(record.value('event_id'))
                    if eventId:
                        eventRecord = self.eventCache.get(eventId)
                        if eventRecord:
                            eventTypeId = forceRef(eventRecord.value('eventType_id'))
                            eventTypeRecord = self.eventTypeCache.get(eventTypeId)
                            if eventTypeRecord:
                                serviceId = forceRef(eventTypeRecord.value('service_id'))
                                if serviceId:
                                    serviceRecord = self.serviceCache.get(serviceId)
                                    if serviceRecord:
                                        code = forceString(serviceRecord.value('code'))
                                        dataIdList = resIdList.get(code, [])
                                        dataIdList.append(accountItemsId)
                                        resIdList[code] = dataIdList
        return resIdList


    def getRKEYColFormat(self, accountItemsIdList):
        resIdList = {}
        for accountItemsId in accountItemsIdList:
            record = self.getRecordById(accountItemsId)
            if record:
                eventId = forceRef(record.value('event_id'))
                actionId = forceRef(record.value('action_id'))
                visitId = forceRef(record.value('visit_id'))
                db = QtGui.qApp.db
                table = db.table('soc_Account_RowKeys')
                cond = [table['event_id'].eq(eventId), table['typeFile'].eq('U')]
                if actionId:
                    cond.append(table['row_id'].eq(actionId))
                elif visitId:
                    cond.append(table['row_id'].eq(visitId))
                else:
                    cond.append(table['row_id'].eq(eventId))
                record = db.getRecordEx(table, table['key'], db.joinAnd(cond))
                code = ''
                if record:
                    code = forceString(record.value('key'))
                dataIdList = resIdList.get(code, [])
                dataIdList.append(accountItemsId)
                resIdList[code] = dataIdList
        return resIdList


    def getFKEYColFormat(self, accountItemsIdList):
        resIdList = {}
        for accountItemsId in accountItemsIdList:
            record = self.getRecordById(accountItemsId)
            if record:
                eventId = forceRef(record.value('event_id'))
                db = QtGui.qApp.db
                table = db.table('soc_Account_RowKeys')
                cond = [table['event_id'].eq(eventId), table['typeFile'].eq('F')]
                record = db.getRecordEx(table, table['key'], db.joinAnd(cond))
                code = ''
                if record:
                    code = forceString(record.value('key'))
                dataIdList = resIdList.get(code, [])
                dataIdList.append(accountItemsId)
                resIdList[code] = dataIdList
        return resIdList


class CLocEventColumn(CCol):
    def __init__(self, title, fields, defaultWidth):
        CCol.__init__(self, title, fields, defaultWidth, 'l')
        db = QtGui.qApp.db
        self.eventCache     = CTableRecordCache(db, 'Event', 'eventType_id, client_id, execDate')
        self.eventTypeCache = CTableRecordCache(db, 'EventType', 'name, service_id')
        self.visitCache     = CTableRecordCache(db, 'Visit', 'date, service_id')
        self.serviceCache   = CTableRecordCache(db, 'rbService', 'name, code')
        self.actionCache    = CTableRecordCache(db, 'Action', 'endDate, actionType_id')
        self.actionTypeCache= CTableRecordCache(db, 'ActionType', 'name')


    def format(self, values):
        serviceId = forceRef(values[3])
        if serviceId:
            serviceRecord = self.serviceCache.get(serviceId)
            if serviceRecord:
                return serviceRecord.value('name')

        actionId = forceRef(values[2])
        if actionId:
            actionRecord = self.actionCache.get(actionId)
            if actionRecord:
                actionTypeId = forceRef(actionRecord.value('actionType_id'))
                actionTypeRecord = self.actionTypeCache.get(actionTypeId)
                if actionTypeRecord:
                    return actionTypeRecord.value('name')
            return CCol.invalid

        visitId = forceRef(values[1])
        if visitId:
            visitRecord = self.visitCache.get(visitId)
            if visitRecord:
                serviceId = forceRef(visitRecord.value('service_id'))
                serviceRecord = self.serviceCache.get(serviceId)
                if serviceRecord:
                    return serviceRecord.value('name')
            return CCol.invalid

        eventId = forceRef(values[0])
        if eventId:
            eventRecord = self.eventCache.get(eventId)
            if eventRecord:
                eventTypeId = forceRef(eventRecord.value('eventType_id'))
                eventTypeRecord = self.eventTypeCache.get(eventTypeId)
                if eventTypeRecord:
                    return eventTypeRecord.value('name')
            return CCol.invalid

        return CCol.invalid


    def invalidateRecordsCache(self):
        self.eventCache.invalidate()
        self.eventTypeCache.invalidate()
        self.visitCache.invalidate()
        self.serviceCache.invalidate()
        self.actionCache.invalidate()
        self.actionTypeCache.invalidate()


class CLocRKEYCol(CCol):
    def __init__(self, title, fields, defaultWidth):
        CCol.__init__(self, title, fields, defaultWidth, 'l')


    def format(self, values):
        eventId = forceRef(values[0])
        actionId = forceRef(values[1])
        visitId = forceRef(values[2])
        eventCSGId = forceRef(values[3])
        db = QtGui.qApp.db
        table = db.table('soc_Account_RowKeys')
        cond = [table['event_id'].eq(eventId),
                table['typeFile'].eq('U')]
        if actionId:
            cond.append(table['row_id'].eq(actionId))
        elif visitId:
            cond.append(table['row_id'].eq(visitId))
        elif eventCSGId:
            cond.append(table['row_id'].eq(eventCSGId))
        else:
            cond.append(table['row_id'].eq(eventId))
        record = db.getRecordEx(table, table['key'], db.joinAnd(cond))
        if record:
            return record.value('key')
        return CCol.invalid

class CLocFKEYCol(CCol):
    def __init__(self, title, fields, defaultWidth):
        CCol.__init__(self, title, fields, defaultWidth, 'l')


    def format(self, values):
        eventId = forceRef(values[0])
        db = QtGui.qApp.db
        table = db.table('soc_Account_RowKeys')
        cond = [table['event_id'].eq(eventId),
                table['typeFile'].eq('F')]
        record = db.getRecordEx(table, table['key'], db.joinAnd(cond))
        if record:
            return record.value('key')
        return CCol.invalid


class CLocEventCodeColumn(CCol):
    def __init__(self, title, fields, defaultWidth, master):
        CCol.__init__(self, title, fields, defaultWidth, 'l')
        self.eventCache     = master.eventCache
        self.eventTypeCache = master.eventTypeCache
        self.visitCache     = master.visitCache
        self.actionCache    = master.actionCache
        self.actionTypeCache= master.actionTypeCache
        self.serviceCache   = master.serviceCache


    def getServiceCode(self, serviceId):
        if serviceId:
            serviceRecord = self.serviceCache.get(serviceId)
            if serviceRecord:
                return serviceRecord.value('code')
        else:
            return CCol.invalid


    def format(self, values):
        serviceId = forceRef(values[3])
        if serviceId:
            return self.getServiceCode(serviceId)

        visitId = forceRef(values[1])
        if visitId:
            visitRecord = self.visitCache.get(visitId)
            if visitRecord:
                serviceId = forceRef(visitRecord.value('service_id'))
                return self.getServiceCode(serviceId)
            return CCol.invalid

        eventId = forceRef(values[0])
        if eventId:
            eventRecord = self.eventCache.get(eventId)
            if eventRecord:
                eventTypeId = forceRef(eventRecord.value('eventType_id'))
                eventTypeRecord = self.eventTypeCache.get(eventTypeId)
                if eventTypeRecord:
                    serviceId = forceRef(eventTypeRecord.value('service_id'))
                    return self.getServiceCode(serviceId)
            return CCol.invalid

        return CCol.invalid

class CLocMKBColumn(CCol):
    def __init__(self, title, fields, defaultWidth):
        CCol.__init__(self, title, fields, defaultWidth, 'l')
        self.MKBCache = dict()

    def format(self, values):
        eventId = forceRef(values[0])
        actionId = forceRef(values[2])
        eventCSG_id = forceRef(values[4])
        if eventId:
            if actionId:
                stmt = u"""SELECT IF(ep.regionalCode in ('102', '103', '8008', '8009', '8010', '8011', '8012', '8013', '8014', '8015', '8016', '8017', '8018', '8019', '8020', '8021', '8022')
                    or mt.regionalCode in ('31', '32'), 
                    IF(IFNULL(a.MKB, '') <> '', a.MKB, d.MKB), d.MKB) AS MKB
                from Event e
                left join EventType et on et.id = e.eventType_id
                left join rbMedicalAidType mt on et.medicalAidType_id = mt.id
                left join rbEventProfile ep on ep.id = et.eventProfile_id
                left join Diagnosis d on d.id = getEventDiagnosis(e.id)
                left join Action a on a.id = %d
                WHERE e.id = %d""" % (actionId, eventId)
            elif eventCSG_id:
                stmt = 'SELECT MKB from Event_CSG WHERE id = {0}'.format(eventCSG_id)
            else:
                stmt = 'SELECT MKB from Diagnosis WHERE id = getEventDiagnosis(%d) LIMIT 1' % eventId
            query = QtGui.qApp.db.query(stmt)
            if query.first():
                return forceString(query.record().value(0))
        return CCol.invalid
        
#class CLocEventDateColumn(CCol):
#    def __init__(self, title, fields, defaultWidth, master):
#        CCol.__init__(self, title, fields, defaultWidth, 'l')
#        db = QtGui.qApp.db
#        self.eventCache     = master.eventCache
#        self.visitCache     = master.visitCache
#        self.actionCache    = master.actionCache
#
#    def format(self, values):
#        fieldValue = None
#        eventId  = forceRef(values[0])
#        visitId  = forceRef(values[1])
#        actionId = forceRef(values[2])
#        if actionId:
#            actionRecord = self.actionCache.get(actionId)
#            if actionRecord:
#                fieldValue = actionRecord.value('endDate')
#        elif visitId:
#            visitRecord = self.visitCache.get(visitId)
#            if visitRecord:
#                fieldValue = visitRecord.value('date')
#        elif eventId:
#            eventRecord = self.eventCache.get(eventId)
#            if eventRecord:
#                fieldValue = eventRecord.value('execDate')
#        if fieldValue is not None:
#            return toVariant(forceString(fieldValue.toDate()))
#        return CCol.invalid


class CLocClientColumn(CCol):
    def __init__(self, title, fields, defaultWidth, eventCache):
        CCol.__init__(self, title, fields, defaultWidth, 'l')
        db = QtGui.qApp.db
        self.eventCache  = eventCache
        self.clientCache = CTableRecordCache(db, 'Client', 'lastName, firstName, patrName, birthDate, sex, SNILS')

    def format(self, values):
        val = values[0]
        eventId  = forceRef(val)
        eventRecord = self.eventCache.get(eventId)
        if eventRecord:
            clientId = forceRef(eventRecord.value('client_id'))
            clientRecord = self.clientCache.get(clientId)
            if clientRecord:
                name  = formatName(clientRecord.value('lastName'),
                                   clientRecord.value('firstName'),
                                   clientRecord.value('patrName'))
                return toVariant(name)
        return CCol.invalid


    def invalidateRecordsCache(self):
        self.clientCache.invalidate()


class CLocClientBirthDateColumn(CCol):
    def __init__(self, title, fields, defaultWidth, eventCache, clientCache):
        CCol.__init__(self, title, fields, defaultWidth, 'l')
        self.eventCache  = eventCache
        self.clientCache = clientCache

    def format(self, values):
        val = values[0]
        eventId  = forceRef(val)
        eventRecord = self.eventCache.get(eventId)
        if eventRecord:
            clientId = forceRef(eventRecord.value('client_id'))
            clientRecord = self.clientCache.get(clientId)
            if clientRecord:
                return toVariant(forceString(clientRecord.value('birthDate')))
        return CCol.invalid


class CLocClientSexColumn(CCol):
    def __init__(self, title, fields, defaultWidth, eventCache, clientCache):
        CCol.__init__(self, title, fields, defaultWidth, 'l')
        self.eventCache  = eventCache
        self.clientCache = clientCache

    def format(self, values):
        val = values[0]
        eventId  = forceRef(val)
        eventRecord = self.eventCache.get(eventId)
        if eventRecord:
            clientId = forceRef(eventRecord.value('client_id'))
            clientRecord = self.clientCache.get(clientId)
            if clientRecord:
                return toVariant(formatSex(clientRecord.value('sex')))
        return CCol.invalid



#
# ######################################################################
#

def getContractDescr(contractId):
    return CContractDescr(contractId)


class CContractDescr:
    def __init__(self, contractId):
        db = QtGui.qApp.db
        table = db.table('Contract')
        record = db.getRecord(table, ('number',
                                      'date',
                                      'payer_id',
                                      'finance_id',
                                      'begDate',
                                      'endDate',
                                      'dateOfVisitExposition',
                                      'visitExposition',
                                      'dateOfActionExposition',
                                      'actionExposition',
                                      'dateOfCsgExposition',
                                      'exposeExternalServices',
                                      'exposeIfContinuedEventFinished',
                                      'exposeByLastEventContract',
                                      'exposeDiscipline',
                                      'pricePrecision',
                                      'valueTariffCoeffPrecision',
                                      'regionalTariffRegulationFactor',
                                      'isOnlyEventsPassedExpertise',
                                      'isExposeByAccountType',
                                      'format_id',
                                      'counter_id'), contractId)
        self.id = contractId
        self.number = forceString(record.value('number'))
        self.date   = forceDate(record.value('date'))
        self.payerId = forceRef(record.value('payer_id'))
        self.financeId = forceRef(record.value('finance_id'))
        self.financeType = CFinanceType.getCode(self.financeId)
        self.payStatusMask = getPayStatusMask(self.financeId)
        self.begDate = forceDate(record.value('begDate'))
        self.endDate = forceDate(record.value('endDate'))
        self.dateOfVisitExposition = forceInt(record.value('dateOfVisitExposition'))
        self.visitExposition = forceInt(record.value('visitExposition'))
        self.dateOfActionExposition = forceInt(record.value('dateOfActionExposition'))
        self.actionExposition = forceInt(record.value('actionExposition'))
        self.dateOfCsgExposition = forceInt(record.value('dateOfCsgExposition'))
        self.exposeExternalServices = forceBool(record.value('exposeExternalServices'))
        self.exposeIfContinuedEventFinished = forceBool(record.value('exposeIfContinuedEventFinished'))
        self.exposeByLastEventContract = forceBool(record.value('exposeByLastEventContract')) and self.exposeIfContinuedEventFinished
        self.exposeDiscipline = forceInt(record.value('exposeDiscipline'))
        self.attributes = CContractAttributesDescr(contractId)
        self.coefficients = CContractCoefficientsDescr(contractId)
        self.pricePrecision = forceInt(record.value('pricePrecision'))
        self.valueTariffCoeffPrecision = forceInt(record.value('valueTariffCoeffPrecision'))
        self.regionalTariffRegulationFactor = forceDouble(record.value('regionalTariffRegulationFactor'))
        self.onlyInspectedEvents = forceBool(record.value('isOnlyEventsPassedExpertise'))
        self.exposeByAccountType = forceBool(record.value('isExposeByAccountType'))
        self.formatId = forceRef(record.value('format_id'))
        self.counterId = forceRef(record.value('counter_id'))
        self.prog = None
        if self.formatId:
            self.prog = forceString(db.translate('rbAccountExportFormat', 'id', self.formatId, 'prog'))

        tableSpecification = db.table('Contract_Specification')
    
        tariffByEventType = {}
        tariffByVisitService = {}
        tariffByActionService = {}
        tariffByCoupleVisitEventType = {}
        tariffByHospitalBedDay = {}
        tariffByHospitalBedService = {}
        tariffVisitByActionService = {}
        tariffVisitsByMES = {}
        tariffEventByMES = {}
        tariffCoupleVisits = {}
        tariffByCSG = {}
        tableContractTariff = db.table('Contract_Tariff')
        eventTypeIdSet = set()
        priceListId = forceRef(db.translate('Contract', 'id', contractId, 'priceListExternal_id'))
        
        if priceListId is None:
            masterCond = tableContractTariff['master_id'].eq(contractId)
            order = 'id'
        else:
            masterCond = tableContractTariff['master_id'].inlist([contractId, priceListId])
            # Антон, такая сортировка подходит?
            order = 'master_id, id' if priceListId<contractId else 'master_id DESC, id'
            
        for record in db.getRecordList(tableContractTariff, '*', [masterCond, tableContractTariff['deleted'].eq(0)], order):
            tariff = CTariff(record, self.pricePrecision)
            tariffType  = tariff.tariffType
            eventTypeId = tariff.eventTypeId
            serviceId   = tariff.serviceId
            if tariffType == CTariff.ttVisit:
                if serviceId:
                    addTariffToDict(tariffByVisitService, serviceId, tariff)
                    eventTypeIdSet.add(eventTypeId)
            elif tariffType == CTariff.ttEvent:
                if eventTypeId:
                    tariff.eventTypeId = None # в этом случае проверка по eventTypeId избыточна.
                    addTariffToDict(tariffByEventType, eventTypeId, tariff)
                    eventTypeIdSet.add(eventTypeId)
            elif tariffType == CTariff.ttActionAmount or tariffType == CTariff.ttActionUET: # action, по количеству или УЕТ
                if serviceId:
                    addTariffToDict(tariffByActionService, serviceId, tariff)
                    eventTypeIdSet.add(eventTypeId)
            elif tariffType == CTariff.ttEventAsCoupleVisits: # визит-день
                if eventTypeId and serviceId:
                    tariff.eventTypeId = None
                    addTariffToDict(tariffByCoupleVisitEventType, eventTypeId, tariff)
                    eventTypeIdSet.add(eventTypeId)
            elif tariffType == CTariff.ttHospitalBedDay:  # койко-день
                if eventTypeId and serviceId:
                    tariff.eventTypeId = None
                    addTariffToDict(tariffByHospitalBedDay, eventTypeId, tariff)
                    eventTypeIdSet.add(eventTypeId)
            elif tariffType == CTariff.ttHospitalBedService: # мероприятия по тарифу коек
                addTariffToDict(tariffByHospitalBedService, eventTypeId, tariff)
                eventTypeIdSet.add(eventTypeId)
            elif tariffType == CTariff.ttVisitByAction:      # визит по мероприятию
                if serviceId:
                    addTariffToDict(tariffVisitByActionService, serviceId, tariff)
                    eventTypeIdSet.add(eventTypeId)
            elif tariffType == CTariff.ttVisitsByMES:
                if eventTypeId:
                    tariff.eventTypeId = None # в этом случае проверка по eventTypeId избыточна.
                    addTariffToDict(tariffVisitsByMES, (eventTypeId, serviceId), tariff)
                    eventTypeIdSet.add(eventTypeId)
            elif tariffType in (CTariff.ttEventByMES,
                                CTariff.ttEventByMESLen,
                                CTariff.ttEventByMESLevel,
                                CTariff.ttMurmansk2015Hospital,
                               ):
                if eventTypeId:
                    tariff.eventTypeId = None # в этом случае проверка по eventTypeId избыточна.
                    addTariffToDict(tariffEventByMES, (eventTypeId, serviceId), tariff)
                    eventTypeIdSet.add(eventTypeId)
            # убрал проверку соответствия по eventType_id
            elif tariffType == CTariff.ttKrasnodarA13:
                tariff.eventTypeId = None # в этом случае проверка по eventTypeId избыточна.
                addTariffToDict(tariffEventByMES, (None, serviceId), tariff)
                eventTypeIdSet.add(eventTypeId)
                
            elif tariffType == CTariff.ttCoupleVisits:
                addTariffToDict(tariffCoupleVisits, (eventTypeId, serviceId), tariff)
                eventTypeIdSet.add(eventTypeId)
            elif tariffType == CTariff.ttCSG:
                # if eventTypeId:
                    tariff.eventTypeId = None # в этом случае проверка по eventTypeId избыточна.
                    addTariffToDict(tariffByCSG, (eventTypeId, serviceId), tariff)
                    eventTypeIdSet.add(eventTypeId)

        self.tariffByEventType            = sortTariffsInDict(tariffByEventType)
        self.tariffByVisitService         = sortTariffsInDict(tariffByVisitService)
        self.tariffByActionService        = sortTariffsInDict(tariffByActionService)
        self.tariffByCoupleVisitEventType = sortTariffsInDict(tariffByCoupleVisitEventType)
        self.tariffByHospitalBedDay       = sortTariffsInDict(tariffByHospitalBedDay)
        self.tariffByHospitalBedService   = sortTariffsInDict(tariffByHospitalBedService)
        self.tariffVisitByActionService   = sortTariffsInDict(tariffVisitByActionService)
        self.tariffVisitsByMES            = sortTariffsInDict(tariffVisitsByMES)
        self.tariffEventByMES             = sortTariffsInDict(tariffEventByMES)
        self.tariffCoupleVisits           = sortTariffsInDict(tariffCoupleVisits)
        self.tariffByCSG = sortTariffsInDict(tariffByCSG)

        eventTypeIdList = db.getIdList(tableSpecification,
                                       'eventType_id',
                                       [tableSpecification['master_id'].eq(contractId), tableSpecification['deleted'].eq(0)])
    
        if eventTypeIdList:
            if None not in eventTypeIdSet:
                eventTypeIdList = list(set(eventTypeIdList)&eventTypeIdSet)
        else:
            if None not in eventTypeIdSet:
                eventTypeIdList = list(eventTypeIdSet)
                
        self.specification = eventTypeIdList


#
# ######################################################################
#

class CVariantSeries(CBaseSeries):
    def __init__(self, default=QVariant()):
        CBaseSeries.__init__(self, default)


class CContractAttributesDescr(CSeriesHolder):
    def __init__(self,  contractId):
        CSeriesHolder.__init__(self, CVariantSeries)
        self.__loadData(contractId)


    def __loadData(self, contractId):
        db = QtGui.qApp.db
        tableContractAttribute = db.table('Contract_Attribute')
        tableAttributeType     = db.table('rbContractAttributeType')
        table = tableContractAttribute.innerJoin(tableAttributeType,
                                                 tableAttributeType['id'].eq(tableContractAttribute['attributeType_id'])
                                                 )
        cond = [  tableContractAttribute['master_id'].eq(contractId),
                  tableContractAttribute['deleted'].eq(0),
               ]
        recordList = db.getRecordList(table,
                                      [ tableAttributeType['code'],
                                        tableContractAttribute['begDate'],
                                        tableContractAttribute['value'],
                                      ],
                                      where=cond,
                                      order=tableContractAttribute['id'].name()
                                     )
        for record in recordList:
            code      = forceString(record.value('code'))
            begDate   = forceDate(record.value('begDate'))
            value     = record.value('value')
            self.append(code, begDate, value)

#
# ######################################################################
#

class CCoefficientTypeSign:
    delta = 0.0001

    def __init__(self, record):
        self.grouping = forceInt(record.value('grouping'))
        self.sex = forceInt(record.value('sex'))
        self.ageSelector = parseAgeSelector(forceString(record.value('age')))
        self.mesCodeRegExp = self._compRegExp(forceString(record.value('mesCodeRegExp')))
        self.mesSpecificationId = forceRef(record.value('mesSpecification_id'))
        self.csgCodeRegExp = self._compRegExp(forceString(record.value('csgCodeRegExp')))
        self.csgSpecificationId = forceRef(record.value('csgSpecification_id'))
        self.diagnosisTypeId = forceRef(record.value('diagnosisType_id'))
        self.mkbRegExp = self._compRegExp(forceString(record.value('mkbRegExp')))
        self.serviceCodeRegExp = self._compRegExp(forceString(record.value('serviceCodeRegExp')))
        self.socStatusTypeId = forceRef(record.value('socStatusType_id'))
        self.resultId = forceRef(record.value('result_id'))
        self.ugrency = forceInt(record.value('urgency'))
        self.actionSpecificationId = forceRef(record.value('actionSpecification_id'))

        self.minAmount = forceDouble(record.value('minAmount'))
        self.maxAmount = forceDouble(record.value('maxAmount'))
#        if self.minAmount == 0.0:
#            self.minAmount = 0.0
        if self.maxAmount == 0.0:
            self.maxAmount = float('inf')


    def _compRegExp(self, srcStr):
        return re.compile('^'+srcStr+'$') if srcStr else None


    def match(self, accontingDetails):
        if self.sex and self.sex != accontingDetails['clientSex']:
            return False
        if self.ageSelector and not checkAgeSelector(self.ageSelector, accontingDetails['clientAge']):
            return False
        if self.mesCodeRegExp and not self.mesCodeRegExp.match(accontingDetails['mesCode']):
            return False
        if self.mesSpecificationId and self.mesSpecificationId != accontingDetails['mesSpecificationId']:
            return False
        if self.csgCodeRegExp and (accontingDetails['csgCode'] is None or not self.csgCodeRegExp.match(accontingDetails['csgCode'])):
            return False
        if self.csgSpecificationId and self.csgSpecificationId != accontingDetails['csgSpecificationId']:
            return False
        if self.diagnosisTypeId or self.mkbRegExp:
            matched = False
            for diagnosisTypeId, mkb in accontingDetails['diagnosisTypeAndCodeList']:
                matched = (not self.diagnosisTypeId or self.diagnosisTypeId == diagnosisTypeId) \
                          and (not self.mkbRegExp or self.mkbRegExp.match(mkb))
                if matched:
                    break
            if not matched:
                return False
        if self.socStatusTypeId and self.socStatusTypeId not in accontingDetails['socStatusIdList']:
            return False
        if self.resultId and self.resultId != accontingDetails['resultId']:
            return False
#        if accontingDetails['matter'] == 2: # Action
#            if self.ugrency == 1 and not accontingDetails['isUrgent']:
#                return False
#            if self.ugrency == 2 and accontingDetails['isUrgent']:
#                return False
#        if self.actionSpecificationId and self.actionSpecificationId != accontingDetails['actionSpecificationId']:
#            return False
        if self.serviceCodeRegExp:
            matchedAmount = 0.0
            for suspa in accontingDetails['SUSPAList']:
                if ( self.serviceCodeRegExp.match(suspa.serviceCode)
                     and ( self.ugrency == 0
                           or (self.ugrency == 1 and suspa.isUrgent)
                           or (self.ugrency == 2 and not suspa.isUrgent)
                         )
                     and ( self.actionSpecificationId is None
                           or self.actionSpecificationId == suspa.actionSpecificationId
                         )
                    ):
                    matchedAmount += suspa.amount
            if (   matchedAmount<self.minAmount-self.delta
                or matchedAmount>self.maxAmount+self.delta
               ):
                return False
        return True

#
# ######################################################################
#

CSUSPA = namedtuple('CSUSPA', # Service - Urgency - SPecification - Amount
                    (
                        'serviceCode',
                        'isUrgent',
                        'actionSpecificationId',
                        'amount',
                    )
                   )


class CCoefficientTypeDescr:
    def __init__(self, id):
        self.groupsOfSigns = {}
        self.usageGroupCodes = set([])

        db = QtGui.qApp.db
        record = db.getRecord('rbContractCoefficientType', ('code', 'regionalCode', 'algorithm'), id)
        if record:
            self.code = forceString(record.value('code'))
            self.regionalCode = forceString(record.value('regionalCode'))
            self.algorithm = CCCAlgorithm(forceString(record.value('algorithm')))
        else:
            self.code = ''
            self.regionalCode = ''
            self.algorithm = CCCAlgorithm('')
        table = db.table('rbContractCoefficientType_Sign')
        for record in db.getRecordList(table,
                                       '*',
                                       table['master_id'].eq(id),
                                       table['grouping'].name()
                                      ):
            sign = CCoefficientTypeSign(record)
            self.groupsOfSigns.setdefault(sign.grouping, []).append(sign)


    def addUsageGroup(self, groupCode):
        self.usageGroupCodes.add(groupCode)


    @classmethod
    def getAccountingDetails(cls, date, eventId, eventCsgId, actionId, visitId):
        db = QtGui.qApp.db
        eventRecord = db.getRecord('Event', ('MES_id', 'mesSpecification_id', 'client_id', 'result_id'), eventId)

        mesId = forceRef(eventRecord.value('MES_id'))
        mesSpecificationId = forceRef(eventRecord.value('mesSpecification_id'))
        clientId = forceRef(eventRecord.value('client_id'))
        resultId = forceRef(eventRecord.value('result_id'))
        clientRecord = db.getRecord('Client', ('sex', 'birthDate'), clientId)
        diagnosisTypeAndCodeList = cls._getDiagnosisTypeAndCodeList(eventId)

        if eventCsgId:
            eventCsgRecord = db.getRecord('Event_CSG', ('MKB', 'CSGCode', 'csgSpecification_id'), eventCsgId)
            diagnosisTypeAndCodeList.append((None, forceString(eventCsgRecord.value('MKB'))))
            csgCode = forceString(eventCsgRecord.value('CSGCode'))
            csgSpecificationId = forceRef(eventCsgRecord.value('csgSpecification_id'))
        else:
            csgCode = None
            csgSpecificationId = None


        result = { 'clientSex': forceInt(clientRecord.value('sex')),
                   'clientAge': calcAgeTuple(forceDate(clientRecord.value('birthDate')), date),
                   'mesCode'  : forceString(db.translate('mes.MES', 'id', mesId, 'code')),
                   'mesSpecificationId'      : mesSpecificationId,
                   'csgCode'  : csgCode,
                   'csgSpecificationId'      : csgSpecificationId,
                   'diagnosisTypeAndCodeList': diagnosisTypeAndCodeList,
                   'SUSPAList'               : cls._getSUSPAList(eventId, eventCsgId),
                   'socStatusIdList':db.getIdList('ClientSocStatus',
                                                  'socStatusType_id',
                                                  'deleted=0 AND client_id=%d' % clientId),
                   'resultId' : resultId,
                   'matter'   : 0, # событие
                 }

        if visitId:
            result['matter'] = 1 # Visit

        if actionId:
            result['matter'] = 2 # Action
        return result


    @staticmethod
    def _getSUSPAList(eventId, eventCsgId):
        db = QtGui.qApp.db
        tableAction = db.table('Action')
        tableActionType = db.table('ActionType')
        tableRBService = db.table('rbService')

        table = tableAction
        table = table.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
        table = table.innerJoin(tableRBService,  tableRBService['id'].eq(tableActionType['nomenclativeService_id']))

        cond = [ tableAction['event_id'].eq(eventId),
                 tableAction['deleted'].eq(0),
                 tableAction['status'].inlist((CActionStatus.finished, CActionStatus.withoutResult)),
               ]
        if eventCsgId:
            cond.append(tableAction['eventCSG_id'].eq(eventCsgId))

        records = db.getRecordList(table,
                         [ tableRBService['code'],
                           tableAction['isUrgent'],
                           tableAction['actionSpecification_id'],
                           tableAction['amount']
                         ],
                         cond,
                        )
        result = [ CSUSPA( forceString(record.value('code')),
                           forceBool(record.value('isUrgent')),
                           forceRef(record.value('actionSpecification_id')),
                     forceDouble(record.value('amount')),
                   )
                   for record in records
                 ]
        return result


    @staticmethod
    def _getDiagnosisTypeAndCodeList(eventId):
        db = QtGui.qApp.db
        tableDiagnostic = db.table('Diagnostic')
        tableDiagnosis  = db.table('Diagnosis')

        table = tableDiagnostic
        table = table.innerJoin(tableDiagnosis, tableDiagnosis['id'].eq(tableDiagnostic['diagnosis_id']))
        records = db.getRecordList(table,
                         [ tableDiagnostic['diagnosisType_id'], tableDiagnosis['MKB'] ],
                         [ tableDiagnostic['event_id'].eq(eventId),
                           tableDiagnostic['deleted'].eq(0),
                         ]
                        )
        result = [ ( forceRef(record.value('diagnosisType_id')),
                     forceString(record.value('MKB')),
                   )
                   for record in records
                 ]
        return result


    def applicable(self, accontingDetails):
        if self.groupsOfSigns:
            for groupOfSigns in self.groupsOfSigns.itervalues():
                if self.groupApplicable(groupOfSigns, accontingDetails):
                    return True
            return False
        else:
            return True


    def groupApplicable(self, groupOfSigns, accontingDetails):
        for sign in groupOfSigns:
            if not sign.match(accontingDetails):
                return False
        return True

#
# ######################################################################
#

class CContractCoefficientsDescr(object):
    def __init__(self,  contractId):
        self.mapMatterAndGroupToSeriesHolder = {}
        self.coefficientTypes = { 0: [],
                                  1: [],
                                  2: []
                                }
        self.fallBackGroup = CSeriesHolder(CDoubleSeries)
        self.__loadData(contractId)


    def __getitem__(self, (matter, groupCode)):
        return self.mapMatterAndGroupToSeriesHolder.get((matter, groupCode), self.fallBackGroup)


    def __loadData(self, contractId):
        db = QtGui.qApp.db
        tableContractCoefficient = db.table('Contract_Coefficient')
        tableCoefficient         = db.table('rbContractCoefficientType')
        table = tableContractCoefficient.leftJoin(tableCoefficient,
                                                  tableCoefficient['id'].eq(tableContractCoefficient['coefficientType_id'])
                                                 )
        cond = [  tableContractCoefficient['master_id'].eq(contractId),
                      tableContractCoefficient['isActive'].ne(0),
                  tableContractCoefficient['deleted'].eq(0),
               ]
        recordList = db.getRecordList(table,
                                          [ tableCoefficient['id'],
                                            tableCoefficient['code'],
                                        tableContractCoefficient['matter'],
                                        tableContractCoefficient['begDate'],
                                        tableContractCoefficient['value'],
                                            tableContractCoefficient['groupCode'],
                                            tableContractCoefficient['groupOp'],
                                        tableContractCoefficient['groupPrecision'],
                                            tableContractCoefficient['maxLimit'],
                                      ],
                                      where=cond,
                                      order=[tableContractCoefficient['idx'].name(),
                                             tableContractCoefficient['id'].name(),
                                            ]
                                     )

        coefficientTypeDescrCache = {}

        for record in recordList:
            coefficientCode= forceString(record.value('code'))
            coefficientId  = forceRef(record.value('id'))
            matter         = forceInt(record.value('matter'))
            groupCode = forceInt(record.value('groupCode'))
            groupOp   = forceInt(record.value('groupOp'))
            groupPrecision = forceInt(record.value('groupPrecision'))
            maxLimit  = forceDouble(record.value('maxLimit'))
            begDate        = forceDate(record.value('begDate'))
            value          = forceDouble(record.value('value'))
            coefficientKey = (matter, coefficientId)
            coefficientTypeDescr = coefficientTypeDescrCache.get(coefficientId)
            if coefficientTypeDescr is None:
                coefficientTypeDescr = CCoefficientTypeDescr(coefficientId)
                coefficientTypeDescrCache[coefficientKey] = coefficientTypeDescr
                self.coefficientTypes[matter].append(coefficientTypeDescr)
            coefficientTypeDescr.addUsageGroup(groupCode)
    
            groupKey = (matter, groupCode)
            series = self.mapMatterAndGroupToSeriesHolder.get(groupKey)
            if series is None:
                self.mapMatterAndGroupToSeriesHolder[groupKey] = series = CSeriesHolder(CDoubleSeries)
                series.groupOp  = groupOp
                series.precision = groupPrecision
                series.maxLimit = maxLimit
            series.append(coefficientCode, begDate, value)

def selectEvents(contractDescr, personIdList, begDate, endDate, reexpose, onlyDispCOVID, onlyResearchOnCOVID, onlyTFOMS):
    if (not contractDescr.tariffByEventType
            and not contractDescr.tariffByCoupleVisitEventType
            and not contractDescr.tariffByHospitalBedDay
            and not contractDescr.tariffVisitsByMES
            and not contractDescr.tariffEventByMES):
        return []
    db = QtGui.qApp.db
    tableEvent = db.table('Event')
    tableAccountItem = db.table('Account_Item')
    tableAccount = db.table('Account')
    tablePayRefuseType = db.table('rbPayRefuseType')
    table = tableEvent.leftJoin(tableAccountItem, [tableAccountItem['event_id'].eq(tableEvent['id']),
                                                   tableAccountItem['visit_id'].isNull(),
                                                   tableAccountItem['action_id'].isNull(),
                                                   tableAccountItem['eventCSG_id'].isNull(),
                                                   tableAccountItem['deleted'].eq(0),
                                                   ]
                                )
    table = table.leftJoin(tablePayRefuseType, tablePayRefuseType['id'].eq(tableAccountItem['refuseType_id']))
    table = table.leftJoin(tableAccount,
                           [tableAccount['id'].eq(tableAccountItem['master_id']),
                            tableAccount['deleted'].eq(0),
                            ]
                           )
    cond = []
    if personIdList:
        cond.append(tableEvent['execPerson_id'].inlist(personIdList))
    cond.append(tableEvent['deleted'].eq(0))
    cond.append(tableEvent['expose'].eq(1))
    cond.append(tableEvent['execDate'].isNotNull())
    if onlyDispCOVID or onlyResearchOnCOVID:
        tableEventType = db.table('EventType')
        table = table.leftJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
        if onlyDispCOVID:
            tableMAT = db.table('rbMedicalAidType')
            table = table.leftJoin(tableMAT, tableMAT['id'].eq(tableEventType['medicalAidType_id']))
            cond.append(tableMAT['regionalCode'].eq('233'))
        if onlyResearchOnCOVID:
            tableETI = db.table('EventType_Identification')
            tableAS = db.table('rbAccountingSystem')
            table = table.leftJoin(tableETI, tableETI['master_id'].eq(tableEventType['id']))
            table = table.leftJoin(tableAS, tableAS['id'].eq(tableETI['system_id']))
            cond.append(tableETI['value'].eq('av'))
            cond.append(tableETI['deleted'].eq(0))
            cond.append(tableAS['code'].eq('AccTFOMS'))
    if onlyTFOMS:
        tableClient = db.table('Client')
        tableClientPolicy = db.table('ClientPolicy')
        tableInsurer = db.table('Organisation').alias("Insurer")
        table = table.leftJoin(tableClient, tableClient['id'].eq(tableEvent['client_id']))
        table = table.leftJoin(tableClientPolicy, u"""ClientPolicy.id = COALESCE((SELECT MAX(cp2.id) 
                                                        FROM ClientPolicy cp2
                                                        WHERE cp2.client_id = Client.id AND cp2.deleted = 0 AND cp2.begDate =
      (select MAX(cp.begDate) from ClientPolicy cp
              WHERE cp.client_id = Client.id
                AND cp.policyType_id IN (1,2)
                AND cp.deleted = 0
                AND cp.begDate <= Event.execDate AND (cp.endDate is NULL OR cp.endDate >= DATE(Event.execDate)))),
     (SELECT MAX(cp2.id)
              FROM ClientPolicy cp2
              WHERE cp2.client_id = Client.id AND cp2.deleted = 0 AND cp2.begDate =
              (select MAX(cp.begDate)
                from ClientPolicy cp
                WHERE cp.client_id = Client.id
                AND cp.policyType_id IN (1,2)
                AND cp.deleted = 0
                AND cp.begDate BETWEEN Event.execDate AND ADDDATE(DATE(Event.execDate), 30)
                )),
    (SELECT MAX(cp2.id)
            FROM ClientPolicy cp2
            WHERE cp2.client_id = Event.relative_id AND cp2.deleted = 0 AND cp2.begDate =
            (select MAX(cp.begDate)
            from ClientPolicy cp
            WHERE cp.client_id = Event.relative_id
                AND cp.policyType_id IN (1,2)
                AND cp.deleted = 0
                AND cp.begDate <= Event.execDate AND (cp.endDate is NULL OR cp.endDate >= DATE(Event.execDate))
               )))""")
        table = table.leftJoin(tableInsurer, tableInsurer['id'].eq(tableClientPolicy['insurer_id']))
        cond.append("substr(Insurer.area, 1, 2) != '%s'" % QtGui.qApp.provinceKLADR()[:2])
    if contractDescr.exposeByLastEventContract:
        tableLastEvent = db.table('Event').alias('LastEvent')
        table = table.innerJoin(tableLastEvent, 'LastEvent.id=getLastEventId(Event.id)')
        cond.append(tableLastEvent['execDate'].ge(contractDescr.begDate))
        cond.append(tableLastEvent['execDate'].lt(contractDescr.endDate.addDays(1)))
        cond.append(tableLastEvent['execDate'].ge(begDate))
        cond.append(tableLastEvent['execDate'].lt(endDate.addDays(1)))
        cond.append(tableLastEvent['contract_id'].eq(contractDescr.id))
    else:
        cond.append(tableEvent['execDate'].ge(contractDescr.begDate))
        cond.append(tableEvent['execDate'].lt(contractDescr.endDate.addDays(1)))
        cond.append(tableEvent['execDate'].ge(begDate))
        cond.append(tableEvent['execDate'].lt(endDate.addDays(1)))


    cond.append(tableEvent['MES_id'].isNotNull())

    # c перевыставлением событий
    if reexpose:
        cond.append(db.joinOr(['(Event.payStatus&%s)=0' % contractDescr.payStatusMask, 
                    db.joinAnd([tableAccountItem['refuseType_id'].isNotNull(), 
                    tablePayRefuseType['rerun'].ne(0), 
                    tableAccountItem['reexposeItem_id'].isNull()])]))
    else:  # без перевыставления
        cond.append('(Event.payStatus&%s)=0' % contractDescr.payStatusMask)
        cond.append(tableAccountItem['id'].isNull())        

    if not contractDescr.exposeExternalServices:
        cond.append(tableEvent['org_id'].eq(QtGui.qApp.currentOrgId()))
    if contractDescr.exposeIfContinuedEventFinished:
        cond.append('isContinuedEventFinished(`Event`.`id`)')
    if contractDescr.specification:
        cond.append(tableEvent['eventType_id'].inlist(contractDescr.specification))
    if contractDescr.onlyInspectedEvents:
        cond.append(tableEvent['expertiseDate'].isNotNull())
        cond.append(tableEvent['expert_id'].isNotNull())
    cond.append(tableEvent['contract_id'].eq(contractDescr.id))

    return db.getIdList(table, idCol='Event.id', where=cond, order='Event.execDate, Event.client_id, Event.id')


def selectVisitsByActionServices(contractDescr, personIdList, date,  reexpose, onlyDispCOVID, onlyResearchOnCOVID):
    result = {}
    if not contractDescr.tariffVisitByActionService:
        return result
    financeId = contractDescr.financeId
    db = QtGui.qApp.db
    tableEvent = db.table('Event')
    tableVisit = db.table('Visit')
    tableAction = db.table('Action')
    tableAccountItem = db.table('Account_Item')
    tableAccount = db.table('Account')
    tableContract = db.table('Contract')
    tablePayRefuseType = db.table('rbPayRefuseType')
    table = tableVisit.leftJoin(tableEvent, tableVisit['event_id'].eq(tableEvent['id']))
    table = table.leftJoin(tableAccountItem, [ tableAccountItem['event_id'].eq(tableEvent['id']),
                                               tableAccountItem['visit_id'].eq(tableVisit['id']),
                                               tableAccountItem['action_id'].isNull(),
                                               tableAccountItem['eventCSG_id'].isNull(),
                                               tableAccountItem['deleted'].eq(0),
                                             ]
                               )
    table = table.leftJoin(tablePayRefuseType, tablePayRefuseType['id'].eq(tableAccountItem['refuseType_id']))
    table = table.leftJoin(tableAccount,
                           [tableAccount['id'].eq(tableAccountItem['master_id']),
                            tableAccount['deleted'].eq(0),
                           ]
                          )
    table = table.leftJoin(tableContract,
                           [tableContract['id'].eq(tableAccount['contract_id']),
                            tableContract['deleted'].eq(0),
                            tableContract['finance_id'].eq(financeId)
                           ]
                          )

    for serviceId, tariffList in contractDescr.tariffVisitByActionService.items():
        cond = [tableEvent['deleted'].eq(0),
                tableEvent['expose'].eq(1),
                tableVisit['deleted'].eq(0),
                'DATE(Visit.date)>=DATE(Event.setDate)'
               ]
        if onlyDispCOVID or onlyResearchOnCOVID:
            tableEventType = db.table('EventType')
            table = table.leftJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
            if onlyDispCOVID:
                tableMAT = db.table('rbMedicalAidType')
                table = table.leftJoin(tableMAT, tableMAT['id'].eq(tableEventType['medicalAidType_id']))
                cond.append(tableMAT['regionalCode'].eq('233'))
            if onlyResearchOnCOVID:
                tableETI = db.table('EventType_Identification')
                tableAS = db.table('rbAccountingSystem')
                table = table.leftJoin(tableETI, tableETI['master_id'].eq(tableEventType['id']))
                table = table.leftJoin(tableAS, tableAS['id'].eq(tableETI['system_id']))
                cond.append(tableETI['value'].eq('av'))
                cond.append(tableETI['deleted'].eq(0))
                cond.append(tableAS['code'].eq('AccTFOMS'))
        if contractDescr.specification:
            cond.append(tableEvent['eventType_id'].inlist(contractDescr.specification))
        if contractDescr.onlyInspectedEvents:
            cond.append(tableEvent['expertiseDate'].isNotNull())
            cond.append(tableEvent['expert_id'].isNotNull())
        cond.append(tableVisit['deleted'].eq(0))
        if contractDescr.dateOfVisitExposition == 0:
            # 0 - событие не закончено, визит в договоре
            cond.append(tableVisit['date'].dateBetween(contractDescr.begDate, contractDescr.endDate))
        elif contractDescr.dateOfVisitExposition == 1:
            # 1 - событие закончено, визит в договоре
            cond.append(tableEvent['execDate'].lt(date))
            cond.append(tableEvent['execDate'].ge(QDate(1, 1, 1)))
            cond.append(tableVisit['date'].dateBetween(contractDescr.begDate, contractDescr.endDate))
        else:
            # 2 - событие закончено, дата окончения события в договоре
            cond.append(tableEvent['execDate'].lt(date))
            cond.append(tableEvent['execDate'].dateBetween(contractDescr.begDate, contractDescr.endDate))

        cond.append(tableVisit['date'].lt(date)) # есть сомнение
        
        #Выборка событий только за последние 3 мес. от расчетной даты 
        if QtGui.qApp.defaultKLADR()[:2] == u'23':
            cond.append(tableEvent['execDate'].ge(firstMonthDay(date).addMonths(-3)))
            
        eventTypeIdList = [tariff.eventTypeId for tariff in tariffList if tariff.eventTypeId]
        if eventTypeIdList:
            cond.append(tableEvent['eventType_id'].inlist(eventTypeIdList))
        actionCond = [ tableAction['deleted'].eq(0),
                       tableAction['event_id'].eq(tableVisit['event_id']),
                       tableVisit['date'].ge(tableAction['begDate']),
                       tableVisit['date'].le(tableAction['endDate']),
#                      очень сложное условие, см. ниже
                       ('IF(EXISTS(SELECT 1 FROM ActionType_Service WHERE ActionType_Service.master_id=Action.actionType_id AND ActionType_Service.finance_id=%(financeId)d), \
                         EXISTS(SELECT 1 FROM ActionType_Service WHERE ActionType_Service.master_id=Action.actionType_id AND ActionType_Service.finance_id=%(financeId)d AND ActionType_Service.service_id=%(serviceId)d), \
                         EXISTS(SELECT 1 FROM ActionType_Service WHERE ActionType_Service.master_id=Action.actionType_id AND ActionType_Service.finance_id IS NULL AND ActionType_Service.service_id=%(serviceId)d))'
                       ) % {'financeId':financeId, 'serviceId':serviceId}
                     ]
        cond.append(db.existsStmt(tableAction, actionCond))
        cond.append(tableVisit['finance_id'].eq(financeId))
        
        #c перевыставлением событий
        if reexpose:
            cond.append(db.joinOr(['(Visit.payStatus&%s)=0' % contractDescr.payStatusMask, 
                        db.joinAnd([tableAccountItem['refuseType_id'].isNotNull(), 
                        tablePayRefuseType['rerun'].ne(0), 
                        tableAccountItem['reexposeItem_id'].isNull()])]))
        else: #без перевыставления
            cond.append('(Visit.payStatus&%s)=0' % contractDescr.payStatusMask)       
        
        if personIdList is not None:
            if contractDescr.visitExposition:
                cond.append(tableVisit['person_id'].inlist(personIdList))
            else:
                cond.append(tableEvent['execPerson_id'].inlist(personIdList))
#        cond.append(tableContract['id'].isNull())
        visitIdList = db.getIdList(table, idCol='Visit.id', where=cond, order='Visit.date, Event.client_id, Visit.id')
        result[serviceId] = visitIdList
    return result


def selectVisits(contractDescr, personIdList, begDate, endDate, reexpose, onlyDispCOVID, onlyResearchOnCOVID, onlyTFOMS):
    if not contractDescr.tariffByVisitService:
        return []
    db = QtGui.qApp.db
    tableEvent = db.table('Event')
    tableVisit = db.table('Visit')
    tableEventContract = db.table('Contract').alias('EventContract')
    tableAccountItem = db.table('Account_Item')
    tableAccount = db.table('Account')
    tablePayRefuseType = db.table('rbPayRefuseType')
    table = tableVisit.innerJoin(tableEvent, tableVisit['event_id'].eq(tableEvent['id']))
    table = table.leftJoin(tableEventContract, tableEventContract['id'].eq(tableEvent['contract_id']))
    table = table.leftJoin(tableAccountItem, [tableAccountItem['event_id'].eq(tableVisit['event_id']),
                                              tableAccountItem['visit_id'].eq(tableVisit['id']),
                                              tableAccountItem['action_id'].isNull(),
                                              tableAccountItem['eventCSG_id'].isNull(),
                                              tableAccountItem['deleted'].eq(0),
                                              ]
                           )
    table = table.leftJoin(tablePayRefuseType, tablePayRefuseType['id'].eq(tableAccountItem['refuseType_id']))
    table = table.leftJoin(tableAccount,
                           [tableAccount['id'].eq(tableAccountItem['master_id']),
                            tableAccount['deleted'].eq(0),
                            ]
                           )

    cond = [tableEvent['deleted'].eq(0),
            tableEvent['expose'].eq(1),
            tableVisit['deleted'].eq(0),
            'DATE(Visit.date)>=DATE(Event.setDate)'
            ]
    if onlyDispCOVID or onlyResearchOnCOVID:
        tableEventType = db.table('EventType')
        table = table.leftJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
        if onlyDispCOVID:
            tableMAT = db.table('rbMedicalAidType')
            table = table.leftJoin(tableMAT, tableMAT['id'].eq(tableEventType['medicalAidType_id']))
            cond.append(tableMAT['regionalCode'].eq('233'))
        if onlyResearchOnCOVID:
            tableETI = db.table('EventType_Identification')
            tableAS = db.table('rbAccountingSystem')
            table = table.leftJoin(tableETI, tableETI['master_id'].eq(tableEventType['id']))
            table = table.leftJoin(tableAS, tableAS['id'].eq(tableETI['system_id']))
            cond.append(tableETI['value'].eq('av'))
            cond.append(tableETI['deleted'].eq(0))
            cond.append(tableAS['code'].eq('AccTFOMS'))
    if onlyTFOMS:
        tableClient = db.table('Client')
        tableClientPolicy = db.table('ClientPolicy')
        tableInsurer = db.table('Organisation').alias("Insurer")
        table = table.leftJoin(tableClient, tableClient['id'].eq(tableEvent['client_id']))
        table = table.leftJoin(tableClientPolicy, u"""ClientPolicy.id = COALESCE((SELECT MAX(cp2.id) 
                                                        FROM ClientPolicy cp2
                                                        WHERE cp2.client_id = Client.id AND cp2.deleted = 0 AND cp2.begDate =
      (select MAX(cp.begDate) from ClientPolicy cp
              WHERE cp.client_id = Client.id
                AND cp.policyType_id IN (1,2)
                AND cp.deleted = 0
                AND cp.begDate <= Event.execDate AND (cp.endDate is NULL OR cp.endDate >= DATE(Event.execDate)))),
     (SELECT MAX(cp2.id)
              FROM ClientPolicy cp2
              WHERE cp2.client_id = Client.id AND cp2.deleted = 0 AND cp2.begDate =
              (select MAX(cp.begDate)
                from ClientPolicy cp
                WHERE cp.client_id = Client.id
                AND cp.policyType_id IN (1,2)
                AND cp.deleted = 0
                AND cp.begDate BETWEEN Event.execDate AND ADDDATE(DATE(Event.execDate), 30)
                )),
    (SELECT MAX(cp2.id)
            FROM ClientPolicy cp2
            WHERE cp2.client_id = Event.relative_id AND cp2.deleted = 0 AND cp2.begDate =
            (select MAX(cp.begDate)
            from ClientPolicy cp
            WHERE cp.client_id = Event.relative_id
                AND cp.policyType_id IN (1,2)
                AND cp.deleted = 0
                AND cp.begDate <= Event.execDate AND (cp.endDate is NULL OR cp.endDate >= DATE(Event.execDate))
               )))""")
        table = table.leftJoin(tableInsurer, tableInsurer['id'].eq(tableClientPolicy['insurer_id']))
        cond.append("substr(Insurer.area, 1, 2) != '%s'" % QtGui.qApp.provinceKLADR()[:2])
    if contractDescr.specification:
        cond.append(tableEvent['eventType_id'].inlist(contractDescr.specification))
    if contractDescr.onlyInspectedEvents:
        cond.append(tableEvent['expertiseDate'].isNotNull())
        cond.append(tableEvent['expert_id'].isNotNull())
    if contractDescr.dateOfVisitExposition == 0:
        # 0 - событие не закончено, визит в договоре
        cond.append(tableVisit['date'].ge(contractDescr.begDate))
        cond.append(tableVisit['date'].lt(contractDescr.endDate.addDays(1)))
    elif contractDescr.dateOfVisitExposition == 1:
        # 1 - событие закончено, визит в договоре
        cond.append(tableEvent['execDate'].lt(endDate.addDays(1)))
        cond.append(tableVisit['date'].ge(contractDescr.begDate))
        cond.append(tableVisit['date'].lt(contractDescr.endDate.addDays(1)))
    else:
        # 2 - событие закончено, дата окончания события в договоре
        cond.append(tableEvent['execDate'].lt(endDate.addDays(1)))
        cond.append(tableEvent['execDate'].ge(contractDescr.begDate))
        cond.append(tableEvent['execDate'].lt(contractDescr.endDate.addDays(1)))

    cond.append(tableEvent['execDate'].ge(begDate))
    cond.append(tableEvent['execDate'].lt(endDate.addDays(1)))

    cond.append(tableVisit['service_id'].inlist(contractDescr.tariffByVisitService.keys()))

    cond.append(db.if_(tableVisit['finance_id'].eq(tableEventContract['finance_id']),
                       tableEvent['contract_id'].eq(contractDescr.id),
                       tableVisit['finance_id'].eq(contractDescr.financeId)))
    
    # с перевыставлением событий
    if reexpose:
        cond.append(db.joinOr(['(Visit.payStatus&%s)=0' % contractDescr.payStatusMask, 
                    db.joinAnd([tableAccountItem['refuseType_id'].isNotNull(), 
                                tablePayRefuseType['rerun'].ne(0),
                                tableAccountItem['reexposeItem_id'].isNull()])]))
    else:  # без перевыставления
        cond.append('(Visit.payStatus&%s)=0' % contractDescr.payStatusMask)
        cond.append(tableAccountItem['id'].isNull())
        
    if personIdList is not None:
        if contractDescr.visitExposition:
            cond.append(tableVisit['person_id'].inlist(personIdList))
        else:
            cond.append(tableEvent['execPerson_id'].inlist(personIdList))

    return db.getIdList(table, idCol='Visit.id', where=cond, order='Visit.date, Event.client_id, Visit.id')


def selectCsgs(contractDescr, personIdList, begDate, endDate, reexpose, onlyDispCOVID, onlyResearchOnCOVID, onlyTFOMS):
    if not contractDescr.tariffEventByMES and not contractDescr.tariffByCSG:
        return []
    financeId = contractDescr.financeId
    db = QtGui.qApp.db
    tableEvent = db.table('Event')
    tableCsg = db.table('Event_CSG')
    tableService = db.table('rbService')
    tableEventContract = db.table('Contract').alias('EventContract')
    tableAccountItem = db.table('Account_Item')
    tablePayRefuseType = db.table('rbPayRefuseType')
    tableAccount = db.table('Account')
    tableContract = db.table('Contract')
    table = tableCsg.innerJoin(tableEvent, tableCsg['master_id'].eq(tableEvent['id']))
    table = table.innerJoin(tableService, tableService['code'].eq(tableCsg['CSGCode']))
    table = table.leftJoin(tableEventContract, tableEventContract['id'].eq(tableEvent['contract_id']))
    table = table.leftJoin(tableAccountItem, [ tableAccountItem['event_id'].eq(tableCsg['master_id']),
                                               tableAccountItem['visit_id'].isNull(),
                                               tableAccountItem['action_id'].isNull(),
                                               tableAccountItem['eventCSG_id'].eq(tableCsg['id']),
                                               tableAccountItem['deleted'].eq(0),
                                             ]
                          )
    table = table.leftJoin(tablePayRefuseType, tablePayRefuseType['id'].eq(tableAccountItem['refuseType_id']))
    table = table.leftJoin(tableAccount,
                           [tableAccount['id'].eq(tableAccountItem['master_id']),
                            tableAccount['deleted'].eq(0),
                            ]
                           )
    table = table.leftJoin(tableContract,
                           [tableContract['id'].eq(tableAccount['contract_id']),
                            tableContract['deleted'].eq(0),
                            tableContract['finance_id'].eq(financeId)
                            ]
                           )

    cond = [tableEvent['deleted'].eq(0),
            tableEvent['expose'].eq(1)
            ]
    if personIdList:
        cond.append(tableEvent['execPerson_id'].inlist(personIdList))
    if onlyDispCOVID or onlyResearchOnCOVID:
        tableEventType = db.table('EventType')
        table = table.leftJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
        if onlyDispCOVID:
            tableMAT = db.table('rbMedicalAidType')
            table = table.leftJoin(tableMAT, tableMAT['id'].eq(tableEventType['medicalAidType_id']))
            cond.append(tableMAT['regionalCode'].eq('233'))
        if onlyResearchOnCOVID:
            tableETI = db.table('EventType_Identification')
            tableAS = db.table('rbAccountingSystem')
            table = table.leftJoin(tableETI, tableETI['master_id'].eq(tableEventType['id']))
            table = table.leftJoin(tableAS, tableAS['id'].eq(tableETI['system_id']))
            cond.append(tableETI['value'].eq('av'))
            cond.append(tableETI['deleted'].eq(0))
            cond.append(tableAS['code'].eq('AccTFOMS'))
    if onlyTFOMS:
        tableClient = db.table('Client')
        tableClientPolicy = db.table('ClientPolicy')
        tableInsurer = db.table('Organisation').alias("Insurer")
        table = table.leftJoin(tableClient, tableClient['id'].eq(tableEvent['client_id']))
        table = table.leftJoin(tableClientPolicy, u"""ClientPolicy.id = COALESCE((SELECT MAX(cp2.id) 
                                                        FROM ClientPolicy cp2
                                                        WHERE cp2.client_id = Client.id AND cp2.deleted = 0 AND cp2.begDate =
      (select MAX(cp.begDate) from ClientPolicy cp
              WHERE cp.client_id = Client.id
                AND cp.policyType_id IN (1,2)
                AND cp.deleted = 0
                AND cp.begDate <= Event.execDate AND (cp.endDate is NULL OR cp.endDate >= DATE(Event.execDate)))),
     (SELECT MAX(cp2.id)
              FROM ClientPolicy cp2
              WHERE cp2.client_id = Client.id AND cp2.deleted = 0 AND cp2.begDate =
              (select MAX(cp.begDate)
                from ClientPolicy cp
                WHERE cp.client_id = Client.id
                AND cp.policyType_id IN (1,2)
                AND cp.deleted = 0
                AND cp.begDate BETWEEN Event.execDate AND ADDDATE(DATE(Event.execDate), 30)
                )),
    (SELECT MAX(cp2.id)
            FROM ClientPolicy cp2
            WHERE cp2.client_id = Event.relative_id AND cp2.deleted = 0 AND cp2.begDate =
            (select MAX(cp.begDate)
            from ClientPolicy cp
            WHERE cp.client_id = Event.relative_id
                AND cp.policyType_id IN (1,2)
                AND cp.deleted = 0
                AND cp.begDate <= Event.execDate AND (cp.endDate is NULL OR cp.endDate >= DATE(Event.execDate))
               )))""")
        table = table.leftJoin(tableInsurer, tableInsurer['id'].eq(tableClientPolicy['insurer_id']))
        cond.append("substr(Insurer.area, 1, 2) != '%s'" % QtGui.qApp.provinceKLADR()[:2])
    if contractDescr.specification:
        cond.append(tableEvent['eventType_id'].inlist(contractDescr.specification))
    if contractDescr.onlyInspectedEvents:
        cond.append(tableEvent['expertiseDate'].isNotNull())
        cond.append(tableEvent['expert_id'].isNotNull())
    if contractDescr.dateOfCsgExposition == 0:
        # 0 - событие не закончено, дата КСГ договоре
        cond.append(tableCsg['endDate'].ge(contractDescr.begDate))
        cond.append(tableCsg['endDate'].lt(contractDescr.endDate.addDays(1)))
    elif contractDescr.dateOfActionExposition == 1:
        # 1 - событие закончено, дата действия в договоре
        cond.append(tableEvent['execDate'].lt(endDate.addDays(1)))
        cond.append(tableCsg['endDate'].ge(contractDescr.begDate))
        cond.append(tableCsg['endDate'].lt(contractDescr.endDate.addDays(1)))
    else:
        # 2 - событие закончено, дата окончания события в договоре
        cond.append(tableEvent['execDate'].lt(endDate.addDays(1)))
        cond.append(tableEvent['execDate'].ge(contractDescr.begDate))
        cond.append(tableEvent['execDate'].lt(contractDescr.endDate.addDays(1)))

    cond.append(tableEvent['execDate'].ge(begDate))
    cond.append(tableEvent['execDate'].lt(endDate.addDays(1)))

    contractCond = [tableEvent['contract_id'].eq(contractDescr.id),
                    db.joinAnd([tableEvent['contract_id'].isNull(),
                                db.joinOr([tableContract['finance_id'].eq(contractDescr.financeId),
                                           tableContract['finance_id'].isNull()
                                           ]),
                                'isClientInContractContingent(%d, Event.client_id, Event.setDate, %s, %s)' % (contractDescr.id, quote(QtGui.qApp.defaultKLADR()), quote(QtGui.qApp.provinceKLADR()))
                                ]),
                    ]
    cond.append(db.joinOr(contractCond))
    # с перевыставлением событий
    if reexpose:
        cond.append(db.joinOr(['(Event_CSG.payStatus&%s)=0' % contractDescr.payStatusMask, db.joinAnd(
            [tableAccountItem['refuseType_id'].isNotNull(), tablePayRefuseType['rerun'].ne(0),
             tableAccountItem['reexposeItem_id'].isNull()])]))
    else:  # без перевыставления
        cond.append(tableAccountItem['id'].isNull())
        cond.append('(Event_CSG.payStatus&%s)=0' % contractDescr.payStatusMask)

    # cond.append(tableContract['id'].isNull())
    return db.getDistinctIdList(table, idCol='Event_CSG.id', where=cond, order='Event_CSG.begDate, Event.client_id, Event_CSG.id')


def selectActions(contractDescr, personIdList, begDate, endDate, reexpose, onlyDispCOVID, onlyResearchOnCOVID, onlyTFOMS):
    from Events.ActionStatus import CActionStatus

    if not contractDescr.tariffByActionService:
        return []
        
    db = QtGui.qApp.db
    tableEvent = db.table('Event')
    tableAction = db.table('vAction').alias('Action')
    tableAccountItem = db.table('Account_Item')
    tablePayRefuseType = db.table('rbPayRefuseType')
    tableEventType = db.table('EventType')
    tableMT = db.table('rbMedicalAidType')
    table = tableEvent.innerJoin(tableAction, tableEvent['id'].eq(tableAction['event_id']))
    table = table.leftJoin(tableAccountItem, [tableAccountItem['event_id'].eq(tableEvent['id']),
                                              tableAccountItem['action_id'].eq(tableAction['id']),
                                              tableAccountItem['deleted'].eq(0),
                                              ]
                           )
    table = table.leftJoin(tablePayRefuseType, tablePayRefuseType['id'].eq(tableAccountItem['refuseType_id']))
    table = table.leftJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
    table = table.leftJoin(tableMT, tableMT['id'].eq(tableEventType['medicalAidType_id']))
    cond = [tableEvent['deleted'].eq(0),
            tableEvent['expose'].eq(1),
            tableAction['deleted'].eq(0)
            ]
    if onlyDispCOVID or onlyResearchOnCOVID:
        # tableEventType = db.table('EventType')
        # table = table.leftJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
        if onlyDispCOVID:
            # tableMAT = db.table('rbMedicalAidType')
            # table = table.leftJoin(tableMAT, tableMAT['id'].eq(tableEventType['medicalAidType_id']))
            cond.append(tableMT['regionalCode'].eq('233'))
        if onlyResearchOnCOVID:
            tableETI = db.table('EventType_Identification')
            tableAS = db.table('rbAccountingSystem')
            table = table.leftJoin(tableETI, tableETI['master_id'].eq(tableEventType['id']))
            table = table.leftJoin(tableAS, tableAS['id'].eq(tableETI['system_id']))
            cond.append(tableETI['value'].eq('av'))
            cond.append(tableETI['deleted'].eq(0))
            cond.append(tableAS['code'].eq('AccTFOMS'))
    if onlyTFOMS:
        tableClient = db.table('Client')
        tableClientPolicy = db.table('ClientPolicy')
        tableInsurer = db.table('Organisation').alias("Insurer")
        table = table.leftJoin(tableClient, tableClient['id'].eq(tableEvent['client_id']))
        table = table.leftJoin(tableClientPolicy, u"""ClientPolicy.id = COALESCE((SELECT MAX(cp2.id) 
                                                      FROM ClientPolicy cp2
                                                      WHERE cp2.client_id = Client.id AND cp2.deleted = 0 AND cp2.begDate =
    (select MAX(cp.begDate) from ClientPolicy cp
            WHERE cp.client_id = Client.id
              AND cp.policyType_id IN (1,2)
              AND cp.deleted = 0
              AND cp.begDate <= Event.execDate AND (cp.endDate is NULL OR cp.endDate >= DATE(Event.execDate)))),
   (SELECT MAX(cp2.id)
            FROM ClientPolicy cp2
            WHERE cp2.client_id = Client.id AND cp2.deleted = 0 AND cp2.begDate =
            (select MAX(cp.begDate)
              from ClientPolicy cp
              WHERE cp.client_id = Client.id
              AND cp.policyType_id IN (1,2)
              AND cp.deleted = 0
              AND cp.begDate BETWEEN Event.execDate AND ADDDATE(DATE(Event.execDate), 30)
              )),
  (SELECT MAX(cp2.id)
          FROM ClientPolicy cp2
          WHERE cp2.client_id = Event.relative_id AND cp2.deleted = 0 AND cp2.begDate =
          (select MAX(cp.begDate)
          from ClientPolicy cp
          WHERE cp.client_id = Event.relative_id
              AND cp.policyType_id IN (1,2)
              AND cp.deleted = 0
              AND cp.begDate <= Event.execDate AND (cp.endDate is NULL OR cp.endDate >= DATE(Event.execDate))
             )))""")
        table = table.leftJoin(tableInsurer, tableInsurer['id'].eq(tableClientPolicy['insurer_id']))
        cond.append("substr(Insurer.area, 1, 2) != '%s'" % QtGui.qApp.provinceKLADR()[:2])
    # для КК отключаем это условие, чтобы услуги, оказанные ранее попадали в счет с нулевой ценой
    if QtGui.qApp.defaultKLADR()[:2] != u'23':
        cond.append('DATE(Action.exposeDate) >= DATE(Event.setDate)')

    if not contractDescr.exposeExternalServices:
        cond.append('COALESCE(Action.org_id, Event.org_id, %d)=%d' % (QtGui.qApp.currentOrgId(), QtGui.qApp.currentOrgId()))
    if contractDescr.specification:
        cond.append(tableEvent['eventType_id'].inlist(contractDescr.specification))
        
    # condStr = 'isClientInContractContingent(%d, Event.client_id, Event.setDate, %s, %s)'
        
    contractCond = [tableAction['contract_id'].eq(contractDescr.id),
                    db.joinAnd([tableAction['contract_id'].isNull(),
                                tableEvent['contract_id'].eq(contractDescr.id),
                                db.joinOr([tableAction['finance_id'].eq(contractDescr.financeId),
                                           tableAction['finance_id'].isNull()
                                           ]),
                                ]),
                    ]
    cond.append(db.joinOr(contractCond))
    if contractDescr.dateOfActionExposition == 0:
        # 0 - событие не закончено, дата действия в договоре
        cond.append(db.joinOr([
            db.joinAnd([
                db.if_(
                    db.joinAnd([tableAction['status'].eq(CActionStatus.refused), tableMT['regionalCode'].inlist(['211', '261', '233', '244', '232', '252', '262'])]),
                    tableAction['begDate'].ge(contractDescr.begDate),
                    tableAction['exposeDate'].ge(contractDescr.begDate)
                ),
                db.if_(
                    db.joinAnd([tableAction['status'].eq(CActionStatus.refused), tableMT['regionalCode'].inlist(['211', '261', '233', '244', '232', '252', '262'])]),
                    tableAction['begDate'].lt(contractDescr.endDate.addDays(1)),
                    tableAction['exposeDate'].lt(contractDescr.endDate.addDays(1))
                )
            ]),
            tableAction['contract_id'].eq(contractDescr.id)
        ])
        )
    elif contractDescr.dateOfActionExposition == 1:
        # 1 - событие закончено, дата действия в договоре
        cond.append(tableEvent['execDate'].lt(endDate.addDays(1)))
        # cond.append(tableAction['exposeDate'].ge(contractDescr.begDate))
        # cond.append(tableAction['exposeDate'].lt(contractDescr.endDate.addDays(1)))

        cond.append(db.if_(
            db.joinAnd([tableAction['status'].eq(CActionStatus.refused), tableMT['regionalCode'].inlist(['211', '261', '233', '244', '232', '252', '262'])]),
            tableAction['begDate'].ge(contractDescr.begDate),
            tableAction['exposeDate'].ge(contractDescr.begDate)
        ))
        cond.append(db.if_(
            db.joinAnd([tableAction['status'].eq(CActionStatus.refused), tableMT['regionalCode'].inlist(['211', '261', '233', '244', '232', '252', '262'])]),
            tableAction['begDate'].lt(contractDescr.endDate.addDays(1)),
            tableAction['exposeDate'].lt(contractDescr.endDate.addDays(1))
        ))
    else:
        # 2 - событие закончено, дата окончания события в договоре
        cond.append(tableEvent['execDate'].lt(endDate.addDays(1)))
        cond.append(tableEvent['execDate'].ge(contractDescr.begDate))
        cond.append(tableEvent['execDate'].lt(contractDescr.endDate.addDays(1)))

    subCond = [tableAction['status'].eq(CActionStatus.finished),
               db.joinAnd([tableAction['status'].eq(CActionStatus.withoutResult),
                           tableAction['takenTissueJournal_id'].isNotNull(),
                           ]),
               db.joinAnd([tableAction['status'].eq(CActionStatus.refused),
                           tableMT['regionalCode'].inlist(['211', '261', '233', '244', '232', '252', '262'])
                           ])
               ]
    cond.append(db.joinOr(subCond))

    # с перевыставлением событий
    if reexpose:
        cond.append(db.joinOr(['(Action.payStatus&%s)=0' % contractDescr.payStatusMask, 
                    db.joinAnd([tableAccountItem['refuseType_id'].isNotNull(), 
                                tablePayRefuseType['rerun'].ne(0),
                                tableAccountItem['reexposeItem_id'].isNull()])]))
    else:  # без перевыставления
        cond.append('(Action.payStatus&%s)=0' % contractDescr.payStatusMask)
        cond.append(tableAccountItem['id'].isNull())

    # фильтр наличия номенклатурной услуги
    cond.append("""EXISTS(SELECT NULL FROM ActionType_Service ats
                      WHERE ats.master_id = Action.actionType_id
                      AND ats.service_id is not null 
                      and (ats.finance_id = %d or ats.finance_id is null))""" % contractDescr.financeId)
    if personIdList:
        if contractDescr.actionExposition:
            cond.append(tableAction['person_id'].inlist(personIdList))
        else:
            cond.append(tableEvent['execPerson_id'].inlist(personIdList))

    cond.append(tableEvent['execDate'].ge(begDate))
    cond.append(tableEvent['execDate'].lt(endDate.addDays(1)))

    return db.getIdList(table, idCol='Action.id', where=cond, order='Action.exposeDate, Event.client_id, Action.id')


def selectHospitalBedActionProperties(contractDescr, personIdList, date, reexpose, onlyDispCOVID, onlyResearchOnCOVID):
    # недостатки:
    # 1) Неправильно обработается ситуация с многократным употреблением свойства типа HospitalBed в действии
    #    Полагаю, что это практически не должно применяться
    # 2) Неправильно обработается ситуация с векторным свойством типа HospitalBed в действии
    #    Таких пока нет
    if not contractDescr.tariffByHospitalBedService:
        return []
    financeId = contractDescr.financeId
    db = QtGui.qApp.db
    tableEvent = db.table('Event')
#    tableAction = db.table('Action')
    tableAction = db.table('vAction').alias('Action')
    tableActionPropertyHospitalBed = db.table('ActionProperty_HospitalBed')
    tableActionProperty = db.table('ActionProperty')
    tableAccountItem = db.table('Account_Item')
    tableAccount = db.table('Account')
    tableContract = db.table('Contract')
    tablePayRefuseType = db.table('rbPayRefuseType')
    table = tableActionPropertyHospitalBed.leftJoin(tableActionProperty, tableActionProperty['id'].eq(tableActionPropertyHospitalBed['id']))
    table = table.leftJoin(tableAction, tableAction['id'].eq(tableActionProperty['action_id']))
    table = table.leftJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
    table = table.leftJoin(tableAccountItem, [ tableAccountItem['event_id'].eq(tableEvent['id']),
                                               tableAccountItem['visit_id'].isNull(),
                                               tableAccountItem['action_id'].eq(tableAction['id']),
                                               tableAccountItem['deleted'].eq(0),
                                             ]
                               )
    table = table.leftJoin(tablePayRefuseType, tablePayRefuseType['id'].eq(tableAccountItem['refuseType_id']))
    table = table.leftJoin(tableAccount,
                           [tableAccount['id'].eq(tableAccountItem['master_id']),
                            tableAccount['deleted'].eq(0),
                           ]
                          )
    table = table.leftJoin(tableContract,
                           [tableContract['id'].eq(tableAccount['contract_id']),
                            tableContract['deleted'].eq(0),
                            tableContract['finance_id'].eq(financeId)
                           ]
                          )
    cond = [tableEvent['deleted'].eq(0),
            tableEvent['expose'].eq(1),
            tableAction['deleted'].eq(0),
            'DATE(Action.exposeDate)>=DATE(Event.setDate)'
           ]
    if onlyDispCOVID or onlyResearchOnCOVID:
        tableEventType = db.table('EventType')
        table = table.leftJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
        if onlyDispCOVID:
            tableMAT = db.table('rbMedicalAidType')
            table = table.leftJoin(tableMAT, tableMAT['id'].eq(tableEventType['medicalAidType_id']))
            cond.append(tableMAT['regionalCode'].eq('233'))
        if onlyResearchOnCOVID:
            tableETI = db.table('EventType_Identification')
            tableAS = db.table('rbAccountingSystem')
            table = table.leftJoin(tableETI, tableETI['master_id'].eq(tableEventType['id']))
            table = table.leftJoin(tableAS, tableAS['id'].eq(tableETI['system_id']))
            cond.append(tableETI['value'].eq('av'))
            cond.append(tableETI['deleted'].eq(0))
            cond.append(tableAS['code'].eq('AccTFOMS'))
    #Выборка событий только за последние 3 мес. от расчетной даты 
    if QtGui.qApp.defaultKLADR()[:2] == u'23':
        cond.append(tableEvent['execDate'].ge(firstMonthDay(date).addMonths(-3)))
        
    if not contractDescr.exposeExternalServices:
        cond.append('COALESCE(Action.org_id, Event.org_id, %d)=%d' % (QtGui.qApp.currentOrgId(), QtGui.qApp.currentOrgId()))
    if contractDescr.specification:
        cond.append(tableEvent['eventType_id'].inlist(contractDescr.specification))
        
    condStr = 'isClientInContractContingent(%d, Event.client_id, Event.setDate, %s, %s)'
    
    if contractDescr.onlyInspectedEvents:
        cond.append(tableEvent['expertiseDate'].isNotNull())
        cond.append(tableEvent['expert_id'].isNotNull())    
    contractCond = [tableAction['contract_id'].eq(contractDescr.id),
                    db.joinAnd([tableAction['contract_id'].isNull(),
                                db.joinOr([tableAction['finance_id'].eq(contractDescr.financeId),
                                           tableAction['finance_id'].isNull()
                                          ]),
                                condStr % ( contractDescr.id, quote(QtGui.qApp.defaultKLADR()), quote(QtGui.qApp.provinceKLADR()) )
                               ]),
                   ]
    cond.append(db.joinOr(contractCond))
    if contractDescr.dateOfActionExposition == 0:
        # 0 - событие не закончено, дата действия в договоре
        cond.append(db.joinOr([tableAction['exposeDate'].dateBetween(contractDescr.begDate, contractDescr.endDate),
                               tableAction['contract_id'].eq(contractDescr.id),
                              ]
                             )
                   )
    elif contractDescr.dateOfActionExposition == 1:
        # 1 - событие закончено, дата действия в договоре
        cond.append(tableEvent['execDate'].lt(date))
        cond.append(tableEvent['execDate'].ge(QDate(1, 1, 1)))
        cond.append(tableAction['exposeDate'].dateBetween(contractDescr.begDate, contractDescr.endDate))
    else:
        # 2 - событие закончено, дата окончения события в договоре
        cond.append(tableEvent['execDate'].lt(date))
        cond.append(tableEvent['execDate'].dateBetween(contractDescr.begDate, contractDescr.endDate))
    cond.append(tableAction['exposeDate'].lt(date)) # или endDate?
    
    #c перевыставлением событий
    if reexpose:
        cond.append(db.joinOr(['(Action.payStatus&%s)=0' % contractDescr.payStatusMask, 
                    db.joinAnd([tableAccountItem['refuseType_id'].isNotNull(), 
                    tablePayRefuseType['rerun'].ne(0), 
                    tableAccountItem['reexposeItem_id'].isNull()])]))
    else: #без перевыставления
        cond.append('(Action.payStatus&%s)=0' % contractDescr.payStatusMask)       
        
    # cond.append(tableAction['expose'].ne(0))
    cond.append(tableActionProperty['deleted'].eq(0))
    cond.append(tableActionPropertyHospitalBed['value'].isNotNull())
    if personIdList is not None:
        if contractDescr.actionExposition:
            cond.append(tableAction['person_id'].inlist(personIdList))
        else:
            cond.append(tableEvent['execPerson_id'].inlist(personIdList))

#    cond.append(tableContract['id'].isNull())
    return db.getIdList(
        table, idCol='ActionProperty.id', where=cond, order='Action.endDate, Event.client_id, Action.id')


def selectEventServicePairsForVisits(contractDescr, personIdList, date):
    # возвращает список пар (eventId, serviceId)
    # для выставления совокупности визитов одного события принадлежащих одной услуге
    if not contractDescr.tariffCoupleVisits:
        return []
    db = QtGui.qApp.db
    tableEvent = db.table('Event')
    tableVisit = db.table('Visit')
    table = tableVisit.leftJoin(tableEvent, tableEvent['id'].eq(tableVisit['event_id']))
    if contractDescr.exposeByLastEventContract:
        tableLastEvent = db.table('Event').alias('LastEvent')
        table = table.innerJoin(tableLastEvent, 'LastEvent.id=getLastEventId(Event.id)')

    cond = [ tableVisit['deleted'].eq(0),
             '(Visit.payStatus&%s)=0' % contractDescr.payStatusMask,
             tableEvent['deleted'].eq(0),
             tableEvent['expose'].eq(1),
             tableEvent['execDate'].isNotNull(),
           ]
    #Выборка событий только за последние 3 мес. от расчетной даты 
    if QtGui.qApp.defaultKLADR()[:2] == u'23':
        cond.append(tableEvent['execDate'].ge(firstMonthDay(date).addMonths(-3)))
        
    if personIdList is not None:
        cond.append(table['execPerson_id'].inlist(personIdList))
    if contractDescr.exposeIfContinuedEventFinished:
        cond.append('isContinuedEventFinished(`Event`.`id`)')
    if contractDescr.specification:
        cond.append(tableEvent['eventType_id'].inlist(contractDescr.specification))
    if contractDescr.onlyInspectedEvents:
        cond.append(tableEvent['expertiseDate'].isNotNull())
        cond.append(tableEvent['expert_id'].isNotNull())
    condPart2 = []
    for eventTypeId, serviceId in contractDescr.tariffCoupleVisits.iterkeys():
        subcond = []
        if eventTypeId:
            subcond.append(tableEvent['eventType_id'].eq(eventTypeId))
        if serviceId:
            subcond.append(tableVisit['service_id'].eq(serviceId))
        if subcond:
            condPart2.append(db.joinAnd(subcond))
        else: # тут подойдёт всё.
            condPart2 = None
            break
    if condPart2:
        cond.append(db.joinOr(condPart2))

    records = db.getRecordListGroupBy(table,
                                      cols='DISTINCT Event.id, Visit.service_id',
                                      where=cond,
                                      group='Event.id, Visit.service_id',
                                      order='Event.execDate, Event.client_id, Event.id')
    return [ (forceRef(record.value(0)), forceRef(record.value(1)))
             for record in records
           ]


def addTariffToDict(tariffDict, key, tariff):
    tariffList = tariffDict.get(key, None)
    if tariffList:
        tariffList.append(tariff)
    else:
        tariffDict[key] = [tariff]


def sortTariffsInDict(tariffDict):
    for tariffList in tariffDict.values():
        tariffList.sort(key=lambda tariff: (0 if tariff.MKB else 1, tariff.MKB, tariff.id))
    return tariffDict
    

def selectReexposableEvents(contractDescr, begDate, endDate, personIdList=None, onlyTFOMS=False):
    db = QtGui.qApp.db
    tableAccountItem = db.table('Account_Item')
    tableAccount = db.table('Account')
    tableEvent = db.table('Event')
    tablePayRefuseType = db.table('rbPayRefuseType')
    cond = [tableAccount['contract_id'].eq(contractDescr.id),
            tableAccount['settleDate'].dateBetween(begDate, endDate),
            tableAccountItem['refuseType_id'].isNotNull(),
            tablePayRefuseType['rerun'].ne(0),
            tableAccountItem['reexposeItem_id'].isNull(),
            tableEvent['deleted'].eq(0),
            tableEvent['expose'].eq(1)
            ]
    table = tableAccountItem.leftJoin(
        tableAccount, tableAccount['id'].eq(tableAccountItem['master_id']))
    table = table.leftJoin(
        tablePayRefuseType, tablePayRefuseType['id'].eq(tableAccountItem['refuseType_id']))
    table = table.leftJoin(
        tableEvent, tableEvent['id'].eq(tableAccountItem['event_id']))
    if onlyTFOMS:
        tableClient = db.table('Client')
        tableClientPolicy = db.table('ClientPolicy')
        tableInsurer = db.table('Organisation').alias("Insurer")
        table = table.leftJoin(tableClient, tableClient['id'].eq(tableEvent['client_id']))
        table = table.leftJoin(tableClientPolicy, u"""ClientPolicy.id = COALESCE((SELECT MAX(cp2.id) 
                                                        FROM ClientPolicy cp2
                                                        WHERE cp2.client_id = Client.id AND cp2.deleted = 0 AND cp2.begDate =
      (select MAX(cp.begDate) from ClientPolicy cp
              WHERE cp.client_id = Client.id
                AND cp.policyType_id IN (1,2)
                AND cp.deleted = 0
                AND cp.begDate <= Event.execDate AND (cp.endDate is NULL OR cp.endDate >= DATE(Event.execDate)))),
     (SELECT MAX(cp2.id)
              FROM ClientPolicy cp2
              WHERE cp2.client_id = Client.id AND cp2.deleted = 0 AND cp2.begDate =
              (select MAX(cp.begDate)
                from ClientPolicy cp
                WHERE cp.client_id = Client.id
                AND cp.policyType_id IN (1,2)
                AND cp.deleted = 0
                AND cp.begDate BETWEEN Event.execDate AND ADDDATE(DATE(Event.execDate), 30)
                )),
    (SELECT MAX(cp2.id)
            FROM ClientPolicy cp2
            WHERE cp2.client_id = Event.relative_id AND cp2.deleted = 0 AND cp2.begDate =
            (select MAX(cp.begDate)
            from ClientPolicy cp
            WHERE cp.client_id = Event.relative_id
                AND cp.policyType_id IN (1,2)
                AND cp.deleted = 0
                AND cp.begDate <= Event.execDate AND (cp.endDate is NULL OR cp.endDate >= DATE(Event.execDate))
               )))""")
        table = table.leftJoin(tableInsurer, tableInsurer['id'].eq(tableClientPolicy['insurer_id']))
        cond.append("substr(Insurer.area, 1, 2) != '%s'" % QtGui.qApp.provinceKLADR()[:2])
        
    if personIdList is not None:
        if contractDescr.visitExposition:
            tableVisit = db.table('Visit')
            table = table.innerJoin(
                tableVisit, tableVisit['id'].eq(tableAccountItem['visit_id']))
            cond.append(tableVisit['deleted'].eq(0))
            cond.append(tableVisit['person_id'].inlist(personIdList))
        elif contractDescr.actionExposition:
            tableAction = db.table('Action')
            table = table.innerJoin(
                tableAction, tableAction['id'].eq(tableAccountItem['action_id']))
            cond.append(tableAction['deleted'].eq(0))
            cond.append(tableAction['person_id'].inlist(personIdList))
        else:
            cond.append(tableEvent['execPerson_id'].inlist(personIdList))
    return db.getIdList(table, idCol='Account_Item.event_id', where=cond, order='Account_Item.date, Account_Item.id')


def selectReexposableAccountItems(contractDescr, date, onlyDispCOVID, onlyResearchOnCOVID):
    db = QtGui.qApp.db
    tableAccountItem = db.table('Account_Item')
    tableAccount = db.table('Account')
    tablePayRefuseType = db.table('rbPayRefuseType')
    cond = [ tableAccount['contract_id'].eq(contractDescr.id),
             tableAccount['settleDate'].le(date),
             tableAccountItem['refuseType_id'].isNotNull(),
             tablePayRefuseType['rerun'].ne(0),
             tableAccountItem['reexposeItem_id'].isNull()
           ]
    table = tableAccountItem.leftJoin(
        tableAccount, tableAccount['id'].eq(tableAccountItem['master_id']))
    table = table.leftJoin(
        tablePayRefuseType, tablePayRefuseType['id'].eq(tableAccountItem['refuseType_id']))


    if onlyDispCOVID or onlyResearchOnCOVID:
        tableEvent = db.table('Event')
        tableEventType = db.table('EventType')
        table = tableEvent.innerJoin(tableAccountItem, tableEvent['id'].eq(tableAccountItem['event_id']))
        table = table.leftJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
        if onlyDispCOVID:
            tableMAT = db.table('rbMedicalAidType')
            table = table.leftJoin(tableMAT, tableMAT['id'].eq(tableEventType['medicalAidType_id']))
            cond.append(tableMAT['regionalCode'].eq('233'))
        if onlyResearchOnCOVID:
            tableETI = db.table('EventType_Identification')
            tableAS = db.table('rbAccountingSystem')
            table = table.leftJoin(tableETI, tableETI['master_id'].eq(tableEventType['id']))
            table = table.leftJoin(tableAS, tableAS['id'].eq(tableETI['system_id']))
            cond.append(tableETI['value'].eq('av'))
            cond.append(tableETI['deleted'].eq(0))
            cond.append(tableAS['code'].eq('AccTFOMS'))
    return db.getIdList(table, idCol='Account_Item.id', where=cond, order='Account_Item.date, Account_Item.id')


def getRefuseTypeId(errorMessage, rerun=True, financeId=None, autoRegisterPayRefuseType=True):
    db = QtGui.qApp.db
    table  = db.table('rbPayRefuseType')
    idList = db.getIdList(table,
                          where=[table['name'].like(errorMessage+'%'),
                                 table['finance_id'].eq(financeId)
                                ])
    if idList:
        return idList[0]
    elif autoRegisterPayRefuseType:
        record = table.newRecord()
        record.setValue('code',       toVariant(''))
        record.setValue('name',       toVariant(errorMessage))
        record.setValue('finance_id', toVariant(financeId))
        record.setValue('rerun',      toVariant(rerun))
        return db.insertRecord(table, record)
    else:
        return None


def updateAccountTotals(accountId):
    stmt = '''
UPDATE Account,
       (SELECT
          SUM(amount) AS totalAmount,
          SUM(uet)    AS totalUet,
          SUM(sum)    AS totalSum
        FROM Account_Item
        WHERE  Account_Item.master_id = %d
         ) AS tmp

SET Account.amount = tmp.totalAmount,
    Account.uet = tmp.totalUet,
    Account.sum = tmp.totalSum
WHERE Account.id = %d'''%(accountId, accountId)
    db = QtGui.qApp.db
    db.query(stmt)


def unpackExposeDiscipline(exposeDiscipline):
    # Биты:
    # sobiicddde
    #        ^ (0)   : exposeByEvent
    #     ^^^  (123) : exposeByDate   (0 - нет, 1- день, 2-неделя, 3-декада, 4-месяц, 5-квартал...)
    #    ^     (4)   : exposeByClient
    #  ^^      (56)  : exposeByInsurer (0- нет, 1 - С.К. с филиалами, 2 - С.К. по филиалам )
    # ^        (7)   : exposeByBatch
    #  ^         (8)   : exposeByOncology
    # ^          (9)   : exposeBySourceOrg
    exposeBySourceOrg = bool(exposeDiscipline>>9 & 1)
    exposeByOncology = bool(exposeDiscipline>>8 & 1)
    exposeByBatch   = bool(exposeDiscipline>>7 & 1)
    exposeByEvent  = bool(exposeDiscipline & 1)
    exposeByDate   = ((exposeDiscipline>>1) & 7) if not exposeByEvent else 0
    exposeByMonth  = exposeByDate == 4
    exposeByClient = bool((exposeDiscipline>>4) & 1) if not exposeByEvent else 0
    exposeByInsurer = ((exposeDiscipline >> 5) & 3) if not exposeByEvent and not exposeByClient else 0
    return ( exposeBySourceOrg,
             exposeByOncology,
             exposeByBatch,
             exposeByEvent,
             exposeByMonth,
             exposeByClient,
             exposeByInsurer,
           )


def packExposeDiscipline(
                          exposeBySourceOrg,
                          exposeByOncology,
                          exposeByBatch,
                          exposeByEvent,
                          exposeByMonth,
                          exposeByClient,
                          exposeByInsurer
                        ):
    result = 0
    if exposeByEvent:
        result |= 1
    if exposeByMonth:
        result |= 4<<1
    if exposeByClient:
        result |= 1<<4
    if exposeByInsurer:
        result |= (exposeByInsurer&3)<<5
    if exposeByBatch:
        result |= 1<<7
    if exposeByOncology:
        result |= 1<<8
    if exposeBySourceOrg:
        result |= 1<<9
    return result


# #############################################


class CAccountIdLineEdit(QtGui.QLineEdit):
    def __init__(self, parent=None):
        QtGui.QLineEdit.__init__(self, parent)
        self._hearingPoint = False
        self._stopEntering = False


    def startHearingPoint(self):
        self._hearingPoint = True


    def stopHearingPoint(self):
        self._hearingPoint = False
        self._stopEntering = False


    def keyPressEvent(self, event):
        if not self._stopEntering:
            if self._hearingPoint:
                if event.text() == '.':
                    self._stopEntering = True
                else:
                    QtGui.QLineEdit.keyPressEvent(self, event)
            else:
                QtGui.QLineEdit.keyPressEvent(self, event)


#поиск выполненных операций стентирования
def getStentOperationCount(eventId):
    db = QtGui.qApp.db
    result = 0       
    stmt = u"""select sum(a.amount) as cnt
    from Action a
    left join ActionType at on at.id = a.actionType_id
    left join rbService s on s.id = at.nomenclativeService_id
    where a.event_id = %s and a.deleted = 0 and s.infis = 'A16.12.004.009'
    """ % eventId
    query = db.query(stmt)
    if query.next():
        record = query.record()
        result = forceInt(record.value('cnt'))
    return result
    

def roundMath(val, digits):
    d = 10**digits
    return round(val*d)/d

def getWeekProfile(index):
    return {0: wpFiveDays,
            1: wpSixDays,
            2: wpSevenDays}.get(index, wpSevenDays)


# поиск выполненных операций, влияющих на выбор ксг
def getOperationCountByCSG(eventId, ksgkusl, mkbCode, csgEndDate):
    db = QtGui.qApp.db
    tableS69 = db.table('soc_spr69')
    tableS82 = db.table('soc_spr82')
    tableAction = db.table('Action')
    tableActionType = db.table('ActionType')
    tableRBService = db.table('rbService').alias('s18')

    table = tableAction.leftJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
    table = table.leftJoin(tableRBService, tableRBService['id'].eq(tableActionType['nomenclativeService_id']))
    table = table.leftJoin(tableS69, u"""soc_spr69.ksgkusl = '{ksgkusl}'
            and (soc_spr69.mkb = '{mkb}' or soc_spr69.mkb is null or (soc_spr69.mkb = 'C.' and substr('{mkb}', 1, 1) = 'C') 
            or (soc_spr69.mkb = 'C00-C80' and '{mkb}' between 'C00' and 'C80.9')) and soc_spr69.kusl is not null""".format(ksgkusl=ksgkusl, mkb=mkbCode))
    table = table.leftJoin(tableS82, tableS82['CODE'].eq(tableS69['ksgkusl']))
    cond = [tableAction['event_id'].eq(eventId),
            tableAction['deleted'].eq(0),
            tableAction['status'].eq(2),
            tableAction['event_id'].eq(eventId),
            tableRBService['infis'].eq(tableS69['kusl']),
            tableS82['DATN'].dateLe(csgEndDate),
            db.joinOr([tableS82['DATO'].dateGe(csgEndDate),
                       tableS82['DATO'].isNull()]),
            tableS82['CODE'].isNotNull()]
    result = db.getCount(table, where=cond)
    return result


# прерванный случай оказания МП
def isInterruptedCase(eventId):
    db = QtGui.qApp.db
    stmt = u"""select EventResult.regionalCode as result
            from Event e
            left join rbResult as EventResult on EventResult.id = e.result_id
            where e.id = {eventId}
                  and EventResult.regionalCode in ('102', '103', '104', '105', '107', '108', '110', '202', '203', '204', '205', '207', '208')""".format(eventId=eventId)
    result = None
    query = db.query(stmt)
    while query.next():
        record = query.record()
        result = forceString(record.value('result'))
    return result


# Предоставление спального места и питания законному представителю несовершеннолетних
# (детей до 4 лет, детей старше 4 лет при наличии медицинских показаний),
# получающих медицинскую помощь по профилю «Детская онкология» и (или) «Гематология»
def hasCancerHemaBloodProfile(eventId):
    db = QtGui.qApp.db
    stmt = u"""select e.id
            from Event e
            LEFT JOIN Person p on p.id = e.execPerson_id
            LEFT JOIN rbSpeciality s ON s.id = p.speciality_id
            LEFT JOIN rbMedicalAidProfile map ON map.id = s.medicalAidProfile_id
            where e.id = {0} and map.regionalCode in ('12', '18')""".format(eventId)
    query = db.query(stmt)
    result = query.size()
    return result


# является ли профиль койки геронтологический?
def isGerontologicalKPK(eventId):
    db = QtGui.qApp.db
    stmt = """select HospitalAction.id 
                from Action AS HospitalAction
                left join ActionPropertyType on ActionPropertyType.typeName = 'HospitalBed' and ActionPropertyType.actionType_id = HospitalAction.actionType_id and ActionPropertyType.deleted = 0
                left join ActionProperty on ActionProperty.type_id = ActionPropertyType.id and ActionProperty.action_id = HospitalAction.id and ActionProperty.deleted = 0
                left join ActionProperty_HospitalBed on ActionProperty_HospitalBed.id = ActionProperty.id
                left join OrgStructure_HospitalBed on OrgStructure_HospitalBed.id = ActionProperty_HospitalBed.value
                left join rbHospitalBedProfile on rbHospitalBedProfile.id = OrgStructure_HospitalBed.profile_id
                where HospitalAction.id = (
                    SELECT MAX(A.id)
                    FROM Action A
                    WHERE A.event_id = %s AND
                              A.deleted = 0 AND
                              A.actionType_id IN (
                                    SELECT AT.id
                                    FROM ActionType AT
                                    WHERE AT.flatCode ='moving'
                                        AND AT.deleted = 0
                              )
                ) and rbHospitalBedProfile.regionalCode = '70'
    """ % eventId
    query = db.query(stmt)
    return query.size()


# Наличие у пациента тяжелой сопутствующей патологии, осложнений заболеваний, сопутствующих заболеваний, влияющих на сложность лечения пациента
def hasSevereMKB(eventId):
    db = QtGui.qApp.db
    stmt = u"""select dc.id
            from Diagnostic dc
            left join Event e on e.id = dc.event_id
            Left join Diagnosis ds on ds.id = dc.diagnosis_id
            left join soc_severeMKB s on ds.MKB like concat(s.mkb, '%')
            where dc.event_id = {eventId}
                AND dc.diagnosisType_id IN (SELECT id FROM rbDiagnosisType WHERE code = '9')
                AND dc.deleted = 0
                AND s.begDate <= e.execDate
                AND (s.endDate is null OR s.endDate >= e.execDate)
            """.format(eventId=eventId)
    query = db.query(stmt)
    result = query.size()
    return result


# наличие услуги в событии
def hasServiceInEvent(eventId, serviceCode):
    db = QtGui.qApp.db
    result = 0
    stmt = u"""select a.id
    from Action a
    left join ActionType at on at.id = a.actionType_id
    left join rbService s on s.id = at.nomenclativeService_id
    where a.event_id = %s and a.deleted = 0 and s.infis = '%s'
    """ % (eventId, serviceCode)
    query = db.query(stmt)
    result = query.size()
    return result
