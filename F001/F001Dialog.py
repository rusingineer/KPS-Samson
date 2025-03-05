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
from PyQt4.QtCore import Qt, QDate, QDateTime, QEvent, QModelIndex, QTime, QVariant, pyqtSignature, SIGNAL

from Events.ExportMIS import iniExportEvent
from F088.F0882022EditDialog import CEventExportTableModel, CAdvancedExportTableModel
from Events.RelatedEventAndActionListDialog import CRelatedEventAndActionListDialog
from library.Attach.AttachAction import getAttachAction
from library.Counter            import CCounterController
from library.database           import CRecordCache
from library.InDocTable         import CInDocTableCol
from library.interchange         import getDatetimeEditValue, getRBComboBoxValue, setDatetimeEditValue, setRBComboBoxValue
from library.ICDUtils            import MKBwithoutSubclassification
from library.ItemsListDialog    import CItemEditorBaseDialog
from library.PrintInfo          import CInfoContext
from library.PrintTemplates     import CPrintButton, customizePrintButton, directPrintTemplate, getFirstPrintTemplate, getPrintButton
from library.TableModel         import CTableModel, CCol, CTextCol
from library.Utils               import forceBool, forceDate, forceDateTime, forceInt, forceRef, forceString, forceStringEx, formatNum, toVariant, trim

from Events.ActionInfo          import CActionInfoProxyList
from Events.ActionProperty      import CToothActionPropertyValueType #wtf?
from Events.ActionsSelector     import CActionsModel, CActionTypesSelectionManager, CEnableCol
from Events.ActionsSummaryModel import CFxxxActionsSummaryModel
from Events.ActionTypeComboBox  import CActionTypeModel
from Events.EventEditDialog     import CEventEditDialog
from Events.EventInfo import CDiagnosticInfo, CCharacterInfo, CTraumaTypeInfo, CPersonInfo, CDiagnosticResultInfo, \
    CToxicSubstancesInfo, CDagnosisTypeInfo
from Events.MKBInfo             import CMKBInfo, CMorphologyMKBInfo
from Events.Utils                import CTableSummaryActionsMenuMixin, getAvailableCharacterIdByMKB, getDiagnosisId2, getEventFinanceId, getEventIncludeTooth, getEventIsTakenTissue, getEventLimitActionTypes, getEventSetPerson, getEventShowTime, getExternalIdDateCond, getEventIsPrimary, getEventCode, checkDiagnosis, getEventTypeForm
from F001.PreF001Dialog         import CPreF001Dialog, CPreF001DagnosticAndActionPresets
from Orgs.Utils                 import getOrgStructureActionTypeIdSet
from Registry.Utils             import CClientInfo
from TissueJournal.TissueInfo   import CTissueTypeInfo, CTakenTissueJournalInfo
from Users.Rights                import urAccessF001planner, urAccessF090planner, urAdmin, urEditEndDateEvent, urRegTabWriteRegistry, urRegTabReadRegistry, urCanReadClientVaccination, urCanEditClientVaccination

from F001.Ui_F001               import Ui_F001Dialog


class CF001Dialog(CEventEditDialog, Ui_F001Dialog, CActionTypesSelectionManager, CTableSummaryActionsMenuMixin):
    @pyqtSignature('')
    def on_actActionEdit_triggered(self): CTableSummaryActionsMenuMixin.on_actActionEdit_triggered(self)
    @pyqtSignature('')
    def on_actAPActionAddSuchAs_triggered(self): CTableSummaryActionsMenuMixin.on_actAPActionAddSuchAs_triggered(self)
    @pyqtSignature('')
    def on_actDeleteRow_triggered(self): CTableSummaryActionsMenuMixin.on_actDeleteRow_triggered(self)
    @pyqtSignature('')
    def on_actUnBindAction_triggered(self): CTableSummaryActionsMenuMixin.on_actUnBindAction_triggered(self)

    def __init__(self, parent):
        CEventEditDialog.__init__(self, parent)
        self._dialogIsExecuted = False
        self.preDiagnostics = []
        self.preSpecialityIdList = []
        self.isSelectionGroupOne = False
        self.addBarcodeScanAction('actScanBarcode')
        self.addModels('ActionTypeGroups', CActionTypeModel(self))
        self.addModels('ActionTypes', CActionLeavesModel(self))
        self.addModels('ActionsSummary', CF001ActionsSummaryModel(self, True))
        self.addObject('btnPrintLabel', CPrintButton(self, u'Печать наклейки'))
        self.addObject('btnPlanning', QtGui.QPushButton(u'Планировщик', self))
        self.addObject('btnRelatedEvent', QtGui.QPushButton(u'Связанные события', self))
        self.btnPrintLabel.setShortcut('F6')

        self.addModels('Export', CEventExportTableModel(self))
        self.addModels('Export_FileAttach', CAdvancedExportTableModel(self))
        self.addModels('Export_VIMIS', CAdvancedExportTableModel(self))

        self.addObject('actEditClient', QtGui.QAction(u'Открыть регистрационную карточку', self))
        self.addObject('actPortal_Doctor', QtGui.QAction(u'Перейти на портал врача', self))
        self.addObject('actShowAttachedToClientFiles', getAttachAction('Client_FileAttach',  self))
        self.addObject('actShowContingentsClient', QtGui.QAction(u'Показать все наблюдаемые контингенты', self))
        self.addObject('actOpenClientVaccinationCard', QtGui.QAction(u'Открыть прививочную карту', self))
        self.addObject('btnPrint', getPrintButton(self, ''))
        # self.addObject('btnMedicalCommission', QtGui.QPushButton(u'ВК', self))
        self.createSaveAndCreateAccountButton()
        self.needToSelectPreviousActions = False

        self.setupUi(self)

        self.buttonBox.addButton(self.btnPrintLabel, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnPrint, QtGui.QDialogButtonBox.ActionRole)
        if QtGui.qApp.defaultKLADR()[:2] in ['23', '01']:
            self.buttonBox.addButton(self.btnPlanning, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnRelatedEvent, QtGui.QDialogButtonBox.ActionRole)


        self.modelActionTypeGroups.setAllSelectable(True)
        self.modelActionTypeGroups.setRootItemVisible(True)
        self.modelActionTypeGroups.setLeavesVisible(False)
        self.setActionTypeClasses([0, 1, 2, 3])
        self.setModels(self.treeActionTypeGroups, self.modelActionTypeGroups, self.selectionModelActionTypeGroups)

        self.setModels(self.tblActionTypes, self.modelActionTypes, self.selectionModelActionTypes)
        self.setModels(self.tblActions, self.modelActionsSummary, self.selectionModelActionsSummary)
        self.setModels(self.tblExport, self.modelExport, self.selectionModelExport)
        self.setModels(self.tblExport_FileAttach, self.modelExport_FileAttach, self.selectionModelExport_FileAttach)
        self.setModels(self.tblExport_VIMIS, self.modelExport_VIMIS, self.selectionModelExport_VIMIS)
#        self.tblActions.setModel(self.modelActionsSummary)
        self.modelActionsSummary.addModel(self.tabActions.modelAPActions)
        self.tabCash.addActionModel(self.tabActions.modelAPActions)

        self.tabActions.setEventEditor(self)
        self.tabCash.setEventEditor(self)
        self.edtFindByCode.installEventFilter(self)
        self.treeActionTypeGroups.installEventFilter(self)
        self.cmbMKB.installEventFilter(self)
        self.cmbMKBEx.installEventFilter(self)
        # cmb
        self.cmbCharacter.setTable('rbDiseaseCharacter')
        self.cmbTissueType.setTable('rbTissueType')
        self.cmbTissueUnit.setTable('rbUnit')
        self.cmbTraumaType.setTable('rbTraumaType')
        self.cmbToxicSubstances.setTable('rbToxicSubstances')
        self.cmbSetPerson.setDefaultOrgStructureId(None)
        #self.cmbSetPerson.setOnlyDoctorsIfUnknowPost(True)

        self.actionTypesByTissueType = None
        self.tableTakenTissueJournal = QtGui.qApp.db.table('TakenTissueJournal')
        self._manualInputExternalId  = None

        self.setTabActionsSettings()
        self.prepareSettings = {}
        self.actionsRowNotForAdding = {}
        self.actualByTissueType = {}
        self.morphologyFilterCache = {}
        self.MKB_allowed_morphology = ['C', 'D']
        isMKBMorphology = QtGui.qApp.defaultMorphologyMKBIsVisible()
        self.cmbMorphology.setVisible(isMKBMorphology)
        self.lblMorphology.setVisible(isMKBMorphology)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        # self.buttonBox.addButton(self.btnMedicalCommission, QtGui.QDialogButtonBox.ActionRole)
        self.btnNextStep = QtGui.QPushButton(u'Продолжить')
        self.buttonBox.addButton(self.btnNextStep, QtGui.QDialogButtonBox.ActionRole)
        self.setupSaveAndCreateAccountButton()

        CTableSummaryActionsMenuMixin.__init__(self, [self.tabActions.tblAPActions])

        # что ха хня, коллеги? on_selectionModelActionTypeGroups_currentChanged должно цепляться автоматом!
        self.connect(self.selectionModelActionTypeGroups,
                     SIGNAL('currentChanged(QModelIndex, QModelIndex)'),
                     self.on_selectionModelActionTypeGroups_currentChanged)

        # что ха хня, коллеги?
        self.connect(self.tabActions.tblAPActions,
                     SIGNAL('delRows()'),
                     self.modelAPActionsAmountChanged)

        # что ха хня, коллеги?
        self.connect(self.cmbMKB,
                     SIGNAL('textChanged(QString)'),
                     self.on_edtMKB_textChanged)

        # что ха хня, коллеги?
        self.connect(self.btnNextStep,
                     SIGNAL('clicked()'),
                     self.makeNextStep)

        # что ха хня, коллеги?
        self.connect(self.tabActions.tblAPActions.model(),
                     SIGNAL('itemsCountChanged()'),
                     self.recountActualByTissueType)

        self.addAction(self.actScanBarcode)
        self.labelTemplate = getFirstPrintTemplate('clientTissueLabel')
        self.postInitSetup()
        self.prolongateEvent = False
        self.prevEventId = None
        self.tabNotes.setEventEditor(self)
        self.setupVisitsIsExposedPopupMenu()

        self.txtClientInfoBrowser.actions.append(self.actEditClient)
        self.txtClientInfoBrowser.actions.append(self.actPortal_Doctor)
        self.txtClientInfoBrowser.actions.append(self.actShowAttachedToClientFiles)
        self.txtClientInfoBrowser.actions.append(self.actShowContingentsClient)
        self.txtClientInfoBrowser.actions.append(self.actOpenClientVaccinationCard)
        self.actOpenClientVaccinationCard.setEnabled(QtGui.qApp.userHasAnyRight([urCanReadClientVaccination, urCanEditClientVaccination]))
        self.actEditClient.setEnabled(QtGui.qApp.userHasAnyRight([urAdmin, urRegTabWriteRegistry, urRegTabReadRegistry]))

        self.tblExport.enableColsHide()
        self.tblExport.enableColsMove()

        self.tblExport_FileAttach.enableColsHide()
        self.tblExport_FileAttach.enableColsMove()

        self.tblExport_VIMIS.enableColsHide()
        self.tblExport_VIMIS.enableColsMove()

        self.postSetupUi()
        if hasattr(self, 'edtEndDate'):
            self.edtEndDate.setEnabled(QtGui.qApp.userHasRight(urEditEndDateEvent))
        if hasattr(self, 'edtEndTime'):
            self.edtEndTime.setEnabled(QtGui.qApp.userHasRight(urEditEndDateEvent))
        self.tblActionTypes.setIdList(self.setActionTypeIdList())
        self.setTNMSVisible(QtGui.qApp.isTNMSVisible())


    def setTNMSVisible(self, value):
        self.lblTNMS.setVisible(value)
        self.cmbTNMS.setVisible(value)


    def setActionTypeIdList(self):
        db = QtGui.qApp.db
        table = db.table('ActionType')
        cond = [table['deleted'].eq(0),
                table['showInForm'].ne(0),
                ]
        return db.getIdList(table, 'id', where=cond)


    def postInitSetup(self):
        self.cmbMorphology.setEnabled(False)
        self.takenTissueRecord = None
        self.setActionTypeIdListInTabActions()
        self.actionsCacheByCode = {}
        self.actionsCodeCacheByName = {}
        self.selectedActionTypeIdList = []
        self.enabledActionTypes = []
        self.existsActionTypesList = []
        self.focusOnAdd = False
        self.treeActionTypeGroups.expandAll()
        index = self.modelActionTypeGroups.createIndex(0, 0, self.modelActionTypeGroups.getRootItem())
        self.selectionModelActionTypeGroups.select(index, self.selectionModelActionTypeGroups.Toggle)
        self.on_selectionModelActionTypeGroups_currentChanged(index)
        self.totalAddedCount = 0
        self.nextStep = False

        self.plannedActionTypes = []
        self.setupDirtyCather()
#        self.defineConditionSettings()
        self.isSetConditionSettings = False
        printer = QtGui.qApp.labelPrinter()
        self.btnPrintLabel.setEnabled(self.labelTemplate is not None and bool(printer))


    def getServiceActionCode(self):
        return None


    def makeNextStep(self):
        self.nextStep = True
        self.accept()


    def updateSelectedCount(self):
        n = len(self.selectedActionTypeIdList)
        if self.totalAddedCount == 0:
            if n == 0:
                msg = u'ничего не выбрано'
            else:
                msg = u'выбрано '+formatNum(n, [u'действие', u'действия', u'действий'])
        else:
            if n == 0:
                msg = u'Добавлено '+formatNum(self.totalAddedCount, [u'действие', u'действия', u'действий'])
            else:
                msg = u'выбрано '+formatNum(n, [u'действие', u'действия', u'действий'])
        self.lblSelectedCount.setText(msg)


    def defineConditionSettings(self):
        execPersonId = self.cmbExecPerson.value()
        orgStructureId = None
        specialityId = QtGui.qApp.userSpecialityId
        if not specialityId:
            if execPersonId:
                specialityId = forceRef(QtGui.qApp.db.translate('Person',
                                        'id',
                                        execPersonId,
                                        'speciality_id'))
        if specialityId:
            self.specialityId = specialityId
        else:
            self.specialityId = None

        if QtGui.qApp.currentOrgStructureId():
            orgStructureId = QtGui.qApp.currentOrgStructureId()
            self.planner = False
        else:
            plannedActionTypes = self.getPlannedActionTypes()
            if plannedActionTypes:
                self.planner = True
            else:
                self.planner = False
                if QtGui.qApp.userSpecialityId:
                    orgStructureId = QtGui.qApp.userOrgStructureId
                else:
                    if execPersonId:
                        orgStructureId = forceRef(QtGui.qApp.db.translate('Person',
                                                                            'id',
                                                                            execPersonId,
                                                                            'orgStructure_id'))
        if orgStructureId:
            self.orgStructureId = orgStructureId
        else:
            self.orgStructureId = None


    def getActionTypesByTissueType(self):
        tissueTypeId = self.cmbTissueType.value()
        if tissueTypeId:
            db = QtGui.qApp.db
            table = db.table('ActionType_TissueType')
            cond = [table['tissueType_id'].eq(tissueTypeId)]
            idList = db.getDistinctIdList(table, 'master_id', cond)
            idList = db.getTheseAndParents('ActionType', 'group_id', idList)
            return idList
        return []


    def getPlannedActionTypes(self, exists=[]):
        if True:#self.plannedActionTypes is None:
            db = QtGui.qApp.db
            idList = []
            if self.chkConstraintActionTypes.isChecked():
                table = db.table('EventType_Action')
                cond = [table['eventType_id'].eq(self.eventTypeId),
                        table['actionType_id'].isNotNull()
                       ]
                specialityId = self.specialityId
                if specialityId:
                    cond.append(db.joinOr([table['speciality_id'].eq(specialityId),
                                           table['speciality_id'].isNull()]))
                else:
                    cond.append(table['speciality_id'].isNull())
                if exists:
                    cond.append(table['actionType_id'].notInlist(exists))
                idList = db.getIdList(table,
                                   'actionType_id',
                                   cond
                                   )
                idList = db.getTheseAndParents('ActionType', 'group_id', idList)
            if not idList:
                tableActionType = db.table('ActionType')
                idList = set(db.getIdList(tableActionType, 'id', [tableActionType['deleted'].eq(0),
                                                                  tableActionType['showInForm'].ne(0),
                                                                  tableActionType['id'].notInlist(exists)]))
            self.plannedActionTypes = set(idList)
        return self.plannedActionTypes


    def resetSettings(self):
        self.tabActions.modelAPActions._items = []
        self.tabActions.modelAPActions.reset()
        self.tblActions.selectionModel().deleteLater()
        self.tblActions.model().deleteLater()
        del self.modelActionsSummary
        del self.selectionModelActionsSummary
        self.addModels('ActionsSummary', CF001ActionsSummaryModel(self, True))
        self.setModels(self.tblActions, self.modelActionsSummary, self.selectionModelActionsSummary)
        self.modelActionsSummary.addModel(self.tabActions.modelAPActions)
        self.tabNotes.edtEventNote.clear()
        self.cmbMKB.clearEditText()
        self.cmbMKBEx.clearEditText()
        self.edtEndDate.clearEditText()
        self.cmbCharacter.setValue(None)
#        self.cmbSetPerson.setValue(None)
        self.cmbDiagnosticResult.setValue(None)
        self.cmbResult.setValue(None)


    def exec_(self):
        self._dialogIsExecuted = True
        self.preMakeNewEvent()
        if not self.prepareSettings:
            self.btnNextStep.setEnabled(False)
        self.recountActualByTissueType()
        self.updateTreeData()
        result = CEventEditDialog.exec_(self)
        try:
            if result:
                if not self.nextStep:
                    return result
                else:
                    self.postInitSetup()
                    self.resetSettings()
                    self._id = None
                    self._record = None
                    self.prepareFromCycle(**self.prepareSettings)
                    self.defineConditionSettings()
                    result = self.exec_()
                    return result
        finally:
            if result:
                QtGui.qApp.delAllCounterValueIdReservation()
            else:
                QtGui.qApp.resetAllCounterValueIdReservation()
                QtGui.qApp.setCounterController(None)
        return result


    def preMakeNewEvent(self):
        if not self.itemId():
            if self.cmbContract.model().rowCount() > 1:
                self.cmbContract.setFocus()
            else:
                self.cmbSetPerson.setFocus()
        else:
            self.cmbSetPerson.setFocus()


    def setTabActionsSettings(self):
        self.tabActions.on_actAPActionsAdd_triggered = self.toDoNone
        for a in self.tabActions.tblAPActions.popupMenu().actions():
            if a.shortcut() == Qt.Key_F9:
                self.tabActions.tblAPActions.popupMenu().removeAction(a)


    def toDoNone(self):
        pass


    def modelAPActionsAmountChanged(self):
        self.updateTreeData(True)
        self.recountActualByTissueType()


    def setSelected(self, actionTypeId, value):
        self.focusOnAdd = True
        CActionTypesSelectionManager.setSelected(self, actionTypeId, value)


    def eventFilter(self, obj, event):
        if obj == self.treeActionTypeGroups:
            if event.type() == QEvent.KeyPress:
#                if event.modifiers() != Qt.ControlModifier:
                self.edtFindByCode.keyPressEvent(event)
                return True
            return False
        elif obj == self.cmbMKB:
            if event.type() == QEvent.KeyPress:
                if event.key() == Qt.Key_Tab:
                    return False
                else:
                    self.cmbMKB.keyPressEvent(event)
                    return True
            return False
        elif obj == self.cmbMKBEx:
            if event.type() == QEvent.KeyPress:
                if event.key() == Qt.Key_Tab:
                    return False
                else:
                    self.cmbMKBEx.keyPressEvent(event)
                    return True
            return False
        else:
            if event.type() == QEvent.KeyPress:
                key = event.key()
                if key == Qt.Key_Space:
                    index = self.tblActionTypes.currentIndex()
                    currentValue = forceInt(self.modelActionTypes.data(
                                            self.modelActionTypes.createIndex(index.row(), 0),
                                            Qt.CheckStateRole))
                    value = 2 if currentValue == 0 else 0
                    if self.modelActionTypes.setData(index, value, Qt.CheckStateRole):
                        self.edtFindByCode.selectAll()
                    self.tblActionTypes.model().emitDataChanged()
                    return True
        return False


    def needAddSelected(self):
        if self.focusOnAdd:
            self.on_btnAdd_clicked()
            self.focusOnAdd = False
            return True
        return False


    @pyqtSignature('int')
    def on_tabWidget_currentChanged(self, index):
        widget = self.tabWidget.widget(index)
        if widget is not None:
            focusProxy = widget.focusProxy()
            if focusProxy:
                focusProxy.setFocus(Qt.OtherFocusReason)
        if index == 2: # amb card page
            self.tabAmbCard.resetWidgets()


    def keyPressEvent(self, event):
        modifier = event.modifiers()
        key = event.key()
        if event.type() == QEvent.KeyPress:
            if key not in (Qt.Key_Control, Qt.Key_Alt, Qt.Key_Shift):
                if self.tabWidget.currentWidget() == self.tabToken:
                    self.edtFindByCode.setFocus()
                    self.edtFindByCode.keyPressEvent(event)
            if key == Qt.Key_F9:
                CItemEditorBaseDialog.keyPressEvent(self, event)
            elif key in (Qt.Key_Enter, Qt.Key_Return):
                if modifier == Qt.ControlModifier:
                    if bool(self.itemId()):
                        if not self.needAddSelected():
                            self.accept()
                    else:
                        if not self.needAddSelected():
                            self.makeNextStep()
                else:
                    if not self.needAddSelected():
                        self.accept()
            elif key == Qt.Key_F2:
                if self.tabWidget.currentWidget() == self.tabToken:
                    self.tblActionTypes.setFocus(Qt.ShortcutFocusReason)
                CItemEditorBaseDialog.keyPressEvent(self, event)
            elif key in (Qt.Key_Up, Qt.Key_Down):
                self.tblActionTypes.keyPressEvent(event)
                CItemEditorBaseDialog.keyPressEvent(self, event)
            else:
                CItemEditorBaseDialog.keyPressEvent(self, event)
        else:
            CItemEditorBaseDialog.keyPressEvent(self, event)


    def setActionTypeClasses(self, actionTypeClasses):
        self.actionTypeClasses = actionTypeClasses
        self.modelActionTypeGroups.setClasses(actionTypeClasses)
        self.modelActionTypeGroups.setClassesVisible(len(actionTypeClasses)>1)


    def setActionTypeIdListInTabActions(self):
        db = QtGui.qApp.db
        tableActionType = db.table('ActionType')
        self.tabActions.modelAPActions.actionTypeIdList = db.getIdList('ActionType', 'id',  [tableActionType['showInForm'].ne(0), tableActionType['deleted'].eq(0)])


    def prepareFromCycle(self, contractId, clientId, eventTypeId, orgId, personId, eventSetDatetime, eventDatetime, weekProfile, numDays, presetDiagnostics, presetActions, disabledActions, externalId, assistantId, curatorId, movingActionTypeId = None, valueProperties = [], contractIdToCmbContract=None):
        if contractIdToCmbContract:
            self.cmbContract.setValue(contractIdToCmbContract)
        return self._prepare(contractId, clientId, eventTypeId, orgId, personId, eventSetDatetime, eventDatetime, weekProfile, numDays, presetDiagnostics, presetActions, disabledActions, externalId, assistantId, curatorId, movingActionTypeId, valueProperties)


    def _prepare(self, contractId, clientId, eventTypeId, orgId, personId, eventSetDatetime, eventDatetime, weekProfile, numDays, presetDiagnostics,
                 presetActions, disabledActions, externalId, assistantId, curatorId, movingActionTypeId = None, valueProperties = [],
                 relegateOrgId = None, relegatePersonId=None, diagnos = None, financeId = None, protocolQuoteId = None,
                 actionByNewEvent = [], eventOrder = 1, relegateInfo=[], plannedEndDate = None, isEdit = False):
        def getPrimary(clientId, eventTypeId, personId):
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
                    tableP2['id'].eq(personId),
                    ]
            record = db.getRecordEx(table, tableEvent['nextEventDate'].name(), cond, order=tableEvent['execDate'].name()+' DESC')
            return not(record and not record.value('nextEventDate').isNull())
        if not isEdit:
            self.eventSetDateTime = eventSetDatetime if isinstance(eventSetDatetime, QDateTime) else QDateTime(eventSetDatetime)
            self.eventDate = eventDatetime.date() if isinstance(eventDatetime, QDateTime) else eventDatetime
            self.setOrgId(orgId if orgId else QtGui.qApp.currentOrgId())
            self.setEventTypeId(eventTypeId)
            self.setClientId(clientId)
            self.prolongateEvent = True if actionByNewEvent else False
            self.tabNotes.setNotesEx(externalId, assistantId, curatorId, relegateOrgId, relegatePersonId, clientId, relegateInfo)
            self.setExternalId(externalId)
            self.cmbExecPerson.setValue(personId)
            self.setEnabledChkCloseEvent(self.eventDate)
            setPerson = getEventSetPerson(self.eventTypeId)
            if setPerson == 0:
                self.cmbSetPerson.setValue(personId)
            elif setPerson == 1:
                self.cmbSetPerson.setValue(QtGui.qApp.userId)
            if getEventIsTakenTissue(self.eventTypeId):
                self.cmbTissueExecPerson.setValue(personId)
                if self.clientSex and self.clientSex != 0:
                    cmbTissueTypeFilter = 'sex IN (0,%d)'%self.clientSex
                    tissueTypeId = self.cmbTissueType.value()
                    self.cmbTissueType.setFilter(cmbTissueTypeFilter)
                    self.cmbTissueType.setValue(tissueTypeId)
    #            datetimeTaken = QDateTime.currentDateTime()
                datetimeTaken = self.eventSetDateTime
                self.edtTissueDate.setDate(datetimeTaken.date())
                self.edtTissueTime.setTime(datetimeTaken.time())
            self.edtBegDate.setDate(self.eventSetDateTime.date())
            self.edtEndDate.setDate(self.eventDate)
            self.edtBegTime.setTime(eventSetDatetime.time() if isinstance(eventSetDatetime, QDateTime) else QTime())
            self.edtEndTime.setTime(eventDatetime.time() if isinstance(eventDatetime, QDateTime) else QTime())
            self.cmbContract.setCurrentIndex(0)
            self.cmbOrder.setCurrentIndex(eventOrder)
            self.chkPrimary.setChecked(getEventIsPrimary(eventTypeId) == 0)
#            if self.cmbDiagnosticResult.model().rowCount() > 0:
#                self.cmbDiagnosticResult.setCurrentIndex(1)
#            else:
#                self.cmbDiagnosticResult.setCurrentIndex(0)
#            self.cmbDiagnosticResult.setValue(None)
            resultId = QtGui.qApp.session("F001_resultId")
            self.cmbResult.setValue(resultId)
            self.cmbDiagnosticResult.setValue(QtGui.qApp.session("F001_DiagnosticResultId"))
            self.cmbResult.setValue(None)
            self.initFocus()
        if presetDiagnostics:
            for MKB, dispanserId, healthGroupId, visitTypeId in presetDiagnostics:
                self.cmbMKB.setText(MKB)
        self.prepareActions(contractId, presetActions, disabledActions, movingActionTypeId, valueProperties, diagnos, financeId, protocolQuoteId, actionByNewEvent, plannedEndDate)
        self.setIsDirty(False)
        self.tabNotes.setEventEditor(self)
        return self.checkEventCreationRestriction() and self.checkDeposit()


    def prepare(self, clientId, eventTypeId, orgId, personId, eventSetDatetime, eventDatetime, weekProfile,
                numDays, externalId, assistantId, curatorId, flagHospitalization = False,
                movingActionTypeId = None, valueProperties = [], tissueTypeId=None, selectPreviousActions=False,
                relegateOrgId = None, relegatePersonId=None, diagnos = None, financeId = None,
                protocolQuoteId = None, actionByNewEvent = [], order = 1, actionListToNewEvent = [],
                typeQueue = -1, docNum=None, relegateInfo=[], plannedEndDate = None, mapJournalInfoTransfer = [], voucherParams = {}, isEdit=False):
        self.setPersonId(personId)
        self.needToSelectPreviousActions = selectPreviousActions
        eventDate = eventDatetime.date() if isinstance(eventDatetime, QDateTime) else eventDatetime
        if not eventDate and eventSetDatetime:
            eventDate = eventSetDatetime.date() if isinstance(eventSetDatetime, QDateTime) else eventSetDatetime
        else:
            eventDate = QDate.currentDate()
        presentActionTypes = []
        for item in self.modelActionsSummary.items():
            actionTypeId = forceString(item.value('actionType_id'))
            if actionTypeId not in presentActionTypes:
                presentActionTypes.append(actionTypeId)
        form = getEventTypeForm(eventTypeId)
        if (form != u'090' and QtGui.qApp.userHasAnyRight([urAccessF001planner, urAdmin])) or (form == u'090' and QtGui.qApp.userHasAnyRight([urAccessF090planner,])):
            dlg = CPreF001Dialog(self, self.contractTariffCache)
            try:
                dlg.setBegDateEvent(eventSetDatetime.date() if isinstance(eventSetDatetime, QDateTime) else eventSetDatetime)
                dlg.prepare(clientId, eventTypeId, eventDate, self.personId, self.personSpecialityId, self.personTariffCategoryId, 
                            flagHospitalization, movingActionTypeId, tissueTypeId, presentActionTypes = presentActionTypes)
                if dlg.diagnosticsTableIsNotEmpty() or dlg.actionsTableIsNotEmpty():
                    if not dlg.exec_():
                        return False
                self.preDiagnostics = dlg.modelDiagnostics.items()
                self.preSpecialityIdList = dlg.preSpecialityIdList
                self.isSelectionGroupOne = dlg.isSelectionGroupOne
                self.prepareSettings = {'contractId':dlg.contractId, 'clientId':clientId, 'eventTypeId':eventTypeId, 'orgId':orgId, 'personId':personId, 'eventSetDatetime':eventSetDatetime, 'eventDatetime':eventDatetime, 'weekProfile':weekProfile, 'numDays':numDays, 'presetDiagnostics':None, 'presetActions':None, 'disabledActions':None, 'externalId':externalId, 'assistantId':assistantId, 'curatorId':curatorId, 'movingActionTypeId':movingActionTypeId, 'valueProperties':valueProperties}

                result = self._prepare(dlg.contractId, clientId, eventTypeId, orgId, personId, eventSetDatetime, eventDatetime,
                                       weekProfile, numDays, dlg.diagnostics(), dlg.actions(), dlg.disabledActionTypeIdList,
                                       externalId, assistantId, curatorId, movingActionTypeId, valueProperties,
                                       relegateOrgId, relegatePersonId, diagnos, financeId, protocolQuoteId, actionByNewEvent,
                                       order, relegateInfo, plannedEndDate, isEdit)
                if result and dlg.contractId:
                    contractFinanceId = forceRef(QtGui.qApp.db.translate('Contract', 'id', dlg.contractId, 'finance_id'))
                    if contractFinanceId == getEventFinanceId(eventTypeId):
                        self.cmbContract.setValue(dlg.contractId)
                        self.prepareSettings.update({'contractIdToCmbContract':dlg.contractId})
                    else:
                        self.prepareSettings.update({'contractIdToCmbContract':None})
                else:
                    self.prepareSettings.update({'contractIdToCmbContract':None})
                self.cmbTissueType.setValue(tissueTypeId)
                return result
            finally:
                dlg.deleteLater()
        else:
            presets = CPreF001DagnosticAndActionPresets(clientId, eventTypeId, eventDate, self.personSpecialityId, flagHospitalization, movingActionTypeId, presentActionTypes = presentActionTypes)
            presets.setBegDateEvent(eventSetDatetime.date() if isinstance(eventSetDatetime, QDateTime) else eventSetDatetime)
            result = self._prepare(None, clientId, eventTypeId, orgId, personId, eventSetDatetime, eventDatetime, weekProfile, numDays,
                                   presets.unconditionalDiagnosticList, presets.unconditionalActionList, presets.disabledActionTypeIdList,
                                   externalId, assistantId, curatorId, None, [], relegateOrgId, relegatePersonId, diagnos, financeId,
                                   protocolQuoteId, actionByNewEvent, order, relegateInfo, plannedEndDate, isEdit)
            if result:
                self.cmbTissueType.setValue(tissueTypeId)
            return result


    def selectPreviousActions(self):
        actionTypeIdList = QtGui.qApp.db.getDistinctIdList('Action', 'actionType_id', 'event_id=(SELECT MAX(id) FROM Event WHERE eventType_id=%d)'%self.eventTypeId)
        currentIdList = self.tblActionTypes.model().idList()
        for actionTypeId in actionTypeIdList:
            if actionTypeId in currentIdList:
                self.setSelected(actionTypeId, True)


    def setContractId(self, contractId):
        if self.contractId != contractId:
            CEventEditDialog.setContractId(self, contractId)
            cols = self.tblActions.model().cols()
            if cols:
                cols[0].setContractId(contractId)
            self.tabCash.modelAccActions.setContractId(contractId)
            self.tabCash.updatePaymentsSum()


    def setOrgId(self, orgId):
        self.orgId = orgId
        self.cmbContract.setOrgId(orgId)
        self.cmbExecPerson.setOrgId(orgId)
        self.tabActions.setOrgId(orgId)


    def setEventTypeId(self, eventTypeId):
        CEventEditDialog.setEventTypeId(self, eventTypeId, u'Ф.001')
        self.modelActionsSummary.setEventTypeId(eventTypeId)
        self.modelActionTypes.setEventTypeId(eventTypeId)

        if not getEventIsTakenTissue(eventTypeId):
            self.tblActionTypes.hideColumn(self.modelActionTypes.colorColumnIndex)

        self.tabCash.windowTitle = self.windowTitle()

        if getEventIsTakenTissue(eventTypeId):
            self.grpTakenTissue.setVisible(True)
            QtGui.qApp.setCounterController(CCounterController(self))
        else:
            self.grpTakenTissue.setVisible(False)

        showTime = getEventShowTime(eventTypeId)
        self.getShowButtonAccount()
        self.getShowButtonTemperatureList()
        self.getShowButtonNomenclatureExpense()
        self.getShowButtonJobTickets()
        self.edtBegTime.setVisible(showTime)
        self.edtEndTime.setVisible(showTime)
        self.cmbDiagnosticResult.setTable('rbDiagnosticResult', True, 'eventPurpose_id=\'%d\'' % self.eventPurposeId)
        self.cmbResult.setTable('rbResult', True, 'eventPurpose_id=\'%d\'' % self.eventPurposeId)
        self.cmbContract.setEventTypeId(eventTypeId)

        toggled = getEventLimitActionTypes(self.eventTypeId)
        self.chkConstraintActionTypes.setChecked(toggled)
        self.chkConstraintActionTypes.emit(SIGNAL('toggled(bool)'), toggled)
        customizePrintButton(self.btnPrint, self.eventContext if self.eventContext else 'F001')
        eventTypeCode = getEventCode(eventTypeId)
        if eventTypeCode == u'УО':
            self.tabWidget.setCurrentIndex(1)


    def initFocus(self):
        if self.cmbContract.count() != 1:
            self.cmbContract.setFocus(Qt.OtherFocusReason)


    def prepareActions(self, contractId, presetActions, disabledActions, actionTypeIdValue, valueProperties, diagnos, financeId, protocolQuoteId, actionByNewEvent, plannedEndDate=None):
        def addActionType(actionTypeId, amount, financeId, contractId, idListActionType, idListActionTypeIPH, actionFinance, idListActionTypeMoving, plannedEndDate):
            db = QtGui.qApp.db
            tableOrgStructure = db.table('OrgStructure')
            for iModel, tab in enumerate(self.getActionsTabsList()):
                model = tab.modelAPActions
                if actionTypeId in model.actionTypeIdList:
                    if actionTypeId in idListActionType and not actionByNewEvent:
                        model.addRow(actionTypeId, amount, financeId, contractId)
                        i = self.modelActionsSummary.itemIndex.index((iModel, model.rowCount()-2))
                        self.onActionChanged(i)
                        record, action = model.items()[-1]
                        # if plannedEndDate:
                        #     record.setValue('directionDate', QVariant(plannedEndDate))
                        if u'Приемное отделение' in action._actionType._propertiesByName:
                            curOrgStructureId = QtGui.qApp.currentOrgStructureId()
                            if curOrgStructureId:
                                recOS = db.getRecordEx(tableOrgStructure,
                                               [tableOrgStructure['id']],
                                               [tableOrgStructure['deleted'].eq(0),
                                                tableOrgStructure['id'].eq(curOrgStructureId),
                                                tableOrgStructure['type'].eq(4)])
                                if recOS:
                                    curOSId = forceRef(recOS.value('id'))
                                    action[u'Приемное отделение'] = curOSId if curOSId else None
                        if valueProperties and len(valueProperties) > 0 and valueProperties[0]:
                            action[u'Направлен в отделение'] = valueProperties[0]
                        if protocolQuoteId:
                            action[u'Квота'] = protocolQuoteId
                        if actionFinance == 0:
                            record.setValue('finance_id', toVariant(financeId))
                    elif actionTypeId in idListActionTypeIPH:
                        model.addRow(actionTypeId, amount, financeId, contractId)
                        i = self.modelActionsSummary.itemIndex.index((iModel, model.rowCount()-2))
                        self.onActionChanged(i)
                        record, action = model.items()[-1]
                        if diagnos:
                            record, action = model.items()[-1]
                            action[u'Диагноз'] = diagnos
                    #[self.eventActionFinance, self.receivedFinanceId, orgStructureTransfer, orgStructurePresence, oldBegDate, movingQuoting, personId]
                    elif actionByNewEvent and actionTypeId in idListActionTypeMoving:
                        model.addRow(actionTypeId, amount, financeId, contractId)
                        i = self.modelActionsSummary.itemIndex.index((iModel, model.rowCount()-2))
                        self.onActionChanged(i)
                        record, action = model.items()[-1]
                        if actionByNewEvent[0] == 0:
                            record.setValue('finance_id', toVariant(actionByNewEvent[1]))
                        action[u'Отделение пребывания'] = actionByNewEvent[2]
                        if actionByNewEvent[3]:
                            action[u'Переведен из отделения'] = actionByNewEvent[3]
                        if actionByNewEvent[4]:
                            record.setValue('begDate', toVariant(actionByNewEvent[4]))
                        else:
                            record.setValue('begDate', toVariant(QDateTime.currentDateTime()))
                        if u'Квота' in action._actionType._propertiesByName and actionByNewEvent[5]:
                            action[u'Квота'] = actionByNewEvent[5]
                        if actionByNewEvent[6]:
                            record.setValue('person_id', toVariant(actionByNewEvent[6]))
                    elif (actionByNewEvent and actionTypeId not in idListActionType) or not actionByNewEvent:
                        model.addRow(actionTypeId, amount, financeId, contractId)
                        i = self.modelActionsSummary.itemIndex.index((iModel, model.rowCount()-2))
                        self.onActionChanged(i)
                        record, action = model.items()[-1]

        def disableActionType(actionTypeId):
            for model in (self.tabStatus.modelAPActions,
                          self.tabDiagnostic.modelAPActions,
                          self.tabCure.modelAPActions,
                          self.tabMisc.modelAPActions):
                if actionTypeId in model.actionTypeIdList:
                    model.disableActionType(actionTypeId)
                    break

        if disabledActions:
            for actionTypeId in disabledActions:
                disableActionType(actionTypeId)
        if presetActions:
            db = QtGui.qApp.db
            tableActionType = db.table('ActionType')
            tableEventType = db.table('EventType')
            idListActionType = db.getIdList(tableActionType, [tableActionType['id']], [tableActionType['flatCode'].like(u'received%'), tableActionType['showInForm'].ne(0), tableActionType['deleted'].eq(0)])
            idListActionTypeIPH = db.getIdList(tableActionType, [tableActionType['id']], [tableActionType['flatCode'].like(u'inspectPigeonHole%'), tableActionType['showInForm'].ne(0), tableActionType['deleted'].eq(0)])
            idListActionTypeMoving = db.getIdList(tableActionType, [tableActionType['id']], [tableActionType['flatCode'].like(u'moving%'), tableActionType['showInForm'].ne(0), tableActionType['deleted'].eq(0)])
            eventTypeId = self.getEventTypeId()
            actionFinance = None
            if eventTypeId:
                recordET = db.getRecordEx(tableEventType, [tableEventType['actionFinance']], [tableEventType['deleted'].eq(0), tableEventType['id'].eq(eventTypeId)])
                actionFinance = forceInt(recordET.value('actionFinance')) if recordET else None
            if actionByNewEvent:
                actionTypeMoving = False
                for actionTypeId, amount, cash in presetActions:
                    if actionTypeId in idListActionTypeMoving:
                        actionTypeMoving = True
                        break
                if not actionTypeMoving and idListActionTypeMoving:
                    presetActions.append((idListActionTypeMoving[0], 1.0, False))
            for actionTypeId, amount, cash in presetActions:
                addActionType(actionTypeId, amount, financeId if cash else None, contractId if cash else None, idListActionType, idListActionTypeIPH, actionFinance, idListActionTypeMoving, plannedEndDate)


    def setRecord(self, record):
        CEventEditDialog.setRecord(self, record)
        setDatetimeEditValue(self.edtBegDate, self.edtBegTime, record, 'setDate')
        setDatetimeEditValue(self.edtEndDate, self.edtEndTime, record, 'execDate')
        setRBComboBoxValue(self.cmbExecPerson,      record, 'execPerson_id')
        setRBComboBoxValue(self.cmbSetPerson, record, 'setPerson_id')
        self.setExternalId(forceString(record.value('externalId')))
        self.cmbOrder.setCurrentIndex(forceInt(record.value('order'))-1)
        self.setPersonId(self.cmbExecPerson.value())
        setRBComboBoxValue(self.cmbContract, record, 'contract_id')
        self.chkPrimary.setChecked(forceInt(record.value('isPrimary'))==1)

        self._updateNoteByPrevEventId()
        self.tabNotes.setNotes(record)
        self.tabNotes.setEventEditor(self)
        self.loadActions()
        self.loadTakenTissue()
        if self.takenTissueRecord:
            self.setTissueWidgetsEditable(False)
            self.modelActionTypes.setTissueTypeId(self.cmbTissueType.value())
        self.loadDiagnostics(self.itemId())
        # установка значения self.cmbResult должна быть после loadDiagnostics,
        # так как иначе установка self.cmbDiagnosticResult затирает self.cmbResult
        setRBComboBoxValue(self.cmbResult,      record, 'result_id')
        self.tabCash.load(self.itemId())
        self.initFocus()
        self.on_cmbResult_currentIndexChanged()
        self.setIsDirty(False)
        self.protectClosedEvent()
        iniExportEvent(self)
        self.btnRelatedEventHighlight()


    def checkSpecialityExists(self, cmbPersonFind, personId):
        specialityId = forceRef(QtGui.qApp.db.translate('Person', 'id', personId, 'speciality_id'))
        if not specialityId:
            cmbPersonFind.setSpecialityIndependents()


    def loadTakenTissue(self):
        if self.takenTissueRecord:
            self.cmbTissueType.blockSignals(True)
            self.edtTissueDate.blockSignals(True)
            execPersonId = forceRef(self.takenTissueRecord.value('execPerson_id'))
            self.checkSpecialityExists(self.cmbTissueExecPerson, execPersonId)
            self.cmbTissueType.setValue(forceRef(self.takenTissueRecord.value('tissueType_id')))
            self.edtTissueExternalId.setText(forceString(self.takenTissueRecord.value('externalId')))
            self.edtTissueNumber.setText(forceString(self.takenTissueRecord.value('number')))
            self.edtTissueAmount.setValue(forceInt(self.takenTissueRecord.value('amount')))
            self.cmbTissueUnit.setValue(forceRef(self.takenTissueRecord.value('unit_id')))
            self.cmbTissueExecPerson.setValue(execPersonId)
            self.edtTissueNote.setText(forceString(self.takenTissueRecord.value('note')))
            datetimeTaken = forceDateTime(self.takenTissueRecord.value('datetimeTaken'))
            self.edtTissueDate.setDate(datetimeTaken.date())
            self.edtTissueTime.setTime(datetimeTaken.time())
            self.edtTissueExternalId.setReadOnly(True)
            self.cmbTissueType.blockSignals(False)
            self.edtTissueDate.blockSignals(False)
        else:
            self.setTissueWidgetsEditable(True)
            self.edtTissueExternalId.setReadOnly(False)


    def setTissueWidgetsEditable(self, val):
        self.cmbTissueType.setEnabled(val)
        self.edtTissueExternalId.setEnabled(val)
        self.edtTissueNumber.setEnabled(val)
        self.edtTissueAmount.setEnabled(val)
        self.cmbTissueUnit.setEnabled(val)
        self.cmbTissueExecPerson.setEnabled(val)
        self.edtTissueNote.setEnabled(val)
        self.edtTissueDate.setEnabled(val)
        self.edtTissueTime.setEnabled(val)


    def loadActions(self):
        items = self.loadActionsInternal()
        actions = []
        for key in items.keys():
            actions.extend(items[key])
        self.tabActions.loadActions(actions)
        if getEventIsTakenTissue(self.eventTypeId):
            for record, action in self.tabActions.modelAPActions.items():
                takenTissueJournalId = forceRef(record.value('takenTissueJournal_id'))
                if takenTissueJournalId:
                    self.takenTissueRecord = QtGui.qApp.db.getRecord('TakenTissueJournal', '*', takenTissueJournalId)
                    break
        self.modelActionsSummary.regenerate()
        self.tabCash.modelAccActions.regenerate()


    def getRecord(self):
        record = CEventEditDialog.getRecord(self)
        showTime = getEventShowTime(self.eventTypeId)
        self.getShowButtonAccount()
        self.getShowButtonTemperatureList()
        self.getShowButtonNomenclatureExpense()
        self.getShowButtonJobTickets()
        getRBComboBoxValue(self.cmbContract,    record, 'contract_id')
        getDatetimeEditValue(self.edtBegDate, self.edtBegTime, record, 'setDate', showTime)
        getRBComboBoxValue(self.cmbSetPerson,      record, 'setPerson_id')
        getDatetimeEditValue(self.edtEndDate, self.edtEndTime, record, 'execDate', showTime)
        getRBComboBoxValue(self.cmbExecPerson,      record, 'execPerson_id')
        record.setValue('order',  toVariant(self.cmbOrder.currentIndex()+1))
        self.tabNotes.getNotes(record, self.eventTypeId)
        record.setValue('isPrimary', toVariant(1 if self.chkPrimary.isChecked() else 2))
        if self.prolongateEvent:
            record.setValue('order', toVariant(5))
#        diagnosticResultId = self.cmbDiagnosticResult.value()
#        eventResultId = QtGui.qApp.db.translate('rbDiagnosticResult', 'id', diagnosticResultId, 'result_id')
#        record.setValue('result_id', eventResultId)
        getRBComboBoxValue(self.cmbResult,      record, 'result_id')
        self.saveTakenTissueRecord()
        # Это хак: удаляем payStatus из записи
        result = type(record)(record) # copy record
        result.remove(result.indexOf('payStatus'))
        return result


    def hasAnyAction(self):
        tabs = [self.tabActions]
        for tab in tabs:
            if self.hasTabAnyAction(tab):
                return True
        return False


    def hasTabAnyAction(self, tab):
        return bool(len(tab.modelAPActions.items()))


    def saveTakenTissueRecord(self):
        if getEventIsTakenTissue(self.eventTypeId):
            canBeSaved = bool(not self.takenTissueRecord) and bool(self.cmbTissueType.value()) and self.hasAnyAction()
            if canBeSaved:
                db = QtGui.qApp.db
                table = db.table('TakenTissueJournal')
                record = table.newRecord()
                tissueTypeId = self.cmbTissueType.value()
                record.setValue('client_id', QVariant(self.clientId))
                record.setValue('tissueType_id', QVariant(tissueTypeId))
#                externalIdValue = self.recountExternalId()
#                record.setValue('externalId', QVariant(externalIdValue))
                record.setValue('externalId', QVariant(self.edtTissueExternalId.text()))
                record.setValue('number', QVariant(self.edtTissueNumber.text()))
                record.setValue('amount', QVariant(self.edtTissueAmount.value()))
                record.setValue('unit_id', QVariant(self.cmbTissueUnit.value()))
                execPersonId = self.cmbTissueExecPerson.value()
                if not execPersonId:
                    execPersonId = QtGui.qApp.userId
                record.setValue('execPerson_id', QVariant(execPersonId))
                record.setValue('note', QVariant(self.edtTissueNote.text()))
                isRealTimeProcessing = forceInt(db.translate('rbTissueType', 'id', tissueTypeId, 'isRealTimeProcessing'))
                if isRealTimeProcessing:
                    currentDateTime = QDateTime.currentDateTime()
                    self.edtTissueDate.setDate(currentDateTime.date())
                    self.edtTissueTime.setTime(currentDateTime.time())
                datetimeTaken = QDateTime()
                datetimeTaken.setDate(self.edtTissueDate.date())
                datetimeTaken.setTime(self.edtTissueTime.time())
                record.setValue('datetimeTaken', QVariant(datetimeTaken))
                recordId = db.insertRecord(table, record)
                record.setValue('parent_id', QVariant(recordId))
                db.updateRecord(table, record)
                self.takenTissueRecord = record


    def getSetPersonId(self):
        return self.cmbSetPerson.value()


    def getExecPersonId(self):
        return self.cmbExecPerson.value()


    def getEventInfo(self, context):
        result = CEventEditDialog.getEventInfo(self, context)
        db = QtGui.qApp.db
        # инициализация свойств
        result._isPrimary = self.chkPrimary.isChecked()+1
        result._diagnosises = [CDiagnosticInfo(context, None)]
        for item in result._diagnosises:
            item._loaded = True
            item._ok = True
            if self.chkDiagnosisType.isChecked():
                diagnosisTypeId = forceRef(db.translate('rbDiagnosisType', 'code', '7', 'id'))
            else:
                diagnosisTypeId = forceRef(db.translate('rbDiagnosisType', 'code', '1', 'id'))
            item._type = context.getInstance(CDagnosisTypeInfo, diagnosisTypeId)
            item._MKB = context.getInstance(CMKBInfo, unicode(self.cmbMKB.text()))
            item._MKBEx = context.getInstance(CMKBInfo, unicode(self.cmbMKBEx.text()))
            item._morphologyMKB = context.getInstance(CMorphologyMKBInfo, unicode(self.cmbMorphology.text()))
            item._character     = context.getInstance(CCharacterInfo, forceRef(self.cmbCharacter.value()))
            item._traumaType    = context.getInstance(CTraumaTypeInfo, forceRef(self.cmbTraumaType.value()))
            item._toxicSubstances = context.getInstance(CToxicSubstancesInfo, forceRef(self.cmbToxicSubstances.value()))
            item._person        = context.getInstance(CPersonInfo, forceRef(self.cmbExecPerson.value()))
            item._result        = context.getInstance(CDiagnosticResultInfo, forceRef(self.cmbDiagnosticResult.value()))
            item._freeInput         = self.edtFreeInput.text()
        # инициализация таблиц
        result._actions = CActionInfoProxyList(context,
                [self.tabActions.modelAPActions],
                result)
        return result


    def saveInternals(self, eventId):
        self.saveActions(eventId)
        self.saveDiagnostics(eventId)
        self.tabCash.save(eventId)
        self.tabNotes.saveAttachedFiles(eventId)
        self.saveTrailerActions(eventId)


    def saveTrailerActions(self, eventId):
        if self.trailerActions:
            for action in self.trailerActions:
                prevActionId = self.trailerIdList.get(action.trailerIdx - 1, None)
                action.getRecord().setValue('prevAction_id', toVariant(prevActionId))
                action.save(eventId)


    def saveActions(self, eventId):
        if self.takenTissueRecord:
            tissueType = forceRef(self.takenTissueRecord.value('tissueType_id'))
            actualByTissueTypeList, actionTypeIdList = self.actualByTissueType.get(tissueType, ([], []))
            id = forceRef(self.takenTissueRecord.value('id'))
            self.tabActions.setCommonTakenTissueJournalRecordId(id, actionTypeIdList)
        self.tabActions.saveActions(eventId)

    
    def afterSave(self):
        CEventEditDialog.afterSave(self)
        QtGui.qApp.session("F001_resultId", self.cmbResult.value())
        QtGui.qApp.session("F001_DiagnosticResultId", self.cmbDiagnosticResult.value())


    def setAPSetPersonWhereNot(self):
        items = self.tabActions.modelAPActions.items()
        for item, action in items:
            if not forceRef(item.value('setPerson_id')):
                item.setValue('setPerson_id', QVariant(self.cmbSetPerson.value()))


    def checkDataEntered(self):
        showTime = getEventShowTime(self.eventTypeId)
        if showTime:
            begDate = QDateTime(self.edtBegDate.date(), self.edtBegTime.time())
            endDate = QDateTime(self.edtEndDate.date(), self.edtEndTime.time())
        else:
            begDate = self.edtBegDate.date()
            endDate = self.edtEndDate.date()
        self.actionsRowNotForAdding = {}
        result = CEventEditDialog.checkDataEntered(self)
        result = result and self.checkSelectedActions()
        eventTypeCode = getEventCode(self.eventTypeId)
        if result and eventTypeCode == u'УО':
            actionEndDate = self.tabActions.edtAPEndDate.date()
            cancelDate = QDate()
            cancelProp = self.tabActions.tblAPProps.model().action.getPropertiesByName().get(u'Дата аннулирования', None)
            if cancelProp:
                cancelDate = cancelProp.getValue()
            if actionEndDate or cancelDate:
                self.edtEndDate.setDate(actionEndDate or cancelDate)
            if not self.cmbExecPerson.value():
                self.cmbExecPerson.setValue(QtGui.qApp.userId)
            if not self.cmbSetPerson.value():
                self.cmbSetPerson.setValue(QtGui.qApp.userId)
        if eventTypeCode != u'УО':
            result = result and (self.cmbExecPerson.value() or self.checkInputMessage(u'ответственного', True, self.cmbExecPerson))
        result = result and (self.cmbSetPerson.value() or self.checkInputMessage(u'назначившего', False, self.cmbSetPerson))
        

        # fix ТТ 1056 "Убрать контроль на заполненность даты выполнения/результата осмотра/лечения в форме 001"
        # result = result and (not self.edtEndDate.date().isNull() or self.checkEndDate())
        if self.edtEndDate.date().isValid():
            lpuCode = forceString(QtGui.qApp.db.translate('Organisation', 'id', QtGui.qApp.currentOrgId(), 'infisCode'))
            # для центра охраны семьи в КК отключаем проверки диагноза, результата осмотра и результата обращения
            if not (forceString(QtGui.qApp.preferences.appPrefs.get('provinceKLADR', '00'))[:2] == '23' and lpuCode == '07541'):
                result = result and self.checkDiagnosisDataEntered()
                result = result and (self.cmbDiagnosticResult.value() or self.checkInputMessage(u'результат осмотра', True, self.cmbDiagnosticResult))
                result = result and (self.cmbResult.value() or self.checkInputMessage(u'результат обращения', True, self.cmbResult))

        if getEventIsTakenTissue(self.eventTypeId):
            result = result and (self.cmbTissueType.value() or self.checkInputMessage(u'тип ткани', True, self.cmbTissueType))
            if self.edtTissueAmount.value() > 0:
                result = result and (self.cmbTissueUnit.value() or self.checkInputMessage(u'ед. измерения', True, self.cmbTissueUnit))
            result = result and self.checkIsSameTissueTypeExistsTodayForCurrentClient()
        result = result and self.checkActionsDataEntered(begDate, endDate)
        result = result and self.checkDeposit(True)
        result = result and self.checkSaveTakenTissue()
        result = result and self.checkUniqueTissueExternalId()
        result = result and self.tabCash.checkDataLocalContract()
        if not result:
            self.updateTreeData()
        else:
            self.setAPSetPersonWhereNot()
        self.removeRowsForModel(self.actionsRowNotForAdding)
        if self.edtEndDate.date():
            result = result and self.checkAndUpdateExpertise(self.edtEndDate.date(), self.cmbExecPerson.value())
        result = result and self.selectNomenclatureAddedActions([self.tabActions])
        return result
    
    
    def checkExecPersonSpecialityEx(self, message, personId, widget):
        specialityId = forceRef(QtGui.qApp.db.translate('Person', 'id', personId, 'speciality_id'))
        if not specialityId:
            self.checkValueMessage(u'У %s не указана специальность. Выберите врача со специальностью.'%(message), False, widget)
            return False
        return True
    

    def checkDiagnosisDataEntered(self):
        result = True
        MKB = forceString(self.cmbMKB.text())
        if MKB:
        #result = result and (MKB or self.checkInputMessage(u'диагноз', True, self.cmbMKB))
            result = result and self.checkDiagnosis(MKB)
            result = result and self.checkActualMKB(self.cmbMKB, self.edtBegDate.date(), MKB)
            if result:
                char = MKB[:1]
                blockMKB = forceInt(MKB[1:3])
                traumaTypeId = self.cmbTraumaType.value()
                if char in 'ST' and not (char in 'T' and 36 <= blockMKB <= 78):
                    if not traumaTypeId:
                        result = self.checkValueMessage(u'Необходимо указать тип травмы',  True if QtGui.qApp.controlTraumaType()==0 else False, self.cmbTraumaType)
                if char not in 'ST' and traumaTypeId:
                    result = self.checkValueMessage(u'Необходимо удалить тип травмы',  True if QtGui.qApp.controlTraumaType()==0 else False, self.cmbTraumaType)
                result = result and self.checkExecPersonSpecialityEx(u'ответственного', self.cmbExecPerson.value(), self.cmbExecPerson)
                result = result and self.checkExecPersonSpecialityEx(u'назначившего', self.cmbSetPerson.value(), self.cmbSetPerson)
        result = result and (self.cmbDiagnosticResult.value() or self.checkInputMessage(u'результат осмотра', True, self.cmbDiagnosticResult))
        return result


    def checkDiagnosis(self, MKB):
        diagFilter = None
        return checkDiagnosis(self, MKB, diagFilter, self.clientId, self.clientSex, self.clientAge, self.edtBegDate.date())


    def checkSelectedActions(self):
        if len(self.selectedActionTypeIdList) > 0:
            buttons = QtGui.QMessageBox.Ok | QtGui.QMessageBox.Ignore | QtGui.QMessageBox.Cancel
            res = QtGui.QMessageBox.warning( self,
                                             u'Внимание',
                                             u'Имееются выделенные и не добавленные действия.\nДобавить?',
                                             buttons,
                                             QtGui.QMessageBox.Cancel)
            if res == QtGui.QMessageBox.Ok:
                self.on_btnAdd_clicked()
                self.focusOnAdd = False
            elif res == QtGui.QMessageBox.Cancel:
                return False
        return True


    def checkUniqueTissueExternalId(self):
        if self._manualInputExternalId:
            if not bool(self.takenTissueRecord):
                tissueType = self.cmbTissueType.value()
                if not tissueType:
                    return True
                needCountValueStr = unicode(self.edtTissueExternalId.text()).lstrip('0')
                if not self.isValidExternalId(needCountValueStr):
                    return False
                needCountValue = int(needCountValueStr)
                if self._manualInputExternalId:
                    existCountValue = needCountValue
                else:
                    existCountValue = needCountValue - 1
                if existCountValue < 0:
                    return self.checkInputMessage(u'другой идентификатор больше нуля', False, self.edtTissueExternalId)
                self.setTissueExternalId(existCountValue)
                date = self.edtTissueDate.date()
                if date:
                    cond = [self.tableTakenTissueJournal['deleted'].eq(0),
                            self.tableTakenTissueJournal['tissueType_id'].eq(tissueType),
                            self.tableTakenTissueJournal['externalId'].eq(self.edtTissueExternalId.text())]
                    dateCond = self.getRecountExternalIdDateCond(tissueType, date)
                    if dateCond:
                        cond.append(dateCond)
                    record = QtGui.qApp.db.getRecordEx(self.tableTakenTissueJournal, 'id', cond)
                    if record and forceRef(record.value('id')):
                        return self.checkInputMessage(u'другой идентификатор.\nТакой уже существует', False, self.edtTissueExternalId)
        return True

    def isValidExternalId(self, needCountValueStr):
        if not needCountValueStr.isdigit():
            return self.checkInputMessage(u'корректный идентификатор.', False, self.edtTissueExternalId)
        return True

    def checkSaveTakenTissue(self):
        tissueType = self.cmbTissueType.value()
        if bool(tissueType):
            actualByTissueTypeList, actionTypeIdList = self.actualByTissueType.get(tissueType, ([], []))
#            if not bool(self.tabActions.modelAPActions.items()):
            if not bool(actionTypeIdList):
                res = self.makeMessageBox(u'Нет соответствующих ткани добавленных действий, забор ткани не зафиксируется!')
                if res == QtGui.QMessageBox.Ok:
                    self.setFocusToWidget(self.tblActionTypes, None, None)
                    return False
        return True


    def checkValueMessageIsSameTissue(self):
        title   = u'Внимание!'
        message = u'Сегодня у данного пациента уже был забор ткани этого типа!\nИспользовать данные предыдущего забора?'
        buttons = QtGui.QMessageBox.Ok | QtGui.QMessageBox.Ignore | QtGui.QMessageBox.Cancel
        res = QtGui.QMessageBox.warning( self,
                                         title,
                                         message,
                                         buttons,
                                         QtGui.QMessageBox.Cancel)
        return res


    def checkIsSameTissueTypeExistsTodayForCurrentClient(self):
        if not bool(self.takenTissueRecord):
            tissueTypeId = self.cmbTissueType.value()
            date = self.edtTissueDate.date()
            cond = [self.tableTakenTissueJournal['client_id'].eq(self.clientId),
                    self.tableTakenTissueJournal['tissueType_id'].eq(tissueTypeId),
                    self.tableTakenTissueJournal['datetimeTaken'].dateEq(date),
                    'EXISTS (SELECT id FROM Action WHERE Action.`deleted`=0 AND Action.`takenTissueJournal_id` = TakenTissueJournal.`id`)']
            record = QtGui.qApp.db.getRecordEx(self.tableTakenTissueJournal, '*', cond, 'datetimeTaken DESC')
            if record:
                res = self.checkValueMessageIsSameTissue()
                if res == QtGui.QMessageBox.Cancel:
                    self.setFocusToWidget(self.cmbTissueType, None, None)
                    return False
                elif res == QtGui.QMessageBox.Ok:
                    self.takenTissueRecord = record
                    self.loadTakenTissue()
                    self.setTissueWidgetsEditable(False)
        return True

    def checkExistsActionsForCurrentDay(self, row, record, action, actionTab):
        db = QtGui.qApp.db
        tableAction = db.table('Action')
        tableActionType = db.table('ActionType')
        tableEvent = db.table('Event')
        endDate = forceDate(record.value('endDate'))
        if not endDate:
            return True
        actionTypeId = forceRef(record.value('actionType_id'))
        cond = [tableEvent['client_id'].eq(self.clientId),
                tableAction['endDate'].eq(endDate),
                tableAction['deleted'].eq(0),
                tableActionType['deleted'].eq(0),
                tableActionType['showInForm'].ne(0)]
        eventId = self.itemId()
        if eventId:
            cond.append(tableEvent['id'].ne(eventId))
        cond.append(tableAction['actionType_id'].eq(actionTypeId))
        stmt = 'SELECT Action.`id` From Action INNER JOIN ActionType ON ActionType.`id`=Action.`actionType_id` INNER JOIN Event ON Event.`id`=Action.`event_id` WHERE %s' % db.joinAnd(cond)
        query = db.query(stmt)
        if query.first():
            res = self.askActionExistingQuestion(actionTab.tblAPActions, row, action._actionType.name)
            if not res:
                return False
        return True

    def removeRowsForModel(self, modelsRows):
        for model in modelsRows:
            rows = modelsRows.get(model)
            if rows:
                rows.sort(reverse=True)
                for row in rows:
                    model.removeRow(row)


    def askActionExistingQuestion(self, tbl, row, actionTypeName):
        buttons = QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel | QtGui.QMessageBox.Ignore
        res = QtGui.QMessageBox.question(self, u'Внимание!', u'Действие "%s" уже было выполненно с данным пациентом в этот день!'%actionTypeName, buttons, QtGui.QMessageBox.Ok)
        if res == QtGui.QMessageBox.Ok:
            self.setFocusToWidget(tbl, row, 0)
            return False
        elif res == QtGui.QMessageBox.Cancel:
            rows = self.actionsRowNotForAdding.get(tbl.model())
            if rows:
                rows.append(row)
            else:
                self.actionsRowNotForAdding[tbl.model()] = [row]
        return True

    def checkEndDate(self):
        res = self.makeMessageBox(u'Нужно ввести дату выполнения!', u'Текущее действие')
        if res == QtGui.QMessageBox.Ok:
            self.setFocusToWidget(self.edtEndDate, None, None)
            return False
        elif res == 0:
            d = self.tabActions.edtAPEndDate.date()
            self.edtEndDate.setDate(d if d else QDate.currentDate())
        return True

    def makeMessageBox(self, question, btnText=None):
        buttons = QtGui.QMessageBox.Ok
        buttons = buttons | QtGui.QMessageBox.Ignore
        messageBox = QtGui.QMessageBox()
        messageBox.setWindowFlags(messageBox.windowFlags() | Qt.WindowStaysOnTopHint)
        messageBox.setWindowTitle(u'Внимание!')
        messageBox.setText(question)
        messageBox.setStandardButtons(buttons)
        messageBox.setDefaultButton(QtGui.QMessageBox.Ok)
        if btnText:
            messageBox.addButton(QtGui.QPushButton(btnText), QtGui.QMessageBox.ActionRole)
        return messageBox.exec_()

    def updateTreeData(self, adding=False):
        if not self._dialogIsExecuted:
            return
        if not self.isSetConditionSettings:
            self.defineConditionSettings()
            self.isSetConditionSettings = True
        existsTypes = []
        inServicetabItems = self.tabActions.modelAPActions.items()
        for i in inServicetabItems:
            typeId = forceRef(i[0].value('actionType_id'))
            if typeId not in existsTypes:
                existsTypes.append(typeId)
        self.existsActionTypesList = existsTypes
        db = QtGui.qApp.db
        QtGui.qApp.setWaitCursor()
        if self.clientSex and self.clientAge:
            self.modelActionTypeGroups.setFilter(self.clientSex, self.clientAge)
        else:
            self.modelActionTypeGroups.setFilter(0, None)
        tableActionType = db.table('ActionType')
        if adding:
            index = self.treeActionTypeGroups.currentIndex()
#            if index.isValid() and index.internalPointer():
#                currentGroupId = index.internalPointer().id()
#            else:
#                currentGroupId = None
        else:
#            currentGroupId = None
            index = None
        cond = [tableActionType['showInForm'].ne(0), tableActionType['deleted'].eq(0)]
        if existsTypes:
            cond.append(tableActionType['id'].notInlist(existsTypes))
        if not self.planner:
            self.enabledActionTypes = enabledActionTypes = self.getOrgStructureActionTypes(existsTypes)
        elif self.planner:
            self.enabledActionTypes = enabledActionTypes = self.getPlannedActionTypes(existsTypes)
        else:
            self.enabledActionTypes = enabledActionTypes = db.getIdList('ActionType', 'id',  cond)
        if getEventIsTakenTissue(self.eventTypeId):
            if bool(self.cmbTissueType.value()):
                self.actionTypesByTissueType = self.getActionTypesByTissueType()
                self.enabledActionTypes = enabledActionTypes = [id for id in self.actionTypesByTissueType if id in enabledActionTypes]
        self.modelActionTypeGroups.setEnabledActionTypeIdList(enabledActionTypes)
        if not index:
            index = self.modelActionTypeGroups.createIndex(0, 0, self.modelActionTypeGroups.getRootItem())
        self.treeActionTypeGroups.setCurrentIndex(index)
        self.on_selectionModelActionTypeGroups_currentChanged(index)
        if not self.enabledActionTypes:
            self.clearGroup()
        if self.needToSelectPreviousActions:
            self.selectPreviousActions()
        QtGui.qApp.restoreOverrideCursor()
#        self.treeActionTypeGroups.reset()
        self.tblActionTypes.model().emitDataChanged()
        self.treeActionTypeGroups.expandAll()


    def getOrgStructureActionTypes(self, exists=[]):
        db = QtGui.qApp.db
        if True:#self.orgStructureActionTypes is None:
            if self.orgStructureId and self.chkConstraintActionTypes.isChecked():
                idSet = getOrgStructureActionTypeIdSet(self.orgStructureId)-set(exists)
                idList = db.getTheseAndParents('ActionType', 'group_id', list(idSet))
            else:
                tableActionType = db.table('ActionType')
                idList = set(db.getIdList(tableActionType, 'id', [tableActionType['deleted'].eq(0),
                                                                  tableActionType['showInForm'].ne(0),
                                                                  tableActionType['id'].notInlist(exists)]))

            self.orgStructureActionTypes = set(idList)
        return self.orgStructureActionTypes


    def clearGroup(self):
        self.tblActionTypes.setIdList([])


    def findByCode(self, value):
        uCode = unicode(value).upper()
        codes = self.actionsCacheByCode.keys()
        codes.sort()
        for c in codes:
            if unicode(c).startswith(uCode):
                self.edtFindByCode.setFocus()
                return self.actionsCacheByCode[c]

        return self.findByName(value)

    def findByName(self, name):
        uName = unicode(name).upper()
        names = self.actionsCodeCacheByName.keys()
        for n in names:
            if uName in n:
                code = self.actionsCodeCacheByName[n]
                return self.actionsCacheByCode.get(code, None)
        return None


    def isSelected(self, actionTypeId):
        return actionTypeId in self.selectedActionTypeIdList


    def setGroupId(self, groupId, _class=None):
        if not self.actionTypeClasses:
            return
        self.actionsCacheByCode.clear()
        self.actionsCodeCacheByName.clear()
        db = QtGui.qApp.db
        tableActionType = db.table('ActionType')

        cond = [tableActionType['deleted'].eq(0),
                tableActionType['showInForm'].ne(0),
                tableActionType['class'].inlist(self.actionTypeClasses)
               ]
        if groupId:
            groupIdList = self.getGroupIdList([groupId], tableActionType) + [groupId]
            cond.append(tableActionType['group_id'].inlist(groupIdList))
        if _class is not None:
            cond.append(tableActionType['class'].eq(_class))
        if self.enabledActionTypes:
            cond.append(tableActionType['id'].inlist(self.enabledActionTypes))
        else:
            return
#        if self.mesActionTypeIdList:
#            cond.append('NOT EXISTS(SELECT id FROM ActionType AS at WHERE ActionType.id NOT IN (%s) AND at.group_id = ActionType.id)'%(u','.join(str(mesActionTypeId) for mesActionTypeId in self.mesActionTypeIdList if mesActionTypeId)))
#        else:
        cond.append('NOT EXISTS(SELECT id FROM ActionType AS at WHERE at.group_id = ActionType.id)')
        if self.existsActionTypesList:
            cond.append(tableActionType['id'].notInlist(self.existsActionTypesList))
        recordList = QtGui.qApp.db.getRecordList(tableActionType, 'id, code, name', cond, 'code, name')
        if recordList:
            index  = 0
            idList = []
            for index, record in enumerate(recordList):
                id = forceRef(record.value('id'))
                code = forceString(record.value('code')).upper()
                name = forceString(record.value('name')).upper()
                idList.append(id)
                existCode = self.actionsCacheByCode.get(code, None)
                if existCode is None:
                    self.actionsCacheByCode[code] = index
                existName = self.actionsCodeCacheByName.get(name, None)
                if existName is None:
                    self.actionsCodeCacheByName[name] = code
        else:
            idList = []
        self.tblActionTypes.setIdList(idList)

    def getGroupIdList(self, groupIdList, table):
        if not groupIdList:
            return []
        resume = []
        cond = [table['showInForm'].ne(0), table['deleted'].eq(0)]
        for id in groupIdList:
            condTmp = list(cond)
            condTmp.append(table['group_id'].eq(id))
            idList = QtGui.qApp.db.getIdList(table.name(),
                                             'id', condTmp,
                                             'code, name')
            if idList:
                resume.append(id)
        return resume + self.getGroupIdList(idList, table)


    def invalidateChecks(self):
        model = self.modelActionTypes
        lt = model.index(0, 0)
        rb = model.index(model.rowCount()-1, 1)
        model.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), lt, rb)


    def getEventDataPlanning(self, eventId):
        if eventId:
            db = QtGui.qApp.db
            tableEvent = db.table('Event')
            tableEventType = db.table('EventType')
            cols = [tableEvent['patientModel_id'],
                    tableEvent['cureType_id'],
                    tableEvent['cureMethod_id'],
                    tableEvent['contract_id'],
                    tableEvent['externalId'],
                    tableEvent['note'],
                    tableEvent['setDate'],
                    tableEventType['name']
                    ]
            cond = [tableEvent['deleted'].eq(0),
                    tableEvent['id'].eq(eventId),
                    tableEventType['deleted'].eq(0)
                    ]
            table = tableEvent.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
            record = db.getRecordEx(table, cols, cond)
            if record:
                patientModelId = forceRef(record.value('patientModel_id'))
                if patientModelId:
                    self.tabNotes.cmbPatientModel.setValue(patientModelId)
                cureTypeId = forceRef(record.value('cureType_id'))
                if cureTypeId:
                    self.tabNotes.cmbCureType.setValue(cureTypeId)
                cureMethodId = forceRef(record.value('cureMethod_id'))
                if cureMethodId:
                    self.tabNotes.cmbCureMethod.setValue(cureMethodId)
                if self.prolongateEvent:
                    self.cmbContract.setValue(forceRef(record.value('contract_id')))
                    self.tabNotes.edtEventExternalIdValue.setText(forceString(record.value('externalId')))
                    self.tabNotes.edtEventNote.setText(forceString(record.value('note')))
                    self.prevEventId = eventId
                    self.lblProlongateEvent.setText(u'п')
                    self.tabNotes.edtPrevEventInfo.setText(u'Продолжение обращения: %s от %s.'%(forceString(record.value('name')), forceDate(record.value('setDate')).toString('dd.MM.yyyy')))
            self.createDiagnostics(eventId)


    def createDiagnostics(self, eventId):
        if eventId:
            self.loadDiagnostics(eventId)


    def loadDiagnostics(self, eventId):
        db = QtGui.qApp.db
        table = db.table('Diagnostic')
        tableDiagnosisType = db.table('rbDiagnosisType')
        diagnosisTypeIdList = []
        priorId = None
        recordsDT = db.getRecordList(tableDiagnosisType, '*', [tableDiagnosisType['code'].inlist([u'1', u'2', u'9', u'7'])])
        for recordDT in recordsDT:
            dtId = forceRef(recordDT.value('id'))
            diagnosisTypeIdList.append(dtId)
            if u'7' == forceString(recordDT.value('code')):
                priorId = dtId
        record = db.getRecordEx(table, '*', [table['deleted'].eq(0), table['event_id'].eq(eventId), table['diagnosisType_id'].inlist(diagnosisTypeIdList)], 'id')
        if record:
            diagnosisId     = forceRef(record.value('diagnosis_id'))
            characterId     = forceRef(record.value('character_id'))
            diagnosisTypeId = forceRef(record.value('diagnosisType_id'))
            resultId        = forceRef(record.value('result_id'))
            traumaTypeId    = forceRef(record.value('traumaType_id'))
            toxicSubstancesId = forceRef(record.value('toxicSubstances_id'))
            MKB             = forceString(db.translate('Diagnosis', 'id', diagnosisId, 'MKB'))
            MKBEx           = forceString(db.translate('Diagnosis', 'id', diagnosisId, 'MKBEx'))
            morphologyMKB   = forceString(db.translate('Diagnosis', 'id', diagnosisId, 'morphologyMKB'))
            freeInput       = forceString(record.value('freeInput'))
            if self.enableMorphology(MKB):
                self.cmbMorphology.setText(morphologyMKB)
            self.updateCharacterByMKB(MKB)
            self.updateToxicSubstancesIdListByMKB(MKB)
            self.cmbMKB.setText(MKB)
            self.cmbCharacter.setValue(characterId)
            self.chkDiagnosisType.setChecked(bool(diagnosisTypeId == priorId))
            self.cmbMKBEx.setText(MKBEx)
            if QtGui.qApp.isTNMSVisible():
                self.cmbTNMS.setMKB(forceStringEx(MKB))
                valueTNMS = forceStringEx(record.value('TNMS'))
                tnmsMap = {}
                for keyName, fieldName in CEventEditDialog.TNMSFieldsDict.items():
                    tnmsMap[keyName] = forceRef(record.value(fieldName))
                self.cmbTNMS.setValue(valueTNMS, tnmsMap)
            self.cmbTraumaType.setValue(traumaTypeId)
            self.cmbToxicSubstances.setValue(toxicSubstancesId)
            self.cmbDiagnosticResult.setValue(resultId)
            self.edtFreeInput.setText(freeInput)


    def enableMorphology(self, MKB):
        if MKB[-1:] == '.':
            MKB = MKB[:-1]
        result = False
        if QtGui.qApp.defaultMorphologyMKBIsVisible():
            if MKB:
                result = MKB[0] in self.MKB_allowed_morphology
        self.cmbMorphology.setEnabled(result)
        return result


    def updateCharacterByMKB(self, MKB):
        if MKB[-1:] == '.':
            MKB = MKB[:-1]
        if not MKB:
            return
        characterIdList = getAvailableCharacterIdByMKB(unicode(MKB))
        table = QtGui.qApp.db.table('rbDiseaseCharacter')
        self.cmbCharacter.setTable(table.name(), not bool(characterIdList), filter=table['id'].inlist(characterIdList))
        self.cmbCharacter.setCurrentIndex(0)


    def updateToxicSubstancesIdListByMKB(self, MKB):
        db = QtGui.qApp.db
        fixedMKB = MKBwithoutSubclassification(MKB)
        table = db.table('rbToxicSubstances')
        toxicSubstancesIdList = db.getDistinctIdList(table, [table['id']], [table['MKB'].eq(fixedMKB)], order=table['name'].name())
        self.cmbToxicSubstances.setTable(table.name(), addNone=True, filter=table['id'].inlist(toxicSubstancesIdList))
        self.cmbToxicSubstances.setValue(0)


    def getDiagnosticRecordAndTypeId(self):
        db = QtGui.qApp.db

        if self.chkDiagnosisType.isChecked():
            diagnosisTypeId = forceRef(db.translate('rbDiagnosisType', 'code', '7', 'id'))
        else:
            diagnosisTypeId = forceRef(db.translate('rbDiagnosisType', 'code', '1', 'id'))

        record = QtSql.QSqlRecord()

        diagnosisTypeIdField = QtSql.QSqlField('diagnosisType_id', QVariant.Int)
        diagnosisTypeIdField.setValue(QVariant(diagnosisTypeId))
        record.append(diagnosisTypeIdField)

        mkbField = QtSql.QSqlField('MKB', QVariant.String)
        mkbField.setValue(QVariant(self.cmbMKB.text()))
        mkbExField = QtSql.QSqlField('MKBEx', QVariant.String)
        mkbExField.setValue(QVariant(self.cmbMKBEx.text()))
        record.append(mkbField)
        record.append(mkbExField)

        morphologyMKBField = QtSql.QSqlField('morphologyMKB', QVariant.String)
        morphologyMKBField.setValue(QVariant(self.cmbMorphology.validText()))
        record.append(morphologyMKBField)

        personField = QtSql.QSqlField('person_id', QVariant.Int)
        personField.setValue(QVariant(self.cmbSetPerson.value()))
        record.append(personField)
        return record, diagnosisTypeId


    def saveDiagnostics(self, eventId=None):
        if not eventId:
            eventId = self.itemId()
        if not eventId:
            return
        db = QtGui.qApp.db
        table = db.table('Diagnostic')
        tableDiagnosisType = db.table('rbDiagnosisType')
        diagnosisTypeIdList = db.getDistinctIdList(tableDiagnosisType, '*', [tableDiagnosisType['code'].inlist([u'1', u'2', u'9', u'7'])])
        record = db.getRecordEx(table, '*', [table['deleted'].eq(0), table['event_id'].eq(eventId), table['diagnosisType_id'].inlist(diagnosisTypeIdList)], 'id')
        if not record:
            record = table.newRecord()

        begDate = self.edtBegDate.date()
        endDate = self.edtEndDate.date()
        date = endDate if endDate else begDate
        MKB = unicode(self.cmbMKB.text())
        MKBEx = unicode(self.cmbMKBEx.text())
        if QtGui.qApp.isTNMSVisible():
            valueTNMS, tnmsMap = self.cmbTNMS.getValue()
            TNMS = forceStringEx(valueTNMS)
            record.setValue('TNMS', toVariant(TNMS))
            for name, TNMSId in tnmsMap.items():
                if name in CEventEditDialog.TNMSFieldsDict.keys():
                    record.setValue(CEventEditDialog.TNMSFieldsDict[forceString(name)], TNMSId)
        else:
            TNMS=''
        traumaTypeId = self.cmbTraumaType.value()
        toxicSubstancesId = self.cmbToxicSubstances.value()
        morphologyMKB = None
        if self.enableMorphology(MKB):
            morphologyMKB = self.cmbMorphology.validText()
        diagnosisId = forceRef(record.value('diagnosis_id'))
        characterId = self.cmbCharacter.value()
        if self.chkDiagnosisType.isChecked():
            diagnosisTypeId = forceRef(db.translate('rbDiagnosisType', 'code', '7', 'id'))
        else:
            diagnosisTypeId = forceRef(db.translate('rbDiagnosisType', 'code', '1', 'id'))
        setPersonId = self.cmbSetPerson.value()
        specialityId = db.translate('Person', 'id', setPersonId, 'speciality_id')
        resultId = self.cmbDiagnosticResult.value()
        freeInput = self.edtFreeInput.text()

        diagnosisId, characterId = getDiagnosisId2(
                date,
                self.personId,
                self.clientId,
                diagnosisTypeId,
                MKB,
                MKBEx,
                characterId,
                forceRef(record.value('dispanser_id')),
                traumaTypeId,
                diagnosisId,
                forceRef(record.value('id')),
                TNMS=TNMS,
                morphologyMKB=morphologyMKB,
                dispanserBegDate=forceDate(record.value('endDate')))

        record.setValue('diagnosis_id', QVariant(diagnosisId))
        record.setValue('TNMS', QVariant(TNMS))
        record.setValue('character_id', QVariant(characterId))
        record.setValue('traumaType_id', QVariant(traumaTypeId))
        record.setValue('toxicSubstances_id', QVariant(toxicSubstancesId))
        record.setValue('diagnosisType_id', QVariant(diagnosisTypeId))
        record.setValue('event_id', QVariant(eventId))
        record.setValue('person_id', QVariant(setPersonId))
        record.setValue('speciality_id', QVariant(specialityId))
        record.setValue('result_id', QVariant(resultId))
        record.setValue('setDate', toVariant(begDate))
        record.setValue('endDate', toVariant(endDate))
        record.setValue('freeInput', toVariant(freeInput))
        db.insertOrUpdate(table, record)


    def on_actAPActionsAdd_triggered(self):
        pass


    def setTissueExternalId(self, existCountValue=None):
        externalIdValue = self.recountExternalId(existCountValue, _manualInputExternalId=self._manualInputExternalId)
        self.edtTissueExternalId.setText(unicode(externalIdValue))

        if existCountValue is None and not self._manualInputExternalId:
            self.edtTissueNumber.setText(unicode(externalIdValue))
        else:
            numberValue = self.recountExternalId(existCountValue=None, _manualInputExternalId=False)
            self.edtTissueNumber.setText(unicode(numberValue))


    def recountExternalId(self, existCountValue=None, _manualInputExternalId=False):
        if self.takenTissueRecord:
            return forceString(self.takenTissueRecord.value('externalId'))

        tissueType = self.cmbTissueType.value()
        date = self.edtTissueDate.date()
        if tissueType and date:
            if _manualInputExternalId:
                return '' if existCountValue is None else existCountValue
            if existCountValue is None:
                counterId = forceInt(QtGui.qApp.db.translate('rbTissueType', 'id', tissueType, 'counter_id'))
                if counterId:
                    QtGui.qApp.resetAllCounterValueIdReservation()
                    existCountValue = QtGui.qApp.getDocumentNumber(None, counterId, date)
                else:
                    cond = [self.tableTakenTissueJournal['tissueType_id'].eq(tissueType)]
                    dateCond = self.getRecountExternalIdDateCond(tissueType, date)
                    if dateCond:
                        cond.append(dateCond)
                    existCountValue = QtGui.qApp.db.getCount(self.tableTakenTissueJournal, where=cond)
                    existCountValue = unicode(existCountValue+1)
            return existCountValue.lstrip('0').zfill(6)
        return ''


    def getRecountExternalIdDateCond(self, tissueType, date):
        return getExternalIdDateCond(tissueType, date)


    def recountActualByTissueType(self):
        self.actualByTissueType.clear()
        actionList = []
        for record, action in self.tabActions.tblAPActions.model().items():
            actionList.append(record.value('actionType_id'))
        db = QtGui.qApp.db
        tableActionType = db.table('ActionType')
        cond = [tableActionType['id'].inlist(actionList),
                tableActionType['showInForm'].ne(0),
                tableActionType['deleted'].eq(0)]
        stmt = 'SELECT DISTINCT ActionType.`id` AS actionTypeId, ActionType_TissueType.`id`, ActionType_TissueType.`tissueType_id`, ActionType_TissueType.`amount`, ActionType_TissueType.`unit_id` FROM ActionType INNER JOIN ActionType_TissueType ON ActionType_TissueType.`master_id`=ActionType.`id` WHERE %s' % db.joinAnd(cond)
        query = db.query(stmt)
#        tissueTypeList = []
        while query.next():
            record = query.record()
            tissueType = forceRef(record.value('tissueType_id'))
            actionTypeId = forceRef(record.value('actionTypeId'))

            actualByTissueTypeList, actionTypeIdList = self.actualByTissueType.get(tissueType, (None, None))
            if actualByTissueTypeList:
                actualByTissueTypeList.append(record)
                actionTypeIdList.append(actionTypeId)
            else:
                self.actualByTissueType[tissueType] = ([record], [actionTypeId])
#        print self.actualByTissueType
        if not bool(self.takenTissueRecord):
            self.prepareTissueWidgets()


    def prepareTissueWidgets(self):
        tissueType = self.cmbTissueType.value()
        actualByTissueTypeList, actionTypeIdList = self.actualByTissueType.get(tissueType, ([], []))
        actionTypesList = []
        globalUnitId = None
        totalAmount = 0
        for actualRecord in actualByTissueTypeList:
            actionTypeId = forceRef(actualRecord.value('actionTypeId'))
            amount = forceInt(actualRecord.value('amount'))
            unitId = forceRef(actualRecord.value('unit_id'))
            if not unitId:
                continue
            if actionTypeId not in actionTypesList:
                actionTypesList.append(actionTypeId)
                if not globalUnitId:
                    globalUnitId = unitId
                else:
                    if unitId != globalUnitId:
                        continue
                totalAmount += amount
        self.edtTissueAmount.setValue(totalAmount)
        self.cmbTissueUnit.setValue(globalUnitId)
        self.cmbTissueUnit.setEnabled(not bool(globalUnitId))


    @pyqtSignature('bool')
    def on_chkConstraintActionTypes_toggled(self, value):
        self.updateTreeData()


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelActionsSummary_currentChanged(self, current, previous):
        self.modelActionsSummary.setCurrentRow(current.row())



    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelActionTypeGroups_currentChanged(self, current, previous=None):
        if current.isValid() and current.internalPointer():
            actionTypeId = current.internalPointer().id()
            _class = current.internalPointer().class_()
        else:
            actionTypeId = None
            _class = None
        self.setGroupId(actionTypeId, _class)
        text = trim(self.edtFindByCode.text())
        if text:
            self.on_edtFindByCode_textChanged(text)

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


    @pyqtSignature('')
    def on_btnSelectAll_clicked(self):
        for actionTypeId in self.modelActionTypes.idList():
            self.setSelected(actionTypeId, True)
        self.invalidateChecks()


    @pyqtSignature('')
    def on_btnClearSelection_clicked(self):
        self.selectedActionTypeIdList = []
        self.updateSelectedCount()
        self.invalidateChecks()


    @pyqtSignature('QDate')
    def on_edtBegDate_dateChanged(self, date):
        self.eventSetDateTime.setDate(date)
        self.setFilterResult(date)
#        contractId = self.cmbContract.value()
        self.cmbContract.setDate(self.getDateForContract())
        self.setPersonDate(date)
#        self.cmbContract.setValue(contractId)


    @pyqtSignature('QDate')
    def on_edtEndDate_dateChanged(self, date):
        self.eventDate = QDate(date)
        self.cmbContract.setDate(self.getDateForContract())
        self.setEnabledChkCloseEvent(self.eventDate)
        if getEventShowTime(self.eventTypeId):
                time = QTime.currentTime() if date else QTime()
                self.edtEndTime.setTime(time)


    @pyqtSignature('int')
    def on_cmbDiagnosticResult_currentIndexChanged(self, index):
        diagnosticResultId = self.cmbDiagnosticResult.value()
        eventResultId = forceRef(QtGui.qApp.db.translate('rbDiagnosticResult', 'id', diagnosticResultId, 'result_id'))
        self.cmbResult.setValue(eventResultId)


    @pyqtSignature('int')
    def on_cmbTissueType_currentIndexChanged(self, index):
        tissueType = self.cmbTissueType.value()
        self._manualInputExternalId = forceBool(QtGui.qApp.db.translate('rbTissueType', 'id',
                                                              tissueType, 'counterManualInput'))
        self.setTissueExternalId()
        self.updateTreeData()
        if not bool(self.takenTissueRecord):
            self.prepareTissueWidgets()
        self.modelActionTypes.setTissueTypeId(tissueType)


    @pyqtSignature('QDate')
    def on_edtTissueDate_dateChanged(self, date):
        if self._manualInputExternalId is None:
            tissueType = self.cmbTissueType.value()
            self._manualInputExternalId = forceBool(QtGui.qApp.db.translate('rbTissueType', 'id',
                                                                            tissueType, 'counterManualInput'))
        self.setTissueExternalId()


    @pyqtSignature('')
    def on_actScanBarcode_triggered(self):
        if not self.edtTissueExternalId.isReadOnly():
            self.edtTissueExternalId.setFocus(Qt.OtherFocusReason)
            self.edtTissueExternalId.selectAll()


    @pyqtSignature('')
    def on_cmbContract_valueChanged(self):
        contractId = self.cmbContract.value()
        self.setContractId(contractId)
        cols = self.tblActions.model().cols()
        if cols:
            cols[0].setContractId(contractId)


    @pyqtSignature('int')
    def on_cmbExecPerson_currentIndexChanged(self, index):
        self.setPersonId(self.cmbExecPerson.value())


#    @pyqtSignature('QString')
    def on_edtMKB_textChanged(self, value):
        value = unicode(value)
        if value[-1:] == '.':
            value = value[:-1]
        self.setIsDirty(True)
        diagName = u''
        if len(value) < 6:
            diagName = forceString(QtGui.qApp.db.translate('MKB', 'DiagID', value, 'DiagName'))
        else:
            MKBSubclassId =  forceRef(QtGui.qApp.db.translate('MKB', 'DiagID', value[:5], 'MKBSubclass_id '))
            if MKBSubclassId:
                cond = 'code = \'%s\' AND master_id=%d' % (value[5], MKBSubclassId)
                record = QtGui.qApp.db.getRecordEx('rbMKBSubclass_Item', 'name', cond)
                if record:
                    diagName = forceString(record.value('name'))
        if diagName:
            self.lblMKBText.setText(diagName)
            self.updateCharacterByMKB(value)
            self.updateToxicSubstancesIdListByMKB(value)
            if self.enableMorphology(value):
                morphologyFilter = self.morphologyFilterCache.get(value, None)
                if not morphologyFilter:
                    morphologyFilter = self.cmbMorphology.getMKBFilter(value)
                    self.morphologyFilterCache[value] = morphologyFilter
                self.cmbMorphology.setMKBFilter(morphologyFilter)
            else:
                self.cmbMorphology.setEnabled(False)
        else:
            self.cmbCharacter.setFilter(None)
            self.cmbCharacter.setCurrentIndex(0)
            self.cmbToxicSubstances.setFilter(None)
            self.cmbToxicSubstances.setCurrentIndex(0)
            self.lblMKBText.clear()
            self.cmbMorphology.setEnabled(False)
        if QtGui.qApp.isTNMSVisible():
            self.cmbTNMS.setMKB(forceStringEx(value))


    @pyqtSignature('')
    def on_btnAdd_clicked(self):
        n = len(self.selectedActionTypeIdList)
        self.totalAddedCount += n
        for id in self.selectedActionTypeIdList:
            self.tabActions.modelAPActions.addRow(id, None, None, self.cmbContract.value())
        self.selectedActionTypeIdList = []
        self.treeActionTypeGroups.reset()
        self.updateTreeData(True)
        self.updateSelectedCount()
        self.recountActualByTissueType()
        self.modelActionsSummary.regenerate()
        self.tabCash.modelAccActions.regenerate()
        
    
    def btnRelatedEventHighlight(self):       
        db = QtGui.qApp.db
        tableEvent = db.table('Event')
        tableEventType = db.table('EventType')
        tablePWS = db.table('vrbPersonWithSpeciality')
        tableCreatePWS = db.table('vrbPersonWithSpeciality').alias('CPWS')
        tableActionType = db.table('ActionType')
        tableAction = db.table('Action')
        cols = [tableEvent['id'].alias('eventId')]

        cond = [tableEvent['deleted'].eq(0),
                tableEventType['context'].like(u'relatedAction%'),
                tableAction['deleted'].eq(0),
                tableEvent['client_id'].eq(self.clientId)
                ]

        table = tableEvent.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
        table = table.innerJoin(tableAction, tableAction['event_id'].eq(tableEvent['id']))
        table = table.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
        table = table.leftJoin(tablePWS, tablePWS['id'].eq(tableAction['person_id']))
        table = table.leftJoin(tableCreatePWS, tableCreatePWS['id'].eq(tableAction['createPerson_id']))
        record = db.getRecordEx(table, cols, cond)

        if record:
            self.btnRelatedEvent.setStyleSheet("""
                QPushButton {
                    background-color: #F28a64;
                }
                QPushButton:hover {
                    background-color: #F6b096;
                }
            """)
        else:
            self.btnRelatedEvent.setGraphicsEffect(None)
            self.btnRelatedEvent.setStyleSheet("")



    @pyqtSignature('')
    def on_btnRelatedEvent_clicked(self):
        currentEventId = self.itemId()
        if not currentEventId:
            QtGui.QMessageBox.warning(self, u'Внимание!',
                                      u'Для доступа к связанным событиям необходимо сохранить текущее событие',
                                      QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ok)
        else:
            self.relDialog = CRelatedEventAndActionListDialog(self, currentEventId, self.prevEventId)
            self.relDialog.exec_()
            self.relDialog.deleteLater()


    @pyqtSignature('')
    def on_btnPlanning_clicked(self):
        actionListToNewEvent = []
        self.prepare(self.clientId, self.eventTypeId, self.orgId, self.personId, self.eventDate, self.eventDate, None, None, None, None, None, isEdit=True)
        self.initPrevEventTypeId(self.eventTypeId, self.clientId)
        self.initPrevEventId(None)
        self.addActions(actionListToNewEvent)

        
    @pyqtSignature('')
    def on_btnPrintLabel_clicked(self):
        printer = QtGui.qApp.labelPrinter()
        if self.labelTemplate and printer:
            context = CInfoContext()
            date = self.eventDate if self.eventDate else QDate.currentDate()
            takenTissueId = forceRef(self.takenTissueRecord.value('id')) if self.takenTissueRecord else None
            data = {'client'     : context.getInstance(CClientInfo, self.clientId, date),
                    'tissueType' : context.getInstance(CTissueTypeInfo, self.cmbTissueType.value()),
                    'externalId' : self.edtTissueExternalId.text(),
                    'takenTissue': context.getInstance(CTakenTissueJournalInfo, takenTissueId)
                   }
            QtGui.qApp.call(self, directPrintTemplate, (self.labelTemplate.id, data, printer))


# ###############################################


class CLocColorCol(CCol):
    def __init__(self, title, fields, defaultWidth, model):
        CCol.__init__(self, title, fields, defaultWidth, 'r')
        self._model = model
        self._cache = CRecordCache()

    def getBackgroundColor(self, values):
        tissueTypeId = self._model.tissueTypeId()
        if tissueTypeId:
            actionTypeId = forceRef(values[0])
            key = (actionTypeId, tissueTypeId)
            color = self._cache.get(key)
            if color is None:
                db = QtGui.qApp.db
                cond = 'master_id=%d AND tissueType_id=%d' %(actionTypeId, tissueTypeId)
                rec = db.getRecordEx('ActionType_TissueType', 'containerType_id', cond)
                colorName = None
                if rec:
                    containerTypeId = forceRef(rec.value('containerType_id'))
                    if containerTypeId:
                        colorName = forceString(db.translate('rbContainerType', 'id', containerTypeId, 'color'))
                if colorName:
                    color = QVariant(QtGui.QColor(colorName))
                else:
                    color = QVariant()
                self._cache.put(key, color)
            return color
        return CCol.invalid

    def format(self, values):
        return CCol.invalid


class CActionLeavesModel(CActionsModel):
    colorColumnIndex = 1
    def __init__(self, parent):
        self._tissueTypeId = None
        cols = [CEnableCol(u'Включить',     ['id'],   20, parent),
                CLocColorCol(u'Цветовая маркировка', ['id'], 10, self),
                CTextCol(u'Код',            ['code'], 20),
                CTextCol(u'Наименование',   ['name'], 20)]
        self.initModel(parent, cols)
        self._parent = parent
        self.__cols = cols


    def setTissueTypeId(self, tissueTypeId):
        self._tissueTypeId = tissueTypeId
        self.emitDataChanged()


    def tissueTypeId(self):
        return self._tissueTypeId


    def data(self, index, role=Qt.DisplayRole):
        return CTableModel.data(self, index, role)


    def setEventTypeId(self, eventTypeId):
        self._eventTypeId = eventTypeId


class CF001ActionsSummaryModel(CFxxxActionsSummaryModel):

    class CPropertyInDocTableCol(CInDocTableCol):
        pass

    def __init__(self, parent, editable=False):
        CFxxxActionsSummaryModel.__init__(self, parent, editable)
        self._propertyColsNames   = []
        self._propertyColsIndexes = []
        self._currentRow = None
        self._mapRow2property = {}
        self._eventTypeId = None
        self._eventEditor = parent


    def flags(self, index = QModelIndex()):
        if index.isValid():
            column = index.column()
            if getEventIncludeTooth(self.eventTypeId()) and column ==  self.getColIndex('tooth'):
                row = index.row()
                property = self._getProperty(column, row)
                if not property:
                    return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return CFxxxActionsSummaryModel.flags(self, index)



    def eventTypeId(self):
        return self._eventTypeId


    def setCurrentRow(self, row):
        if self._currentRow != row:
            self._currentRow = row


    def setEventTypeId(self, eventTypeId):
        self._eventTypeId = eventTypeId
        if getEventIncludeTooth(eventTypeId):
            amountColIndex = self.getColIndex('amount')
            self.addExtCol(CF001ActionsSummaryModel.CPropertyInDocTableCol(u'Зуб', 'tooth', 10),
                           QVariant.String, amountColIndex)
            self._propertyColsNames.append('tooth')
            self._propertyColsIndexes = [self.getColIndex(name) for name in self._propertyColsNames]
            self.reset()


    def regenerate(self, top=0, bottom=0):
        CFxxxActionsSummaryModel.regenerate(self)
        self._mapRow2property.clear()


    def _getProperty(self, column, row=None):
        if row is None:
            row = self._currentRow
        if row is not None:
            property = self._mapRow2property.get(row, None)
            if property is None and 0 <= row < len(self.itemIndex):
                iModel, iAction = self.itemIndex[row]
                actionsModel = self.models[iModel]
                record, action = actionsModel.items()[iAction]
                actionType = action.getType()
                toothEists = False
                for propertyType in actionType.getPropertiesById().values():
                    if isinstance(propertyType.valueType, CToothActionPropertyValueType) and not toothEists:
                        property = action.getPropertyById(propertyType.id)
                        self._mapRow2property[row] = property
            return property

        return None



    def createPropertyEditor(self, column, parent):
        property     = self._getProperty(column)
        if property:
            propertyType = property.type()
            editor       = propertyType.createEditor(None, parent, self._eventEditor.clientId, self.eventTypeId())
            return editor
        return None




    def createEditor(self, column, parent):
        if column in self._propertyColsIndexes:
            return self.createPropertyEditor(column, parent)
        else:
            return CFxxxActionsSummaryModel.createEditor(self, column, parent)


    def setEditorData(self, column, editor, value, record):
        if column in self._propertyColsIndexes:
            editor.setValue(value)
        else:
            return CFxxxActionsSummaryModel.setEditorData(self, column, editor, value, record)



    def getPropertyEditorData(self, column, editor):
        property     = self._getProperty(column)
        if property:
            propertyType = property.type()
            value        = editor.value()
            value        = propertyType.convertQVariantToPyValue(value) if type(value) == QVariant else value
            property.setValue(value)
            return value
        return None



    def getEditorData(self, column, editor):
        if column in self._propertyColsIndexes:
            return self.getPropertyEditorData(column, editor)
        else:
            return CFxxxActionsSummaryModel.getEditorData(self, column, editor)



    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            column = index.column()
            if column in self._propertyColsIndexes:
                row = index.row()
                property = self._getProperty(column, row)
                if property:
                    return toVariant(property.getText())
                QVariant(u'---')
        return CFxxxActionsSummaryModel.data(self, index, role)
