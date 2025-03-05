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

from PyQt4 import QtGui, QtSql, QtCore
from PyQt4.QtGui import QCheckBox, QTextEdit
from PyQt4.QtCore import Qt, QDate, QDateTime, QVariant, pyqtSignature, SIGNAL, QString, QChar, QObject, QEvent, QModelIndex

from Events.ExportMIS import iniExportEvent
from library.TimeoutLogout import CTimeoutLogout
from library.Attach.AttachAction     import getAttachAction
from library.Attach.AttachButton     import CAttachButton
from library.Calendar                import wpFiveDays, wpSixDays, wpSevenDays
from library.Counter                 import CCounterController
from library.InDocTable              import (CInDocTableModel,
                                             CDateInDocTableCol,
                                             CIntInDocTableCol,
                                             CInDocTableCol,
                                             CBoolInDocTableCol,
                                             CDateTimeInDocTableCol,
                                             CEnumInDocTableCol,
                                             forcePyType,
                                             forceBool)
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
from library.ESKLP.ESKLPSmnnComboBox import CESKLPSmnnComboBox
from library.MapCode                 import createMapCodeToRowIdx
from library.PrintInfo               import CInfoContext
from library.PrintTemplates          import applyTemplate, customizePrintButton, getPrintButton
from library.TableModel              import CTableModel, CDateCol, CTextCol, CBoolCol, CEnumCol, CRefBookCol, CDateTimeCol, CCol, CIntCol
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
    toVariant, exceptionToUnicode
)

from Events.Action                   import CAction, CActionType
from Events.ActionEditDialog         import CActionEditDialog
from Events.ActionInfo               import CCookedActionInfo, CLocActionPropertyActionsInfoList, CLocActionPropertyMedicamentInfoList
from Events.ActionStatus             import CActionStatus
from Events.ActionTypeCol            import CActionTypeCol
from Events.ActionTypeComboBox       import CActionTypeTableCol
from Events.ActionPropertiesTable    import CActionPropertiesTableModel
from Events.ActionTemplateChoose     import (
                                              CActionTemplateCache
                                            )
from Events.ActionsModel import CActionRecordItem
from Events.ActionsSummaryModel      import CActionPerson
from Events.EventInfo                import CEventInfo, CCookedEventInfo, CDiagnosticInfo
from Events.MKBInfo                  import CMKBInfo
from Events.EventEditDialog          import CEventEditDialog
from Events.EventVisitsModel import CEventVisitsModel
from Events.Utils import (checkAttachOnDate, checkPolicyOnDate, checkTissueJournalStatusByActions,
                          getEventEnableActionsBeyondEvent, getEventDuration, getEventShowTime,
                          getDeathDate, getEventPurposeId,
                          setActionPropertiesColumnVisible, specifyDiagnosis, CEventTypeDescription,
                          getEventVisitFinance, CFinanceType, getActionTypeIdListByFlatCode)
from Events.ActionProperty.BooleanActionPropertyValueType import CBooleanActionPropertyValueType
from Events.ActionProperty.TextActionPropertyValueType    import CTextActionPropertyValueType
from Events.ActionProperty.StringActionPropertyValueType  import CStringActionPropertyValueType
from Events.ActionProperty.IntegerActionPropertyValueType import CIntegerActionPropertyValueType
from Events.ActionProperty.DoubleStringActionPropertyValueType import CDoubleStringActionPropertyValueType
from Events.ActionProperty.DoubleActionPropertyValueType   import CDoubleActionPropertyValueType
from Events.ActionProperty.ConstructorActionPropertyValueType import CConstructorActionPropertyValueType
from Events.ActionProperty.NomenclatureActionPropertyValueType import CNomenclatureActionPropertyValueType
from Orgs.Orgs                       import selectOrganisation
from Orgs.PersonComboBoxEx           import CPersonFindInDocTableCol
from Orgs.OrgComboBox                import COrgInDocTableColEx
from Orgs.OrgStructureCol            import COrgStructureInDocTableCol
from Registry.AmbCardMixin           import getClientActions
from Registry.ClientEditDialog       import CClientEditDialog
from Registry.Utils import formatClientBanner, getClientInfo, preFillingActionRecordMSI, getClientSexAge
from Orgs.Utils                      import getOrgStructurePersonIdList
from Users.Rights                    import (
                                              urAdmin,
                                              urCopyPrevAction,
                                              urRegTabWriteRegistry,
                                              urRegTabReadRegistry
                                            )
from F088.F088ActionPropertiesCheckTable import CF088ActionPropertiesCheckTableModel

from F088.Ui_F0882022 import Ui_F0882022Dialog


tabNotesFieldNames = ['relegateOrg_id',
                      'relegatePerson_id',
                      'srcNumber',
                      'srcDate',
                      'note',
                      'externalId',
                      'assistant_id',
                      'curator_id',
                      'patientModel_id',
                      'cureType_id',
                      'cureMethod_id',
                      'isClosed',
                      'relative_id',
                      'expertiseDate',
                      'expert_id',
                      'org_id',
                      'setDate']


class CF0882022EditDialog(CItemEditorBaseDialog, Ui_F0882022Dialog):
    cdSaveNoClose = 4 # сохранить не закрывая

    def __init__(self, parent, isCreate=False):
        CItemEditorBaseDialog.__init__(self, parent, 'Action')
        self.isCreate = isCreate
        self.action = None
        self.eventId     = None
        self._eventExecDate = None
        self.clientType = CEventEditDialog.ctOther
        self.personSSFCache = {}
        self.eventTypeId = None
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
        self.nomenclatureSmnnUUIDCache = {}
        self.idx = 0
        self.domainPurposeDirectionMSI5 = []
        self.methodReceivingNotification19_3 = []
        self.domainIPRAResult27_4 = []
        self.domainIPRAResult27_5 = []
        self.isRelationRepresentativeSetClientId = False
        self.addModels('Visits', CEventVisitsModel(self))
        self.addModels('MembersMSIPerson', CMembersMSIPersonTableModel(self))
        self.addModels('TempInvalidYear', CTempInvalidYearTableModel(self))
        self.addModels('DiagnosisDisease_31_1', CDiagnosisDisease_31_1_TableModel(self, diagnosisTypeCode=u'51'))
        self.addModels('DiagnosisDisease_31_3', CDiagnosisDisease_31_TableModel(self, diagnosisTypeCode=u'52'))
        self.addModels('DiagnosisDisease_31_4', CDiagnosisDisease_31_TableModel(self, diagnosisTypeCode=u'53'))
        self.addModels('DiagnosisDisease_31_6', CDiagnosisDisease_31_TableModel(self, diagnosisTypeCode=u'54'))
        self.addModels('AmbCardStatusActionsAnamnesis', CAnamnesisActionsTableModel(self))
        self.addModels('AmbCardStatusActionPropertiesAnamnesis', CF088ActionPropertiesCheckTableModel(self))
        self.addModels('AmbCardStatusActions_29', CAmbCardDiagnosticsActionsCheckTableModel(self))
        self.addModels('AmbCardStatusActionProperties_29', CActionPropertiesTableModel(self))
        self.addModels('AboutMedicalExaminationsRequiredAction', CAboutMedicalExaminationsRequiredActionTableModel(self))
        self.addModels('AboutMedicalExaminationsRequiredProperties', CAboutMedicalExaminationsRequiredPropertiesTableModel(self))
        self.addModels('AmbCardDiagnosticActions_30', CAmbCardDiagnosticsActionsCheckTableModel(self))
        self.addModels('AmbCardDiagnosticActionProperties_30', CF088ActionPropertiesCheckTableModel(self))
        self.addModels('AddActions_30', CF088AddActions30InDocTableModel(self))
        self.addModels('AddActionProperties_30', CActionPropertiesTableModel(self))
        self.addModels('AssignedMedicament', CAssignedMedicamentActionsCheckTableModel(self))
        self.addModels('Medicament', CMedicamentActionsTableModel(self))
        self.addModels('Export', CEventExportTableModel(self))
        self.addModels('Export_FileAttach', CAdvancedExportTableModel(self))
        self.addModels('Export_VIMIS', CAdvancedExportTableModel(self))
        self.addObject('actEditClient', QtGui.QAction(u'Открыть регистрационную карточку', self))
        self.addObject('actPortal_Doctor', QtGui.QAction(u'Перейти на портал врача', self))
        self.addObject('actEditAction', QtGui.QAction(u'Редактировать Действие', self))
        self.addObject('actDeleteAction', QtGui.QAction(u'Удалить Действие', self))
        self.addObject('actShowAttachedToClientFiles', getAttachAction('Client_FileAttach',  self))
        self.addObject('btnPrint', getPrintButton(self, ''))
        self.addObject('btnAttachedFiles', CAttachButton(self, u'Прикреплённые файлы'))
        self.addObject('btnLoadPrevAction', QtGui.QPushButton(u'Копировать из предыдущего', self))
        self.addObject('mnuLoadPrevAction',  QtGui.QMenu(self))
        self.addObject('actAmbCardPrintStatusActionsAnamnesisDisease', QtGui.QAction(u'Преобразовать в текст и вставить в блок Анамнез заболевания', self))
        self.addObject('actAmbCardPrintStatusActionsAnamnesisLife',    QtGui.QAction(u'Преобразовать в текст и вставить в блок Анамнез жизни', self))
        self.addObject('actAmbCardPrintStatusActions',    QtGui.QAction(u'Преобразовать в текст и вставить в блок', self))
        self.addObject('actAmbCardPrintDiagnosticActions_30',QtGui.QAction(u'Вставить в блок Действия', self))
        self.addObject('actAmbCardPrintDiagnosticProperties_30',QtGui.QAction(u'Вставить в блок Свойства', self))
        self.addObject('actAssignedMedicamentAdd',QtGui.QAction(u'Добавить', self))
        self.addObject('actAboutMERPropertiesDeleteRows',        QtGui.QAction(u'Удалить строку', self))
        self.addObject('actStatusShowPropertyHistoryAnamnesis',   QtGui.QAction(u'Показать журнал значения свойства', self))
        self.addObject('actStatusShowPropertiesHistoryAnamnesis', QtGui.QAction(u'Показать журнал значения свойств...', self))
        self.addObject('actStatusShowPropertyHistory',    QtGui.QAction(u'Показать журнал значения свойства', self))
        self.addObject('actStatusShowPropertiesHistory',  QtGui.QAction(u'Показать журнал значения свойств...', self))
        self.addObject('actRequestDocumentDataFromCdaGen',QtGui.QAction(u'Показать документ', self))
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setWindowTitleEx(u'Мероприятие МСЭ')
        self.actionTypeIdListByMSE = self.getActionTypeIdListByMSE(flatCode=u'inspection_mse%')
        self.initNewDate()
        self.edtDirectionDate.canBeEmpty(True)
        self.edtEndDate.canBeEmpty(True)
        self.edtBegDate.canBeEmpty(True)
        self.isActionSave = False
        self.buttonBox.addButton(self.btnPrint, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnLoadPrevAction, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnAttachedFiles, QtGui.QDialogButtonBox.ActionRole)
        self.setModels(self.tblTempInvalidYear, self.modelTempInvalidYear, self.selectionModelTempInvalidYear)
        self.setModels(self.tblMembersMSIPerson, self.modelMembersMSIPerson, self.selectionModelMembersMSIPerson)
        self.setModels(self.tblDiagnosisDisease_31_1, self.modelDiagnosisDisease_31_1, self.selectionModelDiagnosisDisease_31_1)
        self.setModels(self.tblDiagnosisDisease_31_3, self.modelDiagnosisDisease_31_3, self.selectionModelDiagnosisDisease_31_3)
        self.setModels(self.tblDiagnosisDisease_31_4, self.modelDiagnosisDisease_31_4, self.selectionModelDiagnosisDisease_31_4)
        self.setModels(self.tblDiagnosisDisease_31_6, self.modelDiagnosisDisease_31_6, self.selectionModelDiagnosisDisease_31_6)
        self.setModels(self.tblAmbCardStatusActionsAnamnesis, self.modelAmbCardStatusActionsAnamnesis, self.selectionModelAmbCardStatusActionsAnamnesis)
        self.setModels(self.tblAmbCardStatusActionPropertiesAnamnesis, self.modelAmbCardStatusActionPropertiesAnamnesis, self.selectionModelAmbCardStatusActionPropertiesAnamnesis)
        self.setModels(self.tblAmbCardStatusActions_29, self.modelAmbCardStatusActions_29, self.selectionModelAmbCardStatusActions_29)
        self.setModels(self.tblAmbCardStatusActionProperties_29, self.modelAmbCardStatusActionProperties_29, self.selectionModelAmbCardStatusActionProperties_29)
        self.setModels(self.tblAmbCardDiagnosticActions_30, self.modelAmbCardDiagnosticActions_30, self.selectionModelAmbCardDiagnosticActions_30)
        self.setModels(self.tblAmbCardDiagnosticActionProperties_30, self.modelAmbCardDiagnosticActionProperties_30, self.selectionModelAmbCardDiagnosticActionProperties_30)
        self.setModels(self.tblAddActions_30, self.modelAddActions_30, self.selectionModelAddActions_30)
        self.setModels(self.tblAssignedMedicament, self.modelAssignedMedicament, self.selectionModelAssignedMedicament)
        self.setModels(self.tblMedicament, self.modelMedicament, self.selectionModelMedicament)
        self.setModels(self.tblAddActionProperties_30, self.modelAddActionProperties_30, self.selectionModelAddActionProperties_30)
        self.setModels(self.tblAboutMedicalExaminationsRequiredAction, self.modelAboutMedicalExaminationsRequiredAction, self.selectionModelAboutMedicalExaminationsRequiredAction)
        self.setModels(self.tblAboutMedicalExaminationsRequiredProperties, self.modelAboutMedicalExaminationsRequiredProperties, self.selectionModelAboutMedicalExaminationsRequiredProperties)
        self.setModels(self.tblExport, self.modelExport, self.selectionModelExport)
        self.setModels(self.tblExport_FileAttach, self.modelExport_FileAttach, self.selectionModelExport_FileAttach)
        self.setModels(self.tblExport_VIMIS, self.modelExport_VIMIS, self.selectionModelExport_VIMIS)
        self.tblAmbCardStatusActionsAnamnesis.createPopupMenu([self.actAmbCardPrintStatusActionsAnamnesisDisease, self.actAmbCardPrintStatusActionsAnamnesisLife])
        self.tblAmbCardStatusActions_29.createPopupMenu([self.actAmbCardPrintStatusActions])
        self.tblAmbCardDiagnosticActions_30.createPopupMenu([self.actAmbCardPrintDiagnosticActions_30, self.actEditAction, self.actDeleteAction])
        self.tblAssignedMedicament.createPopupMenu([self.actAssignedMedicamentAdd, ])
        self.tblAmbCardDiagnosticActionProperties_30.createPopupMenu([self.actAmbCardPrintDiagnosticProperties_30])
        self.txtClientInfoBrowser.actions.append(self.actEditClient)
        self.txtClientInfoBrowser.actions.append(self.actPortal_Doctor)
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
        self.tblExport.enableColsHide()
        self.tblExport.enableColsMove()
        self.actionTemplateCache = CActionTemplateCache(self, self.cmbPerson)
        action = QtGui.QAction(self)
        action.setShortcut('F3')
        self.addAction(action)
        self.modelTempInvalidYear.setEventEditor(self)
        self.modelMembersMSIPerson.setEventEditor(self)
        self.tabNotes.setEventEditor(self)
        self.modelDiagnosisDisease_31_1.setEventEditor(self)
        self.modelDiagnosisDisease_31_3.setEventEditor(self)
        self.modelDiagnosisDisease_31_4.setEventEditor(self)
        self.modelDiagnosisDisease_31_6.setEventEditor(self)
        self.tblTempInvalidYear.addPopupDelRow()
        self.tblMembersMSIPerson.addPopupDelRow()
        self.tblAboutMedicalExaminationsRequiredAction.addMoveRow()
        self.tblAboutMedicalExaminationsRequiredAction.addPopupDelRow()
        self.tblMedicament.addMoveRow()
        self.tblMedicament.addPopupDelRow()
        self.tblAboutMedicalExaminationsRequiredProperties.createPopupMenu([self.actAboutMERPropertiesDeleteRows])
#        self.tblDiagnosisDisease_31_1.addPopupDelRow()
        self.tblDiagnosisDisease_31_3.addPopupDelRow()
        self.tblDiagnosisDisease_31_4.addPopupDelRow()
        self.tblDiagnosisDisease_31_6.addPopupDelRow()
        self.tblDiagnosisDisease_31_6.setWordWrap(True)
        self.tblAddActions_30.addPopupAddRow()
        self.tblAddActions_30.addPopupDelRow()
        self.modifiableDiagnosisesMap = {}
        self.mapSpecialityIdToDiagFilter = {}
        self.mapMKBTraumaList = createMapCodeToRowIdx([row for row in [(u'S00 -T99.9')]]).keys()
        self.modelAmbCardStatusActionPropertiesAnamnesis.setReadOnly(True)
        self.modelAmbCardStatusActionProperties_29.setReadOnly(True)
        self.modelAmbCardDiagnosticActionProperties_30.setReadOnly(True)
        self.edtNomenclatureExpense35_1.setReadOnly(True)
        self.cmbClientIsLocatedOrg.setNameField('CONCAT(infisCode,\'| \', shortName)')
        self.edtTempInvalidDocumentElectronicNumber.installEventFilter(self)
        self.edtTempInvalidDocumentElectronicNumber.setCursorPosition(0)
        self.prepareActionTable(self.tblAmbCardStatusActionPropertiesAnamnesis, self.actStatusShowPropertyHistory, self.actStatusShowPropertiesHistory)
        self.prepareActionTable(self.tblAmbCardStatusActionProperties_29, self.actStatusShowPropertyHistory, self.actStatusShowPropertiesHistory)
        splAnamnesisIndex = self.splAnamnesis.indexOf(self.tabSpliterAnamnesis)
        self.splAnamnesis.setCollapsible(splAnamnesisIndex, False)
        splAnamnesisIndex2 = self.splAnamnesis.indexOf(self.tabAmbCardContentAnamnesis)
        self.splAnamnesis.setCollapsible(splAnamnesisIndex2, True)
        splStatusIndex = self.splStatus.indexOf(self.tabHealthClientDirectionMSI)
        self.splStatus.setCollapsible(splStatusIndex, False)
        splStatusIndex2 = self.splStatus.indexOf(self.tabAmbCardContent_29)
        self.splStatus.setCollapsible(splStatusIndex2, True)
        splInspectionIndex = self.splInspection.indexOf(self.tabInfoAboutMedicalExaminationsRequired)
        self.splInspection.setCollapsible(splInspectionIndex, False)
        splInspectionIndex2 = self.splInspection.indexOf(self.tabAmbCardInspection_30)
        self.splInspection.setCollapsible(splInspectionIndex2, True)
        self.createApplyButton()
        self.servicesURL = forceString(QtGui.qApp.getGlobalPreference('23:servicesURL'))
        self.tabWidget.setTabEnabled(self.tabWidget.indexOf(self.tabExtendedMSE), forceBool(self.servicesURL))
        self.connect(self.edtBegDate, SIGNAL('dateChanged(const QDate &)'), self.on_edtBegDate_dateChanged)
        self.connect(self.edtEndDate, SIGNAL('dateChanged(const QDate &)'), self.on_edtEndDate_dateChanged)
        self.tblAboutMedicalExaminationsRequiredAction.enableColsHide()
        self.tblAmbCardDiagnosticActions_30.enableColsHide()
        self.tblAddActions_30.enableColsHide()
        self.cmbAmbCardStatusGroup_29.setClassesVisible(True)
        self.cmbAmbCardDiagnosticGroup_30.setClassesVisible(True)
        self.cmbAmbCardStatusGroupAnamnesis.setClassesVisible(True)
        self.tblAssignedMedicament.enableColsHide()
        self.tblMedicament.enableColsHide()
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


    def timeoutAlert(self):
        self.timeoutFilter.disconnectAll()
        self.timeoutFilter.timerActivate(lambda: self.timeoutFilter.close(), 60000, False)
        if self.timeoutFilter.timeoutWindowAlert() == QtGui.QMessageBox.Cancel:
            self.timeoutFilter.disconnectAll()
            self.timeoutFilter.timerActivate(self.timeoutAlert)


    def getActionTypeIdListByMSE(self, flatCode = u'inspection_mse%'):
        return getActionTypeIdListByFlatCode(flatCode)


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


    def getOrganisationByMSI_45Filter(self):
        domain = None
        for propertyTypeName, propertyType in self.action.getType()._propertiesByName.items():
            shortName = trim(propertyType.shortName)
            if shortName == u'45':
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
        return db.joinAnd([domain, u'Organisation.isActive = 1'] if domain else [])


    def initNewDate(self):
        if self.isCreate:
            self.edtProtocolDateMSI.setDate(QDate())
            self.edtConsentReferralConductDateMSI.setDate(QDate())
            self.edtPrevMSI20_2.setDate(QDate())
            self.edtPrevMSI20_7.setDate(QDate())
            self.edtIPRADateMSI.setDate(QDate())
            self.edtRepresentativeDocumentDate.setDate(QDate())
            self.edtAdditionalDataRegistrationDate.setDate(QDate())
            self.edtAdditionalDataExaminationDate.setDate(QDate())


    def initNewData(self):
        if self.isCreate:
            self.on_cmbAnamnesis28_4_currentIndexChanged(0)


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
        begDate = self.edtBegDate.date()
        db = QtGui.qApp.db
        tableDiagnosis = db.table('Diagnosis')
        tableRbDiagnosticResult = db.table('rbDiagnosticResult')
        eventType = CEventTypeDescription.get(self.eventTypeId)
        recDiagResult = db.getRecordEx(tableRbDiagnosticResult,
                                       [tableRbDiagnosticResult['id'], tableRbDiagnosticResult['result_id']],
                                       tableRbDiagnosticResult['eventPurpose_id'].eq(eventType.purposeId))
        personId = self.cmbPerson.value()
        specialityId = None
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


    def escapeSymbols(self, s):
        return unicode(s).replace('<', '_').replace('>', '_').replace('"', '_').replace('\'', '_').replace('/', '_').replace('\\', '_').replace(':', '_')


    @pyqtSignature('bool')
    def on_chkCheckAge_30_toggled(self, checked):
        self.on_cmdAmbCardDiagnosticButtonBox_30_apply()


    @pyqtSignature('bool')
    def on_chkCheckMKB_30_toggled(self, checked):
        self.on_cmdAmbCardDiagnosticButtonBox_30_apply()


    @pyqtSignature('int')
    def on_cmbCheckMKB_30_currentIndexChanged(self, value):
        if self.chkCheckMKB_30.isChecked():
            self.on_cmdAmbCardDiagnosticButtonBox_30_apply()


    @pyqtSignature('bool')
    def on_chkAdditional_30_toggled(self, checked):
        self.on_cmdAmbCardDiagnosticButtonBox_30_apply()


    @pyqtSignature('')
    def on_actStatusShowPropertyHistoryAnamnesis_triggered(self):
        self.tblAmbCardStatusActionPropertiesAnamnesis.showHistory()


    @pyqtSignature('')
    def on_actStatusShowPropertiesHistoryAnamnesis_triggered(self):
        self.tblAmbCardStatusActionPropertiesAnamnesis.showHistoryEx()


    @pyqtSignature('')
    def on_tblAmbCardStatusActionsAnamnesis_popupMenuAboutToShow(self):
        notEmpty = self.modelAmbCardStatusActionsAnamnesis.rowCount() > 0
        self.actAmbCardPrintStatusActionsAnamnesisDisease.setEnabled(notEmpty)
        self.actAmbCardPrintStatusActionsAnamnesisLife.setEnabled(notEmpty)


    @pyqtSignature('')
    def on_actStatusShowPropertyHistory_triggered(self):
        self.tblAmbCardStatusActionProperties_29.showHistory()


    @pyqtSignature('')
    def on_actStatusShowPropertiesHistory_triggered(self):
        self.tblAmbCardStatusActionProperties_29.showHistoryEx()


    @pyqtSignature('')
    def on_tblAmbCardStatusActions_29_popupMenuAboutToShow(self):
        notEmpty = self.modelAmbCardStatusActions_29.rowCount() > 0
        self.actAmbCardPrintStatusActions.setEnabled(notEmpty)


    @pyqtSignature('')
    def on_tblAmbCardDiagnosticActions_30_popupMenuAboutToShow(self):
        notEmpty = self.modelAmbCardDiagnosticActions_30.rowCount() > 0
        self.actAmbCardPrintDiagnosticActions_30.setEnabled(notEmpty)
        isCurrentEvent = False
        indexAction = self.tblAmbCardDiagnosticActions_30.currentIndex()
        if indexAction.isValid():
            rowAction = indexAction.row()
            if rowAction >= 0 and rowAction < len(self.modelAmbCardDiagnosticActions_30.idList()):
                actionId = self.modelAmbCardDiagnosticActions_30._idList[rowAction]
                if actionId and self.eventId == self.modelAmbCardDiagnosticActions_30.eventIdDict.get(actionId, None):
                    isCurrentEvent = True
        self.actEditAction.setEnabled(notEmpty and isCurrentEvent)
        self.actDeleteAction.setEnabled(notEmpty and isCurrentEvent)


    @pyqtSignature('')
    def on_tblAssignedMedicament_popupMenuAboutToShow(self):
        notEmpty = self.modelAssignedMedicament.rowCount() > 0
        self.actAssignedMedicamentAdd.setEnabled(notEmpty)


    @pyqtSignature('')
    def on_tblAmbCardDiagnosticActionProperties_30_popupMenuAboutToShow(self):
        notEmpty = self.modelAmbCardDiagnosticActionProperties_30.rowCount() > 0
        self.actAmbCardPrintDiagnosticProperties_30.setEnabled(notEmpty)


    @pyqtSignature('')
    def on_tblAboutMedicalExaminationsRequiredProperties_popupMenuAboutToShow(self):
        notEmpty = self.modelAboutMedicalExaminationsRequiredProperties.rowCount() > 0
        self.actAboutMERPropertiesDeleteRows.setEnabled(notEmpty)


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


    def getSelectedAnamnesisActions(self, actionId, propertyIdList):
        actionDict = {}
        db = QtGui.qApp.db
        table = db.table('Action')
        if not propertyIdList:
            propertyIdList = self.modelAmbCardStatusActionPropertiesAnamnesis.getPropertyIdList()
        if actionId and propertyIdList:
            if actionId and actionId not in actionDict.keys():
                record = db.getRecordEx(table, '*', [table['id'].eq(actionId), table['deleted'].eq(0)])
                if record:
                    action = CAction(record=record)
                    if action:
                        endDate = forceDate(record.value('endDate'))
                        actionType = action.getType()
                        actionLine = [u'', u'']
                        valuePropertyList = []
                        actionLine[0] = unicode(endDate.toString('dd.MM.yyyy')) + u' ' + actionType.name + u': '
                        propertiesById = action.getPropertiesById()
                        properties = propertiesById.values()
                        properties.sort(key=lambda prop:prop._type.idx)
                        for prop in properties:
                            propRecord = prop.getRecord()
                            if propRecord:
                                propertyId = forceRef(propRecord.value('id'))
                                if propertyId in propertyIdList:
                                    type = prop.type()
                                    if prop.getValue() and not type.isJobTicketValueType():
                                        valuePropertyList.append(type.name + u' - ' + (forceString(prop.getText()) if not type.isBoolean() else (u'Да' if prop.getValue() else u'Нет')))
                        actionLine[1] = u'; '.join(val for val in valuePropertyList if val)
                        actionDict[actionId] = actionLine
        actionDictValues = actionDict.values()
        actionDictValues.sort(key=lambda x:x[0])
        return actionDictValues


    @pyqtSignature('')
    def on_actAmbCardPrintStatusActionsAnamnesisDisease_triggered(self):
        actionId = self.tblAmbCardStatusActionsAnamnesis.currentItemId()
        propertyIdList = self.modelAmbCardStatusActionPropertiesAnamnesis.getSelectedIdList()
        actionDictValues = self.getSelectedAnamnesisActions(actionId, propertyIdList)
        if actionDictValues:
            oldValue = self.edtAnamnesis24.toPlainText()
            oldValue = oldValue.replace('\0', '')
            newValue = u'\n'.join((val[1]) for val in actionDictValues if val)
            newValue = newValue.replace('\0', '')
            value = (oldValue + u'\n' + newValue) if oldValue else newValue
            value = value.replace('\0', '')
            self.edtAnamnesis24.setText(value)


    @pyqtSignature('')
    def on_actAmbCardPrintStatusActionsAnamnesisLife_triggered(self):
        actionId = self.tblAmbCardStatusActionsAnamnesis.currentItemId()
        propertyIdList = self.modelAmbCardStatusActionPropertiesAnamnesis.getSelectedIdList()
        actionDictValues = self.getSelectedAnamnesisActions(actionId, propertyIdList)
        if actionDictValues:
            oldValue = self.edtAnamnesis25.toPlainText()
            oldValue = oldValue.replace('\0', '')
            newValue = u'\n'.join((val[1]) for val in actionDictValues if val)
            newValue = newValue.replace('\0', '')
            value = (oldValue + u'\n' + newValue) if oldValue else newValue
            self.edtAnamnesis25.setText(value)


    @pyqtSignature('')
    def on_actAmbCardPrintStatusActions_triggered(self):
        selectedIdList = self.modelAmbCardStatusActions_29.getSelectedIdList()
        actionDictValues = self.getSelectedActions(selectedIdList)
        if actionDictValues:
            oldValue = self.edtHealthClientDirectionMSI.toPlainText()
            oldValue = oldValue.replace('\0', '')
            newValue = u'\n'.join((val[0] + val[1]) for val in actionDictValues if val)
            newValue = newValue.replace('\0', '')
            value = (oldValue + u'\n' + newValue) if oldValue else newValue
            self.edtHealthClientDirectionMSI.setText(value)


    def getPropertiesIdListToAction(self, actionId):
        propertyTypeIdList = []
        db = QtGui.qApp.db
        table = db.table('Action')
        if actionId:
            record = db.getRecordEx(table, '*', [table['id'].eq(actionId), table['deleted'].eq(0)])
            if record:
                action = CAction(record=record)
                if action:
                    propertiesById = action.getPropertiesById()
                    properties = propertiesById.values()
                    properties.sort(key=lambda prop:prop._type.idx)
                    for prop in properties:
                        type = prop.type()
                        if prop and prop.getValue():
                            valueType = type.getValueType()
                            if isinstance(valueType, (CTextActionPropertyValueType,
                                                      CStringActionPropertyValueType,
                                                      CIntegerActionPropertyValueType,
                                                      CDoubleStringActionPropertyValueType,
                                                      CDoubleActionPropertyValueType,
                                                      CBooleanActionPropertyValueType,
                                                      CConstructorActionPropertyValueType)):
                                recordProp = prop.getRecord()
                                if recordProp:
                                    propertyId = forceRef(recordProp.value('id'))
                                    if propertyId and propertyId not in propertyTypeIdList:
                                        propertyTypeIdList.append(propertyId)
        return propertyTypeIdList


    def updateAmbCardPrintDiagnosticActions_30Table(self):
        actionItems = self.modelAboutMedicalExaminationsRequiredAction.items()
        if len(actionItems) > 0:
            actionRow = 0
            actionIndex = self.tblAboutMedicalExaminationsRequiredAction.currentIndex()
            if actionIndex.isValid():
                actionRow = actionIndex.row()
            self.tblAboutMedicalExaminationsRequiredAction.setCurrentRow(actionRow)
        else:
            self.modelAboutMedicalExaminationsRequiredProperties.clearItems()
        self.on_cmdAmbCardDiagnosticButtonBox_30_apply()


    def deletedAmbCardPrintDiagnosticActions_30Table(self):
        self.resetAmbCardPrintDiagnosticActions_30Table()


    def resetAmbCardPrintDiagnosticActions_30Table(self):
        self.updateAmbCardPrintDiagnosticActions_30Table()
        self.modelAmbCardDiagnosticActionProperties_30.includeRows = {}
        self.modelAmbCardDiagnosticActions_30.includeItems = {}
        self.modelAmbCardDiagnosticActions_30.enableIdList = []
        self.modelAmbCardDiagnosticActions_30.actionsPropertiesRegistry = {}


    @pyqtSignature('')
    def on_actAboutMERPropertiesDeleteRows_triggered(self):
        selectIndexes = self.tblAboutMedicalExaminationsRequiredProperties.selectedIndexes()
        rows = []
        for selectIndex in selectIndexes:
            selectRow = selectIndex.row()
            if selectRow not in rows:
                rows.append(selectRow)
        if rows:
            currentActionId = -1
            for row in reversed(rows):
                actionId = self.modelAboutMedicalExaminationsRequiredProperties.removeRow(row)
                if actionId:
                    currentActionId = actionId
            index = self.tblAboutMedicalExaminationsRequiredAction.currentIndex()
            if index.isValid():
                actionRow = index.row()
            else:
                actionRow = self.modelAboutMedicalExaminationsRequiredAction.getRowToActionId(currentActionId)
            actionItems = self.modelAboutMedicalExaminationsRequiredAction.items()
            propertyItems = self.modelAboutMedicalExaminationsRequiredProperties.getItems()
            if len(propertyItems) == 0 and 0 <= actionRow < len(actionItems):
                self.modelAboutMedicalExaminationsRequiredProperties.clearItems()
                self.modelAboutMedicalExaminationsRequiredAction.removeRow(actionRow)
                for i, propertyId in enumerate(propertyItems):
                    self.modelAboutMedicalExaminationsRequiredProperties.removeRow(i)
                self.modelAboutMedicalExaminationsRequiredAction.reset()
            else:
                if 0 <= actionRow < len(actionItems) and hasattr(actionItems[actionRow], 'aboutMERProperties'):
                    self.modelAboutMedicalExaminationsRequiredAction.items()[actionRow].aboutMERProperties.setItems(propertyItems)
                    self.modelAboutMedicalExaminationsRequiredProperties.setItems(self.modelAboutMedicalExaminationsRequiredAction.items()[actionRow].aboutMERProperties.getItems())
                    self.tblAboutMedicalExaminationsRequiredAction.setCurrentRow(actionRow)
                else:
                    self.modelAboutMedicalExaminationsRequiredProperties.clearItems()
                    self.modelAboutMedicalExaminationsRequiredAction.reset()
            self.deletedAmbCardPrintDiagnosticActions_30Table()


    @pyqtSignature('')
    def on_actAssignedMedicamentAdd_triggered(self):
        selectedIdList = self.modelAssignedMedicament.getSelectedIdList()
        if not selectedIdList:
            return
        medicamentActionIdList = self.modelMedicament.getActionIdList()
        db = QtGui.qApp.db
        tableRBNomenclature = db.table('rbNomenclature')
        for selectedId in selectedIdList:
            if selectedId and selectedId not in medicamentActionIdList:
                nomenclatureId, actionPropertyId = self.modelAssignedMedicament.actionsPropertiesRegistry.get(selectedId, None)
                if nomenclatureId:
                    smnnUUID = self.nomenclatureSmnnUUIDCache.get(nomenclatureId, None)
                    if not smnnUUID:
                        tableEsklp_Smnn = db.table('esklp.Smnn')
                        tableESKLP_Klp = db.table('esklp.Klp')
                        queryTable = tableRBNomenclature.innerJoin(tableESKLP_Klp, tableESKLP_Klp['UUID'].eq(tableRBNomenclature['esklpUUID']))
                        queryTable = queryTable.innerJoin(tableEsklp_Smnn, tableEsklp_Smnn['id'].eq(tableESKLP_Klp['smnn_id']))
                        nomenclatureRecord = db.getRecordEx(queryTable, [tableEsklp_Smnn['UUID']], [tableRBNomenclature['id'].eq(nomenclatureId)])
                        smnnUUID = forceStringEx(nomenclatureRecord.value('UUID')) if nomenclatureRecord else None
                        if smnnUUID:
                            self.nomenclatureSmnnUUIDCache[nomenclatureId] = smnnUUID
                    if smnnUUID:
                        record = self.modelMedicament.getEmptyRecord()
                        record.setValue('master_id', toVariant(self.itemId()))
                        record.setValue('action_id', toVariant(selectedId))
                        record.setValue('actionPropertyNomenclature_id', toVariant(actionPropertyId))
                        record.setValue('smnnUUID', toVariant(smnnUUID))
                        actionRecord = self.modelAssignedMedicament.getItemToActionId(selectedId)
                        record.setValue('duration', toVariant(forceInt(actionRecord.value('duration')) if actionRecord else 0))
                        record.setValue('periodicity', toVariant(forceInt(actionRecord.value('periodicity')) if actionRecord else 0))
                        record.setValue('aliquoticity', toVariant(forceInt(actionRecord.value('aliquoticity')) if actionRecord else 0))
                        self.modelMedicament.addItem(record)
        self.modelMedicament.reset()
        self.updateAssignedMedicament(None)


    @pyqtSignature('')
    def on_actAmbCardPrintDiagnosticActions_30_triggered(self):
        selectedIdList = self.modelAmbCardDiagnosticActions_30.getSelectedIdList()
        aboutMERActionIdList = self.modelAboutMedicalExaminationsRequiredAction.getActionIdList()
        for selectedId in selectedIdList:
            if selectedId and selectedId not in aboutMERActionIdList:
                record = self.modelAboutMedicalExaminationsRequiredAction.getEmptyRecord()
                record.setValue('master_id', toVariant(self.itemId()))
                record.setValue('action_id', toVariant(selectedId))
                record.setValue('additional', toVariant(self.modelAmbCardDiagnosticActions_30.getBasicAdditional(selectedId)))
                record.aboutMERProperties = CAboutMedicalExaminationsRequiredPropertiesRegistry()
                actionsPropertiesRegistry = self.modelAmbCardDiagnosticActions_30.actionsPropertiesRegistry.get(selectedId, None)
                if actionsPropertiesRegistry:
                    actionsPropertyIdItems = actionsPropertiesRegistry.getItems()
                    if not actionsPropertyIdItems:
                        actionsPropertyIdItems = self.getPropertiesIdListToAction(selectedId)
                else:
                    actionsPropertyIdItems = self.getPropertiesIdListToAction(selectedId)
                    if actionsPropertyIdItems:
                        actionsPropertiesRegistry = CAmbCardDiagnosticsActionsPropertiesRegistry()
                        actionsPropertiesRegistry.addItems(actionsPropertyIdItems)
                        self.modelAmbCardDiagnosticActions_30.actionsPropertiesRegistry[selectedId] = actionsPropertiesRegistry
                for actionsPropertyId in actionsPropertyIdItems:
                    record.aboutMERProperties.addItem(self.itemId(), selectedId, actionsPropertyId)
                #self.modelAboutMedicalExaminationsRequiredAction.addRecord(record)
                self.modelAboutMedicalExaminationsRequiredAction.addItem(record)
        row = len(self.modelAboutMedicalExaminationsRequiredAction.items())-1
        if row >= 0 and row < len(self.modelAboutMedicalExaminationsRequiredAction.items()):
            self.modelAboutMedicalExaminationsRequiredAction.reset()
            self.tblAboutMedicalExaminationsRequiredAction.setCurrentRow(row)
        else:
            self.modelAboutMedicalExaminationsRequiredAction.reset()
        self.deletedAmbCardPrintDiagnosticActions_30Table()


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_modelAmbCardDiagnosticActionProperties_30_dataChanged(self, topLeft, bottomRight):
        indexAction = self.tblAmbCardDiagnosticActions_30.currentIndex()
        if indexAction.isValid():
            rowAction = indexAction.row()
            if rowAction >= 0 and rowAction < len(self.modelAmbCardDiagnosticActions_30.idList()):
                indexProperty = topLeft
                if indexProperty.isValid():
                    columnProperty = indexProperty.column()
                    if columnProperty == 0:
                        rowProperty = indexProperty.row()
                        if 0 <= rowProperty < len(self.modelAmbCardDiagnosticActionProperties_30.propertyTypeList):
                            isChecked = self.modelAmbCardDiagnosticActionProperties_30.includeRows[rowProperty]
                            actionId = self.modelAmbCardDiagnosticActions_30._idList[rowAction]
                            actionsPropertiesRegistry = self.modelAmbCardDiagnosticActions_30.actionsPropertiesRegistry.get(actionId, None)
                            if not actionsPropertiesRegistry:
                                actionsPropertiesRegistry = CAmbCardDiagnosticsActionsPropertiesRegistry()
                            property = self.modelAmbCardDiagnosticActionProperties_30.getProperty(rowProperty)
                            if property:
                                record = property.getRecord()
                                if record:
                                    propertyId = forceRef(record.value('id'))
                                    if propertyId:
                                        if bool(isChecked):
                                            actionsPropertiesRegistry.addItem(propertyId)
                                        else:
                                            actionsPropertiesRegistry.removeItem(propertyId)
                                        self.modelAmbCardDiagnosticActions_30.includeItems[actionId] = self.modelAmbCardDiagnosticActionProperties_30.includeRows
                                        self.modelAmbCardDiagnosticActions_30.actionsPropertiesRegistry[actionId] = actionsPropertiesRegistry
                                        if actionsPropertiesRegistry and len(actionsPropertiesRegistry.getItems()) > 0:
                                            self.modelAmbCardDiagnosticActions_30.setData(indexAction, QVariant(Qt.Checked), role=Qt.CheckStateRole)
                                        else:
                                            self.modelAmbCardDiagnosticActions_30.setData(indexAction, QVariant(Qt.Unchecked), role=Qt.CheckStateRole)


    @pyqtSignature('')
    def on_actAmbCardPrintDiagnosticProperties_30_triggered(self):
        selectedIdList = self.modelAmbCardDiagnosticActionProperties_30.getSelectedIdList()
        aboutMERActionIdList = self.modelAboutMedicalExaminationsRequiredAction.getActionIdList()
        aboutMERPropertyIdList = self.modelAboutMedicalExaminationsRequiredProperties.getPropertyIdList()
        currentActionId = self.modelAmbCardDiagnosticActionProperties_30.getCurrentActionId()
        if not currentActionId:
            return
        recordAction = None
        selectedPropertyRows = self.modelAmbCardDiagnosticActionProperties_30.getSelectedPropertyRows()
        for actionsPropertyId in selectedIdList:
            if actionsPropertyId and actionsPropertyId not in aboutMERPropertyIdList:
                record = self.modelAboutMedicalExaminationsRequiredProperties.getEmptyRecordEx(self.itemId(), currentActionId, actionsPropertyId)
                if currentActionId not in aboutMERActionIdList:
                    if not recordAction:
                        recordAction = self.modelAboutMedicalExaminationsRequiredAction.getEmptyRecord()
                        recordAction.setValue('master_id', toVariant(self.itemId()))
                        recordAction.setValue('action_id', toVariant(currentActionId))
                        recordAction.aboutMERProperties = CAboutMedicalExaminationsRequiredPropertiesRegistry()
                else:
                    recordAction = self.modelAboutMedicalExaminationsRequiredAction.getItemToActionId(currentActionId)
                if recordAction:
                    if not recordAction.aboutMERProperties:
                        recordAction.aboutMERProperties = CAboutMedicalExaminationsRequiredPropertiesRegistry()
                    if actionsPropertyId not in recordAction.aboutMERProperties.getPropertyIdList():
                        recordAction.aboutMERProperties.addItem(self.itemId(), currentActionId, actionsPropertyId)
                        self.modelAboutMedicalExaminationsRequiredProperties.addItem(record)
                        propertyRow = selectedPropertyRows.get(actionsPropertyId, -1)
                        if propertyRow >= 0 and propertyRow < len(self.modelAmbCardDiagnosticActionProperties_30.includeRows.keys()):
                            self.modelAmbCardDiagnosticActionProperties_30.includeRows[propertyRow] = False
                            self.modelAmbCardDiagnosticActions_30.includeItems[currentActionId] = self.modelAmbCardDiagnosticActionProperties_30.includeRows
                            actionsPropertiesRegistry = self.modelAmbCardDiagnosticActions_30.actionsPropertiesRegistry.get(currentActionId, None)
                            if actionsPropertiesRegistry and actionsPropertyId in actionsPropertiesRegistry.getItems():
                                actionsPropertiesRegistry.removeItem(actionsPropertyId)
                                self.modelAmbCardDiagnosticActions_30.actionsPropertiesRegistry[currentActionId] = actionsPropertiesRegistry
                        if currentActionId in self.modelAmbCardDiagnosticActions_30.enableIdList and not self.modelAmbCardDiagnosticActionProperties_30.getSelectedIdList():
                            self.modelAmbCardDiagnosticActions_30.enableIdList.remove(currentActionId)
        if recordAction:
            if currentActionId not in aboutMERActionIdList:
                self.modelAboutMedicalExaminationsRequiredAction.addRecord(recordAction)
                #self.modelAboutMedicalExaminationsRequiredAction.addItem(recordAction)
            rowToActionId = self.modelAboutMedicalExaminationsRequiredAction.getRowToActionId(currentActionId)
            if rowToActionId >= 0 and rowToActionId < len(self.modelAboutMedicalExaminationsRequiredAction.items()):
                if currentActionId in aboutMERActionIdList:
                    self.modelAboutMedicalExaminationsRequiredAction.items()[rowToActionId] = recordAction
                self.modelAboutMedicalExaminationsRequiredAction.reset()
                self.tblAboutMedicalExaminationsRequiredAction.setCurrentRow(rowToActionId)
            else:
                self.modelAboutMedicalExaminationsRequiredAction.reset()
        else:
            self.modelAboutMedicalExaminationsRequiredProperties.reset()
            self.updateAboutMedicalExaminationsRequiredActionProperties(self.modelAboutMedicalExaminationsRequiredAction.index(0, 0), self.tblAboutMedicalExaminationsRequiredProperties, actionId=currentActionId)
        self.updateAmbCardPrintDiagnosticActions_30Table()


    def on_actionAmountChanged(self, value):
        self.edtAmount.setValue(value)


    def setEventDate(self, date):
        eventRecord = self._getEventRecord()
        if eventRecord:
            execDate = forceDate(eventRecord.value('execDate'))
            if not execDate:
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
            self.isActionSave = False
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
        self.setPropertyDomainWidget(self.cmbRepresentativeDocumentName, u'17.2.1', isNotDefined=False)
        self.setPropertyDomainWidget(self.cmbClientMilitaryDuty, u'10', isNotDefined=False)
        self.setPropertyDomainWidget(self.cmbClientIsLocated, u'13', isNotDefined=False)
        self.setPropertyDomainWidget(self.cmbFormMedicalCare, u'18.3', isNotDefined=False)
        self.setPropertyDomainWidget(self.cmbTypeMedicalCare, u'18.4', isNotDefined=False)
        self.setPropertyDomainWidget(self.cmbConditionsMedicalCare, u'18.5', isNotDefined=False)
        self.setPropertyDomainWidget(self.cmbPreferredFormHolding, u'19.2', isNotDefined=False)
        # self.setPropertyDomainWidget(self.cmbMethodReceivingNotification, u'19.3', isNotDefined=False)
        self.setPropertyDomainWidget(self.cmbPrevMSI20_1, u'20.1', isNotDefined=False)
        self.setPropertyDomainWidget(self.cmbPrevMSI20_1_1, u'20.1.1', isNotDefined=False)
        self.setPropertyDomainWidget(self.cmbPrevMSI20_1_2, u'20.1.2', isNotDefined=False)
        self.setPropertyDomainWidget(self.cmbPrevMSI20_3, u'20.3', isNotDefined=False)
        self.setPropertyDomainWidget(self.cmbPrevMSI20_4, u'20.4', isNotDefined=False)
        self.setPropertyDomainWidget(self.cmbPrevMSI20_6, u'20.6', isNotDefined=False)
        self.setPropertyDomainWidget(self.cmbAnamnesis28_4, u'28.4', isNotDefined=False)
        self.setPropertyDomainWidget(self.cmbClinicalPrognosis, u'32', isNotDefined=False)
        self.setPropertyDomainWidget(self.cmbRehabilitationPotential, u'33', isNotDefined=False)
        self.setPropertyDomainWidget(self.cmbRehabilitationPrognosis, u'34', isNotDefined=False)
        self.setPropertyDomainWidget(self.cmbAdditionalDataResultMSI, u'48', isNotDefined=False)
        self.setPropertyDomainWidget(self.cmbAdditionalDataDisabilityGroup, u'49', isNotDefined=False)
        domain5, defaultValue5 = self.getPropertyDomain(u'5')
        self.domainPurposeDirectionMSI5 = domain5.split(u',')
        domain19_3, defaultValue19_3 = self.getPropertyDomain(u'19.3')
        self.methodReceivingNotification19_3 = domain19_3.split(u',')
        domain27_4, defaultValue27_4 = self.getPropertyDomain(u'27.4')
        self.domainIPRAResult27_4 = domain27_4.split(u',')
        domain27_5, defaultValue27_5 = self.getPropertyDomain(u'27.5')
        self.domainIPRAResult27_5 = domain27_5.split(u',')
        self.cmbOrganisationByMSI_45.setGlobalFilter(self.getOrganisationByMSI_45Filter())


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
        cond = [tableAT['id'].eq(self.actionTypeId), tableAT['deleted'].eq(0),
                tableAPT['shortName'].like(propertyShortName), tableAPT['deleted'].eq(0)]
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
        if index == 3:  # Анамнез
            self.on_cmdAmbCardStatusButtonBoxAnamnesis_reset()
            self.on_cmdAmbCardStatusButtonBoxAnamnesis_apply()
        if index == 6:  # Статус (п.29)
            self.on_cmdAmbCardStatusButtonBox_29_reset()
            self.on_cmdAmbCardStatusButtonBox_29_apply()
        if index == 7:  # Обследование (п.30)
            self.on_cmdAmbCardDiagnosticButtonBox_30_reset()
            self.on_cmdAmbCardDiagnosticButtonBox_30_apply()
            self.modelAddActions_30.setClientInfo(self.clientId, self.clientSex, self.clientAge)
            self.modelAddActions_30.setEventTypeId(self.eventTypeId)
            MKBList = [[forceStringEx(self.action.getRecord().value('MKB'))]]
            MKBList.append(self.getMKBDiagnostics(self.modelDiagnosisDisease_31_3.items()))
            MKBList.append(self.getMKBDiagnostics(self.modelDiagnosisDisease_31_4.items()))
            MKBList.append(self.getMKBDiagnostics(self.modelDiagnosisDisease_31_6.items()))
            self.modelAddActions_30.setMKBList(MKBList)
        if index == 15:  # amb card page
            self.tabAmbCard.resetWidgets()


    def getMKBDiagnostics(self, items):
        MKBList = []
        for item in items:
            MKB = forceStringEx(item.value('MKB'))
            if MKB and MKB not in MKBList:
                MKBList.append(MKB)
        return MKBList


    @pyqtSignature('int')
    def on_tabAmbCardInspection_30_currentChanged(self, index):
        widget = self.tabWidget.widget(index)
        if widget is not None:
            focusProxy = widget.focusProxy()
            if focusProxy:
                focusProxy.setFocus(Qt.OtherFocusReason)
        if index == 0: # Обследование (п.30)
            self.on_cmdAmbCardDiagnosticButtonBox_30_reset()
            self.on_cmdAmbCardDiagnosticButtonBox_30_apply()
        self.modelAddActions_30.setClientInfo(self.clientId, self.clientSex, self.clientAge)
        self.modelAddActions_30.setEventTypeId(self.eventTypeId)
        MKBList = [[forceStringEx(self.action.getRecord().value('MKB'))]]
        MKBList.append(self.getMKBDiagnostics(self.modelDiagnosisDisease_31_3.items()))
        MKBList.append(self.getMKBDiagnostics(self.modelDiagnosisDisease_31_4.items()))
        MKBList.append(self.getMKBDiagnostics(self.modelDiagnosisDisease_31_6.items()))
        self.modelAddActions_30.setMKBList(MKBList)


    def selectAmbCardActions(self, filter, classCode, order, fieldName):
        return getClientActions(self.clientId, filter, classCode, order, fieldName)


    def getAmbCardFilter(self, edtBegDate, edtEndDate, cmbGroup, edtOffice, cmbOrgStructure):
        filter = {}
        filter['begDate'] = edtBegDate.date()
        filter['endDate'] = edtEndDate.date()
        filter['actionGroupId'] = cmbGroup.value()
        if not filter['actionGroupId']:
            filter['class'] = cmbGroup.getClass()
        filter['office'] = forceString(edtOffice.text())
        filter['orgStructureId'] = cmbOrgStructure.value()
        filter['status'] = CActionStatus.finished
        return filter


    def resetAmbCardFilter(self, edtBegDate, edtEndDate, cmbGroup, edtOffice, cmbOrgStructure):
        edtBegDate.setDate(QDate())
        edtEndDate.setDate(QDate())
        cmbGroup.setValue(None)
        edtOffice.setText('')
        cmbOrgStructure.setValue(None)


    @pyqtSignature('QAbstractButton*')
    def on_btnAmbCardStatusButtonBoxAnamnesis_clicked(self, button):
        buttonCode = self.btnAmbCardStatusButtonBoxAnamnesis.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.on_cmdAmbCardStatusButtonBoxAnamnesis_apply()
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.on_cmdAmbCardStatusButtonBoxAnamnesis_reset()


    @pyqtSignature('QAbstractButton*')
    def on_btnAmbCardStatusButtonBox_29_clicked(self, button):
        buttonCode = self.btnAmbCardStatusButtonBox_29.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.on_cmdAmbCardStatusButtonBox_29_apply()
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.on_cmdAmbCardStatusButtonBox_29_reset()


    @pyqtSignature('QAbstractButton*')
    def on_btnAmbCardDiagnosticButtonBox_30_clicked(self, button):
        buttonCode = self.btnAmbCardDiagnosticButtonBox_30.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.on_cmdAmbCardDiagnosticButtonBox_30_apply()
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.on_cmdAmbCardDiagnosticButtonBox_30_reset()


    def on_cmdAmbCardDiagnosticButtonBox_30_reset(self):
        self.resetAmbCardFilter(self.edtAmbCardDiagnosticBegDate_30,
                                self.edtAmbCardDiagnosticEndDate_30,
                                self.cmbAmbCardDiagnosticGroup_30,
                                self.edtAmbCardDiagnosticOffice_30,
                                self.cmbAmbCardDiagnosticOrgStructure_30
                                )


    def on_cmdAmbCardDiagnosticButtonBox_30_apply(self):
        filter = self.getAmbCardFilter(
                        self.edtAmbCardDiagnosticBegDate_30,
                        self.edtAmbCardDiagnosticEndDate_30,
                        self.cmbAmbCardDiagnosticGroup_30,
                        self.edtAmbCardDiagnosticOffice_30,
                        self.cmbAmbCardDiagnosticOrgStructure_30
                        )
        self.updateAmbCardDiagnostic_30(filter)
        self.focusAmbCardDiagnosticActions_30()


    def getActionTypeClassListDescendants(self, actionTypeId, classList_=None):
        db = QtGui.qApp.db
        tableActionType = db.table('ActionType')
        result = set([actionTypeId])
        parents = [actionTypeId]
        if actionTypeId and classList_ is None:
            record = db.getRecordEx(tableActionType, [tableActionType['class']], [tableActionType['id'].eq(actionTypeId), tableActionType['deleted'].eq(0)])
            classList_ = [forceInt(record.value('class'))] if record else None
        if classList_:
            classCond = tableActionType['class'].inlist(classList_)
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


    def getClientActions_30(self, clientId, filter, classCodeList, order = ['Action.endDate DESC', 'Action.id'], fieldName = None):
        db = QtGui.qApp.db
        tableAction = db.table('Action')
        tableActionType = db.table('ActionType')
        tableEvent = db.table('Event')
        tableActionTypeIdentification = db.table('ActionType_Identification')
        tableRBAccountingSystem = db.table('rbAccountingSystem')
        tableEGISZ = db.table('rbMedicalExaminationsMSE').alias('tableEGISZ')
        queryTable = tableAction
        queryTable = queryTable.innerJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))
        queryTable = queryTable.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
        queryTable = queryTable.innerJoin(tableActionTypeIdentification, tableActionTypeIdentification['master_id'].eq(tableActionType['id']))
        queryTable = queryTable.innerJoin(tableRBAccountingSystem, tableRBAccountingSystem['id'].eq(tableActionTypeIdentification['system_id']))
        queryTable = queryTable.innerJoin(tableEGISZ, tableEGISZ['NMU_code'].eq(tableActionTypeIdentification['value']))
        if fieldName in [u'setPerson_id', u'person_id']:
            tableSPWS = db.table('vrbPersonWithSpeciality')
            queryTable = queryTable.leftJoin(tableSPWS, tableSPWS['id'].eq(tableAction[fieldName]))
        cond = [tableAction['deleted'].eq(0),
                tableEvent['deleted'].eq(0),
                tableEvent['client_id'].eq(clientId),
                tableActionTypeIdentification['deleted'].eq(0),
                tableRBAccountingSystem['urn'].eq(u'urn:oid:1.2.643.5.1.13.13.99.2.857')
                ]
        if classCodeList:
            cond.append(tableActionType['class'].inlist(classCodeList))
        if self.chkCheckAge_30.isChecked():
            years = self.clientAge[3] if (self.clientAge and len(self.clientAge) == 4) else None
            if years is not None:
                if years >= 18:
                    cond.append(tableEGISZ['SECTION'].eq(1))
                else:
                    cond.append(tableEGISZ['SECTION'].eq(2))
#        MKB = forceStringEx(self.action.getRecord().value('MKB')) if self.action else None
        MKBList = []
        if self.chkCheckMKB_30.isChecked():
            MKBListTotal = [[forceStringEx(self.action.getRecord().value('MKB'))]]
            MKBListTotal.append(self.getMKBDiagnostics(self.modelDiagnosisDisease_31_3.items()))
            MKBListTotal.append(self.getMKBDiagnostics(self.modelDiagnosisDisease_31_4.items()))
            MKBListTotal.append(self.getMKBDiagnostics(self.modelDiagnosisDisease_31_6.items()))
            if MKBListTotal:
                MKBList = MKBListTotal[self.cmbCheckMKB_30.currentIndex()]
                condMKB = []
                for MKB in MKBList:
                    condMKB.append(tableEGISZ['MKB'].contain(MKB))
                    condMKB.append(tableEGISZ['MKB'].contain(MKB[:3] if len(MKB) >= 3 else MKB))
                condMKB.extend([tableEGISZ['MKB'].eq(''), tableEGISZ['MKB'].position('-')])
                cond.append(db.joinOr(condMKB))
        aboutMERActionItems = self.modelAboutMedicalExaminationsRequiredAction.items()
        aboutActionIdList = []
        for aboutMERActionItem in aboutMERActionItems:
            if aboutMERActionItem.aboutMERProperties:
                actionsPropertyIdItems = aboutMERActionItem.aboutMERProperties.getItems()
                selectedId = forceRef(aboutMERActionItem.value('action_id'))
                if not actionsPropertyIdItems:
                    if selectedId and selectedId not in aboutActionIdList:
                        aboutActionIdList.append(selectedId)
                else:
                    actionsPropertyIdList = []
                    for actionsPropertyIdItem in actionsPropertyIdItems:
                        actionsPropertyId = forceRef(actionsPropertyIdItem.value('actionProperty_id'))
                        if actionsPropertyId and actionsPropertyId not in actionsPropertyIdList:
                            actionsPropertyIdList.append(actionsPropertyId)
                    propertiesIdListToAction = self.getPropertiesIdListToAction(selectedId)
                    if len(propertiesIdListToAction) == len(actionsPropertyIdList):
                        if selectedId and selectedId not in aboutActionIdList:
                            aboutActionIdList.append(selectedId)
        if aboutActionIdList:
            cond.append(tableAction['id'].notInlist(aboutActionIdList))
        serviceType = filter.get('serviceType', None)
        if serviceType is not None:
            cond.append(tableActionType['serviceType'].eq(serviceType))
        begDate = filter.get('begDate', None)
        if begDate:
            cond.append(tableAction['endDate'].ge(begDate))
        endDate = filter.get('endDate', None)
        if endDate:
            cond.append(tableAction['endDate'].le(endDate))
        actionGroupId = filter.get('actionGroupId', None)
        if actionGroupId:
            cond.append(tableAction['actionType_id'].inlist(self.getActionTypeClassListDescendants(actionGroupId, classCodeList)))
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
            actionIdList = []
            eventIdDict = {}
            isMKB = True
            QtGui.QApplication.setOverrideCursor(QtGui.QCursor(Qt.WaitCursor))
            cols = [tableAction['id'],
                    tableAction['event_id'],
                    tableAction['additional'],
                    tableEGISZ['MKB']
                    ]
            records = db.getRecordList(queryTable, cols, cond, order)
            for record in records:
                isAdditional = False
                additional = forceInt(record.value('additional'))
                if self.chkAdditional_30.isChecked():
                    isAdditional = additional == 2
                else:
                    isAdditional = additional != 2
                if isAdditional:
                    if self.chkCheckMKB_30.isChecked():
                        mkbRecord = forceStringEx(record.value('MKB'))
                        mkbList = mkbRecord.split(';')
                        for MKB in MKBList:
                            if len(mkbList) >= 1:
                                for diagList in mkbList:
                                    isMKB = False
                                    diagSplit = diagList.split('-')
                                    if len(diagSplit) == 2:
                                        if trim(diagSplit[0]) <= MKB and MKB <= trim(diagSplit[1]):
                                            isMKB = True
                                            break
                                        elif len(MKB) >= 3:
                                            if (len(trim(diagSplit[0])) <= 3 and trim(diagSplit[0]) <= MKB[:3]) or (len(trim(diagSplit[0])) > 3 and trim(diagSplit[0]) <= MKB):
                                                if (len(trim(diagSplit[1])) <= 3 and MKB[:3] <= trim(diagSplit[1])) or (len(trim(diagSplit[1])) > 3 and MKB <= trim(diagSplit[1])):
                                                    isMKB = True
                                                    break
                                    elif len(diagSplit) == 1:
                                        if MKB in trim(diagSplit[0]):
                                            isMKB = True
                                            break
                                        elif len(MKB) >= 3 and len(trim(diagSplit[0])) <= 3:
                                            if MKB[:3] in trim(diagSplit[0]):
                                                isMKB = True
                                                break
                            else:
                                isMKB = True
                            if isMKB:
                                break
                    if isMKB:
                        actionId = forceRef(record.value('id'))
                        if actionId and actionId not in actionIdList:
                            actionIdList.append(actionId)
                            eventId = forceRef(record.value('event_id'))
                            eventIdDict[actionId] = eventId
        finally:
            QtGui.QApplication.restoreOverrideCursor()
        return actionIdList, eventIdDict


    def selectAmbCardActions_30(self, filter, classCodeList, order, fieldName):
        return self.getClientActions_30(self.clientId, filter, classCodeList, order, fieldName)


    def updateAmbCardDiagnostic_30(self, filter, posToId=None, fieldName=None):
        self.__ambCardDiagnosticFilter = filter
        order = self.tblAmbCardDiagnosticActions_30.order() if self.tblAmbCardDiagnosticActions_30.order() else ['Action.endDate DESC', 'id']
        actionIdList, eventIdDict = self.selectAmbCardActions_30(filter, [], order, fieldName)
        self.tblAmbCardDiagnosticActions_30.setIdList(actionIdList, posToId)
        self.modelAmbCardDiagnosticActions_30.setEventIdDict(eventIdDict)
        self.modelAmbCardDiagnosticActions_30.setEventId(self.eventId)


    def focusAmbCardDiagnosticActions_30(self):
        self.tblAmbCardDiagnosticActions_30.setFocus(Qt.TabFocusReason)


    def on_cmdAmbCardStatusButtonBoxAnamnesis_reset(self):
        self.resetAmbCardFilter(self.edtAmbCardStatusBegDateAnamnesis,
                                self.edtAmbCardStatusEndDateAnamnesis,
                                self.cmbAmbCardStatusGroupAnamnesis,
                                self.edtAmbCardStatusOfficeAnamnesis,
                                self.cmbAmbCardStatusOrgStructureAnamnesis
                                )


    def on_cmdAmbCardStatusButtonBoxAnamnesis_apply(self):
        filter = self.getAmbCardFilter(
                        self.edtAmbCardStatusBegDateAnamnesis,
                        self.edtAmbCardStatusEndDateAnamnesis,
                        self.cmbAmbCardStatusGroupAnamnesis,
                        self.edtAmbCardStatusOfficeAnamnesis,
                        self.cmbAmbCardStatusOrgStructureAnamnesis
                        )
        self.updateAmbCardStatusAnamnesis(filter)
        self.focusAmbCardStatusActionsAnamnesis()


    def updateAmbCardStatusAnamnesis(self, filter, posToId=None, fieldName=None):
        self.__ambCardStatusFilter = filter
        order = self.tblAmbCardStatusActionsAnamnesis.order() if self.tblAmbCardStatusActionsAnamnesis.order() else ['Action.endDate DESC', 'id']
        self.tblAmbCardStatusActionsAnamnesis.setIdList(self.selectAmbCardActions(filter, [0, 3], order, fieldName), posToId)


    def focusAmbCardStatusActionsAnamnesis(self):
        self.tblAmbCardStatusActionsAnamnesis.setFocus(Qt.TabFocusReason)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelAmbCardStatusActionsAnamnesis_currentRowChanged(self, current, previous):
        self.updateAmbCardAnamnesisPropertiesTable(current, self.tblAmbCardStatusActionPropertiesAnamnesis, previous)


    def on_cmdAmbCardStatusButtonBox_29_reset(self):
        self.resetAmbCardFilter(self.edtAmbCardStatusBegDate_29,
                                self.edtAmbCardStatusEndDate_29,
                                self.cmbAmbCardStatusGroup_29,
                                self.edtAmbCardStatusOffice_29,
                                self.cmbAmbCardStatusOrgStructure_29
                                )


    def on_cmdAmbCardStatusButtonBox_29_apply(self):
        filter = self.getAmbCardFilter(
                        self.edtAmbCardStatusBegDate_29,
                        self.edtAmbCardStatusEndDate_29,
                        self.cmbAmbCardStatusGroup_29,
                        self.edtAmbCardStatusOffice_29,
                        self.cmbAmbCardStatusOrgStructure_29
                        )
        self.updateAmbCardStatus_29(filter)
        self.focusAmbCardStatusActions_29()


    def updateAmbCardStatus_29(self, filter, posToId=None, fieldName=None):
        self.__ambCardStatusFilter = filter
        order = self.tblAmbCardStatusActions_29.order() if self.tblAmbCardStatusActions_29.order() else ['Action.endDate DESC', 'id']
        self.tblAmbCardStatusActions_29.setIdList(self.selectAmbCardActions(filter, [0, 3], order, fieldName), posToId)


    def focusAmbCardStatusActions_29(self):
        self.tblAmbCardStatusActions_29.setFocus(Qt.TabFocusReason)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_modelDiagnosisDisease_31_1_dataChanged(self, topLeft, bottomRight):
        index = self.tblDiagnosisDisease_31_1.currentIndex()
        if index.isValid():
            row = index.row()
            if row == 0:
                self.tblDiagnosisDisease_31_1.resizeColumnToContents(self.tblDiagnosisDisease_31_1.columnHint)
#                self.tblDiagnosisDisease_31_1.resizeRowToContents(row)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_modelDiagnosisDisease_31_3_dataChanged(self, topLeft, bottomRight):
        index = self.tblDiagnosisDisease_31_3.currentIndex()
        if index.isValid():
            row = index.row()
            if row >= 0 and row < len(self.modelDiagnosisDisease_31_3.items()):
                self.tblDiagnosisDisease_31_3.resizeColumnToContents(self.tblDiagnosisDisease_31_3.columnHint)
                self.tblDiagnosisDisease_31_3.resizeRowToContents(row)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_modelDiagnosisDisease_31_4_dataChanged(self, topLeft, bottomRight):
        index = self.tblDiagnosisDisease_31_4.currentIndex()
        if index.isValid():
            row = index.row()
            if row >= 0 and row < len(self.modelDiagnosisDisease_31_4.items()):
                self.tblDiagnosisDisease_31_4.resizeColumnToContents(self.tblDiagnosisDisease_31_4.columnHint)
                self.tblDiagnosisDisease_31_4.resizeRowToContents(row)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_modelDiagnosisDisease_31_6_dataChanged(self, topLeft, bottomRight):
        index = self.tblDiagnosisDisease_31_6.currentIndex()
        if index.isValid():
            row = index.row()
            if row >= 0 and row < len(self.modelDiagnosisDisease_31_6.items()):
                self.tblDiagnosisDisease_31_6.resizeColumnToContents(self.tblDiagnosisDisease_31_6.columnHint)
                self.tblDiagnosisDisease_31_6.resizeRowToContents(row)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelAddActions_30_currentRowChanged(self, current, previous):
        self.updateAddActions30PropertiesTable(current, self.tblAddActionProperties_30, previous)


    def updateAddActions30PropertiesTable(self, index, tbl, previous=None):
        if index.isValid() and index.model():
            if previous:
                tbl.savePreferencesLoc(previous.row())
            row = index.row()
            items = index.model().items()
            if row >= 0 and row < len(items):
                record, action = items[row]
                if action:
                    clientId = self.clientId
                    clientSex = self.clientSex
                    clientAge = self.clientAge
                    tbl.model().setAction(action, clientId, clientSex, clientAge, self.eventTypeId)
                    setActionPropertiesColumnVisible(action._actionType, tbl)
                    tbl.resizeColumnsToContents()
                    tbl.resizeRowsToContents()
                    tbl.horizontalHeader().setStretchLastSection(True)
                    tbl.loadPreferencesLoc(tbl.preferencesLocal, row)
                else:
                    tbl.model().setAction(None, None)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelAmbCardStatusActions_29_currentRowChanged(self, current, previous):
        self.updateAmbCardPropertiesTable(current, self.tblAmbCardStatusActionProperties_29, previous)


    def updateAboutMedicalExaminationsRequiredActionProperties(self, index, tbl, previous=None, actionId=None):
        if previous:
            tbl.savePreferencesLoc(previous.row())
        if index.isValid() and actionId:
            row = index.row()
            db = QtGui.qApp.db
            table = db.table('Action')
            record = db.getRecordEx(table, '*', [table['id'].eq(actionId), table['deleted'].eq(0)])
            if record:
                clientId = self.clientId
                clientSex = self.clientSex
                clientAge = self.clientAge
                action = CAction(record=record)
                tbl.model().setAction2(action, clientId, clientSex, clientAge, eventTypeId=self.eventTypeId)
                setActionPropertiesColumnVisible(action._actionType, tbl)
                tbl.resizeColumnsToContents()
                tbl.resizeRowsToContents()
                tbl.horizontalHeader().setStretchLastSection(True)
                tbl.loadPreferencesLoc(tbl.preferencesLocal, row)
            else:
                tbl.model().setAction2(None, None)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelAboutMedicalExaminationsRequiredAction_currentRowChanged(self, current, previous):
        self.setModelAboutMedicalExaminationsRequiredActionRowChanged(current, previous)


    def setModelAboutMedicalExaminationsRequiredActionRowChanged(self, current, previous=None):
        index = self.tblAboutMedicalExaminationsRequiredAction.currentIndex()
        if index.isValid():
            row = index.row()
            actionId = self.modelAboutMedicalExaminationsRequiredAction.getActionIdToRow(row)
            items = self.modelAboutMedicalExaminationsRequiredAction.items()
            if 0 <= row < len(items) and hasattr(items[row], 'aboutMERProperties'):
                self.modelAboutMedicalExaminationsRequiredProperties.setItems(items[row].aboutMERProperties.getItems())
            else:
                self.modelAboutMedicalExaminationsRequiredProperties.clearItems()
            self.updateAboutMedicalExaminationsRequiredActionProperties(current, self.tblAboutMedicalExaminationsRequiredProperties, previous, actionId)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelAmbCardDiagnosticActions_30_currentRowChanged(self, current, previous):
        self.updateAmbCard30PropertiesTable(current, self.tblAmbCardDiagnosticActionProperties_30, previous)


    def setActionProperties30ColumnVisible(self, actionType, propertiesView):
        propertiesView.setColumnHidden(1, not actionType.propertyAssignedVisible)
        propertiesView.setColumnHidden(3, not actionType.propertyUnitVisible)
        propertiesView.setColumnHidden(4, not actionType.propertyNormVisible)
        propertiesView.setColumnHidden(5, not actionType.propertyEvaluationVisible)
        propertiesView.setColumnHidden(6, not actionType.propertyCommentVisible)


    def getAboutMERPropertyIdList(self):
        propertyIdList = []
        actionItems = self.modelAboutMedicalExaminationsRequiredAction.items()
        for actionItem in actionItems:
            if actionItem.aboutMERProperties:
                propertyItems = actionItem.aboutMERProperties.getItems()
                for propertyItem in propertyItems:
                    propertyId = forceRef(propertyItem.value('actionProperty_id'))
                    if propertyId and propertyId not in propertyIdList:
                        propertyIdList.append(propertyId)
        return propertyIdList


    def updateAmbCard30PropertiesTable(self, index, tbl, previous=None):
        if previous:
            tbl.savePreferencesLoc(previous.row())
        row = index.row()
        record = index.model().getRecordByRow(row) if row >= 0 else None
        if record:
            clientId = self.clientId
            clientSex = self.clientSex
            clientAge = self.clientAge
            action = CAction(record=record)
            propertySelectedIdList = self.getAboutMERPropertyIdList()
            tbl.model().setAction2(action, clientId, clientSex, clientAge, eventTypeId=self.eventTypeId, propertySelectedIdList=propertySelectedIdList)
            self.setActionProperties30ColumnVisible(action._actionType, tbl)
            currentActionId = self.modelAmbCardDiagnosticActionProperties_30.getCurrentActionId()
            if currentActionId:
                self.modelAmbCardDiagnosticActionProperties_30.includeRows = self.modelAmbCardDiagnosticActions_30.includeItems.get(currentActionId, {})
            tbl.resizeColumnsToContents()
            tbl.resizeRowsToContents()
            tbl.horizontalHeader().setStretchLastSection(True)
            tbl.loadPreferencesLoc(tbl.preferencesLocal, row)
        else:
            tbl.model().setAction2(None, None)


    def updateAmbCardAnamnesisPropertiesTable(self, index, tbl, previous=None):
        if previous:
            tbl.savePreferencesLoc(previous.row())
        row = index.row()
        record = index.model().getRecordByRow(row) if row >= 0 else None
        if record:
            clientId = self.clientId
            clientSex = self.clientSex
            clientAge = self.clientAge
            action = CAction(record=record)
            tbl.model().setAction2(action, clientId, clientSex, clientAge, eventTypeId=self.eventTypeId)
            self.setActionProperties30ColumnVisible(action._actionType, tbl)
            tbl.resizeColumnsToContents()
            tbl.resizeRowsToContents()
            tbl.horizontalHeader().setStretchLastSection(True)
            tbl.loadPreferencesLoc(tbl.preferencesLocal, row)
        else:
            tbl.model().setAction2(None, None)


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
            tbl.model().setAction2(action, clientId, clientSex, clientAge, eventTypeId=self.eventTypeId)
            setActionPropertiesColumnVisible(action._actionType, tbl)
            tbl.resizeColumnsToContents()
            tbl.resizeRowsToContents()
            tbl.horizontalHeader().setStretchLastSection(True)
            tbl.loadPreferencesLoc(tbl.preferencesLocal, row)
        else:
            tbl.model().setAction2(None, None)


    def updateAssignedMedicament(self, posToId=None):
        self.modelAssignedMedicament.includeItems = {}
        self.modelAssignedMedicament.enableIdList = []
        actionIdList, eventIdDict, actionsPropertiesRegistry = self.loadAssignedMedicament(self.clientId)
        self.modelAssignedMedicament.setActionsPropertiesRegistry(actionsPropertiesRegistry)
        self.tblAssignedMedicament.setIdList(actionIdList, posToId)
        self.modelAssignedMedicament.setEventIdDict(eventIdDict)
        self.modelAssignedMedicament.setEventId(self.eventId)


    def loadAssignedMedicament(self, clientId, order=['Action.endDate DESC', 'Action.id']):
        actionIdList = []
        eventIdDict = {}
        actionsPropertiesRegistry = {}
        if clientId:
            try:
                QtGui.QApplication.setOverrideCursor(QtGui.QCursor(Qt.WaitCursor))
                db = QtGui.qApp.db
                tableEvent = db.table('Event')
                tableAction = db.table('Action')
                tableActionType = db.table('ActionType')
                tableActionProperty = db.table('ActionProperty')
                tableActionPropertyType = db.table('ActionPropertyType')
                tableAPNomenclature = db.table('ActionProperty_rbNomenclature')
                tableRBNomenclature = db.table('rbNomenclature')
                queryTable = tableEvent.innerJoin(tableAction, tableAction['event_id'].eq(tableEvent['id']))
                queryTable = queryTable.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
                queryTable = queryTable.innerJoin(tableActionProperty, tableActionProperty['action_id'].eq(tableAction['id']))
                queryTable = queryTable.innerJoin(tableActionPropertyType, tableActionPropertyType['actionType_id'].eq(tableActionType['id']))
                queryTable = queryTable.innerJoin(tableAPNomenclature, tableAPNomenclature['id'].eq(tableActionProperty['id']))
                queryTable = queryTable.innerJoin(tableRBNomenclature, tableRBNomenclature['id'].eq(tableAPNomenclature['value']))
                cols = [tableAction['id'],
                        tableAction['event_id'],
                        tableActionProperty['id'].alias('actionPropertyId'),
                        tableAPNomenclature['value']
                        ]
                cond = [tableAction['deleted'].eq(0),
                        tableEvent['deleted'].eq(0),
                        tableEvent['client_id'].eq(clientId),
                        tableActionPropertyType['typeName'].eq(CNomenclatureActionPropertyValueType.name),
                        tableActionProperty['id'].isNotNull(),
                        tableAPNomenclature['value'].isNotNull(),
                        tableRBNomenclature['esklpUUID'].isNotNull()
                        ]
                medicamentActionIdList = self.modelMedicament.getActionIdList()
                if medicamentActionIdList:
                    cond.append(tableAction['id'].notInlist(medicamentActionIdList))
                records = db.getRecordList(queryTable, cols, cond, order)
                for record in records:
                    actionId = forceRef(record.value('id'))
                    if actionId and actionId not in actionIdList:
                        actionPropertyId = forceRef(record.value('actionPropertyId'))
                        nomenclatureId = forceRef(record.value('value'))
                        if nomenclatureId and actionPropertyId:
                            actionIdList.append(actionId)
                            actionsPropertiesRegistry[actionId] = (nomenclatureId, actionPropertyId)
                            eventId = forceRef(record.value('event_id'))
                            if eventId:
                                eventIdDict[actionId] = eventId
            finally:
                QtGui.QApplication.restoreOverrideCursor()
        return actionIdList, eventIdDict, actionsPropertiesRegistry


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
        self.idx = forceInt(record.value('idx'))
        self.clientId = self.getClientId(self.eventId)
        self.action = CAction(record=record)
        actionType = self.action.getType()
        self.actionTypeId = actionType.id
        if not self.isActionSave:
            self.setComboBoxes()
        self.action.executionPlanManager.load()
        self.action.executionPlanManager.setCurrentItemIndex()
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
        self.btnLoadPrevAction.setEnabled(QtGui.qApp.userHasRight(urCopyPrevAction) and canEdit and bool(self.action and self.getPrevActionId()))
        self.edtAmount.setEnabled(actionType.amountEvaluation == 0 and canEdit)
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
        self.modelDiagnosisDisease_31_1.setAction(self.action)
        self.modelDiagnosisDisease_31_1.loadItems(self.eventId)
        self.modelDiagnosisDisease_31_3.setAction(self.action)
        self.modelDiagnosisDisease_31_3.loadItems(self.eventId)
        self.modelDiagnosisDisease_31_4.setAction(self.action)
        self.modelDiagnosisDisease_31_4.loadItems(self.eventId)
        self.modelDiagnosisDisease_31_6.setAction(self.action)
        self.modelDiagnosisDisease_31_6.loadItems(self.eventId)
        self.modelVisits.loadItems(self.eventId)
        self.grpTempInvalid.pickupTempInvalid()
        self.grpAegrotat.pickupTempInvalid()
        self.grpDisability.pickupTempInvalid()
        self.grpVitalRestriction.pickupTempInvalid()
        actionId = self.itemId()
        self.modelMedicament.loadItems(actionId)
        self.updateAssignedMedicament(actionId)
        iniExportEvent(self)
        lpu_guid = forceString(db.translate('Organisation', 'id', QtGui.qApp.currentOrgId(), 'usishCode'))
        self.tabExtendedMSE.setClientInfo({'clientId': self.clientId, 'lpuGuid': lpu_guid, 'actionId': actionId})
        self.modelAboutMedicalExaminationsRequiredAction.loadItems(actionId)
        self.modelAboutMedicalExaminationsRequiredProperties.setMasterId(actionId)
        self.tblAboutMedicalExaminationsRequiredAction.setCurrentRow(0)
        self.tblDiagnosisDisease_31_1.setRowHidden(1, True)
        self.tblDiagnosisDisease_31_1.resizeColumnToContents(self.tblDiagnosisDisease_31_1.columnHint)
#        self.tblDiagnosisDisease_31_1.resizeRowToContents(0)
        self.tblDiagnosisDisease_31_3.resizeColumnsToContents()
        self.tblDiagnosisDisease_31_3.resizeRowsToContents()
        self.tblDiagnosisDisease_31_4.resizeColumnsToContents()
        self.tblDiagnosisDisease_31_4.resizeRowsToContents()
        self.tblDiagnosisDisease_31_6.resizeColumnsToContents()
        self.tblDiagnosisDisease_31_6.resizeRowsToContents()
        self.isActionSave = False


    def getShortNameTextEdit(self): # *
        return [u'5.14', u'24', u'25', u'27.6', u'29', u'29.1', u'30', u'35', u'35.1', u'35.2', u'36', u'37', u'38', u'39']


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
                self.chkBaseInfoMSI4.setChecked(self.getPropertyValue(items, u'4', QCheckBox))
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
                # tabClientData
                self.cmbClientCitizenship.setValue(self.getPropertyValue(items, u'9', QString))
                self.cmbRepresentativeDocumentName.setValue(self.getPropertyValue(items, u'17.2.1', QString))
                self.cmbClientMilitaryDuty.setValue(self.getPropertyValue(items, u'10', QString))
                self.chkClientNoFixedPlaceResidence.setChecked(self.getPropertyValue(items, u'12', QCheckBox))
                self.cmbClientIsLocated.setValue(self.getPropertyValue(items, u'13', QString))
                self.cmbClientIsLocatedOrg.setValue(self.getPropertyValue(items, u'13.x', forceRef))
                self.edtRepresentativeDocumentSeria.setText(self.getPropertyValue(items, u'17.2.2.1', QString))
                self.edtRepresentativeDocumentNumber.setText(self.getPropertyValue(items, u'17.2.2.2', QString))
                self.edtRepresentativeDocumentOrigin.setText(self.getPropertyValue(items, u'17.2.3', QString))
                self.edtRepresentativeDocumentDate.setDate(self.getPropertyValue(items, u'17.2.4', QDate))
                self.edtRepresentativeOrgName.setText(self.getPropertyValue(items, u'17.6.1', QString))
                self.edtRepresentativeOrgAddress.setText(self.getPropertyValue(items, u'17.6.2', QString))
                self.edtRepresentativeOrgOGRN.setText(self.getPropertyValue(items, u'17.6.3', QString))
                self.cmbFormMedicalCare.setValue(self.getPropertyValue(items, u'18.3', QString))
                self.cmbTypeMedicalCare.setValue(self.getPropertyValue(items, u'18.4', QString))
                self.cmbConditionsMedicalCare.setValue(self.getPropertyValue(items, u'18.5', QString))
                self.edtConsentReferralConductDateMSI.setDate(self.getPropertyValue(items, u'19.1', QDate))
                self.cmbPreferredFormHolding.setValue(self.getPropertyValue(items, u'19.2', QString))
                methodReceivingNotification19_3 = self.getPropertyValue(items, u'19.3', QString)
                self.chkMethodReceivingNotification19_3_1.setChecked(u'1. ' in methodReceivingNotification19_3)
                self.chkMethodReceivingNotification19_3_2.setChecked(u'2. ' in methodReceivingNotification19_3)
                self.chkMethodReceivingNotification19_3_3.setChecked(u'3. ' in methodReceivingNotification19_3)
                self.edtClientEducationOrgName.setText(self.getPropertyValue(items, u'21.1', QString))
                self.edtClientEducationOrgAddress.setText(self.getPropertyValue(items, u'21.1.1', QString))
                self.edtClientEducationCourse.setText(self.getPropertyValue(items, u'21.2', QString))
                self.edtClientEducationSpecialty.setText(self.getPropertyValue(items, u'21.3', QString))
                self.edtPatronSpecialty.setText(self.getPropertyValue(items, u'22.1', QString))
                self.edtPatronQualification.setText(self.getPropertyValue(items, u'22.2', QString))
                self.edtPatronWorkExperience.setText(self.getPropertyValue(items, u'22.3', QString))
                self.edtPatronWorkActive.setText(self.getPropertyValue(items, u'22.4', QString))
                self.edtPatronWorkActiveSpecialty.setText(self.getPropertyValue(items, u'22.4.1', QString))
                self.edtPatronWorkActivePost.setText(self.getPropertyValue(items, u'22.4.2', QString))
                self.edtPatronWorkConditions.setText(self.getPropertyValue(items, u'22.5', QString))
                self.edtPatronWorkPlaceOrg.setText(self.getPropertyValue(items, u'22.6', QString))
                self.edtPatronWorkPlaceAddress.setText(self.getPropertyValue(items, u'22.7', QString))
                # tabPrevMSI
                if self.chkAgainMSI.isChecked():
                    self.cmbPrevMSI20_1.setValue(self.getPropertyValue(items, u'20.1', QString))
                    self.cmbPrevMSI20_1_1.setValue(self.getPropertyValue(items, u'20.1.1', QString))
                    self.cmbPrevMSI20_1_2.setValue(self.getPropertyValue(items, u'20.1.2', QString))
                    self.edtPrevMSI20_2.setDate(self.getPropertyValue(items, u'20.2', QDate))
                    self.cmbPrevMSI20_3.setValue(self.getPropertyValue(items, u'20.3', QString))
                    self.cmbPrevMSI20_4.setValue(self.getPropertyValue(items, u'20.4', QString))
                    self.edtPrevMSI20_4_16.setText(self.getPropertyValue(items, u'20.4.16', QString))
                    self.edtPrevMSI20_4_17.setText(self.getPropertyValue(items, u'20.4.17', QString))
                    self.edtPrevMSI20_5.setText(self.getPropertyValue(items, u'20.5', QString))
                    self.cmbPrevMSI20_6.setValue(self.getPropertyValue(items, u'20.6', QString))
                    self.edtPrevMSI20_7.setDate(self.getPropertyValue(items, u'20.7', QDate))
                    self.edtPrevMSI20_8.setText(self.getPropertyValue(items, u'20.8', QString))
                # tabAnamnesis
                self.edtAnamnesis23.setText(self.getPropertyValue(items, u'23', QString))
                self.edtAnamnesis24.setText(self.getPropertyValue(items, u'24', QTextEdit))
                self.edtAnamnesis25.setText(self.getPropertyValue(items, u'25', QTextEdit))
                self.edtAnamnesis28_1.setValue(self.getPropertyValue(items, u'28.1', float))
                self.edtAnamnesis28_2.setValue(self.getPropertyValue(items, u'28.2', float))
                self.edtAnamnesis28_3.setValue(self.getPropertyValue(items, u'28.3', float))
                self.cmbAnamnesis28_4.setValue(self.getPropertyValue(items, u'28.4', QString))
                self.edtAnamnesis28_5.setValue(self.getPropertyValue(items, u'28.5', int))
                self.edtAnamnesis28_6_1.setValue(self.getPropertyValue(items, u'28.6.1', int))
                self.edtAnamnesis28_6_2.setValue(self.getPropertyValue(items, u'28.6.2', int))
                self.edtAnamnesis28_7.setText(self.getPropertyValue(items, u'28.7', QString))
                self.edtAnamnesis28_8.setText(self.getPropertyValue(items, u'28.8', QString))
                # tabTempInvalidVUT
                self.chkTempInvalidDocumentIsElectronic.setChecked(self.getPropertyValue(items, u'26.1', QCheckBox))
                self.edtTempInvalidDocumentElectronicNumber.setText(self.getPropertyValue(items, u'26.2', QString))
                # tabIPRA
                self.edtIPRANumber.setText(self.getPropertyValue(items, u'27.1', QString))
                self.edtIPRANumberMSI.setText(self.getPropertyValue(items, u'27.2', QString))
                self.edtIPRADateMSI.setDate(self.getPropertyValue(items, u'27.3', QDate))
                IPRAResult27_4 = self.getPropertyValue(items, u'27.4', QString)
                self.chkIPRAResult27_1.setChecked(u'27.1. ' in IPRAResult27_4)
                self.chkIPRAResult27_1_1.setChecked(u'27.1.1. ' in IPRAResult27_4)
                self.chkIPRAResult27_1_2.setChecked(u'27.1.2. ' in IPRAResult27_4)
                self.chkIPRAResult27_1_3.setChecked(u'27.1.3. ' in IPRAResult27_4)
                IPRAResult27_5 = self.getPropertyValue(items, u'27.5', QString)
                self.chkIPRAResult27_2.setChecked(u'27.2. ' in IPRAResult27_5)
                self.chkIPRAResult27_2_1.setChecked(u'27.2.1. ' in IPRAResult27_5)
                self.chkIPRAResult27_2_2.setChecked(u'27.2.2. ' in IPRAResult27_5)
                self.chkIPRAResult27_2_3.setChecked(u'27.2.3. ' in IPRAResult27_5)
                self.edtIPRAResult27_6.setPlainText(self.getPropertyValue(items, u'27.6', QTextEdit))
                # tabStatus
                self.edtHealthClientDirectionMSI.setText(self.getPropertyValue(items, u'29', QTextEdit))
                self.edtComplaintsAboutStateHealth.setText(self.getPropertyValue(items, u'29.1', QTextEdit))
                # tabInspection
#                self.edtInfoAboutMedicalExaminationsRequired.setPlainText(self.getPropertyValue(items, u'30', QTextEdit))
                # tabDiagnosis
                self.cmbClinicalPrognosis.setValue(self.getPropertyValue(items, u'32', QString))
                self.cmbRehabilitationPotential.setValue(self.getPropertyValue(items, u'33', QString))
                self.cmbRehabilitationPrognosis.setValue(self.getPropertyValue(items, u'34', QString))
                # tabRecommend
                self.edtRecommendedActionRehabilitation.setPlainText(self.getPropertyValue(items, u'35', QTextEdit))
                self.edtRecommendedActionReconstructiveSurgery.setPlainText(self.getPropertyValue(items, u'36', QTextEdit))
                self.edtRecommendedActionProsthetics.setPlainText(self.getPropertyValue(items, u'37', QTextEdit))
                self.edtHealthResortTreatment.setPlainText(self.getPropertyValue(items, u'38', QTextEdit))
                self.edtExtraneousSpecialMedicalCare.setPlainText(self.getPropertyValue(items, u'39', QTextEdit))
                # tabNomenclatureExpense
                self.edtNomenclatureExpense35_1.setPlainText(self.getPropertyValue(items, u'35.1', QTextEdit))
                self.edtNomenclatureExpense35_2.setPlainText(self.getPropertyValue(items, u'35.2', QTextEdit))
                # tabCommission
                self.cmbOrganisationByMSI_45.setValue(self.getPropertyValue(items, u'45', forceRef))
                # tabAdditionalData
                self.edtAdditionalDataRegistrationDate.setDate(self.getPropertyValue(items, u'46', QDate))
                self.edtAdditionalDataExaminationDate.setDate(self.getPropertyValue(items, u'47', QDate))
                self.cmbAdditionalDataResultMSI.setValue(self.getPropertyValue(items, u'48', QString))
                self.cmbAdditionalDataDisabilityGroup.setValue(self.getPropertyValue(items, u'49', QString))

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
                        value = propertyType.convertQVariantToPyValue(value) if type(value) == QVariant else value
                        if type(value) == unicode:
                            value = value.replace('\0', '')
                        self.action[propertyTypeName] = QVariant(value)
                        break


    def getProperty(self, propertyShortName):
        if self.action:
            actionType = self.action.getType()
            for name, propertyType in actionType._propertiesByName.items():
                if trim(propertyType.shortName) == trim(propertyShortName):
                    return toVariant(self.action[name])
        return QVariant()


    def getRecord(self):
        record = self.record()
        showTime = self.action.getType().showTime
        eventRecord = self._getEventRecord()
        if eventRecord:
            eventExecDate = forceDate(eventRecord.value('execDate'))
            if not eventExecDate:
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

    
    def afterSave(self):
        if self._id:
            db = QtGui.qApp.db
            record = db.getRecord(db.table(self._tableName), '*', self._id)
            self.isActionSave = True
            self.setRecord(record)
        self.setIsDirty(False)
        
        
    def getActionMKB(self):
        MKB = forceStringEx(self.action.getRecord().value('MKB'))
        items = self.modelDiagnosisDisease_31_1.items()
        for item in items:
            MKB = forceStringEx(item.value('MKB'))
            if MKB:
                self.action.getRecord().setValue('MKB', toVariant(MKB))
                self.action.setChanged(True)
                break
        return MKB
    
    
    def saveAction(self):
        newActionId = None
        if self.action:
            self.getActionMKB()
            self.action._record = self.getRecord()
            self.setTextEdits()
            eventRecordMSI = self.getEventRecord()
            idxMSI = self.idx
            db = QtGui.qApp.db
            tableEvent = db.table('Event')
            tableEventType = db.table('EventType')
            recordAction = self.action.getRecord()
            eventRecordMSIId = forceRef(eventRecordMSI.value('id')) if eventRecordMSI else None
            eventId = forceRef(recordAction.value('event_id')) if recordAction else (eventRecordMSIId if eventRecordMSIId else None)
            if eventId and eventRecordMSI:
                newActionId = self.saveMedicalCommissionAction(self.action, eventRecordMSI, eventId, idx = idxMSI)
            else:
                eventTypeId = forceRef(eventRecordMSI.value('eventType_id')) if eventRecordMSI else None
                if not eventTypeId:
                    recordEventType = db.getRecordEx(tableEventType, [tableEventType['id']], [tableEventType['context'].like(u'inspection%'), tableEventType['deleted'].eq(0)], u'EventType.id')
                    eventTypeId = forceRef(recordEventType.value('id')) if recordEventType else None
                if eventTypeId:
                    tableEvent = db.table('Event')
                    recordEvent = tableEvent.newRecord()
                    if eventRecordMSI:
                        for i in xrange(recordEvent.count()):
                            fieldName = recordEvent.fieldName(i)
                            if fieldName in tabNotesFieldNames:
                                recordEvent.setValue(i, eventRecordMSI.value(fieldName))
                        recordEvent.setValue('eventType_id',   toVariant(eventTypeId))
                        if self.clientId and not forceRef(recordEvent.value('client_id')):
                            recordEvent.setValue('client_id', toVariant(self.clientId))
                    else:
                        currentOrgId = None
                        if QtGui.qApp.userId:
                            recordPerson = db.getRecord('Person', ['org_id'], QtGui.qApp.userId)
                            if recordPerson:
                                currentOrgId = forceRef(recordPerson.value('org_id'))
                        if not currentOrgId:
                            currentOrgId = QtGui.qApp.currentOrgId()
                        recordEvent.setValue('createDatetime', toVariant(QDateTime.currentDateTime()))
                        recordEvent.setValue('createPerson_id',toVariant(QtGui.qApp.userId))
                        recordEvent.setValue('modifyDatetime', toVariant(QDateTime.currentDateTime()))
                        recordEvent.setValue('modifyPerson_id',toVariant(QtGui.qApp.userId))
                        recordEvent.setValue('setDate',        toVariant(QDateTime.currentDateTime()))
                        recordEvent.setValue('eventType_id',   toVariant(eventTypeId))
                        recordEvent.setValue('client_id', toVariant(self.clientId))
                        recordEvent.setValue('relegatePerson_id', toVariant(QtGui.qApp.userId))
                        recordEvent.setValue('relegateOrg_id', toVariant(QtGui.qApp.currentOrgId()))
                        recordEvent.setValue('org_id',         toVariant(currentOrgId))
                    eventId = db.insertRecord(tableEvent, recordEvent)
                    if eventId:
                        recordEvent.setValue('id', toVariant(eventId))
                        self.setEventRecord(recordEvent)
                        self.tabNotes.setNotes(self.recordEvent)
                        newActionId = self.saveMedicalCommissionAction(self.action, recordEvent, eventId, idx = idxMSI)
            if eventId and newActionId:
                if hasattr(self, 'tabNotes') and hasattr(self.tabNotes, 'saveAttachedFiles'):
                    self.tabNotes.saveAttachedFiles(eventId)
                if hasattr(self, 'modelDiagnosisDisease_31_1'):
                    self.saveDiagnostics(self.modelDiagnosisDisease_31_1, eventId)
                if hasattr(self, 'modelDiagnosisDisease_31_3'):
                    self.saveDiagnostics(self.modelDiagnosisDisease_31_3, eventId)
                if hasattr(self, 'modelDiagnosisDisease_31_4'):
                    self.saveDiagnostics(self.modelDiagnosisDisease_31_4, eventId)
                if hasattr(self, 'modelDiagnosisDisease_31_6'):
                    self.saveDiagnostics(self.modelDiagnosisDisease_31_6, eventId)
                if hasattr(self, 'modelAddActions_30'):
                    self.modelAddActions_30.saveItems(eventId)
                    self.modelAddActions_30.clearItems()
                if hasattr(self, 'modelElectronicMedicalDocument'):
                    self.modelElectronicMedicalDocument.saveItems(newActionId)
                if hasattr(self, 'modelAboutMedicalExaminationsRequiredAction'):
                    self.modelAboutMedicalExaminationsRequiredAction.saveItems(newActionId)
                if hasattr(self, 'modelMedicament'):
                    self.modelMedicament.saveItems(newActionId)
        return newActionId


    def saveInternals(self, id):
        self.getActionMKB()
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
                recDiagResult = db.getRecordEx(tableRbDiagnosticResult, [tableRbDiagnosticResult['result_id']],
                                               tableRbDiagnosticResult['eventPurpose_id'].eq(eventType.purposeId))
                eventRecord.setValue('result_id', recDiagResult.value('result_id') if recDiagResult else None)
                isPrimary = 1
                for property in self.action._propertiesById.itervalues():
                    propertyType = property.type()
                    if trim(propertyType.shortName) == '18':
                        value = property._value
                        propertyValue = propertyType.convertQVariantToPyValue(value) if type(
                            value) == QVariant else value
                        if isinstance(propertyValue, basestring) or type(propertyValue) == QString:
                            propertyValue = trim(propertyValue)
                            if propertyValue == u'18.2. повторно':
                                isPrimary = 2
                            else:
                                isPrimary = 1
                eventRecord.setValue('isPrimary', QVariant(isPrimary))
                eventRecord.setValue('order', QVariant(1))  # порядок события всегда плановый
                db.updateRecord('Event', eventRecord)

            self.tabNotes.saveAttachedFiles(self.eventId)
            self.saveDiagnostics(self.modelDiagnosisDisease_31_1, self.eventId)
            self.saveDiagnostics(self.modelDiagnosisDisease_31_3, self.eventId)
            self.saveDiagnostics(self.modelDiagnosisDisease_31_4, self.eventId)
            self.saveDiagnostics(self.modelDiagnosisDisease_31_6, self.eventId)
            if hasattr(self, 'modelVisits'):
                if not self.modelVisits.items():
                    visit = self.modelVisits.getEmptyRecord(sceneId=None, personId=self.personId)
                    visit.setValue('date', toVariant(self.eventSetDate))
                else:
                    visit = self.modelVisits.items()[0]
                    visit.setValue('date', toVariant(self.action.getRecord().value('begDate')))
                    visit.setValue('person_id', toVariant(self.personId))
                self.modelVisits.setItems([visit])
                self.modelVisits.saveItems(self.eventId)
            if hasattr(self, 'modelAddActions_30'):
                self.modelAddActions_30.saveItems(self.eventId)
                self.modelAddActions_30.clearItems()
                self.modelAddActionProperties_30.setAction(None, None, None, None, None)
                self.on_cmdAmbCardDiagnosticButtonBox_30_apply()
            if hasattr(self, 'modelAboutMedicalExaminationsRequiredAction'):
                self.modelAboutMedicalExaminationsRequiredAction.saveItems(id)
            if hasattr(self, 'modelMedicament'):
                self.modelMedicament.saveItems(id)
            self.tabExtendedMSE.saveData()
        return id


    def getAssistantId(self):
        if hasattr(self, 'tabNotes'):
            return self.tabNotes.cmbEventAssistant.value()
        if self.record():
            return forceRef(self.recordEvent.value('assistant_id'))
        return None


    def getModelFinalDiagnostics(self):
        return self.modelDiagnosisDisease_31_1


    def updateClientInfo(self):
        db = QtGui.qApp.db
        self.clientInfo = getClientInfo(self.clientId, date=self.edtDirectionDate.date())
        self.txtClientInfoBrowser.setHtml(formatClientBanner(self.clientInfo))
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
        self.modelAddActions_30.setClientInfo(self.clientId, self.clientSex, self.clientAge)


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
                if execDate and setDate:
                    if actionType and u'received' in actionType.flatCode.lower():
                        isControlActionReceivedBegDate = QtGui.qApp.isControlActionReceivedBegDate()
                        if isControlActionReceivedBegDate:
                            eventBegDate = forceDateTime(record.value('setDate')) if showTime else forceDate(record.value('setDate'))
                            eventBegDate = toDateTimeWithoutSeconds(eventBegDate)
                            actionBegDate = begDate
                            if eventBegDate != actionBegDate:
                                if isControlActionReceivedBegDate == 1:
                                    message = u'Дата начала случая обслуживания %s не совпадает с датой начала действия Поступление %s. Исправить?'%(forceString(eventBegDate), forceString(actionBegDate))
                                    skippable = True
                                else:
                                    message = u'Дата начала случая обслуживания %s не совпадает с датой начала действия Поступление %s. Необходимо исправить.'%(forceString(eventBegDate), forceString(actionBegDate))
                                    skippable = False
                                result = result and self.checkValueMessage(message, skippable, self.edtBegDate)
                if setDate and endDate:
                    result = result and (endDate >= setDate or self.checkValueMessage(u'Дата выполнения действия %s не должна быть раньше даты начала события % s'%(forceString(endDate), forceString(setDate)), True, self.edtEndDate))
                actionsBeyondEvent = getEventEnableActionsBeyondEvent(self.eventTypeId)
                if execDate and endDate and actionsBeyondEvent:
                    result = result and (execDate >= endDate or self.checkValueMessage(u'Дата выполнения действия %s не должна быть позже даты выполнения события % s'%(forceString(endDate), forceString(execDate)), True if actionsBeyondEvent == 1 else False, self.edtEndDate))
                elif setDate and endDate:
                    currentDate = QDate.currentDate()
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
                result = result and CEventEditDialog(self).checkEventActionDateEntered(setDate, execDate, status, directionDate, begDate, endDate, None, self.edtEndDate, self.edtBegDate, None, 0, nameActionType, actionShowTime=actionShowTime, enableActionsBeyondEvent=actionsBeyondEvent)
        result = result and (begDate or self.checkInputMessage(u'дату назначения', False, self.edtBegDate))
        if not secondTry:
            result = result and (endDate or self.checkInputMessage(u'дату выполнения', True, self.edtEndDate))
        result = result and self.checkPlannedEndDate()
        result = result and self.checkActionMorphology()
        return result


    def checkActionMorphology(self):
        actionStatus = self.cmbStatus.value()
        if QtGui.qApp.defaultMorphologyMKBIsVisible() \
           and actionStatus in (CActionStatus.finished, CActionStatus.withoutResult):
            action = self.action
            actionType = action.getType()
            defaultMKB = actionType.defaultMKB
            isMorphologyRequired = actionType.isMorphologyRequired
            items = self.modelDiagnosisDisease_31_1.items()
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
    def on_chkBaseInfoMSI4_toggled(self, checked):
        self.setProperty(QVariant(self.chkBaseInfoMSI4.isChecked()), u'4')


    @pyqtSignature('bool')
    def on_chkNeedPalliativeCare_toggled(self, checked):
        self.setProperty(QVariant(self.chkNeedPalliativeCare.isChecked()), u'3')


    def tabPrevMSIReset(self):
        self.cmbPrevMSI20_1.setValue(None)
        self.cmbPrevMSI20_1_1.setValue(None)
        self.cmbPrevMSI20_1_2.setValue(None)
        self.edtPrevMSI20_2.setDate(None)
        self.cmbPrevMSI20_3.setValue(None)
        self.cmbPrevMSI20_4.setValue(None)
        self.edtPrevMSI20_4_16.setText('')
        self.edtPrevMSI20_4_17.setText('')
        self.edtPrevMSI20_5.setText('')
        self.cmbPrevMSI20_6.setValue(None)
        self.edtPrevMSI20_7.setDate(None)
        self.edtPrevMSI20_8.setText('')


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


    @pyqtSignature('bool')
    def on_chkMethodReceivingNotification19_3_1_toggled(self, checked):
        isChecked = self.chkMethodReceivingNotification19_3_1.isChecked()
        self.setMethodReceivingNotification19_3(isChecked, u'1')


    @pyqtSignature('bool')
    def on_chkMethodReceivingNotification19_3_2_toggled(self, checked):
        isChecked = self.chkMethodReceivingNotification19_3_2.isChecked()
        self.setMethodReceivingNotification19_3(isChecked, u'2')


    @pyqtSignature('bool')
    def on_chkMethodReceivingNotification19_3_3_toggled(self, checked):
        isChecked = self.chkMethodReceivingNotification19_3_3.isChecked()
        self.setMethodReceivingNotification19_3(isChecked, u'3')


    def setMethodReceivingNotification19_3(self, isChecked, propertyShortName):
        propertyValue = forceString(self.getProperty(u'19.3'))
        propertyShortNamePoint = propertyShortName + u'. '
        if isChecked:
            if propertyShortNamePoint not in propertyValue:
                for name in self.methodReceivingNotification19_3:
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
        self.setProperty(QVariant(propertyValue), u'19.3')


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
    def on_cmbRepresentativeDocumentName_currentIndexChanged(self, value):
        self.setProperty(QVariant(self.cmbRepresentativeDocumentName.value()), u'17.2.1')


    @pyqtSignature('int')
    def on_cmbClientMilitaryDuty_currentIndexChanged(self, value):
        self.setProperty(QVariant(self.cmbClientMilitaryDuty.value()), u'10')


    @pyqtSignature('int')
    def on_cmbClientIsLocated_currentIndexChanged(self, value):
        self.setProperty(QVariant(self.cmbClientIsLocated.value()), u'13')


    @pyqtSignature('int')
    def on_cmbFormMedicalCare_currentIndexChanged(self, value):
        self.setProperty(QVariant(self.cmbFormMedicalCare.value()), u'18.3')


    @pyqtSignature('int')
    def on_cmbTypeMedicalCare_currentIndexChanged(self, value):
        self.setProperty(QVariant(self.cmbTypeMedicalCare.value()), u'18.4')


    @pyqtSignature('int')
    def on_cmbConditionsMedicalCare_currentIndexChanged(self, value):
        self.setProperty(QVariant(self.cmbConditionsMedicalCare.value()), u'18.5')


    @pyqtSignature('QDate')
    def on_edtConsentReferralConductDateMSI_dateChanged(self, date):
        self.setProperty(QVariant(self.edtConsentReferralConductDateMSI.date()), u'19.1')


    @pyqtSignature('int')
    def on_cmbPreferredFormHolding_currentIndexChanged(self, value):
        self.setProperty(QVariant(self.cmbPreferredFormHolding.value()), u'19.2')


    def setTextEdits(self):
        self.setProperty(QVariant(self.edtClientEducationOrgName.text()), u'21.1')
        self.setProperty(QVariant(self.edtClientEducationOrgAddress.text()), u'21.1.1')
        self.setProperty(QVariant(self.edtClientEducationCourse.text()), u'21.2')
        self.setProperty(QVariant(self.edtClientEducationSpecialty.text()), u'21.3')
        self.setProperty(QVariant(self.edtPatronSpecialty.text()), u'22.1')
        self.setProperty(QVariant(self.edtPatronWorkActive.text()), u'22.4')
        self.setProperty(QVariant(self.edtPatronWorkActiveSpecialty.text()), u'22.4.1')
        self.setProperty(QVariant(self.edtPatronWorkActivePost.text()), u'22.4.2')
        self.setProperty(QVariant(self.edtPatronWorkConditions.text()), u'22.5')
        self.setProperty(QVariant(self.edtPatronWorkPlaceAddress.text()), u'22.7')
        self.setProperty(QVariant(self.edtPatronWorkPlaceOrg.text()), u'22.6')
        self.setProperty(QVariant(self.edtPrevMSI20_8.toPlainText()), u'20.8')
        self.setProperty(QVariant(self.edtAnamnesis24.toPlainText()), u'24')
        self.setProperty(QVariant(self.edtAnamnesis25.toPlainText()), u'25')
        self.setProperty(QVariant(self.edtIPRAResult27_6.toPlainText()), u'27.6')
        self.setProperty(QVariant(self.edtHealthClientDirectionMSI.toPlainText()), u'29')
        self.setProperty(QVariant(self.edtComplaintsAboutStateHealth.toPlainText()), u'29.1')
#        self.setProperty(QVariant(self.edtInfoAboutMedicalExaminationsRequired.toPlainText()), u'30')
        self.setProperty(QVariant(self.edtHealthResortTreatment.toPlainText()), u'38')
        self.setProperty(QVariant(self.edtExtraneousSpecialMedicalCare.toPlainText()), u'39')
        self.setProperty(QVariant(self.edtRecommendedActionProsthetics.toPlainText()), u'37')
        self.setProperty(QVariant(self.edtRecommendedActionReconstructiveSurgery.toPlainText()), u'36')
        self.setProperty(QVariant(self.edtRecommendedActionRehabilitation.toPlainText()), u'35')
        self.setProperty(QVariant(self.edtNomenclatureExpense35_1.toPlainText()), u'35.1')
        self.setProperty(QVariant(self.edtNomenclatureExpense35_2.toPlainText()), u'35.2')


    @pyqtSignature('QString')
    def on_edtClientEducationOrgName_textChanged(self, text):
        self.setProperty(QVariant(self.edtClientEducationOrgName.text()), u'21.1')


    @pyqtSignature('QString')
    def on_edtClientEducationOrgAddress_textChanged(self, text):
        self.setProperty(QVariant(self.edtClientEducationOrgAddress.text()), u'21.1.1')


    @pyqtSignature('QString')
    def on_edtClientEducationCourse_textChanged(self, text):
        self.setProperty(QVariant(self.edtClientEducationCourse.text()), u'21.2')


    @pyqtSignature('QString')
    def on_edtClientEducationSpecialty_textChanged(self, text):
        self.setProperty(QVariant(self.edtClientEducationSpecialty.text()), u'21.3')


    @pyqtSignature('QString')
    def on_edtPatronSpecialty_textChanged(self, text):
        self.setProperty(QVariant(self.edtPatronSpecialty.text()), u'22.1')


    @pyqtSignature('QString')
    def on_edtPatronWorkActive_textChanged(self, text):
        self.setProperty(QVariant(self.edtPatronWorkActive.text()), u'22.4')


    @pyqtSignature('QString')
    def on_edtPatronWorkActiveSpecialty_textChanged(self, text):
        self.setProperty(QVariant(self.edtPatronWorkActiveSpecialty.text()), u'22.4.1')


    @pyqtSignature('QString')
    def on_edtPatronWorkActivePost_textChanged(self, text):
        self.setProperty(QVariant(self.edtPatronWorkActivePost.text()), u'22.4.2')


    @pyqtSignature('QString')
    def on_edtPatronWorkConditions_textChanged(self, text):
        self.setProperty(QVariant(self.edtPatronWorkConditions.text()), u'22.5')


    @pyqtSignature('QString')
    def on_edtPatronWorkPlaceAddress_textChanged(self, text):
        self.setProperty(QVariant(self.edtPatronWorkPlaceAddress.text()), u'22.7')


    @pyqtSignature('QString')
    def on_edtPatronWorkPlaceOrg_textChanged(self, text):
        self.setProperty(QVariant(self.edtPatronWorkPlaceOrg.text()), u'22.6')


    @pyqtSignature('')
    def on_edtPrevMSI20_8_textChanged(self):
        self.setProperty(QVariant(self.edtPrevMSI20_8.toPlainText()), u'20.8')


    @pyqtSignature('')
    def on_edtAnamnesis24_textChanged(self):
        self.setProperty(QVariant(self.edtAnamnesis24.toPlainText()), u'24')


    @pyqtSignature('')
    def on_edtAnamnesis25_textChanged(self):
        self.setProperty(QVariant(self.edtAnamnesis25.toPlainText()), u'25')


    @pyqtSignature('')
    def on_edtIPRAResult27_6_textChanged(self):
        self.setProperty(QVariant(self.edtIPRAResult27_6.toPlainText()), u'27.6')


    @pyqtSignature('')
    def on_edtHealthClientDirectionMSI_textChanged(self):
        self.setProperty(QVariant(self.edtHealthClientDirectionMSI.toPlainText()), u'29')


    @pyqtSignature('')
    def on_edtComplaintsAboutStateHealth_textChanged(self):
        self.setProperty(QVariant(self.edtComplaintsAboutStateHealth.toPlainText()), u'29.1')


#    @pyqtSignature('')
#    def on_edtInfoAboutMedicalExaminationsRequired_textChanged(self):
#        self.setProperty(QVariant(self.edtInfoAboutMedicalExaminationsRequired.toPlainText()), u'30')


    @pyqtSignature('')
    def on_edtHealthResortTreatment_textChanged(self):
        self.setProperty(QVariant(self.edtHealthResortTreatment.toPlainText()), u'38')


    @pyqtSignature('')
    def on_edtExtraneousSpecialMedicalCare_textChanged(self):
        self.setProperty(QVariant(self.edtExtraneousSpecialMedicalCare.toPlainText()), u'39')


    @pyqtSignature('')
    def on_edtRecommendedActionProsthetics_textChanged(self):
        self.setProperty(QVariant(self.edtRecommendedActionProsthetics.toPlainText()), u'37')


    @pyqtSignature('')
    def on_edtRecommendedActionReconstructiveSurgery_textChanged(self):
        self.setProperty(QVariant(self.edtRecommendedActionReconstructiveSurgery.toPlainText()), u'36')


    @pyqtSignature('')
    def on_edtRecommendedActionRehabilitation_textChanged(self):
        self.setProperty(QVariant(self.edtRecommendedActionRehabilitation.toPlainText()), u'35')


    @pyqtSignature('')
    def on_edtNomenclatureExpense35_1_textChanged(self):
        self.setProperty(QVariant(self.edtNomenclatureExpense35_1.toPlainText()), u'35.1')


    @pyqtSignature('')
    def on_edtNomenclatureExpense35_2_textChanged(self):
        self.setProperty(QVariant(self.edtNomenclatureExpense35_2.toPlainText()), u'35.2')


    @pyqtSignature('QString')
    def on_edtPatronQualification_textChanged(self, text):
        self.setProperty(QVariant(self.edtPatronQualification.text()), u'22.2')


    @pyqtSignature('QString')
    def on_edtPatronWorkExperience_textChanged(self, text):
        self.setProperty(QVariant(self.edtPatronWorkExperience.text()), u'22.3')


    @pyqtSignature('int')
    def on_cmbPrevMSI20_1_currentIndexChanged(self, value):
        self.setProperty(QVariant(self.cmbPrevMSI20_1.value()), u'20.1')


    @pyqtSignature('int')
    def on_cmbPrevMSI20_1_1_currentIndexChanged(self, value):
        self.setProperty(QVariant(self.cmbPrevMSI20_1_1.value()), u'20.1.1')


    @pyqtSignature('int')
    def on_cmbPrevMSI20_1_2_currentIndexChanged(self, value):
        self.setProperty(QVariant(self.cmbPrevMSI20_1_2.value()), u'20.1.2')


    @pyqtSignature('QDate')
    def on_edtPrevMSI20_2_dateChanged(self, date):
        self.setProperty(QVariant(self.edtPrevMSI20_2.date()), u'20.2')


    @pyqtSignature('int')
    def on_cmbPrevMSI20_3_currentIndexChanged(self, value):
        self.setProperty(QVariant(self.cmbPrevMSI20_3.value()), u'20.3')


    @pyqtSignature('int')
    def on_cmbPrevMSI20_4_currentIndexChanged(self, value):
        self.setProperty(QVariant(self.cmbPrevMSI20_4.value()), u'20.4')


    @pyqtSignature('QString')
    def on_edtPrevMSI20_4_16_textChanged(self, text):
        self.setProperty(QVariant(self.edtPrevMSI20_4_16.text()), u'20.4.16')


    @pyqtSignature('QString')
    def on_edtPrevMSI20_4_17_textChanged(self, text):
        self.setProperty(QVariant(self.edtPrevMSI20_4_17.text()), u'20.4.17')


    @pyqtSignature('QString')
    def on_edtPrevMSI20_5_textChanged(self, text):
        self.setProperty(QVariant(self.edtPrevMSI20_5.text()), u'20.5')


    @pyqtSignature('int')
    def on_cmbPrevMSI20_6_currentIndexChanged(self, value):
        self.setProperty(QVariant(self.cmbPrevMSI20_6.value()), u'20.6')


    @pyqtSignature('QDate')
    def on_edtPrevMSI20_7_dateChanged(self, date):
        self.setProperty(QVariant(self.edtPrevMSI20_7.date()), u'20.7')


    @pyqtSignature('QString')
    def on_edtAnamnesis23_textChanged(self, text):
        self.setProperty(QVariant(self.edtAnamnesis23.text()), u'23')


    @pyqtSignature('double')
    def on_edtAnamnesis28_1_valueChanged(self, value):
        self.setProperty(QVariant(self.edtAnamnesis28_1.value()), u'28.1')
        self.setBodyMassIndex()


    @pyqtSignature('double')
    def on_edtAnamnesis28_2_valueChanged(self, value):
        self.setProperty(QVariant(self.edtAnamnesis28_2.value()), u'28.2')
        self.setBodyMassIndex()


    def setBodyMassIndex(self):
        growth = forceDouble(self.edtAnamnesis28_1.value())
        weight = forceDouble(self.edtAnamnesis28_2.value())
        growthM = growth/100.0
        bodyMassIndex = float(weight/(growthM*growthM)) if growth > 0 else 0
        self.edtAnamnesis28_3.setValue(bodyMassIndex)


    @pyqtSignature('double')
    def on_edtAnamnesis28_3_valueChanged(self, value):
        self.setProperty(QVariant(self.edtAnamnesis28_3.value()), u'28.3')


    @pyqtSignature('int')
    def on_cmbAnamnesis28_4_currentIndexChanged(self, value):
        self.setProperty(QVariant(self.cmbAnamnesis28_4.value()), u'28.4')


    @pyqtSignature('int')
    def on_edtAnamnesis28_5_valueChanged(self, text):
        self.setProperty(QVariant(self.edtAnamnesis28_5.value()), u'28.5')


    @pyqtSignature('int')
    def on_edtAnamnesis28_6_1_valueChanged(self, text):
        self.setProperty(QVariant(self.edtAnamnesis28_6_1.value()), u'28.6.1')


    @pyqtSignature('int')
    def on_edtAnamnesis28_6_2_valueChanged(self, text):
        self.setProperty(QVariant(self.edtAnamnesis28_6_2.value()), u'28.6.2')


    @pyqtSignature('QString')
    def on_edtAnamnesis28_7_textChanged(self, text):
        self.setProperty(QVariant(self.edtAnamnesis28_7.text()), u'28.7')


    @pyqtSignature('QString')
    def on_edtAnamnesis28_8_textChanged(self, text):
        self.setProperty(QVariant(self.edtAnamnesis28_8.text()), u'28.8')


    @pyqtSignature('bool')
    def on_chkTempInvalidDocumentIsElectronic_toggled(self, checked):
        self.setProperty(QVariant(forceInt(self.chkTempInvalidDocumentIsElectronic.isChecked())), u'26.1')


    @pyqtSignature('QString')
    def on_edtTempInvalidDocumentElectronicNumber_textChanged(self, text):
        self.setProperty(QVariant(self.edtTempInvalidDocumentElectronicNumber.text()), u'26.2')


    @pyqtSignature('QString')
    def on_edtIPRANumber_textChanged(self, text):
        self.setProperty(QVariant(self.edtIPRANumber.text()), u'27.1')


    @pyqtSignature('QString')
    def on_edtIPRANumberMSI_textChanged(self, text):
        self.setProperty(QVariant(self.edtIPRANumberMSI.text()), u'27.2')


    @pyqtSignature('QDate')
    def on_edtIPRADateMSI_dateChanged(self, date):
        self.setProperty(QVariant(self.edtIPRADateMSI.date()), u'27.3')


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
    def on_chkIPRAResult27_1_toggled(self, checked):
        isChecked = self.chkIPRAResult27_1.isChecked()
        self.setIPRAResult27_4(isChecked, u'27.1')


    @pyqtSignature('bool')
    def on_chkIPRAResult27_1_1_toggled(self, checked):
        isChecked = self.chkIPRAResult27_1_1.isChecked()
        self.setIPRAResult27_4(isChecked, u'27.1.1')


    @pyqtSignature('bool')
    def on_chkIPRAResult27_1_2_toggled(self, checked):
        isChecked = self.chkIPRAResult27_1_2.isChecked()
        self.setIPRAResult27_4(isChecked, u'27.1.2')


    @pyqtSignature('bool')
    def on_chkIPRAResult27_1_3_toggled(self, checked):
        isChecked = self.chkIPRAResult27_1_3.isChecked()
        self.setIPRAResult27_4(isChecked, u'27.1.3')


    def setIPRAResult27_4(self, isChecked, propertyShortName):
        propertyValue = forceString(self.getProperty(u'27.4'))
        propertyShortNamePoint = propertyShortName + u'. '
        if isChecked:
            if propertyShortNamePoint not in propertyValue:
                for name in self.domainIPRAResult27_4:
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
        self.setProperty(QVariant(propertyValue), u'27.4')


    @pyqtSignature('bool')
    def on_chkIPRAResult27_2_toggled(self, checked):
        isChecked = self.chkIPRAResult27_2.isChecked()
        self.setIPRAResult27_5(isChecked, u'27.2')


    @pyqtSignature('bool')
    def on_chkIPRAResult27_2_1_toggled(self, checked):
        isChecked = self.chkIPRAResult27_2_1.isChecked()
        self.setIPRAResult27_5(isChecked, u'27.2.1')


    @pyqtSignature('bool')
    def on_chkIPRAResult27_2_2_toggled(self, checked):
        isChecked = self.chkIPRAResult27_2_2.isChecked()
        self.setIPRAResult27_5(isChecked, u'27.2.2')


    @pyqtSignature('bool')
    def on_chkIPRAResult27_2_3_toggled(self, checked):
        isChecked = self.chkIPRAResult27_2_3.isChecked()
        self.setIPRAResult27_5(isChecked, u'27.2.3')


    def setIPRAResult27_5(self, isChecked, propertyShortName):
        propertyValue = forceString(self.getProperty(u'27.5'))
        propertyShortNamePoint = propertyShortName + u'. '
        if isChecked:
            if propertyShortNamePoint not in propertyValue:
                for name in self.domainIPRAResult27_5:
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
        self.setProperty(QVariant(propertyValue), u'27.5')


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
        self.setProperty(QVariant(self.cmbClinicalPrognosis.value()), u'32')


    @pyqtSignature('int')
    def on_cmbRehabilitationPotential_currentIndexChanged(self, value):
        self.setProperty(QVariant(self.cmbRehabilitationPotential.value()), u'33')


    @pyqtSignature('int')
    def on_cmbRehabilitationPrognosis_currentIndexChanged(self, value):
        self.setProperty(QVariant(self.cmbRehabilitationPrognosis.value()), u'34')


    @pyqtSignature('int')
    def on_cmbOrganisationByMSI_45_currentIndexChanged(self, value):
        self.setProperty(QVariant(self.cmbOrganisationByMSI_45.value()), u'45')


    @pyqtSignature('int')
    def on_cmbClientIsLocatedOrg_currentIndexChanged(self, value):
        self.setProperty(QVariant(self.cmbClientIsLocatedOrg.value()), u'13.x')


    @pyqtSignature('QDate')
    def on_edtAdditionalDataRegistrationDate_dateChanged(self, date):
        self.setProperty(QVariant(self.edtAdditionalDataRegistrationDate.date()), u'46')


    @pyqtSignature('QDate')
    def on_edtAdditionalDataExaminationDate_dateChanged(self, date):
        self.setProperty(QVariant(self.edtAdditionalDataExaminationDate.date()), u'47')


    @pyqtSignature('int')
    def on_cmbAdditionalDataResultMSI_currentIndexChanged(self, value):
        self.setProperty(QVariant(self.cmbAdditionalDataResultMSI.value()), u'48')


    @pyqtSignature('int')
    def on_cmbAdditionalDataDisabilityGroup_currentIndexChanged(self, value):
        self.setProperty(QVariant(self.cmbAdditionalDataDisabilityGroup.value()), u'49')


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


    @pyqtSignature('')
    def on_actPortal_Doctor_triggered(self):
        templateId = None
        result = QtGui.qApp.db.getRecordEx('rbPrintTemplate', 'id',
                                           '`default` LIKE "%s" AND deleted = 0' % ('%/EMK_V3/indexV2.php%'))
        context = CInfoContext()
        eventInfo = context.getInstance(CEventInfo, self.eventId)
        data = {'event': eventInfo, 'client': eventInfo.client}

        if result:
            templateId = result.value('id').toString()
            if templateId:
                QtGui.qApp.call(self, applyTemplate, (self, templateId, data))
            else:
                QtGui.QMessageBox.information(self, u'Ошибка', u'Шаблон для перехода на портал врача не найден',
                                              QtGui.QMessageBox.Close, QtGui.QMessageBox.Close)
        else:
            QtGui.QMessageBox.information(self, u'Ошибка', u'Шаблон для перехода на портал врача не найден',
                                          QtGui.QMessageBox.Close, QtGui.QMessageBox.Close)


    @pyqtSignature('')
    def on_actEditAction_triggered(self):
        indexAction = self.tblAmbCardDiagnosticActions_30.currentIndex()
        if indexAction.isValid():
            rowAction = indexAction.row()
            if rowAction >= 0 and rowAction < len(self.modelAmbCardDiagnosticActions_30.idList()):
                actionId = self.modelAmbCardDiagnosticActions_30._idList[rowAction]
                if actionId and self.eventId == self.modelAmbCardDiagnosticActions_30.eventIdDict.get(actionId, None):
                    newActionId = self.editAction(actionId)
                    if newActionId:
                        self.on_cmdAmbCardDiagnosticButtonBox_30_apply()
                        actionIndex = self.tblAboutMedicalExaminationsRequiredAction.currentIndex()
                        if actionIndex.isValid():
                            actionRow = actionIndex.row()
                            self.modelAboutMedicalExaminationsRequiredAction.reset()
                            self.tblAboutMedicalExaminationsRequiredAction.setCurrentRow(actionRow)


    def editAction(self, actionId):
        dialog = CActionEditDialog(self)
        try:
            dialog.load(actionId)
            if dialog.exec_():
                return dialog.itemId()
            return None
        finally:
            dialog.deleteLater()


    @pyqtSignature('')
    def on_actDeleteAction_triggered(self):
        indexAction = self.tblAmbCardDiagnosticActions_30.currentIndex()
        if indexAction.isValid():
            rowAction = indexAction.row()
            if rowAction >= 0 and rowAction < len(self.modelAmbCardDiagnosticActions_30.idList()):
                actionId = self.modelAmbCardDiagnosticActions_30._idList[rowAction]
                if actionId and self.eventId == self.modelAmbCardDiagnosticActions_30.eventIdDict.get(actionId, None):
                    if self.deleteAction(actionId):
                        self.on_cmdAmbCardDiagnosticButtonBox_30_apply()
                        actionIndex = self.tblAboutMedicalExaminationsRequiredAction.currentIndex()
                        if actionIndex.isValid():
                            actionRow = actionIndex.row()
                            self.modelAboutMedicalExaminationsRequiredAction.reset()
                            self.tblAboutMedicalExaminationsRequiredAction.setCurrentRow(actionRow)


    def deleteAction(self, actionId):
        if QtGui.QMessageBox.question(self,
                u'Удаление Действия!', u'Вы действительно хотите удалить Действие?',
                QtGui.QMessageBox.Yes|QtGui.QMessageBox.No,
                QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes:
            db = QtGui.qApp.db
            table = db.table('Action')
            tableEvent = db.table('Event')
            record = db.getRecordEx(table, '*', [table['id'].eq(actionId), table['deleted'].eq(0)])
            payStatusAction = forceInt(record.value('payStatus')) if record else 0
            isPayStatus = forceBool(payStatusAction)
            payStatusEvent = False
            if self.eventId and not isPayStatus:
                recordEvent = db.getRecordEx(tableEvent, [tableEvent['payStatus'], tableEvent['id']], [tableEvent['id'].eq(self.eventId), tableEvent['deleted'].eq(0)])
                payStatusEvent = forceInt(recordEvent.value('payStatus')) if recordEvent else 0
            isPayStatus = isPayStatus and forceBool(payStatusEvent)
            if isPayStatus:
                message = u'%s включено в счёт\nи его данные не могут быть изменены!'%(u'Данное Действие' if payStatusAction else (u'Событие, содержащее данное Действие,' if payStatusEvent else u'Данное Действие'))
                QtGui.QMessageBox.critical(self, u'Внимание!', message)
                return
            createPersonId = forceRef(record.value('createPerson_id')) if record else None
            if actionId and createPersonId and QtGui.qApp.userId == createPersonId and not isPayStatus:
                tableActionProperty = db.table('ActionProperty')
                filter = [tableActionProperty['action_id'].eq(actionId), tableActionProperty['deleted'].eq(0)]
                db.deleteRecord(tableActionProperty, filter)

                tableActionExecutionPlan = db.table('Action_ExecutionPlan')
                filter = [tableActionExecutionPlan['master_id'].eq(actionId), tableActionExecutionPlan['deleted'].eq(0)]
                db.deleteRecord(tableActionExecutionPlan, filter)

                tableStockMotion = db.table('StockMotion')
                tableActionNR = db.table('Action_NomenclatureReservation')
                filter = [tableActionNR['action_id'].eq(actionId)]
                reservationIdList = db.getDistinctIdList(tableActionNR, [tableActionNR['reservation_id']], filter)
                if reservationIdList:
                    filter = [tableStockMotion['id'].inlist(reservationIdList), tableStockMotion['deleted'].eq(0)]
                    db.deleteRecord(tableStockMotion, filter)

                filter = [table['id'].eq(actionId), table['deleted'].eq(0)]
                stockMotionIdList = db.getDistinctIdList(table, [table['stockMotion_id']], filter)
                if stockMotionIdList:
                    tableStockMotionItem = db.table('StockMotion_Item')
                    filter = [tableStockMotionItem['master_id'].inlist(stockMotionIdList), tableStockMotionItem['deleted'].eq(0)]
                    db.deleteRecord(tableStockMotionItem, filter)
                    filter = [tableStockMotion['id'].inlist(stockMotionIdList), tableStockMotion['deleted'].eq(0)]
                    db.deleteRecord(tableStockMotion, filter)

                db.deleteRecord(table, [table['id'].eq(actionId)])
                return True
        return False


    @pyqtSignature('double')
    def on_edtAmount_valueChanged(self, value):
        actionType = self.action.getType()
        if actionType.defaultPlannedEndDate == CActionType.dpedBegDatePlusAmount:
            begDate = self.edtBegDate.date()
            amountValue = int(value)
            date = begDate.addDays(amountValue-1) if begDate and amountValue else QDate()
            self.edtPlannedEndDate.setDate(date)


    @pyqtSignature('')
    def on_btnAttachedFiles_pressed(self):
        if self.btnAttachedFiles.getIsSaveModel():
            self.setIsDirty(True)


    @pyqtSignature('')
    def on_btnSelectOrg_clicked(self):
        orgId = selectOrganisation(self, self.cmbOrg.value(), False, self.cmbOrg.filter)
        self.cmbOrg.updateModel()
        if orgId:
            self.cmbOrg.setValue(orgId)


    @pyqtSignature('int')
    def on_cmbPerson_currentIndexChanged(self, value):
        self.setPersonId(self.cmbPerson.value())


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
        if self.action.getType().closeEvent:
            self.setEventDate(date)


    @pyqtSignature('int')
    def on_cmbStatus_currentIndexChanged(self, index):
        actionStatus = self.cmbStatus.value()
        if actionStatus in (CActionStatus.finished, CActionStatus.canceled, CActionStatus.refused):
            if not self.edtEndDate.date():
                now = QDateTime.currentDateTime()
                self.edtEndDate.setDate(now.date())
                if self.edtEndTime.isVisible():
                    self.edtEndTime.setTime(now.time())
            if actionStatus in (CActionStatus.canceled, CActionStatus.refused) and not self.cmbSetPerson.value():
                if QtGui.qApp.userId and QtGui.qApp.userSpecialityId:
                    self.cmbPerson.setValue(QtGui.qApp.userId)
                else:
                    self.cmbPerson.setValue(self.cmbSetPerson.value())


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
        eventInfo = context.getInstance(CEventInfo, self.eventId)
        eventByRecord = CCookedEventInfo(context, self.eventId, self.recordEvent)
        eventActions = eventInfo.actions

        diagnosis_31_1 = []
        for record in self.modelDiagnosisDisease_31_1.items():
            diag = CDiagnosticInfo(context, forceRef(record.value('id')))
            diag.initByRecord(record)
            diag.setOkLoaded()
            diag._diagnosis.setOkLoaded()
            diag._diagnosis._MKB = CMKBInfo(context, forceStringEx(record.value('MKB')))
            diagnosis_31_1.append(diag)
        diagnosis_31_3 = []
        for record in self.modelDiagnosisDisease_31_3.items():
            diag = CDiagnosticInfo(context, forceRef(record.value('id')))
            diag.initByRecord(record)
            diag.setOkLoaded()
            diag._diagnosis.setOkLoaded()
            diag._diagnosis._MKB = CMKBInfo(context, forceStringEx(record.value('MKB')))
            diagnosis_31_3.append(diag)
        diagnosis_31_4 = []
        for record in self.modelDiagnosisDisease_31_4.items():
            diag = CDiagnosticInfo(context, forceRef(record.value('id')))
            diag.initByRecord(record)
            diag.setOkLoaded()
            diag._diagnosis.setOkLoaded()
            diag._diagnosis._MKB = CMKBInfo(context, forceStringEx(record.value('MKB')))
            diagnosis_31_4.append(diag)
        diagnosis_31_6 = []
        for record in self.modelDiagnosisDisease_31_6.items():
            diag = CDiagnosticInfo(context, forceRef(record.value('id')))
            diag.initByRecord(record)
            diag.setOkLoaded()
            diag._diagnosis.setOkLoaded()
            diag._diagnosis._MKB = CMKBInfo(context, forceStringEx(record.value('MKB')))
            diagnosis_31_6.append(diag)

        actionItems = self.modelAboutMedicalExaminationsRequiredAction.items()
        aboutMedicalExaminationsRequiredAction = CLocActionPropertyActionsInfoList(context, actionItems)
        medicamentItems = self.modelMedicament.items()
        medicament = CLocActionPropertyMedicamentInfoList(context, medicamentItems)
        self.modelMembersMSIPerson.saveItems()
        actionRecord = self.getRecord()
        action = CCookedActionInfo(context, actionRecord, self.action)
        action._isDirty = self.isDirty()
        currentAction = CActionRecordItem(actionRecord, action)
        data = {'event': eventInfo,
                'eventByRecord': eventByRecord,
                'diagnosis_31_1': diagnosis_31_1,
                'diagnosis_31_3': diagnosis_31_3,
                'diagnosis_31_4': diagnosis_31_4,
                'diagnosis_31_6': diagnosis_31_6,
                'aboutMedicalExaminationsRequiredAction': aboutMedicalExaminationsRequiredAction,
                'medicament': medicament,
                'action': action,
                'client': eventByRecord.client,
                'actions': eventActions,
                'currentActionIndex': 0,
                'currentAction': currentAction,
                'tempInvalid': None
                }
        applyTemplate(self, templateId, data, signAndAttachHandler=self.btnAttachedFiles.getSignAndAttachHandler())

    
    def getPersonIdAndDate(self, action):
        actionPersonId = forceRef(action.getRecord().value('person_id'))
        if actionPersonId:
            personId = actionPersonId
        elif QtGui.qApp.userSpecialityId:
            personId = QtGui.qApp.userId
        else:
            personId = forceRef(action.getRecord().value('setPerson_id'))

        actionEndDate = forceDate(action.getRecord().value('endDate'))
        if actionEndDate:
            date = actionEndDate
        else:
            date = forceDate(action.getRecord().value('directionDate'))
        return personId, date
    

    def getPrevActionId(self, isPersonId=True):
        actionTypeId = self.action.getType().id
        actionId = forceRef(self.action.getRecord().value('id')) if self.action.getRecord() else None
        personId, date = self.getPersonIdAndDate(self.action)
        return self.findPrevActionId(actionTypeId, actionId, personId, date, isPersonId=isPersonId)


    def findPrevActionId(self, actionTypeId, actionId, personId, date, isPersonId=True):
        if not self.clientId:
            return None
        db = QtGui.qApp.db
        tableEvent  = db.table('Event')
        tableAction = db.table('Action')
        tableActionTypeTestator = db.table('ActionType_Testator')
        table = tableAction.leftJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))
        table = table.leftJoin(tableActionTypeTestator,
                               tableActionTypeTestator['testator_id'].eq(tableAction['actionType_id']))
        cond = [tableAction['deleted'].eq(0),
                tableEvent['deleted'].eq(0),
                db.joinOr([tableAction['actionType_id'].eq(actionTypeId),
                           tableActionTypeTestator['master_id'].eq(actionTypeId)
                          ]
                         ),
                tableEvent['client_id'].eq(self.clientId)
               ]
        cond.append(tableAction['endDate'].lt(date.addDays(1)))
        if isPersonId:
            cond.append(tableAction['person_id'].eq(personId))
        if actionId:
            cond.append(tableAction['id'].ne(actionId))
        return db.getRecordEx(table, u'*', cond, u'Action.endDate DESC, Action.id DESC')
    

    def setRecordPrevAction(self, templateAction):
        if not templateAction:
            return
        self.setProperties()
        record = templateAction.getRecord()
        prevActionEventId = forceRef(record.value('event_id'))
        prevActionId = forceRef(record.value('id'))
        recordEvent = None
        db = QtGui.qApp.db
        if prevActionEventId:
            tableEvent = db.table('Event')
            recordEvent = db.getRecordEx(tableEvent, '*', [tableEvent['id'].eq(prevActionEventId), tableEvent['deleted'].eq(0)])
        prevActionEventId = forceRef(recordEvent.value('id')) if recordEvent else None
        self.isRelationRepresentativeSetClientId = True
        self.cmbClientRelationRepresentative.clear()
        self.cmbClientRelationRepresentative.setClientId(self.clientId)
        self.cmbClientRelationRepresentative.setValue(forceRef(recordEvent.value('relative_id')) if recordEvent else None)
        self.tabNotes.cmbClientRelationConsents.clear()
        self.tabNotes.cmbClientRelationConsents.setClientId(self.clientId)
        self.tabNotes.cmbClientRelationConsents.setValue(forceRef(recordEvent.value('relative_id')) if recordEvent else None)
        self.isRelationRepresentativeSetClientId = False
        self.modelTempInvalidYear.setAction(self.action)
        self.modelTempInvalidYear.loadPrevActionItems(self.clientId)
        self.modelMembersMSIPerson.setAction(self.action)
        self.modelMembersMSIPerson.loadItems()
        self.modelDiagnosisDisease_31_1.setAction(self.action)
        self.modelDiagnosisDisease_31_1.loadPrevActionItems(prevActionEventId, self.eventId)
        self.modelDiagnosisDisease_31_3.setAction(self.action)
        self.modelDiagnosisDisease_31_3.loadPrevActionItems(prevActionEventId, self.eventId)
        self.modelDiagnosisDisease_31_4.setAction(self.action)
        self.modelDiagnosisDisease_31_4.loadPrevActionItems(prevActionEventId, self.eventId)
        self.modelDiagnosisDisease_31_6.setAction(self.action)
        self.modelDiagnosisDisease_31_6.loadPrevActionItems(prevActionEventId, self.eventId)
        actionId = self.itemId()
        self.modelMedicament.loadPrevActionItems(prevActionId, actionId)
        self.updateAssignedMedicament(actionId)
        #self.modelElectronicMedicalDocument.reset()
        self.modelAboutMedicalExaminationsRequiredAction.loadPrevActionItems(prevActionId, actionId)
        self.modelAboutMedicalExaminationsRequiredProperties.setMasterId(actionId)
        self.tblAboutMedicalExaminationsRequiredAction.setCurrentRow(0)
        self.tblDiagnosisDisease_31_1.setRowHidden(1, True)
        self.tblDiagnosisDisease_31_1.resizeColumnToContents(self.tblDiagnosisDisease_31_1.columnHint)
        self.tblDiagnosisDisease_31_3.resizeColumnsToContents()
        self.tblDiagnosisDisease_31_3.resizeRowsToContents()
        self.tblDiagnosisDisease_31_4.resizeColumnsToContents()
        self.tblDiagnosisDisease_31_4.resizeRowsToContents()
        self.tblDiagnosisDisease_31_6.resizeColumnsToContents()
        self.tblDiagnosisDisease_31_6.resizeRowsToContents()


    @pyqtSignature('')
    def on_btnLoadPrevAction_clicked(self):
        try:
            try:
                if QtGui.qApp.userHasRight(urCopyPrevAction):
                    templateRecord = self.getPrevActionId(False)
                    if templateRecord:
                        templateAction = CAction(record=templateRecord)
                        self.action.updateByAction(templateAction)
                        self.setRecordPrevAction(templateAction)
            except:
                QtGui.QMessageBox.critical( self,
                                            u'Внимание!',
                                            u'Информация не была скопирована.',
                                            QtGui.QMessageBox.Ok)
                raise
            self.setIsDirty(True)
            QtGui.QMessageBox.information( self,
                           u'Внимание!',
                           u'Информация была успешно скопирована.',
                           QtGui.QMessageBox.Ok,
                           QtGui.QMessageBox.Ok)
        except Exception, e:
            QtGui.qApp.logCurrentException()
            QtGui.QMessageBox.critical( self,
                                        u'',
                                        exceptionToUnicode(e),
                                        QtGui.QMessageBox.Close)


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
                                             personId)
            if record:
                specialityId = forceRef(record.value('speciality_id'))
                serviceId = forceRef(record.value('service_id'))
                provinceServiceId = forceRef(record.value('provinceService_id'))
                otherServiceId = forceRef(record.value('otherService_id'))
                financeId = forceRef(record.value('finance_id'))
                tariffCategoryId = forceRef(record.value('tariffCategory_id'))
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
        self.shortNameList = [u'41', u'42', u'43', u'44']


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
            if shortName in self.shortNameList or u'44.' in shortName:
                if shortName and shortName not in self.shortNameList:
                    self.shortNameList.append(shortName)


    def setData(self, index, value, role=Qt.EditRole):
        row = index.row()
        if row >= len(self.shortNameList):
            return False
        return CInDocTableModel.setData(self, index, value, role)


    def removeRows(self, row, count, parentIndex = QModelIndex()):
        if 0 <= row and row+count <= len(self._items):
            self.beginRemoveRows(parentIndex, row, row+count-1)
            del self._items[row:row+count]
            self.endRemoveRows()
            self.saveItems()
            return True
        else:
            return False


    def removeRow(self, row, parentIndex = QModelIndex()):
        return self.removeRows(row, 1, parentIndex)


    def loadItems(self, masterId = None):
        self._items = []
        if self.eventEditor and self.action:
            items = {}
            for property in self.action._propertiesById.itervalues():
                propertyType = property.type()
                shortName = trim(propertyType.shortName)
                if shortName in self.shortNameList or u'44.' in shortName:
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
        action = self.action if self.action else self.eventEditor.action
        if self.eventEditor and action:
            for idx, shortName in enumerate(self.shortNameList):
                if shortName:
                    for propertyTypeName, property in action._propertiesByName.items():
                        propertyType = property.type()
                        if trim(shortName) == trim(propertyType.shortName):
                            del self.eventEditor.action[propertyType.name]
            if self.eventEditor and self._items is not None and self.eventEditor.action:
                shortNameListLen = len(self.shortNameList)
                for idx, record in enumerate(self._items):
                    if idx < shortNameListLen:
                        shortName = self.shortNameList[idx]
                    else:
                        shortName = u'44.' + forceString(idx - shortNameListLen + 1)
                        if shortName and shortName not in self.shortNameList:
                            self.shortNameList.append(shortName)
                    self.eventEditor.setProperty(QVariant(forceInt(record.value('id'))), shortName)
                self.action = self.eventEditor.action


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
            MKB = forceStringEx(record.value('MKB')) if record else u''
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
        if row > 19:
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


    def removeRows(self, row, count, parentIndex = QModelIndex()):
        if 0 <= row and row+count <= len(self._items):
            self.beginRemoveRows(parentIndex, row, row+count-1)
            del self._items[row:row+count]
            self.endRemoveRows()
            self.saveItems()
            return True
        else:
            return False


    def removeRow(self, row, parentIndex = QModelIndex()):
        return self.removeRows(row, 1, parentIndex)


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
            currentDate = QDate.currentDate() #0013020
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
                    for idx in xrange(20):
                        begDate = self.eventEditor.getPropertyValue(items, u'26.%s.2'%(forceString(idx+1)), QDate)
                        endDate = self.eventEditor.getPropertyValue(items, u'26.%s.3'%(forceString(idx+1)), QDate)
                        if begDate or endDate:
                            duration = self.eventEditor.getPropertyValue(items, u'26.%s.4'%(forceString(idx+1)), int)
                            MKB = self.eventEditor.getPropertyValue(items, u'26.%s.5'%(forceString(idx+1)), QString)
                            item = self.getEmptyRecord()
                            item.setValue('begDate', toVariant(begDate))
                            item.setValue('endDate', toVariant(endDate))
                            item.setValue('duration', toVariant(duration))
                            item.setValue('MKB', toVariant(MKB))
                            self._items.append(item)
        self.reset()
    
    
    def loadPrevActionItems(self, masterId):
        self._items = []
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
                for idx in xrange(20):
                    begDate = self.eventEditor.getPropertyValue(items, u'26.%s.2'%(forceString(idx+1)), QDate)
                    endDate = self.eventEditor.getPropertyValue(items, u'26.%s.3'%(forceString(idx+1)), QDate)
                    if begDate or endDate:
                        duration = self.eventEditor.getPropertyValue(items, u'26.%s.4'%(forceString(idx+1)), int)
                        MKB = self.eventEditor.getPropertyValue(items, u'26.%s.5'%(forceString(idx+1)), QString)
                        item = self.getEmptyRecord()
                        item.setValue('begDate', toVariant(begDate))
                        item.setValue('endDate', toVariant(endDate))
                        item.setValue('duration', toVariant(duration))
                        item.setValue('MKB', toVariant(MKB))
                        self._items.append(item)
        elif masterId and not self.action or not forceRef(self.action.getRecord().value('id')):
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
            currentDate = QDate.currentDate() #0013020
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
        self.reset()


    def saveItems(self, masterId):
        if self.eventEditor and self.eventEditor.action:
            for idx, record in enumerate(self._items):
                self.eventEditor.setProperty(QVariant(forceInt(record.value('cnt'))), u'26.%s.1'%(forceString(idx+1)))
                self.eventEditor.setProperty(QVariant(forceDate(record.value('begDate'))), u'26.%s.2'%(forceString(idx+1)))
                self.eventEditor.setProperty(QVariant(forceDate(record.value('endDate'))), u'26.%s.3'%(forceString(idx+1)))
                self.eventEditor.setProperty(QVariant(forceInt(record.value('duration'))), u'26.%s.4'%(forceString(idx+1)))
                self.eventEditor.setProperty(QVariant(forceStringEx(record.value('MKB'))), u'26.%s.5'%(forceString(idx+1)))
            rowCount = self.realRowCount()
            if rowCount < 20:
                noRows = 20 - rowCount
                idx = rowCount + 1
                while noRows > 0:
                    self.delProperty(u'26.%s.1'%(forceString(idx)))
                    self.delProperty(u'26.%s.2'%(forceString(idx)))
                    self.delProperty(u'26.%s.3'%(forceString(idx)))
                    self.delProperty(u'26.%s.4'%(forceString(idx)))
                    self.delProperty(u'26.%s.5'%(forceString(idx)))
                    idx += 1
                    noRows -= 1
            self.action = self.eventEditor.action


    def delProperty(self, shortName):
        shortName = trim(shortName)
        if self.eventEditor.action and self.action and shortName:
            for propertyTypeName, property in self.action._propertiesByName.items():
                propertyType = property.type()
                if shortName == trim(propertyType.shortName):
                    del self.eventEditor.action[propertyType.name]


class CAnamnesisActionsTableModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self.actionsPropertiesRegistry = {}
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
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled
    
    
    def sort(self, col, sortOrder=Qt.AscendingOrder):
        if self._idList:
            db = QtGui.qApp.db
            table = db.table('Action')
            cond = [table['id'].inlist(self._idList)]
            colClass = self.cols()[col]
            colName = colClass.fields()[0]
            if col in [1, 7, 8]:
                tableSort = db.table('ActionType' if col==1 else colClass.tableName).alias('fieldSort')
                table = table.leftJoin(tableSort, tableSort['id'].eq(table[colName]))
                colName = 'fieldSort.name'
            order = '{} {}'.format(colName, u'DESC' if sortOrder else u'ASC')
            self._idList = db.getIdList(table, table['id'].name() , where = cond, order=order)
            self.reset()


class CMedicamentActionsTableModel(CInDocTableModel):
    class CLocSmnnDataInDocTableCol(CInDocTableCol):
        def __init__(self, title, fieldName, fieldNameCol, width, **params):
            CInDocTableCol.__init__(self, title, fieldName, width, **params)
            self.fieldNameCol = fieldNameCol
            self.cache = {}

        def toString(self, val, record):
            smnnUUID = forceStringEx(val)
            if smnnUUID:
                smnnInfo = self.cache.get(smnnUUID, {})
                if smnnInfo:
                    return toVariant(smnnInfo.get(self.fieldNameCol, u''))
                else:
                    smnnInfo = {}
                    db = QtGui.qApp.db
                    tableEsklp_Smnn = db.table('esklp.Smnn')
                    record = db.getRecordEx(tableEsklp_Smnn, [tableEsklp_Smnn['code'], tableEsklp_Smnn['mnn'], tableEsklp_Smnn['form']], [tableEsklp_Smnn['UUID'].eq(smnnUUID)])
                    if record:
                        smnnInfo['code'] = forceStringEx(record.value('code'))
                        smnnInfo['mnn'] = forceStringEx(record.value('mnn'))
                        smnnInfo['form'] = forceStringEx(record.value('form'))
                        self.cache[smnnUUID] = smnnInfo
                        return toVariant(smnnInfo.get(self.fieldNameCol, u''))
            return QVariant()

        def invalidateRecordsCache(self):
            self.cache.invalidate()

    class CLocMnnDataInDocTableCol(CInDocTableCol):
        def __init__(self, title, fieldName, fieldNameCol, width, **params):
            CInDocTableCol.__init__(self, title, fieldName, width, **params)
            self.fieldNameCol = fieldNameCol
            self.cache = {}

        def toString(self, val, record):
            smnnUUID = forceStringEx(val)
            if smnnUUID:
                smnnInfo = self.cache.get(smnnUUID, {})
                if smnnInfo:
                    return toVariant(smnnInfo.get(self.fieldNameCol, u''))
                else:
                    smnnInfo = {}
                    db = QtGui.qApp.db
                    tableEsklp_Smnn = db.table('esklp.Smnn')
                    record = db.getRecordEx(tableEsklp_Smnn, [tableEsklp_Smnn['code'], tableEsklp_Smnn['mnn'], tableEsklp_Smnn['form']], [tableEsklp_Smnn['UUID'].eq(smnnUUID)])
                    if record:
                        smnnInfo['code'] = forceStringEx(record.value('code'))
                        smnnInfo['mnn'] = forceStringEx(record.value('mnn'))
                        smnnInfo['form'] = forceStringEx(record.value('form'))
                        self.cache[smnnUUID] = smnnInfo
                        return toVariant(smnnInfo.get(self.fieldNameCol, u''))
            return QVariant()

        def createEditor(self, parent):
            editor = CESKLPSmnnComboBox(parent)
            return editor

        def setEditorData(self, editor, value, record):
            editor.setValue(forceStringEx(value))


        def getEditorData(self, editor):
            return toVariant(editor.value())

        def invalidateRecordsCache(self):
            self.cache.invalidate()

    class CLocDosageInDocTableCol(CInDocTableCol):
        def __init__(self, title, fieldName, width, **params):
            CInDocTableCol.__init__(self, title, fieldName, width, **params)
            self.cache = {}

        def toString(self, val, record):
            smnnUUID = forceStringEx(val)
            if smnnUUID:
                grls_value = self.cache.get(smnnUUID, u'')
                if grls_value:
                    return toVariant(grls_value)
                else:
                    db = QtGui.qApp.db
                    tableEsklp_Smnn = db.table('esklp.Smnn')
                    tableEsklp_Smnn_Dosage = db.table('esklp.Smnn_Dosage')
                    queryTable = tableEsklp_Smnn.innerJoin(tableEsklp_Smnn_Dosage, tableEsklp_Smnn_Dosage['master_id'].eq(tableEsklp_Smnn['id']))
                    record = db.getRecordEx(queryTable, [tableEsklp_Smnn_Dosage['grls_value']], [tableEsklp_Smnn['UUID'].eq(smnnUUID)])
                    if record:
                        grls_value = forceStringEx(record.value('grls_value'))
                        self.cache[smnnUUID] = grls_value
                        return toVariant(grls_value)
            return QVariant()

        def invalidateRecordsCache(self):
            self.cache.invalidate()

    class CLocTextInDocTableCol(CInDocTableCol):
        def __init__(self, title, fieldName, width, **params):
            CInDocTableCol.__init__(self, title, fieldName, width, **params)

        def toString(self, value, record):
            val = forceStringEx(value)
            if val:
                return toVariant(u'' if val == u'0' else val)
            else:
                return QVariant()

        def setEditorData(self, editor, value, record):
            val = forceStringEx(value)
            editor.setText(u'' if val == u'0' else val)

        def getEditorData(self, editor):
            text = trim(editor.text())
            if text:
                return toVariant(u'' if text == u'0' else text)
            else:
                return QVariant()

        def alignment(self):
            return QVariant(Qt.AlignLeft + Qt.AlignTop)

    Col_SmnnCode = 0
    Col_SmnnMnn = 1
    Col_SmnnForm = 2
    Col_SmnnDosage = 3
    Col_SmnnDuration = 4
    Col_SmnnPeriodicity = 5
    Col_SmnnAliquoticity = 6

    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'Action_ESKLP_Smnn', 'id', 'master_id', parent)
        self.addHiddenCol('action_id')
        self.addHiddenCol('actionPropertyNomenclature_id')
        self.addCol(self.CLocSmnnDataInDocTableCol(u'Код узла СМНН', 'smnnUUID', 'code', 20)).setReadOnly()
        self.addCol(self.CLocMnnDataInDocTableCol(u'Стандартизованное МНН', 'smnnUUID', 'mnn', 20))
        self.addCol(self.CLocSmnnDataInDocTableCol(u'Стандартизованная лекарственная форма', 'smnnUUID', 'form', 20)).setReadOnly()
        self.addCol(self.CLocDosageInDocTableCol(u'Стандартизованная лекарственная доза', 'smnnUUID', 20)).setReadOnly()
        self.addCol(self.CLocTextInDocTableCol(u'Продолжительность приема', 'duration', 20))
        self.addCol(self.CLocTextInDocTableCol(u'Кратность курсов лечения', 'periodicity', 20))
        self.addCol(self.CLocTextInDocTableCol(u'Кратность приема', 'aliquoticity', 20))
        #self.setEnableAppendLine(False)
        self.readOnly = False
        self.action = None
        self.eventEditor = None


    def cellReadOnly(self, index):
        row = index.row()
        column = index.column()
        if 0 <= row < len(self._items):
            if column in (self.Col_SmnnCode, self.Col_SmnnForm, self.Col_SmnnDosage):
                return True
            elif column == self.Col_SmnnMnn:
                record = self._items[row]
                if record and forceRef(record.value('action_id')):
                    return True
            if column in (self.Col_SmnnDuration, self.Col_SmnnPeriodicity, self.Col_SmnnAliquoticity):
                record = self._items[row]
                if not record or not forceStringEx(record.value('smnnUUID')):
                    return True
        elif column != self.Col_SmnnMnn:
            return True
        return False


    def flags(self, index):
        if self.readOnly:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        column = index.column()
        flags = self._cols[column].flags()
        if self.cellReadOnly(index):
            flags = flags & (~Qt.ItemIsEditable) & (~Qt.ItemIsUserCheckable)
        return flags


    def getEmptyRecord(self):
        result = QtGui.qApp.db.table('Action_ESKLP_Smnn').newRecord()
#        result.setValue('duration', toVariant())
#        result
#        result
        return result


    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        if role == Qt.FontRole:
            row = index.row()
            if 0 <= row < len(self._items):
                record = self._items[row]
                if record and not forceRef(record.value('action_id')):
                    result = QtGui.QFont()
                    result.setBold(True)
                    return QVariant(result)
        return CInDocTableModel.data(self, index, role)


    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.EditRole:
            column = index.column()
            row = index.row()
            if row == len(self._items):
                if value.isNull() or (column == self.Col_SmnnMnn and not forceStringEx(value)):
                    return False
                self._addEmptyItem()
            if column == self.Col_SmnnMnn and not forceStringEx(value):
                return False
            record = self._items[row]
            col = self._cols[column]
            record.setValue(col.fieldName(), value)
            self.emitCellChanged(row, column)
            return True
        return CInDocTableModel.setData(self, index, value, role)


    def addItem(self, item):
        self._items.append(item)


    def getItemToActionId(self, findActionId):
        if findActionId:
            for idx, record in enumerate(self._items):
                actionId = forceRef(record.value('action_id'))
                if actionId == findActionId:
                    return record
        return None


    def getRowToActionId(self, findActionId):
        if findActionId:
            for row, record in enumerate(self._items):
                actionId = forceRef(record.value('action_id'))
                if actionId == findActionId:
                    return row
        return -1


    def getActionIdToRow(self, findRow):
        for row, record in enumerate(self._items):
            if findRow == row:
                return forceRef(record.value('action_id'))
        return None


    def getActionIdList(self):
        actionIdList = []
        for idx, record in enumerate(self._items):
            actionId = forceRef(record.value('action_id'))
            if actionId and actionId not in actionIdList:
                actionIdList.append(actionId)
        return actionIdList


    def getPropertyIdList(self):
        propertyIdList = []
        for idx, record in enumerate(self._items):
            propertyId = forceRef(record.value('actionPropertyNomenclature_id'))
            if propertyId and propertyId not in propertyIdList:
                propertyIdList.append(propertyId)
        return propertyIdList


    def setEventEditor(self, eventEditor):
        self.eventEditor = eventEditor


    def setAction(self, action):
        self.action = action


    def removeRows(self, row, count, parentIndex = QModelIndex()):
        if 0<=row and row+count<=len(self._items):
            self.beginRemoveRows(parentIndex, row, row+count-1)
            del self._items[row:row+count]
            self.endRemoveRows()
            return True
        else:
            return False


    def removeRow(self, row, parentIndex = QModelIndex()):
        result = self.removeRows(row, 1, parentIndex)
        QObject.parent(self).updateAssignedMedicament()
        return result


    def setReadOnly(self, value=True):
        self.readOnly = value

    
    def loadPrevActionItems(self, prevMasterId, masterId):
        self._items = []
        if prevMasterId:
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
            filter = [table[self._masterIdFieldName].eq(prevMasterId)]
            if self._filter:
                filter.append(self._filter)
            if table.hasField('deleted'):
                filter.append(table['deleted'].eq(0))
            if self._idxFieldName:
                order = [self._idxFieldName, self._idFieldName]
            else:
                order = [self._idFieldName]
            prevRecords = db.getRecordList(table, cols, filter, order)
            for record in prevRecords:
                record.setValue('id', toVariant(None))
                record.setValue(self._masterIdFieldName, toVariant(None))
                newRecord = self.getEmptyRecord()
                for i in xrange(record.count()):
                    fieldName = forceStringEx(record.fieldName(i))
                    if fieldName not in ('id', self._masterIdFieldName, 'createDatetime', 'createPerson_id', 'modifyDatetime', 'modifyPerson_id', 'deleted'):
                        newRecord.setValue(fieldName, record.value(fieldName))
                    newRecord.setValue(self._masterIdFieldName, toVariant(masterId))
                self._items.append(newRecord)
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
        self.reset()


    def emitRowsChanged(self, begRow, endRow):
        CInDocTableModel.emitRowsChanged(self, begRow, endRow)
        for idx, record in enumerate(self._items):
            record.setValue(self._idxFieldName, toVariant(idx))


class CAssignedMedicamentActionsCheckTableModel(CTableModel):
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

    class CAssignedMedicamentCol(CCol):
        def __init__(self, title, fields, defaultWidth, alignment='l'):
            CCol.__init__(self, title, fields, defaultWidth, alignment)
            self._cache = {}
            self.actionsPropertiesRegistry = {}

        def setActionsPropertiesRegistry(self, actionsPropertiesRegistry):
            self.actionsPropertiesRegistry = actionsPropertiesRegistry

        def format(self, values):
            actionId = forceRef(values[0])
            if actionId:
                nomenclatureId, actionPropertyId = self.actionsPropertiesRegistry.get(actionId, None)
                if nomenclatureId:
                    nomenclatureName = self._cache.get(nomenclatureId, None)
                    if nomenclatureName:
                        return toVariant(nomenclatureName)
                    else:
                        result = CCol.invalid
                        db = QtGui.qApp.db
                        tableRBNomenclature = db.table('rbNomenclature')
                        record = db.getRecordEx(tableRBNomenclature, [tableRBNomenclature['name']], [tableRBNomenclature['id'].eq(nomenclatureId)])
                        if record:
                            result = toVariant(forceStringEx(record.value('name')))
                            self._cache[nomenclatureId] = result
                        return result
            return CCol.invalid

        def clearCache(self):
            self._cache = {}

    Col_AssignedMedicament = 2

    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self.enableIdList = []
        self.actionsPropertiesRegistry = {}
        self.includeItems = {}
        self.addColumn(self.CEnableCol(u'Выбрать', ['id'], 5, self))
        self.addColumn(CDateCol(u'Назначено', ['directionDate'], 15))
        self.addColumn(self.CAssignedMedicamentCol(u'Лекарственный препарат', ['id'], 5))
        self.addColumn(CIntCol(u'Продолжительность приема', ['duration'],     6))
        self.addColumn(CIntCol(u'Кратность курсов лечения', ['periodicity'],  6))
        self.addColumn(CIntCol(u'Кратность приема',         ['aliquoticity'], 6))
        self.setTable('Action')
        self._mapColumnToOrder = {u'directionDate' :u'Action.directionDate',
                                  u'duration'       :u'ActionType.duration',
                                  u'periodicity'    :u'Action.periodicity',
                                  u'aliquoticity'   :u'Action.aliquoticity'
                                 }
        self.eventId = None
        self.eventIdDict = {}


    def setActionsPropertiesRegistry(self, actionsPropertiesRegistry):
        self.actionsPropertiesRegistry = actionsPropertiesRegistry
        self._cols[self.Col_AssignedMedicament].setActionsPropertiesRegistry(self.actionsPropertiesRegistry)


    def setEventId(self, eventId):
        self.eventId = eventId


    def setEventIdDict(self, eventIdDict):
        self.eventIdDict = eventIdDict


    def getItemToActionId(self, findActionId):
        if findActionId:
            recordIdList = self.idList()
            for actionId in recordIdList:
                if actionId == findActionId:
                    return self.getRecordById(actionId)
        return None


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


    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        column = index.column()
        row    = index.row()
        if role == Qt.DisplayRole:
            (col, values) = self.getRecordValues(column, row)
            return col.format(values)
        elif role == Qt.TextAlignmentRole:
           col = self._cols[column]
           return col.alignment()
        elif role == Qt.CheckStateRole:
            (col, values) = self.getRecordValues(column, row)
            return col.checked(values)
        elif role == Qt.ForegroundRole:
            (col, values) = self.getRecordValues(column, row)
            return col.getForegroundColor(values)
        elif role == Qt.BackgroundRole:
            (col, values) = self.getRecordValues(column, row)
            return col.getBackgroundColor(values)
        elif role == Qt.FontRole:
            if row >= 0 and row < len(self._idList):
                actionId = forceRef(self._idList[row])
                if self.eventId == self.eventIdDict.get(actionId, None):
                    result = QtGui.QFont()
                    result.setBold(True)
                    return QVariant(result)
        return QVariant()


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

    class CAdditionalCol(CBoolCol):
        def __init__(self, title, fields, defaultWidth):
            CBoolCol.__init__(self, title, fields, defaultWidth)

        def checked(self, values):
            value = forceInt(values[0])
            if value == 2:
                return CBoolCol.valChecked
            else:
                return CBoolCol.valUnchecked

    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self.enableIdList = []
        self.actionsPropertiesRegistry = {}
        self.includeItems = {}
        self.addColumn(CAmbCardDiagnosticsActionsCheckTableModel.CEnableCol(u'Выбрать', ['id'], 5, self))
        self.addColumn(CDateCol(u'Назначено',      ['directionDate'], 15))
        self.addColumn(CActionTypeCol(u'Тип',                         15))
        self.addColumn(CAmbCardDiagnosticsActionsCheckTableModel.CAdditionalCol(u'Дополнительно',  ['additional'],    15))
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
        self.basicAdditionalDict = {}
        self.eventId = None
        self.eventIdDict = {}


    def sort(self, col, sortOrder=Qt.AscendingOrder):
        if self._idList:
            db = QtGui.qApp.db
            table = db.table('Action')
            cond = [table['id'].inlist(self._idList)]
            colClass = self.cols()[col]
            colName = colClass.fields()[0]
            if col in [2, 9, 10]:
                tableSort = db.table('ActionType' if col==2 else colClass.tableName).alias('fieldSort')
                table = table.leftJoin(tableSort, tableSort['id'].eq(table[colName]))
                colName = 'fieldSort.name'
            order = '{} {}'.format(colName, u'DESC' if sortOrder else u'ASC')
            self._idList = db.getIdList(table, table['id'].name() , where = cond, order=order)
            self.reset()
            

    def setEventId(self, eventId):
        self.eventId = eventId


    def setEventIdDict(self, eventIdDict):
        self.eventIdDict = eventIdDict


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


    def getBasicAdditional(self, actionId):
        additional = 0
        if actionId:
            record = self.getRecordById(actionId)
            additional = forceInt(record.value('additional')) if record else 0
        return additional


    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        column = index.column()
        row    = index.row()
        if role == Qt.DisplayRole:
            (col, values) = self.getRecordValues(column, row)
            return col.format(values)
        elif role == Qt.TextAlignmentRole:
           col = self._cols[column]
           return col.alignment()
        elif role == Qt.CheckStateRole:
            (col, values) = self.getRecordValues(column, row)
            return col.checked(values)
        elif role == Qt.ForegroundRole:
            (col, values) = self.getRecordValues(column, row)
            return col.getForegroundColor(values)
        elif role == Qt.BackgroundRole:
            (col, values) = self.getRecordValues(column, row)
            return col.getBackgroundColor(values)
        elif role == Qt.FontRole:
            if row >= 0 and row < len(self._idList):
                actionId = forceRef(self._idList[row])
                if self.eventId == self.eventIdDict.get(actionId, None):
                    result = QtGui.QFont()
                    result.setBold(True)
                    return QVariant(result)
        return QVariant()


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


class CEventExportTableModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self._parent = parent
        self.firstExport = None
        self.addColumn(CDateTimeCol(u'Дата и время экспорта', ['dateTime'], 40))
        self.addColumn(CRefBookCol(u'Внешняя система', ['system_id'], 'rbExternalSystem', 50))
        self.addColumn(CEnumCol(u'отправка в Региональный РЭМД', ['success'], [u'ошибка', u'успех'], 15))
        self.addColumn(CTextCol(u'Примечания',     ['note'], 6))

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        column = index.column()
        row    = index.row()
        record = self.getRecordByRow(row)
        if forceInt(record.value('success')) == 1 and not self.firstExport:
            self.firstExport = record
        if role == Qt.DisplayRole: ### or role == Qt.EditRole:
            (col, values) = self.getRecordValues(column, row)
            return col.format(values)
        elif role == Qt.TextAlignmentRole:
            col = self._cols[column]
            return col.alignment()
        elif role == Qt.CheckStateRole:
            (col, values) = self.getRecordValues(column, row)
            return col.checked(values)
        elif role == Qt.ForegroundRole:
            (col, values) = self.getRecordValues(column, row)
            return col.getForegroundColor(values)
        elif role == Qt.DecorationRole:
            if column == 2 and forceInt(record.value('success')) == 1:
                return QtCore.QVariant(QtGui.QColor('#9ACD32'))
            elif column == 2 and forceInt(record.value('success')) == 0:
                return QtCore.QVariant(QtGui.QColor('#FF4500'))
            elif column == 0 and self.firstExport == record:
                execDate = forceDate(QtGui.qApp.db.translate('Event', 'id', forceInt(self._parent.itemId()), 'execDate'))
                if column == 0 and execDate.daysTo(forceDate(record.value('dateTime'))) > 2:
                    return QtCore.QVariant(QtGui.QColor('#FFFF66'))
        elif role == Qt.ToolTipRole:
            if column == 2 and forceInt(record.value('success')) == 1:
                return QVariant(u'Выгружено в ИЭМК')
            elif column == 2 and forceInt(record.value('success')) == 0:
                return QVariant(u'Случай обслуживания не выгружен')
            elif column == 0 and self.firstExport == record:
                execDate = forceDate(QtGui.qApp.db.translate('Event', 'id', forceInt(self._parent.itemId()), 'execDate'))
                if column == 0 and execDate.daysTo(forceDate(record.value('dateTime'))) > 2:
                    return QVariant(u'Случай был выгружен с нарушением сроков')
        return QVariant()


class CAdvancedExportTableModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self._parent = parent

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        column = index.column()
        row    = index.row()
        record = self.getRecordByRow(row)
        if role == Qt.DisplayRole: ### or role == Qt.EditRole:
            (col, values) = self.getRecordValues(column, row)
            return col.format(values)
        elif role == Qt.TextAlignmentRole:
            col = self._cols[column]
            return col.alignment()
        elif role == Qt.CheckStateRole:
            (col, values) = self.getRecordValues(column, row)
            return col.checked(values)
        elif role == Qt.ForegroundRole:
            (col, values) = self.getRecordValues(column, row)
            return col.getForegroundColor(values)
        elif role == Qt.DecorationRole:
            if column == 5 and (forceInt(record.value('success')) == 1 or self.data(index) == u'успех'):
                return QtCore.QVariant(QtGui.QColor('#9ACD32'))
            elif column == 5 and forceInt(record.value('success')) == 0:
                return QtCore.QVariant(QtGui.QColor('#FF4500'))
            elif column == 3 and u'успеш' in forceString(record.value('Message')) and self.table().tableName == 'Information_Messages':
                return QtCore.QVariant(QtGui.QColor('#9ACD32'))
            elif column == 3 and u'успеш' not in forceString(record.value('Message')) and self.table().tableName == 'Information_Messages':
                return QtCore.QVariant(QtGui.QColor('#FF4500'))
        elif role == Qt.ToolTipRole:
            if column == 5 and (forceInt(record.value('success')) == 1 or self.data(index) == u'успех'):
                return QVariant(u'Выгружено в ИЭМК')
            elif column == 5 and forceInt(record.value('success')) == 0:
                return QVariant(u'Документ не выгружен')
        return QVariant()


class CAmbCardDiagnosticsActionsPropertiesRegistry:
    def __init__(self):
        self.items = []

    def getItems(self):
        return self.items


    def setItems(self, items):
        self.items = items


    def addItem(self, item):
        if item and item not in self.items:
            self.items.append(item)


    def addItems(self, items):
        self.items.extend(items)


    def removeItem(self, item):
        if item and item in self.items:
            items = self.items
            self.items = list(set(items)-set([item]))


class CAboutMedicalExaminationsRequiredPropertiesRegistry:
    def __init__(self):
        self.items = []


    def getEmptyRecordEx(self, masterId, actionId, actionProperyId):
        db = QtGui.qApp.db
        table = db.table('Action_ActionProperty')
        newRecord = table.newRecord()
        newRecord.setValue('id', toVariant(None))
        newRecord.setValue('master_id', toVariant(masterId))
        newRecord.setValue('action_id', toVariant(actionId))
        newRecord.setValue('actionProperty_id', toVariant(actionProperyId))
        return newRecord


    def addItem(self, masterId, actionId, actionProperyId):
        record = self.getEmptyRecordEx(masterId, actionId, actionProperyId)
        self.items.append(record)


    def loadEx(self, masterId, actionId, actionProperyId):
        self.items = []
        record = self.getEmptyRecordEx(masterId, actionId, actionProperyId)
        if record:
            self.items = [record]
    
    
    def loadPrevAction(self, prevActionMasterId, masterId, actionId):
        self.items = []
        db = QtGui.qApp.db
        table = db.table('Action_ActionProperty')
        prevRecords = db.getRecordList(table, '*', [table['master_id'].eq(prevActionMasterId), table['action_id'].eq(actionId), table['deleted'].eq(0), table['actionProperty_id'].isNotNull()], order = u'Action_ActionProperty.idx, Action_ActionProperty.id')
        for record in prevRecords:
            actionId = forceRef(record.value('action_id'))
            actionProperyId = forceRef(record.value('actionProperty_id'))
            additional = forceInt(record.value('additional'))
            newRecord = self.getEmptyRecordEx(masterId, actionId, actionProperyId)
            newRecord.setValue('additional', toVariant(additional))
            self.items.append(newRecord)
        return self.items


    def load(self, masterId, actionId):
        db = QtGui.qApp.db
        table = db.table('Action_ActionProperty')
        self.items = db.getRecordList(table, '*', [table['master_id'].eq(masterId), table['action_id'].eq(actionId), table['deleted'].eq(0), table['actionProperty_id'].isNotNull()], order = u'Action_ActionProperty.idx, Action_ActionProperty.id')


    def save(self, masterId):
        db = QtGui.qApp.db
        table = db.table('Action_ActionProperty')
        idList = []
        for idx, record in enumerate(self.items):
            record.setValue('idx', toVariant(idx))
            record.setValue('master_id', toVariant(masterId))
            id = db.insertOrUpdate(table, record)
            idList.append(id)
#        oldIdList = db.getDistinctIdList(table,[table['id']], [table['master_id'].eq(masterId), table['actionProperty_id'].isNotNull(), table['deleted'].eq(0)])
#        cond = [table['master_id'].eq(masterId), table['actionProperty_id'].isNotNull()]
#        if oldIdList:
#            cond.append(table['id'].inlist(oldIdList))
#        if idList:
#            cond.append(table['id'].notInlist(idList))
#        db.deleteRecord(table, db.joinAnd(cond))
        return idList


    def getItems(self):
        return self.items


    def setItems(self, items):
        self.items = items


    def getActionIdList(self):
        actionIdList = []
        for idx, record in enumerate(self.items):
            actionId = forceRef(record.value('action_id'))
            if actionId and actionId not in actionIdList:
                actionIdList.append(actionId)
        return actionIdList


    def getPropertyIdList(self):
        propertyIdList = []
        for idx, record in enumerate(self.items):
            propertyId = forceRef(record.value('actionProperty_id'))
            if propertyId and propertyId not in propertyIdList:
                propertyIdList.append(propertyId)
        return propertyIdList


class CAdditionalInDocTableCol(CBoolInDocTableCol):
    def __init__(self, title, fieldName, width, **params):
        CBoolInDocTableCol.__init__(self, title, fieldName, width, **params)

    def toCheckState(self, val, record):
        value = forceInt(val)
        if value == 2:
            return QVariant(Qt.Checked)
        else:
            return QVariant(Qt.Unchecked)


class CAboutMedicalExaminationsRequiredActionTableModel(CInDocTableModel):
    class CLocDateInDocTableCol(CDateInDocTableCol):
        def __init__(self, title, fieldName, fieldNameCol, width, **params):
            CDateInDocTableCol.__init__(self, title, fieldName, width, **params)
            self.fieldNameCol = fieldNameCol
            self.cache = {}

        def toString(self, val, record):
            actionId = forceRef(val)
            if actionId:
                if self.cache.has_key(actionId):
                    action = self.cache[actionId]
                else:
                    action = CAction.getActionById(actionId)
                    if action:
                        self.cache[actionId] = action
                if action:
                    actionRecord = action.getRecord()
                    if actionRecord:
                        value = forceDate(actionRecord.value(self.fieldNameCol))
                        return toVariant(value)
            return QVariant()

        def invalidateRecordsCache(self):
            self.cache.invalidate()

    class CLocBoolInDocTableCol(CBoolInDocTableCol):
        def __init__(self, title, fieldName, fieldNameCol, width, **params):
            CBoolInDocTableCol.__init__(self, title, fieldName, width, **params)
            self.fieldNameCol = fieldNameCol
            self.cache = {}

        def toCheckState(self, val, record):
            value = self.getIsChecked(val)
            if value == 0:
                return QVariant(Qt.Unchecked)
            else:
                return QVariant(Qt.Checked)

        def getIsChecked(self, val):
            value = 0
            actionId = forceRef(val)
            if actionId:
                if self.cache.has_key(actionId):
                    action = self.cache[actionId]
                else:
                    action = CAction.getActionById(actionId)
                    if action:
                        self.cache[actionId] = action
                if action:
                    actionRecord = action.getRecord()
                    if actionRecord:
                        value = forceInt(actionRecord.value(self.fieldNameCol))
            return value

        def invalidateRecordsCache(self):
            self.cache.invalidate()

    class CLocEnumInDocTableCol(CEnumInDocTableCol):
        def __init__(self, title, fieldName, fieldNameCol, width, values, **params):
            CEnumInDocTableCol.__init__(self, title, fieldName, width, values, **params)
            self.fieldNameCol = fieldNameCol
            self.values = values
            self.cache = {}

        def toString(self, val, record):
            value = 0
            actionId = forceRef(val)
            if actionId:
                if self.cache.has_key(actionId):
                    action = self.cache[actionId]
                else:
                    action = CAction.getActionById(actionId)
                    if action:
                        self.cache[actionId] = action
                if action:
                    actionRecord = action.getRecord()
                    if actionRecord:
                        value = forceInt(actionRecord.value(self.fieldNameCol))
            return toVariant(self.values[value])

        def invalidateRecordsCache(self):
            self.cache.invalidate()

    class CLocCInDocTableCol(CInDocTableCol):
        def __init__(self, title, fieldName, fieldNameCol, width, **params):
            CInDocTableCol.__init__(self, title, fieldName, width, **params)
            self.fieldNameCol = fieldNameCol
            self.cache = {}

        def toString(self, val, record):
            actionId = forceRef(val)
            if actionId:
                if self.cache.has_key(actionId):
                    action = self.cache[actionId]
                else:
                    action = CAction.getActionById(actionId)
                    if action:
                        self.cache[actionId] = action
                if action:
                    actionRecord = action.getRecord()
                    if actionRecord:
                        value = forceString(actionRecord.value(self.fieldNameCol))
                        return toVariant(value)
            return QVariant()

        def invalidateRecordsCache(self):
            self.cache.invalidate()

    class CLocPersonInDocTableCol(CInDocTableCol):
        def __init__(self, title, fieldName, fieldNameCol, width, tableName, **params):
            CInDocTableCol.__init__(self, title, fieldName, width, **params)
            self.tableName  = tableName
            self.fieldNameCol = fieldNameCol
            self.cache = {}
            self.personCache = {}

        def toString(self, val, record):
            actionId = forceRef(val)
            if actionId:
                if self.cache.has_key(actionId):
                    action = self.cache[actionId]
                else:
                    action = CAction.getActionById(actionId)
                    if action:
                        self.cache[actionId] = action
                if action:
                    actionRecord = action.getRecord()
                    if actionRecord:
                        personId = forceRef(actionRecord.value(self.fieldNameCol))
                        if personId:
                            if self.personCache.has_key(personId):
                                personName = self.personCache[personId]
                            else:
                                personName = forceString(QtGui.qApp.db.translate(self.tableName, 'id', personId, 'name'))
                                if personName:
                                    self.personCache[personId] = personName
                            if personName:
                                return toVariant(personName)
            return QVariant()

        def invalidateRecordsCache(self):
            self.cache.invalidate()
            self.personCache.invalidate()

    class CLocActionTypeInDocTableCol(CInDocTableCol):
        def __init__(self, title, fieldName, fieldNameCol, width, tableName, **params):
            CInDocTableCol.__init__(self, title, fieldName, width, **params)
            self.tableName  = tableName
            self.fieldNameCol = fieldNameCol
            self.cache = {}
            self.actionTypeCache = {}

        def toString(self, val, record):
            actionId = forceRef(val)
            if actionId:
                if self.cache.has_key(actionId):
                    action = self.cache[actionId]
                else:
                    action = CAction.getActionById(actionId)
                    if action:
                        self.cache[actionId] = action
                if action:
                    actionRecord = action.getRecord()
                    if actionRecord:
                        actionTypeId = forceRef(actionRecord.value(self.fieldNameCol))
                        if actionTypeId:
                            actionTypeName = u''
                            if self.actionTypeCache.has_key(actionTypeId):
                                actionTypeName = self.actionTypeCache[actionTypeId]
                            else:
                                db = QtGui.qApp.db
                                table = db.table(self.tableName)
                                actionTypeRecord = db.getRecordEx(table, [table['code'], table['name']], [table['id'].eq(actionTypeId), table['deleted'].eq(0)])
                                if actionTypeRecord:
                                    #code = forceString(actionTypeRecord.value('code'))
                                    actionTypeName = forceString(actionTypeRecord.value('name'))
                                    #actionTypeName = u'-'.join(n for n in [code, name] if n)
                                if actionTypeName:
                                    self.actionTypeCache[actionTypeId] = actionTypeName
                            return toVariant(actionTypeName)
            return QVariant()

        def invalidateRecordsCache(self):
            self.cache.invalidate()
            self.actionTypeCache.invalidate()

    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'Action_ActionProperty', 'id', 'master_id', parent)
        self.addHiddenCol('action_id')
        self.addHiddenCol('actionProperty_id')
        self.addCol(self.CLocDateInDocTableCol(u'Назначено', 'action_id', 'directionDate', 20)).setReadOnly()
        self.addCol(self.CLocActionTypeInDocTableCol(u'Тип', 'action_id', 'actionType_id',  20, 'ActionType')).setReadOnly()
        self.addCol(CAdditionalInDocTableCol(u'Дополнительно', 'additional', 10)).setReadOnly(False)
        self.addCol(self.CLocBoolInDocTableCol(u'Срочно', 'action_id', 'isUrgent', 15)).setReadOnly()
        self.addCol(self.CLocEnumInDocTableCol(u'Состояние', 'action_id', 'status', 4, CActionStatus.names)).setReadOnly()
        self.addCol(self.CLocDateInDocTableCol(u'План', 'action_id', 'plannedEndDate', 20)).setReadOnly()
        self.addCol(self.CLocDateInDocTableCol(u'Начато', 'action_id', 'begDate', 20)).setReadOnly()
        self.addCol(self.CLocDateInDocTableCol(u'Окончено', 'action_id', 'endDate', 20)).setReadOnly()
        self.addCol(self.CLocPersonInDocTableCol(u'Назначил', 'action_id', 'setPerson_id',  20, 'vrbPersonWithSpecialityAndOrgStr')).setReadOnly()
        self.addCol(self.CLocPersonInDocTableCol(u'Выполнил', 'action_id', 'person_id',  20, 'vrbPersonWithSpecialityAndOrgStr')).setReadOnly()
        self.addCol(self.CLocCInDocTableCol(u'Каб', 'action_id', 'office', 20)).setReadOnly()
        self.addCol(self.CLocCInDocTableCol(u'Примечания', 'action_id', 'note', 20)).setReadOnly()
        self.setEnableAppendLine(False)
        self.readOnly = False
        self.action = None
        self.eventEditor = None


    def getEmptyRecord(self):
        result = QtGui.qApp.db.table('Action_ActionProperty').newRecord()
        return result


    def addItem(self, item):
        self._items.append(item)


    def getItemToActionId(self, findActionId):
        if findActionId:
            for idx, record in enumerate(self._items):
                actionId = forceRef(record.value('action_id'))
                if actionId == findActionId:
                    return record
        return None


    def getRowToActionId(self, findActionId):
        if findActionId:
            for row, record in enumerate(self._items):
                actionId = forceRef(record.value('action_id'))
                if actionId == findActionId:
                    return row
        return -1


    def getActionIdToRow(self, findRow):
        for row, record in enumerate(self._items):
            if findRow == row:
                return forceRef(record.value('action_id'))
        return None


    def getActionIdList(self):
        actionIdList = []
        for idx, record in enumerate(self._items):
            actionId = forceRef(record.value('action_id'))
            if actionId and actionId not in actionIdList:
                actionIdList.append(actionId)
        return actionIdList


    def getPropertyIdList(self):
        propertyIdList = []
        for idx, record in enumerate(self._items):
            propertyId = forceRef(record.value('actionProperty_id'))
            if propertyId and propertyId not in propertyIdList:
                propertyIdList.append(propertyId)
        return propertyIdList


    def setEventEditor(self, eventEditor):
        self.eventEditor = eventEditor


    def setAction(self, action):
        self.action = action


    def removeRows(self, row, count, parentIndex = QModelIndex()):
        if 0<=row and row+count<=len(self._items):
            self.beginRemoveRows(parentIndex, row, row+count-1)
            actionId = forceRef(self._items[row].value('action_id'))
            del self._items[row:row+count]
            self.endRemoveRows()
            return actionId
        else:
            return False


    def removeRow(self, row, parentIndex = QModelIndex()):
        result = self.removeRows(row, 1, parentIndex)
        QObject.parent(self).deletedAmbCardPrintDiagnosticActions_30Table()
        return result


    def setReadOnly(self, value=True):
        self.readOnly = value


    def flags(self, index):
        if self.readOnly:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        column = index.column()
        flags = self._cols[column].flags()
        if self.cellReadOnly(index):
            flags = flags & (~Qt.ItemIsEditable) & (~Qt.ItemIsUserCheckable)
        return flags


    def emitRowsChanged(self, begRow, endRow):
        CInDocTableModel.emitRowsChanged(self, begRow, endRow)
        for idx, record in enumerate(self._items):
            record.setValue(self._idxFieldName, toVariant(idx))


    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.CheckStateRole:
            column = index.column()
            row = index.row()
            state = value.toInt()[0]
            if row >= 0 and row < len(self._items):
                record = self._items[row]
                col = self._cols[column]
                record.setValue(col.fieldName(), QVariant(0 if state == Qt.Unchecked else 2))
                self.emitCellChanged(row, column)
                return True
        return CInDocTableModel.setData(self, index, value, role)


    def loadItems(self, masterId):
        self._items = []
        if masterId:
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
            filter = [table[self._masterIdFieldName].eq(masterId),
                      table['actionProperty_id'].isNull()
                      ]
            if self._filter:
                filter.append(self._filter)
            if table.hasField('deleted'):
                filter.append(table['deleted'].eq(0))
            if self._idxFieldName:
                order = [self._idxFieldName, self._idFieldName]
            else:
                order = [self._idFieldName]
            self._items = db.getRecordList(table, '*', filter, order)
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
                item.aboutMERProperties = CAboutMedicalExaminationsRequiredPropertiesRegistry()
                item.aboutMERProperties.load(forceRef(item.value('master_id')), forceRef(item.value('action_id')))
        self.reset()
    
    
    def loadPrevActionItems(self, prevMasterId, masterId):
        self._items = []
        if prevMasterId:
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
            filter = [table[self._masterIdFieldName].eq(prevMasterId),
                      table['actionProperty_id'].isNull()
                      ]
            if self._filter:
                filter.append(self._filter)
            if table.hasField('deleted'):
                filter.append(table['deleted'].eq(0))
            if self._idxFieldName:
                order = [self._idxFieldName, self._idFieldName]
            else:
                order = [self._idFieldName]
            prevRecords = db.getRecordList(table, '*', filter, order)
            for record in prevRecords:
                record.setValue('id', toVariant(None))
                record.setValue(self._masterIdFieldName, toVariant(None))
                newRecord = self.getEmptyRecord()
                for i in xrange(record.count()):
                    fieldName = forceStringEx(record.fieldName(i))
                    if fieldName not in ('id', self._masterIdFieldName, 'createDatetime', 'createPerson_id', 'modifyDatetime', 'modifyPerson_id', 'deleted'):
                        newRecord.setValue(fieldName, record.value(fieldName))
                    newRecord.setValue(self._masterIdFieldName, toVariant(masterId))
                self._items.append(newRecord)
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
                item.aboutMERProperties = CAboutMedicalExaminationsRequiredPropertiesRegistry()
                item.aboutMERProperties.loadPrevAction(prevMasterId, masterId, forceRef(item.value('action_id')))
        QObject.parent(self).resetAmbCardPrintDiagnosticActions_30Table()
        self.reset()


    def saveItems(self, masterId):
        if masterId and self._items is not None:
            aboutMERPropertiesIdList = []
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
                aboutMERPropertiesIdList.extend(record.aboutMERProperties.save(forceRef(record.value('master_id'))))
            filter = [table[masterIdFieldName].eq(masterId),
                      'NOT ('+table[idFieldName].inlist(idList)+')']
            if aboutMERPropertiesIdList:
                filter.append(table[idFieldName].notInlist(aboutMERPropertiesIdList))
            if self._filter:
                filter.append(self._filter)
            db.deleteRecordSimple(table, filter)


class CAboutMedicalExaminationsRequiredPropertiesTableModel(CActionPropertiesTableModel):
    def __init__(self, parent):
        CActionPropertiesTableModel.__init__(self, parent)
        self._items = []
        self.masterId = None


    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled


    def getPropertyTypeRow(self, actionPropertyId):
        for row, propertyType in enumerate(self.propertyTypeList):
            property = self.action.getPropertyById(propertyType.id)
            if property:
                record = property.getRecord()
                if record:
                    propertyId = forceRef(record.value('id'))
                    if propertyId == actionPropertyId:
                        return row
        return -1


    def removeRows(self, row, count, parentIndex = QModelIndex()):
        if 0<=row and row+count<=len(self._items):
            self.beginRemoveRows(parentIndex, row, row+count-1)
            actionId = forceRef(self._items[row].value('action_id'))
            actionPropertyId = forceRef(self._items[row].value('actionProperty_id'))
            del self._items[row:row+count]
            if actionPropertyId:
                propertyTypeRow = self.getPropertyTypeRow(actionPropertyId)
                if propertyTypeRow >= 0 and propertyTypeRow < len(self.propertyTypeList):
                    del self.propertyTypeList[propertyTypeRow:propertyTypeRow+count]
            self.endRemoveRows()
            return actionId
        else:
            return False


    def removeRow(self, row, parentIndex = QModelIndex()):
        return self.removeRows(row, 1, parentIndex)


    def setAction2(self, action, clientId, clientSex=None, clientAge=None, eventTypeId=None, propertySelectedIdList=[]):
        propertyTypeListEx = []
        self.propertyTypeList = []
        propertyIdList = self.getPropertyIdList()
        if propertyIdList:
            self.action = action
            self.clientId = clientId
            self.clientNormalParameters = self.getClientNormalParameters()
            self.eventTypeId = eventTypeId
            if self.action:
                propertyTypeList = [(id, prop.type()) for (id, prop) in action.getPropertiesById().items()]
                propertyTypeList.sort(key=lambda x: (x[1].idx, x[0]))
                self.propertyTypeList = [x[1] for x in propertyTypeList if x[1].applicable(clientSex, clientAge) and self.visible(x[1]) and x[1].typeName!='PacsImages']
                actionType = action.getType()
                propertyTypeList = actionType.getPropertiesTypeByTypeName('PacsImages')
                if propertyTypeList:
                    self.propertyTypeList.extend(propertyTypeList)
            else:
                self.propertyTypeList = []
            if self.action:
                for propertyType in self.propertyTypeList:
                    property = self.action.getPropertyById(propertyType.id)
                    if property:
                        record = property.getRecord()
                        if record:
                            propertyId = forceRef(record.value('id'))
                            if propertyId and propertyId in propertyIdList and propertyId not in propertySelectedIdList:
                                propertyTypeListEx.append(propertyType)
        self.propertyTypeList = propertyTypeListEx
        for propertyType in self.propertyTypeList:
            propertyType.shownUp(action, clientId)
        self.updateActionStatusTip()
        self.reset()


    def getActionIdList(self):
        actionIdList = []
        for idx, record in enumerate(self._items):
            actionId = forceRef(record.value('action_id'))
            if actionId and actionId not in actionIdList:
                actionIdList.append(actionId)
        return actionIdList


    def getPropertyIdList(self):
        propertyIdList = []
        for idx, record in enumerate(self._items):
            propertyId = forceRef(record.value('actionProperty_id'))
            if propertyId and propertyId not in propertyIdList:
                propertyIdList.append(propertyId)
        return propertyIdList


    def getEmptyRecordEx(self, masterId, actionId, actionProperyId):
        db = QtGui.qApp.db
        table = db.table('Action_ActionProperty')
        newRecord = table.newRecord()
        newRecord.setValue('id', toVariant(None))
        newRecord.setValue('master_id', toVariant(masterId))
        newRecord.setValue('action_id', toVariant(actionId))
        newRecord.setValue('actionProperty_id', toVariant(actionProperyId))
        return newRecord


    def addItem(self, item):
        self._items.append(item)


    def setItems(self, items):
        self._items = items


    def clearItems(self):
        self._items = []
        self.propertyTypeList = []
        self.reset()


    def getItems(self):
        return self._items


    def setMasterId(self, masterId):
        self._items = []
        self.masterId = masterId


    def loadItems(self, masterId):
        self._items = []
        self.masterId = masterId
        if not self.masterId:
            return
        db = QtGui.qApp.db
        table = db.table('Action_ActionProperty')
        cond = [table['master_id'].eq(masterId),
                table['actionProperty_id'].isNotNull(),
                table['deleted'].eq(0)
                ]
        self._items = db.getRecordList(table, u'*', cond)
        self.reset()


#    def saveItems(self, masterId):
#        if masterId and self._items is not None:
#            db = QtGui.qApp.db
#            table = db.table('Action_ActionProperty')
#            masterId = toVariant(masterId)
#            idList = []
#            for idx, record in enumerate(self._items):
#                record.setValue('master_id', masterId)
#                id = db.insertOrUpdate(table, record)
#                record.setValue('id', toVariant(id))
#                idList.append(id)
#            filter = [table['master_id'].eq(masterId),
#                      'NOT ('+table['id'].inlist(idList)+')']
#            db.deleteRecord(table, filter)


class CDiagnosisDisease_31_TableModel(CInDocTableModel):
    class CLocMKBDiagNameColumn(CInDocTableCol):
        def __init__(self, title, fieldName, width, **params):
            CInDocTableCol.__init__(self, title, fieldName, width, **params)
            self.cache = {}

        def toString(self, val, record):
            MKB = forceStringEx(record.value('MKB'))
            if self.cache.has_key(MKB):
                descr = self.cache[MKB]
            else:
                descr = getMKBName(MKB) if MKB else ''
                self.cache[MKB] = descr
            return QVariant((MKB+': '+descr) if MKB else '')

        def invalidateRecordsCache(self):
            self.cache.invalidate()

    class CLocTextInDocTableCol(CInDocTableCol):
        def __init__(self, title, fieldName, width, **params):
            CInDocTableCol.__init__(self, title, fieldName, width, **params)

        def toString(self, value, record):
            val = forceStringEx(value)
            if val:
                return toVariant(u'' if val == u'0' else val)
            else:
                return QVariant()

        def createEditor(self, parent):
            editor = QtGui.QTextEdit(parent)
#            editor.setLineWrapMode(QtGui.QTextEdit.WidgetWidth)
#            editor.setWordWrapMode(QtGui.QTextOption.WrapAtWordBoundaryOrAnywhere)
            return editor

        def setEditorData(self, editor, value, record):
            editor.setPlainText(forceString(value))

        def getEditorData(self, editor):
            text = editor.toPlainText()
            if text:
                return toVariant(text)
            else:
                return QVariant()

        def alignment(self):
            return QVariant(Qt.AlignLeft + Qt.AlignTop)


    def __init__(self, parent, diagnosisTypeCode):
        CInDocTableModel.__init__(self, 'Diagnostic', 'id', 'event_id', parent)
        self.addHiddenCol('diagnosis_id')
        self.addExtCol(CICDExInDocTableCol(u'Диагноз', 'MKB', 20), QVariant.String).setReadOnly(False)
        self.addCol(CDiagnosisDisease_31_TableModel.CLocMKBDiagNameColumn(u'Диагноз расшифровка', 'id', 30), QVariant.String).setReadOnly()
        self.addCol(CDiagnosisDisease_31_TableModel.CLocTextInDocTableCol(u'Врачебное описание нозологической единицы', 'freeInput', 30))
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


    def cellReadOnly(self, index):
        personId = self.eventEditor.cmbPerson.value()
        specialityId = None
        if personId:
            db = QtGui.qApp.db
            tablePerson = db.table('Person')
            recordPerson = db.getRecordEx(tablePerson, [tablePerson['speciality_id']],
                                          [tablePerson['id'].eq(personId), tablePerson['deleted'].eq(0)])
            specialityId = forceRef(recordPerson.value('speciality_id')) if recordPerson else None
        elif QtGui.qApp.userId and QtGui.qApp.userSpecialityId:
            personId = QtGui.qApp.userId
            specialityId = QtGui.qApp.userSpecialityId
        if personId and specialityId:
            row = index.row()
            column = index.column()
            if 0 <= row < len(self._items):
                if column == 0:
                    return False
                record = self._items[row]
                if record:
                    MKB = forceStringEx(record.value('MKB'))
                    if MKB and column != 1:
                        return False
            elif column == 0:
                return False
        return True


    def setReadOnly(self, value=True):
        self.readOnly = value


    def flags(self, index):
        if self.readOnly or self.cellReadOnly(index):
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
            MKB = forceStringEx(record.value('MKB')) if record else u''
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
                newMKB = forceString(value)
                acceptable, specifiedMKB, specifiedMKBEx, specifiedCharacterId, specifiedTraumaTypeId, specifiedDispanserId, specifiedRequiresFillingDispanser, specifiedProlongMKB = QObject.parent(self).specifyDiagnosis(newMKB)
                if not acceptable:
                    return False
                if row == len(self._items):
                    if value.isNull():
                        return False
                    self._addEmptyItem()
                if 0 <= row < len(self._items):
                    result = CInDocTableModel.setData(self, index, value, role)
                    if result:
                        self._items[row].setValue('diagnosisType_id', toVariant(self.diagnosisTypeId))
                        self.emitCellChanged(row, column)
                    return result
                else:
                    return False
            elif column == self.getColIndex('freeInput'):
                if '\0' in forceString(value):
                    value = toVariant(forceString(value).replace('\0', ''))
                return CInDocTableModel.setData(self, index, value, role)
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


    def loadPrevActionItems(self, prevActionMasterId, masterId):
        self._items = []
        if prevActionMasterId:
            db = QtGui.qApp.db
            cols = '*'
            table = self._table
            filter = [table[self._masterIdFieldName].eq(prevActionMasterId),
                      table['diagnosisType_id'].eq(self.diagnosisTypeId)]
            if self._filter:
                filter.append(self._filter)
            if table.hasField('deleted'):
                filter.append(table['deleted'].eq(0))
            if self._idxFieldName:
                order = [self._idxFieldName, self._idFieldName]
            else:
                order = [self._idFieldName]
            prevRecords = db.getRecordList(table, cols, filter, order)
            for record in prevRecords:
                record.setValue('id', toVariant(None))
                record.setValue(self._masterIdFieldName, toVariant(None))
                newRecord = self.getEmptyRecord()
                for i in xrange(record.count()):
                    fieldName = forceStringEx(record.fieldName(i))
                    if fieldName not in (
                    'id', self._masterIdFieldName, 'createDatetime', 'createPerson_id', 'modifyDatetime',
                    'modifyPerson_id', 'deleted'):
                        newRecord.setValue(fieldName, record.value(fieldName))
                    newRecord.setValue(self._masterIdFieldName, toVariant(masterId))
                self._items.append(newRecord)
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
                            item.setValue(field.name(),
                                          toVariant(self.getMKBToDiagnosis(forceRef(item.value('diagnosis_id')))))
                            item.setValue('diagnosis_id', toVariant(None))
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


class CDiagnosisDisease_31_1_TableModel(CDiagnosisDisease_31_TableModel):
    def __init__(self, parent, diagnosisTypeCode):
        CDiagnosisDisease_31_TableModel.__init__(self, parent, diagnosisTypeCode)
        self.mapMKBToServiceId = {}
        self._enableAppendLine = False
        self.isMKBMorphology = QtGui.qApp.defaultMorphologyMKBIsVisible()
        if self.isMKBMorphology:
            self.addExtCol(CMKBMorphologyCol(u'Морфология МКБ', 'morphologyMKB', 10, 'MKB_Morphology', filter='`group` IS NOT NULL'), QVariant.String).setReadOnly(False)
        self.setEnableAppendLine(False)


    def cellReadOnly(self, index):
        personId = self.eventEditor.cmbPerson.value()
        specialityId = None
        if personId:
            db = QtGui.qApp.db
            tablePerson = db.table('Person')
            recordPerson = db.getRecordEx(tablePerson, [tablePerson['speciality_id']],
                                          [tablePerson['id'].eq(personId), tablePerson['deleted'].eq(0)])
            specialityId = forceRef(recordPerson.value('speciality_id')) if recordPerson else None
        elif QtGui.qApp.userId and QtGui.qApp.userSpecialityId:
            personId = QtGui.qApp.userId
            specialityId = QtGui.qApp.userSpecialityId
        if personId and specialityId:
            row = index.row()
            column = index.column()
            if 0 <= row < len(self._items):
                if column == 0:
                    return False
                record = self._items[row]
                if record:
                    MKB = forceStringEx(record.value('MKB'))
                    if MKB and column != 1:
                        return False
            elif column == 0 and len(self._items) == 0:
                return False
        return True


    def rowCount(self, index = None):
        countRows = len(self._items)
        return countRows if countRows > 0 else 1


    def _addEmptyItem(self):
        self._items.append(self.getEmptyRecord())


    def getEmptyRecord(self):
        result = CDiagnosisDisease_31_TableModel.getEmptyRecord(self)
        MKB = forceStringEx(result.value('MKB')) if result else u''
        self.setMKBAction('MKB', MKB)
        if self.isMKBMorphology:
            result.append(QtSql.QSqlField('morphologyMKB', QVariant.String))
            result.setValue('morphologyMKB', toVariant(self.getMorphologyMKBToDiagnosis(forceRef(result.value('diagnosis_id')))))
            self.setMKBAction('morphologyMKB', forceStringEx(result.value('morphologyMKB')))
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
                newMKB = forceString(value)
                acceptable, specifiedMKB, specifiedMKBEx, specifiedCharacterId, specifiedTraumaTypeId, specifiedDispanserId, specifiedRequiresFillingDispanser, specifiedProlongMKB = QObject.parent(self).specifyDiagnosis(newMKB)
                if not acceptable:
                    return False
                if row == len(self._items) and len(self._items) == 0:
                    if value.isNull():
                        return False
                    self._addEmptyItem()
                if 0 <= row < len(self._items):
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
            elif column == self.getColIndex('freeInput'):
                if '\0' in forceString(value):
                    value = toVariant(forceString(value).replace('\0', ''))
                return CInDocTableModel.setData(self, index, value, role)
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

    
    def loadPrevActionItems(self, prevActionMasterId, masterId):
        self._items = []
        if prevActionMasterId:
            db = QtGui.qApp.db
            cols = '*'
            table = self._table
            filter = [table[self._masterIdFieldName].eq(prevActionMasterId),
                      table['diagnosisType_id'].eq(self.diagnosisTypeId)]
            if self._filter:
                filter.append(self._filter)
            if table.hasField('deleted'):
                filter.append(table['deleted'].eq(0))
            if self._idxFieldName:
                order = [self._idxFieldName, self._idFieldName]
            else:
                order = [self._idFieldName]
            prevRecords = db.getRecordList(table, cols, filter, order)
            for record in prevRecords:
                record.setValue('id', toVariant(None))
                record.setValue(self._masterIdFieldName, toVariant(None))
                newRecord = self.getEmptyRecord()
                for i in xrange(record.count()):
                    fieldName = forceStringEx(record.fieldName(i))
                    if fieldName not in ('id', self._masterIdFieldName, 'createDatetime', 'createPerson_id', 'modifyDatetime', 'modifyPerson_id', 'deleted'):
                        newRecord.setValue(fieldName, record.value(fieldName))
                    newRecord.setValue(self._masterIdFieldName, toVariant(masterId))
                self._items.append(newRecord)
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
                        item.setValue('diagnosis_id', toVariant(None))
        self.reset()



class CF088AddActions30InDocTableModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'Action', 'id', 'event_id', parent)
        self.addCol(CActionTypeTableCol(u'Тип',      'actionType_id',  15, None, classesVisible=True)).setReadOnly(True)
        self.addCol(CAdditionalInDocTableCol(u'Дополнительно', 'additional', 10))
        self.addCol(CBoolInDocTableCol(u'Срочный',   'isUrgent',       10))
        self.addCol(CEnumInDocTableCol(u'Состояние', 'status',         10, CActionStatus.names))
        self.addCol(CDateInDocTableCol(u'Назначено', 'directionDate',  20, canBeEmpty=True))
        self.addCol(CDateInDocTableCol(u'Начато',    'begDate',        15, canBeEmpty=True))
        self.addCol(CDateInDocTableCol(u'Окончено',  'endDate',        15, canBeEmpty=True))
        self.addCol(CActionPerson(u'Назначил',       'setPerson_id',   20, 'vrbPersonWithSpecialityAndOrgStr', parent=parent))
        self.addCol(CActionPerson(u'Выполнил',       'person_id',      20, 'vrbPersonWithSpecialityAndOrgStr', parent=parent, useFilter=True))
        self.addCol(CInDocTableCol(u'Каб',           'office',         6))
        self.addCol(COrgInDocTableColEx(u'Место выполнения',      'org_id', 30))
        self.addCol(COrgStructureInDocTableCol(u'Подразделение',  'orgStructure_id',  100))
        self.addCol(CInDocTableCol(u'Примечания',    'note',   40))
        self.setEnableAppendLine(False)
        self.readOnly = False
        self.clientId  = None
        self.clientSex = None
        self.clientAge = None
        self.MKB = None
        self.MKBList = []
        self.eventTypeId = None


    def setEventTypeId(self, eventTypeId):
        self.eventTypeId = eventTypeId


    def setClientInfo(self, clientId, clientSex, clientAge):
        self.clientId  = clientId
        self.clientSex = clientSex
        self.clientAge = clientAge


    def setMKBList(self, MKBList):
        self.MKB = None
        self.MKBList = MKBList
        if MKBList and len(MKBList) > 0:
            self.MKB = MKBList[0][0]


    def cellReadOnly(self, index):
        row = index.row()
        if 0 <= row < len(self._items):
            record, action = self._items[row]
            if record:
                actionTypeId = forceRef(record.value('actionType_id'))
                if actionTypeId:
                    return False
        return True


    def setReadOnly(self, value):
        self.readOnly = value


    def flags(self, index):
        if self.readOnly:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        column = index.column()
        flags = self._cols[column].flags()
        if self.cellReadOnly(index):
            flags = flags & (~Qt.ItemIsEditable) & (~Qt.ItemIsUserCheckable)
        return flags


    def getEmptyRecord(self):
        result = QtGui.qApp.db.table('Action').newRecord()
        return result


    def setItems(self, items):
        recordNew, actionNew = items
        record, action = self._items
        if id(record) != id(recordNew):
            self._items = items
            self.reset()


    def insertRecord(self, row, record, action):
        self.beginInsertRows(QModelIndex(), row, row)
        self._items.insert(row, (record, action))
        self.endInsertRows()


    def addRecord(self, record, action):
        self.insertRecord(len(self._items), record, action)


    def setValue(self, row, fieldName, value):
        if 0 <= row < len(self._items):
            record, action = self._items[row]
            valueAsVariant = toVariant(value)
            if record.value(fieldName) != valueAsVariant:
                record.setValue(fieldName, valueAsVariant)
                self.emitValueChanged(row, fieldName)


    def value(self, row, fieldName):
        if 0 <= row < len(self._items):
            record, action = self._items[row]
            return record.value(fieldName)
        return None


    def sortData(self, column, ascending):
        pass


    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        row = index.row()
        if 0 <= row < len(self._items):
            if role == Qt.EditRole:
                col = self._cols[column]
                record, action = self._items[row]
                return record.value(col.fieldName())

            if role == Qt.DisplayRole:
                col = self._cols[column]
                record, action = self._items[row]
                return col.toString(record.value(col.fieldName()), record)

            if role == Qt.StatusTipRole:
                col = self._cols[column]
                record, action = self._items[row]
                return col.toStatusTip(record.value(col.fieldName()), record)

            if role == Qt.TextAlignmentRole:
                col = self._cols[column]
                return col.alignment()

            if role == Qt.CheckStateRole:
                col = self._cols[column]
                record, action = self._items[row]
                return col.toCheckState(record.value(col.fieldName()), record)

            if role == Qt.ForegroundRole:
                col = self._cols[column]
                record, action = self._items[row]
                return col.getForegroundColor(record.value(col.fieldName()), record)

        return QVariant()


    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.EditRole:
            column = index.column()
            row = index.row()
            if row == len(self._items):
                if value.isNull():
                    return False
                record = self.getEmptyRecord()
                actionTypeId = forceRef(record.value('actionType_id'))
                if not actionTypeId:
                    return False
                record = preFillingActionRecordMSI(record, actionTypeId)
                self._items.append(record, CAction(record=record))
                count = len(self._items)
                rootIndex = QModelIndex()
                self.beginInsertRows(rootIndex, count, count)
                self.insertRows(count, 1, rootIndex)
                self.endInsertRows()
            record, action = self._items[row]
            col = self._cols[column]
            action.getRecord().setValue(col.fieldName(), value)
            record.setValue(col.fieldName(), value)
            self.emitCellChanged(row, column)
            if column == self.getColIndex('endDate'):
                if forceDate(record.value('endDate')):
                    newStatus = CActionStatus.finished
                    status = forceInt(record.value('status'))
                    if status != newStatus:
                        action.getRecord().setValue('status', toVariant(newStatus))
                        record.setValue('status', toVariant(newStatus))
                        self.emitCellChanged(row, self.getColIndex('status'))
            return True
        if role == Qt.CheckStateRole:
            column = index.column()
            row = index.row()
            state = value.toInt()[0]
            if row == len(self._items):
                if state == Qt.Unchecked:
                    return False
                record = self.getEmptyRecord()
                actionTypeId = forceRef(record.value('actionType_id'))
                if not actionTypeId:
                    return False
                record = preFillingActionRecordMSI(record, actionTypeId)
                self._items.append(record, CAction(record=record))
                count = len(self._items)
                rootIndex = QModelIndex()
                self.beginInsertRows(rootIndex, count, count)
                self.insertRows(count, 1, rootIndex)
                self.endInsertRows()
            record, action = self._items[row]
            col = self._cols[column]
            action.getRecord().setValue(col.fieldName(), QVariant(0 if state == Qt.Unchecked else 2))
            record.setValue(col.fieldName(), QVariant(0 if state == Qt.Unchecked else 2))
            self.emitCellChanged(row, column)
            return True
        return False


#    def loadItems(self, masterId):
#        self._items = []
#        self.actionList = {}
##        actionTypeIdList = getActionTypeIdListByFlatCode(u'blablabla%')
##        if actionTypeIdList:
#        db = QtGui.qApp.db
#        table = self._table
#        tableAT = db.table('ActionType')
#        queryTable = table.innerJoin(tableAT, tableAT['id'].eq(table['actionType_id']))
#        filter = [table['event_id'].eq(masterId),
#                  tableAT['deleted'].eq(0),
#                  table['deleted'].eq(0),
##                  table['actionType_id'].inlist(actionTypeIdList)
#                  ]
#        if self._filter:
#            filter.append(self._filter)
#        order = ['Action.endDate DESC']
#        records = db.getRecordList(queryTable, u'Action.*', filter, order)
#        for record in records:
#            action = CAction(record=record)
#            self._items.append((record, action))
#        self.reset()


    def saveItems(self, masterId):
        if self._items is not None:
            masterId = toVariant(masterId)
            masterIdFieldName = self._masterIdFieldName
            idFieldName = self._idFieldName
            for idx, (record, action) in enumerate(self._items):
                action.getRecord().setValue(masterIdFieldName, masterId)
                if self._idxFieldName:
                    action.getRecord().setValue(self._idxFieldName, toVariant(idx))
                id = action.save(forceRef(masterId))
                action.getRecord().setValue(idFieldName, toVariant(id))




