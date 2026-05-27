# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2024 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################


from PyQt4 import QtGui, QtSql
from PyQt4.QtCore import Qt, QDate, QDateTime, QModelIndex, QString, QVariant, SIGNAL

from Orgs.Utils import getOrgStructureDescendants, getParentOrgStructureId
from library.ICDInDocTableCol import CICDExInDocTableCol
from library.InDocTable import CInDocTableModel, CBoolInDocTableCol, CDateInDocTableCol, CEnumInDocTableCol, CFloatInDocTableCol, CInDocTableCol, CRBInDocTableCol
from library.Utils import forceBool, forceDate, forceDateTime, forceDouble, forceInt, forceRef, forceString, toVariant, forceStringEx
from library.crbcombobox import CRBComboBox, CRBModelDataCache

from Events.Action import CActionTypeCache
from Events.ActionStatus import CActionStatus
from Events.ActionTypeComboBox import CActionTypeTableCol
from Events.ContractTariffCache import CContractTariffCache
from Events.Utils import CFinanceType, payStatusText, getEventActionContract, getEventActionFinance
from Orgs.OrgComboBox import CContractComboBox, CContractDbModel, COrgInDocTableColEx
from Orgs.PersonComboBoxEx import CPersonFindInDocTableCol, CPersonComboBoxEx
from Users.Rights import urEditAfterInvoicingEvent, canChangeActionPerson


class CActionPerson(CPersonFindInDocTableCol):
    def __init__(self, title, fieldName, width, tableName, **params):
        CPersonFindInDocTableCol.__init__(self, title, fieldName, width, tableName, **params)
        self._parent = params.get('parent', None)
        self._useFilter = params.get('useFilter', None)
        self.filter = None
        self.orgStructureId = QtGui.qApp.currentOrgStructureId()
        self.date = None

    def setIndex(self, index):
        if self._useFilter:
            self.filter = None
            _filter = []
            model = index.model()
            if len(model._items) == 0:
                return
            record = model._items[index.row()]
            actionTypeId = forceInt(record.value('actionType_id'))
            actionType = CActionTypeCache.getById(actionTypeId)
            orgStructureList = actionType.getPFOrgStructureRecordList()
            specialityList = actionType.getPFSpecialityRecordList()
            tablePerson = QtGui.qApp.db.table('vrbPersonWithSpecialityAndPost')
            orgStructureIdList = []
            for orgStructureRecord in orgStructureList:
                orgStruct = forceInt(orgStructureRecord.value('orgStructure_id'))
                orgStructureIdList.append(orgStruct)
                for orgStructDescendant in getOrgStructureDescendants(orgStruct):
                    orgStructureIdList.append(orgStructDescendant)
            orgStructureIdList = list(set(orgStructureIdList))
            specialityIdList = [forceInt(specialityRecord.value('speciality_id')) for specialityRecord in specialityList]
            if orgStructureIdList:
                _filter.append(tablePerson['orgStructure_id'].inlist(orgStructureIdList))
            if specialityIdList:
                _filter.append(tablePerson['speciality_id'].inlist(specialityIdList))
            self.filter = QtGui.qApp.db.joinAnd(_filter)


    def createEditor(self, parent):
        editor = CPersonComboBoxEx(parent)
        if self.filter:
            editor.setFilter(self.filter)
        editor.setDate(self.date)
        editor.setOrgStructureId(self.orgStructureId)
        editor.setOrgStructureList(self.orgStructureIdList)
        editor.setPersonIdList(self.personIdList)
        editor.setBegDate(self._parent.getSetDateTime().date())
        editor.setPreferredWidth(self.preferredWidth)
        return editor



class CActionsSummaryModel(CInDocTableModel):
    class CUetCol(CFloatInDocTableCol):
        def __init__(self, model):
            CFloatInDocTableCol.__init__(self, u'УЕТ',  'uet', 6, precision=2)
            self.model = model
            self.setReadOnly()


        def getUet(self, value, record):
            actionTypeId = forceRef(record.value('actionType_id'))
            personId = forceRef(record.value('person_id'))
            financeId = forceRef(record.value('finance_id'))
            contractId = forceRef(record.value('contract_id'))
#            result = forceDouble(value)*self.model.eventEditor.getUet(actionTypeId, personId, financeId, contractId)
            result = forceDouble(record.value('amount'))*self.model.eventEditor.getUet(actionTypeId, personId, financeId, contractId)
            return result


        def toString(self, value, record):
            if value.isNull():
                return value
            if not record:
                return QVariant()

            v = self.getUet(value, record)
            s = QString()
            if self.precision is None:
                s.setNum(v)
            else:
                s.setNum(v, 'f', self.precision)
            return toVariant(s)


    class CPayStatusCol(CInDocTableCol):
        def __init__(self):
            CInDocTableCol.__init__(self, u'Оплата', 'payStatus', 10)
            self.setReadOnly()


        def toString(self, value, record):
            payStatus = forceInt(value)
            return toVariant(payStatusText(payStatus))


    # модель сводки действий
    __pyqtSignals__ = ('currentRowMovedTo(int)',
                       'amountChanged()',
                       )

    def __init__(self, parent, editable=False):
        CInDocTableModel.__init__(self, 'Action', 'id', 'event_id', parent)
        self.addCol(CActionTypeTableCol(u'Тип',           'actionType_id', 15, None, classesVisible=True))  # 0
        self.addCol(CICDExInDocTableCol(u'МКБ',           'MKB', 10))  # 1
        self.addCol(CBoolInDocTableCol(u'Срочный',        'isUrgent', 10))  # 2
        self.addCol(CDateInDocTableCol(u'Назначено',      'directionDate', 15, canBeEmpty=True))  # 3
        self.addCol(CDateInDocTableCol(u'Начато',         'begDate',       15, canBeEmpty=True))  # 4
        self.addCol(CDateInDocTableCol(u'Окончено',       'endDate',       15, canBeEmpty=True))  # 5
        self.addCol(CEnumInDocTableCol(u'Состояние',      'status',        10, CActionStatus.names))  # 6
        self.addCol(CActionPerson(u'Назначил',            'setPerson_id',  20, 'vrbPersonWithSpecialityAndOrgStr', parent=parent))  # 7
        self.addCol(CActionPerson(u'Выполнил',            'person_id',  20, 'vrbPersonWithSpecialityAndOrgStr', readOnly=(True if not QtGui.qApp.userHasRight(canChangeActionPerson) else False), parent=parent, useFilter=True))  # 8
        self.addCol(CActionPerson(u'Ассистент',           'assistant_id',  20, 'vrbPersonWithSpecialityAndOrgStr', parent=parent))  # 9
        self.addCol(CInDocTableCol(u'Каб',                'office',                                6))  # 10
        self.addCol(CFloatInDocTableCol(u'Кол-во',        'amount',                                6, precision=2))  # 11
        self.colUet = self.addCol(CActionsSummaryModel.CUetCol(self))  # 12
        self.addCol(COrgInDocTableColEx(u'Место выполнения', 'org_id', 30))  # 13
        self.addCol(CInDocTableCol(u'Примечания',         'note',                                 40))  # 14

        self.models = []
        self.itemIndex = []
        self.editable = editable
        self.setEnableAppendLine(self.editable)
        self.eventEditor = parent
        self.connect(self.eventEditor, SIGNAL('updateActionsPriceAndUet()'), self.on_updateActionsPriceAndUet)

        self.visitList = {}
        self.readOnly = False


    def setReadOnly(self, value):
        self.readOnly = value


    def addModel(self, model):
        self.connect(model, SIGNAL('dataChanged(QModelIndex, QModelIndex)'), self.onDataChanged)
        self.connect(model, SIGNAL('modelReset'), self.onModelReset)
        self.connect(model, SIGNAL('rowsInserted(QModelIndex, int, int)'), self.onRowInserted)
        self.connect(model, SIGNAL('rowsRemoved(QModelIndex, int, int)'), self.onRowRemoved)
        self.connect(model, SIGNAL('amountChanged(int)'), self.onAmountChanged)
        self.models.append(model)

    def translate2ActionsSummaryRow(self, model, modelRow):
        try:
            iModel = self.models.index(model)
            return self.itemIndex.index((iModel, modelRow))
        except:
            return None

    def regenerate(self, top=0, bottom=0):
        items = []
        itemIndex = []
        for i, model in enumerate(self.models):
            for j, (record, action) in enumerate(model.items()):
                items.append(record)
                itemIndex.append((i, j))
        self.itemIndex = itemIndex
        self.setItems(items)


    def onDataChanged(self, topLeft, bottomRight):
        iModel = self.models.index(topLeft.model())
        top = topLeft.row()
        bottom = bottomRight.row()
        try:
            newTop = self.itemIndex.index((iModel, top))
        except:
            newTop = 0
        try:
            newBottom = self.itemIndex.index((iModel, bottom))
        except:
            newBottom = len(self.itemIndex)-1
        self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), self.index(newTop, 0), self.index(newBottom, len(self.cols())-1))
        # self.regenerate()


    def onModelReset(self):
        self.regenerate()


    def onRowInserted(self, parent, start, end):
        self.regenerate(start-1, end-1)


    def onRowRemoved(self, parent, start, end):
        self.regenerate(start, end)


    def onAmountChanged(self, row):
        self.emit(SIGNAL('amountChanged()'))


    def isLocked(self, row):
        iModel, iAction = self.itemIndex[row]
        actionsModel = self.models[iModel]
        return actionsModel.isLocked(iAction)


    def isLockedOrExposed(self, row):
        iModel, iAction = self.itemIndex[row]
        actionsModel = self.models[iModel]
        return actionsModel.isLockedOrExposed(iAction)

    def isCanDeletedByUser(self, row):
        iModel, iAction = self.itemIndex[row]
        actionsModel = self.models[iModel]
        return actionsModel.isCanDeletedByUser(iAction)


    def flags(self, index=QModelIndex()):
        row = index.row()
        column = index.column()
        items = self.items()
        if self.readOnly:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        if self.editable:
            if 0 <= row < len(items):
                iModel, iAction = self.itemIndex[row]
                actionsModel = self.models[iModel]
                financeId = forceInt(items[row].value('finance_id'))
                if ((actionsModel.isLocked(iAction)
                        or column == 0
                        or forceInt(items[row].value('payStatus')))
                    and (not QtGui.qApp.refundRegistrationEnabled() or financeId != CFinanceType.getId(CFinanceType.cash))):  # actionType
                    return Qt.ItemIsSelectable | Qt.ItemIsEnabled
            if column == self.getColIndex('assistant_id'):
                row = index.row()
                record = items[row] if 0 <= row < len(items) else None
                actionTypeId = forceRef(record.value('actionType_id')) if record else None
                if actionTypeId:
                    actionType = CActionTypeCache.getById(actionTypeId)
                    if actionType.hasAssistant:
                        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable
                    else:
                        return Qt.ItemIsSelectable
            if column == self.getColIndex('status'):
                items = self.items()
                record = items[row] if 0 <= row < len(items) else None
                actionTypeId = forceRef(record.value('actionType_id')) if record else None
                if actionTypeId:
                    actionType = CActionTypeCache.getById(actionTypeId)
                    return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable
            if column == self.getColIndex('amount'):
                items = self.items()
                record = items[row] if 0 <= row < len(items) else None
                actionTypeId = forceRef(record.value('actionType_id')) if record else None
                if actionTypeId:
                    actionType = CActionTypeCache.getById(actionTypeId)
                    if actionType.amountEvaluation == 0:
                        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable
                    else:
                        return Qt.ItemIsSelectable
            if column == self.getColIndex('uet'):
                return Qt.ItemIsSelectable
            return CInDocTableModel.flags(self, index)
        else:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled


    def canChangeAction(self, payStatus, actionId, eventId):
        if not payStatus and actionId and eventId:
            db = QtGui.qApp.db
            table = db.table('Action')
            cond = [table['event_id'].eq(eventId),
                    table['id'].eq(actionId),
                    table['payStatus'].ne(0),
                    table['deleted'].eq(0)
                    ]
            record = db.getRecordEx(table, [table['payStatus']], where=cond)
            payStatus = forceInt(record.value('payStatus')) if record else 0
        if payStatus and not QtGui.qApp.userHasRight(urEditAfterInvoicingEvent):
            return False
        return True


    def setData(self, index, value, role=Qt.EditRole, presetAction=None, related=False):
        column = index.column()
        row = index.row()
        payStatus = forceRef(self.items()[row].value('payStatus')) if 0 <= row < len(self.items()) else 0
        actionId = forceRef(self.items()[row].value('id')) if 0 <= row < len(self.items()) else None
        eventId = forceRef(self.items()[row].value('event_id')) if 0 <= row < len(self.items()) else None
        if not self.canChangeAction(payStatus, actionId, eventId) and not QtGui.qApp.refundRegistrationEnabled():
            return False
        items = self.items()
        cols = self.cols()
        col = cols[column]
        fieldName = col.fieldName()
        if role == Qt.EditRole:
            if row == self.rowCount()-1:
                if value.isNull() or fieldName != 'actionType_id':
                    return False
                actionTypeId = forceRef(value)
                actionTypeClass = CActionTypeCache.getById(actionTypeId).class_ if actionTypeId else None
                for iModel, model in enumerate(self.models):
                    if model.actionTypeClass == actionTypeClass:
                        model.addRow(forceRef(value), presetAction=presetAction, related=related)
                        self.regenerate()
                        i = self.itemIndex.index((iModel, model.rowCount()-2))
                        self.emit(SIGNAL('currentRowMovedTo(int)'), i)
                        items = self.items()
                        record = items[i]
                        self.eventEditor.onActionChanged(i)
                        return True
                return False
            iModel, iAction = self.itemIndex[row]
            actionsModel = self.models[iModel]
            if actionsModel.isLocked(iAction):
                return False
            record = items[row]
            oldValue = record.value(fieldName)
            if oldValue != value:
                if fieldName == 'actionType_id':
                    actionTypeId = forceRef(value)
                    oldActionTypeId = forceRef(oldValue)
                    newClass = CActionTypeCache.getById(actionTypeId).class_ if actionTypeId else None
                    oldClass = CActionTypeCache.getById(oldActionTypeId).class_ if oldActionTypeId else None
                    if newClass == oldClass:
                        actionsModel.setData(actionsModel.index(iAction, 0), value, Qt.EditRole)
                    else:
                        actionsModel.removeRow(iAction)
                        for iModel, model in enumerate(self.models):
                            if model.actionTypeClass == newClass:
                                model.addRow(forceRef(value))
                                self.regenerate()
                                i = self.itemIndex.index((iModel, model.rowCount()-2))
                                self.emit(SIGNAL('currentRowMovedTo(int)'), i)
                                self.eventEditor.onActionChanged(i)
                                return True
                else:
                    if fieldName == 'endDate':
                        date = forceDate(value)
                        record.setValue(fieldName, value)
                        self.eventEditor.onActionChanged(row)
                        status = forceInt(record.value('status'))
                        newStatus = status
                        if date:
                            newStatus = CActionStatus.finished
                        else:
                            if status in (CActionStatus.finished, CActionStatus.withoutResult, CActionStatus.appointed):
                                newStatus = CActionStatus.canceled
                        if status != newStatus:
                            record.setValue('status', toVariant(newStatus))
                            self.emitValueChanged(row, 'status')
                    elif fieldName == 'status':
                        record.setValue(fieldName, value)
                        status = forceInt(value)
                        date = forceDate(record.value('endDate'))
                        newDate = date
                        if status in (CActionStatus.finished, CActionStatus.withoutResult, CActionStatus.appointed) and not date.isValid():
                            newDate = QDateTime().currentDateTime()
                        else:
                            newDate = QDateTime()
                        if newDate != date:
                            record.setValue('endDate', toVariant(newDate))
                            self.emitValueChanged(row, 'endDate')
                    elif fieldName == 'person_id':
                        record.setValue(fieldName, value)
                        self.eventEditor.onActionChanged(row)
                    else:
                        record.setValue(fieldName, value)
                    self.emitCellChanged(row, column)
                    index = actionsModel.index(iAction, 0)
                    actionsModel.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index, index)
                    actionsModel.updateActionAmount(iAction)
            return True
        elif role == Qt.CheckStateRole:
            if row == self.rowCount()-1:
                return False
            iModel, iAction = self.itemIndex[row]
            actionsModel = self.models[iModel]
            if actionsModel.isLocked(iAction):
                return False
            record = items[row]
            oldValue = record.value(fieldName)
            if oldValue != value:
                record.setValue(fieldName, value)
                self.emitCellChanged(row, column)
                index = actionsModel.index(iAction, 0)
                actionsModel.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index, index)
                actionsModel.updateActionAmount(iAction)
            return True
        return False


    def setBegDate(self, row, date):
        self.setData(self.index(row, 3), toVariant(date), Qt.EditRole)
        self.setData(self.index(row, 4), toVariant(date), Qt.EditRole)


    def calcTotalUet(self):
        result = 0.0
        for item in self.items():
            result += self.colUet.getUet(item.value('amount'), item)
        return result


    def on_updateActionsPriceAndUet(self):
        self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), self.index(0, 9), self.index(len(self.items()), 9))



class CAccActionsSummary(CActionsSummaryModel):
    __pyqtSignals__ = ('sumChanged()',
                       )

    class CFinanceInDocTableCol(CRBInDocTableCol):
        def __init__(self):
            CRBInDocTableCol.__init__(self, u'Тип финансирования', 'finance_id', 10, 'rbFinance', addNone=True, preferredWidth=100)
            self.eventEditor = None


#        def toString(self, val, record):
#            if val.isNull():
#                val = toVariant(self.eventEditor.eventFinanceId)
#            return CRBInDocTableCol.toString(self, val, record)


#        def toStatusTip(self, val, record):
#            if val.isNull():
#                val = toVariant(self.eventEditor.eventFinanceId)
#            return CRBInDocTableCol.toStatusTip(self, val, record)


#        def setEditorData(self, editor, val, record):
#            if val.isNull():
#                id = self.eventEditor.eventFinanceId
#            else:
#                id = forceRef(val)
#            editor.setValue(id)


#        def getEditorData(self, editor):
#            val = editor.value()
#            if val == self.eventEditor.eventFinanceId:
#                val = None
#            return toVariant(val)

    class CContractInDocTableCol(CInDocTableCol):

        def __init__(self):
            CInDocTableCol.__init__(self, u'Договор', 'contract_id', 20)
            self.eventEditor = None

        def toString(self, val, record):
            contractId = forceRef(val)
#            if contractId is None:
#                financeId = forceRef(record.value('finance_id')) or self.eventEditor.eventFinanceId
#                if financeId == self.eventEditor.eventFinanceId:
#                    contractId = self.eventEditor.contractId
#
            if contractId:
                names = ['number', 'date', 'resolution']
                record = QtGui.qApp.db.getRecord('Contract', names, contractId)
                text = ' '.join([forceString(record.value(name)) for name in names])
            else:
                text = u'не задано'
            return QVariant(text)

        def getFirstContractId(self, actionTypeId, financeId, begDate, endDate):
            model = CContractDbModel(None)
            try:
                model.setOrgId(self.eventEditor.orgId)
                model.setEventTypeId(self.eventEditor.eventTypeId)
                model.setClientInfo(self.eventEditor.clientId,
                                    self.eventEditor.clientSex,
                                    self.eventEditor.clientAge,
                                    self.eventEditor.clientWorkOrgId,
                                    self.eventEditor.clientPolicyInfoList)
                model.setFinanceId(financeId)
                model.setActionTypeId(actionTypeId)
                model.setBegDate(begDate or QDate().currentDate())
                model.setEndDate(endDate or QDate().currentDate())
                model.initDbData()
                return model.getId(0)
            finally:
                model.deleteLater()

        def createEditor(self, parent):
            editor = CContractComboBox(parent, addNone=True)
            editor.setOrgId(self.eventEditor.orgId)
            editor.setClientInfo(self.eventEditor.clientId,
                                 self.eventEditor.clientSex,
                                 self.eventEditor.clientAge,
                                 self.eventEditor.clientWorkOrgId,
                                 self.eventEditor.clientPolicyInfoList)
            return editor

        def setEditorData(self, editor, value, record):
            financeId = forceRef(record.value('finance_id')) or self.eventEditor.eventFinanceId
            medicalAidKindId = forceInt(record.value('medicalAidKind_id')) or self.eventEditor.eventMedicalAidKindId
            editor.setFinanceId(financeId)
            editor.setMedicalAidKindId(medicalAidKindId)
            editor.setActionTypeId(forceRef(record.value('actionType_id')))
            contractId = forceRef(value)
            if contractId is None:
                if financeId == self.eventEditor.eventFinanceId:
                    contractId = self.eventEditor.contractId
            editor.setBegDate(forceDate(record.value('directionDate')) or QDate().currentDate())
            editor.setEndDate(forceDate(record.value('endDate')) or QDate().currentDate())
            editor.setValue(contractId)

        def getEditorData(self, editor):
            contractId = editor.value()
#            if contractId == self.eventEditor.contractId:
#                contractId = None
            return toVariant(contractId)

    class CRBServiceInDocTableCol(CRBInDocTableCol):
        def __init__(self, title, fieldName, width, tableName, **params):
            CRBInDocTableCol.__init__(self, title, fieldName, width, tableName, **params)
            self.eventEditor = None

        def toString(self, val, record):
            serviceId = None
            actionTypeId = forceRef(record.value('actionType_id'))
            if actionTypeId:
                # personId = forceRef(record.value('person_id'))
                # tariffCategoryId = self.eventEditor.getPersonTariffCategoryId(personId)
                contractId = forceRef(record.value('contract_id'))
                if contractId and contractId != self.eventEditor.contractId:
                    financeId = forceRef(QtGui.qApp.db.translate('Contract', 'id', contractId, 'finance_id'))
                else:
                    contractId = self.eventEditor.contractId
                    financeId = self.eventEditor.eventFinanceId
                serviceIdList = self.eventEditor.getActionTypeServiceIdList(actionTypeId, financeId)
                serviceId = serviceIdList[0] if len(serviceIdList) > 0 else None
            cache = CRBModelDataCache.getData(self.tableName, True)
            text = cache.getStringById(serviceId, self.showFields)
            return toVariant(text)


    def __init__(self, parent, editable=False):
        CActionsSummaryModel.__init__(self, parent, editable)
        self.paymentItems = []
        for col in self.cols():
            col.setReadOnly(True)
        self.addExtCol(CBoolInDocTableCol(u'Считать',    'account', 10), QVariant.Int)  # 14
        self.addExtCol(CFloatInDocTableCol(u'Цена',  'price', 6, precision=2), QVariant.Double).setReadOnly(True)  # 15
        self.addExtCol(CFloatInDocTableCol(u'Сумма', 'sum',   6, precision=2), QVariant.Double).setReadOnly(True)  # 16
        self.financeCol = self.addCol(CAccActionsSummary.CFinanceInDocTableCol())  # 17
        self.contractCol = self.addCol(CAccActionsSummary.CContractInDocTableCol())  # 18

        self.addCol(CActionsSummaryModel.CPayStatusCol())  # 19
        self.serviceCol = self.addCol(CAccActionsSummary.CRBServiceInDocTableCol(u'Услуга', 'id', 30, 'rbService', showFields=CRBComboBox.showCodeAndName)).setReadOnly(True)
        for col in self.cols():
            col.setSortable(True)
        self.addExtCol(CFloatInDocTableCol(u'Расчетная сумма', 'accSum', 6, precision=2), QVariant.Double).setReadOnly(True)
        self.setEnableAppendLine(False)


    def addExtColsFields(self):
        if self._extColsPresent:
            cols = []
            for col in self.cols():
                if not col.external():
                    cols.append(col.fieldName())
            extSqlFields = []
            for col in self.cols():
                if col.external():
                    fieldName = col.fieldName()
                    if fieldName not in cols:
                        extSqlFields.append(QtSql.QSqlField(fieldName, col.valueType()))
            if extSqlFields:
                for item in self.items():
                    for field in extSqlFields:
                        isNotField = True
                        for i in range(item.count()):
                            if item.field(i).name() == field.name():
                                isNotField = False
                                continue
                        if isNotField:
                            item.append(field)
                self.reset()


    def setEventEditor(self, eventEditor):
        self.eventEditor = eventEditor
        self.financeCol.eventEditor = eventEditor
        self.contractCol.eventEditor = eventEditor
        self.serviceCol.eventEditor = eventEditor


    def regenerate(self, top=0, bottom=0):
        CActionsSummaryModel.regenerate(self)
        self.addExtColsFields()
        self.setCountFlag()
        self.updatePricesAndSums(top, len(self.items()) - 1 if bottom == 0 else bottom)


    def regenerateOnLoad(self):
        CActionsSummaryModel.regenerate(self)
        self.addExtColsFields()
        self.setCountFlag()


    def setData(self, index, value, role=Qt.EditRole, presetAction=None):
        column = index.column()
        row = index.row()
        payStatus = forceRef(self.items()[row].value('payStatus')) if 0 <= row < len(self.items()) else 0
        actionId = forceRef(self.items()[row].value('id')) if 0 <= row < len(self.items()) else None
        eventId = forceRef(self.items()[row].value('event_id')) if 0 <= row < len(self.items()) else None
        if not self.canChangeAction(payStatus, actionId, eventId) and not QtGui.qApp.refundRegistrationEnabled():
            return False
        items = self.items()
        cols = self.cols()
        col = cols[column]
        fieldName = col.fieldName()
        if role == Qt.EditRole:
            iModel, iAction = self.itemIndex[row]
            actionsModel = self.models[iModel]
            if actionsModel.isLocked(iAction):
                return False
            record = items[row]
            oldValue = record.value(fieldName)
            if oldValue != value:
                if fieldName == 'note':
                    record.setValue(fieldName, value)
                    self.emitCellChanged(row, column)
                if fieldName == 'status':
                    updateRecord = True
                    if QtGui.qApp.refundRegistrationEnabled() and value in (CActionStatus.refused, CActionStatus.canceled):
                        updateRecord = self.generateRefund(record, fieldName)
                    if updateRecord:
                        record.setValue(fieldName, value)
                        self.emitCellChanged(row, column)

                if fieldName == 'finance_id':
                    record.setValue(fieldName, value)
                    self.emitCellChanged(row, column)
                    self.initContract(row)
                    self.updatePricesAndSums(row, row)
                elif fieldName == 'contract_id':
                    record.setValue(fieldName, value)
                    self.emitCellChanged(row, column)
                    self.updatePricesAndSums(row, row)
                elif fieldName == 'amount':
                    oldValue = forceDouble(record.value('amount'))
                    newValue = value
                    updateRecord = True
                    if QtGui.qApp.refundRegistrationEnabled():
                        refund = self.generateRefund(record, fieldName, oldValue, newValue)
                        updateRecord = refund
                    if updateRecord:
                        record.setValue(fieldName, value)
                        self.emitCellChanged(row, column)
                        self.updatePricesAndSums(row, row)
                else:
                    return False
            return True
        if role == Qt.CheckStateRole:
            # if column == 14: # 'account'
            if column == self.getColIndex('account'):
                val = forceInt(items[row].value('account'))
                items[row].setValue('account',  QVariant(forceInt(not val)))
                self.emitCellChanged(row, column)
                self.updatePricesAndSums(row, row)
            return True
        return False


    def generateRefund(self, record, fieldName, oldValue=None, newValue=None):
        payStatus = forceInt(record.value('payStatus'))
        financeId = forceInt(record.value('finance_id'))
        widget = QtGui.qApp.activeModalWidget() or QtGui.qApp.mainWindow or None
        buttons = QtGui.QMessageBox.Yes | QtGui.QMessageBox.No
        if payStatus and financeId == CFinanceType.getId(CFinanceType.cash):
            result = QtGui.QMessageBox.question(widget,
                                                u'Внимание!',
                                                u'Оформить возврат?',
                                                buttons,
                                                QtGui.QMessageBox.No)
            if result == QtGui.QMessageBox.Yes:
                if financeId != CFinanceType.getId(CFinanceType.cash):
                    QtGui.QMessageBox.critical(widget,
                                               u'Внимание!',
                                               u'Невозможно оформить возврат. Тип финансирования "%s" не является платными услугами' % (CFinanceType.getNameById(financeId)),
                                               QtGui.QMessageBox.Close)
                    return False
                elif not payStatus:
                    QtGui.QMessageBox.critical(widget,
                                               u'Внимание!',
                                               u'Невозможно оформить возврат. Действие не выставлено',
                                               QtGui.QMessageBox.Close)
                    return False
                else:
                    if fieldName == u'amount':
                        item = record
                        paymentItems = self.paymentItems
                        cashOperationId = self.getRefundCashOperationId()
                        paymentItemSum = None
                        _sum = forceDouble(item.value('sum'))
                        oldValue = forceInt(oldValue) if forceInt(oldValue) else 1
                        price = _sum/oldValue
                        refundSum = - price*(oldValue-forceInt(newValue))
                        paymentItem = None
                        for paymentItem in paymentItems:
                            if forceDate(paymentItem.value('date')) == QDate().currentDate() and forceDouble(paymentItem.value('sum')) < 0:
                                paymentItemSum = forceDouble(paymentItem.value('sum'))
                                break
                        if paymentItemSum:
                            newSum = refundSum + paymentItemSum
                            paymentItem.setValue('sum', toVariant(newSum))
                            if cashOperationId:
                                paymentItem.setValue('cashOperation_id', toVariant(cashOperationId))
                        else:
                            newRefundRecord = self.paymentItemsEmptyRecord
                            newRefundRecord.setValue('sum', toVariant(refundSum))
                            if cashOperationId:
                                newRefundRecord.setValue('cashOperation_id', toVariant(cashOperationId))
                            paymentItems.append(newRefundRecord)

                        accountChanges = QtGui.QMessageBox.question(widget,
                                                                    u'Внимание!',
                                                                    u'Внести изменения в счет?',
                                                                    buttons,
                                                                    QtGui.QMessageBox.No)
                        if accountChanges == QtGui.QMessageBox.Yes:
                            actionId = forceInt(item.value('id'))
                            financeId = forceInt(item.value('finance_id'))
                            from Accounting.PayStatusDialog import CPayStatusDialog
                            payStatusDialog = CPayStatusDialog(None, financeId)
                            payStatusDialog.edtNote.setVisible(False)
                            payStatusDialog.lblNote.setVisible(False)
                            payStatusDialog.edtFactPayed.setVisible(False)
                            payStatusDialog.rbnFactPayed.setVisible(False)
                            payStatusDialog.rbnRefused.setVisible(False)
                            payStatusDialog.rbnAccepted.setVisible(False)
                            payStatusDialog.edtNumber.setVisible(False)
                            payStatusDialog.lblNumber.setVisible(False)
                            payStatusDialog.edtDate.setVisible(False)
                            payStatusDialog.lblDate.setVisible(False)
                            payStatusDialog.lblPayRefuseType.setEnabled(True)
                            payStatusDialog.cmbRefuseType.setEnabled(True)
                            payStatusDialog.cmbRefuseType.setTable('rbPayRefuseType',
                                                                   addNone=False,
                                                                   filter='finance_id=\'%s\'' % financeId)
                            if payStatusDialog.exec_():
                                refuseTypeId = payStatusDialog.cmbRefuseType.value()
                                if refuseTypeId and actionId:
                                    self.changeAccountItemAmountAndSum(actionId, forceInt(newValue), refuseTypeId)

                            self.paymentItems = paymentItems
                            self.emitAllChanged()

                    elif fieldName == u'status':
                        item = record
                        paymentItems = self.paymentItems
                        cashOperationId = self.getRefundCashOperationId()
                        paymentItemSum = None
                        _sum = forceDouble(item.value('sum'))
                        # oldValue = forceInt(oldValue) if forceInt(oldValue) else 1
                        # price = sum/oldValue
                        refundSum = - _sum
                        paymentItem = None
                        for paymentItem in paymentItems:
                            if forceDate(paymentItem.value('date')) == QDate().currentDate() and forceDouble(paymentItem.value('sum')) < 0:
                                paymentItemSum = forceDouble(paymentItem.value('sum'))
                                break
                        if paymentItemSum:
                            newSum = refundSum + paymentItemSum
                            paymentItem.setValue('sum', toVariant(newSum))
                            if cashOperationId:
                                paymentItem.setValue('cashOperation_id', toVariant(cashOperationId))
                        else:
                            newRefundRecord = self.paymentItemsEmptyRecord
                            newRefundRecord.setValue('sum', toVariant(refundSum))
                            if cashOperationId:
                                newRefundRecord.setValue('cashOperation_id', toVariant(cashOperationId))
                            paymentItems.append(newRefundRecord)

                        accountChanges = QtGui.QMessageBox.question(widget,
                                                                    u'Внимание!',
                                                                    u'Внести изменения в счет?',
                                                                    buttons,
                                                                    QtGui.QMessageBox.No)
                        if accountChanges == QtGui.QMessageBox.Yes:
                            actionId = forceInt(item.value('id'))
                            financeId = forceInt(item.value('finance_id'))
                            from Accounting.PayStatusDialog import CPayStatusDialog
                            payStatusDialog = CPayStatusDialog(None, financeId)
                            payStatusDialog.edtNote.setVisible(False)
                            payStatusDialog.lblNote.setVisible(False)
                            payStatusDialog.edtFactPayed.setVisible(False)
                            payStatusDialog.rbnFactPayed.setVisible(False)
                            payStatusDialog.rbnRefused.setVisible(False)
                            payStatusDialog.rbnAccepted.setVisible(False)
                            payStatusDialog.edtNumber.setVisible(False)
                            payStatusDialog.lblNumber.setVisible(False)
                            payStatusDialog.edtDate.setVisible(False)
                            payStatusDialog.lblDate.setVisible(False)
                            payStatusDialog.lblPayRefuseType.setEnabled(True)
                            payStatusDialog.cmbRefuseType.setEnabled(True)
                            payStatusDialog.cmbRefuseType.setTable('rbPayRefuseType',
                                                                   addNone=False,
                                                                   filter='finance_id=\'%s\'' % financeId)
                            if payStatusDialog.exec_():
                                refuseTypeId = payStatusDialog.cmbRefuseType.value()
                                if refuseTypeId and actionId:
                                    self.changeAccountItemAmountAndSum(actionId, None, refuseTypeId)

                            self.paymentItems = paymentItems
                            self.emitAllChanged()

        return True


    def changeAccountItemAmountAndSum(self, actionId, newAmount=None, refuseTypeId=None):
        db = QtGui.qApp.db
        tableAccount = db.table('Account')
        tableAccountItem = db.table('Account_Item')
        recordItem = db.getRecordEx(tableAccountItem, '*', tableAccountItem['action_id'].eq(actionId))
        record = db.getRecordEx(tableAccount, '*', tableAccount['id'].eq(forceInt(recordItem.value('master_id'))))
        if recordItem:
            amount = forceDouble(recordItem.value('amount')) if forceDouble(recordItem.value('amount')) else 1
            sum = forceDouble(recordItem.value('sum'))
            payedSum = forceDouble(recordItem.value('payedSum'))
            deltaAmount = amount-newAmount if newAmount else amount
            price = sum/amount
            recordItem.setValue('payedSum', toVariant(payedSum-deltaAmount*price))
            recordItem.setValue('refuseType_id', toVariant(refuseTypeId))
            db.updateRecord(tableAccountItem, recordItem)
            if record:
                accountPayedAmount = forceDouble(record.value('payedAmount'))
                accountPayedSum = forceDouble(record.value('payedSum'))
                accountRefusedAmount = forceDouble(record.value('refusedAmount'))
                accountRefusedSum = forceDouble(record.value('refusedSum'))
                record.setValue('payedAmount', toVariant(accountPayedAmount-deltaAmount))
                record.setValue('payedSum', toVariant(accountPayedSum-(price*deltaAmount)))
                record.setValue('refusedAmount', toVariant(accountRefusedAmount+deltaAmount))
                record.setValue('refusedSum', toVariant(accountRefusedSum+(price*deltaAmount)))
                db.updateRecord(tableAccount, record)


    def setPaymentItems(self, items=[]):
        self.paymentItems = items


    def setPaymentItemsEmptyRecord(self, record):
        self.paymentItemsEmptyRecord = record


    def getRefundCashOperationId(self):
        cashOperationId = None
        db = QtGui.qApp.db
        table = db.table('rbCashOperation')
        record = db.getRecordEx(table, 'id', table['name'].like(u'Возврат'))
        if record:
            cashOperationId = forceInt(record.value('id'))
        return cashOperationId


    def initContract(self, row):
        item = self.items()[row]
        actionTypeId = forceRef(item.value('actionType_id'))
        financeId = forceRef(item.value('finance_id'))
        if financeId:
            if financeId == self.eventEditor.eventFinanceId and getEventActionContract(self.eventEditor.eventTypeId):
                contractId = self.eventEditor.contractId
            else:
                begDate = forceDate(item.value('directionDate'))
                endDate = forceDate(item.value('endDate'))
                contractId = self.contractCol.getFirstContractId(actionTypeId, financeId, begDate, endDate)
        else:
            contractId = None
        item.setValue('contract_id', toVariant(contractId))
        self.emitValueChanged(row, 'contract_id')


    def onDataChanged(self, topLeft, bottomRight):
        CActionsSummaryModel.onDataChanged(self, topLeft, bottomRight)
        self.updatePricesAndSums(topLeft.row(), bottomRight.row())


    def onAmountChanged(self, row):
        CActionsSummaryModel.onAmountChanged(self, row)
        iModel = self.models.index(self.sender())
        try:
            row = self.itemIndex.index((iModel, row))
        except:
            row = -1

        if row >= 0:
            self.updatePricesAndSums(row, row)
        else:
            self.updatePricesAndSums(0, len(self.items())-1)


    def setContractId(self, contractId):
        if getEventActionContract(self.eventEditor.eventTypeId):
            financeId = self.eventEditor.eventFinanceId
            for row, item in enumerate(self.items()):
                if forceRef(item.value('finance_id')) != financeId:
                    item.setValue('contract_id', contractId)
                    item.setValue('finance_id', financeId)
#                self.emitFieldChanged(row, 'contract_id')
                self.emitCellChanged(row, self.getColIndex('contract_id'))
        elif getEventActionFinance(self.eventEditor.eventTypeId):
            for row, item in enumerate(self.items()):
                if forceRef(item.value('contract_id')) is None:
                    financeId = self.eventEditor.getActionFinanceId(item)
                    if forceRef(item.value('finance_id')) != financeId:
                        item.setValue('finance_id', financeId)
                        self.emitCellChanged(row, self.getColIndex('finance_id'))
        self.updatePricesAndSums(0, len(self.items())-1)



    def getTariffMap(self, contractId, actionEndDate):
        tariffDescr = self.eventEditor.contractTariffCache.getTariffDescr(contractId, self.eventEditor, actionEndDate)
        return tariffDescr.actionTariffMap


    def getTariffDateMap(self, contractId, date, financeId):
        tariffDescr = self.eventEditor.contractTariffCache.getTariffDate(contractId, self.eventEditor, date, financeId)
        return tariffDescr.dateTariffMap


    def setCountFlag(self):
        cashFinanceId = CFinanceType.getId(CFinanceType.cash)
        eventFinanceId = self.eventEditor.eventFinanceId
        for item in self.items():
            itemFinanceId = forceRef(item.value('finance_id'))
            if itemFinanceId is None:
                itemFinanceId = eventFinanceId
            item.setValue('account', toVariant(itemFinanceId == cashFinanceId))


    def updatePricesAndSums(self, top, bottom):
        sumChanged = False
        financeActionTypes = dict()
        personIdSet = set()
        for i in xrange(top, bottom + 1):
            try:
                item = self.items()[i]
            except IndexError:
                break
            actionTypeId = forceRef(item.value('actionType_id'))
            if actionTypeId:
                contractId = forceRef(item.value('contract_id'))
                personId = forceRef(item.value('person_id'))
                personIdSet.add(personId)
                if contractId and contractId != self.eventEditor.contractId:
                    financeId = self.eventEditor.mapContractIdToFinance.get(contractId, None)
                    if not financeId:
                        financeId = forceRef(QtGui.qApp.db.translate('Contract', 'id', contractId, 'finance_id'))
                        self.eventEditor.mapContractIdToFinance[contractId] = financeId
                else:
                    financeId = self.eventEditor.eventFinanceId
                financeActionTypes.setdefault(financeId, []).append(actionTypeId)
        for key in financeActionTypes.keys():
            self.eventEditor.mappingActionTypeList(financeActionTypes[key], key)
        self.eventEditor.cachePersonSSF(personIdSet)
        for i in xrange(top, bottom + 1):
            try:
                item = self.items()[i]
            except IndexError:
                break
            sumChanged = self.updatePriceAndSum(i, item) or sumChanged
        if sumChanged:
            self.emitSumChanged()


    def getPriceAccountItem(self, contractId, eventId, actionId):
        price = 0.0
        if contractId and eventId and actionId:
            db = QtGui.qApp.db
            tableAccount = db.table('Account')
            tableAccountItem = db.table('Account_Item')
            queryTable = tableAccount.innerJoin(tableAccountItem, tableAccountItem['master_id'].eq(tableAccount['id']))
            cond = [tableAccount['contract_id'].eq(contractId),
                    tableAccountItem['event_id'].eq(eventId),
                    tableAccountItem['action_id'].eq(actionId),
                    tableAccount['deleted'].eq(0),
                    tableAccountItem['deleted'].eq(0)
                    ]
            record = db.getRecordEx(queryTable, [tableAccountItem['id'], tableAccountItem['price']], cond, u'Account_Item.id DESC')
            price = forceDouble(record.value('price')) if record else 0.0
        return price


    def updatePriceAndSum(self, row, item):
        result = False
        actionTypeId = forceRef(item.value('actionType_id'))
        if not actionTypeId:
            return result

        amount = forceDouble(item.value('amount'))
        price = 0.0
        personId = forceRef(item.value('person_id'))
        tariffCategoryId = self.eventEditor.getPersonTariffCategoryId(personId)
        contractId = forceRef(item.value('contract_id'))
        if contractId and contractId != self.eventEditor.contractId:
            financeId = self.eventEditor.mapContractIdToFinance.get(contractId, None)
            if not financeId:
                financeId = forceRef(QtGui.qApp.db.translate('Contract', 'id', contractId, 'finance_id'))
                self.eventEditor.mapContractIdToFinance[contractId] = financeId
        else:
            contractId = self.eventEditor.contractId
            financeId = self.eventEditor.eventFinanceId

        serviceIdList = self.eventEditor.getActionTypeServiceIdList(actionTypeId, financeId)
        # Цену определять только если есть услуги
        if serviceIdList:
            if forceInt(item.value('payStatus')) == 0:
                date = forceDate(item.value('endDate'))
                if not date and self.eventEditor.eventDate:
                    if isinstance(self.eventEditor.eventDate, QDateTime):
                        date = self.eventEditor.eventDate.date()
                    else:
                        date = self.eventEditor.eventDate
                if not date:
                    date = forceDate(item.value('begDate'))
                if not date:
                    date = forceDate(item.value('directionDate'))
                if date:
                    tariffMap = self.getTariffDateMap(contractId, self.eventEditor.eventSetDateTime, financeId)
                    price = CContractTariffCache.getPriceToDate(tariffMap, serviceIdList, tariffCategoryId, date)
            else:
                price = self.getPriceAccountItem(contractId, forceRef(item.value('event_id')),
                                                 forceRef(item.value('id')))

        if forceDouble(self.items()[row].value('price')) != price:
            self.items()[row].setValue('price', toVariant(price))
            self.emitCellChanged(row, self.items()[row].indexOf('price'))
            result = True

        sum = price * amount if amount else price
        if sum != forceDouble(self.items()[row].value('sum')):
            self.items()[row].setValue('sum', toVariant(sum))
            self.emitCellChanged(row, self.items()[row].indexOf('sum'))
            result = True
        if self.items()[row].value('accSum').isNull():
            self.items()[row].setValue('accSum', toVariant(0))

        if forceBool(item.value('account')):
            if forceDouble(self.items()[row].value('accSum')) != sum:
                self.items()[row].setValue('accSum', toVariant(sum))
                self.emitCellChanged(row, self.items()[row].indexOf('accSum'))
                result = True
        else:
            if forceDouble(self.items()[row].value('accSum')) != 0:
                self.items()[row].setValue('accSum', toVariant(0))
                self.emitCellChanged(row, self.items()[row].indexOf('accSum'))
                result = True
        return result


    def emitSumChanged(self):
        self.emit(SIGNAL('sumChanged()'))


    def sum(self):
        accSum = []
        for item in self.items():
            if forceInt(item.value('status')) not in (CActionStatus.refused, CActionStatus.canceled):
                accSum.append(forceDouble(item.value('accSum')))
        return sum(accSum)


class CFxxxActionsSummaryModel(CActionsSummaryModel):
    def setData(self, index, value, role=Qt.EditRole, presetAction=None, related=False):
        result = CActionsSummaryModel.setData(self, index, value, role, presetAction, related=related)
        if result:
            column = index.column()
            if column == self.getColIndex('endDate'):  # end date
                newDateTime = forceDateTime(value)
                eventSetDateTime = self.eventEditor.eventSetDateTime
                newDate = newDateTime.date() if isinstance(newDateTime, QDateTime) else newDateTime
                eventSetDate = eventSetDateTime.date() if isinstance(eventSetDateTime, QDateTime) else eventSetDateTime
                if not newDate.isValid():
                    pass
                elif newDate < eventSetDate:
                    self.setBegDate(index.row(), QDate())
                elif newDate >= eventSetDate:
                    row = index.row()
                    if not forceDate(self.data(self.index(row, 3), Qt.EditRole)):
                        self.setData(self.index(row, 3), toVariant(eventSetDateTime), Qt.EditRole)
                    if not forceDate(self.data(self.index(row, 4), Qt.EditRole)):
                        self.setData(self.index(row, 4), toVariant(eventSetDateTime), Qt.EditRole)
            if role == Qt.EditRole:
                if column == self.getColIndex('MKB'):
                    mkb = forceStringEx(value)
                    if mkb:
                        acceptable = self.eventEditor.checkDiagnosis(unicode(mkb))
                        if not acceptable:
                            result = self.setData(self.index(index.row(), self.getColIndex('MKB')), toVariant(None), Qt.EditRole)
        self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index, index)
        return result


    def setBegDate(self, row, date):
        execDate = forceDate(self.data(self.index(row, 4), Qt.EditRole))
        if not execDate:
            CActionsSummaryModel.setBegDate(self, row, date)
        else:
            CActionsSummaryModel.setBegDate(self, row, date if date <= execDate else QDate())
    
    
    def flags(self, index=QModelIndex()):
        row = index.row()
        column = index.column()
        items = self.items()
        if row >= len(self.items()):
            return Qt.NoItemFlags
        record = items[row] if 0 <= row < len(items) else None
        actionTypeId = forceRef(record.value('actionType_id')) if record else None
        actionType = CActionTypeCache.getById(actionTypeId) if actionTypeId else None
        if actionType:
            if column == self.getColIndex('begDate'):
                if actionType.editBegDate:
                    return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable
                else:
                    return Qt.ItemIsSelectable | Qt.ItemIsEnabled
            elif column == self.getColIndex('endDate'):
                if actionType.editEndDate:
                    return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable
                else:
                    return Qt.ItemIsSelectable | Qt.ItemIsEnabled
            elif column == self.getColIndex('status'):
                if actionType.editStatus:
                    return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable
                else:
                    return Qt.ItemIsSelectable | Qt.ItemIsEnabled
            elif column == self.getColIndex('setPerson_id'):
                if actionType.editSetPerson:
                    return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable
                else:
                    return Qt.ItemIsSelectable | Qt.ItemIsEnabled
            elif column == self.getColIndex('person_id'):
                if actionType.editExecPers:
                    return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable
                else:
                    return Qt.ItemIsSelectable | Qt.ItemIsEnabled
            elif column == self.getColIndex('org_id'):
                if actionType.editOrg:
                    return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable
                else:
                    return Qt.ItemIsSelectable | Qt.ItemIsEnabled
            elif column == self.getColIndex('note'):
                if actionType.editNote:
                    return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable
                else:
                    return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return CActionsSummaryModel.flags(self, index)
