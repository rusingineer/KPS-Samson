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

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QObject, pyqtSignature, QVariant

from library.DialogBase            import CDialogBase
from library.InDocTable            import CInDocTableModel, CDateInDocTableCol, CFloatInDocTableCol, CInDocTableCol
from library.Utils                 import forceDate, forceDouble, forceRef, forceString, pyDate

from Accounting.Tariff             import CTariff
from Orgs.ContractFindComboBox     import CContractTreeFindComboBox
from Registry.AmbCardMixin         import CAmbCardMixin

from Events.Ui_ClientDepositDialog import Ui_ClientDepositDialog


class CCheckLimitContractClientDialog(CDialogBase, CAmbCardMixin, Ui_ClientDepositDialog):
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


    def __init__(self, parent, contractId, clientId, clientAge, clientSex, buttonBoxIgnore, title):
        CDialogBase.__init__(self, parent)
        self.addModels('Deposit', CCheckLimitContractClientModel(self, contractId))
        self.setWindowTitle(title)
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setModels(self.tblDeposit,  self.modelDeposit, self.selectionModelDeposit)
        self.setWindowTitle(title)
        self.contractId = contractId
        self.currentClientId = clientId
        self.clientAge = clientAge
        self.clientSex = clientSex
        self.buttonBoxIgnore = buttonBoxIgnore
        self.btnIgnore.setVisible(self.buttonBoxIgnore)
        self.modelDeposit.loadItems(self.contractId)
        self.on_btnUpdateFactSum_clicked()


    @pyqtSignature('')
    def on_btnClose_clicked(self):
        from Registry.ClientEditDialog   import CClientEditDialog
        from Events.EventEditDialog      import CEventEditDialog

        if isinstance(self.parent(), CClientEditDialog) or isinstance(self.parent(), CEventEditDialog):
            self.parent().btnExit = False
        self.close()


    @pyqtSignature('')
    def on_btnIgnore_clicked(self):
        from Registry.ClientEditDialog   import CClientEditDialog
        from Events.EventEditDialog      import CEventEditDialog

        if isinstance(self.parent(), CClientEditDialog) or isinstance(self.parent(), CEventEditDialog):
            self.parent().btnExit = True
        self.close()


    @pyqtSignature('')
    def on_btnUpdateFactSum_clicked(self):
        self.modelDeposit.factSum = []
        self.modelDeposit.factSumContract = []
        contractIdOfDateList = {}
        contractIdList = {}
        parentObj = QObject.parent(self)
        if not parentObj:
            return
        eventId = parentObj.itemId()
        if hasattr(parentObj, 'tabCash'):
            for row, record in enumerate(parentObj.tabCash.modelAccActions._items):
                accContractId = forceRef(record.value('contract_id'))
                if accContractId:
                    sum = forceDouble(parentObj.tabCash.modelAccActions.items()[row].value('sum'))
                    contractSumList = contractIdList.get(accContractId, 0.0)
                    contractSumList += sum
                    contractIdList[accContractId] = contractSumList

        for row, record in enumerate(self.modelDeposit._items):
            contractId = forceRef(record.value('id'))
            contractDate = forceDate(record.value('date'))
            dateList = contractIdOfDateList.get(contractId, [])
            if contractDate and contractDate not in dateList:
                dateList.append(pyDate(contractDate))
                contractIdOfDateList[contractId] = dateList

        for row, record in enumerate(self.modelDeposit._items):
            contractId = forceRef(record.value('id'))
            contractDate = forceDate(record.value('date'))
            dateList = contractIdOfDateList.get(contractId, [])
            dateList.sort()
            lenDateList = len(dateList)
            if lenDateList > 1:
                begDateContract = dateList[0]
                endDateContract = dateList[lenDateList-1]
            else:
                begDateContract = contractDate
                endDateContract = 0
            sumAction = 0.0
            sumItem = 0.0
            sumCurrentEvent = 0.0
            contractSumAllClients = 0.0
            if contractId:
                db = QtGui.qApp.db
                tableAction = db.table('Action')
                tableEvent = db.table('Event')
                tableAccountItem = db.table('Account_Item')

            #  payStatus != 0
                cond = [tableAction['deleted'].eq(0),
                        tableEvent['deleted'].eq(0),
                        tableAccountItem['deleted'].eq(0),
                        tableAction['contract_id'].eq(contractId),
                        tableAction['payStatus'].ne(0),
                        tableAccountItem['refuseType_id'].isNull()
                        ]
                if eventId:
                    cond.append(tableEvent['id'].ne(eventId))
                if begDateContract:
                    cond.append(tableAction['begDate'].dateGe(begDateContract))
                if endDateContract:
                    cond.append(tableAction['begDate'].dateLt(endDateContract))
                cond.append(tableEvent['client_id'].eq(self.currentClientId))
                table = tableEvent.innerJoin(tableAction, tableEvent['id'].eq(tableAction['event_id']))
                table = table.innerJoin(tableAccountItem, tableAction['id'].eq(tableAccountItem['action_id']))
                records = db.getRecordListGroupBy(table, u'SUM(Account_Item.sum) AS sumAction, Action.contract_id', cond, u'Action.contract_id')
                for newRecord in records:
                    contractId = forceRef(newRecord.value('contract_id'))
                    sumAction += forceDouble(newRecord.value('sumAction'))

            #  payStatus == 0
                tableActionTypeService = db.table('ActionType_Service')
                tableContractTariff = db.table('Contract_Tariff')
                tableA = db.table('Action').alias('A')
                cols = u'''SUM(IF(A.amount > Contract_Tariff.amount AND Contract_Tariff.amount != 0, Contract_Tariff.amount * Contract_Tariff.price,
                A.amount * Contract_Tariff.price))'''
                cond = [tableContractTariff['deleted'].eq(0),
                        tableContractTariff['master_id'].eq(contractId),
                        tableContractTariff['tariffType'].eq(CTariff.ttActionAmount)
                        ]
                cond.append(u'A.id = Action.id')
                if self.clientAge:
                    cond.append(db.joinOr([tableContractTariff['age'].eq(''), tableContractTariff['age'].ge(self.clientAge[3])]))
                cond.append(u'''ActionType_Service.`service_id`=(SELECT ATS.`service_id`
                                FROM ActionType_Service AS ATS
                                WHERE ATS.`master_id`=ActionType_Service.`master_id`
                                AND (ATS.`finance_id` IS NULL OR A.`finance_id`=ATS.`finance_id`)
                                ORDER BY ATS.`finance_id` DESC
                                LIMIT 1)''')
                cond.append(db.joinOr([tableContractTariff['sex'].eq(0), tableContractTariff['sex'].eq(self.clientSex)]))
                table = tableA.innerJoin(tableActionTypeService, tableA['actionType_id'].eq(tableActionTypeService['master_id']))
                table = table.innerJoin(tableContractTariff, tableActionTypeService['service_id'].eq(tableContractTariff['service_id']))
                stmt = db.selectStmtGroupBy(table, cols, cond, u'A.contract_id')

                condQuery = [tableAction['deleted'].eq(0),
                            tableEvent['deleted'].eq(0),
                            tableAction['contract_id'].eq(contractId),
                            tableAction['payStatus'].eq(0)
                            ]
                if eventId:
                    condQuery.append(tableEvent['id'].ne(eventId))
                condQuery.append(tableEvent['client_id'].eq(self.currentClientId))
                tableQuery = tableEvent.innerJoin(tableAction, tableEvent['id'].eq(tableAction['event_id']))
                colsQuery = [u'(%s) AS sumItem'%stmt,
                             tableAction['contract_id']
                             ]
                records = db.getRecordList(tableQuery, colsQuery, condQuery)
                for newRecord in records:
                    contractId = forceRef(newRecord.value('contract_id'))
                    sumItem += forceDouble(newRecord.value('sumItem'))
                sumCurrentEvent = contractIdList.get(contractId, 0.0)
                contractSumAllClients = parentObj.getContractSumAllClients(contractId, contractIdList, eventId)

            self.modelDeposit.factSum.append(sumAction + sumItem + sumCurrentEvent)
            self.modelDeposit.factSumContract.append(contractSumAllClients)
            self.modelDeposit.reset()


class CCheckLimitContractClientModel(CInDocTableModel):
    def __init__(self, parent, contractId):
        CInDocTableModel.__init__(self, 'Contract', 'id', 'id', parent)
        self.addCol(CDateInDocTableCol(u'Дата', 'date', 15, canBeEmpty=True)).setReadOnly(True)
        self.addCol(CCheckLimitContractClientModel.CContractInDocTableCol(self)).setReadOnly(True)
        self.addCol(CFloatInDocTableCol(u'Лимит финансирования', 'limitOfFinancing', 8, precision=4)).setReadOnly(True)
        self.addCol(CFloatInDocTableCol(u'Предел превышения', 'limitExceeding', 8, precision=4)).setReadOnly(True)
        self.addExtCol(CFloatInDocTableCol( u'Сумма фактическая по пациенту',   'factSum', 10), QVariant.Int).setReadOnly(True)
        self.addExtCol(CFloatInDocTableCol( u'Сумма фактическая по договору',   'factSumContract', 10), QVariant.Int).setReadOnly(True)
        self.columnFactSum = self.getColIndex('factSum')
        self.columnFactSumContract = self.getColIndex('factSumContract')
        self.factSum = []
        self.factSumContract = []
        self.contractId = contractId


    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        if role == Qt.DisplayRole:
            if column == self.columnFactSum:
                row = index.row()
                if 0 <= row < len(self.items()) and len(self.factSum) <= len(self.items()):
                    return QVariant(self.factSum[row])
            elif column == self.columnFactSumContract:
                row = index.row()
                if 0 <= row < len(self.items()) and len(self.factSumContract) <= len(self.items()):
                    return QVariant(self.factSumContract[row])
        return CInDocTableModel.data(self, index, role)


    def saveItems(self, masterId):
        pass


    class CContractInDocTableCol(CInDocTableCol):

        def __init__(self, model):
            CInDocTableCol.__init__(self, u'Договор', 'id', 20)
            self.model = model


        def toString(self, val, record):
            contractId = forceRef(val)
            if contractId:
                names = ['number', 'date', 'resolution']
                record = QtGui.qApp.db.getRecord('Contract', names, contractId)
                str = ' '.join([forceString(record.value(name)) for name in names])
            else:
                str = u'не задано'
            return QVariant(str)


        def createEditor(self, parent):
            filter = {}
            editor = CContractTreeFindComboBox(parent, filter)
            return editor


        def getEditorData(self, editor):
            return QVariant(editor.value())


        def setEditorData(self, editor, value, record):
            date = forceDate(record.value('contractDate'))
            editor.setDate(date)


