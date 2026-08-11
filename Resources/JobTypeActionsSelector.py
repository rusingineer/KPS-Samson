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

from PyQt4 import QtGui, QtSql
from PyQt4.QtCore import Qt, QDate, QObject, QVariant, pyqtSignature, QDateTime

from library.Counter                     import CCounterController
from library.DialogBase                  import CDialogBase
from library.InDocTable                  import CRecordListModel, CBoolInDocTableCol, CFloatInDocTableCol, CRBInDocTableCol
from library.RecordLock                  import CRecordLockMixin
from library.Utils                       import calcAgeTuple, forceBool, forceDate, forceDateTime, forceDouble, forceInt, forceRef, forceString, forceStringEx, addDotsEx, toVariant

from Events.Action                       import CAction
from Events.ActionTemplateChoose         import CActionTemplateCache
from Events.ContractTariffCache          import CContractTariffCache
from Events.MapActionTypeToServiceIdList import CMapActionTypeIdToServiceIdList
from Events.Utils                        import getEventActionFinance, getEventFinanceId, recordAcceptable, isEventTerritorialBelonging
from KLADR.Utils                         import KLADRMatch
from Registry.Utils                      import getClientInfo, getClientWork

from Ui_JobTypeActionsSelector import Ui_JobTypeActionsSelectorDialog

class CJobTypeActionsSelector(CDialogBase, Ui_JobTypeActionsSelectorDialog):
    def __init__(self, parent, jobTypeId, existsActionTypeIdList=[]):
        CDialogBase.__init__(self, parent)
        self._jobTypeId = jobTypeId
        self.addModels('ActionTypes', CJobTypeActionsSelectorModel(self, existsActionTypeIdList))
        self.setupUi(self)
        self.setModels(self.tblActionTypes, self.modelActionTypes, self.selectionModelActionTypes)
        self._load()
        self.setWindowTitle(u'Добавить действия')


    def _load(self):
        self.modelActionTypes.loadItems(self._jobTypeId)


    def checkedItems(self):
        return self.modelActionTypes.checkedItems()


    def findByCode(self, value):
        uCode = unicode(value).upper()
        codes = self.modelActionTypes.actionsCacheByCode.keys()
        codes.sort()
        for c in codes:
            if unicode(c).startswith(uCode):
                return self.modelActionTypes.actionsCacheByCode[c]
        return self.findByName(value)


    def findByName(self, name):
        uName = unicode(name).upper()
        names = self.modelActionTypes.actionsCodeCacheByName.keys()
        for n in names:
            if uName in n:
                code = self.modelActionTypes.actionsCodeCacheByName[n]
                return self.modelActionTypes.actionsCacheByCode.get(code, None)
        return None


    @pyqtSignature('QString')
    def on_edtFindByCode_textChanged(self, text):
        if text:
            row = self.findByCode(text)
            if row is not None:
                self.tblActionTypes.setCurrentRow(row)
            else:
                self.tblActionTypes.setCurrentRow(0)
        else:
            self.tblActionTypes.setCurrentRow(0)


    @pyqtSignature('int')
    def on_chkFindFilter_stateChanged(self, state):
        self.edtFindByCode.setText(u'')
        if state == Qt.Unchecked:
            self.modelActionTypes.actionTypeFindFilter = u''
            self.modelActionTypes.loadItems(self._jobTypeId)
        elif state == Qt.Checked and self.edtFindFilter.text():
            self.modelActionTypes.actionTypeFindFilter = addDotsEx(forceStringEx(self.edtFindFilter.text()))
            self.modelActionTypes.loadItems(self._jobTypeId)


    @pyqtSignature('QString')
    def on_edtFindFilter_textChanged(self, text):
        if self.chkFindFilter.isChecked():
            self.modelActionTypes.actionTypeFindFilter = addDotsEx(forceStringEx(text))
            self.modelActionTypes.loadItems(self._jobTypeId)


    @pyqtSignature('bool')
    def on_chkOnlyNotExists_toggled(self, value):
        self.modelActionTypes.setOnlyNotExists(value)
        self._load()


# #######################################################

class CJobTypeActionsSelectorModel(CRecordListModel):
    def __init__(self, parent, existsActionTypeIdList=[]):
        CRecordListModel.__init__(self, parent)
        self.addCol(CBoolInDocTableCol( u'Включить',      'checked',        10))
        self.addCol(CRBInDocTableCol(   u'Тип действия',  'actionType_id',  14, 'ActionType', showFields=2).setReadOnly())
        self.addCol(CFloatInDocTableCol(u'Количество',    'amount',         12, precision=2))
#        self.addCol(CIntInDocTableCol(  u'Группа выбора', 'selectionGroup', 12).setReadOnly())
        self._existsActionTypeIdList = existsActionTypeIdList
        self._cacheItemsByGroup = {}
        self.actionsCacheByCode = {}
        self.actionsCodeCacheByName = {}
        self.actionTypeFindFilter = u''
        self.isOnlyNotExists = True


    def setOnlyNotExists(self, value):
        self.isOnlyNotExists = value


    def loadItems(self, masterId):
        self.actionsCacheByCode.clear()
        self.actionsCodeCacheByName.clear()
        db = QtGui.qApp.db
        table = db.table('rbJobType_ActionType')
        tableActionType = db.table('ActionType')
        cols = [table['id'],
                table['master_id'],
                table['actionType_id'],
                table['selectionGroup'],
                tableActionType['amount'],
                tableActionType['code'],
                tableActionType['name'],
                ]
        cond = [table['master_id'].eq(masterId),
                tableActionType['deleted'].eq(0)
                ]
        if self._existsActionTypeIdList and self.isOnlyNotExists:
            cond.append(table['actionType_id'].notInlist(self._existsActionTypeIdList))
        if self.actionTypeFindFilter:
            cond.append(db.joinOr([tableActionType['code'].like(self.actionTypeFindFilter), tableActionType['name'].like(self.actionTypeFindFilter)]))
        queryTable = table.innerJoin(tableActionType, tableActionType['id'].eq(table['actionType_id']))
        self._items = db.getRecordList(queryTable, cols, cond, ['id'])
        for row, item in enumerate(self._items):
            item.append(QtSql.QSqlField('checked', QVariant.Bool))
            item.append(QtSql.QSqlField('amount',  QVariant.Double))
            selectionGroup = forceInt(item.value('selectionGroup'))
            groupItemList = self._cacheItemsByGroup.setdefault(selectionGroup, [])
            groupItemList.append(item)
            if selectionGroup == 1 or (selectionGroup and len(groupItemList) == 1):
                item.setValue('checked', QVariant(True))
            code = forceString(item.value('code')).upper()
            name = forceString(item.value('name')).upper()
            existCode = self.actionsCacheByCode.get(code, None)
            if existCode is None:
                self.actionsCacheByCode[code] = row
            existName = self.actionsCodeCacheByName.get(name, None)
            if existName is None:
                self.actionsCodeCacheByName[name] = code
        self.reset()


    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.CheckStateRole and forceBool(value):
            row = index.row()
            item = self._items[row]
            selectionGroup = forceInt(item.value('selectionGroup'))
            if selectionGroup > 1:
                groupItemList = self._cacheItemsByGroup.get(selectionGroup, [])
                for item in groupItemList:
                    item.setValue('checked', QVariant(False))
                self.emitColumnChanged(self.getColIndex('checked'))
        return CRecordListModel.setData(self, index, value, role)


    def checkedItems(self):
        return [(forceRef(item.value('actionType_id')), forceDouble(item.value('amount'))) for item in self._items if forceBool(item.value('checked'))]


class CJobTypeActionsAddingHelper():
    ## special class for help to add Actions to Event by actual job ticket id
    def __init__(self, holder, forceValues=None):
        ## holder class must have following methods:
        # jobTicketId - method, return actual job ticket id
        # actionTypeIdList - method, return list of existing action type ids
        # getDefaultEventId - method, return event id if cannot to find by action
        # getTakenTissueId - method, return actual taken tissue id if exists
        # getTakenTissueTypeId - method, return actual taken tissue type id if exists
        # applyDependents(int actionId, CAction action) - method, apply dependents if need
        # addActionList(list<CAction> l) - add actual actions

        self._holder = holder
        self._forceValues = forceValues


    def addActions(self, sourceActionId):
        def currentEventId():
            eventId = forceRef(QtGui.qApp.db.translate('Action', 'id', sourceActionId, 'event_id'))
            if not eventId:
                eventId = self._holder.getDefaultEventId()
            return eventId
        jobTicketId = self._holder.jobTicketId()
        jobId = forceRef(QtGui.qApp.db.translate('Job_Ticket', 'id', jobTicketId, 'master_id'))
        jobTypeId = forceRef(QtGui.qApp.db.translate('Job', 'id', jobId, 'jobType_id'))

        actionTypeIdList = self._holder.actionTypeIdList()
        dlg = CJobTypeActionsSelector(self._holder, jobTypeId, actionTypeIdList)

        if dlg.exec_():
            actionTypeItemsList = list(dlg.checkedItems())
            if actionTypeItemsList:
                eventId = currentEventId()
                if eventId:
                    currentActionCount = QtGui.qApp.db.getCount('Action', 'id', 'event_id=%d'%eventId)
                else:
                    currentActionCount = 0
                # WFT? Ещё кусочек говнокода...
                if not hasattr(self._holder, 'eventEditor') or self._holder.eventEditor is None:
                    self.creatEventPossibilities(eventId)

                if not QtGui.qApp.counterController():
                    QtGui.qApp.setCounterController(CCounterController())
                QtGui.qApp.setJTR(self._holder.eventEditor)
                try:
                    date = QDate.currentDate()
                    actionList = []
                    for additionalIdx, (actionTypeId, amount) in enumerate(actionTypeItemsList):
                        idx = additionalIdx + currentActionCount
                        action = self.addEventAction(eventId, actionTypeId, jobTicketId, date, idx, amount)
                        if action:
                            actionList.append(action)
                    self._holder.addActionList(actionList)
                finally:
                    if QtGui.qApp.counterController():
                        QtGui.qApp.delAllCounterValueIdReservation()
                    QtGui.qApp.unsetJTR(self._holder.eventEditor)
                    QtGui.qApp.setCounterController(None)


    def addEventAction(self, eventId, actionTypeId, jobTicketId, date, idx, amount):
        def checkActionTypeIdByTissueType(actionTypeId):
#            tissueTypeId = forceRef(self._holder.takenTissueRecord.value('tissueType_id'))
            tissueTypeId = self._holder.getTakenTissueTypeId()
            table = QtGui.qApp.db.table('ActionType_TissueType')
            cond = [table['master_id'].eq(actionTypeId),
                    table['tissueType_id'].eq(tissueTypeId)]
            return bool(QtGui.qApp.db.getRecordEx(table, 'id', cond))

        def setTicketIdToAction(action, jobTicketId):
            propertyTypeList = action.getType().getPropertiesById().values() if action else []
            for propertyType in propertyTypeList:
                if propertyType.isJobTicketValueType():
                    property = action.getPropertyById(propertyType.id)
                    property.setValue(jobTicketId)
                    return True
            return False

        db = QtGui.qApp.db
        record = db.table('Action').newRecord()
        record.setValue('createDatetime', toVariant(QDateTime.currentDateTime()))
        record.setValue('createPerson_id', toVariant(QtGui.qApp.userId))
        record.setValue('modifyDatetime', toVariant(QDateTime.currentDateTime()))
        record.setValue('modifyPerson_id', toVariant(QtGui.qApp.userId))
        action = CAction.getFilledAction(self._holder.eventEditor, record, actionTypeId)
        if setTicketIdToAction(action, jobTicketId):
            record.setValue('setPerson_id', QVariant(QtGui.qApp.userId))
            if amount is not None:
                record.setValue('amount', QVariant(amount))
            takenTissueId = self._holder.getTakenTissueId()
            if takenTissueId and checkActionTypeIdByTissueType(actionTypeId):
                record.setValue('takenTissueJournal_id', QVariant(takenTissueId))
            if self._forceValues:
                status = self._forceValues.get('status', None)
                if status:
                    record.setValue('status', QVariant(status))
                setPersonId = self._forceValues.get('setPersonId', None)
                if setPersonId:
                    record.setValue('setPerson_id', QVariant(setPersonId))
                begDate = self._forceValues.get('begDate', None)
                if begDate:
                    record.setValue('begDate', QVariant(begDate))
                directionDate = self._forceValues.get('directionDate', None)
                if directionDate:
                    record.setValue('directionDate', QVariant(directionDate))
            actionId = action.save(eventId, idx)
            if isinstance(self, CRecordLockMixin):
                CRecordLockMixin.lock(self._holder, 'Action', actionId)
            self._holder.applyDependents(actionId, action)
            return action
        return None


    def creatEventPossibilities(self, eventId):
        setattr(self._holder, 'eventEditor', CFakeEventEditor(self._holder, eventId))
        setattr(self._holder, 'actionTemplateCache', CActionTemplateCache(self._holder.eventEditor,
                                                                          self._holder.eventEditor.cmbSetPerson))


u'''Классы и функции помогающие имитировать ситуацию добавления действия в редакторе.'''
class CFakeEventEditor(QObject, CMapActionTypeIdToServiceIdList, CRecordLockMixin):
    ## Special class for imitation event editor's behavior

    ctOther    = 0
    ctLocal    = 1
    ctProvince = 2
    ctRegAddress = 0
    ctLocAddress = 1
    ctInsurer    = 2

    # fo F001
    class CFakeCmbSetPerson():
        def __init__(self, parent):
            self._parent = parent
        def value(self):
            return self._parent.personId
        def currentPersonSpecialityId(self):
            return self._parent.personSpecialityId


    def __init__(self, parent, eventId):
        QObject.__init__(self, parent)
        CMapActionTypeIdToServiceIdList.__init__(self)
        CRecordLockMixin.__init__(self)
        db           = QtGui.qApp.db
        self._parent = parent
        self._id     = eventId
        self._record = db.getRecord('Event', '*', eventId)

        self.eventTypeId        = forceRef(self._record.value('eventType_id'))
        self.eventSetDateTime   = forceDateTime(self._record.value('setDate'))
        self.eventDate          = forceDate(self._record.value('execDate'))
        self.personId           = forceRef(self._record.value('setPerson_id'))
        orgId                   = forceRef(self._record.value('org_id'))
        self.orgId              = orgId if orgId else QtGui.qApp.currentOrgId()
        self.personSpecialityId = forceRef(db.translate('Person', 'id', self.personId, 'speciality_id'))
        self.cmbSetPerson       = CFakeEventEditor.CFakeCmbSetPerson(self)

        self.contractId = forceRef(self._record.value('contract_id'))
        if self.contractId:
            self.eventFinanceId = forceRef(db.translate('Contract', 'id', self.contractId, 'finance_id'))
        else:
            self.eventFinanceId = getEventFinanceId(self.eventTypeId)

        self.clientId        = forceRef(self._record.value('client_id'))
        self.clientInfo      = getClientInfo(self.clientId)

        clientKLADRCode = ''
        self.isTerritorialBelonging = isEventTerritorialBelonging(self.eventTypeId)
        if self.isTerritorialBelonging == CFakeEventEditor.ctLocAddress:
            clientKLADRCode = self.clientInfo.locAddressInfo.KLADRCode
        elif self.isTerritorialBelonging == CFakeEventEditor.ctInsurer:
            financeCode = forceString(QtGui.qApp.db.translate('rbFinance', 'id', self.eventFinanceId, 'code')) if self.eventFinanceId else u''
            if financeCode == 3:
                record = self.clientInfo.voluntaryPolicyRecord
                if record:
                    clientKLADRCode = forceString(record.value('area'))
            else:
                record = self.clientInfo.compulsoryPolicyRecord
                if record:
                    clientKLADRCode = forceString(record.value('area'))
        if not clientKLADRCode:
            regAddressInfo = self.clientInfo.get('regAddressInfo')
            if regAddressInfo:
                clientKLADRCode = regAddressInfo.KLADRCode

        if KLADRMatch(clientKLADRCode, QtGui.qApp.defaultKLADR()):
            self.clientType  = CFakeEventEditor.ctLocal
        elif KLADRMatch(clientKLADRCode, QtGui.qApp.provinceKLADR()):
            self.clientType  = CFakeEventEditor.ctProvince
        else:
            self.clientType  = CFakeEventEditor.ctOther
        self.clientSex       = self.clientInfo.sexCode
        self.clientBirthDate = self.clientInfo.birthDate
        self.clientAge       = calcAgeTuple(self.clientBirthDate, self.eventDate)

        workRecord           = getClientWork(self.clientId)
        self.clientWorkOrgId = forceRef(workRecord.value('org_id')) if workRecord else None

        self.clientPolicyInfoList = []
        policyRecord = self.clientInfo.compulsoryPolicyRecord
        if policyRecord:
            self.clientPolicyInfoList.append(self.getPolicyInfo(policyRecord))
        policyRecord = self.clientInfo.voluntaryPolicyRecord
        if policyRecord:
            self.clientPolicyInfoList.append(self.getPolicyInfo(policyRecord))
        self.personCache = {}
        self.contractTariffCache = CContractTariffCache()


    def _confirmLock(self, message):
        return QtGui.QMessageBox.critical(self._parent,
                                          u'Ограничение совместного доступа к данным',
                                          message,
                                          QtGui.QMessageBox.Retry|QtGui.QMessageBox.Cancel,
                                          QtGui.QMessageBox.Retry
                                         ) == QtGui.QMessageBox.Retry


    def onActionChanged(self, actionsSummaryRow):
        pass


    def getPolicyInfo(self, policyRecord):
        if policyRecord:
            insurerId = forceRef(policyRecord.value('insurer_id'))
            policyTypeId = forceRef(policyRecord.value('policyType_id'))
        else:
            insurerId = None
            policyTypeId = None
        return insurerId, policyTypeId


    def getActionFinanceId(self, actionRecord):
        finance = getEventActionFinance(self.eventTypeId)
        if finance == 1:
            return self.eventFinanceId
        elif finance == 2:
            personId = forceRef(actionRecord.value('setPerson_id'))
            return self.getPersonFinanceId(personId) if personId else self.personFinanceId
        elif finance == 3:
            personId = forceRef(actionRecord.value('person_id'))
            return self.getPersonFinanceId(personId) if personId else self.personFinanceId
        else:
            return None


    def getPersonSSF(self, personId):
        key = personId, self.clientType
        result = self.personCache.get(key, None)
        if not result:
            record = QtGui.qApp.db.getRecord('Person LEFT JOIN rbSpeciality ON rbSpeciality.id = Person.speciality_id',
                                             'speciality_id, service_id, provinceService_id, otherService_id, finance_id, tariffCategory_id',
                                             personId
                                             )
            if record:
                specialityId      = forceRef(record.value('speciality_id'))
                serviceId         = forceRef(record.value('service_id'))
                provinceServiceId = forceRef(record.value('provinceService_id'))
                otherServiceId    = forceRef(record.value('otherService_id'))
                financeId         = forceRef(record.value('finance_id'))
                tariffCategoryId  = forceRef(record.value('tariffCategory_id'))
                if self.clientType == CFakeEventEditor.ctOther and otherServiceId:
                    serviceId = otherServiceId
                elif self.clientType == CFakeEventEditor.ctProvince and provinceServiceId:
                    serviceId = provinceServiceId
                result = (specialityId, serviceId, financeId, tariffCategoryId)

            else:
                result = (None, None, None, None)
            self.personCache[key] = result
        return result


    def getDefaultMKBValue(self, defaultMKB, setPersonId):
        return '', ''


    def getSuggestedPersonId(self):
        return QtGui.qApp.userId if QtGui.qApp.userSpecialityId else self.personId


    def getUet(self, actionTypeId, personId, financeId, contractId):
        if not contractId:
            contractId = self.contractId
            financeId = self.eventFinanceId
        if contractId and actionTypeId:
            serviceIdList = self.getActionTypeServiceIdList(actionTypeId, financeId)
            tariffDescr = self.contractTariffCache.getTariffDescr(contractId, self)
            tariffCategoryId = self.getPersonTariffCategoryId(personId)
            uet = CContractTariffCache.getUet(tariffDescr.actionTariffMap, serviceIdList, tariffCategoryId)
            return uet
        return 0


    def getPersonFinanceId(self, personId):
        return self.getPersonSSF(personId)[2]


    def getPersonTariffCategoryId(self, personId):
        return self.getPersonSSF(personId)[3]


    def getEventId(self):
        return self._id


    def getEventTypeId(self):
        return self.eventTypeId


    def recordAcceptable(self, record):
        return recordAcceptable(self.clientSex, self.clientAge, record)

