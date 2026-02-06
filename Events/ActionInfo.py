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

from PyQt4 import QtGui
from PyQt4.QtCore import QString

from library.Identification import getIdentificationInfo, getIdentification
from library.exception        import CException
from library.PrintInfo import (
    CInfo,
    CTemplatableInfoMixin,
    CInfoList,
    CInfoProxyList,
    CDateTimeInfo, CRBInfo, CDateInfo, _identification,
)
from library.Utils            import (
                                      forceBool,
                                      forceDate,
                                      forceDateTime,
                                      forceDouble,
                                      forceInt,
                                      forceRef,
                                      forceString,
                                      forceStringEx,
                                      forceTime,
                                     )
from library.ESKLP.SmnnInfo   import CSmnnInfo
from Events.Action import CActionTypeCache, CAction, CActionType
from ActionProperty           import CActionProperty, CActionPropertyType
from Events.ContractTariffCache import CContractTariffCache
from Events.MapActionTypeToServiceIdList import CMapActionTypeIdToServiceIdList
from Events.MKBInfo           import CMKBInfo, CMorphologyMKBInfo
from RefBooks.Post.Info       import CPostInfo
from RefBooks.Service.Info    import CServiceInfo
from Events.Utils import CCSGInfo
from Orgs.PersonInfo          import CPersonInfo
from Orgs.Utils               import COrgInfo, COrgStructureInfo, getActionTypeOrgStructureIdList
from RefBooks.Test.Info       import CTestInfo
from RefBooks.Unit.Info       import CUnitInfo
from RefBooks.Finance.Info    import CFinanceInfo

from Stock.StockMotionInfo    import CStockMotionInfo, CStockMotionItemInfo, CNomenclatureInfo, CLFFormInfo, CNomenclatureActiveSubstanceInfo
from TissueJournal.TissueInfo import CTakenTissueJournalInfo, CTissueTypeInfo, CContainerTypeInfo
#from library.Pacs.RestToolbox  import getRequest
from Registry.Utils import CQuotaTypeInfo, CClientVaccinationInfo, CRBInfectionInfo


class CActionTypeTissueTypeInfoList(CInfoList):
    def __init__(self, context, actionTypeId):
        CInfoList.__init__(self, context)
        self._actionTypeId = actionTypeId

    def _load(self):
        if self._actionTypeId:
            self.idList = QtGui.qApp.db.getIdList('ActionType_TissueType', 'id', 'master_id=%d'%self._actionTypeId)
            self._items = [ self.getInstance(CActionTypeTissueTypeInfo, id) for id in self.idList ]
        else:
            self.idList = []
            self._items = []
        return True

class CActionTypeTissueTypeInfo(CInfo):
    def __init__(self, context, id):
        CInfo.__init__(self, context)
        self.id = id


    def _load(self):
        db = QtGui.qApp.db
        table = db.table('ActionType_TissueType')
        record = db.getRecordEx(table, '*', [table['id'].eq(self.id)])
        if record:
            self.initByRecord(record)
            return True
        else:
            self.initByRecord(db.dummyRecord())
            return False


    def initByRecord(self, record):
        self._amount = forceInt(record.value('amount'))
        self._type = self.getInstance(CTissueTypeInfo, forceRef(record.value('tissueType_id')))
        self._container = self.getInstance(CContainerTypeInfo, forceRef(record.value('containerType_id')))

    amount       = property(lambda self: self.load()._amount)
    type        = property(lambda self: self.load()._type)
    container        = property(lambda self: self.load()._container)


#class CActionTypeInfo(CInfo, CIdentificationInfoMixin):
class CActionTypeInfo(CInfo):
    def __init__(self, context, actionType):
        self.tableName = 'ActionType'
        CInfo.__init__(self, context)
        self._mapUrnToIdentifier = {}
        self._mapUrnToIdentifierInfo = {}
        self._mapCodeToIdentifierInfo = {}
        self._actionType = actionType
        self._loaded = True
        self._ok = True
        self._tissueTypeList = self.getInstance(CActionTypeTissueTypeInfoList, actionType.id if actionType else None)
        self._quotaTypeList = self.getInstance(CActionTypeQuotaTypeInfoList, actionType.id if actionType else None)


    def isServiceTypeProcedure(self):
        return self._actionType.isServiceTypeProcedure() if self._actionType else None


    def isServiceTypeResearch(self):
        return self._actionType.isServiceTypeResearch() if self._actionType else None


    def hasJobTicketPropertyType(self):
        return self._actionType.hasJobTicketPropertyType() if self._actionType else None


    def _getGroup(self):
        groupId = self._actionType.groupId if self._actionType else None
        actionType = CActionTypeCache.getById(groupId) if groupId else None
        return self.getInstance(CActionTypeInfo, actionType)


    def __nonzero__(self):
        return bool(self._actionType)


    def __cmp__(self, other):
        selfKey = self._actionType.id if self._actionType else None
        otherKey = other._actionType.id if other._actionType else None if isinstance(other, CActionTypeInfo) else None
        return cmp(selfKey, otherKey)


    def getOrgStructures(self, includeInheritance=False):
        idList = getActionTypeOrgStructureIdList(self._actionType.id, includeInheritance) if self._actionType else []
        return [self.getInstance(COrgStructureInfo, id) for id in idList]

    def identify(self, urn):
        if self._actionType.id:
            if urn in self._mapUrnToIdentifier:
                return self._mapUrnToIdentifier[urn]
            else:
                result = getIdentification(self.tableName, self._actionType.id, urn, False)
                self._mapUrnToIdentifier[urn] = result
                return result
        else:
            return None

    def identifyInfoByUrn(self, urn):
        if self._actionType.id:
            if urn in self._mapUrnToIdentifierInfo:
                return self._mapUrnToIdentifierInfo[urn]
            else:
                code, name, urn, version, value, note, checkDate, value_spr, name_spr,record = getIdentificationInfo(self.tableName, self._actionType.id, urn)
                result = _identification(code, name, urn, version, value, note, CDateInfo(checkDate),value_spr, name_spr,record)
                self._mapUrnToIdentifierInfo[urn] = result
                return result
        else:
            return _identification(None, None, None, None, None, None, None, None, None, None)

    def identifyInfoByCode(self, code):
        if self._actionType.id:
            if code in self._mapCodeToIdentifierInfo:
                return self._mapCodeToIdentifierInfo[code]
            else:
                code, name, urn, version, value, note, checkDate,value_spr, name_spr,record = getIdentificationInfo(self.tableName, self._actionType.id, code, byCode=True)
                result = _identification(code, name, urn, version, value, note, CDateInfo(checkDate),value_spr, name_spr,record)
                self._mapCodeToIdentifierInfo[code] = result
                return result
        else:
            return _identification(None, None, None, None, None, None, None,None, None, None)

    group   = property(_getGroup)
    id      = property(lambda self: self._actionType.id if self._actionType else None)
    class_  = property(lambda self: self._actionType.class_ if self._actionType else None)
    code    = property(lambda self: self._actionType.code  if self._actionType else None)
    flatCode= property(lambda self: self._actionType.flatCode if self._actionType else None)
    name    = property(lambda self: self._actionType.name  if self._actionType else None)
    title   = property(lambda self: self._actionType.title if self._actionType else None)
    showTime= property(lambda self: self._actionType.showTime if self._actionType else None)
    isMes  = property(lambda self: self._actionType.isMes if self._actionType else None)
    nomenclativeService = property(lambda self: self.getInstance(CServiceInfo, self._actionType.nomenclativeServiceId if self._actionType else None))
    isHtml  = property(lambda self: self._actionType.isHtml() if self._actionType else None)
    isImage = property(lambda self: self._actionType.isImage() if self._actionType else None)
    hasAssistant = property(lambda self: self._actionType.hasAssistant if self._actionType else None)
    orgStructures = property(getOrgStructures)
    serviceType = property(lambda self: self._actionType.serviceType if self._actionType else None)
    tissueTypeList = property(lambda self: self._tissueTypeList)
    ticketDuration = property(lambda self: self._actionType.ticketDuration if self._actionType else None)
    quotaType = property(lambda self: self._quotaTypeList)


class CActionTypeQuotaTypeInfoList(CInfoList):
    def __init__(self, context, actionTypeId):
        CInfoList.__init__(self, context)
        self._actionTypeId = actionTypeId

    def _load(self):
        if self._actionTypeId:
            self.idList = QtGui.qApp.db.getIdList('ActionType_QuotaType', 'id', 'master_id=%d'%self._actionTypeId)
            self._items = [ self.getInstance(CActionTypeQuotaTypeInfo, id) for id in self.idList ]
        else:
            self.idList = []
            self._items = []
        return True

class CActionExport(CInfo):
    def __init__(self, context, action):
        CInfo.__init__(self, context)
        self.action = action
        self._externalId = ''
        self._note = ''
        self._alter_externalId = ''
        self._note_Person = ''


    def _load(self):
        db = QtGui.qApp.db
        record = db.getRecordEx('Action_Export', '*', 'master_id=%d'%self.action)
        if record:
            self._externalId = forceString(record.value('externalId'))
            self._note = forceString(record.value('note'))
            self._alter_externalId = forceString(record.value('alter_externalId'))
            self._note_Person = forceString(record.value('note_Person'))
            return True
        else:
            return False

    externalId = property(lambda self: self.load()._externalId)
    note = property(lambda self: self.load()._note)
    alter_externalId = property(lambda self: self.load()._alter_externalId)
    note_Person = property(lambda self: self.load()._note_Person)

class CActionTypeQuotaTypeInfo(CInfo):
    def __init__(self, context, id):
        CInfo.__init__(self, context)
        self.id = id
    

    def _load(self):
        db = QtGui.qApp.db
        table = db.table('ActionType_QuotaType')
        record = db.getRecordEx(table, '*', [table['id'].eq(self.id)])
        if record:
            self._initByRecord(record)
            return True
        else:
            self._initByRecord(db.dummyRecord())
            return False


    def _initByRecord(self, record):
        self._quotaClass = forceInt(record.value('quotaClass'))
        self._quotaType = forceInt(record.value('quotaType_id'))
        self._financeId = forceString(record.value('finance_id'))


    quotaClass = property(lambda self: self.load()._quotaClass)
    quotaType = property(lambda self: self.getInstance(CQuotaTypeInfo, self.load()._quotaType))
    financeId = property(lambda self: self.load()._financeId)


class CActionTypeInfoList(CInfoList):
    def __init__(self, context):
        CInfoList.__init__(self, context)
        self._idList = []
        self._loaded = True
        self._ok = True


    def _setIdList(self, idList):
        self._idList = idList[:]
        self._items = [ self.getInstance(CActionTypeInfo, CActionTypeCache.getById(id))
                        for id in self._idList
                      ]


    idList = property(lambda self: self._idList, _setIdList)


class CCookedActionInfo(CActionTypeInfo, CTemplatableInfoMixin):
    def __init__(self, context, record, action, isExecutionPlan=False):
        CActionTypeInfo.__init__(self, context, action.getType())
        self._record = record
        self._action = action
        self._isExecutionPlan = isExecutionPlan
        self._eventInfo = None
# получается, что CActionInfo загружается при инициализации (зачем?)
# надо ли тут сделать отдельный метод load()???
        self._ok = self._load()
        self._loaded = True
        self._isDirty = False

        self._price = None
        self._servicesIdList = None
        self.currentPropertyIndex = -1

    def _load(self):
        if self._record:
            self._id = forceRef(self._record.value('id'))
            self._typeId = self._actionType.id
            self._classId = self._actionType.class_
            self._ticketDuration = self._actionType.ticketDuration
            self._expirationDate = self._actionType.expirationDate
            self._directionDate = CDateTimeInfo(forceDateTime(self._record.value('directionDate')))
            self._begDate = CDateTimeInfo(forceDateTime(self._record.value('begDate')))
            self._plannedEndDate = CDateTimeInfo(forceDateTime(self._record.value('plannedEndDate')))
            self._endDate = CDateTimeInfo(forceDateTime(self._record.value('endDate')))
            self._isUrgent = forceBool(self._record.value('isUrgent'))
            self._coordDate = CDateTimeInfo(forceDate(self._record.value('coordDate')))
            self._coordAgent = forceString(self._record.value('coordAgent'))
            self._coordInspector = forceString(self._record.value('coordInspector'))
            self._coordText = forceString(self._record.value('coordText'))
            self._status = forceInt(self._record.value('status'))
            self._office = forceString(self._record.value('office'))
            self._note = forceString(self._record.value('note'))
            self._export = self.getInstance(CActionExport, self._id)
            self._amount = forceDouble(self._record.value('amount'))
            self._quantity = forceInt(self._record.value('quantity'))
            self._uet = forceDouble(self._record.value('uet'))
            self._financeId = forceRef(self._record.value('finance_id'))
            self._setPerson = self.getInstance(CPersonInfo, forceRef(self._record.value('setPerson_id')))
            self._person = self.getInstance(CPersonInfo, forceRef(self._record.value('person_id')))
            self._assistant = self.getInstance(CPersonInfo, forceRef(self._record.value('assistant_id')) if self.hasAssistant else None)
            self._expose = forceBool(self._record.value('expose'))
            self._account = forceBool(self._record.value('account'))
            self._MKB = self.getInstance(CMKBInfo, forceString(self._record.value('MKB')))
            self._exSubclassMKB = forceString(self._record.value('exSubclassMKB'))
            self._morphologyMKB = self.getInstance(CMorphologyMKBInfo, forceString(self._record.value('morphologyMKB')))
            self._takenTissueJournal = self.getInstance(CTakenTissueJournalInfo, forceRef(self._record.value('takenTissueJournal_id')))
            self._duration = forceInt(self._record.value('duration'))
            self._periodicity = forceInt(self._record.value('periodicity'))
            self._aliquoticity = forceInt(self._record.value('aliquoticity'))
            self._payStatus = forceInt(self._record.value('payStatus'))
            self._prescriptionId = forceInt(self._record.value('prescription_id'))
            self._csg = self.getInstance(CCSGInfo, forceInt(self._record.value('EventCSG_id')))
            self._prevAction = self.getInstance(CActionInfo, forceInt(self._record.value('prevAction_id')))
            self._createDatetime = CDateTimeInfo(forceDateTime(self._record.value('createDatetime')))
            self._createPerson = self.getInstance(CPersonInfo, forceRef(self._record.value('createPerson_id')))
            self._modifyDatetime = CDateTimeInfo(forceDateTime(self._record.value('modifyDatetime')))
            self._modifyPerson = self.getInstance(CPersonInfo, forceRef(self._record.value('modifyPerson_id')))
            self._orgStructure = self.getInstance(COrgStructureInfo, forceRef(self._record.value('orgStructure_id')))
            self._specification = self.getInstance(CActionSpecificationInfo, forceRef(self._record.value('actionSpecification_id')))
            self._additional = forceBool(self._record.value('additional'))
            self._actionTypeGroup = self.getInstance(CActionTypeGroupInfo, forceRef(self._record.value('actionTypeGroup_id')))
            if self._isExecutionPlan:
                self._executionPlanItemsToAction = self.getInstance(CExecutionPlanItemsToActionInfoList, forceRef(self._record.value('id')))
            else:
                self._executionPlanItemsToAction = self.getInstance(CExecutionPlanItemsToActionInfoList, None)
            self._masterId = forceRef(self._record.value('master_id'))
            return True
        else:
            self._id = None
            self._typeId = None
            self._classId = None
            self._ticketDuration = None
            self._expirationDate = None
            self._directionDate = CDateTimeInfo(None)
            self._begDate = CDateTimeInfo(None)
            self._plannedEndDate = CDateTimeInfo(None)
            self._endDate = CDateTimeInfo(None)
            self._isUrgent = False
            self._coordDate = CDateTimeInfo(None)
            self._coordAgent = ''
            self._coordInspector = ''
            self._coordText = ''
            self._status = 0
            self._office = ''
            self._note = ''
            self._export = ''
            self._amount = 0.0
            self._quantity = 0
            self._uet = 0.0
            self._financeId = None
            self._setPerson = self.getInstance(CPersonInfo, None)
            self._person = self.getInstance(CPersonInfo, None)
            self._assistant = self.getInstance(CPersonInfo, None)
            self._expose = False
            self._account = False
            self._MKB = self.getInstance(CMKBInfo, None)
            self._exSubclassMKB = ''
            self._morphologyMKB = self.getInstance(CMorphologyMKBInfo, None)
            self._takenTissueJournal = self.getInstance(CTakenTissueJournalInfo, None)
            self._payStatus = 0
            self._prescriptionId = None
            self._csg = self.getInstance(CCSGInfo, None)
            self._prevAction = self.getInstance(CActionInfo, None)
            self._createDatetime = CDateTimeInfo(None)
            self._createPerson = self.getInstance(CPersonInfo, None)
            self._modifyDatetime = CDateTimeInfo(None)
            self._modifyPerson = self.getInstance(CPersonInfo, None)
            self._orgStructure = self.getInstance(COrgStructureInfo, None)
            self._specification = self.getInstance(CActionSpecificationInfo, None)
            self._additional = False
            self._actionTypeGroup = self.getInstance(CActionTypeGroupInfo, None)
            self._executionPlanItemsToAction = self.getInstance(CExecutionPlanItemsToActionInfoList, None)
            self._masterId = None
            return False


    def getPrintTemplateContext(self):
        return self._action.getType().context if self._action.getType() else None


    def getEventInfo(self, infoClass=None):
        if not self._eventInfo:
            from Events.EventInfo import CEventInfo
            eventId = forceRef(self._record.value('event_id')) if self._record else None
            self._eventInfo = self.getInstance(infoClass if infoClass else CEventInfo, eventId)
        return self._eventInfo


    def getFinanceInfo(self):
        financeId = forceRef(self._record.value('finance_id')) if self._record else None
        if financeId:
            return self.getInstance(CFinanceInfo, financeId)
        else:
            return self.getEventInfo().finance


    def getContractInfo(self):
        from Events.EventInfo import CContractInfo
        contractId = forceRef(self._record.value('contract_id')) if self._record else None
        if contractId:
            return self.getInstance(CContractInfo, contractId)
        else:
            return self.getEventInfo().contract


    def _getTariffDescr(self):
        event = self.getEventInfo()
        return event.getTariffDescrEx(self.getContractInfo().id)


    def _getServicesIdList(self):
        if self._servicesIdList is None:
            if not hasattr(self.context, 'mapActionTypeIdToServiceIdList'):
                self.context.mapActionTypeIdToServiceIdList = CMapActionTypeIdToServiceIdList()
            actionTypeId = self._actionType.id
            financeId = self.getFinanceInfo().id
            self._servicesIdList = self.context.mapActionTypeIdToServiceIdList.getActionTypeServiceIdList(actionTypeId, financeId)
        return self._servicesIdList


    def getServices(self):
        return [ self.getInstance(CServiceInfo, serviceId)
                 for serviceId in self._getServicesIdList()
               ]


    def getService(self):
        servicesIdList = self._getServicesIdList()
        serviceId = servicesIdList[0] if servicesIdList else None
        return self.getInstance(CServiceInfo, serviceId)


    def getPrice(self):
        if self._price is None:
            tariffDescr = self._getTariffDescr()
            tariffMap = tariffDescr.actionTariffMap
            tariffCategoryId = self.person.tariffCategory.id
            self._price = CContractTariffCache.getPrice(tariffMap, self._getServicesIdList(), tariffCategoryId)
        return self._price


    def getServicePrice(self, serviceId): # алгоритм взят из self.getPrice()
        tariffDescr = self._getTariffDescr()
        tariffMap = tariffDescr.actionTariffMap
        tariffCategoryId = self.person.tariffCategory.id
        return CContractTariffCache.getPrice(tariffMap, [serviceId, ], tariffCategoryId)


    def getOrgInfo(self):
        orgId = forceRef(self._record.value('org_id')) if self._record else None
        if not orgId:
            orgId = self._actionType.defaultOrgId
        return self.getInstance(COrgInfo, orgId)


    def getStockMotionInfo(self):
        result = self.getInstance(CStockMotionInfo, None)
        stockMotionRecord = self._action.getStockMotionRecord()
        if stockMotionRecord:
            result.setRecord(stockMotionRecord)
            result._items = [self.getInstance(CStockMotionItemInfo, None).setRecord(itemRecord).setOkLoaded() for itemRecord in self._action.getStockMotionItemList()]
        return result


    def getExecutionPlanInfo(self):
        if not self._action.getType().isNomenclatureExpense or not self._isExecutionPlan:
            return self.getInstance(CExecutionPlanInfo, None)
        executionPlan = self._action.getExecutionPlan()
        if executionPlan:
            executionPlanRecord = executionPlan.getRecord()
            _executionPlan = self.getInstance(CExecutionPlanInfo, None)
            _executionPlan.setRecord(executionPlanRecord)
            _executionPlan.setOkLoaded()
            return _executionPlan
        return self.getInstance(CExecutionPlanInfo, None)


    def getExecutionPlanItemsInfo(self):
        if not self._action.getType().isNomenclatureExpense or not self._isExecutionPlan:
            return [self.getInstance(CExecutionPlanItemInfo, None)]
        executionPlan = self._action.getExecutionPlan()
        if executionPlan and executionPlan.items:
            return [self.getInstance(CExecutionPlanItemInfo, None, i).setRecord(item.getRecord(), item.nomenclature).setOkLoaded() for i, item in enumerate(executionPlan.items)]
        return [self.getInstance(CExecutionPlanItemInfo, None)]


    def getNomenclaturePrice(self, propertyName):
        nomenclatureId = self[propertyName].value.id
        nomenclatureItem = self.getStockMotionInfo().getNomenclatureItem(nomenclatureId)
        if nomenclatureItem:
            return nomenclatureItem._sum
        return None


    def getData(self):
        itemId = forceRef(self._record.value('id')) if self._record else None
        eventInfo = self.getEventInfo()
        eventActions = eventInfo.actions
        eventActions._idList = [itemId]
        eventActions._items  = [self]
        eventActions._loaded = True

        return { 'event'  : eventInfo,
                 'action' : self,
                 'client' : eventInfo.client,
                 'actions': eventActions,
                 'currentActionIndex': 0,
                 'tempInvalid': None
               }


    def setCurrentPropertyIndex(self, currentPropertyIndex):
        self.currentPropertyIndex = currentPropertyIndex


    id = property(lambda self: self.load()._id)
    typeId = property(lambda self: self.load()._typeId)
    classId = property(lambda self: self.load()._classId)
    ticketDuration = property(lambda self: self.load()._ticketDuration)
    expirationDate = property(lambda self: self.load()._expirationDate)
    event = property(getEventInfo)
    directionDate = property(lambda self: self.load()._directionDate)
    begDate = property(lambda self: self.load()._begDate)
    plannedEndDate = property(lambda self: self.load()._plannedEndDate)
    endDate = property(lambda self: self.load()._endDate)
    isUrgent = property(lambda self: self.load()._isUrgent)
    coordDate = property(lambda self: self.load()._coordDate)
    coordAgent = property(lambda self: self.load()._coordAgent)
    coordInspector = property(lambda self: self.load()._coordInspector)
    coordText = property(lambda self: self.load()._coordText)
    status = property(lambda self: self.load()._status)
    office = property(lambda self: self.load()._office)
    note = property(lambda self: self.load()._note)
    export = property(lambda self: self.load()._export)
    amount = property(lambda self: self.load()._amount)
    quantity = property(lambda self: self.load()._quantity)
    uet = property(lambda self: self.load()._uet)
    setPerson = property(lambda self: self.load()._setPerson)
    person = property(lambda self: self.load()._person)
    assistant = property(lambda self: self.load()._assistant)
    expose = property(lambda self: self.load()._expose)
    account = property(lambda self: self.load()._account)
    MKB = property(lambda self: self.load()._MKB)
    exSubclassMKB = property(lambda self: self.load()._exSubclassMKB)
    morphologyMKB = property(lambda self: self.load()._morphologyMKB)
    duration = property(lambda self: self.load()._duration)
    periodicity = property(lambda self: self.load()._periodicity)
    aliquoticity = property(lambda self: self.load()._aliquoticity)
    services = property(getServices)
    service = property(getService) ### kill it!
    price = property(getPrice)
    contract = property(getContractInfo)
    finance = property(getFinanceInfo)
    takenTissueJournal = property(lambda self: self.load()._takenTissueJournal)
    stockMotion = property(getStockMotionInfo)
    organisation = property(getOrgInfo)
    payStatus = property(lambda self: self.load()._payStatus)
    prescriptionId = property(lambda self: self.load()._prescriptionId)
    csg = property(lambda self: self.load()._csg)
    pacs = property(lambda self: self.load()._pacs)
    isDirty = property(lambda self: self._isDirty)
    prevAction = property(lambda self: self._prevAction)
    createDatetime = property(lambda self: self._createDatetime)
    createPerson = property(lambda self: self._createPerson)
    modifyDatetime = property(lambda self: self._modifyDatetime)
    modifyPerson = property(lambda self: self._modifyPerson)
    orgStructure = property(lambda self: self.load()._orgStructure)
    specification = property(lambda self: self.load()._specification)
    additional = property(lambda self: self.load()._additional)
    masterId = property(lambda self: self.load()._masterId)
    actionTypeGroup = property(lambda self: self.load()._actionTypeGroup)
    executionPlanItemsToAction = property(lambda self: self.load()._executionPlanItemsToAction)
    executionPlan = property(lambda self: self.load()._executionPlan)
    executionPlanItems = property(lambda self: self.load()._executionPlanItems)


    def getPropertyByShortName(self, key):
        if isinstance(key, (basestring, QString)):
            try:
                return self.getInstance(CPropertyInfo, self._action.getPropertyByShortName(unicode(key)))
            except KeyError:
                actionType = self._action.getType()
                raise CException(u'Действие типа "%s" не имеет свойства с коротким наименованием"%s"' % (actionType.name, unicode(key)))


    def __len__(self):
        self.load()
        return len(self._action.getProperties())


    def __getitem__(self, key):
        if isinstance(key, (basestring, QString)):
            try:
                return self.getInstance(CPropertyInfo, self._action.getProperty(unicode(key)))
            except KeyError:
                actionType = self._action.getType()
                raise CException(u'Действие типа "%s" не имеет свойства "%s"' % (actionType.name, unicode(key)))
        if isinstance(key, (int, long)):
            try:
                return self.getInstance(CPropertyInfo, self._action.getPropertyByIndex(key))
            except IndexError:
                actionType = self._action.getType()
                raise CException(u'Действие типа "%s" не имеет свойства c индексом "%s"' % (actionType.name, unicode(key)))
        else:
            raise TypeError, u'Action property subscription must be string or integer'


    def __iter__(self):
        for property in self._action.getProperties():
            yield self.getInstance(CPropertyInfo, property)


    def __contains__(self, key):
        if isinstance(key, (basestring, QString)):
            return unicode(key) in self._action.getPropertiesByName()
        if isinstance(key, (int, long)):
            return 0<=key<len(self._action.getPropertiesById())
        else:
            raise TypeError, u'Action property subscription must be string or integer'


class CActionInfo(CCookedActionInfo):
    def __init__(self, context, actionId, isExecutionPlan=False):
        action = CAction.getActionById(actionId)
        if action:
            CCookedActionInfo.__init__(self, context, action.getRecord() if action else None, action, isExecutionPlan=isExecutionPlan)


class CUnitInfo(CRBInfo):
    tableName = 'rbUnit'

    def _load(self):
        db = QtGui.qApp.db
        record = db.getRecord(self.tableName, '*', self.id) if self.id else None
        if record:
            self._code = forceString(record.value('code'))
            self._name = forceString(record.value('name'))
            self._latinName = forceString(record.value('latinName'))
            self._federalCode = forceString(record.value('federalCode'))
            self._initByRecord(record)
            return True
        else:
            self._code = ''
            self._name = ''
            self._latinName = ''
            self._federalCode = ''
            self._initByNull()
            return False

    code = property(lambda self: self.load()._code)
    name = property(lambda self: self.load()._name)
    latinName = property(lambda self: self.load()._latinName)
    federalCode = property(lambda self: self.load()._federalCode)


class CPropertyInfo(CInfo):
    def __init__(self, context, property):
        CInfo.__init__(self, context)
        self._property = property
        self._loaded = True
        self._ok = True

    value = property(lambda self: self._property.getInfo(self.context))
    name  = property(lambda self: self._property._type.name)
    age  = property(lambda self: self._property._type.age[1] if self._property._type.age else '')
    shortName  = property(lambda self: self._property._type.shortName)
    comment = property(lambda self: self._property.getComment())
    descr = property(lambda self: self._property._type.descr)
    sectionCDA = property(lambda self: self._property._type.sectionCDA)
    valueDomain = property(lambda self: self._property._type.valueDomain)
    type = property(lambda self: self._property._type.typeName)
    id = property(lambda self: self._property.getId())
    unit  = property(lambda self: self.getInstance(CUnitInfo, self._property.getUnitId()))
    norm  = property(lambda self: self._property.getNorm())
    isAssigned = property(lambda self: self._property.isAssigned())
    evaluation = property(lambda self: self._property.getEvaluation())
    isHtml  = property(lambda self: self._property.isHtml())
    isImage = property(lambda self: self._property.isImage())
    test = property(lambda self: self.getInstance(CTestInfo, self._property._type.testId))
    sex = property(lambda self: self._property._type.sex)
    penalty = property(lambda self: self._property._type.penalty)
    visibleInJobTicket = property(lambda self: self._property._type.visibleInJobTicket)
    visibleInTableEditor = property(lambda self: self._property._type.visibleInTableEditor)
    inPlanOperatingDay = property(lambda self: self._property._type.inPlanOperatingDay)
    inMedicalDiagnosis = property(lambda self: self._property._type.inMedicalDiagnosis)
    inActionsSelectionTable = property(lambda self: self._property._type.inActionsSelectionTable)


    def __str__(self):
#        v = self._property.getValue()
#        return forceString(v) if v else ''
        return forceString(self.value)


class CActionInfoList(CInfoList):
    def __init__(self, context, eventId, isExecutionPlan=False):
        CInfoList.__init__(self, context)
        self.eventId = eventId
        self._idList = []
        self.isExecutionPlan = isExecutionPlan

    def _load(self):
        db = QtGui.qApp.db
        table = db.table('Action')
        self._idList = db.getIdList(table, 'id', [table['event_id'].eq(self.eventId), table['deleted'].eq(0)], 'id')
        self._items = [ self.getInstance(CActionInfo, id, self.isExecutionPlan) for id in self._idList ]
        return True


class CActionInfoProxyListEx(CInfoProxyList):
    def __init__(self, context, rawItems, eventInfo):
        CInfoProxyList.__init__(self, context)
        self._rawItems = rawItems
        self._items = [ None ]*len(self._rawItems)
        self._eventInfo = eventInfo


    def _getItemEx(self, key):
        record, action = self._rawItems[key]
        v = self.getInstance(CCookedActionInfo, record, action, isExecutionPlan=True)
        v._eventInfo = self._eventInfo
        return v


    def __getitem__(self, key):
        if isinstance(key, slice):
            for i in range(key.start or 0, key.stop or len(self._items), key.step or 1):
                val = self._items[i]
                if val is None:
                    self._items[i] = self._getItemEx(i)
        v = self._items[key]
        if v is None:
            v = self._getItemEx(key)
            self._items[key] = v
        return v


class CActionSelectedInfoProxyList(CInfoProxyList):
    def __init__(self, context, modelsItems, eventInfo):
        CInfoProxyList.__init__(self, context)
        self._rawItems = []
        for items in modelsItems:
            if items:
                self._rawItems.extend(items)
        self._items = [ None ]*len(self._rawItems)
        self._eventInfo = eventInfo

    def _getItemEx(self, key):
        record, action = self._rawItems[key]
        v = self.getInstance(CCookedActionInfo, record, action)
        v._eventInfo = self._eventInfo
        return v

    def __getitem__(self, key):
        if isinstance(key, slice):
            for i in range(key.start or 0, key.stop or len(self._items), key.step or 1):
                val = self._items[i]
                if val is None:
                    self._items[i] = self._getItemEx(i)
        v = self._items[key]
        if v is None:
            v = self._getItemEx(key)
            self._items[key] = v
        return v


class CActionInfoProxyList(CInfoProxyList):
    def __init__(self, context, models, eventInfo):
        CInfoProxyList.__init__(self, context)
        self._rawItems = []
        for model in models:
            self._rawItems.extend(model.items())
        self._items = [ None ]*len(self._rawItems)
        self._eventInfo = eventInfo

    def _getItemEx(self, key):
        record, action = self._rawItems[key]
        if not action:
            return None
        v = self.getInstance(CCookedActionInfo, record, action)
        v._eventInfo = self._eventInfo
        return v

    def __getitem__(self, key):
        if isinstance(key, slice):
            for i in range(key.start or 0, key.stop or len(self._items), key.step or 1):
                val = self._items[i]
                if val is None:
                    self._items[i] = self._getItemEx(i)
        v = self._items[key]
        if v is None:
            v = self._getItemEx(key)
            self._items[key] = v
        return v


class CLocActionInfoProxyList(CActionInfoProxyList):
    def __init__(self, context, models, eventInfo):
        CActionInfoProxyList.__init__(self, context)


# TODO: не должен ли этот класс наследоваться от CActionInfoProxyList???
class CLocActionInfoList(CInfoProxyList):
    def __init__(self, context, idList, clientSex=0, clientAge=0, type_ = CCookedActionInfo):
        CInfoProxyList.__init__(self, context)
        self.idList = idList
        self._items = [ None ]*len(self.idList)
        self.clientSex = clientSex
        self.clientAge = clientAge
        self._type = type_


    def __getitem__(self, key):
        v = self._items[key]
        if v is None:
            action = CAction.getActionById(self.idList[key])
            v = self.getInstance(self._type, action.getRecord(), action)
            self._items[key] = v
        return v


class CCookedNotActionInfo(CCookedActionInfo):
    def __init__(self, context, record, action):
        CCookedActionInfo.__init__(self, context, record, action)

    def getPrintTemplateContext(self):
        return None

    def getStockMotionInfo(self):
        return None

    def __len__(self):
        self.load()
        return len(self._items)


    def __getitem__(self, key):
        self.load()
        return self._items[key]


    def __iter__(self):
        self.load()
        return iter(self._items)


    def __contains__(self, key):
        return len(self._items)


class CPlanOperatingDayInfo(CCookedActionInfo):
    def __init__(self, context, record, action):
        if action:
            CCookedActionInfo.__init__(self, context, action.getRecord(), action)
        else:
            CCookedNotActionInfo.__init__(self, context, record, action)


class CPlanOperatingDayInfoList(CActionInfoProxyList):
    def __init__(self, context, models, eventInfo):
        CActionInfoProxyList.__init__(self, context, models, eventInfo)
        self._rawItems = []
        for model in models:
            self._rawItems.extend(model.items())
        self._items = [ None ]*len(self._rawItems)
        self._eventInfo = eventInfo

    def _getItemEx(self, key):
        record, action = self._rawItems[key]
        v = self.getInstance(CPlanOperatingDayInfo, record, action)
        v._eventInfo = self._eventInfo
        return v


class CMedicalDiagnosisInfo(CCookedActionInfo):
    def __init__(self, context, record, action):
        CCookedActionInfo.__init__(self, context, action.getRecord(), action)


class CMedicalDiagnosisInfoList(CActionInfoProxyList):
    def __init__(self, context, models, eventInfo):
        CActionInfoProxyList.__init__(self, context, models, eventInfo)
        self._rawItems = []
        for model in models:
            self._rawItems.extend(model.items())
        self._items = [ None ]*len(self._rawItems)
        self._eventInfo = eventInfo

    def _getItemEx(self, key):
        record, action = self._rawItems[key]
        v = self.getInstance(CMedicalDiagnosisInfo, record, action)
        v._eventInfo = self._eventInfo
        return v


class CActionInfoListEx(CInfoList):
    def __init__(self, context, actionIdList, isExecutionPlan=False):
        CInfoList.__init__(self, context)
        self._idList = actionIdList
        self.isExecutionPlan = isExecutionPlan

    def _load(self):
        self._items = [ self.getInstance(CActionInfo, id, self.isExecutionPlan) for id in self._idList ]
        return True

class CActionSpecificationInfo(CRBInfo):
    tableName = 'rbActionSpecification'


class CLocActionPropertyMedicamentInfoList(CInfoList):
    def __init__(self, context, records):
        CInfoList.__init__(self, context)
        self._records = records
        self._items = []


    def _load(self):
        if self._records:
            self._items = [self.getInstance(CLocActionPropertyMedicamentInfo, record) for record in self._records]
        else:
            self._items = []
        return True


class CLocActionPropertyMedicamentInfo(CInfo):
    def __init__(self, context, record):
        CInfo.__init__(self, context)
        self._record = record
        self._ok = self._load()
        self._loaded = True
        self._isDirty = False


    def _load(self):
        if self._record:
            self._id = forceRef(self._record.value('id'))
            self._createDatetime = CDateTimeInfo(forceDateTime(self._record.value('createDatetime')))
            self._createPerson = self.getInstance(CPersonInfo, forceRef(self._record.value('createPerson_id')))
            self._modifyDatetime = CDateTimeInfo(forceDateTime(self._record.value('modifyDatetime')))
            self._modifyPerson = self.getInstance(CPersonInfo, forceRef(self._record.value('modifyPerson_id')))
            self._deleted = forceInt(self._record.value('deleted'))
            self._idx = forceInt(self._record.value('idx'))
            self._masterAction = self.getInstance(CActionInfo, forceRef(self._record.value('master_id')))
            self._action = self.getInstance(CActionInfo, forceRef(self._record.value('action_id')))
            self._nomenclature = self.getInstance(CNomenclatureInfo, forceRef(self._record.value('actionPropertyNomenclature_id')))
            self._smnnUUID = forceStringEx(self._record.value('smnnUUID'))
            self._smnn = self.getInstance(CSmnnInfo, self._smnnUUID)
            self._duration = forceString(self._record.value('duration'))
            self._periodicity = forceString(self._record.value('periodicity'))
            self._aliquoticity = forceString(self._record.value('aliquoticity'))
            return True
        else:
            self._id = None
            self._createDatetime = CDateTimeInfo(None)
            self._createPerson = self.getInstance(CPersonInfo, None)
            self._modifyDatetime = CDateTimeInfo(None)
            self._modifyPerson = self.getInstance(CPersonInfo, None)
            self._deleted = 0
            self._idx = 0
            self._masterAction = self.getInstance(CActionInfo, None)
            self._action = self.getInstance(CActionInfo, None)
            self._nomenclature = self.getInstance(CNomenclatureInfo, None)
            self._smnnUUID = None
            self._smnn = self.getInstance(CSmnnInfo, None)
            self._duration = ''
            self._periodicity = ''
            self._aliquoticity = ''
            return False


    id = property(lambda self: self.load()._id)
    createDatetime = property(lambda self: self._createDatetime)
    createPerson = property(lambda self: self._createPerson)
    modifyDatetime = property(lambda self: self._modifyDatetime)
    modifyPerson = property(lambda self: self._modifyPerson)
    deleted = property(lambda self: self.load()._deleted)
    idx = property(lambda self: self.load()._idx)
    masterAction = property(lambda self: self.load()._masterAction)
    action = property(lambda self: self.load()._action)
    nomenclature = property(lambda self: self.load()._nomenclature)
    smnnUUID = property(lambda self: self.load()._smnnUUID)
    smnn = property(lambda self: self.load()._smnn)
    duration = property(lambda self: self.load()._duration)
    periodicity = property(lambda self: self.load()._periodicity)
    aliquoticity = property(lambda self: self.load()._aliquoticity)


class CLocActionPropertyActionsInfoList(CInfoList):
    def __init__(self, context, records):
        CInfoList.__init__(self, context)
        self._records = records
        self._items = []


    def _load(self):
        if self._records:
            self._items = [self.getInstance(CLocActionPropertyActionsInfo, record) for record in self._records]
        else:
            self._items = []
        return True


class CLocActionPropertyActionsInfo(CInfo):
    def __init__(self, context, record):
        CInfo.__init__(self, context)
        self._record = record
        self._ok = self._load()
        self._loaded = True
        self._isDirty = False


    def _load(self):
        if self._record:
            db = QtGui.qApp.db
            tableA = db.table('Action')
            tableAT = db.table('ActionType')
            tableAP = db.table('ActionProperty')
            tableAPT = db.table('ActionPropertyType')
            actionId = forceRef(self._record.value('action_id'))
            if actionId:
                actionType = None
                propertyIdList = []
                propertyList = []
                if hasattr(self._record, 'aboutMERProperties'):
                    propertyItems = self._record.aboutMERProperties.getItems()
                elif hasattr (self._record, 'aboutChildrenProperties'):
                    propertyItems = self._record.aboutChildrenProperties.getItems()
                for propertyItem in propertyItems:
                    propertyId = forceRef(propertyItem.value('actionProperty_id'))
                    if propertyId and propertyId not in propertyIdList:
                        propertyIdList.append(propertyId)
                if propertyIdList:
                    actionRecord = db.getRecordEx(tableA, [tableA['actionType_id']], [tableA['id'].eq(actionId), tableA['deleted'].eq(0)])
                    actionTypeId = forceRef(actionRecord.value('actionType_id')) if actionRecord else None
                    if actionTypeId:
                        actionTypeRecord = db.getRecordEx(tableAT, '*', [tableAT['id'].eq(actionTypeId), tableAT['deleted'].eq(0)])
                        actionType = CActionType(record=actionTypeRecord)
                    propsCond = [
                        tableAP['id'].inlist(propertyIdList),
                        tableAP['action_id'].eq(actionId),
                        tableAP['deleted'].eq(0),
                    ]
                    recordProps = db.getRecordList(tableAP, [tableAP['id'], tableAP['type_id']], propsCond)
                    for recordProp in recordProps:
                        propId = forceRef(recordProp.value('id'))
                        propTypeId = forceRef(recordProp.value('type_id'))
                        if propId and propTypeId:
                            propRecord = db.getRecord(tableAP, '*', propId)
                            propTypeRecord = db.getRecord(tableAPT, '*', propTypeId)
                            propType = CActionPropertyType(propTypeRecord)
                            prop = CActionProperty(actionType=actionType, record=propRecord, type=propType)
                            propertyList.append(prop)
                self._id = forceRef(self._record.value('id'))
                self._idx = forceInt(self._record.value('idx'))
                self._action = self.getInstance(CActionInfo, actionId)
                self._masterAction = self.getInstance(CActionInfo, forceRef(self._record.value('master_id')))
                self._properties = [self.getInstance(CPropertyInfo, p) for p in propertyList]
                self._additional = forceBool(self._record.value('additional'))
                return True
            else:
                self._id = None
                self._idx = 0
                self._action = self.getInstance(CActionInfo, None)
                self._masterAction = self.getInstance(CActionInfo, None)
                self._properties = []
                self._additional = False
                return False
        else:
            self._id = None
            self._idx = 0
            self._action = self.getInstance(CActionInfo, None)
            self._masterAction = self.getInstance(CActionInfo, None)
            self._properties = []
            self._additional = False
            return False


    id = property(lambda self: self.load()._id)
    idx = property(lambda self: self.load()._idx)
    action = property(lambda self: self.load()._action)
    masterAction = property(lambda self: self.load()._masterAction)
    properties = property(lambda self: self.load()._properties)
    additional = property(lambda self: self.load()._additional)




class CActionMEVaccinationInfo(CInfo):
    def __init__(self, context, id, record=None):
        CInfo.__init__(self, context)
        self.id = id
        self._record = record
        self._createDatetime = CDateTimeInfo()
        self._modifyDatetime = CDateTimeInfo()
        self._modifyPerson = self.getInstance(CPersonInfo, None)
        self._createPerson = self.getInstance(CPersonInfo, None)
        self._deleted = 0
        self._master = self.getInstance(CActionInfo, None)
        self._clientVaccination = self.getInstance(CClientVaccinationInfo, None)
        self._date = CDateInfo()
        self._infection = self.getInstance(CRBInfectionInfo, None)
        self._vaccinationType = ''


    def setRecord(self, record):
        if record:
            self.id = forceRef(record.value('id'))
            self._createDatetime = CDateTimeInfo(forceDateTime(record.value('createDatetime')))
            self._modifyDatetime = CDateTimeInfo(forceDateTime(record.value('modifyDatetime')))
            self._modifyPerson = self.getInstance(CPersonInfo, forceRef(record.value('modifyPerson_id')))
            self._createPerson = self.getInstance(CPersonInfo, forceRef(record.value('createPerson_id')))
            self._deleted = forceInt(record.value('deleted'))
            self._master = self.getInstance(CActionInfo, forceRef(record.value('master_id')))
            self._clientVaccination = self.getInstance(CClientVaccinationInfo, forceRef(record.value('clientVaccination_id')))
            self._date = CDateInfo(forceDate(record.value('date')))
            self._infection = self.getInstance(CRBInfectionInfo, forceRef(record.value('infection_id')))
            self._vaccinationType = forceString(record.value('vaccinationType'))
        else:
            self._createDatetime = CDateTimeInfo()
            self._modifyDatetime = CDateTimeInfo()
            self._modifyPerson = self.getInstance(CPersonInfo, None)
            self._createPerson = self.getInstance(CPersonInfo, None)
            self._deleted = 0
            self._master = self.getInstance(CActionInfo, None)
            self._clientVaccination = self.getInstance(CClientVaccinationInfo, None)
            self._date = CDateInfo()
            self._infection = self.getInstance(CRBInfectionInfo, None)
            self._vaccinationType = ''


    def _load(self):
        record = self._record
        if not record:
            db = QtGui.qApp.db
            table = db.table('Action_ME_Vaccination')
            record = db.getRecordEx(table, '*', [table['id'].eq(self.id), table['deleted'].eq(0)], 'id')
        if record:
            self.id = forceRef(record.value('id'))
            self._createDatetime = CDateTimeInfo(forceDateTime(record.value('createDatetime')))
            self._modifyDatetime = CDateTimeInfo(forceDateTime(record.value('modifyDatetime')))
            self._modifyPerson = self.getInstance(CPersonInfo, forceRef(record.value('modifyPerson_id')))
            self._createPerson = self.getInstance(CPersonInfo, forceRef(record.value('createPerson_id')))
            self._deleted = forceInt(record.value('deleted'))
            self._master = self.getInstance(CActionInfo, forceRef(record.value('master_id')))
            self._clientVaccination = self.getInstance(CClientVaccinationInfo, forceRef(record.value('clientVaccination_id')))
            self._date = CDateInfo(forceDate(record.value('date')))
            self._infection = self.getInstance(CRBInfectionInfo, forceRef(record.value('infection_id')))
            self._vaccinationType = forceString(record.value('vaccinationType'))
            return True
        else:
            self._createDatetime = CDateTimeInfo()
            self._modifyDatetime = CDateTimeInfo()
            self._modifyPerson = self.getInstance(CPersonInfo, None)
            self._createPerson = self.getInstance(CPersonInfo, None)
            self._deleted = 0
            self._master = self.getInstance(CActionInfo, None)
            self._clientVaccination = self.getInstance(CClientVaccinationInfo, None)
            self._date = CDateInfo()
            self._infection = self.getInstance(CRBInfectionInfo, None)
            self._vaccinationType = ''
            return False


    createDatetime = property(lambda self: self.load()._createDatetime)
    modifyDatetime = property(lambda self: self.load()._modifyDatetime)
    modifyPerson   = property(lambda self: self.load()._modifyPerson)
    createPerson   = property(lambda self: self.load()._createPerson)
    deleted        = property(lambda self: self.load()._deleted)
    master         = property(lambda self: self.load()._master)
    clientVaccination = property(lambda self: self.load()._clientVaccination)
    date           = property(lambda self: self.load()._date)
    infection      = property(lambda self: self.load()._infection)
    vaccinationType = property(lambda self: self.load()._vaccinationType)


class CActionMEVaccinationInfoList(CInfoList):
    def __init__(self, context, records):
        CInfoList.__init__(self, context)
        self._records = records
        self._items = []


    def _load(self):
        if self._records:
            self._items = [self.getInstance(CActionMEVaccinationInfo, forceRef(record.value('id')) if record else None, record) for record in self._records]
        else:
            self._items = []
        return True


class CActionMEVaccinationToActionInfoList(CInfoList):
    def __init__(self, context, actionId):
        CInfoList.__init__(self, context)
        self._actionId = actionId
        self._items = []


    def _load(self):
        vaccinationIdList = []
        if self._actionId:
            db = QtGui.qApp.db
            table = db.table('Action_ME_Vaccination')
            vaccinationIdList = db.getDistinctIdList(table, [table['id']], [table['master_id'].eq(self._actionId), table['deleted'].eq(0)])
        if vaccinationIdList:
            self._items = [self.getInstance(CActionMEVaccinationInfo, vaccinationId, None) for vaccinationId in vaccinationIdList]
        else:
            self._items = []
        return True


class CActionMEExaminationsInfo(CInfo):
    def __init__(self, context, id, record=None):
        CInfo.__init__(self, context)
        self.id = id
        self._record = record
        self._createDatetime = CDateTimeInfo()
        self._modifyDatetime = CDateTimeInfo()
        self._modifyPerson = self.getInstance(CPersonInfo, None)
        self._createPerson = self.getInstance(CPersonInfo, None)
        self._deleted = 0
        self._master = self.getInstance(CActionInfo, None)
        self._examination = self.getInstance(CActionInfo, None)
        self._date = CDateInfo()
        self._post = self.getInstance(CPostInfo, None)
        self._lastName = ''
        self._firstName = ''
        self._patrName = ''
        self._isComissioner = 0
        self._result = ''


    def setRecord(self, record):
        if record:
            self.id = forceRef(record.value('id'))
            self._createDatetime = CDateTimeInfo(forceDateTime(record.value('createDatetime')))
            self._modifyDatetime = CDateTimeInfo(forceDateTime(record.value('modifyDatetime')))
            self._modifyPerson = self.getInstance(CPersonInfo, forceRef(record.value('modifyPerson_id')))
            self._createPerson = self.getInstance(CPersonInfo, forceRef(record.value('createPerson_id')))
            self._deleted = forceInt(record.value('deleted'))
            self._master = self.getInstance(CActionInfo, forceRef(record.value('master_id')))
            self._examination = self.getInstance(CActionInfo, forceRef(record.value('examination_id')))
            self._date = CDateInfo(forceDate(record.value('date')))
            self._post = self.getInstance(CPostInfo, forceRef(record.value('post_id')))
            self._lastName = forceString(record.value('lastName'))
            self._firstName = forceString(record.value('firstName'))
            self._patrName = forceString(record.value('patrName'))
            self._isComissioner = forceInt(record.value('isComissioner'))
            self._result = forceString(record.value('result'))
        else:
            self._createDatetime = CDateTimeInfo()
            self._modifyDatetime = CDateTimeInfo()
            self._modifyPerson = self.getInstance(CPersonInfo, None)
            self._createPerson = self.getInstance(CPersonInfo, None)
            self._deleted = 0
            self._master = self.getInstance(CActionInfo, None)
            self._examination = self.getInstance(CActionInfo, None)
            self._date = CDateInfo()
            self._post = self.getInstance(CPostInfo, None)
            self._lastName = ''
            self._firstName = ''
            self._patrName = ''
            self._isComissioner = 0
            self._result = ''


    def _load(self):
        record = self._record
        if not record:
            db = QtGui.qApp.db
            table = db.table('Action_ME_Examinations')
            record = db.getRecordEx(table, '*', [table['id'].eq(self.id), table['deleted'].eq(0)], 'id')
        if record:
            self.id = forceRef(record.value('id'))
            self._createDatetime = CDateTimeInfo(forceDateTime(record.value('createDatetime')))
            self._modifyDatetime = CDateTimeInfo(forceDateTime(record.value('modifyDatetime')))
            self._modifyPerson = self.getInstance(CPersonInfo, forceRef(record.value('modifyPerson_id')))
            self._createPerson = self.getInstance(CPersonInfo, forceRef(record.value('createPerson_id')))
            self._deleted = forceInt(record.value('deleted'))
            self._master = self.getInstance(CActionInfo, forceRef(record.value('master_id')))
            self._examination = self.getInstance(CActionInfo, forceRef(record.value('examination_id')))
            self._date = CDateInfo(forceDate(record.value('date')))
            self._post = self.getInstance(CPostInfo, forceRef(record.value('post_id')))
            self._lastName = forceString(record.value('lastName'))
            self._firstName = forceString(record.value('firstName'))
            self._patrName = forceString(record.value('patrName'))
            self._isComissioner = forceInt(record.value('isComissioner'))
            self._result = forceString(record.value('result'))
            return True
        else:
            self._createDatetime = CDateTimeInfo()
            self._modifyDatetime = CDateTimeInfo()
            self._modifyPerson = self.getInstance(CPersonInfo, None)
            self._createPerson = self.getInstance(CPersonInfo, None)
            self._deleted = 0
            self._master = self.getInstance(CActionInfo, None)
            self._examination = self.getInstance(CActionInfo, None)
            self._date = CDateInfo()
            self._post = self.getInstance(CPostInfo, None)
            self._lastName = ''
            self._firstName = ''
            self._patrName = ''
            self._isComissioner = 0
            self._result = ''
            return False


    createDatetime = property(lambda self: self.load()._createDatetime)
    modifyDatetime = property(lambda self: self.load()._modifyDatetime)
    modifyPerson   = property(lambda self: self.load()._modifyPerson)
    createPerson   = property(lambda self: self.load()._createPerson)
    deleted        = property(lambda self: self.load()._deleted)
    master         = property(lambda self: self.load()._master)
    examination    = property(lambda self: self.load()._examination)
    date           = property(lambda self: self.load()._date)
    post           = property(lambda self: self.load()._post)
    lastName       = property(lambda self: self.load()._lastName)
    firstName      = property(lambda self: self.load()._firstName)
    patrName       = property(lambda self: self.load()._patrName)
    isComissioner  = property(lambda self: self.load()._isComissioner)
    result         = property(lambda self: self.load()._result)


class CActionMEExaminationsInfoList(CInfoList):
    def __init__(self, context, records):
        CInfoList.__init__(self, context)
        self._records = records
        self._items = []


    def _load(self):
        if self._records:
            self._items = [self.getInstance(CActionMEExaminationsInfo, forceRef(record.value('id')) if record else None, record) for record in self._records]
        else:
            self._items = []
        return True


class CActionMEExaminationsToActionInfoList(CInfoList):
    def __init__(self, context, actionId):
        CInfoList.__init__(self, context)
        self._actionId = actionId
        self._items = []


    def _load(self):
        examinationsIdList = []
        if self._actionId:
            db = QtGui.qApp.db
            table = db.table('Action_ME_Examinations')
            examinationsIdList = db.getDistinctIdList(table, [table['id']], [table['master_id'].eq(self._actionId), table['deleted'].eq(0)])
        if examinationsIdList:
            self._items = [self.getInstance(CActionMEExaminationsInfo, examinationsId, None) for examinationsId in examinationsIdList]
        else:
            self._items = []
        return True


class CActionMEResearchesInfo(CInfo):
    def __init__(self, context, id, record=None, findResearchType=0):
        CInfo.__init__(self, context)
        self.id = id
        self.findResearchType = findResearchType
        self._record = record
        #        self._loaded = True
        #        self._ok = True
        self._createDatetime = CDateTimeInfo()
        self._modifyDatetime = CDateTimeInfo()
        self._modifyPerson = self.getInstance(CPersonInfo, None)
        self._createPerson = self.getInstance(CPersonInfo, None)
        self._deleted = 0
        self._master = self.getInstance(CActionInfo, None)
        self._research = self.getInstance(CActionInfo, None)
        self._researchType = 0
        self._date = CDateInfo()
        self._serviceId = self.getInstance(CServiceInfo, None)
        self._titer = ''
        self._result = ''


    def setRecord(self, record):
        if record:
            self.id = forceRef(record.value('id'))
            self._createDatetime = CDateTimeInfo(forceDateTime(record.value('createDatetime')))
            self._modifyDatetime = CDateTimeInfo(forceDateTime(record.value('modifyDatetime')))
            self._modifyPerson = self.getInstance(CPersonInfo, forceRef(record.value('modifyPerson_id')))
            self._createPerson = self.getInstance(CPersonInfo, forceRef(record.value('createPerson_id')))
            self._deleted = forceInt(record.value('deleted'))
            self._master = self.getInstance(CActionInfo, forceRef(record.value('master_id')))
            self._research = self.getInstance(CActionInfo, forceRef(record.value('research_id')))
            self._researchType = forceInt(record.value('researchType'))
            self._date = CDateInfo(forceDate(record.value('date')))
            self._serviceId = self.getInstance(CServiceInfo, forceRef(record.value('service_id')))
            self._titer = forceString(record.value('titer'))
            self._result = forceString(record.value('result'))
        else:
            self._createDatetime = CDateTimeInfo()
            self._modifyDatetime = CDateTimeInfo()
            self._modifyPerson = self.getInstance(CPersonInfo, None)
            self._createPerson = self.getInstance(CPersonInfo, None)
            self._deleted = 0
            self._master = self.getInstance(CActionInfo, None)
            self._research = self.getInstance(CActionInfo, None)
            self._researchType = 0
            self._date = CDateInfo()
            self._serviceId = self.getInstance(CServiceInfo, None)
            self._titer = ''
            self._result = ''


    def _load(self):
        record = self._record
        if not record:
            db = QtGui.qApp.db
            table = db.table('Action_ME_Researches')
            cond = [table['id'].eq(self.id),
                    table['deleted'].eq(0)
                    ]
            if self.findResearchType > 0:
                cond.append(table['researchType'].eq(self.findResearchType))
            record = db.getRecordEx(table, '*', cond, 'id')
        if record:
            self.id = forceRef(record.value('id'))
            self._createDatetime = CDateTimeInfo(forceDateTime(record.value('createDatetime')))
            self._modifyDatetime = CDateTimeInfo(forceDateTime(record.value('modifyDatetime')))
            self._modifyPerson = self.getInstance(CPersonInfo, forceRef(record.value('modifyPerson_id')))
            self._createPerson = self.getInstance(CPersonInfo, forceRef(record.value('createPerson_id')))
            self._deleted = forceInt(record.value('deleted'))
            self._master = self.getInstance(CActionInfo, forceRef(record.value('master_id')))
            self._research = self.getInstance(CActionInfo, forceRef(record.value('research_id')))
            self._researchType = forceInt(record.value('researchType'))
            self._date = CDateInfo(forceDate(record.value('date')))
            self._serviceId = self.getInstance(CServiceInfo, forceRef(record.value('service_id')))
            self._titer = forceString(record.value('titer'))
            self._result = forceString(record.value('result'))
            return True
        else:
            self._createDatetime = CDateTimeInfo()
            self._modifyDatetime = CDateTimeInfo()
            self._modifyPerson = self.getInstance(CPersonInfo, None)
            self._createPerson = self.getInstance(CPersonInfo, None)
            self._deleted = 0
            self._master = self.getInstance(CActionInfo, None)
            self._research = self.getInstance(CActionInfo, None)
            self._researchType = 0
            self._date = CDateInfo()
            self._serviceId = self.getInstance(CServiceInfo, None)
            self._titer = ''
            self._result = ''
            return False


    createDatetime = property(lambda self: self.load()._createDatetime)
    modifyDatetime = property(lambda self: self.load()._modifyDatetime)
    modifyPerson   = property(lambda self: self.load()._modifyPerson)
    createPerson   = property(lambda self: self.load()._createPerson)
    deleted        = property(lambda self: self.load()._deleted)
    master         = property(lambda self: self.load()._master)
    research       = property(lambda self: self.load()._research)
    researchType   = property(lambda self: self.load()._researchType)
    date           = property(lambda self: self.load()._date)
    serviceId     = property(lambda self: self.load()._serviceId)
    titer          = property(lambda self: self.load()._titer)
    result         = property(lambda self: self.load()._result)


class CActionMEResearchesInfoList(CInfoList):
    def __init__(self, context, records, findResearchType=0):
        CInfoList.__init__(self, context)
        self._records = records
        self._findResearchType = findResearchType
        self._items = []


    def _load(self):
        if self._records:
            self._items = [self.getInstance(CActionMEResearchesInfo, forceRef(record.value('id') if record else None), record, self._findResearchType) for record in self._records]
        else:
            self._items = []
        return True


class CActionMEResearchesToActionInfoList(CInfoList):
    def __init__(self, context, actionId, findResearchType=0):
        CInfoList.__init__(self, context)
        self._actionId = actionId
        self._findResearchType = findResearchType
        self._items = []


    def _load(self):
        researchesIdList = []
        if self._actionId:
            db = QtGui.qApp.db
            table = db.table('Action_ME_Researches')
            researchesIdList = db.getDistinctIdList(table, [table['id']], [table['master_id'].eq(self._actionId), table['deleted'].eq(0)])
        if researchesIdList:
            self._items = [self.getInstance(CActionMEResearchesInfo, researchesId, None, self._findResearchType) for researchesId in researchesIdList]
        else:
            self._items = []
        return True
    

class CExecutionPlanInfo(CInfo):
    def __init__(self, context, id):
        CInfo.__init__(self, context)
        self.id            = id
        self._createDatetime = CDateTimeInfo()
        self._modifyDatetime = CDateTimeInfo()
        self._modifyPerson = self.getInstance(CPersonInfo, None)
        self._createPerson = self.getInstance(CPersonInfo, None)
        self._deleted      = 0
        self._type         = 0
        self._begDate      = CDateInfo()
        self._duration     = 0
        self._periodicity  = 0
        self._aliquoticity = 0
        self._quantity     = 0
        self._scheduleWeekendDays = 0
        self._note     = ''
        self._smnnUUID = ''
        self._smnn   = self.getInstance(CSmnnInfo, None)
        self._lfForm = self.getInstance(CLFFormInfo, None)
        self._items = self.getInstance(CExecutionPlanItemsInfoList, None)


    def setRecord(self, record):
        if record:
            self.id            = forceRef(record.value('id'))
            self._createDatetime = CDateTimeInfo(forceDateTime(record.value('createDatetime')))
            self._modifyDatetime = CDateTimeInfo(forceDateTime(record.value('modifyDatetime')))
            self._modifyPerson = self.getInstance(CPersonInfo, forceRef(record.value('modifyPerson_id')))
            self._createPerson = self.getInstance(CPersonInfo, forceRef(record.value('createPerson_id')))
            self._deleted      = forceInt(record.value('deleted'))
            self._type         = forceInt(record.value('type'))
            self._begDate      = CDateInfo(forceDate(record.value('begDate')))
            self._duration     = forceInt(record.value('duration'))
            self._periodicity  = forceInt(record.value('periodicity'))
            self._aliquoticity = forceInt(record.value('aliquoticity'))
            self._quantity     = forceInt(record.value('quantity'))
            self._scheduleWeekendDays = forceInt(record.value('scheduleWeekendDays'))
            self._note     = forceStringEx(record.value('note'))
            self._smnnUUID = forceStringEx(record.value('smnnUUID'))
            self._smnn   = self.getInstance(CSmnnInfo, self._smnnUUID)
            self._lfForm = self.getInstance(CLFFormInfo, forceRef(record.value('lfForm_id')))
            self._items = self.getInstance(CExecutionPlanItemsInfoList, self.id)
        else:
            self._createDatetime = CDateTimeInfo()
            self._modifyDatetime = CDateTimeInfo()
            self._modifyPerson = self.getInstance(CPersonInfo, None)
            self._createPerson = self.getInstance(CPersonInfo, None)
            self._deleted      = 0
            self._type         = 0
            self._begDate      = CDateInfo()
            self._duration     = 0
            self._periodicity  = 0
            self._aliquoticity = 0
            self._quantity     = 0
            self._scheduleWeekendDays = 0
            self._note     = ''
            self._smnnUUID = ''
            self._smnn   = self.getInstance(CSmnnInfo, None)
            self._lfForm = self.getInstance(CLFFormInfo, None)
            self._items = self.getInstance(CExecutionPlanItemsInfoList, None)


    def _load(self):
        db = QtGui.qApp.db
        table = db.table('ActionExecutionPlan')
        record = db.getRecordEx(table, '*', [table['id'].eq(self.id), table['deleted'].eq(0)], 'id')
        if record:
            self.id            = forceRef(record.value('id'))
            self._createDatetime = CDateTimeInfo(forceDateTime(record.value('createDatetime')))
            self._modifyDatetime = CDateTimeInfo(forceDateTime(record.value('modifyDatetime')))
            self._modifyPerson = self.getInstance(CPersonInfo, forceRef(record.value('modifyPerson_id')))
            self._createPerson = self.getInstance(CPersonInfo, forceRef(record.value('createPerson_id')))
            self._deleted      = forceInt(record.value('deleted'))
            self._type         = forceInt(record.value('type'))
            self._begDate      = CDateInfo(forceDate(record.value('begDate')))
            self._duration     = forceInt(record.value('duration'))
            self._periodicity  = forceInt(record.value('periodicity'))
            self._aliquoticity = forceInt(record.value('aliquoticity'))
            self._quantity     = forceInt(record.value('quantity'))
            self._scheduleWeekendDays = forceInt(record.value('scheduleWeekendDays'))
            self._note     = forceStringEx(record.value('note'))
            self._smnnUUID = forceStringEx(record.value('smnnUUID'))
            self._smnn   = self.getInstance(CSmnnInfo, self._smnnUUID)
            self._lfForm = self.getInstance(CLFFormInfo, forceRef(record.value('lfForm_id')))
            self._items = self.getInstance(CExecutionPlanItemsInfoList, self.id)
        else:
            self._createDatetime = CDateTimeInfo()
            self._modifyDatetime = CDateTimeInfo()
            self._modifyPerson = self.getInstance(CPersonInfo, None)
            self._createPerson = self.getInstance(CPersonInfo, None)
            self._deleted      = 0
            self._type         = 0
            self._begDate      = CDateInfo()
            self._duration     = 0
            self._periodicity  = 0
            self._aliquoticity = 0
            self._quantity     = 0
            self._scheduleWeekendDays = 0
            self._note     = ''
            self._smnnUUID = ''
            self._smnn   = self.getInstance(CSmnnInfo, None)
            self._lfForm = self.getInstance(CLFFormInfo, None)
            self._items = self.getInstance(CExecutionPlanItemsInfoList, None)


    createDatetime = property(lambda self: self.load()._createDatetime)
    modifyDatetime = property(lambda self: self.load()._modifyDatetime)
    modifyPerson   = property(lambda self: self.load()._modifyPerson)
    createPerson   = property(lambda self: self.load()._createPerson)
    deleted = property(lambda self: self.load()._deleted)
    type = property(lambda self: self.load()._type)
    begDate = property(lambda self: self.load()._begDate)
    duration = property(lambda self: self.load()._duration)
    periodicity = property(lambda self: self.load()._periodicity)
    aliquoticity = property(lambda self: self.load()._aliquoticity)
    quantity = property(lambda self: self.load()._quantity)
    daysExecutionPlan = property(lambda self: self.load()._daysExecutionPlan)
    scheduleWeekendDays = property(lambda self: self.load()._scheduleWeekendDays)
    note = property(lambda self: self.load()._note)
    smnnUUID = property(lambda self: self.load()._smnnUUID)
    smnn = property(lambda self: self.load()._smnn)
    lfForm = property(lambda self: self.load()._lfForm)
    items = property(lambda self: self.load()._items)


class CExecutionPlanItemInfo(CInfo):
    def __init__(self, context, id, row=0):
        CInfo.__init__(self, context)
        self.id            = id
        self.row           = row
        self._master = self.getInstance(CExecutionPlanInfo, None)
        self._action = self.getInstance(CActionInfo, None)
        self._idx    = 0
        self._aliquoticityIdx = 0
        self._time   = 0
        self._date   = CDateInfo()
        self._executedDatetime = CDateTimeInfo()
        self._nomenclature = self.getInstance(CExecutionPlanItemNomenclatureInfo, None, masterId=self.id)
        self._nomenclatureToRecord = self.getInstance(CExecutionPlanItemNomenclatureInfo, None, masterId=self.id)


    def setRecord(self, item, record, nomenclature):
        #record = item.getRecord()
        #nomenclature = item.nomenclature
        if record:
            self.id      = forceRef(record.value('id'))
            self._master = self.getInstance(CExecutionPlanInfo, forceRef(record.value('master_id')))
            self._action = self.getInstance(CActionInfo, forceRef(record.value('action_id')))
            self._idx    = forceInt(record.value('idx'))
            self._aliquoticityIdx = forceInt(record.value('aliquoticityIdx'))
            self._time   = forceTime(record.value('time'))
            self._date   = CDateInfo(forceDate(record.value('date')))
            self._executedDatetime = CDateTimeInfo(forceDate(record.value('executedDatetime')))
            self._nomenclature = self.getInstance(CExecutionPlanItemNomenclatureInfo, None, masterId=self.id, row=self.row)
            nomenclatureToRecord = self.getInstance(CExecutionPlanItemNomenclatureInfo, None, masterId=self.id, row=self.row)
            nomenclatureToRecord.setRecord(nomenclature.getRecord())
            nomenclatureToRecord.setOkLoaded()
            self._nomenclatureToRecord = nomenclatureToRecord
        else:
            self._master = self.getInstance(CExecutionPlanInfo, None)
            self._action = self.getInstance(CActionInfo, None)
            self._idx    = 0
            self._aliquoticityIdx = 0
            self._time   = 0
            self._date   = CDateInfo()
            self._executedDatetime = CDateTimeInfo()
            self._nomenclature = self.getInstance(CExecutionPlanItemNomenclatureInfo, None, masterId=self.id, row=self.row)
            self._nomenclatureToRecord = self.getInstance(CExecutionPlanItemNomenclatureInfo, None, masterId=self.id, row=self.row)
        return self


    def setOkLoaded(self):
        CInfo.setOkLoaded(self)
        return self


    def _load(self):
        db = QtGui.qApp.db
        table = db.table('ActionExecutionPlan_Item')
        record = db.getRecordEx(table, '*', [table['id'].eq(self.id)], 'id')
        if record:
            self.id      = forceRef(record.value('id'))
            self._master = self.getInstance(CExecutionPlanInfo, forceRef(record.value('master_id')))
            self._action = self.getInstance(CActionInfo, forceRef(record.value('action_id')))
            self._idx    = forceInt(record.value('idx'))
            self._aliquoticityIdx = forceInt(record.value('aliquoticityIdx'))
            self._time   = forceTime(record.value('time'))
            self._date   = CDateInfo(forceDate(record.value('date')))
            self._executedDatetime = CDateTimeInfo(forceDate(record.value('executedDatetime')))
            self._nomenclature = self.getInstance(CExecutionPlanItemNomenclatureInfo, None, masterId=self.id, row=self.row)
            self._nomenclatureToRecord = self.getInstance(CExecutionPlanItemNomenclatureInfo, None, masterId=self.id, row=self.row)
            return True
        else:
            self._master = self.getInstance(CExecutionPlanInfo, None)
            self._action = self.getInstance(CActionInfo, None)
            self._idx    = 0
            self._aliquoticityIdx = 0
            self._time   = 0
            self._date   = CDateInfo()
            self._executedDatetime = CDateTimeInfo()
            self._nomenclature = self.getInstance(CExecutionPlanItemNomenclatureInfo, None, masterId=self.id, row=self.row)
            self._nomenclatureToRecord = self.getInstance(CExecutionPlanItemNomenclatureInfo, None, masterId=self.id, row=self.row)
            return False


    master = property(lambda self: self.load()._master)
    action = property(lambda self: self.load()._action)
    idx = property(lambda self: self.load()._idx)
    aliquoticityIdx = property(lambda self: self.load()._aliquoticityIdx)
    time = property(lambda self: self.load()._time)
    date = property(lambda self: self.load()._date)
    executedDatetime = property(lambda self: self.load()._executedDatetime)
    nomenclature = property(lambda self: self.load()._nomenclature)
    nomenclatureToRecord = property(lambda self: self.load()._nomenclatureToRecord)


class CExecutionPlanItemsInfoList(CInfoList):
    def __init__(self, context, executionPlanId):
        CInfoList.__init__(self, context)
        self.executionPlanId = executionPlanId
        self._idList = []

    def _load(self):
        db = QtGui.qApp.db
        table = db.table('ActionExecutionPlan_Item')
        cond = [table['master_id'].eq(self.executionPlanId)]
        self._idList = db.getIdList(table, 'id', cond, 'id')
        self._items = [ self.getInstance(CExecutionPlanItemInfo, id) for id in self._idList ]
        return True


class CExecutionPlanItemsToActionInfoList(CInfoList):
    def __init__(self, context, actionId):
        CInfoList.__init__(self, context)
        self.actionId = actionId
        self._idList = []

    def _load(self):
        db = QtGui.qApp.db
        table = db.table('ActionExecutionPlan_Item')
        cond = [table['action_id'].eq(self.actionId)]
        self._idList = db.getIdList(table, 'id', cond, 'id')
        self._items = [ self.getInstance(CExecutionPlanItemInfo, id) for id in self._idList ]
        return True


class CExecutionPlanItemNomenclatureInfo(CInfo):
    def __init__(self, context, id, masterId=None, row=0):
        CInfo.__init__(self, context)
        self.id       = id
        self.row      = row
        self.masterId = masterId
        #self._actionExecutionPlan_item = self.getInstance(CExecutionPlanItemInfo, None)
        self._nomenclature = self.getInstance(CNomenclatureInfo, None)
        self._dosage       = ''


    def setRecord(self, record):
        if record:
            self.id            = forceRef(record.value('id'))
            #self._actionExecutionPlan_item = self.getInstance(CExecutionPlanItemInfo, forceRef(record.value('actionExecutionPlan_item_id')) if not self.masterId else None)
            self._nomenclature = self.getInstance(CNomenclatureInfo, forceRef(record.value('nomenclature_id')))
            self._dosage       = forceString(record.value('dosage'))
        else:
            #self._actionExecutionPlan_item = self.getInstance(CExecutionPlanItemInfo, None)
            self._nomenclature = self.getInstance(CNomenclatureInfo, None)
            self._dosage       = ''


    def _load(self):
        record = None
        db = QtGui.qApp.db
        table = db.table('ActionExecutionPlan_Item_Nomenclature')
        if self.id:
            record = db.getRecordEx(table, '*', [table['id'].eq(self.id)], 'id')
        elif self.masterId:
            record = db.getRecordEx(table, '*', [table['actionExecutionPlan_item_id'].eq(self.masterId)], 'id')
        if record:
            self.id      = forceRef(record.value('id'))
            #self._actionExecutionPlan_item = self.getInstance(CExecutionPlanItemInfo, forceRef(record.value('actionExecutionPlan_item_id')) if not self.masterId else None)
            self._nomenclature = self.getInstance(CNomenclatureInfo, forceRef(record.value('nomenclature_id')))
            self._dosage       = forceString(record.value('dosage'))
            return True
        else:
            #self._actionExecutionPlan_item = self.getInstance(CExecutionPlanItemInfo, None)
            self._nomenclature = self.getInstance(CNomenclatureInfo, None)
            self._dosage       = ''
            return False


    #actionExecutionPlan_item = property(lambda self: self.load()._actionExecutionPlan_item)
    nomenclature = property(lambda self: self.load()._nomenclature)
    dosage = property(lambda self: self.load()._dosage)


class CExecutionPlanItemNomenclatureInfoList(CInfoList):
    def __init__(self, context, executionPlanItemId):
        CInfoList.__init__(self, context)
        self.executionPlanItemId = executionPlanItemId
        self._idList = []

    def _load(self):
        db = QtGui.qApp.db
        table = db.table('ActionExecutionPlan_Item_Nomenclature')
        cond = [table['actionExecutionPlan_item_id'].eq(self.executionPlanItemId)]
        self._idList = db.getIdList(table, 'id', cond, 'id')
        self._items = [ self.getInstance(CExecutionPlanItemNomenclatureInfo, id) for id in self._idList ]
        return True
    

class CActionTypeGroupItemsInfoList(CInfoList):
    def __init__(self, context, actionTypeGroupId):
        CInfoList.__init__(self, context)
        self.actionTypeGroupId = actionTypeGroupId
        self._idList = []

    def _load(self):
        db = QtGui.qApp.db
        table = db.table('ActionTypeGroup_Item')
        cond = [table['master_id'].eq(self.actionTypeGroupId)]
        self._idList = db.getIdList(table, 'id', cond, 'id')
        self._items = [ self.getInstance(CActionTypeGroupItemsInfo, id) for id in self._idList ]
        return True


class CActionTypeGroupInfo(CInfo):
    def __init__(self, context, id):
        CInfo.__init__(self, context)
        self.id            = id
        self._createDatetime = CDateTimeInfo()
        self._modifyDatetime = CDateTimeInfo()
        self._modifyPerson = self.getInstance(CPersonInfo, None)
        self._createPerson = self.getInstance(CPersonInfo, None)
        self._deleted      = 0
        self._code         = ''
        self._name         = ''
        self._type         = 0
        self._availability = 0
        self._class        = None
        self._isOffset     = 0
        self._items = []


    def setRecord(self, record):
        if record:
            self.id            = forceRef(record.value('id'))
            self._createDatetime = CDateTimeInfo(forceDateTime(record.value('createDatetime')))
            self._modifyDatetime = CDateTimeInfo(forceDateTime(record.value('modifyDatetime')))
            self._modifyPerson = self.getInstance(CPersonInfo, forceRef(record.value('modifyPerson_id')))
            self._createPerson = self.getInstance(CPersonInfo, forceRef(record.value('createPerson_id')))
            self._deleted      = forceInt(record.value('deleted'))
            self._code         = forceString(record.value('code'))
            self._name         = forceString(record.value('name'))
            self._availability = forceInt(record.value('availability'))
            self._class        = forceInt(record.value('class'))
            self._isOffset     = forceInt(record.value('isOffset'))
            self._items        = self.getInstance(CActionTypeGroupItemsInfoList, self.id)
        else:
            self._createDatetime = CDateTimeInfo()
            self._modifyDatetime = CDateTimeInfo()
            self._modifyPerson = self.getInstance(CPersonInfo, None)
            self._createPerson = self.getInstance(CPersonInfo, None)
            self._deleted      = 0
            self._code         = ''
            self._name         = ''
            self._type         = 0
            self._availability = 0
            self._class        = None
            self._isOffset     = 0
            self._items = self.getInstance(CActionTypeGroupItemsInfoList, None)


    def _load(self):
        db = QtGui.qApp.db
        table = db.table('ActionTypeGroup')
        record = db.getRecordEx(table, '*', [table['id'].eq(self.id), table['deleted'].eq(0)], 'id')
        if record:
            self.id            = forceRef(record.value('id'))
            self._createDatetime = CDateTimeInfo(forceDateTime(record.value('createDatetime')))
            self._modifyDatetime = CDateTimeInfo(forceDateTime(record.value('modifyDatetime')))
            self._modifyPerson = self.getInstance(CPersonInfo, forceRef(record.value('modifyPerson_id')))
            self._createPerson = self.getInstance(CPersonInfo, forceRef(record.value('createPerson_id')))
            self._deleted      = forceInt(record.value('deleted'))
            self._code         = forceString(record.value('code'))
            self._name         = forceString(record.value('name'))
            self._availability = forceInt(record.value('availability'))
            self._class        = forceInt(record.value('class'))
            self._isOffset     = forceInt(record.value('isOffset'))
            self._items = self.getInstance(CActionTypeGroupItemsInfoList, self.id)
        else:
            self._createDatetime = CDateTimeInfo()
            self._modifyDatetime = CDateTimeInfo()
            self._modifyPerson = self.getInstance(CPersonInfo, None)
            self._createPerson = self.getInstance(CPersonInfo, None)
            self._deleted      = 0
            self._code         = ''
            self._name         = ''
            self._type         = 0
            self._availability = 0
            self._class        = None
            self._isOffset     = 0
            self._items = self.getInstance(CActionTypeGroupItemsInfoList, None)


    createDatetime = property(lambda self: self.load()._createDatetime)
    modifyDatetime = property(lambda self: self.load()._modifyDatetime)
    modifyPerson   = property(lambda self: self.load()._modifyPerson)
    createPerson   = property(lambda self: self.load()._createPerson)
    deleted        = property(lambda self: self.load()._deleted)
    code           = property(lambda self: self.load()._code)
    name           = property(lambda self: self.load()._name)
    type           = property(lambda self: self.load()._type)
    availability   = property(lambda self: self.load()._availability)
    class_         = property(lambda self: self.load()._class)
    isOffset       = property(lambda self: self.load()._isOffset)
    items          = property(lambda self: self.load()._items)


class CActionTypeGroupItemsInfo(CInfo):
    def __init__(self, context, id):
        CInfo.__init__(self, context)
        self.id            = id
        self._createDatetime = CDateTimeInfo()
        self._modifyDatetime = CDateTimeInfo()
        self._modifyPerson = self.getInstance(CPersonInfo, None)
        self._createPerson = self.getInstance(CPersonInfo, None)
        self._deleted      = 0
        self._actionType = self.getInstance(CActionTypeInfo, None)
        self._nomenclature = self.getInstance(CNomenclatureInfo, None)
        self._doses = ''
        self._signa   = ''
        self._duration   = 0
        self._periodicity = 0
        self._aliquoticity = 0
        self._offset = 0
        self._orgStructure = self.getInstance(COrgStructureInfo, None)
        self._activeSubstance = self.getInstance(CNomenclatureActiveSubstanceInfo, None)
        self._smnnUUID = ''
        self._smnn = self.getInstance(CSmnnInfo, '')
        self._lfForm = self.getInstance(CLFFormInfo, None)
        self._actionPropertyTemplate = self.getInstance(CActionPropertyTemplateInfo, None)


    def setRecord(self, record):
        if record:
            self.id = forceRef(record.value('id'))
            self._createDatetime = CDateTimeInfo(forceDateTime(record.value('createDatetime')))
            self._modifyDatetime = CDateTimeInfo(forceDateTime(record.value('modifyDatetime')))
            self._modifyPerson = self.getInstance(CPersonInfo, forceRef(record.value('modifyPerson_id')))
            self._createPerson = self.getInstance(CPersonInfo, forceRef(record.value('createPerson_id')))
            self._deleted      = forceInt(record.value('deleted'))
            self._actionType = self.getInstance(CActionTypeInfo, forceRef(self._record.value('actionType_id')))
            self._nomenclature = self.getInstance(CNomenclatureInfo, forceRef(self._record.value('nomenclature_id')))
            self._doses = forceString(self._record.value('doses'))
            self._signa   = forceString(self._record.value('signa'))
            self._duration   = forceInt(record.value('duration'))
            self._periodicity = forceInt(record.value('periodicity'))
            self._aliquoticity = forceInt(record.value('aliquoticity'))
            self._offset = forceInt(record.value('offset'))
            self._orgStructure = self.getInstance(COrgStructureInfo, forceRef(self._record.value('orgStructure_id')))
            self._activeSubstance = self.getInstance(CNomenclatureActiveSubstanceInfo, forceRef(self._record.value('activeSubstance_id')))
            self._smnnUUID = forceStringEx(self._record.value('smnnUUID'))
            self._smnn = self.getInstance(CSmnnInfo, self._smnnUUID)
            self._lfForm = self.getInstance(CLFFormInfo, forceRef(record.value('lfForm_id')))
            self._actionPropertyTemplate = self.getInstance(CActionPropertyTemplateInfo, forceRef(self._record.value('actionPropertyTemplate_id')))
        else:
            self._createDatetime = CDateTimeInfo()
            self._modifyDatetime = CDateTimeInfo()
            self._modifyPerson = self.getInstance(CPersonInfo, None)
            self._createPerson = self.getInstance(CPersonInfo, None)
            self._deleted      = 0
            self._actionType = self.getInstance(CActionTypeInfo, None)
            self._nomenclature = self.getInstance(CNomenclatureInfo, None)
            self._doses = ''
            self._signa   = ''
            self._duration   = 0
            self._periodicity = 0
            self._aliquoticity = 0
            self._offset = 0
            self._orgStructure = self.getInstance(COrgStructureInfo, None)
            self._activeSubstance = self.getInstance(CNomenclatureActiveSubstanceInfo, None)
            self._smnnUUID = ''
            self._smnn = self.getInstance(CSmnnInfo, '')
            self._lfForm = self.getInstance(CLFFormInfo, None)
            self._actionPropertyTemplate = self.getInstance(CActionPropertyTemplateInfo, None)


    def _load(self):
        db = QtGui.qApp.db
        table = db.table('ActionTypeGroup_Item')
        record = db.getRecordEx(table, '*', [table['id'].eq(self.id), table['deleted'].eq(0)], 'id')
        if record:
            self.id = forceRef(record.value('id'))
            self._createDatetime = CDateTimeInfo(forceDateTime(record.value('createDatetime')))
            self._modifyDatetime = CDateTimeInfo(forceDateTime(record.value('modifyDatetime')))
            self._modifyPerson = self.getInstance(CPersonInfo, forceRef(record.value('modifyPerson_id')))
            self._createPerson = self.getInstance(CPersonInfo, forceRef(record.value('createPerson_id')))
            self._deleted      = forceInt(record.value('deleted'))
            self._actionType = self.getInstance(CActionTypeInfo, forceRef(self._record.value('actionType_id')))
            self._nomenclature = self.getInstance(CNomenclatureInfo, forceRef(self._record.value('nomenclature_id')))
            self._doses = forceString(self._record.value('doses'))
            self._signa   = forceString(self._record.value('signa'))
            self._duration   = forceInt(record.value('duration'))
            self._periodicity = forceInt(record.value('periodicity'))
            self._aliquoticity = forceInt(record.value('aliquoticity'))
            self._offset = forceInt(record.value('offset'))
            self._orgStructure = self.getInstance(COrgStructureInfo, forceRef(self._record.value('orgStructure_id')))
            self._activeSubstance = self.getInstance(CNomenclatureActiveSubstanceInfo, forceRef(self._record.value('activeSubstance_id')))
            self._smnnUUID = forceStringEx(self._record.value('smnnUUID'))
            self._smnn = self.getInstance(CSmnnInfo, self._smnnUUID)
            self._lfForm = self.getInstance(CLFFormInfo, forceRef(record.value('lfForm_id')))
            self._actionPropertyTemplate = self.getInstance(CActionPropertyTemplateInfo, forceRef(self._record.value('actionPropertyTemplate_id')))
            return True
        else:
            self._createDatetime = CDateTimeInfo()
            self._modifyDatetime = CDateTimeInfo()
            self._modifyPerson = self.getInstance(CPersonInfo, None)
            self._createPerson = self.getInstance(CPersonInfo, None)
            self._deleted      = 0
            self._actionType = self.getInstance(CActionTypeInfo, None)
            self._nomenclature = self.getInstance(CNomenclatureInfo, None)
            self._doses = ''
            self._signa   = ''
            self._duration   = 0
            self._periodicity = 0
            self._aliquoticity = 0
            self._offset = 0
            self._orgStructure = self.getInstance(COrgStructureInfo, None)
            self._activeSubstance = self.getInstance(CNomenclatureActiveSubstanceInfo, None)
            self._smnnUUID = ''
            self._smnn = self.getInstance(CSmnnInfo, '')
            self._lfForm = self.getInstance(CLFFormInfo, None)
            self._actionPropertyTemplate = self.getInstance(CActionPropertyTemplateInfo, None)
            return False


    createDatetime = property(lambda self: self.load()._createDatetime)
    modifyDatetime = property(lambda self: self.load()._modifyDatetime)
    modifyPerson   = property(lambda self: self.load()._modifyPerson)
    createPerson   = property(lambda self: self.load()._createPerson)
    deleted        = property(lambda self: self.load()._deleted)
    actionType     = property(lambda self: self.load()._actionType)
    nomenclature   = property(lambda self: self.load()._nomenclature)
    doses          = property(lambda self: self.load()._doses)
    signa          = property(lambda self: self.load()._signa)
    duration       = property(lambda self: self.load()._duration)
    periodicity    = property(lambda self: self.load()._periodicity)
    aliquoticity   = property(lambda self: self.load()._aliquoticity)
    offset         = property(lambda self: self.load()._offset)
    orgStructure   = property(lambda self: self.load()._orgStructure)
    activeSubstance= property(lambda self: self.load()._activeSubstance)
    smnnUUID       = property(lambda self: self.load()._smnnUUID)
    smnn           = property(lambda self: self.load()._smnn)
    lfForm         = property(lambda self: self.load()._lfForm)
    actionPropertyTemplate = property(lambda self: self.load()._actionPropertyTemplate)


class CActionPropertyTemplateInfo(CRBInfo):
    tableName = 'ActionPropertyTemplate'
