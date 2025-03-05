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

import os
from sys import platform
import re
import json
import math

from PyQt4 import QtGui, QtSql
from PyQt4.QtCore import Qt, SIGNAL, QDate, QObject, QVariant, QTime, QDateTime, pyqtSignature
from Events.ActionRelations.Groups import CRelationsProxyModelGroup
from Events.ExecutionPlan.Groups import CExecutionPlanProxyModelGroup

from Orgs.Utils import getPersonOrgStructureChiefs

from Users.Rights import ( 
                        urAdmin,
                        urEditClosedEvent,
                        urEditOtherpeopleAction,
                        urEditOtherPeopleActionSpecialityOnly,
                        urEditSubservientPeopleAction,
                        urEditAfterReturnEvent
                        )

from Events.InputDialog import CInputDialog
from library.AgeSelector         import checkAgeSelector, parseAgeSelector
from library.crbcombobox              import CRBModelDataCache
from library.PrintInfo           import CInfo, CDateInfo
from library.Calendar            import countWorkDays
from library.DbEntityCache       import CDbEntityCache
from library.ICDUtils            import MKBwithoutSubclassification
from library.PrintInfo           import CInfoContext
from library.Utils                    import calcAgeTuple, trim, firstHalfYearDay, firstMonthDay, firstQuarterDay, firstWeekDay, firstYearDay, forceBool, forceDate, forceDouble, forceInt, forceRef, forceString, forceStringEx, forceTime, formatName, lastHalfYearDay, lastMonthDay, lastQuarterDay, lastWeekDay, lastYearDay, toVariant, pyDate
from library.Preferences                import CPreferences
from library                import database
from library.InDocTable          import CInDocTableView

from Events.MKBInfo              import CMKBInfo
from RefBooks.Service.Info            import CServiceInfo

from Stock.Utils                      import applyNomenclatureUnitRatio, getExistsNomenclatureStmt, getRatio, getExistsNomenclatureAmount

from RefBooks.Service.ServiceModifier import parseModifier, applyModifier

from Registry.Utils                   import getClientCompulsoryPolicy, getClientVoluntaryPolicy, getClientAttaches
from TissueJournal.TissueStatus  import CTissueStatus

_RECIPE = 1
_DOSES  = 2
_SIGNA  = 3
_ACTIVESUBSTANCE = 4

orderTexts = [
    u'-',
    u'плановый',
    u'экстренный',
    u'самотёком',
    u'принудительный',
    u'внутренний перевод',
    u'неотложная',
    ]


inPlanOperatingDay = [u'-',
                      u'ассистент',
                      u'анестезиолог',
                      u'ассистент анестезиолога',
                      u'особые отметки',
                      u'длительность операции',
                      u'номер по порядку',
                      u'работа',
                      u'предоперационный диагноз',
                      ]


inMedicalDiagnosis = [u'-',
                      u'Основной',
                      u'Осложнения',
                      u'Сопутствующие'
                      ]


medicalDiagnosisType = [u'основной',
                        u'осложнения',
                        u'сопутствующие'
                        ]


def getOrderText(order):
    if 0<=order<len(orderTexts):
        return orderTexts[order]
    else:
        return '{%s}' % order


def getWorkEventTypeFilter(isApplyActive=True):
    filter = """(EventType.purpose_id NOT IN (
                SELECT rbEventTypePurpose.id from rbEventTypePurpose where rbEventTypePurpose.code = '0')) 
                /*AND EventType.context NOT LIKE 'inspection%'*/ AND EventType.context NOT LIKE 'relatedAction%'
                AND EventType.deleted = 0"""
    if forceBool(QtGui.qApp.preferences.appPrefs.get('isPreferencesEventTypeActive', False)) and isApplyActive:
        filter += u''' AND EventType.isActive = 1'''
    filter += ''' AND (EventType.context != 'flag' AND EventType.code != 'flag') '''
    return filter

def getOrgStructureEventTypeFilter(orgStructureId):
    idSet = set()
    db = QtGui.qApp.db
    tableOrgStructure = db.table('OrgStructure')
    tableOSET = db.table('OrgStructure_EventType')
    while orgStructureId:
        idList = db.getIdList(tableOSET, idCol='eventType_id',  where=tableOSET['master_id'].eq(orgStructureId))
        idSet.update(set(idList))
        record = db.getRecord(tableOrgStructure, ['parent_id', 'inheritEventTypes'], orgStructureId)
        if record and forceBool(record.value('inheritEventTypes')):
            orgStructureId = forceRef(record.value('parent_id'))
        else:
            orgStructureId = None
    idList = list(idSet.difference(set([None])))
    if idList:
        return db.table('EventType')['id'].inlist(idList)
    else:
        return 'True'


def getEventContextData(editor):
    from Events.TempInvalidInfo import CTempInvalidInfo
    context = CInfoContext()
    eventInfo = editor.getEventInfo(context)
    eventInfo.setFocusToWidget = editor.setFocusToWidget
    eventInfo.getActionsTabsList = editor.getActionsTabsList
    if hasattr(editor, 'getTempInvalidInfo'):
        tempInvalidInfo = editor.getTempInvalidInfo(context)
    else:
        tempInvalidInfo = context.getInstance(CTempInvalidInfo, None)
    data = { 'event' : eventInfo,
             'client': eventInfo.client,
             'tempInvalid': tempInvalidInfo,
            }
    return data


def getIsRequiredCoordination(actionTypeId):
    db = QtGui.qApp.db
    tableActionType = db.table('ActionType')
    record = db.getRecordEx(tableActionType,
                            [tableActionType['isRequiredCoordination']],
                            [tableActionType['id'].eq(actionTypeId), tableActionType['deleted'].eq(0)])
    return forceBool(record.value('isRequiredCoordination')) if record else False


def getChiefId(orgStructureId):
    chiefId = None
    if orgStructureId:
        db = QtGui.qApp.db
        table = db.table('OrgStructure')
        record = db.getRecordEx(table, [table['chief_id']], [table['id'].eq(orgStructureId), table['deleted'].eq(0)])
        chiefId = forceRef(record.value('chief_id')) if record else None
    return chiefId


def getHealthGroupFilter(birthDate, begDate):
    return """
(ageFrom is NULL OR ageFrom <= age('{birthDate}', '{begDate}'))
AND (ageTo is NULL OR ageTo >= age('{birthDate}', '{begDate}'))
AND (begDate is NULL OR begDate <= '{begDate}')
AND (endDate is NULL OR endDate >= '{begDate}')
""".format(birthDate=birthDate, begDate=begDate)

class CActionCSGComboBox(QtGui.QComboBox):
    def __init__(self,  parent = None):
        QtGui.QComboBox.__init__(self, parent)
        self.eventEditor = None
        self.currentIndexChanged.connect(self.on_indexChanged)
        self.mapIndexToCSGRecord = {-1: None, 0: None}
        self.mapCSGRecordToIndex = {}
        self.mapIdToCSGRecord = {}
        self.mapActionToCSG = {}
        self.currentRecord = None


    def setEventEditor(self, eventEditor):
        self.eventEditor = eventEditor


    def setItems(self):
        currentCSGRecord = self.mapIndexToCSGRecord[self.currentIndex()]
        currentActionRecord = self.currentRecord
        self.currentRecord = None
        self.clear()
        self.mapIndexToCSGRecord = {-1: None, 0: None}
        self.mapCSGRecordToIndex = {}
        self.addItem(u"Нет")
        if self.eventEditor:
            if hasattr(self.eventEditor, 'tabMes'):
                index = 1
                for seqNum, record in enumerate(self.eventEditor.tabMes.modelCSGs.items()):
                    csgCode = forceString(record.value('CSGCode'))
                    csgEndDate = forceDate(record.value('endDate'))
                    id = forceRef(record.value('id'))
                    if id:
                        self.mapIdToCSGRecord[id] = record
                    self.mapIndexToCSGRecord[index] = record
                    self.mapCSGRecordToIndex[record] = index
                    code = '%i: '%(seqNum+1) + '%s - %s'%(csgCode, forceString(csgEndDate)) if csgEndDate else csgCode
                    self.addItem(code)
                    index += 1
                    subItems = self.eventEditor.tabMes.modelCSGSubItems.mapRecordToItems.get(record, [])
                    for srecord in subItems:
                        csgCode = forceString(srecord.value('CSGCode'))
                        csgEndDate = forceDate(srecord.value('endDate'))
                        id = forceRef(srecord.value('id'))
                        if id:
                            self.mapIdToCSGRecord[id] = srecord
                        self.mapIndexToCSGRecord[index] = srecord
                        self.mapCSGRecordToIndex[srecord] = index
                        code = u' доп %s - %s'%(csgCode, forceString(csgEndDate)) if csgEndDate else u' доп %s'%csgCode
                        self.addItem(code)
                        index += 1

        if currentCSGRecord:
            self.setCurrentIndex(self.mapCSGRecordToIndex.get(currentCSGRecord, 0))
        if currentActionRecord:
            self.currentRecord = currentActionRecord


    def setCurrentActionRecord(self, record):
        self.currentRecord = record
        if record:
            index = 0
            if not self.mapActionToCSG.get(record, None):
                id = forceRef(record.value('eventCSG_id'))
                csgRecord = self.mapIdToCSGRecord.get(id, None)
                self.mapActionToCSG[record] = csgRecord
            else:
                csgRecord = self.mapActionToCSG[record]
            if csgRecord:
                index = self.mapCSGRecordToIndex[csgRecord]
            self.setCurrentIndex(index)


    def addActionToCSG(self, record, csgRecord):
        self.currentRecord = record
        if record:
            self.mapActionToCSG[record] = csgRecord


    def on_indexChanged(self, index):
        if self.currentRecord:
            csgRecord = self.mapIndexToCSGRecord[index]
            self.mapActionToCSG[self.currentRecord] = csgRecord
            if index <= 0:
                id = forceRef(self.currentRecord.value('eventCSG_id'))
                #self.currentRecord.setValue('eventCSG_id', None)
                self.mapIdToCSGRecord[id] = None


    def saveCSG(self):
        for aRecord in self.mapActionToCSG.keys():
            if aRecord:
                csgRecord = self.mapActionToCSG[aRecord]
                if csgRecord:
                    aRecord.setValue('eventCSG_id', csgRecord.value('id'))
                else:
                    aRecord.setValue('eventCSG_id', toVariant(None))


    def showPopup(self):
        self.setItems()
        QtGui.QComboBox.showPopup(self)

# ######################################################

# коды типов финиасирования, должны соотв. кодам из rbFinance
class CFinanceType(CDbEntityCache):
    budget   = 1 # бюджет
    CMI      = 2 # ОМС
    VMI      = 3 # ДМС
    cash     = 4 # платный
    paid     = 4 # платный (устар.)
    targeted = 5 # целевой

    allCodes = (budget, CMI, VMI, cash, targeted)

    mapCodeToId = {}
    mapIdToCode = {}
    mapIdToName = {}

    @classmethod
    def purge(cls):
        cls.mapCodeToId.clear()
        cls.mapIdToCode.clear()
        cls.mapIdToName.clear()


    @classmethod
    def register(cls, record, code=0, id=None):
        if record:
            id   = forceRef(record.value('id'))
            code = forceInt(record.value('code'))
            name = forceString(record.value('name'))
        else:
            name = 'unknow finance code=%r, id=%r' % (code, id)
        cls.mapCodeToId[code] = id
        cls.mapIdToCode[id] = code
        cls.mapIdToName[id] = name
        return id, code, name


    @classmethod
    def getId(cls, code):
        code = forceInt(code)
        if code in cls.mapCodeToId:
            return cls.mapCodeToId[code]
        else:
            cls.connect()
            db = QtGui.qApp.db
            table = db.table('rbFinance')
            id, code, name = cls.register(db.getRecordEx(table, 'id, code, name', table['code'].eq(code)), code=code)
            return id


    @classmethod
    def getCode(cls, id):
        if id in cls.mapIdToCode:
            return cls.mapIdToCode[id]
        else:
            cls.connect()
            db = QtGui.qApp.db
            table = db.table('rbFinance')
            id, code, name = cls.register(db.getRecord(table, 'id, code, name', id), id=id)
            return code


    @classmethod
    def getNameById(cls, id):
        cls.getCode(id)
        return cls.mapIdToName[id]

    @classmethod
    def getNameByCode(cls, code):
        return cls.mapIdToName[cls.getId(code)]


class CTestDescription(CDbEntityCache):
    mapCodeToId = {}
    mapIdToCode = {}
    mapIdToName = {}
    mapIdTotestInEquipment = {}

    @classmethod
    def purge(cls):
        cls.mapCodeToId.clear()
        cls.mapIdToCode.clear()
        cls.mapIdToName.clear()
        cls.mapIdTotestInEquipment.clear()


    @classmethod
    def register(cls, record, code='0', id=None):
        testInEquipment = {}
        if record:
            db = QtGui.qApp.db
            id   = forceRef(record.value('id'))
            code = forceString(record.value('code'))
            name = forceString(record.value('name'))
            table = db.table('rbEquipment_Test')
            equipTestRecordList = db.getRecordList(table, '*', table['test_id'].eq(id))
            for eRecord in equipTestRecordList:
                equipId = forceRef(eRecord.value('equipment_id'))
                hCode = forceString(eRecord.value('hardwareTestCode'))
                hName = forceString(eRecord.value('hardwareTestName'))
                testInEquipment[equipId] = {'hCode':hCode, 'hName':hName}
        else:
            name = 'unknown test code=%r, id=%r' % (code, id)
        cls.mapCodeToId[code] = id
        cls.mapIdToCode[id] = code
        cls.mapIdToName[id] = name
        cls.mapIdTotestInEquipment[id] = testInEquipment
        return id, code, name, testInEquipment


    @classmethod
    def getId(cls, code):
        code = forceString(code)
        if code in cls.mapCodeToId:
            return cls.mapCodeToId[code]
        else:
            cls.connect()
            db = QtGui.qApp.db
            table = db.table('rbTest')
            id, code, name, testInEquipment = cls.register(db.getRecordEx(table, 'id, code, name', table['code'].eq(code)), code=code)
            return id


    @classmethod
    def getCode(cls, id):
        if id in cls.mapIdToCode:
            return cls.mapIdToCode[id]
        else:
            cls.connect()
            db = QtGui.qApp.db
            table = db.table('rbTest')
            id, code, name, testInEquipment = cls.register(db.getRecord(table, 'id, code, name', id), id=id)
            return code


    @classmethod
    def getTestInEquipment(cls, id):
        if id in cls.mapIdTotestInEquipment:
            return cls.mapIdTotestInEquipment[id]
        else:
            cls.connect()
            db = QtGui.qApp.db
            table = db.table('rbTest')
            id, code, name, testInEquipment = cls.register(db.getRecord(table, 'id, code, name', id), id=id)
            return testInEquipment


class CEquipmentDescription(CDbEntityCache):
    mapIdToDescription = {}

    @classmethod
    def purge(cls):
        cls.mapIdToDescription.clear()

    @classmethod
    def register(cls, record, code = '0', id=None, protocol = 0):
        if record:
            id   = forceRef(record.value('id'))
            code = forceString(record.value('code'))
            name = forceString(record.value('name'))
            ownName = forceString(record.value('ownName'))
            protocol = forceInt(record.value('protocol'))
            try:
                address = json.loads(forceString(record.value('address')))
            except:
                address = {}
            description = {'code': code, 'name':name, 'protocol':protocol, 'ownName':ownName, 'address':address}
        else:
            name = 'unknown equipment'
            description = {}
        cls.mapIdToDescription[id] = description
        return description


    @classmethod
    def getDescription(cls, id):
        if id in cls.mapIdToDescription:
            return cls.mapIdToDescription[id]
        else:
            cls.connect()
            db = QtGui.qApp.db
            table = db.table('rbEquipment')
            description  = cls.register(db.getRecord(table, '*', id), id=id)
            return description


class CEventTypeDescription(CDbEntityCache):
    cache = {}
    mapCodeToId = {}

    #contract, planner, orgstructure condition in F9
    cDefault = 0
    cYes     = 1
    cNo      = 2

    def __init__(self, eventTypeId):
        db = QtGui.qApp.db
        tableEventType = db.table('EventType')
        tableFinance   = db.table('rbFinance')
        tableMedicalAidKind = db.table('rbMedicalAidKind')
        tableMedicalAidType = db.table('rbMedicalAidType')
        tableEventTypePurpose = db.table('rbEventTypePurpose')
        table = tableEventType.leftJoin(tableFinance, tableFinance['id'].eq(tableEventType['finance_id']))
        table = table.leftJoin(tableMedicalAidKind, tableMedicalAidKind['id'].eq(tableEventType['medicalAidKind_id']))
        table = table.leftJoin(tableMedicalAidType, tableMedicalAidType['id'].eq(tableEventType['medicalAidType_id']))
        table = table.leftJoin(tableEventTypePurpose, tableEventTypePurpose['id'].eq(tableEventType['purpose_id']))
        record = db.getRecordEx(table,('EventType.id as eventTypeId',
                                       'EventType.code AS code',
                                       'EventType.name AS name',
                                       'EventType.age  AS eventAgeSelector',
                                       'period',
                                       'isPrimary',
                                       'EventType.order',
                                       'singleInPeriod',
                                       'isLong',
                                       'isTerritorialBelonging',
                                       'dateInput',
                                       'fillNextEventDate',
                                       'form',
                                       'minDuration',
                                       'maxDuration',
                                       'finance_id',
                                       'medicalAidKind_id',
                                       'addVisit',
                                       'weekProfileCode',
                                       'showVisitTime',
                                       'scene_id',
                                       'visitServiceModifier',
                                       'visitServiceFilter',
                                       'visitFinance',
                                       'actionFinance',
                                       'actionContract',
                                       'contractCondition',
                                       'plannerCondition',
                                       'onlyNotExistsCondition',
                                       'nomenclatureCondition',
                                       'mesCondition',
                                       'orgStructureCondition',
                                       'rbFinance.code as financeCode',
                                       'showTime',
                                       'showButtonAccount',
                                       'counter_id',
                                       'voucherCounter_id',
                                       'isExternal',
                                       'hasAssistant',
                                       'hasCurator',
                                       'relegationRequired',
                                       'hasVisitAssistant',
                                       'canHavePayableActions',
                                       'rbMedicalAidKind.code as aidKindCode',
                                       'rbMedicalAidType.id   as aidType_id',
                                       'rbMedicalAidType.code as aidTypeCode',
                                       'rbMedicalAidType.regionalCode as aidTypeRegionalCode',
                                       'showStatusActionsInPlanner',
                                       'showDiagnosticActionsInPlanner',
                                       'showCureActionsInPlanner',
                                       'showMiscActionsInPlanner',
                                       'purpose_id',
                                       'rbEventTypePurpose.code as purposeCode',
                                       'service_id',
                                       'context',
                                       'mesRequired',
                                       'mesRequiredParams',
                                       'csgRequired',
                                       'isTakenTissue',
                                       'mesCodeMask',
                                       'mesNameMask',
                                       'csgCodeMask',
                                       'subCsgCodeMask',
                                       'mesServiceMask',
                                       'eventProfile_id',
                                       'isOrgStructurePriority',
                                       'limitActionTypes',
                                       'includeTooth',
                                       'prevEventType_id',
                                       'setPerson',
                                       'requiredCondition',
                                       'actionsControlEnabled',
                                       'isAutoFillingExpertise',
                                       'isCheckedExecDateForVisit',
                                       'isResolutionOfDirection',
                                       'showActionTypesWithoutService',
                                       'unfinishedAction',
                                       'actionsBeyondEvent',
                                       'keepVisitParity',
                                       'isRestrictVisitTypeAgeSex',
                                       'mesSpecification_id',
                                       'showButtonTemperatureList',
                                       'showButtonNomenclatureExpense',
                                       'showButtonJobTickets',
                                       'relOrg_id',
                                       'relcounter_id'
                                       ), tableEventType['id'].eq(eventTypeId))
        if not record:
            record = QtSql.QSqlRecord()
        self.eventTypeId = forceRef(record.value('eventTypeId'))
        self.code = forceString(record.value('code'))
        self.name = forceString(record.value('name'))
        self.isPrimary = forceInt(record.value('isPrimary'))
        self.order = forceInt(record.value('order'))
        self.ageSelector = parseAgeSelector(forceString(record.value('eventAgeSelector')))
        self.purposeId = forceRef(record.value('purpose_id'))
        self.purposeCode = forceString(record.value('purposeCode'))
        self.period = max(0, forceInt(record.value('period')))
        self.singleInPeriod = min(7, max(0, forceInt(record.value('singleInPeriod'))))
        self.periodEx = getEventPeriod(self.period, self.singleInPeriod)
        self.isLong = forceBool(record.value('isLong'))
        self.isTerritorialBelonging = forceInt(record.value('isTerritorialBelonging'))
        self.isAutoFillingExpertise = forceBool(record.value('isAutoFillingExpertise'))
        self.dateInput = forceInt(record.value('dateInput'))
        self.fillNextEventDate = forceBool(record.value('fillNextEventDate'))
        self.isUrgent = self.code == '22'
#            self.isDeath  = self.code == '15'
        self.isDeath  = self.purposeCode == '5'
        self.form = forceString(record.value('form'))
        self.financeId = forceRef(record.value('finance_id'))
        self.financeCode = forceInt(record.value('financeCode'))
        self.medicalAidKindId = forceRef(record.value('medicalAidKind_id'))
        self.canHavePayableActions = forceBool(record.value('canHavePayableActions')) or self.financeCode == 4
        self.addVisit = forceBool(record.value('addVisit'))
        self.weekProfileCode = forceInt(record.value('weekProfileCode'))
        self.sceneId = forceRef(record.value('scene_id'))
        self.visitServiceModifier = forceString(record.value('visitServiceModifier'))
        self.visitServiceFilter = forceString(record.value('visitServiceFilter'))
        self.visitFinance = forceInt(record.value('visitFinance'))
        self.actionFinance = forceInt(record.value('actionFinance'))
        self.actionContract = forceInt(record.value('actionContract'))
        self.contractCondition = forceInt(record.value('contractCondition'))
        self.plannerCondition = forceInt(record.value('plannerCondition'))
        self.onlyNotExistsCondition = forceInt(record.value('onlyNotExistsCondition'))
        self.orgStructureCondition = forceInt(record.value('orgStructureCondition'))
        self.nomenclatureCondition = forceInt(record.value('nomenclatureCondition'))
        self.mesCondition = forceInt(record.value('mesCondition'))
        self.durationRange = (forceInt(record.value('minDuration')), forceInt(record.value('maxDuration')))
        self.showTime = forceBool(record.value('showTime'))
        self.showVisitTime = forceBool(record.value('showVisitTime'))
        self.isCheckedExecDateForVisit = forceBool(record.value('isCheckedExecDateForVisit'))
        self.isResolutionOfDirection = forceBool(record.value('isResolutionOfDirection'))
        self.showButtonAccount = forceBool(record.value('showButtonAccount'))
        self.showButtonTemperatureList = forceBool(record.value('showButtonTemperatureList'))
        self.showButtonNomenclatureExpense = forceBool(record.value('showButtonNomenclatureExpense'))
        self.showButtonJobTickets = forceBool(record.value('showButtonJobTickets'))
        self.counterId = forceRef(record.value('counter_id'))
        self.voucherCounterId = forceRef(record.value('voucherCounter_id'))
        self.isExternal = forceBool(record.value('isExternal'))
        self.hasAssistant = forceBool(record.value('hasAssistant'))
        self.hasCurator = forceBool(record.value('hasCurator'))
        self.hasVisitAssistant = forceBool(record.value('hasVisitAssistant'))
        self.relegationRequired = forceBool(record.value('relegationRequired'))
        self.relCounterId = forceInt(record.value('relcounter_id'))
        self.relOrgId = forceInt(record.value('relOrg_id'))
        self.aidKindCode = forceString(record.value('aidKindCode'))
        self.aidTypeId   = forceRef(record.value('aidType_id'))
        self.aidTypeCode = forceString(record.value('aidTypeCode'))
        self.aidTypeRegionalCode = forceString(record.value('aidTypeRegionalCode'))
        self.isStationary = self.aidTypeCode in ('1', '2', '3')
        self.isDayStationary = self.aidTypeCode == '7'
        self.isHealthResort = self.aidTypeCode == '8'
        self.showStatusActionsInPlanner = forceBool(record.value('showStatusActionsInPlanner'))
        self.showDiagnosticActionsInPlanner = forceBool(record.value('showDiagnosticActionsInPlanner'))
        self.showCureActionsInPlanner = forceBool(record.value('showCureActionsInPlanner'))
        self.showMiscActionsInPlanner = forceBool(record.value('showMiscActionsInPlanner'))
        self.serviceId = forceRef(record.value('service_id'))
        self.context = forceString(record.value('context'))
        self.mesRequired = forceBool(record.value('mesRequired'))
        self.mesRequiredParams = forceInt(record.value('mesRequiredParams'))
        self.csgRequired = forceBool(record.value('csgRequired'))
        self.isTakenTissue = forceBool(record.value('isTakenTissue'))
        self.csgCodeMask = forceString(record.value('csgCodeMask'))
        self.subCsgCodeMask = forceString(record.value('subCsgCodeMask'))
        self.mesCodeMask = forceString(record.value('mesCodeMask'))
        self.mesNameMask = forceString(record.value('mesNameMask'))
        self.mesServiceMask = forceString(record.value('mesServiceMask'))
        self.profileId   = forceRef(record.value('eventProfile_id'))
        self.isOrgStructurePriority = forceBool(record.value('isOrgStructurePriority'))
        self.limitActionTypes = forceBool(record.value('limitActionTypes'))
        self.includeTooth = forceBool(record.value('includeTooth'))
        self.prevEventTypeId = forceRef(record.value('prevEventType_id'))
        self.setPerson = forceInt(record.value('setPerson'))
        self.requiredCondition = forceInt(record.value('requiredCondition'))
        self.actionsControlEnabled = forceBool(record.value('actionsControlEnabled'))
        self.showActionTypesWithoutService = forceBool(record.value('showActionTypesWithoutService'))
        self.unfinishedAction = forceInt(record.value('unfinishedAction'))
        self.actionsBeyondEvent = forceInt(record.value('actionsBeyondEvent'))
        self.keepVisitParity = forceBool(record.value('keepVisitParity'))
        self.isRestrictVisitTypeAgeSex = forceBool(record.value('isRestrictVisitTypeAgeSex'))
        self.mesSpecificationId = forceRef(record.value('mesSpecification_id'))
        self.plannedInspections = None
        self.mapPlannedInspectionSpecialityIdToServiceId = {}
        self.mapPlannedSpecialityIdVisitTypeIdList = {}
        self.mapPlannedVisitTypeIdList = {}


    @classmethod
    def get(cls, eventTypeId, code = None):
        result = cls.cache.get(eventTypeId, None)
        if not result:
            cls.connect()
            result = CEventTypeDescription(eventTypeId)
            cls.cache[eventTypeId] = result
            cls.mapCodeToId[result.code] = eventTypeId
            if code is not None:
                cls.mapCodeToId[code] = eventTypeId
        return result


    @classmethod
    def getByCode(cls, eventTypeCode):
        eventTypeId = cls.mapCodeToId.get(eventTypeCode, False)
        if eventTypeId != False:
            return cls.get(eventTypeId, eventTypeCode)

        db = QtGui.qApp.db
        table = db.table('EventType')
        record = db.getRecordEx(table, [table['id']], [table['deleted'].eq(0), table['code'].eq(eventTypeCode)])
        eventTypeId = forceRef(record.value('id')) if record else None
        return cls.get(eventTypeId, eventTypeCode)


    @classmethod
    def purge(cls):
        cls.cache.clear()
        cls.mapCodeToId.clear()


    def getPlannedInspections(self):
        if self.plannedInspections is None:
            if self.eventTypeId:
                db = QtGui.qApp.db
                self.plannedInspections = db.getRecordList('EventType_Diagnostic', '*', 'eventType_id=%d'%self.eventTypeId, 'idx, id')
            else:
                self.plannedInspections = []
        return self.plannedInspections


    def getPlannedServiceIdForSpecialityId(self, specialityId):
        result = self.mapPlannedInspectionSpecialityIdToServiceId.get(specialityId, False)
        if result is False:
            result = None
            for record in self.getPlannedInspections():
                if forceRef(record.value('speciality_id')) == specialityId:
                    result = forceRef(record.value('service_id'))
                    break
            self.mapPlannedInspectionSpecialityIdToServiceId[specialityId] = result
        return result


    def getPlannedServiceIdForSpecialityIdForAge(self, specialityId, clientSex, clientAge):
        result = self.mapPlannedInspectionSpecialityIdToServiceId.get(specialityId, False)
        findSpecialityId = specialityId
        if result is False or result is None:
            result = None
            specialityId = None
            for record in self.getPlannedInspections():
                if forceRef(record.value('speciality_id')) == findSpecialityId:
                    if recordAcceptable(clientSex, clientAge, record):
                        result = forceRef(record.value('service_id'))
                        self.mapPlannedInspectionSpecialityIdToServiceId[findSpecialityId] = result
                        specialityId = findSpecialityId
                        break
        return result, specialityId


    def getPlannedVisitTypeIdListSpecialityAgeSex(self, specialityId, clientSex, clientAge):
        visitTypeIdList = []
        if specialityId:
            visitTypeIdList = self.mapPlannedSpecialityIdVisitTypeIdList.get((specialityId, clientSex, clientAge), [])
            findSpecialityId = specialityId
            if not visitTypeIdList:
                specialityId = None
                for record in self.getPlannedInspections():
                    if forceRef(record.value('speciality_id')) == findSpecialityId:
                        if recordAcceptable(clientSex, clientAge, record):
                            visitTypeId = forceRef(record.value('visitType_id'))
                            if visitTypeId and visitTypeId not in visitTypeIdList:
                                visitTypeIdList.append(visitTypeId)
                            specialityId = findSpecialityId
                self.mapPlannedSpecialityIdVisitTypeIdList[(specialityId, clientSex, clientAge)] = visitTypeIdList
        else:
            for record in self.getPlannedInspections():
                if recordAcceptable(clientSex, clientAge, record):
                    visitTypeId = forceRef(record.value('visitType_id'))
                    if visitTypeId and visitTypeId not in visitTypeIdList:
                        visitTypeIdList.append(visitTypeId)
            self.mapPlannedVisitTypeIdList[(clientSex, clientAge)] = visitTypeIdList
        return visitTypeIdList


def getEventType(eventTypeCode):
    return CEventTypeDescription.getByCode(eventTypeCode)


def getEventCode(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).code


def getEventName(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).name


def getEventIsPrimary(eventTypeId):
    curOrgStrId = QtGui.qApp.currentOrgStructureId()
    if curOrgStrId:
        table = QtGui.qApp.db.table('OrgStructure_EventType')
        record = QtGui.qApp.db.getRecordEx(table, ['isPrimary'],  [table['master_id'].eq(curOrgStrId), table['eventType_id'].eq(eventTypeId)])
        if record is not None:
            isPrimary = forceInt(record.value(0))
            if isPrimary > 0:
                return isPrimary-1
    return CEventTypeDescription.get(eventTypeId).isPrimary

def getEventOrder(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).order


def getEventAgeSelector(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).ageSelector


def getEventPurposeId(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).purposeId


def getEventPurposeCode(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).purposeCode


def isEventDeath(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).isDeath


def isEventPeriodic(eventTypeId):
    description = CEventTypeDescription.get(eventTypeId)
    return description.period or description.singleInPeriod


def isEventLong(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).isLong


def isEventTerritorialBelonging(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).isTerritorialBelonging


def isEventAutoFillingExpertise(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).isAutoFillingExpertise


def getEventPeriodEx(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).periodEx


def getEventDateInput(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).dateInput


def isEventUrgent(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).isUrgent


def getEventTypeForm(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).form


def getEventTypeRelOrg(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).relOrgId


def getEventTypeRelCounter(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).relCounterId


def getEventFinanceCode(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).financeCode


def getEventFinanceId(eventTypeId):
    description = CEventTypeDescription.get(eventTypeId)
    return description.financeId


def getEventMedicalAidKindId(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).medicalAidKindId


def getEventVisitServiceModifier(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).visitServiceModifier


def getEventVisitServiceFilter(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).visitServiceFilter


def getEventSceneId(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).sceneId


def getEventWeekProfileCode(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).weekProfileCode


def getEventVisitFinance(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).visitFinance


def getEventActionFinance(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).actionFinance


def getEventActionContract(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).actionContract


def getEventContractCondition(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).contractCondition


def getEventShowActionTypesWithoutService(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).showActionTypesWithoutService


def getEventEnableUnfinishedActions(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).unfinishedAction


def getEventEnableActionsBeyondEvent(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).actionsBeyondEvent


def getEventKeepVisitParity(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).keepVisitParity


def getEventRestrictVisitTypeAgeSex(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).isRestrictVisitTypeAgeSex


def getEventPlannerCondition(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).plannerCondition


def getEventOnlyNotExistsCondition(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).onlyNotExistsCondition


def getEventOrgStructureCondition(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).orgStructureCondition


def getEventNomenclatureCondition(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).nomenclatureCondition


def getEventMESCondition(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).mesCondition


def getEventRequiredCondition(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).requiredCondition


def getEventDurationRange(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).durationRange


def getEventShowTime(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).showTime


def getEventShowVisitTime(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).showVisitTime


def isEventCheckedExecDateForVisit(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).isCheckedExecDateForVisit


def isEventResolutionOfDirection(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).isResolutionOfDirection


def getEventShowButtonAccount(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).showButtonAccount


def getEventShowButtonTemperatureList(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).showButtonTemperatureList


def getEventShowButtonNomenclatureExpense(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).showButtonNomenclatureExpense


def getEventShowButtonJobTickets(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).showButtonJobTickets


def getEventShowActionsInPlanner(eventTypeId):
    description = CEventTypeDescription.get(eventTypeId)
    return (description.showStatusActionsInPlanner,
            description.showDiagnosticActionsInPlanner,
            description.showCureActionsInPlanner,
            description.showMiscActionsInPlanner)


def getEventCounterId(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).counterId


def getEventvoucherCounterId(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).voucherCounterId


def getEventIsExternal(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).isExternal


def hasEventAssistant(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).hasAssistant


def hasEventCurator(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).hasCurator


def getRelegationRequired(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).relegationRequired


def hasEventVisitAssistant(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).hasVisitAssistant


def getEventDurationRule(eventTypeId):
    # 0 : длительность определяется к-н
    # 1 : длительность определяется к-н+1
    return 0 if (CEventTypeDescription.get(eventTypeId).isStationary or (CEventTypeDescription.get(eventTypeId).isHealthResort and not QtGui.qApp.isDurationTakingIntoMedicalDays())) else 1


def getNextEventDate(eventTypeId, thisEventDate):
    descr = CEventTypeDescription.get(eventTypeId)
    if descr.periodEx and descr.fillNextEventDate:
        return thisEventDate.addMonths(descr.periodEx)
    else:
        return QDate()


# перенести eventTypeId вперёд.
def getEventDuration(startDate, stopDate, weekProfile, eventTypeId):
    rule = getEventDurationRule(eventTypeId)
    result = countWorkDays(startDate, stopDate, weekProfile)
    if result == 1 and rule == 0 and forceDate(startDate) == forceDate(stopDate):
        return 1
    else:
        return max(1, result+rule-1)


def getEventCanHavePayableActions(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).canHavePayableActions


def getEventAidKindCode(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).aidKindCode


def getIsDayStationary(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).isDayStationary


def getIsHealthResort(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).isHealthResort


def getEventAidTypeCode(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).aidTypeCode


def getEventAidTypeRegionalCode(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).aidTypeRegionalCode


def getEventServiceId(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).serviceId


def getEventContext(eventTypeId):
    eventDescr = CEventTypeDescription.get(eventTypeId)
    return eventDescr.context if eventDescr.context else 'f'+ eventDescr.form


def getEventMesRequired(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).mesRequired


def getEventMesRequiredParams(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).mesRequiredParams


def getEventCSGRequired(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).csgRequired


def getEventIsTakenTissue(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).isTakenTissue


def getEventCSGCodeMask(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).csgCodeMask


def getEventSubCSGCodeMask(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).subCsgCodeMask


def getEventMesCodeMask(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).mesCodeMask


def getEventMesNameMask(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).mesNameMask


def getEvenMesServiceMask(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).mesServiceMask


def getEventProfileId(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).profileId


def getEventMesSpecificationId(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).mesSpecificationId


def getEventLimitActionTypes(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).limitActionTypes


def getEventIncludeTooth(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).includeTooth


def getEventPrevEventTypeId(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).prevEventTypeId


def getEventPlannedInspections(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).getPlannedInspections()


def getEventPlannedService(eventTypeId, specialityId):
    return CEventTypeDescription.get(eventTypeId).getPlannedServiceIdForSpecialityId(specialityId)


def getEventPlannedServiceForAge(eventTypeId, specialityId, clientSex, clientAge):
    return CEventTypeDescription.get(eventTypeId).getPlannedServiceIdForSpecialityIdForAge(specialityId, clientSex, clientAge)


def getEventPlannedVisitTypeIdListAgeSex(eventTypeId, specialityId, clientSex, clientAge):
    return CEventTypeDescription.get(eventTypeId).getPlannedVisitTypeIdListSpecialityAgeSex(specialityId, clientSex, clientAge)


def getEventAddVisit(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).addVisit


def getEventSetPerson(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).setPerson


def getEventActionsControlRequired(eventTypeId):
    return CEventTypeDescription.get(eventTypeId).actionsControlEnabled


# #######################################################################

def getDeathDate(clientId):
    date = QtGui.qApp.db.translate('Client', 'id', clientId, 'deathDate')
    if date is not None:
        return forceDate(date)
    else:
        return None


def checkEventPosibilityLetal(clientId, eventTypeId, eventDate):
    db = QtGui.qApp.db
    deathDate = getDeathDate(clientId)
    if deathDate and deathDate<eventDate:
        table = db.table('EventType')
        cond=[table['id'].eq(eventTypeId), table['purpose_id'].eq(6)]
        if not db.getRecordEx(table, '*', where=cond):
            return False
    return True


def checkEventPosibility(clientId, eventTypeId, personId, eventDate):
    # Проверка возможности создания события
    if not checkEventPosibilityLetal(clientId, eventTypeId, eventDate):
        return False,  None
    description = CEventTypeDescription.get(eventTypeId)
    if description.form == '030':
        posible, eventId = checkF030EventPosibility(clientId, eventTypeId, personId, eventDate)
        if posible and (description.period or description.singleInPeriod):
            posible, eventId = checkPeriodicEventPosibility(clientId, eventTypeId, eventDate, description.period, description.singleInPeriod)
    elif description.period or description.singleInPeriod:
        posible, eventId = checkPeriodicEventPosibility(clientId, eventTypeId, eventDate, description.period, description.singleInPeriod)
    else:
        posible, eventId = checkNonPeriodicEventPosibility(clientId, eventTypeId, personId, eventDate)
    return posible, eventId


def checkF030EventPosibility(clientId, eventTypeId, personId, eventDate):
    # Проверка возможности создания события c формой 030
    db = QtGui.qApp.db
    tableEvent = db.table('Event')
    tablePerson = db.table('Person')
    tableP1 = tablePerson.alias('p1')
    tableP2 = tablePerson.alias('p2')
    table = tableEvent.leftJoin(tableP1, tableP1['id'].eq(tableEvent['execPerson_id']))
    table = table.leftJoin(tableP2, tableP1['speciality_id'].eq(tableP2['speciality_id']))
    cond = [tableEvent['deleted'].eq(0),
            tableEvent['client_id'].eq(clientId),
            tableEvent['eventType_id'].eq(eventTypeId),
            tableEvent['execDate'].isNull(),
            tableP2['id'].eq(personId),
            ]
    idList = db.getIdList(table, idCol=tableEvent['id'].name(),  where=cond, order=tableEvent['id'].name(), limit=1)
    if idList:
        return False, idList[0]
    else:
        return True, None



def checkNonPeriodicEventPosibility(clientId, eventTypeId, personId, eventDate):
    # Проверка возможности создания непериодического события
    db = QtGui.qApp.db
    table = db.table('Event')
    cond = [table['client_id'].eq(clientId),
            table['eventType_id'].eq(eventTypeId),
            table['execPerson_id'].eq(personId),
            table['execDate'].eq(eventDate),
            table['deleted'].eq(0)
            ]
    idList = db.getIdList(table, where=cond, order='id', limit=1)
    if idList:
        return False, idList[0]
    else:
        return True, None


def checkPeriodicEventPosibility(clientId, eventTypeId, eventDate, period, singleInPeriod):
    # Проверка возможности создания периодического события
    db = QtGui.qApp.db
    table = db.table('Event')
    cond = [table['client_id'].eq(clientId), table['eventType_id'].eq(eventTypeId), table['deleted'].eq(0)]
    if period != 0:
        lowDate  = eventDate.addMonths(-period)
        highDate = eventDate.addMonths(+period) # дата вперёд от eventDate для поддержки ввода задним числом
        cond.append(table['setDate'].between(lowDate,  highDate))
    if singleInPeriod:
        if singleInPeriod == 1: # раз в неделю
            lowDate  = firstWeekDay(eventDate)
            highDate = lastWeekDay(eventDate)
        elif singleInPeriod == 2: # раз в месяц
            lowDate  = firstMonthDay(eventDate)
            highDate = lastMonthDay(eventDate)
        elif singleInPeriod == 3: # раз в квартал
            lowDate  = firstQuarterDay(eventDate)
            highDate = lastQuarterDay(eventDate)
        elif singleInPeriod == 4: # раз в полгода
            lowDate  = firstHalfYearDay(eventDate)
            highDate = lastHalfYearDay(eventDate)
        elif singleInPeriod == 5: # раз в год
            lowDate  = firstYearDay(eventDate)
            highDate = lastYearDay(eventDate)
        elif singleInPeriod == 6: # раз в два год
            lowDate  = firstYearDay(eventDate).addYears(-1)
            highDate = lastYearDay(eventDate).addYears(1)
        elif singleInPeriod == 7: # раз в три год
            lowDate  = firstYearDay(eventDate).addYears(-2)
            highDate = lastYearDay(eventDate).addYears(2)
        else:
            lowDate  = eventDate
            highDate = eventDate
        cond.append(table['setDate'].between(lowDate,  highDate))
    idList = db.getIdList(table, where=cond, order='id')
    if idList:
        return False, idList[0]
    else:
        return True, None


def getEventPeriod(period, singleInPeriod):
    # вычисление периода события по интервалу и периоду однократности
    if singleInPeriod == 2:
        periodBySingle = 1
    elif singleInPeriod == 3:
        periodBySingle = 3
    elif singleInPeriod == 4:
        periodBySingle = 6
    elif singleInPeriod == 5:
        periodBySingle = 12
    elif singleInPeriod == 6:
        periodBySingle = 24
    elif singleInPeriod == 7:
        periodBySingle = 36
    else:
        periodBySingle = 0
    return max(period, periodBySingle)


def recordAcceptable(clientSex, clientAge, record, setEventDate = None, birthDate = None):
    if clientSex:
        sex = forceInt(record.value('sex'))
        if sex and sex != clientSex:
            return False
    if clientAge:
        age = forceStringEx(record.value('age'))
        controlPeriod = forceInt(record.value('controlPeriod'))
        if controlPeriod and setEventDate and birthDate:
            if controlPeriod == 2:
                setEventDate = QDate(setEventDate.year(), 1, 1)
            elif controlPeriod == 3:
                setEventDate = QDate(setEventDate.year(), 12, 31)
            clientAge = calcAgeTuple(birthDate, setEventDate)
            if not clientAge:
                clientAge = (0, 0, 0, 0)
        if age:
            ageSelector = parseAgeSelector(age)
            return checkAgeSelector(ageSelector, clientAge)
    return True


def checkDiagnosis(parentWidget, MKB, diagFilter, clientId, clientSex, clientAge, date = None):
    db = QtGui.qApp.db
    # 1) диагноз должен существовать
    tableMKB = db.table('MKB')
    if date:
        cond = [tableMKB['DiagID'].eq(MKBwithoutSubclassification(MKB)),
                      tableMKB['endDate'].isNotNull(),
                      tableMKB['endDate'].dateLt(date)
                      ]
        record  = db.getRecordEx(tableMKB, 'DiagName, endDate', cond)
        if record:
            message = u'Код %s (%s)\n в данном случае не применим.\n Дата окончания применения диагноза %s' % (MKB, forceString(record.value('DiagName')), forceString(record.value('endDate')))
            QtGui.QMessageBox.critical(parentWidget, u'Внимание!', message)
            return False
    record  = db.getRecordEx(tableMKB, 'DiagName, sex, age, MKBSubclass_id', tableMKB['DiagID'].eq(MKBwithoutSubclassification(MKB)))
    if not record:
        message = u'Кода %s не существует' % (MKB)
        QtGui.QMessageBox.critical(parentWidget, u'Внимание!', message)
        return False
    if not MKB[3:] and forceString(QtGui.qApp.getGlobalPreference('controlSubheadingMKB')) == u'нет': # не выбирать рубрику, если у неё есть подрубрики, с учётом "Даты окончания применения" этих подрубрик
        cond = [tableMKB['DiagID'].like(MKBwithoutSubclassification(MKB) + u'.%')]
        if date:
            cond.append(db.joinOr([tableMKB['endDate'].isNull(), tableMKB['endDate'].dateGt(date)]))
        if bool(db.getCount(tableMKB, tableMKB['DiagID'].name(), cond)):
            message = u'Код %s нельзя выбрать, у него есть подрубрики' % (MKB)
            QtGui.QMessageBox.critical(parentWidget, u'Внимание!', message)
            return False
    elif date:  # не выбирать подрубрику, если её рубрика имеет истёкшую "Дату окончания применения"
        cond = [tableMKB['DiagID'].eq(MKBwithoutSubclassification(MKB[:3])),
                      tableMKB['endDate'].isNotNull(),
                      tableMKB['endDate'].dateLt(date)
                    ]
        recordEndDate  = db.getRecordEx(tableMKB, 'DiagName, endDate', cond)
        if recordEndDate:
            message = u'Код %s (%s)\n в данном случае не применим.\n Рубрика %s имеет Дату окончания применения %s' % (MKB, forceString(recordEndDate.value('DiagName')), MKB[:3], forceString(recordEndDate.value('endDate')))
            QtGui.QMessageBox.critical(parentWidget, u'Внимание!', message)
            return False
    # 1.1) и субклассификация - тоже
    subclassMKB = MKB[5:]
    if subclassMKB:
        subclassId = forceInt(record.value('MKBSubclass_id'))
        tableSubclass = db.table('rbMKBSubclass_Item')
        record  = db.getRecordEx(tableSubclass, 'id', [tableSubclass['master_id'].eq(subclassId), tableSubclass['code'].eq(subclassMKB)])
        if not record:
            message = u'В коде %s указана недопустимая субклассификация' % (MKB)
            QtGui.QMessageBox.critical(parentWidget, u'Внимание!', message)
            return False
    # 2) диагноз должен быть применим по полу и возрасту
    elif not recordAcceptable(clientSex, clientAge, record):
        message = u'Код %s (%s)\n в данном случае не применим' % (MKB, forceString(record.value('DiagName')))
        QtGui.QMessageBox.critical(parentWidget, u'Внимание!', message)
        return False
    # 3) диагноз должен быть применим по специалисту
    if diagFilter and diagFilter.find(MKB[:1])>=0:
        message = u'Код %s (%s)\nпо правилам контроля не должен применяться данным специалистом\nВвод верен?' % (MKB, forceString(record.value('DiagName')))
        if QtGui.QMessageBox.Yes != QtGui.QMessageBox.question(parentWidget, u'Внимание!', message, QtGui.QMessageBox.Yes|QtGui.QMessageBox.No, QtGui.QMessageBox.Yes):
            return False
    return True


def checkSpecifyDiagnosis(parentWidget, MKB, diagFilter, clientId, clientSex, clientAge, date, mapMKBTraumaList=[]):
    def getPrefixMKB(MKB):
        lowCode = MKB
        if len(MKB) == 3:
            lowCode = MKB + '.0'
        return lowCode
    specifiedMKB = MKB
    specifiedMKBEx = ''
    specifiedCharacterId = None
    specifiedTraumaTypeId = None
    modifiableDiagnosisId = None
    specifiedDispanserId = None
    specifiedRequiresFillingDispanser = 0
    specifiedProlongMKB = False
    acceptable = checkDiagnosis(parentWidget, MKB, diagFilter, clientId, clientSex, clientAge, date)
    if acceptable and not MKB.startswith('Z'):
        db = QtGui.qApp.db
        tableMKB = db.table('MKB')
        recordFillingDispanser = db.getRecordEx(tableMKB, [tableMKB['requiresFillingDispanser']], [tableMKB['DiagID'].eq(MKB)])
        specifiedRequiresFillingDispanser = forceInt(recordFillingDispanser.value('requiresFillingDispanser')) if recordFillingDispanser else None
        table = db.table('Diagnosis')
        tableCharacter = db.table('rbDiseaseCharacter')
        queryTable = table.join(tableCharacter, tableCharacter['id'].eq(table['character_id']))
        queryTable = queryTable.join(tableMKB, 'MKB.DiagID=LEFT(Diagnosis.MKB,5)')
        cols = 'Diagnosis.id, Diagnosis.MKB, Diagnosis.MKBEx, Diagnosis.character_id, Diagnosis.traumaType_id, Diagnosis.dispanser_id, MKB.requiresFillingDispanser'
        cond = db.joinAnd([table['client_id'].eq(clientId), table['deleted'].eq(0), table['mod_id'].isNull(),
                           db.joinOr([tableCharacter['code'].ne('1'),
                                      'ADDDATE(Diagnosis.endDate, IF(MKB.duration,MKB.duration,%d))>=%s'%(QtGui.qApp.averageDuration(), db.formatDate(date))
                                     ]),
                           db.joinOr([tableMKB['endDate'].isNull(), tableMKB['endDate'].dateGe(date)])
                          ])
        record = db.getRecordEx(queryTable, cols, [cond, table['MKB'].eq(MKB)]) # точно такой
        if not record:
            record = db.getRecordEx(queryTable, cols, [cond, table['MKB'].like(MKB+'%')]) # такой, но с субклассификацией
        if not record:
            record = db.getRecordEx(queryTable, cols, [cond, table['MKB'].like(MKBwithoutSubclassification(MKB)+'%')]) # такой, без субклассификацией (другой субклассификацией)
        if not record:
            record = db.getRecordEx(queryTable, cols, [cond, table['MKB'].like(MKB[:3]+'%')]) # такой, без классификации (другой классификацией)
        if not record:# другой в этом-же блоке
            tableMKB = db.table('MKB')
            tableMKB1 = db.table('MKB').alias('MKB1')
            condExists = [tableMKB1['DiagID'].eq(MKB[:3]),
            'LEFT('+table['MKB'].name()+', 3)='+tableMKB['DiagID'].name()]
            condExists.append(db.joinOr([tableMKB['endDate'].isNull(), tableMKB['endDate'].dateGe(date)] ))
            condMKBInBlock = db.existsStmt(tableMKB.leftJoin(tableMKB1, tableMKB['BlockID'].eq(tableMKB1['BlockID'])),
                                           condExists)
            record = db.getRecordEx(queryTable, cols, [cond, condMKBInBlock]) # другой в этом-же блоке
        if record:
            specifiedMKB = forceString(record.value('MKB'))
            specifiedMKBEx = forceString(record.value('MKBEx'))
            specifiedCharacterId = forceRef(record.value('character_id'))
            specifiedTraumaTypeId = forceRef(record.value('traumaType_id'))
            specifiedDispanserId = forceRef(record.value('dispanser_id'))
            specifiedRequiresFillingDispanser = forceInt(record.value('requiresFillingDispanser'))
            specifiedProlongMKB = True
    return (acceptable, specifiedMKB, specifiedMKBEx, specifiedCharacterId, specifiedTraumaTypeId, modifiableDiagnosisId, specifiedDispanserId, specifiedRequiresFillingDispanser, specifiedProlongMKB)


def specifyDiagnosis(parentWidget, MKB, diagFilter, clientId, clientSex, clientAge, date, mapMKBTraumaList=[]):
    def  getPrefixMKB(MKB):
        lowCode = MKB
        if len(MKB) == 3:
            lowCode = MKB + '.0'
        return lowCode
    specifiedMKB = MKB
    specifiedMKBEx = ''
    specifiedCharacterId = None
    specifiedTraumaTypeId = None
    modifiableDiagnosisId = None
    specifiedDispanserId = None
    specifiedRequiresFillingDispanser = 0
    specifiedProlongMKB = False
    acceptable = checkDiagnosis(parentWidget, MKB, diagFilter, clientId, clientSex, clientAge, date)
    if acceptable and not MKB.startswith('Z'):
        # 4) диагноз должен быть подтверждён, если есть похожий
        db = QtGui.qApp.db
        tableMKB = db.table('MKB')
        recordFillingDispanser = db.getRecordEx(tableMKB, [tableMKB['requiresFillingDispanser']], [tableMKB['DiagID'].eq(MKB)])
        specifiedRequiresFillingDispanser = forceInt(recordFillingDispanser.value('requiresFillingDispanser')) if recordFillingDispanser else None
        table = db.table('Diagnosis')
        tableCharacter = db.table('rbDiseaseCharacter')
        queryTable = table.join(tableCharacter, tableCharacter['id'].eq(table['character_id']))
        queryTable = queryTable.join(tableMKB, 'MKB.DiagID=LEFT(Diagnosis.MKB,5)')
        cols = 'Diagnosis.id, Diagnosis.MKB, Diagnosis.MKBEx, Diagnosis.character_id, Diagnosis.traumaType_id, Diagnosis.dispanser_id, MKB.requiresFillingDispanser'
        cond = db.joinAnd([table['client_id'].eq(clientId), table['deleted'].eq(0), table['mod_id'].isNull(),
                           db.joinOr([tableCharacter['code'].ne('1'),
                                      'ADDDATE(Diagnosis.endDate, IF(MKB.duration,MKB.duration,%d))>=%s'%(QtGui.qApp.averageDuration(), db.formatDate(date))
                                     ]),
                           db.joinOr([tableMKB['endDate'].isNull(), tableMKB['endDate'].dateGe(date)])
                          ])
        record = db.getRecordEx(queryTable, cols, [cond, table['MKB'].eq(MKB)]) # точно такой
        if not record:
            record = db.getRecordEx(queryTable, cols, [cond, table['MKB'].like(MKB+'%')]) # такой, но с субклассификацией
        if not record:
            record = db.getRecordEx(queryTable, cols, [cond, table['MKB'].like(MKBwithoutSubclassification(MKB)+'%')]) # такой, без субклассификацией (другой субклассификацией)
        if not record:
            record = db.getRecordEx(queryTable, cols, [cond, table['MKB'].like(MKB[:3]+'%')]) # такой, без классификации (другой классификацией)
        if not record:# другой в этом-же блоке
            tableMKB = db.table('MKB')
            tableMKB1 = db.table('MKB').alias('MKB1')
            condExists = [tableMKB1['DiagID'].eq(MKB[:3]),
            'LEFT('+table['MKB'].name()+', 3)='+tableMKB['DiagID'].name()]
            condExists.append(db.joinOr([tableMKB['endDate'].isNull(), tableMKB['endDate'].dateGe(date)] ))
            condMKBInBlock = db.existsStmt(tableMKB.leftJoin(tableMKB1, tableMKB['BlockID'].eq(tableMKB1['BlockID'])),
                                           condExists)
            record = db.getRecordEx(queryTable, cols, [cond, condMKBInBlock]) # другой в этом-же блоке
        if record:
            suggestedMKB = forceString(record.value('MKB'))
            suggestedMKBEx = forceString(record.value('MKBEx'))
            suggestedCharacterId = forceRef(record.value('character_id'))
            suggestedTraumaTypeId = forceRef(record.value('traumaType_id'))
            suggestedDispanserId = forceRef(record.value('dispanser_id'))
            suggestedRequiresFillingDispanser = forceInt(record.value('requiresFillingDispanser'))
            if suggestedMKB != MKB:
                from DiagnosisConfirmationDialog import CDiagnosisConfirmationDialog
                dlg = CDiagnosisConfirmationDialog(parentWidget, suggestedMKB, MKB)
                choise = dlg.exec_()
                if choise == dlg.acceptNew:
                    lowCode = getPrefixMKB(MKB)
                    lowSuggestedCode = getPrefixMKB(suggestedMKB)
                    if (lowCode in mapMKBTraumaList) and (lowSuggestedCode in mapMKBTraumaList):
                        specifiedTraumaTypeId = suggestedTraumaTypeId
                elif choise == dlg.accentNewAndModifyOld:
                    modifiableDiagnosisId = forceRef(record.value('id'))
                    lowCode = getPrefixMKB(MKB)
                    lowSuggestedCode = getPrefixMKB(suggestedMKB)
                    if (lowCode in mapMKBTraumaList) and (lowSuggestedCode in mapMKBTraumaList):
                        specifiedTraumaTypeId = suggestedTraumaTypeId
                    specifiedDispanserId = suggestedDispanserId
                    specifiedProlongMKB = True
                else: # acceptOld or Esc
                    specifiedMKB = suggestedMKB
                    specifiedMKBEx = suggestedMKBEx
                    specifiedCharacterId = suggestedCharacterId
                    specifiedTraumaTypeId = suggestedTraumaTypeId
                    specifiedDispanserId = suggestedDispanserId
                    specifiedRequiresFillingDispanser = suggestedRequiresFillingDispanser
                    specifiedProlongMKB = True
            else:
                specifiedMKB = suggestedMKB
                specifiedMKBEx = suggestedMKBEx
                specifiedCharacterId = suggestedCharacterId
                specifiedTraumaTypeId = suggestedTraumaTypeId
                specifiedDispanserId = suggestedDispanserId
                specifiedRequiresFillingDispanser = suggestedRequiresFillingDispanser
                specifiedProlongMKB = True
    return (acceptable, specifiedMKB, specifiedMKBEx, specifiedCharacterId, specifiedTraumaTypeId, modifiableDiagnosisId, specifiedDispanserId, specifiedRequiresFillingDispanser, specifiedProlongMKB)


def getDiagnosisPrimacy(clientId, date, MKB, characterId):
    db = QtGui.qApp.db
    table = db.table('Diagnosis')
    cond  = [table['client_id'].eq(clientId), table['MKB'].eq(MKB), table['endDate'].le(date)]
    characterCode = forceString(db.translate('rbDiseaseCharacter', 'id', characterId, 'code'))
    if characterCode == '1':
        duration = forceInt(db.translate('MKB', 'DiagID', MKBwithoutSubclassification(MKB), 'duration'))
        if not duration:
            duration = QtGui.qApp.averageDuration()
        cond.append(table['endDate'].ge(date.addDays(-duration)))
    else:
        cond.append(table['endDate'].ge(firstYearDay(date)))
    record = db.getRecordEx(table, 'id', cond)
    return not record


#######################################################################
#
# второй подход к ведению ЛУД
#
#######################################################################

# считаем количество Diagnostic, Diagnosis, TempInvalid и TempInvalid_Period ссылающихся на данный diagnosis
def countUsageDiagnosis(diagnosisId, excludeDiagnosticId, countTempInvalid):
    result = 0
    if diagnosisId:
        db = QtGui.qApp.db
        table = db.table('Diagnostic')
        cond = [table['diagnosis_id'].eq(diagnosisId)]
        if excludeDiagnosticId:
            cond.append(table['id'].ne(excludeDiagnosticId))
        record = db.getRecordEx(table, 'COUNT(id)', cond)
        if record:
            result += forceInt(record.value(0))

        table = db.table('Diagnosis')
        cond = [table['mod_id'].eq(diagnosisId)]
        record = db.getRecordEx(table, 'COUNT(id)', cond)
        if record:
            result += forceInt(record.value(0))

        if countTempInvalid:
            for tableName in ('TempInvalid', 'TempInvalid_Period'):
                table = db.table(tableName)
                cond = [table['diagnosis_id'].eq(diagnosisId)]
                record = db.getRecordEx(table, 'COUNT(id)', cond)
                if record:
                    result += forceInt(record.value(0))
    return result


def createDiagnosisRecord(clientId, diagnosisTypeCode, characterCode, MKB, MKBEx, dispanserId, traumaTypeId, setDate, endDate, personId, morphologyMKB, TNMS, dispanserBegDate=None, dispanserUpdateDate=False, exSubclassMKB=None):
    # создаём новую запись Diagnosis
    db = QtGui.qApp.db
    diagnosisTypeId = db.translate('rbDiagnosisType', 'code', diagnosisTypeCode, 'id')
    characterId = db.translate('rbDiseaseCharacter', 'code', characterCode, 'id')

    table = db.table('Diagnosis')
    record = table.newRecord()
    record.setValue('client_id',        toVariant(clientId))
    record.setValue('diagnosisType_id', toVariant(diagnosisTypeId))
    record.setValue('character_id',     toVariant(characterId))
    record.setValue('MKB',              toVariant(MKB))
    record.setValue('MKBEx',            toVariant(MKBEx))
    if QtGui.qApp.isExSubclassMKBVisible():
        record.setValue('exSubclassMKB', toVariant(exSubclassMKB))
    if QtGui.qApp.isTNMSVisible():
        record.setValue('TNMS',         toVariant(TNMS))
    if QtGui.qApp.defaultMorphologyMKBIsVisible():
        record.setValue('morphologyMKB',    toVariant(morphologyMKB))
    record.setValue('dispanser_id',     toVariant(dispanserId))
    if dispanserUpdateDate:
        record.setValue('dispanserBegDate', toVariant(dispanserBegDate))
        record.setValue('dispanserPerson_id', toVariant(personId))
    record.setValue('traumaType_id',    toVariant(traumaTypeId))
    record.setValue('setDate',          toVariant(setDate))
    record.setValue('endDate',          toVariant(endDate))
    record.setValue('person_id',        toVariant(personId))
    return db.insertRecord(table, record)


def modifyDiagnosisRecord(record, diagnosisTypeCode, characterCode, MKB, MKBEx, dispanserId, traumaTypeId, setDate, endDate, personId, morphologyMKB, TNMS, dispanserBegDate=None, dispanserUpdateDate=False, exSubclassMKB=None):
    # меняем существующую запись Diagnosis, из предположения что она использована только в одном
    # месте и при этом исправляется ошибочный ввод.
    db = QtGui.qApp.db
    diagnosisTypeId = db.translate('rbDiagnosisType', 'code', diagnosisTypeCode, 'id')
    characterId = db.translate('rbDiseaseCharacter', 'code', characterCode, 'id')
    table = db.table('Diagnosis')
    record.setValue('diagnosisType_id', toVariant(diagnosisTypeId))
    record.setValue('character_id',     toVariant(characterId))
    record.setValue('MKB',              toVariant(MKB))
    record.setValue('MKBEx',            toVariant(MKBEx))
    if QtGui.qApp.isExSubclassMKBVisible():
        if exSubclassMKB is None:
            exSubclassMKB = ''
        record.setValue('exSubclassMKB', toVariant(exSubclassMKB))
    if QtGui.qApp.isTNMSVisible():
        if TNMS is None:
            TNMS = ''
        record.setValue('TNMS',         toVariant(TNMS))
    if QtGui.qApp.defaultMorphologyMKBIsVisible():
        if morphologyMKB is None:
            morphologyMKB = ''
        record.setValue('morphologyMKB',    toVariant(morphologyMKB))
    record.setValue('dispanser_id',     toVariant(dispanserId))
    if dispanserUpdateDate:
        record.setValue('dispanserBegDate', toVariant(dispanserBegDate))
        record.setValue('dispanserPerson_id', toVariant(personId))
    record.setValue('traumaType_id',    toVariant(traumaTypeId))
    record.setValue('setDate',          toVariant(setDate))
    record.setValue('endDate',          toVariant(endDate))
    record.setValue('person_id',        toVariant(personId))
    return db.updateRecord(table, record)


def updateDiagnosisRecord(record, setDate, endDate, MKBEx, dispanserId, traumaTypeId, personId, morphologyMKB, TNMS, dispanserBegDate=None, dispanserUpdateDate=False, exSubclassMKB=None):
    # меняем существующую запись Diagnosis, из предположения что она использована во многих
    # местах и при этом "расширяется"
    oldSetDate = forceDate(record.value('setDate'))
    oldEndDate = forceDate(record.value('endDate'))
    if oldEndDate<=endDate:
        record.setValue('endDate', QVariant(endDate))
        record.setValue('MKBEx', toVariant(MKBEx))
        if QtGui.qApp.isExSubclassMKBVisible():
            record.setValue('exSubclassMKB', toVariant(exSubclassMKB))
        if QtGui.qApp.isTNMSVisible() and TNMS:
            record.setValue('TNMS', toVariant(TNMS))
        if QtGui.qApp.defaultMorphologyMKBIsVisible():
            record.setValue('morphologyMKB', toVariant(morphologyMKB))
        if dispanserId:
            record.setValue('dispanser_id', toVariant(dispanserId))
        if dispanserUpdateDate and dispanserBegDate:
            record.setValue('dispanserBegDate', toVariant(dispanserBegDate))
            record.setValue('dispanserPerson_id', toVariant(personId))
        if traumaTypeId:
            record.setValue('traumaType_id',toVariant(traumaTypeId))
        if personId:
            record.setValue('person_id',toVariant(personId))

    if setDate:
        if not oldSetDate:
#            if setDate<oldEndDate:
#                record.setValue('setDate', QVariant(setDate))
            pass
        else:
            if setDate<oldSetDate:
                record.setValue('setDate', QVariant(setDate))
    QtGui.qApp.db.updateRecord('Diagnosis', record)


def findDiagnosisRecord(db, table, permanentCond, date, delta):
    tableDiagnosisType = db.table('rbDiagnosisType')
    recordDiagnosisTypeMSIId = db.getDistinctIdList(tableDiagnosisType, [tableDiagnosisType['id']], where='''TRIM(rbDiagnosisType.code) IN ('51', '52', '53', '54')''')
    # ищем в периоде
    cond1 = [permanentCond,
                                         db.joinOr([table['setDate'].isNull(), table['setDate'].le(date.addDays(delta))]),
                   table['endDate'].ge(date.addDays(-delta))]
    if recordDiagnosisTypeMSIId:
        cond1.append(table['diagnosisType_id'].notInlist(recordDiagnosisTypeMSIId))
    record = db.getRecordEx(table, '*', cond1, 'endDate DESC')
    if not record:
        # ищем после периода
        cond2 = [permanentCond, table['endDate'].le(date)]
        if recordDiagnosisTypeMSIId:
            cond2.append(table['diagnosisType_id'].notInlist(recordDiagnosisTypeMSIId))
        record = db.getRecordEx(table, '*', cond2, 'endDate DESC')
    if not record:
        # ищем до периода
        cond3 = [permanentCond]
        if recordDiagnosisTypeMSIId:
            cond3.append(table['diagnosisType_id'].notInlist(recordDiagnosisTypeMSIId))
        record = db.getRecordEx(table, '*', cond3, 'endDate DESC')
    return record


def getDiagnosisId2(
            date,
            personId,
            clientId,
            diagnosisTypeId,
            MKB,
            MKBEx,
            characterId,
            dispanserId,
            traumaTypeId,
            suggestedDiagnosisId=None,
            ownerId=None,
            isDiagnosisManualSwitch = None,
            handleDiagnosis=None,
            TNMS=None,
            morphologyMKB=None,
            dispanserBegDate=None,
            exSubclassMKB=None
            ):
    db = QtGui.qApp.db
    rbDispanserCache = CRBModelDataCache.getData('rbDispanser', True, '')
    if dispanserId:
        dispanserName = rbDispanserCache.getNameById(dispanserId) if rbDispanserCache else u''
        dispanserUpdateDate = bool(u'взят' in forceString(dispanserName).lower())
    else:
        dispanserUpdateDate = False
    if MKB.startswith('Z'):
        diagnosisTypeCode = '98' # magic!!!
    else:
        diagnosisTypeCode = forceString(db.translate('rbDiagnosisType', 'id', diagnosisTypeId, 'replaceInDiagnosis'))
    recordRDTs = db.getRecordListGroupBy('rbDiagnosisType', 'replaceInDiagnosis', where='''TRIM(replaceInDiagnosis) NOT IN ('', '98', '99') ''', group='replaceInDiagnosis', order='CAST(replaceInDiagnosis AS SIGNED)')
    replaceInDiagnosisList = []
    for recordRDT in recordRDTs:
        replaceInDiagnosisList.append(forceString(recordRDT.value('replaceInDiagnosis')))
    replaceInDiagnosisList = tuple(replaceInDiagnosisList)
    characterCode = forceString(db.translate('rbDiseaseCharacter', 'id', characterId, 'replaceInDiagnosis'))
    table = db.table('Diagnosis')
    result = None

    if diagnosisTypeCode == '98':
        result = createDiagnosisRecord(clientId, diagnosisTypeCode, characterCode, MKB, MKBEx, dispanserId, traumaTypeId, date, date, personId, morphologyMKB, TNMS, dispanserBegDate, dispanserUpdateDate, exSubclassMKB=exSubclassMKB)
    else:
        assert diagnosisTypeCode in replaceInDiagnosisList, 'diagnosisTypeCode is "%s", expected in "%s" ' % (diagnosisTypeCode, replaceInDiagnosisList)

        clientCond = table['client_id'].eq(clientId)
        diagCond = table['MKB'].eq(MKB)
        commonCond = db.joinAnd([table['deleted'].eq(0), table['mod_id'].isNull(), clientCond, diagCond])
        setDate = date

        if characterCode == '3' : # хроническое
            record = findDiagnosisRecord(db, table, commonCond, date, 0)
            docCharacterCode = forceString(db.translate('rbDiseaseCharacter', 'id', characterId, 'code'))
            if docCharacterCode in ('3', '4'): # "хроническое" или "обострение хронического"
                setDate = QDate()
            if record:
                oldCharacterId = forceRef(record.value('character_id'))
                oldCharacterCode = forceString(db.translate('rbDiseaseCharacter', 'id', oldCharacterId, 'code'))
                oldSetDate = forceDate(record.value('setDate'))
                oldEndDate = forceDate(record.value('endDate'))
#                countUsage = countUsageDiagnosis(suggestedDiagnosisId, ownerId, False)
                countUsage = countUsageDiagnosis(forceRef(record.value('id')), ownerId, False)
                if countUsage:
                    if oldCharacterCode == '3':
                        # и раньше было хроническим, обновляем документ
                        if (not oldSetDate or oldSetDate<date) and docCharacterCode == '2':
                            # при наличии уже установленного хрон. и выставлении впервые установленного
                            characterId = oldCharacterId # меняем в документе на хроническое
                    else:
                        # раньше было острым
                        if oldEndDate.year()>=date.year():
                            # меняем на хроническое
                            characterId = db.translate('rbDiseaseCharacter', 'code', characterCode, 'id')
                            record.setValue('character_id', toVariant(characterId))
                            characterId = db.translate('rbDiseaseCharacter', 'code', '4', 'id') # меняем в документе на обострение
                        else:
                            # прошлогодние данные не меняем.
                            result = createDiagnosisRecord(clientId, diagnosisTypeCode, characterCode, MKB, MKBEx, dispanserId, traumaTypeId, setDate, date, personId, morphologyMKB, TNMS, dispanserBegDate, dispanserUpdateDate, exSubclassMKB=exSubclassMKB)
                else:
                    result = modifyDiagnosisRecord(record, diagnosisTypeCode, characterCode, MKB, MKBEx, dispanserId, traumaTypeId, setDate, date, personId, morphologyMKB, TNMS, dispanserBegDate, dispanserUpdateDate, exSubclassMKB=exSubclassMKB)
            else:
                result = createDiagnosisRecord(clientId, diagnosisTypeCode, characterCode, MKB, MKBEx, dispanserId, traumaTypeId, setDate, date, personId, morphologyMKB, TNMS, dispanserBegDate, dispanserUpdateDate, exSubclassMKB=exSubclassMKB)
        else: # это острое заболевание
            if isDiagnosisManualSwitch:
                return getDiagnosisIdByManualSwitch(
                       handleDiagnosis,
                       date,
                       personId,
                       clientId,
                       diagnosisTypeId,
                       MKB,
                       MKBEx,
                       characterId,
                       dispanserId,
                       traumaTypeId,
                       suggestedDiagnosisId,
                       ownerId,
                       morphologyMKB,
                       TNMS,
                       dispanserBegDate,
                       dispanserUpdateDate,
                       exSubclassMKB)
            duration = forceInt(db.translate('MKB', 'DiagID', MKBwithoutSubclassification(MKB), 'duration'))
            if not duration:
                duration = QtGui.qApp.averageDuration()
            record = findDiagnosisRecord(db, table, commonCond, date, duration)
            if record:
                oldCharacterId = forceRef(record.value('character_id'))
                oldCharacterCode = forceString(db.translate('rbDiseaseCharacter', 'id', oldCharacterId, 'code'))
#                countUsage = countUsageDiagnosis(suggestedDiagnosisId, ownerId, False)
                countUsage = countUsageDiagnosis(forceRef(record.value('id')), ownerId, False)
                if countUsage:
                    if oldCharacterCode == '3':
                        # раньше было хроническим, обновляем в документе на обострение
                        characterId = db.translate('rbDiseaseCharacter', 'code', '4', 'id') # меняем в документе на обострение
                        updateDiagnosisRecord(record, date, date, MKBEx, dispanserId, traumaTypeId, personId, morphologyMKB, TNMS, dispanserBegDate, dispanserUpdateDate, exSubclassMKB=exSubclassMKB)
                    else:
                        oldSetDate = forceDate(record.value('setDate'))
                        oldEndDate = forceDate(record.value('endDate'))
                        if oldSetDate.addDays(-duration)>date or date>oldEndDate.addDays(duration):
                            result = createDiagnosisRecord(clientId, diagnosisTypeCode, characterCode, MKB, MKBEx, dispanserId, traumaTypeId, date, date, personId, morphologyMKB, TNMS, dispanserBegDate, dispanserUpdateDate, exSubclassMKB=exSubclassMKB)
                else:
                    result = modifyDiagnosisRecord(record, diagnosisTypeCode, characterCode, MKB, MKBEx, dispanserId, traumaTypeId, setDate, date, personId, morphologyMKB, TNMS, dispanserBegDate, dispanserUpdateDate, exSubclassMKB=exSubclassMKB)
            else:
                result = createDiagnosisRecord(clientId, diagnosisTypeCode, characterCode, MKB, MKBEx, dispanserId, traumaTypeId, date, date, personId, morphologyMKB, TNMS, dispanserBegDate, dispanserUpdateDate, exSubclassMKB=exSubclassMKB)
        if result is None:
            if diagnosisTypeCode == '2':
                diagnosisTypeId = db.translate('rbDiagnosisType', 'code', diagnosisTypeCode, 'id')
                record.setValue('diagnosisType_id', diagnosisTypeId)
            updateDiagnosisRecord(record, setDate, date, MKBEx, dispanserId, traumaTypeId, personId, morphologyMKB, TNMS, dispanserBegDate, dispanserUpdateDate, exSubclassMKB=exSubclassMKB)
            result = forceRef(record.value('id'))
    if suggestedDiagnosisId and suggestedDiagnosisId != result:
        if countUsageDiagnosis(suggestedDiagnosisId, ownerId, True) == 0:
            db.deleteRecord(table, table['id'].eq(suggestedDiagnosisId))
    return result, characterId


def getDiagnosisIdByManualSwitch(
            handleDiagnosis,
            date,
            personId,
            clientId,
            diagnosisTypeId,
            MKB,
            MKBEx,
            characterId,
            dispanserId,
            traumaTypeId,
            suggestedDiagnosisId=None,
            ownerId=None,
            morphologyMKB=None,
            TNMS=None,
            dispanserBegDate=None,
            dispanserUpdateDate=False,
            exSubclassMKB=None
            ):
    db = QtGui.qApp.db
    if MKB.startswith('Z'):
        diagnosisTypeCode = '98' # magic from getDiagnosisId2 :-)
    else:
        diagnosisTypeCode = forceString(db.translate('rbDiagnosisType', 'id', diagnosisTypeId, 'replaceInDiagnosis'))
    characterCode = forceString(db.translate('rbDiseaseCharacter', 'id', characterId, 'replaceInDiagnosis'))
    tableDiagnosis = db.table('Diagnosis')
    if characterCode == '3': # хроническое
        return getDiagnosisId2(
                    date,
                    personId,
                    clientId,
                    diagnosisTypeId,
                    MKB,
                    MKBEx,
                    characterId,
                    dispanserId,
                    traumaTypeId,
                    suggestedDiagnosisId,
                    ownerId,
                    TNMS=TNMS,
                    morphologyMKB=morphologyMKB,
                    dispanserBegDate=dispanserBegDate,
                    exSubclassMKB=exSubclassMKB)
    result = None
    clientCond = tableDiagnosis['client_id'].eq(clientId)
    diagCond = tableDiagnosis['MKB'].eq(MKB)
    commonCond = db.joinAnd([tableDiagnosis['deleted'].eq(0),
                             tableDiagnosis['mod_id'].isNull(), clientCond, diagCond])
    if handleDiagnosis:
        if not bool(ownerId):
            result = createDiagnosisRecord(clientId, diagnosisTypeCode, characterCode, MKB, MKBEx, dispanserId, traumaTypeId, date, date, personId, morphologyMKB, TNMS, dispanserBegDate, dispanserUpdateDate, exSubclassMKB=exSubclassMKB)
        else:
            wasCheckedHandleDiagnosis = checkIsHandleDiagnosisIsChecked(date,
                                                                        clientId,
                                                                        suggestedDiagnosisId)
            if wasCheckedHandleDiagnosis:
                diagnosisId = forceRef(db.translate('Diagnostic', 'id', ownerId, 'diagnosis_id'))
                checkRecord = db.getRecord(tableDiagnosis, '*', diagnosisId)
                if bool(checkRecord):
                    modifySetDate = forceDate(checkRecord.value('setDate'))
                    modifyEndDate = forceDate(checkRecord.value('endDate'))
                    result = modifyDiagnosisRecord(checkRecord, diagnosisTypeCode, characterCode, MKB, MKBEx, dispanserId, traumaTypeId, modifySetDate, modifyEndDate, personId, morphologyMKB, TNMS, dispanserBegDate, dispanserUpdateDate, exSubclassMKB=exSubclassMKB)
                else:
                    result = createDiagnosisRecord(clientId, diagnosisTypeCode, characterCode, MKB, MKBEx, dispanserId, traumaTypeId, date, date, personId, morphologyMKB, TNMS, dispanserBegDate, dispanserUpdateDate, exSubclassMKB=exSubclassMKB)
            else:
                result = createDiagnosisRecord(clientId, diagnosisTypeCode, characterCode, MKB, MKBEx, dispanserId, traumaTypeId, date, date, personId, morphologyMKB, TNMS, dispanserBegDate, dispanserUpdateDate, exSubclassMKB=exSubclassMKB)
    else:
        duration = forceInt(db.translate('MKB', 'DiagID', MKBwithoutSubclassification(MKB), 'duration'))
        if not duration:
            duration = QtGui.qApp.averageDuration()
        record = findDiagnosisRecord(db, tableDiagnosis, commonCond, date, duration)
        if record:
            oldCharacterId = forceRef(record.value('character_id'))
            oldCharacterCode = forceString(db.translate('rbDiseaseCharacter', 'id', oldCharacterId, 'code'))
            countUsage = countUsageDiagnosis(forceRef(record.value('id')), ownerId, False)
            if countUsage:
                if oldCharacterCode == '3':
                    characterId = db.translate('rbDiseaseCharacter', 'code', '4', 'id')
                oldSetDate = forceDate(record.value('setDate'))
                oldEndDate = forceDate(record.value('endDate'))
                if oldSetDate.addDays(-duration*2)>date or date>oldEndDate.addDays(duration*2):
                    if CAskedValueForDiagnosisManualSwitch.ask():
                        updateDiagnosisRecord(record, date, date, MKBEx, dispanserId, traumaTypeId, personId, morphologyMKB, TNMS, dispanserBegDate, dispanserUpdateDate, exSubclassMKB=exSubclassMKB)
                        result = forceRef(record.value('id'))
                    else:
                        result = createDiagnosisRecord(clientId, diagnosisTypeCode, characterCode, MKB, MKBEx, dispanserId, traumaTypeId, date, date, personId, morphologyMKB, TNMS, dispanserBegDate, dispanserUpdateDate, exSubclassMKB=exSubclassMKB)
                else:
                    updateDiagnosisRecord(record, date, date, MKBEx, dispanserId, traumaTypeId, personId, morphologyMKB, TNMS, dispanserBegDate, dispanserUpdateDate, exSubclassMKB=exSubclassMKB)
                    result = forceRef(record.value('id'))
            else:
                result = createDiagnosisRecord(clientId, diagnosisTypeCode, characterCode, MKB, MKBEx, dispanserId, traumaTypeId, date, date, personId, morphologyMKB, TNMS, dispanserBegDate, dispanserUpdateDate, exSubclassMKB=exSubclassMKB)
        else:
            result = createDiagnosisRecord(clientId, diagnosisTypeCode, characterCode, MKB, MKBEx, dispanserId, traumaTypeId, date, date, personId, morphologyMKB, TNMS, dispanserBegDate, dispanserUpdateDate, exSubclassMKB=exSubclassMKB)
    if suggestedDiagnosisId and suggestedDiagnosisId != result:
        if countUsageDiagnosis(suggestedDiagnosisId, ownerId, True) == 0:
            db.deleteRecord(tableDiagnosis, tableDiagnosis['id'].eq(suggestedDiagnosisId))
    return result, characterId


def checkIsHandleDiagnosisIsChecked(setDate, clientId, diagnosisId):
    if bool(diagnosisId):
        db = QtGui.qApp.db
        tableDiagnosis = db.table('Diagnosis')
        cond = [tableDiagnosis['setDate'].dateEq(setDate),
                tableDiagnosis['client_id'].eq(clientId),
                tableDiagnosis['id'].eq(diagnosisId)]
        recordCheck = db.getRecordEx(tableDiagnosis, 'id', cond)
        return int(bool(recordCheck))
    return 0

def setAskedClassValueForDiagnosisManualSwitch(val):
    CAskedValueForDiagnosisManualSwitch.setValue(val)

class CAskedValueForDiagnosisManualSwitch(object):
    # не забыть после всего установить
    # `value` в значение None

    u'''0 - `да` только для текущего
        1 - `нет` только для текущего
        2 - `да` для всех
        3 - `нет` для всех'''

    value = None
    messageBox = None
    buttons = []

    @classmethod
    def setValue(cls, value):
        cls.value = value

    @classmethod
    def ask(cls):
        val = cls.value
        if val in (None, 0, 1):# еще не было вопроса, либо ответ не распространялся на все
            messageBox = cls.getMessageBox()
            messageBox.exec_()
            button = messageBox.clickedButton()
            if button in cls.buttons:
                cls.setValue(cls.buttons.index(button))
                return cls.getResult()
        else:
            return cls.getResult()

    @classmethod
    def getResult(cls):
        if cls.value in (0, 2):
            return True
#        elif cls.value in (1, 3):
#            return False
        return False


    @classmethod
    def getMessageBox(cls):
        if not cls.messageBox:
            buttonYes = QtGui.QPushButton(u'да')
            buttonNo = QtGui.QPushButton(u'нет')
            buttonYesForAll = QtGui.QPushButton(u'да для всех')
            buttonNoForAll = QtGui.QPushButton(u'нет для всех')
            cls.buttons = [buttonYes, buttonNo, buttonYesForAll, buttonNoForAll]
            messageBox = QtGui.QMessageBox()
            messageBox.setWindowFlags(messageBox.windowFlags() | Qt.WindowStaysOnTopHint)
            messageBox.setWindowTitle(u'Внимание!')
            messageBox.setText(u'Слишком большой временной промежуток между датами \nв однотипных заболеваниях\n\nСчитать одним заболеванием?')
            messageBox.addButton(buttonYes,       QtGui.QMessageBox.ActionRole)
            messageBox.addButton(buttonNo,        QtGui.QMessageBox.ActionRole)
            messageBox.addButton(buttonYesForAll, QtGui.QMessageBox.ActionRole)
            messageBox.addButton(buttonNoForAll,  QtGui.QMessageBox.ActionRole)
            cls.messageBox = messageBox
        return cls.messageBox

#######################################################################

def getEventDiagnosis(eventId):
    stmt = 'SELECT MKB from Diagnosis WHERE id=getEventDiagnosis(%d) LIMIT 1' % eventId
    query = QtGui.qApp.db.query(stmt)
    if query.first():
        return forceString(query.record().value(0))
    else:
        return None


def getEventDiseasePhases(eventId):
    stmt = 'SELECT getEventDiseasePhasesDiagnostic(%d)' % eventId
    query = QtGui.qApp.db.query(stmt)
    if query.first():
        return forceRef(query.record().value(0))
    else:
        return None

#######################################################################

MapMKBCharactersToCharacterID = None


def getMapMKBCharactersToCharacterID():
    u'''
        получить список id записей характеров в соответствии с
        характером указанным в МКБ
    '''
    global MapMKBCharactersToCharacterID
    from RefBooks.MKB.List import MapMKBCharactersToCharacterCode

    if not MapMKBCharactersToCharacterID:
        db = QtGui.qApp.db
        mapCodeToId = {}
        for record in db.getRecordList('rbDiseaseCharacter', 'id, code'):
            id   = forceRef(record.value(0))
            code = forceString(record.value(1))
            mapCodeToId[code] = id
        result = []
        for (title,  codes) in MapMKBCharactersToCharacterCode:
            idList = []
            for code in codes:
                idList.append(mapCodeToId[code])
            result.append(idList)
        MapMKBCharactersToCharacterID = result
    return MapMKBCharactersToCharacterID


def getAvailableCharacterIdByMKB(MKB):
    u'''
        получить список id записей характеров в соответствии с кодом МКБ
    '''
# in RefBooks/MKB.py:
#MKBCharacters = [   u'нет',                             #0
#                    u'острое',                          #1
#                    u'хроническое впервые выявленное',  #2
#                    u'хроническое ранее известное',     #3
#                    u'обострение хронического',         #4
#                    u'хроническое',                     #5
#                    u'хроническое или острое',          #6
#                ]
    fixedMKB = MKBwithoutSubclassification(MKB)
    MKBCharacters = forceInt(QtGui.qApp.db.translate('MKB', 'DiagID', fixedMKB, 'characters'))
    return getMapMKBCharactersToCharacterID()[MKBCharacters]


def getExactServiceId(diagnosisServiceId, eventServiceId, personServiceId, eventTypeId, visitTypeId, sceneId, specialityId, clientSex=0, clientAge=[]):
    u'получить id услуги с учётом дополнительных факторов'
    db = QtGui.qApp.db
    if clientAge:
        plannedServiceId, specialityId = getEventPlannedServiceForAge(eventTypeId, specialityId, clientSex, clientAge)
    else:
        plannedServiceId = getEventPlannedService(eventTypeId, specialityId)
    baseServiceId = diagnosisServiceId or eventServiceId or plannedServiceId or personServiceId
    baseServiceCode = forceString(db.translate('rbService', 'id', baseServiceId, 'code'))
    serviceCode = baseServiceCode
    serviceModifier = parseModifier(getEventVisitServiceModifier(eventTypeId))
    serviceCode = applyModifier(serviceCode, serviceModifier)
    serviceModifier = parseModifier(db.translate('rbVisitType', 'id', visitTypeId, 'serviceModifier'))
    serviceCode = applyModifier(serviceCode, serviceModifier)
    serviceModifier = parseModifier(db.translate('rbScene',     'id', sceneId,     'serviceModifier'))
    serviceCode = applyModifier(serviceCode, serviceModifier)
    if serviceCode == baseServiceCode:
        return baseServiceId
    elif serviceCode:
        return forceRef(db.translate('rbService', 'code', serviceCode, 'id'))
    else:
        return None


def getExactVisitTypeIdList(eventTypeId, specialityId, clientSex, clientAge):
    return getEventPlannedVisitTypeIdListAgeSex(eventTypeId, specialityId, clientSex, clientAge)


def createVisits(eventId, eventTypeId=None, clientSex=0, clientAge=[]):
    db = QtGui.qApp.db
    sceneId = forceRef(db.translate('rbScene', 'code',  '1', 'id'))
    if not eventTypeId:
        eventTypeId = forceRef(db.translate('Event', 'id',  eventId, 'eventType_id'))
    eventServiceId = getEventServiceId(eventTypeId)
    tableDiagnostic = db.table('Diagnostic')
    tableVisit      = db.table('Visit')
    tableEventTypeDiagnostic = db.table('EventType_Diagnostic')
    diagnosisTypes  = db.getIdList('rbDiagnosisType', where='code in (1, 2)') # magic
    diagnostics     = db.getRecordList(tableDiagnostic, '*', where=tableDiagnostic['event_id'].eq(eventId))
    db.deleteRecord(tableVisit, where=tableVisit['event_id'].eq(eventId))
    if sceneId and eventTypeId:
        for diagnostic in diagnostics:
            diagnosisTypeId = forceRef(diagnostic.value('diagnosisType_id'))
            if diagnosisTypeId in  diagnosisTypes:
                setDate = forceDate(diagnostic.value('setDate'))
                endDate = forceDate(diagnostic.value('endDate'))
                specialityId = forceRef(diagnostic.value('speciality_id'))
                personId     = forceRef(diagnostic.value('person_id'))
                financeId    = forceRef(db.translate('Person', 'id', personId, 'finance_id'))
                serviceId    = forceRef(db.translate('rbSpeciality', 'id', specialityId, 'service_id'))
                serviceId    = forceRef(db.translate('rbSpeciality', 'id', specialityId, 'service_id'))
#                visitTypeId  = forceRef(diagnostic.value('visitType_id'))
                visitTypeCond = [tableEventTypeDiagnostic['eventType_id'].eq(eventTypeId),
                                 tableEventTypeDiagnostic['speciality_id'].eq(specialityId)]
                visitTypeIdList  = db.getIdList(tableEventTypeDiagnostic, 'visitType_id', where=visitTypeCond)
                if visitTypeIdList:
                    visitTypeId = visitTypeIdList[0]
                else:
                    visitTypeId = None
                serviceId    = getExactServiceId(None, eventServiceId, serviceId, eventTypeId, visitTypeId, sceneId, specialityId, clientSex, clientAge)
                if endDate and (not setDate or setDate<=endDate) \
                   and personId     \
                   and financeId    \
                   and serviceId    \
                   and visitTypeId:
                    record = tableVisit.newRecord()
                    record.setValue('event_id',     toVariant(eventId))
                    record.setValue('scene_id',     toVariant(sceneId))
                    record.setValue('date',         toVariant(endDate))
                    record.setValue('visitType_id', toVariant(visitTypeId))
                    record.setValue('person_id',    toVariant(personId))
                    record.setValue('isPrimary',    toVariant(1))
                    record.setValue('finance_id',   toVariant(financeId))
                    record.setValue('service_id',   toVariant(serviceId))
                    record.setValue('payStatus',    toVariant(0))
                    db.insertRecord(tableVisit, record)


#
# ################################################################################
#

class CPayStatus:
    initial    = 0 # ни выставления, ни оплаты, ни отказа
    exposed    = 1 # выставлено, но не оплачено и не отказано
    refused    = 2 # отказано
    payed      = 3 # оплачено

    names      = (u'-', u'выставлено', u'отказано', u'оплачено')

    exposedBits = 0x55555555
    refusedBits = 0xAAAAAAAA
    payedBits   = 0xFFFFFFFF


def getPayStatusValueByCode(status, financeCode):
    return status << (2*financeCode)


def getPayStatusMaskByCode(financeCode):
    return 3 << (2*financeCode)


def extractLonePayStaus(payStatus, financeCode):
    return  (payStatus >> (2*financeCode)) & 3


def getPayStatusMask(financeId):
    code = CFinanceType.getCode(financeId)
    return 3 << (2*code)


def getExposed(payStatusMask):
    return CPayStatus.exposedBits & payStatusMask


def getRefused(payStatusMask):
    return CPayStatus.refusedBits & payStatusMask


def getPayed(payStatusMask):
    return payStatusMask


def getWorstPayStatus(payStatus):
    statusSet = set([CPayStatus.initial])
    while payStatus>0:
        status = payStatus & 0x3
        statusSet.add(status)
        payStatus = payStatus >> 2
    for status in (CPayStatus.exposed, CPayStatus.payed, CPayStatus.refused, CPayStatus.initial):
        if status in statusSet:
            return status


def payStatusText(payStatus):
    resultList = []
    for code in CFinanceType.allCodes:
        status = extractLonePayStaus(payStatus, code)
        if status:
            name = forceString(CFinanceType.getNameByCode(code))
            resultList.append( name + ': ' + CPayStatus.names[status] )
    return ', '.join(resultList)


def getRealPayed(payStatus):
    for code in CFinanceType.allCodes:
        status = extractLonePayStaus(payStatus, code)
        if status == CPayStatus.payed:
            return True
    return False

#
# #####################################
#

def getActionTypeIdListByClass(actionTypeClass):
    db = QtGui.qApp.db
    tableActionType = db.table('ActionType')
    cond = [tableActionType['deleted'].eq(0),
            tableActionType['class'].eq(actionTypeClass),
           ]
    return db.getIdList(tableActionType, 'id', cond)


def getActionTypeIdListByFlatCode(flatCode):
    if not isinstance(flatCode, list):
        flatCode = [flatCode]
    db = QtGui.qApp.db
    tableActionType = db.table('ActionType')
    cond =[tableActionType['deleted'].eq(0),
           db.joinOr([tableActionType['flatCode'].like(flatCodeItem) for flatCodeItem in flatCode]),
          ]
    return db.getDistinctIdList(tableActionType, 'id', cond)


def getActionTypeDescendants(actionTypeId, class_=None):
    db = QtGui.qApp.db
    tableActionType = db.table('ActionType')

    result = set([actionTypeId])
    parents = [actionTypeId]

    if actionTypeId and class_ is None:
        class_ = db.translate(tableActionType, 'id', actionTypeId, 'class')
    if class_:
        classCond = tableActionType['class'].eq(class_)
    else:
        classCond = None
    while parents:
        cond = tableActionType['group_id'].inlist(parents)
        if classCond:
          cond = [cond, classCond]
        children = set(db.getIdList(tableActionType, where=cond))
        newChildren = children-result
        result |= newChildren
        parents = newChildren
    return list(result)

#
# #######################################
#


def getClosingMKBValueForAction(diagnosticsRecordList, diagnosisTypeIdList):
    for diagnosisTypeId in diagnosisTypeIdList:
        for record in diagnosticsRecordList:
            if forceRef(record.value('diagnosisType_id')) == diagnosisTypeId:
                MKB = forceString(record.value('MKB'))
                morphologyMKB = forceString(record.value('morphologyMKB'))
                return MKB, morphologyMKB
    return '', ''


def getMKBValueBySetPerson(diagnosticsRecordList, setPersonId, diagnosisTypeIdList, eventPersonId):
    for diagnosisTypeId in diagnosisTypeIdList:
        for record in diagnosticsRecordList:
            if not record.value('person_id').isNull():
                diagnosticsPersonId = forceRef(record.value('person_id'))
                if diagnosticsPersonId == setPersonId:
                    if forceRef(record.value('diagnosisType_id')) == diagnosisTypeId:
                        MKB = forceString(record.value('MKB'))
                        morphologyMKB = forceString(record.value('morphologyMKB'))
                        return MKB, morphologyMKB
    for diagnosisTypeId in diagnosisTypeIdList:
        for record in diagnosticsRecordList:
            if eventPersonId == setPersonId:
                if forceRef(record.value('diagnosisType_id')) == diagnosisTypeId:
                    MKB = forceString(record.value('MKB'))
                    morphologyMKB = forceString(record.value('morphologyMKB'))
                    return MKB, morphologyMKB
    return '', ''


#
# #######################################
#



class CTableSummaryActionsMenuMixin():
    u'''
    Реализация контекстного меню
    таблицы "Мероприятия" вкладки
    "Стат.учет" форм ввода (ф.000,ф.003,ф.025,ф.030)
    '''
    def __init__(self, tabsTableList=None):
        if tabsTableList:
            self.tabsTableList = tabsTableList
        else:
            self.tabsTableList = [self.tabStatus.tblAPActions, self.tabDiagnostic.tblAPActions, self.tabCure.tblAPActions, self.tabMisc.tblAPActions]
        self.setupActionsMenu()
        self.tblActions.setPopupMenu(self.mnuAction)
        self.addObject('qshcActionsEdit', QtGui.QShortcut('F4', self.tblActions, self.on_actActionEdit_triggered))
        self.qshcActionsEdit.setContext(Qt.WidgetShortcut)
        QObject.connect(self.actActionEdit, SIGNAL('triggered()'), self.on_actActionEdit_triggered)

        self.addObject('qshcAPActionAddSuchAs', QtGui.QShortcut('F2', self.tblActions, self.on_actAPActionAddSuchAs_triggered))
        self.qshcAPActionAddSuchAs.setContext(Qt.WidgetShortcut)
        QObject.connect(self.actActionAddSuchAs, SIGNAL('triggered()'), self.on_actAPActionAddSuchAs_triggered)

        QObject.connect(self.actDeleteRow, SIGNAL('triggered()'), self.on_actDeleteRow_triggered)
        QObject.connect(self.actUnBindAction, SIGNAL('triggered()'), self.on_actUnBindAction_triggered)
        QObject.connect(self.tblActions.popupMenu(), SIGNAL('aboutToShow()'), self.onAboutToShow)


    def setupActionsMenu(self):
        self.addObject('mnuAction', QtGui.QMenu(self))

        self.addObject('actActionEdit', QtGui.QAction(u'Перейти к редактированию', self))
        self.actActionEdit.setShortcut(Qt.Key_F4)
        self.mnuAction.addAction(self.actActionEdit)

        self.addObject('actActionAddSuchAs', QtGui.QAction(u'Добавить такой же', self))
        self.actActionAddSuchAs.setShortcut(Qt.Key_F2)
        self.mnuAction.addAction(self.actActionAddSuchAs)

        self.addObject('actUnBindAction', QtGui.QAction(u'Открепить мероприятие', self))
        self.mnuAction.addAction(self.actUnBindAction)

        self.addObject('actDeleteRow', QtGui.QAction(u'Удалить запись', self))
        self.mnuAction.addAction(self.actDeleteRow)


    def getPageAndRow(self):
        index = self.tblActions.currentIndex()
        row = index.row()
        if 0 <= row < len(self.modelActionsSummary.itemIndex):
            return self.modelActionsSummary.itemIndex[row]
        else:
            return None, None
    
    
    def canUnbindRow(self, rows):
        from Events.Action import CActionTypeCache
        tabs = {
            0: self.tabStatus,
            1: self.tabDiagnostic,
            2: self.tabCure,
            3: self.tabMisc
        }
        
        def afterReturnCond(actions):
            db = QtGui.qApp.db
            tableAccountItem = db.table('Account_Item')
            prevEventId = self.getEventId()
            actionIds = []
            for record, action in actions:
                actionIds.append(record.value('id'))
            query = db.query('SELECT {}'.format(db.existsStmt(tableAccountItem, [
                tableAccountItem['event_id'].eq(prevEventId), 
                tableAccountItem['refuseType_id'].isNotNull()
                ])))
            if query.next():
                record = query.record()
                query = db.query('SELECT {}'.format(db.existsStmt(tableAccountItem, tableAccountItem['action_id'].inlist(actionIds))))
                if forceInt(record.value(0)) and query.next():
                    record = query.record()
                    if not forceBool(record.value(0)):
                        return False
                    else:
                        return True
            return False
            
        if QtGui.qApp.userHasRight(urAdmin):
            return True
        if self.isReadOnly():
            return False
        relatedRows = []
        for row in rows:
            if 0 <= row < len(self.modelActionsSummary.itemIndex):
                page, row = self.modelActionsSummary.itemIndex[row]
                tbl = self.tabsTableList[page]
                row = tbl.model()._mapModelRow2ProxyRow[row]
                items = tbl.model()._items
                group = items._mapProxyRow2Group[row]
                if group.firstItem.action.getMasterId():
                    for itemClass in list(tabs.values()):
                        if group.firstItem.action.getType().class_ == itemClass:
                            continue
                        for item in itemClass.modelAPActions._groups.groupsIterator:
                            if item.firstItem.id == group.firstItem.action.getMasterId():
                                row = item._mapItem2Row[item.firstItem]
                                page, row = self.modelActionsSummary.itemIndex[row]
                                tbl = self.tabsTableList[page]
                                row = tbl.model()._mapModelRow2ProxyRow[row]
                                items = tbl.model()._items
                                group = items._mapProxyRow2Group[row]
                                break
                if row < len(items):
                    record, action = items[row]
                else:
                    if not group.expanded and isinstance(group, CRelationsProxyModelGroup):
                        tbl.model().touchGrouping(row)
                    record, action = group.getItem(row)
                relatedRows.append((record, action))
                if isinstance(group, CRelationsProxyModelGroup):
                    parentActionType = group.firstItem.action.getType()
                    relatedActionTypes = CActionTypeCache.getById(parentActionType.id).getRelatedActionTypes()
                    required = []
                    for item in relatedActionTypes:
                        relatedActionType = CActionTypeCache.getById(item)
                        if parentActionType.class_ != relatedActionType.class_:
                            required.append(relatedActionType.class_)     
                    required = set(required)
                    for proxyRow in reversed(sorted(group.proxyRows)):
                        record, action = group.getItem(proxyRow)
                        relatedRows.append((record, action))
                    for itemClass in required:
                        for item in tabs[itemClass].modelAPActions._groups.groupsIterator:
                            if item.firstItem.action.getMasterId() == group.firstItem.id:
                                record, action = item.firstItem
                                relatedRows.append((record, action))
        relatedRows = list(set(relatedRows))
        if QtGui.qApp.userHasRight(urEditClosedEvent) or (QtGui.qApp.userHasRight(urEditAfterReturnEvent) and afterReturnCond(relatedRows)):
            if QtGui.qApp.userHasRight(urEditOtherpeopleAction):
                return True
            elif QtGui.qApp.userHasRight(urEditOtherPeopleActionSpecialityOnly):
                for record, action in relatedRows:
                    if not (forceInt(record.value('person_id')) and QtGui.qApp.userSpecialityId == action.getSpecialityId(forceInt(record.value('person_id')))):
                        return False
                return True
            elif QtGui.qApp.userHasRight(urEditSubservientPeopleAction):
                for record, action in relatedRows:
                    if not (forceInt(record.value('person_id')) and QtGui.qApp.userId in getPersonOrgStructureChiefs(forceInt(record.value('person_id')))):
                        return False
                return True
        return False


    def onAboutToShow(self):
        row = self.tblActions.currentIndex().row()
        rows = self.tblActions.getSelectedRows()

        canDeleteRow = not any(map(self.modelActionsSummary.isLockedOrExposed, rows)) and all(map(self.modelActionsSummary.isCanDeletedByUser, rows)) if rows else False
        if len(rows) == 1 and rows[0] == row:
            self.actDeleteRow.setText(u'Удалить текущую строку')
            self.actUnBindAction.setText(u'Открепить текущее мероприятие')
        elif len(rows) == 1:
            self.actDeleteRow.setText(u'Удалить выделенную строку')
            self.actUnBindAction.setText(u'Открепить выделенное мероприятие')
        else:
            self.actDeleteRow.setText(u'Удалить выделенные строки')
            self.actUnBindAction.setText(u'Открепить выделенные мероприятия')
        self.actUnBindAction.setEnabled(self.canUnbindRow(rows))
        self.actDeleteRow.setEnabled(canDeleteRow)


#    @pyqtSignature('')
    def on_actActionEdit_triggered(self):
        page, row = self.getPageAndRow()
        optionalTabs = 0
        if row is not None:
            if hasattr(self, 'tabMedicalDiagnosis'):
                optionalTabs += 1
            if hasattr(self, 'tabMes'):
                optionalTabs += 1
            tabIndex = page+1+optionalTabs
            self.tabWidget.setCurrentIndex(tabIndex)
            tbl = self.tabsTableList[page]
            tbl.setCurrentIndex(tbl.model().index(row, 0))


#    @pyqtSignature('')
    def on_actAPActionAddSuchAs_triggered(self):
        index = self.tblActions.currentIndex()
        rowSummary = index.row()
        columnSummary = index.column()
        if 0 <= rowSummary < len(self.modelActionsSummary.itemIndex):
            page, row = self.modelActionsSummary.itemIndex[rowSummary]
            tbl = self.tabsTableList[page]
            model = tbl.model()
            if 0<=row<model.rowCount()-1:
                record = model._items[row][0]
                actionTypeId = forceRef(record.value('actionType_id'))
                index = model.index(model.rowCount()-1, 0)
                if model.setData(index, toVariant(actionTypeId)):
                    newRowSummary = len(model.items())-row+rowSummary-1
                    indexSummary = self.tblActions.model().index(newRowSummary, columnSummary)
                    self.tblActions.setCurrentIndex(indexSummary)


#    @pyqtSignature('')
    def on_actDeleteRow_triggered(self):
        rowsSortByPagesTables = {}
        rows = self.tblActions.getSelectedRows()
        for row in rows:
            if 0 <= row < len(self.modelActionsSummary.itemIndex):
                page, row = self.modelActionsSummary.itemIndex[row]
                tbl = self.tabsTableList[page]
                if not tbl.model().isLockedOrExposed(row):
                    rowsList = rowsSortByPagesTables.get(tbl, None)
                    if rowsList:
                        rowsList.append(row)
                    else:
                        rowsSortByPagesTables[tbl] = [row]
        for tbl in rowsSortByPagesTables:
            rows = rowsSortByPagesTables.get(tbl, [])
            rows.sort(reverse=True)
            for row in rows:
                tbl.model().removeRow(row)
            tbl.emitDelRows()


    def on_actUnBindAction_triggered(self):
        from Events.Action import CActionTypeCache
        tabs = {
            0: self.tabStatus,
            1: self.tabDiagnostic,
            2: self.tabCure,
            3: self.tabMisc
        }
        
        def nomenclatureGroupingRows(rows):
            newRows = []
            newRows.extend(rows)
            for proxyRow in rows:
                if 0 <= proxyRow < len(self.modelActionsSummary.itemIndex):
                    page, proxyRow = self.modelActionsSummary.itemIndex[proxyRow]
                    tbl = self.tabsTableList[page]
                    if not tbl.model().isLockedOrExposed(proxyRow):
                        proxyRow = tbl.model()._mapModelRow2ProxyRow[proxyRow]
                        items = tbl.model()._items
                        group = items._mapProxyRow2Group[proxyRow]
                        if isinstance(group, CExecutionPlanProxyModelGroup):
                            if group.currentItem and hasattr(group, 'groupingItem') and group.groupingItem == group.currentItem and group.groupingInfo and len(group.groupingInfo) > 1 and group.currentItem in group.groupingInfo:
                                for subrow, subgroup in items._mapProxyRow2Group.items():
                                    if isinstance(subgroup, CExecutionPlanProxyModelGroup):
                                        if subgroup.groupingItem and group.groupingItem == subgroup.groupingItem:
                                            if self.modelActionsSummary.itemIndex.index((page,subrow)) in newRows:
                                                group.removeGroupingInfo(subgroup.currentItem)
                                            else:
                                                newRows.append(self.modelActionsSummary.itemIndex.index((page,subrow)))
                                if rows != newRows:            
                                    if QtGui.QMessageBox().question(self,
                                                            u'Внимание!',
                                                            u'При откреплении группирующего элемента, открепится вся группа. Продолжить?',
                                                            QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                                            QtGui.QMessageBox.No
                                                            ) == QtGui.QMessageBox.No:
                                        return []
                            elif group.currentItem and hasattr(group, 'groupingItem') and group.currentItem._record.value('id') == group.currentItem._record.value('group_id'):
                                for subrow, subgroup in items._mapProxyRow2Group.items():
                                    if isinstance(subgroup, CExecutionPlanProxyModelGroup):
                                        if subgroup.currentItem and group.currentItem._record.value('id') == subgroup.currentItem._record.value('group_id'):
                                            if self.modelActionsSummary.itemIndex.index((page,subrow)) in newRows:
                                                pass
                                            else:
                                                newRows.append(self.modelActionsSummary.itemIndex.index((page,subrow)))
                                if rows != newRows:
                                    if QtGui.QMessageBox().question(self,
                                                            u'Внимание!',
                                                            u'При откреплении группирующего элемента, открепится вся группа. Продолжить?',
                                                            QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                                            QtGui.QMessageBox.No
                                                            ) == QtGui.QMessageBox.No:
                                        return []
            newRows.sort()
            return newRows
    
        def unbindRelated(group, row, tbl, masterId = None):
            if not group:
                return
            if not group.expanded and isinstance(group, CRelationsProxyModelGroup):
                tbl.model().touchGrouping(row)
            actions = []
            record, action = group.firstItem
            if self.modelActionsSummary.table.newRecord().count() != record.count():
                action._record = self.modelActionsSummary.removeExtCols(record)
            if not masterId:
                masterId = action.save(eventId, idx=0, checkModifyDate=False)
                actions.append(masterId)
            else:
                actions.append(action.save(eventId, idx=0, checkModifyDate=False))
            rowsList = rowsSortByPagesTables.get(tbl, None)
            if rowsList and not row in rowsList:
                rowsList.append(row)
            elif rowsList:
                pass
            else:
                rowsSortByPagesTables[tbl] = [row]
            for proxyRow in reversed(sorted(group.proxyRows)):
                record, action = group.getItem(proxyRow)
                if record == group.firstItem.record and isinstance(group, CRelationsProxyModelGroup):
                    continue
                record.setValue('master_id', masterId)
                if self.modelActionsSummary.table.newRecord().count() != record.count():
                    action._record = self.modelActionsSummary.removeExtCols(record)
                actionId = action.save(eventId, idx=0, checkModifyDate=False)
                actions.append(actionId)
                rowsList = rowsSortByPagesTables.get(tbl, None)
                if rowsList and not row in rowsList:
                    rowsList.append(row)
                elif rowsList:
                    pass
                else:
                    rowsSortByPagesTables[tbl] = [row] 
            return actions
                
        rowsSortByPagesTables = {}
        rows = self.tblActions.getSelectedRows()
        rows = nomenclatureGroupingRows(rows)
        if QtGui.QMessageBox().warning(self,
                                       u'Подтверждение',
                                       u'Открепить мероприятие?',
                                       QtGui.QMessageBox.Yes | QtGui.QMessageBox.Cancel,
                                       QtGui.QMessageBox.Cancel) == QtGui.QMessageBox.Cancel:
            return
        db = QtGui.qApp.db
        tableEvent = db.table('Event')
        tableEventType = db.table('EventType')
        clientId = self.clientId
        prevEventId = self.getEventId()

        recordEventType = db.getRecordEx(tableEventType, [tableEventType['id']],
                                         [tableEventType['context'].like(u'relatedAction%'),
                                          tableEventType['deleted'].eq(0)], u'EventType.id')
        eventTypeId = forceRef(recordEventType.value('id')) if recordEventType else None

        if not eventTypeId:
            QtGui.QMessageBox().warning(self, u'Внимание!',
                                        u'Отсутствует тип события с контекстом "relatedAction"',
                                        QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ok)
            return


        recordEvent = db.getRecordEx(tableEvent, [tableEvent['id']],
                                     [tableEvent['eventType_id'].eq(eventTypeId),
                                     tableEvent['deleted'].eq(0),
                                     tableEvent['client_id'].eq(clientId),
                                     tableEvent['prevEvent_id'].eq(prevEventId)], u'Event.id')
        eventId = forceRef(recordEvent.value('id')) if recordEvent else None

        if not eventId:
            recordEvent = tableEvent.newRecord()
            recordEvent.setValue('createDatetime', toVariant(QDateTime().currentDateTime()))
            recordEvent.setValue('createPerson_id', toVariant(QtGui.qApp.userId))
            recordEvent.setValue('modifyDatetime', toVariant(QDateTime().currentDateTime()))
            recordEvent.setValue('modifyPerson_id', toVariant(QtGui.qApp.userId))
            recordEvent.setValue('setDate', toVariant(QDateTime().currentDateTime()))
            recordEvent.setValue('eventType_id', toVariant(eventTypeId))
            recordEvent.setValue('client_id', toVariant(clientId))
            recordEvent.setValue('prevEvent_id', toVariant(prevEventId))
            eventId = db.insertRecord(tableEvent, recordEvent)

        actionIdList = []
        unbind = {}
        for row in rows:
            if 0 <= row < len(self.modelActionsSummary.itemIndex):
                page, row = self.modelActionsSummary.itemIndex[row]
                tbl = self.tabsTableList[page]
                if not tbl.model().isLockedOrExposed(row):
                    row = tbl.model()._mapModelRow2ProxyRow[row]
                    items = tbl.model()._items
                    group = items._mapProxyRow2Group[row]
                    text = None
                    if group.firstItem.action.getMasterId():
                        for itemClass in list(tabs.values()):
                            if group.firstItem.action.getType().class_ == itemClass:
                                continue
                            for item in itemClass.modelAPActions._groups.groupsIterator:
                                if item.firstItem.id == group.firstItem.action.getMasterId():
                                    row = item._mapItem2Row[item.firstItem]
                                    page, row = self.modelActionsSummary.itemIndex[row]
                                    tbl = self.tabsTableList[page]
                                    row = tbl.model()._mapModelRow2ProxyRow[row]
                                    items = tbl.model()._items
                                    group = items._mapProxyRow2Group[row]
                                    text = u"При откреплении подчиненного действия открепятся все подчиненные и родительское. Продолжить?"
                                    break
                    if row < len(items):
                        record, action = items[row]
                    else:
                        if not group.expanded and isinstance(group, CRelationsProxyModelGroup):
                            tbl.model().touchGrouping(row)
                        record, action = group.getItem(row)
                    if isinstance(group, CRelationsProxyModelGroup):
                        parentActionType = group.firstItem.action.getType()
                        relatedActionTypes = CActionTypeCache.getById(parentActionType.id).getRelatedActionTypes()
                        required = []
                        for item in relatedActionTypes:
                            relatedActionType = CActionTypeCache.getById(item)
                            if parentActionType.class_ != relatedActionType.class_:
                                required.append(relatedActionType.class_)     
                        required = set(required)
                        if (len(group.items) > 1 or required) and record == group.firstItem.record and not text:
                            text = u"При откреплении родительского действия открепятся и все подчиненные. Продолжить?"
                        else:
                            text = u"При откреплении подчиненного действия открепятся все подчиненные и родительское. Продолжить?"
                        res = QtGui.QMessageBox().warning(
                                            None,
                                            u'Внимание!',
                                            text,
                                            QtGui.QMessageBox.Ok|QtGui.QMessageBox.Cancel,
                                            QtGui.QMessageBox.Cancel)
                        if res == QtGui.QMessageBox.Ok:
                            unbind[row] = True
                            actions = unbindRelated(group, row, tbl)
                            actionIdList.extend(actions)
                            for itemClass in required:
                                for item in tabs[itemClass].modelAPActions._groups.groupsIterator:
                                    masterId = actions[0]
                                    if item.firstItem.action.getMasterId() == group.firstItem.id:
                                        actions = unbindRelated(item, item._mapItem2Row[item.firstItem], self.tabsTableList[itemClass], masterId)
                                        actionIdList.extend(actions)
                            continue
                        else:
                            return False
                    if self.modelActionsSummary.table.newRecord().count() != record.count():
                        action._record = self.modelActionsSummary.removeExtCols(record)
                    actionId = action.save(eventId, idx=0, checkModifyDate=False)
                    actionIdList.append(actionId)
                    rowsList = rowsSortByPagesTables.get(tbl, None)
                    if rowsList:
                        rowsList.append(row)
                    else:
                        rowsSortByPagesTables[tbl] = [row]
        for tbl in rowsSortByPagesTables:
            rows = rowsSortByPagesTables.get(tbl, [])
            rows.sort(reverse=True)
            for row in rows:
                if row in unbind.keys():
                    tbl.model()._unbindRow(row)
                else:
                    tbl.model().removeRow(row)
            tbl.emitDelRows()
            for actionId in actionIdList:
                if actionId in tbl.model().actionIdForMarkDeleted:
                    tbl.model().actionIdForMarkDeleted.remove(actionId)

# ################################################################

def checkTissueJournalStatusByActions(actionModelItemsList):
    actionTakenTissueJournalIdList = []
    for record, action in actionModelItemsList:
        actionTakenTissueJournalId = forceRef(record.value('takenTissueJournal_id'))
        if actionTakenTissueJournalId and actionTakenTissueJournalId not in actionTakenTissueJournalIdList:
            actionTakenTissueJournalIdList.append(actionTakenTissueJournalId)
            targetIdList = QtGui.qApp.db.getDistinctIdList('TakenTissueJournal',
                                                           where='parent_id=%d' % actionTakenTissueJournalId)
            for targetId in targetIdList:
                checkTissueJournalStatus(targetId, actionTakenTissueJournalId)


def checkTissueJournalStatus(takenTissueJournalId, actionTakenTissueJournalId=None):
    db = QtGui.qApp.db
    if actionTakenTissueJournalId is None:
        actionTakenTissueJournalId = forceRef(db.translate('TakenTissueJournal', 'id', takenTissueJournalId, 'parent_id'))

    recordList = db.getRecordList('Action', 'DISTINCT Action.`status`',
                                  'Action.`deleted`=0 AND Action.`takenTissueJournal_id`=%d' % actionTakenTissueJournalId)
    if len(recordList) > 1:
        record = db.getRecord('TakenTissueJournal', 'id, status', takenTissueJournalId)
        record.setValue('status', QVariant(CTissueStatus.inProcess))
        db.updateRecord('TakenTissueJournal', record)
    if len(recordList) == 1:
        actionStatusRecord = recordList[0]
        actionsStatus = forceInt(actionStatusRecord.value('status'))
        record = db.getRecord('TakenTissueJournal', 'id, status', takenTissueJournalId)
        # в журнале забора биоматериалов теже статусы что и в действиях но со сдвигом на единицу
        # статус 0 в журнале - 'в работе'
        takenTissueStatus = CTissueStatus.fromActionStatus(actionsStatus)
        record.setValue('status', QVariant(takenTissueStatus))
        db.updateRecord('TakenTissueJournal', record)


def getExternalIdDateCond(tissueType, date):
    db = QtGui.qApp.db
    table = db.table('TakenTissueJournal')
    counterResetType = forceInt(db.translate('rbTissueType', 'id', tissueType, 'counterResetType'))
    if counterResetType == 0:   # каждый день новый отсчет
        return table['datetimeTaken'].dateEq(date)
    elif counterResetType == 1: # каждую неделю
        begDate = QDate(date.year(), date.month(), QDate(date).addDays(-(date.dayOfWeek()-1)).day())
        endDate = QDate(begDate).addDays(6)
    elif counterResetType == 2: # каждый месяц
        begDate = QDate(date.year(), date.month(), 1)
        endDate = QDate(date.year(), date.month(), date.daysInMonth())
    elif counterResetType == 3: # каждые пол года
        begMonth = 1 if date.month() <= 6 else 7
        endDays = 30 if begMonth == 1 else 31
        begDate = QDate(date.year(), begMonth, 1)
        endDate = QDate(date.year(), begMonth+5, endDays)
    elif counterResetType == 4: # каждый год
        begDate = QDate(date.year(), 1, 1)
        endDate = QDate(date.year(), 12, 31)
    else:
        return None # никогда
    return db.joinAnd([table['datetimeTaken'].dateGe(begDate),
                       table['datetimeTaken'].dateLe(endDate)])


# ###########################################################################
def checkUniqueEventVoucherNumber(voucherNumber, eventTypeId, date, eventId, voucherSerial=None, counterId=None):
    db = QtGui.qApp.db
    tableEvent = db.table('Event')
    tableEventType = db.table('EventType')
    tableEventVoucher = db.table('Event_Voucher')
    table = tableEvent.innerJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
    table = table.innerJoin(tableEventVoucher, tableEventVoucher['event_id'].eq(tableEvent['id']))
    cond   = [tableEventVoucher['number'].eq(voucherNumber),
              tableEvent['deleted'].eq(0),
              tableEventVoucher['deleted'].eq(0)
             ]
    if voucherSerial:
        cond.append(tableEventVoucher['serial'].eq(voucherSerial))
    if not counterId:
        counterId = getEventvoucherCounterId(eventTypeId)
    if counterId:
        cond.append(tableEventType['counter_id'].eq(counterId))
        dateAsString = db.formatDate(date) if date else 'CURRENT_DATE()'
        query = db.query('''SELECT findOrCreateCounterValueRecord(%d, %s)''' % (counterId, dateAsString))
        if query.first():
            counterValueId = forceRef(query.record().value(0))
            record = db.getRecord('rbCounter_Value', ('begDate', 'endDate'), counterValueId)
            if record:
                begDate = forceDate(record.value('begDate'))
                endDate = forceDate(record.value('endDate'))
                timeCond = []
                if begDate:
                    timeCond.append(tableEvent['setDate'].ge(begDate))
                if endDate:
                    timeCond.append(tableEvent['setDate'].le(endDate))
                if timeCond:
                    cond.append(db.joinAnd(timeCond))
#    elif eventTypeId:
#        cond.append(tableEventType['id'].eq(eventTypeId))
    if eventId:
        cond.append(tableEvent['id'].ne(eventId))
    fields = [tableEvent['id'].name(),
              tableEvent['eventType_id'].name(),
              tableEvent['setDate'].name(),
              tableEvent['client_id'].name()
              ]
    result = []
    recordList = db.getRecordList(table, fields, cond)
    for record in recordList:
        id = forceRef(record.value('id'))
        eventType = getEventName(forceRef(record.value('eventType_id')))
        setDate = forceString(record.value('setDate'))
        clientId = forceRef(record.value('client_id'))
        clientRecord = db.getRecord('Client', 'lastName, firstName, patrName', clientId)
        clientName = formatName(clientRecord.value('lastName'),
                                clientRecord.value('firstName'),
                                clientRecord.value('patrName'))
        resultValue = u'Событие(%s): %d от %s, пациент \'%s\'' %(eventType, id, setDate, clientName)
        result.append(resultValue)
    return result


def checkUniqueEventExternalId(externalId, eventTypeId, date, eventId):
    db = QtGui.qApp.db

    tableEvent = db.table('Event')
    tableEventType = db.table('EventType')
    table = tableEvent.leftJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
    cond   = [tableEvent['externalId'].eq(externalId),
              tableEvent['deleted'].eq(0)
             ]
    counterId = getEventCounterId(eventTypeId)
    if counterId:
        cond.append(tableEventType['counter_id'].eq(counterId))
        dateAsString = db.formatDate(date) if date else 'CURRENT_DATE()'
        query = db.query('''SELECT findOrCreateCounterValueRecord(%d, %s)''' % (counterId, dateAsString))
        if query.first():
            counterValueId = forceRef(query.record().value(0))
            record = db.getRecord('rbCounter_Value', ('begDate', 'endDate'), counterValueId)
            if record:
                begDate = forceDate(record.value('begDate'))
                endDate = forceDate(record.value('endDate'))
                timeCond = []
                if begDate:
                    timeCond.append(tableEvent['setDate'].ge(begDate))
                if endDate:
                    timeCond.append(tableEvent['setDate'].le(endDate))
                if timeCond:
                    cond.append(db.joinAnd(timeCond))
    else:
        cond.append(tableEventType['id'].eq(eventTypeId))

    if eventId:
        cond.append(tableEvent['id'].ne(eventId))
    fields = [tableEvent['id'].name(),
              tableEvent['eventType_id'].name(),
              tableEvent['setDate'].name(),
              tableEvent['client_id'].name(),
              tableEvent['deleted'].eq(0)]
    result = []
    recordList = db.getRecordList(table, fields, cond)
    for record in recordList:
        id = forceRef(record.value('id'))
        eventType = getEventName(forceRef(record.value('eventType_id')))
        setDate = forceString(record.value('setDate'))
        clientId = forceRef(record.value('client_id'))
        clientRecord = db.getRecord('Client', 'lastName, firstName, patrName', clientId)
        clientName = formatName(clientRecord.value('lastName'),
                                clientRecord.value('firstName'),
                                clientRecord.value('patrName'))
        resultValue = u'Событие(%s): %d от %s, пациент \'%s\'' %(eventType, id, setDate, clientName)
        result.append(resultValue)
    return result


def getDiagnosticResultIdList(eventPurposeId, resultId = None):
    if eventPurposeId:
        db = QtGui.qApp.db
        table = db.table('rbDiagnosticResult')
        cond = [table['eventPurpose_id'].eq(eventPurposeId)]
        if resultId:
            cond.append(table['result_id'].eq(resultId))
        return db.getDistinctIdList(table, [table['id']], cond)
    return []


def getDiagnosticResultId(resultId, eventPurposeId = None):
    if resultId:
        db = QtGui.qApp.db
        table = db.table('rbDiagnosticResult')
        cond = [table['result_id'].eq(resultId)]
        if eventPurposeId:
            cond.append(table['eventPurpose_id'].eq(eventPurposeId))
        record = db.getRecordEx(table, [table['id']], cond)
        return forceRef(record.value('id')) if record else None
    return None


def getEventResultId(id, eventPurposeId = None):
    if id:
        db = QtGui.qApp.db
        table = db.table('rbDiagnosticResult')
        cond = [table['id'].eq(id)]
        if eventPurposeId:
            cond.append(table['eventPurpose_id'].eq(eventPurposeId))
        record = db.getRecordEx(table, [table['result_id']], cond)
        return forceRef(record.value('result_id')) if record else None
    return None


def getNewResultCond(resultId, endDateCheck):
    if not resultId:
        return ''
    db = QtGui.qApp.db
    ishlCode = forceString(db.translate('rbDiagnosticResult', 'id', resultId, 'regionalCode'))
    table = db.table('soc_checkSpr12')
    cond = [table['code_ishl'].contain(ishlCode),
            table['begDate'].le(endDateCheck),
            table['endDate'].gt(endDateCheck.addDays(1))]
    records = db.getRecordList(table, 'code', cond)
    ishob = []
    for record in records:
        ishob.append(forceString(record.value('code')))
    if ishob:
        table = db.table('rbResult')
        return ' AND %s' % table['regionalCode'].inlist(ishob)
    return ''


def isDefaultResultIdValid(resultId, eventPurposeId, condition):
    if not resultId:
        return False
    db = QtGui.qApp.db
    query = db.query('''SELECT id FROM rbResult where id=\'%d\' and eventPurpose_id=\'%d\' %s''' % (resultId, eventPurposeId, condition))
    while query.next():
        record = query.record()
        if record:
            return True
    return False



def mkbIsOnko(mkb1, mkb2):
    if (mkb1 and len(mkb1) > 1 and mkb1[0] == 'C') or (
            mkb1 and mkb2 and mkb1[:3] == 'D70' and (('C00' <= mkb2[:3] <= 'C80') or (mkb2[:3] == 'C97'))) or (
            mkb1 and ('D00' <= mkb1[:3] <= 'D09')) or (mkb1 and ('D45' <= mkb1[:3] <= 'D47')):
        return True
    return False


def mkbIsVIMIS(mkb):
    db = QtGui.qApp.db
    table = db.table('rbMKB_vimis')
    record = db.getRecordEx(table, '`group`', table['code'].eq(mkb))
    if record:
        return forceInt(record.value('group'))
    return 0


# WTF
def setActionPropertiesColumnVisible(actionType, propertiesView):
    propertiesView.setColumnHidden(0, not actionType.propertyAssignedVisible)
    propertiesView.setColumnHidden(2, not actionType.propertyUnitVisible)
    propertiesView.setColumnHidden(3, not actionType.propertyNormVisible)
    propertiesView.setColumnHidden(4, not actionType.propertyEvaluationVisible)
    propertiesView.setColumnHidden(5, not actionType.propertyCommentVisible)


def validCalculatorSettings(value):
    return True if value in ('LL*', 'GG*', 'EE*', 'CI*') else bool(re.match('^[0-9/*\-+][A%][0-9A-D]$', value))



def getPrevEventIdByEventTypeId(prevEventTypeId, clientId):
    db = QtGui.qApp.db
    tableEvent = db.table('Event')
    cond = [tableEvent['deleted'].eq(0),
            tableEvent['eventType_id'].eq(prevEventTypeId),
            tableEvent['client_id'].eq(clientId)]
    return forceRef(db.getMax(tableEvent, tableEvent['id'].name(), cond))


# ##############################################################
class CRadiationDoseSumLabel(QtGui.QLabel):
    def __init__(self, parent):
        QtGui.QLabel.__init__(self, parent)
        self._onlyTotalDoseInfo = True
        self._info = None

    def setRadiationDoseInfo(self, info):
        if info:
            self._info = info
            if self._onlyTotalDoseInfo:
                value = u'Сумма доз: %.2f'%info['total']
            else:
                value = '\n'.join(['%s: %s' % (key, item) for key, item in info.items() if key != 'total']+[u'Всего: %s'%info['total']])
            self.setText(value)


    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._onlyTotalDoseInfo = not self._onlyTotalDoseInfo
            self.setRadiationDoseInfo(self._info)
        QtGui.QLabel.mousePressEvent(self, event)


# ##############################################################################


class CActionWidgetVisibilityButton(QtGui.QToolButton):
    __pyqtSignals__ = ('arrowTypeChanged(bool)',
                      )
    arrowType = None
    def __init__(self, parent=None):
        QtGui.QToolButton.__init__(self, parent)
        self._arrowType = self.getArrowType()
        self.connect(self, SIGNAL('released()'), self.on_arrowChanged)


    def on_arrowChanged(self):
        self.applayArrow(self.changeArrowType())


    def emitArrowTypeChanged(self):
        self.emit(SIGNAL('arrowTypeChanged(bool)'), self._arrowType==Qt.UpArrow)


    def applayArrow(self, arrowType=None):
        if arrowType is None:
            arrowType = self.getArrowType() if self.getArrowType() else self.changeArrowType()
        self._arrowType = arrowType
        self.setArrowType(self._arrowType)
        self.emitArrowTypeChanged()

    @classmethod
    def changeArrowType(cls):
        cls.arrowType = {False: Qt.UpArrow, True:Qt.DownArrow}.get(cls.arrowType==Qt.UpArrow, Qt.UpArrow)
        return cls.arrowType


    @classmethod
    def getArrowType(cls):
        return cls.arrowType


# ###########################################


def checkDateByRecord(record, date):
    if record:
        begDate = forceDate(record.value('begDate'))
        endDate = forceDate(record.value('endDate'))

        return checkDateByPeriod(begDate, endDate, date)

    return False


def checkDateByPeriod(begDate, endDate, date):
    if begDate and endDate:
        return begDate <= date <= endDate
    elif begDate:
        return begDate <= date
    elif endDate:
        return date <= endDate
    else:
        return True


def checkAttachOnDate(clientId, date):
    if not date:
        return True

    attacheList = getClientAttaches(clientId)
    for attach in attacheList:
        if checkDateByPeriod(attach['begDate'], attach['endDate'], date):
            return True
    return False


def checkPolicyOnDate(clientId, date):
    if not date:
        return True

    policyRecord = getClientCompulsoryPolicy(clientId)
    if checkDateByRecord(policyRecord, date):
        return True

    policyRecord = getClientVoluntaryPolicy(clientId)
    return checkDateByRecord(policyRecord, date)


def getExistsNomenclature(nomenclatureIdList, filter={}):
    if not nomenclatureIdList:
        return {}

    result = {}
    db = QtGui.qApp.db
    tableStockMotion = db.table('StockMotion')
    tableStockMotionItem = db.table('StockMotion_Item')
    clientId = filter.get('clientId', None)
    financeId = filter.get('financeId', None)
    medicalAidKindId = filter.get('medicalAidKindId', None)
    batch = filter.get('batch', None)
    shelfTime = filter.get('shelfTime', None)
    orgStructureIdFilter = filter.get('orgStructureId', None)
    orgStructureId = orgStructureIdFilter or QtGui.qApp.currentOrgStructureId()
    begDateAction = filter.get('begDateAction', None)
    if clientId:
        nomenclatureIdListCond = u''
        if nomenclatureIdList:
            nomenclatureIdListCond = tableStockMotionItem['nomenclature_id'].inlist(nomenclatureIdList)
        financeCond = u''
        if financeId: #0012562:0044803
            if QtGui.qApp.controlSMFinance() == 1:
                financeCond = db.joinOr([tableStockMotionItem['finance_id'].eq(financeId), tableStockMotionItem['finance_id'].isNull()])
            elif QtGui.qApp.controlSMFinance() == 2:
                financeCond = tableStockMotionItem['finance_id'].eq(financeId)
        if medicalAidKindId:
            medicalAidKindCond = db.joinOr([tableStockMotionItem['medicalAidKind_id'].eq(medicalAidKindId), tableStockMotionItem['medicalAidKind_id'].isNull()])
        else:
            medicalAidKindCond = u''
        if batch:
            batchCond = tableStockMotionItem['batch'].eq(batch)
        else:
            batchCond = u''
        if shelfTime:
            shelfTimeCond = db.joinOr(tableStockMotionItem['shelfTime'].isNull(), tableStockMotionItem['shelfTime'].dateGe(shelfTime))
        else:
            shelfTimeCond = u''
        if orgStructureId:
            orgStructureCond = tableStockMotion['supplier_id'].eq(orgStructureId)
        else:
            orgStructureCond = u''
        if begDateAction:
            dateCond = tableStockMotion['date'].dateLe(begDateAction)
        else:
            dateCond = u''
        reservationStmt = u'''SELECT
                StockMotion_Item.nomenclature_id,
                StockMotion_Item.finance_id,
                StockMotion_Item.batch,
                StockMotion_Item.price,
                StockMotion_Item.unit_id,
                StockMotion_Item.shelfTime,
                StockMotion_Item.medicalAidKind_id,
                StockMotion_Item.qnt
            FROM
                StockMotion
                    INNER JOIN
                StockMotion_Item ON StockMotion_Item.master_id = StockMotion.id
            WHERE
                    StockMotion.type = 6
                    AND StockMotion_Item.qnt > 0
                    AND StockMotion.deleted = 0
                    AND StockMotion_Item.deleted = 0
                    AND StockMotion.client_id = %(clientId)s
                    AND %(nomenclatureIdListCond)s
                    and %(financeCond)s
                    AND %(medicalAidKindCond)s
                    AND %(shelfTimeCond)s
                    AND %(batchCond)s
                    AND %(orgStructureCond)s
                    AND %(dateCond)s
                    ORDER BY StockMotion_Item.shelfTime, StockMotion_Item.qnt'''% {
        'clientId': clientId,
        'nomenclatureIdListCond': nomenclatureIdListCond if nomenclatureIdListCond else 1,
        'financeCond': financeCond if financeCond else 1,
        'medicalAidKindCond':medicalAidKindCond if medicalAidKindId else 1,
        'shelfTimeCond':shelfTimeCond if shelfTimeCond else 1,
        'batchCond':batchCond if batchCond else 1,
        'orgStructureCond':orgStructureCond if orgStructureCond else 1,
        'dateCond':dateCond if dateCond else 1
            }
        reservationQuery = db.query(reservationStmt)
        while reservationQuery.next():
            reservationRecord = reservationQuery.record()
            if reservationRecord:
                nomenclatureId = forceRef(reservationRecord.value('nomenclature_id'))
                financeId = forceRef(reservationRecord.value('finance_id'))
                medicalAidKindId = forceRef(reservationRecord.value('medicalAidKind_id'))
                recordList = result.setdefault((nomenclatureId,  financeId, clientId, medicalAidKindId), [])
                recordList.append(reservationRecord)
        return result
    stmt = getExistsNomenclatureStmt(nomenclatureId=nomenclatureIdList,
                                     financeId=financeId,
                                     orgStructureId=orgStructureId,
                                     medicalAidKindId=medicalAidKindId,
                                     batch=batch,
                                     shelfTime=shelfTime)
    query = db.query(stmt)
    while query.next():
        record = query.record()
        nomenclatureId = forceRef(record.value('nomenclature_id'))
        financeId = forceRef(record.value('finance_id'))
        medicalAidKindId = forceRef(record.value('medicalAidKind_id'))
        recordList = result.setdefault((nomenclatureId,  financeId, medicalAidKindId), [])
        recordList.append(record)
    return result


def syncNomenclature(exists, targetRecord, unset, translateExistsQnt=False, financeId=None, clientId=None, medicalAidKindId=None, isStrictMedicalAidKindId=False, isNoAvialableQnt=False, avialableQntDict = {}, orgStructureId=None):
    stockMotionItems = []
    orgStructureId = orgStructureId or QtGui.qApp.currentOrgStructureId()
    nomenclatureId = forceRef(targetRecord.value('nomenclature_id'))
    qnt = forceDouble(targetRecord.value('qnt'))
    isQntFilled = False
    sourceRecordList = []
    sourceRecord = None
    existsList = []
    reservedClientList = []
    for exKey, exItems in exists.items():
        if len(exKey) > 3:
            for exItem in exItems:
                reservedClientList.append((exKey, exItem))
    reservedClientList.sort(key=lambda x: (forceDate(x[1].value('shelfTime')), forceDouble(x[1].value('qnt'))), reverse=False)
    for exKey, exItems in exists.items():
        if len(exKey) < 4:
            for exItem in exItems:
                existsList.append((exKey, exItem))
    existsList.sort(key=lambda x: (forceDate(x[1].value('shelfTime')), forceDouble(x[1].value('qnt'))), reverse=False)
    if clientId:
        for exKey, exItem in reservedClientList:
            sourceRecord = None
            if (nomenclatureId, financeId, clientId, medicalAidKindId) == exKey:
                sourceRecord = exItem
            if not sourceRecord and not isStrictMedicalAidKindId and QtGui.qApp.controlSMFinance() != 0:
                if (nomenclatureId, financeId, clientId, None) == exKey:
                    sourceRecord = exItem
            if not sourceRecord and QtGui.qApp.controlSMFinance() in (0, 1):
                if isStrictMedicalAidKindId:
                    if (nomenclatureId, financeId, clientId, medicalAidKindId) == exKey or (nomenclatureId, None, clientId, medicalAidKindId) == exKey:
                        sourceRecord = exItem
                    if not sourceRecord and (nomenclatureId == exKey[0] and financeId != exKey[1] and clientId == exKey[2] and medicalAidKindId == exKey[3]):
                        sourceRecord = exItem
                if not sourceRecord and not isStrictMedicalAidKindId:
                    if (nomenclatureId, financeId, clientId, medicalAidKindId) == exKey or (nomenclatureId, None, clientId, medicalAidKindId) == exKey:
                        sourceRecord = exItem
                    if not sourceRecord and ((nomenclatureId, financeId, clientId, None) == exKey or (nomenclatureId, None, clientId, None) == exKey):
                        sourceRecord = exItem
                    if not sourceRecord and (nomenclatureId == exKey[0] and financeId != exKey[1] and clientId == exKey[2]):
                        sourceRecord = exItem
            if sourceRecord:
                sourceRecordList.append(sourceRecord)
    for exKey, exItem in existsList:
        sourceRecord = None
        if (nomenclatureId, financeId, medicalAidKindId) == exKey:
            sourceRecord = exItem
        if not sourceRecord and not isStrictMedicalAidKindId and QtGui.qApp.controlSMFinance() != 0:
            if (nomenclatureId, financeId, None) == exKey:
                sourceRecord = exItem
        if not sourceRecord and QtGui.qApp.controlSMFinance() in (0, 1):
            if isStrictMedicalAidKindId:
                if (nomenclatureId, financeId, medicalAidKindId) == exKey or (nomenclatureId, None, medicalAidKindId) == exKey:
                    sourceRecord = exItem
                if not sourceRecord and (nomenclatureId == exKey[0] and financeId != exKey[1] and medicalAidKindId == exKey[2]):
                    sourceRecord = exItem
            if not sourceRecord and not isStrictMedicalAidKindId:
                if (nomenclatureId, financeId, medicalAidKindId) == exKey or (nomenclatureId, None, medicalAidKindId) == exKey:
                    sourceRecord = exItem
                if not sourceRecord and ((nomenclatureId, financeId, None) == exKey or (nomenclatureId, None, None) == exKey):
                    sourceRecord = exItem
                if not sourceRecord and (nomenclatureId == exKey[0] and financeId != exKey[1]):
                    sourceRecord = exItem
        if sourceRecord:
            sourceRecordList.append(sourceRecord)
    avialableQnt = None
    if not sourceRecordList:
        avialableQntLine = avialableQntDict.get(nomenclatureId, {})
        avialableQnt = avialableQntLine.get((None, None, None, None), None)
        avialableQntLine[(None, None, None, None)] = 0
        avialableQntDict[nomenclatureId] = avialableQntLine
    #newTargetRecord = targetRecord
    stockMotionRecords = {}
    targetUnitId = forceRef(targetRecord.value('unit_id'))
    for recordCnt, sourceRecord in enumerate(sourceRecordList):
        existsQnt = forceDouble(sourceRecord.value('qnt'))
        sourceUnitId = forceRef(sourceRecord.value('unit_id'))
        nomenclatureIdSR = forceRef(sourceRecord.value('nomenclature_id'))
        batch = forceString(sourceRecord.value('batch'))
        shelfTime = forceDate(sourceRecord.value('shelfTime'))
        price = forceDouble(sourceRecord.value('price'))
        financeId = forceRef(sourceRecord.value('finance_id'))
        medicalAidKindId = forceRef(sourceRecord.value('medicalAidKind_id'))
        newRow, newTargetRecord = stockMotionRecords.get((nomenclatureIdSR, batch, pyDate(shelfTime), price, financeId, medicalAidKindId), [-1, None])
        if translateExistsQnt:
            if targetUnitId and sourceUnitId != targetUnitId:
                existsQnt = round(applyNomenclatureUnitRatio(existsQnt, nomenclatureId, targetUnitId), 2)
        if existsQnt > 0 and qnt > 0:
            if recordCnt == 0 and not newTargetRecord:
                newTargetRecord = targetRecord
            elif recordCnt > 0 and not newTargetRecord:
                newTargetRecord = QtGui.qApp.db.table('StockMotion_Item').newRecord()
                newTargetRecord.setValue('nomenclature_id', toVariant(nomenclatureId))
                newTargetRecord.setValue('unit_id', toVariant(targetUnitId))
            if existsQnt >= qnt:
                sourceRecord.setValue('qnt', toVariant(existsQnt-qnt))
                isQntFilled = True
                prevQnt = forceDouble(newTargetRecord.value('qnt')) if recordCnt > 0 else 0.0
                newTargetRecord.setValue('qnt', toVariant(prevQnt+qnt))
            else:
                sourceRecord.setValue('qnt', toVariant(0))
                qnt = qnt - existsQnt
                prevQnt = forceDouble(newTargetRecord.value('qnt')) if recordCnt > 0 else 0.0
                newTargetRecord.setValue('qnt', toVariant(prevQnt+existsQnt))
            if not unset:
                newTargetRecord.setValue('batch', batch)
                stockUnitId = forceRef(QtGui.qApp.db.translate('rbNomenclature', 'id', nomenclatureId, 'defaultStockUnit_id'))
                if targetUnitId and sourceUnitId == targetUnitId:
                    pass
                else:
                    if sourceUnitId:
                        ratio = getRatio(nomenclatureId, targetUnitId, sourceUnitId)
                        if ratio is not None:
                            price = price*ratio
                    elif stockUnitId and stockUnitId != targetUnitId:
                        ratio = getRatio(nomenclatureId, targetUnitId, stockUnitId)
                        if ratio is not None:
                            price = price*ratio
                newTargetRecord.setValue('price', toVariant(price))
                newTargetRecord.setValue('sum', toVariant(forceDouble(newTargetRecord.value('qnt')) * forceDouble(newTargetRecord.value('price'))))
                newTargetRecord.setValue('shelfTime', shelfTime)
                newTargetRecord.setValue('finance_id', financeId)
                newTargetRecord.setValue('medicalAidKind_id', medicalAidKindId)
                if isNoAvialableQnt and (financeId or batch or shelfTime or price):
                    priceFind = price
                    if stockUnitId and stockUnitId != targetUnitId:
                        ratioFind = getRatio(nomenclatureId, stockUnitId, targetUnitId)
                        if ratioFind is not None:
                            priceFind = priceFind*ratioFind
                    avialableQntLine = avialableQntDict.setdefault(nomenclatureId, {})
                    avialableQnt = avialableQntLine.setdefault((financeId, batch, shelfTime, price), None)
                    if avialableQnt is None:
                        avialableQnt = round(getExistsNomenclatureAmount(nomenclatureId, financeId = financeId, batch=batch, orgStructureId = orgStructureId, unitId = targetUnitId, medicalAidKindId = medicalAidKindId, exact=True, price=priceFind), 2)
                    avialableQnt -= forceDouble(newTargetRecord.value('qnt'))
                    avialableQntLine[(financeId, batch, shelfTime, price)] = avialableQnt
                    avialableQntDict[nomenclatureId] = avialableQntLine
            if QtGui.qApp.controlSMFinance() == 2:
                stockMotionRecords[(nomenclatureIdSR, batch, pyDate(shelfTime), price, financeId, medicalAidKindId)] = [newRow if newRow >= 0 else recordCnt, newTargetRecord]
            #
            # sourceSum = forceDouble(sourceRecord.value('sum'))
            # price = sourceSum/existsQnt
            # newTargetRecord.setValue('sum', toVariant((qnt-residue)*price))
        stockMotionRecords[(nomenclatureIdSR, batch, pyDate(shelfTime), price, financeId, medicalAidKindId)] = [newRow if newRow >= 0 else recordCnt, newTargetRecord]
        if QtGui.qApp.controlSMFinance() in (0, 1):
            stockMotionRecords[(nomenclatureIdSR, batch, pyDate(shelfTime), price, financeId, medicalAidKindId)] = [newRow if newRow >= 0 else recordCnt, newTargetRecord]
#        stockMotionItems.append(newTargetRecord)
        if isQntFilled:
            break
    stockMotionItemsList = stockMotionRecords.values()
    stockMotionItemsList.sort(key=lambda x: x[0])
    for i, stockMotionItem in stockMotionItemsList:
        stockMotionItems.append(stockMotionItem)
    if len(sourceRecordList) == 0:
        stockMotionItems = [targetRecord]
    return avialableQntDict, stockMotionItems


def cutFeed(eventId, date, toEventId = None):
    db = QtGui.qApp.db
    tableEventFeed = db.table('Event_Feed')
    if toEventId:
        if eventId != toEventId:
            cond = [tableEventFeed['event_id'].eq(eventId),
                    tableEventFeed['date'].dateGe(date)]
            db.updateRecords(tableEventFeed, [tableEventFeed['event_id'].eq(toEventId)], cond)
    else:
        cond = [tableEventFeed['event_id'].eq(eventId),
                    tableEventFeed['date'].dateGt(date)]
        firstMealTimeRecord = db.getRecordEx('rbMealTime', 'MIN(begTime)')
        if firstMealTimeRecord:
            time = forceTime(firstMealTimeRecord.value(0))
            if time > date.time():
                cond = [cond[0], tableEventFeed['date'].dateGe(date)]
        db.deleteRecord(tableEventFeed, cond)


def getActionDispansPhase(eventId, phase=0):
    if not eventId:
        return None
    db = QtGui.qApp.db
    tableMESVisit = db.table('mes.MES_visit')
    tableMES = db.table('mes.MES')
    tableMESGroup = db.table('mes.mrbMESGroup')
    tableEvent = db.table('Event')
    tableAction = db.table('Action')
    tableActionType = db.table('ActionType')
    tableService = db.table('rbService')
    tablePerson = db.table('Person')
    tableMESSpeciality = db.table('mes.mrbSpeciality')
    tableSpeciality = db.table('rbSpeciality')
    queryTable = tableEvent
    queryTable = queryTable.leftJoin(tableMES, tableMES['id'].eq(tableEvent['MES_id']))
    queryTable = queryTable.leftJoin(tableMESVisit, tableMESVisit['master_id'].eq(tableMES['id']))
    queryTable = queryTable.leftJoin(tableMESGroup, tableMESGroup['id'].eq(tableMES['group_id']))
    queryTable = queryTable.leftJoin(tableAction, tableAction['event_id'].eq(tableEvent['id']))
    queryTable = queryTable.leftJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
    queryTable = queryTable.leftJoin(tableService, tableService['id'].eq(tableActionType['nomenclativeService_id']))
    queryTable = queryTable.leftJoin(tablePerson, tablePerson['id'].eq(tableAction['person_id']))
    queryTable = queryTable.leftJoin(tableSpeciality, tableSpeciality['id'].eq(tablePerson['speciality_id']))
    queryTable = queryTable.leftJoin(tableMESSpeciality, tableMESSpeciality['id'].eq(tableMESVisit['speciality_id']))
    cond = [tableEvent['deleted'].eq(0),
            tableEvent['id'].eq(eventId),
            tableMESGroup['code'].eq(u'ДиспанС'),
            tableAction['endDate'].isNotNull(),
            tableAction['deleted'].eq(0),
            '(mes.MES_visit.`serviceCode` = SUBSTR(rbService.`code`,1, CHAR_LENGTH(mes.MES_visit.`serviceCode`))AND SUBSTR(rbService.`code`, CHAR_LENGTH(mes.MES_visit.`serviceCode`)+1) REGEXP \'^([*.]|$)\'  OR Action.`id` IS NULL)',
            ]
    if phase == 1:
        cond.append(tableEvent['prevEvent_id'].isNull())
    elif phase == 2:
        cond.append(tableEvent['prevEvent_id'].isNotNull())
    fields = [tableEvent['id'].alias('eventId'),
              tableEvent['client_id'].alias('clientId'),
              tableEvent['execDate'].alias('eventExecDate'),
              tableAction['actionType_id'].alias('actionTypeId'),
              'CONCAT_WS(" | ", ActionType.`code`, ActionType.`name`) AS actionTypeName',
              tableService['name'].alias('serviceName'),
              tableAction['id'].alias('actionId'),
              tableAction['endDate'],
              tableAction['directionDate'],
              tableAction['MKB'].alias('actionMkb'),
              tableMESVisit['additionalServiceCode'].alias('numMesVisitCode'),
              db.if_(db.joinAnd([tableAction['endDate'].dateGe(tableEvent['setDate']),
              tableAction['endDate'].dateLe(tableEvent['execDate'])]), '1', '0') + ' AS actionExecNow'
              ]
    fields.append('''IF((DATE(Action.endDate)>=DATE(DATE_ADD(Event.setDate, INTERVAL -1 YEAR)))
    AND (DATE(Action.endDate)<DATE(Event.setDate)),1,0) AS actionExecPrev''')
    fields.append('''(SELECT COUNT(A.id)
    FROM Action AS A
    WHERE A.event_id = Event.id AND A.status = 6 AND A.endDate IS NULL AND A.deleted = 0
    GROUP BY Event.id
    ) AS actionExecRefusal''')
    fields.append('''(SELECT COUNT(ActionProperty.id)
    FROM ActionProperty
    WHERE ActionProperty.action_id = Action.id AND ActionProperty.deleted = 0
    AND ActionProperty.evaluation IS NOT NULL AND ActionProperty.evaluation != 0
    GROUP BY Event.id) AS propertyEvaluation''')
    stmt = db.selectDistinctStmt(queryTable, fields, cond, tableEvent['id'].name())
    return db.query(stmt)

class CCSGInfo(CInfo):
    def __init__(self, context, id):
        CInfo.__init__(self, context)
        self.id = id


    def _load(self):
        db = QtGui.qApp.db
        table = db.table('Event_CSG')
        record = db.getRecordEx(table, '*', table['id'].eq(self.id))
        if record:
            self.initByRecord(record)
            return True
        else:
            self.initByRecord(db.dummyRecord())
            return False


    def initByRecord(self, record):
        self._begDate = CDateInfo(forceDate(record.value('begDate')))
        self._endDate = CDateInfo(forceDate(record.value('endDate')))
        self._MKB = self.getInstance(CMKBInfo, forceString(record.value('MKB')))
        self._CSGCode = forceString(record.value('CSGCode'))
        self._amount = forceInt(record.value('amount'))
        self._payStatus = forceInt(record.value('payStatus'))
        self._service = self.getInstance(CServiceInfo, forceInt(QtGui.qApp.db.translate('rbService', 'code', self._CSGCode, 'id')))

    begDate = property(lambda self: self.load()._begDate)
    endDate = property(lambda self: self.load()._endDate)
    MKB = property(lambda self: self.load()._MKB)
    CSGCode = property(lambda self: self.load()._CSGCode)
    amount = property(lambda self: self.load()._amount)
    payStatus   = property(lambda self: self.load()._payStatus)
    service    = property(lambda self: self.load()._service)


def updateDurationEvent(begDate, endDate, eventTypeId):
    if not endDate:
        endDate = QDate.currentDate()
    text = '-'
    if begDate:
        duration = begDate.daysTo(endDate)+getEventDurationRule(eventTypeId)
        if duration > 0:
            text = str(duration)
    return text


def updateDurationTakingIntoMedicalDaysEvent(begDateTime, endDateTime, eventTypeId):
    if not getEventShowTime(eventTypeId):
        return updateDurationEvent(begDateTime.date(), endDateTime.date(), eventTypeId)
    if not endDateTime.date():
        endDateTime = QDateTime.currentDateTime()
    text = '-'
    if begDateTime.date():
        day = 0
        if QtGui.qApp.isDurationTakingIntoMedicalDays():
            medicalDayBegTime = QtGui.qApp.medicalDayBegTime()
            if not medicalDayBegTime:
                medicalDayBegTime = QTime(9, 0)
            begTime = begDateTime.time()
            if begTime and begTime < medicalDayBegTime:
                day += 1
            endTime = endDateTime.time()
            if endTime and endTime < medicalDayBegTime:
                day -= 1
        duration = begDateTime.daysTo(endDateTime)+day+getEventDurationRule(eventTypeId)
        if duration > 0:
            text = str(duration)
    return text


class CCSGView(CInDocTableView):
    def on_duplicateSelectRows(self):
        currentRow = self.currentIndex().row()
        items = self.model().items()
        if currentRow < len(items):
            selectIndexes = self.selectedIndexes()
            selectRowList = []
            for selectIndex in selectIndexes:
                selectRow = selectIndex.row()
                if selectRow not in selectRowList:
                    selectRowList.append(selectRow)
            selectRowList.sort()
            for row in selectRowList:
                newRecord = self.model().getEmptyRecord()
                for i in xrange(newRecord.count()):
                    if not (newRecord.fieldName(i) == 'id' or newRecord.fieldName(i) == 'idx'):
                        newRecord.setValue(i, items[row].value(newRecord.fieldName(i)))
                items.append(newRecord)
            self.model().reset()


def calcQuantity(record, durationIsValid = False):
    aliquoticity = forceInt(record.value('aliquoticity'))
    periodicity = forceInt(record.value('periodicity'))
    duration = forceInt(record.value('duration'))
    if durationIsValid and not duration:
        duration = 1
    return math.floor((duration+periodicity)/float(periodicity+1))*(aliquoticity if aliquoticity else 1)


def calcQuantityEx(aliquoticity, periodicity, duration, durationIsValid = False):
    if durationIsValid and not duration:
        duration = 1
    return math.floor((duration+periodicity)/float(periodicity+1))*(aliquoticity if aliquoticity else 1)



def updateNomenclatureDosageValue(action):
    nomencalureId = None
    doses = None
    for properties in action._properties:
        type = properties._type
        name = type.name
        if type.isNomenclatureValueType():
            property = action.getProperty(name)
            nomencalureId = property.getValue()
            if nomencalureId:
                break
    for properties in action._properties:
        type = properties._type
        name = type.name
        if type.inActionsSelectionTable == _DOSES:  # doses
            property = action.getProperty(name)
            doses = property.getValue()
            if isinstance(doses, (float, int)):
                break
            else:
                doses = None
    action.nomenclatureExpense.updateNomenclatureDosageValue(nomencalureId, doses, force=True)
    return action


class CInputCutFeedDialog(CInputDialog):
    def __init__(self, action, actionType, actionRecord, eventPersonId, parent=None):
        CInputDialog.__init__(self, parent)
        self.chkCutFeed = QtGui.QCheckBox(self)
        self.chkCutFeed.setText(u'Отменить питание после перевода')
        self.chkCutFeed.setChecked(True)
        self.setExecPersonVisible(True)
        self.gridLayout.removeWidget(self.buttonBox)
        self.gridLayout.addWidget(self.chkCutFeed, 5, 0, 1, 2)
        self.gridLayout.addWidget(self.buttonBox, 6, 0, 1, 2)
        self.initEditors(action, actionType, actionRecord, eventPersonId)

    def initEditors(self, action, actionType, actionRecord, eventPersonId):
        self.setPerson(forceRef(actionRecord.value('person_id')))
        osTransfer = None
        osPresence = None
        if u'received' in actionType.flatCode.lower():
            osTransfer = action[u'Направлен в отделение']
            osPresence = action[u'Отделение'] if u'Отделение' in actionType._propertiesByName else None
        elif u'moving' in actionType.flatCode.lower():
            osTransfer = action[u'Переведен в отделение']
            osPresence = action[u'Отделение пребывания']
        self.cmbPerson.setOrgStructureId(osPresence, True)
        self.cmbExecPerson.setOrgStructureId(osTransfer, True)
        transferChiefId = getChiefId(osTransfer) if osTransfer else None
        self.setExecPerson(transferChiefId if transferChiefId else eventPersonId)

    def cutFeed(self):
        return self.chkCutFeed.isChecked()


def getIdListActionType(obj, flatCode):
    from Events.Action import CActionTypeCache
    from Events.ActionTypeDialog import CActionTypeDialogTableModel
    actionTypeId = None
    db = QtGui.qApp.db
    tableActionType = db.table('ActionType')
    if flatCode==u'moving':
        idList = db.getIdList(tableActionType, [tableActionType['id']], [tableActionType['flatCode'].like(flatCode), tableActionType['deleted'].eq(0)])
        idListActionType = []
        for actionTypeId in idList:
            actionType = CActionTypeCache.getById(actionTypeId) if actionTypeId else None
            orgStructureList = actionType.getPFOrgStructureRecordList()
            specialityList = actionType.getPFSpecialityRecordList()
            orgStructureIdList = [forceInt(orgStructureRecord.value('orgStructure_id')) for orgStructureRecord in orgStructureList]
            specialityIdList      = [forceInt(specialityRecord.value('speciality_id'))     for specialityRecord in specialityList]
            if len(orgStructureIdList) or len(specialityIdList):
                for orgStructureId in orgStructureIdList:
                    if orgStructureId == QtGui.qApp.userOrgStructureId and actionTypeId not in idListActionType:
                        idListActionType.append(actionTypeId)
                for specialityId in specialityIdList:
                    if specialityId == QtGui.qApp.userSpecialityId and actionTypeId not in idListActionType:
                        idListActionType.append(actionTypeId)
            else:
                if actionTypeId not in idListActionType:
                    idListActionType.append(actionTypeId)
    else:
        idListActionType = db.getIdList(tableActionType, [tableActionType['id']], [tableActionType['flatCode'].like(flatCode), tableActionType['deleted'].eq(0)])
    if len(idListActionType) > 1:
        dialogActionType = CActionTypeDialogTableModel(obj, idListActionType)
        if dialogActionType.exec_():
            actionTypeId= dialogActionType.currentItemId()
    else:
        actionTypeId = idListActionType[0] if idListActionType else None
    return actionTypeId

from Ui_ExecuteActionParamsDialog import Ui_ExecuteActionParamsDialog


class CExecuteActionParamsDialog(QtGui.QDialog, Ui_ExecuteActionParamsDialog):
    def __init__(self,  parent, isCourseVisible=True):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.isCourseVisible = isCourseVisible
        self.edtTime.setTime(QDateTime.currentDateTime().time())
        if QtGui.qApp.userId and QtGui.qApp.userSpecialityId:
            self.cmbPerson.setValue(QtGui.qApp.userId)
        self.params = {}
        self.setCourseVisible(self.isCourseVisible)


    def setCourseVisible(self, value):
        self._courseVisible = value
        self.cmbCourse.setVisible(value)
        self.lblCourse.setVisible(value)


    def setParams(self):
        self.params = {}
        self.params['execDate'] = QDateTime(self.edtDate.date(), self.edtTime.time())
        if self._courseVisible:
            self.params['course'] = self.cmbCourse.currentIndex()
        self.params['execPersonId'] = self.cmbPerson.value()


    def getParams(self):
        return self.params


    @pyqtSignature('QAbstractButton*')
    def on_buttonBox_clicked(self, button):
        buttonCode = self.buttonBox.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Ok:
            self.setParams()
        elif buttonCode == QtGui.QDialogButtonBox.Cancel:
            self.close()

def checkReferralLisLab(eventEditor, eventId):
    db = QtGui.qApp.db
    stmt = u"""select a.id as id, aps.value as value, a.directionDate
from Action a
left join ActionType at on at.id = a.actionType_id
left join ActionPropertyType apt on apt.actionType_id = at.id and apt.deleted = 0 and apt.name = 'Группа забора'
left join ActionProperty ap on ap.action_id = a.id and ap.type_id = apt.id and ap.deleted = 0
left join ActionProperty_String aps on aps.id = ap.id
where a.deleted = 0 and at.flatCode = 'referralLisLab' and not exists(select NULL from Action where Action.prescription_id = a.id)
and a.event_id = %d""" % eventId
    query = db.query(stmt)
    while query.next():
        record = query.record()
        id = forceRef(record.value('id'))
        value = forceString(record.value('value'))
        directionDate = forceDate(record.value('directionDate'))
        if id:
            stmt = u"""select a.id
    from Action a
    left join ActionType at on at.id = a.actionType_id
    where a.deleted = 0 and at.serviceType = 10 and at.flatCode = '{0}' and date(directionDate) = {1}
    and a.prescription_id is null and a.event_id = {2}""".format(value, db.formatDate(directionDate), eventId)
            actQuery = db.query(stmt)
            actIdList = []
            while actQuery.next():
                actIdList.append(forceRef(actQuery.record().value('id')))

            model = eventEditor.tabDiagnostic.tblAPActions.model()
            for row, (actRecord, action) in enumerate(model.items()):
                if action and action.getId() in actIdList:
                    action._record.setValue('prescription_id', id)
                    actRecord.setValue('prescription_id', id)
                    action.save(idx=-1)
                    model.items()[row]._data = (actRecord, action)


def sendTempInvalidDocuments(tempInvalidDoc_list):
    if tempInvalidDoc_list:
        user_id = QtGui.qApp.userId
        args_list = ['-t ' + str(i) for i in tempInvalidDoc_list]
        if platform.startswith('win'):
            command = "fsseln.exe %s -u %s" % (' '.join(args_list), user_id)
        elif platform.startswith('lin'):
            from s11main import ROOT_DIR
            command = "python2 %s %s -u %s" % (os.path.join(ROOT_DIR, 'appendix/fsselnv2/main.py'), ' '.join(args_list), user_id)
        os.popen(command)


def isDispanserisation(eventtype):
    stmt = """SELECT COUNT(rbMedicalAidType.id) cnt
            FROM EventType
                LEFT JOIN rbMedicalAidType ON EventType.medicalAidType_id = rbMedicalAidType.id 
            WHERE EventType.id = {eventtype} 
                AND rbMedicalAidType.regionalCode IN ('11', '21')""".format(eventtype=eventtype)  # ,'12'
    cnt = 0
    db = QtGui.qApp.db
    query = db.query(stmt)
    while query.next():
        record = query.record()
        cnt = forceInt(record.value('cnt'))
    if cnt > 0:
        return True
    return False


def checkFileAttachListChanged(currentList, origList):
    neq = currentList != origList
    return neq or any([item.getRecord().isDirty() for item in currentList])


def parseActionTypeGroupMKBInput(MKBInput):
    MKBList = []
    rowList = MKBInput.split(',')
    for diagnosisItem in rowList:
        diagnosisItem = diagnosisItem.strip()
        if diagnosisItem.find('-') > 0:
            MKBList.append(diagnosisItem.split('-'))
        elif diagnosisItem:
            MKBList.append(diagnosisItem)
    return MKBList


def getLfFormId(nomenclatureId = None, smnnUUID = None):
    db = QtGui.qApp.db
    tableLfForm= db.table('rbLfForm')
    tableNC = db.table('rbNomenclature')
    tableESKLP_Klp = db.table('esklp.Klp')
    tableEsklp_SmnnGrlsLf = db.table('esklp.Smnn_GrlsLf')
    queryTable = tableNC.innerJoin(tableESKLP_Klp, tableESKLP_Klp['UUID'].eq(tableNC['esklpUUID']))
    queryTable = queryTable.innerJoin(tableEsklp_SmnnGrlsLf, tableEsklp_SmnnGrlsLf['master_id'].eq(tableESKLP_Klp['smnn_id']))
    queryTable = queryTable.innerJoin(tableLfForm, db.joinAnd([tableLfForm['name'].eq(tableEsklp_SmnnGrlsLf['lf_name']), tableLfForm['dosage'].eq(tableEsklp_SmnnGrlsLf['dosage_name'])]))
    cond = [tableLfForm['isESKLP'].eq(1)]
    order = u'esklp.Smnn_GrlsLf.lf_name, esklp.Smnn_GrlsLf.dosage_name'
    if nomenclatureId:
        cond.append(tableNC['id'].eq(nomenclatureId))
    if smnnUUID:
        tableEsklp_Smnn = db.table('esklp.Smnn')
        queryTable = queryTable.innerJoin(tableEsklp_Smnn, tableEsklp_Smnn['id'].eq(tableESKLP_Klp['smnn_id']))
        cond.append(tableEsklp_Smnn['UUID'].eq(smnnUUID))
    if nomenclatureId or smnnUUID:
        cond.append(tableLfForm['name'].eq(tableESKLP_Klp['lf_norm_name']))
        cond.append(tableLfForm['dosage'].eq(tableESKLP_Klp['dosage_norm_name']))
    record = db.getRecordEx(queryTable, [tableLfForm['id']], cond, order=order)
    return forceRef(record.value('id')) if record else None


def getLfFormIdList(nomenclatureId = None, smnnUUID = None, nomenclatureIdList=[]):
    idList = []
    db = QtGui.qApp.db
    tableLfForm= db.table('rbLfForm')
    tableNC = db.table('rbNomenclature')
    tableESKLP_Klp = db.table('esklp.Klp')
    tableEsklp_SmnnGrlsLf = db.table('esklp.Smnn_GrlsLf')
    queryTable = tableNC.innerJoin(tableESKLP_Klp, tableESKLP_Klp['UUID'].eq(tableNC['esklpUUID']))
    queryTable = queryTable.innerJoin(tableEsklp_SmnnGrlsLf, tableEsklp_SmnnGrlsLf['master_id'].eq(tableESKLP_Klp['smnn_id']))
    queryTable = queryTable.innerJoin(tableLfForm, db.joinAnd([tableLfForm['name'].eq(tableEsklp_SmnnGrlsLf['lf_name']), tableLfForm['dosage'].eq(tableEsklp_SmnnGrlsLf['dosage_name'])]))
    cond = [tableLfForm['isESKLP'].eq(1)]
    order = u'esklp.Smnn_GrlsLf.lf_name, esklp.Smnn_GrlsLf.dosage_name'
    if nomenclatureId:
        cond.append(tableNC['id'].eq(nomenclatureId))
    if nomenclatureIdList:
        cond.append(tableNC['id'].inlist(nomenclatureIdList))
    if smnnUUID:
        tableEsklp_Smnn = db.table('esklp.Smnn')
        queryTable = queryTable.innerJoin(tableEsklp_Smnn, tableEsklp_Smnn['id'].eq(tableESKLP_Klp['smnn_id']))
        cond.append(tableEsklp_Smnn['UUID'].eq(smnnUUID))
    if nomenclatureId or smnnUUID:
        cond.append(tableLfForm['name'].eq(tableESKLP_Klp['lf_norm_name']))
        cond.append(tableLfForm['dosage'].eq(tableESKLP_Klp['dosage_norm_name']))
    idList = db.getDistinctIdList(queryTable, [tableLfForm['id']], cond, order=order)
    return idList


def getNomenclatureSmnn(smnnUUID, lfFormId):
    if trim(smnnUUID) and lfFormId:
        db = QtGui.qApp.db
        tableEsklp_Smnn = db.table('esklp.Smnn')
        tableNC = db.table('rbNomenclature')
        tableESKLP_Klp = db.table('esklp.Klp')
        tableLfForm= db.table('rbLfForm')
        tableEsklp_SmnnGrlsLf = db.table('esklp.Smnn_GrlsLf')
        queryTable = tableNC.innerJoin(tableESKLP_Klp, tableESKLP_Klp['UUID'].eq(tableNC['esklpUUID']))
        queryTable = queryTable.innerJoin(tableEsklp_Smnn, tableEsklp_Smnn['id'].eq(tableESKLP_Klp['smnn_id']))
        queryTable = queryTable.innerJoin(tableEsklp_SmnnGrlsLf, tableEsklp_SmnnGrlsLf['master_id'].eq(tableEsklp_Smnn['id']))
        queryTable = queryTable.innerJoin(tableLfForm, db.joinAnd([tableLfForm['name'].eq(tableEsklp_SmnnGrlsLf['lf_name']), tableLfForm['dosage'].eq(tableEsklp_SmnnGrlsLf['dosage_name'])]))
        cond = [tableEsklp_Smnn['UUID'].eq(smnnUUID),
                tableLfForm['id'].eq(lfFormId),
                tableLfForm['name'].eq(tableESKLP_Klp['lf_norm_name']),
                tableLfForm['dosage'].eq(tableESKLP_Klp['dosage_norm_name'])
                ]
        record = db.getRecordEx(queryTable, [tableNC['id']], cond, order = tableNC['name'].name())
        return forceRef(record.value('id')) if record else None
    return None


def getNomenclatureSmnnIdList(smnnUUID, lfFormId, nomenclatureIdList=[]):
    if trim(smnnUUID) and lfFormId:
        db = QtGui.qApp.db
        tableEsklp_Smnn = db.table('esklp.Smnn')
        tableNC = db.table('rbNomenclature')
        tableESKLP_Klp = db.table('esklp.Klp')
        tableLfForm= db.table('rbLfForm')
        tableEsklp_SmnnGrlsLf = db.table('esklp.Smnn_GrlsLf')
        queryTable = tableNC.innerJoin(tableESKLP_Klp, tableESKLP_Klp['UUID'].eq(tableNC['esklpUUID']))
        queryTable = queryTable.innerJoin(tableEsklp_Smnn, tableEsklp_Smnn['id'].eq(tableESKLP_Klp['smnn_id']))
        queryTable = queryTable.innerJoin(tableEsklp_SmnnGrlsLf, tableEsklp_SmnnGrlsLf['master_id'].eq(tableEsklp_Smnn['id']))
        queryTable = queryTable.innerJoin(tableLfForm, db.joinAnd([tableLfForm['name'].eq(tableEsklp_SmnnGrlsLf['lf_name']), tableLfForm['dosage'].eq(tableEsklp_SmnnGrlsLf['dosage_name'])]))
        cond = [tableEsklp_Smnn['UUID'].eq(smnnUUID),
                tableLfForm['id'].eq(lfFormId),
                tableLfForm['name'].eq(tableESKLP_Klp['lf_norm_name']),
                tableLfForm['dosage'].eq(tableESKLP_Klp['dosage_norm_name'])
                ]
        if nomenclatureIdList:
            cond.append(tableNC['id'].inlist(nomenclatureIdList))
        return db.getDistinctIdList(queryTable, [tableNC['id']], cond, order = tableNC['name'].name())
    return []


def getNomenclatureSmnnToLfFormIdList(smnnUUID, lfFormIdList, nomenclatureIdList=[]):
    if trim(smnnUUID) and lfFormIdList:
        db = QtGui.qApp.db
        tableEsklp_Smnn = db.table('esklp.Smnn')
        tableNC = db.table('rbNomenclature')
        tableESKLP_Klp = db.table('esklp.Klp')
        tableLfForm= db.table('rbLfForm')
        tableEsklp_SmnnGrlsLf = db.table('esklp.Smnn_GrlsLf')
        queryTable = tableNC.innerJoin(tableESKLP_Klp, tableESKLP_Klp['UUID'].eq(tableNC['esklpUUID']))
        queryTable = queryTable.innerJoin(tableEsklp_Smnn, tableEsklp_Smnn['id'].eq(tableESKLP_Klp['smnn_id']))
        queryTable = queryTable.innerJoin(tableEsklp_SmnnGrlsLf, tableEsklp_SmnnGrlsLf['master_id'].eq(tableEsklp_Smnn['id']))
        queryTable = queryTable.innerJoin(tableLfForm, db.joinAnd([tableLfForm['name'].eq(tableEsklp_SmnnGrlsLf['lf_name']), tableLfForm['dosage'].eq(tableEsklp_SmnnGrlsLf['dosage_name'])]))
        cond = [tableEsklp_Smnn['UUID'].eq(smnnUUID),
                tableLfForm['id'].inlist(lfFormIdList),
                tableLfForm['name'].eq(tableESKLP_Klp['lf_norm_name']),
                tableLfForm['dosage'].eq(tableESKLP_Klp['dosage_norm_name'])
                ]
        if nomenclatureIdList:
            cond.append(tableNC['id'].inlist(nomenclatureIdList))
        return db.getDistinctIdList(queryTable, [tableNC['id']], cond, order = tableNC['name'].name())
    return []

def getNomenclatureSmnnNotLfFormIdList(smnnUUID, nomenclatureIdList=[]):
    if trim(smnnUUID):
        db = QtGui.qApp.db
        tableEsklp_Smnn = db.table('esklp.Smnn')
        tableNC = db.table('rbNomenclature')
        tableESKLP_Klp = db.table('esklp.Klp')
        tableLfForm= db.table('rbLfForm')
        tableEsklp_SmnnGrlsLf = db.table('esklp.Smnn_GrlsLf')
        queryTable = tableNC.innerJoin(tableESKLP_Klp, tableESKLP_Klp['UUID'].eq(tableNC['esklpUUID']))
        queryTable = queryTable.innerJoin(tableEsklp_Smnn, tableEsklp_Smnn['id'].eq(tableESKLP_Klp['smnn_id']))
        queryTable = queryTable.innerJoin(tableEsklp_SmnnGrlsLf, tableEsklp_SmnnGrlsLf['master_id'].eq(tableEsklp_Smnn['id']))
        queryTable = queryTable.innerJoin(tableLfForm, db.joinAnd([tableLfForm['name'].eq(tableEsklp_SmnnGrlsLf['lf_name']), tableLfForm['dosage'].eq(tableEsklp_SmnnGrlsLf['dosage_name'])]))
        cond = [tableEsklp_Smnn['UUID'].eq(smnnUUID),
                tableLfForm['id'].isNull(),
                tableLfForm['name'].eq(tableESKLP_Klp['lf_norm_name']),
                tableLfForm['dosage'].eq(tableESKLP_Klp['dosage_norm_name'])
                ]
        if nomenclatureIdList:
            cond.append(tableNC['id'].inlist(nomenclatureIdList))
        return db.getDistinctIdList(queryTable, [tableNC['id']], cond, order = tableNC['name'].name())
    return []


def getNomenclatureIdSmnnLfFormIdList(nomenclatureId):
    nomenclatureIdSmnnLfFormIdList = []
    if nomenclatureId:
        db = QtGui.qApp.db
        tableEsklp_Smnn = db.table('esklp.Smnn')
        tableNC = db.table('rbNomenclature')
        tableESKLP_Klp = db.table('esklp.Klp')
        tableLfForm= db.table('rbLfForm')
        tableEsklp_SmnnGrlsLf = db.table('esklp.Smnn_GrlsLf')
        queryTable = tableNC.innerJoin(tableESKLP_Klp, tableESKLP_Klp['UUID'].eq(tableNC['esklpUUID']))
        queryTable = queryTable.innerJoin(tableEsklp_Smnn, tableEsklp_Smnn['id'].eq(tableESKLP_Klp['smnn_id']))
        queryTable = queryTable.innerJoin(tableEsklp_SmnnGrlsLf, tableEsklp_SmnnGrlsLf['master_id'].eq(tableEsklp_Smnn['id']))
        queryTable = queryTable.innerJoin(tableLfForm, db.joinAnd([tableLfForm['name'].eq(tableEsklp_SmnnGrlsLf['lf_name']), tableLfForm['dosage'].eq(tableEsklp_SmnnGrlsLf['dosage_name'])]))
        cols = [tableEsklp_Smnn['UUID'], 
                    tableLfForm['id'].alias('lfFormId')
                    ]
        cond = [tableLfForm['name'].eq(tableESKLP_Klp['lf_norm_name']),
                    tableLfForm['dosage'].eq(tableESKLP_Klp['dosage_norm_name']), 
                    tableNC['id'].eq(nomenclatureId)
                    ]
        records = db.getRecordList(queryTable, cols, cond, order = tableNC['name'].name())
        for record in records:
            smnnUUID = forceStringEx(record.value('UUID'))
            lfFormId = forceRef(record.value('lfFormId'))
            if (smnnUUID, lfFormId) not in nomenclatureIdSmnnLfFormIdList:
                nomenclatureIdSmnnLfFormIdList.append((smnnUUID, lfFormId))
    return nomenclatureIdSmnnLfFormIdList   


