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
##
## Форма 131: ДД и т.п.
##
#############################################################################
from math import ceil

from PyQt4 import QtGui, QtSql, QtCore
from PyQt4.QtCore import Qt, QDate, QDateTime, QModelIndex, QObject, QTime, QVariant, pyqtSignature, SIGNAL, QEvent

from Events.ActionsSelector import selectActionTypesEx
from Events.EventAddChronicDiseasesDialog import CChronicDiseasesLoadDialog
from Events.ExportMIS import iniExportEvent
from F088.F0882022EditDialog import CEventExportTableModel, CAdvancedExportTableModel
from Events.RelatedEventAndActionListDialog import CRelatedEventAndActionListDialog
from library.Attach.AttachAction import getAttachAction
from library.crbcombobox        import CRBComboBox
from library.ICDInDocTableCol   import CICDExInDocTableCol
from library.ICDMorphologyInDocTableCol import CMKBMorphologyCol
from library.InDocTable         import CBoolInDocTableCol, CDateInDocTableCol, CDateTimeForEventInDocTableCol, CInDocTableCol, CMKBListInDocTableModel, CRBInDocTableCol, CRBLikeEnumInDocTableCol, CEnumInDocTableCol
from library.interchange        import getDateEditValue, getDatetimeEditValue, getRBComboBoxValue, setDateEditValue, setDatetimeEditValue, setRBComboBoxValue
from library.MapCode            import createMapCodeToRowIdx
from library.PrintInfo          import CDateInfo, CInfoContext
from library.PrintTemplates     import applyTemplate, getPrintButton, customizePrintButton
from library.TNMS.TNMSComboBox   import CTNMSCol
from library.MKBExSubclassComboBox import CMKBExSubclassCol
from library.Utils              import copyFields, forceBool, forceDate, forceDateTime, forceInt, forceRef, forceString, forceStringEx, formatNum, toDateTimeWithoutSeconds, toVariant, trim, variantEq

from Events.Action                import CActionTypeCache, CActionType
from Events.ActionInfo          import CActionInfoProxyList
from Events.ActionsSummaryModel import CFxxxActionsSummaryModel
from Events.DiagnosisType       import CDiagnosisTypeCol
from Events.DispansInfo         import CLocActionDispansPhaseInfo, CLocAdditionInfoList, CLocDiagnosticInfoList, CLocDiseasesInfoList, CLocHazardInfoList
from Events.EventEditDialog     import CEventEditDialog, CDiseaseCharacter, CDiseaseStage, CDiseasePhases, CToxicSubstances, getToxicSubstancesIdListByMKB
from Events.EventInfo           import CActionDispansPhaseInfo, CDiagnosticInfoProxyList, CEventInfo, CHospitalInfo
from Events.Utils import getEventResultId, CEventTypeDescription, checkDiagnosis, checkIsHandleDiagnosisIsChecked, \
    CPayStatus, getEventSceneId, getAvailableCharacterIdByMKB, getDiagnosisId2, getEventDurationRange, \
    getEventMesRequired, getEventPlannedInspections, getEventSetPerson, getEventShowTime, getEventShowVisitTime, \
    getExactServiceId, getHealthGroupFilter, getNextEventDate, getWorstPayStatus, \
    setAskedClassValueForDiagnosisManualSwitch, getEventIsPrimary, CTableSummaryActionsMenuMixin, getNewResultCond, \
    isDefaultResultIdValid, CFinanceType, mkbIsOnko, getEventAidTypeRegionalCode
from F131.PreF131Dialog         import CPreF131Dialog
from Orgs.Orgs                  import selectOrganisation
from Orgs.PersonInfo            import CPersonInfo
from Orgs.Utils import getOrganisationInfo, getOrgstructureListByEventtypeId, getPersonListByEventtypeId
from Registry.HurtModels        import CWorkHurtFactorsModel, CWorkHurtsModel
from Reports.Report             import normalizeMKB
from Users.Rights                import urAdmin, urEditAfterInvoicingEvent, urEditEndDateEvent, urRegTabWriteRegistry, urRegTabReadRegistry, urCanReadClientVaccination, urCanEditClientVaccination
from Orgs.PersonComboBoxEx      import CPersonFindInDocTableCol

from F131.Ui_F131               import Ui_Dialog
import ExaminCalc


RowsTemplate = [
                (u'Некоторые инфекционные и паразитарные болезни', u'1', u'A00 - B99'),
                (u'в том числе: туберкулез', u'1.1', u'A15 - A19'),
                (u'Новообразования', u'2', u'C00 - D48'),
	            (u'в том числе: злокачественные новообразования и новообразования in situ', u'2.1', u'C00 - D09'),
                (u'в том числе: пищевода', u'2.2', u'C15, D00.1'),
                (u'из них в 1 - 2 стадии', u'2.2.1', u'C15, D00.1'),
                (u'желудка', u'2.3', u'C16, D00.2'),
                (u'из них в 1 - 2 стадии', u'2.3.1', u'C16, D00.2'),
                (u'ободочной кишки', u'2.4', u'C18, D01.0'),
                (u'из них в 1 - 2 стадии', u'2.4.1', u'C18, D01.0'),
                (u'ректосигмоидного соединения, прямой кишки, заднего прохода (ануса) и анального канала', u'2.5', u'C19 - C21, D01.1 - D01.3'),
                (u'из них в 1 - 2 стадии', u'2.5.1', u'C19 - C21, D01.1 - D01.3'),
                (u'поджелудочной железы', u'2.6', u'C25'),
                (u'из них в 1 - 2 стадии', u'2.6.1', u'C25'),
                (u'трахеи, бронхов и легкого', u'2.7', u'C33, C34, D02.1 - D02.2'),
                (u'из них в 1 - 2 стадии', u'2.7.1', u'C33, C34, D02.1 - D02.2'),
                (u'молочной железы', u'2.8', u'C50, D05'),
                (u'из них в 1 - 2 стадии', u'2.8.1', u'C50, D05'),
                (u'шейки матки', u'2.9', u'C53, D06'),
                (u'из них в 1 - 2 стадии', u'2.9.1', u'C53, D06'),
                (u'тела матки', u'2.10', u'C54'),
                (u'из них в 1 - 2 стадии', u'2.10.1', u'C54'),
                (u'яичника', u'2.11', u'C56'),
                (u'из них в 1 - 2 стадии', u'2.11.1', u'C56'),
                (u'предстательной железы', u'2.12', u'C61, D07.5'),
                (u'из них в 1 - 2 стадии', u'2.12.1', u'C61, D07.5'),
                (u'почки, кроме почечной лоханки', u'2.13', u'C64'),
                (u'из них в 1 - 2 стадии', u'2.13.1', u'C64'),
                (u'Болезни крови, кроветворных органов и отдельные нарушения, вовлекающие иммунный механизм', u'3', u'D50 - D89'),
                (u'в том числе: анемии, связанные с питанием, гемолитические анемии,', u'3.1', u'D50 - D64'),
                (u'апластические и другие анемии', u'', u''), #??????????????????????
                (u'Болезни эндокринной системы, расстройства питания и нарушения обмена веществ', u'4', u'E00 - E90'),
                (u'в том числе: сахарный диабет', u'4.2', u'E10 - E14'),
                (u'ожирение', u'2', u'E66'),
                (u'нарушения обмена липопротеинов и другие липидемии', u'4.3', u'E78'),
                (u'Болезни нервной системы', u'5', u'G00 - G99'),
                (u'в том числе: преходящие церебральные ишемические приступы [атаки] и родственные синдромы', u'5.1', u'G45'),
                (u'Болезни глаза и его придаточного аппарата', u'6', u'H00 - H59'),
                (u'в том числе: старческая катаракта и другие катаракты', u'6.1', u'H25, H26'),
                (u'глаукома', u'6.2', u'H40'),
                (u'слепота и пониженное зрение', u'6.3', u'H54'),
                (u'Болезни системы кровообращения', u'7', u'I00 - I99'),
                (u'в том числе: болезни, характеризующиеся повышенным кровяным давлением', u'7.1', u'I10 - I15'),
                (u'ишемическая болезнь сердца', u'7.2', u'I20 - I25'),
                (u'в том числе: стенокардия (грудная жаба)', u'7.2.1', u'I20'),
                (u'в том числе нестабильная стенокардия', u'7.2.2', u'I20.0'),
                (u'хроническая ишемическая болезнь сердца', u'7.2.3', u'I25'),
                (u'в том числе: перенесенный в прошлом инфаркт миокарда', u'7.2.4', u'I25.2'),
                (u'другие болезни сердца', u'7.3', u'I30 - I52'),
                (u'цереброваскулярные болезни', u'7.4', u'I60 - I69'),
                (u'в том числе: закупорка и стеноз прецеребральных артерий, не приводящие к инфаркту мозга и закупорка и стеноз церебральных артерий, не приводящие к инфаркту мозга', u'7.4.1', u'I65, I66'),
                (u'другие цереброваскулярные болезни', u'7.4.2', u'I67'),
                (u'последствия субарахноидального кровоизлияния, последствия внутричерепного кровоизлияния, последствия другого нетравматического внутричерепного кровоизлияния, последствия инфаркта мозга, последствия инсульта, не уточненные как кровоизлияние или инфаркт мозга', u'7.4.3', u'I69.0 - I69.4'),
                (u'аневризма брюшной аорты', u'7.4.4', u'I71.3 - I71.4'),
                (u'Болезни органов дыхания', u'8', u'J00 - J98'),
                (u'в том числе: вирусная пневмония, пневмония, вызванная Streptococcus pneumonia, пневмония, вызванная Haemophilus influenza, бактериальная пневмония, пневмония, вызванная другими инфекционными возбудителями, пневмония при болезнях, классифицированных в других рубриках, пневмония без уточнения возбудителя', u'8.1', u'J12 - J18'),
                (u'бронхит, не уточненный как острый и хронический, простой и слизисто-гнойный хронический бронхит, хронический бронхит неуточненный, эмфизема', u'8.2', u'J40 - J43'),
                (u'другая хроническая обструктивная легочная болезнь, астма, астматический статус, бронхоэктатическая болезнь', u'8.3', u'J44 - J47'),
                (u'Болезни органов пищеварения', u'9', u'K00 - K93'),
                (u'в том числе: язва желудка, язва двенадцатиперстной кишки', u'9.1', u'K25, K26'),
                (u'гастрит и дуоденит', u'9.2', u'K29'),
                (u'неинфекционный энтерит и колит', u'9.3', u'K50 - K52'),
                (u'другие болезни кишечника', u'9.4', u'K55 - K63'),
                (u'Болезни мочеполовой системы', u'10', u'N00 - N99'),
                (u'в том числе: гиперплазия предстательной железы, воспалительные болезни предстательной железы, другие болезни предстательной железы', u'10.1', u'N40 - N42'),
                (u'доброкачественная дисплазия молочной железы', u'10.2', u'N60'),
                (u'воспалительные болезни женских тазовых органов', u'10.3', u'N70 - N77'),
                (u'Прочие заболевания', u'11', u'')
                ]

healthGroupToResults = {
    '1': ['317', '321', '327', '332', '337', '343', '347', '352', '375'],
    '2': ['318', '322', '328', '333', '338', '344', '348', '353', '361', '365', '369', '376', '378'],
    '3': ['319', '323', '329', '334', '339', '345', '349', '354', '362', '366', '370', '377', '379'],
    u'3а': ['355', '357', '373'],
    u'3б': ['356', '358', '374'],
    '4': ['320', '324','330', '335', '340', '350', '363', '367', '371'],
    '5': ['325', '331', '336', '341', '351', '364', '368', '372' ]
}


def specialityName(specialityId):
    specialityRecord = QtGui.qApp.db.getRecord('rbSpeciality', 'name', specialityId)
    if specialityRecord:
        return forceString(specialityRecord.value('name'))
    else:
        return '{%d}'%specialityId


def actionTypeName(actionTypeId):
    actionTypeRecord = QtGui.qApp.db.getRecord('ActionType', 'name', actionTypeId)
    if actionTypeRecord:
        return forceString(actionTypeRecord.value('name'))
    else:
        return '{%d}'%actionTypeId


class CF131Dialog(CEventEditDialog, Ui_Dialog, CTableSummaryActionsMenuMixin):
    # типы диагнозов
    dtFinish = 0 # Заключительный
    dtBase   = 1 # Основной
    dfFinished = 1  # Заключительный
    dfAccomp = 2 # Сопутствующий
#    dfMapToCode   = {dtFinish:'1', dtBase:'2', dfAccomp:'9'}
#    dfMapFromCode = {'1': dtFinish, '2':dtBase, '9':dfAccomp}

    @pyqtSignature('')
    def on_actActionEdit_triggered(self): CTableSummaryActionsMenuMixin.on_actActionEdit_triggered(self)
    @pyqtSignature('')
    def on_actAPActionAddSuchAs_triggered(self): CTableSummaryActionsMenuMixin.on_actAPActionAddSuchAs_triggered(self)
    @pyqtSignature('')
    def on_actDeleteRow_triggered(self): CTableSummaryActionsMenuMixin.on_actDeleteRow_triggered(self)
    @pyqtSignature('')
    def on_actUnBindAction_triggered(self): CTableSummaryActionsMenuMixin.on_actUnBindAction_triggered(self)

    def __init__(self, parent):
# ctor
        CEventEditDialog.__init__(self, parent)
        self.__workRecord   = None

        self.availableDiagnostics = []
        self.mapSpecialityIdToDiagFilter = {}

# create models
        self.addModels('WorkHurts', CWorkHurtsModel(self))
        self.addModels('WorkHurtFactors', CWorkHurtFactorsModel(self))
        #self.modelWorkHurts.setFactorsModel(self.modelWorkHurtFactors)
        self.addModels('Diagnostics', CF131DiagnosticsModel(self))
        self.addModels('ActionsSummary', CF131ActionsSummaryModel(self, True))
        self.addModels('Export', CEventExportTableModel(self))
        self.addModels('Export_FileAttach', CAdvancedExportTableModel(self))
        self.addModels('Export_VIMIS', CAdvancedExportTableModel(self))

# ui
        self.addObject('actEditClient', QtGui.QAction(u'Открыть регистрационную карточку', self))
        self.addObject('actPortal_Doctor', QtGui.QAction(u'Перейти на портал врача', self))
        self.addObject('actShowAttachedToClientFiles', getAttachAction('Client_FileAttach',  self))
        self.addObject('actShowContingentsClient', QtGui.QAction(u'Показать все наблюдаемые контингенты', self))
        self.addObject('actOpenClientVaccinationCard', QtGui.QAction(u'Открыть прививочную карту', self))
        self.addObject('actSurveillancePlanningClients', QtGui.QAction(u'Контрольная карта диспансерного наблюдения', self))
        self.setupDiagnosticsMenu()
        # self.setupActionsMenu()

        self.addObject('btnPrint', getPrintButton(self, ''))
        # self.addObject('btnMedicalCommission', QtGui.QPushButton(u'ВК', self))
        self.addObject('btnPrintMedicalDiagnosis', getPrintButton(self, '', u'Врачебный диагноз'))
        self.addObject('btnPlanning', QtGui.QPushButton(u'Планировщик', self))
        self.addObject('btnRelatedEvent', QtGui.QPushButton(u'Связанные события', self))

        self.createSaveAndCreateAccountButton()

        self.setupUi(self)
#        self.statusBar.payStatus = QtGui.QLabel(self.statusBar)
#        self.statusBar.payStatus.setFrameStyle(QtGui.QFrame.StyledPanel)
#        self.statusBar.addPermanentWidget(self.statusBar.payStatus)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setWindowTitleEx(u'Осмотр Ф.131')
        self.setMedicalDiagnosisContext()
        self.tabMes.setEventEditor(self)

        self.tabStatus.setEventEditor(self)
        self.tabMedicalDiagnosis.setEventEditor(self)
        self.tabDiagnostic.setEventEditor(self)
        self.tabCure.setEventEditor(self)
        self.tabMisc.setEventEditor(self)
        self.tabCash.setEventEditor(self)
        self.tabStatus.setActionTypeClass(0)
        self.tabDiagnostic.setActionTypeClass(1)
        self.tabCure.setActionTypeClass(2)
        self.tabMisc.setActionTypeClass(3)
        self.tabAmbCard.setEventEditor(self)

        self.buttonBox.addButton(self.btnPrint, QtGui.QDialogButtonBox.ActionRole)
        # self.buttonBox.addButton(self.btnMedicalCommission, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnPrintMedicalDiagnosis, QtGui.QDialogButtonBox.ActionRole)
        if QtGui.qApp.defaultKLADR()[:2] in ['23', '01']:
            self.buttonBox.addButton(self.btnPlanning, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnRelatedEvent, QtGui.QDialogButtonBox.ActionRole)
        self.setupActionSummarySlots()
# tables to rb and combo-boxes

        self.setupSaveAndCreateAccountButton()

# assign models
        self.tblWorkHurts.setModel(self.modelWorkHurts)
        self.tblWorkHurtFactors.setModel(self.modelWorkHurtFactors)
        self.tblInspections.setModel(self.modelDiagnostics)
        self.tblActions.setModel(self.modelActionsSummary)
        self.modelActionsSummary.addModel(self.tabStatus.modelAPActions)
        self.modelActionsSummary.addModel(self.tabDiagnostic.modelAPActions)
        self.modelActionsSummary.addModel(self.tabCure.modelAPActions)
        self.modelActionsSummary.addModel(self.tabMisc.modelAPActions)
        self.tabCash.addActionModel(self.tabStatus.modelAPActions)
        self.tabCash.addActionModel(self.tabDiagnostic.modelAPActions)
        self.tabCash.addActionModel(self.tabCure.modelAPActions)
        self.tabCash.addActionModel(self.tabMisc.modelAPActions)
        self.setModels(self.tblExport, self.modelExport, self.selectionModelExport)
        self.setModels(self.tblExport_FileAttach, self.modelExport_FileAttach, self.selectionModelExport_FileAttach)
        self.setModels(self.tblExport_VIMIS, self.modelExport_VIMIS, self.selectionModelExport_VIMIS)

# popup menus
        self.txtClientInfoBrowser.actions.append(self.actEditClient)
        self.txtClientInfoBrowser.actions.append(self.actPortal_Doctor)
        self.txtClientInfoBrowser.actions.append(self.actShowAttachedToClientFiles)
        self.txtClientInfoBrowser.actions.append(self.actShowContingentsClient)
        self.txtClientInfoBrowser.actions.append(self.actOpenClientVaccinationCard)
        self.txtClientInfoBrowser.actions.append(self.actSurveillancePlanningClients)
        self.actOpenClientVaccinationCard.setEnabled(QtGui.qApp.userHasAnyRight([urCanReadClientVaccination, urCanEditClientVaccination]))
        self.actEditClient.setEnabled(QtGui.qApp.userHasAnyRight([urAdmin, urRegTabWriteRegistry, urRegTabReadRegistry]))
        self.tblWorkHurts.addPopupDelRow()
        self.tblWorkHurtFactors.addPopupDelRow()
        self.tblInspections.setPopupMenu(self.mnuDiagnostics)
        self.tblInspections.setDelRowsIsExposed(lambda rowsExp: not any(map(self.modelDiagnostics.isExposed, rowsExp)))
        self.tblInspections.installEventFilter(self)
        # self.tblActions.setPopupMenu(self.mnuAction)
        # self.addObject('qshcActionsEdit', QtGui.QShortcut('F4', self.tblActions, self.on_actActionEdit_triggered))
        # self.qshcActionsEdit.setContext(Qt.WidgetShortcut)
        #
        # QObject.connect(self.actActionEdit, SIGNAL('triggered()'), self.on_actActionEdit_triggered)
        #
        # self.addObject('qshcAPActionAddSuchAs', QtGui.QShortcut(QtGui.QKeySequence('F2'), self.tblActions, self.on_actAPActionAddSuchAs_triggered))
        # self.qshcAPActionAddSuchAs.setContext(Qt.WidgetShortcut)
        # QObject.connect(self.actActionAddSuchAs, SIGNAL('triggered()'), self.on_actAPActionAddSuchAs_triggered)
        #
        # QObject.connect(self.actDeleteRow, SIGNAL('triggered()'), self.on_actDeleteRow_triggered)
        CTableSummaryActionsMenuMixin.__init__(self)

# default values

        self.tblActions.enableColsHide()
        self.tblActions.enableColsMove()
        self.tblExport.enableColsHide()
        self.tblExport.enableColsMove()

        self.tblExport_FileAttach.enableColsHide()
        self.tblExport_FileAttach.enableColsMove()

        self.tblExport_VIMIS.enableColsHide()
        self.tblExport_VIMIS.enableColsMove()

# done
        self.setupDirtyCather()
        self.setIsDirty(False)
        self.blankMovingIdList = []
        self.prolongateEvent = False
        self.prevEventId = None
        self.tabNotes.setEventEditor(self)

        self.postSetupUi()
        if hasattr(self, 'edtEndDate'):
            self.edtEndDate.setEnabled(QtGui.qApp.userHasRight(urEditEndDateEvent))
        if hasattr(self, 'edtEndTime'):
            self.edtEndTime.setEnabled(QtGui.qApp.userHasRight(urEditEndDateEvent))
        self.btnPrintMedicalDiagnosis.setVisible(False)


    def destroy(self):
        pass


    def setupDiagnosticsMenu(self):
        self.mnuDiagnostics = QtGui.QMenu(self)
        self.mnuDiagnostics.setObjectName('mnuDiagnostics')
        self.addObject('actAddChronicDiseases', QtGui.QAction(u'Добавить хронические диагнозы', self))
        self.actDiagnosticsAddBase = QtGui.QAction(u'Добавить осмотр', self)
        self.actDiagnosticsAddBase.setObjectName('actDiagnosticsAddBase')
        self.actDiagnosticsAddAccomp = QtGui.QAction(u'Добавить сопутствующий диагноз', self)
        self.actDiagnosticsAddAccomp.setObjectName('actDiagnosticsAddAccomp')
        self.actDiagnosticsRemove = QtGui.QAction(u'Удалить запись', self)
        self.actDiagnosticsRemove.setObjectName('actDiagnosticsRemove')
        self.mnuDiagnostics.addAction(self.actDiagnosticsAddBase)
        self.mnuDiagnostics.addAction(self.actDiagnosticsAddAccomp)
        self.mnuDiagnostics.addAction(self.actAddChronicDiseases)
        self.mnuDiagnostics.addSeparator()
        self.mnuDiagnostics.addAction(self.actDiagnosticsRemove)

    def setFinalDiagnosticsMenuControlsState(self):
        """
        Активность пункта меню "Вставить хронические диагнозы" в таблице Диагнозов
        """
        self.actAddChronicDiseases.setEnabled(False)
        current = self.tblInspections.currentItem()
        if current and current.value('diagnosisType_id') == self.modelDiagnostics.diagnosisTypeCol.codeToId(CF131Dialog.dfFinished):
            self.actAddChronicDiseases.setEnabled(True)

    def eventFilter(self, obj, event):
        if obj == self.tblInspections and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Down:
                if self.modelDiagnostics.rowCount() > 0:
                    current_index = self.tblInspections.currentIndex()
                    if current_index.isValid() and current_index.row() == self.modelDiagnostics.rowCount() - 1:
                        self.on_actDiagnosticsAddAccomp_triggered()
                        return True
        return CEventEditDialog.eventFilter(self, obj, event)

    # def setupActionsMenu(self):
    #     self.addObject('mnuAction', QtGui.QMenu(self))
    #     self.addObject('actActionEdit', QtGui.QAction(u'Перейти к редактированию', self))
    #     self.actActionEdit.setShortcut(Qt.Key_F4)
    #     self.mnuAction.addAction(self.actActionEdit)
    #
    #     self.addObject('actActionAddSuchAs', QtGui.QAction(u'Добавить такой-же', self))
    #     self.actActionAddSuchAs.setShortcut(Qt.Key_F2)
    #     self.mnuAction.addAction(self.actActionAddSuchAs)
    #
    #     self.addObject('actUnBindAction', QtGui.QAction(u'Открепить мероприятие', self))
    #     self.mnuAction.addAction(self.actUnBindAction)
    #
    #     self.addObject('actDeleteRow', QtGui.QAction(u'Удалить запись', self))
    #     self.mnuAction.addAction(self.actDeleteRow)


    @pyqtSignature('int')
    def on_tabWidget_currentChanged(self, index):
        widget = self.tabWidget.widget(index)
        if widget is not None:
            focusProxy = widget.focusProxy()
            if focusProxy:
                focusProxy.setFocus(Qt.OtherFocusReason)
        self.btnPrintMedicalDiagnosisEnabled(index)
        if index == 1 and self.eventTypeId:
            self.tabMes.setMESServiceTemplate(self.eventTypeId)
        if index == 7:  # amb card page
            self.tabAmbCard.resetWidgets()


    @pyqtSignature('')
    def on_actActionEdit_triggered(self):
        index = self.tblActions.currentIndex()
        row = index.row()
        if 0 <= row < len(self.modelActionsSummary.itemIndex):
            page, row = self.modelActionsSummary.itemIndex[row]
            if page in [0, 1, 2, 3]:
                self.tabWidget.setCurrentIndex(page+3)
            tbl = [self.tabStatus.tblAPActions, self.tabDiagnostic.tblAPActions, self.tabCure.tblAPActions, self.tabMisc.tblAPActions][page]
            tbl.setCurrentIndex(tbl.model().index(row, 0))
            
            
    @pyqtSignature('')
    def on_actAPActionAddSuchAs_triggered(self):
        index = self.tblActions.currentIndex()
        rowSummary = index.row()
        columnSummary = index.column()
        if 0 <= rowSummary < len(self.modelActionsSummary.itemIndex):
            page, row = self.modelActionsSummary.itemIndex[rowSummary]
            tbl = [self.tabStatus.tblAPActions, self.tabDiagnostic.tblAPActions, self.tabCure.tblAPActions, self.tabMisc.tblAPActions][page]
            model = tbl.model()
            if 0<=row<model.rowCount()-1:
                record = model._items[row][0]
                actionTypeId = forceRef(record.value('actionType_id'))
                index = model.index(model.rowCount()-1, 0)
                if model.setData(index, toVariant(actionTypeId)):
                    newRowSummary = len(model.items())-row+rowSummary-1
                    indexSummary = self.tblActions.model().index(newRowSummary, columnSummary)
                    self.tblActions.setCurrentIndex(indexSummary)


    @pyqtSignature('')
    def on_actDeleteRow_triggered(self):
        rowsSortByPagesTables = {}
        rows = self.tblActions.getSelectedRows()
        for row in rows:
            if 0 <= row < len(self.modelActionsSummary.itemIndex):
                page, row = self.modelActionsSummary.itemIndex[row]
                tbl = [self.tabStatus.tblAPActions, self.tabDiagnostic.tblAPActions, self.tabCure.tblAPActions, self.tabMisc.tblAPActions][page]
                if not tbl.model().isLockedOrExposed(row):
                    rowsList = rowsSortByPagesTables.get(tbl, None)
                    if rowsList:
                        rowsList.append(row)
                    else:
                        rowsSortByPagesTables[tbl] = [row]
        for tbl in rowsSortByPagesTables:
            rows = rowsSortByPagesTables.get(tbl, [])
            rows.sort(reverse=True)
            for row in rows:
                tbl.model().removeRow(row)
            tbl.emitDelRows()


    def prepare(self, clientId, eventTypeId, orgId, personId, eventSetDatetime, eventDatetime, weekProfile,
                numDays, externalId, assistantId, curatorId, flagHospitalization = False,
                actionTypeIdValue = None, valueProperties = [], tissueTypeId=None, selectPreviousActions=False,
                relegateOrgId = None, relegatePersonId=None, diagnos = None, financeId = None,
                protocolQuoteId = None, actionByNewEvent = [], order = 1,  actionListToNewEvent = [],
                typeQueue = -1, docNum=None, relegateInfo=[], plannedEndDate=None, mapJournalInfoTransfer=[], voucherParams={}, isEdit=False):
        self.setPersonId(personId)
        dlg = CPreF131Dialog(self, self.personSpecialityId)
        try:
            eventDate = eventDatetime.date() if isinstance(eventDatetime, QDateTime) else eventDatetime
            if not eventDate and eventSetDatetime:
                eventDate = eventSetDatetime.date() if isinstance(eventSetDatetime, QDateTime) else eventSetDatetime
            else:
                eventDate = QDate.currentDate()
            dlg.setBegDateEvent(eventSetDatetime.date() if isinstance(eventSetDatetime, QDateTime) else eventSetDatetime)
            presentActionTypes = []
            maxOccursLimitActionTypes = []
            for item in self.modelActionsSummary.items():
                actionTypeId = forceString(item.value('actionType_id'))
                if actionTypeId not in presentActionTypes:
                    presentActionTypes.append(actionTypeId)
                    if not self.checkMaxOccursLimit(actionTypeId) and actionTypeId not in maxOccursLimitActionTypes:
                        maxOccursLimitActionTypes.append(actionTypeId)
            dlg.prepare(clientId, eventTypeId, eventDate, tissueTypeId, presentActionTypes = presentActionTypes, maxOccursLimitActionTypes = maxOccursLimitActionTypes)
            if dlg.warnAboutUnmatchedSpeciality:
                widget = QtGui.qApp.activeModalWidget() or QtGui.qApp.mainWindow or None
                QtGui.QMessageBox.critical( widget,
                                            u'Произошла ошибка',
                                            u'В планировщике отсутствует специальность ответственного лица',
                                            QtGui.QMessageBox.Ok)
                return False
            if dlg.diagnosticsTableIsNotEmpty() or dlg.actionsTableIsNotEmpty():
                if not dlg.exec_():
                    return False
            if not isEdit:
                self.eventSetDateTime = eventSetDatetime if isinstance(eventSetDatetime, QDateTime) else QDateTime(eventSetDatetime)
                self.eventDate = eventDatetime.date() if isinstance(eventDatetime, QDateTime) else eventDatetime
                self.setOrgId(orgId if orgId else QtGui.qApp.currentOrgId())
                self.setEventTypeId(eventTypeId)
                self.setClientId(clientId)
                self.prolongateEvent = True if actionByNewEvent else False
                self.tabNotes.setNotesEx(externalId, assistantId, curatorId, relegateOrgId, relegatePersonId, clientId, relegateInfo)
                self.setExternalId(externalId)
    #            self.setPersonId(personId)
                self.cmbPerson.setValue(personId)
                setPerson = getEventSetPerson(self.eventTypeId)
                if setPerson == 0:
                    self.setPerson = personId
                elif setPerson == 1:
                    self.setPerson = QtGui.qApp.userId
                self.edtBegDate.setDate(self.eventSetDateTime.date())
                self.edtBegTime.setTime(eventSetDatetime.time() if isinstance(eventSetDatetime, QDateTime) else QTime())
                self.edtEndDate.setDate(self.eventDate)
                self.edtEndTime.setTime(eventDatetime.time() if isinstance(eventDatetime, QDateTime) else QTime())
                self.setEnabledChkCloseEvent(eventDatetime)
                self.edtPrevDate.setDate(QDate())
                self.chkPrimary.setChecked(getEventIsPrimary(eventTypeId)==0)
                self.cmbContract.setCurrentIndex(0)
                self.edtNextDate.setDate(getNextEventDate(self.eventTypeId, self.eventSetDateTime.date()))
                self.setOrgStructAndPersonsInCmbPersons(eventTypeId)
                self.prepareDiagnostics(dlg.diagnostics())
                diagnosticResultId = QtGui.qApp.session("F131_DiagnosticResultIdByPurpose%d" % self.eventPurposeId)
                if diagnosticResultId:
                    for item in self.modelDiagnostics.items():
                        if forceInt(item.value("diagnosisType_id")) == 1:
                            item.setValue('result_id', QVariant(diagnosticResultId))
            self.prepareActions(dlg.actions(), isEdit=isEdit)
            self.setFocusToWidget(self.tblInspections)
            self.setIsDirty(False)
            self.tabNotes.setEventEditor(self)
            return self.checkEventCreationRestriction() and self.checkDeposit()
        finally:
            dlg.deleteLater()


    def setPersonId(self, personId):
        self.personId = personId
        self.personSpecialityId = None
        personRecord = QtGui.qApp.db.getRecord('Person', 'speciality_id', personId)
        if personRecord:
            self.personSpecialityId = forceRef(personRecord.value('speciality_id'))


    def newDiagnosticRecord(self, template, boolSetRecord = True):
        finishDiagnosisTypeId, baseDiagnosisTypeId, accompDiagnosisTypeId = self.modelDiagnostics.diagnosisTypeCol.ids
        result = self.tblInspections.model().getEmptyRecord()
        result.setValue('speciality_id',  template.value('speciality_id'))
        if boolSetRecord:
            result.setValue('diagnosisType_id',  template.value('diagnosisType_id'))
        else:

            specialityId = forceRef(template.value('speciality_id'))
            mayEngageGP  = forceBool(template.value('mayEngageGP'))
            if (self.personSpecialityId == specialityId
                or mayEngageGP and self.personSpecialityId == QtGui.qApp.getGPSpecialityId()
               ):
                if any( forceInt(item.value('diagnosisType_id')) == finishDiagnosisTypeId
                        for item in self.modelDiagnostics.items()
                      ):
                    diagnosisTypeId = baseDiagnosisTypeId
                else:
                    diagnosisTypeId = finishDiagnosisTypeId
            if self.personSpecialityId == forceRef(template.value('speciality_id')):
                result.setValue('person_id', QVariant(self.personId))
                result.setValue('diagnosisType_id', QVariant(diagnosisTypeId))
            else:
                result.setValue('diagnosisType_id', QVariant(baseDiagnosisTypeId))
                result.setValue('person_id', QVariant(template.value('person_id')))
        result.setValue('setDate',        QVariant(self.eventSetDateTime))
        if forceDate(template.value('endDate')):
            result.setValue('endDate',        QVariant(template.value('endDate')))
        else:
            result.setValue('endDate', QVariant(self.eventDate))
        result.setValue('healthGroup_id', template.value('defaultHealthGroup_id'))
        result.setValue('MKB',            template.value('defaultMKB'))
        result.setValue('defaultMKB',     template.value('defaultMKB'))
        result.setValue('actuality',      template.value('actuality'))
        result.setValue('visitType_id',   template.value('visitType_id'))
        if forceInt(template.value('scene_id')):
            sceneId = template.value('scene_id')
        else:
            sceneId = getEventSceneId(self.eventTypeId)
        result.setValue('scene_id',       toVariant(sceneId) if sceneId else QtGui.qApp.db.translate('rbScene', 'code',  '1', 'id'))
        result.setValue('selectionGroup', template.value('selectionGroup'))
        result.setValue('payStatus',      CPayStatus.initial)
        result.setValue('dispanser_id', template.value('defaultDispanser_id'))
        return result


    def prepareDiagnostics(self, diagnostics, addVisit = False):
        for record in diagnostics:
            if forceInt(record.value('include')) != 0 or addVisit:
                self.modelDiagnostics.items().append(self.newDiagnosticRecord(record, False))
        self.modelDiagnostics.reset()


    def prepareActions(self, presetActions, isEdit=False):

        def addActionTypeRowAndEmitSignal(model, actionTypeId, amount):
            model.addRow(actionTypeId, amount)
            if isEdit:
                model.emit(QtCore.SIGNAL('onAddNewAction(int)'), len(model.items()) - 1)
                
        def addActionType(actionTypeId, amount):
            for iModel, model in enumerate([self.tabStatus.modelAPActions,
                          self.tabDiagnostic.modelAPActions,
                          self.tabCure.modelAPActions,
                          self.tabMisc.modelAPActions]):
                if actionTypeId in model.actionTypeIdList:
                    addActionTypeRowAndEmitSignal(model, actionTypeId, amount)
                    i = self.modelActionsSummary.itemIndex.index((iModel, model.rowCount()-2))
                    self.onActionChanged(i)
                    break

        for record in presetActions:
            if forceInt(record.value('include')) != 0:
                actionTypeId = forceRef(record.value('actionType_id'))
                #actionAmount = forceDouble(record.value('amount'))
                addActionType(actionTypeId, 1.0)


    def setRecord(self, record):
        CEventEditDialog.setRecord(self, record)
        setDateEditValue(self.edtPrevDate,      record, 'prevEventDate')
        setDatetimeEditValue(self.edtBegDate, self.edtBegTime, record, 'setDate')
        setDatetimeEditValue(self.edtEndDate, self.edtEndTime, record, 'execDate')
        setRBComboBoxValue(self.cmbPerson,      record, 'execPerson_id')
        setRBComboBoxValue(self.cmbResult,      record, 'result_id')
        setDateEditValue(self.edtNextDate,      record, 'nextEventDate')
        self.chkPrimary.setChecked(forceInt(record.value('isPrimary'))==1)
        self.setExternalId(forceString(record.value('externalId')))
        self.setPersonId(self.cmbPerson.value())
        setRBComboBoxValue(self.cmbContract,    record, 'contract_id')
        self.setPerson = forceRef(record.value('setPerson_id'))
        self._updateNoteByPrevEventId()
        self.blankMovingIdList = []
        dlg = CPreF131Dialog(None, self.personSpecialityId)
        try:
            dlg.setBegDateEvent(self.eventSetDateTime.date() if isinstance(self.eventSetDateTime, QDateTime) else self.eventSetDateTime)
            dlg.prepare(self.clientId, self.eventTypeId, self.eventSetDateTime.date(), None)
            if dlg.warnAboutUnmatchedSpeciality:
                widget = QtGui.qApp.activeModalWidget() or QtGui.qApp.mainWindow or None
                QtGui.QMessageBox.critical( widget,
                                            u'Произошла ошибка',
                                            u'В планировщике отсутствует специальность ответственного лица',
                                            QtGui.QMessageBox.Ok)
            self.tabNotes.setNotes(record)
            self.tabNotes.setEventEditor(self)
            self.loadDiagnostics(dlg.diagnostics(), self.itemId())
            self.tabMedicalDiagnosis.load(self.itemId())
#            self.loadActions(dlg.actions())
            self.updateMesMKB()
            self.setOrgStructAndPersonsInCmbPersons(self.eventTypeId)
            self.tabMes.setRecord(record)
            self.loadActions()
            self.setFocusToWidget(self.tblInspections)
            self.tabCash.load(self.itemId())
            self.on_cmbResult_currentIndexChanged()
            self.setIsDirty(False)
            self.protectClosedEvent()
            iniExportEvent(self)
            self.actSurveillancePlanningClients.setEnabled(bool(self.getDiagnosticIdList(self.clientId)))
        finally:
            dlg.deleteLater()
            self.btnRelatedEventHighlight()

    def setOrgStructAndPersonsInCmbPersons(self, eventTypeId):
        orgstructureListByEventtype = getOrgstructureListByEventtypeId(eventTypeId)
        personListByEventtype = getPersonListByEventtypeId(eventTypeId)
        self.cmbPerson.setOrgStructureList(orgstructureListByEventtype)
        self.cmbPerson.setPersonIdList(personListByEventtype)
        self.modelDiagnostics._cols[self.modelDiagnostics.getColIndex('person_id')].orgStructureIdList = orgstructureListByEventtype
        self.modelDiagnostics._cols[self.modelDiagnostics.getColIndex('person_id')].personIdList = personListByEventtype
        self.modelActionsSummary._cols[
            self.modelActionsSummary.getColIndex('person_id')].orgStructureIdList = orgstructureListByEventtype
        self.modelActionsSummary._cols[
            self.modelActionsSummary.getColIndex('person_id')].personIdList = personListByEventtype

        #self.modelDiagnostics._cols[2].F131flag = True

    def setLeavedAction(self, actionTypeIdValue, params = {}):
        pass


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
            self.loadDiagnostics([], eventId)


    def loadDiagnostics(self, diagnostics, eventId):
        def selectionGroup(i):
            return forceInt(diagnostics[i].value('selectionGroup'))

        def getDiagnosisType(diagnosisTypeId):
            if diagnosisTypeId in self.modelDiagnostics.diagnosisTypeCol.ids:
                return self.modelDiagnostics.diagnosisTypeCol.ids.index(diagnosisTypeId)
            else:
                return 2

        n = len(diagnostics)
        db = QtGui.qApp.db
        table = db.table('Diagnostic')
        tableVisit  = db.table('Visit')
        tablePerson = db.table('Person')
        isDiagnosisManualSwitch = self.modelDiagnostics.manualSwitchDiagnosis()
        joinVisitPerson = tableVisit.leftJoin(tablePerson, tablePerson['id'].eq(tableVisit['person_id']))
        rawItems = db.getRecordList(table, '*', [table['deleted'].eq(0), table['event_id'].eq(eventId)], 'id')
        mapSpecialityIdToRows = {}
        gpSpecialityId = QtGui.qApp.getGPSpecialityId()

        for i, record in enumerate(diagnostics):
            specialityId = forceRef(record.value('speciality_id'))
            mapSpecialityIdToRows.setdefault(specialityId, []).append(i)

        for i, record in enumerate(diagnostics):
            mayEngageGP  = forceBool(record.value('mayEngageGP'))
            if mayEngageGP:
                mapSpecialityIdToRows.setdefault(gpSpecialityId, []).append(i)

        mapSpecialityIdToIdx = {}
        for specialityId in mapSpecialityIdToRows.iterkeys():
            mapSpecialityIdToIdx[specialityId] = 0

        specInTemplate = [None]*n
        for specialityId, rows in mapSpecialityIdToRows.iteritems():
            specInTemplate[rows[0]] = specialityId

        # группируем записи по группам по id специальности
        if diagnostics:
            rawSorted = [ [] for record in diagnostics ]
        else:
            rawSorted = [[]]
        for record in rawItems:
            specialityId = forceRef(record.value('speciality_id'))
            if specialityId and (specialityId in mapSpecialityIdToRows):
                idx = mapSpecialityIdToIdx[specialityId]
                if ( idx<len(mapSpecialityIdToRows[specialityId])):
                    mapSpecialityIdToIdx[specialityId] = idx + 1
                else:
                    idx = -1
                i = mapSpecialityIdToRows[specialityId][idx]
                diagnosisTypeId = record.value('diagnosisType_id')
                diagnosisId     = record.value('diagnosis_id')
                MKB             = db.translate('Diagnosis', 'id', forceRef(diagnosisId), 'MKB')
                exSubclassMKB = db.translate('Diagnosis', 'id', forceRef(diagnosisId), 'exSubclassMKB')
                morphologyMKB   = db.translate('Diagnosis', 'id', forceRef(diagnosisId), 'morphologyMKB')
                setDate         = forceDate(record.value('setDate'))
                newRecord = self.modelDiagnostics.getEmptyRecord()
                copyFields(newRecord, record)
                newRecord.setValue('diagnosisTypeId', diagnosisTypeId)
                if MKB:
                    newRecord.setValue('MKB',           MKB)
                if morphologyMKB:
                    newRecord.setValue('morphologyMKB', morphologyMKB)
                newRecord.setValue('exSubclassMKB', exSubclassMKB)
                self.modelDiagnostics.updateMKBTNMS(newRecord, MKB)
                self.modelDiagnostics.updateMKBToExSubclass(newRecord, MKB)
                newRecord.setValue('defaultMKB',    diagnostics[i].value('defaultMKB'))
                newRecord.setValue('actuality',     diagnostics[i].value('actuality'))
                newRecord.setValue('visitType_id',  diagnostics[i].value('visitType_id'))
                newRecord.setValue('payStatus',     CPayStatus.initial)

                currentEventId = self.itemId()
                if eventId != currentEventId:
                    newRecord.setValue('id', toVariant(None))
                    newRecord.setValue('event_id', toVariant(currentEventId))
                    newRecord.setValue('diagnosis_id', toVariant(None))
                    newRecord.setValue('handleDiagnosis', QVariant(0))
                else:
                    if isDiagnosisManualSwitch:
                        isCheckedHandleDiagnosis = checkIsHandleDiagnosisIsChecked(setDate,
                                                                                   self.clientId,
                                                                                   diagnosisId)
                        newRecord.setValue('handleDiagnosis', QVariant(isCheckedHandleDiagnosis))

                rawSorted[i].append(newRecord)
            elif not diagnostics or not (specialityId in mapSpecialityIdToRows):
                diagnosisTypeId = record.value('diagnosisType_id')
                diagnosisId     = record.value('diagnosis_id')
                MKB             = db.translate('Diagnosis', 'id', forceRef(diagnosisId), 'MKB')
                exSubclassMKB = db.translate('Diagnosis', 'id', forceRef(diagnosisId), 'exSubclassMKB')
                morphologyMKB   = db.translate('Diagnosis', 'id', forceRef(diagnosisId), 'morphologyMKB')
                setDate         = forceDate(record.value('setDate'))
                newRecord = self.modelDiagnostics.getEmptyRecord()
                copyFields(newRecord, record)
                newRecord.setValue('diagnosisTypeId', diagnosisTypeId)
                if MKB:
                    newRecord.setValue('MKB',           MKB)
                if morphologyMKB:
                    newRecord.setValue('morphologyMKB', morphologyMKB)
                newRecord.setValue('exSubclassMKB', exSubclassMKB)
                self.modelDiagnostics.updateMKBTNMS(newRecord, MKB)
                self.modelDiagnostics.updateMKBToExSubclass(newRecord, MKB)
                newRecord.setValue('payStatus',     CPayStatus.initial)

                currentEventId = self.itemId()
                if eventId != currentEventId:
                    newRecord.setValue('id', toVariant(None))
                    newRecord.setValue('event_id', toVariant(currentEventId))
                    newRecord.setValue('diagnosis_id', toVariant(None))
                    newRecord.setValue('handleDiagnosis', QVariant(0))
                else:
                    if isDiagnosisManualSwitch:
                        isCheckedHandleDiagnosis = checkIsHandleDiagnosisIsChecked(setDate,
                                                                                   self.clientId,
                                                                                   diagnosisId)
                        newRecord.setValue('handleDiagnosis', QVariant(isCheckedHandleDiagnosis))

                rawSorted[0].append(newRecord)


        # в случае обнаружения альтернативных групп (имеющих равный не 0 и не 1 код выбора)
        # оставляем только первый выбор
        for i in xrange(n):
            group = selectionGroup(i)
            if rawSorted[i] and group not in (0, 1):
                for j in xrange(i+1, n):
                    if selectionGroup(j) == group:
                        rawSorted[j] = []
        # упорядочиваем по коду типа диагноза
        for group in rawSorted:
            group.sort(key=lambda record: getDiagnosisType(forceInt(record.value('diagnosisType_id'))))
        # в пустые группы с ненулевым кодом добавляем строки из планировщика
        for i in xrange(n):
            if not rawSorted[i]:
                group = selectionGroup(i)
                needAdd = group > 0
                if group > 1:
                    for j in xrange(n):
                        if i != j and rawSorted[j] and selectionGroup(j) == group:
                            needAdd = False
                            break
                if needAdd and specInTemplate[i]:
                    rawSorted[i].append(self.newDiagnosticRecord(diagnostics[i]))

        # восстанавливаем тип диагноза (если он утрачен), устанавливаем ссылки на визиты и статусы оплаты
        finishDiagnosisTypeId, baseDiagnosisTypeId, accompDiagnosisTypeId = self.modelDiagnostics.diagnosisTypeCol.ids
        visitIdListRecord = []
        dfSceneId = getEventSceneId(self.eventTypeId)
        for group in rawSorted:
            for i, record in enumerate(group):
                diagnosisTypeId = forceRef(record.value('diagnosisType_id'))
                if i == 0 and diagnosisTypeId == accompDiagnosisTypeId:
                    diagnosisTypeId = baseDiagnosisTypeId
                    record.setValue('diagnosisType_id', toVariant(diagnosisTypeId))

                if diagnosisTypeId in (finishDiagnosisTypeId, baseDiagnosisTypeId):
#                    visitCond = [tableVisit['event_id'].eq(self.itemId()), tableVisit['person_id'].eq(record.value('person_id'))]
                    visitCond = [tableVisit['event_id'].eq(self.itemId()),
                                 tableVisit['deleted'].eq(0),
                                 tableVisit['person_id'].eq(record.value('person_id'))
                                # tablePerson['speciality_id'].eq(record.value('speciality_id'))
                                 ]
                    if visitIdListRecord:
                        visitCond.append(tableVisit['id'].notInlist(visitIdListRecord))
                    visitIdList = db.getIdList(joinVisitPerson, tableVisit['id'].name(), where=visitCond, order=tableVisit['id'].name())
                    visitId = visitIdList[0] if visitIdList else None
                    if visitId and visitId not in visitIdListRecord:
                        visitIdListRecord.append(visitId)

                    endDate = forceDate(record.value('endDate'))
                    if visitId:
                        sceneId = forceRef(db.translate(tableVisit, 'id', visitId, 'scene_id'))
                        visitTypeId = forceRef(db.translate(tableVisit, 'id', visitId, 'visitType_id'))
                        payStatus = getWorstPayStatus(forceInt(db.translate(tableVisit, 'id', visitId, 'payStatus')))

                        record.setValue('visit_id',      toVariant(visitId))
                        record.setValue('scene_id',      toVariant(sceneId))
                        record.setValue('visitType_id',  toVariant(visitTypeId))
                        record.setValue('payStatus',     toVariant(payStatus))
                    if not endDate and not visitId:
                        sceneId = forceRef(diagnostics[i].value('scene_id'))
                        if not sceneId:
                            sceneId = dfSceneId if dfSceneId else forceRef(QtGui.qApp.db.translate('rbScene', 'code',  '1', 'id'))
                            record.setValue('scene_id', toVariant(sceneId))
                        visitTypeId = forceRef(diagnostics[i].value('visitType_id'))
                sceneId = forceRef(record.value('scene_id'))
                if not sceneId:
                    record.setValue('scene_id', toVariant(dfSceneId) if dfSceneId else QtGui.qApp.db.translate('rbScene', 'code',  '1', 'id'))

        # объединяем в один список
        items = []
        for group in rawSorted:
            for item in group:
                item._dirty = False
                items.append(item)
        # и устанавливаем в модель:
        self.modelDiagnostics.setItems(items)
        self.modelDiagnostics.cols()[self.modelDiagnostics.getColIndex('healthGroup_id')].setFilter(getHealthGroupFilter(forceString(self.clientBirthDate.toString('yyyy-MM-dd')), forceString(self.eventSetDateTime.date().toString('yyyy-MM-dd'))))


    def getRecord(self):
        if not self.record():
            record = CEventEditDialog.getRecord(self)
        else:
            record = self.record()
            record._dirty = True
        showTime = getEventShowTime(self.eventTypeId)
        self.getShowButtonAccount()
        self.getShowButtonTemperatureList()
        self.getShowButtonNomenclatureExpense()
        self.getShowButtonJobTickets()

        getRBComboBoxValue(self.cmbContract,    record, 'contract_id')
        getDateEditValue(self.edtPrevDate,      record, 'prevEventDate')
        getDatetimeEditValue(self.edtBegDate, self.edtBegTime, record, 'setDate', showTime)
        record.setValue('setPerson_id', self.setPerson)
        getDatetimeEditValue(self.edtEndDate, self.edtEndTime, record, 'execDate', showTime)
        getRBComboBoxValue(self.cmbPerson,      record, 'execPerson_id')
        getRBComboBoxValue(self.cmbResult,      record, 'result_id')
        getDateEditValue(self.edtNextDate,      record, 'nextEventDate')
        record.setValue('isPrimary', toVariant(1 if self.chkPrimary.isChecked() else 2))
        if self.prolongateEvent:
            record.setValue('order', toVariant(5))
        self.setCheckedChkCloseEvent()
        self.tabMes.getRecord(record)
        self.tabNotes.getNotes(record, self.eventTypeId)
        # Это хак: удаляем payStatus из записи
        result = type(record)(record) # copy record
        result.remove(result.indexOf('payStatus'))
        return result


    def saveInternals(self, eventId):
        self.saveWorkRecord()
        self.saveDiagnostics(eventId)
        self.tabMedicalDiagnosis.save(eventId)
        self.tabMes.save(eventId)
        setAskedClassValueForDiagnosisManualSwitch(None)
        self.updateVisits(eventId)
        self.saveActions(eventId)
        self.tabCash.save(eventId)
        self.saveBlankUsers(self.blankMovingIdList)
        self.tabNotes.saveAttachedFiles(eventId)
        self.saveTrailerActions(eventId)


    def saveTrailerActions(self, eventId):
        if self.trailerActions:
            for action in self.trailerActions:
                prevActionId = self.trailerIdList.get(action.trailerIdx - 1, None)
                action.getRecord().setValue('prevAction_id', toVariant(prevActionId))
                action.save(eventId)


    def afterSave(self):
        CEventEditDialog.afterSave(self)
        QtGui.qApp.session("F131_resultIdByPurpose%d" % self.eventPurposeId, self.cmbResult.value())
        for item in self.modelDiagnostics.items():
            if forceInt(item.value("diagnosisType_id")) == 1:
                QtGui.qApp.session("F131_DiagnosticResultIdByPurpose%d" % self.eventPurposeId, forceInt(item.value("result_id")))


    def saveWorkRecord(self):
        workRecord, workRecordChanged = self.getWorkRecord()
##                if workRecordChanged and workRecord is not None:
        if workRecordChanged and workRecord:
            workRecordId = QtGui.qApp.db.insertOrUpdate('ClientWork', workRecord)
        elif workRecord:
            workRecordId = forceRef(workRecord.value('id'))
        else:
            workRecordId = None
        if workRecordId:
            self.modelWorkHurts.saveItems(workRecordId)
            self.modelWorkHurtFactors.saveItems(workRecordId)


    def saveDiagnostics(self, eventId):
        baseDiagnosisTypeId = self.modelDiagnostics.diagnosisTypeCol.ids[1]
        accompDiagnosisTypeId = self.modelDiagnostics.diagnosisTypeCol.ids[2]
        items = self.modelDiagnostics.items()
        isDiagnosisManualSwitch = self.modelDiagnostics.manualSwitchDiagnosis()
        prevId = 0
        prevItem = None
        for item in items:
            diagnosisTypeId = forceRef(item.value('diagnosisType_id'))
            if diagnosisTypeId is None:
                diagnosisTypeId = baseDiagnosisTypeId
                item.setValue('diagnosisType_id', toVariant(diagnosisTypeId))
            MKB = forceStringEx(item.value('MKB'))
            TNMS = forceStringEx(item.value('TNMS'))
            morphologyMKB = forceStringEx(item.value('morphologyMKB'))
            if diagnosisTypeId == accompDiagnosisTypeId and prevItem:
                for fieldName in ('speciality_id', 'person_id', 'setDate', 'endDate'):
                    item.setValue(fieldName, prevItem.value(fieldName) )
            diagnosisId = forceRef(item.value('diagnosis_id'))
            diagnosisId, characterId = getDiagnosisId2(
                                forceDate(item.value('endDate')),
                                forceRef(item.value('person_id')),
                                self.clientId,
                                diagnosisTypeId,
                                MKB,
                                '',
                                forceRef(item.value('character_id')),
                                forceRef(item.value('dispanser_id')),
                                None,
                                diagnosisId,
                                forceRef(item.value('id')),
                                isDiagnosisManualSwitch,
                                forceBool(item.value('handleDiagnosis')),
                                TNMS=TNMS,
                                morphologyMKB=morphologyMKB,
                                dispanserBegDate=forceDate(item.value('endDate')),
                                exSubclassMKB=forceStringEx(item.value('exSubclassMKB')))
            item.setValue('diagnosis_id', toVariant(diagnosisId))
            item.setValue('TNMS', toVariant(TNMS))
            item.setValue('character_id', toVariant(characterId))
            payStatus = forceInt(item.value('payStatus'))
            itemId = forceInt(item.value('id'))
            if prevId>itemId and payStatus == CPayStatus.initial:
                item.setValue('id', QVariant())
                prevId=0
            else:
               prevId=itemId
            prevItem = item
        self.modelDiagnostics.saveItems(eventId)


    def checkAppointments(self):
        where_id = self.cmbResult.value()
        if not where_id:
            return False
        db = QtGui.qApp.db
        smt1 = u''' select rbResult.regionalCode as reg_code
                                    from rbResult
                                    where rbResult.id = %s ''' % where_id
        query = db.query(smt1)
        reg_c = 0
        while query.next():
            record = query.record()
            if record:
                reg_c = forceInt(record.value('reg_code'))
        if reg_c not in (355, 356, 323, 324, 325, 334, 335, 336, 339, 340, 341, 345, 349, 350, 351, 357, 358, 373, 374):
            return False
        else:
            return True


    def updateVisits(self, eventId):
        db = QtGui.qApp.db
#        sceneId = forceRef(db.translate('rbScene', 'code',  '1', 'id'))
        finishDiagnosisTypeId = self.modelDiagnostics.diagnosisTypeCol.ids[0]
        baseDiagnosisTypeId = self.modelDiagnostics.diagnosisTypeCol.ids[1]
        table = db.table('Visit')
        eventVisitFinance = False
#        eventFinanceId = None
        if self.eventTypeId:
            tableEventType = db.table('EventType')
            recordEventType = db.getRecordEx(tableEventType, [tableEventType['visitFinance'], tableEventType['finance_id']], [tableEventType['visitFinance'].eq(0), tableEventType['deleted'].eq(0), tableEventType['id'].eq(self.eventTypeId)])
            if recordEventType:
                eventVisitFinance = not forceBool(recordEventType.value('visitFinance'))
#                eventFinanceId = forceRef(recordEventType.value('finance_id'))
        diagnostics  = self.modelDiagnostics.items()
        visitIdList  = []
        for diagnostic in diagnostics:
            diagnosisTypeId = forceRef(diagnostic.value('diagnosisType_id'))
            if diagnosisTypeId == finishDiagnosisTypeId or diagnosisTypeId == baseDiagnosisTypeId:
#                setDate = forceDate(diagnostic.value('setDate'))
                endDate = forceDate(diagnostic.value('endDate'))
                sceneId      = forceRef(diagnostic.value('scene_id'))
                visitTypeId  = forceRef(diagnostic.value('visitType_id'))
                specialityId = forceRef(diagnostic.value('speciality_id'))
                visitId      = forceRef(diagnostic.value('visit_id'))
                personId     = forceRef(diagnostic.value('person_id'))
                if endDate and personId and visitTypeId and sceneId:
                    financeId = None
                    if not eventVisitFinance:
                        financeId = forceRef(db.translate('Person', 'id', personId, 'finance_id'))
                    if not financeId:
                        financeId = forceRef(db.translate('Contract', 'id', self.cmbContract.value(), 'finance_id'))
                    serviceId = forceRef(db.translate('rbSpeciality', 'id', specialityId, 'service_id'))
                    CEventTypeDescription.get( self.eventTypeId).mapPlannedInspectionSpecialityIdToServiceId = {}
                    serviceId = getExactServiceId(None, self.eventServiceId, serviceId, self.eventTypeId, visitTypeId, sceneId, specialityId, self.clientSex, self.clientAge)
                    visitId = forceRef(diagnostic.value('visit_id'))
                    if visitId:
                        record = db.getRecord(table, '*', visitId)
                    else:
                        record = table.newRecord()
                    record.setValue('event_id',     toVariant(eventId))
                    record.setValue('scene_id',     toVariant(sceneId))
                    record.setValue('date',         toVariant(endDate))
                    record.setValue('visitType_id', toVariant(visitTypeId))
                    record.setValue('person_id',    toVariant(personId))
                    record.setValue('isPrimary',    toVariant(0))
                    record.setValue('finance_id',   toVariant(financeId))
                    record.setValue('service_id',   toVariant(serviceId))
                    record.setValue('deleted',      toVariant(0))
##                        record.setValue('payStatus',    toVariant(0))
                    visitId = db.insertOrUpdate(table, record)
                    visitIdList.append(visitId)
                    diagnostic.setValue('visit_id', toVariant(visitId))
        cond = [table['event_id'].eq(eventId)]
        if visitIdList:
            cond.append('NOT ('+table['id'].inlist(visitIdList)+')')
        # запрещаю удалять выставленные визиты
        tableAccountItem = db.table('Account_Item')
        cond.append('NOT '+db.existsStmt(tableAccountItem, tableAccountItem['visit_id'].eq(table['id'])))
        db.deleteRecord(table, where=cond)


    def getFinalDiagnosisMKB(self):
        for row, record in enumerate(self.modelDiagnostics.items()):
            diagnosisType = self.modelDiagnostics.diagnosisType(row)
            if diagnosisType == CF131Dialog.dtFinish:
                MKB   = forceString(record.value('MKB'))
                MKBEx = forceString(record.value('MKBEx'))
                return MKB, MKBEx
        return '', ''


    def saveActions(self, eventId):
        self.tabStatus.saveActions(eventId)
        self.tabDiagnostic.saveActions(eventId)
        self.tabCure.saveActions(eventId)
        self.tabMisc.saveActions(eventId)


    def setOrgId(self, orgId):
        self.orgId = orgId
        self.cmbPerson.setOrgId(orgId)
        self.cmbContract.setOrgId(orgId)


    def setEventTypeId(self, eventTypeId):
        CEventEditDialog.setEventTypeId(self, eventTypeId, u'Ф.131')
        self.tabCash.windowTitle = self.windowTitle()
        showTime = getEventShowTime(eventTypeId)
        showVisitTime = getEventShowVisitTime(self.eventTypeId)
        if showVisitTime:
            self.modelDiagnostics._cols[self.modelDiagnostics.getColIndex('endDate')] = CDateTimeForEventInDocTableCol(u'Выполнен', 'endDate', 15, canBeEmpty=True)
        self.getShowButtonAccount()
        self.getShowButtonTemperatureList()
        self.getShowButtonNomenclatureExpense()
        self.getShowButtonJobTickets()
        self.edtBegTime.setVisible(showTime)
        self.edtEndTime.setVisible(showTime)
        self.cmbResult.setTable('rbResult', True, 'eventPurpose_id=\'%d\'' % self.eventPurposeId)
        self.cmbResult.setValue(QtGui.qApp.session("F131_resultIdByPurpose%d" % self.eventPurposeId))

        cols = self.modelDiagnostics.cols()
        resultCol = cols[len(cols)-1]
        resultCol.filter = 'eventPurpose_id=\'%d\'' % self.eventPurposeId
        self.cmbContract.setEventTypeId(eventTypeId)
        customizePrintButton(self.btnPrint, self.eventContext if self.eventContext else 'F131')


    def setWorkRecord(self, record):
        self.__workRecord = record
        self.cmbWorkOrganisation.setValue(forceRef(record.value('org_id')) if record else None)
        self.UpdateWorkOrganisationInfo()
        self.edtWorkOrganisationFreeInput.setText(forceString(record.value('freeInput')) if record else '')
        self.edtWorkPost.setText(forceString(record.value('post')) if record else '')
        if record and forceString(record.value('OKVED')):
            self.cmbWorkOKVED.setText(forceString(record.value('OKVED')))
        self.edtWorkStage.setValue(forceInt(record.value('stage')) if record else 0)
        self.modelWorkHurts.loadItems(forceRef(record.value('id')) if record else None)
        self.modelWorkHurtFactors.loadItems(forceRef(record.value('id')) if record else None)


    def getWorkRecord(self):
        organisationId = self.cmbWorkOrganisation.value()
        freeInput = u'' if organisationId else forceStringEx(self.edtWorkOrganisationFreeInput.text())
        post  = forceStringEx(self.edtWorkPost.text())
        OKVED = forceStringEx(self.cmbWorkOKVED.text())
        stage = self.edtWorkStage.value()
        if self.__workRecord:
            recordChanged = (
                organisationId  != forceRef(self.__workRecord.value('org_id')) or
                freeInput       != forceString(self.__workRecord.value('freeInput')) or
                post            != forceString(self.__workRecord.value('post')) or
                OKVED           != forceString(self.__workRecord.value('OKVED')) or
                stage           != forceInt(self.__workRecord.value('stage'))
                )
        else:
            recordChanged=True
        if recordChanged:
            record = QtGui.qApp.db.record('ClientWork')
            record.setValue('client_id',    toVariant(self.clientId))
            record.setValue('org_id',       toVariant(organisationId))
            record.setValue('freeInput',    toVariant(freeInput))
            record.setValue('post',         toVariant(post))
            record.setValue('OKVED',        toVariant(OKVED))
            record.setValue('stage',        toVariant(stage))
        else:
            record = self.__workRecord
        return record, recordChanged


    def UpdateWorkOrganisationInfo(self):
        id = self.cmbWorkOrganisation.value()
        orgInfo = getOrganisationInfo(id)
#        self.edtWorkOrganisationINN.setText(orgInfo.get('INN', ''))
#        self.edtWorkOrganisationOGRN.setText(orgInfo.get('OGRN', ''))
        self.lblINN.setText(u'ИНН ' + orgInfo.get('INN', ''))
        self.lblKPP.setText(u'КПП ' + orgInfo.get('KPP', ''))
        self.lblOGRN.setText(u'ОГРН ' + orgInfo.get('OGRN', ''))
        self.cmbWorkOKVED.setOrgCode(orgInfo.get('OKVED', ''))
        self.edtWorkOrganisationFreeInput.setEnabled(not id)


    def addVisitByActionSummaryRow(self, actionsSummaryRow, checkActionPersonIdIsEventPerson=False):
        showTime = getEventShowTime(self.eventTypeId)
        if not hasattr(self, 'tblInspections'):
            return
        visitRecord = None
        visitId = None

        actionList = self.modelActionsSummary.items()
        visitList = self.modelActionsSummary.visitList
        if not (0 <= actionsSummaryRow < len(actionList)):
            return

        actionRecord = actionList[actionsSummaryRow]
        visitRecord = visitList.get(actionRecord)
        if not visitRecord:
            visitId = forceRef(actionRecord.value('visit_id'))
        actionTypeId = forceRef(actionRecord.value('actionType_id'))
        actionType   = CActionTypeCache.getById(actionTypeId)
        if not (actionType and actionType.addVisit):
            return

        actionEndDate = forceDateTime(actionRecord.value('endDate')) if showTime else forceDate(actionRecord.value('endDate'))
        actionBegDate = forceDateTime(actionRecord.value('begDate')) if showTime else forceDate(actionRecord.value('begDate'))
        if not actionEndDate:
            return

        actionPersonId = forceRef(actionRecord.value('person_id'))
        if not actionPersonId:
            return

        addVisit    = True
        visitsModel = self.tblInspections.model()
        visitList   = visitsModel.items()


        if visitId:
            for record in visitList:
                if forceInt(record.value('id')) == visitId:
                    visitRecord = record

        if visitRecord:
            visitRecord.setValue('person_id', actionPersonId )
            visitRecord.setValue('date', actionEndDate )
            visitsModel.reset()
        else:

            if checkActionPersonIdIsEventPerson and not self.checkPersonIdIsEventPerson(actionPersonId):
                return

            for visitRecord in visitList:
                visitDate = forceDate(visitRecord.value('date'))
                visitPersonId = forceRef(visitRecord.value('person_id'))
                if self.checkEqDateAndPersonDuringAddingVisitByAction(visitDate, actionEndDate, visitPersonId, actionPersonId):
                    addVisit = False
                    break

            if addVisit:
                sceneId     = actionType.addVisitSceneId
                visitTypeId = actionType.addVisitTypeId
                visitRecord = visitsModel.getEmptyRecord()
                visitRecord.setValue('person_id', actionPersonId)
                visitRecord.setValue('endDate', actionEndDate)
                visitRecord.setValue('setDate', actionBegDate)
                visitRecord.setValue('scene_id', sceneId)
                visitRecord.setValue('visitType_id', visitTypeId)
                visitRecord.setValue('diagnosisType_id', QVariant(self.modelDiagnostics.diagnosisTypeCol.ids[2]))
                if actionPersonId:
                    personRecord = QtGui.qApp.db.getRecord('Person', 'speciality_id', actionPersonId)
                    if personRecord:
                        actionPersonSpecialityId = forceRef(personRecord.value('speciality_id'))
                        visitRecord.setValue('speciality_id', actionPersonSpecialityId)
                self.modelActionsSummary.visitList[ actionRecord ] = visitRecord
                self.prepareDiagnostics([visitRecord], addVisit = True)


    def checkDataEntered(self):
        result = CEventEditDialog.checkDataEntered(self)
        tabList = [self.tabStatus, self.tabDiagnostic, self.tabCure, self.tabMisc]
        result = result and (self.orgId != QtGui.qApp.currentOrgId() or self.cmbContract.value() or self.checkInputMessage(u'договор', False, self.cmbContract))
        result = result and (self.cmbPerson.value() or self.checkInputMessage(u'врач', False, self.cmbPerson))
        result = result and self.checkExecPersonSpeciality(self.cmbPerson.value(), self.cmbPerson)
        result = result and self.checkWorkHurts()
        self.blankMovingIdList = []
        mesRequired = getEventMesRequired(self.eventTypeId)
        showTime = getEventShowTime(self.eventTypeId)
        if showTime:
            begDate = QDateTime(self.edtBegDate.date(), self.edtBegTime.time())
            endDate = QDateTime(self.edtEndDate.date(), self.edtEndTime.time())
        else:
            begDate = self.edtBegDate.date()
            endDate = self.edtEndDate.date()
#        begDateCheck = self.edtBegDate.date()
        endDateCheck = self.edtEndDate.date()
        nextDate = self.edtNextDate.date()
        if not endDateCheck and QtGui.qApp.userHasRight(urEditEndDateEvent):
            maxEndDate, finishMKB = self.getMaxEndDateByDiagnostics()
            if maxEndDate and finishMKB:
                if QtGui.QMessageBox.question(self,
                                    u'Внимание!',
                                    u'Дата выполнения обращения не указана.\nУстановить дату завершения по максимальной дате осмотров?',
                                    QtGui.QMessageBox.No|QtGui.QMessageBox.Yes,
                                    QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes:
                    self.edtEndDate.setDate(maxEndDate)
                    endDate = maxEndDate
                    endDateCheck = self.edtEndDate.date()
        if endDateCheck:
            checkEpic, ConsFlatCodeList, needsListNazOnko = self.checkConsultationOrEpicris(tabList)
            if result and not checkEpic and self.checkAppointments():
                result = result and (checkEpic or self.checkValueMessage(
                    u"Необходимо заполнить Назначения после проведения диспансеризации", False, self.tabStatus))
                self.setActionCons([u'appointments'])
            checkRequireAction, ActionTypeIdList = self.checkRequireAction(self.eventTypeId, tabList, self.personSpecialityId, self.modelDiagnostics.items())
            result = result and checkRequireAction
            if ActionTypeIdList:
                self.setActionConsbyIds(ActionTypeIdList)
            result = result and self.needOnkoDocs(ConsFlatCodeList)
            result = result and (self.cmbResult.value()   or self.checkInputMessage(u'результат',   False, self.cmbResult))
            result = result and self.checkEventResult()
            result = result and self.checkResultEvent(self.cmbResult.value(), endDateCheck, self.cmbResult)
            result = result and self.checkActionDataEntered(begDate, QDateTime(), endDate, self.tabToken, self.edtBegDate, None, self.edtEndDate)
            result = result and self.checkEventDate(begDate, endDate, nextDate, self.tabToken, self.edtNextDate, self.edtEndDate, True)
            minDuration,  maxDuration = getEventDurationRange(self.eventTypeId)
            if minDuration<=maxDuration:
                result = result and (begDate.daysTo(endDate)+1>=minDuration or self.checkValueMessage(u'Длительность должна быть не менее %s'%formatNum(minDuration, (u'дня', u'дней', u'дней')), False, self.edtEndDate))
                result = result and (maxDuration==0 or begDate.daysTo(endDate)+1<=maxDuration or self.checkValueMessage(u'Длительность должна быть не более %s'%formatNum(maxDuration, (u'дня', u'дней', u'дней')), False, self.edtEndDate))
            if mesRequired:
                result = result and self.tabMes.checkMesAndSpecification()
                result = result and (self.tabMes.chechMesDuration() or self.checkValueMessage(u'Длительность события должна попадать в интервал минимальной и максимальной длительности по требованию к МЭС', True, self.edtBegDate))
                result = result and self.checkDiagnosticsMKBForMes(self.tblInspections, self.tabMes.cmbMes.value())
            result = result and self.checkDiagnosticsDataEntered(begDate, endDate)
            result = result and self.getPersonByDiagnostics()
            result = result and self.checkActionsDateEnteredActuality(begDate, endDate, tabList)
            result = result and self.checkActionsDataEntered(begDate, endDate)
            result = result and self.checkExecDateForVisit(endDateCheck)
            result = result and self.checkDiagnosticsPersonSpeciality()
            result = result and self.checkExecPersonSpeciality(self.cmbPerson.value(), self.cmbPerson)
            result = result and self.checkDeposit(True)

            # ТТ 4230 "Профосмотры 2026. Отключить проверку на 85% услуг" Было принято решение совсем отключить этот рудимент
            # if QtGui.qApp.defaultKLADR()[:2] == u'23':
            #     eventProfileId = forceRef(QtGui.qApp.db.translate('EventType', 'id', self.eventTypeId, 'eventProfile_id'))
            #     if eventProfileId:
            #         profileCode = forceString(QtGui.qApp.db.translate('rbEventProfile', 'id', eventProfileId, 'regionalCode'))
            #         if profileCode in ['8008', '8014'] or profileCode == '8011' and endDateCheck >= QDate(2019, 5, 1):
            #             result = result and self.checkExaminCompletion(profileCode, endDateCheck)

            #result = result and self.checkActionsDataEntered(begDate, endDate)
        else:
            result = result and self.checkDiagnosticsPersonSpeciality()
        result = result and self.tabCash.checkDataLocalContract()
        result = result and self.checkSerialNumberEntered()
        result = result and self.checkTabNotesEventExternalId()
        #                                                self.modelDiagnostics)
        result = result and (self.checkCorrectlyEnteredPersons(self.cmbPerson
                                                              ) if not QtGui.qApp.checkGlobalPreference('23:checkChosenPerson',
                                                                                                        u'не выполнять') else True)
        if self.edtEndDate.date():
            result = result and self.checkAndUpdateExpertise(self.edtEndDate.date(), self.cmbPerson.value())
            result = result and self.checkEventTypeNextEventDate(self.eventTypeId, endDateCheck, self.clientId)
            if CFinanceType.getCode(self.eventFinanceId) == CFinanceType.CMI and QtGui.qApp.defaultKLADR()[:2] == u'23':
                result = result and self.checkServiceDates(begDate, endDate)
        result = result and self.selectNomenclatureAddedActions(tabList)
        return result


    def checkWorkHurts(self):
        for row, item in enumerate(self.modelWorkHurts.items()):
            if not forceRef(item.value('hurtType_id')):
                return self.checkInputMessage(u'вредность', False, self.tblWorkHurts, row, 0)
        return True


    def getMaxEndDateByDiagnostics(self):
        result = QDate()
        finishMKB = False
        for row, record in enumerate(self.modelDiagnostics.items()):
            diagnosisType = self.modelDiagnostics.diagnosisType(row)
            if diagnosisType != CF131Dialog.dfAccomp:
                endDate = forceDate(record.value('endDate'))
                result = max(endDate, result)
                if diagnosisType == CF131Dialog.dtFinish:
                    finishMKB = bool(endDate)
        return result, finishMKB


    def getPersonByDiagnostics(self):
        result = True
        finishMKB = False
        for row, record in enumerate(self.modelDiagnostics.items()):
            diagnosisType = self.modelDiagnostics.diagnosisType(row)
            if diagnosisType == CF131Dialog.dtFinish:
                finishMKB = True
        if finishMKB:
            for row, record in enumerate(self.modelDiagnostics.items()):
                if not forceRef(record.value('person_id')) and self.modelDiagnostics.diagnosisType(row) != CF131Dialog.dfAccomp:
                    return self.checkInputMessage(u'врача.', False, self.tblInspections, row, self.modelDiagnostics.getColIndex('person_id'))
        return result

    
    def checkDiagnosticsPersonSpeciality(self):
        result = True
        result = result and self.checkPersonSpecialityDiagnostics(self.modelDiagnostics, self.tblInspections)
        return result
    

    def checkDiagnosticsDataEntered(self, begDate, endDate):
        for row, record in enumerate(self.modelDiagnostics.items()):
            if not self.checkDiagnosticDataEntered(begDate, endDate, row, record):
                return False
        return True


    def checkDiagnosticDataEntered(self, begDate, endDate, row, record):
        showVisitTime = getEventShowVisitTime(self.eventTypeId)
        showTime = getEventShowTime(self.eventTypeId)
        rowEndDate = forceDateTime(record.value('endDate')) if showVisitTime and showTime else forceDate(record.value('endDate'))
        evEndDate = toDateTimeWithoutSeconds(endDate) if showVisitTime and showTime else (endDate.date() if isinstance(endDate, QDateTime) else endDate)
        evBegDate = toDateTimeWithoutSeconds(begDate) if showVisitTime and showTime else (begDate.date() if isinstance(begDate, QDateTime) else begDate)
        eventPersonId = self.cmbPerson.value()
        column = record.indexOf('endDate')
        diagnosisTypeId = forceRef(record.value('diagnosisType_id'))
        personId = forceRef(record.value('person_id'))
        specialityId = forceRef(QtGui.qApp.db.translate('Person', 'id', personId, 'speciality_id'))
        result = specialityId or self.checkValueMessage(u'Отсутствует специальность врача', False, self.tblInspections, row, record.indexOf('person_id'))
        result = result and self.checkRowEndDate(evBegDate, evEndDate, row, record, self.tblInspections)
        if result and not diagnosisTypeId:
            column = record.indexOf('diagnosisType_id')
            result = self.checkInputMessage(u'тип диагноза.', False, self.tblInspections, row, column)
        if endDate and (self.modelDiagnostics.diagnosisTypeCol.ids[2] != diagnosisTypeId):
            result = result and (rowEndDate or self.checkInputMessage(u'дату выполнения в осмотре по специальности: %s' % (forceString(QtGui.qApp.db.translate('rbSpeciality', 'id', specialityId, 'name'))), True, self.tblInspections, row, column))
        if result and rowEndDate and eventPersonId and eventPersonId == forceRef(record.value('person_id')):
            if rowEndDate!=evEndDate:
                result = self.checkValueMessage(u'Дата выполнения осмотра ответственным лицом должна совпадать с датой выполнения обращения', True, self.tblInspections, row, column)
        if result and (self.modelDiagnostics.diagnosisTypeCol.ids[2] != diagnosisTypeId):
            healthGroupId = forceRef(record.value('healthGroup_id'))
            if not healthGroupId:
                column = self.modelDiagnostics.getColIndex('healthGroup_id')
                result = self.checkInputMessage(u'группу здоровья.', False, self.tblInspections, row, column)
        MKB = forceStringEx(record.value('MKB'))
        if result:
            if not MKB:
                column = self.modelDiagnostics.getColIndex('MKB')
                result = self.checkInputMessage(u'МКБ', False, self.tblInspections, row, column)
            result = result and self.checkActualMKB(self.tblInspections, self.edtBegDate.date(), MKB, record, row)
        if result:
            resultId = forceRef(record.value('result_id'))
            if not resultId:
                column = self.modelDiagnostics.getColIndex('result_id')
                result = self.checkInputMessage(u'результат осмотра', False, self.tblInspections, row, column)
        if result:
            result = self.checkRequiresFillingDispanser(result, self.tblInspections, record, row, MKB)
        if self.modelDiagnostics.diagnosisTypeCol.ids[2] != diagnosisTypeId:
            result = result and self.checkPersonSpeciality(record, row, self.tblInspections)
        result = result and self.checkPeriodResultHealthGroup(record, row, self.tblInspections)
        return result

    def getDiagnosisForOnko(self):
        diagnostics = self.modelDiagnostics.items()
        mkb1, mkb2, mkb3 = '', '', ''
        if diagnostics:
            for record in diagnostics:
                diagnosis = forceRef(record.value('diagnosisType_id'))
                if diagnosis == 1:
                    mkb1 = forceString(record.value('MKB'))
                elif diagnosis == 5:
                    mkb3 = forceString(record.value('MKB'))
                elif diagnosis == 2 and mkb1 == '':
                    mkb1 = forceString(record.value('MKB'))
                else:
                    mkb2 = forceString(record.value('MKB'))
            return mkb1, mkb2, mkb3
        else:
            return '', '', ''

    def needOnkoDocs(self, ConsFlatCodeList):
        mkb = self.getDiagnosisForOnko()
        if mkbIsOnko(mkb[0], mkb[2]):
            regionalCode = getEventAidTypeRegionalCode(self.eventTypeId)
            if regionalCode not in ['301', '302', '511', '522'] and u'ControlListOnko' not in ConsFlatCodeList:
                self.setActionCons([u'ControlListOnko'])
                self.checkValueMessage(
                    u"Необходимо заполнить Контрольный лист учета при новообразовании", False, self.tabStatus)
                return False
        return True

    def checkRowEndDate(self, begDate, endDate, row, record, widget):
        result = True
        showVisitTime = getEventShowVisitTime(self.eventTypeId)
        showTime = getEventShowTime(self.eventTypeId)
        rowEndDate = forceDateTime(record.value('endDate')) if showVisitTime and showTime else forceDate(record.value('endDate'))
        column = record.indexOf('endDate')
        if rowEndDate:
            actuality = forceInt(record.value('actuality'))
            if rowEndDate>endDate:
                result = result and self.checkValueMessage(u'Дата выполнения должна быть не позже %s' % forceString(endDate), False, widget, row, column)
            lowDate = begDate.addMonths(-actuality)
            if rowEndDate < lowDate:
                result = result and self.checkValueMessage(u'Дата выполнения должна быть не раньше %s' % forceString(lowDate), False, widget, row, column)
        return result


    def checkSpecialityUsed(self, specialityId, visitTypeId):
        for i in xrange(self.modelDiagnostics.rowCount()):
                if self.modelDiagnostics.specialityId(i) == specialityId and self.modelDiagnostics.visitTypeId(i) == visitTypeId:
                    return True
        return False


    def checkSelectionGroupUsed(self, model, selectionGroup):
        if selectionGroup != 0:
            for item in model.items():
                if forceInt(item.value('selectionGroup')) == selectionGroup:
                    return True
        return False

    # ТТ 4230 "Профосмотры 2026. Отключить проверку на 85% услуг" Было принято решение совсем отключить этот рудимент
    # def checkExaminCompletion(self, profileCode, endDateCheck):
    #     allServices = {}
    #     examinService = None
    #     checkDate =  self.getExecDateTime() if self.getExecDateTime().isValid() else self.getSetDateTime()
    #     if profileCode in ['8008', '8014']:
    #         if checkDate >= QDateTime(2019, 5, 1, 0, 0, 0):
    #             examinCodes = ExaminCalc.examinList2019[1][1][0]
    #         elif checkDate >= QDateTime(2018, 1, 1, 0, 0, 0):
    #             examinCodes = ExaminCalc.examinList2018[1][1][0]
    #         else:
    #             examinCodes = ExaminCalc.examinList2017[1][1][0]
    #
    #         if checkDate >= QDateTime(2019, 5, 1, 0, 0, 0):
    #             visitCodes = ExaminCalc.examinList2019[19][1][0]
    #         elif checkDate >= QDateTime(2018, 1, 1, 0, 0, 0):
    #             visitCodes = ExaminCalc.examinList2018[17][1][0]
    #         else:
    #             visitCodes = ExaminCalc.examinList2017[21][1][0]
    #     elif profileCode == '8011':
    #         examinCodes = ExaminCalc.examinListProf2019[1][1][0]
    #         visitCodes = ExaminCalc.examinListProf2019[10][1][0]
    #
    #     for actionTab in [self.tabStatus, self.tabDiagnostic, self.tabCure, self.tabMisc]:
    #         model = actionTab.tblAPActions.model()
    #         for row, (record, action) in enumerate(model.items()):
    #             if action and action._actionType.id:
    #                 status = forceInt(record.value('status'))
    #                 endDate = forceDate(record.value('endDate'))
    #                 serviceId = action._actionType.nomenclativeServiceId
    #                 if status == 2 and bool(endDate) and endDate.isValid() and serviceId:
    #                     serviceCode = forceString(QtGui.qApp.db.translate('rbService', 'id', serviceId, 'infis'))
    #                     orgId = forceRef(record.value('org_id'))
    #                     external = (orgId and orgId != self.orgId)
    #                     allServices[serviceCode] = (endDate, external)
    #     for code in examinCodes:
    #         if code in allServices:
    #             examinService = allServices[code]
    #     if examinService is None:
    #         return self.checkValueMessage(u'Не проведено анкетирование!', False, self.tblActions)
    #     mainCompleted = False
    #     for code in visitCodes:
    #         if code in allServices:
    #             mainCompleted = True
    #             break
    #     if not mainCompleted:
    #         return self.checkValueMessage(u'Не проведен прием врача-терапевта!', False, self.tblActions)
    #     if examinService and examinService[1]:
    #         return self.checkValueMessage(u'Анкетирование не может быть проведено в другой организации!', False, self.tblActions)
    #     minDate = examinService[0]
    #
    #     for code, (endDate, external) in allServices.iteritems():
    #         allServices[code] = (endDate, (endDate < minDate))
    #
    #     if checkDate < QDate(2026, 2, 1):
    #         age = self.edtBegDate.date().year() - self.clientBirthDate.year()
    #         (numTotal, numCompleted, numExternal, notCompletedList) = ExaminCalc.checkCompletion(age, self.clientSex, allServices, checkDate, profileCode)
    #         if numCompleted < ceil(numTotal * 0.85):
    #             return self.checkValueMessage(u'Выполнено меньше 85%% мероприятий (%d из %d); не проведено:\n%s' % (numCompleted, numTotal, '\n'.join(notCompletedList)), False, self.tblActions)
    #
    #     if numExternal > ceil(numTotal * 0.15) and endDateCheck < QDate(2021, 3, 1):
    #
    #         if profileCode in ['8008', '8014']:
    #             serv026code = 'B04.026.001.062'
    #             serv047code = 'B04.047.001.061'
    #         else:
    #             serv026code = 'B04.026.002'
    #             serv047code = 'B04.047.002'
    #
    #         if serv026code in allServices or serv047code in allServices:
    #             return True
    #         serviceId026 = QtGui.qApp.db.translate('rbService', 'infis', serv026code, 'id')
    #         serviceId047 = QtGui.qApp.db.translate('rbService', 'infis', serv047code, 'id')
    #         actionTypeId026 = QtGui.qApp.db.translate('ActionType', 'nomenclativeService_id', serviceId026, 'id')
    #         actionTypeId047 = QtGui.qApp.db.translate('ActionType', 'nomenclativeService_id', serviceId047, 'id')
    #         if not (serviceId026 and serviceId047 and actionTypeId026 and actionTypeId047):
    #             return self.checkValueMessage(u'Более 15% мероприятий проведено ранее, либо в других учреждениях, \nно тип мероприятия для приема терапевта при ранее оказанных услугах свыше 15% не найден.', False, self.tblActions)
    #         if QtGui.QMessageBox.question(self,
    #                             u'Внимание!',
    #                             u'Более 15% мероприятий проведено ранее, либо в других учреждениях. Тип приема врача-терапевта будет изменен. Продолжить?',
    #                             QtGui.QMessageBox.No|QtGui.QMessageBox.Yes,
    #                             QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes:
    #             self.changeExaminServiceCode = (actionTypeId026, actionTypeId047)
    #             return True
    #         else:
    #             return False
    #     return True
        

    def getAvailableDiagnostics(self):
        available = []
        if self.eventTypeId:
            records = getEventPlannedInspections(self.eventTypeId)
            for record in records:
                selectionGroup = forceInt(record.value('selectionGroup'))
                if (     selectionGroup<=0
                     and self.recordAcceptable(record, setEventDate = forceDate(self.eventSetDateTime), birthDate = self.clientBirthDate)
                     and not self.checkSpecialityUsed(forceInt(record.value('speciality_id')), forceInt(record.value('visitType_id')))
                     and not self.checkSelectionGroupUsed(self.modelDiagnostics, selectionGroup)
                   ):
                    available.append(self.newDiagnosticRecord(record, False))
        return available


    def canAddDiagnostic(self):
        available = self.getAvailableDiagnostics()
        if available:
            newMenu = QtGui.QMenu(self.mnuDiagnostics)
            for i, record in enumerate(available):
                specialityId = forceRef(record.value('speciality_id'))
                action = newMenu.addAction(specialityName(specialityId))
                action.setData( QVariant(i) )
                self.connect(action, SIGNAL('triggered()'), self.addBaseDiagnostic)
            self.actDiagnosticsAddBase.setMenu(newMenu)
            self.availableDiagnostics = available
            return True
        else:
            self.availableDiagnostics = []
            return False


    def addBaseDiagnostic(self):
        sender = self.sender()
        if isinstance(sender, QtGui.QAction):
            index = forceInt(sender.data())
            rowIndex = self.modelDiagnostics.rowCount()
            self.modelDiagnostics.insertRecord(rowIndex, self.availableDiagnostics[index])
            self.tblInspections.setCurrentIndex(self.modelDiagnostics.index(rowIndex, 0))


    def isRemovableDiagnostic(self, row):
        specialityId = self.modelDiagnostics.specialityId(row)
        records = getEventPlannedInspections(self.eventTypeId)
        for record in records:
            selectionGroup  = forceInt(record.value('selectionGroup'))
            recSpecialityId = forceRef(record.value('speciality_id'))
            if (    recSpecialityId == specialityId
                 and selectionGroup<=0
                 and self.recordAcceptable(record)
               ):
                   return True
        return False


    def checkActionTypeUsed(self, actionTypeId):
#        for i in xrange(self.modelActions.rowCount()):
#                if self.modelActions.actionTypeId(i) == actionTypeId:
#                    return True
        return False


#    def getAvailableActions(self):
#        if self.eventTypeId:
#            records = QtGui.qApp.db.getRecordList('EventType_Action', cols='actionType_id, sex, age, selectionGroup, actuality', where='eventType_id=\'%d\' AND selectionGroup<=\'0\'' % self.eventTypeId, order='id')
#            available = []
#            for record in records:
#                if self.recordAcceptable(record) \
#                and not self.checkActionTypeUsed(forceInt(record.value('actionType_id'))) \
#                and not self.checkSelectionGroupUsed(self.modelActions, forceInt(record.value('selectionGroup'))):
#
#                    available.append(self.newActionRecord(record))
#            return available
#        return []


#    def canAddAction(self):
#        available = self.getAvailableActions()
#        if available:
#            newMenu = QtGui.QMenu(self.mnuActions)
#            for i, record in enumerate(available):
#                actionTypeId = forceRef(record.value('actionType_id'))
#                action = newMenu.addAction(actionTypeName(actionTypeId))
#                action.setData( QVariant(i) )
#                self.connect(action, SIGNAL('triggered()'), self.addActionType)
#            self.actActionsAdd.setMenu(newMenu)
#            self.availableActions = available
#            return True
#        else:
#            self.actActionsAdd.setMenu(None)
#            self.availableAction = []
#            return False
#
#
#    def addActionType(self):
#        sender = self.sender()
#        if isinstance(sender, QtGui.QAction):
#            index = forceInt(sender.data())
#            rowIndex = self.modelActions.rowCount()
#            self.modelActions.insertRecord(rowIndex, self.availableActions[index])
#            self.tblActions.setCurrentIndex(self.modelActions.index(rowIndex, 0))
#
#
#    def getActionSelectionGroup(self, actionTypeId):
#        records = QtGui.qApp.db.getRecordList('EventType_Action',
#                                               cols='selectionGroup',
#                                               where='eventType_id=\'%d\' AND actionType_id=\'%d\'' % (self.eventTypeId, actionTypeId)
#                                             )
#        if records:
#            return forceInt(records[0].value('selectionGroup'))
#        else:
#            return 1
#
#
#    def isChangeableAction(self,  row):
#        actionTypeId = self.modelActions.actionTypeId(row)
#        selectionGroup = self.getActionSelectionGroup(actionTypeId)
#        if not(selectionGroup in (0, 1)):
#            records = QtGui.qApp.db.getRecordList('EventType_Action',
#                                                   cols='*',
#                                                   where='eventType_id=\'%d\' AND selectionGroup=\'%d\' AND actionType_id != \'%d\'' % (self.eventTypeId, selectionGroup, actionTypeId)
#                                                 )
#        else:
#            records = []
#
#        types = []
#        if records:
#            newMenu = QtGui.QMenu(self.mnuActions)
#            for i, record in enumerate(records):
#                if self.recordAcceptable(record):
#                    actionTypeId = forceRef(record.value('actionType_id'))
#                    action = newMenu.addAction(actionTypeName(actionTypeId))
#                    action.setData( QVariant(i) )
#                    self.connect(action, SIGNAL('triggered()'), self.changeActionType)
#                    types.append(actionTypeId)
#        self.availableChangeActions = types
#        if types:
#            self.actActionsChange.setMenu(newMenu)
#            return True
#        else:
#            self.actActionsChange.setMenu(None)
#            return False
#
#
#    def changeActionType(self):
#        sender = self.sender()
#        if isinstance(sender, QtGui.QAction):
#            index = forceInt(sender.data())
#            rowIndex = self.tblActions.currentIndex().row()
#            self.modelActions.changeActionType(rowIndex, self.availableChangeActions[index])
#
#
#    def isRemovableAction(self,  row):
#        actionTypeId = self.modelActions.actionTypeId(row)
#        ids = QtGui.qApp.db.getIdList('EventType_Action',
#                                       where='eventType_id=\'%d\' AND selectionGroup<=\'0\' AND actionType_id=\'%d\'' % (self.eventTypeId, actionTypeId))
#        return bool(ids)


    def getDiagFilter(self, specialityId=None):
        if not specialityId:
            specialityId = self.personSpecialityId
        result = self.mapSpecialityIdToDiagFilter.get(specialityId, None)
        if result is None:
            result = QtGui.qApp.db.translate('rbSpeciality', 'id', specialityId, 'mkbFilter')
            if result is None:
                result = ''
            else:
                result = forceString(result)
            self.mapSpecialityIdToDiagFilter[specialityId] = forceString(result)
        return result


    def checkDiagnosis(self, MKB, specialityId=None):
        diagFilter = self.getDiagFilter(specialityId)
        return checkDiagnosis(self, MKB, diagFilter, self.clientId, self.clientSex, self.clientAge, self.edtBegDate.date())



    def getEventInfo(self, context):
        result = CEventEditDialog.getEventInfo(self, context)
        # инициализация свойств
        result._isPrimary = self.chkPrimary.isChecked()+1
        # инициализация таблиц
        result._actions = CActionInfoProxyList(context,
                [self.tabStatus.modelAPActions, self.tabDiagnostic.modelAPActions, self.tabCure.modelAPActions, self.tabMisc.modelAPActions, self.tabMedicalDiagnosis.tblEventMedicalDiagnosis.model()],
                result)
        result._diagnosises = CDiagnosticInfoProxyList(context, [self.modelDiagnostics])
        return result


    def updateMesMKB(self):
        MKB, MKBEx = self.getFinalDiagnosisMKB()
        self.tabMes.setMKB(MKB)
        self.tabMes.setMKBEx(MKBEx)


    def setContractId(self, contractId):
        if self.contractId != contractId:
            CEventEditDialog.setContractId(self, contractId)
            cols = self.tblActions.model().cols()
            if cols:
                cols[0].setContractId(contractId)
            self.tabCash.modelAccActions.setContractId(contractId)
            self.tabCash.updatePaymentsSum()

# # #

    @pyqtSignature('QDate')
    def on_edtBegDate_dateChanged(self, date):
        date = QDate(date)
        self.eventSetDateTime.setDate(date)
        self.setFilterResult(date)
        for row in xrange(self.modelDiagnostics.rowCount()):
            self.modelDiagnostics.setSetDate(row, date)
        for row in xrange(self.modelActionsSummary.rowCount()):
            self.modelActionsSummary.setBegDate(row, date)
#        contractId = self.cmbContract.value()
#        self.cmbContract.setBegDate(date)
#        self.cmbContract.setEndDate(date)
#        self.cmbContract.setValue(contractId)
        self.cmbPerson.setBegDate(date)
        self.setPersonDate(date)
        self.tabMes.setEventBegDate(self.eventSetDateTime.date())


    @pyqtSignature('QTime')
    def on_edtBegTime_timeChanged(self, time):
        self.eventSetDateTime.setTime(time)


    @pyqtSignature('QDate')
    def on_edtEndDate_dateChanged(self, date):
        self.eventDate = QDate(date)
        for row in xrange(self.modelDiagnostics.rowCount()):
            self.modelDiagnostics.setEndDate(row, date)
        self.cmbContract.setDate(self.getDateForContract())
        self.setEnabledChkCloseEvent(self.eventDate)
        self.cmbPerson.setEndDate(date)
        if getEventShowTime(self.eventTypeId):
            time = QTime.currentTime() if date else QTime()
            self.edtEndTime.setTime(time)


    @pyqtSignature('')
    def on_cmbContract_valueChanged(self):
        contractId = self.cmbContract.value()
        self.setContractId(contractId)
        cols = self.tblActions.model().cols()
        if cols:
            cols[0].setContractId(contractId)


    @pyqtSignature('int')
    def on_cmbPerson_currentIndexChanged(self):
        self.setPersonId(self.cmbPerson.value())


    @pyqtSignature('int')
    def on_cmbWorkOrganisation_currentIndexChanged(self):
        self.UpdateWorkOrganisationInfo()

    @pyqtSignature('int')
    def on_cmbResult_currentIndexChanged(self):
        super(CF131Dialog, self).on_cmbResult_currentIndexChanged()

        resultId = self.cmbResult.value()
        if not resultId:
            return

        db = QtGui.qApp.db
        tableResult = db.table('rbResult')
        record = db.getRecordEx(tableResult, [tableResult['regionalCode']], [tableResult['id'].eq(resultId)])
        if not record:
            return

        resultRegCode = forceString(record.value('regionalCode'))
        if not resultRegCode:
            return

        group = ''
        for healthGroup, regCodes in healthGroupToResults.items():
            if resultRegCode in regCodes:
                group = healthGroup
                break

        idDiagResult = None
        tableDiagResult = db.table('rbDiagnosticResult')

        resultFilter = ''
        if hasattr(self, 'modelDiagnostics') and self.modelDiagnostics:
            resultColIndex = self.modelDiagnostics.getColIndex('result_id')
            if resultColIndex is not None:
                resultCol = self.modelDiagnostics.cols()[resultColIndex]
                resultFilter = getattr(resultCol, 'filter', '')

        idDiagResult = db.getMax(tableDiagResult, where=resultFilter)

        idHealthGroup = None
        if group:
            tableHealth = db.table('rbHealthGroup')
            idHealthGroup = db.translate(tableHealth, 'code', group, 'id')

            for item in self.modelDiagnostics.items():
                if forceInt(item.value("diagnosisType_id")) == 1:
                    if idHealthGroup:
                        item.setValue('healthGroup_id', QVariant(idHealthGroup))
                    if idDiagResult:
                        item.setValue('result_id', QVariant(idDiagResult))

    @pyqtSignature('')
    def on_btnSelectWorkOrganisation_clicked(self):
        orgId = selectOrganisation(self, self.cmbWorkOrganisation.value(), False)
        self.cmbWorkOrganisation.model()._getDataCache().purge()
        self.cmbWorkOrganisation.updateModel()
        if orgId:
            self.setIsDirty()
            self.cmbWorkOrganisation.setValue(orgId)
        self.cmbWorkOrganisation.setFocus(Qt.OtherFocusReason)


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
        lenActions = len(self.modelActionsSummary.items())
        actionListToNewEvent = []
        isDirty = self.isDirty()
        self.prepare(self.clientId, self.eventTypeId, self.orgId, self.personId, self.eventDate, self.eventDate, None, None, None, None, None, isEdit=True)
        self.initPrevEventTypeId(self.eventTypeId, self.clientId)
        self.initPrevEventId(None)
        self.addActions(actionListToNewEvent)
        if lenActions != len(self.modelActionsSummary.items()) or isDirty:
            self.setIsDirty(True)

        
    @pyqtSignature('int')
    def on_btnPrint_printByTemplate(self, templateId):
        if self.checkPrintByTemplateAllowed(templateId):
            context = CInfoContext()
            eventInfo = self.getEventInfo(context)

            data = {'event' : eventInfo, 'client': eventInfo.client}

    #        diagnosticsColNames = ['type', 'speciality', 'person', 'setDate', 'endDate', 'healthGroup',
    #                               'MKB',  'character', 'stage', 'dispanser', 'sanatorium', 'hospital', 'result'
    #                              ]
    #        diagnostics = []
    #        for row in xrange(self.modelDiagnostics.rowCount()):
    #            diagnostic = {}
    #            for col, colName in enumerate(diagnosticsColNames):
    #                diagnostic[colName] = forceString(self.modelDiagnostics.data(self.modelDiagnostics.index(row, col)))
    #            diagnostics.append(diagnostic)
    #        data['diagnostics'] = diagnostics

            actionsCols = [(0, 'type'), (1, 'directionDate'), (2,'begDate'),  (3,'endDate'), (5,'person'), (10, 'note')]
            actions = []
            for row in xrange(self.modelActionsSummary.rowCount()):
                action = {}
                for col, colName in actionsCols:
                    action[colName] = forceString(self.modelActionsSummary.data(self.modelActionsSummary.index(row, col)))
                actions.append(action)
            data['actions'] = actions
            data['setDate']  = CDateInfo(self.edtBegDate.date())
            data['execDate'] = CDateInfo(self.edtEndDate.date())
            person = context.getInstance(CPersonInfo, self.cmbPerson.value())
            data['setPerson'] = person
            data['execPerson'] = person
            data['person'] = person
            dispansIPhase, dispansIIPhase, hazardList = self.getActionDispans(context)
            data['dispansIPhase'] = dispansIPhase
            data['dispansIIPhase'] = dispansIIPhase
            data['hazardList'] = hazardList
            diagnosticInfoList = context.getInstance(CLocDiagnosticInfoList, self.itemId())
            data['diseasesInfoList'] = self.getIdentifiedDiseasesInfo(context, diagnosticInfoList, eventInfo)
            data['additionInfoList'] = self.getAdditionDispansInfo(context)
            applyTemplate(self, templateId, data, signAndAttachHandler=self.tabNotes.btnAttachedFiles.getSignAndAttachHandler())


    @pyqtSignature('')
    def on_modelDiagnostics_resultChanged(self):
        currentValue = self.cmbResult.value()
        if QtGui.qApp.provinceKLADR()[:2] == u'23' and CFinanceType.getCode(self.eventFinanceId) == 2:
            endDateCheck = self.edtEndDate.date()
            if not endDateCheck:
                endDateCheck = self.edtBegDate.date()
            resultCond = getNewResultCond(self.modelDiagnostics.resultId(), endDateCheck)
        else:
            resultCond = ''
        self.cmbResult.setTable('rbResult', True, 'eventPurpose_id=\'%d\'  %s' % (self.eventPurposeId, resultCond))
        if forceBool(QtGui.qApp.preferences.appPrefs.get('fillDiagnosticsEventsResults', True)):
            CF131Dialog.defaultDiagnosticResultId = self.modelDiagnostics.resultId()
            defaultResultId = getEventResultId(CF131Dialog.defaultDiagnosticResultId, self.eventPurposeId)
            if defaultResultId and isDefaultResultIdValid(defaultResultId, self.eventPurposeId, resultCond) and not currentValue:
                self.cmbResult.setValue(defaultResultId)
            else:
                self.cmbResult.setValue(currentValue)
        else:
            self.cmbResult.setValue(currentValue)


    def getActionDispans(self, context):
        params = {}
        eventId = self.itemId()
        dispansIPhase = None
        dispansIIPhase = None
        i = 0
        for model in self.modelActionsSummary.models:
            for row, (record, action) in enumerate(model.items()):
                actionTypeId = forceRef(record.value('actionType_id'))
                if not actionTypeId:
                    continue
                param = {}
                param['actionTypeId'] = actionTypeId
                param['MKB'] = forceString(record.value('MKB'))
                param['isUrgent'] = forceInt(record.value('isUrgent'))
                param['directionDate'] = forceDate(record.value('directionDate'))
                param['begDate'] = forceDate(record.value('begDate'))
                param['endDate'] = forceDate(record.value('endDate'))
                param['status'] = forceInt(record.value('status'))
                param['personId'] = forceRef(record.value('person_id'))
                param['mesId'] = self.tabMes.cmbMes.value()
                param['eventId'] = eventId
                param['prevEventId'] = self.prevEventId
                param['clientId'] = self.clientId
                param['setDate'] = self.edtBegDate.date()
                param['execDate'] = self.edtEndDate.date()
                if self.prevEventId:
                    param['phase'] = 2
                else:
                    param['phase'] = 1
                for actionPropertie in action.getProperties():
                    param['namePropertyType']  = actionPropertie._type.name
                    param['descrPropertyType'] = actionPropertie._type.descr
                    param['valueProperty']     = actionPropertie.getValue()
                    evaluation = actionPropertie.getEvaluation()
                    if evaluation:
                        param['evaluation'] = evaluation
                params[i] = param
                i += 1
        if self.prevEventId:
            dispansIIPhase = context.getInstance(CLocActionDispansPhaseInfo, eventId, 2, dictOut=params)
            dispansIPhase = context.getInstance(CActionDispansPhaseInfo, self.prevEventId, 1)
        else:
            dispansIPhase = context.getInstance(CLocActionDispansPhaseInfo, eventId, 1, dictOut=params)
            if eventId:
                db = QtGui.qApp.db
                tableEvent = db.table('Event')
                recordNextId = db.getRecordEx(tableEvent, [tableEvent['id']], [tableEvent['prevEvent_id'].eq(eventId), tableEvent['deleted'].eq(0)])
                nextEventId = forceRef(recordNextId.value('id')) if recordNextId else None
                if nextEventId:
                    dispansIIPhase = context.getInstance(CActionDispansPhaseInfo, nextEventId, 2)
        hazardList = context.getInstance(CLocHazardInfoList, eventId, dictOut=params)
        return dispansIPhase, dispansIIPhase, hazardList


    def getIdentifiedDiseasesInfo(self, context, diagnosticInfoList, eventInfo):
        mapMainRows = createMapCodeToRowIdx( [row[2] for row in RowsTemplate] )
        rowSize = 5
        reportMainData = [ [0]*rowSize for row in xrange(len(RowsTemplate)) ]
        reportMainData = self.getReportDiseasesInfo(diagnosticInfoList, mapMainRows, reportMainData, eventInfo)
        if self.prevEventId:
            diagnosticInfoList = context.getInstance(CLocDiagnosticInfoList, self.prevEventId)
            eventInfo = context.getInstance(CEventInfo, self.prevEventId)
            reportMainData = self.getReportDiseasesInfo(diagnosticInfoList, mapMainRows, reportMainData, eventInfo)
        return context.getInstance(CLocDiseasesInfoList, RowsTemplate, dictOutData=reportMainData)


    def getReportDiseasesInfo(self, diagnosticInfoList, mapMainRows, reportMainData, eventInfo):
        execDate = eventInfo.execDate.date
        setDate = eventInfo.setDate.date
        for diagnosises in diagnosticInfoList.diagnosticItems:
            phaseCode = diagnosises.phase.code
#            phaseName = diagnosises.phase.name
            MKBRec = normalizeMKB(diagnosises.MKB.code)
#            classMKB = diagnosises.MKB.class_
#            block = diagnosises.MKB.block
#            descr = diagnosises.MKB.descr
            dispanserCode = diagnosises.dispanser.code
#            dispanserName = diagnosises.dispanser.name
            diagnosticSetDate = diagnosises.setDate.date
            characterCode = diagnosises.character.code
            for row in mapMainRows.get(MKBRec, []):
                reportLine = reportMainData[row]
                reportLine[0] = forceString(diagnosticSetDate)
                if diagnosticSetDate and diagnosticSetDate <= execDate and diagnosticSetDate >= setDate:
                    reportLine[1] = forceString(diagnosticSetDate)
                if characterCode in [u'1', u'2']:
                    reportLine[2] = forceString(diagnosticSetDate)
                if dispanserCode in [u'1', u'2', u'6']:                  
                    reportLine[3] = forceString(diagnosticSetDate)
                if phaseCode == u'10':
                    reportLine[4] = forceString(diagnosticSetDate)
        return reportMainData


    def getInterviewActionTypeIdList(self):
        db = QtGui.qApp.db
        table = db.table('rbService')
        cond = [db.joinOr([table['code'].like(u'А25.12.004*'),
                table['code'].like(u'A25.12.004*')])]
        fields = table['id'].name()
        record = db.getRecordEx(table, fields, cond)
        return forceRef(record.value('id')) if record else None


    def getAdditionDispansInfo(self, context):
        params = {}
        eventId = self.itemId()
#        additionInfoList = None
        hazardActionTypeId = self.getInterviewActionTypeIdList()
        relativeSumHazard = 0 #{0-нет, 1-низкий, 2-высокий}
        absoluteSumHazard = 0 #{0-нет, 1-высокий, 2-очень высокий}
        params['actionTypeClass'] = 0
        params['followUpSurvey'] = 0
        params['directionHeartDoctor'] = 0
        params['directionPsychiaterDoctor'] = 0
        params['directionWTMP'] = 0
        params['directionSanatorium'] = 0
        params['healthGroup'] = u''
        db = QtGui.qApp.db
        tableAT = db.table('ActionType')
        for model in self.modelActionsSummary.models:
            for row, (record, action) in enumerate(model.items()):
                actionTypeId = forceRef(record.value('actionType_id'))
                if not actionTypeId:
                    continue
                recordAT = db.getRecordEx(tableAT, [tableAT['nomenclativeService_id']], [tableAT['id'].eq(actionTypeId), tableAT['deleted'].eq(0)])
                nomenclativeServiceId = forceRef(recordAT.value('nomenclativeService_id')) if recordAT else None
                if hazardActionTypeId and hazardActionTypeId == nomenclativeServiceId:
                    for actionPropertie in action.getProperties():
                        descrPropertyType = trim(forceString(actionPropertie._type.descr))
                        valueProperty     = trim(forceString(actionPropertie.getValue()))
                        if descrPropertyType == u'1':
                            if u'да' in valueProperty.lower():
                                relativeSumHazard = 1
                        elif descrPropertyType == u'2':
                            if u'да' in valueProperty.lower():
                                relativeSumHazard = 2
                        elif descrPropertyType == u'5':
                            if u'да' in valueProperty.lower():
                                absoluteSumHazard = 1
                        elif descrPropertyType == u'6':
                            if u'да' in valueProperty.lower():
                                absoluteSumHazard = 2
                actionType = action.getType()
                actionTypeClass = actionType.class_
                if actionTypeClass == 2 and forceInt(record.value('status')) == 2 and forceDate(record.value('endDate')):
                    params['actionTypeClass'] = 2
        baseDiagnosisTypeId = self.modelDiagnostics.diagnosisTypeCol.ids[0]
        for item in self.modelDiagnostics.items():
            diagnosisTypeId = forceRef(item.value('diagnosisType_id'))
            healthGroupId = forceRef(item.value('healthGroup_id'))
            sanatorium = forceInt(item.value('sanatorium'))
            hospital = forceInt(item.value('hospital'))
            resultId = forceRef(item.value('result_id'))
            diagnosisTypeId = forceRef(item.value('diagnosisType_id'))
            resultCode = forceString(db.translate('rbDiagnosticResult', 'id', resultId,'code'))
            if healthGroupId and diagnosisTypeId == baseDiagnosisTypeId:
                recordHG = db.getRecordEx('rbHealthGroup', 'code, name', 'id = %s'%healthGroupId)
                if recordHG:
                    params['healthGroup'] = forceString(recordHG.value('code')) + u'(' + forceString(recordHG.value('name')) + u')'
                    healthGroupCode = forceString(recordHG.value('code'))
            else:
                healthGroupCode = forceString(db.translate('rbHealthGroup', 'id', healthGroupId,'code'))
            if resultCode == u'07':
                params['followUpSurvey'] = 1
            if resultCode == u'08':
                params['directionHeartDoctor'] = 1
            if resultCode == u'09':
                params['directionPsychiaterDoctor'] = 1
            if (hospital > 1 and (healthGroupCode == u'4' or healthGroupCode == u'5')) or resultCode == u'10':
                params['directionWTMP'] = 1
            if sanatorium > 1:
                params['directionSanatorium'] = 1
        params['relativeSumHazard'] = relativeSumHazard
        params['absoluteSumHazard'] = absoluteSumHazard
        return context.getInstance(CLocAdditionInfoList, eventId, dictOut=params)


    @pyqtSignature('')
    def on_mnuDiagnostics_aboutToShow(self):
        canRemove = False
        currentRow = self.tblInspections.currentIndex().row()
        if currentRow>=0:
            if QtGui.qApp.defaultKLADR()[:2] == u'23':
                canRemove = self.modelDiagnostics.payStatus(currentRow) == 0
            else:
                canRemove = self.modelDiagnostics.isAccompDiagnostic(currentRow) or self.isRemovableDiagnostic(currentRow)
                canRemove = canRemove and self.modelDiagnostics.payStatus(currentRow) == 0
        self.actDiagnosticsAddBase.setEnabled(self.canAddDiagnostic())
        self.actDiagnosticsAddAccomp.setEnabled(True)
        self.actDiagnosticsRemove.setEnabled(canRemove)
        self.setFinalDiagnosticsMenuControlsState()


    @pyqtSignature('')
    def on_actDiagnosticsAddAccomp_triggered(self):
        currentRow = self.tblInspections.currentIndex().row()
        if currentRow>=0:
            currentRecord = self.modelDiagnostics.items()[currentRow]
            newRecord = self.modelDiagnostics.getEmptyRecord()
            newRecord.setValue('diagnosisType_id', QVariant(self.modelDiagnostics.diagnosisTypeCol.ids[2]))
            newRecord.setValue('person_id', currentRecord.value('person_id'))
            newRecord.setValue('speciality_id', currentRecord.value('speciality_id'))
            newRecord.setValue('healthGroup_id', currentRecord.value('healthGroup_id'))
            newRecord.setValue('result_id', currentRecord.value('result_id'))
            self.modelDiagnostics.insertRecord(currentRow+1, newRecord)
            self.tblInspections.setCurrentIndex(self.modelDiagnostics.index(currentRow+1, newRecord.indexOf('MKB')))


    @pyqtSignature('')
    def on_actDiagnosticsRemove_triggered(self):
        currentRow = self.tblInspections.currentIndex().row()
        self.modelDiagnostics.removeRowEx(currentRow)


    @pyqtSignature('')
    def on_modelDiagnostics_diagnosisChanged(self):
        self.updateMesMKB()


    @pyqtSignature('QModelIndex')
    def on_tblActions_doubleClicked(self, index):
        row = index.row()
        column = index.column()
        if 0 <= row < len(self.modelActionsSummary.itemIndex):
            page, row = self.modelActionsSummary.itemIndex[row]
            if page in [0, 1, 2, 3] and not column in [3, 4, 5, 7, 8]:
                self.tabWidget.setCurrentIndex(page+3)
                tbl = [self.tabStatus.tblAPActions, self.tabDiagnostic.tblAPActions, self.tabCure.tblAPActions, self.tabMisc.tblAPActions][page]
                tbl.setCurrentIndex(tbl.model().index(row, 0))


    def autoInsertingActionByMES(self):
        """Автодобавление услуг по МЭС"""
        if QtGui.qApp.checkGlobalPreference(u'23:f131plannerMESDispan', u'нет'):
            return
        orgStructureId = QtGui.qApp.currentOrgStructureId()
        financeCode = forceStringEx(QtGui.qApp.db.translate('rbFinance', 'id', self.eventFinanceId, 'code'))
        if financeCode:
            financeCode = financeCode in ('3', '4')
        existsActionTypesList = []
        actionTypeClasses = [0, 1, 2, 3]
        actionTypes = selectActionTypesEx(self,
                                          self,
                                          actionTypeClasses,
                                          orgStructureId,
                                          self.eventTypeId,
                                          self.contractId,
                                          self.getMesId(),
                                          financeCode,
                                          self._id,
                                          existsActionTypesList,
                                          visibleTblSelected=True,
                                          contractTariffCache=self.contractTariffCache,
                                          clientMesInfo=self.getClientMesInfo(),
                                          eventDate=self.edtEndDate.date() if self.edtEndDate.date() else self.edtBegDate.date()
                                          )
        updateTabList = []
        actionsTabsList = self.getActionsTabsList()
        for actionTypeId, action, csgRecord in actionTypes:
            class_ = forceInt(QtGui.qApp.db.translate('ActionType', 'id', actionTypeId, 'class'))
            actionsTab = actionsTabsList[class_]
            if actionsTab not in updateTabList:
                updateTabList.append(actionsTab)
            model = actionsTab.tblAPActions.model()
            model.addRow(actionTypeId, presetAction=action)
        for actionsTab in updateTabList:
            actionsTab.onActionCurrentChanged()
        if hasattr(self, 'modelActionsSummary'):
            self.modelActionsSummary.regenerate()
        if hasattr(self, 'tabCash') and hasattr(self.tabCash, 'modelAccActions'):
            self.tabCash.modelAccActions.regenerate()


# # #
#    @pyqtSignature('')
#    def on_mnuActions_aboutToShow(self):
#        canRemove = False
#        canChange = False
#        currentRow = self.tblActions.currentIndex().row()
#        if currentRow>=0:
#            payStatus = self.modelActions.payStatus(currentRow)
#            canChange = payStatus == 0 and self.isChangeableAction(currentRow)
#            canRemove = payStatus == 0 and self.isRemovableAction(currentRow)
#        self.actActionsAdd.setEnabled(self.canAddAction())
#        self.actActionsChange.setEnabled(canChange)
#        self.actActionsRemove.setEnabled(canRemove)
#
#
#    @pyqtSignature('')
#    def on_actActionsRemove_triggered(self):
#        currentRow = self.tblActions.currentIndex().row()
#        self.modelActions.removeRowEx(currentRow)

    @pyqtSignature('')
    def on_actAddChronicDiseases_triggered(self):
        """
        Добавляем хронические диагнозы к списку диагнозов
        :return:
        """
        dialog = CChronicDiseasesLoadDialog(self.clientId, self.modelDiagnostics, self)
        if dialog.exec_():
            currentRecord = self.tblInspections.currentItem()
            currentRow = self.tblInspections.currentIndex().row()
            for rowNum, item in enumerate(dialog.modelChronicDiagnoses.items()):
                index = dialog.modelChronicDiagnoses.index(rowNum, 0)
                if index in dialog.selectionModelChronicDiagnoses.selectedRows():
                    record = self.modelDiagnostics.getEmptyRecord()
                    record.setValue('diagnosisType_id', QVariant(self.modelDiagnostics.diagnosisTypeCol.ids[2]))
                    record.setValue('speciality_id', currentRecord.value('speciality_id'))
                    record.setValue('healthGroup_id', currentRecord.value('healthGroup_id'))
                    record.setValue('MKB', item.value('MKB'))
                    record.setValue('MKBEx', item.value('MKBEx'))
                    record.setValue('TNMS', item.value('TNMS'))
                    record.setValue('exSubclassMKB', item.value('exSubclassMKB'))
                    record.setValue('morphologyMKB', item.value('morphologyMKB'))
                    record.setValue('character_id', item.value('character_id'))
                    record.setValue('dispanser_id', item.value('dispanser_id'))
                    record.setValue('traumaType_id', item.value('traumaType_id'))
                    self.modelDiagnostics.insertRecord(currentRow+1, record)


#
# #####################################################################################33
#


class CF131ActionsSummaryModel(CFxxxActionsSummaryModel):
    def setData(self, index, value, role=Qt.EditRole, presetAction=None, related=True):
        result = CFxxxActionsSummaryModel.setData(self, index, value, role, presetAction)
        if result:
            column = index.column()
            items = self.items()
            row = index.row()
            record = items[row] if 0<=row<len(items) else None
            actionTypeId = forceRef(record.value('actionType_id')) if record else None
            if column == self.getColIndex('begDate'): # beg date
                newDateTime = forceDateTime(value)
                if actionTypeId:
                    defaultEndDate = CActionTypeCache.getById(actionTypeId).defaultEndDate
                    if defaultEndDate == CActionType.dedSyncActionBegDate:
                        self.setData(self.index(row, 5), toVariant(newDateTime), Qt.EditRole)
        return result


class CDiagnosisPerson(CRBInDocTableCol):
    def __init__(self, title, fieldName, width, tableName, **params):
        CRBInDocTableCol.__init__(self, title, fieldName, width, tableName, **params)
        self.eventEditor = params['eventEditor']


    def setEditorData(self, editor, value, record):
        orgId = self.eventEditor.orgId
        specialityId = forceRef(record.value('speciality_id'))
        if self.mayEngageGP(self.eventEditor.eventTypeId, specialityId):
            gpSpecialityId = QtGui.qApp.getGPSpecialityId()
        else:
            gpSpecialityId = None
        if specialityId or gpSpecialityId:
            specialityIdSet = set([specialityId, gpSpecialityId])
            filter = '''speciality_id IN (%s) AND org_id=%d''' % (','.join(str(specialityId) for specialityId in specialityIdSet if specialityId), orgId)
        elif specialityId:
            filter = '''speciality_id IS NULL AND org_id=%d''' % (orgId)
        setDate = forceDate(record.value('setDate'))
        if setDate:
            filter += ''' AND (retireDate IS NULL OR DATE(retireDate) > DATE(%s))'''%(QtGui.qApp.db.formatDate(setDate))
        editor.setTable(self.tableName, self.addNone, filter, u'''name ASC''')
        editor.setShowFields(self.showFields)
        editor.setValue(forceInt(value))


    def mayEngageGP(self, eventTypeId, specialityId): # GP == General Practitioner
        records = getEventPlannedInspections(eventTypeId)
        for record in records:
            if (     forceRef(record.value('speciality_id')) == specialityId
                 and self.eventEditor.recordAcceptable(record)
               ):
                   if forceBool(record.value('mayEngageGP')):
                       return True
        return False


class CF131DiagnosticsModel(CMKBListInDocTableModel):
    __pyqtSignals__ = ('diagnosisChanged()',
                       'resultChanged()',
                      )
    MKB_allowed_morphology = ['C', 'D']
    def __init__(self, parent):
        CMKBListInDocTableModel.__init__(self, 'Diagnostic', 'id', 'event_id', parent)
        self.isManualSwitchDiagnosis = QtGui.qApp.defaultIsManualSwitchDiagnosis()
        self.isMKBMorphology = QtGui.qApp.defaultMorphologyMKBIsVisible()
        self.characterIdForHandleDiagnosis = None
        self.diagnosisTypeCol = self.addCol(CDiagnosisTypeCol(   u'Тип',           'diagnosisType_id', 5, ['1', '2', '9']))
        self.addCol(CRBInDocTableCol(    u'Специальность', 'speciality_id', 20, 'rbSpeciality')).setReadOnly()
        self.addCol(CPersonFindInDocTableCol(u'Врач', 'person_id',  20, 'vrbPersonWithSpecialityAndOrgStr', parent=parent))
        #self.addCol(CDiagnosisPerson(    u'Врач',          'person_id',     20, 'vrbPerson', showFields=CRBComboBox.showCodeAndName, preferredWidth=250, eventEditor=parent))
        self.addCol(CDateInDocTableCol(  u'Назначен',      'setDate',     15)).setReadOnly()
        self.addCol(CDateInDocTableCol(  u'Выполнен',      'endDate',     15, canBeEmpty=True))
        self.addExtCol(CRBInDocTableCol( u'Место визита',  'scene_id',    10, 'rbScene', addNone=False, preferredWidth=150), QVariant.Int)
        self.addExtCol(CRBInDocTableCol( u'Тип визита',    'visitType_id', 10, 'rbVisitType', addNone=False, showFields=CRBComboBox.showCodeAndName), QVariant.Int)
        self.addCol(CRBInDocTableCol(    u'ГрЗд',          'healthGroup_id',     4, 'rbHealthGroup', addNone=False, showFields=CRBComboBox.showCode, preferredWidth=150)).setToolTip(u'Группа здоровья')
        self.addExtCol(CICDExInDocTableCol(u'МКБ',           'MKB', 5), QVariant.String)
        if QtGui.qApp.isExSubclassMKBVisible():
            self.addExtCol(CMKBExSubclassCol(u'РСК', 'exSubclassMKB', 20), QVariant.String).setToolTip(u'Расширенная субклассификация МКБ')
        if QtGui.qApp.isTNMSVisible():
            self.addCol(CTNMSCol(u'TNM-Ст', 'TNMS',  10))
        if QtGui.qApp.isClinicalGroupDiagnosticVisible():
            self.addCol(CEnumInDocTableCol(u'КГ', 'clinicalGroup', 30, [u'', u'1а - подозрение', u'1б - предрак', u'2 - подлежат радикальному лечению', u'3 - ремиссия', u'4 - подлежат паллиативному лечению'])).setToolTip(u'Клиническая группа')
        if self.isMKBMorphology:
            self.addExtCol(CMKBMorphologyCol(u'Морф.', 'morphologyMKB', 10, 'MKB_Morphology', filter='`group` IS NOT NULL'), QVariant.String)
        self.addCol(CDiseaseCharacter(     u'Хар',         'character_id',   7, showFields=CRBComboBox.showCode, preferredWidth=150)).setToolTip(u'Характер')

        if self.isManualSwitchDiagnosis:
            self.addExtCol(CBoolInDocTableCol( u'П',   'handleDiagnosis', 10), QVariant.Int)
            self.characterIdForHandleDiagnosis = forceRef(QtGui.qApp.db.translate('rbDiseaseCharacter', 'code', '1', 'id'))

        self.addCol(CDiseasePhases(        u'Фаза',        'phase_id',       7, showFields=CRBComboBox.showCode, preferredWidth=150)).setToolTip(u'Фаза')
        self.addCol(CDiseaseStage(         u'Ст',          'stage_id',       7, showFields=CRBComboBox.showCode, preferredWidth=150)).setToolTip(u'Стадия')
        self.addCol(CRBInDocTableCol(    u'ДН',            'dispanser_id',       4, 'rbDispanser', showFields=CRBComboBox.showCode, preferredWidth=150)).setToolTip(u'Диспансерное наблюдение')
        self.addCol(CRBLikeEnumInDocTableCol(u'СКЛ',       'sanatorium',         2, CHospitalInfo.names, showFields=CRBComboBox.showCode, preferredWidth=150)).setToolTip(u'Потребность в санаторно-курортном лечении')
        self.addCol(CRBLikeEnumInDocTableCol(u'Госп',      'hospital',           2, CHospitalInfo.names, showFields=CRBComboBox.showCode, preferredWidth=150)).setToolTip(u'Потребность в госпитализации')
        self.addCol(CToxicSubstances(u'ТоксВещ', 'toxicSubstances_id', 10, addNone=True, showFields=CRBComboBox.showName, preferredWidth=150)).setToolTip(u'Токсичное вещество')
        self.addCol(CInDocTableCol(u'Описание',     'freeInput', 15))
        self.addCol(CRBInDocTableCol(    u'Результат',     'result_id',          4, 'rbDiagnosticResult', showFields=CRBComboBox.showNameAndCode, preferredWidth=350))
        self.columnHandleDiagnosis = self.getColIndex('handleDiagnosis', None)
        self.setEnableAppendLine(False)
        self.eventEditor = parent
        self.readOnly = False


    def setReadOnly(self, value):
        self.readOnly = value


    def getCloseOrMainDiagnosisTypeIdList(self):
        return [self.diagnosisTypeCol.codeToId(code) for code in ('1', '2')]
    
    
    def getMainDiagnosisTypeIdList(self):
        return [self.diagnosisTypeCol.codeToId('2')]


    def manualSwitchDiagnosis(self):
        return self.isManualSwitchDiagnosis


    def getEmptyRecord(self):
        result = CMKBListInDocTableModel.getEmptyRecord(self)
        result.append(QtSql.QSqlField('diagnosis_id',     QVariant.Int))
        result.append(QtSql.QSqlField('defaultMKB',       QVariant.String))
        result.append(QtSql.QSqlField('actuality',        QVariant.Int))
        result.append(QtSql.QSqlField('selectionGroup',   QVariant.Int))
        result.append(QtSql.QSqlField('visit_id',         QVariant.Int))
        result.append(QtSql.QSqlField('scene_id',         QVariant.Int))
        result.append(QtSql.QSqlField('visitType_id',     QVariant.Int))
        result.append(QtSql.QSqlField('payStatus',        QVariant.Int))
        result.append(QtSql.QSqlField('cTumor_id',        QVariant.Int))
        result.append(QtSql.QSqlField('cNodus_id',        QVariant.Int))
        result.append(QtSql.QSqlField('cMetastasis_id',   QVariant.Int))
        result.append(QtSql.QSqlField('cTNMphase_id',     QVariant.Int))
        result.append(QtSql.QSqlField('pTumor_id',        QVariant.Int))
        result.append(QtSql.QSqlField('pNodus_id',        QVariant.Int))
        result.append(QtSql.QSqlField('pMetastasis_id',   QVariant.Int))
        result.append(QtSql.QSqlField('pTNMphase_id',     QVariant.Int))
        return result


    def flags(self, index=QModelIndex()):
        if self.readOnly:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        result = CMKBListInDocTableModel.flags(self, index)
        row = index.row()
        if row < len(self._items):
            column = index.column()
            if self.isManualSwitchDiagnosis and index.isValid():
                if column == self.columnHandleDiagnosis:
                    characterId = forceRef(self.items()[row].value('character_id'))
                    if characterId != self.characterIdForHandleDiagnosis:
                        result = (result & ~Qt.ItemIsUserCheckable)
#                        return result
            if self.isMKBMorphology and index.isValid():
                if column == self.getColIndex('morphologyMKB'):
                    mkb = forceString(self.items()[row].value('MKB'))
                    if not (bool(mkb) and mkb[0] in CF131DiagnosticsModel.MKB_allowed_morphology):
                        result = (result & ~Qt.ItemIsEditable)
            if QtGui.qApp.isExSubclassMKBVisible() and index.isValid():
                if column == self.getColIndex('exSubclassMKB'):
                    mkb = forceString(self.items()[row].value('MKB'))
                    if len(mkb) != 6:
                        return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return result


    def cellReadOnly(self, index):
        if index.isValid():
            row = index.row()
            column = index.column()
            if self.diagnosisType(row) == 2:
                if 0 <= column <=6:
                    return True
        return False


    def isExposed(self, row):
        if 0 <= row < len(self.items()):
            return not self.canChangeDiagnostic(row)
        return False


    def canChangeDiagnostic(self, row):
        payStatus = self.payStatus(row)
        visitId = forceRef(self.items()[row].value('visit_id')) if 0 <= row < len(self.items()) else None
        eventId = forceRef(self.items()[row].value('event_id')) if 0 <= row < len(self.items()) else None
        if not payStatus and visitId and eventId:
            db = QtGui.qApp.db
            tableVisit = db.table('Visit')
            cond = [ tableVisit['event_id'].eq(eventId),
                     tableVisit['id'].eq(visitId),
                     tableVisit['payStatus'].ne(0),
                     tableVisit['deleted'].eq(0)
                   ]
            record = db.getRecordEx(tableVisit, [tableVisit['payStatus']], where=cond)
            payStatus = forceInt(record.value('payStatus')) if record else 0
        if payStatus and not QtGui.qApp.userHasRight(urEditAfterInvoicingEvent):
            return False
        return True


    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        row = index.row()
        if 0 <= row < len(self._items):
            if role == Qt.EditRole:
                if QtGui.qApp.isTNMSVisible() and 0 <= row < len(self.items()) and column == self.items()[row].indexOf('TNMS'):
                    col = self._cols[column]
                    record = self._items[row]
                    tnmsMap = {}
                    for keyName, fieldName in CEventEditDialog.TNMSFieldsDict.items():
                        tnmsMap[keyName] = forceRef(record.value(fieldName))
                    return QVariant([forceString(record.value(col.fieldName())), tnmsMap])
        if index.isValid() and role==Qt.DisplayRole:
            if self.diagnosisType(row) == 2:
                if 0 < column <=6:
                    return QVariant()
            if column == 3:
                record = self.items()[row]
                setDate = record.value('setDate').toDate()
                endDate = record.value('endDate').toDate()
                if endDate and endDate < setDate:
                    return QVariant()
        return CMKBListInDocTableModel.data(self, index, role)


    def setData(self, index, value, role=Qt.EditRole):
        column = index.column()
        row = index.row()
        if not variantEq(self.data(index, role), value):
            eventEditor = QObject.parent(self)
            if not self.canChangeDiagnostic(row):
                return False
            if column == 0: # тип, может быть изменён всегда
                if forceInt(value) == self.diagnosisTypeCol.ids[0]:
                    for i, record in enumerate(self.items()):
                        if forceInt(record.value('diagnosisType_id')) == self.diagnosisTypeCol.ids[0]:
                            record.setValue('diagnosisType_id', toVariant(self.diagnosisTypeCol.ids[1]))
                            self.emitCellChanged(i, 0)
                            self.emit(SIGNAL('diagnosisChanged()'))
            elif column == 1: # специальность, не меняется никогда
                return False
            elif column == 2: # врач, изменяется всегда
                personId = forceRef(value)
                personRecord = QtGui.qApp.db.getRecord('Person', 'speciality_id', personId)
                personSpecialityId = forceRef(personRecord.value('speciality_id')) if personRecord else None
                record = self.items()[row]
                record.setValue('speciality_id', toVariant(personSpecialityId))
                self.emitRowChanged(row)
            elif column == 8: # код МКБ
                newMKB = forceString(value)
                if not newMKB:
                    value = self.items()[row].value('defaultMKB')
                    newMKB = forceString(value)
                elif not QObject.parent(self).checkDiagnosis(newMKB, self.specialityId(row)):
                    return False
                value = toVariant(newMKB)
                oldMKB = forceString(self.items()[row].value('MKB')) if 0 <= row < len(self.items()) else None
                self.updateCharacterByMKB(row, newMKB)
                self.updateClinicalGroup(row, oldMKB, newMKB, self.eventEditor.itemId(), self.eventEditor.clientId, self.eventEditor.eventSetDateTime.date())
                self.updateToxicSubstancesByMKB(row, newMKB)
                self.updateTNMS(index, self.items()[row], newMKB)
                self.updateMKBTNMS(self.items()[row], newMKB)
                self.inheritMKBTNMS(self.items()[row], oldMKB, newMKB, eventEditor.clientId, eventEditor.eventSetDateTime)
                self.updateExSubclass(index, self.items()[row], newMKB)
                self.updateMKBToExSubclass(self.items()[row], newMKB)
            elif QtGui.qApp.isTNMSVisible() and 0 <= row < len(self.items()) and column == self.items()[row].indexOf('TNMS'):
                record = self.items()[row]
                self.updateMKBTNMS(record, forceString(record.value('MKB')))
                if value:
                    valueList = value.toList()
                    valueTNMS = valueList[0]
                    tnmsMap = valueList[1].toMap()
                    for name, TNMSId in tnmsMap.items():
                        if name in CEventEditDialog.TNMSFieldsDict.keys():
                            record.setValue(CEventEditDialog.TNMSFieldsDict[forceString(name)], TNMSId)
                    self.emitRowChanged(row)
                    return CMKBListInDocTableModel.setData(self, index, valueTNMS, role)
            elif QtGui.qApp.isExSubclassMKBVisible() and 0 <= row < len(self.items()) and column == self.items()[row].indexOf('exSubclassMKB'):
                record = self.items()[row]
                self.updateMKBToExSubclass(record, forceStringEx(record.value('MKB')))
                return CMKBListInDocTableModel.setData(self, index, value, role)
            result = CMKBListInDocTableModel.setData(self, index, value, role)
            if result:
                self.emit(SIGNAL('diagnosisChanged()'))
            if row == 0 and column == self._mapFieldNameToCol.get('result_id'):
                self.emitResultChanged()
            return result
        else:
            return True


    def updateMKBToExSubclass(self, record, MKB):
        if QtGui.qApp.isExSubclassMKBVisible():
            self.cols()[record.indexOf('exSubclassMKB')].setMKB(forceString(MKB))


    def updateExSubclass(self, index, record, MKB):
        if QtGui.qApp.isExSubclassMKBVisible():
            newMKB = forceString(MKB)
            if self.cols()[record.indexOf('exSubclassMKB')].MKB != newMKB:
                record.setValue('exSubclassMKB', toVariant(u''))
                self.emitRowChanged(index.row())


    def updateMKBTNMS(self, record, MKB):
        if QtGui.qApp.isTNMSVisible():
            self.cols()[record.indexOf('TNMS')].setMKB(forceString(MKB))


    def updateTNMS(self, index, record, MKB):
        if QtGui.qApp.isTNMSVisible():
            newMKB = forceString(MKB)
            if self.cols()[record.indexOf('TNMS')].MKB != newMKB:
                row = index.row()
                tnmsMap = {}
                for keyName, fieldName in CEventEditDialog.TNMSFieldsDict.items():
                    tnmsMap[keyName] = None
                    record.setValue(fieldName, toVariant(None))
                record.setValue('TNMS', toVariant(u''))
                self.emitRowChanged(row)


    def diagnosisTypeId(self, row):
        return forceRef(self.items()[row].value('diagnosisType_id'))


    def diagnosisType(self, row):
        diagnosisTypeId = self.diagnosisTypeId(row)
        if diagnosisTypeId in self.diagnosisTypeCol.ids:
            return self.diagnosisTypeCol.ids.index(diagnosisTypeId)
        else:
            return -1


    def specialityId(self, row):
        return forceInt(self.items()[row].value('speciality_id'))


    def visitTypeId(self, row):
        return forceInt(self.items()[row].value('visitType_id'))


    def payStatus(self, row):
        if 0 <= row < len(self.items()):
            return forceInt(self.items()[row].value('payStatus'))
        else:
            return 0


    def isAccompDiagnostic(self, row):
        diagnosisType = self.diagnosisType(row)
        return diagnosisType == 2


    def removeRowEx(self, row):
        diagnosisType = self.diagnosisType(row)
        if diagnosisType == 2:
            self.removeRows(row, 1)
        else:
            i = row + 1
            while i < len(self.items()) and self.diagnosisType(i) == 2:
                i += 1
            self.removeRows(row, i - row)
        if row == 0:
            self.emitResultChanged()


    def emitResultChanged(self):
        self.emit(SIGNAL('resultChanged()'))


    def setSetDate(self, row, date):
        self.items()[row].setValue('setDate',  QVariant(date))
        self.emitCellChanged(row, self.items()[row].indexOf('setDate'))

    def setEndDate(self, row, date):
        self.items()[row].setValue('endDate',  QVariant(date))
        self.emitCellChanged(row, self.items()[row].indexOf('endDate'))


    def updateCharacterByMKB(self, row, MKB):
        characterIdList = getAvailableCharacterIdByMKB(MKB)
        item = self.items()[row]
        characterId = forceRef(item.value('character_id'))
        if (characterId in characterIdList) or (characterId is None and not characterIdList):
            return
        if characterIdList:
            characterId = characterIdList[0]
        else:
            characterId = None
        item.setValue('character_id', toVariant(characterId))
        self.emitCellChanged(row, item.indexOf('character_id'))


    def updateToxicSubstancesByMKB(self, row, MKB):
        toxicSubstanceIdList = getToxicSubstancesIdListByMKB(MKB)
        item = self.items()[row]
        toxicSubstanceId = forceRef(item.value('toxicSubstances_id'))
        if toxicSubstanceId and toxicSubstanceId in toxicSubstanceIdList:
            return
        item.setValue('toxicSubstances_id', toVariant(None))
        self.emitCellChanged(row, item.indexOf('toxicSubstances_id'))


    def resultId(self):
        items = self.items()
        if items:
            return forceRef(items[0].value('result_id'))
        else:
            return None
    
    
    def saveItems(self, masterId = None):
        CMKBListInDocTableModel.saveItems(self, masterId)
        self.prophylaxisPlanningSync()
