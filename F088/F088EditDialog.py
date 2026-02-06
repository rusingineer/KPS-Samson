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

# Редактор действия МСЭ форма F088

import re

from PyQt4 import QtGui, QtSql
from PyQt4.QtGui import QCheckBox, QTextEdit
from PyQt4.QtCore import Qt, QDate, QDateTime, QTime, QVariant, pyqtSignature, SIGNAL, QString, QChar, QObject, QEvent, QModelIndex

from Events.EventVisitsModel import CEventVisitsModel
from library.Attach.AttachAction     import getAttachAction
from library.Attach.AttachButton     import CAttachButton
from library.Calendar                import wpFiveDays, wpSixDays, wpSevenDays
from library.Counter                 import CCounterController
from library.InDocTable              import CInDocTableModel, CDateInDocTableCol, CIntInDocTableCol, CInDocTableCol, forcePyType
from library.ICDCodeEdit             import CICDCodeEditEx
from library.ICDInDocTableCol        import CICDExInDocTableCol
from library.ICDMorphologyInDocTableCol import CMKBMorphologyCol
from library.ICDUtils                import getMKBName
from library.interchange             import (
                                              getDatetimeEditValue,
                                              getDoubleBoxValue,
                                              getLineEditValue,
                                              getRBComboBoxValue,
                                              setCheckBoxValue,
                                              setDatetimeEditValue,
                                              setDoubleBoxValue,
                                              setLineEditValue,
                                              setRBComboBoxValue,
                                            )

from library.ItemsListDialog         import CItemEditorBaseDialog
from library.MapCode                 import createMapCodeToRowIdx
from library.PrintInfo               import CInfoContext
from library.PrintTemplates          import applyTemplate, customizePrintButton, getPrintButton
from library.TableModel              import CTableModel, CDateCol, CTextCol, CBoolCol, CEnumCol, CRefBookCol, CDateTimeCol
from library.Utils import (
    calcAgeTuple,
    forceDate,
    forceDateTime,
    forceInt,
    forceRef,
    forceDouble,
    forceString,
    forceStringEx,
    formatName,
    toDateTimeWithoutSeconds,
    trim,
    toVariant, forceBool,
)

from Events.Action                   import CAction, CActionType
from Events.ActionInfo               import CCookedActionInfo
from Events.ActionStatus             import CActionStatus
from Events.ActionTypeCol            import CActionTypeCol
from Events.ActionPropertiesTable    import CActionPropertiesTableModel
from Events.ActionTemplateChoose     import (
                                              CActionTemplateCache,
                                              CActionTemplateSelectButton,
                                            )
from Events.ActionTemplateSaveDialog import CActionTemplateSaveDialog
from Events.ActionTemplateSelectDialog import CActionTemplateSelectDialog
from Events.EventInfo                import CEventInfo, CCookedEventInfo, CDiagnosticInfoProxyList
from Events.EventEditDialog          import CEventEditDialog
from Events.GetPrevActionIdHelper    import CGetPrevActionIdHelper
from Events.Utils import (checkAttachOnDate, checkPolicyOnDate, checkTissueJournalStatusByActions,
                          getEventEnableActionsBeyondEvent, getEventDuration, getEventShowTime,
                          getActionTypeIdListByFlatCode, getDeathDate, getEventPurposeId,
                          setActionPropertiesColumnVisible, specifyDiagnosis, CEventTypeDescription, getEventServiceId,
                          getEventVisitFinance, CFinanceType, )
from library.TimeoutLogout            import CTimeoutLogout
from Orgs.Orgs                       import selectOrganisation
from Orgs.PersonComboBoxEx           import CPersonFindInDocTableCol
from Registry.AmbCardMixin           import getClientActions
from Registry.ClientEditDialog       import CClientEditDialog
from Registry.Utils import getClientInfo, getClientSexAge, getClientBanner
from Users.Rights                    import (
                                              urAdmin,
                                              urCopyPrevAction,
                                              urLoadActionTemplate,
                                              urEditOtherpeopleAction,
                                              urRegTabWriteRegistry,
                                              urRegTabReadRegistry,
                                              urSaveActionTemplate
                                            )

from F088.Ui_F088 import Ui_F088Dialog
from F088.F0882022EditDialog import CEventExportTableModel


class CF088EditDialog(CItemEditorBaseDialog, Ui_F088Dialog):
    def __init__(self, parent, isCreate=False):
        CItemEditorBaseDialog.__init__(self, parent, 'Action')
        self.isCreate = isCreate
        self.action = None
        self.eventId     = None
        self._eventExecDate = None
        self.eventTypeId = None
        self.clientType = CEventEditDialog.ctOther
        self.personSSFCache = {}
        self.eventPurposeId = None
        self.eventServiceId = None
        self.eventSetDate = None
        self.eventDate = None
        self.eventSetDateTime = None
        self.clientId    = None
        self.forceClientId = None
        self.clientSex   = None
        self.clientAge   = None
        self.clientBirthDate = None
        self.clientDeathDate = None
        self.personId    = None
        self.personSNILS = u''
        self.showTypeTemplate = 0
        self.personSpecialityId = None
        self.recordEvent = None
        self.clientInfo = None
        self.actionTypeId = None
        self.idx = 0
        self.domainPurposeDirectionMSI5 = []
        self.domainIPRAResult26_4 = []
        self.domainIPRAResult26_5 = []
        self.isRelationRepresentativeSetClientId = False
        self.getPrevActionIdHelper = CGetPrevActionIdHelper()
        self.addModels('Visits', CEventVisitsModel(self))
        self.addModels('MembersMSIPerson', CMembersMSIPersonTableModel(self))
        self.addModels('TempInvalidYear', CTempInvalidYearTableModel(self))
        self.addModels('DiagnosisDisease_30_2', CDiagnosisDisease_30_2_TableModel(self, diagnosisTypeCode=u'51'))
        self.addModels('DiagnosisDisease_30_3', CDiagnosisDisease_30_TableModel(self, diagnosisTypeCode=u'52'))
        self.addModels('DiagnosisDisease_30_5', CDiagnosisDisease_30_TableModel(self, diagnosisTypeCode=u'53'))
        self.addModels('DiagnosisDisease_30_6', CDiagnosisDisease_30_TableModel(self, diagnosisTypeCode=u'54'))
        self.addModels('AmbCardStatusActions_28', CAmbCardDiagnosticsActionsCheckTableModel(self))
        self.addModels('AmbCardStatusActionProperties_28', CActionPropertiesTableModel(self))
        self.addModels('AmbCardDiagnosticActions_29', CAmbCardDiagnosticsActionsCheckTableModel(self))
        self.addModels('AmbCardDiagnosticActionProperties_29', CActionPropertiesTableModel(self))
        self.addModels('Export', CEventExportTableModel(self))
        self.addObject('actEditClient', QtGui.QAction(u'Открыть регистрационную карточку', self))
        self.addObject('actShowAttachedToClientFiles', getAttachAction('Client_FileAttach',  self))
        self.addObject('btnPrint', getPrintButton(self, ''))
        self.addObject('btnLoadTemplate', CActionTemplateSelectButton(self))
        self.addObject('btnAttachedFiles', CAttachButton(self, u'Прикреплённые файлы'))
        self.btnLoadTemplate.setText(u'Загрузить шаблон')
        self.addObject('btnSaveAsTemplate', QtGui.QPushButton(u'Сохранить шаблон', self))
        self.addObject('btnLoadPrevAction', QtGui.QPushButton(u'Копировать из предыдущего', self))
        self.addObject('mnuLoadPrevAction',  QtGui.QMenu(self))
        self.addObject('actLoadSameSpecialityPrevAction', QtGui.QAction(u'Той же самой специальности', self))
        self.addObject('actLoadOwnPrevAction',            QtGui.QAction(u'Только свои', self))
        self.addObject('actLoadAnyPrevAction',            QtGui.QAction(u'Любое', self))
        self.addObject('actAmbCardPrintStatusActions',    QtGui.QAction(u'Преобразовать в текст и вставить в блок', self))
        self.addObject('actAmbCardPrintDiagnosticActions',QtGui.QAction(u'Преобразовать в текст и вставить в блок', self))
        self.mnuLoadPrevAction.addAction(self.actLoadSameSpecialityPrevAction)
        self.mnuLoadPrevAction.addAction(self.actLoadOwnPrevAction)
        self.mnuLoadPrevAction.addAction(self.actLoadAnyPrevAction)
        self.btnLoadPrevAction.setMenu(self.mnuLoadPrevAction)
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setWindowTitleEx(u'Мероприятие МСЭ')
        self.initNewDate()
        self.edtDirectionDate.canBeEmpty(True)
        self.edtEndDate.canBeEmpty(True)
        self.edtBegDate.canBeEmpty(True)
        self.buttonBox.addButton(self.btnPrint, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnLoadTemplate, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnSaveAsTemplate, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnLoadPrevAction, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnAttachedFiles, QtGui.QDialogButtonBox.ActionRole)
        self.setModels(self.tblTempInvalidYear, self.modelTempInvalidYear, self.selectionModelTempInvalidYear)
        self.setModels(self.tblMembersMSIPerson, self.modelMembersMSIPerson, self.selectionModelMembersMSIPerson)
        self.setModels(self.tblDiagnosisDisease_30_2, self.modelDiagnosisDisease_30_2, self.selectionModelDiagnosisDisease_30_2)
        self.setModels(self.tblDiagnosisDisease_30_3, self.modelDiagnosisDisease_30_3, self.selectionModelDiagnosisDisease_30_3)
        self.setModels(self.tblDiagnosisDisease_30_5, self.modelDiagnosisDisease_30_5, self.selectionModelDiagnosisDisease_30_5)
        self.setModels(self.tblDiagnosisDisease_30_6, self.modelDiagnosisDisease_30_6, self.selectionModelDiagnosisDisease_30_6)
        self.setModels(self.tblAmbCardStatusActions_28, self.modelAmbCardStatusActions_28, self.selectionModelAmbCardStatusActions_28)
        self.setModels(self.tblAmbCardStatusActionProperties_28, self.modelAmbCardStatusActionProperties_28, self.selectionModelAmbCardStatusActionProperties_28)
        self.setModels(self.tblAmbCardDiagnosticActions_29, self.modelAmbCardDiagnosticActions_29, self.selectionModelAmbCardDiagnosticActions_29)
        self.setModels(self.tblAmbCardDiagnosticActionProperties_29, self.modelAmbCardDiagnosticActionProperties_29, self.selectionModelAmbCardDiagnosticActionProperties_29)
        self.setModels(self.tblExport, self.modelExport, self.selectionModelExport)
        self.tblAmbCardStatusActions_28.createPopupMenu([self.actAmbCardPrintStatusActions])
        self.tblAmbCardDiagnosticActions_29.createPopupMenu([self.actAmbCardPrintDiagnosticActions])
        self.txtClientInfoBrowser.actions.append(self.actEditClient)
        self.txtClientInfoBrowser.actions.append(self.actShowAttachedToClientFiles)
        self.actEditClient.setEnabled(QtGui.qApp.userHasAnyRight([urAdmin, urRegTabWriteRegistry, urRegTabReadRegistry]))
        self.tabTempInvalidAndAegrotat.setCurrentIndex(1 if QtGui.qApp.tempInvalidDoctype() == '2' else 0)
        self.grpTempInvalid.setEventEditor(self)
        self.grpTempInvalid.setType(0, '1')
        self.grpAegrotat.setEventEditor(self)
        self.grpAegrotat.setType(0, '2')
        self.grpDisability.setEventEditor(self)
        self.grpDisability.setType(1)
        self.grpVitalRestriction.setEventEditor(self)
        self.grpVitalRestriction.setType(2)
        self.setupDirtyCather()
        self.setIsDirty(False)
        self.actionTemplateCache = CActionTemplateCache(self, self.cmbPerson)
        action = QtGui.QAction(self)
        action.setShortcut('F3')
        self.addAction(action)
        self.modelTempInvalidYear.setEventEditor(self)
        self.modelMembersMSIPerson.setEventEditor(self)
        self.tabNotes.setEventEditor(self)
        self.modelDiagnosisDisease_30_2.setEventEditor(self)
        self.modelDiagnosisDisease_30_3.setEventEditor(self)
        self.modelDiagnosisDisease_30_5.setEventEditor(self)
        self.modelDiagnosisDisease_30_6.setEventEditor(self)
        self.tblTempInvalidYear.addPopupDelRow()
        self.tblMembersMSIPerson.addPopupDelRow()
        self.tblDiagnosisDisease_30_2.addPopupDelRow()
        self.tblDiagnosisDisease_30_3.addPopupDelRow()
        self.tblDiagnosisDisease_30_5.addPopupDelRow()
        self.tblDiagnosisDisease_30_6.addPopupDelRow()
        self.modifiableDiagnosisesMap = {}
        self.mapSpecialityIdToDiagFilter = {}
        self.mapMKBTraumaList = createMapCodeToRowIdx( [row for row in [(u'S00 -T99.9')]]).keys()
        self.modelAmbCardStatusActionProperties_28.setReadOnly(True)
        self.modelAmbCardDiagnosticActionProperties_29.setReadOnly(True)
        self.cmbClientIsLocatedOrg.setNameField('CONCAT(infisCode,\'| \', shortName)')
        self.edtTempInvalidDocumentElectronicNumber.installEventFilter(self)
        self.edtTempInvalidDocumentElectronicNumber.setCursorPosition(0)
        splStatusIndex = self.splStatus.indexOf(self.tabHealthClientDirectionMSI)
        self.splStatus.setCollapsible(splStatusIndex, False)
        splStatusIndex2 = self.splStatus.indexOf(self.tabAmbCardContent_28)
        self.splStatus.setCollapsible(splStatusIndex2, True)
        splInspectionIndex = self.splInspection.indexOf(self.tabInfoAboutMedicalExaminationsRequired)
        self.splInspection.setCollapsible(splInspectionIndex, False)
        splInspectionIndex2 = self.splInspection.indexOf(self.tabAmbCardInspection_29)
        self.splInspection.setCollapsible(splInspectionIndex2, True)
        self.cmbAmbCardStatusGroup_28.setClasses([0, 3])
        self.cmbAmbCardStatusGroup_28.setClassesVisible(True)
        self.cmbAmbCardDiagnosticGroup_29.setClass(1)
        self.createApplyButton()
        self.servicesURL = forceString(QtGui.qApp.getGlobalPreference('23:servicesURL'))
        self.tabWidget.setTabEnabled(self.tabWidget.indexOf(self.tabExtendedMSE), forceBool(self.servicesURL))
        self.connect(self.edtBegDate, SIGNAL('dateChanged(const QDate &)'), self.on_edtBegDate_dateChanged)
        self.connect(self.edtEndDate, SIGNAL('dateChanged(const QDate &)'), self.on_edtEndDate_dateChanged)

        self._timeoutLogout = CTimeoutLogout(self)
        if QtGui.qApp.getEventTimeout() != 0 and bool(self.itemId()):
            self._timeoutLogout.setup(QtGui.qApp.getEventTimeout() * 60000, u'обращение')


    def createApplyButton(self):
        self.addObject('btnApply', QtGui.QPushButton(u'Применить', self))
        self.buttonBox.addButton(self.btnApply, QtGui.QDialogButtonBox.ApplyRole)
        self.connect(self.btnApply, SIGNAL('clicked()'), self.on_btnApply_clicked)


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
            QtGui.qApp.delAllCounterValueIdReservation()
            self.lock(self._tableName, self._id)
            return True
        else:
            return False


    def getOrganisationByMSI_43Filter(self):
        domain = None
        for propertyTypeName, propertyType in self.action.getType()._propertiesByName.items():
            shortName = trim(propertyType.shortName)
            if shortName == u'43':
                if propertyType.valueType:
                    domain = propertyType.valueType.domain
                break
        db = QtGui.qApp.db
        if domain and u'isDirection' in domain:
            domainAND = domain.split('AND')
            domainTrim = []
            for domainI in domainAND:
                domainTrim.append(trim(domainI))
            domain = db.joinAnd(domainTrim.remove(u'(isDirection)'))
        return db.joinAnd([domain] if domain else [])


    def initNewDate(self):
        if self.isCreate:
            self.edtProtocolDateMSI.setDate(QDate())
            self.edtDirectionDateMSI.setDate(QDate())
            self.edtPrevMSI19_2.setDate(QDate())
            self.edtPrevMSI19_7.setDate(QDate())
            self.edtIPRADateMSI.setDate(QDate())
            self.edtRepresentativeDocumentDate.setDate(QDate())


    def initNewData(self):
        if self.isCreate:
            self.on_cmbAnamnesis27_4_currentIndexChanged(0)


    def eventFilter(self, watched, event):
        if watched == self.edtTempInvalidDocumentElectronicNumber:
            if event.type() == QEvent.MouseButtonPress:
                event.accept()
                maskLen = len(trim(self.edtTempInvalidDocumentElectronicNumber.inputMask())) - 1
                curPos = self.edtTempInvalidDocumentElectronicNumber.cursorPositionAt(event.pos())
                pos = len(trim(self.edtTempInvalidDocumentElectronicNumber.text()))
                if not pos or curPos == maskLen:
                    self.edtTempInvalidDocumentElectronicNumber.setCursorPosition(0)
                    return True
                elif curPos > pos:
                    self.edtTempInvalidDocumentElectronicNumber.setCursorPosition(pos)
                    return True
        return QtGui.QDialog.eventFilter(self, watched, event)


    def saveDiagnostics(self, modelDiagnostics, eventId):
        items = modelDiagnostics.items()
        recordAction = self.action.getRecord() if self.action else None
        begDate = forceDateTime(recordAction.value('begDate')) if recordAction else QDateTime()
        db = QtGui.qApp.db
        tableDiagnosis = db.table('Diagnosis')
        tableRbDiagnosticResult = db.table('rbDiagnosticResult')
        eventType = CEventTypeDescription.get(self.eventTypeId)
        recDiagResult = db.getRecordEx(tableRbDiagnosticResult,
                                       [tableRbDiagnosticResult['id'], tableRbDiagnosticResult['result_id']],
                                       tableRbDiagnosticResult['eventPurpose_id'].eq(eventType.purposeId))
        personId = None
        specialityId = None
        if recordAction:
            personId = forceRef(recordAction.value('person_id'))
            if personId:
                tablePerson = db.table('Person')
                recordPerson = db.getRecordEx(tablePerson, [tablePerson['speciality_id']],
                                              [tablePerson['id'].eq(personId), tablePerson['deleted'].eq(0)])
                specialityId = forceRef(recordPerson.value('speciality_id')) if recordPerson else None
            elif QtGui.qApp.userId and QtGui.qApp.userSpecialityId:
                personId = QtGui.qApp.userId
                specialityId = QtGui.qApp.userSpecialityId

        for item in items:
            item.setValue('setDate', toVariant(begDate))
            item.setValue('endDate', toVariant(begDate))
            item.setValue('event_id', toVariant(eventId))
            item.setValue('speciality_id', toVariant(specialityId))
            item.setValue('person_id', toVariant(personId))
            item.setValue('result_id', recDiagResult.value('id') if recDiagResult else None)
            record = None
            diagnosisId = forceRef(item.value('diagnosis_id'))
            if diagnosisId:
                record = db.getRecordEx(tableDiagnosis, '*', [tableDiagnosis['id'].eq(diagnosisId), tableDiagnosis['deleted'].eq(0)])
            if not record:
                record = tableDiagnosis.newRecord()
            record.setValue('MKB', toVariant(forceStringEx(item.value('MKB'))))
            record.setValue('morphologyMKB', toVariant(forceStringEx(item.value('morphologyMKB'))))
            record.setValue('diagnosisType_id', item.value('diagnosisType_id'))
            record.setValue('client_id', toVariant(self.clientId))
            record.setValue('person_id', item.value('person_id'))
            record.setValue('setDate', item.value('setDate'))
            record.setValue('endDate', item.value('endDate'))
            newDiagnosisId = db.insertOrUpdate(tableDiagnosis, record)
            record.setValue('id', toVariant(newDiagnosisId))
            item.setValue('diagnosis_id', toVariant(newDiagnosisId))
        modelDiagnostics.saveItems(eventId)


    @pyqtSignature('')
    def on_tblAmbCardStatusActions_28_popupMenuAboutToShow(self):
        notEmpty = self.modelAmbCardStatusActions_28.rowCount() > 0
        self.actAmbCardPrintStatusActions.setEnabled(notEmpty)


    @pyqtSignature('')
    def on_tblAmbCardDiagnosticActions_29_popupMenuAboutToShow(self):
        notEmpty = self.modelAmbCardDiagnosticActions_29.rowCount() > 0
        self.actAmbCardPrintDiagnosticActions.setEnabled(notEmpty)


    def getSelectedActions(self, selectedIdList):
        actionDict = {}
        db = QtGui.qApp.db
        table = db.table('Action')
        for id in selectedIdList:
            if id and id not in actionDict.keys():
                record = db.getRecordEx(table, '*', [table['id'].eq(id), table['deleted'].eq(0)])
                if record:
                    action = CAction(record=record)
                    if action:
                        endDate = forceDate(record.value('endDate'))
                        actionType = action.getType()
                        actionLine = [u'', u'']
                        valuePropertyList = []
                        #actionLine[0] = ((actionType.code + u'-') if actionType.code else u'') + actionType.name + u': '
                        actionLine[0] = unicode(endDate.toString('dd.MM.yyyy')) + u' ' + actionType.name + u': '
                        propertiesById = action.getPropertiesById()
                        properties = propertiesById.values()
                        properties.sort(key=lambda prop:prop._type.idx)
#                        for prop in propertiesById.itervalues():
                        for prop in properties:
                            type = prop.type()
                            if prop.getValue() and not type.isJobTicketValueType():
                                valuePropertyList.append(type.name + u' - ' + (forceString(prop.getText()) if not type.isBoolean() else (u'Да' if prop.getValue() else u'Нет')))
                        #valuePropertyList.sort()
                        actionLine[1] = u'; '.join(val for val in valuePropertyList if val)
                        actionDict[id] = actionLine
        actionDictValues = actionDict.values()
        actionDictValues.sort(key=lambda x:x[0])
        return actionDictValues


    @pyqtSignature('')
    def on_actAmbCardPrintStatusActions_triggered(self):
        selectedIdList = self.modelAmbCardStatusActions_28.getSelectedIdList()
        actionDictValues = self.getSelectedActions(selectedIdList)
        if actionDictValues:
            oldValue = self.edtHealthClientDirectionMSI.toPlainText()
            newValue = u'\n'.join((val[0] + val[1]) for val in actionDictValues if val)
            value = (oldValue + u'\n' + newValue) if oldValue else newValue
            self.edtHealthClientDirectionMSI.setText(value)


    @pyqtSignature('')
    def on_actAmbCardPrintDiagnosticActions_triggered(self):
        selectedIdList = self.modelAmbCardDiagnosticActions_29.getSelectedIdList()
        actionDictValues = self.getSelectedActions(selectedIdList)
        if actionDictValues:
            oldValue = self.edtInfoAboutMedicalExaminationsRequired.toPlainText()
            newValue = u'\n'.join((val[0] + val[1]) for val in actionDictValues if val)
            value = (oldValue + u'\n' + newValue) if oldValue else newValue
            self.edtInfoAboutMedicalExaminationsRequired.setText(value)


    def on_actionAmountChanged(self, value):
        self.edtAmount.setValue(value)


    def setEventDate(self, date):
        eventRecord = self._getEventRecord()
        if eventRecord:
            execDate = forceDate(eventRecord.value('execDate'))
            # if not execDate:
            self._eventExecDate = date
            self.eventDate = date


    def _getEventRecord(self):
        if not self.recordEvent and self.eventId:
            self.recordEvent = QtGui.qApp.db.getRecordEx('Event', 'id, execDate, isClosed', 'id=%d'%self.eventId)
        return self.recordEvent


    def setReduced(self, value):
        self.txtClientInfoBrowser.setVisible(not value)
        if self.clientInfo is None:
            self.clientInfo = getClientInfo(self.clientId, date=self.edtDirectionDate.date())
        name = formatName(self.clientInfo.lastName, self.clientInfo.firstName, self.clientInfo.patrName)
        self.setWindowTitle(self.windowTitle()+' : '+ name)


    def exec_(self):
        QtGui.qApp.setCounterController(CCounterController(self))
        QtGui.qApp.setJTR(self)
        try:
            result = CItemEditorBaseDialog.exec_(self)
        finally:
            QtGui.qApp.unsetJTR(self)
        if result:
            QtGui.qApp.delAllCounterValueIdReservation()
        else:
            QtGui.qApp.resetAllCounterValueIdReservation()
        QtGui.qApp.setCounterController(None)
        QtGui.qApp.disconnectClipboard()
        return result


    def setForceClientId(self, clientId):
        self.forceClientId = clientId


    def getCurrentTimeAction(self, actionDate):
        currentDateTime = QDateTime.currentDateTime()
        if currentDateTime == actionDate:
            currentTime = currentDateTime.time()
            return currentTime.addSecs(60)
        else:
            return currentDateTime.time()


    def getClientId(self, eventId):
        if self.forceClientId:
            return self.forceClientId
        return forceRef(QtGui.qApp.db.translate('Event', 'id', eventId, 'client_id'))


    def setComboBoxes(self):
        self.setPropertyDomainWidget(self.cmbClientCitizenship, u'9', isNotDefined=False)
        self.setPropertyDomainWidget(self.cmbClientMilitaryDuty, u'10', isNotDefined=False)
        self.setPropertyDomainWidget(self.cmbClientIsLocated, u'13', isNotDefined=False)
        self.setPropertyDomainWidget(self.cmbPrevMSI19_1, u'19.1', isNotDefined=False)
        self.setPropertyDomainWidget(self.cmbPrevMSI19_3, u'19.3', isNotDefined=False)
        self.setPropertyDomainWidget(self.cmbPrevMSI19_4, u'19.4', isNotDefined=False)
        self.setPropertyDomainWidget(self.cmbPrevMSI19_6, u'19.6', isNotDefined=False)
        self.setPropertyDomainWidget(self.cmbClinicalPrognosis, u'31', isNotDefined=False)
        self.setPropertyDomainWidget(self.cmbRehabilitationPotential, u'32', isNotDefined=False)
        self.setPropertyDomainWidget(self.cmbRehabilitationPrognosis, u'33', isNotDefined=False)
        domain5, defaultValue5 = self.getPropertyDomain(u'5')
        self.domainPurposeDirectionMSI5 = domain5.split(u',')
        domain26_4, defaultValue26_4 = self.getPropertyDomain(u'26.4')
        self.domainIPRAResult26_4 = domain26_4.split(u',')
        domain26_5, defaultValue26_5 = self.getPropertyDomain(u'26.5')
        self.domainIPRAResult26_5 = domain26_5.split(u',')
        self.cmbOrganisationByMSI_43.setGlobalFilter(self.getOrganisationByMSI_43Filter())


    def setPropertyDomainWidget(self, widget, propertyShortName, isNotDefined=True):
        widget._model.clear()
        domain, defaultValue = self.getPropertyDomain(propertyShortName, isNotDefined)
        widget.setDomain(domain, isUpdateCurrIndex=False)
        if self.isCreate:
            if defaultValue:
                widget.setValue(defaultValue)
            else:
                widget.setCurrentIndex(0)


    def getPropertyDomain(self, propertyShortName, isNotDefined=True):
        domain = u'\'не определено\',' if isNotDefined else u''
        record, defaultValue = self.propertyDomain(propertyShortName)
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


    def propertyDomain(self, propertyShortName):
        db = QtGui.qApp.db
        tableAT = db.table('ActionType')
        tableAPT = db.table('ActionPropertyType')
        cond = [tableAT['id'].eq(self.actionTypeId),
                tableAT['deleted'].eq(0),
                tableAPT['shortName'].like(propertyShortName),
                tableAPT['deleted'].eq(0)
                ]
        queryTable = tableAT.innerJoin(tableAPT, tableAT['id'].eq(tableAPT['actionType_id']))
        record = db.getRecordEx(queryTable, [tableAPT['valueDomain'], tableAPT['defaultValue']], cond)
        if record:
            return record.value(0), record.value(1)
        return None, None


    @pyqtSignature('int')
    def on_tabWidget_currentChanged(self, index):
        widget = self.tabWidget.widget(index)
        if widget is not None:
            focusProxy = widget.focusProxy()
            if focusProxy:
                focusProxy.setFocus(Qt.OtherFocusReason)
        if index == 6:  # Статус (п.28)
            self.on_cmdAmbCardStatusButtonBox_28_reset()
            self.on_cmdAmbCardStatusButtonBox_28_apply()
        if index == 7:  # Обследование (п.29)
            self.on_cmdAmbCardDiagnosticButtonBox_29_reset()
            self.on_cmdAmbCardDiagnosticButtonBox_29_apply()
        if index == 12:  # amb card page
            self.tabAmbCard.resetWidgets()


    def selectAmbCardActions(self, filter, classCode, order, fieldName):
        return getClientActions(self.clientId, filter, classCode, order, fieldName)


    def getAmbCardFilter(self, edtBegDate, edtEndDate, cmbGroup, edtOffice, cmbOrgStructure):
        filter = {}
        filter['begDate'] = edtBegDate.date()
        filter['endDate'] = edtEndDate.date()
        filter['actionGroupId'] = cmbGroup.value()
        filter['office'] = forceString(edtOffice.text())
        filter['orgStructureId'] = cmbOrgStructure.value()
        return filter


    def resetAmbCardFilter(self, edtBegDate, edtEndDate, cmbGroup, edtOffice, cmbOrgStructure):
        edtBegDate.setDate(QDate())
        edtEndDate.setDate(QDate())
        cmbGroup.setValue(None)
        edtOffice.setText('')
        cmbOrgStructure.setValue(None)


    @pyqtSignature('QAbstractButton*')
    def on_btnAmbCardStatusButtonBox_28_clicked(self, button):
        buttonCode = self.btnAmbCardStatusButtonBox_28.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.on_cmdAmbCardStatusButtonBox_28_apply()
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.on_cmdAmbCardStatusButtonBox_28_reset()


    @pyqtSignature('QAbstractButton*')
    def on_btnAmbCardDiagnosticButtonBox_29_clicked(self, button):
        buttonCode = self.btnAmbCardDiagnosticButtonBox_29.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.on_cmdAmbCardDiagnosticButtonBox_29_apply()
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.on_cmdAmbCardDiagnosticButtonBox_29_reset()


    def on_cmdAmbCardDiagnosticButtonBox_29_reset(self):
        self.resetAmbCardFilter(self.edtAmbCardDiagnosticBegDate_29,
                                self.edtAmbCardDiagnosticEndDate_29,
                                self.cmbAmbCardDiagnosticGroup_29,
                                self.edtAmbCardDiagnosticOffice_29,
                                self.cmbAmbCardDiagnosticOrgStructure_29
                                )


    def on_cmdAmbCardDiagnosticButtonBox_29_apply(self):
        filter = self.getAmbCardFilter(
                        self.edtAmbCardDiagnosticBegDate_29,
                        self.edtAmbCardDiagnosticEndDate_29,
                        self.cmbAmbCardDiagnosticGroup_29,
                        self.edtAmbCardDiagnosticOffice_29,
                        self.cmbAmbCardDiagnosticOrgStructure_29
                        )
        self.updateAmbCardDiagnostic_29(filter)
        self.focusAmbCardDiagnosticActions_29()


    def updateAmbCardDiagnostic_29(self, filter, posToId=None, fieldName=None):
        self.__ambCardDiagnosticFilter = filter
        order = self.tblAmbCardDiagnosticActions_29.order() if self.tblAmbCardDiagnosticActions_29.order() else ['Action.endDate DESC', 'id']
        self.tblAmbCardDiagnosticActions_29.setIdList(self.selectAmbCardActions(filter, 1, order, fieldName), posToId)


    def focusAmbCardDiagnosticActions_29(self):
        self.tblAmbCardDiagnosticActions_29.setFocus(Qt.TabFocusReason)


    def on_cmdAmbCardStatusButtonBox_28_reset(self):
        self.resetAmbCardFilter(self.edtAmbCardStatusBegDate_28,
                                self.edtAmbCardStatusEndDate_28,
                                self.cmbAmbCardStatusGroup_28,
                                self.edtAmbCardStatusOffice_28,
                                self.cmbAmbCardStatusOrgStructure_28
                                )


    def on_cmdAmbCardStatusButtonBox_28_apply(self):
        filter = self.getAmbCardFilter(
                        self.edtAmbCardStatusBegDate_28,
                        self.edtAmbCardStatusEndDate_28,
                        self.cmbAmbCardStatusGroup_28,
                        self.edtAmbCardStatusOffice_28,
                        self.cmbAmbCardStatusOrgStructure_28
                        )
        self.updateAmbCardStatus_28(filter)
        self.focusAmbCardStatusActions_28()


    def updateAmbCardStatus_28(self, filter, posToId=None, fieldName=None):
        self.__ambCardStatusFilter = filter
        order = self.tblAmbCardStatusActions_28.order() if self.tblAmbCardStatusActions_28.order() else ['Action.endDate DESC', 'id']
        self.tblAmbCardStatusActions_28.setIdList(self.selectAmbCardActions(filter, [0, 3], order, fieldName), posToId)


    def focusAmbCardStatusActions_28(self):
        self.tblAmbCardStatusActions_28.setFocus(Qt.TabFocusReason)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelAmbCardStatusActions_28_currentRowChanged(self, current, previous):
        self.updateAmbCardPropertiesTable(current, self.tblAmbCardStatusActionProperties_28, previous)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelAmbCardDiagnosticActions_29_currentRowChanged(self, current, previous):
        self.updateAmbCardPropertiesTable(current, self.tblAmbCardDiagnosticActionProperties_29, previous)


    def updateAmbCardPropertiesTable(self, index, tbl, previous=None):
        if previous:
            tbl.savePreferencesLoc(previous.row())
        row = index.row()
        record = index.model().getRecordByRow(row) if row >= 0 else None
        if record:
            clientId = self.clientId
            clientSex = self.clientSex
            clientAge = self.clientAge
            action = CAction(record=record)
            tbl.model().setAction2(action, clientId, clientSex, clientAge)
            setActionPropertiesColumnVisible(action._actionType, tbl)
            tbl.resizeColumnsToContents()
            tbl.resizeRowsToContents()
            tbl.horizontalHeader().setStretchLastSection(True)
            tbl.loadPreferencesLoc(tbl.preferencesLocal, row)
        else:
            tbl.model().setAction2(None, None)


    def setRecord(self, record):
        CItemEditorBaseDialog.setRecord(self, record)
        self.eventId = forceRef(record.value('event_id'))
        self.eventTypeId = None
        self.eventSetDate = None
        self.eventSetDateTime = None
        self.eventDate = None
        self.recordEvent = None
        db = QtGui.qApp.db
        if self.eventId:
            tableEvent = db.table('Event')
            self.recordEvent = db.getRecordEx(tableEvent, '*', [tableEvent['id'].eq(self.eventId), tableEvent['deleted'].eq(0)])
            if self.recordEvent:
                self.eventTypeId = forceRef(self.recordEvent.value('eventType_id'))
                self.eventSetDate = forceDate(self.recordEvent.value('setDate'))
                self.eventSetDateTime = forceDateTime(self.recordEvent.value('setDate'))
                self.eventDate = forceDate(self.recordEvent.value('execDate'))
                self.eventServiceId = getEventServiceId(self.eventTypeId)
        self.idx = forceInt(record.value('idx'))
        self.clientId = self.getClientId(self.eventId)
        self.action = CAction(record=record)
        self.action.executionPlanManager.load()
        self.action.executionPlanManager.setCurrentItemIndex()
        actionType = self.action.getType()
        self.actionTypeId = actionType.id
        self.setComboBoxes()
        showTime = actionType.showTime
        self.isRelationRepresentativeSetClientId = True
        self.cmbClientRelationRepresentative.clear()
        self.cmbClientRelationRepresentative.setClientId(self.clientId)
        self.cmbClientRelationRepresentative.setValue(forceRef(self.recordEvent.value('relative_id')) if self.recordEvent else None)
        self.tabNotes.cmbClientRelationConsents.clear()
        self.tabNotes.cmbClientRelationConsents.setClientId(self.clientId)
        self.tabNotes.cmbClientRelationConsents.setValue(forceRef(self.recordEvent.value('relative_id')))
        self.isRelationRepresentativeSetClientId = False
        self.edtDirectionTime.setVisible(showTime)
        self.edtPlannedEndTime.setVisible(showTime)
        self.edtBegTime.setVisible(showTime)
        self.edtEndTime.setVisible(showTime)
        self.lblAssistant.setVisible(actionType.hasAssistant)
        self.cmbAssistant.setVisible(actionType.hasAssistant)
        self.setWindowTitle(actionType.code + '|' + actionType.name)
        setCheckBoxValue(self.chkIsUrgent, record, 'isUrgent')
        setDatetimeEditValue(self.edtDirectionDate,    self.edtDirectionTime,    record, 'directionDate')
        setDatetimeEditValue(self.edtPlannedEndDate,   self.edtPlannedEndTime,   record, 'plannedEndDate')
        setDatetimeEditValue(self.edtBegDate,          self.edtBegTime,          record, 'begDate')
        setDatetimeEditValue(self.edtEndDate,          self.edtEndTime,          record, 'endDate')
        setRBComboBoxValue(self.cmbStatus,      record, 'status')
        setDoubleBoxValue(self.edtAmount,       record, 'amount')
        setDoubleBoxValue(self.edtUet,          record, 'uet')
        setRBComboBoxValue(self.cmbPerson,      record, 'person_id')
        setRBComboBoxValue(self.cmbSetPerson,   record, 'setPerson_id')
        setLineEditValue(self.edtOffice,        record, 'office')
        setRBComboBoxValue(self.cmbAssistant,   record, 'assistant_id')
        setLineEditValue(self.edtNote,          record, 'note')
        self.cmbOrg.setValue(forceRef(record.value('org_id')))
        if (self.cmbPerson.value() is None
                and actionType.defaultPersonInEditor in (CActionType.dpUndefined, CActionType.dpCurrentUser, CActionType.dpCurrentMedUser)
                and QtGui.qApp.userSpecialityId):
            self.cmbPerson.setValue(QtGui.qApp.userId)
        self.setPersonId(self.cmbPerson.value())
        self.updateClientInfo()
        context = actionType.context if actionType else ''
        customizePrintButton(self.btnPrint, context)
        self.btnAttachedFiles.setAttachedFileItemList(self.action.getAttachedFileItemList())
        if QtGui.qApp.userHasRight(urLoadActionTemplate) and (self.cmbStatus.value() != CActionStatus.finished or not self.cmbPerson.value() or QtGui.qApp.userId == self.cmbPerson.value() or QtGui.qApp.userHasRight(urEditOtherpeopleAction)):
            actionTemplateTreeModel = self.actionTemplateCache.getModel(actionType.id)
            self.btnLoadTemplate.setModel(actionTemplateTreeModel)
        else:
            self.btnLoadTemplate.setEnabled(False)
        self.btnSaveAsTemplate.setEnabled(QtGui.qApp.userHasRight(urSaveActionTemplate))
        canEdit = not self.action.isLocked() if self.action else True
        for widget in (self.edtPlannedEndDate, self.edtPlannedEndTime,
                       self.cmbStatus, self.edtBegDate, self.edtBegTime,
                       self.edtEndDate, self.edtEndTime,
                       self.cmbPerson, self.edtOffice,
                       self.cmbAssistant,
                       self.edtUet,
                       self.edtNote, self.cmbOrg,
                       self.buttonBox.button(QtGui.QDialogButtonBox.Ok)
                      ):
                widget.setEnabled(canEdit)
        self.btnLoadPrevAction.setEnabled(QtGui.qApp.userHasRight(urCopyPrevAction) and canEdit)
        self.edtAmount.setEnabled(actionType.amountEvaluation == 0 and canEdit)
        if not QtGui.qApp.userHasRight(urLoadActionTemplate) and not (self.cmbStatus.value() != CActionStatus.finished or not self.cmbPerson.value() or QtGui.qApp.userId == self.cmbPerson.value() or QtGui.qApp.userHasRight(urEditOtherpeopleAction)) and not canEdit:
            self.btnLoadTemplate.setEnabled(False)
        canEditPlannedEndDate = canEdit and actionType.defaultPlannedEndDate not in (CActionType.dpedBegDatePlusAmount,
                                                                                     CActionType.dpedBegDatePlusDuration)
        canEditIsExecutionPlan = not bool(self.action.getExecutionPlan() and self.action.executionPlanManager.hasItemsToDo())
        self.edtPlannedEndDate.setEnabled(canEditPlannedEndDate and canEditIsExecutionPlan)
        self.edtPlannedEndTime.setEnabled(canEditPlannedEndDate and bool(self.edtPlannedEndDate.date()) and canEditIsExecutionPlan)
        self.edtBegTime.setEnabled(bool(self.edtBegDate.date()) and canEdit)
        self.edtEndTime.setEnabled(bool(self.edtEndDate.date()) and canEdit)
        self.edtPlannedEndTime.setEnabled(bool(self.edtPlannedEndDate.date()) and canEdit)
        self.setProperties()
        if self.recordEvent:
            self.tabNotes.setNotes(self.recordEvent)
        self.tabNotes.setEventEditor(self)
        self.modelTempInvalidYear.setAction(self.action)
        self.modelTempInvalidYear.loadItems(self.clientId)
        self.modelMembersMSIPerson.setAction(self.action)
        self.modelMembersMSIPerson.loadItems()
        self.modelDiagnosisDisease_30_2.setAction(self.action)
        self.modelDiagnosisDisease_30_2.loadItems(self.eventId)
        self.modelDiagnosisDisease_30_3.setAction(self.action)
        self.modelDiagnosisDisease_30_3.loadItems(self.eventId)
        self.modelDiagnosisDisease_30_5.setAction(self.action)
        self.modelDiagnosisDisease_30_5.loadItems(self.eventId)
        self.modelDiagnosisDisease_30_6.setAction(self.action)
        self.modelDiagnosisDisease_30_6.loadItems(self.eventId)
        self.modelVisits.loadItems(self.eventId)
        self.grpTempInvalid.pickupTempInvalid()
        self.grpAegrotat.pickupTempInvalid()
        self.grpDisability.pickupTempInvalid()
        self.grpVitalRestriction.pickupTempInvalid()
        actionId = self.itemId()
        actionExportIdList = []
        if actionId:
            tableActionFileAttach = db.table('Action_FileAttach')
            tableActionExport = db.table('Action_FileAttach_Export')
            actionExportId = db.getDistinctIdList(tableActionFileAttach, [tableActionFileAttach['id']], [tableActionFileAttach['master_id'].eq(actionId)])
            actionExportIdList = db.getDistinctIdList(tableActionExport, [tableActionExport['id']], [tableActionExport['master_id'].inlist(actionExportId)])
        self.modelExport.setIdList(actionExportIdList)
        lpu_guid = forceString(db.translate('Organisation', 'id', QtGui.qApp.currentOrgId(), 'usishCode'))
        self.tabExtendedMSE.setClientInfo({'clientId': self.clientId, 'lpuGuid': lpu_guid, 'actionId': actionId})


    def getShortNameTextEdit(self):
        return [u'5.14', u'23', u'24', u'26.6', u'28', u'29', u'34', u'35', u'36', u'37']

    def getVisitFinanceId(self, personId=None):
        financeId = None
        if getEventVisitFinance(self.eventTypeId):
            financeId = self.getPersonFinanceId(personId) if personId else self.personFinanceId
        if not financeId:
            financeId = CFinanceType.budget
        return financeId

    def getPersonSSF(self, personId):
        key = personId, self.clientType
        result = self.personSSFCache.get(key, None)
        if not result:
            record = QtGui.qApp.db.getRecord('Person LEFT JOIN rbSpeciality ON rbSpeciality.id = Person.speciality_id',
                                             'speciality_id, service_id, provinceService_id, otherService_id, finance_id, tariffCategory_id',
                                             personId
                                            )
            if record:
                specialityId      = forceRef(record.value('speciality_id'))
                serviceId         = forceRef(record.value('service_id'))
                provinceServiceId = forceRef(record.value('provinceService_id'))
                otherServiceId    = forceRef(record.value('otherService_id'))
                financeId         = forceRef(record.value('finance_id'))
                tariffCategoryId  = forceRef(record.value('tariffCategory_id'))
                if self.clientType == CEventEditDialog.ctOther and otherServiceId:
                    serviceId = otherServiceId
                elif self.clientType == CEventEditDialog.ctProvince and provinceServiceId:
                    serviceId = provinceServiceId
                result = (specialityId, serviceId, financeId, tariffCategoryId)
            else:
                result = (None, None, None, None)
            self.personSSFCache[key] = result
        return result

    def getPersonSpecialityId(self, personId):
        return self.getPersonSSF(personId)[0]

    def getPersonServiceId(self, personId):
        return self.getPersonSSF(personId)[1]

    def getPersonFinanceId(self, personId):
        return self.getPersonSSF(personId)[2]


    def setProperties(self, isCreate=False):
        items = {}
        if self.action:
            shortNameTextEditList = self.getShortNameTextEdit()
            if isCreate:
                for propertyTypeName, propertyType in self.action.getType()._propertiesByName.items():
                    isShortNameTextEdit = False
                    shortName = trim(propertyType.shortName)
                    value = self.action[propertyTypeName]
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
            else:
                for property in self.action._propertiesById.itervalues():
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
            if items:
                # tabToken
                self.edtProtocolNumberMSI.setText(self.getPropertyValue(items, u'1.1', QString))
                self.edtProtocolDateMSI.setDate(self.getPropertyValue(items, u'1.2', QDate))
                self.chkSpendMSIHome.setChecked(self.getPropertyValue(items, u'2', QCheckBox))
                self.chkNeedPalliativeCare.setChecked(self.getPropertyValue(items, u'3', QCheckBox))
                self.edtDirectionDateMSI.setDate(self.getPropertyValue(items, u'4', QDate))
                isPrimary = self.getPropertyValue(items, u'18', int)
                self.chkPrimaryMSI.setChecked(isPrimary == 1)
                self.chkAgainMSI.setChecked(isPrimary == 2)
                purposeDirectionMSI5 = self.getPropertyValue(items, u'5', QString)
                self.chkPurposeDirectionMSI51.setChecked(u'5.1.' in purposeDirectionMSI5)
                self.chkPurposeDirectionMSI52.setChecked(u'5.2.' in purposeDirectionMSI5)
                self.chkPurposeDirectionMSI53.setChecked(u'5.3.' in purposeDirectionMSI5)
                self.chkPurposeDirectionMSI54.setChecked(u'5.4.' in purposeDirectionMSI5)
                self.chkPurposeDirectionMSI55.setChecked(u'5.5.' in purposeDirectionMSI5)
                self.chkPurposeDirectionMSI56.setChecked(u'5.6.' in purposeDirectionMSI5)
                self.chkPurposeDirectionMSI57.setChecked(u'5.7.' in purposeDirectionMSI5)
                self.chkPurposeDirectionMSI58.setChecked(u'5.8.' in purposeDirectionMSI5)
                self.chkPurposeDirectionMSI59.setChecked(u'5.9.' in purposeDirectionMSI5)
                self.chkPurposeDirectionMSI510.setChecked(u'5.10.' in purposeDirectionMSI5)
                self.chkPurposeDirectionMSI511.setChecked(u'5.11.' in purposeDirectionMSI5)
                self.chkPurposeDirectionMSI512.setChecked(u'5.12.' in purposeDirectionMSI5)
                self.chkPurposeDirectionMSI513.setChecked(u'5.13.' in purposeDirectionMSI5)
                self.edtPurposeDirectionMSI514.setPlainText(self.getPropertyValue(items, u'5.14', QTextEdit))
                # tabClientData
                self.cmbClientCitizenship.setValue(self.getPropertyValue(items, u'9', QString))
                self.cmbClientMilitaryDuty.setValue(self.getPropertyValue(items, u'10', QString))
                self.chkClientNoFixedPlaceResidence.setChecked(self.getPropertyValue(items, u'12', QCheckBox))
                self.cmbClientIsLocated.setValue(self.getPropertyValue(items, u'13', QString))
                self.cmbClientIsLocatedOrg.setValue(self.getPropertyValue(items, u'13.x', forceRef))
                self.edtRepresentativeDocumentName.setText(self.getPropertyValue(items, u'17.2.1', QString))
                self.edtRepresentativeDocumentSeria.setText(self.getPropertyValue(items, u'17.2.2.1', QString))
                self.edtRepresentativeDocumentNumber.setText(self.getPropertyValue(items, u'17.2.2.2', QString))
                self.edtRepresentativeDocumentOrigin.setText(self.getPropertyValue(items, u'17.2.3', QString))
                self.edtRepresentativeDocumentDate.setDate(self.getPropertyValue(items, u'17.2.4', QDate))
                self.edtRepresentativeOrgName.setText(self.getPropertyValue(items, u'17.6.1', QString))
                self.edtRepresentativeOrgAddress.setText(self.getPropertyValue(items, u'17.6.2', QString))
                self.edtRepresentativeOrgOGRN.setText(self.getPropertyValue(items, u'17.6.3', QString))
                self.edtClientEducationOrg.setText(self.getPropertyValue(items, u'20.1', QString))
                self.edtClientEducationCourse.setText(self.getPropertyValue(items, u'20.2', QString))
                self.edtClientEducationSpecialty.setText(self.getPropertyValue(items, u'20.3', QString))
                self.edtPatronSpecialty.setText(self.getPropertyValue(items, u'21.1', QString))
                self.edtPatronQualification.setText(self.getPropertyValue(items, u'21.2', QString))
                self.edtPatronWorkExperience.setText(self.getPropertyValue(items, u'21.3', QString))
                self.edtPatronWorkActive.setText(self.getPropertyValue(items, u'21.4', QString))
                self.edtPatronWorkConditions.setText(self.getPropertyValue(items, u'21.5', QString))
                self.edtPatronWorkPlaceOrg.setText(self.getPropertyValue(items, u'21.6', QString))
                self.edtPatronWorkPlaceAddress.setText(self.getPropertyValue(items, u'21.7', QString))
                # tabPrevMSI
                if self.chkAgainMSI.isChecked():
                    self.cmbPrevMSI19_1.setValue(self.getPropertyValue(items, u'19.1', QString))
                    self.edtPrevMSI19_2.setDate(self.getPropertyValue(items, u'19.2', QDate))
                    self.cmbPrevMSI19_3.setValue(self.getPropertyValue(items, u'19.3', QString))
                    self.cmbPrevMSI19_4.setValue(self.getPropertyValue(items, u'19.4', QString))
                    self.edtPrevMSI19_4_16.setText(self.getPropertyValue(items, u'19.4.16', QString))
                    self.edtPrevMSI19_4_17.setText(self.getPropertyValue(items, u'19.4.17', QString))
                    self.edtPrevMSI19_5.setText(self.getPropertyValue(items, u'19.5', QString))
                    self.cmbPrevMSI19_6.setValue(self.getPropertyValue(items, u'19.6', QString))
                    self.edtPrevMSI19_7.setDate(self.getPropertyValue(items, u'19.7', QDate))
                    self.edtPrevMSI19_8.setText(self.getPropertyValue(items, u'19.8', QString))
                # tabAnamnesis
                self.edtAnamnesis22.setText(self.getPropertyValue(items, u'22', QString))
                self.edtAnamnesis23.setText(self.getPropertyValue(items, u'23', QTextEdit))
                self.edtAnamnesis24.setText(self.getPropertyValue(items, u'24', QTextEdit))
                self.edtAnamnesis27_1.setValue(self.getPropertyValue(items, u'27.1', float))
                self.edtAnamnesis27_2.setValue(self.getPropertyValue(items, u'27.2', float))
                self.edtAnamnesis27_3.setValue(self.getPropertyValue(items, u'27.3', float))
                self.cmbAnamnesis27_4.setCurrentIndex(self.cmbAnamnesis27_4.findText('%s'%(self.getPropertyValue(items, u'27.4', QString)), Qt.MatchFixedString))
                self.edtAnamnesis27_5.setValue(self.getPropertyValue(items, u'27.5', int))
                self.edtAnamnesis27_6_1.setValue(self.getPropertyValue(items, u'27.6.1', int))
                self.edtAnamnesis27_6_2.setValue(self.getPropertyValue(items, u'27.6.2', int))
                self.edtAnamnesis27_7.setText(self.getPropertyValue(items, u'27.7', QString))
                self.edtAnamnesis27_8.setText(self.getPropertyValue(items, u'27.8', QString))
                # tabTempInvalidVUT
                self.chkTempInvalidDocumentIsElectronic.setChecked(self.getPropertyValue(items, u'25.1', QCheckBox))
                self.edtTempInvalidDocumentElectronicNumber.setText(self.getPropertyValue(items, u'25.2', QString))
                # tabIPRA
                self.edtIPRANumber.setText(self.getPropertyValue(items, u'26.1', QString))
                self.edtIPRANumberMSI.setText(self.getPropertyValue(items, u'26.2', QString))
                self.edtIPRADateMSI.setDate(self.getPropertyValue(items, u'26.3', QDate))
                IPRAResult26_4 = self.getPropertyValue(items, u'26.4', QString)
                self.chkIPRAResult26_1.setChecked(u'26.1. ' in IPRAResult26_4)
                self.chkIPRAResult26_1_1.setChecked(u'26.1.1. ' in IPRAResult26_4)
                self.chkIPRAResult26_1_2.setChecked(u'26.1.2. ' in IPRAResult26_4)
                self.chkIPRAResult26_1_3.setChecked(u'26.1.3. ' in IPRAResult26_4)
                IPRAResult26_5 = self.getPropertyValue(items, u'26.5', QString)
                self.chkIPRAResult26_2.setChecked(u'26.2. ' in IPRAResult26_5)
                self.chkIPRAResult26_2_1.setChecked(u'26.2.1. ' in IPRAResult26_5)
                self.chkIPRAResult26_2_2.setChecked(u'26.2.2. ' in IPRAResult26_5)
                self.chkIPRAResult26_2_3.setChecked(u'26.2.3. ' in IPRAResult26_5)
                self.edtIPRAResult26_6.setPlainText(self.getPropertyValue(items, u'26.6', QTextEdit))
                # tabStatus
                self.edtHealthClientDirectionMSI.setPlainText(self.getPropertyValue(items, u'28', QTextEdit))
                # tabInspection
                self.edtInfoAboutMedicalExaminationsRequired.setPlainText(self.getPropertyValue(items, u'29', QTextEdit))
                # tabDiagnosis
                self.edtDiagnosisDirectionMSI_30_1.setText(self.getPropertyValue(items, u'30.1', QString))
                self.edtDiagnosisDirectionMSI_30_3.setText(self.getPropertyValue(items, u'30.3', QString))
                self.edtDiagnosisDirectionMSI_30_4.setText(self.getPropertyValue(items, u'30.4', QString))
                self.edtDiagnosisDirectionMSI_30_6.setText(self.getPropertyValue(items, u'30.6', QString))
                self.cmbClinicalPrognosis.setValue(self.getPropertyValue(items, u'31', QString))
                self.cmbRehabilitationPotential.setValue(self.getPropertyValue(items, u'32', QString))
                self.cmbRehabilitationPrognosis.setValue(self.getPropertyValue(items, u'33', QString))
                # tabRecommend
                self.edtRecommendedActionRehabilitation.setPlainText(self.getPropertyValue(items, u'34', QTextEdit))
                self.edtRecommendedActionReconstructiveSurgery.setPlainText(self.getPropertyValue(items, u'35', QTextEdit))
                self.edtRecommendedActionProsthetics.setPlainText(self.getPropertyValue(items, u'36', QTextEdit))
                self.edtHealthResortTreatment.setPlainText(self.getPropertyValue(items, u'37', QTextEdit))
                # tabCommission
                # self.cmbChairmanMSIPerson.setValue(self.getPropertyValue(items, u'38', forceRef))
                # self.cmbChairmanMSIPerson.setVisible(False)
                # self.lblChairmanMSI.setVisible(False)
                self.cmbOrganisationByMSI_43.setValue(self.getPropertyValue(items, u'43', forceRef))


    def getPropertyValue(self, items, shortName, widgetType):
        item = items.get(shortName, [])
        if shortName != u'18' and widgetType == QString:
            return u','.join(val if (val and (isinstance(val, basestring) or type(val) == QString)) else str(val) for val in item if val)
        valueProperty = None
        if len(item) > 0:
            valueProperty = item[0]
        if shortName != u'18' and widgetType == QTextEdit:
            return forceString(valueProperty)
        if shortName == u'18':
            if valueProperty == u'18.1. первично':
                return 1
            elif valueProperty == u'18.2. повторно':
                return 2
            return 0
        if widgetType == forceRef:
            return forceRef(valueProperty)
        if widgetType == QCheckBox:
            if valueProperty and (isinstance(valueProperty, basestring) or type(valueProperty) == QString):
                if valueProperty == u'Да' or valueProperty == u'да' or valueProperty in [u'true', u'True']:
                    return True
            elif type(valueProperty) is int and valueProperty > 0:
                return True
            elif type(valueProperty) is bool:
                return valueProperty
            return False
        if widgetType == int:
            if valueProperty and (isinstance(valueProperty, basestring) or type(valueProperty) == QString):
                if (valueProperty == u'Да' or valueProperty == u'да' or valueProperty in [u'true', u'True']):
                    return 1
                else:
                    return int(valueProperty) if valueProperty else 0
            elif type(valueProperty) is bool:
                return int(valueProperty)
            return forceInt(valueProperty)
        if widgetType == QDate:
            if valueProperty and (isinstance(valueProperty, basestring) or type(valueProperty) == QString):
                return QDate().fromString(valueProperty,'dd.MM.yyyy')
            else:
                return forceDate(valueProperty)
        if widgetType == float:
            return forceDouble(QVariant(valueProperty))


    def setProperty(self, value, propertyShortName):
        if self.action:
            for propertyTypeName, propertyType in self.action.getType()._propertiesByName.items():
                if trim(propertyShortName) == trim(propertyType.shortName):
                    if propertyTypeName and propertyTypeName in self.action._actionType._propertiesByName:
                        self.action[propertyTypeName] = value
                        break


    def getProperty(self, propertyShortName):
        if self.action:
            actionType = self.action.getType()
            for name, propertyType in actionType._propertiesByName.items():
                if trim(propertyType.shortName) == trim(propertyShortName):
                    return toVariant(self.action[name])
        return QVariant()


    def delProperty(self, propertyShortName):
        if self.action:
            actionType = self.action.getType()
            for name, propertyType in actionType._propertiesByName.items():
                if trim(propertyType.shortName) == trim(propertyShortName):
                    del self.action[name]


    def getRecord(self):
        record = self.record()
        showTime = self.action.getType().showTime
        eventRecord = self._getEventRecord()
        getDatetimeEditValue(self.edtDirectionDate, self.edtDirectionTime, record, 'directionDate', showTime)
        getDatetimeEditValue(self.edtPlannedEndDate, self.edtPlannedEndTime, record, 'plannedEndDate', showTime)
        getDatetimeEditValue(self.edtBegDate, self.edtBegTime, record, 'begDate', showTime)
        getDatetimeEditValue(self.edtEndDate, self.edtEndTime, record, 'endDate', showTime)
        getRBComboBoxValue(self.cmbStatus,      record, 'status')
        getDoubleBoxValue(self.edtAmount,       record, 'amount')
        getDoubleBoxValue(self.edtUet,          record, 'uet')
        getRBComboBoxValue(self.cmbPerson,      record, 'person_id')
        getRBComboBoxValue(self.cmbSetPerson,   record, 'setPerson_id')
        getRBComboBoxValue(self.cmbAssistant,   record, 'assistant_id')
        getLineEditValue(self.edtOffice,        record, 'office')
        getLineEditValue(self.edtNote,          record, 'note')
        record.setValue('org_id', QVariant(self.cmbOrg.value()))
        if self.recordEvent:
            self.recordEvent.setValue('relative_id', toVariant(self.cmbClientRelationRepresentative.value()))
        result = type(record)(record) # copy record
        result.remove(result.indexOf('payStatus'))
        if self.recordEvent:
            self.tabNotes.getNotes(self.recordEvent, self.eventTypeId)
        self.modelTempInvalidYear.saveItems(self.clientId)
        self.modelMembersMSIPerson.saveItems()
        return result


    def getEventRecord(self):
        return self.recordEvent


    def saveInternals(self, id):
        if self.checkDataEntered(secondTry=True):
            self.setTextEdits()
            db = QtGui.qApp.db
            id = self.action.save(self.eventId, self.idx, checkModifyDate=False)
            checkTissueJournalStatusByActions([(self.action.getRecord(), self.action)])
            eventRecord = self._getEventRecord()
            if eventRecord:
                eventRecord.setValue('setDate', toVariant(self.action.getRecord().value('begDate')))
                if forceDateTime(self.action.getRecord().value('endDate')):
                    eventRecord.setValue('execDate', self.action.getRecord().value('endDate'))
                    eventRecord.setValue('isClosed', QVariant(1))
                else:
                    eventRecord.setValue('execDate', QVariant(None))
                    eventRecord.setValue('isClosed', QVariant(0))
                eventRecord.setValue('setPerson_id', QVariant(self.personId))
                eventRecord.setValue('execPerson_id', QVariant(self.personId))
                tableRbDiagnosticResult = db.table('rbDiagnosticResult')
                eventType = CEventTypeDescription.get(self.eventTypeId)
                recDiagResult = db.getRecordEx(tableRbDiagnosticResult,
                                               [tableRbDiagnosticResult['result_id']],
                                               tableRbDiagnosticResult['eventPurpose_id'].eq(eventType.purposeId))
                eventRecord.setValue('result_id', recDiagResult.value('result_id') if recDiagResult else None)
                isPrimary = 1
                for property in self.action._propertiesById.itervalues():
                    propertyType = property.type()
                    if trim(propertyType.shortName) == '18':
                        value = property._value
                        propertyValue = propertyType.convertQVariantToPyValue(value) if type(value) == QVariant else value
                        if isinstance(propertyValue, basestring) or type(propertyValue) == QString:
                            propertyValue = trim(propertyValue)
                            if propertyValue == u'18.2. повторно':
                                isPrimary = 2
                            else:
                                isPrimary = 1
                eventRecord.setValue('isPrimary', QVariant(isPrimary))
                eventRecord.setValue('order', QVariant(1))  # порядок события всегда плановый
                QtGui.qApp.db.updateRecord('Event', eventRecord)

            self.tabNotes.saveAttachedFiles(self.eventId)
            self.saveDiagnostics(self.modelDiagnosisDisease_30_2, self.eventId)
            self.saveDiagnostics(self.modelDiagnosisDisease_30_3, self.eventId)
            self.saveDiagnostics(self.modelDiagnosisDisease_30_5, self.eventId)
            self.saveDiagnostics(self.modelDiagnosisDisease_30_6, self.eventId)
            if hasattr(self, 'modelVisits') and self.modelVisits.items():
                visit = self.modelVisits.items()[0]
                visit.setValue('date', toVariant(self.action.getRecord().value('begDate')))
                visit.setValue('person_id', toVariant(self.personId))
                self.modelVisits.setItems([visit])
                self.modelVisits.saveItems(self.eventId)
            self.tabExtendedMSE.saveData()
        return id

    def getAssistantId(self):
        if hasattr(self, 'tabNotes'):
            return self.tabNotes.cmbEventAssistant.value()
        if self.record():
            return forceRef(self.recordEvent.value('assistant_id'))
        return None

    def getModelFinalDiagnostics(self):
        return self.modelDiagnosisDisease_30_2

    def updateClientInfo(self):
        db = QtGui.qApp.db
        self.clientInfo = getClientInfo(self.clientId, date=self.edtDirectionDate.date())
        self.txtClientInfoBrowser.setHtml(getClientBanner(self.clientId, self.edtDirectionDate.date()))
        table  = db.table('Client')
        record = db.getRecord(table, '*', self.clientId)
        if record:
            directionDate = self.edtDirectionDate.date()
            self.clientSex       = forceInt(record.value('sex'))
            self.clientBirthDate = forceDate(record.value('birthDate'))
            self.clientAge       = calcAgeTuple(self.clientBirthDate, directionDate)
        self.actShowAttachedToClientFiles.setMasterId(self.clientId)
        self.tabAmbCard.setClientId(self.clientId, self.clientSex, self.clientAge)
        self.clientDeathDate = getDeathDate(self.clientId)
        self.isRelationRepresentativeSetClientId = True
        self.cmbClientRelationRepresentative.clear()
        self.cmbClientRelationRepresentative.setClientId(self.clientId)
        self.cmbClientRelationRepresentative.setValue(forceRef(self.recordEvent.value('relative_id')) if self.recordEvent else None)
        self.tabNotes.cmbClientRelationConsents.clear()
        self.tabNotes.cmbClientRelationConsents.setClientId(self.clientId)
        self.tabNotes.cmbClientRelationConsents.setValue(forceRef(self.recordEvent.value('relative_id')))
        self.isRelationRepresentativeSetClientId = False


    def currentClientId(self):
        return self.clientId


    def currentClientSex(self):
        return self.clientSex


    def currentClientAge(self):
        return self.clientAge


    def updateAmount(self):
        def getActionDuration(weekProfile):
            startDate = self.edtBegDate.date()
            stopDate  = self.edtEndDate.date()
            if startDate and stopDate:
                return getEventDuration(startDate, stopDate, weekProfile, self.eventTypeId)
            else:
                return 0
        def setAmount(amount):
            self.edtAmount.setValue(amount)
        actionType = self.action.getType()
        if actionType.amountEvaluation == CActionType.actionPredefinedNumber:
            setAmount(actionType.amount)
        elif actionType.amountEvaluation == CActionType.actionDurationWithFiveDayWorking:
            setAmount(actionType.amount*getActionDuration(wpFiveDays))
        elif actionType.amountEvaluation == CActionType.actionDurationWithSixDayWorking:
            setAmount(actionType.amount*getActionDuration(wpSixDays))
        elif actionType.amountEvaluation == CActionType.actionDurationWithSevenDayWorking:
            setAmount(actionType.amount*getActionDuration(wpSevenDays))
        elif actionType.amountEvaluation == CActionType.actionFilledPropsCount:
            setAmount(actionType.amount*self.action.getFilledPropertiesCount())
        elif actionType.amountEvaluation == CActionType.actionAssignedPropsCount:
            setAmount(actionType.amount*self.action.getAssignedPropertiesCount())
        if actionType.defaultPlannedEndDate == CActionType.dpedBegDatePlusAmount:
            begDate = self.edtBegDate.date()
            amountValue = int(self.edtAmount.value())
            date = begDate.addDays(amountValue-1) if begDate and amountValue else QDate()
            self.edtPlannedEndDate.setDate(date)
        elif actionType.defaultPlannedEndDate == CActionType.dpedBegDatePlusDuration:
            begDate = self.edtBegDate.date()
            durationValue = self.edtDuration.value()
            date = begDate.addDays(durationValue) if begDate else QDate()
            self.edtPlannedEndDate.setDate(date)


    def checkDataEntered(self, secondTry=False):
        result = True
        begDate = self.edtBegDate.date()
        endDate = self.edtEndDate.date()
        if endDate:
            if QtGui.qApp.isStrictCheckPolicyOnEndAction() in (0, 1):
                if not checkPolicyOnDate(self.clientId, endDate):
                    skippable = QtGui.qApp.isStrictCheckPolicyOnEndAction() == 0
                    result = result and self.checkInputMessage(u'время закрытия действия соответствующее полису',
                                                               skippable, self.edtEndDate)
            if QtGui.qApp.isStrictCheckAttachOnEndAction() in (0, 1):
                if not checkAttachOnDate(self.clientId, endDate):
                    skippable = QtGui.qApp.isStrictCheckAttachOnEndAction() == 0
                    result = result and self.checkInputMessage(u'время закрытия действия соответствующее прикреплению',
                                                               skippable, self.edtEndDate)
        showTime = self.action._actionType.showTime and getEventShowTime(self.eventTypeId)
        if showTime:
            begDate = toDateTimeWithoutSeconds(QDateTime(begDate, self.edtBegTime.time()))
            endDate = toDateTimeWithoutSeconds(QDateTime(endDate, self.edtEndTime.time()))
            result = result and (endDate >= begDate or self.checkValueMessage(u'Дата выполнения действия %s не должна быть раньше даты начала действия % s'%(forceString(endDate), forceString(begDate)), False, self.edtEndTime))
        if begDate and endDate:
            if showTime:
                result = result and (endDate >= begDate or self.checkValueMessage(u'Дата выполнения действия %s не должна быть раньше даты начала действия % s'%(forceString(endDate), forceString(begDate)), False, self.edtEndTime))
            else:
                result = result and (endDate >= begDate or self.checkValueMessage(u'Дата выполнения действия %s не должна быть раньше даты начала действия % s'%(forceString(endDate), forceString(begDate)), False, self.edtEndDate))
        if result and self.eventId:
            record = QtGui.qApp.db.getRecord('Event', '*',  self.eventId)
            if record:
                actionType = self.action.getType()
                eventTypeId = forceRef(record.value('eventType_id'))
                self.eventPurposeId = getEventPurposeId(eventTypeId)
                setDate = forceDateTime(record.value('setDate')) if showTime else forceDate(record.value('setDate'))
                execDate = forceDateTime(record.value('execDate')) if showTime else forceDate(record.value('execDate'))
                # if execDate and setDate:
                #     if actionType and u'received' in actionType.flatCode.lower():
                #         isControlActionReceivedBegDate = QtGui.qApp.isControlActionReceivedBegDate()
                #         if isControlActionReceivedBegDate:
                #             eventBegDate = forceDateTime(record.value('setDate')) if showTime else forceDate(record.value('setDate'))
                #             eventBegDate = toDateTimeWithoutSeconds(eventBegDate)
                #             actionBegDate = begDate
                #             if eventBegDate != actionBegDate:
                #                 if isControlActionReceivedBegDate == 1:
                #                     message = u'Дата начала случая обслуживания %s не совпадает с датой начала действия Поступление %s. Исправить?'%(forceString(eventBegDate), forceString(actionBegDate))
                #                     skippable = True
                #                 else:
                #                     message = u'Дата начала случая обслуживания %s не совпадает с датой начала действия Поступление %s. Необходимо исправить.'%(forceString(eventBegDate), forceString(actionBegDate))
                #                     skippable = False
                #                 result = result and self.checkValueMessage(message, skippable, self.edtBegDate)
                # if setDate and endDate:
                #     result = result and (endDate >= setDate or self.checkValueMessage(u'Дата выполнения действия %s не должна быть раньше даты начала события % s'%(forceString(endDate), forceString(setDate)), True, self.edtEndDate))
                # actionsBeyondEvent = getEventEnableActionsBeyondEvent(self.eventTypeId)
                # if execDate and endDate and actionsBeyondEvent:
                #     result = result and (execDate >= endDate or self.checkValueMessage(u'Дата выполнения действия %s не должна быть позже даты выполнения события % s'%(forceString(endDate), forceString(execDate)), True if actionsBeyondEvent == 1 else False, self.edtEndDate))
                if setDate and endDate:
                    currentDate = QDate().currentDate()
                    if currentDate and not secondTry:
                        endDateCur = endDate.date() if showTime else endDate
                        result = result and (currentDate >= endDateCur or self.checkValueMessage(
                            u'Дата выполнения действия %s не должна быть позже текущей даты % s'%(forceString(endDateCur), forceString(currentDate)), True, self.edtEndDate)
                        )
                actionRecord = self.action.getRecord()
                status = forceInt(actionRecord.value('status'))
                actionShowTime = self.action._actionType.showTime
                directionDate = QDateTime(self.edtDirectionDate.date(), self.edtDirectionTime.time()) if actionShowTime else self.edtDirectionDate.date()
                nameActionType = actionType.name
                eventEditDialog = CEventEditDialog(self)
                eventEditDialog.setClientBirthDate(self.clientBirthDate)
                eventEditDialog.setClientDeathDate(self.clientDeathDate)
                eventEditDialog.setEventPurposeId(self.eventPurposeId)
                eventEditDialog.setClientSex(self.clientSex)
                eventEditDialog.setClientAge(self.clientAge)
                eventEditDialog.setEventTypeIdToAction(eventTypeId)
                result = result and CEventEditDialog(self).checkActionDataEntered(directionDate, begDate, endDate, None, self.edtDirectionDate, self.edtBegDate, self.edtEndDate, None, 0)
                # result = result and CEventEditDialog(self).checkEventActionDateEntered(setDate, execDate, status, directionDate, begDate, endDate, None, self.edtEndDate, self.edtBegDate, None, 0, nameActionType, actionShowTime=actionShowTime, enableActionsBeyondEvent=actionsBeyondEvent)
        result = result and (begDate or self.checkInputMessage(u'дату назначения', False, self.edtBegDate))
        if not secondTry:
            result = result and (endDate or self.checkInputMessage(u'дату выполнения', True, self.edtEndDate))
        result = result and self.checkPlannedEndDate()
        result = result and self.checkActionMorphology()
        return result


    def getSuggestedPersonId(self):
        return QtGui.qApp.userId if QtGui.qApp.userSpecialityId else self.personId


    def checkActionMorphology(self):
        actionStatus = self.cmbStatus.value()
        if QtGui.qApp.defaultMorphologyMKBIsVisible() \
           and actionStatus in (CActionStatus.finished, CActionStatus.withoutResult):
            action = self.action
            actionType = action.getType()
            defaultMKB = actionType.defaultMKB
            isMorphologyRequired = actionType.isMorphologyRequired
            items = self.modelDiagnosisDisease_30_2.items()
            for item in items:
                morphologyMKB = forceStringEx(item.value('morphologyMKB'))
                if (not bool(re.match('M\d{4}/', forceStringEx(morphologyMKB)))) and defaultMKB > 0 and isMorphologyRequired > 0:
                    if actionStatus == CActionStatus.withoutResult and isMorphologyRequired == 2:
                        return True
                    skippable = True if isMorphologyRequired == 1 else False
                    message = u'Необходимо ввести корректную морфологию диагноза действия `%s`' % actionType.name
                    return self.checkValueMessage(message, skippable, self.cmbMorphologyMKB)
        return True


    def checkPlannedEndDate(self):
        action = self.action
        if action:
            actionType = action.getType()
            if actionType and actionType.isPlannedEndDateRequired in [CActionType.dpedControlMild, CActionType.dpedControlHard]:
                if not self.edtPlannedEndDate.date():
                    skippable = True if actionType.isPlannedEndDateRequired == CActionType.dpedControlMild else False
                    message = u'Необходимо указать Плановую дату выполнения у действия %s'%(actionType.name)
                    return self.checkValueMessage(message, skippable, self.edtPlannedEndDate)
        return True


    def setPersonId(self, personId):
        self.personId = personId
        record = QtGui.qApp.db.getRecord('Person', 'speciality_id, tariffCategory_id, SNILS, showTypeTemplate',  self.personId)
        if record:
            self.personSpecialityId     = forceRef(record.value('speciality_id'))
            self.personTariffCategoryId = forceRef(record.value('tariffCategory_id'))
            self.personSNILS            = forceStringEx(record.value('SNILS'))
            self.showTypeTemplate       = forceInt(record.value('showTypeTemplate'))
            self.actionTemplateCache.setPersonSNILS(self.personSNILS)
            self.actionTemplateCache.setShowTypeTemplate(self.showTypeTemplate)


    def getEventInfo(self, context):
        return None


    @pyqtSignature('QString')
    def on_edtProtocolNumberMSI_textChanged(self, text):
        self.setProperty(QVariant(self.edtProtocolNumberMSI.text()), u'1.1')


    @pyqtSignature('QDate')
    def on_edtProtocolDateMSI_dateChanged(self, date):
        self.setProperty(QVariant(self.edtProtocolDateMSI.date()), u'1.2')


    @pyqtSignature('bool')
    def on_chkSpendMSIHome_toggled(self, checked):
        self.setProperty(QVariant(self.chkSpendMSIHome.isChecked()), u'2')


    @pyqtSignature('bool')
    def on_chkClientNoFixedPlaceResidence_toggled(self, checked):
        self.setProperty(QVariant(self.chkClientNoFixedPlaceResidence.isChecked()), u'12')


    @pyqtSignature('bool')
    def on_chkNeedPalliativeCare_toggled(self, checked):
        self.setProperty(QVariant(self.chkNeedPalliativeCare.isChecked()), u'3')


    @pyqtSignature('QDate')
    def on_edtDirectionDateMSI_dateChanged(self, date):
        self.setProperty(QVariant(self.edtDirectionDateMSI.date()), u'4')


    def tabPrevMSIReset(self):
        self.cmbPrevMSI19_1.setValue(None)
        self.edtPrevMSI19_2.setDate(None)
        self.cmbPrevMSI19_3.setValue(None)
        self.cmbPrevMSI19_4.setValue(None)
        self.edtPrevMSI19_4_16.setText('')
        self.edtPrevMSI19_4_17.setText('')
        self.edtPrevMSI19_5.setText('')
        self.cmbPrevMSI19_6.setValue(None)
        self.edtPrevMSI19_7.setDate(None)
        self.edtPrevMSI19_8.setText('')


    @pyqtSignature('bool')
    def on_chkPrimaryMSI_toggled(self, checked):
        isChecked = self.chkPrimaryMSI.isChecked()
        if isChecked:
            self.chkAgainMSI.setChecked(False)
            self.setProperty(QVariant(u'18.1. первично'), u'18')
            self.tabWidget.setTabEnabled(self.tabWidget.indexOf(self.tabPrevMSI), False)
            self.tabPrevMSIReset()
        elif not self.chkAgainMSI.isChecked():
            self.setProperty(QVariant(), u'18')


    @pyqtSignature('bool')
    def on_chkAgainMSI_toggled(self, checked):
        isChecked = self.chkAgainMSI.isChecked()
        if isChecked:
            self.chkPrimaryMSI.setChecked(False)
            self.setProperty(QVariant(u'18.2. повторно'), u'18')
        elif not self.chkPrimaryMSI.isChecked():
            self.setProperty(QVariant(), u'18')
        self.tabWidget.setTabEnabled(self.tabWidget.indexOf(self.tabPrevMSI), isChecked)


    @pyqtSignature('bool')
    def on_chkPurposeDirectionMSI51_toggled(self, checked):
        isChecked = self.chkPurposeDirectionMSI51.isChecked()
        self.setPurposeDirectionMSI5(isChecked, u'5.1')


    @pyqtSignature('bool')
    def on_chkPurposeDirectionMSI52_toggled(self, checked):
        isChecked = self.chkPurposeDirectionMSI52.isChecked()
        self.setPurposeDirectionMSI5(isChecked, u'5.2')


    @pyqtSignature('bool')
    def on_chkPurposeDirectionMSI53_toggled(self, checked):
        isChecked = self.chkPurposeDirectionMSI53.isChecked()
        self.setPurposeDirectionMSI5(isChecked, u'5.3')


    @pyqtSignature('bool')
    def on_chkPurposeDirectionMSI54_toggled(self, checked):
        isChecked = self.chkPurposeDirectionMSI54.isChecked()
        self.setPurposeDirectionMSI5(isChecked, u'5.4')


    @pyqtSignature('bool')
    def on_chkPurposeDirectionMSI55_toggled(self, checked):
        isChecked = self.chkPurposeDirectionMSI55.isChecked()
        self.setPurposeDirectionMSI5(isChecked, u'5.5')


    @pyqtSignature('bool')
    def on_chkPurposeDirectionMSI56_toggled(self, checked):
        isChecked = self.chkPurposeDirectionMSI56.isChecked()
        self.setPurposeDirectionMSI5(isChecked, u'5.6')


    @pyqtSignature('bool')
    def on_chkPurposeDirectionMSI57_toggled(self, checked):
        isChecked = self.chkPurposeDirectionMSI57.isChecked()
        self.setPurposeDirectionMSI5(isChecked, u'5.7')


    @pyqtSignature('bool')
    def on_chkPurposeDirectionMSI58_toggled(self, checked):
        isChecked = self.chkPurposeDirectionMSI58.isChecked()
        self.setPurposeDirectionMSI5(isChecked, u'5.8')


    @pyqtSignature('bool')
    def on_chkPurposeDirectionMSI59_toggled(self, checked):
        isChecked = self.chkPurposeDirectionMSI59.isChecked()
        self.setPurposeDirectionMSI5(isChecked, u'5.9')


    @pyqtSignature('bool')
    def on_chkPurposeDirectionMSI510_toggled(self, checked):
        isChecked = self.chkPurposeDirectionMSI510.isChecked()
        self.setPurposeDirectionMSI5(isChecked, u'5.10')


    @pyqtSignature('bool')
    def on_chkPurposeDirectionMSI511_toggled(self, checked):
        isChecked = self.chkPurposeDirectionMSI511.isChecked()
        self.setPurposeDirectionMSI5(isChecked, u'5.11')


    @pyqtSignature('bool')
    def on_chkPurposeDirectionMSI512_toggled(self, checked):
        isChecked = self.chkPurposeDirectionMSI512.isChecked()
        self.setPurposeDirectionMSI5(isChecked, u'5.12')


    @pyqtSignature('bool')
    def on_chkPurposeDirectionMSI513_toggled(self, checked):
        isChecked = self.chkPurposeDirectionMSI513.isChecked()
        self.setPurposeDirectionMSI5(isChecked, u'5.13')


    @pyqtSignature('bool')
    def on_chkPurposeDirectionMSI514_toggled(self, checked):
        self.setProperty(QVariant(self.chkPurposeDirectionMSI514.isChecked()), u'5.14')


    def setPurposeDirectionMSI5(self, isChecked, propertyShortName):
        propertyValue = forceString(self.getProperty(u'5'))
        propertyShortNamePoint = propertyShortName + u'. '
        if isChecked:
            if propertyShortNamePoint not in propertyValue:
                for name in self.domainPurposeDirectionMSI5:
                    if propertyShortNamePoint in name:
                        if trim(propertyValue):
                            propertyValue += u','
                        propertyValue += name
                        break
        else:
            if propertyShortNamePoint in propertyValue:
                propertyValueList = propertyValue.split(u',')
                for i, name in enumerate(propertyValueList):
                    if propertyShortNamePoint in name:
                        propertyValueList.pop(i)
                        break
                propertyValue = u''
                for i, name in enumerate(propertyValueList):
                    if trim(name):
                        if trim(propertyValue):
                            propertyValue += u','
                        propertyValue += name
        propertyValue = QString(propertyValue).remove(QChar('\''), Qt.CaseInsensitive)
        self.setProperty(QVariant(propertyValue), u'5')


    @pyqtSignature('int')
    def on_cmbClientRelationRepresentative_currentIndexChanged(self, value):
        if not self.isRelationRepresentativeSetClientId:
            self.recordEvent.setValue('relative_id', toVariant(self.cmbClientRelationRepresentative.value()))
            self.tabNotes.cmbClientRelationConsents.setClientId(self.clientId)
            self.tabNotes.cmbClientRelationConsents.setValue(forceRef(self.recordEvent.value('relative_id')))


    @pyqtSignature('int')
    def on_cmbClientCitizenship_currentIndexChanged(self, value):
        self.setProperty(QVariant(self.cmbClientCitizenship.value()), u'9')


    @pyqtSignature('int')
    def on_cmbClientMilitaryDuty_currentIndexChanged(self, value):
        self.setProperty(QVariant(self.cmbClientMilitaryDuty.value()), u'10')


    @pyqtSignature('int')
    def on_cmbClientIsLocated_currentIndexChanged(self, value):
        self.setProperty(QVariant(self.cmbClientIsLocated.value()), u'13')


    def setTextEdits(self):
        self.setProperty(QVariant(self.edtClientEducationOrg.text()), u'20.1')
        self.setProperty(QVariant(self.edtPurposeDirectionMSI514.toPlainText()), u'5.14')
        self.setProperty(QVariant(self.edtClientEducationCourse.text()),u'20.2')
        self.setProperty(QVariant(self.edtClientEducationSpecialty.text()), u'20.3')
        self.setProperty(QVariant(self.edtPatronSpecialty.text()), u'21.1')
        self.setProperty(QVariant(self.edtPatronWorkActive.text()), u'21.4')
        self.setProperty(QVariant(self.edtPatronWorkConditions.text()), u'21.5')
        self.setProperty(QVariant(self.edtPatronWorkPlaceAddress.text()), u'21.7')
        self.setProperty(QVariant(self.edtPatronWorkPlaceOrg.text()), u'21.6')
        self.setProperty(QVariant(self.edtPrevMSI19_8.toPlainText()), u'19.8')
        self.setProperty(QVariant(self.edtAnamnesis23.toPlainText()), u'23')
        self.setProperty(QVariant(self.edtAnamnesis24.toPlainText()), u'24')
        self.setProperty(QVariant(self.edtIPRAResult26_6.toPlainText()), u'26.6')
        self.setProperty(QVariant(self.edtHealthClientDirectionMSI.toPlainText()), u'28')
        self.setProperty(QVariant(self.edtInfoAboutMedicalExaminationsRequired.toPlainText()), u'29')
        self.setProperty(QVariant(self.edtHealthResortTreatment.toPlainText()), u'37')
        self.setProperty(QVariant(self.edtRecommendedActionProsthetics.toPlainText()), u'36')
        self.setProperty(QVariant(self.edtRecommendedActionReconstructiveSurgery.toPlainText()), u'35')
        self.setProperty(QVariant(self.edtRecommendedActionRehabilitation.toPlainText()), u'34')


    @pyqtSignature('')
    def on_edtClientEducationOrg_textChanged(self):
        self.setProperty(QVariant(self.edtClientEducationOrg.text()), u'20.1')


    @pyqtSignature('')
    def on_edtPurposeDirectionMSI514_textChanged(self):
        self.setProperty(QVariant(self.edtPurposeDirectionMSI514.toPlainText()), u'5.14')


    @pyqtSignature('')
    def on_edtClientEducationCourse_textChanged(self):
        self.setProperty(QVariant(self.edtClientEducationCourse.text()),u'20.2')


    @pyqtSignature('')
    def on_edtClientEducationSpecialty_textChanged(self):
        self.setProperty(QVariant(self.edtClientEducationSpecialty.text()), u'20.3')


    @pyqtSignature('QString')
    def on_edtPatronSpecialty_textChanged(self, text):
        self.setProperty(QVariant(self.edtPatronSpecialty.text()), u'21.1')


    @pyqtSignature('QString')
    def on_edtPatronWorkActive_textChanged(self, text):
        self.setProperty(QVariant(self.edtPatronWorkActive.text()), u'21.4')


    @pyqtSignature('QString')
    def on_edtPatronWorkConditions_textChanged(self, text):
        self.setProperty(QVariant(self.edtPatronWorkConditions.text()), u'21.5')


    @pyqtSignature('QString')
    def on_edtPatronWorkPlaceAddress_textChanged(self, text):
        self.setProperty(QVariant(self.edtPatronWorkPlaceAddress.text()), u'21.7')


    @pyqtSignature('QString')
    def on_edtPatronWorkPlaceOrg_textChanged(self, text):
        self.setProperty(QVariant(self.edtPatronWorkPlaceOrg.text()), u'21.6')


    @pyqtSignature('')
    def on_edtPrevMSI19_8_textChanged(self):
        self.setProperty(QVariant(self.edtPrevMSI19_8.toPlainText()), u'19.8')


    @pyqtSignature('')
    def on_edtAnamnesis23_textChanged(self):
        self.setProperty(QVariant(self.edtAnamnesis23.toPlainText()), u'23')


    @pyqtSignature('')
    def on_edtAnamnesis24_textChanged(self):
        self.setProperty(QVariant(self.edtAnamnesis24.toPlainText()), u'24')


    @pyqtSignature('')
    def on_edtIPRAResult26_6_textChanged(self):
        self.setProperty(QVariant(self.edtIPRAResult26_6.toPlainText()), u'26.6')


    @pyqtSignature('')
    def on_edtHealthClientDirectionMSI_textChanged(self):
        self.setProperty(QVariant(self.edtHealthClientDirectionMSI.toPlainText()), u'28')


    @pyqtSignature('')
    def on_edtInfoAboutMedicalExaminationsRequired_textChanged(self):
        self.setProperty(QVariant(self.edtInfoAboutMedicalExaminationsRequired.toPlainText()), u'29')


    @pyqtSignature('')
    def on_edtHealthResortTreatment_textChanged(self):
        self.setProperty(QVariant(self.edtHealthResortTreatment.toPlainText()), u'37')


    @pyqtSignature('')
    def on_edtRecommendedActionProsthetics_textChanged(self):
        self.setProperty(QVariant(self.edtRecommendedActionProsthetics.toPlainText()), u'36')


    @pyqtSignature('')
    def on_edtRecommendedActionReconstructiveSurgery_textChanged(self):
        self.setProperty(QVariant(self.edtRecommendedActionReconstructiveSurgery.toPlainText()), u'35')


    @pyqtSignature('')
    def on_edtRecommendedActionRehabilitation_textChanged(self):
        self.setProperty(QVariant(self.edtRecommendedActionRehabilitation.toPlainText()), u'34')


    @pyqtSignature('QString')
    def on_edtPatronQualification_textChanged(self, text):
        self.setProperty(QVariant(self.edtPatronQualification.text()), u'21.2')


    @pyqtSignature('QString')
    def on_edtPatronWorkExperience_textChanged(self, text):
        self.setProperty(QVariant(self.edtPatronWorkExperience.text()), u'21.3')


    @pyqtSignature('int')
    def on_cmbPrevMSI19_1_currentIndexChanged(self, value):
        self.setProperty(QVariant(self.cmbPrevMSI19_1.value()), u'19.1')


    @pyqtSignature('QDate')
    def on_edtPrevMSI19_2_dateChanged(self, date):
        self.setProperty(QVariant(self.edtPrevMSI19_2.date()), u'19.2')


    @pyqtSignature('int')
    def on_cmbPrevMSI19_3_currentIndexChanged(self, value):
        self.setProperty(QVariant(self.cmbPrevMSI19_3.value()), u'19.3')


    @pyqtSignature('int')
    def on_cmbPrevMSI19_4_currentIndexChanged(self, value):
        self.setProperty(QVariant(self.cmbPrevMSI19_4.value()), u'19.4')


    @pyqtSignature('QString')
    def on_edtPrevMSI19_4_16_textChanged(self, text):
        self.setProperty(QVariant(self.edtPrevMSI19_4_16.text()), u'19.4.16')


    @pyqtSignature('QString')
    def on_edtPrevMSI19_4_17_textChanged(self, text):
        self.setProperty(QVariant(self.edtPrevMSI19_4_17.text()), u'19.4.17')


    @pyqtSignature('QString')
    def on_edtPrevMSI19_5_textChanged(self, text):
        self.setProperty(QVariant(self.edtPrevMSI19_5.text()), u'19.5')


    @pyqtSignature('int')
    def on_cmbPrevMSI19_6_currentIndexChanged(self, value):
        self.setProperty(QVariant(self.cmbPrevMSI19_6.value()), u'19.6')


    @pyqtSignature('QDate')
    def on_edtPrevMSI19_7_dateChanged(self, date):
        self.setProperty(QVariant(self.edtPrevMSI19_7.date()), u'19.7')


    @pyqtSignature('QString')
    def on_edtAnamnesis22_textChanged(self, text):
        self.setProperty(QVariant(self.edtAnamnesis22.text()), u'22')


    @pyqtSignature('double')
    def on_edtAnamnesis27_1_valueChanged(self, value):
        self.setProperty(QVariant(self.edtAnamnesis27_1.value()), u'27.1')
        self.setBodyMassIndex()


    @pyqtSignature('double')
    def on_edtAnamnesis27_2_valueChanged(self, value):
        self.setProperty(QVariant(self.edtAnamnesis27_2.value()), u'27.2')
        self.setBodyMassIndex()


    def setBodyMassIndex(self):
        growth = forceDouble(self.edtAnamnesis27_1.value())
        weight = forceDouble(self.edtAnamnesis27_2.value())
        growthM = growth/100.0
        bodyMassIndex = float(weight/(growthM*growthM)) if growth > 0 else 0
        self.edtAnamnesis27_3.setValue(bodyMassIndex)


    @pyqtSignature('double')
    def on_edtAnamnesis27_3_valueChanged(self, value):
        self.setProperty(QVariant(self.edtAnamnesis27_3.value()), u'27.3')


    @pyqtSignature('int')
    def on_cmbAnamnesis27_4_currentIndexChanged(self, value):
        self.setProperty(QVariant(self.cmbAnamnesis27_4.currentText()), u'27.4')


    @pyqtSignature('int')
    def on_edtAnamnesis27_5_valueChanged(self, text):
        self.setProperty(QVariant(self.edtAnamnesis27_5.value()), u'27.5')


    @pyqtSignature('int')
    def on_edtAnamnesis27_6_1_valueChanged(self, text):
        self.setProperty(QVariant(self.edtAnamnesis27_6_1.value()), u'27.6.1')


    @pyqtSignature('int')
    def on_edtAnamnesis27_6_2_valueChanged(self, text):
        self.setProperty(QVariant(self.edtAnamnesis27_6_2.value()), u'27.6.2')


    @pyqtSignature('QString')
    def on_edtAnamnesis27_7_textChanged(self, text):
        self.setProperty(QVariant(self.edtAnamnesis27_7.text()), u'27.7')


    @pyqtSignature('QString')
    def on_edtAnamnesis27_8_textChanged(self, text):
        self.setProperty(QVariant(self.edtAnamnesis27_8.text()), u'27.8')


    @pyqtSignature('bool')
    def on_chkTempInvalidDocumentIsElectronic_toggled(self, checked):
        self.setProperty(QVariant(forceInt(self.chkTempInvalidDocumentIsElectronic.isChecked())), u'25.1')


    @pyqtSignature('QString')
    def on_edtTempInvalidDocumentElectronicNumber_textChanged(self, text):
        self.setProperty(QVariant(self.edtTempInvalidDocumentElectronicNumber.text()), u'25.2')


    @pyqtSignature('QString')
    def on_edtIPRANumber_textChanged(self, text):
        self.setProperty(QVariant(self.edtIPRANumber.text()), u'26.1')


    @pyqtSignature('QString')
    def on_edtIPRANumberMSI_textChanged(self, text):
        self.setProperty(QVariant(self.edtIPRANumberMSI.text()), u'26.2')


    @pyqtSignature('QDate')
    def on_edtIPRADateMSI_dateChanged(self, date):
        self.setProperty(QVariant(self.edtIPRADateMSI.date()), u'26.3')


    @pyqtSignature('QString')
    def on_edtRepresentativeDocumentName_textChanged(self, text):
        self.setProperty(QVariant(self.edtRepresentativeDocumentName.text()), u'17.2.1')


    @pyqtSignature('QString')
    def on_edtRepresentativeDocumentSeria_textChanged(self, text):
        self.setProperty(QVariant(self.edtRepresentativeDocumentSeria.text()), u'17.2.2.1')


    @pyqtSignature('QString')
    def on_edtRepresentativeDocumentNumber_textChanged(self, text):
        self.setProperty(QVariant(self.edtRepresentativeDocumentNumber.text()), u'17.2.2.2')


    @pyqtSignature('QString')
    def on_edtRepresentativeDocumentOrigin_textChanged(self, text):
        self.setProperty(QVariant(self.edtRepresentativeDocumentOrigin.text()), u'17.2.3')


    @pyqtSignature('QDate')
    def on_edtRepresentativeDocumentDate_dateChanged(self, date):
        self.setProperty(QVariant(self.edtRepresentativeDocumentDate.date()), u'17.2.4')


    @pyqtSignature('QString')
    def on_edtRepresentativeOrgName_textChanged(self, text):
        self.setProperty(QVariant(self.edtRepresentativeOrgName.text()), u'17.6.1')


    @pyqtSignature('QString')
    def on_edtRepresentativeOrgAddress_textChanged(self, text):
        self.setProperty(QVariant(self.edtRepresentativeOrgAddress.text()), u'17.6.2')


    @pyqtSignature('QString')
    def on_edtRepresentativeOrgOGRN_textChanged(self, text):
        self.setProperty(QVariant(self.edtRepresentativeOrgOGRN.text()), u'17.6.3')


    @pyqtSignature('bool')
    def on_chkIPRAResult26_1_toggled(self, checked):
        isChecked = self.chkIPRAResult26_1.isChecked()
        self.setIPRAResult26_4(isChecked, u'26.1')


    @pyqtSignature('bool')
    def on_chkIPRAResult26_1_1_toggled(self, checked):
        isChecked = self.chkIPRAResult26_1_1.isChecked()
        self.setIPRAResult26_4(isChecked, u'26.1.1')


    @pyqtSignature('bool')
    def on_chkIPRAResult26_1_2_toggled(self, checked):
        isChecked = self.chkIPRAResult26_1_2.isChecked()
        self.setIPRAResult26_4(isChecked, u'26.1.2')


    @pyqtSignature('bool')
    def on_chkIPRAResult26_1_3_toggled(self, checked):
        isChecked = self.chkIPRAResult26_1_3.isChecked()
        self.setIPRAResult26_4(isChecked, u'26.1.3')


    def setIPRAResult26_4(self, isChecked, propertyShortName):
        propertyValue = forceString(self.getProperty(u'26.4'))
        propertyShortNamePoint = propertyShortName + u'. '
        if isChecked:
            if propertyShortNamePoint not in propertyValue:
                for name in self.domainIPRAResult26_4:
                    if propertyShortNamePoint in name and propertyShortNamePoint not in propertyValue and trim(name):
                        if trim(propertyValue):
                            propertyValue += u','
                        propertyValue += name
                        break
        else:
            if propertyShortNamePoint in propertyValue:
                propertyValueList = propertyValue.split(u',')
                for i, name in enumerate(propertyValueList):
                    if propertyShortNamePoint in name:
                        propertyValueList.pop(i)
                        break
                propertyValue = u''
                for i, name in enumerate(propertyValueList):
                    if trim(name):
                        if trim(propertyValue):
                            propertyValue += u','
                        propertyValue += name
        propertyValue = QString(propertyValue).remove(QChar('\''), Qt.CaseInsensitive)
        self.setProperty(QVariant(propertyValue), u'26.4')


    @pyqtSignature('bool')
    def on_chkIPRAResult26_2_toggled(self, checked):
        isChecked = self.chkIPRAResult26_2.isChecked()
        self.setIPRAResult26_5(isChecked, u'26.2')


    @pyqtSignature('bool')
    def on_chkIPRAResult26_2_1_toggled(self, checked):
        isChecked = self.chkIPRAResult26_2_1.isChecked()
        self.setIPRAResult26_5(isChecked, u'26.2.1')


    @pyqtSignature('bool')
    def on_chkIPRAResult26_2_2_toggled(self, checked):
        isChecked = self.chkIPRAResult26_2_2.isChecked()
        self.setIPRAResult26_5(isChecked, u'26.2.2')


    @pyqtSignature('bool')
    def on_chkIPRAResult26_2_3_toggled(self, checked):
        isChecked = self.chkIPRAResult26_2_3.isChecked()
        self.setIPRAResult26_5(isChecked, u'26.2.3')


    def setIPRAResult26_5(self, isChecked, propertyShortName):
        propertyValue = forceString(self.getProperty(u'26.5'))
        propertyShortNamePoint = propertyShortName + u'. '
        if isChecked:
            if propertyShortNamePoint not in propertyValue:
                for name in self.domainIPRAResult26_5:
                    if propertyShortNamePoint in name and propertyShortNamePoint not in propertyValue and trim(name):
                        if trim(propertyValue):
                            propertyValue += u','
                        propertyValue += name
                        break
        else:
            if propertyShortNamePoint in propertyValue:
                propertyValueList = propertyValue.split(u',')
                for i, name in enumerate(propertyValueList):
                    if propertyShortNamePoint in name:
                        propertyValueList.pop(i)
                        break
                propertyValue = u''
                for i, name in enumerate(propertyValueList):
                    if trim(name):
                        if trim(propertyValue):
                            propertyValue += u','
                        propertyValue += name
        propertyValue = QString(propertyValue).remove(QChar('\''), Qt.CaseInsensitive)
        self.setProperty(QVariant(propertyValue), u'26.5')


    @pyqtSignature('QString')
    def on_edtDiagnosisDirectionMSI_30_1_textChanged(self, text):
        self.setProperty(QVariant(self.edtDiagnosisDirectionMSI_30_1.text()), u'30.1')


    @pyqtSignature('QString')
    def on_edtDiagnosisDirectionMSI_30_3_textChanged(self, text):
        self.setProperty(QVariant(self.edtDiagnosisDirectionMSI_30_3.text()), u'30.3')


    @pyqtSignature('QString')
    def on_edtDiagnosisDirectionMSI_30_4_textChanged(self, text):
        self.setProperty(QVariant(self.edtDiagnosisDirectionMSI_30_4.text()), u'30.4')


    @pyqtSignature('QString')
    def on_edtDiagnosisDirectionMSI_30_6_textChanged(self, text):
        self.setProperty(QVariant(self.edtDiagnosisDirectionMSI_30_6.text()), u'30.6')


    def updateDiagnosisDirectionMSI_Info(self, value, widgetInfo):
        if value[-1:] == '.':
            value = value[:-1]
        diagName = forceString(QtGui.qApp.db.translate('MKB', 'DiagID', value, 'DiagName'))
        if diagName:
            widgetInfo.setText(diagName)
        else:
            widgetInfo.clear()


    @pyqtSignature('int')
    def on_cmbClinicalPrognosis_currentIndexChanged(self, value):
        self.setProperty(QVariant(self.cmbClinicalPrognosis.value()), u'31')


    @pyqtSignature('int')
    def on_cmbRehabilitationPotential_currentIndexChanged(self, value):
        self.setProperty(QVariant(self.cmbRehabilitationPotential.value()), u'32')


    @pyqtSignature('int')
    def on_cmbRehabilitationPrognosis_currentIndexChanged(self, value):
        self.setProperty(QVariant(self.cmbRehabilitationPrognosis.value()), u'33')


    # @pyqtSignature('int')
    # def on_cmbChairmanMSIPerson_currentIndexChanged(self, value):
        # self.setProperty(QVariant(self.cmbChairmanMSIPerson.value()), u'38')


    @pyqtSignature('int')
    def on_cmbOrganisationByMSI_43_currentIndexChanged(self, value):
        self.setProperty(QVariant(self.cmbOrganisationByMSI_43.value()), u'43')


    @pyqtSignature('int')
    def on_cmbClientIsLocatedOrg_currentIndexChanged(self, value):
        self.setProperty(QVariant(self.cmbClientIsLocatedOrg.value()), u'13.x')


    @pyqtSignature('')
    def on_actEditClient_triggered(self):
        if QtGui.qApp.userHasAnyRight([urAdmin, urRegTabWriteRegistry, urRegTabReadRegistry]):
            dialog = CClientEditDialog(self)
            try:
                dialog.load(self.clientId)
                if dialog.exec_():
                    self.updateClientInfo()
            finally:
                dialog.deleteLater()


    @pyqtSignature('double')
    def on_edtAmount_valueChanged(self, value):
        actionType = self.action.getType()
        if actionType.defaultPlannedEndDate == CActionType.dpedBegDatePlusAmount:
            begDate = self.edtBegDate.date()
            amountValue = int(value)
            date = begDate.addDays(amountValue-1) if begDate and amountValue else QDate()
            self.edtPlannedEndDate.setDate(date)


    @pyqtSignature('')
    def on_btnSelectOrg_clicked(self):
        orgId = selectOrganisation(self, self.cmbOrg.value(), False, self.cmbOrg.filter)
        self.cmbOrg.updateModel()
        if orgId:
            self.cmbOrg.setValue(orgId)


    @pyqtSignature('int')
    def on_cmbPerson_currentIndexChanged(self, value):
        self.setPersonId(self.cmbPerson.value())
        actionTemplateTreeModel = self.actionTemplateCache.getModel(self.action.getType().id)
        self.btnLoadTemplate.setModel(actionTemplateTreeModel)
        if not(QtGui.qApp.userHasRight(urLoadActionTemplate) and (self.cmbStatus.value() != CActionStatus.finished or not self.cmbPerson.value() or QtGui.qApp.userId == self.cmbPerson.value() or QtGui.qApp.userHasRight(urEditOtherpeopleAction))):
            self.btnLoadTemplate.setEnabled(False)


    @pyqtSignature('QDate')
    def on_edtDirectionDate_dateChanged(self, date):
        self.edtDirectionTime.setEnabled(bool(date))


    @pyqtSignature('QDate')
    def on_edtBegDate_dateChanged(self, date):
        self.edtBegTime.setEnabled(bool(date))
        self.updateAmount()


    @pyqtSignature('QDate')
    def on_edtEndDate_dateChanged(self, date):
        self.edtEndTime.setEnabled(bool(date))
        self.updateAmount()
        if date:
            self.cmbStatus.setValue(CActionStatus.finished)
            if self.eventSetDate and date < self.eventSetDate:
                self.edtBegDate.setDate(QDate())
                self.edtBegTime.setTime(QTime())
                self.edtDirectionDate.setDate(QDate())
                self.edtDirectionTime.setTime(QTime())
            if self.cmbStatus.value() == CActionStatus.finished:
                self.freeJobTicket(QDateTime(self.edtEndDate.date(), self.edtEndTime.time()) if self.edtEndTime.isVisible() else self.edtEndDate.date())
        else:
            if self.cmbStatus.value() == CActionStatus.finished:
                self.cmbStatus.setValue(CActionStatus.canceled)

        if self.action.getType().closeEvent:
            self.setEventDate(date)


    @pyqtSignature('int')
    def on_cmbStatus_currentIndexChanged(self, index):
        actionStatus = self.cmbStatus.value()
        if actionStatus in (CActionStatus.finished, ):
            if not self.edtEndDate.date():
                now = QDateTime.currentDateTime()
                self.edtEndDate.setDate(now.date())
                if self.edtEndTime.isVisible():
                    self.edtEndTime.setTime(now.time())
        elif actionStatus in (CActionStatus.canceled, CActionStatus.refused):
            self.edtEndDate.setDate(QDate())
            self.edtEndTime.setTime(QTime())
            if QtGui.qApp.userId and QtGui.qApp.userSpecialityId:
                self.cmbPerson.setValue(QtGui.qApp.userId)
            else:
                self.cmbPerson.setValue(self.cmbSetPerson.value())
        else:
            self.edtEndDate.setDate(QDate())
            self.edtEndTime.setTime(QTime())


    def freeJobTicket(self, endDate):
        if self.action:
            jobTicketIdList = []
            for property in self.action.getType()._propertiesById.itervalues():
                if property.isJobTicketValueType():
                    jobTicketId = self.action[property.name]
                    if jobTicketId and jobTicketId not in jobTicketIdList:
                        jobTicketIdList.append(jobTicketId)
            if jobTicketIdList:
                db = QtGui.qApp.db
                tableJobTicket = db.table('Job_Ticket')
                cond = [tableJobTicket['id'].eq(jobTicketId),
                        tableJobTicket['deleted'].eq(0)
                        ]
                if self.edtEndTime.isVisible():
                    cond.append(tableJobTicket['datetime'].ge(endDate))
                else:
                    cond.append(tableJobTicket['datetime'].dateGe(endDate))
                records = db.getRecordList(tableJobTicket, '*', cond)
                for record in records:
                    datetime = forceDateTime(record.value('datetime')) if self.edtEndTime.isVisible() else forceDate(record.value('datetime'))
                    if datetime > endDate:
                        self.action[property.name] = None


    @pyqtSignature('int')
    def on_btnPrint_printByTemplate(self, templateId):
        context = CInfoContext()
        action = CCookedActionInfo(context, self.getRecord(), self.action)
        action._isDirty = self.isDirty()
        eventInfo = context.getInstance(CEventInfo, self.eventId)
        eventByRecord = CCookedEventInfo(context, self.eventId, self.recordEvent)
        eventActions = eventInfo.actions
        diagnosis_30_2 = CDiagnosticInfoProxyList(context, [self.modelDiagnosisDisease_30_2])
        diagnosis_30_3 = CDiagnosticInfoProxyList(context, [self.modelDiagnosisDisease_30_3])
        diagnosis_30_5 = CDiagnosticInfoProxyList(context, [self.modelDiagnosisDisease_30_5])
        diagnosis_30_6 = CDiagnosticInfoProxyList(context, [self.modelDiagnosisDisease_30_6])
        data = {'event': eventByRecord,
                'eventByRecord': eventByRecord,
                'diagnosis_30_2': diagnosis_30_2,
                'diagnosis_30_3': diagnosis_30_3,
                'diagnosis_30_5': diagnosis_30_5,
                'diagnosis_30_6': diagnosis_30_6,
                'action': action,
                'client': eventByRecord.client,
                'actions': eventActions,
                'currentActionIndex': 0,
                'tempInvalid': None
                }
        applyTemplate(self, templateId, data, signAndAttachHandler=self.btnAttachedFiles.getSignAndAttachHandler())


    @pyqtSignature('')
    def on_btnLoadTemplate_clicked(self):
        if QtGui.qApp.userHasRight(urLoadActionTemplate) and (self.cmbStatus.value() != CActionStatus.finished
                                                              or not self.cmbPerson.value()
                                                              or QtGui.qApp.userId == self.cmbPerson.value()
                                                              or QtGui.qApp.userHasRight(urEditOtherpeopleAction)):
            record = self.getRecord()
            templateAction = None
            isMethodRecording = CAction.actionNoMethodRecording
            db = QtGui.qApp.db
            personId = QtGui.qApp.userId if QtGui.qApp.userSpecialityId else self.personId
            specialityId = QtGui.qApp.userSpecialityId if QtGui.qApp.userSpecialityId else self.personSpecialityId
            personSNILS = forceString(db.translate(db.table('Person'), 'id', personId, 'SNILS')) if QtGui.qApp.userSpecialityId else self.personSNILS
            dlg = CActionTemplateSelectDialog(parent=self,
                                              actionRecord=record,
                                              action=self.action,
                                              clientSex=self.clientSex,
                                              clientAge=self.clientAge,
                                              personId=personId,
                                              specialityId=specialityId,
                                              orgStructureId=QtGui.qApp.currentOrgStructureId(),
                                              SNILS=personSNILS,
                                              showTypeTemplate=self.showTypeTemplate,
                                              model=self.actionTemplateCache.getModel(self.action.getType().id)
                                              )
            try:
                if dlg.exec_():
                    templateAction = dlg.getSelectAction()
                    isMethodRecording = dlg.getMethodRecording()
            finally:
                dlg.deleteLater()
            if templateAction:
                self.action.updateByAction(templateAction,
                                           checkPropsOnOwner=True,
                                           clientSex=self.clientSex,
                                           clientAge=self.clientAge,
                                           isMethodRecording=isMethodRecording)
                self.setProperties()
                self.modelMembersMSIPerson.loadItems()
                self.updateAmount()


    def getPrevActionId(self, action, type):
        self.getPrevActionIdHelper._clientId = self.clientId
        return self.getPrevActionIdHelper.getPrevActionId(action, type)


    def loadPrevAction(self, type):
        if QtGui.qApp.userHasRight(urCopyPrevAction):
            prevActionId = self.getPrevActionId(self.action, type)
            if prevActionId:
                clientSex, clientAge = getClientSexAge(self.clientId)
                self.action.updateByActionId(prevActionId, clientSex=clientSex, clientAge=clientAge)
                self.setProperties()


    @pyqtSignature('')
    def on_mnuLoadPrevAction_aboutToShow(self):
        self.actLoadSameSpecialityPrevAction.setEnabled(bool(
                self.action and self.getPrevActionId(self.action, CGetPrevActionIdHelper.sameSpecialityPrevAction))
                                                         )
        self.actLoadOwnPrevAction.setEnabled(bool(
                self.action and self.getPrevActionId(self.action, CGetPrevActionIdHelper.ownPrevAction))
                                              )

        self.actLoadAnyPrevAction.setEnabled(bool(
                self.action and self.getPrevActionId(self.action, CGetPrevActionIdHelper.anyPrevAction))
                                              )


    @pyqtSignature('')
    def on_actLoadSameSpecialityPrevAction_triggered(self):
        self.loadPrevAction(CGetPrevActionIdHelper.sameSpecialityPrevAction)


    @pyqtSignature('')
    def on_actLoadOwnPrevAction_triggered(self):
        self.loadPrevAction(CGetPrevActionIdHelper.ownPrevAction)


    @pyqtSignature('')
    def on_actLoadAnyPrevAction_triggered(self):
        self.loadPrevAction(CGetPrevActionIdHelper.anyPrevAction)


    @pyqtSignature('')
    def on_btnSaveAsTemplate_clicked(self):
        if QtGui.qApp.userHasRight(urSaveActionTemplate):
            record = self.getRecord()
            db = QtGui.qApp.db
            personId = QtGui.qApp.userId if QtGui.qApp.userSpecialityId else self.personId
            specialityId = QtGui.qApp.userSpecialityId if QtGui.qApp.userSpecialityId else self.personSpecialityId
            personSNILS  = forceString(db.translate(db.table('Person'), 'id', personId, 'SNILS')) if QtGui.qApp.userSpecialityId else self.personSNILS
            dlg = CActionTemplateSaveDialog(parent=self,
                                            actionRecord=record,
                                            action=self.action,
                                            clientSex=self.clientSex,
                                            clientAge=self.clientAge,
                                            personId=personId,
                                            specialityId=specialityId,
                                            orgStructureId=QtGui.qApp.currentOrgStructureId(),
                                            SNILS=personSNILS,
                                            showTypeTemplate=self.showTypeTemplate
                                           )
            dlg.exec_()
            dlg.deleteLater()
            actionType = self.action.getType()
            self.actionTemplateCache.reset()
            actionTemplateTreeModel = self.actionTemplateCache.getModel(actionType.id)
            self.btnLoadTemplate.setModel(actionTemplateTreeModel)
            if not(QtGui.qApp.userHasRight(urLoadActionTemplate) and (self.cmbStatus.value() != CActionStatus.finished or not self.cmbPerson.value() or QtGui.qApp.userId == self.cmbPerson.value() or QtGui.qApp.userHasRight(urEditOtherpeopleAction))):
                self.btnLoadTemplate.setEnabled(False)


    def getDiagFilter(self):
        result = ''
        personId = self.cmbPerson.value()
        if personId:
            db = QtGui.qApp.db
            tablePerson = db.table('Person')
            record = db.getRecordEx(tablePerson, [tablePerson['speciality_id']], [tablePerson['id'].eq(personId), tablePerson['deleted'].eq(0)])
            specialityId = forceRef(record.value('speciality_id')) if record else None
            result = self.mapSpecialityIdToDiagFilter.get(specialityId, None)
            if result is None:
                result = QtGui.qApp.db.translate('rbSpeciality', 'id', specialityId, 'mkbFilter')
                if result is None:
                    result = ''
                else:
                    result = forceString(result)
                self.mapSpecialityIdToDiagFilter[specialityId] = forceString(result)
        return result


    def specifyDiagnosis(self, MKB):
        diagFilter = self.getDiagFilter()
        date = min(d for d in (self.edtBegDate.date(), self.edtEndDate.date(), QDate().currentDate()) if d)
        acceptable, specifiedMKB, specifiedMKBEx, specifiedCharacterId, specifiedTraumaTypeId, modifiableDiagnosisId, specifiedDispanserId, specifiedRequiresFillingDispanser, specifiedProlongMKB = specifyDiagnosis(self, MKB, diagFilter, self.clientId, self.clientSex, self.clientAge, date, self.mapMKBTraumaList)
        self.modifiableDiagnosisesMap[specifiedMKB] = modifiableDiagnosisId
        return acceptable, specifiedMKB, specifiedMKBEx, specifiedCharacterId, specifiedTraumaTypeId, specifiedDispanserId, specifiedRequiresFillingDispanser, specifiedProlongMKB


class CMembersMSIPersonTableModel(CInDocTableModel):
    class CLocNumbeRowColumn(CInDocTableCol):
        def __init__(self, title, fieldName, width, **params):
            CInDocTableCol.__init__(self, title, fieldName, width, **params)

        def toString(self, val, record, row):
            return toVariant(row + 1)

        def toSortString(self, val, record, row):
            return forcePyType(self.toString(val, record, row))

        def toStatusTip(self, val, record, row):
            return self.toString(val, record, row)

        def alignment(self):
            return QVariant(Qt.AlignLeft + Qt.AlignTop)

    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'Person', 'id', 'id', parent)
        self.addExtCol(CMembersMSIPersonTableModel.CLocNumbeRowColumn(u'№', 'cnt', 5), QVariant.Int).setReadOnly()
        self.addCol(CPersonFindInDocTableCol(u'Члены врачебной комиссии', 'id',  20, 'vrbPersonWithSpecialityAndOrgStr', parent=parent))
        self.readOnly = False
        self.action = None
        self.eventEditor = None
        self.shortNameList = [u'39', u'40', u'41', u'42']


    def setEventEditor(self, eventEditor):
        self.eventEditor = eventEditor


    def setAction(self, action):
        self.action = action
        self.getShortNameList()


    def setReadOnly(self, value=True):
        self.readOnly = value


    def flags(self, index):
        if self.readOnly:
           return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return CInDocTableModel.flags(self, index)


    def getEmptyRecord(self):
        result = CInDocTableModel.getEmptyRecord(self)
        result.append(QtSql.QSqlField('cnt', QVariant.Int))
        return result


    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        row = index.row()
        if 0 <= row < len(self._items):
            if role == Qt.EditRole:
                col = self._cols[column]
                record = self._items[row]
                return record.value(col.fieldName())
            if role == Qt.DisplayRole:
                col = self._cols[column]
                record = self._items[row]
                if column == 0:
                    return col.toString(record.value(col.fieldName()), record, row)
                return col.toString(record.value(col.fieldName()), record)
            if role == Qt.StatusTipRole:
                col = self._cols[column]
                record = self._items[row]
                if column == 0:
                    return col.toStatusTip(record.value(col.fieldName()), record, row)
                return col.toStatusTip(record.value(col.fieldName()), record)
            if role == Qt.TextAlignmentRole:
                col = self._cols[column]
                return col.alignment()
            if role == Qt.ForegroundRole:
                col = self._cols[column]
                record = self._items[row]
                return col.getForegroundColor(record.value(col.fieldName()), record)
        return QVariant()


    def getShortNameList(self):
        for propertyTypeName, propertyType in self.action.getType()._propertiesByName.items():
            shortName = trim(propertyType.shortName)
            if shortName in self.shortNameList or u'42.' in shortName:
                if shortName and shortName not in self.shortNameList:
                    self.shortNameList.append(shortName)


    def setData(self, index, value, role=Qt.EditRole):
        row = index.row()
        if row >= len(self.shortNameList):
            return False
        return CInDocTableModel.setData(self, index, value, role)


    def loadItems(self, masterId = None):
        self._items = []
        if self.eventEditor and self.action:
            items = {}
            for property in self.action._propertiesById.itervalues():
                propertyType = property.type()
                shortName = trim(propertyType.shortName)
                if shortName in self.shortNameList or u'42.' in shortName:
                    if shortName and shortName not in self.shortNameList:
                        self.shortNameList.append(shortName)
                    value = property._value
                    propertyValue = propertyType.convertQVariantToPyValue(value) if type(value) == QVariant else value
                    if isinstance(propertyValue, basestring) or type(propertyValue) == QString:
                        propertyValue = trim(propertyValue)
                    if propertyValue:
                        items[shortName] = forceRef(propertyValue)
            itemsKeys = items.keys()
            itemsKeys.sort()
            for itemsKey in itemsKeys:
                val = items.get(itemsKey, None)
                if val:
                    record = self.getEmptyRecord()
                    record.setValue('id', toVariant(val))
                    self._items.append(record)
        self.reset()


    def saveItems(self, masterId = None):
        if self.eventEditor and self.action:
            for idx, shortName in enumerate(self.shortNameList):
                if shortName and shortName in self.action._actionType._propertiesByName:
                    del self.eventEditor.action[shortName]
            if self.eventEditor and self._items is not None and self.eventEditor.action:
                shortNameListLen = len(self.shortNameList)
                for idx, record in enumerate(self._items):
                    if idx < shortNameListLen:
                        shortName = self.shortNameList[idx]
                    else:
                        shortName = u'42.' + forceString(idx - shortNameListLen + 1)
                        if shortName and shortName not in self.shortNameList:
                            self.shortNameList.append(shortName)
                    self.eventEditor.setProperty(forceInt(record.value('id')), shortName)


class CICDCodeComboBoxF088Ex(CICDCodeEditEx): #0013018
    u"""Редактор кодов МКБ с выпадающим деревом, с ограничением ввода - 1 знак после запятой"""
    def __init__(self, parent = None):
        CICDCodeEditEx.__init__(self, parent)
        self._lineEdit.setInputMask('A99.X;_')


    def sizeHint(self):
        style = self.style()
        option = QtGui.QStyleOptionComboBox()
        option.initFrom(self)
        size = option.fontMetrics.boundingRect('W06.9').size()
        result = style.sizeFromContents(style.CT_ComboBox, # ContentsType type,
                                        option,            # const QStyleOption * option
                                        size,              # const QSize & contentsSize,
                                        self)              # const QWidget * widget = 0
        return result


class CICDExF088InDocTableCol(CICDExInDocTableCol):
    def createEditor(self, parent):
        editor = CICDCodeComboBoxF088Ex(parent)
        return editor


class CTempInvalidYearTableModel(CInDocTableModel):
    class CLocNumbeRowColumn(CInDocTableCol):
        def __init__(self, title, fieldName, width, **params):
            CInDocTableCol.__init__(self, title, fieldName, width, **params)

        def toString(self, val, record, row):
            return toVariant(row + 1)

        def toSortString(self, val, record, row):
            return forcePyType(self.toString(val, record, row))

        def toStatusTip(self, val, record, row):
            return self.toString(val, record, row)

        def alignment(self):
            return QVariant(Qt.AlignLeft + Qt.AlignTop)

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
            return QVariant((MKB+': '+descr) if MKB else '')

        def invalidateRecordsCache(self):
            self.cache.invalidate()


    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'TempInvalid', 'id', 'client_id', parent)
        self.addHiddenCol('diagnosis_id')
        self.addExtCol(CTempInvalidYearTableModel.CLocNumbeRowColumn(u'№', 'cnt', 5), QVariant.Int).setReadOnly()
        self.addCol(CDateInDocTableCol(u'Дата начала ВУТ', 'begDate', 20, canBeEmpty=True)).setReadOnly(False)
        self.addCol(CDateInDocTableCol(u'Дата окончания ВУТ', 'endDate', 20, canBeEmpty=True)).setReadOnly(False)
        self.addCol(CIntInDocTableCol(u'Число дней ВУТ', 'duration', 20)).setReadOnly()
        self.addExtCol(CICDExInDocTableCol(u'Диагноз', 'MKB', 7), QVariant.String).setReadOnly(False)
        self.addExtCol(CTempInvalidYearTableModel.CLocMKBDiagNameColumn(u'Диагноз расшифровка', 'MKB', 20), QVariant.String).setReadOnly()
        self.readOnly = False
        self.action = None
        self.eventEditor = None


    def setEventEditor(self, eventEditor):
        self.eventEditor = eventEditor


    def setAction(self, action):
        self.action = action


    def setReadOnly(self, value=True):
        self.readOnly = value


    def flags(self, index):
        if self.readOnly:
           return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return CInDocTableModel.flags(self, index)


    def getEmptyRecord(self):
        result = CInDocTableModel.getEmptyRecord(self)
        result.append(QtSql.QSqlField('cnt', QVariant.Int))
        result.append(QtSql.QSqlField('MKB', QVariant.String))
        result.setValue('MKB', toVariant(self.getMKBToDiagnosis(forceRef(result.value('diagnosis_id')))))
        return result


    def getMKBToDiagnosis(self, diagnosisId):
        MKB = u''
        if diagnosisId:
            db = QtGui.qApp.db
            table = db.table('Diagnosis')
            record = db.getRecordEx(table, 'MKB', [table['id'].eq(diagnosisId), table['deleted'].eq(0)])
            MKB = forceString(record.value('MKB')) if record else u''
        return MKB


    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        row = index.row()
        if 0 <= row < len(self._items):
            if role == Qt.EditRole:
                col = self._cols[column]
                record = self._items[row]
                return record.value(col.fieldName())
            if role == Qt.DisplayRole:
                col = self._cols[column]
                record = self._items[row]
                if column == 0:
                    return col.toString(record.value(col.fieldName()), record, row)
                return col.toString(record.value(col.fieldName()), record)
            if role == Qt.StatusTipRole:
                col = self._cols[column]
                record = self._items[row]
                if column == 0:
                    return col.toStatusTip(record.value(col.fieldName()), record, row)
                return col.toStatusTip(record.value(col.fieldName()), record)
            if role == Qt.TextAlignmentRole:
                col = self._cols[column]
                return col.alignment()
            if role == Qt.CheckStateRole:
                col = self._cols[column]
                record = self._items[row]
                return col.toCheckState(record.value(col.fieldName()), record)
            if role == Qt.ForegroundRole:
                col = self._cols[column]
                record = self._items[row]
                return col.getForegroundColor(record.value(col.fieldName()), record)
        else:
            if role == Qt.CheckStateRole:
                flags = self.flags(index)
                if (      flags & Qt.ItemIsUserCheckable
                    and   flags & Qt.ItemIsEnabled):
                    col = self._cols[column]
                    return col.toCheckState(QVariant(False), None)
        return QVariant()


    def setData(self, index, value, role=Qt.EditRole):
        row = index.row()
        if row > 9:
            return False
        result = CInDocTableModel.setData(self, index, value, role)
        if result:
            if role == Qt.EditRole:
                if 0 <= row < len(self._items):
                    column = index.column()
                    if column == self.getColIndex('MKB'):
                        self.emitRowChanged(row)
                        return True
                    elif column in [self.getColIndex('begDate'), self.getColIndex('endDate')]:
                        record = self._items[row]
                        begDate = forceDate(record.value('begDate'))
                        endDate = forceDate(record.value('endDate'))
                        duration = begDate.daysTo(endDate)+1 if begDate and endDate and begDate <= endDate else 0
                        record.setValue('duration', toVariant(duration))
                        self.emitCellChanged(row, self.getColIndex('duration'))
                        return True
        return result


    def loadItems(self, masterId):
        if not self.action or not forceRef(self.action.getRecord().value('id')):
            db = QtGui.qApp.db
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
            filter = [table[self._masterIdFieldName].eq(masterId)]
            if self._filter:
                filter.append(self._filter)
            if table.hasField('deleted'):
                filter.append(table['deleted'].eq(0))
            currentDate = QDate.currentDate()  # 0013020
            filter.append(db.joinOr([table['endDate'].isNull(), table['endDate'].dateGe(currentDate.addYears(-1))]))
            if self._idxFieldName:
                order = [self._idxFieldName, table['begDate'].name(), table['endDate'].name()]
            else:
                order = [table['begDate'].name(), table['endDate'].name()]
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
                            item.setValue(field.name(), toVariant(self.getMKBToDiagnosis(forceRef(item.value('diagnosis_id')))))
            self.saveItems(masterId)
        else:
            if self.eventEditor and self.action:
                items = {}
                for property in self.action._propertiesById.itervalues():
                    propertyType = property.type()
                    shortName = trim(propertyType.shortName)
                    value = property._value
                    propertyValue = propertyType.convertQVariantToPyValue(value) if type(value) == QVariant else value
                    if isinstance(propertyValue, basestring) or type(propertyValue) == QString:
                        propertyValue = trim(propertyValue)
                    if propertyValue:
                        item = items.get(shortName, [])
                        if propertyValue and (isinstance(propertyValue, basestring) or type(propertyValue) == QString) and len(propertyValue) > 1:
                            propertyValue = propertyValue.split(u',')
                            item.extend(propertyValue)
                        else:
                            item.append(propertyValue)
                        items[shortName] = item
                if items:
                    self._items = []
                    for idx in xrange(10):
                        begDate = self.eventEditor.getPropertyValue(items, u'25.%s.2'%(forceString(idx+1)), QDate)
                        endDate = self.eventEditor.getPropertyValue(items, u'25.%s.3'%(forceString(idx+1)), QDate)
                        if begDate or endDate:
                            duration = self.eventEditor.getPropertyValue(items, u'25.%s.4'%(forceString(idx+1)), int)
                            MKB = self.eventEditor.getPropertyValue(items, u'25.%s.5'%(forceString(idx+1)), QString)
                            item = self.getEmptyRecord()
                            item.setValue('begDate', toVariant(begDate))
                            item.setValue('endDate', toVariant(endDate))
                            item.setValue('duration', toVariant(duration))
                            item.setValue('MKB', toVariant(MKB))
                            self._items.append(item)
        self.reset()


    def saveItems(self, masterId):
        if self.eventEditor and self._items is not None and self.eventEditor.action:
            for idx, record in enumerate(self._items):
                self.eventEditor.setProperty(forceInt(record.value('cnt')), u'25.%s.1'%(forceString(idx+1)))
                self.eventEditor.setProperty(forceDate(record.value('begDate')), u'25.%s.2'%(forceString(idx+1)))
                self.eventEditor.setProperty(forceDate(record.value('endDate')), u'25.%s.3'%(forceString(idx+1)))
                self.eventEditor.setProperty(forceInt(record.value('duration')), u'25.%s.4'%(forceString(idx+1)))
                self.eventEditor.setProperty(forceStringEx(record.value('MKB')), u'25.%s.5'%(forceString(idx+1)))
            rowCount = self.realRowCount()
            if rowCount < 10:
                noRows = 10 - rowCount
                idx = rowCount + 1
                while noRows > 0:
                    self.eventEditor.delProperty('25.%s.1'%(forceString(idx)))
                    self.eventEditor.delProperty('25.%s.2' % (forceString(idx)))
                    self.eventEditor.delProperty('25.%s.3' % (forceString(idx)))
                    self.eventEditor.delProperty('25.%s.4' % (forceString(idx)))
                    self.eventEditor.delProperty('25.%s.5' % (forceString(idx)))
                    idx += 1
                    noRows -= 1


class CAmbCardDiagnosticsActionsCheckTableModel(CTableModel):
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
        self.enableIdList = []
        self.addColumn(CAmbCardDiagnosticsActionsCheckTableModel.CEnableCol(u'Выбрать', ['id'], 5, self))
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
        self._mapColumnToOrder = {u'directionDate'      :u'Action.directionDate',
                                 u'actionType_id'      :u'ActionType.name',
                                 u'isUrgent'           :u'Action.isUrgent',
                                 u'status'             :u'Action.status',
                                 u'plannedEndDate'     :u'Action.plannedEndDate',
                                 u'begDate'            :u'Action.begDate',
                                 u'endDate'            :u'Action.endDate',
                                 u'setPerson_id'       :u'vrbPersonWithSpeciality.name',
                                 u'person_id'          :u'vrbPersonWithSpeciality.name',
                                 u'office'             :u'Action.office',
                                 u'note'               :u'Action.note'
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
        if role == Qt.CheckStateRole and column == 0:
            id = self._idList[row]
            if id:
                self.setSelected(id, forceInt(value) == Qt.Checked)
                self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index, index)
            return True
        return CTableModel.setData(self, index, value, role)


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


class CExportTableModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self.addColumn(CDateTimeCol(u'Дата и время экспорта', ['dateTime'], 15))
        self.addColumn(CRefBookCol(u'Внешняя система', ['system_id'], 'rbExternalSystem', 20))
        self.addColumn(CEnumCol(u'Состояние', ['success'], [u'не прошёл', u'прошёл'], 15))
        self.addColumn(CTextCol(u'Примечания',     ['note'],                                  6))
        self.setTable('Action_FileAttach_Export')


class CDiagnosisDisease_30_TableModel(CInDocTableModel):
    class CLocMKBDiagNameColumn(CInDocTableCol):
        def __init__(self, title, fieldName, width, **params):
            CInDocTableCol.__init__(self, title, fieldName, width, **params)
            self.cache = {}

        def toString(self, val, record):
            MKB = forceString(record.value('MKB'))
            if self.cache.has_key(MKB):
                descr = self.cache[MKB]
            else:
                descr = getMKBName(MKB) if MKB else ''
                self.cache[MKB] = descr
            return QVariant((MKB+': '+descr) if MKB else '')

        def invalidateRecordsCache(self):
            self.cache.invalidate()


    def __init__(self, parent, diagnosisTypeCode):
        CInDocTableModel.__init__(self, 'Diagnostic', 'id', 'event_id', parent)
        self.addHiddenCol('diagnosis_id')
        self.addExtCol(CICDExF088InDocTableCol(u'Диагноз', 'MKB', 20), QVariant.String).setReadOnly(False)
        self.addCol(CDiagnosisDisease_30_TableModel.CLocMKBDiagNameColumn(u'Диагноз расшифровка', 'id', 30), QVariant.String).setReadOnly()
        self.readOnly = False
        self.action = None
        self.eventEditor = None
        self.diagnosisTypeCode = diagnosisTypeCode
        self.diagnosisTypeId = self.getDiagnosisTypeId(self.diagnosisTypeCode)


    def getDiagnosisTypeId(self, diagnosisTypeCode):
        if diagnosisTypeCode:
            return forceRef(QtGui.qApp.db.translate('rbDiagnosisType', 'code', diagnosisTypeCode, 'id'))
        return None


    def setEventEditor(self, eventEditor):
        self.eventEditor = eventEditor


    def setAction(self, action):
        self.action = action


    def setReadOnly(self, value=True):
        self.readOnly = value


    def flags(self, index):
        if self.readOnly:
           return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return CInDocTableModel.flags(self, index)


    def getEmptyRecord(self):
        result = QtGui.qApp.db.table('Diagnostic').newRecord()
        result.append(QtSql.QSqlField('MKB', QVariant.String))
        result.setValue('MKB', toVariant(self.getMKBToDiagnosis(forceRef(result.value('diagnosis_id')))))
        return result


    def getMKBToDiagnosis(self, diagnosisId):
        MKB = u''
        if diagnosisId:
            db = QtGui.qApp.db
            table = db.table('Diagnosis')
            record = db.getRecordEx(table, 'MKB', [table['id'].eq(diagnosisId), table['deleted'].eq(0)])
            MKB = forceString(record.value('MKB')) if record else u''
        return MKB


    def setMKBAction(self, fieldName, value):
        if self.eventEditor and self.eventEditor.action:
            self.eventEditor.action.getRecord().setValue(fieldName, toVariant(value))
        elif self.action:
            self.action.getRecord().setValue(fieldName, toVariant(value))


    def removeRow(self, row, parentIndex = QModelIndex()):
        row = self.removeRows(row, 1, parentIndex)
        self.reset()
        return row


    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.EditRole:
            row = index.row()
            column = index.column()
            if column == self.getColIndex('MKB'):
                if row == len(self._items):
                    if value.isNull():
                        return False
                    self._addEmptyItem()
                if 0 <= row < len(self._items):
                    newMKB = forceString(value)
                    acceptable, specifiedMKB, specifiedMKBEx, specifiedCharacterId, specifiedTraumaTypeId, specifiedDispanserId, specifiedRequiresFillingDispanser, specifiedProlongMKB = QObject.parent(self).specifyDiagnosis(newMKB)
                    if not acceptable:
                        return False
                    result = CInDocTableModel.setData(self, index, value, role)
                    if result:
                        self._items[row].setValue('diagnosisType_id', toVariant(self.diagnosisTypeId))
                        self.emitCellChanged(row, column)
                    return result
                else:
                    return False
        return CInDocTableModel.setData(self, index, value, role)


    def loadItems(self, masterId):
        db = QtGui.qApp.db
        cols = '*'
        table = self._table
        filter = [table[self._masterIdFieldName].eq(masterId),
                  table['diagnosisType_id'].eq(self.diagnosisTypeId)]
        if self._filter:
            filter.append(self._filter)
        if table.hasField('deleted'):
            filter.append(table['deleted'].eq(0))
        if self._idxFieldName:
            order = [self._idxFieldName, self._idFieldName]
        else:
            order = [self._idFieldName]
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
                        item.setValue(field.name(), toVariant(self.getMKBToDiagnosis(forceRef(item.value('diagnosis_id')))))
        self.reset()


    def saveItems(self, masterId):
        if self._items is not None:
            db = QtGui.qApp.db
            table = self._table
            masterId = toVariant(masterId)
            masterIdFieldName = self._masterIdFieldName
            idFieldName = self._idFieldName
            idList = []
            for idx, record in enumerate(self._items):
                record.setValue(masterIdFieldName, masterId)
                if self._idxFieldName:
                    record.setValue(self._idxFieldName, toVariant(idx))
                if self._extColsPresent:
                    outRecord = self.removeExtCols(record)
                else:
                    outRecord = record
                id = db.insertOrUpdate(table, outRecord)
                record.setValue(idFieldName, toVariant(id))
                idList.append(id)
                self.saveDependence(idx, id)

            filter = [table[masterIdFieldName].eq(masterId),
                      table['deleted'].eq(0),
                      table['diagnosisType_id'].eq(self.diagnosisTypeId),
                      'NOT ('+table[idFieldName].inlist(idList)+')']
            if self._filter:
                filter.append(self._filter)
            db.deleteRecord(table, filter)


class CDiagnosisDisease_30_2_TableModel(CDiagnosisDisease_30_TableModel):
    def __init__(self, parent, diagnosisTypeCode):
        CDiagnosisDisease_30_TableModel.__init__(self, parent, diagnosisTypeCode)
        self._enableAppendLine = False
        self.mapMKBToServiceId = {}
        self.isMKBMorphology = QtGui.qApp.defaultMorphologyMKBIsVisible()
        if self.isMKBMorphology:
            self.addExtCol(CMKBMorphologyCol(u'Морфология МКБ', 'morphologyMKB', 10, 'MKB_Morphology', filter='`group` IS NOT NULL'), QVariant.String).setReadOnly(False)


    def rowCount(self, index = None):
        return 1


    def getEmptyRecord(self):
        result = CDiagnosisDisease_30_TableModel.getEmptyRecord(self)
        if self.isMKBMorphology:
            result.append(QtSql.QSqlField('morphologyMKB', QVariant.String))
            result.setValue('morphologyMKB', toVariant(self.getMorphologyMKBToDiagnosis(forceRef(result.value('diagnosis_id')))))
        return result


    def getMorphologyMKBToDiagnosis(self, diagnosisId):
        morphologyMKB = u''
        if diagnosisId:
            db = QtGui.qApp.db
            table = db.table('Diagnosis')
            record = db.getRecordEx(table, 'morphologyMKB', [table['id'].eq(diagnosisId), table['deleted'].eq(0)])
            morphologyMKB = forceString(record.value('morphologyMKB')) if record else u''
        return morphologyMKB


    def getMorphologyMKBFilter(self, MKB):
        cond = ['`group` IS NOT NULL']
        db = QtGui.qApp.db
        if bool(MKB):
            table = db.table('MKB_Morphology')
            if MKB.endswith('.'):
                MKB = MKB[:-1]
            condAnd1 = db.joinAnd([table['bottomMKBRange1'].le(MKB[:3]),
                        table['topMKBRange1'].ge(MKB[:3])])
            condAnd2 = db.joinAnd([table['bottomMKBRange1'].le(MKB),
                        table['topMKBRange1'].ge(MKB)])
            condAnd3 = db.joinAnd([table['bottomMKBRange2'].le(MKB[:3]),
                        table['topMKBRange2'].ge(MKB[:3])])
            condAnd4 = db.joinAnd([table['bottomMKBRange2'].le(MKB),
                        table['topMKBRange2'].ge(MKB)])
            condOr = db.joinOr([condAnd1, condAnd2, condAnd3, condAnd4])
            cond.append(condOr)
        filter = db.joinAnd(cond)
        return filter


    def setData(self, index, value, role=Qt.EditRole):
        row = index.row()
        if row > 0:
            return False
        if role == Qt.EditRole:
            column = index.column()
            if column == self.getColIndex('MKB'):
                if row == len(self._items):
                    if value.isNull():
                        return False
                    self._addEmptyItem()
                if 0 <= row < len(self._items):
                    newMKB = forceString(value)
                    acceptable, specifiedMKB, specifiedMKBEx, specifiedCharacterId, specifiedTraumaTypeId, specifiedDispanserId, specifiedRequiresFillingDispanser, specifiedProlongMKB = QObject.parent(self).specifyDiagnosis(newMKB)
                    if not acceptable:
                        return False
                    result = CInDocTableModel.setData(self, index, value, role)
                    if result:
                        record = self._items[row]
                        self._items[row].setValue('diagnosisType_id', toVariant(self.diagnosisTypeId))
                        mkb = forceStringEx(record.value('MKB'))
                        self.setMKBAction('MKB', mkb)
                        if self.isMKBMorphology:
                            columnMorphologyMKB = self.getColIndex('morphologyMKB')
                            if columnMorphologyMKB != -1:
                                col = self._cols[columnMorphologyMKB]
                                if mkb:
                                    if mkb[-1:] == '.':
                                        mkb = mkb[:-1]
                                    col.setFilter(self.getMorphologyMKBFilter(unicode(mkb)))
                        self.emitCellChanged(row, column)
                    return result
                else:
                    return False
            elif self.isMKBMorphology and column == self.getColIndex('morphologyMKB'):
                result = CInDocTableModel.setData(self, index, value, role)
                if result:
                    record = self._items[row]
                    self._items[row].setValue('diagnosisType_id', toVariant(self.diagnosisTypeId))
                    self.setMKBAction('morphologyMKB', forceStringEx(record.value('morphologyMKB')))
                    self.emitCellChanged(row, column)
                return result
        return CInDocTableModel.setData(self, index, value, role)


    def loadItems(self, masterId):
        db = QtGui.qApp.db
        cols = '*'
        table = self._table
        filter = [table[self._masterIdFieldName].eq(masterId),
                  table['diagnosisType_id'].eq(self.diagnosisTypeId)]
        if self._filter:
            filter.append(self._filter)
        if table.hasField('deleted'):
            filter.append(table['deleted'].eq(0))
        if self._idxFieldName:
            order = [self._idxFieldName, self._idFieldName]
        else:
            order = [self._idFieldName]
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
                    item.setValue('MKB', toVariant(self.getMKBToDiagnosis(forceRef(item.value('diagnosis_id')))))
                    if self.isMKBMorphology:
                        item.setValue('morphologyMKB', toVariant(self.getMorphologyMKBToDiagnosis(forceRef(item.value('diagnosis_id')))))
        self.reset()

    def diagnosisServiceId(self):
        items = self.items()
        if items:
            code = forceString(items[0].value('MKB'))
            if code in self.mapMKBToServiceId:
                return self.mapMKBToServiceId[code]
            else:
                serviceId = forceRef(QtGui.qApp.db.translate('MKB', 'DiagID', code, 'service_id'))
                self.mapMKBToServiceId[code] = serviceId
                return serviceId
        else:
            return None
