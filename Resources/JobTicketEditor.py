# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2025 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################


from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt, QDate, QDateTime, QTime, QVariant, pyqtSignature, pyqtSignal,  SIGNAL,  QMimeData,  QString

from Registry.ClientEditDialog import CClientEditDialog
from library.Counter                  import CCounterController

from library.interchange              import getDatetimeEditValue, getLineEditValue, getRBComboBoxValue, setDatetimeEditValue, setLineEditValue, setRBComboBoxValue
from library.ItemsListDialog          import CItemEditorBaseDialog
from library.PrintInfo                import CInfoContext
from library.PrintTemplates           import additionalCustomizePrintButton, applyTemplate, directPrintTemplate, getFirstPrintTemplate, getPrintButton
from library.Utils                        import calcAgeTuple, forceBool, forceDate, forceDateTime, forceDouble, forceInt, forceRef, forceString, toVariant, trim, forceStringEx

from Events.InputDialog                   import CDateTimeInputDialog # WTF?
from Events.Action                        import CAction, CActionType, CActionTypeCache
from Events.ActionInfo                import CCookedActionInfo
from Events.ActionPropertiesTable     import CActionPropertiesTableModel
from Events.ActionStatus              import CActionStatus
from Events.ActionTemplateSaveDialog  import CActionTemplateSaveDialog
from Events.ActionTemplateSelectDialog    import CActionTemplateSelectDialog
from Events.AmbCardDialog             import CAmbCardDialog
from Events.EventInfo                 import CEventInfo
from Events.GetPrevActionIdHelper     import CGetPrevActionIdHelper
from Events.Utils                         import checkAttachOnDate, checkPolicyOnDate, checkTissueJournalStatus, checkTissueJournalStatusByActions, setActionPropertiesColumnVisible,  validCalculatorSettings
from Orgs.Utils                       import getOrgStructureName
from RefBooks.Equipment.RoleInIntegration import CEquipmentRoleInIntegration
from Registry.StatusObservationClientEditor import CStatusObservationClientEditor
from Registry.Utils                   import getClientInfo, CClientInfo, getClientBanner
from Resources.JobTicketActionsModel  import CJobTicketActionsModel as CActionsModel
from Resources.JobTicketInfo          import makeDependentActionIdList, CJobTicketWithActionsInfo
from Resources.JobTicketProbeModel        import CJobTicketProbeModel, CJobTicketProbeTestItem
from Resources.JobTicketProbesDialog  import CJobTicketProbesDialog
from Resources.JobTicketStatus        import CJobTicketStatus
from Resources.JobTypeActionsSelector import CJobTypeActionsAddingHelper
from Resources.JobActionsCourses      import CJobActionsCoursesMixin
from Resources.JobTicketChooserHelper import createNewExceedJobTicketRecord
from Resources.CourseStatus               import CCourseStatus
from TissueJournal.TissueInfo         import CTakenTissueJournalInfo, CTissueTypeInfo
from TissueJournal.Utils              import CTissueJournalTotalEditorDialog as CActionValuesEditor

from Users.Rights import (urAdmin, urCopyPrevAction, urLoadActionTemplate, urRegTabWriteRegistry, urRegTabReadRegistry,
                          urSaveActionTemplate, urCanDetachActionFromJobTicket, urEditOtherpeopleAction,
                          urEditStatusObservationClient, urEditOtherPeopleActionSpecialityOnly, urReadJobTicketMedKart)

from Resources.BarCodeActionExecutingContext import CBarCodeActionExecutingContext

from Resources.Ui_JobTicketEditor     import Ui_JobTicketEditorDialog


class CJobTicketEditor(CItemEditorBaseDialog, CJobActionsCoursesMixin, Ui_JobTicketEditorDialog):
    openProbesQueuedSignal = pyqtSignal()
    def __init__(self,  parent, actionIdList=None):
        actionIdList = actionIdList if actionIdList is not None else []
        self._jobTicketWasClosed = False
        self._detachedActionsExists = False
        self._jobTypeId = None
        self._jobId = None
        self._jobOrgStructureId = None
        self._jobPurposeId = None
        self._cachedRecord = None
        self._cachedFreeJobTicket = []
#        self._cachedUpdateJobTicket = {}
#        self._cachedChangeJobTicket = []
        self._actionIdList = actionIdList
        self._courseNumber = 1
        self._maxCourseNumber = 1
        self._courseNumber2TakenTissueRecordId = {}

        CItemEditorBaseDialog.__init__(self, parent, 'Job_Ticket')

        self.openProbesQueuedSignal.connect(self.on_btnProbes_clicked, Qt.QueuedConnection)

        self.addObject('actEditClient', QtGui.QAction(u'Открыть регистрационную карточку', self))
        self.addObject('actStatusObservationClient', QtGui.QAction(u'Изменить статус наблюдения пациента', self))

        # popupMenu tblActions
        self.addObject('actSelectAllRowActions',      QtGui.QAction(u'Выделить все строки', self))
        self.addObject('actClearSelectionRowActions', QtGui.QAction(u'Снять выделение', self))
        self.addObject('actChangeValueActions',       QtGui.QAction(u'Изменить данные F2', self))
        self.addObject('actChangeValueCurrentAction', QtGui.QAction(u'Изменить данные текущего элемента', self))
        self.addObject('actAddActions',               QtGui.QAction(u'Добавить действия', self))
        self.addObject('actDetachActions',            QtGui.QAction(u'Отменить', self))
        self.addObject('actDelAddedActions',          QtGui.QAction(u'Удалить', self))

        self.addObject('mnuLoadPrevAction', QtGui.QMenu(self))
        self.addObject('actLoadSameSpecialityPrevAction', QtGui.QAction(u'Той же самой специальности', self))
        self.addObject('actLoadOwnPrevAction',            QtGui.QAction(u'Только свои', self))
        self.addObject('actLoadAnyPrevAction',            QtGui.QAction(u'Любое', self))
        self.addObject('btnPrint', getPrintButton(self, 'jobTicket'))
        self.addObject('btnApplyModifier', QtGui.QPushButton(u'Закрыть работу', self))

        self.addModels('Actions',          CActionsModel(self))
        self.addModels('ActionProperties', CLocActionPropertiesTableModel(self,
                                                                          CActionPropertiesTableModel.visibleInJobTicket))
        self.addModels('JobTicketProbe',   CJobTicketProbeModel(self))


        self.addBarcodeScanAction('actScanBarcode')

        self.getPrevActionIdHelper = CGetPrevActionIdHelper()

        self.clientId  = None
        self.clientSex = None
        self.clientAge = None
        self.isFinishExec = False
        self._defaultEventId = None
        self.actionStatusChanger = None
        self.manualExecutionAssignments = None
        self.actionPersonChanger = 0
        self.actionDateChanger   = 0
        self.execCourse = CCourseStatus.proceed
        self.firstTTJR = self.takenTissueRecord = None
        self.tissueExternalIdForProperty = None
        self._manualInputExternalId = None
        self.actionIdListCanDeleted = []
        self.isTakenTissue = False
        self.date = QDate.currentDate()
        self.labelTemplate = getFirstPrintTemplate('clientTissueLabel')
        self._jobTypeActionsAddingHelper = CJobTypeActionsAddingHelper(self)

        self.setupUi(self)

        self._barCodeExecutingContext = CBarCodeActionExecutingContext(self, True, self.edtTissueExternalId)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setWindowTitleEx(u'Выполнение работы')

        self.edtBegDate.canBeEmpty(True)
        self.edtEndDate.canBeEmpty(True)
        self.cmbTissueType.setTable('rbTissueType')
        self.cmbTissueUnit.setTable('rbUnit')
        self.cmbEquipment.setTable('rbEquipment',
                                   filter='status=1 AND roleInIntegration in %s' % ((CEquipmentRoleInIntegration.external, CEquipmentRoleInIntegration.internal),)
                                  )

        self.actStatusObservationClient.setShortcut('Shift+F5')
        self.txtClientInfoBrowser.actions.append(self.actEditClient)
        self.txtClientInfoBrowser.actions.append(self.actStatusObservationClient)
        self.addObject('qshcStatusObservationClient', QtGui.QShortcut('Shift+F5', self.txtClientInfoBrowser, self.on_actStatusObservationClient_triggered))
        self.actEditClient.setEnabled(QtGui.qApp.userHasAnyRight([urAdmin, urRegTabWriteRegistry, urRegTabReadRegistry]))
        self.actStatusObservationClient.setEnabled(QtGui.qApp.userHasAnyRight([urAdmin, urEditStatusObservationClient]))
        self.qshcStatusObservationClient.setContext(Qt.WidgetShortcut)

        self.setModels(self.tblActions, self.modelActions, self.selectionModelActions)
        self.setModels(self.tblProps, self.modelActionProperties, self.selectionModelActionProperties)
        self.mapActionIdToAction = {}
        self.mapActionIdToDateChangePossibility = {}
        self.actualByTissueType = {}
        self.actionIdWithTissue = []
        self.eventEditor = None
        self.actionTemplateCache = None
        self._counterId = None
        self.mapActionIdToStaticAction = {}
        self.rtProcessingCache = {}

        self.buttonBox.addButton(self.btnPrint, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnApplyModifier, QtGui.QDialogButtonBox.ActionRole)
        self.btnApplyModifier.setDefault(True)
        self.btnApplyModifier.setAutoDefault(True)

        self.tblActions.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)

        # popupMenu tblActions
        self.tblActions.addPopupAction(self.actSelectAllRowActions)
        self.tblActions.addPopupAction(self.actClearSelectionRowActions)
        self.tblActions.addPopupAction(self.actChangeValueActions)
        self.tblActions.addPopupSeparator()
        self.tblActions.addPopupAction(self.actAddActions)
        self.tblActions.addPopupAction(self.actDetachActions)
        self.tblActions.addPopupAction(self.actDelAddedActions)

        self.actChangeValueCurrentAction.setShortcut('F2')
        self.actAddActions.setShortcut('F9')

        self.addAction(self.actChangeValueCurrentAction)
        self.addAction(self.actAddActions)
        self.addAction(self.actScanBarcode)

        self.mnuLoadPrevAction.addAction(self.actLoadSameSpecialityPrevAction)
        self.mnuLoadPrevAction.addAction(self.actLoadOwnPrevAction)
        self.mnuLoadPrevAction.addAction(self.actLoadAnyPrevAction)
        self.btnLoadPrevAction.setMenu(self.mnuLoadPrevAction)

        action = QtGui.QAction(self)
        self.addObject('actSetLaboratoryCalculatorInfo', action)
        action.setShortcut('F3')
        self.addAction(action)
        self.connect(self.actSetLaboratoryCalculatorInfo, SIGNAL('triggered()'), self.on_actSetLaboratoryCalculatorInfo)

        #defaults
        self.cmbTissueExecPerson.setValue(QtGui.qApp.userId)

        currentDateTime = QDateTime.currentDateTime()
        self.edtTissueDate.setDate(currentDateTime.date())
        self.edtTissueTime.setTime(currentDateTime.time())

        self.setupDirtyCather()
        QtGui.qApp.setCounterController(CCounterController(self))
        self.btnAmbCard.setEnabled(QtGui.qApp.userHasRight(urReadJobTicketMedKart))

    def checkNeedLaboratoryCalculator(self, propertyTypeList, clipboardSlot):
        actualPropertyTypeList = [propType for propType in propertyTypeList if validCalculatorSettings(propType.laboratoryCalculator)]
        if actualPropertyTypeList:
            QtGui.qApp.connectClipboard(clipboardSlot)
        else:
            QtGui.qApp.disconnectClipboard()
        return actualPropertyTypeList

    def on_actSetLaboratoryCalculatorInfo(self):
        result = self.checkNeedLaboratoryCalculator(self.modelActionProperties.propertyTypeList,
                                                    self.on_laboratoryCalculatorClipboard)
        self._canUseLaboratoryCalculatorPropertyTypeList = result
        self.setInfoToLaboratoryCalculatorClipboard()

    def setInfoToLaboratoryCalculatorClipboard(self):
        def chooseLabCode(propType):
            code = propType.laboratoryCalculator
            if code in ('LL*', 'GG*', 'EE*', 'CI*'):
                return '%s%s'%(code, unicode(self.modelActionProperties.action.getPropertyById(propType.id).getValue()))
            else:
                return code
        if self._canUseLaboratoryCalculatorPropertyTypeList:
            propertyTypeList = self._canUseLaboratoryCalculatorPropertyTypeList
            #actual = unicode('; '.join(['('+','.join([forceString(propType.id), propType.laboratoryCalculator, propType.name])+')' for propType in propertyTypeList]))
            actual = unicode('; '.join(['('+','.join([forceString(propType.id),
                chooseLabCode(propType),
                propType.name])+')' for propType in propertyTypeList]))
            mimeData = QMimeData()
            mimeData.setData(QtGui.qApp.inputCalculatorMimeDataType,
                             QString(actual).toUtf8())
            QtGui.qApp.clipboard().setMimeData(mimeData)
            self._mainWindowState = QtGui.qApp.mainWindow.windowState()
            QtGui.qApp.mainWindow.showMinimized()

    def on_laboratoryCalculatorClipboard(self):
        mimeData = QtGui.qApp.clipboard().mimeData()
        baData = mimeData.data(QtGui.qApp.outputCalculatorMimeDataType)
        if baData:
            QtGui.qApp.mainWindow.setWindowState(self._mainWindowState)
            data = forceString(QString.fromUtf8(baData))
            self.modelActionProperties.setLaboratoryCalculatorData(data)

    @property
    def needUpdateAfterClose(self):
        return bool(self.actionIdListCanDeleted) or self._detachedActionsExists

    def getMaxCourseNumber(self):
        return self._maxCourseNumber

    def isLastCoursePart(self):
        return self._courseNumber == self._maxCourseNumber

    def isCoursePassed(self, courseNumber):
        return courseNumber < self._courseNumber

    def canFillMenstrualDay(self, clientSex):
        if clientSex == 1:
            self.chkTissueMenstrualDay.setEnabled(False)

    @property
    def courseNumber(self):
        return self._courseNumber

    def getClientId(self):
        return self.clientId

    def _getLoadedActions(self):
        return self.mapActionIdToAction.values() + self.mapActionIdToStaticAction.values()

    def exec_(self):
        result = CItemEditorBaseDialog.exec_(self)
        if result:
            QtGui.qApp.delAllCounterValueIdReservation()
        else:
            QtGui.qApp.resetAllCounterValueIdReservation()
            QtGui.qApp.setCounterController(None)
        return result

    def getPrevActionId(self, action, type):
        return self.getPrevActionIdHelper.getPrevActionId(action, type)

    def loadPrevAction(self, type):
        model = self.tblActions.model()
        row = self.tblActions.currentIndex().row()
        if QtGui.qApp.userHasRight(urCopyPrevAction) and 0<=row<len(model.idList()):
            actionId = self.modelActions.idList()[row]
            action = self.mapActionIdToAction[actionId]
            prevActionId = self.getPrevActionId(action, type)
            if prevActionId:
                action.updateByActionId(prevActionId)
                self.tblProps.model().emitDataChanged()
                self.tblProps.resizeRowsToContents()


    @pyqtSignature('')
    def on_actStatusObservationClient_triggered(self):
        self.updateStatusObservationClient()


    def updateStatusObservationClient(self):
        if QtGui.qApp.userHasAnyRight([urAdmin, urEditStatusObservationClient]):
            try:
                if self.clientId:
                    dialog = CStatusObservationClientEditor(self, [self.clientId])
                    try:
                        if dialog.exec_():
                            self.updateClientInfo()
                    finally:
                        dialog.deleteLater()
            except:
                pass


    @pyqtSignature('')
    def on_btnApplyModifier_clicked(self):
        if self.isTakenTissue:
            self.on_btnPrintTissueLabel_clicked()
        else:
            self.on_btnApplyJobTypeModifier_clicked()


    @pyqtSignature('double')
    def on_modelActionProperties_actionAmountChanged(self, value):
        index = self.tblActions.currentIndex()
        if index.isValid():
            row = index.row()
            actionId = self.modelActions.idList()[row]
            action = self.mapActionIdToAction[actionId]
            action.getRecord().setValue('amount', QVariant(value))


    @pyqtSignature('')
    def on_actDelAddedActions_triggered(self):
        self.tblActions.removeSelectedRows()
        self.resetProbesTree()

    @pyqtSignature('')
    def on_actDetachActions_triggered(self):
        if QtGui.QMessageBox().warning(
            self, u"Внимание!", u"Отмененное действие можно будет вернуть только через редактор события!\nПродолжить?",
            QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel, QtGui.QMessageBox.Cancel
        ) != QtGui.QMessageBox.Ok:
            return


        db = QtGui.qApp.db

        actionIdList = self.tblActions.selectedItemIdList()

        tmpl = """
        DELETE FROM ActionProperty_Job_Ticket
        WHERE value = %d
        AND id IN (
          SELECT ActionProperty.id FROM ActionProperty
          INNER JOIN Action ON Action.id = ActionProperty.action_id
          INNER JOIN ActionPropertyType ON ActionPropertyType.id = ActionProperty.type_id
          WHERE ActionPropertyType.typeName = \'JobTicket\'
          AND Action.id IN (%s)
        )
        """
        db.transaction()
        try:
            stmt = tmpl % (self.jobTicketId(), ','.join([str(v) for v in actionIdList]))
            db.query(stmt)
            for actionId in actionIdList:
                if actionId in self.mapActionIdToAction:
                    del self.mapActionIdToAction[actionId]
                if actionId in self.mapActionIdToDateChangePossibility:
                    del self.mapActionIdToDateChangePossibility[actionId]
                if actionId in self.modelActions.recordCache().map:
                    del self.modelActions.recordCache().map[actionId]
                if actionId in self.modelActions.recordCache().queue:
                    self.modelActions.recordCache().queue.remove(actionId)
                if actionId in self.modelActions.idList():
                    self.modelActions.idList().remove(actionId)

            self.modelActions.reset()

            self._detachedActionsExists = True

        except:
            QtGui.qApp.db.rollback()
            raise

        else:
            QtGui.qApp.db.commit()

        self._maxCourseNumber = 1
        for action in self.mapActionIdToAction.values():
            maxPropertiesCourse = action.maxPropertiesCourse()
            if self._maxCourseNumber < maxPropertiesCourse:
                self._maxCourseNumber = maxPropertiesCourse

        self.resetProbesTree()

    @pyqtSignature('int')
    def on_btnPrint_printByTemplate(self, templateId):
        context = CInfoContext()
        # if templateId in (printAction.id for printAction in self.btnPrint.additionalActions()): # хз
        if templateId in (self.btnPrint.additionalActions()): # хз
            self.additionalPrint(context, templateId)
        else:
            jobTicketId = self.itemId()
            makeDependentActionIdList([jobTicketId])
            presetActions = tuple([action for action in self.mapActionIdToAction.values()])
            jobTicketInfo = context.getInstance(CJobTicketWithActionsInfo, jobTicketId, presetActions=presetActions)
            action = self.modelActionProperties.action
            actionId = action.getId()
            actionRecord = action.getRecord()
            eventId = forceRef(actionRecord.value('event_id'))
            eventInfo = context.getInstance(CEventInfo, eventId)

            eventActions = eventInfo.actions
            eventActions.load()
            try:
                currentActionIndex = eventActions._idList.index(actionId)
                actionInfo = CCookedActionInfo(context, actionRecord, action)
                eventActions._items[currentActionIndex] = actionInfo
            except:
                currentActionIndex = -1
                actionInfo = None
            data = { 'jobTicket' : jobTicketInfo,
                     'event': eventInfo,
                     'action': actionInfo,
                     'client': eventInfo.client,
                     }
            applyTemplate(self, templateId, data, signAndAttachHandler=self.btnAttachedFiles.getSignAndAttachHandler())


    def additionalPrint(self, context, templateId):
        action = self.modelActionProperties.action
        actionId  = action.getId()
        actionRecord = action.getRecord()
        eventId = forceRef(actionRecord.value('event_id'))
        eventInfo = context.getInstance(CEventInfo, eventId)

        eventActions = eventInfo.actions
        eventActions.load()
        try:
            currentActionIndex = eventActions._idList.index(actionId)
            actionInfo = CCookedActionInfo(context, actionRecord, action)
            eventActions._items[currentActionIndex] = actionInfo
        except:
            currentActionIndex = -1
            actionInfo = None
        data = { 'event' : eventInfo,
                 'action': actionInfo,
                 'client': eventInfo.client,
                 'actions':eventActions,
                 'currentActionIndex': currentActionIndex,
                 'tempInvalid': None
               }
        applyTemplate(self, templateId, data, signAndAttachHandler=self.btnAttachedFiles.getSignAndAttachHandler())


    def setRecord(self, record):
        CItemEditorBaseDialog.setRecord(self, record)
        dateTime = forceDateTime(record.value('datetime'))
        begDateTime = forceDateTime(record.value('begDateTime'))
        self.date = dateTime.date()
        self.datetime = begDateTime if begDateTime.date() else dateTime
        self.lblDatetimeValue.setText(forceString(dateTime))
        setLineEditValue( self.edtLabel,  record, 'label')
        setRBComboBoxValue(self.cmbOrgStructure,  record, 'orgStructure_id')
        setLineEditValue( self.edtNote,   record, 'note')
        setRBComboBoxValue( self.cmbStatus, record, 'status')
        setDatetimeEditValue(self.edtBegDate, self.edtBegTime, record, 'begDateTime')
        setDatetimeEditValue(self.edtEndDate, self.edtEndTime, record, 'endDateTime')

        self._jobId = forceRef(record.value('master_id'))
        self.setJobInfo(self._jobId)
        self.setDateTimeByStatus(self.cmbStatus.value())
        self.modelJobTicketProbe.setOrgStructureId(forceRef(record.value('orgStructure_id')))
        self.setupActions()
        self.loadTakenTissue()
        self.setIsDirty(False)


    def applyDependents(self, actionId, action):
        self.actionIdListCanDeleted.append(actionId)
        self.mapActionIdToAction[actionId] = action


    def getTakenTissueId(self):
        if self.takenTissueRecord:
            return forceRef(self.takenTissueRecord.value('id'))
        return None

    def _fromRecordToRecord(self, source, target=None, excludeFields=None):
        if target is None:
            target = QtGui.qApp.db.table('Job_Ticket').newRecord()

        for fieldIndex in xrange(source.count()):
            fieldName = source.fieldName(fieldIndex)
            if fieldName == 'id' or (excludeFields and fieldName in excludeFields):
                continue
            # Создам новый объект QVariant. Вот не знаю может ли где изменится
            # его значение по ссылке в оригинальном наборе записей.
            target.setValue(fieldName, QtCore.QVariant(source.value(fieldName)))
        return target


    def getRecord(self):
        record = CItemEditorBaseDialog.getRecord(self)
        self._cachedRecord = self._fromRecordToRecord(record)
        getLineEditValue( self.edtLabel,  record, 'label')
        getRBComboBoxValue(self.cmbOrgStructure,  record, 'orgStructure_id')
        getLineEditValue( self.edtNote,   record, 'note')

        currentStatus = forceInt(record.value('status'))
        getRBComboBoxValue( self.cmbStatus, record, 'status')
        newStatus = forceInt(record.value('status'))
        self._jobTicketWasClosed = newStatus != currentStatus and newStatus == CJobTicketStatus.done
        if currentStatus != newStatus and newStatus == CJobTicketStatus.enqueued:
            record.setValue('registrationDateTime', toVariant(QDateTime.currentDateTime()))
        if currentStatus != newStatus and newStatus == CJobTicketStatus.wait:
            record.setNull('registrationDateTime')

        getDatetimeEditValue(self.edtBegDate, self.edtBegTime, record, 'begDateTime', True)
        getDatetimeEditValue(self.edtEndDate, self.edtEndTime, record, 'endDateTime', True)

        if QtGui.qApp.needSaveTissueOnSaveJT():
            self.saveTakenTissueRecord()

        return record


    def getRTProcessingValue(self,  tissueTypeId):
        if not tissueTypeId:
            return 0
        if tissueTypeId not in self.rtProcessingCache:
            self.rtProcessingCache[tissueTypeId] = forceInt(QtGui.qApp.db.translate('rbTissueType', 'id', tissueTypeId, 'isRealTimeProcessing'))
        return self.rtProcessingCache[tissueTypeId]

    def findExistsExternalId(self, takenExternalId, probeExternalIdList, tissueTypeId, date):
        db = QtGui.qApp.db
        tableTTJ = db.table('TakenTissueJournal')
        tableProbe = db.table('Probe')
        begDate, endDate = self.getTissueIdPeriod(tissueTypeId, date)
        if takenExternalId:
            cond = [
                tableTTJ['externalId'].eq(takenExternalId),
                tableTTJ['tissueType_id'].eq(tissueTypeId),
                tableTTJ['deleted'].eq(0)
            ]
            if begDate and endDate:
                cond.append(tableTTJ['datetimeTaken'].dateBetween(begDate, endDate))
            ttjList = [forceString(r.value(0)) for r in db.getRecordList(tableTTJ, tableTTJ['externalId'], where=cond)]
        else:
            ttjList = []
        table = tableProbe.innerJoin(tableTTJ, tableProbe['takenTissueJournal_id'].eq(tableTTJ['id']))
        cond = [
            tableProbe['externalId'].inlist(probeExternalIdList),
            tableTTJ['tissueType_id'].eq(tissueTypeId),
            tableTTJ['deleted'].eq(0)
        ]
        if begDate and endDate:
            cond.append(tableTTJ['datetimeTaken'].dateBetween(begDate, endDate))
        pList = [forceString(r.value(0)) for r in db.getRecordListGroupBy(table, tableProbe['externalId'], where=cond, group='externalId')]
        return list(set(ttjList + pList))

    def saveTakenTissueRecord(self):
        if self.isTakenTissue:# and self.cmbStatus.value() == CJobTicketStatus.done:
            tissueTypeId = self.cmbTissueType.value()
            canBeSaved = bool(not self.takenTissueRecord) and bool(tissueTypeId)
            if canBeSaved:#комбобокс с тканями ограничен по ActionType_TissueType
                db = QtGui.qApp.db
                table = db.table('TakenTissueJournal')
                record = table.newRecord()
                record.setValue('client_id', QVariant(self.clientId))
                record.setValue('tissueType_id', QVariant(tissueTypeId))
#                externalIdValue = self.recountTissueExternalId()
#                record.setValue('externalId', QVariant(externalIdValue))
                record.setValue('externalId', QVariant(self.edtTissueExternalId.text()))
                record.setValue('number', QVariant(self.edtTissueNumber.text()))
                record.setValue('amount', QVariant(self.edtTissueAmount.value()))
                if self.edtTissueMenstrualDay.isEnabled():
                    record.setValue('menstrualDay', QVariant(self.edtTissueMenstrualDay.value()))
                record.setValue('unit_id', QVariant(self.cmbTissueUnit.value()))
                execPersonId = self.cmbTissueExecPerson.value()
                if not execPersonId:
                    execPersonId = QtGui.qApp.userId
                record.setValue('execPerson_id', QVariant(execPersonId))
                record.setValue('note', QVariant(self.edtTissueNote.text()))
                record.setValue('course', self._courseNumber)
                if self.firstTTJR is not None:
                    # Если курсовой забор, то мы выстраиваем цепочки потомков у первого забора.
                    # Через первый забор мы свяжем набор заборов с набором действий.
                    record.setValue('parent_id', self.firstTTJR.value('id'))
                datetimeTaken = QDateTime()
                datetimeTaken.setDate(self.edtTissueDate.date())
                datetimeTaken.setTime(self.edtTissueTime.time())
                record.setValue('datetimeTaken', QVariant(datetimeTaken))
                recordId = db.insertRecord(table, record)
                if self.firstTTJR is None:
                    # Для дюбого первого забора подкинем связь на самого себя.
                    # Это унифицирует ситуацию как для курса так и для всего остального
                    # при линковании с Action-ами будет проще вытащить все нужные записи.
                    # SELECT TakenTissueJournal.* FROM TakenTissueJournal
                    # INNER JOIN TakenTissueJournal AS MainTTJ ON TakenTissueJournal.parent_id=MainTTJ.id
                    # WHERE MainTTJ.id = Action.id
                    record.setValue('parent_id', QVariant(recordId))
                    db.updateRecord(table, record)
                self.takenTissueRecord = record
                self.setTissueWidgetsEditable(False)
                return True
        return False


    def saveInternals(self, id):
        self._saveInternals(id)
        if self._jobTicketWasClosed or self.execCourse in [CCourseStatus.skipRefusalClient, CCourseStatus.skipRefusalMO]:
            self._checkJobActionsExecutionPlan(id)
            # self._checkPrematurelyClosing(id)
            # self._updateOrgStructureIdForAction(id)
        self.afterRemoveJobTicket()


    def afterRemoveJobTicket(self):
        if self._cachedFreeJobTicket:
            db = QtGui.qApp.db
            tableJobTicket = db.table('Job_Ticket')
            records = db.getRecordList(tableJobTicket, '*', [tableJobTicket['id'].inlist(self._cachedFreeJobTicket), tableJobTicket['deleted'].eq(0)])
            for record in records:
                record.setValue('status', toVariant(CJobTicketStatus.wait))
                record.setValue('begDateTime', toVariant(None))
                record.setValue('endDateTime', toVariant(None))
                record.setValue('orgStructure_id', toVariant(None))
                db.updateRecord(tableJobTicket, record)


    def afterSave(self):
        jobTicketId = self.itemId()
        if jobTicketId:
            for action in self.mapActionIdToAction.values():
                record = action.getRecord()
                actionType = action.getType()
                if record and actionType and actionType.hasJobTicketPropertyType():
                    record.setValue('orgStructure_id', toVariant(action.getJobTicketOrgStructureId(jobTicketId=jobTicketId, cachedFreeJobTicket=self._cachedFreeJobTicket)))
                action.save(idx=-1, checkModifyDate=False)
#        self._cachedUpdateJobTicket = {}
#        self._cachedChangeJobTicket = []
        self._cachedFreeJobTicket = []


    def getPrematurelyClosingThreshold(self, jobTicketId):
        if not jobTicketId:
            return 0
        db = QtGui.qApp.db
        tableJobTicket = db.table('Job_Ticket')
        tableJob = db.table('Job')
        tableJobPurpose = db.table('rbJobPurpose')
        queryTable = tableJobTicket.innerJoin(tableJob, tableJob['id'].eq(tableJobTicket['master_id']))
        queryTable = queryTable.innerJoin(tableJobPurpose, tableJobPurpose['id'].eq(tableJob['jobPurpose_id']))
        cond = [tableJobTicket['id'].eq(jobTicketId), tableJobTicket['deleted'].eq(0), tableJob['deleted'].eq(0)]
        record = db.getRecordEx(queryTable, tableJobPurpose['prematurelyClosingThreshold'], cond)
        return forceInt(record.value('prematurelyClosingThreshold')) if record else 0


    def _saveInternals(self, id):
        takenTissueEnabled = self.isTakenTissue and bool(self.takenTissueRecord)
        for action in self.mapActionIdToAction.values():
            record = action.getRecord()
            actionId = forceRef(record.value('id'))

            actualByTissueTypeList, actionIdList = self.actualByTissueType.get(self.cmbTissueType.value(), ([], []))
            if takenTissueEnabled and actionId in actionIdList:
                if self.firstTTJR is None:
                    # Это значит что мы регистрируем первый забор в курсе. Если у нас курсовой забор, конечно.
                    # Иначе все работает как по старому, так как забор все равно один.
                    record.setValue('takenTissueJournal_id', self.takenTissueRecord.value('id'))
            record.setValue('expose', QVariant(1))
            if takenTissueEnabled and forceInt(record.value('status')) in (CActionStatus.finished, CActionStatus.withoutResult):
                action = self.freeJobTicket(action, forceDateTime(self.takenTissueRecord.value('datetimeTaken')))
            elif forceInt(record.value('status')) == CActionStatus.finished:  # and not self.isTakenTissue:
                action = self.freeJobTicket(action)

            # idx=-1 значит что мы не меняем этот параметр. Наверное нужно использовать None
            action.save(idx=-1, checkModifyDate=False)

        if takenTissueEnabled:
            takenTissueJournalId = forceRef(self.takenTissueRecord.value('id'))
            actionTakenTissueJournalId = forceRef(self.takenTissueRecord.value('parent_id'))
            checkTissueJournalStatus(takenTissueJournalId, actionTakenTissueJournalId)


    def freeJobTicket(self, action, dateTimeExecJob=None):
        if action and not action.getJobTicketChange():
            jobTicketIdList = []
            for property in action.getType()._propertiesById.itervalues():
                if property.isJobTicketValueType():
                    jobTicketId = action[property.name]
                    if jobTicketId and jobTicketId not in jobTicketIdList:
                        jobTicketIdList.append(jobTicketId)
            for jobTicketId in jobTicketIdList:
                if jobTicketId: #and jobTicketId not in self._cachedChangeJobTicket:
                    prematurelyClosingThreshold = self.getPrematurelyClosingThreshold(jobTicketId)
                    if prematurelyClosingThreshold > 0 and prematurelyClosingThreshold <= 24:
                        record = action.getRecord()
                        actionTypeId = forceRef(record.value('actionType_id'))
                        if actionTypeId:
                            actionType = CActionTypeCache.getById(actionTypeId)
                            if actionType:
                                db = QtGui.qApp.db
                                showTime = actionType.showTime
                                if dateTimeExecJob:
                                    endDate = dateTimeExecJob if showTime else dateTimeExecJob.date()
                                    dateTimeDoneJob = dateTimeExecJob
                                else:
                                    endDate = forceDateTime(record.value('endDate')) if showTime else forceDate(record.value('endDate'))
                                    dateTimeDoneJob = forceDateTime(record.value('endDate'))
    #                            updateJobTicketId, updateEndDate = self._cachedUpdateJobTicket.get(jobTicketId, (None, None))
    #                            if not endDate:
    #                                endDate = updateEndDate
                                tableJobTicket = db.table('Job_Ticket')
                                cond = [tableJobTicket['id'].eq(jobTicketId),
                                        tableJobTicket['deleted'].eq(0)
                                        ]
                                if endDate:
                                    cond.append(tableJobTicket['datetime'].dateGe(endDate))
                                else:
                                    return action
                                records = db.getRecordList(tableJobTicket, '*', cond)
                                for recordJT in records:
                                    datetime = forceDateTime(recordJT.value('datetime')) if showTime else forceDate(recordJT.value('datetime'))
                                    jobTicketId = forceRef(recordJT.value('id'))
                                    if jobTicketId and datetime > endDate:
                                        stmt = 'SELECT DATE_ADD(\'{0}\', INTERVAL {1} HOUR) > Job_Ticket.datetime FROM Job_Ticket WHERE id = {2}'.format(unicode(endDate.toString('yyyy-MM-dd H:mm')), prematurelyClosingThreshold, jobTicketId)
                                        query = db.query(stmt)
                                        if query.first() and not forceBool(query.value(0)):
                                            for property in action.getType()._propertiesById.itervalues():
                                                if property.isJobTicketValueType() and property.valueType.initPresetValue:
                                                    if jobTicketId == action[property.name]:
                                                        prop = action.getPropertyById(property.id)
                                                        if prop and prop._type:
        #                                                    if updateJobTicketId:
        #                                                        prop._value = updateJobTicketId
        #                                                    else:
                                                            prop._type.valueType.setIsExceedJobTicket(True)
                                                            prop._type.valueType.setIsNearestJobTicket(True)
                                                            prop._type.valueType.setPrematurelyClosingThreshold(prematurelyClosingThreshold)
                                                            if self._jobOrgStructureId:
                                                                prop._type.valueType.setExecOrgStructureId(self._jobOrgStructureId)
                                                            if self._jobPurposeId:
                                                                prop._type.valueType.setExecJobPurposeId(self._jobPurposeId)
                                                            prop._type.valueType.setDateTimeExecJob(dateTimeExecJob)
                                                            QtGui.qApp.setJTR(self)
                                                            try:
                                                                prop._value = prop._type.valueType.getPresetValueWithoutAutomatic(action, isFreeJobTicket=True)
                                                                prop._type.valueType.resetParams()
                                                                prop._changed = True
                                                                action.setJobTicketChange(True)
                                                            finally:
                                                                QtGui.qApp.unsetJTR(self)
                                                            if action[property.name] and jobTicketId != action[property.name]:
                                                                if jobTicketId not in self._cachedFreeJobTicket:
                                                                    self._cachedFreeJobTicket.append(jobTicketId)
        #                                                        if jobTicketId not in self._cachedUpdateJobTicket.keys():
        #                                                            self._cachedUpdateJobTicket[jobTicketId] = (action[property.name], endDate)
        #                                                        if action[property.name] and action[property.name] not in self._cachedChangeJobTicket:
        #                                                            self._cachedChangeJobTicket.append(action[property.name])
                                                                newRecord = db.getRecord(tableJobTicket, '*', action[property.name])
                                                                self.setFreeRecord(newRecord, dateTimeDoneJob)
                                                                self.setIsDirty(False)
                                                                self.modelActionProperties.reset()
        return action


    def setFreeRecord(self, record, dateTimeDoneJob=None):
        CItemEditorBaseDialog.setRecord(self, record)
        dateTime = forceDateTime(record.value('datetime'))
        begDateTime = forceDateTime(record.value('begDateTime'))
        self.date = dateTime.date()
        self.datetime = begDateTime if begDateTime.date() else dateTime
        self.lblDatetimeValue.setText(forceString(dateTime))
        setLineEditValue( self.edtLabel,  record, 'label')
        orgStructureId = forceRef(record.value('orgStructure_id'))
        if not orgStructureId:
            orgStructureId = QtGui.qApp.currentOrgStructureId()
        self.cmbOrgStructure.setValue(orgStructureId)
        setLineEditValue( self.edtNote,   record, 'note')
        setRBComboBoxValue( self.cmbStatus, record, 'status')
        takenTissueEnabled = self.isTakenTissue and bool(self.takenTissueRecord)
        if dateTimeDoneJob and takenTissueEnabled:
            self.edtBegDate.setDate(dateTimeDoneJob.date())  # 0013620:0052836
            self.edtBegTime.setTime(dateTimeDoneJob.time())  # 0013620:0052836
            if self.cmbStatus.value() == CJobTicketStatus.done:  # 0013620:0052836
                self.edtEndDate.setDate(dateTimeDoneJob.date())
                self.edtEndTime.setTime(dateTimeDoneJob.time())
        else:
            setDatetimeEditValue(self.edtBegDate, self.edtBegTime, record, 'begDateTime')
            setDatetimeEditValue(self.edtEndDate, self.edtEndTime, record, 'endDateTime')


    def _checkPrematurelyClosing(self, jobTicketId):
        if forceRef(self._record.value('masterJobTicket_id')):
            return

        endDateTime = forceDateTime(self._record.value('endDateTime'))
        if not endDateTime or not endDateTime.isValid():
            return

        db = QtGui.qApp.db

        tableJobTicket = db.table('Job_Ticket')
        tableJob = db.table('Job')
        tableJobPurpose = db.table('rbJobPurpose')

        queryTable = tableJobTicket \
            .innerJoin(tableJob, tableJob['id'].eq(tableJobTicket['master_id'])) \
            .innerJoin(tableJobPurpose, tableJobPurpose['id'].eq(tableJob['jobPurpose_id']))

        record = db.getRecordEx(queryTable, tableJobPurpose['prematurelyClosingThreshold'],
                                tableJobTicket['id'].eq(jobTicketId))
        if not record:
            return

        prematurelyClosingThreshold = forceInt(record.value('prematurelyClosingThreshold'))
        if prematurelyClosingThreshold == 0:
            return

        stmt = 'SELECT DATE_ADD(\'{0}\', INTERVAL {1} HOUR) > Job_Ticket.datetime FROM Job_Ticket WHERE id = {2}' \
            .format(unicode(endDateTime.toString('yyyy-MM-dd H:mm')), prematurelyClosingThreshold, jobTicketId)

        query = db.query(stmt)
        if not query.first():
            return

        if forceBool(query.value(0)):
            return

        if self._jobPurposeId:
            order = 'Job.jobPurpose_id <=> {0}'.format(self._jobPurposeId)
        else:
            order = ''

        newJobRecord = db.getRecordEx(tableJob, tableJob['id'],
                                      [tableJob['deleted'].eq(0),
                                       tableJob['jobType_id'].eq(self._jobTypeId),
                                       tableJob['date'].dateEq(endDateTime),
                                       tableJob['orgStructure_id'].eq(self._jobOrgStructureId)],
                                      order=order)

        if newJobRecord:
            jobId = forceRef(newJobRecord.value('id'))
        else:
            jobId = self._jobId

        exceedJobTicketRecord = createNewExceedJobTicketRecord(jobId, tableJobTicket, storeIdx=False)

        self._fromRecordToRecord(
            self._record, exceedJobTicketRecord,
            excludeFields=('idx', 'master_id', 'datetime', 'isExceedQuantity', 'masterJobTicket_id', 'status', 'registrationDateTime')
        )
        exceedJobTicketRecord.setValue('status', CJobTicketStatus.done)
        db.updateRecord(tableJobTicket, exceedJobTicketRecord)

        stmt = "UPDATE ActionProperty_Job_Ticket SET value = {0} WHERE value = {1}" \
            .format(forceRef(exceedJobTicketRecord.value('id')), jobTicketId)
        db.query(stmt)

        self._cachedRecord.setValue('status', QVariant(CJobTicketStatus.wait))
        self._cachedRecord.setValue('begDateTime', QVariant(None))
        self._cachedRecord.setValue('endDateTime', QVariant(None))
        self._cachedRecord.setValue('orgStructure_id', QVariant(None))
        self._fromRecordToRecord(self._cachedRecord, self._record)
        db.updateRecord(tableJobTicket, self._record)


    def fillPropertyValueForTakenTissue(self):
        if self.isTakenTissue and self.cmbTissueType.value():
            for action in self.mapActionIdToAction.values():
                record = action.getRecord()
                actionId = forceRef(record.value('id'))
                actualByTissueTypeList, actionIdList = self.actualByTissueType.get(self.cmbTissueType.value(), ([], []))
                if actionId in actionIdList:
                    actionType = action.getType()
                    propertyTypeList = [propertyType for propertyType in actionType.getPropertiesByName().values() if propertyType.typeName == u'Проба' and propertyType.visibleInJobTicket]
                    for propertyType in propertyTypeList:
                        property = action.getPropertyById(propertyType.id)
                        value = property.getValue()
                        if not value:
                            value = unicode(self.edtTissueExternalId.text()).lstrip('0')
#                            value = unicode(self.tissueExternalIdForProperty)
                            property.setValue(value)
                            self.modelActionProperties.emitDataChanged()


    def checkDataEntered(self):
        result = True
        result = result and self.checkMorphologyMKB()
        if self.isTakenTissue and QtGui.qApp.needSaveTissueOnSaveJT():
            result = result and self.checkUniqueTissueExternalId()
        result = result and self.checkActionsValue()
        return result


    def checkActionsValue(self):
        def isNull(val, typeName):
            if val is None:
                return True
            if isinstance(val, basestring):
                if typeName == 'ImageMap':
                    return 'object' not in val
                if typeName == 'Html':
                    edt = QtGui.QTextEdit()
                    edt.setHtml(val)
                    val = edt.toPlainText()
                if not trim(val):
                    return True
            if type(val) == list:
                if len(val) == 0:
                    return True
            if isinstance(val, (QDate, QDateTime, QTime)):
                return not val.isValid()
            return False

        actionsModel = self.modelActions
        for actionRow, actionId in enumerate(actionsModel.idList()):
            action = self.mapActionIdToAction[actionId]

            actionType = action.getType()
            propertyTypeList = actionType.getPropertiesById().items()
            propertyTypeList.sort(key=lambda x: (x[1].idx, x[0]))
            propertyTypeList = [x[1] for x in propertyTypeList if x[1].applicable(self.clientSex, self.clientAge) and x[1].visibleInJobTicket]

            actionEndDate = forceDate(action.getRecord().value('endDate'))

            for row, propertyType in enumerate(propertyTypeList):
                penalty = propertyType.penalty
                needChecking = penalty > 0 and (penalty < 50 and not actionEndDate.isNull() or penalty >= 50)
                if needChecking:
                    skippable = (penalty < 50 and not actionEndDate) or (50 <= penalty < 100)
                    property = action.getPropertyById(propertyType.id)
                    if isNull(property._value, propertyType.typeName):
                        actionTypeName = action._actionType.name
                        propertyTypeName = propertyType.name
                        if actionRow:
                            self.tblActions.setCurrentIndex(actionsModel.createIndex(actionRow, 0))
                        result = self.checkValueMessage(u'Необходимо заполнить значение свойства "%s" в действии "%s"' %(propertyTypeName, actionTypeName), skippable, self.tblProps, row, 1)
                        if not result:
                            return result
        return True


    def checkMorphologyMKB(self):
        if QtGui.qApp.defaultMorphologyMKBIsVisible():
            import re
            for row, actionId in enumerate(self.modelActions.idList()):
                action = self.mapActionIdToAction.get(actionId, None)
                if action:
                    actionType           = action.getType()
                    record               = action.getRecord()
                    defaultMKB           = actionType.defaultMKB
                    isMorphologyRequired = actionType.isMorphologyRequired
                    morphologyMKB        = forceString(record.value('morphologyMKB'))
                    status               = forceInt(record.value('status'))
                    isValidMorphologyMKB = bool(re.match('M\d{4}/', morphologyMKB))
                    if not isValidMorphologyMKB and defaultMKB > 0 and isMorphologyRequired > 0:
                        if status == CActionStatus.withoutResult and isMorphologyRequired == 2:
                            continue
                        skippable = True if isMorphologyRequired == 1 else False
                        message = u'Необходимо ввести корректную морфологию диагноза действия `%s`' % actionType.name
                        result = self.checkValueMessage(message, skippable, self.tblActions, row, column=4)
                        if not result:
                            return result
        return True


    def setJobInfo(self, jobId):
        db = QtGui.qApp.db
        record = db.getRecord('Job', '*', jobId)
        self._jobOrgStructureId = forceRef(record.value('orgStructure_id'))
        self._jobTypeId = forceRef(record.value('jobType_id'))
        self._jobPurposeId = forceRef(record.value('jobPurpose_id'))
        self.lblOrgStructureValue.setText(getOrgStructureName(self._jobOrgStructureId))
        self.lblJobTypeValue.setText(forceString(db.translate('rbJobType', 'id', self._jobTypeId, 'name')))

        self.actionStatusChanger = forceRef(db.translate('rbJobType', 'id', self._jobTypeId, 'actionStatusChanger'))
        self.actionPersonChanger = forceInt(db.translate('rbJobType', 'id', self._jobTypeId, 'actionPersonChanger'))
        self.actionDateChanger   = forceInt(db.translate('rbJobType', 'id', self._jobTypeId, 'actionDateChanger'))
        self.manualExecutionAssignments = forceRef(db.translate('rbJobType', 'id', self._jobTypeId, 'manualExecutionAssignments'))

    def setupActions(self):
        db = QtGui.qApp.db

        table       = db.table('Job_Ticket')
        tableAction = db.table('Action')

        queryTable, cond = self._getMainQueryTableAndCond()
        cond.append(table['id'].eq(self.itemId()))

        condStaticActions = list(cond)
        cond.append(tableAction['id'].inlist(self._actionIdList))
        if self._actionIdList:
            condStaticActions.append(tableAction['id'].notInlist(self._actionIdList))

        order = 'Action.id'

        actionIdList = []
        clientIdSet = set()
        fields = 'Action.id, Client.id'
        records = db.getRecordList(queryTable, fields, cond, order)
        for record in records:
            actionIdList.append(forceRef(record.value(0)))
            clientIdSet.add(forceRef(record.value(1)))
#        if len(clientIdSet) != 1:
#            raise Exception(u'Job_Ticket.id=%d применён неправильно (%d раз)', self.itemId(), len(len(clientIdSet)))
        if not clientIdSet and self.itemId():
            clientIdSet = self.getClientIdByJobTicketId(self.itemId())
        if self._defaultEventId is None:
            self.setDefaultEventId(self.itemId())
        self.setClientId(list(clientIdSet)[0] if len(clientIdSet) >= 1 else None)
        self.setActionIdList(actionIdList)
        self.checkIsTakenTissue(actionIdList)
        self.canFillMenstrualDay(self.clientSex)

        staticActionIdList = db.getDistinctIdList(queryTable, fields, condStaticActions, order)
        self.setStaticActionIdList(staticActionIdList)

        self.checkTakenTissueJournalCourse(actionIdList + staticActionIdList)

        self.resetProbesTree()


    def setDefaultEventId(self, jobTicketId):
        db = QtGui.qApp.db
        table       = db.table('Job_Ticket')
        tableAPJT   = db.table('ActionProperty_Job_Ticket')
        tableAP     = db.table('ActionProperty')
        tableAction = db.table('Action')
        tableEvent  = db.table('Event')

        queryTable = table
        queryTable = queryTable.leftJoin(tableAPJT,   tableAPJT['value'].eq(table['id']))
        queryTable = queryTable.leftJoin(tableAP,     tableAP['id'].eq(tableAPJT['id']))
        queryTable = queryTable.leftJoin(tableAction, tableAction['id'].eq(tableAP['action_id']))
        queryTable = queryTable.leftJoin(tableEvent,  tableEvent['id'].eq(tableAction['event_id']))

        cond = [table['id'].eq(jobTicketId),
                tableAction['deleted'].eq(0),
                tableEvent['deleted'].eq(0),
               ]

        recordList = db.getRecordList(queryTable, [tableEvent['client_id'].name(), tableEvent['id'].name()], cond)
        if recordList:
            record = recordList[0]
            self._defaultEventId = forceRef(record.value('id'))


    def getDefaultEventId(self):
        return self._defaultEventId


    def getClientIdByJobTicketId(self, jobTicketId):
        db = QtGui.qApp.db
        table       = db.table('Job_Ticket')
        tableAPJT   = db.table('ActionProperty_Job_Ticket')
        tableAP     = db.table('ActionProperty')
        tableAction = db.table('Action')
        tableEvent  = db.table('Event')


        queryTable = table
        queryTable = queryTable.leftJoin(tableAPJT,   tableAPJT['value'].eq(table['id']))
        queryTable = queryTable.leftJoin(tableAP,     tableAP['id'].eq(tableAPJT['id']))
        queryTable = queryTable.leftJoin(tableAction, tableAction['id'].eq(tableAP['action_id']))
        queryTable = queryTable.leftJoin(tableEvent,  tableEvent['id'].eq(tableAction['event_id']))

        cond = [table['id'].eq(jobTicketId),
                tableAction['deleted'].eq(0),
                tableEvent['deleted'].eq(0),
               ]

        recordList = db.getRecordList(queryTable, [tableEvent['client_id'].name(), tableEvent['id'].name()], cond)
        if recordList:
            record = recordList[0]
            self._defaultEventId = forceRef(record.value('id'))
            return [forceRef(record.value('client_id'))]
        self._defaultEventId = None
        return [None]


    def checkIsTakenTissue(self, actionIdList):
        db = QtGui.qApp.db
        tableAction = db.table('Action')
        tableActionType = db.table('ActionType')
        tableActionTypeTissueType = db.table('ActionType_TissueType')

        cond = [tableAction['id'].inlist(actionIdList)]

        queryTable = tableAction.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
        queryTable = queryTable.innerJoin(tableActionTypeTissueType,
                                          tableActionTypeTissueType['master_id'].eq(tableActionType['id']))

        fields = [tableActionType['id'].alias('actionTypeId'),
                  tableActionTypeTissueType['id'],
                  tableActionTypeTissueType['tissueType_id'],
                  tableActionTypeTissueType['jobType_id'],
                  tableAction['id'].alias('actionId'),
                  tableActionTypeTissueType['amount'].name(),
                  tableActionTypeTissueType['unit_id'].name()]

        stmt = db.selectDistinctStmt(queryTable, fields, where=cond,
                                     order=tableActionTypeTissueType['idx'].name())

        query = db.query(stmt)
        isTakenTissue = query.size() > 0
        self.isTakenTissue = isTakenTissue
        self.grpTissue.setVisible(isTakenTissue)
        self.btnFillPropertiesValue.setVisible(isTakenTissue)
        if isTakenTissue:
            tissueTypeList = []
            while query.next():
                record = query.record()
                tissueType = forceRef(record.value('tissueType_id'))
                jobTypeId = forceRef(record.value('jobType_id'))
                actionId = forceRef(record.value('actionId'))

                actualByTissueTypeList, actionIdList = self.actualByTissueType.get(tissueType, (None, None))
                if actualByTissueTypeList:
                    actualByTissueTypeList.append(record)
                    actionIdList.append(actionId)
                else:
                    self.actualByTissueType[tissueType] = ([record], [actionId])
                if tissueType not in tissueTypeList and (not jobTypeId or self._jobTypeId == jobTypeId):
                    tissueTypeList.append(tissueType)
                self.actionIdWithTissue.append(actionId)
            self.cmbTissueType.addFilterAnd(db.table('rbTissueType')['id'].inlist(tissueTypeList))
            if len(tissueTypeList):
                self.cmbTissueType.setValue(tissueTypeList[0])


    def checkSpecialityExists(self, cmbPersonFind, personId):
        specialityId = forceRef(QtGui.qApp.db.translate('Person', 'id', personId, 'speciality_id'))
        if not specialityId:
            cmbPersonFind.setSpecialityIndependents()


    def loadTakenTissue(self):
        if self.isTakenTissue:
            if self.takenTissueRecord:
                self.cmbTissueType.blockSignals(True)
                self.edtTissueDate.blockSignals(True)
                execPersonId = forceRef(self.takenTissueRecord.value('execPerson_id'))
                self.checkSpecialityExists(self.cmbTissueExecPerson, execPersonId)
                self.cmbTissueType.setValue(forceRef(self.takenTissueRecord.value('tissueType_id')))
                self.edtTissueExternalId.setText(forceString(self.takenTissueRecord.value('externalId')))
                self.edtTissueNumber.setText(forceString(self.takenTissueRecord.value('number')))
                self.edtTissueAmount.setValue(forceInt(self.takenTissueRecord.value('amount')))
                if forceInt(self.takenTissueRecord.value('menstrualDay')):
                    self.chkTissueMenstrualDay.setEnabled(True)
                    self.edtTissueMenstrualDay.setValue(forceInt(self.takenTissueRecord.value('menstrualDay')))
                self.cmbTissueUnit.setValue(forceRef(self.takenTissueRecord.value('unit_id')))
                self.cmbTissueExecPerson.setValue(execPersonId)
                self.edtTissueNote.setText(forceString(self.takenTissueRecord.value('note')))
                datetimeTaken = forceDateTime(self.takenTissueRecord.value('datetimeTaken'))
                self.edtTissueDate.setDate(datetimeTaken.date())
                self.edtTissueTime.setTime(datetimeTaken.time())
                if forceString(self.takenTissueRecord.value('externalId'))!=u'':
                    self.setTissueWidgetsEditable(False)
                else:
                    self.setTissueWidgetsEditable(True)
                    self.cmbTissueType.blockSignals(False)
                    self.edtTissueDate.blockSignals(False)

            else:
                self.setTissueWidgetsEditable(True)
                execPersonId = QtGui.qApp.userId
                self.checkSpecialityExists(self.cmbTissueExecPerson, execPersonId)
                self.cmbTissueExecPerson.setValue(execPersonId)
                self.on_edtTissueDate_dateChanged(self.edtTissueDate.date())


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
        self.cmbEquipment.setEnabled(val)
        self.btnFillPropertiesValue.setEnabled(val)


    def setClientId(self, clientId):
        self.clientId = clientId
        self.getPrevActionIdHelper.setClientId(clientId)
        self.updateClientInfo()


    def updateClientInfo(self):
        if self.clientId:
            clientInfo = getClientInfo(self.clientId, date=self.date)
            self.txtClientInfoBrowser.setHtml(getClientBanner(self.clientId, self.date))
            self.clientSex       = clientInfo.sexCode
            self.clientBirthDate = clientInfo.birthDate
            self.clientAge      = calcAgeTuple(self.clientBirthDate, self.date)
            cmbTissueTypeFilter = 'sex IN (0,%d)'%self.clientSex
        else:
            self.txtClientInfoBrowser.setText('')
            self.clientSex       = None
            self.clientBirthDate = QDate()
            self.clientAge       = None
            cmbTissueTypeFilter = '1'
        self.cmbTissueType.setFilter(cmbTissueTypeFilter)


    def setActionIdList(self, actionIdList):
        db = QtGui.qApp.db
        table = db.table('Action')
        actionRecords = db.getRecordList(table, '*', table['id'].inlist(actionIdList))
        for actionRecord in actionRecords:
            takenTissueJournalId = forceRef(actionRecord.value('takenTissueJournal_id'))
            if self.firstTTJR is None and takenTissueJournalId:
                self.firstTTJR = db.getRecord('TakenTissueJournal', '*', takenTissueJournalId)
            actionId = forceRef(actionRecord.value('id'))
            action = CAction(record=actionRecord)
            self.mapActionIdToAction[actionId] = action
            endDateNotValid = not forceDate(actionRecord.value('endDate'))
            self.mapActionIdToDateChangePossibility[actionId] = {'endDate': endDateNotValid}
            maxPropertiesCourse = action.maxPropertiesCourse()
            if self._maxCourseNumber < maxPropertiesCourse:
                self._maxCourseNumber = maxPropertiesCourse

        self.tblActions.setIdList(actionIdList)
        self.modelActions.setAllChecked()


    def checkTakenTissueJournalCourse(self, actionIdList):
        if not self.isCourseJobTicket:
            self.takenTissueRecord = self.firstTTJR
            return

        if self.firstTTJR is None:
            return

        db = QtGui.qApp.db

        firstTTJId = forceRef(self.firstTTJR.value('id'))

        stmt = """
        SELECT
          TakenTissueJournal.id,
          TakenTissueJournal.course,
          EXISTS (SELECT NULL FROM Probe WHERE takenTissueJournal_id = TakenTissueJournal.id) AS withProbes
        FROM TakenTissueJournal
        WHERE TakenTissueJournal.parent_id = %d
        """ % firstTTJId

        courseToProbeExists = {}
        query = db.query(stmt)
        while query.next():
            takenTissueJournalId = forceRef(query.value(0))
            course = forceInt(query.value(1))
            withProbes = forceBool(query.value(2))
            self._courseNumber2TakenTissueRecordId[course] = takenTissueJournalId
            courseToProbeExists[course] = withProbes

        # Так как в этом месте мы уже получили проверку что firstTTJR существует,
        # Значит предыдущий запрос точно что-то вернул.

        course = max(courseToProbeExists.keys())
        takenTissueJournalId = self._courseNumber2TakenTissueRecordId[course]
        withProbes = courseToProbeExists[course]

        if not withProbes:
            self._courseNumber = course
            self.takenTissueRecord = db.getRecord('TakenTissueJournal', '*', takenTissueJournalId)
        elif takenTissueJournalId:
            if course == self._maxCourseNumber:
                self.takenTissueRecord = db.getRecord('TakenTissueJournal', '*', takenTissueJournalId)
                self._courseNumber = course
            else:
                self._courseNumber = course + 1


    def getTakenTissueIdByCourseNumber(self, courseNumber):
        return self._courseNumber2TakenTissueRecordId[courseNumber]


    def lock(self, tableName, id):
        return CItemEditorBaseDialog.lock(self, tableName, id)


    def setStaticActionIdList(self, staticActionIdList):
        db = QtGui.qApp.db
        table = db.table('Action')
        staticActionRecords = db.getRecordList(table, '*', table['id'].inlist(staticActionIdList))
        for staticRecord in staticActionRecords:
            staticActionId = forceRef(staticRecord.value('id'))
            self.mapActionIdToStaticAction[staticActionId] = CAction(record=staticRecord)


    def addActionList(self, actionList):
        for action in actionList:
            record = action.getRecord()
            actionId = forceRef(record.value('id'))
            self.modelActions.idList().append(actionId)
            self.modelActions.recordCache().put(actionId, record)
            self.modelActions.setCheckedById(actionId)
            endDateNotValid = not forceDate(record.value('endDate'))
            self.mapActionIdToDateChangePossibility[actionId] = {'endDate': endDateNotValid}
            maxPropertiesCourse = action.maxPropertiesCourse()
            if self._maxCourseNumber < maxPropertiesCourse:
                self._maxCourseNumber = maxPropertiesCourse

        self.modelActions.reset()
        self.resetProbesTree()


    def setDateTime(self, edtDate, edtTime):
        now = QDateTime.currentDateTime()
        edtDate.setDate(now.date())
        edtTime.setTime(now.time())


    def setDateTimeByStatus(self, status):
        if status == CJobTicketStatus.wait:
            begEnabled = False
            endEnabled = False
        elif status == CJobTicketStatus.enqueued:
            begEnabled = False
            endEnabled = False
#            if not self.edtBegDate.date():
#                self.setDateTime(self.edtBegDate, self.edtBegTime)
        elif status == CJobTicketStatus.doing:
            begEnabled = True
            endEnabled = False
            if not self.edtBegDate.date():
                self.setDateTime(self.edtBegDate, self.edtBegTime)
        elif status == CJobTicketStatus.done:
            begEnabled = False
            endEnabled = True
            if not self.edtBegDate.date():
                self.setDateTime(self.edtBegDate, self.edtBegTime)
            if not self.edtEndDate.date():
                self.setDateTime(self.edtEndDate, self.edtEndTime)

        self.edtBegDate.setEnabled(begEnabled)
        self.edtBegTime.setEnabled(begEnabled)
        self.btnSetBegDateTime.setEnabled(begEnabled)
        self.edtEndDate.setEnabled(endEnabled)
        self.edtEndTime.setEnabled(endEnabled)
        self.btnSetEndDateTime.setEnabled(endEnabled)


    def cloneValues(self):
        idList = self.modelActions.idList()
        row = self.tblActions.currentIndex().row()
        actionId = idList[row]
        values = self.getPropValues(self.mapActionIdToAction[actionId])
        for row in xrange(row+1, len(idList)):
            actionId = idList[row]
            self.setPropValues(self.mapActionIdToAction[actionId], values)


    def getPropValues(self, action):
        result = {}
        actionType = action.getType()
        propertyTypeList = actionType.getPropertiesById().values()
        for propertyType in propertyTypeList:
            if propertyType.applicable(self.clientSex, self.clientAge) and propertyType.visibleInJobTicket:
                name = propertyType.name
                typeName = propertyType.typeName
                tableName = propertyType.tableName
                value = action.getPropertyById(propertyType.id).getValue()
                result[(name, typeName, tableName)] = value
        return result


    def setPropValues(self, action, values):
        actionType = action.getType()
        propertyTypeList = actionType.getPropertiesById().values()
        for propertyType in propertyTypeList:
            if propertyType.applicable(self.clientSex, self.clientAge) and propertyType.visibleInJobTicket:
                name = propertyType.name
                typeName = propertyType.typeName
                tableName = propertyType.tableName
                value = values.get((name, typeName, tableName), None)
                if value is not None:
                    property = action.getPropertyById(propertyType.id)
                    property.setValue(value)


    def recountTissueExternalId(self, tissueType=None, existCountValue=None, _manualInputExternalId=False):
        if self.takenTissueRecord:
            return forceString(self.takenTissueRecord.value('externalId'))

        if not tissueType:
            tissueType = self.cmbTissueType.value()
        tableTakenTissueJournal = QtGui.qApp.db.table('TakenTissueJournal')
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
                    cond = [tableTakenTissueJournal['tissueType_id'].eq(tissueType)]
                    dateCond = self.getRecountExternalIdDateCond(tissueType, date, tableTakenTissueJournal)
                    if dateCond:
                        cond.append(dateCond)
                    existCountValue = QtGui.qApp.db.getCount(tableTakenTissueJournal, where=cond)
                    existCountValue += 1
            self.tissueExternalIdForProperty = existCountValue
            return unicode(existCountValue).zfill(6)
        else:
            return ''


    def getTissueIdPeriod(self, tissueType, date):
        db = QtGui.qApp.db
        counterResetType = forceInt(db.translate('rbTissueType', 'id', tissueType, 'counterResetType'))
        if counterResetType == 0:   # каждый день новый отсчет
            return date, date
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
            return None, None
        return begDate, endDate


    def getRecountExternalIdDateCond(self, tissueType, date, tableTakenTissueJournal):
        db = QtGui.qApp.db
        begDate, endDate = self.getTissueIdPeriod(tissueType, date)
        if begDate == endDate:
            return tableTakenTissueJournal['datetimeTaken'].eq(date)
        return db.joinAnd([tableTakenTissueJournal['datetimeTaken'].dateGe(begDate),
                    tableTakenTissueJournal['datetimeTaken'].dateLe(endDate)])


    def checkUniqueTissueExternalId(self):
        if self._manualInputExternalId:
            if not bool(self.takenTissueRecord):
                tissueType = self.cmbTissueType.value()
                if not tissueType:
                    return True
                needCountValueStr = unicode(self.edtTissueExternalId.text()).lstrip('0')
                if not self.isValidExternalId(needCountValueStr):
                    return False
                if needCountValueStr or self.cmbStatus.value() == CJobTicketStatus.done:
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
                    tableTakenTissueJournal = QtGui.qApp.db.table('TakenTissueJournal')
                    cond = [tableTakenTissueJournal['deleted'].eq(0),
                            tableTakenTissueJournal['tissueType_id'].eq(tissueType),
                            tableTakenTissueJournal['externalId'].eq(self.edtTissueExternalId.text())]
                    dateCond = self.getRecountExternalIdDateCond(tissueType, date, tableTakenTissueJournal)
                    if dateCond:
                        cond.append(dateCond)
                    record = QtGui.qApp.db.getRecordEx(tableTakenTissueJournal, 'id', cond)
                    if record and not record.isNull('id'):
                        return self.checkInputMessage(u'другой идентификатор.\nТакой уже существует', False, self.edtTissueExternalId)
        return True


    def isValidExternalId(self, needCountValueStr):
        if not needCountValueStr.isdigit():
            return self.checkInputMessage(u'корректный идентификатор.',
                                          self.cmbStatus.value() != CJobTicketStatus.done,
                                          self.edtTissueExternalId)
        return True


    def setTissueExternalId(self, existCountValue=None):
        externalIdValue = self.recountTissueExternalId(existCountValue=existCountValue,
                                                       _manualInputExternalId=self._manualInputExternalId)
        self.edtTissueExternalId.setText(unicode(externalIdValue))
        if existCountValue is None and not self._manualInputExternalId:
            self.edtTissueNumber.setText(unicode(externalIdValue))
        else:
            numberValue = self.recountTissueExternalId(existCountValue=None,
                                                       _manualInputExternalId=False)
            self.edtTissueNumber.setText(unicode(numberValue))


    def recountTissueAmount(self):
        tissueType = self.cmbTissueType.value()
        actualByTissueTypeList, actionIdList = self.actualByTissueType.get(tissueType, ([], []))
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


    @pyqtSignature('')
    def on_actSelectAllRowActions_triggered(self):
        self.tblActions.selectAll()


    @pyqtSignature('')
    def on_actClearSelectionRowActions_triggered(self):
        self.tblActions.clearSelection()


    @pyqtSignature('')
    def on_actChangeValueActions_triggered(self):
        self.changeValueActions()


    @pyqtSignature('')
    def on_actChangeValueCurrentAction_triggered(self):
        itemId = self.tblActions.currentItemId()
        if itemId:
            self.changeValueActions(itemId)


    def getNewValues(self, itemId, selectedIdList, morphologyMKBVisible):
        dlg = CActionValuesEditor(self)
        dlg.setVisibleJournalWidgets(False)

        lenSelectedIdList = len(selectedIdList)

        if lenSelectedIdList == 1:
            if not itemId:
                itemId = selectedIdList[0]
            action = self.mapActionIdToAction[itemId]
            record = action.getRecord()
            actionType = action.getType()
            mkbVisible = actionType.defaultMKB != CActionType.dmkbNotUsed
            dlg.setWindowTitle(forceString(record.value('name')))
            dlg.setPersonIdInAction(forceRef(record.value('person_id')))
            dlg.setAssistantInAction(forceRef(record.value('assistant_id')))
            dlg.setStatus(forceInt(record.value('status')))
            dlg.setActionTypeId(forceInt(record.value('actionType_id')))
            dlg.setActionSpecification(forceInt(record.value('actionSpecification_id')))
            if mkbVisible:
                dlg.setMKB(forceString(record.value('MKB')))
                if morphologyMKBVisible:
                    dlg.setMorphology(forceString(record.value('morphologyMKB')))
            dlg.setAmount(forceDouble(record.value('amount')))
            dlg.setVisibleMKB(mkbVisible)
            dlg.setVisibleMorphologyMKB(morphologyMKBVisible and mkbVisible)
            amountVisible = actionType.amountEvaluation == CActionType.userInput
            dlg.setVisibleAmountWidgets(amountVisible)
            dlg.updateIsChecked(True)
        else:
            dlg.setVisibleAmountWidgets(True)
            dlg.setVisibleMKB(True)
            dlg.setVisibleMorphologyMKB(morphologyMKBVisible)

        if dlg.exec_():
            return dlg.values()
        return None


    def changeValueActions(self, itemId=None):
        def locCheckPolicyOnDate(clientId, date):
            if QtGui.qApp.isStrictCheckPolicyOnEndAction() in (0, 1):
                if not checkPolicyOnDate(self.clientId, date):
                    skippable = QtGui.qApp.isStrictCheckPolicyOnEndAction() == 0
                    return self.checkInputMessage(u'время закрытия действия соответствующее полису',
                                                  skippable, self.tblActions)
            return True

        def locCheckAttachOnDate(clientId, date):
            if QtGui.qApp.isStrictCheckAttachOnEndAction() in (0, 1):
                if not checkAttachOnDate(self.clientId, date):
                    skippable = QtGui.qApp.isStrictCheckAttachOnEndAction() == 0
                    return self.checkInputMessage(u'время закрытия действия соответствующее прикреплению',
                                                  skippable, self.tblActions)
            return True

        selectedIdList       = self.tblActions.selectedItemIdList()
        morphologyMKBVisible = QtGui.qApp.defaultMorphologyMKBIsVisible()

        values = self.getNewValues(itemId, selectedIdList, morphologyMKBVisible)
        if values is None:
            return

        personIdInAction       = values['personIdInAction']
        assistantIdInAction    = values['assistantIdInAction']
        status                 = values['status']
        mkb                    = values['mkb']
        morphologyMKB          = values['morphologyMKB']
        amount                 = values['amount']
        actionSpecification                 = values['actionSpecification']
        makeChanges =(   status is not None
                      or bool(assistantIdInAction)
                      or bool(personIdInAction)
                      or bool(mkb)
                      or morphologyMKB is not None
                      or amount is not None
                      or actionSpecification is not None
                     )

        if not makeChanges:
            return

        currentIndex = self.tblActions.currentIndex()

        checkItems  = []

        for action in self.mapActionIdToAction.values():
            actionType = action.getType()
            record = action.getRecord()
            actionId = forceRef(record.value('id'))
            if actionId in selectedIdList:

                mkbVisible = actionType.defaultMKB != CActionType.dmkbNotUsed
                amountVisible = actionType.amountEvaluation == CActionType.userInput

                if status is not None:
                    record.setValue('status', QVariant(status))
                    if status in (CActionStatus.finished, CActionStatus.withoutResult):
                        endDate = forceDate(record.value('endDate'))
                        if not endDate:
                            if not locCheckPolicyOnDate(self.clientId, endDate):
                                break
                            if not locCheckAttachOnDate(self.clientId, endDate):
                                break
                            record.setValue('endDate', QVariant(QDate.currentDate()))
                    elif status in (CActionStatus.canceled, CActionStatus.appointed):
                        record.setValue('endDate', QVariant(QDate()))
                if bool(personIdInAction):
                    record.setValue('person_id', QVariant(personIdInAction))
                if bool(assistantIdInAction):
                    record.setValue('assistant_id', QVariant(assistantIdInAction))
                if bool(mkb) and mkbVisible:
                    record.setValue('MKB', QVariant(mkb))
                if morphologyMKB is not None and mkbVisible and morphologyMKBVisible:
                    record.setValue('morphologyMKB', QVariant(morphologyMKB))
                if amount is not None and amountVisible:
                    record.setValue('amount', QVariant(amount))
                if actionSpecification:
                    record.setValue('actionSpecification_id', QVariant(actionSpecification))
                else:
                    record.setNull('actionSpecification_id')

                checkItems.append((record, action))

                self.modelActions.recordCache().put(actionId, record)

        checkTissueJournalStatusByActions(checkItems)
        self.modelActions.emitDataChanged()
        self.tblActions.setCurrentIndex(currentIndex)


    def jobTicketId(self):
        return self.itemId()


    def actionTypeIdList(self):
        return [action.getType().id for action in self.mapActionIdToAction.values()]


    def getTakenTissueTypeId(self):
        if self.takenTissueRecord:
            return forceRef(self.takenTissueRecord.value('tissueType_id'))
        return None


    @pyqtSignature('')
    def on_actAddActions_triggered(self):
        sourceActionId = self.tblActions.currentItemId()
        self._jobTypeActionsAddingHelper.addActions(sourceActionId)


    def getJobTicketDate(self):
        return self.date


    def removeCanDeletedId(self, actionId):
        if actionId in self.actionIdListCanDeleted:
            self.actionIdListCanDeleted.remove(actionId)
            del self.mapActionIdToAction[actionId]
            del self.mapActionIdToDateChangePossibility[actionId]
            self.resetProbesTree()


    def syncActionProperties(self, previousActionState, action):
#        assert action.getType().id == previousActionState.getType().id, 'need same action type'
        action._propertiesByName = dict(previousActionState._propertiesByName)
        action._propertiesById = dict(previousActionState._propertiesById)
        action._properties = list(previousActionState._properties)


    @pyqtSignature('')
    def on_tblActions_popupMenuAboutToShow(self):
        currentIndex = self.tblActions.currentIndex()
        curentIndexIsValid = currentIndex.isValid()
        b = bool(self.tblActions.selectedItemIdList()) and curentIndexIsValid
        self.actClearSelectionRowActions.setEnabled(b)
        self.actChangeValueActions.setEnabled(b)

        # удаление добаленных действий
        selected = set(self.tblActions.selectedItemIdList())
        b = selected.issubset(self.actionIdListCanDeleted)
        self.actDelAddedActions.setEnabled(b)

        # Мы не отменяем добавленные действия, мы должны их удалять
        b = not selected.intersection(self.actionIdListCanDeleted)
        # И у нас должно быть соответствующее право
        b = b and QtGui.qApp.userHasAnyRight([urAdmin, urCanDetachActionFromJobTicket])
        self.actDetachActions.setEnabled(b)


    def resetProbesTree(self):
        self.modelJobTicketProbe.resetCache()
        self.modelJobTicketProbe.setActionList(self.mapActionIdToAction.values(), force=True)
        self.modelJobTicketProbe.setJobTypeId(self._jobTypeId)
        self.modelJobTicketProbe.resetItems()
        self.modelJobTicketProbe.loadAll()
        equipId = self.modelJobTicketProbe.getRootEquipmentId()
        self.cmbEquipment.setValue(equipId)


    def applyChkIsAssigned(self, action):
        propertyList = action.getPropertiesById().values()
        for property in propertyList:
            if property.isAssigned():
                self.setIsAssignedChecked(True)
                return
        self.setIsAssignedChecked(False)


    def setIsAssignedChecked(self, value):
        self.chkIsAssigned.setChecked(value)


    def applyJobTypeModifier(self, actionIdList, dateTime=None):
        eventPersonCache = {}
        result = True
        for actionId in actionIdList:
            action = self.mapActionIdToAction[actionId]
            record = action.getRecord()
            if self.actionDateChanger == 1:
#                if actionId in self.mapActionIdToDateChangePossibility:
#                    # можно менять только даты окончания тех действий которые изночально были не заплнены
#                    result = self.mapActionIdToDateChangePossibility[actionId]['endDate']
#                else:
#                    # добавленные при редактировании
#                    result = not forceDate(record.value('endDate'))
                if not forceDate(record.value('endDate')):
                    if not dateTime:
                        dateTime = QDateTime(self.edtEndDate.date(), self.edtEndTime.time())
                    actionDirectionDate = forceDateTime(record.value('directionDate'))
                    if dateTime < actionDirectionDate:
                        self.checkValueMessageIgnoreAll(u'Время закрытия действия раньше времени назначения действия!',
                            False,
                            self.tblActions)
                        result = False
                        break
                    if QtGui.qApp.isStrictCheckPolicyOnEndAction() in (0, 1):
                        if not checkPolicyOnDate(self.clientId, forceDate(dateTime)):
                            skippable = QtGui.qApp.isStrictCheckPolicyOnEndAction() == 0
                            if not self.checkInputMessage(u'время закрытия действия соответствующее полису',
                                                          skippable, self.tblActions):
                                result = False
                                break
                    if QtGui.qApp.isStrictCheckAttachOnEndAction() in (0, 1):
                        if not checkAttachOnDate(self.clientId, forceDate(dateTime)):
                            skippable = QtGui.qApp.isStrictCheckAttachOnEndAction() == 0
                            if not self.checkInputMessage(u'время закрытия действия соответствующее прикреплению',
                                                          skippable, self.tblActions):
                                result = False
                                break
                    record.setValue('endDate', toVariant(dateTime))
            if self.manualExecutionAssignments and self.isFinishExec:
                record.setValue('status', QVariant(CActionStatus.finished))
            elif self.actionStatusChanger is not None:
                record.setValue('status', QVariant(self.actionStatusChanger))
#                if self.actionStatusChanger == CActionStatus.canceled: # отменено
#                    record.setValue('endDate', QVariant())
#                elif self.actionStatusChanger in (CActionStatus.finished, CActionStatus.withoutResult):
#                    record.setValue('endDate', QVariant(QDate.currentDate()))
            if not action.getType().isNomenclatureExpense and self.execCourse > CCourseStatus.proceed:
                if self.execCourse in [CCourseStatus.skipRefusalClient, CCourseStatus.finishRefusalClient]:
                    record.setValue('status', QVariant(CActionStatus.refused))
                if self.execCourse in [CCourseStatus.skipRefusalMO, CCourseStatus.finishRefusalMO]:
                    record.setValue('status', QVariant(CActionStatus.canceled))
            self.isFinishExec = False
            if self.actionPersonChanger:
                if self.actionPersonChanger == 1:
                    record.setValue('person_id', QVariant(QtGui.qApp.userId))
                elif self.actionPersonChanger == 2:
                    record.setValue('person_id', record.value('setPerson_id'))
                elif self.actionPersonChanger == 3:
                    eventId = forceRef(record.value('event_id'))
                    eventPersonId = eventPersonCache.get(eventId, None)
                    if not eventPersonId:
                        eventPersonId = QtGui.qApp.db.translate('Event', 'id', eventId, 'execPerson_id')
                        eventPersonCache[eventId] = eventPersonId
                    record.setValue('person_id', eventPersonId)
            self.modelActions.recordCache().put(forceRef(record.value('id')), record)
        self.modelActions.emitDataChanged()
        return result


    @pyqtSignature('bool')
    def on_chkIsAssigned_toggled(self, value):
        self.modelActionProperties.setFilterByAssigned(value, self.clientId, self.clientSex, self.clientAge)
        self.modelJobTicketProbe.setCheckAssignable(value)
        self.tblProps.resizeRowsToContents()


    @pyqtSignature('')
    def on_btnProbes_clicked(self):
        dlg = CJobTicketProbesDialog(self, self.modelJobTicketProbe)
        dlg.exec_()
        equipId = self.modelJobTicketProbe.getRootEquipmentId()
        self.cmbEquipment.setValue(equipId)


    @pyqtSignature('')
    def on_btnSetBegDateTime_clicked(self):
        self.setDateTime(self.edtBegDate, self.edtBegTime)


    @pyqtSignature('')
    def on_btnSetEndDateTime_clicked(self):
        self.setDateTime(self.edtEndDate, self.edtEndTime)


    @pyqtSignature('int')
    def on_cmbStatus_currentIndexChanged(self, index):
        status = self.cmbStatus.value()
        self.setDateTimeByStatus(status)
        if status == CJobTicketStatus.done: # закончено
            self.applyJobTypeModifier(self.mapActionIdToAction.keys())


    @pyqtSignature('QDate')
    def on_edtBegDate_dateChanged(self, date):
        self.edtBegTime.setEnabled(self.edtBegDate.isEnabled() and bool(date))


    @pyqtSignature('QDate')
    def on_edtEndDate_dateChanged(self, date):
        self.edtEndTime.setEnabled(self.edtEndDate.isEnabled() and bool(date))
        if self.cmbStatus.value() == CJobTicketStatus.done:
            for actionId in self.mapActionIdToAction.keys():
                action = self.mapActionIdToAction[actionId]
                record = action.getRecord()
                if self.actionDateChanger == 1 and self.mapActionIdToDateChangePossibility[actionId]['endDate']:
                    if QtGui.qApp.isStrictCheckPolicyOnEndAction() in (0, 1):
                        if not checkPolicyOnDate(self.clientId, date):
                            skippable = QtGui.qApp.isStrictCheckPolicyOnEndAction() == 0
                            if not self.checkInputMessage(u'время закрытия действия соответствующее полису',
                                                          skippable, self.tblActions):
                                break
                    if QtGui.qApp.isStrictCheckAttachOnEndAction() in (0, 1):
                        if not checkAttachOnDate(self.clientId, date):
                            skippable = QtGui.qApp.isStrictCheckAttachOnEndAction() == 0
                            if not self.checkInputMessage(u'время закрытия действия соответствующее прикреплению',
                                                          skippable, self.tblActions):
                                break
                    record.setValue('endDate', QVariant(QDateTime(date, self.edtEndTime.time())))
#            self.modelActions.emitDataChanged()


    @pyqtSignature('QTime')
    def on_edtEndTime_timeChanged(self, time):
        if self.cmbStatus.value() == CJobTicketStatus.done:
            for actionId in self.mapActionIdToAction.keys():
                action = self.mapActionIdToAction[actionId]
                record = action.getRecord()
                if self.actionDateChanger == 1 and self.mapActionIdToDateChangePossibility[actionId]['endDate']:
                    if self.edtEndDate.date():
                        record.setValue('endDate', QVariant(QDateTime(self.edtEndDate.date(), time)))


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelActions_currentChanged(self, current, previous):
        row = current.row()
        if row>=0:
            idList = self.modelActions.idList()
            actionId = idList[row]
            action = self.mapActionIdToAction[actionId]
            actionType = action.getType()
#            self.applyChkIsAssigned(action)
            self.tblProps.model().setAction(action, self.clientId, self.clientSex, self.clientAge)
            setActionPropertiesColumnVisible(actionType, self.tblProps)
            self.tblProps.resizeRowsToContents()
            self.tblProps.setEnabled(True)
            self.btnCloneValues.setEnabled(row<len(idList)-1)

            context = actionType.context if actionType else None
            additionalCustomizePrintButton(self, self.btnPrint, context)

            if not self.eventEditor:
                self._jobTypeActionsAddingHelper.creatEventPossibilities(forceRef(action.getRecord().value('event_id')))

            personId = forceRef(action.getRecord().value('person_id'))
            status = forceInt(action.getRecord().value('status'))
            if QtGui.qApp.userHasRight(urLoadActionTemplate) and action and (status != CActionStatus.finished or not personId or QtGui.qApp.userId == personId or QtGui.qApp.userHasRight(urEditOtherpeopleAction)):
                actionTemplateTreeModel = self.actionTemplateCache.getModel(action.getType().id)
                self.btnLoadTemplate.setModel(actionTemplateTreeModel)
            else:
                self.btnLoadTemplate.setEnabled(False)

            self.btnLoadPrevAction.setEnabled(QtGui.qApp.userHasRight(urCopyPrevAction) and bool(action))
            self.btnAttachedFiles.setAttachedFileItemList(action.getAttachedFileItemList())
            self.btnAttachedFiles.setEnabled(True)
        else:
            self.tblProps.setEnabled(False)
            self.btnCloneValues.setEnabled(False)
            additionalCustomizePrintButton(self, self.btnPrint, '')
#            self.chkIsAssigned.setChecked(False)
            self.btnAttachedFiles.setEnabled(False)


    @pyqtSignature('')
    def on_btnCloneValues_clicked(self):
        self.cloneValues()


    @pyqtSignature('')
    def on_btnApplyJobTypeModifier_clicked(self):
        prefs = QtGui.qApp.preferences.appPrefs
        jobTicketEndDateAskingIsRequired = forceBool(prefs.get('jobTicketEndDateAskingIsRequired', QVariant(True)))
        if jobTicketEndDateAskingIsRequired:
            actionIdList = self.modelActions.getCheckedActionIdList()
            minDate = None
            isCourseVisible = False
            for actionId in actionIdList:
                action = self.mapActionIdToAction[actionId]
                record = action.getRecord()
                actDate = forceDate(record.value('directionDate'))
                if actDate and (not minDate or actDate < minDate):
                    minDate = actDate
                executionPlan = action.executionPlanManager
                if executionPlan and executionPlan._currentItem:
                    isCourseVisible = True
            dialog = CDateTimeInputDialog(isCourseVisible=isCourseVisible)
            try:
                dialog.setMinimumDate(minDate)
                if dialog.exec_():
                    dateTime = dialog.dateTime()
                    self.execCourse = dialog.execCourse()
                else:
                    dateTime = QDateTime.currentDateTime()
                    self.execCourse = CCourseStatus.proceed
            finally:
                    dialog.deleteLater()
        else:
            dateTime = QDateTime.currentDateTime()
            self.execCourse = CCourseStatus.proceed
        if dateTime:
#            actionIdList = self.modelActions.idList()
            actionIdList = self.modelActions.getCheckedActionIdList()
            setJobEndedModifier = self.applyJobTypeModifier(actionIdList, dateTime)
            setJobEnded = True
            for action in self.mapActionIdToAction.values():
                if forceInt(action.getRecord().value('status')) != CActionStatus.finished:
                    if not action.getType().isNomenclatureExpense and self.execCourse in [CCourseStatus.skipRefusalClient, CCourseStatus.skipRefusalMO, CCourseStatus.finishRefusalClient, CCourseStatus.finishRefusalMO]:
                        action = self.freeJobTicketFirstCourse(action)
                    setJobEnded = False
                    break
            if setJobEnded and setJobEndedModifier:
                for action in self.mapActionIdToStaticAction.values():
                    if forceInt(action.getRecord().value('status')) != CActionStatus.finished:
                        if not action.getType().isNomenclatureExpense and self.execCourse in [CCourseStatus.skipRefusalClient, CCourseStatus.skipRefusalMO, CCourseStatus.finishRefusalClient, CCourseStatus.finishRefusalMO]:
                            action = self.freeJobTicketFirstCourse(action)
                        setJobEnded = False
                        break
            if setJobEnded:
                for action in self.mapActionIdToAction.values():
                    if forceInt(action.getRecord().value('status')) == CActionStatus.finished:
                        action = self.freeJobTicket(action, dateTime)
                if setJobEndedModifier:
                    for action in self.mapActionIdToStaticAction.values():
                        if forceInt(action.getRecord().value('status')) == CActionStatus.finished:
                            action = self.freeJobTicket(action, dateTime)
            self.cmbStatus.blockSignals(True)
            if setJobEnded and setJobEndedModifier:
                self.edtBegDate.setDate(dateTime.date()) #0012446:0044039
                self.edtBegTime.setTime(dateTime.time()) #0012446:0044039
                self.edtEndDate.setDate(dateTime.date())
                self.edtEndTime.setTime(dateTime.time())
                self.cmbStatus.setValue(CJobTicketStatus.done)
            elif setJobEndedModifier:
                self.edtBegDate.setDate(dateTime.date())
                self.edtBegTime.setTime(dateTime.time())
                self.cmbStatus.setValue(CJobTicketStatus.doing)
            self.cmbStatus.blockSignals(False)
        else:
            self.checkValueMessageIgnoreAll(u'Время закрытия действия некорректно или раньше времени назначения действия!', False, self.tblActions)


    def freeJobTicketFirstCourse(self, action):
        if action:
            for property in action.getType()._propertiesById.itervalues():
                if property.isJobTicketValueType():
                    jobTicketId = action[property.name]
                    prop = action.getPropertyById(property.id)
                    if prop._type:
                        QtGui.qApp.setJTR(self)
                        try:
                            prop._value = None
                            prop._changed = True
                        finally:
                            QtGui.qApp.unsetJTR(self)
                        if jobTicketId and jobTicketId not in self._cachedFreeJobTicket:
                            self._cachedFreeJobTicket.append(jobTicketId)
                            action.setFreeJobTicketCourseId(jobTicketId)
                        self.setIsDirty(False)
                        self.modelActionProperties.reset()
        return action


    @property
    def isCourseJobTicket(self):
        return self._maxCourseNumber > 1


    def on_btnPrintTissueLabel_clicked(self, callingByBarCode=False):
        self.isFinishExec = False
        callingByBarCode = callingByBarCode or self._barCodeExecutingContext.isWork()

        if self.cmbStatus.value() != CJobTicketStatus.done:
            probeExternalIdList = []
            for item in self.modelJobTicketProbe.absoluteItemList():
                if isinstance(item, CJobTicketProbeTestItem) and item.isCourseJobTicket == False:
                    probeExternalIdList.append(item.externalId)
            if not self.edtTissueExternalId.text() and not all(probeExternalIdList):
                QtGui.QMessageBox.critical(self,
                                           u'Внимание!',
                                           u'Идентификатор биоматериала не заполнен',
                                           QtGui.QMessageBox.Close)
                return
            probeExternalIdList = list(set([i if i else forceString(self.edtTissueExternalId.text()) for i in probeExternalIdList]))
            foundedIdList = self.findExistsExternalId(self.edtTissueExternalId.text(), probeExternalIdList, self.cmbTissueType.value(),
                                     self.edtTissueDate.date())
            if foundedIdList:
                QtGui.QMessageBox.critical(self,
                                           u'Внимание!',
                                           u'Идентификатор %s биоматериала не уникальный'%(foundedIdList[0]) if len(foundedIdList)==1 else \
                                             u'Идентификаторы %s не уникальны'%(', '.join(foundedIdList)),
                                           QtGui.QMessageBox.Close)
                return

            ask = not callingByBarCode or QtGui.qApp.askCloseJTAfterIBMBarCodeScanning()
            if self.isLastCoursePart():
                if not ask:
                    self.cmbStatus.setValue(CJobTicketStatus.done)
                else:
                    if self.manualExecutionAssignments:
                        buttonFinish = QtGui.QPushButton(u'Завершить')
                        buttonFinishExec = QtGui.QPushButton(u'Завершить и выполнить')
                        buttonCancel = QtGui.QPushButton(u'Отмена')
                        buttons = [buttonFinish, buttonFinishExec, buttonCancel]
                        messageBox = QtGui.QMessageBox()
                        messageBox.setWindowFlags(messageBox.windowFlags() | Qt.WindowStaysOnTopHint)
                        messageBox.addButton(buttonFinish, messageBox.AcceptRole)
                        messageBox.addButton(buttonFinishExec, messageBox.AcceptRole)
                        messageBox.addButton(buttonCancel, messageBox.RejectRole)
                        messageBox.setWindowTitle(u'Внимание!')
                        messageBox.setText(u'Завершить работу?')
                        messageBox.exec_()
                        button = messageBox.clickedButton()
                        res = None
                        if button in buttons:
                            res = buttons.index(button)
                        if res is not None and res in (0, 1):
                            self.isFinishExec = (res == 1)
                            self.cmbStatus.setValue(CJobTicketStatus.done)
                        else:
                            return
                    else:
                        messageBox = QtGui.QMessageBox(self)
                        messageBox.setWindowFlags(messageBox.windowFlags() | Qt.WindowStaysOnTopHint)
                        messageBox.addButton(u'Завершить', messageBox.AcceptRole)
                        messageBox.addButton(u'Отмена', messageBox.RejectRole)
                        messageBox.setWindowTitle(u'Внимание!')
                        messageBox.setText(u'Завершить работу?')
                        if messageBox.exec_() == QtGui.QDialogButtonBox.AcceptRole:
                            self.cmbStatus.setValue(CJobTicketStatus.done)
                        else:
                            return

        if not self.takenTissueRecord:
            equipId = self.cmbEquipment.value()
            isAutoSave = False
            if equipId:
                isAutoSave = forceBool(QtGui.qApp.db.translate('rbEquipment', 'id', equipId, 'samplePreparationMode'))
            if not isAutoSave:
                if not self.modelJobTicketProbe.getIsAutoSave():
                    if QtGui.QMessageBox.question(self,
                                       u'Внимание!',
                                       u'Необходимо зарегистрировать забор биоматериала. Продолжить?',
                                       QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel,
                                       QtGui.QMessageBox.Cancel) == QtGui.QMessageBox.Cancel:
                                           return

        if self.saveTakenTissueRecord():
            self._saveInternals(self.itemId())

        self.modelJobTicketProbe.registrateProbe()

        if self.takenTissueRecord:
            printer = QtGui.qApp.labelPrinter()
            if self.labelTemplate and printer:
                context = CInfoContext()
                takenTissueId = forceRef(self.takenTissueRecord.value('id'))
                date = QDate.currentDate()
                data = {'client'     : context.getInstance(CClientInfo, self.clientId, date),
                        'tissueType' : context.getInstance(CTissueTypeInfo, self.cmbTissueType.value()),
                        'externalId' : unicode(self.edtTissueExternalId.text()),
                        'takenTissue': context.getInstance(CTakenTissueJournalInfo, takenTissueId)
                       }

                QtGui.qApp.call(self, directPrintTemplate, (self.labelTemplate.id, data, printer))

        if callingByBarCode:
            self.accept()


    # ################################
#    @pyqtSignature('')
    def on_mnuLoadPrevAction_aboutToShow(self):
        model = self.tblActions.model()
        row = self.tblActions.currentIndex().row()
        if 0<=row<len(model.idList()):
            record = model.getRecordByRow(row)
            action = CAction(record=record)
        else:
            action = None

        self.actLoadSameSpecialityPrevAction.setEnabled(bool(
                action and self.getPrevActionId(action, CGetPrevActionIdHelper.sameSpecialityPrevAction))
                                                       )
        self.actLoadOwnPrevAction.setEnabled(bool(
                action and self.getPrevActionId(action, CGetPrevActionIdHelper.ownPrevAction))
                                            )

        self.actLoadAnyPrevAction.setEnabled(bool(
                action and self.getPrevActionId(action, CGetPrevActionIdHelper.anyPrevAction))
                                            )



#    @pyqtSignature('')
    def on_actLoadSameSpecialityPrevAction_triggered(self):
        self.loadPrevAction(CGetPrevActionIdHelper.sameSpecialityPrevAction)


#    @pyqtSignature('')
    def on_actLoadOwnPrevAction_triggered(self):
        self.loadPrevAction(CGetPrevActionIdHelper.ownPrevAction)


#    @pyqtSignature('')
    def on_actLoadAnyPrevAction_triggered(self):
        self.loadPrevAction(CGetPrevActionIdHelper.anyPrevAction)


# #####################################################################


    @pyqtSignature('int')
    def on_cmbOrgStructure_currentIndexChanged(self, index):
        val = self.cmbOrgStructure.value()
        if val:
            self.modelJobTicketProbe.setOrgStructureId(val)


    @pyqtSignature('int')
    def on_cmbEquipment_currentIndexChanged(self, index):
        val = self.cmbEquipment.value()
        if val != self.modelJobTicketProbe.getRootEquipmentId():
            self.modelJobTicketProbe.getRootItem().setEquipmentId(val)
            self.cmbEquipment.setValue(self.modelJobTicketProbe.getRootEquipmentId())


    @pyqtSignature('int')
    def on_cmbTissueType_currentIndexChanged(self, index):
        self._manualInputExternalId = forceBool(QtGui.qApp.db.translate('rbTissueType', 'id', self.cmbTissueType.value(), 'counterManualInput'))
        self._counterId = forceRef(QtGui.qApp.db.translate('rbTissueType', 'id', self.cmbTissueType.value(), 'counter_id'))
        self.edtTissueExternalId.setReadOnly(not self._manualInputExternalId)
        self.recountTissueAmount()
        self.resetProbesTree()
        isRTProcessing = self.getRTProcessingValue(self.cmbTissueType.value())
        datetimeTaken = QDateTime.currentDateTime() if isRTProcessing else  self.datetime
        self.edtTissueDate.setDate(datetimeTaken.date())
        self.edtTissueTime.setTime(datetimeTaken.time())


    @pyqtSignature('QDate')
    def on_edtTissueDate_dateChanged(self, date):
        if self._manualInputExternalId is None:
            self._manualInputExternalId = forceBool(QtGui.qApp.db.translate('rbTissueType', 'id', self.cmbTissueType.value(), 'counterManualInput'))
        self.setTissueExternalId()


    @pyqtSignature('')
    def on_actScanBarcode_triggered(self):
        if not self.edtTissueExternalId.isReadOnly():
            self.edtTissueExternalId.setFocus(Qt.OtherFocusReason)
            self.edtTissueExternalId.selectAll()
            self._barCodeExecutingContext.setOnStop(self.on_btnApplyModifier_clicked)
            self._barCodeExecutingContext.start()


    @pyqtSignature('')
    def on_btnFillPropertiesValue_clicked(self):
        self.fillPropertyValueForTakenTissue()


    @pyqtSignature('')
    def on_btnAmbCard_clicked(self):
        CAmbCardDialog(self, self.clientId).exec_()


    @pyqtSignature('')
    def on_btnLoadTemplate_clicked(self):
        if QtGui.qApp.userHasRight(urLoadActionTemplate):
            actionId = self.tblActions.currentItemId()
            action = self.mapActionIdToAction.get(actionId, None)
            if action:
                actionRecord = action.getRecord()
                if not self.eventEditor:
                    self._jobTypeActionsAddingHelper.creatEventPossibilities(forceRef(actionRecord.value('event_id')))
                personSNILS      = u''
                showTypeTemplate = 0
                templateAction   = None
                personId = QtGui.qApp.userId if QtGui.qApp.userSpecialityId else self.eventEditor.personId
                specialityId = QtGui.qApp.userSpecialityId if QtGui.qApp.userSpecialityId else self.eventEditor.personSpecialityId
                isMethodRecording = CAction.actionNoMethodRecording
                if personId:
                    db = QtGui.qApp.db
                    tablePerson = db.table('Person')
                    record = db.getRecordEx(tablePerson, [tablePerson['showTypeTemplate'], tablePerson['SNILS']], [tablePerson['id'].eq(personId), tablePerson['deleted'].eq(0)])
                    if record:
                        personSNILS      = forceStringEx(record.value('SNILS'))
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
                                                showTypeTemplate=showTypeTemplate
                                               )
                try:
                    if dlg.exec_():
                        templateAction = dlg.getSelectAction()
                        isMethodRecording = dlg.getMethodRecording()
                finally:
                    dlg.deleteLater()
                if templateAction:
                    action.updateByAction(templateAction, checkPropsOnOwner = True, clientSex = self.eventEditor.clientSex, clientAge = self.eventEditor.clientAge, isMethodRecording = isMethodRecording)
                action.save(idx=-1)
                self.modelActions.emitDataChanged()
                self.modelActionProperties.emitDataChanged()


    @pyqtSignature('')
    def on_btnSaveAsTemplate_clicked(self):
        if QtGui.qApp.userHasRight(urSaveActionTemplate):
            actionId = self.tblActions.currentItemId()
            action = self.mapActionIdToAction.get(actionId, None)
            if action:
                actionRecord = action.getRecord()
                if not self.eventEditor:
                    self._jobTypeActionsAddingHelper.creatEventPossibilities(forceRef(actionRecord.value('event_id')))
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
                self.actionTemplateCache.reset(action.getType().id)
                actionTemplateTreeModel = self.actionTemplateCache.getModel(action.getType().id)
                self.btnLoadTemplate.setModel(actionTemplateTreeModel)
                personId = forceRef(action.getRecord().value('person_id'))
                status = forceInt(action.getRecord().value('status'))
                if not(QtGui.qApp.userHasRight(urLoadActionTemplate) and (status != CActionStatus.finished
                                                                          or not personId
                                                                          or QtGui.qApp.userId == personId
                                                                          or (QtGui.qApp.userHasRight(urEditOtherPeopleActionSpecialityOnly) and QtGui.qApp.userSpecialityId == self.getSpecialityId(personId))
                                                                          or QtGui.qApp.userHasRight(urEditOtherpeopleAction))):
                    self.btnLoadTemplate.setEnabled(False)

    def getSpecialityId(self, personId):
        specialityId = None
        if personId:
            db = QtGui.qApp.db
            tablePerson = db.table('Person')
            record = db.getRecordEx(tablePerson, [tablePerson['speciality_id']], [tablePerson['deleted'].eq(0), tablePerson['id'].eq(personId)])
            specialityId = forceRef(record.value('speciality_id')) if record else None
        return specialityId
    
    
    @pyqtSignature('QModelIndex, QModelIndex')
    def on_modelActionProperties_dataChanged(self, index, index2):
        column = index.column()
        if column == self.modelActionProperties.ciIsAssigned:
            for item in self.modelJobTicketProbe.absoluteItemList():
                if isinstance(item, CJobTicketProbeTestItem):
                    item.setChecked(item.isAssigned())

    @pyqtSignature('')
    def on_actEditClient_triggered(self):
        # jobTicketId = self.tblJobTickets.currentItemId()
        # clientId = self.modelJobTickets.getClientId(jobTicketId)
        if self.clientId and QtGui.qApp.userHasAnyRight([urAdmin, urRegTabWriteRegistry, urRegTabReadRegistry]):
            dialog = CClientEditDialog(self)
            try:
                dialog.load(self.clientId)
                if dialog.exec_():
                    self.updateClientInfo()
            finally:
                dialog.deleteLater()


# #################################################


class CLocActionPropertiesTableModel(CActionPropertiesTableModel):
    def __init__(self, parent, visibilityFilter):
        CActionPropertiesTableModel.__init__(self, parent, visibilityFilter)
        self.filterByAssigned = False


    def setFilterByAssigned(self, value, clientId, clientSex, clientAge):
        self.filterByAssigned = value
        self.setAction(self.action, clientId, clientSex, clientAge)


    def visible(self, propertyType):
        result = CActionPropertiesTableModel.visible(self, propertyType)
        if self.filterByAssigned and propertyType.isAssignable:
            result = result and self.isAssigned(propertyType)
        return result


    def isAssigned(self, propertyType):
        property = self.action.getPropertyById(propertyType.id)
        return property.isAssigned()
