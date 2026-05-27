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

# Редактор действия "Индивидуальная медицинская карта беременной и родильницы" Форма 111/y-20

import json
from collections import OrderedDict
from PyQt4 import QtGui
from PyQt4.QtGui import QCheckBox, QTextEdit, QComboBox
from PyQt4.QtCore import Qt, QDate, QDateTime, QTime, QVariant, pyqtSlot, pyqtSignature, SIGNAL

from library.Attach.AttachAction  import getAttachAction
from library.Attach.AttachButton import CAttachButton
from library.Calendar import wpFiveDays, wpSixDays, wpSevenDays
from library.Counter import CCounterController
from library.interchange import (getDatetimeEditValue,
                                getDoubleBoxValue,
                                getLineEditValue,
                                getRBComboBoxValue,
                                setCheckBoxValue,
                                setDatetimeEditValue,
                                setDoubleBoxValue,
                                setLineEditValue,
                                setRBComboBoxValue,
                                )

from library.ItemsListDialog import CItemEditorBaseDialog
from library.PrintInfo import CInfoContext
from library.PrintTemplates import applyTemplate, customizePrintButton, getPrintButton
from library.Utils import (calcAgeTuple,
                        forceDate,
                        forceDateTime,
                        forceTime,
                        forceInt,
                        forceRef,
                        forceDouble,
                        forceString,
                        forceStringEx,
                        forceBool,
                        toDateTimeWithoutSeconds,
                        trim,
                        toVariant,
                        exceptionToUnicode
                        )

from Events.Action import CAction, CActionType, CActionTypeCache
from Events.ActionEditDialog import CActionEditDialog
from Events.ActionInfo import CCookedActionInfo, CLocActionPropertyActionsInfoList

from Events.ActionProperty.ActionPropertyValueType import CActionPropertyValueType
from Events.ActionProperty.BooleanActionPropertyValueType import CBooleanActionPropertyValueType
from Events.ActionProperty.TextActionPropertyValueType    import CTextActionPropertyValueType
from Events.ActionProperty.StringActionPropertyValueType  import CStringActionPropertyValueType
from Events.ActionProperty.IntegerActionPropertyValueType import CIntegerActionPropertyValueType
from Events.ActionProperty.DoubleStringActionPropertyValueType import CDoubleStringActionPropertyValueType
from Events.ActionProperty.DoubleActionPropertyValueType   import CDoubleActionPropertyValueType
from Events.ActionProperty.ConstructorActionPropertyValueType import CConstructorActionPropertyValueType
from Events.ActionStatus import CActionStatus
from Events.ActionTemplateChoose import CActionTemplateCache
from Events.EventInfo import CCookedEventInfo, CEventInfo
from Events.PropertyEditorAmbCard import CPropertyEditorAmbCard
from Events.Utils import (checkAttachOnDate,
                        checkPolicyOnDate,
                        checkTissueJournalStatusByActions,
                        getEventEnableActionsBeyondEvent,
                        getEventDuration,
                        getEventShowTime,
                        getActionTypeIdListByFlatCode,
                        getDeathDate,
                        getEventPurposeId, setActionPropertiesColumnVisible,
                        )
from F111.F111TableModels import (CSOPSvORNMTableModel, 
                                  CNVNBVARRSTableModel, 
                                  CNVNBARTableModel, 
                                  CNVNBSGVBTableModel, 
                                  CPreviousPregnancyModel,
                                  CPregnancyRetrospectModel,
                                  CAboutChildrenPropertiesRegistry,
                                  CPreviousPregnancyChildrenModel,
                                  CActionsPropertiesRegistry,
                                  CPregnancyInfoAddModel
                                  )
from Orgs.Orgs import selectOrganisation
from Registry.ClientEditDialog import CClientEditDialog
from Registry.Utils import getClientInfo, getClientBanner, CCheckNetMixin
from Users.Rights import (urAdmin,
                        urRegTabWriteRegistry,
                        urRegTabReadRegistry,
                        )

from F111.Ui_F111 import Ui_F111Dialog


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


class CF111EditDialog(CItemEditorBaseDialog, CCheckNetMixin, Ui_F111Dialog):
    cdSaveNoClose = 4 # сохранить не закрывая

    def __init__(self, parent, isCreate=False):
        CItemEditorBaseDialog.__init__(self, parent, 'Action')
        self.isCreate = isCreate
        self.action = None
        self.eventId = None
        self._eventExecDate = None
        self.eventTypeId = None
        self.eventPurposeId = None
        self.eventSetDate = None
        self.eventDate = None
        self.eventSetDateTime = None
        self.clientId = None
        self.forceClientId = None
        self.clientSex = None
        self.clientAge = None
        self.clientBirthDate = None
        self.clientDeathDate = None
        self.personId = None
        self.personSNILS = u''
        self.showTypeTemplate = 0
        self.personSpecialityId = None
        self.recordEvent = None
        self.newRecordClientSocStatus = None
        self.clientInfo = None
        self.actionTypeId = None
        self.idx = 0
        self.dictDiagnosisMKB = {}
        self.addModels('PreviousPregnancy', CPreviousPregnancyModel(self))
        self.addModels('PregnancyRetrospect', CPregnancyRetrospectModel(self))
        self.addModels('PregnancyInfoAdd', CPregnancyInfoAddModel(self))
        self.addModels('PreviousPregnancyChildren', CPreviousPregnancyChildrenModel(self))
        self.addModels('PregnancyRetrospectChildren', CPreviousPregnancyChildrenModel(self))
        self.addModels('PregnancyInfoAddChildren', CPreviousPregnancyChildrenModel(self))
        self.addModels('SOPSvORNM', CSOPSvORNMTableModel(self))
        self.addModels('NVNBVARRS', CNVNBVARRSTableModel(self))
        self.addModels('NVNBAR', CNVNBARTableModel(self))
        self.addModels('NVNBSGVB', CNVNBSGVBTableModel(self))
        self.addObject('actEditClient', QtGui.QAction(u'Открыть регистрационную карточку', self))
        self.addObject('actPortal_Doctor', QtGui.QAction(u'Перейти на портал врача', self))
        self.addObject('actShowAttachedToClientFiles', getAttachAction('Client_FileAttach',  self))
        self.addObject('btnPrint', getPrintButton(self, ''))
        self.addObject('btnAttachedFiles', CAttachButton(self, u'Прикреплённые файлы'))
        self.addObject('btnApply', QtGui.QPushButton(u'Применить', self))
        self.addObject('actEditAction', QtGui.QAction(u'Редактировать Действие', self))
        self.addObject('actDeleteAction', QtGui.QAction(u'Удалить Действие', self))
        self.addObject('actAddPregnancyRetrospect',QtGui.QAction(u'Вставить в блок Действия', self))
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setWindowTitleEx(u'Индивидуальная медицинская карта беременной и родильницы')
        self.actionTypeIdListByKBiR = self.getActionTypeIdListByKBiR(flatCode = u'111/y-20')
        self.edtDirectionDate.canBeEmpty(True)
        self.edtEndDate.canBeEmpty(True)
        self.edtBegDate.canBeEmpty(True)
        self.setModels(self.tblPreviousPregnancy, self.modelPreviousPregnancy, self.selectionModelPreviousPregnancy)
        self.setModels(self.tblPregnancyRetrospect, self.modelPregnancyRetrospect, self.selectionModelPregnancyRetrospect)
        self.setModels(self.tblPregnancyInfoAdd, self.modelPregnancyInfoAdd, self.selectionModelPregnancyInfoAdd)
        self.setModels(self.tblPreviousPregnancyChildren, self.modelPreviousPregnancyChildren, self.selectionModelPreviousPregnancyChildren)
        self.setModels(self.tblPregnancyRetrospectChildren, self.modelPregnancyRetrospectChildren, self.selectionModelPregnancyRetrospectChildren)
        self.setModels(self.tblPregnancyInfoAddChildren, self.modelPregnancyInfoAddChildren, self.selectionModelPregnancyInfoAddChildren)
        self.setModels(self.tblSOPSvORNM, self.modelSOPSvORNM, self.selectionModelSOPSvORNM)
        self.setModels(self.tblNVNBVARRS, self.modelNVNBVARRS, self.selectionModelNVNBVARRS)
        self.setModels(self.tblNVNBAR, self.modelNVNBAR, self.selectionModelNVNBAR)
        self.setModels(self.tblNVNBSGVB, self.modelNVNBSGVB, self.selectionModelNVNBSGVB)
        self.buttonBox.addButton(self.btnPrint, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnAttachedFiles, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnApply, QtGui.QDialogButtonBox.ApplyRole)
        self.txtClientInfoBrowser.actions.append(self.actEditClient)
        self.txtClientInfoBrowser.actions.append(self.actPortal_Doctor)
        self.txtClientInfoBrowser.actions.append(self.actShowAttachedToClientFiles)
        
        self.actEditClient.setEnabled(QtGui.qApp.userHasAnyRight([urAdmin, urRegTabWriteRegistry, urRegTabReadRegistry]))
        self.setupDirtyCather()
        self.setIsDirty(False)
        self.actionTemplateCache = CActionTemplateCache(self, self.cmbPerson)
        action = QtGui.QAction(self)
        action.setShortcut('F3')
        self.addAction(action)
        self.modelSOPSvORNM.setEventEditor(self)
        self.tblSOPSvORNM.addPopupDelRow()
        
        self.tblNVNBVARRS.resizeRowsToContents()
        self.tblNVNBVARRS.resizeColumnsToContents()
        rowHeight = self.tblNVNBVARRS.rowHeight(0)
        headerHeight = self.tblNVNBVARRS.horizontalHeader().height()
        margin = 2 * self.tblNVNBVARRS.frameWidth()
        maxHeight = headerHeight + rowHeight * 7 + margin
        self.tblNVNBVARRS.setMaximumHeight(headerHeight + rowHeight * 7 + margin)
        self.tblNVNBAR.setMaximumHeight(headerHeight + rowHeight * 5 + margin)
        self.tblSOPSvORNM.setMaximumHeight(headerHeight + rowHeight * 4 + margin)
        
        self.modelNVNBVARRS.setEventEditor(self)
        self.modelNVNBAR.setEventEditor(self)
        self.tblNVNBAR.addPopupDelRow()
        self.modelNVNBSGVB.setEventEditor(self)
        self.tblNVNBSGVB.addPopupDelRow()
        self.setWidgetsVisible(False)
        self.setComoboBoxWheel()
        self.setReferenceComboBoxes()
        self.tabNotes.setEventEditor(self)
        self.tblPreviousPregnancy.addMoveRow()
        self.tblPreviousPregnancy.addPopupDelRow()
        self.tblPregnancyRetrospect.enableColsHide()
        self.tblPregnancyRetrospect.createPopupMenu([self.actAddPregnancyRetrospect, self.actEditAction, self.actDeleteAction])
        self.modelPregnancyRetrospectChildren.setReadOnly(True)
        self.tblPregnancyInfoAdd.createPopupMenu()
        self.actAddRows = QtGui.QAction(u'Добавить данные о беременности', self.tblPregnancyInfoAdd)
        self.actAddRows.setObjectName('actAddRows')
        self.tblPregnancyInfoAdd._popupMenu.addAction(self.actAddRows)
        self.tblPregnancyInfoAdd.addPopupDelRow()
        self.tblPregnancyInfoAdd.enableColsHide()
        self.connect(self.actAddRows, SIGNAL('triggered()'), self.on_addRows)
        
        btnApply = self.btnBoxPregnancyRetrospect.button(QtGui.QDialogButtonBox.Apply)
        btnReset = self.btnBoxPregnancyRetrospect.button(QtGui.QDialogButtonBox.Reset)
        btnApply.clicked.connect(self.on_btnBoxPregnancyRetrospect_apply)
        btnReset.clicked.connect(self.on_btnBoxPregnancyRetrospect_reset)
        self.modelNVNBVARRS.setEnableAppendLine(False)
        self.frameAP.setVisible(False)
        
        self.ambWidgets = self.initAmbWidgets()
        self.ambCardMenu = QtGui.QMenu(self)
        self.addObject('actPropertyEditorAmbCard', QtGui.QAction(u'Заполнить данные из мед карты', self))
        self.actPropertyEditorAmbCard.triggered.connect(self.on_actPropertyEditorAmbCard_triggered)
        self.ambCardMenuSetup()

    
    def ambCardMenuSetup(self):
        for widget in self.ambWidgets.keys():
            widget.setContextMenuPolicy(Qt.CustomContextMenu)
            widget.customContextMenuRequested.connect(self.ambCardMenuExec)
    
    def ambCardMenuExec(self, point):
        widget = self.sender()
        try:
            menu = widget.createStandardContextMenu()
        except AttributeError:
            menu = QtGui.QMenu(widget)
        self.actPropertyEditorAmbCard.widget = widget
        self.actPropertyEditorAmbCard.setData(self.ambWidgets[widget])

        defaultActions = menu.actions()
        if defaultActions:
            menu.insertAction(defaultActions[0], self.actPropertyEditorAmbCard)
            menu.insertSeparator(defaultActions[0])
        else:
            menu.addAction(self.actPropertyEditorAmbCard)
        menu.exec_(widget.mapToGlobal(point))


    def setWidgetsVisible(self, value):
        self.edtODGODSMText.setVisible(value)
        self.chkNVNBIBRM2.setVisible(value)
        self.edtNVNBIBRM4.setVisible(value)
        self.chkNVNBIBRM6.setVisible(value)
        self.chkNVNBIBRM7.setVisible(value)
        self.edtNVNBIBRM7.setVisible(value)
        self.chkNVNBIBRM8.setVisible(value)
        self.edtPregravidarText.setVisible(value)
        self.frameAgeCryo.setVisible(value)
        self.frameCryo.setVisible(value)
        self.frameEmbryos.setVisible(value)
        self.frameVRT.setVisible(value)
        self.lblFetusCount.setVisible(value)
        self.edtFetusCount.setVisible(value)
        self.edtODPOBGText.setVisible(value)
        self.lblODPOBOLocalization.setVisible(value)
        self.lblODPOBULULocalization.setVisible(value)
        self.edtODPOBOLocalizationText.setVisible(value)
        self.edtODPOBULULocalizationText.setVisible(value)
        self.edtODPOBOPMG3Text.setVisible(value)
        self.edtODPOBC3Text.setVisible(value)
        self.edtODPOBTS2Text.setVisible(value)
        self.edtODPOBAL2Text.setVisible(value)
        self.edtODGOOSMZ2Text.setVisible(value)
        self.edtODGONPO2Text.setVisible(value)
        self.edtODGOV2Text.setVisible(value)
        self.edtODGOTM4Text.setVisible(value)
        self.edtODGOPSL2Text.setVisible(value)
        self.edtODGOPSP3Text.setVisible(value)
        self.edtODGOE2Text.setVisible(value)
        self.edtSOPWPRText.setVisible(value)
        self.edtSOPDBText.setVisible(value)
        self.edtSOPSZText.setVisible(value)
        self.edtSOPDSText.setVisible(value)
        self.edtSOPTROText.setVisible(value)
        self.edtSOPSZIText.setVisible(value)
        self.label_60.setVisible(value)
        self.edtSOPVSTATUSDate.setVisible(value)
        self.edtSOPVSTATUSNumberText.setVisible(value)
        self.lblSOPVSTATUS2.setVisible(value)
        self.lblSOPVSTATUSARVTText.setVisible(value)
        self.edtSOPVSTATUSARVTText.setVisible(value)
        self.edtSOPNZText.setVisible(value)
        self.edtSOPGTRDate.setVisible(value)
        self.edtSOPGTRComponent.setVisible(value)
        self.lblSOPGTRComponent.setVisible(value)
        self.label_67.setVisible(value)
        self.chkSOPWP3.setVisible(value)
        self.chkSOPWP4.setVisible(value)
        self.chkSOPWP5.setVisible(value)
        self.edtSOPWPText.setVisible(value)
        self.label_70.setVisible(value)
        self.chkSOPWP8.setVisible(value)
        self.chkSOPWP9.setVisible(value)
        self.chkSOPWP10.setVisible(value)
        self.edtSOPWPText11.setVisible(value)
        self.label_71.setVisible(value)
        self.edtSOPWP.setVisible(value)
        self.label_72.setVisible(value)
        self.edtSOPWPText12.setVisible(value)
        self.label_73.setVisible(value)
        self.edtSOPIPPPText.setVisible(value)
        self.edtSOPSOPR1Date.setVisible(value)
        self.label_82.setVisible(value)
        self.edtSOPSOPR2Date.setVisible(value)
        self.label_83.setVisible(value)
        self.edtSOPSOPR3Date.setVisible(value)
        self.label_80.setVisible(value)
        self.edtSOPSOPR4Date.setVisible(value)
        self.label_79.setVisible(value)
        self.edtSOPSOPR5Date.setVisible(value)
        self.label_78.setVisible(value)
        self.edtSOPSOPR6Date.setVisible(value)
        self.label_81.setVisible(value)
        self.edtSOPSOPR7Date.setVisible(value)
        self.label_77.setVisible(value)
        self.edtSOPSOPR8Date.setVisible(value)
        self.label_75.setVisible(value)
        self.edtSOPSOPR9Date.setVisible(value)
        self.edtSOPSOPR9Text.setVisible(value)
        self.label_76.setVisible(value)
        self.edtSOPPRWText.setVisible(value)
        self.edtSOPOXZText.setVisible(value)
        self.edtSOPOIPPPText.setVisible(value)
        self.edtSOPOSZIText.setVisible(value)
        self.label_215.setVisible(value)
        self.edtSOPMNText.setVisible(value)
        self.label_94.setVisible(value)
        self.edtNVNBDG2Text.setVisible(value)
        self.lblNVNBDGK.setVisible(value)
        self.chkNVNBDGK1.setVisible(value)
        self.chkNVNBDGK2.setVisible(value)
        self.lblNVNBDGO.setVisible(value)
        self.edtNVNBDGO.setVisible(value)
        self.label_86.setVisible(value)
        self.frame_30.setVisible(value)
        self.frame_31.setVisible(value)
        self.frame_33.setVisible(value)
        self.frame_34.setVisible(value)
        self.frame_35.setVisible(value)
        self.frame_36.setVisible(value)
        self.frame_40.setVisible(value)
        self.frame_41.setVisible(value)
        self.frame_42.setVisible(value)
        self.frame_43.setVisible(value)
        self.setODPOBRPPGRFVisible(False)
        self.lblNVNBPUDRP.setVisible(value)
        self.cmbNVNBPUDRP.setVisible(value)
        self.lblNVNBPUDSM.setVisible(value)
        self.cmbNVNBPUDSM.setVisible(value)
        self.lblNVNBPUDFTB.setVisible(value)
        self.cmbNVNBPUDFTB.setVisible(value)
        self.lblNVNBPUDSST.setVisible(value)
        self.cmbNVNBPUDSST.setVisible(value)
        self.lblNVNBPUDKOV.setVisible(value)
        self.cmbNVNBPUDKOV.setVisible(value)
        self.lblNVNBPUDCA.setVisible(value)
        self.cmbNVNBPUDCA.setVisible(value)
        self.edtSkinStatus.setVisible(value)
        self.edtODPOBSBPR_1.setVisible(value)
        self.edtODPOBSBPR_2.setVisible(value)
        self.edtODPOBSBPR_3.setVisible(value)
        self.edtODPOBSBPR_4.setVisible(value)
        self.edtODPOBSBPR_5.setVisible(value)
        self.edtCloseReason.setVisible(value)
        self.lblCloseReason.setVisible(value)


    def setInitDate(self):
        self.edtBegDateMaternityLeave.setDate(QDate())
        self.edtEndDateMaternityLeave.setDate(QDate())
        self.edtGenericCertificateDate.setDate(QDate())
        self.edtBloodGroupFatherDate.setDate(QDate())
        self.edtAntiresusIgPrevPregnBegDate.setDate(QDate())
        self.edtAntiresusIgPrevPregnEndDate.setDate(QDate())
        self.edtAntiresusIgCurrPregnBegDate.setDate(QDate())
        self.edtAntiresusIgCurrPregnEndDate.setDate(QDate())
        self.edtEstimatedBirthsDate.setDate(QDate())
        self.edtExchangeAndNotificationCardClientDate.setDate(QDate())
        self.edtVRTDate.setDate(QDate())
        self.edtLastMenstruationDate.setDate(QDate())
        self.edtFirstUSIDate.setDate(QDate())
        self.edtFirstStirringFetusDate.setDate(QDate())
        self.edtNVNBIBRM13Date.setDate(QDate())
        self.edtNVNBIBRMResultDate.setDate(QDate())
        self.edtNVNBDZKDate.setDate(QDate())
        self.edtNVNBP.setDate(QDate())
        self.edtNVNBDZ.setDate(QDate())
        self.edtSOPVSTATUSDate.setDate(QDate())
        self.edtSOPPFDate.setDate(QDate())
        self.edtSOPOPFDate.setDate(QDate())
        self.edtSOPSOPR1Date.setDate(QDate())
        self.edtSOPSOPR2Date.setDate(QDate())
        self.edtSOPSOPR3Date.setDate(QDate())
        self.edtSOPSOPR4Date.setDate(QDate())
        self.edtSOPSOPR5Date.setDate(QDate())
        self.edtSOPSOPR6Date.setDate(QDate())
        self.edtSOPSOPR7Date.setDate(QDate())
        self.edtSOPSOPR8Date.setDate(QDate())
        self.edtSOPSOPR9Date.setDate(QDate())
        self.edtFirstAppearanceTermDate.setDate(QDate())
        self.edtAppointDate.setDate(QDate())
        self.edtODPOBDO.setDate(QDate())


    def getActionTypeIdListByKBiR(self, flatCode = u'111/y-20'):
        return getActionTypeIdListByFlatCode(flatCode)


    def setEventDate(self, date):
        eventRecord = self._getEventRecord()
        if eventRecord:
            execDate = forceDate(eventRecord.value('execDate'))
            if not execDate:
                self._eventExecDate = date
                self.eventDate = date


    def _getEventRecord(self):
        if not self.recordEvent and self.eventId:
            self.recordEvent = QtGui.qApp.db.getRecordEx('Event', '*', 'id=%d'%self.eventId)
        return self.recordEvent


    def setODPOBRPPGRFVisible(self, value):
        self.lblODPOBRPPGRF_1.setVisible(value)
        self.chkODPOBRPPGRF1_1.setVisible(value)
        self.chkODPOBRPPGRF2_1.setVisible(value)
        self.lblODPOBRPPGRF_2.setVisible(value)
        self.chkODPOBRPPGRF1_2.setVisible(value)
        self.chkODPOBRPPGRF2_2.setVisible(value)
        self.lblODPOBRPPGRF_3.setVisible(value)
        self.chkODPOBRPPGRF1_3.setVisible(value)
        self.chkODPOBRPPGRF2_3.setVisible(value)
        self.lblODPOBRPPGRF_4.setVisible(value)
        self.chkODPOBRPPGRF1_4.setVisible(value)
        self.chkODPOBRPPGRF2_4.setVisible(value)
        self.lblODPOBRPPGRF_5.setVisible(value)
        self.chkODPOBRPPGRF1_5.setVisible(value)
        self.chkODPOBRPPGRF2_5.setVisible(value)


    def setComoboBoxWheel(self, value=False):
        self.cmbPrevOrganisation.setWheel(value)
        self.cmbBloodGroupFather.setWheel(value)
        self.cmbOrg.setWheel(value)
        self.cmbAssistant.setWheel(value)
        self.cmbStatus.setWheel(value)
        self.cmbSetPerson.setWheel(value)
        self.cmbPerson.setWheel(value)
        self.cmbNVNBPNVNBMOdR.setWheel(value)
        self.cmbNVNBPNVNBUAS.setWheel(value)
    
    
    def setReferenceComboBoxes(self):
        db = QtGui.qApp.db
        refComboBoxes = self.getReferenceComboBoxes()
        for cmb, code in refComboBoxes.items():
            obj = None
            tableAPT = db.table('ActionPropertyType')
            record = db.getRecordEx(tableAPT, u'valueDomain', [tableAPT[u'shortName'].eq(code), tableAPT['actionType_id'].inlist(self.actionTypeIdListByKBiR)])
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


    def getDiagnosisMKB(self):
        self.dictDiagnosisMKB = {}
        if self.clientId:
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
            cond = [tableDiagnosis['client_id'].eq(self.clientId),
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
                    self.dictDiagnosisMKB['isNVNBPUDRP'] = isNVNBPUDRP
                isNVNBPUDSM = forceBool(record.value('isNVNBPUDSM'))
                if isNVNBPUDSM:
                    self.dictDiagnosisMKB['isNVNBPUDSM'] = isNVNBPUDSM
                isNVNBPUDSST = forceBool(record.value('isNVNBPUDSST'))
                if isNVNBPUDSST:
                    self.dictDiagnosisMKB['isNVNBPUDSST'] = isNVNBPUDSST
                isNVNBPUDFTB = forceBool(record.value('isNVNBPUDFTB'))
                if isNVNBPUDFTB:
                    self.dictDiagnosisMKB['isNVNBPUDFTB'] = isNVNBPUDFTB
                isNVNBPUDKOV = forceBool(record.value('isNVNBPUDKOV'))
                if isNVNBPUDKOV:
                    self.dictDiagnosisMKB['isNVNBPUDKOV'] = isNVNBPUDKOV
                isNVNBPUDCA = forceBool(record.value('isNVNBPUDCA'))
                if isNVNBPUDCA:
                    self.dictDiagnosisMKB['isNVNBPUDCA'] = isNVNBPUDCA
        if self.dictDiagnosisMKB:
            self.frame_44.setVisible(True)
            isNVNBPUDRP = (self.dictDiagnosisMKB.get('isNVNBPUDRP', False))
            self.lblNVNBPUDRP.setVisible(isNVNBPUDRP)
            self.cmbNVNBPUDRP.setVisible(isNVNBPUDRP)
            isNVNBPUDSM = (self.dictDiagnosisMKB.get('isNVNBPUDSM', False))
            self.lblNVNBPUDSM.setVisible(isNVNBPUDSM)
            self.cmbNVNBPUDSM.setVisible(isNVNBPUDSM)
            isNVNBPUDFTB = (self.dictDiagnosisMKB.get('isNVNBPUDFTB', False))
            self.lblNVNBPUDFTB.setVisible(isNVNBPUDFTB)
            self.cmbNVNBPUDFTB.setVisible(isNVNBPUDFTB)
            isNVNBPUDSST = (self.dictDiagnosisMKB.get('isNVNBPUDSST', False))
            self.lblNVNBPUDSST.setVisible(isNVNBPUDSST)
            self.cmbNVNBPUDSST.setVisible(isNVNBPUDSST)
            isNVNBPUDKOV = (self.dictDiagnosisMKB.get('isNVNBPUDKOV', False))
            self.lblNVNBPUDKOV.setVisible(isNVNBPUDKOV)
            self.cmbNVNBPUDKOV.setVisible(isNVNBPUDKOV)
            isNVNBPUDCA = (self.dictDiagnosisMKB.get('isNVNBPUDCA', False))
            self.lblNVNBPUDCA.setVisible(isNVNBPUDCA)
            self.cmbNVNBPUDCA.setVisible(isNVNBPUDCA)
        else:
            self.frame_44.setVisible(False)


    @pyqtSlot()
    def on_btnApply_clicked(self):
        if self.applyChanges():
            buttons = QtGui.QMessageBox.Ok
            messageBox = QtGui.QMessageBox()
            messageBox.setWindowFlags(messageBox.windowFlags() | Qt.WindowStaysOnTopHint)
            messageBox.setWindowTitle(u'Внимание!')
            messageBox.setText(u'Данные сохранены')
            messageBox.setStandardButtons(buttons)
            messageBox.setDefaultButton(QtGui.QMessageBox.Ok)
            messageBox.exec_()


    def applyChanges(self):
        if self.saveData():
            QtGui.qApp.delAllCounterValueIdReservation()
            self.lock(self._tableName, self._id)
            return True
        else:
            return False


    @pyqtSlot(QtGui.QAbstractButton)
    def on_buttonBox_clicked(self, button):
        buttonCode = self.buttonBox.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Save:
            self.save()


    def exec_(self):
        counterController = QtGui.qApp.counterController()
        if not counterController:
            QtGui.qApp.setCounterController(CCounterController(self))
            QtGui.qApp.setJTR(self)
        try:
            if self.lock(self._tableName, self._id):
                try:
                    if self._id:
                        db = QtGui.qApp.db
                        record = db.getRecord(db.table(self._tableName), '*', self._id)
                        self.setRecord(record)
                        self.setIsDirty(False)
                        if not self.checkDataBeforeOpen():
                            return QtGui.QDialog.Rejected
                    self.loadDialogPreferences()
                    rect = self.frameGeometry()
                    pos = self.pos()
                    if pos.x() < 0 or pos.y() < 0:
                        rect.moveCenter(QtGui.qApp.desktop().availableGeometry().center())
                        self.setGeometry(rect)
                    result = QtGui.QDialog.exec_(self)
                finally:
                    self.releaseLock()
            else:
                result = QtGui.QDialog.Rejected
                self.setResult(result)
        finally:
            QtGui.qApp.unsetJTR(self)
        if result:
            QtGui.qApp.delAllCounterValueIdReservation()
        else:
            QtGui.qApp.resetAllCounterValueIdReservation()
        QtGui.qApp.setCounterController(None)
        QtGui.qApp.disconnectClipboard()
        return result


    def destroy(self):
        CItemEditorBaseDialog.destroy(self)
        self.tabAmbCard.deleteLater()


    def getClientId(self, eventId):
        if self.forceClientId:
            return self.forceClientId
        return forceRef(QtGui.qApp.db.translate('Event', 'id', eventId, 'client_id'))


    def setComboBoxes(self):
        self.setPropertyDomainWidget(self.cmbBloodGroupFather, u'ОД:ОДП:ГКО:1', isNotDefined = True)


    def setPropertyDomainWidget(self, widget, propertyShortName, isNotDefined = True):
        widget._model.clear()
        domain, defaultValue = self.getPropertyDomain(propertyShortName, isNotDefined)
        widget.setDomain(domain, isUpdateCurrIndex=False)
        if self.isCreate:
            if defaultValue:
                widget.setValue(defaultValue)
            else:
                widget.setCurrentIndex(0)


    def getPropertyDomain(self, propertyShortName, isNotDefined = True):
        domain = u'\'не определено\',' if isNotDefined else u''
        record, defaultValue = self.propertyDomain(propertyShortName)
        if record:
            domainR = forceString(record)
            if u'*' in domainR:
                index = domainR.index(u'*')
                if domainR[index - 1] != u',':
                    domainR = domainR.replace('*', ',')
                else:
                    domainR = domainR.replace('*', '')
            domain += domainR
            if u'[mc]' in domain:
                domain = domain.replace(u'[mc]', '')
        return domain, defaultValue


    def propertyDomain(self, propertyShortName):
        if not self.actionTypeIdListByKBiR:
            return None, None
        db = QtGui.qApp.db
        tableAPT = db.table('ActionPropertyType')
        tableActionType = db.table('ActionType')
        cond =[tableActionType['id'].inlist(self.actionTypeIdListByKBiR),
               tableAPT['shortName'].like(propertyShortName),
               tableActionType['deleted'].eq(0),
               tableAPT['deleted'].eq(0)
               ]
        if self.actionTypeId:
            cond.append(tableAPT['actionType_id'].eq(self.actionTypeId))
        queryTable = tableActionType.innerJoin(tableAPT, tableActionType['id'].eq(tableAPT['actionType_id']))
        record = db.getRecordEx(queryTable, [tableAPT['valueDomain'], tableAPT['defaultValue']], cond)
        if record:
            return record.value(0), record.value(1)
        return None, None


    @pyqtSlot(int)
    def on_tabClient_currentChanged(self, index):
        widget = self.tabClient.widget(index)
        if widget is not None:
            focusProxy = widget.focusProxy()
            if focusProxy:
                focusProxy.setFocus(Qt.OtherFocusReason)
        if widget == self.tabAmbCard:
            self.tabAmbCard.resetWidgets()


    def setRecord(self, record):
        CItemEditorBaseDialog.setRecord(self, record)
        self.eventId = forceRef(record.value('event_id'))
        self.eventTypeId = None
        self.eventSetDate = None
        self.eventSetDateTime = None
        self.eventDate = None
        self.recordEvent = None
        self.newRecordClientSocStatus = None
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
        self.edtNVNBDZKDate.setDate(self.eventDate)
        self.clientId = self.getClientId(self.eventId)
        self.action = CAction(record=record)
        actionType = self.action.getType()
        self.actionTypeId = actionType.id
        self.getDiagnosisMKB()
        self.setComboBoxes()
        self.action.executionPlanManager.load()
        self.action.executionPlanManager.setCurrentItemIndex()
        showTime = actionType.showTime
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
        
        if self.clientId:
            tableClient = db.table('Client')
            tableRBBloodType = db.table('rbBloodType')
            table = tableClient.leftJoin(tableRBBloodType, tableRBBloodType['id'].eq(tableClient['bloodType_id']))
            recordClient = db.getRecordEx(table, [tableRBBloodType['name']], [tableClient['id'].eq(self.clientId), tableClient['deleted'].eq(0)])
        if recordClient:
            isRhNegative = u'Rh-' in forceStringEx(recordClient.value('name'))
            if not isRhNegative:
                self.clearODPOBRPPGRF()
            self.setODPOBRPPGRFVisible(isRhNegative)
        
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
        self.modelSOPSvORNM.setAction(self.action)
        self.modelSOPSvORNM.loadItems(self.clientId)
        self.modelNVNBVARRS.setAction(self.action)
        self.modelNVNBVARRS.loadItems(self.clientId)
        self.modelNVNBAR.setAction(self.action)
        self.modelNVNBAR.loadItems(self.clientId)
        self.modelNVNBSGVB.setAction(self.action)
        self.modelNVNBSGVB.loadItems(self.clientId)
        self.modelPreviousPregnancy.loadItems(self.action.getId())
        conActionId = self.modelPreviousPregnancy.getActionIdToRow(0)
        conItems = self.modelPreviousPregnancy.items()
        if conItems and hasattr(conItems[0], 'aboutChildrenProperties'):
            self.modelPreviousPregnancyChildren.setItems(conItems[0].aboutChildrenProperties.getItems())
        else:
            self.modelPreviousPregnancyChildren.clearItems()
        self.updatePreviousPregnancyChildren(self.modelPreviousPregnancy.index(0, 0), self.tblPreviousPregnancyChildren, actionId=conActionId)
        if self.recordEvent:
            self.tabNotes.setNotes(self.recordEvent)
            self.tabNotes.setEventEditor(self)
        self.on_btnBoxPregnancyRetrospect_apply()


    def getShortNameTextEdit(self):
        return [u'ОД:ОДП:ОУК:1', u'ОД:СНБ:ПП:2', u'ОД:ПОБ:Ж:2', u'ОД:ПОБ:О:2', u'ОД:ПОБ:УЛУ:2',
        u'ОД:ПОБ:ОПМЖ:2', u'ОД:ПОБ:С:2', u'ОД:ПОБ:ТС:2', u'ОД:ГО:ОШМЗ:2', u'ОД:ГО:ВИ:НПО:2',
        u'ОД:ГО:ВИ:В:2', u'ОД:ГО:ВИ:ШМ:3', u'ОД:ГО:ВИ:ШМ:5', u'ОД:ГО:ВИ:ТМ:3', u'ОД:ГО:ВИ:ОП', u'ОД:ГО:ВИ:ПСл:2',
        u'ОД:ГО:ВИ:ПСп:2', u'ОД:ГО:ВИ:Э:2', u'ОД:ГО:ВИ:ОЦК', u'ОД:ГО:ВИ:ОБ', u'ОД:ГО:ВИ:Ан', u'ОД:ГО:ВИ:Наз', u'НВНБ:ДГ:2',
        u'НВНБ:ДГ:4', u'НВНБ:Пелв:10', u'НВНБ:ИБРМ:5', u'НВНБ:ИБРМ:9', u'НВНБ:ИБРП:1:6',
        u'НВНБ:ИБРП:1:10', u'СОП:ВПР:2', u'СОП:ДР:1', u'СОП:ПЗ:ДИ:2', u'СОП:ПЗ:НДУ:2', u'СОП:ПЗ:СЗ:2', u'СОП:ПЗ:СЗИ:2', u'СОП:ПЗ:ВИЧ:3',
        u'СОП:ПЗ:АТ', u'СОП:ПЗ:НЗ:2', u'СОП:ПЗ:ПФ:2', u'СОП:ВП:3', u'СОП:ВП:5', u'СОП:ВП:7', u'СОП:ПВ:2', u'СОП:Контрац',
        u'СОП:ГЗО', u'СОП:ИППП:2', u'СОП:ПЦИМШМ:3', u'СОП:ПИМЖ:3', u'СОП:СОР:ХЗ:2', u'СОП:СОР:ИППП:2', u'СОП:СОР:СЗП:2', u'СОП:СОР:ПФ:2']


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
                    if (isinstance(propertyValue, basestring) or propertyValue.__class__.__name__ == 'QString') and not isShortNameTextEdit:
                        propertyValue = trim(propertyValue)
                    if propertyValue:
                        item = items.get(shortName, [])
                        if propertyValue and (isinstance(propertyValue, basestring) or propertyValue.__class__.__name__ == 'QString') and len(propertyValue) > 1 and not isShortNameTextEdit:
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
                    if (isinstance(propertyValue, basestring) or propertyValue.__class__.__name__ == 'QString') and not isShortNameTextEdit:
                        propertyValue = trim(propertyValue)
                    if propertyValue:
                        item = items.get(shortName, [])
                        if propertyValue and (isinstance(propertyValue, basestring) or propertyValue.__class__.__name__ == 'QString') and len(propertyValue) > 1 and not isShortNameTextEdit:
                            propertyValue = propertyValue.split(u',')
                            item.extend(propertyValue)
                        else:
                            item.append(propertyValue)
                        items[shortName] = item
            if items:
                # #tabBasicData
                # tabGeneralDataAboutPatient
                isMaritalStatus = self.getChkPropertyValue(items, u'ОД:ОДП:БС', [u'брак зарегистрирован',u'брак не зарегистрирован',u'одинокая'])
                self.chkMaritalStatus1.setChecked(isMaritalStatus == 1)
                self.chkMaritalStatus2.setChecked(isMaritalStatus == 2)
                self.chkMaritalStatus3.setChecked(isMaritalStatus == 3)
                self.edtBegDateMaternityLeave.setDate(self.getPropertyValue(items, u'ОД:ОДП:ДО:1', QDate))
                self.edtEndDateMaternityLeave.setDate(self.getPropertyValue(items, u'ОД:ОДП:ДО:2', QDate))
                self.edtGenericCertificateSeria.setText(self.getPropertyValue(items, u'ОД:ОДП:РС:1', unicode))
                self.edtGenericCertificateNumber.setText(self.getPropertyValue(items, u'ОД:ОДП:РС:2', unicode))
                self.edtGenericCertificateDate.setDate(self.getPropertyValue(items, u'ОД:ОДП:РС:3', QDate))
                self.cmbBloodGroupFather.setValue(self.getPropertyValue(items, u'ОД:ОДП:ГКО:1', unicode))
                self.edtBloodGroupFatherDate.setDate(self.getPropertyValue(items, u'ОД:ОДП:ГКО:2', QDate))
                self.edtAntiresusIgPrevPregnBegDate.setDate(self.getPropertyValue(items, u'ОД:ОДП:ДАР:ППБ:1', QDate))
                self.edtAntiresusIgPrevPregnEndDate.setDate(self.getPropertyValue(items, u'ОД:ОДП:ДАР:ППБ:2', QDate))
                self.edtAntiresusIgCurrPregnBegDate.setDate(self.getPropertyValue(items, u'ОД:ОДП:ДАР:ПТБ:1', QDate))
                self.edtAntiresusIgCurrPregnEndDate.setDate(self.getPropertyValue(items, u'ОД:ОДП:ДАР:ПТБ:2', QDate))
                self.edtPregnancyByAccount.setValue(self.getPropertyValue(items, u'ОД:ОДП:ДБпС', int))
                self.edtBirthsByAccount.setValue(self.getPropertyValue(items, u'ОД:ОДП:ДРпС', int))
                self.edtFirstAppearanceTerm.setValue(self.getPropertyValue(items, u'ОД:ОДП:СПЯ', int))
                self.edtFirstAppearanceTermDays.setValue(self.getPropertyValue(items, u'ОД:ОДП:СПЯД', int))
                if isCreate:
                    self.setProperty(QVariant(self.edtFirstAppearanceTermDate.date()), u'ОД:ОДП:ДПЯ')
                else:
                    self.edtFirstAppearanceTermDate.setDate(self.getPropertyValue(items, u'ОД:ОДП:ДПЯ', QDate))
                self.edtAppointTermWeeks.setValue(self.getPropertyValue(items, u'ОД:ОДП:СПНУ:1', int))
                self.edtAppointTermDays.setValue(self.getPropertyValue(items, u'ОД:ОДП:СПНУ:2', int))
                if isCreate:
                    self.setProperty(QVariant(self.edtAppointDate.date()), u'ОД:ОДП:СПНУ:3')
                else:
                    self.edtAppointDate.setDate(self.getPropertyValue(items, u'ОД:ОДП:СПНУ:3', QDate))
                self.cmbPrevOrganisation.setCurrentIndex(self.cmbPrevOrganisation.findText(self.getPropertyValue(items, u'ОД:ОДП:ТУПНП', QComboBox) ))
                self.edtEstimatedBirthsDate.setDate(self.getPropertyValue(items, u'ОД:ОДП:ПДР:1', QDate))
                self.edtEstimatedTermDate.setValue(self.getPropertyValue(items, u'ОД:ОДП:ПДР:2', int))
                self.edtExchangeAndNotificationCardNumber.setText(self.getPropertyValue(items, u'ОД:ОДП:ОУК:1', unicode))
                self.edtExchangeAndNotificationCardClientDate.setDate(self.getPropertyValue(items, u'ОД:ОДП:ОУК:2', QDate))
                isBeginPregnancy = self.getChkPropertyValue(items, u'ОД:СНБ:БН', [u'спонтанно',u'индуцирована',u'с помощью ВРТ'])
                self.chkSpontaneously.setChecked(isBeginPregnancy == 1)
                self.chkInduced.setChecked(isBeginPregnancy == 2)
                self.chkWithHelpVRT.setChecked(isBeginPregnancy == 3)
                isPregravidar = self.getChkPropertyValue(items, u'ОД:СНБ:ПП:1', [u'нет',u'да'])
                self.chkPregravidarNot.setChecked(isPregravidar == 1)
                self.chkPregravidarYes.setChecked(isPregravidar == 2)
                self.edtPregravidarText.setText(self.getPropertyValue(items, u'ОД:СНБ:ПП:2', unicode))
                self.edtVRTNumber.setValue(self.getPropertyValue(items, u'ОД:СНБ:ВРТ:1', int))
                self.edtVRTDate.setDate(self.getPropertyValue(items, u'ОД:СНБ:ВРТ:2', QDate))
                isTransferFetus = self.getChkPropertyValue(items, u'ОД:СНБ:ВРТ:3', [u'нативного',u'криоконсервированного'])
                self.chkVRTNative.setChecked(isTransferFetus == 1)
                self.chkCryopreserved.setChecked(isTransferFetus == 2)
                self.edtEmbryosCount.setValue(self.getPropertyValue(items, u'ОД:СНБ:ВРТ:4', int))
                self.edtAgePatientCryopreservedDate.setValue(self.getPropertyValue(items, u'ОД:СНБ:ВРТ:5', int))
                isPregnancyType = self.getChkPropertyValue(items, u'ОД:СНБ:Б:1', [u'одноплодная',u'многоплодная'])
                self.chkOneFetus.setChecked(isPregnancyType == 1)
                self.chkMultipleFetus.setChecked(isPregnancyType == 2)
                self.edtFetusCount.setValue(self.getPropertyValue(items, u'ОД:СНБ:Б:2', int))
                self.edtLastMenstruationDate.setDate(self.getPropertyValue(items, u'ОД:СНБ:ПМ', QDate))
                self.edtFirstUSIDate.setDate(self.getPropertyValue(items, u'ОД:СНБ:ДУЗИ', QDate))
                self.edtFirstUSITermWeeks.setValue(self.getPropertyValue(items, u'ОД:СНБ:ДУЗИ:Н', int))
                self.edtFirstUSITermDays.setValue(self.getPropertyValue(items, u'ОД:СНБ:ДУЗИ:Д', int))
                self.edtFirstStirringFetusDate.setDate(self.getPropertyValue(items, u'ОД:СНБ:ПШП', QDate))
                # tabFirstExaminationPregnant
                if isCreate:
                    self.setProperty(QVariant(self.edtODPOBDO.date()), u'ОД:ПОБ:ДО')
                else:
                    self.edtODPOBDO.setDate(self.getPropertyValue(items, u'ОД:ПОБ:ДО', QDate))
                isODPOBG = self.getChkPropertyValue(items, u'ОД:ПОБ:Ж:1', [u'нет',u'да'])
                self.chkODPOBGNot.setChecked(isODPOBG == 1)
                self.chkODPOBGYes.setChecked(isODPOBG == 2)
                self.edtODPOBGText.setText(self.getPropertyValue(items, u'ОД:ПОБ:Ж:2', unicode))
                isODPOBRVGK = self.getChkPropertyValue(items, u'ОД:ПОБ:РВЖК:1', [u'по женскому типу',u'по мужскому типу'])
                self.chkODPOBRVGKWoman.setChecked(isODPOBRVGK == 1)
                self.chkODPOBRVGKMen.setChecked(isODPOBRVGK == 2)
                isODPOBRVGK2 = self.getChkPropertyValue(items, u'ОД:ПОБ:РВЖК:2', [u'недостаточно выражена',u'нормально выражена',u'избыточно выражена'])
                self.chkODPOBRVGKNotEnough.setChecked(isODPOBRVGK2 == 1)
                self.chkODPOBRVGKNormal.setChecked(isODPOBRVGK2 == 2)
                self.chkODPOBRVGKRedundant.setChecked(isODPOBRVGK2 == 3)
                isODPOBO = self.getChkPropertyValue(items, u'ОД:ПОБ:О:1', [u'нет',u'да'])
                self.chkODPOBONot.setChecked(isODPOBO == 1)
                self.chkODPOBOYes.setChecked(isODPOBO == 2)
                self.edtODPOBOLocalizationText.setText(self.getPropertyValue(items, u'ОД:ПОБ:О:2', unicode))
                isODPOBVRVNK = self.getChkPropertyValue(items, u'ОД:ПОБ:ВРВНК', [u'нет',u'да'])
                self.chkODPOBVRVNKNot.setChecked(isODPOBVRVNK == 1)
                self.chkODPOBVRVNKYes.setChecked(isODPOBVRVNK == 2)
                isODPOBULU = self.getChkPropertyValue(items, u'ОД:ПОБ:УЛУ:1', [u'нет',u'да'])
                self.chkODPOBULUNot.setChecked(isODPOBULU == 1)
                self.chkODPOBULUYes.setChecked(isODPOBULU == 2)
                self.edtODPOBULULocalizationText.setText(self.getPropertyValue(items, u'ОД:ПОБ:УЛУ:2', unicode))
                isODPOBOPMG = self.getChkPropertyValue(items, u'ОД:ПОБ:ОПМЖ:1', [u'патологических изменений нет',u'признаки фиброзно-кистозной мистопатии',u'пальпируется узловое образование'])
                self.chkODPOBOPMG1.setChecked(isODPOBOPMG == 1)
                self.chkODPOBOPMG2.setChecked(isODPOBOPMG == 2)
                self.chkODPOBOPMG3.setChecked(isODPOBOPMG == 3)
                self.edtODPOBOPMG3Text.setText(self.getPropertyValue(items, u'ОД:ПОБ:ОПМЖ:2', unicode))
                isODPOBOPMG2 = self.getChkPropertyValue(items, u'ОД:ПОБ:ОПМЖ:3', [u'безболезненны',u'масталгия'])
                self.chkODPOBOPMG4.setChecked(isODPOBOPMG2 == 1)
                self.chkODPOBOPMG5.setChecked(isODPOBOPMG2 == 2)
                isODPOBC = self.getChkPropertyValue(items, u'ОД:ПОБ:С:1', [u'сформированы правильно',u'втянуты', u'другие изменения'])
                self.chkODPOBC1.setChecked(isODPOBC == 1)
                self.chkODPOBC2.setChecked(isODPOBC == 2)
                self.chkODPOBC3.setChecked(isODPOBC == 3)
                self.edtODPOBC3Text.setText(self.getPropertyValue(items, u'ОД:ПОБ:С:2', unicode))
                isODPOBTS = self.getChkPropertyValue(items, u'ОД:ПОБ:ТС:1', [u'ясные',u'другие'])
                self.chkODPOBTS1.setChecked(isODPOBTS == 1)
                self.chkODPOBTS2.setChecked(isODPOBTS == 2)
                self.edtODPOBTS2Text.setText(self.getPropertyValue(items, u'ОД:ПОБ:ТС:2', unicode))
                self.edtODPOBP.setValue(self.getPropertyValue(items, u'ОД:ПОБ:П', int))
                self.edtODPOBADPR.setText(self.getPropertyValue(items, u'ОД:ПОБ:АД:1', unicode))
                self.edtODPOBADLR.setText(self.getPropertyValue(items, u'ОД:ПОБ:АД:2', unicode))
                isODPOBAL = self.getChkPropertyValue(items, u'ОД:ПОБ:АЛ:1', [u'дыхание везикулярное', u'другое'])
                self.chkODPOBAL1.setChecked(isODPOBAL == 1)
                self.chkODPOBAL2.setChecked(isODPOBAL == 2)
                self.edtODPOBAL2Text.setText(self.getPropertyValue(items, u'ОД:ПОБ:АЛ:2', unicode))
                isODPOBSP = self.getChkPropertyValue(items, u'ОД:ПОБ:ШП16', [u'ощущает',u'не ощущает'])
                self.chkODPOBSP1.setChecked(isODPOBSP == 1)
                self.chkODPOBSP2.setChecked(isODPOBSP == 2)
                self.edtODPOBOG.setValue(self.getPropertyValue(items, u'ОД:ПОБ:ОЖ20', int))
                self.edtODPOBVDM.setValue(self.getPropertyValue(items, u'ОД:ПОБ:ВДМ20', int))

                #Первый ребёнок
                self.edtODPOBSBP.setValue(self.getPropertyValue(items, u'ОД:ПОБ:СП12', int))
                self.cmbODPOBPP1.setValue(self.getPropertyValue(items, u'ОД:ПОБ:ПП34:s', int))
                self.cmbODPOBNVMTO_1.setValue(self.getPropertyValue(items, u'ОД:ПОБ:НВМТО34:1:s', int))
                self.cmbODPOBCZVRP_1.setValue(self.getPropertyValue(items, u'ОД:ПОБ:СЗВРП:1:s', int))
                isODPOBGCH = self.getChkPropertyValue(items, u'ОД:ПОБ:ПЧ34', [u'прижата',u'подвижна'])
                self.chkODPOBGCH1_1.setChecked(isODPOBGCH == 1)
                self.chkODPOBGCH2_1.setChecked(isODPOBGCH == 2)
                isODPOBMT = self.getChkPropertyValue(items, u'ОД:ПОБ:МТ:1', [u'Над входом в малый таз', u'Не определяется'])
                self.chkODPOBMT1_1.setChecked(isODPOBMT == 1)
                self.chkODPOBMT1_2.setChecked(isODPOBMT == 2)
                isODPOBSBPRList = self.getChkPropertyList(items, u'ОД:ПОБ:СПР1:1', [u'Ясное',u'Ритмичное',u'Другое'])
                for isODPOBSBPR in isODPOBSBPRList:
                    if isODPOBSBPR == 1:
                        self.chkODPOBSBPR1_1.setChecked(True)
                    elif isODPOBSBPR == 2:
                        self.chkODPOBSBPR2_1.setChecked(True)
                    elif isODPOBSBPR == 3:
                        self.chkODPOBSBPR3_1.setChecked(True)
                        self.edtODPOBSBPR_1.setText(self.getPropertyValue(items, u'ОД:ПОБ:СПР2:1', unicode))
                self.edtEstimatedWeight_1.setValue(self.getPropertyValue(items, u'ОД:ПОБ:ПМ:1', int))
                isODPOBRPPGRF = self.getChkPropertyValue(items, u'ОД:ПОБ:РППГРФ:1', [u'обнаружен',u'не обнаружен'])
                self.chkODPOBRPPGRF1_1.setChecked(isODPOBRPPGRF == 1)
                self.chkODPOBRPPGRF2_1.setChecked(isODPOBRPPGRF == 2)

                #Второй ребёнок
                self.edtODPOBSBP_2.setValue(self.getPropertyValue(items, u'ОД:ПОБ:СП12:2', int))
                self.cmbODPOBPP_2.setValue(self.getPropertyValue(items, u'ОД:ПОБ:ПП34:2:s', int))
                self.cmbODPOBNVMTO_2.setValue(self.getPropertyValue(items, u'ОД:ПОБ:НВМТО34:2:s', int))
                self.cmbODPOBCZVRP_2.setValue(self.getPropertyValue(items, u'ОД:ПОБ:СЗВРП:2:s', int))
                isODPOBGCH = self.getChkPropertyValue(items, u'ОД:ПОБ:ПЧ34:2', [u'прижата',u'подвижна'])
                self.chkODPOBGCH1_2.setChecked(isODPOBGCH == 1)
                self.chkODPOBGCH2_2.setChecked(isODPOBGCH == 2)
                isODPOBMT = self.getChkPropertyValue(items, u'ОД:ПОБ:МТ:2', [u'Над входом в малый таз', u'Не определяется'])
                self.chkODPOBMT1_2.setChecked(isODPOBMT == 1)
                self.chkODPOBMT2_2.setChecked(isODPOBMT == 2)
                isODPOBSBPRList = self.getChkPropertyList(items, u'ОД:ПОБ:СПР1:2', [u'Ясное',u'Ритмичное',u'Другое'])
                for isODPOBSBPR in isODPOBSBPRList:
                    if isODPOBSBPR == 1:
                        self.chkODPOBSBPR1_2.setChecked(True)
                    elif isODPOBSBPR == 2:
                        self.chkODPOBSBPR2_2.setChecked(True)
                    elif isODPOBSBPR == 3:
                        self.chkODPOBSBPR3_2.setChecked(True)
                        self.edtODPOBSBPR_2.setText(self.getPropertyValue(items, u'ОД:ПОБ:СПР2:2', unicode))
                self.edtEstimatedWeight_2.setValue(self.getPropertyValue(items, u'ОД:ПОБ:ПМ:2', int))
                isODPOBRPPGRF = self.getChkPropertyValue(items, u'ОД:ПОБ:РППГРФ:2', [u'обнаружен',u'не обнаружен'])
                self.chkODPOBRPPGRF1_2.setChecked(isODPOBRPPGRF == 1)
                self.chkODPOBRPPGRF2_2.setChecked(isODPOBRPPGRF == 2)

                #Третий ребёнок
                self.edtODPOBSBP_3.setValue(self.getPropertyValue(items, u'ОД:ПОБ:СП12:3', int))
                self.cmbODPOBPP_3.setValue(self.getPropertyValue(items, u'ОД:ПОБ:ПП34:3:s', int))
                self.cmbODPOBNVMTO_3.setValue(self.getPropertyValue(items, u'ОД:ПОБ:НВМТО34:3:s', int))
                self.cmbODPOBCZVRP_3.setValue(self.getPropertyValue(items, u'ОД:ПОБ:СЗВРП:3:s', int))
                isODPOBGCH = self.getChkPropertyValue(items, u'ОД:ПОБ:ПЧ34:3', [u'прижата',u'подвижна'])
                self.chkODPOBGCH1_3.setChecked(isODPOBGCH == 1)
                self.chkODPOBGCH2_3.setChecked(isODPOBGCH == 2)
                isODPOBMT = self.getChkPropertyValue(items, u'ОД:ПОБ:МТ:3', [u'Над входом в малый таз', u'Не определяется'])
                self.chkODPOBMT1_3.setChecked(isODPOBMT == 1)
                self.chkODPOBMT2_3.setChecked(isODPOBMT == 2)
                isODPOBSBPRList = self.getChkPropertyList(items, u'ОД:ПОБ:СПР1:3', [u'Ясное',u'Ритмичное',u'Другое'])
                for isODPOBSBPR in isODPOBSBPRList:
                    if isODPOBSBPR == 1:
                        self.chkODPOBSBPR1_3.setChecked(True)
                    elif isODPOBSBPR == 2:
                        self.chkODPOBSBPR2_3.setChecked(True)
                    elif isODPOBSBPR == 3:
                        self.chkODPOBSBPR3_3.setChecked(True)
                        self.edtODPOBSBPR_3.setText(self.getPropertyValue(items, u'ОД:ПОБ:СПР2:3', unicode))
                self.edtEstimatedWeight_3.setValue(self.getPropertyValue(items, u'ОД:ПОБ:ПМ:3', int))
                isODPOBRPPGRF = self.getChkPropertyValue(items, u'ОД:ПОБ:РППГРФ:3', [u'обнаружен',u'не обнаружен'])
                self.chkODPOBRPPGRF1_3.setChecked(isODPOBRPPGRF == 1)
                self.chkODPOBRPPGRF2_3.setChecked(isODPOBRPPGRF == 2)

                #Четвёртый ребёнок
                self.edtODPOBSBP_4.setValue(self.getPropertyValue(items, u'ОД:ПОБ:СП12:4', int))
                self.cmbODPOBPP_4.setValue(self.getPropertyValue(items, u'ОД:ПОБ:ПП34:4:s', int))
                self.cmbODPOBNVMTO_4.setValue(self.getPropertyValue(items, u'ОД:ПОБ:НВМТО34:4:s', int))
                self.cmbODPOBCZVRP_4.setValue(self.getPropertyValue(items, u'ОД:ПОБ:СЗВРП:4:s', int))
                isODPOBGCH = self.getChkPropertyValue(items, u'ОД:ПОБ:ПЧ34:4', [u'прижата',u'подвижна'])
                self.chkODPOBGCH1_4.setChecked(isODPOBGCH == 1)
                self.chkODPOBGCH2_4.setChecked(isODPOBGCH == 2)
                isODPOBMT = self.getChkPropertyValue(items, u'ОД:ПОБ:МТ:4', [u'Над входом в малый таз', u'Не определяется'])
                self.chkODPOBMT1_4.setChecked(isODPOBMT == 1)
                self.chkODPOBMT2_4.setChecked(isODPOBMT == 2)
                isODPOBSBPRList = self.getChkPropertyList(items, u'ОД:ПОБ:СПР1:4', [u'Ясное',u'Ритмичное',u'Другое'])
                for isODPOBSBPR in isODPOBSBPRList:
                    if isODPOBSBPR == 1:
                        self.chkODPOBSBPR1_4.setChecked(True)
                    elif isODPOBSBPR == 2:
                        self.chkODPOBSBPR2_4.setChecked(True)
                    elif isODPOBSBPR == 3:
                        self.chkODPOBSBPR3_4.setChecked(True)
                        self.edtODPOBSBPR_4.setText(self.getPropertyValue(items, u'ОД:ПОБ:СПР2:4', unicode))
                self.edtEstimatedWeight_4.setValue(self.getPropertyValue(items, u'ОД:ПОБ:ПМ:4', int))
                isODPOBRPPGRF = self.getChkPropertyValue(items, u'ОД:ПОБ:РППГРФ:4', [u'обнаружен',u'не обнаружен'])
                self.chkODPOBRPPGRF1_4.setChecked(isODPOBRPPGRF == 1)
                self.chkODPOBRPPGRF2_4.setChecked(isODPOBRPPGRF == 2)

                #Пятый ребёнок
                self.edtODPOBSBP_5.setValue(self.getPropertyValue(items, u'ОД:ПОБ:СП12:5', int))
                self.cmbODPOBPP_5.setValue(self.getPropertyValue(items, u'ОД:ПОБ:ПП34:5:s', int))
                self.cmbODPOBNVMTO_5.setValue(self.getPropertyValue(items, u'ОД:ПОБ:НВМТО34:5:s', int))
                self.cmbODPOBCZVRP_5.setValue(self.getPropertyValue(items, u'ОД:ПОБ:СЗВРП:5:s', int))
                isODPOBGCH = self.getChkPropertyValue(items, u'ОД:ПОБ:ПЧ34:5', [u'прижата',u'подвижна'])
                self.chkODPOBGCH1_5.setChecked(isODPOBGCH == 1)
                self.chkODPOBGCH2_5.setChecked(isODPOBGCH == 2)
                isODPOBMT = self.getChkPropertyValue(items, u'ОД:ПОБ:МТ:5', [u'Над входом в малый таз', u'Не определяется'])
                self.chkODPOBMT1_5.setChecked(isODPOBMT == 1)
                self.chkODPOBMT2_5.setChecked(isODPOBMT == 2)
                isODPOBSBPRList = self.getChkPropertyList(items, u'ОД:ПОБ:СПР1:5', [u'Ясное',u'Ритмичное',u'Другое'])
                for isODPOBSBPR in isODPOBSBPRList:
                    if isODPOBSBPR == 1:
                        self.chkODPOBSBPR1_5.setChecked(True)
                    elif isODPOBSBPR == 2:
                        self.chkODPOBSBPR2_5.setChecked(True)
                    elif isODPOBSBPR == 3:
                        self.chkODPOBSBPR3_5.setChecked(True)
                        self.edtODPOBSBPR_5.setText(self.getPropertyValue(items, u'ОД:ПОБ:СПР2:5', unicode))
                self.edtEstimatedWeight_5.setValue(self.getPropertyValue(items, u'ОД:ПОБ:ПМ:5', int))
                isODPOBRPPGRF = self.getChkPropertyValue(items, u'ОД:ПОБ:РППГРФ:5', [u'обнаружен',u'не обнаружен'])
                self.chkODPOBRPPGRF1_5.setChecked(isODPOBRPPGRF == 1)
                self.chkODPOBRPPGRF2_5.setChecked(isODPOBRPPGRF == 2)

                # tabGynecologicalExamination
                isODGOOSMZ = self.getChkPropertyValue(items, u'ОД:ГО:ОШМЗ:1', [u'визуально не изменена', u'другое'])
                self.chkODGOOSMZ1.setChecked(isODGOOSMZ == 1)
                self.chkODGOOSMZ2.setChecked(isODGOOSMZ == 2)
                self.edtODGOOSMZ2Text.setText(self.getPropertyValue(items, u'ОД:ГО:ОШМЗ:2', unicode))
                isODGONPO = self.getChkPropertyValue(items, u'ОД:ГО:ВИ:НПО:1', [u'развиты правильно', u'указать отклонение'])
                self.chkODGONPO1.setChecked(isODGONPO == 1)
                self.chkODGONPO2.setChecked(isODGONPO == 2)
                self.edtODGONPO2Text.setText(self.getPropertyValue(items, u'ОД:ГО:ВИ:НПО:2', unicode))
                isODGOV = self.getChkPropertyValue(items, u'ОД:ГО:ВИ:В:1', [u'без патологии', u'указать отклонение'])
                self.chkODGOV1.setChecked(isODGOV == 1)
                self.chkODGOV2.setChecked(isODGOV == 2)
                self.edtODGOV2Text.setText(self.getPropertyValue(items, u'ОД:ГО:ВИ:В:2', unicode))
                isODGOSM = self.getChkPropertyValue(items, u'ОД:ГО:ВИ:ШМ:1', [u'плотная',u'размягчённая',u'мягкая',u'другое'])
                self.chkODGOSM1.setChecked(isODGOSM == 1)
                self.chkODGOSM2.setChecked(isODGOSM == 2)
                self.chkODGOSM3.setChecked(isODGOSM == 3)
                self.chkODGOSM4.setChecked(isODGOSM == 4)
                self.edtODGODSM.setValue(self.getPropertyValue(items, u'ОД:ГО:ВИ:ШМ:2', int))
                self.edtODGODSMText.setText(self.getPropertyValue(items, u'ОД:ГО:ВИ:ШМ:3', unicode))
                isODGOSMO = self.getChkPropertyValue(items, u'ОД:ГО:ВИ:ШМ:4', [u'кзади',u'кпереди',u'расположена по центру'])
                self.chkODGOSMO1.setChecked(isODGOSMO == 1)
                self.chkODGOSMO2.setChecked(isODGOSMO == 2)
                self.chkODGOSMO3.setChecked(isODGOSMO == 3)
                self.edtODGOSL.setText(self.getPropertyValue(items, u'ОД:ГО:ВИ:ШМ:5', unicode))
                isODGOZV = self.getChkPropertyValue(items, u'ОД:ГО:ВИ:НЗ', [u'сомкнут',u'пропускает кончик пальца',u'пропускает палец'])
                self.chkODGOZV1.setChecked(isODGOZV == 1)
                self.chkODGOZV2.setChecked(isODGOZV == 2)
                self.chkODGOZV3.setChecked(isODGOZV == 3)
                isODGOTM = self.getChkPropertyValue(items, u'ОД:ГО:ВИ:ТМ:1', [u'безболезненное',u'болезненное'])
                self.chkODGOTM1.setChecked(isODGOTM == 1)
                self.chkODGOTM2.setChecked(isODGOTM == 2)
                isODGOTM2 = self.getChkPropertyValue(items, u'ОД:ГО:ВИ:ТМ:2', [u'подвижное', u'другое'])
                self.chkODGOTM3.setChecked(isODGOTM2 == 1)
                self.chkODGOTM4.setChecked(isODGOTM2 == 2)
                self.edtODGOTM4Text.setText(self.getPropertyValue(items, u'ОД:ГО:ВИ:ТМ:3', unicode))
                self.edtODGOTMU.setText(self.getPropertyValue(items, u'ОД:ГО:ВИ:ТМ:4', unicode))
                self.edtODGOOMP.setText(self.getPropertyValue(items, u'ОД:ГО:ВИ:ОП', unicode))
                isODGOPSL = self.getChkPropertyValue(items, u'ОД:ГО:ВИ:ПСл:1', [u'без особенностей',u'особенности'])
                self.chkODGOPSL1.setChecked(isODGOPSL == 1)
                self.chkODGOPSL2.setChecked(isODGOPSL == 2)
                self.edtODGOPSL2Text.setText(self.getPropertyValue(items, u'ОД:ГО:ВИ:ПСл:2', unicode))
                isODGOPSP = self.getChkPropertyValue(items, u'ОД:ГО:ВИ:ПСп:1', [u'без особенностей',u'особенности'])
                self.chkODGOPSP1.setChecked(isODGOPSP == 1)
                self.chkODGOPSP2.setChecked(isODGOPSP == 2)
                self.edtODGOPSP3Text.setText(self.getPropertyValue(items, u'ОД:ГО:ВИ:ПСп:2', unicode))
                isODGOE = self.getChkPropertyValue(items, u'ОД:ГО:ВИ:Э:1', [u'нет',u'обнаружены'])
                self.chkODGOE1.setChecked(isODGOE == 1)
                self.chkODGOE2.setChecked(isODGOE == 2)
                self.edtODGOE2Text.setText(self.getPropertyValue(items, u'ОД:ГО:ВИ:Э:2', unicode))
                self.edtODGOOZK.setText(self.getPropertyValue(items, u'ОД:ГО:ВИ:ОЦК', unicode))
                self.edtODGOOV.setText(self.getPropertyValue(items, u'ОД:ГО:ВИ:ОБ', unicode))
                self.edtODGOA.setText(self.getPropertyValue(items, u'ОД:ГО:ВИ:Ан', unicode))
                self.edtODGON.setText(self.getPropertyValue(items, u'ОД:ГО:ВИ:Наз', unicode))
                self.edtODGOPSSP.setValue(self.getPropertyValue(items, u'ОД:ГО:ВИ:РССП', int))
                if isCreate:
                    self.setProperty(QVariant(self.edtODGODZ.date()), u'ОД:ГО:ВИ:ДЗ')
                else:
                    self.edtODGODZ.setDate(self.getPropertyValue(items, u'ОД:ГО:ВИ:ДЗ', QDate))
                # #tabClientData
                isSOPWPR = self.getChkPropertyValue(items, u'СОП:ВПР:1', [u'нет', u'да'])
                self.chkSOPWPRNot.setChecked(isSOPWPR == 1)
                self.chkSOPWPRYes.setChecked(isSOPWPR == 2)
                self.edtSOPWPRText.setText(self.getPropertyValue(items, u'СОП:ВПР:2', unicode))
                self.edtSOPIMT.setValue(self.getPropertyValue(items, u'СОП:ИМТМ', int))
                self.edtSOPRost.setValue(self.getPropertyValue(items, u'СОП:РПЯ', int))
                self.edtSOPMT.setValue(self.getPropertyValue(items, u'СОП:МТПЯ', float))
                self.edtSOPDRS.setText(self.getPropertyValue(items, u'СОП:ДР:1', unicode))
                isSOPDRS = self.getChkPropertyValue(items, u'СОП:ДР:2', [u'низкий', u'высокий'])
                self.chkSOPDRS1.setChecked(isSOPDRS == 1)
                self.chkSOPDRS2.setChecked(isSOPDRS == 2)
                isSOPDB = self.getChkPropertyValue(items, u'СОП:ПЗ:ДИ:1', [u'нет', u'да'])
                self.chkSOPDB1.setChecked(isSOPDB == 1)
                self.chkSOPDB2.setChecked(isSOPDB == 2)
                self.edtSOPDBText.setText(self.getPropertyValue(items, u'СОП:ПЗ:ДИ:2', unicode))
                isSOPDS = self.getChkPropertyValue(items, u'СОП:ПЗ:НДУ:1', [u'не состояла', u'состояла'])
                self.chkSOPDS1.setChecked(isSOPDS == 1)
                self.chkSOPDS2.setChecked(isSOPDS == 2)
                self.edtSOPDSText.setText(self.getPropertyValue(items, u'СОП:ПЗ:НДУ:2', unicode))
                isSOPTRO = self.getChkPropertyValue(items, u'СОП:ПЗ:ТО:1', [u'нет', u'да'])
                self.chkSOPTRO1.setChecked(isSOPTRO == 1)
                self.chkSOPTRO2.setChecked(isSOPTRO == 2)
                self.edtSOPTROText.setText(self.getPropertyValue(items, u'СОП:ПЗ:ТО:2', unicode))
                isSOPSZ = self.getChkPropertyValue(items, u'СОП:ПЗ:СЗ:1', [u'нет', u'да'])
                self.chkSOPSZ1.setChecked(isSOPSZ == 1)
                self.chkSOPSZ2.setChecked(isSOPSZ == 2)
                self.edtSOPSZText.setText(self.getPropertyValue(items, u'СОП:ПЗ:СЗ:2', unicode))
                isSOPSZIList = self.getChkPropertyList(items, u'СОП:ПЗ:СЗИ:1', [u'нет',u'ВИЧ',u'Туберкулёз',u'Гепатит-В',u'Гепатит-С',u'Сифилис',u'другие'])
                for isSOPSZI in isSOPSZIList:
                    if isSOPSZI == 1:
                        self.chkSOPSZI1.setChecked(True)
                    elif isSOPSZI == 2:
                        self.chkSOPSZI2.setChecked(True)
                    elif isSOPSZI == 3:
                        self.chkSOPSZI3.setChecked(True)
                    elif isSOPSZI == 4:
                        self.chkSOPSZI4.setChecked(True)
                    elif isSOPSZI == 5:
                        self.chkSOPSZI5.setChecked(True)
                    elif isSOPSZI == 6:
                        self.chkSOPSZI6.setChecked(True)
                    elif isSOPSZI == 7:
                        self.chkSOPSZI7.setChecked(True)
                self.edtSOPSZIText.setText(self.getPropertyValue(items, u'СОП:ПЗ:СЗИ:2', unicode))
                isSOPVSTATUS = self.getChkPropertyValue(items, u'СОП:ПЗ:ВИЧ:1', [u'негативный',u'позитивный'])
                self.chkSOPVSTATUS1.setChecked(isSOPVSTATUS == 1)
                self.chkSOPVSTATUS2.setChecked(isSOPVSTATUS == 2)
                self.edtSOPVSTATUSDate.setDate(self.getPropertyValue(items, u'СОП:ПЗ:ВИЧ:2', QDate))
                self.edtSOPVSTATUSNumberText.setText(self.getPropertyValue(items, u'СОП:ПЗ:ВИЧ:3', unicode))
                self.edtSOPVSTATUSARVTText.setText(self.getPropertyValue(items, u'СОП:ПЗ:АТ', unicode))
                isSOPNZ = self.getChkPropertyValue(items, u'СОП:ПЗ:НЗ:1', [u'нет', u'да'])
                self.chkSOPNZ1.setChecked(isSOPNZ == 1)
                self.chkSOPNZ2.setChecked(isSOPNZ == 2)
                self.edtSOPNZText.setText(self.getPropertyValue(items, u'СОП:ПЗ:НЗ:2', unicode))
                isSOPGTR = self.getChkPropertyValue(items, u'СОП:ПЗ:Г:1', [u'нет', u'да'])
                self.chkSOPGTR1.setChecked(isSOPGTR == 1)
                self.chkSOPGTR2.setChecked(isSOPGTR == 2)
                self.edtSOPGTRDate.setText(self.getPropertyValue(items, u'СОП:ПЗ:Г:2', unicode))
                self.edtSOPGTRComponent.setText(self.getPropertyValue(items, u'СОП:ПЗ:Г:3', unicode))
                self.edtSOPPFDate.setDate(self.getPropertyValue(items, u'СОП:ПЗ:ПФ:1', QDate))
                self.edtSOPPFText.setText(self.getPropertyValue(items, u'СОП:ПЗ:ПФ:2', unicode))
                isSOPWPList = self.getChkPropertyList(items, u'СОП:ВП:1', [u'нет', u'курение', u'алкоголь', u'наркотики'])
                for isSOPWP in isSOPWPList:
                    if isSOPWP == 1:
                        self.chkSOPWP1.setChecked(True)
                    elif isSOPWP == 2:
                        self.chkSOPWP2.setChecked(True)
                    elif isSOPWP == 3:
                        self.chkSOPWP7.setChecked(True)
                    elif isSOPWP == 4:
                        self.chkSOPWP11.setChecked(True)
                isSOPWP2 = self.getChkPropertyValue(items, u'СОП:ВП:2', [u'-<1/2 пачки в день',u'1/2-1 пачка в день',u'>1 пачки в день'])
                self.chkSOPWP3.setChecked(isSOPWP2 == 1)
                self.chkSOPWP4.setChecked(isSOPWP2 == 2)
                self.chkSOPWP5.setChecked(isSOPWP2 == 3)
                self.edtSOPWPText.setText(self.getPropertyValue(items, u'СОП:ВП:3', unicode))
                isSOPWP3 = self.getChkPropertyValue(items, u'СОП:ВП:4', [u'каждый день',u'1-2 раза в неделю',u'1-2 раза в месяц'])
                self.chkSOPWP8.setChecked(isSOPWP3 == 1)
                self.chkSOPWP9.setChecked(isSOPWP3 == 2)
                self.chkSOPWP10.setChecked(isSOPWP3 == 3)
                self.edtSOPWPText11.setText(self.getPropertyValue(items, u'СОП:ВП:5', unicode))
                self.edtSOPWP.setValue(self.getPropertyValue(items, u'СОП:ВП:6', int))
                self.edtSOPWPText12.setText(self.getPropertyValue(items, u'СОП:ВП:7', unicode))
                isSOPPRW = self.getChkPropertyValue(items, u'СОП:ПВ:1', [u'нет', u'да'])
                self.chkSOPPRW1.setChecked(isSOPPRW == 1)
                self.chkSOPPRW2.setChecked(isSOPPRW == 2)
                self.edtSOPPRWText.setText(self.getPropertyValue(items, u'СОП:ПВ:2', unicode))
                isSOPSOPRList = self.getChkPropertyList(items, u'СОП:СОПр:1', [u'столбняк', u'дифтерия', u'корь', u'краснуха', u'ветряная оспа', u'грипп', u'ВПЧ', u'гепатит-В', u'другие'])
                for isSOPSOPR in isSOPSOPRList:
                    if isSOPSOPR == 1:
                        self.chkSOPSOPR1.setChecked(True)
                    elif isSOPSOPR == 2:
                        self.chkSOPSOPR2.setChecked(True)
                    elif isSOPSOPR == 3:
                        self.chkSOPSOPR3.setChecked(True)
                    elif isSOPSOPR == 4:
                        self.chkSOPSOPR4.setChecked(True)
                    elif isSOPSOPR == 5:
                        self.chkSOPSOPR5.setChecked(True)
                    elif isSOPSOPR == 6:
                        self.chkSOPSOPR6.setChecked(True)
                    elif isSOPSOPR == 7:
                        self.chkSOPSOPR7.setChecked(True)
                    elif isSOPSOPR == 8:
                        self.chkSOPSOPR8.setChecked(True)
                    elif isSOPSOPR == 9:
                        self.chkSOPSOPR9.setChecked(True)
                self.edtSOPSOPR1Date.setDate(self.getPropertyValue(items, u'СОП:СОПр:2', QDate))
                self.edtSOPSOPR2Date.setDate(self.getPropertyValue(items, u'СОП:СОПр:3', QDate))
                self.edtSOPSOPR3Date.setDate(self.getPropertyValue(items, u'СОП:СОПр:4', QDate))
                self.edtSOPSOPR4Date.setDate(self.getPropertyValue(items, u'СОП:СОПр:5', QDate))
                self.edtSOPSOPR5Date.setDate(self.getPropertyValue(items, u'СОП:СОПр:6', QDate))
                self.edtSOPSOPR6Date.setDate(self.getPropertyValue(items, u'СОП:СОПр:7', QDate))
                self.edtSOPSOPR7Date.setDate(self.getPropertyValue(items, u'СОП:СОПр:8', QDate))
                self.edtSOPSOPR8Date.setDate(self.getPropertyValue(items, u'СОП:СОПр:9', QDate))
                self.edtSOPSOPR9Date.setDate(self.getPropertyValue(items, u'СОП:СОПр:11', QDate))
                self.edtSOPSOPR9Text.setText(self.getPropertyValue(items, u'СОП:СОПр:10', unicode))
                self.edtSOPMN1.setValue(self.getPropertyValue(items, u'СОП:Менстр:1', int))
                isSOPMN = self.getChkPropertyValue(items, u'СОП:Менстр:2', [u'сразу;', u'нет'])
                self.chkSOPMN1.setChecked(isSOPMN == 1)
                self.chkSOPMN2.setChecked(isSOPMN == 2)
                self.edtSOPMNText.setText(self.getPropertyValue(items, u'СОП:Менстр:3', unicode))
                self.edtSOPMN2.setValue(self.getPropertyValue(items, u'СОП:Менстр:5', int))
                self.edtSOPMN3.setText(self.getPropertyValue(items, u'СОП:Менстр:6', unicode))
                isSOPMN2 = self.getChkPropertyValue(items, u'СОП:Менстр:7', [u'скудные',u'умеренные',u'обильные'])
                self.chkSOPMN3.setChecked(isSOPMN2 == 1)
                self.chkSOPMN4.setChecked(isSOPMN2 == 2)
                self.chkSOPMN5.setChecked(isSOPMN2 == 3)
                isSOPMN2 = self.getChkPropertyValue(items, u'СОП:Менстр:8', [u'болезненные',u'безболезненные'])
                self.chkSOPMN6.setChecked(isSOPMN2 == 1)
                self.chkSOPMN7.setChecked(isSOPMN2 == 2)
                isSOPMN2 = self.getChkPropertyValue(items, u'СОП:Менстр:9', [u'регулярные', u'нерегулярные'])
                self.chkSOPMN8.setChecked(isSOPMN2 == 1)
                self.chkSOPMN9.setChecked(isSOPMN2 == 2)
                self.edtSOPPL.setValue(self.getPropertyValue(items, u'СОП:ПЖ', int))
                self.edtSOPKRZPText.setText(self.getPropertyValue(items, u'СОП:Контрац', unicode))
                self.edtSOPGZOPText.setText(self.getPropertyValue(items, u'СОП:ГЗО', unicode))
                isSOPIPPP = self.getChkPropertyValue(items, u'СОП:ИППП:1', [u'нет', u'да'])
                self.chkSOPIPPP1.setChecked(isSOPIPPP == 1)
                self.chkSOPIPPP2.setChecked(isSOPIPPP == 2)
                self.edtSOPIPPPText.setText(self.getPropertyValue(items, u'СОП:ИППП:2', unicode))
                self.edtSOPPIMGDate.setText(self.getPropertyValue(items, u'СОП:ПИМЖ:1', unicode))
                self.edtSOPPIMGText1.setText(self.getPropertyValue(items, u'СОП:ПИМЖ:2', unicode))
                self.edtSOPPIMGText2.setText(self.getPropertyValue(items, u'СОП:ПИМЖ:3', unicode))
                self.edtSOPPZIMSMDate.setText(self.getPropertyValue(items, u'СОП:ПЦИМШМ:1', unicode))
                self.edtSOPPZIMSMText1.setText(self.getPropertyValue(items, u'СОП:ПЦИМШМ:2', unicode))
                self.edtSOPPZIMSMText2.setText(self.getPropertyValue(items, u'СОП:ПЦИМШМ:3', unicode))
                self.edtSOPSoORVZ.setValue(self.getPropertyValue(items, u'СОП:СОР:В', int))
                self.edtSOPSoORIMT.setValue(self.getPropertyValue(items, u'СОП:СОР:ИМТ', int))
                self.edtSOPSoORRost.setValue(self.getPropertyValue(items, u'СОП:СОР:Р', int))
                self.edtSOPSoORMT.setValue(self.getPropertyValue(items, u'СОП:СОР:МТ', float))
                isSOPOVPList = self.getChkPropertyList(items, u'СОП:СОР:ВП', [u'нет',u'курение',u'алкоголь',u'наркотики'])
                for isSOPOVP in isSOPOVPList:
                    if isSOPOVP == 1:
                        self.chkSOPOVP1.setChecked(True)
                    elif isSOPOVP == 2:
                        self.chkSOPOVP2.setChecked(True)
                    elif isSOPOVP == 3:
                        self.chkSOPOVP3.setChecked(True)
                    elif isSOPOVP == 4:
                        self.chkSOPOVP4.setChecked(True)
                isSOPOXZ = self.getChkPropertyValue(items, u'СОП:СОР:ХЗ:1', [u'нет', u'да'])
                self.chkSOPOXZ1.setChecked(isSOPOXZ == 1)
                self.chkSOPOXZ2.setChecked(isSOPOXZ == 2)
                self.edtSOPOXZText.setText(self.getPropertyValue(items, u'СОП:СОР:ХЗ:2', unicode))
                isSOPOIPPP = self.getChkPropertyValue(items, u'СОП:СОР:ИППП:1', [u'нет', u'да'])
                self.chkSOPOIPPP1.setChecked(isSOPOIPPP == 1)
                self.chkSOPOIPPP2.setChecked(isSOPOIPPP == 2)
                self.edtSOPOIPPPText.setText(self.getPropertyValue(items, u'СОП:СОР:ИППП:2', unicode))
                isSOPOSZIList = self.getChkPropertyList(items, u'СОП:СОР:СЗП:1', [u'нет',u'ВИЧ',u'Туберкулёз',u'Гепатит-В',u'Гепатит-С',u'Сифилис',u'другие'])
                for isSOPOSZI in isSOPOSZIList:
                    if isSOPOSZI == 1:
                        self.chkSOPOSZI1.setChecked(True)
                    elif isSOPOSZI == 2:
                        self.chkSOPOSZI2.setChecked(True)
                    elif isSOPOSZI == 3:
                        self.chkSOPOSZI3.setChecked(True)
                    elif isSOPOSZI == 4:
                        self.chkSOPOSZI4.setChecked(True)
                    elif isSOPOSZI == 5:
                        self.chkSOPOSZI5.setChecked(True)
                    elif isSOPOSZI == 6:
                        self.chkSOPOSZI6.setChecked(True)
                    elif isSOPOSZI == 7:
                        self.chkSOPOSZI7.setChecked(True)
                self.edtSOPOSZIText.setText(self.getPropertyValue(items, u'СОП:СОР:СЗП:2', unicode))
                self.edtSOPOPFDate.setDate(self.getPropertyValue(items, u'СОП:СОР:ПФ:1', QDate))
                self.edtSOPOPFText.setText(self.getPropertyValue(items, u'СОП:СОР:ПФ:2', unicode))
                isSOPOSvOPRList = self.getChkPropertyList(items, u'СОП:СОР:СОПр', [u'столбняк',u'дифтерия',u'корь',u'краснуха',u'грипп'])
                for isSOPOSvOPR in isSOPOSvOPRList:
                    if isSOPOSvOPR == 1:
                        self.chkSOPOSvOPR1.setChecked(True)
                    elif isSOPOSvOPR == 2:
                        self.chkSOPOSvOPR2.setChecked(True)
                    elif isSOPOSvOPR == 3:
                        self.chkSOPOSvOPR3.setChecked(True)
                    elif isSOPOSvOPR == 4:
                        self.chkSOPOSvOPR4.setChecked(True)
                    elif isSOPOSvOPR == 5:
                        self.chkSOPOSvOPR5.setChecked(True)
                # #tabSurveillancePregnancy
                isNVNBDG = self.getChkPropertyValue(items, u'НВНБ:ДГ:1', [u'не показана', u'показана'])
                self.chkNVNBDG1.setChecked(isNVNBDG == 1)
                self.chkNVNBDG2.setChecked(isNVNBDG == 2)
                self.edtNVNBDG2Text.setText(self.getPropertyValue(items, u'НВНБ:ДГ:2', unicode))
                isNVNBDGK = self.getChkPropertyValue(items, u'НВНБ:ДГ:3', [u'в отделение патологии беременности', u'в отделение акушерского ухода'])
                self.chkNVNBDGK1.setChecked(isNVNBDGK == 1)
                self.chkNVNBDGK2.setChecked(isNVNBDGK == 2)
                self.edtNVNBDGO.setText(self.getPropertyValue(items, u'НВНБ:ДГ:4', unicode))
                self.edtNVNBDZ.setDate(self.getPropertyValue(items, u'НВНБ:ДГ:5', QDate))
                self.edtPreHospitalizationTermWeeks.setValue(self.getPropertyValue(items, u'ОД:ОДП:ДГ:6', int))
                self.edtNVNBP1.setValue(self.getPropertyValue(items, u'НВНБ:Пелв:1', int))
                self.edtNVNBP2.setValue(self.getPropertyValue(items, u'НВНБ:Пелв:2', int))
                self.edtNVNBP3.setValue(self.getPropertyValue(items, u'НВНБ:Пелв:3', int))
                self.edtNVNBP4.setValue(self.getPropertyValue(items, u'НВНБ:Пелв:4', int))
                self.edtNVNBP5.setValue(self.getPropertyValue(items, u'НВНБ:Пелв:5', int))
                self.edtNVNBP6.setValue(self.getPropertyValue(items, u'НВНБ:Пелв:6', int))
                self.edtNVNBP7.setValue(self.getPropertyValue(items, u'НВНБ:Пелв:7', int))
                self.edtNVNBP8.setValue(self.getPropertyValue(items, u'НВНБ:Пелв:8', int))
                self.edtNVNBP9.setValue(self.getPropertyValue(items, u'НВНБ:Пелв:9', int))
                self.edtNVNBPText.setText(self.getPropertyValue(items, u'НВНБ:Пелв:10', unicode))
                self.edtNVNBP.setDate(self.getPropertyValue(items, u'НВНБ:Пелв:11', QDate))
                self.chkNVNBPTNPkVB12.setChecked(self.getPropertyValue(items, u'НВНБ:НПкВБ:12', QCheckBox))
                self.chkNVNBPTNPkVB20.setChecked(self.getPropertyValue(items, u'НВНБ:НПкВБ:20', QCheckBox))
                isNVNBPNVNBPSR = self.getChkPropertyValue(items, u'НВНБ:ПСР', [u'вагинальные роды', u'кесарево сечение'])
                self.chkNVNBPNVNBPSR1.setChecked(isNVNBPNVNBPSR == 1)
                self.chkNVNBPNVNBPSR2.setChecked(isNVNBPNVNBPSR == 2)
                self.cmbNVNBPNVNBUAS.setCurrentIndex(self.cmbNVNBPNVNBUAS.findText(self.getPropertyValue(items, u'НВНБ:УАС', QComboBox) ))
                self.cmbNVNBPNVNBMOdR.setValue(self.getPropertyValue(items, u'НВНБ:МОдР', forceRef))
                isNVNBPNVNBPrR = self.getChkPropertyValue(items, u'НВНБ:ПрР', [u'плановый', u'экстренный'])
                self.chkNVNBPNVNBPrR1.setChecked(isNVNBPNVNBPrR == 1)
                self.chkNVNBPNVNBPrR2.setChecked(isNVNBPNVNBPrR == 2)
                self.chkNVNBPNVNBSUG.setChecked(self.getPropertyValue(items, u'НВНБ:СУЖ', QCheckBox))
                self.chkNVNBPNVNBOoG.setChecked(self.getPropertyValue(items, u'НВНБ:ОоГ', QCheckBox))
                self.chkNVNBPNVNBNPkT.setChecked(self.getPropertyValue(items, u'НВНБ:НПкТ', QCheckBox))
                self.cmbNVNBPUDRP.setValue(self.getPropertyValue(items, u'НВНБ:УД:РП:s', int))
                self.cmbNVNBPUDSM.setValue(self.getPropertyValue(items, u'НВНБ:УД:СМ:s', int))
                self.cmbNVNBPUDSST.setValue(self.getPropertyValue(items, u'НВНБ:УД:ССТ:s', int))
                self.cmbNVNBPUDFTB.setValue(self.getPropertyValue(items, u'НВНБ:УД:ФТБ:s', int))
                self.cmbNVNBPUDKOV.setValue(self.getPropertyValue(items, u'НВНБ:УД:КОВ:s', int))
                self.cmbNVNBPUDCA.setValue(self.getPropertyValue(items, u'НВНБ:УД:СА:s', int))
                self.cmbNVNBIBRM.setValue(self.getPropertyValue(items, u'НВНБ:ИБРМ:1:s', int))
                isNVNBIBRM2 = self.getChkPropertyValue(items, u'НВНБ:ИБРМ:2', [u'Роды: самопроизвольные', u'оперативные'])
                self.chkNVNBIBRM2.setChecked(isNVNBIBRM2 == 1)
                self.chkNVNBIBRM6.setChecked(isNVNBIBRM2 == 2)
                isNVNBIBRM2 = self.getChkPropertyValue(items, u'НВНБ:ИБРМ:3', [u'без осложнений', u'с осложнениями'])
                self.chkNVNBIBRM3.setChecked(isNVNBIBRM2 == 1)
                self.chkNVNBIBRM4.setChecked(isNVNBIBRM2 == 2)
                self.edtNVNBIBRM4.setText(self.getPropertyValue(items, u'НВНБ:ИБРМ:5', unicode))
                isNVNBIBRM4 = self.getChkPropertyValue(items, u'НВНБ:ИБРМ:8', [u'кесарево сечение', u'другое'])
                self.chkNVNBIBRM7.setChecked(isNVNBIBRM4 == 1)
                self.chkNVNBIBRM8.setChecked(isNVNBIBRM4 == 2)
                self.edtNVNBIBRM7.setText(self.getPropertyValue(items, u'НВНБ:ИБРМ:9', unicode))
                self.edtNVNBIBRM13Date.setDate(self.getPropertyValue(items, u'НВНБ:ИБРМ:15', QDate))
                self.edtNVNBIBRMResultDate.setDate(self.getPropertyValue(items, u'НВНБ:ИБРМ:17', QDate))
                self.edtNVNBIBRMResultDateWeeks.setValue(self.getPropertyValue(items, u'НВНБ:ИБРМ:1:1', int))
                self.edtNVNBIBRMResultDateDays.setValue(self.getPropertyValue(items, u'НВНБ:ИБРМ:1:2', int))
                self.edtNVNBIBRM3.setText(self.getPropertyValue(items, u'НВНБ:ИБРМ:1:3', unicode))
                self.edtNVNBIBRM13Time.setTime(self.getPropertyValue(items, u'НВНБ:ИБРМ:15', QTime))
                self.edtNVNBIBRM13MKB.setText(self.getPropertyValue(items, u'НВНБ:ИБРМ:16', unicode))
                self.chkNVNBIBRM13.setChecked(self.getPropertyValue(items, u'НВНБ:ИБРМ:15:1', QCheckBox))
                self.edtNVNBIBRP1.setValue(self.getPropertyValue(items, u'НВНБ:ИБРП:КД', int))
                # Первый ребёнок
                self.cmbNVNBIBRP1.setValue(self.getPropertyValue(items, u'НВНБ:ИБРП:1:1:1', int))
                isNVNBIBRPPRP = self.getChkPropertyValue(items, u'НВНБ:ИБРП:1:3', [u'Ж', u'М'])
                self.chkNVNBIBRPPRP1.setChecked(isNVNBIBRPPRP == 1)
                self.chkNVNBIBRPPRP2.setChecked(isNVNBIBRPPRP == 2)
                self.edtNVNBIBRPPRP.setValue(self.getPropertyValue(items, u'НВНБ:ИБРП:1:4', float))
                self.edtNVNBIBRPPRPD.setValue(self.getPropertyValue(items, u'НВНБ:ИБРП:1:5', int))
                isNVNBIBRPD = self.getChkPropertyValue(items, u'НВНБ:ИБРП:1:7', [u'доношенный', u'недоношенный', u'переношенный'])
                self.chkNVNBIBRPD1.setChecked(isNVNBIBRPD == 1)
                self.chkNVNBIBRPD2.setChecked(isNVNBIBRPD == 2)
                self.chkNVNBIBRPD3.setChecked(isNVNBIBRPD == 3)
                self.edtNVNBIBRPZMKB1.setText(self.getPropertyValue(items, u'НВНБ:ИБРП:1:8', unicode))
                self.edtNVNBIBRPZMKB2.setText(self.getPropertyValue(items, u'НВНБ:ИБРП:1:9', unicode))
                self.edtNVNBIBRPUV.setText(self.getPropertyValue(items, u'НВНБ:ИБРП:1:10', unicode))
                self.edtNVNBIBRPO1_1.setValue(self.getPropertyValue(items, u'НВНБ:ИБРП:1:6:1', int))
                self.edtNVNBIBRPO5_1.setValue(self.getPropertyValue(items, u'НВНБ:ИБРП:1:6:2', int))
                # Второй ребёнок
                self.cmbNVNBIBRP2.setValue(self.getPropertyValue(items, u'НВНБ:ИБРП:2:1:1', int))
                isNVNBIBRPPRP = self.getChkPropertyValue(items, u'НВНБ:ИБРП:2:3', [u'Ж', u'М'])
                self.chkNVNBIBRPPRP1_2.setChecked(isNVNBIBRPPRP == 1)
                self.chkNVNBIBRPPRP2_2.setChecked(isNVNBIBRPPRP == 2)
                self.edtNVNBIBRPPRP_2.setValue(self.getPropertyValue(items, u'НВНБ:ИБРП:2:4', float))
                self.edtNVNBIBRPPRPD_2.setValue(self.getPropertyValue(items, u'НВНБ:ИБРП:2:5', int))
                isNVNBIBRPD = self.getChkPropertyValue(items, u'НВНБ:ИБРП:2:7', [u'доношенный', u'недоношенный', u'переношенный'])
                self.chkNVNBIBRPD1_2.setChecked(isNVNBIBRPD == 1)
                self.chkNVNBIBRPD2_2.setChecked(isNVNBIBRPD == 2)
                self.chkNVNBIBRPD3_2.setChecked(isNVNBIBRPD == 3)
                self.edtNVNBIBRPZMKB1_2.setText(self.getPropertyValue(items, u'НВНБ:ИБРП:2:8', unicode))
                self.edtNVNBIBRPZMKB2_2.setText(self.getPropertyValue(items, u'НВНБ:ИБРП:2:9', unicode))
                self.edtNVNBIBRPUV_2.setText(self.getPropertyValue(items, u'НВНБ:ИБРП:2:10', unicode))
                self.edtNVNBIBRPO1_2.setValue(self.getPropertyValue(items, u'НВНБ:ИБРП:2:6:1', int))
                self.edtNVNBIBRPO5_2.setValue(self.getPropertyValue(items, u'НВНБ:ИБРП:2:6:2', int))
                # Третий ребёнок
                self.cmbNVNBIBRP3.setValue(self.getPropertyValue(items, u'НВНБ:ИБРП:3:1:1', int))
                isNVNBIBRPPRP = self.getChkPropertyValue(items, u'НВНБ:ИБРП:3:3', [u'Ж', u'М'])
                self.chkNVNBIBRPPRP1_3.setChecked(isNVNBIBRPPRP == 1)
                self.chkNVNBIBRPPRP2_3.setChecked(isNVNBIBRPPRP == 2)
                self.edtNVNBIBRPPRP_3.setValue(self.getPropertyValue(items, u'НВНБ:ИБРП:3:4', float))
                self.edtNVNBIBRPPRPD_3.setValue(self.getPropertyValue(items, u'НВНБ:ИБРП:3:5', int))
                isNVNBIBRPD = self.getChkPropertyValue(items, u'НВНБ:ИБРП:3:7', [u'доношенный', u'недоношенный', u'переношенный'])
                self.chkNVNBIBRPD1_3.setChecked(isNVNBIBRPD == 1)
                self.chkNVNBIBRPD2_3.setChecked(isNVNBIBRPD == 2)
                self.chkNVNBIBRPD3_3.setChecked(isNVNBIBRPD == 3)
                self.edtNVNBIBRPZMKB1_3.setText(self.getPropertyValue(items, u'НВНБ:ИБРП:3:8', unicode))
                self.edtNVNBIBRPZMKB2_3.setText(self.getPropertyValue(items, u'НВНБ:ИБРП:3:9', unicode))
                self.edtNVNBIBRPUV_3.setText(self.getPropertyValue(items, u'НВНБ:ИБРП:3:10', unicode))
                self.edtNVNBIBRPO1_3.setValue(self.getPropertyValue(items, u'НВНБ:ИБРП:3:6:1', int))
                self.edtNVNBIBRPO5_3.setValue(self.getPropertyValue(items, u'НВНБ:ИБРП:3:6:2', int))
                # Четвёртый ребёнок
                self.cmbNVNBIBRP4.setValue(self.getPropertyValue(items, u'НВНБ:ИБРП:4:1:1', int))
                isNVNBIBRPPRP = self.getChkPropertyValue(items, u'НВНБ:ИБРП:4:3', [u'Ж', u'М'])
                self.chkNVNBIBRPPRP1_4.setChecked(isNVNBIBRPPRP == 1)
                self.chkNVNBIBRPPRP2_4.setChecked(isNVNBIBRPPRP == 2)
                self.edtNVNBIBRPPRP_4.setValue(self.getPropertyValue(items, u'НВНБ:ИБРП:4:4', float))
                self.edtNVNBIBRPPRPD_4.setValue(self.getPropertyValue(items, u'НВНБ:ИБРП:4:5', int))
                isNVNBIBRPD = self.getChkPropertyValue(items, u'НВНБ:ИБРП:4:7', [u'доношенный', u'недоношенный', u'переношенный'])
                self.chkNVNBIBRPD1_4.setChecked(isNVNBIBRPD == 1)
                self.chkNVNBIBRPD2_4.setChecked(isNVNBIBRPD == 2)
                self.chkNVNBIBRPD3_4.setChecked(isNVNBIBRPD == 3)
                self.edtNVNBIBRPZMKB1_4.setText(self.getPropertyValue(items, u'НВНБ:ИБРП:4:8', unicode))
                self.edtNVNBIBRPZMKB2_4.setText(self.getPropertyValue(items, u'НВНБ:ИБРП:4:9', unicode))
                self.edtNVNBIBRPUV_4.setText(self.getPropertyValue(items, u'НВНБ:ИБРП:4:10', unicode))
                self.edtNVNBIBRPO1_4.setValue(self.getPropertyValue(items, u'НВНБ:ИБРП:4:6:1', int))
                self.edtNVNBIBRPO5_4.setValue(self.getPropertyValue(items, u'НВНБ:ИБРП:4:6:2', int))
                # Пятый ребёнок
                self.cmbNVNBIBRP5.setValue(self.getPropertyValue(items, u'НВНБ:ИБРП:5:1:1', int))
                isNVNBIBRPPRP = self.getChkPropertyValue(items, u'НВНБ:ИБРП:5:3', [u'Ж', u'М'])
                self.chkNVNBIBRPPRP1_5.setChecked(isNVNBIBRPPRP == 1)
                self.chkNVNBIBRPPRP2_5.setChecked(isNVNBIBRPPRP == 2)
                self.edtNVNBIBRPPRP_5.setValue(self.getPropertyValue(items, u'НВНБ:ИБРП:5:4', float))
                self.edtNVNBIBRPPRPD_5.setValue(self.getPropertyValue(items, u'НВНБ:ИБРП:5:5', int))
                isNVNBIBRPD = self.getChkPropertyValue(items, u'НВНБ:ИБРП:5:7', [u'доношенный', u'недоношенный', u'переношенный'])
                self.chkNVNBIBRPD1_5.setChecked(isNVNBIBRPD == 1)
                self.chkNVNBIBRPD2_5.setChecked(isNVNBIBRPD == 2)
                self.chkNVNBIBRPD3_5.setChecked(isNVNBIBRPD == 3)
                self.edtNVNBIBRPZMKB1_5.setText(self.getPropertyValue(items, u'НВНБ:ИБРП:5:8', unicode))
                self.edtNVNBIBRPZMKB2_5.setText(self.getPropertyValue(items, u'НВНБ:ИБРП:5:9', unicode))
                self.edtNVNBIBRPUV_5.setText(self.getPropertyValue(items, u'НВНБ:ИБРП:5:10', unicode))
                self.edtNVNBIBRPO1_5.setValue(self.getPropertyValue(items, u'НВНБ:ИБРП:5:6:1', int))
                self.edtNVNBIBRPO5_5.setValue(self.getPropertyValue(items, u'НВНБ:ИБРП:5:6:2', int))
                #
                self.edtNVNBIBRPOPS.setText(self.getPropertyValue(items, u'НВНБ:ИБРП:ОПС', unicode))
                self.edtClinicalDiagnosisMain.setText(self.getPropertyValue(items, u'ОД:КФД:1', unicode))
                self.edtClinicalDiagnosisAccomp.setText(self.getPropertyValue(items, u'ОД:КФД:2', unicode))
                self.edtClinicalDiagnosisComplications.setText(self.getPropertyValue(items, u'ОД:КФД:3', unicode))
                self.edtDiagnosis.setText(self.getPropertyValue(items, u'ОД:Д', unicode))
                isSkinStatus = self.getChkPropertyValue(items, u'ОД:СКП:1', [u'чистые',u'высыпания'])
                self.chkSkinStatus1.setChecked(isSkinStatus == 1)
                self.chkSkinStatus2.setChecked(isSkinStatus == 2)
                self.edtSkinStatus.setText(self.getPropertyValue(items, u'ОД:СКП:2', unicode))
                
                self.edtCloseReason.setText(self.getPropertyValue(items, u'НВНБ:ПЗ', unicode))
                date = self.edtNVNBDZKDate.date()
                if date and date.isValid():
                    self.lblCloseReason.setVisible(True)
                    self.edtCloseReason.setVisible(True)
                else:
                    self.lblCloseReason.setVisible(False)
                    self.edtCloseReason.setVisible(False)
            else:
                if isCreate:
                    self.setProperty(QVariant(self.edtFirstAppearanceTermDate.date()), u'ОД:ОДП:ДПЯ')
                    self.setProperty(QVariant(self.edtODPOBDO.date()), u'ОД:ПОБ:ДО')
                    self.setProperty(QVariant(self.edtODGODZ.date()), u'ОД:ГО:ВИ:ДЗ')

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
        item = items.get(shortName, [])
        if widgetType == unicode:
            return u','.join(val if (val and (isinstance(val, basestring) or val.__class__.__name__ == 'QString')) else str(val) for val in item if val)
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
            if valueProperty and (isinstance(valueProperty, basestring) or valueProperty.__class__.__name__ == 'QString'):
                if valueProperty == u'Да' or valueProperty == u'да' or valueProperty in [u'true', u'True']:
                    return True
            elif type(valueProperty) is int and valueProperty > 0:
                return True
            elif type(valueProperty) is bool:
                return valueProperty
            return False
        if widgetType == u'year':
            if valueProperty and (isinstance(valueProperty, basestring) or valueProperty.__class__.__name__ == 'QString'):
                return QDate().fromString(valueProperty,'dd.MM.yyyy')
            else:
                return forceDate(valueProperty)
        if widgetType == int:
            if valueProperty and (isinstance(valueProperty, basestring) or valueProperty.__class__.__name__ == 'QString'):
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
            if valueProperty and (isinstance(valueProperty, basestring) or valueProperty.__class__.__name__ == 'QString'):
                return QDate().fromString(valueProperty,'dd.MM.yyyy')
            else:
                return forceDate(valueProperty)
        if widgetType == QDateTime:
            if valueProperty and (isinstance(valueProperty, basestring) or valueProperty.__class__.__name__ == 'QString'):
                return QDateTime().fromString(valueProperty,'dd.MM.yyyy hh:mm')
            else:
                return forceDateTime(valueProperty)
        if widgetType == QTime:
            if valueProperty and (isinstance(valueProperty, basestring) or valueProperty.__class__.__name__ == 'QString'):
                return QTime().fromString(valueProperty,'hh:mm')
            else:
                return forceTime(valueProperty)
        if widgetType == float:
            return forceDouble(QVariant(valueProperty))


    def setProperty(self, value, propertyShortName):
        if self.action:
            for propertyTypeName, propertyType in self.action.getType()._propertiesByName.items():
                if trim(propertyShortName) == trim(propertyType.shortName):
                    if propertyTypeName and propertyTypeName in self.action._actionType._propertiesByName:
                        value = propertyType.convertQVariantToPyValue(value)
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
            eventRecord.setValue('execDate', QVariant(self.edtNVNBDZKDate.date()))
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
            self.recordEvent.setValue('execDate', QVariant(self.edtNVNBDZKDate.date()))
        result = type(record)(record) # copy record
        result.remove(result.indexOf('payStatus'))
        self.modelPreviousPregnancy.saveItems(self.action.getId())
        self.modelSOPSvORNM.saveItems()
        self.modelNVNBVARRS.saveItems()
        self.modelNVNBAR.saveItems()
        self.modelNVNBSGVB.saveItems()
        self.modelPregnancyInfoAdd.saveItems(self.eventId)
        self.modelPregnancyInfoAdd.clearItems()
        self.modelPregnancyInfoAddChildren.clearItems()
        self.tabNotes.getNotes(self.recordEvent, self.eventTypeId)
        return result


    def getEventRecord(self):
        return self.recordEvent


    def setEventRecord(self, recordEvent):
        self.recordEvent = recordEvent


    def saveData(self):
        self.syncData()
        return self.checkDataEntered() and self.save()


    def save(self):
        try:
            prevId = self.itemId()
            db = QtGui.qApp.db
            db.transaction()
            try:
                id = self.saveAction()
                db.commit()
            except:
                db.rollback()
                self.setItemId(prevId)
                QtGui.QMessageBox.critical( self,
                                            u'Внимание!',
                                            u'Информация не была сохранена.',
                                            QtGui.QMessageBox.Ok)
                raise
            self.setItemId(id)
            self.afterSave()
            return id
        except Exception as e:
            if self._isAssertNoMessage:
                return None
            QtGui.qApp.logCurrentException()
            QtGui.QMessageBox.critical( self,
                                        u'',
                                        exceptionToUnicode(e),
                                        QtGui.QMessageBox.Close)
            return None


    def saveAction(self):
        newActionId = None
        self.action._record = self.getRecord()
        self.setTextEdits()
        eventRecordMSI = self.getEventRecord()
        idxMSI = self.idx
        if self.action:
            db = QtGui.qApp.db
            tableEvent = db.table('Event')
            tableEventType = db.table('EventType')
            recordAction = self.action.getRecord()
            eventRecordMSIId = forceRef(eventRecordMSI.value('id')) if eventRecordMSI else None
            eventId = forceRef(recordAction.value('event_id')) if recordAction else (eventRecordMSIId if eventRecordMSIId else None)
            if not eventId:
                tableEventType = db.table('EventType')
                queryTable = tableEvent.innerJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
                cond = [tableEventType['code'].like(u'KBiR%'),
                        tableEvent['execDate'].isNull(),
                        tableEvent['client_id'].eq(self.clientId),
                        tableEvent['deleted'].eq(0),
                        tableEventType['deleted'].eq(0),
                        ]
                recordEvent = db.getRecordEx(queryTable, 'Event.*', cond, u'Event.id DESC')
                eventId = forceRef(recordEvent.value('id')) if recordEvent else None
                if eventId != eventRecordMSIId:
                    for i in xrange(recordEvent.count()):
                        fieldName = recordEvent.fieldName(i)
                        if fieldName in tabNotesFieldNames:
                            recordEvent.setValue(i, eventRecordMSI.value(fieldName))
                    eventRecordMSI = recordEvent
            if eventId and eventRecordMSI:
                newActionId = self.saveMedicalCommissionAction(self.action, eventRecordMSI, eventId, idx = idxMSI)
            else:
                eventTypeId = forceRef(eventRecordMSI.value('eventType_id')) if eventRecordMSI else None
                if not eventTypeId:
                    recordEventType = db.getRecordEx(tableEventType, [tableEventType['id']], [tableEventType['code'].like(u'KBiR%'), tableEventType['deleted'].eq(0)], u'EventType.id')
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
                        newActionId = self.saveMedicalCommissionAction(self.action, recordEvent, eventId, idx = idxMSI)
        return newActionId


    def saveMedicalCommissionAction(self, action, recordEvent = None, eventId = None, idx = 0):
        id = None
        try:
            try:
                db = QtGui.qApp.db
                db.transaction()
                id = self.action.save(eventId, idx = idx, checkModifyDate = False)
                if id:
                    self.action.getRecord().setValue('id', toVariant(id))
                    self.action.getRecord().setValue('event_id', toVariant(eventId))
                    checkTissueJournalStatusByActions([(self.action.getRecord(), self.action)])
                    if self.action.getType().closeEvent and recordEvent:
                        eventExecDate = forceDate(recordEvent.value('execDate'))
                        actionEndDate = forceDateTime(self.action.getRecord().value('endDate'))
                        if not eventExecDate and actionEndDate:
                            recordEvent.setValue('execDate', QVariant(actionEndDate))
                            recordEvent.setValue('isClosed', QVariant(1))
                    self.eventId = eventId
                if recordEvent and self.isDirty():
                    recordEvent.setIsDirty(True)
                    db.updateRecord('Event', recordEvent)
                db.commit()
            except:
                db.rollback()
                raise
        except Exception as e:
            QtGui.qApp.logCurrentException()
            QtGui.QMessageBox.critical( self,
                                        u'',
                                        exceptionToUnicode(e),
                                        QtGui.QMessageBox.Close)
        return id


    def saveInternals(self, id):
        if self.checkDataEntered(secondTry=True):
            self.setTextEdits()
            id = self.action.save(self.eventId, self.idx, checkModifyDate=False)
            checkTissueJournalStatusByActions([(self.action.getRecord(), self.action)])
            eventRecord = self._getEventRecord()
            if self.action.getType().closeEvent:
                if eventRecord:
                    eventExecDate = forceDate(eventRecord.value('execDate'))
                    if not eventExecDate and self._eventExecDate:
                        eventRecord.setValue('execDate', QVariant(self._eventExecDate))
                        eventRecord.setValue('isClosed', QVariant(1))
            db = QtGui.qApp.db
            if eventRecord and self.isDirty():
                eventRecord.setIsDirty(True)
                db.updateRecord('Event', eventRecord)
                self.recordEvent = None
                eventRecord = self._getEventRecord()
            self.tabNotes.saveAttachedFiles(self.eventId)
        return id


    def updateClientInfo(self):
        db = QtGui.qApp.db
        self.clientInfo = getClientInfo(self.clientId, date=self.edtDirectionDate.date())
        self.txtClientInfoBrowser.setHtml(getClientBanner(self.clientId, self.edtDirectionDate.date()))
        table = db.table('Client')
        record = db.getRecord(table, '*', self.clientId)
        if record:
            directionDate = self.edtDirectionDate.date()
            self.clientSex = forceInt(record.value('sex'))
            self.clientBirthDate = forceDate(record.value('birthDate'))
            self.clientAge = calcAgeTuple(self.clientBirthDate, directionDate)
        self.actShowAttachedToClientFiles.setMasterId(self.clientId)
        self.tabAmbCard.setClientId(self.clientId, self.clientSex, self.clientAge)
        self.tabAmbCard.resetWidgets()
        self.clientDeathDate = getDeathDate(self.clientId)


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
        from Events.EventEditDialog import CEventEditDialog
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
        if begDate and endDate:
            if showTime:
                result = result and (endDate >= begDate or self.checkValueMessage(u'Дата выполнения действия %s не должна быть раньше даты начала действия % s'%(forceString(endDate), forceString(begDate)), False, self.edtEndTime))
            else:
                result = result and (endDate >= begDate or self.checkValueMessage(u'Дата выполнения действия %s не должна быть раньше даты начала действия % s'%(forceString(endDate), forceString(begDate)), False, self.edtEndDate))
        if result and self.eventId:
            record = self.recordEvent
            if not record:
                record = self._getEventRecord()
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
        result = result and self.checkPlannedEndDate()
        result = result and self.checkTabNotesEventExternalId()
        result = result and self.checkProperties()
        if not self.personId:
            result = result and self.checkValueMessage(u'"Внимание! Необходимо указать врача, наблюдающего данную беременность!', False, self.cmbPerson)

        return result
    
    
    def checkProperties(self):
        eventRecord = self._getEventRecord()
        if eventRecord and forceRef(eventRecord.value('id')):
            checkDate = forceDate(eventRecord.value('createDateTime'))
            checkDateText = u'даты создания записи'
        else:
            checkDate = QDate.currentDate()
            checkDateText = u'текущей даты'
        lastMenstruationDate = self.edtLastMenstruationDate.date()
        if not lastMenstruationDate.isValid():
            return self.checkInputMessage(u'Дату последней менструации', False, self.edtLastMenstruationDate)
        elif abs(checkDate.daysTo(lastMenstruationDate)) > 294:
            return self.checkValueMessage(u'Дата последней менструации не может быть меньше/больше 294 дней от {}'.format(checkDateText), False, self.edtLastMenstruationDate)
            
        
        appointDate = self.edtAppointDate.date()
        if not appointDate.isValid():
            return self.checkInputMessage(u'Дату постановки на учёт по беременности', False, self.edtAppointDate)
        elif abs(checkDate.daysTo(appointDate)) > 294:
            return self.checkValueMessage(u'Дата постановки на учёт по беременности не может быть меньше/больше 294 дней от {}'.format(checkDateText), False, self.edtLastMenstruationDate)
        
        appointTermWeeks = self.edtAppointTermWeeks.value()
        if appointTermWeeks <= 0:
            return self.checkInputMessage(u'Срок при постановке на учёт (недель) по беременности', False, self.edtAppointTermWeeks)
        
        estimadtedBirthsDate = self.edtEstimatedBirthsDate.date()
        if not estimadtedBirthsDate.isValid():
            return self.checkInputMessage(u'Предполагаемая дата родов', False, self.edtEstimatedBirthsDate)
        elif abs(checkDate.daysTo(estimadtedBirthsDate)) > 294:
            return self.checkValueMessage(u'Предполагаемая дата родов не может быть меньше/больше 294 дней от {}'.format(checkDateText), False, self.edtEstimatedBirthsDate)
        return True
            
    
    def syncData(self):
        record = self.record()
        actionShowTime = self.action._actionType.showTime
        begDate = self.edtBegDate.date()
        self.edtDirectionDate.setDate(begDate)
        if actionShowTime:
            begTime = self.edtBegTime.time()
            self.edtDirectionTime.setTime(begTime)
        getDatetimeEditValue(self.edtDirectionDate, self.edtDirectionTime, record, 'directionDate', actionShowTime)
        begDate = QDateTime(self.edtDirectionDate.date(), self.edtDirectionTime.time()) if actionShowTime else self.edtDirectionDate.date()
        self.recordEvent.setValue('setDate', toVariant(begDate))
        
        endDate = self.edtNVNBDZKDate.date()
        self.edtEndDate.setDate(endDate)
        getDatetimeEditValue(self.edtEndDate, self.edtEndTime, record, 'endDate', actionShowTime)
        self.recordEvent.setValue('execDate', toVariant(endDate))
        
        self.recordEvent.setValue('execPerson_id', toVariant(self.personId))
    
    
    def _date2StringToCompare(self, date):
        if isinstance(date, QDate):
            return unicode(date.toString('yyyy.MM.dd'))
        if isinstance(date, QDateTime):
            return unicode(date.toString('yyyy.MM.dd HH:mm'))


    def checkTabNotesEventExternalId(self):
        if self.tabNotes:
            setDate = self.eventSetDateTime.date() if self.eventSetDateTime else None
            sameExternalIdListInfo = self.tabNotes.checkEventExternalId(setDate, self.itemId())
            if bool(sameExternalIdListInfo):
                sameExternalIdListText = '\n'.join(sameExternalIdListInfo)
                message = u'Подобный внешний идентификатор уже существует в других событиях:\n%s\n\n%s'%(
                                                                                    sameExternalIdListText, u'Исправить?')
                return self.checkValueMessage(message, True, self.tabNotes.edtEventExternalIdValue)
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
            self.personSpecialityId = forceRef(record.value('speciality_id'))
            self.personTariffCategoryId = forceRef(record.value('tariffCategory_id'))
            self.personSNILS = forceStringEx(record.value('SNILS'))
            self.showTypeTemplate = forceInt(record.value('showTypeTemplate'))
            self.actionTemplateCache.setPersonSNILS(self.personSNILS)
            self.actionTemplateCache.setShowTypeTemplate(self.showTypeTemplate)


    def getEventInfo(self, context):
        return None


    def clearODPOBRPPGRF(self):
        self.chkODPOBRPPGRF1_1.setChecked(False)
        self.chkODPOBRPPGRF2_1.setChecked(False)
        self.chkODPOBRPPGRF1_2.setChecked(False)
        self.chkODPOBRPPGRF2_2.setChecked(False)
        self.chkODPOBRPPGRF1_3.setChecked(False)
        self.chkODPOBRPPGRF2_3.setChecked(False)
        self.chkODPOBRPPGRF1_4.setChecked(False)
        self.chkODPOBRPPGRF2_4.setChecked(False)
        self.chkODPOBRPPGRF1_5.setChecked(False)
        self.chkODPOBRPPGRF2_5.setChecked(False)


    @pyqtSlot(bool)
    def on_chkNVNBIBRM2_toggled(self, checked):
        isChecked = self.chkNVNBIBRM2.isChecked()
        if isChecked:
            self.chkNVNBIBRM6.setChecked(False)
            self.setProperty(QVariant(self.chkNVNBIBRM2.text()), u'НВНБ:ИБРМ:2')
        else:
            if not self.chkNVNBIBRM6.isChecked():
                self.setProperty(QVariant(), u'НВНБ:ИБРМ:2')
            self.chkNVNBIBRM4.setChecked(False)


    @pyqtSlot(bool)
    def on_chkNVNBIBRM6_toggled(self, checked):
        isChecked = self.chkNVNBIBRM6.isChecked()
        if isChecked:
            self.chkNVNBIBRM2.setChecked(False)
            self.setProperty(QVariant(self.chkNVNBIBRM6.text()), u'НВНБ:ИБРМ:2')
        else:
            if not self.chkNVNBIBRM2.isChecked():
                self.setProperty(QVariant(), u'НВНБ:ИБРМ:2')
            self.chkNVNBIBRM7.setChecked(False)
            self.chkNVNBIBRM8.setChecked(False)


    @pyqtSlot(bool)
    def on_chkNVNBIBRM7_toggled(self, checked):
        isChecked = self.chkNVNBIBRM7.isChecked()
        if isChecked:
            self.chkNVNBIBRM8.setChecked(False)
            self.setProperty(QVariant(self.chkNVNBIBRM7.text()), u'НВНБ:ИБРМ:8')
        else:
            if not self.chkNVNBIBRM8.isChecked():
                self.setProperty(QVariant(), u'НВНБ:ИБРМ:8')


    @pyqtSlot(bool)
    def on_chkNVNBIBRM8_toggled(self, checked):
        isChecked = self.chkNVNBIBRM8.isChecked()
        if isChecked:
            self.edtNVNBIBRM7.setVisible(True)
            self.chkNVNBIBRM7.setChecked(False)
            self.setProperty(QVariant(self.chkNVNBIBRM8.text()), u'НВНБ:ИБРМ:8')
        else:
            if not self.chkNVNBIBRM7.isChecked():
                self.setProperty(QVariant(), u'НВНБ:ИБРМ:8')
            self.edtNVNBIBRM7.setText('')
            self.edtNVNBIBRM7.setVisible(False)


    @pyqtSlot(bool)
    def on_chkNVNBIBRM3_toggled(self, checked):
        isChecked = self.chkNVNBIBRM3.isChecked()
        if isChecked:
            self.chkNVNBIBRM4.setChecked(False)
            self.setProperty(QVariant(self.chkNVNBIBRM3.text()), u'НВНБ:ИБРМ:3')
        else:
            if not self.chkNVNBIBRM4.isChecked():
                self.setProperty(QVariant(), u'НВНБ:ИБРМ:3')


    @pyqtSlot(bool)
    def on_chkNVNBIBRM4_toggled(self, checked):
        isChecked = self.chkNVNBIBRM4.isChecked()
        if isChecked:
            self.edtNVNBIBRM4.setVisible(True)
            self.chkNVNBIBRM3.setChecked(False)
            self.setProperty(QVariant(self.chkNVNBIBRM4.text()), u'НВНБ:ИБРМ:3')
        else:
            if not self.chkNVNBIBRM3.isChecked():
                self.setProperty(QVariant(), u'НВНБ:ИБРМ:3')
            self.edtNVNBIBRM4.setText('')
            self.edtNVNBIBRM4.setVisible(False)


    @pyqtSlot(bool)
    def on_chkMaritalStatus1_toggled(self, checked):
        isChecked = self.chkMaritalStatus1.isChecked()
        if isChecked:
            self.chkMaritalStatus2.setChecked(False)
            self.chkMaritalStatus3.setChecked(False)
            self.setProperty(QVariant(self.chkMaritalStatus1.text()), u'ОД:ОДП:БС')
        elif not self.chkMaritalStatus2.isChecked() and not self.chkMaritalStatus3.isChecked():
            self.setProperty(QVariant(), u'ОД:ОДП:БС')


    @pyqtSlot(bool)
    def on_chkMaritalStatus2_toggled(self, checked):
        isChecked = self.chkMaritalStatus2.isChecked()
        if isChecked:
            self.chkMaritalStatus1.setChecked(False)
            self.chkMaritalStatus3.setChecked(False)
            self.setProperty(QVariant(self.chkMaritalStatus2.text()), u'ОД:ОДП:БС')
        elif not self.chkMaritalStatus1.isChecked() and not self.chkMaritalStatus3.isChecked():
            self.setProperty(QVariant(), u'ОД:ОДП:БС')


    @pyqtSlot(bool)
    def on_chkMaritalStatus3_toggled(self, checked):
        isChecked = self.chkMaritalStatus3.isChecked()
        if isChecked:
            self.chkMaritalStatus1.setChecked(False)
            self.chkMaritalStatus2.setChecked(False)
            self.setProperty(QVariant(self.chkMaritalStatus3.text()), u'ОД:ОДП:БС')
        elif not self.chkMaritalStatus1.isChecked() and not self.chkMaritalStatus2.isChecked():
            self.setProperty(QVariant(), u'ОД:ОДП:БС')


    @pyqtSlot(bool)
    def on_chkODPOBGNot_toggled(self, checked):
        isChecked = self.chkODPOBGNot.isChecked()
        if isChecked:
            self.chkODPOBGYes.setChecked(False)
            self.edtODPOBGText.setText(u'')
            self.setProperty(QVariant(self.chkODPOBGNot.text()), u'ОД:ПОБ:Ж:1')
            self.edtODPOBGText.setText('')
        elif not self.chkODPOBGYes.isChecked():
            self.setProperty(QVariant(), u'ОД:ПОБ:Ж:1')
            self.edtODPOBGText.setText('')


    @pyqtSlot(bool)
    def on_chkODPOBGYes_toggled(self, checked):
        isChecked = self.chkODPOBGYes.isChecked()
        if isChecked:
            self.chkODPOBGNot.setChecked(False)
            self.setProperty(QVariant(self.chkODPOBGYes.text()), u'ОД:ПОБ:Ж:1')
        else:
            if not self.chkODPOBGNot.isChecked():
                self.setProperty(QVariant(), u'ОД:ПОБ:Ж:1')
            self.edtODPOBGText.setText('')


    @pyqtSlot(bool)
    def on_chkSpontaneously_toggled(self, checked):
        isChecked = self.chkSpontaneously.isChecked()
        if isChecked:
            self.chkInduced.setChecked(False)
            self.chkWithHelpVRT.setChecked(False)
            self.setProperty(QVariant(self.chkSpontaneously.text()), u'ОД:СНБ:БН')
        elif not self.chkInduced.isChecked() and not self.chkWithHelpVRT.isChecked():
            self.setProperty(QVariant(), u'ОД:СНБ:БН')


    @pyqtSlot(bool)
    def on_chkInduced_toggled(self, checked):
        isChecked = self.chkInduced.isChecked()
        if isChecked:
            self.chkSpontaneously.setChecked(False)
            self.chkWithHelpVRT.setChecked(False)
            self.setProperty(QVariant(self.chkInduced.text()), u'ОД:СНБ:БН')
        elif not self.chkWithHelpVRT.isChecked() and not self.chkSpontaneously.isChecked():
            self.setProperty(QVariant(), u'ОД:СНБ:БН')


    @pyqtSlot(bool)
    def on_chkWithHelpVRT_toggled(self, checked):
        isChecked = self.chkWithHelpVRT.isChecked()
        if not isChecked:
            self.chkCryopreserved.setChecked(False)
            self.chkVRTNative.setChecked(False)
            self.edtVRTNumber.setValue(0)
            self.edtVRTDate.setDate(QDate())
            self.edtEmbryosCount.setValue(0)
            self.edtAgePatientCryopreservedDate.setValue(0)
        elif isChecked:
            self.chkSpontaneously.setChecked(False)
            self.chkInduced.setChecked(False)
            self.setProperty(QVariant(self.chkWithHelpVRT.text()), u'ОД:СНБ:БН')
        elif not self.chkInduced.isChecked() and not self.chkSpontaneously.isChecked():
            self.setProperty(QVariant(), u'ОД:СНБ:БН')


    @pyqtSlot(bool)
    def on_chkPregravidarNot_toggled(self, checked):
        isChecked = self.chkPregravidarNot.isChecked()
        if isChecked:
            self.chkPregravidarYes.setChecked(False)
            self.setProperty(QVariant(self.chkPregravidarNot.text()), u'ОД:СНБ:ПП:1')
            self.edtPregravidarText.setText('')
        elif not self.chkPregravidarYes.isChecked():
            self.setProperty(QVariant(), u'ОД:СНБ:ПП:1')
            self.edtPregravidarText.setText('')


    @pyqtSlot(bool)
    def on_chkPregravidarYes_toggled(self, checked):
        isChecked = self.chkPregravidarYes.isChecked()
        if isChecked:
            self.chkPregravidarNot.setChecked(False)
            self.setProperty(QVariant(self.chkPregravidarYes.text()), u'ОД:СНБ:ПП:1')
        else:
            if not self.chkPregravidarNot.isChecked():
                self.setProperty(QVariant(), u'ОД:СНБ:ПП:1')
            self.edtPregravidarText.setText('')


    @pyqtSlot(bool)
    def on_chkVRTNative_toggled(self, checked):
        isChecked = self.chkVRTNative.isChecked()
        if isChecked:
            self.chkCryopreserved.setChecked(False)
            self.setProperty(QVariant(self.chkVRTNative.text()), u'ОД:СНБ:ВРТ:3')
        elif not self.chkCryopreserved.isChecked():
            self.setProperty(QVariant(), u'ОД:СНБ:ВРТ:3')


    @pyqtSlot(bool)
    def on_chkCryopreserved_toggled(self, checked):
        isChecked = self.chkCryopreserved.isChecked()
        if isChecked:
            self.chkVRTNative.setChecked(False)
            self.setProperty(QVariant(self.chkCryopreserved.text()), u'ОД:СНБ:ВРТ:3')
        elif not self.chkVRTNative.isChecked():
            self.setProperty(QVariant(), u'ОД:СНБ:ВРТ:3')


    @pyqtSlot(bool)
    def on_chkOneFetus_toggled(self, checked):
        isChecked = self.chkOneFetus.isChecked()
        if isChecked:
            self.chkMultipleFetus.setChecked(False)
            self.setProperty(QVariant(self.chkOneFetus.text()), u'ОД:СНБ:Б:1')
            self.edtFetusCount.setValue(0)
            self.frame_40.setVisible(False)
            self.frame_41.setVisible(False)
            self.frame_42.setVisible(False)
            self.frame_43.setVisible(False)
        elif not self.chkMultipleFetus.isChecked():
            self.setProperty(QVariant(), u'ОД:СНБ:Б:1')
            self.edtFetusCount.setValue(0)


    @pyqtSlot(bool)
    def on_chkMultipleFetus_toggled(self, checked):
        isChecked = self.chkMultipleFetus.isChecked()
        if isChecked:
            self.chkOneFetus.setChecked(False)
            self.setProperty(QVariant(self.chkMultipleFetus.text()), u'ОД:СНБ:Б:1')
        else:
            if not self.chkOneFetus.isChecked():
                self.setProperty(QVariant(), u'ОД:СНБ:Б:1')
            self.edtFetusCount.setValue(0)


    @pyqtSlot(bool)
    def on_chkODPOBONot_toggled(self, checked):
        isChecked = self.chkODPOBONot.isChecked()
        if isChecked:
            self.chkODPOBOYes.setChecked(False)
            self.setProperty(QVariant(self.chkODPOBONot.text()), u'ОД:ПОБ:О:1')
            self.edtODPOBOLocalizationText.setText('')
        elif not self.chkODPOBOYes.isChecked():
            self.setProperty(QVariant(), u'ОД:ПОБ:О:1')
            self.edtODPOBOLocalizationText.setText('')


    @pyqtSlot(bool)
    def on_chkODPOBOYes_toggled(self, checked):
        isChecked = self.chkODPOBOYes.isChecked()
        if isChecked:
            self.chkODPOBONot.setChecked(False)
            self.setProperty(QVariant(self.chkODPOBOYes.text()), u'ОД:ПОБ:О:1')
        else:
            if not self.chkODPOBONot.isChecked():
                self.setProperty(QVariant(), u'ОД:ПОБ:О:1')
            self.edtODPOBOLocalizationText.setText('')


    @pyqtSlot(bool)
    def on_chkODPOBRVGKWoman_toggled(self, checked):
        isChecked = self.chkODPOBRVGKWoman.isChecked()
        if isChecked:
            self.chkODPOBRVGKMen.setChecked(False)
            self.setProperty(QVariant(self.chkODPOBRVGKWoman.text()), u'ОД:ПОБ:РВЖК:1')
        elif not self.chkODPOBRVGKMen.isChecked():
            self.setProperty(QVariant(), u'ОД:ПОБ:РВЖК:1')


    @pyqtSlot(bool)
    def on_chkODPOBRVGKMen_toggled(self, checked):
        isChecked = self.chkODPOBRVGKMen.isChecked()
        if isChecked:
            self.chkODPOBRVGKWoman.setChecked(False)
            self.setProperty(QVariant(self.chkODPOBRVGKMen.text()), u'ОД:ПОБ:РВЖК:1')
        elif not self.chkODPOBRVGKWoman.isChecked():
            self.setProperty(QVariant(), u'ОД:ПОБ:РВЖК:1')


    @pyqtSlot(bool)
    def on_chkODPOBRVGKNotEnough_toggled(self, checked):
        isChecked = self.chkODPOBRVGKNotEnough.isChecked()
        if isChecked:
            self.chkODPOBRVGKRedundant.setChecked(False)
            self.chkODPOBRVGKNormal.setChecked(False)
            self.setProperty(QVariant(self.chkODPOBRVGKNotEnough.text()), u'ОД:ПОБ:РВЖК:2')
        elif not self.chkODPOBRVGKRedundant.isChecked() and not self.chkODPOBRVGKNormal.isChecked():
            self.setProperty(QVariant(), u'ОД:ПОБ:РВЖК:2')


    @pyqtSlot(bool)
    def on_chkODPOBRVGKNormal_toggled(self, checked):
        isChecked = self.chkODPOBRVGKNormal.isChecked()
        if isChecked:
            self.chkODPOBRVGKNotEnough.setChecked(False)
            self.chkODPOBRVGKRedundant.setChecked(False)
            self.setProperty(QVariant(self.chkODPOBRVGKNormal.text()), u'ОД:ПОБ:РВЖК:2')
        elif not self.chkODPOBRVGKNotEnough.isChecked() and not self.chkODPOBRVGKRedundant.isChecked():
            self.setProperty(QVariant(), u'ОД:ПОБ:РВЖК:2')


    @pyqtSlot(bool)
    def on_chkODPOBRVGKRedundant_toggled(self, checked):
        isChecked = self.chkODPOBRVGKRedundant.isChecked()
        if isChecked:
            self.chkODPOBRVGKNotEnough.setChecked(False)
            self.chkODPOBRVGKNormal.setChecked(False)
            self.setProperty(QVariant(self.chkODPOBRVGKRedundant.text()), u'ОД:ПОБ:РВЖК:2')
        elif not self.chkODPOBRVGKNotEnough.isChecked() and not self.chkODPOBRVGKNormal.isChecked():
            self.setProperty(QVariant(), u'ОД:ПОБ:РВЖК:2')


    @pyqtSlot(bool)
    def on_chkODPOBVRVNKNot_toggled(self, checked):
        isChecked = self.chkODPOBVRVNKNot.isChecked()
        if isChecked:
            self.chkODPOBVRVNKYes.setChecked(False)
            self.setProperty(QVariant(self.chkODPOBVRVNKNot.text()), u'ОД:ПОБ:ВРВНК')
        elif not self.chkODPOBVRVNKYes.isChecked():
            self.setProperty(QVariant(), u'ОД:ПОБ:ВРВНК')


    @pyqtSlot(bool)
    def on_chkODPOBVRVNKYes_toggled(self, checked):
        isChecked = self.chkODPOBVRVNKYes.isChecked()
        if isChecked:
            self.chkODPOBVRVNKNot.setChecked(False)
            self.setProperty(QVariant(self.chkODPOBVRVNKYes.text()), u'ОД:ПОБ:ВРВНК')
        elif not self.chkODPOBVRVNKNot.isChecked():
            self.setProperty(QVariant(), u'ОД:ПОБ:ВРВНК')


    @pyqtSlot(bool)
    def on_chkODPOBULUNot_toggled(self, checked):
        isChecked = self.chkODPOBULUNot.isChecked()
        if isChecked:
            self.chkODPOBULUYes.setChecked(False)
            self.setProperty(QVariant(self.chkODPOBULUNot.text()), u'ОД:ПОБ:УЛУ:1')
            self.edtODPOBULULocalizationText.setText('')
        elif not self.chkODPOBULUYes.isChecked():
            self.setProperty(QVariant(), u'ОД:ПОБ:УЛУ:1')
            self.edtODPOBULULocalizationText.setText('')


    @pyqtSlot(bool)
    def on_chkODPOBULUYes_toggled(self, checked):
        isChecked = self.chkODPOBULUYes.isChecked()
        if isChecked:
            self.chkODPOBULUNot.setChecked(False)
            self.setProperty(QVariant(self.chkODPOBULUYes.text()), u'ОД:ПОБ:УЛУ:1')
        else:
            if not self.chkODPOBULUNot.isChecked():
                self.setProperty(QVariant(), u'ОД:ПОБ:УЛУ:1')
            self.edtODPOBULULocalizationText.setText('')


    @pyqtSlot(bool)
    def on_chkODPOBOPMG1_toggled(self, checked):
        isChecked = self.chkODPOBOPMG1.isChecked()
        if isChecked:
            self.chkODPOBOPMG2.setChecked(False)
            self.chkODPOBOPMG3.setChecked(False)
            self.setProperty(QVariant(self.chkODPOBOPMG1.text()), u'ОД:ПОБ:ОПМЖ:1')
            self.edtODPOBOPMG3Text.setText('')
        elif not self.chkODPOBOPMG2.isChecked() and not self.chkODPOBOPMG3.isChecked():
            self.setProperty(QVariant(), u'ОД:ПОБ:ОПМЖ:1')


    @pyqtSlot(bool)
    def on_chkODPOBOPMG2_toggled(self, checked):
        isChecked = self.chkODPOBOPMG2.isChecked()
        if isChecked:
            self.chkODPOBOPMG1.setChecked(False)
            self.chkODPOBOPMG3.setChecked(False)
            self.setProperty(QVariant(self.chkODPOBOPMG2.text()), u'ОД:ПОБ:ОПМЖ:1')
            self.edtODPOBOPMG3Text.setText('')
        elif not self.chkODPOBOPMG1.isChecked() and not self.chkODPOBOPMG3.isChecked():
            self.setProperty(QVariant(), u'ОД:ПОБ:ОПМЖ:1')


    @pyqtSlot(bool)
    def on_chkODPOBOPMG3_toggled(self, checked):
        isChecked = self.chkODPOBOPMG3.isChecked()
        if isChecked:
            self.chkODPOBOPMG1.setChecked(False)
            self.chkODPOBOPMG2.setChecked(False)
            self.setProperty(QVariant(self.chkODPOBOPMG3.text()), u'ОД:ПОБ:ОПМЖ:1')
        else:
            if not self.chkODPOBOPMG1.isChecked() and not self.chkODPOBOPMG2.isChecked():
                self.setProperty(QVariant(), u'ОД:ПОБ:ОПМЖ:1')
            self.edtODPOBOPMG3Text.setText('')


    @pyqtSlot(bool)
    def on_chkODPOBOPMG4_toggled(self, checked):
        isChecked = self.chkODPOBOPMG4.isChecked()
        if isChecked:
            self.chkODPOBOPMG5.setChecked(False)
            self.setProperty(QVariant(self.chkODPOBOPMG4.text()), u'ОД:ПОБ:ОПМЖ:3')
        elif not self.chkODPOBOPMG5.isChecked():
            self.setProperty(QVariant(), u'ОД:ПОБ:ОПМЖ:3')


    @pyqtSlot(bool)
    def on_chkODPOBOPMG5_toggled(self, checked):
        isChecked = self.chkODPOBOPMG5.isChecked()
        if isChecked:
            self.chkODPOBOPMG4.setChecked(False)
            self.setProperty(QVariant(self.chkODPOBOPMG5.text()), u'ОД:ПОБ:ОПМЖ:3')
        elif not self.chkODPOBOPMG4.isChecked():
            self.setProperty(QVariant(), u'ОД:ПОБ:ОПМЖ:3')


    @pyqtSlot(bool)
    def on_chkODPOBC1_toggled(self, checked):
        isChecked = self.chkODPOBC1.isChecked()
        if isChecked:
            self.chkODPOBC2.setChecked(False)
            self.chkODPOBC3.setChecked(False)
            self.setProperty(QVariant(self.chkODPOBC1.text()), u'ОД:ПОБ:С:1')
            self.edtODPOBC3Text.setText('')
        elif not self.chkODPOBC2.isChecked() and not self.chkODPOBC3.isChecked():
            self.setProperty(QVariant(), u'ОД:ПОБ:С:1')


    @pyqtSlot(bool)
    def on_chkODPOBC2_toggled(self, checked):
        isChecked = self.chkODPOBC2.isChecked()
        if isChecked:
            self.chkODPOBC1.setChecked(False)
            self.chkODPOBC3.setChecked(False)
            self.setProperty(QVariant(self.chkODPOBC2.text()), u'ОД:ПОБ:С:1')
            self.edtODPOBC3Text.setText('')
        elif not self.chkODPOBC1.isChecked() and not self.chkODPOBC3.isChecked():
            self.setProperty(QVariant(), u'ОД:ПОБ:С:1')


    @pyqtSlot(bool)
    def on_chkODPOBC3_toggled(self, checked):
        isChecked = self.chkODPOBC3.isChecked()
        if isChecked:
            self.chkODPOBC1.setChecked(False)
            self.chkODPOBC2.setChecked(False)
            self.setProperty(QVariant(self.chkODPOBC3.text()), u'ОД:ПОБ:С:1')
        else:
            if not self.chkODPOBC1.isChecked() and not self.chkODPOBC2.isChecked():
                self.setProperty(QVariant(), u'ОД:ПОБ:С:1')
            self.edtODPOBC3Text.setText('')


    @pyqtSlot(bool)
    def on_chkODPOBTS1_toggled(self, checked):
        isChecked = self.chkODPOBTS1.isChecked()
        if isChecked:
            self.chkODPOBTS2.setChecked(False)
            self.setProperty(QVariant(self.chkODPOBTS1.text()), u'ОД:ПОБ:ТС:1')
            self.edtODPOBTS2Text.setText('')
        elif not self.chkODPOBTS2.isChecked():
            self.setProperty(QVariant(), u'ОД:ПОБ:ТС:1')
            self.edtODPOBTS2Text.setText('')


    @pyqtSlot(bool)
    def on_chkODPOBTS2_toggled(self, checked):
        isChecked = self.chkODPOBTS2.isChecked()
        if isChecked:
            self.chkODPOBTS1.setChecked(False)
            self.setProperty(QVariant(self.chkODPOBTS2.text()), u'ОД:ПОБ:ТС:1')
        else:
            if not self.chkODPOBTS1.isChecked():
                self.setProperty(QVariant(), u'ОД:ПОБ:ТС:1')
            self.edtODPOBTS2Text.setText('')


    @pyqtSlot(bool)
    def on_chkODPOBAL1_toggled(self, checked):
        isChecked = self.chkODPOBAL1.isChecked()
        if isChecked:
            self.chkODPOBAL2.setChecked(False)
            self.setProperty(QVariant(self.chkODPOBAL1.text()), u'ОД:ПОБ:АЛ:1')
            self.edtODPOBAL2Text.setText('')
        elif not self.chkODPOBAL2.isChecked():
            self.setProperty(QVariant(), u'ОД:ПОБ:АЛ:1')
            self.edtODPOBAL2Text.setText('')


    @pyqtSlot(bool)
    def on_chkODPOBAL2_toggled(self, checked):
        isChecked = self.chkODPOBAL2.isChecked()
        if isChecked:
            self.chkODPOBAL1.setChecked(False)
            self.setProperty(QVariant(self.chkODPOBAL2.text()), u'ОД:ПОБ:АЛ:1')
        else:
            if not self.chkODPOBAL1.isChecked():
                self.setProperty(QVariant(), u'ОД:ПОБ:АЛ:1')
            self.edtODPOBAL2Text.setText('')


    @pyqtSlot(bool)
    def on_chkODPOBSP1_toggled(self, checked):
        isChecked = self.chkODPOBSP1.isChecked()
        if isChecked:
            self.chkODPOBSP2.setChecked(False)
            self.setProperty(QVariant(self.chkODPOBSP1.text()), u'ОД:ПОБ:ШП16')
        elif not self.chkODPOBSP2.isChecked():
            self.setProperty(QVariant(), u'ОД:ПОБ:ШП16')


    @pyqtSlot(bool)
    def on_chkODPOBSP2_toggled(self, checked):
        isChecked = self.chkODPOBSP2.isChecked()
        if isChecked:
            self.chkODPOBSP1.setChecked(False)
            self.setProperty(QVariant(self.chkODPOBSP2.text()), u'ОД:ПОБ:ШП16')
        else:
            if not self.chkODPOBSP1.isChecked():
                self.setProperty(QVariant(), u'ОД:ПОБ:ШП16')

# ################################################################


    @pyqtSlot(bool)
    def on_chkODPOBGCH1_1_toggled(self, checked):
        isChecked = self.chkODPOBGCH1_1.isChecked()
        if isChecked:
            self.chkODPOBGCH2_1.setChecked(False)
            self.setProperty(QVariant(self.chkODPOBGCH1_1.text()), u'ОД:ПОБ:ПЧ34')
        elif not self.chkODPOBGCH2_1.isChecked():
            self.setProperty(QVariant(), u'ОД:ПОБ:ПЧ34')


    @pyqtSlot(bool)
    def on_chkODPOBGCH2_1_toggled(self, checked):
        isChecked = self.chkODPOBGCH2_1.isChecked()
        if isChecked:
            self.chkODPOBGCH1_1.setChecked(False)
            self.setProperty(QVariant(self.chkODPOBGCH2_1.text()), u'ОД:ПОБ:ПЧ34')
        else:
            if not self.chkODPOBGCH1_1.isChecked():
                self.setProperty(QVariant(), u'ОД:ПОБ:ПЧ34')


    @pyqtSlot(bool)
    def on_chkODPOBGCH1_2_toggled(self, checked):
        isChecked = self.chkODPOBGCH1_2.isChecked()
        if isChecked:
            self.chkODPOBGCH2_2.setChecked(False)
            self.setProperty(QVariant(self.chkODPOBGCH1_2.text()), u'ОД:ПОБ:ПЧ34:2')
        elif not self.chkODPOBGCH2_2.isChecked():
            self.setProperty(QVariant(), u'ОД:ПОБ:ПЧ34:2')


    @pyqtSlot(bool)
    def on_chkODPOBGCH2_2_toggled(self, checked):
        isChecked = self.chkODPOBGCH2_2.isChecked()
        if isChecked:
            self.chkODPOBGCH1_2.setChecked(False)
            self.setProperty(QVariant(self.chkODPOBGCH2_2.text()), u'ОД:ПОБ:ПЧ34:2')
        else:
            if not self.chkODPOBGCH1_2.isChecked():
                self.setProperty(QVariant(), u'ОД:ПОБ:ПЧ34:2')


    @pyqtSlot(bool)
    def on_chkODPOBGCH1_3_toggled(self, checked):
        isChecked = self.chkODPOBGCH1_3.isChecked()
        if isChecked:
            self.chkODPOBGCH2_3.setChecked(False)
            self.setProperty(QVariant(self.chkODPOBGCH1_3.text()), u'ОД:ПОБ:ПЧ34:3')
        elif not self.chkODPOBGCH2_3.isChecked():
            self.setProperty(QVariant(), u'ОД:ПОБ:ПЧ34:3')


    @pyqtSlot(bool)
    def on_chkODPOBGCH2_3_toggled(self, checked):
        isChecked = self.chkODPOBGCH2_3.isChecked()
        if isChecked:
            self.chkODPOBGCH1_3.setChecked(False)
            self.setProperty(QVariant(self.chkODPOBGCH2_3.text()), u'ОД:ПОБ:ПЧ34:3')
        else:
            if not self.chkODPOBGCH1_3.isChecked():
                self.setProperty(QVariant(), u'ОД:ПОБ:ПЧ34:3')


    @pyqtSlot(bool)
    def on_chkODPOBGCH1_4_toggled(self, checked):
        isChecked = self.chkODPOBGCH1_4.isChecked()
        if isChecked:
            self.chkODPOBGCH2_4.setChecked(False)
            self.setProperty(QVariant(self.chkODPOBGCH1_4.text()), u'ОД:ПОБ:ПЧ34:4')
        elif not self.chkODPOBGCH2_4.isChecked():
            self.setProperty(QVariant(), u'ОД:ПОБ:ПЧ34:4')


    @pyqtSlot(bool)
    def on_chkODPOBGCH2_4_toggled(self, checked):
        isChecked = self.chkODPOBGCH2_4.isChecked()
        if isChecked:
            self.chkODPOBGCH1_4.setChecked(False)
            self.setProperty(QVariant(self.chkODPOBGCH2_4.text()), u'ОД:ПОБ:ПЧ34:4')
        else:
            if not self.chkODPOBGCH1_4.isChecked():
                self.setProperty(QVariant(), u'ОД:ПОБ:ПЧ34:4')


    @pyqtSlot(bool)
    def on_chkODPOBGCH1_5_toggled(self, checked):
        isChecked = self.chkODPOBGCH1_5.isChecked()
        if isChecked:
            self.chkODPOBGCH2_5.setChecked(False)
            self.setProperty(QVariant(self.chkODPOBGCH1_5.text()), u'ОД:ПОБ:ПЧ34:5')
        elif not self.chkODPOBGCH2_5.isChecked():
            self.setProperty(QVariant(), u'ОД:ПОБ:ПЧ34:5')


    @pyqtSlot(bool)
    def on_chkODPOBGCH2_5_toggled(self, checked):
        isChecked = self.chkODPOBGCH2_5.isChecked()
        if isChecked:
            self.chkODPOBGCH1_5.setChecked(False)
            self.setProperty(QVariant(self.chkODPOBGCH2_5.text()), u'ОД:ПОБ:ПЧ34:5')
        else:
            if not self.chkODPOBGCH1_5.isChecked():
                self.setProperty(QVariant(), u'ОД:ПОБ:ПЧ34:5')


    @pyqtSlot(bool)
    def on_chkODPOBMT1_1_toggled(self, checked):
        isChecked = self.chkODPOBMT1_1.isChecked()
        if isChecked:
            self.chkODPOBMT2_1.setChecked(False)
            self.setProperty(QVariant(self.chkODPOBMT1_1.text()), u'ОД:ПОБ:МТ:1')
        elif not self.chkODPOBMT2_1.isChecked():
            self.setProperty(QVariant(), u'ОД:ПОБ:МТ:1')


    @pyqtSlot(bool)
    def on_chkODPOBMT1_2_toggled(self, checked):
        isChecked = self.chkODPOBMT1_2.isChecked()
        if isChecked:
            self.chkODPOBMT2_2.setChecked(False)
            self.setProperty(QVariant(self.chkODPOBMT1_2.text()), u'ОД:ПОБ:МТ:2')
        elif not self.chkODPOBMT2_2.isChecked():
            self.setProperty(QVariant(), u'ОД:ПОБ:МТ:2')


    @pyqtSlot(bool)
    def on_chkODPOBMT1_3_toggled(self, checked):
        isChecked = self.chkODPOBMT1_3.isChecked()
        if isChecked:
            self.chkODPOBMT2_3.setChecked(False)
            self.setProperty(QVariant(self.chkODPOBMT1_3.text()), u'ОД:ПОБ:МТ:3')
        elif not self.chkODPOBMT2_3.isChecked():
            self.setProperty(QVariant(), u'ОД:ПОБ:МТ:3')


    @pyqtSlot(bool)
    def on_chkODPOBMT1_4_toggled(self, checked):
        isChecked = self.chkODPOBMT1_4.isChecked()
        if isChecked:
            self.chkODPOBMT2_4.setChecked(False)
            self.setProperty(QVariant(self.chkODPOBMT1_4.text()), u'ОД:ПОБ:МТ:4')
        elif not self.chkODPOBMT2_4.isChecked():
            self.setProperty(QVariant(), u'ОД:ПОБ:МТ:4')


    @pyqtSlot(bool)
    def on_chkODPOBMT1_5_toggled(self, checked):
        isChecked = self.chkODPOBMT1_5.isChecked()
        if isChecked:
            self.chkODPOBMT2_5.setChecked(False)
            self.setProperty(QVariant(self.chkODPOBMT1_5.text()), u'ОД:ПОБ:МТ:5')
        elif not self.chkODPOBMT2_5.isChecked():
            self.setProperty(QVariant(), u'ОД:ПОБ:МТ:5')


    @pyqtSlot(bool)
    def on_chkODPOBMT2_1_toggled(self, checked):
        isChecked = self.chkODPOBMT2_1.isChecked()
        if isChecked:
            self.chkODPOBMT1_1.setChecked(False)
            self.setProperty(QVariant(self.chkODPOBMT2_1.text()), u'ОД:ПОБ:МТ:1')
        else:
            if not self.chkODPOBMT1_1.isChecked():
                self.setProperty(QVariant(), u'ОД:ПОБ:МТ:1')


    @pyqtSlot(bool)
    def on_chkODPOBMT2_2_toggled(self, checked):
        isChecked = self.chkODPOBMT2_2.isChecked()
        if isChecked:
            self.chkODPOBMT1_2.setChecked(False)
            self.setProperty(QVariant(self.chkODPOBMT2_2.text()), u'ОД:ПОБ:МТ:2')
        else:
            if not self.chkODPOBMT1_2.isChecked():
                self.setProperty(QVariant(), u'ОД:ПОБ:МТ:2')


    @pyqtSlot(bool)
    def on_chkODPOBMT2_3_toggled(self, checked):
        isChecked = self.chkODPOBMT2_3.isChecked()
        if isChecked:
            self.chkODPOBMT1_3.setChecked(False)
            self.setProperty(QVariant(self.chkODPOBMT2_3.text()), u'ОД:ПОБ:МТ:3')
        else:
            if not self.chkODPOBMT1_3.isChecked():
                self.setProperty(QVariant(), u'ОД:ПОБ:МТ:3')


    @pyqtSlot(bool)
    def on_chkODPOBMT2_4_toggled(self, checked):
        isChecked = self.chkODPOBMT2_4.isChecked()
        if isChecked:
            self.chkODPOBMT1_4.setChecked(False)
            self.setProperty(QVariant(self.chkODPOBMT2_4.text()), u'ОД:ПОБ:МТ:4')
        else:
            if not self.chkODPOBMT1_4.isChecked():
                self.setProperty(QVariant(), u'ОД:ПОБ:МТ:4')


    @pyqtSlot(bool)
    def on_chkODPOBMT2_5_toggled(self, checked):
        isChecked = self.chkODPOBMT2_5.isChecked()
        if isChecked:
            self.chkODPOBMT1_5.setChecked(False)
            self.setProperty(QVariant(self.chkODPOBMT2_5.text()), u'ОД:ПОБ:МТ:5')
        else:
            if not self.chkODPOBMT1_5.isChecked():
                self.setProperty(QVariant(), u'ОД:ПОБ:МТ:5')


    @pyqtSlot(bool)
    def on_chkODPOBSBPR1_1_toggled(self, checked):
        isChecked = self.chkODPOBSBPR1_1.isChecked()
        if isChecked:
            self.chkODPOBSBPR3_1.setChecked(False)
            self.addValuePropertyList(self.chkODPOBSBPR1_1.text(), u'ОД:ПОБ:СПР1:1')
        else:
            if not self.chkODPOBSBPR3_1.isChecked() and not self.chkODPOBSBPR2_1.isChecked():
                self.setProperty(QVariant(), u'ОД:ПОБ:СПР1:1')
            else:
                self.deletedValuePropertyList(self.chkODPOBSBPR1_1.text(), u'ОД:ПОБ:СПР1:1')
            self.edtODPOBSBPR_1.setText('')


    @pyqtSlot(bool)
    def on_chkODPOBSBPR1_2_toggled(self, checked):
        isChecked = self.chkODPOBSBPR1_2.isChecked()
        if isChecked:
            self.chkODPOBSBPR3_2.setChecked(False)
            self.addValuePropertyList(self.chkODPOBSBPR1_2.text(), u'ОД:ПОБ:СПР1:2')
        else:
            if not self.chkODPOBSBPR3_2.isChecked() and not self.chkODPOBSBPR2_2.isChecked():
                self.setProperty(QVariant(), u'ОД:ПОБ:СПР1:2')
            else:
                self.deletedValuePropertyList(self.chkODPOBSBPR1_2.text(), u'ОД:ПОБ:СПР1:2')
            self.edtODPOBSBPR_2.setText('')


    @pyqtSlot(bool)
    def on_chkODPOBSBPR1_3_toggled(self, checked):
        isChecked = self.chkODPOBSBPR1_3.isChecked()
        if isChecked:
            self.chkODPOBSBPR3_3.setChecked(False)
            self.addValuePropertyList(self.chkODPOBSBPR1_3.text(), u'ОД:ПОБ:СПР1:3')
        else:
            if not self.chkODPOBSBPR3_3.isChecked() and not self.chkODPOBSBPR2_3.isChecked():
                self.setProperty(QVariant(), u'ОД:ПОБ:СПР1:3')
            else:
                self.deletedValuePropertyList(self.chkODPOBSBPR1_3.text(), u'ОД:ПОБ:СПР1:3')
            self.edtODPOBSBPR_3.setText('')


    @pyqtSlot(bool)
    def on_chkODPOBSBPR1_4_toggled(self, checked):
        isChecked = self.chkODPOBSBPR1_4.isChecked()
        if isChecked:
            self.chkODPOBSBPR3_4.setChecked(False)
            self.addValuePropertyList(self.chkODPOBSBPR1_4.text(), u'ОД:ПОБ:СПР1:4')
        else:
            if not self.chkODPOBSBPR3_4.isChecked() and not self.chkODPOBSBPR2_4.isChecked():
                self.setProperty(QVariant(), u'ОД:ПОБ:СПР1:4')
            else:
                self.deletedValuePropertyList(self.chkODPOBSBPR1_4.text(), u'ОД:ПОБ:СПР1:4')
            self.edtODPOBSBPR_4.setText('')


    @pyqtSlot(bool)
    def on_chkODPOBSBPR1_5_toggled(self, checked):
        isChecked = self.chkODPOBSBPR1_5.isChecked()
        if isChecked:
            self.chkODPOBSBPR3_5.setChecked(False)
            self.addValuePropertyList(self.chkODPOBSBPR1_5.text(), u'ОД:ПОБ:СПР1:5')
        else:
            if not self.chkODPOBSBPR3_5.isChecked() and not self.chkODPOBSBPR2_5.isChecked():
                self.setProperty(QVariant(), u'ОД:ПОБ:СПР1:5')
            else:
                self.deletedValuePropertyList(self.chkODPOBSBPR1_5.text(), u'ОД:ПОБ:СПР1:5')
            self.edtODPOBSBPR_5.setText('')


    @pyqtSlot(bool)
    def on_chkODPOBSBPR2_1_toggled(self, checked):
        isChecked = self.chkODPOBSBPR2_1.isChecked()
        if isChecked:
            self.chkODPOBSBPR3_1.setChecked(False)
            self.addValuePropertyList(self.chkODPOBSBPR2_1.text(), u'ОД:ПОБ:СПР1:1')
        else:
            if not self.chkODPOBSBPR3_1.isChecked() and not self.chkODPOBSBPR1_1.isChecked():
                self.setProperty(QVariant(), u'ОД:ПОБ:СПР1:1')
            else:
                self.deletedValuePropertyList(self.chkODPOBSBPR2_1.text(), u'ОД:ПОБ:СПР1:1')
            self.edtODPOBSBPR_1.setText('')


    @pyqtSlot(bool)
    def on_chkODPOBSBPR2_2_toggled(self, checked):
        isChecked = self.chkODPOBSBPR2_2.isChecked()
        if isChecked:
            self.chkODPOBSBPR3_2.setChecked(False)
            self.addValuePropertyList(self.chkODPOBSBPR2_2.text(), u'ОД:ПОБ:СПР1:2')
        else:
            if not self.chkODPOBSBPR3_2.isChecked() and not self.chkODPOBSBPR1_2.isChecked():
                self.setProperty(QVariant(), u'ОД:ПОБ:СПР1:2')
            else:
                self.deletedValuePropertyList(self.chkODPOBSBPR2_2.text(), u'ОД:ПОБ:СПР1:2')
            self.edtODPOBSBPR_2.setText('')


    @pyqtSlot(bool)
    def on_chkODPOBSBPR2_3_toggled(self, checked):
        isChecked = self.chkODPOBSBPR2_3.isChecked()
        if isChecked:
            self.chkODPOBSBPR3_3.setChecked(False)
            self.addValuePropertyList(self.chkODPOBSBPR2_3.text(), u'ОД:ПОБ:СПР1:3')
        else:
            if not self.chkODPOBSBPR3_3.isChecked() and not self.chkODPOBSBPR1_3.isChecked():
                self.setProperty(QVariant(), u'ОД:ПОБ:СПР1:3')
            else:
                self.deletedValuePropertyList(self.chkODPOBSBPR2_3.text(), u'ОД:ПОБ:СПР1:3')
            self.edtODPOBSBPR_3.setText('')


    @pyqtSlot(bool)
    def on_chkODPOBSBPR2_4_toggled(self, checked):
        isChecked = self.chkODPOBSBPR2_4.isChecked()
        if isChecked:
            self.chkODPOBSBPR3_4.setChecked(False)
            self.addValuePropertyList(self.chkODPOBSBPR2_4.text(), u'ОД:ПОБ:СПР1:4')
        else:
            if not self.chkODPOBSBPR3_4.isChecked() and not self.chkODPOBSBPR1_4.isChecked():
                self.setProperty(QVariant(), u'ОД:ПОБ:СПР1:4')
            else:
                self.deletedValuePropertyList(self.chkODPOBSBPR2_4.text(), u'ОД:ПОБ:СПР1:4')
            self.edtODPOBSBPR_4.setText('')


    @pyqtSlot(bool)
    def on_chkODPOBSBPR2_5_toggled(self, checked):
        isChecked = self.chkODPOBSBPR2_5.isChecked()
        if isChecked:
            self.chkODPOBSBPR3_5.setChecked(False)
            self.addValuePropertyList(self.chkODPOBSBPR2_5.text(), u'ОД:ПОБ:СПР1:5')
        else:
            if not self.chkODPOBSBPR3_5.isChecked() and not self.chkODPOBSBPR1_5.isChecked():
                self.setProperty(QVariant(), u'ОД:ПОБ:СПР1:5')
            else:
                self.deletedValuePropertyList(self.chkODPOBSBPR2_5.text(), u'ОД:ПОБ:СПР1:5')
            self.edtODPOBSBPR_5.setText('')


    @pyqtSlot(bool)
    def on_chkODPOBSBPR3_1_toggled(self, checked):
        isChecked = self.chkODPOBSBPR3_1.isChecked()
        if isChecked:
            self.chkODPOBSBPR1_1.setChecked(False)
            self.chkODPOBSBPR2_1.setChecked(False)
            self.setProperty(QVariant(self.chkODPOBSBPR3_1.text()), u'ОД:ПОБ:СПР1:1')
        else:
            if not self.chkODPOBSBPR1_1.isChecked() and not self.chkODPOBSBPR2_1.isChecked():
                self.setProperty(QVariant(), u'ОД:ПОБ:СПР1:1')
            else:
                self.deletedValuePropertyList(self.chkODPOBSBPR3_1.text(), u'ОД:ПОБ:СПР1:1')


    @pyqtSlot(bool)
    def on_chkODPOBSBPR3_2_toggled(self, checked):
        isChecked = self.chkODPOBSBPR3_2.isChecked()
        if isChecked:
            self.chkODPOBSBPR1_2.setChecked(False)
            self.chkODPOBSBPR2_2.setChecked(False)
            self.setProperty(QVariant(self.chkODPOBSBPR3_2.text()), u'ОД:ПОБ:СПР1:2')
        else:
            if not self.chkODPOBSBPR1_2.isChecked() and not self.chkODPOBSBPR2_2.isChecked():
                self.setProperty(QVariant(), u'ОД:ПОБ:СПР1:2')
            else:
                self.deletedValuePropertyList(self.chkODPOBSBPR3_2.text(), u'ОД:ПОБ:СПР1:2')


    @pyqtSlot(bool)
    def on_chkODPOBSBPR3_3_toggled(self, checked):
        isChecked = self.chkODPOBSBPR3_3.isChecked()
        if isChecked:
            self.chkODPOBSBPR1_3.setChecked(False)
            self.chkODPOBSBPR2_3.setChecked(False)
            self.setProperty(QVariant(self.chkODPOBSBPR3_3.text()), u'ОД:ПОБ:СПР1:3')
        else:
            if not self.chkODPOBSBPR1_3.isChecked() and not self.chkODPOBSBPR2_3.isChecked():
                self.setProperty(QVariant(), u'ОД:ПОБ:СПР1:3')
            else:
                self.deletedValuePropertyList(self.chkODPOBSBPR3_3.text(), u'ОД:ПОБ:СПР1:3')


    @pyqtSlot(bool)
    def on_chkODPOBSBPR3_4_toggled(self, checked):
        isChecked = self.chkODPOBSBPR3_4.isChecked()
        if isChecked:
            self.chkODPOBSBPR1_4.setChecked(False)
            self.chkODPOBSBPR2_4.setChecked(False)
            self.setProperty(QVariant(self.chkODPOBSBPR3_4.text()), u'ОД:ПОБ:СПР1:4')
        else:
            if not self.chkODPOBSBPR1_4.isChecked() and not self.chkODPOBSBPR2_4.isChecked():
                self.setProperty(QVariant(), u'ОД:ПОБ:СПР1:4')
            else:
                self.deletedValuePropertyList(self.chkODPOBSBPR3_4.text(), u'ОД:ПОБ:СПР1:4')


    @pyqtSlot(bool)
    def on_chkODPOBSBPR3_5_toggled(self, checked):
        isChecked = self.chkODPOBSBPR3_5.isChecked()
        if isChecked:
            self.chkODPOBSBPR1_5.setChecked(False)
            self.chkODPOBSBPR2_5.setChecked(False)
            self.setProperty(QVariant(self.chkODPOBSBPR3_5.text()), u'ОД:ПОБ:СПР1:5')
        else:
            if not self.chkODPOBSBPR1_5.isChecked() and not self.chkODPOBSBPR2_5.isChecked():
                self.setProperty(QVariant(), u'ОД:ПОБ:СПР1:5')
            else:
                self.deletedValuePropertyList(self.chkODPOBSBPR3_5.text(), u'ОД:ПОБ:СПР1:5')


    @pyqtSlot(bool)
    def on_chkODPOBRPPGRF1_1_toggled(self, checked):
        isChecked = self.chkODPOBRPPGRF1_1.isChecked()
        if isChecked:
            self.chkODPOBRPPGRF2_1.setChecked(False)
            self.setProperty(QVariant(self.chkODPOBRPPGRF1_1.text()), u'ОД:ПОБ:РППГРФ:1')
        elif not self.chkODPOBRPPGRF2_1.isChecked():
            self.setProperty(QVariant(), u'ОД:ПОБ:РППГРФ:1')


    @pyqtSlot(bool)
    def on_chkODPOBRPPGRF2_1_toggled(self, checked):
        isChecked = self.chkODPOBRPPGRF2_1.isChecked()
        if isChecked:
            self.chkODPOBRPPGRF1_1.setChecked(False)
            self.setProperty(QVariant(self.chkODPOBRPPGRF2_1.text()), u'ОД:ПОБ:РППГРФ:1')
        else:
            if not self.chkODPOBRPPGRF1_1.isChecked():
                self.setProperty(QVariant(), u'ОД:ПОБ:РППГРФ:1')


    @pyqtSlot(bool)
    def on_chkODPOBRPPGRF1_2_toggled(self, checked):
        isChecked = self.chkODPOBRPPGRF1_2.isChecked()
        if isChecked:
            self.chkODPOBRPPGRF2_2.setChecked(False)
            self.setProperty(QVariant(self.chkODPOBRPPGRF1_2.text()), u'ОД:ПОБ:РППГРФ:2')
        elif not self.chkODPOBRPPGRF2_2.isChecked():
            self.setProperty(QVariant(), u'ОД:ПОБ:РППГРФ:2')


    @pyqtSlot(bool)
    def on_chkODPOBRPPGRF2_2_toggled(self, checked):
        isChecked = self.chkODPOBRPPGRF2_2.isChecked()
        if isChecked:
            self.chkODPOBRPPGRF1_2.setChecked(False)
            self.setProperty(QVariant(self.chkODPOBRPPGRF2_2.text()), u'ОД:ПОБ:РППГРФ:2')
        else:
            if not self.chkODPOBRPPGRF1_2.isChecked():
                self.setProperty(QVariant(), u'ОД:ПОБ:РППГРФ:2')


    @pyqtSlot(bool)
    def on_chkODPOBRPPGRF1_3_toggled(self, checked):
        isChecked = self.chkODPOBRPPGRF1_3.isChecked()
        if isChecked:
            self.chkODPOBRPPGRF2_3.setChecked(False)
            self.setProperty(QVariant(self.chkODPOBRPPGRF1_3.text()), u'ОД:ПОБ:РППГРФ:3')
        elif not self.chkODPOBRPPGRF2_3.isChecked():
            self.setProperty(QVariant(), u'ОД:ПОБ:РППГРФ:3')


    @pyqtSlot(bool)
    def on_chkODPOBRPPGRF2_3_toggled(self, checked):
        isChecked = self.chkODPOBRPPGRF2_3.isChecked()
        if isChecked:
            self.chkODPOBRPPGRF1_3.setChecked(False)
            self.setProperty(QVariant(self.chkODPOBRPPGRF2_3.text()), u'ОД:ПОБ:РППГРФ:3')
        else:
            if not self.chkODPOBRPPGRF1_3.isChecked():
                self.setProperty(QVariant(), u'ОД:ПОБ:РППГРФ:3')


    @pyqtSlot(bool)
    def on_chkODPOBRPPGRF1_4_toggled(self, checked):
        isChecked = self.chkODPOBRPPGRF1_4.isChecked()
        if isChecked:
            self.chkODPOBRPPGRF2_4.setChecked(False)
            self.setProperty(QVariant(self.chkODPOBRPPGRF1_4.text()), u'ОД:ПОБ:РППГРФ:4')
        elif not self.chkODPOBRPPGRF2_4.isChecked():
            self.setProperty(QVariant(), u'ОД:ПОБ:РППГРФ:4')


    @pyqtSlot(bool)
    def on_chkODPOBRPPGRF2_4_toggled(self, checked):
        isChecked = self.chkODPOBRPPGRF2_4.isChecked()
        if isChecked:
            self.chkODPOBRPPGRF1_4.setChecked(False)
            self.setProperty(QVariant(self.chkODPOBRPPGRF2_4.text()), u'ОД:ПОБ:РППГРФ:4')
        else:
            if not self.chkODPOBRPPGRF1_4.isChecked():
                self.setProperty(QVariant(), u'ОД:ПОБ:РППГРФ:4')


    @pyqtSlot(bool)
    def on_chkODPOBRPPGRF1_5_toggled(self, checked):
        isChecked = self.chkODPOBRPPGRF1_5.isChecked()
        if isChecked:
            self.chkODPOBRPPGRF2_5.setChecked(False)
            self.setProperty(QVariant(self.chkODPOBRPPGRF1_5.text()), u'ОД:ПОБ:РППГРФ:5')
        elif not self.chkODPOBRPPGRF2_5.isChecked():
            self.setProperty(QVariant(), u'ОД:ПОБ:РППГРФ:5')


    @pyqtSlot(bool)
    def on_chkODPOBRPPGRF2_5_toggled(self, checked):
        isChecked = self.chkODPOBRPPGRF2_5.isChecked()
        if isChecked:
            self.chkODPOBRPPGRF1_5.setChecked(False)
            self.setProperty(QVariant(self.chkODPOBRPPGRF2_5.text()), u'ОД:ПОБ:РППГРФ:5')
        else:
            if not self.chkODPOBRPPGRF1_5.isChecked():
                self.setProperty(QVariant(), u'ОД:ПОБ:РППГРФ:5')
####################################################################

    @pyqtSlot(bool)
    def on_chkODGOOSMZ1_toggled(self, checked):
        isChecked = self.chkODGOOSMZ1.isChecked()
        if isChecked:
            self.chkODGOOSMZ2.setChecked(False)
            self.setProperty(QVariant(self.chkODGOOSMZ1.text()), u'ОД:ГО:ОШМЗ:1')
            self.edtODGOOSMZ2Text.setText('')
        elif not self.chkODGOOSMZ2.isChecked():
            self.setProperty(QVariant(), u'ОД:ГО:ОШМЗ:1')
            self.edtODGOOSMZ2Text.setText('')


    @pyqtSlot(bool)
    def on_chkODGOOSMZ2_toggled(self, checked):
        isChecked = self.chkODGOOSMZ2.isChecked()
        if isChecked:
            self.chkODGOOSMZ1.setChecked(False)
            self.setProperty(QVariant(self.chkODGOOSMZ2.text()), u'ОД:ГО:ОШМЗ:1')
        else:
            if not self.chkODGOOSMZ1.isChecked():
                self.setProperty(QVariant(), u'ОД:ГО:ОШМЗ:1')
            self.edtODGOOSMZ2Text.setText('')


    @pyqtSlot(bool)
    def on_chkODGONPO1_toggled(self, checked):
        isChecked = self.chkODGONPO1.isChecked()
        if isChecked:
            self.chkODGONPO2.setChecked(False)
            self.setProperty(QVariant(self.chkODGONPO1.text()), u'ОД:ГО:ВИ:НПО:1')
            self.edtODGONPO2Text.setText('')
        else:
            if not self.chkODGONPO2.isChecked():
                self.setProperty(QVariant(), u'ОД:ГО:ВИ:НПО:1')
                self.edtODGONPO2Text.setText('')


    @pyqtSlot(bool)
    def on_chkODGONPO2_toggled(self, checked):
        isChecked = self.chkODGONPO2.isChecked()
        if isChecked:
            self.chkODGONPO1.setChecked(False)
            self.setProperty(QVariant(self.chkODGONPO2.text()), u'ОД:ГО:ВИ:НПО:1')
        else:
            if not self.chkODGONPO1.isChecked():
                self.setProperty(QVariant(), u'ОД:ГО:ВИ:НПО:1')
            self.edtODGONPO2Text.setText('')


    @pyqtSlot(bool)
    def on_chkODGOV1_toggled(self, checked):
        isChecked = self.chkODGOV1.isChecked()
        if isChecked:
            self.chkODGOV2.setChecked(False)
            self.setProperty(QVariant(self.chkODGOV1.text()), u'ОД:ГО:ВИ:В:1')
            self.edtODGOV2Text.setText('')
        else:
            if not self.chkODGOV2.isChecked():
                self.setProperty(QVariant(), u'ОД:ГО:ВИ:В:1')
                self.edtODGOV2Text.setText('')


    @pyqtSlot(bool)
    def on_chkODGOV2_toggled(self, checked):
        isChecked = self.chkODGOV2.isChecked()
        if isChecked:
            self.chkODGOV1.setChecked(False)
            self.setProperty(QVariant(self.chkODGOV2.text()), u'ОД:ГО:ВИ:В:1')
        else:
            if not self.chkODGOV1.isChecked():
                self.setProperty(QVariant(), u'ОД:ГО:ВИ:В:1')
            self.edtODGOV2Text.setText('')


    @pyqtSlot(bool)
    def on_chkODGOSM1_toggled(self, checked):
        isChecked = self.chkODGOSM1.isChecked()
        if isChecked:
            self.chkODGOSM2.setChecked(False)
            self.chkODGOSM3.setChecked(False)
            self.chkODGOSM4.setChecked(False)
            self.setProperty(QVariant(self.chkODGOSM1.text()), u'ОД:ГО:ВИ:ШМ:1')
        elif not self.chkODGOSM2.isChecked() and not self.chkODGOSM3.isChecked() and not self.chkODGOSM4.isChecked():
            self.setProperty(QVariant(), u'ОД:ГО:ВИ:ШМ:1')


    @pyqtSlot(bool)
    def on_chkODGOSM2_toggled(self, checked):
        isChecked = self.chkODGOSM2.isChecked()
        if isChecked:
            self.chkODGOSM1.setChecked(False)
            self.chkODGOSM3.setChecked(False)
            self.chkODGOSM4.setChecked(False)
            self.setProperty(QVariant(self.chkODGOSM2.text()), u'ОД:ГО:ВИ:ШМ:1')
        elif not self.chkODGOSM1.isChecked() and not self.chkODGOSM3.isChecked() and not self.chkODGOSM4.isChecked():
            self.setProperty(QVariant(), u'ОД:ГО:ВИ:ШМ:1')


    @pyqtSlot(bool)
    def on_chkODGOSM3_toggled(self, checked):
        isChecked = self.chkODGOSM3.isChecked()
        if isChecked:
            self.chkODGOSM2.setChecked(False)
            self.chkODGOSM1.setChecked(False)
            self.chkODGOSM4.setChecked(False)
            self.setProperty(QVariant(self.chkODGOSM3.text()), u'ОД:ГО:ВИ:ШМ:1')
        elif not self.chkODGOSM2.isChecked() and not self.chkODGOSM1.isChecked() and not self.chkODGOSM4.isChecked():
            self.setProperty(QVariant(), u'ОД:ГО:ВИ:ШМ:1')


    @pyqtSlot(bool)
    def on_chkODGOSM4_toggled(self, checked):
        isChecked = self.chkODGOSM4.isChecked()
        if not isChecked:
            self.edtODGODSMText.setText('')
        if isChecked:
            self.chkODGOSM2.setChecked(False)
            self.chkODGOSM3.setChecked(False)
            self.chkODGOSM1.setChecked(False)
            self.setProperty(QVariant(self.chkODGOSM4.text()), u'ОД:ГО:ВИ:ШМ:1')
        elif not self.chkODGOSM2.isChecked() and not self.chkODGOSM3.isChecked() and not self.chkODGOSM1.isChecked():
            self.setProperty(QVariant(), u'ОД:ГО:ВИ:ШМ:1')


    @pyqtSlot(bool)
    def on_chkODGOSMO1_toggled(self, checked):
        isChecked = self.chkODGOSMO1.isChecked()
        if isChecked:
            self.chkODGOSMO2.setChecked(False)
            self.chkODGOSMO3.setChecked(False)
            self.setProperty(QVariant(self.chkODGOSMO1.text()), u'ОД:ГО:ВИ:ШМ:4')
        elif not self.chkODGOSMO2.isChecked() and not self.chkODGOSMO3.isChecked():
            self.setProperty(QVariant(), u'ОД:ГО:ВИ:ШМ:4')


    @pyqtSlot(bool)
    def on_chkODGOSMO2_toggled(self, checked):
        isChecked = self.chkODGOSMO2.isChecked()
        if isChecked:
            self.chkODGOSMO1.setChecked(False)
            self.chkODGOSMO3.setChecked(False)
            self.setProperty(QVariant(self.chkODGOSMO2.text()), u'ОД:ГО:ВИ:ШМ:4')
        elif not self.chkODGOSMO1.isChecked() and not self.chkODGOSMO3.isChecked():
            self.setProperty(QVariant(), u'ОД:ГО:ВИ:ШМ:4')


    @pyqtSlot(bool)
    def on_chkODGOSMO3_toggled(self, checked):
        isChecked = self.chkODGOSMO3.isChecked()
        if isChecked:
            self.chkODGOSMO1.setChecked(False)
            self.chkODGOSMO2.setChecked(False)
            self.setProperty(QVariant(self.chkODGOSMO3.text()), u'ОД:ГО:ВИ:ШМ:4')
        elif not self.chkODGOSMO1.isChecked() and not self.chkODGOSMO2.isChecked():
            self.setProperty(QVariant(), u'ОД:ГО:ВИ:ШМ:4')


    @pyqtSlot(bool)
    def on_chkODGOZV1_toggled(self, checked):
        isChecked = self.chkODGOZV1.isChecked()
        if isChecked:
            self.chkODGOZV2.setChecked(False)
            self.chkODGOZV3.setChecked(False)
            self.setProperty(QVariant(self.chkODGOZV1.text()), u'ОД:ГО:ВИ:НЗ')
        elif not self.chkODGOZV2.isChecked() and not self.chkODGOZV3.isChecked():
            self.setProperty(QVariant(), u'ОД:ГО:ВИ:НЗ')


    @pyqtSlot(bool)
    def on_chkODGOZV2_toggled(self, checked):
        isChecked = self.chkODGOZV2.isChecked()
        if isChecked:
            self.chkODGOZV1.setChecked(False)
            self.chkODGOZV3.setChecked(False)
            self.setProperty(QVariant(self.chkODGOZV2.text()), u'ОД:ГО:ВИ:НЗ')
        elif not self.chkODGOZV1.isChecked() and not self.chkODGOZV3.isChecked():
            self.setProperty(QVariant(), u'ОД:ГО:ВИ:НЗ')


    @pyqtSlot(bool)
    def on_chkODGOZV3_toggled(self, checked):
        isChecked = self.chkODGOZV3.isChecked()
        if isChecked:
            self.chkODGOZV1.setChecked(False)
            self.chkODGOZV2.setChecked(False)
            self.setProperty(QVariant(self.chkODGOZV3.text()), u'ОД:ГО:ВИ:НЗ')
        elif not self.chkODGOZV1.isChecked() and not self.chkODGOZV2.isChecked():
            self.setProperty(QVariant(), u'ОД:ГО:ВИ:НЗ')


    @pyqtSlot(bool)
    def on_chkODGOTM1_toggled(self, checked):
        isChecked = self.chkODGOTM1.isChecked()
        if isChecked:
            self.chkODGOTM2.setChecked(False)
            self.setProperty(QVariant(self.chkODGOTM1.text()), u'ОД:ГО:ВИ:ТМ:1')
        elif not self.chkODGOTM2.isChecked():
            self.setProperty(QVariant(), u'ОД:ГО:ВИ:ТМ:1')
            if not self.chkODGOTM4.isChecked():
                self.edtODGOTM4Text.setText('')
        elif not self.chkODGOTM4.isChecked():
            self.edtODGOTM4Text.setText('')


    @pyqtSlot(bool)
    def on_chkODGOTM2_toggled(self, checked):
        isChecked = self.chkODGOTM2.isChecked()
        if isChecked:
            self.chkODGOTM1.setChecked(False)
            self.setProperty(QVariant(self.chkODGOTM2.text()), u'ОД:ГО:ВИ:ТМ:1')
        elif not self.chkODGOTM1.isChecked():
            self.setProperty(QVariant(), u'ОД:ГО:ВИ:ТМ:1')
            if not self.chkODGOTM4.isChecked():
                self.edtODGOTM4Text.setText('')
        elif not self.chkODGOTM4.isChecked():
            self.edtODGOTM4Text.setText('')


    @pyqtSlot(bool)
    def on_chkODGOTM3_toggled(self, checked):
        isChecked = self.chkODGOTM3.isChecked()
        if isChecked:
            self.chkODGOTM4.setChecked(False)
            self.setProperty(QVariant(self.chkODGOTM3.text()), u'ОД:ГО:ВИ:ТМ:2')
            self.edtODGOTM4Text.setText('')
        elif not self.chkODGOTM4.isChecked():
            self.setProperty(QVariant(), u'ОД:ГО:ВИ:ТМ:2')
            self.edtODGOTM4Text.setText('')


    @pyqtSlot(bool)
    def on_chkODGOTM4_toggled(self, checked):
        isChecked = self.chkODGOTM4.isChecked()
        if isChecked:
            self.chkODGOTM3.setChecked(False)
            self.setProperty(QVariant(self.chkODGOTM4.text()), u'ОД:ГО:ВИ:ТМ:2')
        else:
            if not self.chkODGOTM3.isChecked():
                self.setProperty(QVariant(), u'ОД:ГО:ВИ:ТМ:2')
            self.edtODGOTM4Text.setText('')


    @pyqtSlot(bool)
    def on_chkODGOPSL1_toggled(self, checked):
        isChecked = self.chkODGOPSL1.isChecked()
        if isChecked:
            self.chkODGOPSL2.setChecked(False)
            self.setProperty(QVariant(self.chkODGOPSL1.text()), u'ОД:ГО:ВИ:ПСл:1')
            self.edtODGOPSL2Text.setText('')
        elif not self.chkODGOPSL2.isChecked():
            self.setProperty(QVariant(), u'ОД:ГО:ВИ:ПСл:1')
            self.edtODGOPSL2Text.setText('')


    @pyqtSlot(bool)
    def on_chkODGOPSL2_toggled(self, checked):
        isChecked = self.chkODGOPSL2.isChecked()
        if isChecked:
            self.chkODGOPSL1.setChecked(False)
            self.setProperty(QVariant(self.chkODGOPSL2.text()), u'ОД:ГО:ВИ:ПСл:1')
        else:
            if not self.chkODGOPSL1.isChecked():
                self.setProperty(QVariant(), u'ОД:ГО:ВИ:ПСл:1')
            self.edtODGOPSL2Text.setText('')


    @pyqtSlot(bool)
    def on_chkODGOPSP1_toggled(self, checked):
        isChecked = self.chkODGOPSP1.isChecked()
        if isChecked:
            self.chkODGOPSP2.setChecked(False)
            self.setProperty(QVariant(self.chkODGOPSP1.text()), u'ОД:ГО:ВИ:ПСп:1')
            self.edtODGOPSP3Text.setText('')
        elif not self.chkODGOPSP2.isChecked():
            self.setProperty(QVariant(), u'ОД:ГО:ВИ:ПСп:1')
            self.edtODGOPSP3Text.setText('')


    @pyqtSlot(bool)
    def on_chkODGOPSP2_toggled(self, checked):
        isChecked = self.chkODGOPSP2.isChecked()
        if isChecked:
            self.chkODGOPSP1.setChecked(False)
            self.setProperty(QVariant(self.chkODGOPSP2.text()), u'ОД:ГО:ВИ:ПСп:1')
        else:
            if not self.chkODGOPSP1.isChecked():
                self.setProperty(QVariant(), u'ОД:ГО:ВИ:ПСп:1')
            self.edtODGOPSP3Text.setText('')


    @pyqtSlot(bool)
    def on_chkODGOE1_toggled(self, checked):
        isChecked = self.chkODGOE1.isChecked()
        if isChecked:
            self.chkODGOE2.setChecked(False)
            self.setProperty(QVariant(self.chkODGOE1.text()), u'ОД:ГО:ВИ:Э:1')
            self.edtODGOE2Text.setText('')
        elif not self.chkODGOE2.isChecked():
            self.setProperty(QVariant(), u'ОД:ГО:ВИ:Э:1')
            self.edtODGOE2Text.setText('')


    @pyqtSlot(bool)
    def on_chkODGOE2_toggled(self, checked):
        isChecked = self.chkODGOE2.isChecked()
        if isChecked:
            self.chkODGOE1.setChecked(False)
            self.setProperty(QVariant(self.chkODGOE2.text()), u'ОД:ГО:ВИ:Э:1')
        else:
            if not self.chkODGOE1.isChecked():
                self.setProperty(QVariant(), u'ОД:ГО:ВИ:Э:1')
            self.edtODGOE2Text.setText('')


    @pyqtSlot(bool)
    def on_chkSkinStatus1_toggled(self, checked):
        isChecked = self.chkSkinStatus1.isChecked()
        if isChecked:
            self.chkSkinStatus2.setChecked(False)
            self.setProperty(QVariant(self.chkSkinStatus1.text()), u'ОД:СКП:1')
            self.edtSkinStatus.setText('')
        elif not self.chkSkinStatus2.isChecked():
            self.setProperty(QVariant(), u'ОД:СКП:1')
            self.edtSkinStatus.setText('')


    @pyqtSlot(bool)
    def on_chkSkinStatus2_toggled(self, checked):
        isChecked = self.chkSkinStatus2.isChecked()
        if isChecked:
            self.chkSkinStatus1.setChecked(False)
            self.setProperty(QVariant(self.chkSkinStatus2.text()), u'ОД:СКП:1')
        else:
            if not self.chkSkinStatus1.isChecked():
                self.setProperty(QVariant(), u'ОД:СКП:1')
            self.edtSkinStatus.setText('')


    @pyqtSlot(bool)
    def on_chkSOPWPRNot_toggled(self, checked):
        isChecked = self.chkSOPWPRNot.isChecked()
        if isChecked:
            self.chkSOPWPRYes.setChecked(False)
            self.setProperty(QVariant(self.chkSOPWPRNot.text()), u'СОП:ВПР:1')
            self.edtSOPWPRText.setText('')
        elif not self.chkSOPWPRYes.isChecked():
            self.setProperty(QVariant(), u'СОП:ВПР:1')
            self.edtSOPWPRText.setText('')


    @pyqtSlot(bool)
    def on_chkSOPWPRYes_toggled(self, checked):
        isChecked = self.chkSOPWPRYes.isChecked()
        if isChecked:
            self.chkSOPWPRNot.setChecked(False)
            self.setProperty(QVariant(self.chkSOPWPRYes.text()), u'СОП:ВПР:1')
        else:
            if not self.chkSOPWPRNot.isChecked():
                self.setProperty(QVariant(), u'СОП:ВПР:1')
            self.edtSOPWPRText.setText('')


    @pyqtSlot(bool)
    def on_chkSOPDB1_toggled(self, checked):
        isChecked = self.chkSOPDB1.isChecked()
        if isChecked:
            self.chkSOPDB2.setChecked(False)
            self.setProperty(QVariant(self.chkSOPDB1.text()), u'СОП:ПЗ:ДИ:1')
            self.edtSOPDBText.setText('')
        elif not self.chkSOPDB2.isChecked():
            self.setProperty(QVariant(), u'СОП:ПЗ:ДИ:1')
            self.edtSOPDBText.setText('')


    @pyqtSlot(bool)
    def on_chkSOPDB2_toggled(self, checked):
        isChecked = self.chkSOPDB2.isChecked()
        if isChecked:
            self.chkSOPDB1.setChecked(False)
            self.setProperty(QVariant(self.chkSOPDB2.text()), u'СОП:ПЗ:ДИ:1')
        else:
            if not self.chkSOPDB1.isChecked():
                self.setProperty(QVariant(), u'СОП:ПЗ:ДИ:1')
            self.edtSOPDBText.setText('')


    @pyqtSlot(bool)
    def on_chkSOPSZ1_toggled(self, checked):
        isChecked = self.chkSOPSZ1.isChecked()
        if isChecked:
            self.chkSOPSZ2.setChecked(False)
            self.setProperty(QVariant(self.chkSOPSZ1.text()), u'СОП:ПЗ:СЗ:1')
            self.edtSOPSZText.setText('')
        elif not self.chkSOPSZ2.isChecked():
            self.setProperty(QVariant(), u'СОП:ПЗ:СЗ:1')
            self.edtSOPSZText.setText('')


    @pyqtSlot(bool)
    def on_chkSOPSZ2_toggled(self, checked):
        isChecked = self.chkSOPSZ2.isChecked()
        if isChecked:
            self.chkSOPSZ1.setChecked(False)
            self.setProperty(QVariant(self.chkSOPSZ2.text()), u'СОП:ПЗ:СЗ:1')
        else:
            if not self.chkSOPSZ1.isChecked():
                self.setProperty(QVariant(), u'СОП:ПЗ:СЗ:1')
            self.edtSOPSZText.setText('')


    @pyqtSlot(bool)
    def on_chkSOPDS1_toggled(self, checked):
        isChecked = self.chkSOPDS1.isChecked()
        if isChecked:
            self.chkSOPDS2.setChecked(False)
            self.setProperty(QVariant(self.chkSOPDS1.text()), u'СОП:ПЗ:НДУ:1')
            self.edtSOPDSText.setText('')
        elif not self.chkSOPDS2.isChecked():
            self.setProperty(QVariant(), u'СОП:ПЗ:НДУ:1')
            self.edtSOPDSText.setText('')


    @pyqtSlot(bool)
    def on_chkSOPDS2_toggled(self, checked):
        isChecked = self.chkSOPDS2.isChecked()
        if isChecked:
            self.chkSOPDS1.setChecked(False)
            self.setProperty(QVariant(self.chkSOPDS2.text()), u'СОП:ПЗ:НДУ:1')
        else:
            if not self.chkSOPDS1.isChecked():
                self.setProperty(QVariant(), u'СОП:ПЗ:НДУ:1')
            self.edtSOPDSText.setText('')


    @pyqtSlot(bool)
    def on_chkSOPDRS1_toggled(self, checked):
        isChecked = self.chkSOPDRS1.isChecked()
        if isChecked:
            self.chkSOPDRS2.setChecked(False)
            self.setProperty(QVariant(self.chkSOPDRS1.text()), u'СОП:ДР:2')
        elif not self.chkSOPDRS2.isChecked():
            self.setProperty(QVariant(), u'СОП:ДР:2')


    @pyqtSlot(bool)
    def on_chkSOPDRS2_toggled(self, checked):
        isChecked = self.chkSOPDRS2.isChecked()
        if isChecked:
            self.chkSOPDRS1.setChecked(False)
            self.setProperty(QVariant(self.chkSOPDRS2.text()), u'СОП:ДР:2')
        else:
            if not self.chkSOPDRS1.isChecked():
                self.setProperty(QVariant(), u'СОП:ДР:2')


    @pyqtSlot(bool)
    def on_chkSOPTRO1_toggled(self, checked):
        isChecked = self.chkSOPTRO1.isChecked()
        if isChecked:
            self.chkSOPTRO2.setChecked(False)
            self.setProperty(QVariant(self.chkSOPTRO1.text()), u'СОП:ПЗ:ТО:1')
            self.edtSOPTROText.setText('')
        elif not self.chkSOPTRO2.isChecked():
            self.setProperty(QVariant(), u'СОП:ПЗ:ТО:1')
            self.edtSOPTROText.setText('')


    @pyqtSlot(bool)
    def on_chkSOPTRO2_toggled(self, checked):
        isChecked = self.chkSOPTRO2.isChecked()
        if isChecked:
            self.chkSOPTRO1.setChecked(False)
            self.setProperty(QVariant(self.chkSOPTRO2.text()), u'СОП:ПЗ:ТО:1')
        else:
            if not self.chkSOPTRO1.isChecked():
                self.setProperty(QVariant(), u'СОП:ПЗ:ТО:1')
            self.edtSOPTROText.setText('')


    @pyqtSlot(bool)
    def on_chkSOPSZI1_toggled(self, checked):
        isChecked = self.chkSOPSZI1.isChecked()
        if isChecked:
            self.chkSOPSZI2.setChecked(False)
            self.chkSOPSZI3.setChecked(False)
            self.chkSOPSZI4.setChecked(False)
            self.chkSOPSZI5.setChecked(False)
            self.chkSOPSZI6.setChecked(False)
            self.chkSOPSZI7.setChecked(False)
            self.setProperty(QVariant(self.chkSOPSZI1.text()), u'СОП:ПЗ:СЗИ:1')
            self.edtSOPSZIText.setText('')
        elif not self.chkSOPSZI2.isChecked() and not self.chkSOPSZI3.isChecked() and not self.chkSOPSZI4.isChecked() and not self.chkSOPSZI5.isChecked() and not self.chkSOPSZI6.isChecked() and not self.chkSOPSZI7.isChecked():
            self.setProperty(QVariant(), u'СОП:ПЗ:СЗИ:1')
            self.edtSOPSZIText.setText('')
        elif not self.chkSOPSZI7.isChecked():
            self.setProperty(QVariant(), u'СОП:ПЗ:СЗИ:1')
            self.edtSOPSZIText.setText('')


    def addValuePropertyList(self, text, shortName):
        if shortName and text:
            value = unicode(text)
            valuePropertyList = []
            propertyValueStr = forceStringEx(self.getProperty(shortName))
            valuePropertyListTemp = propertyValueStr.split(u',')
            if value not in valuePropertyListTemp:
                valuePropertyList.append(value)
            if valuePropertyList:
                valuePropertyListTemp.extend(valuePropertyList)
            propertyValueStr = u','.join(valuePropertyListTemp)
            self.setProperty(QVariant(propertyValueStr), shortName)


    def deletedValuePropertyList(self, text, shortName):
        if shortName and text:
            value = unicode(text)
            propertyValueStr = forceStringEx(self.getProperty(shortName))
            valuePropertyList = []
            valuePropertyListTemp = propertyValueStr.split(u',')
            for valueProperty in valuePropertyListTemp:
                if value != valueProperty:
                    valuePropertyList.append(valueProperty)
            propertyValue = u','.join(valuePropertyList)
            self.setProperty(QVariant(propertyValue), shortName)


    @pyqtSlot(bool)
    def on_chkSOPSZI2_toggled(self, checked):
        isChecked = self.chkSOPSZI2.isChecked()
        if isChecked:
            self.chkSOPSZI1.setChecked(False)
            self.addValuePropertyList(self.chkSOPSZI2.text(), u'СОП:ПЗ:СЗИ:1')
        elif not self.chkSOPSZI1.isChecked() and not self.chkSOPSZI3.isChecked() and not self.chkSOPSZI4.isChecked() and not self.chkSOPSZI5.isChecked() and not self.chkSOPSZI6.isChecked() and not self.chkSOPSZI7.isChecked():
            self.setProperty(QVariant(), u'СОП:ПЗ:СЗИ:1')
            self.edtSOPSZIText.setText('')
        else:
            self.deletedValuePropertyList(self.chkSOPSZI2.text(), u'СОП:ПЗ:СЗИ:1')
            if not self.chkSOPSZI7.isChecked():
                self.edtSOPSZIText.setText('')


    @pyqtSlot(bool)
    def on_chkSOPSZI3_toggled(self, checked):
        isChecked = self.chkSOPSZI3.isChecked()
        if isChecked:
            self.chkSOPSZI1.setChecked(False)
            self.addValuePropertyList(self.chkSOPSZI3.text(), u'СОП:ПЗ:СЗИ:1')
        elif not self.chkSOPSZI1.isChecked() and not self.chkSOPSZI2.isChecked() and not self.chkSOPSZI4.isChecked() and not self.chkSOPSZI5.isChecked() and not self.chkSOPSZI6.isChecked() and not self.chkSOPSZI7.isChecked():
            self.setProperty(QVariant(), u'СОП:ПЗ:СЗИ:1')
            self.edtSOPSZIText.setText('')
        else:
            self.deletedValuePropertyList(self.chkSOPSZI3.text(), u'СОП:ПЗ:СЗИ:1')
            if not self.chkSOPSZI7.isChecked():
                self.edtSOPSZIText.setText('')


    @pyqtSlot(bool)
    def on_chkSOPSZI4_toggled(self, checked):
        isChecked = self.chkSOPSZI4.isChecked()
        if isChecked:
            self.chkSOPSZI1.setChecked(False)
            self.addValuePropertyList(self.chkSOPSZI4.text(), u'СОП:ПЗ:СЗИ:1')
        elif not self.chkSOPSZI1.isChecked() and not self.chkSOPSZI3.isChecked() and not self.chkSOPSZI2.isChecked() and not self.chkSOPSZI5.isChecked() and not self.chkSOPSZI6.isChecked() and not self.chkSOPSZI7.isChecked():
            self.setProperty(QVariant(), u'СОП:ПЗ:СЗИ:1')
            self.edtSOPSZIText.setText('')
        else:
            self.deletedValuePropertyList(self.chkSOPSZI4.text(), u'СОП:ПЗ:СЗИ:1')
            if not self.chkSOPSZI7.isChecked():
                self.edtSOPSZIText.setText('')


    @pyqtSlot(bool)
    def on_chkSOPSZI5_toggled(self, checked):
        isChecked = self.chkSOPSZI5.isChecked()
        if isChecked:
            self.chkSOPSZI1.setChecked(False)
            self.addValuePropertyList(self.chkSOPSZI5.text(), u'СОП:ПЗ:СЗИ:1')
        elif not self.chkSOPSZI1.isChecked() and not self.chkSOPSZI3.isChecked() and not self.chkSOPSZI4.isChecked() and not self.chkSOPSZI2.isChecked() and not self.chkSOPSZI6.isChecked() and not self.chkSOPSZI7.isChecked():
            self.setProperty(QVariant(), u'СОП:ПЗ:СЗИ:1')
            self.edtSOPSZIText.setText('')
        else:
            self.deletedValuePropertyList(self.chkSOPSZI5.text(), u'СОП:ПЗ:СЗИ:1')
            if not self.chkSOPSZI7.isChecked():
                self.edtSOPSZIText.setText('')


    @pyqtSlot(bool)
    def on_chkSOPSZI6_toggled(self, checked):
        isChecked = self.chkSOPSZI6.isChecked()
        if isChecked:
            self.chkSOPSZI1.setChecked(False)
            self.addValuePropertyList(self.chkSOPSZI6.text(), u'СОП:ПЗ:СЗИ:1')
        elif not self.chkSOPSZI1.isChecked() and not self.chkSOPSZI3.isChecked() and not self.chkSOPSZI4.isChecked() and not self.chkSOPSZI5.isChecked() and not self.chkSOPSZI2.isChecked() and not self.chkSOPSZI7.isChecked():
            self.setProperty(QVariant(), u'СОП:ПЗ:СЗИ:1')
            self.edtSOPSZIText.setText('')
        else:
            self.deletedValuePropertyList(self.chkSOPSZI6.text(), u'СОП:ПЗ:СЗИ:1')
            if not self.chkSOPSZI7.isChecked():
                self.edtSOPSZIText.setText('')


    @pyqtSlot(bool)
    def on_chkSOPSZI7_toggled(self, checked):
        isChecked = self.chkSOPSZI7.isChecked()
        if isChecked:
            self.chkSOPSZI1.setChecked(False)
            self.addValuePropertyList(self.chkSOPSZI7.text(), u'СОП:ПЗ:СЗИ:1')
        elif not self.chkSOPSZI1.isChecked() and not self.chkSOPSZI3.isChecked() and not self.chkSOPSZI4.isChecked() and not self.chkSOPSZI5.isChecked() and not self.chkSOPSZI6.isChecked() and not self.chkSOPSZI2.isChecked():
            self.setProperty(QVariant(), u'СОП:ПЗ:СЗИ:1')
            self.edtSOPSZIText.setText('')
        else:
            self.deletedValuePropertyList(self.chkSOPSZI7.text(), u'СОП:ПЗ:СЗИ:1')
            self.edtSOPSZIText.setText('')


    @pyqtSlot(bool)
    def on_chkSOPVSTATUS1_toggled(self, checked):
        isChecked = self.chkSOPVSTATUS1.isChecked()
        if isChecked:
            self.chkSOPVSTATUS2.setChecked(False)
            self.setProperty(QVariant(self.chkSOPVSTATUS1.text()), u'СОП:ПЗ:ВИЧ:1')
            self.edtSOPVSTATUSDate.setDate(QDate())
            self.edtSOPVSTATUSNumberText.setText('')
            self.edtSOPVSTATUSARVTText.setText('')
        elif not self.chkSOPVSTATUS2.isChecked():
            self.setProperty(QVariant(), u'СОП:ПЗ:ВИЧ:1')
            self.edtSOPVSTATUSDate.setDate(QDate())
            self.edtSOPVSTATUSNumberText.setText('')
            self.edtSOPVSTATUSARVTText.setText('')


    @pyqtSlot(bool)
    def on_chkSOPVSTATUS2_toggled(self, checked):
        isChecked = self.chkSOPVSTATUS2.isChecked()
        if isChecked:
            self.chkSOPVSTATUS1.setChecked(False)
            self.setProperty(QVariant(self.chkSOPVSTATUS2.text()), u'СОП:ПЗ:ВИЧ:1')
        else:
            if not self.chkSOPVSTATUS1.isChecked():
                self.setProperty(QVariant(), u'СОП:ПЗ:ВИЧ:1')
            self.edtSOPVSTATUSDate.setDate(QDate())
            self.edtSOPVSTATUSNumberText.setText('')
            self.edtSOPVSTATUSARVTText.setText('')


    @pyqtSlot(bool)
    def on_chkSOPGTR1_toggled(self, checked):
        isChecked = self.chkSOPGTR1.isChecked()
        if isChecked:
            self.chkSOPGTR2.setChecked(False)
            self.setProperty(QVariant(self.chkSOPGTR1.text()), u'СОП:ПЗ:Г:1')
            self.edtSOPGTRDate.setText('')
            self.edtSOPGTRComponent.setText('')
        elif not self.chkSOPGTR2.isChecked():
            self.setProperty(QVariant(), u'СОП:ПЗ:Г:1')
            self.edtSOPGTRDate.setText('')
            self.edtSOPGTRComponent.setText('')


    @pyqtSlot(bool)
    def on_chkSOPGTR2_toggled(self, checked):
        isChecked = self.chkSOPGTR2.isChecked()
        if isChecked:
            self.chkSOPGTR1.setChecked(False)
            self.setProperty(QVariant(self.chkSOPGTR2.text()), u'СОП:ПЗ:Г:1')
        else:
            if not self.chkSOPGTR1.isChecked():
                self.setProperty(QVariant(), u'СОП:ПЗ:Г:1')
            self.edtSOPGTRDate.setText('')
            self.edtSOPGTRComponent.setText('')


    @pyqtSlot(bool)
    def on_chkSOPNZ1_toggled(self, checked):
        isChecked = self.chkSOPNZ1.isChecked()
        if isChecked:
            self.chkSOPNZ2.setChecked(False)
            self.setProperty(QVariant(self.chkSOPNZ1.text()), u'СОП:ПЗ:НЗ:1')
            self.edtSOPNZText.setText('')
        elif not self.chkSOPNZ2.isChecked():
            self.setProperty(QVariant(), u'СОП:ПЗ:НЗ:1')
            self.edtSOPNZText.setText('')


    @pyqtSlot(bool)
    def on_chkSOPNZ2_toggled(self, checked):
        isChecked = self.chkSOPNZ2.isChecked()
        if isChecked:
            self.chkSOPNZ1.setChecked(False)
            self.setProperty(QVariant(self.chkSOPNZ2.text()), u'СОП:ПЗ:НЗ:1')
        else:
            if not self.chkSOPNZ1.isChecked():
                self.setProperty(QVariant(), u'СОП:ПЗ:НЗ:1')
            self.edtSOPNZText.setText('')


    @pyqtSlot(bool)
    def on_chkSOPPRW1_toggled(self, checked):
        isChecked = self.chkSOPPRW1.isChecked()
        if isChecked:
            self.chkSOPPRW2.setChecked(False)
            self.setProperty(QVariant(self.chkSOPPRW1.text()), u'СОП:ПВ:1')
            self.edtSOPPRWText.setText('')
        elif not self.chkSOPPRW2.isChecked():
            self.setProperty(QVariant(), u'СОП:ПВ:1')
            self.edtSOPPRWText.setText('')


    @pyqtSlot(bool)
    def on_chkSOPPRW2_toggled(self, checked):
        isChecked = self.chkSOPPRW2.isChecked()
        if isChecked:
            self.chkSOPPRW1.setChecked(False)
            self.setProperty(QVariant(self.chkSOPPRW2.text()), u'СОП:ПВ:1')
        else:
            if not self.chkSOPPRW1.isChecked():
                self.setProperty(QVariant(), u'СОП:ПВ:1')
            self.edtSOPPRWText.setText('')


    @pyqtSlot(bool)
    def on_chkSOPIPPP1_toggled(self, checked):
        isChecked = self.chkSOPIPPP1.isChecked()
        if isChecked:
            self.chkSOPIPPP2.setChecked(False)
            self.setProperty(QVariant(self.chkSOPIPPP1.text()), u'СОП:ИППП:1')
            self.edtSOPIPPPText.setText('')
        elif not self.chkSOPIPPP2.isChecked():
            self.setProperty(QVariant(), u'СОП:ИППП:1')
            self.edtSOPIPPPText.setText('')


    @pyqtSlot(bool)
    def on_chkSOPIPPP2_toggled(self, checked):
        isChecked = self.chkSOPIPPP2.isChecked()
        if isChecked:
            self.chkSOPIPPP1.setChecked(False)
            self.setProperty(QVariant(self.chkSOPIPPP2.text()), u'СОП:ИППП:1')
        else:
            if not self.chkSOPIPPP1.isChecked():
                self.setProperty(QVariant(), u'СОП:ИППП:1')
            self.edtSOPIPPPText.setText('')


    @pyqtSlot(bool)
    def on_chkSOPWP1_toggled(self, checked):
        isChecked = self.chkSOPWP1.isChecked()
        if isChecked:
            self.chkSOPWP2.setChecked(False)
            self.chkSOPWP7.setChecked(False)
            self.chkSOPWP11.setChecked(False)
            self.setProperty(QVariant(self.chkSOPWP1.text()), u'СОП:ВП:1')
        elif not self.chkSOPWP2.isChecked() and not self.chkSOPWP7.isChecked() and not self.chkSOPWP11.isChecked():
            self.setProperty(QVariant(), u'СОП:ВП:1')
        else:
            self.deletedValuePropertyList(self.chkSOPWP1.text(), u'СОП:ВП:1')


    @pyqtSlot(bool)
    def on_chkSOPWP2_toggled(self, checked):
        isChecked = self.chkSOPWP2.isChecked()
        if isChecked:
            self.chkSOPWP1.setChecked(False)
            self.addValuePropertyList(self.chkSOPWP2.text(), u'СОП:ВП:1')
        else:
            if not self.chkSOPWP1.isChecked() and not self.chkSOPWP7.isChecked() and not self.chkSOPWP11.isChecked():
                self.setProperty(QVariant(), u'СОП:ВП:1')
            else:
                self.deletedValuePropertyList(self.chkSOPWP2.text(), u'СОП:ВП:1')
            self.chkSOPWP3.setChecked(False)
            self.chkSOPWP4.setChecked(False)
            self.chkSOPWP5.setChecked(False)
            self.edtSOPWPText.setText('')


    @pyqtSlot(bool)
    def on_chkSOPWP3_toggled(self, checked):
        isChecked = self.chkSOPWP3.isChecked()
        if isChecked:
            self.setProperty(QVariant(self.chkSOPWP3.text()), u'СОП:ВП:2')
            self.chkSOPWP4.setChecked(False)
            self.chkSOPWP5.setChecked(False)
        elif not self.chkSOPWP4.isChecked() and not self.chkSOPWP5.isChecked():
            self.setProperty(QVariant(), u'СОП:ВП:2')


    @pyqtSlot(bool)
    def on_chkSOPWP4_toggled(self, checked):
        isChecked = self.chkSOPWP4.isChecked()
        if isChecked:
            self.setProperty(QVariant(self.chkSOPWP4.text()), u'СОП:ВП:2')
            self.chkSOPWP3.setChecked(False)
            self.chkSOPWP5.setChecked(False)
        elif not self.chkSOPWP3.isChecked() and not self.chkSOPWP5.isChecked():
            self.setProperty(QVariant(), u'СОП:ВП:2')


    @pyqtSlot(bool)
    def on_chkSOPWP5_toggled(self, checked):
        isChecked = self.chkSOPWP5.isChecked()
        if isChecked:
            self.setProperty(QVariant(self.chkSOPWP5.text()), u'СОП:ВП:2')
            self.chkSOPWP3.setChecked(False)
            self.chkSOPWP4.setChecked(False)
        elif not self.chkSOPWP3.isChecked() and not self.chkSOPWP4.isChecked():
            self.setProperty(QVariant(), u'СОП:ВП:2')


    @pyqtSlot(bool)
    def on_chkSOPWP8_toggled(self, checked):
        isChecked = self.chkSOPWP8.isChecked()
        if isChecked:
            self.setProperty(QVariant(self.chkSOPWP8.text()), u'СОП:ВП:4')
            self.chkSOPWP9.setChecked(False)
            self.chkSOPWP10.setChecked(False)
        elif not self.chkSOPWP9.isChecked() and not self.chkSOPWP10.isChecked():
            self.setProperty(QVariant(), u'СОП:ВП:4')


    @pyqtSlot(bool)
    def on_chkSOPWP9_toggled(self, checked):
        isChecked = self.chkSOPWP9.isChecked()
        if isChecked:
            self.setProperty(QVariant(self.chkSOPWP9.text()), u'СОП:ВП:4')
            self.chkSOPWP8.setChecked(False)
            self.chkSOPWP10.setChecked(False)
        elif not self.chkSOPWP8.isChecked() and not self.chkSOPWP10.isChecked():
            self.setProperty(QVariant(), u'СОП:ВП:4')


    @pyqtSlot(bool)
    def on_chkSOPWP10_toggled(self, checked):
        isChecked = self.chkSOPWP10.isChecked()
        if isChecked:
            self.setProperty(QVariant(self.chkSOPWP10.text()), u'СОП:ВП:4')
            self.chkSOPWP8.setChecked(False)
            self.chkSOPWP9.setChecked(False)
        elif not self.chkSOPWP8.isChecked() and not self.chkSOPWP9.isChecked():
            self.setProperty(QVariant(), u'СОП:ВП:4')


    @pyqtSlot(bool)
    def on_chkSOPWP7_toggled(self, checked):
        isChecked = self.chkSOPWP7.isChecked()
        if isChecked:
            self.chkSOPWP1.setChecked(False)
            self.addValuePropertyList(self.chkSOPWP7.text(), u'СОП:ВП:1')
        else:
            if not self.chkSOPWP1.isChecked() and not self.chkSOPWP2.isChecked() and not self.chkSOPWP11.isChecked():
                self.setProperty(QVariant(), u'СОП:ВП:1')
            else:
                self.deletedValuePropertyList(self.chkSOPWP7.text(), u'СОП:ВП:1')
            self.chkSOPWP8.setChecked(False)
            self.chkSOPWP9.setChecked(False)
            self.chkSOPWP10.setChecked(False)
            self.edtSOPWPText11.setText('')
            self.edtSOPWP.setValue(0)


    @pyqtSlot(bool)
    def on_chkSOPWP11_toggled(self, checked):
        isChecked = self.chkSOPWP11.isChecked()
        if isChecked:
            self.chkSOPWP1.setChecked(False)
            self.addValuePropertyList(self.chkSOPWP11.text(), u'СОП:ВП:1')
        else:
            if not self.chkSOPWP1.isChecked() and not self.chkSOPWP2.isChecked() and not self.chkSOPWP7.isChecked():
                self.setProperty(QVariant(), u'СОП:ВП:1')
            else:
                self.deletedValuePropertyList(self.chkSOPWP11.text(), u'СОП:ВП:1')
            self.edtSOPWPText12.setText('')


    @pyqtSlot(bool)
    def on_chkSOPMN1_toggled(self, checked):
        isChecked = self.chkSOPMN1.isChecked()
        if isChecked:
            self.chkSOPMN2.setChecked(False)
            self.setProperty(QVariant(self.chkSOPMN1.text()), u'СОП:Менстр:2')
            self.edtSOPMNText.setText('')
        else:
            if not self.chkSOPMN2.isChecked():
                self.setProperty(QVariant(), u'СОП:Менстр:2')
                self.label_215.setVisible(not isChecked)
                self.edtSOPMNText.setVisible(not isChecked)
                self.label_86.setVisible(not isChecked)
            self.edtSOPMN2.setValue(0)
            self.edtSOPMN3.setText('')


    @pyqtSlot(bool)
    def on_chkSOPMN2_toggled(self, checked):
        isChecked = self.chkSOPMN2.isChecked()
        if isChecked:
            self.chkSOPMN1.setChecked(False)
            self.setProperty(QVariant(self.chkSOPMN2.text()), u'СОП:Менстр:2')
        else:
            if not self.chkSOPMN1.isChecked():
                self.setProperty(QVariant(), u'СОП:Менстр:2')
                self.edtSOPMN2.setValue(0)
                self.edtSOPMN3.setText('')
            self.edtSOPMNText.setText('')


    @pyqtSlot(bool)
    def on_chkSOPMN3_toggled(self, checked):
        isChecked = self.chkSOPMN3.isChecked()
        if isChecked:
            self.chkSOPMN4.setChecked(False)
            self.chkSOPMN5.setChecked(False)
            self.setProperty(QVariant(self.chkSOPMN3.text()), u'СОП:Менстр:7')
        elif not self.chkSOPMN4.isChecked() and not self.chkSOPMN5.isChecked():
            self.setProperty(QVariant(), u'СОП:Менстр:7')


    @pyqtSlot(bool)
    def on_chkSOPMN4_toggled(self, checked):
        isChecked = self.chkSOPMN4.isChecked()
        if isChecked:
            self.chkSOPMN3.setChecked(False)
            self.chkSOPMN5.setChecked(False)
            self.setProperty(QVariant(self.chkSOPMN4.text()), u'СОП:Менстр:7')
        elif not self.chkSOPMN3.isChecked() and not self.chkSOPMN5.isChecked():
            self.setProperty(QVariant(), u'СОП:Менстр:7')


    @pyqtSlot(bool)
    def on_chkSOPMN5_toggled(self, checked):
        isChecked = self.chkSOPMN5.isChecked()
        if isChecked:
            self.chkSOPMN3.setChecked(False)
            self.chkSOPMN4.setChecked(False)
            self.setProperty(QVariant(self.chkSOPMN5.text()), u'СОП:Менстр:7')
        elif not self.chkSOPMN3.isChecked() and not self.chkSOPMN4.isChecked():
            self.setProperty(QVariant(), u'СОП:Менстр:7')


    @pyqtSlot(bool)
    def on_chkSOPMN6_toggled(self, checked):
        isChecked = self.chkSOPMN6.isChecked()
        if isChecked:
            self.chkSOPMN7.setChecked(False)
            self.setProperty(QVariant(self.chkSOPMN6.text()), u'СОП:Менстр:8')
        elif not self.chkSOPMN7.isChecked():
            self.setProperty(QVariant(), u'СОП:Менстр:8')


    @pyqtSlot(bool)
    def on_chkSOPMN7_toggled(self, checked):
        isChecked = self.chkSOPMN7.isChecked()
        if isChecked:
            self.chkSOPMN6.setChecked(False)
            self.setProperty(QVariant(self.chkSOPMN7.text()), u'СОП:Менстр:8')
        elif not self.chkSOPMN6.isChecked():
            self.setProperty(QVariant(), u'СОП:Менстр:8')


    @pyqtSlot(bool)
    def on_chkSOPMN8_toggled(self, checked):
        isChecked = self.chkSOPMN8.isChecked()
        if isChecked:
            self.chkSOPMN9.setChecked(False)
            self.setProperty(QVariant(self.chkSOPMN8.text()), u'СОП:Менстр:9')
        elif not self.chkSOPMN9.isChecked():
            self.setProperty(QVariant(), u'СОП:Менстр:9')


    @pyqtSlot(bool)
    def on_chkSOPMN9_toggled(self, checked):
        isChecked = self.chkSOPMN9.isChecked()
        if isChecked:
            self.chkSOPMN8.setChecked(False)
            self.setProperty(QVariant(self.chkSOPMN9.text()), u'СОП:Менстр:9')
        elif not self.chkSOPMN8.isChecked():
            self.setProperty(QVariant(), u'СОП:Менстр:9')


    @pyqtSlot(bool)
    def on_chkSOPSOPR1_toggled(self, checked):
        isChecked = self.chkSOPSOPR1.isChecked()
        if isChecked:
            self.addValuePropertyList(self.chkSOPSOPR1.text(), u'СОП:СОПр:1')
        else:
            self.deletedValuePropertyList(self.chkSOPSOPR1.text(), u'СОП:СОПр:1')
            self.edtSOPSOPR1Date.setDate(QDate())


    @pyqtSlot(bool)
    def on_chkSOPSOPR2_toggled(self, checked):
        isChecked = self.chkSOPSOPR2.isChecked()
        if isChecked:
            self.addValuePropertyList(self.chkSOPSOPR2.text(), u'СОП:СОПр:1')
        else:
            self.deletedValuePropertyList(self.chkSOPSOPR2.text(), u'СОП:СОПр:1')
            self.edtSOPSOPR2Date.setDate(QDate())


    @pyqtSlot(bool)
    def on_chkSOPSOPR3_toggled(self, checked):
        isChecked = self.chkSOPSOPR3.isChecked()
        if isChecked:
            self.addValuePropertyList(self.chkSOPSOPR3.text(), u'СОП:СОПр:1')
        else:
            self.deletedValuePropertyList(self.chkSOPSOPR3.text(), u'СОП:СОПр:1')
            self.edtSOPSOPR3Date.setDate(QDate())


    @pyqtSlot(bool)
    def on_chkSOPSOPR4_toggled(self, checked):
        isChecked = self.chkSOPSOPR4.isChecked()
        if isChecked:
            self.addValuePropertyList(self.chkSOPSOPR4.text(), u'СОП:СОПр:1')
        else:
            self.deletedValuePropertyList(self.chkSOPSOPR4.text(), u'СОП:СОПр:1')
            self.edtSOPSOPR4Date.setDate(QDate())


    @pyqtSlot(bool)
    def on_chkSOPSOPR5_toggled(self, checked):
        isChecked = self.chkSOPSOPR5.isChecked()
        if isChecked:
            self.addValuePropertyList(self.chkSOPSOPR5.text(), u'СОП:СОПр:1')
        else:
            self.deletedValuePropertyList(self.chkSOPSOPR5.text(), u'СОП:СОПр:1')
            self.edtSOPSOPR5Date.setDate(QDate())


    @pyqtSlot(bool)
    def on_chkSOPSOPR6_toggled(self, checked):
        isChecked = self.chkSOPSOPR6.isChecked()
        if isChecked:
            self.addValuePropertyList(self.chkSOPSOPR6.text(), u'СОП:СОПр:1')
        else:
            self.deletedValuePropertyList(self.chkSOPSOPR6.text(), u'СОП:СОПр:1')
            self.edtSOPSOPR6Date.setDate(QDate())


    @pyqtSlot(bool)
    def on_chkSOPSOPR7_toggled(self, checked):
        isChecked = self.chkSOPSOPR7.isChecked()
        if isChecked:
            self.addValuePropertyList(self.chkSOPSOPR7.text(), u'СОП:СОПр:1')
        else:
            self.deletedValuePropertyList(self.chkSOPSOPR7.text(), u'СОП:СОПр:1')
            self.edtSOPSOPR7Date.setDate(QDate())


    @pyqtSlot(bool)
    def on_chkSOPSOPR8_toggled(self, checked):
        isChecked = self.chkSOPSOPR8.isChecked()
        if isChecked:
            self.addValuePropertyList(self.chkSOPSOPR8.text(), u'СОП:СОПр:1')
        else:
            self.deletedValuePropertyList(self.chkSOPSOPR8.text(), u'СОП:СОПр:1')
            self.edtSOPSOPR8Date.setDate(QDate())


    @pyqtSlot(bool)
    def on_chkSOPSOPR9_toggled(self, checked):
        isChecked = self.chkSOPSOPR9.isChecked()
        if isChecked:
            self.addValuePropertyList(self.chkSOPSOPR9.text(), u'СОП:СОПр:1')
        else:
            self.deletedValuePropertyList(self.chkSOPSOPR9.text(), u'СОП:СОПр:1')
            self.edtSOPSOPR9Date.setDate(QDate())
            self.edtSOPSOPR9Text.setText('')


    @pyqtSlot(bool)
    def on_chkSOPOVP1_toggled(self, checked):
        isChecked = self.chkSOPOVP1.isChecked()
        if isChecked:
            self.chkSOPOVP2.setChecked(False)
            self.chkSOPOVP3.setChecked(False)
            self.chkSOPOVP4.setChecked(False)
            self.setProperty(QVariant(self.chkSOPOVP1.text()), u'СОП:СОР:ВП')
        elif not self.chkSOPOVP2.isChecked() and not self.chkSOPOVP3.isChecked() and not self.chkSOPOVP4.isChecked():
            self.setProperty(QVariant(), u'СОП:СОР:ВП')
        else:
            self.deletedValuePropertyList(self.chkSOPOVP1.text(), u'СОП:СОР:ВП')


    @pyqtSlot(bool)
    def on_chkSOPOVP2_toggled(self, checked):
        isChecked = self.chkSOPOVP2.isChecked()
        if isChecked:
            self.chkSOPOVP1.setChecked(False)
            self.addValuePropertyList(self.chkSOPOVP2.text(), u'СОП:СОР:ВП')
        elif not self.chkSOPOVP1.isChecked() and not self.chkSOPSZI3.isChecked() and not self.chkSOPSZI4.isChecked():
            self.setProperty(QVariant(), u'СОП:СОР:ВП')
        else:
            self.deletedValuePropertyList(self.chkSOPOVP2.text(), u'СОП:СОР:ВП')


    @pyqtSlot(bool)
    def on_chkSOPOVP3_toggled(self, checked):
        isChecked = self.chkSOPOVP3.isChecked()
        if isChecked:
            self.chkSOPOVP1.setChecked(False)
            self.addValuePropertyList(self.chkSOPOVP3.text(), u'СОП:СОР:ВП')
        elif not self.chkSOPOVP1.isChecked() and not self.chkSOPSZI2.isChecked() and not self.chkSOPSZI4.isChecked():
            self.setProperty(QVariant(), u'СОП:СОР:ВП')
        else:
            self.deletedValuePropertyList(self.chkSOPOVP3.text(), u'СОП:СОР:ВП')


    @pyqtSlot(bool)
    def on_chkSOPOVP4_toggled(self, checked):
        isChecked = self.chkSOPOVP4.isChecked()
        if isChecked:
            self.chkSOPOVP1.setChecked(False)
            self.addValuePropertyList(self.chkSOPOVP4.text(), u'СОП:СОР:ВП')
        elif not self.chkSOPOVP1.isChecked() and not self.chkSOPSZI3.isChecked() and not self.chkSOPSZI3.isChecked():
            self.setProperty(QVariant(), u'СОП:СОР:ВП')
        else:
            self.deletedValuePropertyList(self.chkSOPOVP4.text(), u'СОП:СОР:ВП')


    @pyqtSlot(bool)
    def on_chkSOPOXZ1_toggled(self, checked):
        isChecked = self.chkSOPOXZ1.isChecked()
        if isChecked:
            self.chkSOPOXZ2.setChecked(False)
            self.setProperty(QVariant(self.chkSOPOXZ1.text()), u'СОП:СОР:ХЗ:1')
            self.edtSOPOXZText.setText('')
        elif not self.chkSOPOXZ2.isChecked():
            self.setProperty(QVariant(), u'СОП:СОР:ХЗ:1')
            self.edtSOPOXZText.setText('')


    @pyqtSlot(bool)
    def on_chkSOPOXZ2_toggled(self, checked):
        isChecked = self.chkSOPOXZ2.isChecked()
        if isChecked:
            self.chkSOPOXZ1.setChecked(False)
            self.setProperty(QVariant(self.chkSOPOXZ2.text()), u'СОП:СОР:ХЗ:1')
        else:
            if not self.chkSOPOXZ1.isChecked():
                self.setProperty(QVariant(), u'СОП:СОР:ХЗ:1')
            self.edtSOPOXZText.setText('')


    @pyqtSlot(bool)
    def on_chkSOPOIPPP1_toggled(self, checked):
        isChecked = self.chkSOPOIPPP1.isChecked()
        if isChecked:
            self.chkSOPOIPPP2.setChecked(False)
            self.setProperty(QVariant(self.chkSOPOIPPP1.text()), u'СОП:СОР:ИППП:1')
            self.edtSOPOIPPPText.setText('')
        elif not self.chkSOPOIPPP2.isChecked():
            self.setProperty(QVariant(), u'СОП:СОР:ИППП:1')
            self.edtSOPOIPPPText.setText('')


    @pyqtSlot(bool)
    def on_chkSOPOIPPP2_toggled(self, checked):
        isChecked = self.chkSOPOIPPP2.isChecked()
        if isChecked:
            self.chkSOPOIPPP1.setChecked(False)
            self.setProperty(QVariant(self.chkSOPOIPPP2.text()), u'СОП:СОР:ИППП:1')
        else:
            if not self.chkSOPOIPPP1.isChecked():
                self.setProperty(QVariant(), u'СОП:СОР:ИППП:1')
            self.edtSOPOIPPPText.setText('')


    @pyqtSlot(bool)
    def on_chkSOPOSZI1_toggled(self, checked):
        isChecked = self.chkSOPOSZI1.isChecked()
        if isChecked:
            self.chkSOPOSZI2.setChecked(False)
            self.chkSOPOSZI3.setChecked(False)
            self.chkSOPOSZI4.setChecked(False)
            self.chkSOPOSZI5.setChecked(False)
            self.chkSOPOSZI6.setChecked(False)
            self.chkSOPOSZI7.setChecked(False)
            self.setProperty(QVariant(self.chkSOPOSZI1.text()), u'СОП:СОР:СЗП:1')
            self.edtSOPOSZIText.setText('')
        elif not self.chkSOPOSZI2.isChecked() and not self.chkSOPOSZI3.isChecked() and not self.chkSOPOSZI4.isChecked() and not self.chkSOPOSZI5.isChecked() and not self.chkSOPOSZI6.isChecked() and not self.chkSOPOSZI7.isChecked():
            self.setProperty(QVariant(), u'СОП:СОР:СЗП:1')
            self.edtSOPOSZIText.setText('')
        elif not self.chkSOPOSZI7.isChecked():
            self.setProperty(QVariant(), u'СОП:СОР:СЗП:1')
            self.edtSOPOSZIText.setText('')


    @pyqtSlot(bool)
    def on_chkSOPOSZI2_toggled(self, checked):
        isChecked = self.chkSOPOSZI2.isChecked()
        if isChecked:
            self.chkSOPOSZI1.setChecked(False)
            self.addValuePropertyList(self.chkSOPOSZI2.text(), u'СОП:СОР:СЗП:1')
        elif not self.chkSOPOSZI1.isChecked() and not self.chkSOPOSZI3.isChecked() and not self.chkSOPOSZI4.isChecked() and not self.chkSOPOSZI5.isChecked() and not self.chkSOPOSZI6.isChecked() and not self.chkSOPOSZI7.isChecked():
            self.setProperty(QVariant(), u'СОП:СОР:СЗП:1')
            self.edtSOPOSZIText.setText('')
        else:
            self.deletedValuePropertyList(self.chkSOPOSZI2.text(), u'СОП:СОР:СЗП:1')
            if not self.chkSOPOSZI7.isChecked():
                self.edtSOPOSZIText.setText('')


    @pyqtSlot(bool)
    def on_chkSOPOSZI3_toggled(self, checked):
        isChecked = self.chkSOPOSZI3.isChecked()
        if isChecked:
            self.chkSOPOSZI1.setChecked(False)
            self.addValuePropertyList(self.chkSOPOSZI3.text(), u'СОП:СОР:СЗП:1')
        elif not self.chkSOPOSZI1.isChecked() and not self.chkSOPOSZI2.isChecked() and not self.chkSOPOSZI4.isChecked() and not self.chkSOPOSZI5.isChecked() and not self.chkSOPOSZI6.isChecked() and not self.chkSOPOSZI7.isChecked():
            self.setProperty(QVariant(), u'СОП:СОР:СЗП:1')
            self.edtSOPOSZIText.setText('')
        else:
            self.deletedValuePropertyList(self.chkSOPOSZI3.text(), u'СОП:СОР:СЗП:1')
            if not self.chkSOPOSZI7.isChecked():
                self.edtSOPOSZIText.setText('')


    @pyqtSlot(bool)
    def on_chkSOPOSZI4_toggled(self, checked):
        isChecked = self.chkSOPOSZI4.isChecked()
        if isChecked:
            self.chkSOPOSZI1.setChecked(False)
            self.addValuePropertyList(self.chkSOPOSZI4.text(), u'СОП:СОР:СЗП:1')
        elif not self.chkSOPOSZI1.isChecked() and not self.chkSOPOSZI3.isChecked() and not self.chkSOPOSZI2.isChecked() and not self.chkSOPOSZI5.isChecked() and not self.chkSOPOSZI6.isChecked() and not self.chkSOPOSZI7.isChecked():
            self.setProperty(QVariant(), u'СОП:СОР:СЗП:1')
            self.edtSOPOSZIText.setText('')
        else:
            self.deletedValuePropertyList(self.chkSOPOSZI4.text(), u'СОП:СОР:СЗП:1')
            if not self.chkSOPOSZI7.isChecked():
                self.edtSOPOSZIText.setText('')


    @pyqtSlot(bool)
    def on_chkSOPOSZI5_toggled(self, checked):
        isChecked = self.chkSOPOSZI5.isChecked()
        if isChecked:
            self.chkSOPOSZI1.setChecked(False)
            self.addValuePropertyList(self.chkSOPOSZI5.text(), u'СОП:СОР:СЗП:1')
        elif not self.chkSOPOSZI1.isChecked() and not self.chkSOPOSZI3.isChecked() and not self.chkSOPOSZI4.isChecked() and not self.chkSOPOSZI2.isChecked() and not self.chkSOPOSZI6.isChecked() and not self.chkSOPOSZI7.isChecked():
            self.setProperty(QVariant(), u'СОП:СОР:СЗП:1')
            self.edtSOPOSZIText.setText('')
        else:
            self.deletedValuePropertyList(self.chkSOPOSZI5.text(), u'СОП:СОР:СЗП:1')
            if not self.chkSOPOSZI7.isChecked():
                self.edtSOPOSZIText.setText('')


    @pyqtSlot(bool)
    def on_chkSOPOSZI6_toggled(self, checked):
        isChecked = self.chkSOPOSZI6.isChecked()
        if isChecked:
            self.chkSOPOSZI1.setChecked(False)
            self.addValuePropertyList(self.chkSOPOSZI6.text(), u'СОП:СОР:СЗП:1')
        elif not self.chkSOPOSZI1.isChecked() and not self.chkSOPOSZI3.isChecked() and not self.chkSOPOSZI4.isChecked() and not self.chkSOPOSZI5.isChecked() and not self.chkSOPOSZI2.isChecked() and not self.chkSOPOSZI7.isChecked():
            self.setProperty(QVariant(), u'СОП:СОР:СЗП:1')
            self.edtSOPOSZIText.setText('')
        else:
            self.deletedValuePropertyList(self.chkSOPOSZI6.text(), u'СОП:СОР:СЗП:1')
            if not self.chkSOPOSZI7.isChecked():
                self.edtSOPOSZIText.setText('')


    @pyqtSlot(bool)
    def on_chkSOPOSZI7_toggled(self, checked):
        isChecked = self.chkSOPOSZI7.isChecked()
        if isChecked:
            self.chkSOPOSZI1.setChecked(False)
            self.addValuePropertyList(self.chkSOPOSZI7.text(), u'СОП:СОР:СЗП:1')
        elif not self.chkSOPOSZI1.isChecked() and not self.chkSOPOSZI3.isChecked() and not self.chkSOPOSZI4.isChecked() and not self.chkSOPOSZI5.isChecked() and not self.chkSOPOSZI6.isChecked() and not self.chkSOPOSZI2.isChecked():
            self.setProperty(QVariant(), u'СОП:СОР:СЗП:1')
            self.edtSOPOSZIText.setText('')
        else:
            self.deletedValuePropertyList(self.chkSOPOSZI7.text(), u'СОП:СОР:СЗП:1')
            if not self.chkSOPOSZI7.isChecked():
                self.edtSOPOSZIText.setText('')


    @pyqtSlot(bool)
    def on_chkSOPOSvOPR1_toggled(self, checked):
        isChecked = self.chkSOPOSvOPR1.isChecked()
        if isChecked:
            self.addValuePropertyList(self.chkSOPOSvOPR1.text(), u'СОП:СОР:СОПр')
        elif not self.chkSOPOSvOPR2.isChecked() and not self.chkSOPOSvOPR3.isChecked() and not self.chkSOPOSvOPR4.isChecked() and not self.chkSOPOSvOPR5.isChecked():
            self.setProperty(QVariant(), u'СОП:СОР:СОПр')
        else:
            self.deletedValuePropertyList(self.chkSOPOSvOPR1.text(), u'СОП:СОР:СОПр')


    @pyqtSlot(bool)
    def on_chkSOPOSvOPR2_toggled(self, checked):
        isChecked = self.chkSOPOSvOPR2.isChecked()
        if isChecked:
            self.addValuePropertyList(self.chkSOPOSvOPR2.text(), u'СОП:СОР:СОПр')
        elif not self.chkSOPOSvOPR1.isChecked() and not self.chkSOPOSvOPR3.isChecked() and not self.chkSOPOSvOPR4.isChecked() and not self.chkSOPOSvOPR5.isChecked():
            self.setProperty(QVariant(), u'СОП:СОР:СОПр')
        else:
            self.deletedValuePropertyList(self.chkSOPOSvOPR2.text(), u'СОП:СОР:СОПр')


    @pyqtSlot(bool)
    def on_chkSOPOSvOPR3_toggled(self, checked):
        isChecked = self.chkSOPOSvOPR3.isChecked()
        if isChecked:
            self.addValuePropertyList(self.chkSOPOSvOPR3.text(), u'СОП:СОР:СОПр')
        elif not self.chkSOPOSvOPR2.isChecked() and not self.chkSOPOSvOPR1.isChecked() and not self.chkSOPOSvOPR4.isChecked() and not self.chkSOPOSvOPR5.isChecked():
            self.setProperty(QVariant(), u'СОП:СОР:СОПр')
        else:
            self.deletedValuePropertyList(self.chkSOPOSvOPR3.text(), u'СОП:СОР:СОПр')


    @pyqtSlot(bool)
    def on_chkSOPOSvOPR4_toggled(self, checked):
        isChecked = self.chkSOPOSvOPR4.isChecked()
        if isChecked:
            self.addValuePropertyList(self.chkSOPOSvOPR4.text(), u'СОП:СОР:СОПр')
        elif not self.chkSOPOSvOPR2.isChecked() and not self.chkSOPOSvOPR3.isChecked() and not self.chkSOPOSvOPR1.isChecked() and not self.chkSOPOSvOPR5.isChecked():
            self.setProperty(QVariant(), u'СОП:СОР:СОПр')
        else:
            self.deletedValuePropertyList(self.chkSOPOSvOPR4.text(), u'СОП:СОР:СОПр')


    @pyqtSlot(bool)
    def on_chkSOPOSvOPR5_toggled(self, checked):
        isChecked = self.chkSOPOSvOPR5.isChecked()
        if isChecked:
            self.addValuePropertyList(self.chkSOPOSvOPR5.text(), u'СОП:СОР:СОПр')
        elif not self.chkSOPOSvOPR2.isChecked() and not self.chkSOPOSvOPR3.isChecked() and not self.chkSOPOSvOPR4.isChecked() and not self.chkSOPOSvOPR1.isChecked():
            self.setProperty(QVariant(), u'СОП:СОР:СОПр')
        else:
            self.deletedValuePropertyList(self.chkSOPOSvOPR5.text(), u'СОП:СОР:СОПр')


    @pyqtSlot(bool)
    def on_chkNVNBDG1_toggled(self, checked):
        isChecked = self.chkNVNBDG1.isChecked()
        if isChecked:
            self.chkNVNBDG2.setChecked(False)
            self.setProperty(QVariant(self.chkNVNBDG1.text()), u'НВНБ:ДГ:1')
            self.edtNVNBDG2Text.setText('')
        elif not self.chkNVNBDG2.isChecked():
            self.setProperty(QVariant(), u'НВНБ:ДГ:1')
            self.edtNVNBDG2Text.setText('')


    @pyqtSlot(bool)
    def on_chkNVNBDG2_toggled(self, checked):
        isChecked = self.chkNVNBDG2.isChecked()
        if isChecked:
            self.chkNVNBDG1.setChecked(False)
            self.setProperty(QVariant(self.chkNVNBDG2.text()), u'НВНБ:ДГ:1')
        else:
            if not self.chkNVNBDG1.isChecked():
                self.setProperty(QVariant(), u'НВНБ:ДГ:1')
            self.edtNVNBDG2Text.setText('')
            self.chkNVNBDGK1.setChecked(False)
            self.chkNVNBDGK2.setChecked(False)
            self.edtPreHospitalizationTermWeeks.setValue(0)


    @pyqtSlot(bool)
    def on_chkNVNBPNVNBPSR1_toggled(self, checked):
        isChecked = self.chkNVNBPNVNBPSR1.isChecked()
        if isChecked:
            self.chkNVNBPNVNBPSR2.setChecked(False)
            self.setProperty(QVariant(self.chkNVNBPNVNBPSR1.text()), u'НВНБ:ПСР')
        elif not self.chkNVNBPNVNBPSR2.isChecked():
            self.setProperty(QVariant(), u'НВНБ:ПСР')


    @pyqtSlot(bool)
    def on_chkNVNBPNVNBPSR2_toggled(self, checked):
        isChecked = self.chkNVNBPNVNBPSR2.isChecked()
        if isChecked:
            self.chkNVNBPNVNBPSR1.setChecked(False)
            self.setProperty(QVariant(self.chkNVNBPNVNBPSR2.text()), u'НВНБ:ПСР')
        else:
            if not self.chkNVNBPNVNBPSR1.isChecked():
                self.setProperty(QVariant(), u'НВНБ:ПСР')


    @pyqtSlot(bool)
    def on_chkNVNBPNVNBPrR1_toggled(self, checked):
        isChecked = self.chkNVNBPNVNBPrR1.isChecked()
        if isChecked:
            self.chkNVNBPNVNBPrR2.setChecked(False)
            self.setProperty(QVariant(self.chkNVNBPNVNBPrR1.text()), u'НВНБ:ПрР')
        elif not self.chkNVNBPNVNBPrR2.isChecked():
            self.setProperty(QVariant(), u'НВНБ:ПрР')


    @pyqtSlot(bool)
    def on_chkNVNBPNVNBPrR2_toggled(self, checked):
        isChecked = self.chkNVNBPNVNBPrR2.isChecked()
        if isChecked:
            self.chkNVNBPNVNBPrR1.setChecked(False)
            self.setProperty(QVariant(self.chkNVNBPNVNBPrR2.text()), u'НВНБ:ПрР')
        else:
            if not self.chkNVNBPNVNBPrR1.isChecked():
                self.setProperty(QVariant(), u'НВНБ:ПрР')


    @pyqtSlot(bool)
    def on_chkNVNBPNVNBSUG_toggled(self, checked):
        self.setProperty(QVariant(self.chkNVNBPNVNBSUG.isChecked()), u'НВНБ:СУЖ')


    @pyqtSlot(bool)
    def on_chkNVNBPNVNBOoG_toggled(self, checked):
        self.setProperty(QVariant(self.chkNVNBPNVNBOoG.isChecked()), u'НВНБ:ОоГ')


    @pyqtSlot(bool)
    def on_chkNVNBPNVNBNPkT_toggled(self, checked):
        self.setProperty(QVariant(self.chkNVNBPNVNBNPkT.isChecked()), u'НВНБ:НПкТ')


    @pyqtSlot(bool)
    def on_chkNVNBIBRM13_toggled(self, checked):
        self.frame_30.setVisible(checked)
        self.setProperty(QVariant(self.chkNVNBIBRM13.isChecked()), u'НВНБ:ИБРМ:15:1')


    @pyqtSlot(int)
    def on_cmbNVNBPNVNBUAS_currentIndexChanged(self,  val):
        self.setProperty(QVariant(forceStringEx(self.cmbNVNBPNVNBUAS.currentText())), u'НВНБ:УАС')


    @pyqtSlot(int)
    def on_cmbNVNBPNVNBMOdR_currentIndexChanged(self,  val):
        self.setProperty(QVariant(forceRef(self.cmbNVNBPNVNBMOdR.value())), u'НВНБ:МОдР')


    @pyqtSlot(int)
    def on_cmbNVNBPUDRP_currentIndexChanged(self,  val):
        self.setProperty(QVariant(forceRef(self.cmbNVNBPUDRP.value())), u'НВНБ:УД:РП:s')

    @pyqtSlot(int)
    def on_cmbNVNBPUDSM_currentIndexChanged(self,  val):
        self.setProperty(QVariant(forceRef(self.cmbNVNBPUDSM.value())), u'НВНБ:УД:СМ:s')

    @pyqtSlot(int)
    def on_cmbNVNBPUDSST_currentIndexChanged(self,  val):
        self.setProperty(QVariant(forceRef(self.cmbNVNBPUDSST.value())), u'НВНБ:УД:ССТ:s')

    @pyqtSlot(int)
    def on_cmbNVNBPUDFTB_currentIndexChanged(self,  val):
        self.setProperty(QVariant(forceRef(self.cmbNVNBPUDFTB.value())), u'НВНБ:УД:ФТБ:s')

    @pyqtSlot(int)
    def on_cmbNVNBPUDKOV_currentIndexChanged(self,  val):
        self.setProperty(QVariant(forceRef(self.cmbNVNBPUDKOV.value())), u'НВНБ:УД:КОВ:s')

    @pyqtSlot(int)
    def on_cmbNVNBPUDCA_currentIndexChanged(self,  val):
        self.setProperty(QVariant(forceRef(self.cmbNVNBPUDCA.value())), u'НВНБ:УД:СА:s')

    @pyqtSlot(int)
    def on_cmbNVNBIBRM_currentIndexChanged(self,  val):
        self.setProperty(QVariant(forceRef(self.cmbNVNBIBRM.value())), u'НВНБ:ИБРМ:1:s')
        rootParent = forceString(self.cmbNVNBIBRM.getRootTextForId(self.cmbNVNBIBRM.value()))
        if u'рождение' in rootParent.lower():
            self.chkNVNBIBRM2.setVisible(True)
            self.chkNVNBIBRM6.setVisible(True)
        else:
            self.chkNVNBIBRM2.setVisible(False)
            self.chkNVNBIBRM6.setVisible(False)
            self.chkNVNBIBRM7.setVisible(False)
            self.chkNVNBIBRM8.setVisible(False)
            self.chkNVNBIBRM2.setChecked(False)
            self.chkNVNBIBRM6.setChecked(False)
            self.chkNVNBIBRM7.setChecked(False)
            self.chkNVNBIBRM8.setChecked(False)
            
            

    @pyqtSlot(int)
    def on_cmbNVNBIBRP1_currentIndexChanged(self,  val):
        self.setProperty(QVariant(forceRef(self.cmbNVNBIBRP1.value())), u'НВНБ:ИБРП:1:1:1')

    @pyqtSlot(int)
    def on_cmbNVNBIBRP2_currentIndexChanged(self,  val):
        self.setProperty(QVariant(forceRef(self.cmbNVNBIBRP2.value())), u'НВНБ:ИБРП:2:1:1')

    @pyqtSlot(int)
    def on_cmbNVNBIBRP3_currentIndexChanged(self,  val):
        self.setProperty(QVariant(forceRef(self.cmbNVNBIBRP3.value())), u'НВНБ:ИБРП:3:1:1')

    @pyqtSlot(int)
    def on_cmbNVNBIBRP4_currentIndexChanged(self,  val):
        self.setProperty(QVariant(forceRef(self.cmbNVNBIBRP4.value())), u'НВНБ:ИБРП:4:1:1')

    @pyqtSlot(int)
    def on_cmbNVNBIBRP5_currentIndexChanged(self,  val):
        self.setProperty(QVariant(forceRef(self.cmbNVNBIBRP5.value())), u'НВНБ:ИБРП:5:1:1')


    @pyqtSlot(bool)
    def on_chkNVNBDGK1_toggled(self, checked):
        isChecked = self.chkNVNBDGK1.isChecked()
        if isChecked:
            self.chkNVNBDGK2.setChecked(False)
            self.setProperty(QVariant(self.chkNVNBDGK1.text()), u'НВНБ:ДГ:3')
            self.edtNVNBDGO.setText('')
        elif not self.chkNVNBDGK2.isChecked():
            self.setProperty(QVariant(), u'НВНБ:ДГ:3')
            self.edtNVNBDGO.setText('')


    @pyqtSlot(bool)
    def on_chkNVNBDGK2_toggled(self, checked):
        isChecked = self.chkNVNBDGK2.isChecked()
        if isChecked:
            self.chkNVNBDGK1.setChecked(False)
            self.setProperty(QVariant(self.chkNVNBDGK2.text()), u'НВНБ:ДГ:3')
        else:
            if not self.chkNVNBDGK1.isChecked():
                self.setProperty(QVariant(), u'НВНБ:ДГ:3')
            self.edtNVNBDGO.setText('')


    @pyqtSlot(bool)
    def on_chkNVNBPTNPkVB12_toggled(self, checked):
        self.setProperty(QVariant(self.chkNVNBPTNPkVB12.isChecked()), u'НВНБ:НПкВБ:12')


    @pyqtSlot(bool)
    def on_chkNVNBPTNPkVB20_toggled(self, checked):
        self.setProperty(QVariant(self.chkNVNBPTNPkVB20.isChecked()), u'НВНБ:НПкВБ:20')


    @pyqtSlot(bool)
    def on_chkNVNBIBRPPRP1_toggled(self, checked):
        isChecked = self.chkNVNBIBRPPRP1.isChecked()
        if isChecked:
            self.chkNVNBIBRPPRP2.setChecked(False)
            self.setProperty(QVariant(self.chkNVNBIBRPPRP1.text()), u'НВНБ:ИБРП:1:3')
        else:
            if not self.chkNVNBIBRPPRP2.isChecked():
                self.setProperty(QVariant(), u'НВНБ:ИБРП:1:3')


    @pyqtSlot(bool)
    def on_chkNVNBIBRPPRP2_toggled(self, checked):
        isChecked = self.chkNVNBIBRPPRP2.isChecked()
        if isChecked:
            self.chkNVNBIBRPPRP1.setChecked(False)
            self.setProperty(QVariant(self.chkNVNBIBRPPRP2.text()), u'НВНБ:ИБРП:1:3')
        else:
            if not self.chkNVNBIBRPPRP1.isChecked():
                self.setProperty(QVariant(), u'НВНБ:ИБРП:1:3')


    @pyqtSlot(bool)
    def on_chkNVNBIBRPPRP1_2_toggled(self, checked):
        isChecked = self.chkNVNBIBRPPRP1_2.isChecked()
        if isChecked:
            self.chkNVNBIBRPPRP2_2.setChecked(False)
            self.setProperty(QVariant(self.chkNVNBIBRPPRP1_2.text()), u'НВНБ:ИБРП:2:3')
        else:
            if not self.chkNVNBIBRPPRP2_2.isChecked():
                self.setProperty(QVariant(), u'НВНБ:ИБРП:2:3')


    @pyqtSlot(bool)
    def on_chkNVNBIBRPPRP2_2_toggled(self, checked):
        isChecked = self.chkNVNBIBRPPRP2_2.isChecked()
        if isChecked:
            self.chkNVNBIBRPPRP1_2.setChecked(False)
            self.setProperty(QVariant(self.chkNVNBIBRPPRP2_2.text()), u'НВНБ:ИБРП:2:3')
        else:
            if not self.chkNVNBIBRPPRP1_2.isChecked():
                self.setProperty(QVariant(), u'НВНБ:ИБРП:2:3')


    @pyqtSlot(bool)
    def on_chkNVNBIBRPPRP1_3_toggled(self, checked):
        isChecked = self.chkNVNBIBRPPRP1_3.isChecked()
        if isChecked:
            self.chkNVNBIBRPPRP2_3.setChecked(False)
            self.setProperty(QVariant(self.chkNVNBIBRPPRP1_3.text()), u'НВНБ:ИБРП:3:3')
        else:
            if not self.chkNVNBIBRPPRP2_3.isChecked():
                self.setProperty(QVariant(), u'НВНБ:ИБРП:3:3')


    @pyqtSlot(bool)
    def on_chkNVNBIBRPPRP2_3_toggled(self, checked):
        isChecked = self.chkNVNBIBRPPRP2_3.isChecked()
        if isChecked:
            self.chkNVNBIBRPPRP1_3.setChecked(False)
            self.setProperty(QVariant(self.chkNVNBIBRPPRP2_3.text()), u'НВНБ:ИБРП:3:3')
        else:
            if not self.chkNVNBIBRPPRP1_3.isChecked():
                self.setProperty(QVariant(), u'НВНБ:ИБРП:3:3')


    @pyqtSlot(bool)
    def on_chkNVNBIBRPPRP1_4_toggled(self, checked):
        isChecked = self.chkNVNBIBRPPRP1_4.isChecked()
        if isChecked:
            self.chkNVNBIBRPPRP2_4.setChecked(False)
            self.setProperty(QVariant(self.chkNVNBIBRPPRP1_4.text()), u'НВНБ:ИБРП:4:3')
        else:
            if not self.chkNVNBIBRPPRP2_4.isChecked():
                self.setProperty(QVariant(), u'НВНБ:ИБРП:4:3')


    @pyqtSlot(bool)
    def on_chkNVNBIBRPPRP2_4_toggled(self, checked):
        isChecked = self.chkNVNBIBRPPRP2_4.isChecked()
        if isChecked:
            self.chkNVNBIBRPPRP1_4.setChecked(False)
            self.setProperty(QVariant(self.chkNVNBIBRPPRP2_4.text()), u'НВНБ:ИБРП:4:3')
        else:
            if not self.chkNVNBIBRPPRP1_4.isChecked():
                self.setProperty(QVariant(), u'НВНБ:ИБРП:4:3')


    @pyqtSlot(bool)
    def on_chkNVNBIBRPPRP1_5_toggled(self, checked):
        isChecked = self.chkNVNBIBRPPRP1_5.isChecked()
        if isChecked:
            self.chkNVNBIBRPPRP2_5.setChecked(False)
            self.setProperty(QVariant(self.chkNVNBIBRPPRP1_5.text()), u'НВНБ:ИБРП:5:3')
        else:
            if not self.chkNVNBIBRPPRP2_5.isChecked():
                self.setProperty(QVariant(), u'НВНБ:ИБРП:5:3')


    @pyqtSlot(bool)
    def on_chkNVNBIBRPPRP2_5_toggled(self, checked):
        isChecked = self.chkNVNBIBRPPRP2_5.isChecked()
        if isChecked:
            self.chkNVNBIBRPPRP1_5.setChecked(False)
            self.setProperty(QVariant(self.chkNVNBIBRPPRP2_5.text()), u'НВНБ:ИБРП:5:3')
        else:
            if not self.chkNVNBIBRPPRP1_5.isChecked():
                self.setProperty(QVariant(), u'НВНБ:ИБРП:5:3')


    @pyqtSlot(bool)
    def on_chkNVNBIBRPD1_toggled(self, checked):
        isChecked = self.chkNVNBIBRPD1.isChecked()
        if isChecked:
            self.chkNVNBIBRPD2.setChecked(False)
            self.chkNVNBIBRPD3.setChecked(False)
            self.setProperty(QVariant(self.chkNVNBIBRPD1.text()), u'НВНБ:ИБРП:1:7')
        else:
            if not self.chkNVNBIBRPD2.isChecked() and not self.chkNVNBIBRPD3.isChecked():
                self.setProperty(QVariant(), u'НВНБ:ИБРП:1:7')


    @pyqtSlot(bool)
    def on_chkNVNBIBRPD2_toggled(self, checked):
        isChecked = self.chkNVNBIBRPD2.isChecked()
        if isChecked:
            self.chkNVNBIBRPD1.setChecked(False)
            self.chkNVNBIBRPD3.setChecked(False)
            self.setProperty(QVariant(self.chkNVNBIBRPD2.text()), u'НВНБ:ИБРП:1:7')
        else:
            if not self.chkNVNBIBRPD1.isChecked() and not self.chkNVNBIBRPD3.isChecked():
                self.setProperty(QVariant(), u'НВНБ:ИБРП:1:7')


    @pyqtSlot(bool)
    def on_chkNVNBIBRPD3_toggled(self, checked):
        isChecked = self.chkNVNBIBRPD3.isChecked()
        if isChecked:
            self.chkNVNBIBRPD2.setChecked(False)
            self.chkNVNBIBRPD1.setChecked(False)
            self.setProperty(QVariant(self.chkNVNBIBRPD3.text()), u'НВНБ:ИБРП:1:7')
        else:
            if not self.chkNVNBIBRPD2.isChecked() and not self.chkNVNBIBRPD1.isChecked():
                self.setProperty(QVariant(), u'НВНБ:ИБРП:1:7')


    @pyqtSlot(bool)
    def on_chkNVNBIBRPD1_2_toggled(self, checked):
        isChecked = self.chkNVNBIBRPD1_2.isChecked()
        if isChecked:
            self.chkNVNBIBRPD2_2.setChecked(False)
            self.chkNVNBIBRPD3_2.setChecked(False)
            self.setProperty(QVariant(self.chkNVNBIBRPD1_2.text()), u'НВНБ:ИБРП:2:7')
        else:
            if not self.chkNVNBIBRPD2_2.isChecked() and not self.chkNVNBIBRPD3_2.isChecked():
                self.setProperty(QVariant(), u'НВНБ:ИБРП:2:7')


    @pyqtSlot(bool)
    def on_chkNVNBIBRPD2_2_toggled(self, checked):
        isChecked = self.chkNVNBIBRPD2_2.isChecked()
        if isChecked:
            self.chkNVNBIBRPD1_2.setChecked(False)
            self.chkNVNBIBRPD3_2.setChecked(False)
            self.setProperty(QVariant(self.chkNVNBIBRPD2_2.text()), u'НВНБ:ИБРП:2:7')
        else:
            if not self.chkNVNBIBRPD1_2.isChecked() and not self.chkNVNBIBRPD3_2.isChecked():
                self.setProperty(QVariant(), u'НВНБ:ИБРП:2:7')


    @pyqtSlot(bool)
    def on_chkNVNBIBRPD3_2_toggled(self, checked):
        isChecked = self.chkNVNBIBRPD3_2.isChecked()
        if isChecked:
            self.chkNVNBIBRPD2_2.setChecked(False)
            self.chkNVNBIBRPD1_2.setChecked(False)
            self.setProperty(QVariant(self.chkNVNBIBRPD3_2.text()), u'НВНБ:ИБРП:2:7')
        else:
            if not self.chkNVNBIBRPD2_2.isChecked() and not self.chkNVNBIBRPD1_2.isChecked():
                self.setProperty(QVariant(), u'НВНБ:ИБРП:2:7')


    @pyqtSlot(bool)
    def on_chkNVNBIBRPD1_3_toggled(self, checked):
        isChecked = self.chkNVNBIBRPD1_3.isChecked()
        if isChecked:
            self.chkNVNBIBRPD2_3.setChecked(False)
            self.chkNVNBIBRPD3_3.setChecked(False)
            self.setProperty(QVariant(self.chkNVNBIBRPD1_3.text()), u'НВНБ:ИБРП:3:7')
        else:
            if not self.chkNVNBIBRPD2_3.isChecked() and not self.chkNVNBIBRPD3_3.isChecked():
                self.setProperty(QVariant(), u'НВНБ:ИБРП:3:7')


    @pyqtSlot(bool)
    def on_chkNVNBIBRPD2_3_toggled(self, checked):
        isChecked = self.chkNVNBIBRPD2_3.isChecked()
        if isChecked:
            self.chkNVNBIBRPD1_3.setChecked(False)
            self.chkNVNBIBRPD3_3.setChecked(False)
            self.setProperty(QVariant(self.chkNVNBIBRPD2_3.text()), u'НВНБ:ИБРП:3:7')
        else:
            if not self.chkNVNBIBRPD1_3.isChecked() and not self.chkNVNBIBRPD3_3.isChecked():
                self.setProperty(QVariant(), u'НВНБ:ИБРП:3:7')


    @pyqtSlot(bool)
    def on_chkNVNBIBRPD3_3_toggled(self, checked):
        isChecked = self.chkNVNBIBRPD3_3.isChecked()
        if isChecked:
            self.chkNVNBIBRPD2_3.setChecked(False)
            self.chkNVNBIBRPD1_3.setChecked(False)
            self.setProperty(QVariant(self.chkNVNBIBRPD3_3.text()), u'НВНБ:ИБРП:3:7')
        else:
            if not self.chkNVNBIBRPD2_3.isChecked() and not self.chkNVNBIBRPD1_3.isChecked():
                self.setProperty(QVariant(), u'НВНБ:ИБРП:3:7')


    @pyqtSlot(bool)
    def on_chkNVNBIBRPD1_4_toggled(self, checked):
        isChecked = self.chkNVNBIBRPD1_4.isChecked()
        if isChecked:
            self.chkNVNBIBRPD2_4.setChecked(False)
            self.chkNVNBIBRPD3_4.setChecked(False)
            self.setProperty(QVariant(self.chkNVNBIBRPD1_4.text()), u'НВНБ:ИБРП:4:7')
        else:
            if not self.chkNVNBIBRPD2_4.isChecked() and not self.chkNVNBIBRPD3_4.isChecked():
                self.setProperty(QVariant(), u'НВНБ:ИБРП:4:7')


    @pyqtSlot(bool)
    def on_chkNVNBIBRPD2_4_toggled(self, checked):
        isChecked = self.chkNVNBIBRPD2_4.isChecked()
        if isChecked:
            self.chkNVNBIBRPD1_4.setChecked(False)
            self.chkNVNBIBRPD3_4.setChecked(False)
            self.setProperty(QVariant(self.chkNVNBIBRPD2_4.text()), u'НВНБ:ИБРП:4:7')
        else:
            if not self.chkNVNBIBRPD1_4.isChecked() and not self.chkNVNBIBRPD3_4.isChecked():
                self.setProperty(QVariant(), u'НВНБ:ИБРП:4:7')


    @pyqtSlot(bool)
    def on_chkNVNBIBRPD3_4_toggled(self, checked):
        isChecked = self.chkNVNBIBRPD3_4.isChecked()
        if isChecked:
            self.chkNVNBIBRPD2_4.setChecked(False)
            self.chkNVNBIBRPD1_4.setChecked(False)
            self.setProperty(QVariant(self.chkNVNBIBRPD3_4.text()), u'НВНБ:ИБРП:4:7')
        else:
            if not self.chkNVNBIBRPD2_4.isChecked() and not self.chkNVNBIBRPD1_4.isChecked():
                self.setProperty(QVariant(), u'НВНБ:ИБРП:4:7')


    @pyqtSlot(bool)
    def on_chkNVNBIBRPD1_5_toggled(self, checked):
        isChecked = self.chkNVNBIBRPD1_5.isChecked()
        if isChecked:
            self.chkNVNBIBRPD2_5.setChecked(False)
            self.chkNVNBIBRPD3_5.setChecked(False)
            self.setProperty(QVariant(self.chkNVNBIBRPD1_5.text()), u'НВНБ:ИБРП:5:7')
        else:
            if not self.chkNVNBIBRPD2_5.isChecked() and not self.chkNVNBIBRPD3_5.isChecked():
                self.setProperty(QVariant(), u'НВНБ:ИБРП:5:7')


    @pyqtSlot(bool)
    def on_chkNVNBIBRPD2_5_toggled(self, checked):
        isChecked = self.chkNVNBIBRPD2_5.isChecked()
        if isChecked:
            self.chkNVNBIBRPD1_5.setChecked(False)
            self.chkNVNBIBRPD3_5.setChecked(False)
            self.setProperty(QVariant(self.chkNVNBIBRPD2_5.text()), u'НВНБ:ИБРП:5:7')
        else:
            if not self.chkNVNBIBRPD1_5.isChecked() and not self.chkNVNBIBRPD3_5.isChecked():
                self.setProperty(QVariant(), u'НВНБ:ИБРП:5:7')


    @pyqtSlot(bool)
    def on_chkNVNBIBRPD3_5_toggled(self, checked):
        isChecked = self.chkNVNBIBRPD3_5.isChecked()
        if isChecked:
            self.chkNVNBIBRPD2_5.setChecked(False)
            self.chkNVNBIBRPD1_5.setChecked(False)
            self.setProperty(QVariant(self.chkNVNBIBRPD3_5.text()), u'НВНБ:ИБРП:5:7')
        else:
            if not self.chkNVNBIBRPD2_5.isChecked() and not self.chkNVNBIBRPD1_5.isChecked():
                self.setProperty(QVariant(), u'НВНБ:ИБРП:5:7')


# ##################################################################


    @pyqtSlot(int)
    def on_cmbBloodGroupFather_currentIndexChanged(self, value):
        self.setProperty(QVariant(self.cmbBloodGroupFather.value()), u'ОД:ОДП:ГКО:1')


    @pyqtSlot()
    def on_btnNVNBPNVNBMOdR7_clicked(self):
        orgId = selectOrganisation(self, self.cmbNVNBPNVNBMOdR.value(), False, filter=self.cmbNVNBPNVNBMOdR.filter)
        self.cmbNVNBPNVNBMOdR.updateModel()
        if orgId:
            self.cmbNVNBPNVNBMOdR.setValue(orgId)


    @pyqtSlot(int)
    def on_cmbPrevOrganisation_currentIndexChanged(self,  val):
        self.setProperty(QVariant(forceStringEx(self.cmbPrevOrganisation.currentText())), u'ОД:ОДП:ТУПНП')


    @pyqtSlot(QDate)
    def on_edtBegDateMaternityLeave_dateChanged(self, date):
        self.setProperty(QVariant(self.edtBegDateMaternityLeave.date()), u'ОД:ОДП:ДО:1')


    @pyqtSlot(QDate)
    def on_edtEndDateMaternityLeave_dateChanged(self, date):
        self.setProperty(QVariant(self.edtEndDateMaternityLeave.date()), u'ОД:ОДП:ДО:2')


    @pyqtSlot(QDate)
    def on_edtGenericCertificateDate_dateChanged(self, date):
        self.setProperty(QVariant(self.edtGenericCertificateDate.date()), u'ОД:ОДП:РС:3')


    @pyqtSlot(QDate)
    def on_edtBloodGroupFatherDate_dateChanged(self, date):
        self.setProperty(QVariant(self.edtBloodGroupFatherDate.date()), u'ОД:ОДП:ГКО:2')


    @pyqtSlot(QDate)
    def on_edtAntiresusIgPrevPregnBegDate_dateChanged(self, date):
        self.setProperty(QVariant(self.edtAntiresusIgPrevPregnBegDate.date()), u'ОД:ОДП:ДАР:ППБ:1')


    @pyqtSlot(QDate)
    def on_edtAntiresusIgPrevPregnEndDate_dateChanged(self, date):
        self.setProperty(QVariant(self.edtAntiresusIgPrevPregnEndDate.date()), u'ОД:ОДП:ДАР:ППБ:2')


    @pyqtSlot(QDate)
    def on_edtAntiresusIgCurrPregnBegDate_dateChanged(self, date):
        self.setProperty(QVariant(self.edtAntiresusIgCurrPregnBegDate.date()), u'ОД:ОДП:ДАР:ПТБ:1')


    @pyqtSlot(QDate)
    def on_edtAntiresusIgCurrPregnEndDate_dateChanged(self, date):
        self.setProperty(QVariant(self.edtAntiresusIgCurrPregnEndDate.date()), u'ОД:ОДП:ДАР:ПТБ:2')


    @pyqtSlot(QDate)
    def on_edtFirstAppearanceTermDate_dateChanged(self, date):
        self.setProperty(QVariant(self.edtFirstAppearanceTermDate.date()), u'ОД:ОДП:ДПЯ')


    @pyqtSlot(QDate)
    def on_edtAppointDate_dateChanged(self, date):
        self.setProperty(QVariant(self.edtAppointDate.date()), u'ОД:ОДП:СПНУ:3')


    @pyqtSlot(QDate)
    def on_edtEstimatedBirthsDate_dateChanged(self, date):
        self.setProperty(QVariant(self.edtEstimatedBirthsDate.date()), u'ОД:ОДП:ПДР:1')


    @pyqtSlot(QDate)
    def on_edtExchangeAndNotificationCardClientDate_dateChanged(self, date):
        self.setProperty(QVariant(self.edtExchangeAndNotificationCardClientDate.date()), u'ОД:ОДП:ОУК:2')


    @pyqtSlot(QDate)
    def on_edtVRTDate_dateChanged(self, date):
        self.setProperty(QVariant(self.edtVRTDate.date()), u'ОД:СНБ:ВРТ:2')


    @pyqtSlot(QDate)
    def on_edtLastMenstruationDate_dateChanged(self, date):
        self.setProperty(QVariant(self.edtLastMenstruationDate.date()), u'ОД:СНБ:ПМ')


    @pyqtSlot(QDate)
    def on_edtFirstUSIDate_dateChanged(self, date):
        self.setProperty(QVariant(self.edtFirstUSIDate.date()), u'ОД:СНБ:ДУЗИ')


    @pyqtSlot(int)
    def on_edtFirstUSITermWeeks_valueChanged(self, value):
        self.setProperty(QVariant(self.edtFirstUSITermWeeks.value()), u'ОД:СНБ:ДУЗИ:Н')


    @pyqtSlot(int)
    def on_edtFirstUSITermDays_valueChanged(self, value):
        self.setProperty(QVariant(self.edtFirstUSITermDays.value()), u'ОД:СНБ:ДУЗИ:Д')


    @pyqtSlot(QDate)
    def on_edtFirstStirringFetusDate_dateChanged(self, date):
        self.setProperty(QVariant(self.edtFirstStirringFetusDate.date()), u'ОД:СНБ:ПШП')


    @pyqtSlot(QDate)
    def on_edtODPOBDO_dateChanged(self, date):
        self.setProperty(QVariant(self.edtODPOBDO.date()), u'ОД:ПОБ:ДО')


    @pyqtSlot(QDate)
    def on_edtODGODZ_dateChanged(self, date):
        self.setProperty(QVariant(self.edtODGODZ.date()), u'ОД:ГО:ВИ:ДЗ')


    @pyqtSlot(QDate)
    def on_edtSOPVSTATUSDate_dateChanged(self, date):
        self.setProperty(QVariant(self.edtSOPVSTATUSDate.date()), u'СОП:ПЗ:ВИЧ:2')


    @pyqtSlot(QDate)
    def on_edtSOPPFDate_dateChanged(self, date):
        self.setProperty(QVariant(self.edtSOPPFDate.date()), u'СОП:ПЗ:ПФ:1')


    @pyqtSlot(QDate)
    def on_edtSOPSOPR1Date_dateChanged(self, date):
        self.setProperty(QVariant(self.edtSOPSOPR1Date.date()), u'СОП:СОПр:2')


    @pyqtSlot(QDate)
    def on_edtSOPSOPR2Date_dateChanged(self, date):
        self.setProperty(QVariant(self.edtSOPSOPR2Date.date()), u'СОП:СОПр:3')


    @pyqtSlot(QDate)
    def on_edtSOPSOPR3Date_dateChanged(self, date):
        self.setProperty(QVariant(self.edtSOPSOPR3Date.date()), u'СОП:СОПр:4')


    @pyqtSlot(QDate)
    def on_edtSOPSOPR4Date_dateChanged(self, date):
        self.setProperty(QVariant(self.edtSOPSOPR4Date.date()), u'СОП:СОПр:5')


    @pyqtSlot(QDate)
    def on_edtSOPSOPR5Date_dateChanged(self, date):
        self.setProperty(QVariant(self.edtSOPSOPR5Date.date()), u'СОП:СОПр:6')


    @pyqtSlot(QDate)
    def on_edtSOPSOPR6Date_dateChanged(self, date):
        self.setProperty(QVariant(self.edtSOPSOPR6Date.date()), u'СОП:СОПр:7')


    @pyqtSlot(QDate)
    def on_edtSOPSOPR7Date_dateChanged(self, date):
        self.setProperty(QVariant(self.edtSOPSOPR7Date.date()), u'СОП:СОПр:8')


    @pyqtSlot(QDate)
    def on_edtSOPSOPR8Date_dateChanged(self, date):
        self.setProperty(QVariant(self.edtSOPSOPR8Date.date()), u'СОП:СОПр:9')


    @pyqtSlot(QDate)
    def on_edtSOPSOPR9Date_dateChanged(self, date):
        self.setProperty(QVariant(self.edtSOPSOPR9Date.date()), u'СОП:СОПр:11')


    @pyqtSlot(QDate)
    def on_edtSOPOPFDate_dateChanged(self, date):
        self.setProperty(QVariant(self.edtSOPOPFDate.date()), u'СОП:СОР:ПФ:1')


    @pyqtSlot(QDate)
    def on_edtNVNBDZ_dateChanged(self, date):
        self.setProperty(QVariant(self.edtNVNBDZ.date()), u'НВНБ:ДГ:5')


    @pyqtSlot(QDate)
    def on_edtNVNBP_dateChanged(self, date):
        self.setProperty(QVariant(self.edtNVNBP.date()), u'НВНБ:Пелв:11')


    @pyqtSlot(QDate)
    def on_edtNVNBIBRM13Date_dateChanged(self, date):
        self.setProperty(QVariant(QDateTime(self.edtNVNBIBRM13Date.date(), self.edtNVNBIBRM13Time.time())), u'НВНБ:ИБРМ:15')


    @pyqtSlot(QTime)
    def on_edtNVNBIBRM13Time_timeChanged(self, time):
        self.setProperty(QVariant(QDateTime(self.edtNVNBIBRM13Date.date(), self.edtNVNBIBRM13Time.time())), u'НВНБ:ИБРМ:15')


    @pyqtSlot(QDate)
    def on_edtNVNBIBRMResultDate_dateChanged(self, date):
        self.setProperty(QVariant(QDate(self.edtNVNBIBRMResultDate.date())), u'НВНБ:ИБРМ:17')
        
    
    @pyqtSlot(int) 
    def on_edtNVNBIBRMResultDateWeeks_valueChanged(self, value):
        self.setProperty(QVariant(self.edtNVNBIBRMResultDateWeeks.value()), u'НВНБ:ИБРМ:1:1')
        
    
    @pyqtSlot(int) 
    def on_edtNVNBIBRMResultDateDays_valueChanged(self, value):
        self.setProperty(QVariant(self.edtNVNBIBRMResultDateDays.value()), u'НВНБ:ИБРМ:1:2')


    @pyqtSlot(QDate)
    def on_edtNVNBDZKDate_dateChanged(self, date):
        if self.recordEvent:
            self.recordEvent.setValue('execDate', QVariant(self.edtNVNBDZKDate.date()))
            if date:
                if self.cmbStatus.value() != CActionStatus.withoutResult:
                    self.cmbStatus.setValue(CActionStatus.finished)
                if QtGui.qApp.userId and QtGui.qApp.userSpecialityId:
                    self.cmbPerson.setValue(QtGui.qApp.userId)
                elif not self.cmbPerson.value():
                    self.cmbPerson.setValue(self.cmbSetPerson.value())
        if date and date.isValid():
            self.lblCloseReason.setVisible(True)
            self.edtCloseReason.setVisible(True)
        else:
            self.lblCloseReason.setVisible(False)
            self.edtCloseReason.setVisible(False)    
            self.edtCloseReason.setText('')


    @pyqtSlot(int)
    def on_edtPregnancyByAccount_valueChanged(self, value):
        self.setProperty(QVariant(self.edtPregnancyByAccount.value()), u'ОД:ОДП:ДБпС')


    @pyqtSlot(int)
    def on_edtBirthsByAccount_valueChanged(self, value):
        self.setProperty(QVariant(self.edtBirthsByAccount.value()), u'ОД:ОДП:ДРпС')


    @pyqtSlot(int)
    def on_edtNVNBIBRPO1_1_valueChanged(self, value):
        self.setProperty(QVariant(self.edtNVNBIBRPO1_1.value()), u'НВНБ:ИБРП:1:6:1')


    @pyqtSlot(int)
    def on_edtNVNBIBRPO1_2_valueChanged(self, value):
        self.setProperty(QVariant(self.edtNVNBIBRPO1_2.value()), u'НВНБ:ИБРП:2:6:1')


    @pyqtSlot(int)
    def on_edtNVNBIBRPO1_3_valueChanged(self, value):
        self.setProperty(QVariant(self.edtNVNBIBRPO1_3.value()), u'НВНБ:ИБРП:3:6:1')


    @pyqtSlot(int)
    def on_edtNVNBIBRPO1_4_valueChanged(self, value):
        self.setProperty(QVariant(self.edtNVNBIBRPO1_4.value()), u'НВНБ:ИБРП:4:6:1')


    @pyqtSlot(int)
    def on_edtNVNBIBRPO1_5_valueChanged(self, value):
        self.setProperty(QVariant(self.edtNVNBIBRPO1_5.value()), u'НВНБ:ИБРП:5:6:1')


    @pyqtSlot(int)
    def on_edtNVNBIBRPO5_1_valueChanged(self, value):
        self.setProperty(QVariant(self.edtNVNBIBRPO5_1.value()), u'НВНБ:ИБРП:1:6:2')


    @pyqtSlot(int)
    def on_edtNVNBIBRPO5_2_valueChanged(self, value):
        self.setProperty(QVariant(self.edtNVNBIBRPO5_2.value()), u'НВНБ:ИБРП:2:6:2')

    @pyqtSlot(int)
    def on_edtNVNBIBRPO5_3_valueChanged(self, value):
        self.setProperty(QVariant(self.edtNVNBIBRPO5_3.value()), u'НВНБ:ИБРП:3:6:2')


    @pyqtSlot(int)
    def on_edtNVNBIBRPO5_4_valueChanged(self, value):
        self.setProperty(QVariant(self.edtNVNBIBRPO5_4.value()), u'НВНБ:ИБРП:4:6:2')


    @pyqtSlot(int)
    def on_edtNVNBIBRPO5_5_valueChanged(self, value):
        self.setProperty(QVariant(self.edtNVNBIBRPO5_5.value()), u'НВНБ:ИБРП:5:6:2')


    @pyqtSlot(int)
    def on_edtFirstAppearanceTerm_valueChanged(self, value):
        self.setProperty(QVariant(self.edtFirstAppearanceTerm.value()), u'ОД:ОДП:СПЯ')


    @pyqtSlot(int)
    def on_edtFirstAppearanceTermDays_valueChanged(self, value):
        self.setProperty(QVariant(self.edtFirstAppearanceTermDays.value()), u'ОД:ОДП:СПЯД')


    @pyqtSlot(int)
    def on_edtAppointTermWeeks_valueChanged(self, value):
        self.setProperty(QVariant(self.edtAppointTermWeeks.value()), u'ОД:ОДП:СПНУ:1')


    @pyqtSlot(int)
    def on_edtPreHospitalizationTermWeeks_valueChanged(self, value):
        value = self.edtPreHospitalizationTermWeeks.value()
        if not value:
            value = None
        self.setProperty(QVariant(value), u'ОД:ОДП:ДГ:6')


    @pyqtSlot(int)
    def on_edtAppointTermDays_valueChanged(self, value):
        self.setProperty(QVariant(self.edtAppointTermDays.value()), u'ОД:ОДП:СПНУ:2')


    @pyqtSlot(int)
    def on_edtEstimatedTermDate_valueChanged(self, value):
        self.setProperty(QVariant(self.edtEstimatedTermDate.value()), u'ОД:ОДП:ПДР:2')


    @pyqtSlot(int)
    def on_edtEstimatedWeight_1_valueChanged(self, value):
        value = self.edtEstimatedWeight_1.value()
        if not value:
            value = None
        self.setProperty(QVariant(value), u'ОД:ПОБ:ПМ:1')


    @pyqtSlot(int)
    def on_edtEstimatedWeight_2_valueChanged(self, value):
        value = self.edtEstimatedWeight_2.value()
        if not value:
            value = None
        self.setProperty(QVariant(value), u'ОД:ПОБ:ПМ:2')


    @pyqtSlot(int)
    def on_edtEstimatedWeight_3_valueChanged(self, value):
        value = self.edtEstimatedWeight_3.value()
        if not value:
            value = None
        self.setProperty(QVariant(value), u'ОД:ПОБ:ПМ:3')


    @pyqtSlot(int)
    def on_edtEstimatedWeight_4_valueChanged(self, value):
        value = self.edtEstimatedWeight_4.value()
        if not value:
            value = None
        self.setProperty(QVariant(value), u'ОД:ПОБ:ПМ:4')


    @pyqtSlot(int)
    def on_edtEstimatedWeight_5_valueChanged(self, value):
        value = self.edtEstimatedWeight_5.value()
        if not value:
            value = None
        self.setProperty(QVariant(value), u'ОД:ПОБ:ПМ:5')


    @pyqtSlot(int)
    def on_edtVRTNumber_valueChanged(self, value):
        self.setProperty(QVariant(self.edtVRTNumber.value()), u'ОД:СНБ:ВРТ:1')


    @pyqtSlot(int)
    def on_edtEmbryosCount_valueChanged(self, value):
        self.setProperty(QVariant(self.edtEmbryosCount.value()), u'ОД:СНБ:ВРТ:4')


    @pyqtSlot(int)
    def on_edtAgePatientCryopreservedDate_valueChanged(self, value):
        self.setProperty(QVariant(self.edtAgePatientCryopreservedDate.value()), u'ОД:СНБ:ВРТ:5')


    @pyqtSlot(int)
    def on_edtFetusCount_valueChanged(self, value):
        self.setProperty(QVariant(self.edtFetusCount.value()), u'ОД:СНБ:Б:2')
        if self.edtFetusCount.value() == 0:
            self.setFetusFrameVisible(self.frame_40, False)
            self.setFetusFrameVisible(self.frame_41, False)
            self.setFetusFrameVisible(self.frame_42, False)
            self.setFetusFrameVisible(self.frame_43, False)
        elif self.edtFetusCount.value() == 1:
            self.setFetusFrameVisible(self.frame_40, False)
            self.setFetusFrameVisible(self.frame_41, False)
            self.setFetusFrameVisible(self.frame_42, False)
            self.setFetusFrameVisible(self.frame_43, False)
        elif self.edtFetusCount.value() == 2:
            self.setFetusFrameVisible(self.frame_40, True)
            self.setFetusFrameVisible(self.frame_41, False)
            self.setFetusFrameVisible(self.frame_42, False)
            self.setFetusFrameVisible(self.frame_43, False)
        elif self.edtFetusCount.value() == 3:
            self.setFetusFrameVisible(self.frame_40, True)
            self.setFetusFrameVisible(self.frame_41, True)
            self.setFetusFrameVisible(self.frame_42, False)
            self.setFetusFrameVisible(self.frame_43, False)
        elif self.edtFetusCount.value() == 4:
            self.setFetusFrameVisible(self.frame_40, True)
            self.setFetusFrameVisible(self.frame_41, True)
            self.setFetusFrameVisible(self.frame_42, True)
            self.setFetusFrameVisible(self.frame_43, False)
        elif self.edtFetusCount.value() == 5:
            self.setFetusFrameVisible(self.frame_40, True)
            self.setFetusFrameVisible(self.frame_41, True)
            self.setFetusFrameVisible(self.frame_42, True)
            self.setFetusFrameVisible(self.frame_43, True)
    
    
    def setFetusFrameVisible(self, frame, visible):
        frameWidgets = {
            self.frame_40: [self.edtODPOBSBP_2, self.chkODPOBGCH1_2, self.chkODPOBGCH2_2, self.cmbODPOBNVMTO_2, self.cmbODPOBPP_2, self.chkODPOBRPPGRF1_2, self.chkODPOBRPPGRF2_2, self.cmbODPOBCZVRP_2, self.chkODPOBMT1_2, self.chkODPOBMT2_2, self.chkODPOBSBPR1_2, self.chkODPOBSBPR2_2, self.chkODPOBSBPR3_2, self.edtODPOBSBPR_2, self.edtEstimatedWeight_2],
            self.frame_41: [self.edtODPOBSBP_3, self.chkODPOBGCH1_3, self.chkODPOBGCH2_3, self.cmbODPOBNVMTO_3, self.cmbODPOBPP_3, self.chkODPOBRPPGRF1_3, self.chkODPOBRPPGRF2_3, self.cmbODPOBCZVRP_3, self.chkODPOBMT1_3, self.chkODPOBMT2_3, self.chkODPOBSBPR1_3, self.chkODPOBSBPR2_3, self.chkODPOBSBPR3_3, self.edtODPOBSBPR_3, self.edtEstimatedWeight_3],
            self.frame_42: [self.edtODPOBSBP_4, self.chkODPOBGCH1_4, self.chkODPOBGCH2_4, self.cmbODPOBNVMTO_4, self.cmbODPOBPP_4, self.chkODPOBRPPGRF1_4, self.chkODPOBRPPGRF2_4, self.cmbODPOBCZVRP_4, self.chkODPOBMT1_4, self.chkODPOBMT2_4, self.chkODPOBSBPR1_4, self.chkODPOBSBPR2_4, self.chkODPOBSBPR3_4, self.edtODPOBSBPR_4, self.edtEstimatedWeight_4],
            self.frame_43: [self.edtODPOBSBP_5, self.chkODPOBGCH1_5, self.chkODPOBGCH2_5, self.cmbODPOBNVMTO_5, self.cmbODPOBPP_5, self.chkODPOBRPPGRF1_5, self.chkODPOBRPPGRF2_5, self.cmbODPOBCZVRP_5, self.chkODPOBMT1_5, self.chkODPOBMT2_5, self.chkODPOBSBPR1_5, self.chkODPOBSBPR2_5, self.chkODPOBSBPR3_5, self.edtODPOBSBPR_5, self.edtEstimatedWeight_5],
            self.frame_31: [self.edtNVNBIBRPUV, self.edtNVNBIBRPPRPD, self.chkNVNBIBRPD1, self.chkNVNBIBRPD2, self.chkNVNBIBRPD3, self.edtNVNBIBRPZMKB1, self.edtNVNBIBRPZMKB2, self.chkNVNBIBRPPRP1, self.chkNVNBIBRPPRP2, self.edtNVNBIBRPPRP, self.cmbNVNBIBRP1, self.edtNVNBIBRPO1_1, self.edtNVNBIBRPO5_1],
            self.frame_33: [self.edtNVNBIBRPUV_2, self.edtNVNBIBRPPRPD_2, self.chkNVNBIBRPD1_2, self.chkNVNBIBRPD2_2, self.chkNVNBIBRPD3_2, self.edtNVNBIBRPZMKB1_2, self.edtNVNBIBRPZMKB2_2, self.chkNVNBIBRPPRP1_2, self.chkNVNBIBRPPRP2_2, self.edtNVNBIBRPPRP_2, self.cmbNVNBIBRP2, self.edtNVNBIBRPO1_2, self.edtNVNBIBRPO5_2],
            self.frame_34: [self.edtNVNBIBRPUV_3, self.edtNVNBIBRPPRPD_3, self.chkNVNBIBRPD1_3, self.chkNVNBIBRPD2_3, self.chkNVNBIBRPD3_3, self.edtNVNBIBRPZMKB1_3, self.edtNVNBIBRPZMKB2_3, self.chkNVNBIBRPPRP1_3, self.chkNVNBIBRPPRP2_3, self.edtNVNBIBRPPRP_3, self.cmbNVNBIBRP3, self.edtNVNBIBRPO1_3, self.edtNVNBIBRPO5_3],
            self.frame_35: [self.edtNVNBIBRPUV_4, self.edtNVNBIBRPPRPD_4, self.chkNVNBIBRPD1_4, self.chkNVNBIBRPD2_4, self.chkNVNBIBRPD3_4, self.edtNVNBIBRPZMKB1_4, self.edtNVNBIBRPZMKB2_4, self.chkNVNBIBRPPRP1_4, self.chkNVNBIBRPPRP2_4, self.edtNVNBIBRPPRP_4, self.cmbNVNBIBRP4, self.edtNVNBIBRPO1_4, self.edtNVNBIBRPO5_4],
            self.frame_36: [self.edtNVNBIBRPUV_5, self.edtNVNBIBRPPRPD_5, self.chkNVNBIBRPD1_5, self.chkNVNBIBRPD2_5, self.chkNVNBIBRPD3_5, self.edtNVNBIBRPZMKB1_5, self.edtNVNBIBRPZMKB2_5, self.chkNVNBIBRPPRP1_5, self.chkNVNBIBRPPRP2_5, self.edtNVNBIBRPPRP_5, self.cmbNVNBIBRP5, self.edtNVNBIBRPO1_5, self.edtNVNBIBRPO5_5],
        }
        frame.setVisible(visible)
        if frame in frameWidgets.keys() and not visible:
            for widget in frameWidgets[frame]:
                if isinstance(widget, QCheckBox):
                   widget.setChecked(visible)
                elif isinstance(widget, QtGui.QSpinBox):
                    widget.setValue(0)
                elif isinstance(widget, QComboBox):
                    widget.setCurrentIndex(-1)
                elif isinstance(widget, QtGui.QLineEdit):
                    widget.setText('')
                elif isinstance(widget, QtGui.QDoubleSpinBox):
                    widget.setValue(0)


    @pyqtSlot(int)
    def on_edtODPOBSBP_valueChanged(self, value):
        value = self.edtODPOBSBP.value()
        if not value:
            value = None
        self.setProperty(QVariant(value), u'ОД:ПОБ:СП12')


    @pyqtSlot(int)
    def on_edtODPOBSBP_2_valueChanged(self, value):
        value = self.edtODPOBSBP_2.value()
        if not value:
            value = None
        self.setProperty(QVariant(value), u'ОД:ПОБ:СП12:2')


    @pyqtSlot(int)
    def on_edtODPOBSBP_3_valueChanged(self, value):
        value = self.edtODPOBSBP_3.value()
        if not value:
            value = None
        self.setProperty(QVariant(value), u'ОД:ПОБ:СП12:3')


    @pyqtSlot(int)
    def on_edtODPOBSBP_4_valueChanged(self, value):
        value = self.edtODPOBSBP_4.value()
        if not value:
            value = None
        self.setProperty(QVariant(value), u'ОД:ПОБ:СП12:4')


    @pyqtSlot(int)
    def on_edtODPOBSBP_5_valueChanged(self, value):
        value = self.edtODPOBSBP_5.value()
        if not value:
            value = None
        self.setProperty(QVariant(value), u'ОД:ПОБ:СП12:5')


    @pyqtSlot(int)
    def on_cmbODPOBPP1_currentIndexChanged(self, value):
        self.setProperty(QVariant(self.cmbODPOBPP1.value()), u'ОД:ПОБ:ПП34:s')


    @pyqtSlot(int)
    def on_cmbODPOBPP_2_currentIndexChanged(self, value):
        self.setProperty(QVariant(self.cmbODPOBPP_2.value()), u'ОД:ПОБ:ПП34:2:s')


    @pyqtSlot(int)
    def on_cmbODPOBPP_3_currentIndexChanged(self, value):
        self.setProperty(QVariant(self.cmbODPOBPP_3.value()), u'ОД:ПОБ:ПП34:3:s')


    @pyqtSlot(int)
    def on_cmbODPOBPP_4_currentIndexChanged(self, value):
        self.setProperty(QVariant(self.cmbODPOBPP_4.value()), u'ОД:ПОБ:ПП34:4:s')


    @pyqtSlot(int)
    def on_cmbODPOBPP_5_currentIndexChanged(self, value):
        self.setProperty(QVariant(self.cmbODPOBPP_5.value()), u'ОД:ПОБ:ПП34:4:s')


    @pyqtSlot(int)
    def on_cmbODPOBNVMTO_1_currentIndexChanged(self, value):
        self.setProperty(QVariant(self.cmbODPOBNVMTO_1.value()), u'ОД:ПОБ:НВМТО34:1:s')


    @pyqtSlot(int)
    def on_cmbODPOBNVMTO_2_currentIndexChanged(self, value):
        self.setProperty(QVariant(self.cmbODPOBNVMTO_2.value()), u'ОД:ПОБ:НВМТО34:2:s')


    @pyqtSlot(int)
    def on_cmbODPOBNVMTO_3_currentIndexChanged(self, value):
        self.setProperty(QVariant(self.cmbODPOBNVMTO_3.value()), u'ОД:ПОБ:НВМТО34:3:s')


    @pyqtSlot(int)
    def on_cmbODPOBNVMTO_4_currentIndexChanged(self, value):
        self.setProperty(QVariant(self.cmbODPOBNVMTO_4.value()), u'ОД:ПОБ:НВМТО34:4:s')


    @pyqtSlot(int)
    def on_cmbODPOBNVMTO_5_currentIndexChanged(self, value):
        self.setProperty(QVariant(self.cmbODPOBNVMTO_5.value()), u'ОД:ПОБ:НВМТО34:5:s')


    @pyqtSlot(int)
    def on_cmbODPOBCZVRP_1_currentIndexChanged(self, value):
        self.setProperty(QVariant(self.cmbODPOBCZVRP_1.value()), u'ОД:ПОБ:СЗВРП:1:s')


    @pyqtSlot(int)
    def on_cmbODPOBCZVRP_2_currentIndexChanged(self, value):
        self.setProperty(QVariant(self.cmbODPOBCZVRP_2.value()), u'ОД:ПОБ:СЗВРП:2:s')


    @pyqtSlot(int)
    def on_cmbODPOBCZVRP_3_currentIndexChanged(self, value):
        self.setProperty(QVariant(self.cmbODPOBCZVRP_3.value()), u'ОД:ПОБ:СЗВРП:3:s')


    @pyqtSlot(int)
    def on_cmbODPOBCZVRP_4_currentIndexChanged(self, value):
        self.setProperty(QVariant(self.cmbODPOBCZVRP_4.value()), u'ОД:ПОБ:СЗВРП:4:s')


    @pyqtSlot(int)
    def on_cmbODPOBCZVRP_5_currentIndexChanged(self, value):
        self.setProperty(QVariant(self.cmbODPOBCZVRP_5.value()), u'ОД:ПОБ:СЗВРП:5:s')


    @pyqtSlot(int)
    def on_edtODPOBP_valueChanged(self, value):
        self.setProperty(QVariant(self.edtODPOBP.value()), u'ОД:ПОБ:П')


    @pyqtSlot(int)
    def on_edtODPOBOG_valueChanged(self, value):
        self.setProperty(QVariant(self.edtODPOBOG.value()), u'ОД:ПОБ:ОЖ20')


    @pyqtSlot(int)
    def on_edtODPOBVDM_valueChanged(self, value):
        self.setProperty(QVariant(self.edtODPOBVDM.value()), u'ОД:ПОБ:ВДМ20')


    @pyqtSlot(int)
    def on_edtODGODSM_valueChanged(self, value):
        self.setProperty(QVariant(self.edtODGODSM.value()), u'ОД:ГО:ВИ:ШМ:2')


    @pyqtSlot(str)
    def on_edtODGOTMU_textChanged(self, text):
        self.setProperty(QVariant(self.edtODGOTMU.text()), u'ОД:ГО:ВИ:ТМ:4')


    @pyqtSlot(int)
    def on_edtODGOPSSP_valueChanged(self, value):
        self.setProperty(QVariant(self.edtODGOPSSP.value()), u'ОД:ГО:ВИ:РССП')


    @pyqtSlot(int)
    def on_edtSOPWP_valueChanged(self, value):
        self.setProperty(QVariant(self.edtSOPWP.value()), u'СОП:ВП:6')


    @pyqtSlot(int)
    def on_edtSOPMN1_valueChanged(self, value):
        self.setProperty(QVariant(self.edtSOPMN1.value()), u'СОП:Менстр:1')


    @pyqtSlot(int)
    def on_edtSOPMN2_valueChanged(self, value):
        self.setProperty(QVariant(self.edtSOPMN2.value()), u'СОП:Менстр:5')


    @pyqtSlot(str)
    def on_edtSOPMN3_textChanged(self, text):
        self.setProperty(QVariant(self.edtSOPMN3.text()), u'СОП:Менстр:6')


    @pyqtSlot(int)
    def on_edtSOPPL_valueChanged(self, value):
        self.setProperty(QVariant(self.edtSOPPL.value()), u'СОП:ПЖ')


    @pyqtSlot(int)
    def on_edtSOPSoORVZ_valueChanged(self, value):
        self.setProperty(QVariant(self.edtSOPSoORVZ.value()), u'СОП:СОР:В')


    @pyqtSlot(int)
    def on_edtNVNBP1_valueChanged(self, value):
        self.setProperty(QVariant(self.edtNVNBP1.value()), u'НВНБ:Пелв:1')


    @pyqtSlot(int)
    def on_edtNVNBP2_valueChanged(self, value):
        self.setProperty(QVariant(self.edtNVNBP2.value()), u'НВНБ:Пелв:2')


    @pyqtSlot(int)
    def on_edtNVNBP3_valueChanged(self, value):
        self.setProperty(QVariant(self.edtNVNBP3.value()), u'НВНБ:Пелв:3')


    @pyqtSlot(int)
    def on_edtNVNBP4_valueChanged(self, value):
        self.setProperty(QVariant(self.edtNVNBP4.value()), u'НВНБ:Пелв:4')


    @pyqtSlot(int)
    def on_edtNVNBP5_valueChanged(self, value):
        self.setProperty(QVariant(self.edtNVNBP5.value()), u'НВНБ:Пелв:5')


    @pyqtSlot(int)
    def on_edtNVNBP6_valueChanged(self, value):
        self.setProperty(QVariant(self.edtNVNBP6.value()), u'НВНБ:Пелв:6')


    @pyqtSlot(int)
    def on_edtNVNBP7_valueChanged(self, value):
        self.setProperty(QVariant(self.edtNVNBP7.value()), u'НВНБ:Пелв:7')


    @pyqtSlot(int)
    def on_edtNVNBP8_valueChanged(self, value):
        self.setProperty(QVariant(self.edtNVNBP8.value()), u'НВНБ:Пелв:8')


    @pyqtSlot(int)
    def on_edtNVNBP9_valueChanged(self, value):
        self.setProperty(QVariant(self.edtNVNBP9.value()), u'НВНБ:Пелв:9')


    @pyqtSlot(int)
    def on_edtNVNBIBRP1_valueChanged(self, value):
        self.setProperty(QVariant(self.edtNVNBIBRP1.value()), u'НВНБ:ИБРП:КД')
        if self.edtNVNBIBRP1.value() == 0:
            self.setFetusFrameVisible(self.frame_31, False)
            self.setFetusFrameVisible(self.frame_33, False)
            self.setFetusFrameVisible(self.frame_34, False)
            self.setFetusFrameVisible(self.frame_35, False)
            self.setFetusFrameVisible(self.frame_36, False)
        elif self.edtNVNBIBRP1.value() == 1:
            self.setFetusFrameVisible(self.frame_31, True)
            self.setFetusFrameVisible(self.frame_33, False)
            self.setFetusFrameVisible(self.frame_34, False)
            self.setFetusFrameVisible(self.frame_35, False)
            self.setFetusFrameVisible(self.frame_36, False)
        elif self.edtNVNBIBRP1.value() == 2:
            self.setFetusFrameVisible(self.frame_31, True)
            self.setFetusFrameVisible(self.frame_33, True)
            self.setFetusFrameVisible(self.frame_34, False)
            self.setFetusFrameVisible(self.frame_35, False)
            self.setFetusFrameVisible(self.frame_36, False)
        elif self.edtNVNBIBRP1.value() == 3:
            self.setFetusFrameVisible(self.frame_31, True)
            self.setFetusFrameVisible(self.frame_33, True)
            self.setFetusFrameVisible(self.frame_34, True)
            self.setFetusFrameVisible(self.frame_35, False)
            self.setFetusFrameVisible(self.frame_36, False)
        elif self.edtNVNBIBRP1.value() == 4:
            self.setFetusFrameVisible(self.frame_31, True)
            self.setFetusFrameVisible(self.frame_33, True)
            self.setFetusFrameVisible(self.frame_34, True)
            self.setFetusFrameVisible(self.frame_35, True)
            self.setFetusFrameVisible(self.frame_36, False)
        elif self.edtNVNBIBRP1.value() == 5:
            self.setFetusFrameVisible(self.frame_31, True)
            self.setFetusFrameVisible(self.frame_33, True)
            self.setFetusFrameVisible(self.frame_34, True)
            self.setFetusFrameVisible(self.frame_35, True)
            self.setFetusFrameVisible(self.frame_36, True)


    @pyqtSlot(float)
    def on_edtNVNBIBRPPRP_valueChanged(self, value):
        self.setProperty(QVariant(self.edtNVNBIBRPPRP.value()), u'НВНБ:ИБРП:1:4')


    @pyqtSlot(int)
    def on_edtNVNBIBRPPRPD_valueChanged(self, value):
        self.setProperty(QVariant(self.edtNVNBIBRPPRPD.value()), u'НВНБ:ИБРП:1:5')


    @pyqtSlot(float)
    def on_edtNVNBIBRPPRP_2_valueChanged(self, value):
        self.setProperty(QVariant(self.edtNVNBIBRPPRP_2.value()), u'НВНБ:ИБРП:2:4')


    @pyqtSlot(int)
    def on_edtNVNBIBRPPRPD_2_valueChanged(self, value):
        self.setProperty(QVariant(self.edtNVNBIBRPPRPD_2.value()), u'НВНБ:ИБРП:2:5')


    @pyqtSlot(float)
    def on_edtNVNBIBRPPRP_3_valueChanged(self, value):
        self.setProperty(QVariant(self.edtNVNBIBRPPRP_3.value()), u'НВНБ:ИБРП:3:4')


    @pyqtSlot(float)
    def on_edtNVNBIBRPPRP_4_valueChanged(self, value):
        self.setProperty(QVariant(self.edtNVNBIBRPPRP_4.value()), u'НВНБ:ИБРП:4:4')


    @pyqtSlot(float)
    def on_edtNVNBIBRPPRP_5_valueChanged(self, value):
        self.setProperty(QVariant(self.edtNVNBIBRPPRP_5.value()), u'НВНБ:ИБРП:5:4')


    @pyqtSlot(int)
    def on_edtNVNBIBRPPRPD_3_valueChanged(self, value):
        self.setProperty(QVariant(self.edtNVNBIBRPPRPD_3.value()), u'НВНБ:ИБРП:3:5')


    @pyqtSlot(int)
    def on_edtNVNBIBRPPRPD_4_valueChanged(self, value):
        self.setProperty(QVariant(self.edtNVNBIBRPPRPD_4.value()), u'НВНБ:ИБРП:4:5')


    @pyqtSlot(int)
    def on_edtNVNBIBRPPRPD_5_valueChanged(self, value):
        self.setProperty(QVariant(self.edtNVNBIBRPPRPD_5.value()), u'НВНБ:ИБРП:5:5')


    @pyqtSlot(int)
    def on_edtSOPRost_valueChanged(self, value):
        self.setProperty(QVariant(self.edtSOPRost.value()), u'СОП:РПЯ')
        self.setBodyMassIndex()


    @pyqtSlot(float)
    def on_edtSOPMT_valueChanged(self, value):
        self.setProperty(QVariant(self.edtSOPMT.value()), u'СОП:МТПЯ')
        self.setBodyMassIndex()


    def setBodyMassIndex(self):
        growth = forceDouble(self.edtSOPRost.value())
        weight = forceDouble(self.edtSOPMT.value())
        growthM = growth/100.0
        bodyMassIndex = float(weight/(growthM*growthM)) if growth > 0 else 0
        self.edtSOPIMT.setValue(bodyMassIndex)


    @pyqtSlot(int)
    def on_edtSOPIMT_valueChanged(self, value):
        self.setProperty(QVariant(self.edtSOPIMT.value()), u'СОП:ИМТМ')


    @pyqtSlot(int)
    def on_edtSOPSoORRost_valueChanged(self, value):
        self.setProperty(QVariant(self.edtSOPSoORRost.value()), u'СОП:СОР:Р')
        self.setSoORBodyMassIndex()


    @pyqtSlot(float)
    def on_edtSOPSoORMT_valueChanged(self, value):
        self.setProperty(QVariant(self.edtSOPSoORMT.value()), u'СОП:СОР:МТ')
        self.setSoORBodyMassIndex()


    def setSoORBodyMassIndex(self):
        growth = forceDouble(self.edtSOPSoORRost.value())
        weight = forceDouble(self.edtSOPSoORMT.value())
        growthM = growth/100.0
        bodyMassIndex = float(weight/(growthM*growthM)) if growth > 0 else 0
        self.edtSOPSoORIMT.setValue(bodyMassIndex)


    @pyqtSlot(int)
    def on_edtSOPSoORIMT_valueChanged(self, value):
        self.setProperty(QVariant(self.edtSOPSoORIMT.value()), u'СОП:СОР:ИМТ')


    @pyqtSlot(str)
    def on_edtSOPPIMGDate_textChanged(self, text):
        self.setProperty(QVariant(forceStringEx(self.edtSOPPIMGDate.text())), u'СОП:ПИМЖ:1')


    @pyqtSlot(str)
    def on_edtSOPPZIMSMDate_textChanged(self, text):
        self.setProperty(QVariant(forceStringEx(self.edtSOPPZIMSMDate.text())), u'СОП:ПЦИМШМ:1')


    @pyqtSlot(str)
    def on_edtSOPGTRDate_textChanged(self, text):
        self.setProperty(QVariant(forceStringEx(self.edtSOPGTRDate.text())), u'СОП:ПЗ:Г:2')


    @pyqtSlot(str)
    def on_edtSOPGTRComponent_textChanged(self, text):
        self.setProperty(QVariant(forceStringEx(self.edtSOPGTRComponent.text())), u'СОП:ПЗ:Г:3')


    @pyqtSlot(str)
    def on_edtGenericCertificateSeria_textChanged(self, text):
        self.setProperty(QVariant(self.edtGenericCertificateSeria.text()),u'ОД:ОДП:РС:1')


    @pyqtSlot(str)
    def on_edtGenericCertificateNumber_textChanged(self, text):
        self.setProperty(QVariant(self.edtGenericCertificateNumber.text()),u'ОД:ОДП:РС:2')


    @pyqtSlot(str)
    def on_edtExchangeAndNotificationCardNumber_textChanged(self, text):
        self.setProperty(QVariant(self.edtExchangeAndNotificationCardNumber.text()),u'ОД:ОДП:ОУК:1')


    @pyqtSlot(str)
    def on_edtPregravidarText_textChanged(self, text):
        self.setProperty(QVariant(self.edtPregravidarText.text()),u'ОД:СНБ:ПП:2')


    @pyqtSlot(str)
    def on_edtCloseReason_textChanged(self, text):
        self.setProperty(QVariant(self.edtCloseReason.text()), u'НВНБ:ПЗ')


    @pyqtSlot()
    def on_edtODPOBGText_textChanged(self):
        self.setProperty(QVariant(self.edtODPOBGText.toPlainText()),u'ОД:ПОБ:Ж:2')


    @pyqtSlot()
    def on_edtODPOBOLocalizationText_textChanged(self):
        self.setProperty(QVariant(self.edtODPOBOLocalizationText.toPlainText()),u'ОД:ПОБ:О:2')


    @pyqtSlot()
    def on_edtODPOBULULocalizationText_textChanged(self):
        self.setProperty(QVariant(self.edtODPOBULULocalizationText.toPlainText()),u'ОД:ПОБ:УЛУ:2')


    @pyqtSlot(str)
    def on_edtODPOBC3Text_textChanged(self, text):
        self.setProperty(QVariant(self.edtODPOBC3Text.text()),u'ОД:ПОБ:С:2')


    @pyqtSlot(str)
    def on_edtODPOBOPMG3Text_textChanged(self, text):
        self.setProperty(QVariant(self.edtODPOBOPMG3Text.text()),u'ОД:ПОБ:ОПМЖ:2')


    @pyqtSlot(str)
    def on_edtODPOBTS2Text_textChanged(self, text):
        self.setProperty(QVariant(self.edtODPOBTS2Text.text()),u'ОД:ПОБ:ТС:2')


    @pyqtSlot(str)
    def on_edtODPOBADPR_textChanged(self, text):
        self.setProperty(QVariant(self.edtODPOBADPR.text()),u'ОД:ПОБ:АД:1')


    @pyqtSlot(str)
    def on_edtODPOBADLR_textChanged(self, text):
        self.setProperty(QVariant(self.edtODPOBADLR.text()),u'ОД:ПОБ:АД:2')


    @pyqtSlot()
    def on_edtODPOBAL2Text_textChanged(self):
        self.setProperty(QVariant(self.edtODPOBAL2Text.toPlainText()),u'ОД:ПОБ:АЛ:2')


    @pyqtSlot()
    def on_edtODGOOSMZ2Text_textChanged(self):
        self.setProperty(QVariant(self.edtODGOOSMZ2Text.toPlainText()),u'ОД:ГО:ОШМЗ:2')


    @pyqtSlot(str)
    def on_edtODGONPO2Text_textChanged(self, text):
        self.setProperty(QVariant(self.edtODGONPO2Text.text()),u'ОД:ГО:ВИ:НПО:2')


    @pyqtSlot(str)
    def on_edtODGOV2Text_textChanged(self, text):
        self.setProperty(QVariant(self.edtODGOV2Text.text()),u'ОД:ГО:ВИ:В:2')


    @pyqtSlot(str)
    def on_edtODGODSMText_textChanged(self, text):
        self.setProperty(QVariant(self.edtODGODSMText.text()),u'ОД:ГО:ВИ:ШМ:3')


    @pyqtSlot(str)
    def on_edtODGOSL_textChanged(self, text):
        self.setProperty(QVariant(self.edtODGOSL.text()),u'ОД:ГО:ВИ:ШМ:5')


    @pyqtSlot(str)
    def on_edtODGOTM4Text_textChanged(self, text):
        self.setProperty(QVariant(self.edtODGOTM4Text.text()),u'ОД:ГО:ВИ:ТМ:3')


    @pyqtSlot(str)
    def on_edtODGOOMP_textChanged(self, text):
        self.setProperty(QVariant(self.edtODGOOMP.text()),u'ОД:ГО:ВИ:ОП')


    @pyqtSlot(str)
    def on_edtODGOPSL2Text_textChanged(self, text):
        self.setProperty(QVariant(self.edtODGOPSL2Text.text()),u'ОД:ГО:ВИ:ПСл:2')


    @pyqtSlot(str)
    def on_edtODGOPSP3Text_textChanged(self, text):
        self.setProperty(QVariant(self.edtODGOPSP3Text.text()),u'ОД:ГО:ВИ:ПСп:2')


    @pyqtSlot(str)
    def on_edtODGOE2Text_textChanged(self, text):
        self.setProperty(QVariant(self.edtODGOE2Text.text()),u'ОД:ГО:ВИ:Э:2')


    @pyqtSlot(str)
    def on_edtSkinStatus_textChanged(self, text):
        self.setProperty(QVariant(self.edtSkinStatus.text()),u'ОД:СКП:2')


    @pyqtSlot(str)
    def on_edtODGOOZK_textChanged(self, text):
        self.setProperty(QVariant(self.edtODGOOZK.text()),u'ОД:ГО:ВИ:ОЦК')


    @pyqtSlot(str)
    def on_edtODGOOV_textChanged(self, text):
        self.setProperty(QVariant(self.edtODGOOV.text()),u'ОД:ГО:ВИ:ОБ')


    @pyqtSlot()
    def on_edtClinicalDiagnosisMain_textChanged(self):
        self.setProperty(QVariant(self.edtClinicalDiagnosisMain.toPlainText()),u'ОД:КФД:1')


    @pyqtSlot()
    def on_edtClinicalDiagnosisAccomp_textChanged(self):
        self.setProperty(QVariant(self.edtClinicalDiagnosisAccomp.toPlainText()),u'ОД:КФД:2')


    @pyqtSlot()
    def on_edtClinicalDiagnosisComplications_textChanged(self):
        self.setProperty(QVariant(self.edtClinicalDiagnosisComplications.toPlainText()),u'ОД:КФД:3')


    @pyqtSlot()
    def on_edtDiagnosis_textChanged(self):
        self.setProperty(QVariant(self.edtDiagnosis.toPlainText()),u'ОД:Д')


    @pyqtSlot()
    def on_edtODGOA_textChanged(self):
        self.setProperty(QVariant(self.edtODGOA.toPlainText()),u'ОД:ГО:ВИ:Ан')


    @pyqtSlot()
    def on_edtODGON_textChanged(self):
        self.setProperty(QVariant(self.edtODGON.toPlainText()),u'ОД:ГО:ВИ:Наз')


    @pyqtSlot(str)
    def on_edtSOPWPRText_textChanged(self, text):
        self.setProperty(QVariant(self.edtSOPWPRText.text()),u'СОП:ВПР:2')


    @pyqtSlot(str)
    def on_edtSOPDRS_textChanged(self, text):
        self.setProperty(QVariant(self.edtSOPDRS.text()),u'СОП:ДР:1')


    @pyqtSlot(str)
    def on_edtSOPDBText_textChanged(self, text):
        self.setProperty(QVariant(self.edtSOPDBText.text()),u'СОП:ПЗ:ДИ:2')


    @pyqtSlot(str)
    def on_edtSOPDSText_textChanged(self, text):
        self.setProperty(QVariant(self.edtSOPDSText.text()),u'СОП:ПЗ:НДУ:2')


    @pyqtSlot(str)
    def on_edtSOPTROText_textChanged(self, text):
        self.setProperty(QVariant(self.edtSOPTROText.text()),u'СОП:ПЗ:ТО:2')


    @pyqtSlot(str)
    def on_edtODPOBSBPR_1_textChanged(self, text):
        self.setProperty(QVariant(self.edtODPOBSBPR_1.text()),u'ОД:ПОБ:СПР2:1')


    @pyqtSlot(str)
    def on_edtODPOBSBPR_2_textChanged(self, text):
        self.setProperty(QVariant(self.edtODPOBSBPR_2.text()),u'ОД:ПОБ:СПР2:2')


    @pyqtSlot(str)
    def on_edtODPOBSBPR_3_textChanged(self, text):
        self.setProperty(QVariant(self.edtODPOBSBPR_3.text()),u'ОД:ПОБ:СПР2:3')


    @pyqtSlot(str)
    def on_edtODPOBSBPR_4_textChanged(self, text):
        self.setProperty(QVariant(self.edtODPOBSBPR_4.text()),u'ОД:ПОБ:СПР2:4')


    @pyqtSlot(str)
    def on_edtODPOBSBPR_5_textChanged(self, text):
        self.setProperty(QVariant(self.edtODPOBSBPR_5.text()),u'ОД:ПОБ:СПР2:5')


    @pyqtSlot(str)
    def on_edtSOPSZText_textChanged(self, text):
        self.setProperty(QVariant(self.edtSOPSZText.text()),u'СОП:ПЗ:СЗ:2')


    @pyqtSlot(str)
    def on_edtSOPSZIText_textChanged(self, text):
        self.setProperty(QVariant(self.edtSOPSZIText.text()),u'СОП:ПЗ:СЗИ:2')


    @pyqtSlot(str)
    def on_edtSOPVSTATUSNumberText_textChanged(self, text):
        self.setProperty(QVariant(self.edtSOPVSTATUSNumberText.text()),u'СОП:ПЗ:ВИЧ:3')


    @pyqtSlot(str)
    def on_edtSOPVSTATUSARVTText_textChanged(self, text):
        self.setProperty(QVariant(self.edtSOPVSTATUSARVTText.text()),u'СОП:ПЗ:АТ')


    @pyqtSlot(str)
    def on_edtSOPNZText_textChanged(self, text):
        self.setProperty(QVariant(self.edtSOPNZText.text()),u'СОП:ПЗ:НЗ:2')


    @pyqtSlot(str)
    def on_edtSOPPFText_textChanged(self, text):
        self.setProperty(QVariant(self.edtSOPPFText.text()),u'СОП:ПЗ:ПФ:2')


    @pyqtSlot(str)
    def on_edtSOPWPText_textChanged(self, text):
        self.setProperty(QVariant(self.edtSOPWPText.text()),u'СОП:ВП:3')


    @pyqtSlot(str)
    def on_edtSOPPRWText_textChanged(self, text):
        self.setProperty(QVariant(self.edtSOPPRWText.text()),u'ОД:ПОБ:О:2')


    @pyqtSlot(str)
    def on_edtSOPWPText11_textChanged(self, text):
        self.setProperty(QVariant(self.edtSOPWPText11.text()),u'СОП:ВП:5')


    @pyqtSlot(str)
    def on_edtSOPWPText12_textChanged(self, text):
        self.setProperty(QVariant(self.edtSOPWPText12.text()),u'СОП:ВП:7')


    @pyqtSlot(str)
    def on_edtSOPMNText_textChanged(self, text):
        self.setProperty(QVariant(self.edtSOPMNText.text()),u'ОД:ПОБ:О:2')


    @pyqtSlot(str)
    def on_edtSOPSOPR9Text_textChanged(self, text):
        self.setProperty(QVariant(self.edtSOPSOPR9Text.text()),u'СОП:СОПр:10')


    @pyqtSlot()
    def on_edtSOPKRZPText_textChanged(self):
        self.setProperty(QVariant(self.edtSOPKRZPText.toPlainText()),u'СОП:Контрац')


    @pyqtSlot()
    def on_edtSOPGZOPText_textChanged(self):
        self.setProperty(QVariant(self.edtSOPGZOPText.toPlainText()),u'СОП:ГЗО')


    @pyqtSlot(str)
    def on_edtSOPIPPPText_textChanged(self, text):
        self.setProperty(QVariant(self.edtSOPIPPPText.text()),u'СОП:ИППП:2')


    @pyqtSlot(str)
    def on_edtSOPOXZText_textChanged(self, text):
        self.setProperty(QVariant(self.edtSOPOXZText.text()),u'СОП:СОР:ХЗ:2')


    @pyqtSlot(str)
    def on_edtSOPOIPPPText_textChanged(self, text):
        self.setProperty(QVariant(self.edtSOPOIPPPText.text()),u'СОП:СОР:ИППП:2')


    @pyqtSlot(str)
    def on_edtSOPOSZIText_textChanged(self, text):
        self.setProperty(QVariant(self.edtSOPOSZIText.text()),u'СОП:СОР:СЗП:2')


    @pyqtSlot(str)
    def on_edtSOPOPFText_textChanged(self, text):
        self.setProperty(QVariant(self.edtSOPOPFText.text()),u'СОП:СОР:ПФ:2')


    @pyqtSlot(str)
    def on_edtSOPPIMGText1_textChanged(self, text):
        self.setProperty(QVariant(self.edtSOPPIMGText1.text()),u'СОП:ПИМЖ:2')


    @pyqtSlot(str)
    def on_edtSOPPIMGText2_textChanged(self, text):
        self.setProperty(QVariant(self.edtSOPPIMGText2.text()),u'СОП:ПИМЖ:3')


    @pyqtSlot(str)
    def on_edtSOPPZIMSMText1_textChanged(self, text):
        self.setProperty(QVariant(self.edtSOPPZIMSMText1.text()),u'СОП:ПЦИМШМ:2')


    @pyqtSlot(str)
    def on_edtSOPPZIMSMText2_textChanged(self, text):
        self.setProperty(QVariant(self.edtSOPPZIMSMText2.text()),u'СОП:ПЦИМШМ:3')


    @pyqtSlot(str)
    def on_edtNVNBDG2Text_textChanged(self, text):
        self.setProperty(QVariant(self.edtNVNBDG2Text.text()),u'НВНБ:ДГ:2')


    @pyqtSlot(str)
    def on_edtNVNBDGO_textChanged(self, text):
        self.setProperty(QVariant(self.edtNVNBDGO.text()),u'НВНБ:ДГ:4')


    @pyqtSlot(str)
    def on_edtNVNBPText_textChanged(self, text):
        self.setProperty(QVariant(self.edtNVNBPText.text()),u'НВНБ:Пелв:10')


    @pyqtSlot(str)
    def on_edtNVNBIBRM4_textChanged(self, text):
        self.setProperty(QVariant(self.edtNVNBIBRM4.text()),u'НВНБ:ИБРМ:5')


    @pyqtSlot(str)
    def on_edtNVNBIBRM7_textChanged(self, text):
        self.setProperty(QVariant(self.edtNVNBIBRM7.text()),u'НВНБ:ИБРМ:9')


    @pyqtSlot(str)
    def on_edtNVNBIBRM13MKB_textChanged(self, text):
        self.setProperty(QVariant(self.edtNVNBIBRM13MKB.text()),u'НВНБ:ИБРМ:16')


    @pyqtSlot(str)
    def on_edtNVNBIBRM3_textChanged(self, text):
        self.setProperty(QVariant(self.edtNVNBIBRM3.text()),u'НВНБ:ИБРМ:1:3')


    @pyqtSlot(str)
    def on_edtNVNBIBRPZMKB1_textChanged(self, text):
        self.setProperty(QVariant(self.edtNVNBIBRPZMKB1.text()),u'НВНБ:ИБРП:1:8')


    @pyqtSlot(str)
    def on_edtNVNBIBRPZMKB2_textChanged(self, text):
        self.setProperty(QVariant(self.edtNVNBIBRPZMKB2.text()),u'НВНБ:ИБРП:1:9')


    @pyqtSlot(str)
    def on_edtNVNBIBRPUV_textChanged(self, text):
        self.setProperty(QVariant(self.edtNVNBIBRPUV.text()),u'НВНБ:ИБРП:1:10')


    @pyqtSlot(str)
    def on_edtNVNBIBRPUV_2_textChanged(self, text):
        self.setProperty(QVariant(self.edtNVNBIBRPUV_2.text()),u'НВНБ:ИБРП:2:10')


    @pyqtSlot(str)
    def on_edtNVNBIBRPZMKB2_2_textChanged(self, text):
        self.setProperty(QVariant(self.edtNVNBIBRPZMKB2_2.text()),u'НВНБ:ИБРП:2:9')


    @pyqtSlot(str)
    def on_edtNVNBIBRPZMKB1_2_textChanged(self, text):
        self.setProperty(QVariant(self.edtNVNBIBRPZMKB1_2.text()),u'НВНБ:ИБРП:2:8')


    @pyqtSlot(str)
    def on_edtNVNBIBRPOPS_textChanged(self, text):
        self.setProperty(QVariant(self.edtNVNBIBRPOPS.text()),u'НВНБ:ИБРП:ОПС')


    @pyqtSlot(str)
    def on_edtNVNBIBRPZMKB1_3_textChanged(self, text):
        self.setProperty(QVariant(self.edtNVNBIBRPZMKB1_3.text()),u'НВНБ:ИБРП:3:8')


    @pyqtSlot(str)
    def on_edtNVNBIBRPZMKB2_3_textChanged(self, text):
        self.setProperty(QVariant(self.edtNVNBIBRPZMKB2_3.text()),u'НВНБ:ИБРП:3:9')


    @pyqtSlot(str)
    def on_edtNVNBIBRPZMKB1_4_textChanged(self, text):
        self.setProperty(QVariant(self.edtNVNBIBRPZMKB1_4.text()),u'НВНБ:ИБРП:4:8')


    @pyqtSlot(str)
    def on_edtNVNBIBRPZMKB2_4_textChanged(self, text):
        self.setProperty(QVariant(self.edtNVNBIBRPZMKB2_4.text()),u'НВНБ:ИБРП:4:9')


    @pyqtSlot(str)
    def on_edtNVNBIBRPZMKB1_5_textChanged(self, text):
        self.setProperty(QVariant(self.edtNVNBIBRPZMKB1_5.text()),u'НВНБ:ИБРП:5:8')


    @pyqtSlot(str)
    def on_edtNVNBIBRPZMKB2_5_textChanged(self, text):
        self.setProperty(QVariant(self.edtNVNBIBRPZMKB2_5.text()),u'НВНБ:ИБРП:5:9')


    @pyqtSlot(str)
    def on_edtNVNBIBRPUV_3_textChanged(self, text):
        self.setProperty(QVariant(self.edtNVNBIBRPUV_3.text()),u'НВНБ:ИБРП:3:10')


    @pyqtSlot(str)
    def on_edtNVNBIBRPUV_4_textChanged(self, text):
        self.setProperty(QVariant(self.edtNVNBIBRPUV_4.text()),u'НВНБ:ИБРП:4:10')


    @pyqtSlot(str)
    def on_edtNVNBIBRPUV_5_textChanged(self, text):
        self.setProperty(QVariant(self.edtNVNBIBRPUV_5.text()),u'НВНБ:ИБРП:5:10')


    def setTextEdits(self):
        self.setProperty(QVariant(self.edtGenericCertificateSeria.text()),u'ОД:ОДП:РС:1')
        self.setProperty(QVariant(self.edtGenericCertificateNumber.text()), u'ОД:ОДП:РС:2')
        self.setProperty(QVariant(self.edtExchangeAndNotificationCardNumber.text()), u'ОД:ОДП:ОУК:1')
        self.setProperty(QVariant(self.edtPregravidarText.text()), u'ОД:СНБ:ПП:2')
        self.setProperty(QVariant(self.edtCloseReason.text()), u'НВНБ:ПЗ')
        self.setProperty(QVariant(self.edtODPOBGText.toPlainText()), u'ОД:ПОБ:Ж:2')
        self.setProperty(QVariant(self.edtODPOBOLocalizationText.toPlainText()), u'ОД:ПОБ:О:2')
        self.setProperty(QVariant(self.edtODPOBULULocalizationText.toPlainText()), u'ОД:ПОБ:УЛУ:2')
        self.setProperty(QVariant(self.edtODPOBC3Text.text()), u'ОД:ПОБ:С:2')
        self.setProperty(QVariant(self.edtODPOBTS2Text.text()), u'ОД:ПОБ:ТС:2')
        self.setProperty(QVariant(self.edtODPOBADPR.text()), u'ОД:ПОБ:АД:1')
        self.setProperty(QVariant(self.edtODPOBADLR.text()), u'ОД:ПОБ:АД:2')
        self.setProperty(QVariant(self.edtODPOBAL2Text.toPlainText()), u'ОД:ПОБ:АЛ:2')
        self.setProperty(QVariant(self.edtODGOOSMZ2Text.toPlainText()), u'ОД:ГО:ОШМЗ:2')
        self.setProperty(QVariant(self.edtODGONPO2Text.text()), u'ОД:ГО:ВИ:НПО:2')
        self.setProperty(QVariant(self.edtODGOV2Text.text()), u'ОД:ГО:ВИ:В:2')
        self.setProperty(QVariant(self.edtODGODSMText.text()), u'ОД:ГО:ВИ:ШМ:3')
        self.setProperty(QVariant(self.edtODGOSL.text()), u'ОД:ГО:ВИ:ШМ:5')
        self.setProperty(QVariant(self.edtODGOTM4Text.text()), u'ОД:ГО:ВИ:ТМ:3')
        self.setProperty(QVariant(self.edtODGOOMP.text()), u'ОД:ГО:ВИ:ОП')
        self.setProperty(QVariant(self.edtODGOPSL2Text.text()), u'ОД:ГО:ВИ:ПСл:2')
        self.setProperty(QVariant(self.edtODGOPSP3Text.text()), u'ОД:ГО:ВИ:ПСп:2')
        self.setProperty(QVariant(self.edtODGOE2Text.text()), u'ОД:ГО:ВИ:Э:2')
        self.setProperty(QVariant(self.edtODGOOZK.text()), u'ОД:ГО:ВИ:ОЦК')
        self.setProperty(QVariant(self.edtODGOOV.text()), u'ОД:ГО:ВИ:ОБ')
        self.setProperty(QVariant(self.edtODGOA.toPlainText()), u'ОД:ГО:ВИ:Ан')
        self.setProperty(QVariant(self.edtODGON.toPlainText()), u'ОД:ГО:ВИ:Наз')
        self.setProperty(QVariant(self.edtSOPWPRText.text()), u'СОП:ВПР:2')
        self.setProperty(QVariant(self.edtSOPDRS.text()), u'СОП:ДР:1')
        self.setProperty(QVariant(self.edtSOPDBText.text()), u'СОП:ПЗ:ДИ:2')
        self.setProperty(QVariant(self.edtSOPDSText.text()), u'СОП:ПЗ:НДУ:2')
        self.setProperty(QVariant(self.edtSOPTROText.text()), u'СОП:ПЗ:ТО:2')
        self.setProperty(QVariant(self.edtODPOBSBPR_1.text()), u'ОД:ПОБ:СПР2:1')
        self.setProperty(QVariant(self.edtODPOBSBPR_2.text()), u'ОД:ПОБ:СПР2:2')
        self.setProperty(QVariant(self.edtODPOBSBPR_3.text()), u'ОД:ПОБ:СПР2:3')
        self.setProperty(QVariant(self.edtODPOBSBPR_4.text()), u'ОД:ПОБ:СПР2:4')
        self.setProperty(QVariant(self.edtODPOBSBPR_5.text()), u'ОД:ПОБ:СПР2:5')
        self.setProperty(QVariant(self.edtSOPSZText.text()), u'СОП:ПЗ:СЗ:2')
        self.setProperty(QVariant(self.edtSOPSZIText.text()), u'СОП:ПЗ:СЗИ:2')
        self.setProperty(QVariant(self.edtSOPVSTATUSNumberText.text()), u'СОП:ПЗ:ВИЧ:3')
        self.setProperty(QVariant(self.edtSOPVSTATUSARVTText.text()), u'СОП:ПЗ:АТ')
        self.setProperty(QVariant(self.edtSOPNZText.text()), u'СОП:ПЗ:НЗ:2')
        self.setProperty(QVariant(self.edtSOPPFText.text()), u'СОП:ПЗ:ПФ:2')
        self.setProperty(QVariant(self.edtSOPWPText.text()), u'СОП:ВП:3')
        self.setProperty(QVariant(self.edtSOPPRWText.text()), u'СОП:ПВ:2')
        self.setProperty(QVariant(self.edtSOPWPText11.text()), u'СОП:ВП:5')
        self.setProperty(QVariant(self.edtSOPWPText12.text()), u'СОП:ВП:7')
        self.setProperty(QVariant(self.edtSOPMNText.text()), u'СОП:Менстр:3')
        self.setProperty(QVariant(self.edtSOPSOPR9Text.text()), u'СОП:СОПр:10')
        self.setProperty(QVariant(self.edtSOPKRZPText.toPlainText()), u'СОП:Контрац')
        self.setProperty(QVariant(self.edtSOPGZOPText.toPlainText()), u'СОП:ГЗО')
        self.setProperty(QVariant(self.edtSOPIPPPText.text()), u'СОП:ИППП:2')
        self.setProperty(QVariant(self.edtSOPOXZText.text()), u'СОП:СОР:ХЗ:2')
        self.setProperty(QVariant(self.edtSOPOIPPPText.text()), u'СОП:СОР:ИППП:2')
        self.setProperty(QVariant(self.edtSOPOSZIText.text()), u'СОП:СОР:СЗП:2')
        self.setProperty(QVariant(self.edtSOPOPFText.text()), u'СОП:СОР:ПФ:2')
        self.setProperty(QVariant(self.edtSOPPIMGText1.text()), u'СОП:ПИМЖ:2')
        self.setProperty(QVariant(self.edtSOPPIMGText2.text()), u'СОП:ПИМЖ:3')
        self.setProperty(QVariant(self.edtSOPPZIMSMText1.text()), u'СОП:ПЦИМШМ:2')
        self.setProperty(QVariant(self.edtSOPPZIMSMText2.text()), u'СОП:ПЦИМШМ:3')
        self.setProperty(QVariant(self.edtNVNBDG2Text.text()), u'НВНБ:ДГ:2')
        self.setProperty(QVariant(self.edtNVNBDGO.text()), u'НВНБ:ДГ:4')
        self.setProperty(QVariant(self.edtNVNBPText.text()), u'НВНБ:Пелв:10')
        self.setProperty(QVariant(self.edtNVNBIBRM4.text()), u'НВНБ:ИБРМ:5')
        self.setProperty(QVariant(self.edtNVNBIBRM7.text()), u'НВНБ:ИБРМ:9')
        self.setProperty(QVariant(self.edtNVNBIBRM13MKB.text()), u'НВНБ:ИБРМ:16')
        self.setProperty(QVariant(self.edtNVNBIBRPZMKB1.text()), u'НВНБ:ИБРП:1:8')
        self.setProperty(QVariant(self.edtNVNBIBRPZMKB2.text()), u'НВНБ:ИБРП:1:9')
        self.setProperty(QVariant(self.edtNVNBIBRPUV.text()), u'НВНБ:ИБРП:1:10')
        self.setProperty(QVariant(self.edtNVNBIBRPZMKB1_2.text()), u'НВНБ:ИБРП:2:8')
        self.setProperty(QVariant(self.edtNVNBIBRPZMKB2_2.text()), u'НВНБ:ИБРП:2:9')
        self.setProperty(QVariant(self.edtNVNBIBRPUV_2.text()), u'НВНБ:ИБРП:2:10')
        self.setProperty(QVariant(self.edtNVNBIBRPZMKB1_3.text()), u'НВНБ:ИБРП:3:8')
        self.setProperty(QVariant(self.edtNVNBIBRPZMKB2_3.text()), u'НВНБ:ИБРП:3:9')
        self.setProperty(QVariant(self.edtNVNBIBRPUV_3.text()), u'НВНБ:ИБРП:3:10')
        self.setProperty(QVariant(self.edtNVNBIBRPOPS.text()), u'НВНБ:ИБРП:ОПС')
        self.setProperty(QVariant(self.edtClinicalDiagnosisMain.toPlainText()), u'ОД:КФБ:1')
        self.setProperty(QVariant(self.edtClinicalDiagnosisAccomp.toPlainText()), u'ОД:КФБ:2')
        self.setProperty(QVariant(self.edtClinicalDiagnosisComplications.toPlainText()), u'ОД:КФБ:3')
        self.setProperty(QVariant(self.edtDiagnosis.toPlainText()), u'ОД:Д')
        self.setProperty(QVariant(self.edtSkinStatus.text()), u'ОД:СКП:2')


    @pyqtSlot()
    def on_actEditClient_triggered(self):
        if QtGui.qApp.userHasAnyRight([urAdmin, urRegTabWriteRegistry, urRegTabReadRegistry]):
            dialog = CClientEditDialog(self)
            try:
                dialog.load(self.clientId)
                if dialog.exec_():
                    self.updateClientInfo()
            finally:
                dialog.deleteLater()


    @pyqtSlot()
    def on_actPortal_Doctor_triggered(self):
        templateId = None
        result = QtGui.qApp.db.getRecordEx('rbPrintTemplate', 'id',
                                           '`default` LIKE "%s" AND deleted = 0' % ('%/emkGate/index.php%'))
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


    @pyqtSlot(float)
    def on_edtAmount_valueChanged(self, value):
        actionType = self.action.getType()
        if actionType.defaultPlannedEndDate == CActionType.dpedBegDatePlusAmount:
            begDate = self.edtBegDate.date()
            amountValue = int(value)
            date = begDate.addDays(amountValue-1) if begDate and amountValue else QDate()
            self.edtPlannedEndDate.setDate(date)


    @pyqtSlot()
    def on_btnAttachedFiles_pressed(self):
        if self.btnAttachedFiles.getIsSaveModel():
            self.setIsDirty(True)



    @pyqtSlot()
    def on_btnSelectOrg_clicked(self):
        orgId = selectOrganisation(self, self.cmbOrg.value(), False, self.cmbOrg.filter)
        self.cmbOrg.updateModel()
        if orgId:
            self.cmbOrg.setValue(orgId)


    @pyqtSlot(int)
    def on_cmbPerson_currentIndexChanged(self, value):
        if self.action and forceRef(self.action.getRecord().value('person_id')) != value:
            self.action.setChanged(True)
        self.setPersonId(self.cmbPerson.value())


    @pyqtSlot(QDate)
    def on_edtDirectionDate_dateChanged(self, date):
        if self.action and forceDate(self.action.getRecord().value('directionDate')) != date:
            self.action.setChanged(True)
        self.edtDirectionTime.setEnabled(bool(date))


    @pyqtSlot(QDate)
    def on_edtBegDate_dateChanged(self, date):
        if self.action and forceDate(self.action.getRecord().value('begDate')) != date:
            self.action.setChanged(True)
        self.edtBegTime.setEnabled(bool(date))
        self.updateAmount()


    @pyqtSlot(QDate)
    def on_edtEndDate_dateChanged(self, date):
        self.edtEndTime.setEnabled(bool(date))
        self.updateAmount()
        if self.action.getType().closeEvent:
            self.setEventDate(date)


    @pyqtSlot(int)
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


    @pyqtSlot(int)
    def on_btnPrint_printByTemplate(self, templateId): # *
        context = CInfoContext()
        eventInfo = context.getInstance(CEventInfo, self.eventId)
        actionItems = self.modelPreviousPregnancy.items()
        aboutPreviousPregnancyAction = CLocActionPropertyActionsInfoList(context, actionItems)
        eventByRecord = CCookedEventInfo(context, self.eventId, self.recordEvent)
        eventActions = eventInfo.actions
        action = CCookedActionInfo(context, self.getRecord(), self.action)
        action._isDirty = self.isDirty()
        data = { 'event' : eventInfo,
                 'eventByRecord' : eventByRecord,
                 'action': action,
                 'client': eventByRecord.client,
                 'actions':eventActions,
                 'aboutPreviousPregnancyAction':aboutPreviousPregnancyAction,
                 'currentActionIndex': 0,
                 'tempInvalid': None
               }
        signAndAttachResult = applyTemplate(self, templateId, data, signAndAttachHandler=self.btnAttachedFiles.getSignAndAttachHandler())
        if signAndAttachResult:
            self.setIsDirty(True)


    def done(self, result):
        if self.isReadOnly():
            scd = self.cdDiscard
        elif result < 0: # закрытие из closeEvent или Esc
            scd = self.askSaveDiscardContinueEdit()
        elif result == 0:   # закрытие кнопкой отмены
            scd = self.cdDiscard
        else:               # закрытие кнопкой "ok"
            scd = self.cdSave
            if self.itemId() and hasattr(self, 'tabNotes') and self.tabNotes.isEventClosed():
                scd = self.askSaveDiscardContinueEdit()

        if scd == self.cdDiscard:
            self.discardData()

        if scd == self.cdDiscard or (scd == self.cdSave and self.saveData()):
            self.saveDialogPreferences()
            if result < 0:
                result = 1 if scd == self.cdSave else 0
            QtGui.QDialog.done(self, result)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelPreviousPregnancy_currentRowChanged(self, current, previous=None):
        index = self.tblPreviousPregnancy.currentIndex()
        if index.isValid():
            row = index.row()
            actionId = self.modelPreviousPregnancy.getActionIdToRow(row)
            items = self.modelPreviousPregnancy.items()
            if 0 <= row < len(items) and hasattr(items[row], 'aboutChildrenProperties'):
                self.modelPreviousPregnancyChildren.setItems(items[row].aboutChildrenProperties.getItems())
            else:
                self.modelPreviousPregnancyChildren.clearItems()
            self.updatePreviousPregnancyChildren(current, self.tblPreviousPregnancyChildren, previous, actionId)


    def updatePreviousPregnancyChildren(self, index, tbl, previous=None, actionId=None):
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
                tbl.model().setAction(action, clientId, clientSex, clientAge, eventTypeId=self.eventTypeId)
                setActionPropertiesColumnVisible(action._actionType, tbl)
                tbl.resizeColumnsToContents()
                tbl.resizeRowsToContents()
                tbl.horizontalHeader().setStretchLastSection(True)
                tbl.loadPreferencesLoc(tbl.preferencesLocal, row)
            else:
                tbl.model().setAction(None, None)


    @pyqtSignature('')
    def on_tblPregnancyRetrospect_popupMenuAboutToShow(self):
        notEmpty = self.modelPregnancyRetrospect.rowCount() > 0
        self.actAddPregnancyRetrospect.setEnabled(notEmpty)
        isCurrentEvent = False
        indexAction = self.tblPregnancyRetrospect.currentIndex()
        if indexAction.isValid():
            rowAction = indexAction.row()
            if rowAction >= 0 and rowAction < len(self.modelPregnancyRetrospect.idList()):
                actionId = self.modelPregnancyRetrospect._idList[rowAction]
                if actionId and self.eventId == self.modelPregnancyRetrospect.eventIdDict.get(actionId, None):
                    isCurrentEvent = True
        self.actEditAction.setEnabled(notEmpty and isCurrentEvent)
        self.actDeleteAction.setEnabled(notEmpty and isCurrentEvent)


    def resetPregnancyRetrospectTable(self):
        self.updateAddPregnancyRetrospectTable()
        self.modelPregnancyRetrospectChildren.includeRows = {}
        self.modelPregnancyRetrospect.includeItems = {}
        self.modelPregnancyRetrospect.enableIdList = []
        self.modelPregnancyRetrospect.actionsPropertiesRegistry = {}


    def updateAddPregnancyRetrospectTable(self):
        actionItems = self.modelPreviousPregnancy.items()
        if len(actionItems) > 0:
            actionRow = 0
            actionIndex = self.tblPreviousPregnancy.currentIndex()
            if actionIndex.isValid():
                actionRow = actionIndex.row()
            self.tblPreviousPregnancy.setCurrentRow(actionRow)
        else:
            self.modelPreviousPregnancyChildren.clearItems()
        self.on_btnBoxPregnancyRetrospect_apply()


    @pyqtSignature('')
    def on_actAddPregnancyRetrospect_triggered(self):
        selectedIdList = self.modelPregnancyRetrospect.getSelectedIdList()
        ActionIdList = self.modelPreviousPregnancy.getActionIdList()
        for selectedId in selectedIdList:
            if selectedId and selectedId not in ActionIdList:
                record = self.modelPreviousPregnancy.getEmptyRecord()
                record.setValue('master_id', toVariant(self.itemId()))
                record.setValue('action_id', toVariant(selectedId))
                record.setValue('additional', toVariant(self.modelPregnancyRetrospect.getBasicAdditional(selectedId)))
                record.aboutChildrenProperties = CAboutChildrenPropertiesRegistry()
                actionsPropertiesRegistry = self.modelPregnancyRetrospect.actionsPropertiesRegistry.get(selectedId, None)
                if actionsPropertiesRegistry:
                    actionsPropertyIdItems = actionsPropertiesRegistry.getItems()
                    if not actionsPropertyIdItems:
                        actionsPropertyIdItems = self.getPropertiesIdListToAction(selectedId)
                else:
                    actionsPropertyIdItems = self.getPropertiesIdListToAction(selectedId)
                    if actionsPropertyIdItems:
                        actionsPropertiesRegistry = CActionsPropertiesRegistry()
                        actionsPropertiesRegistry.addItems(actionsPropertyIdItems)
                        self.modelPregnancyRetrospect.actionsPropertiesRegistry[selectedId] = actionsPropertiesRegistry
                for actionsPropertyId in actionsPropertyIdItems:
                    record.aboutChildrenProperties.addItem(self.itemId(), selectedId, actionsPropertyId)
                self.modelPreviousPregnancy.addItem(record)
        row = len(self.modelPreviousPregnancy.items())-1
        if row >= 0 and row < len(self.modelPreviousPregnancy.items()):
            self.modelPreviousPregnancy.reset()
            self.tblPreviousPregnancy.setCurrentRow(row)
        else:
            self.modelPreviousPregnancy.reset()
        self.deletedPregnancyRetrospectTable()


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


    def deletedPregnancyRetrospectTable(self):
        self.resetPregnancyRetrospectTable()


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_modelPregnancyRetrospectChildren_dataChanged(self, topLeft, bottomRight):
        indexAction = self.tblPregnancyRetrospect.currentIndex()
        if indexAction.isValid():
            rowAction = indexAction.row()
            if rowAction >= 0 and rowAction < len(self.modelPregnancyRetrospect.idList()):
                indexProperty = topLeft
                if indexProperty.isValid():
                    columnProperty = indexProperty.column()
                    if columnProperty == 0:
                        rowProperty = indexProperty.row()
                        if 0 <= rowProperty < len(self.modelPregnancyRetrospectChildren.propertyTypeList):
                            isChecked = self.modelPregnancyRetrospectChildren.includeRows[rowProperty]
                            actionId = self.modelPregnancyRetrospect._idList[rowAction]
                            actionsPropertiesRegistry = self.modelPregnancyRetrospect.actionsPropertiesRegistry.get(actionId, None)
                            if not actionsPropertiesRegistry:
                                actionsPropertiesRegistry = CActionsPropertiesRegistry()
                            property = self.modelPregnancyRetrospectChildren.getProperty(rowProperty)
                            if property:
                                record = property.getRecord()
                                if record:
                                    propertyId = forceRef(record.value('id'))
                                    if propertyId:
                                        if bool(isChecked):
                                            actionsPropertiesRegistry.addItem(propertyId)
                                        else:
                                            actionsPropertiesRegistry.removeItem(propertyId)
                                        self.modelPregnancyRetrospect.includeItems[actionId] = self.modelPregnancyRetrospectChildren.includeRows
                                        self.modelPregnancyRetrospect.actionsPropertiesRegistry[actionId] = actionsPropertiesRegistry
                                        if actionsPropertiesRegistry and len(actionsPropertiesRegistry.getItems()) > 0:
                                            self.modelPregnancyRetrospect.setData(indexAction, QVariant(Qt.Checked), role=Qt.CheckStateRole)
                                        else:
                                            self.modelPregnancyRetrospect.setData(indexAction, QVariant(Qt.Unchecked), role=Qt.CheckStateRole)


    def on_btnBoxPregnancyRetrospect_apply(self):
        filter = {}
        filter['begDate'] = self.edtBegDatePregnancyRetrospect.text()
        filter['endDate'] = self.edtEndDatePregnancyRetrospect.text()
        self.updatePregnancyRetrospect(filter)
        self.focusPregnancyRetrospect()


    def updatePregnancyRetrospect(self, filter, posToId=None, fieldName=None):
        order = ['Action.endDate DESC', 'id']
        actionIdList, eventIdDict = self.selectPregnancyRetrospect(filter, order, fieldName)
        self.tblPregnancyRetrospect.setIdList(actionIdList, posToId)
        self.modelPregnancyRetrospect.setEventIdDict(eventIdDict)
        self.modelPregnancyRetrospect.setEventId(self.eventId)
        self.modelPregnancyRetrospect.reset()


    def selectPregnancyRetrospect(self, filter, order, fieldName):
        return self.getClientPregnancyRetrospect(self.clientId, filter, order, fieldName)
    

    def getClientPregnancyRetrospect(self, clientId, filter, order = ['Action.endDate DESC', 'Action.id'], fieldName = None):
        db = QtGui.qApp.db
        tableEvent = db.table('Event')
        tableAction = db.table('Action')
        tableEventType = db.table('EventType')
        tableActionProperty = db.table('ActionProperty')
        tableActionPropertyString = db.table('ActionProperty_String')
        table = tableAction.leftJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))
        table = table.innerJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
        table = table.leftJoin(tableActionProperty, tableActionProperty['action_id'].eq(tableAction['id']))
        table = table.leftJoin(tableActionPropertyString, tableActionPropertyString['id'].eq(tableActionProperty['id']))
        actionTypeIdListByKBiR = getActionTypeIdListByFlatCode(u'111/y-20_1')
        cond = [tableEventType['code'].like(u'KBiR%'),
                tableEvent['client_id'].eq(clientId),
                tableEvent['deleted'].eq(0),
                tableEventType['deleted'].eq(0),
                tableAction['deleted'].eq(0),
                tableAction['actionType_id'].inlist(actionTypeIdListByKBiR),
                    ]
        begDate = filter.get('begDate', u'1900')
        endDate = filter.get('endDate', u'2999')
        if begDate and endDate:
            cond.append(u'''
                        (LEFT(ActionProperty_String.value, 4) + 0) between {} and {}
                        '''.format(begDate, endDate))          
        try:
            actionIdList = []
            eventIdDict = {}
            QtGui.QApplication.setOverrideCursor(QtGui.QCursor(Qt.WaitCursor))
            records = db.getRecordList(table, 'Action.*', cond, order)
            for record in records:
                    actionId = forceRef(record.value('id'))
                    if actionId and actionId not in actionIdList:
                        actionIdList.append(actionId)
                        eventId = forceRef(record.value('event_id'))
                        eventIdDict[actionId] = eventId
        finally:
            QtGui.QApplication.restoreOverrideCursor()
        return actionIdList, eventIdDict


    def focusPregnancyRetrospect(self):
        self.tblPregnancyRetrospect.setFocus(Qt.TabFocusReason)
        

    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelPregnancyRetrospect_currentRowChanged(self, current, previous):
        self.updatePregnancyRetrospectChildrenTable(current, self.tblPregnancyRetrospectChildren, previous)


    def updatePregnancyRetrospectChildrenTable(self, index, tbl, previous=None):
        if previous:
            tbl.savePreferencesLoc(previous.row())
        row = index.row()
        record = index.model().getRecordByRow(row) if row >= 0 else None
        if record:
            clientId = self.clientId
            clientSex = self.clientSex
            clientAge = self.clientAge
            action = CAction(record=record)
            tbl.model().setChildrenAction(action, clientId, clientSex, clientAge, eventTypeId=self.eventTypeId)
            setActionPropertiesColumnVisible(action._actionType, tbl)
            currentActionId = self.modelPregnancyRetrospectChildren.getCurrentActionId()
            if currentActionId:
                self.modelPregnancyRetrospectChildren.includeRows = self.modelPregnancyRetrospect.includeItems.get(currentActionId, {})
            tbl.resizeColumnsToContents()
            tbl.resizeRowsToContents()
            tbl.horizontalHeader().setStretchLastSection(True)
            tbl.loadPreferencesLoc(tbl.preferencesLocal, row)
        else:
            tbl.model().setChildrenAction(None, None)


    @pyqtSignature('')
    def on_actEditAction_triggered(self):
        indexAction = self.tblPregnancyRetrospect.currentIndex()
        if indexAction.isValid():
            rowAction = indexAction.row()
            if rowAction >= 0 and rowAction < len(self.modelPregnancyRetrospect.idList()):
                actionId = self.modelPregnancyRetrospect._idList[rowAction]
                if actionId and self.eventId == self.modelPregnancyRetrospect.eventIdDict.get(actionId, None):
                    newActionId = self.editAction(actionId)
                    if newActionId:
                        self.on_btnBoxPregnancyRetrospect_apply()
                        self.modelPreviousPregnancyChildren.clearItems()
                        actionIndex = self.tblPreviousPregnancy.currentIndex()
                        if actionIndex.isValid():
                            actionRow = actionIndex.row()
                        else:
                            actionRow = 0
                        self.modelPreviousPregnancy.reset()
                        self.tblPreviousPregnancy.setCurrentRow(actionRow)
                        self.modelPreviousPregnancy.invalidateRecordsCache()


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
        indexAction = self.tblPregnancyRetrospect.currentIndex()
        if indexAction.isValid():
            rowAction = indexAction.row()
            if rowAction >= 0 and rowAction < len(self.modelPregnancyRetrospect.idList()):
                actionId = self.modelPregnancyRetrospect._idList[rowAction]
                if actionId and self.eventId == self.modelPregnancyRetrospect.eventIdDict.get(actionId, None):
                    if self.deleteAction(actionId):
                        self.tblPregnancyRetrospect.setCurrentRow(0)
                        self.on_btnBoxPregnancyRetrospect_apply()
                        self.modelPreviousPregnancy.clearItems()
                        self.modelPreviousPregnancyChildren.clearItems()
                        self.modelPregnancyRetrospectChildren.clearItems()
                        actionIndex = self.tblPreviousPregnancy.currentIndex()
                        if actionIndex.isValid():
                            actionRow = actionIndex.row()
                        else:
                            actionRow = 0
                        self.modelPreviousPregnancy.reset()
                        self.tblPreviousPregnancy.setCurrentRow(actionRow)
                        self.tblPreviousPregnancy.setCurrentRow(0)


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
                
                tableAActionProperty = db.table('Action_ActionProperty')
                filter = [db.joinOr([tableAActionProperty['action_id'].eq(actionId), tableAActionProperty['master_id'].eq(actionId)]), tableAActionProperty['deleted'].eq(0)]
                db.deleteRecord(tableAActionProperty, filter)

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


    def on_btnBoxPregnancyRetrospect_reset(self):
        self.edtBegDatePregnancyRetrospect.setValue(1900)
        self.edtEndDatePregnancyRetrospect.setValue(2999)


    @pyqtSignature('int')
    def on_twPregnancyRetrospect_currentChanged(self, index):
        widget = self.twPregnancyRetrospect.widget(index)
        if widget is not None:
            focusProxy = widget.focusProxy()
            if focusProxy:
                focusProxy.setFocus(Qt.OtherFocusReason)
        if index == 0:
            self.on_btnBoxPregnancyRetrospect_reset()
            self.on_btnBoxPregnancyRetrospect_apply()


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelPregnancyInfoAdd_currentRowChanged(self, current, previous):
        self.updatePregnancyInfoAddTable(current, self.tblPregnancyInfoAddChildren, previous)


    def updatePregnancyInfoAddTable(self, index, tbl, previous=None):
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


    def on_addRows(self):
        actionTypeIds = getActionTypeIdListByFlatCode(u'111/y-20_1')
        if actionTypeIds:
            currentRow = self.tblPregnancyInfoAdd.currentIndex().row() if self.tblPregnancyInfoAdd.currentIndex().isValid() else -1
            db = QtGui.qApp.db
            tableAction = db.table('Action')
            actionType = CActionTypeCache.getById(actionTypeIds[0])
            defaultStatus = actionType.defaultStatus
            defaultOrgId = actionType.defaultOrgId
            defaultExecPersonId = actionType.defaultExecPersonId
            newRecord = tableAction.newRecord()
            newRecord.setValue('createDatetime', toVariant(QDateTime.currentDateTime()))
            newRecord.setValue('createPerson_id', toVariant(QtGui.qApp.userId))
            newRecord.setValue('modifyDatetime', toVariant(QDateTime.currentDateTime()))
            newRecord.setValue('modifyPerson_id', toVariant(QtGui.qApp.userId))
            newRecord.setValue('actionType_id', toVariant(actionTypeIds[0]))
            newRecord.setValue('status', toVariant(defaultStatus))
            newRecord.setValue('begDate', toVariant(QDateTime.currentDateTime()))
            newRecord.setValue('directionDate', toVariant(QDateTime.currentDateTime()))
            newRecord.setValue('org_id', toVariant(defaultOrgId if defaultOrgId else QtGui.qApp.currentOrgId()))
            newRecord.setValue('setPerson_id', toVariant(QtGui.qApp.userId))
            newRecord.setValue('person_id', toVariant(defaultExecPersonId))
            newRecord.setValue('id', toVariant(None))
            newRecord.setValue('additional', toVariant(0))
            dialog = CActionEditDialog(self)
            try:
                dialog.save = lambda: True
                dialog.setForceClientId(self.clientId)
                dialog.setRecord(newRecord)
                dialog.setReduced(True)
                if dialog.exec_():
                    newAction = dialog.action
                else:
                    newAction = None
            finally:
                dialog.deleteLater()
            if newAction:
                self.modelPregnancyInfoAdd.addRecord(newAction.getRecord(), newAction)
                self.modelPregnancyInfoAdd.setAction(newAction, newAction.getRecord())
            if currentRow >= 0:
                self.tblPregnancyInfoAdd.setCurrentRow(currentRow)
            elif len(self.modelPregnancyInfoAdd.items()) > 0:
                self.tblPregnancyInfoAdd.setCurrentRow(0)
            self.modelPregnancyInfoAdd.reset()
        

    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelPregnancyInfoAdd_currentRowChanged(self, current, previous):
        self.updatePregnancyInfoAddChildrenTable(current, self.tblPregnancyInfoAddChildren, previous)


    def updatePregnancyInfoAddChildrenTable(self, index, tbl, previous=None):
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


    def on_actPropertyEditorAmbCard_triggered(self):
        act = self.sender()
        propertyTypeName = act.data()
        widget = act.widget
        actionProperty = self.action.getPropertyByShortName(forceString(propertyTypeName))
        if actionProperty:
            dialog = CPropertyEditorAmbCard(self, self.clientId, self.clientSex, self.clientAge, self.eventTypeId, actionProperty)
            try:
                if dialog.exec_():
                    actionProperty = dialog.actionProperty
                    widget.setText(dialog.actionProperty.getValue())
            finally:
                dialog.deleteLater()
    
    
    def initAmbWidgets(self):
        return {
            self.edtPregravidarText: u'ОД:СНБ:ПП:2',
            self.edtCloseReason: u'НВНБ:ПЗ',
            self.edtODPOBGText: u'ОД:ПОБ:Ж:2',
            self.edtODPOBOLocalizationText: u'ОД:ПОБ:О:2',
            self.edtODPOBULULocalizationText: u'ОД:ПОБ:УЛУ:2',
            self.edtODPOBOPMG3Text: u'ОД:ПОБ:ОПМЖ:2',
            self.edtODPOBC3Text: u'ОД:ПОБ:С:2',
            self.edtODPOBTS2Text: u'ОД:ПОБ:ТС:2',
            self.edtODPOBAL2Text: u'ОД:ПОБ:АЛ:2',
            self.edtODGOOSMZ2Text: u'ОД:ГО:ОШМЗ:2',
            self.edtODGONPO2Text: u'ОД:ГО:ВИ:НПО:2',
            self.edtODGOV2Text: u'ОД:ГО:ВИ:В:2',
            self.edtODGODSMText: u'ОД:ГО:ВИ:ШМ:3',
            self.edtODGOSL: u'ОД:ГО:ВИ:ШМ:5',
            self.edtODGOTM4Text: u'ОД:ГО:ВИ:ТМ:3',
            self.edtODGOOMP: u'ОД:ГО:ВИ:ОП',
            self.edtODGOPSL2Text: u'ОД:ГО:ВИ:ПСл:2',
            self.edtODGOPSP3Text: u'ОД:ГО:ВИ:ПСп:2',
            self.edtODGOE2Text: u'ОД:ГО:ВИ:Э:2',
            self.edtODGOOZK: u'ОД:ГО:ВИ:ОЦК',
            self.edtODGOOV: u'ОД:ГО:ВИ:ОБ',
            self.edtODGOA: u'ОД:ГО:ВИ:Ан',
            self.edtODGON: u'ОД:ГО:ВИ:Наз',
            self.edtSOPWPRText: u'СОП:ВПР:2',
            self.edtSOPDRS: u'СОП:ДР:1',
            self.edtSOPDBText: u'СОП:ПЗ:ДИ:2',
            self.edtSOPDSText: u'СОП:ПЗ:НДУ:2',
            self.edtSOPTROText: u'СОП:ПЗ:ТО:2',
            self.edtODPOBSBPR_1: u'ОД:ПОБ:СПР2:1',
            self.edtODPOBSBPR_2: u'ОД:ПОБ:СПР2:2',
            self.edtODPOBSBPR_3: u'ОД:ПОБ:СПР2:3',
            self.edtODPOBSBPR_4: u'ОД:ПОБ:СПР2:4',
            self.edtODPOBSBPR_5: u'ОД:ПОБ:СПР2:5',
            self.edtSOPSZText: u'СОП:ПЗ:СЗ:2',
            self.edtSOPVSTATUSARVTText: u'СОП:ПЗ:АТ',
            self.edtSOPSZIText: u'СОП:ПЗ:СЗИ:2',
            self.edtSOPNZText: u'СОП:ПЗ:НЗ:2',
            self.edtSOPGTRComponent: u'СОП:ПЗ:Г:3',
            self.edtSOPPFText: u'СОП:ПЗ:ПФ:2',
            self.edtSOPPRWText: u'СОП:ПВ:2',
            self.edtSOPKRZPText: u'СОП:Контрац',
            self.edtSOPGZOPText: u'СОП:ГЗО',
            self.edtSOPIPPPText: u'СОП:ИППП:2',
            self.edtSOPPIMGText2: u'СОП:ПИМЖ:3',
            self.edtSOPPZIMSMText2: u'СОП:ПЦИМШМ:3',
            self.edtSOPOXZText: u'СОП:СОР:ХЗ:2',
            self.edtSOPOIPPPText: u'СОП:СОР:ИППП:2',
            self.edtSOPOSZIText: u'СОП:СОР:СЗП:2',
            self.edtSOPOPFText: u'СОП:СОР:ПФ:2',
            self.edtNVNBDG2Text: u'НВНБ:ДГ:2',
            self.edtNVNBPText: u'НВНБ:Пелв:10',
            self.edtNVNBIBRM4: u'НВНБ:ИБРМ:5',
            self.edtNVNBIBRM7: u'НВНБ:ИБРМ:9',
            self.edtClinicalDiagnosisMain: u'ОД:КФД:1',
            self.edtClinicalDiagnosisAccomp: u'ОД:КФД:2',
            self.edtClinicalDiagnosisComplications: u'ОД:КФД:3',
            self.edtDiagnosis: u'ОД:Д',
            self.edtSkinStatus: u'ОД:СКП:2',
            self.edtNVNBDGO: u'НВНБ:ДГ:4',
            self.edtNVNBIBRM3: u'НВНБ:ИБРМ:1:3',
            
        }
    
    
    def getReferenceComboBoxes(self):
        return {
            self.cmbODPOBPP1: u'ОД:ПОБ:ПП34:s',
            self.cmbODPOBPP_2: u'ОД:ПОБ:ПП34:2:s',
            self.cmbODPOBPP_3: u'ОД:ПОБ:ПП34:3:s',
            self.cmbODPOBPP_4: u'ОД:ПОБ:ПП34:4:s',
            self.cmbODPOBPP_5: u'ОД:ПОБ:ПП34:5:s',
            self.cmbODPOBNVMTO_1: u'ОД:ПОБ:НВМТО34:1:s',
            self.cmbODPOBNVMTO_2: u'ОД:ПОБ:НВМТО34:2:s',
            self.cmbODPOBNVMTO_3: u'ОД:ПОБ:НВМТО34:3:s',
            self.cmbODPOBNVMTO_4: u'ОД:ПОБ:НВМТО34:4:s',
            self.cmbODPOBNVMTO_5: u'ОД:ПОБ:НВМТО34:5:s',
            self.cmbODPOBCZVRP_1: u'ОД:ПОБ:СЗВРП:1:s',
            self.cmbODPOBCZVRP_2: u'ОД:ПОБ:СЗВРП:2:s',
            self.cmbODPOBCZVRP_3: u'ОД:ПОБ:СЗВРП:3:s',
            self.cmbODPOBCZVRP_4: u'ОД:ПОБ:СЗВРП:4:s',
            self.cmbODPOBCZVRP_5: u'ОД:ПОБ:СЗВРП:5:s',
            self.cmbNVNBPUDRP: u'НВНБ:УД:РП:s',
            self.cmbNVNBPUDSM: u'НВНБ:УД:СМ:s',
            self.cmbNVNBPUDSST: u'НВНБ:УД:ССТ:s',
            self.cmbNVNBPUDFTB: u'НВНБ:УД:ФТБ:s', 
            self.cmbNVNBPUDKOV: u'НВНБ:УД:КОВ:s', 
            self.cmbNVNBPUDCA: u'НВНБ:УД:СА:s', 
            self.cmbNVNBIBRM: u'НВНБ:ИБРМ:1:s',
            self.cmbNVNBIBRP1: u'НВНБ:ИБРП:1:1:1',
            self.cmbNVNBIBRP2: u'НВНБ:ИБРП:2:1:1',
            self.cmbNVNBIBRP3: u'НВНБ:ИБРП:3:1:1',
            self.cmbNVNBIBRP4: u'НВНБ:ИБРП:4:1:1',
            self.cmbNVNBIBRP5: u'НВНБ:ИБРП:5:1:1',
        }