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

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QVariant, QModelIndex

from library.crbcombobox  import CRBComboBox, CRBModelDataCache
from library.InDocTable   import CInDocTableCol
from library.TreeComboBox import CTreeComboBox, CTreeComboBoxGetIdSetIdMixin
from library.TreeModel    import CTreeItemWithId, CTreeModel
from library.Utils        import forceBool, forceInt, forceRef, forceString, forceStringEx, toVariant

from Accounting.Tariff    import CTariff
from Events.Utils         import recordAcceptable


class CActionTypeTreeItem(CTreeItemWithId):
    def __init__(self, parent, id, code, name, model, class_):
        CTreeItemWithId.__init__(self, parent, name, id)
        self._model = model
        self._code = code
        self._name = name
        self._maxCodeLen = 5
        self._class = class_


    def class_(self):
        return self._class


    def loadChildren(self):
        return self._model.loadChildrenItems(self)


    def flags(self):
        if self.childCount() > 0 and not self._model._allSelectable:
            return Qt.ItemIsEnabled
        else:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable


    def data(self, column):
        if column == 0:
            if self._code:
                s = '%-*s|%s' % (self._maxCodeLen, self._code, self._name)
            else:
                s = self._name
            return toVariant(s)
        else:
            return QVariant()


class CActionTypeClassTreeItem(CActionTypeTreeItem):
    def __init__(self, parent, class_, model):
        CActionTypeTreeItem.__init__(self, parent, None, '', [u'статус', u'диагностика', u'лечение', u'мероприятия'][class_], model, class_)
#        self._class = class_

    def flags(self):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable


class CActionTypeRootTreeItem(CActionTypeTreeItem):
    def __init__(self, model):
        CActionTypeTreeItem.__init__(self, None, None, '', u'-', model, None)


    def loadChildren(self):
        if self._model._classesVisible:
            result = []
            for class_ in self._model._classes:
                result.append(CActionTypeClassTreeItem(self, class_, self._model))
            return result
        else:
            return self._model.loadChildrenItems(self)


    def flags(self):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable


    def reset(self):
        if self._items is None:
            return False
        else:
            self._items = None
            return True


class CActionTypeRootTreeItemIsSelect(CActionTypeTreeItem):
    def __init__(self, group, id, code, name, model, class_):
        CActionTypeTreeItem.__init__(self, group, id, code, name, model, class_)


    def loadChildren(self):
        if self._model._classesVisible:
            result = []
            for class_ in self._model._classes:
                result.append(CActionTypeClassTreeItem(self, class_, self._model))
            return result
        else:
            return self._model.loadChildrenItems(self)


    def flags(self):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable


    def reset(self):
        if self._items is None:
            return False
        else:
            self._items = None
            return True


class CActionTypeModel(CTreeModel):
    def __init__(self, parent=None, enabledActionTypeIdList=None):
        CTreeModel.__init__(self, parent, CActionTypeRootTreeItem(self))
        self._enabledActionTypeIdList=enabledActionTypeIdList
        self._classes = range(4)
        self.parnt = parent
        self._classesVisible = False
        self._allSelectable = False
        self._leavesVisible = True
        self._disabledActionTypeIdList = None
        self._clientSex = 0
        self._clientAge = None
        self._eventDate = None
        self._clientBirthDate = None
        self._serviceType = None


    def setClasses(self, classes):
        if self._classes != classes:
            self._classes = classes
            if self.getRootItem().reset():
                self.reset()


    def setClassesVisible(self, value):
        if self._classesVisible != value:
            self._classesVisible = value
            if self.getRootItem().reset():
                self.reset()


    def setServiceType(self, serviceType):
        if self._serviceType != serviceType:
            self._serviceType = serviceType
            if self.getRootItem().reset():
                self.reset()


    def setAllSelectable(self, value):
        if self._allSelectable != value:
            self._allSelectable = value


    def setDisabledActionTypeIdList(self, disabledActionTypeIdList):
        if self._disabledActionTypeIdList != disabledActionTypeIdList:
            self._disabledActionTypeIdList = disabledActionTypeIdList
            if self.getRootItem().reset():
                self.reset()


    def setEnabledActionTypeIdList(self, enabledActionTypeIdList):
        if self._enabledActionTypeIdList != enabledActionTypeIdList:
            self._enabledActionTypeIdList = enabledActionTypeIdList
            if self.getRootItem().reset():
                self.reset()


    def setFilter(self, clientSex, clientAge, eventDate=None, clientBirthDate=None):
        if self._clientSex != clientSex or self._clientAge != clientAge or self._eventDate != eventDate or self._clientBirthDate != clientBirthDate:
            self._clientSex = clientSex
            self._clientAge = clientAge
            self._eventDate = eventDate
            self._clientBirthDate = clientBirthDate
            if self.getRootItem().reset():
                self.reset()


    def setLeavesVisible(self, leavesVisible):
        if self._leavesVisible != leavesVisible:
            self._leavesVisible = leavesVisible
            if self.getRootItem().reset():
                self.reset()


    def flags(self, index):
        if index.isValid():
            item = index.internalPointer()
            if item:
                return item.flags()
            return Qt.NoItemFlags

    def loadMaxWord(self):
        db = QtGui.qApp.db
        maxWord = u''
        query = db.query("SELECT name FROM ActionType WHERE (ActionType.`deleted` = 0) AND (ActionType.`class` = 0) ORDER BY LENGTH(name) DESC LIMIT 1")
        while query.next():
            record = query.record()
            maxWord = forceStringEx(record.value('name'))

        return maxWord

    def loadChildrenItems(self, group):
        db = QtGui.qApp.db
        tableActionType = db.table('ActionType')
        if hasattr(self.parnt, 'showInForm') or hasattr(self.parnt, '_popup') and hasattr(self.parnt._popup, 'showInForm'):
            cond = [tableActionType['deleted'].eq(0)]
            if hasattr(self.parnt, 'showInForm'):
                if self.parnt.showInForm:
                    cond.append(tableActionType['showInForm'].eq(1))

            if hasattr(self.parnt, '_popup') and hasattr(self.parnt._popup, 'showInForm'):
                if self.parnt._popup.showInForm:
                    cond.append(tableActionType['showInForm'].eq(1))
        else:
            cond = [tableActionType['deleted'].eq(0), tableActionType['showInForm'].eq(1)]

        if isinstance(group, CActionTypeClassTreeItem):
            cond.append(tableActionType['class'].eq(group._class))
        elif group.id() is None:
            cond.append(tableActionType['class'].inlist(self._classes))
        if self._enabledActionTypeIdList is not None:
            cond.append(tableActionType['id'].inlist(self._enabledActionTypeIdList))
        if self._disabledActionTypeIdList:
            cond.append(tableActionType['id'].notInlist(self._disabledActionTypeIdList))
        if self._serviceType is not None:
            cond.append(tableActionType['serviceType'].eq(self._serviceType))
        mapGroupIdToItems = {}
        mapIdToItems = {}
        query = db.query(db.selectStmt(tableActionType, 'id, class, group_id, code, name, sex, age', where=cond, order='code'))
        while query.next():
            record = query.record()
            if recordAcceptable(self._clientSex, self._clientAge, record, self._eventDate, self._clientBirthDate):
                id   = forceInt(record.value('id'))
                code = forceStringEx(record.value('code'))
                name = forceStringEx(record.value('name'))
                groupId = forceRef(record.value('group_id'))
                class_ = forceInt(record.value('class'))
                item = CActionTypeRootTreeItemIsSelect(group, id, code, name, self, class_)
                item._items = []
                items = mapGroupIdToItems.setdefault(groupId, [])
                items.append(item)
                mapIdToItems[id] = item
        if not self._leavesVisible:
            leavesIdSet = set(mapIdToItems.keys()) - set(mapGroupIdToItems.keys())
            filterFunc = lambda item: item._id not in leavesIdSet
        else:
            filterFunc = None
        for groupId, items in mapGroupIdToItems.iteritems():
            groupItem = mapIdToItems.get(groupId, None)
            if groupItem:
                if filterFunc:
                    items = filter(filterFunc, items)
                for item in items:
                    item._parent = groupItem
                groupItem._items = items
        return mapGroupIdToItems.get(group.id(), [])


    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            return QVariant(u'Типы мероприятий')
        return QVariant()


class CActionTypeComboBox(CTreeComboBoxGetIdSetIdMixin, CTreeComboBox):
    def __init__(self, parent, enabledActionTypeIdList = None):
        CTreeComboBox.__init__(self, parent)
        self.SizeAdjustPolicy(QtGui.QComboBox.AdjustToMinimumContentsLength)
        self._model = CActionTypeModel(self, enabledActionTypeIdList)
        self.setModel(self._model)
        self.setPreferredHeight(300)


    def setLeavesVisible(self, leavesVisible):
        self._model.setLeavesVisible(leavesVisible)


    def setClass(self, class_):
        if class_ is not None:
            self.setClasses([class_])
        else:
            self.setClasses(range(4))


    def setClasses(self, classes):
        self._model.setClasses(classes)


    def setClassesVisible(self, value):
        self._model.setClassesVisible(value)


    def setServiceType(self, value):
        self._model.setServiceType(value)


    def setAllSelectable(self, value):
        self._model.setAllSelectable(value)


    def setDisabledActionTypeIdList(self, disabledActionTypeIdList):
        self._model.setDisabledActionTypeIdList(disabledActionTypeIdList)


    def setEnabledActionTypeIdList(self, enabledActionTypeIdList):
        self._model.setEnabledActionTypeIdList(enabledActionTypeIdList)


    def setFilter(self, sex, age):
        self._model.setFilter(sex, age)


    def getClass(self):
        modelIndex = self.currentModelIndex()
        if modelIndex and modelIndex.isValid():
            item = modelIndex.internalPointer()
            return item.class_() if item else None
        return None


    def showPopup(self):
        # возня с installEventFilter/removeEventFilter
        # обусловлена тем, что при использовании Qt 4.6/4.7/4.8 и PyQt 4.9
        # в windows время от времени происходит segmentationFault.
        # Исследование показало, что это связано с установкой
        # view().viewport().installEventFilter(self)
        # в конструкторе. Поэтому я перенёс этот код в showPopup
        # и добавил removeEventFilter в hidePopup.
        # Так не падает.
        self.setRootModelIndex(QModelIndex())
        if self._expandAll:
            self._view.expandAll()
        else:
            if self._expandDepth:
                self._view.expandToDepth(self._expandDepth)
            else:
                self._view.expandUp(self.currentModelIndex())

        items = "    " * (3 + 1) + self.model().loadMaxWord() + "   "
        itemLenghts = [self._view.fontMetrics().width(items)]
        preferredWidth = max(max(itemLenghts), self._preferredWidth, self._view.sizeHint().width())

        # на маленьком разрешениии, часть попапа пропадает за пределами экрана
        # ограничиваем его размер до ширины активного окна - 5%
        if preferredWidth > self.window().width():
            preferredWidth = self.window().width() - self.window().width() * 0.05
            #self._view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
            #self._view.setTextElideMode(QtCore.Qt.ElideNone)
        if preferredWidth:
            if self.width() < preferredWidth:
                self._view.setFixedWidth(preferredWidth)
        if self._preferredHeight:
            self._view.setMinimumHeight(self._preferredHeight)
        self._view.installEventFilter(self)
        self._view.viewport().installEventFilter(self)
        self._selectedModelIndex = None
        QtGui.QComboBox.showPopup(self)
        scrollBar = self._view.horizontalScrollBar()
        scrollBar.setValue(0)


class CActionTypeTableCol(CInDocTableCol):
    tableName = 'ActionType'
    showFields = CRBComboBox.showCodeAndName
    def __init__(self, title, fieldName, width, actionTypeClass, **params):
        CInDocTableCol.__init__(self, title, fieldName, width, **params)
        self.actionTypeClass = actionTypeClass
        self.classesVisible = params.get('classesVisible', False)
        self.showFields = params.get('showFields', CRBComboBox.showCodeAndName)
        self.filter = params.get('filter', '')
        self.contractId = None
        self.enabledActionTypeIdList = None
        self.leavesVisible = True


    def setLeavesVisible(self, leavesVisible):
        self.leavesVisible = leavesVisible


    def setActionTypeClass(self, actionTypeClass):
        self.actionTypeClass = actionTypeClass


    def toString(self, val, record):
        cache = CRBModelDataCache.getData(self.tableName, True)
        text = cache.getStringById(forceRef(val), self.showFields)
        specifiedName = forceString(record.value('specifiedName'))
        if specifiedName:
            text = forceString(text) + ' ' + specifiedName
        return toVariant(text)


    def toStatusTip(self, val, record):
        cache = CRBModelDataCache.getData(self.tableName, True)
        text = cache.getStringById(forceRef(val), CRBComboBox.showName)
        specifiedName = forceString(record.value('specifiedName'))
        if specifiedName:
            text = forceString(text) + ' ' + specifiedName
        return toVariant(text)


    def setContractId(self, newValue):
        if self.contractId != newValue:
            self.contractId = newValue
            self.enabledActionTypeIdList = None


    def createEditor(self, parent):
        enabledActionTypeIdList = None
        db = QtGui.qApp.db
        keyboardModifiers = QtGui.qApp.keyboardModifiers()
        if keyboardModifiers & Qt.ControlModifier:
            if self.contractId:
                if self.enabledActionTypeIdList is None:
                    idList = getActionTypeIdListByContract(self.contractId)
                    idList = db.getTheseAndParents('ActionType', 'group_id', idList)
                    self.enabledActionTypeIdList = idList
                enabledActionTypeIdList = self.enabledActionTypeIdList
        if self.filter:
            table = db.table('ActionType')
            cond = [table['deleted'].eq(0), self.filter]
            if enabledActionTypeIdList:
                cond.append(table['id'].inlist(enabledActionTypeIdList))
            enabledActionTypeIdList = db.getDistinctIdList(table, ['id'], cond)
            self.enabledActionTypeIdList = enabledActionTypeIdList
        editor = CActionTypeComboBox(parent, enabledActionTypeIdList)
        editor.setClass(self.actionTypeClass)
        editor.setClassesVisible(self.classesVisible)
        editor.setLeavesVisible(self.leavesVisible)
#        editor.setPreferredWidth(self.preferredWidth)
        return editor


    def setEditorData(self, editor, value, record):
        editor.setValue(forceRef(value))


    def getEditorData(self, editor):
        return toVariant(editor.value())


def getActionTypeIdListWithLimitationByContractTariffAttach(contractId, contractTariffAttachLimitations=False):
    idList = None
    actionTypeId2ContractTariffAtach = None
    if contractId:
        idList = []
        actionTypeId2ContractTariffAtach = {}
        db = QtGui.qApp.db
        priceListId = forceInt(db.translate('Contract', 'id', contractId, 'priceListExternal_id'))
        tableContract = db.table('Contract')
        tableContractTariff = db.table('Contract_Tariff')
        tableActionTypeService = db.table('ActionType_Service')
        tableActionType = db.table('ActionType')
        table = tableContract.leftJoin(tableContractTariff,
                                       [ tableContractTariff['master_id'].inlist([contractId,  priceListId]),
                                         tableContractTariff['deleted'].eq(0),
                                         tableContractTariff['tariffType'].inlist([CTariff.ttActionAmount,
                                                                                   CTariff.ttActionUET,
                                                                                   CTariff.ttHospitalBedService])
                                       ]
                                      )
        table = table.leftJoin(tableActionTypeService, tableActionTypeService['service_id'].eq(tableContractTariff['service_id']))
        table = table.leftJoin(tableActionType,  tableActionType['id'].eq(tableActionTypeService['master_id']))
        cond  = [ tableContract['id'].eq(contractId),
                  tableActionType['deleted'].eq(0),
                  '''IF(EXISTS(SELECT id FROM ActionType_Service AS ATS WHERE ActionType.id = ATS.master_id AND Contract.finance_id = ATS.finance_id),
                        ActionType_Service.finance_id = Contract.finance_id,
                        ActionType_Service.finance_id IS NULL
                      )'''
                ]

        fields = [tableActionType['id'].alias('actionTypeId')]

#        if contractTariffAttachLimitations:
        tableContractTariffAttach = db.table('ContractTariff_Attach')

        table = table.leftJoin(tableContractTariffAttach,
                               tableContractTariffAttach['master_id'].eq(tableContractTariff['id']))

        fields.extend(
                      [
                       tableContractTariffAttach['id'].alias('contractTariffAttachId'),
                       tableContractTariffAttach['attachType_id'].alias('attachTypeId'),
                       tableContractTariffAttach['amount'],
                       tableContractTariffAttach['agreement'],
                       tableContractTariffAttach['exception'],
                      ]
                     )


        recordList = db.getRecordList(table, fields, cond)
        for record in recordList:
            actionTypeId = forceRef(record.value('actionTypeId'))
            if actionTypeId not in idList:
                idList.append(actionTypeId)


#            if contractTariffAttachLimitations:
            contractTariffAttachId = forceRef(record.value('contractTariffAttachId'))
            if contractTariffAttachId:
                attachTypeId = forceRef(record.value('attachTypeId'))
                amount = forceInt(record.value('amount'))
                agreement = forceBool(record.value('agreement'))
                exception = forceBool(record.value('exception'))

                valueList = actionTypeId2ContractTariffAtach.setdefault(actionTypeId, [])
                valueList.append((attachTypeId, amount, agreement, exception))



        idList = db.getDistinctIdList(table, tableActionType['id'], cond)

    return idList, actionTypeId2ContractTariffAtach
    
def getActionTypeIdListWithLimitationByContractTariffAttachByDate(contractId, eventDate, datecontractTariffAttachLimitations=False):
    idList = None
    actionTypeId2ContractTariffAtach = None
    if contractId:
        idList = []
        actionTypeId2ContractTariffAtach = {}
        db = QtGui.qApp.db
        priceListId = forceInt(db.translate('Contract', 'id', contractId, 'priceListExternal_id'))
        tableContract = db.table('Contract')
        tableContractTariff = db.table('Contract_Tariff')
        tableActionTypeService = db.table('ActionType_Service')
        tableActionType = db.table('ActionType')
        table = tableContract.leftJoin(tableContractTariff,
                                       [ tableContractTariff['master_id'].inlist([contractId,  priceListId]),
                                         tableContractTariff['deleted'].eq(0),
                                         tableContractTariff['tariffType'].inlist([CTariff.ttActionAmount,
                                                                                   CTariff.ttActionUET,
                                                                                   CTariff.ttHospitalBedService])
                                       ]
                                      )
        table = table.leftJoin(tableActionTypeService, tableActionTypeService['service_id'].eq(tableContractTariff['service_id']))
        table = table.leftJoin(tableActionType,  tableActionType['id'].eq(tableActionTypeService['master_id']))
        cond  = [ tableContract['id'].eq(contractId),
                  tableActionType['deleted'].eq(0),
                  '''IF(EXISTS(SELECT id FROM ActionType_Service AS ATS WHERE ActionType.id = ATS.master_id AND Contract.finance_id = ATS.finance_id),
                        ActionType_Service.finance_id = Contract.finance_id,
                        ActionType_Service.finance_id IS NULL
                      )''', 
                    """Contract_Tariff.endDate is not null and '%(eventDate)s' between Contract_Tariff.begDate and Contract_Tariff.endDate 
            or '%(eventDate)s' >= Contract_Tariff.begDate and Contract_Tariff.endDate is null"""% {'eventDate': eventDate.toString('yyyy-MM-dd')}
                ]

        fields = [tableActionType['id'].alias('actionTypeId')]

#        if contractTariffAttachLimitations:
        tableContractTariffAttach = db.table('ContractTariff_Attach')

        table = table.leftJoin(tableContractTariffAttach,
                               tableContractTariffAttach['master_id'].eq(tableContractTariff['id']))

        fields.extend(
                      [
                       tableContractTariffAttach['id'].alias('contractTariffAttachId'),
                       tableContractTariffAttach['attachType_id'].alias('attachTypeId'),
                       tableContractTariffAttach['amount'],
                       tableContractTariffAttach['agreement'],
                       tableContractTariffAttach['exception'],
                      ]
                     )


        recordList = db.getRecordList(table, fields, cond)
        for record in recordList:
            actionTypeId = forceRef(record.value('actionTypeId'))
            if actionTypeId not in idList:
                idList.append(actionTypeId)


#            if contractTariffAttachLimitations:
            contractTariffAttachId = forceRef(record.value('contractTariffAttachId'))
            if contractTariffAttachId:
                attachTypeId = forceRef(record.value('attachTypeId'))
                amount = forceInt(record.value('amount'))
                agreement = forceBool(record.value('agreement'))
                exception = forceBool(record.value('exception'))

                valueList = actionTypeId2ContractTariffAtach.setdefault(actionTypeId, [])
                valueList.append((attachTypeId, amount, agreement, exception))



        idList = db.getDistinctIdList(table, tableActionType['id'], cond)

    return idList, actionTypeId2ContractTariffAtach


def getActionTypeIdListByContract(contractId, contractTariffAttachLimitations=False):
    return getActionTypeIdListWithLimitationByContractTariffAttach(contractId, contractTariffAttachLimitations)[0]


class CActionTypeComboBoxMCL(CActionTypeComboBox):
    def __init__(self, parent, enabledActionTypeIdList = None):
        CActionTypeComboBox.__init__(self, parent, enabledActionTypeIdList)
        self.SizeAdjustPolicy(QtGui.QComboBox.AdjustToMinimumContentsLength)
        self.setMinimumContentsLength(20)
        self._model = CActionTypeModel(self, enabledActionTypeIdList)
        self.setModel(self._model)
        self.setPreferredHeight(300)

