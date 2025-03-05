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

from PyQt4.QtCore import pyqtSignature, Qt, QEvent
from PyQt4 import QtGui

from Registry.AmbCardMixin import CAmbCardMixin


from Ui_AmbCardPage        import Ui_AmbCardPage

class CAmbCardPage(QtGui.QWidget, CAmbCardMixin, Ui_AmbCardPage):
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
    @pyqtSignature('int')
    def on_actAmbCardPrintVisitsHistory_printByTemplate(self, *args): CAmbCardMixin.on_actAmbCardPrintVisitsHistory_printByTemplate(self, *args)
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

    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self._clientId = None
        self._clientSex = None
        self._clientAge = None
        self.ambCardMonitoringIsInitialised = False
        self.ambCardComboBoxFilters = {}
        self.preSetupUi()
        self.setupUi(self)
        self.postSetupUi()


    def setClientId(self, clientId, clientSex, clientAge):
        self._clientId = clientId
        self._clientSex = clientSex
        self._clientAge = clientAge
        self.tabRadiationDose.setClientId(clientId)


    def currentClientId(self):
        return self._clientId


    def currentClientSex(self):
        return self._clientSex


    def currentClientAge(self):
        return self._clientAge


    def keyPressEvent(self, event):
        if event.type() == QEvent.KeyPress and event.key() in (Qt.Key_Enter, Qt.Key_Return):
            currentIndex = self.tabAmbCardContent.currentIndex()
            if currentIndex == 0:   # диагнозы
                self.on_cmdAmbCardDiagnosticsButtonBox_apply()
            elif currentIndex == 1:  # статус
                self.on_cmdAmbCardStatusButtonBox_apply()
            elif currentIndex == 2:  # диагностика
                self.on_cmdAmbCardDiagnosticButtonBox_apply()
            elif currentIndex == 3:  # лечение
                self.on_cmdAmbCardCureButtonBox_apply()
            elif currentIndex == 4:  # мероприятия
                self.on_cmdAmbCardMiscButtonBox_apply()
            elif currentIndex == 6:  # визиты
                self.on_cmdAmbCardVisitButtonBox_apply()
            elif currentIndex == 8:  # опрос
                self.on_cmdAmbCardSurveyButtonBox_apply()
