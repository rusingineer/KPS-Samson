# -*- coding: utf-8 -*-
#############################################################################
##
# Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
# Copyright (C) 2012-2025 SAMSON Group. All rights reserved.
##
#############################################################################
##
# Это программа является свободным программным обеспечением.
# Вы можете использовать, распространять и/или модифицировать её согласно
# условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################
from PyQt4 import QtGui, QtSql
from PyQt4.QtCore import Qt, QDate, pyqtSignature, QVariant, SIGNAL, QAbstractTableModel, QModelIndex

from Events.Action import CAction, CActionType, CActionTypeCache
from Events.ActionInfo import CActionInfoProxyList, CActionSelectedInfoProxyList
from Events.ActionPropertiesTable import InterpretationData, CActionPropertiesTableView
from Events.ActionStatus import CActionStatus
from Events.ActionTypeCol import CActionTypeCol
from Events.ActionsModel import CActionRecordItem
from Events.Utils import getDiagnosisId2, getDeathDate, setActionPropertiesColumnVisible, getActionTypeDescendants
from Orgs.PersonComboBoxEx import CPersonFindInDocTableCol
from Orgs.Utils import getOrgStructurePersonIdList, getPersonInfo
from Registry.ChangeDispanserBegDateLUD import CChangeDispanserBegDateLUD
from Registry.ProphylaxisPlanningInfo import CProphylaxisPlanningInfoProxyList, CProphylaxisPlanningInfoList
from Registry.Utils import CClientInfo, getClientPhone, updateDiagnosisRecords, createDiagnosticRecords
from Surveillance.ChangeDispanserPerson import CChangeDispanserPerson
from Surveillance.SurveillanceRemovedDialog import CSurveillanceRemovedDialog
from Surveillance.Ui_SurveillancePlanningEditDialog import Ui_SurveillancePlanningEditDialog
from Users.Rights import urCanUserRemoveDispanser
from library.Attach.AttachButton import CAttachButton
from library.DialogBase import CDialogBase
from library.ICDInDocTableCol import CICDExInDocTableCol
from library.ICDUtils import getMKBName
from library.InDocTable import (CDateInDocTableCol,
                                CInDocTableCol,
                                CRBInDocTableCol,
                                CInDocTableModel
                                )
from library.ItemsListDialog import CItemEditorBaseDialog
from library.PrintInfo import CInfoContext
from library.PrintTemplates import getPrintButton, applyTemplate
from library.TableModel import CTableModel, CBoolCol, CDateCol, CEnumCol, CRefBookCol, CTextCol
from library.Utils import forceDate, forceString, forceRef, forceStringEx, forceInt, forceBool, toVariant, \
    firstMonthDay, foldText, trim, conv_data, calcAgeTuple, formatDate
from library.crbcombobox import CRBModelDataCache
from library.database import CSqlRecord, CTableRecordCache


# Планирование Диспансерного наблюдения #CSurveillancePlanningEditDialog


class CSurveillancePlanningEditDialog(CItemEditorBaseDialog, Ui_SurveillancePlanningEditDialog):
    def __init__(self, parent):
        CItemEditorBaseDialog.__init__(self, parent, 'ProphylaxisPlanning')
        self.eventEditor = None
        self.eventRecord = None
        self.addModels('PlanningSurveillance', CPlanningSurveillanceModel(self))
        self.addModels('ControlSurveillance', CControlSurveillanceModel(self))
        self.addModels('MeasuresStatusActions', CMeasuresActionsCheckTableModel(self))
        self.addModels('MeasuresStatusActionProperties', CActionPropertiesTableModel(self))
        self.addModels('MeasuresDiagnosticActions', CMeasuresActionsCheckTableModel(self))
        self.addModels('MeasuresDiagnosticActionProperties', CActionPropertiesTableModel(self))
        self.addModels('MeasuresCureActions', CMeasuresActionsCheckTableModel(self))
        self.addModels('MeasuresCureActionProperties', CActionPropertiesTableModel(self))
        self.addModels('MeasuresMiscActions', CMeasuresActionsCheckTableModel(self))
        self.addModels('MeasuresMiscActionProperties', CActionPropertiesTableModel(self))
        self.addObject('btnApply', QtGui.QPushButton(u'Применить', self))
        self.addObject('btnPrint', getPrintButton(self, 'surveillancePlanningCard', u'Печать'))
        self.addObject('btnAttachedFiles', CAttachButton(self, u'Прикреплённые файлы'))
        self.btnAttachedFiles.setTable('ProphylaxisPlanning_FileAttach')
        self.addObject('btnSurveillanceRemoved', QtGui.QPushButton(u'Снять с ДН в МО', self))
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setWindowTitleEx(u'Диспансерное наблюдение')
        self.setWindowState(Qt.WindowMaximized)
        self.grpPlanningSurveillance.setStyleSheet('QGroupBox {font-weight: bold;}')
        self.grpControlSurveillance.setStyleSheet('QGroupBox {font-weight: bold;}')
        self.grpMeasuresSurveillance.setStyleSheet('QGroupBox {font-weight: bold;}')
        self.setModels(self.tblPlanningSurveillance, self.modelPlanningSurveillance, self.selectionModelPlanningSurveillance)
        self.setModels(self.tblControlSurveillance, self.modelControlSurveillance, self.selectionModelControlSurveillance)
        self.setModels(self.tblMeasuresStatusActions, self.modelMeasuresStatusActions, self.selectionModelMeasuresStatusActions)
        self.setModels(self.tblMeasuresStatusActionProperties, self.modelMeasuresStatusActionProperties, self.selectionModelMeasuresStatusActionProperties)
        self.setModels(self.tblMeasuresDiagnosticActions, self.modelMeasuresDiagnosticActions, self.selectionModelMeasuresDiagnosticActions)
        self.setModels(self.tblMeasuresDiagnosticActionProperties, self.modelMeasuresDiagnosticActionProperties, self.selectionModelMeasuresDiagnosticActionProperties)
        self.setModels(self.tblMeasuresCureActions, self.modelMeasuresCureActions, self.selectionModelMeasuresCureActions)
        self.setModels(self.tblMeasuresCureActionProperties, self.modelMeasuresCureActionProperties, self.selectionModelMeasuresCureActionProperties)
        self.setModels(self.tblMeasuresMiscActions, self.modelMeasuresMiscActions, self.selectionModelMeasuresMiscActions)
        self.setModels(self.tblMeasuresMiscActionProperties, self.modelMeasuresMiscActionProperties, self.selectionModelMeasuresMiscActionProperties)
        self.planningSurveillanceRecord = None
        self.controlSurveillanceItems = []
        self.MKB = u''
        self.diagnosticRecords = {}
        self.diagnosticGroupRecords = {}
        self.itemFilesRecords = {}
        self.visitCache = {}
        self.prophylaxisPlanningTypeId = self.getProphylaxisPlanningType()
        self.modelPlanningSurveillance.setEventEditor(self)
        self.modelControlSurveillance.setEventEditor(self)
        self.tblPlanningSurveillance.addPopupDelRow()

        self.addObject('actChangePersonDN', QtGui.QAction(u'Изменить врача ДН', self))
        self.connect(self.actChangePersonDN, SIGNAL('triggered()'), self.on_actChangePersonDN_triggered)
        self.tblPlanningSurveillance.addPopupAction(self.actChangePersonDN)
        self.addObject('actChangeDispanserDate', QtGui.QAction(u'Изменить дату постановки на учет', self))
        self.connect(self.actChangeDispanserDate, SIGNAL('triggered()'), self.on_actChangeDispanserDate_triggered)
        self.tblPlanningSurveillance.addPopupAction(self.actChangeDispanserDate)
        self.connect(self.tblPlanningSurveillance.popupMenu(), SIGNAL('aboutToShow()'), self.on_popupMenu_aboutToShow)
        self.tblControlSurveillance.addPopupDelRow()
        self.buttonBox.addButton(self.btnApply, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnPrint, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnAttachedFiles, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnSurveillanceRemoved, QtGui.QDialogButtonBox.ActionRole)
        self.btnAttachedFiles.setEnabled(True)
        self.getDispanserRecords()
        self.getRBDispanserConsists()
        self.getRBDispanserRemoved()
        self.getSurveillanceRemoveReason()
        if not QtGui.qApp.userHasRight(urCanUserRemoveDispanser):
            self.btnSurveillanceRemoved.setEnabled(False)
        self.currentItemId = None

    def on_popupMenu_aboutToShow(self):
        model = self.tblPlanningSurveillance.model()
        rowCount = model.realRowCount() if hasattr(model, 'realRowCount') else model.rowCount()
        row = self.tblPlanningSurveillance.currentIndex().row()
        self.actChangeDispanserDate.setEnabled(0 <= row < rowCount)
        self.actChangePersonDN.setEnabled(0 <= row < rowCount)
        self.tblPlanningSurveillance.on_popupMenu_aboutToShow()


    def on_actChangePersonDN_triggered(self):
        item = self.tblPlanningSurveillance.currentItem()
        if item:
            MKB = forceString(item.value('MKB'))
            record = self.diagnosticRecords.get(MKB, None)
            if not record:
                MKBGroup = MKB[:3] if len(MKB) > 3 else MKB
                record = self.diagnosticGroupRecords.get(MKBGroup, None)
            diagnosisId = forceRef(record.value('diagnosis_id')) if record else None
            dialog = CChangeDispanserPerson(self)
            if forceInt(item.value('dispanser_id')) == forceInt(record.value('diagnosisDispanser_id')):
                dialog.load(diagnosisId)
            if dialog.exec_():
                personId = dialog.getPersonId()
                dispanserPersonId = forceRef(personId)
                personRecord = QtGui.qApp.db.getRecordEx('Person', 'speciality_id, orgStructure_id', 'id=%s' % dispanserPersonId)
                specialityId = forceRef(personRecord.value('speciality_id'))
                orgStructureId = forceRef(personRecord.value('orgStructure_id'))
                item.setValue('person_id', dispanserPersonId)
                item.setValue('speciality_id', specialityId)
                item.setValue('orgStructure_id', orgStructureId)


    @pyqtSignature('')
    def on_actChangeDispanserDate_triggered(self):
        item = self.tblPlanningSurveillance.currentItem()
        if item:
            MKB = forceString(item.value('MKB'))
            record = self.diagnosticRecords.get(MKB, None)
            if not record:
                MKBGroup = MKB[:3] if len(MKB) > 3 else MKB
                record = self.diagnosticGroupRecords.get(MKBGroup, None)
            diagnosisId = forceRef(record.value('diagnosis_id')) if record else None
            dialog = CChangeDispanserBegDateLUD(self)
            if forceInt(item.value('dispanser_id')) == forceInt(record.value('diagnosisDispanser_id')):
                dialog.load(diagnosisId)
            if dialog.exec_():
                date = dialog.getDate()
                item.setValue('takenDate', date)


    def getDispanserRecords(self):
        self.dispanserRecords = {}
        db = QtGui.qApp.db
        tableRBDispanser = db.table('rbDispanser')
        records = db.getRecordList(tableRBDispanser, '*')
        for record in records:
            dispanserId = forceRef(record.value('id'))
            if dispanserId:
                self.dispanserRecords[dispanserId] = record

    def getRBDispanserConsists(self):
        db = QtGui.qApp.db
        tableRBDispanser = db.table('rbDispanser')
        record = db.getRecordEx(tableRBDispanser, [tableRBDispanser['id']], [tableRBDispanser['code'].eq(1)])
        self.rbDispanserConsists = forceRef(record.value('id')) if record else None

    def getRBDispanserRemoved(self):
        db = QtGui.qApp.db
        tableRBDispanser = db.table('rbDispanser')
        record = db.getRecordEx(tableRBDispanser, [tableRBDispanser['id']], [tableRBDispanser['name'].like(u'%снят%')])
        self.rbDispanserRemoved = forceRef(record.value('id')) if record else None

    def getSurveillanceRemoveReason(self):
        self.rbSurveillanceRemoveReason = {}
        db = QtGui.qApp.db
        tableSurveillanceRemoveReason = db.table('rbSurveillanceRemoveReason')
        records = db.getRecordList(tableSurveillanceRemoveReason, '*')
        for record in records:
            surveillanceRemoveReasonId = forceRef(record.value('id'))
            if surveillanceRemoveReasonId:
                self.rbSurveillanceRemoveReason[surveillanceRemoveReasonId] = record

    def setEventEditor(self, eventEditor):
        self.eventEditor = eventEditor

    def setEventRecord(self, eventRecord):
        self.eventRecord = eventRecord

    def getProphylaxisPlanningType(self):
        db = QtGui.qApp.db
        table = db.table('rbProphylaxisPlanningType')
        record = db.getRecordEx(table, [table['id']], [table['code'].eq(u'ДН')])
        return forceRef(record.value('id')) if record else None

    def setControlSurveillanceItems(self, items):
        self.controlSurveillanceItems = items

    def setDiagnosticEventLastRecords(self, records):
        self.diagnosticGroupRecords = {}
        records.sort(key=lambda x: forceDate(x.value('endDate')))
        for diagnosticRecord in records:
            MKB = forceStringEx(diagnosticRecord.value('MKB'))
            if MKB:
                MKBGroup = MKB[:3] if len(MKB) > 3 else MKB
                self.diagnosticGroupRecords[MKBGroup] = diagnosticRecord

    def setDiagnosticRecords(self, records):
        self.diagnosticRecords = {}
        diagnosticGroupRecords = {}
        self.MKBs = []
        for diagnosticRecord in records:
            MKB = forceStringEx(diagnosticRecord.value('MKB'))
            if MKB:
                if MKB not in self.MKBs:
                    self.MKBs.append(MKB)
                self.diagnosticRecords[MKB] = diagnosticRecord
                MKBGroup = MKB[:3] if len(MKB) > 3 else MKB
                if MKBGroup not in self.diagnosticGroupRecords.keys():
                    diagnosticGroupRecords[MKBGroup] = diagnosticRecord
        for diagnosticGroupMKB, diagnosticGroupRecord in diagnosticGroupRecords.items():
            self.diagnosticGroupRecords[diagnosticGroupMKB] = diagnosticGroupRecord

    def getProphylaxisPlanningIdList(self):
        prophylaxisPlanningIdList = []
        planningSurveillanceItems = self.modelPlanningSurveillance.items()
        for planningSurveillanceItem in planningSurveillanceItems:
            controlSurveillanceItems = planningSurveillanceItem.controlSurveillance.getItems()
            prophylaxisPlanningId = forceRef(planningSurveillanceItem.value('id'))
            prophylaxisPlanningIdParentId = forceRef(planningSurveillanceItem.value('parent_id'))
            if prophylaxisPlanningIdParentId and prophylaxisPlanningIdParentId not in prophylaxisPlanningIdList:
                prophylaxisPlanningIdList.append(prophylaxisPlanningIdParentId)
            elif prophylaxisPlanningIdParentId is None and prophylaxisPlanningId and prophylaxisPlanningId not in prophylaxisPlanningIdList:
                prophylaxisPlanningIdList.append(prophylaxisPlanningId)
            for controlSurveillanceItem in controlSurveillanceItems:
                controlSurveillanceId = forceRef(controlSurveillanceItem.value('id'))
                controlSurveillanceIdParentId = forceRef(controlSurveillanceItem.value('parent_id'))
                if controlSurveillanceIdParentId and controlSurveillanceIdParentId not in prophylaxisPlanningIdList:
                    prophylaxisPlanningIdList.append(controlSurveillanceIdParentId)
                elif controlSurveillanceIdParentId is None and controlSurveillanceId and controlSurveillanceId not in prophylaxisPlanningIdList:
                    prophylaxisPlanningIdList.append(controlSurveillanceId)
        return prophylaxisPlanningIdList

    def exec_(self):
        self.setRecord(self.eventRecord)
        prophylaxisPlanningIdList = self.getProphylaxisPlanningIdList()
        if prophylaxisPlanningIdList:
            self.lockListEx('ProphylaxisPlanning', prophylaxisPlanningIdList, 0, 0)
            if self.locked():
                try:
                    self.setIsDirty(False)
                    if not self.checkDataBeforeOpen():
                        return QtGui.QDialog.Rejected
                    result = CDialogBase.exec_(self)
                finally:
                    self.releaseLock()
            else:
                result = QtGui.QDialog.Rejected
                self.setResult(result)
        else:
            self.setIsDirty(False)
            if not self.checkDataBeforeOpen():
                return QtGui.QDialog.Rejected
            result = CDialogBase.exec_(self)
        return result

    def setRecord(self, record):
        self.clientSex = None
        self.clientBirthDate = None
        self.clientAge = None
        self.measuresBegDate = None
        self.measuresEndDate = None
        self.MKBList = []
        baseDate = QDate.currentDate()
        CItemEditorBaseDialog.setRecord(self, record)
        self.eventId = forceRef(record.value('id'))
        self.clientId = forceRef(record.value('client_id'))
        self.MKB = forceStringEx(record.value('MKB'))
        db = QtGui.qApp.db
        if self.eventId:
            tableEvent = db.table('Event')
            recordEvent = db.getRecordEx(tableEvent,
                                         [tableEvent['client_id'], tableEvent['setDate'], tableEvent['execDate']],
                                         [tableEvent['id'].eq(self.eventId), tableEvent['deleted'].eq(0)])
            if not self.clientId:
                self.clientId = forceRef(recordEvent.value('client_id'))if recordEvent else None
            setDate = forceDate(recordEvent.value('setDate'))
            execDate = forceDate(recordEvent.value('execDate'))
            baseDate = execDate if execDate else setDate
        if self.clientId:
            tableClient = db.table('Client')
            recordClient = db.getRecordEx(tableClient, [tableClient['sex'], tableClient['birthDate']],
                                          [tableClient['id'].eq(self.clientId), tableClient['deleted'].eq(0)])
            if recordClient:
                self.clientSex = forceInt(recordClient.value('sex'))
                self.clientBirthDate = forceDate(recordClient.value('birthDate'))
                self.clientAge = calcAgeTuple(self.clientBirthDate, baseDate)
        self.modelPlanningSurveillance.setProphylaxisPlanningTypeId(self.prophylaxisPlanningTypeId)
        self.modelPlanningSurveillance.setDiagnosticRecords(self.diagnosticRecords)
        self.modelPlanningSurveillance.setDiagnosticGroupRecords(self.diagnosticGroupRecords)
        self.modelPlanningSurveillance.setClientId(self.clientId)
        self.modelPlanningSurveillance.setMKBs(self.MKBs)
        self.modelControlSurveillance.setProphylaxisPlanningTypeId(self.prophylaxisPlanningTypeId)
        self.modelControlSurveillance.setDiagnosticRecords(self.diagnosticRecords)
        self.modelControlSurveillance.setDiagnosticGroupRecords(self.diagnosticGroupRecords)
        self.modelControlSurveillance.setClientId(self.clientId)
        self.modelControlSurveillance.setEventId(self.eventId)
        self.modelControlSurveillance.setMKBs(self.MKBs)
        self.modelPlanningSurveillance.loadItems(None)
        self.tblPlanningSurveillance.setCurrentRow(0)
        self.controlSurveillanceItems = self.modelControlSurveillance.items()
        if self.controlSurveillanceItems:
            for item in self.controlSurveillanceItems:
                MKB = forceStringEx(item.value('MKB'))
                if MKB and MKB not in self.MKBList:
                    self.MKBList.append(MKB)
            CSItems = self.controlSurveillanceItems
            CSItems.sort(key=lambda x: forceDate(x.value('removeDate')), reverse=True)
            self.measuresEndDate = forceDate(CSItems[0].value('removeDate'))
            CSItems.sort(key=lambda x: forceDate(x.value('takenDate')), reverse=False)
            self.measuresBegDate = forceDate(CSItems[0].value('takenDate'))
            CSItems.sort(key=lambda x: (forceDate(x.value('begDate')), forceDate(x.value('endDate'))) if x else None)
            # self.on_tabMeasuresContent_currentChanged(1)
            # self.on_tabMeasuresContent_currentChanged(2)
            # self.on_tabMeasuresContent_currentChanged(3)
            self.on_tabMeasuresContent_currentChanged(0)
            recordIdList = self.getProphylaxisPlanningAction(0)
            self.modelMeasuresStatusActions.enableIdList = recordIdList

    def getRecord(self):
        record = CItemEditorBaseDialog.getRecord(self)
        return record

    def save(self):
        idList = self.modelPlanningSurveillance.saveItems()
        for item in self.modelPlanningSurveillance.items():
            item.controlSurveillance.saveItems()
        if idList:
            if len(idList) == 1:
                self.btnAttachedFiles.saveItems(idList[0])
            else:
                for key, item in idList.items():
                    if key in self.itemFilesRecords:
                        self.btnAttachedFiles.modelFiles.items = self.itemFilesRecords[key]
                        self.btnAttachedFiles.saveItems(item)
        return True

    def getMaxVisitDate(self, items):
        maxDate = None
        for item in items:
            visitId = forceRef(item.value('visit_id'))
            if visitId:
                visitRecord = self.visitCache.get(visitId, None) if visitId else None
                if not visitRecord:
                    db = QtGui.qApp.db
                    table = db.table('Visit')
                    visitRecord = db.getRecordEx(table, '*', [table['id'].eq(visitId), table['deleted'].eq(0)])
                    if visitRecord:
                        self.visitCache[visitId] = visitRecord
                if visitRecord:
                    date = forceDate(visitRecord.value('date'))
                    if date and date > maxDate:
                        maxDate = date
        return maxDate

    def checkDataEntered(self):
        result = True
        planningSurveillanceItems = self.modelPlanningSurveillance.items()
        for rowPS, planningSurveillanceItem in enumerate(planningSurveillanceItems):
            if not result:
                return result
            MKB = forceStringEx(planningSurveillanceItem.value('MKB'))
            if not MKB:
                self.tblPlanningSurveillance.setCurrentRow(rowPS)
                self.checkInputMessage(u'МКБ', False, self.tblPlanningSurveillance, rowPS,
                                       CPlanningSurveillanceModel.Col_MKB)
                result = False
                return result
            dispanserId = forceRef(planningSurveillanceItem.value('dispanser_id'))
            if not dispanserId:
                self.tblPlanningSurveillance.setCurrentRow(rowPS)
                self.checkInputMessage(u'ДН', False, self.tblPlanningSurveillance, rowPS,
                                       CPlanningSurveillanceModel.Col_DispanserId)
                result = False
                return result
            removeDate = forceDate(planningSurveillanceItem.value('removeDate'))
            removeReasonId = forceRef(planningSurveillanceItem.value('removeReason_id'))
            if removeDate and not removeReasonId:
                self.tblPlanningSurveillance.setCurrentRow(rowPS)
                self.checkInputMessage(u'Причину снятия по диагнозу "%s"'
                                        % MKB, False, self.tblPlanningSurveillance, rowPS,
                                        CPlanningSurveillanceModel.Col_RemoveReasonId)
                result = False
                return result
            takenDate = forceDate(planningSurveillanceItem.value('takenDate'))
            if not takenDate:
                self.tblPlanningSurveillance.setCurrentRow(rowPS)
                self.checkInputMessage(u'Дату взятия', False, self.tblPlanningSurveillance, rowPS,
                                       CPlanningSurveillanceModel.Col_TakenDate)
                result = False
                return result
            if removeReasonId and not removeDate:
                self.tblPlanningSurveillance.setCurrentRow(rowPS)
                self.checkInputMessage(u'Дату снятия по диагнозу "%s"'
                                        % MKB, False, self.tblPlanningSurveillance, rowPS,
                                        CPlanningSurveillanceModel.Col_RemoveDate)
                result = False
                return result
            if takenDate and removeDate and takenDate > removeDate:
                self.tblPlanningSurveillance.setCurrentRow(rowPS)
                self.checkValueMessage(u'Дата снятия %s по диагнозу "%s" не должна быть раньше Даты взятия %s'
                                        % (removeDate.toString('dd.MM.yyyy'), MKB, takenDate.toString('dd.MM.yyyy')),
                                        False, self.tblPlanningSurveillance, rowPS,
                                        CPlanningSurveillanceModel.Col_RemoveDate)
                result = False
                return result
            maxVisitDate = self.getMaxVisitDate(planningSurveillanceItem.controlSurveillance.getItems())
            if maxVisitDate and removeDate and maxVisitDate > removeDate:
                self.tblPlanningSurveillance.setCurrentRow(rowPS)
                self.checkValueMessage(u'Дата снятия %s по диагнозу "%s" не должна быть раньше Даты последнего '
                                        u'визита %s' % (
                                        removeDate.toString('dd.MM.yyyy'), MKB, maxVisitDate.toString('dd.MM.yyyy')),
                                        False, self.tblPlanningSurveillance, rowPS,
                                        CPlanningSurveillanceModel.Col_RemoveDate)
                result = False
                return result
            personId = forceRef(planningSurveillanceItem.value('person_id'))
            if not personId:
                self.tblPlanningSurveillance.setCurrentRow(rowPS)
                self.checkInputMessage(u'Врача', False, self.tblPlanningSurveillance, rowPS,
                                       CPlanningSurveillanceModel.Col_PersonId)
                result = False
                return result
            specialityId = forceRef(QtGui.qApp.db.translate('Person', 'id', personId, 'speciality_id'))
            if not specialityId:
                self.tblPlanningSurveillance.setCurrentRow(rowPS)
                self.checkInputMessage(u'Специальность врача в ККДН', False, self.tblPlanningSurveillance, rowPS,
                                       CPlanningSurveillanceModel.Col_PersonId)
                return False

            # Синхронизация данных с ЛУД
            diagnosticRecord = self.diagnosticRecords.get(MKB, None)
            if not diagnosticRecord:
                MKBGroup = MKB[:3] if len(MKB) > 3 else MKB
                diagnosticRecord = self.diagnosticGroupRecords.get(MKBGroup, None)
            diagnosisId = forceRef(diagnosticRecord.value('diagnosis_id')) if diagnosticRecord else None
            diagEndDate = None
            if diagnosisId:
                diagnosisRecord = QtGui.qApp.db.getRecordEx('Diagnosis', 'dispanserPerson_id, dispanserBegDate, endDate, dispanser_id', 'id=%s' % diagnosisId)
                dispanserPersonId = forceRef(diagnosisRecord.value('dispanserPerson_id'))
                dispanserBegDate = forceDate(diagnosisRecord.value('dispanserBegDate'))
                diagnosticRemovedRecord = QtGui.qApp.db.getRecordEx('Diagnostic', 'endDate', 'diagnosis_id={} AND dispanser_id in (3, 4, 5) AND deleted=0'.format(diagnosisId), order='endDate DESC')
                diagEndDate = None
                if diagnosticRemovedRecord:
                    diagEndDate = forceDate(diagnosticRemovedRecord.value('endDate'))
                if not diagEndDate:
                    diagEndDate = forceDate(diagnosisRecord.value('endDate')) if forceDate(diagnosisRecord.value('endDate')) else QDate().currentDate()
                dispanser = QtGui.qApp.db.getRecordEx('rbDispanser', 'name', 'code="{}"'.format(forceString(diagnosisRecord.value('dispanser_id'))))
                if not dispanserPersonId or not dispanserBegDate:
                    valuesList = []
                    if not dispanserPersonId:
                        valuesList.append(u'врача по ДН')
                    if not dispanserBegDate:
                        valuesList.append(u'дату взятия')
                    self.tblPlanningSurveillance.setCurrentRow(rowPS)
                    QtGui.QMessageBox.warning(self,
                                              u'Внимание!',
                                              u'Синхронизация данных по ДН с ЛУД\nдиагноз: %s\nдата взятия на ДН: %s\nврач: %s\nНеобходимо указать %s' % (
                                              MKB,
                                              formatDate(dispanserBegDate) if dispanserBegDate else u'отсутствует',
                                              getPersonInfo(dispanserPersonId)['fullName'] if dispanserPersonId else u'отсутствует',
                                              u' и '.join(valuesList)),
                                              QtGui.QMessageBox.Ok,
                                              QtGui.QMessageBox.Ok)
                    return False

                personInfo = getPersonInfo(dispanserPersonId)
                orgStructureId = forceRef(planningSurveillanceItem.value('orgStructure_id'))
                diagnosisDispanserId = forceInt(diagnosisRecord.value('dispanser_id'))
                if forceInt(planningSurveillanceItem.value('dispanser_id')) in (1,2,6) and (personId != dispanserPersonId or takenDate != dispanserBegDate or specialityId != personInfo['specialityId'] or orgStructureId != personInfo['orgStructureId'] or \
                    (diagnosisDispanserId != forceInt(planningSurveillanceItem.value('dispanser_id')))):

                    self.tblPlanningSurveillance.setCurrentRow(rowPS)
                    diagnosisDispanserCheck = diagnosisDispanserId and diagnosisDispanserId not in (1,2,6)
                    QtGui.QMessageBox.warning(self,
                                              u'Внимание!',
                                              u'''Синхронизация данных по ДН с ЛУД\nдиагноз: {}\nдата взятия на ДН: {}\nврач: {}\nспециальность: {}\nподразделение: {}\nдолжность: {}\nДН: {}\nДата снятия: {}\n'''.format(MKB, 
                                                                  formatDate(dispanserBegDate), 
                                                                  personInfo['fullName'], 
                                                                  personInfo['specialityName'], 
                                                                  personInfo['orgStructureName'], 
                                                                  personInfo['postName'],
                                                                  forceString(dispanser.value('name')) if dispanser else u'',
                                                                  forceString(diagEndDate) if diagnosisRecord and diagnosisDispanserCheck else u''),
                                              QtGui.QMessageBox.Ok,
                                              QtGui.QMessageBox.Ok)
                    planningSurveillanceItem.setValue('person_id', dispanserPersonId)
                    planningSurveillanceItem.setValue('speciality_id', personInfo['specialityId'])
                    planningSurveillanceItem.setValue('orgStructure_id', personInfo['orgStructureId'])
                    planningSurveillanceItem.setValue('takenDate', dispanserBegDate)
                    planningSurveillanceItem.setValue('removeDate', diagEndDate if diagnosisDispanserCheck else None)
                    planningSurveillanceItem.setValue('dispanser_id', diagnosisRecord.value('dispanser_id'))
                    planningSurveillanceItem.setValue('removeReason_id', 1 if diagnosisDispanserCheck else None)
                    if diagnosisDispanserCheck:
                        self.surveillanceRemovedBySync(diagnosisDispanserId, diagEndDate, 1, rowPS)

        db = QtGui.qApp.db
        tableRBDispanser = db.table('rbDispanser')
        primumPlanningItems = self.modelPlanningSurveillance.items()
        secondPlanningItems = self.modelPlanningSurveillance.items()
        for rowPSP, primumPlanningItem in enumerate(primumPlanningItems):
            if not result:
                return result
            primumMKB = forceStringEx(primumPlanningItem.value('MKB'))
            primumDiag = primumMKB
            if len(primumMKB) >= 3:
                primumDiag = primumMKB[:3]
            primumDispanserId = forceRef(primumPlanningItem.value('dispanser_id'))
            if primumDiag:
                primumObserved = 0
                if primumDispanserId:
                    recObservedPrimum = db.getRecordEx(tableRBDispanser, [tableRBDispanser['observed']],
                                                       [tableRBDispanser['id'].eq(primumDispanserId)])
                    primumObserved = forceInt(recObservedPrimum.value('observed')) if recObservedPrimum else 0
                if primumObserved == 1:
                    for rowPSS, secondPlanningItem in enumerate(secondPlanningItems):
                        if rowPSS != rowPSP:
                            secondMKB = forceStringEx(secondPlanningItem.value('MKB'))
                            secondDiag = secondMKB
                            if len(secondMKB) >= 3:
                                secondDiag = secondMKB[:3]
                            if secondDiag and secondDiag == primumDiag:
                                secondDispanserId = forceRef(secondPlanningItem.value('dispanser_id'))
                                secondObserved = 0
                                if secondDispanserId:
                                    recObservedSecond = db.getRecordEx(tableRBDispanser, [tableRBDispanser['observed']],
                                                                       [tableRBDispanser['id'].eq(secondDispanserId)])
                                    secondObserved = forceInt(
                                        recObservedSecond.value('observed')) if recObservedSecond else 0
                                if secondObserved == 1:
                                    self.tblPlanningSurveillance.setCurrentRow(rowPSS)
                                    self.checkValueMessage(
                                        u'У пациента должна быть только одна группа %s со значением ДН = "нуждается/взят/состоит/взят повторно"' % (
                                            primumDiag), False, self.tblPlanningSurveillance, rowPSS,
                                        CPlanningSurveillanceModel.Col_MKB)
                                    result = False
                                    return result
        for rowPS, planningSurveillanceItem in enumerate(planningSurveillanceItems):
            if not result:
                return result
            takenDate = forceDate(planningSurveillanceItem.value('takenDate'))
            items = planningSurveillanceItem.controlSurveillance.getItems()
            for row, item in enumerate(items):
                MKB = forceStringEx(item.value('MKB'))
                if not MKB:
                    self.tblPlanningSurveillance.setCurrentRow(rowPS)
                    self.checkInputMessage(u'МКБ', False, self.tblControlSurveillance, row,
                                           CControlSurveillanceModel.Col_MKB)
                    result = False
                    return result
                begDate = forceDate(item.value('begDate'))
                endDate = forceDate(item.value('endDate'))
                if not begDate:
                    self.tblPlanningSurveillance.setCurrentRow(rowPS)
                    if not self.checkInputMessage(u'Дату начала периода по диагнозу "%s". Иначе период будет удалён!'
                                                  % MKB, True, self.tblControlSurveillance, row,
                                                  CControlSurveillanceModel.Col_BegDate):
                        result = False
                        return result
                if begDate and not endDate:
                    self.tblPlanningSurveillance.setCurrentRow(rowPS)
                    if not self.checkInputMessage(u'Дату окончания периода по диагнозу "%s". Иначе период будет удалён!'
                                                  % MKB, True, self.tblControlSurveillance, row,
                                                  CControlSurveillanceModel.Col_EndDate):
                        result = False
                        return result
                if begDate and endDate and begDate > endDate:
                    self.tblPlanningSurveillance.setCurrentRow(rowPS)
                    self.checkValueMessage(u'Дата начала периода %s по диагнозу "%s" не может быть больше Даты '
                                           u'окончания периода %s' % (
                                           begDate.toString('dd.MM.yyyy'), MKB, endDate.toString('dd.MM.yyyy')), False,
                                           self.tblControlSurveillance, row, CControlSurveillanceModel.Col_BegDate)
                    result = False
                    return result
                personId = forceRef(item.value('person_id'))
                specialityId = forceRef(QtGui.qApp.db.translate('Person', 'id', personId, 'speciality_id'))
                if not specialityId:
                    self.tblPlanningSurveillance.setCurrentRow(rowPS)
                    self.checkInputMessage(u'Сотрудника со специальностью в периоде', False, self.tblControlSurveillance, row,
                                           CControlSurveillanceModel.Col_PersonId)
                    return False
                orgStructureId = forceRef(item.value('orgStructure_id'))
                if not orgStructureId:
                    self.tblPlanningSurveillance.setCurrentRow(rowPS)
                    self.checkValueMessage(u'Не указано Подразделение в профиле сотрудника', False, self.tblControlSurveillance, row,
                                           CControlSurveillanceModel.Col_PersonId)
                    return False

        for rowPS, planningSurveillanceItem in enumerate(planningSurveillanceItems):
            if not result:
                return result
            primumItems = planningSurveillanceItem.controlSurveillance.getItems()
            secondItems = planningSurveillanceItem.controlSurveillance.getItems()
            for primumRow, primumItem in enumerate(primumItems):
                if not result:
                    return result
                begDateP = forceDate(primumItem.value('begDate'))
                endDateP = forceDate(primumItem.value('endDate'))
                for secondRow, secondItem in enumerate(secondItems):
                    if primumRow != secondRow:
                        begDateS = forceDate(secondItem.value('begDate'))
                        endDateS = forceDate(secondItem.value('endDate'))
                        if (begDateS <= begDateP <= endDateS) or (begDateS <= endDateP <= endDateS):
                            self.tblPlanningSurveillance.setCurrentRow(rowPS)
                            self.checkValueMessage(u'Пересечение периодов %s - %s и %s - %s по диагнозу "%s"'
                                                   % (begDateP.toString('dd.MM.yyyy'), endDateP.toString('dd.MM.yyyy'),
                                                      begDateS.toString('dd.MM.yyyy'), endDateS.toString('dd.MM.yyyy'),
                                                      MKB), False, self.tblControlSurveillance, secondRow,
                                                   CControlSurveillanceModel.Col_BegDate)
                            result = False
                            return result
        return result

    def saveData(self):
        return self.checkDataEntered() and self.save()

    @pyqtSignature('')
    def on_btnSurveillanceRemoved_clicked(self):
        specialityId = forceRef(QtGui.qApp.db.translate('Person', 'id', QtGui.qApp.userId, 'speciality_id'))
        if specialityId:
            dialog = CSurveillanceRemovedDialog()
            try:
                if dialog.exec_():
                    self.modelPlanningSurveillance.removeReasonDate = dialog.getRemoveReasonDate()
                    self.modelPlanningSurveillance.removeDispanserId = dialog.getDispanserId()
                    removeReasonId = dialog.getRemoveReasonId()
                    self.surveillanceRemoved(dialog.getDispanserId(), dialog.getRemoveReasonDate(), removeReasonId)
            finally:
                dialog.deleteLater()
        else:
            QtGui.QMessageBox.warning(self,
                                      u'Внимание!',
                                      u'В текущей учетной записи отсутствует специальность. Заполнение данных о снятии с ДН невозможно!',
                                      QtGui.QMessageBox.Ok,
                                      QtGui.QMessageBox.Ok)

    def surveillanceRemoved(self, dispanserIdNew, removeReasonDateNew, removeReasonIdNew):
        items = self.modelPlanningSurveillance.items()
        for row, item in enumerate(items):
            if hasattr(item, 'controlSurveillance'):
                dispanserId = forceRef(item.value('dispanser_id'))
                dispanserRecord = self.dispanserRecords.get(dispanserId, None) if dispanserId else None
                observed = forceInt(dispanserRecord.value('observed')) if dispanserRecord else 0
                if observed == 1:
                    self.modelPlanningSurveillance.items()[row].setValue('dispanser_id', toVariant(dispanserIdNew))
                    self.modelPlanningSurveillance.items()[row].setValue('removeDate', toVariant(removeReasonDateNew))
                    self.modelPlanningSurveillance.items()[row].setValue('removeReason_id', toVariant(removeReasonIdNew))
                    removeDate = forceDate(self.modelPlanningSurveillance.items()[row].value('removeDate'))
                    self.modelControlSurveillance.setItems(items[row].controlSurveillance.getItems(), items[row].controlSurveillance.getDiagnosticItems())
                    itemsCS = self.modelControlSurveillance.items()
                    for itemRCS in reversed(xrange(len(itemsCS))):
                        begDate = forceDate(itemsCS[itemRCS].value('begDate'))
                        visitId = forceRef(itemsCS[itemRCS].value('visit_id'))
                        if removeDate and begDate and removeDate < begDate and not visitId:
                            self.modelControlSurveillance.removeRow(itemRCS)
                    itemsCS = self.modelControlSurveillance.items()
                    for rowCS, itemCS in enumerate(itemsCS):
                        self.modelControlSurveillance.items()[rowCS].setValue('dispanser_id', toVariant(dispanserIdNew))
                        self.modelControlSurveillance.items()[rowCS].setValue('removeDate', toVariant(removeReasonDateNew))
                        self.modelControlSurveillance.items()[rowCS].setValue('removeReason_id', toVariant(removeReasonIdNew))
                    self.modelPlanningSurveillance.items()[row].controlSurveillance.setItems(
                        self.modelControlSurveillance.items(), self.modelControlSurveillance.diagnosticItems)
                    self.modelPlanningSurveillance.emitRowChanged(row)


    def surveillanceRemovedBySync(self, dispanserIdNew, removeReasonDateNew, removeReasonIdNew, row):
        item = self.modelPlanningSurveillance.items()[row]
        if hasattr(item, 'controlSurveillance'):
            dispanserId = forceRef(item.value('dispanser_id'))
            dispanserRecord = self.dispanserRecords.get(dispanserId, None) if dispanserId else None
            observed = forceInt(dispanserRecord.value('observed')) if dispanserRecord else 0
            if observed == 1:
                self.modelPlanningSurveillance.items()[row].setValue('dispanser_id', toVariant(dispanserIdNew))
                self.modelPlanningSurveillance.items()[row].setValue('removeDate', toVariant(removeReasonDateNew))
                self.modelPlanningSurveillance.items()[row].setValue('removeReason_id', toVariant(removeReasonIdNew))
                removeDate = forceDate(self.modelPlanningSurveillance.items()[row].value('removeDate'))
                self.modelControlSurveillance.setItems(item.controlSurveillance.getItems(), item.controlSurveillance.getDiagnosticItems())
                itemsCS = self.modelControlSurveillance.items()
                for itemRCS in reversed(xrange(len(itemsCS))):
                    begDate = forceDate(itemsCS[itemRCS].value('begDate'))
                    visitId = forceRef(itemsCS[itemRCS].value('visit_id'))
                    if removeDate and begDate and removeDate < begDate and not visitId:
                        self.modelControlSurveillance.removeRow(itemRCS)
                itemsCS = self.modelControlSurveillance.items()
                for rowCS, itemCS in enumerate(itemsCS):
                    self.modelControlSurveillance.items()[rowCS].setValue('dispanser_id', toVariant(dispanserIdNew))
                    self.modelControlSurveillance.items()[rowCS].setValue('removeDate', toVariant(removeReasonDateNew))
                    self.modelControlSurveillance.items()[rowCS].setValue('removeReason_id', toVariant(removeReasonIdNew))
                self.modelPlanningSurveillance.items()[row].controlSurveillance.setItems(
                    self.modelControlSurveillance.items(), self.modelControlSurveillance.diagnosticItems)
                self.modelPlanningSurveillance.emitRowChanged(row)


    @pyqtSignature('int')
    def on_btnPrint_printByTemplate(self, templateId):
        context = CInfoContext()
        idPlanningSurveillance = forceInt(self.tblPlanningSurveillance.currentItem().value('id'))
        planningSurveillances = context.getInstance(CProphylaxisPlanningInfoList, [idPlanningSurveillance])
        controlSurveillances = CProphylaxisPlanningInfoProxyList(context, [self.modelControlSurveillance])
        self.on_tabMeasuresContent_currentChanged(1)
        self.on_tabMeasuresContent_currentChanged(2)
        self.on_tabMeasuresContent_currentChanged(3)
        self.on_tabMeasuresContent_currentChanged(0)
        measuresActions = CActionInfoProxyList(context, [self.modelMeasuresStatusActions, self.modelMeasuresDiagnosticActions, self.modelMeasuresCureActions, self.modelMeasuresMiscActions], eventInfo=None)
        measuresActionsSelected = CActionSelectedInfoProxyList(context, [self.modelMeasuresStatusActions.getSelectedItems(), self.modelMeasuresDiagnosticActions.getSelectedItems(),
        self.modelMeasuresCureActions.getSelectedItems(), self.modelMeasuresMiscActions.getSelectedItems()], eventInfo=None)
        personId = forceInt(self.tblPlanningSurveillance.currentItem().value('person_id'))
        data = {'client': context.getInstance(CClientInfo, self.clientId, QDate.currentDate()),
                'planningSurveillances': planningSurveillances,
                'controlSurveillances': controlSurveillances,
                'measuresActions': measuresActions,
                'measuresActionsSelected': measuresActionsSelected,
                'signerPerson': personId if personId else None
                }
        signAndAttachResult = applyTemplate(self, templateId, data, signAndAttachHandler=self.btnAttachedFiles.getSignAndAttachHandler())
        if signAndAttachResult:
            self.setIsDirty(True)
            self.setFilesList()

    @pyqtSignature('')
    def on_btnAttachedFiles_pressed(self):
        self.setFilesList()
    
    
    @pyqtSignature('')
    def on_btnApply_clicked(self):
        if self.applyChanges():
            buttons = QtGui.QMessageBox.Ok
            messageBox = QtGui.QMessageBox()
            messageBox.setWindowFlags(messageBox.windowFlags() | Qt.WindowStaysOnTopHint)
            messageBox.setWindowTitle(u'Внимание!')
            messageBox.setText(u'Данные сохранены')
            messageBox.setStandardButtons(buttons)
            messageBox.setDefaultButton(QtGui.QMessageBox.Ok)
            return messageBox.exec_()
    
    
    def applyChanges(self):
        if self.saveData():
            self.lock(self._tableName, self._id)
            return True
        else:
            return False
            

    def setFilesList(self):
        index = self.tblPlanningSurveillance.currentIndex()
        if index.isValid():
            if len(self.modelPlanningSurveillance.items()) > 1:
                row = index.row()
                self.itemFilesRecords[row] = self.btnAttachedFiles.modelFiles.items

    @pyqtSignature('QModelIndex, QModelIndex')
    def on_modelPlanningSurveillance_dataChanged(self, topLeft, bottomRight):
        index = self.tblPlanningSurveillance.currentIndex()
        if index.isValid():
            row = index.row()
            items = self.modelPlanningSurveillance.items()
            if 0 <= row < len(items) and hasattr(items[row], 'controlSurveillance'):
                self.modelControlSurveillance.setItems(items[row].controlSurveillance.getItems(),
                                                       items[row].controlSurveillance.getDiagnosticItems())
                indexPS = self.tblPlanningSurveillance.currentIndex()
                itemsPS = self.modelPlanningSurveillance.items()
                i = indexPS.row()
                if 0 <= i < len(itemsPS):
                    column = indexPS.column()
                    itemPS = itemsPS[i]
                    controlSurveillanceItems = self.modelControlSurveillance.items()
                    if column == CPlanningSurveillanceModel.Col_TakenDate:
                        takenDate = forceDate(itemPS.value('takenDate'))
                        for i, controlSurveillanceItem in enumerate(controlSurveillanceItems):
                            self.modelControlSurveillance.items()[i].setValue('takenDate', toVariant(takenDate))
                    elif column == CPlanningSurveillanceModel.Col_DispanserId:
                        dispanserId = forceRef(itemPS.value('dispanser_id'))
                        for i, controlSurveillanceItem in enumerate(controlSurveillanceItems):
                            self.modelControlSurveillance.items()[i].setValue('dispanser_id', toVariant(dispanserId))
                    self.modelPlanningSurveillance.items()[row].controlSurveillance.setItems(
                        self.modelControlSurveillance.items(), self.modelControlSurveillance.diagnosticItems)
                    self.on_tabMeasuresContent_currentChanged(self.tabMeasuresContent.currentIndex())
            else:
                self.modelControlSurveillance.clearItems()

    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelPlanningSurveillance_currentRowChanged(self, current, previous):
        index = self.tblPlanningSurveillance.currentIndex()
        if index.isValid():
            row = index.row()
            items = self.modelPlanningSurveillance.items()
            currentItem = self.tblPlanningSurveillance.currentItem()
            if currentItem:
                self.currentItemId = forceInt(currentItem.value('id'))
                self.MKB = forceString(self.tblPlanningSurveillance.currentItem().value('MKB'))
                dispanserId = forceInt(currentItem.value('dispanser_id'))
                dispanserRecord = self.dispanserRecords.get(dispanserId, None)
                if dispanserRecord:
                    observed = forceInt(dispanserRecord.value('observed'))
                    if observed:
                        self.modelPlanningSurveillance.cols()[self.modelPlanningSurveillance.Col_RemoveReasonId].setReadOnly(True)
                    else:
                        self.modelPlanningSurveillance.cols()[self.modelPlanningSurveillance.Col_RemoveReasonId].setReadOnly(False)
                if 0 <= row < len(items) and hasattr(items[row], 'controlSurveillance'):
                    self.modelControlSurveillance.setItems(items[row].controlSurveillance.getItems(),
                                                           items[row].controlSurveillance.getDiagnosticItems())
                    indexPS = self.tblPlanningSurveillance.currentIndex()
                    itemsPS = self.modelPlanningSurveillance.items()
                    i = indexPS.row()
                    if 0 <= i < len(itemsPS):
                        # column = indexPS.column()
                        itemPS = itemsPS[i]
                        # controlSurveillanceItems = self.modelControlSurveillance.items()
                        # if column == CPlanningSurveillanceModel.Col_PersonId:
                        #     personId = forceInt(itemPS.value('person_id'))
                        #     orgStrId = forceInt(itemPS.value('orgStructure_id'))
                        #     for i, controlSurveillanceItem in enumerate(controlSurveillanceItems):
                        #         self.modelControlSurveillance.items()[i].setValue('person_id', toVariant(personId))
                        #         self.modelControlSurveillance.items()[i].setValue('orgStructure_id', toVariant(orgStrId))
                        self.modelPlanningSurveillance.items()[row].controlSurveillance.setItems(
                            self.modelControlSurveillance.items(), self.modelControlSurveillance.diagnosticItems)
                        if forceRef(itemPS.value('id')):
                            self.btnAttachedFiles.loadItems(forceRef(itemPS.value('id')))
                            self.itemFilesRecords[row] = self.btnAttachedFiles.modelFiles.items
                        self.btnAttachedFiles.modelFiles.items = self.itemFilesRecords.get(row, [])
                        self.on_tabMeasuresContent_currentChanged(self.tabMeasuresContent.currentIndex())
                else:
                    self.modelControlSurveillance.clearItems()

    @pyqtSignature('QModelIndex, QModelIndex')
    def on_modelControlSurveillance_dataChanged(self, topLeft, bottomRight):
        index = self.tblPlanningSurveillance.currentIndex()
        if index.isValid():
            row = index.row()
            items = self.modelPlanningSurveillance.items()
            if 0 <= row < len(items) and hasattr(items[row], 'controlSurveillance'):
                indexCS = self.tblControlSurveillance.currentIndex()
                itemsCS = self.modelControlSurveillance.items()
                i = indexCS.row()
                if 0 <= i < len(itemsCS):
                    column = indexCS.column()
                    itemCS = itemsCS[i]
                    #if column == CControlSurveillanceModel.Col_RemoveDate:
                    #    removeDate = forceDate(itemCS.value('removeDate'))
                    #    rRows = []
                    #    for rowRCS, itemRCS in enumerate(itemsCS):
                    #        begDate = forceDate(itemRCS.value('begDate'))
                    #        visitId = forceRef(itemRCS.value('visit_id'))
                    #        if removeDate and begDate and removeDate < begDate and rowRCS not in rRows and not visitId:
                    #            rRows.append(rowRCS)
                    #    for rRow in rRows:
                    #        self.modelControlSurveillance.removeRow(rRow)
                    #    itemsCS = self.modelControlSurveillance.items()
                    #    for rowCS, itemCS in enumerate(itemsCS):
                    #        self.modelControlSurveillance.items()[rowCS].setValue('removeDate', toVariant(removeDate))
                    #    self.modelPlanningSurveillance.items()[row].setValue('removeDate', toVariant(removeDate))
                    #elif column == CControlSurveillanceModel.Col_RemoveReasonId:
                    #    removeReasonId = forceRef(itemCS.value('removeReason_id'))
                    #    itemsCS = self.modelControlSurveillance.items()
                    #    for rowCS, itemCS in enumerate(itemsCS):
                    #        self.modelControlSurveillance.items()[rowCS].setValue('removeReason_id',
                    #                                                              toVariant(removeReasonId))
                    #    self.modelPlanningSurveillance.items()[row].setValue('removeReason_id',
                    #                                                         toVariant(removeReasonId))
                    if column == CControlSurveillanceModel.Col_MKB:
                        MKB = forceStringEx(itemCS.value('MKB'))
                        if MKB and i >= (len(self.modelControlSurveillance.items()) - 1):
                            self.modelPlanningSurveillance.items()[row].setValue('MKB', toVariant(MKB))
                    elif column == CControlSurveillanceModel.Col_VisitId:
                        visitId = forceRef(itemCS.value('visit_id'))
                        if visitId:
                            dispanserId = None
                            MKB = forceStringEx(itemCS.value('MKB'))
                            visitLastRow = self.modelControlSurveillance.getLastVisitRow()
                            if i == len(itemsCS) - 1 or visitLastRow < 0 or i >= visitLastRow:
                                if forceStringEx(self.modelPlanningSurveillance.items()[row].value('MKB')) != MKB:
                                    self.modelPlanningSurveillance.items()[row].setValue('MKB', toVariant(MKB))
                            if MKB:
                                MKBCaches = self.modelControlSurveillance.cols()[column].MKBCaches
                                MKBRecord = MKBCaches.get((visitId, MKB), None)
                                if MKBRecord:
                                    dispanserId = forceRef(MKBRecord.value('dispanser_id'))
                            if not dispanserId:
                                MKBGroup = MKB[:3] if len(MKB) > 3 else MKB
                                diagnosticRecord = self.diagnosticGroupRecords.get(MKBGroup, None)
                                if not diagnosticRecord:
                                    diagnosticRecord = self.diagnosticRecords.get(MKB, None) if MKB else None
                                if diagnosticRecord:
                                    dispanserId = forceRef(diagnosticRecord.value('diagnosisDispanser_id'))
                            if dispanserId:
                                db = QtGui.qApp.db
                                tableRBDispanser = db.table('rbDispanser')
                                recObserved = db.getRecordEx(tableRBDispanser, [tableRBDispanser['observed']],
                                                            [tableRBDispanser['id'].eq(dispanserId)])
                                dispObserved = forceInt(recObserved.value('observed')) if recObserved else 0
                                oldDispanserId = forceInt(self.modelPlanningSurveillance.items()[row].value('dispanser_id'))
                                self.modelPlanningSurveillance.items()[row].setValue('dispanser_id',
                                                                                     toVariant(dispanserId))
                                if self.eventId:
                                    dispanserRecord = self.dispanserRecords.get(dispanserId, None)
                                    if dispanserRecord:
                                        observed = forceInt(dispanserRecord.value('observed'))
                                        name = forceStringEx(dispanserRecord.value('name'))
                                        if oldDispanserId != dispanserId:
                                            if observed:
                                                self.modelPlanningSurveillance.cols()[self.modelPlanningSurveillance.Col_RemoveReasonId].setReadOnly(True)
                                            else:
                                                self.modelPlanningSurveillance.cols()[self.modelPlanningSurveillance.Col_RemoveReasonId].setReadOnly(False)
                                        if observed == 0 and u'нуждается' not in name:
                                            dateVisitForRemoved = self.getEventVisitMAXDate(self.eventId, i,
                                                                                            self.modelControlSurveillance.items())
                                            if dateVisitForRemoved:
                                                self.modelPlanningSurveillance.items()[row].setValue('removeDate',
                                                                                                     toVariant(
                                                                                                         dateVisitForRemoved))
                                                itemsCS = self.modelControlSurveillance.items()
                                                for rowCS, itemCS in enumerate(itemsCS):
                                                    self.modelControlSurveillance.items()[rowCS].setValue('removeDate',
                                                                                                          toVariant(
                                                                                                              dateVisitForRemoved))  
                                removeReasonId = None
                                defaultReasonId = None
                                if not dispObserved:
                                    for surveillanceRemoveReasonId, rbSurveillanceRemoveReasonItem in self.rbSurveillanceRemoveReason.items():
                                        removeReasonName = forceString(rbSurveillanceRemoveReasonItem.value('name'))
                                        dispanserSRRId = forceRef(rbSurveillanceRemoveReasonItem.value('dispanser_id'))
                                        if dispanserSRRId == dispanserId:
                                            removeReasonId = surveillanceRemoveReasonId
                                            break
                                        if u'выздоров' in removeReasonName.lower():
                                            defaultReasonId = surveillanceRemoveReasonId
                                    if not forceDate(self.modelPlanningSurveillance.items()[row].value('removeDate')):
                                        self.modelPlanningSurveillance.items()[row].setValue(
                                        'removeDate', toVariant(QDate().currentDate()))
                                else:
                                    self.modelPlanningSurveillance.items()[row].setValue(
                                        'removeDate', toVariant(QDate()))
                                if not removeReasonId:
                                    removeReasonId = defaultReasonId
                                self.modelPlanningSurveillance.items()[row].setValue(
                                    'removeReason_id', toVariant(removeReasonId))
                                itemsCS = self.modelControlSurveillance.items()
                                for rowCS, itemCS in enumerate(itemsCS):
                                    self.modelControlSurveillance.items()[rowCS].setValue(
                                        'removeReason_id', toVariant(removeReasonId))
                    self.modelPlanningSurveillance.items()[row].controlSurveillance.setItems(
                        self.modelControlSurveillance.items(), self.modelControlSurveillance.diagnosticItems)
                    self.modelPlanningSurveillance.emitRowChanged(row)
            else:
                self.modelControlSurveillance.clearItems()
        else:
            self.modelControlSurveillance.clearItems()

    def getEventVisitMAXDate(self, eventId, row, items):
        visitIdList = []
        prophylaxisPlanningIdList = []
        removeDate = None
        visitRecords = None
        for i, item in enumerate(items):
            if i != row:
                visitId = forceRef(item.value('visit_id'))
                if visitId and visitId not in visitIdList:
                    visitIdList.append(visitId)
                prophylaxisPlanningId = forceRef(item.value('id'))
                if prophylaxisPlanningId and prophylaxisPlanningId not in prophylaxisPlanningIdList:
                    prophylaxisPlanningIdList.append(prophylaxisPlanningId)
            if not removeDate:
                removeDate = forceDate(item.value('removeDate'))
        record = items[row]
        takenDate = forceDate(record.value('takenDate'))
        MKB = forceStringEx(record.value('MKB'))
        MKB = MKB[:3]
        clientId = forceRef(record.value('client_id'))
        if takenDate and MKB and clientId:
            db = QtGui.qApp.db
            table = db.table('Visit')
            tableEvent = db.table('Event')
            tableDiagnosis = db.table('Diagnosis')
            tableDiagnostic = db.table('Diagnostic')
            tableDispanser = db.table('rbDispanser')
            queryTable = tableEvent.innerJoin(table, table['event_id'].eq(tableEvent['id']))
            queryTable = queryTable.innerJoin(tableDiagnostic, tableDiagnostic['event_id'].eq(tableEvent['id']))
            queryTable = queryTable.innerJoin(tableDiagnosis, tableDiagnosis['id'].eq(tableDiagnostic['diagnosis_id']))
            queryTable = queryTable.innerJoin(tableDispanser, tableDispanser['id'].eq(tableDiagnostic['dispanser_id']))
            cond = [table['date'].dateGe(takenDate),
                    tableDiagnosis['client_id'].eq(clientId),
                    tableEvent['id'].eq(eventId),
                    tableEvent['client_id'].eq(clientId),
                    tableDiagnosis['MKB'].like(MKB[:3] + '%'),
                    tableDiagnostic['dispanser_id'].isNotNull(),
                    table['deleted'].eq(0),
                    tableDiagnosis['deleted'].eq(0),
                    tableDiagnostic['deleted'].eq(0),
                    tableEvent['deleted'].eq(0)
                    ]
            if visitIdList:
                cond.append(table['id'].notInlist(visitIdList))
            if removeDate:
                cond.append(table['date'].dateLe(removeDate))
            cond.append(u'''NOT EXISTS(SELECT ProphylaxisPlanning.id
            FROM ProphylaxisPlanning
            WHERE ProphylaxisPlanning.visit_id = Visit.id
            AND ProphylaxisPlanning.MKB LIKE '%s'
            AND ProphylaxisPlanning.deleted = 0 %s)''' % (MKB[:3] + '%', (u'AND ProphylaxisPlanning.id NOT IN (%s)' % (
                u','.join(
                    str(ppId) for ppId in prophylaxisPlanningIdList if ppId))) if prophylaxisPlanningIdList else u''))
            visitRecords = db.getMax(queryTable, table['date'].name(), cond)
        return forceDate(visitRecords) if visitRecords else None

    def getProphylaxisPlanningAction(self, classCode):
        db = QtGui.qApp.db
        tableProphylaxisPlanningAction = db.table('ProphylaxisPlanning_Action')
        result = db.getRecordList(tableProphylaxisPlanningAction, 'action_id',
                                  [tableProphylaxisPlanningAction['master_id'].eq(self.currentItemId),
                                   tableProphylaxisPlanningAction['classCode'].eq(classCode)])
        return [forceInt(item.value('action_id')) for item in result]

    def getClientActions(self, clientId, filter, classCode, order=['Action.endDate DESC', 'Action.id'], fieldName=None):
        loadActionIdList = self.getProphylaxisPlanningAction(classCode)
        db = QtGui.qApp.db
        tableAction = db.table('Action')
        queryTable = tableAction
        tableEvent = db.table('Event')
        queryTable = queryTable.innerJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))
        tableActionType = db.table('ActionType')
        queryTable = queryTable.leftJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
        if fieldName in [u'setPerson_id', u'person_id']:
            tableSPWS = db.table('vrbPersonWithSpeciality')
            queryTable = queryTable.leftJoin(tableSPWS, tableSPWS['id'].eq(tableAction[fieldName]))
        cond = [tableAction['deleted'].eq(0),
                tableEvent['deleted'].eq(0),
                tableEvent['client_id'].eq(clientId)]
        if not self.MKBList and not self.controlSurveillanceItems:
            return []
        tableDiagnosis = db.table('Diagnosis')
        tableDiagnostic = db.table('Diagnostic')
        tableDispanser = db.table('rbDispanser')
        queryTable = queryTable.innerJoin(tableDiagnostic, tableDiagnostic['event_id'].eq(tableEvent['id']))
        queryTable = queryTable.innerJoin(tableDiagnosis, tableDiagnosis['id'].eq(tableDiagnostic['diagnosis_id']))
        queryTable = queryTable.innerJoin(tableDispanser, tableDispanser['id'].eq(tableDiagnostic['dispanser_id']))
        cond.append(tableDiagnosis['MKB'].eq(self.MKB))
        cond.append(tableDiagnostic['dispanser_id'].isNotNull())
        cond.append(tableDiagnosis['deleted'].eq(0))
        cond.append(tableDiagnostic['deleted'].eq(0))
        cond.append(tableEvent['deleted'].eq(0))
        if classCode is not None:
            cond.append(tableActionType['class'].eq(classCode))
        serviceType = filter.get('serviceType', None)
        if serviceType is not None:
            cond.append(tableActionType['serviceType'].eq(serviceType))
        begDate = filter.get('begDate', None)
        if begDate:
            cond.append(db.joinOr([tableAction['endDate'].isNull(), tableAction['endDate'].dateGe(begDate)]))
        endDate = filter.get('endDate', None)
        if endDate:
            cond.append(db.joinOr([tableAction['endDate'].isNull(), tableAction['endDate'].dateLe(endDate)]))
        actionGroupId = filter.get('actionGroupId', None)
        if actionGroupId:
            cond.append(tableAction['actionType_id'].inlist(getActionTypeDescendants(actionGroupId, classCode)))
        office = filter.get('office', '')
        if office:
            cond.append(tableAction['office'].like(office))
        orgStructureId = filter.get('orgStructureId', None)
        if orgStructureId:
            cond.append(tableAction['person_id'].inlist(getOrgStructurePersonIdList(orgStructureId)))
        try:
            QtGui.QApplication.setOverrideCursor(QtGui.QCursor(Qt.WaitCursor))
            res = db.getIdList(queryTable, tableAction['id'].name(), cond, order)
            for loadId in loadActionIdList:
                if loadId not in res:
                    db.deleteRecordSimple('ProphylaxisPlanning_Action', 'action_id=%s' % loadId)
            return res
        finally:
            QtGui.QApplication.restoreOverrideCursor()

    @pyqtSignature('int')
    def on_tabMeasuresContent_currentChanged(self, index):
        currentItem = self.tblPlanningSurveillance.currentItem()
        measuresBegDate = forceDate(currentItem.value('takenDate'))
        measuresEndDate = forceDate(currentItem.value('removeDate'))
        widget = self.tabMeasuresContent.widget(index)
        if widget:
            focusProxy = widget.focusProxy()
            if focusProxy:
                focusProxy.setFocus(Qt.OtherFocusReason)
        if index == 0:
            self.on_btnMeasuresStatusButtonBox_reset()
            self.edtMeasuresStatusBegDate.setDate(measuresBegDate)
            self.edtMeasuresStatusEndDate.setDate(measuresEndDate)
            self.on_btnMeasuresStatusButtonBox_apply()
        elif index == 1:
            self.on_btnMeasuresDiagnosticButtonBox_reset()
            self.edtMeasuresDiagnosticBegDate.setDate(measuresBegDate)
            self.edtMeasuresDiagnosticEndDate.setDate(measuresEndDate)
            self.on_btnMeasuresDiagnosticButtonBox_apply()
        elif index == 2:
            self.on_btnMeasuresCureButtonBox_reset()
            self.edtMeasuresCureBegDate.setDate(measuresBegDate)
            self.edtMeasuresCureEndDate.setDate(measuresEndDate)
            self.on_btnMeasuresCureButtonBox_apply()
        elif index == 3:
            self.on_btnMeasuresMiscButtonBox_reset()
            self.edtMeasuresMiscBegDate.setDate(measuresBegDate)
            self.edtMeasuresMiscEndDate.setDate(measuresEndDate)
            self.on_btnMeasuresMiscButtonBox_apply()

    def selectMeasuresActions(self, filter, classCode, order, fieldName):
        res = self.getClientActions(self.clientId, filter, classCode, order, fieldName)
        return res

    def getMeasuresFilter(self, edtBegDate, edtEndDate, cmbGroup, edtOffice, cmbOrgStructure):
        filter = {'begDate': edtBegDate.date(),
                  'endDate': edtEndDate.date(),
                  'actionGroupId': cmbGroup.value(),
                  'office': forceString(edtOffice.text()),
                  'orgStructureId': cmbOrgStructure.value()}
        return filter

    def resetMeasuresFilter(self, edtBegDate, edtEndDate, cmbGroup, edtOffice, cmbOrgStructure):
        edtBegDate.setDate(self.measuresBegDate)
        edtEndDate.setDate(self.measuresEndDate)
        cmbGroup.setValue(None)
        edtOffice.setText('')
        cmbOrgStructure.setValue(None)

    @pyqtSignature('QAbstractButton*')
    def on_btnMeasuresStatusButtonBox_clicked(self, button):
        buttonCode = self.btnMeasuresStatusButtonBox.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.on_btnMeasuresStatusButtonBox_apply()
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.on_btnMeasuresStatusButtonBox_reset()

    @pyqtSignature('QAbstractButton*')
    def on_btnMeasuresDiagnosticButtonBox_clicked(self, button):
        buttonCode = self.btnMeasuresDiagnosticButtonBox.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.on_btnMeasuresDiagnosticButtonBox_apply()
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.on_btnMeasuresDiagnosticButtonBox_reset()

    @pyqtSignature('QAbstractButton*')
    def on_btnMeasuresCureButtonBox_clicked(self, button):
        buttonCode = self.btnMeasuresCureButtonBox.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.on_btnMeasuresCureButtonBox_apply()
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.on_btnMeasuresCureButtonBox_reset()

    @pyqtSignature('QAbstractButton*')
    def on_btnMeasuresMiscButtonBox_clicked(self, button):
        buttonCode = self.btnMeasuresMiscButtonBox.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.on_btnMeasuresMiscButtonBox_apply()
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.on_btnMeasuresMiscButtonBox_reset()

    def on_btnMeasuresDiagnosticButtonBox_apply(self):
        filter = self.getMeasuresFilter(
            self.edtMeasuresDiagnosticBegDate,
            self.edtMeasuresDiagnosticEndDate,
            self.cmbMeasuresDiagnosticGroup,
            self.edtMeasuresDiagnosticOffice,
            self.cmbMeasuresDiagnosticOrgStructure
        )
        self.updateMeasuresDiagnosticActions(filter)
        self.focusMeasuresDiagnosticActions()

    def on_btnMeasuresDiagnosticButtonBox_reset(self):
        self.resetMeasuresFilter(
            self.edtMeasuresDiagnosticBegDate,
            self.edtMeasuresDiagnosticEndDate,
            self.cmbMeasuresDiagnosticGroup,
            self.edtMeasuresDiagnosticOffice,
            self.cmbMeasuresDiagnosticOrgStructure)

    def updateMeasuresDiagnosticActions(self, filter, posToId=None, fieldName=None):
        self.__measuresDiagnosticFilter = filter
        order = self.tblMeasuresDiagnosticActions.order() if self.tblMeasuresDiagnosticActions.order() else ['Action.endDate DESC', 'id']
        self.tblMeasuresDiagnosticActions.setIdList(self.selectMeasuresActions(filter, 1, order, fieldName), posToId)
        self.modelMeasuresDiagnosticActions.enableIdList = self.getProphylaxisPlanningAction(1)

    def focusMeasuresDiagnosticActions(self):
        self.tblMeasuresDiagnosticActions.setFocus(Qt.TabFocusReason)

    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelMeasuresDiagnosticActions_currentRowChanged(self, current, previous):
        self.updateMeasuresPropertiesTable(current, self.tblMeasuresDiagnosticActionProperties, previous)

    @pyqtSignature('QModelIndex, QModelIndex')
    def on_modelMeasuresDiagnosticActions_dataChanged(self, current, previous):
        if current.isValid():
            row = current.row()
            items = self.modelMeasuresDiagnosticActions.items()[row]
            actionId = forceInt(items[0].value('id'))
            enable = 1 if actionId in current.model().enableIdList else 0
            self.saveStatusItem(actionId, 1, enable)

    def on_btnMeasuresStatusButtonBox_apply(self):
        filter = self.getMeasuresFilter(
            self.edtMeasuresStatusBegDate,
            self.edtMeasuresStatusEndDate,
            self.cmbMeasuresStatusGroup,
            self.edtMeasuresStatusOffice,
            self.cmbMeasuresStatusOrgStructure)
        self.updateMeasuresStatus(filter)
        self.focusMeasuresStatusActions()

    def on_btnMeasuresStatusButtonBox_reset(self):
        self.resetMeasuresFilter(
            self.edtMeasuresStatusBegDate,
            self.edtMeasuresStatusEndDate,
            self.cmbMeasuresStatusGroup,
            self.edtMeasuresStatusOffice,
            self.cmbMeasuresStatusOrgStructure)

    def updateMeasuresStatus(self, filter, posToId=None, fieldName=None):
        self.__measuresStatusFilter = filter
        order = self.tblMeasuresStatusActions.order() if self.tblMeasuresStatusActions.order() else ['Action.endDate DESC', 'id']
        self.tblMeasuresStatusActions.setIdList(self.selectMeasuresActions(filter, 0, order, fieldName), posToId)
        self.modelMeasuresStatusActions.enableIdList = self.getProphylaxisPlanningAction(0)

    def focusMeasuresStatusActions(self):
        self.tblMeasuresStatusActions.setFocus(Qt.TabFocusReason)

    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelMeasuresStatusActions_currentRowChanged(self, current, previous):
        self.updateMeasuresPropertiesTable(current, self.tblMeasuresStatusActionProperties, previous)

    @pyqtSignature('QModelIndex, QModelIndex')
    def on_modelMeasuresStatusActions_dataChanged(self, current, previous):
        if current.isValid():
            row = current.row()
            items = self.modelMeasuresStatusActions.items()[row]
            actionId = forceInt(items[0].value('id'))
            enable = 1 if actionId in current.model().enableIdList else 0
            self.saveStatusItem(actionId, 0, enable)

    def on_btnMeasuresCureButtonBox_apply(self):
        filter = self.getMeasuresFilter(
            self.edtMeasuresCureBegDate,
            self.edtMeasuresCureEndDate,
            self.cmbMeasuresCureGroup,
            self.edtMeasuresCureOffice,
            self.cmbMeasuresCureOrgStructure)
        self.updateMeasuresCure(filter)
        self.focusMeasuresCureActions()

    def on_btnMeasuresCureButtonBox_reset(self):
        self.resetMeasuresFilter(
            self.edtMeasuresCureBegDate,
            self.edtMeasuresCureEndDate,
            self.cmbMeasuresCureGroup,
            self.edtMeasuresCureOffice,
            self.cmbMeasuresCureOrgStructure)

    def updateMeasuresCure(self, filter, posToId=None, fieldName=None):
        self.__measuresCureFilter = filter
        order = self.tblMeasuresCureActions.order() if self.tblMeasuresCureActions.order() else ['Action.endDate DESC', 'id']
        self.tblMeasuresCureActions.setIdList(self.selectMeasuresActions(filter, 2, order, fieldName), posToId)
        self.modelMeasuresCureActions.enableIdList = self.getProphylaxisPlanningAction(2)

    def focusMeasuresCureActions(self):
        self.tblMeasuresCureActions.setFocus(Qt.TabFocusReason)

    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelMeasuresCureActions_currentRowChanged(self, current, previous):
        self.updateMeasuresPropertiesTable(current, self.tblMeasuresCureActionProperties, previous)

    @pyqtSignature('QModelIndex, QModelIndex')
    def on_modelMeasuresCureActions_dataChanged(self, current, previous):
        if current.isValid():
            row = current.row()
            items = self.modelMeasuresCureActions.items()[row]
            actionId = forceInt(items[0].value('id'))
            enable = 1 if actionId in current.model().enableIdList else 0
            self.saveStatusItem(actionId, 2, enable)

    def on_btnMeasuresMiscButtonBox_apply(self):
        filter = self.getMeasuresFilter(
            self.edtMeasuresMiscBegDate,
            self.edtMeasuresMiscEndDate,
            self.cmbMeasuresMiscGroup,
            self.edtMeasuresMiscOffice,
            self.cmbMeasuresMiscOrgStructure)
        self.updateMeasuresMisc(filter)
        self.focusMeasuresMiscActions()

    def on_btnMeasuresMiscButtonBox_reset(self):
        self.resetMeasuresFilter(
            self.edtMeasuresMiscBegDate,
            self.edtMeasuresMiscEndDate,
            self.cmbMeasuresMiscGroup,
            self.edtMeasuresMiscOffice,
            self.cmbMeasuresMiscOrgStructure)

    def updateMeasuresMisc(self, filter, posToId=None, fieldName=None):
        self.__measuresMiscFilter = filter
        order = self.tblMeasuresMiscActions.order() if self.tblMeasuresMiscActions.order() else ['Action.endDate DESC', 'id']
        self.tblMeasuresMiscActions.setIdList(self.selectMeasuresActions(filter, 3, order, fieldName), posToId)
        self.modelMeasuresMiscActions.enableIdList = self.getProphylaxisPlanningAction(3)

    def focusMeasuresMiscActions(self):
        self.tblMeasuresMiscActions.setFocus(Qt.TabFocusReason)

    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelMeasuresMiscActions_currentRowChanged(self, current, previous):
        self.updateMeasuresPropertiesTable(current, self.tblMeasuresMiscActionProperties, previous)

    @pyqtSignature('QModelIndex, QModelIndex')
    def on_modelMeasuresMiscActions_dataChanged(self, current, previous):
        if current.isValid():
            row = current.row()
            items = self.modelMeasuresMiscActions.items()[row]
            actionId = forceInt(items[0].value('id'))
            enable = 1 if actionId in current.model().enableIdList else 0
            self.saveStatusItem(actionId, 3, enable)

    def updateMeasuresPropertiesTable(self, index, tbl, previous=None):
        if previous:
            tbl.savePreferencesLoc(previous.row())
        row = index.row()
        record = index.model().getRecordByRow(row) if row >= 0 else None
        if record:
            clientId = self.clientId
            clientSex = self.clientSex
            clientAge = self.clientAge
            action = CAction(record=record)
            tbl.model().setAction(action, clientId, clientSex, clientAge)
            setActionPropertiesColumnVisible(action._actionType, tbl)
            tbl.resizeColumnsToContents()
            tbl.resizeRowsToContents()
            tbl.horizontalHeader().setStretchLastSection(True)
            tbl.loadPreferencesLoc(tbl.preferencesLocal, row)
        else:
            tbl.model().setAction(None, None)

    def saveStatusItem(self, actionId, classCode, enable):
        db = QtGui.qApp.db
        tablePPA = db.table('ProphylaxisPlanning_Action')
        if enable:
            record = tablePPA.newRecord()
            record.setValue('deleted', toVariant(0))
            record.setValue('master_id', toVariant(self.currentItemId))
            record.setValue('action_id', toVariant(actionId))
            record.setValue('classCode', toVariant(classCode))
            db.insertRecord(tablePPA, record)
        else:
            db.deleteRecordSimple(tablePPA,
                                  'action_id=%s and master_id=%s and classCode=%s' % (actionId, self.currentItemId, classCode))


class CControlSurveillanceRegistry:
    def __init__(self):
        self.items = []
        self.diagnosticItems = []
        prefs = QtGui.qApp.preferences.appPrefs
        self.autoPlanning = forceBool(prefs.get('paramPlanningCheck', False))
        if self.autoPlanning:
            self.planningBegDate = forceInt(prefs.get('paramPlanningBegDate', 0))
            self.planningFreq = forceInt(prefs.get('paramPlanningFreq', 6))
            self.planningDuration = forceInt(prefs.get('paramPlanningDuration', 28))

    def getMaxEndDate(self):
        items = self.items
        maxEndDate = None
        for item in items:
            endDate = forceDate(item.value('endDate'))
            if endDate and endDate > maxEndDate:
                maxEndDate = endDate
        return maxEndDate

    def getMaxRemoveDateDate(self):
        items = self.items
        maxRemoveDate = None
        for item in items:
            removeDate = forceDate(item.value('removeDate'))
            if removeDate and removeDate > maxRemoveDate:
                maxRemoveDate = removeDate
        return maxRemoveDate

    def getEmptyRecordEx(self, MKB, prophylaxisPlanningTypeId, clientId, personId, dispanserId):
        db = QtGui.qApp.db
        personId = personId if personId else QtGui.qApp.userId
        table = db.table('ProphylaxisPlanning')
        record = CSqlRecord()
        fields = [table['id'],
                  table['parent_id'],
                  table['MKB'],
                  table['plannedDate'],
                  table['begDate'],
                  table['endDate'],
                  table['visit_id'],
                  table['removeDate'],
                  table['removeReason_id'],
                  table['person_id'],
                  table['orgStructure_id'],
                  table['speciality_id'],
                  table['scene_id'],
                  table['prophylaxisPlanningType_id'],
                  table['client_id'],
                  table['takenDate'],
                  table['dispanser_id'],
                  table['contact'],
                  ]
        for field in fields:
            record.append(QtSql.QSqlField(field.field))
        self.personCache = CTableRecordCache(db, db.forceTable('vrbPerson'), u'*', capacity=None)
        personRecord = self.personCache.get(personId) if personId else None
        orgStructureId = forceInt(personRecord.value('orgStructure_id'))
        specialityId = forceInt(personRecord.value('speciality_id'))

        record.setValue('MKB', toVariant(MKB))
        record.setValue('takenDate', toVariant(QDate()))
        record.setValue('plannedDate', toVariant(QDate.currentDate()))
        record.setValue('person_id', toVariant(personId))
        record.setValue('orgStructure_id', toVariant(orgStructureId))
        record.setValue('speciality_id', toVariant(specialityId))
        record.setValue('scene_id', toVariant(None))
        record.setValue('prophylaxisPlanningType_id', toVariant(prophylaxisPlanningTypeId))
        record.setValue('client_id', toVariant(clientId))
        record.setValue('contact', getClientPhone(clientId))
        record.setValue('dispanser_id', toVariant(dispanserId))
        return record

    def setNewPeriodRecord(self, record):
        if forceDate(record.value('endDate')) and forceDate(record.value('endDate')) > QDate.currentDate():
            begDate = forceDate(record.value('endDate'))
        else:
            begDate = QDate.currentDate()
        if not self.planningBegDate:
            if not begDate == firstMonthDay(begDate):
                begDate = firstMonthDay(begDate.addMonths(1))
        begDate = begDate.addMonths(self.planningFreq)
        record.setValue('begDate', toVariant(begDate))
        record.setValue('endDate', toVariant(begDate.addDays(self.planningDuration)))
        return record

    def loadEx(self, MKB, prophylaxisPlanningTypeId, clientId, personId, dispanserId):
        self.items = []
        record = self.getEmptyRecordEx(MKB, prophylaxisPlanningTypeId, clientId, personId, dispanserId)
        if self.autoPlanning:
            self.setNewPeriodRecord(record)
        if record:
            self.items = [record]

    def appendEx(self, MKB, prophylaxisPlanningTypeId, clientId, personId, dispanserId):
        record = self.getEmptyRecordEx(MKB, prophylaxisPlanningTypeId, clientId, personId, dispanserId)
        if self.autoPlanning:
            self.setNewPeriodRecord(record)
        if record:
            self.items.append(record)

    def load(self, planningSurveillanceId, observed = 1, dispanserId = None):
        db = QtGui.qApp.db
        table = db.table('ProphylaxisPlanning')
        self.items = db.getRecordList(table,
                                      '*',
                                      [table['parent_id'].eq(planningSurveillanceId), table['deleted'].eq(0)],
                                      order=u'ProphylaxisPlanning.begDate, ProphylaxisPlanning.endDate')
        if self.autoPlanning and self.items and observed:
            lastItm = self.items[-1]
            if forceDate(lastItm.value('endDate')) and forceDate(lastItm.value('endDate')) < QDate.currentDate():
                record = self.getEmptyRecordEx(forceString(lastItm.value('MKB')),
                                               forceInt(lastItm.value('prophylaxisPlanningType_id')),
                                               forceInt(lastItm.value('client_id')),
                                               None, # forceInt(lastItm.value('person_id')),
                                               dispanserId)
                record.setValue('parent_id', forceInt(lastItm.value('parent_id')))
                self.setNewPeriodRecord(record)
                self.items.append(record)

    def save(self, planningSurveillanceId):
        db = QtGui.qApp.db
        table = db.table('ProphylaxisPlanning')
        idList = []
        for idx, record in enumerate(self.items):
            if forceDate(record.value('begDate')) and forceDate(record.value('endDate')):
                record.setValue('parent_id', toVariant(planningSurveillanceId))
                id = db.insertOrUpdate(table, record)
                idList.append(id)
        oldIdList = db.getDistinctIdList(table, [table['id']], [table['parent_id'].eq(planningSurveillanceId)])
        db.deleteRecord(table, db.joinAnd([table['parent_id'].eq(planningSurveillanceId), table['id'].notInlist(idList),
                                           table['id'].inlist(oldIdList)]))

    def diagnosticSave(self, clientId):
        db = QtGui.qApp.db
        tableDiagnostic = db.table('Diagnostic')
        for item in self.diagnosticItems:
            MKB = forceStringEx(item.value('MKB'))
            MKBEx = forceStringEx(item.value('MKBEx'))
            TNMS = forceStringEx(item.value('TNMS'))
            morphologyMKB = forceStringEx(item.value('morphologyMKB'))
            diagnosisTypeId = forceRef(item.value('diagnosisType_id'))
            personId = forceRef(item.value('person_id'))
            if not personId:
                personId = QtGui.qApp.userId
                item.setValue('person_id', toVariant(personId))
            specialityId = forceRef(QtGui.qApp.db.translate('Person', 'id', personId, 'speciality_id'))
            item.setValue('speciality_id', toVariant(specialityId))
            diagnosisId = forceRef(item.value('diagnosis_id'))
            characterId = forceRef(item.value('character_id'))
            endDate = forceDate(item.value('endDate'))
            begDate = forceDate(item.value('begDate'))
            date = endDate if endDate else begDate
            diagnosisId, characterId = getDiagnosisId2(
                date,
                personId,
                clientId,
                diagnosisTypeId,
                MKB,
                MKBEx,
                forceRef(item.value('character_id')),
                forceRef(item.value('dispanser_id')),
                forceRef(item.value('traumaType_id')),
                diagnosisId,
                forceRef(item.value('id')),
                QtGui.qApp.defaultIsManualSwitchDiagnosis(),
                forceBool(item.value('handleDiagnosis')),
                TNMS=TNMS,
                morphologyMKB=morphologyMKB,
                dispanserBegDate=forceDate(item.value('endDate')),
                exSubclassMKB=forceStringEx(item.value('exSubclassMKB')))
            item.setValue('diagnosis_id', toVariant(diagnosisId))
            item.setValue('TNMS', toVariant(TNMS))
            item.setValue('character_id', toVariant(characterId))

            record = tableDiagnostic.newRecord()
            for i in xrange(item.count()):
                record.setValue(i, item.value(record.fieldName(i)))
            db.updateRecord(tableDiagnostic, record)

    def diagnosisUpdateDispanserBegDate(self, clientId, MKB, takenDate):
        db = QtGui.qApp.db
        tableDiagnosis = db.table('Diagnosis')
        updateCond = [
            tableDiagnosis['client_id'].eq(clientId),
            tableDiagnosis['deleted'].eq(0),
            tableDiagnosis['MKB'].eq(MKB),
        ]
        updateCols = [
            tableDiagnosis['dispanserBegDate'].eq(takenDate),
        ]
        db.updateRecords(tableDiagnosis, updateCols, updateCond)

    def getItems(self):
        return self.items

    def setItems(self, items, diagnosticItems):
        self.items = items
        self.diagnosticItems = diagnosticItems

    def getDiagnosticItems(self):
        return self.diagnosticItems

    
    def saveItems(self):
        db = QtGui.qApp.db
        mkbByDate = []
        for record in self.items:
            begDate = forceDate(record.value(u'begDate'))
            if ((forceString(record.value('MKB')), begDate.year(), begDate.month())) in mkbByDate:
                continue
            prophylaxisPlanningTypeIds = db.getIdList(u'rbProphylaxisPlanningType', u'rbProphylaxisPlanningType.id', u'code like "%ДН%"')
            if not forceInt(record.value(u'prophylaxisPlanningType_id')) in prophylaxisPlanningTypeIds:
                continue
            currentDate = QDate.currentDate()
            if currentDate.year() > begDate.year() or (currentDate.year() == begDate.year() and currentDate.month() > begDate.month()):
                continue
            #plannedDate = forceDate(record.value(u'plannedDate'))
            #if plannedDate.year() != currentDate.year():
            #    continue
            removeDate = forceDate(record.value(u'removeDate'))
            if removeDate:
                continue
            clientRecord = db.getRecordEx(u'Client', u'age(Client.birthDate, {}) as age'.format(db.formatDate(forceDate(record.value('begDate')))), u'Client.id = {}'.format(forceInt(record.value('client_id'))))
            if forceInt(clientRecord.value('age')) < 18:
                continue
            dispNabMKBRecord = db.getRecordEx(u'soc_DispNabMKB', u'id', u'soc_DispNabMKB.code = "{}" and (soc_DispNabMKB.endDate is NULL or soc_DispNabMKB.endDate > {})'.format(forceString(record.value('MKB')), db.formatDate(forceDate(record.value('begDate')))))
            if not dispNabMKBRecord:
                continue
            tableDiagnosisDispansPlaned = db.table('DiagnosisDispansPlaned')
            tableDiagnosis = db.table('Diagnosis')
            queryTable = tableDiagnosisDispansPlaned.leftJoin(tableDiagnosis, tableDiagnosis['id'].eq(tableDiagnosisDispansPlaned['diagnosis_id']))
            cond = [
                tableDiagnosisDispansPlaned['deleted'].eq(0),
                'year = year({})'.format(db.formatDate(forceDate(record.value('begDate')))),
                'month = month({})'.format(db.formatDate(forceDate(record.value('begDate')))),
                tableDiagnosisDispansPlaned['client_id'].eq(forceInt(record.value('client_id'))),
                tableDiagnosis['MKB'].eq(forceString(record.value('MKB')))
            ]
            diagnosisDispansPlanedRecord = db.getRecordEx(queryTable, u'DiagnosisDispansPlaned.id', cond)
            if diagnosisDispansPlanedRecord:
                continue
            tableRBDispanser = db.table('rbDispanser')
            tableRBDiagnosisType = db.table('rbDiagnosisType')
            queryTable = tableDiagnosis.leftJoin(tableRBDispanser, tableRBDispanser['id'].eq(tableDiagnosis['dispanser_id']))
            queryTable = queryTable.leftJoin(tableRBDiagnosisType, tableRBDiagnosisType['id'].eq(tableDiagnosis['diagnosisType_id']))
            cond = [
                tableDiagnosis['deleted'].eq(0),
                tableDiagnosis['MKB'].eq(forceString(record.value('MKB'))),
                tableDiagnosis['client_id'].eq(forceInt(record.value('client_id'))),
                tableRBDispanser['observed'].eq(1),
                tableRBDiagnosisType['code'].inlist(['2','9'])
            ]
            diagnosisRecord = db.getRecordEx(queryTable, u'max(Diagnosis.id) as diagId', cond)
            if forceInt(diagnosisRecord.value('diagId')):
                table = db.table('DiagnosisDispansPlaned')
                newRecord = table.newRecord()
                newRecord.setValue('createDatetime', toVariant(currentDate))
                newRecord.setValue('createPerson_id', QtGui.qApp.userId)
                newRecord.setValue('modifyDatetime', toVariant(currentDate))
                newRecord.setValue('modifyPerson_id', QtGui.qApp.userId)
                newRecord.setValue('deleted', toVariant(0))
                newRecord.setValue('client_id', record.value('client_id'))
                newRecord.setValue('diagnosis_id', diagnosisRecord.value('diagId'))
                newRecord.setValue('person_id', record.value('person_id'))
                newRecord.setValue('year', begDate.year())
                newRecord.setValue('month', begDate.month())
                newRecord.setValue('planVisits', toVariant(1))
                newRecord.setValue('isExport', toVariant(1))
                db.insertRecord(table, newRecord)
                mkbByDate.append((forceString(record.value('MKB')), begDate.year(), begDate.month()))
        

class CPlanningSurveillanceModel(CInDocTableModel):
    class CLocMKBDiagNameColumn(CInDocTableCol):
        def __init__(self, title, fieldName, width, **params):
            CInDocTableCol.__init__(self, title, fieldName, width, **params)
            self.cache = {}

        def toString(self, val, record):
            MKB = forceString(val)
            if self.cache.has_key(MKB):
                descr = self.cache[MKB]
            else:
                descr = getMKBName(MKB) if MKB else ''
                self.cache[MKB] = descr
            return QVariant((MKB + ': ' + descr) if MKB else '')

        def invalidateRecordsCache(self):
            self.cache.invalidate()

    Col_MKB = 0
    Col_DispanserId = 2
    Col_TakenDate = 3
    Col_PersonId = 4
    Col_RemoveDate = 5
    Col_RemoveReasonId = 6

    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'ProphylaxisPlanning', 'id', 'parent_id', parent)
        db = QtGui.qApp.db
        self.personCache = CTableRecordCache(db, db.forceTable('vrbPersonWithSpeciality'), u'*', capacity=None)
        self.addCol(CICDExInDocTableCol(u'МКБ', 'MKB', 7), QVariant.String).setReadOnly(True)
        self.addExtCol(CPlanningSurveillanceModel.CLocMKBDiagNameColumn(u'Наименование', 'MKB', 20), QVariant.String).setReadOnly()
        self.addCol(CRBInDocTableCol(u'ДН', 'dispanser_id', 10, 'rbDispanser')).setReadOnly(True)
        self.addCol(CDateInDocTableCol(u'Дата взятия', 'takenDate', 10)).setReadOnly(True)
        self.addCol(CPersonInDocTableCol(u'Врач', 'person_id', 20, 'vrbPersonWithSpeciality')).setReadOnly(True)
        self.addCol(CDateInDocTableCol(u'Дата снятия', 'removeDate', 10)).setReadOnly(True)
        self.addCol(CRBInDocTableCol(u'Причина снятия', 'removeReason_id', 10, 'rbSurveillanceRemoveReason')).setReadOnly(True)
        self.addHiddenCol('orgStructure_id')
        self.addHiddenCol('speciality_id')
        self.addHiddenCol('scene_id')
        self.addHiddenCol('prophylaxisPlanningType_id')
        self.addHiddenCol('client_id')
        self.addHiddenCol('contact')
        self.eventEditor = None
        self.readOnly = False
        self.diagnosticRecords = {}
        self.diagnosticGroupRecords = {}
        self.prophylaxisPlanningTypeId = None
        self.MKBs = []
        self.parentIdToDel = []
        self.clientId = None
        self.clientDeathDate = None
        self.removeDispanserId = None
        self.removeReasonDate = None
        application = QtGui.qApp
        if application.preferences.appPrefs.get('paramPlanningCheck', False):
            self.planningBegDate = application.preferences.appPrefs.get('paramPlanningBegDate', 0)
            self.planningFreq = application.preferences.appPrefs.get('paramPlanningFreq', 6)
            self.planningDuration = application.preferences.appPrefs.get('paramPlanningDuration', 28)

    def setDiagnosticRecords(self, diagnosticRecords):
        self.diagnosticRecords = diagnosticRecords

    def setDiagnosticGroupRecords(self, diagnosticGroupRecords):
        self.diagnosticGroupRecords = diagnosticGroupRecords

    def setClientId(self, clientId):
        self.clientId = clientId
        if self.clientId:
            self.clientDeathDate = getDeathDate(self.clientId)

    def setMKB(self, MKB):
        self.MKB = MKB

    def setMKBs(self, MKBs):
        self.MKBs = MKBs

    def setProphylaxisPlanningTypeId(self, prophylaxisPlanningTypeId):
        self.prophylaxisPlanningTypeId = prophylaxisPlanningTypeId

    def getEmptyRecord(self):
        result = CInDocTableModel.getEmptyRecord(self)
        result.setValue('prophylaxisPlanningType_id', toVariant(self.prophylaxisPlanningTypeId))
        result.setValue('client_id', toVariant(self.clientId))
        result.setValue('takenDate', toVariant(QDate()))
        return result

    def removeRow(self, row, parentIndex=QModelIndex()):
        self.parentIdToDel.append(forceRef(self.items()[row].value('id')))
        return self.removeRows(row, 1, parentIndex)

    def setEventEditor(self, eventEditor):
        self.eventEditor = eventEditor

    def setReadOnly(self, value=True):
        self.readOnly = value

    def flags(self, index):
        if self.readOnly:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return CInDocTableModel.flags(self, index)

    def cellReadOnly(self, index):
        column = index.column()
        row = index.row()
        if 0 <= row < len(self._items):
            record = self._items[row]
            if column == CPlanningSurveillanceModel.Col_MKB:
                return False
            elif not forceStringEx(record.value('MKB')):
                return True
        elif column != CPlanningSurveillanceModel.Col_MKB:
            return True
        return False

    def setData(self, index, value, role=Qt.EditRole):
        result = CInDocTableModel.setData(self, index, value, role)
        if role == Qt.EditRole and result:
            row = index.row()
            column = index.column()
            if 0 <= row < len(self._items):
                item = self._items[row]
                personId = forceRef(item.value('person_id'))
                personRecord = self.personCache.get(personId) if personId else None
                orgStructureId = forceRef(item.value('orgStructure_id'))
                specialityId = forceRef(item.value('speciality_id'))
                if column == self.Col_MKB and not hasattr(item, 'controlSurveillance'):
                    MKB = forceStringEx(item.value('MKB'))
                    dispanserId = forceInt(item.value('dispanser_id'))
                    if MKB:
                        item.controlSurveillance = CControlSurveillanceRegistry()
                        item.controlSurveillance.loadEx(MKB, self.prophylaxisPlanningTypeId, self.clientId, personId,
                                                        dispanserId)
                elif column == self.Col_PersonId:
                    if not personRecord:
                        orgStructureId = toVariant(None)
                        specialityId = toVariant(None)
                    self.setValue(row, 'orgStructure_id', orgStructureId)
                    self.setValue(row, 'speciality_id', specialityId)
        return result

    def loadItems(self, masterId):
        self._items = []
        MKBs = {}
        if self.MKBs and self.clientId:
            db = QtGui.qApp.db
            tableDiagnosis = db.table('Diagnosis')
            tableDiagnostic = db.table('Diagnostic')
            tableRBDispanser = db.table('rbDispanser')
            cols = []
            for col in self._cols:
                if not col.external():
                    cols.append(col.fieldName())
            cols.append(self._idFieldName)
            cols.append(self._masterIdFieldName)
            if self._idxFieldName:
                cols.append(self._idxFieldName)
            for col in self._hiddenCols:
                cols.append(col)
            table = self._table
            filter = [table['parent_id'].isNull(),
                      table['client_id'].eq(self.clientId)]
            condMKB = []
            tempMKBs = []
            for MKB in self.MKBs:
                diag = MKB
                if len(MKB) >= 3:
                    diag = MKB[:3]
                if diag and diag not in tempMKBs:
                    tempMKBs.append(diag)
            for tempMKB in tempMKBs:
                condMKB.append(table['MKB'].like(tempMKB + '%'))
            filter.append(db.joinOr(condMKB))
            if self._filter:
                filter.append(self._filter)
            if table.hasField('deleted'):
                filter.append(table['deleted'].eq(0))
            if self._idxFieldName:
                order = [self._idxFieldName, table['takenDate'].name() + u'ASC', table['removeDate'].name() + u'DESC']
            else:
                order = [table['takenDate'].name() + u'ASC', table['removeDate'].name() + u'DESC']
            self._items = db.getRecordList(table, cols, filter, order)
            if self._extColsPresent:
                extSqlFields = []
                for col in self._cols:
                    if col.external():
                        fieldName = col.fieldName()
                        if fieldName not in cols:
                            extSqlFields.append(QtSql.QSqlField(fieldName, col.valueType()))
                if extSqlFields:
                    for item in self._items:
                        for field in extSqlFields:
                            item.append(field)
            for item in self._items:
                dispanserId = forceRef(item.value('dispanser_id'))
                observed = 0
                if dispanserId:
                    recObserved = db.getRecordEx(tableRBDispanser, [tableRBDispanser['observed']],
                                                 [tableRBDispanser['id'].eq(dispanserId)])
                    observed = forceInt(recObserved.value('observed')) if recObserved else 0
                item.controlSurveillance = CControlSurveillanceRegistry()
                item.controlSurveillance.load(forceRef(item.value('id')), observed, dispanserId)
                takenDate = forceDate(item.value('takenDate')) if forceDate(
                    item.value('takenDate')) else QDate()
                MKB = forceStringEx(item.value('MKB'))
                if not item.controlSurveillance.items and observed:
                    item.controlSurveillance.loadEx(MKB, self.prophylaxisPlanningTypeId, self.clientId,
                                                    None, #forceRef(item.value('person_id')),
                                                    dispanserId)
                setDate = None
                periodEnded = False
                diagnosticRecord = self.diagnosticRecords.get(MKB, None)
                if not takenDate:
                    if diagnosticRecord:
                        setDate = forceDate(diagnosticRecord.value('setDate'))
                    if not setDate and diagnosticRecord:
                        diagnosticId = forceRef(diagnosticRecord.value('id'))
                        if diagnosticId:
                            diagnosticRecord = db.getRecordEx(tableDiagnostic, [tableDiagnostic['setDate']],
                                                              [tableDiagnostic['id'].eq(diagnosticId),
                                                               tableDiagnostic['deleted'].eq(0)])
                            setDate = forceDate(diagnosticRecord.value('setDate')) if diagnosticRecord else None
                    dispanserBegDate = forceDate(
                        diagnosticRecord.value('dispanserBegDate')) if diagnosticRecord else QDate()
                else:
                    dispanserBegDate = takenDate
                if diagnosticRecord:
                    diagnosticDispanserId = forceRef(diagnosticRecord.value('diagnosisDispanser_id'))
                    diagnosticRecObserved = db.getRecordEx(tableRBDispanser, [tableRBDispanser['observed']],
                                                [tableRBDispanser['id'].eq(diagnosticDispanserId)])
                    diagnosticObserved = forceInt(diagnosticRecObserved.value('observed')) if diagnosticRecObserved else 0
                    if diagnosticObserved and not observed and forceDate(item.value('removeDate')):
                        periodEnded = True
                if dispanserBegDate:
                    self._items[self._items.index(item)].setValue('takenDate', dispanserBegDate)
                if MKB and MKB not in MKBs and not periodEnded and (
                        (takenDate and setDate and takenDate >= setDate) or observed == 1 or dispanserId or self.clientDeathDate):
                    MKB3 = MKB
                    if len(MKB) >= 3:
                        MKB3 = MKB[:3]
                    MKBs[MKB3] = observed
            for MKB in self.MKBs:
                MKBFind = MKB
                if len(MKB) >= 3:
                    MKBFind = MKB[:3]
                needGroup = 0
                if (MKBFind not in MKBs.keys() or not MKBs[MKBFind]):
                    tableDiagnosisType = db.table('rbDiagnosisType')
                    tableDispanserDS = db.table('rbDispanser').alias('DDS')
                    tableDispanserDC = db.table('rbDispanser').alias('DDC')
                    queryTable = tableDiagnosis.leftJoin(tableDiagnostic, tableDiagnosis['id'].eq(tableDiagnostic['diagnosis_id']))
                    queryTable = queryTable.leftJoin(tableDispanserDC, tableDispanserDC['id'].eq(tableDiagnostic['dispanser_id']))
                    queryTable = queryTable.leftJoin(tableDispanserDS, tableDispanserDS['id'].eq(tableDiagnosis['dispanser_id']))
                    queryTable = queryTable.leftJoin(tableDiagnosisType, tableDiagnosisType['id'].eq(tableDiagnosis['diagnosisType_id']))
                    cond = [tableDiagnosis['MKB'].eq(MKB),
                            tableDiagnosis['deleted'].eq(0),
                            tableDiagnostic['deleted'].eq(0),
                            tableDiagnosis['client_id'].eq(self.clientId),
                            tableDispanserDC['observed'].eq(1),
                            tableDispanserDS['observed'].eq(1),
                            tableDiagnostic['event_id'].isNotNull(),
                            tableDiagnosisType['code'].inlist(['1','2','9','98'])
                            ]
                    cols = [u'Diagnostic.*',
                            tableDiagnosis['MKB'],
                            tableDiagnosis['MKBEx'],
                            tableDiagnosis['dispanserBegDate'],
                            tableDiagnosis['dispanserPerson_id'],
                            tableDiagnosis['dispanser_id'].alias('diagnosisDispanser_id'),
                            tableDiagnostic['endDate'],
                            'max(Diagnosis.endDate) as maxDiagnosisEndDate',
                            'max(Diagnostic.endDate) as maxDiagnosticEndDate'
                            ]
                    diagRecord = db.getRecordEx(queryTable, cols, cond, order='maxDiagnosisEndDate DESC, maxDiagnosticEndDate DESC')
                    if diagRecord and forceInt(diagRecord.value('id')):
                        needGroup = 1
                        self.diagnosticRecords[MKB] = diagRecord
                if needGroup:
                    record = CInDocTableModel.getEmptyRecord(self)
                    personId = None
                    specialityId = None
                    orgStructureId = None
                    takenDate = None
                    diagnosticRecord = self.diagnosticRecords.get(MKB, None)
                    if diagnosticRecord:
                        takenDate = forceDate(diagnosticRecord.value('dispanserBegDate')) if forceDate(diagnosticRecord.value('dispanserBegDate')) else QDate()
                        personId = forceRef(diagnosticRecord.value('dispanserPerson_id'))
                        if not personId:
                            diagnosisId = forceRef(diagnosticRecord.value('diagnosis_id'))
                            diagnosisRecord = db.getRecordEx(tableDiagnosis, [tableDiagnosis['dispanserBegDate'],
                                                                              tableDiagnosis['dispanserPerson_id']],
                                                             tableDiagnosis['id'].eq(diagnosisId))
                            if diagnosisRecord:
                                personId = forceRef(diagnosisRecord.value('dispanserPerson_id'))
                                takenDate = forceDate(diagnosisRecord.value('dispanserBegDate')) if forceDate(diagnosisRecord.value('dispanserBegDate')) else QDate()

                        record.setValue('person_id', toVariant(personId))
                        personRecord = self.personCache.get(personId) if personId else None
                        if personRecord:
                            orgStructureId = forceRef(personRecord.value('orgStructure_id'))
                            specialityId = forceRef(personRecord.value('speciality_id'))
                        record.setValue('orgStructure_id', toVariant(orgStructureId))
                        record.setValue('speciality_id', toVariant(specialityId))
                        record.setValue('MKB', diagnosticRecord.value('MKB'))
                    dispanserId = diagnosticRecord.value('diagnosisDispanser_id')
                    record.setValue('dispanser_id', dispanserId)
                    record.setValue('scene_id', toVariant(None))
                    record.setValue('prophylaxisPlanningType_id', toVariant(self.prophylaxisPlanningTypeId))
                    record.setValue('client_id', toVariant(self.clientId))
                    record.setValue('takenDate', toVariant(takenDate))
                    record.controlSurveillance = CControlSurveillanceRegistry()
                    record.controlSurveillance.loadEx(MKB, self.prophylaxisPlanningTypeId, self.clientId, None, dispanserId)
                    MKBs[MKBFind] = 1
                    self._items.append(record)
        self.reset()

    def saveItems(self, masterId=None):
        db = QtGui.qApp.db
        table = self._table
        masterId = toVariant(masterId)
        masterIdFieldName = self._masterIdFieldName
        idFieldName = self._idFieldName
        idList = {}
        for idx, record in enumerate(self._items):
            record.setValue(masterIdFieldName, masterId)
            record.setValue('client_id', toVariant(self.clientId))
            if self._idxFieldName:
                record.setValue(self._idxFieldName, toVariant(idx))
            if self._extColsPresent:
                outRecord = self.removeExtCols(record)
            else:
                outRecord = record
            id = db.insertOrUpdate(table, outRecord)
            record.setValue(idFieldName, toVariant(id))
            idList[idx] = id
            self.saveDependence(idx, id)
            record.controlSurveillance.save(forceRef(record.value('id')))
            record.controlSurveillance.diagnosticSave(self.clientId)

        if self.parentIdToDel:
            filter = [table['client_id'].eq(self.clientId),
                      table['deleted'].eq(0)]
            if forceRef(masterId):
                filter.append(table[masterIdFieldName].eq(masterId))
            filter.append(db.joinOr([db.joinAnd([table[idFieldName].inlist(self.parentIdToDel), 
                                                 table[masterIdFieldName].isNull()]), 
                                     table[masterIdFieldName].inlist(self.parentIdToDel)]))
            if self._filter:
                filter.append(self._filter)
            db.deleteRecord(table, filter)

        if self.removeDispanserId and self.removeReasonDate:
            diagnosisList = updateDiagnosisRecords(self.clientId, self.removeDispanserId, self.removeReasonDate)
            if diagnosisList:
                createDiagnosticRecords(diagnosisList, clientId=self.clientId, removeDispanserId=self.removeDispanserId, removeDate=self.removeReasonDate)
        return idList

class CControlSurveillanceModel(CInDocTableModel):
    Col_MKB = 0
    Col_PlannedDate = 1
    Col_BegDate = 2
    Col_EndDate = 3
    Col_VisitId = 4
    Col_PersonId = 5
    Col_OrgStructure = 6
    #Col_RemoveDate = 7
    #Col_RemoveReasonId = 8

    class CVisitInDocTableCol(CInDocTableCol):
        def __init__(self, title, fieldName, width, **params):
            CInDocTableCol.__init__(self, title, fieldName, width, **params)
            self.caches = {}
            self.MKBCaches = {}

        def toString(self, val, record):
            visitId = forceRef(val)
            date = u''
            db = QtGui.qApp.db
            if visitId:
                visitRecord = self.caches.get(visitId, None)
                if not visitRecord:
                    table = db.table('Visit')
                    visitRecord = db.getRecordEx(table, '*', [table['id'].eq(visitId)])
                if visitRecord:
                    date = forceStringEx(forceDate(visitRecord.value('date')))
                    self.caches[visitId] = visitRecord
                    MKB = forceStringEx(record.value('MKB'))
                    if MKB:
                        MKBRecord = self.MKBCaches.get((visitId, MKB), None)
                        if not MKBRecord:
                            table = db.table('Visit')
                            tableEvent = db.table('Event')
                            tableDiagnosis = db.table('Diagnosis')
                            tableDiagnostic = db.table('Diagnostic')
                            tableDispanser = db.table('rbDispanser')
                            queryTable = tableEvent.innerJoin(table, table['event_id'].eq(tableEvent['id']))
                            queryTable = queryTable.innerJoin(tableDiagnostic,
                                                              tableDiagnostic['event_id'].eq(tableEvent['id']))
                            queryTable = queryTable.innerJoin(tableDiagnosis,
                                                              tableDiagnosis['id'].eq(tableDiagnostic['diagnosis_id']))
                            queryTable = queryTable.innerJoin(tableDispanser,
                                                              tableDispanser['id'].eq(tableDiagnostic['dispanser_id']))
                            cond = [table['id'].eq(visitId),
                                    db.joinOr(
                                        [tableDiagnosis['MKB'].eq(MKB), tableDiagnosis['MKB'].like(MKB[:3] + '%')]),
                                    tableDiagnostic['dispanser_id'].isNotNull(),
                                    table['deleted'].eq(0),
                                    tableDiagnosis['deleted'].eq(0),
                                    tableDiagnostic['deleted'].eq(0),
                                    tableEvent['deleted'].eq(0)
                                    ]
                            MKBRecord = db.getRecordEx(queryTable, 'Diagnosis.MKB, Diagnostic.dispanser_id', cond)
                            if MKBRecord:
                                self.MKBCaches[(visitId, MKB)] = MKBRecord
            return toVariant(date)

        def setEditorData(self, editor, value, record):
            editor.setValue(forceRef(value))

        def getEditorData(self, editor):
            return toVariant(editor.value())

    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'ProphylaxisPlanning', 'id', 'parent_id', parent)
        self._parent = parent
        db = QtGui.qApp.db
        self.personCache = CTableRecordCache(db, db.forceTable('vrbPersonWithSpeciality'), u'*', capacity=None)
        self.addCol(CICDExInDocTableCol(u'МКБ', 'MKB', 7), QVariant.String)
        self.addCol(CDateInDocTableCol(u'Дата планирования', 'plannedDate', 10, canBeEmpty=True))
        self.addCol(CDateInDocTableCol(u'Дата начала периода', 'begDate', 10, canBeEmpty=True))
        self.addCol(CDateInDocTableCol(u'Дата окончания периода', 'endDate', 10, canBeEmpty=True))
        self.addCol(CControlSurveillanceModel.CVisitInDocTableCol(u'Явился', 'visit_id', 20))
        self.addCol(CPersonFindInDocTableCol(u'Врач', 'person_id', 20, 'vrbPersonWithSpeciality'))
        self.addCol(CPersonInDocTableCol(u'Подразделение', 'orgStructure_id', 20, 'OrgStructure')).setReadOnly(True)
        self.addHiddenCol('removeDate')
        self.addHiddenCol('removeReason_id')
        # self.addHiddenCol('person_id')
        # self.addHiddenCol('orgStructure_id')
        self.addHiddenCol('speciality_id')
        self.addHiddenCol('scene_id')
        self.addHiddenCol('prophylaxisPlanningType_id')
        self.addHiddenCol('client_id')
        self.addHiddenCol('takenDate')
        self.addHiddenCol('contact')
        self.addHiddenCol('dispanser_id')
        self.eventEditor = None
        self.readOnly = False
        self.diagnosticRecords = {}
        self.diagnosticGroupRecords = {}
        self.diagnosticItems = []
        self.prophylaxisPlanningTypeId = None
        self.MKBs = []
        self.clientId = None
        self.eventId = None
        self.getDispanserRecords()
        self.getRBDispanserConsists()
        self.getRBDispanserRemoved()
        self.getSurveillanceRemoveReason()
        prefs = QtGui.qApp.preferences.appPrefs
        self.autoPlanning = forceBool(prefs.get('paramPlanningCheck', False))
        if self.autoPlanning:
            self.planningBegDate = prefs.get('paramPlanningBegDate', 0)
            self.planningFreq = prefs.get('paramPlanningFreq', 6)
            self.planningDuration = prefs.get('paramPlanningDuration', 28)

    def getDispanserRecords(self):
        self.dispanserRecords = {}
        db = QtGui.qApp.db
        tableRBDispanser = db.table('rbDispanser')
        records = db.getRecordList(tableRBDispanser, '*')
        for record in records:
            dispanserId = forceRef(record.value('id'))
            if dispanserId:
                self.dispanserRecords[dispanserId] = record

    def getRBDispanserConsists(self):
        db = QtGui.qApp.db
        tableRBDispanser = db.table('rbDispanser')
        record = db.getRecordEx(tableRBDispanser, [tableRBDispanser['id']], [tableRBDispanser['code'].eq(1)])
        self.rbDispanserConsists = forceRef(record.value('id')) if record else None

    def getRBDispanserRemoved(self):
        db = QtGui.qApp.db
        tableRBDispanser = db.table('rbDispanser')
        record = db.getRecordEx(tableRBDispanser, [tableRBDispanser['id']], [tableRBDispanser['name'].like(u'%снят%')])
        self.rbDispanserRemoved = forceRef(record.value('id')) if record else None

    def getSurveillanceRemoveReason(self):
        self.rbSurveillanceRemoveReason = {}
        db = QtGui.qApp.db
        tableSurveillanceRemoveReason = db.table('rbSurveillanceRemoveReason')
        records = db.getRecordList(tableSurveillanceRemoveReason, '*')
        for record in records:
            surveillanceRemoveReasonId = forceRef(record.value('id'))
            if surveillanceRemoveReasonId:
                self.rbSurveillanceRemoveReason[surveillanceRemoveReasonId] = record

    def getEventVisitMAXDate(self, eventId, row):
        visitIdList = []
        prophylaxisPlanningIdList = []
        removeDate = None
        visitRecords = None
        items = self.items()
        for i, item in enumerate(items):
            if i != row:
                visitId = forceRef(item.value('visit_id'))
                if visitId and visitId not in visitIdList:
                    visitIdList.append(visitId)
                prophylaxisPlanningId = forceRef(item.value('id'))
                if prophylaxisPlanningId and prophylaxisPlanningId not in prophylaxisPlanningIdList:
                    prophylaxisPlanningIdList.append(prophylaxisPlanningId)
            if not removeDate:
                removeDate = forceDate(item.value('removeDate'))
        record = items[row]
        takenDate = forceDate(record.value('takenDate'))
        MKB = forceStringEx(record.value('MKB'))
        MKB = MKB[:3]
        clientId = forceRef(record.value('client_id'))
        if takenDate and MKB and clientId:
            db = QtGui.qApp.db
            table = db.table('Visit')
            tableEvent = db.table('Event')
            tableDiagnosis = db.table('Diagnosis')
            tableDiagnostic = db.table('Diagnostic')
            tableDispanser = db.table('rbDispanser')
            queryTable = tableEvent.innerJoin(table, table['event_id'].eq(tableEvent['id']))
            queryTable = queryTable.innerJoin(tableDiagnostic, tableDiagnostic['event_id'].eq(tableEvent['id']))
            queryTable = queryTable.innerJoin(tableDiagnosis, tableDiagnosis['id'].eq(tableDiagnostic['diagnosis_id']))
            queryTable = queryTable.innerJoin(tableDispanser, tableDispanser['id'].eq(tableDiagnostic['dispanser_id']))
            cond = [table['date'].dateGe(takenDate),
                    tableDiagnosis['client_id'].eq(clientId),
                    tableEvent['id'].eq(eventId),
                    tableEvent['client_id'].eq(clientId),
                    tableDiagnosis['MKB'].like(MKB[:3] + '%'),
                    tableDiagnostic['dispanser_id'].isNotNull(),
                    table['deleted'].eq(0),
                    tableDiagnosis['deleted'].eq(0),
                    tableDiagnostic['deleted'].eq(0),
                    tableEvent['deleted'].eq(0)
                    ]
            if visitIdList:
                cond.append(table['id'].notInlist(visitIdList))
            if removeDate:
                cond.append(table['date'].dateLe(removeDate))
            cond.append(u'''NOT EXISTS(SELECT ProphylaxisPlanning.id
            FROM ProphylaxisPlanning
            WHERE ProphylaxisPlanning.visit_id = Visit.id
            AND ProphylaxisPlanning.MKB LIKE '%s'
            AND ProphylaxisPlanning.deleted = 0 %s)''' % (MKB[:3] + '%', (u'AND ProphylaxisPlanning.id NOT IN (%s)' % (
                u','.join(
                    str(ppId) for ppId in prophylaxisPlanningIdList if ppId))) if prophylaxisPlanningIdList else u''))
            visitRecords = db.getMax(queryTable, table['date'].name(), cond)
        return forceDate(visitRecords) if visitRecords else None

    def setDiagnosticRecords(self, diagnosticRecords):
        self.diagnosticRecords = diagnosticRecords

    def setDiagnosticGroupRecords(self, diagnosticGroupRecords):
        self.diagnosticGroupRecords = diagnosticGroupRecords

    def setClientId(self, clientId):
        self.clientId = clientId

    def setEventId(self, eventId):
        self.eventId = eventId

    def setMKB(self, MKB):
        self.MKB = MKB

    def setMKBs(self, MKBs):
        self.MKBs = MKBs

    def setItems(self, items, diagnosticItems):
        CInDocTableModel.setItems(self, items)
        self.diagnosticItems = diagnosticItems

    def setProphylaxisPlanningTypeId(self, prophylaxisPlanningTypeId):
        self.prophylaxisPlanningTypeId = prophylaxisPlanningTypeId

    def getEmptyRecord(self):
        result = CInDocTableModel.getEmptyRecord(self)
        rowCount = len(self._items)
        if rowCount > 0:
            item = self._items[rowCount - 1]
            MKB = forceStringEx(item.value('MKB'))
            if MKB:
                result.setValue('MKB', toVariant(MKB))
                result.setValue('takenDate', item.value('takenDate'))
                result.setValue('dispanser_id', item.value('dispanser_id'))
        result.setValue('prophylaxisPlanningType_id', toVariant(self.prophylaxisPlanningTypeId))
        result.setValue('client_id', toVariant(self.clientId))
        result.setValue('plannedDate', toVariant(QDate.currentDate()))
        return result

    def setEventEditor(self, eventEditor):
        self.eventEditor = eventEditor

    def setReadOnly(self, value=True):
        self.readOnly = value

    def flags(self, index):
        if self.readOnly:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return CInDocTableModel.flags(self, index)

    def getMaxVisitDate(self):
        items = self._items
        maxDate = None
        for item in items:
            visitId = forceRef(item.value('visit_id'))
            if visitId:
                visitCache = self.cols()[self.Col_VisitId].caches
                visitRecord = visitCache.get(visitId, None) if visitId else None
                if not visitRecord:
                    db = QtGui.qApp.db
                    table = db.table('Visit')
                    visitRecord = db.getRecordEx(table, '*', [table['id'].eq(visitId), table['deleted'].eq(0)])
                    if visitRecord:
                        self.cols()[self.Col_VisitId].caches[visitId] = visitRecord
                if visitRecord:
                    date = forceDate(visitRecord.value('date'))
                    if date and date > maxDate:
                        maxDate = date
        return maxDate

    def getMaxEndDate(self):
        items = self._items
        maxEndDate = None
        for item in items:
            endDate = forceDate(item.value('endDate'))
            if endDate and endDate > maxEndDate:
                maxEndDate = endDate
        return maxEndDate

    def getLastVisitRow(self):
        rows = []
        items = self._items
        for row, item in enumerate(items):
            visitId = forceRef(item.value('visit_id'))
            if visitId and row not in rows:
                rows.append(row)
        rows.sort()
        lenRows = len(rows)
        if lenRows > 0:
            return rows[lenRows - 1]
        return -1

    def getMaxRemoveDate(self):
        items = self._items
        maxRemoveDate = None
        for item in items:
            removeDate = forceDate(item.value('removeDate'))
            if removeDate and removeDate > maxRemoveDate:
                maxRemoveDate = removeDate
        return maxRemoveDate

    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.EditRole:
            row = index.row()
            column = index.column()
            orgStructureId = None
            specialityId = None
            if row == len(self._items):
                if value.isNull():
                    return False
                maxRemoveDate = self.getMaxRemoveDate()
                maxEndDate = self.getMaxEndDate()
                if maxRemoveDate >= maxEndDate:
                    return False
            result = CInDocTableModel.setData(self, index, value, role)
            if result and 0 <= row < len(self._items):
                item = self._items[row]
                sceneId = toVariant(None)
                userId = QtGui.qApp.userId
                if column == self.Col_VisitId:
                    visitId = forceRef(item.value('visit_id'))
                    if visitId:
                        visitCache = self.cols()[column].caches
                        visitRecord = visitCache.get(visitId, None) if visitId else None
                        if not visitRecord:
                            db = QtGui.qApp.db
                            table = db.table('Visit')
                            visitRecord = db.getRecordEx(table, '*', [table['id'].eq(visitId), table['deleted'].eq(0)])
                            if visitRecord:
                                self.cols()[column].caches[visitId] = visitRecord
                        if visitRecord:
                            sceneId = visitRecord.value('scene_id')
                        MKB = forceStringEx(item.value('MKB'))
                        MKBCaches = self.cols()[column].MKBCaches
                        MKBRecord = MKBCaches.get((visitId, MKB), None) if (visitId and MKB) else None
                        if not MKBRecord and MKB:
                            table = db.table('Visit')
                            tableEvent = db.table('Event')
                            tableDiagnosis = db.table('Diagnosis')
                            tableDiagnostic = db.table('Diagnostic')
                            tableDispanser = db.table('rbDispanser')
                            queryTable = tableEvent.innerJoin(table, table['event_id'].eq(tableEvent['id']))
                            queryTable = queryTable.innerJoin(tableDiagnostic,
                                                              tableDiagnostic['event_id'].eq(tableEvent['id']))
                            queryTable = queryTable.innerJoin(tableDiagnosis,
                                                              tableDiagnosis['id'].eq(tableDiagnostic['diagnosis_id']))
                            queryTable = queryTable.innerJoin(tableDispanser,
                                                              tableDispanser['id'].eq(tableDiagnostic['dispanser_id']))
                            cond = [table['id'].eq(visitId),
                                    db.joinOr(
                                        [tableDiagnosis['MKB'].eq(MKB), tableDiagnosis['MKB'].like(MKB[:3] + '%')]),
                                    tableDiagnostic['dispanser_id'].isNotNull(),
                                    table['deleted'].eq(0),
                                    tableDiagnosis['deleted'].eq(0),
                                    tableDiagnostic['deleted'].eq(0),
                                    tableEvent['deleted'].eq(0)
                                    ]
                            MKBRecord = db.getRecordEx(queryTable, 'Diagnosis.MKB, Diagnostic.dispanser_id', cond)
                            if MKBRecord:
                                self.cols()[column].MKBCaches[(visitId, MKB)] = MKBRecord
                        if MKBRecord:
                            MKBVisit = forceStringEx(MKBRecord.value('MKB'))
                            if MKB != MKBVisit:
                                res = QtGui.QMessageBox.warning(self._parent,
                                                                u'Внимание!',
                                                                u'Диагноз по ДН События визита \'%s\' отличается от '
                                                                u'диагноза контроля \'%s\'.\nОбновить значение в поле МКБ?' % (
                                                                MKBVisit, MKB),
                                                                QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel,
                                                                QtGui.QMessageBox.Cancel)
                                if res == QtGui.QMessageBox.Ok:
                                    self.setValue(row, 'MKB', toVariant(MKBVisit))
                                    rowLast = row + 1
                                    while rowLast < len(self._items):
                                        self.setValue(rowLast, 'MKB', toVariant(MKBVisit))
                                        rowLast += 1
                                        self.emitRowChanged(rowLast)
                        if MKB:
                            diagnosticRecord = self.diagnosticRecords.get(MKB, None)
                            if not diagnosticRecord:
                                MKBGroup = MKB[:3] if len(MKB) > 3 else MKB
                                diagnosticRecord = self.diagnosticGroupRecords.get(MKBGroup, None)
                            if diagnosticRecord:
                                dispanserId = forceRef(diagnosticRecord.value('diagnosisDispanser_id'))
                                if not dispanserId:
                                    removeDate = forceDate(item.value('removeDate'))
                                    removeReasonId = forceRef(item.value('removeReason_id'))
                                    if self.rbDispanserConsists and not removeDate and not removeReasonId:
                                        diagnosticRecord.setValue('diagnosisDispanser_id', toVariant(self.rbDispanserConsists))
                                        self.diagnosticItems.append(diagnosticRecord)
                                    elif removeDate and removeReasonId:
                                        dateVisit = forceDate(visitRecord.value('date')) if visitRecord else None
                                        if dateVisit and dateVisit == removeDate:
                                            recordSRR = self.rbSurveillanceRemoveReason.get(removeReasonId, None)
                                            dispanserSRRId = forceRef(
                                                recordSRR.value('dispanser_id')) if recordSRR else None
                                            diagnosticRecord.setValue('diagnosisDispanser_id', toVariant(
                                                dispanserSRRId if dispanserSRRId else self.rbDispanserRemoved))
                                            self.diagnosticItems.append(diagnosticRecord)
                                else:
                                    self.setValue(row, 'dispanser_id', toVariant(dispanserId))
                                    if self.eventId:
                                        dispanserRecord = self.dispanserRecords.get(dispanserId, None)
                                        if dispanserRecord:
                                            observed = forceInt(dispanserRecord.value('observed'))
                                            name = forceStringEx(dispanserRecord.value('name'))
                                            if observed == 0 and u'нуждается' not in name:
                                                dateVisitForRemoved = self.getEventVisitMAXDate(self.eventId, row)
                                                if dateVisitForRemoved:
                                                    self.setValue(row, 'removeDate', toVariant(dateVisitForRemoved))
                        self.setValue(row, 'scene_id', sceneId)
                elif column == self.Col_PersonId:
                    userId = forceRef(item.value('person_id'))

                personRecord = self.personCache.get(userId) if userId else None
                if personRecord:
                    orgStructureId = forceInt(personRecord.value('orgStructure_id'))
                    specialityId = forceInt(personRecord.value('speciality_id'))

                self.setValue(row, 'person_id', userId)
                self.setValue(row, 'orgStructure_id', orgStructureId)
                self.setValue(row, 'speciality_id', specialityId)
                self.emitRowChanged(row)
            return result
        return False
    

class CActionPropertiesTableModel(QAbstractTableModel):
    __pyqtSignals__ = ('actionNameChanged()',
                       'setEventEndDate(QDate)',
                       'setCurrentActionPlannedEndDate(QDate)',
                       'actionAmountChanged(double)',)

    column = [u'Назначено', u'Значение', u'Ед.изм.', u'Норма', u'Оценка']
    visibleAll = 0
    visibleInJobTicket = 1
    ciIsAssigned = 0
    ciValue = 1
    ciUnit = 2
    ciNorm = 3
    ciEvaluation = 4

    def __init__(self, parent, visibilityFilter=0):
        QAbstractTableModel.__init__(self, parent)
        self.action = None
        self.clientId = None
        self.clientNormalParameters = {}
        self.propertyTypeList = []
        self.unitData = CRBModelDataCache.getData('rbUnit', True)
        self.evaluationData = InterpretationData()
        self.visibilityFilter = visibilityFilter
        self.readOnly = False
        self.actionStatusTip = None

    def getClientNormalParameters(self):
        clientNormalParameters = {}
        if self.clientId:
            db = QtGui.qApp.db
            table = db.table('Client_NormalParameters')
            cond = [table['client_id'].eq(self.clientId),
                    table['deleted'].eq(0)
                    ]
            records = db.getRecordList(table, '*', cond, order=table['idx'].name())
            for record in records:
                templateId = forceRef(record.value('template_id'))
                norm = forceStringEx(record.value('norm'))
                if templateId:
                    clientNormalParameters[templateId] = norm
        return clientNormalParameters

    def setReadOnly(self, value):
        self.readOnly = value

    def setAction(self, action, clientId, clientSex=None, clientAge=None, eventTypeId=None):
        self.action = action
        self.clientId = clientId
        self.clientNormalParameters = self.getClientNormalParameters()
        self.eventTypeId = eventTypeId
        if self.action:
            actionType = action.getType()
            propertyTypeList = actionType.getPropertiesById().items()
            propertyTypeList.sort(key=lambda x: (x[1].idx, x[0]))
            self.propertyTypeList = [x[1] for x in propertyTypeList if
                                     x[1].applicable(clientSex, clientAge) and self.visible(x[1])]
        else:
            self.propertyTypeList = []
        for propertyType in self.propertyTypeList:
            propertyType.shownUp(action, clientId)
        self.updateActionStatusTip()
        self.reset()

    def updateActionStatusTip(self):
        # update self.actionStatusTip by self.action
        if self.action:
            actionType = self.action.getType()
            self.actionStatusTip = actionType.code + ': ' + actionType.name
        else:
            self.actionStatusTip = None

    def visible(self, propertyType):
        return self.visibilityFilter == self.visibleAll or \
               self.visibilityFilter == self.visibleInJobTicket and propertyType.visibleInJobTicket

    def columnCount(self, index=None):
        return 5

    def rowCount(self, index=QModelIndex()):
        return len(self.propertyTypeList)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return QVariant(self.column[section])
        elif orientation == Qt.Vertical:
            propertyType = self.propertyTypeList[section]
            property = self.action.getPropertyById(propertyType.id)
            if role == Qt.DisplayRole:
                return QVariant(foldText(propertyType.name, [CActionPropertiesTableView.titleWidth]))
            elif role == Qt.ToolTipRole:
                result = propertyType.descr if trim(propertyType.descr) else propertyType.name
                return QVariant(result)
            elif role == Qt.TextAlignmentRole:
                return QVariant(Qt.AlignLeft | Qt.AlignTop)
            elif role == Qt.FontRole:
                evaluation = property.getEvaluation()
                hasEvalColor = bool(evaluation and self.evaluationData.getColorById(evaluation))
                hasPenalty = propertyType.penalty > 0
                if hasEvalColor or hasPenalty:
                    font = QtGui.QFont()
                    font.setBold(True)
                    return QVariant(font)
        return QVariant()

    def getPropertyType(self, row):
        return self.propertyTypeList[row]

    def getProperty(self, row):
        propertyType = self.propertyTypeList[row]
        return self.action.getPropertyById(propertyType.id)

    def flags(self, index):
        row = index.row()
        column = index.column()
        propertyType = self.propertyTypeList[row]
        if propertyType.isPacsImage():
            return Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled
        if self.readOnly or (self.action and self.action.isLocked()):
            if propertyType.isImage():
                return Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled
            else:
                return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        else:
            if self.hasCommonPropertyChangingRight(row):
                if column == self.ciIsAssigned and propertyType.isAssignable:
                    return Qt.ItemIsSelectable | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled
                elif column == self.ciValue:
                    if propertyType.isBoolean():
                        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsUserCheckable
                    return Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled
                elif column == self.ciEvaluation:
                    propertyType = propertyType
                    if propertyType.defaultEvaluation in (0, 1):  # 0-не определять, 1-автомат
                        return Qt.ItemIsSelectable | Qt.ItemIsEnabled
                    elif propertyType.defaultEvaluation in (2, 3):  # 2-полуавтомат, 3-ручное
                        return Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def data(self, index, role=Qt.DisplayRole):
        row = index.row()
        column = index.column()
        propertyType = self.propertyTypeList[row]
        property = self.action.getPropertyById(propertyType.id)
        if role == Qt.DisplayRole:
            if column == self.ciValue:
                if propertyType.isBoolean():
                    return QVariant()
                text = property.getText()
                if not text:
                    try:
                        values = self.updateDependedProperties(propertyType.whatDepends or [])
                        text = propertyType.evalValue(values)
                        property.setValue(text)
                    except Exception:
                        pass
                return toVariant(text)
            elif column == self.ciUnit:
                return QVariant(self.unitData.getNameById(property.getUnitId()))
            elif column == self.ciNorm:
                return toVariant(property.getNorm())
            elif column == self.ciEvaluation:
                return QVariant(self.evaluationData.getNameById(property.getEvaluation()))
            else:
                return QVariant()
        elif role == Qt.CheckStateRole:
            if column == self.ciValue:
                if propertyType.isBoolean():
                    return QVariant(Qt.Checked if property.getValue() else Qt.Unchecked)
            if column == self.ciIsAssigned:
                if propertyType.isAssignable:
                    return toVariant(Qt.Checked if property.isAssigned() else Qt.Unchecked)
        elif role == Qt.EditRole:
            if column == self.ciIsAssigned:
                return toVariant(property.getStatus())
            elif column == self.ciValue:
                return toVariant(property.getValue())
            elif column == self.ciUnit:
                return toVariant(property.getUnitId())
            elif column == self.ciNorm:
                return toVariant(property.getNorm())
            elif column == self.ciEvaluation:
                return toVariant(property.getEvaluation())
            else:
                return QVariant()
        elif role == Qt.TextAlignmentRole:
            return QVariant(Qt.AlignLeft | Qt.AlignTop)
        elif role == Qt.DecorationRole:
            return QVariant()
        #            if column == self.ciValue:
        #                image = property.getImage()
        #                if isinstance(image, QtGui.QImage):
        #                    return toVariant(QtGui.QPixmap.fromImage(image))
        #                return toVariant(image)
        #            else:
        #                return QVariant()
        elif role == Qt.ForegroundRole:
            evaluation = property.getEvaluation()
            if evaluation and self.evaluationData.isWhiteText(evaluation):
                return QVariant(QtGui.QBrush(QtGui.QColor('white')))
        elif role == Qt.BackgroundColorRole:
            evaluation = property.getEvaluation()
            if evaluation:
                color = self.evaluationData.getColorById(evaluation)
                if color:
                    return QVariant(QtGui.QBrush(QtGui.QColor(color)))
            # rowColor = property.type().color
            # if rowColor is not None:
            #     return QVariant(QtGui.QBrush(rowColor))
        elif role == Qt.FontRole:
            evaluation = property.getEvaluation()
            if evaluation and self.evaluationData.getColorById(evaluation):
                font = QtGui.QFont()
                font.setBold(True)
                return QVariant(font)
        elif role == Qt.ToolTipRole:
            if column == self.ciIsAssigned:
                if propertyType.isAssignable:
                    return toVariant(u'Назначено' if property.isAssigned() else u'Не назначено')
        elif role == Qt.StatusTipRole:
            if self.actionStatusTip:
                return toVariant(self.actionStatusTip)
        return QVariant()

    def hasCommonPropertyChangingRight(self, row):
        propertyType = self.propertyTypeList[row]
        if propertyType.canChangeOnlyOwner == 0:  # все могут редактировать свойство
            return True
        elif propertyType.canChangeOnlyOwner == 1 and self.action:
            setPersonId = forceRef(self.action.getRecord().value('setPerson_id'))
            return setPersonId == QtGui.qApp.userId
        return False

    def getDefaultEvaluation(self, propertyType, property, index):
        isClientNormalParameters = False
        templateId = property.getTemplateId()
        if templateId:
            clientNormalParameters = trim(self.clientNormalParameters.get(templateId, u''))
            if clientNormalParameters:
                property.setNorm(clientNormalParameters)
                isClientNormalParameters = True
        if propertyType.defaultEvaluation in (1, 2) or isClientNormalParameters:
            # if propertyType.defaultEvaluation == 2 and not isClientNormalParameters:
            #     if property.getEvaluation() is not None:
            #         return ('%+d'%property.getEvaluation())
            value = unicode(property.getText())
            if bool(value):
                try:
                    value = float(value)
                except ValueError:
                    return ''
                norm = property.getNorm()
                parts = norm.split('-')
                if len(parts) == 2:
                    try:
                        bottom = float(parts[0].replace(',', '.'))
                        top = float(parts[1].replace(',', '.'))
                    except ValueError:
                        return ''
                    if bottom > top:
                        return ''
                    if value < bottom:
                        evaluationCode = "L"
                    elif value > top:
                        evaluationCode = "H"
                    else:
                        evaluationCode = "N"
                    table = QtGui.qApp.db.table('rbResultInterpretation')
                    evaluationRecord = QtGui.qApp.db.getRecordEx(table, ['id', 'name'],
                                                                 table['code'].eq(evaluationCode))
                    if not evaluationRecord:
                        return ''
                    index = self.index(index.row(), self.ciEvaluation)
                    self.setData(index, evaluationRecord.value('id'))
                    return forceString(evaluationRecord.value('name'))
        return ''

    # WFT?
    def sort(self, column, order):
        flag = False
        if order == 1:
            flag = True
        if column == self.ciIsAssigned:
            self.propertyTypeList.sort(key=lambda x: self.action.getPropertyById(x.id).isAssigned(), reverse=flag)
        if column == self.ciValue:
            self.propertyTypeList.sort(key=lambda x: conv_data(self.action.getPropertyById(x.id).getText()), reverse=flag)
        if column == self.ciUnit:
            self.propertyTypeList.sort(key=lambda x: conv_data(self.unitData.getNameById(self.action.getPropertyById(x.id).getUnitId())), reverse=flag)
        if column == self.ciNorm:
            self.propertyTypeList.sort(key=lambda x: conv_data(self.action.getPropertyById(x.id).getNorm()), reverse=flag)
        if column == self.ciEvaluation:
            self.propertyTypeList.sort(key=lambda x: conv_data(self.action.getPropertyById(x.id).getEvaluation()), reverse=flag)
        self.reset()

    def setData(self, index, value, role=Qt.EditRole):
        row = index.row()
        column = index.column()
        propertyType = self.propertyTypeList[row]
        property = self.action.getPropertyById(propertyType.id)

        if role == Qt.EditRole:
            if column == self.ciValue:
                if not propertyType.isVector:
                    property.preApplyDependents(self.action)
                    property.setValue(propertyType.convertQVariantToPyValue(value))
                    self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index, index)
                    self.getDefaultEvaluation(propertyType, property, index)
                    if property.isActionNameSpecifier():
                        self.action.updateSpecifiedName()
                        self.emit(SIGNAL('actionNameChanged()'))
                    property.applyDependents(self.action)
                    if propertyType.isJobTicketValueType():
                        self.action.setPlannedEndDateOnJobTicketChanged(property.getValue())
                    if propertyType.whatDepends:
                        self.updateDependedProperties(propertyType.whatDepends)
                    return True
            elif column == self.ciEvaluation:
                property.setEvaluation(None if value.isNull() else forceInt(value))
                self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index, index)
                return True
        elif role == Qt.CheckStateRole:
            if column == self.ciValue:
                if propertyType.isBoolean():
                    property.setValue(forceInt(value) == Qt.Checked)
                    self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index, index)
                    self.getDefaultEvaluation(propertyType, property, index)
                    if propertyType.whatDepends:
                        self.updateDependedProperties(propertyType.whatDepends)
                    return True
            if column == self.ciIsAssigned:
                property.setAssigned(forceInt(value) == Qt.Checked)
                self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index, index)
                #                actionType = self.action.getType()
                #                if actionType.amountEvaluation == CActionType.actionAssignedProps:
                #                    self.updateAmountAsAssignedPropertyCount()
                return True
        return False

    def updateDependedProperties(self, vars):
        values = {}
        propertiesByVar = self.action.getPropertiesByVar()
        for var, property in propertiesByVar.iteritems():
            values[var] = property.getValue()

        for var in vars:
            if var in propertiesByVar.keys():
                property = propertiesByVar[var]
                propertyType = property.type()
                val = propertyType.evalValue(values)
                values[var] = val
                property.setValue(val)

                row = self.propertyTypeList.index(propertyType)
                index = self.index(row, self.ciValue)
                self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index, index)
        return values


    def emitDataChanged(self):
        leftTop = self.index(0, 0)
        rightBottom = self.index(self.rowCount(), self.columnCount())
        self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), leftTop, rightBottom)

    #    def updateAmountAsAssignedPropertyCount(self):
    #        result = self.action.getAssignedPropertiesCount()
    #        self.emit(SIGNAL('actionAmountChanged(double)'), float(result))

    def setLaboratoryCalculatorData(self, data):
        propertyTypeIdList = [propType.id for propType in self.propertyTypeList]
        for sValuePair in data.split(';'):
            sValuePair = trim(sValuePair).strip('()').split(',')
            propertyTypeId, value = forceInt(sValuePair[0]), sValuePair[1]
            if propertyTypeId in propertyTypeIdList:
                propertyTypeIndex = propertyTypeIdList.index(propertyTypeId)
                propertyType = self.propertyTypeList[propertyTypeIndex]
                property = self.action.getPropertyById(propertyTypeId)
                property.setValue(propertyType.convertQVariantToPyValue(QVariant(value)))
        begIndex = self.index(0, 0)
        endIndex = self.index(self.rowCount() - 1, self.columnCount() - 1)
        self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), begIndex, endIndex)

    def setPlannedEndDateByJobTicket(self, jobTicketId):
        db = QtGui.qApp.db
        date = forceDate(db.translate('Job_Ticket', 'id', jobTicketId, 'datetime'))
        jobId = forceRef(db.translate('Job_Ticket', 'id', jobTicketId, 'master_id'))
        jobTypeId = forceRef(db.translate('Job', 'id', jobId, 'jobType_id'))
        ticketDuration = forceInt(db.translate('rbJobType', 'id', jobTypeId, 'ticketDuration'))
        self.emit(SIGNAL('setCurrentActionPlannedEndDate(QDate)'), date.addDays(ticketDuration))

    def plannedEndDateByJobTicket(self):
        actionType = self.action.getType()
        return actionType.defaultPlannedEndDate == CActionType.dpedJobTicketDate


class CMeasuresActionsCheckTableModel(CTableModel):
    class CEnableCol(CBoolCol):
        def __init__(self, title, fields, defaultWidth, selector):
            CBoolCol.__init__(self, title, fields, defaultWidth)
            self.selector = selector

        def checked(self, values):
            id = forceRef(values[0])
            if self.selector.isSelected(id):
                return CBoolCol.valChecked
            else:
                return CBoolCol.valUnchecked

    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self._idList = None
        self._actionRecordItemCache = {}
        self.enableIdList = []
        self._items = []
        self.addColumn(CMeasuresActionsCheckTableModel.CEnableCol(u'Выбрать', ['id'], 5, self))
        self.addColumn(CDateCol(u'Назначено',      ['directionDate'], 15))
        self.addColumn(CActionTypeCol(u'Тип',                         15))
        self.addColumn(CBoolCol(u'Срочно',         ['isUrgent'],      15))
        self.addColumn(CEnumCol(u'Состояние',      ['status'], CActionStatus.names, 4))
        self.addColumn(CDateCol(u'План',           ['plannedEndDate'],15))
        self.addColumn(CDateCol(u'Начато',         ['begDate'],       15))
        self.addColumn(CDateCol(u'Окончено',       ['endDate'],       15))
        self.addColumn(CRefBookCol(u'Назначил',    ['setPerson_id'], 'vrbPersonWithSpeciality', 20))
        self.addColumn(CRefBookCol(u'Выполнил',    ['person_id'],    'vrbPersonWithSpeciality', 20))
        self.addColumn(CTextCol(u'Каб',            ['office'],                                6))
        self.addColumn(CTextCol(u'Примечания',     ['note'],                                  6))
        self.setTable('Action')
        self._mapColumnToOrder = {u'directionDate' : u'Action.directionDate',
                                  u'actionType_id' : u'ActionType.name',
                                  u'isUrgent'      : u'Action.isUrgent',
                                  u'status'        : u'Action.status',
                                  u'plannedEndDate': u'Action.plannedEndDate',
                                  u'begDate'       : u'Action.begDate',
                                  u'endDate'       : u'Action.endDate',
                                  u'setPerson_id'  : u'vrbPersonWithSpeciality.name',
                                  u'person_id'     : u'vrbPersonWithSpeciality.name',
                                  u'office'        : u'Action.office',
                                  u'note'          : u'Action.note'
                                  }

    def getOrder(self, fieldName, column):
        if hasattr(self._cols[column], 'extraFields'):
            if len(self._cols[column].extraFields) > 0:
                fieldName = self._cols[column].extraFields[0]
        return self._mapColumnToOrder[fieldName]

    def flags(self, index):
        result = CTableModel.flags(self, index)
        if index.column() == 0:
            result |= Qt.ItemIsUserCheckable
        return result

    def setData(self, index, value, role=Qt.EditRole):
        row = index.row()
        column = index.column()
        id = self._idList[row]
        if column == 0:
            if role == Qt.CheckStateRole:
                if id:
                    self.setSelected(id, forceInt(value) == Qt.Checked)
                    self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index, index)
                return True
        return CTableModel.setData(self, index, value, role)

    # def data(self, index, role=Qt.DisplayRole):
    #     if not index.isValid():
    #         return QVariant()
    #     row = index.row()
    #     column = index.column()
    #     id = self._idList[row]
    #     if role == Qt.DisplayRole:
    #         if column == 0 and id in self.enableIdList:
    #             return QVariant(forceInt(2) == Qt.Checked)
    #     return CTableModel.data(self, index, role)

    def setSelected(self, id, value):
        present = self.isSelected(id)
        if value:
            if not present:
                self.enableIdList.append(id)
        else:
            if present:
                self.enableIdList.remove(id)

    def isSelected(self, id):
        return id in self.enableIdList

    def getSelectedIdList(self):
        return self.enableIdList

    def getSelectedItems(self):
        selectedItems = []
        idList = self.getSelectedIdList()
        for id in idList:
            if id:
                record = self.getRecordById(id)
                selectedItems.append((record, CAction(record=record)))
        return selectedItems

    def setIdList(self, idList, realItemCount=None):
        self._items = []
        self._idList = idList
        self._realItemCount = realItemCount
        self._prevColumn = None
        self._prevRow    = None
        self._prevData   = None
        # self.invalidateRecordsCache()
        self.reset()
        self.emitItemsCountChanged()
        # ----------------------------
        db = QtGui.qApp.db
        table = db.table('Action')
        if self._recordsCache is None:
            self.setTable('Action')
        tmpIdList = [id for id in idList if not self._recordsCache.has_key(id)]
        self._recordsCache.fetch(tmpIdList)
        tmpIdList = [id for id in idList if not self._actionRecordItemCache.get(id)]
        # records = db.getRecordList('Action', where=table['id'].inlist(idList), order='id')
        ATset = set()
        personSet = set()
        personSpecialityMap = dict()
        actionTypeMap = dict()
        for id in tmpIdList:
            record = self.getRecordById(id)
            ATset.add(forceRef(record.value('actionType_id')))
            personId = forceRef(record.value('person_id'))
            personSet.add(personId)
            actionTypeMap[forceRef(record.value('id'))] = forceRef(record.value('actionType_id'))

        # массовое кэширование ТД для события
        CActionTypeCache.getByIds(ATset)

        # массовая загрузка специальностей исполнителей действий
        if personSet:
            db = QtGui.qApp.db
            tablePerson = db.table('Person')
            recordsSpeciality = db.getRecordList(tablePerson, [tablePerson['id'], tablePerson['speciality_id']],
                                                 [tablePerson['deleted'].eq(0), tablePerson['id'].inlist(personSet)])
            for record in recordsSpeciality:
                specialityId = forceRef(record.value('speciality_id'))
                personId = forceRef(record.value('id'))
                personSpecialityMap[personId] = specialityId

        # массовая загрузка связей действий с резервированием ЛСиИМН
        tableActionNR = db.table('Action_NomenclatureReservation')
        nomenclatureReservationRecords = db.getRecordList(tableActionNR, '*',
                                                          [tableActionNR['action_id'].inlist(actionTypeMap.keys())])
        mapReservation = {}
        for recordReservation in nomenclatureReservationRecords:
            actionId = forceRef(recordReservation.value('action_id'))
            reservation_id = forceRef(recordReservation.value('reservation_id'))
            mapReservation[actionId] = reservation_id

        # массовая загрузка элементов плана выполнения
        mapExecutionPlan = {}
        tableActionEPI = db.table('ActionExecutionPlan_Item')
        executionPlanItemRecords = db.getRecordList(tableActionEPI, '*',
                                                    [tableActionEPI['action_id'].inlist(actionTypeMap.keys())])
        for recordExecutionPlan in executionPlanItemRecords:
            actionId = forceRef(recordExecutionPlan.value('action_id'))
            mapExecutionPlan.setdefault(actionId, []).append(recordExecutionPlan)

        # массовая загрузка прикрепленных файлов
        mapFileAttach = {}
        tableFileAttach = db.table('Action_FileAttach')
        fileAttachRecords = db.getRecordList(tableFileAttach, '*',
                                             [tableFileAttach['master_id'].inlist(actionTypeMap.keys()),
                                              tableFileAttach['deleted'].eq(0)])
        for recordFileAttach in fileAttachRecords:
            actionId = forceRef(recordFileAttach.value('master_id'))
            mapFileAttach.setdefault(actionId, []).append(recordFileAttach)

        # массовая загрузка свойств действий
        tableActionProperty = db.table('ActionProperty')
        APRecords = db.getRecordList(tableActionProperty, '*',
                                     [tableActionProperty['action_id'].inlist(actionTypeMap.keys()),
                                      tableActionProperty['deleted'].eq(0)])
        mapValuesTable = {}
        mapProperties = {}
        mapValues = {}
        for propertyRecord in APRecords:
            propertyTypeId = forceRef(propertyRecord.value('type_id'))
            actionId = forceRef(propertyRecord.value('action_id'))
            actionType = CActionTypeCache.getById(actionTypeMap[actionId])
            if actionType.propertyTypeIdPresent(propertyTypeId):
                tableName = actionType.getPropertyTypeById(propertyTypeId).tableName
                mapValuesTable.setdefault(tableName, []).append(forceRef(propertyRecord.value('id')))
                mapProperties.setdefault(actionId, []).append(propertyRecord)

        for key in mapValuesTable.keys():
            valueTable = db.table(key)
            valueRecords = db.getRecordList(valueTable, '*', valueTable['id'].inlist(mapValuesTable[key]))
            for rec in valueRecords:
                mapValues.setdefault(forceRef(rec.value('id')), []).append(rec)
        for id in tmpIdList:
            record = self.getRecordById(id)
            actionId = forceRef(record.value('id'))
            actionType = CActionTypeCache.getById(actionTypeMap[actionId])
            propertyRecords = mapProperties.get(actionId, [])
            reservationId = mapReservation.get(actionId, -1)
            executionPlanRecord = mapExecutionPlan.get(actionId, [])
            fileAttachRecords = mapFileAttach.get(actionId, [])
            personId = forceRef(record.value('person_id'))
            specialityId = personSpecialityMap.get(personId, -1)
            mapActionValueRecords = dict()
            for prop in propertyRecords:
                mapActionValueRecords[forceRef(prop.value('id'))] = mapValues.get(forceRef(prop.value('id')), [])
            action = CAction(actionType=actionType, record=record, propertyRecords=propertyRecords,
                             valueRecords=mapActionValueRecords, reservationId=reservationId,
                             executionPlanRecord=executionPlanRecord, fileAttachRecords=fileAttachRecords,
                             specialityId=specialityId)
            # items.setdefault(action.getType().class_, []).append(CActionRecordItem(action.getRecord(), action))
            self._actionRecordItemCache[action.getId()] = CActionRecordItem(action.getRecord(), action)

        tablePPA = db.table('ProphylaxisPlanning_Action')
        checksList = db.getIdList(tablePPA, idCol='action_id', where=tablePPA['id'].inlist(idList))
        for id in idList:
            check = id in checksList
            check = 2 if check else 0
            self.setSelected(id, forceInt(check) == Qt.Checked)
            # record = self.getRecordById(id)
            self._items.append(self._actionRecordItemCache.get(id))
        # ----------------------------
        # for id in self._idList:
        #     if id:
        #         check = forceInt(QtGui.qApp.db.translate('ProphylaxisPlanning_Action', 'id', id, 'action_id'))
        #         check = 2 if check else 0
        #         self.setSelected(id, forceInt(check) == Qt.Checked)
        #         record = self.getRecordById(id)
        #         self._items.append((record, CAction(record=record)))

    def items(self):
        return self._items


class CPersonInDocTableCol(CRBInDocTableCol):
    def __init__(self, title, fieldName, width, tableName, **params):
        CRBInDocTableCol.__init__(self, title, fieldName, width, tableName, **params)
        self.eventEditor = None
        self.filterLoc = u''
        self.isFilterAddSpeciality = True

    def setFilterAddSpeciality(self, value):
        self.isFilterAddSpeciality = value

    def setFilter(self, filter):
        self.filterLoc = filter

    def setEventEditor(self, eventEditor):
        self.eventEditor = eventEditor

    def setEditorData(self, editor, value, record):
        filterRetired = u''
        if self.eventEditor is not None:
            orgId = self.eventEditor.orgId
            begDate = forceDate(record.value('begDate'))
            endDate = forceDate(record.value('endDate'))
            filterDate = None
            if endDate:
                filterDate = u'DATE(retireDate) > DATE(%s)' % QtGui.qApp.db.formatDate(endDate)
            elif begDate:
                filterDate = u'DATE(retireDate) > DATE(%s)' % QtGui.qApp.db.formatDate(begDate)
            filterRetired = u' AND (retireDate IS NULL %s)' % ((u' OR (%s)' % filterDate) if filterDate else u'')
        else:
            orgId = QtGui.qApp.currentOrgId()
        if self.isFilterAddSpeciality:
            filter = 'speciality_id IS NOT NULL AND org_id=\'%s\' %s' % (orgId, filterRetired)
        else:
            filter = 'org_id=\'%s\' %s' % (orgId, filterRetired)
        if self.filterLoc:
            filter += u' AND ' + self.filterLoc
        editor.setTable(self.tableName, self.addNone, filter, 'name')
        editor.setShowFields(self.showFields)
        editor.setValue(forceRef(value))
