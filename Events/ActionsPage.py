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
import requests
# Страница редактирования action одного класса в пределах event'а

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QDate, QDateTime, QMimeData, QString, QTime, QVariant, pyqtSignature, SIGNAL
from Events.ExecutionPlan.Groups import CExecutionPlanProxyModelGroup
from Orgs.Utils import getOrgStructureDescendants, getParentOrgStructureId

from library.Calendar                import wpFiveDays, addWorkDays, getNextWorkDay, wpSixDays, wpSevenDays
from library.DialogBase              import CConstructHelperMixin, CDialogBase
from library.ICDUtils import MKBwithoutSubclassification, getMKBName
from library.interchange             import setDatetimeEditValue
from library.JsonRpc.client          import CJsonRpcClent
from library.PrintTemplates import applyTemplate, customizePrintButton, applyMultiTemplateList, getFirstPrintTemplate
from library.Utils import exceptionToUnicode, forceBool, forceDate, forceDateTime, forceDouble, forceInt, forceRef, \
    forceString, toVariant, forceStringEx, formatSNILS, pyDate, getExSubclassItemLastName

from Events.Action                   import CActionTypeCache, CAction, CActionType, selectNomenclatureExpense
from Events.ActionPropertiesTable    import CActionPropertiesTableModel
from Events.ActionRelations.AddRelatedAction import CAddRelatedAction
from Events.ActionsModel import CGroupActionsProxyModel, CActionRecordItem
from Events.ActionsSelector          import selectActionTypes
from Events.ActionStatus             import CActionStatus
from Events.ActionTemplateChoose   import CActionTemplateCache
from Events.ActionTemplateSaveDialog import CActionTemplateSaveDialog
from Events.ActionTemplateSelectDialog import CActionTemplateSelectDialog
from Events.ActionTypeDialog       import CActionTypeDialogTableModel
from Events.ExecTimeNextActionDialog import CExecTimeNextActionDialog
from Events.ExecutionPlanDialog      import CGetExecutionPlan
from Events.GetPrevActionIdHelper    import CGetPrevActionIdHelper
from Events.InputDialog              import CInputDialog
from Events.HospitalOrderSelectDialog import CHospitalOrderSelectDialog
from Events.PropertiesDialog         import CPropertiesDialog
from Events.PropertyEditorAmbCard import CPropertyEditorAmbCard
from Events.ActionGroupSignDialog import CActionGroupSignDialog
from Events.Utils                    import (CFinanceType,
                                             CInputCutFeedDialog,
                                             getIdListActionType,
                                             getEventCode,
                                             updateNomenclatureDosageValue,
                                             getDiagnosisId2,
                                             getChiefId,
                                             getActionTypeIdListByFlatCode,
                                             checkAttachOnDate,
                                             checkPolicyOnDate,
                                             cutFeed,
                                             getEventContextData,
                                             getEventShowTime,
                                             setActionPropertiesColumnVisible,
                                             getEventCSGRequired,
                                             getEventTypeForm,
                                             getEventMedicalAidKindId,)
from Events.LLO78Login               import CLLO78LoginDialog
from Events.PrintActionsListDialog    import CPrintActionsListDialog
from Events.Utils import CFinanceType, getDiagnosisId2, getChiefId, getActionTypeIdListByFlatCode, checkAttachOnDate, \
    checkPolicyOnDate, cutFeed, getEventContextData, getEventShowTime, setActionPropertiesColumnVisible, \
    getEventCSGRequired, getEventTypeForm, getEventAidTypeRegionalCode
from Orgs.Orgs                       import selectOrganisation
from Stock.ClientInvoiceEditDialog import CClientInvoiceEditDialog, CClientRefundInvoiceEditDialog
from Stock.Utils                     import getExistsNomenclatureAmount, getStockMotionItemQntEx, getNomenclatureUnitRatio, getNomenclatureSimpleUnitRatio
from Resources.CourseStatus          import CCourseStatus
from Resources.Utils                 import getNextDateExecutionPlan
from Users.Rights import urCopyPrevAction, urEditClosedEvent, urLoadActionTemplate, urSaveActionTemplate, \
    urEditOtherpeopleAction, urCanSaveEventWithMKBNotOMS, urEditOtherPeopleActionSpecialityOnly, urHBLeaved, urNoRestrictRetrospectiveNEClient, \
    urNomenclatureExpenseLaterDate, canChangeActionPerson, urCanAttachFile, urCanIgnoreAttachFile
from Exchange.UO.UOAppointmentsTableDialog import CUOAppointmentsTableDialog
from Exchange.UO.UOServiceClient import CUOServiceClient
from Events.LLO78RegistryWindow      import CLLO78RecipeRegistryDialog

from Events.Ui_ActionsPage import Ui_ActionsPageWidget


_RECIPE = 1
_DOSES  = 2
_SIGNA  = 3
_ACTIVESUBSTANCE = 4


class CActionsPage(QtGui.QWidget, CConstructHelperMixin, Ui_ActionsPageWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.eventEditor = None
        self.notAvialableNomenclatureDict = {}
        self.cacheExSubClassMKBNames = {}

        self.addModels('APActions',            CGroupActionsProxyModel(self))
        self.addModels('APActionProperties',   CActionPropertiesTableModel(self))
        self.addObject('actAPAddLikeAction',   QtGui.QAction(u'Добавить такой же', self))
        self.addObject('actAPAddRelatedAction',QtGui.QAction(u'Добавить подчиненные действия', self))
        self.addObject('actAPDuplicateAction', QtGui.QAction(u'Дублировать', self))
        self.addObject('actRefreshAction',     QtGui.QAction(u'Обновить действие', self))
        self.addObject('actAPReplicateAction', QtGui.QAction(u'Тиражировать', self))
        self.addObject('actAPActionsAdd',      QtGui.QAction(u'Добавить ...', self))
        self.addObject('actAPActionSplitEvent',      QtGui.QAction(u'В новое событие', self))
        self.addObject('actAPPrintAllActions', QtGui.QAction(u'Печать всех действий', self))
        self.addObject('actAPGroupSign', QtGui.QAction(u'Групповое подписание и прикрепление', self))
        self.addObject('actAPCopyProperties',  QtGui.QAction(u'Копировать свойства', self))
        self.addObject('actAPPasteProperties', QtGui.QAction(u'Вставить свойства', self))
        self.addObject('mnuAPLoadPrevAction', QtGui.QMenu(self))
        self.addObject('actAPLoadSameSpecialityPrevAction', QtGui.QAction(u'Той же самой специальности', self))
        self.addObject('actAPLoadOwnPrevAction',            QtGui.QAction(u'Только свои', self))
        self.addObject('actAPLoadAnyPrevAction',            QtGui.QAction(u'Любое', self))
        self.addObject('actCopyInputActionProperty',            QtGui.QAction(u'Наследование', self))
        self.addObject('actPropertyEditorAmbCard', QtGui.QAction(u'Заполнить данные из мед карты', self))
        self.mnuAPLoadPrevAction.addAction(self.actAPLoadSameSpecialityPrevAction)
        self.mnuAPLoadPrevAction.addAction(self.actAPLoadOwnPrevAction)
        self.mnuAPLoadPrevAction.addAction(self.actAPLoadAnyPrevAction)
        self.mnuAPLoadPrevAction.addAction(self.actCopyInputActionProperty)
        self.addObject('mnuAPQueueManagement', QtGui.QMenu(self))
        self.addObject('actAPQMSetAppointment', QtGui.QAction(u'Записать на прием', self))
        self.addObject('actAPQMCancelReferral', QtGui.QAction(u'Аннулировать направление', self))
        self.addObject('actAPQMCreateClaimForRefusal', QtGui.QAction(u'Отменить запись на прием', self))
        self.addObject('actImportAvailableProfiles', QtGui.QAction(u'Обновить профили', self))

        self.addObject('actCreatingApplication', QtGui.QAction(u'Создать направление', self))
        self.addObject('actViewingApplications', QtGui.QAction(u'Просмотреть список направлений', self))
        # self.addObject('actAPMoveToStage', QtGui.QAction(u'Отправить заявку в МО', self))
        # self.addObject('actAPEditProcess', QtGui.QAction(u'Редактировать заявку', self))
        # self.addObject('actAPMoveToStage_ForEnd', QtGui.QAction(u'Отменить заявку', self))
        # self.addObject('actAPMoveToStage_Dop_Export', QtGui.QAction(u'Отправить дополнительную информацию', self))
        #
        # self.addObject('actAPMoveToStage_Dop', QtGui.QAction(u'Запросить дополнительную информацию', self))
        # self.addObject('actAPMoveToStage_consilium', QtGui.QAction(u'Запросить и указать участников консилиума (в разработке)', self))
        # self.addObject('actAPMoveToStage_ForHappyEnd', QtGui.QAction(u'Сформировать и отправить консультативное заключение', self))

        self.mnuAPQueueManagement.addAction(self.actAPQMSetAppointment)
        self.mnuAPQueueManagement.addAction(self.actAPQMCancelReferral)
        self.mnuAPQueueManagement.addAction(self.actAPQMCreateClaimForRefusal)
        self.mnuAPQueueManagement.addAction(self.actImportAvailableProfiles)
        self.mnuAPQueueManagement.addAction(self.actCreatingApplication)
        self.mnuAPQueueManagement.addAction(self.actViewingApplications)
        # self.mnuAPQueueManagement.addAction(self.actAPEditProcess)
        # self.mnuAPQueueManagement.addAction(self.actAPMoveToStage_ForEnd)
        # self.mnuAPQueueManagement.addAction(self.actAPMoveToStage_Dop_Export)
        #
        # self.mnuAPQueueManagement.addAction(self.actAPMoveToStage_Dop)
        # self.mnuAPQueueManagement.addAction(self.actAPMoveToStage_consilium)
        # self.mnuAPQueueManagement.addAction(self.actAPMoveToStage_ForHappyEnd)

        self.actAPActionsAdd.setShortcut(Qt.Key_F9)
        self.addAction(self.actAPActionsAdd)
        self.setupUi(self)
        self.tblAPActions.setParentWidget(self)
        self.setFocusProxy(self.tblAPActions)
        self.isCmbAPMKBTextChanged = False
        self.edtAPDirectionDate.canBeEmpty(True)
        self.edtAPBegDate.canBeEmpty(True)
        self.edtAPEndDate.canBeEmpty(True)
        self.copyAction = None
        self.setupActionPopupMenu()
        self.setupActionPropertyPopupMenu()
        self.commonTakenTissueJournalRecordId = None
        self.allowedActionTypesByTissue = []
        self.defaultDirectionDate = CActionType.dddUndefined
        self.defaultEndDate = CActionType.dedUndefined
        self.actionTemplateCache = CActionTemplateCache(self.eventEditor, self.cmbAPPerson)
        self.setModels(self.tblAPActions, self.modelAPActions, self.selectionModelAPActions)
        self.setModels(self.tblAPProps, self.modelAPActionProperties, self.selectionModelAPActionProperties)
        self.btnAPLoadPrevAction.setMenu(self.mnuAPLoadPrevAction)
        self._visibleMorphologyMKB = QtGui.qApp.defaultMorphologyMKBIsVisible()
        self._canUseLaboratoryCalculator = False
        self._mapNomenclatureIdToUnitId = {}
        self.receivedFinanceId = None
        self.eventActionFinance = None
        self.btnAPHospitalOrderSelect.setVisible(False)
        self.btnAPQueueManagement.setEnabled(False)
        self.btnAPQueueManagement.setMenu(self.mnuAPQueueManagement)

        action = QtGui.QAction(self)
        self.addObject('actSetLaboratoryCalculatorInfo', action)
        action.setShortcut('F3')
        self.addAction(action)
        self.connect(self.actSetLaboratoryCalculatorInfo, SIGNAL('triggered()'), self.on_actSetLaboratoryCalculatorInfo)

        self._canUseLaboratoryCalculatorPropertyTypeList = None
        self._mainWindowState = QtGui.qApp.mainWindow.windowState()
        self.cmbAPOrgStructure.setOrgId(QtGui.qApp.currentOrgId())
        self._readOnly = False

        self.connect(self.modelAPActionProperties,
                     SIGNAL('actionNameChanged()'), self.updateCurrentActionName)
        self.connect(self.modelAPActionProperties,
                     SIGNAL('setEventEndDate(QDate)'), self.setEventEndDate)
        self.connect(self.modelAPActionProperties,
                     SIGNAL('setCurrentActionPlannedEndDate(QDate)'), self.setCurrentActionPlannedEndDate)
        self.connect(self.modelAPActionProperties,
                     SIGNAL('actionAmountChanged(double)'), self.on_actionAmountChanged)
        self.connect(self.tblAPActions,
                     SIGNAL('delRows()'), self.modelAPActions.emitItemsCountChanged)
        self.cmbAPMKB.connect(self.cmbAPMKB._lineEdit, SIGNAL('editingFinished()'), self.on_cmbAPMKB_editingFinished)

        if QtGui.qApp.isExSubclassMKBVisible():
            self.connect(self.cmbAPMKBExSubclass, SIGNAL('editingFinished()'), self.on_cmbAPMKBExSubclass_editingFinished)
        self.lblAPMKBText.mousePressEvent = self.on_lblAPMKBText_click
        self.lblAPMKBText.contextMenuEvent = self.lblAPMKBTextContextMenuEvent
        self.connect(self.btnCloseWidgets, SIGNAL('arrowTypeChanged(bool)'), self.on_arrowTypeChanged)
        self.setVisibleBtnCloseWidgets(True)


    def setReadOnly(self, value=True):
        self._readOnly = value


    def isReadOnly(self):
        return self._readOnly


    def lblAPMKBTextContextMenuEvent(self, event):
        self.menu = QtGui.QMenu(self)
        copyText = QtGui.QAction(u'Копировать в буфер обмена', self)
        self.menu.addAction(copyText)
        copyText.triggered.connect(self.copyToClipboard)
        self.menu.popup(QtGui.QCursor.pos())

    def copyToClipboard(self):
        text = forceString(self.lblAPMKBText.text())
        clipBoard = QtGui.qApp.clipboard()
        clipBoard.setText(text)


    @pyqtSignature('')
    def on_actPropertyEditorAmbCard_triggered(self):
        index = self.tblAPProps.currentIndex()
        model = self.tblAPProps.model()
        row = index.row()
        if 0 <= row < model.rowCount():
            actionProperty = model.getProperty(row)
            dialog = CPropertyEditorAmbCard(self, self.eventEditor.clientId, self.eventEditor.clientSex, self.eventEditor.clientAge, self.eventEditor.eventTypeId, actionProperty)
            try:
                if dialog.exec_():
                    actionProperty = dialog.actionProperty
            finally:
                dialog.deleteLater()


    def protectFromEdit(self, isProtected):
        editWidgets = [self.edtAPDirectionDate,
                       self.edtAPDirectionTime,
                       self.edtAPPlannedEndDate,
                       self.edtAPPlannedEndTime,
                       self.edtAPBegDate,
                       self.edtAPBegTime,
                       self.edtAPEndDate,
                       self.edtAPEndTime,
                       self.edtAPOffice,
                       self.edtAPAmount,
                       self.edtAPUet,
                       self.edtAPNote,
                       self.edtAPCoordDate,
                       self.edtAPCoordTime,
                       self.edtAPQuantity,
                       self.edtAPDuration,
                       self.edtAPPeriodicity,
                       self.edtAPAliquoticity,
                       self.cmbAPSetPerson,
                       self.cmbAPStatus,
                       self.cmbAPOrg,
                       self.cmbAPPerson,
                       self.cmbAPOrgStructure,
                       self.cmbAPAssistant,
                       self.cmbAPMKB,
                       self.cmbAPMorphologyMKB
                       ]
        for widget in editWidgets:
            widget.setReadOnly(isProtected)
        editWidgets = [self.chkAPIsUrgent,
                       self.btnAPLoadTemplate,
                       self.btnAPLoadPrevAction,
                       self.btnAPSaveAsTemplate,
                       self.btnPlanNextAction,
                       self.btnAPNomenclatureExpense,
                       self.btnAPSelectOrg,
                       self.actAPActionsAdd
                       ]
        for widget in editWidgets:
            widget.setEnabled(not isProtected)
        if self.btnNextAction.isEnabled():
            self.btnNextAction.setEnabled(not isProtected)
        self.setReadOnly(isProtected)


    def on_actionAmountChanged(self, value):
        self.edtAPAmount.setValue(value)


    def updateCurrentActionName(self):
        index = self.tblAPActions.currentIndex()
        # Правильно было бы сделать emit dataChanged,
        #self.modelAPActions.emit(SIGNAL('dataChanged(const QModelIndex &, const QModelIndex &)'), index, index)
        # но это приводит к перескоку фокуса в неведомые места
        self.tblAPActions.dataChanged(index, index)


    def setEventEndDate(self, date):
        self.eventEditor.edtEndDate.setDate(date)

    def setCurrentActionPlannedEndDate(self, date):
        self.edtAPPlannedEndDate.setDate(date)


    def destroy(self):
        self.tblAPActions.setModel(None)
        del self.modelAPActions


    def setActionTypeClass(self, actionTypeClass):
        self.modelAPActions.setActionTypeClass(actionTypeClass)


    def setEventEditor(self, eventEditor):
        self.eventEditor = eventEditor
        self.modelAPActions.eventEditor = eventEditor
        self.actionTemplateCache.eventEditor = eventEditor
#        if hasattr(self, 'cmbAPMKB'):
#            self.cmbAPMKB.setEventEditor(eventEditor)
        self.connect(eventEditor, SIGNAL('updateActionsAmount()'), self.modelAPActions.updateActionsAmount)
        self.cmbCSG.setEventEditor(eventEditor)
        if hasattr(self.eventEditor, 'tabMes'):
            self.eventEditor.tabMes.csgRowAboutToBeRemoved.connect(self.onCsgRowAboutToBeRemoved)
            self.eventEditor.tabMes.csgRowRemoved.connect(self.onCsgRowRemoved)
        if hasattr(self.eventEditor, 'tabAmbCard'):
           self.connect(self.eventEditor.tabAmbCard, SIGNAL('actionSelected(int)'), self.createCopyAction)


    def onCsgRowRemoved(self):
        self.cmbCSG.setItems()

    def onCsgRowAboutToBeRemoved(self, record):
        for action in self.cmbCSG.mapActionToCSG:
            if self.cmbCSG.mapActionToCSG[action] == record:
                del self.cmbCSG.mapActionToCSG[action]
                action.setValue('eventCSG_id', QVariant(None))
                break
        csgId = forceRef(record.value('id'))
        if csgId:
            for actionRecord in self.eventEditor.modelActionsSummary._items:
                actionCsgId = forceRef(actionRecord.value('eventCSG_id'))
                if actionCsgId == csgId:
                    actionRecord.setValue('eventCSG_id', QVariant(None))

    def updateCmbCSG(self):
        model = self.tblAPActions.model()
        items = model.items()
        row = self.tblAPActions.currentIndex().row()

        if 0<=row<len(items):# and (row == len(items) - 1):
            record, action = items[row]
            self.cmbCSG.setCurrentActionRecord(record)

    def setupActionPopupMenu(self):
        tbl = self.tblAPActions
        tbl.createPopupMenu([
                             self.actAPAddLikeAction,
                             self.actAPAddRelatedAction,
                             self.actAPDuplicateAction,
                             self.actAPReplicateAction,
                             '-',
                             self.actAPActionsAdd,
                             '-',
                             self.actAPActionSplitEvent,
                             '-',
                             self.actAPPrintAllActions,
                             self.actAPGroupSign,
                             self.actAPCopyProperties,
                             self.actAPPasteProperties,
                             self.actRefreshAction,
                             ])
        tbl.popupMenu().addSeparator()
        tbl.addMoveRow()
        tbl.popupMenu().addSeparator()
        tbl.addSortingRow()
        tbl.popupMenu().addSeparator()
        tbl.addOpenInEditor()
        tbl.popupMenu().addSeparator()
        tbl.addPopupDelRow()
        tbl.setDelRowsChecker(lambda rows: not any(map(self.modelAPActions.isLockedOrExposed, rows)) and all(map(self.modelAPActions.isCanDeletedByUser, rows)))
        tbl.setDelRowsIsExposed(lambda rowsExp: not any(map(self.modelAPActions.isExposed, rowsExp)) and all(map(self.modelAPActions.isCanDeletedByUser, rowsExp)))
        tbl.setActionsWithCheckers([(self.actAPActionSplitEvent, self.actAPActionSplitEventChecker)])
        tbl.setActionsWithCheckers([(self.actAPCopyProperties, self.copyPasteAboutToShowChecker)])
        tbl.setActionsWithCheckers([(self.actAPPasteProperties, self.pasteAboutToShowChecker)])
        self.connect(tbl.popupMenu(), SIGNAL('aboutToShow()'), self.popupMenuAboutToShow)
        tbl.addPopupRecordProperies()


    def setupActionPropertyPopupMenu(self):
        tbl = self.tblAPProps
        tbl.createPopupMenu([self.actPropertyEditorAmbCard])
        self.connect(tbl.popupMenu(), SIGNAL('aboutToShow()'), self.popupMenuPropertyAboutToShow)



    def setOrgId(self, orgId):
        self.cmbAPSetPerson.setOrgId(orgId)
        self.cmbAPPerson.setOrgId(orgId)
        self.cmbAPAssistant.setOrgId(orgId)
        self.cmbAPOrgStructure.setOrgId(QtGui.qApp.currentOrgId())


    def setBegDate(self, date):
        self.cmbAPSetPerson.setBegDate(date)
        self.cmbAPPerson.setBegDate(date)
        self.cmbAPAssistant.setBegDate(date)


    def setEndDate(self, date):
        self.cmbAPSetPerson.setEndDate(date)
        self.cmbAPPerson.setEndDate(date)
        self.cmbAPAssistant.setEndDate(date)

    def setCommonTakenTissueJournalRecordIdToActions(self):
        for record, action in self.modelAPActions.items():
            actionTypeId = forceRef(record.value('actionType_id'))
            if actionTypeId in self.allowedActionTypesByTissue:
                record.setValue('takenTissueJournal_id', toVariant(self.commonTakenTissueJournalRecordId))

    def updatePersonId(self, oldPersonId, newPersonId):
        self.modelAPActions.updatePersonId(oldPersonId, newPersonId)


    # def loadActions(self, eventId):
    #     self.modelAPActions.loadItems(eventId)
    #     # self.updateActionEditor()

    def loadActions(self, items):
        self.modelAPActions.loadItems(items)
        # self.updateActionEditor()

    def setCommonTakenTissueJournalRecordId(self, id=None, actionTypeIdList=[]):
        self.commonTakenTissueJournalRecordId = id
        self.allowedActionTypesByTissue = actionTypeIdList

    def saveActions(self, eventId):
        if self.commonTakenTissueJournalRecordId:
            self.setCommonTakenTissueJournalRecordIdToActions()
        self.cmbCSG.saveCSG()
        self.modelAPActions.saveItems(eventId)


    def updateActionEditor(self):
        model = self.tblAPActions.model()
        self.cmbCSG.setItems()
        if model.rowCount() > 0:
            self.tblAPActions.setCurrentIndex(model.index(0, 0))
        else:
            for widget in (self.edtAPDirectionDate, self.edtAPDirectionTime,
                           self.edtAPPlannedEndDate, self.edtAPPlannedEndTime,
                           self.cmbAPSetPerson,
                           self.cmbAPStatus, self.edtAPBegDate, self.edtAPBegTime,
                           self.edtAPEndDate, self.edtAPEndTime,
                           self.cmbAPPerson, self.edtAPOffice,
                           self.cmbAPOrgStructure,
                           self.cmbAPAssistant,
                           self.edtAPAmount, # self.edtAPUet,
                           self.edtAPNote,
                           self.tblAPProps,
                           self.btnAPPrint,
                           self.btnAPLoadTemplate, self.btnAPSaveAsTemplate, self.btnAPLoadPrevAction,
                           self.btnAPAttachedFiles,
                           self.lblCSG,  self.cmbCSG):
                widget.setEnabled(False)


    def updatePrintButton(self, actionType):
        context = actionType.context if actionType else ''
        customizePrintButton(self.btnAPPrint, context, shortcut='Shift+F6')


    def setCSGEditEnable(self, actionTypeId, canEdit):
        required = getEventCSGRequired(actionTypeId) if canEdit else False
        self.lblCSG.setEnabled(required)
        self.cmbCSG.setEnabled(required)


    def isEnabledNomenclatureExpense(self, action):
        if not action:
            return False
        if action.actionType().isDoesNotInvolveExecutionCourse and self.cmbAPStatus.value() == CActionStatus.finished:
            return False
        record = action.getRecord() if action else None
        begDate = forceDate(record.value('begDate')) if record else None
        currentDate = QDate().currentDate()
        minimumDate = None
        isEnabled = bool(begDate)
        if not QtGui.qApp.userHasRight(urNoRestrictRetrospectiveNEClient):
            if QtGui.qApp.admissibilityNomenclatureExpensePostDates() == 1:
                minimumDate = currentDate.addDays(-1)
            elif QtGui.qApp.admissibilityNomenclatureExpensePostDates() == 2:
                minimumDate = QDate(currentDate.year(), currentDate.month(), 1)
        if minimumDate:
            if QtGui.qApp.userHasRight(urNomenclatureExpenseLaterDate):
                isEnabled = begDate >= minimumDate
            else:
                isEnabled = begDate >= minimumDate and begDate <= currentDate
        else:
            if not QtGui.qApp.userHasRight(urNomenclatureExpenseLaterDate):
                isEnabled = begDate <= currentDate
        return isEnabled


    def getNomenclatureExpenseEnabled(self, action, actionType = None):
        nomenclatureExpenseEnabled = False
        if action:
            if not actionType:
                actionType = action.getType()
            if actionType and actionType.isNomenclatureExpense:
                nomenclatureId = action.findNomenclaturePropertyValue()
                dosage = action.findDosagePropertyValue()
                if nomenclatureId and dosage:
                    nomenclatureExpenseEnabled = True
        return nomenclatureExpenseEnabled


    def onActionCurrentChanged(self, previous=None):
        model = self.tblAPActions.model()
        items = model.items()
        row = self.tblAPActions.currentIndex().row()
        editWidgets = [self.edtAPDirectionDate, self.edtAPDirectionTime,
                       self.edtAPPlannedEndDate, self.edtAPPlannedEndTime,
                       self.cmbAPSetPerson,
                       self.edtAPBegDate, self.edtAPBegTime,
                       self.cmbAPOrg,
                       self.btnAPSelectOrg,
                       self.edtAPOffice,
                       self.cmbAPOrgStructure,
                       self.cmbAPAssistant,
                       self.edtAPAmount, # self.edtAPUet,
                       self.btnAPLoadTemplate, self.btnAPLoadPrevAction,
                       self.btnAPAttachedFiles,
                       self.cmbCSG, self.lblCSG]
        protWidgets = [self.cmbAPStatus,
                       self.cmbAPPerson,
                       self.edtAPEndDate, self.edtAPEndTime,
                       self.edtAPNote]
        otherWidgets = [self.tblAPProps, self.btnAPPrint, self.btnAPSaveAsTemplate]
        mkbWidgets   = [self.cmbAPMKB, self.cmbAPMorphologyMKB]
        if 0<=row<len(items):
            record, action = items[row]
        else:
            record = action = None
        if record:
            actionTypeId = forceRef(record.value('actionType_id'))
            actionType = CActionTypeCache.getById(actionTypeId) if actionTypeId else None
            personId = forceRef(record.value('person_id'))
            orgStructureId = forceRef(record.value('orgStructure_id'))
            financeId = forceRef(record.value('finance_id'))
            contractId = forceRef(record.value('contract_id'))
            self.specIdList = []
            for item in actionType.getPFSpecialityRecordList():
                self.specIdList.append(forceRef(item.value('speciality_id')))
            self.orgStructIdList = []
            for item in actionType.getPFOrgStructureRecordList():
                orgStruct = forceInt(item.value('orgStructure_id'))
                self.orgStructIdList.append(orgStruct)
                for orgStructDescendant in getOrgStructureDescendants(orgStruct):
                    self.orgStructIdList.append(orgStructDescendant)
            self.orgStructIdList = list(set(self.orgStructIdList))
        else:
            actionType = actionTypeId = None
            self.defaultDirectionDate = CActionType.dddUndefined
            self.defaultEndDate = CActionType.dedUndefined
            orgStructureId = None
        if actionType:
            self.btnAPHospitalOrderSelect.setVisible(QtGui.qApp.defaultKLADR()[:2] == u'23' and actionType.flatCode == 'hospitalDirection')
            self.cmbCSG.setCurrentActionRecord(record)
            if previous:
                self.tblAPProps.savePreferencesLoc(model.actionTypeId(previous.row()))
            setActionPropertiesColumnVisible(actionType, self.tblAPProps)
            self.tblAPProps.resizeColumnsToContents()
            self.tblAPProps.resizeRowsToContents()
            self.tblAPProps.loadPreferencesLoc(self.tblAPProps.preferencesLocal, actionType.id)
            self.defaultDirectionDate = actionType.defaultDirectionDate
            self.defaultEndDate = actionType.defaultEndDate
            visibleMKB = True
            if actionType.defaultMKB == CActionType.dmkbNotUsed:
                enableMKB  = False
                visibleMKB = False
            elif actionType.defaultMKB in (CActionType.dmkbSyncFinalDiag,
                                           CActionType.dmkbSyncSetPersonDiag,
                                           CActionType.dmkbSyncPreDiag):
                enableMKB = not forceString(record.value('MKB'))
            else:
                enableMKB = True
            dentitionCanEdit = True
            if ((u'dentitionInspection'.lower() in actionType.flatCode.lower()) or (u'parodentInsp'.lower() in actionType.flatCode.lower())):
                dentitionCanEdit = False
            if action:
                canEditIsLocked  = not action.isLocked()
                canEditIsExposed = not action.isExposed()
                canEditIsExecutionPlan = not bool(action.getExecutionPlan() and action.executionPlanManager.hasItemsToDo())
            else:
                canEditIsLocked = True
                canEditIsExposed = True
                canEditIsExecutionPlan = True
            enableEdit = True
            enableClosed = True
            if self.eventEditor:
                isClosed = self.eventEditor.tabNotes.isEventClosed()
                enableClosed = not isClosed or QtGui.qApp.userHasRight(urEditClosedEvent)
            canEdit = canEditIsLocked and canEditIsExposed and dentitionCanEdit and enableEdit
            if enableClosed:
                editWidgets.append(self.chkAPIsUrgent)
            for widget in editWidgets:
                if widget is self.btnAPAttachedFiles:
                    widget.setEnabled(canEdit or QtGui.qApp.userHasRight(urCanAttachFile))
                else:
                    widget.setEnabled(canEdit)
            actionType = CActionTypeCache.getById(actionTypeId) if actionTypeId else None 
            self.cmbAPStatus.setEnabled(actionType.editStatus)
            self.cmbAPPerson.setEnabled(actionType.editExecPers)
            self.edtAPBegDate.setEnabled(actionType.editBegDate)
            self.edtAPBegTime.setEnabled(actionType.editBegDate)
            self.edtAPEndDate.setEnabled(actionType.editEndDate) 
            self.edtAPEndTime.setEnabled(actionType.editEndDate)
            self.edtAPNote.setEnabled(actionType.editNote)
            self.cmbAPSetPerson.setEnabled(actionType.editSetPerson)
            self.cmbAPOrg.setEnabled(actionType.editOrg)
            self.btnAPSelectOrg.setEnabled(actionType.editOrg)

            self.setCSGEditEnable(self.eventEditor.eventTypeId, canEdit)
            self.lblAPMKB.setVisible(visibleMKB)
            self.cmbAPMKB.setVisible(visibleMKB)
            self.cmbAPMKB.setEnabled(canEdit and enableMKB)

            self.lblAPMorphologyMKB.setVisible(self._visibleMorphologyMKB and visibleMKB)
            self.cmbAPMorphologyMKB.setVisible(self._visibleMorphologyMKB and visibleMKB)
            self.cmbAPMorphologyMKB.setEnabled(canEdit and enableMKB)

            for widget in otherWidgets:
                widget.setEnabled(canEditIsExposed and dentitionCanEdit and enableEdit)
            self.btnAPNomenclatureExpense.setEnabled(canEdit and self.getNomenclatureExpenseEnabled(action, actionType))
            
            orgStructureList = actionType.getPFOrgStructureRecordList()
            specialityList = actionType.getPFSpecialityRecordList()
            tablePerson = QtGui.qApp.db.table('vrbPersonWithSpecialityAndPost')
            orgStructureIdList = []
            for orgStructureRecord in orgStructureList:
                orgStruct = forceInt(orgStructureRecord.value('orgStructure_id'))
                orgStructureIdList.append(orgStruct)
                for orgStructDescendant in getOrgStructureDescendants(orgStruct):
                    orgStructureIdList.append(orgStructDescendant)
                org = orgStruct
                while org:
                    org = getParentOrgStructureId(org)
                    if org:
                        orgStructureIdList.append(org)
            orgStructureIdList = list(set(orgStructureIdList))
            specialityIdList      = [forceInt(specialityRecord.value('speciality_id'))     for specialityRecord in specialityList]
            pFilter= []
            if orgStructureIdList:
                pFilter.append(tablePerson['orgStructure_id'].inlist(orgStructureIdList))
            if specialityIdList:
                pFilter.append(tablePerson['speciality_id'].inlist(specialityIdList))
            self.cmbAPPerson.blockSignals(True)
            self.cmbAPPerson.setFilter(QtGui.qApp.db.joinAnd(pFilter) if pFilter else None)
            self.cmbAPPerson.blockSignals(False)
            self.cmbAPPerson.filterInSearch(orgStructureIdList, specialityIdList)

            try:
                relegateOrgId = self.eventEditor.tabVoucher.cmbDirectionOrgs.value() if getEventTypeForm(self.eventEditor.eventTypeId) == u'072' else (self.eventEditor.tabNotes.cmbRelegateOrg.value() if hasattr(self.eventEditor.tabNotes, 'cmbRelegateOrg') else None)
                for widget in editWidgets+mkbWidgets+protWidgets:
                    widget.blockSignals(True)
#                self.cmbAPMKB.blockSignals(True)
#                if ((u'moving' in actionType.flatCode.lower()) or (u'received' in actionType.flatCode.lower())) and (row == len(items) - 1):
                if ((u'moving' in actionType.flatCode.lower()) or (u'received' in actionType.flatCode.lower())):
                    self.onCurrentActionAdd(actionType.flatCode, action)
                elif relegateOrgId and (relegateOrgId != QtGui.qApp.currentOrgId()
                    and ('recoveryDirection'.lower() in actionType.flatCode.lower()
                    or u'inspectionDirection'.lower() in actionType.flatCode.lower()
                    or u'researchDirection'.lower() in actionType.flatCode.lower()
                    or u'consultationDirection'.lower() in actionType.flatCode.lower()
                    or (u'planning'.lower() in actionType.flatCode.lower() and getEventCode(self.eventEditor.eventTypeId) == u'УО'))
                   ):
                    pass
                else:
                    if (action and
                            ((action.getExecutionPlan() and
                            action.executionPlanManager.hasItemsToDo()) or actionType.isDoesNotInvolveExecutionCourse) and
                            self.cmbAPStatus.value() != CActionStatus.canceled):
                        if actionType.isDoesNotInvolveExecutionCourse and self.cmbAPStatus.value() == CActionStatus.finished:
                            self.btnNextAction.setText(u'Действие')
                            self.btnNextAction.setEnabled(False)
                        else:
                            self.btnNextAction.setText(u'Выполнить')
                            isEnable = dentitionCanEdit and self.cmbAPStatus.value() != CActionStatus.refused and enableEdit
                            if action.getType().isNomenclatureExpense:
                                isEnable = isEnable and self.isEnabledNomenclatureExpense(action)
                            self.btnNextAction.setEnabled(isEnable)
                    else:
                        self.btnNextAction.setText(u'Действие')
                        self.btnNextAction.setEnabled(dentitionCanEdit and self.isTrailerActionType(actionTypeId) and enableEdit)
                    if self.edtAPDuration.value() > 0:
                        self.btnPlanNextAction.setEnabled(canEditIsExposed and dentitionCanEdit and True and enableEdit)
                    else:
                        self.btnPlanNextAction.setEnabled(canEditIsExposed and dentitionCanEdit and False and enableEdit)
                        
              #  if QtGui.qApp.defaultKLADR()[:2] == u'23' and actionType.context == 'recipe':
              #      self.btnAPPrint.setText(u'Сохранить и распечатать')
              #  else:
              #      self.btnAPPrint.setText(u'Печать')
                self.btnAPPrint.setText(u'Печать')
                            
                if action and u'Серия и номер бланка' in actionType._propertiesByName:
                    actionPropertyType = actionType._propertiesByName[u'Серия и номер бланка']
                    if actionPropertyType.valueDomain.lower() in [u'a', u'а']: #wtf
                        action[u'Серия и номер бланка'] = self.getBlankSerialNumberParams(actionType.id)
                
                if u'consultationDirection'.lower() in actionType.flatCode.lower() or u'researchDirection'.lower() in actionType.flatCode.lower():
                    self.btnAPQueueManagement.setText(u'УО')
                    enableQM = bool(action
                        and u'Идентификатор направления' in actionType._propertiesByName
                        and u'Причина аннулирования' in actionType._propertiesByName
                        and u'Идентификатор талона' in actionType._propertiesByName)
                    self.btnAPQueueManagement.setEnabled(enableQM and (action[u'Причина аннулирования'] is None or len(action[u'Причина аннулирования']) == 0))
                    self.actAPQMSetAppointment.setEnabled(enableQM and (action[u'Идентификатор талона'] is None or action[u'Идентификатор талона'] == u'Направление для самостоятельной записи через ЕПГУ'))
                    self.actAPQMCancelReferral.setEnabled(enableQM and action[u'Идентификатор направления'] is not None)
                    self.actAPQMCreateClaimForRefusal.setEnabled(enableQM and action[u'Идентификатор талона'] is not None)
                    self.actImportAvailableProfiles.setEnabled(True)
                    self.actAPQMCancelReferral.setVisible(True)
                    self.actAPQMCreateClaimForRefusal.setVisible(True)
                    self.actAPQMSetAppointment.setVisible(True)
                    self.actCreatingApplication.setVisible(False)
                    self.actImportAvailableProfiles.setVisible(True)
                    self.actViewingApplications.setVisible(False)
                elif u'tmkDirection'.lower() in actionType.flatCode.lower():
                    self.ActionTMK_BTN_Visible(action, actionType)
                else:
                    self.btnAPQueueManagement.setEnabled(False)


                self.on_edtAPDuration_valueChanged(forceInt(record.value('duration')))
                showTime = actionType.showTime if actionType else False
                self.edtAPDirectionTime.setVisible(showTime)
                self.edtAPPlannedEndTime.setVisible(showTime)
                self.edtAPCoordTime.setVisible(showTime)
                self.edtAPBegTime.setVisible(showTime)
                self.edtAPEndTime.setVisible(showTime)
                showAssistant = actionType.hasAssistant if actionType else False
                self.lblAPAssistant.setVisible(showAssistant)
                self.cmbAPAssistant.setVisible(showAssistant)
                requiredActionSpecification = actionType.requiredActionSpecification if actionType else False
                self.lblActionSpecification.setVisible(requiredActionSpecification)
                self.cmbActionSpecification.setVisible(requiredActionSpecification)
                self.cmbActionSpecification.setEnabled(requiredActionSpecification)
                actionSpecificationIdList = actionType.getActionSpecificationIdList()
                if requiredActionSpecification and actionSpecificationIdList:
                    actionSpecificationId = forceRef(record.value('actionSpecification_id'))
                    setFilter = u'id IN (%s)' % (u', '.join(str(actionSpecificationId) for actionSpecificationId in actionSpecificationIdList if actionSpecificationId is not None))
                    self.cmbActionSpecification.setTable('rbActionSpecification', True, filter=setFilter)
                    self.cmbActionSpecification.setValue(actionSpecificationId)
                setDatetimeEditValue(self.edtAPDirectionDate,    self.edtAPDirectionTime,    record, 'directionDate')
                setDatetimeEditValue(self.edtAPPlannedEndDate,   self.edtAPPlannedEndTime,   record, 'plannedEndDate')
                self.chkAPIsUrgent.setChecked(forceBool(record.value('isUrgent')))
                setDatetimeEditValue(self.edtAPCoordDate, self.edtAPCoordTime, record, 'coordDate')
                self.lblAPCoordText.setText(forceString(record.value('coordText')))
                setDatetimeEditValue(self.edtAPBegDate, self.edtAPBegTime, record, 'begDate')
                setDatetimeEditValue(self.edtAPEndDate, self.edtAPEndTime, record, 'endDate')
                self.APEndDate = forceDate(record.value('endDate'))
                self.APPerson = personId
                self.edtAPDirectionTime.setEnabled(canEdit and bool(self.edtAPDirectionDate.date()))
                canEditPlannedEndDate = canEdit and bool(actionType.defaultPlannedEndDate not in (CActionType.dpedBegDatePlusAmount,
                                                                                             CActionType.dpedBegDatePlusDuration))
                self.edtAPPlannedEndDate.setEnabled(canEditIsExposed and canEditPlannedEndDate and enableEdit and canEditIsExecutionPlan)
                self.edtAPPlannedEndTime.setEnabled(canEditIsExposed and canEditPlannedEndDate and bool(self.edtAPPlannedEndDate.date()) and enableEdit and canEditIsExecutionPlan)
                self.cmbAPSetPerson.setValue(QtGui.qApp.userId if actionType.defaultSetPersonInEvent == CActionType.dspUndefined and not forceRef(record.value('setPerson_id')) else forceRef(record.value('setPerson_id')))
                self.edtAPBegTime.setEnabled(canEdit and bool(self.edtAPBegDate.date()) and actionType.editBegDate)
                self.edtAPEndTime.setEnabled(canEdit and bool(self.edtAPEndDate.date()) and actionType.editEndDate)
                self.cmbAPStatus.setValue(forceInt(record.value('status')))
                if self.specIdList or self.orgStructIdList:
                    db = QtGui.qApp.db
                    table = db.table('vrbPersonWithSpecialityAndPost')
                    cond = []
                    if self.specIdList:
                        cond.append(table['speciality_id'].inlist(self.specIdList))
                    if self.orgStructIdList:
                        cond.append(table['orgStructure_id'].inlist(self.orgStructIdList))
                    if isinstance(cond, (list, tuple)):
                        cond = db.joinAnd(cond)
                    self.cmbAPPerson.setFilter(cond)
                self.cmbAPPerson.setValue(personId)
                self.edtAPOffice.setText(forceString(record.value('office')))
                if forceRef(record.value('actionSpecification_id')):
                    self.cmbActionSpecification.setValue(forceRef(record.value('actionSpecification_id')))
                self.cmbAPAssistant.setValue(forceRef(record.value('assistant_id')))
                self.edtAPQuantity.setValue(forceInt(record.value('quantity')))
                self.edtAPDuration.setValue(forceInt(record.value('duration')))
                self.edtAPPeriodicity.setValue(forceInt(record.value('periodicity')))
                self.edtAPAliquoticity.setValue(forceInt(record.value('aliquoticity')))
                amount = forceDouble(record.value('amount'))
                self.edtAPAmount.setValue(amount)
                self.edtAPAmount.setEnabled(canEdit and bool(actionType) and actionType.amountEvaluation == 0)
                uet = forceDouble(record.value('uet'))
                if amount and uet == 0:
                    uet = amount*self.eventEditor.getUet(actionTypeId, personId, financeId, contractId)
                self.edtAPUet.setValue(uet)
#                self.edtAPUet.setEnabled(canEditIsExposed and False)
                self.edtAPNote.setText(forceString(record.value('note')))
                MKB = forceString(record.value('MKB'))
                exSubclassMKB = forceString(record.value('exSubclassMKB'))
                self.cmbAPMKB.setText(MKB)
                self.cmbAPMorphologyMKB.setText(forceString(record.value('morphologyMKB')))
                self.cmbAPOrg.setValue(forceRef(record.value('org_id')))
                
                self.cmbAPOrgStructure.setValue(orgStructureId)
                if QtGui.qApp.isExSubclassMKBVisible():
                    self.cmbAPMKBExSubclass.setMKB(MKB)
                    self.cmbAPMKBExSubclass.setValue(exSubclassMKB)
                self.on_cmbAPMKB_textChanged(MKB)
                self.tblAPProps.setEnabled(canEditIsExposed and bool(action) and dentitionCanEdit and enableEdit)
                #self.tblAPProps.setEnabled(True)
                self.updatePropTable(action)
                self.updatePrintButton(actionType)
                self.btnAPAttachedFiles.setAttachedFileItemList(action.getAttachedFileItemList())

                if QtGui.qApp.userHasRight(urLoadActionTemplate) and action and (self.cmbAPStatus.value() != CActionStatus.finished
                                                                                 or not self.cmbAPPerson.value()
                                                                                 or QtGui.qApp.userId == self.cmbAPPerson.value()
                                                                                 or (QtGui.qApp.userHasRight(urEditOtherPeopleActionSpecialityOnly) and QtGui.qApp.userSpecialityId == self.getSpecialityId(personId))
                                                                                 or QtGui.qApp.userHasRight(urEditOtherpeopleAction)):
                    # actionTemplateTreeModel = self.actionTemplateCache.getModel(action.getType().id)
                    # self.btnAPLoadTemplate.setModel(actionTemplateTreeModel)
                    pass
                else:
                    self.btnAPLoadTemplate.setEnabled(False)
                self.btnAPSaveAsTemplate.setEnabled(canEditIsExposed
                                                    and dentitionCanEdit
                                                    and QtGui.qApp.userHasRight(urSaveActionTemplate)
                                                    and enableEdit)
                self.btnAPLoadPrevAction.setEnabled(canEdit
                                                    and QtGui.qApp.userHasRight(urCopyPrevAction)
                                                    and bool(action))
                executionPlan = action.getExecutionPlan()
                self.edtAPQuantity.setEnabled(canEditIsExposed
                                                    and dentitionCanEdit
                                                    and QtGui.qApp.userHasRight(urCopyPrevAction)
                                                    and QtGui.qApp.userId == self.cmbAPSetPerson.value()
                                                    and bool(executionPlan)
                                                    and not executionPlan #executionPlan.type == CActionExecutionPlanType.type
                                                    and self.cmbAPStatus.value() in (CActionStatus.appointed, )
                                                    and self.edtAPEndDate.date().isNull()
                                                    and enableEdit)
                self.edtAPDuration.setEnabled(canEditIsExposed
                                                    and dentitionCanEdit
                                                    and QtGui.qApp.userHasRight(urCopyPrevAction)
                                                    and QtGui.qApp.userId == self.cmbAPSetPerson.value()
                                                    and not executionPlan
                                                    and self.cmbAPStatus.value() in (CActionStatus.started, CActionStatus.finished)
                                                    and self.edtAPEndDate.date().isNull()
                                                    and enableEdit)
                self.edtAPPeriodicity.setEnabled(canEditIsExposed
                                                    and dentitionCanEdit
                                                    and QtGui.qApp.userHasRight(urCopyPrevAction)
                                                    and QtGui.qApp.userId == self.cmbAPSetPerson.value()
                                                    and not executionPlan
                                                    and self.cmbAPStatus.value() in (CActionStatus.started, CActionStatus.appointed)
                                                    and self.edtAPEndDate.date().isNull()
                                                    and enableEdit)
                self.edtAPAliquoticity.setEnabled(canEditIsExposed
                                                    and dentitionCanEdit
                                                    and QtGui.qApp.userHasRight(urCopyPrevAction)
                                                    and QtGui.qApp.userId == self.cmbAPSetPerson.value()
                                                    and not executionPlan
                                                    and self.cmbAPStatus.value() in (CActionStatus.started, CActionStatus.appointed)
                                                    and self.edtAPEndDate.date().isNull()
                                                    and enableEdit)
                self._canUseLaboratoryCalculator = False
                QtGui.qApp.disconnectClipboard()
            finally:
                for widget in editWidgets+mkbWidgets+protWidgets:
                    widget.blockSignals(False)
                self.edtAPPlannedEndDate.setEnabled(canEditIsExposed and dentitionCanEdit and self.edtAPPlannedEndDate.isEnabled() and enableEdit and canEditIsExecutionPlan)
                self.edtAPDirectionDate.setEnabled(canEditIsExposed and dentitionCanEdit and self.edtAPDirectionDate.isEnabled() and enableEdit)
                self.edtAPBegDate.setEnabled(canEditIsExposed and dentitionCanEdit and self.edtAPBegDate.isEnabled() and enableEdit and actionType.editBegDate)
                self.edtAPEndDate.setEnabled(canEditIsExposed and dentitionCanEdit and self.edtAPEndDate.isEnabled() and enableEdit and actionType.editEndDate)
                self.cmbAPSetPerson.setEnabled(canEditIsExposed and dentitionCanEdit and self.cmbAPSetPerson.isEnabled() and enableEdit and actionType.editSetPerson)
                self.btnAPSelectOrg.setEnabled(canEditIsExposed and dentitionCanEdit and self.btnAPSelectOrg.isEnabled() and enableEdit)
                if 'recipeLLO78'.lower() in actionType.flatCode.lower():
                    self.btnNextAction.setText(u'Зарегистрировать рецепт')
                    self.btnNextAction.setEnabled(True)
#                self.cmbAPMKB.blockSignals(False)
        else:
            self.cmbAPPerson.blockSignals(True)
            self.cmbAPPerson.setFilter(None)
            self.cmbAPPerson.blockSignals(False)
            self.defaultDirectionDate = CActionType.dddUndefined
            self.defaultEndDate = CActionType.dedUndefined
            for widget in editWidgets+mkbWidgets+protWidgets:
                widget.setEnabled(False)
#            self.cmbAPMKB.setEnabled(False)
            for widget in otherWidgets:
                widget.setEnabled(False)
            self.edtAPDirectionTime.setVisible(False)
            self.edtAPPlannedEndTime.setVisible(False)
            self.edtAPBegTime.setVisible(False)
            self.edtAPEndTime.setVisible(False)
            if (action and
                    ((action.getExecutionPlan() and
                    action.executionPlanManager.hasItemsToDo()) or actionType.isDoesNotInvolveExecutionCourse) and
                    self.cmbAPStatus.value() != CActionStatus.canceled):
                if actionType.isDoesNotInvolveExecutionCourse and self.cmbAPStatus.value() == CActionStatus.finished:
                    self.btnNextAction.setText(u'Действие')
                    self.btnNextAction.setEnabled(False)
                else:
                    self.btnNextAction.setText(u'Выполнить')
                    isEnable = self.cmbAPStatus.value() != CActionStatus.refused
                    if action.getType().isNomenclatureExpense:
                        isEnable = isEnable and self.isEnabledNomenclatureExpense(action)
                    self.btnNextAction.setEnabled(isEnable)
            else:
                self.btnNextAction.setText(u'Действие')
                self.btnNextAction.setEnabled(False)
            if self.edtAPDuration.value() > 0:
                self.btnPlanNextAction.setEnabled(True)
            else:
                self.btnPlanNextAction.setEnabled(False)
            self.btnAPNomenclatureExpense.setEnabled(False)
        if actionType:
            stockMotionId = None
            if action and actionType.isNomenclatureExpense:
                recordExpense = action.getRecord()
                stockMotionId = forceRef(recordExpense.value('stockMotion_id'))
            self.cmbAPOrgStructure.setEnabled(self.cmbAPOrgStructure.isEnabled() and not actionType.hasJobTicketPropertyType() and not stockMotionId)
        self.cmbAPMKB.setFilter('''case when MKB.endDate IS NOT NULL then MKB.endDate >= %s else true end'''%(QtGui.qApp.db.formatDate(self.edtAPBegDate.date())))
        if self.cmbAPMKB.isVisible() and QtGui.qApp.isExSubclassMKBVisible():
            self.lblAPMKBExSubclass.setVisible(True)
            self.cmbAPMKBExSubclass.setVisible(True)
        else:
            self.lblAPMKBExSubclass.setVisible(False)
            self.cmbAPMKBExSubclass.setVisible(False)

        if not QtGui.qApp.userHasRight(canChangeActionPerson):
            self.cmbAPPerson.setEnabled(False)

    def ActionTMK_BTN_Visible(self, action, actionType):
        self.btnAPQueueManagement.setText(u'ТМК')

        if action._propertiesByShortName['direction_identifier']._value:
            self.actCreatingApplication.setText(u'Перейти в направление')
        else:
            self.actCreatingApplication.setText(u'Создать направление')

        self.actAPQMCancelReferral.setVisible(False)
        self.actAPQMCreateClaimForRefusal.setVisible(False)
        self.actAPQMSetAppointment.setVisible(False)
        self.actImportAvailableProfiles.setVisible(False)
        self.btnAPQueueManagement.setEnabled(True)
        self.actCreatingApplication.setVisible(True)
        self.actViewingApplications.setVisible(True)



    def getBlankSerialNumberParams(self, docTypeId):
        blankParams = {}
        blankIdList = []
        text = ''
        if docTypeId:
            db = QtGui.qApp.db
            personId = QtGui.qApp.userId
            tableRBBlankTempInvalids = db.table('rbBlankActions')
            tableBlankTempInvalidParty = db.table('BlankActions_Party')
            tableBlankTempInvalidMoving = db.table('BlankActions_Moving')
            tableTempInvalid = db.table('TempInvalid')
            tablePerson = db.table('Person')
            orgStructureId = None
            if personId:
                orgStructRecord = db.getRecordEx(tablePerson, [tablePerson['orgStructure_id']], [tablePerson['deleted'].eq(0), tablePerson['id'].eq(personId)])
                orgStructureId = forceRef(orgStructRecord.value('orgStructure_id')) if orgStructRecord else None

            cols = [tableBlankTempInvalidMoving['id'].alias('blankMovingId'),
                    tableBlankTempInvalidParty['serial'],
                    tableBlankTempInvalidMoving['numberFrom'],
                    tableBlankTempInvalidMoving['numberTo'],
                    tableBlankTempInvalidMoving['returnAmount'],
                    tableBlankTempInvalidMoving['used'],
                    tableBlankTempInvalidMoving['received']
                    ]
            cond = [tableRBBlankTempInvalids['doctype_id'].eq(docTypeId),
                    tableBlankTempInvalidParty['deleted'].eq(0),
                    tableBlankTempInvalidMoving['deleted'].eq(0)
                    ]
            cond.append('''BlankActions_Moving.received > (BlankActions_Moving.used - BlankActions_Moving.returnAmount)''')
            order = []
            queryTable = tableBlankTempInvalidParty.innerJoin(tableBlankTempInvalidMoving, tableBlankTempInvalidMoving['blankParty_id'].eq(tableBlankTempInvalidParty['id']))
            order = []
            orgStructureIdList = db.getTheseAndParents('OrgStructure', 'parent_id', [orgStructureId]) if orgStructureId else []
            if personId and orgStructureIdList:
                cond.append(db.joinOr([tableBlankTempInvalidMoving['person_id'].eq(personId), tableBlankTempInvalidMoving['orgStructure_id'].inlist(orgStructureIdList)]))
                order.append(u'BlankActions_Moving.person_id')
            elif personId:
                cond.append(tableBlankTempInvalidMoving['person_id'].eq(personId))
            elif orgStructureIdList:
                cond.append(tableBlankTempInvalidMoving['orgStructure_id'].inlist(orgStructureIdList))
            queryTable = tableRBBlankTempInvalids.innerJoin(tableBlankTempInvalidParty, tableBlankTempInvalidParty['doctype_id'].eq(tableRBBlankTempInvalids['id']))
            queryTable = queryTable.innerJoin(tableBlankTempInvalidMoving, tableBlankTempInvalidMoving['blankParty_id'].eq(tableBlankTempInvalidParty['id']))
            order.append(u'BlankActions_Moving.numberFrom ASC')
            records = db.getRecordList(queryTable, cols, cond, order)
            for record in records:
                blankInfo = {}
                blankMovingId = forceRef(record.value('blankMovingId'))
                serial = forceString(record.value('serial'))
                numberFromString = forceString(record.value('numberFrom'))
                numberFromFirstChar = numberFromString[:1]
                numberFrom = int(numberFromString) if numberFromString else 0
                numberToString = forceString(record.value('numberTo'))
                numberTo = int(numberToString) if numberToString else 0
                returnAmount = forceInt(record.value('returnAmount'))
                used = forceInt(record.value('used'))
                received = forceInt(record.value('received'))
                blankInfo['serial'] = serial
                blankInfo['numberFromFirstChar'] = numberFromFirstChar
                blankInfo['numberFrom'] = numberFrom
                blankInfo['numberTo'] = numberTo
                blankInfo['returnAmount'] = returnAmount
                blankInfo['used'] = used
                blankInfo['received'] = received
                blankParams[blankMovingId] = blankInfo
                blankIdList.append(blankMovingId)
            if blankIdList:
                movingId = blankIdList[0]
            else:
                movingId = None
            if movingId:
                blankInfo = blankParams.get(movingId, None)
                if blankInfo:
                    serial = forceString(blankInfo.get('serial', u''))
                    numberFromFirstChar = blankInfo.get('numberFromFirstChar', u'')
                    numberFrom = blankInfo.get('numberFrom', 0)
                    numberTo = blankInfo.get('numberTo', 0)
                    returnAmount = forceInt(blankInfo.get('returnAmount', 0))
                    used = forceInt(blankInfo.get('used', 0))
                    received = forceInt(blankInfo.get('received', 0))
                    balance = received - used - returnAmount
                    if balance > 0:
                        number = numberFrom + used + returnAmount
                        if number <= numberTo:
                            numberBlank = number
                            if numberFromFirstChar and numberFromFirstChar == u'0':
                                numberBlank = numberFromFirstChar + forceString(number)
                            record = db.getRecordEx(tableTempInvalid, [tableTempInvalid['id']], [tableTempInvalid['deleted'].eq(0), tableTempInvalid['serial'].eq(serial), tableTempInvalid['number'].eq(numberBlank)])
                            if not record:
                                text = forceString(serial) + u' ' + forceString(numberBlank)
        return  text
        

    def on_actSetLaboratoryCalculatorInfo(self):
        result = self.eventEditor.checkNeedLaboratoryCalculator(self.modelAPActionProperties.propertyTypeList,
                                                                self.on_laboratoryCalculatorClipboard)
        self._canUseLaboratoryCalculatorPropertyTypeList = result
        self.setInfoToLaboratoryCalculatorClipboard()


    def setInfoToLaboratoryCalculatorClipboard(self):
        def chooseLabCode(propType):
            code = propType.laboratoryCalculator
            if code in ('LL*', 'GG*', 'EE*', 'CI*'):
                return '%s%s'%(code, forceString(self.modelAPActionProperties.action.getPropertyById(propType.id).getValue()))
            else:
                return code
        if self._canUseLaboratoryCalculatorPropertyTypeList:
            propertyTypeList = self._canUseLaboratoryCalculatorPropertyTypeList
            actual = unicode('; '.join(['('+','.join([forceString(propType.id),
                chooseLabCode(propType),#'LL*%s'%forceString(self.modelAPActionProperties.action.getPropertyByIndex(i).getValue()) if propType.laboratoryCalculator == 'LL*' else propType.laboratoryCalculator,
                propType.name])+')' for propType in propertyTypeList]))
            QtGui.qApp.log(u'Передача в лаб кальк', actual)
            mimeData = QMimeData()
            mimeData.setData(QtGui.qApp.inputCalculatorMimeDataType,
                             QString(actual).toUtf8())
            QtGui.qApp.clipboard().setMimeData(mimeData)
            self._mainWindowState = QtGui.qApp.mainWindow.windowState()
            QtGui.qApp.mainWindow.showMinimized()

    def on_laboratoryCalculatorClipboard(self):
        QtGui.qApp.setActiveWindow(self.eventEditor)
        mimeData = QtGui.qApp.clipboard().mimeData()
        baData = mimeData.data(QtGui.qApp.outputCalculatorMimeDataType)
        if baData:
            QtGui.qApp.mainWindow.setWindowState(self._mainWindowState)
            data = forceString(QString.fromUtf8(baData))
            self.modelAPActionProperties.setLaboratoryCalculatorData(data)


    def onCurrentActionAdd(self, flatCode, action):
        model = self.tblAPActions.model()
        items = model.items()
        relegateOrgId = self.eventEditor.tabVoucher.cmbDirectionOrgs.value() if getEventTypeForm(self.eventEditor.eventTypeId) == u'072' else self.eventEditor.tabNotes.cmbRelegateOrg.value()
        if relegateOrgId and (relegateOrgId != QtGui.qApp.currentOrgId()
            and self.cmbAPStatus.currentIndex() in (CActionStatus.started, CActionStatus.wait, CActionStatus.withoutResult, CActionStatus.appointed)
            and ('recoveryDirection'.lower() in flatCode.lower()
            or u'inspectionDirection'.lower() in flatCode.lower()
            or u'researchDirection'.lower() in flatCode.lower()
            or u'consultationDirection'.lower() in flatCode.lower()
            or (u'planning'.lower() in flatCode.lower() and getEventCode(self.eventEditor.eventTypeId) == u'УО'))
           ):
            self.btnNextAction.setText(u'Выполнить')
            isEnable = True
            if action.getType().isNomenclatureExpense:
                isEnable = isEnable and self.isEnabledNomenclatureExpense(action)
            self.btnNextAction.setEnabled(isEnable)
        elif u'createNIL' in flatCode and QtGui.qApp.gis_oms_enable():
            if action[u'Номер листа регистрации']:
                self.btnNextAction.setText(u'Обновить НИЛ')
            else:
                self.btnNextAction.setText(u'Создать НИЛ')
            self.btnNextAction.setEnabled(True)
        else:
            noPresentLeaved = True
            for item in items:
                record, actionItem = item
                if record:
                    actionTypeId = forceRef(record.value('actionType_id'))
                    actionType = CActionTypeCache.getById(actionTypeId) if actionTypeId else None
                    if u'leaved' in actionType.flatCode.lower():
                        noPresentLeaved = False
                        break
            if noPresentLeaved:
                if u'received' in flatCode.lower():
                    if action[u'Направлен в отделение']:
                        self.btnNextAction.setText(u'Перевод')
                        self.btnNextAction.setEnabled(self.edtAPEndDate.date().isNull())
                    else:
                        self.btnNextAction.setText(u'Выписка')
                        isEnable = not self.isReadOnly() and ((QtGui.qApp.userHasRight(urHBLeaved) or QtGui.qApp.isAdmin()) if (self.eventEditor and self.eventEditor.isHBDialog) else True)
                        self.btnNextAction.setEnabled(self.edtAPEndDate.date().isNull() and isEnable)
                elif u'moving' in flatCode.lower():
                    if action[u'Переведен в отделение']:
                        self.btnNextAction.setText(u'Перевод')
                        self.btnNextAction.setEnabled(self.edtAPEndDate.date().isNull())
                    else:
                        self.btnNextAction.setText(u'Выписка')
                        isEnable = not self.isReadOnly() and ((QtGui.qApp.userHasRight(urHBLeaved) or QtGui.qApp.isAdmin()) if (self.eventEditor and self.eventEditor.isHBDialog) else True)
                        self.btnNextAction.setEnabled(self.edtAPEndDate.date().isNull() and isEnable)
                elif u'inspectPigeonHole'.lower() in flatCode.lower():
                    self.btnNextAction.setText(u'Закончить')
                    self.btnNextAction.setEnabled(self.edtAPEndDate.date().isNull())
                else:
                    if (action and
                            ((action.getExecutionPlan() and
                            action.executionPlanManager.hasItemsToDo()) or actionType.isDoesNotInvolveExecutionCourse) and
                            self.cmbAPStatus.value() != CActionStatus.canceled):
                        if actionType.isDoesNotInvolveExecutionCourse and self.cmbAPStatus.value() == CActionStatus.finished:
                            self.btnNextAction.setText(u'Действие')
                            self.btnNextAction.setEnabled(False)
                        else:
                            self.btnNextAction.setText(u'Выполнить')
                            isEnable = self.cmbAPStatus.value() != CActionStatus.refused
                            if action.getType().isNomenclatureExpense:
                                isEnable = isEnable and self.isEnabledNomenclatureExpense(action)
                            self.btnNextAction.setEnabled(isEnable)
                    else:
                        self.btnNextAction.setText(u'Действие')
                        self.btnNextAction.setEnabled(self.isTrailerActionType())
                    if self.edtAPDuration.value() > 0:
                        self.btnPlanNextAction.setEnabled(True)
                    else:
                        self.btnPlanNextAction.setEnabled(False)
            else:
                if (action and
                        ((action.getExecutionPlan() and
                        action.executionPlanManager.hasItemsToDo()) or actionType.isDoesNotInvolveExecutionCourse) and
                        self.cmbAPStatus.value() != CActionStatus.canceled):
                    if actionType.isDoesNotInvolveExecutionCourse and self.cmbAPStatus.value() == CActionStatus.finished:
                        self.btnNextAction.setText(u'Действие')
                        self.btnNextAction.setEnabled(False)
                    else:
                        self.btnNextAction.setText(u'Выполнить')
                        isEnable = self.cmbAPStatus.value() != CActionStatus.refused
                        if action.getType().isNomenclatureExpense:
                            isEnable = isEnable and self.isEnabledNomenclatureExpense(action)
                        self.btnNextAction.setEnabled(isEnable)
                else:
                    self.btnNextAction.setText(u'Действие')
                    self.btnNextAction.setEnabled(self.isTrailerActionType())
                if self.edtAPDuration.value() > 0:
                    self.btnPlanNextAction.setEnabled(True)
                else:
                    self.btnPlanNextAction.setEnabled(False)


    def getIdListActionType(self, flatCode):
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
            dialogActionType = CActionTypeDialogTableModel(self, idListActionType)
            if dialogActionType.exec_():
                actionTypeId= dialogActionType.currentItemId()
        else:
            actionTypeId = idListActionType[0] if idListActionType else None
        return actionTypeId


    def checkActionByNextEventCreation(self):
        if QtGui.qApp.isNextEventCreationFromAction() == 1:
            res = QtGui.QMessageBox.warning(self,
                                   u'Внимание!',
                                   u'Добавить движение во вновь зарегистрированное Событие?',
                                   QtGui.QMessageBox.Yes|QtGui.QMessageBox.No|QtGui.QMessageBox.Help,
                                   QtGui.QMessageBox.No)
            if res == QtGui.QMessageBox.Yes:
                return True
            elif res == QtGui.QMessageBox.Help:
                QtGui.QMessageBox.information(self, 
                            u'Справка', 
                            u'При согласии, действие "Движение" будет добавлено в новое событие, текущее событие будет закрыто. Это необходимо в том случае, если перевод пациента связан с изменением МЭСа.')
                res = self.checkActionByNextEventCreation()
                return res
            else:
                return False
        elif QtGui.qApp.isNextEventCreationFromAction() == 2:
            return True
        return False


    def checkPolicyOnActionsEndDate(self):
        for row, (record, action) in enumerate(self.modelAPActions.items()):
            actionId = forceRef(record.value('id'))
            if not actionId in self.modelAPActions.loadedActionIdListWithEndDate():
                if not checkPolicyOnDate(self.clientId(), forceDate(record.value('endDate'))):
                    skippable = QtGui.qApp.isStrictCheckPolicyOnEndAction() == 0
                    if not self.eventEditor.checkInputMessage(u'время закрытия действия соответствующее полису',
                                                              skippable, self.tblAPActions, row=row, column=0):
                        self.edtAPEndDate.setFocus(Qt.ShortcutFocusReason)
                        return False
        return True


    def checkAttachOnActionsEndDate(self):
        for row, (record, action) in enumerate(self.modelAPActions.items()):
            actionId = forceRef(record.value('id'))
            if not actionId in self.modelAPActions.loadedActionIdListWithEndDate():
                if not checkAttachOnDate(self.clientId(), forceDate(record.value('endDate'))):
                    skippable = QtGui.qApp.isStrictCheckAttachOnEndAction() == 0
                    if not self.eventEditor.checkInputMessage(u'время закрытия действия соответствующее прикреплению',
                                                              skippable, self.tblAPActions, row=row, column=0):
                        self.edtAPEndDate.setFocus(Qt.ShortcutFocusReason)
                        return False
        return True


    def checkAPRelatedAction(self):
        tabs = {}
        if hasattr(self.eventEditor, 'tabStatus'):
            tabs[0] = self.eventEditor.tabStatus
        if hasattr(self.eventEditor, 'tabDiagnostic'):
            tabs[1] = self.eventEditor.tabDiagnostic
        if hasattr(self.eventEditor, 'tabCure'):
            tabs[2] = self.eventEditor.tabCure
        if hasattr(self.eventEditor, 'tabMisc'):
            tabs[3] = self.eventEditor.tabMisc
        if not tabs:
            tabs = {0: self.eventEditor.tabActions,
                    1: self.eventEditor.tabActions,
                    2: self.eventEditor.tabActions,
                    3: self.eventEditor.tabActions}

        for row, parentItem in enumerate(self.modelAPActions.items()):
            record, action = parentItem.record, parentItem.action
            # group = self.modelAPActions._mapModelRow2ProxyRow[row]
            # if not self.modelAPActions._mapProxyRow2Group[group].expanded:
            #     self.modelAPActions.touchGrouping(group)

            if action:
                parentActionType = CActionTypeCache.getById(action.getType().id)
                reqActionTypes = parentActionType.getRelatedActionTypes()
                if reqActionTypes:
                    actionTypes = []
                    required = False
                    dlg = CAddRelatedAction(self, reqActionTypes.keys())
                    for item in self.modelAPActions._mapProxyRow2Group[self.modelAPActions._mapModelRow2ProxyRow[row]].items:
                        actionTypes.append(item.action.getType().id)
                    for actionType, isRequired in reqActionTypes.items():
                        relatedActionType = CActionTypeCache.getById(actionType)
                        if isRequired and actionType not in actionTypes and parentActionType.class_ == relatedActionType.class_:
                            required = True
                            dlg.setSelected(actionType, True)
                        elif isRequired and actionType not in actionTypes:
                            required = True
                            for item in tabs[relatedActionType.class_].modelAPActions.items():
                                if item.action.getMasterId() == parentItem.id:
                                    required = False
                            if required:
                                dlg.setSelected(actionType, True)
                    if required:
                        nameActionType = action._actionType.name[:50] + '...' if len(action._actionType.name) > 50 else action._actionType.name
                        if not self.eventEditor.checkValueMessage(u'Действие \"%s\" не имеет обязательных подчиненных действий!' % nameActionType,
                                                                    True, self.tblAPActions, row=row, column=0):
                            if dlg.exec_():
                                result = dlg.getSelectedList()
                                for actionType in result:
                                    index = self.modelAPActions._actionModel.index(self.modelAPActions._actionModel.rowCount() - 1, 0)
                                    self.modelAPActions.setData(index, actionType, self.modelAPActions._mapProxyRow2Group[self.modelAPActions._mapModelRow2ProxyRow[row]])
                            return False
        return True


    def checkAPDataEntered(self):
        isStrictCheckPolicyOnEndAction = QtGui.qApp.isStrictCheckPolicyOnEndAction()
        isStrictCheckAttachOnEndAction = QtGui.qApp.isStrictCheckAttachOnEndAction()
        checkPolicyOnEndAction = isStrictCheckPolicyOnEndAction in (0, 1) or isStrictCheckAttachOnEndAction in (0, 1)
        for row, (record, action) in enumerate(self.modelAPActions.items()):
            # group = self.modelAPActions._mapModelRow2ProxyRow[row]
            # if not self.modelAPActions._mapProxyRow2Group[group].expanded:
            #     self.modelAPActions.touchGrouping(group)
            actionId = forceRef(record.value('id'))
            statusNeedAttachFile = action._actionType.isNeedAttachFile
            if checkPolicyOnEndAction:
                if not actionId in self.modelAPActions.loadedActionIdListWithEndDate():
                    if isStrictCheckPolicyOnEndAction in (0, 1):
                        if not checkPolicyOnDate(self.clientId(), forceDate(record.value('endDate'))):
                            skippable = isStrictCheckPolicyOnEndAction == 0
                            if not self.eventEditor.checkInputMessage(u'время закрытия действия соответствующее полису',
                                                                      skippable, self.tblAPActions, row=row, column=0):
                                self.edtAPEndDate.setFocus(Qt.ShortcutFocusReason)
                                return False
                    if isStrictCheckAttachOnEndAction in (0, 1):
                        if not checkAttachOnDate(self.clientId(), forceDate(record.value('endDate'))):
                            skippable = isStrictCheckAttachOnEndAction == 0
                            if not self.eventEditor.checkInputMessage(u'время закрытия действия соответствующее прикреплению',
                                                                      skippable, self.tblAPActions, row=row, column=0):
                                self.edtAPEndDate.setFocus(Qt.ShortcutFocusReason)
                                return False
            if action and action.nomenclatureExpense:
                nomenclatureName = None
                if not action.nomenclatureExpense.stockMotionItems() and forceInt(record.value('status'))==2:
                    for property in action._properties:
                        if property.type().name == u'ЛСиИМН':
                            nomenclatureName = forceString(QtGui.qApp.db.translate(u'rbNomenclature', 'id', property._value, 'name'))
                            nomenclatureCode = forceString(QtGui.qApp.db.translate(u'rbNomenclature', 'id', property._value, 'code'))
                            self.notAvialableNomenclatureDict[nomenclatureName] = nomenclatureCode
                            res =  self.eventEditor.checkValueMessageIgnoreAll(u'Списываемое ЛСиИМН %s - %s отсутствует на складе' % (nomenclatureCode,  nomenclatureName),
                                                                                True, self.tblAPActions, row=row, column=0)
                            if res == 0:
                                return False
                            elif res == 2:
                                return True
                    if not nomenclatureName:
                        if not self.eventEditor.checkInputMessage(u'списываемые ЛСиИМН',
                                                              True, self.tblAPActions, row=row, column=0):
                            self.btnAPNomenclatureExpense.setFocus(Qt.ShortcutFocusReason)
                            return False
            begDate = forceDate(record.value('begDate'))
            MKB = forceString(record.value('MKB'))
            financeId = forceRef(record.value('finance_id'))
            if MKB and not self.checkActualMKB(row, MKB, begDate, financeId):
                return False
            endDate = forceDate(record.value('endDate'))
            personId = forceInt(record.value('person_id'))
            setPersonId = forceInt(record.value('setPerson_id'))
            nameActionType = action._actionType.name[:50] + '...' if len(action._actionType.name) > 50 else action._actionType.name
            attachFiles = [filesItem for filesItem in action._attachedFileItemList if filesItem.newName.lower().endswith('pdf')]
            if statusNeedAttachFile in (1, 2) and endDate.isValid() and not attachFiles:
                db = QtGui.qApp.db
                currentSNILS = forceRef(db.translate('Person', 'id', QtGui.qApp.userId, 'SNILS'))
                personIdSNILS = forceRef(db.translate('Person', 'id', personId, 'SNILS'))
                setPersonIdSNILS = forceRef(db.translate('Person', 'id', setPersonId, 'SNILS'))
                if (statusNeedAttachFile == 1 and currentSNILS == personIdSNILS) or (statusNeedAttachFile == 2 and currentSNILS == setPersonIdSNILS):
                    skippable = QtGui.qApp.userHasRight(urCanIgnoreAttachFile)
                    message = u'Действие \"%s\" не имеет прикреплённых документов!' % nameActionType
                    res = self.eventEditor.checkValueMessage(message, skippable, self.tblAPActions, row, 0)
                    if res:
                        continue
                    else:
                        return False
        return True


    def checkActualMKB(self, row, MKB, begDate, financeId):
        result = True
        db = QtGui.qApp.db
        tableMKB = db.table('MKB')
        cond = [tableMKB['DiagID'].eq(MKBwithoutSubclassification(MKB))]
        cond.append(db.joinOr([tableMKB['endDate'].isNull(), tableMKB['endDate'].dateGe(begDate)]))
        recordMKB = db.getRecordEx(tableMKB, [tableMKB['DiagID']], cond)
        result = result and (forceString(recordMKB.value('DiagID')) == MKBwithoutSubclassification(MKB) if recordMKB else False) or self.eventEditor.checkValueMessage(u'Диагноз %s не доступен для применения' % MKB, False, self.tblAPActions, row=row, column=0)
        if financeId is None:
            financeId = self.eventEditor.eventFinanceId
        # проверка на "оплачиваемость" диагноза в системе ОМС для КК
        if result and QtGui.qApp.provinceKLADR()[:2] == u'23' and CFinanceType.getCode(financeId) == 2:
            tableSpr20 = db.table('soc_spr20')
            if begDate:
                cond = [db.joinOr([tableSpr20['code'].eq(MKB), tableSpr20['code'].eq(MKB[:3])]),
                        db.joinOr([tableSpr20['dato'].isNull(), tableSpr20['dato'].dateGe(begDate)]),
                        tableSpr20['datn'].dateLe(begDate)]
            else:
                cond = [db.joinOr([tableSpr20['code'].eq(MKB), tableSpr20['code'].eq(MKB[:3])]),
                        tableSpr20['dato'].isNull()]
            recordMKB = db.getRecordEx(tableSpr20, [tableSpr20['code']], cond)
            if not recordMKB:
                result = self.eventEditor.checkValueMessage(u'Диагноз %s не оплачивается в системе ОМС!' % MKB, QtGui.qApp.userHasRight(urCanSaveEventWithMKBNotOMS), self.tblAPActions, row=row, column=0)
        return result


    @pyqtSignature('')
    def on_btnPlanNextAction_clicked(self):
        model = self.tblAPActions.model()
        items = model.items()
        row = self.tblAPActions.currentIndex().row()
        if 0<=row<len(items):
            record, action = items[row]
            if record and action:
                orgStructureIdList = []
                if not action.getType().isNomenclatureExpense:
                    currentOrgStructureId = QtGui.qApp.currentOrgStructureId()
                    userOrgStructureId = QtGui.qApp.userOrgStructureId
                    currentOrgStructureIdList = []
                    userOrgStructureIdList = []
                    db = QtGui.qApp.db
                    tableOrgStructure = db.table('OrgStructure')
                    if currentOrgStructureId:
                        recordOS = db.getRecordEx(tableOrgStructure, [tableOrgStructure['parent_id']], [tableOrgStructure['id'].eq(currentOrgStructureId), tableOrgStructure['deleted'].eq(0)])
                        parentOSId = forceRef(recordOS.value('parent_id')) if recordOS else None
                        currentOrgStructureIdList = db.getDescendants('OrgStructure', 'parent_id', parentOSId if parentOSId else currentOrgStructureId)
                    if userOrgStructureId:
                        recordOS = db.getRecordEx(tableOrgStructure, [tableOrgStructure['parent_id']], [tableOrgStructure['id'].eq(userOrgStructureId), tableOrgStructure['deleted'].eq(0)])
                        parentOSId = forceRef(recordOS.value('parent_id')) if recordOS else None
                        userOrgStructureIdList = db.getDescendants('OrgStructure', 'parent_id', parentOSId if parentOSId else userOrgStructureId)
                    orgStructureIdList = list(set(currentOrgStructureIdList)|set(userOrgStructureIdList))
                dialog = CGetExecutionPlan(self, record, action.getExecutionPlan(), action = action, orgStructureIdList = orgStructureIdList)
                dialog.setVisibleBtn(False)
                dialog.exec_()
                action.executionPlanManager.setExecutionPlan(dialog.model.executionPlan)


    def _onNextActionIsInspectPigeonHole(self, record, endDate):
        endDate = forceDateTime(record.value('endDate'))
        if not endDate:
            record.setValue('endDate', toVariant(endDate))
        record.setValue('status', toVariant(2))
        if hasattr(self.eventEditor, 'btnNextActionSetFocus'):
            self.eventEditor.btnNextActionSetFocus()


    def _onExecActionIsDoesNotInvolveExecutionCourse(self, action, record, newEndDate):
        prevActionStatus = forceRef(record.value('status'))
        record.setValue('status', toVariant(CActionStatus.finished))
        endDate = forceDateTime(record.value('endDate'))
        if not endDate:
            record.setValue('endDate', toVariant(newEndDate))
#        begDate = forceDateTime(record.value('begDate'))
#        endDate = forceDateTime(record.value('endDate'))
#        if not endDate:
#            record.setValue('endDate', toVariant(begDate))
        record.setValue('person_id', toVariant(
            QtGui.qApp.userId if (QtGui.qApp.userId and QtGui.qApp.userSpecialityId) else self.cmbAPSetPerson.value())
        )
        if action.nomenclatureExpense:
            action = updateNomenclatureDosageValue(action)
            nomenclatureIdDict = {}
            if action.executionPlanManager:
                executionPlanItem = action.executionPlanManager.currentItem
                if executionPlanItem and executionPlanItem.nomenclature and executionPlanItem.nomenclature.nomenclatureId:
                    if executionPlanItem.nomenclature.nomenclatureId:
                        nomenclatureIdDict[executionPlanItem.nomenclature.nomenclatureId] = (action.getRecord(), executionPlanItem.nomenclature.dosage)
            orgStructureId = forceRef(record.value('orgStructure_id'))
            isControlExecWriteOffNomenclatureExpense = QtGui.qApp.controlExecutionWriteOffNomenclatureExpense()
            if isControlExecWriteOffNomenclatureExpense:
                db = QtGui.qApp.db
                message = u''
                nomenclatureLine = []
                resQntDict = {}
                tableNomenclature = db.table('rbNomenclature')
                if action.nomenclatureExpense:
                    stockMotionItems = action.nomenclatureExpense.stockMotionItems()
                    for stockMotionItem in stockMotionItems:
                        price = forceDouble(stockMotionItem.value('price'))
                        oldPrice = price
                        nomenclatureId = forceRef(stockMotionItem.value('nomenclature_id'))
                        if nomenclatureId and nomenclatureId not in nomenclatureLine:
                            qnt = forceDouble(stockMotionItem.value('qnt'))
                            resQnt, proxyQnt, planQnt, simpleRatio = resQntDict.get(nomenclatureId, (None, None, None, 2))
                            unitId = forceRef(stockMotionItem.value('unit_id'))
                            stockUnitId = self.getDefaultStockUnitId(nomenclatureId)
                            ratio = self.getRatio(nomenclatureId, stockUnitId, unitId)
                            if ratio is not None:
                                price = price*ratio
                                qnt = qnt / ratio
                            qnt = round(qnt, QtGui.qApp.numberDecimalPlacesQnt())
                            if planQnt is None:
                                nomenclativeRecord, dosage = nomenclatureIdDict.get(nomenclatureId, (None, 0))
                                planQnt = action.nomenclatureExpense.getNomenclatureDosageToQntValue(nomenclatureId, dosage)
                                if ratio is not None:
                                    planQnt = planQnt / ratio
                                planQnt = round(planQnt, QtGui.qApp.numberDecimalPlacesQnt())
                            if proxyQnt is None:
                                proxyQnt = 0
                                model = self.tblAPActions.model()
                                mapProxyRow2Group = model._mapProxyRow2Group
                                actionRow = self.tblAPActions.currentIndex().row()
                                if mapProxyRow2Group and actionRow >= 0 and actionRow < len(model.items()) and actionRow in mapProxyRow2Group.keys():
                                    proxyGroup = mapProxyRow2Group[actionRow]
                                    if proxyGroup:
                                        for proxyItem in proxyGroup.items:
                                            i = proxyGroup._mapItem2Row.get(proxyItem, -1)
                                            if i > -1 and i != proxyGroup._headModelRow:
                                                proxyQnt += proxyItem.action.findDosagePropertyValue()
                                        if ratio is not None:
                                            proxyQnt = proxyQnt / ratio
                                        proxyQnt = round(proxyQnt, QtGui.qApp.numberDecimalPlacesQnt())
                            if proxyQnt > 0:
                                proxyQnt = proxyQnt - qnt
                                proxyQnt = round(proxyQnt, QtGui.qApp.numberDecimalPlacesQnt())
                            if proxyQnt < 0:
                                proxyQnt = 0
                            financeId = forceRef(stockMotionItem.value('finance_id'))
                            batch = forceString(stockMotionItem.value('batch'))
                            shelfTime = forceDate(stockMotionItem.value('shelfTime'))
                            shelfTime = shelfTime.toPyDate() if bool(shelfTime) else None
                            medicalAidKindId = forceRef(stockMotionItem.value('medicalAidKind_id'))
                            otherHaving=[u'(shelfTime>=curDate()) OR shelfTime is NULL']
                            existsQnt = getExistsNomenclatureAmount(nomenclatureId, financeId, batch, orgStructureId=orgStructureId, unitId=stockUnitId, medicalAidKindId = medicalAidKindId, shelfTime=shelfTime, otherHaving=otherHaving, exact=True, price=price, isStockUtilization=False, precision=QtGui.qApp.numberDecimalPlacesQnt())
                            masterId = forceRef(stockMotionItem.value('master_id'))
                            prevQnt = round(getStockMotionItemQntEx(nomenclatureId, stockMotionId=masterId, batch=batch, financeId=financeId, medicalAidKindId=medicalAidKindId, price=None, oldPrice=oldPrice, oldUnitId=stockUnitId), QtGui.qApp.numberDecimalPlacesQnt()) if masterId else 0
                            reservationQnt = round(getStockMotionItemQntEx(nomenclatureId, stockMotionId=None, batch=batch, financeId=financeId, clientId=self.clientId(), medicalAidKindId=medicalAidKindId, price=None, oldPrice=price, oldUnitId=stockUnitId), QtGui.qApp.numberDecimalPlacesQnt())
                            if existsQnt < 0:
                                existsQnt = 0
                            if prevQnt < 0:
                                prevQnt = 0
                            if reservationQnt < 0:
                                reservationQnt = 0
                            if resQnt is None:
                                resQnt = (existsQnt + reservationQnt + prevQnt) - qnt
                            else:
                                resQnt += (existsQnt + reservationQnt + prevQnt) - qnt
                            resQnt = round(resQnt, QtGui.qApp.numberDecimalPlacesQnt())
                            planQnt = planQnt - qnt
                            planQnt = round(planQnt, QtGui.qApp.numberDecimalPlacesQnt())
                            resQntDict[nomenclatureId] = (resQnt, proxyQnt, planQnt, len(forceStringEx(self.getSimpleRatio(nomenclatureId, stockUnitId, unitId))))
                    for nomenclatureIdKey, (resQntValue, proxyQntValue, planQntValue, simpleQntRatio) in resQntDict.items():
                        if resQntValue < 0 or resQntValue is None or (round(planQntValue, len(forceStringEx(simpleQntRatio))) != 0 and planQntValue is not None):
                            nomenclatureLine.append(nomenclatureIdKey)
                    if nomenclatureLine:
                        nomenclatureName = u''
                        records = db.getRecordList(tableNomenclature, [tableNomenclature['name']], [tableNomenclature['id'].inlist(nomenclatureLine)], order = tableNomenclature['name'].name())
                        nomenclatureName = u','.join(forceString(recordNomenclature.value('name')) for recordNomenclature in records)
                        message += u'''Действие типа %s.\nОтсутствуют ЛСиИМН: %s!\n'''%(action._actionType.name, nomenclatureName)
                    if message:
                        if isControlExecWriteOffNomenclatureExpense == 1:
                            button = QtGui.QMessageBox.Ok|QtGui.QMessageBox.Cancel
                            message2 = u'Списываемого ЛСиИМН %s недостаточно на остатке подразделения. Выполнить списание?'%(nomenclatureName)
                        else:
                            button = QtGui.QMessageBox.Cancel
                            message2 = u'Списываемого ЛСиИМН %s недостаточно на остатке подразделения. Выполнение назначения невозможно!\n'%(nomenclatureName)
                        res = QtGui.QMessageBox.warning(None,
                                                  u'Внимание!',
                                                  message2,
                                                  button,
                                                  QtGui.QMessageBox.Cancel)
                        if res == QtGui.QMessageBox.Cancel:
                            record.setValue('status', toVariant(prevActionStatus))
                            return
            if not self._openNomenclatureEditor(action, record, requireItems=True):
                record.setValue('status', toVariant(prevActionStatus))
                if action.nomenclatureExpense:
                    action.nomenclatureExpense.cancelEx()
                return False
            nextExecutionPlanItem = None
            if action.executionPlanManager.executionPlan:
                currentExecutionPlanItem = action.executionPlanManager._currentItem
                action.executionPlanManager.setCurrentItemIndex(action.executionPlanManager.executionPlan.items.index(currentExecutionPlanItem))
                nextExecutionPlanItem = action.executionPlanManager.getNextItem()
                action.executionPlanManager.setCurrentItemExecuted()
                while nextExecutionPlanItem:
                    action.executionPlanManager.setCurrentItemIndex(action.executionPlanManager.executionPlan.items.index(nextExecutionPlanItem))
                    nextExecutionPlanItem = action.executionPlanManager.getNextItem()
                    action.executionPlanManager.setCurrentItemExecuted()
    #            if not nextExecutionPlanItem:
    #                if action.nomenclatureClientReservation:
    #                    action.nomenclatureClientReservation.cancel()
                action.executionPlanManager.setCurrentItemIndex(action.executionPlanManager.executionPlan.items.index(currentExecutionPlanItem))
    #            action.setNomenclatureExpenseChange(action.saveNomenclatureExpense(action.nomenclatureExpensePreliminarySave, isActionNoSave = True))
            elif action.executionPlanManager and action.executionPlanManager._currentItem:
                action.executionPlanManager.setCurrentItemExecuted()
        else:
            record.setValue('status', toVariant(CActionStatus.finished))
        return True


    def _onNextActionIsReceived(self, action, actionType, record, jobTicketEndDateAskingIsRequired, nextChiefId, dateTime):
        db = QtGui.qApp.db
        tableEventType = db.table('EventType')

        model = self.tblAPActions.model()

        orgStructureMoving = action[u'Направлен в отделение']
        hospitalBedProfileId = action[u'Профиль'] if action.hasProperty(u'Профиль') else None
        receivedQuoting = action[u'Квота']  if action.hasProperty(u'Квота') else None
        currentOrgStructureId = None
        if orgStructureMoving:
            actionTypeId = self.getIdListActionType(u'moving')
            if not actionTypeId:
                        QtGui.QMessageBox.critical(self,
                        u'Внимание!',
                        u'Не найдено подходящего действия "Движение" для Ваших специальности и подразделения',
                        QtGui.QMessageBox.Ok,
                        QtGui.QMessageBox.Ok)
            chiefId = getChiefId(orgStructureMoving) if not jobTicketEndDateAskingIsRequired else nextChiefId
            if chiefId:
                setPersonTRId = forceRef(record.value('person_id'))
                self.eventEditor.mapJournalInfoTransfer = [
                    chiefId, forceDateTime(record.value('endDate')), setPersonTRId if setPersonTRId else self.eventEditor.cmbPerson.value()
                ]
                self.eventEditor.cmbPerson.setValue(chiefId)
        else:
            actionTypeId = self.getIdListActionType(u'leaved')
            currentOrgStructureId = QtGui.qApp.currentOrgStructureId()
        if actionTypeId:
            oldBegDate = forceDateTime(record.value('endDate'))
            if not oldBegDate:
                record.setValue('endDate', toVariant(dateTime))
            record.setValue('status', toVariant(2))
            self.receivedFinanceId = forceRef(record.value('finance_id'))
            self.updateAmount()
            model.addRow(actionTypeId, actionType.amount)
            record, action = model.items()[-1]
            eventTypeId = self.eventEditor.getEventTypeId()
            if eventTypeId:
                recordET = db.getRecordEx(
                    tableEventType, [tableEventType['actionFinance']],
                    [tableEventType['deleted'].eq(0), tableEventType['id'].eq(eventTypeId)]
                )
                self.eventActionFinance = forceInt(recordET.value('actionFinance')) if recordET else None
                if self.eventActionFinance == 0:
                    record.setValue('finance_id', toVariant(self.receivedFinanceId))
            if orgStructureMoving:
                action[u'Отделение пребывания'] = orgStructureMoving
            elif currentOrgStructureId:
                typeRecord = db.getRecordEx(
                    'OrgStructure', 'type', 'id = %d AND type = 4 AND deleted = 0' % (currentOrgStructureId)
                )
                if typeRecord and (typeRecord.value('type')) == 4:
                    if action.hasProperty(u'Отделение'):
                        action[u'Отделение'] = currentOrgStructureId
            if action.hasProperty(u'Профиль') and hospitalBedProfileId:
                action[u'Профиль'] = hospitalBedProfileId
            if oldBegDate:
                record.setValue('begDate', toVariant(oldBegDate))
                record.setValue('directionDate', toVariant(oldBegDate))
            else:
                record.setValue('begDate', toVariant(dateTime))
                record.setValue('directionDate', toVariant(dateTime))
            actionTypeOfNewItem = action.getType()
            if actionTypeOfNewItem.defaultEndDate in [CActionType.dedSyncActionBegDate, CActionType.dedActionBegDate]:
                record.setValue('endDate', record.value('begDate'))
            if actionTypeOfNewItem.defaultDirectionDate == CActionType.dddActionExecDate:
                record.setValue('directionDate', record.value('endDate'))
            if u'Квота' in action._actionType._propertiesByName and receivedQuoting:
                action[u'Квота'] = receivedQuoting


    def _onNextActionIsMoving(self, action, actionType, record, jobTicketEndDateAskingIsRequired, nextChiefId, dateTime, needCutFeed):
        db = QtGui.qApp.db
        model = self.tblAPActions.model()
        eventId = forceRef(record.value('event_id')) if record else None
        orgStructureTransfer = action[u'Переведен в отделение']
        orgStructurePresence = action[u'Отделение пребывания']
        hospitalBedId = action[u'койка']
        oldBegDate = forceDateTime(record.value('endDate'))
        if not oldBegDate:
            record.setValue('endDate', toVariant(dateTime))
            reverseEndDate = None
            oldBegDate = dateTime
        else:
            reverseEndDate = oldBegDate
        record.setValue('status', toVariant(2))
        movingQuoting = action[u'Квота'] if u'Квота' in action._actionType._propertiesByName else None
        if orgStructureTransfer:
            actionTypeId = self.getIdListActionType(u'moving')
            if actionTypeId:
                chiefId = getChiefId(orgStructureTransfer) if not jobTicketEndDateAskingIsRequired else nextChiefId
                if chiefId:
                    setPersonTRId = forceRef(record.value('person_id'))
                    self.eventEditor.mapJournalInfoTransfer = [
                        chiefId, forceDateTime(record.value('endDate')), setPersonTRId if setPersonTRId else self.eventEditor.cmbPerson.value()
                    ]
                if self.checkActionByNextEventCreation():
                    self.eventEditor.eventDate = forceDate(record.value('endDate'))
                    self.eventEditor.edtEndDate.setDate(self.eventEditor.eventDate)
                    if hasattr(self.eventEditor, 'edtEndTime'):
                        self.eventEditor.edtEndTime.setTime(forceDateTime(record.value('endDate')).time())
                    self.updateAmount()
                    personId = forceRef(record.value('person_id'))
                    prevEndDate = oldBegDate
                    res = self.requestNewEvent(
                        orgStructureTransfer, chiefId if chiefId else personId, self.receivedFinanceId,
                        orgStructurePresence, prevEndDate, movingQuoting, actionTypeId,
                        [self.eventActionFinance, self.receivedFinanceId, orgStructureTransfer,
                         orgStructurePresence, prevEndDate, movingQuoting, chiefId if chiefId else personId],
                        mapJournalInfoTransfer=self.eventEditor.mapJournalInfoTransfer)
                    if not res:
                        record.setValue('endDate', toVariant(reverseEndDate))
                        record.setValue('status', toVariant(0))
                    return
                if chiefId:
                    self.eventEditor.cmbPerson.setValue(chiefId)
                self.updateAmount()
                model.addRow(actionTypeId, actionType.amount)
                record, action = model.items()[-1]
                if eventId:
                    record.setValue('event_id', toVariant(eventId))
                if self.eventActionFinance == 0:
                    record.setValue('finance_id', toVariant(self.receivedFinanceId))
                action[u'Отделение пребывания'] = orgStructureTransfer
                if orgStructurePresence:
                    action[u'Переведен из отделения'] = orgStructurePresence
                if oldBegDate:
                    record.setValue('begDate', toVariant(oldBegDate))
                else:
                    record.setValue('begDate', toVariant(dateTime))
                actionTypeOfNewItem = action.getType()
                if actionTypeOfNewItem.defaultEndDate in [CActionType.dedSyncActionBegDate, CActionType.dedActionBegDate]:
                    record.setValue('endDate', record.value('begDate'))
                if actionTypeOfNewItem.defaultDirectionDate == CActionType.dddActionExecDate:
                    record.setValue('directionDate', record.value('endDate'))
                if u'Квота' in action._actionType._propertiesByName and movingQuoting:
                    action[u'Квота'] = movingQuoting
                if hasattr(self.eventEditor, 'tabFeed') and needCutFeed:
                    cutFeed(eventId, forceDateTime(record.value('begDate')))
                    self.eventEditor.tabFeed.load(eventId)
        else:
            actionTypeId = self.getIdListActionType(u'leaved')
            if actionTypeId:
                self.updateAmount()
                model.addRow(actionTypeId, actionType.amount)
                record, action = model.items()[-1]
                if self.eventActionFinance == 0:
                    record.setValue('finance_id', toVariant(self.receivedFinanceId))
                if orgStructurePresence:
                    if u'Отделение' in action._actionType._propertiesByName:
                        action[u'Отделение'] = orgStructurePresence
                if oldBegDate:
                    record.setValue('begDate', toVariant(oldBegDate))
                    record.setValue('directionDate', toVariant(oldBegDate))
                else:
                    record.setValue('begDate', toVariant(dateTime))
                    record.setValue('directionDate', toVariant(dateTime))
                actionTypeOfNewItem = action.getType()
                if actionTypeOfNewItem.defaultEndDate in [CActionType.dedSyncActionBegDate, CActionType.dedActionBegDate]:
                    record.setValue('endDate', record.value('begDate'))
                if actionTypeOfNewItem.defaultDirectionDate == CActionType.dddActionExecDate:
                    record.setValue('directionDate', record.value('endDate'))
                if u'Квота' in action._actionType._propertiesByName and movingQuoting:
                    action[u'Квота'] = movingQuoting
                if hospitalBedId:
                    tableOSHB = db.table('OrgStructure_HospitalBed')
                    recordProfile = db.getRecordEx(
                        tableOSHB, [tableOSHB['profile_id']], [tableOSHB['id'].eq(hospitalBedId)]
                    )
                    if recordProfile:
                        profileId = forceRef(recordProfile.value('profile_id'))
                        if u'Профиль' in action._actionType._propertiesByName and profileId:
                            action[u'Профиль'] = profileId
                if hasattr(self.eventEditor, 'tabFeed'):
                    cutFeed(eventId, forceDateTime(record.value('begDate')))
                    self.eventEditor.tabFeed.load(eventId)


    def _onNextActionDurationOrAliquoticity(
            self,
            action,
            record,
            actionType,
            duration,
            aliquoticity,
            quantity,
            actionTypeId,
            directionDate,
            setPersonId,
            groupingRecords=[]):

        def _checkNewRecordAction(_duration, newRecordAction):
            if _duration == 1 and not newRecordAction:
                begDate = forceDateTime(record.value('begDate'))
                record.setValue('status', toVariant(CActionStatus.finished))
                endDate = forceDateTime(record.value('endDate'))
                if not endDate:
                    record.setValue('endDate', toVariant(begDate))
                record.setValue('person_id', toVariant(
                    QtGui.qApp.userId if (QtGui.qApp.userId and QtGui.qApp.userSpecialityId) else self.cmbAPSetPerson.value())
                )
                record.setValue('plannedEndDate', toVariant(begDate.addDays(duration - 1)))

        aliquoticity = aliquoticity or 1
        newRecordAction = False
        returnAfter = False

        noExecTimeNextDialog = True
        periodicity = self.edtAPPeriodicity.value()
        if not (aliquoticity and actionTypeId and directionDate and setPersonId):
            _checkNewRecordAction(duration, newRecordAction)
            return noExecTimeNextDialog

        lastRecord = action.getRecord()
        if lastRecord:
            begDate = forceDateTime(lastRecord.value('begDate'))
            if QtGui.qApp.userId and QtGui.qApp.userSpecialityId:
                execPersonId = QtGui.qApp.userId
            else:
                execPersonId = self.cmbAPSetPerson.value()

            if action.nomenclatureExpense:
                nomenclatureIdDict = {}
                executionPlanItem = action.executionPlanManager.currentItem
                if executionPlanItem and executionPlanItem.nomenclature and executionPlanItem.nomenclature.nomenclatureId:
                    if executionPlanItem.nomenclature.nomenclatureId:
                        nomenclatureIdDict[executionPlanItem.nomenclature.nomenclatureId] = (action.getRecord(), executionPlanItem.nomenclature.dosage)
                        force = True
                        if not action.nomenclatureExpense.stockMotionItems() or not action.nomenclatureExpense.getNomenclatureIdItem(executionPlanItem.nomenclature.nomenclatureId):
                            #nomenclatureIdDict = {}
                            #nomenclatureIdDict[executionPlanItem.nomenclature.nomenclatureId] = (action.getRecord(), executionPlanItem.nomenclature.dosage)
                            action.nomenclatureExpense.updateNomenclatureIdListToAction(nomenclatureIdDict)
                            force = False
                        if executionPlanItem.nomenclature.dosage and not executionPlanItem.executedDatetime:
                            action.nomenclatureExpense.updateNomenclatureDosageValue(
                                executionPlanItem.nomenclature.nomenclatureId,
                                executionPlanItem.nomenclature.dosage,
                                force=force
                            )
                for subrecord, subaction, subgroup in groupingRecords:
                    executionPlanItem = subaction.executionPlanManager.currentItem
                    nomenclatureIdDict[subaction.findNomenclaturePropertyValue()] = (subaction.getRecord(), executionPlanItem.nomenclature.dosage)
                action.nomenclatureExpense.updateNomenclatureIdListToAction(nomenclatureIdDict)
                orgStructureId = forceRef(record.value('orgStructure_id'))
                isControlExecWriteOffNomenclatureExpense = QtGui.qApp.controlExecutionWriteOffNomenclatureExpense()
                if isControlExecWriteOffNomenclatureExpense:
                    db = QtGui.qApp.db
                    message = u''
                    nomenclatureLine = []
                    resQntDict = {}
                    tableNomenclature = db.table('rbNomenclature')
                    for subrecord, subaction, subgroup in groupingRecords:
                        if subaction.nomenclatureExpense:
                            stockMotionItems = subaction.nomenclatureExpense.stockMotionItems()
                            for stockMotionItem in stockMotionItems:
                                price = forceDouble(stockMotionItem.value('price'))
                                oldPrice = price
                                nomenclatureId = forceRef(stockMotionItem.value('nomenclature_id'))
                                if nomenclatureId and nomenclatureId not in nomenclatureLine:
                                    qnt = forceDouble(stockMotionItem.value('qnt'))
                                    resQnt, proxyQnt, planQnt, simpleRatio = resQntDict.get(nomenclatureId, (None, None, None, 2))
                                    unitId = forceRef(stockMotionItem.value('unit_id'))
                                    stockUnitId = self.getDefaultStockUnitId(nomenclatureId)
                                    ratio = self.getRatio(nomenclatureId, stockUnitId, unitId)
                                    if ratio is not None:
                                        price = price*ratio
                                        qnt = qnt / ratio
                                    qnt = round(qnt, QtGui.qApp.numberDecimalPlacesQnt())
                                    if planQnt is None:
                                        nomenclativeRecord, dosage = nomenclatureIdDict.get(nomenclatureId, (None, 0))
                                        planQnt = subaction.nomenclatureExpense.getNomenclatureDosageToQntValue(nomenclatureId, dosage)
                                        if ratio is not None:
                                            planQnt = planQnt / ratio
                                        planQnt = round(planQnt, QtGui.qApp.numberDecimalPlacesQnt())
                                    if proxyQnt is None:
                                        proxyQnt = 0
                                        model = self.tblAPActions.model()
                                        if subgroup:
                                            for proxyItem in subgroup.items:
                                                i = subgroup._mapItem2Row.get(proxyItem, -1)
                                                if i > -1 and i != subgroup._headModelRow:
                                                    proxyQnt += proxyItem.action.findDosagePropertyValue()
                                            if ratio is not None:
                                                proxyQnt = proxyQnt / ratio
                                            proxyQnt = round(proxyQnt, QtGui.qApp.numberDecimalPlacesQnt())
                                    if proxyQnt > 0:
                                        proxyQnt = proxyQnt - qnt
                                        proxyQnt = round(proxyQnt, QtGui.qApp.numberDecimalPlacesQnt())
                                    if proxyQnt < 0:
                                        proxyQnt = 0
                                    financeId = forceRef(stockMotionItem.value('finance_id'))
                                    batch = forceString(stockMotionItem.value('batch'))
                                    shelfTime = forceDate(stockMotionItem.value('shelfTime'))
                                    shelfTime = shelfTime.toPyDate() if bool(shelfTime) else None
                                    medicalAidKindId = forceRef(stockMotionItem.value('medicalAidKind_id'))
                                    otherHaving=[u'(shelfTime>=curDate()) OR shelfTime is NULL']
                                    existsQnt = getExistsNomenclatureAmount(nomenclatureId, financeId, batch, orgStructureId=orgStructureId, unitId=stockUnitId, medicalAidKindId = medicalAidKindId, shelfTime=shelfTime, otherHaving=otherHaving, exact=True, price=price, isStockUtilization=False, precision=QtGui.qApp.numberDecimalPlacesQnt())
                                    masterId = forceRef(stockMotionItem.value('master_id'))
                                    prevQnt = round(getStockMotionItemQntEx(nomenclatureId, stockMotionId=masterId, batch=batch, financeId=financeId, clientId=self.clientId(), medicalAidKindId=medicalAidKindId, price=None, oldPrice=oldPrice, oldUnitId=unitId), QtGui.qApp.numberDecimalPlacesQnt())
                                    reservationQnt = round(getStockMotionItemQntEx(nomenclatureId, stockMotionId=None, batch=batch, financeId=financeId, clientId=self.clientId(), medicalAidKindId=medicalAidKindId, price=None, oldPrice=price, oldUnitId=stockUnitId), QtGui.qApp.numberDecimalPlacesQnt())
                                    if existsQnt < 0:
                                        existsQnt = 0
                                    if prevQnt < 0:
                                        prevQnt = 0
                                    if reservationQnt < 0:
                                        reservationQnt = 0
                                    if resQnt is None:
                                        resQnt = (existsQnt + reservationQnt + prevQnt) - qnt
                                    else:
                                        resQnt += (existsQnt + reservationQnt + prevQnt) - qnt
                                    resQntDict[nomenclatureId] = (resQnt, proxyQnt)
                                    resQnt = round(resQnt, QtGui.qApp.numberDecimalPlacesQnt())
                                    planQnt = planQnt - qnt
                                    planQnt = round(planQnt, QtGui.qApp.numberDecimalPlacesQnt())
                                    resQntDict[nomenclatureId] = (resQnt, proxyQnt, planQnt, len(forceStringEx(self.getSimpleRatio(nomenclatureId, stockUnitId, unitId))))
                            for nomenclatureIdKey, (resQntValue, proxyQntValue, planQntValue, simpleQntRatio) in resQntDict.items():
                                if resQntValue < 0 or resQntValue is None or (round(planQntValue, simpleQntRatio) != 0 and planQntValue is not None):
                                    nomenclatureLine.append(nomenclatureIdKey)
                            nomenclatureName = u''
                            if nomenclatureLine:
                                records = db.getRecordList(tableNomenclature, [tableNomenclature['name']], [tableNomenclature['id'].inlist(nomenclatureLine)], order = tableNomenclature['name'].name())
                                nomenclatureName = u','.join(forceString(recordNomenclature.value('name')) for recordNomenclature in records)
                                message += u'''Действие типа %s.\nОтсутствуют ЛСиИМН: %s!\n''' % (action._actionType.name, nomenclatureName)
                            if message:
                                if isControlExecWriteOffNomenclatureExpense == 1:
                                    button = QtGui.QMessageBox.Ok|QtGui.QMessageBox.Cancel
                                    message2 = u'Списываемого ЛСиИМН %s недостаточно на остатке подразделения. Выполнить списание?' % (nomenclatureName)
                                else:
                                    button = QtGui.QMessageBox.Cancel
                                    message2 = u'Списываемого ЛСиИМН %s недостаточно на остатке подразделения. Выполнение назначения невозможно!\n' % (nomenclatureName)
                                res = QtGui.QMessageBox().warning(None,
                                                                u'Внимание!',
                                                                message2,
                                                                button,
                                                                QtGui.QMessageBox.Cancel)
                                if res == QtGui.QMessageBox.Cancel:
                                    return
                if not self._openNomenclatureEditor(action, record, requireItems=True):
                    if action.nomenclatureExpense:
                        action.nomenclatureExpense.cancelEx()
                    return
            nextPlanDate = None
            jobTicketOrgStructureId = None
            
#            if executionPlan and not actionType.isNomenclatureExpense and nextExecutionPlanItem and not bool(nextExecutionPlanItem.date):
#                nextPlanDate, jobData = getNextDateExecutionPlan(self, jobTicketId=None, prevActionDate=begDate, executionPlan=executionPlan, lastAction=action, nextExecutionPlanItem=nextExecutionPlanItem)
#                jobTicketOrgStructureId = jobData[2] if len(jobData) >= 3 else None
#                if bool(nextPlanDate):
#                    if action and action.executionPlanManager:
#                        action.executionPlanManager.setExecutionPlan(executionPlan)
            execTimePlanManager = None
            epManagerCurrentItem = action.executionPlanManager._currentItem if (not action.getType().isNomenclatureExpense and action.executionPlanManager) else None
            if epManagerCurrentItem:
                execDateTimePlanManager = epManagerCurrentItem.getDateTime()
                if execDateTimePlanManager:
                    execTimePlanManager = execDateTimePlanManager.time()
            dialog = CExecTimeNextActionDialog(self, begDate, execPersonId, execTimePlanManager=execTimePlanManager)
            newCurrentItem = None
            newActions = []
            try:
                dialog.setCourseVisible(bool(epManagerCurrentItem))
                if dialog.exec_():
                    execTime = dialog.getExecTime()
                    execCourse = dialog.execCourse()
                    execPersonId = dialog.getExecPersonId()
                    for subrecord, subaction, subgroup in groupingRecords:
                        subaction.executionPlanManager.setCurrentItemIndex(subaction.executionPlanManager.executionPlan.items.index(subaction.executionPlanManager._currentItem))
                        nextExecutionPlanItem = subaction.executionPlanManager.getNextItem()
                        specifiedName = forceString(subrecord.value('specifiedName'))
                        subrecord.setValue('person_id', toVariant(execPersonId))
                        subrecord.setValue('begDate', toVariant(begDate))
                        subrecord.setValue('endDate', toVariant(QDateTime(begDate.date(), execTime)))
                        subrecord.setValue('status', toVariant(CActionStatus.finished))
                        if not subaction.getType().isNomenclatureExpense and execCourse > CCourseStatus.proceed:
                            if execCourse in [CCourseStatus.skipRefusalClient, CCourseStatus.finishRefusalClient]:
                                subrecord.setValue('status', QVariant(CActionStatus.refused))
                            if execCourse in [CCourseStatus.skipRefusalMO, CCourseStatus.finishRefusalMO]:
                                subrecord.setValue('status', QVariant(CActionStatus.canceled))
                            if execCourse in [CCourseStatus.skipRefusalClient, CCourseStatus.skipRefusalMO, CCourseStatus.finishRefusalClient, CCourseStatus.finishRefusalMO]:
                                subaction = self.freeJobTicketFirstCourse(subaction)
                        subrecord.setValue('periodicity', toVariant(periodicity))
                        if actionType.requiredActionSpecification:
                            subrecord.setValue('actionSpecification_id', toVariant(self.cmbActionSpecification.value()))

                        plannedEndDate = forceDateTime(subrecord.value('plannedEndDate'))
                        executionPlan = subaction.getExecutionPlan()
    #                    nextExecutionPlanItem = action.executionPlanManager.getNextItem()
                        if not subaction.getType().isNomenclatureExpense and execCourse not in [CCourseStatus.finishRefusalClient, CCourseStatus.finishRefusalMO]:
                            if executionPlan and not actionType.isNomenclatureExpense and nextExecutionPlanItem and not bool(nextExecutionPlanItem.date):
                                nextPlanDate, jobData = getNextDateExecutionPlan(self, jobTicketId=None, prevActionDate=begDate, executionPlan=executionPlan, lastAction=action, nextExecutionPlanItem=nextExecutionPlanItem)
                                jobTicketOrgStructureId = jobData[2] if len(jobData) >= 3 else None
                                if bool(nextPlanDate):
                                    if subaction and subaction.executionPlanManager:
                                        subaction.executionPlanManager.setExecutionPlan(executionPlan)
                        subaction.executionPlanManager.setCurrentItemExecuted()
                        if not nextExecutionPlanItem:
                            #if action.nomenclatureClientReservation:
                            #    action.nomenclatureClientReservation.cancel()
                            subrecord.setValue('quantity', toVariant(quantity-(1 if quantity > 0 else 0)))
                            self.onActionCurrentChanged()
                            returnAfter = True
                            continue
                        if jobTicketOrgStructureId and not forceRef(subrecord.value('orgStructure_id')):
                            subrecord.setValue('orgStructure_id', toVariant(jobTicketOrgStructureId))
                        subaction.setNomenclatureExpenseChange(subaction.saveNomenclatureExpense(subaction.nomenclatureExpensePreliminarySave, isActionNoSave = True))
                        executionPlan = subaction.getExecutionPlan()
                        if not (not subaction.getType().isNomenclatureExpense and execCourse in [CCourseStatus.finishRefusalClient, CCourseStatus.finishRefusalMO]):
                            model = self.tblAPActions.model()
                            newRecord = QtGui.qApp.db.table('Action').newRecord()
                            newRecord.setValue('plannedEndDate', toVariant(plannedEndDate))
                            newRecord.setValue('directionDate', toVariant(directionDate))
                            newRecord.setValue('begDate', toVariant(nextExecutionPlanItem.getDateTime()))
                            actionFinanceId = subaction.getFinanceId()
                            actionMedicalAidKindId = subaction.getMedicalAidKindId()
                            newAction = model.getFilledAction(newRecord, actionTypeId, actionType.amount, actionFinanceId, saveDirectionDates=True)
                            newRecord.setValue('medicalAidKind_id', toVariant(actionMedicalAidKindId))
                            newAction.setFinanceId(forceRef(newRecord.value('finance_id')))
                            newAction.setMedicalAidKindId(actionMedicalAidKindId)
                            newAction.updateByAction(subaction)
                            if nextExecutionPlanItem:
                                if newAction and newAction.executionPlanManager:
                                    newAction.executionPlanManager.setExecutionPlan(executionPlan)
                                newAction.setExecutionPlanItem(nextExecutionPlanItem)
                                newAction.executionPlanManager.bindAction(newAction)
                                if subaction.executionPlanManager.getDuration() > 0:
                                    duration = max(
                                        nextExecutionPlanItem.date.daysTo(
                                            subaction.executionPlanManager.plannedEndDate()
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
                            newAction.initPropertiesBySameAction(subaction)
                            orgStructureId = forceRef(subrecord.value('orgStructure_id'))
                            medicalAidKindId = subaction.getMedicalAidKindId()
                            #if QtGui.qApp.controlSMFinance() == 0:
                            #    newAction.initNomenclature(self.clientId(), medicalAidKindId=medicalAidKindId)
                            #    newAction.nomenclatureReservationFromAction(action, medicalAidKindId=medicalAidKindId, supplierId=orgStructureId)
                            #else:
                            newAction.initNomenclature(self.clientId(), financeId=forceRef(newRecord.value('finance_id')), medicalAidKindId=actionMedicalAidKindId)
                            newAction.nomenclatureReservationFromAction(subaction, financeId=forceRef(newRecord.value('finance_id')), medicalAidKindId=actionMedicalAidKindId, supplierId=orgStructureId)
    #                        newAction.initNomenclature(self.clientId())
    #                        newAction.nomenclatureReservationFromAction(action)
                            if newAction.getType().isNomenclatureExpense:
                                newAction.updateDosageFromExecutionPlan()
                                newAction.updateSpecifiedName()
                                noteAction = forceStringEx(subrecord.value('note'))
                                note = noteAction if noteAction else (forceStringEx(executionPlan.getNote()) if executionPlan else u'')
                                newAction.setNote(note)
                                newRecord.setValue('note', toVariant(note))
                                if executionPlan:
                                    executionPlan.setNote(note)
                            else:
                                newRecord.setValue('specifiedName', toVariant(specifiedName))
                                newAction.setSpecifiedName(specifiedName)
                            if executionPlan and not actionType.isNomenclatureExpense:
                                for property in newAction.getType()._propertiesById.itervalues():
                                    if property.isJobTicketValueType() and property.valueType.initPresetValue:
                                        prop = newAction.getPropertyById(property.id)
                                        if prop._type:
                                            prop._type.valueType.setIsExceedJobTicket(True)
                                            prop._type.valueType.setIsNearestJobTicket(True)
                                            prop._type.valueType.setDateTimeExecJob(nextExecutionPlanItem.getDateTime() if nextExecutionPlanItem else begDate)
        #                                        if jobTicketOrgStructureId:
        #                                            prop._type.valueType.setExecOrgStructureId(jobTicketOrgStructureId)
                                newAction.initPresetValues()
                            newAction.finalFillingPlannedEndDate()
                            self.updateAmount()
                            newRecord.setValue('event_id', toVariant(subrecord.value('event_id')))
                            newRecord.setValue('begDate', toVariant(
                                nextExecutionPlanItem.getDateTime() if nextExecutionPlanItem else begDate
                            ))
                            newRecord.setValue('status', toVariant(CActionStatus.started))
                            newRecord.setValue('duration', toVariant(duration))
                            newRecord.setValue('periodicity', toVariant(periodicity))
                            newRecord.setValue('aliquoticity', toVariant(aliquoticity))
                            newRecord.setValue('quantity', toVariant(quantity-(1 if quantity > 0 else 0)))
                            if not forceDate(newRecord.value('plannedEndDate')):
                                newRecord.setValue('plannedEndDate', toVariant(plannedEndDate))
                            newRecord.setValue('actionType_id', toVariant(actionTypeId))
                            newRecord.setValue('directionDate', toVariant(directionDate))
                            newRecord.setValue('setPerson_id', toVariant(setPersonId))
                            newRecord.setValue('org_id', toVariant(subrecord.value('org_id')))
                            newRecord.setValue('amount', toVariant(subrecord.value('amount')))
                            if subaction.getType().isNomenclatureExpense:
                                prevOrgStructureId = forceRef(subrecord.value('orgStructure_id'))
                                nomenclatureOrgStructureId = subaction.getType().getNomenclatureOrgStructureId()
                                newRecord.setValue('orgStructure_id', toVariant(nomenclatureOrgStructureId) if nomenclatureOrgStructureId else toVariant(prevOrgStructureId))
                            else:
                                newRecord.setValue('orgStructure_id', toVariant(jobTicketOrgStructureId) if jobTicketOrgStructureId else subrecord.value('orgStructure_id'))
                            newRecord.setValue('actionTypeGroup_id', toVariant(subrecord.value('actionTypeGroup_id')))
                            if actionType.requiredActionSpecification:
                                newRecord.setValue('actionSpecification_id', toVariant(subrecord.value('actionSpecification_id')))
                            personId = QtGui.qApp.userId  \
                                if (QtGui.qApp.userId and QtGui.qApp.userSpecialityId) \
                                else self.cmbAPSetPerson.value()
                            newRecord.setValue('person_id', toVariant(personId))
                            model.addRow(presetAction=newAction, related = False, subgroup = subgroup)
                            #noExecTimeNextDialog = False
                            newRecordAction = True
                            if action == subaction:
                                newCurrentItem = newAction.executionPlanManager._currentItem
                            else:
                                subaction._isShort = True
                                subaction.groupedNomenclature = True
                            if subgroup.groupingItem or subgroup.currentItem._record.value('group_id'):
                                newActions.append(newAction)
            finally:
                dialog.deleteLater()
        if returnAfter:
            return
        for newAction in newActions:
            newAction.executionPlanManager.groupingItem = newCurrentItem
            newAction.executionPlanManager._currentItem._record.setValue('group_id', None)
        _checkNewRecordAction(duration, newRecordAction)
        return noExecTimeNextDialog


    def _getNomenclatureDefaultUnits(self, nomenclatureId):
        if not nomenclatureId:
            return {}
        result = self._mapNomenclatureIdToUnitId.get(nomenclatureId)
        if result is None:
            record = QtGui.qApp.db.getRecord('rbNomenclature',
                                             ('defaultStockUnit_id', 'defaultClientUnit_id'),
                                             nomenclatureId
                                            )
            if record:
                defaultStockUnitId = forceRef(record.value('defaultStockUnit_id'))
                defaultClientUnitId = forceRef(record.value('defaultClientUnit_id'))
            else:
                defaultStockUnitId = defaultClientUnitId = None
            result = {
                       'defaultStockUnitId' : defaultStockUnitId,
                       'defaultClientUnitId': defaultClientUnitId
                     }
            self._mapNomenclatureIdToUnitId[nomenclatureId] = result
        return result


    def getDefaultStockUnitId(self, nomenclatureId):
        return self._getNomenclatureDefaultUnits(nomenclatureId).get('defaultStockUnitId')


    def getRatio(self, nomenclatureId, oldUnitId, newUnitId):
        if oldUnitId is None:
            oldUnitId = self.getDefaultStockUnitId(nomenclatureId)
        if newUnitId is None:
            newUnitId = self.getDefaultStockUnitId(nomenclatureId)
        if oldUnitId == newUnitId:
            return 1
        ratio = getNomenclatureUnitRatio(nomenclatureId, oldUnitId, newUnitId)
        return ratio


    def getSimpleRatio(self, nomenclatureId, oldUnitId, newUnitId):
        if oldUnitId is None:
            oldUnitId = self.getDefaultStockUnitId(nomenclatureId)
        if newUnitId is None:
            newUnitId = self.getDefaultStockUnitId(nomenclatureId)
        if oldUnitId == newUnitId:
            return 1
        ratio = getNomenclatureSimpleUnitRatio(nomenclatureId, oldUnitId, newUnitId)
        return ratio


    def freeJobTicketFirstCourse(self, action):
        if action:
            for property in action.getType()._propertiesById.itervalues():
                if property.isJobTicketValueType():
                    prop = action.getPropertyById(property.id)
                    if prop._type:
                        QtGui.qApp.setJTR(self)
                        try:
                            prop._value = None
                            prop._changed = True
                        finally:
                            QtGui.qApp.unsetJTR(self)
                        self.tblAPProps.model().reset()
        return action


    def _onNextEventAfterDirection(self):
        eventId = self.requestNewEvent(None, None, None, None, None, None, None, [],
                                       srcDate=self.eventEditor.getSrcDate(), srcNumber=self.eventEditor.getSrcNumber(),
                                       relegatePersonId=self.eventEditor.getRelegatePersonId(), relegateOrgId=self.eventEditor.tabNotes.cmbRelegateOrg.value(), isMoving=False)
        if eventId:
            db = QtGui.qApp.db
            tableEvent = db.table('Event')
            recordNext = db.getRecordEx(tableEvent,
                        [tableEvent['prevEvent_id'],tableEvent['setDate'], tableEvent['execPerson_id']],
                        [tableEvent['id'].eq(eventId), tableEvent['deleted'].eq(0)])
            prevEventId = forceRef(recordNext.value('prevEvent_id'))
            if prevEventId:
                tableEventType = db.table('EventType')
                record = db.getRecordEx(tableEvent,
                                        u'*',
                                        [tableEvent['id'].eq(prevEventId), tableEvent['deleted'].eq(0)])
                if record:
                    eventTypeId = forceRef(record.value('eventType_id'))
                    recordEventType = db.getRecordEx(tableEventType,
                                            [tableEventType['purpose_id']],
                                            [tableEventType['id'].eq(eventTypeId), tableEventType['deleted'].eq(0)])
                    execDate = forceDateTime(record.value('execDate'))
                    resultId = forceRef(record.value('result_id'))
                    execPersonId = forceRef(record.value('execPerson_id'))
                    purposeId = forceRef(recordEventType.value('purpose_id')) if recordEventType else None
                    execPersonId = forceRef(recordNext.value('execPerson_id')) if recordNext else None
                    setDate = forceDateTime(recordNext.value('setDate'))  if recordNext else None
                    isUpdateEvent = False
                    if not execPersonId and recordNext:
                        record.setValue('execPerson_id', toVariant(execPersonId))
                        isUpdateEvent = True
                    if not execDate and recordNext:
                        record.setValue('execDate', toVariant(setDate))
                        isUpdateEvent = True
                    if not resultId:
                        tableResult = db.table('rbResult')
                        cond = [tableResult['name'].like(u'динам%')]
                        if purposeId:
                            cond.append(tableResult['eventPurpose_id'].eq(purposeId))
                        recordResult = db.getRecordEx(tableResult, [tableResult['id']], cond)
                        eventResultId = forceRef(recordResult.value('id')) if recordResult else None
                        record.setValue('result_id', toVariant(eventResultId))
                        isUpdateEvent = True
                    if isUpdateEvent:
                        db.transaction()
                        try:
                            db.updateRecord(tableEvent, record)
                            db.commit()
                        except:
                            db.rollback()
                    isUpdateDiagnosis = False
                    isDiagnosis = False
                    tableDiagnosis = db.table('Diagnosis')
                    tableDiagnostic = db.table('Diagnostic')
                    tableDiagnosticResult = db.table('rbDiagnosticResult')
                    cond = [tableDiagnosticResult['name'].like(u'динам%')]
                    if purposeId:
                        cond.append(tableDiagnosticResult['eventPurpose_id'].eq(purposeId))
                    recordDiagnosticResult = db.getRecordEx(tableDiagnosticResult, [tableDiagnosticResult['id']], cond)
                    diagnosticResultId = forceRef(recordDiagnosticResult.value('id')) if recordDiagnosticResult else None
                    query = db.query('SELECT getEventDiagnosis(%d)'%prevEventId)
                    if query.next():
                        diagnosisId = forceRef(query.record().value(0))
                        if diagnosisId:
                            recordDiagnosis = db.getRecordEx(tableDiagnosis, '*', tableDiagnosis['id'].eq(diagnosisId))
                            if recordDiagnosis:
                                MKB = forceString(recordDiagnosis.value('MKB'))
                                if not MKB:
                                    recordDiagnosis.setValue('MKB', toVariant(u' Z00.0'))
                                    isUpdateDiagnosis = True
                                    db.transaction()
                                    try:
                                        db.updateRecord(tableDiagnosis, recordDiagnosis)
                                        db.commit()
                                    except:
                                        db.rollback()
                                else:
                                    isDiagnosis = True
                                diagnosisId = forceRef(recordDiagnosis.value('id'))
                                recordDiagnostic = db.getRecordEx(tableDiagnostic, '*', [tableDiagnostic['event_id'].eq(prevEventId),
                                                                                         tableDiagnostic['diagnosis_id'].eq(diagnosisId),
                                                                                         tableDiagnostic['deleted'].eq(0)])
                                if recordDiagnostic:
                                    resultId = forceRef(recordDiagnostic.value('result_id'))
                                    if not resultId:
                                        recordDiagnostic.setValue('result_id', toVariant(diagnosticResultId))
                                        db.transaction()
                                        try:
                                            db.updateRecord(tableDiagnostic, recordDiagnostic)
                                            db.commit()
                                        except:
                                            db.rollback()
                    if not isDiagnosis and not isUpdateDiagnosis:
                        recordDiagnostic = self.setDiagnosDirection(diagnosticResultId, prevEventId)
                        db.transaction()
                        try:
                            db.insertOrUpdate(tableDiagnostic, recordDiagnostic)
                            db.commit()
                        except:
                            db.rollback()
                    execDateToAction = None
                    planningAction = False
                    tableAction = db.table('Action')
                    tableActionType = db.table('ActionType')
                    table = tableAction.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
                    table = table.innerJoin(tableEvent, db.joinAnd([tableEvent['id'].eq(tableAction['event_id']), tableEvent['deleted'].eq(0)]))
                    table = table.innerJoin(tableEventType, db.joinAnd([tableEventType['id'].eq(tableEvent['eventType_id']), tableEventType['deleted'].eq(0)]))
                    cond = [tableAction['event_id'].eq(prevEventId),
                            tableAction['deleted'].eq(0),
                            tableActionType['deleted'].eq(0),
                            db.joinOr([tableActionType['flatCode'].like(u'recoveryDirection%'),
                                       tableActionType['flatCode'].like(u'inspectionDirection%'),
                                       tableActionType['flatCode'].like(u'researchDirection%'),
                                       tableActionType['flatCode'].like(u'consultationDirection%'),
                                       db.joinAnd([tableActionType['flatCode'].like(u'planning%'), tableEventType['code'].like(u'УО')])])
                            ]
                    cols = [tableAction['id'],
                            tableAction['person_id'],
                            tableAction['endDate'],
                            tableAction['status'],
                            tableActionType['flatCode'],
                            tableEventType['code']
                            ]
                    record = db.getRecordEx(table, cols, cond, tableAction['id'].name())
                    if record:
                        actionId = forceRef(record.value('id'))
                        if actionId:
                            isUpdateAction = False
                            endDate = forceDateTime(record.value('endDate'))
                            personId = forceRef(record.value('person_id'))
                            status = forceInt(record.value('status'))
                            flatCode = forceStringEx(record.value('flatCode'))
                            code = forceStringEx(record.value('code'))
                            planningAction = bool(u'planning'.lower() in flatCode and code == u'УО')
                            recordAction = db.getRecordEx(tableAction, u'*', [tableAction['id'].eq(actionId), tableAction['deleted'].eq(0)])
                            if not endDate:
                                recordAction.setValue('endDate', toVariant(QDateTime.currentDateTime() if planningAction else setDate))
                                endDate = forceDateTime(recordAction.value('endDate'))
                                isUpdateAction = True
                            if not personId:
                                recordAction.setValue('person_id', toVariant(execPersonId))
                                isUpdateAction = True
                            if planningAction:
                                if endDate:
                                    execDateToAction = endDate
                                else:
                                    execDateToAction = QDateTime.currentDateTime()
                            if planningAction and (CActionStatus.refused or CActionStatus.canceled):
                                action = CAction(record=recordAction)
                                if action and u'Дата аннулирования' in action._actionType._propertiesByName:
                                    execDateToAction = action[u'Дата аннулирования']
                            elif status != CActionStatus.finished:
                                recordAction.setValue('status', toVariant(CActionStatus.finished))
                                isUpdateAction = True
                            if isUpdateAction:
                                db.transaction()
                                try:
                                    db.updateRecord(tableAction, recordAction)
                                    db.commit()
                                except:
                                    db.rollback()
                            if planningAction and execDateToAction and prevEventId:
                                recordPrevEvent = db.getRecordEx(tableEvent, u'*', [tableEvent['id'].eq(prevEventId), tableEvent['deleted'].eq(0)])
                                if recordPrevEvent:
                                    recordPrevEvent.setValue('execDate', toVariant(execDateToAction))
                                    db.transaction()
                                    try:
                                        db.updateRecord(tableEvent, recordPrevEvent)
                                        db.commit()
                                    except:
                                        db.rollback()


    def setDiagnosDirection(self, diagnosticResultId, eventId):
        db = QtGui.qApp.db
        tableEvent = db.table('Event')
        tableDiagnostic = db.table('Diagnostic')
        record = db.getRecordEx(tableEvent,
                                u'*',
                                [tableEvent['id'].eq(eventId), tableEvent['deleted'].eq(0)])
        execDate = forceDateTime(record.value('execDate')) if record else None
        execPersonId = forceRef(record.value('execPerson_id')) if record else None
        clientId = forceRef(record.value('client_id')) if record else None
        MKB           = u' Z00.0'
        MKBEx         = U''
        TNMS          = u''
        morphologyMKB = u''
        diagnosisTypeId = forceRef(QtGui.qApp.db.translate('rbDiagnosisType', 'code', '1', 'id'))
        specialityId = forceRef(QtGui.qApp.db.translate('Person', 'id', execPersonId, 'speciality_id'))
        recordDiagnostic = tableDiagnostic.newRecord()
        recordDiagnostic.setValue('diagnosisType_id', toVariant(diagnosisTypeId))
        recordDiagnostic.setValue('speciality_id', toVariant(specialityId))
        recordDiagnostic.setValue('person_id', toVariant(execPersonId))
        recordDiagnostic.setValue('setDate', toVariant(execDate))
        recordDiagnostic.setValue('endDate', toVariant(execDate))
        diagnosisId = None
        characterId = None
        diagnosisId, characterId = getDiagnosisId2(
                execDate,
                execPersonId,
                clientId,
                diagnosisTypeId,
                MKB,
                MKBEx,
                None,
                None,
                None,
                diagnosisId,
                forceRef(recordDiagnostic.value('id')),
                QtGui.qApp.defaultIsManualSwitchDiagnosis(),
                forceBool(recordDiagnostic.value('handleDiagnosis')),
                TNMS=TNMS,
                morphologyMKB=morphologyMKB
                )
        recordDiagnostic.setValue('diagnosis_id', toVariant(diagnosisId))
        recordDiagnostic.setValue('TNMS', toVariant(TNMS))
        recordDiagnostic.setValue('character_id', toVariant(characterId))
        recordDiagnostic.setValue('event_id', toVariant(eventId))
        recordDiagnostic.setValue('result_id', toVariant(diagnosticResultId))
        return recordDiagnostic


    def isTrailerActionType(self, actionTypeId = None):
        if not actionTypeId:
            model = self.tblAPActions.model()
            items = model.items()
            row = self.tblAPActions.currentIndex().row()
            if 0<= row <len(items):
                record, action = items[row]
                if record:
                    actionTypeId = forceRef(record.value('actionType_id'))
        return bool(CActionTypeCache.getById(actionTypeId).getExpansionIdList()) and self.cmbAPStatus.value() in [CActionStatus.started, CActionStatus.appointed, CActionStatus.wait, CActionStatus.withoutResult]


    @pyqtSignature('')
    def on_btnNextAction_clicked(self):
        db = QtGui.qApp.db
        model = self.tblAPActions.model()
        items = model.items()
        row = self.tblAPActions.currentIndex().row()

#        if not (0 <= row < len(items)):
#            return

        record, action = items[row]

        flatCode = action.actionType().flatCode

        # ГИС ОМС. ФЕРЗЛ. Создание/обновление НИЛ
        if u'createNIL' in flatCode:
            from Registry.Ferzl_service import Ferzl_service
            service = Ferzl_service()
            result_dict = service.createUpdateNil(self.clientId(), self.eventEditor.eventSetDateTime, self.eventEditor.eventDate, action)
            if result_dict['result']:
                prop = action.getPropertyByShortName('nLr')
                if prop:
                    prop.setValue(result_dict['elements']['nLr'])
                    self.btnNextAction.setText(u'Обновить НИЛ')
            return

        if flatCode.lower() in ['recipeLLO78'.lower()] and unicode(self.btnNextAction.text()) == u'Зарегистрировать рецепт' and (0 <= row < len(items)):
            clientId = self.clientId()
            tablePolicy = QtGui.qApp.db.table('ClientPolicy')
            tablePolicyKind = QtGui.qApp.db.table('rbPolicyKind').alias('policyKind')
            tablePolicyType = QtGui.qApp.db.table('rbPolicyType').alias('policyType')
            cols = [tablePolicy['serial'],
                    tablePolicy['number'],
                    tablePolicyKind['code'].alias('kindCode')
                   ]
            tablePolicy = tablePolicy.innerJoin(tablePolicyKind, tablePolicyKind['id'].eq(tablePolicy['policyKind_id']))
            tablePolicy = tablePolicy.innerJoin(tablePolicyType, tablePolicyType['id'].eq(tablePolicy['policyType_id']))
            actionBegDate = forceDate(self.edtAPBegDate.date())
            if not actionBegDate:
                QtGui.QMessageBox.critical( self, u'', u'Не задана дата начала действия полиса пациента', QtGui.QMessageBox.Close)
                return
            policyList = QtGui.qApp.db.getRecordList(tablePolicy,
                                                     cols,
                                                     db.joinAnd([tablePolicy['client_id'].eq(clientId),
                                                                 tablePolicy['deleted'].eq(0),
                                                                 tablePolicy['begDate'].dateLe(actionBegDate),
                                                                 db.joinOr([tablePolicy['endDate'].dateGe(actionBegDate),
                                                                            tablePolicy['endDate'].isNull()]
                                                                          ),
                                                                 tablePolicyType['code'].inlist(['1', '2'])
                                                                ]
                                                               ),
                                                     'ClientPolicy.modifyDatetime', 1
                                                    )
            policyNumber = u''
            policySeria = u''
            if policyList and len(policyList) == 1:
                for policyRecord in policyList:
                    policySeria = forceString(policyRecord.value('serial'))
                    policyNumber = forceString(policyRecord.value('number'))
                    policyKindCode = forceString(policyRecord.value('kindCode'))
            else:
                QtGui.QMessageBox.critical( self, u'', u'Проверьте, что дата начала действия попадает в период обслуживания полиса', QtGui.QMessageBox.Close)
                return
            if not policySeria and policyKindCode == '3': # новый полис без серии, но в ЛЛО необходимо отправлять серию 'ЕП' в таком случае
                policySeria = u'ЕП'
            clientInfo = []
            clientInfo.append(forceString(QtGui.qApp.db.translate('Client', 'id', clientId, 'lastName')))
            clientInfo.append(forceString(QtGui.qApp.db.translate('Client', 'id', clientId, 'firstName')))
            clientInfo.append(forceString(QtGui.qApp.db.translate('Client', 'id', clientId, 'patrName')))
            clientInfo.append(formatSNILS(forceString(QtGui.qApp.db.translate('Client', 'id', clientId, 'SNILS'))))
            dr = forceDate(QtGui.qApp.db.translate('Client', 'id', clientId, 'birthDate')).toString('yyyy-MM-dd') + 'T00:00:00'
            clientInfo.append(dr)
            clientInfo.append(policySeria)
            clientInfo.append(policyNumber)
            clientInfo.append(clientId)
            clientInfo.append(forceString(QtGui.qApp.db.translate('Client', 'id', clientId, 'sex')))
            LLO78LoginDialog = CLLO78LoginDialog(self, clientInfo)
            if LLO78LoginDialog.exec_():
                ckatlList = LLO78LoginDialog.ckatlList
                servCode  = LLO78LoginDialog.servCode
                login     = LLO78LoginDialog.login
                password  = LLO78LoginDialog.password
                NPPCode   = LLO78LoginDialog.NPP
                LLO78RegistryDialog = CLLO78RecipeRegistryDialog(self, ckatlList, servCode,  login, password, clientInfo, NPPCode)
                if LLO78RegistryDialog.exec_():
                    # порядок присваивания важен
                    action[u'Штрих-код']                 = LLO78RegistryDialog.actionProps[0]
                    action[u'Серия']                     = LLO78RegistryDialog.actionProps[1]
                    action[u'Номер']                     = LLO78RegistryDialog.actionProps[2]
                    action[u'Наименование ЛС в рецепте'] = LLO78RegistryDialog.actionProps[3]
                    action[u'Тип выписки']               = LLO78RegistryDialog.actionProps[4]
                    action[u'Количество']                = LLO78RegistryDialog.actionProps[5]
                    action[u'Способ применения']         = LLO78RegistryDialog.actionProps[6]
                    action[u'Срок действия рецепта']     = LLO78RegistryDialog.actionProps[7]
                    action[u'Наличие протокола ВК']      = LLO78RegistryDialog.actionProps[8]
                    action[u'Льгота пациента']           = LLO78RegistryDialog.actionProps[9]
                    action[u'Выписано']                  = LLO78RegistryDialog.actionProps[10]
                    if action.actionType().hasProperty(u'D.T.d.'):
                        action[u'D.T.d.']                = LLO78RegistryDialog.actionProps[11]
                    actionMKB                            = LLO78RegistryDialog.actionProps[12]
                    self.cmbAPMKB.setText(actionMKB)
                    if not self.cmbAPMKB.isVisible():
                        self.lblAPMKBText.setVisible(False)
                    return
            return

        model = self.tblAPActions.model()
        items = model.items()
        row = self.tblAPActions.currentIndex().row()
        if 0<= row <len(items):
            record, action = items[row]
            if record:
                actionTypeId = forceRef(record.value('actionType_id'))
                prevActionId = forceRef(record.value('prevAction_id'))
                if prevActionId:
                    return
                actionTypeExpansionIdList = CActionTypeCache.getById(actionTypeId).getExpansionIdList()
                if actionTypeExpansionIdList and self.cmbAPStatus.value() in [CActionStatus.started, CActionStatus.appointed, CActionStatus.wait, CActionStatus.withoutResult]:
                    if actionTypeExpansionIdList:
                        expansionId = None
                        if len(actionTypeExpansionIdList) > 1:
                            try:
                                dialog = CActionTypeDialogTableModel(self, actionTypeExpansionIdList)
                                if dialog.exec_():
                                    expansionId = dialog.currentItemId()
                            finally:
                                dialog.deleteLater()
                        else:
                            expansionId = actionTypeExpansionIdList[0]
                        if expansionId:
                            actionTypeExpansion = CActionTypeCache.getById(expansionId) if expansionId else None
                            actionType = CActionTypeCache.getById(actionTypeId) if actionTypeId else None
                            if actionTypeExpansion and actionType:
                                if actionType.class_ != actionTypeExpansion.class_:
                                    if hasattr(self.eventEditor, ['tabStatus', 'tabDiagnostic', 'tabCure', 'tabMisc'][actionTypeExpansion.class_]):
                                        model = [self.eventEditor.tabStatus.modelAPActions, self.eventEditor.tabDiagnostic.modelAPActions, self.eventEditor.tabCure.modelAPActions, self.eventEditor.tabMisc.modelAPActions][actionTypeExpansion.class_]
                                    else:
                                        return
#                                actionId = forceRef(record.value('id'))
                                model.addRow(expansionId, actionTypeExpansion.amount)
                                newRecord, newAction = model.items()[-1]
                                newRecord.setValue('event_id', toVariant(record.value('event_id')))
                                newRecord.setValue('id', toVariant(None))
                                newRecord.setValue('idx', toVariant(forceInt(record.value('idx')) + 1))
                                newRecord.setValue('prevAction_id',  toVariant(None))
                                record.setValue('status', toVariant(CActionStatus.wait))
                                if self.eventEditor.trailerIdx:
                                    if not action.trailerIdx:
                                        self.eventEditor.trailerIdx += 2
                                        action.trailerIdx = self.eventEditor.trailerIdx
                                else:
                                    self.eventEditor.trailerIdx += 1
                                    action.trailerIdx = self.eventEditor.trailerIdx
                                newAction.trailerIdx = action.trailerIdx + 1
                                model.reset()
                                if actionType.class_ != actionTypeExpansion.class_:
                                    tabIndex = self.eventEditor.tabWidget.indexOf([self.eventEditor.tabStatus, self.eventEditor.tabDiagnostic, self.eventEditor.tabCure, self.eventEditor.tabMisc][actionTypeExpansion.class_])
                                    if tabIndex >= 0:
                                        self.eventEditor.tabWidget.setCurrentIndex(tabIndex)
                                        if hasattr(self.eventEditor, ['tabStatus', 'tabDiagnostic', 'tabCure', 'tabMisc'][actionTypeExpansion.class_]):
                                            tableAPActions = [self.eventEditor.tabStatus.tblAPActions, self.eventEditor.tabDiagnostic.tblAPActions, self.eventEditor.tabCure.tblAPActions, self.eventEditor.tabMisc.tblAPActions][actionTypeExpansion.class_]
                                            model = [self.eventEditor.tabStatus.modelAPActions, self.eventEditor.tabDiagnostic.modelAPActions, self.eventEditor.tabCure.modelAPActions, self.eventEditor.tabMisc.modelAPActions][actionTypeExpansion.class_]
                                            tableAPActions.setCurrentIndex(model.index(len(model.items())-1, 0))
                        return
        nextChiefId = None
        isNextEventAfterDirection = False
        relegateOrgId = self.eventEditor.tabVoucher.cmbDirectionOrgs.value() if getEventTypeForm(self.eventEditor.eventTypeId) == u'072' else self.eventEditor.tabNotes.cmbRelegateOrg.value()
        if relegateOrgId and (relegateOrgId != QtGui.qApp.currentOrgId()
            and self.cmbAPStatus.currentIndex() in (CActionStatus.started, CActionStatus.wait, CActionStatus.withoutResult, CActionStatus.appointed)):
            model = self.tblAPActions.model()
            items = model.items()
            row = self.tblAPActions.currentIndex().row()
            if 0<= row <len(items):
                record, action = items[row]
                actionTypeId = forceRef(record.value('actionType_id')) if record else None
                actionType = CActionTypeCache.getById(actionTypeId) if actionTypeId else None
                flatCode = actionType.flatCode.lower()
                if ('recoveryDirection'.lower() in flatCode
                    or u'inspectionDirection'.lower() in flatCode
                    or u'researchDirection'.lower() in flatCode
                    or u'consultationDirection'.lower() in flatCode
                    or (u'planning'.lower() in flatCode and getEventCode(self.eventEditor.eventTypeId) == u'УО')
                    ):
                    self._onNextEventAfterDirection()
                    isNextEventAfterDirection = True
        if self.cmbAPStatus.value() == CActionStatus.canceled:
            currentDateTime = QDateTime.currentDateTime()
            table = db.table('vrbPersonWithSpeciality')
            personId = QtGui.qApp.userId if (QtGui.qApp.userId and QtGui.qApp.userSpecialityId) else self.cmbAPSetPerson.value()
            record = db.getRecordEx(table, [table['name']], [table['id'].eq(personId)]) if personId else None
            personName = forceString(record.value('name')) if record else ''
            self.edtAPNote.setText(u'Отменить: %s %s'%(currentDateTime.toString('dd-MM-yyyy hh:mm'), personName))
        if isNextEventAfterDirection:
            pass
        else:
            model = self.tblAPActions.model()
            items = model.items()
            row = self.tblAPActions.currentIndex().row()

            if not (0 <= row < len(items)):
                return
            
            group = items._mapProxyRow2Group[row]
            groupingRecords = []
            anyGroupingCancelled = True
            if group.groupingItem or isinstance(group, CExecutionPlanProxyModelGroup) and group.currentItem and forceInt(group.currentItem._record.value('group_id')):
                headRow = 0 if group.expanded else -1
                if forceInt(group.items[headRow].action._record.value('status')) == CActionStatus.canceled:
                    anyGroupingCancelled = False
                for subgroup in items._groups:
                    if isinstance(subgroup, CExecutionPlanProxyModelGroup):
                        subHeadRow = 0 if subgroup.expanded else -1
                        if subgroup.isGrouped() and group.isGrouped() and subgroup.groupingItem == subgroup.currentItem and subgroup.currentItem == group.groupingItem:
                            record, action = subgroup.items[subHeadRow].record, subgroup.items[subHeadRow].action
                            groupingRecords.append((subgroup.items[subHeadRow].record, subgroup.items[subHeadRow].action, subgroup))
                        elif subgroup.isGroupedAndSaved() and group.isGroupedAndSaved() and subgroup.currentItem._record.value('id') == subgroup.currentItem._record.value('group_id') and \
                                subgroup.currentItem._record.value('id') == group.currentItem._record.value('group_id'):
                            record, action = subgroup.items[subHeadRow].record, subgroup.items[subHeadRow].action
                            groupingRecords.append((subgroup.items[subHeadRow].record, subgroup.items[subHeadRow].action, subgroup))
                        elif (group.isGrouped() and subgroup.isGrouped() and subgroup.groupingItem == group.groupingItem) \
                                or (group.isGroupedAndSaved() and subgroup.isGroupedAndSaved() and \
                                forceInt(group.currentItem._record.value('group_id')) == forceInt(subgroup.currentItem._record.value('group_id'))):
                            groupingRecords.append((subgroup.items[subHeadRow].record, subgroup.items[subHeadRow].action, subgroup))
                            if forceInt(subgroup.items[subHeadRow].action._record.value('status')) == CActionStatus.canceled:
                                anyGroupingCancelled = False
            else:
                record, action = items[row]
                groupingRecords.append((record, action, group))

            needCutFeed = True
            actionTypeId = forceRef(record.value('actionType_id')) if record else None
            actionType = CActionTypeCache.getById(actionTypeId) if actionTypeId else None

            if any([actionType and i in actionType.flatCode.lower() for i in ['moving', 'received', 'inspectpigeonhole']]):
                jobTicketEndDateAskingIsRequired = forceBool(
                    QtGui.qApp.preferences.appPrefs.get('jobTicketEndDateAskingIsRequired', QVariant(True))
                )
            else:
                jobTicketEndDateAskingIsRequired = False

            if jobTicketEndDateAskingIsRequired:
                dlg = CInputCutFeedDialog(action, actionType, record, self.eventEditor.cmbPerson.value(), self)
                if dlg.exec_():
                    currentDateTime = dlg.dateTime()
                    record.setValue('person_id', dlg.person())
                    nextChiefId = dlg.execPerson()
                    needCutFeed = dlg.cutFeed()
                else:
                    return
            else:
                currentDateTime = QDateTime.currentDateTime()
            noExecTimeNextDialog = True
            directionDate = forceDateTime(record.value('directionDate')) if record else None
            setPersonId = forceRef(record.value('setPerson_id')) if record else None
            duration = self.edtAPDuration.value() or 1
            aliquoticity = self.edtAPAliquoticity.value() or 1
            quantity = self.edtAPQuantity.value()
            if u'inspectPigeonHole'.lower() in actionType.flatCode.lower():
                self._onNextActionIsInspectPigeonHole(record, currentDateTime)

            elif u'received' in actionType.flatCode.lower():
                self._onNextActionIsReceived(
                    action, actionType, record, jobTicketEndDateAskingIsRequired, nextChiefId, currentDateTime
                )

            elif u'moving' in actionType.flatCode.lower():
                self._onNextActionIsMoving(
                    action, actionType, record, jobTicketEndDateAskingIsRequired, nextChiefId, currentDateTime, needCutFeed
                )

            elif action and action.actionType().isDoesNotInvolveExecutionCourse and self.cmbAPStatus.value() != CActionStatus.canceled:
                noExecTimeNextDialog = self._onExecActionIsDoesNotInvolveExecutionCourse(action, record, currentDateTime)

            elif (action and
                        action.getExecutionPlan() and
                        action.executionPlanManager.hasItemsToDo() and
                        self.cmbAPStatus.value() != CActionStatus.canceled and
                        anyGroupingCancelled):
                noExecTimeNextDialog = self._onNextActionDurationOrAliquoticity(
                    action, record, actionType, duration, aliquoticity, quantity, actionTypeId, directionDate, setPersonId, groupingRecords
                )
            if noExecTimeNextDialog and not action.actionType().isDoesNotInvolveExecutionCourse:
                row = (row + 1) if (row + 1) <= model.rowCount()-1 else model.rowCount()-1
                self.tblAPActions.setCurrentIndex(model.index(row, 0))
                self.edtAPBegDate.setFocus(Qt.OtherFocusReason)

            row = self.tblAPActions.currentIndex().row()
            self.onActionCurrentChanged()
            actionsSummaryRow = self.eventEditor.translate2ActionsSummaryRow(model, row)
            if actionsSummaryRow is not None:
                self.eventEditor.onActionChanged(actionsSummaryRow)


    def getCurrentTimeAction(self, actionDate):
        currentDateTime = QDateTime.currentDateTime()
        if currentDateTime == actionDate:
            currentTime = currentDateTime.time()
            return currentTime.addSecs(60)
        else:
            return currentDateTime.time()


    def clientId(self):
        return self.eventEditor.clientId


    def requestNewEvent(self, orgStructureTransfer, personId, financeId, orgStructurePresence, actionDate, movingQuoting,
                        actionTypeId, actionByNewEvent, actionListToNewEvent=[], endDateTime=None, result=None, mapJournalInfoTransfer=[],
                        srcDate=QDate(), srcNumber=u'', relegatePersonId=None, relegateOrgId=None, isMoving=True):
        from Events.CreateEvent import requestNewEvent
        clientId = self.clientId()
        self.eventEditor.done(1)
        eventId = self.eventEditor._id
        if not self.eventEditor.isDirty() and clientId:
            params = {}
            params['widget'] = self.eventEditor
            params['clientId'] = clientId
            params['flagHospitalization'] = True
            params['actionTypeId'] = actionTypeId
            params['valueProperties'] = [orgStructureTransfer]
            if isMoving:
                params['eventTypeFilterHospitalization'] = 2
            params['dateTime'] = actionDate
            params['personId'] = personId
            params['planningEventId'] = eventId
            params['diagnos'] = None
            params['financeId'] = financeId
            params['protocolQuoteId'] = movingQuoting
            params['actionByNewEvent'] = actionByNewEvent
            params['externalId'] = self.eventEditor.getExternalId()
            params['relegateOrgId'] = self.eventEditor.tabVoucher.cmbDirectionOrgs.value() if getEventTypeForm(self.eventEditor.eventTypeId) == u'072' else relegateOrgId  # self.eventEditor.tabNotes.cmbRelegateOrg.value()
            params['srcNumber'] = srcNumber
            params['srcDate'] = srcDate
            params['relegatePersonId'] = relegatePersonId
            params['order'] = self.eventEditor.cmbOrder.currentIndex()
            params['moving'] = True
            params['actionListToNewEvent'] = actionListToNewEvent
            params['endDateTime'] = endDateTime
            params['prevEventId'] = eventId
            params['result'] = result
            params['mapJournalInfoTransfer'] = mapJournalInfoTransfer
            for action in actionListToNewEvent:
                action.checkModifyDate = False
            return requestNewEvent(params)
        return None


    def updatePropTable(self, action):
        self.tblAPProps.model().setAction(action, self.eventEditor.clientId, self.eventEditor.clientSex, self.eventEditor.clientAge, self.eventEditor.eventTypeId)
        self.tblAPProps.resizeRowsToContents()


    def onActionDataChanged(self, name, value):
        model = self.tblAPActions.model()
        items = model.items()
        row = self.tblAPActions.currentIndex().row()
        if 0<=row<len(items):
            #record = items[row][0]
            record, action = items[row]
            record.setValue(name, toVariant(value))
            actionTypeId = forceRef(record.value('actionType_id')) if record else None
            actionType = CActionTypeCache.getById(actionTypeId) if actionTypeId else None
            if (u'moving' in actionType.flatCode.lower()
                or u'received' in actionType.flatCode.lower()
                or u'inspectPigeonHole'.lower() in actionType.flatCode.lower()
                or u'recoveryDirection'.lower() in actionType.flatCode.lower()
                or u'inspectionDirection'.lower() in actionType.flatCode.lower()
                or u'researchDirection'.lower() in actionType.flatCode.lower()
                or u'consultationDirection'.lower() in actionType.flatCode.lower()
                or (u'planning'.lower() in actionType.flatCode.lower() and getEventCode(self.eventEditor.eventTypeId) == u'УО')
                or u'createnil'.lower() in actionType.flatCode.lower()
                ):
                self.onCurrentActionAdd(actionType.flatCode, action)
            else:
                if (action and
                        ((action.getExecutionPlan() and
                        action.executionPlanManager.hasItemsToDo()) or actionType.isDoesNotInvolveExecutionCourse) and
                        self.cmbAPStatus.value() != CActionStatus.canceled):
                    if actionType.isDoesNotInvolveExecutionCourse and self.cmbAPStatus.value() == CActionStatus.finished:
                        self.btnNextAction.setText(u'Действие')
                        self.btnNextAction.setEnabled(False)
                    else:
                        self.btnNextAction.setText(u'Выполнить')
                        isEnable = self.cmbAPStatus.value() != CActionStatus.refused
                        if action.getType().isNomenclatureExpense:
                            isEnable = isEnable and self.isEnabledNomenclatureExpense(action)
                        self.btnNextAction.setEnabled(isEnable)
                else:
                    self.btnNextAction.setText(u'Действие')
                    self.btnNextAction.setEnabled(self.isTrailerActionType(actionTypeId))
                    if actionType and 'recipeLLO78'.lower() in actionType.flatCode.lower():
                        self.btnNextAction.setText(u'Зарегистрировать рецепт')
                        self.btnNextAction.setEnabled(True)
                if name in ('duration',) and not action.getType().isNomenclatureExpense:
                    duration = value
                    if record and forceInt(record.value('duration')) != duration:
                        record.setValue('duration', toVariant(duration))
                elif name in ('periodicity',) and not action.getType().isNomenclatureExpense:
                    periodicity = self.edtAPPeriodicity.value()
                    if record and forceInt(record.value('periodicity')) != periodicity:
                        record.setValue('periodicity', toVariant(periodicity))
                elif name in ('aliquoticity',) and not action.getType().isNomenclatureExpense:
                    aliquoticity = self.edtAPAliquoticity.value()
                    if record and forceInt(record.value('aliquoticity')) != aliquoticity:
                        record.setValue('aliquoticity', toVariant(aliquoticity))
                elif name in ('quantity',) and not action.getType().isNomenclatureExpense:
                    quantity = self.edtAPQuantity.value()
                    if record and forceInt(record.value('quantity')) != quantity:
                        record.setValue('quantity', toVariant(quantity))
            if not action.getType().isNomenclatureExpense:
                self.btnPlanNextAction.setEnabled(bool(self.edtAPQuantity.value()))
            else:
                self.btnPlanNextAction.setEnabled(self.edtAPDuration.value() > 0)
            if actionType.defaultSetPersonInEvent == CActionType.dspExecPerson and name in ('person_id'):
                self.cmbAPSetPerson.setValue(self.cmbAPPerson.value())
            if actionType.defaultPlannedEndDate == CActionType.dpedBegDatePlusAmount and name in ('amount', 'begDate'):
                begDate = self.edtAPBegDate.date()
                amountValue = int(self.edtAPAmount.value())
                date = begDate.addDays(amountValue-1) if begDate and amountValue else QDate()
                self.edtAPPlannedEndDate.setDate(date)
            elif actionType.defaultPlannedEndDate == CActionType.dpedBegDatePlusDuration and name in ('duration', 'begDate'):
                begDate = self.edtAPBegDate.date()
                durationValue = self.edtAPDuration.value()
                date = begDate.addDays(durationValue-1) if begDate and durationValue else QDate()
                self.edtAPPlannedEndDate.setDate(date)
            if actionType.isNomenclatureExpense and action.nomenclatureExpense and name in ('amount'):
                action.nomenclatureExpense._actionAmount = value
                action.nomenclatureExpense.set(actionType=actionType)


    def updateAmount(self):
        model = self.tblAPActions.model()
        row = self.tblAPActions.currentIndex().row()
        model.updateActionAmount(row)


    def loadPrevAction(self, type):
        model = self.tblAPActions.model()
        items = model.items()
        row = self.tblAPActions.currentIndex().row()
        if QtGui.qApp.userHasRight(urCopyPrevAction) and 0<=row<len(items):
                action = items[row][1]
                prevActionId = self.eventEditor.getPrevActionId(action, type)
                if prevActionId:
                    action.updateByActionId(prevActionId)
                    self.tblAPProps.model().reset()
                    self.tblAPProps.resizeRowsToContents()
                    model.updateActionAmount(row)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelAPActions_currentChanged(self, current, previous):
        self.onActionCurrentChanged(previous)
        # self.tblAPProps.updatePropertiesTable(current, previous)


    def popupMenuAboutToShow(self):
        model = self.tblAPActions.model()
        row = self.tblAPActions.currentIndex().row()
        if 0<=row<model.rowCount()-1:
            group = self.modelAPActions._mapProxyRow2Group[row]
            if not group.expanded:
                record, action = group.firstItem
            else:
                record, action = model._items[row]
            actionTypeId = forceRef(record.value('actionType_id'))
            actionType = CActionTypeCache.getById(actionTypeId) if actionTypeId else None
            self.actAPDuplicateAction.setEnabled(bool(actionType.duplication))
            self.actRefreshAction.setEnabled(bool(action.getId()))
            actionType = CActionTypeCache.getById(actionTypeId)
            self.actAPAddRelatedAction.setEnabled(bool(actionType.getRelatedActionTypes()))
            isReplicateAvailable = not (
                u'moving' in actionType.flatCode.lower() or 
                u'received' in actionType.flatCode.lower() or 
                u'leaved' in actionType.flatCode.lower())
            self.actAPReplicateAction.setEnabled(isReplicateAvailable)


    def popupMenuPropertyAboutToShow(self):
        model = self.tblAPProps.model()
        row = self.tblAPProps.currentIndex().row()
        if 0 <= row < model.rowCount():
            actionPropertyType = model.getPropertyType(row)
            if model.readOnly or (model.action and model.action.isLocked()):
                self.actPropertyEditorAmbCard.setEnabled(False)
            elif model.hasCommonPropertyChangingRight(row):
                self.actPropertyEditorAmbCard.setEnabled(actionPropertyType.typeName in ['Text', 'Constructor'])
            else:
                self.actPropertyEditorAmbCard.setEnabled(False)
        else:
            self.actPropertyEditorAmbCard.setEnabled(False)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_modelAPActions_dataChanged(self, topLeft, bottomRight):
        topLeftRow = topLeft.row()
        bottomRightRow = bottomRight.row()
        if topLeftRow<=self.tblAPActions.currentIndex().row()<=bottomRightRow:
            self.onActionCurrentChanged()


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_modelAPActions_personChanged(self, topLeft, bottomRight):
#        print u"Человек сменился\n"
        pass


    @pyqtSignature('int')
    def on_modelAPActions_amountChanged(self, row):
        if row == self.tblAPActions.currentIndex().row():
            model = self.modelAPActions
            record = model._items[row][0]
            actionTypeId = forceRef(record.value('actionType_id'))
            amount = forceDouble(record.value('amount'))
            personId = forceRef(record.value('person_id'))
            financeId = forceRef(record.value('finance_id'))
            contractId = forceRef(record.value('contract_id'))
            self.edtAPAmount.setValue(amount)
            uet = amount*self.eventEditor.getUet(actionTypeId, personId, financeId, contractId)
            self.edtAPUet.setValue(uet)
            self.onActionDataChanged('uet', uet)
            self.emit(SIGNAL('actionUetChanged()'))


    def findPrevAction(self, actionBegDate):
        model = self.tblAPActions.model()
        found = [None, None, None]
        for item in model._items:
            record, action = item
            actionTypeId = forceRef(record.value('actionType_id'))
            actionType = CActionTypeCache.getById(actionTypeId) if actionTypeId else None
            if u'moving' in actionType.flatCode.lower():
                if action[u'Переведен в отделение']:
                    endDate = forceDateTime(record.value('endDate'))
                    if endDate and endDate <= actionBegDate:
                        if found:
                           if endDate > found[2]:
                                found = [record, action, endDate]
                        else:
                            found = [record, action, endDate]
        return found[0]


    def findAllAfterCurrent(self, actionBegDate):
        model = self.tblAPActions.model()
        found = []
        for item in model._items:
            record, action = item
            begDate = forceDateTime(record.value('begDate'))
            if begDate and begDate >= actionBegDate:
                found.append(action)
        return found


    def actAPActionSplitEventChecker(self):
        if not self.eventEditor.mesRequired:
            return False
        model = self.tblAPActions.model()
        row = self.tblAPActions.currentIndex().row()
        if 0<=row<model.rowCount()-1:
            record = model._items[row][0]
            action = model._items[row][1]
            actionTypeId = forceRef(record.value('actionType_id'))
            actionType = CActionTypeCache.getById(actionTypeId) if actionTypeId else None
            if u'moving' in actionType.flatCode.lower():
                if action[u'Переведен из отделения']:
                    return True
        return False


    @pyqtSignature('')
    def on_actAPActionSplitEvent_triggered(self):
        if self.isReadOnly():
            return
        if QtGui.QMessageBox.question(self,
            u'Внимание!',
            u'Выполнить перенос действий в новое событие?',
            QtGui.QMessageBox.No|QtGui.QMessageBox.Yes,
            QtGui.QMessageBox.No) != QtGui.QMessageBox.Yes:
                return
        resultId = forceRef(QtGui.qApp.db.translate('rbResult', 'federalCode', '104', 'id'))
        model = self.tblAPActions.model()
        row = self.tblAPActions.currentIndex().row()
        if 0<=row<model.rowCount()-1:
            from F003.F003Dialog import CF003Dialog
            if type(self.eventEditor) == CF003Dialog and not  self.eventEditor.getExecDateTime().isValid():
                result = True
                showTime = getEventShowTime(self.eventEditor.eventTypeId)
                if showTime:
                    endDate = QDateTime(self.eventEditor.edtEndDate.date(), self.eventEditor.edtEndTime.time())
                else:
                    endDate = self.eventEditor.edtEndDate.date()
                result = result and (len(self.eventEditor.modelFinalDiagnostics.items())>0 or self.eventEditor.checkInputMessage(u'диагноз', False, self.eventEditor.tblFinalDiagnostics))
                #WTF? какое дело ActionPage до МЭСа?
                if self.eventEditor.mesRequired:
                    result = result and self.eventEditor.tabMes.checkMesAndSpecification()
                    result = result and (self.eventEditor.tabMes.chechMesDuration() or self.eventEditor.checkValueMessage(u'Длительность события должна попадать в интервал минимальной и максимальной длительности по требованию к МЭС', True, self.eventEditor.edtBegDate))
                    result = result and self.eventEditor.checkDiagnosticsMKBForMes(self.eventEditor.tblFinalDiagnostics, self.eventEditor.tabMes.cmbMes.value())
                result = result and self.eventEditor.checkDiagnosticsDataEntered(endDate)
                if not resultId:
                    result = result and (self.cmbResult.value() or self.checkInputMessage(u'результат', False, self.cmbResult))
                if not result:
                    return
            group = self.modelAPActions._mapProxyRow2Group[row]
            if not group.expanded:
                record, action = group.firstItem
            else:
                record, action = model._items[row]
            actionTypeId = forceRef(record.value('actionType_id'))
            actionType = CActionTypeCache.getById(actionTypeId) if actionTypeId else None
            if u'moving' in actionType.flatCode.lower():
                if action[u'Переведен из отделения']:
                    begDate = forceDateTime(record.value('begDate'))
                    prevActionRecord = self.findPrevAction(begDate)
                    if prevActionRecord:
                        personId = forceRef(record.value('person_id'))
                        prevActionEndDate = forceDateTime(prevActionRecord.value('endDate'))
                        movingQuoting = action[u'Квота'] if u'Квота' in action._actionType._propertiesByName else None
                        actions = self.findAllAfterCurrent(begDate)
                        if hasattr(self.eventEditor, 'tabNotes'):
                            self.eventEditor.tabNotes.chkIsClosed.setChecked(0)
                        eventId = self.requestNewEvent(None, personId, None, None, prevActionEndDate, movingQuoting, actionTypeId, [], actions, self.eventEditor.getExecDateTime())
                        if eventId:
                            record = self.eventEditor.getRecord()
                            record.setValue('execDate', toVariant(prevActionEndDate))
                            if resultId:
                                record.setValue('result_id', toVariant(resultId))
                            QtGui.qApp.db.transaction()
                            try:
                                QtGui.qApp.db.insertOrUpdate('Event', record)
                                QtGui.qApp.db.commit()
                            except:
                                QtGui.qApp.db.rollback()


    def createCopyAction(self, actionId):
        self.setCopyAction(CAction.getActionById(actionId))


    def setCopyAction(self, action):
        self.copyAction = action
        self.actAPPasteProperties.setEnabled(bool(self.copyAction))


    def copyPasteAboutToShowChecker(self):
        enabled = False
        model = self.tblAPActions.model()
        currentIndex = self.tblAPActions.currentIndex()
        if currentIndex and currentIndex.isValid():
            row = currentIndex.row()
            enabled = bool(0 <= row < (model.rowCount()-1))
        return enabled


    def pasteAboutToShowChecker(self):
        return bool(self.copyAction) and self.copyPasteAboutToShowChecker()


    @pyqtSignature('')
    def on_actAPCopyProperties_triggered(self):
        if self.isReadOnly():
            return
        model = self.tblAPActions.model()
        row = self.tblAPActions.currentIndex().row()
        if 0 <= row < (model.rowCount()-1):
            group = self.modelAPActions._mapProxyRow2Group[row]
            if not group.expanded:
                record, action = group.firstItem
            else:
                record, action = model._items[row]
            self.setCopyAction(action)


    @pyqtSignature('')
    def on_actAPPasteProperties_triggered(self):
        if self.isReadOnly():
            return
        if self.copyAction:
            model = self.tblAPActions.model()
            currentIndex = self.tblAPActions.currentIndex()
            if currentIndex and currentIndex.isValid():
                row = currentIndex.row()
                if 0 <= row < (model.rowCount()-1):
                    group = self.modelAPActions._mapProxyRow2Group[row]
                    if not group.expanded:
                        record, action = group.firstItem
                    else:
                        record, action = model._items[row]
                    clientSex = self.eventEditor.clientSex
                    clientAge = self.eventEditor.clientAge
                    canCopyPropertyList = action.updateByAction(self.copyAction, clientSex=clientSex, clientAge=clientAge)
                    canCopyPropertyIdList = []
                    for canCopyProperty in canCopyPropertyList:
                        if canCopyProperty and canCopyProperty.type().id not in canCopyPropertyIdList and canCopyProperty.type().applicable(clientSex, clientAge):
                            canCopyPropertyIdList.append(canCopyProperty.type().id)
                    propertyList = self.copyAction.getPropertiesById()
                    noCanCopyPropertyList = [val for key, val in propertyList.items() if (key not in canCopyPropertyIdList and val.type().applicable(clientSex, clientAge))]
                    self.modelAPActionProperties.emitDataChanged()
                    self.tblAPProps.model().reset()
                    self.tblAPActions.setCurrentIndex(currentIndex)
                    if noCanCopyPropertyList:
                        dialog = CPropertiesDialog(self)
                        try:
                            dialog.setProperties(self.copyAction, noCanCopyPropertyList, clientSex, clientAge)
                            dialog.exec_()
                        finally:
                            dialog.deleteLater()


    @pyqtSignature('')
    def on_actAPAddLikeAction_triggered(self):
        if self.isReadOnly():
            return
        model = self.tblAPActions.model()
        row = self.tblAPActions.currentIndex().row()
        if 0<=row<model.rowCount()-1:
            group = self.modelAPActions._mapProxyRow2Group[row]
            if not group.expanded:
                record = group.firstItem[0]
            else:
                record = model._items[row][0]
            actionTypeId = forceRef(record.value('actionType_id'))
            index = model.index(model.rowCount()-1, 0)
            if model.setData(index, toVariant(actionTypeId), related = False):
                self.tblAPActions.setCurrentIndex(index)

    
    @pyqtSignature('')
    def on_actAPAddRelatedAction_triggered(self):
        row = self.tblAPActions.currentIndex().row()
        group = self.modelAPActions._mapProxyRow2Group[row]
        if not group.expanded:
            record, action = group.firstItem
        else:
            record, action = self.tblAPActions.model()._items[row]
        actionTypeId = forceRef(record.value('actionType_id'))
        actionTypes = CActionTypeCache.getById(actionTypeId).getRelatedActionTypes()
        if actionTypes:
            dlg = CAddRelatedAction(self, actionTypes.keys())
            if dlg.exec_():
                result = dlg.getSelectedList()
                group = self.modelAPActions._mapProxyRow2Group[row]
                if not group.expanded:
                    self.modelAPActions.touchGrouping(row)
                for actionType in result:
                    self.modelAPActions.setData(self.modelAPActions._actionModel.index(self.modelAPActions._actionModel.rowCount()-1, 0), actionType, group, related = False)
        else:
            QtGui.QMessageBox.warning(self,
                                    u'Внимание!',
                                    u'Нет подчинённых типов действий!',
                                    QtGui.QMessageBox.Ok,
                                    QtGui.QMessageBox.Ok)
                        

    @pyqtSignature('')
    def on_actAPDuplicateAction_triggered(self):
        if self.isReadOnly():
            return
        model = self.tblAPActions.model()
        row = self.tblAPActions.currentIndex().row()
        if 0<=row<model.rowCount()-1:
            group = self.modelAPActions._mapProxyRow2Group[row]
            if not group.expanded:
                record, action = group.firstItem
            else:
                record, action = model._items[row]
            actionTypeId = forceRef(record.value('actionType_id'))
            index = model.index(model.rowCount()-1, 0)
            if model.setData(index, toVariant(actionTypeId), related = False):
                newRecord, newAction = model._items[index.row()]
                MKB = action.getRecord().value('MKB')
                newAction.getRecord().setValue('MKB', MKB)
                self.cmbAPMKB.setText(forceString(MKB))
                newAction.updateByAction(action)
                self.tblAPActions.setCurrentIndex(index)


    @pyqtSignature('')
    def on_actRefreshAction_triggered(self):
        if self.isReadOnly():
            return
        model = self.tblAPActions.model()
        row = self.tblAPActions.currentIndex().row()
        if 0 <= row < model.rowCount() - 1:
            group = self.modelAPActions._mapProxyRow2Group[row]
            if not group.expanded:
                record, action = group.firstItem
            else:
                record, action = model._items[row]
            actionTypeId = forceRef(record.value('actionType_id'))
            actionId = forceRef(record.value('id'))
            actionType = CActionTypeCache.getById(actionTypeId)

            db = QtGui.qApp.db
            table = db.table('Action')
            tableActionProperty = db.table('ActionProperty')
            record = db.getRecord(table, '*', actionId)

            APRecords = db.getRecordList(tableActionProperty, '*',
                                         [tableActionProperty['action_id'].eq(actionId),
                                          tableActionProperty['deleted'].eq(0)])
            dictValuesTable = {}
            dictProperties = {}
            dictValues = {}
            for propertyRecord in APRecords:
                propertyTypeId = forceRef(propertyRecord.value('type_id'))
                if actionType.propertyTypeIdPresent(propertyTypeId):
                    tableName = actionType.getPropertyTypeById(propertyTypeId).tableName
                    dictValuesTable.setdefault(tableName, []).append(forceRef(propertyRecord.value('id')))
                    dictProperties.setdefault(actionId, []).append(propertyRecord)
            for key in dictValuesTable.keys():
                valueTable = db.table(key)
                valueRecords = db.getRecordList(valueTable, '*', valueTable['id'].inlist(dictValuesTable[key]))
                for rec in valueRecords:
                    dictValues.setdefault(forceRef(rec.value('id')), []).append(rec)

            propertyRecords = dictProperties.get(actionId, [])
            valDict = dict()
            for prop in propertyRecords:
                valDict[forceRef(prop.value('id'))] = dictValues.get(forceRef(prop.value('id')), [])
            action = CAction(actionType=actionType, record=record, propertyRecords=propertyRecords, valueRecords=valDict)
            model._actionModel.items()[row]._data = CActionRecordItem(action.getRecord(), action)
            self.onActionCurrentChanged()
            self._onActionChanged()


    @pyqtSignature('')
    def on_actAPReplicateAction_triggered(self):
        if self.isReadOnly():
            return
        model = self.tblAPActions.model()
        row = self.tblAPActions.currentIndex().row()
        if 0<=row<model.rowCount()-1:
            group = self.modelAPActions._mapProxyRow2Group[row]
            if not group.expanded:
                action = group.firstItem[1]
            else:
                action = model._items[row][1]
#WFT?
# диалог НЕ должен создавать/изменять Actions
# он должен ввести что-то, а код для копирования должен быть здесь
            dlg = CActionReplicateDialog(self, action, self.eventEditor)
            dlg.exec_()
            for action in dlg.getResult():
                actionTypeId = action._actionType.id
                index = model.index(model.rowCount()-1, 0)
                model.setData(index, toVariant(actionTypeId), presetAction=action, related = False)


    @pyqtSignature('')
    def on_actAPActionsAdd_triggered(self):
        if self.isReadOnly():
            return
        orgStructureId = QtGui.qApp.currentOrgStructureId()
        eventFinanceId = self.eventEditor.eventFinanceId
        financeCode = CFinanceType.getCode(eventFinanceId)
        existsActionTypesList = []
        for item in self.modelAPActions.items():
            existsActionTypesList.append(forceRef(item[0].value('actionType_id')))
        actionTypes = selectActionTypes(self,
                                self.eventEditor,
                                [self.modelAPActions.actionTypeClass],
                                 orgStructureId,
                                 # self.eventEditor.getExecPersonId(),
                                 self.eventEditor.getEventTypeId(),
                                 self.eventEditor.getContractId(),
                                 self.eventEditor.getMesId(),
                                 financeCode in (CFinanceType.VMI, CFinanceType.cash),
                                 self.eventEditor._id,
                                 existsActionTypesList,
                                 visibleTblSelected=True,
                                 contractTariffCache=self.eventEditor.contractTariffCache, 
                                 clientMesInfo=self.eventEditor.getClientMesInfo(),
                                 eventDate=self.eventEditor.eventDate if self.eventEditor.eventDate else self.eventEditor.eventSetDateTime
                               )
        model = self.tblAPActions.model()
        isEventCSGRequired = getEventCSGRequired(self.eventEditor.eventTypeId)
        labGroup = set()
        hasAlfaLabActions = False
        referralActionTypeId = forceRef(QtGui.qApp.db.translate('ActionType', 'flatCode', 'referralLisLab', 'id'))
        for item in model.items():
            record, action = item
            actionType = action.actionType()
            if actionType.flatCode == 'referralLisLab':
                labGroup.add((pyDate(forceDate(action.getDirectionDate())), action[u'Группа забора'], action.getId()))
        for actionTypeId, action, csgRecord in actionTypes:
            if 'alfalabgroup_' in action.actionType().flatCode:
                hasAlfaLabActions = True
                if (pyDate(forceDate(action.getDirectionDate())), action.actionType().flatCode, action.getPrescriptionId()) not in labGroup:
                    labGroup.add((pyDate(forceDate(action.getDirectionDate())), action.actionType().flatCode, action.getPrescriptionId()))
                    index = model.index(model.rowCount() - 1, 0)
                    model.setData(index, toVariant(referralActionTypeId))
                    self.tblAPActions.setCurrentIndex(index)
                    record, referralAction = model.items()[model.rowCount() - 2]
                    record.setValue('directionDate', forceDateTime(action.getDirectionDate()))
                    record.setValue('begDate', forceDateTime(action.getDirectionDate()))
                    referralAction[u'Группа забора'] = action.actionType().flatCode
                    self._onActionChanged()
            index = model.index(model.rowCount()-1, 0)
            model.setData(index, toVariant(actionTypeId), presetAction=action)
            if isEventCSGRequired:
                self.cmbCSG.addActionToCSG(action.getRecord(), csgRecord)
                self.cmbCSG.setItems()
                self.updateCmbCSG()
            self._onActionChanged()
        if hasAlfaLabActions:
            self.tblAPActions.sortByReferrals()


    @pyqtSignature('')
    def on_actAPPrintAllActions_triggered(self):
        dialog = CPrintActionsListDialog(self, self.eventEditor)
        try:
            if dialog.exec_():
                applyMultiTemplateList(self, dialog.templateIdAndDataList, addPageBreaks=dialog.addPageBreaks)
        finally:
            dialog.deleteLater()
    
    
    @pyqtSignature('')
    def on_actAPGroupSign_triggered(self):
        row = self.tblAPActions.currentIndex().row()
        items = self.tblAPActions.model().items()
        record, action = items[row]
        dialog = CActionGroupSignDialog(self, self.btnAPAttachedFiles, action)
        dialog.setEventEditor(self.eventEditor)
        dialog.exec_()


    @pyqtSignature('QDate')
    def on_edtAPDirectionDate_dateChanged(self, date):
        self.edtAPDirectionTime.setEnabled(bool(date))
        time = self.edtAPDirectionTime.time() if date and self.edtAPDirectionTime.isVisible() else QTime()
        self.onActionDataChanged('directionDate', QDateTime(date, time))
        row = self.tblAPActions.currentIndex().row()
        model = self.tblAPActions.model()
        action = model.items()[row][1]
        if action:
            defaultPlannedEndDate = action.getType().defaultPlannedEndDate
            if defaultPlannedEndDate == CActionType.dpedNextDay:
                plannedEndDate = date.addDays(1)
                self.edtAPPlannedEndDate.setDate(plannedEndDate)
            elif defaultPlannedEndDate == CActionType.dpedNextWorkDay:
                plannedEndDate = addWorkDays(date, 1, wpFiveDays)
                self.edtAPPlannedEndDate.setDate(plannedEndDate)


    @pyqtSignature('QString')
    def on_cmbAPMKB_textChanged(self, value):
        if value[-1:] == '.':
            value = value[:-1]
        self.cmbAPMorphologyMKB.setMKBFilter(self.cmbAPMorphologyMKB.getMKBFilter(unicode(value)))
        self.cmbAPMKBExSubclass.setMKB(unicode(value))
        self.onActionDataChanged('MKB', value)
        self.updateLblAPMKBText()


    @pyqtSignature('')
    def on_cmbAPMKBExSubclass_editingFinished(self):
        self.onActionDataChanged('exSubclassMKB', self.cmbAPMKBExSubclass.getValue())
        self.updateLblAPMKBText()


    def updateLblAPMKBText(self):
        diagName = None
        exSubClassDiagName = ''
        valueMKB = self.cmbAPMKB.text()
        valueExSubClass = self.cmbAPMKBExSubclass.getValue() if self.cmbAPMKBExSubclass._value else ''

        if valueMKB:
            diagName = getMKBName(forceString(valueMKB))

        if valueExSubClass:
            if self.cacheExSubClassMKBNames.has_key(valueExSubClass):
                exSubClassDiagName = self.cacheExSubClassMKBNames[valueExSubClass]
            else:
                exSubClassDiagName = getExSubclassItemLastName(forceStringEx(valueExSubClass), forceStringEx(valueMKB)) if valueExSubClass else ''
                self.cacheExSubClassMKBNames[valueExSubClass] = exSubClassDiagName

        if diagName:
            self.lblAPMKBText.setText(u', '.join([diagName, exSubClassDiagName]) if exSubClassDiagName else diagName)
        else:
            self.lblAPMKBText.clear()


    def on_lblAPMKBText_click(self, event):
        carrier = QMimeData()
        carrier.setText(unicode(self.lblAPMKBText.text()))
        QtGui.qApp.clipboard().setMimeData(carrier)


    def on_cmbAPMKB_editingFinished(self):
        if self.focusWidget() != self.cmbAPMKB: #if not self.cmbAPMKB.underMouse() or
            if not self.isCmbAPMKBTextChanged:
                value = self.cmbAPMKB.text()
                if value[-1:] == '.':
                    value = value[:-1]
                if value and len(value) >= 3 and self.eventEditor and hasattr(self.eventEditor, 'checkDiagnosis'):
                    self.isCmbAPMKBTextChanged = True
                    acceptable = self.eventEditor.checkDiagnosis(unicode(value))
                    if not acceptable:
                        self.cmbAPMKB.setText(u'')
                        CDialogBase(self).setFocusToWidget(self.cmbAPMKB)
        self.isCmbAPMKBTextChanged = False


    @pyqtSignature('QString')
    def on_cmbAPMorphologyMKB_textChanged(self, value):
        self.onActionDataChanged('morphologyMKB', value)


    @pyqtSignature('QTime')
    def on_edtAPDirectionTime_timeChanged(self, time):
        date = self.edtAPDirectionDate.date()
        self.onActionDataChanged('directionDate', QDateTime(date, time if date else QTime()))


    @pyqtSignature('bool')
    def on_chkAPIsUrgent_toggled(self, checked):
        self.onActionDataChanged('isUrgent', checked)


    @pyqtSignature('QDate')
    def on_edtAPPlannedEndDate_dateChanged(self, date):
        self.edtAPPlannedEndTime.setEnabled(bool(date))
        time = self.edtAPPlannedEndTime.time() if date and self.edtAPPlannedEndTime.isVisible() else QTime()
        self.onActionDataChanged('plannedEndDate', QDateTime(date, time))


    @pyqtSignature('QTime')
    def on_edtAPPlannedEndTime_timeChanged(self, time):
        date = self.edtAPPlannedEndDate.date()
        self.onActionDataChanged('plannedEndDate', QDateTime(date, time if date else QTime()))


    @pyqtSignature('int')
    def on_cmbAPSetPerson_currentIndexChanged(self, index):
        self.onActionDataChanged('setPerson_id', self.cmbAPSetPerson.value())


    @pyqtSignature('int')
    def on_cmbAPOrg_currentIndexChanged(self, index):
        self.onActionDataChanged('org_id', self.cmbAPOrg.value())


    @pyqtSignature('')
    def on_btnAPSelectOrg_clicked(self):
        orgId = selectOrganisation(self, self.cmbAPOrg.value(), False)
        self.cmbAPOrg.updateModel()
        if orgId:
            self.cmbAPOrg.setValue(orgId)


    @pyqtSignature('QDate')
    def on_edtAPBegDate_dateChanged(self, date):
        self.edtAPBegTime.setEnabled(bool(date))
        time = self.edtAPBegTime.time() if date and self.edtAPBegTime.isVisible() else QTime()
        self.onActionDataChanged('begDate', QDateTime(date, time))
        self.updateAmount()
        self.cmbAPMKB.setFilter('''IF(MKB.endDate IS NOT NULL, MKB.endDate >= %s, 1)'''%(QtGui.qApp.db.formatDate(self.edtAPBegDate.date())))
        defaultEndDate = self.defaultEndDate
        if defaultEndDate == CActionType.dedSyncActionBegDate:
            if date and self.edtAPEndDate.date() != self.edtAPBegDate.date():
                self.edtAPEndDate.setDate(date)


    @pyqtSignature('QTime')
    def on_edtAPBegTime_timeChanged(self, time):
        date = self.edtAPBegDate.date()
        self.onActionDataChanged('begDate', QDateTime(date, time if date else QTime()))
        defaultEndDate = self.defaultEndDate
        if defaultEndDate == CActionType.dedSyncActionBegDate:
            if date and self.edtAPEndTime.time() != self.edtAPBegTime.time():
                self.edtAPEndTime.setTime(time)


    def checkDateTimeTOCurrentDateTime(self, isDate):
        if self.edtAPEndDate.date():
            model = self.tblAPActions.model()
            items = model.items()
            row = self.tblAPActions.currentIndex().row()
            if 0<=row<len(items):
                record, action = items[row]
                if record:
                    actionTypeId = forceRef(record.value('actionType_id'))
                    if actionTypeId and actionTypeId in self.eventEditor.actionTypeHBIdList:
                        time = self.edtAPEndTime.time()
                        if self.edtAPEndTime.isVisible() and bool(self.edtAPEndTime.time()) and self.edtAPEndTime.time().isValid():
                            date = QDateTime(self.edtAPEndDate.date(), time)
                            curDate = QDateTime.currentDateTime()
                        else:
                            date = self.edtAPEndDate.date()
                            curDate = QDate.currentDate()
                        if date > curDate:
                            return CDialogBase(self).checkValueMessage(u'Дата окончания действия %s не может быть больше текущей даты %s' % (forceString(date), forceString(curDate)), True, self.tblAPActions, row, 0, self.edtAPEndDate if isDate else self.edtAPEndTime)
        return True


    @pyqtSignature('QDate')
    def on_edtAPEndDate_dateChanged(self, date):
        if not self.checkDateTimeTOCurrentDateTime(True):
            return
        eventEditor = self.eventEditor
        defaultDirectionDate = self.defaultDirectionDate
        eventSetDate = eventEditor.eventSetDateTime.date() if eventEditor and eventEditor.eventSetDateTime else None
        begDate = eventEditor.eventSetDateTime
        if defaultDirectionDate == CActionType.dddActionExecDate:
            if date:
                if date < eventSetDate:
                    directionDate = eventSetDate
                    begDate = QDate()
                else:
                    directionDate = date
                    begDate = date
            else:
                directionDate = eventSetDate
            self.edtAPBegDate.setDate(begDate.date() if type(begDate) == QDateTime else begDate)
            self.edtAPDirectionDate.setDate(directionDate)
        else:
            if date and eventSetDate and date < eventSetDate:
                self.edtAPBegDate.setDate(QDate())
                self.edtAPBegTime.setTime(QTime())
                self.edtAPDirectionDate.setDate(QDate())
                self.edtAPDirectionTime.setTime(QTime())
            elif date and eventSetDate and date >= eventSetDate:
                if not self.edtAPDirectionDate.date():
                    self.edtAPDirectionDate.setDate(eventSetDate)
                if not self.edtAPBegDate.date():
                    self.edtAPBegDate.setDate(eventSetDate)
        self.edtAPEndTime.setEnabled(bool(date))
        time = self.edtAPEndTime.time() if date and self.edtAPEndTime.isVisible() else QTime()
        self.onActionDataChanged('endDate', QDateTime(date, time))
        self.updateAmount()
        if date and self.cmbAPStatus.value() != CActionStatus.withoutResult:
            self.cmbAPStatus.setValue(CActionStatus.finished)
            if self.cmbAPStatus.value() == CActionStatus.finished:
                self.freeJobTicket(QDateTime(self.edtAPEndDate.date(), self.edtAPEndTime.time()) if self.edtAPEndTime.isVisible() else self.edtAPEndDate.date())
        else:
            if self.cmbAPStatus.value() == CActionStatus.finished:
                self.cmbAPStatus.setValue(CActionStatus.canceled)
        self._onActionChanged()
        if not self.cmbAPPerson.value() and not self.edtAPEndDate.date().isNull():
            self.setUserExecPerson()


    def setUserExecPerson(self):
        model = self.tblAPActions.model()
        items = model.items()
        row = self.tblAPActions.currentIndex().row()
        record, action = items[row]
        actionTypeId = forceRef(record.value('actionType_id')) if record else None
        actionType = CActionTypeCache.getById(actionTypeId) if actionTypeId else None
        if actionType:
            if actionType.defaultPersonInEvent == CActionType.dpUserExecPerson:
                if QtGui.qApp.userId and QtGui.qApp.userSpecialityId:
                    self.cmbAPPerson.setValue(QtGui.qApp.userId)


    def _onActionChanged(self):
        model = self.tblAPActions.model()
        row = self.tblAPActions.currentIndex().row()
        actionsSummaryRowRow = self.eventEditor.translate2ActionsSummaryRow(model, row)
        if actionsSummaryRowRow is not None:
            self.eventEditor.onActionChanged(actionsSummaryRowRow)


    @pyqtSignature('QTime')
    def on_edtAPEndTime_timeChanged(self, time):
        if not self.checkDateTimeTOCurrentDateTime(False):
            return
        date = self.edtAPEndDate.date()
        self.onActionDataChanged('endDate', QDateTime(date, time if date else QTime()))
        defaultDirectionDate = self.defaultDirectionDate
        if defaultDirectionDate == CActionType.dddActionExecDate:
            if date and self.edtAPDirectionTime.time() != self.edtAPEndTime.time():
                self.edtAPDirectionTime.setTime(time)
        self._onActionChanged()

#       TODO: с временем события по закрытию действия отложим пока.
#        if self.edtAPEndTime.isVisible() and bool(time) and time.isValid():
#            model = self.tblAPActions.model()
#            items = model.items()
#            row = self.tblAPActions.currentIndex().row()
#            if 0 <= row < len(items):
#                record, action = items[row]
#                actionType = action.getType()
#                if actionType and actionType.closeEvent:
#                    self.eventEditor.setEndTime(time)


    @pyqtSignature('int')
    def on_cmbAPStatus_currentIndexChanged(self, index):
        actionStatus = self.cmbAPStatus.value()
        self.onActionDataChanged('status', actionStatus)
        if actionStatus in (CActionStatus.finished, CActionStatus.withoutResult):
            if self.edtAPEndDate.date().isNull():
                now = QDateTime.currentDateTime()
                self.edtAPEndDate.setDate(now.date())
                if self.edtAPEndTime.isVisible():
                    self.edtAPEndTime.setTime(now.time())
                self._onActionChanged()
            if actionStatus == CActionStatus.finished \
               and not self.cmbAPPerson.value() \
               and not self.edtAPEndDate.date().isNull():
                self.setUserExecPerson()
        elif actionStatus in (CActionStatus.canceled, CActionStatus.refused):
            self.edtAPEndDate.setDate(QDate())
            self.edtAPEndTime.setTime(QTime())
            if QtGui.qApp.userId and QtGui.qApp.userSpecialityId:
                self.cmbAPPerson.setValue(QtGui.qApp.userId)
            else:
                self.cmbAPPerson.setValue(self.cmbAPSetPerson.value())

        else:
            self.edtAPEndDate.setDate(QDate())
            self.edtAPEndTime.setTime(QTime())


    def freeJobTicket(self, endDate):
        model = self.tblAPActions.model()
        items = model.items()
        row = self.tblAPActions.currentIndex().row()
        if 0<=row<len(items):
            record, action = items[row]
            if action:
                jobTicketIdList = []
                for property in action.getType()._propertiesById.itervalues():
                    if property.isJobTicketValueType():
                        jobTicketId = action[property.name]
                        if jobTicketId and jobTicketId not in jobTicketIdList:
                            jobTicketIdList.append(jobTicketId)
                            db = QtGui.qApp.db
                            tableJobTicket = db.table('Job_Ticket')
                            cond = [tableJobTicket['id'].eq(jobTicketId),
                                    tableJobTicket['deleted'].eq(0)
                                    ]
                            if self.edtAPEndTime.isVisible():
                                cond.append(tableJobTicket['datetime'].ge(endDate))
                            else:
                                cond.append(tableJobTicket['datetime'].dateGe(endDate))
                            records = db.getRecordList(tableJobTicket, '*', cond)
                            for record in records:
                                datetime = forceDateTime(record.value('datetime')) if self.edtAPEndTime.isVisible() else forceDate(record.value('datetime'))
                                if datetime > endDate:
                                    action[property.name] = None
                self.tblAPProps.model().reset()


    @pyqtSignature('int')
    def on_edtAPDuration_valueChanged(self, value):
        self.onActionDataChanged('duration', value)
        record, action = self.tblAPActions.model().items()[self.tblAPActions.currentIndex().row()]
        if action and not action.getType().isDoesNotInvolveExecutionCourse:
            canEdit = not action.isLocked() if action else True
            canEditIsExecutionPlan = not bool(action.getExecutionPlan() and action.executionPlanManager.hasItemsToDo())
            self.edtAPDirectionDate.setEnabled(bool(not value > 0) and canEdit)
            self.edtAPDirectionTime.setEnabled(bool(not value > 0) and canEdit)
            self.cmbAPSetPerson.setEnabled(bool(not value > 0) and canEdit)
            self.edtAPPlannedEndDate.setEnabled(bool(not value > 0) and canEdit and canEditIsExecutionPlan)
            self.edtAPPlannedEndTime.setEnabled(bool(not value > 0) and canEdit and canEditIsExecutionPlan)
            self.edtAPBegDate.setEnabled(bool(not value > 0) and canEdit)
            self.edtAPBegTime.setEnabled(bool(not value > 0) and canEdit)
            self.edtAPEndDate.setEnabled(bool(not value > 0) and canEdit)
            self.edtAPEndTime.setEnabled(bool(not value > 0) and canEdit)
        if action and action.getType().isDoesNotInvolveExecutionCourse and action.nomenclatureExpense:
            if self.getIsUpdateNomenclatureDosage(action):
                action = updateNomenclatureDosageValue(action)
            self.edtAPQuantity.setValue(forceInt(action.getRecord().value('quantity')))


    def getIsUpdateNomenclatureDosage(self, action):
        isUpdateNomenclatureDosage = True
        stockMotionItems = action.nomenclatureExpense.stockMotionItems()
        if action.nomenclatureExpense.stockMotionRecord() and stockMotionItems:
            nomencalureId = None
            for properties in action._properties:
                type = properties._type
                name = type.name
                if type.isNomenclatureValueType():
                    property = action.getProperty(name)
                    nomencalureId = property.getValue()
                    if nomencalureId:
                        break
            for item in stockMotionItems:
                if nomencalureId == forceRef(item.value('nomenclature_id')) and forceRef(item.value('id')):
                    isUpdateNomenclatureDosage = False
                    break
        return isUpdateNomenclatureDosage


    @pyqtSignature('int')
    def on_edtAPPeriodicity_valueChanged(self, value):
        self.onActionDataChanged('periodicity', value)
        record, action = self.tblAPActions.model().items()[self.tblAPActions.currentIndex().row()]
        if action and action.getType().isDoesNotInvolveExecutionCourse and action.nomenclatureExpense:
            if self.getIsUpdateNomenclatureDosage(action):
                action = updateNomenclatureDosageValue(action)
            self.edtAPQuantity.setValue(forceInt(action.getRecord().value('quantity')))


    @pyqtSignature('int')
    def on_edtAPAliquoticity_valueChanged(self, value):
        self.onActionDataChanged('aliquoticity', value)
        record, action = self.tblAPActions.model().items()[self.tblAPActions.currentIndex().row()]
        if action and action.getType().isDoesNotInvolveExecutionCourse and action.nomenclatureExpense:
            if self.getIsUpdateNomenclatureDosage(action):
                action = updateNomenclatureDosageValue(action)
            self.edtAPQuantity.setValue(forceInt(action.getRecord().value('quantity')))


    @pyqtSignature('int')
    def on_edtAPQuantity_valueChanged(self, value):
        self.onActionDataChanged('quantity', value)
        record, action = self.tblAPActions.model().items()[self.tblAPActions.currentIndex().row()]
        canEdit = not action.isLocked() if action else True
        canEditIsExecutionPlan = not bool(action.getExecutionPlan() and action.executionPlanManager.hasItemsToDo())
        self.edtAPPlannedEndDate.setEnabled(bool(not value > 0) and canEdit and canEditIsExecutionPlan)
        self.edtAPPlannedEndTime.setEnabled(bool(not value > 0) and canEdit and canEditIsExecutionPlan)


    @pyqtSignature('double')
    def on_edtAPAmount_valueChanged(self, value):
        self.onActionDataChanged('amount', value)
        row = self.tblAPActions.currentIndex().row()
        model = self.modelAPActions
        model.emitAmountChanged(row)
#        record = model._items[row][0]
#        actionTypeId = forceRef(record.value('actionType_id'))
#        amount = forceDouble(record.value('amount'))
#        personId = forceRef(record.value('person_id'))
#        financeId = forceRef(record.value('finance_id'))
#        contractId = forceRef(record.value('contract_id'))
#        self.edtAPUet.setValue(value*self.eventEditor.getUet(actionTypeId, personId, financeId, contractId))



#    @pyqtSignature('double')
#    def on_edtAPUet_valueChanged(self, value):
#        self.onActionDataChanged('uet', value)


    @pyqtSignature('QString')
    def on_edtAPOffice_textChanged(self, text):
        self.onActionDataChanged('office', text)


    @pyqtSignature('int')
    def on_cmbAPOrgStructure_currentIndexChanged(self, index):
        orgStructureId = self.cmbAPOrgStructure.value()
        itemsOS = self.tblAPActions.model().items()
        rowOS = self.tblAPActions.currentIndex().row()
        if 0 <= rowOS < len(itemsOS):
            recordOS, actionOS = itemsOS[rowOS]
            if actionOS and forceRef(actionOS.getRecord().value('orgStructure_id')) != orgStructureId:
                self.onActionDataChanged('orgStructure_id', orgStructureId)
                if orgStructureId and self.eventEditor:
                    items = self.tblAPActions.model().items()
                    row = self.tblAPActions.currentIndex().row()
                    if 0 <= row < len(items):
                        record, action = items[row]
                        if action and action.getType().isNomenclatureExpense:
                            recordExpense = action.getRecord()
                            stockMotionId = forceRef(recordExpense.value('stockMotion_id'))
                            if not stockMotionId:
                                if action.nomenclatureClientReservation:
                                    action.nomenclatureClientReservation.cancel()
                                    action.nomenclatureClientReservation = None
                                    financeId = action.getFinanceId()
                                    medicalAidKindId = action.getMedicalAidKindId() if action.getMedicalAidKindId() else self.eventEditor.eventMedicalAidKindId
                                    action.initNomenclatureReservation(self.eventEditor.clientId, financeId=financeId,
                                                                       medicalAidKindId=medicalAidKindId,
                                                                       supplierId=orgStructureId)
                                if action.nomenclatureExpense:
                                    action.nomenclatureExpense.setSupplierId(orgStructureId)
        if self.eventEditor:
            self._onActionChanged()


    @pyqtSignature('int')
    def on_cmbAPPerson_currentIndexChanged(self, index):
        self.onActionDataChanged('person_id', self.cmbAPPerson.value())
        self._onActionChanged()
        items = self.tblAPActions.model().items()
        row = self.tblAPActions.currentIndex().row()
        if 0<=row<len(items):
            record, action = items[row]
            # actionTemplateTreeModel = self.actionTemplateCache.getModel(action.getType().id)
            # self.btnAPLoadTemplate.setModel(actionTemplateTreeModel)
            if not(QtGui.qApp.userHasRight(urLoadActionTemplate) and (self.cmbAPStatus.value() != CActionStatus.finished
                                                                      or not self.cmbAPPerson.value()
                                                                      or QtGui.qApp.userId == self.cmbAPPerson.value()
                                                                      or (QtGui.qApp.userHasRight(urEditOtherPeopleActionSpecialityOnly) and QtGui.qApp.userSpecialityId == self.getSpecialityId(self.cmbAPPerson.value()))
                                                                      or QtGui.qApp.userHasRight(urEditOtherpeopleAction))):
                self.btnAPLoadTemplate.setEnabled(False)

    def getSpecialityId(self, personId):
        specialityId = None
        if personId:
            db = QtGui.qApp.db
            tablePerson = db.table('Person')
            record = db.getRecordEx(tablePerson, [tablePerson['speciality_id']],
                                    [tablePerson['deleted'].eq(0), tablePerson['id'].eq(personId)])
            specialityId = forceRef(record.value('speciality_id')) if record else None
        return specialityId


    @pyqtSignature('int')
    def on_cmbAPAssistant_currentIndexChanged(self, index):
        self.onActionDataChanged('assistant_id', self.cmbAPAssistant.value())

    @pyqtSignature('int')
    def on_cmbActionSpecification_currentIndexChanged(self, index):
        self.onActionDataChanged('actionSpecification_id', self.cmbActionSpecification.value())


    @pyqtSignature('QString')
    def on_edtAPNote_textChanged(self, text):
        self.onActionDataChanged('note', text)


    @pyqtSignature('')
    def on_btnAPAllocateIdMq_clicked(self):
        model = self.tblAPActions.model()
        items = model.items()
        row = self.tblAPActions.currentIndex().row()
        if 0<=row<len(items):
            record, action = items[row]
            flatCode = action.actionType().flatCode
            hospitalBedProfileId = action[u'Профиль'] if action.hasProperty(u'Профиль') else None
            specialityId         = action[u'Профиль'] if action.hasProperty(u'Профиль') else None
            serviceId            = action[u'Услуга']  if action.hasProperty(u'Услуга') else None
            apNumber             = action[u'Номер']   if action.hasProperty(u'Номер') else None
            misDirectionNumber   = apNumber if apNumber else unicode(action.getId())

            actionPersonId = forceRef(action.getRecord().value('person_id'))
            if not actionPersonId:
                actionPersonId = forceRef(action.getRecord().value('setPerson_id'))

            serviceUrl = QtGui.qApp.getMqHelperUrl()
#            serviceUrl = 'http://serv/queueManagement_P39/api'
            client = CJsonRpcClent(serviceUrl)
            try:
                result = client.call('allocateIdMq',
                                     params={ 'clientId'            : self.eventEditor.clientId,
                                              'actionTypeFlatCode'  : flatCode,
                                              'hospitalBedProfileId': hospitalBedProfileId,
                                              'specialityId'        : specialityId,
                                              'serviceId'           : serviceId,
                                              'misDirectionNumber'  : misDirectionNumber,
                                              'personId'            : actionPersonId
                                            }
                                    )
                action[u'Идентификатор УО'] = result['IdMq']
            except Exception, e:
                QtGui.QMessageBox.critical(self,
                        u'Ошибка регистрации направления',
                        exceptionToUnicode(e),
                        QtGui.QMessageBox.Ok,
                        QtGui.QMessageBox.Ok)


    @pyqtSignature('')
    def on_btnAPNomenclatureExpense_clicked(self):
        model = self.tblAPActions.model()
        items = model.items()
        row = self.tblAPActions.currentIndex().row()
        if 0 <= row < len(items):
            record, action = items[row]
            if not self._openNomenclatureEditor(action, record):
                if action.nomenclatureExpense:
                    action.nomenclatureExpense.cancelEx()
    

    def reloadCurrentAction(self):
        model = self.tblAPActions.model()
        row = self.tblAPActions.currentIndex().row()
        model.reloadItem(row)

    @pyqtSignature('')
    def on_actImportAvailableProfiles_triggered(self):
        url = 'http://'+QtGui.qApp.preferences.dbServerName+'/queueManagement/importAvailableProfiles.php'
        response = requests.get(url)
        if response.status_code == 200:
            QtGui.QMessageBox.information(self, u'Внимание!', u'Данные загружены')
        else:
            QtGui.QMessageBox.information(self, u'Внимание!', u'Данные не загружены')

    @pyqtSignature('')
    def on_actAPQMSetAppointment_triggered(self):
        model = self.tblAPActions.model()
        items = model.items()
        row = self.tblAPActions.currentIndex().row()
        if 0 <= row < len(items):
            record, action = items[row]
            if action._actionType.flatCode in (u'consultationDirection', u'researchDirection'):
                requiredProperties = [
                    u'Профиль',
                    u'Куда направляется',
                ]
                for requiredPropertyName in requiredProperties:
                    if not action.hasProperty(requiredPropertyName) or not action[requiredPropertyName]:
                        QtGui.QMessageBox.warning(self,
                                                  u'Внимание!',
                                                  u'Необходимо заполнить свойство "%s"!' % requiredPropertyName,
                                                  QtGui.QMessageBox.Ok,
                                                  QtGui.QMessageBox.Ok
                                                  )
                        return
                orgId = action[u'Куда направляется']
                profileId = action[u'Профиль']
                if self.eventEditor.isDirty():
                    if QtGui.QMessageBox.question(self,
                                                  u'Внимание!',
                                                  u'Необходимо применить изменения перед записью на прием. Сохранить событие?',
                                                  QtGui.QMessageBox.Ok | QtGui.QMessageBox.No,
                                                  QtGui.QMessageBox.No) == QtGui.QMessageBox.No:
                        return
                    if not self.eventEditor.applyChanges():
                        return
                dialog = CUOAppointmentsTableDialog(self, action)
                try:
                    dialog.exec_()
                    if dialog.actionChanged:
                        self.reloadCurrentAction()
                        self.onActionCurrentChanged()
                finally:
                    dialog.deleteLater()

    @pyqtSignature('')
    def on_actAPQMCancelReferral_triggered(self):
        model = self.tblAPActions.model()
        items = model.items()
        row = self.tblAPActions.currentIndex().row()
        if 0 <= row < len(items):
            record, action = items[row]
            actionChanged = False
            appointmentCanceled = False
            if action[u'Идентификатор направления'] is None:
                return
            if (action[u'Причина аннулирования'] is not None and len(action[u'Причина аннулирования']) > 0):
                return
            if self.eventEditor.isDirty():
                if QtGui.QMessageBox.question(self,
                                              u'Внимание!',
                                              u'Необходимо применить изменения перед записью на прием. Сохранить событие?',
                                              QtGui.QMessageBox.Ok | QtGui.QMessageBox.No,
                                              QtGui.QMessageBox.No) == QtGui.QMessageBox.No:
                    return
                if not self.eventEditor.applyChanges():
                    return
            client = CUOServiceClient()
            # if action[u'Идентификатор талона'] is not None:
            #     try:
            #         client.createClaimForRefusal(action)
            #         appointmentCanceled = True
            #         actionChanged = True
            #     except Exception, e:
            #         QtGui.QMessageBox.critical(self,
            #             u'Ошибка при отмене записи на прием',
            #             exceptionToUnicode(e),
            #             QtGui.QMessageBox.Ok,
            #             QtGui.QMessageBox.Ok)
            #         return
            # Уходим от отмены записи с нашей стороны, в виду автоматической отмены записи самой шиной при аннулировании направления
            try:
                client.cancelReferral(action, u'3', u'5', u'Прочее')
                actionChanged = True
                if appointmentCanceled:
                    message = u'Запись на прием отменена, направление аннулировано'
                else:
                    message = u'Направление аннулировано'
                QtGui.QMessageBox.information(self,
                                              u'Внимание!',
                                              message,
                                              QtGui.QMessageBox.Ok,
                                              QtGui.QMessageBox.Ok)
            except Exception, e:
                QtGui.QMessageBox.critical(self,
                                           u'Ошибка при аннулировании направления',
                                           exceptionToUnicode(e),
                                           QtGui.QMessageBox.Ok,
                                           QtGui.QMessageBox.Ok)
            if actionChanged:
                self.reloadCurrentAction()
                self.onActionCurrentChanged()

    @pyqtSignature('')
    def on_actAPQMCreateClaimForRefusal_triggered(self):
        model = self.tblAPActions.model()
        items = model.items()
        row = self.tblAPActions.currentIndex().row()
        if 0 <= row < len(items):
            record, action = items[row]
            if action[u'Идентификатор талона'] is None:
                return
            if self.eventEditor.isDirty():
                if QtGui.QMessageBox.question(self,
                                              u'Внимание!',
                                              u'Необходимо применить изменения перед записью на прием. Сохранить событие?',
                                              QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                              QtGui.QMessageBox.No) == QtGui.QMessageBox.No:
                    return
                if not self.eventEditor.applyChanges():
                    return
            try:
                client = CUOServiceClient()
                client.createClaimForRefusal(action)
                QtGui.QMessageBox.information(self,
                                              u'Внимание!',
                                              u'Запись на прием отменена',
                                              QtGui.QMessageBox.Ok,
                                              QtGui.QMessageBox.Ok)
                self.reloadCurrentAction()
                self.onActionCurrentChanged()
            except Exception, e:
                QtGui.QMessageBox.critical(self,
                                           u'Ошибка при отмене записи на прием',
                                           exceptionToUnicode(e),
                                           QtGui.QMessageBox.Ok,
                                           QtGui.QMessageBox.Ok)

    @pyqtSignature('')
    def on_actCreatingApplication_triggered(self):
        model = self.tblAPActions.model()
        items = model.items()
        row = self.tblAPActions.currentIndex().row()
        if 0 <= row < len(items):
            record, action = items[row]
            if not action._propertiesByShortName['direction_identifier']._value:
                if self.eventEditor.isDirty():
                    if QtGui.QMessageBox.question(self,
                                                  u'Внимание!',
                                                  u'Необходимо применить изменения. Сохранить событие?',
                                                  QtGui.QMessageBox.Ok | QtGui.QMessageBox.No,
                                                  QtGui.QMessageBox.No) == QtGui.QMessageBox.No:
                        return
                    if not self.eventEditor.applyChanges():
                        return
            template = getFirstPrintTemplate('startTMK')
            if template:
                self.on_btnAPPrint_printByTemplate(template.id)


    @pyqtSignature('')
    def on_actViewingApplications_triggered(self):
        template = getFirstPrintTemplate('listTMK')
        if template:
            self.on_btnAPPrint_printByTemplate(template.id)


    def _openNomenclatureEditor(self, action, record, requireItems=False):
        if not action:
            return False
        if not action.getType().isNomenclatureExpense:
            return True
        # Результат может влиять на продолжение работы функционала "Выполнить"
        if action.getType().isNomenclatureExpense and forceInt(action.getRecord().value('status')) == CActionStatus.finished:
            actionTypeId = forceRef(action.getRecord().value('actionType_id'))
            if actionTypeId:
                db = QtGui.qApp.db
                tableATN = db.table('ActionType_Nomenclature')
                nomenclatureIdList = db.getDistinctIdList(tableATN, [tableATN['id']], [tableATN['master_id'].eq(actionTypeId)])
                if nomenclatureIdList:
                    result, (record, action) = selectNomenclatureExpense(self, action)
                    if not result or not action:
                        return False

        if not action.nomenclatureExpense:
            return True

        if action.nomenclatureExpense.stockMotionRecord():
            supplierId = forceRef(action.getRecord().value('orgStructure_id'))
            if supplierId:
                action.nomenclatureExpense.setSupplierId(supplierId)
            if requireItems and not action.nomenclatureExpense.stockMotionItems():
                nomenclatureIdDict = {}
                nomenclatureId = action.findNomenclaturePropertyValue()
                if not nomenclatureId:
                    return True
                nomenclatureIdDict[nomenclatureId] = (action.getRecord(), action.findDosagePropertyValue())
                action.nomenclatureExpense.updateNomenclatureIdListToAction(nomenclatureIdDict)
                if not action.nomenclatureExpense.stockMotionItems():
                    return True

            isControlExecWriteOffNomenclatureExpense = QtGui.qApp.controlExecutionWriteOffNomenclatureExpense()
            if isControlExecWriteOffNomenclatureExpense:
                db = QtGui.qApp.db
                message = u''
                nomenclatureLine = []
                resQntDict = {}
                tableNomenclature = db.table('rbNomenclature')
                if action.nomenclatureExpense:
                    stockMotionItems = action.nomenclatureExpense.stockMotionItems()
                    for stockMotionItem in stockMotionItems:
                        price = forceDouble(stockMotionItem.value('price'))
                        oldPrice = price
                        nomenclatureId = forceRef(stockMotionItem.value('nomenclature_id'))
                        if nomenclatureId and nomenclatureId not in nomenclatureLine:
                            qnt = forceDouble(stockMotionItem.value('qnt'))
                            resQnt, proxyQnt, planQnt, simpleRatio = resQntDict.get(nomenclatureId, (None, None, None, 2))
                            unitId = forceRef(stockMotionItem.value('unit_id'))
                            stockUnitId = self.getDefaultStockUnitId(nomenclatureId)
                            ratio = self.getRatio(nomenclatureId, stockUnitId, unitId)
                            if ratio is not None:
                                price = price*ratio
                                qnt = qnt / ratio
                            qnt = round(qnt, QtGui.qApp.numberDecimalPlacesQnt())
                            if planQnt is None:
                                nomenclativeRecord, dosage = nomenclatureIdDict.get(nomenclatureId, (None, 0))
                                planQnt = action.nomenclatureExpense.getNomenclatureDosageToQntValue(nomenclatureId, dosage)
                                if ratio is not None:
                                    planQnt = planQnt / ratio
                                planQnt = round(planQnt, QtGui.qApp.numberDecimalPlacesQnt())
                            if proxyQnt is None:
                                proxyQnt = 0
                                model = self.tblAPActions.model()
                                mapProxyRow2Group = model._mapProxyRow2Group
                                actionRow = self.tblAPActions.currentIndex().row()
                                if mapProxyRow2Group and actionRow >= 0 and actionRow < len(model.items()) and actionRow in mapProxyRow2Group.keys():
                                    proxyGroup = mapProxyRow2Group[actionRow]
                                    if proxyGroup:
                                        for proxyItem in proxyGroup.items:
                                            i = proxyGroup._mapItem2Row.get(proxyItem, -1)
                                            if i > -1 and i != proxyGroup._headModelRow:
                                                proxyQnt += proxyItem.action.findDosagePropertyValue()
                                        if ratio is not None:
                                            proxyQnt = proxyQnt / ratio
                                        proxyQnt = round(proxyQnt, QtGui.qApp.numberDecimalPlacesQnt())
                            if proxyQnt > 0:
                                proxyQnt = proxyQnt - qnt
                                proxyQnt = round(proxyQnt, QtGui.qApp.numberDecimalPlacesQnt())
                            if proxyQnt < 0:
                                proxyQnt = 0
                            financeId = forceRef(stockMotionItem.value('finance_id'))
                            batch = forceString(stockMotionItem.value('batch'))
                            shelfTime = forceDate(stockMotionItem.value('shelfTime'))
                            shelfTime = shelfTime.toPyDate() if bool(shelfTime) else None
                            medicalAidKindId = forceRef(stockMotionItem.value('medicalAidKind_id'))
                            otherHaving=[u'(shelfTime>=curDate()) OR shelfTime is NULL']
                            existsQnt = getExistsNomenclatureAmount(nomenclatureId, financeId, batch, orgStructureId=supplierId, unitId=stockUnitId, medicalAidKindId = medicalAidKindId, shelfTime=shelfTime, otherHaving=otherHaving, exact=True, price=price, isStockUtilization=False, precision=QtGui.qApp.numberDecimalPlacesQnt())
                            masterId = forceRef(stockMotionItem.value('master_id'))
                            prevQnt = round(getStockMotionItemQntEx(nomenclatureId, stockMotionId=masterId, batch=batch, financeId=financeId, medicalAidKindId=medicalAidKindId, price=None, oldPrice=oldPrice, oldUnitId=stockUnitId), QtGui.qApp.numberDecimalPlacesQnt()) if masterId else 0
                            reservationQnt = round(getStockMotionItemQntEx(nomenclatureId, stockMotionId=None, batch=batch, financeId=financeId, clientId=self.clientId(), medicalAidKindId=medicalAidKindId, price=None, oldPrice=price, oldUnitId=stockUnitId), QtGui.qApp.numberDecimalPlacesQnt())
                            if existsQnt < 0:
                                existsQnt = 0
                            if prevQnt < 0:
                                prevQnt = 0
                            if reservationQnt < 0:
                                reservationQnt = 0
                            if resQnt is None:
                                resQnt = (existsQnt + reservationQnt + prevQnt) - qnt
                            else:
                                resQnt += (existsQnt + reservationQnt + prevQnt) - qnt
                            resQnt = round(resQnt, QtGui.qApp.numberDecimalPlacesQnt())
                            planQnt = planQnt - qnt
                            planQnt = round(planQnt, QtGui.qApp.numberDecimalPlacesQnt())
                            resQntDict[nomenclatureId] = (resQnt, proxyQnt, planQnt, len(forceStringEx(self.getSimpleRatio(nomenclatureId, stockUnitId, unitId))))
                    for nomenclatureIdKey, (resQntValue, proxyQntValue, planQntValue, simpleQntRatio) in resQntDict.items():
                        if resQntValue < 0 or resQntValue is None or (round(planQntValue, simpleQntRatio) != 0 and planQntValue is not None):
                            nomenclatureLine.append(nomenclatureIdKey)
                    if nomenclatureLine:
                        records = db.getRecordList(tableNomenclature, [tableNomenclature['name']], [tableNomenclature['id'].inlist(nomenclatureLine)], order = tableNomenclature['name'].name())
                        nomenclatureName = u','.join(forceString(recordNomenclature.value('name')) for recordNomenclature in records)
                        message += u'''Действие типа %s.\nОтсутствуют ЛСиИМН: %s!\n'''%(action._actionType.name, nomenclatureName)
                    if message:
                        if isControlExecWriteOffNomenclatureExpense == 1:
                            button = QtGui.QMessageBox.Ok|QtGui.QMessageBox.Cancel
                            message2 = u'Списываемого ЛСиИМН %s недостаточно на остатке подразделения. Выполнить списание?'%(nomenclatureName)
                        else:
                            button = QtGui.QMessageBox.Cancel
                            message2 = u'Списываемого ЛСиИМН %s недостаточно на остатке подразделения. Выполнение назначения невозможно!\n'%(nomenclatureName)
                        res = QtGui.QMessageBox.warning(None,
                                                    u'Внимание!',
                                                    message2,
                                                    button,
                                                    QtGui.QMessageBox.Cancel)
                        if res == QtGui.QMessageBox.Cancel:
                            return False

            medicalAidKindId = action.getMedicalAidKindId()
            if QtGui.qApp.keyboardModifiers() & Qt.ShiftModifier:
                dlg = CClientRefundInvoiceEditDialog(self)
                dlg.setData(action.nomenclatureExpense)
            else:
                dlg = CClientInvoiceEditDialog(self, fromAction=True)
                dlg.setFinanceId(self.eventEditor.eventFinanceId)
                if medicalAidKindId:
                    dlg.setMedicalAidKindId(medicalAidKindId)
                dlg.setData(action.nomenclatureExpense)
                dlg.setClientId(self.eventEditor.clientId)
            try:
                dlg.exec_()
                dlg.getRecord()
                result = dlg.closeByOkButton
                action.setNomenclatureExpensePreliminarySave(result)
            finally:
                dlg.deleteLater()

            return result
        else:
            QtGui.QMessageBox.warning(self,
                                      u'Внимание!',
                                      u'Не удалось инициализировать записи ЛСиИМН \nсвязанные с данным действием!',
                                      QtGui.QMessageBox.Ok,
                                      QtGui.QMessageBox.Ok)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_modelAPActionProperties_dataChanged(self, topLeft, bottomRight):
        self.updateAmount()
        model = self.tblAPActions.model()
        items = model.items()
        row = self.tblAPActions.currentIndex().row()
        record, action = items[row]
        actionTypeId = forceRef(record.value('actionType_id')) if record else None
        actionType = CActionTypeCache.getById(actionTypeId) if actionTypeId else None
        if u'moving' in actionType.flatCode.lower():
            if action[u'Переведен в отделение']:
                self.btnNextAction.setText(u'Перевод')
                self.btnNextAction.setEnabled(self.edtAPEndDate.date().isNull())
            else:
                self.btnNextAction.setText(u'Выписка')
                isEnable = not self.isReadOnly() and ((QtGui.qApp.userHasRight(urHBLeaved) or QtGui.qApp.isAdmin()) if (self.eventEditor and self.eventEditor.isHBDialog) else True)
                self.btnNextAction.setEnabled(self.edtAPEndDate.date().isNull() and isEnable)
        elif u'received' in actionType.flatCode.lower():
            if action[u'Направлен в отделение']:
                self.btnNextAction.setText(u'Перевод')
                self.btnNextAction.setEnabled(self.edtAPEndDate.date().isNull())
            else:
                self.btnNextAction.setText(u'Выписка')
                isEnable = not self.isReadOnly() and ((QtGui.qApp.userHasRight(urHBLeaved) or QtGui.qApp.isAdmin()) if (self.eventEditor and self.eventEditor.isHBDialog) else True)
                self.btnNextAction.setEnabled(self.edtAPEndDate.date().isNull() and isEnable)
            if u'Доставлен по' in action._actionType._propertiesByName and action[u'Доставлен по'] is not None and getEventAidTypeRegionalCode(self.eventEditor.eventTypeId) not in ['111', '112']:
                if u'экстренным показаниям' in action[u'Доставлен по'].lower():
                    self.eventEditor.cmbOrder.setCurrentIndex(1)
                elif u'плановым показаниям' in action[u'Доставлен по'].lower():
                    self.eventEditor.cmbOrder.setCurrentIndex(0)
            # if hasattr(self.eventEditor, 'tabNotes'):
            #     form = getEventTypeForm(self.eventEditor.eventTypeId)
            #     if form == '003':
            #         if action and u'Кем направлен' in action._actionType._propertiesByName and u'Кем направлен' in action._properties[topLeft.row()].type().name:
            #             if hasattr(self.eventEditor, 'tabNotes') and hasattr(self.eventEditor.tabNotes, 'cmbRelegateOrg'):
            #                 self.eventEditor.tabNotes.cmbRelegateOrg.setValue(forceRef(action[u'Кем направлен']))
            #             elif hasattr(self.eventEditor, 'tabVoucher') and hasattr(self.eventEditor.tabVoucher, 'cmbDirectionOrgs'):
            #                 self.eventEditor.tabVoucher.cmbDirectionOrgs.setValue(forceRef(action[u'Кем направлен']))
            #         if action and u'Номер направления' in action._actionType._propertiesByName and u'Номер направления' in action._properties[topLeft.row()].type().name:
            #             if hasattr(self.eventEditor.tabNotes, 'edtEventSrcNumber'):
            #                 self.eventEditor.tabNotes.edtEventSrcNumber.setText(forceString(action[u'Номер направления']))
            #         elif u'№ направления' in action._actionType._propertiesByName and u'№ направления' in action._properties[topLeft.row()].type().name:
            #             if hasattr(self.eventEditor.tabNotes, 'edtEventSrcNumber'):
            #                 self.eventEditor.tabNotes.edtEventSrcNumber.setText(forceString(action[u'№ направления']))
            #         if action and u'Дата направления' in action._actionType._propertiesByName and u'Дата направления' in action._properties[topLeft.row()].type().name:
            #             if hasattr(self.eventEditor.tabNotes, 'edtEventSrcDate'):
            #                 self.eventEditor.tabNotes.edtEventSrcDate.setDate(forceDate(action[u'Дата направления']))
        elif u'planning' in actionType.flatCode.lower():
            if action and u'Кем направлен' in action._actionType._propertiesByName:
                # if hasattr(self.eventEditor, 'tabNotes') and hasattr(self.eventEditor.tabNotes, 'cmbRelegateOrg'):
                #     propRelegateOrgId = forceRef(action[u'Кем направлен'])
                #     if propRelegateOrgId:
                #         property = self.modelAPActionProperties.getPropertyType(self.tblAPProps.currentIndex().row())
                #         if property and property.name == u'Кем направлен':
                #             self.eventEditor.tabNotes.cmbRelegateOrg.setValue(propRelegateOrgId)
                if hasattr(self.eventEditor, 'tabVoucher') and hasattr(self.eventEditor.tabVoucher, 'cmbDirectionOrgs'):
                    self.eventEditor.tabVoucher.cmbDirectionOrgs.setValue(forceRef(action[u'Кем направлен']))
            # if action and u'Номер документа' in action._actionType._propertiesByName:
            #     if hasattr(self.eventEditor.tabNotes, 'edtEventSrcNumber'):
            #         self.eventEditor.tabNotes.edtEventSrcNumber.setText(forceString(action[u'Номер документа']))
            # elif u'№ документа' in action._actionType._propertiesByName:
            #     if hasattr(self.eventEditor.tabNotes, 'edtEventSrcNumber'):
            #         self.eventEditor.tabNotes.edtEventSrcNumber.setText(forceString(action[u'№ документа']))
            # if action and u'Дата направления' in action._actionType._propertiesByName:
            #     if hasattr(self.eventEditor.tabNotes, 'edtEventSrcDate'):
            #         self.eventEditor.tabNotes.edtEventSrcDate.setDate(forceDate(action[u'Дата направления']))
        elif u'inspectPigeonHole'.lower() in actionType.flatCode.lower():
            self.btnNextAction.setText(u'Закончить')
            self.btnNextAction.setEnabled(self.edtAPEndDate.date().isNull())
        if actionType.defaultBegDate == CActionType.dbdJobTicketTime:
            if self.modelAPActionProperties.getPropertyType(self.tblAPProps.currentIndex().row()).isJobTicketValueType():
                dateTimeJT = action.getJobTicketDateTime()
                if dateTimeJT and forceDateTime(record.value('begDate')) != dateTimeJT:
                    record.setValue('begDate',toVariant(dateTimeJT))
                    self.edtAPBegDate.setDate(dateTimeJT.date())
                    self.edtAPBegTime.setTime(dateTimeJT.time())
        property = self.modelAPActionProperties.getPropertyType(self.tblAPProps.currentIndex().row())
        if action and record and property and property.isJobTicketValueType():
            prop = action.getPropertyById(property.id)
            if prop:
                jobTicketId = prop.getValue()
                jobTicketOrgStructureId = action.getJobTicketOrgStructureId(jobTicketId) if jobTicketId else None
                if jobTicketOrgStructureId:
                    record.setValue('orgStructure_id', toVariant(jobTicketOrgStructureId))
        if action and action.getType().isDoesNotInvolveExecutionCourse and action.nomenclatureExpense and record and property and property.inActionsSelectionTable == _DOSES: # doses
            action = updateNomenclatureDosageValue(action)


    @pyqtSignature('int')
    def on_btnAPPrint_printByTemplate(self, templateId):
        if self.eventEditor.checkPrintByTemplateAllowed(templateId):
            model = self.tblAPActions.model()
            items = model.items()
            row = self.tblAPActions.currentIndex().row()
            if 0 <= row < len(items):
                data = getEventContextData(self.eventEditor)
                eventInfo = data['event']
                currentActionIndex = eventInfo.actions._rawItems.index(items[row])
                action = eventInfo.actions[currentActionIndex]
                action.setCurrentPropertyIndex(self.tblAPProps.currentIndex().row())
                data['action'] = action
                data['actions'] = eventInfo.actions
                data['currentActionIndex'] = currentActionIndex
                data['currentAction'] = items[self.tblAPActions.currentIndex().row()]
                applyTemplate(self.eventEditor,
                              templateId,
                              data,
                              signAndAttachHandler=self.btnAPAttachedFiles.getSignAndAttachHandler())


    @pyqtSignature('')
    def on_actCopyInputActionProperty_triggered(self):
        model = self.tblAPActions.model()
        items = model.items()
        row = self.tblAPActions.currentIndex().row()
        if not self.eventEditor.applyChanges():
            return
        data = getEventContextData(self.eventEditor)
        eventInfo = data['event']
        currentActionIndex = eventInfo.actions._rawItems.index(items[row])
        actionId = eventInfo.actions[currentActionIndex].id
        from library.PrintInfo import CInfoContext
        context = CInfoContext()
        union_value = ''
        if 0 <= row < len(items):
            record_, current_action = items[row]
            from library.copyInput import searchActionIn, searchActionOut
            queryIn = searchActionIn(actionId)
            if queryIn.size() == 0:
                return
            while queryIn.next():
                recordIn = queryIn.record()

                temp_settings = forceString(recordIn.value('dataInheritance')).split('][')
                if len(temp_settings) > 1:
                    settings = temp_settings[0][1:]
                    current_dataInheritance = temp_settings[1][:-1]
                else:
                    settings = None
                    current_dataInheritance = forceString(recordIn.value('dataInheritance')).replace('[','').replace(']','')

                current_name = forceString(recordIn.value('name'))
                if not current_action[current_name]:
                    current_action[current_name] = ''
                if len(current_dataInheritance.split(',')) > 1:
                    current_dataInheritance_temp = []
                    for short in current_dataInheritance.split(','):
                        if 'in_' in short.strip():
                            current_dataInheritance_temp.append(short.strip())
                    queryOut = searchActionOut(current_dataInheritance_temp, eventInfo.id)
                    checkAction = 0
                    while queryOut.next():
                        recordOut = queryOut.record()
                        value = forceString(recordOut.value('value'))
                        if checkAction != forceString(recordOut.value('action_id')):
                            checkAction = 0
                        if settings:
                            union_value = ''
                            from Events.ActionInfo import CActionInfo
                            temp_action = context.getInstance(CActionInfo, forceString(recordOut.value('action_id')))
                            if len(settings.split(',')) > 1:
                                for short_settings in settings.split(','):
                                    if 'property' in short_settings:
                                        if union_value != '':
                                            union_value += '\n'
                                        code = "union_value += temp_action[forceString(recordOut.value('name'))]." + short_settings.replace('property.', '')
                                        exec (code)
                                        union_value += ' '
                                    elif 'action' in short_settings and checkAction == 0:
                                        code = "union_value += temp_action." + short_settings.replace('action.', '')
                                        exec (code)
                                        union_value += ' '
                            else:
                                if 'property' in settings:
                                    if union_value != '':
                                        union_value += '\n'
                                    code = "union_value += temp_action[forceString(recordOut.value('name'))]." + settings.replace('property.', '')
                                    exec (code)
                                    union_value += ' '
                                elif 'action' in settings and checkAction == 0:
                                    code = "union_value += temp_action." + settings.replace('action.', '')
                                    exec (code)
                                    union_value += ' '
                        else:
                            union_value = ''
                        if checkAction == 0:
                            checkAction = forceString(recordOut.value('action_id'))

                        if (union_value + '\n' + value) not in current_action[current_name] and (union_value + ' - ' + value) not in current_action[current_name]:
                            if current_action[current_name] != '':
                                current_action[current_name] += '\n'
                            if union_value != '':
                                if settings and 'property' in settings:
                                    current_action[current_name] += union_value + ' - ' + value
                                else:
                                    current_action[current_name] += union_value + '\n' + value
                            else:
                                current_action[current_name] += value
                else:
                    queryOut = searchActionOut(current_dataInheritance, eventInfo.id)
                    checkAction = 0
                    while queryOut.next():
                        recordOut = queryOut.record()
                        value = forceString(recordOut.value('value'))
                        if checkAction != forceString(recordOut.value('action_id')):
                            checkAction = 0
                        if settings:
                            union_value = ''
                            from Events.ActionInfo import CActionInfo
                            temp_action = context.getInstance(CActionInfo, forceString(recordOut.value('action_id')))
                            if len(settings.split(',')) > 1:
                                for short_settings in settings.split(','):
                                    if 'property' in short_settings:
                                        if union_value != '':
                                            union_value += '\n'
                                        code = "union_value += temp_action[forceString(recordOut.value('name'))]." + short_settings.replace('property.', '')
                                        exec(code)
                                        union_value += ' '
                                    elif 'action' in short_settings  and checkAction == 0:
                                        code = "union_value += temp_action." + short_settings.replace('action.', '')
                                        exec (code)
                                        union_value += ' '
                            else:
                                if 'property' in settings:
                                    if union_value != '':
                                        union_value += '\n'
                                    code = "union_value += temp_action[forceString(recordOut.value('name'))]." + settings.replace('property.', '')
                                    exec (code)
                                    union_value += ' '
                                elif 'action' in settings  and checkAction == 0:
                                    code = "union_value += temp_action." + settings.replace('action.', '')
                                    exec (code)
                                    union_value += ' '
                        else:
                            union_value = ''

                        if checkAction == 0:
                            checkAction = forceString(recordOut.value('action_id'))

                        if (union_value + '\n' + value) not in unicode(current_action[current_name]) and (union_value + ' - ' + value) not in unicode(current_action[current_name]):
                            if current_action[current_name] != '':
                                current_action[current_name] = unicode(current_action[current_name]) + '\n'
                            if union_value != '':
                                if settings and 'property' in settings:
                                    current_action[current_name] = unicode(current_action[current_name]) + union_value + '- ' + value
                                else:
                                    current_action[current_name] = unicode(current_action[current_name]) + union_value + '\n' + value
                            else:
                                current_action[current_name] = unicode(current_action[current_name]) + value
        self.tblAPProps.model().reset()

    @pyqtSignature('')
    def on_btnAPLoadTemplate_clicked(self):
        model = self.tblAPActions.model()
        items = model.items()
        row = self.tblAPActions.currentIndex().row()
        if QtGui.qApp.userHasRight(urLoadActionTemplate) and 0 <= row < len(items) and (self.cmbAPStatus.value() != CActionStatus.finished
                                                                                    or not self.cmbAPPerson.value()
                                                                                    or QtGui.qApp.userId == self.cmbAPPerson.value()
                                                                                    or (QtGui.qApp.userHasRight(urEditOtherPeopleActionSpecialityOnly) and QtGui.qApp.userSpecialityId == self.getSpecialityId(self.cmbAPPerson.value()))
                                                                                    or QtGui.qApp.userHasRight(urEditOtherpeopleAction)):
            actionRecord, action = items[row]
            personSNILS = u''
            showTypeTemplate = 0
            templateAction = None
            isMethodRecording = CAction.actionNoMethodRecording
            personId = QtGui.qApp.userId if QtGui.qApp.userSpecialityId else self.eventEditor.personId
            specialityId = QtGui.qApp.userSpecialityId if QtGui.qApp.userSpecialityId else self.eventEditor.personSpecialityId
            if personId:
                db = QtGui.qApp.db
                tablePerson = db.table('Person')
                record = db.getRecordEx(tablePerson, [tablePerson['showTypeTemplate'], tablePerson['SNILS']], [tablePerson['id'].eq(personId), tablePerson['deleted'].eq(0)])
                if record:
                    personSNILS = forceStringEx(record.value('SNILS'))
                    showTypeTemplate = forceInt(record.value('showTypeTemplate'))
            dlg = CActionTemplateSelectDialog(parent=self,
                                            actionRecord=actionRecord,
                                            action=action,
                                            clientSex=self.eventEditor.clientSex,
                                            clientAge=self.eventEditor.clientAge,
                                            personId=personId,
                                            specialityId=specialityId,
                                            orgStructureId=QtGui.qApp.currentOrgStructureId(),
                                            SNILS=personSNILS,
                                            showTypeTemplate=showTypeTemplate,
                                            model=self.actionTemplateCache.getModel(action.getType().id)
                                           )
            try:
                if dlg.exec_():
                   templateAction = dlg.getSelectAction()
                   isMethodRecording = dlg.getMethodRecording()
            finally:
                dlg.deleteLater()
            if templateAction:
                action.updateByAction(templateAction, checkPropsOnOwner=True, clientSex=self.eventEditor.clientSex, clientAge=self.eventEditor.clientAge, isMethodRecording=isMethodRecording)
                for prop in action._properties:
                    if prop.isActionNameSpecifier():
                        action.updateSpecifiedName()
                        self.modelAPActionProperties.emit(SIGNAL('actionNameChanged()'))
                        self.modelAPActionProperties.emitDataChanged()
                self.tblAPProps.model().reset()
                self.tblAPProps.resizeRowsToContents()
                model.updateActionAmount(row)


    @pyqtSignature('')
    def on_btnAPSaveAsTemplate_clicked(self):
        model = self.tblAPActions.model()
        items = model.items()
        row = self.tblAPActions.currentIndex().row()
        if QtGui.qApp.userHasRight(urSaveActionTemplate) and 0<=row<len(items):
            actionRecord, action = items[row]
            personSNILS      = u''
            showTypeTemplate = 0
            personId = QtGui.qApp.userId if QtGui.qApp.userSpecialityId else self.eventEditor.personId
            specialityId = QtGui.qApp.userSpecialityId if QtGui.qApp.userSpecialityId else self.eventEditor.personSpecialityId
            if personId:
                db = QtGui.qApp.db
                tablePerson = db.table('Person')
                record = db.getRecordEx(tablePerson, [tablePerson['showTypeTemplate'], tablePerson['SNILS']], [tablePerson['id'].eq(personId), tablePerson['deleted'].eq(0)])
                if record:
                    personSNILS      = forceStringEx(record.value('SNILS'))
                    showTypeTemplate = forceInt(record.value('showTypeTemplate'))
            dlg = CActionTemplateSaveDialog(parent=self,
                                            actionRecord=actionRecord,
                                            action=action,
                                            clientSex=self.eventEditor.clientSex,
                                            clientAge=self.eventEditor.clientAge,
                                            personId=personId,
                                            specialityId=specialityId,
                                            orgStructureId=QtGui.qApp.currentOrgStructureId(),
                                            SNILS=personSNILS,
                                            showTypeTemplate=showTypeTemplate
                                           )
            try:
                dlg.exec_()
            finally:
                dlg.deleteLater()
            self.actionTemplateCache.reset()
            # actionTemplateTreeModel = self.actionTemplateCache.getModel(action.getType().id)
            # self.btnAPLoadTemplate.setModel(actionTemplateTreeModel)
            if not(QtGui.qApp.userHasRight(urLoadActionTemplate) and (self.cmbAPStatus.value() != CActionStatus.finished
                                                                      or not self.cmbAPPerson.value()
                                                                      or QtGui.qApp.userId == self.cmbAPPerson.value()
                                                                      or (QtGui.qApp.userHasRight(urEditOtherPeopleActionSpecialityOnly) and QtGui.qApp.userSpecialityId == self.getSpecialityId(self.cmbAPPerson.value()))
                                                                      or QtGui.qApp.userHasRight(urEditOtherpeopleAction))):
                self.btnAPLoadTemplate.setEnabled(False)


    @pyqtSignature('')
    def on_mnuAPLoadPrevAction_aboutToShow(self):
        model = self.tblAPActions.model()
        items = model.items()
        row = self.tblAPActions.currentIndex().row()
        if 0 <= row < len(items):
            record, action = items[row]
        else:
            action = None
        self.actAPLoadSameSpecialityPrevAction.setEnabled(bool(
                action and self.eventEditor.getPrevActionId(action, CGetPrevActionIdHelper.sameSpecialityPrevAction))
                                                         )
        self.actAPLoadOwnPrevAction.setEnabled(bool(
                action and self.eventEditor.getPrevActionId(action, CGetPrevActionIdHelper.ownPrevAction))
                                              )

        self.actAPLoadAnyPrevAction.setEnabled(bool(
                action and self.eventEditor.getPrevActionId(action, CGetPrevActionIdHelper.anyPrevAction))
                                              )
        if action:
            check_Yes = False
            for prop in action.getPropertiesBydataInheritance():
                if u'in_' in prop:
                    check_Yes = True
            if check_Yes:
                self.actCopyInputActionProperty.setEnabled(True)
            else:
                self.actCopyInputActionProperty.setEnabled(False)
        else:
            self.actCopyInputActionProperty.setEnabled(False)


    @pyqtSignature('')
    def on_actAPLoadSameSpecialityPrevAction_triggered(self):
        if self.isReadOnly():
            return
        self.loadPrevAction(CGetPrevActionIdHelper.sameSpecialityPrevAction)


    @pyqtSignature('')
    def on_actAPLoadOwnPrevAction_triggered(self):
        if self.isReadOnly():
            return
        self.loadPrevAction(CGetPrevActionIdHelper.ownPrevAction)


    @pyqtSignature('')
    def on_actAPLoadAnyPrevAction_triggered(self):
        if self.isReadOnly():
            return
        self.loadPrevAction(CGetPrevActionIdHelper.anyPrevAction)

    @pyqtSignature('')
    def on_btnAPHospitalOrderSelect_clicked(self):
        items = self.tblAPActions.model().items()
        row = self.tblAPActions.currentIndex().row()
        if 0 <= row < len(items):
            action = items[row][1]
        else:
            action = None
        if action:
            dialog = CHospitalOrderSelectDialog(self)
            try:
                if dialog.exec_() == QtGui.QDialog.Accepted:
                    action[u'Куда направляется'] = dialog.organisationId
                    action[u'Профиль койки'] = dialog.bedProfileId
                    action[u'Тип стационара'] = dialog.usok
            finally:
                dialog.deleteLater()

    def on_arrowTypeChanged(self, value):
        self.frmWidgets.setVisible(value)

    def setVisibleBtnCloseWidgets(self, value):
        self.btnCloseWidgets.setVisible(value)
        if value:
            self.btnCloseWidgets.applayArrow()


# ##################################################################

#WFT?
class CActionReplicateDialog(QtGui.QDialog):
    WeekProfiles = (wpFiveDays, wpSixDays, wpSevenDays)
    
    def __init__(self, parent=None, sourceAction=None, eventEditor=None):
        QtGui.QDialog.__init__(self, parent)
        self.lblAmount = QtGui.QLabel(u'Количество', self)
        self.edtAmount = QtGui.QSpinBox(self)

        self.lblWeekProfile = QtGui.QLabel(u'Длительность рабочей недели', self)
        self.cmbWeekProfile = QtGui.QComboBox(self)

        self.buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok, Qt.Horizontal, self)

        self.layout = QtGui.QGridLayout(self)

        self.layout.addWidget(self.lblAmount, 0, 0)
        self.layout.addWidget(self.edtAmount, 0, 1)
        self.layout.addWidget(self.lblWeekProfile, 1, 0)
        self.layout.addWidget(self.cmbWeekProfile, 1, 1)
        self.layout.addWidget(self.buttonBox, 2, 1)

        self.setLayout(self.layout)

        self._result = []
        self._sourceAction = sourceAction
        self._eventEditor = eventEditor

        self._applyWidgetSettings()

        self.setWindowTitle(u'Тиражирование действия')

        self.connect(self.buttonBox, SIGNAL('accepted()'), self.accept)
        self.connect(self.buttonBox, SIGNAL('rejected()'), self.reject)


    def _applyWidgetSettings(self):
        self.edtAmount.setMinimum(1)

        self.cmbWeekProfile.addItem(u'пятидневная рабочая неделя')
        self.cmbWeekProfile.addItem(u'шестидневаня рабочая неделя')
        self.cmbWeekProfile.addItem(u'семидневная рабочая неделя')

        endDate = self._eventEditor.edtEndDate.date()
        begDate = forceDate(self._sourceAction.getRecord().value('begDate'))
        if endDate and begDate:
            amount = begDate.daysTo(endDate)
            amount = 1 if amount in (0, 1) else amount
        else:
            amount = 1
        self.edtAmount.setValue(amount)


    def getResult(self):
        return self._result


    def _countResult(self):
        from PyQt4.QtSql import QSqlRecord

        def _initActionProperties(action):
            actionType = action.getType()
            propertyTypeList = actionType.getPropertiesById().values()
            for propertyType in propertyTypeList:
                action.getPropertyById(propertyType.id)

        def _setNewDate(record, sourceDate, additional, index, weekType):
            def _getNewDate(newDate, weekType):
                if weekType == 0:
                    weekProfile = wpFiveDays
                elif weekType == 1:
                    weekProfile = wpSixDays
                elif weekType == 2:
                    weekProfile = wpSevenDays
                workDay = getNextWorkDay(newDate, weekProfile)
                return workDay

            newTime = sourceDate.time()
            sourceDate = forceDate(sourceDate)
            newDate = sourceDate.addDays(additional)
            targetDate = _getNewDate(newDate, weekType)
            additional = sourceDate.daysTo(targetDate)
            targetDate = forceDateTime(targetDate)
            targetDate.setTime(newTime)
            record.setValue('begDate', toVariant(targetDate))
            record.setValue('endDate', toVariant(targetDate))
            return additional

        sourceRecord = self._sourceAction.getRecord()
        endDate = forceDateTime(sourceRecord.value('endDate'))
        #actionType = self._sourceAction.getType()
        additional = 0
        for i in xrange(self.edtAmount.value()):
            newActionRecord = QSqlRecord(sourceRecord)
            newActionRecord.setValue('id', toVariant(None))
            newAction = CAction(record=newActionRecord)
            _initActionProperties(newAction)
            newAction.updateByAction(self._sourceAction)
            if endDate:
                additional = _setNewDate(newActionRecord, endDate, additional, i, self.cmbWeekProfile.currentIndex())
            self._result.append(newAction)


    def exec_(self):
        r = QtGui.QDialog.exec_(self)
        if r:
            self._countResult()
        return r

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
