# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2026 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

u"""
Описание объекта Action и его свойств
"""

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import QDateTime, QVariant, QTime

from ActionProperty import CActionProperty, CActionPropertyType
from Events.ActionServiceType import CActionServiceType
from Events.ActionStatus import CActionStatus
from Events.BLModels.Event import CEvent
from Events.NomenclatureAddedActionsSelectDialog import CNomenclatureAddedActionsSelectDialog
from Events.Utils import (getActionTypeIdListByFlatCode, getExistsNomenclature, getEventTypeForm, getEventDuration,
                          getEventActionContract, syncNomenclature, getEventMedicalAidKindId, calcQuantity, checkFileAttachListChanged,
                                      updateNomenclatureDosageValue,)
from ExecutionPlan.ActionExecutionPlanManager import CActionExecutionPlanManager
from Orgs.OrgComboBox import CContractDbModel
from Orgs.Utils import getPersonOrgStructureChiefs, getOrgStructureDescendants
from Resources.JobTicketStatus import CJobTicketStatus
from Stock.Service import CStockService
from Stock.Utils import (getNomenclatureUnitRatio, applyNomenclatureUnitRatio, findFinanceBatchShelfTime,
                         getStockMotionNumberCounterId, getExistsNomenclatureAmount,
                         #getBatchShelfTimeFinance,
                         getBatchShelfTimeFinanceQnt,
                         getRatio)
from Users.Rights import urEditAfterInvoicingEvent, urEditOtherpeopleAction, urEditSubservientPeopleAction, \
    urEditOtherPeopleActionSpecialityOnly, urDeleteNotOwnActions, urDeleteActionsWithJobTicket, urAdmin, \
    urCanAttachFile
from library.Attach.AttachedFile import CAttachedFilesLoader
from library.Calendar import wpFiveDays, wpSixDays, wpSevenDays, addWorkDays
from library.DbEntityCache import CDbEntityCache
from library.Utils import (forceBool, forceDate, forceDateTime, forceDouble, forceInt, forceRef, forceString,
                           forceStringEx, formatNum1, toVariant)
from library.calc import buildMapWhatdepends, buildExecutionPlan
from library.database import CDocumentTable, CSqlRecord
from library.exception import CException

_RECIPE = 1
_DOSES  = 2
_SIGNA  = 3
_ACTIVESUBSTANCE = 4


class CActionType(object):
    # режимы подсчёта количества в действии
    userInput                            = 0
    eventVisitCount                      = 1
    eventDurationWithFiveDayWorking      = 2
    eventDurationWithSixDayWorking       = 3
    eventDurationWithSevenDayWorking     = 4
    actionFilledPropsCount               = 5
    actionAssignedPropsCount             = 6
    actionDurationWithFiveDayWorking     = 7
    actionDurationWithSixDayWorking      = 8
    actionDurationWithSevenDayWorking    = 9
    actionPredefinedNumber               = 10
    actionDurationFact                   = 11

    # их названия
    amountEvaluation = [
                        u'Количество вводится непосредственно',
                        u'Число визитов',
                        u'Длительность события при пятидневной рабочей неделе',
                        u'Длительность события при шестидневной рабочей неделе',
                        u'Длительность события при семидневной рабочей неделе',
                        u'Количество заполненных свойств действия',
                        u'Количество назначенных свойств действия',
                        u'Длительность действия при пятидневной рабочей неделе',
                        u'Длительность действия при шестидневной рабочей неделе',
                        u'Длительность действия при семидневной рабочей неделе',
                        u'Предопределенное количество',
                        u'Фактическое количество'
                       ]

#    amountEvaluationFreeInput = 0

    # дата выполнения(default end date)
    dedUndefined         = 0
    dedCurrentDate       = 1
    dedEventSetDate      = 2
    dedEventExecDate     = 3
    dedActionBegDate     = 4
    dedSyncActionBegDate = 5
    dedSyncEventBegDate  = 6
    dedSyncEventEndDate  = 7

    # дата начала действия(default beg date)
    dbdUndefined        = 0
    dbdCurrentDate      = 1
    dbdEventSetDate     = 2
    dbdEventExecDate    = 3
    dbdActionEndDate    = 4
    dbdJobTicketTime    = 5
    dbdSyncEventBegDate = 6
    dbdSyncEventEndDate = 7

    # планируемая дата выполнения(default planned end date)
    dpedUndefined           = 0
    dpedNextDay             = 1
    dpedNextWorkDay         = 2
    dpedJobTicketDate       = 3
    dpedBegDatePlusAmount   = 4
    dpedBegDatePlusDuration = 5

    # заполнение планируемой даты выполнения(isPlannedEndDateRequired)
    dpedControlNoNeed       = 0
    dpedControlMild         = 1
    dpedControlHard         = 2

    # дата назначения(default direction date)
    dddUndefined      = 0
    dddEventSetDate   = 1
    dddCurrentDate    = 2
    dddActionExecDate = 3
    dddSyncEventBegDate = 4
    dddSyncEventEndDate = 5

    # назначивший (default setPerson)
    dspUndefined = 0
    dspEventExecPerson = 1
    dspExecPerson = 2

    # ответственный (default person)
    dpUndefined       = 0
    dpEmpty           = 1
    dpSetPerson       = 2
    dpEventExecPerson = 3
    dpCurrentUser     = 4
    dpCurrentMedUser  = 5
    dpUserExecPerson  = 6

    #MKB (default MKB)
    dmkbNotUsed           = 0
    dmkbByFinalDiag       = 1
    dmkbBySetPersonDiag   = 2
    dmkbSyncFinalDiag     = 3
    dmkbSyncSetPersonDiag = 4
    dmkbUserInput         = 5
    dmkbSyncPreDiag       = 6

    def __init__(self, record, propertyTypeRecords=None, relatedActionTypeRecords=None):
        self._propertiesById = {}
        self._propertiesByName = {}
        self._propertiesByType = {}
        self._propertiesByTest = {}
        self._propertiesByShortName = {}
        self._relatedActionTypes = {}
        self._relatedActionTypesOrder = {}
        self.initByRecord(record, propertyTypeRecords, relatedActionTypeRecords)
        self.PFOrgStructureLoaded = False
        self.PFSpecialityLoaded = False
        self.EquipmentLoaded = False
        self.ActionSpecificationLoaded = False
        self.QuotaTypeLoaded = False
        self.TestatorLoaded = False
        self.ExpansionLoaded = False
        self.NomenclatureLoaded = False


    def initByRecord(self, record, propertyTypeRecords=None, relatedActionTypeRecords=None):
        self.id   = forceRef(record.value('id'))
        self.groupId = forceRef(record.value('group_id'))
        self.class_ = forceInt(record.value('class'))
        self.expirationDate = forceInt(record.value('expirationDate'))
        self.code = forceString(record.value('code'))
        self.name = forceString(record.value('name'))
        self.title = forceString(record.value('title'))
        self.flatCode = forceString(record.value('flatCode'))
        self.isRequiredCoordination = forceBool(record.value('isRequiredCoordination'))
#        self.serviceId = forceRef(record.value('service_id'))
        self.amount = forceDouble(record.value('amount'))
        self.amountEvaluation = forceInt(record.value('amountEvaluation'))
        self.defaultStatus  = forceInt(record.value('defaultStatus'))
        self.defaultDirectionDate = forceInt(record.value('defaultDirectionDate'))
        self.defaultPlannedEndDate = forceInt(record.value('defaultPlannedEndDate'))
        self.isPlannedEndDateRequired = forceInt(record.value('isPlannedEndDateRequired'))
        self.defaultBegDate = forceInt(record.value('defaultBegDate'))
        self.defaultEndDate = forceInt(record.value('defaultEndDate'))
        self.defaultExecPersonId   = forceRef(record.value('defaultExecPerson_id'))
        self.defaultPersonInEvent  = forceInt(record.value('defaultPersonInEvent'))
        self.defaultSetPersonInEvent = forceInt(record.value('defaultSetPersonInEvent'))
        self.defaultPersonInEditor = forceInt(record.value('defaultPersonInEditor'))
        self.defaultOrgId          = forceRef(record.value('defaultOrg_id'))
        self.defaultMKB            = forceInt(record.value('defaultMKB'))
        self.isMorphologyRequired  = forceInt(record.value('isMorphologyRequired'))
        self.isMKBRequired         = forceInt(record.value('isMKBRequired'))
        self.isExecPersonRequired  = forceInt(record.value('isExecPersonRequired'))
        self.duplication           = forceInt(record.value('duplication'))
        self.office = forceString(record.value('office'))
        self.showInForm = forceInt(record.value('showInForm'))
        self.showTime = forceBool(record.value('showTime'))
        self.maxOccursInEvent = forceInt(record.value('maxOccursInEvent'))
        self.isMes = forceBool(record.value('isMES'))
        self.nomenclativeServiceId = forceRef(record.value('nomenclativeService_id'))
        self.context = forceString(record.value('context'))
        self.prescribedTypeId = forceRef(record.value('prescribedType_id'))
        self.sheduleId = forceRef(record.value('shedule_id'))
        self.isNomenclatureExpense = forceBool(record.value('isNomenclatureExpense'))
        self.isDoesNotInvolveExecutionCourse = forceBool(record.value('isDoesNotInvolveExecutionCourse'))
        self.isNeedAttachFile = forceInt(record.value('isNeedAttachFile'))
        self.nomenclatureCounterId = forceRef(record.value('nomenclatureCounter_id'))
        self.generateStockMotionReason = forceBool(record.value('generateStockMotionReason'))
        self.hasAssistant = forceBool(record.value('hasAssistant'))
        self.requiredActionSpecification = forceBool(record.value('requiredActionSpecification'))
        self.propertyAssignedVisible = forceBool(record.value('propertyAssignedVisible'))
        self.propertyAssignedRequired = forceBool(record.value('propertyAssignedRequired'))
        self.propertyUnitVisible = forceBool(record.value('propertyUnitVisible'))
        self.propertyNormVisible = forceBool(record.value('propertyNormVisible'))
        self.propertyEvaluationVisible = forceBool(record.value('propertyEvaluationVisible'))
        self.propertyCommentVisible = forceBool(record.value('propertyCommentVisible'))
        self.serviceType = forceInt(record.value('serviceType'))
        self.actualAppointmentDuration = forceInt(record.value('actualAppointmentDuration'))
        self.ticketDuration = forceInt(record.value('ticketDuration'))
        self.closeEvent = forceInt(record.value('closeEvent'))
        self.addVisit = forceInt(record.value('addVisit'))
        self.addVisitSceneId = forceRef(record.value('addVisitScene_id'))
        self.addVisitTypeId = forceRef(record.value('addVisitType_id'))
        self.generateAfterEventExecDate = forceBool(record.value('generateAfterEventExecDate'))
        self.nomenclatureOrgStructureId = forceRef(record.value('nomenclatureOrgStructure_id'))
        self.showBegDate = forceBool(record.value('showBegDate'))
        self.editStatus = forceBool(record.value('editStatus'))
        self.editBegDate = forceBool(record.value('editBegDate'))
        self.editEndDate = forceBool(record.value('editEndDate'))
        self.editNote = forceBool(record.value('editNote'))
        self.editExecPers = forceBool(record.value('editExecPers'))
        self.editSetPerson = forceBool(record.value('editSetPerson'))
        self.editOrg = forceBool(record.value('editOrg'))
        self.editOrgStructure = forceBool(record.value('editOrgStructure'))

        self._nomenclatureRecordList = None
        self._hasJobTicketPropertyType = False

        self._initProperties(propertyTypeRecords)
        self._loadRelatedActionTypes(relatedActionTypeRecords)
        # self._loadPFOrgStructureRecordList()
        # self._loadPFSpecialityRecordList()
        # self._loadEquipmentRecordList()
        # self._loadActionSpecificationRecordList()
        # self._loadQuotaTypeList()
        # self._loadTestatorIdList()
        # self._loadExpansionIdList()
        # if self.isNomenclatureExpense:
        #     self._loadNomenclatureRecordList()


    def isServiceTypeProcedure(self):
        return self.serviceType == CActionServiceType.procedure


    def isServiceTypeResearch(self):
        return self.serviceType in (CActionServiceType.research, CActionServiceType.labResearch)


    def hasJobTicketPropertyType(self):
        return self._hasJobTicketPropertyType


    def _loadNomenclatureRecordList(self):
        self._nomenclatureRecordList = QtGui.qApp.db.getRecordList('ActionType_Nomenclature', '*', 'master_id=%d' % self.id)
        self.NomenclatureLoaded = True


    def _loadPFSpecialityRecordList(self):
        self._pfSpecialityRecordList = QtGui.qApp.db.getRecordList('ActionType_PFSpeciality', '*', 'master_id=%d' % self.id)
        self.PFSpecialityLoaded = True


    def _loadPFOrgStructureRecordList(self):
        self._pfOrgStructureRecordList = QtGui.qApp.db.getRecordList('ActionType_PFOrgStructure', '*', 'master_id=%d' % self.id)
        self.PFOrgStructureLoaded = True


    def _loadTestatorIdList(self):
        self._testatorIdList = QtGui.qApp.db.getIdList('ActionType_Testator', idCol='testator_id', where='master_id=%d' % self.id)
        self.TestatorLoaded = True


    def _loadExpansionIdList(self):
        db = QtGui.qApp.db
        tableAT = db.table('ActionType')
        tableATE = db.table('ActionType_Expansion')
        queryTable = tableAT.innerJoin(tableATE, tableATE['actionType_id'].eq(tableAT['id']))
        cond = [tableATE['deleted'].eq(0), tableAT['deleted'].eq(0), tableATE['master_id'].eq(self.id)]
        order = [tableAT['code'].name(), tableAT['name'].name()]
        self._actionTypeExpansionIdList = db.getDistinctIdList(queryTable, [tableATE['actionType_id']], cond, order)
        self.ExpansionLoaded = True


    def _loadEquipmentRecordList(self):
        self._equipmentRecordList = QtGui.qApp.db.getRecordList('ActionType_Equipment', '*', 'master_id=%d' % self.id)
        self._equipmentIdList = []
        for record in self._equipmentRecordList:
            self._equipmentIdList.append(forceRef(record.value('equipment_id')))
        self.EquipmentLoaded = True


    def _loadActionSpecificationRecordList(self):
        self._actionSpecificationRecordList = QtGui.qApp.db.getRecordList('ActionType_UETActionSpecification', '*', 'master_id=%d' % self.id)
        self._actionSpecificationIdList = []
        for record in self._actionSpecificationRecordList:
            self._actionSpecificationIdList.append(forceRef(record.value('actionSpecification_id')))
        self.ActionSpecificationLoaded = True


    def _loadQuotaTypeList(self):
        self._quotaTypeList = QtGui.qApp.db.getRecordList('ActionType_QuotaType', '*', 'master_id=%d' % self.id)
        self._quotaType = []
        for record in self._quotaTypeList:
            self._quotaType.append(forceRef(record.value('quotaType_id')))
        self.QuotaTypeLoaded = True
    
    
    def _loadRelatedActionTypes(self, relatedActionTypeRecords=None):
        if relatedActionTypeRecords is None:
            actionTypeList = QtGui.qApp.db.getRecordList('ActionType_Relations', 'related_id, isRequired, idx', 'master_id={} and related_id IS NOT NULL'.format(self.id), order = 'idx')
        else:
            actionTypeList = relatedActionTypeRecords
        for record in actionTypeList:
            self._relatedActionTypes[forceRef(record.value('related_id'))] = forceBool(record.value('isRequired'))
            self._relatedActionTypesOrder[forceRef(record.value('related_id'))] = forceInt(record.value('idx'))
        self.RelatedActionTypesLoaded = True


    def getNomenclatureOrgStructureId(self):
        return self.nomenclatureOrgStructureId


    def getNomenclatureRecordList(self):
        if not self.NomenclatureLoaded:
            self._loadNomenclatureRecordList()
        return self._nomenclatureRecordList


    def getActionSpecificationIdList(self):
        if not self.ActionSpecificationLoaded:
            self._loadActionSpecificationRecordList()
        return self._actionSpecificationIdList


    def getPFSpecialityRecordList(self):
        if not self.PFSpecialityLoaded:
            self._loadPFSpecialityRecordList()
        return self._pfSpecialityRecordList


    def getPFOrgStructureRecordList(self):
        if not self.PFOrgStructureLoaded:
            self._loadPFOrgStructureRecordList()
        return self._pfOrgStructureRecordList
    
    
    def getRelatedActionTypes(self):
        if not self.RelatedActionTypesLoaded:
            self._loadRelatedActionTypes()
        return self._relatedActionTypes
    
    
    def getRelatedActionTypesOrder(self):
        if not self.RelatedActionTypesLoaded:
            self._loadRelatedActionTypes()
        return self._relatedActionTypesOrder


    def getTestatorIdList(self):
        if not self.TestatorLoaded:
            self._loadTestatorIdList()
        return self._testatorIdList


    def getExpansionIdList(self):
        if not self.ExpansionLoaded:
            self._loadExpansionIdList()
        return self._actionTypeExpansionIdList


    def _initProperties(self, propertyTypeRecords):
        if propertyTypeRecords is None:
            db = QtGui.qApp.db
            tablePropertyType = db.table('ActionPropertyType')
            propertyTypeRecords = db.getRecordList(tablePropertyType,
                                                   '*',
                                                   [tablePropertyType['actionType_id'].eq(self.id),
                                                    tablePropertyType['deleted'].eq(0)],
                                                   'name')
        mapDepends = {}
        for record in propertyTypeRecords:
            propertyType = CActionPropertyType(record)
            self._propertiesById[propertyType.id] = propertyType
            self._propertiesByName[propertyType.name] = propertyType
            if propertyType.var:
                mapDepends[propertyType.var] = propertyType.depends
            if propertyType.testId:
                self._propertiesByTest[propertyType.testId] = propertyType
            if propertyType.shortName:
                self._propertiesByShortName[propertyType.shortName] = propertyType
            propsList = self._propertiesByType.setdefault(propertyType.typeName, [])
            propsList.append(propertyType)
            if not self._hasJobTicketPropertyType and propertyType.isJobTicketValueType():
                self._hasJobTicketPropertyType = True
        mapWhatDepends = buildMapWhatdepends(mapDepends)  # выворачиваем зависимости наизнанку
        for propertyType in self._propertiesById.itervalues():
            if propertyType.var and not propertyType.expr:
                propertyType.whatDepends = buildExecutionPlan(propertyType.var, mapWhatDepends)


    def getPropertiesById(self):
        return self._propertiesById


    def getPropertiesByName(self):
        return self._propertiesByName


#    def getPropertiesByVar(self):
#        return self._propertiesByVar


    def hasProperty(self, name):
        return name in self._propertiesByName


    def getPropertyType(self, name):
        return self._propertiesByName[name]


    def getPropertyTypeById(self, id):
        return self._propertiesById[id]

    
    def getPropertyTypeByTest(self, testId):
        return self._propertiesByTest.get(testId, None)

    def getPropertyTypeByShortName(self, shortName):
        return self._propertiesByShortName.get(shortName, None)


    def getPropertiesTypeByTypeName(self, typeName):
        return self._propertiesByType.get(typeName, [])


    def propertyTypeIdPresent(self, id):
        return id in self._propertiesById


    def checkMaxOccursLimit(self, count, displayMessage=True):
        result = self.maxOccursInEvent == 0 or count < self.maxOccursInEvent
        if not result and displayMessage:
            widget = QtGui.qApp.activeModalWidget() or QtGui.qApp.mainWindow or None
            QtGui.QMessageBox.critical( widget,
                                        u'Произошла ошибка',
                                        u'Действие типа "%s" должно применяться в осмотре не более %s' % (self.name, formatNum1(self.maxOccursInEvent, (u'раза', u'раз', u'раз'))),
                                        QtGui.QMessageBox.Close)
        return result


    def checkReceivedMovingLeaved(self, message):
        widget = QtGui.qApp.activeModalWidget() or QtGui.qApp.mainWindow or None
        QtGui.QMessageBox.critical( widget,
                                    u'Произошла ошибка',
                                    message,
                                    QtGui.QMessageBox.Close)
        return False


class CActionTypeCache(CDbEntityCache):
    mapIdToActionType = {}
    mapCodeToActionType = {}
    mapFlatCodeToActionType = {}

    @classmethod
    def purge(cls):
        cls.mapIdToActionType.clear()
        cls.mapCodeToActionType.clear()
        cls.mapFlatCodeToActionType.clear()


    @classmethod
    def getById(cls, actionTypeId):
        result = cls.mapIdToActionType.get(actionTypeId, None)
        if not result:
            cls.connect()
            db = QtGui.qApp.db
            actionTypeRecord = db.getRecord('ActionType', '*', actionTypeId)
            result = CActionType(actionTypeRecord)
            cls.register(result)
        return result


    @classmethod
    def getByIds(cls, actionTypeIdList):
        result = []
        notFound = []
        for actionTypeId in actionTypeIdList:
            res = cls.mapIdToActionType.get(actionTypeId, None)
            if not res:
                notFound.append(actionTypeId)
            else:
                result.append(res)
        if notFound:
            db = QtGui.qApp.db
            ptDict = dict()
            relDict = dict()
            table = db.table('ActionType')
            tableAPT = db.table('ActionPropertyType')
            actionTypeRecords = db.getRecordList(table, '*', table['id'].inlist(notFound))
            propertyTypeRecords = db.getRecordList(tableAPT,
                                                   '*',
                                                   [tableAPT['actionType_id'].inlist(notFound),
                                                    tableAPT['deleted'].eq(0)],
                                                   'name')
            for record in propertyTypeRecords:
                ptDict.setdefault(forceRef(record.value('actionType_id')), []).append(record)

            tableRelated = db.table('ActionType_Relations')
            relatedRecords = db.getRecordList(tableRelated,
                                                   '*',
                                                   [tableRelated['master_id'].inlist(notFound)],
                                                   'master_id, idx')
            for record in relatedRecords:
                relDict.setdefault(forceRef(record.value('master_id')), []).append(record)

            for record in actionTypeRecords:
                actionType = CActionType(record, ptDict.get(forceRef(record.value('id')), []), relDict.get(forceRef(record.value('id')), []))
                cls.register(actionType)
                result.append(actionType)
        return result


    @classmethod
    def getByCode(cls, actionTypeCode):
        result = cls.mapCodeToActionType.get(actionTypeCode, None)
        if not result:
            cls.connect()
            db = QtGui.qApp.db
            tableActionType = db.table('ActionType')
            actionTypeRecord = db.getRecordEx(tableActionType, '*', tableActionType['code'].eq(actionTypeCode))
            assert actionTypeRecord
            result = CActionType(actionTypeRecord)
            cls.register(result)
        return result


    @classmethod
    def getByFlatCode(cls, actionTypeFlatCode):
        result = cls.mapFlatCodeToActionType.get(actionTypeFlatCode, None)
        if not result:
            cls.connect()
            db = QtGui.qApp.db
            tableActionType = db.table('ActionType')
            actionTypeRecord = db.getRecordEx(tableActionType, '*', tableActionType['flatCode'].eq(actionTypeFlatCode))
            assert actionTypeRecord
            result = CActionType(actionTypeRecord)
            cls.register(result)
        return result


    @classmethod
    def register(cls, actionType):
        cls.mapIdToActionType[actionType.id]     = actionType
        cls.mapCodeToActionType[actionType.code] = actionType
        cls.mapFlatCodeToActionType[actionType.flatCode] = actionType


# ################################################


class CActionLoadingFabric(object):
    def __init__(self):
        self.__ctx = None

    def __enter__(self):
        if self.__ctx is not None:
            self.__ctx = None
            raise RuntimeError("Context already initialized")

        self.__ctx = {
            'actionListMap': {},
            'epIdMap': {}
        }
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        ctx, self.__ctx = self.__ctx, None
        mngrs = []
        for epId, actionList in ctx['actionListMap'].items():
            executionPlan = ctx['epIdMap'][epId]
            executionPlanItems = []
            for action in actionList:
                mngrs.append(action.executionPlanManager)
                executionPlanItems.append(action.executionPlanManager.currentItem)
                action.executionPlanManager.setExecutionPlan(executionPlan)
            executionPlan.loadItems(executionPlanItems)

        for mngr in mngrs:
            mngr.setCurrentItemIndex()

    def __call__(self, actionType=None, record=None):
        assert self.__ctx is not None, "Batch action creation work out of context"
        action = CAction(actionType=actionType, record=record)
        self.__mapAction(action)
        return action

    def __mapAction(self, action):
        if not action.executionPlanManager.initialized:
            return

        executionPlanManager = action.executionPlanManager
        epId = executionPlanManager.currentItem.masterId
        assert epId
        if epId not in self.__ctx['epIdMap']:
            executionPlan = executionPlanManager.loadExecutionPlan()
            self.__ctx['epIdMap'][epId] = executionPlan

        self.__ctx['actionListMap'].setdefault(epId, []).append(action)


class CAction(object):
    # __slots__ = ['_actionType', '_record', '_properties']

    # метод копирования свойств в действие
    actionNoMethodRecording = 0
    actionFillProperties    = 1
    actionAddProperties     = 2

    def __init__(self, actionType=None, record=None, addition_data=None, isShort=False):
        self._actionType = actionType
        self._record = None
        self._masterId = None
        self._propertiesById = {}
        self._propertiesByName = {}
        self._propertiesByShortName = {}
        self._propertiesBydataInheritance = {}
        self._propertiesByVar = {}
        self._propertiesByTest = {}
        self._propertiesById = {}
        self._executionPlanManager = CActionExecutionPlanManager(self)
        self._presetValuesConditions = {}
        self._properties = []
        self._locked = False
        self._isShort = isShort
        self.nomenclatureExpense = None
        self.nomenclatureClientReservation = None
        self._specifiedName = ''
        self._clientId = None
        self._event = None
        self._orgStructureId = None
        self._financeId = None
        self._medicalAidKindId = None
        self._attachedFileItemList = []
        self._attachedFileItemList_orig = []
        self.checkModifyDate = True
        self.nomenclatureExpensePreliminarySave = False
        self._actionTemplateId = None
        self.trailerIdx = -1
        self.deleteMark = False
        self.isNomenclatureExpenseChange = False
        self.isNomenclatureClientReservationChange = False
        self.isJobTicketChange = False
        self.valuePropertyToTemplateItems = {}
        self.groupedNomenclature = False
        self._changed = False
        if record:
            self.setRecord(record, addition_data)

    def setValuePropertyToTemplateItems(self, items):
        self.valuePropertyToTemplateItems = items


    def getValuePropertyToTemplateItems(self):
        return self.valuePropertyToTemplateItems


    def getValuePropertyToTemplate(self, templateId):
        valueProperty = []
        if templateId:
            items = self.getValuePropertyToTemplateItems()
            valueProperty = items.get(templateId, [])
        return valueProperty


    def setNomenclatureExpenseChange(self, value):
        self.isNomenclatureExpenseChange = value


    def getNomenclatureExpenseChange(self):
        return self.isNomenclatureExpenseChange


    def setNomenclatureClientReservationChange(self, value):
        self.isNomenclatureClientReservationChange = value


    def getNomenclatureClientReservationChange(self):
        return self.isNomenclatureClientReservationChange


    def setNomenclatureClientReservationPrimarySource(self, value):
        self.isNomenclatureClientReservationPrimarySource = value


    def getNomenclatureClientReservationPrimarySource(self):
        return self.isNomenclatureClientReservationPrimarySource

    
    def setNomenclatureExpensePreliminarySave(self, value):
        self.nomenclatureExpensePreliminarySave = value


    def setFreeJobTicketCourseId(self, value):
        self.freeJobTicketCourseId = value


    def getFreeJobTicketCourseId(self):
        return self.freeJobTicketCourseId


    def setJobTicketChange(self, value):
        self.isJobTicketChange = value


    def getJobTicketChange(self):
        return self.isJobTicketChange


    def actionType(self):
        return self._actionType


    @staticmethod
    def fromRecordList(recordList, formatter=lambda x: x):
        with CActionLoadingFabric() as fabric:
            return [
                formatter(fabric(record=record)) for record in recordList
            ]


    @property
    def executionPlanManager(self):
        return self._executionPlanManager


    @property
    def presetValuesConditions(self):
        return self._presetValuesConditions

    @classmethod
    def createByTypeId(cls, actionTypeId):
        actionType = CActionTypeCache.getById(actionTypeId)
        return cls(actionType=actionType)


    @classmethod
    def createByTypeCode(cls, actionTypeCode):
        actionType = CActionTypeCache.getByCode(actionTypeCode)
        return cls(actionType=actionType)


    @classmethod
    def getActionById(cls, actionId, isShort=False):
        db = QtGui.qApp.db
        actionRecord = db.getRecord('Action', '*', actionId)
        return cls(record=actionRecord, isShort=isShort) if actionRecord else None


    @classmethod
    def getAction(cls, eventId, actionTypeCode):
        db = QtGui.qApp.db
        tableAction = db.table('Action')
        actionType = CActionTypeCache.getByCode(actionTypeCode)
        cond = [tableAction['event_id'].eq(eventId), tableAction['actionType_id'].eq(actionType.id)]
        record = db.getRecordEx(tableAction, '*', cond)
        return cls(record=record, actionType=actionType)


    def setRecord(self, record, addition_data=None):
        # установить тип
        actionTypeId = forceRef(record.value('actionType_id'))
        if self._actionType:
            assert actionTypeId == self._actionType.id
        else:
            self._actionType = CActionTypeCache.getById(actionTypeId)
        if type(record) != CSqlRecord:
            record = CSqlRecord(record)
        self._record = record
        self._masterId = forceRef(record.value('master_id'))

        if not addition_data:
            addition_data = dict()
        propertyRecords = addition_data.get("propertyRecords", None)
        valueRecords = addition_data.get("valueRecords", None)
        reservationId = addition_data.get("reservationId", None)
        specialityId = addition_data.get("specialityId", None)
        executionPlanRecord = addition_data.get("executionPlanRecord", None)
        fileAttachRecords = addition_data.get("fileAttachRecords", None)
        fileAttachSignRecords = addition_data.get("fileAttachSignRecords", None)
        fileAttachPTRecords = addition_data.get("fileAttachPTRecords", None)

        # инициализировать properties
        actionId = forceRef(record.value('id'))
        if actionId:
            if propertyRecords is not None:
                for propertyRecord in propertyRecords:
                    propValueId = forceRef(propertyRecord.value('id'))
                    prop = CActionProperty(self._actionType, record=propertyRecord, actionId=actionId,
                                           valueRecords=valueRecords.get(propValueId, []))
                    self._propertiesById[prop._type.id] = prop
                    self._propertiesByName[prop._type.name] = prop
                    if prop._type.var:
                        self._propertiesByVar[prop._type.var] = prop
                    self._propertiesByTest[prop._type.testId] = prop
                    if prop._type.shortName:
                        self._propertiesByShortName[prop._type.shortName] = prop
                    if prop._type.dataInheritance:
                        self._propertiesBydataInheritance[prop._type.dataInheritance] = prop
            else:
                db = QtGui.qApp.db
                tableActionProperty = db.table('ActionProperty')
                APRecords = db.getRecordList(tableActionProperty, '*', [tableActionProperty['action_id'].eq(actionId), tableActionProperty['deleted'].eq(0)])
                dictValuesTable = {}
                dictValues = {}
                for propertyRecord in APRecords:
                    propertyTypeId = forceRef(propertyRecord.value('type_id'))
                    if self._actionType.propertyTypeIdPresent(propertyTypeId):
                        tableName = self._actionType.getPropertyTypeById(propertyTypeId).tableName
                        dictValuesTable.setdefault(tableName, []).append(forceRef(propertyRecord.value('id')))
                for key in dictValuesTable.keys():
                    valueTable = db.table(key)
                    valueRecords = db.getRecordList(valueTable, '*', valueTable['id'].inlist(dictValuesTable[key]))
                    for rec in valueRecords:
                        dictValues.setdefault(forceRef(rec.value('id')), []).append(rec)
                for propertyRecord in APRecords:
                    propertyTypeId = forceRef(propertyRecord.value('type_id'))
                    if self._actionType.propertyTypeIdPresent(propertyTypeId):
                        propValueId = forceRef(propertyRecord.value('id'))
                        prop = CActionProperty(self._actionType, record=propertyRecord, actionId=actionId, valueRecords=dictValues.get(propValueId, []))
                        self._propertiesById[prop._type.id] = prop
                        self._propertiesByName[prop._type.name] = prop
                        if prop._type.var:
                            self._propertiesByVar[prop._type.var] = prop
                        self._propertiesByTest[prop._type.testId] = prop
                        if prop._type.shortName:
                            self._propertiesByShortName[prop._type.shortName] = prop
                        if prop._type.dataInheritance:
                            self._propertiesBydataInheritance[prop._type.dataInheritance] = prop
            self._properties = self._propertiesById.values()
            self._properties.sort(key=lambda prop:prop._type.idx)
            if not self._isShort:
                if reservationId != -1:
                    self.nomenclatureClientReservation = CNomenclatureClientReservation(self).load(reservationId)

            self.setNomenclatureClientReservationPrimarySource(self.nomenclatureClientReservation is not None)
        # Добавили инициализацию пустых свойств для шаблонов печати заполнение свойств дефолтными значениями при добавлении через планировщик
        propertyTypeList = self._actionType.getPropertiesById().items()
        for propertyTypeId, propertyType in propertyTypeList:
            self.getPropertyById(propertyTypeId)

        # спец. отметки
        status = forceInt(record.value('status'))
        personId = forceRef(record.value('person_id'))
        if specialityId is None and not addition_data.has_key("specialityId"):
            specialityId = self.getSpecialityId(personId)
        if not record.isNull('id') and status == CActionStatus.finished and personId and not QtGui.qApp.userHasRight(urAdmin):
            self._locked = not ( QtGui.qApp.userId == personId
                             or (QtGui.qApp.userHasRight(urEditOtherPeopleActionSpecialityOnly) and QtGui.qApp.userSpecialityId == specialityId)
                             or QtGui.qApp.userHasRight(urEditOtherpeopleAction)
                             or (QtGui.qApp.userHasRight(urEditSubservientPeopleAction) and QtGui.qApp.userId in getPersonOrgStructureChiefs(personId))
                           )
        else:
            self._locked = False
        if not self._isShort:
            # списание ЛСиИМН
            if actionId and self._actionType.isNomenclatureExpense:
                self.nomenclatureExpense = CNomenclatureExpense(self, actionId, self._actionType,
                                                                financeId=forceRef(record.value('finance_id')),
                                                                medicalAidKindId=self._medicalAidKindId,
                                                                actionAmount=forceInt(record.value('amount')) if forceInt(
                                                                    record.value('amount')) else None,
                                                                supplierId=self._orgStructureId)

            if actionId:
                self._executionPlanManager.load(executionPlanRecord)

            self._specifiedName = forceString(record.value('specifiedName'))
            self.updateSpecifiedName()
            # прикреплённые файлы
            self._attachedFileItemList = []
            self._attachedFileItemList_orig = []
            # у скриптов типа labExchange нет таких штук, а попользоваться этими функциями хочется
            if hasattr(QtGui.qApp, 'webDAVInterface'):
                storageInterface = QtGui.qApp.webDAVInterface
                if fileAttachRecords is None:
                    self._attachedFileItemList = CAttachedFilesLoader.loadItems(storageInterface, 'Action_FileAttach', actionId)
                else:
                    self._attachedFileItemList = CAttachedFilesLoader.loadItemsFromRecords(storageInterface, fileAttachRecords, fileAttachSignRecords, fileAttachPTRecords)
                self._attachedFileItemList_orig = self._attachedFileItemList[:]


    def getSpecialityId(self, personId):
        specialityId = None
        if personId:
            db = QtGui.qApp.db
            tablePerson = db.table('Person')
            record = db.getRecordEx(tablePerson, [tablePerson['speciality_id']],
                                    [tablePerson['deleted'].eq(0), tablePerson['id'].eq(personId)])
            specialityId = forceRef(record.value('speciality_id')) if record else None
        return specialityId


    def addNomenclature(self, nomenclatureId):
        if self.nomenclatureExpense:
            self._financeId = self.getFinanceId()
            if not self._medicalAidKindId:
                self._medicalAidKindId = self.getMedicalAidKindId()
            self.nomenclatureExpense.addNomenclature(nomenclatureId, financeId=self._financeId, medicalAidKindId=self._medicalAidKindId)


    def addNomenclatureEx(self, nomenclatureId):
        if self.nomenclatureExpense:
            self._financeId = self.getFinanceId()
            if not self._medicalAidKindId:
                self._medicalAidKindId = self.getMedicalAidKindId()
            self.nomenclatureExpense.addNomenclatureEx(nomenclatureId, financeId=self._financeId, medicalAidKindId=self._medicalAidKindId)


    def updateNomenclatureDosageValue(self, nomenclatureId, dosageValue, force=False):
        if self.nomenclatureExpense:
            self.nomenclatureExpense.updateNomenclatureDosageValue(nomenclatureId, dosageValue, force)


    def removeNomenclature(self, nomenclatureId):
        if self.nomenclatureExpense:
            self.nomenclatureExpense.removeNomenclature(nomenclatureId)
    
    
    def findReactionPropertyValue(self):
        return self._findActionSelectionTableProeprtyValue(5)


    def getReactionPropertyText(self):
        return self._findActionSelectionTableProeprtyText(5)


    def setReactionPropertyValue(self, value):
        return self.setActionSelectionTablePropertyValue(5, value)


    def setCancelDatePropertyValue(self, value):
        return self.setActionSelectionTablePropertyValue(6, value)
    

    def findSignaPropertyValue(self):
        return self._findActionSelectionTableProeprtyValue(3)
    
    
    def findSignaPropertyText(self):
        return self._findActionSelectionTableProeprtyText(3)
    
    
    def findSignaCommentPropertyText(self):
        return self._findActionSelectionTablePropertyComment(3)


    def findSignaCommentTypePropertyText(self):
        return self._findActionSelectionTablePropertyCommentType(3)


    def setSignaPropertyValue(self, value):
        return self.setActionSelectionTablePropertyValue(3, value)

    
    def setSignaCommentPropertyValue(self, value):
        return self.setActionSelectionTablePropertyComment(3, value)


    def findDosagePropertyValue(self):
        return self._findActionSelectionTableProeprtyValue(2)
    
    
    def setDosagePropertyValue(self, value):
        return self.setActionSelectionTablePropertyValue(2, value)


    def findNomenclaturePropertyValue(self):
        return self._findActionSelectionTableProeprtyValue(1)

    
    def getNomenclaturePropertyText(self):
        return self._findActionSelectionTableProeprtyText(1)
    
    
    def setNomenclaturePropertyValue(self, value):
        return self.setActionSelectionTablePropertyValue(1, value)

    
    def getGroupDosesTextEx(self):
        doses = self.findDosagePropertyValue()
        name = self.getNomenclatureDosageUnitName(self.findNomenclaturePropertyValue())
        if name:
            return ' '.join([str(doses), name])
        return str(doses)


    def getNomenclatureDosageUnitName(self, nomenclatureId):
        values = self._getNomenclatureValues(nomenclatureId)
        if not values:
            return ''
        return values['dosageUnitName']


    def _getNomenclatureValues(self, nomenclatureId):
        nomenclatureData = {}
        if not nomenclatureId:
            return {
                'dosageUnitName': u'',
                'usingTypes': [],
                'dosageValue': 0.0,
                'dosageUnitId': None
                }
        if nomenclatureId not in nomenclatureData:
            db = QtGui.qApp.db
            nomenclatureRecord = db.getRecord(
                'rbNomenclature',
                'unit_id, '
                'dosageValue',
                nomenclatureId
            )
            if not nomenclatureRecord:
                nomenclatureData[nomenclatureId] = {
                    'dosageUnitName': u'',
                    'usingTypes': [],
                    'dosageValue': 0.0,
                    'dosageUnitId': None
                }
                return nomenclatureData[nomenclatureId]
            dosageUnitId = forceRef(nomenclatureRecord.value('unit_id'))
            result = {
                'dosageValue': forceDouble(nomenclatureRecord.value('dosageValue')),
                'dosageUnitId': dosageUnitId
            }
            if dosageUnitId:
                unitRecord = db.getRecord('rbUnit', 'code, name', dosageUnitId)
                name = forceString(unitRecord.value('code')) if unitRecord else u''
            else:
                name = ''
            result['dosageUnitName'] = name
            unitTypesTable = db.table('rbNomenclature_UsingType')
            tableUsingType = db.table('rbNomenclatureUsingType')
            queryUsingType = unitTypesTable.innerJoin(tableUsingType, tableUsingType['id'].eq(unitTypesTable['usingType_id']))
            unitTypesRecordList = db.getRecordList(
                queryUsingType,
                [tableUsingType['name'].alias('usingType')],
                where=unitTypesTable['master_id'].eq(nomenclatureId),
                order=unitTypesTable['idx'].name()
            )
            result['usingTypes'] = [forceStringEx(r.value('usingType')) for r in unitTypesRecordList]
            nomenclatureData[nomenclatureId] = result
        return nomenclatureData[nomenclatureId]
    

    def _findActionSelectionTableProeprtyValue(self, inActionsSelectionTable):
        actionType = self.getType()
        for propertyType in actionType.getPropertiesById().values():
            if propertyType.inActionsSelectionTable != inActionsSelectionTable:
                continue
            return self.getPropertyById(propertyType.id).getValue()
        return None


    def _findActionSelectionTablePropertyComment(self, inActionsSelectionTable):
        actionType = self.getType()
        for propertyType in actionType.getPropertiesById().values():
            if propertyType.inActionsSelectionTable != inActionsSelectionTable:
                continue
            return self.getPropertyById(propertyType.id).getComment()
        return u''


    def _findActionSelectionTablePropertyCommentType(self, inActionsSelectionTable):
        actionType = self.getType()
        for propertyType in actionType.getPropertiesById().values():
            if propertyType.inActionsSelectionTable != inActionsSelectionTable:
                continue
            return self.getPropertyById(propertyType.id).getCommentType()
        return u''


    def setActionSelectionTablePropertyComment(self, inActionsSelectionTable, value):
        actionType = self.getType()
        for propertyType in actionType.getPropertiesById().values():
            if propertyType.inActionsSelectionTable == inActionsSelectionTable:
                self.getPropertyById(propertyType.id).setComment(value)
                return self.getPropertyById(propertyType.id).getComment()


    def getSmnnUUIDPropertyValue(self):
        propertyList = self.getProperties()
        for actionProperty in propertyList:
            propertyType = actionProperty.type()
            if propertyType.isNomenclatureSmnnActionPropertyValueType():
                property = self.getPropertyById(propertyType.id)
                return property.getValue()
        return None


    def getSmnnUUIDPropertyText(self):
        propertyList = self.getProperties()
        for actionProperty in propertyList:
            propertyType = actionProperty.type()
            if propertyType.isNomenclatureSmnnActionPropertyValueType():
                property = self.getPropertyById(propertyType.id)
                return property.getText()
        return ''


    def setSmnnUUIDPropertyValue(self, value):
        propertyList = self.getProperties()
        for actionProperty in propertyList:
            propertyType = actionProperty.type()
            if propertyType.isNomenclatureSmnnActionPropertyValueType():
                self.getPropertyById(propertyType.id).setValue(value)
                return self.getPropertyById(propertyType.id).getValue()
        return None

    def getSmnnGrlsLfPropertyValue(self):
        propertyList = self.getProperties()
        for actionProperty in propertyList:
            propertyType = actionProperty.type()
            if propertyType.isNomenclatureSmnnGrlsLfActionPropertyValueType():
                property = self.getPropertyById(propertyType.id)
                return property.getValue()
        return None
    

    def getSmnnGrlsLfPropertyText(self):
        propertyList = self.getProperties()
        for actionProperty in propertyList:
            propertyType = actionProperty.type()
            if propertyType.isNomenclatureSmnnGrlsLfActionPropertyValueType():
                property = self.getPropertyById(propertyType.id)
                return property.getText()
        return ''


    def setSmnnGrlsLfPropertyValue(self, value):
        propertyList = self.getProperties()
        for actionProperty in propertyList:
            propertyType = actionProperty.type()
            if propertyType.isNomenclatureSmnnGrlsLfActionPropertyValueType():
                self.getPropertyById(propertyType.id).setValue(value)
                return self.getPropertyById(propertyType.id).getValue()
        return None


    def _findActionSelectionTableProeprtyText(self, inActionsSelectionTable):
        actionType = self.getType()
        for propertyType in actionType.getPropertiesById().values():
            if propertyType.inActionsSelectionTable != inActionsSelectionTable:
                continue
            return self.getPropertyById(propertyType.id).getText()
        return ''
    
    def setActionSelectionTablePropertyValue(self, inActionsSelectionTable, value):
        actionType = self.getType()
        for propertyType in actionType.getPropertiesById().values():
            if propertyType.inActionsSelectionTable == inActionsSelectionTable:
                self.getPropertyById(propertyType.id).setValue(value)
                return self.getPropertyById(propertyType.id).getValue()
            
    
    def getCalculationParamPropertyValue(self):
        propertyList = self.getProperties()
        for actionProperty in propertyList:
            propertyType = actionProperty.type()
            if propertyType.isNomenclatureCalculationParamActionPropertyValueType():
                property = self.getPropertyById(propertyType.id)
                return property.getValue()
        return None
    
    
    def setCalculationParamPropertyValue(self, value):
        propertyList = self.getProperties()
        for actionProperty in propertyList:
            propertyType = actionProperty.type()
            if propertyType.isNomenclatureCalculationParamActionPropertyValueType():
                self.getPropertyById(propertyType.id).setValue(value)
                return self.getPropertyById(propertyType.id).getValue()
        return None


    def isNomenclatureUsingTypeActionPropertyValueType(self):
        actionType = self.getType()
        for propertyType in actionType.getPropertiesById().values():
            if propertyType.isNomenclatureUsingTypeActionPropertyValueType():
                return True
        return False
    
    
    def getStockMotionRecord(self):
        return self.nomenclatureExpense.stockMotionRecord() if self.nomenclatureExpense else None


    def getStockMotionItemList(self):
        return self.nomenclatureExpense.stockMotionItems() if self.nomenclatureExpense else []


    def initNomenclature(self, clientId, financeId=None, medicalAidKindId=None):
        if self._actionType and self._actionType.isNomenclatureExpense:
            self.nomenclatureExpense = CNomenclatureExpense(self, None, self._actionType, clientId=clientId, financeId=financeId, medicalAidKindId=medicalAidKindId, supplierId=self._orgStructureId)
        else:
            self.nomenclatureExpense = None

    def _getNewRecord(self):
        db = QtGui.qApp.db
        tableAction = db.table('Action')
        record = tableAction.newRecord()
        record.setValue('actionType_id', QVariant(self._actionType.id))
        record.setValue('specifiedName', QVariant(self._specifiedName))
        return record

    def cancel(self):
        # Вот в случае разных отмен, не сохранения действия, тут нужно зависимости подчищать.
        if self.nomenclatureExpense:
            self.nomenclatureExpense.cancel()
            self.nomenclatureExpense = None
        if self.nomenclatureClientReservation:
            self.nomenclatureClientReservation.cancel()
            self.nomenclatureClientReservation = None
    
    
    def checkRecordChanged(self):
        if type(self._record) == CSqlRecord:
            return self._record.isDirty()
        return False
    
    
    def setChanged(self, value):
        self._changed = value


    def isChanged(self):
        return self._changed
    
    
    def nomenclatureClientReservationCancel(self):
        if self.nomenclatureClientReservation:
            self.nomenclatureClientReservation.cancel()
            self.nomenclatureClientReservation = None


    def save(self, eventId=None, idx=0, checkModifyDate = True):
        self._changed = self._changed or self.checkRecordChanged()
        db = QtGui.qApp.db
        id = forceRef(self._record.value('id')) if self._record else None
        
        if self._record:
            for property in self._propertiesById.itervalues():
                if property._changed:
                    self._changed = True
                    self._record._dirty = True
                    break
            if checkFileAttachListChanged(self._attachedFileItemList, self._attachedFileItemList_orig):
                self._changed = True
                self._record._dirty = True
        if id and not self._changed:
            return id

        # попытка спасти затирающиеся ИБМ в выполнении работ
        if id and checkModifyDate and self.checkModifyDate and self.actionType().hasJobTicketPropertyType():
            curRec = db.getRecord('Action', ['takenTissueJournal_id', 'status'], id)
            if curRec:
                ttjId = forceRef(curRec.value(0))
                status = forceRef(curRec.value(1))
                if ttjId and forceRef(self._record.value('takenTissueJournal_id')) is None and forceString(QtGui.qApp.db.translate('TakenTissueJournal', 'id', ttjId, 'externalId')) != '':
                    QtGui.qApp.log(u'Предупреждение ', u'Действие с id %i не сохранено, так как была попытка стереть ИБМ' % id)
                    return id

        if id and checkModifyDate and self.checkModifyDate:
            curRec = db.getRecord('Action', ['modifyDatetime', 'modifyPerson_id'], id)
            if curRec:
                modDT = forceDateTime(curRec.value(0))
                modPerson = forceInt(curRec.value(1))
                if modDT.isValid() and modDT != forceDateTime(self._record.value('modifyDatetime')):
                    if hasattr(QtGui.qApp, 'log'):
                        QtGui.qApp.log(u'Предупреждение ', u'Действие с id %i не сохранено, так как дата модификации записи отличается. Изменивший пользователь на момент открытия %i, на момент сохранения %i'
                                      % (id, forceInt(self._record.value('modifyPerson_id')), modPerson))
                    return id
                
        if self._locked:
            # для заблокированной записи сохраняем только idx (позиция в списке на экране) и master_id из-за откреплений
            id = forceRef(self._record.value('id'))
            if idx != -1:
                self._record.setValue('idx', QVariant(idx))
                db.query('UPDATE Action SET idx=%d WHERE id=%d' % (idx, id))
            master_id = forceRef(self._record.value('master_id'))
            if master_id:
                db.query('UPDATE Action SET master_id=%d WHERE id=%d' % (master_id, id))
            if not self._isShort and QtGui.qApp.userHasRight(urCanAttachFile):
                if hasattr(QtGui.qApp, 'webDAVInterface'):
                    storageInterface = QtGui.qApp.webDAVInterface
                    CAttachedFilesLoader.saveItems(storageInterface, 'Action_FileAttach', id,
                                                   self._attachedFileItemList)
            self._changed = False
            if self._record:
                self._record._dirty = False
            for prop in self._propertiesById.itervalues():
                prop._changed = False
                if hasattr(prop, '_normChanged'):
                    prop._normChanged = False
                    
            return id
        else:
            # сохранить основную запись
            tableAction = db.table('Action')
            if not self._record:
                self._record = self._getNewRecord()
            if eventId:
                self._record.setValue('event_id', QVariant(eventId))
            else:
                eventId = forceRef(self._record.value('event_id'))
            if idx != -1:
                #TODO как насчет использовать None для определения случая не изменять порядковый номер?
                self._record.setValue('idx', QVariant(idx))

            # TT 1029 "Автоматическое добавление статуса наблюдения"
            if self.actionType().code in ('reanimation', 'vacation'):
                tableObservationType = db.table('rbStatusObservationClientType')
                tableClientStatusObservation = db.table('Client_StatusObservation')
                statusTypeRecord = db.getRecordEx(tableObservationType, 'id', tableObservationType['code'].eq(self.actionType().code))
                statusId = forceRef(statusTypeRecord.value('id')) if statusTypeRecord else None
                if statusId:
                    if id is None and forceInt(self._record.value('status')) == 0:
                        db.deleteRecord(tableClientStatusObservation, tableClientStatusObservation['master_id'].eq(self.event.client_id))
                        observationRecord = tableClientStatusObservation.newRecord()
                        observationRecord.setValue('master_id', QVariant(self.event.client_id))
                        observationRecord.setValue('statusObservationType_id', QVariant(statusId))
                        db.insertRecord(tableClientStatusObservation, observationRecord)
                    elif id is not None and forceInt(self._record.value('status')) != 0:
                        db.deleteRecord(tableClientStatusObservation,
                                        db.joinAnd([tableClientStatusObservation['master_id'].eq(self.event.client_id),
                                                    tableClientStatusObservation['statusObservationType_id'].eq(statusId),
                                                    tableClientStatusObservation['createDatetime'].le(self._record.value('createDatetime'))
                                                    ]))

            # Это хак: удаляем payStatus из записи
            tmpRecord = type(self._record)(self._record) # copy record
            tmpRecord.remove(tmpRecord.indexOf('payStatus'))
            id = db.insertOrUpdate(tableAction, tmpRecord)
            self._record.setValue('id', toVariant(id))
            if id:
                self._record = db.getRecordEx(tableAction, '*', [tableAction['id'].eq(id), tableAction['deleted'].eq(0)])

            # для обновления данных в модели при нажатии кнопки "применить"
            for fieldName in [CDocumentTable.dtfCreateDatetime, CDocumentTable.dtfCreateUserId, CDocumentTable.dtfModifyDatetime, CDocumentTable.dtfModifyUserId]:
                self._record.setValue(fieldName, tmpRecord.value(fieldName))
            if not forceRef(self._record.value('expose')):
                self._record.setValue('expose', toVariant(1))

            propertiesIdList = []

            # сохранить записи свойств
            for property in self._propertiesById.itervalues():
                changed = property._changed or property._normChanged
                propertyId = property.save(id)
                if propertyId:
                    propertiesIdList.append(propertyId)
                if changed:
                    # сохраняем отделение в номерке на работу
                    if property.type().isJobTicketValueType() and property.getValue() and eventId:
                        recordJT = db.getRecord('Job_Ticket', '*', property.getValue())
                        if recordJT:
                            begDateJT = forceDateTime(recordJT.value('dateTime'))
                            execOrgStructureId = None
                            if QtGui.qApp.checkGlobalPreference('23:orgStructJobTickets', u'да'):
                                personId = forceRef(self._record.value('setPerson_id'))
                                execOrgStructureId = forceRef(db.translate('Person', 'id', personId, 'orgStructure_id'))
                            else:
                                actionTypeIdList = None
                                tableEvent = db.table('Event')
                                tableEventType = db.table('EventType')
                                tableRBMedicalAidType = db.table('rbMedicalAidType')
                                queryTable = tableEvent.innerJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
                                queryTable = queryTable.innerJoin(tableRBMedicalAidType, tableRBMedicalAidType['id'].eq(tableEventType['medicalAidType_id']))
                                condMAT = [tableEvent['id'].eq(eventId),
                                           tableEvent['deleted'].eq(0),
                                           tableEventType['deleted'].eq(0),
                                           tableRBMedicalAidType['code'].inlist(['1', '2', '3', '7'])
                                           ]
                                recordMAT = db.getRecordEx(queryTable, [tableRBMedicalAidType['id']], condMAT)
                                matId = forceRef(recordMAT.value('id')) if recordMAT else None
                                if matId:
                                    actionTypeList = getActionTypeIdListByFlatCode(u'moving%')
                                    actionTypeIdList = (','.join(str(actionTypeId) for actionTypeId in actionTypeList if actionTypeId))
                                    # if self._record and not forceInt(self._record.value('medicalAidKind_id')):
                                    #     self._record.setValue('medicalAidKind_id', QVariant(matId))
                                if actionTypeIdList and matId:
                                    nameProperty = u'''Отделение пребывания'''
                                    stmt = '''
                                            SELECT (SELECT APOS.value
                                            FROM ActionPropertyType AS APT
                                            INNER JOIN ActionProperty AS AP ON AP.type_id=APT.id
                                            INNER JOIN ActionProperty_OrgStructure AS APOS ON APOS.id=AP.id
                                            WHERE APT.actionType_id=Action.actionType_id AND AP.action_id=Action.id AND APT.deleted=0
                                            AND APT.name = '%s') AS execOrgStructureId
                                            FROM Event
                                            INNER JOIN Action ON Event.id = Action.event_id
                                            WHERE Event.id = %d AND Action.deleted = 0 AND Event.deleted = 0 AND Action.actionType_id IN (%s)
                                            AND Action.begDate <= %s AND (Action.endDate IS NULL OR Action.endDate > %s)
                                            ORDER BY Action.id DESC
                                            LIMIT 1
                                            '''%(nameProperty, eventId, actionTypeIdList, db.formatDate(begDateJT), db.formatDate(begDateJT))
                                    query = db.query(stmt)
                                    if query.next():
                                        execOSRecord = query.record()
                                        execOrgStructureId = forceRef(execOSRecord.value('execOrgStructureId')) if execOSRecord else None
                                if not execOrgStructureId and matId:
                                    execOrgStructureId = QtGui.qApp.currentOrgStructureId()
#
                                if not execOrgStructureId:
                                    execOrgStructureId = QtGui.qApp.userOrgStructureId
                            if execOrgStructureId:
                                recordJT.setValue('orgStructure_id', toVariant(execOrgStructureId))
                                db.updateRecord('Job_Ticket', recordJT)
            if not self._isShort or self.groupedNomenclature:
                if self.actionType().isDoesNotInvolveExecutionCourse:
                    self._executionPlanManager.saveFromCurrentItems()
                else:
                    self._executionPlanManager.save()

            # удалить записи свойств кроме сохранённых
            tableActionProperty = db.table('ActionProperty')
            if propertiesIdList:
                db.deleteRecord(tableActionProperty,
                                 [tableActionProperty['action_id'].eq(id),
                                   tableActionProperty['id'].notInlist(propertiesIdList)])
            else:
                db.deleteRecord(tableActionProperty,
                                 [tableActionProperty['action_id'].eq(id)])

            if not self._isShort:
                # списание ЛСиИМН
                if self._record and self.saveNomenclatureExpense(self.nomenclatureExpensePreliminarySave):
                    db.updateRecord(tableAction, self._record)
                    
            if not self._isShort or self.groupedNomenclature:
                self.updateNomenclatureClientReservation()
                if self.groupedNomenclature:
                    self.nomenclatureExpense._releaseReservation()

            if not self._isShort:
                # проверка прикреплённых файлов
                if hasattr(QtGui.qApp, 'webDAVInterface'): # у скриптов типа labExchange нет таких штук, а попользоваться этими функциями хочется
                    storageInterface = QtGui.qApp.webDAVInterface
                    CAttachedFilesLoader.saveItems(storageInterface, 'Action_FileAttach', id, self._attachedFileItemList)
            
            self._changed = False
            if self._record:
                self._record._dirty = False
            for prop in self._propertiesById.itervalues():
                prop._changed = False
                if hasattr(prop, '_normChanged'):
                    prop._normChanged = False
            
            return id

    def updateNomenclatureClientReservation(self):
        if not self.nomenclatureClientReservation:
            return

        self.nomenclatureClientReservation.linkAction(self)

    def saveNomenclatureExpense(self, nomenclatureExpensePreliminarySave = False, isActionNoSave = False):
        status = forceInt(self.getRecord().value('status'))
        if self.nomenclatureExpense:
            if not self._actionType.generateAfterEventExecDate or bool(self._actionType.generateAfterEventExecDate and self.event.execDate):
                if self.nomenclatureExpense and status == CActionStatus.finished and (
                        self.nomenclatureExpense.getStockMotionId() or self.nomenclatureExpense.stockMotionItems()
                ):
                    if QtGui.qApp.controlSMFinance() in (1, 2):
                        self._financeId = self.getFinanceId()
                    self._medicalAidKindId = self.getMedicalAidKindId()
                    stockMotionId = self.nomenclatureExpense.save(nomenclatureExpensePreliminarySave, isActionNoSave = isActionNoSave)
                    if stockMotionId:
                        if not self._record:
                            self._record = self._getNewRecord()
                        prevStockMotionId = forceRef(self._record.value('stockMotion_id'))
                        self._record.setValue('prevStockMotion_id', toVariant(prevStockMotionId))
                        self._record.setValue('stockMotion_id', toVariant(stockMotionId))
                        return True
                elif status == CActionStatus.canceled:
                    self.cancel()

        return False


    def getType(self):
        return self._actionType
    
    
    def getMasterId(self):
        return self._masterId


    def setMasterId(self, masterId):
        self._masterId = masterId


    def getRecord(self):
        return self._record

    @property
    def idx(self):
        return forceInt(self._record.value('idx')) if self._record else None


    def getId(self):
        return forceRef(self._record.value('id')) if self._record else None


    def getPrescriptionId(self):
        return forceRef(self._record.value('prescription_id')) if self._record else None


    def getPrevActionId(self):
        return forceRef(self._record.value('prevAction_id')) if self._record else None


    def getBegDate(self):
        return forceDate(self._record.value('begDate')) if self._record else None


    def getBegDatetime(self):
        return forceDateTime(self._record.value('begDate')) if self._record else None


    def getEndDate(self):
        return forceDate(self._record.value('endDate')) if self._record else None


    def getEndDatetime(self):
        return forceDateTime(self._record.value('endDate')) if self._record else None


    def getPersonId(self):
        return forceRef(self._record.value('person_id')) if self._record else None


    def getSetPersonId(self):
        return forceRef(self._record.value('setPerson_id')) if self._record else None


    def getCreatePersonId(self):
        return forceRef(self._record.value('createPerson_id')) if self._record else None


    def getModifyPersonId(self):
        return forceRef(self._record.value('modifyPerson_id')) if self._record else None


    def getOwnerPersonId(self):
        if self._record:
            personId = forceRef(self._record.value('person_id'))
            if not personId:
                personId = forceRef(self._record.value('setPerson_id'))
                if not personId:
                    personId = forceRef(self._record.value('createPerson_id'))
            return personId
        return None


    def getEventId(self):
        return forceRef(self._record.value('event_id')) if self._record else None


    def getFinanceId(self):
        return forceRef(self._record.value('finance_id')) if self._record else None

    def getMedicalAidKindId(self, eventTypeId = None):
        if self._medicalAidKindId:
            return self._medicalAidKindId
        else:
            return forceRef(self._record.value('medicalAidKind_id')) if self._record else None

    def getDirectionDate(self):
        return forceDateTime(self._record.value('directionDate')) if self._record else None

    def getActionTypeGroupId(self):
        return forceRef(self._record.value('actionTypeGroup_id')) if self._record else None


    def setDirectionDate(self, directionDate):
        assert self._record
        self._record.setValue('directionDate', toVariant(directionDate))

    @property
    def event(self):
        if self._event:
            return self._event

        eventId = self.getEventId()
        if not eventId:
            return None

        eventRecord = QtGui.qApp.db.getRecord(CEvent.tableName, '*', eventId)
        if not eventRecord:
            return None

        self._event = CEvent(eventRecord)
        return self._event


    def setDuration(self, value):
        self._record.setValue('duration', toVariant(value))


    def getDuration(self):
        return forceInt(self._record.value('duration'))


    def setOrgStructureId(self, value):
        self._orgStructureId = value
        self._record.setValue('orgStructure_id', toVariant(value))


    def getOrgStructureId(self):
        self._orgStructureId = forceRef(self._record.value('orgStructure_id'))
        return self._orgStructureId


    def setFinanceId(self, value):
        self._financeId = value
        self._record.setValue('finance_id', toVariant(value))


    def setMedicalAidKindId(self, value):
        self._medicalAidKindId = value
        self._record.setValue('medicalAidKind_id', toVariant(value))


    def setQuantity(self, value):
        self._record.setValue('quantity', toVariant(value))


    def getQuantity(self):
        return forceInt(self._record.value('quantity'))


    def setAliquoticity(self, value):
        self._record.setValue('aliquoticity', toVariant(value))


    def getAliquoticity(self):
        return forceInt(self._record.value('aliquoticity'))


    def setPeriodicity(self, value):
        self._record.setValue('periodicity', toVariant(value))


    def getPeriodicity(self):
        return forceInt(self._record.value('periodicity'))


    def setNote(self, value):
        self._record.setValue('note', toVariant(value))


    def getNote(self):
        return forceInt(self._record.value('note'))


    def isLocked(self):
        return self._locked

    def isCanDeletedByUser(self):
        res = True
        if self.getId():
            personId = self.getOwnerPersonId()
            res = personId == QtGui.qApp.userId or QtGui.qApp.userHasRight(urDeleteNotOwnActions)
            if res and self.findFireableJobTicketId():
                return QtGui.qApp.userHasRight(urDeleteActionsWithJobTicket)
        return res


    def isExposed(self):
        payStatus = forceInt(self._record.value('payStatus')) if self._record else 0
        actionId = forceRef(self._record.value('id')) if self._record else None
        eventId = forceRef(self._record.value('event_id')) if self._record else None
        if not payStatus and actionId and eventId:
            db = QtGui.qApp.db
            table = db.table('Action')
            cond = [ table['event_id'].eq(eventId),
                     table['id'].eq(actionId),
                     table['payStatus'].ne(0),
                     table['deleted'].eq(0)
                   ]
            record = db.getRecordEx(table, [table['payStatus']], where=cond)
            payStatus = forceInt(record.value('payStatus')) if record else 0
        if payStatus and not QtGui.qApp.userHasRight(urEditAfterInvoicingEvent):
            return True
        return False


    def getSpecifiedName(self):
        return self._specifiedName


    def getAttachedFileItemList(self):
        return self._attachedFileItemList


    def getProperties(self):
        return self._properties


    def getPropertiesById(self):
        return self._propertiesById


    def getPropertiesByName(self):
        return self._propertiesByName


    def getPropertiesByShortName(self):
        return self._propertiesByShortName


    def getPropertiesBydataInheritance(self):
        return self._propertiesBydataInheritance


    def getPropertiesByVar(self):
        return self._propertiesByVar


    def getFilledPropertiesCount(self):
        count = 0
        for prop in self._propertiesById.itervalues():
            if prop.getValue():
                count += 1
        return count


    def getAssignedPropertiesCount(self):
        count = 0
        for prop in self._propertiesById.itervalues():
            if prop.isAssigned():
                count += 1
        return count


    def hasProperty(self, name):
        return self._actionType.hasProperty(name)


    def getPropertyByIndex(self, index):
        return self._properties[index]


    def getIndexByProperty(self, property):
        return self._properties.index(property)


    def _addProperty(self, propertyType):
        result = CActionProperty(self._actionType, type=propertyType, actionId=forceRef(self._record.value('id') if self._record else None))
        self._propertiesById[propertyType.id] = result
        self._propertiesByName[propertyType.name] = result
        if propertyType.var:
            self._propertiesByVar[propertyType.var] = result
        self._propertiesByTest[propertyType.testId] = result
        if propertyType.shortName:
            self._propertiesByShortName[propertyType.shortName] = result
        if propertyType.dataInheritance:
            self._propertiesBydataInheritance[propertyType.dataInheritance] = result
        self._properties.append(result)
        self._properties.sort(key=lambda prop:prop._type.idx)
        return result


    def getPropertyById(self, id):
        result = self._propertiesById.get(id, None)
        if not result:
            propertyType = self._actionType.getPropertyTypeById(id)
            result = self._addProperty(propertyType)
        return result
        
        
    def getProperty(self, name):
        result = self._propertiesByName.get(name, None)
        if not result:
            propertyType = self._actionType.getPropertyType(name)
            result = self._addProperty(propertyType)
        return result


    def getPropertyByTest(self, testId):
        result = self._propertiesByTest.get(testId, None)
        if not result:
            propertyType = self._actionType.getPropertyTypeByTest(testId)
            if propertyType:
                result = CActionProperty(self._actionType, type=propertyType, actionId=forceRef(self._record.value('id') if self._record else None))
                self._propertiesByName[propertyType.name] = result
                self._propertiesById[propertyType.id] = result
                self._propertiesByTest[propertyType.testId] = result
                if propertyType.shortName:
                    self._propertiesByShortName[propertyType.shortName] = result
                self._properties.append(result)
                self._properties.sort(key=lambda prop:prop._type.idx)
        return result


    def getPropertyByShortName(self, shortName):
        result = self._propertiesByShortName.get(shortName, None)
        if not result:
            propertyType = self._actionType.getPropertyTypeByShortName(shortName)
            if propertyType:
                result = CActionProperty(self._actionType, type=propertyType, actionId=forceRef(self._record.value('id') if self._record else None))
                self._propertiesByName[propertyType.name] = result
                self._propertiesById[propertyType.id] = result
                self._propertiesByShortName[propertyType.shortName] = result
                if propertyType.testId:
                    self._propertiesByTest[propertyType.testId] = result
                self._properties.append(result)
                self._properties.sort(key=lambda prop:prop._type.idx)
        return result


#    def getPropertyByVar(self, var):
#        result = self._propertiesByVar.get(var, None)
#        if not result:
#            propertyType = self._actionType.getPropertyTypeByVar(name)
#            result = self._addProperty(propertyType)
#        return result


    def getExecutionPlan(self):
        if hasattr(self._executionPlanManager.executionPlan, 'items'):
            items = self._executionPlanManager.executionPlan.items
            if items:
                #sortedItemsByDate = sorted(items, key=lambda x: x.date, reverse=False)
                sortedItemsByDate = sorted(items, key=lambda x: (x.date.toPyDate(), x.idx, x.aliquoticityIdx), reverse=False)
                self._executionPlanManager.executionPlan.items = sortedItemsByDate
        return self._executionPlanManager.executionPlan


    def setExecutionPlanItem(self, executionPlanItem):
        if self._executionPlanManager.initialized:
            raise RuntimeError()
        self._executionPlanManager.setCurrentItem(executionPlanItem)


    def updateDosageFromExecutionPlan(self):
        dosage = self._executionPlanManager.getCurrentDosage()
        if dosage is None:
            return
        actionType = self.getType()
        for propertyType in actionType.getPropertiesById().values():
            if propertyType.inActionsSelectionTable == _DOSES:
                self.getPropertyById(propertyType.id).setValue(dosage)
                return

    def minExecutionPlanDate(self):
        return self._executionPlanManager.minExecutionPlanDate()

    def isStarted(self):
        return forceInt(self._record.value('status')) == CActionStatus.started

    def isFinished(self):
        return forceInt(self._record.value('status')) == CActionStatus.finished


    def defaultExecutionPlanCount(self):
        if self.getType().isNomenclatureExpense:
            return self._executionPlanManager.defaultExecutionPlanCountNE()
        else:
            return self._executionPlanManager.defaultExecutionPlanCount()


    def updateExecutionPlanByRecord(self, forceDuration=False, daysExecutionPlan=[]):
        self._executionPlanManager.update(forceDuration, daysExecutionPlan=daysExecutionPlan)

    def __getitem__(self, name):
        return self.getProperty(name).getValue()

    def __setitem__(self, name, value):
        property = self.getProperty(name)
        property.setValue(value)

    def __delitem__(self, name):
        if name in self._propertiesByName:
            property = self._propertiesByName[name]
            del self._propertiesById[property.type().id]
            del self._propertiesByName[name]
            if property.type().var and property.type().var in self._propertiesByVar:
                del self._propertiesByVar[property.type().var]
            if property.type().testId and property.type().testId in self._propertiesByTest:
                del self._propertiesByTest[property.type().testId]
            if property.type().shortName and property.type().shortName in self._propertiesByShortName:
                del self._propertiesByShortName[property.type().shortName]
            if property.type().dataInheritance and property.type().dataInheritance in self._propertiesBydataInheritance:
                del self._propertiesBydataInheritance[property.type().dataInheritance]
            self._properties.remove(property)


    def get(self, name, default=None):
        if self.hasProperty(name):
            return self.getProperty(name).getValue()
        else:
            return default

    def initPropertiesBySameAction(self, action):
        for property in action._properties:
            propertyType = property._type

            name = propertyType.name
            if name and propertyType.canBeInitializedBySameAction:
                if not self[name]:
                    self[name] = action[name]

                self.getProperty(name).applyDependents(self)
                if propertyType.isActionNameSpecifier:
                    self.updateSpecifiedName()


    def updateByTemplate(self, templateId, checkPropsOnOwner=True, clientSex = None, clientAge = None):
        db = QtGui.qApp.db
        templateActionId = forceRef(db.translate('ActionTemplate', 'id', templateId, 'action_id'))
        self.updateByActionId(templateActionId, checkPropsOnOwner, clientSex, clientAge)


    def updateByActionId(self, actionId, checkPropsOnOwner=False, clientSex = None, clientAge = None):
        db = QtGui.qApp.db
        templateRecord = db.getRecord('Action', '*', actionId)
        if templateRecord:
            if not clientSex and not clientAge:
                from Registry.Utils        import getClientSexAge
                clientId = self.event.client_id if self.event else self._presetValuesConditions.get('clientId', None)
                clientSex, clientAge = getClientSexAge(clientId)
            templateAction = CAction(record=templateRecord)
            self.updateByAction(templateAction, checkPropsOnOwner, clientSex, clientAge)


    def updateByAction(self, templateAction, checkPropsOnOwner=False, clientSex=None, clientAge=None, isMethodRecording=0, isNomenclatureExpense=True):
        canCopyPropertyList = []
        if checkPropsOnOwner:
            setPersonId = forceRef(self.getRecord().value('setPerson_id'))
        if isNomenclatureExpense:
            self.nomenclatureExpense = templateAction.nomenclatureExpense

        for id, targetPropertyType in self._actionType._propertiesById.iteritems():
            sourceProperty =(targetPropertyType.applicable(clientSex, clientAge) and
                            ( templateAction._propertiesById.get(id) or
                               templateAction._propertiesByName.get(targetPropertyType.name)
                             ))
            canCopy = (targetPropertyType.valueType.isCopyable
                       and sourceProperty
                       and targetPropertyType.valueType.variantType == sourceProperty.type().valueType.variantType
                      )
            if checkPropsOnOwner and canCopy and targetPropertyType.canChangeOnlyOwner == 1:
                canCopy = setPersonId == QtGui.qApp.userId
            if canCopy:
                targetProperty = self.getPropertyById(id)
                if isMethodRecording == CAction.actionFillProperties:
                    targetProperty.copyIfNotIsspace(sourceProperty)
                elif isMethodRecording == CAction.actionAddProperties:
                    targetProperty.copyIfString(sourceProperty)
                else:
                    targetProperty.copy(sourceProperty)
                if sourceProperty and sourceProperty not in canCopyPropertyList:
                    canCopyPropertyList.append(sourceProperty)
        if canCopyPropertyList:
            self.setChanged(True)
        return canCopyPropertyList


    def clone(self):
        newAction = CAction(actionType=self.getType())
        for id in self._propertiesById:
            property = newAction.getPropertyById(id)
            if property.type().valueType.isCopyable:
                property.copy(self._propertiesById[id])
        return newAction


    def findFireableJobTicketId(self):
        for property in self._properties:
            if property.type().isJobTicketValueType():
                jobTicketId = property.getValue()
                if jobTicketId:
                    return jobTicketId
        return None


    def getTestProperties(self):
        return [property
                for property in self._properties
                if property.type().testId and property.isAssigned()
               ]


    def updateSpecifiedName(self):
        name = ' '.join([forceString(property.getText())
                         for property in self._properties
                         if property.isActionNameSpecifier() and property.getValue()
                        ]
                       )
        self.setSpecifiedName(name)


    def setSpecifiedName(self, name):
        if self._record:
            self._record.setValue('specifiedName', QVariant(name))
        self._specifiedName = name


    def initPresetValues(self):
        actionType = self.getType()
        if actionType:
            propertyTypeList = actionType.getPropertiesById().values()
            for propertyType in propertyTypeList:
                if propertyType.valueType.initPresetValue:
                    prop = self.getPropertyById(propertyType.id)
                    prop.setPresetValue(self)

    def maxPropertiesCourse(self):
        actionType = self.getType()
        if actionType:
            propertyTypeList = actionType.getPropertiesById().values()
            return max(pt.course for pt in propertyTypeList)
        return None


    def simpleInitNomenclatureReservation(self, clientId, dosage=None, financeId=None, medicalAidKindId=None, supplierId=None, markToUpdate=False):
        if self.nomenclatureClientReservation is None:
            self.nomenclatureClientReservation = CNomenclatureClientReservation(self, clientId=clientId, financeId=financeId, medicalAidKindId=medicalAidKindId, supplierId=supplierId, markToUpdate=markToUpdate).init(dosage)


    def initNomenclatureReservation(self, clientId, dosage=None, financeId=None, medicalAidKindId=None, supplierId=None, markToUpdate=False):
        if self.nomenclatureClientReservation is None:
            if not QtGui.qApp.isGenerateNomenclatureReservation():
                self.nomenclatureClientReservation = CNomenclatureClientReservation(self, clientId=clientId, financeId=financeId, medicalAidKindId=medicalAidKindId, supplierId=supplierId, markToUpdate=markToUpdate).init(dosage)
            elif QtGui.qApp.isGenerateNomenclatureReservation() == 1:
                buttons = QtGui.QMessageBox.Yes|QtGui.QMessageBox.No | QtGui.QMessageBox.Cancel
                widget = QtGui.qApp.activeModalWidget() or QtGui.qApp.mainWindow or None
                nomenclatureId = self.findNomenclaturePropertyValue()
                if nomenclatureId:
                    nomenclatureName = forceString(QtGui.qApp.db.translate('rbNomenclature', 'id', nomenclatureId, 'name'))
                    result = QtGui.QMessageBox.question(widget,
                                                u'Внимание!',
                                                u'Выполнить резервирование %s?'%nomenclatureName,
                                                buttons,
                                                QtGui.QMessageBox.Cancel)
                    if result == QtGui.QMessageBox.Cancel:
                        self.deleteMark = True
                    elif result == QtGui.QMessageBox.Yes:
                        self.nomenclatureClientReservation = CNomenclatureClientReservation(self, clientId=clientId, financeId=financeId, medicalAidKindId=medicalAidKindId, supplierId=supplierId, markToUpdate=markToUpdate).init(dosage)


    def releaseNomenclatureReservation(self, nomenclatureId):
        if self.nomenclatureClientReservation is not None and nomenclatureId:
            self.nomenclatureExpense._releaseReservationToNomenclatureId(nomenclatureId)


    def nomenclatureReservationFromAction(self, anotherAction, financeId=None, medicalAidKindId=None, supplierId=None):
        if self.nomenclatureClientReservation is None:
            self.nomenclatureClientReservation = CNomenclatureClientReservation(self, financeId=financeId, medicalAidKindId=medicalAidKindId, supplierId=supplierId).fromAction(anotherAction)

    def updatePresetValuesConditions(self, conditions):
        self._presetValuesConditions.update(conditions)


    def getJobEndDate(self, jobTicketId=None):
        actionType = self.getType()
        if jobTicketId is None:
            propertyTypeList = actionType.getPropertiesById().values() if actionType else []
            for propertyType in propertyTypeList:
                if propertyType.isJobTicketValueType():
                    property = self.getPropertyById(propertyType.id)
                    jobTicketId = property.getValue()
                    break

        if jobTicketId:
            db = QtGui.qApp.db
            date = forceDate(db.translate('Job_Ticket', 'id', jobTicketId, 'datetime'))
            ticketDuration = actionType.ticketDuration
            if not ticketDuration:
                jobId = forceRef(db.translate('Job_Ticket', 'id', jobTicketId, 'master_id'))
                jobTypeId = forceRef(db.translate('Job', 'id', jobId, 'jobType_id'))
                ticketDuration = forceInt(db.translate('rbJobType', 'id', jobTypeId, 'ticketDuration'))
            return date.addDays(ticketDuration)
        return None

    def getJobOrgStructureId(self, jobTicketId=None):
        orgStructureId = None
        actionType = self.getType()
        if jobTicketId is None:
            propertyTypeList = actionType.getPropertiesById().values() if actionType else []
            for propertyType in propertyTypeList:
                if propertyType.isJobTicketValueType():
                    property = self.getPropertyById(propertyType.id)
                    jobTicketId = property.getValue()
                    break
        if jobTicketId:
            db = QtGui.qApp.db
            tableJT = db.table('Job_Ticket')
            tableJ = db.table('Job')
            tableQuery = tableJ.innerJoin(tableJT, tableJ['id'].eq(tableJT['master_id']))
            record = db.getRecordEx(tableQuery, [tableJ['orgStructure_id']], [tableJT['id'].eq(jobTicketId), tableJ['deleted'].eq(0), tableJT['deleted'].eq(0)])
            orgStructureId = forceRef(record.value('orgStructure_id')) if record else None
        return orgStructureId


    def getJobTicketOrgStructureId(self, jobTicketId=None, cachedFreeJobTicket=[]):
        orgStructureId = None
        jobTicketIdList = []
        actionType = self.getType()
        if jobTicketId is None or jobTicketId in cachedFreeJobTicket:
            propertyTypeList = actionType.getPropertiesById().values() if actionType else []
            for propertyType in propertyTypeList:
                if propertyType.isJobTicketValueType():
                    property = self.getPropertyById(propertyType.id)
                    jobTicketId = property.getValue()
                    if jobTicketId and jobTicketId not in cachedFreeJobTicket:
                        jobTicketIdList.append(jobTicketId)
        if not jobTicketIdList and jobTicketId and jobTicketId not in cachedFreeJobTicket:
            jobTicketIdList = list(set(jobTicketIdList)|set([jobTicketId]))
        if jobTicketIdList:
            db = QtGui.qApp.db
            tableJT = db.table('Job_Ticket')
            cond = [tableJT['id'].inlist(jobTicketIdList),
                    tableJT['id'].notInlist(cachedFreeJobTicket),
                    tableJT['status'].eq(CJobTicketStatus.done),
                    tableJT['orgStructure_id'].isNotNull(),
                    tableJT['deleted'].eq(0)
                    ]
            record = db.getRecordEx(tableJT, [tableJT['orgStructure_id']], cond, tableJT['datetime'].name())
            orgStructureId = forceRef(record.value('orgStructure_id')) if record else None
        return orgStructureId


    def checkOptimisticLock(self):
        id = self.getId()
        if not id:
            return True

        record = QtGui.qApp.db.getRecord('Action', 'modifyDatetime', id)
        if not record:
            return True

        modifyDatetime = forceDateTime(record.value('modifyDatetime'))

        return modifyDatetime == forceDateTime(self._record.value('modifyDatetime'))


    def finishAction(self, clientId, date=None):
        if not self._record:
            return None
        if date:
            self._record.setValue('endDate', toVariant(date))
        else:
            self._record.setValue('endDate', toVariant(QtCore.QDateTime.currentDateTime()))

        self._record.setValue('status', toVariant(CActionStatus.finished))
        duration = forceInt(self._record.value('duration'))
        if duration < 1:
            return None
        db = QtGui.qApp.db
        record = self._record
        plannedEndDate = forceDateTime(record.value('plannedEndDate'))
        aliquoticity = forceInt(record.value('aliquoticity')) or 1
        quantity = forceInt(record.value('quantity'))
        begDate = forceDateTime(record.value('begDate'))
        periodicity = forceInt(record.value('periodicty')) or 0
        actionTypeId = forceRef(record.value('actionType_id'))
        specifiedName = forceString(record.value('specifiedName'))
        orgStructureId = forceRef(record.value('orgStructure_id'))
        if QtGui.qApp.userId and QtGui.qApp.userSpecialityId:
            execPersonId = QtGui.qApp.userId
        else:
            execPersonId = forceRef(record.value('setPerson_id'))
        record.setValue('person_id', toVariant(execPersonId))
        record.setValue('aliquoticity', toVariant(aliquoticity))
        record.setValue('begDate', toVariant(begDate))
        if not self.executionPlanManager.currentItem:
            return None
        self.executionPlanManager.setCurrentItemIndex(self.executionPlanManager.executionPlan.items.index(self.executionPlanManager._currentItem))
        nextExecutionPlanItem = self.executionPlanManager.getNextItem()
        self.executionPlanManager.setCurrentItemExecuted()
        if not nextExecutionPlanItem:
            return None
        tableAction = db.table('Action')
        newRecord = tableAction.newRecord()
        newRecord.setValue('plannedEndDate', toVariant(plannedEndDate))
        newRecord.setValue('directionDate', toVariant(record.value('directionDate')))
        newRecord.setValue('begDate', toVariant(nextExecutionPlanItem.getDateTime()))
        newRecord.setValue('orgStructure_id', toVariant(orgStructureId))
        newRecord.setValue('event_id', toVariant(record.value('event_id')))
        newRecord.setValue('status', toVariant(CActionStatus.started))
        # newRecord.setValue('specifiedName', toVariant(specifiedName))
        newRecord.setValue('periodicity', toVariant(periodicity))
        newRecord.setValue('actionType_id', toVariant(actionTypeId))
        newRecord.setValue('setPerson_id', toVariant(record.value('setPerson_id')))
        newRecord.setValue('person_id', toVariant(
            QtGui.qApp.userId if (QtGui.qApp.userId and QtGui.qApp.userSpecialityId) else execPersonId))
        newRecord.setValue('org_id', toVariant(record.value('org_id')))
        newRecord.setValue('amount', toVariant(record.value('amount')))
        actionFinanceId = self.getFinanceId()
        newRecord.setValue('finance_id', toVariant(actionFinanceId))
        actionMedicalAidKindId = self.getMedicalAidKindId()
        newRecord.setValue('medicalAidKind_id', toVariant(actionMedicalAidKindId))
        newAction = CAction(record=newRecord)
        newAction.setFinanceId(forceRef(newRecord.value('finance_id')))
        newAction.setMedicalAidKindId(forceRef(newRecord.value('medicalAidKind_id')))
        newAction.updateByAction(self)
        executionPlan = self.getExecutionPlan()
        if nextExecutionPlanItem:
            if newAction and newAction.executionPlanManager and executionPlan:
                newAction.executionPlanManager.setExecutionPlan(executionPlan)

            newAction.setExecutionPlanItem(nextExecutionPlanItem)
            newAction.executionPlanManager.bindAction(newAction)
            duration = max(
                nextExecutionPlanItem.date.daysTo(
                    self.executionPlanManager.plannedEndDate()
                ), 1)
        else:
            duration = 1
        if executionPlan:
            aliquoticity = 1
            aliquoticityToDate = executionPlan.getCountItemsByDate(nextExecutionPlanItem.getDateTime().date() if nextExecutionPlanItem else begDate.date())
            if aliquoticityToDate:
                aliquoticity = aliquoticityToDate
            else:
                aliquoticityEP = executionPlan.getAliquoticity()
                if aliquoticityEP:
                    aliquoticity = aliquoticityEP
        newRecord.setValue('duration', toVariant(duration))
        newRecord.setValue('aliquoticity', toVariant(aliquoticity))
        newRecord.setValue('quantity', toVariant(quantity - (1 if quantity > 0 else 0)))
        newAction.initPropertiesBySameAction(self)
        financeId = newAction.getFinanceId()
        medicalAidKindId = newAction.getMedicalAidKindId()
        #if QtGui.qApp.controlSMFinance() == 0:
        #    newAction.initNomenclature(clientId, medicalAidKindId=self._medicalAidKindId)
        #    newAction.nomenclatureReservationFromAction(self, medicalAidKindId=self._medicalAidKindId, supplierId=orgStructureId)
        #else:
        newAction.initNomenclature(clientId, financeId=financeId, medicalAidKindId=medicalAidKindId)
        newAction.nomenclatureReservationFromAction(self, financeId=financeId, medicalAidKindId=medicalAidKindId, supplierId=orgStructureId)
        if newAction.getType().isNomenclatureExpense:
            newAction.updateDosageFromExecutionPlan()
            newAction.updateSpecifiedName()
            noteAction = forceStringEx(record.value('note'))
            note = noteAction if noteAction else (forceStringEx(executionPlan.getNote()) if executionPlan else u'')
            newAction.setNote(note)
            newRecord.setValue('note', toVariant(note))
            if executionPlan:
                executionPlan.setNote(note)
        else:
            newRecord.setValue('specifiedName', toVariant(specifiedName))
            newAction.setSpecifiedName(specifiedName)
        newAction.finalFillingPlannedEndDate()
        return newAction


    def countIdx(self, eventId):
        db = QtGui.qApp.db

        actionTypeClass = self.getType().class_

        tableAction = db.table('Action')
        tableActionType = db.table('ActionType')

        queryTable = tableAction.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))

        cond = [
            tableAction['deleted'].eq(0),
            tableAction['event_id'].eq(eventId),
            tableActionType['deleted'].eq(0),
            tableActionType['class'].eq(actionTypeClass)
        ]

        return forceInt(
            QtGui.qApp.db.getMax(queryTable, tableAction['idx'], where=cond)
        )

    def getJobTicketDateTime(self):
        actionType = self.getType()
        propertyTypeList = actionType.getPropertiesById().values() if actionType else []
        for propertyType in propertyTypeList:
            if propertyType.isJobTicketValueType():
                property = self.getPropertyById(propertyType.id)
                jobTicketId = property.getValue()
                if jobTicketId:
                    db = QtGui.qApp.db
                    table = db.table('Job_Ticket')
                    record = db.getRecordEx(table, [table['datetime']], [table['id'].eq(jobTicketId)])
                    if record:
                        return forceDateTime(record.value('datetime'))
        return None


    @classmethod
    def getFilledAction(cls, eventEditor, record, actionTypeId,
                        amount=None, financeId=None, contractId=None, initPresetValues=True, orgStructureId=None):

        cls.preFillingActionRecord(eventEditor, record, actionTypeId, amount, financeId, contractId, orgStructureId=orgStructureId)
        if actionTypeId is None:
            return None

        action = cls(record=record)
        action.fillAction(eventEditor, initPresetValues=initPresetValues)
        return action


    @staticmethod
    def preFillingActionRecord(eventEditor, record, actionTypeId, amount, financeId, contractId, orgStructureId=None):
        # сюда - инициализация, которая никак не зависит от свойств действия
        orgStructureId = orgStructureId
        if actionTypeId:
            actionType = CActionTypeCache.getById(actionTypeId)
            defaultStatus = actionType.defaultStatus
            defaultDirectionDate = actionType.defaultDirectionDate
            defaultBegDate = actionType.defaultBegDate
            defaultEndDate = actionType.defaultEndDate
            defaultSetPerson = actionType.defaultSetPersonInEvent
            defaultExecPersonId = actionType.defaultExecPersonId
            defaultPerson = actionType.defaultPersonInEvent
            defaultMKB = actionType.defaultMKB
            defaultOrgId = actionType.defaultOrgId
            office = actionType.office
            record.setValue('actionType_id', toVariant(actionTypeId))
            if actionType.isNomenclatureExpense:
                orgStructureId = actionType.getNomenclatureOrgStructureId()
        else:
            defaultStatus = CActionStatus.finished  # Закончено
            defaultDirectionDate = CActionType.dddUndefined
            defaultBegDate = 0
            defaultEndDate = CActionType.dedEventExecDate  # Дата события
            defaultSetPerson = 0
            defaultExecPersonId = None
            defaultPerson = CActionType.dpEmpty
            defaultMKB = None
            defaultOrgId = None
            office = ''
        if not orgStructureId:
            orgStructureId = QtGui.qApp.currentOrgStructureId()

        if defaultEndDate == CActionType.dedEventExecDate:
            endDate = forceDateTime(eventEditor.eventDate)
        elif defaultEndDate == CActionType.dedEventSetDate:
            endDate = eventEditor.eventSetDateTime
        elif defaultEndDate == CActionType.dedCurrentDate:
            endDate = QDateTime.currentDateTime()
        else:
            if defaultStatus in (CActionStatus.finished, CActionStatus.withoutResult):
                endDate = QDateTime.currentDateTime()
            else:
                endDate = QDateTime()

        begDate = eventEditor.eventSetDateTime
        if defaultDirectionDate == CActionType.dddEventSetDate:
            directionDate = eventEditor.eventSetDateTime
        elif defaultDirectionDate == CActionType.dddCurrentDate:
            directionDate = QDateTime.currentDateTime()
        elif defaultDirectionDate == CActionType.dddActionExecDate:
            if endDate:
                if endDate < eventEditor.eventSetDateTime:
                    directionDate = eventEditor.eventSetDateTime
                    begDate = QDateTime()
                else:
                    directionDate = begDate = endDate
            else:
                directionDate = eventEditor.eventSetDateTime
        else:
            directionDate = eventEditor.eventSetDateTime

        if defaultBegDate == CActionType.dbdEventExecDate:
            begDate = forceDateTime(eventEditor.eventDate)
        elif defaultBegDate == CActionType.dbdEventSetDate:
            begDate = eventEditor.eventSetDateTime
        elif defaultBegDate == CActionType.dbdCurrentDate:
            begDate = QDateTime.currentDateTime()

        if defaultEndDate == CActionType.dedActionBegDate or defaultEndDate == CActionType.dedSyncActionBegDate:
            endDate = max(begDate, directionDate)
        if defaultEndDate == CActionType.dedSyncEventEndDate:
            endDate = forceDateTime(eventEditor.eventDate)

        if defaultSetPerson == CActionType.dspUndefined:
            if getEventTypeForm(eventEditor.eventTypeId) == '001':  # WTF?
                setPersonId = eventEditor.cmbSetPerson.value()
            else:
                setPersonId = eventEditor.getSuggestedPersonId()
        elif defaultSetPerson == CActionType.dspEventExecPerson:
            setPersonId = eventEditor.personId
        elif defaultSetPerson == CActionType.dspExecPerson:
            setPersonId = None


        if defaultExecPersonId:
            personId = defaultExecPersonId
        else:
            if defaultPerson == CActionType.dpCurrentMedUser:
                if QtGui.qApp.userSpecialityId:
                    personId = QtGui.qApp.userId
                else:
                    personId = None
            elif defaultPerson == CActionType.dpCurrentUser:
                personId = QtGui.qApp.userId
            elif defaultPerson == CActionType.dpEventExecPerson:
                personId = eventEditor.personId
            elif defaultPerson == CActionType.dpSetPerson:
                personId = setPersonId
            else:
                personId = None

        
        if defaultSetPerson == CActionType.dspExecPerson:
            setPersonId = personId
        elif defaultSetPerson == CActionType.dspUndefined:
            setPersonId = QtGui.qApp.userId

        if defaultBegDate == CActionType.dbdActionEndDate:
            begDate = max(endDate, directionDate)

        defaultMKBValue = ''
        defaultMorphologyMKBValue = ''
        if defaultMKB in (CActionType.dmkbByFinalDiag,
                          CActionType.dmkbBySetPersonDiag,
                          CActionType.dmkbSyncFinalDiag,
                          CActionType.dmkbSyncSetPersonDiag,
                          CActionType.dmkbSyncPreDiag
                          ):
            defaultMKBValue, defaultMorphologyMKBValue = eventEditor.getDefaultMKBValue(defaultMKB, setPersonId)

        if actionTypeId and actionType:
            specIdList = []
            for item in actionType.getPFSpecialityRecordList():
                specIdList.append(forceRef(item.value('speciality_id')))
            orgStructIdList = []
            for item in actionType.getPFOrgStructureRecordList():
                orgStruct = forceInt(item.value('orgStructure_id'))
                orgStructIdList.append(orgStruct)
                for orgStructDescendant in getOrgStructureDescendants(orgStruct):
                    orgStructIdList.append(orgStructDescendant)
            db = QtGui.qApp.db
            personRecord = db.getRecord('Person', 'speciality_id, orgStructure_id', personId)
            if personRecord:
                if (specIdList and forceInt(personRecord.value('speciality_id')) not in specIdList) or \
                    (orgStructIdList and forceInt(personRecord.value('orgStructure_id')) not in orgStructIdList):
                        personId = None
                
        record.setValue('orgStructure_id', toVariant(orgStructureId))
        record.setValue('directionDate', toVariant(directionDate))
        record.setValue('setPerson_id', toVariant(setPersonId))
        record.setValue('begDate', toVariant(max(begDate, directionDate)))
        record.setValue('endDate', toVariant(endDate))
        record.setValue('status', toVariant(defaultStatus))
        record.setValue('office', toVariant(office))
        record.setValue('person_id', toVariant(personId))
        record.setValue('MKB', toVariant(defaultMKBValue))
        record.setValue('morphologyMKB', toVariant(defaultMorphologyMKBValue))
        record.setValue('org_id', toVariant(defaultOrgId))
        if actionTypeId:
            if not (amount and actionType.amountEvaluation == CActionType.userInput):
                amount = getActionDefaultAmountEx(eventEditor, actionType, record, None)
        else:
            amount = 0
        record.setValue('amount', toVariant(amount))
        if not financeId:
            financeId = eventEditor.getActionFinanceId(record)
        if getEventActionContract(eventEditor.eventTypeId):
            contractId = getActionDefaultContractId(eventEditor, actionTypeId, financeId, begDate, endDate,
                                                    contractId or eventEditor.contractId)
        else:
            contractId = None
        record.setValue('uet',
                        toVariant(amount * eventEditor.getUet(actionTypeId, personId, financeId, contractId)))
        record.setValue('finance_id', toVariant(financeId))
        record.setValue('contract_id', toVariant(contractId))
        if eventEditor._id:
            record.setValue('event_id', toVariant(eventEditor._id))
        eventMedicalAidKindId = getEventMedicalAidKindId(eventEditor.eventTypeId)
        record.setValue('medicalAidKind_id', toVariant(eventMedicalAidKindId))


    def fillAction(self, eventEditor, initPresetValues=True):
        self.updatePresetValuesConditions({'clientId': eventEditor.clientId,
                                           'eventTypeId': eventEditor.eventTypeId})
        if initPresetValues:
            self.initPresetValues()
        self._medicalAidKindId = self.getMedicalAidKindId(eventEditor.eventTypeId)
        self.finalFillingActionRecord()
        #if QtGui.qApp.controlSMFinance() == 0:
        #    self.initNomenclature(eventEditor.clientId, medicalAidKindId=self.getMedicalAidKindId())
        #else:
        self.initNomenclature(eventEditor.clientId, financeId=self.getFinanceId(), medicalAidKindId=self.getMedicalAidKindId())


    def finalFillingActionRecord(self):
        # сюда - инициализация, которая может зависеть от свойств
        record = self.getRecord()
        directionDate = forceDate(record.value('directionDate'))
        plannedEndDate = None
        defaultPlannedEndDate = self.getType().defaultPlannedEndDate
        if directionDate:
            if defaultPlannedEndDate == CActionType.dpedNextDay:
                plannedEndDate = directionDate.addDays(1)
            elif defaultPlannedEndDate == CActionType.dpedNextWorkDay:
                plannedEndDate = addWorkDays(directionDate, 1, wpFiveDays)
            elif defaultPlannedEndDate == CActionType.dpedJobTicketDate:
                plannedEndDate = self.getJobEndDate()
        actionType = self._actionType
        if actionType:
            defaultBegDate = actionType.defaultBegDate
            if defaultBegDate == CActionType.dbdJobTicketTime:
                dateTimeJT = self.getJobTicketDateTime()
                if dateTimeJT:
                    record.setValue('begDate', toVariant(dateTimeJT))
        begDate = forceDate(record.value('begDate'))
        if begDate:
            if defaultPlannedEndDate == CActionType.dpedBegDatePlusAmount:
                plannedEndDate = begDate.addDays(forceInt(record.value('quantity')))
            elif defaultPlannedEndDate == CActionType.dpedBegDatePlusDuration:
                plannedEndDate = begDate.addDays(forceInt(record.value('duration')))
        record.setValue('plannedEndDate', toVariant(plannedEndDate))
        if actionType.hasJobTicketPropertyType():
            record.setValue('orgStructure_id', toVariant(self.getJobTicketOrgStructureId()))


    def finalFillingPlannedEndDate(self):
        # сюда - инициализация, которая может зависеть от свойств
        record = self.getRecord()
        directionDate = forceDate(record.value('directionDate'))
        plannedEndDate = None
        defaultPlannedEndDate = self.getType().defaultPlannedEndDate
        if directionDate:
            if defaultPlannedEndDate == CActionType.dpedNextDay:
                plannedEndDate = directionDate.addDays(1)
            elif defaultPlannedEndDate == CActionType.dpedNextWorkDay:
                plannedEndDate = addWorkDays(directionDate, 1, wpFiveDays)
            elif defaultPlannedEndDate == CActionType.dpedJobTicketDate:
                plannedEndDate = self.getJobEndDate()
        actionType = self._actionType
        if actionType:
            defaultBegDate = actionType.defaultBegDate
            if defaultBegDate == CActionType.dbdJobTicketTime:
                dateTimeJT = self.getJobTicketDateTime()
                if dateTimeJT:
                    record.setValue('begDate', toVariant(dateTimeJT))
        begDate = forceDate(record.value('begDate'))
        if begDate:
            if defaultPlannedEndDate == CActionType.dpedBegDatePlusAmount:
                plannedEndDate = begDate.addDays(forceInt(record.value('quantity')))
            elif defaultPlannedEndDate == CActionType.dpedBegDatePlusDuration:
                plannedEndDate = begDate.addDays(forceInt(record.value('duration')))
        record.setValue('plannedEndDate', toVariant(plannedEndDate))

    def setPlannedEndDateOnJobTicketChanged(self, jobTicketId):
        # Если плановая дата выполнения действия зависит от номерка на работу согласно умолчаниям
        record = self.getRecord()
        defaultPlannedEndDate = self.getType().defaultPlannedEndDate
        if defaultPlannedEndDate == CActionType.dpedJobTicketDate and forceDate(record.value('directionDate')):
            if jobTicketId:
                plannedEndDate = self.getJobEndDate(jobTicketId)
            else:
                plannedEndDate = None

            self.setPlannedEndDate(plannedEndDate)

    def setBegDate(self, begDate):
        record = self.getRecord()
        record.setValue('begDate', toVariant(begDate))


    def setBegTime(self, begTime):
        showTime = self._actionType.showTime if self._actionType else False
        if not showTime:
           begTime = QTime()
        record = self.getRecord()
        begDate = forceDate(record.value('begDate'))
        record.setValue('begDate', toVariant(QDateTime(begDate, begTime)))


    def setEndDate(self, endDate):
        record = self.getRecord()
        record.setValue('endDate', toVariant(endDate))


    def setPlannedEndDate(self, plannedEndDate):
        record = self.getRecord()
        record.setValue('plannedEndDate', toVariant(plannedEndDate))

    def getCreateDateTime(self):
        if self._record:
            return forceDateTime(self._record.value('createDatetime'))
        return None


def getActionDefaultAmountEx(eventEditor, actionType, record, action):
    result = actionType.amount
    if actionType.amountEvaluation == CActionType.eventVisitCount:
        result = result * eventEditor.getVisitCount()
    elif actionType.amountEvaluation == CActionType.eventDurationWithFiveDayWorking:
        result = result * eventEditor.getEventDuration(wpFiveDays)
    elif actionType.amountEvaluation == CActionType.eventDurationWithSixDayWorking:
        result = result * eventEditor.getEventDuration(wpSixDays)
    elif actionType.amountEvaluation == CActionType.eventDurationWithSevenDayWorking:
        result = result * eventEditor.getEventDuration(wpSevenDays)
    elif actionType.amountEvaluation == CActionType.actionDurationWithFiveDayWorking:
        result = result * getActionDuration(eventEditor.eventTypeId, record, wpFiveDays)
    elif actionType.amountEvaluation == CActionType.actionDurationWithSixDayWorking:
        result = result * getActionDuration(eventEditor.eventTypeId, record, wpSixDays)
    elif actionType.amountEvaluation == CActionType.actionDurationWithSevenDayWorking:
        result = result * getActionDuration(eventEditor.eventTypeId, record, wpSevenDays)
    elif actionType.amountEvaluation == CActionType.actionFilledPropsCount:
        result = result * action.getFilledPropertiesCount() if action else 0
    elif actionType.amountEvaluation == CActionType.actionAssignedPropsCount:
        result = result * action.getAssignedPropertiesCount() if action else 0
    elif actionType.amountEvaluation == CActionType.actionDurationFact: ###ymd
        result = result * getActionDurationFact(eventEditor.eventTypeId, record)
    return result


def getActionDuration(eventTypeId, record, weekProfile):
    if record:
        startDate = forceDate(record.value('begDate'))
        stopDate  = forceDate(record.value('endDate'))
        if startDate and stopDate:
            return getEventDuration(startDate, stopDate, weekProfile, eventTypeId)
    return 0

def getActionDurationFact(eventTypeId, record): ###ymd
    if record:
        startDate = forceDate(record.value('begDate'))
        stopDate  = forceDate(record.value('endDate'))
        if startDate and stopDate:
            return (stopDate.day() - startDate.day())+1
    return 0

def getActionDefaultContractId(eventEditor, actionTypeId, financeId, begDate, endDate, contractId):
    model = CContractDbModel(None)
    try:
        model.setOrgId(eventEditor.orgId)
        model.setEventTypeId(eventEditor.eventTypeId)
        model.setClientInfo(eventEditor.clientId,
                            eventEditor.clientSex,
                            eventEditor.clientAge,
                            eventEditor.clientWorkOrgId,
                            eventEditor.clientPolicyInfoList)
        model.setFinanceId(financeId)
        model.setActionTypeId(actionTypeId)
        model.setBegDate(begDate or QtCore.QDate.currentDate())
        model.setEndDate(endDate or QtCore.QDate.currentDate())
        model.initDbData()
        return contractId if contractId and model.searchId(contractId)>=0 else model.getId(0)
    finally:
        model.deleteLater()


def selectNomenclatureExpense(obj, actionExpense):
    result = True
    actionExpenseItems = []
    recordExpense = None
    if actionExpense:
        recordExpense = actionExpense.getRecord()
        status = forceInt(recordExpense.value('status'))
        stockMotionId = forceRef(recordExpense.value('stockMotion_id'))
        if actionExpense.nomenclatureExpense and not stockMotionId:
            if not actionExpense._actionType.generateAfterEventExecDate or bool(actionExpense._actionType.generateAfterEventExecDate and actionExpense.event.execDate):
                if actionExpense.nomenclatureExpense and status == CActionStatus.finished and (
                        actionExpense.nomenclatureExpense.getStockMotionId() or actionExpense.nomenclatureExpense.stockMotionItems()):
                    actionExpenseItems.append((recordExpense, actionExpense))
    if actionExpenseItems:
        dialog = CNomenclatureAddedActionsSelectDialog(obj, actionExpenseItems)
        try:
            dialog.btnAPNomenclatureExpense.setVisible(False)
            dialog.actAPNomenclatureExpense.setVisible(False)
            if dialog.exec_():
                actionExpenseItems = dialog.getActionExpenseItems()
                result = True
            else:
                result = False
        finally:
            dialog.deleteLater()
    return result, actionExpenseItems[0] if actionExpenseItems else (recordExpense, actionExpense)


####################################################
#TODO вынести в отдельный модуль
class CNomenclatureClientReservation(object):
    _RECIPE_PROPERTY = 1

    def __init__(self, action, clientId=None, financeId=None, medicalAidKindId=None, supplierId=None, markToUpdate=False):
        self._tableStockMotion = QtGui.qApp.db.table('StockMotion')
        self._tableStockMotionItem = QtGui.qApp.db.table('StockMotion_Item')
        self._linkTable = QtGui.qApp.db.table('Action_NomenclatureReservation')
        self._action = action
        self._clientId = clientId
        self._supplierId = supplierId
        self._financeId = financeId
        self._medicalAidKindId = medicalAidKindId
        self._record = None
        self._items = []
        self._actionId = action.getId()
        self.markToDelete = False
        self.markToUpdate = markToUpdate


    def cancelEx(self, clientReservationToAction):
        if not self._record:
            return False
        reservationId = forceRef(self._record.value('id'))
        if not reservationId:
            return False
        reservationToActionLine = clientReservationToAction.get(reservationId, [])
        for reservationActionId in reservationToActionLine:
            if self._actionId != reservationActionId:
                return False
        QtGui.qApp.db.deleteRecord(self._tableStockMotionItem, [self._tableStockMotionItem['master_id'].eq(reservationId), self._tableStockMotionItem['deleted'].eq(0)])
        QtGui.qApp.db.deleteRecord(self._tableStockMotion, [self._tableStockMotion['id'].eq(reservationId), self._tableStockMotion['deleted'].eq(0)])
        if self._actionId:
            QtGui.qApp.db.deleteRecord(self._linkTable, [self._linkTable['action_id'].eq(self._actionId), self._linkTable['reservation_id'].eq(reservationId)])
        self._record = None
        self._items = []
        return True

    def cancel(self):
        if not self._record:
            return
        reservationId = forceRef(self._record.value('id'))
        if not reservationId:
            return

        QtGui.qApp.db.deleteRecord(self._tableStockMotionItem, [self._tableStockMotionItem['master_id'].eq(reservationId), self._tableStockMotionItem['deleted'].eq(0)])
        QtGui.qApp.db.deleteRecord(self._tableStockMotion, [self._tableStockMotion['id'].eq(reservationId), self._tableStockMotion['deleted'].eq(0)])
        if self._actionId:
            QtGui.qApp.db.deleteRecord(self._linkTable, [self._linkTable['action_id'].eq(self._actionId), self._linkTable['reservation_id'].eq(reservationId)])
        self._record = None
        self._items = []


    def reverseNomenclature(self, clientStockMotionItem):
        nomenclatureId = forceRef(clientStockMotionItem.value('nomenclature_id'))
        csmQnt = forceDouble(clientStockMotionItem.value('qnt'))
        if csmQnt > 0 and forceRef(clientStockMotionItem.value('id')):
            csmPrice = forceDouble(clientStockMotionItem.value('price'))
            unitId = forceRef(clientStockMotionItem.value('unit_id'))
            batch = forceString(clientStockMotionItem.value('batch'))
            shelfTime = forceDate(clientStockMotionItem.value('shelfTime'))
            financeId = forceRef(clientStockMotionItem.value('finance_id'))
            medicalAidKindId = forceRef(clientStockMotionItem.value('medicalAidKind_id'))
            for item in self._items:
                if nomenclatureId != forceRef(item.value('nomenclature_id')):
                    continue
                if csmQnt > 0 and batch == forceString(item.value('batch')) and shelfTime == forceDate(item.value('shelfTime')) and csmPrice == forceDouble(item.value('price')) and financeId == forceRef(item.value('finance_id')) and  medicalAidKindId == forceRef(item.value('medicalAidKind_id')):
                    ratio = getNomenclatureUnitRatio(nomenclatureId, unitId, forceRef(item.value('unit_id')))
                    csmQnt *= ratio
                    reservedQnt = forceDouble(item.value('qnt'))
                    item.setValue('qnt', toVariant(reservedQnt+csmQnt))
                    sum = forceDouble(item.value('price')) * forceDouble(item.value('qnt'))
                    item.setValue('sum', toVariant(sum))
                    csmQnt = 0
                    QtGui.qApp.db.updateRecord(self._tableStockMotionItem, item)


    def releaseNomenclature(self, clientStockMotionItem):
        nomenclatureId = forceRef(clientStockMotionItem.value('nomenclature_id'))
        csmQnt = forceDouble(clientStockMotionItem.value('qnt'))
        csmSum = forceDouble(clientStockMotionItem.value('sum'))
        unitId = forceRef(clientStockMotionItem.value('unit_id'))
        batch = forceString(clientStockMotionItem.value('batch'))
        shelfTime = forceDate(clientStockMotionItem.value('shelfTime'))
        csmPrice = forceDouble(clientStockMotionItem.value('price'))
        financeId = forceRef(clientStockMotionItem.value('finance_id'))
        medicalAidKindId = forceRef(clientStockMotionItem.value('medicalAidKind_id'))

        for item in self._items:
            if nomenclatureId != forceRef(item.value('nomenclature_id')):
                continue

            if batch == forceString(item.value('batch')) and shelfTime == forceDate(item.value('shelfTime')) and csmPrice == forceDouble(item.value('price')) and financeId == forceRef(item.value('finance_id')) and  medicalAidKindId == forceRef(item.value('medicalAidKind_id')):
                ratio = getNomenclatureUnitRatio(nomenclatureId, unitId, forceRef(item.value('unit_id')))

                csmQnt *= ratio

                reservedQnt = forceDouble(item.value('qnt'))
                reservedSum = forceDouble(item.value('sum'))
                if csmQnt > 0:
                    if reservedQnt!=0:
                        if reservedQnt < csmQnt:
                            csmQnt = reservedQnt
                            csmSum = reservedSum
                            clientStockMotionItem.setValue('qnt', toVariant(csmQnt / ratio))
                            clientStockMotionItem.setValue('sum', toVariant(csmSum / csmQnt))

                        item.setValue('qnt', toVariant(reservedQnt-csmQnt))
                        item.setValue('sum', toVariant(reservedSum-csmSum))
                        csmQnt = csmQnt - reservedQnt
                        csmSum = csmSum - reservedSum

                        QtGui.qApp.db.updateRecord(self._tableStockMotionItem, item)


    def _calcQnt(self, dosageValue=None):
        actionRecord = self._action.getRecord()
        total = (forceInt(actionRecord.value('duration')) or 1)
        perodicity = forceInt(actionRecord.value('periodicity'))
        if not perodicity:
            qnt = total * (forceInt(actionRecord.value('aliquoticity')) or 1)
        else:
            qnt = len(range(perodicity, total + perodicity, perodicity + 1)) * (
            forceInt(actionRecord.value('aliquoticity')) or 1)

        if qnt == 0:
            return None

        doses = None
        for properties in self._action._properties:
            type = properties._type
            name = type.name
            if type.inActionsSelectionTable == _DOSES:  # doses
                property = self._action.getProperty(name)
                doses = property.getValue()
                if isinstance(doses, (float, int)):
                    break
                else:
                    doses = None

        coeff = 1
        if dosageValue:
            coeff = doses / dosageValue

        return qnt * coeff

    def init(self, dosage=None):
        actionType = self._action.getType()
        executionPlan = self._action.getExecutionPlan()
        if (not executionPlan and not actionType.isDoesNotInvolveExecutionCourse) or not self._clientId:
            return None

        db = QtGui.qApp.db

        stockMotionId = None

        stockService = None

        db.transaction()

        try:
            actionRecord = self._action.getRecord()
            self._supplierId = forceRef(actionRecord.value('orgStructure_id'))
            propertyTypeList = actionType.getPropertiesById().values() if actionType else []
            for propertyType in propertyTypeList:
                if propertyType.isNomenclatureValueType() and propertyType.inActionsSelectionTable == self._RECIPE_PROPERTY:
                    property = self._action.getPropertyById(propertyType.id)
                    nomenclatureId = property.getValue()
                    if not nomenclatureId:
                        continue

                    nomenclatureRecord = db.getRecord(
                        'rbNomenclature', 'defaultClientUnit_id, defaultStockUnit_id, dosageValue', nomenclatureId
                    )
                    dosageValue = forceDouble(nomenclatureRecord.value('dosageValue'))
                    clientUnitId = forceRef(nomenclatureRecord.value('defaultClientUnit_id'))
#                    stockUnitId = forceRef(nomenclatureRecord.value('defaultStockUnit_id'))

                    executionPlanQnt = 0
                    if executionPlan:
                        for item in executionPlan.items:
                            if item.nomenclature and not item.executedDatetime:
                                executionPlanQnt += item.nomenclature.dosage

                    if not stockMotionId:
                        # TODO Это все через сервис
                        self._record = stockMotionRecord = self._tableStockMotion.newRecord()
                        currentDateTime = QDateTime.currentDateTime()
                        stockMotionRecord.setValue('type', toVariant(6))  # client reservation type
                        stockMotionRecord.setValue('client_id', toVariant(self._clientId))
                        stockMotionRecord.setValue('supplier_id', toVariant(self._supplierId) if self._supplierId else toVariant(QtGui.qApp.currentOrgStructureId()))
                        stockMotionRecord.setValue('date', toVariant(currentDateTime))
                        stockMotionRecord.setValue('reasonDate', toVariant(currentDateTime))
                        stockMotionRecord.setValue(
                            'supplierPerson_id',
                            toVariant(
                                QtGui.qApp.userId if QtGui.qApp.userSpecialityId
                                else forceRef(actionRecord.value('person_id'))
                            )
                        )

                        stockMotionId = db.insertRecord(self._tableStockMotion, stockMotionRecord)
                        stockMotion = CStockService.getStockMotionByRecord(stockMotionRecord)
                        stockService = CStockService(stockMotion)

                    if executionPlanQnt:
                        if dosageValue:
                            qnt = executionPlanQnt/dosageValue
                        else:
                            qnt = executionPlanQnt
                    elif dosage is None:
                        qnt = self._calcQnt(dosageValue)
                    elif dosageValue:
                        qnt = dosage/dosageValue
                    else:
                        qnt = self._calcQnt()
                    orgStructureId = self._supplierId if self._supplierId else QtGui.qApp.currentOrgStructureId()
                    while qnt > 0:
                        itemRecord = self._tableStockMotionItem.newRecord()
                        stockMotionItem = stockService.getStockMotionItemByRecord(itemRecord)
                        stockMotionItem.nomenclature_id = nomenclatureId
                        stockMotionItem.unit_id = clientUnitId
                        stockMotionItem.setFinanceId(self._financeId)
                        stockMotionItem.setMedicalAidKindId(self._medicalAidKindId)
                        stockMotionItem.note = u''
                        existQnt = getExistsNomenclatureAmount(nomenclatureId, financeId=stockMotionItem.finance_id, medicalAidKindId=stockMotionItem.medicalAidKind_id, batch=stockMotionItem.batch, orgStructureId=orgStructureId, unitId=clientUnitId, precision=QtGui.qApp.numberDecimalPlacesQnt())
                        if existQnt:
                            #stockMotionItem.qnt = existQnt if existQnt <= qnt else qnt
                            remainsQnt = existQnt if existQnt <= qnt else qnt
#                            stockMotionItem.sum = calcNomenclatureSumFromRecord(itemRecord)
                            ratioQnt = getRatio(nomenclatureId, stockMotionItem.unit_id, None)
                            findQnt = (remainsQnt * ratioQnt) if ratioQnt else remainsQnt
                            #financeId, batch, shelfTime, medicalAidKindId, price, reservationClient = findFinanceBatchShelfTime(orgStructureId, nomenclatureId, qnt=findQnt, financeId=self._financeId, medicalAidKind=self._medicalAidKindId)
                            findMinimumQnt = 1.0/pow(10, QtGui.qApp.numberDecimalPlacesQnt()) #0011442:0065687 и 0011442:0065689: иначе остаются крошки от таблеток, партия как бы есть, а в результате округления по numberDecimalPlacesQnt batchQnt = 0, из-за чего подбор партий зацикливается.
                            batch, shelfTime, financeId, medicalAidKindId, price, batchQnt = getBatchShelfTimeFinanceQnt(nomenclatureId, financeId=self._financeId, medicalAidKind=self._medicalAidKindId, condHaving=u'''(qnt >= %s or qnt > %s)'''%(str(findQnt), str(findMinimumQnt)), orgStructureId=orgStructureId, unitId=clientUnitId, precision=QtGui.qApp.numberDecimalPlacesQnt())
                            if batchQnt > 0:
                                stockMotionItem.qnt = remainsQnt if remainsQnt <= batchQnt else batchQnt
                                stockMotionItem.finance_id = financeId
                                stockMotionItem.batch = batch
                                stockMotionItem.shelfTime = shelfTime
                                if ratioQnt is not None:
                                    price = price*ratioQnt
                                stockMotionItem.price = price
                                stockMotionItem.sum = stockMotionItem.price * stockMotionItem.qnt
                                stockMotionItem.medicalAidKind_id = medicalAidKindId
                                if not medicalAidKindId:
                                    itemRecord.setNull('medicalAidKind_id')
                                db.insertRecord(self._tableStockMotionItem, itemRecord)
                                self._items.append(itemRecord)
                                qnt = qnt - (stockMotionItem.qnt if stockMotionItem.qnt <= qnt else qnt)
                        else:
                            qnt = 0
        except:
            db.rollback()
            raise

        else:
            db.commit()

        if not stockMotionId:
            return None

        return self


#    def getRatio(self, nomenclatureId, oldUnitId, newUnitId):
#        if oldUnitId == newUnitId:
#            return 1
#
#        ratio = getNomenclatureUnitRatio(nomenclatureId, oldUnitId, newUnitId)
#        if ratio is None:
#            raise ValueError()
#
#        return ratio


    def updateSupplierId(self, value):
        self._supplierId = value
        if not self._supplierId:
            return
        stockMotionId = self._record.value('id')
        if not stockMotionId:
            return
        db = QtGui.qApp.db
        db.transaction()
        try:
            tableStockMotion = db.table('StockMotion')
            cond = [tableStockMotion['id'].eq(stockMotionId),
                    tableStockMotion['deleted'].eq(0)]
            record = db.getRecordEx(tableStockMotion, u'*', cond)
            if record:
                record.setValue('supplier_id', toVariant(self._supplierId))
                db.updateRecord(tableStockMotion, record)
        except:
            db.rollback()
            raise
        else:
            db.commit()


    def linkAction(self, action):
        if self._record is None:
            return None

        elif self.markToDelete:
            if self._actionId:
                QtGui.qApp.db.query(
                    'DELETE FROM {0} WHERE action_id = {1}'.format(self._linkTable.tableName, self._actionId)

                )
            return

        elif self._actionId == action.getId() and not self.markToUpdate:
            return

        self._actionId = action.getId()

        db = QtGui.qApp.db
        tableStockMotion = db.table('StockMotion')
        cond = [tableStockMotion['id'].eq(self._record.value('id')), tableStockMotion['deleted'].eq(0)]
        exists = db.getRecordEx(tableStockMotion, tableStockMotion['id'], cond)
        if exists:
            linkRecord = self._linkTable.newRecord()
            linkRecord.setValue('action_id', self._actionId)
            linkRecord.setValue('reservation_id', self._record.value('id'))

            db.insertRecord(self._linkTable, linkRecord)


    def fromAction(self, anotherAction):
        if not anotherAction.nomenclatureClientReservation:
            return None

        anotherNCR = anotherAction.nomenclatureClientReservation
        self._record = anotherNCR._record
        self._items = anotherNCR._items
        self.markToUpdate = False

        anotherNCR.markToDelete = True
        anotherNCR.markToUpdate = False

        return self


    def load(self, reservation_id=None):
        actionId = self._action.getId()
        if actionId:
            db = QtGui.qApp.db
            if reservation_id is None:
                linkTable = db.table(self._linkTable.name())
                queryTable = linkTable
                queryTable = queryTable.innerJoin(self._tableStockMotion, self._tableStockMotion['id'].eq(linkTable['reservation_id']))
                linkRecord = db.getRecordEx(queryTable, linkTable['reservation_id'], [linkTable['action_id'].eq(actionId), self._tableStockMotion['deleted'].eq(0)])
                reservation_id = forceRef(linkRecord.value('reservation_id')) if linkRecord else None
                if not reservation_id:
                    return None

            self._record = db.getRecordEx(self._tableStockMotion, '*', [self._tableStockMotion['id'].eq(reservation_id), self._tableStockMotion['deleted'].eq(0)])
            if not self._record:
                return None

            self._clientId = forceRef(self._record.value('client_id'))
            if not self._clientId:
                db.deleteRecord(self._tableStockMotionItem, self._record)
                db.query('DELETE FROM {0} WHERE action_id = {1}'.format(self._linkTable.tableName, actionId))
                return None

            self._items = db.getRecordList(
                self._tableStockMotionItem, '*', [self._tableStockMotionItem['master_id'].eq(reservation_id), self._tableStockMotionItem['deleted'].eq(0)]
            )
            return self

        return None


class CNomenclatureExpense:
    def __init__(self, action=None, actionId = None, actionType = None, actionTypeId = None, clientId=None, financeId=None, medicalAidKindId = None, actionAmount=None, supplierId=None):
        self._tableStockMotion = QtGui.qApp.db.table('StockMotion')
        self._tableStockMotionItem = QtGui.qApp.db.table('StockMotion_Item')
        self._dirty = False
        self._stockMotionId = None
        self._clientId = clientId
        self._supplierId = supplierId
        self._financeId = financeId
        self._medicalAidKindId = medicalAidKindId
        self._actionAmount = actionAmount
        self._avialableQnt = 0
        self._reservationUsed = False
        self._isApplyBatch = False
        self._necessaryQnt = None
        self._noAvialableQnt = {}
        self.selectNomenclatureIdList = []
        self._items = []
        self._exists = {}
        self._stockMotionRecord = None
        self._action = action
        if not self._supplierId and self._action:
            self._supplierId = forceRef(self._action.getRecord().value('orgStructure_id'))
        self.set(actionId, actionType, actionTypeId)
        if not self._actionType and action:
            self._actionType = action.getType()


    def cancel(self):
        stockMotionId = self.getStockMotionId()
        if not stockMotionId:
            return
        QtGui.qApp.db.deleteRecord(self._tableStockMotionItem, [self._tableStockMotionItem['master_id'].eq(stockMotionId), self._tableStockMotionItem['deleted'].eq(0)])
        QtGui.qApp.db.deleteRecord(self._tableStockMotion, [self._tableStockMotion['id'].eq(stockMotionId), self._tableStockMotion['deleted'].eq(0)])
        db = QtGui.qApp.db
        tableAction = db.table('Action')
        record = db.getRecordEx(tableAction, [tableAction['prevStockMotion_id']], [tableAction['id'].eq(self._actionId), tableAction['deleted'].eq(0)])
        self._stockMotionId = forceRef(record.value('prevStockMotion_id')) if record else None
        self._action.getRecord().setValue('stockMotion_id', toVariant(self._stockMotionId))
        self._reverseNomenclature()
        self._items = []
        self._exists = {}
        self._noAvialableQnt = {}
        self._stockMotionRecord = None
        self._avialableQnt = 0
        self._reservationUsed = False
        self._isApplyBatch = False
        self._necessaryQnt = None


    def cancelEx(self):
        stockMotionId = self.getStockMotionId()
        if not stockMotionId:
            db = QtGui.qApp.db
            tableAction = db.table('Action')
            record = db.getRecordEx(tableAction, [tableAction['prevStockMotion_id']], [tableAction['id'].eq(self._actionId), tableAction['deleted'].eq(0)])
            self._stockMotionId = forceRef(record.value('prevStockMotion_id')) if record else None
            self._action.getRecord().setValue('stockMotion_id', toVariant(self._stockMotionId))
            self._reverseNomenclature()
            self._items = []
            self._exists = {}
            self._noAvialableQnt = {}
            self._stockMotionRecord = None
            self._avialableQnt = 0
            self._reservationUsed = False
            self._isApplyBatch = False
            self._necessaryQnt = None


    def getNomenclatureIdItem(self, nomenclatureId):
        if nomenclatureId:
            for item in self._items:
                if forceRef(item.value('nomenclature_id')) == nomenclatureId:
                    return item
        return None


    def setSupplierId(self, supplierId):
        self._supplierId = supplierId
        if self._stockMotionRecord:
            self._stockMotionRecord.setValue('supplier_id', QVariant(supplierId))


    def getStockMotionId(self):
        return self._stockMotionId


    def setClientId(self, clientId):
        if self._stockMotionRecord:
            self._stockMotionRecord.setValue('client_id', QVariant(clientId))


    def stockMotionRecord(self):
        return self._stockMotionRecord


    def set(self, actionId = None, actionType = None, actionTypeId = None):
        self._actionId = actionId
        self._actionType = actionType
        if actionId:
            if QtGui.qApp.controlSMFinance() != 0:
                self._financeId = self.setFinanceId(actionId)
            self._medicalAidKindId = self.setMedicalAidKindId(actionId)
            self._clientId = self.getClientId(actionId)
            self._load(actionId)
            return
        if actionType:
            self._setActionType(actionType)
        elif actionTypeId:
            actionType = CActionTypeCache.getById(actionTypeId)
            self._setActionType(actionType)
        else:
            raise CException(u'Неправильные настройки списания ЛСиИМН')


    def setFinanceId(self, actionId):
        db = QtGui.qApp.db
        tableAction = db.table('Action')
        cond = [tableAction['id'].eq(actionId)]
        record = db.getRecordEx(tableAction, tableAction['finance_id'], cond)
        if record:
            return forceInt(record.value('finance_id'))
        return None

    def setMedicalAidKindId(self, actionId):
        db = QtGui.qApp.db
        tableAction = db.table('Action')
        cond = [tableAction['id'].eq(actionId)]
        record = db.getRecordEx(tableAction, tableAction['medicalAidKind_id'], cond)
        if record:
            return forceInt(record.value('medicalAidKind_id'))
        return None


    def getClientId(self, actionId):
        db = QtGui.qApp.db
        tableAction = db.table('Action')
        tableEvent = db.table('Event')
        queryTable = tableAction
        queryTable = queryTable.leftJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))
        cond = [tableAction['id'].eq(actionId)]
        record = db.getRecordEx(queryTable, tableEvent['client_id'], cond)
        if record:
            return forceInt(record.value('client_id'))
        return None

    def getNewRecord(self):
        record = self._tableStockMotion.newRecord()
        record.setValue('type', toVariant(4)) # списание на пациента
        record.setValue('client_id', toVariant(self._clientId))
        if self._actionType.nomenclatureCounterId:
            record.setValue('number', toVariant(
                    QtGui.qApp.getDocumentNumber(self._clientId, self._actionType.nomenclatureCounterId)))
        record.setValue('date', toVariant(QDateTime.currentDateTime()))
        record.setValue('supplier_id', toVariant(self._supplierId) if self._supplierId else toVariant(QtGui.qApp.currentOrgStructureId()))
        record.setValue('supplierPerson_id', toVariant(QtGui.qApp.userId if QtGui.qApp.userSpecialityId else forceRef(self._action.getRecord().value('person_id'))))
        return record


    def stockMotionItems(self):
        return self._items

    @staticmethod
    def _getExists(nomenclatureIdList, filter={}):
        return getExistsNomenclature(nomenclatureIdList, filter)


    @staticmethod
    def _sync(exists, targetRecord, unset=False, translateExistsQnt=False, financeId=None, clientId=None, medicalAidKindId=None, isNoAvialableQnt=False, avialableQntDict={}, orgStructureId=None):
        return syncNomenclature(exists, targetRecord, unset, translateExistsQnt, financeId=financeId, clientId=clientId, medicalAidKindId=medicalAidKindId, isNoAvialableQnt=isNoAvialableQnt, avialableQntDict=avialableQntDict, orgStructureId=orgStructureId)


    def _getNomenclatureIdList(self, recordList):
        return [forceRef(record.value('nomenclature_id')) for record in recordList]

    def _setActionType(self, actionType):
        _defaultsCache = {}

        def _getDefaultUnitId(nomenclatureId):
            if not nomenclatureId:
                return None
            if nomenclatureId not in _defaultsCache:
                unitId = forceRef(
                    QtGui.qApp.db.translate('rbNomenclature', 'id', nomenclatureId, 'defaultClientUnit_id')
                )
                _defaultsCache[nomenclatureId] = unitId
            return _defaultsCache[nomenclatureId]

        self._stockMotionRecord = self.getNewRecord()
        self._items = []
        self._noAvialableQnt = {}
        avialableQntDict = {}
        orgStructureId = self._supplierId if self._supplierId else QtGui.qApp.currentOrgStructureId()
        nomenclatureRecordList = actionType.getNomenclatureRecordList()
        self.selectNomenclatureIdList = self._getNomenclatureIdList(nomenclatureRecordList)
        exists = self._getExists(self.selectNomenclatureIdList, filter={'financeId': self._financeId, 'clientId':self._clientId, 'medicalAidKindId':self._medicalAidKindId, 'orgStructureId':self._supplierId, 'begDateAction':forceDate(self._action.getRecord().value('begDate')) if self._action else None})
        for idx, nomenclativeRecord in enumerate(nomenclatureRecordList):
            stockMotionItem = QtGui.qApp.db.table('StockMotion_Item').newRecord()
            nomenclatureId = forceRef(nomenclativeRecord.value('nomenclature_id'))
            amount = forceDouble(nomenclativeRecord.value('amount'))
#            writeoffTime = forceInt(nomenclativeRecord.value('writeoffTime'))
            stockMotionItem.setValue('nomenclature_id', toVariant(nomenclatureId))
            if actionType.isDoesNotInvolveExecutionCourse:
                stockMotionItem.setValue('qnt', toVariant(self.getIsDoesNotInvolveExecutionCourseQnt(nomenclatureId)))
            else:
                stockMotionItem.setValue('qnt', toVariant(amount*(self._actionAmount if self._actionAmount else 1)))
            stockMotionItem.setValue('unit_id', toVariant(_getDefaultUnitId(nomenclatureId)))
            avialableQntDict, stockMotionItems = self._sync(exists, stockMotionItem, translateExistsQnt=True, financeId=self._financeId, clientId=self._clientId, medicalAidKindId=self._medicalAidKindId, isNoAvialableQnt=True, avialableQntDict=avialableQntDict, orgStructureId=orgStructureId)
            self._items.extend(stockMotionItems)
            self._isApplyBatch = True
        for nomenclatureId, avialableQntLine in avialableQntDict.items():
            for avialableQnt in avialableQntLine.values():
                if avialableQnt <= 0 and avialableQnt is not None:
                    nomenclatureLine = self._noAvialableQnt.setdefault(actionType.id, [])
                    if nomenclatureId and nomenclatureId not in nomenclatureLine:
                        nomenclatureLine.append(nomenclatureId)
        nomenclatureLine = self._noAvialableQnt.setdefault(actionType.id, [])
        for nomenclatureId in self.selectNomenclatureIdList:
            if nomenclatureId and nomenclatureId not in nomenclatureLine:
                avialableQntLine = avialableQntDict.get(nomenclatureId, {})
                avialableQnt = avialableQntLine.get((None, None, None, None), None)
                if avialableQnt <= 0 and avialableQnt is not None:
                    nomenclatureLine = self._noAvialableQnt.setdefault(actionType.id, [])
                    if nomenclatureId and nomenclatureId not in nomenclatureLine:
                        nomenclatureLine.append(nomenclatureId)
        self._exists = exists

    def updateNomenclatureIdListToAction(self, nomenclatureIdDict):
        _defaultsCache = {}
        def _getDefaultUnitId(nomenclatureId):
            if not nomenclatureId:
                return None
            if nomenclatureId not in _defaultsCache:
                unitId = forceRef(
                    QtGui.qApp.db.translate('rbNomenclature', 'id', nomenclatureId, 'defaultClientUnit_id')
                )
                _defaultsCache[nomenclatureId] = unitId
            return _defaultsCache[nomenclatureId]

        orgStructureId = self._supplierId if self._supplierId else QtGui.qApp.currentOrgStructureId()
        self._stockMotionRecord = self.getNewRecord()
        self._items = []
        self._noAvialableQnt = {}
        avialableQntDict = {}
        actionType = self._action.getType()
        self.selectNomenclatureIdList = nomenclatureIdDict.keys()
        exists = self._getExists(self.selectNomenclatureIdList, filter={'financeId': self._financeId, 'clientId':self._clientId, 'medicalAidKindId':self._medicalAidKindId, 'orgStructureId':self._supplierId, 'begDateAction':forceDate(self._action.getRecord().value('begDate')) if self._action else None})
        for idx, (nomenclatureId, (nomenclativeRecord, dosage)) in enumerate(nomenclatureIdDict.items()):
            stockMotionItem = QtGui.qApp.db.table('StockMotion_Item').newRecord()
            amount = forceDouble(nomenclativeRecord.value('amount'))
#            actionTypeId = forceRef(nomenclativeRecord.value('actionType_id'))
#            actionType = CActionTypeCache.getById(actionTypeId) if actionTypeId else None
#            writeoffTime = forceInt(nomenclativeRecord.value('writeoffTime'))
            stockMotionItem.setValue('nomenclature_id', toVariant(nomenclatureId))
            if actionType.isDoesNotInvolveExecutionCourse:
                stockMotionItem.setValue('qnt', toVariant(self.getIsDoesNotInvolveExecutionCourseQnt(nomenclatureId)))
            elif dosage:
                stockMotionItem.setValue('qnt', toVariant(self.updateNomenclatureDosageToQntValue(nomenclatureId, dosage)))
            else:
                stockMotionItem.setValue('qnt', toVariant(amount*(self._actionAmount if self._actionAmount else 1)))
            stockMotionItem.setValue('unit_id', toVariant(_getDefaultUnitId(nomenclatureId)))
            avialableQntDict, stockMotionItems = self._sync(exists, stockMotionItem, translateExistsQnt=True, financeId=self._financeId, clientId=self._clientId, medicalAidKindId=self._medicalAidKindId, isNoAvialableQnt=True, avialableQntDict=avialableQntDict, orgStructureId=orgStructureId)
            self._items.extend(stockMotionItems)
            self._isApplyBatch = True
        for nomenclatureId, avialableQntLine in avialableQntDict.items():
            for avialableQnt in avialableQntLine.values():
                if avialableQnt <= 0 and avialableQnt is not None:
                    nomenclatureLine = self._noAvialableQnt.setdefault(self._actionType.id, [])
                    if nomenclatureId and nomenclatureId not in nomenclatureLine:
                        nomenclatureLine.append(nomenclatureId)
        nomenclatureLine = self._noAvialableQnt.setdefault(self._actionType.id, [])
        for nomenclatureId in self.selectNomenclatureIdList:
            if nomenclatureId and nomenclatureId not in nomenclatureLine:
                avialableQntLine = avialableQntDict.get(nomenclatureId, {})
                avialableQnt = avialableQntLine.get((None, None, None, None), None)
                if avialableQnt <= 0 and avialableQnt is not None:
                    nomenclatureLine = self._noAvialableQnt.setdefault(self._actionType.id, [])
                    if nomenclatureId and nomenclatureId not in nomenclatureLine:
                        nomenclatureLine.append(nomenclatureId)
        self._exists = exists


    def updateNomenclatureToAction(self, nomenclatureRecordList):
        _defaultsCache = {}
        def _getDefaultUnitId(nomenclatureId):
            if not nomenclatureId:
                return None
            if nomenclatureId not in _defaultsCache:
                unitId = forceRef(
                    QtGui.qApp.db.translate('rbNomenclature', 'id', nomenclatureId, 'defaultClientUnit_id')
                )
                _defaultsCache[nomenclatureId] = unitId
            return _defaultsCache[nomenclatureId]
        orgStructureId = self._supplierId if self._supplierId else QtGui.qApp.currentOrgStructureId()
        self._stockMotionRecord = self.getNewRecord()
        self._items = []
        self._noAvialableQnt = {}
        avialableQntDict = {}
        actionType = self._action.getType()
        self.selectNomenclatureIdList = self._getNomenclatureIdList(nomenclatureRecordList)
        exists = self._getExists(self.selectNomenclatureIdList, filter={'financeId': self._financeId, 'clientId':self._clientId, 'medicalAidKindId':self._medicalAidKindId, 'orgStructureId':self._supplierId, 'begDateAction':forceDate(self._action.getRecord().value('begDate')) if self._action else None})
        for idx, nomenclativeRecord in enumerate(nomenclatureRecordList):
            stockMotionItem = QtGui.qApp.db.table('StockMotion_Item').newRecord()
            nomenclatureId = forceRef(nomenclativeRecord.value('nomenclature_id'))
            amount = forceDouble(nomenclativeRecord.value('amount'))
#            writeoffTime = forceInt(nomenclativeRecord.value('writeoffTime'))
            stockMotionItem.setValue('nomenclature_id', toVariant(nomenclatureId))
            if actionType.isDoesNotInvolveExecutionCourse:
                stockMotionItem.setValue('qnt', toVariant(self.getIsDoesNotInvolveExecutionCourseQnt(nomenclatureId)))
            else:
                stockMotionItem.setValue('qnt', toVariant(amount*(self._actionAmount if self._actionAmount else 1)))
            stockMotionItem.setValue('unit_id', toVariant(_getDefaultUnitId(nomenclatureId)))
            avialableQntDict, stockMotionItems = self._sync(exists, stockMotionItem, translateExistsQnt=True, financeId=self._financeId, clientId=self._clientId, medicalAidKindId=self._medicalAidKindId, isNoAvialableQnt=True, avialableQntDict=avialableQntDict, orgStructureId=orgStructureId)
            self._items.extend(stockMotionItems)
            self._isApplyBatch = True
        for nomenclatureId, avialableQntLine in avialableQntDict.items():
            for avialableQnt in avialableQntLine.values():
                if avialableQnt <= 0 and avialableQnt is not None:
                    nomenclatureLine = self._noAvialableQnt.setdefault(self._actionType.id, [])
                    if nomenclatureId and nomenclatureId not in nomenclatureLine:
                        nomenclatureLine.append(nomenclatureId)
        nomenclatureLine = self._noAvialableQnt.setdefault(self._actionType.id, [])
        for nomenclatureId in self.selectNomenclatureIdList:
            if nomenclatureId and nomenclatureId not in nomenclatureLine:
                avialableQntLine = avialableQntDict.get(nomenclatureId, {})
                avialableQnt = avialableQntLine.get((None, None, None, None), None)
                if avialableQnt <= 0 and avialableQnt is not None:
                    nomenclatureLine = self._noAvialableQnt.setdefault(self._actionType.id, [])
                    if nomenclatureId and nomenclatureId not in nomenclatureLine:
                        nomenclatureLine.append(nomenclatureId)
        self._exists = exists


    def getNomenclatureDosageToQntValue(self, nomenclatureId, dosageValue):
        qnt = 0
        if nomenclatureId:
            nomenclatureRecord = QtGui.qApp.db.getRecord('rbNomenclature', 'defaultClientUnit_id, dosageValue', nomenclatureId)
            if nomenclatureRecord:
                actionType = self._action.getType()
                defaultValue = forceDouble(nomenclatureRecord.value('dosageValue'))
                if defaultValue:
                    if actionType.isDoesNotInvolveExecutionCourse:
                        qnt = calcQuantity(self._action.getRecord(), durationIsValid = True)
                        qnt = qnt*(dosageValue / defaultValue)
                    else:
                        qnt = dosageValue / defaultValue
                elif not actionType.isDoesNotInvolveExecutionCourse:
                    qnt = 1
        return qnt


    def updateNomenclatureDosageToQntValue(self, nomenclatureId, dosageValue):
        qnt = 0
        if nomenclatureId:
            nomenclatureRecord = QtGui.qApp.db.getRecord('rbNomenclature', 'defaultClientUnit_id, dosageValue',
                                                         nomenclatureId)
            if nomenclatureRecord:
                actionType = self._action.getType()
                if actionType.isDoesNotInvolveExecutionCourse:
                    qnt = calcQuantity(self._action.getRecord(), durationIsValid=True)
                    self._action.getRecord().setValue('quantity', toVariant(qnt))
                else:
                    qnt = 1
                defaultValue = forceDouble(nomenclatureRecord.value('dosageValue'))
                if defaultValue:
                    if actionType.isDoesNotInvolveExecutionCourse:
                        qnt = qnt * (dosageValue / defaultValue)
                    else:
                        qnt = dosageValue / defaultValue
        return qnt


    def updateNomenclatureDosageValue(self, nomenclatureId, dosageValue, force=False):
        if not nomenclatureId:
            return

        target = None
        for item in self._items:
            if nomenclatureId == forceRef(item.value('nomenclature_id')):
                target = item
                break

        if not target:
            return

        if not force and forceDouble(target.value('qnt')):
            return

        nomenclatureRecord = QtGui.qApp.db.getRecord(
            'rbNomenclature', 'defaultClientUnit_id, dosageValue', nomenclatureId
        )
        actionType = self._action.getType()
        if actionType.isDoesNotInvolveExecutionCourse:
            qnt = calcQuantity(self._action.getRecord(), durationIsValid = True)
            self._action.getRecord().setValue('quantity', toVariant(qnt))
        defaultValue = forceDouble(nomenclatureRecord.value('dosageValue'))
        if defaultValue:
            if actionType.isDoesNotInvolveExecutionCourse:
                qnt = qnt*(dosageValue / defaultValue)
            else:
                qnt = dosageValue / defaultValue
            target.setValue('qnt', toVariant(qnt))
        elif actionType.isDoesNotInvolveExecutionCourse:
            target.setValue('qnt', toVariant(qnt))


    def getIsDoesNotInvolveExecutionCourseQnt(self, nomenclatureId):
        nomenclatureRecord = QtGui.qApp.db.getRecord(
            'rbNomenclature', 'defaultClientUnit_id, dosageValue', nomenclatureId
        )
        dosageValue = forceDouble(nomenclatureRecord.value('dosageValue'))
        qnt = calcQuantity(self._action.getRecord(), durationIsValid = True)
        self._action.getRecord().setValue('quantity', toVariant(qnt))
        if dosageValue:
            for properties in self._action._properties:
                type = properties._type
                name = type.name
                if type.inActionsSelectionTable == _DOSES:  # doses
                    property = self._action.getProperty(name)
                    doses = property.getValue()
                    if isinstance(doses, (float, int)):
                        qnt = qnt*(doses / dosageValue)
                        break
        return qnt


    def addNomenclatureEx(self, nomenclatureId, financeId=None, medicalAidKindId=None):
        if not nomenclatureId:
            return

        if financeId:
            self._financeId = financeId

        if medicalAidKindId:
            self._medicalAidKindId = medicalAidKindId

        for item in self._items:
            if nomenclatureId == forceRef(item.value('nomenclature_id')):
                return

        nomenclatureIdDict = {}
        dosage = self._action.findDosagePropertyValue()
        if self._action.nomenclatureExpense:
            self._action = updateNomenclatureDosageValue(self._action)
            executionPlanItem = self._action.executionPlanManager.currentItem
            if executionPlanItem and executionPlanItem.nomenclature and executionPlanItem.nomenclature.nomenclatureId:
                if executionPlanItem.nomenclature.nomenclatureId:
                    dosage = executionPlanItem.nomenclature.dosage
        if dosage:
            nomenclatureIdDict[nomenclatureId] = (self._action.getRecord(), dosage)
            self.updateNomenclatureIdListToAction(nomenclatureIdDict)


    def addNomenclature(self, nomenclatureId, financeId=None, medicalAidKindId=None):
        if not nomenclatureId:
            return

        if financeId:
            self._financeId = financeId

        if medicalAidKindId:
            self._medicalAidKindId = medicalAidKindId

        for item in self._items:
            if nomenclatureId == forceRef(item.value('nomenclature_id')):
                return

        if not self._stockMotionRecord:
            self._stockMotionRecord = self.getNewRecord()

        nomenclatureRecord = QtGui.qApp.db.getRecord(
            'rbNomenclature', 'defaultClientUnit_id, dosageValue', nomenclatureId
        )
        unitId = forceRef(forceRef(nomenclatureRecord.value('defaultClientUnit_id')))
        dosageValue = forceDouble(nomenclatureRecord.value('dosageValue'))
        actionType = self._action.getType()
        if actionType.isDoesNotInvolveExecutionCourse:
            qnt = calcQuantity(self._action.getRecord(), durationIsValid = True)
            self._action.getRecord().setValue('quantity', toVariant(qnt))
        else:
            qnt = 1
        if dosageValue:
            for properties in self._action._properties:
                type = properties._type
                name = type.name
                if type.inActionsSelectionTable == _DOSES:  # doses
                    property = self._action.getProperty(name)
                    doses = property.getValue()
                    if isinstance(doses, (float, int)):
                        if actionType.isDoesNotInvolveExecutionCourse:
                            qnt = qnt*(doses / dosageValue)
                        else:
                            qnt = doses / dosageValue
                        break

        self._necessaryQnt = qnt
        self._isApplyBatch = False
        while self._necessaryQnt > 0 and self._avialableQnt != -1:
            stockMotionItem = self._tableStockMotionItem.newRecord()
            stockMotionItem.setValue('nomenclature_id', toVariant(nomenclatureId))
            stockMotionItem.setValue('unit_id', toVariant(unitId))
            self._applyBatchFinanceIdShelfTime(stockMotionItem)
            if self._avialableQnt != -1:
                stockMotionItem.setValue('qnt', toVariant(self._avialableQnt))
            #elif QtGui.qApp.controlSMFinance() == 0:
            #    stockMotionItem.setValue('qnt', toVariant(0))
            if forceDouble(stockMotionItem.value('qnt')) > 0:
                stockMotionItem.setValue('sum', toVariant(forceDouble(stockMotionItem.value('price')) * forceDouble(stockMotionItem.value('qnt'))))
                self._items.insert(0, stockMotionItem)
            self._necessaryQnt = self._necessaryQnt - self._avialableQnt

    def _applyBatchFinanceIdShelfTime(self, item):
        avialableQnt = None
        if not self._necessaryQnt:
            self._necessaryQnt = forceDouble(item.value('qnt'))
        nomenclatureId = forceRef(item.value('nomenclature_id'))
        unitId = forceRef(item.value('unit_id'))
        stockUnitId = forceRef(QtGui.qApp.db.translate('rbNomenclature', 'id', nomenclatureId, 'defaultStockUnit_id'))
        qnt = round(applyNomenclatureUnitRatio(self._necessaryQnt, nomenclatureId, unitId, revert=True), 2)
        orgStructureId = self._supplierId if self._supplierId else QtGui.qApp.currentOrgStructureId()
        self._financeId = self._action.getFinanceId()
        self._medicalAidKindId = self._action.getMedicalAidKindId()
        if self._reservationUsed:
            financeId, batch, shelfTime, medicalAidKindId, price, reservationClient = findFinanceBatchShelfTime(orgStructureId, nomenclatureId, qnt, financeId=self._financeId, medicalAidKind=self._medicalAidKindId, oldUnitId=stockUnitId)
        else:
            financeId, batch, shelfTime, medicalAidKindId, price, reservationClient = findFinanceBatchShelfTime(orgStructureId, nomenclatureId, qnt, clientId=self._clientId, financeId=self._financeId, medicalAidKind=self._medicalAidKindId, oldUnitId=stockUnitId)
        if financeId or batch or shelfTime or price:
            priceFind = price
            if stockUnitId and stockUnitId != unitId:
                ratioFind = getRatio(nomenclatureId, stockUnitId, unitId)
                if ratioFind is not None:
                    priceFind = priceFind*ratioFind
            avialableQnt = round(getExistsNomenclatureAmount(nomenclatureId, financeId = financeId, batch=batch, orgStructureId = orgStructureId, unitId = unitId, medicalAidKindId = medicalAidKindId, exact=True, price=priceFind), 2)
        if avialableQnt <= self._necessaryQnt and avialableQnt>0:
            if self._reservationUsed:
                self._avialableQnt = -1
                if avialableQnt>0:
                    item.setValue('qnt', toVariant(avialableQnt))
            else:
                if avialableQnt>0:
                    self._avialableQnt = avialableQnt
                self._reservationUsed = True
        elif avialableQnt<0:
            self._avialableQnt = -1
        else:
            self._avialableQnt = self._necessaryQnt

            item.setValue('finance_id', toVariant(financeId))
            item.setValue('batch', toVariant(batch))
            item.setValue('shelfTime', toVariant(shelfTime))
        item.setValue('medicalAidKind_id', toVariant(medicalAidKindId))
        self._isApplyBatch = True
        if price and unitId and not reservationClient:
            ratio = getRatio(nomenclatureId, unitId, None)
            if ratio is not None:
                price = price*ratio
        item.setValue('price', toVariant(price))

        if self._avialableQnt<0 and not financeId and not batch and not medicalAidKindId and QtGui.qApp.controlSMFinance() == 0:
            avialableQnt = round(getExistsNomenclatureAmount(nomenclatureId, financeId = financeId, batch=batch, orgStructureId = orgStructureId, unitId = unitId, medicalAidKindId = medicalAidKindId, exact=True, price=price), 2)
            if avialableQnt>0:
                self._avialableQnt = avialableQnt
        if self._avialableQnt > 0:
            item.setValue('sum', toVariant(forceDouble(item.value('price')) * forceDouble(item.value('qnt'))))
        else:
            nomenclatureLine = self._noAvialableQnt.setdefault(self._actionType.id, [])
            if nomenclatureId and nomenclatureId not in nomenclatureLine:
                nomenclatureLine.append(nomenclatureId)


    def removeNomenclature(self, nomenclatureId):
        rows  = []
        if nomenclatureId:
            for row, item in enumerate(self._items):
                if forceRef(item.value('nomenclature_id')) == nomenclatureId:
                    rows.append(row)
        for row in reversed(rows): 
            if 0<=row and row+1<=len(self._items):
                del self._items[row:row+1]     
                    #self._items.remove(item)
                    #break


    def _load(self, actionId):
        db = QtGui.qApp.db
        self._stockMotionId = forceRef(db.translate('Action', 'id', actionId, 'stockMotion_id'))
        if self._stockMotionId:
            self._stockMotionRecord = db.getRecord(self._tableStockMotion, '*', self._stockMotionId)
            self._items = db.getRecordList(self._tableStockMotionItem, '*', 'master_id=%d'%self._stockMotionId)
            return bool(self._stockMotionRecord)
        else:
            self._setActionType(self._actionType)
            #for properties in self._action._properties:
            #    type = properties._type
            #    name = type.name
            #    if type.isNomenclatureValueType():
            #        property = self._action.getProperty(name)
            #        nomencalureId = property.getValue()
            #        if nomencalureId:
            #            self.addNomenclatureEx(nomencalureId)
        return False


    def _getReason(self):
        if self._actionType and self._actionType.generateStockMotionReason:
            actionId = forceRef(self._action.getRecord().value('id'))
            if actionId:
                return u'/'.join([self._actionType.code, unicode(actionId)])
        return None


    def _generateStockMotionNumber(self):
        if not self._stockMotionRecord or not QtGui.qApp.counterController():
            return

        number = forceString(self._stockMotionRecord.value('number'))
        if number:
            return

        counterId = getStockMotionNumberCounterId(4) #списание на пациента
        if not counterId:
            return

        number = QtGui.qApp.getDocumentNumber(None, counterId, date=QtCore.QDate.currentDate())

        self._stockMotionRecord.setValue('number', number)


    def save(self, nomenclatureExpensePreliminarySave = False, isActionNoSave = False):
        if self._stockMotionRecord:
            self._generateStockMotionNumber()
            db = QtGui.qApp.db
            if not forceStringEx(self._stockMotionRecord.value('reason')):
                reason = self._getReason()
                if reason:
                    self._stockMotionRecord.setValue('reason', toVariant(reason))
            self._stockMotionId = db.insertOrUpdate(self._tableStockMotion, self._stockMotionRecord)
            self._releaseReservation(isActionNoSave = isActionNoSave)
            stockMotionItemIdList = []
            for stockMotionItem in self._items:
                stockMotionItem.setValue('master_id', toVariant(self._stockMotionId))
                if not forceRef(stockMotionItem.value('id')) and not nomenclatureExpensePreliminarySave and not self._isApplyBatch:
                    self._applyBatchFinanceIdShelfTime(stockMotionItem)
                stockMotionItemIdList.append(db.insertOrUpdate(self._tableStockMotionItem, stockMotionItem))
            filter = [self._tableStockMotionItem['master_id'].eq(self._stockMotionId),
                      'NOT ('+self._tableStockMotionItem['id'].inlist(stockMotionItemIdList)+')']
            db.deleteRecord(self._tableStockMotionItem, filter)
            return self._stockMotionId


    def getExecutionPlanIsDirty(self, action, nomenclatureId):
        if action:
            executionPlan = action.getExecutionPlan()
            if executionPlan:
                items = executionPlan.items
                for item in items:
                    if item.getIsDirty() and item.nomenclature and item.nomenclature.nomenclatureId == nomenclatureId:
                        return True
        return False


    def _reverseNomenclature(self):
        if not self._action.nomenclatureClientReservation:
            return

        #actionId = self._action.getId()
        #if not actionId:
        #    return

        for item in self._items:
            self._action.nomenclatureClientReservation.reverseNomenclature(item)


    def _releaseReservation(self, isActionNoSave = False):
        if not self._action.nomenclatureClientReservation:
            return

        if not isActionNoSave:
            actionId = self._action.getId()
            if not actionId:
                return

        for item in self._items:
            if forceRef(item.value('id')):
                continue

            self._action.nomenclatureClientReservation.releaseNomenclature(item)


    def _releaseReservationToNomenclatureId(self, nomenclatureId):
        if not self._action.nomenclatureClientReservation:
            return
        actionId = self._action.getId()
        if not actionId:
            return
        for item in self._items:
            if nomenclatureId == forceRef(item.value('nomenclature_id')):
                self._action.nomenclatureClientReservation.releaseNomenclature(item)


def initActionProperties(action):
    actionType = action.getType()
    propertyTypeList = actionType.getPropertiesById().values()
    for propertyType in propertyTypeList:
        action.getPropertyById(propertyType.id)


####################################################

#def ensureActionTypePresence(actionTypeCode, propTypeList=[]):
#    db = QtGui.qApp.db
#    tableActionType = db.table('ActionType')
#    tablePropertyType = db.table('ActionPropertyType')
#    actionTypeRecord = db.getRecordEx(tableActionType, '*', tableActionType['code'].eq(actionTypeCode))
#    if actionTypeRecord:
#        actionTypeId = forceRef(actionTypeRecord.value('id'))
#    else:
#        actionTypeRecord = tableActionType.newRecord()
#        actionTypeRecord.setValue('code',  toVariant(actionTypeCode))
#        actionTypeId = db.insertOrUpdate(tableActionType, actionTypeRecord)
#    if propTypeList:
#        for propTypeDef in propTypeList:
#            name = propTypeDef.get('name', None)
#            descr = propTypeDef.get('descr', None)
#            unit = propTypeDef.get('unit', None)
#            typeName = propTypeDef.get('typeName', 'String')
#            valueDomain = propTypeDef.get('valueDomain', None)
#            isVector = propTypeDef.get('isVector', False)
#            norm = propTypeDef.get('norm', None)
#            sex = propTypeDef.get('sex', None)
#            age = propTypeDef.get('age', None)
#
#            propertyTypeRecord = db.getRecordEx(tablePropertyType, '*', [tablePropertyType['actionType_id'].eq(actionTypeId), tablePropertyType['name'].eq(name)])
#            if propertyTypeRecord:
#                pass
#            else:
#                propertyTypeRecord = tablePropertyType.newRecord()
#                propertyTypeRecord.setValue('actionType_id', toVariant(actionTypeId))
#                propertyTypeRecord.setValue('name', toVariant(name))
#                propertyTypeRecord.setValue('descr', toVariant(descr))
#                if unit:
#                    unitId = db.translate('rbUnit', 'code', unit, 'id')
#                    if unitId:
#                        propertyTypeRecord.setValue('descr', unitId)
#                propertyTypeRecord.setValue('typeName', toVariant(CActionPropertyValueTypeRegistry.normTypeName(typeName)))
#                propertyTypeRecord.setValue('valueDomain', toVariant(valueDomain))
#                propertyTypeRecord.setValue('isVector',    toVariant(isVector))
#                propertyTypeRecord.setValue('norm',        toVariant(norm))
#                propertyTypeRecord.setValue('sex',         toVariant(sex))
#                propertyTypeRecord.setValue('age',         toVariant(age))
#                db.insertRecord(tablePropertyType, propertyTypeRecord)

####################################################



####################################################################
# сценарий работы c Actions:
#
# 1) создание Action
#    a1 = CAction.createByTypeCode(10)
# 2) загрузка Action
#    a2 = CAction(record=query.record())
# 3) сохранение Action
#    a1.save(eventId)
#    a2.save()
# 4) доступ к свойствам Action
#    x = a2['value']
# 5) изменение свойства Action
#    a2['value'] = x
# 6) очистка/удаление свойства Action
#    del a2['value']
# 7) векторные свойства?
