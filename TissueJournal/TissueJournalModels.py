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

import re

from PyQt4 import QtGui, QtSql
from PyQt4.QtCore import Qt, SIGNAL, QAbstractTableModel, QDate, QDateTime, QEvent, QModelIndex, QObject, QVariant

from Users.Rights import urEditProbePerson, urDeleteProbe
from library.crbcombobox          import CRBComboBox
from library.database             import CTableRecordCache
from library.InDocTable           import CBoolInDocTableCol, CDateInDocTableCol, CEnumInDocTableCol, CFloatInDocTableCol, CInDocTableCol, CInDocTableModel, CInDocTableView, CLocItemDelegate, CRBInDocTableCol, CRecordListModel
from library.PreferencesMixin     import CPreferencesMixin
from library.RecordLock           import CRecordLockMixin
from library.TableModel           import CBoolCol, CCol, CDateCol, CDateTimeCol, CDesignationCol, CEnumCol, CNumCol, CRefBookCol, CSumCol, CTableModel, CTextCol

from library.Utils                import calcAgeTuple, forceBool, forceDate, forceDateTime, forceDouble, forceInt, forceRef, forceString, forceStringEx, formatName, getPref, setPref, smartDict, toVariant

from Events.Action                import CAction
from Events.ActionPropertiesTable import CActionPropertiesTableModel
from Events.ActionProperty        import CActionPropertyValueTypeRegistry
from Events.ActionStatus          import CActionStatus
from Events.ActionTypeCol         import CActionTypeCol
from Events.Utils                 import CEquipmentDescription

from Orgs.PersonComboBoxEx        import CPersonComboBoxEx
from Orgs.SuiteReagentComboBox    import CRBSuiteReagentCol
from RefBooks.Test.TestComboBox   import CRBTestCol, CTestComboBox

from TissueJournal.TissueStatus   import CTissueStatus
from TissueJournal.Utils          import CEmptyEditor, checkActionPreliminaryResultByTissueJournalIdList, checkActionTestSetClosingController, computeActionPreliminaryResult, CTotalEditorDialog, getActualEquipmentId, getActualSpecimenTypeId, getContainerTypeValues, getNextTissueJournalActionType, resetActionTestSetClosingController, resetContainerTypeCache, resetTissueJournalActionTypeStackHelper, resultLost, setActionPreliminaryResult, setProbeResultToActionProperties

# примечание 1:
#   при уменьшении количества строк в таблице при некоторых случаях
#   verticalHeader().updatesEnabled() остаётся False
#   эта ошибка наблюдается в Alt linux 6, причём в PyQt она есть, а в Qt - нет.
#   когда эта ошибка будет исправлена можно будет удалисть строки с этой пометкой



# ##########################################################

class CInDocPersonCol(CRBInDocTableCol):
    def createEditor(self, parent):
        editor = CPersonComboBoxEx(parent)
        return editor


class CTissueTypesModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent, [
            CTextCol(u'Код',          ['code'],  6),
            CTextCol(u'Наименование', ['name'], 20),
            ], 'rbTissueType')

    def setFullIdList(self):
        self.setIdList(QtGui.qApp.db.getIdList(self.table()))

# #######################################################################

class CCheckItemsModelMixin(object):

    def flags(self, index):
        result = CTableModel.flags(self, index)
        if index.column() == 0:
            result |= Qt.ItemIsUserCheckable
        return result


    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.CheckStateRole:
            row = index.row()
#            id = self._idList[row]
            self.parentWidget.setSelected(self._idList[row], forceInt(value) == Qt.Checked, self.table().tableName)
            self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index, index)
            return True
        return False

    def setFullIdList(self):
        self.setIdList(QtGui.qApp.db.getIdList(self.table()))



class CCheckCol(CBoolCol):
    def __init__(self, title, fields, defaultWidth, selector, tableName):
        CBoolCol.__init__(self, title, fields, defaultWidth)
        self.selector = selector
        self.tableName = tableName


    def checked(self, values):
        tissueTypeId = forceRef(values[0])
        if self.selector.isSelected(tissueTypeId, self.tableName):
            return CBoolCol.valChecked
        else:
            return CBoolCol.valUnchecked


class CResultTissueTypesModel(CCheckItemsModelMixin, CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent, [
            CCheckCol(u'Включить',    ['id'], 16, parent, 'rbTissueType'),
            CTextCol(u'Код',          ['code'],  6),
            CTextCol(u'Наименование', ['name'], 20),
            ], 'rbTissueType')
        self.parentWidget = parent


class CResultTestsModel(CCheckItemsModelMixin, CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent, [
            CCheckCol(u'Включить',    ['id'], 16, parent, 'rbTest'),
            CTextCol(u'Код',          ['code'],  6),
            CTextCol(u'Наименование', ['name'], 20),
            ], 'rbTest')
        self.parentWidget = parent



# #########################################################################

class CTissueJournalModel(CTableModel):
    __pyqtSignals__ = ('itemsCountChanged(int)',
                       'rowCountChanged()',) # см. примечание 1
    def __init__(self, parent):
#        db = QtGui.qApp.db
        accountingSystemName = QtGui.qApp.defaultAccountingSystemName()
        if accountingSystemName is None:
            accountingSystemName = u'Код пациента'

        clientIdCol = CLocClientIdentifierColumn(accountingSystemName, ['client_id'], 10)
        clientCol   = CLocClientColumn( u'Ф.И.О.', ['client_id'], 20)

        CTableModel.__init__(self, parent,  [
            clientIdCol,
            clientCol,
            CRefBookCol(u'Тип биоматериала', ['tissueType_id'], 'rbTissueType', 10),
            CTextCol(u'ИБМ', ['externalId'], 10),
            CEnumCol(u'Статус', ['status'], CTissueStatus.names, 7),
            CDateTimeCol(u'Время', ['datetimeTaken'], 18),
            CRefBookCol(u'Ответственный', ['execPerson_id'], 'vrbPersonWithSpeciality', 20),
            CTextCol(u'Примечание', ['note'], 30),
            CNumCol(u'Количество', ['amount'], 5),
            CRefBookCol(u'Ед. измерения', ['unit_id'], 'rbUnit', 10)
            ])
        self.loadField('number')
        self.loadField('parent_id')
        self.setTable('TakenTissueJournal')
        self.parentWidget = parent

        self._colNames = [col.fields()[0] for col in self.cols()]


    def getColIndex(self, colName):
        return self._colNames.index(colName)


    def getIdentifiers(self, row):
        clientIdentifier = forceString(self.data(self.index(row, 0)))
        clientFio        = forceString(self.data(self.index(row, 1)))
        externalId       = forceString(self.data(self.index(row, 3)))
        return clientIdentifier, clientFio, externalId


    def getIdentifiersById(self, id):
        if id in self._idList:
            row = self._idList.index(id)
            return self.getIdentifiers(row)
        return '', '', ''


    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if section == 0:
                if role == Qt.DisplayRole:
                    value = None
                    if QtGui.qApp.defaultAccountingSystemName():
                        value = u'%s' % QtGui.qApp.defaultAccountingSystemName()
                    if QtGui.qApp.checkGlobalPreference('3', '0'): # нужен Client.`id`
                        value = u'Код пациента'
                    if value:
                        return QVariant(value)
            return CTableModel.headerData(self, section, orientation, role)
        elif orientation == Qt.Vertical:
            if role == Qt.DisplayRole:
                return toVariant(u' - '.join([unicode(section+1), forceString(self.getRecordByRow(section).value('number'))]))
        return QVariant()


    def deleteRecord(self, table, itemId):
        QtGui.qApp.db.markRecordsDeleted(table, table[self.idFieldName].eq(itemId))
        stmt = 'UPDATE `Action` SET `takenTissueJournal_id` = NULL WHERE `takenTissueJournal_id`=%d' % itemId
        QtGui.qApp.db.query(stmt)


    def sort(self, col, sortOrder):
        if self._idList:
            db = QtGui.qApp.db
            table = tableJournal = self.table()
            tableClient = db.table('Client')
            tablePerson = db.table('vrbPersonWithSpeciality').alias('Person')
            cond = [tableJournal['id'].inlist(self._idList)]
            colClass = self.cols()[col]
            colName = colClass.fields()[0]
            if type(colClass) == CLocClientColumn:
                colName = 'Client.lastName'
                table = table.innerJoin(tableClient, tableClient['id'].eq(tableJournal['client_id']))
            elif colName == 'execPerson_id':
                table = table.leftJoin(tablePerson, tablePerson['id'].eq(tableJournal['execPerson_id']))
                colName = 'Person.name'
            order = '%s %s'%(colName, u'DESC' if sortOrder else u'ASC')
            self._idList = db.getIdList(table, tableJournal['id'].name(), cond, order)
            self.reset()


    def reset(self):                                # см. примечание 1
        CTableModel.reset(self)                     # см. примечание 1
        self.emitRowCountChanged()                  # см. примечание 1


    def endInsertRows(self):                        # см. примечание 1
        CTableModel.endInsertRows(self)             # см. примечание 1
        self.emitRowCountChanged()                  # см. примечание 1


    def endRemoveRows(self):                        # см. примечание 1
        CTableModel.endRemoveRows(self)             # см. примечание 1
        self.emitRowCountChanged()                  # см. примечание 1


    def emitRowCountChanged(self):                      # см. примечание 1
        self.emit(SIGNAL('rowCountChanged()'))   # см. примечание 1


class CLocClientColumn(CCol):
    def __init__(self, title, fields, defaultWidth):
        CCol.__init__(self, title, fields, defaultWidth, 'l')
        db = QtGui.qApp.db
        self.clientCache = CTableRecordCache(db, 'Client', 'firstName, lastName, patrName, birthDate, sex')


    def getClientRecord(self, clientId):
        return self.clientCache.get(clientId) if clientId else None


    def format(self, values):
        clientId = forceRef(values[0])
        record = self.getClientRecord(clientId)
        if record:
            name  = formatName(record.value('lastName'),
                               record.value('firstName'),
                               record.value('patrName'))
            return toVariant(name)
        else:
            return CCol.invalid


class CLocClientIdentifierColumn(CCol):
    def __init__(self, title, fields, defaultWidth):
        CCol.__init__(self, title, fields, defaultWidth, 'l')
        self.identifiersCache = {}

    def getClientIdentifier(self, clientId):
        identifier = self.identifiersCache.get(clientId, None)
        if identifier is None:
            accountingSystemId = QtGui.qApp.defaultAccountingSystemId()
            if accountingSystemId is None:
                identifier = clientId
            else:
                db = QtGui.qApp.db
                tableClientIdentification = db.table('ClientIdentification')
                cond = [tableClientIdentification['client_id'].eq(clientId),
                        tableClientIdentification['accountingSystem_id'].eq(accountingSystemId),
                        tableClientIdentification['deleted'].eq(0)]
                record = db.getRecordEx(tableClientIdentification, tableClientIdentification['identifier'], cond)
                identifier = forceString(record.value(0)) if record else ''
            self.identifiersCache[clientId] = identifier
        return identifier


    def format(self, values):
        clientId = forceRef(values[0])
        identifier = self.getClientIdentifier(clientId)
        return toVariant(identifier)



# ####################################################################3

CAmountCol = CSumCol

class CTissueJournalActionsModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent,  [
            CBoolCol(u'Срочный', ['isUrgent'], 6),
            CActionTypeCol(u'Тип действия', 10, 2),
            CAmountCol(u'Кол-во', ['amount'], 7),
            CEnumCol(u'Статус', ['status'], CActionStatus.names, 6),
            CDateCol(u'Дата выполнения', ['endDate'], 8),
            CRefBookCol(u'Исполнитель', ['person_id'], 'vrbPersonWithSpeciality', 20),
            CRefBookCol(u'Ассистент', ['assistant_id'], 'vrbPersonWithSpeciality', 20),
            CDateCol(u'Дата назначения', ['directionDate'], 8),
            CDateCol(u'Дата начала', ['begDate'], 8),
            CRefBookCol(u'Назначивший', ['setPerson_id'], 'vrbPersonWithSpeciality', 20),
            CTextCol(u'Примечание', ['note'], 30)
            ], 'Action')
        self.parentWidget = parent


    def getActionsAmount(self):
        return sum([forceDouble(self.getRecordById(id).value('amount')) for id in self._idList])


    def sort(self, col, sortOrder):
        if self._idList:
            db = QtGui.qApp.db
            table = tableAction = db.table('Action')
            tableActionType = db.table('ActionType')
            tablePerson = db.table('vrbPersonWithSpeciality').alias('Person')
            colName = self.cols()[col].fields()[0]
            if colName in ('person_id', 'assistant_id', 'setPerson_id'):
                table = table.leftJoin(tablePerson, tablePerson['id'].eq(tableAction[colName]))
                colName = 'Person.name'
            elif colName == 'actionType_id':
                table = table.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
                colName = 'ActionType.code'
            cond = [tableAction['id'].inlist(self._idList)]
            order = '%s %s'%(colName, u'DESC' if sortOrder else u'ASC')
            self._idList = db.getIdList(table, tableAction['id'].name(), cond, order)
            self.reset()


# ###########################################################################

class CRegistratorCol(CCol):
    def __init__(self, title, fields, defaultWidth):
        CCol.__init__(self, title, fields, defaultWidth, 'l')
        db = QtGui.qApp.db
        self.personCache = CTableRecordCache(db, 'vrbPersonWithSpeciality', 'name')
        self.cache = {}


    def format(self, values):
        takenTissueJournalId = forceRef(values[0])
        if takenTissueJournalId:
            registrator = self.cache.get(takenTissueJournalId, None)
            if not registrator:
                registratorId = QtGui.qApp.db.translate('TakenTissueJournal', 'id', takenTissueJournalId, 'execPerson_id')
                registratorRecord = self.personCache.get(forceRef(registratorId))
                if registratorRecord:
                    registrator = registratorRecord.value('name')
                    self.cache[takenTissueJournalId] = registrator
            return registrator
        return CCol.invalid


class CResultActionsClientIdentifierColumn(CCol):
    mapEventIdToClientId = {}
    def __init__(self, title, fields, defaultWidth):
        CCol.__init__(self, title, fields, defaultWidth, 'l')
        self.mapClientIdToIdentifier = {}
        CResultActionsClientIdentifierColumn.mapEventIdToClientId.clear()


    @classmethod
    def getClientId(cls, eventId):
        clientId = cls.mapEventIdToClientId.get(eventId, None)
        if not clientId:
            clientId = forceRef(QtGui.qApp.db.translate('Event', 'id', eventId, 'client_id'))
            cls.mapEventIdToClientId[eventId] = clientId
        return clientId


    def format(self, values):
        eventId = forceRef(values[0])
        clientId = self.getClientId(eventId)
        if not QtGui.qApp.defaultAccountingSystemId():
            if QtGui.qApp.checkGlobalPreference('3', '0'): # нужен Client.`id`
                return QVariant(clientId)
            return QVariant()
        identifier = self.mapClientIdToIdentifier.get(clientId, None)
        if not identifier:
            db = QtGui.qApp.db
            tableClientIdentification = db.table('ClientIdentification')
            cond = [tableClientIdentification['client_id'].eq(clientId),
                    tableClientIdentification['accountingSystem_id'].eq(QtGui.qApp.defaultAccountingSystemId())]
            record = db.getRecordEx(tableClientIdentification, tableClientIdentification['identifier'], cond)
            if record:
                identifier = record.value('identifier')
            else:
                identifier = QVariant()
            self.mapClientIdToIdentifier[clientId] = identifier
        return identifier


class CResultClientColumn(CCol):
    def __init__(self, title, fields, defaultWidth, clientIdentifierColumn):
        CCol.__init__(self, title, fields, defaultWidth, 'l')
        db = QtGui.qApp.db
        self._clientIdentifierColumn = clientIdentifierColumn
        self.clientCache = CTableRecordCache(db, 'Client', 'firstName, lastName, patrName, birthDate, sex')


    def getClientRecord(self, clientId):
        return self.clientCache.get(clientId) if clientId else None


    def format(self, values):
        eventId = forceRef(values[0])
        clientId = self._clientIdentifierColumn.getClientId(eventId)
        record = self.getClientRecord(clientId)
        if record:
            name  = formatName(record.value('lastName'),
                               record.value('firstName'),
                               record.value('patrName'))
            return toVariant(name)
        else:
            return CCol.invalid



class CResultActionsModel(CTableModel):
    def __init__(self, parent):
        clientIdentifierColumn = CResultActionsClientIdentifierColumn(u'', ['event_id'], 10)
        CTableModel.__init__(self, parent,  [
            clientIdentifierColumn,
            CResultClientColumn(u'ФИО', ['event_id'], 10, clientIdentifierColumn),
            CBoolCol(u'Срочный', ['isUrgent'], 6),
            CDesignationCol(u'ИБМ', ['takenTissueJournal_id'], ('TakenTissueJournal', 'externalId'), 3),
            CActionTypeCol(u'Тип действия', 10, 2),
            CAmountCol(u'Кол-во', ['amount'], 7),
            CEnumCol(u'Статус', ['status'], CActionStatus.names, 6),
            CDateCol(u'Дата выполнения', ['endDate'], 8),
            CRefBookCol(u'Исполнитель', ['person_id'], 'vrbPersonWithSpeciality', 20),
            CRefBookCol(u'Ассистент', ['assistant_id'], 'vrbPersonWithSpeciality', 20),
            CDateCol(u'Дата назначения', ['directionDate'], 8),
            CDateCol(u'Дата начала', ['begDate'], 8),
            CRefBookCol(u'Назначивший', ['setPerson_id'], 'vrbPersonWithSpeciality', 20),
            CRegistratorCol(u'Регистратор', ['takenTissueJournal_id'], 13),
            CTextCol(u'Примечание', ['note'], 30)
            ], 'Action')
        self.parentWidget = parent


    def getClientId(self, eventId):
        clientIdentifierCol = self._cols[0]
        return clientIdentifierCol.getClientId(eventId)


    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if section == 0:
                if role == Qt.DisplayRole:
                    value = None
                    if QtGui.qApp.defaultAccountingSystemName():
                        value = u'%s' % QtGui.qApp.defaultAccountingSystemName()
                    if QtGui.qApp.checkGlobalPreference('3', '0'): # нужен Client.`id`
                        value = u'Код пациента'
                    if value:
                        return QVariant(value)
        elif orientation == Qt.Vertical:
            if role == Qt.DisplayRole:
                return QVariant(section+1)
        return CTableModel.headerData(self, section, orientation, role)

# #################################################

class CResultActionPropertiesModel(CActionPropertiesTableModel):
    def __init__(self, parent):
        CActionPropertiesTableModel.__init__(self, parent)
        self.onlyWithTests = False
        self.allPropertyTypeList = []
        self.clientSex = None
        self.clientAge = None


    def setAction(self, action, clientSex, clientAge):
        self.clientSex = clientSex
        self.clientAge = clientAge
        self.action = action
        if self.action:
            actionType = action.getType()
            propertyTypeList = actionType.getPropertiesById().items()
            propertyTypeList.sort(key=lambda x: (x[1].idx, x[0]))
            self.allPropertyTypeList = [x[1] for x in propertyTypeList]
            self.propertyTypeList = [x[1] for x in propertyTypeList if self.visible(x[1]) and x[1].applicable(clientSex, clientAge)]
        else:
            self.propertyTypeList = []
        self.reset()


    def getGlobalPropertyRow(self, lRow):
        return self.allPropertyTypeList.index(self.propertyTypeList[lRow])


    def visible(self, propertyType):
        result =  True
        if self.onlyWithTests:
            result = result and bool(propertyType.testId)
        return result


    def setOnlyWithTests(self, val):
        self.onlyWithTests = val
        if self.action:
            self.setAction(self.action, self.clientSex, self.clientAge)


# ################################################################################
# ################################################################################

class CBaseEditorModel(QAbstractTableModel):
    def __init__(self, parent):
        QAbstractTableModel.__init__(self, parent)
        self._parent = parent

# ################################################################################

HEADER_VIEW_MODE = smartDict()
HEADER_VIEW_MODE.ACTION_TYPE_MODE      = 0
HEADER_VIEW_MODE.IDENTIFIERS_TYPE_MODE = 1


class CActionPersonCol(CInDocPersonCol):
    pass


class CActionEditorModel(QAbstractTableModel):
    def __init__(self, parent):
        QAbstractTableModel.__init__(self, parent)
        self._parent = parent
        self.staticFieldsList  = [
                                  CFloatInDocTableCol(u'Количество', 'amount', 5, precision=2),
                                  CEnumInDocTableCol(u'Статус', 'status', 5, CActionStatus.names),
                                  CDateInDocTableCol(u'Дата окончания', 'endDate', 8, canBeEmpty=True),
                                  CActionPersonCol(u'Исполнитель', 'person_id', 10, 'vrbPersonWithSpeciality'),
                                  CActionPersonCol(u'Ассистент',    'assistant_id', 10, 'vrbPersonWithSpeciality'),
                                  CInDocTableCol(u'Примечание', 'note', 10)]
        self.actionTypeField = CRBInDocTableCol(u'Тип действия', 'actionType_id', 10, 'ActionType', showFields=2)
        self.staticFieldsCount = len(self.staticFieldsList)
        self.iStaticFieldsList = range(self.staticFieldsCount)
        self._actionIdList        = []
        self._items               = [] # Действие и словарь с типами его свойств(ключ кортеж (`typeName`,`name`))
        self._itemsForDeleting    = []
        self._totalItemKeys       = [] # все случившиеся ключи, по ним будем вытаскивать в data
        self._totalItemKeysCount  = 0
        self._mapPropertyNameToTypeName    = {} # словарь для сравнения одинаковых имен и их типов на оригинальность
        self._propertiesNameNeedAdditional = [] # имена которые требуют приставки со значением типа
        self._mapTakenTissueJournalIdToIdentifiers = {} # список из идентификатора пациента, ФИО пациента и ИБМ
        self._mapTakenTissueJournalIdToClientId = {}
        self._mapEventIdToClientAgeAndSex = {}
        self._verticalHeaderViewMode = HEADER_VIEW_MODE.ACTION_TYPE_MODE
        self._mapActionId2EventTypeId = {}


    def firstAvailableIndex(self):
        return self.index(0, self._verticalHeaderViewMode)


    def setVerticalHeaderViewIdentifiersMode(self):
        self._verticalHeaderViewMode = HEADER_VIEW_MODE.IDENTIFIERS_TYPE_MODE
        self.staticFieldsList.insert(0, self.actionTypeField)
        self.resetFieldsProperties()
        self.reset()


    def setVerticalHeaderViewActionTypeMode(self):
        self._verticalHeaderViewMode = HEADER_VIEW_MODE.ACTION_TYPE_MODE
        if self.actionTypeField in self.staticFieldsList:
            self.staticFieldsList.remove(self.actionTypeField)
        self.resetFieldsProperties()
        self.reset()


    def resetFieldsProperties(self):
        self.staticFieldsCount = len(self.staticFieldsList)
        self.iStaticFieldsList = range(self.staticFieldsCount)


    def getTakenTissueJournalId(self, row):
        action, propertiesDict = self._items[row]
        actionRecord = action.getRecord()
        takenTissueJournalId = forceRef(actionRecord.value('takenTissueJournal_id'))
        return takenTissueJournalId


    def getIdentifiersByRow(self, row):
        takenTissueJournalId = self.getTakenTissueJournalId(row)
        result = self._mapTakenTissueJournalIdToIdentifiers.setdefault(takenTissueJournalId, [])
        if not result:
            if self._parent._tissueJournalModel:
                model  = self._parent._tissueJournalModel
                result = model.getIdentifiersById(takenTissueJournalId)
            else:
                db = QtGui.qApp.db
                record = db.getRecord('TakenTissueJournal', 'client_id, externalId', takenTissueJournalId)
                clientId = forceRef(record.value('client_id'))
                clientFio = forceString(db.translate('Client',
                                         'id', clientId,
                                         'CONCAT_WS(\' \', `lastName`, `firstName`, `patrName`)'))
                externalId = forceString(record.value('externalId'))
                clientIdentifier = ''
                if not QtGui.qApp.defaultAccountingSystemId():
                    if QtGui.qApp.checkGlobalPreference('3', '0'): # нужен Client.`id`
                        clientIdentifier = clientId
                else:
                    tableClientIdentification = db.table('ClientIdentification')
                    cond = [tableClientIdentification['client_id'].eq(clientId),
                            tableClientIdentification['accountingSystem_id'].eq(QtGui.qApp.defaultAccountingSystemId())]
                    record = db.getRecordEx(tableClientIdentification, tableClientIdentification['identifier'], cond)
                    if record:
                        clientIdentifier = forceString(record.value('identifier'))
                result = (clientIdentifier, clientFio, externalId)
                if not self._mapTakenTissueJournalIdToClientId.get(takenTissueJournalId, None):
                    self._mapTakenTissueJournalIdToClientId[takenTissueJournalId] = clientId
        return result


    def getClientIdByTakenTissueJournalId(self, takenTissueJournalId):
        clientId = self._mapTakenTissueJournalIdToClientId.get(takenTissueJournalId, None)
        if not clientId:
            if self._parent._tissueJournalModel:
                model = self._parent._tissueJournalModel
                record = model.getRecordById(takenTissueJournalId)
                clientId = forceRef(record.value('client_id'))
            else:
                clientId = forceRef(QtGui.qApp.db.translate('TakenTissueJournal', 'id', takenTissueJournalId, 'client_id'))
            self._mapTakenTissueJournalIdToClientId[takenTissueJournalId] = clientId
        return clientId


    def setActionIdList(self, actionIdList):
        self._actionIdList = actionIdList
        db = QtGui.qApp.db
        for actionId in actionIdList:
            actionRecord = db.getRecord('Action', '*', actionId)
            eventId = forceRef(actionRecord.value('event_id'))
            self._mapActionId2EventTypeId[actionId] = forceRef(db.translate('Event', 'id', eventId, 'eventType_id'))
            action = CAction(record=actionRecord)
            self.initializeProperties(action)
        self._totalItemKeysCount = len(self._totalItemKeys)
        self.reset()


    def initializeProperties(self, action):
        actionType = action.getType()
        clientSex, clientAge = self.getClientSexAndAge(action)
        propertyTypeList = actionType.getPropertiesById().items()
        propertyTypeList = [x[1] for x in propertyTypeList if self.isVisible(x[1]) and x[1].applicable(clientSex, clientAge)]
        propertyTypeList.sort(key=lambda x: x.idx)
        mapPropertyTypeByTypeNameAndName = {}
        for propertyType in propertyTypeList:
#            propertyTypeLongName  = propertyType.name.lower()
            propertyTypeShortName = propertyType.shortName.lower()
            propertyTypeName = propertyTypeShortName if propertyTypeShortName else propertyType.name.lower()
            typeName              = propertyType.typeName
            key = (typeName, propertyTypeName)
            existTypeName = self._mapPropertyNameToTypeName.setdefault(propertyTypeName, typeName)
            if typeName != existTypeName and propertyTypeName not in self._propertiesNameNeedAdditional:
                self._propertiesNameNeedAdditional.append(propertyTypeName)
            mapPropertyTypeByTypeNameAndName[key] = propertyType
            if key not in self._totalItemKeys:
                self._totalItemKeys.append(key)
        self._items.append((action, mapPropertyTypeByTypeNameAndName))


    def getClientSexAndAge(self, action):
        actionRecord = action.getRecord()
        eventId = forceRef(actionRecord.value('event_id'))
        clientInfo = self._mapEventIdToClientAgeAndSex.get(eventId, None)
        if not clientInfo:
            db = QtGui.qApp.db
            tableEvent = db.table('Event')
            tableClient = db.table('Client')
            queryTable = tableEvent.innerJoin(tableClient,
                                              tableClient['id'].eq(tableEvent['client_id']))
            fields = [tableClient['sex'].alias('clientSex'),
                      tableClient['birthDate'].alias('clientBirthDate'),
                      tableEvent['setDate'].alias('eventSetDate')]
            cond   = [tableEvent['id'].eq(eventId)]
            record = db.getRecordEx(queryTable, fields, cond)
            clientSex = clientAge = None
            if record:
                clientSex       = forceInt(record.value('clientSex'))
                clientBirthDate = forceDate(record.value('clientBirthDate'))
                eventDate       = forceDate(record.value('eventSetDate'))
                clientAge       = calcAgeTuple(clientBirthDate, eventDate)
            clientInfo = (clientSex, clientAge)
            self._mapEventIdToClientAgeAndSex[eventId] = clientInfo
        return clientInfo


    def getActionTypeTextInfo(self, index):
        row = index.row()
        if self._verticalHeaderViewMode == HEADER_VIEW_MODE.IDENTIFIERS_TYPE_MODE:
            return forceString(self.data(self.index(row, 0)))
        elif self._verticalHeaderViewMode == HEADER_VIEW_MODE.ACTION_TYPE_MODE:
            return forceString(self.headerData(row, Qt.Vertical))
        return ''


    def isVisible(self, propertyType):
        return bool(propertyType.visibleInTableEditor)


    def hasCommonPropertyChangingRight(self, action, propertyType):
        if propertyType.canChangeOnlyOwner == 0: # все могут редактировать свойство
            return True
        elif propertyType.canChangeOnlyOwner == 1:
            setPersonId = forceRef(action.getRecord().value('setPerson_id'))
            return setPersonId == QtGui.qApp.userId
        elif propertyType.canChangeOnlyOwner == 2 and self.action:
            person_id = forceRef(action.getRecord().value('person_id'))
            return person_id == QtGui.qApp.userId
        elif propertyType.canChangeOnlyOwner == 4 and self.action:
            return not self.action.isExported()
        return False


    def getPropertyTypeFlags(self, action, propertyType):
        if self.hasCommonPropertyChangingRight(action, propertyType):
            if propertyType.visibleInTableEditor == 1: # редактируется
                flags = Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled
            elif propertyType.visibleInTableEditor == 2: # не редактируется
                flags = Qt.ItemIsSelectable
            else: # по логике по этой ветке алгоритм идти не должен
                flags = Qt.ItemIsSelectable
        else:
            flags = Qt.ItemIsSelectable
        return flags


    def splitHeaderValue(self, value):
        strValue = forceString(value)
        tail = strValue
        parts = []
        while len(tail) > CActionEditorTableView.titleWidth:
            head = tail[:CActionEditorTableView.titleWidth]
            tail = tail[CActionEditorTableView.titleWidth:]
            parts.append(head)
        if tail:
            parts.append(tail)
        strValue = '\n'.join(parts)
        return QVariant(strValue)


    def headerData(self, section, orientation, role = Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                if section in self.iStaticFieldsList:
                    fieldColumn = self.staticFieldsList[section]
                    return fieldColumn.title()
                else:
                    typeName, name = self._totalItemKeys[section-self.staticFieldsCount]
                    additional = '('+typeName+')' if name in self._propertiesNameNeedAdditional else u''
                    fChar = name[0]
                    name = name.replace(fChar, fChar.upper(), 1)
                    return QVariant(name+additional)
        if orientation == Qt.Vertical:
            if role == Qt.DisplayRole:
                if self._verticalHeaderViewMode == HEADER_VIEW_MODE.IDENTIFIERS_TYPE_MODE:
                    clientIdentifier, clientFio, takenTissueJournalExternalId = self.getIdentifiersByRow(section)
                    result = u'%s\n%s\nИБМ: %s' % (clientIdentifier, clientFio, takenTissueJournalExternalId)
                    return QVariant(result)
                elif self._verticalHeaderViewMode == HEADER_VIEW_MODE.ACTION_TYPE_MODE:
                    action, propertiesDict = self._items[section]
                    actionRecord = action.getRecord()
                    value = self.actionTypeField.toString(actionRecord.value(self.actionTypeField.fieldName()), actionRecord)
                    value = self.splitHeaderValue(value)
                return value
        return QVariant()


    def data(self, index, role=Qt.DisplayRole):
        row    = index.row()
        column = index.column()
        if row >= len(self._items):
            return QVariant()
        if role in (Qt.DisplayRole, Qt.EditRole):
            action, propertiesDict = self._items[row]
            if column in self.iStaticFieldsList:
                actionRecord = action.getRecord()
                value = self.getActionValue(actionRecord, column, role)
                return value
            else:
                result = self.getActionAndPropertyType(column, row)
                if result:
                    action, propertyType = result
                    property = action.getPropertyById(propertyType.id)
                    if role == Qt.DisplayRole:
                        return QVariant(property.getText())
                    elif role == Qt.EditRole:
                        return QVariant(property.getValue())
                else:
                    return QVariant('-----')
        return QVariant()


    def getActionValue(self, actionRecord, column, role):
        fieldColumn = self.staticFieldsList[column]
        if role == Qt.DisplayRole:
            return fieldColumn.toString(actionRecord.value(fieldColumn.fieldName()), actionRecord)
        elif role == Qt.EditRole:
            return actionRecord.value(fieldColumn.fieldName())
        return QVariant()


    # добавил emitDataChanged=True, ввиду того что без этого при массовом изменении значений
    # через редактор свойств для колонки все происходит очень долго.
    # В setEditorValueForColumn после всех изменений происходит вызов self.emitAllDataChanged()
    def setData(self, index, value, role=Qt.EditRole, emitDataChanged=True):
        row    = index.row()
        column = index.column()
        if role == Qt.EditRole:
            action, propertiesDict = self._items[row]
            if column in self.iStaticFieldsList:
                if action.isLocked():
                    return False
                actionRecord = action.getRecord()
                fieldColumn = self.staticFieldsList[column]
                actionRecord.setValue(fieldColumn.fieldName(), value)
                if emitDataChanged:
                    self.emitCellChanged(row, column)
                columnsShift = 1 if self._verticalHeaderViewMode == HEADER_VIEW_MODE.ACTION_TYPE_MODE else 0
                if column == 2-columnsShift: # статус. возня с датой окончания.
                    self.setDateValueByStatus(row, forceInt(value), actionRecord, emitDataChanged)
                elif column == 3-columnsShift: # дата окончания. возня со статусом
                    self.setStatusByDateValue(row, forceDate(value), actionRecord, emitDataChanged)
                return True
            elif column in range(self.staticFieldsCount,
                                 self.staticFieldsCount+self._totalItemKeysCount):
                key = self._totalItemKeys[column-self.staticFieldsCount]
                propertyType = propertiesDict.get(key, None)
                if propertyType and not propertyType.isVector:
                    property = action.getPropertyById(propertyType.id)
                    property.setValue(propertyType.convertQVariantToPyValue(value))
                    if emitDataChanged:
                        self.emitCellChanged(row, column)
                    return True
        return False


    def setDateValueByStatus(self, row, status, record, emitDataChanged):
        dateIndex = self.index(row, 3)
        date = forceDate(record.value('endDate'))
        if status in (2, 4):
            if not date:
                record.setValue('endDate', toVariant(QDate.currentDate()))
        else:
            record.setValue('endDate', toVariant(QDate()))
        if emitDataChanged:
            self.emitCellChanged(dateIndex.row(), dateIndex.column())


    def setStatusByDateValue(self, row, date, record, emitDataChanged):
        statusIndex = self.index(row, 2)
        status = forceInt(record.value('status'))
        if date:
            if status != 2:
                record.setValue('status', toVariant(2))
        else:
            if status == 2:
                record.setValue('status', toVariant(3))
        if emitDataChanged:
            self.emitCellChanged(statusIndex.row(), statusIndex.column())


    def flags(self, index):
        row    = index.row()
        column = index.column()
        action, propertiesDict = self._items[row]
        if column in self.iStaticFieldsList:
            if action.isLocked():
                flags = Qt.ItemIsSelectable
            else:
                fieldColumn = self.staticFieldsList[column]
                flags = fieldColumn.flags()
        else:
            result = self.getActionAndPropertyType(column, row)
            if result:
                action, propertyType = result
                flags = self.getPropertyTypeFlags(action, propertyType)
            else:
                flags = Qt.ItemIsSelectable
        if column == 0 and self._verticalHeaderViewMode == HEADER_VIEW_MODE.IDENTIFIERS_TYPE_MODE:
            flags = Qt.ItemIsEnabled  | Qt.ItemIsSelectable
        return flags


    def emitAllDataChanged(self):
        index1 = self.index(0, 0)
        index2 = self.index(self.rowCount()-1, self.columnCount()-1)
        self.emitDataChanged(index1, index2)


    def emitCellChanged(self, row, column):
        index = self.index(row, column)
        self.emitDataChanged(index, index)


    def emitDataChanged(self, index1, index2):
        self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index1, index2)


    def items(self):
        return self._items


    def saveItems(self):
        listForTissueJournalStatusChecking = []
        for actionItem, propertiesDictItem in self._items:
            actionRecord = actionItem.getRecord()
            actionItem.save(idx=forceInt(actionRecord.value('idx')))
            listForTissueJournalStatusChecking.append((actionRecord, actionItem))
        return listForTissueJournalStatusChecking


    def columnCount(self, index=None):
        return self.staticFieldsCount + self._totalItemKeysCount


    def rowCount(self, index=None):
        return len(self.items())


    def setClientId(self, clientId):
        pass


    def createEditor(self, parent, index):
        row    = index.row()
        column = index.column()
        if column in self.iStaticFieldsList:
            fieldColumn = self.staticFieldsList[column]
            return fieldColumn.createEditor(parent)
        else:
            result = self.getActionAndPropertyType(column, row)
            if result:
                action, propertyType = result
                clientId = self.getClientIdByTakenTissueJournalId(self.getTakenTissueJournalId(row))
                eventTypeId = self._mapActionId2EventTypeId.get(forceRef(action.getRecord().value('id')), None)
                return propertyType.createEditor(action, parent, clientId, eventTypeId)
        return QtGui.QWidget()


    def setEditorData(self, index, editor):
        row    = index.row()
        column = index.column()
        if column in self.iStaticFieldsList:
            value = self.data(index, Qt.EditRole)
            action, propertiesDict = self._items[row]
            record = action.getRecord()
            fieldColumn = self.staticFieldsList[column]
            fieldColumn.setEditorData(editor, value, record)
        else:
            result = self.getActionAndPropertyType(column, row)
            if result:
                value = self.data(index, Qt.EditRole)
                editor.setValue(value)


    def getEditorData(self, index, editor):
        row    = index.row()
        column = index.column()
        if column in self.iStaticFieldsList:
            fieldColumn = self.staticFieldsList[column]
            return fieldColumn.getEditorData(editor)
        else:
            result = self.getActionAndPropertyType(column, row)
            if result:
                action, propertyType = result
                return toVariant(editor.value())
        return QVariant()


    def itemsForDeleting(self):
        return self._itemsForDeleting


    def removingRows(self, rows):
        tmpItems = list(self._items)
        rows = list(set(rows) & set(rows))
        for row in rows:
            if 0<=row and row<len(self._items):
                item = self._items[row]
                self._itemsForDeleting.append(item)
                del tmpItems[tmpItems.index(item)]
        self._items = tmpItems
        self.reset()
#        self.emitAllDataChanged()


    def isPropertyColumn(self, column):
        return column in range(self.staticFieldsCount,
                               self.staticFieldsCount+self._totalItemKeysCount)


    def changeColumnValues(self, column, rows):
        parent = QObject.parent(self)
        fieldColumn = None
        if column in self.iStaticFieldsList:
            fieldColumn = self.staticFieldsList[column]
            editor = fieldColumn.createEditor(parent)
        else:
            editor = None
            for row in range(self.rowCount()):
                result = self.getActionAndPropertyType(column, row)
                if result:
                    action, propertyType = result
                    clientId = self.getClientIdByTakenTissueJournalId(self.getTakenTissueJournalId(row))
                    eventTypeId = self._mapActionId2EventTypeId.get(forceRef(action.getRecord().value('id')), None)
                    editor = propertyType.createEditor(action, parent, clientId, eventTypeId)
                if editor is not None:
                    break
        if editor is not None:
            totalEditorDialog = CTotalEditorDialog(parent, editor)
            if totalEditorDialog.exec_():
                if totalEditorDialog.isNullValue():
                    self.setValueForColumn(rows, column, QVariant())
                else:
                    editor = totalEditorDialog.editor()
                    QtGui.qApp.callWithWaitCursor(self, self.setEditorValueForColumn, column, rows, editor, fieldColumn)


    def setEditorValueForColumn(self, column, rows, editor, fieldColumn):
        if fieldColumn:
            value = fieldColumn.getEditorData(editor)
        else:
            value = toVariant(editor.value())
        self.setValueForColumn(rows, column, value)


    def setValueForColumn(self, rows, column, value):
        for row in rows:
            index = self.index(row, column)
            self.setData(index, value, emitDataChanged=False)
        self.emitAllDataChanged()


    def getActionAndPropertyType(self, column, row):
        key = self._totalItemKeys[column-self.staticFieldsCount]
        action, propertiesDict = self._items[row]
        propertyType = propertiesDict.get(key, None)
        if propertyType:
            return action, propertyType
        return None

# ####################################################################

class CPropertiesEditorModel(QAbstractTableModel):
    def __init__(self, parent):
        QAbstractTableModel.__init__(self, parent)
        self._parent = parent
        self._mapTissueJournaIdToProperties = {}
        self.staticFieldsList        = [CInDocTableCol(u'Примечание забора', 'note', 10)]
        self.staticFieldsCount       = len(self.staticFieldsList )
        self.iStaticFieldsList       = range(self.staticFieldsCount)
        self._tissueJournalIdList    = []
        self._actionIdList           = []
        self._mapActionIdToItemIndex = {}
        self._items                  = [] # Действие и словарь с типами его свойств(ключ кортеж (`typeName`,`name`))
        self._itemsForDeleting       = []
        self._totalItemKeys          = [] # все случившиеся ключи, по ним будем вытаскивать в data
        self._totalItemKeysCount     = 0
        self._mapPropertyNameToTypeName    = {} # словарь для сравнения одинаковых имен и их типов на оригинальность
        self._propertiesNameNeedAdditional = [] # имена которые требуют приставки со значением типа
        self._mapTakenTissueJournalIdToIdentifiers = {} # список из идентификатора пациента, ФИО пациента и ИБМ
        self._mapTakenTissueJournalIdToClientId = {}
        self._mapEventIdToClientAgeAndSex = {}
        self._tissueJournalRecordList = []
        self._mapActionId2EventTypeId = {}


    def getActionTypeTextInfo(self, index):
        return ''


    def getClientIdByTakenTissueJournalId(self, takenTissueJournalId):
        clientId = self._mapTakenTissueJournalIdToClientId.get(takenTissueJournalId, None)
        if not clientId:
            if self._parent._tissueJournalModel:
                model = self._parent._tissueJournalModel
                record = model.getRecordById(takenTissueJournalId)
                clientId = forceRef(record.value('client_id'))
            else:
                clientId = forceRef(QtGui.qApp.db.translate('TakenTissueJournal', 'id', takenTissueJournalId, 'client_id'))
            self._mapTakenTissueJournalIdToClientId[takenTissueJournalId] = clientId
        return clientId


    def hasCommonPropertyChangingRight(self, action, propertyType):
        if propertyType.canChangeOnlyOwner == 0: # все могут редактировать свойство
            return True
        elif propertyType.canChangeOnlyOwner == 1:
            setPersonId = forceRef(action.getRecord().value('setPerson_id'))
            return setPersonId == QtGui.qApp.userId
        elif propertyType.canChangeOnlyOwner == 2 and self.action:
            person_id = forceRef(action.getRecord().value('person_id'))
            return person_id == QtGui.qApp.userId
        elif propertyType.canChangeOnlyOwner == 4 and self.action:
            return not self.action.isExported()
        return False


    def getPropertyTypeFlags(self, action, propertyType):
        if self.hasCommonPropertyChangingRight(action, propertyType):
            if propertyType.visibleInTableEditor == 1: # редактируется
                flags = Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled
            elif propertyType.visibleInTableEditor == 2: # не редактируется
                flags = Qt.ItemIsSelectable
            else: # по логике по этой ветке алгоритм идти не должен
                flags = Qt.ItemIsSelectable
        else:
            flags = Qt.ItemIsSelectable
        return flags


    def setActionIdList(self, actionIdList):
        self._actionIdList = actionIdList
        db = QtGui.qApp.db
        for actionId in actionIdList:
            actionRecord = db.getRecord('Action', '*', actionId)
            eventId = forceRef(actionRecord.value('event_id'))
            self._mapActionId2EventTypeId[actionId] = forceRef(db.translate('Event', 'id', eventId, 'eventType_id'))
            action = CAction(record=actionRecord)
            self.initializeProperties(action, actionRecord, actionId)
        self._totalItemKeysCount = len(self._totalItemKeys)
        self.reset()


    def initializeProperties(self, action, actionRecord, actionId):
        actionType = action.getType()
        clientSex, clientAge = self.getClientSexAndAge(action)
        propertyTypeList = actionType.getPropertiesById().items()
        propertyTypeList = [x[1] for x in propertyTypeList if self.isVisible(x[1]) and x[1].applicable(clientSex, clientAge)]
        propertyTypeList.sort(key=lambda x: x.idx)
        mapPropertyTypeByTypeNameAndName = {}
        takenTissueJournalId = forceRef(actionRecord.value('takenTissueJournal_id'))
        if takenTissueJournalId not in self._tissueJournalIdList:
            self._tissueJournalIdList.append(takenTissueJournalId)
            self._tissueJournalRecordList.append(QtGui.qApp.db.getRecord('TakenTissueJournal',
                                                                         'id, note',
                                                                         takenTissueJournalId))
        tissueItemsList = self._mapTissueJournaIdToProperties.setdefault(takenTissueJournalId,
                                                                         {'tissuePropertiesDict':{},
                                                                          'tissueActionsDict':{},
                                                                          'tissueActionsList':[]})
        tissuePropertiesDict = tissueItemsList['tissuePropertiesDict']
        tissueActionsList    = tissueItemsList['tissueActionsList']
        tissueActionsDict    = tissueItemsList['tissueActionsDict']
        if actionId not in tissueActionsList:
            tissueActionsList.append(actionId)
        for propertyType in propertyTypeList:
            propertyTypeShortName = propertyType.shortName.lower()
            propertyTypeName = propertyTypeShortName if propertyTypeShortName else propertyType.name.lower()
            typeName              = propertyType.typeName
            key = (typeName, propertyTypeName)
            existTypeName = self._mapPropertyNameToTypeName.setdefault(propertyTypeName, typeName)
            if typeName != existTypeName and propertyTypeName not in self._propertiesNameNeedAdditional:
                self._propertiesNameNeedAdditional.append(propertyTypeName)
            mapPropertyTypeByTypeNameAndName[key] = propertyType
            tissuePropertiesDict.setdefault(key, propertyType)
            tissueActionsDict.setdefault(key+(takenTissueJournalId,), action)
            if key not in self._totalItemKeys:
                self._totalItemKeys.append(key)


        item = (action, mapPropertyTypeByTypeNameAndName)
        self._items.append(item)
        self._mapActionIdToItemIndex[actionId] = len(self._items)-1


    def getTakenTissueJournalId(self, row):
        return self._tissueJournalIdList[row]


    def firstAvailableIndex(self):
        return self.index(0, 0)


    def setVerticalHeaderViewIdentifiersMode(self):
        pass


    def setVerticalHeaderViewActionTypeMode(self):
        pass


    def getClientSexAndAge(self, action):
        actionRecord = action.getRecord()
        eventId = forceRef(actionRecord.value('event_id'))
        clientInfo = self._mapEventIdToClientAgeAndSex.get(eventId, None)
        if not clientInfo:
            db = QtGui.qApp.db
            tableEvent = db.table('Event')
            tableClient = db.table('Client')
            queryTable = tableEvent.innerJoin(tableClient,
                                              tableClient['id'].eq(tableEvent['client_id']))
            fields = [tableClient['sex'].alias('clientSex'),
                      tableClient['birthDate'].alias('clientBirthDate'),
                      tableEvent['setDate'].alias('eventSetDate')]
            cond   = [tableEvent['id'].eq(eventId)]
            record = db.getRecordEx(queryTable, fields, cond)
            clientSex = clientAge = None
            if record:
                clientSex       = forceInt(record.value('clientSex'))
                clientBirthDate = forceDate(record.value('clientBirthDate'))
                eventDate       = forceDate(record.value('eventSetDate'))
                clientAge       = calcAgeTuple(clientBirthDate, eventDate)
            clientInfo = (clientSex, clientAge)
            self._mapEventIdToClientAgeAndSex[eventId] = clientInfo
        return clientInfo


    def getIdentifiersByRow(self, row):
        takenTissueJournalId = self.getTakenTissueJournalId(row)
        result = self._mapTakenTissueJournalIdToIdentifiers.setdefault(takenTissueJournalId, [])
        if not result:
            if self._parent._tissueJournalModel:
                model  = self._parent._tissueJournalModel
                result = model.getIdentifiersById(takenTissueJournalId)
            else:
                db = QtGui.qApp.db
                record = db.getRecord('TakenTissueJournal', 'client_id, externalId', takenTissueJournalId)
                clientId = forceRef(record.value('client_id'))
                clientFio = forceString(db.translate('Client',
                                         'id', clientId,
                                         'CONCAT_WS(\' \', `lastName`, `firstName`, `patrName`)'))
                externalId = forceString(record.value('externalId'))
                clientIdentifier = ''
                if not QtGui.qApp.defaultAccountingSystemId():
                    if QtGui.qApp.checkGlobalPreference('3', '0'): # нужен Client.`id`
                        clientIdentifier = clientId
                else:
                    tableClientIdentification = db.table('ClientIdentification')
                    cond = [tableClientIdentification['client_id'].eq(clientId),
                            tableClientIdentification['accountingSystem_id'].eq(QtGui.qApp.defaultAccountingSystemId())]
                    record = db.getRecordEx(tableClientIdentification, tableClientIdentification['identifier'], cond)
                    if record:
                        clientIdentifier = forceString(record.value('identifier'))
                result = (clientIdentifier, clientFio, externalId)
                if not self._mapTakenTissueJournalIdToClientId.get(takenTissueJournalId, None):
                    self._mapTakenTissueJournalIdToClientId[takenTissueJournalId] = clientId
        return result


    def isVisible(self, propertyType):
        return bool(propertyType.visibleInTableEditor)


    def rowCount(self, index=None):
        return len(self._tissueJournalIdList)


    def columnCount(self, index=None):
        return self._totalItemKeysCount + self.staticFieldsCount


    def headerData(self, section, orientation, role = Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                if section in self.iStaticFieldsList:
                    fieldColumn = self.staticFieldsList[section]
                    return fieldColumn.title()
                else:
                    typeName, name = self._totalItemKeys[section-self.staticFieldsCount]
                    additional = '('+typeName+')' if name in self._propertiesNameNeedAdditional else u''
                    fChar = name[0]
                    name = name.replace(fChar, fChar.upper(), 1)
                    return QVariant(name+additional)
        if orientation == Qt.Vertical:
            if role == Qt.DisplayRole:
                clientIdentifier, clientFio, takenTissueJournalExternalId = self.getIdentifiersByRow(section)
                result = u'%s\n%s\nИБМ: %s' % (clientIdentifier, clientFio, takenTissueJournalExternalId)
                return QVariant(result)
        return QVariant()


    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        row    = index.row()
        column = index.column()
        if role in (Qt.DisplayRole, Qt.EditRole):
            if column in self.iStaticFieldsList:
                tissueRecord = self._tissueJournalRecordList[row]
                value = self.getTissueJournalValue(tissueRecord, column, role)
                return value
            else:
                result = self.getActionAndPropertyType(column, row)
                if result:
                    action, propertyType = result
                    property = action.getPropertyById(propertyType.id)
                    if role == Qt.DisplayRole:
                        return QVariant(property.getText())
                    elif role == Qt.EditRole:
                        return QVariant(property.getValue())
                else:
                    return QVariant('-----')
        return QVariant()


    def getTissueJournalValue(self, record, column, role):
        fieldColumn = self.staticFieldsList[column]
        if role == Qt.DisplayRole:
            return fieldColumn.toString(record.value(fieldColumn.fieldName()), record)
        elif role == Qt.EditRole:
            return record.value(fieldColumn.fieldName())
        return QVariant()


    def setData(self, index, value, role=Qt.EditRole, emitDataChanged=True):
        row    = index.row()
        column = index.column()
        if role == Qt.EditRole:
            if column in self.iStaticFieldsList:
                tissueRecord = self._tissueJournalRecordList[row]
                fieldColumn = self.staticFieldsList[column]
                tissueRecord.setValue(fieldColumn.fieldName(), value)
                if emitDataChanged:
                    self.emitCellChanged(row, column)
                return True
            else:
                tissueJournalId = self._tissueJournalIdList[row]
                tissueItemsList = self._mapTissueJournaIdToProperties[tissueJournalId]
                tissuePropertiesDict = tissueItemsList['tissuePropertiesDict']
                key = self._totalItemKeys[column-self.staticFieldsCount]
                propertyType = tissuePropertiesDict.get(key, None)
                if propertyType and not propertyType.isVector:
                    self.setValueAllSameTissueProperties(key, value, tissueItemsList)
                    return True
        return False


    def setValueAllSameTissueProperties(self, key, value, tissueItemsList):
        tissueActionsList = tissueItemsList['tissueActionsList']
        if not type(value) == QVariant:
            value = QVariant(value)
        for actionId in tissueActionsList:
            action, mapPropertyTypeByTypeNameAndName = self._items[self._mapActionIdToItemIndex[actionId]]
            propertyType = mapPropertyTypeByTypeNameAndName.get(key, None)
            if propertyType and not propertyType.isVector:
                property = action.getPropertyById(propertyType.id)
                property.setValue(propertyType.convertQVariantToPyValue(value))


    def flags(self, index):
        row    = index.row()
        column = index.column()
        if column in self.iStaticFieldsList:
            flags = Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled
        else:
            flags = Qt.ItemIsSelectable
            result = self.getActionAndPropertyType(column, row)
            if result:
                action, propertyType = result
                flags = self.getPropertyTypeFlags(action, propertyType)
        return flags


    def emitAllDataChanged(self):
        index1 = self.index(0, 0)
        index2 = self.index(self.rowCount()-1, self.columnCount()-1)
        self.emitDataChanged(index1, index2)


    def emitCellChanged(self, row, column):
        index = self.index(row, column)
        self.emitDataChanged(index, index)


    def emitDataChanged(self, index1, index2):
        self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index1, index2)


    def items(self):
        return self._items


    def saveItems(self):
        listForTissueJournalStatusChecking = []
        for actionItem, propertiesDictItem in self._items:
            actionRecord = actionItem.getRecord()
            actionItem.save(idx=forceInt(actionRecord.value('idx')))
            listForTissueJournalStatusChecking.append((actionRecord, actionItem))
        for tissueRecord in self._tissueJournalRecordList:
            QtGui.qApp.db.updateRecord('TakenTissueJournal', tissueRecord)
        return listForTissueJournalStatusChecking


    def createEditor(self, parent, index):
        row    = index.row()
        column = index.column()
        if column in self.iStaticFieldsList:
            fieldColumn = self.staticFieldsList[column]
            return fieldColumn.createEditor(parent)
        else:
            result = self.getActionAndPropertyType(column, row)
            if result:
                action, propertyType = result
                clientId = self.getClientIdByTakenTissueJournalId(self.getTakenTissueJournalId(row))
                eventTypeId = self._mapActionId2EventTypeId.get(forceRef(action.getRecord().value('id')), None)
                return propertyType.createEditor(action, parent, clientId, eventTypeId)
        return CEmptyEditor(parent)


    def setEditorData(self, index, editor):
        row    = index.row()
        column = index.column()
        if column in self.iStaticFieldsList:
            value = self.data(index, Qt.EditRole)
            record = self._tissueJournalRecordList[row]
            fieldColumn = self.staticFieldsList[column]
            fieldColumn.setEditorData(editor, value, record)
        else:
            result = self.getActionAndPropertyType(column, row)
            if result:
                value = self.data(index, Qt.EditRole)
                editor.setValue(value)


    def getEditorData(self, index, editor):
        row    = index.row()
        column = index.column()
        if column in self.iStaticFieldsList:
            fieldColumn = self.staticFieldsList[column]
            return fieldColumn.getEditorData(editor)
        else:
            result = self.getActionAndPropertyType(column, row)
            if result:
                return toVariant(editor.value())
        return QVariant()


    def itemsForDeleting(self):
        return self._itemsForDeleting


    def removingRows(self, rows):
        tmpItems = list(self._items)
        tmpTissueJournalRecordList = (self._tissueJournalRecordList)
        tmpTissueJournalIdList = list(self._tissueJournalIdList)
        rows = list(set(rows) & set(rows))
        for row in rows:
            if 0<=row and row<len(self._tissueJournalIdList):
                tissueJournalId = self._tissueJournalIdList[row]
                tissueJournalRecord = self._tissueJournalRecordList[row]
                tissueItemsList = self._mapTissueJournaIdToProperties[tissueJournalId]
                tissueActionsList = tissueItemsList['tissueActionsList']
                tmpTissueActionsList = list(tissueActionsList)
                for actionId in tissueActionsList:
                    itemIndex = self._mapActionIdToItemIndex[actionId]
                    item = self._items[itemIndex]
                    self._itemsForDeleting.append(item)
                    del tmpItems[tmpItems.index(item)]
                    del tmpTissueActionsList[tmpTissueActionsList.index(actionId)]
                tissueItemsList['tissueActionsList'] = tmpTissueActionsList
                del tmpTissueJournalIdList[tmpTissueJournalIdList.index(tissueJournalId)]
                del tmpTissueJournalRecordList[tmpTissueJournalRecordList.index(tissueJournalRecord)]
        self._items = tmpItems
        self._tissueJournalIdList = tmpTissueJournalIdList
        self._tissueJournalRecordList = tmpTissueJournalRecordList
        self._recountMapActionIdToItemIndex()
        self.reset()


    def _recountMapActionIdToItemIndex(self):
        self._mapActionIdToItemIndex.clear()
        for index, item in enumerate(self._items):
            self._mapActionIdToItemIndex[forceRef(item[0].getRecord().value('id'))] = index


    def changeColumnValues(self, column, rows):
        parent = QObject.parent(self)
        if column in self.iStaticFieldsList:
            fieldColumn = self.staticFieldsList[column]
            editor = fieldColumn.createEditor(parent)
        else:
            fieldColumn = None
            for row in range(self.rowCount()):
                result = self.getActionAndPropertyType(column, row)
                if result:
                    action, propertyType = result
                    clientId = self.getClientIdByTakenTissueJournalId(self.getTakenTissueJournalId(row))
                    eventTypeId = self._mapActionId2EventTypeId.get(forceRef(action.getRecord().value('id')), None)
                    editor = propertyType.createEditor(action, parent, clientId, eventTypeId)
                if editor is not None:
                    break
        if editor is not None:
            totalEditorDialog = CTotalEditorDialog(parent, editor)
            if totalEditorDialog.exec_():
                if totalEditorDialog.isNullValue():
                    self.setValueForColumn(rows, column, QVariant())
                else:
                    editor = totalEditorDialog.editor()
                    QtGui.qApp.callWithWaitCursor(self, self.setEditorValueForColumn, column, rows, editor, fieldColumn)


    def setEditorValueForColumn(self, column, rows, editor, fieldColumn):
        if fieldColumn:
            value = fieldColumn.getEditorData(editor)
        else:
            value = editor.value()
        self.setValueForColumn(rows, column, value)


    def setValueForColumn(self, rows, column, value):
        for row in rows:
            index = self.index(row, column)
            self.setData(index, value, emitDataChanged=False)
        self.emitAllDataChanged()


    def getActionAndPropertyType(self, column, row):
        tissueJournalId = self._tissueJournalIdList[row]
        tissueItemsList = self._mapTissueJournaIdToProperties[tissueJournalId]
        tissuePropertiesDict = tissueItemsList['tissuePropertiesDict']
        key = self._totalItemKeys[column-self.staticFieldsCount]
        propertyType = tissuePropertiesDict.get(key, None)
        if propertyType:
            action = tissueItemsList['tissueActionsDict'].get(key+(tissueJournalId, ), None)
            if action:
                return action, propertyType
        return None



class CActionEditorItemDelegate(QtGui.QItemDelegate):
    def __init__(self, parent):
        QtGui.QItemDelegate.__init__(self, parent)


    def createEditor(self, parent, option, index):
        model = index.model()
        editor = model.createEditor(parent, index)
        self.connect(editor, SIGNAL('commit()'), self.emitCommitData)
        self.connect(editor, SIGNAL('editingFinished()'), self.commitAndCloseEditor)
        return editor

    def setEditorData(self, editor, index):
        if editor is not None:
            model  = index.model()
            model.setEditorData(index, editor)


    def setModelData(self, editor, model, index):
        if editor is not None:
            model.setData(index, index.model().getEditorData(index, editor))

    def emitCommitData(self):
        self.emit(SIGNAL('commitData(QWidget *)'), self.sender())


    def commitAndCloseEditor(self):
        editor = self.sender()
        self.emit(SIGNAL('commitData(QWidget *)'), editor)
        self.emit(SIGNAL('closeEditor(QWidget *,QAbstractItemDelegate::EndEditHint)'), editor, QtGui.QAbstractItemDelegate.NoHint)


class CActionEditorTableView(QtGui.QTableView, CPreferencesMixin):
    titleWidth = 50
    def __init__(self, parent):
        QtGui.QTableView.__init__(self, parent)
        fontMetrics = self.fontMetrics()
        h = fontMetrics.height()
        verticalHeader = self.verticalHeader()
        verticalHeader.setDefaultSectionSize(3*h/2)
        verticalHeader.setResizeMode(QtGui.QHeaderView.ResizeToContents)
        self.setShowGrid(True)
        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectItems)
        self.setAlternatingRowColors(True)
        self.horizontalHeader().setStretchLastSection(True)
        self.setTabKeyNavigation(True)
        self.setEditTriggers(QtGui.QAbstractItemView.AnyKeyPressed | QtGui.QAbstractItemView.EditKeyPressed | QtGui.QAbstractItemView.SelectedClicked | QtGui.QAbstractItemView.DoubleClicked)
        self.setFocusPolicy(Qt.StrongFocus)

        self.setItemDelegate(CActionEditorItemDelegate(self))

        self._popupMenu = QtGui.QMenu(self)
        self.connect(self._popupMenu, SIGNAL('aboutToShow()'), self.on_aboutToShow)

        self._actDeleteRows = QtGui.QAction(u'Удалить строку', self)
        self._popupMenu.addAction(self._actDeleteRows)
        self.connect(self._actDeleteRows, SIGNAL('triggered()'), self.on_deleteRows)

        self._actSelectAllRow = QtGui.QAction(u'Выделить все строки', self)
        self._popupMenu.addAction(self._actSelectAllRow)
        self.connect(self._actSelectAllRow, SIGNAL('triggered()'), self.on_selectAllRow)

        self._actClearSelectionRow = QtGui.QAction(u'Снять выделение', self)
        self._popupMenu.addAction(self._actClearSelectionRow)
        self.connect(self._actClearSelectionRow, SIGNAL('triggered()'), self.on_clearSelectionRow)

        self._actChangePropertyValue = QtGui.QAction(u'Изменить значение свойства', self)
        self._popupMenu.addAction(self._actChangePropertyValue)
        self.connect(self._actChangePropertyValue, SIGNAL('triggered()'), self.on_changePropertyValue)


    def getSelectedRows(self):
        result = [index.row() for index in self.selectionModel().selectedIndexes()]
        result.sort()
        return result


    def on_aboutToShow(self):
        row = self.currentIndex().row()
        rows = self.getSelectedRows()
        existSelectedRows = bool(rows)
        if len(rows) == 1 and rows[0] == row:
            self._actDeleteRows.setText(u'Удалить текущую строку')
            self._actChangePropertyValue.setText(u'Изменить значение свойства')
        elif len(rows) == 1:
            self._actDeleteRows.setText(u'Удалить выделенную строку')
            self._actChangePropertyValue.setText(u'Изменить значение свойства')
        else:
            self._actDeleteRows.setText(u'Удалить выделенные строки')
            self._actChangePropertyValue.setText(u'Изменить значения свойств')
        self._actDeleteRows.setEnabled(existSelectedRows)
        self._actClearSelectionRow.setEnabled(existSelectedRows)
        canChangeValue = existSelectedRows
        if canChangeValue:
            selectedIndexes = self.selectionModel().selectedIndexes()
            columns = [ index.column() for index in selectedIndexes ]
            columns = list( set(columns) & set(columns) )
            model = self.model()
            if hasattr(model, '_verticalHeaderViewMode'):
                if model._verticalHeaderViewMode == HEADER_VIEW_MODE.ACTION_TYPE_MODE:
                    canChangeFirstColumn = True
                else:
                    canChangeFirstColumn = columns[0] != 0
            else:
                canChangeFirstColumn = True
            canChangeValue = ( (len(columns) == 1) and  canChangeFirstColumn)
        self._actChangePropertyValue.setEnabled(canChangeValue)


    def on_deleteRows(self):
        rows = self.getSelectedRows()
        rows.sort(reverse=True)
        self.model().removingRows(rows)


    def contextMenuEvent(self, event):
        if self._popupMenu:
            self._popupMenu.exec_(event.globalPos())
            event.accept()
        else:
            event.ignore()


    def on_selectAllRow(self):
        self.selectAll()


    def on_clearSelectionRow(self):
        self.clearSelection()


    def on_changePropertyValue(self):
        selectedIndexes = self.selectionModel().selectedIndexes()
        rows = []
        columns = []
        for index in selectedIndexes:
            row = index.row()
            column = index.column()
            if row not in rows:
                rows.append(row)
            if column not in columns:
                columns.append(column)
        if len(columns) == 1:
            self.model().changeColumnValues(columns[0], rows)


    def keyPressEvent(self, event):
        # В случае если при навигации последняя в строке ячейка не имеет флага `Qt.ItemIsEditable`
        # то фокус намертво застревает на возможной ячейке перед ней.
        # Если строка заканчивается ячейкой с `Qt.ItemIsEditable` то фокус свободно бежит перескакивая на следующуе строки.
        # Почему так пока не ясно. Как заплатка поставлен этот механизм.
        if event.type() == QEvent.KeyPress:
            key = event.key()
            if key in (Qt.Key_Tab, Qt.Key_Right):
                index = self.currentIndex()
                row = index.row()
                column = index.column()
                model = self.model()
                if (row == model.rowCount()-1) and (column == model.columnCount()-1):
                    self.parent().focusNextChild()
                    event.accept()
                else:
                    if self.goNextCell(row, column, model):
                        event.accept()
                    else:
                        QtGui.QTableView.keyPressEvent(self, event)
            elif key in (Qt.Key_Backtab, Qt.Key_Left):
                index = self.currentIndex()
                row = index.row()
                column = index.column()
                model = self.model()
                if (index.row() == 0) and (index.column() == 0):
                    self.parent().focusPreviousChild()
                    event.accept()
                else:
                    if self.goPreviousCell(row, column, model):
                        event.accept()
                    else:
                        QtGui.QTableView.keyPressEvent(self, event)
            else:
                QtGui.QTableView.keyPressEvent(self, event)
        else:
            QtGui.QTableView.keyPressEvent(self, event)


    def goNextCell(self, currentRow, currentColumn, model):
        availableRows         = range(model.rowCount())[currentRow:]
        availableColumns      = range(model.columnCount())
        availableFirstColumns = availableColumns[currentColumn+1:]
        return self.goCell(availableRows, availableFirstColumns, availableColumns, model)


    def goPreviousCell(self, currentRow, currentColumn, model):
        availableRows         = range(model.rowCount())[:currentRow+1]
        availableRows.reverse()
        availableColumns      = range(model.columnCount())
        availableFirstColumns = availableColumns[:currentColumn]
        availableFirstColumns.reverse()
        availableColumns.reverse()
        return self.goCell(availableRows, availableFirstColumns, availableColumns, model)


    def goCell(self, availableRows, availableFirstColumns, availableColumns, model):
        isCurrentRow = True
        for row in availableRows:
            if isCurrentRow:
                for column in availableFirstColumns:
                    index = model.index(row, column)
                    flags = model.flags(index)
                    if flags & Qt.ItemIsEditable:
                        self.setCurrentIndex(index)
                        return True
                isCurrentRow = False
            else:
                for column in availableColumns:
                    index = model.index(row, column)
                    flags = model.flags(index)
                    if flags & Qt.ItemIsEditable:
                        self.setCurrentIndex(index)
                        return True
        return False


    def loadPreferences(self, preferences):
        model = self.model()
#        verticalHeaderType = '_vht'+str(model._verticalHeaderViewMode)
        if model:
            for i in xrange(model.staticFieldsCount):
                key = 'col_'+str(i)#+verticalHeaderType
                width = forceInt(getPref(preferences, key, None))
                if width:
                    self.setColumnWidth(i, width)
            for i in xrange(model.staticFieldsCount,
                                 model.staticFieldsCount+model._totalItemKeysCount):
                averageCharWidth = self.horizontalHeader().fontMetrics().averageCharWidth()
                charCount = len(forceString(model.headerData(i, Qt.Horizontal)))
                if charCount < 4:
                    charCount += 1
                elif charCount < 8:
                    charCount += 2
                elif charCount < 10:
                    charCount += 3
                width = averageCharWidth*charCount*3/2
                self.setColumnWidth(i, width)


    def savePreferences(self):
        preferences = {}
        model = self.model()
#        verticalHeaderType = '_vht'+str(model._verticalHeaderViewMode)
        if model:
            for i in xrange(model.staticFieldsCount):
                width = self.columnWidth(i)
                key = 'col_'+str(i)#+verticalHeaderType
                setPref(preferences, key, QVariant(width))
        return preferences

# ############################################################

probeStatuses = [u'Без пробы',
                 u'Ожидание',
                 u'В работе',
                 u'Закончено',
                 u'Без результата',
                 u'Назначено',
                 u'Передано в ЛИС',
                 u'Получено из ЛИС']


class CWorkTestCol(CRBTestCol):
    def createFilter(self, testId):
        db = QtGui.qApp.db
        table = db.table('rbTest')
        testIdList = [testId]
        analogTestIdList = db.getIdList('rbTest_AnalogTest',
                                        'analogTest_id',
                                        'master_id = %d' % testId)
        if analogTestIdList:
            testIdList.extend(analogTestIdList)
        self.additionalFilter = table['id'].inlist(testIdList)


    def createEditor(self, parent):
        editor = CTestComboBox(parent)
        editor.setAdditionalFilter(self.additionalFilter)
        editor.setTable(self.tableName, addNone=False, filter=self.filter, needCache=False)
        editor.setShowFields(self.showFields)
        editor.setPreferredWidth(self.preferredWidth)
        return editor


class CSamplePreparationInDocTableModel(CInDocTableModel, CRecordLockMixin):
    probeInWaiting = 1
    def __init__(self, parent):
        self._dependentTestIdList                  = []
        self._allTestIdList                        = []
        self._existsTestIdList                     = []
        self._selectedTestIdList                   = []
        self._mapItemToTestId                      = {}
        self._mapTestIdListToGroupId               = {}
        self._mapEquipmentTest2CheckingPossibility = {}
        self._mapTestIdToPropertyTypeValues        = {}
        CInDocTableModel.__init__(self, 'Probe', 'id', 'takenTissueJournal_id', parent)
        CRecordLockMixin.__init__(self)
        workTestCol = CWorkTestCol(u'Тест', 'workTest_id', 10, 'rbTest', showFields=2)
        specimenTypeCol = CSpecimenTypeCol(u'Тип образца', 'specimenType_id', 10, 'rbSpecimenType', showFields=2)
        statusCol = CEnumInDocTableCol(u'Статус', 'status', 10, probeStatuses)
        statusCol.setReadOnly(True)
        self.addExtCol(CBoolInDocTableCol(u'Проба', 'exists', 8), QVariant.Bool)
        self.addCol(CRBInDocTableCol(u'Оборудование', 'equipment_id', 10, 'rbEquipment', showFields=2))
        self.addCol(workTestCol)
        self.addCol(specimenTypeCol)
        self.addCol(CInDocTableCol(u'Номер документа', 'externalId', 10))
        self.addCol(CBoolInDocTableCol(u'Срочное', 'isUrgent', 10))
        self.addCol(statusCol)
        self.addCol(CRBSuiteReagentCol(u'Набор реагентов', 'suiteReagent_id', 10, 'SuiteReagent', showFields=2))
        self.addHiddenCol('unit_id')
        self.addHiddenCol('test_id')
        self.addHiddenCol('norm')
        self.addHiddenCol('typeName')
        self.addHiddenCol('containerType_id')
        self.setEnableAppendLine(False)
        self.colsNameList = []
        self.loadColsName()
        self._takenTissueJournalId = None
        self._parent = parent
        self._tmpFilterEquipmentId = None


    def addObject(self, name, object):
        self.__setattr__(name, object)
        object.setObjectName(name)


    def selectAll(self, equipmentId=None):
        self._tmpFilterEquipmentId = equipmentId
        for item in self._items:
            item.setValue('exists', QVariant(True))
            testId = forceRef(item.value('test_id'))
            self.setTestSelected(testId, True)
        self.emitColumnChanged(self.getColIndex('exists'))


    def loadColsName(self):
        cols = []
        for col in self._cols:
            if not col.external():
                cols.append(col.fieldName())
        for col in self._hiddenCols:
            cols.append(col)
        cols.append(self._idFieldName)
        cols.append(self._masterIdFieldName)
        self.colsNameList = cols


    def loadItems(self, takenTissueJournalId):
        self._dependentTestIdList = []
        self._selectedTestIdList  = []
        self._mapItemToTestId.clear()
        self._mapTestIdListToGroupId.clear()
        self._mapTestIdToPropertyTypeValues.clear()
        self._mapEquipmentTest2CheckingPossibility.clear()

        self._allTestIdList = self.getAllTestIdList(takenTissueJournalId)
        self._takenTissueJournalId = takenTissueJournalId

        table = self._table
        cond = [table[self._masterIdFieldName].eq(self._takenTissueJournalId)]

        self._items = self.getExistsItems(table, cond)
        self._existsTestIdList = [forceRef(item.value('test_id')) for item in self._items]
        for testId in list(set(self._allTestIdList) - set(self._existsTestIdList) ):
            item = self.getEmptyRecord()
            item.setValue('test_id', QVariant(testId))
            item.setValue('workTest_id', QVariant(testId))
            values = self._mapTestIdToPropertyTypeValues.get(testId, None)
            if values:
                unitId   = values.get('unitId', None)
                if unitId:
                    item.setValue('unit_id', unitId)
                norm     = values.get('norm', None)
                if norm:
                    item.setValue('norm', norm)
                typeName = values.get('typeName', None)
                if typeName:
                    item.setValue('typeName', typeName)
                isUrgent = values.get('isUrgent', None)
                if isUrgent:
                    item.setValue('isUrgent', isUrgent)
                containerTypeId = values.get('containerTypeId', None)
                if containerTypeId:
                    item.setValue('containerType_id', containerTypeId)
            self._items.append(item)
            self._mapItemToTestId[testId] = item
        self.reset()


    def selectItemsByFilter(self, equipmentId, testGroupId=None, force=False):
        self._tmpFilterEquipmentId = equipmentId
        self.createDependentTestIdList(equipmentId if equipmentId not in (-1, 0, None) else None, testGroupId)
        actualTestIdList = self.getActualTestIdList()
        #?select = (actualTestIdList != self._allTestIdList) or force
#        if select:
        needSelectTestIdSet = set(actualTestIdList) - set(self._existsTestIdList)
        for testId in needSelectTestIdSet:
            item = self._mapItemToTestId.get(testId, None)
            if item:
                item.setValue('exists', QVariant(True))
                self.setTestSelected(testId, True)
        self.emitColumnChanged(self.getColIndex('exists'))


    def setValuesForSelected(self, externalId, equipmentId):
        def explainEquipmentId(equipmentId, testId):
            if equipmentId != -1:
                return equipmentId
            else:
                return forceRef(QtGui.qApp.db.translate('rbEquipment_Test', 'test_id', testId, 'equipment_id'))

        for testId in self._selectedTestIdList:
            locEquipmentId = explainEquipmentId(equipmentId, testId)
            item = self._mapItemToTestId.get(testId, None)
            if item:
                item.setValue('equipment_id', QVariant(locEquipmentId))
                if externalId is not None:
                    item.setValue('externalId', QVariant(externalId))
        self.emitAllChanged()


    def uncheckItems(self):
        tmpSelectedTestIdList = list(self._selectedTestIdList)
        for testId in tmpSelectedTestIdList:
            item = self._mapItemToTestId.get(testId, None)
            if item:
                item.setValue('exists', QVariant(False))
                self.setTestSelected(testId, False)
        self.emitColumnChanged(self.getColIndex('exists'))


    def getExistsItems(self, table, cond):
        items = QtGui.qApp.db.getRecordList(table, self.colsNameList, cond)
        for item in items:
            item.append(QtSql.QSqlField('exists', QVariant.Bool))
            item.setValue('exists', QVariant(True))
        return items


    def createDependentTestIdList(self, equipmentId, testGroupId):
        db = QtGui.qApp.db
        table = db.table('rbEquipment_Test')
        cond = []
        if equipmentId:
            cond.append(table['equipment_id'].eq(equipmentId))
        if testGroupId:
            cond.append(self.getTestGroupCond(testGroupId, table))
        cond = cond if cond else '0'
        dependentTestIdList = db.getDistinctIdList(table, 'test_id', cond)
        self._dependentTestIdList = dependentTestIdList


    def getTestGroupCond(self, testGroupId, table):
        testIdList = self._mapTestIdListToGroupId.get(testGroupId, None)
        if testIdList is None:
            testIdList = QtGui.qApp.db.getDistinctIdList('rbTest', 'id', 'testGroup_id=%d'%testGroupId)
            self._mapTestIdListToGroupId[testGroupId] = testIdList
        return table['test_id'].inlist(testIdList)


    def getActualTestIdList(self):
        result = self._allTestIdList
        if self._dependentTestIdList:
            result = list( set(self._allTestIdList) & set(self._dependentTestIdList) )
        return result


    def getAllTestIdList(self, takenTissueJournalId):
        db = QtGui.qApp.db
        tableAction = db.table('Action')
        tableActionType = db.table('ActionType')
        tableActionPropertyType = db.table('ActionPropertyType')

        queryTable = tableAction.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
        queryTable = queryTable.innerJoin(tableActionPropertyType,
                                          tableActionPropertyType['actionType_id'].eq(tableActionType['id']))

        cond = [tableAction['takenTissueJournal_id'].eq(takenTissueJournalId),
                tableAction['deleted'].eq(0),
                tableActionPropertyType['deleted'].eq(0),
                tableActionPropertyType['test_id'].isNotNull()]

        fields = [tableActionPropertyType['test_id'].name(),
                  tableActionPropertyType['unit_id'].name(),
                  tableActionPropertyType['norm'].name(),
                  tableActionPropertyType['typeName'].name(),
                  tableAction['isUrgent'].name(),
                  tableAction['actionType_id'].name()]

        recordList = db.getRecordList(queryTable, fields, cond)
        testIdList = []

        resetContainerTypeCache()
        tissueTypeId = forceRef(db.translate('TakenTissueJournal', 'id', takenTissueJournalId, 'tissueType_id'))

        for record in recordList:
            testId = forceRef(record.value('test_id'))
            actionTypeId = forceRef(record.value('actionType_id'))
            values, containerTypeId = getContainerTypeValues(actionTypeId, tissueTypeId)
            propertyTypeValues = self._mapTestIdToPropertyTypeValues.get(testId, None)
            if not propertyTypeValues:
                testIdList.append(testId)
                self._mapTestIdToPropertyTypeValues[testId] = {'unitId'         : record.value('unit_id'),
                                                               'norm'           : record.value('norm'),
                                                               'typeName'       : record.value('typeName'),
                                                               'isUrgent'       : record.value('isUrgent'),
                                                               'containerTypeId': QVariant(containerTypeId)}
        return testIdList


    def saveItems(self, takenTissueJournalId, resetTmpFilter=True):
        if self._items is not None:
            items = self._mapItemToTestId.values()
            for idx, record in enumerate(items):
                if forceBool(record.value('exists')):
                    equipmentId = forceRef(record.value('equipment_id'))
                    workTestId  = forceRef(record.value('workTest_id'))
                    if not self._checkEquipmentTest(equipmentId, workTestId):
                        continue
                    if self._tmpFilterEquipmentId:
                        if equipmentId != self._tmpFilterEquipmentId:
                            continue
                    self.saveItem(record, takenTissueJournalId)
        if resetTmpFilter:
            self._tmpFilterEquipmentId = None


    def saveItem(self, record, takenTissueJournalId, oldRecord=None):
        record.setValue(self._masterIdFieldName, toVariant(takenTissueJournalId))
        record.setValue('status', QVariant(CSamplePreparationInDocTableModel.probeInWaiting))
        if self._extColsPresent:
            outRecord = self.removeExtCols(record)
        else:
            outRecord = record
        if not forceRef(outRecord.value('equipment_id')):
            outRecord.setValue('equipment_id', QVariant(self._getActualEquipmentId(outRecord)))
        if not forceRef(outRecord.value('specimenType_id')):
            outRecord.setValue('specimenType_id', QVariant(self._getActualSpecimenTypeId(outRecord)))
        id = QtGui.qApp.db.insertOrUpdate(self._table, outRecord)
        record.setValue(self._idFieldName, toVariant(id))

        oldSuiteReagentId = forceRef(oldRecord.value('suiteReagent_id')) if oldRecord else None
        newSuiteReagentId = forceRef(record.value('suiteReagent_id'))

        if oldSuiteReagentId != newSuiteReagentId:
            self.recountSuiteReagentAmount(oldSuiteReagentId, newSuiteReagentId)


    def _getActualEquipmentId(self, record):
        testId = forceRef(record.value('workTest_id'))
        return getActualEquipmentId(testId)


    def _getActualSpecimenTypeId(self, record):
        testId = forceRef(record.value('workTest_id'))
        equipmentId = forceRef(record.value('equipment_id'))
        return getActualSpecimenTypeId(testId, equipmentId)


    def flags(self, index):
        row = index.row()
        column = index.column()
        if 0 <= row and row < len(self._items):
            item = self._items[row]
            itemId = forceRef(item.value(self._idFieldName))
            if itemId:
                if column == self.getColIndex('exists'):
                    return Qt.ItemIsSelectable
                elif column == self.getColIndex('suiteReagent_id'):
                    return CInDocTableModel.flags(self, index)
                else:
                    return Qt.ItemIsEnabled | Qt.ItemIsSelectable
            else:
                if column == self.getColIndex('specimenType_id'):
                    if not (forceRef(item.value('workTest_id')) and forceRef(item.value('equipment_id'))):
                        return Qt.ItemIsEnabled | Qt.ItemIsSelectable
                elif column == self.getColIndex('exists'):
                    workTestId = forceRef(item.value('workTest_id'))
                    equipmentId = forceRef(item.value('equipment_id'))
                    if workTestId and equipmentId and not self._checkEquipmentTest(equipmentId, workTestId):
                        return Qt.ItemIsSelectable
        return CInDocTableModel.flags(self, index)


    def _checkEquipmentTest(self, equipmentId, testId):
        result = self._mapEquipmentTest2CheckingPossibility.get((equipmentId, testId), None)
        if result is None:
            db = QtGui.qApp.db
            table = db.table('rbEquipment_Test')
            cond = [table['equipment_id'].eq(equipmentId), table['test_id'].eq(testId)]
            record = db.getRecordEx(table, 'type', cond)
            if record:
                result = forceInt(record.value('type')) in (1, 2)
            else:
                result = False
            self._mapEquipmentTest2CheckingPossibility[(equipmentId, testId)] = result
        return result


    def setTestSelected(self, testId, value):
        if value:
            if testId not in self._selectedTestIdList:
                self._selectedTestIdList.append(testId)
        else:
            if testId in self._selectedTestIdList:
                del self._selectedTestIdList[self._selectedTestIdList.index(testId)]


    def hasSelected(self):
        return bool(self._selectedTestIdList)


    def setData(self, index, value, role=Qt.EditRole):
        try:
            column = index.column()
            row = index.row()
            record = self._items[row]
            if role == Qt.CheckStateRole:
                if column == self.getColIndex('exists'):
                    self.setTestSelected(forceRef(record.value('test_id')), forceBool(value))
                    record.setValue('exists', value)
                    self.emitCellChanged(row, column)
                    return True
            itemId = forceRef(record.value('id'))
            if itemId:
                oldRecord = QtSql.QSqlRecord(record)
                result = CInDocTableModel.setData(self, index, value, role)
                if result:
                    self.saveItem(record, self._takenTissueJournalId, oldRecord=oldRecord)
                else:
                    result = False
            else:
                result = CInDocTableModel.setData(self, index, value, role)
            return result
        except:
            return False


    def releaseLock(self):
        CRecordLockMixin.releaseLock(self)


    def recountSuiteReagentAmount(self, oldSuiteReagentId, newSuiteReagentId):
        stmtTemplate = 'UPDATE `SuiteReagent` SET execTestQuantity=execTestQuantity%(action)s1 WHERE SuiteReagent.`id`=%(suiteReagentId)d'
        if oldSuiteReagentId:
            self.decreaseSuiteReagentAmount(stmtTemplate, oldSuiteReagentId)
        if newSuiteReagentId:
            self.increaseSuiteReagentAmount(stmtTemplate, newSuiteReagentId)


    def decreaseSuiteReagentAmount(self, stmtTemplate, suiteReagentId):
        QtGui.qApp.db.query(stmtTemplate%{'action':'-', 'suiteReagentId':suiteReagentId})


    def increaseSuiteReagentAmount(self, stmtTemplate, suiteReagentId):
        QtGui.qApp.db.query(stmtTemplate%{'action':'+', 'suiteReagentId':suiteReagentId})


    def lockItem(self, index):
#        column = index.column()
        row = index.row()
        record = self._items[row]
        itemId = forceRef(record.value('id'))
        if itemId:
            if not self.lock(self.table.tableName, itemId):
                return False
        return True


    def notRetryLock(self, obj, message):
        return CRecordLockMixin.notRetryLock(self, self._parent, message)


    def createWorkTestEditor(self, index, parent):
        if self.lockItem(index):
            column = index.column()
            self._cols[column].createFilter(forceRef(self._items[index.row()].value('test_id')))
            return CRecordListModel.createEditor(self, index, parent)
        return None


    def createEditor(self, index, parent):
        if self.lockItem(index):
            editor = CRecordListModel.createEditor(self, index, parent)
            column = index.column()
            if column == self.getColIndex('suiteReagent_id'):
                self.setSuiteReagentFIlter(index, editor)
            elif column == self.getColIndex('specimenType_id'):
                item = self._items[index.row()]
                self._cols[column].setSpecimenTypeFilter(item, editor)
            return editor
        return None


    def setSuiteReagentFIlter(self, index, editor):
        item = self._items[index.row()]
        editor.setTestId(forceRef(item.value('test_id')))
        editor.setTissueJournalDate(forceDate(QtGui.qApp.db.translate('TakenTissueJournal', 'id', self._takenTissueJournalId, 'createDatetime')))


class CDelegate(CLocItemDelegate):
    def createEditor(self, parent, option, index):
        column = index.column()
        editor = self._locCreateEditor(index, parent)
        if editor:
            self.connect(editor, SIGNAL('commit()'), self.emitCommitData)
            self.connect(editor, SIGNAL('editingFinished()'), self.commitAndCloseEditor)
        self.editor   = editor
        self.row      = index.row()
        self.rowcount = index.model().rowCount(None)
        self.column   = column
        return editor

    def _locCreateEditor(self, index, parent):
        return index.model().createEditor(index, parent)


class CAnalogTestColumnDelegate(CDelegate):
    def _locCreateEditor(self, index, parent):
        return index.model().createWorkTestEditor(index, parent)

# ###############

class CSamplePreparationInDocTableView(CInDocTableView):
    def __init__(self, parent):
        CInDocTableView.__init__(self, parent)
        self.setItemDelegate(CDelegate(self))
        self.setItemDelegateForColumn(2, CAnalogTestColumnDelegate(self))


    def closeEditor(self, editor, hint):
        self.model().releaseLock()
        CInDocTableView.closeEditor(self, editor, hint)

# ##########################################################

class CSamplePreparationIBMCol(CInDocTableCol):
    tissueTypeId  = 0
    ibm           = 1
    datetimeTaken = 2

    def __init__(self, title, fieldName, width, **params):
        CInDocTableCol.__init__(self, title, fieldName, width, **params)
        self.cache = {}
        self._table = QtGui.qApp.db.table('TakenTissueJournal')
        self.__fieldName = fieldName
        self._valueIdx = 1


    def toString(self, val, record):
        if not val.isValid():
            tissueJournalId = forceRef(record.value('takenTissueJournal_id'))
            if tissueJournalId:
                values = self.cache.get(tissueJournalId, None)
                if not values:
                    tissueTypeId, ibm, datetimeTaken = self.getTissueJournalValues(tissueJournalId)
                    values = tissueTypeId, ibm, datetimeTaken
                    self.cache[tissueJournalId] = values
                    record.append(QtSql.QSqlField(self.__fieldName, QVariant.String))
                val = values[self._valueIdx]
                record.setValue(self.__fieldName, val)
        return val


    def getIBM(self, tissueJournalId):
        return self.getTissueJournalValue(tissueJournalId, CSamplePreparationIBMCol.ibm)


    def getTissueTypeId(self, tissueJournalId):
        return self.getTissueJournalValue(tissueJournalId, CSamplePreparationIBMCol.tissueTypeId)


    def getTissueDatetimeTaken(self, tissueJournalId):
        return self.getTissueJournalValue(tissueJournalId, CSamplePreparationIBMCol.datetimeTaken)


    def getTissueJournalValue(self, tissueJournalId, field):
        values = self.cache.get(tissueJournalId, None)
        if not values:
            tissueTypeId, ibm, datetimeTaken = self.getTissueJournalValues(tissueJournalId)
            values = tissueTypeId, ibm
            self.cache[tissueJournalId] = values
        return values[field]


    def getTissueJournalValues(self, tissueJournalId):
        record = QtGui.qApp.db.getRecord(self._table, 'tissueType_id, externalId, datetimeTaken', tissueJournalId)
        return record.value('tissueType_id'), record.value('externalId'), record.value('datetimeTaken')


class CSamplePreparationDatetimeTakenCol(CSamplePreparationIBMCol):
    def __init__(self, title, fieldName, width, **params):
        CSamplePreparationIBMCol.__init__(self, title, fieldName, width, **params)
        self._valueIdx = 2


class CSamplePreparationTissueTypeCol(CInDocTableCol):
    def __init__(self, title, fieldName, width, ibmCol, **params):
        CInDocTableCol.__init__(self, title, fieldName, width, **params)
        self.ibmCol = ibmCol

    def toString(self, val, record):
        if not val.isValid():
            tissueJournalId = forceRef(record.value('takenTissueJournal_id'))
            tissueTypeId = forceRef(self.ibmCol.getTissueTypeId(tissueJournalId))
            if tissueTypeId:
                val = QtGui.qApp.db.translate('rbTissueType', 'id',
                                              tissueTypeId, 'CONCAT_WS(\'|\', code, name)')
                record.append(QtSql.QSqlField('tissueType', QVariant.String))
            else:
                val = QVariant('')
            record.setValue('tissueType', val)
        return val

# ########

class CResultCol(CInDocTableCol):
    redForegraundValue = QVariant(QtGui.QColor(255, 0, 0))
    notForegraundValue = QVariant()
    def __init__(self, title, fieldName, width, parent, **params):
        CInDocTableCol.__init__(self, title, fieldName, width, **params)
        self._parent = parent


    def flags(self, index):
        result = CInDocTableCol.flags(self)
        row = index.row()
        isEditable = self._parent.isResultEditableByRow(row)
        if not isEditable:
            result = result & (~Qt.ItemIsEditable)
        else:
            result = result | Qt.ItemIsUserCheckable
        return result


    def toCheckState(self, val, record):
        probeId = forceRef(record.value('id'))
        checkedIdx = self._parent.getCheckedResult(probeId)
        fieldName = self.fieldName()
        return QVariant(int(fieldName[-1]) == checkedIdx)


    def getForegroundColor(self, val, record):
        if forceBool(self.toCheckState(val, record)):
            norm = forceString(record.value('norm'))
            parts = norm.split('-')
            if len(parts) == 2:
                try:
                    bottom = float(parts[0].replace(',', '.'))
                    top    = float(parts[1].replace(',', '.'))
                except ValueError:
                    return CResultCol.notForegraundValue
                val, ok = val.toDouble()
                if ok:
                    if bottom > val or val > top:
                        return CResultCol.redForegraundValue
        return CResultCol.notForegraundValue


class CSamplePreparationPersonCol(CInDocPersonCol):
    pass


class CSpecimenTypeCol(CRBInDocTableCol):
    class CSpecimenTypeComboBox(CRBComboBox):
        def __init__(self, parent):
            CRBComboBox.__init__(self, parent)
            self.setTable('rbSpecimenType', addNone=True, needCache=False)

        def setExternalFilter(self, testId=None, equipmentId=None):
            if testId or equipmentId:
                table = QtGui.qApp.db.table(self._tableName)
                filter = table['id'].inlist(self._getFilterList(testId, equipmentId))
                self.setFilter(filter)

        @staticmethod
        def _getFilterList(testId, equipmentId):
            db = QtGui.qApp.db
            table = db.table('rbEquipment_Test')
            cond = []
            if testId:
                cond.append(table['test_id'].eq(testId))
            if equipmentId:
                cond.append(table['equipment_id'].eq(equipmentId))
            return db.getDistinctIdList(table, 'specimenType_id', cond)


    def createEditor(self, parent):
        editor = CSpecimenTypeCol.CSpecimenTypeComboBox(parent)
        editor.setShowFields(self.showFields)
        editor.setPreferredWidth(self.preferredWidth)
        return editor


    def setSpecimenTypeFilter(self, item, editor):
        testId = forceRef(item.value('workTest_id'))
        equipmentId = forceRef(item.value('equipment_id'))
        editor.setExternalFilter(testId, equipmentId)


class CSamplePreparationModel(CRecordListModel, CRecordLockMixin):
    probeNone          = 0
    probeInWaiting     = 1
    probeInWorking     = 2
    probeIsFinished    = 3
    probeWithoutResult = 4
    probeIsAssigned    = 5
    probeExportToLIS   = 6
    probeImportFromLIS = 7

    probeResultIndexNull = 4

    importResultFullResultField = 0 # Все поля результат заняты, некуда импортировать.
    importResultCannotFindProbe = 1 # Не удалось идентифицировать пробу
    importResultOk = 2
    importResultValueIsEmpty = 3
    importResultCannotFindTest = 4
    importResultExists = 5

#    class CLocInDocTripodCol(CInDocTableCol):
#        def __init__(self, name, fieldName):
#            CInDocTableCol.__init__(self, name, fieldName, 10)
#            self.low = 0
#            self.high = 9
#            self.setReadOnly(True)
#
#
#        def createEditor(self, parent):
#            editor    = QLineEdit(parent)
#            validator = QIntValidator(self.low, self.high, editor)
#            editor.setValidator(validator)
#            return editor
#
#
#        def setEditorData(self, editor, value, record):
#            editor.setText(forceString(forceInt(value)))
#            editor.selectAll()
#
#
#        def getEditorData(self, editor):
#            value = editor.text()
#            if value:
#                result = toVariant(int(value))
#            else:
#                result = QVariant()
#            return result


    class CExternalNormUnit(CInDocTableCol):
        def __init__(self):
            CInDocTableCol.__init__(self, u'Норма ЛИС', 'id', 10)
            self.setReadOnly()


        def toString(self, val, record):
            if record:
                externalNorm = forceString(record.value('externalNorm'))
                externalUnit = forceString(record.value('externalUnit'))
                if externalNorm and externalUnit:
                    return ' | '.join([externalNorm, externalUnit])
                return externalNorm + externalUnit
            return u''


    def __init__(self, parent):
        CRecordListModel.__init__(self, parent)
        CRecordLockMixin.__init__(self)
        probeCol = CInDocTableCol(u'Проба', 'externalId', 6).setReadOnly()
        self._IBMCol = IBMCol = CSamplePreparationIBMCol(u'ИБМ', 'ibm', 6).setReadOnly()
        self._tissueDatetimeTakenCol = CSamplePreparationDatetimeTakenCol(u'Забор биоматериала', 'datetimeTaken', 6).setReadOnly()
        statusCol = CEnumInDocTableCol(u'Статус', 'status', 8, probeStatuses).setReadOnly()
        workTestCol = CWorkTestCol(u'Тест', 'workTest_id', 10, 'rbTest', showFields=2)
        specimenTypeCol = CSpecimenTypeCol(u'Тип образца', 'specimenType_id', 10, 'rbSpecimenType', showFields=2)
        suiteReagentCol = CRBSuiteReagentCol(u'Набор реагентов', 'suiteReagent_id', 10, 'SuiteReagent', showFields=2)
        equipmentCol = CRBInDocTableCol(u'Оборудование', 'equipment_id', 10, 'rbEquipment', showFields=2).setReadOnly()
        tissueTypeCol = CSamplePreparationTissueTypeCol(u'Тип биоматериала', 'tissueType', 6, IBMCol).setReadOnly()
        unitCol = CRBInDocTableCol(u'Ед.изм.', 'unit_id', 10, 'rbUnit').setReadOnly()
        normCol = CInDocTableCol(u'Норма', 'norm', 10).setReadOnly()
        externalEvaluationCol = CInDocTableCol(u'Оценка', 'externalEvaluation', 10).setReadOnly()
        personCol = CSamplePreparationPersonCol(u'Исполнитель', 'person_id', 10, 'vrbPersonWithSpeciality', showFields=2)
        self.addCol(probeCol)
        self.addExtCol(IBMCol, QVariant.String)
        self.addCol(CBoolInDocTableCol(u'Срочное', 'isUrgent', 10))
        self.addCol(statusCol)
        self.addCol(workTestCol)
        self.addCol(specimenTypeCol)
        self.addCol(normCol)
        self.addCol(externalEvaluationCol)
        self.addCol(CSamplePreparationModel.CExternalNormUnit())
#        self.addCol(CInDocTableCol(u'Норма ЛИС', 'externalNorm', 10).setReadOnly())
#        self.addCol(CInDocTableCol(u'Ед.изм. ЛИС', 'externalUnit', 10).setReadOnly())
        self.addCol(personCol.setReadOnly(not QtGui.qApp.userHasRight(urEditProbePerson)))
        self.addCol(CResultCol(u'Результат1', 'result1', 6, self))
        self.addCol(CResultCol(u'Результат2', 'result2', 6, self))
        self.addCol(CResultCol(u'Результат3', 'result3', 6, self))
        self.addCol(suiteReagentCol)
        self.addCol(equipmentCol)
        self.addExtCol(tissueTypeCol, QVariant.String)
        self.addCol(unitCol)
        #self.addCol(CSamplePreparationModel.CLocInDocTripodCol(u'Штатив', 'tripodNumber'))
        #self.addCol(CSamplePreparationModel.CLocInDocTripodCol(u'Место в штативе', 'placeInTripod'))
        self.addCol(CInDocTableCol(u'Штатив', 'tripodNumber', 10).setReadOnly())
        self.addCol(CInDocTableCol(u'Место в штативе', 'placeInTripod', 10).setReadOnly())
        self.addHiddenCol('takenTissueJournal_id')
        self.addHiddenCol('typeName')
        self.addHiddenCol('resultIndex')
        self.addHiddenCol('test_id')
        self.addHiddenCol('externalNorm')
        self.addHiddenCol('externalUnit')
        self.addHiddenCol('assistant_id')
        self.addHiddenCol('exportName')
        self.addHiddenCol('exportDatetime')
        self.addHiddenCol('exportPerson_id')
        self.addHiddenCol('importName')
        self.addHiddenCol('importDatetime')
        self.addHiddenCol('importPerson_id')
        self.addHiddenCol('course')

        self._originalProbeItems = {}
        self._mapIdToOriginalKey = {}
        self._additionalMapIdToOriginalKey = {}
        self._additionalOriginalProbeItems = {}
        self._mapExternalId2Rows = {}
        self._mapWorkTestId2Rows = {}
        self._mapEquipmentId2Rows = {}
        self._mapExternalId2WorkTestIdList = {}

        self._checkedRowsList = []
        self._mapIdToCheckedResults = {} # list [editable(bool), checked result index(int)]
        self._mapIdToItem           = {}
        self._resultColumnsIndexs = [self.getColIndex('result1'),
                                     self.getColIndex('result2'),
                                     self.getColIndex('result3')]
        self._idList = []
        self._table = QtGui.qApp.db.table('Probe')
        self._parent = parent
        self._itemWithoutImportValueHelper = smartDict(checkedIdList=[],
                                                       mapId2Item={})
        self._mapTestCodeToId = {}


    table = property(lambda self: self._table)


    def applayItemWithoutImportValue(self):
        db = QtGui.qApp.db
        for item in self._itemWithoutImportValueHelper.mapId2Item.values():
            item.setValue('status', QVariant(CSamplePreparationModel.probeImportFromLIS))
            item.setValue('resultIndex', QVariant(CSamplePreparationModel.probeResultIndexNull))
            db.insertOrUpdate('Probe', item)
            if hasattr(self, 'receivedItemsList'):
                self.receivedItemsList.append(item)
        self.resetItemWithoutImportValueHelper()


    def resetItemWithoutImportValueHelper(self):
        self._itemWithoutImportValueHelper.checkedIdList = []
        self._itemWithoutImportValueHelper.mapId2Item.clear()


    def _setResultCheckEditable(self, probeId):
        self._mapIdToCheckedResults[probeId][0] = True


    def _checkAction(self, testId, takenTissueId, assistantId, personId):
        db = QtGui.qApp.db
        tableAction = db.table('Action')
        eventId = None
        setPersonId = personId or assistantId or forceRef(db.translate('OrgStructure',
                                                                       'id', QtGui.qApp.currentOrgStructureId(),
                                                                       'chief_id'))
        plannedEndDate = QDateTime()
        jobValueList = []
        dissabledActionTypeIdList = []
        mapJobTicket2Job = {}
        mapJob2JobType = {}
        actionRecordList = db.getRecordList(tableAction, '*', [tableAction['deleted'].eq(0),
                                                               tableAction['takenTissueJournal_id'].eq(takenTissueId)])
        for actionRecord in actionRecordList:
            action = CAction(record=actionRecord)
            actionType = action.getType()
            propertyTypeItemsList = actionType.getPropertiesById().items()
            for propertyTypeId, propertyType in propertyTypeItemsList:
                if testId == propertyType.testId:
                    return True
                if propertyType.isJobTicketValueType():
                    jobTicketId = action.getPropertyById(propertyTypeId).getValue()
                    if jobTicketId:
                        jobId = mapJobTicket2Job.get(jobTicketId, None)
                        if jobId is None:
                            jobId = forceInt(db.translate('Job_Ticket', 'id', jobTicketId, 'master_id'))
                            mapJobTicket2Job[jobTicketId] = jobId
                        jobTypeId = mapJob2JobType.get(jobId, None)
                        if jobTypeId is None and jobId:
                            jobTypeId = forceInt(db.translate('Job', 'id', jobId, 'jobType_id'))
                            mapJob2JobType[jobId] = jobTypeId
                        if jobTypeId and jobTicketId:
                            jobValueList.append((jobTypeId, jobTicketId))
            eventId = forceRef(actionRecord.value('event_id'))
            plannedEndDate = forceDateTime(actionRecord.value('plannedEndDate'))
            dissabledActionTypeIdList.append(forceRef(actionRecord.value('actionType_id')))

        if jobValueList:
            jobTypeId, jobTicketId = jobValueList[0]
            tableJTAT = db.table('rbJobType_ActionType')
            tableActionType = db.table('ActionType')
            table = tableJTAT.leftJoin(tableActionType, tableActionType['id'].eq(tableJTAT['actionType_id']))
            cond = [tableActionType['deleted'].eq(0),
                    tableJTAT['master_id'].eq(jobTypeId)]
            if dissabledActionTypeIdList:
                cond.append(tableJTAT['actionType_id'].notInlist(dissabledActionTypeIdList))
            actionTypeIdList = db.getDistinctIdList(table, tableJTAT['actionType_id'].name(), cond)
            QtGui.qApp.setJTR(jobValueList)
            try:
                for actionTypeId in actionTypeIdList:
                    actionRecord = tableAction.newRecord()
                    actionRecord.setValue('actionType_id', QVariant(actionTypeId))
                    actionRecord.setValue('event_id', QVariant(eventId))
                    actionRecord.setValue('plannedEndDate', QVariant(plannedEndDate))
                    actionRecord.setValue('setPerson_id', QVariant(setPersonId))
                    actionRecord.setValue('takenTissueJournal_id', QVariant(takenTissueId))

                    action = CAction(record=actionRecord)
                    actionType = action.getType()
                    propertyTypeItemsList = actionType.getPropertiesById().items()

                    jobTicketProperty = None
                    testOk = False

                    for propertyTypeId, propertyType in propertyTypeItemsList:
                        testOk = testOk or testId == propertyType.testId
                        if not jobTicketProperty and propertyType.isJobTicketValueType():
                            jobTicketProperty = action.getPropertyById(propertyTypeId)
                        if testOk and jobTicketProperty:
                            jobTicketProperty.setValue(jobTicketId)
                            action.save(idx=db.getCount('Action', 'id', 'event_id=%d'%eventId))
                            return True
            finally:
                QtGui.qApp.unsetJTR(jobValueList)
        return False


    def _appendTest(self, testId, takenTissueId, externalId, sameItem, assistantId, personId, appendIntoModel=True):
        if not sameItem:
            return

        if appendIntoModel:
            record = self._table.newRecord(fields=self.getColsForItems())
        else:
            record = self._table.newRecord()

        record.setValue('test_id',               QVariant(testId))
        record.setValue('workTest_id',           QVariant(testId))
        record.setValue('externalId',            QVariant(externalId))
        record.setValue('takenTissueJournal_id', QVariant(takenTissueId))

        record.setValue('status',                sameItem.value('status'))
        record.setValue('specimenType_id',       sameItem.value('specimenType_id'))
        record.setValue('suiteReagent_id',       sameItem.value('suiteReagent_id'))
        record.setValue('equipment_id',          sameItem.value('equipment_id'))
        record.setValue('person_id',             sameItem.value('person_id'))
        record.setValue('typeName',              sameItem.value('typeName'))
        record.setValue('isUrgent',              sameItem.value('isUrgent'))

        itemId = QtGui.qApp.db.insertRecord(self._table, record)

        self._checkAction(testId, takenTissueId, assistantId, personId)

        if appendIntoModel:
            self._idList.append(itemId)
            self._items.append(record)
            count = len(self._items)
            rootIndex = QModelIndex()
            self.beginInsertRows(rootIndex, count, count)
            self.insertRows(count, 1, rootIndex)
            self.endInsertRows()
            self.applyItemsSettings()
            self.emitAllChanged()
            return record, len(self._items)-1

        self.applyItemsSettings()
        self.emitAllChanged()

        return record


    def setResult(self, arg):
        db = QtGui.qApp.db

        clientId = arg.get('clientId') or arg.get('clientId3') or arg.get('laboratoryPatientId') or arg.get('clientLastName')
        try:
            clientId = int(clientId)
        except:
            return CSamplePreparationModel.importResultCannotFindProbe

        externalId        = arg['externalId']
        testId_like_code  = arg['testId_like_code']
        testCode          = arg['testCode']
        testName          = arg['testName']
        value             = arg['value']
        referenceRange    = arg['referenceRange']
        abnormalFlags     = arg['abnormalFlags']
        unit              = arg['unit']
        resultStatus      = arg['resultStatus']
        assistantCode     = arg['assistantCode']
        personCode        = arg['personCode']
        rewrite           = arg['rewrite']
        onlyFromModel     = arg['onlyFromModel']
#        filterEquipmentId = arg['filterEquipmentId']
        equipmentId       = arg['equipmentId']
        dataFileName      = arg['dataFileName']
        resultOnFact      = arg['resultOnFact']
        resultType        = arg['resultType']
        specimenCode = arg['specimenDescr']
        orderComment = arg['orderComment']


        def _getAssistantAndPerson(assistantCode, personCode):
            assistantId = forceRef(db.translate('Person', 'code', assistantCode, 'id')) if assistantCode else None
            personId    = forceRef(db.translate('Person', 'code', personCode,    'id')) if personCode else None
            return assistantId, personId


        def _getFullActualTestIdList(testId):
            return [testId]+db.getIdList('rbTest_AnalogTest', 'analogTest_id', 'master_id=%d'%testId)


        def _list2Unicode(val):
            if isinstance(val, list):
                result = u''
                for v in val:
                    result += unicode(_list2Unicode(v))
                return result
            else:
                return unicode(val)


        def _getActualItems(testId, itemList, onlyFromModel, statusList):
            idList = self._mapIdToItem.keys()
            def _applyMapItemWithoutImportValue():
                if resultOnFact:
                    for item in itemList:
                        probeId = forceRef(item.value('id'))
                        if ((not onlyFromModel) or (probeId in idList)) and probeId not in self._itemWithoutImportValueHelper.checkedIdList:
                            self._itemWithoutImportValueHelper.checkedIdList.append(probeId)
                            if forceInt(item.value('status')) == CSamplePreparationModel.probeExportToLIS:
                                self._itemWithoutImportValueHelper.mapId2Item[probeId] = item
            # WFT? функция, определённая внутри другой и вызываемая только в одном месте
            _applyMapItemWithoutImportValue()
            tmpItem = None
#            actualItem = None
            for actualTestId in _getFullActualTestIdList(testId):
                for item in itemList:
                    probeId = forceRef(item.value('id'))
                    if onlyFromModel and probeId not in idList:
                        continue
                    tmpItem = tmpItem or item
                    if forceRef(item.value('workTest_id')) == actualTestId:
                        if forceInt(item.value('status')) in statusList:
                            if resultOnFact and probeId in self._itemWithoutImportValueHelper.mapId2Item:
                                del self._itemWithoutImportValueHelper.mapId2Item[probeId]
                            return item, forceRef(item.value('takenTissueJournal_id')), False, None
                        else:
                            return None, None, False, CSamplePreparationModel.importResultExists
            if tmpItem:
                return None, forceRef(tmpItem.value('takenTissueJournal_id')), True, None
            return None, None, False, CSamplePreparationModel.importResultCannotFindProbe


        def _getSourceItem(itemList, clientId):
            for item in itemList:
                takenTissueId = forceRef(item.value('takenTissueJournal_id'))
                if takenTissueId:
                    if clientId == forceRef(db.translate('TakenTissueJournal', 'id', takenTissueId, 'client_id')):
                        return item
            return None


        def _getItem(externalId, equipmentId, testId, clientId, assistantId, personId, onlyFromModel):
            tableProbe = db.table('Probe')
            tableTissueJournal = db.table('TakenTissueJournal')
            queryTable = tableProbe.innerJoin(tableTissueJournal,
                                         tableTissueJournal['id'].eq(tableProbe['takenTissueJournal_id']))

            statusList = [CSamplePreparationModel.probeExportToLIS]
            if rewrite and not resultOnFact:
                statusList.extend([CSamplePreparationModel.probeWithoutResult,
                                   CSamplePreparationModel.probeImportFromLIS])

            cond = [
                    tableProbe['externalId'].eq(externalId),
                    #tableProbe['equipment_id'].eq(equipmentId),
                    tableTissueJournal['client_id'].eq(clientId)
                ]
            if equipmentId:
                if type(equipmentId) == list:
                    cond.append(tableProbe['equipment_id'].inlist(equipmentId))
                else:
                    cond.append(tableProbe['equipment_id'].eq(equipmentId))
            if not rewrite:
                cond.append(tableProbe['status'].inlist(statusList))
            itemList = db.getRecordList(queryTable, 'Probe.*', cond)
            if not itemList:
                return (None, CSamplePreparationModel.importResultCannotFindProbe)
            item, takenTissueId, mustAppendTest, error = _getActualItems(testId, itemList, onlyFromModel, statusList)
            if error:
                return None, error
            if not item and mustAppendTest:
                if takenTissueId:
                    item = self._appendTest(testId, takenTissueId, externalId, _getSourceItem(itemList, clientId),
                                            assistantId, personId, appendIntoModel=False)
            return (item, None)


        def _setImportProperty(item, fileName):
            item.setValue('importName', QVariant(fileName))
            item.setValue('importDatetime', QVariant(QDateTime.currentDateTime()))
            item.setValue('importPerson_id', QVariant(QtGui.qApp.userId))


        def _insertOrUpdate(item):
            tableProbe = db.table('Probe')
            db.insertOrUpdate(tableProbe, item)
            self.applyItemsSettings()
            self.emitAllChanged()

        def _updateOrderComment(item, orderComment):
            if orderComment:
                tableTTJ = db.table('TakenTissueJournal')
                record = tableTTJ.newRecord(fields=['id', 'note'])
                record.setValue('id', item.value('takenTissueJournal_id'))
                record.setValue('note', QVariant(orderComment))
                db.updateRecord(tableTTJ, record)


        if not equipmentId:
            tableProbe = db.table('Probe')
            equipmentId = db.getDistinctIdList(tableProbe, [tableProbe['equipment_id']],  [tableProbe['externalId'].eq(externalId)])

        testId = self._getTestId(testId_like_code or testCode, testName, resultType if resultType else None, equipmentId,  specimenCode)
        if not testId:
            return CSamplePreparationModel.importResultCannotFindTest

        assistantId, personId = _getAssistantAndPerson(assistantCode, personCode)
        (item, error) = _getItem(externalId, equipmentId, testId, clientId, assistantId, personId, onlyFromModel)
        if error:
            return error
        if not item:
            return CSamplePreparationModel.importResultCannotFindProbe

        value = self.preprocessResultValue(equipmentId, value)

        if hasattr(self, 'receivedItemsList'):
            self.receivedItemsList.append(item)

        if resultOnFact and forceInt(item.value('status')) != CSamplePreparationModel.probeExportToLIS:
            return CSamplePreparationModel.importResultOk

        if resultStatus.upper() == 'X' or (resultOnFact and (value is None or value == u'')):
            item.setValue('status', QVariant(CSamplePreparationModel.probeImportFromLIS))
            item.setValue('resultIndex', QVariant(CSamplePreparationModel.probeResultIndexNull))
            item.setValue('assistant_id', QVariant(assistantId))
            item.setValue('person_id', QVariant(personId))
            _setImportProperty(item, dataFileName)
            _insertOrUpdate(item)
            _updateOrderComment(item, orderComment)
            return CSamplePreparationModel.importResultOk
        else:
            if value:
                for rIndex in ('1', '2', '3'):
                    resultFieldName = 'result'+rIndex
                    if not forceString(item.value(resultFieldName)) or (rIndex=='3' and rewrite):
                        item.setValue(resultFieldName, QVariant(value))
                        item.setValue('status', QVariant(CSamplePreparationModel.probeImportFromLIS))
                        item.setValue('resultIndex', QVariant(int(rIndex)))
                        item.setValue('assistant_id', QVariant(assistantId))
                        item.setValue('person_id', QVariant(personId))
                        item.setValue('externalEvaluation', QVariant(abnormalFlags))
                        if not forceString(item.value('externalNorm')):
                            item.setValue('externalNorm', QVariant(_list2Unicode(referenceRange)))
                        if not forceString(item.value('externalUnit')) and referenceRange:
                            item.setValue('externalUnit', QVariant(unit))
                        if unit:
                            unitId = db.translate('rbUnit', 'code', unit, 'id')
                            if unitId:
                                item.setValue('unit_id', QVariant(unitId))
                        _setImportProperty(item, dataFileName)
                        _insertOrUpdate(item)
                        _updateOrderComment(item, orderComment)
                        if hasattr(self, 'importedItemsList'):
                            self.importedItemsList.append(item)
                        return CSamplePreparationModel.importResultOk
                return CSamplePreparationModel.importResultFullResultField
            else:
                return CSamplePreparationModel.importResultValueIsEmpty


    def preprocessResultValue(self, equipmentId, value):
        if type(equipmentId) == int:
            description = CEquipmentDescription.getDescription(equipmentId)
            if description:
                preprocess = description['address'].get('preprocess', {})
                for task in preprocess.keys():
                    if task == 'sub':
                        try:
                            for processList in preprocess[task]:
                                value = re.sub(processList[0], processList[1], value)
                        except:
                            pass
        return value


    def _getTestId(self, code, name, type_=None, equipmentId = None,  specimenCode = None):
        #data = CRBModelDataCache.getData('rbTest')
        #return data.getIdByCode(code)
        if not code and name:
            code = name
        testId = self._mapTestCodeToId.get((code, type_, specimenCode), None)
        if not testId:
            #testId = forceRef(QtGui.qApp.db.translate('rbEquipment_Test', 'hardwareTestCode', code, 'test_id'))
            db = QtGui.qApp.db
            table = db.table('rbEquipment_Test')
            cond = [table['hardwareTestCode'].eq(code)]
            if equipmentId:
                if type(equipmentId) == list:
                    cond.append(table['equipment_id'].inlist(equipmentId))
                else:
                    cond.append(table['equipment_id'].eq(equipmentId))
            if specimenCode:
                cond.append(db.joinOr([ table['hardwareSpecimenCode'].eq(specimenCode),  table['hardwareSpecimenCode'].eq('') ]))
            if type_:
                cond.append(db.joinOr([table['resultType'].eq(type_), table['resultType'].isNull()]))
            recordList = db.getRecordList(table, where=cond, order='resultType DESC')
            if recordList:
                testId = forceRef(recordList[0].value('test_id'))
                self._mapTestCodeToId[(code, type_, specimenCode)] = testId
        return testId


    def getItemById(self, probeId):
        return self._mapIdToItem[probeId][0]


    def addObject(self, name, object):
        self.__setattr__(name, object)
        object.setObjectName(name)


    def setData(self, index, value, role=Qt.EditRole):
        try:
            column = index.column()
            row = index.row()
            if role == Qt.CheckStateRole and column in self._resultColumnsIndexs:
                fieldName = self._cols[column].fieldName()
                resultIndex = int(fieldName[-1])
                self.setCheckedResultByRow(row, resultIndex)
                self.emitRowChanged(row)
                return True
            else:
                record = self._items[row]
                oldRecord = QtSql.QSqlRecord(record)
                result = CRecordListModel.setData(self, index, value, role)
                if result and value.isValid():
                    if column in self._resultColumnsIndexs:
                        record.setValue('status', QVariant(CSamplePreparationModel.probeInWorking))
                        self.emit(SIGNAL('resetProbeStatus()'))
                        if not forceRef(record.value('person_id')):
                            record.setValue('person_id', QVariant(QtGui.qApp.userId))
                        self.saveItem(record, oldRecord=oldRecord)
                    elif column in (self.getColIndex('tripodNumber'), self.getColIndex('placeInTripod')):
                        self.saveItem(record, oldRecord=oldRecord)
                return result
        except:
            return False


    def setStatus(self, status):
        for item in self._items:
            item.setValue('status', QVariant(status))
            oldRecord = QtSql.QSqlRecord(item)
            self.saveItem(item, oldRecord=oldRecord)
        self.emitAllChanged()


    def setStatusItem(self, item, status=None):
        item.setValue('status', QVariant(status))
        oldRecord = QtSql.QSqlRecord(item)
        self.saveItem(item, oldRecord=oldRecord)


    def releaseLock(self):
        CRecordLockMixin.releaseLock(self)


    def setDataForOnlyTestProxy(self, mainProbeId, testColumn, testRow, value, role):
        index = self.getIndexForTestsProxy(mainProbeId, testColumn, testRow)
        return self.setData(index, value, role)


    def recountSuiteReagentAmount(self, oldSuiteReagentId, newSuiteReagentId):
        stmtTemplate = 'UPDATE `SuiteReagent` SET execTestQuantity=execTestQuantity%(action)s1 WHERE SuiteReagent.`id`=%(suiteReagentId)d'
        if oldSuiteReagentId:
            self.decreaseSuiteReagentAmount(stmtTemplate, oldSuiteReagentId)
        if newSuiteReagentId:
            self.increaseSuiteReagentAmount(stmtTemplate, newSuiteReagentId)


    def decreaseSuiteReagentAmount(self, stmtTemplate, suiteReagentId):
        QtGui.qApp.db.query(stmtTemplate%{'action':'-', 'suiteReagentId':suiteReagentId})


    def increaseSuiteReagentAmount(self, stmtTemplate, suiteReagentId):
        QtGui.qApp.db.query(stmtTemplate%{'action':'+', 'suiteReagentId':suiteReagentId})


    def setIdList(self, idList, force=False):
        if idList != self._idList or force:
            self._idList = idList
            db = QtGui.qApp.db
            table = self._table
            cols = self.getColsForItems()
            self._items = db.getRecordList(table, cols, table['id'].inlist(idList))
            self.applyItemsSettings()
            self.reset()
            return True
        return False


    def getColsForItems(self):
        cols = []
        for col in self._cols:
            if not col.external():
                cols.append(col.fieldName())
        for col in self._hiddenCols:
            cols.append(col)
        cols.append('id')
        return cols


    def resetProperties(self):
        self._checkedRowsList = []
        self._mapIdToCheckedResults.clear()
        self._mapIdToItem.clear()
        self._mapIdToOriginalKey.clear()
        self._additionalMapIdToOriginalKey.clear()
        self._additionalOriginalProbeItems.clear()
        self._originalProbeItems.clear()
        self._mapExternalId2Rows.clear()
        self._mapWorkTestId2Rows.clear()
        self._mapEquipmentId2Rows.clear()
        self._mapExternalId2WorkTestIdList.clear()
        resetTissueJournalActionTypeStackHelper()
        resetContainerTypeCache()


    def applyItemsSettings(self):
        self.resetProperties()
        lockCacheTissueJournalToTissueType = {}
        for row, item in enumerate(self._items):
            id = forceRef(item.value('id'))
#            result1  = forceString(item.value('result1'))
#            result2  = forceString(item.value('result2'))
#            result3  = forceString(item.value('result3'))
            status   = forceInt(item.value('status'))
            editable = status in (CSamplePreparationModel.probeInWaiting,
                                  CSamplePreparationModel.probeInWorking,
                                  CSamplePreparationModel.probeImportFromLIS)
            checkedResultIndex = forceInt(item.value('resultIndex'))
            if checkedResultIndex:
                if editable:
                    self._checkedRowsList.append(row)

            self._mapIdToCheckedResults[id] = [editable, checkedResultIndex, row]
            self._mapIdToItem[id] = (item, row)

            externalId      = forceString(item.value('externalId'))
            tissueJournalId = forceRef(item.value('takenTissueJournal_id'))

            actionTypeId    = getNextTissueJournalActionType(tissueJournalId, forceRef(item.value('test_id')))
            if actionTypeId:
                tissueTypeId = lockCacheTissueJournalToTissueType.get(tissueJournalId, None)
                if not tissueTypeId:
                    tissueTypeId = forceRef(QtGui.qApp.db.translate('TakenTissueJournal', 'id', tissueJournalId, 'tissueType_id'))
                    lockCacheTissueJournalToTissueType[tissueJournalId] = tissueTypeId

                containerValues, containerTypeId = self.getContainerValues(actionTypeId, tissueTypeId)
                key = (externalId, containerTypeId, tissueJournalId)
                self._mapIdToOriginalKey[id] = key
                if key not in self._originalProbeItems.keys():
                    self._originalProbeItems[key] = [[id],
                                                     externalId,
                                                     forceString(self._tissueDatetimeTakenCol.toString(QVariant(), item)),
                                                     forceString(self._IBMCol.toString(QVariant(), item))]
                    if containerValues:
                        self._originalProbeItems[key].extend(containerValues)
                    else:
                        self._originalProbeItems[key] += [None]*6
                else:
                    self.appendOriginalProbeItemValues(key, id)

            externalIdRowList = self._mapExternalId2Rows.setdefault(externalId, [])
            externalIdRowList.append(row)

            workTestId = forceRef(item.value('workTest_id'))
            self._mapWorkTestId2Rows.setdefault(workTestId, []).append(row)

            self._mapExternalId2WorkTestIdList.setdefault(externalId, []).append(workTestId)

            equipmentId = forceRef(item.value('equipment_id'))
            self._mapEquipmentId2Rows.setdefault(equipmentId, []).append(row)


            if not checkedResultIndex and status == CSamplePreparationModel.probeImportFromLIS:
                self.setCheckedResultByRow(row, 1)


    def appendOriginalProbeItemValues(self, key, id, map=None):
        if map is None:
            map = self._originalProbeItems
        map[key][0].append(id)
        tissueAmount = map[key][8]
        if tissueAmount:
            amount = tissueAmount * len(map[key][0])
            containerCapacity = map[key][9]
            if containerCapacity:
                amount = amount/containerCapacity
            map[key][7] = amount


    def getOriginalProbeItemsKeys(self):
        keyList = self._originalProbeItems.keys()
        keyList.sort(key=lambda keyItem: keyItem[0])
        return keyList


    def onlyProbeProxyValue(self, row, column):
        keyList = self.getOriginalProbeItemsKeys()
        key = keyList[row]
        if column != 3:
            return self._originalProbeItems[key][column+1]
        else:
            idList = self._originalProbeItems[key][0]
            status  = None
            allSame = True
            for id in idList:
                item = self._mapIdToItem[id][0]
                locStatus = forceInt(item.value('status'))
                if status is None:
                    status = locStatus
                if status != locStatus:
                    allSame = False

            resultStatus = 0

            if allSame:
                if status in (CSamplePreparationModel.probeIsFinished, CSamplePreparationModel.probeWithoutResult):
                    resultStatus = CSamplePreparationModel.probeIsFinished
                else:
                    resultStatus = status
            else:
                resultStatus = CSamplePreparationModel.probeInWorking

            return probeStatuses[resultStatus]


    def originalProbeCount(self):
        return len(self._originalProbeItems.keys())


    def onlyTestsProxyValue(self, mainProbeId, testColumn, testRow, role):
        return self.data(self.getIndexForTestsProxy(mainProbeId, testColumn, testRow), role)


    def onlyTestsProxyFlags(self, mainProbeId, testColumn, testRow):
        return self.flags(self.getIndexForTestsProxy(mainProbeId, testColumn, testRow))


    def getIndexForTestsProxy(self, mainProbeId, testColumn, testRow):
        row = self.getRowForTestsProxy(mainProbeId, testRow)
        return self.index(row, testColumn+2)


    def getRowForTestsProxy(self, mainProbeId, testRow):
        key = self._mapIdToOriginalKey[mainProbeId]
        probeTestId = self._originalProbeItems[key][0][testRow]
        return self._mapIdToItem[probeTestId][1]


    def originalProbeTestsCount(self, probeId):
        if probeId:
            return len(self.originalProbeTestsIdList(probeId))
        return 0


    def originalProbeTestsIdList(self, probeId):
        if probeId:
            key, map = self.forceKey(probeId)
            if key is not None:
                return map[key][0]
        return []


    def forceKey(self, probeId):
        map = self._originalProbeItems
        result = self._mapIdToOriginalKey.get(probeId, None)
        if result is None:
            map = self._additionalOriginalProbeItems
            result = self._additionalMapIdToOriginalKey.get(probeId, None)
            if result is None:
                db   = QtGui.qApp.db
                item = db.getRecord('Probe', '*', probeId)
                if item:
                    tissueJournalId = forceRef(item.value('takenTissueJournal_id'))
                    tissueTypeId    = forceRef(db.translate('TakenTissueJournal', 'id', tissueJournalId, 'tissueType_id'))
                    testId          = forceRef(item.value('test_id'))
                    externalId      = forceString(item.value('externalId'))
                    actionTypeId    = getNextTissueJournalActionType(tissueJournalId, testId)
                    containerValues, containerTypeId = self.getContainerValues(actionTypeId, tissueTypeId)
                    result = key = (externalId, containerTypeId)
                    self._additionalMapIdToOriginalKey[probeId] = key

                    table = db.table('Probe')
                    cond = [table['takenTissueJournal_id'].eq(tissueJournalId),
                            table['externalId'].eq(externalId),
                            table['containerType_id'].eq(containerTypeId),
                            table['id'].ne(probeId)]

                    probeRecordList = db.getRecordList(table, '*', cond)
                    probeRecordList.insert(0, item)
                    for item in probeRecordList:
                        probeId = forceRef(item.value('id'))
                        self._mapIdToItem[probeId] = (item, None)
                        if key not in self._additionalOriginalProbeItems.keys():
                            self._additionalOriginalProbeItems[key] = [[probeId],
                                                             externalId,
                                                             forceString(self._tissueDatetimeTakenCol.toString(QVariant(), item)),
                                                             forceString(self._IBMCol.toString(QVariant(), item))]
                            if containerValues:
                                self._additionalOriginalProbeItems[key].extend(containerValues)
                            else:
                                self._additionalOriginalProbeItems[key] += [None]*6
                        else:
                            self.appendOriginalProbeItemValues(key, probeId, map=map)
        return result, map


    def getOriginalProbeItemsList(self, probeId):
        result = []
        key, map = self.forceKey(probeId)
        idList = map[key][0]
        for id in idList:
            result.append(self._mapIdToItem[id][0])
        return result


    def getContainerValues(self, actionTypeId, tissueTypeId):
        return getContainerTypeValues(actionTypeId, tissueTypeId)


    def getRowById(self, probeId):
        values = self._mapIdToCheckedResults.get(probeId, None)
        if values:
            return values[2]
        return -1


    def getIdByRow(self, row):
        if 0 <= row and row < len(self._items):
            return forceRef(self._items[row].value('id'))


    def isResultEditableByRow(self, row):
        probeId = self.getIdByRow(row)
        if probeId:
            return self.isResultEditable(probeId)
        return False


    def isResultEditable(self, probeId):
        return self._mapIdToCheckedResults[probeId][0]


    def setResultEditableByRow(self, row, editable):
        probeId = self.getIdByRow(row)
        if probeId:
            return self.setResultEditable(probeId, editable)


    def setResultEditable(self, probeId, editable):
        values = self._mapIdToCheckedResults[probeId]
        values[0] = editable


    def getCheckedResultByRow(self, row):
        probeId = self.getIdByRow(row)
        if probeId:
            return self.getCheckedResult(probeId)
        return 0


    def getCheckedResult(self, probeId):
        return self._mapIdToCheckedResults[probeId][1]


    def setCheckedResultByRow(self, row, idx):
        probeId = self.getIdByRow(row)
        if probeId:
            self.setCheckedResult(probeId, idx, row)


    def setCheckedResult(self, probeId, idx, row=None):
        values = self._mapIdToCheckedResults[probeId]
        currentIdx = values[1]
        if currentIdx:
            if currentIdx == idx:
                idx = 0
        self.configureCheckedRowsList(probeId, idx, row)
        values[1] = idx


    def configureCheckedRowsList(self, probeId, idx, row=None):
        if row is None:
            row = self.getRowById(probeId)
        if idx:
            if row > -1:
                if row not in self._checkedRowsList:
                    self._checkedRowsList.append(row)
        else:
            if row > -1:
                if row in self._checkedRowsList:
                    del self._checkedRowsList[self._checkedRowsList.index(row)]


    def idList(self):
        return self._idList


    def flags(self, index):
        column = index.column()
        flags = self._cols[column].flags(index)
        if self.cellReadOnly(index):
            flags = flags & (~Qt.ItemIsEditable) & (~Qt.ItemIsUserCheckable)

        elif column in (self.getColIndex('workTest_id'),
                        self.getColIndex('tripodNumber'),
                        self.getColIndex('placeInTripod'),
                        self.getColIndex('specimenType_id')):
            item = self._items[index.row()]
            if forceInt(item.value('status')) != CSamplePreparationModel.probeInWaiting:
                flags = flags & (~Qt.ItemIsEditable)
            else:
                if column == self.getColIndex('specimenType_id'):
                    if not (forceRef(item.value('workTest_id')) and forceRef(item.value('equipment_id'))):
                        flags = flags & (~Qt.ItemIsEditable)

        elif column in self._resultColumnsIndexs:
            item = self._items[index.row()]
            if forceInt(item.value('resultIndex')) == CSamplePreparationModel.probeResultIndexNull:
                flags = Qt.NoItemFlags

        return flags


    def existsCheckedRows(self):
        return bool(self._checkedRowsList)


    def registrateProbe(self, closeAction = False):
        db = QtGui.qApp.db
        db.transaction()
        tableTTJ = db.table('TakenTissueJournal')
        try:
            if self.existsCheckedRows():
                mapActionId2PreliminaryResult = {} # key - actionId, value - preliminaryResultList(first-current action value)
                for row in self._checkedRowsList:
                    item = self._items[row]
                    result = self.getItemForSave(item, row)
                    if result:
                        itemForSave, resultValue, resultIndex = result
                        testId = forceRef(item.value('test_id'))
                        course = forceRef(item.value('course'))
                        tissueJournalId = forceRef(item.value('takenTissueJournal_id'))
                        status = self.getStatusByResult(itemForSave, row)
                        itemForSave.setValue('status', QVariant(status))
                        itemForSave.setValue('resultIndex', QVariant(resultIndex))
                        item.setValue('status', QVariant(status))
                        orderComment = forceString(db.translate(tableTTJ, 'id', tissueJournalId, 'note'))
                        ttjExecDate = forceDateTime(db.translate(tableTTJ, 'id', tissueJournalId, 'execDatetime'))
                        if resultIndex==4:
                            norm = resultLost
                        else:
                            norm = forceStringEx(item.value('externalNorm')) or forceStringEx(item.value('norm'))
                        externalEvaluation = forceStringEx(item.value('externalEvaluation'))
                        unitId = forceRef(item.value('unit_id'))
                        extUnit = forceString(item.value('externalUnit'))
                        if not unitId and extUnit:
                            unitId = forceRef(db.translate('rbUnit', 'code', extUnit, 'id'))
                        id = db.insertOrUpdate(self._table, itemForSave)
                        if id:
                            self.setResultEditable(id, False)
                            setProbeResultToActionProperties(tissueJournalId,
                                                             testId,
                                                             resultValue,
                                                             norm,
                                                             externalEvaluation,
                                                             unitId,
                                                             forceRef(item.value('assistant_id')),
                                                             forceRef(item.value('person_id')),
                                                             ttjExecDate,
                                                             closeAction,
                                                             course,
                                                             orderComment)
                            computeActionPreliminaryResult(item, mapActionId2PreliminaryResult)
                setActionPreliminaryResult(mapActionId2PreliminaryResult)
                self._checkedRowsList = []
                self.reset()
            checkActionTestSetClosingController()
            db.commit()
        except:
            db.rollback()
            QtGui.qApp.logCurrentException()
            resetActionTestSetClosingController()
            raise


    def saveItem(self, record, oldRecord=None):
        record = self.removeExtCols(record)
        fieldsForSaving = ['id', 'equipment_id', 'suiteReagent_id', 'workTest_id', 'specimenType_id', 'status',
                           'isUrgent', 'person_id', 'result1', 'result2', 'result3', 'externalNorm', 'externalUnit',
                           'exportName', 'exportDatetime', 'exportPerson_id', 'externalEvaluation']
        newRecord = self._table.newRecord(fieldsForSaving)
        for i in xrange(newRecord.count()):
            newRecord.setValue(i, record.value(newRecord.fieldName(i)))
        QtGui.qApp.db.insertOrUpdate(self._table, newRecord)

        oldSuiteReagentId = forceRef(oldRecord.value('suiteReagent_id')) if oldRecord else None
        newSuiteReagentId = forceRef(record.value('suiteReagent_id'))

        if oldSuiteReagentId != newSuiteReagentId:
            self.recountSuiteReagentAmount(oldSuiteReagentId, newSuiteReagentId)


    def getItemForSave(self, record, row):
        if self._extColsPresent:
            record = self.removeExtCols(record)
        fieldsForSaving = ['id', 'status', 'result1', 'result2', 'result3', 'resultIndex', 'course']
        resultIndex = self.getCheckedResultByRow(row)
        if resultIndex == 0:
            return None
        resultField = 'result'+unicode(resultIndex)
        newRecord = self._table.newRecord(fieldsForSaving)

        for i in xrange(newRecord.count()):
            newRecord.setValue(i, record.value(newRecord.fieldName(i)))

        return newRecord, newRecord.value(resultField), resultIndex


    def getStatusByResult(self, item, row):
        resultIndex = self.getCheckedResultByRow(row)
#        value = forceStringEx(item.value('result'+unicode(resultIndex)))
#        if bool(value):
        if resultIndex:
            status = CSamplePreparationModel.probeIsFinished
        else:
            status = CSamplePreparationModel.probeWithoutResult
        return status


    def removeExtCols(self, srcRecord, fields=None):
        record = self._table.newRecord(fields)
        for i in xrange(record.count()):
            record.setValue(i, srcRecord.value(record.fieldName(i)))
        return record


    def saveWorkTestValue(self, row):
        record = self._items[row]
        record = self.removeExtCols(record, ['id','workTest_id'])
        QtGui.qApp.db.updateRecord(self._table, record)


    def saveWorkTestValueForOnlyTestProxy(self, mainProbeId, testRow):
        row = self.getRowForTestsProxy(mainProbeId, testRow)
        self.saveWorkTestValue(row)


    def lockItem(self, index):
#        column = index.column()
        row = index.row()
        record = self._items[row]
        itemId = forceRef(record.value('id'))
        if itemId:
            if not self.lock(self.table.tableName, itemId):
                return False
        return True


    def notRetryLock(self, obj, message):
        return CRecordLockMixin.notRetryLock(self, self._parent, message)


    def getItemWithUpdating(self, row, column):
        oldItem = self._items[row]
        itemId = forceRef(oldItem.value('id'))
        cols = self.getColsForItems()
        item = QtGui.qApp.db.getRecord('Probe', cols, itemId)
        if item:
            fieldName = self._cols[column].fieldName()
            item.setValue(fieldName, oldItem.value(fieldName))
            self._items[row] = item
            self.emitRowChanged(row)
        return self._items[row]


    def createEditor(self, index, parent):
        if self.lockItem(index):
            column = index.column()
            row = index.row()
#            item = self._items[row]
            item = self.getItemWithUpdating(row, column)
            if column in self._resultColumnsIndexs:
                typeName = forceString(item.value('typeName')).lower()
                valueType = CActionPropertyValueTypeRegistry.get(typeName, None)

                editorClass = valueType.getEditorClass()
                if editorClass:
                    return editorClass(None, None, parent, None, None) # action, domain, parent, clientId, eventTypeId

            elif column == self.getColIndex('workTest_id'):
                self._cols[column].createFilter(forceRef(self._items[index.row()].value('test_id')))
            elif column == self.getColIndex('suiteReagent_id'):
                editor = CRecordListModel.createEditor(self, index, parent)
                self.setSuiteReagentFIlter(index, editor)
                return editor
            elif column == self.getColIndex('specimenType_id'):
                editor = CRecordListModel.createEditor(self, index, parent)
                self._cols[column].setSpecimenTypeFilter(item, editor)
                return editor
            return CRecordListModel.createEditor(self, index, parent)
        return None


    def createEditorForOnlyTestProxy(self, mainProbeId, testColumn, testRow, parent):
        index = self.getIndexForTestsProxy(mainProbeId, testColumn, testRow)
        return self.createEditor(index, parent)


    def setEditorData(self, index, editor, value, record):
        column = index.column()
        if column in self._resultColumnsIndexs:
            value = self.data(index, Qt.EditRole)
            return editor.setValue(value)

        return self._cols[column].setEditorData(editor, value, record)


    def setEditorDataForOnlyTestProxy(self, mainProbeId, testColumn, testRow, editor, value, record):
        index = self.getIndexForTestsProxy(mainProbeId, testColumn, testRow)
        return self.setEditorData(index, editor, value, record)


    def deleteRows(self, rows):
        idList = []
        newItems = []
        tissueJournalIdList = []
        for row, item in enumerate(self._items):
            if row in rows:
                idList.append(forceRef(item.value('id')))
                tissueJournalIdList.append(forceRef(item.value('takenTissueJournal_id')))
            else:
                newItems.append(item)
        self._items = newItems
        if idList:
            db    = QtGui.qApp.db
            tabel = db.table('Probe')
            cond  = tabel['id'].inlist(idList)
            db.deleteRecord(tabel, cond)
        checkActionPreliminaryResultByTissueJournalIdList(tissueJournalIdList)
        self.applyItemsSettings()
        self.reset()


    def deleteRowsForOnlyProbeProxy(self, mainProbeId):
        key = self._mapIdToOriginalKey[mainProbeId]
        probeTestIdList = self._originalProbeItems[key][0]
        rows = [self._idList.index(id) for id in probeTestIdList]
        self.deleteRows(rows)


    def deleteRowsForOnlyTestProxy(self, mainProbeId, testRows):
        rows = [self.getRowForTestsProxy(mainProbeId, testRow) for testRow in testRows]
        self.deleteRows(rows)


    def allProbInWaiting(self, rows):
        for row in rows:
            if forceInt(self._items[row].value('status')) != CSamplePreparationModel.probeInWaiting:
                return False
        return True


    def allProbInWaitingForOnlyTestProxy(self, mainProbeId, testRows):
        rows = [self.getRowForTestsProxy(mainProbeId, testRow) for testRow in testRows]
        return self.allProbInWaiting(rows)


    def itemsForOnlyTestProxy(self, mainProbeId):
        key = self._mapIdToOriginalKey[mainProbeId]
        probeTestIdList = self._originalProbeItems[key][0]
        return [self._mapIdToItem[probeTestId][1] for probeTestId in probeTestIdList]


    def setSuiteReagentFIlter(self, index, editor):
        item = self._items[index.row()]
        editor.setTestId(forceRef(item.value('test_id')))
        editor.setTissueJournalDate(forceDate(QtGui.qApp.db.translate('TakenTissueJournal', 'id',
                                                                      forceRef(item.value('takenTissueJournal_id')),
                                                                      'createDatetime')))


    def reset(self):
        CRecordListModel.reset(self)
        self.emit(SIGNAL('probeModelReseted()'))

# ###############################

class CSamplePreparationItemDelegate(CLocItemDelegate):
    def createEditor(self, parent, option, index):
        column = index.column()
        editor = index.model().createEditor(index, parent)
        if editor:
            self.connect(editor, SIGNAL('commit()'), self.emitCommitData)
            self.connect(editor, SIGNAL('editingFinished()'), self.commitAndCloseEditor)
        self.editor   = editor
        self.row      = index.row()
        self.rowcount = index.model().rowCount(None)
        self.column   = column
        return editor


    def setEditorData(self, editor, index):
        if editor is not None:
#            column = index.column()
            row    = index.row()
            model  = index.model()
            if row < len(model.items()):
                record = model.items()[row]
            else:
                record = model.getEmptyRecord()
            model.setEditorData(index, editor, model.data(index, Qt.EditRole), record)

    def setModelData(self, editor, model, index):
        if editor is not None:
            column = index.column()
            if column in model._resultColumnsIndexs:
                model.setData(index, toVariant(editor.value()))
            else:
                model.setData(index, index.model().getEditorData(column, editor))
            if column == model.getColIndex('workTest_id'):
                model.saveWorkTestValue(index.row())



class CSamplePreparationView(CInDocTableView):
    def __init__(self, parent):
        CInDocTableView.__init__(self, parent)
        self.setItemDelegate(CSamplePreparationItemDelegate(self))
        self.addPopupDelRow()


    def closeEditor(self, editor, hint):
        self.model().releaseLock()
        CInDocTableView.closeEditor(self, editor, hint)


    def allProbInWaiting(self, rows):
        return self.model().allProbInWaiting(rows)


    def on_deleteRows(self):
        rows = self.getSelectedRows()
        if self.allProbInWaiting(rows) or QtGui.qApp.userHasRight(urDeleteProbe):
            self.model().deleteRows(rows)
        else:
            QtGui.QMessageBox.information(self,
                                          u'Внимание!',
                                          u'Удаление проб со статусом не \'Ожидание\' невозможно',
                                          QtGui.QMessageBox.Ok,
                                          QtGui.QMessageBox.Ok)


# ###################################################################################



class CSamplingOnlyProbesModel(CRecordListModel):
    columnNames = [u'Пробы',
                   u'Дата',
                   u'ИБМ',
                   u'Статус',
                   u'Тип контейнера',
                   u'Цветовой маркер',
                   u'Количество контейнеров']
    colorColumn = 5

    def __init__(self, parent, mainSamplingModel):
        CRecordListModel.__init__(self, parent)
        self._mainSamplingModel = mainSamplingModel
        self.connect(self._mainSamplingModel, SIGNAL('probeModelReseted()'), self.reset)
        self.connect(self._mainSamplingModel, SIGNAL('resetProbeStatus()'), self.resetProbeStatus)


    def resetProbeStatus(self):
        self.emitAllChanged()


    def rowCount(self, index=None):
        return self._mainSamplingModel.originalProbeCount()


    def columnCount(self, index=None):
        return 7


    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()

        column = index.column()
        row    = index.row()

        if role == Qt.DisplayRole and column != CSamplingOnlyProbesModel.colorColumn:
            return QVariant(self._mainSamplingModel.onlyProbeProxyValue(row, column))
        elif role == Qt.BackgroundRole and column == CSamplingOnlyProbesModel.colorColumn:
            return QVariant(self._mainSamplingModel.onlyProbeProxyValue(row, column))
        return QVariant()


    def headerData(self, section, orientation, role = Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return QVariant(CSamplingOnlyProbesModel.columnNames[section])
        return QVariant()


    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled


    def getId(self, row):
        keyList = self._mainSamplingModel.getOriginalProbeItemsKeys()
        key = keyList[row]
        return self._mainSamplingModel._originalProbeItems[key][0][0]


    def canRemoveRow(self, row):
        return QtGui.qApp.userHasRight(urDeleteProbe)


    def removeRow(self, row, parent = QModelIndex()):
        id = self.getId(row)
        self._mainSamplingModel.deleteRowsForOnlyProbeProxy(id)


    def confirmRemoveRow(self, view, row, multiple):
        buttons = QtGui.QMessageBox.Yes|QtGui.QMessageBox.No
        mbResult = QtGui.QMessageBox.question(view, u'Внимание!', u'Действительно удалить?', buttons, QtGui.QMessageBox.No)
        return {QtGui.QMessageBox.Yes: True,
                QtGui.QMessageBox.No: False}.get(mbResult, None)


class CSamplingOnlyTestsModel(CRecordListModel):
    def __init__(self, parent, mainSamplingModel):
        CRecordListModel.__init__(self, parent)
        self._mainSamplingModel = mainSamplingModel
        self.connect(self._mainSamplingModel, SIGNAL('probeModelReseted()'), self.reset)
        self.applyProxyProperties()
        self._mainProbeId = None


    def reset(self, probeId=None):
        self._mainProbeId = probeId
        CRecordListModel.reset(self)


    def setMainProbeId(self, probeId):
        self.reset(probeId)


    def applyProxyProperties(self):
        self._cols = self._mainSamplingModel.cols()[2:]
        self._hiddenCols = self._mainSamplingModel.hiddenCols()
        self._mainSamplingModel.getColIndex('') # я не понимаю что за магия с _mapFieldNameToCol. поэтому форсирую её создание...
        self._mapFieldNameToCol = self._mainSamplingModel._mapFieldNameToCol
        self._resultColumnsIndexs = self._mainSamplingModel._resultColumnsIndexs


    def data(self, index, role=Qt.DisplayRole):
        if self._mainProbeId:
            column = index.column()
            row = index.row()
            return self._mainSamplingModel.onlyTestsProxyValue(self._mainProbeId, column, row, role)
        return QVariant()


    def rowCount(self, index=None):
        return self._mainSamplingModel.originalProbeTestsCount(self._mainProbeId)


    def flags(self, index):
        column = index.column()
        row = index.row()
        return self._mainSamplingModel.onlyTestsProxyFlags(self._mainProbeId, column, row)


    def createEditor(self, index, parent):
        return self._mainSamplingModel.createEditorForOnlyTestProxy(self._mainProbeId,
                                                                    index.column(),
                                                                    index.row(),
                                                                    parent)

    def setEditorData(self, index, editor, value, record):
        return self._mainSamplingModel.setEditorDataForOnlyTestProxy(self._mainProbeId,
                                                                     index.column(),
                                                                     index.row(),
                                                                     editor, value, record)


    def setData(self, index, value, role=Qt.EditRole):
        row    = index.row()
        column = index.column()
        result = self._mainSamplingModel.setDataForOnlyTestProxy(self._mainProbeId,
                                                                 column,
                                                                 row,
                                                                 value, role)
        if result:
            self.emitRowChanged(row)
        return result


    def saveWorkTestValue(self, row):
        self._mainSamplingModel.saveWorkTestValueForOnlyTestProxy(self._mainProbeId, row)


    def deleteRows(self, rows):
        self._mainSamplingModel.deleteRowsForOnlyTestProxy(self._mainProbeId, rows)


    def allProbInWaiting(self, rows):
        return self._mainSamplingModel.allProbInWaitingForOnlyTestProxy(self._mainProbeId, rows)


    def items(self):
        return self._mainSamplingModel.itemsForOnlyTestProxy(self._mainProbeId)
        self.reset(self._mainProbeId)


    def releaseLock(self):
        self._mainSamplingModel.releaseLock()

