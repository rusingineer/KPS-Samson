# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2026 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, pyqtSignature, QAbstractTableModel, QVariant

from library.DialogBase        import CDialogBase
from library.TableModel import CCol
from library.Utils             import forceRef, forceString, toVariant, formatShortName
from Registry.AmbCardMixin     import CAmbCardMixin

from Ui_RelationsClientListDialog import Ui_RelationsClientListDialog


class CRelationsClientListDialog(CDialogBase, CAmbCardMixin, Ui_RelationsClientListDialog):
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


    def __init__(self, parent, clientId, hideActions = False):
        CDialogBase.__init__(self, parent)
        self.addModels('RelationsClientList', CRelationsClientListModel(self))
        self.addObject('mnuRelationsClientList', QtGui.QMenu(self))
        self.addObject('actEditClient', QtGui.QAction(u'Открыть регистрационную карточку', self))
        self.addObject('actMoveRegistry', QtGui.QAction(u'Перейти в картотеку', self))

        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setModels(self.tblRelationsClientList,  self.modelRelationsClientList, self.selectionModelRelationsClientList)
        self.tblRelationsClientList.setPopupMenu(self.mnuRelationsClientList)
        self.clientId = clientId
        self.modelRelationsClientList.loadData(self.clientId)
        self.__hideActions = hideActions
        self.mnuRelationsClientList.addAction(self.actEditClient)
        if not self.__hideActions:
            self.mnuRelationsClientList.addAction(self.actMoveRegistry)


    @pyqtSignature('')
    def on_mnuRelationsClientList_aboutToShow(self):
        currentRow = -1
        index = self.tblRelationsClientList.currentIndex()
        if index and index.isValid():
            currentRow = index.row()
        itemPresent = currentRow>=0
        self.actEditClient.setEnabled(itemPresent)
        self.actMoveRegistry.setEnabled(itemPresent)


    @pyqtSignature('')
    def on_actEditClient_triggered(self):
        currentIndex = self.tblRelationsClientList.currentIndex()
        self.getEditClient(currentIndex)


    @pyqtSignature('')
    def on_actMoveRegistry_triggered(self):
        currentIndex = self.tblRelationsClientList.currentIndex()
        if currentIndex and currentIndex.isValid():
            row = currentIndex.row()
            relationId = self.modelRelationsClientList.getRelationId(row)
            if relationId:
                self.close()
                QtGui.qApp.findClient(relationId)


    @pyqtSignature('')
    def on_btnClose_clicked(self):
        self.close()


    @pyqtSignature('QModelIndex')
    def on_tblRelationsClientList_doubleClicked(self, index):
        if not self.__hideActions:
            self.getEditClient(index)


    def getEditClient(self, currentIndex):
        if currentIndex and currentIndex.isValid():
            row = currentIndex.row()
            relationId = self.modelRelationsClientList.getRelationId(row)
            if relationId:
                QtGui.qApp.callWithWaitCursor(self, self.editClient, relationId)


    def editClient(self, clientId):
        from Registry.ClientEditDialog  import CClientEditDialog
        dialog = CClientEditDialog(self)
        try:
            dialog.load(clientId)
            QtGui.qApp.restoreOverrideCursor()
            if dialog.exec_():
                QtGui.qApp.callWithWaitCursor(self, self.modelRelationsClientList.loadData, self.clientId)
        finally:
            dialog.deleteLater()


class CRelationsClientListModel(QAbstractTableModel):
    column = [u'Связан с пациентом']
    def __init__(self, parent):
        QAbstractTableModel.__init__(self, parent)
        self.items = []
        self._cols = []


    def cols(self):
        self._cols = [CCol(u'Связан с пациентом', ['relativeType_id'], 20, 'l')]
        return self._cols


    def columnCount(self, index = None):
        return 1


    def rowCount(self, index = None):
        return len(self.items)


    def headerData(self, section, orientation, role = Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return QVariant(self.column[section])
        return QVariant()


    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        row = index.row()
        if role == Qt.DisplayRole:
            item = self.items[row]
            return toVariant(item[column])
        return QVariant()


    def getRelationId(self, row):
        relationId = None
        if 0 <= row < self.rowCount():
            relationId = self.items[row][1]
        return relationId


    def loadData(self, clientId):
        self.items = []
        db = QtGui.qApp.db
        tableC  = db.table('Client')
        tableCR = db.table('ClientRelation')
        tableRT = db.table('rbRelationType')
        queryTable = tableCR
        queryTable = queryTable.leftJoin(tableRT, tableRT['id'].eq(tableCR['relativeType_id']))
        queryTable = queryTable.leftJoin(tableC, tableC['id'].eq(tableCR['client_id']))
        cond = [tableCR['relative_id'].eq(clientId),
                tableC['deleted'].eq(0),
                tableCR['deleted'].eq(0)]
        fields = ['CONCAT_WS(\' | \', rbRelationType.`code`, CONCAT_WS(\'->\', rbRelationType.`rightName`, rbRelationType.`leftName`)) AS relationType',
                  tableC['lastName'].alias(), tableC['firstName'].name(),
                  tableC['patrName'].name(), tableC['birthDate'].name(),
                  tableC['id'].alias('relationId')]
        records = db.getRecordList(queryTable, fields, cond)
        for record in records:
            relationId = forceRef(record.value('relationId'))
            name = formatShortName(record.value('lastName'),
                                   record.value('firstName'),
                                   record.value('patrName'))
            relationName = ', '.join([name,
                                forceString(record.value('birthDate')),
                                forceString(record.value('relationType'))])
            item = [relationName,
                    relationId
                    ]
            self.items.append(item)
        queryTable = tableCR
        queryTable = queryTable.leftJoin(tableRT, tableRT['id'].eq(tableCR['relativeType_id']))
        queryTable = queryTable.leftJoin(tableC, tableC['id'].eq(tableCR['relative_id']))
        cond = [tableCR['client_id'].eq(clientId),
                tableC['deleted'].eq(0),
                tableCR['deleted'].eq(0)]
        fields = ['CONCAT_WS(\' | \', rbRelationType.`code`, CONCAT_WS(\'->\', rbRelationType.`leftName`, rbRelationType.`rightName`)) AS relationType',
                  tableC['lastName'].alias(), tableC['firstName'].name(),
                  tableC['patrName'].name(), tableC['birthDate'].name(),
                  tableC['id'].alias('relationId')]
        records = db.getRecordList(queryTable, fields, cond)
        for record in records:
            relationId = forceRef(record.value('relationId'))
            name = formatShortName(record.value('lastName'),
                                   record.value('firstName'),
                                   record.value('patrName'))
            relationName = ', '.join([name,
                                forceString(record.value('birthDate')),
                                forceString(record.value('relationType'))])
            item = [relationName,
                    relationId
                    ]
            self.items.append(item)
        self.reset()

