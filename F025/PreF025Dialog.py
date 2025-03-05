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
##
## Планировщик формы 025: стат.талон и т.п.
##
#############################################################################

from PyQt4 import QtGui, QtSql
from PyQt4.QtCore import Qt, QEvent, QVariant, pyqtSignature, SIGNAL, QModelIndex

from library.crbcombobox        import CRBComboBox
from library.DialogBase         import CDialogBase
from library.InDocTable         import CInDocTableModel, CBoolInDocTableCol, CFloatInDocTableCol, CInDocTableCol, CIntInDocTableCol, CRBInDocTableCol
from library.PrintInfo          import CInfoContext, CDateInfo
from library.PrintTemplates     import applyTemplate, getPrintButton
from library.Utils              import calcAgeTuple, forceBool, forceDate, forceDouble, forceInt, forceRef, forceString, formatName, formatSex, toVariant

from Events.Action              import CActionTypeCache
from Events.ActionInfo          import CActionTypeInfo
from Events.ActionsSelector     import selectActionTypes
from Events.MapActionTypeToServiceIdList import CMapActionTypeIdToServiceIdList
from Events.Utils               import CFinanceType, recordAcceptable, getEventTypeForm, getEventName, getEventShowActionsInPlanner, getEventCanHavePayableActions, getEventFinanceCode, getEventPlannedInspections
from Orgs.PersonInfo            import CPersonInfo
from Registry.Utils             import CClientInfo
from library.SortFilterProxyInDocTableModel import CSortFilterProxyInDocTableModel

from F025.Ui_PreF025            import Ui_PreF025Dialog


class CPreF025DagnosticAndActionPresets:
    def __init__(self, clientId, eventTypeId, eventDate, specialityId, flagHospitalization, addActionTypeId, presentActionTypes = []):
        self.unconditionalDiagnosticList = []
        self.unconditionalActionList = []
        self.disabledActionTypeIdList = []
        self.setEventDate = None
        self.setClientInfo(clientId, eventDate)
        self.setEventTypeId(eventTypeId, specialityId, flagHospitalization, addActionTypeId, presentActionTypes = presentActionTypes)


    def setClientInfo(self, clientId, eventDate):
        self.clientId = clientId
        self.eventDate = eventDate
        db = QtGui.qApp.db
        table  = db.table('Client')
        record = db.getRecord(table, 'sex, birthDate', clientId)
        if record:
            self.clientSex       = forceInt(record.value('sex'))
            self.clientBirthDate = forceDate(record.value('birthDate'))
            self.clientAge       = calcAgeTuple(self.clientBirthDate, eventDate)
            if not self.clientAge:
                self.clientAge = (0, 0, 0, 0)


    def setBegDateEvent(self, date):
        self.setEventDate = date


    def setEventTypeId(self, eventTypeId, specialityId, flagHospitalization, addActionTypeId, presentActionTypes = []):
        self.eventTypeId = eventTypeId
        self.prepareDiagnositics(eventTypeId, specialityId)
        self.prepareActions(eventTypeId, specialityId, flagHospitalization, addActionTypeId, presentActionTypes = presentActionTypes)


    def prepareDiagnositics(self, eventTypeId, specialityId):
        records = getEventPlannedInspections(eventTypeId)
        for record in records:
            if (   specialityId is None
                or forceRef(record.value('speciality_id')) == specialityId
                or record.isNull('speciality_id')
               ):
                selectionGroup = forceInt(record.value('selectionGroup'))
                if selectionGroup == 1 and self.recordAcceptable(record):
                    MKB = forceString(record.value('defaultMKB'))
                    dispanserId = forceRef(record.value('defaultDispanser_id'))
                    healthGroupId = forceRef(record.value('defaultHealthGroup_id'))
                    visitTypeId = forceRef(record.value('visitType_id'))
                    self.unconditionalDiagnosticList.append((MKB, dispanserId, healthGroupId, visitTypeId))
                    break


    def prepareActions(self, eventTypeId, specialityId, flagHospitalization, addActionTypeId, presentActionTypes = []):
        wholeEventForCash = getEventFinanceCode(eventTypeId) == 4
        db = QtGui.qApp.db
        table = db.table('EventType_Action')
        tableActionType = db.table('ActionType')
        self.disabledActionTypeIdList = []
        join = table.leftJoin(tableActionType, tableActionType['id'].eq(table['actionType_id']))
        cond = [ table['eventType_id'].eq(eventTypeId), tableActionType['deleted'].eq(0) ]
        if specialityId:
            cond.append(db.joinOr( [ table['speciality_id'].eq(specialityId),  table['speciality_id'].isNull()] ))
        if presentActionTypes:
            cond.append('''(IF(selectionGroup=1 and ActionType.id in ({}), False, True))'''.format(', '.join(presentActionTypes)))
        records = QtGui.qApp.db.getRecordList(join, 'EventType_Action.*', cond, 'ActionType.class, idx, id')
        for record in records:
            actionTypeId = forceRef(record.value('actionType_id'))
            if actionTypeId and self.recordAcceptable(record):
                selectionGroup = forceInt(record.value('selectionGroup'))
                if selectionGroup == -99:
                    self.disabledActionTypeIdList.append(actionTypeId)
                elif selectionGroup == 1 or flagHospitalization and addActionTypeId == actionTypeId:
                    payable = forceInt(record.value('payable'))
                    self.unconditionalActionList.append((actionTypeId, 1.0, payable or wholeEventForCash))


    def recordAcceptable(self, record):
        return recordAcceptable(self.clientSex, self.clientAge, record, self.setEventDate, self.clientBirthDate)


class CPreF025Dialog(CDialogBase, Ui_PreF025Dialog, CMapActionTypeIdToServiceIdList):
    def __init__(self, parent, contractTariffCache=None):
        CDialogBase.__init__(self,  parent)
        CMapActionTypeIdToServiceIdList.__init__(self)
        self.addModels('Diagnostics', CDiagnosticsModel(self))
        self.addModels('Actions', CActionsModel(self))
        self.__modelSortActions = CSortFilterProxyInDocTableModel(self, self.modelActions)
        self.__modelSortActions.setObjectName('__modelSortActions')
        self.modelActions = self.__modelSortActions.sourceModel()

        self.addObject('btnPrint', getPrintButton(self, 'planner'))

        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setWindowTitleEx(u'Планирование осмотра Ф.025')
        self.clientId        = None
        self.clientName      = None
        self.clientSex       = None
        self.clientBirthDate = None
        self.clientAge       = None
        self.eventTypeId     = None
        self.setEventDate    = None
        self.eventDate       = None
        self.contractId      = None
        self.financeId       = None
        self.tariffCategoryId= None
        self.personId        = None
        self.showPrice       = False
        self.tissueTypeId    = None
        self.eventTypeForm   = u''
        self.preSpecialityIdList = []
        self.isSelectionGroupOne = False
        self.contractTariffCache = contractTariffCache
        self.tblDiagnostics.setModel(self.modelDiagnostics)
        self.tblDiagnostics.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.tblDiagnostics.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.tblActions.setModel(self.__modelSortActions)
        self.tblActions.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.tblActions.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)

        self.unconditionalDiagnosticList = []
        self.disabledActionTypeIdList = []
        self.unconditionalActionTypeIdList = []
        self.applicableActionTypeIdList = []  # это список всех actionTypeId в "правильном" порядке
                                              # потребность в этом списке обусловлена желанием
                                              # получить список в определённом порядке
                                              # и наличием двух независимых списков -
                                              # unconditionalActionTypeIdList и выбор оператора
        self.buttonBox.addButton(self.btnPrint, QtGui.QDialogButtonBox.ActionRole)
        self.tblDiagnostics.installEventFilter(self)
        self.tblActions.installEventFilter(self)


    def destroy(self):
        self.tblDiagnostics.setModel(None)
        self.tblActions.setModel(None)
        del self.modelDiagnostics
        del self.modelActions


    def setBegDateEvent(self, date):
        self.setEventDate = date


    def prepare(self, clientId, eventTypeId, eventDate, personId, specialityId, tariffCategoryId,
                flagHospitalization = False, addActionTypeId = None, tissueTypeId=None, typeQueue = -1,
                docNum=None, relegateInfo=[], plannedEndDate = None, mapJournalInfoTransfer = [], voucherParams = {}, eventId = None,
                presentActionTypes = []):
        self.showPrice = getEventCanHavePayableActions(eventTypeId)
        self.wholeEventForCash = getEventFinanceCode(eventTypeId) == 4
        self.personId = personId
        self.setClientInfo(clientId, eventDate)
        self.tissueTypeId = tissueTypeId
        if self.showPrice:
            self.modelDiagnostics.addPriceAndSumColumn()
            self.modelActions.addPriceAndSumColumn()
            self.setDefaultCash()
            self.grpContract.setVisible(True)
            self.tariffCategoryId = tariffCategoryId
            self.setEventTypeId(eventTypeId, specialityId, flagHospitalization, addActionTypeId, presentActionTypes = presentActionTypes)
            orgId = QtGui.qApp.currentOrgId()
            self.cmbContract.setOrgId(orgId)
            self.cmbContract.setEventTypeId(eventTypeId)
            self.cmbContract.setClientInfo(clientId, self.clientSex, self.clientAge, None, None)
            self.cmbContract.setFinanceId(CFinanceType.getId(CFinanceType.cash))
            self.cmbContract.setDate(eventDate)
            self.cmbContract.setCurrentIndex(0)
        else:
            self.grpContract.setVisible(False)
            self.setEventTypeId(eventTypeId, specialityId, flagHospitalization, addActionTypeId, eventId, presentActionTypes = presentActionTypes)


    def setClientInfo(self, clientId, eventDate):
        self.clientId = clientId
        self.eventDate = eventDate
        db = QtGui.qApp.db
        table  = db.table('Client')
        record = db.getRecord(table, 'lastName, firstName, patrName, sex, birthDate', clientId)
        if record:
            lastName  = record.value('lastName')
            firstName = record.value('firstName')
            partName  = record.value('patrName')
            self.clientName      = formatName(lastName, firstName, partName)
            self.clientSex       = forceInt(record.value('sex'))
            self.clientBirthDate = forceDate(record.value('birthDate'))
            self.clientAge       = calcAgeTuple(self.clientBirthDate, eventDate)
            if not self.clientAge:
                self.clientAge = (0, 0, 0, 0)


    def setEventTypeId(self, eventTypeId, specialityId, flagHospitalization, addActionTypeId, eventId = None, presentActionTypes = []):
        self.eventTypeId = eventTypeId
        eventTypeName  = getEventName(eventTypeId)
        self.eventTypeForm = getEventTypeForm(eventTypeId)
        self.modelDiagnostics.setEventTypeForm(self.eventTypeForm)
        showFlags = getEventShowActionsInPlanner(eventTypeId)
        title = u'Планирование: %s, Пациент: %s, Пол: %s, ДР.: %s '% (eventTypeName, self.clientName, formatSex(self.clientSex), forceString(self.clientBirthDate))
        QtGui.QDialog.setWindowTitle(self, title)
        if self.eventTypeForm == '090':
            self.modelDiagnostics._cols[2].setDefaultHidden(False)
            self.tblDiagnostics.horizontalHeader().setSectionHidden(1, False)
        else:
            self.modelDiagnostics._cols[2].setDefaultHidden(True)
            self.tblDiagnostics.horizontalHeader().setSectionHidden(1, True)
        self.prepareDiagnositics(eventTypeId, specialityId)
        self.prepareActions(eventTypeId, specialityId, showFlags, flagHospitalization, addActionTypeId, eventId, presentActionTypes)


    def prepareDiagnositics(self, eventTypeId, specialityId):
        includedGroups = set()
        self.preSpecialityIdList = []
        self.isSelectionGroupOne = False
        records = getEventPlannedInspections(eventTypeId)
        gpSpecialityId = QtGui.qApp.getGPSpecialityId()
        if self.eventTypeForm == '090' and self.personId:
            selectionGroupCnt = 0
            for record in records:
                selectionGroup = forceInt(record.value('selectionGroup'))
                recSpecialityId = forceRef(record.value('speciality_id'))
                if selectionGroup == 1:
                    selectionGroupCnt += 1
                if recSpecialityId and recSpecialityId not in self.preSpecialityIdList:
                    self.preSpecialityIdList.append(recSpecialityId)
                elif specialityId and specialityId not in self.preSpecialityIdList and not recSpecialityId:
                    self.preSpecialityIdList.append(specialityId)
            recordCount = len(records) if records else 0
            db = QtGui.qApp.db
            tablePerson = db.table('Person')
            personRecord = db.getRecordEx(tablePerson, [tablePerson['post_id']], [tablePerson['id'].eq(self.personId), tablePerson['deleted'].eq(0)])
            postId = forceRef(personRecord.value('post_id')) if personRecord else None
            for record in records:
                selectionGroup = forceInt(record.value('selectionGroup'))
                recSpecialityId = forceRef(record.value('speciality_id'))
                recPostId = forceRef(record.value('post_id'))
                if (recordCount == 1 or selectionGroupCnt == 1) and selectionGroup == 1:
                    MKB = forceString(record.value('defaultMKB'))
                    dispanserId = forceRef(record.value('defaultDispanser_id'))
                    healthGroupId = forceRef(record.value('defaultHealthGroup_id'))
                    visitTypeId = forceRef(record.value('visitType_id'))
                    self.isSelectionGroupOne = forceBool(recSpecialityId)
                    self.unconditionalDiagnosticList.append((MKB, dispanserId, healthGroupId, visitTypeId))
                    item = self.modelDiagnostics.getEmptyRecord()
                    item.setValue('speciality_id', toVariant(recSpecialityId if recSpecialityId else specialityId))
                    item.setValue('post_id', toVariant(recPostId if recPostId else postId))
                    item.setValue('person_id', toVariant(self.personId if (recSpecialityId == specialityId or not recSpecialityId) else None))
                    item.setValue('defaultMKB', toVariant(MKB))
                    item.setValue('defaultDispanser_id', toVariant(dispanserId))
                    item.setValue('defaulthealthGroup_id', toVariant(healthGroupId))
                    item.setValue('visitType_id', toVariant(visitTypeId))
                    item.setValue('selectionGroup', record.value('selectionGroup'))
                    if selectionGroup <= 0 or selectionGroup in includedGroups:
                        item.setValue('include', QVariant(0))
                    elif selectionGroup != 1:
                        item.setValue('include', QVariant(1))
                        includedGroups.add(selectionGroup)
                    item.setValue('price', QVariant(0.0))
                    self.modelDiagnostics.items().append(item)
                    break
                else:
                    mayEngageGP = forceBool(record.value('mayEngageGP'))
                    if selectionGroup == 1 and ((specialityId is None and postId is None)
                        or (recSpecialityId is None and recPostId is None) or (specialityId and (recSpecialityId == specialityId
                        or (mayEngageGP and specialityId == gpSpecialityId)))
                        or (recSpecialityId is None and postId and recPostId == postId)) and self.recordAcceptable(record):
                        MKB = forceString(record.value('defaultMKB'))
                        dispanserId = forceRef(record.value('defaultDispanser_id'))
                        healthGroupId = forceRef(record.value('defaultHealthGroup_id'))
                        visitTypeId = forceRef(record.value('visitType_id'))
                        self.unconditionalDiagnosticList.append((MKB, dispanserId, healthGroupId, visitTypeId))
                        item = self.modelDiagnostics.getEmptyRecord()
                        item.setValue('speciality_id', toVariant(recSpecialityId if recSpecialityId else specialityId))
                        item.setValue('post_id', toVariant(recPostId if recPostId else postId))
                        item.setValue('person_id', toVariant(self.personId if (recSpecialityId == specialityId or not recSpecialityId) else None))
                        item.setValue('defaultMKB', toVariant(MKB))
                        item.setValue('defaultDispanser_id', toVariant(dispanserId))
                        item.setValue('defaulthealthGroup_id', toVariant(healthGroupId))
                        item.setValue('visitType_id', toVariant(visitTypeId))
                        item.setValue('selectionGroup', record.value('selectionGroup'))
                        if selectionGroup <= 0 or selectionGroup in includedGroups:
                            item.setValue('include', QVariant(0))
                        elif selectionGroup != 1:
                            item.setValue('include', QVariant(1))
                            includedGroups.add(selectionGroup)
                        item.setValue('price', QVariant(0.0))
                        self.modelDiagnostics.items().append(item)
                        break
            if len(self.modelDiagnostics.items()) == 0 and selectionGroupCnt > 1:
                for record in records:
                    selectionGroup = forceInt(record.value('selectionGroup'))
                    recSpecialityId = forceRef(record.value('speciality_id'))
                    recPostId = forceRef(record.value('post_id'))
                    if selectionGroup == 1 and self.recordAcceptable(record):
                        MKB = forceString(record.value('defaultMKB'))
                        dispanserId = forceRef(record.value('defaultDispanser_id'))
                        healthGroupId = forceRef(record.value('defaultHealthGroup_id'))
                        visitTypeId = forceRef(record.value('visitType_id'))
                        self.unconditionalDiagnosticList.append(
                            (MKB, dispanserId, healthGroupId, visitTypeId))
                        item = self.modelDiagnostics.getEmptyRecord()
                        item.setValue('speciality_id',         toVariant(recSpecialityId if recSpecialityId == specialityId else (specialityId if not recSpecialityId else None)))
                        item.setValue('post_id', toVariant(recPostId if recPostId else postId))
                        item.setValue('person_id',             toVariant(self.personId if recSpecialityId == specialityId else None))
                        item.setValue('defaultMKB', toVariant(MKB))
                        item.setValue('defaultDispanser_id', toVariant(dispanserId))
                        item.setValue('defaulthealthGroup_id', toVariant(healthGroupId))
                        item.setValue('visitType_id', toVariant(visitTypeId))
                        item.setValue('selectionGroup', record.value('selectionGroup'))
                        if selectionGroup <= 0 or selectionGroup in includedGroups:
                            item.setValue('include', QVariant(0))
                        elif selectionGroup != 1:
                            item.setValue('include', QVariant(1))
                            includedGroups.add(selectionGroup)
                        item.setValue('price', QVariant(0.0))
                        self.modelDiagnostics.items().append(item)
                        break
        else:
            for record in records:
                recSpecialityId = forceRef(record.value('speciality_id'))
                selectionGroup = forceInt(record.value('selectionGroup'))
                mayEngageGP    = forceBool(record.value('mayEngageGP'))
                if (   specialityId is None
                    or recSpecialityId == specialityId
                    or (mayEngageGP and specialityId == gpSpecialityId)
                    or recSpecialityId is None
                    or selectionGroup == 0
                   ) and self.recordAcceptable(record):
                    MKB = forceString(record.value('defaultMKB'))
                    dispanserId = forceRef(record.value('defaultDispanser_id'))
                    healthGroupId = forceRef(record.value('defaultHealthGroup_id'))
                    visitTypeId = forceRef(record.value('visitType_id'))
                    if selectionGroup == 1:
                        self.unconditionalDiagnosticList.append((MKB, dispanserId, healthGroupId, visitTypeId))
                        break
                    else:
                        item = self.modelDiagnostics.getEmptyRecord()
                        item.setValue('speciality_id',         toVariant(recSpecialityId))
                        item.setValue('defaultMKB',            toVariant(MKB))
                        item.setValue('defaultDispanser_id',   toVariant(dispanserId))
                        item.setValue('defaulthealthGroup_id', toVariant(healthGroupId))
                        item.setValue('visitType_id',          toVariant(visitTypeId))
                        item.setValue('selectionGroup',        record.value('selectionGroup'))
                        if selectionGroup <= 0 or selectionGroup in includedGroups:
                            item.setValue('include',  QVariant(0))
                        else:
                            item.setValue('include',  QVariant(1))
                            includedGroups.add(selectionGroup)
                        item.setValue('price', QVariant(0.0))
                        if specialityId and (recSpecialityId == specialityId):
                            item.setValue('include',  QVariant(1))
                        self.modelDiagnostics.items().append(item)
        self.modelDiagnostics.reset()


    def prepareActions(self, eventTypeId, specialityId, showFlags, flagHospitalization, addActionTypeId, eventId = None, presentActionTypes = []):
        includedGroups = set()
        db = QtGui.qApp.db

        self.disabledActionTypeIdList = []

        if specialityId:
            speciality = '''AND (((EventType_Action.`speciality_id` = %s) OR (EventType_Action.`speciality_id` IS NULL)))''' %specialityId
        else:
            speciality = ''
        
        if presentActionTypes:
            presentAction = '''AND (IF(selectionGroup=1 and ActionType.id in ({}), False, True))'''.format(', '.join(presentActionTypes))
        else:
            presentAction = ''

        if eventId:
            event = '''(SELECT 1 FROM Event e LEFT JOIN Action a ON e.id = a.event_id 
  WHERE EventType_Action.selectionGroup=1 AND a.actionType_id=ActionType.id AND e.deleted=0 AND a.deleted=0 AND e.id = %s
   HAVING (COUNT(a.id) >= maxOccursInEvent) AND maxOccursInEvent != 0
  )  AS test''' % eventId
            having = '''HAVING test IS NULL'''
        else:
            event = '1'
            having = ''

        stmt = '''SELECT
  EventType_Action.*,
%(event)s

FROM EventType_Action
  LEFT JOIN ActionType
    ON ActionType.`id` = EventType_Action.`actionType_id`
WHERE (EventType_Action.`eventType_id` = %(eventTypeId)s)
AND (ActionType.`deleted` = 0)

%(speciality)s

%(presentAction)s

%(having)s

ORDER BY ActionType.class, idx, id'''% {'event': event,
                  'having': having,
                  'eventTypeId': eventTypeId,
                  'speciality': speciality,
                  'presentAction': presentAction,
                  }

        db = QtGui.qApp.db
        query = db.query(stmt)
        records = []
        while query.next():
            records.append(query.record())


        for record in records:
            actionTypeId = forceRef(record.value('actionType_id'))
            actionType = CActionTypeCache.getById(actionTypeId)
            if self.wholeEventForCash:
                payable = 2
            elif not self.showPrice:
                payable = 0
            else:
                payable = forceInt(record.value('payable'))

            if actionType and self.recordAcceptable(record):
                tissueTypeId = forceRef(record.value('tissueType_id'))
                if tissueTypeId and self.tissueTypeId:
                    if self.tissueTypeId != tissueTypeId:
                        continue
                selectionGroup = forceInt(record.value('selectionGroup'))
                if selectionGroup == -99:
                    self.disabledActionTypeIdList.append(actionTypeId)
                elif selectionGroup == 1 and not payable:
                    self.unconditionalActionTypeIdList.append(actionTypeId)
                    self.applicableActionTypeIdList.append(actionTypeId)
                else:
                    if selectionGroup > 1 or showFlags[actionType.class_] or payable:
                        item = self.modelActions.getEmptyRecord()
                        item.setValue('actionType_id',  toVariant(actionTypeId))
                        item.setValue('actuality',      record.value('actuality'))
                        item.setValue('selectionGroup', record.value('selectionGroup'))
                        if selectionGroup <= 0 or selectionGroup in includedGroups:
                            item.setValue('include',  QVariant(0))
                        else:
                            item.setValue('include',  QVariant(1))
                            if selectionGroup != 1:
                                includedGroups.add(selectionGroup)
                        item.setValue('cash', QVariant(self.wholeEventForCash or payable == 2))
                        item.setValue('price', QVariant(0.0))
                        item.setValue('payable', QVariant(payable))
                        self.modelActions.items().append(item)
                    self.applicableActionTypeIdList.append(actionTypeId)
        if flagHospitalization and addActionTypeId:
            actionTypeId = addActionTypeId
            actionType = CActionTypeCache.getById(actionTypeId)
            if actionType:
                if actionTypeId not in self.unconditionalActionTypeIdList:
                    self.unconditionalActionTypeIdList.append(actionTypeId)
                if actionTypeId not in self.applicableActionTypeIdList:
                    self.applicableActionTypeIdList.append(actionTypeId)
        self.modelActions.reset()


    def getEventTypeId(self):
        return self.eventTypeId


    def recordAcceptable(self, record):
        return recordAcceptable(self.clientSex, self.clientAge, record, self.setEventDate, self.clientBirthDate)


    def setDefaultCash(self):
        self.modelDiagnostics.setDefaultCash(self.wholeEventForCash)
        self.modelActions.setDefaultCash(self.wholeEventForCash)


    def updatePrices(self):
        visitTariffMap, actionTariffMap = self.getTariffMap()
        self.updateVisitPrices(visitTariffMap)
        self.updateActionPrices(actionTariffMap)
        self.updateTotalSum()


    def getTariffMap(self):
        if self.contractTariffCache and self.contractId:
            tariffDescr = self.contractTariffCache.getTariffDescr(self.contractId, self)
            return tariffDescr.visitTariffMap, tariffDescr.actionTariffMap
        return {}, {}


    def updateVisitPrices(self, tariffMap):
        for i, item in enumerate(self.modelDiagnostics.items()):
            self.modelDiagnostics.setPrice(i, 0)


    def updateActionPrices(self, tariffMap):
        for i, item in enumerate(self.modelActions.items()):
            actionTypeId = forceRef(item.value('actionType_id'))
            if actionTypeId:
                serviceIdList = self.getActionTypeServiceIdList(actionTypeId, self.financeId)
                price = self.contractTariffCache.getPrice(tariffMap, serviceIdList, self.tariffCategoryId)
            else:
                price = ''
            self.modelActions.setPrice(i, price)


    def updateTotalSum(self):
        s = 0.0
        for item in self.modelDiagnostics.items():
            if forceBool(item.value('include')) and forceBool(item.value('cash')):
                s += forceDouble(item.value('sum'))
        for item in self.modelActions.items():
            if forceBool(item.value('include')) and forceBool(item.value('cash')):
                s += forceDouble(item.value('sum'))
        self.lblSumValue.setText('%.2f'%s)


    def diagnosticsTableIsNotEmpty(self):
        return bool(self.modelDiagnostics.items())


    def actionsTableIsNotEmpty(self):
        return bool(self.modelActions.items())


    def diagnostics(self):
        result = self.unconditionalDiagnosticList
        for item in self.modelDiagnostics.items():
            if forceBool(item.value('include')):
                MKB = forceString(item.value('defaultMKB'))
                dispanserId   = forceRef(item.value('defaultDispanser_id'))
                healthGroupId = forceRef(item.value('defaultHealthGroup_id'))
                visitTypeId   = forceRef(item.value('visitType_id'))
                diagnostic = (MKB, dispanserId, healthGroupId, visitTypeId)
                if diagnostic not in result:
                    result.append(diagnostic)
        return result


    def actions(self):
        selected = set([])
        deselected = set([])
        sets = (deselected, selected)
        amounts = {}
        forCash = set([])
        for item in self.modelActions.items():
            actionTypeId = forceRef(item.value('actionType_id'))
            sets[forceBool(item.value('include'))].add(actionTypeId)
            amount = forceDouble(item.value('amount'))
            if amount:
                amounts[actionTypeId] = amount
            cash = forceBool(item.value('cash'))
            if cash:
                forCash.add(actionTypeId)
        requested = (set(self.unconditionalActionTypeIdList) - deselected) | selected
        result = [ (actionTypeId, amounts.get(actionTypeId, 1.0), actionTypeId in forCash)
                   for actionTypeId in self.applicableActionTypeIdList
                   if actionTypeId in requested ]
        return result


    def selectAll(self, model, newState):
        for i, item in enumerate(model.items()):
            selectionGroup = forceInt(item.value('selectionGroup'))
            if selectionGroup == 0:
                item.setValue('include', QVariant(newState))
        model.reset()
        self.updateTotalSum()


    def addActionType(self, actionTypeId):
        model = self.modelActions
        item = model.getEmptyRecord()
        item.setValue('actionType_id',  toVariant(actionTypeId))
        item.setValue('selectionGroup', toVariant(0))
        item.setValue('include',  QVariant(1))
        if self.showPrice:
            item.setValue('cash', QVariant(self.wholeEventForCash or bool(self.contractId)))
            item.setValue('payable', 2 if self.wholeEventForCash else 1 if self.contractId else 0)
            serviceIdList = self.getActionTypeServiceIdList(actionTypeId, self.financeId)
            visitTariffMap, actionTariffMap = self.getTariffMap()
            price = self.contractTariffCache.getPrice(actionTariffMap, serviceIdList, self.tariffCategoryId)
            item.setValue('price',  QVariant(price))
            item.setValue('amount', QVariant(1.0))
            item.setValue('sum',    QVariant(price))
        model.items().append(item)
        count = len(model.items())
        model.beginInsertRows(QModelIndex(), count, count)
        model.insertRows(count, 1)
        model.endInsertRows()
        self.applicableActionTypeIdList.append(actionTypeId)


    def eventFilter(self, watched, event):
        if watched == self.tblDiagnostics or watched == self.tblActions:
            if (    event.type() == QEvent.KeyPress
                and event.key() in (Qt.Key_Up, Qt.Key_Down)
                and event.modifiers() & Qt.ControlModifier
               ):
                    event.accept()
                    self.moveSelectionToNextIncluded(watched, event.key() == Qt.Key_Up)
                    return True
        return CDialogBase.eventFilter(self, watched, event)


    def moveSelectionToNextIncluded(self, tblWidget, moveUp):
        index = tblWidget.currentIndex()
        row = index.row()
        row = tblWidget.model().getNextIncludedRow(row, moveUp)
        tblWidget.setCurrentIndex(index.sibling(row, index.column()))


    @pyqtSignature('')
    def on_cmbContract_valueChanged(self):
        self.contractId = self.cmbContract.value()
        self.financeId  = forceRef(QtGui.qApp.db.translate('Contract', 'id', self.contractId, 'finance_id'))
        self.updatePrices()


    @pyqtSignature('')
    def on_modelDiagnostics_sumChanged(self):
        if self.showPrice:
            self.updateTotalSum()


    @pyqtSignature('')
    def on_modelActions_sumChanged(self):
        if self.showPrice:
            self.updateTotalSum()


    @pyqtSignature('')
    def on_btnSelectVisits_clicked(self):
        self.selectAll(self.modelDiagnostics, 1)


    @pyqtSignature('')
    def on_btnDeselectVisits_clicked(self):
        self.selectAll(self.modelDiagnostics, 0)


    @pyqtSignature('')
    def on_btnSelectActions_clicked(self):
        self.selectAll(self.modelActions, 1)


    @pyqtSignature('')
    def on_btnDeselectActions_clicked(self):
        self.selectAll(self.modelActions, 0)


    def getSelectedActionTypeIdList(self):
        selectedActionTypeIdList = []
        items = self.modelActions.items()
        for item in items:
            if forceBool(item.value('include')):
                actionTypeId = forceRef(item.value('actionType_id'))
                if actionTypeId and actionTypeId not in selectedActionTypeIdList:
                    selectedActionTypeIdList.append(actionTypeId)
        return selectedActionTypeIdList


    @pyqtSignature('')
    def on_btnAddActionTypes_clicked(self):
        actionTypeIdList = selectActionTypes(self, self,
                          [0, 1, 2, 3],
                          orgStructureId=None,
                          # execPersonId=self.personId,
                          eventTypeId=self.eventTypeId,
                          contractId=self.contractId,
                          mesId=None,
                          visibleTblSelected=False,
                          preActionTypeIdList=self.getSelectedActionTypeIdList())
        for actionTypeId in actionTypeIdList:
            if not (actionTypeId in self.disabledActionTypeIdList):
                row = self.modelActions.actionTypePresent(actionTypeId)
                if row is not None:
                    self.modelActions.items()[row].setValue('include',  QVariant(1))
                else:
                    self.addActionType(actionTypeId)
        if actionTypeIdList:
            self.modelActions.reset()
            if self.showPrice:
                self.updateTotalSum()


    @pyqtSignature('int')
    def on_btnPrint_printByTemplate(self, templateId):
        context = CInfoContext()
        data = { 'client' : context.getInstance(CClientInfo, self.clientId),
                 'date'   : CDateInfo(self.eventDate),
                 'person' : context.getInstance(CPersonInfo, self.personId),
                 'visits' : [],
                 'actions': self.modelActions.getInfoList(context)
               }
        applyTemplate(self, templateId, data)


    @pyqtSignature('QString')
    def on_edtNameFilter_textChanged(self, text):
        self.__modelSortActions.setNameFilter(unicode(text))


class CPreModel(CInDocTableModel):
    __pyqtSignals__ = ('sumChanged()',
                      )

    def __init__(self, *args, **kwargs):
        CInDocTableModel.__init__(self, *args, **kwargs)
        self.wholeEventForCash = False


    def getEmptyRecord(self):
        result = CInDocTableModel.getEmptyRecord(self)
        result.append(QtSql.QSqlField('payable', QVariant.Int))
        result.setValue('amount', QVariant(1.0))
        result.setValue('cash', QVariant(self.wholeEventForCash))
        return result

    def flags(self, index):
        row = index.row()
        column = index.column()
        if column == self.ciCash:
            payable = forceInt(self.items()[row].value('payable'))
            if self.wholeEventForCash or payable == 2:
                return Qt.ItemIsSelectable | Qt.ItemIsUserCheckable
            elif payable == 0:
                return Qt.ItemIsSelectable
        return CInDocTableModel.flags(self, index)


    def data(self, index, role):
        if role == Qt.CheckStateRole and index.column() == self.ciCash:
            row = index.row()
            payable = forceInt(self.items()[row].value('payable'))
            if payable == 0:
                return QVariant()
        return CInDocTableModel.data(self, index, role)


    def setData(self, index, value, role=Qt.EditRole):
        column = index.column()
        row = index.row()
        if role == Qt.CheckStateRole:
            column = index.column()
            if column == 0:
                group = forceInt(self.items()[row].value('selectionGroup'))
                newState = 1 if forceInt(value) == Qt.Checked else 0
                if group>0:
                    newState = 1
                if group == 0:  # нулевая группа - всегда переключается
                    result = CInDocTableModel.setData(self, index, value, role)
                    self.emit(SIGNAL('sumChanged()'))
                    return result
                if group == 1:  # первая группа - никогда не переключается
                    return False
                for itemIndex, item in enumerate(self.items()):
                    itemGroup = forceInt(item.value('selectionGroup'))
                    if itemGroup == group:
                        item.setValue('include',  QVariant(newState if itemIndex == row else 0))
                        self.emitCellChanged(itemIndex, 0)
                self.emitColumnChanged(0)
                self.emit(SIGNAL('sumChanged()'))
                return True
            elif column == self.ciCash:
                payable = forceInt(self.items()[row].value('payable'))
                if payable == 1:
                    result = CInDocTableModel.setData(self, index, value, role)
                    self.emit(SIGNAL('sumChanged()'))
                    return result
                else:
                    return False
        result = CInDocTableModel.setData(self, index, value, role)
        if result and role==Qt.EditRole:
            if column == self.ciPrice or column == self.ciAmount:
                item = self.items()[row]
                price = forceDouble(item.value('price'))
                amount = forceDouble(item.value('amount'))
                sum = round(price*amount, 2)
                item.setValue('sum', toVariant(sum))
                self.emitCellChanged(row, column)
                self.emit(SIGNAL('sumChanged()'))
        return result


    def setDefaultCash(self, wholeEventForCash):
        self.wholeEventForCash = wholeEventForCash


    def setPrice(self, i, price):
        self.setData(self.index(i, self.ciPrice), toVariant(price), Qt.EditRole)


    def getNextIncludedRow(self, row, moveUp):
        items = self.items()
        step = -1 if moveUp else 1
        nextrow = row + step
        while 0<=nextrow<len(items):
            if forceBool(items[nextrow].value('include')):
                return nextrow
            nextrow += step
        return row


class CDiagnosticsModel(CPreModel):
    ciCash   = 7
    ciPrice  = 8
    ciAmount = 9
    ciSum    = 10

    def __init__(self, parent):
        CPreModel.__init__(self, 'EventType_Diagnostic', 'id', 'eventType_id', parent)
        self.addExtCol(CBoolInDocTableCol( u'Включить',       'include', 10), QVariant.Int)
        self.addCol(CRBInDocTableCol(      u'Специальность',  'speciality_id', 20, 'rbSpeciality')).setReadOnly()
        self.addCol(CRBInDocTableCol(      u'Должность',      'post_id', 10, 'rbPost', defaultHidden=True))
        self.addCol(CRBInDocTableCol(      u'Тип визита',     'visitType_id',  20, 'rbVisitType')).setReadOnly()
        self.addCol(CInDocTableCol(        u'МКБ',            'defaultMKB', 5)).setReadOnly()
        self.addCol(CRBInDocTableCol(      u'ДН',             'defaultDispanser_id',   20, 'rbDispanser', showFields=CRBComboBox.showCode)).setReadOnly()
        self.addCol(CRBInDocTableCol(      u'ГрЗд',           'defaultHealthGroup_id', 20, 'rbHealthGroup', showFields=CRBComboBox.showCode)).setReadOnly()
        self.addCol(CIntInDocTableCol(     u'Группа выбора',  'selectionGroup', 5)).setReadOnly()
        self.setEnableAppendLine(False)
        self.eventTypeForm = u''

    def addPriceAndSumColumn(self):
        self.addExtCol(CBoolInDocTableCol( u'Нал.', 'cash', 10), QVariant.Int)
        self.addExtCol(CFloatInDocTableCol(u'Цена', 'price', 7, precision=2), QVariant.Double).setReadOnly()
        self.addExtCol(CInDocTableCol(u'Кол-во', 'amount', 7, precision=2), QVariant.Double).setReadOnly(False)
        self.addExtCol(CFloatInDocTableCol(u'Сумма', 'sum', 7, precision=2), QVariant.Double).setReadOnly()
        if self.eventTypeForm == u'090':
            self.ciCash = 8
            self.ciPrice = 9
            self.ciAmount = 10
            self.ciSum = 11


    def setEventTypeForm(self, eventTypeForm):
        self.eventTypeForm = eventTypeForm


    def getEmptyRecord(self):
        result = CPreModel.getEmptyRecord(self)
        result.append(QtSql.QSqlField('person_id', QVariant.Int))
        result.setValue('person_id', toVariant(None))
        return result


class CActionsModel(CPreModel):
    ciCash   = 4
    ciPrice  = 5
    ciAmount = 6
    ciSum    = 7

    def __init__(self, parent):
        CPreModel.__init__(self, 'EventType_Action', 'id', 'eventType_id', parent)
        self.addExtCol(CBoolInDocTableCol( u'Включить',      'include', 10), QVariant.Int)
        self.addCol(CRBInDocTableCol(      u'Код',           'actionType_id',20, 'ActionType', showFields=CRBComboBox.showCode)).setReadOnly()
        self.addCol(CRBInDocTableCol(      u'Наименование',  'actionType_id',20, 'ActionType', showFields=CRBComboBox.showName)).setReadOnly()
        self.addCol(CIntInDocTableCol(     u'Группа выбора', 'selectionGroup', 5)).setReadOnly()
        self.setEnableAppendLine(False)


    def addPriceAndSumColumn(self):
        self.addExtCol(CBoolInDocTableCol( u'Нал.', 'cash', 10), QVariant.Int)
        self.addExtCol(CFloatInDocTableCol(u'Цена', 'price', 7, precision=2), QVariant.Double).setReadOnly()
        self.addExtCol(CInDocTableCol(u'Кол-во',    'amount', 7, precision=2), QVariant.Double).setReadOnly(False)
        self.addExtCol(CFloatInDocTableCol(u'Сумма','sum', 7, precision=2), QVariant.Double).setReadOnly()


    def getInfoList(self, context):
        result = []
        for item in self.items():
            include = forceBool(item.value('include'))
            cash    = forceBool(item.value('cash'))
            if include:
                actionTypeId = forceRef(item.value('actionType_id'))
                actionType = CActionTypeCache.getById(actionTypeId)
                actionTypeInfo = CActionTypeInfo(context, actionType)
                price = forceDouble(item.value('price'))
                actionTypeInfo.price = price
                amount = forceDouble(item.value('amount'))
                actionTypeInfo.amount = amount
                sum = forceDouble(item.value('sum'))
                actionTypeInfo.sum  = sum
                actionTypeInfo.cash = cash
                result.append(actionTypeInfo)
        return result


    def actionTypePresent(self, actionTypeId):
        for row, item in enumerate(self.items()):
            if actionTypeId == forceRef(item.value('actionType_id')):
                return row
        return None
