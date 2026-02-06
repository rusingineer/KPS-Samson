# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2012-2025 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui, QtSql
from PyQt4.QtCore import (Qt,
                          pyqtSignature,
                          QDate,
                          QDateTime,
                          QVariant,
                          QModelIndex,
                          )

from library.DateEdit import CDateEdit
from library.DialogBase             import CDialogBase
from library.InDocTable import CRecordListModel, CInDocTableCol, CIntInDocTableCol, CEnumInDocTableCol
from library.TableModel             import (
                                            CTableModel,
                                            CDateCol,
                                            CDesignationCol,
                                            CEnumCol,
                                            CRefBookCol,
                                            CTextCol,
                                           )
from library.Utils import (agreeNumberAndWord, forceInt, forceRef, forceString, forceStringEx, formatName,
                           formatRecordsCount, formatSex, trim, forceBool, toVariant, exceptionToUnicode, forceDate,
                           formatDate)
from Events.EditDispatcher          import getEventFormClass
from Events.AmbCardDialog           import CAmbCardDialog
from Events.EventInfo               import CDiagnosticInfoIdList, CSocStatusType
from Events.MKBInfo                 import CMKBInfo
from Surveillance.ChangeDispanserPerson import CChangeDispanserPerson
from Surveillance.SurveillancePlanningDialog import CSurveillancePlanningEditDialog
from Surveillance.GroupChangeDispanserPerson import CGroupChangeDispanserPerson

from RefBooks.AccountingSystem.Info import CAccountingSystemInfo
from Registry.AmbCardMixin          import CAmbCardMixin
from Registry.Utils import (
    CCheckNetMixin,
    CClientSurveillanceInfoListEx,
    getClientBanner,
    CClientInfo,
    CSocStatusClassInfo,
    getProphylaxisPlanningType,
    updateDiagnosisRecords,
    createDiagnosticRecords
)
from Registry.RegistryTable         import CSNILSCol
from Registry.ClientEditDialog      import CClientEditDialog
from Reports.ReportBase             import CReportBase, createTable
from Reports.ReportView             import CReportViewDialog
from Reports.Utils                  import dateRangeAsStr
from library                        import database
from library.PrintInfo              import CInfoContext, CDateInfo
from Orgs.PersonComboBoxEx          import CPersonFindInDocTableCol
from Orgs.PersonInfo                import CPersonInfo
from RefBooks.Speciality.Info       import CSpecialityInfoList
from Orgs.Utils                     import COrgInfo, COrgStructureInfo
from Orgs.Utils                     import (
                                            getOrgStructureAddressIdList,
                                            getOrgStructureDescendants,
                                            getPersonInfo,
                                           )
from KLADR.Utils                    import getLikeMaskForRegion
from KLADR.KLADRModel               import getCityName, getStreetName
from library.PrintTemplates         import (
                                            getPrintButton,
                                            applyTemplate,
                                            CPrintAction,
                                            getPrintTemplates,
                                           )
from Users.Rights                   import (
                                            urSurReadEvent,
                                            urSurReadClientInfo,
                                            urSurEditEvent,
                                            urSurEditClientInfo,
                                            urSurvChangePerson,
                                            urRegTabReadAmbCard,
                                            urRegTabWriteAmbCard,
                                           )
from HospitalBeds.HospitalizationEventDialog import CFindClientInfoDialog

from Ui_SurveillanceDialog import Ui_SurveillanceDialog


class CSurveillanceDialog(CDialogBase, CAmbCardMixin, CCheckNetMixin, Ui_SurveillanceDialog):
    @pyqtSignature('')
    def on_tblAmbCardStatusActions_popupMenuAboutToShow(self): CAmbCardMixin.on_tblAmbCardStatusActions_popupMenuAboutToShow(self)
    @pyqtSignature('')
    def on_tblAmbCardDiagnosticActions_popupMenuAboutToShow(self): CAmbCardMixin.on_tblAmbCardDiagnosticActions_popupMenuAboutToShow(self)
    @pyqtSignature('')
    def on_tblAmbCardCureActions_popupMenuAboutToShow(self): CAmbCardMixin.on_tblAmbCardCureActions_popupMenuAboutToShow(self)
    @pyqtSignature('')
    def on_tblAmbCardMiscActions_popupMenuAboutToShow(self): CAmbCardMixin.on_tblAmbCardMiscActions_popupMenuAboutToShow(self)
    @pyqtSignature('')
    def on_actAmbCardActionTypeGroupId_triggered(self): CAmbCardMixin.on_actAmbCardActionTypeGroupId_triggered(self)
    @pyqtSignature('')
    def on_actAmbCardOpenActionELMK_triggered(self): CAmbCardMixin.on_actAmbCardOpenActionELMK_triggered(self)
    @pyqtSignature('QModelIndex')
    def on_tblAmbCardStatusActions_doubleClicked(self, *args): CAmbCardMixin.on_tblAmbCardStatusActions_doubleClicked(self, *args)
    @pyqtSignature('QModelIndex')
    def on_tblAmbCardDiagnosticActions_doubleClicked(self, *args): CAmbCardMixin.on_tblAmbCardDiagnosticActions_doubleClicked(self, *args)
    @pyqtSignature('QModelIndex')
    def on_tblAmbCardCureActions_doubleClicked(self, *args): CAmbCardMixin.on_tblAmbCardCureActions_doubleClicked(self, *args)
    @pyqtSignature('QModelIndex')
    def on_tblAmbCardMiscActions_doubleClicked(self, *args): CAmbCardMixin.on_tblAmbCardMiscActions_doubleClicked(self, *args)
    @pyqtSignature('int')
    def on_cmbAmbCardDiagnosticsSpeciality_currentIndexChanged(self, *args): CAmbCardMixin.on_cmbAmbCardDiagnosticsSpeciality_currentIndexChanged(self, *args)
    @pyqtSignature('QAbstractButton*')
    def on_cmdAmbCardDiagnosticsButtonBox_clicked(self, *args): CAmbCardMixin.on_cmdAmbCardDiagnosticsButtonBox_clicked(self, *args)
    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelAmbCardDiagnostics_currentRowChanged(self, *args): CAmbCardMixin.on_selectionModelAmbCardDiagnostics_currentRowChanged(self, *args)
    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelAmbCardVisits_currentRowChanged(self, *args): CAmbCardMixin.on_selectionModelAmbCardVisits_currentRowChanged(self, *args)
    @pyqtSignature('int')
    def on_tabAmbCardDiagnosticDetails_currentChanged(self, *args): CAmbCardMixin.on_tabAmbCardDiagnosticDetails_currentChanged(self, *args)
    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelAmbCardDiagnosticsActions_currentRowChanged(self, *args): CAmbCardMixin.on_selectionModelAmbCardDiagnosticsActions_currentRowChanged(self, *args)
    @pyqtSignature('')
    def on_actDiagnosticsShowPropertyHistory_triggered(self): CAmbCardMixin.on_actDiagnosticsShowPropertyHistory_triggered(self)
    @pyqtSignature('')
    def on_actDiagnosticsShowPropertiesHistory_triggered(self): CAmbCardMixin.on_actDiagnosticsShowPropertiesHistory_triggered(self)
    @pyqtSignature('int')
    def on_tabAmbCardContent_currentChanged(self, *args): CAmbCardMixin.on_tabAmbCardContent_currentChanged(self, *args)
    @pyqtSignature('')
    def on_actAmbCardPrintEvents_triggered(self): CAmbCardMixin.on_actAmbCardPrintEvents_triggered(self)
    @pyqtSignature('int')
    def on_actAmbCardPrintCaseHistory_printByTemplate(self, *args): CAmbCardMixin.on_actAmbCardPrintCaseHistory_printByTemplate(self, *args)
    @pyqtSignature('')
    def on_mnuAmbCardPrintActions_aboutToShow(self): CAmbCardMixin.on_mnuAmbCardPrintActions_aboutToShow(self)
    @pyqtSignature('int')
    def on_actAmbCardPrintAction_printByTemplate(self, *args): CAmbCardMixin.on_actAmbCardPrintAction_printByTemplate(self, *args)
    @pyqtSignature('')
    def on_actAmbCardPrintActions_triggered(self): CAmbCardMixin.on_actAmbCardPrintActions_triggered(self)
    @pyqtSignature('')
    def on_actAmbCardCopyAction_triggered(self): CAmbCardMixin.on_actAmbCardCopyAction_triggered(self)
    @pyqtSignature('int')
    def on_actAmbCardPrintActionsHistory_printByTemplate(self, *args): CAmbCardMixin.on_actAmbCardPrintActionsHistory_printByTemplate(self, *args)
    @pyqtSignature('QAbstractButton*')
    def on_cmdAmbCardStatusButtonBox_clicked(self, *args): CAmbCardMixin.on_cmdAmbCardStatusButtonBox_clicked(self, *args)
    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelAmbCardStatusActions_currentRowChanged(self, *args): CAmbCardMixin.on_selectionModelAmbCardStatusActions_currentRowChanged(self, *args)
    @pyqtSignature('')
    def on_actStatusShowPropertyHistory_triggered(self): CAmbCardMixin.on_actStatusShowPropertyHistory_triggered(self)
    @pyqtSignature('')
    def on_actStatusShowPropertiesHistory_triggered(self): CAmbCardMixin.on_actStatusShowPropertiesHistory_triggered(self)
    @pyqtSignature('QAbstractButton*')
    def on_cmdAmbCardDiagnosticButtonBox_clicked(self, *args): CAmbCardMixin.on_cmdAmbCardDiagnosticButtonBox_clicked(self, *args)
    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelAmbCardDiagnosticActions_currentRowChanged(self, *args): CAmbCardMixin.on_selectionModelAmbCardDiagnosticActions_currentRowChanged(self, *args)
    @pyqtSignature('')
    def on_actDiagnosticShowPropertyHistory_triggered(self): CAmbCardMixin.on_actDiagnosticShowPropertyHistory_triggered(self)
    @pyqtSignature('')
    def on_actDiagnosticShowPropertiesHistory_triggered(self): CAmbCardMixin.on_actDiagnosticShowPropertiesHistory_triggered(self)
    @pyqtSignature('QAbstractButton*')
    def on_cmdAmbCardCureButtonBox_clicked(self, *args): CAmbCardMixin.on_cmdAmbCardCureButtonBox_clicked(self, *args)
    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelAmbCardCureActions_currentRowChanged(self, *args): CAmbCardMixin.on_selectionModelAmbCardCureActions_currentRowChanged(self, *args)
    @pyqtSignature('')
    def on_actCureShowPropertyHistory_triggered(self): CAmbCardMixin.on_actCureShowPropertyHistory_triggered(self)
    @pyqtSignature('')
    def on_actCureShowPropertiesHistory_triggered(self): CAmbCardMixin.on_actCureShowPropertiesHistory_triggered(self)
    @pyqtSignature('QAbstractButton*')
    def on_cmdAmbCardVisitButtonBox_clicked(self, *args): CAmbCardMixin.on_cmdAmbCardVisitButtonBox_clicked(self, *args)
    @pyqtSignature('')
    def on_actAmbCardPrintVisits_triggered(self): CAmbCardMixin.on_actAmbCardPrintVisits_triggered(self)
    @pyqtSignature('QAbstractButton*')
    def on_cmdAmbCardMiscButtonBox_clicked(self, *args): CAmbCardMixin.on_cmdAmbCardMiscButtonBox_clicked(self, *args)
    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelAmbCardMiscActions_currentRowChanged(self, *args): CAmbCardMixin.on_selectionModelAmbCardMiscActions_currentRowChanged(self, *args)
    @pyqtSignature('')
    def on_actMiscShowPropertyHistory_triggered(self): CAmbCardMixin.on_actMiscShowPropertyHistory_triggered(self)
    @pyqtSignature('')
    def on_actMiscShowPropertiesHistory_triggered(self): CAmbCardMixin.on_actMiscShowPropertiesHistory_triggered(self)
    @pyqtSignature('')
    def on_tblAmbCardSurveyActions_popupMenuAboutToShow(self): CAmbCardMixin.on_tblAmbCardSurveyActions_popupMenuAboutToShow(self)
    @pyqtSignature('QModelIndex')
    def on_tblAmbCardSurveyActions_doubleClicked(self, *args): CAmbCardMixin.on_tblAmbCardSurveyActions_doubleClicked(self, *args)
    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelAmbCardSurveyActions_currentRowChanged(self, *args): CAmbCardMixin.on_selectionModelAmbCardSurveyActions_currentRowChanged(self, *args)
    @pyqtSignature('QAbstractButton*')
    def on_cmdAmbCardSurveyButtonBox_clicked(self, *args): CAmbCardMixin.on_cmdAmbCardSurveyButtonBox_clicked(self, *args)
    @pyqtSignature('')
    def on_actSurveyShowPropertyHistory_triggered(self): CAmbCardMixin.on_actSurveyShowPropertyHistory_triggered(self)
    @pyqtSignature('')
    def on_actSurveyShowPropertiesHistory_triggered(self): CAmbCardMixin.on_actSurveyShowPropertiesHistory_triggered(self)

    def __init__(self, parent, isFake=False):
        CDialogBase.__init__(self, parent)
        CCheckNetMixin.__init__(self)
        self.addModels('ConsistsClients',    CConsistsClientsModel(self))
        self.addModels('ConsistsDiagnosis',  CConsistsDiagnosisModel(self))
        self.addModels('ConsistsMonitoring', CConsistsMonitoringModel(self))
        self.addModels('ConsistsPlanning',   CConsistsPlanningModel(self))
        self.addModels('TakenClients',       CTakenClientsModel(self))
        self.addModels('TakenDiagnosis',     CTakenDiagnosisModel(self))
        self.addModels('TakenMonitoring',    CTakenMonitoringModel(self))
        self.addModels('TakenPlanning',      CTakenPlanningModel(self))
        self.addModels('RemoveClients',      CRemoveClientsModel(self))
        self.addModels('RemoveDiagnosis',    CRemoveDiagnosisModel(self))
        self.addModels('RemoveMonitoring',   CRemoveMonitoringModel(self))
        self.addModels('RemovePlanning',     CRemovePlanningModel(self))
        self.addModels('SubjectToSurveillanceClients', CSubjectToSurveillanceClientsModel(self))
        self.addModels('SubjectToSurveillanceDiagnosis', CSubjectToSurveillanceDiagnosisModel(self))
        self.addModels('SubjectToSurveillanceMonitoring', CSubjectToSurveillanceMonitoringModel(self))
        self.addModels('SubjectToSurveillancePlanning', CSubjectToSurveillancePlanningModel(self))
        self.addObject('btnPrint', getPrintButton(self, ''))
        self.setupClientsMenu()
        self.setupDiagnosisMenu()
        self.setupMonitoringMenu()
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setModels(self.tblConsistsClients, self.modelConsistsClients, self.selectionModelConsistsClients)
        self.setModels(self.tblConsistsDiagnosis, self.modelConsistsDiagnosis, self.selectionModelConsistsDiagnosis)
        self.setModels(self.tblConsistsMonitoring, self.modelConsistsMonitoring, self.selectionModelConsistsMonitoring)
        self.setModels(self.tblConsistsPlanning, self.modelConsistsPlanning, self.selectionModelConsistsPlanning)
        self.setModels(self.tblTakenClients, self.modelTakenClients, self.selectionModelTakenClients)
        self.setModels(self.tblTakenDiagnosis, self.modelTakenDiagnosis, self.selectionModelTakenDiagnosis)
        self.setModels(self.tblTakenMonitoring, self.modelTakenMonitoring, self.selectionModelTakenMonitoring)
        self.setModels(self.tblTakenPlanning, self.modelTakenPlanning, self.selectionModelTakenPlanning)
        self.setModels(self.tblRemoveClients, self.modelRemoveClients, self.selectionModelRemoveClients)
        self.setModels(self.tblRemoveDiagnosis, self.modelRemoveDiagnosis, self.selectionModelRemoveDiagnosis)
        self.setModels(self.tblRemoveMonitoring, self.modelRemoveMonitoring, self.selectionModelRemoveMonitoring)
        self.setModels(self.tblRemovePlanning, self.modelRemovePlanning, self.selectionModelRemovePlanning)
        self.setModels(self.tblSubjectToSurveillanceClients, self.modelSubjectToSurveillanceClients, self.selectionModelSubjectToSurveillanceClients)
        self.setModels(self.tblSubjectToSurveillanceDiagnosis, self.modelSubjectToSurveillanceDiagnosis, self.selectionModelSubjectToSurveillanceDiagnosis)
        self.setModels(self.tblSubjectToSurveillanceMonitoring, self.modelSubjectToSurveillanceMonitoring, self.selectionModelSubjectToSurveillanceMonitoring)
        self.setModels(self.tblSubjectToSurveillancePlanning, self.modelSubjectToSurveillancePlanning, self.selectionModelSubjectToSurveillancePlanning)
        self.buttonBox.addButton(self.btnPrint, QtGui.QDialogButtonBox.ActionRole)
        self.tblConsistsClients.setPopupMenu(self.mnuClients)
        self.tblConsistsDiagnosis.setPopupMenu(self.mnuDiagnosis)
        self.tblConsistsMonitoring.setPopupMenu(self.mnuMonitoring)
        self.tblTakenClients.setPopupMenu(self.mnuClients)
        self.tblTakenDiagnosis.setPopupMenu(self.mnuDiagnosis)
        self.tblTakenMonitoring.setPopupMenu(self.mnuMonitoring)
        self.tblRemoveClients.setPopupMenu(self.mnuClients)
        self.tblRemoveDiagnosis.setPopupMenu(self.mnuDiagnosis)
        self.tblRemoveMonitoring.setPopupMenu(self.mnuMonitoring)
        self.tblSubjectToSurveillanceClients.setPopupMenu(self.mnuClients)
        self.tblSubjectToSurveillanceDiagnosis.setPopupMenu(self.mnuDiagnosis)
        self.tblSubjectToSurveillanceMonitoring.setPopupMenu(self.mnuMonitoring)
        for tableView in [self.tblConsistsPlanning, self.tblTakenPlanning, self.tblRemovePlanning, self.tblSubjectToSurveillancePlanning]:
            tableView.createPopupMenu()
            tableView.addPopupDelRow()
            tableView.addPopupRecordProperies()
        self.tblConsistsClients.enableColsMove()
        self.tblConsistsDiagnosis.enableColsMove()
        self.tblConsistsMonitoring.enableColsMove()
        self.tblConsistsPlanning.enableColsMove()
        self.tblTakenClients.enableColsMove()
        self.tblTakenDiagnosis.enableColsMove()
        self.tblTakenMonitoring.enableColsMove()
        self.tblTakenPlanning.enableColsMove()
        self.tblRemoveClients.enableColsMove()
        self.tblRemoveDiagnosis.enableColsMove()
        self.tblRemoveMonitoring.enableColsMove()
        self.tblRemovePlanning.enableColsMove()
        self.tblSubjectToSurveillanceClients.enableColsMove()
        self.tblSubjectToSurveillanceDiagnosis.enableColsMove()
        self.tblSubjectToSurveillanceMonitoring.enableColsMove()
        self.tblSubjectToSurveillancePlanning.enableColsMove()
        self.txtConsistsClientInfoBrowser.actions.append(self.actEditClientInfoBeds)
        self.txtConsistsClientInfoBrowser.actions.append(self.actPortal_Doctor)
        self.txtTakenClientInfoBrowser.actions.append(self.actEditClientInfoBeds)
        self.txtTakenClientInfoBrowser.actions.append(self.actPortal_Doctor)
        self.txtRemoveClientInfoBrowser.actions.append(self.actEditClientInfoBeds)
        self.txtRemoveClientInfoBrowser.actions.append(self.actPortal_Doctor)
        self.txtSubjectToSurveillanceClientInfoBrowser.actions.append(self.actEditClientInfoBeds)
        self.txtSubjectToSurveillanceClientInfoBrowser.actions.append(self.actPortal_Doctor)
        self.cmbFilterEventSpeciality.setTable(u'rbSpeciality')
        self.cmbSocStatusesType.setTable('rbSocStatusType', True)
        self.cmbFilterAccountingSystem.setTable('rbAccountingSystem',  True)
        self.cmbFilterAccountingSystem.setValue(forceRef(QtGui.qApp.preferences.appPrefs.get('FilterAccountingSystem', 0)))
        self.cmbDiseaseCharacter.setTable('rbDiseaseCharacter')

        templates = getPrintTemplates('surveillance')
        if not templates:
            self.btnPrint.setId(-1)
        else:
            for template in templates:
                action = CPrintAction(template.name, template.id, self.btnPrint, self.btnPrint)
                self.btnPrint.addAction(action)
            self.btnPrint.menu().addSeparator()
            self.btnPrint.addAction(CPrintAction(u'Список Диспансерное наблюдение', -1, self.btnPrint, self.btnPrint))
        self.btnPrint.setEnabled(True)

        self.tblConsistsPlanning.setDelRowsChecker(lambda rows: all(map(self.modelConsistsPlanning.isLocked, rows)))
        self.tblTakenPlanning.setDelRowsChecker(lambda rows: all(map(self.modelTakenPlanning.isLocked, rows)))
        self.tblRemovePlanning.setDelRowsChecker(lambda rows: all(map(self.modelRemovePlanning.isLocked, rows)))
        self.tblSubjectToSurveillancePlanning.setDelRowsChecker(lambda rows: all(map(self.modelSubjectToSurveillancePlanning.isLocked, rows)))

        self.chkList = [
            (self.chkFilterAddressOrgStructure, [self.cmbFilterAddressOrgStructureType, self.cmbFilterAddressOrgStructure]),
            (self.chkFilterAddress, [self.cmbFilterAddressType, self.cmbFilterAddressCity, self.cmbFilterAddressOkato,
                                     self.cmbFilterAddressStreet, self.lblFilterAddressHouse, self.edtFilterAddressHouse,
                                     self.lblFilterAddressCorpus, self.edtFilterAddressCorpus, self.lblFilterAddressFlat, self.edtFilterAddressFlat]),
            (self.chkSocStatuses, [self.label_4, self.edtFilterSocStatusesBegDate, self.lblFilterSocStatusesBegDate_,
                                   self.edtFilterSocStatusesEndDate, self.cmbSocStatusesClass, self.cmbSocStatusesType]),
            (self.chkFilterEvent, [self.chkEventVisitDiagnosis, self.cmbFilterEventVisitType, self.label,
                                   self.edtFilterEventVisitBegDate, self.label_3, self.edtFilterEventVisitEndDate]),
            (self.chkFilterDateRange, [self.cmbFilterPlanningType, self.label_5, self.edtFilterBegDate, self.label_6, self.edtFilterEndDate])]

        self.setChildElementsVisible(self.chkList, self.chkFilterAddressOrgStructure, False)
        self.setChildElementsVisible(self.chkList, self.chkFilterAddress, False)
        self.setChildElementsVisible(self.chkList, self.chkSocStatuses, False)
        self.setChildElementsVisible(self.chkList, self.chkFilterEvent, False)
        self.setChildElementsVisible(self.chkList, self.chkFilterDateRange, False)

        self.filter = {}
        self.resetFilter()
        self.fillingSpeciality()
        if not isFake:
            self.on_tabDispensaireClients_currentChanged(0)


    @pyqtSignature('bool')
    def on_chkFilterAddressOrgStructure_toggled(self, checked):
        self.setChildElementsVisible(self.chkList, self.chkFilterAddressOrgStructure, checked)
        self.onChkFilterToggled(self.sender(), checked)

    @pyqtSignature('bool')
    def on_chkFilterAddress_toggled(self, checked):
        self.setChildElementsVisible(self.chkList, self.chkFilterAddress, checked)
        self.onChkFilterToggled(self.sender(), checked)

    @pyqtSignature('bool')
    def on_chkSocStatuses_toggled(self, checked):
        self.setChildElementsVisible(self.chkList, self.chkSocStatuses, checked)
        self.onChkFilterToggled(self.sender(), checked)

    @pyqtSignature('bool')
    def on_chkFilterEvent_toggled(self, checked):
        self.setChildElementsVisible(self.chkList, self.chkFilterEvent, checked)
        self.onChkFilterToggled(self.sender(), checked)

    @pyqtSignature('bool')
    def on_chkFilterDateRange_toggled(self, checked):
        self.setChildElementsVisible(self.chkList, self.chkFilterDateRange, checked)
        self.onChkFilterToggled(self.sender(), checked)

    @pyqtSignature('int')
    def on_cmbSocStatusesClass_currentIndexChanged(self, index):
        socStatusClassId = self.cmbSocStatusesClass.value()
        if socStatusClassId:
            filter = (u'''rbSocStatusType.id IN (SELECT DISTINCT rbSocStatusClassTypeAssoc.type_id
            FROM  rbSocStatusClassTypeAssoc
            WHERE rbSocStatusClassTypeAssoc.class_id = %s)'''%(socStatusClassId))
        else:
            filter = u''
        self.cmbSocStatusesType.setFilter(filter)

    def setChildElementsVisible(self, chkList, parentChk, value):
        for row in chkList:
            if row[0] == parentChk:
                for childElement in row[1]:
                    childElement.setVisible(value)


    def onChkFilterToggled(self, chk, checked):
        controlled = self.findControlledByChk(chk)
        if checked:
            self.activateFilterWdgets(controlled)
        else:
            self.deactivateFilterWdgets(controlled)


    def findControlledByChk(self, chk):
        for s in self.chkList:
            if s[0] == chk:
                return s[1]


    def activateFilterWdgets(self, alist):
        if alist:
            for s in alist:
                s.setEnabled(True)
                if isinstance(s, (QtGui.QLineEdit, CDateEdit)):
                    s.selectAll()
            alist[0].setFocus(Qt.ShortcutFocusReason)
            alist[0].update()


    def deactivateFilterWdgets(self, alist):
        for s in alist:
            s.setEnabled(False)


    def setupClientsMenu(self):
        self.addObject('mnuClients', QtGui.QMenu(self))
        self.addObject('actEditClientInfoBeds', QtGui.QAction(u'Открыть регистрационную карточку', self))
        self.addObject('actPortal_Doctor', QtGui.QAction(u'Перейти на портал врача', self))
        self.addObject('actAmbCardShow',    QtGui.QAction(u'Открыть медицинскую карту', self))
        self.addObject('actSurveillancePlanningClients', QtGui.QAction(u'Контрольная карта диспансерного наблюдения', self))
        self.addObject('actGroupChangePersonDN', QtGui.QAction(u'Изменить врача по ДН всех пациентов списка', self))
        self.actEditClientInfoBeds.setShortcut('Shift+F4')
        self.mnuClients.addAction(self.actEditClientInfoBeds)
        self.mnuClients.addAction(self.actPortal_Doctor)
        self.mnuClients.addAction(self.actAmbCardShow)
        self.mnuClients.addAction(self.actSurveillancePlanningClients)
        self.mnuClients.addAction(self.actGroupChangePersonDN)


    def setupDiagnosisMenu(self):
        self.addObject('mnuDiagnosis', QtGui.QMenu(self))
        self.addObject('actChangePersonDN', QtGui.QAction(u'Изменить врача ДН', self))
        self.addObject('actGroupChangePersonDNMKB', QtGui.QAction(u'Изменить врача по ДН пациента по диагнозам', self))
        self.mnuDiagnosis.addAction(self.actChangePersonDN)
        self.mnuDiagnosis.addAction(self.actGroupChangePersonDNMKB)


    def setupMonitoringMenu(self):
        self.addObject('mnuMonitoring', QtGui.QMenu(self))
        self.addObject('actOpenEvent', QtGui.QAction(u'Открыть обращение', self))
        self.addObject('actSurveillancePlanningMonitoring', QtGui.QAction(u'Контрольная карта диспансерного наблюдения', self))
        self.actOpenEvent.setShortcut(Qt.Key_F4)
        self.mnuMonitoring.addAction(self.actOpenEvent)
        self.mnuMonitoring.addAction(self.actSurveillancePlanningMonitoring)


    def dumpParams(self, cursor, params):
        description = self.getDescription(params)
        columns = [('100%', [], CReportBase.AlignLeft)]
        table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
        for i, row in enumerate(description):
            table.setText(i, 0, row)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()


    def getDescription(self, params):
        db = QtGui.qApp.db
        rows = []
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        if begDate or endDate:
            rows.append(dateRangeAsStr(u'За период', begDate, endDate))
        orgStructureId = params.get('orgStructureId', None)
        if orgStructureId:
            rows.append(u'\n' + u'Подразделение врача: ' + forceString(QtGui.qApp.db.translate('OrgStructure', 'id', orgStructureId, 'name')))
        else:
            rows.append(u'\n' + u'ЛПУ')
        specialityType = params.get('specialityType', 0)
        specialityId = params.get('specialityId', None)
        if specialityId:
            rows.append(u'Cпециальность: ' + [u'Отбор по "ИЛИ": ', u'Отбор по "И": '][specialityType] + forceString(db.translate('rbSpeciality', 'id', specialityId, 'name')))
        MKBFilter = params.get('MKBFilter', 0)
        MKBFrom = params.get('MKBFrom', '')
        MKBTo = params.get('MKBTo', '')
        if MKBFilter == 1:
            rows.append(u'Код МКБ: с "%s" по "%s"' % (MKBFrom, MKBTo))
        diseaseCharacterId = params.get('diseaseCharacterId', None)
        if diseaseCharacterId:
            rows.append(u'Характер заболевания: ' + forceString(db.translate('rbDiseaseCharacter', 'id', diseaseCharacterId, 'name')))
        accountingSystemId = params.get('accountingSystemId', None)
        if accountingSystemId:
            accountingSystemName = forceString(db.translate('rbAccountingSystem', 'id', accountingSystemId, 'name'))
            # titleDescription += u'\n' + u'Внешняя учётная система: ' + accountingSystemName
            rows.append(u'Внешняя учётная система: ' + accountingSystemName)
        filterClientId = params.get('filterClientId', None)
        if filterClientId:
            # titleDescription += u'\n' + u'Идентификатор пациента: %s'%(str(filterClientId))
            rows.append(u'Идентификатор пациента: %s'%(str(filterClientId)))
        sex = params.get('sex', 0)
        ageFrom = params.get('ageFrom', None)
        ageTo = params.get('ageTo', None)
        if sex:
            rows.append(u'Пол: ' + formatSex(sex))
        if ageFrom is not None and ageTo is not None and ageFrom <= ageTo:
            rows.append(u'Возраст: c %d по %d %s' % (ageFrom, ageTo, agreeNumberAndWord(ageTo, (u'год', u'года', u'лет'))))
        death = params.get('death', 0)
        if death == 1:
            rows.append(u'Летальность: только живые')
        elif death == 2:
            deathBegDate = params.get('deathBegDate', None)
            deathEndDate = params.get('deathEndDate', None)
            rows.append(u'Летальность: только умершие в период с %s по %s'%(deathBegDate.toString('dd.MM.yyyy') if deathBegDate else u'', deathEndDate.toString('dd.MM.yyyy') if deathEndDate else u''))
        attachOrganisationId = params.get('attachOrganisationId', None)
        if attachOrganisationId:
            isNotAttachOrganisation = params.get('isNotAttachOrganisation', False)
            lpu = forceString(db.translate('Organisation', 'id', attachOrganisationId, 'shortName'))
            rows.append((u'Не имеет прикрепления к выбранному ЛПУ: ' if isNotAttachOrganisation else u'Прикрепление к ЛПУ: ') + lpu)
        if params.get('isFilterAddressOrgStructure', False):
            addressOrgStructureTypeId = params.get('addressOrgStructureTypeId', None)
            addressOrgStructureId = params.get('addressOrgStructureId', None)
            if addressOrgStructureId:
                addressOrgStructureType = [u'Регистрация', u'Проживание', u'Регистрация или проживание', u'Прикрепление', u'Регистрация или прикрепление', u'Проживание или прикрепление', u'Регистрация, проживание или прикрепление']
                rows.append(u'\n' + u'По участку ' + addressOrgStructureType[addressOrgStructureTypeId] + u': ' + forceString(QtGui.qApp.db.translate('OrgStructure', 'id', addressOrgStructureId, 'name')))
        if params.get('isFilterAddress', False):
            addressTypeId = params.get('addressTypeId', None)
            typeAdress = [u'регистрации', u'проживания']
            filterAddressOkato = params.get('addressOkato', 0)
            filterAddressCity = params.get('addressCity', None)
            filterAddressStreet = params.get('addressStreet', None)
            if filterAddressOkato or filterAddressCity or filterAddressStreet:
                filterAddressHouse = params.get('addressHouse', u'')
                filterAddressCorpus = params.get('addressCorpus', u'')
                filterAddressFlat = params.get('addressFlat', u'')
                rows.append(u'Адрес: ' + forceString(typeAdress[addressTypeId]) + u':')
                rows.append((u'город ' + forceString(db.translate(u'kladr.KLADR', u'CODE', filterAddressCity, u'NAME')) if filterAddressCity else u'')
                                    + ((u'район ' + forceString(db.translate(u'kladr.OKATO', u'CODE', filterAddressOkato, u'NAME'))) if filterAddressOkato else u'')
                                    + (u' улица ' + forceString(db.translate(u'kladr.STREET', u'CODE', filterAddressStreet, u'NAME')) if filterAddressStreet else u'')
                                    + (u' дом ' + forceString(filterAddressHouse) if filterAddressHouse else u'')
                                    + (u' корпус ' + forceString(filterAddressCorpus) if filterAddressCorpus else u'')
                                    + (u' квартира ' + forceString(filterAddressFlat) if filterAddressFlat else u''))
        if params.get('isSocStatuses', False):
            socStatusesClass = params.get('socStatusesClass', None)
            socStatusTypeId  = params.get('socStatusesType', None)
            if socStatusTypeId:
                rows.append(u'Тип соц.статуса: ' + forceString(db.translate('vrbSocStatusType', 'id', socStatusTypeId, 'name')))
            if socStatusesClass:
                rows.append(u'Класс соц.статуса: ' + forceString(db.translate('rbSocStatusClass', 'id', socStatusesClass, 'name')))
            if socStatusTypeId or socStatusesClass:
                socStatusesBegDate = params.get('socStatusesBegDate', QDate())
                socStatusesEndDate = params.get('socStatusesEndDate', QDate())
                rows.append(dateRangeAsStr(u'За период', socStatusesBegDate, socStatusesEndDate))
        if params.get('isFilterEvent', False):
            eventVisitType = params.get('eventVisitType', None)
            if eventVisitType is not None:
                eventVisitTypeList = [u'обращались', u'не обращались']
                chkEventVisitDiagnosis = params.get('chkEventVisitDiagnosis', 0)
                rows.append(u'Обращения: ' + (u'по Диспансерному наблюдению ' if chkEventVisitDiagnosis else u'') + eventVisitTypeList[eventVisitType])
                eventBegDate = params.get('eventBegDate', QDate())
                eventEndDate = params.get('eventEndDate', QDate())
                rows.append(dateRangeAsStr(u'За период', eventBegDate, eventEndDate))
        rows.append(u'отчёт составлен: '+forceString(QDateTime.currentDateTime()))
        return rows


    @pyqtSignature('int')
    def on_cmbFilterAttachOrganisation_currentIndexChanged(self, index):
        orgId = self.cmbFilterAttachOrganisation.value()
        self.chkFilterNotAttachOrganisation.setEnabled(bool(orgId))


    @pyqtSignature('int')
    def on_cmbFilterDeath_currentIndexChanged(self, index):
        value = self.cmbFilterDeath.currentIndex()
        self.edtFilterDeathBegDate.setEnabled(bool(value == 2))
        self.edtFilterDeathEndDate.setEnabled(bool(value == 2))


    def execDispanserObservationReport(self, model, table, messag):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(u'Диспансерное наблюдение %s' % messag)
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertBlock()
        self.dumpParams(cursor, self.filter)
        cursor.insertBlock()
        colWidths  = [table.columnWidth(i) for i in xrange(model.columnCount())]
        totalWidth = sum(colWidths)
        tableColumns = []
        for iCol, colWidth in enumerate(colWidths):
            widthInPercents = str(max(1, colWidth*90/totalWidth)) + '%'
            tableColumns.append((widthInPercents, [forceString(model._cols[iCol].title())], CReportBase.AlignLeft))
        table = createTable(cursor, tableColumns)
        for iModelRow in xrange(model.rowCount()):
            iTableRow = table.addRow()
            for iModelCol in xrange(model.columnCount()):
                index = model.createIndex(iModelRow, iModelCol)
                text = forceString(model.data(index))
                table.setText(iTableRow, iModelCol, text)
        html = doc.toHtml('utf-8')
        view = CReportViewDialog(self)
        view.setText(html)
        view.exec_()


    def execDispanserObservationReportEx(self, model, messag, modelDiagnosis):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(u'Диспансерное наблюдение %s' % messag)
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertBlock()
        self.dumpParams(cursor, self.filter)
        cursor.insertBlock()
        tableColumns = []
        for iCol in xrange(model.columnCount()):
            tableColumns.append(('', [forceString(model._cols[iCol].title())], CReportBase.AlignLeft))
        tableColumns.append(('', [u'Контакты'], CReportBase.AlignLeft))
        tableColumns.append(('', [u'Адрес'], CReportBase.AlignLeft))
        tableColumns.append(('', [u'Участок'], CReportBase.AlignLeft))
        tableColumns.append(('', [u'МКБ'], CReportBase.AlignLeft))
        tableColumns.append(('', [u'Врач'], CReportBase.AlignLeft))
        tableColumns.append(('', [u'Дата последнего осмотра'], CReportBase.AlignLeft))
        table = createTable(cursor, tableColumns)
        for iModelRow in xrange(model.rowCount()):
            iTableRow = table.addRow()
            clientId = forceInt(model.data(model.createIndex(iModelRow, 0)))
            contacts, address, attach, mkb, person, date = modelDiagnosis.getPrintData(clientId, self.filter)
            cols = model.columnCount()
            for iModelCol in xrange(cols):
                index = model.createIndex(iModelRow, iModelCol)
                text = forceString(model.data(index))
                table.setText(iTableRow, iModelCol, text)
            table.setText(iTableRow, cols,   contacts)
            table.setText(iTableRow, cols+1, address)
            table.setText(iTableRow, cols+2, attach)
            table.setText(iTableRow, cols+3, mkb)
            table.setText(iTableRow, cols+4, person)
            table.setText(iTableRow, cols+5, date)
        html = doc.toHtml('utf-8')
        view = CReportViewDialog(self)
        view.setText(html)
        view.exec_()


    @pyqtSignature('int')
    def on_btnPrint_printByTemplate(self, templateId):
        widgetIndex = self.tabDispensaireClients.currentIndex()
        messag = ''
        if widgetIndex == 0:
            model = self.modelConsistsClients
            tableClients = self.tblConsistsClients
            messag = u'Состоят'
            modelDiagnostic = self.modelConsistsMonitoring
            modelDiagnosis = self.modelConsistsDiagnosis
        elif widgetIndex == 1:
            model = self.modelTakenClients
            tableClients = self.tblTakenClients
            messag = u'Взяты'
            modelDiagnostic = self.modelTakenMonitoring
            modelDiagnosis = self.modelTakenDiagnosis
        elif widgetIndex == 2:
            model = self.modelRemoveClients
            tableClients = self.tblRemoveClients
            messag = u'Сняты'
            modelDiagnostic = self.modelRemoveMonitoring
        elif widgetIndex == 3:
            model = self.modelSubjectToSurveillanceClients
            tableClients = self.tblSubjectToSurveillanceClients
            messag = u'Подлежат'
            modelDiagnostic = self.modelSubjectToSurveillanceMonitoring

        if templateId == -1:
            if widgetIndex == 0 or widgetIndex == 1:
                self.execDispanserObservationReportEx(model, messag, modelDiagnosis)
            else:
                self.execDispanserObservationReport(model, tableClients, messag)
        else:
            db = QtGui.qApp.db
            death = self.cmbFilterDeath.currentIndex()
            addressOkatoCode = self.cmbFilterAddressOkato.value()
            addressCityCode = self.cmbFilterAddressCity.code()
            addressStreetCode = self.cmbFilterAddressStreet.code()
            tableKladrOKATO = db.table('kladr.OKATO')
            tableKladrSTREET = db.table('kladr.STREET')
            tableKladrKLADR = db.table('kladr.KLADR')
            addressOkatoName = forceStringEx(db.translate(tableKladrOKATO, u'CODE', addressOkatoCode, u'kladr.OKATO.NAME')) if addressOkatoCode else u''
            addressCitySOCR = forceStringEx(db.translate(tableKladrKLADR, u'CODE', addressCityCode, u'kladr.KLADR.SOCR')) if addressCityCode else u''
            addressStreetSOCR = forceStringEx(db.translate(tableKladrSTREET, u'CODE', addressStreetCode, u'kladr.STREET.SOCR')) if addressStreetCode else u''
            context = CInfoContext()
            specialityListId = []
            specialityList = self.cmbFilterEventSpeciality.value()
            if specialityList:
                specialityLine = specialityList.split(u',')
                for speciality in specialityLine:
                    specialityId = int(trim(speciality))
                    if specialityId and specialityId not in specialityListId:
                        specialityListId.append(specialityId)
            clientInfoList = context.getInstance(CClientSurveillanceInfoListEx, tuple(model.idList()))
            for i, clientInfo in enumerate(clientInfoList):
                clientInfoList[i]._diagnostics = context.getInstance(CDiagnosticInfoIdList, tuple(modelDiagnostic.getDiagnosticIdList(clientInfo.id, self.filter)))
            data = {'clientsInfo': clientInfoList,
                    'begDate': CDateInfo(self.edtFilterEventBegDate.date()),
                    'endDate': CDateInfo(self.edtFilterEventEndDate.date()),
                    'orgStructureId': context.getInstance(COrgStructureInfo, self.cmbFilterEventOrgStructure.value()),
                    'specialityType': self.cmbFilterEventSpecialityType.currentIndex(),
                    'specialityId': context.getInstance(CSpecialityInfoList, specialityListId),
                    'MKBFilter': self.cmbMKBFilter.currentIndex(),
                    'MKBFrom': context.getInstance(CMKBInfo, forceString(self.edtMKBFrom.text())),
                    'MKBTo': context.getInstance(CMKBInfo, forceString(self.edtMKBTo.text())),
                    'sex': formatSex(forceInt(self.cmbSex.currentIndex())),
                    'ageFor': self.spbAgeFor.value(),
                    'ageTo': self.spbAgeTo.value(),
                    'death': death,
                    'deathBegDate': CDateInfo(self.edtFilterDeathBegDate.date() if death == 2 else None),
                    'deathEndDate': CDateInfo(self.edtFilterDeathEndDate.date()if death == 2 else None),
                    'attachOrganisationId': context.getInstance(COrgInfo, self.cmbFilterAttachOrganisation.value()),
                    'isNotAttachOrganisation': self.chkFilterNotAttachOrganisation.isChecked(),
                    'isFilterAddressOrgStructure': self.chkFilterAddressOrgStructure.isChecked(),
                    'addressOrgStructureTypeId': self.cmbFilterAddressOrgStructureType.currentIndex(),
                    'addressOrgStructureId': context.getInstance(COrgStructureInfo, self.cmbFilterAddressOrgStructure.value()),
                    'isFilterAddress': self.chkFilterAddress.isChecked(),
                    'addressTypeId': self.cmbFilterAddressType.currentIndex(),
                    'addressCityCode': addressCityCode,
                    'addressCityName': getCityName(addressCityCode) if addressCityCode else u'',
                    'addressCitySOCR': addressCitySOCR,
                    'addressOkatoCode': addressOkatoCode,
                    'addressOkatoName': addressOkatoName,
                    'addressStreetCode': addressStreetCode,
                    'addressStreetName': getStreetName(addressStreetCode) if addressStreetCode else u'',
                    'addressStreetSOCR': addressStreetSOCR,
                    'KLADRStreetCodeList': self.cmbFilterAddressStreet.codeList(),
                    'addressHouse': self.edtFilterAddressHouse.text(),
                    'addressCorpus': self.edtFilterAddressCorpus.text(),
                    'addressFlat': self.edtFilterAddressFlat.text(),
                    'isSocStatuses': self.chkSocStatuses.isChecked(),
                    'socStatusesBegDate': CDateInfo(self.edtFilterSocStatusesBegDate.date()),
                    'socStatusesEndDate': CDateInfo(self.edtFilterSocStatusesEndDate.date()),
                    'socStatusesClass': context.getInstance(CSocStatusClassInfo, self.cmbSocStatusesClass.value()),
                    'socStatusesType': context.getInstance(CSocStatusType, self.cmbSocStatusesType.value()),
                    'isFilterEvent': self.chkFilterEvent.isChecked(),
                    'isEventVisitDiagnosis': self.chkEventVisitDiagnosis.isChecked(),
                    'eventVisitType': self.cmbFilterEventVisitType.currentIndex(),
                    'eventBegDate': CDateInfo(self.edtFilterEventVisitBegDate.date()),
                    'eventEndDate': CDateInfo(self.edtFilterEventVisitEndDate.date()),
                    'accountingSystemId': context.getInstance(CAccountingSystemInfo, self.cmbFilterAccountingSystem.value()),
                    'filterClientId': context.getInstance(CClientInfo, forceRef(QVariant(self.edtFilterClientId.text()))),
                    'messag': messag
                    }
            QtGui.qApp.call(self, applyTemplate, (self, templateId, data))


    @pyqtSignature('QAbstractButton*')
    def on_buttonBoxFilter_clicked(self, button):
        buttonCode = self.buttonBoxFilter.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.setFilter()
            self.on_tabDispensaireClients_currentChanged(self.tabDispensaireClients.currentIndex())
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.resetFilter()


    def setFilter(self):
        self.filter = {}
        self.filter['personDN'] = self.cmbFilterPersonDN.value()
        self.filter['begDate'] = self.edtFilterEventBegDate.date()
        self.filter['endDate'] = self.edtFilterEventEndDate.date()
        self.filter['orgStructureId'] = self.cmbFilterEventOrgStructure.value()
        self.filter['specialityType'] = self.cmbFilterEventSpecialityType.currentIndex()
        self.filter['specialityId'] = self.cmbFilterEventSpeciality.value()
        self.filter['MKBFilter'] = self.cmbMKBFilter.currentIndex()
        self.filter['MKBFrom']   = unicode(self.edtMKBFrom.text())
        self.filter['MKBTo']     = unicode(self.edtMKBTo.text())
        self.filter['diseaseCharacterId'] = self.cmbDiseaseCharacter.value()
        self.filter['diseaseCharacterName'] = self.cmbDiseaseCharacter.name() #Не для поиска. Чтобы запоминать значение
        self.filter['sex'] = self.cmbSex.currentIndex()
        self.filter['ageFor'] = self.spbAgeFor.value()
        self.filter['ageTo'] = self.spbAgeTo.value()
        death = self.cmbFilterDeath.currentIndex()
        self.filter['death'] = death
        if death == 2:
            self.filter['deathBegDate'] = self.edtFilterDeathBegDate.date()
            self.filter['deathEndDate'] = self.edtFilterDeathEndDate.date()
        self.filter['attachOrganisationId'] = self.cmbFilterAttachOrganisation.value()
        self.filter['isNotAttachOrganisation'] = self.chkFilterNotAttachOrganisation.isChecked()
        self.filter['isFilterAddressOrgStructure'] = self.chkFilterAddressOrgStructure.isChecked()
        if self.chkFilterAddressOrgStructure.isChecked():
            self.filter['addressOrgStructureTypeId'] = self.cmbFilterAddressOrgStructureType.currentIndex()
            self.filter['addressOrgStructureId'] = self.cmbFilterAddressOrgStructure.value()
        self.filter['isFilterAddress'] = self.chkFilterAddress.isChecked()
        if self.chkFilterAddress.isChecked():
            self.filter['addressTypeId'] = self.cmbFilterAddressType.currentIndex()
            self.filter['addressCity'] = self.cmbFilterAddressCity.code()
            self.filter['addressOkato'] = self.cmbFilterAddressOkato.value()
            self.filter['KLADRStreetCodeList'] = self.cmbFilterAddressStreet.codeList()
            self.filter['addressStreet'] = self.cmbFilterAddressStreet.code()
            self.filter['addressHouse'] = self.edtFilterAddressHouse.text()
            self.filter['addressCorpus'] = self.edtFilterAddressCorpus.text()
            self.filter['addressFlat'] = self.edtFilterAddressFlat.text()
        self.filter['isSocStatuses'] = self.chkSocStatuses.isChecked()
        if self.chkSocStatuses.isChecked():
            self.filter['socStatusesBegDate'] = self.edtFilterSocStatusesBegDate.date()
            self.filter['socStatusesEndDate'] = self.edtFilterSocStatusesEndDate.date()
            self.filter['socStatusesClass'] = self.cmbSocStatusesClass.value()
            self.filter['socStatusesType'] = self.cmbSocStatusesType.value()
        self.filter['isFilterEvent'] = self.chkFilterEvent.isChecked()
        if self.chkFilterEvent.isChecked():
            self.filter['chkEventVisitDiagnosis'] = self.chkEventVisitDiagnosis.isChecked()
            self.filter['eventVisitType'] = self.cmbFilterEventVisitType.currentIndex()
            self.filter['eventBegDate'] = self.edtFilterEventVisitBegDate.date()
            self.filter['eventEndDate'] = self.edtFilterEventVisitEndDate.date()
        self.filter['accountingSystemId'] = self.cmbFilterAccountingSystem.value()
        self.filter['filterClientId'] = forceStringEx(self.edtFilterClientId.text())
        if self.chkFilterDateRange.isChecked():
            self.filter['planningType'] = self.cmbFilterPlanningType.currentIndex()
            self.filter['dateRange'] = self.edtFilterBegDate.date(), self.edtFilterEndDate.date()
            self.filter['begVisitDate'] = self.edtFilterBegDate.date()
            self.filter['endVisitDate'] = self.edtFilterEndDate.date()


    def resetFilter(self):
        personId = None
        if QtGui.qApp.isGetPersonStationary():
            personId = QtGui.qApp.userId if QtGui.qApp.userSpecialityId else None
        self.cmbFilterPersonDN.setValue(personId)
        self.edtFilterEventBegDate.setDate(QDate.currentDate())
        self.edtFilterEventEndDate.setDate(QDate())
        self.cmbFilterEventOrgStructure.setValue(None)
        self.cmbFilterEventSpecialityType.setCurrentIndex(0)
        self.cmbFilterEventSpeciality.clearValue()
        self.cmbFilterEventSpeciality.setValue(None)
        self.cmbFilterEventSpeciality.setText(u'')
        self.cmbMKBFilter.setCurrentIndex(0)
        self.edtMKBFrom.setText('A__. _')
        self.edtMKBTo.setText('Z99.9_')
        self.on_cmbMKBFilter_currentIndexChanged(0)
        self.cmbDiseaseCharacter.setValue(None)
        self.cmbSex.setCurrentIndex(0)
        self.spbAgeFor.setValue(0)
        self.spbAgeTo.setValue(self.spbAgeTo.maximum())
        self.cmbFilterDeath.setCurrentIndex(1)
        self.edtFilterDeathBegDate.setDate(QDate())
        self.edtFilterDeathEndDate.setDate(QDate())
        self.cmbFilterAttachOrganisation.setValue(None)
        self.chkFilterNotAttachOrganisation.setChecked(False)
        self.cmbFilterAddressOrgStructureType.setCurrentIndex(0)
        self.cmbFilterAddressOrgStructure.setValue(None)
        self.cmbFilterAddressType.setCurrentIndex(0)
        self.cmbFilterAddressCity.setCode(u'')
        self.cmbFilterAddressOkato.setValue(None)
        self.cmbFilterAddressStreet.setCode(u'')
        self.edtFilterAddressHouse.setText(u'')
        self.edtFilterAddressCorpus.setText(u'')
        self.edtFilterAddressFlat.setText(u'')
        self.edtFilterSocStatusesBegDate.setDate(QDate())
        self.edtFilterSocStatusesEndDate.setDate(QDate())
        self.cmbSocStatusesClass.setValue(None)
        self.cmbSocStatusesType.setValue(None)
        self.chkEventVisitDiagnosis.setChecked(False)
        self.cmbFilterEventVisitType.setCurrentIndex(0)
        self.edtFilterEventVisitBegDate.setDate(QDate(QDate.currentDate().year(), 1, 1))
        self.edtFilterEventVisitEndDate.setDate(QDate(QDate.currentDate().year(), 12, 31))
        self.cmbFilterAccountingSystem.setValue(None)
        self.edtFilterClientId.setText('')
        self.chkFilterAddressOrgStructure.setChecked(False)
        self.chkFilterAddress.setChecked(False)
        self.chkSocStatuses.setChecked(False)
        self.chkFilterEvent.setChecked(False)
        self.edtFilterEventBegDate.setDate(QDate.currentDate().addMonths(-1))
        self.setFilter()


    def fillingSpeciality(self):
        userId = QtGui.qApp.userId
        userSpecialityId = QtGui.qApp.userSpecialityId
        specialityId = None
        if userId and userSpecialityId:
            db = QtGui.qApp.db
            table = db.table('Person')
            tableRBPost = db.table('rbPost')
            cond = [table['id'].eq(userId),
                    table['deleted'].eq(0),
                    u'''LEFT(rbPost.code, 1) IN ('1','2','3')'''
                    ]
            queryTable = table.innerJoin(tableRBPost, tableRBPost['id'].eq(table['post_id']))
            record = db.getRecordEx(queryTable, ['speciality_id'], cond)
            if record:
                specialityId = forceRef(record.value('speciality_id'))
        self.cmbFilterEventSpecialityType.setCurrentIndex(0)
        self.cmbFilterEventSpeciality.clearValue()
        self.cmbFilterEventSpeciality.setValue((u'%s'%(forceString(specialityId))) if specialityId else None)
        if not specialityId:
            self.cmbFilterEventSpeciality.setText(u'')


    @pyqtSignature('int')
    def on_cmbMKBFilter_currentIndexChanged(self, index):
        mode = bool(index)
        for widget in (self.edtMKBFrom, self.edtMKBTo):
            widget.setEnabled(mode)


    @pyqtSignature('')
    def on_btnFindClientInfo_clicked(self):
        self.cmbFilterAccountingSystem.setValue(None)
        self.edtFilterClientId.setText('')
        clientIdList = self.getCurrentClientsTable().model().idList()
        dialog = CSurveillanceFindClientInfoDialog(self, clientIdList)
        if dialog:
            dialog.setWindowTitle(u'''Поиск пациента''')
            dialog.exec_()
            self.edtFilterClientId.setText(forceString(dialog.filterClientId))


    @pyqtSignature('int')
    def on_cmbFilterAddressCity_currentIndexChanged(self, index):
        code = self.cmbFilterAddressCity.code()
        self.cmbFilterAddressOkato.setEnabled(True)
        self.cmbFilterAddressOkato.setKladrCode(code)
        self.cmbFilterAddressStreet.setCity(code)


    @pyqtSignature('int')
    def on_cmbFilterAddressOkato_currentIndexChanged(self, index):
        okato = self.cmbFilterAddressOkato.value()
        self.cmbFilterAddressStreet.setOkato(okato)


    @pyqtSignature('')
    def on_mnuClients_aboutToShow(self):
        isEnabled = False
        controlCardBtnEnabled = True
        widgetIndex = self.tabDispensaireClients.currentIndex()
        if widgetIndex == 0:
            self.tblConsistsClients.setFocus(Qt.OtherFocusReason)
            currentIndex = self.tblConsistsClients.currentIndex()
            isEnabled = currentIndex.row() >= 0
        elif widgetIndex == 1:
            self.tblTakenClients.setFocus(Qt.TabFocusReason)
            currentIndex = self.tblTakenClients.currentIndex()
            isEnabled = currentIndex.row() >= 0
        elif widgetIndex == 2:
            self.tblRemoveClients.setFocus(Qt.OtherFocusReason)
            currentIndex = self.tblRemoveClients.currentIndex()
            isEnabled = currentIndex.row() >= 0
        elif widgetIndex == 3:
            self.tblSubjectToSurveillanceClients.setFocus(Qt.OtherFocusReason)
            currentIndex = self.tblSubjectToSurveillanceClients.currentIndex()
            isEnabled = currentIndex.row() >= 0
            controlCardBtnEnabled = False
        self.actEditClientInfoBeds.setEnabled(isEnabled)
        self.actAmbCardShow.setEnabled(isEnabled)
        self.actSurveillancePlanningClients.setEnabled(controlCardBtnEnabled)
        self.actGroupChangePersonDN.setEnabled(widgetIndex == 0  and (QtGui.qApp.isAdmin() or QtGui.qApp.userHasRight(urSurvChangePerson)))


    @pyqtSignature('')
    def on_mnuDiagnosis_aboutToShow(self):
        widgetIndex = self.tabDispensaireClients.currentIndex()
        self.actGroupChangePersonDNMKB.setEnabled(widgetIndex == 0 and (QtGui.qApp.isAdmin() or QtGui.qApp.userHasRight(urSurvChangePerson)))
        self.actChangePersonDN.setEnabled(widgetIndex == 0)


    @pyqtSignature('')
    def on_mnuMonitoring_aboutToShow(self):
        isEnabled = False
        controlCardBtnEnabled = True
        widgetIndex = self.tabDispensaireClients.currentIndex()
        if widgetIndex == 0:
            self.tblConsistsMonitoring.setFocus(Qt.OtherFocusReason)
            currentIndex = self.tblConsistsMonitoring.currentIndex()
            isEnabled = currentIndex.row() >= 0
        elif widgetIndex == 1:
            self.tblTakenMonitoring.setFocus(Qt.TabFocusReason)
            currentIndex = self.tblTakenMonitoring.currentIndex()
            isEnabled = currentIndex.row() >= 0
        elif widgetIndex == 2:
            self.tblRemoveMonitoring.setFocus(Qt.OtherFocusReason)
            currentIndex = self.tblRemoveMonitoring.currentIndex()
            isEnabled = currentIndex.row() >= 0
        elif widgetIndex == 3:
            self.tblSubjectToSurveillanceMonitoring.setFocus(Qt.OtherFocusReason)
            currentIndex = self.tblSubjectToSurveillanceMonitoring.currentIndex()
            isEnabled = currentIndex.row() >= 0
            controlCardBtnEnabled = False
        self.actOpenEvent.setEnabled(isEnabled)
        self.actSurveillancePlanningMonitoring.setEnabled(controlCardBtnEnabled)


    @pyqtSignature('')
    def on_actAmbCardShow_triggered(self):
        self.ambCardShow()


    def ambCardShow(self):
        isRightAdmin = QtGui.qApp.isAdmin()
        isRegTabReadAmbCard = QtGui.qApp.userHasRight(urRegTabReadAmbCard) or isRightAdmin
        isRegTabWriteAmbCard = QtGui.qApp.userHasRight(urRegTabWriteAmbCard) or isRightAdmin
        if isRegTabReadAmbCard or isRegTabWriteAmbCard:
            # currentTableIndex = self.tabDispensaireClients.currentIndex()
            currentTable = self.getCurrentClientsTable()
            currentRow = currentTable.currentRow()
            clientId = currentTable.currentItemId()
            if clientId:
                try:
                    dialog = CAmbCardDialog(self, clientId)
                    if dialog.exec_():
                        currentTable.setCurrentRow(currentRow)
                        self.on_tabDispensaireClients_currentChanged(self.tabDispensaireClients.currentIndex())
                finally:
                    dialog.deleteLater()
        else:
            QtGui.QMessageBox.warning(self,
                                      u'Внимание!',
                                      u'Нет права на чтение и редактирование Мед.карты!',
                                      QtGui.QMessageBox.Ok,
                                      QtGui.QMessageBox.Ok)


    @pyqtSignature('')
    def on_actSurveillancePlanningClients_triggered(self):
        tableClients = self.getCurrentClientsTable()
        clientId = tableClients.currentItemId()
        self.surveillancePlanningShow(clientId)


    @pyqtSignature('')
    def on_actGroupChangePersonDN_triggered(self):
        dialog = CGroupChangeDispanserPerson(self)
        dialog.setClientCount(self.tblConsistsClients.model().rowCount())
        dialog.setMKBList(self.filter['MKBFrom'], self.filter['MKBTo'], self.filter['MKBFilter'])
        dialog.setCharacterList(self.filter['diseaseCharacterName'])
        dialog.setMKB(False)
        if dialog.exec_():
            personId = dialog.getPersonId()
            clientIdList = self.tblConsistsClients.model().idList()
            diagnosisIdList = dialog.getDiagnosisIdList(clientIdList, self.filter)
            db = QtGui.qApp.db
            tableDiagnosis = db.table('Diagnosis')
            db.updateRecords(tableDiagnosis, 'dispanserPerson_id = {}'.format(forceInt(personId)), tableDiagnosis['id'].inlist(diagnosisIdList))
            tblClients = self.getCurrentClientsTable()
            tblDiagnosis = self.getCurrentDiagnosisTable()
            model = tblClients.model()
            model.loadData(self.filter)
            clientId = tblClients.currentItemId()
            tblDiagnosis.model().loadData(clientId, self.filter)


    @pyqtSignature('')
    def on_actSurveillancePlanningMonitoring_triggered(self):
        tableClients = self.getCurrentClientsTable()
        clientId = tableClients.currentItemId()
        self.surveillancePlanningShow(clientId)


    @pyqtSignature('')
    def on_actChangePersonDN_triggered(self):
        tableDiagnosis = self.getCurrentDiagnosisTable()
        diagnosisId = tableDiagnosis.currentItemId()
        dialog = CChangeDispanserPerson(self)
        dialog.load(diagnosisId)
        if dialog.exec_():
            tableClients = self.getCurrentClientsTable()
            clientId = tableClients.currentItemId()
            model = tableDiagnosis.model()
            model.loadData(clientId, self.filter)


    @pyqtSignature('')
    def on_actGroupChangePersonDNMKB_triggered(self):
        dialog = CGroupChangeDispanserPerson(self)
        dialog.setClientCount(1)
        dialog.setMKBList(self.filter['MKBFrom'], self.filter['MKBTo'], self.filter['MKBFilter'])
        dialog.setCharacterList(self.filter['diseaseCharacterName'])
        diagnosisIdList = self.tblConsistsDiagnosis.model().idList()
        dialog.setMKB(True, diagnosisIdList)
        if dialog.exec_():
            personId = dialog.getPersonId()
            db = QtGui.qApp.db
            tableDiagnosis = db.table('Diagnosis')
            MKBList = dialog.getMKB()
            db.updateRecords(tableDiagnosis, 'dispanserPerson_id = {}'.format(forceInt(personId)), db.joinAnd([tableDiagnosis['id'].inlist(diagnosisIdList), tableDiagnosis['MKB'].inlist(MKBList)]))
            
            tblClients = self.getCurrentClientsTable()
            tblDiagnosis = self.getCurrentDiagnosisTable()
            oldClientId = tblClients.currentItemId()
            modelClients = tblClients.model()
            modelClients.loadData(self.filter)
            
            try:
                row = modelClients.idList().index(oldClientId)
            except ValueError:
                return
            idx = modelClients.index(row, 0, QModelIndex())
            selectionModelClient = tblClients.selectionModel()
            selectionModelClient.select(idx, QtGui.QItemSelectionModel.ClearAndSelect | QtGui.QItemSelectionModel.Rows)
            selectionModelClient.setCurrentIndex(idx, QtGui.QItemSelectionModel.NoUpdate)
                    
            clientId = tblClients.currentItemId()
            tblDiagnosis.model().loadData(clientId, self.filter)


    def surveillancePlanningShow(self, clientId, monitoringIdList=None, eventId=None):
        if clientId:
            db = QtGui.qApp.db
            tableDiagnosis = db.table('Diagnosis')
            tableDiagnostic = db.table('Diagnostic')
            queryTable = tableDiagnosis.leftJoin(tableDiagnostic, tableDiagnosis['id'].eq(tableDiagnostic['diagnosis_id']))
            cond = [tableDiagnosis['deleted'].eq(0),
                    tableDiagnostic['deleted'].eq(0),
                    tableDiagnosis['dispanser_id'].isNotNull(),
                    tableDiagnostic['dispanser_id'].isNotNull(),
                    tableDiagnosis['client_id'].eq(clientId)
                    ]
            if monitoringIdList:
                cond.append(tableDiagnosis['id'].inlist(monitoringIdList))
            if eventId:
                cond.append(tableDiagnostic['event_id'].eq(eventId))
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
            dispanserItems = db.getRecordListGroupBy(queryTable, cols, cond, group = 'MKB', order='maxDiagnosisEndDate DESC, maxDiagnosticEndDate DESC')
            if dispanserItems:
                dialog = CSurveillancePlanningEditDialog(self)
                try:
                    dialog.setEventEditor(self)
                    eventIdList = []
                    for dispanserItem in dispanserItems:
                        eventId = forceRef(dispanserItem.value('event_id'))
                        if eventId and eventId not in eventIdList:
                            eventIdList.append(eventId)
                    if eventIdList:
                        tableEvent = db.table('Event')
                        eventRecord = db.getRecordEx(tableEvent, u'*', [tableEvent['id'].inlist(eventIdList), tableEvent['deleted'].eq(0)], u'Event.setDate DESC')
                        dialog.setEventRecord(eventRecord)
                        eventIdLast = forceRef(eventRecord.value('id')) if eventRecord else None
                        if eventIdLast:
                            cond = [tableDiagnostic['event_id'].eq(eventIdLast),
                                    tableDiagnosis['deleted'].eq(0),
                                    tableDiagnostic['deleted'].eq(0),
                                    tableDiagnosis['dispanser_id'].isNotNull(),
                                    tableDiagnostic['dispanser_id'].isNotNull(),
                                    tableDiagnosis['client_id'].eq(clientId)
                                    ]
                            dispanserEventLastItems = db.getRecordListGroupBy(queryTable, cols, cond, group = 'MKB', order='maxDiagnosisEndDate DESC, maxDiagnosticEndDate DESC')
                            dialog.setDiagnosticEventLastRecords(dispanserEventLastItems)
                        dialog.setDiagnosticRecords(dispanserItems)
                        if dialog.exec_():
                            tableDiagnosis = self.getCurrentDiagnosisTable()
                            tableClients = self.getCurrentClientsTable()
                            oldDiagnosisId = tableDiagnosis.currentItemId()
                            clientId = tableClients.currentItemId()
                            model = tableDiagnosis.model()
                            model.loadData(clientId, self.filter)
                            try:
                                row = model.idList().index(oldDiagnosisId)
                            except ValueError:
                                return
                            idx = model.index(row, 0, QModelIndex())
                            selectionModelDiagnosis = tableDiagnosis.selectionModel()
                            selectionModelDiagnosis.select(idx, QtGui.QItemSelectionModel.ClearAndSelect | QtGui.QItemSelectionModel.Rows)
                            selectionModelDiagnosis.setCurrentIndex(idx, QtGui.QItemSelectionModel.NoUpdate)
                finally:
                    dialog.deleteLater()


    @pyqtSignature('')
    def on_actEditClientInfoBeds_triggered(self):
        self.editClient()


    @pyqtSignature('')
    def on_actPortal_Doctor_triggered(self):
        templateId = None
        result = QtGui.qApp.db.getRecordEx('rbPrintTemplate', 'id',
                                           '`default` LIKE "%s" AND deleted = 0' % ('%/EMK_V3/indexV2.php%'))
        table = self.getCurrentClientsTable()
        context = CInfoContext()
        clientInfo = context.getInstance(CClientInfo, table.currentItemId())
        data = {'client': clientInfo}
        if clientInfo:
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


    def editClient(self):
        isRightAdmin = QtGui.qApp.isAdmin()
        isSurReadClientInfo = QtGui.qApp.userHasRight(urSurReadClientInfo) or isRightAdmin
        isSurEditClientInfo = QtGui.qApp.userHasRight(urSurEditClientInfo) or isRightAdmin
        if isSurReadClientInfo or isSurEditClientInfo:
            table = self.getCurrentClientsTable()
            if table:
                tableIndex = table.currentIndex()
                row = tableIndex.row()
                if row >= 0:
                    currentRow = table.currentRow()
                    clientId = table.currentItemId()
                    if clientId:
                        dialog = CSurveillanceClientEditDialog(self)
                        try:
                            if clientId:
                                dialog.load(clientId)
                            if dialog.exec_():
                                table.setCurrentRow(currentRow)
                                self.on_tabDispensaireClients_currentChanged(self.tabDispensaireClients.currentIndex())
                        finally:
                            dialog.deleteLater()
        else:
            QtGui.QMessageBox.warning(self,
                                      u'Внимание!',
                                      u'Нет права на чтение и редактирование карты пациента!',
                                      QtGui.QMessageBox.Ok,
                                      QtGui.QMessageBox.Ok)


    @pyqtSignature('')
    def on_actOpenEvent_triggered(self):
        QtGui.qApp.callWithWaitCursor(self, self.openEvent)


    def openEvent(self):
        isRightAdmin = QtGui.qApp.isAdmin()
        isSurReadEvent = QtGui.qApp.userHasRight(urSurReadEvent) or isRightAdmin
        isSurEditEvent = QtGui.qApp.userHasRight(urSurEditEvent) or isRightAdmin
        if isSurReadEvent or isSurEditEvent:
            currentTable = self.getCurrentMonitoringTable()
            currentRow = currentTable.currentRow()
            record = currentTable.model().getRecordByRow(currentRow)
            eventId = forceRef(record.value('event_id')) if record else None
            if eventId:
                try:
                    formClass = getEventFormClass(eventId)
                    dialog = formClass(self)
                    dialog.load(eventId)
                    QtGui.qApp.restoreOverrideCursor()
                    dialog.setReadOnly(isSurReadEvent and not isSurEditEvent)
                    if dialog.exec_():
                        currentTable.setCurrentRow(currentRow)
                        self.getFillingMonitoring(self.tabDispensaireClients.currentIndex(), currentTable.currentItemId())
                finally:
                    dialog.deleteLater()
        else:
            QtGui.QMessageBox.warning(self,
                                      u'Внимание!',
                                      u'Нет права на чтение и редактирование события!',
                                      QtGui.QMessageBox.Ok,
                                      QtGui.QMessageBox.Ok)


    def getCurrentClientsTable(self):
        index = self.tabDispensaireClients.currentIndex()
        return [self.tblConsistsClients,
                self.tblTakenClients,
                self.tblRemoveClients,
                self.tblSubjectToSurveillanceClients][index]

    def getCurrentDiagnosisTable(self):
        index = self.tabDispensaireClients.currentIndex()
        return [self.tblConsistsDiagnosis,
                self.tblTakenDiagnosis,
                self.tblRemoveDiagnosis,
                self.tblSubjectToSurveillanceDiagnosis][index]


    def getCurrentMonitoringTable(self):
        index = self.tabDispensaireClients.currentIndex()
        return [self.tblConsistsMonitoring,
                self.tblTakenMonitoring,
                self.tblRemoveMonitoring,
                self.tblSubjectToSurveillanceMonitoring][index]


    def getCurrentInfoBrowserTable(self):
        index = self.tabDispensaireClients.currentIndex()
        return [self.txtConsistsClientInfoBrowser,
                self.txtTakenClientInfoBrowser,
                self.txtRemoveClientInfoBrowser,
                self.txtSubjectToSurveillanceClientInfoBrowser][index]


    @pyqtSignature('int')
    def on_tabDispensaireClients_currentChanged(self, index):
        if index == 0:  # состоят
            QtGui.qApp.callWithWaitCursor(self, self.getFillingClients, self.tblConsistsClients, self.txtConsistsClientInfoBrowser)
            self.periodChanged(u'На дату', False)
        elif index == 1:  # взяты
            QtGui.qApp.callWithWaitCursor(self, self.getFillingClients, self.tblTakenClients, self.txtTakenClientInfoBrowser)
            self.periodChanged(u'Начало периода', True)
        elif index == 2:  # сняты
            QtGui.qApp.callWithWaitCursor(self, self.getFillingClients, self.tblRemoveClients, self.txtRemoveClientInfoBrowser)
            self.periodChanged(u'Начало периода', True)
        elif index == 3:  # подлежат
            QtGui.qApp.callWithWaitCursor(self, self.getFillingClients,
                                                self.tblSubjectToSurveillanceClients,
                                                self.txtSubjectToSurveillanceClientInfoBrowser)
            self.periodChanged(u'Начало периода', True)


    def periodChanged(self, text, isVisible):
        self.lblBegDate.setText(text)
        self.lblEndDate.setVisible(isVisible)
        self.edtFilterEventEndDate.setVisible(isVisible)


    def getFillingClients(self, table, clientInfoBrowser):
        self.setFilter()
        currentRow = table.currentRow()
        model = table.model()
        model.loadData(self.filter)
        if model.rowCount() >= 0:
            if currentRow is None:
                currentRow = 0
            table.setCurrentRow(currentRow)
            clientId = table.currentItemId()
            self.getClientInfoBrowser(clientId, clientInfoBrowser)
        else:
            clientInfoBrowser.setText('')
        tableDiagnosis = self.getCurrentDiagnosisTable()
        tableDiagnosis.model().loadData(table.currentItemId(), self.filter)
        QtGui.qApp.restoreOverrideCursor()
        self.lblCountRecordList.setText(formatRecordsCount(self.getCurrentClientsTable().model().rowCount()))


    def getFillingMonitoring(self, indexTab, clientId):
        table = self.getCurrentMonitoringTable()
        currentRow = table.currentRow()
        model = table.model()
        model.loadData(clientId, self.filter)
        if model.rowCount() >= 0:
            if currentRow is None:
                currentRow = 0
            table.setCurrentRow(currentRow)


    def getClientInfoBrowser(self, clientId, clientInfoBrowser):
        if clientId:
            clientInfoBrowser.setHtml(getClientBanner(clientId))
        else:
            clientInfoBrowser.setText('')


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelConsistsClients_currentRowChanged(self, current, previous):
        clientId = self.tblConsistsClients.currentItemId()
        self.getClientInfoBrowser(clientId, self.txtConsistsClientInfoBrowser)
        self.modelConsistsDiagnosis.loadData(clientId, self.filter)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelTakenClients_currentRowChanged(self, current, previous):
        clientId = self.tblTakenClients.currentItemId()
        self.getClientInfoBrowser(clientId, self.txtTakenClientInfoBrowser)
        self.modelTakenDiagnosis.loadData(clientId, self.filter)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelRemoveClients_currentRowChanged(self, current, previous):
        clientId = self.tblRemoveClients.currentItemId()
        self.getClientInfoBrowser(clientId, self.txtRemoveClientInfoBrowser)
        self.modelRemoveDiagnosis.loadData(clientId, self.filter)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelSubjectToSurveillanceClients_currentRowChanged(self, current, previous):
        clientId = self.tblSubjectToSurveillanceClients.currentItemId()
        self.getClientInfoBrowser(clientId, self.txtSubjectToSurveillanceClientInfoBrowser)
        self.modelSubjectToSurveillanceDiagnosis.loadData(clientId, self.filter)


    @pyqtSignature('')
    def on_modelConsistsDiagnosis_modelReset(self):
        self.modelConsistsMonitoring.setIdList([])
        self.tblConsistsMonitoring.setEnabled(False)
        self.modelConsistsPlanning.clearItems()
        self.tblConsistsPlanning.setEnabled(False)


    @pyqtSignature('')
    def on_modelTakenDiagnosis_modelReset(self):
        self.modelTakenMonitoring.setIdList([])
        self.tblTakenMonitoring.setEnabled(False)
        self.modelTakenPlanning.clearItems()
        self.tblTakenPlanning.setEnabled(False)


    @pyqtSignature('')
    def on_modelRemoveDiagnosis_modelReset(self):
        self.modelTakenMonitoring.setIdList([])
        self.tblTakenMonitoring.setEnabled(False)
        self.modelRemovePlanning.clearItems()
        self.tblRemovePlanning.setEnabled(False)


    @pyqtSignature('')
    def on_modelSubjectToSurveillanceDiagnosis_modelReset(self):
        self.modelSubjectToSurveillanceMonitoring.setIdList([])
        self.tblSubjectToSurveillanceMonitoring.setEnabled(False)
        self.modelSubjectToSurveillancePlanning.clearItems()
        self.tblSubjectToSurveillancePlanning.setEnabled(False)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelConsistsDiagnosis_currentRowChanged(self, current, previous):
        clientId = self.tblConsistsClients.currentItemId()
        diagnosisId = self.tblConsistsDiagnosis.currentItemId()
        if clientId is None or diagnosisId is None:
            self.modelConsistsMonitoring.setIdList([])
            self.tblConsistsMonitoring.setEnabled(False)
            self.modelConsistsPlanning.clearItems()
            self.tblConsistsPlanning.setEnabled(False)
        else:
            self.modelConsistsMonitoring.loadData(diagnosisId, self.filter)
            self.tblConsistsMonitoring.setEnabled(True)
            self.modelConsistsPlanning.loadItems(clientId, diagnosisId)
            self.tblConsistsPlanning.setEnabled(True)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelTakenDiagnosis_currentRowChanged(self, current, previous):
        clientId = self.tblTakenClients.currentItemId()
        diagnosisId = self.tblTakenDiagnosis.currentItemId()
        if clientId is None or diagnosisId is None:
            self.modelTakenMonitoring.setIdList([])
            self.tblTakenMonitoring.setEnabled(False)
            self.modelTakenPlanning.clearItems()
            self.tblTakenPlanning.setEnabled(False)
        else:
            self.modelTakenMonitoring.loadData(diagnosisId, self.filter)
            self.tblTakenMonitoring.setEnabled(True)
            self.modelTakenPlanning.loadItems(clientId, diagnosisId)
            self.tblTakenPlanning.setEnabled(True)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelRemoveDiagnosis_currentRowChanged(self, current, previous):
        clientId = self.tblRemoveClients.currentItemId()
        diagnosisId = self.tblRemoveDiagnosis.currentItemId()
        if clientId is None or diagnosisId is None:
            self.modelRemoveMonitoring.setIdList([])
            self.tblRemoveMonitoring.setEnabled(False)
            self.modelRemovePlanning.clearItems()
            self.tblRemovePlanning.setEnabled(False)
        else:
            self.modelRemoveMonitoring.loadData(diagnosisId, self.filter)
            self.tblRemoveMonitoring.setEnabled(True)
            self.modelRemovePlanning.loadItems(clientId, diagnosisId)
            self.tblRemovePlanning.setEnabled(True)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelSubjectToSurveillanceDiagnosis_currentRowChanged(self, current, previous):
        clientId = self.tblSubjectToSurveillanceClients.currentItemId()
        diagnosisId = self.tblSubjectToSurveillanceDiagnosis.currentItemId()
        if clientId is None or diagnosisId is None:
            self.modelSubjectToSurveillanceMonitoring.setIdList([])
            self.tblSubjectToSurveillanceMonitoring.setEnabled(False)
            self.modelSubjectToSurveillancePlanning.clearItems()
            self.tblSubjectToSurveillancePlanning.setEnabled(False)
        else:
            self.modelSubjectToSurveillanceMonitoring.loadData(diagnosisId, self.filter)
            self.tblSubjectToSurveillanceMonitoring.setEnabled(True)
            self.modelSubjectToSurveillancePlanning.loadItems(clientId, diagnosisId)
            self.tblSubjectToSurveillancePlanning.setEnabled(True)


class CSurveillanceClientsModel(CTableModel):
    class CLocClientNameColumn(CTextCol):
        def __init__(self, title, fields, defaultWidth, alignment='l'):
            CTextCol.__init__(self, title, fields, defaultWidth, alignment)

        def format(self, values):
            val = formatName(unicode(values[0].toString()), unicode(values[1].toString()), unicode(values[2].toString()))
            return QVariant(val)

    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self.addColumn(CTextCol(u'Код пациента',            ['id'],                                                            15))
        self.addColumn(CSurveillanceClientsModel.CLocClientNameColumn(u'ФИО пациента ', ['lastName', 'firstName', 'patrName'], 30, 'l'),)
        self.addColumn(CEnumCol(u'Пол',                     ['sex'], [u'-', u'М', u'Ж'],                                       4, 'c'))
        self.addColumn(CDateCol(u'Дата рожд.',              ['birthDate'],                                                     12, highlightRedDate=False))
        self.addColumn(CSNILSCol(u'СНИЛС',                  ['SNILS'],                                                         4))
        self.setTable('Client')
        self.prophylaxisPlanningType = getProphylaxisPlanningType()


    def getClientIdList(self, records, filter, observedType):
        clientIdList = []
        specialityType = filter.get('specialityType', None)
        specialityList = filter.get('specialityId', None)
        clientSpecIdList = {}
        if specialityList and specialityType:
            specialityListId = []
            specialityLine = specialityList.split(u',')
            for speciality in specialityLine:
                specialityId = int(trim(speciality))
                if specialityId and specialityId not in specialityListId:
                    specialityListId.append(specialityId)
            for record in records:
                clientId = forceRef(record.value('id'))
                specialityId  = forceRef(record.value('speciality_id'))
                if specialityId and specialityId in specialityListId:
                    observed = forceInt(record.value('observed'))
                    if observedType is None or observed == observedType:
                        clientSpecIdLine = clientSpecIdList.get(clientId, [])
                        clientSpecIdLine.append(specialityId)
                        clientSpecIdList[clientId] = clientSpecIdLine
            for clientId, clientSpecIdLine in clientSpecIdList.items():
                if not set(clientSpecIdLine) ^ set(specialityListId):
                    if clientId and clientId not in clientIdList:
                        clientIdList.append(clientId)
        else:
            for record in records:
                observed = forceInt(record.value('observed'))
                if observedType is None or observed == observedType:
                    clientIdList.append(forceRef(record.value('id')))
        return clientIdList


    def getColsGroupBySpeciality(self, cols, groupBy):
        db = QtGui.qApp.db
        tablePerson = db.table('Person')
        cols.append(tablePerson['speciality_id'])
        groupBy += u', Person.speciality_id '
        return cols, groupBy


class CConsistsClientsModel(CSurveillanceClientsModel):
    def __init__(self, parent):
        CSurveillanceClientsModel.__init__(self, parent)

    def loadData(self, filter):
        self.filter = filter
        date = self.filter.get('begDate', QDate.currentDate())
        specialityType = self.filter.get('specialityType', None)
        specialityList = self.filter.get('specialityId', None)
        if not date:
            date = QDate.currentDate()
        db = QtGui.qApp.db
        tableClient = db.table('Client')
        tableDiagnosis = db.table('Diagnosis')
        tableDiagnostic = db.table('Diagnostic')
        tableRBDispanser = db.table('rbDispanser')
        cond = [tableClient['deleted'].eq(0),
                tableDiagnosis['deleted'].eq(0),
                tableDiagnostic['deleted'].eq(0),
                tableDiagnostic['endDate'].le(date),
                tableRBDispanser['observed'].eq(1)
                ]
        queryTable = tableClient.innerJoin(tableDiagnosis, tableDiagnosis['client_id'].eq(tableClient['id']))
        queryTable = queryTable.innerJoin(tableDiagnostic, tableDiagnostic['diagnosis_id'].eq(tableDiagnosis['id']))
        queryTable = queryTable.innerJoin(tableRBDispanser, tableRBDispanser['id'].eq(tableDiagnosis['dispanser_id']))
        cond, queryTable = diagnosticCondAdd(db, queryTable, filter, cond, tableDiagnosis, tableDiagnostic)
        cond, queryTable = clientsCondAdd(db, queryTable, filter, cond, tableClient)
        cond.append(u'''NOT EXISTS(SELECT DC.id
                                   FROM Diagnostic AS DC
                                   INNER JOIN Diagnosis AS DS ON DS.id = DC.diagnosis_id
                                   INNER JOIN rbDispanser AS rbDP ON rbDP.id = DC.dispanser_id
                                   WHERE DS.client_id = Client.id
                                   AND DC.endDate <= %s AND rbDP.name LIKE '%s' AND DC.deleted = 0 AND DS.deleted = 0
                                   AND (DC.diagnosis_id = Diagnosis.id OR DS.MKB = Diagnosis.MKB))
                        OR EXISTS(SELECT DC.id
                                   FROM Diagnostic AS DC
                                   INNER JOIN Diagnosis AS DS ON DS.id = DC.diagnosis_id
                                   INNER JOIN rbDispanser AS rbDP ON rbDP.id = DC.dispanser_id
                                   WHERE DS.client_id = Client.id
                                   AND DC.endDate <= %s AND rbDP.name LIKE '%s' AND DC.deleted = 0 AND DS.deleted = 0
                                   AND (DC.diagnosis_id = Diagnosis.id OR DS.MKB = Diagnosis.MKB))''' % (db.formatDate(date), u'%снят%', db.formatDate(date), u'%взят повторно%'))
        personDN = self.filter.get('personDN')
        if personDN:
            cond.append(tableDiagnosis['dispanserPerson_id'].eq(personDN))
        planningType = self.filter.get('planningType')
        if planningType is not None:
            dataRange = self.filter.get('dateRange')
            begDate, endDate = dataRange
            begDateCond = (' AND pp.endDate >= %s ' % db.formatDate(begDate)) if not begDate.isNull() else ''
            endDateCond = (' AND pp.begDate <= %s ' % db.formatDate(endDate)) if not endDate.isNull() else ''
            cond.append(u'''%sEXISTS(SELECT pp.id
                                               FROM ProphylaxisPlanning pp
                                               WHERE pp.client_id = Client.id
                                               AND pp.prophylaxisPlanningType_id = %s
                                               AND Diagnosis.MKB = pp.MKB AND pp.deleted = 0
                                               %s%s
                                               )''' % ({0: '', 1: 'NOT '}[planningType], self.prophylaxisPlanningType, begDateCond, endDateCond))
        cols = [u'DISTINCT MAX(Diagnostic.endDate)', u'Client.id', u'rbDispanser.observed', u'Client.lastName', u'Client.firstName', u'Client.patrName']
        group = 'Client.id'
        if specialityList and specialityType:
            cols, group = self.getColsGroupBySpeciality(cols, group)
        records = db.getRecordListGroupBy(queryTable,
                                          cols,
                                          where=cond, group=group,
                                          order='Client.lastName ASC, Client.firstName ASC, Client.patrName ASC, Diagnostic.endDate DESC')
        clientIdList = self.getClientIdList(records, self.filter, observedType=1)
        self.setIdList(clientIdList)


class CTakenClientsModel(CSurveillanceClientsModel):
    def __init__(self, parent):
        CSurveillanceClientsModel.__init__(self, parent)


    def loadData(self, filter):
        self.filter = filter
        begDate = self.filter.get('begDate', QDate.currentDate())
        endDate = self.filter.get('endDate', QDate())
        specialityType = self.filter.get('specialityType', None)
        specialityList = self.filter.get('specialityId', None)
        if not begDate:
            begDate = QDate.currentDate()
        db = QtGui.qApp.db
        tableClient = db.table('Client')
        tableDiagnosis = db.table('Diagnosis')
        tableDiagnostic = db.table('Diagnostic')
        tableRBDispanser = db.table('rbDispanser')
        cond = [tableClient['deleted'].eq(0),
                tableDiagnosis['deleted'].eq(0),
                tableDiagnostic['deleted'].eq(0),
                tableDiagnostic['dispanser_id'].isNotNull(),
                tableDiagnostic['endDate'].ge(begDate),
                tableRBDispanser['name'].like(u'%взят%')
                ]
        if endDate:
            cond.append(tableDiagnostic['endDate'].le(endDate))
        queryTable = tableClient.innerJoin(tableDiagnosis, tableDiagnosis['client_id'].eq(tableClient['id']))
        queryTable = queryTable.innerJoin(tableDiagnostic, tableDiagnostic['diagnosis_id'].eq(tableDiagnosis['id']))
        queryTable = queryTable.innerJoin(tableRBDispanser, tableRBDispanser['id'].eq(tableDiagnostic['dispanser_id']))
        cond, queryTable = diagnosticCondAdd(db, queryTable, filter, cond, tableDiagnosis, tableDiagnostic)
        cond, queryTable = clientsCondAdd(db, queryTable, filter, cond, tableClient)
        personDN = self.filter.get('personDN')
        if personDN:
            cond.append(tableDiagnosis['dispanserPerson_id'].eq(personDN))
        planningType = self.filter.get('planningType')
        if planningType is not None:
            dataRange = self.filter.get('dateRange')
            begDate, endDate = dataRange
            begDateCond = (' AND pp.endDate >= %s ' % db.formatDate(begDate)) if not begDate.isNull() else ''
            endDateCond = (' AND pp.begDate <= %s ' % db.formatDate(endDate)) if not endDate.isNull() else ''
            cond.append(u'''%sEXISTS(SELECT pp.id
                                                       FROM ProphylaxisPlanning pp
                                                       WHERE pp.client_id = Client.id
                                                       AND pp.prophylaxisPlanningType_id = %s
                                                       AND Diagnosis.MKB = pp.MKB AND pp.deleted = 0
                                                       %s%s
                                                       )''' % (
            {0: '', 1: 'NOT '}[planningType], self.prophylaxisPlanningType, begDateCond, endDateCond))
        cols = [u'DISTINCT MAX(Diagnostic.endDate)', u'Client.id', u'rbDispanser.observed', u'Client.lastName', u'Client.firstName', u'Client.patrName']
        group = 'Client.id'
        if specialityList and specialityType:
            cols, group = self.getColsGroupBySpeciality(cols, group)
        records = db.getRecordListGroupBy(queryTable,
                                          cols,
                                          where=cond, group=group,
                                          order='Client.lastName ASC, Client.firstName ASC, Client.patrName ASC, Diagnostic.endDate DESC')
        clientIdList = self.getClientIdList(records, self.filter, observedType=1)
        self.setIdList(clientIdList)


class CRemoveClientsModel(CSurveillanceClientsModel):
    def __init__(self, parent):
        CSurveillanceClientsModel.__init__(self, parent)


    def loadData(self, filter):
        self.filter = filter
        clientIdList = []
        begDate = self.filter.get('begDate', QDate.currentDate())
        endDate = self.filter.get('endDate', QDate())
        specialityType = self.filter.get('specialityType', None)
        specialityList = self.filter.get('specialityId', None)
        if not begDate:
            begDate = QDate.currentDate()
        db = QtGui.qApp.db
        tableClient = db.table('Client')
        tableDiagnosis = db.table('Diagnosis')
        tableDiagnostic = db.table('Diagnostic')
        tableRBDispanser = db.table('rbDispanser')
        cond = [tableClient['deleted'].eq(0),
                tableDiagnosis['deleted'].eq(0),
                tableDiagnostic['deleted'].eq(0),
                tableDiagnostic['dispanser_id'].isNotNull(),
                tableDiagnostic['endDate'].ge(begDate),
                tableRBDispanser['observed'].eq(0),
                tableRBDispanser['name'].like(u'%снят%'),
                ]
        if endDate:
            cond.append(tableDiagnostic['endDate'].le(endDate))
        queryTable = tableClient.innerJoin(tableDiagnosis, tableDiagnosis['client_id'].eq(tableClient['id']))
        queryTable = queryTable.innerJoin(tableDiagnostic, tableDiagnostic['diagnosis_id'].eq(tableDiagnosis['id']))
        queryTable = queryTable.innerJoin(tableRBDispanser, tableRBDispanser['id'].eq(tableDiagnostic['dispanser_id']))
        cond, queryTable = diagnosticCondAdd(db, queryTable, filter, cond, tableDiagnosis, tableDiagnostic)
        cond, queryTable = clientsCondAdd(db, queryTable, filter, cond, tableClient)
        personDN = self.filter.get('personDN')
        if personDN:
            cond.append(tableDiagnosis['dispanserPerson_id'].eq(personDN))
        planningType = self.filter.get('planningType')
        if planningType is not None:
            dataRange = self.filter.get('dateRange')
            begDate, endDate = dataRange
            begDateCond = (' AND pp.endDate >= %s ' % db.formatDate(begDate)) if not begDate.isNull() else ''
            endDateCond = (' AND pp.begDate <= %s ' % db.formatDate(endDate)) if not endDate.isNull() else ''
            cond.append(u'''%sEXISTS(SELECT pp.id
                                                       FROM ProphylaxisPlanning pp
                                                       WHERE pp.client_id = Client.id
                                                       AND pp.prophylaxisPlanningType_id = %s
                                                       AND Diagnosis.MKB = pp.MKB AND pp.deleted = 0
                                                       %s%s
                                                       )''' % (
            {0: '', 1: 'NOT '}[planningType], self.prophylaxisPlanningType, begDateCond, endDateCond))
        cols = [u'DISTINCT MAX(Diagnostic.endDate)', u'Client.id', u'rbDispanser.observed', u'Client.lastName', u'Client.firstName', u'Client.patrName']
        group='Client.id'
        if specialityList and specialityType:
            cols, group = self.getColsGroupBySpeciality(cols, group)
        records = db.getRecordListGroupBy(queryTable,
                                          cols,
                                          where=cond, group=group,
                                          order='Client.lastName ASC, Client.firstName ASC, Client.patrName ASC, Diagnostic.endDate DESC')
        clientIdList = self.getClientIdList(records, self.filter, observedType=0)
        self.setIdList(clientIdList)


class CSubjectToSurveillanceClientsModel(CSurveillanceClientsModel):
    def __init__(self, parent):
        CSurveillanceClientsModel.__init__(self, parent)


    def loadData(self, filter):
        self.filter = filter
        clientIdList = []
        begDate = self.filter.get('begDate', QDate.currentDate())
        endDate = self.filter.get('endDate', QDate())
        specialityType = self.filter.get('specialityType', None)
        specialityList = self.filter.get('specialityId', None)
        if not begDate:
            begDate = QDate.currentDate()
        db = QtGui.qApp.db
        tableClient = db.table('Client')
        tableDiagnosis = db.table('Diagnosis')
        tableDS = db.table('Diagnosis').alias('DS')
        tableDiagnostic = db.table('Diagnostic')
        tableEvent = db.table('Event')
        tableEventType = db.table('EventType')
        tableRBDispanser = db.table('rbDispanser')
        tableMKB = db.table('MKB')
        cond = [
            tableClient['deleted'].eq(0),
            tableDiagnosis['deleted'].eq(0),
            tableMKB['requiresFillingDispanser'].inlist([1,2]), # 1-иногда, 2-всегда
            db.joinOr([tableDiagnosis['dispanser_id'].isNull(), tableDiagnosis['dispanser_id'].inlist([3,4,5])]), #tt2432
            tableEventType['code'].notlike(u'%%rmDisp%'),
            tableEventType['code'].notlike(u'%%ЭЛМК%'),
            tableEventType['form'].ne(u'088'),
            tableDS['id'].isNull()
        ]
        queryTable = tableClient.innerJoin(tableDiagnosis, tableDiagnosis['client_id'].eq(tableClient['id']))
        queryTable = queryTable.innerJoin(tableDiagnostic, db.joinAnd([tableDiagnostic['diagnosis_id'].eq(tableDiagnosis['id']), 
                                                                               tableDiagnostic['deleted'].eq(0),
                                                                               tableDiagnostic['endDate'].ge(begDate),
                                                                               tableDiagnostic['endDate'].le(endDate) if endDate else 'TRUE',
                                                                               u'''Diagnostic.endDate = (SELECT MAX(d2.endDate)
                                                                                    FROM Diagnostic d2
                                                                                    WHERE
                                                                                        d2.diagnosis_id = Diagnosis.id
                                                                                        AND d2.deleted = 0
                                                                                        AND d2.endDate >= {}
                                                                                        AND {})'''.format(db.formatDate(begDate), 
                                                                                                          u'd2.endDate <= {}'.format(db.formatDate(endDate)) if endDate else 'TRUE')]))
            
        queryTable = queryTable.leftJoin(tableEvent, tableEvent['id'].eq(tableDiagnostic['event_id']))
        queryTable = queryTable.leftJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
        queryTable = queryTable.innerJoin(tableMKB, u"MKB.DiagID = Diagnosis.MKB")
        queryTable = queryTable.leftJoin(tableRBDispanser, tableRBDispanser['id'].eq(tableDiagnostic['dispanser_id']))
        queryTable = queryTable.leftJoin(tableDS, db.joinAnd([tableDS['client_id'].eq(tableClient['id']), u'LEFT(DS.MKB, 3) = LEFT(Diagnosis.MKB, 3)', tableDS['dispanser_id'].inlist([1,2,6])]))
        cond, queryTable = diagnosticCondAdd(db, queryTable, filter, cond, tableDiagnosis, tableDiagnostic)
        cond, queryTable = clientsCondAdd(db, queryTable, filter, cond, tableClient)
        personDN = self.filter.get('personDN')
        if personDN:
            cond.append(tableDiagnosis['dispanserPerson_id'].eq(personDN))
        planningType = self.filter.get('planningType')
        if planningType is not None:
            dataRange = self.filter.get('dateRange')
            begDate, endDate = dataRange
            begDateCond = (' AND pp.endDate >= %s ' % db.formatDate(begDate)) if not begDate.isNull() else ''
            endDateCond = (' AND pp.begDate <= %s ' % db.formatDate(endDate)) if not endDate.isNull() else ''
            cond.append(u'''%sEXISTS(SELECT pp.id
                                                       FROM ProphylaxisPlanning pp
                                                       WHERE pp.client_id = Client.id
                                                       AND pp.prophylaxisPlanningType_id = %s
                                                       AND Diagnosis.MKB = pp.MKB AND pp.deleted = 0
                                                       %s%s
                                                       )''' % (
            {0: '', 1: 'NOT '}[planningType], self.prophylaxisPlanningType, begDateCond, endDateCond))
        cols = [u'DISTINCT MAX(Diagnostic.endDate)',
                u'Diagnostic.dispanser_id as isNotSubject',
                u'Client.id', 
                u'rbDispanser.observed',
                u'Client.lastName', 
                u'Client.firstName', 
                u'Client.patrName']
        group = 'Client.id'
        if specialityList and specialityType:
            cols, group = self.getColsGroupBySpeciality(cols, group)
        records = db.getRecordListGroupBy(queryTable,
                                          cols,
                                          where=cond, group=group,
                                          order='Client.lastName ASC, Client.firstName ASC, Client.patrName ASC, Diagnostic.endDate DESC')
        subjectRecords = []
        for record in records:
            if not forceRef(record.value('isNotSubject')) and forceRef(record.value('id')):
                subjectRecords.append(record)
        clientIdList = self.getClientIdList(subjectRecords, self.filter, observedType=None)
        self.setIdList(clientIdList)


class CSurveillanceMonitoringModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self.addColumn(CDesignationCol(u'МКБ',                             ['diagnosis_id'], ('Diagnosis', 'MKB'),      6))
        self.addColumn(CDateCol(       u'Дата записи',                     ['endDate'],                                 12))
        self.addColumn(CRefBookCol(    u'Статус ДН',                       ['dispanser_id'], 'rbDispanser',             15))
        self.addColumn(CRefBookCol(    u'Врач',                            ['person_id'],    'vrbPersonWithSpecialityAndOrgStr', 6))
        self.addColumn(CTextCol(       u'Описание диагноза',               ['freeInput'],                               6))
        self.loadField('event_id')
        self.loadField('diagnosis_id')
        self.setTable('Diagnostic')


class CSurveillanceDiagnosisModel(CTableModel):

    class CLocNextDateColumn(CTextCol):
        def __init__(self, title, fields, defaultWidth, alignment='l'):
            CTextCol.__init__(self, title, fields, defaultWidth, alignment)
            self.prophylaxisPlanningType = getProphylaxisPlanningType()

        def format(self, values):
            db = QtGui.qApp.db
            table = db.table('ProphylaxisPlanning')
            record = db.getRecordEx(table, 'begDate, endDate', [table['client_id'].eq(values[0]),
                                                                table['prophylaxisPlanningType_id'].eq(self.prophylaxisPlanningType),
                                                                table['MKB'].eq(values[1]),
                                                                table['deleted'].eq(0),
                                                                table['begDate'].ge(QDate.currentDate())],
                                    'begDate')
            date = ''
            if record:
                begDate = forceDate(record.value(0))
                endDate = forceDate(record.value(1))
                if not begDate.isNull():
                    date = formatDate(begDate)
                    if not endDate.isNull():
                        date += ' - ' + formatDate(endDate)

            return QVariant(date)

    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self.addColumn(CTextCol(u'МКБ', ['MKB'], 6))
        self.addColumn(CDateCol(u'Дата взятия на ДН', ['dispanserBegDate'], 12))
        self.addColumn(CRefBookCol(u'Статус ДН', ['dispanser_id'], 'rbDispanser', 15))
        self.addColumn(CRefBookCol(u'Врач ДН', ['dispanserPerson_id'], 'vrbPersonWithSpecialityAndOrgStr', 6))
        self.addColumn(CSurveillanceDiagnosisModel.CLocNextDateColumn(u'Следующая явка', ['client_id', 'MKB'], 30, 'l'))
        self.loadField('client_id')
        self.loadField('id')
        self.setTable('Diagnosis')


class CConsistsMonitoringModel(CSurveillanceMonitoringModel):
    def __init__(self, parent):
        CSurveillanceMonitoringModel.__init__(self, parent)


    def getDiagnosticIdList(self, masterId, filter):
        diagnosticIdList = []
        if masterId:
            self.filter = filter
            date = self.filter.get('begDate', QDate.currentDate())
            if not date:
                date = QDate.currentDate()
            db = QtGui.qApp.db
            tableDiagnosis = db.table('Diagnosis')
            tableDiagnostic = db.table('Diagnostic')
            tableRBDispanser = db.table('rbDispanser')
            cond = [tableDiagnostic['diagnosis_id'].eq(masterId),
                    tableDiagnosis['deleted'].eq(0),
                    tableDiagnostic['deleted'].eq(0),
                    tableDiagnostic['dispanser_id'].isNotNull(),
                    db.joinOr([db.joinAnd([tableDiagnostic['endDate'].isNotNull(), tableDiagnostic['endDate'].le(date)]),
                               db.joinAnd([tableDiagnostic['endDate'].isNull(), tableDiagnostic['setDate'].le(date)])]),
                    ]
            queryTable = tableDiagnosis.innerJoin(tableDiagnostic, tableDiagnostic['diagnosis_id'].eq(tableDiagnosis['id']))
            queryTable = queryTable.innerJoin(tableRBDispanser, tableRBDispanser['id'].eq(tableDiagnostic['dispanser_id']))
            cond, queryTable = diagnosticCondAdd(db, queryTable, filter, cond, tableDiagnosis, tableDiagnostic)
            cond.append(u'''NOT EXISTS(SELECT DC.id
                                   FROM Diagnostic AS DC
                                   INNER JOIN Diagnosis AS DS ON DS.id = DC.diagnosis_id
                                   INNER JOIN rbDispanser AS rbDP ON rbDP.id = DC.dispanser_id
                                   WHERE DC.diagnosis_id = Diagnosis.id AND DC.endDate <= %s AND DC.deleted = 0 AND rbDP.name LIKE '%s')
                            OR EXISTS(SELECT DC.id
                                   FROM Diagnostic AS DC
                                   INNER JOIN Diagnosis AS DS ON DS.id = DC.diagnosis_id
                                   INNER JOIN rbDispanser AS rbDP ON rbDP.id = DC.dispanser_id
                                   WHERE DC.diagnosis_id = Diagnosis.id AND DC.endDate <= %s AND DC.deleted = 0 AND rbDP.name LIKE '%s')'''%(db.formatDate(date), u'%снят%', db.formatDate(date), u'%взят повторно%'))
            diagnosticIdList = db.getDistinctIdList(queryTable, [u'Diagnostic.id'], where=cond, order='Diagnostic.endDate DESC')
        return diagnosticIdList


    def loadData(self, masterId, filter):
        self.setIdList(self.getDiagnosticIdList(masterId, filter))


class CConsistsDiagnosisModel(CSurveillanceDiagnosisModel):
    def __init__(self, parent):
        CSurveillanceDiagnosisModel.__init__(self, parent)


    def getDiagnosisIdList(self, masterId, filter):
        diagnosisIdList = []
        if masterId:
            self.filter = filter
            date = self.filter.get('begDate', QDate.currentDate())
            if not date:
                date = QDate.currentDate()
            db = QtGui.qApp.db
            tableDiagnosis = db.table('Diagnosis')
            tableDiagnostic = db.table('Diagnostic')
            tableRBDispanser = db.table('rbDispanser')
            cond = [tableDiagnosis['client_id'].eq(masterId),
                    tableDiagnosis['deleted'].eq(0),
                    tableDiagnostic['deleted'].eq(0),
                    db.joinOr([db.joinAnd([tableDiagnostic['endDate'].isNotNull(), tableDiagnostic['endDate'].le(date)]),
                               db.joinAnd([tableDiagnostic['endDate'].isNull(), tableDiagnostic['setDate'].le(date)])]),
                    tableRBDispanser['observed'].eq(1)
                    ]
            queryTable = tableDiagnosis.innerJoin(tableDiagnostic, tableDiagnostic['diagnosis_id'].eq(tableDiagnosis['id']))
            queryTable = queryTable.innerJoin(tableRBDispanser, tableRBDispanser['id'].eq(tableDiagnostic['dispanser_id']))
            cond, queryTable = diagnosticCondAdd(db, queryTable, filter, cond, tableDiagnosis, tableDiagnostic)
            cond.append(u'''NOT EXISTS(SELECT DC.id
                                   FROM Diagnostic AS DC
                                   INNER JOIN Diagnosis AS DS ON DS.id = DC.diagnosis_id
                                   INNER JOIN rbDispanser AS rbDP ON rbDP.id = DC.dispanser_id
                                   WHERE DC.diagnosis_id = Diagnosis.id AND DC.endDate <= %s AND DC.deleted = 0 AND rbDP.name LIKE '%s')
                            OR EXISTS(SELECT DC.id
                                   FROM Diagnostic AS DC
                                   INNER JOIN Diagnosis AS DS ON DS.id = DC.diagnosis_id
                                   INNER JOIN rbDispanser AS rbDP ON rbDP.id = DC.dispanser_id
                                   WHERE DC.diagnosis_id = Diagnosis.id AND DC.endDate <= %s AND DC.deleted = 0 AND rbDP.name LIKE '%s')''' % (db.formatDate(date), u'%снят%', db.formatDate(date), u'%взят повторно%'))
            diagnosisIdList = db.getDistinctIdList(queryTable, [u'Diagnosis.id'], where=cond, order='Diagnostic.endDate DESC')
        return diagnosisIdList

        
    def getPrintData(self, masterId, filter):
        printData = ['', '', '', '', '', '']
        if masterId:
            db = QtGui.qApp.db
            query = db.query('SELECT getClientContacts(%d)' % masterId)
            if query.first():
                printData[0] = (forceString(query.value(0)))

            query = db.query('SELECT getClientRegAddress(%d)' % masterId)
            if query.first():
                printData[1] = (forceString(query.value(0)))
                
            query = db.query('SELECT O.code'
                             ' FROM OrgStructure O'
                             ' JOIN ClientAttach CA ON CA.orgStructure_id = O.id'
                             ' WHERE CA.client_id = %d AND CA.deleted = 0 AND O.deleted = 0'
                             ' ORDER BY CA.id DESC LIMIT 1' % masterId)
            if query.first():
                printData[2] = (forceString(query.value(0)))
                
            cols = ['Diagnosis.MKB', 'vrbPerson.name', 'Diagnosis.endDate']
            self.filter = filter
            date = self.filter.get('begDate', QDate.currentDate())
            if not date:
                date = QDate.currentDate()
            db = QtGui.qApp.db
            tableDiagnosis = db.table('Diagnosis')
            tableDiagnostic = db.table('Diagnostic')
            tableRBDispanser = db.table('rbDispanser')
            tablePerson = db.table('vrbPerson')
            cond = [tableDiagnosis['client_id'].eq(masterId),
                    tableDiagnosis['deleted'].eq(0),
                    tableDiagnostic['deleted'].eq(0),
                    tableDiagnostic['dispanser_id'].isNotNull(),
                    db.joinOr([db.joinAnd([tableDiagnostic['endDate'].isNotNull(), tableDiagnostic['endDate'].le(date)]),
                               db.joinAnd([tableDiagnostic['endDate'].isNull(), tableDiagnostic['setDate'].le(date)])]),
                    tableRBDispanser['observed'].eq(1)
                    ]
            queryTable = tableDiagnosis.innerJoin(tableDiagnostic, tableDiagnostic['diagnosis_id'].eq(tableDiagnosis['id']))
            queryTable = queryTable.innerJoin(tableRBDispanser, tableRBDispanser['id'].eq(tableDiagnostic['dispanser_id']))
            queryTable = queryTable.leftJoin(tablePerson, tablePerson['id'].eq(tableDiagnosis['dispanserPerson_id']))
            cond, queryTable = diagnosticCondAdd(db, queryTable, filter, cond, tableDiagnosis, tableDiagnostic)
            cond.append(u'''NOT EXISTS(SELECT DC.id
                                   FROM Diagnostic AS DC
                                   INNER JOIN rbDispanser AS rbDP ON rbDP.id = DC.dispanser_id
                                   WHERE DC.diagnosis_id = Diagnosis.id AND DC.endDate <= %s AND DC.deleted = 0 AND rbDP.name LIKE '%s')'''%(db.formatDate(date), u'%снят%'))
            query = db.getRecordListGroupBy(queryTable, cols, where=cond, group='Diagnosis.id', order='Diagnostic.endDate DESC')
            for record in query:
                printData[3] += forceString(record.value(0)) + '\n'
                printData[4] += forceString(record.value(1)) + '\n'
                printData[5] += forceString(record.value(2)) + '\n'
        return printData


    def loadData(self, masterId, filter):
        self.setIdList(self.getDiagnosisIdList(masterId, filter))

class CTakenDiagnosisModel(CSurveillanceDiagnosisModel):
    def __init__(self, parent):
        CSurveillanceDiagnosisModel.__init__(self, parent)


    def getDiagnosisIdList(self, masterId, filter):
        diagnosisIdList = []
        if masterId:
            self.filter = filter
            begDate = self.filter.get('begDate', QDate.currentDate())
            endDate = self.filter.get('endDate', QDate())
            if not begDate:
                begDate = QDate.currentDate()
            db = QtGui.qApp.db
            tableDiagnosis = db.table('Diagnosis')
            tableDiagnostic = db.table('Diagnostic')
            tableRBDispanser = db.table('rbDispanser')
            cond = [tableDiagnosis['client_id'].eq(masterId),
                    tableDiagnosis['deleted'].eq(0),
                    tableDiagnostic['deleted'].eq(0),
                    tableDiagnostic['dispanser_id'].isNotNull(),
                    tableDiagnostic['endDate'].ge(begDate),
                    tableRBDispanser['name'].like(u'%взят%'),
                    ]
            if endDate:
                cond.append(tableDiagnostic['endDate'].le(endDate))
            queryTable = tableDiagnosis.innerJoin(tableDiagnostic, tableDiagnostic['diagnosis_id'].eq(tableDiagnosis['id']))
            queryTable = queryTable.innerJoin(tableRBDispanser, tableRBDispanser['id'].eq(tableDiagnostic['dispanser_id']))
            cond, queryTable = diagnosticCondAdd(db, queryTable, filter, cond, tableDiagnosis, tableDiagnostic)
            diagnosisIdList = db.getDistinctIdList(queryTable, [u'Diagnosis.id'], where=cond, order='Diagnostic.endDate DESC')
        return diagnosisIdList

    
    def getPrintData(self, masterId, filter):
        printData = ['', '', '', '', '', '']
        if masterId:
            db = QtGui.qApp.db
            query = db.query('SELECT getClientContacts(%d)' % masterId)
            if query.first():
                printData[0] = (forceString(query.value(0)))

            query = db.query('SELECT getClientRegAddress(%d)' % masterId)
            if query.first():
                printData[1] = (forceString(query.value(0)))
                
            query = db.query('SELECT O.code'
                             ' FROM OrgStructure O'
                             ' JOIN ClientAttach CA ON CA.orgStructure_id = O.id'
                             ' WHERE CA.client_id = %d AND CA.deleted = 0 AND O.deleted = 0'
                             ' ORDER BY CA.id DESC LIMIT 1' % masterId)
            if query.first():
                printData[2] = (forceString(query.value(0)))
                
            cols = ['Diagnosis.MKB', 'vrbPerson.name', 'Diagnosis.endDate']
            self.filter = filter
            begDate = self.filter.get('begDate', QDate.currentDate())
            endDate = self.filter.get('endDate', QDate())
            if not begDate:
                begDate = QDate.currentDate()
            db = QtGui.qApp.db
            tableDiagnosis = db.table('Diagnosis')
            tableDiagnostic = db.table('Diagnostic')
            tableRBDispanser = db.table('rbDispanser')
            tablePerson = db.table('vrbPerson')
            cond = [tableDiagnosis['client_id'].eq(masterId),
                    tableDiagnosis['deleted'].eq(0),
                    tableDiagnostic['deleted'].eq(0),
                    tableDiagnostic['dispanser_id'].isNotNull(),
                    tableDiagnostic['endDate'].ge(begDate),
                    tableRBDispanser['name'].like(u'%взят%'),
                    ]
            if endDate:
                cond.append(tableDiagnostic['endDate'].le(endDate))
            queryTable = tableDiagnosis.innerJoin(tableDiagnostic, tableDiagnostic['diagnosis_id'].eq(tableDiagnosis['id']))
            queryTable = queryTable.innerJoin(tableRBDispanser, tableRBDispanser['id'].eq(tableDiagnostic['dispanser_id']))
            queryTable = queryTable.leftJoin(tablePerson, tablePerson['id'].eq(tableDiagnosis['dispanserPerson_id']))
            cond, queryTable = diagnosticCondAdd(db, queryTable, filter, cond, tableDiagnosis, tableDiagnostic)
            query = db.getRecordListGroupBy(queryTable, cols, where=cond, group='Diagnosis.id', order='Diagnostic.endDate DESC')
            for record in query:
                printData[3] += forceString(record.value(0)) + '\n'
                printData[4] += forceString(record.value(1)) + '\n'
                printData[5] += forceString(record.value(2)) + '\n'
        return printData
    

    def loadData(self, masterId, filter):
        self.setIdList(self.getDiagnosisIdList(masterId, filter))


class CTakenMonitoringModel(CSurveillanceMonitoringModel):
    def __init__(self, parent):
        CSurveillanceMonitoringModel.__init__(self, parent)


    def getDiagnosticIdList(self, masterId, filter):
        diagnosticIdList = []
        if masterId:
            self.filter = filter
            begDate = self.filter.get('begDate', QDate.currentDate())
            endDate = self.filter.get('endDate', QDate())
            if not begDate:
                begDate = QDate.currentDate()
            db = QtGui.qApp.db
            tableDiagnosis = db.table('Diagnosis')
            tableDiagnostic = db.table('Diagnostic')
            tableRBDispanser = db.table('rbDispanser')
            cond = [tableDiagnosis['id'].eq(masterId),
                    tableDiagnosis['deleted'].eq(0),
                    tableDiagnostic['deleted'].eq(0),
                    tableDiagnostic['dispanser_id'].isNotNull(),
                    tableDiagnostic['endDate'].ge(begDate),
                    tableRBDispanser['name'].like(u'%взят%'),
                    ]
            if endDate:
                cond.append(tableDiagnostic['endDate'].le(endDate))
            queryTable = tableDiagnosis.innerJoin(tableDiagnostic, tableDiagnostic['diagnosis_id'].eq(tableDiagnosis['id']))
            queryTable = queryTable.innerJoin(tableRBDispanser, tableRBDispanser['id'].eq(tableDiagnostic['dispanser_id']))
            cond, queryTable = diagnosticCondAdd(db, queryTable, filter, cond, tableDiagnosis, tableDiagnostic)
            diagnosticIdList = db.getDistinctIdList(queryTable, [u'Diagnostic.id'], where=cond, order='Diagnostic.endDate DESC')
        return diagnosticIdList


    def loadData(self, masterId, filter):
        self.setIdList(self.getDiagnosticIdList(masterId, filter))


class CRemoveMonitoringModel(CSurveillanceMonitoringModel):
    def __init__(self, parent):
        CSurveillanceMonitoringModel.__init__(self, parent)


    def getDiagnosticIdList(self, masterId, filter):
        diagnosticIdList = []
        if masterId:
            self.filter = filter
            begDate = self.filter.get('begDate', QDate.currentDate())
            endDate = self.filter.get('endDate', QDate())
            if not begDate:
                begDate = QDate.currentDate()
            db = QtGui.qApp.db
            tableDiagnosis = db.table('Diagnosis')
            tableDiagnostic = db.table('Diagnostic')
            tableRBDispanser = db.table('rbDispanser')
            cond = [tableDiagnosis['id'].eq(masterId),
                    tableDiagnosis['deleted'].eq(0),
                    tableDiagnostic['deleted'].eq(0),
                    tableDiagnostic['dispanser_id'].isNotNull(),
                    tableDiagnostic['endDate'].ge(begDate),
                    tableRBDispanser['observed'].eq(0),
                    tableRBDispanser['name'].like(u'%снят%'),
                    ]
            if endDate:
                cond.append(tableDiagnostic['endDate'].le(endDate))
            queryTable = tableDiagnosis.innerJoin(tableDiagnostic, tableDiagnostic['diagnosis_id'].eq(tableDiagnosis['id']))
            queryTable = queryTable.innerJoin(tableRBDispanser, tableRBDispanser['id'].eq(tableDiagnostic['dispanser_id']))
            cond, queryTable = diagnosticCondAdd(db, queryTable, filter, cond, tableDiagnosis, tableDiagnostic)
            diagnosticIdList = db.getDistinctIdList(queryTable, [u'Diagnostic.id'], where=cond, order='Diagnostic.endDate DESC')
        return diagnosticIdList


    def loadData(self, masterId, filter):
        self.setIdList(self.getDiagnosticIdList(masterId, filter))


class CRemoveDiagnosisModel(CSurveillanceDiagnosisModel):
    def __init__(self, parent):
        CSurveillanceDiagnosisModel.__init__(self, parent)


    def getDiagnosisIdList(self, masterId, filter):
        diagnosisIdList = []
        if masterId:
            self.filter = filter
            begDate = self.filter.get('begDate', QDate())
            endDate = self.filter.get('endDate', QDate())
            db = QtGui.qApp.db
            tableDiagnosis = db.table('Diagnosis')
            tableDiagnostic = db.table('Diagnostic')
            tableRBDispanser = db.table('rbDispanser')
            cond = [tableDiagnosis['client_id'].eq(masterId),
                    tableDiagnosis['deleted'].eq(0),
                    tableDiagnostic['deleted'].eq(0),
                    tableDiagnostic['dispanser_id'].isNotNull(),
                    tableRBDispanser['observed'].eq(0),
                    tableRBDispanser['name'].like(u'%снят%'),
                    ]
            if begDate:
                cond.append(tableDiagnostic['endDate'].ge(begDate))
            if endDate:
                cond.append(tableDiagnostic['endDate'].le(endDate))
            queryTable = tableDiagnosis.innerJoin(tableDiagnostic, tableDiagnostic['diagnosis_id'].eq(tableDiagnosis['id']))
            queryTable = queryTable.innerJoin(tableRBDispanser, tableRBDispanser['id'].eq(tableDiagnostic['dispanser_id']))
            cond, queryTable = diagnosticCondAdd(db, queryTable, filter, cond, tableDiagnosis, tableDiagnostic)
            diagnosisIdList = db.getDistinctIdList(queryTable, [u'Diagnosis.id'], where=cond, order='Diagnostic.endDate DESC')
        return diagnosisIdList


    def loadData(self, masterId, filter):
        self.setIdList(self.getDiagnosisIdList(masterId, filter))


class CSubjectToSurveillanceMonitoringModel(CSurveillanceMonitoringModel):
    def __init__(self, parent):
        CSurveillanceMonitoringModel.__init__(self, parent)


    def getDiagnosticIdList(self, masterId, filter):
        diagnosticIdList = []
        if masterId:
            self.filter = filter
            begDate = self.filter.get('begDate', QDate.currentDate())
            endDate = self.filter.get('endDate', QDate())
            if not begDate:
                begDate = QDate.currentDate()
            db = QtGui.qApp.db
            tableDiagnosis = db.table('Diagnosis')
            tableDS = db.table('Diagnosis').alias('DS')
            tableDiagnostic = db.table('Diagnostic')
            tableEvent = db.table('Event')
            tableEventType = db.table('EventType')
            tableRBDispanser = db.table('rbDispanser')
            tableMKB = db.table('MKB')
            cond = [
                tableDiagnosis['id'].eq(masterId),
                tableDiagnosis['deleted'].eq(0),
                tableMKB['requiresFillingDispanser'].inlist([1, 2]),  # 1-иногда, 2-всегда
                db.joinOr([tableDiagnosis['dispanser_id'].isNull(), tableDiagnosis['dispanser_id'].inlist([3,4,5])]), #tt2432
                tableEventType['code'].notlike(u'%%rmDisp%'),
                tableEventType['code'].notlike(u'%%ЭЛМК%'),
                tableEventType['form'].ne(u'088'),
                tableDS['id'].isNull()
            ]
            queryTable = tableDiagnosis.innerJoin(tableDiagnostic, db.joinAnd([tableDiagnostic['diagnosis_id'].eq(tableDiagnosis['id']), 
                                                                               tableDiagnostic['deleted'].eq(0),
                                                                               tableDiagnostic['endDate'].ge(begDate),
                                                                               tableDiagnostic['endDate'].le(endDate) if endDate else 'TRUE',
                                                                               u'''Diagnostic.endDate = (SELECT MAX(d2.endDate)
                                                                                    FROM Diagnostic d2
                                                                                    WHERE
                                                                                        d2.diagnosis_id = Diagnosis.id
                                                                                        AND d2.deleted = 0
                                                                                        AND d2.endDate >= {}
                                                                                        AND {})'''.format(db.formatDate(begDate), 
                                                                                                          u'd2.endDate <= {}'.format(db.formatDate(endDate)) if endDate else 'TRUE')]))
            
            queryTable = queryTable.leftJoin(tableEvent, tableEvent['id'].eq(tableDiagnostic['event_id']))
            queryTable = queryTable.leftJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
            queryTable = queryTable.innerJoin(tableMKB, u"MKB.DiagID = Diagnosis.MKB")
            queryTable = queryTable.leftJoin(tableRBDispanser, tableRBDispanser['id'].eq(tableDiagnostic['dispanser_id']))
            queryTable = queryTable.leftJoin(tableDS, db.joinAnd([tableDS['client_id'].eq(masterId), u'LEFT(DS.MKB, 3) = LEFT(Diagnosis.MKB, 3)', tableDS['dispanser_id'].inlist([1,2,6])]))
            cond, queryTable = diagnosticCondAdd(db, queryTable, filter, cond, tableDiagnosis, tableDiagnostic)
            diagnosticIdList = []
            records = db.getDistinctRecordList(queryTable, [u'Diagnostic.id, Diagnostic.dispanser_id as isNotSubject'], cond, order='Diagnostic.endDate DESC')
            for record in records:
                if not forceRef(record.value('isNotSubject')):
                    diagnosticId = forceRef(record.value('id'))
                    if diagnosticId and diagnosticId not in diagnosticIdList:
                        diagnosticIdList.append(diagnosticId)
        return diagnosticIdList


    def loadData(self, masterId, filter):
        self.setIdList(self.getDiagnosticIdList(masterId, filter))


class CSubjectToSurveillanceDiagnosisModel(CSurveillanceDiagnosisModel):
    def __init__(self, parent):
        CSurveillanceDiagnosisModel.__init__(self, parent)


    def getDiagnosisIdList(self, masterId, filter):
        diagnosisIdList = []
        if masterId:
            self.filter = filter
            begDate = self.filter.get('begDate', QDate.currentDate())
            endDate = self.filter.get('endDate', QDate())
            if not begDate:
                begDate = QDate.currentDate()
            db = QtGui.qApp.db
            tableDiagnosis = db.table('Diagnosis')
            tableDS = db.table('Diagnosis').alias('DS')
            tableDiagnostic = db.table('Diagnostic')
            tableEvent = db.table('Event')
            tableEventType = db.table('EventType')
            tableRBDispanser = db.table('rbDispanser')
            tableMKB = db.table('MKB')
            cond = [
                tableDiagnosis['client_id'].eq(masterId),
                tableDiagnosis['deleted'].eq(0),
                tableMKB['requiresFillingDispanser'].inlist([1, 2]),  # 1-иногда, 2-всегда
                db.joinOr([tableDiagnosis['dispanser_id'].isNull(), tableDiagnosis['dispanser_id'].inlist([3,4,5])]), #tt2432
                tableEventType['code'].notlike(u'%%rmDisp%'),
                tableEventType['code'].notlike(u'%%ЭЛМК%'),
                tableEventType['form'].ne(u'088'),
                tableDS['id'].isNull()
            ]
            queryTable = tableDiagnosis.innerJoin(tableDiagnostic, db.joinAnd([tableDiagnostic['diagnosis_id'].eq(tableDiagnosis['id']), 
                                                                               tableDiagnostic['deleted'].eq(0),
                                                                               tableDiagnostic['endDate'].ge(begDate),
                                                                               tableDiagnostic['endDate'].le(endDate) if endDate else 'TRUE',
                                                                               u'''Diagnostic.endDate = (SELECT MAX(d2.endDate)
                                                                                    FROM Diagnostic d2
                                                                                    WHERE
                                                                                        d2.diagnosis_id = Diagnosis.id
                                                                                        AND d2.deleted = 0
                                                                                        AND d2.endDate >= {}
                                                                                        AND {})'''.format(db.formatDate(begDate), 
                                                                                                          u'd2.endDate <= {}'.format(db.formatDate(endDate)) if endDate else 'TRUE')]))
            queryTable = queryTable.leftJoin(tableEvent, tableEvent['id'].eq(tableDiagnostic['event_id']))
            queryTable = queryTable.leftJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
            queryTable = queryTable.innerJoin(tableMKB, u"MKB.DiagID = Diagnosis.MKB")
            queryTable = queryTable.leftJoin(tableRBDispanser, tableRBDispanser['id'].eq(tableDiagnostic['dispanser_id']))
            queryTable = queryTable.leftJoin(tableDS, db.joinAnd([tableDS['client_id'].eq(masterId), u'LEFT(DS.MKB, 3) = LEFT(Diagnosis.MKB, 3)', tableDS['dispanser_id'].inlist([1,2,6])]))
            cond, queryTable = diagnosticCondAdd(db, queryTable, filter, cond, tableDiagnosis, tableDiagnostic)
            diagnosisIdList = []
            records = db.getDistinctRecordList(queryTable, [u'Diagnosis.id, Diagnostic.dispanser_id as isNotSubject'], cond, order='Diagnostic.endDate DESC')
            for record in records:
                if not forceRef(record.value('isNotSubject')):
                    diagnosticId = forceRef(record.value('id'))
                    if diagnosticId and diagnosticId not in diagnosisIdList:
                        diagnosisIdList.append(diagnosticId)
        return diagnosisIdList


    def loadData(self, masterId, filter):
        self.setIdList(self.getDiagnosisIdList(masterId, filter))


class CSurveillancePlanningModel(CRecordListModel):
    class CEnableEditCol(CInDocTableCol):
        def __init__(self, title, fieldName, width):
            CInDocTableCol.__init__(self, title, fieldName, width, readOnly=True)

        def toString(self, val, record):
            if val == 2:
                return QVariant(u'Не подлежит')
            elif val == 1:
                return QVariant(u'Не отправлен')
            else:
                return QVariant(u'Отправлен')

    class CMonthCol(CEnumInDocTableCol):
        monthNames = (
        u'январь', u'февраль', u'март', u'апрель', u'май', u'июнь', u'июль', u'август', u'сентябрь', u'октябрь',
        u'ноябрь', u'декабрь')

        def __init__(self, title, fieldName, width):
            CEnumInDocTableCol.__init__(self, title, fieldName, width, self.monthNames)

        def toString(self, val, record):
            return toVariant(self.values[forceInt(val) - 1])

        def setEditorData(self, editor, value, record):
            editor.setCurrentIndex(forceInt(value) - 1)

        def getEditorData(self, editor):
            if editor.currentIndex() == -1:
                return QVariant()
            else:
                return toVariant(editor.currentIndex() + 1)

    # изменения применяются в БД сразу же при редактировании
    def __init__(self, parent):
        CRecordListModel.__init__(self, parent)
        db = QtGui.qApp.db
        self._table = db.table('DiagnosisDispansPlaned')
        self._idFieldName = 'id'
        self._clientIdFieldName = 'client_id'
        self._diagnosisIdFieldName = 'diagnosis_id'
        self._tableFields = None
        self._enableAppendLine = True
        self._extColsPresent = False
        self.currentClientId = None
        self.currentDiagnosisId = None
        self.addCol(CPersonFindInDocTableCol(u'Запланировал врач', 'person_id', 20, 'vrbPersonWithSpecialityAndOrgStr',
                                             parent=parent))
        self.addCol(CIntInDocTableCol(u'Год осмотра', 'year', 10, low=QDate.currentDate().year(), high=9999))
        self.addCol(CSurveillancePlanningModel.CMonthCol(u'Месяц осмотра', 'month', 10))
        self.enableEditCol = CSurveillancePlanningModel.CEnableEditCol(u'Экспорт в ТФОМС', 'enableEdit', 10)
        self.addExtCol(self.enableEditCol, QVariant.Bool)

    table = property(lambda self: self._table)

    def getTableFieldList(self):
        if self._tableFields is None:
            fields = []
            for col in self._cols:
                if col.external():
                    field = database.CSurrogateField(col.fieldName(), col.valueType())
                else:
                    field = self._table[col.fieldName()]
                fields.append(field)
            fields.append(self._table['id'])
            fields.append(self._table['client_id'])
            fields.append(self._table['diagnosis_id'])
            for col in self._hiddenCols:
                field = self._table[col]
                fields.append(field)
            self._tableFields = fields
        return self._tableFields

    def loadItems(self, clientId, diagnosisId):
        db = QtGui.qApp.db
        self._currentClientId = clientId
        self._currentDiagnosisId = diagnosisId
        if clientId is None or diagnosisId is None:
            self._items = []
        else:
            cols = ['id', 'client_id', 'diagnosis_id', 'isExport']
            for col in self._cols:
                if not col.external():
                    cols.append(col.fieldName())
            for col in self._hiddenCols:
                cols.append(col)
            table = self._table
            filter = [
                table['diagnosis_id'].eq(diagnosisId),
            ]
            if table.hasField('deleted'):
                filter.append(table['deleted'].eq(0))
            order = ['year desc', 'month desc']
            self._items = db.getRecordList(table, cols, filter, order)
            idList = []
            for item in self._items:
                idList.append(forceRef(item.value('id')))
            tablePlanExport = db.table('disp_PlanExport')
            planExportFilter = [
                tablePlanExport['exportKind'].eq('DiagnosisDispansPlaned'),
                tablePlanExport['row_id'].inlist(idList),
            ]
            exportedIdSet = set(db.getDistinctIdList(tablePlanExport, idCol='row_id', where=planExportFilter))
            enableEditField = QtSql.QSqlField('enableEdit', self.enableEditCol.valueType())
            for item in self._items:
                id = forceRef(item.value('id'))
                item.append(enableEditField)
                item.setValue('enableEdit', 2 if not forceBool(item.value('isExport')) else int(id not in exportedIdSet))
        self.reset()

    def getEmptyRecord(self):
        record = QtSql.QSqlRecord()
        fields = self.getTableFieldList()
        for field in fields:
            record.append(QtSql.QSqlField(field.field))
        currentDate = QDate.currentDate()
        record.setValue('client_id', toVariant(self._currentClientId))
        record.setValue('diagnosis_id', toVariant(self._currentDiagnosisId))
        record.setValue('person_id', toVariant(QtGui.qApp.userId))
        record.setValue('year', toVariant(currentDate.year()))
        record.setValue('month', toVariant(currentDate.month()))
        record.setValue('enableEdit', toVariant(True))
        return record

    def appendItemToModel(self, item):
        self._items.append(item)
        count = len(self._items)
        rootIndex = QModelIndex()
        self.beginInsertRows(rootIndex, count, count)
        self.insertRows(count, 1, rootIndex)
        self.endInsertRows()

    def insertItemInDb(self, item):
        db = QtGui.qApp.db
        dbRecord = self.removeExtCols(item)
        return db.insertRecord(self._table, dbRecord)

    def updateItemInDb(self, itemId, fieldName, value):
        db = QtGui.qApp.db
        dbRecord = QtSql.QSqlRecord()
        dbRecord.append(self._table['id'].field)
        dbRecord.append(self._table[fieldName].field)
        dbRecord.setValue('id', toVariant(itemId))
        dbRecord.setValue(fieldName, value)
        db.updateRecord(self._table, dbRecord)

    def deleteItemsInDb(self, items):
        db = QtGui.qApp.db
        idList = []
        for item in items:
            id = forceRef(item.value('id'))
            idList.append(id)
        filter = [self._table['id'].inlist(idList)]
        db.markRecordsDeleted(self._table, filter)

    def removeExtCols(self, srcRecord):
        record = self._table.newRecord()
        for i in xrange(record.count()):
            record.setValue(i, srcRecord.value(record.fieldName(i)))
        return record

    def removeRows(self, row, count, parentIndex=QModelIndex()):
        if 0 <= row and row + count <= len(self._items):
            try:
                self.deleteItemsInDb(self._items[row:row + count])
            except Exception as e:
                QtGui.qApp.logCurrentException()
                QtGui.QMessageBox.critical(None, u'Произошла ошибка при удалении записей', exceptionToUnicode(e),
                                           QtGui.QMessageBox.Close)
                return False
            self.beginRemoveRows(parentIndex, row, row + count - 1)
            del self._items[row:row + count]
            self.endRemoveRows()
            return True
        else:
            return False

    def validateMonth(self, item, canChangeYear, canChangeMonth):
        otherMonths = set()
        itemId = forceRef(item.value('id'))
        for otherItem in self._items:
            if itemId is not None and forceRef(otherItem.value('id')) == itemId:
                continue
            year = forceInt(otherItem.value('year'))
            month = forceInt(otherItem.value('month'))
            elem = (year, month)
            otherMonths.add(elem)
        year = forceInt(item.value('year'))
        month = forceInt(item.value('month'))
        while (year, month) in otherMonths:
            if not canChangeMonth:
                monthName = CSurveillancePlanningModel.CMonthCol.monthNames[month - 1]
                QtGui.QMessageBox.warning(None, u'Ошибка ввода данных',
                                          u'Запись за %s %d уже существует!' % (monthName, year),
                                          QtGui.QMessageBox.Close)
                return False
            if month == 12 and not canChangeYear:
                QtGui.QMessageBox.warning(None, u'Ошибка ввода данных', u'Все месяцы за %d год уже заняты!' % year,
                                          QtGui.QMessageBox.Close)
                return False
            if month < 12:
                month += 1
            else:
                year += 1
                month = 1
        item.setValue('year', toVariant(year))
        item.setValue('month', toVariant(month))
        return True

    def isLocked(self, row):
        record = self._items[row] if row < len(self._items) else None
        return forceInt(record.value('enableEdit')) > 0 if record else True

    def flags(self, index):
        result = CRecordListModel.flags(self, index)
        row = index.row()
        record = self._items[row] if row < len(self._items) else None
        enableEdit = forceBool(record.value('enableEdit')) if record else True
        if not enableEdit:
            result = result & (~Qt.ItemIsEditable) & (~Qt.ItemIsUserCheckable)
        return result

    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.EditRole:
            if value.isNull():
                return False
            column = index.column()
            row = index.row()
            col = self._cols[column]
            fieldName = col.fieldName()
            if row == len(self._items):
                existingItem = None
                updatedItem = self.getEmptyRecord()
                if fieldName == 'year' and QDate.currentDate().year() != forceInt(value):
                    updatedItem.setValue('month', toVariant(1))
            else:
                existingItem = self._items[row]
                updatedItem = QtSql.QSqlRecord(existingItem)
            updatedItem.setValue(fieldName, value)
            if existingItem is None or fieldName in ('month', 'year'):
                canChangeMonth = (existingItem is None and fieldName != 'month')
                canChangeYear = (canChangeMonth and fieldName != 'year')
                if not self.validateMonth(updatedItem, canChangeMonth=canChangeMonth, canChangeYear=canChangeYear):
                    return False
            if existingItem is None:
                try:
                    id = self.insertItemInDb(updatedItem)
                    updatedItem.setValue('id', QVariant(id))
                except Exception as e:
                    QtGui.qApp.logCurrentException()
                    QtGui.QMessageBox.critical(None, u'Произошла ошибка при добавлении записи', exceptionToUnicode(e),
                                               QtGui.QMessageBox.Close)
                    return False
                self.appendItemToModel(updatedItem)
            else:
                try:
                    id = forceRef(existingItem.value('id'))
                    self.updateItemInDb(id, fieldName, value)
                except Exception as e:
                    QtGui.qApp.logCurrentException()
                    QtGui.QMessageBox.critical(None, u'Произошла ошибка при изменении записи', exceptionToUnicode(e),
                                               QtGui.QMessageBox.Close)
                    return False
                existingItem.setValue(fieldName, value)
                self.emitCellChanged(row, column)
            return True
        return False


class CConsistsPlanningModel(CSurveillancePlanningModel):
    pass


class CTakenPlanningModel(CSurveillancePlanningModel):
    pass


class CRemovePlanningModel(CSurveillancePlanningModel):
    pass


class CSubjectToSurveillancePlanningModel(CSurveillancePlanningModel):
    pass


class CSurveillanceClientEditDialog(CClientEditDialog):
    def __init__(self, parent):
        CClientEditDialog.__init__(self, parent)


    def saveData(self):
        isRightAdmin = QtGui.qApp.isAdmin()
        isSurReadClientInfo = QtGui.qApp.userHasRight(urSurReadClientInfo) or isRightAdmin
        isSurEditClientInfo = QtGui.qApp.userHasRight(urSurEditClientInfo) or isRightAdmin
        if isSurReadClientInfo and not isSurEditClientInfo:
            QtGui.QMessageBox.warning(self,
                                      u'Внимание',
                                      u'Право только на чтение!',
                                      QtGui.QMessageBox.Ok,
                                      QtGui.QMessageBox.Ok)
            return False
        if isSurEditClientInfo:
            return self.checkDataEntered() and self.save()
        return False


def diagnosticCondAdd(db, queryTable, filter, cond, tableDiagnosis, tableDiagnostic):
    MKBFilter = filter.get('MKBFilter', 0)
    if MKBFilter:
        MKBFrom = filter.get('MKBFrom', None)
        MKBTo   = filter.get('MKBTo', None)
        cond.append(isSurveillanceMKB(MKBFrom, MKBTo))
    diseaseCharacterId = filter.get('diseaseCharacterId', None)
    if diseaseCharacterId:
        cond.append(tableDiagnosis['character_id'].eq(diseaseCharacterId))
    personDN = filter.get('personDN')
    if personDN:
        cond.append(tableDiagnosis['dispanserPerson_id'].eq(personDN))
    orgStructureId = filter.get('orgStructureId', None)
    specialityIdListAsString = filter.get('specialityId', None)
    if orgStructureId or specialityIdListAsString:
        tablePerson = db.table('Person')
        queryTable = queryTable.innerJoin(tablePerson, tablePerson['id'].eq(tableDiagnosis['dispanserPerson_id']))
        cond.append(tablePerson['deleted'].eq(0))
    if orgStructureId:
        orgStructureIdList = db.getDescendants('OrgStructure', 'parent_id', orgStructureId)
        if orgStructureIdList:
            cond.append(tablePerson['orgStructure_id'].inlist(orgStructureIdList))
    if specialityIdListAsString:
        # specialityType = filter.get('specialityType', None)
        cond.append('Person.speciality_id IN (%s)'%specialityIdListAsString)
    return cond, queryTable
    

def clientsCondAdd(db, queryTable, filter, cond, tableClient):
    def addAddressCond(cond3, addrType, addrIdList):
        tableClientAddress = db.table('ClientAddress')
        subcond = [tableClientAddress['client_id'].eqEx('`Client`.`id`'),
                   tableClientAddress['id'].eqEx(u'getClientLocAddressId(Client.id)' if addrType else u'getClientRegAddressId(Client.id)')
                  ]
        if addrIdList is None:
            subcond.append(tableClientAddress['address_id'].isNull())
            subcondNoCAId = u'(SELECT %s IS NULL)'%(u'getClientLocAddressId(Client.id)' if addrType else u'getClientRegAddressId(Client.id)')
        else:
            subcond.append(tableClientAddress['address_id'].inlist(addrIdList))
        if addrIdList is None:
            cond3.append(db.joinOr([db.existsStmt(tableClientAddress, subcond), subcondNoCAId]))
        else:
            cond3.append(db.existsStmt(tableClientAddress, subcond))
    sex = filter.get('sex', 0)
    if sex > 0:
        cond.append(tableClient['sex'].eq(sex))
    ageFor = filter.get('ageFor', 0)
    ageTo = filter.get('ageTo', 0)
    if ageFor <= ageTo and not all([ageFor == 0,  ageTo == 150]):
        currentDate = db.formatDate(QDate.currentDate())
        cond.append('''(%s >= ADDDATE(Client.birthDate, INTERVAL %d YEAR)) AND (%s < ADDDATE(Client.birthDate, INTERVAL %d YEAR))''' % (currentDate, ageFor, currentDate, ageTo+1))
    death = filter.get('death', 0)
    if death == 1:
        cond.append(tableClient['deathDate'].isNull())
    elif death == 2:
        cond.append(tableClient['deathDate'].isNotNull())
        deathBegDate = filter.get('deathBegDate', None)
        deathEndDate = filter.get('deathEndDate', None)
        if deathBegDate:
            cond.append(tableClient['deathDate'].dateGe(deathBegDate))
        if deathEndDate:
            cond.append(tableClient['deathDate'].dateLe(deathEndDate))
    accountingSystemId = filter.get('accountingSystemId', None)
    filterClientId = filter.get('filterClientId', None)
    if accountingSystemId and filterClientId:
        tableIdentification = db.table('ClientIdentification')
        queryTable = queryTable.innerJoin(tableIdentification, tableIdentification['client_id'].eq(tableClient['id']))
        cond.append(tableIdentification['accountingSystem_id'].eq(accountingSystemId))
        cond.append(tableIdentification['identifier'].eq(filterClientId))
        cond.append(tableIdentification['deleted'].eq(0))
    elif filterClientId:
        cond.append(tableClient['id'].eq(filterClientId))
    if filter.get('isFilterEvent', False):
        eventVisitType = filter.get('eventVisitType', None)
        if eventVisitType is not None:
            eventBegDate = filter.get('eventBegDate', QDate())
            eventEndDate = filter.get('eventEndDate', QDate())
            tableEvent = db.table('Event').alias(u'E')
            condDate = []
            if eventBegDate:
                condDate.append(db.joinOr([tableEvent['execDate'].isNull(), tableEvent['execDate'].ge(eventBegDate)]))
            if eventEndDate:
                condDate.append(tableEvent['setDate'].le(eventEndDate))
            chkEventVisitDiagnosis = filter.get('chkEventVisitDiagnosis', 0)
            if chkEventVisitDiagnosis:
                if eventVisitType == 0:
                    cond.append(u'''EXISTS(SELECT E.id
                                           FROM Event AS E
                                           LEFT JOIN EventType et on et.id = E.eventType_id
                                           LEFT JOIN rbEventTypePurpose ep on ep.id = purpose_id
                                           INNER JOIN Diagnostic AS DC ON DC.event_id = E.id
                                           INNER JOIN Diagnosis AS DS ON DS.id = DC.diagnosis_id
                                           WHERE E.client_id = Client.id
                                           AND DC.deleted = 0
                                           AND DS.deleted = 0
                                           AND DS.MKB = Diagnosis.MKB
                                           AND ep.purpose = 6
                                           AND E.deleted = 0 %s)''' % (('AND %s' % db.joinAnd(condDate)) if condDate else u''))
                if eventVisitType == 1:
                    cond.append(u'''NOT EXISTS(SELECT E.id
                                           FROM Event AS E
                                           LEFT JOIN EventType et on et.id = E.eventType_id
                                           LEFT JOIN rbEventTypePurpose ep on ep.id = purpose_id
                                           INNER JOIN Diagnostic AS DC ON DC.event_id = E.id
                                           INNER JOIN Diagnosis AS DS ON DS.id = DC.diagnosis_id
                                           WHERE E.client_id = Client.id
                                           AND DC.deleted = 0
                                           AND DS.deleted = 0
                                           AND DS.MKB = Diagnosis.MKB
                                           AND ep.purpose = 6
                                           AND E.deleted = 0 %s)''' % (('AND %s' % db.joinAnd(condDate)) if condDate else u''))
            else:
                if eventVisitType == 0:
                    cond.append(u'''EXISTS(SELECT E.id FROM Event AS E WHERE E.client_id = Client.id AND E.deleted = 0 %s)''' % (('AND %s' % db.joinAnd(condDate)) if condDate else u''))
                if eventVisitType == 1:
                    cond.append(u'''NOT EXISTS(SELECT E.id FROM Event AS E WHERE E.client_id = Client.id AND E.deleted = 0 %s)''' % (('AND %s' % db.joinAnd(condDate)) if condDate else u''))
    attachOrgId = filter.get('attachOrganisationId', None)
    if attachOrgId:
        begDate = filter.get('begDate', QDate.currentDate())
        endDate = filter.get('endDate', None)
        isNotAttachOrganisation = filter.get('isNotAttachOrganisation', False)
        stmt = '''{} EXISTS (SELECT ClientAttach.id
           FROM ClientAttach
           LEFT JOIN rbAttachType ON rbAttachType.id = ClientAttach.attachType_id
           WHERE ClientAttach.deleted=0
           AND ClientAttach.client_id = Client.id AND LPU_id={}
           AND ClientAttach.id in (SELECT MAX(CA2.id)
                       FROM ClientAttach AS CA2
                       LEFT JOIN rbAttachType AS rbAttachType2 ON rbAttachType2.id = CA2.attachType_id
                       WHERE CA2.deleted=0 AND CA2.client_id = Client.id {} {}))'''.format(
                           (u'NOT' if isNotAttachOrganisation else u''), 
                           attachOrgId,
                           u'AND CA2.begDate <= {}'.format(db.formatDate(endDate)) if endDate else u'AND CA2.begDate <= {}'.format(db.formatDate(begDate)),
                           u'AND (CA2.endDate is NULL or CA2.endDate >= {})'.format(db.formatDate(begDate)))
        cond.append(stmt)
    if filter.get('isFilterAddressOrgStructure', False):
        addrType = filter.get('addressOrgStructureTypeId', 0)
        areaOrgStructureId = filter.get('addressOrgStructureId', None)
        if areaOrgStructureId:
            addrIdList = None
            cond2 = []
            if (addrType+1) & 1:
                addrIdList = getOrgStructureAddressIdList(areaOrgStructureId)
                addAddressCond(cond2, 0, addrIdList)
            if (addrType+1) & 2:
                if addrIdList is None:
                    addrIdList = getOrgStructureAddressIdList(areaOrgStructureId)
                addAddressCond(cond2, 1, addrIdList)
            if (addrType + 1) & 4:
                if areaOrgStructureId:
                    begDate = filter.get('begDate', QDate.currentDate())
                    endDate = filter.get('endDate', None)
                    orgStructureIdList = getOrgStructureDescendants(areaOrgStructureId)
                    outerCond = ['ClientAttach.client_id = Client.id']
                    innerCond = ['CA2.client_id = Client.id']
                    outerCond.append('ClientAttach.orgStructure_id IN (%s)' % (u','.join(forceString(areaOrgStructureId) for areaOrgStructureId in orgStructureIdList)))
                    innerCond.append('rbAttachType2.temporary=0')
                    stmt = '''EXISTS (SELECT ClientAttach.id
                       FROM ClientAttach
                       LEFT JOIN rbAttachType ON rbAttachType.id = ClientAttach.attachType_id
                       WHERE ClientAttach.deleted=0
                       AND {}
                       AND ClientAttach.id in (SELECT MAX(CA2.id)
                                   FROM ClientAttach AS CA2
                                   LEFT JOIN rbAttachType AS rbAttachType2 ON rbAttachType2.id = CA2.attachType_id
                                   WHERE CA2.deleted=0 AND {} {} {}))'''.format(
                                       db.joinAnd(outerCond), 
                                       db.joinAnd(innerCond),
                                       u'AND CA2.begDate <= {}'.format(db.formatDate(endDate)) if endDate else u'AND CA2.begDate <= {}'.format(db.formatDate(begDate)),
                                       u'AND (CA2.endDate is NULL or CA2.endDate >= {})'.format(db.formatDate(begDate)))
                    cond2.append(stmt)
                else:
                    begDate = filter.get('begDate', QDate.currentDate())
                    endDate = filter.get('endDate', None)
                    outerCond = ['ClientAttach.client_id = Client.id']
                    innerCond = ['CA2.client_id = Client.id']
                    outerCond.append('LPU_id=%d' % QtGui.qApp.currentOrgId())
                    innerCond.append('rbAttachType2.temporary=0')
                    stmt = '''EXISTS (SELECT ClientAttach.id
                       FROM ClientAttach
                       LEFT JOIN rbAttachType ON rbAttachType.id = ClientAttach.attachType_id
                       WHERE ClientAttach.deleted=0
                       AND {}
                       AND ClientAttach.id in (SELECT MAX(CA2.id)
                                   FROM ClientAttach AS CA2
                                   LEFT JOIN rbAttachType AS rbAttachType2 ON rbAttachType2.id = CA2.attachType_id
                                   WHERE CA2.deleted=0 AND {} {} {}))'''.format(
                                       db.joinAnd(outerCond), 
                                       db.joinAnd(innerCond),
                                       u'AND CA2.begDate <= {}'.format(db.formatDate(endDate)) if endDate else u'AND CA2.begDate <= {}'.format(db.formatDate(begDate)),
                                       u'AND (CA2.endDate is NULL or CA2.endDate >= {})'.format(db.formatDate(begDate)))
                    cond2.append(stmt)
            if cond2:
                cond.append(db.joinOr(cond2))
    if filter.get('isFilterAddress', False):
        addrType = filter.get('addressTypeId', 0)
        KLADRCode = filter.get('addressCity', None)
        Okato = filter.get('addressOkato', None)
        KLADRStreetCode = filter.get('addressStreet', None)
        KLADRStreetCodeList = filter.get('KLADRStreetCodeList', [])
        house = filter.get('addressHouse', u'')
        corpus = filter.get('addressCorpus', u'')
        flat = filter.get('addressFlat', u'')
        if KLADRCode or Okato or KLADRStreetCode:
            tableClientAddress = db.table('ClientAddress')
            tableAddressHouse = db.table('AddressHouse')
            tableAddress = db.table('Address')
            queryTable = queryTable.leftJoin(tableClientAddress, tableClientAddress['client_id'].eq(tableClient['id']))
            queryTable = queryTable.leftJoin(tableAddress, tableAddress['id'].eq(tableClientAddress['address_id']))
            queryTable = queryTable.leftJoin(tableAddressHouse, tableAddressHouse['id'].eq(tableAddress['house_id']))
            cond.append('''ClientAddress.id IN (SELECT MAX(CA.id) FROM ClientAddress AS CA WHERE CA.type=%d
            AND CA.deleted=0 AND CA.client_id=Client.id)''' % addrType)
            if KLADRStreetCode:
                cond.append(tableAddressHouse['KLADRStreetCode'].eq(KLADRStreetCode))
                if Okato and house:
                    okatoCond = (u'''kladr.DOMA.OCATD LIKE \'%s%%\'''' % Okato) if Okato else '''1'''
                    cond.append(u'''(SELECT DISTINCT kladr.STREET.CODE
                    FROM kladr.STREET INNER JOIN kladr.DOMA ON LEFT(kladr.DOMA.CODE,15) = LEFT(kladr.STREET.CODE,15)
                    WHERE %sRIGHT(kladr.STREET.CODE,2)=\'00\'
                    AND kladr.STREET.CODE = %s
                    AND %s
                    AND kladr.STREET.CODE = AddressHouse.KLADRStreetCode
                    AND (IF(TRIM(AddressHouse.number) != '', FIND_IN_SET(AddressHouse.number,
                    kladr.DOMA.flatHouseList), 1))
                    ORDER BY kladr.STREET.NAME, kladr.STREET.SOCR, kladr.STREET.CODE)'''%((u'kladr.DOMA.CODE LIKE \'%s%%\' AND '%(KLADRCode[0:-2])) if KLADRCode else u'', KLADRStreetCode, okatoCond))
                else:
                    cond.append(tableAddressHouse['KLADRStreetCode'].eq(KLADRStreetCode))
            elif Okato:
                cond.append(tableAddressHouse['KLADRStreetCode'].inlist(KLADRStreetCodeList))
            elif KLADRCode:
                mask = getLikeMaskForRegion(KLADRCode)
                if mask == KLADRCode:
                    cond.append(tableAddressHouse['KLADRCode'].eq(KLADRCode))
                else:
                    cond.append(tableAddressHouse['KLADRCode'].like(mask))
            if house:
                cond.append(tableAddressHouse['number'].eq(house))
            if corpus:
                cond.append('''TRIM(AddressHouse.corpus) = TRIM('%s')'''%(corpus))
            if flat:
                cond.append(tableAddress['flat'].eq(flat))
    if filter.get('isSocStatuses', False):
        socStatusesClass = filter.get('socStatusesClass', None)
        socStatusesType = filter.get('socStatusesType', None)
        socStatusesBegDate = filter.get('socStatusesBegDate', QDate())
        socStatusesEndDate = filter.get('socStatusesEndDate', QDate())
        if socStatusesClass or socStatusesType:
            tableClientSocStatus = db.table('ClientSocStatus')
            cond.append(tableClientSocStatus['deleted'].eq(0))
            if socStatusesClass:
                socStatusClassIdList = db.getDescendants('rbSocStatusClass', 'group_id', socStatusesClass)
                if socStatusClassIdList:
                    stmtStatusTypeId = u'''SELECT DISTINCT rbSocStatusClassTypeAssoc.type_id
            FROM  rbSocStatusClassTypeAssoc
            WHERE rbSocStatusClassTypeAssoc.class_id IN (%s)''' % (u','.join(str(socStatusClassId) for socStatusClassId in socStatusClassIdList))
                    queryStatusTypeId = db.query(stmtStatusTypeId)
                    resultStatusTypeIdList = []
                    while queryStatusTypeId.next():
                        resultStatusTypeIdList.append(queryStatusTypeId.value(0).toInt()[0])
                    if resultStatusTypeIdList:
                        cond.append(tableClientSocStatus['socStatusType_id'].inlist(resultStatusTypeIdList))
                    else:
                        parentSocStatusClassIdList = db.getTheseAndParents('rbSocStatusClass', 'group_id', [socStatusesClass])
                        cond.append(tableClientSocStatus['socStatusClass_id'].inlist(parentSocStatusClassIdList))
                        cond.append(tableClientSocStatus['socStatusType_id'].isNull())
                else:
                    cond.append(tableClientSocStatus['socStatusClass_id'].eq(socStatusesClass))
            if socStatusesType:
                cond.append(tableClientSocStatus['socStatusType_id'].eq(socStatusesType))
            if socStatusesBegDate:
                cond.append(db.joinOr([tableClientSocStatus['endDate'].dateGe(socStatusesBegDate),
                                       tableClientSocStatus['endDate'].isNull()
                                       ]
                                      )
                            )
            if socStatusesEndDate:
                cond.append(db.joinOr([tableClientSocStatus['begDate'].dateLe(socStatusesEndDate),
                                       tableClientSocStatus['begDate'].isNull()
                                       ]
                                      )
                            )
            queryTable = queryTable.leftJoin(tableClientSocStatus, tableClient['id'].eq(tableClientSocStatus['client_id']))
    return cond, queryTable


def getAgeSurveillanceRangeCond(ageFor, ageTo):
    return '''(DATE(Diagnostic.endDate) >= ADDDATE(Client.birthDate, INTERVAL %d YEAR))
           AND (DATE(Diagnostic.endDate) < ADDDATE(Client.birthDate, INTERVAL %d YEAR))''' % (ageFor, ageTo+1)


def isSurveillanceMKB(MKBFrom, MKBTo):
    return '''Diagnosis.MKB >= '%s' AND Diagnosis.MKB <= '%s' '''%(MKBFrom, MKBTo)


def isProphylaxisMKB(MKBFrom, MKBTo):
    return '''ProphylaxisPlanning.MKB >= '{}' AND ProphylaxisPlanning.MKB <= '{}' '''.format(MKBFrom, MKBTo)


class CSurveillanceFindClientInfoDialog(CFindClientInfoDialog):
    def __init__(self, parent, clientIdList=None):
        CFindClientInfoDialog.__init__(self, parent, clientIdList)
        if clientIdList is None:
            clientIdList = []

    def setupGetClientIdMenu(self):
        self.addObject('mnuGetClientId', QtGui.QMenu(self))
        self.addObject('actGetClientId', QtGui.QAction(u'''Добавить в фильтр "Диспансерного наблюдения"''', self))
        self.mnuGetClientId.addAction(self.actGetClientId)



def isSurveillanceActive(masterId, filterPP, filterD):
    diagnosisIdList = []
    if masterId:
        begDate = filterPP.get('begDate', QDate())
        eventId = filterPP.get('event_id', None)
        db = QtGui.qApp.db
        MKBs = []
        if eventId:
            tableDiagnosis = db.table('Diagnosis')
            tableDiagnostic = db.table('Diagnostic')
            queryTable = tableDiagnostic.leftJoin(tableDiagnosis, tableDiagnosis['id'].eq(tableDiagnostic['diagnosis_id']))
            cond = [
                tableDiagnostic['dispanser_id'].inlist([3,4,5]),
                tableDiagnosis['dispanser_id'].inlist([3,4,5]),
                tableDiagnostic['event_id'].eq(eventId),
                tableDiagnostic['deleted'].eq(0),
                tableDiagnosis['deleted'].eq(0),
                tableDiagnosis['client_id'].eq(masterId)
            ]
            recordList = db.getRecordListGroupBy(queryTable, ['MKB'], where=cond, group='MKB', order='Diagnostic.endDate DESC')
            for record in recordList:
                MKB = forceString(record.value('MKB'))
                if MKB and MKB not in MKBs:
                    MKBs.append(MKB)
        tableProphylaxisPlanning = db.table('ProphylaxisPlanning')
        cond = [tableProphylaxisPlanning['client_id'].eq(masterId),
                tableProphylaxisPlanning['deleted'].eq(0),
                tableProphylaxisPlanning['dispanser_id'].isNotNull(),
                tableProphylaxisPlanning['parent_id'].isNotNull()
                ]
        if begDate:
            cond.append(tableProphylaxisPlanning['endDate'].ge(begDate))
        if eventId:
            cond.append(tableProphylaxisPlanning['MKB'].inlist(MKBs))
        diagnosisIdList = db.getDistinctIdList(tableProphylaxisPlanning, [u'ProphylaxisPlanning.id'], where=cond, order='ProphylaxisPlanning.endDate DESC')
        if not diagnosisIdList:
            date = filterD.get('begDate', QDate.currentDate())
            if not date:
                date = QDate.currentDate()
            eventId = filterD.get('event_id', None)
            db = QtGui.qApp.db
            tableDiagnosis = db.table('Diagnosis')
            tableDiagnostic = db.table('Diagnostic')
            tableRBDispanser = db.table('rbDispanser')
            cond = [tableDiagnosis['client_id'].eq(masterId),
                    tableDiagnosis['deleted'].eq(0),
                    tableDiagnostic['deleted'].eq(0),
                    db.joinOr([db.joinAnd([tableDiagnostic['endDate'].isNotNull(), tableDiagnostic['endDate'].le(date)]),
                               db.joinAnd([tableDiagnostic['endDate'].isNull(), tableDiagnostic['setDate'].le(date)])]),
                    tableRBDispanser['observed'].eq(1)
                    ]
            if eventId:
                cond.append(tableDiagnostic['event_id'].eq(eventId))
                cond.append(tableDiagnosis['MKB'].ne(''))
            queryTable = tableDiagnosis.innerJoin(tableDiagnostic, tableDiagnostic['diagnosis_id'].eq(tableDiagnosis['id']))
            queryTable = queryTable.innerJoin(tableRBDispanser, tableRBDispanser['id'].eq(tableDiagnosis['dispanser_id']))
            diagnosisIdList = db.getDistinctIdList(queryTable, [u'Diagnosis.id'], where=cond, order='Diagnostic.endDate DESC')
    if diagnosisIdList:
        return True
    return False