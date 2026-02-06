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

import json
from collections import OrderedDict
from PyQt4 import QtGui, QtSql
from PyQt4.QtGui import QCheckBox, QTextEdit, QComboBox
from PyQt4.QtCore import (
    Qt,
    SIGNAL,
    QDate,
    QDateTime,
    QTime,
    QAbstractTableModel,
    QModelIndex,
    QVariant,
    QString,
    QObject,
    QChar, 
    pyqtSignature, 
    pyqtSlot
)

from F111.F111TableModels import (CSOPSvORNMTableModel, 
                                  CNVNBVARRSTableModel, 
                                  CNVNBARTableModel, 
                                  CNVNBSGVBTableModel, 
                                  CPreviousPregnancyModel,
                                  CPreviousPregnancyChildrenModel,
                                  )
from Events.AmbulatoryCardDialog import CAmbulatoryCardDialog
from library.Attach.AttachFilesTableFlag import CAttachFilesTableFlag
from library.DialogBase           import CConstructHelperMixin
from library.ICDUtils             import getMKBName
from library.PrintInfo            import CInfoContext, CDateInfo
from library.PrintTemplates       import applyTemplate, getPrintAction
from library.Utils                import CReadOnlyFilter, forceDate, forceBool, forceInt, forceRef, forceString, pyDate, toVariant, forceStringEx, trim, forceDateTime, forceTime, forceDouble, setPref
from library.TableView            import CTableView
from library.SortFilterProxyTableModel import CSortFilterProxyTableModel

from Events.Action                import CAction
from Events.ActionProperty.ActionPropertyValueType import CActionPropertyValueType
from Events.ActionProperty        import CActionPropertyValueTypeRegistry
from Events.ActionInfo            import CActionInfo, CActionTypeCache, CLocActionInfoList, CLocActionPropertyActionsInfoList
from Events.ActionPropertiesTable import CActionPropertiesTableModel, CActionPropertiesTableView
from Events.ActionStatus          import CActionStatus
from Events.AmbCardJournalDialog  import CAmbCardJournalDialog
from Events.EventInfo             import CEventInfo, CDiagnosisInfoList, CLocEventInfoList, CVisitInfoListEx, CVisitInfo, CEventTypeInfo, CSceneInfo
from Events.TempInvalidInfo       import CTempInvalidInfoList
from Events.Utils                 import getActionTypeDescendants, getOrderText, payStatusText, setActionPropertiesColumnVisible, getActionTypeIdListByFlatCode
from Events.ActionServiceType     import CActionServiceType
from Orgs.Utils                   import getOrgStructurePersonIdList, COrgStructureInfo
from Orgs.PersonInfo              import CPersonInfo
from RefBooks.Service.Info        import CServiceInfo
from RefBooks.Speciality.Info     import CSpecialityInfo
from Registry.RegistryTable       import (CAmbCardDiagnosticsAccompDiagnosticsTableModel,
                                          CAmbCardDiagnosticsActionsTableModel,
                                          CAmbCardDiagnosticsTableModel,
                                          CAmbCardDiagnosticsVisitsTableModel,
                                          CAmbCardStatusActionsTableModel,
                                          CAmbCardVisitTableModel,
                                          CAmbCardAttachedFilesTableModel,
                                          CRegistryActionsTableView
                                          )
from Registry.Utils               import getClientBanner, getClientInfo2, getClientSexAge, canChangePayStatusAdditional, canEditOtherpeopleAction
from Reports.ClientDiagnostics    import CClientDiagnostics
from Reports.ClientVisits         import CClientVisits



def getClientActions(clientId, filter, classCode, order=['Action.endDate DESC', 'Action.id'], fieldName=None, isKBiR=False):
    if not clientId:
        return []
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
    if isKBiR:
        actionTypeIdListByKBiR = getActionTypeIdListByFlatCode(u'111/y-20')
        if actionTypeIdListByKBiR:
            cond.append(tableAction['actionType_id'].inlist(actionTypeIdListByKBiR))
        else:
            return []
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
    if not clientId:
        return []
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
        #CConstructHelperMixin.__init__(self) что это?
        self.__ambCardVisitIsInitialised = False
        self.__ambCardFilesIsInitialised = False
        self.ambCardMonitoringIsInitialised = False
        self.__ambCardDiagnosticsFilter = {}
        self.__ambCardVisitsFilter = {}
        self.ambCardComboBoxFilters = {}
        self.docDateList = []
        self.signerIdList = []
        self.authorIdList = []
        self.eventEditor = None
        self.actionTypeIdListByKBiR = getActionTypeIdListByFlatCode(flatCode = u'111/y-20')
        #self.btnAmbCardJournal.clicked.connect(self.on_btnAmbCardJournal_clicked)

    def preSetupUi(self):
        self.addModels('AmbCardDiagnostics', CAmbCardDiagnosticsTableModel(self))
        self.addModels('AmbCardDiagnosticsSort', CAmbCardSortFilterProxyTableModel(self, self.modelAmbCardDiagnostics))
        self.addModels('AmbCardDiagnosticsVisits', CAmbCardDiagnosticsVisitsTableModel(self))
        self.addModels('AmbCardDiagnosticsAccompDiagnostics', CAmbCardDiagnosticsAccompDiagnosticsTableModel(self))
        self.addModels('AmbCardDiagnosticsActions', CAmbCardDiagnosticsActionsTableModel(self))
        self.addModels('AmbCardDiagnosticsActionProperties', CActionPropertiesTableModel(self))
        self.addModels('AmbCardStatusActions', CAmbCardStatusActionsTableModel(self))
        self.addModels('AmbCardStatusActionsSort', CAmbCardSortFilterProxyTableModel(self, self.modelAmbCardStatusActions))
        self.addModels('AmbCardStatusActionProperties', CActionPropertiesTableModel(self))
        self.addModels('AmbCardDiagnosticActions', CAmbCardStatusActionsTableModel(self))
        self.addModels('AmbCardDiagnosticActionsSort', CAmbCardSortFilterProxyTableModel(self, self.modelAmbCardDiagnosticActions))
        self.addModels('AmbCardDiagnosticActionProperties', CActionPropertiesTableModel(self))
        self.addModels('AmbCardCureActions', CAmbCardStatusActionsTableModel(self))
        self.addModels('AmbCardCureActionsSort', CAmbCardSortFilterProxyTableModel(self, self.modelAmbCardCureActions))
        self.addModels('AmbCardCureActionProperties', CActionPropertiesTableModel(self))
        self.addModels('AmbCardMiscActions', CAmbCardStatusActionsTableModel(self))
        self.addModels('AmbCardMiscActionsSort', CAmbCardSortFilterProxyTableModel(self, self.modelAmbCardMiscActions))
        self.addModels('AmbCardMiscActionProperties', CActionPropertiesTableModel(self))
        self.addModels('AmbCardVisits', CAmbCardVisitTableModel(self))
        self.addModels('AmbCardVisitsSort', CAmbCardSortFilterProxyTableModel(self, self.modelAmbCardVisits))
        self.addModels('AmbCardFiles', CAmbCardAttachedFilesTableModel(self))
        self.addModels('AmbCardSurveyActions', CAmbCardStatusActionsTableModel(self))
        self.addModels('AmbCardSurveyActionsSort', CAmbCardSortFilterProxyTableModel(self, self.modelAmbCardSurveyActions))
        self.addModels('AmbCardSurveyActionProperties', CActionPropertiesTableModel(self))
        self.addModels('AmbCardMonitoring', CAmbCardMonitoringModel(self))
        self.addModels('AmbCardKBiRActions', CAmbCardStatusActionsTableModel(self))
        self.addModels('AmbCardKBiRActionsSort', CAmbCardSortFilterProxyTableModel(self, self.modelAmbCardKBiRActions))
        self.addModels('AmbCardPreviousPregnancy', CPreviousPregnancyModel(self))
        self.addModels('AmbCardPreviousPregnancyChildren', CPreviousPregnancyChildrenModel(self))
        self.addModels('AmbCardSOPSvORNM', CSOPSvORNMTableModel(self))
        self.addModels('AmbCardNVNBVARRS', CNVNBVARRSTableModel(self))
        self.addModels('AmbCardNVNBAR', CNVNBARTableModel(self))
        self.addModels('AmbCardNVNBSGVB', CNVNBSGVBTableModel(self))

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
        self.addObject('actAmbCardActionTypeGroupId',         QtGui.QAction(u'Фильтровать по группе Действия', self))
        self.addObject('actAmbCardOpenActionELMK',            QtGui.QAction(u'Открыть обращение ЭЛМК', self))
        self.addObject('actAmbCardPrintAction',               getPrintAction(self, None, u'Напечатать по шаблону', False))
        self.addObject('actAmbCardPrintActions',              QtGui.QAction(u'Напечатать список мероприятий', self))
        self.addObject('actAmbCardPrintActionsHistory',       getPrintAction(self, 'actionsHistory', u'Напечатать карту мероприятий', False))
        self.addObject('actAmbCardCopyAction',                QtGui.QAction(u'Копировать свойства', self))
        self.addObject('actAmbCardCopyAsNewAction', QtGui.QAction(u'Скопировать документ в текущее обращение', self))

    def postSetupUi(self):
        self.setModels(self.tblAmbCardDiagnostics, self.modelAmbCardDiagnosticsSort, self.selectionModelAmbCardDiagnosticsSort)
        self.tblAmbCardDiagnostics.setSourceModel(self.modelAmbCardDiagnostics)
        self.setModels(self.tblAmbCardDiagnosticsVisits, self.modelAmbCardDiagnosticsVisits, self.selectionModelAmbCardDiagnosticsVisits)
        self.setModels(self.tblAmbCardDiagnosticsAccompDiagnostics, self.modelAmbCardDiagnosticsAccompDiagnostics, self.selectionModelAmbCardDiagnosticsAccompDiagnostics)
        self.setModels(self.tblAmbCardDiagnosticsActions, self.modelAmbCardDiagnosticsActions, self.selectionModelAmbCardDiagnosticsActions)
        self.setModels(self.tblAmbCardDiagnosticsActionProperties, self.modelAmbCardDiagnosticsActionProperties, self.selectionModelAmbCardDiagnosticsActionProperties)
        self.setModels(self.tblAmbCardStatusActions, self.modelAmbCardStatusActionsSort, self.selectionModelAmbCardStatusActionsSort)
        self.tblAmbCardStatusActions.setSourceModel(self.modelAmbCardStatusActions)
        self.setModels(self.tblAmbCardStatusActionProperties, self.modelAmbCardStatusActionProperties, self.selectionModelAmbCardStatusActionProperties)
        self.tblAmbCardStatusActionProperties.setSourceModel(self.modelAmbCardStatusActionProperties)
        self.setModels(self.tblAmbCardDiagnosticActions, self.modelAmbCardDiagnosticActionsSort, self.selectionModelAmbCardDiagnosticActionsSort)
        self.tblAmbCardDiagnosticActions.setSourceModel(self.modelAmbCardDiagnosticActions)
        self.setModels(self.tblAmbCardDiagnosticActionProperties, self.modelAmbCardDiagnosticActionProperties, self.selectionModelAmbCardDiagnosticActionProperties)
        self.tblAmbCardDiagnosticActionProperties.setSourceModel(self.modelAmbCardDiagnosticActionProperties)
        self.setModels(self.tblAmbCardCureActions, self.modelAmbCardCureActionsSort, self.selectionModelAmbCardCureActionsSort)
        self.tblAmbCardCureActions.setSourceModel(self.modelAmbCardCureActions)
        self.setModels(self.tblAmbCardCureActionProperties, self.modelAmbCardCureActionProperties, self.selectionModelAmbCardCureActionProperties)
        self.tblAmbCardCureActionProperties.setSourceModel(self.modelAmbCardCureActionProperties)
        self.setModels(self.tblAmbCardMiscActions, self.modelAmbCardMiscActionsSort, self.selectionModelAmbCardMiscActionsSort)
        self.tblAmbCardMiscActions.setSourceModel(self.modelAmbCardMiscActions)
        self.setModels(self.tblAmbCardMiscActionProperties, self.modelAmbCardMiscActionProperties, self.selectionModelAmbCardMiscActionProperties)
        self.tblAmbCardMiscActionProperties.setSourceModel(self.modelAmbCardMiscActionProperties)
        self.setModels(self.tblAmbCardVisits, self.modelAmbCardVisitsSort, self.selectionModelAmbCardVisitsSort)
        self.tblAmbCardVisits.setSourceModel(self.modelAmbCardVisits)
        self.setModels(self.tblAmbCardAttachedFiles, self.modelAmbCardFiles, self.selectionModelAmbCardFiles)
        self.setModels(self.tblAmbCardSurveyActions, self.modelAmbCardSurveyActionsSort, self.selectionModelAmbCardSurveyActionsSort)
        self.tblAmbCardSurveyActions.setSourceModel(self.modelAmbCardSurveyActions)
        self.setModels(self.tblAmbCardSurveyActionProperties, self.modelAmbCardSurveyActionProperties, self.selectionModelAmbCardSurveyActionProperties)
        self.tblAmbCardSurveyActionProperties.setSourceModel(self.modelAmbCardSurveyActionProperties)
        self.setModels(self.tblAmbCardMonitoring, self.modelAmbCardMonitoring, self.selectionModelAmbCardMonitoring)
        self.setModels(self.tblAmbCardKBiRActions, self.modelAmbCardKBiRActionsSort, self.selectionModelAmbCardKBiRActionsSort)
        self.tblAmbCardKBiRActions.setSourceModel(self.modelAmbCardKBiRActions)
        self.setModels(self.tblAmbCardPreviousPregnancy, self.modelAmbCardPreviousPregnancy, self.selectionModelAmbCardPreviousPregnancy)
        self.setModels(self.tblAmbCardPreviousPregnancyChildren, self.modelAmbCardPreviousPregnancyChildren, self.selectionModelAmbCardPreviousPregnancyChildren)
        self.setModels(self.tblAmbCardSOPSvORNM, self.modelAmbCardSOPSvORNM, self.selectionModelAmbCardSOPSvORNM)
        self.setModels(self.tblAmbCardNVNBVARRS, self.modelAmbCardNVNBVARRS, self.selectionModelAmbCardNVNBVARRS)
        self.setModels(self.tblAmbCardNVNBAR, self.modelAmbCardNVNBAR, self.selectionModelAmbCardNVNBAR)
        self.setModels(self.tblAmbCardNVNBSGVB, self.modelAmbCardNVNBSGVB, self.selectionModelAmbCardNVNBSGVB)

        self.tblAmbCardStatusActions.createPopupMenu([self.actAmbCardActionTypeGroupId, self.actAmbCardCopyAction, self.actAmbCardOpenActionELMK])
        self.tblAmbCardDiagnosticActions.createPopupMenu([self.actAmbCardActionTypeGroupId, self.actAmbCardCopyAction])
        self.tblAmbCardCureActions.createPopupMenu([self.actAmbCardActionTypeGroupId, self.actAmbCardCopyAction])
        self.tblAmbCardMiscActions.createPopupMenu([self.actAmbCardActionTypeGroupId, self.actAmbCardCopyAction])
        self.tblAmbCardSurveyActions.createPopupMenu([self.actAmbCardActionTypeGroupId, self.actAmbCardCopyAction])
        self.tblAmbCardKBiRActions.createPopupMenu([self.actAmbCardActionTypeGroupId, ])

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
        self.cmbAmbCardFilesEventType.setTable('EventType')
        self.cmbAmbCardFilesEventType.setValue(None)
        # self.cmbAmbCardFilesActionTypeGroup.setTable('ActionTypeGroup')
        # self.cmbAmbCardFilesActionTypeGroup.setValue(None)
        self.cmbAmbCardFilesActionType.setTable('ActionType')
        self.cmbAmbCardFilesActionType.setValue(None)
        self.edtAmbCardSurveyBegDate.setDate(QDate(QDate.currentDate().year(), 1, 1))  # btnAmbCardGraphClicked

        self.connect(self.tblAmbCardDiagnostics.horizontalHeader(), SIGNAL('sectionClicked(int)'), self._setActionsOrderByColumn)
        self.connect(self.tblAmbCardStatusActions.horizontalHeader(), SIGNAL('sectionClicked(int)'), self._setActionsOrderByColumn)
        self.connect(self.tblAmbCardDiagnosticActions.horizontalHeader(), SIGNAL('sectionClicked(int)'), self._setActionsOrderByColumn)
        self.connect(self.tblAmbCardCureActions.horizontalHeader(), SIGNAL('sectionClicked(int)'), self._setActionsOrderByColumn)
        self.connect(self.tblAmbCardMiscActions.horizontalHeader(), SIGNAL('sectionClicked(int)'), self._setActionsOrderByColumn)
        self.connect(self.tblAmbCardKBiRActions.horizontalHeader(), SIGNAL('sectionClicked(int)'), self._setActionsOrderByColumn)
        self.connect(self.tblAmbCardVisits.horizontalHeader(), SIGNAL('sectionClicked(int)'), self.onHeaderAmbCardVisitsColClicked)
        self.connect(self.btnAmbCardJournal,  SIGNAL('clicked()'),  self.on_btnAmbCardJournalClicked)
        self.connect(self.btnAmbCardGraph,  SIGNAL('clicked()'),  self.on_btnAmbCardGraphClicked)
        self.connect(self.tblAmbCardSurveyActions.horizontalHeader(), SIGNAL('sectionClicked(int)'), self._setActionsOrderByColumn)
        self.connect(self.btnAmbCard, SIGNAL('clicked()'), self.on_btnAmbCardClicked)

        self.tblAmbCardStatusActions.enableColsHide()
        self.tblAmbCardDiagnosticActions.enableColsHide()
        self.tblAmbCardCureActions.enableColsHide()
        self.tblAmbCardMiscActions.enableColsHide()
        self.tblAmbCardKBiRActions.enableColsHide()
        self.tblAmbCardStatusActions.enableColsMove()
        self.tblAmbCardDiagnosticActions.enableColsMove()
        self.tblAmbCardCureActions.enableColsMove()
        self.tblAmbCardMiscActions.enableColsMove()
        self.tblAmbCardKBiRActions.enableColsMove()
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
        self.ambCardContentTabEnabled()
        self.cmbAmbCardFilesAuthor.setTable('vrbPerson')
        self.cmbAmbCardFilesSigner.setTable('vrbPerson')
        self.modelAmbCardSOPSvORNM.setEventEditor(self)
        self.modelAmbCardNVNBVARRS.setEventEditor(self)
        self.modelAmbCardNVNBAR.setEventEditor(self)
        self.modelAmbCardNVNBSGVB.setEventEditor(self)
        self.modelAmbCardNVNBAR.setReadOnly(True)
        self.setInitDate()
        self.setWidgetsVisible(False)
        self.setComoboBoxWheel()
        self.setReferenceComboBoxes()
        self.setKBirReadOnly(True)
        self.tblAmbCardNVNBVARRS.resizeRowsToContents()
        self.tblAmbCardNVNBVARRS.resizeColumnsToContents()
        rowHeight = self.tblAmbCardNVNBVARRS.rowHeight(0)
        headerHeight = self.tblAmbCardNVNBVARRS.horizontalHeader().height()
        margin = 2 * self.tblAmbCardNVNBVARRS.frameWidth()
        maxHeight = headerHeight + rowHeight * 7 + margin
        self.tblAmbCardNVNBVARRS.setMaximumHeight(headerHeight + rowHeight * 7 + margin)
        self.tblAmbCardNVNBAR.setMaximumHeight(headerHeight + rowHeight * 5 + margin)
        self.tblAmbCardSOPSvORNM.setMaximumHeight(headerHeight + rowHeight * 4 + margin)
        
        self.modelAmbCardPreviousPregnancy.setReadOnly(True)
        self.modelAmbCardPreviousPregnancyChildren.setReadOnly(True)
        
        self.tblAmbCardDiagnostics.setSortingEnabled(True)
        self.tblAmbCardStatusActions.setSortingEnabled(True)
        self.tblAmbCardStatusActionProperties.setSortingEnabled(True)
        self.tblAmbCardDiagnosticActions.setSortingEnabled(True)
        self.tblAmbCardDiagnosticActionProperties.setSortingEnabled(True)
        self.tblAmbCardCureActions.setSortingEnabled(True)
        self.tblAmbCardCureActionProperties.setSortingEnabled(True)
        self.tblAmbCardMiscActions.setSortingEnabled(True)
        self.tblAmbCardMiscActionProperties.setSortingEnabled(True)
        self.tblAmbCardSurveyActions.setSortingEnabled(True)
        self.tblAmbCardSurveyActionProperties.setSortingEnabled(True)
        self.tblAmbCardVisits.setSortingEnabled(True)
        self.tblAmbCardKBiRActions.setSortingEnabled(True)


    def ambCardContentTabEnabled(self):
        if hasattr(self, 'tabAmbCardKBiR'):
            indexAmbCardKBiR = self.tabAmbCardContent.indexOf(self.tabAmbCardKBiR)
            clientSex = None
            clientId = self.currentClientId()
            if hasattr(self, 'currentClientSex'):
                clientSex = self.currentClientSex()
            elif clientId and not clientSex:
                clientSex, clientAge = getClientSexAge(clientId, QDate.currentDate())
#            self.tabAmbCardContent.setTabEnabled(indexAmbCardKBiR, clientSex != 1)
            if indexAmbCardKBiR == -1 and clientSex != 1:
                self.tabAmbCardContent.addTab(self.tabAmbCardKBiR, u'Карты беременной и роженицы')
            elif indexAmbCardKBiR > -1 and clientSex == 1:
                self.tabAmbCardContent.removeTab(self.tabAmbCardContent.indexOf(self.tabAmbCardKBiR))

    def on_mnuPopup_aboutToShow(self):
        fileItem = self.tblAmbCardAttachedFiles.getCurrentFileItem()
        if fileItem.isLost:
            pass


    def setEventEditor(self, eventEditor):
        self.eventEditor = eventEditor
        self.addCopyAsNewActions()

    def onHeaderAmbCardVisitsColClicked(self, column):
        self.tblAmbCardVisits.setOrder(column)
        filter = {'begDate': self.edtAmbCardVisitBegDate.date(),
                  'endDate': self.edtAmbCardVisitEndDate.date(),
                  'orgStructureId': self.cmbAmbCardVisitOrgStructure.value(),
                  'specialityId': self.cmbAmbCardVisitSpeciality.value(),
                  'personId': self.cmbAmbCardVisitPerson.value(),
                  'sceneId': self.cmbAmbCardVisitScene.value(),
                  'eventTypeId': self.cmbAmbCardVisitEventType.value(),
                  'serviceId': self.cmbAmbCardVisitService.value()}
        self.updateAmbCardVisit(filter, self.tblAmbCardVisits.model().cols()[column].fields()[0])
        self.tblAmbCardVisits.setFocus(Qt.TabFocusReason)


    def savePreferencesLoc(self):
        if self._clientId:
            preferences = self.tblAmbCardMonitoring.savePreferences()
            setPref(QtGui.qApp.preferences.windowPrefs, u'CAmbCardMonitoringInDocTableView_%s'%(str(self._clientId)), preferences)
        
        
    def resetWidgets(self):
        self.ambCardContentTabEnabled()
        self.getComboBoxesFilterParamsByClient(self._clientId)
        self.on_cmdAmbCardDiagnosticsButtonBox_reset()
        self.on_cmdAmbCardStatusButtonBox_reset()
        self.on_cmdAmbCardDiagnosticButtonBox_reset()
        self.on_cmdAmbCardCureButtonBox_reset()
        self.on_cmdAmbCardMiscButtonBox_reset()
        self.on_cmdAmbCardVisitButtonBox_reset()
        self.on_cmdAmbCardSurveyButtonBox_reset()
        self.on_cmdAmbCardKBiRButtonBox_reset()

        self.on_cmdAmbCardDiagnosticsButtonBox_apply()
        self.on_cmdAmbCardStatusButtonBox_apply()
        self.on_cmdAmbCardDiagnosticButtonBox_apply()
        self.on_cmdAmbCardCureButtonBox_apply()
        self.on_cmdAmbCardMiscButtonBox_apply()
        self.on_cmdAmbCardSurveyButtonBox_apply()
        self.on_cmdAmbCardFilesButtonBox_apply()
        self.on_cmdAmbCardKBiRButtonBox_apply()

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
        self.actAmbCardCopyAsNewAction.setEnabled(False)
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
            if actionId:
                actionTypeId = forceRef(record.value('actionType_id')) if record else None
                self.actAmbCardCopyAsNewAction.setEnabled(
                    CActionTypeCache.getById(actionTypeId).showInForm if actionTypeId else False)

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
        self.actAmbCardCopyAsNewAction.setEnabled(False)
        index = self.tblAmbCardCureActions.currentIndex()
        if index:
            row = index.row()
            record = index.model().getRecordByRow(row) if row >= 0 else None
            actionId = forceRef(record.value('id')) if record else None
            if actionId:
                actionTypeId = forceRef(record.value('actionType_id')) if record else None
                self.actAmbCardCopyAsNewAction.setEnabled(
                    CActionTypeCache.getById(actionTypeId).showInForm if actionTypeId else False)

    # @pyqtSignature('')
    def on_tblAmbCardMiscActions_popupMenuAboutToShow(self):
        notEmpty = self.modelAmbCardMiscActions.rowCount() > 0
        self.actAmbCardActionTypeGroupId.setEnabled(notEmpty)
        self.actAmbCardCopyAction.setEnabled(notEmpty)

#    @pyqtSignature('')
    def on_tblAmbCardKBiRActions_popupMenuAboutToShow(self):
        notEmpty = self.modelAmbCardKBiRActions.rowCount() > 0
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
        elif index == self.tabAmbCardContent.indexOf(self.tabAmbCardKBiR):
            return (self.tblAmbCardKBiRActions, self.updateAmbCardKBiR, self.cmbAmbCardKBiRGroup,
                     self.getAmbCardFilter(
                        self.edtAmbCardKBiRBegDate,
                        self.edtAmbCardKBiREndDate,
                        self.cmbAmbCardKBiRGroup,
                        self.edtAmbCardKBiROffice,
                        self.cmbAmbCardKBiROrgStructure
                        ))
        elif index == self.tabAmbCardContent.indexOf(self.tabAmbCardDiagnostics):
            return (self.tblAmbCardDiagnostics, self.updateAmbCardDiagnostics, None,
                    {'begDate': self.edtAmbCardDiagnosticsBegDate.date(),
                    'endDate': self.edtAmbCardDiagnosticsEndDate.date(),
                    'eventPurposeId': self.cmbAmbCardDiagnosticsPurpose.value(),
                    'specialityId': self.cmbAmbCardDiagnosticsSpeciality.value(),
                    'personId': self.cmbAmbCardDiagnosticsPerson.value(),
                    'healthGroupId': self.cmbHealthGroup.value()}
                    )

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

#    @pyqtSignature('QModelIndex')
    def on_tblAmbCardKBiRActions_doubleClicked(self, index):
        self.ambCardTableDoubleClicked(self.tblAmbCardKBiRActions, self.cmbAmbCardKBiRGroup)

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
        self.tblAmbCardKBiRActions.setModel(None)
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
        del self.modelAmbCardKBiRActions

    def updateAmbCardDiagnostics(self, filter, posToId=None, fieldName=None):
        """
            В соответствии с фильтром обновляет список Diagnostics на вкладке AmbCard/Diagnostics.
        """
        if not self.currentClientId():
            self.tblAmbCardDiagnostics.setIdList([])
            return

        def ref(field, table, id_name):
            return u'(select {} from {} where id = Diagnostic.{})'.format(field, table, id_name)
        orderDict = {
            'person_id': ref(u'name', u'vrbPerson', u'person_id'),
            'speciality_id' : ref(u'name', u'rbSpeciality', u'speciality_id'),
            'endDate': 'endDate',
            'diagnosisType_id': ref(u'name', u'rbDiagnosisType', u'diagnosisType_id'),
            'healthGroup_id': ref(u'code', u'rbHealthGroup', u'healthGroup_id'),
            'MKB': ref(u'concat_ws("+",MKB,MKBEx)', u'Diagnosis', u'diagnosis_id'),
            'MKBEx': ref(u'concat_ws("+",MKB,MKBEx)', u'Diagnosis', u'diagnosis_id'),
            'character_id': ref(u'name', u'rbDiseaseCharacter', u'character_id'),
            'phase_id': ref(u'name', u'rbDiseasePhases', u'phase_id'),
            'stage_id': ref(u'name', u'rbDiseaseStage', u'stage_id'),
            'dispanser_id': ref(u'code', u'rbDispanser', u'dispanser_id'),
            'hospital': u'hospital',
            'traumaType_id': ref(u'code', u'rbTraumaType', u'traumaType_id'),
            'result_id': ref(u'name', u'rbDiagnosticResult', u'result_id'),
            'notes': u'notes',
            'freeInput': u'freeInput',
            'TNMS': ref(u'TNMS', u'Diagnosis', u'diagnosis_id'),
            'clinicalGroup': u'clinicalGroup',
            'exSubclassMKB': ref(u'exSubclassMKB', u'Diagnosis', u'diagnosis_id'),
            'toxicSubstances_id': ref(u'name', u'rbToxicSubstances', u'toxicSubstances_id'),
            }
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
        if self.tblAmbCardDiagnostics.order():
            orderBY = self.tblAmbCardDiagnostics.order().split(' ')
            orderBY = orderDict[fieldName] + ' ' + orderBY[1]
        try:
            QtGui.QApplication.setOverrideCursor(QtGui.QCursor(Qt.WaitCursor))
            idList = db.getIdList(queryTable,
                           tableDiagnostic['id'].name(),
                           cond, orderBY)
            self.tblAmbCardDiagnostics.setIdList(idList, posToId)
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

    def setKBirReadOnly(self, value):
        def setBlocked(widget, block):
            if block:
                if not hasattr(widget, '_inputBlocker'):
                    widget._savedFocusPolicy = widget.focusPolicy()
                    widget.setFocusPolicy(Qt.NoFocus)
                    blocker = CReadOnlyFilter(widget)
                    widget._inputBlocker = blocker
                    widget.installEventFilter(blocker)
            else:
                if hasattr(widget, '_inputBlocker'):
                    widget.removeEventFilter(widget._inputBlocker)
                    del widget._inputBlocker
                    if hasattr(widget, '_savedFocusPolicy'):
                        widget.setFocusPolicy(widget._savedFocusPolicy)
                        del widget._savedFocusPolicy
                        
        for i in range(self.tabAmbCardClient.count()):
            page = self.tabAmbCardClient.widget(i)
            setBlocked(page, value)
            for child in page.findChildren(QtGui.QWidget):
                setBlocked(child, value)


    def setLayoutVisible(self, layout, value):
        countWidget = layout.count()
        for i in range(0, countWidget):
            widget = layout.itemAt(i).widget()
            if widget:
                widget.setVisible(value)
                
    
    def setWidgetsVisible(self, value):
        self.edtAmbCardODGODSMText.setVisible(value)
        self.chkAmbCardNVNBIBRM2.setVisible(value)
        self.edtAmbCardNVNBIBRM4.setVisible(value)
        self.chkAmbCardNVNBIBRM6.setVisible(value)
        self.chkAmbCardNVNBIBRM7.setVisible(value)
        self.edtAmbCardNVNBIBRM7.setVisible(value)
        self.chkAmbCardNVNBIBRM8.setVisible(value)
        self.edtAmbCardPregravidarText.setVisible(value)
        self.frameAgeCryoAmbCard.setVisible(value)
        self.frameCryoAmbCard.setVisible(value)
        self.frameEmbryosAmbCard.setVisible(value)
        self.frameVRTAmbCard.setVisible(value)
        self.lblAmbCardFetusCount.setVisible(value)
        self.edtAmbCardFetusCount.setVisible(value)
        self.edtAmbCardODPOBGText.setVisible(value)
        self.lblAmbCardODPOBOLocalization.setVisible(value)
        self.lblAmbCardODPOBULULocalization.setVisible(value)
        self.edtAmbCardODPOBOLocalizationText.setVisible(value)
        self.edtAmbCardODPOBULULocalizationText.setVisible(value)
        self.edtAmbCardODPOBOPMG3Text.setVisible(value)
        self.edtAmbCardODPOBC3Text.setVisible(value)
        self.edtAmbCardODPOBTS2Text.setVisible(value)
        self.edtAmbCardODPOBAL2Text.setVisible(value)
        self.edtAmbCardODGOOSMZ2Text.setVisible(value)
        self.edtAmbCardODGONPO2Text.setVisible(value)
        self.edtAmbCardODGOV2Text.setVisible(value)
        self.edtAmbCardODGOTM4Text.setVisible(value)
        self.edtAmbCardODGOPSL2Text.setVisible(value)
        self.edtAmbCardODGOPSP3Text.setVisible(value)
        self.edtAmbCardODGOE2Text.setVisible(value)
        self.edtAmbCardSOPWPRText.setVisible(value)
        self.edtAmbCardSOPDBText.setVisible(value)
        self.edtAmbCardSOPSZText.setVisible(value)
        self.edtAmbCardSOPDSText.setVisible(value)
        self.edtAmbCardSOPTROText.setVisible(value)
        self.edtAmbCardSOPSZIText.setVisible(value)
        self.label_60AmbCard.setVisible(value)
        self.edtAmbCardSOPVSTATUSDate.setVisible(value)
        self.edtAmbCardSOPVSTATUSNumberText.setVisible(value)
        self.lblAmbCardSOPVSTATUS2.setVisible(value)
        self.lblAmbCardSOPVSTATUSARVTText.setVisible(value)
        self.edtAmbCardSOPVSTATUSARVTText.setVisible(value)
        self.edtAmbCardSOPNZText.setVisible(value)
        self.edtAmbCardSOPGTRDate.setVisible(value)
        self.edtAmbCardSOPGTRComponent.setVisible(value)
        self.lblAmbCardSOPGTRComponent.setVisible(value)
        self.label_67AmbCard.setVisible(value)
        self.chkAmbCardSOPWP3.setVisible(value)
        self.chkAmbCardSOPWP4.setVisible(value)
        self.chkAmbCardSOPWP5.setVisible(value)
        self.edtAmbCardSOPWPText.setVisible(value)
        self.label_70AmbCard.setVisible(value)
        self.chkAmbCardSOPWP8.setVisible(value)
        self.chkAmbCardSOPWP9.setVisible(value)
        self.chkAmbCardSOPWP10.setVisible(value)
        self.edtAmbCardSOPWPText11.setVisible(value)
        self.label_71AmbCard.setVisible(value)
        self.edtAmbCardSOPWP.setVisible(value)
        self.label_72AmbCard.setVisible(value)
        self.edtAmbCardSOPWPText12.setVisible(value)
        self.label_73AmbCard.setVisible(value)
        self.edtAmbCardSOPIPPPText.setVisible(value)
        self.edtAmbCardSOPSOPR1Date.setVisible(value)
        self.label_82AmbCard.setVisible(value)
        self.edtAmbCardSOPSOPR2Date.setVisible(value)
        self.label_83AmbCard.setVisible(value)
        self.edtAmbCardSOPSOPR3Date.setVisible(value)
        self.label_80AmbCard.setVisible(value)
        self.edtAmbCardSOPSOPR4Date.setVisible(value)
        self.label_79AmbCard.setVisible(value)
        self.edtAmbCardSOPSOPR5Date.setVisible(value)
        self.label_78AmbCard.setVisible(value)
        self.edtAmbCardSOPSOPR6Date.setVisible(value)
        self.label_81AmbCard.setVisible(value)
        self.edtAmbCardSOPSOPR7Date.setVisible(value)
        self.label_77AmbCard.setVisible(value)
        self.edtAmbCardSOPSOPR8Date.setVisible(value)
        self.label_75AmbCard.setVisible(value)
        self.edtAmbCardSOPSOPR9Date.setVisible(value)
        self.edtAmbCardSOPSOPR9Text.setVisible(value)
        self.label_76AmbCard.setVisible(value)
        self.edtAmbCardSOPPRWText.setVisible(value)
        self.edtAmbCardSOPOXZText.setVisible(value)
        self.edtAmbCardSOPOIPPPText.setVisible(value)
        self.edtAmbCardSOPOSZIText.setVisible(value)
        self.label_215AmbCard.setVisible(value)
        self.edtAmbCardSOPMNText.setVisible(value)
        self.label_94AmbCard.setVisible(value)
        self.edtAmbCardNVNBDG2Text.setVisible(value)
        self.lblAmbCardNVNBDGK.setVisible(value)
        self.chkAmbCardNVNBDGK1.setVisible(value)
        self.chkAmbCardNVNBDGK2.setVisible(value)
        self.lblAmbCardNVNBDGO.setVisible(value)
        self.edtAmbCardNVNBDGO.setVisible(value)
        self.frameAmbCard_30.setVisible(value)
        self.label_86AmbCard.setVisible(value)
        self.frame_31AmbCard.setVisible(value)
        self.frame_33AmbCard.setVisible(value)
        self.frame_34AmbCard.setVisible(value)
        self.frame_35AmbCard.setVisible(value)
        self.frame_36AmbCard.setVisible(value)
        self.frame_40AmbCard.setVisible(value)
        self.frame_41AmbCard.setVisible(value)
        self.frame_42AmbCard.setVisible(value)
        self.frame_43AmbCard.setVisible(value)
        self.setODPOBRPPGRFVisible(False)
        self.lblAmbCardNVNBPUDRP.setVisible(value)
        self.cmbAmbCardNVNBPUDRP.setVisible(value)
        self.lblAmbCardNVNBPUDSM.setVisible(value)
        self.cmbAmbCardNVNBPUDSM.setVisible(value)
        self.lblAmbCardNVNBPUDFTB.setVisible(value)
        self.cmbAmbCardNVNBPUDFTB.setVisible(value)
        self.lblAmbCardNVNBPUDSST.setVisible(value)
        self.cmbAmbCardNVNBPUDSST.setVisible(value)
        self.lblAmbCardNVNBPUDKOV.setVisible(value)
        self.cmbAmbCardNVNBPUDKOV.setVisible(value)
        self.lblAmbCardNVNBPUDCA.setVisible(value)
        self.cmbAmbCardNVNBPUDCA.setVisible(value)
        self.edtAmbCardSkinStatus.setVisible(value)
        
    
    def setODPOBRPPGRFVisible(self, value):
        self.lblAmbCardODPOBRPPGRF_1.setVisible(value)
        self.chkAmbCardODPOBRPPGRF1_1.setVisible(value)
        self.chkAmbCardODPOBRPPGRF2_1.setVisible(value)
        self.lblAmbCardODPOBRPPGRF_2.setVisible(value)
        self.chkAmbCardODPOBRPPGRF1_2.setVisible(value)
        self.chkAmbCardODPOBRPPGRF2_2.setVisible(value)
        self.lblAmbCardODPOBRPPGRF_3.setVisible(value)
        self.chkAmbCardODPOBRPPGRF1_3.setVisible(value)
        self.chkAmbCardODPOBRPPGRF2_3.setVisible(value)
        self.lblAmbCardODPOBRPPGRF_4.setVisible(value)
        self.chkAmbCardODPOBRPPGRF1_4.setVisible(value)
        self.chkAmbCardODPOBRPPGRF2_4.setVisible(value)
        self.lblAmbCardODPOBRPPGRF_5.setVisible(value)
        self.chkAmbCardODPOBRPPGRF1_5.setVisible(value)
        self.chkAmbCardODPOBRPPGRF2_5.setVisible(value)


    def clearODPOBRPPGRF(self):
        self.chkAmbCardODPOBRPPGRF1_1.setChecked(False)
        self.chkAmbCardODPOBRPPGRF2_1.setChecked(False)
        self.chkAmbCardODPOBRPPGRF1_2.setChecked(False)
        self.chkAmbCardODPOBRPPGRF2_2.setChecked(False)
        self.chkAmbCardODPOBRPPGRF1_3.setChecked(False)
        self.chkAmbCardODPOBRPPGRF2_3.setChecked(False)
        self.chkAmbCardODPOBRPPGRF1_4.setChecked(False)
        self.chkAmbCardODPOBRPPGRF2_4.setChecked(False)
        self.chkAmbCardODPOBRPPGRF1_5.setChecked(False)
        self.chkAmbCardODPOBRPPGRF2_5.setChecked(False)

    
    def setComoboBoxWheel(self, value=False):
        self.cmbAmbCardPrevOrganisation.setWheel(value)
        self.cmbAmbCardBloodGroupFather.setWheel(value)
        self.cmbAmbCardNVNBPNVNBMOdR.setWheel(value)
        self.cmbAmbCardNVNBPNVNBUAS.setWheel(value)
    
    
    def setReferenceComboBoxes(self):
        db = QtGui.qApp.db
        refComboBoxes = self.getReferenceComboBoxes()
        for cmb, code in refComboBoxes.items():
            obj = None
            tableAPT = db.table('ActionPropertyType')
            record = db.getRecordEx(tableAPT, u'valueDomain', [tableAPT[u'shortName'].eq(code), tableAPT['actionType_id'].inlist(self.actionTypeIdListByKBiR)])
            if record:
                domain = forceString(record.value(0))
                if domain:
                    obj = json.loads(domain, object_pairs_hook=OrderedDict)
                    dTableName = obj.get(u'table', u'').strip()
                    if dTableName.replace('`','').startswith('v1') or dTableName.replace('`','').startswith('1'):
                        tableName = unicode(db.db.databaseName()) + "." + dTableName
                    else:
                        tableName = dTableName
                    fields = obj.get(u'fields', {})
                    where = obj.get(u'where', [])
                    parentCol = obj.get(u'parent', None)
                    childCol = obj.get(u'child', None)
                    orderCol = obj.get(u'order', None)
                    ok, cond = CActionPropertyValueType._checkAndNormalizeCodeObj(where)
                    if parentCol and childCol and fields:
                        cmb.setTable(tableName, 
                                fields=fields, 
                                order=','.join(fields),
                                parentCol = parentCol, 
                                childCol = childCol,
                                orderCol = orderCol,
                                filter=QtGui.qApp.db.joinAnd(cond),
                                rawTable = dTableName)
                    elif fields:
                        cmb.setTable(tableName, 
                                fields=','+','.join(fields.keys()), 
                                fieldNames=list(fields.values()), 
                                order=','.join(fields.keys()), 
                                filter=QtGui.qApp.db.joinAnd(cond),
                                rawTable = dTableName)
        
        
    def setInitDate(self):
        self.edtAmbCardBegDateMaternityLeave.setDate(QDate())
        self.edtAmbCardEndDateMaternityLeave.setDate(QDate())
        self.edtAmbCardGenericCertificateDate.setDate(QDate())
        self.edtAmbCardBloodGroupFatherDate.setDate(QDate())
        self.edtAmbCardAntiresusIgPrevPregnBegDate.setDate(QDate())
        self.edtAmbCardAntiresusIgPrevPregnEndDate.setDate(QDate())
        self.edtAmbCardAntiresusIgCurrPregnBegDate.setDate(QDate())
        self.edtAmbCardAntiresusIgCurrPregnEndDate.setDate(QDate())
        self.edtAmbCardEstimatedBirthsDate.setDate(QDate())
        self.edtAmbCardExchangeAndNotificationCardClientDate.setDate(QDate())
        self.edtAmbCardVRTDate.setDate(QDate())
        self.edtAmbCardLastMenstruationDate.setDate(QDate())
        self.edtAmbCardFirstUSIDate.setDate(QDate())
        self.edtAmbCardFirstStirringFetusDate.setDate(QDate())
        self.edtAmbCardNVNBIBRM13Date.setDate(QDate())
        self.edtAmbCardNVNBIBRMResultDate.setDate(QDate())
        self.edtAmbCardNVNBDZKDate.setDate(QDate())
        self.edtAmbCardNVNBP.setDate(QDate())
        self.edtAmbCardNVNBDZ.setDate(QDate())
        self.edtAmbCardSOPVSTATUSDate.setDate(QDate())
        self.edtAmbCardSOPPFDate.setDate(QDate())
        self.edtAmbCardSOPOPFDate.setDate(QDate())
        self.edtAmbCardSOPSOPR1Date.setDate(QDate())
        self.edtAmbCardSOPSOPR2Date.setDate(QDate())
        self.edtAmbCardSOPSOPR3Date.setDate(QDate())
        self.edtAmbCardSOPSOPR4Date.setDate(QDate())
        self.edtAmbCardSOPSOPR5Date.setDate(QDate())
        self.edtAmbCardSOPSOPR6Date.setDate(QDate())
        self.edtAmbCardSOPSOPR7Date.setDate(QDate())
        self.edtAmbCardSOPSOPR8Date.setDate(QDate())
        self.edtAmbCardSOPSOPR9Date.setDate(QDate())
        self.edtAmbCardFirstAppearanceTermDate.setDate(QDate())
        self.edtAmbCardAppointDate.setDate(QDate())
        self.edtAmbCardODPOBDO.setDate(QDate())


    def setComboBoxes(self, actionTypeIdListByKBiR=[], actionTypeId=None):
        self.setPropertyDomainWidget(self.cmbAmbCardBloodGroupFather, u'ОД:ОДП:ГКО:1', isNotDefined = False, actionTypeIdListByKBiR=actionTypeIdListByKBiR, actionTypeId=actionTypeId)


    def setPropertyDomainWidget(self, widget, propertyShortName, isNotDefined = True, actionTypeIdListByKBiR=[], actionTypeId=None):
        widget._model.clear()
        domain, defaultValue = self.getPropertyDomain(propertyShortName, isNotDefined, actionTypeIdListByKBiR=actionTypeIdListByKBiR, actionTypeId=actionTypeId)
        widget.setDomain(domain, isUpdateCurrIndex=False)


    def getPropertyDomain(self, propertyShortName, isNotDefined = True, actionTypeIdListByKBiR=[], actionTypeId=None):
        domain = u'\'не определено\',' if isNotDefined else u''
        record, defaultValue = self.propertyDomain(propertyShortName, actionTypeIdListByKBiR, actionTypeId=actionTypeId)
        if record:
            domainR = QString(forceString(record))
            if u'*' in domainR:
                index = domainR.indexOf(u'*', 0, Qt.CaseInsensitive)
                if domainR[index - 1] != u',':
                    domainR.replace(QString('*'), QString(','))
                else:
                    domainR.remove(QChar('*'), Qt.CaseInsensitive)
            domain += domainR
            if u'[mc]' in domain:
                domain = domain.remove(QString(u'[mc]'), Qt.CaseInsensitive)
        return domain, defaultValue


    def propertyDomain(self, propertyShortName, actionTypeIdListByKBiR, actionTypeId=None):
        if not actionTypeIdListByKBiR:
            return None, None
        db = QtGui.qApp.db
        tableAPT = db.table('ActionPropertyType')
        tableActionType = db.table('ActionType')
        cond =[tableActionType['id'].inlist(actionTypeIdListByKBiR),
               #tableAPT['name'].like(propertyName),
               tableAPT['shortName'].like(propertyShortName),
               tableAPT['deleted'].eq(0)
               ]
        if actionTypeId:
            cond.append(tableAPT['actionType_id'].eq(actionTypeId))
        queryTable = tableActionType.innerJoin(tableAPT, tableActionType['id'].eq(tableAPT['actionType_id']))
        record = db.getRecordEx(queryTable, [tableAPT['valueDomain'], tableAPT['defaultValue']], cond)
        if record:
            return record.value(0), record.value(1)
        return None, None


    def setNVNBIBRPPRVisible(self):
        if self.edtAmbCardNVNBIBRP1.value() == 0:
            self.frame_31AmbCard.setVisible(False)
            self.frame_33AmbCard.setVisible(False)
            self.frame_34AmbCard.setVisible(False)
            self.frame_35AmbCard.setVisible(False)
            self.frame_36AmbCard.setVisible(False)
        elif self.edtAmbCardNVNBIBRP1.value() == 1:
            self.frame_31AmbCard.setVisible(True)
            self.frame_33AmbCard.setVisible(False)
            self.frame_34AmbCard.setVisible(False)
            self.frame_35AmbCard.setVisible(False)
            self.frame_36AmbCard.setVisible(False)
        elif self.edtAmbCardNVNBIBRP1.value() == 2:
            self.frame_31AmbCard.setVisible(True)
            self.frame_33AmbCard.setVisible(True)
            self.frame_34AmbCard.setVisible(False)
            self.frame_35AmbCard.setVisible(False)
            self.frame_36AmbCard.setVisible(False)
        elif self.edtAmbCardNVNBIBRP1.value() == 3:
            self.frame_31AmbCard.setVisible(True)
            self.frame_33AmbCard.setVisible(True)
            self.frame_34AmbCard.setVisible(True)
            self.frame_35AmbCard.setVisible(False)
            self.frame_36AmbCard.setVisible(False)
        elif self.edtAmbCardNVNBIBRP1.value() == 4:
            self.frame_31AmbCard.setVisible(True)
            self.frame_33AmbCard.setVisible(True)
            self.frame_34AmbCard.setVisible(True)
            self.frame_35AmbCard.setVisible(True)
            self.frame_36AmbCard.setVisible(False)
        elif self.edtAmbCardNVNBIBRP1.value() == 5:
            self.frame_31AmbCard.setVisible(True)
            self.frame_33AmbCard.setVisible(True)
            self.frame_34AmbCard.setVisible(True)
            self.frame_35AmbCard.setVisible(True)
            self.frame_36AmbCard.setVisible(True)



    def getShortNameTextEdit(self):
        return [u'ОД:ОДП:ОУК:1', u'ОД:СНБ:ПП:2', u'ОД:ПОБ:Ж:2', u'ОД:ПОБ:О:2', u'ОД:ПОБ:УЛУ:2',
        u'ОД:ПОБ:ОПМЖ:2', u'ОД:ПОБ:С:2', u'ОД:ПОБ:ТС:2', u'ОД:ГО:ОШМЗ:2', u'ОД:ГО:ВИ:НПО:2',
        u'ОД:ГО:ВИ:В:2', u'ОД:ГО:ВИ:ШМ:3', u'ОД:ГО:ВИ:ШМ:5', u'ОД:ГО:ВИ:ТМ:3', u'ОД:ГО:ВИ:ОП', u'ОД:ГО:ВИ:ПСл:2',
        u'ОД:ГО:ВИ:ПСп:2', u'ОД:ГО:ВИ:Э:2', u'ОД:ГО:ВИ:ОЦК', u'ОД:ГО:ВИ:ОБ', u'ОД:ГО:ВИ:Ан', u'ОД:ГО:ВИ:Наз', u'НВНБ:ДГ:2',
        u'НВНБ:ДГ:4', u'НВНБ:Пелв:10', u'НВНБ:ИБРМ:5', u'НВНБ:ИБРМ:9', u'НВНБ:ИБРП:1:6',
        u'НВНБ:ИБРП:1:10', u'СОП:ВПР:2', u'СОП:ДР:1', u'СОП:ПЗ:ДИ:2', u'СОП:ПЗ:НДУ:2', u'СОП:ПЗ:СЗ:2', u'СОП:ПЗ:СЗИ:2', u'СОП:ПЗ:ВИЧ:3',
        u'СОП:ПЗ:АТ', u'СОП:ПЗ:НЗ:2', u'СОП:ПЗ:ПФ:2', u'СОП:ВП:3', u'СОП:ВП:5', u'СОП:ВП:7', u'СОП:ПВ:2', u'СОП:Контрац',
        u'СОП:ГЗО', u'СОП:ИППП:2', u'СОП:ПЦИМШМ:3', u'СОП:ПИМЖ:3', u'СОП:СОР:ХЗ:2', u'СОП:СОР:ИППП:2', u'СОП:СОР:СЗП:2', u'СОП:СОР:ПФ:2']


    def setProperties(self, action):
        items = {}
        if action:
            shortNameTextEditList = self.getShortNameTextEdit()
            for property in action._propertiesById.itervalues():
                isShortNameTextEdit = False
                propertyType = property.type()
                shortName = trim(propertyType.shortName)
                value = property._value
                propertyValue = propertyType.convertQVariantToPyValue(value) if type(value) == QVariant else value
                for shortNameTextEdit in shortNameTextEditList:
                    if shortName == shortNameTextEdit:
                        isShortNameTextEdit = True
                        break
                if (isinstance(propertyValue, basestring) or type(propertyValue) == QString) and not isShortNameTextEdit:
                    propertyValue = trim(propertyValue)
                if propertyValue:
                    item = items.get(shortName, [])
                    if propertyValue and (isinstance(propertyValue, basestring) or type(propertyValue) == QString) and len(propertyValue) > 1 and not isShortNameTextEdit:
                        propertyValue = propertyValue.split(u',')
                        item.extend(propertyValue)
                    else:
                        item.append(propertyValue)
                    items[shortName] = item
            # #tabAmbCardBasicData
            # tabGeneralDataAboutPatient
            isMaritalStatus = self.getChkPropertyValue(items, u'ОД:ОДП:БС', [u'брак зарегистрирован',u'брак не зарегистрирован',u'одинокая'])
            self.chkAmbCardMaritalStatus1.setChecked(isMaritalStatus == 1)
            self.chkAmbCardMaritalStatus2.setChecked(isMaritalStatus == 2)
            self.chkAmbCardMaritalStatus3.setChecked(isMaritalStatus == 3)
            self.edtAmbCardBegDateMaternityLeave.setDate(self.getPropertyValue(items, u'ОД:ОДП:ДО:1', QDate))
            self.edtAmbCardEndDateMaternityLeave.setDate(self.getPropertyValue(items, u'ОД:ОДП:ДО:2', QDate))
            self.edtAmbCardGenericCertificateSeria.setText(self.getPropertyValue(items, u'ОД:ОДП:РС:1', QString))
            self.edtAmbCardGenericCertificateNumber.setText(self.getPropertyValue(items, u'ОД:ОДП:РС:2', QString))
            self.edtAmbCardGenericCertificateDate.setDate(self.getPropertyValue(items, u'ОД:ОДП:РС:3', QDate))
            self.cmbAmbCardBloodGroupFather.setValue(self.getPropertyValue(items, u'ОД:ОДП:ГКО:1', QString))
            self.edtAmbCardBloodGroupFatherDate.setDate(self.getPropertyValue(items, u'ОД:ОДП:ГКО:2', QDate))
            self.edtAmbCardAntiresusIgPrevPregnBegDate.setDate(self.getPropertyValue(items, u'ОД:ОДП:ДАР:ППБ:1', QDate))
            self.edtAmbCardAntiresusIgPrevPregnEndDate.setDate(self.getPropertyValue(items, u'ОД:ОДП:ДАР:ППБ:2', QDate))
            self.edtAmbCardAntiresusIgCurrPregnBegDate.setDate(self.getPropertyValue(items, u'ОД:ОДП:ДАР:ПТБ:1', QDate))
            self.edtAmbCardAntiresusIgCurrPregnEndDate.setDate(self.getPropertyValue(items, u'ОД:ОДП:ДАР:ПТБ:2', QDate))
            self.edtAmbCardPregnancyByAccount.setValue(self.getPropertyValue(items, u'ОД:ОДП:ДБпС', int))
            self.edtAmbCardBirthsByAccount.setValue(self.getPropertyValue(items, u'ОД:ОДП:ДРпС', int))
            self.edtAmbCardFirstAppearanceTerm.setValue(self.getPropertyValue(items, u'ОД:ОДП:СПЯ', int))
            self.edtAmbCardFirstAppearanceTermDays.setValue(self.getPropertyValue(items, u'ОД:ОДП:СПЯД', int))
            self.edtAmbCardFirstAppearanceTermDate.setDate(self.getPropertyValue(items, u'ОД:ОДП:ДПЯ', QDate))
            self.edtAmbCardAppointTermWeeks.setValue(self.getPropertyValue(items, u'ОД:ОДП:СПНУ:1', int))
            self.edtAmbCardAppointTermDays.setValue(self.getPropertyValue(items, u'ОД:ОДП:СПНУ:2', int))
            self.edtAmbCardAppointDate.setDate(self.getPropertyValue(items, u'ОД:ОДП:СПНУ:3', QDate))
            self.cmbAmbCardPrevOrganisation.setCurrentIndex(self.cmbAmbCardPrevOrganisation.findText(self.getPropertyValue(items, u'ОД:ОДП:ТУПНП', QComboBox) ))
            self.edtAmbCardEstimatedBirthsDate.setDate(self.getPropertyValue(items, u'ОД:ОДП:ПДР:1', QDate))
            self.edtAmbCardEstimatedTermDate.setValue(self.getPropertyValue(items, u'ОД:ОДП:ПДР:2', int))
            self.edtAmbCardExchangeAndNotificationCardNumber.setText(self.getPropertyValue(items, u'ОД:ОДП:ОУК:1', QString))
            self.edtAmbCardExchangeAndNotificationCardClientDate.setDate(self.getPropertyValue(items, u'ОД:ОДП:ОУК:2', QDate))
            isBeginPregnancy = self.getChkPropertyValue(items, u'ОД:СНБ:БН', [u'спонтанно',u'индуцирована',u'с помощью ВРТ'])
            self.chkAmbCardSpontaneously.setChecked(isBeginPregnancy == 1)
            self.chkAmbCardInduced.setChecked(isBeginPregnancy == 2)
            self.chkAmbCardWithHelpVRT.setChecked(isBeginPregnancy == 3)
            isPregravidar = self.getChkPropertyValue(items, u'ОД:СНБ:ПП:1', [u'нет',u'да'])
            self.chkAmbCardPregravidarNot.setChecked(isPregravidar == 1)
            self.chkAmbCardPregravidarYes.setChecked(isPregravidar == 2)
            self.edtAmbCardPregravidarText.setText(self.getPropertyValue(items, u'ОД:СНБ:ПП:2', QString))
            self.edtAmbCardVRTNumber.setValue(self.getPropertyValue(items, u'ОД:СНБ:ВРТ:1', int))
            self.edtAmbCardVRTDate.setDate(self.getPropertyValue(items, u'ОД:СНБ:ВРТ:2', QDate))
            isTransferFetus = self.getChkPropertyValue(items, u'ОД:СНБ:ВРТ:3', [u'нативного',u'криоконсервированного'])
            self.chkAmbCardVRTNative.setChecked(isTransferFetus == 1)
            self.chkAmbCardCryopreserved.setChecked(isTransferFetus == 2)
            self.edtAmbCardEmbryosCount.setValue(self.getPropertyValue(items, u'ОД:СНБ:ВРТ:4', int))
            self.edtAmbCardAgePatientCryopreservedDate.setValue(self.getPropertyValue(items, u'ОД:СНБ:ВРТ:5', int))
            isPregnancyType = self.getChkPropertyValue(items, u'ОД:СНБ:Б:1', [u'одноплодная',u'многоплодная'])
            self.chkAmbCardOneFetus.setChecked(isPregnancyType == 1)
            if self.chkAmbCardOneFetus.isChecked():
                self.frame_40AmbCard.setVisible(False)
                self.frame_41AmbCard.setVisible(False)
                self.frame_42AmbCard.setVisible(False)
                self.frame_43AmbCard.setVisible(False)
            self.chkAmbCardMultipleFetus.setChecked(isPregnancyType == 2)
            self.edtAmbCardFetusCount.setValue(self.getPropertyValue(items, u'ОД:СНБ:Б:2', int))
            if self.edtAmbCardFetusCount.value() == 0:
                self.frame_40AmbCard.setVisible(False)
                self.frame_41AmbCard.setVisible(False)
                self.frame_42AmbCard.setVisible(False)
                self.frame_43AmbCard.setVisible(False)
            elif self.edtAmbCardFetusCount.value() == 1:
                self.frame_40AmbCard.setVisible(False)
                self.frame_41AmbCard.setVisible(False)
                self.frame_42AmbCard.setVisible(False)
                self.frame_43AmbCard.setVisible(False)
            elif self.edtAmbCardFetusCount.value() == 2:
                self.frame_40AmbCard.setVisible(True)
                self.frame_41AmbCard.setVisible(False)
                self.frame_42AmbCard.setVisible(False)
                self.frame_43AmbCard.setVisible(False)
            elif self.edtAmbCardFetusCount.value() == 3:
                self.frame_40AmbCard.setVisible(True)
                self.frame_41AmbCard.setVisible(True)
                self.frame_42AmbCard.setVisible(False)
                self.frame_43AmbCard.setVisible(False)
            elif self.edtAmbCardFetusCount.value() == 4:
                self.frame_40AmbCard.setVisible(True)
                self.frame_41AmbCard.setVisible(True)
                self.frame_42AmbCard.setVisible(True)
                self.frame_43AmbCard.setVisible(False)
            elif self.edtAmbCardFetusCount.value() == 5:
                self.frame_40AmbCard.setVisible(True)
                self.frame_41AmbCard.setVisible(True)
                self.frame_42AmbCard.setVisible(True)
                self.frame_43AmbCard.setVisible(True)
            self.edtAmbCardLastMenstruationDate.setDate(self.getPropertyValue(items, u'ОД:СНБ:ПМ', QDate))
            self.edtAmbCardFirstUSIDate.setDate(self.getPropertyValue(items, u'ОД:СНБ:ДУЗИ', QDate))
            self.edtAmbCardFirstStirringFetusDate.setDate(self.getPropertyValue(items, u'ОД:СНБ:ПШП', QDate))
            # tabFirstExaminationPregnant
            self.edtAmbCardODPOBDO.setDate(self.getPropertyValue(items, u'ОД:ПОБ:ДО', QDate))
            isODPOBG = self.getChkPropertyValue(items, u'ОД:ПОБ:Ж:1', [u'нет',u'да'])
            self.chkAmbCardODPOBGNot.setChecked(isODPOBG == 1)
            self.chkAmbCardODPOBGYes.setChecked(isODPOBG == 2)
            self.edtAmbCardODPOBGText.setText(self.getPropertyValue(items, u'ОД:ПОБ:Ж:2', QString))
            isODPOBRVGK = self.getChkPropertyValue(items, u'ОД:ПОБ:РВЖК:1', [u'по женскому типу',u'по мужскому типу'])
            self.chkAmbCardODPOBRVGKWoman.setChecked(isODPOBRVGK == 1)
            self.chkAmbCardODPOBRVGKMen.setChecked(isODPOBRVGK == 2)
            isODPOBRVGK2 = self.getChkPropertyValue(items, u'ОД:ПОБ:РВЖК:2', [u'недостаточно выражена',u'нормально выражена',u'избыточно выражена'])
            self.chkAmbCardODPOBRVGKNotEnough.setChecked(isODPOBRVGK2 == 1)
            self.chkAmbCardODPOBRVGKNormal.setChecked(isODPOBRVGK2 == 2)
            self.chkAmbCardODPOBRVGKRedundant.setChecked(isODPOBRVGK2 == 3)
            isODPOBO = self.getChkPropertyValue(items, u'ОД:ПОБ:О:1', [u'нет',u'да'])
            self.chkAmbCardODPOBONot.setChecked(isODPOBO == 1)
            self.chkAmbCardODPOBOYes.setChecked(isODPOBO == 2)
            self.edtAmbCardODPOBOLocalizationText.setText(self.getPropertyValue(items, u'ОД:ПОБ:О:2', QString))
            isODPOBVRVNK = self.getChkPropertyValue(items, u'ОД:ПОБ:ВРВНК', [u'нет',u'да'])
            self.chkAmbCardODPOBVRVNKNot.setChecked(isODPOBVRVNK == 1)
            self.chkAmbCardODPOBVRVNKYes.setChecked(isODPOBVRVNK == 2)
            isODPOBULU = self.getChkPropertyValue(items, u'ОД:ПОБ:УЛУ:1', [u'нет',u'да'])
            self.chkAmbCardODPOBULUNot.setChecked(isODPOBULU == 1)
            self.chkAmbCardODPOBULUYes.setChecked(isODPOBULU == 2)
            self.edtAmbCardODPOBULULocalizationText.setText(self.getPropertyValue(items, u'ОД:ПОБ:УЛУ:2', QString))
            isODPOBOPMG = self.getChkPropertyValue(items, u'ОД:ПОБ:ОПМЖ:1', [u'патологических изменений нет',u'признаки фиброзно-кистозной мистопатии',u'пальпируется узловое образование'])
            self.chkAmbCardODPOBOPMG1.setChecked(isODPOBOPMG == 1)
            self.chkAmbCardODPOBOPMG2.setChecked(isODPOBOPMG == 2)
            self.chkAmbCardODPOBOPMG3.setChecked(isODPOBOPMG == 3)
            self.edtAmbCardODPOBOPMG3Text.setText(self.getPropertyValue(items, u'ОД:ПОБ:ОПМЖ:2', QString))
            isODPOBOPMG2 = self.getChkPropertyValue(items, u'ОД:ПОБ:ОПМЖ:3', [u'безболезненны',u'масталгия'])
            self.chkAmbCardODPOBOPMG4.setChecked(isODPOBOPMG2 == 1)
            self.chkAmbCardODPOBOPMG5.setChecked(isODPOBOPMG2 == 2)
            isODPOBC = self.getChkPropertyValue(items, u'ОД:ПОБ:С:1', [u'сформированы правильно',u'втянуты', u'другие изменения'])
            self.chkAmbCardODPOBC1.setChecked(isODPOBC == 1)
            self.chkAmbCardODPOBC2.setChecked(isODPOBC == 2)
            self.chkAmbCardODPOBC3.setChecked(isODPOBC == 3)
            self.edtAmbCardODPOBC3Text.setText(self.getPropertyValue(items, u'ОД:ПОБ:С:2', QString))
            isODPOBTS = self.getChkPropertyValue(items, u'ОД:ПОБ:ТС:1', [u'ясные',u'другие'])
            self.chkAmbCardODPOBTS1.setChecked(isODPOBTS == 1)
            self.chkAmbCardODPOBTS2.setChecked(isODPOBTS == 2)
            self.edtAmbCardODPOBTS2Text.setText(self.getPropertyValue(items, u'ОД:ПОБ:ТС:2', QString))
            self.edtAmbCardODPOBP.setValue(self.getPropertyValue(items, u'ОД:ПОБ:П', int))
            self.edtAmbCardODPOBADPR.setText(self.getPropertyValue(items, u'ОД:ПОБ:АД:1', QString))
            self.edtAmbCardODPOBADLR.setText(self.getPropertyValue(items, u'ОД:ПОБ:АД:2', QString))
            isODPOBAL = self.getChkPropertyValue(items, u'ОД:ПОБ:АЛ:1', [u'дыхание везикулярное', u'другое'])
            self.chkAmbCardODPOBAL1.setChecked(isODPOBAL == 1)
            self.chkAmbCardODPOBAL2.setChecked(isODPOBAL == 2)
            self.edtAmbCardODPOBAL2Text.setText(self.getPropertyValue(items, u'ОД:ПОБ:АЛ:2', QString))
            isODPOBSP = self.getChkPropertyValue(items, u'ОД:ПОБ:ШП16', [u'ощущает',u'не ощущает'])
            self.chkAmbCardODPOBSP1.setChecked(isODPOBSP == 1)
            self.chkAmbCardODPOBSP2.setChecked(isODPOBSP == 2)
            self.edtAmbCardODPOBSBP.setValue(self.getPropertyValue(items, u'ОД:ПОБ:СП12', int))
            self.edtAmbCardODPOBOG.setValue(self.getPropertyValue(items, u'ОД:ПОБ:ОЖ20', int))
            self.edtAmbCardODPOBVDM.setValue(self.getPropertyValue(items, u'ОД:ПОБ:ВДМ20', int))
            #Первый ребёнок
            self.cmbAmbCardODPOBPP1.setValue(self.getPropertyValue(items, u'ОД:ПОБ:ПП34:s', int))
            self.cmbAmbCardODPOBNVMTO_1.setValue(self.getPropertyValue(items, u'ОД:ПОБ:НВМТО34:1:s', int))
            self.cmbAmbCardODPOBCZVRP_1.setValue(self.getPropertyValue(items, u'ОД:ПОБ:СЗВРП:1:s', int))
            isODPOBGCH = self.getChkPropertyValue(items, u'ОД:ПОБ:ПЧ34', [u'прижата',u'подвижна'])
            self.chkAmbCardODPOBGCH1_1.setChecked(isODPOBGCH == 1)
            self.chkAmbCardODPOBGCH2_1.setChecked(isODPOBGCH == 2)
            isODPOBRPPGRF = self.getChkPropertyValue(items, u'ОД:ПОБ:РППГРФ:1', [u'обнаружен',u'не обнаружен'])
            self.chkAmbCardODPOBRPPGRF1_1.setChecked(isODPOBRPPGRF == 1)
            self.chkAmbCardODPOBRPPGRF2_1.setChecked(isODPOBRPPGRF == 2)

            #Второй ребёнок
            self.cmbAmbCardODPOBPP_2.setValue(self.getPropertyValue(items, u'ОД:ПОБ:ПП34:2:s', int))
            self.cmbAmbCardODPOBNVMTO_2.setValue(self.getPropertyValue(items, u'ОД:ПОБ:НВМТО34:2:s', int))
            self.cmbAmbCardODPOBCZVRP_2.setValue(self.getPropertyValue(items, u'ОД:ПОБ:СЗВРП:2:s', int))
            isODPOBGCH = self.getChkPropertyValue(items, u'ОД:ПОБ:ПЧ34:2', [u'прижата',u'подвижна'])
            self.chkAmbCardODPOBGCH1_2.setChecked(isODPOBGCH == 1)
            self.chkAmbCardODPOBGCH2_2.setChecked(isODPOBGCH == 2)
            isODPOBRPPGRF = self.getChkPropertyValue(items, u'ОД:ПОБ:РППГРФ:2', [u'обнаружен',u'не обнаружен'])
            self.chkAmbCardODPOBRPPGRF1_2.setChecked(isODPOBRPPGRF == 1)
            self.chkAmbCardODPOBRPPGRF2_2.setChecked(isODPOBRPPGRF == 2)

            #Третий ребёнок
            self.cmbAmbCardODPOBPP_3.setValue(self.getPropertyValue(items, u'ОД:ПОБ:ПП34:3:s', int))
            self.cmbAmbCardODPOBNVMTO_3.setValue(self.getPropertyValue(items, u'ОД:ПОБ:НВМТО34:3:s', int))
            self.cmbAmbCardODPOBCZVRP_3.setValue(self.getPropertyValue(items, u'ОД:ПОБ:СЗВРП:3:s', int))
            isODPOBGCH = self.getChkPropertyValue(items, u'ОД:ПОБ:ПЧ34:3', [u'прижата',u'подвижна'])
            self.chkAmbCardODPOBGCH1_3.setChecked(isODPOBGCH == 1)
            self.chkAmbCardODPOBGCH2_3.setChecked(isODPOBGCH == 2)
            isODPOBRPPGRF = self.getChkPropertyValue(items, u'ОД:ПОБ:РППГРФ:3', [u'обнаружен',u'не обнаружен'])
            self.chkAmbCardODPOBRPPGRF1_3.setChecked(isODPOBRPPGRF == 1)
            self.chkAmbCardODPOBRPPGRF2_3.setChecked(isODPOBRPPGRF == 2)

            #Четвёртый ребёнок
            self.cmbAmbCardODPOBPP_4.setValue(self.getPropertyValue(items, u'ОД:ПОБ:ПП34:4:s', int))
            self.cmbAmbCardODPOBNVMTO_4.setValue(self.getPropertyValue(items, u'ОД:ПОБ:НВМТО34:4:s', int))
            self.cmbAmbCardODPOBCZVRP_4.setValue(self.getPropertyValue(items, u'ОД:ПОБ:СЗВРП:4:s', int))
            isODPOBGCH = self.getChkPropertyValue(items, u'ОД:ПОБ:ПЧ34:4', [u'прижата',u'подвижна'])
            self.chkAmbCardODPOBGCH1_4.setChecked(isODPOBGCH == 1)
            self.chkAmbCardODPOBGCH2_4.setChecked(isODPOBGCH == 2)
            isODPOBRPPGRF = self.getChkPropertyValue(items, u'ОД:ПОБ:РППГРФ:4', [u'обнаружен',u'не обнаружен'])
            self.chkAmbCardODPOBRPPGRF1_4.setChecked(isODPOBRPPGRF == 1)
            self.chkAmbCardODPOBRPPGRF2_4.setChecked(isODPOBRPPGRF == 2)

            #Пятый ребёнок
            self.cmbAmbCardODPOBPP_5.setValue(self.getPropertyValue(items, u'ОД:ПОБ:ПП34:5:s', int))
            self.cmbAmbCardODPOBNVMTO_5.setValue(self.getPropertyValue(items, u'ОД:ПОБ:НВМТО34:5:s', int))
            self.cmbAmbCardODPOBCZVRP_5.setValue(self.getPropertyValue(items, u'ОД:ПОБ:СЗВРП:5:s', int))
            isODPOBGCH = self.getChkPropertyValue(items, u'ОД:ПОБ:ПЧ34:5', [u'прижата',u'подвижна'])
            self.chkAmbCardODPOBGCH1_5.setChecked(isODPOBGCH == 1)
            self.chkAmbCardODPOBGCH2_5.setChecked(isODPOBGCH == 2)
            isODPOBRPPGRF = self.getChkPropertyValue(items, u'ОД:ПОБ:РППГРФ:5', [u'обнаружен',u'не обнаружен'])
            self.chkAmbCardODPOBRPPGRF1_5.setChecked(isODPOBRPPGRF == 1)
            self.chkAmbCardODPOBRPPGRF2_5.setChecked(isODPOBRPPGRF == 2)

            # tabGynecologicalExamination
            isODGOOSMZ = self.getChkPropertyValue(items, u'ОД:ГО:ОШМЗ:1', [u'визуально не изменена', u'другое'])
            self.chkAmbCardODGOOSMZ1.setChecked(isODGOOSMZ == 1)
            self.chkAmbCardODGOOSMZ2.setChecked(isODGOOSMZ == 2)
            self.edtAmbCardODGOOSMZ2Text.setText(self.getPropertyValue(items, u'ОД:ГО:ОШМЗ:2', QString))
            isODGONPO = self.getChkPropertyValue(items, u'ОД:ГО:ВИ:НПО:1', [u'развиты правильно', u'указать отклонение'])
            self.chkAmbCardODGONPO1.setChecked(isODGONPO == 1)
            self.chkAmbCardODGONPO2.setChecked(isODGONPO == 2)
            self.edtAmbCardODGONPO2Text.setText(self.getPropertyValue(items, u'ОД:ГО:ВИ:НПО:2', QString))
            isODGOV = self.getChkPropertyValue(items, u'ОД:ГО:ВИ:В:1', [u'без патологии', u'указать отклонение'])
            self.chkAmbCardODGOV1.setChecked(isODGOV == 1)
            self.chkAmbCardODGOV2.setChecked(isODGOV == 2)
            self.edtAmbCardODGOV2Text.setText(self.getPropertyValue(items, u'ОД:ГО:ВИ:В:2', QString))
            isODGOSM = self.getChkPropertyValue(items, u'ОД:ГО:ВИ:ШМ:1', [u'плотная',u'размягчённая',u'мягкая',u'другое'])
            self.chkAmbCardODGOSM1.setChecked(isODGOSM == 1)
            self.chkAmbCardODGOSM2.setChecked(isODGOSM == 2)
            self.chkAmbCardODGOSM3.setChecked(isODGOSM == 3)
            self.chkAmbCardODGOSM4.setChecked(isODGOSM == 4)
            self.edtAmbCardODGODSM.setValue(self.getPropertyValue(items, u'ОД:ГО:ВИ:ШМ:2', int))
            self.edtAmbCardODGODSMText.setText(self.getPropertyValue(items, u'ОД:ГО:ВИ:ШМ:3', QString))
            isODGOSMO = self.getChkPropertyValue(items, u'ОД:ГО:ВИ:ШМ:4', [u'кзади',u'кпереди',u'расположена по центру'])
            self.chkAmbCardODGOSMO1.setChecked(isODGOSMO == 1)
            self.chkAmbCardODGOSMO2.setChecked(isODGOSMO == 2)
            self.chkAmbCardODGOSMO3.setChecked(isODGOSMO == 3)
            self.edtAmbCardODGOSL.setText(self.getPropertyValue(items, u'ОД:ГО:ВИ:ШМ:5', QString))
            isODGOZV = self.getChkPropertyValue(items, u'ОД:ГО:ВИ:НЗ', [u'сомкнут',u'пропускает кончик пальца',u'пропускает палец'])
            self.chkAmbCardODGOZV1.setChecked(isODGOZV == 1)
            self.chkAmbCardODGOZV2.setChecked(isODGOZV == 2)
            self.chkAmbCardODGOZV3.setChecked(isODGOZV == 3)
            isODGOTM = self.getChkPropertyValue(items, u'ОД:ГО:ВИ:ТМ:1', [u'безболезненное',u'болезненное'])
            self.chkAmbCardODGOTM1.setChecked(isODGOTM == 1)
            self.chkAmbCardODGOTM2.setChecked(isODGOTM == 2)
            isODGOTM2 = self.getChkPropertyValue(items, u'ОД:ГО:ВИ:ТМ:2', [u'подвижное', u'другое'])
            self.chkAmbCardODGOTM3.setChecked(isODGOTM2 == 1)
            self.chkAmbCardODGOTM4.setChecked(isODGOTM2 == 2)
            self.edtAmbCardODGOTM4Text.setText(self.getPropertyValue(items, u'ОД:ГО:ВИ:ТМ:3', QString))
            self.edtAmbCardODGOTMU.setText(self.getPropertyValue(items, u'ОД:ГО:ВИ:ТМ:4', QString))
            self.edtAmbCardODGOOMP.setText(self.getPropertyValue(items, u'ОД:ГО:ВИ:ОП', QString))
            isODGOPSL = self.getChkPropertyValue(items, u'ОД:ГО:ВИ:ПСл:1', [u'без особенностей',u'особенности'])
            self.chkAmbCardODGOPSL1.setChecked(isODGOPSL == 1)
            self.chkAmbCardODGOPSL2.setChecked(isODGOPSL == 2)
            self.edtAmbCardODGOPSL2Text.setText(self.getPropertyValue(items, u'ОД:ГО:ВИ:ПСл:2', QString))
            isODGOPSP = self.getChkPropertyValue(items, u'ОД:ГО:ВИ:ПСп:1', [u'без особенностей',u'особенности'])
            self.chkAmbCardODGOPSP1.setChecked(isODGOPSP == 1)
            self.chkAmbCardODGOPSP2.setChecked(isODGOPSP == 2)
            self.edtAmbCardODGOPSP3Text.setText(self.getPropertyValue(items, u'ОД:ГО:ВИ:ПСп:2', QString))
            isODGOE = self.getChkPropertyValue(items, u'ОД:ГО:ВИ:Э:1', [u'нет',u'обнаружены'])
            self.chkAmbCardODGOE1.setChecked(isODGOE == 1)
            self.chkAmbCardODGOE2.setChecked(isODGOE == 2)
            self.edtAmbCardODGOE2Text.setText(self.getPropertyValue(items, u'ОД:ГО:ВИ:Э:2', QString))
            self.edtAmbCardODGOOZK.setText(self.getPropertyValue(items, u'ОД:ГО:ВИ:ОЦК', QString))
            self.edtAmbCardODGOOV.setText(self.getPropertyValue(items, u'ОД:ГО:ВИ:ОБ', QString))
            self.edtAmbCardODGOA.setText(self.getPropertyValue(items, u'ОД:ГО:ВИ:Ан', QString))
            self.edtAmbCardODGON.setText(self.getPropertyValue(items, u'ОД:ГО:ВИ:Наз', QString))
            self.edtAmbCardODGOPSSP.setValue(self.getPropertyValue(items, u'ОД:ГО:ВИ:РССП', int))
            self.edtAmbCardODGODZ.setDate(self.getPropertyValue(items, u'ОД:ГО:ВИ:ДЗ', QDate))
            # #tabAmbCardClientData
            isSOPWPR = self.getChkPropertyValue(items, u'СОП:ВПР:1', [u'нет', u'да'])
            self.chkAmbCardSOPWPRNot.setChecked(isSOPWPR == 1)
            self.chkAmbCardSOPWPRYes.setChecked(isSOPWPR == 2)
            self.edtAmbCardSOPWPRText.setText(self.getPropertyValue(items, u'СОП:ВПР:2', QString))
            self.edtAmbCardSOPIMT.setValue(self.getPropertyValue(items, u'СОП:ИМТМ', int))
            self.edtAmbCardSOPRost.setValue(self.getPropertyValue(items, u'СОП:РПЯ', int))
            self.edtAmbCardSOPMT.setValue(self.getPropertyValue(items, u'СОП:МТПЯ', float))
            self.edtAmbCardSOPDRS.setText(self.getPropertyValue(items, u'СОП:ДР:1', QString))
            isSOPDRS = self.getChkPropertyValue(items, u'СОП:ДР:2', [u'низкий', u'высокий'])
            self.chkAmbCardSOPDRS1.setChecked(isSOPDRS == 1)
            self.chkAmbCardSOPDRS2.setChecked(isSOPDRS == 2)
            isSOPDB = self.getChkPropertyValue(items, u'СОП:ПЗ:ДИ:1', [u'нет', u'да'])
            self.chkAmbCardSOPDB1.setChecked(isSOPDB == 1)
            self.chkAmbCardSOPDB2.setChecked(isSOPDB == 2)
            self.edtAmbCardSOPDBText.setText(self.getPropertyValue(items, u'СОП:ПЗ:ДИ:2', QString))
            isSOPDS = self.getChkPropertyValue(items, u'СОП:ПЗ:НДУ:1', [u'не состояла', u'состояла'])
            self.chkAmbCardSOPDS1.setChecked(isSOPDS == 1)
            self.chkAmbCardSOPDS2.setChecked(isSOPDS == 2)
            self.edtAmbCardSOPDSText.setText(self.getPropertyValue(items, u'СОП:ПЗ:НДУ:2', QString))
            isSOPTRO = self.getChkPropertyValue(items, u'СОП:ПЗ:ТО:1', [u'нет', u'да'])
            self.chkAmbCardSOPTRO1.setChecked(isSOPTRO == 1)
            self.chkAmbCardSOPTRO2.setChecked(isSOPTRO == 2)
            self.edtAmbCardSOPTROText.setText(self.getPropertyValue(items, u'СОП:ПЗ:ТО:2', QString))
            isSOPSZ = self.getChkPropertyValue(items, u'СОП:ПЗ:СЗ:1', [u'нет', u'да'])
            self.chkAmbCardSOPSZ1.setChecked(isSOPSZ == 1)
            self.chkAmbCardSOPSZ2.setChecked(isSOPSZ == 2)
            self.edtAmbCardSOPSZText.setText(self.getPropertyValue(items, u'СОП:ПЗ:СЗ:2', QString))
            isSOPSZIList = self.getChkPropertyList(items, u'СОП:ПЗ:СЗИ:1', [u'нет',u'ВИЧ',u'Туберкулёз',u'Гепатит-В',u'Гепатит-С',u'Сифилис',u'другие'])
            self.chkAmbCardSOPSZI1.setChecked(False)
            self.chkAmbCardSOPSZI2.setChecked(False)
            self.chkAmbCardSOPSZI3.setChecked(False)
            self.chkAmbCardSOPSZI4.setChecked(False)
            self.chkAmbCardSOPSZI5.setChecked(False)
            self.chkAmbCardSOPSZI6.setChecked(False)
            self.chkAmbCardSOPSZI7.setChecked(False)
            for isSOPSZI in isSOPSZIList:
                if isSOPSZI == 1:
                    self.chkAmbCardSOPSZI1.setChecked(True)
                elif isSOPSZI == 2:
                    self.chkAmbCardSOPSZI2.setChecked(True)
                elif isSOPSZI == 3:
                    self.chkAmbCardSOPSZI3.setChecked(True)
                elif isSOPSZI == 4:
                    self.chkAmbCardSOPSZI4.setChecked(True)
                elif isSOPSZI == 5:
                    self.chkAmbCardSOPSZI5.setChecked(True)
                elif isSOPSZI == 6:
                    self.chkAmbCardSOPSZI6.setChecked(True)
                elif isSOPSZI == 7:
                    self.chkAmbCardSOPSZI7.setChecked(True)
            self.edtAmbCardSOPSZIText.setText(self.getPropertyValue(items, u'СОП:ПЗ:СЗИ:2', QString))
            isSOPVSTATUS = self.getChkPropertyValue(items, u'СОП:ПЗ:ВИЧ:1', [u'негативный',u'позитивный'])
            self.chkAmbCardSOPVSTATUS1.setChecked(isSOPVSTATUS == 1)
            self.chkAmbCardSOPVSTATUS2.setChecked(isSOPVSTATUS == 2)
            self.edtAmbCardSOPVSTATUSDate.setDate(self.getPropertyValue(items, u'СОП:ПЗ:ВИЧ:2', QDate))
            self.edtAmbCardSOPVSTATUSNumberText.setText(self.getPropertyValue(items, u'СОП:ПЗ:ВИЧ:3', QString))
            self.edtAmbCardSOPVSTATUSARVTText.setText(self.getPropertyValue(items, u'СОП:ПЗ:АТ', QString))
            isSOPNZ = self.getChkPropertyValue(items, u'СОП:ПЗ:НЗ:1', [u'нет', u'да'])
            self.chkAmbCardSOPNZ1.setChecked(isSOPNZ == 1)
            self.chkAmbCardSOPNZ2.setChecked(isSOPNZ == 2)
            self.edtAmbCardSOPNZText.setText(self.getPropertyValue(items, u'СОП:ПЗ:НЗ:2', QString))
            isSOPGTR = self.getChkPropertyValue(items, u'СОП:ПЗ:Г:1', [u'нет', u'да'])
            self.chkAmbCardSOPGTR1.setChecked(isSOPGTR == 1)
            self.chkAmbCardSOPGTR2.setChecked(isSOPGTR == 2)
            self.edtAmbCardSOPGTRDate.setText(self.getPropertyValue(items, u'СОП:ПЗ:Г:2', QString))
            self.edtAmbCardSOPGTRComponent.setText(self.getPropertyValue(items, u'СОП:ПЗ:Г:3', QString))
            self.edtAmbCardSOPPFDate.setDate(self.getPropertyValue(items, u'СОП:ПЗ:ПФ:1', QDate))
            self.edtAmbCardSOPPFText.setText(self.getPropertyValue(items, u'СОП:ПЗ:ПФ:2', QString))
            isSOPWPList = self.getChkPropertyList(items, u'СОП:ВП:1', [u'нет', u'курение', u'алкоголь', u'наркотики'])
            self.chkAmbCardSOPWP1.setChecked(False)
            self.chkAmbCardSOPWP2.setChecked(False)
            self.chkAmbCardSOPWP7.setChecked(False)
            self.chkAmbCardSOPWP11.setChecked(False)
            for isSOPWP in isSOPWPList:
                if isSOPWP == 1:
                    self.chkAmbCardSOPWP1.setChecked(True)
                elif isSOPWP == 2:
                    self.chkAmbCardSOPWP2.setChecked(True)
                elif isSOPWP == 3:
                    self.chkAmbCardSOPWP7.setChecked(True)
                elif isSOPWP == 4:
                    self.chkAmbCardSOPWP11.setChecked(True)
            isSOPWP2 = self.getChkPropertyValue(items, u'СОП:ВП:2', [u'-<1/2 пачки в день',u'1/2-1 пачка в день',u'>1 пачки в день'])
            self.chkAmbCardSOPWP3.setChecked(isSOPWP2 == 1)
            self.chkAmbCardSOPWP4.setChecked(isSOPWP2 == 2)
            self.chkAmbCardSOPWP5.setChecked(isSOPWP2 == 3)
            self.edtAmbCardSOPWPText.setText(self.getPropertyValue(items, u'СОП:ВП:3', QString))
            isSOPWP3 = self.getChkPropertyValue(items, u'СОП:ВП:4', [u'каждый день',u'1-2 раза в неделю',u'1-2 раза в месяц'])
            self.chkAmbCardSOPWP8.setChecked(isSOPWP3 == 1)
            self.chkAmbCardSOPWP9.setChecked(isSOPWP3 == 2)
            self.chkAmbCardSOPWP10.setChecked(isSOPWP3 == 3)
            self.edtAmbCardSOPWPText11.setText(self.getPropertyValue(items, u'СОП:ВП:5', QString))
            self.edtAmbCardSOPWP.setValue(self.getPropertyValue(items, u'СОП:ВП:6', int))
            self.edtAmbCardSOPWPText12.setText(self.getPropertyValue(items, u'СОП:ВП:7', QString))
            isSOPPRW = self.getChkPropertyValue(items, u'СОП:ПВ:1', [u'нет', u'да'])
            self.chkAmbCardSOPPRW1.setChecked(isSOPPRW == 1)
            self.chkAmbCardSOPPRW2.setChecked(isSOPPRW == 2)
            self.edtAmbCardSOPPRWText.setText(self.getPropertyValue(items, u'СОП:ПВ:2', QString))
            isSOPSOPRList = self.getChkPropertyList(items, u'СОП:СОПр:1', [u'столбняк', u'дифтерия', u'корь', u'краснуха', u'ветряная оспа', u'грипп', u'ВПЧ', u'гепатит-В', u'другие'])
            self.chkAmbCardSOPSOPR1.setChecked(False)
            self.chkAmbCardSOPSOPR2.setChecked(False)
            self.chkAmbCardSOPSOPR3.setChecked(False)
            self.chkAmbCardSOPSOPR4.setChecked(False)
            self.chkAmbCardSOPSOPR5.setChecked(False)
            self.chkAmbCardSOPSOPR6.setChecked(False)
            self.chkAmbCardSOPSOPR7.setChecked(False)
            self.chkAmbCardSOPSOPR8.setChecked(False)
            self.chkAmbCardSOPSOPR9.setChecked(False)
            for isSOPSOPR in isSOPSOPRList:
                if isSOPSOPR == 1:
                    self.chkAmbCardSOPSOPR1.setChecked(True)
                elif isSOPSOPR == 2:
                    self.chkAmbCardSOPSOPR2.setChecked(True)
                elif isSOPSOPR == 3:
                    self.chkAmbCardSOPSOPR3.setChecked(True)
                elif isSOPSOPR == 4:
                    self.chkAmbCardSOPSOPR4.setChecked(True)
                elif isSOPSOPR == 5:
                    self.chkAmbCardSOPSOPR5.setChecked(True)
                elif isSOPSOPR == 6:
                    self.chkAmbCardSOPSOPR6.setChecked(True)
                elif isSOPSOPR == 7:
                    self.chkAmbCardSOPSOPR7.setChecked(True)
                elif isSOPSOPR == 8:
                    self.chkAmbCardSOPSOPR8.setChecked(True)
                elif isSOPSOPR == 9:
                    self.chkAmbCardSOPSOPR9.setChecked(True)
            self.edtAmbCardSOPSOPR1Date.setDate(self.getPropertyValue(items, u'СОП:СОПр:2', QDate))
            self.edtAmbCardSOPSOPR2Date.setDate(self.getPropertyValue(items, u'СОП:СОПр:3', QDate))
            self.edtAmbCardSOPSOPR3Date.setDate(self.getPropertyValue(items, u'СОП:СОПр:4', QDate))
            self.edtAmbCardSOPSOPR4Date.setDate(self.getPropertyValue(items, u'СОП:СОПр:5', QDate))
            self.edtAmbCardSOPSOPR5Date.setDate(self.getPropertyValue(items, u'СОП:СОПр:6', QDate))
            self.edtAmbCardSOPSOPR6Date.setDate(self.getPropertyValue(items, u'СОП:СОПр:7', QDate))
            self.edtAmbCardSOPSOPR7Date.setDate(self.getPropertyValue(items, u'СОП:СОПр:8', QDate))
            self.edtAmbCardSOPSOPR8Date.setDate(self.getPropertyValue(items, u'СОП:СОПр:9', QDate))
            self.edtAmbCardSOPSOPR9Date.setDate(self.getPropertyValue(items, u'СОП:СОПр:11', QDate))
            self.edtAmbCardSOPSOPR9Text.setText(self.getPropertyValue(items, u'СОП:СОПр:10', QString))
            self.edtAmbCardSOPMN1.setValue(self.getPropertyValue(items, u'СОП:Менстр:1', int))
            isSOPMN = self.getChkPropertyValue(items, u'СОП:Менстр:2', [u'сразу;', u'нет'])
            self.chkAmbCardSOPMN1.setChecked(isSOPMN == 1)
            self.chkAmbCardSOPMN2.setChecked(isSOPMN == 2)
            self.edtAmbCardSOPMNText.setText(self.getPropertyValue(items, u'СОП:Менстр:3', QString))
            self.edtAmbCardSOPMN2.setValue(self.getPropertyValue(items, u'СОП:Менстр:5', int))
            self.edtAmbCardSOPMN3.setText(self.getPropertyValue(items, u'СОП:Менстр:6', QString))
            isSOPMN2 = self.getChkPropertyValue(items, u'СОП:Менстр:7', [u'скудные',u'умеренные',u'обильные'])
            self.chkAmbCardSOPMN3.setChecked(isSOPMN2 == 1)
            self.chkAmbCardSOPMN4.setChecked(isSOPMN2 == 2)
            self.chkAmbCardSOPMN5.setChecked(isSOPMN2 == 3)
            isSOPMN2 = self.getChkPropertyValue(items, u'СОП:Менстр:8', [u'болезненные',u'безболезненные'])
            self.chkAmbCardSOPMN6.setChecked(isSOPMN2 == 1)
            self.chkAmbCardSOPMN7.setChecked(isSOPMN2 == 2)
            isSOPMN2 = self.getChkPropertyValue(items, u'СОП:Менстр:9', [u'регулярные', u'нерегулярные'])
            self.chkAmbCardSOPMN8.setChecked(isSOPMN2 == 1)
            self.chkAmbCardSOPMN9.setChecked(isSOPMN2 == 2)
            self.edtAmbCardSOPPL.setValue(self.getPropertyValue(items, u'СОП:ПЖ', int))
            self.edtAmbCardSOPKRZPText.setText(self.getPropertyValue(items, u'СОП:Контрац', QString))
            self.edtAmbCardSOPGZOPText.setText(self.getPropertyValue(items, u'СОП:ГЗО', QString))
            isSOPIPPP = self.getChkPropertyValue(items, u'СОП:ИППП:1', [u'нет', u'да'])
            self.chkAmbCardSOPIPPP1.setChecked(isSOPIPPP == 1)
            self.chkAmbCardSOPIPPP2.setChecked(isSOPIPPP == 2)
            self.edtAmbCardSOPIPPPText.setText(self.getPropertyValue(items, u'СОП:ИППП:2', QString))
            self.edtAmbCardSOPPIMGDate.setText(self.getPropertyValue(items, u'СОП:ПИМЖ:1', QString))
            self.edtAmbCardSOPPIMGText1.setText(self.getPropertyValue(items, u'СОП:ПИМЖ:2', QString))
            self.edtAmbCardSOPPIMGText2.setText(self.getPropertyValue(items, u'СОП:ПИМЖ:3', QString))
            self.edtAmbCardSOPPZIMSMDate.setText(self.getPropertyValue(items, u'СОП:ПЦИМШМ:1', QString))
            self.edtAmbCardSOPPZIMSMText1.setText(self.getPropertyValue(items, u'СОП:ПЦИМШМ:2', QString))
            self.edtAmbCardSOPPZIMSMText2.setText(self.getPropertyValue(items, u'СОП:ПЦИМШМ:3', QString))
            self.edtAmbCardSOPSoORVZ.setValue(self.getPropertyValue(items, u'СОП:СОР:В', int))
            self.edtAmbCardSOPSoORIMT.setValue(self.getPropertyValue(items, u'СОП:СОР:ИМТ', int))
            self.edtAmbCardSOPSoORRost.setValue(self.getPropertyValue(items, u'СОП:СОР:Р', int))
            self.edtAmbCardSOPSoORMT.setValue(self.getPropertyValue(items, u'СОП:СОР:МТ', float))
            isSOPOVPList = self.getChkPropertyList(items, u'СОП:СОР:ВП', [u'нет',u'курение',u'алкоголь',u'наркотики'])
            self.chkAmbCardSOPOVP1.setChecked(False)
            self.chkAmbCardSOPOVP2.setChecked(False)
            self.chkAmbCardSOPOVP3.setChecked(False)
            self.chkAmbCardSOPOVP4.setChecked(False)
            for isSOPOVP in isSOPOVPList:
                if isSOPOVP == 1:
                    self.chkAmbCardSOPOVP1.setChecked(True)
                elif isSOPOVP == 2:
                    self.chkAmbCardSOPOVP2.setChecked(True)
                elif isSOPOVP == 3:
                    self.chkAmbCardSOPOVP3.setChecked(True)
                elif isSOPOVP == 4:
                    self.chkAmbCardSOPOVP4.setChecked(True)
            isSOPOXZ = self.getChkPropertyValue(items, u'СОП:СОР:ХЗ:1', [u'нет', u'да'])
            self.chkAmbCardSOPOXZ1.setChecked(isSOPOXZ == 1)
            self.chkAmbCardSOPOXZ2.setChecked(isSOPOXZ == 2)
            self.edtAmbCardSOPOXZText.setText(self.getPropertyValue(items, u'СОП:СОР:ХЗ:2', QString))
            isSOPOIPPP = self.getChkPropertyValue(items, u'СОП:СОР:ИППП:1', [u'нет', u'да'])
            self.chkAmbCardSOPOIPPP1.setChecked(isSOPOIPPP == 1)
            self.chkAmbCardSOPOIPPP2.setChecked(isSOPOIPPP == 2)
            self.edtAmbCardSOPOIPPPText.setText(self.getPropertyValue(items, u'СОП:СОР:ИППП:2', QString))
            isSOPOSZIList = self.getChkPropertyList(items, u'СОП:СОР:СЗП:1', [u'нет',u'ВИЧ',u'Туберкулёз',u'Гепатит-В',u'Гепатит-С',u'Сифилис',u'другие'])
            self.chkAmbCardSOPOSZI1.setChecked(False)
            self.chkAmbCardSOPOSZI2.setChecked(False)
            self.chkAmbCardSOPOSZI3.setChecked(False)
            self.chkAmbCardSOPOSZI4.setChecked(False)
            self.chkAmbCardSOPOSZI5.setChecked(False)
            self.chkAmbCardSOPOSZI6.setChecked(False)
            self.chkAmbCardSOPOSZI7.setChecked(False)
            for isSOPOSZI in isSOPOSZIList:
                if isSOPOSZI == 1:
                    self.chkAmbCardSOPOSZI1.setChecked(True)
                elif isSOPOSZI == 2:
                    self.chkAmbCardSOPOSZI2.setChecked(True)
                elif isSOPOSZI == 3:
                    self.chkAmbCardSOPOSZI3.setChecked(True)
                elif isSOPOSZI == 4:
                    self.chkAmbCardSOPOSZI4.setChecked(True)
                elif isSOPOSZI == 5:
                    self.chkAmbCardSOPOSZI5.setChecked(True)
                elif isSOPOSZI == 6:
                    self.chkAmbCardSOPOSZI6.setChecked(True)
                elif isSOPOSZI == 7:
                    self.chkAmbCardSOPOSZI7.setChecked(True)
            self.edtAmbCardSOPOSZIText.setText(self.getPropertyValue(items, u'СОП:СОР:СЗП:2', QString))
            self.edtAmbCardSOPOPFDate.setDate(self.getPropertyValue(items, u'СОП:СОР:ПФ:1', QDate))
            self.edtAmbCardSOPOPFText.setText(self.getPropertyValue(items, u'СОП:СОР:ПФ:2', QString))
            isSOPOSvOPRList = self.getChkPropertyList(items, u'СОП:СОР:СОПр', [u'столбняк',u'дифтерия',u'корь',u'краснуха',u'грипп'])
            self.chkAmbCardSOPOSvOPR1.setChecked(False)
            self.chkAmbCardSOPOSvOPR2.setChecked(False)
            self.chkAmbCardSOPOSvOPR3.setChecked(False)
            self.chkAmbCardSOPOSvOPR4.setChecked(False)
            self.chkAmbCardSOPOSvOPR5.setChecked(False)
            for isSOPOSvOPR in isSOPOSvOPRList:
                if isSOPOSvOPR == 1:
                    self.chkAmbCardSOPOSvOPR1.setChecked(True)
                elif isSOPOSvOPR == 2:
                    self.chkAmbCardSOPOSvOPR2.setChecked(True)
                elif isSOPOSvOPR == 3:
                    self.chkAmbCardSOPOSvOPR3.setChecked(True)
                elif isSOPOSvOPR == 4:
                    self.chkAmbCardSOPOSvOPR4.setChecked(True)
                elif isSOPOSvOPR == 5:
                    self.chkAmbCardSOPOSvOPR5.setChecked(True)
            # #tabAmbCardSurveillancePregnancy
            isNVNBDG = self.getChkPropertyValue(items, u'НВНБ:ДГ:1', [u'не показана', u'показана'])
            self.chkAmbCardNVNBDG1.setChecked(isNVNBDG == 1)
            self.chkAmbCardNVNBDG2.setChecked(isNVNBDG == 2)
            self.edtAmbCardNVNBDG2Text.setText(self.getPropertyValue(items, u'НВНБ:ДГ:2', QString))
            isNVNBDGK = self.getChkPropertyValue(items, u'НВНБ:ДГ:3', [u'в отделение патологии беременности', u'в отделение акушерского ухода'])
            self.chkAmbCardNVNBDGK1.setChecked(isNVNBDGK == 1)
            self.chkAmbCardNVNBDGK2.setChecked(isNVNBDGK == 2)
            self.edtAmbCardNVNBDGO.setText(self.getPropertyValue(items, u'НВНБ:ДГ:4', QString))
            self.edtAmbCardNVNBDZ.setDate(self.getPropertyValue(items, u'НВНБ:ДГ:5', QDate))
            self.edtAmbCardNVNBP1.setValue(self.getPropertyValue(items, u'НВНБ:Пелв:1', int))
            self.edtAmbCardNVNBP2.setValue(self.getPropertyValue(items, u'НВНБ:Пелв:2', int))
            self.edtAmbCardNVNBP3.setValue(self.getPropertyValue(items, u'НВНБ:Пелв:3', int))
            self.edtAmbCardNVNBP4.setValue(self.getPropertyValue(items, u'НВНБ:Пелв:4', int))
            self.edtAmbCardNVNBP5.setValue(self.getPropertyValue(items, u'НВНБ:Пелв:5', int))
            self.edtAmbCardNVNBP6.setValue(self.getPropertyValue(items, u'НВНБ:Пелв:6', int))
            self.edtAmbCardNVNBP7.setValue(self.getPropertyValue(items, u'НВНБ:Пелв:7', int))
            self.edtAmbCardNVNBP8.setValue(self.getPropertyValue(items, u'НВНБ:Пелв:8', int))
            self.edtAmbCardNVNBP9.setValue(self.getPropertyValue(items, u'НВНБ:Пелв:9', int))
            self.edtAmbCardNVNBPText.setText(self.getPropertyValue(items, u'НВНБ:Пелв:10', QString))
            self.edtAmbCardNVNBP.setDate(self.getPropertyValue(items, u'НВНБ:Пелв:11', QDate))
            self.chkAmbCardNVNBPTNPkVB12.setChecked(self.getPropertyValue(items, u'НВНБ:НПкВБ:12', QCheckBox))
            self.chkAmbCardNVNBPTNPkVB20.setChecked(self.getPropertyValue(items, u'НВНБ:НПкВБ:20', QCheckBox))
            isNVNBPNVNBPSR = self.getChkPropertyValue(items, u'НВНБ:ПСР', [u'вагинальные роды', u'кесарево сечение'])
            self.chkAmbCardNVNBPNVNBPSR1.setChecked(isNVNBPNVNBPSR == 1)
            self.chkAmbCardNVNBPNVNBPSR2.setChecked(isNVNBPNVNBPSR == 2)
            self.cmbAmbCardNVNBPNVNBUAS.setCurrentIndex(self.cmbAmbCardNVNBPNVNBUAS.findText(self.getPropertyValue(items, u'НВНБ:УАС', QComboBox) ))
            self.cmbAmbCardNVNBPNVNBMOdR.setValue(self.getPropertyValue(items, u'НВНБ:МОдР', forceRef))
            isNVNBPNVNBPrR = self.getChkPropertyValue(items, u'НВНБ:ПрР', [u'плановый', u'экстренный'])
            self.chkAmbCardNVNBPNVNBPrR1.setChecked(isNVNBPNVNBPrR == 1)
            self.chkAmbCardNVNBPNVNBPrR2.setChecked(isNVNBPNVNBPrR == 2)
            self.chkAmbCardNVNBPNVNBSUG.setChecked(self.getPropertyValue(items, u'НВНБ:СУЖ', QCheckBox))
            self.chkAmbCardNVNBPNVNBOoG.setChecked(self.getPropertyValue(items, u'НВНБ:ОоГ', QCheckBox))
            self.chkAmbCardNVNBPNVNBNPkT.setChecked(self.getPropertyValue(items, u'НВНБ:НПкТ', QCheckBox))
            self.cmbAmbCardNVNBPUDRP.setValue(self.getPropertyValue(items, u'НВНБ:УД:РП:s', int))
            self.cmbAmbCardNVNBPUDSM.setValue(self.getPropertyValue(items, u'НВНБ:УД:СМ:s', int))
            self.cmbAmbCardNVNBPUDSST.setValue(self.getPropertyValue(items, u'НВНБ:УД:ССТ', int))
            self.cmbAmbCardNVNBPUDFTB.setValue(self.getPropertyValue(items, u'НВНБ:УД:ФТБ:s', int))
            self.cmbAmbCardNVNBPUDKOV.setValue(self.getPropertyValue(items, u'НВНБ:УД:КОВ:s', int))
            self.cmbAmbCardNVNBPUDCA.setValue(self.getPropertyValue(items, u'НВНБ:УД:СА:s', int))
            self.cmbAmbCardNVNBIBRM.setValue(self.getPropertyValue(items, u'НВНБ:ИБРМ:1:s', int))
            isNVNBIBRM2 = self.getChkPropertyValue(items, u'НВНБ:ИБРМ:2', [u'Роды: самопроизвольные', u'оперативные'])
            self.chkAmbCardNVNBIBRM2.setChecked(isNVNBIBRM2 == 1)
            self.chkAmbCardNVNBIBRM6.setChecked(isNVNBIBRM2 == 2)
            isNVNBIBRM2 = self.getChkPropertyValue(items, u'НВНБ:ИБРМ:3', [u'без осложнений', u'с осложнениями'])
            self.chkAmbCardNVNBIBRM3.setChecked(isNVNBIBRM2 == 1)
            self.chkAmbCardNVNBIBRM4.setChecked(isNVNBIBRM2 == 2)
            self.edtAmbCardNVNBIBRM4.setText(self.getPropertyValue(items, u'НВНБ:ИБРМ:5', QString))
            isNVNBIBRM4 = self.getChkPropertyValue(items, u'НВНБ:ИБРМ:8', [u'кесарево сечение', u'другое'])
            self.chkAmbCardNVNBIBRM7.setChecked(isNVNBIBRM4 == 1)
            self.chkAmbCardNVNBIBRM8.setChecked(isNVNBIBRM4 == 2)
            self.edtAmbCardNVNBIBRM7.setText(self.getPropertyValue(items, u'НВНБ:ИБРМ:9', QString))
            self.edtAmbCardNVNBIBRM13Date.setDate(self.getPropertyValue(items, u'НВНБ:ИБРМ:15', QDate))
            self.edtAmbCardNVNBIBRM13Time.setTime(self.getPropertyValue(items, u'НВНБ:ИБРМ:15', QTime))
            self.edtAmbCardNVNBIBRM13MKB.setText(self.getPropertyValue(items, u'НВНБ:ИБРМ:16', QString))
            self.edtAmbCardNVNBIBRMResultDate.setDate(self.getPropertyValue(items, u'НВНБ:ИБРМ:17', QDate))
            self.edtAmbCardNVNBIBRMResultDateWeeks.setValue(self.getPropertyValue(items, u'НВНБ:ИБРМ:1:1', int))
            self.edtAmbCardNVNBIBRMResultDateDays.setValue(self.getPropertyValue(items, u'НВНБ:ИБРМ:1:2', int))
            self.edtAmbCardNVNBIBRM3.setText(self.getPropertyValue(items, u'НВНБ:ИБРМ:1:3', unicode))
            self.chkAmbCardNVNBIBRM13.setChecked(self.getPropertyValue(items, u'НВНБ:ИБРМ:15:1', QCheckBox))
            self.edtAmbCardNVNBIBRP1.setValue(self.getPropertyValue(items, u'НВНБ:ИБРП:КД', int))
            self.setNVNBIBRPPRVisible()
            # Первый ребёнок
            self.edtAmbCardODPOBSBP.setValue(self.getPropertyValue(items, u'ОД:ПОБ:СП12', int))
            self.cmbAmbCardNVNBIBRP1.setValue(self.getPropertyValue(items, u'НВНБ:ИБРП:1:1:1', int))
            isNVNBIBRPPRP = self.getChkPropertyValue(items, u'НВНБ:ИБРП:1:3', [u'Ж', u'М'])
            self.chkAmbCardNVNBIBRPPRP1.setChecked(isNVNBIBRPPRP == 1)
            self.chkAmbCardNVNBIBRPPRP2.setChecked(isNVNBIBRPPRP == 2)
            self.edtAmbCardNVNBIBRPPRP.setValue(self.getPropertyValue(items, u'НВНБ:ИБРП:1:4', float))
            self.edtAmbCardNVNBIBRPPRPD.setValue(self.getPropertyValue(items, u'НВНБ:ИБРП:1:5', int))
            isNVNBIBRPD = self.getChkPropertyValue(items, u'НВНБ:ИБРП:1:7', [u'доношенный', u'недоношенный', u'переношенный'])
            self.chkAmbCardNVNBIBRPD1.setChecked(isNVNBIBRPD == 1)
            self.chkAmbCardNVNBIBRPD2.setChecked(isNVNBIBRPD == 2)
            self.chkAmbCardNVNBIBRPD3.setChecked(isNVNBIBRPD == 3)
            self.edtAmbCardNVNBIBRPZMKB1.setText(self.getPropertyValue(items, u'НВНБ:ИБРП:1:8', QString))
            self.edtAmbCardNVNBIBRPZMKB2.setText(self.getPropertyValue(items, u'НВНБ:ИБРП:1:9', QString))
            self.edtAmbCardNVNBIBRPUV.setText(self.getPropertyValue(items, u'НВНБ:ИБРП:1:10', QString))
            self.edtAmbCardNVNBIBRPO1_1.setValue(self.getPropertyValue(items, u'НВНБ:ИБРП:1:6:1', int))
            self.edtAmbCardNVNBIBRPO5_1.setValue(self.getPropertyValue(items, u'НВНБ:ИБРП:1:6:2', int))
            # Второй ребёнок
            self.edtAmbCardODPOBSBP_2.setValue(self.getPropertyValue(items, u'ОД:ПОБ:СП12:2', int))
            self.cmbAmbCardNVNBIBRP2.setValue(self.getPropertyValue(items, u'НВНБ:ИБРП:2:1:1', int))
            isNVNBIBRPPRP = self.getChkPropertyValue(items, u'НВНБ:ИБРП:2:3', [u'Ж', u'М'])
            self.chkAmbCardNVNBIBRPPRP1_2.setChecked(isNVNBIBRPPRP == 1)
            self.chkAmbCardNVNBIBRPPRP2_2.setChecked(isNVNBIBRPPRP == 2)
            self.edtAmbCardNVNBIBRPPRP_2.setValue(self.getPropertyValue(items, u'НВНБ:ИБРП:2:4', float))
            self.edtAmbCardNVNBIBRPPRPD_2.setValue(self.getPropertyValue(items, u'НВНБ:ИБРП:2:5', int))
            isNVNBIBRPD = self.getChkPropertyValue(items, u'НВНБ:ИБРП:2:7', [u'доношенный', u'недоношенный', u'переношенный'])
            self.chkAmbCardNVNBIBRPD1_2.setChecked(isNVNBIBRPD == 1)
            self.chkAmbCardNVNBIBRPD2_2.setChecked(isNVNBIBRPD == 2)
            self.chkAmbCardNVNBIBRPD3_2.setChecked(isNVNBIBRPD == 3)
            self.edtAmbCardNVNBIBRPZMKB1_2.setText(self.getPropertyValue(items, u'НВНБ:ИБРП:2:8', QString))
            self.edtAmbCardNVNBIBRPZMKB2_2.setText(self.getPropertyValue(items, u'НВНБ:ИБРП:2:9', QString))
            self.edtAmbCardNVNBIBRPUV_2.setText(self.getPropertyValue(items, u'НВНБ:ИБРП:2:10', QString))
            self.edtAmbCardNVNBIBRPO1_2.setValue(self.getPropertyValue(items, u'НВНБ:ИБРП:2:6:1', int))
            self.edtAmbCardNVNBIBRPO5_2.setValue(self.getPropertyValue(items, u'НВНБ:ИБРП:2:6:2', int))
            # Третий ребёнок
            self.edtAmbCardODPOBSBP_3.setValue(self.getPropertyValue(items, u'ОД:ПОБ:СП12:3', int))
            self.cmbAmbCardNVNBIBRP3.setValue(self.getPropertyValue(items, u'НВНБ:ИБРП:3:1:1', int))
            isNVNBIBRPPRP = self.getChkPropertyValue(items, u'НВНБ:ИБРП:3:3', [u'Ж', u'М'])
            self.chkAmbCardNVNBIBRPPRP1_3.setChecked(isNVNBIBRPPRP == 1)
            self.chkAmbCardNVNBIBRPPRP2_3.setChecked(isNVNBIBRPPRP == 2)
            self.edtAmbCardNVNBIBRPPRP_3.setValue(self.getPropertyValue(items, u'НВНБ:ИБРП:3:4', float))
            self.edtAmbCardNVNBIBRPPRPD_3.setValue(self.getPropertyValue(items, u'НВНБ:ИБРП:3:5', int))
            isNVNBIBRPD = self.getChkPropertyValue(items, u'НВНБ:ИБРП:3:7', [u'доношенный', u'недоношенный', u'переношенный'])
            self.chkAmbCardNVNBIBRPD1_3.setChecked(isNVNBIBRPD == 1)
            self.chkAmbCardNVNBIBRPD2_3.setChecked(isNVNBIBRPD == 2)
            self.chkAmbCardNVNBIBRPD3_3.setChecked(isNVNBIBRPD == 3)
            self.edtAmbCardNVNBIBRPZMKB1_3.setText(self.getPropertyValue(items, u'НВНБ:ИБРП:3:8', QString))
            self.edtAmbCardNVNBIBRPZMKB2_3.setText(self.getPropertyValue(items, u'НВНБ:ИБРП:3:9', QString))
            self.edtAmbCardNVNBIBRPUV_3.setText(self.getPropertyValue(items, u'НВНБ:ИБРП:3:10', QString))
            self.edtAmbCardNVNBIBRPO1_3.setValue(self.getPropertyValue(items, u'НВНБ:ИБРП:3:6:1', int))
            self.edtAmbCardNVNBIBRPO5_3.setValue(self.getPropertyValue(items, u'НВНБ:ИБРП:3:6:2', int))
            # Четвёртый ребёнок
            self.edtAmbCardODPOBSBP_4.setValue(self.getPropertyValue(items, u'ОД:ПОБ:СП12:4', int))
            self.cmbAmbCardNVNBIBRP4.setValue(self.getPropertyValue(items, u'НВНБ:ИБРП:4:1:1', int))
            isNVNBIBRPPRP = self.getChkPropertyValue(items, u'НВНБ:ИБРП:4:3', [u'Ж', u'М'])
            self.chkAmbCardNVNBIBRPPRP1_4.setChecked(isNVNBIBRPPRP == 1)
            self.chkAmbCardNVNBIBRPPRP2_4.setChecked(isNVNBIBRPPRP == 2)
            self.edtAmbCardNVNBIBRPPRP_4.setValue(self.getPropertyValue(items, u'НВНБ:ИБРП:4:4', float))
            self.edtAmbCardNVNBIBRPPRPD_4.setValue(self.getPropertyValue(items, u'НВНБ:ИБРП:4:5', int))
            isNVNBIBRPD = self.getChkPropertyValue(items, u'НВНБ:ИБРП:4:7', [u'доношенный', u'недоношенный', u'переношенный'])
            self.chkAmbCardNVNBIBRPD1_4.setChecked(isNVNBIBRPD == 1)
            self.chkAmbCardNVNBIBRPD2_4.setChecked(isNVNBIBRPD == 2)
            self.chkAmbCardNVNBIBRPD3_4.setChecked(isNVNBIBRPD == 3)
            self.edtAmbCardNVNBIBRPZMKB1_4.setText(self.getPropertyValue(items, u'НВНБ:ИБРП:4:8', QString))
            self.edtAmbCardNVNBIBRPZMKB2_4.setText(self.getPropertyValue(items, u'НВНБ:ИБРП:4:9', QString))
            self.edtAmbCardNVNBIBRPUV_4.setText(self.getPropertyValue(items, u'НВНБ:ИБРП:4:10', QString))
            self.edtAmbCardNVNBIBRPO1_4.setValue(self.getPropertyValue(items, u'НВНБ:ИБРП:4:6:1', int))
            # Пятый ребёнок
            self.edtAmbCardODPOBSBP_5.setValue(self.getPropertyValue(items, u'ОД:ПОБ:СП12:5', int))
            self.cmbAmbCardNVNBIBRP5.setValue(self.getPropertyValue(items, u'НВНБ:ИБРП:5:1:1', int))
            isNVNBIBRPPRP = self.getChkPropertyValue(items, u'НВНБ:ИБРП:5:3', [u'Ж', u'М'])
            self.chkAmbCardNVNBIBRPPRP1_5.setChecked(isNVNBIBRPPRP == 1)
            self.chkAmbCardNVNBIBRPPRP2_5.setChecked(isNVNBIBRPPRP == 2)
            self.edtAmbCardNVNBIBRPPRP_5.setValue(self.getPropertyValue(items, u'НВНБ:ИБРП:5:4', float))
            self.edtAmbCardNVNBIBRPPRPD_5.setValue(self.getPropertyValue(items, u'НВНБ:ИБРП:5:5', int))
            isNVNBIBRPD = self.getChkPropertyValue(items, u'НВНБ:ИБРП:5:7', [u'доношенный', u'недоношенный', u'переношенный'])
            self.chkAmbCardNVNBIBRPD1_5.setChecked(isNVNBIBRPD == 1)
            self.chkAmbCardNVNBIBRPD2_5.setChecked(isNVNBIBRPD == 2)
            self.chkAmbCardNVNBIBRPD3_5.setChecked(isNVNBIBRPD == 3)
            self.edtAmbCardNVNBIBRPZMKB1_5.setText(self.getPropertyValue(items, u'НВНБ:ИБРП:5:8', QString))
            self.edtAmbCardNVNBIBRPZMKB2_5.setText(self.getPropertyValue(items, u'НВНБ:ИБРП:5:9', QString))
            self.edtAmbCardNVNBIBRPUV_5.setText(self.getPropertyValue(items, u'НВНБ:ИБРП:5:10', QString))
            self.edtAmbCardNVNBIBRPO1_5.setValue(self.getPropertyValue(items, u'НВНБ:ИБРП:5:6:1', int))
            #
            self.edtAmbCardNVNBIBRPOPS.setText(self.getPropertyValue(items, u'НВНБ:ИБРП:ОПС', QString))
            self.edtAmbCardClinicalDiagnosisMain.setText(self.getPropertyValue(items, u'ОД:КФД:1', QString))
            self.edtAmbCardClinicalDiagnosisAccomp.setText(self.getPropertyValue(items, u'ОД:КФД:2', QString))
            self.edtAmbCardClinicalDiagnosisComplications.setText(self.getPropertyValue(items, u'ОД:КФД:3', QString))
            self.edtAmbCardDiagnosis.setText(self.getPropertyValue(items, u'ОД:Д', QString))
            isSkinStatus = self.getChkPropertyValue(items, u'ОД:СКП:1', [u'чистые',u'высыпания'])
            self.chkAmbCardSkinStatus1.setChecked(isSkinStatus == 1)
            self.chkAmbCardSkinStatus2.setChecked(isSkinStatus == 2)
            self.edtAmbCardSkinStatus.setText(self.getPropertyValue(items, u'ОД:СКП:2', QString))


    def getChkPropertyValue(self, items, shortName, widgetType):
        value = 0
        widgetTypeList = [u'не задано']
        if widgetType:
            widgetTypeList.extend(widgetType)
        item = items.get(shortName, [])
        valueProperty = None
        if shortName == u'НВНБ:ИБРМ:2' and len(item) == 2:
            valueProperty = u','.join(item)
        else:
            if len(item) > 0:
                valueProperty = item[0]
        if valueProperty and valueProperty in widgetTypeList:
            value = widgetTypeList.index(valueProperty)
        return value if value >= 0 else 0


    def getChkPropertyList(self, items, shortName, widgetType):
        result = []
        widgetTypeList = [u'не задано']
        if widgetType:
            widgetTypeList.extend(widgetType)
        valuePropertyList = items.get(shortName, [])
        for valueProperty in valuePropertyList:
            value = 0
            if valueProperty and valueProperty in widgetTypeList:
                value = widgetTypeList.index(valueProperty)
                if value > 0:
                    result.append(value)
        return result


    def getPropertyValue(self, items, shortName, widgetType):
        if widgetType == unicode:
            widgetType = QString
        item = items.get(shortName, [])
        if widgetType == QString:
            return u','.join(val if (val and (isinstance(val, basestring) or type(val) == QString)) else str(val) for val in item if val)
        valueProperty = None
        if len(item) > 0:
            valueProperty = item[0]
        if widgetType == QTextEdit:
            return forceString(valueProperty)
        if widgetType == forceRef:
            return forceRef(valueProperty)
        if widgetType == QComboBox:
            return forceStringEx(valueProperty)
        if widgetType == QCheckBox:
            if valueProperty and (isinstance(valueProperty, basestring) or type(valueProperty) == QString):
                if valueProperty == u'Да' or valueProperty == u'да' or valueProperty in [u'true', u'True']:
                    return True
            elif type(valueProperty) is int and valueProperty > 0:
                return True
            elif type(valueProperty) is bool:
                return valueProperty
            return False
        if widgetType == u'year':
            if valueProperty and (isinstance(valueProperty, basestring) or type(valueProperty) == QString):
                return QDate().fromString(valueProperty,'dd.MM.yyyy')
            else:
                return forceDate(valueProperty)
        if widgetType == int:
            if valueProperty and (isinstance(valueProperty, basestring) or type(valueProperty) == QString):
                if (valueProperty == u'Да' or valueProperty == u'да' or valueProperty in [u'true', u'True']):
                    return 1
                else:
                    try:
                        return int(valueProperty) if valueProperty else 0
                    except (ValueError, TypeError):
                        return 0
            elif type(valueProperty) is bool:
                return int(valueProperty)
            return forceInt(valueProperty)
        if widgetType == QDate:
            if valueProperty and (isinstance(valueProperty, basestring) or type(valueProperty) == QString):
                return QDate().fromString(valueProperty,'dd.MM.yyyy')
            else:
                return forceDate(valueProperty)
        if widgetType == QDateTime:
            if valueProperty and (isinstance(valueProperty, basestring) or type(valueProperty) == QString):
                return QDateTime().fromString(valueProperty,'dd.MM.yyyy hh:mm')
            else:
                return forceDateTime(valueProperty)
        if widgetType == QTime:
            if valueProperty and (isinstance(valueProperty, basestring) or type(valueProperty) == QString):
                return QTime().fromString(valueProperty,'hh:mm')
            else:
                return forceTime(valueProperty)
        if widgetType == float:
            return forceDouble(QVariant(valueProperty))


    def setProperty(self, value, propertyShortName, action):
        if action:
            for propertyTypeName, propertyType in action.getType()._propertiesByName.items():
                if trim(propertyShortName) == trim(propertyType.shortName):
                    if propertyTypeName and propertyTypeName in action._actionType._propertiesByName:
                        value = propertyType.convertQVariantToPyValue(value)
                        if type(value) == unicode:
                            value = value.replace('\0', '')
                        action[propertyTypeName] = QVariant(value)
                        break


    def getProperty(self, propertyShortName, action):
        if action:
            actionType = action.getType()
            for name, propertyType in actionType._propertiesByName.items():
                if trim(propertyType.shortName) == trim(propertyShortName):
                    return toVariant(action[name])
        return QVariant()


    def updateAmbCardKBiRF111(self, actionId):
        self.modelAmbCardSOPSvORNM.setEventEditor(self)
        self.modelAmbCardNVNBVARRS.setEventEditor(self)
        self.modelAmbCardNVNBAR.setEventEditor(self)
        self.modelAmbCardNVNBSGVB.setEventEditor(self)
        self.setInitDate()
        self.setWidgetsVisible(False)
        record = None
        db = QtGui.qApp.db
        tableAction = db.table('Action')
        if actionId:
            record = db.getRecordEx(tableAction, '*', [tableAction['id'].eq(actionId), tableAction['deleted'].eq(0)])
        eventId = forceRef(record.value('event_id')) if record else None
        eventDate = None
        recordEvent = None
        if eventId:
            tableEvent = db.table('Event')
            recordEvent = db.getRecordEx(tableEvent, '*', [tableEvent['id'].eq(eventId), tableEvent['deleted'].eq(0)])
            if recordEvent:
                eventDate = forceDate(recordEvent.value('execDate'))
        self.edtAmbCardNVNBDZKDate.setDate(eventDate)
        isRhNegative = False
        clientId = forceRef(QtGui.qApp.db.translate('Event', 'id', eventId, 'client_id'))
        if clientId:
            tableClient = db.table('Client')
            tableRBBloodType = db.table('rbBloodType')
            table = tableClient.leftJoin(tableRBBloodType, tableRBBloodType['id'].eq(tableClient['bloodType_id']))
            recordClient = db.getRecordEx(table, [tableRBBloodType['name']], [tableClient['id'].eq(clientId), tableClient['deleted'].eq(0)])
        if recordClient:
            isRhNegative = u'Rh-' in forceStringEx(recordClient.value('name'))
            if not isRhNegative:
                self.clearODPOBRPPGRF()
            self.setODPOBRPPGRFVisible(isRhNegative)
        actionTypeIdListByKBiR = getActionTypeIdListByFlatCode(u'111/y-20')
        if not self.actionTypeIdListByKBiR:
            self.actionTypeIdListByKBiR = getActionTypeIdListByFlatCode(u'111/y-20')
        if record:
            action = CAction(record=record)
        elif self.actionTypeIdListByKBiR:
            action = CAction(actionType=CActionTypeCache.getById(self.actionTypeIdListByKBiR[0]))
        else:
            return
        actionType = action.getType()
        actionTypeId = actionType.id
        self.getDiagnosisMKB(clientId)
        self.setComboBoxes(self.actionTypeIdListByKBiR, actionTypeId)
        action.executionPlanManager.load()
        action.executionPlanManager.setCurrentItemIndex()
        self.setProperties(action)
        self.modelAmbCardSOPSvORNM.setAction(action)
        self.modelAmbCardSOPSvORNM.loadItems(clientId)
        self.modelAmbCardNVNBVARRS.setAction(action)
        self.modelAmbCardNVNBVARRS.loadItems(clientId)
        self.modelAmbCardNVNBAR.setAction(action)
        self.modelAmbCardNVNBAR.loadItems(clientId)
        self.modelAmbCardNVNBSGVB.setAction(action)
        self.modelAmbCardNVNBSGVB.loadItems(clientId)
        self.modelAmbCardPreviousPregnancy.loadItems(action.getId())
        conActionId = self.modelAmbCardPreviousPregnancy.getActionIdToRow(0)
        conItems = self.modelAmbCardPreviousPregnancy.items()
        if conItems and hasattr(conItems[0], 'aboutChildrenProperties'):
            self.modelAmbCardPreviousPregnancyChildren.setItems(conItems[0].aboutChildrenProperties.getItems())
        else:
            self.modelAmbCardPreviousPregnancyChildren.clearItems()
        self.updatePreviousPregnancyChildren(self.modelAmbCardPreviousPregnancy.index(0, 0), self.tblAmbCardPreviousPregnancyChildren, actionId=conActionId)


    def getDiagnosisMKB(self, clientId):
        dictDiagnosisMKB = {}
        if clientId:
            db = QtGui.qApp.db
            tableDiagnosis = db.table('Diagnosis')
            cols = [tableDiagnosis['id'],
                    tableDiagnosis['MKB'],
                    tableDiagnosis['endDate'],
                    u'''(Diagnosis.MKB IN ('O44', 'O44.0', 'O44.1')) AS isNVNBPUDRP''',
                    u'''(Diagnosis.MKB = 'H52.1') AS isNVNBPUDSM''',
                    u'''(Diagnosis.MKB IN ('O33', 'O33.1', 'O33.2', 'O33.3', 'O33.4')) AS isNVNBPUDSST''',
                    u'''(Diagnosis.MKB IN ('O33.0', 'O33.2', 'O33.3')) AS isNVNBPUDFTB''',
                    u'''(Diagnosis.MKB IN ('O40', 'O40.9', 'O41', 'O41.0')) AS isNVNBPUDKOV''',
                    u'''(Diagnosis.MKB IN ('D50', 'D50.0', 'D50.1', 'D50.8', 'D50.9')) AS isNVNBPUDCA'''
                    ]
            cond = [tableDiagnosis['client_id'].eq(clientId),
                         tableDiagnosis['deleted'].eq(0),
                         tableDiagnosis['MKB'].inlist([u'O44', u'O44.0', u'O44.1', u'H52.1', u'O33', u'O33.0', u'O33.1', u'O33.2', u'O33.3', u'O33.4',
                         u'O40', u'O40.9', u'O41', u'O41.0', u'D50', u'D50.0', u'D50.1', u'D50.8', u'D50.9']),
                        u'''EXISTS(SELECT NULL
                                          FROM Diagnostic
                                          WHERE Diagnostic.deleted = 0
                                           AND Diagnostic.diagnosis_id = Diagnosis.id)
                            OR
                                EXISTS(SELECT NULL
                                            FROM Diagnosis D
                                            JOIN Diagnostic ON Diagnostic.diagnosis_id = D.id
                                            WHERE Diagnostic.deleted = 0 AND D.deleted = 0 AND D.id = Diagnosis.mod_id)''',
                        ]
            cond.append(tableDiagnosis['mod_id'].isNull())
            records = db.getRecordList(tableDiagnosis, cols, cond, tableDiagnosis['endDate'].name() + ' DESC')
            for record in records:
                isNVNBPUDRP = forceBool(record.value('isNVNBPUDRP'))
                if isNVNBPUDRP:
                    dictDiagnosisMKB['isNVNBPUDRP'] = isNVNBPUDRP
                isNVNBPUDSM = forceBool(record.value('isNVNBPUDSM'))
                if isNVNBPUDSM:
                    dictDiagnosisMKB['isNVNBPUDSM'] = isNVNBPUDSM
                isNVNBPUDSST = forceBool(record.value('isNVNBPUDSST'))
                if isNVNBPUDSST:
                    dictDiagnosisMKB['isNVNBPUDSST'] = isNVNBPUDSST
                isNVNBPUDFTB = forceBool(record.value('isNVNBPUDFTB'))
                if isNVNBPUDFTB:
                    dictDiagnosisMKB['isNVNBPUDFTB'] = isNVNBPUDFTB
                isNVNBPUDKOV = forceBool(record.value('isNVNBPUDKOV'))
                if isNVNBPUDKOV:
                    dictDiagnosisMKB['isNVNBPUDKOV'] = isNVNBPUDKOV
                isNVNBPUDCA = forceBool(record.value('isNVNBPUDCA'))
                if isNVNBPUDCA:
                    dictDiagnosisMKB['isNVNBPUDCA'] = isNVNBPUDCA
        if dictDiagnosisMKB:
            self.frame_44AmbCard.setVisible(True)
            isNVNBPUDRP = (dictDiagnosisMKB.get('isNVNBPUDRP', False))
            self.lblAmbCardNVNBPUDRP.setVisible(isNVNBPUDRP)
            self.cmbAmbCardNVNBPUDRP.setVisible(isNVNBPUDRP)
            isNVNBPUDSM = (dictDiagnosisMKB.get('isNVNBPUDSM', False))
            self.lblAmbCardNVNBPUDSM.setVisible(isNVNBPUDSM)
            self.cmbAmbCardNVNBPUDSM.setVisible(isNVNBPUDSM)
            isNVNBPUDFTB = (dictDiagnosisMKB.get('isNVNBPUDFTB', False))
            self.lblAmbCardNVNBPUDFTB.setVisible(isNVNBPUDFTB)
            self.cmbAmbCardNVNBPUDFTB.setVisible(isNVNBPUDFTB)
            isNVNBPUDSST = (dictDiagnosisMKB.get('isNVNBPUDSST', False))
            self.lblAmbCardNVNBPUDSST.setVisible(isNVNBPUDSST)
            self.cmbAmbCardNVNBPUDSST.setVisible(isNVNBPUDSST)
            isNVNBPUDKOV = (dictDiagnosisMKB.get('isNVNBPUDKOV', False))
            self.lblAmbCardNVNBPUDKOV.setVisible(isNVNBPUDKOV)
            self.cmbAmbCardNVNBPUDKOV.setVisible(isNVNBPUDKOV)
            isNVNBPUDCA = (dictDiagnosisMKB.get('isNVNBPUDCA', False))
            self.lblAmbCardNVNBPUDCA.setVisible(isNVNBPUDCA)
            self.cmbAmbCardNVNBPUDCA.setVisible(isNVNBPUDCA)
        else:
            self.frame_44AmbCard.setVisible(False)


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
        filter = {'begDate': edtBegDate.date(),
                  'endDate': edtEndDate.date(),
                  'actionGroupId': cmbGroup.value(),
                  'office': forceString(edtOffice.text()),
                  'orgStructureId': cmbOrgStructure.value()}
        return filter

    #### AmbCard page: AttachFiles page ##############

    def updateAmbCardFiles(self, filter=None):
        """
            В соответствии с фильтром обновляет список Files на вкладке AmbCard/Files.
            Заполняет комбобоксы фильтров для таблиц Event и Action
        """
        self.modelAmbCardFiles.loadItems(self._clientId, filter)
        self.authorIdList = []
        self.signerIdList = []
        self.docDateList = []
        self.eventIdList = []
        self.externalIdList = []
        self.eventTypeIdList = []
        self.actionTypeGroupIdList = []
        self.actionTypeIdList = []
        self.existsWidgetDocs = {}
        self.docDateList = []
        authorIdList = []
        fileItems = self.modelAmbCardFiles.items
        if fileItems:
            self.tblAmbCardAttachedFiles.selectRow(0)
            fileAttachTableDict = {u'Client': 1,
                                   u'Event': 2,
                                   u'Action': 3,
                                   u'ProphylaxisPlanning': 4, }
            db = QtGui.qApp.db
            for item in fileItems:
                docTableName = forceString(item._record.value('objectTableName'))
                if docTableName == u'Event':
                    tableE = db.table(docTableName)
                    eventId = forceRef(item._record.value('master_id'))
                    self.eventIdList.append(eventId)
                    condE = [
                        tableE['id'].eq(eventId),
                        tableE['deleted'].eq(0),
                    ]
                    eventRecord = db.getRecordEx(tableE, 'eventType_id, externalId', condE)
                    eventTypeId = forceRef(eventRecord.value('eventType_id'))
                    externalId = forceString(eventRecord.value('externalId'))
                    if eventTypeId:
                        self.eventTypeIdList.append(str(eventTypeId))
                    if externalId:
                        self.externalIdList.append(externalId)
                elif docTableName == u'Action':
                    tableA = db.table(docTableName)
                    tableAT = db.table('ActionType')
                    actionId = forceRef(item._record.value('master_id'))
                    cols = [
                        tableA['actionType_id'],
                        tableAT['group_id'],
                    ]
                    query = tableA.leftJoin(tableAT, tableAT['id'].eq(tableA['actionType_id']))
                    actionRecord = db.getRecordEx(query, cols, [tableA['id'].eq(actionId)])
                    actionTypeId = forceRef(actionRecord.value('actionType_id'))
                    actionTypeGroupId = forceRef(actionRecord.value('group_id'))
                    if actionTypeId:
                        self.actionTypeIdList.append(str(actionTypeId))
                    if actionTypeGroupId:
                        self.actionTypeGroupIdList.append(str(actionTypeGroupId))
                if docTableName and not self.existsWidgetDocs.has_key(docTableName):
                    self.existsWidgetDocs[docTableName] = fileAttachTableDict[docTableName]
                itemSigner = item.respSignature
                if itemSigner:
                    signerId = itemSigner.signerId
                    if signerId:
                        self.signerIdList.append(signerId)

            authorIdList = sorted(list(set([item.authorId for item in fileItems if item.authorId])))
            self.docDateList = [item.lastModified for item in fileItems if item.lastModified and item.lastModified.isValid()]
        if self.existsWidgetDocs:
            model = self.cmbAmbCardFilesOwnerDoc.model()
            for k in range(model.rowCount()):
                if k == 0:
                    model.item(k).setEnabled(True)
                else:
                    if k not in self.existsWidgetDocs.values():
                        model.item(k).setEnabled(False)
                    else:
                        model.item(k).setEnabled(True)
        else:
            model = self.cmbAmbCardFilesOwnerDoc.model()
            for k in range(model.rowCount()):
                model.item(k).setEnabled(True if k == 0 else False)
        self.cmbAmbCardFilesEventId.clear()
        self.cmbAmbCardFilesEventId.addItem(u'не задано')
        if self.eventIdList:
            eventIdList = set(self.eventIdList)
            for eventId in list(eventIdList):
                self.cmbAmbCardFilesEventId.addItem(str(eventId))
        self.cmbAmbCardFilesExternalId.clear()
        self.cmbAmbCardFilesExternalId.addItem(u'не задано')
        if self.externalIdList:
            externalIdList = set(self.externalIdList)
            for externalId in list(externalIdList):
                self.cmbAmbCardFilesExternalId.addItem(str(externalId))
        if self.docDateList:
            self.edtAmbCardFilesBegDate.setDate(min(self.docDateList).date())
            self.edtAmbCardFilesEndDate.setDate(max(self.docDateList).date())
        else:
            self.edtAmbCardFilesBegDate.setDate(QDate.currentDate())
            self.edtAmbCardFilesEndDate.setDate(QDate.currentDate())
        if authorIdList:
            self.cmbAmbCardFilesAuthor.setFilter(u'id in (%s)' % u','.join([str(i) for i in authorIdList]))
            self.cmbAmbCardFilesAuthor.setCurrentIndex(0)
            self.cmbAmbCardFilesAuthor.setEnabled(True)
        else:
            self.cmbAmbCardFilesAuthor.setEnabled(False)
        if self.signerIdList:
            self.cmbAmbCardFilesSigner.setFilter(u'id in (%s)' % u','.join([str(i) for i in sorted(set(self.signerIdList))]))
            self.cmbAmbCardFilesSigner.setCurrentIndex(0)
            self.cmbAmbCardFilesSigner.setEnabled(True)
        else:
            self.cmbAmbCardFilesSigner.setEnabled(False)
        if self.eventTypeIdList:
            eventTypeIdList = set(self.eventTypeIdList)
            self.cmbAmbCardFilesEventType.setFilter(u'id in (%s)' % u','.join(list(eventTypeIdList)))
            self.cmbAmbCardFilesEventType.setValue(None)
        # if self.actionTypeGroupIdList:
        #     actionTypeGroupIdList = set(self.actionTypeGroupIdList)
        #     self.cmbAmbCardFilesActionTypeGroup.setFilter(u'id in (%s)' % u','.join(list(actionTypeGroupIdList)))
        #     self.cmbAmbCardFilesActionTypeGroup.setValue(None)
        if self.actionTypeIdList:
            actionTypeIdList = set(self.actionTypeIdList)
            self.cmbAmbCardFilesActionType.setFilter(u'id in (%s)' % u','.join(list(actionTypeIdList)))
            self.cmbAmbCardFilesActionType.setValue(None)

        # self.on_cmdAmbCardFilesButtonBox_reset()

    def on_cmdAmbCardFilesButtonBox_reset(self):
        self.on_chkAmbCardFilesDate_toggled(False)
        self.on_chkAmbCardFilesStartDate_toggled(False)
        if self.docDateList:
            self.edtAmbCardFilesBegDate.setDate(min(self.docDateList).date())
            self.edtAmbCardFilesEndDate.setDate(max(self.docDateList).date())
            self.edtAmbCardFilesBegSetDate.setDate(min(self.docDateList).date())
            self.edtAmbCardFilesEndSetDate.setDate(max(self.docDateList).date())
        else:
            self.edtAmbCardFilesBegDate.setDate(QDate.currentDate())
            self.edtAmbCardFilesEndDate.setDate(QDate.currentDate())
            self.edtAmbCardFilesBegSetDate.setDate(QDate.currentDate())
            self.edtAmbCardFilesEndSetDate.setDate(QDate.currentDate())

        self.cmbAmbCardFilesAuthor.setCode(0)
        self.cmbAmbCardFilesSigner.setCode(0)
        self.resetOwnerDocWidgets()
        self.edtAmbCardFilesFileName.clear()

    def resetOwnerDocWidgets(self):
        self.cmbAmbCardFilesOwnerDoc.setCurrentIndex(0)
        self.cmbAmbCardFilesEventType.setCurrentIndex(0)
        self.cmbAmbCardFilesEventId.setCurrentIndex(0)
        self.cmbAmbCardFilesExternalId.setCurrentIndex(0)
        self.cmbAmbCardFilesActionTypeClass.setCurrentIndex(0)
        # self.cmbAmbCardFilesActionTypeGroup.setCurrentIndex(0)
        self.cmbAmbCardFilesActionType.setCurrentIndex(0)
        self.cmbAmbCardFilesActionTypeServiceType.setCurrentIndex(0)
        widgets = [self.cmbAmbCardFilesEventType,
                   self.cmbAmbCardFilesEventId,
                   self.cmbAmbCardFilesExternalId,
                   self.cmbAmbCardFilesActionTypeClass,
                   self.cmbAmbCardFilesActionTypeServiceType,
                   # self.cmbAmbCardFilesActionTypeGroup,
                   self.cmbAmbCardFilesActionType]
        for widget in widgets:
            widget.setEnabled(True)

    def on_cmdAmbCardFilesButtonBox_clicked(self, button):
        buttonCode = self.cmdAmbCardFilesButtonBox.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Reset:
            self.on_cmdAmbCardFilesButtonBox_reset()
        self.on_cmdAmbCardFilesButtonBox_apply()

    def on_cmbAmbCardFilesOwnerDoc_currentIndexChanged(self, index):
        if index not in [0, 1, 2, 3, 4]:
            return
        if not self.modelAmbCardFiles.items:
            widgetEnabled = False
        else:
            widgetEnabled = False if index in (1, 4) else True
        if index in (1, 4):
            self.cmbAmbCardFilesEventType.setEnabled(widgetEnabled)
            self.cmbAmbCardFilesEventId.setEnabled(widgetEnabled)
            self.cmbAmbCardFilesExternalId.setEnabled(widgetEnabled)
            self.cmbAmbCardFilesActionTypeClass.setEnabled(widgetEnabled)
            # self.cmbAmbCardFilesActionTypeGroup.setEnabled(widgetEnabled)
            self.cmbAmbCardFilesActionType.setEnabled(widgetEnabled)
            self.cmbAmbCardFilesActionTypeServiceType.setEnabled(widgetEnabled)
        elif index == 2:
            self.cmbAmbCardFilesEventType.setEnabled(False if not self.eventTypeIdList else widgetEnabled)
            self.cmbAmbCardFilesEventId.setEnabled(False if not self.eventIdList else widgetEnabled)
            self.cmbAmbCardFilesExternalId.setEnabled(False if not self.externalIdList else widgetEnabled)
            self.cmbAmbCardFilesActionTypeClass.setEnabled(not widgetEnabled)
            # self.cmbAmbCardFilesActionTypeGroup.setEnabled(not widgetEnabled)
            self.cmbAmbCardFilesActionType.setEnabled(not widgetEnabled)
            self.cmbAmbCardFilesActionTypeServiceType.setEnabled(not widgetEnabled)
        elif index == 3:
            self.cmbAmbCardFilesEventType.setEnabled(not widgetEnabled)
            self.cmbAmbCardFilesEventId.setEnabled(not widgetEnabled)
            self.cmbAmbCardFilesExternalId.setEnabled(not widgetEnabled)
            widgetEnabled = True if index in self.existsWidgetDocs.values() else False
            self.cmbAmbCardFilesActionTypeClass.setEnabled(widgetEnabled)
            self.cmbAmbCardFilesActionTypeServiceType.setEnabled(widgetEnabled)
            # self.cmbAmbCardFilesActionTypeGroup.setEnabled(False if not self.actionTypeGroupIdList else widgetEnabled)
            self.cmbAmbCardFilesActionType.setEnabled(False if not self.actionTypeIdList else widgetEnabled)
        else:
            self.cmbAmbCardFilesEventType.setEnabled(False if not self.eventTypeIdList else widgetEnabled)
            self.cmbAmbCardFilesEventId.setEnabled(False if not self.eventIdList else widgetEnabled)
            self.cmbAmbCardFilesExternalId.setEnabled(False if not self.externalIdList else widgetEnabled)
            widgetEnabled = True if 3 in self.existsWidgetDocs.values() else False
            self.cmbAmbCardFilesActionTypeClass.setEnabled(widgetEnabled)
            self.cmbAmbCardFilesActionTypeServiceType.setEnabled(widgetEnabled)
            # self.cmbAmbCardFilesActionTypeGroup.setEnabled(False if not self.actionTypeGroupIdList else widgetEnabled)
            self.cmbAmbCardFilesActionType.setEnabled(False if not self.actionTypeIdList else widgetEnabled)
            self.cmbAmbCardFilesEventType.setCurrentIndex(0)
            self.cmbAmbCardFilesEventId.setCurrentIndex(0)
            self.cmbAmbCardFilesExternalId.setCurrentIndex(0)
            self.cmbAmbCardFilesActionTypeClass.setCurrentIndex(0)
            # self.cmbAmbCardFilesActionTypeGroup.setCurrentIndex(0)
            self.cmbAmbCardFilesActionType.setCurrentIndex(0)
            self.cmbAmbCardFilesActionTypeServiceType.setCurrentIndex(0)

    def on_cmbAmbCardFilesEventId_currentIndexChanged(self, index):
        self.cmbAmbCardFilesExternalId.setEnabled(False if self.cmbAmbCardFilesEventId.currentIndex() != 0 else True)

    def on_cmbAmbCardFilesExternalId_currentIndexChanged(self, index):
        self.cmbAmbCardFilesEventId.setEnabled(False if self.cmbAmbCardFilesExternalId.currentIndex() != 0 else True)


    def on_cmdAmbCardFilesButtonBox_apply(self):
        filter = {}
        if self.chkAmbCardFilesDate.isChecked():
            filter['begDate'] = self.edtAmbCardFilesBegDate.date()
            filter['endDate'] = self.edtAmbCardFilesEndDate.date().addDays(1)
        if self.chkAmbCardFilesStartDate.isChecked():
            filter['begSetDate'] = self.edtAmbCardFilesBegSetDate.date()
            filter['endSetDate'] = self.edtAmbCardFilesEndSetDate.date().addDays(1)
        if self.cmbAmbCardFilesAuthor.value():
            filter['authorId'] = self.cmbAmbCardFilesAuthor.value()
        if self.cmbAmbCardFilesSigner.value():
            filter['signerId'] = self.cmbAmbCardFilesSigner.value()
        if self.edtAmbCardFilesFileName.text():
            filter['fileName'] = forceStringEx(self.edtAmbCardFilesFileName.text())
        indexACFOD = self.cmbAmbCardFilesOwnerDoc.currentIndex()
        if indexACFOD == 1:
            filter['docTableName'] = u'Client'
        elif indexACFOD == 2:
            filter['docTableName'] = u'Event'
            if self.cmbAmbCardFilesEventType.value():
                filter['eventType'] = self.cmbAmbCardFilesEventType.value()
            if self.cmbAmbCardFilesEventId.currentIndex() and self.cmbAmbCardFilesEventId.isEnabled():
                filter['eventId'] = forceInt(self.cmbAmbCardFilesEventId.currentText())
            if self.cmbAmbCardFilesExternalId.currentIndex() and self.cmbAmbCardFilesExternalId.isEnabled():
                filter['externalId'] = self.cmbAmbCardFilesExternalId.currentText()
        elif indexACFOD == 3:
            filter['docTableName'] = u'Action'
            if self.cmbAmbCardFilesActionTypeClass.currentIndex():
                filter['actionTypeClass'] = self.cmbAmbCardFilesActionTypeClass.currentIndex() - 1
            # if self.cmbAmbCardFilesActionTypeGroup.value():
            #     filter['actionTypeGroup'] = self.cmbAmbCardFilesActionTypeGroup.value()
            if self.cmbAmbCardFilesActionType.value():
                filter['actionType'] = self.cmbAmbCardFilesActionType.value()
            if self.cmbAmbCardFilesActionTypeServiceType.currentIndex():
                filter['serviceType'] = self.cmbAmbCardFilesActionTypeServiceType.currentIndex() - 1
        elif indexACFOD == 4:
            filter['docTableName'] = u'ProphylaxisPlanning'
        else:
            filter['docTableName'] = u'All'
            if self.cmbAmbCardFilesActionTypeClass.currentIndex():
                filter['actionTypeClass'] = self.cmbAmbCardFilesActionTypeClass.currentIndex() - 1
            # if self.cmbAmbCardFilesActionTypeGroup.value():
            #     filter['actionTypeGroup'] = self.cmbAmbCardFilesActionTypeGroup.value()
            if self.cmbAmbCardFilesActionType.value():
                filter['actionType'] = self.cmbAmbCardFilesActionType.value()
            if self.cmbAmbCardFilesActionTypeServiceType.currentIndex():
                filter['serviceType'] = self.cmbAmbCardFilesActionTypeServiceType.currentIndex() - 1
            if self.cmbAmbCardFilesEventType.value():
                filter['eventType'] = self.cmbAmbCardFilesEventType.value()
            if self.cmbAmbCardFilesEventId.currentIndex() > 0 and self.cmbAmbCardFilesEventId.isEnabled():
                filter['eventId'] = forceInt(self.cmbAmbCardFilesEventId.currentText())
            if self.cmbAmbCardFilesExternalId.currentIndex() and self.cmbAmbCardFilesExternalId.isEnabled():
                filter['externalId'] = forceString(self.cmbAmbCardFilesExternalId.currentText())
        self.modelAmbCardFiles.loadItems(self._clientId, filter)


    @pyqtSlot(int)
    def on_cmbAmbCardNVNBIBRM_currentIndexChanged(self, val):
        rootParent = forceString(self.cmbAmbCardNVNBIBRM.getRootTextForId(self.cmbAmbCardNVNBIBRM.value()))
        if u'рождение' in rootParent.lower():
            self.chkAmbCardNVNBIBRM2.setVisible(True)
            self.chkAmbCardNVNBIBRM6.setVisible(True)
        else:
            self.chkAmbCardNVNBIBRM2.setVisible(False)
            self.chkAmbCardNVNBIBRM6.setVisible(False)
            self.chkAmbCardNVNBIBRM7.setVisible(False)
            self.chkAmbCardNVNBIBRM8.setVisible(False)
            self.chkAmbCardNVNBIBRM2.setChecked(False)
            self.chkAmbCardNVNBIBRM6.setChecked(False)
            self.chkAmbCardNVNBIBRM7.setChecked(False)
            self.chkAmbCardNVNBIBRM8.setChecked(False)


    @pyqtSlot(bool)
    def on_chkAmbCardNVNBIBRM4_toggled(self, checked):
        isChecked = self.chkAmbCardNVNBIBRM4.isChecked()
        if isChecked:
            self.edtAmbCardNVNBIBRM4.setVisible(True)


    @pyqtSlot(bool)
    def on_chkAmbCardNVNBIBRM8_toggled(self, checked):
        isChecked = self.chkAmbCardNVNBIBRM8.isChecked()
        if isChecked:
            self.edtAmbCardNVNBIBRM7.setVisible(True)


    @pyqtSlot(bool)
    def on_chkAmbCardNVNBIBRM13_toggled(self, checked):
        self.frameAmbCard_30.setVisible(checked)
        self.setProperty(QVariant(self.chkAmbCardNVNBIBRM13.isChecked()), u'НВНБ:ИБРМ:15:1')


    def on_chkAmbCardFilesDate_toggled(self, checked):
        self.chkAmbCardFilesDate.setChecked(checked)
        self.edtAmbCardFilesBegDate.setEnabled(checked)
        self.edtAmbCardFilesEndDate.setEnabled(checked)
        if checked:
            self.edtAmbCardFilesBegDate.setFocus()
        else:
            if self.docDateList:
                self.edtAmbCardFilesBegDate.setDate(min(self.docDateList).date())
                self.edtAmbCardFilesEndDate.setDate(max(self.docDateList).date())
            else:
                self.edtAmbCardFilesBegDate.setDate(QDate.currentDate())
                self.edtAmbCardFilesEndDate.setDate(QDate.currentDate())

    def on_chkAmbCardFilesStartDate_toggled(self, checked):
        self.chkAmbCardFilesStartDate.setChecked(checked)
        self.edtAmbCardFilesBegSetDate.setEnabled(checked)
        self.edtAmbCardFilesEndSetDate.setEnabled(checked)
        if checked:
            self.edtAmbCardFilesBegSetDate.setFocus()
        else:
            if self.docDateList:
                self.edtAmbCardFilesBegSetDate.setDate(min(self.docDateList).date())
                self.edtAmbCardFilesEndSetDate.setDate(max(self.docDateList).date())
            else:
                self.edtAmbCardFilesBegSetDate.setDate(QDate.currentDate())
                self.edtAmbCardFilesEndSetDate.setDate(QDate.currentDate())

    def on_actGetFileObject_triggered(self):
        fileItem = self.tblAmbCardAttachedFiles.getCurrentFileItem()
        if fileItem:
            if not fileItem.isLost:
                from Registry.DialogGetObject import CDialogGetObject
                dialog = CDialogGetObject(self, self._ambCardFilesUserId, fileItem)
                try:
                    dialog.exec_()
                finally:
                    dialog.destroy()
                    del dialog

    def on_actAllFilesSelect_triggered(self):
        self.tblAmbCardAttachedFiles.selectAll()

    def selectAmbCardActions(self, filter, classCode, order, fieldName, isKBiR=False):
        return getClientActions(self.currentClientId(), filter, classCode, order, fieldName, isKBiR=isKBiR)

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

    def updateAmbCardKBiR(self, filter, posToId=None, fieldName=None):
        """
            в соответствии с фильтром обновляет список Actions на вкладке AmbCard/Cure.
        """
        self.__ambCardMiscFilter = filter
        order = self.tblAmbCardKBiRActions.order() if self.tblAmbCardKBiRActions.order() else ['Action.endDate DESC', 'id']
        self.tblAmbCardKBiRActions.setIdList(self.selectAmbCardActions(filter, None, order, fieldName, isKBiR=True), posToId)

    def focusAmbCardKBiRActions(self):
        self.tblAmbCardKBiRActions.setFocus(Qt.TabFocusReason)

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
        filter = {'begDate': self.edtAmbCardDiagnosticsBegDate.date(),
                  'endDate': self.edtAmbCardDiagnosticsEndDate.date(),
                  'eventPurposeId': self.cmbAmbCardDiagnosticsPurpose.value(),
                  'specialityId': self.cmbAmbCardDiagnosticsSpeciality.value(),
                  'personId': self.cmbAmbCardDiagnosticsPerson.value(),
                  'healthGroupId': self.cmbHealthGroup.value()}
        self.updateAmbCardDiagnostics(filter)
        self.focusAmbCardDiagnostics()

    # @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelAmbCardDiagnosticsSort_currentRowChanged(self, current, previous):
        self.updateAmbCardDiagnosticsInfo()

    # @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelAmbCardVisitsSort_currentRowChanged(self, current, previous):
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
        if index != self.tabAmbCardContent.indexOf(self.tabAmbCardMonitoring) and self.ambCardMonitoringIsInitialised:
            self.savePreferencesLoc()
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
            if self._clientId != self._ambCardFilesUserId:
                self.__ambCardFilesIsInitialised = False
                self._ambCardFilesUserId = self._clientId
            else:
                self.on_cmdAmbCardFilesButtonBox_apply()
                self.__ambCardFilesIsInitialised = True
            if not self.__ambCardFilesIsInitialised:
                self.updateAmbCardFiles({'docTableName': u'All'})
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
        filter = {'clientId': self.currentClientId()}
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
                      None,
                      self.tblAmbCardSurveyActions,
                      None,
                      self.tblAmbCardKBiRActions
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
                      None,
                      self.tblAmbCardSurveyActions,
                      self.tblAmbCardKBiRActions
                    ][index-1]
            if table:
                actionId = table.currentItemId()
                if actionId:
                    from Events.EditDispatcher import getEventFormClass
                    from F088.F088EditDialog import CF088EditDialog
                    
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
                    if getEventFormClass(eventId) == CF088EditDialog:
                        data.update(self.get0882022InfoContext(context, eventId, actionId, table.currentItem()))
                    if table == self.tblAmbCardKBiRActions:
                        actionItems = self.modelAmbCardPreviousPregnancy.items()
                        aboutPreviousPregnancyAction = CLocActionPropertyActionsInfoList(context, actionItems)
                        data['aboutPreviousPregnancyAction'] = aboutPreviousPregnancyAction
                    QtGui.qApp.call(self, applyTemplate, (self, templateId, data))


    def get0882022InfoContext(self, context, eventId, actionId, actionRecord):
        from Events.EventInfo import CDiagnosticInfo, CCookedEventInfo
        from Events.ActionInfo import CCookedActionInfo, CLocActionPropertyActionsInfoList, \
            CLocActionPropertyMedicamentInfoList
        from Events.ActionsModel import CActionRecordItem
        from F088.F0882022EditDialog import CAboutMedicalExaminationsRequiredPropertiesRegistry

        eventByRecord = CCookedEventInfo(context, eventId,
                                         QtGui.qApp.db.getRecordEx('Event', '*', 'id=%d' % eventId))

        tableDiagnostic = QtGui.qApp.db.table('Diagnostic')
        tableDiagnosisType = QtGui.qApp.db.table('rbDiagnosisType')
        table = tableDiagnostic.innerJoin(tableDiagnosisType, [
            tableDiagnosisType['id'].eq(tableDiagnostic['diagnosisType_id'])])
        cond = [
            tableDiagnostic['event_id'].eq(eventId),
            tableDiagnostic['deleted'].eq(0)
        ]
        diagnosis_31_1 = []
        for diagId in QtGui.qApp.db.getDistinctIdList(table, tableDiagnostic['id'],
                                                      cond + [tableDiagnosisType['code'].eq('51')]):
            diag = CDiagnosticInfo(context, forceRef(diagId))
            diagnosis_31_1.append(diag)
        diagnosis_31_3 = []
        for diagId in QtGui.qApp.db.getDistinctIdList(table, tableDiagnostic['id'],
                                                      cond + [tableDiagnosisType['code'].eq('52')]):
            diag = CDiagnosticInfo(context, forceRef(diagId))
            diagnosis_31_3.append(diag)
        diagnosis_31_4 = []
        for diagId in QtGui.qApp.db.getDistinctIdList(table, tableDiagnostic['id'],
                                                      cond + [tableDiagnosisType['code'].eq('53')]):
            diag = CDiagnosticInfo(context, forceRef(diagId))
            diagnosis_31_4.append(diag)
        diagnosis_31_6 = []
        for diagId in QtGui.qApp.db.getDistinctIdList(table, tableDiagnostic['id'],
                                                      cond + [tableDiagnosisType['code'].eq('54')]):
            diag = CDiagnosticInfo(context, forceRef(diagId))
            diagnosis_31_6.append(diag)

        table = QtGui.qApp.db.table('Action_ActionProperty')
        actionItems = QtGui.qApp.db.getDistinctRecordList(table, '*', [table['master_id'].eq(actionId),
                                                                       table['actionProperty_id'].isNotNull(),
                                                                       table['deleted'].eq(0)])
        for item in actionItems:
            item.aboutMERProperties = CAboutMedicalExaminationsRequiredPropertiesRegistry()
            item.aboutMERProperties.load(forceRef(item.value('master_id')), forceRef(item.value('action_id')))

        aboutMedicalExaminationsRequiredAction = CLocActionPropertyActionsInfoList(context, actionItems)
        table = QtGui.qApp.db.table('Action_ESKLP_Smnn')
        medicamentItems = QtGui.qApp.db.getDistinctRecordList(table, '*', [table['master_id'].eq(actionId),
                                                                           table['deleted'].eq(0)])
        medicament = CLocActionPropertyMedicamentInfoList(context, medicamentItems)
        action = CCookedActionInfo(context, actionRecord, CAction(record=actionRecord))
        currentAction = CActionRecordItem(actionRecord, action)

        data088 = {
            'eventByRecord': eventByRecord,
            'diagnosis_31_1': diagnosis_31_1,
            'diagnosis_31_3': diagnosis_31_3,
            'diagnosis_31_4': diagnosis_31_4,
            'diagnosis_31_6': diagnosis_31_6,
            'aboutMedicalExaminationsRequiredAction': aboutMedicalExaminationsRequiredAction,
            'medicament': medicament,
            'currentAction': currentAction,
            'action': action,
        }
        return data088

    # @pyqtSignature('')
    def on_actAmbCardPrintActions_triggered(self):
        index = self.tabAmbCardContent.currentIndex()
        if index:
            table, title = [ (self.tblAmbCardStatusActions,      u'статус'),
                             (self.tblAmbCardDiagnosticActions,  u'диагностика'),
                             (self.tblAmbCardCureActions,        u'лечение'),
                             (self.tblAmbCardMiscActions,        u'прочие мероприятия'),
                             (None,                              u'ЭМД'),
                             (self.tblAmbCardKBiRActions,        u'Карты беременной и роженицы')
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
                      None,
                      None,
                      None,
                      None,
                      self.modelAmbCardSurveyActions,
                      None,
                      self.modelAmbCardKBiRActions
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
    def on_selectionModelAmbCardStatusActionsSort_currentRowChanged(self, current, previous):
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

    def on_selectionModelAmbCardSurveyActionsSort_currentRowChanged(self, current, previous):
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
    def on_selectionModelAmbCardDiagnosticActionsSort_currentRowChanged(self, current, previous):
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
    def on_selectionModelAmbCardCureActionsSort_currentRowChanged(self, current, previous):
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
        filter = {'begDate': self.edtAmbCardVisitBegDate.date(),
                  'endDate': self.edtAmbCardVisitEndDate.date(),
                  'orgStructureId': self.cmbAmbCardVisitOrgStructure.value(),
                  'specialityId': self.cmbAmbCardVisitSpeciality.value(),
                  'personId': self.cmbAmbCardVisitPerson.value(),
                  'sceneId': self.cmbAmbCardVisitScene.value(),
                  'eventTypeId': self.cmbAmbCardVisitEventType.value(),
                  'serviceId': self.cmbAmbCardVisitService.value()}

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

#    @pyqtSignature('QAbstractButton*')
    def on_cmdAmbCardKBiRButtonBox_clicked(self, button):
        buttonCode = self.cmdAmbCardKBiRButtonBox.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.on_cmdAmbCardKBiRButtonBox_apply()
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.on_cmdAmbCardKBiRButtonBox_reset()
            self.on_cmdAmbCardKBiRButtonBox_apply()

#    @pyqtSignature('')
    def on_cmdAmbCardKBiRButtonBox_reset(self):
        self.resetAmbCardFilter(self.edtAmbCardKBiRBegDate,
                                self.edtAmbCardKBiREndDate,
                                self.cmbAmbCardKBiRGroup,
                                self.edtAmbCardKBiROffice,
                                self.cmbAmbCardKBiROrgStructure
                                )

#    @pyqtSignature('')
    def on_cmdAmbCardKBiRButtonBox_apply(self):
        filter = self.getAmbCardFilter(
                        self.edtAmbCardKBiRBegDate,
                        self.edtAmbCardKBiREndDate,
                        self.cmbAmbCardKBiRGroup,
                        self.edtAmbCardKBiROffice,
                        self.cmbAmbCardKBiROrgStructure
                        )
        self.updateAmbCardKBiR(filter)
        self.focusAmbCardKBiRActions()

    # @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelAmbCardMiscActionsSort_currentRowChanged(self, current, previous):
        self.updateAmbCardPropertiesTable(current, self.tblAmbCardMiscActionProperties, previous)
        self.updateAmbCardPrintActionAction(current)

#    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelAmbCardKBiRActionsSort_currentRowChanged(self, current, previous):
        actionId = self.tblAmbCardKBiRActions.currentItemId()
        self.updateAmbCardKBiRF111(actionId)
        self.updateAmbCardPrintActionAction(current)

    # @pyqtSignature('')
    def on_actMiscShowPropertyHistory_triggered(self):
        self.tblAmbCardMiscActionProperties.showHistory()

    # @pyqtSignature('')
    def on_actMiscShowPropertiesHistory_triggered(self):
        self.tblAmbCardMiscActionProperties.showHistoryEx()

    def on_actGetFileObject_triggered(self):
        recordItem = self.getCurrentFileItem()._record
        itemMasterId = forceInt(recordItem.value('master_id'))
        itemTable = forceString(recordItem.value('objectTableName'))
        clientId = self.parent().parent().parent().parent()._ambCardFilesUserId
        if itemTable == 'Event':
            pass
        elif itemTable == 'Action':
            pass
        elif itemTable == 'Client':
            pass
        elif itemTable == 'ProphylaxisPlanning':
            pass
        
        
    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelAmbCardPreviousPregnancy_currentRowChanged(self, current, previous=None):
        index = self.tblAmbCardPreviousPregnancy.currentIndex()
        if index.isValid():
            row = index.row()
            actionId = self.modelAmbCardPreviousPregnancy.getActionIdToRow(row)
            items = self.modelAmbCardPreviousPregnancy.items()
            if 0 <= row < len(items) and hasattr(items[row], 'aboutChildrenProperties'):
                self.modelAmbCardPreviousPregnancyChildren.setItems(items[row].aboutChildrenProperties.getItems())
            else:
                self.modelAmbCardPreviousPregnancyChildren.clearItems()
            self.updatePreviousPregnancyChildren(current, self.tblAmbCardPreviousPregnancyChildren, previous, actionId)


    def updatePreviousPregnancyChildren(self, index, tbl, previous=None, actionId=None):
        if previous:
            tbl.savePreferencesLoc(previous.row())
        if index.isValid() and actionId:
            row = index.row()
            db = QtGui.qApp.db
            table = db.table('Action')
            record = db.getRecordEx(table, '*', [table['id'].eq(actionId), table['deleted'].eq(0)])
            if record:
                clientId = self.currentClientId()
                date = QDate.currentDate()
                clientSex, clientAge = getClientSexAge(clientId, date)
                action = CAction(record=record)
                tbl.model().setAction(action, clientId, clientSex, clientAge)
                setActionPropertiesColumnVisible(action._actionType, tbl)
                tbl.resizeColumnsToContents()
                tbl.resizeRowsToContents()
                tbl.horizontalHeader().setStretchLastSection(True)
                tbl.loadPreferencesLoc(tbl.preferencesLocal, row)
            else:
                tbl.model().setAction(None, None)
    
    
    def getReferenceComboBoxes(self):
        return {
            self.cmbAmbCardODPOBPP1: u'ОД:ПОБ:ПП34:s',
            self.cmbAmbCardODPOBPP_2: u'ОД:ПОБ:ПП34:2:s',
            self.cmbAmbCardODPOBPP_3: u'ОД:ПОБ:ПП34:3:s',
            self.cmbAmbCardODPOBPP_4: u'ОД:ПОБ:ПП34:4:s',
            self.cmbAmbCardODPOBPP_5: u'ОД:ПОБ:ПП34:5:s',
            self.cmbAmbCardODPOBNVMTO_1: u'ОД:ПОБ:НВМТО34:1:s',
            self.cmbAmbCardODPOBNVMTO_2: u'ОД:ПОБ:НВМТО34:2:s',
            self.cmbAmbCardODPOBNVMTO_3: u'ОД:ПОБ:НВМТО34:3:s',
            self.cmbAmbCardODPOBNVMTO_4: u'ОД:ПОБ:НВМТО34:4:s',
            self.cmbAmbCardODPOBNVMTO_5: u'ОД:ПОБ:НВМТО34:5:s',
            self.cmbAmbCardODPOBCZVRP_1: u'ОД:ПОБ:СЗВРП:1:s',
            self.cmbAmbCardODPOBCZVRP_2: u'ОД:ПОБ:СЗВРП:2:s',
            self.cmbAmbCardODPOBCZVRP_3: u'ОД:ПОБ:СЗВРП:3:s',
            self.cmbAmbCardODPOBCZVRP_4: u'ОД:ПОБ:СЗВРП:4:s',
            self.cmbAmbCardODPOBCZVRP_5: u'ОД:ПОБ:СЗВРП:5:s',
            self.cmbAmbCardNVNBPUDRP: u'НВНБ:УД:РП:s',
            self.cmbAmbCardNVNBPUDSM: u'НВНБ:УД:СМ:s',
            self.cmbAmbCardNVNBPUDSST: u'НВНБ:УД:ССТ',
            self.cmbAmbCardNVNBPUDFTB: u'НВНБ:УД:ФТБ:s', 
            self.cmbAmbCardNVNBPUDKOV: u'НВНБ:УД:КОВ:s', 
            self.cmbAmbCardNVNBPUDCA: u'НВНБ:УД:СА:s', 
            self.cmbAmbCardNVNBIBRM: u'НВНБ:ИБРМ:1:s',
            self.cmbAmbCardNVNBIBRP1: u'НВНБ:ИБРП:1:1:1',
            self.cmbAmbCardNVNBIBRP2: u'НВНБ:ИБРП:2:1:1',
            self.cmbAmbCardNVNBIBRP3: u'НВНБ:ИБРП:3:1:1',
            self.cmbAmbCardNVNBIBRP4: u'НВНБ:ИБРП:4:1:1',
            self.cmbAmbCardNVNBIBRP5: u'НВНБ:ИБРП:5:1:1',
        }


    def addCopyAsNewActions(self):
        if self.eventEditor:
            self.tblAmbCardStatusActions.addPopupAction(self.actAmbCardCopyAsNewAction)
            self.tblAmbCardCureActions.addPopupAction(self.actAmbCardCopyAsNewAction)


    def on_actAmbCardCopyAsNewAction_triggered(self):
        index = self.tabAmbCardContent.currentIndex()
        if index:
            table = [self.tblAmbCardStatusActions,
                     self.tblAmbCardDiagnosticActions,
                     self.tblAmbCardCureActions,
                     self.tblAmbCardMiscActions,
                     ][index - 1]
            actionIndex = table.currentIndex()
            row = actionIndex.row()
            if 0 <= row < (table.model().rowCount()):
                record = actionIndex.model().getRecordByRow(row)
                self.emit(SIGNAL('actionCopyAsNew(QSqlRecord, int)'), record, index - 1)


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




class CAmbCardFilterProxyTableView(CTableView):
    def __init__(self, parent):
        CTableView.__init__(self, parent)
        self._sourceModel = None
    
    def setSourceModel(self, sourceModel):
        self._sourceModel = sourceModel
    
    def model(self):
        if self._sourceModel:
            return self._sourceModel
        return CTableView.model(self)


class CAmbCardFilterProxyRegistryActionsTableView(CRegistryActionsTableView):
    def __init__(self, parent):
        CRegistryActionsTableView.__init__(self, parent)
        self._sourceModel = None
    
    def setSourceModel(self, sourceModel):
        self._sourceModel = sourceModel
    
    def model(self):
        if self._sourceModel:
            return self._sourceModel
        return CRegistryActionsTableView.model(self)


class CAmbCardFilterProxyActionPropertiesTableView(CActionPropertiesTableView):
    def __init__(self, parent):
        CActionPropertiesTableView.__init__(self, parent)
        self._sourceModel = None
    
    def setSourceModel(self, sourceModel):
        self._sourceModel = sourceModel
    
    def model(self):
        if self._sourceModel:
            return self._sourceModel
        return CActionPropertiesTableView.model(self)


class CAmbCardSortFilterProxyTableModel(CSortFilterProxyTableModel):
    def sort(self, column, order=Qt.AscendingOrder):
        pass