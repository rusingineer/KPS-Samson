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
from PyQt4.QtCore import (
    Qt,
    SIGNAL,
    QDate,
    QAbstractTableModel,
    QModelIndex,
    QVariant,
    QString,
    QObject
)

from Events.AmbulatoryCardDialog import CAmbulatoryCardDialog
from library.Attach.AttachFilesTableFlag import CAttachFilesTableFlag
from library.DialogBase           import CConstructHelperMixin
from library.ICDUtils             import getMKBName
from library.PrintInfo            import CInfoContext, CDateInfo
from library.PrintTemplates       import applyTemplate, getPrintAction
from library.Utils                import forceDate, forceBool, forceInt, forceRef, forceString, pyDate, toVariant

from Events.Action                import CAction
from Events.ActionProperty        import CActionPropertyValueTypeRegistry
from Events.ActionInfo            import CActionInfo, CActionTypeCache, CLocActionInfoList
from Events.ActionPropertiesTable import CActionPropertiesTableModel
from Events.ActionStatus          import CActionStatus
from Events.AmbCardJournalDialog  import CAmbCardJournalDialog
from Events.EventInfo             import CEventInfo, CDiagnosisInfoList, CLocEventInfoList, CVisitInfoListEx, CVisitInfo, CEventTypeInfo, CSceneInfo
from Events.TempInvalidInfo       import CTempInvalidInfoList
from Events.Utils                 import getActionTypeDescendants, getOrderText, payStatusText, setActionPropertiesColumnVisible
from Events.ActionServiceType     import CActionServiceType
from Orgs.Utils                   import getOrgStructurePersonIdList, COrgStructureInfo
from Orgs.PersonInfo              import CPersonInfo
from RefBooks.Service.Info        import CServiceInfo
from RefBooks.Speciality.Info     import CSpecialityInfo
from Registry.RegistryTable       import ( CAmbCardDiagnosticsAccompDiagnosticsTableModel,
                                           CAmbCardDiagnosticsActionsTableModel,
                                           CAmbCardDiagnosticsTableModel,
                                           CAmbCardDiagnosticsVisitsTableModel,
                                           CAmbCardStatusActionsTableModel,
                                           CAmbCardVisitTableModel,
                                           CAmbCardAttachedFilesTableModel,
                                         )
from Registry.Utils               import getClientBanner, getClientInfo2, getClientSexAge, canChangePayStatusAdditional, canEditOtherpeopleAction
from Reports.ClientDiagnostics         import CClientDiagnostics
from Reports.ClientVisits         import CClientVisits


def getClientActions(clientId, filter, classCode, order = ['Action.endDate DESC', 'Action.id'], fieldName = None):
    db = QtGui.qApp.db
    tableAction = db.table('Action')
    queryTable = tableAction
    tableEvent = db.table('Event')
    queryTable = queryTable.leftJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))
    tableActionType = db.table('ActionType')
    queryTable = queryTable.leftJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
    if fieldName in [u'setPerson_id', u'person_id']:
        tableSPWS = db.table('vrbPersonWithSpeciality')
        queryTable = queryTable.leftJoin(tableSPWS, tableSPWS['id'].eq(tableAction[fieldName]))
    cond = [tableAction['deleted'].eq(0),
            #tableAction['status'].ne(CActionStatus.withoutResult),
                tableEvent['deleted'].eq(0),
            tableEvent['client_id'].eq(clientId)]
    classFilter = filter.get('class', None)
    if classFilter:
        cond.append(tableActionType['class'].eq(classFilter))
    if classCode is not None:
        if type(classCode) == list:
            cond.append(tableActionType['class'].inlist(classCode))
        else:
            cond.append(tableActionType['class'].eq(classCode))
    serviceType = filter.get('serviceType', None)

    if serviceType is not None:
        cond.append(tableActionType['serviceType'].eq(serviceType))
    excludeServiceType = filter.get('excludeServiceType', None)
    if excludeServiceType is not None:
        cond.append(tableActionType['serviceType'].ne(excludeServiceType))
    begDate = filter.get('begDate', None)
    if begDate:
        cond.append(tableAction['endDate'].ge(begDate))
    endDate = filter.get('endDate', None)
    if endDate:
        cond.append(tableAction['endDate'].le(endDate))
    actionGroupId = filter.get('actionGroupId', None)
    if actionGroupId:
        cond.append(tableAction['actionType_id'].inlist(getActionTypeDescendants(actionGroupId, classCode)))
    office = filter.get('office', '')
    if office:
        cond.append(tableAction['office'].like(office))
    orgStructureId = filter.get('orgStructureId', None)
    if orgStructureId:
        cond.append(tableAction['person_id'].inlist(getOrgStructurePersonIdList(orgStructureId)))
    status = filter.get('status', None)
    if status is not None:
        cond.append(tableAction['status'].eq(status))
    try:
        QtGui.QApplication.setOverrideCursor(QtGui.QCursor(Qt.WaitCursor))
        return db.getIdList(queryTable,
               tableAction['id'].name(),
               cond,
               order)
    finally:
        QtGui.QApplication.restoreOverrideCursor()


def getClientVisits(clientId, filter, fieldName=u'', tblAmbCardVisits=None, orderBY=None):
    begDate        = filter.get('begDate')
    endDate        = filter.get('endDate')
    orgStructureId = filter.get('orgStructureId')
    specialityId   = filter.get('specialityId')
    personId       = filter.get('personId')
    sceneId        = filter.get('sceneId')
    eventTypeId    = filter.get('eventTypeId')
    serviceId      = filter.get('serviceId')

    db = QtGui.qApp.db

    tableVisit  = db.table('Visit')
    tableEvent  = db.table('Event')
    tablePerson = db.table('Person')
    order = tblAmbCardVisits.order() if (tblAmbCardVisits and tblAmbCardVisits.order()) else ['Visit.date ASC']
    queryTable = tableVisit.leftJoin(tableEvent, tableEvent['id'].eq(tableVisit['event_id']))
    if 'vrbPersonWithSpeciality.name' in order and fieldName:
        tablePersonWS = db.table('vrbPersonWithSpeciality')
        queryTable = queryTable.leftJoin(tablePersonWS, tablePersonWS['id'].eq(tableVisit[fieldName]))
    if 'rbScene.name' in order and fieldName:
        tableScene = db.table('rbScene')
        queryTable = queryTable.leftJoin(tableScene, tableScene['id'].eq(tableVisit[fieldName]))
    if 'rbVisitType.name' in order and fieldName:
        tableVisitType = db.table('rbVisitType')
        queryTable = queryTable.leftJoin(tableVisitType, tableVisitType['id'].eq(tableVisit[fieldName]))
    if 'rbService.name' in order and fieldName:
        tableService = db.table('rbService')
        queryTable = queryTable.leftJoin(tableService, tableService['id'].eq(tableVisit[fieldName]))
    if 'rbFinance.name' in order and fieldName:
        tableFinance = db.table('rbFinance')
        queryTable = queryTable.leftJoin(tableFinance, tableFinance['id'].eq(tableVisit[fieldName]))
    cond = [tableVisit['deleted'].eq(0),
            tableEvent['deleted'].eq(0),
            tableEvent['client_id'].eq(clientId)]
    if begDate:
        cond.append(tableVisit['date'].dateGe(begDate))
    if endDate:
        cond.append(tableVisit['date'].dateLe(endDate))
    if specialityId or orgStructureId:
        queryTable = queryTable.leftJoin(tablePerson, tableVisit['person_id'].eq(tablePerson['id']))
        if specialityId:
            cond.append(tablePerson['speciality_id'].eq(specialityId))
        if orgStructureId:
            cond.append(tablePerson['orgStructure_id'].eq(orgStructureId))
    if personId:
        cond.append(tableVisit['person_id'].eq(personId))
    if sceneId:
        cond.append(tableVisit['scene_id'].eq(sceneId))
    if eventTypeId:
        cond.append(tableEvent['eventType_id'].eq(eventTypeId))
    if serviceId:
        cond.append(tableVisit['service_id'].eq(serviceId))
    return db.getIdList(queryTable, tableVisit['id'].name(), cond, order)


class CAmbCardMixin(CConstructHelperMixin):
    __pyqtSignals__ = ('actionSelected(int)'
                      )

    def __init__(self):
        CConstructHelperMixin.__init__(self)
        self.__ambCardVisitIsInitialised = False
        self.__ambCardFilesIsInitialised = False
        self.ambCardMonitoringIsInitialised = False
        self.__ambCardDiagnosticsFilter = {}
        self.__ambCardVisitsFilter = {}
        self.ambCardComboBoxFilters = {}
        #self.btnAmbCardJournal.clicked.connect(self.on_btnAmbCardJournal_clicked)


    def preSetupUi(self):
        self.addModels('AmbCardDiagnostics', CAmbCardDiagnosticsTableModel(self))
        self.addModels('AmbCardDiagnosticsVisits', CAmbCardDiagnosticsVisitsTableModel(self))
        self.addModels('AmbCardDiagnosticsAccompDiagnostics', CAmbCardDiagnosticsAccompDiagnosticsTableModel(self))
        self.addModels('AmbCardDiagnosticsActions', CAmbCardDiagnosticsActionsTableModel(self))
        self.addModels('AmbCardDiagnosticsActionProperties', CActionPropertiesTableModel(self))
        self.addModels('AmbCardStatusActions', CAmbCardStatusActionsTableModel(self))
        self.addModels('AmbCardStatusActionProperties', CActionPropertiesTableModel(self))
        self.addModels('AmbCardDiagnosticActions', CAmbCardStatusActionsTableModel(self))
        self.addModels('AmbCardDiagnosticActionProperties', CActionPropertiesTableModel(self))
        self.addModels('AmbCardCureActions', CAmbCardStatusActionsTableModel(self))
        self.addModels('AmbCardCureActionProperties', CActionPropertiesTableModel(self))
        self.addModels('AmbCardMiscActions', CAmbCardStatusActionsTableModel(self))
        self.addModels('AmbCardMiscActionProperties', CActionPropertiesTableModel(self))
        self.addModels('AmbCardVisits', CAmbCardVisitTableModel(self))
        self.addModels('AmbCardFiles', CAmbCardAttachedFilesTableModel(self))
        self.addModels('AmbCardSurveyActions', CAmbCardStatusActionsTableModel(self))
        self.addModels('AmbCardSurveyActionProperties', CActionPropertiesTableModel(self))
        self.addModels('AmbCardMonitoring', CAmbCardMonitoringModel(self))

        self.addObject('actDiagnosticsShowPropertyHistory',   QtGui.QAction(u'Показать журнал значения свойства', self))
        self.addObject('actDiagnosticsShowPropertiesHistory', QtGui.QAction(u'Показать журнал значения свойств...', self))
        self.addObject('actStatusShowPropertyHistory',        QtGui.QAction(u'Показать журнал значения свойства', self))
        self.addObject('actStatusShowPropertiesHistory',      QtGui.QAction(u'Показать журнал значения свойств...', self))
        self.addObject('actDiagnosticShowPropertyHistory',    QtGui.QAction(u'Показать журнал значения свойства', self))
        self.addObject('actDiagnosticShowPropertiesHistory',  QtGui.QAction(u'Показать журнал значения свойств...', self))
        self.addObject('actCureShowPropertyHistory',          QtGui.QAction(u'Показать журнал значения свойства', self))
        self.addObject('actCureShowPropertiesHistory',        QtGui.QAction(u'Показать журнал значения свойств...', self))
        self.addObject('actMiscShowPropertyHistory',          QtGui.QAction(u'Показать журнал значения свойства', self))
        self.addObject('actMiscShowPropertiesHistory',        QtGui.QAction(u'Показать журнал значения свойств...', self))
        self.addObject('actSurveyShowPropertyHistory',        QtGui.QAction(u'Показать журнал значения свойства', self))
        self.addObject('actSurveyShowPropertiesHistory',      QtGui.QAction(u'Показать журнал значения свойств...', self))
        self.addObject('actAmbCardPrintEvents',               QtGui.QAction(u'Напечатать список диагнозов', self))
        self.addObject('actAmbCardPrintVisits',               QtGui.QAction(u'Напечатать список визитов', self))
        self.addObject('actAmbCardPrintVisitsHistory',        getPrintAction(self, 'visitsHistory', u'Напечатать визиты по шаблону', False))
        self.addObject('actAmbCardPrintCaseHistory',          getPrintAction(self, 'caseHistory', u'Напечатать карту'))
#        self.connect(self.actAmbCardPrintEvents, SIGNAL('triggered()'), self.on_actAmbCardPrintEvents_triggered)
        self.addObject('actAmbCardActionTypeGroupId',         QtGui.QAction(u'Фильтровать по группе Действия', self))
        self.addObject('actAmbCardOpenActionELMK',            QtGui.QAction(u'Открыть обращение ЭЛМК', self))
        self.addObject('actAmbCardPrintAction',               getPrintAction(self, None, u'Напечатать по шаблону', False))
        self.addObject('actAmbCardPrintActions',              QtGui.QAction(u'Напечатать список мероприятий', self))
        self.addObject('actAmbCardPrintActionsHistory',       getPrintAction(self, 'actionsHistory', u'Напечатать карту мероприятий', False))
        self.addObject('actAmbCardCopyAction',                QtGui.QAction(u'Копировать свойства', self))
#        self.actAmbCardPrintActions.setShortcut('F6')
#        self.connect(self.actAmbCardPrintVisits, SIGNAL('triggered()'), self.on_actAmbCardPrintVisits_triggered)


    def postSetupUi(self):
        self.setModels(self.tblAmbCardDiagnostics, self.modelAmbCardDiagnostics, self.selectionModelAmbCardDiagnostics)
        self.setModels(self.tblAmbCardDiagnosticsVisits, self.modelAmbCardDiagnosticsVisits, self.selectionModelAmbCardDiagnosticsVisits)
        self.setModels(self.tblAmbCardDiagnosticsAccompDiagnostics, self.modelAmbCardDiagnosticsAccompDiagnostics, self.selectionModelAmbCardDiagnosticsAccompDiagnostics)
        self.setModels(self.tblAmbCardDiagnosticsActions, self.modelAmbCardDiagnosticsActions, self.selectionModelAmbCardDiagnosticsActions)
        self.setModels(self.tblAmbCardDiagnosticsActionProperties, self.modelAmbCardDiagnosticsActionProperties, self.selectionModelAmbCardDiagnosticsActionProperties)
        self.setModels(self.tblAmbCardStatusActions, self.modelAmbCardStatusActions, self.selectionModelAmbCardStatusActions)
        self.setModels(self.tblAmbCardStatusActionProperties, self.modelAmbCardStatusActionProperties, self.selectionModelAmbCardStatusActionProperties)
        self.setModels(self.tblAmbCardDiagnosticActions, self.modelAmbCardDiagnosticActions, self.selectionModelAmbCardDiagnosticActions)
        self.setModels(self.tblAmbCardDiagnosticActionProperties, self.modelAmbCardDiagnosticActionProperties, self.selectionModelAmbCardDiagnosticActionProperties)
        self.setModels(self.tblAmbCardCureActions, self.modelAmbCardCureActions, self.selectionModelAmbCardCureActions)
        self.setModels(self.tblAmbCardCureActionProperties, self.modelAmbCardCureActionProperties, self.selectionModelAmbCardCureActionProperties)
        self.setModels(self.tblAmbCardMiscActions, self.modelAmbCardMiscActions, self.selectionModelAmbCardMiscActions)
        self.setModels(self.tblAmbCardMiscActionProperties, self.modelAmbCardMiscActionProperties, self.selectionModelAmbCardMiscActionProperties)
        self.setModels(self.tblAmbCardVisits, self.modelAmbCardVisits, self.selectionModelAmbCardVisits)
        self.setModels(self.tblAmbCardAttachedFiles, self.modelAmbCardFiles, self.selectionModelAmbCardFiles)
        self.setModels(self.tblAmbCardSurveyActions, self.modelAmbCardSurveyActions, self.selectionModelAmbCardSurveyActions)
        self.setModels(self.tblAmbCardSurveyActionProperties, self.modelAmbCardSurveyActionProperties, self.selectionModelAmbCardSurveyActionProperties)
        self.setModels(self.tblAmbCardMonitoring, self.modelAmbCardMonitoring, self.selectionModelAmbCardMonitoring)

        self.tblAmbCardStatusActions.createPopupMenu([self.actAmbCardActionTypeGroupId, self.actAmbCardCopyAction, self.actAmbCardOpenActionELMK])
        self.tblAmbCardDiagnosticActions.createPopupMenu([self.actAmbCardActionTypeGroupId, self.actAmbCardCopyAction])
        self.tblAmbCardCureActions.createPopupMenu([self.actAmbCardActionTypeGroupId, self.actAmbCardCopyAction])
        self.tblAmbCardMiscActions.createPopupMenu([self.actAmbCardActionTypeGroupId, self.actAmbCardCopyAction])
        self.tblAmbCardSurveyActions.createPopupMenu([self.actAmbCardActionTypeGroupId, self.actAmbCardCopyAction])

        self.cmbAmbCardDiagnosticsPurpose.setTable('rbEventTypePurpose', True)
        self.cmbAmbCardDiagnosticsSpeciality.setTable('rbSpeciality', True)
        self.cmbHealthGroup.setTable('rbHealthGroup', True)

        self.cmbAmbCardStatusGroup.setClass(0)
        self.cmbAmbCardDiagnosticGroup.setClass(1)
        self.cmbAmbCardCureGroup.setClass(2)
        self.cmbAmbCardMiscGroup.setClass(3)
        self.cmbAmbCardSurveyGroup.setClass(None)
        self.cmbAmbCardSurveyGroup.setServiceType(CActionServiceType.survey)

        self.tabAmbCardContent.setCurrentIndex(0)

        self.cmbAmbCardVisitSpeciality.setTable('rbSpeciality')
        self.cmbAmbCardVisitScene.setTable('rbScene')
        self.cmbAmbCardVisitEventType.setTable('EventType')
        self.cmbAmbCardVisitService.setTable('rbService')
        self.edtAmbCardSurveyBegDate.setDate(QDate(QDate.currentDate().year(), 1, 1))  # btnAmbCardGraphClicked

        self.connect(self.tblAmbCardStatusActions.horizontalHeader(), SIGNAL('sectionClicked(int)'), self._setActionsOrderByColumn)
        self.connect(self.tblAmbCardDiagnosticActions.horizontalHeader(), SIGNAL('sectionClicked(int)'), self._setActionsOrderByColumn)
        self.connect(self.tblAmbCardCureActions.horizontalHeader(), SIGNAL('sectionClicked(int)'), self._setActionsOrderByColumn)
        self.connect(self.tblAmbCardMiscActions.horizontalHeader(), SIGNAL('sectionClicked(int)'), self._setActionsOrderByColumn)
        self.connect(self.tblAmbCardVisits.horizontalHeader(), SIGNAL('sectionClicked(int)'), self.onHeaderAmbCardVisitsColClicked)
        self.connect(self.btnAmbCardJournal,  SIGNAL('clicked()'),  self.on_btnAmbCardJournalClicked)
        self.connect(self.btnAmbCardGraph,  SIGNAL('clicked()'),  self.on_btnAmbCardGraphClicked)
        self.connect(self.tblAmbCardSurveyActions.horizontalHeader(), SIGNAL('sectionClicked(int)'), self._setActionsOrderByColumn)
        self.connect(self.btnAmbCard, SIGNAL('clicked()'), self.on_btnAmbCardClicked)

        self.tblAmbCardStatusActions.enableColsHide()
        self.tblAmbCardDiagnosticActions.enableColsHide()
        self.tblAmbCardCureActions.enableColsHide()
        self.tblAmbCardMiscActions.enableColsHide()
        self.tblAmbCardStatusActions.enableColsMove()
        self.tblAmbCardDiagnosticActions.enableColsMove()
        self.tblAmbCardCureActions.enableColsMove()
        self.tblAmbCardMiscActions.enableColsMove()
        self.tblAmbCardSurveyActions.enableColsHide()
        self.tblAmbCardSurveyActions.enableColsMove()
        self.tblAmbCardAttachedFiles.setFlags(CAttachFilesTableFlag.canRead)
        self.tblAmbCardMonitoring.enableColsHide()
        self.tblAmbCardMonitoring.enableColsMove()

        self.prepareActionTable(self.tblAmbCardDiagnosticsActionProperties, self.actDiagnosticsShowPropertyHistory, self.actDiagnosticsShowPropertiesHistory)
        self.prepareActionTable(self.tblAmbCardStatusActionProperties, self.actStatusShowPropertyHistory, self.actStatusShowPropertiesHistory)
        self.prepareActionTable(self.tblAmbCardDiagnosticActionProperties, self.actDiagnosticShowPropertyHistory, self.actDiagnosticShowPropertiesHistory)
        self.prepareActionTable(self.tblAmbCardCureActionProperties, self.actCureShowPropertyHistory, self.actCureShowPropertiesHistory)
        self.prepareActionTable(self.tblAmbCardMiscActionProperties, self.actMiscShowPropertyHistory, self.actMiscShowPropertiesHistory)
        self.prepareActionTable(self.tblAmbCardSurveyActionProperties, self.actSurveyShowPropertyHistory, self.actSurveyShowPropertiesHistory)

        # self.connect(self.cmdAmbCardDiagnosticsButtonBox, SIGNAL('clicked(QAbstractButton*)'), self.on_cmdAmbCardDiagnosticsButtonBox_clicked)
        # self.connect(self.cmdAmbCardStatusButtonBox, SIGNAL('clicked(QAbstractButton*)'), self.on_cmdAmbCardStatusButtonBox_clicked)
        # self.connect(self.cmdAmbCardDiagnosticButtonBox, SIGNAL('clicked(QAbstractButton*)'), self.on_cmdAmbCardDiagnosticButtonBox_clicked)
        # self.connect(self.cmdAmbCardCureButtonBox, SIGNAL('clicked(QAbstractButton*)'), self.on_cmdAmbCardCureButtonBox_clicked)
        # self.connect(self.cmdAmbCardMiscButtonBox, SIGNAL('clicked(QAbstractButton*)'), self.on_cmdAmbCardMiscButtonBox_clicked)
        # self.connect(self.cmdAmbCardVisitButtonBox, SIGNAL('clicked(QAbstractButton*)'), self.on_cmdAmbCardVisitButtonBox_clicked)
        # self.connect(self.tabAmbCardContent, SIGNAL('currentChanged(int)'), self.on_tabAmbCardContent_currentChanged)

        # словарь для создания пунктов меню для btnActionPrint
        self.action_menu_dict = {
            'Events': [self.actAmbCardPrintEvents, self.actAmbCardPrintCaseHistory],
            'Actions': [self.actAmbCardPrintAction, self.actAmbCardPrintActions, self.actAmbCardPrintActionsHistory],
            'Visits': [self.actAmbCardPrintVisits, self.actAmbCardPrintVisitsHistory]
        }

        # self.setSortable(self.tblAmbCardDiagnostics, self.on_cmdAmbCardDiagnosticsButtonBox_apply)
        # self.setSortable(self.tblAmbCardDiagnosticsVisits, self.updateAmbCardDiagnosticsInfo)
        # self.setSortable(self.tblAmbCardDiagnosticsAccompDiagnostics, self.updateAmbCardDiagnosticsInfo)
        # # self.setSortable(self.tblAmbCardStatusActions, self.on_cmdAmbCardStatusButtonBox_apply)
        # self.setSortable(self.tblAmbCardStatusActionProperties, lambda: \
        #     self.updateAmbCardPropertiesTable(self.tblAmbCardStatusActions.currentIndex(),
        #                                       self.tblAmbCardStatusActionProperties))
        # # self.setSortable(self.tblAmbCardDiagnosticActions, self.on_cmdAmbCardDiagnosticButtonBox_apply)
        # self.setSortable(self.tblAmbCardDiagnosticActionProperties, lambda: \
        #     self.updateAmbCardPropertiesTable(self.tblAmbCardDiagnosticActions.currentIndex(),
        #                                       self.tblAmbCardDiagnosticActionProperties))
        # # self.setSortable(self.tblAmbCardCureActions, self.on_cmdAmbCardCureButtonBox_apply)
        # self.setSortable(self.tblAmbCardCureActionProperties, lambda: \
        #     self.updateAmbCardPropertiesTable(self.tblAmbCardCureActions.currentIndex(),
        #                                       self.tblAmbCardCureActionProperties))
        # # self.setSortable(self.tblAmbCardMiscActions, self.on_cmdAmbCardMiscButtonBox_apply)
        # self.setSortable(self.tblAmbCardMiscActionProperties, lambda: \
        #     self.updateAmbCardPropertiesTable(self.tblAmbCardMiscActions.currentIndex(),
        #                                       self.tblAmbCardMiscActionProperties))
        # self.setSortable(self.tblAmbCardVisits, self.on_cmdAmbCardVisitButtonBox_apply)
        #
        # self.setSortable(self.tblAmbCardDiagnosticsActions, self.updateAmbCardDiagnosticsInfo)
        # self.setSortable(self.tblAmbCardDiagnosticsActionProperties, lambda: self.updateAmbCardPropertiesTable(
        #     self.tblAmbCardDiagnosticsActions.currentIndex(), self.tblAmbCardDiagnosticsActionProperties))
        
    def onHeaderAmbCardVisitsColClicked(self, column):
        self.tblAmbCardVisits.setOrder(column)
        filter = {}
        filter['begDate'] = self.edtAmbCardVisitBegDate.date()
        filter['endDate'] = self.edtAmbCardVisitEndDate.date()
        filter['orgStructureId'] = self.cmbAmbCardVisitOrgStructure.value()
        filter['specialityId'] = self.cmbAmbCardVisitSpeciality.value()
        filter['personId'] = self.cmbAmbCardVisitPerson.value()
        filter['sceneId'] = self.cmbAmbCardVisitScene.value()
        filter['eventTypeId'] = self.cmbAmbCardVisitEventType.value()
        filter['serviceId'] = self.cmbAmbCardVisitService.value()
        self.updateAmbCardVisit(filter, self.tblAmbCardVisits.model().cols()[column].fields()[0])
        self.tblAmbCardVisits.setFocus(Qt.TabFocusReason)
        

    def resetWidgets(self):
        self.getComboBoxesFilterParamsByClient(self._clientId)
        self.on_cmdAmbCardDiagnosticsButtonBox_reset()
        self.on_cmdAmbCardStatusButtonBox_reset()
        self.on_cmdAmbCardDiagnosticButtonBox_reset()
        self.on_cmdAmbCardCureButtonBox_reset()
        self.on_cmdAmbCardMiscButtonBox_reset()
        self.on_cmdAmbCardVisitButtonBox_reset()
        self.on_cmdAmbCardSurveyButtonBox_reset()

        self.on_cmdAmbCardDiagnosticsButtonBox_apply()
        self.on_cmdAmbCardStatusButtonBox_apply()
        self.on_cmdAmbCardDiagnosticButtonBox_apply()
        self.on_cmdAmbCardCureButtonBox_apply()
        self.on_cmdAmbCardMiscButtonBox_apply()
        self.on_cmdAmbCardSurveyButtonBox_apply()

        self.__ambCardVisitIsInitialised = False
        self.__ambCardFilesIsInitialised = False
        self.ambCardMonitoringIsInitialised = False
        self.__ambCardDiagnosticsFilter = {}
        self.__ambCardVisitsFilter = {}
        self.ambCardComboBoxFilters = {}
        self.on_tabAmbCardContent_currentChanged(self.tabAmbCardContent.currentIndex())


    def getComboBoxesFilterParamsByClient(self, clientId):
        if clientId:
            db = QtGui.qApp.db
            tableDiagnostic = db.table('Diagnostic')
            tableDiagnosis = db.table('Diagnosis')
            tableEvent = db.table('Event')
            tableEventType = db.table('EventType')
            tablePerson = db.table('vrbPerson')
            tableVisit = db.table('Visit')
            queryTable = tableDiagnostic
            queryTable = queryTable.leftJoin(tableDiagnosis, tableDiagnosis['id'].eq(tableDiagnostic['diagnosis_id']))
            queryTable = queryTable.leftJoin(tablePerson, tablePerson['id'].eq(tableDiagnostic['person_id']))
            queryTable = queryTable.leftJoin(tableEvent, tableEvent['id'].eq(tableDiagnostic['event_id']))
            queryTable = queryTable.leftJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
            cols = [u'GROUP_CONCAT(DISTINCT Diagnostic.person_id) AS personId',
                        u'GROUP_CONCAT(DISTINCT vrbPerson.speciality_id) AS specialityId',
                        u'GROUP_CONCAT(DISTINCT EventType.purpose_id) AS eventPurposeId']
            cond = [tableDiagnosis['client_id'].eq(clientId), 
                        tableDiagnostic['deleted'].eq(0), ]
            record = db.getRecordEx(queryTable, cols, cond)
            if forceString(record.value('personId')) != u'':
                self.ambCardComboBoxFilters['personId'] = forceString(record.value('personId'))
                self.ambCardComboBoxFilters['specialityId'] = forceString(record.value('specialityId'))
                self.ambCardComboBoxFilters['eventPurposeId'] = forceString(record.value('eventPurposeId'))
            
            queryTable = tableVisit
            queryTable = queryTable.leftJoin(tableEvent, tableEvent['id'].eq(tableVisit['event_id']))
            queryTable = queryTable.leftJoin(tablePerson, tablePerson['id'].eq(tableVisit['person_id']))
            cols = [u'GROUP_CONCAT(DISTINCT vrbPerson.id) AS visitPersonId',
                        u'GROUP_CONCAT(DISTINCT vrbPerson.speciality_id) AS visitSpecialityId', 
                        u'GROUP_CONCAT(DISTINCT Visit.service_id) AS visitServiceId', 
                        u'GROUP_CONCAT(DISTINCT Event.eventType_id) AS visitEventTypeId']
            cond = [tableEvent['client_id'].eq(clientId), 
                        tableVisit['deleted'].eq(0)]
            record = db.getRecordEx(queryTable, cols, cond)
            if forceString(record.value('visitPersonId')) != u'':
                if forceString(record.value('visitPersonId')) != '':
                    self.ambCardComboBoxFilters['visitPersonId'] = forceString(record.value('visitPersonId'))
                if forceString(record.value('visitSpecialityId')) != '':
                    self.ambCardComboBoxFilters['visitSpecialityId'] = forceString(record.value('visitSpecialityId'))
                if forceString(record.value('visitServiceId')) != '':
                    self.ambCardComboBoxFilters['visitServiceId'] = forceString(record.value('visitServiceId'))
                if forceString(record.value('visitEventTypeId')) != '':
                    self.ambCardComboBoxFilters['visitEventTypeId'] = forceString(record.value('visitEventTypeId'))


    def editF090Action(self, actionId):
        from F090.F090EditDialog import CF090EditDialog
        newActionId = None
        dialog = CF090EditDialog(self)
        try:
            dialog.load(actionId)
            dialog.protectWidgetFromEdit(True)
            dialog.exec_()
            if dialog.isBtnSave:
                newActionId = dialog.itemId()
            else:
                pass
        finally:
            dialog.deleteLater()
        return newActionId


    def getF090ActionTypeId(self, actionId):
        if actionId:
            db = QtGui.qApp.db
            tableAction = db.table('Action')
            tableActionType = db.table('ActionType')
            queryTable = tableAction.innerJoin(tableActionType,
                                               tableActionType['id'].eq(tableAction['actionType_id']))
            cond = [tableAction['id'].eq(actionId),
                    tableAction['deleted'].eq(0),
                    tableActionType['deleted'].eq(0),
                    tableActionType['flatCode'].like(u'%medical_examination'),
                    ]
            record = db.getRecordEx(queryTable, [tableActionType['id'].alias('actionTypeId')], cond)
            return forceRef(record.value('actionTypeId')) if record else None
        return None


    # @pyqtSignature('')
    def on_actAmbCardOpenActionELMK_triggered(self):
        index = self.tblAmbCardStatusActions.currentIndex()
        if index:
            row = index.row()
            record = index.model().getRecordByRow(row) if row >= 0 else None
            actionId = forceRef(record.value('id')) if record else None
            if actionId and canChangePayStatusAdditional(self, 'Action', actionId) and canEditOtherpeopleAction(
                    self, actionId):
                if forceBool(self.getF090ActionTypeId(actionId)):
                    if self.editF090Action(actionId):
                        self.on_cmdAmbCardStatusButtonBox_apply()


    # @pyqtSignature('')
    def on_tblAmbCardStatusActions_popupMenuAboutToShow(self):
        notEmpty = self.modelAmbCardStatusActions.rowCount() > 0
        self.actAmbCardActionTypeGroupId.setEnabled(notEmpty)
        self.actAmbCardCopyAction.setEnabled(notEmpty)
        self.actAmbCardOpenActionELMK.setVisible(False)
        index = self.tblAmbCardStatusActions.currentIndex()
        if index:
            row = index.row()
            record = index.model().getRecordByRow(row) if row >= 0 else None
            actionId = forceRef(record.value('id')) if record else None
            if actionId and forceBool(self.getF090ActionTypeId(actionId)):
                self.actAmbCardOpenActionELMK.setVisible(True)
                if canChangePayStatusAdditional(self, 'Action', actionId) and canEditOtherpeopleAction(self, actionId):
                    self.actAmbCardOpenActionELMK.setEnabled(notEmpty)
                else:
                    self.actAmbCardOpenActionELMK.setEnabled(False)
                self.actAmbCardCopyAction.setEnabled(False)


    # @pyqtSignature('')
    def on_tblAmbCardDiagnosticActions_popupMenuAboutToShow(self):
        notEmpty = self.modelAmbCardDiagnosticActions.rowCount() > 0
        self.actAmbCardActionTypeGroupId.setEnabled(notEmpty)
        self.actAmbCardCopyAction.setEnabled(notEmpty)


    # @pyqtSignature('')
    def on_tblAmbCardCureActions_popupMenuAboutToShow(self):
        notEmpty = self.modelAmbCardCureActions.rowCount() > 0
        self.actAmbCardActionTypeGroupId.setEnabled(notEmpty)
        self.actAmbCardCopyAction.setEnabled(notEmpty)


    # @pyqtSignature('')
    def on_tblAmbCardMiscActions_popupMenuAboutToShow(self):
        notEmpty = self.modelAmbCardMiscActions.rowCount() > 0
        self.actAmbCardActionTypeGroupId.setEnabled(notEmpty)
        self.actAmbCardCopyAction.setEnabled(notEmpty)


    def on_tblAmbCardSurveyActions_popupMenuAboutToShow(self):
        notEmpty = self.modelAmbCardSurveyActions.rowCount() > 0
        self.actAmbCardActionTypeGroupId.setEnabled(notEmpty)
        self.actAmbCardCopyAction.setEnabled(notEmpty)


#    @pyqtSignature('')
    def on_actAmbCardActionTypeGroupId_triggered(self):
        groupId = None
        column = None
        table, updateFunction, cmbActionType, filter = self.getCurrentActionsTable()
        index = table.currentIndex()
        if index:
            row = index.row()
            column = index.column()
            record = index.model().getRecordByRow(row) if row >= 0 else None
            actionTypeId = forceRef(record.value('actionType_id')) if record else None
            actionType = CActionTypeCache.getById(actionTypeId) if actionTypeId else None
            groupId = actionType.groupId if actionType else None
            if not groupId:
               groupId = actionTypeId if actionTypeId else None
        cmbActionType.setValue(groupId)
        self._setActionsOrderByColumn(column)


    def getCurrentActionsTable(self):
        index = self.tabAmbCardContent.currentIndex()
        if index in [1, 2, 3, 4]:
            return [(self.tblAmbCardStatusActions, self.updateAmbCardStatus, self.cmbAmbCardStatusGroup,
                     self.getAmbCardFilter(
                        self.edtAmbCardStatusBegDate,
                        self.edtAmbCardStatusEndDate,
                        self.cmbAmbCardStatusGroup,
                        self.edtAmbCardStatusOffice,
                        self.cmbAmbCardStatusOrgStructure
                        )),
                    (self.tblAmbCardDiagnosticActions, self.updateAmbCardDiagnostic, self.cmbAmbCardDiagnosticGroup,
                     self.getAmbCardFilter(
                        self.edtAmbCardDiagnosticBegDate,
                        self.edtAmbCardDiagnosticEndDate,
                        self.cmbAmbCardDiagnosticGroup,
                        self.edtAmbCardDiagnosticOffice,
                        self.cmbAmbCardDiagnosticOrgStructure
                        )),
                    (self.tblAmbCardCureActions, self.updateAmbCardCure, self.cmbAmbCardCureGroup,
                     self.getAmbCardFilter(
                        self.edtAmbCardCureBegDate,
                        self.edtAmbCardCureEndDate,
                        self.cmbAmbCardCureGroup,
                        self.edtAmbCardCureOffice,
                        self.cmbAmbCardCureOrgStructure
                        )),
                    (self.tblAmbCardMiscActions, self.updateAmbCardMisc, self.cmbAmbCardMiscGroup,
                     self.getAmbCardFilter(
                        self.edtAmbCardMiscBegDate,
                        self.edtAmbCardMiscEndDate,
                        self.cmbAmbCardMiscGroup,
                        self.edtAmbCardMiscOffice,
                        self.cmbAmbCardMiscOrgStructure
                        ))][index-1]
        elif index == self.tabAmbCardContent.indexOf(self.tabAmbCardSurvey):
            return (self.tblAmbCardSurveyActions, self.updateAmbCardSurvey, self.cmbAmbCardSurveyGroup,
                     self.getAmbCardFilter(
                        self.edtAmbCardSurveyBegDate,
                        self.edtAmbCardSurveyEndDate,
                        self.cmbAmbCardSurveyGroup,
                        self.edtAmbCardSurveyOffice,
                        self.cmbAmbCardSurveyOrgStructure
                        ))


    def _setActionsOrderByColumn(self, column):
        table, updateFunction, cmbActionType, filter = self.getCurrentActionsTable()
        table.setOrder(column)
        fieldName = table.model().cols()[column].fields()[0]
        updateFunction(filter, table.currentItemId(), fieldName)


    def ambCardTableDoubleClicked(self, table, cmbActionType):
        actionTypeId = None
        column = None
        actionId = table.currentItemId()
        if actionId:
            index = table.currentIndex()
            if index:
                row = index.row()
                column = index.column()
                record = index.model().getRecordByRow(row) if row >= 0 else None
                actionTypeId = forceRef(record.value('actionType_id')) if record else None
        cmbActionType.setValue(actionTypeId)
        self._setActionsOrderByColumn(column)


    # @pyqtSignature('QModelIndex')
    def on_tblAmbCardStatusActions_doubleClicked(self, index):
        self.ambCardTableDoubleClicked(self.tblAmbCardStatusActions, self.cmbAmbCardStatusGroup)


    # @pyqtSignature('QModelIndex')
    def on_tblAmbCardDiagnosticActions_doubleClicked(self, index):
        self.ambCardTableDoubleClicked(self.tblAmbCardDiagnosticActions, self.cmbAmbCardDiagnosticGroup)


    # @pyqtSignature('QModelIndex')
    def on_tblAmbCardCureActions_doubleClicked(self, index):
        self.ambCardTableDoubleClicked(self.tblAmbCardCureActions, self.cmbAmbCardCureGroup)


    # @pyqtSignature('QModelIndex')
    def on_tblAmbCardMiscActions_doubleClicked(self, index):
        self.ambCardTableDoubleClicked(self.tblAmbCardMiscActions, self.cmbAmbCardMiscGroup)


    def on_tblAmbCardSurveyActions_doubleClicked(self, index):
        self.ambCardTableDoubleClicked(self.tblAmbCardSurveyActions, self.cmbAmbCardSurveyGroup)



    def setSortingIndicator(self, tbl, col, asc):
        tbl.setSortingEnabled(True)
        tbl.horizontalHeader().setSortIndicator(col, Qt.AscendingOrder if asc else Qt.DescendingOrder)

    def setSortable(self, tbl, update_function=None):
        def on_click(col):
            hs = tbl.horizontalScrollBar().value()
            model = tbl.model()
            sortingCol = model.headerSortingCol.get(col, False)
            model.headerSortingCol = {}
            model.headerSortingCol[col] = not sortingCol
            if update_function:
                update_function()
            else:
                model.loadData()
            self.setSortingIndicator(tbl, col, not sortingCol)
            tbl.horizontalScrollBar().setValue(hs)
        header = tbl.horizontalHeader()
        header.setClickable(True)
        QObject.connect(header, SIGNAL('sectionClicked(int)'), on_click)

    def prepareActionTable(self, tbl, *actions):
        tbl.setEditTriggers(QtGui.QAbstractItemView.SelectedClicked | QtGui.QAbstractItemView.DoubleClicked)
        tbl.model().setReadOnly(True)
        tbl.addPopupCopyCell()
        tbl.addPopupSeparator()
        for action in actions:
            if action == '-':
                tbl.addPopupSeparator()
            else:
                tbl.addPopupAction(action)


    def destroy(self):
        self.tblAmbCardDiagnostics.setModel(None)
        self.tblAmbCardDiagnosticsVisits.setModel(None)
        self.tblAmbCardDiagnosticsAccompDiagnostics.setModel(None)
        self.tblAmbCardDiagnosticsActions.setModel(None)
        self.tblAmbCardDiagnosticsActionProperties.setModel(None)
        self.tblAmbCardStatusActions.setModel(None)
        self.tblAmbCardStatusActionProperties.setModel(None)
        self.tblAmbCardDiagnosticActions.setModel(None)
        self.tblAmbCardDiagnosticActionProperties.setModel(None)
        self.tblAmbCardCureActions.setModel(None)
        self.tblAmbCardCureActionProperties.setModel(None)
        self.tblAmbCardMiscActions.setModel(None)
        self.tblAmbCardMiscActionProperties.setModel(None)
        self.tblAmbCardAttachedFiles.setModel(None)
        self.tblAmbCardMonitoring.setModel(None)
        del self.modelAmbCardDiagnostics
        del self.modelAmbCardDiagnosticsVisits
        del self.modelAmbCardDiagnosticsAccompDiagnostics
        del self.modelAmbCardDiagnosticsActions
        del self.modelAmbCardDiagnosticsActionProperties
        del self.modelAmbCardStatusActions
        del self.modelAmbCardStatusActionProperties
        del self.modelAmbCardDiagnosticActions
        del self.modelAmbCardDiagnosticActionProperties
        del self.modelAmbCardCureActions
        del self.modelAmbCardCureActionProperties
        del self.modelAmbCardMiscActions
        del self.modelAmbCardMiscActionProperties
        del self.modelAmbCardFiles
        del self.modelAmbCardMonitoring


    def updateAmbCardDiagnostics(self, filter):
        """
            в соответствии с фильтром обновляет список Diagnostics на вкладке AmbCard/Diagnostics.
        """
        self.__ambCardDiagnosticsFilter = filter
        db = QtGui.qApp.db
        tableDiagnostic = db.table('Diagnostic')
        queryTable = tableDiagnostic
        tableEvent = db.table('Event')
        queryTable = queryTable.leftJoin(tableEvent, tableEvent['id'].eq(tableDiagnostic['event_id']))
        cond = [tableDiagnostic['deleted'].eq(0),
                tableEvent['deleted'].eq(0),
                tableEvent['client_id'].eq(self.currentClientId())]
        begDate = filter.get('begDate', None)
        if begDate:
            cond.append(tableDiagnostic['endDate'].ge(begDate))
        endDate = filter.get('endDate', None)
        if endDate:
            cond.append(tableDiagnostic['endDate'].le(endDate))
        eventPurposeId = filter.get('eventPurposeId', None)
        if eventPurposeId:
            tableEventType = db.table('EventType')
            queryTable = queryTable.leftJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
            cond.append(tableEventType['purpose_id'].eq(eventPurposeId))
        specialityId = filter.get('specialityId', None)
        if specialityId:
            cond.append(tableDiagnostic['speciality_id'].eq(specialityId))
        personId = filter.get('personId', None)
        if personId:
            cond.append(tableDiagnostic['person_id'].eq(personId))
        healthGroupId = filter.get('healthGroupId', None)
        if healthGroupId:
            cond.append(tableDiagnostic['healthGroup_id'].eq(healthGroupId))
        tableDiagnosisType = db.table('rbDiagnosisType')
        queryTable = queryTable.leftJoin(tableDiagnosisType, tableDiagnosisType['id'].eq(tableDiagnostic['diagnosisType_id']))
        cond.append(tableDiagnosisType['code'].inlist(['1', '2', '4']))
        orderBY = u'endDate DESC, id'
        def ref(table, id_name):
            return u'(select name from %s where id = Diagnostic.%s)' % (table, id_name) + u' %s'
        for key, value in self.tblAmbCardDiagnostics.model().headerSortingCol.items():
            if value:
                ASC = u'ASC'
            else:
                ASC = u'DESC'
            if key == 0:
                orderBY = ref(u'vrbPerson', u'person_id') % ASC
            elif key == 1:
                orderBY = ref(u'rbSpeciality', u'speciality_id') % ASC
            elif key == 2:
                orderBY = u'endDate %s' % ASC
            elif key == 3:
                orderBY = ref(u'rbDiagnosisType', u'diagnosisType_id') % ASC
            elif key == 4:
                orderBY = ref(u'rbHealthGroup', u'healthGroup_id') % ASC
            elif key == 5:
                orderBY = u'(select concat_ws("+",MKB,MKBEx) from Diagnosis where id = Diagnostic.diagnosis_id) %s' % ASC
            elif key == 6:
                orderBY = ref(u'rbDiseaseCharacter', u'character_id') % ASC
            elif key == 7:
                orderBY = ref(u'rbDiseasePhases', u'phase_id') % ASC
            elif key == 8:
                orderBY = ref(u'rbDiseaseStage', u'stage_id') % ASC
            elif key == 9:
                orderBY = ref(u'rbDispanser', u'dispanser_id') % ASC
            elif key == 10:
                orderBY = u'hospital %s' % ASC
            elif key == 11:
                orderBY = ref(u'rbTraumaType', u'traumaType_id') % ASC
            elif key == 12:
                orderBY = ref(u'rbDiagnosticResult', u'result_id') % ASC
            elif key == 13:
                orderBY = u'notes %s' % ASC
            elif key == 14:
                orderBY = u'freeInput %s' % ASC


        try:
            QtGui.QApplication.setOverrideCursor(QtGui.QCursor(Qt.WaitCursor))
            idList = db.getIdList(queryTable,
                           tableDiagnostic['id'].name(),
                           cond, orderBY)
            self.tblAmbCardDiagnostics.setIdList(idList, None)
        finally:
            QtGui.QApplication.restoreOverrideCursor()


    def focusAmbCardDiagnostics(self):
        self.tblAmbCardDiagnostics.setFocus(Qt.TabFocusReason)


    def updateAmbCardDiagnosticsInfo(self): # обновить таблички внизу AmbCardDiagnostic
        diagnosticId = self.tblAmbCardDiagnostics.currentItemId()
        if diagnosticId:
            eventId = forceRef(QtGui.qApp.db.translate('Diagnostic', 'id', diagnosticId, 'event_id'))
        else:
            eventId = None
        pageIndex = self.tabAmbCardDiagnosticDetails.currentIndex()
        if pageIndex == 0:
            self.updateAmbCardDiagnosticsEvent(eventId, diagnosticId)
        elif pageIndex == 1:
            self.updateAmbCardDiagnosticsVisits(eventId)
        elif pageIndex == 2:
            self.updateAmbCardDiagnosticsAccompDiagnostics(eventId, diagnosticId)
        elif pageIndex == 3:
            self.updateAmbCardDiagnosticsActions(eventId)


    def updateAmbCardDiagnosticsEvent(self, eventId, diagnosticId):
        db = QtGui.qApp.db
        if eventId:
            stmt = 'SELECT Event.externalId AS externalId, '\
                   'EventType.name AS eventTypeName, ' \
                   'Organisation.shortName AS orgName, ' \
                   'P1.name AS setPersonName, Event.setDate, ' \
                   'P2.name AS execPersonName, Event.execDate, ' \
                   'Event.isPrimary, Event.order, Event.nextEventDate, Event.nextEventDate, Event.payStatus, ' \
                   'rbResult.name AS result ' \
                   'FROM Event ' \
                   'LEFT JOIN EventType    ON EventType.id = Event.eventType_id ' \
                   'LEFT JOIN Organisation ON Organisation.id = Event.org_id ' \
                   'LEFT JOIN vrbPersonWithSpeciality AS P1 ON P1.id = Event.setPerson_id ' \
                   'LEFT JOIN vrbPersonWithSpeciality AS P2 ON P2.id = Event.execPerson_id ' \
                   'LEFT JOIN rbResult     ON rbResult.id = Event.result_id ' \
                   'WHERE Event.id=%d' % eventId
            query = db.query(stmt)
            if query.first():
                record=query.record()
            else:
                record=QtSql.QSqlRecord()
        else:
            record=QtSql.QSqlRecord()
        if diagnosticId:
            stmt = 'SELECT createPerson.name AS createName,  modifyPerson.name AS modityName, ' \
                   'Diagnosis.MKB, Diagnosis.MKBEx ' \
                   'FROM '\
                   'Diagnostic '\
                   'LEFT JOIN vrbPersonWithSpeciality AS createPerson ON createPerson.id = Diagnostic.createPerson_id '\
                   'LEFT JOIN vrbPersonWithSpeciality AS modifyPerson ON modifyPerson.id = Diagnostic.modifyPerson_id '\
                   'LEFT JOIN Diagnosis ON Diagnosis.id = Diagnostic.diagnosis_id '\
                   'WHERE Diagnostic.id=%d' % diagnosticId
            query = db.query(stmt)
            if query.first():
                diagnosticRecord=query.record()
            else:
                diagnosticRecord=QtSql.QSqlRecord()
        else:
            diagnosticRecord=QtSql.QSqlRecord()

        self.lblAmbCardEventExtIdValue.setText(forceString(record.value('externalId')))
        self.lblAmbCardEventTypeValue.setText(forceString(record.value('eventTypeName')))
        self.lblAmbCardEventOrgValue.setText(forceString(record.value('orgName')))
        self.lblAmbCardEventSetPersonValue.setText(forceString(record.value('setPersonName')))
        self.lblAmbCardEventSetDateValue.setText(forceString(record.value('setDate')))
        self.lblAmbCardEventExecPersonValue.setText(forceString(record.value('execPersonName')))
        self.lblAmbCardEventExecDateValue.setText(forceString(record.value('execDate')))
        self.lblAmbCardEventOrderValue.setText(getOrderText(forceInt(record.value('order'))))
        self.chkAmbCardEventPrimary.setChecked(forceInt(record.value('isPrimary'))==1)

        self.lblAmbCardEventCreatePersonValue.setText(forceString(diagnosticRecord.value('createName')))
        self.lblAmbCardEventModifyPersonValue.setText(forceString(diagnosticRecord.value('modifyName')))
        MKB = forceString(diagnosticRecord.value('MKB'))
        MKBName = getMKBName(MKB) if MKB else ''
        self.lblAmbCardEventDiagValue.setText(MKB)
        self.lblAmbCardEventDiagName.setText(MKBName)
        MKBEx = forceString(diagnosticRecord.value('MKBEx'))
        MKBExName = getMKBName(MKBEx) if MKBEx else ''
        self.lblAmbCardEventDiagExValue.setText(MKBEx)
        self.lblAmbCardEventDiagExName.setText(MKBExName)

        self.lblAmbCardEventNextDateValue.setText(forceString(forceDate(record.value('nextEventDate'))))
        self.lblAmbCardEventResultValue.setText(forceString(record.value('result')))
        self.lblAmbCardEventPayStatusValue.setText(payStatusText(forceInt(record.value('payStatus'))))



    def updateAmbCardVisitEvent(self, eventId, diagnosticId=None):
        # tabAmbCardVisit

        db = QtGui.qApp.db
        if eventId:
            stmt = 'SELECT Event.externalId AS externalId, '\
                   'EventType.name AS eventTypeName, ' \
                   'Organisation.shortName AS orgName, ' \
                   'P1.name AS setPersonName, Event.setDate, ' \
                   'P2.name AS execPersonName, Event.execDate, ' \
                   'Event.isPrimary, Event.order, Event.nextEventDate, Event.nextEventDate, Event.payStatus, ' \
                   'rbResult.name AS result ' \
                   'FROM Event ' \
                   'LEFT JOIN EventType    ON EventType.id = Event.eventType_id ' \
                   'LEFT JOIN Organisation ON Organisation.id = Event.org_id ' \
                   'LEFT JOIN vrbPersonWithSpeciality AS P1 ON P1.id = Event.setPerson_id ' \
                   'LEFT JOIN vrbPersonWithSpeciality AS P2 ON P2.id = Event.execPerson_id ' \
                   'LEFT JOIN rbResult     ON rbResult.id = Event.result_id ' \
                   'WHERE Event.id=%d' % eventId
            query = db.query(stmt)
            if query.first():
                record=query.record()
            else:
                record=QtSql.QSqlRecord()
        else:
            record=QtSql.QSqlRecord()
        if diagnosticId:
            stmt = 'SELECT createPerson.name AS createName,  modifyPerson.name AS modityName, ' \
                   'Diagnosis.MKB, Diagnosis.MKBEx ' \
                   'FROM '\
                   'Diagnostic '\
                   'LEFT JOIN vrbPersonWithSpeciality AS createPerson ON createPerson.id = Diagnostic.createPerson_id '\
                   'LEFT JOIN vrbPersonWithSpeciality AS modifyPerson ON modifyPerson.id = Diagnostic.modifyPerson_id '\
                   'LEFT JOIN Diagnosis ON Diagnosis.id = Diagnostic.diagnosis_id '\
                   'WHERE Diagnostic.id=%d' % diagnosticId
            query = db.query(stmt)
            if query.first():
                diagnosticRecord=query.record()
            else:
                diagnosticRecord=QtSql.QSqlRecord()
        else:
            diagnosticRecord=QtSql.QSqlRecord()

        self.lblAmbCardEventExtIdValue_2.setText(forceString(record.value('externalId')))
        self.lblAmbCardEventTypeValue_2.setText(forceString(record.value('eventTypeName')))
        self.lblAmbCardEventOrgValue_2.setText(forceString(record.value('orgName')))
        self.lblAmbCardEventSetPersonValue_2.setText(forceString(record.value('setPersonName')))
        self.lblAmbCardEventSetDateValue_2.setText(forceString(record.value('setDate')))
        self.lblAmbCardEventExecPersonValue_2.setText(forceString(record.value('execPersonName')))
        self.lblAmbCardEventExecDateValue_2.setText(forceString(record.value('execDate')))
        self.lblAmbCardEventOrderValue_2.setText(getOrderText(forceInt(record.value('order'))))
        self.chkAmbCardEventPrimary_2.setChecked(forceInt(record.value('isPrimary'))==1)

        self.lblAmbCardEventCreatePersonValue_2.setText(forceString(diagnosticRecord.value('createName')))
        self.lblAmbCardEventModifyPersonValue_2.setText(forceString(diagnosticRecord.value('modifyName')))

        MKB = forceString(diagnosticRecord.value('MKB'))
        MKBName = getMKBName(MKB) if MKB else ''
        self.lblAmbCardEventDiagValue_2.setText(MKB)
        self.lblAmbCardEventDiagName_2.setText(MKBName)

        MKBEx = forceString(diagnosticRecord.value('MKBEx'))
        MKBExName = getMKBName(MKBEx) if MKBEx else ''
        self.lblAmbCardEventDiagExValue_2.setText(MKBEx)
        self.lblAmbCardEventDiagExName_2.setText(MKBExName)

        self.lblAmbCardEventNextDateValue_2.setText(forceString(forceDate(record.value('nextEventDate'))))
        self.lblAmbCardEventResultValue_2.setText(forceString(record.value('result')))
        self.lblAmbCardEventPayStatusValue_2.setText(payStatusText(forceInt(record.value('payStatus'))))


    def updateAmbCardDiagnosticsVisits(self,  eventId):
        orderBY = u'date, id'
        def ref(tbl, id):
            return u'(select name from %s where id = Visit.%s)' % (tbl, id) + u' %s'
        for key, value in self.tblAmbCardDiagnosticsVisits.model().headerSortingCol.items():
            if value:
                ASC = u'ASC'
            else:
                ASC = u'DESC'
            if key == 0:
                orderBY = ref(u'rbScene', u'scene_id') % ASC
            elif key == 1:
                orderBY = u'date %s' % ASC
            elif key == 2:
                orderBY = ref(u'rbVisitType', u'visitType_id') % ASC
            elif key == 3:
                orderBY = ref(u'rbService', u'service_id') % ASC
            elif key == 4:
                orderBY = ref(u'vrbPersonWithSpeciality', u'person_id') % ASC
            elif key == 5:
                orderBY = u'isPrimary %s' % ASC
            elif key == 6:
                orderBY = u'createDatetime %s' % ASC
            elif key == 7:
                orderBY = u'modifyDatetime %s' % ASC

        if eventId:
            db = QtGui.qApp.db
            table = db.table('Visit')
            try:
                QtGui.QApplication.setOverrideCursor(QtGui.QCursor(Qt.WaitCursor))
                idList = db.getIdList(table,
                                      table['id'].name(),
                                      [table['event_id'].eq(eventId), table['deleted'].eq(0)],
                                      orderBY)
            finally:
                QtGui.QApplication.restoreOverrideCursor()
        else:
            idList = []
        self.tblAmbCardDiagnosticsVisits.setIdList(idList, None)


    def updateAmbCardDiagnosticsAccompDiagnostics(self, eventId, diagnosticId):
        orderBY = u'endDate, id'
        def ref(tbl, id):
            return u'(select name from %s where id = Diagnostic.%s)' % (tbl, id) + u' %s'
        for key, value in self.tblAmbCardDiagnosticsAccompDiagnostics.model().headerSortingCol.items():
            if value:
                ASC = u'ASC'
            else:
                ASC = u'DESC'
            if key == 0:
                orderBY = ref(u'vrbPerson', u'person_id') % ASC
            elif key == 1:
                orderBY = ref(u'rbSpeciality', u'speciality_id') % ASC
            elif key == 2:
                orderBY = u'endDate %s' % ASC
            elif key == 3:
                orderBY = ref(u'rbDiagnosisType', u'diagnosisType_id') % ASC
            elif key == 4:
                orderBY = ref(u'rbHealthGroup', u'healthGroup_id') % ASC
            elif key == 5:
                orderBY = u'(select concat_ws("+",MKB,MKBEx) from Diagnosis where id = Diagnostic.diagnosis_id) %s' % ASC
            elif key == 6:
                orderBY = ref(u'rbDiseaseCharacter', u'character_id') % ASC
            elif key == 7:
                orderBY = ref(u'rbDiseasePhases', u'phase_id') % ASC
            elif key == 8:
                orderBY = ref(u'rbDiseaseStage', u'stage_id') % ASC
            elif key == 9:
                orderBY = ref(u'rbDispanser', u'dispanser_id') % ASC
            elif key == 10:
                orderBY = u'hospital %s' % ASC
            elif key == 11:
                orderBY = ref(u'rbTraumaType', u'traumaType_id') % ASC
            elif key == 12:
                orderBY = ref(u'rbDiagnosticResult', u'result_id') % ASC
            elif key == 13:
                orderBY = u'notes %s' % ASC

        if eventId:
            db = QtGui.qApp.db
            table = db.table('Diagnostic')
            specialityId = db.translate(table, 'id', diagnosticId, 'speciality_id')
            tableDiagnosisType = db.table('rbDiagnosisType')
            queryTable = table.leftJoin(tableDiagnosisType, tableDiagnosisType['id'].eq(table['diagnosisType_id']))
            cond = [table['event_id'].eq(eventId),
                    table['deleted'].eq(0),
                    table['speciality_id'].eq(specialityId),
                    'NOT ('+tableDiagnosisType['code'].inlist(['1', '2', '4'])+')']
            try:
                QtGui.QApplication.setOverrideCursor(QtGui.QCursor(Qt.WaitCursor))
                idList = db.getIdList(queryTable, table['id'].name(), cond, orderBY)
            finally:
                QtGui.QApplication.restoreOverrideCursor()
        else:
            idList = []
        self.tblAmbCardDiagnosticsAccompDiagnostics.setIdList(idList, None)


    def updateAmbCardDiagnosticsActions(self, eventId):
        orderBY = u'endDate DESC, id'
        for key, value in self.tblAmbCardDiagnosticsActions.model().headerSortingCol.items():
            if value:
                ASC = u'ASC'
            else:
                ASC = u'DESC'
            if key == 0:
                orderBY = u"Action.directionDate %s" % ASC
            elif key == 1:
                orderBY = u"(select name from ActionType where id = Action.actionType_id) %s" % ASC
            elif key == 2:
                orderBY = u"Action.isUrgent %s" % ASC
            elif key == 3:
                orderBY = u"Action.status %s" % ASC
            elif key == 4:
                orderBY = u"Action.plannedEndDate %s" % ASC
            elif key == 5:
                orderBY = u"Action.begDate %s" % ASC
            elif key == 6:
                orderBY = u"Action.endDate %s" % ASC
            elif key == 7:
                orderBY = u"(select name from vrbPersonWithSpeciality where id = Action.setPerson_id) %s" % ASC
            elif key == 8:
                orderBY = u"(select name from vrbPersonWithSpeciality where id = Action.person_id) %s" % ASC
            elif key == 9:
                orderBY = u"Action.office %s" % ASC
            elif key == 10:
                orderBY = u"Action.note %s" % ASC
        if eventId:
            db = QtGui.qApp.db
            table = db.table('Action')
            try:
                QtGui.QApplication.setOverrideCursor(QtGui.QCursor(Qt.WaitCursor))
                idList = db.getIdList(table,
                                      table['id'].name(),
                                      [table['event_id'].eq(eventId),
                                       table['deleted'].eq(0),
                                       table['status'].ne(CActionStatus.withoutResult)
                                      ],
                                      orderBY)
            finally:
                QtGui.QApplication.restoreOverrideCursor()
        else:
            idList = []
        self.tblAmbCardDiagnosticsActions.setIdList(idList, None)


    def resetAmbCardFilter(self, edtBegDate, edtEndDate, cmbGroup, edtOffice, cmbOrgStructure):
        edtBegDate.setDate(QDate())
        edtEndDate.setDate(QDate())
        cmbGroup.setValue(None)
        edtOffice.setText('')
        cmbOrgStructure.setValue(None)


    def resetAmbCardSurveyFilter(self, edtBegDate, edtEndDate, cmbGroup, edtOffice, cmbOrgStructure):
        edtBegDate.setDate(QDate(QDate.currentDate().year(), 1, 1))
        edtEndDate.setDate(QDate().currentDate())
        cmbGroup.setValue(None)
        edtOffice.setText('')
        cmbOrgStructure.setValue(None)


    def getAmbCardFilter(self, edtBegDate, edtEndDate, cmbGroup, edtOffice, cmbOrgStructure):
        filter = {}
        filter['begDate'] = edtBegDate.date()
        filter['endDate'] = edtEndDate.date()
        filter['actionGroupId'] = cmbGroup.value()
        filter['office'] = forceString(edtOffice.text())
        filter['orgStructureId'] = cmbOrgStructure.value()
        return filter


    def selectAmbCardActions(self, filter, classCode, order, fieldName):
        return getClientActions(self.currentClientId(), filter, classCode, order, fieldName)

       
    def selectAmbCardVisits(self, filter, fieldName=u''):
        return getClientVisits(self.currentClientId(), filter, fieldName, self.tblAmbCardVisits)


    def updateAmbCardStatus(self, filter, posToId=None, fieldName=None):
        """
            в соответствии с фильтром обновляет список Actions на вкладке AmbCard/Status.
        """
        filter['excludeServiceType'] = CActionServiceType.survey
        self.__ambCardStatusFilter = filter
        order = self.tblAmbCardStatusActions.order() if self.tblAmbCardStatusActions.order() else ['Action.endDate DESC', 'id']
        self.tblAmbCardStatusActions.setIdList(self.selectAmbCardActions(filter, 0, order, fieldName), posToId)


    def focusAmbCardStatusActions(self):
        self.tblAmbCardStatusActions.setFocus(Qt.TabFocusReason)


    def updateAmbCardDiagnostic(self, filter, posToId=None, fieldName=None):
        """
            в соответствии с фильтром обновляет список Actions на вкладке AmbCard/Diagnostic.
        """
        filter['excludeServiceType'] = CActionServiceType.survey
        self.__ambCardDiagnosticFilter = filter
        order = self.tblAmbCardDiagnosticActions.order() if self.tblAmbCardDiagnosticActions.order() else ['Action.endDate DESC', 'id']
        self.tblAmbCardDiagnosticActions.setIdList(self.selectAmbCardActions(filter, 1, order, fieldName), posToId)


    def focusAmbCardDiagnosticActions(self):
        self.tblAmbCardDiagnosticActions.setFocus(Qt.TabFocusReason)


    def updateAmbCardCure(self, filter, posToId=None, fieldName=None):
        """
            в соответствии с фильтром обновляет список Actions на вкладке AmbCard/Cure.
        """
        filter['excludeServiceType'] = CActionServiceType.survey
        self.__ambCardCureFilter = filter
        order = self.tblAmbCardCureActions.order() if self.tblAmbCardCureActions.order() else ['Action.endDate DESC', 'id']
        self.tblAmbCardCureActions.setIdList(self.selectAmbCardActions(filter, 2, order, fieldName), posToId)


    def focusAmbCardCureActions(self):
        self.tblAmbCardCureActions.setFocus(Qt.TabFocusReason)


    def updateAmbCardMisc(self, filter, posToId=None, fieldName=None):
        """
            в соответствии с фильтром обновляет список Actions на вкладке AmbCard/Cure.
        """
        filter['excludeServiceType'] = CActionServiceType.survey
        self.__ambCardMiscFilter = filter
        order = self.tblAmbCardMiscActions.order() if self.tblAmbCardMiscActions.order() else ['Action.endDate DESC', 'id']
        self.tblAmbCardMiscActions.setIdList(self.selectAmbCardActions(filter, 3, order, fieldName), posToId)


    def focusAmbCardMiscActions(self):
        self.tblAmbCardMiscActions.setFocus(Qt.TabFocusReason)



    def updateAmbCardVisit(self, filter, fieldName=u''):
        self.__ambCardVisitsFilter = filter
        self.tblAmbCardVisits.setIdList(self.selectAmbCardVisits(filter, fieldName), None)


    def updateAmbCardSurvey(self, filter, posToId=None, fieldName=None):
        """
            в соответствии с фильтром обновляет список Actions на вкладке AmbCard/Survey.
        """
        filter['serviceType'] = CActionServiceType.survey
        self.__ambCardSurveyFilter = filter
        order = self.tblAmbCardSurveyActions.order() if self.tblAmbCardSurveyActions.order() else ['Action.endDate DESC', 'id']
        self.tblAmbCardSurveyActions.setIdList(self.selectAmbCardActions(filter, None, order, fieldName), posToId)


    def focusAmbCardSurveyActions(self):
        self.tblAmbCardSurveyActions.setFocus(Qt.TabFocusReason)


    #### AmbCard page: Diagnostics page ##############

    # @pyqtSignature('int')
    def on_cmbAmbCardDiagnosticsSpeciality_currentIndexChanged(self, index):
        self.cmbAmbCardDiagnosticsPerson.setSpecialityId(self.cmbAmbCardDiagnosticsSpeciality.value())


    # @pyqtSignature('QAbstractButton*')
    def on_cmdAmbCardDiagnosticsButtonBox_clicked(self, button):
        buttonCode = self.cmdAmbCardDiagnosticsButtonBox.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.on_cmdAmbCardDiagnosticsButtonBox_apply()
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.on_cmdAmbCardDiagnosticsButtonBox_reset()
            self.on_cmdAmbCardDiagnosticsButtonBox_apply()


   # @pyqtSignature('')
    def on_cmdAmbCardDiagnosticsButtonBox_reset(self):
        self.edtAmbCardDiagnosticsBegDate.setDate(QDate())
        self.edtAmbCardDiagnosticsEndDate.setDate(QDate())
        self.cmbAmbCardDiagnosticsPurpose.setValue(None)

        eventPurposeId = self.ambCardComboBoxFilters.get('eventPurposeId', '')
        specialityId = self.ambCardComboBoxFilters.get('specialityId', '')
        personId = self.ambCardComboBoxFilters.get('personId', '')

        if eventPurposeId:
            self.cmbAmbCardDiagnosticsPurpose.setFilter(u'id in (%s)' % eventPurposeId)
        else:
            self.cmbAmbCardDiagnosticsPurpose.setFilter(u'')

        self.cmbAmbCardDiagnosticsSpeciality.setValue(None)
        if specialityId:
            self.cmbAmbCardDiagnosticsSpeciality.setFilter(u'id in (%s)' % specialityId)
        else:
            self.cmbAmbCardDiagnosticsSpeciality.setFilter(u'')

        self.cmbAmbCardDiagnosticsPerson.setValue(None)
        if personId:
            self.cmbAmbCardDiagnosticsPerson.setFilter(u'vrbPersonWithSpecialityAndPost.id in (%s)' % personId)
        else:
            self.cmbAmbCardDiagnosticsPerson.setFilter(u'')
        self.cmbHealthGroup.setValue(None)


   # @pyqtSignature('')
    def on_cmdAmbCardDiagnosticsButtonBox_apply(self):
        filter = {}
        filter['begDate'] = self.edtAmbCardDiagnosticsBegDate.date()
        filter['endDate'] = self.edtAmbCardDiagnosticsEndDate.date()
        filter['eventPurposeId'] = self.cmbAmbCardDiagnosticsPurpose.value()
        filter['specialityId'] = self.cmbAmbCardDiagnosticsSpeciality.value()
        filter['personId'] = self.cmbAmbCardDiagnosticsPerson.value()
        filter['healthGroupId'] = self.cmbHealthGroup.value()
        self.updateAmbCardDiagnostics(filter)
        self.focusAmbCardDiagnostics()


    # @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelAmbCardDiagnostics_currentRowChanged(self, current, previous):
        self.updateAmbCardDiagnosticsInfo()



    # @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelAmbCardVisits_currentRowChanged(self, current, previous):
        if current and current.isValid():
            row = current.row()
            record = self.modelAmbCardVisits.getRecordByRow(row)
            self.updateAmbCardVisitEvent(forceRef(record.value('event_id')))
        else:
            self.updateAmbCardVisitEvent(None)


    # @pyqtSignature('int')
    def on_tabAmbCardDiagnosticDetails_currentChanged(self, index):
        self.updateAmbCardDiagnosticsInfo()


    def updateAmbCardPropertiesTable(self, index, tbl, previous=None):
        if previous and index.model():
            record = index.model().getRecordByRow(previous.row()) if previous.row() >= 0 else None
            actionTypeId = forceRef(record.value('actionType_id')) if record else None
            if actionTypeId:
                tbl.savePreferencesLoc(actionTypeId)
        row = index.row()
        record = index.model().getRecordByRow(row) if row >= 0 else None
        if record:
            clientId = self.currentClientId()
            if hasattr(self, 'currentClientSex'):
                clientSex = self.currentClientSex()
            if hasattr(self, 'currentClientAge'):
                clientAge = self.currentClientAge()
            if not hasattr(self, 'currentClientSex') or not hasattr(self, 'currentClientAge'):
                begDate = forceDate(record.value('begDate'))
                endDate = forceDate(record.value('endDate'))
                date = endDate if endDate else (begDate if begDate else QDate.currentDate())
                clientSex, clientAge = getClientSexAge(clientId, date)
            action = CAction(record=record)
#            tblProps.model().setAction(action, self.clientSex, self.clientAge)
            tbl.model().setAction2(action, clientId, clientSex, clientAge)
            setActionPropertiesColumnVisible(action._actionType, tbl)
            tbl.horizontalHeader().setStretchLastSection(True)
            tbl.resizeColumnsToContents()
            tbl.resizeRowsToContents()
            tbl.loadPreferencesLoc(tbl.preferencesLocal, action._actionType.id)
        else:
            tbl.model().setAction2(None, None)
    
    
    def updateAmbCardAttachedFiles(self, index, tbl, previous=None):
        row = index.row()
        record = index.model().getRecordByRow(row) if row >= 0 else None
        if record:
            action = CAction(record=record)
            if hasattr(QtGui.qApp, 'webDAVInterface'):
                storageInterface = QtGui.qApp.webDAVInterface
            else:
                storageInterface = None
            tbl.model().setInterface(storageInterface)
            tbl.model().setTable('Action_FileAttach')
            tbl.model().loadItems(forceRef(record.value('id')))
            tbl.resizeColumnsToContents()
            tbl.resizeRowsToContents()
            tbl.horizontalHeader().setStretchLastSection(True)
        else:
            if hasattr(QtGui.qApp, 'webDAVInterface'):
                storageInterface = QtGui.qApp.webDAVInterface
            else:
                storageInterface = None
            tbl.model().setInterface(storageInterface)
            tbl.model().setTable('Action_FileAttach')
            tbl.model().loadItems(None)


    def updateAmbCardPrintActionAction(self, index):
        row = index.row()
        record = index.model().getRecordByRow(row) if row >= 0 else None
        actionTypeId = forceRef(record.value('actionType_id')) if record else None
        actionType = CActionTypeCache.getById(actionTypeId) if actionTypeId else None
        context = actionType.context if actionType else None
        self.actAmbCardPrintAction.setContext(context, False)


    def on_btnAmbCardJournalClicked(self):
        dialog = CAmbCardJournalDialog(self, clientId=self.currentClientId())
        dialog.exec_()


    def on_btnAmbCardClicked(self):
        dialog = CAmbulatoryCardDialog(self, clientId=self.currentClientId())
        dialog.exec_()


    def getSurveyActions(self):
        # groupId = None
        # column = None
        actionIdList = []
        index = self.tblAmbCardSurveyActions.currentIndex()
        if index:
            row = index.row()
            # column = index.column()
            record = index.model().getRecordByRow(row) if row >= 0 else None
            actionTypeId = forceRef(record.value('actionType_id')) if record else None
            if actionTypeId:
                actionId = forceRef(record.value('id'))
                if actionId and actionId not in actionIdList:
                    actionIdList.append(actionId)
                modelIdList = self.modelAmbCardSurveyActions.idList()
                for id in modelIdList:
                    record = self.modelAmbCardSurveyActions.getRecordById(id)
                    if record:
                        actionTypeRecId = forceRef(record.value('actionType_id'))
                        if actionTypeRecId == actionTypeId:
                            actionId = forceRef(record.value('id'))
                            if actionId and actionId not in actionIdList:
                                actionIdList.append(actionId)
        return actionIdList


    def on_btnAmbCardGraphClicked(self):
        from Registry.GraphDialog import CGraphDialog
        from Reports.ReportView   import CPageFormat
        try:
            pageFormat = CPageFormat(pageSize=CPageFormat.A4, orientation=CPageFormat.Portrait, leftMargin=5, topMargin=5, rightMargin=5,  bottomMargin=5)
            actionIdList = self.getSurveyActions()
            view = CGraphDialog(self, pageFormat, actionIdList)
            view.setPeriod(self.edtAmbCardSurveyBegDate.date(), self.edtAmbCardSurveyEndDate.date())
            view.exec_()
        except:
            QtGui.qApp.logCurrentException()


#    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelAmbCardDiagnosticsActions_currentRowChanged(self, current, previous):
        self.updateAmbCardPropertiesTable(current, self.tblAmbCardDiagnosticsActionProperties, previous)
        self.updateAmbCardPrintActionAction(current)


    # @pyqtSignature('')
    def on_actDiagnosticsShowPropertyHistory_triggered(self):
        self.tblAmbCardDiagnosticsActionProperties.showHistory()


    # @pyqtSignature('')
    def on_actDiagnosticsShowPropertiesHistory_triggered(self):
        self.tblAmbCardDiagnosticsActionProperties.showHistoryEx()


    # @pyqtSignature('int')
    def on_tabAmbCardContent_currentChanged(self, index):
        if index == 0:
            name_menu_tab = 'Events'
        elif index == 6:
            name_menu_tab = 'Visits'
        else:
            name_menu_tab = 'Actions'
        menu = QtGui.QMenu()
        for itm in self.action_menu_dict[name_menu_tab]:
            menu.addAction(itm)
        self.btnAmbCardPrint.setMenu(menu)
        self.btnAmbCardGraph.setVisible(index == self.tabAmbCardContent.indexOf(self.tabAmbCardSurvey))
        if index == self.tabAmbCardContent.indexOf(self.tabAmbCardVisit):
            if not self.__ambCardVisitIsInitialised:
                self.on_cmdAmbCardVisitButtonBox_apply()
                self.__ambCardVisitIsInitialised = True
        elif index == self.tabAmbCardContent.indexOf(self.tabAttachedFiles):
            if not self.__ambCardFilesIsInitialised:
                self.modelAmbCardFiles.loadItems(self.currentClientId())
                self.tblAmbCardAttachedFiles.resetSortIndicator()
                self.__ambCardFilesIsInitialised = True
        elif index == self.tabAmbCardContent.indexOf(self.tabAmbCardMonitoring):
            self.updateAmbCardMonitoring(self.currentClientId())
        elif index == self.tabAmbCardContent.indexOf(self.tabAmbCardStatus):
            self.updateAmbCardPrintActionAction(self.tblAmbCardStatusActions.currentIndex())
        elif index == self.tabAmbCardContent.indexOf(self.tabAmbCardDiagnostic):
            self.updateAmbCardPrintActionAction(self.tblAmbCardDiagnosticActions.currentIndex())
        elif index == self.tabAmbCardContent.indexOf(self.tabAmbCardCure):
            self.updateAmbCardPrintActionAction(self.tblAmbCardCureActions.currentIndex())
        elif index == self.tabAmbCardContent.indexOf(self.tabAmbCardMisc):
            self.updateAmbCardPrintActionAction(self.tblAmbCardMiscActions.currentIndex())

        self.actAmbCardPrintActions.setVisible(index in (1, 2, 3, 4, 8))


    def updateAmbCardMonitoring(self, clientId):
        if not self.ambCardMonitoringIsInitialised and clientId:
            self.modelAmbCardMonitoring.loadItems(clientId)
            self.tblAmbCardMonitoring.resetSorting()
            self.ambCardMonitoringIsInitialised = True


#    @pyqtSignature('')
    def on_actAmbCardPrintEvents_triggered(self):
        filter = {'clientId':self.currentClientId()}
        if self.__ambCardDiagnosticsFilter:
            filter.update(self.__ambCardDiagnosticsFilter)
        CClientDiagnostics(self).oneShot(filter)


#    @pyqtSignature('int')
    def on_actAmbCardPrintVisitsHistory_printByTemplate(self, templateId):
        if templateId == -1:
            self.on_actAmbCardPrintVisits_triggered()
        else:
            context = CInfoContext()
            clientId = self.currentClientId()
            clientInfo = getClientInfo2(clientId)
            visitInfo = context.getInstance(CVisitInfo, self.tblAmbCardVisits.currentItemId())
            visitInfoList = context.getInstance(CVisitInfoListEx, tuple(self.tblAmbCardVisits.model().idList()))
            data = { 'client'       :clientInfo,
                     'visitList'    : visitInfoList,
                     'visit'        : visitInfo,
                     'filterVisitBegDate'     : CDateInfo(self.edtAmbCardVisitBegDate.date()),
                     'filterVisitEndDate'     : CDateInfo(self.edtAmbCardVisitEndDate.date()),
                     'filterVisitOrgStructure': context.getInstance(COrgStructureInfo, forceRef(self.cmbAmbCardVisitOrgStructure.value())),
                     'filterVisitSpeciality'  : context.getInstance(CSpecialityInfo, forceRef(self.cmbAmbCardVisitSpeciality.value())),
                     'filterVisitPerson'      : context.getInstance(CPersonInfo, forceRef(self.cmbAmbCardVisitPerson.value())),
                     'filterVisitEventType'   : context.getInstance(CEventTypeInfo, forceRef(self.cmbAmbCardVisitEventType.value())),
                     'filterVisitService'     : context.getInstance(CServiceInfo, forceRef(self.cmbAmbCardVisitService.value())),
                     'filterVisitScene'       : context.getInstance(CSceneInfo, forceRef(self.cmbAmbCardVisitScene.value())),
                     }
            QtGui.qApp.call(self, applyTemplate, (self, templateId, data))


#    @pyqtSignature('int')
    def on_actAmbCardPrintCaseHistory_printByTemplate(self, templateId):
        clientId = self.currentClientId()
        clientInfo = getClientInfo2(clientId)
        db = QtGui.qApp.db
        tableEvent = db.table('Event')
        tableDiagnostic = db.table('Diagnostic')
        table = tableEvent.leftJoin(tableDiagnostic, tableDiagnostic['event_id'].eq(tableEvent['id']))
        cond = tableDiagnostic['id'].inlist(self.modelAmbCardDiagnostics.idList())
        idList = db.getDistinctIdList(table, tableEvent['id'].name(), cond, [tableEvent['setDate'].name(), tableEvent['id'].name()])
        events = CLocEventInfoList(clientInfo.context, idList)
        diagnosises = CDiagnosisInfoList(clientInfo.context, clientId)
        getTempInvalidList = lambda begDate=None, endDate=None, types=None: CTempInvalidInfoList._get(clientInfo.context, clientId, begDate, endDate, types)
        data = {'client':clientInfo,
                'events':events,
                'diagnosises':diagnosises,
                'getTempInvalidList': getTempInvalidList,
                'tempInvalids':getTempInvalidList()}
        QtGui.qApp.call(self, applyTemplate, (self, templateId, data))


    # @pyqtSignature('')
    def on_mnuAmbCardPrintActions_aboutToShow(self):
        index = self.tabAmbCardContent.currentIndex()
        if index:
            table = [ self.tblAmbCardStatusActions,
                      self.tblAmbCardDiagnosticActions,
                      self.tblAmbCardCureActions,
                      self.tblAmbCardMiscActions,
                      None,
                      None,
                      None,
                      self.tblAmbCardSurveyActions,
                    ][index-1]
            if table:
                self.updateAmbCardPrintActionAction(table.currentIndex())


    # @pyqtSignature('int')
    def on_actAmbCardPrintAction_printByTemplate(self, templateId):
        index = self.tabAmbCardContent.currentIndex()
        if index:
            table = [ self.tblAmbCardStatusActions,
                      self.tblAmbCardDiagnosticActions,
                      self.tblAmbCardCureActions,
                      self.tblAmbCardMiscActions,
                      None,
                      None,
                      None,
                      self.tblAmbCardSurveyActions,
                    ][index-1]
            if table:
                actionId = table.currentItemId()
                if actionId:
                    eventId = forceRef(QtGui.qApp.db.translate('Action', 'id', actionId, 'event_id'))
                    context = CInfoContext()
                    eventInfo = context.getInstance(CEventInfo, eventId)
                    # eventActions = eventInfo.actions
                    # eventActions._idList = [actionId]
                    eventActions = []
                    for action_id in table.model().idList():
                        eventActions.append(context.getInstance(CActionInfo, action_id))
                    # eventActions._loaded = True
                    # currentActionIndex = 0
                    action = context.getInstance(CActionInfo, actionId)
                    data = { 'event' : eventInfo,
                             'action': action,
                             'client': eventInfo.client,
                             'actions': eventActions,
                             'currentActionIndex': 0,
                             'tempInvalid': None
                           }
                    QtGui.qApp.call(self, applyTemplate, (self, templateId, data))


    # @pyqtSignature('')
    def on_actAmbCardPrintActions_triggered(self):
        index = self.tabAmbCardContent.currentIndex()
        if index:
            table, title = [ (self.tblAmbCardStatusActions,      u'статус'),
                             (self.tblAmbCardDiagnosticActions,  u'диагностика'),
                             (self.tblAmbCardCureActions,        u'лечение'),
                             (self.tblAmbCardMiscActions,        u'прочие мероприятия'),
                           ][index-1]
            table.setReportHeader(u'Список мероприятий (%s) пациента' % title)
            table.setReportDescription(getClientBanner(self.currentClientId()))
            table.printContent()


#    @pyqtSignature('')
    def on_actAmbCardCopyAction_triggered(self):
        actionId = None
        index = self.tabAmbCardContent.currentIndex()
        if index:
            table = [ self.tblAmbCardStatusActions,
                      self.tblAmbCardDiagnosticActions,
                      self.tblAmbCardCureActions,
                      self.tblAmbCardMiscActions,
                    ][index-1]
            model = table.model()
            row = table.currentIndex().row()
            if 0 <= row < (model.rowCount()):
                actionId = model.idList()[row]
        self.emit(SIGNAL('actionSelected(int)'), actionId)


#    @pyqtSignature('int')
    def on_actAmbCardPrintActionsHistory_printByTemplate(self, templateId):
        index = self.tabAmbCardContent.currentIndex()
        if index:
            clientId = self.currentClientId()
            clientInfo = getClientInfo2(clientId)
            model = [ self.modelAmbCardStatusActions,
                      self.modelAmbCardDiagnosticActions,
                      self.modelAmbCardCureActions,
                      self.modelAmbCardMiscActions,
                    ][index-1]
            idList = model.idList()
            actions = CLocActionInfoList(clientInfo.context, idList, clientInfo.sexCode, clientInfo.ageTuple)
            diagnosises = CDiagnosisInfoList(clientInfo.context, clientId)
            getTempInvalidList = lambda begDate=None, endDate=None, types=None: CTempInvalidInfoList._get(clientInfo.context, clientId, begDate, endDate, types)
            data = {'client':clientInfo,
                    'actions':actions,
                    'diagnosises':diagnosises,
                    'getTempInvalidList': getTempInvalidList,
                    'tempInvalids':getTempInvalidList()}
            QtGui.qApp.call(self, applyTemplate, (self, templateId, data))

    #### AmbCard page: Status page ###################

    # @pyqtSignature('QAbstractButton*')
    def on_cmdAmbCardStatusButtonBox_clicked(self, button):
        buttonCode = self.cmdAmbCardStatusButtonBox.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.on_cmdAmbCardStatusButtonBox_apply()
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.on_cmdAmbCardStatusButtonBox_reset()
            self.on_cmdAmbCardStatusButtonBox_apply()


#    @pyqtSignature('')
    def on_cmdAmbCardStatusButtonBox_reset(self):
        self.resetAmbCardFilter(self.edtAmbCardStatusBegDate,
                                self.edtAmbCardStatusEndDate,
                                self.cmbAmbCardStatusGroup,
                                self.edtAmbCardStatusOffice,
                                self.cmbAmbCardStatusOrgStructure
                                )


#    @pyqtSignature('')
    def on_cmdAmbCardStatusButtonBox_apply(self):
        filter = self.getAmbCardFilter(
                        self.edtAmbCardStatusBegDate,
                        self.edtAmbCardStatusEndDate,
                        self.cmbAmbCardStatusGroup,
                        self.edtAmbCardStatusOffice,
                        self.cmbAmbCardStatusOrgStructure
                        )
        self.updateAmbCardStatus(filter)
        self.focusAmbCardStatusActions()


    def on_cmdAmbCardSurveyButtonBox_clicked(self, button):
        buttonCode = self.cmdAmbCardSurveyButtonBox.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.on_cmdAmbCardSurveyButtonBox_apply()
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.on_cmdAmbCardSurveyButtonBox_reset()
            self.on_cmdAmbCardSurveyButtonBox_apply()


    def on_cmdAmbCardSurveyButtonBox_reset(self):
        self.resetAmbCardSurveyFilter(self.edtAmbCardSurveyBegDate,
                                      self.edtAmbCardSurveyEndDate,
                                      self.cmbAmbCardSurveyGroup,
                                      self.edtAmbCardSurveyOffice,
                                      self.cmbAmbCardSurveyOrgStructure
                                     )


    def on_cmdAmbCardSurveyButtonBox_apply(self):
        filter = self.getAmbCardFilter(
                        self.edtAmbCardSurveyBegDate,
                        self.edtAmbCardSurveyEndDate,
                        self.cmbAmbCardSurveyGroup,
                        self.edtAmbCardSurveyOffice,
                        self.cmbAmbCardSurveyOrgStructure
                        )
        self.updateAmbCardSurvey(filter)
        self.focusAmbCardSurveyActions()


#    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelAmbCardStatusActions_currentRowChanged(self, current, previous):
        isF090ActionType = False
        index = self.tblAmbCardStatusActions.currentIndex()
        if index:
            row = index.row()
            record = index.model().getRecordByRow(row) if row >= 0 else None
            actionId = forceRef(record.value('id')) if record else None
            if actionId and forceBool(self.getF090ActionTypeId(actionId)):
                isF090ActionType = True
        if not isF090ActionType:
            self.updateAmbCardPropertiesTable(current, self.tblAmbCardStatusActionProperties, previous)
        self.updateAmbCardPrintActionAction(current)


    # @pyqtSignature('')
    def on_actStatusShowPropertyHistory_triggered(self):
        self.tblAmbCardStatusActionProperties.showHistory()


    # @pyqtSignature('')
    def on_actStatusShowPropertiesHistory_triggered(self):
        self.tblAmbCardStatusActionProperties.showHistoryEx()


    def on_actSurveyShowPropertyHistory_triggered(self):
        self.tblAmbCardSurveyActionProperties.showHistory()


    def on_actSurveyShowPropertiesHistory_triggered(self):
        self.tblAmbCardSurveyActionProperties.showHistoryEx()


    def on_selectionModelAmbCardSurveyActions_currentRowChanged(self, current, previous):
        self.updateAmbCardPropertiesTable(current, self.tblAmbCardSurveyActionProperties, previous)

    #### AmbCard page: Diagnostic page ###################

    # @pyqtSignature('QAbstractButton*')
    def on_cmdAmbCardDiagnosticButtonBox_clicked(self, button):
        buttonCode = self.cmdAmbCardDiagnosticButtonBox.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.on_cmdAmbCardDiagnosticButtonBox_apply()
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.on_cmdAmbCardDiagnosticButtonBox_reset()
            self.on_cmdAmbCardDiagnosticButtonBox_apply()


#    @pyqtSignature('')
    def on_cmdAmbCardDiagnosticButtonBox_reset(self):
        self.resetAmbCardFilter(self.edtAmbCardDiagnosticBegDate,
                                self.edtAmbCardDiagnosticEndDate,
                                self.cmbAmbCardDiagnosticGroup,
                                self.edtAmbCardDiagnosticOffice,
                                self.cmbAmbCardDiagnosticOrgStructure
                                )


#    @pyqtSignature('')
    def on_cmdAmbCardDiagnosticButtonBox_apply(self):
        filter = self.getAmbCardFilter(
                        self.edtAmbCardDiagnosticBegDate,
                        self.edtAmbCardDiagnosticEndDate,
                        self.cmbAmbCardDiagnosticGroup,
                        self.edtAmbCardDiagnosticOffice,
                        self.cmbAmbCardDiagnosticOrgStructure
                        )
        self.updateAmbCardDiagnostic(filter)
        self.focusAmbCardDiagnosticActions()


    # @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelAmbCardDiagnosticActions_currentRowChanged(self, current, previous):
        self.updateAmbCardPropertiesTable(current, self.tblAmbCardDiagnosticActionProperties, previous)
        self.updateAmbCardPrintActionAction(current)


    # @pyqtSignature('')
    def on_actDiagnosticShowPropertyHistory_triggered(self):
        self.tblAmbCardDiagnosticActionProperties.showHistory()


    # @pyqtSignature('')
    def on_actDiagnosticShowPropertiesHistory_triggered(self):
        self.tblAmbCardDiagnosticActionProperties.showHistoryEx()

    #### AmbCard page: Cure page ###################

    # @pyqtSignature('QAbstractButton*')
    def on_cmdAmbCardCureButtonBox_clicked(self, button):
        buttonCode = self.cmdAmbCardCureButtonBox.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.on_cmdAmbCardCureButtonBox_apply()
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.on_cmdAmbCardCureButtonBox_reset()
            self.on_cmdAmbCardCureButtonBox_apply()

#    @pyqtSignature('')
    def on_cmdAmbCardCureButtonBox_reset(self):
        self.resetAmbCardFilter(self.edtAmbCardCureBegDate,
                                self.edtAmbCardCureEndDate,
                                self.cmbAmbCardCureGroup,
                                self.edtAmbCardCureOffice,
                                self.cmbAmbCardCureOrgStructure
                                )


#    @pyqtSignature('')
    def on_cmdAmbCardCureButtonBox_apply(self):
        filter = self.getAmbCardFilter(
                        self.edtAmbCardCureBegDate,
                        self.edtAmbCardCureEndDate,
                        self.cmbAmbCardCureGroup,
                        self.edtAmbCardCureOffice,
                        self.cmbAmbCardCureOrgStructure
                        )
        self.updateAmbCardCure(filter)
        self.focusAmbCardCureActions()


    # @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelAmbCardCureActions_currentRowChanged(self, current, previous):
        self.updateAmbCardPropertiesTable(current, self.tblAmbCardCureActionProperties, previous)
        self.updateAmbCardPrintActionAction(current)


    # @pyqtSignature('')
    def on_actCureShowPropertyHistory_triggered(self):
        self.tblAmbCardCureActionProperties.showHistory()


    # @pyqtSignature('')
    def on_actCureShowPropertiesHistory_triggered(self):
        self.tblAmbCardCureActionProperties.showHistoryEx()

    ### AmbCard page: Visit page ###################

    # @pyqtSignature('QAbstractButton*')
    def on_cmdAmbCardVisitButtonBox_clicked(self, button):
        buttonCode = self.cmdAmbCardVisitButtonBox.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.on_cmdAmbCardVisitButtonBox_apply()
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.on_cmdAmbCardVisitButtonBox_reset()
            self.on_cmdAmbCardVisitButtonBox_apply()


#    @pyqtSignature('')
    def on_cmdAmbCardVisitButtonBox_reset(self):
        self.edtAmbCardVisitBegDate.setDate(QDate())
        self.edtAmbCardVisitEndDate.setDate(QDate())
        self.cmbAmbCardVisitOrgStructure.setValue(None)
        self.cmbAmbCardVisitSpeciality.setValue(None)
        if self.ambCardComboBoxFilters.has_key('visitSpecialityId'):
            self.cmbAmbCardVisitSpeciality.setFilter(u'id in (%s)'%self.ambCardComboBoxFilters['visitSpecialityId'])
        else:
            self.cmbAmbCardVisitSpeciality.setFilter(u'')
        self.cmbAmbCardVisitPerson.setValue(None)
        if self.ambCardComboBoxFilters.has_key('visitPersonId'):
            self.cmbAmbCardVisitPerson.setFilter(u'vrbPersonWithSpecialityAndPost.id in (%s)'%self.ambCardComboBoxFilters['visitPersonId'])
        else:
            self.cmbAmbCardVisitPerson.setFilter(u'')
        self.cmbAmbCardVisitScene.setValue(None)
        self.cmbAmbCardVisitEventType.setValue(None)
        if self.ambCardComboBoxFilters.has_key('visitEventTypeId'):
            self.cmbAmbCardVisitEventType.setFilter(u'id in (%s)'%self.ambCardComboBoxFilters['visitEventTypeId'])
        else:
            self.cmbAmbCardVisitEventType.setFilter(u'')
        self.cmbAmbCardVisitService.setValue(None)
        if self.ambCardComboBoxFilters.has_key('visitServiceId') and self.ambCardComboBoxFilters['visitServiceId']:
            self.cmbAmbCardVisitService.setFilter(u'id in (%s)'%self.ambCardComboBoxFilters['visitServiceId'])
        else:
            self.cmbAmbCardVisitService.setFilter(u'')


#    @pyqtSignature('')
    def on_cmdAmbCardVisitButtonBox_apply(self):
        filter = {}
        filter['begDate'] = self.edtAmbCardVisitBegDate.date()
        filter['endDate'] = self.edtAmbCardVisitEndDate.date()
        filter['orgStructureId'] = self.cmbAmbCardVisitOrgStructure.value()
        filter['specialityId'] = self.cmbAmbCardVisitSpeciality.value()
        filter['personId'] = self.cmbAmbCardVisitPerson.value()
        filter['sceneId'] = self.cmbAmbCardVisitScene.value()
        filter['eventTypeId'] = self.cmbAmbCardVisitEventType.value()
        filter['serviceId'] = self.cmbAmbCardVisitService.value()

        self.updateAmbCardVisit(filter)
        self.tblAmbCardVisits.setFocus(Qt.TabFocusReason)


    # @pyqtSignature('')
    def on_actAmbCardPrintVisits_triggered(self):
        filter = {'clientId':self.currentClientId()}
        if self.__ambCardVisitsFilter:
            filter.update(self.__ambCardVisitsFilter)
        filter['order'] = self.tblAmbCardVisits.order() if self.tblAmbCardVisits.order() else 'Visit.date ASC'
        CClientVisits(self).oneShot(filter)    


    #### AmbCard page: Misc page ###################

    # @pyqtSignature('QAbstractButton*')
    def on_cmdAmbCardMiscButtonBox_clicked(self, button):
        buttonCode = self.cmdAmbCardMiscButtonBox.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.on_cmdAmbCardMiscButtonBox_apply()
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.on_cmdAmbCardMiscButtonBox_reset()
            self.on_cmdAmbCardMiscButtonBox_apply()


#    @pyqtSignature('')
    def on_cmdAmbCardMiscButtonBox_reset(self):
        self.resetAmbCardFilter(self.edtAmbCardMiscBegDate,
                                self.edtAmbCardMiscEndDate,
                                self.cmbAmbCardMiscGroup,
                                self.edtAmbCardMiscOffice,
                                self.cmbAmbCardMiscOrgStructure
                                )


#    @pyqtSignature('')
    def on_cmdAmbCardMiscButtonBox_apply(self):
        filter = self.getAmbCardFilter(
                        self.edtAmbCardMiscBegDate,
                        self.edtAmbCardMiscEndDate,
                        self.cmbAmbCardMiscGroup,
                        self.edtAmbCardMiscOffice,
                        self.cmbAmbCardMiscOrgStructure
                        )
        self.updateAmbCardMisc(filter)
        self.focusAmbCardMiscActions()


    # @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelAmbCardMiscActions_currentRowChanged(self, current, previous):
        self.updateAmbCardPropertiesTable(current, self.tblAmbCardMiscActionProperties, previous)
        self.updateAmbCardPrintActionAction(current)


    # @pyqtSignature('')
    def on_actMiscShowPropertyHistory_triggered(self):
        self.tblAmbCardMiscActionProperties.showHistory()


    # @pyqtSignature('')
    def on_actMiscShowPropertiesHistory_triggered(self):
        self.tblAmbCardMiscActionProperties.showHistoryEx()


class CAmbCardMonitoringModel(QAbstractTableModel):
    def __init__(self, parent):
        QAbstractTableModel.__init__(self, parent)
        self.headers = []
        self.items = {}
        self.dates = []
        self.actionTypeIdList = []
        self.readOnly = False
        self.eventEditor = None


    def items(self):
        return self.items


    def setEventEditor(self, eventEditor):
        self.eventEditor = eventEditor


    def setReadOnly(self, value):
        self.readOnly = value


    def columnCount(self, index = None):
        return len(self.headers)


    def rowCount(self, index = None):
        return len(self.dates)


    def flags(self, index = QModelIndex()):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled


    def headerData(self, section, orientation, role = Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                header = self.headers[section]
                if header:
                    return QVariant(header[1])
        return QVariant()


    def loadHeader(self):
        self.headers = [[None, u'Дата', False]]
        if self.clientId:
            db = QtGui.qApp.db
            tableMonitoring = db.table('Client_Monitoring')
            tableAPTemplate = db.table('ActionPropertyTemplate')
            queryTable = tableMonitoring.innerJoin(tableAPTemplate, tableAPTemplate['id'].eq(tableMonitoring['propertyTemplate_id']))
            cond = [tableMonitoring['deleted'].eq(0),
                    tableAPTemplate['deleted'].eq(0),
                    tableMonitoring['client_id'].eq(self.clientId)
                    ]
            cols = [tableAPTemplate['id'],
                    tableAPTemplate['name']
                    ]
            records = db.getRecordList(queryTable, cols, cond, order='ActionPropertyTemplate.code, ActionPropertyTemplate.name')
            for record in records:
                header = [forceRef(record.value('id')),
                          forceString(record.value('name')),
                          True
                          ]
                self.headers.append(header)
        self.reset()


    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        row = index.row()
        if role == Qt.DisplayRole:
            if row < len(self.dates):
                dateHeader = self.dates[row]
                if column == 0:
                    if dateHeader:
                        return QVariant(dateHeader.toString('dd.MM.yyyy'))
                else:
                    if self.headers[column] and self.headers[column][0] and ((pyDate(dateHeader), self.headers[column][0]) in self.items.keys()):
                        keyScheme = (pyDate(dateHeader), self.headers[column][0])
                        item = self.items.get(keyScheme, None)
                        return toVariant(item[0]) if item else QVariant()
        elif role == Qt.ForegroundRole:
            if row < len(self.dates) and column > 0:
                dateHeader = self.dates[row]
                if self.headers[column] and self.headers[column][0] and ((pyDate(dateHeader), self.headers[column][0]) in self.items.keys()):
                    keyScheme = (pyDate(dateHeader), self.headers[column][0])
                    item = self.items.get(keyScheme, None)
                    evaluation = item[1] if item else None
                    if evaluation:
                        return QVariant(QtGui.QBrush(QtGui.QColor(255, 0, 0)))
        elif role == Qt.FontRole:
            if row < len(self.dates) and column > 0:
                dateHeader = self.dates[row]
                if self.headers[column] and self.headers[column][0] and ((pyDate(dateHeader), self.headers[column][0]) in self.items.keys()):
                    keyScheme = (pyDate(dateHeader), self.headers[column][0])
                    item = self.items.get(keyScheme, None)
                    evaluation = item[1] if item else None
                    if (evaluation and abs(evaluation) == 2):
                        font = QtGui.QFont()
                        font.setBold(True)
                        return QVariant(font)
        return QVariant()


    def loadItems(self, clientId):
        self.clientId = clientId
        self.headers = []
        self.items = {}
        self.dates = []
        propertyIdHeader = []
        if not self.clientId:
            self.reset()
            return
        self.loadHeader()
        if len(self.headers) > 1:
            for i, header in enumerate(self.headers):
                if i > 0:
                    propertyIdHeader.append(header[0])
            db = QtGui.qApp.db
            tableEvent = db.table('Event')
            tableAction = db.table('Action')
            tableActionType = db.table('ActionType')
            tableActionProperty = db.table('ActionProperty')
            tableActionPropertyType = db.table('ActionPropertyType')
            tableMonitoring = db.table('Client_Monitoring')
            tableAPTemplate = db.table('ActionPropertyTemplate')
            queryTable = tableEvent.innerJoin(tableAction, tableAction['event_id'].eq(tableEvent['id']))
            queryTable = queryTable.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
            queryTable = queryTable.innerJoin(tableActionProperty, tableActionProperty['action_id'].eq(tableAction['id']))
            queryTable = queryTable.innerJoin(tableActionPropertyType, tableActionPropertyType['actionType_id'].eq(tableActionType['id']))
            queryTable = queryTable.innerJoin(tableAPTemplate, tableAPTemplate['id'].eq(tableActionPropertyType['template_id']))
            queryTable = queryTable.innerJoin(tableMonitoring, tableMonitoring['propertyTemplate_id'].eq(tableAPTemplate['id']))
            cond = [tableEvent['client_id'].eq(self.clientId),
                    tableEvent['deleted'].eq(0),
                    tableAction['deleted'].eq(0),
                    tableAction['endDate'].isNotNull(),
                    tableActionPropertyType['template_id'].isNotNull(),
                    tableActionType['deleted'].eq(0),
                    tableActionPropertyType['deleted'].eq(0),
                    tableAPTemplate['deleted'].eq(0),
                    tableMonitoring['deleted'].eq(0),
                    tableActionProperty['deleted'].eq(0),
                    tableActionPropertyType['template_id'].inlist(propertyIdHeader),
                    tableActionProperty['type_id'].eq(tableActionPropertyType['id'])
                    ]
            cols = [u'DISTINCT ActionPropertyType.typeName, ActionPropertyType.valueDomain',]
            records = db.getRecordList(queryTable, cols, cond)
            cols = [tableAction['endDate'],
                    tableActionPropertyType['template_id'],
                    tableActionPropertyType['typeName'],
                    tableActionPropertyType['valueDomain'],
                    tableActionProperty['evaluation']
                    ]
            for record in records:
                queryTableProperty = queryTable
                typeName = forceString(record.value('typeName'))
                valueDomain = forceString(record.value('valueDomain'))
                propertyType = CActionPropertyValueTypeRegistry.get(typeName, valueDomain)
                if propertyType:
                    tablePropertyType = db.table(propertyType.getTableName())
                    queryTableProperty = queryTableProperty.leftJoin(tablePropertyType, db.joinAnd([tablePropertyType['id'].eq(tableActionProperty['id']), tablePropertyType['value'].trim()+' IS NOT NULL']))
                    cols.append(tablePropertyType['value'])
                    queryTable = queryTableProperty
            if len(cols) > 5:
                order = [u'Action.endDate DESC']
                records = db.getRecordList(queryTable, cols, cond, order)
                for record in records:
                    templateId = forceRef(record.value('template_id'))
                    endDate = forceDate(record.value('endDate'))
                    if templateId and endDate:
                        typeName = forceString(record.value('typeName'))
                        valueDomain = forceString(record.value('valueDomain'))
                        value = record.value('value')
                        propertyType = CActionPropertyValueTypeRegistry.get(typeName, valueDomain)
                        if propertyType:
                            valueProperty = propertyType.convertQVariantToPyValue(value) if type(value) == QVariant else value
                            if valueProperty:
                                evaluation = forceInt(record.value('evaluation'))
                                if endDate and endDate not in self.dates:
                                    self.dates.append(endDate)
                                if type(valueProperty) is int:
                                    reportLine = self.items.setdefault((pyDate(endDate), templateId), (0, None))
                                    reportLine = (reportLine[0] + valueProperty, evaluation)
                                    self.items[(pyDate(endDate), templateId)] = reportLine
                                elif type(valueProperty) is float:
                                    reportLine = self.items.setdefault((pyDate(endDate), templateId), (0.0, None))
                                    reportLine = (reportLine[0] + valueProperty, evaluation)
                                    self.items[(pyDate(endDate), templateId)] = reportLine
                                elif isinstance(valueProperty, basestring) or type(valueProperty) == QString:
                                    reportLine = self.items.setdefault((pyDate(endDate), templateId), ('', None))
                                    reportLine = ((reportLine[0] + u', ' + valueProperty) if reportLine[0] else valueProperty, evaluation)
                                    self.items[(pyDate(endDate), templateId)] = reportLine
                                else:
                                    reportLine = self.items.setdefault((pyDate(endDate), templateId), (None, None))
                                    reportLine = (valueProperty, evaluation)
                                    self.items[(pyDate(endDate), templateId)] = reportLine
        self.dates.sort(reverse=True)
        self.reset()


    def sort(self, column, order):
        self.dates.sort(reverse=bool(order))
        self.reset()

