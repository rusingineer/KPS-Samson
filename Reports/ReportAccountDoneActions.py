# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2020 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

import json

from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignature, QDate, QDateTime

from library.Utils       import firstMonthDay, forceDouble, forceInt, forceRef, forceString, formatName, lastMonthDay
from Events.ActionStatus import CActionStatus
from Events.FinanceTypeListEditorDialog import CFinanceTypeListEditorDialog
from Reports.Report      import CReport
from Reports.ReportBase  import CReportBase, createTable

from Reports.Ui_ReportSetupAccountDoneActions import Ui_ReportSetupAccountDoneActions


class CAccountDoneActionsSetupReport(QtGui.QDialog, Ui_ReportSetupAccountDoneActions):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.patientRequired                = False
        self.groupByPatientVisible          = False
        self.setupByOrgStructureVisible     = False
        self.strongOrgStructureVisible      = False
        self.clientAgeCategoryVisible       = False
        self.onlyClientAsPersonInLPUVisible = False
        self.personVisible                  = False
        self.detailServiceVisible           = False
        self.eventIdentifierTypeVisible     = False
        self.dateTypeVisible                = False
        self.eventStatusVisible             = False
        self.setStrongOrgStructureVisible(      self.strongOrgStructureVisible      )
        self.setGroupByPatientVisible(          self.groupByPatientVisible          )
        self.setSetupByOrgStructureVisible(     self.setupByOrgStructureVisible     )
        self.setClientAgeCategoryVisible(       self.clientAgeCategoryVisible       )
        self.setOnlyClientAsPersonInLPUVisible( self.onlyClientAsPersonInLPUVisible )
        self.setPersonVisible(                  self.personVisible                  )
        self.setDetailServiceVisible(           self.detailServiceVisible           )
        self.setEventIdentifierTypeVisible(     self.eventIdentifierTypeVisible     )
        self.setDateTypeVisible(                self.dateTypeVisible                )
        self.setEventStatusVisible(             self.eventStatusVisible             )
        self.cmbActionTypeGroup.setClass(None)
        self.cmbActionTypeGroup.model().setLeavesVisible(False)
        self.cmbAccountingSystem.setTable('rbAccountingSystem', addNone=True, filter = u'''domain = 'EventType' ''')
        self.financeTypeList = []


    def setDateTypeVisible(self, value):
        self.dateTypeVisible = value
        self.cmbDateType.setVisible(value)
        self.lblDateType.setVisible(value)


    def setEventIdentifierTypeVisible(self, value):
        self.eventIdentifierTypeVisible = value
        self.lblEventIdentifierType.setVisible(value)
        self.cmbEventIdentifierType.setVisible(value)


    def setDetailServiceVisible(self, value):
        self.detailServiceVisible = value
        self.chkDetailService.setVisible(value)


    def setPersonVisible(self, value):
        self.personVisible = value
        self.chkPerson.setVisible(value)
        self.cmbPerson.setVisible(value)


    def setStrongOrgStructureVisible(self, value):
        self.strongOrgStructureVisible = value
        self.chkOrgStructure.setVisible(value)
        self.cmbOrgStructure.setVisible(value)


    def setGroupByPatientVisible(self, value):
        self.groupByPatientVisible = value
        self.chkGroupByPatient.setVisible(value)


    def setSetupByOrgStructureVisible(self, value):
        self.setupByOrgStructureVisible = value
        self.lblReportType.setVisible(value)
        self.cmbReportType.setVisible(value)
        self.chkPatientInfo.setVisible(value)
        self.chkAllOrgStructure.setVisible(value)


    def setClientAgeCategoryVisible(self, value):
        self.clientAgeCategoryVisible = value
        self.chkClientAgeCategory.setVisible(value)
        self.cmbClientAgeCategory.setVisible(value)


    def setOnlyClientAsPersonInLPUVisible(self, value):
        self.onlyClientAsPersonInLPUVisible = value
        self.chkOnlyClientAsPersonInLPU.setVisible(value)


    def setEventStatusVisible(self, value):
        self.eventStatusVisible = value
        self.chkEventStatus.setVisible(value)
        self.cmbEventStatus.setVisible(value)


    def setTitle(self, title):
        self.setWindowTitle(title)


    def setParams(self, params):
        if self.dateTypeVisible:
            self.cmbDateType.setCurrentIndex(params.get('dateType', 0))
        self.edtBegDate.setDate(params.get('begDate', QDate.currentDate()))
        self.edtEndDate.setDate(params.get('endDate', QDate.currentDate()))
        chkClass = params.get('chkClass', False)
        self.chkClass.setChecked(chkClass)
        self.cmbClass.setCurrentIndex(params.get('class', 0))
        chkActionTypeGroup = params.get('chkActionTypeGroup', False)
        self.chkActionTypeGroup.setChecked(chkActionTypeGroup)
        self.cmbActionTypeGroup.setValue(params.get('actionTypeGroupId', None))
        chkStatus = params.get('chkStatus', False)
        self.chkStatus.setChecked(chkStatus)
        self.cmbStatus.setValue(params.get('status', CActionStatus.started))
        self.chkCoefficient.setChecked(params.get('chkCoefficient', False))
        self.cmbReportType.setCurrentIndex(params.get('reportType', 0))
        self.chkAllOrgStructure.setChecked(params.get('chkAllOrgStructure', False))
        self.chkPatientInfo.setChecked(params.get('chkPatientInfo', False))
#        self.cmbContract.setValue(params.get('contractId', None))
        self.cmbContract.setPath(params.get('contractPath', None))
        self.financeTypeList =  params.get('financeTypeList', [])
        if self.financeTypeList:
            db = QtGui.qApp.db
            table = db.table('rbFinance')
            records = db.getRecordList(table, [table['name']], [table['id'].inlist(self.financeTypeList)])
            nameList = []
            for record in records:
                nameList.append(forceString(record.value('name')))
            self.lblFinanceTypeList.setText(u','.join(name for name in nameList if name))
        else:
            self.lblFinanceTypeList.setText(u'не задано')
        self.chkConfirmation.setChecked(params.get('confirmation', False))
        date = QDate.currentDate()
        self.edtConfirmationBegDate.setDate(params.get('confirmationBegDate', firstMonthDay(date)))
        self.edtConfirmationEndDate.setDate(params.get('confirmationEndDate', lastMonthDay(date)))
        self.cmbConfirmationType.setCurrentIndex(params.get('confirmationType', 0))
        self.cmbConfirmationPeriodType.setCurrentIndex(params.get('confirmationPeriodType', 0))
        if self.eventIdentifierTypeVisible:
            self.cmbEventIdentifierType.setCurrentIndex(params.get('eventIdentifierType', 0))
        if self.strongOrgStructureVisible:
            chkOrgStructure = params.get('chkOrgStructure', False)
            self.chkOrgStructure.setChecked(chkOrgStructure)
            self.cmbOrgStructure.setValue(params.get('orgStructureId', None))
        if self.clientAgeCategoryVisible:
            chkClientAgeCategory = params.get('chkClientAgeCategory', False)
            self.chkClientAgeCategory.setChecked(chkClientAgeCategory)
            self.cmbClientAgeCategory.setCurrentIndex(params.get('clientAgeCategory', 0))
            self.cmbClientAgeCategory.setEnabled(chkClientAgeCategory)
        if self.onlyClientAsPersonInLPUVisible:
            self.chkOnlyClientAsPersonInLPU.setChecked(params.get('chkOnlyClientAsPersonInLPU', False))
        if self.personVisible:
            chkPerson = params.get('chkPerson', False)
            self.chkPerson.setChecked(chkPerson)
            self.cmbPerson.setValue(params.get('personId', None))
        if self.detailServiceVisible:
            self.chkDetailService.setChecked(params.get('chkDetailService', False))
        if self.groupByPatientVisible:
            chkGroupByPatient = params.get('chkGroupByPatient', False)
            self.chkGroupByPatient.setChecked(chkGroupByPatient)
        if self.eventStatusVisible:
            chkEventStatus = params.get('chkEventStatus', False)
            self.chkEventStatus.setChecked(chkEventStatus)
            self.cmbEventStatus.setCurrentIndex(params.get('eventStatus',  0))
        self.chkDetailPerson.setChecked(params.get('chkDetailPerson', False))
        self.cmbAccountingSystem.setValue(params.get('accountingSystemId', None))


    def params(self):
        params = {}
        if self.dateTypeVisible:
            params['dateType'] = self.cmbDateType.currentIndex()
        params['begDate']  = self.edtBegDate.date()
        params['endDate']  = self.edtEndDate.date()
        params['chkClass']  = self.chkClass.isChecked()
        if params['chkClass']:
            params['class'] = self.cmbClass.currentIndex()
        params['chkActionTypeGroup']    = self.chkActionTypeGroup.isChecked()
        if params['chkActionTypeGroup']:
            params['actionTypeGroupId'] = self.cmbActionTypeGroup.value()
        params['chkStatus'] = self.chkStatus.isChecked()
        params['chkCoefficient'] = self.chkCoefficient.isChecked()
        params['status']    = self.cmbStatus.value()
#        params['contractId'] = self.cmbContract.value()
        params['contractPath'] = self.cmbContract.getPath()
        params['contractIdList'] = self.cmbContract.getIdList()
        params['contractText'] = forceString(self.cmbContract.currentText())
        params['financeTypeList'] = self.financeTypeList
        params['financeText'] = self.lblFinanceTypeList.text()
        params['confirmation'] = self.chkConfirmation.isChecked()
        params['confirmationType'] = self.cmbConfirmationType.currentIndex()
        params['confirmationPeriodType'] = self.cmbConfirmationPeriodType.currentIndex()
        params['confirmationBegDate'] = self.edtConfirmationBegDate.date()
        params['confirmationEndDate'] = self.edtConfirmationEndDate.date()
        if self.eventIdentifierTypeVisible:
            params['eventIdentifierType'] = self.cmbEventIdentifierType.currentIndex()
        if self.strongOrgStructureVisible:
            params['chkOrgStructure'] = self.chkOrgStructure.isChecked()
            params['orgStructureId'] = self.cmbOrgStructure.value()
            params['orgStructureIdList'] = self.getOrgStructureIdList()
        if self.setupByOrgStructureVisible:
            params['reportType'] = self.cmbReportType.currentIndex()
            if self.chkAllOrgStructure.isEnabled():
                params['chkAllOrgStructure'] = self.chkAllOrgStructure.isChecked()
            else:
                params['chkAllOrgStructure'] = False
            params['chkPatientInfo'] = self.chkPatientInfo.isChecked()
        if self.groupByPatientVisible:
            params['chkGroupByPatient'] = self.chkGroupByPatient.isChecked()
        if self.clientAgeCategoryVisible:
            params['chkClientAgeCategory'] = self.chkClientAgeCategory.isChecked()
            params['clientAgeCategory'] = self.cmbClientAgeCategory.currentIndex()
        if self.onlyClientAsPersonInLPUVisible:
            params['chkOnlyClientAsPersonInLPU'] = self.chkOnlyClientAsPersonInLPU.isChecked()
        if self.personVisible:
            params['chkPerson'] = self.chkPerson.isChecked()
            params['personId'] = self.cmbPerson.value()
        if self.detailServiceVisible:
            params['chkDetailService'] = self.chkDetailService.isChecked()
        if self.eventStatusVisible:
            params['chkEventStatus'] = self.chkEventStatus.isChecked()
            params['eventStatus'] = self.cmbEventStatus.currentIndex()
        params['chkDetailPerson'] = self.chkDetailPerson.isChecked()
        params['accountingSystemId'] = self.cmbAccountingSystem.value()
        return params


    def getOrgStructureModel(self):
        return self.cmbOrgStructure.model()


    def getOrgStructureIdList(self):
        treeIndex = self.cmbOrgStructure._model.index(self.cmbOrgStructure.currentIndex(), 0, self.cmbOrgStructure.rootModelIndex())
        treeItem = treeIndex.internalPointer() if treeIndex.isValid() else None
        return treeItem.getItemIdList() if treeItem else []


    @pyqtSignature('bool')
    def on_chkGroupByPatient_toggled(self, value):
        if value and not self.chkDetailService.isChecked():
            self.cmbAccountingSystem.setEnabled(False)
        else:
            self.cmbAccountingSystem.setEnabled(True)


    @pyqtSignature('bool')
    def on_chkDetailService_toggled(self, value):
        if not value and self.chkGroupByPatient.isChecked():
            self.cmbAccountingSystem.setEnabled(False)
        else:
            self.cmbAccountingSystem.setEnabled(True)


    @pyqtSignature('int')
    def on_cmbReportType_currentIndexChanged(self, index):
        self.chkAllOrgStructure.setEnabled(index==1)


    @pyqtSignature('bool')
    def on_chkClass_clicked(self, bValue):
        if bValue:
            class_ = self.cmbClass.currentIndex()
        else:
            class_ = None
        self.cmbActionTypeGroup.setClass(class_)


    @pyqtSignature('int')
    def on_cmbClass_currentIndexChanged(self, index):
        self.cmbActionTypeGroup.setClass(index)


    @pyqtSignature('')
    def on_btnFinanceTypeList_clicked(self):
        self.financeTypeList = []
        self.lblFinanceTypeList.setText(u'не задано')
        dialog = CFinanceTypeListEditorDialog(self)
        if dialog.exec_():
            self.financeTypeList = dialog.values()
            if self.financeTypeList:
                db = QtGui.qApp.db
                table = db.table('rbFinance')
                records = db.getRecordList(table, [table['name']], [table['id'].inlist(self.financeTypeList)])
                nameList = []
                for record in records:
                    nameList.append(forceString(record.value('name')))
                self.lblFinanceTypeList.setText(u','.join(name for name in nameList if name))


def selectData(params):
    dateType          = params.get('dateType', 0)
    begDate           = params.get('begDate', None)
    endDate           = params.get('endDate', None)
    class_            = params.get('class', None)
    db = QtGui.qApp.db
    actionTypeGroupId = params.get('actionTypeGroupId', None)
    if actionTypeGroupId:
        actionTypeGroupIdList = db.getDescendants('ActionType', 'group_id', actionTypeGroupId)
    else:
        actionTypeGroupIdList = None
    chkStatus         = params.get('chkStatus', False)
    status            = params.get('status', None)
    chkGroupByPatient = params.get('chkGroupByPatient', False)
    contractIdList    = params.get('contractIdList', None)
    financeTypeList   = params.get('financeTypeList', None)
    confirmation      = params.get('confirmation', False)
    confirmationBegDate = params.get('confirmationBegDate', None)
    confirmationEndDate = params.get('confirmationEndDate', None)
    confirmationType    = params.get('confirmationType', 0)
    confirmationPeriodType = params.get('confirmationType', 0)
    chkClientAgeCategory   = params.get('chkClientAgeCategory', False)
    clientAgeCategory      = params.get('clientAgeCategory', None)
    chkOnlyClientAsPersonInLPU = params.get('chkOnlyClientAsPersonInLPU', False)
    chkOrgStructure = params.get('chkOrgStructure', False)
    orgStructureIdList = params.get('orgStructureIdList', None)
    chkPerson        = params.get('chkPerson', False)
    personId         = params.get('personId', None)
    chkDetailService = params.get('chkDetailService', False)
    chkDetailPerson  = params.get('chkDetailPerson', False)
    eventIdentifierType = params.get('eventIdentifierType', 0)
    chkEventStatus   = params.get('chkEventStatus',  False)
    eventStatus      = params.get('eventStatus',  0)
    chkCoefficient   = params.get('chkCoefficient', False)
    accountingSystemId = params.get('accountingSystemId', None)
    eventIdentifierFieldName = {0:'id', 1:'externalId'}.get(eventIdentifierType, 'id')

    tableAction            = db.table('Action')
    tableActionType        = db.table('ActionType')
    tableContract          = db.table('Contract')
    tablePriceList         = db.table('Contract').alias('ContractPriceList')
    tableAccountItem       = db.table('Account_Item')
    tableAccount           = db.table('Account')
    tableClient            = db.table('Client')
    tableClientWork        = db.table('ClientWork')
    tableEvent             = db.table('Event')
    tableEventType         = db.table('EventType')
    tableEventTypeIdentification = db.table('EventType_Identification')
    tableCreatePerson      = db.table('vrbPersonWithSpeciality').alias('CreatePerson')
    tablePerson            = db.table('vrbPersonWithSpeciality')
    tablePersonExec        = db.table('Person')
    queryTable = tableAction.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
    queryTable = queryTable.innerJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))
    queryTable = queryTable.innerJoin(tableClient, tableClient['id'].eq(tableEvent['client_id']))
    if not(chkGroupByPatient and not chkDetailService):
        queryTable = queryTable.innerJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
        queryTable = queryTable.leftJoin(tableEventTypeIdentification, db.joinAnd([tableEventTypeIdentification['master_id'].eq(tableEventType['id']), tableEventTypeIdentification['deleted'].eq(0)]))
    queryTable = queryTable.innerJoin(tableContract, 'Contract.`id`=IF(Action.`contract_id`, Action.`contract_id`, Event.`contract_id`)')
    queryTable = queryTable.leftJoin(tablePriceList, tableContract['priceListExternal_id'].eq(tablePriceList['id']))
    queryTable = queryTable.innerJoin(tableAccountItem, tableAccountItem['event_id'].eq(tableEvent['id']))
    queryTable = queryTable.innerJoin(tableAccount, tableAccount['id'].eq(tableAccountItem['master_id']))
    queryTable = queryTable.leftJoin(tablePersonExec, tablePersonExec['id'].eq(tableAction['person_id']))
    cond = [tableAction['deleted'].eq(0),
            tableActionType['deleted'].eq(0),
            tableEvent['deleted'].eq(0),
            tableAccountItem['deleted'].eq(0),
            tableAccount['deleted'].eq(0)
            ]
    if dateType:
        cond.append(tableEvent['setDate'].ge(begDate))
        cond.append(tableEvent['setDate'].lt(endDate.addDays(1)))
    else:
        cond.append(tableAction['endDate'].isNotNull())
        cond.append(tableAction['endDate'].ge(begDate))
        cond.append(tableAction['begDate'].lt(endDate.addDays(1)))
    if contractIdList:
        cond.append(tableContract['id'].inlist(contractIdList))
    if financeTypeList:
        cond.append(tableContract['finance_id'].inlist(financeTypeList))
    if confirmation:
        cond.append(tableAccountItem['master_id'].eq(tableAccount['id']))
        if confirmationType == 0:
            cond.append(tableAccountItem['id'].isNull())
        elif confirmationType == 1:
            cond.append(tableAccountItem['date'].isNotNull())
            cond.append(tableAccountItem['number'].ne(''))
        elif confirmationType == 2:
            cond.append(tableAccountItem['date'].isNotNull())
            cond.append(tableAccountItem['number'].ne(''))
            cond.append(tableAccountItem['refuseType_id'].isNull())
        elif confirmationType == 3:
            cond.append(tableAccountItem['date'].isNotNull())
            cond.append(tableAccountItem['number'].ne(''))
            cond.append(tableAccountItem['refuseType_id'].isNotNull())
        if confirmationPeriodType:
            if confirmationBegDate:
                cond.append(tableAccountItem['date'].ge(confirmationBegDate))
            if confirmationEndDate:
                cond.append(tableAccountItem['date'].lt(confirmationEndDate.addDays(1)))
        else:
            if confirmationBegDate:
                cond.append(tableAccount['date'].ge(confirmationBegDate))
            if confirmationEndDate:
                cond.append(tableAccount['date'].lt(confirmationEndDate.addDays(1)))
    if class_ is not None:
        cond.append(tableActionType['class'].eq(class_))
    if actionTypeGroupIdList:
        cond.append(tableActionType['group_id'].inlist(actionTypeGroupIdList))
    if chkStatus and status is not None:
        cond.append(tableAction['status'].eq(status))
    if chkClientAgeCategory and clientAgeCategory is not None:
        ageCond = '< 18' if clientAgeCategory == 0 else '>= 18'
        cond.append('age(Client.`birthDate`,CURRENT_DATE) %s'%ageCond)
    if chkOnlyClientAsPersonInLPU:
        clientWorkJoinCond = [tableClient['id'].eq(tableClientWork['client_id']),
                              'ClientWork.`id`=(SELECT MAX(CW.`id`) FROM ClientWork AS CW WHERE CW.`client_id`=Client.`id`)']
        queryTable = queryTable.innerJoin(tableClientWork, clientWorkJoinCond)
        cond.append(tableClientWork['org_id'].eq(QtGui.qApp.currentOrgId()))
    if (chkOrgStructure and orgStructureIdList) or (chkPerson and personId) or chkDetailPerson:
        queryTable = queryTable.leftJoin(tablePerson, tablePerson['id'].eq(tableAction['person_id']))
    if chkOrgStructure and orgStructureIdList:
        cond.append(tablePerson['orgStructure_id'].inlist(orgStructureIdList))
    if chkPerson and personId:
        cond.append(tablePerson['id'].eq(personId))
    if chkEventStatus:
        cond.append(tableEvent['execDate'].isNull() if eventStatus else tableEvent['execDate'].isNotNull())
    namePaymentCols = u'''IF(EXISTS(SELECT rbFinance.id
                                        FROM rbFinance
                                        WHERE Contract.finance_id IS NOT NULL AND rbFinance.id = Contract.finance_id
                                        AND rbFinance.code = 3), 'ДМС',
                                        IF(Contract.payType = 1, 'наличный',
                                            IF(Contract.payType = 2, 'безналичный',
                                                IF(Contract.payType = 3, 'комбинированный',
                                                    IF(EXISTS(SELECT Event_Payment.id
                                                        FROM Event_Payment
                                                        WHERE Event_Payment.master_id = Event.id
                                                        AND Event_Payment.deleted = 0),
                                                        (SELECT IF(Event_Payment.id = 0, 'наличный', 'безналичный')
                                                        FROM Event_Payment
                                                        WHERE Event_Payment.master_id = Event.id
                                                        AND Event_Payment.deleted = 0
                                                        ORDER BY Event_Payment.dateTime
                                                        LIMIT 1),
                                                            IF(Contract.finance_id IS NOT NULL,
                                                                (SELECT rbFinance.name
                                                                FROM rbFinance
                                                                WHERE rbFinance.id = Contract.finance_id),
                                                                '')
                                                       )
                                                    )
                                        )
                                    )
                            ) AS namePayment'''
    cond.append('''Account_Item.visit_id IS NULL AND IF(Account_Item.action_id IS NOT NULL, Account_Item.action_id = Action.id, 1)''')
    if chkGroupByPatient:
        if not chkDetailService:
            if chkDetailPerson:
                order = [
                         tablePerson['name'].name(),
                         tableClient['lastName'].name(),
                         tableClient['firstName'].name(),
                         tableClient['patrName'].name()
                        ]
            else:
                order = [
                         tableClient['lastName'].name(),
                         tableClient['firstName'].name(),
                         tableClient['patrName'].name()
                        ]
            group  = order + [
                              'Client.id'
                             ]
            fields = order + [tableClient['id'].alias('clientId'),
                              'SUM('+tableAccountItem['amount'].name()+') AS actionsCount',
                              'SUM('+tableAccountItem['sum'].name()+') AS priceSum',
                              tableAction['id'].alias('actionId'),
                              tableAccountItem['price'],
                              tableAccountItem['VAT'],
                              tableAccountItem['usedCoefficients'],
                              tableAccount['number'].alias('accountNumber'),
                              tableAccount['date'].alias('accountDate'),
                              tableAccountItem['number'].alias('accountItemNumber'),
                              tableAccountItem['date'].alias('accountItemDate'),
                              namePaymentCols,
                              u'''IF(Account_Item.unit_id IS NOT NULL,
                                    (SELECT MAU.name FROM rbMedicalAidUnit AS MAU WHERE MAU.id = Account_Item.unit_id ), '') AS unitName''',
                              u'''IF(Event.expert_id IS NOT NULL,
                                    (SELECT PE.name FROM vrbPersonWithSpeciality AS PE WHERE PE.id = Event.expert_id), '') AS expertName'''
                             ]
            if chkDetailPerson:
                fields.append(tablePerson['id'].alias('personExecId'))
                fields.append(tablePerson['name'].alias('personExecName'))
                fields.append(u'''IF(Action.assistant_id IS NOT NULL,
                                    (SELECT P.name FROM vrbPersonWithSpeciality AS P WHERE P.id = Action.assistant_id), '') AS assistantName''')
                fields.append(u'''IF(vrbPersonWithSpeciality.orgStructure_id IS NOT NULL,
                                    (SELECT OS.name FROM OrgStructure AS OS WHERE OS.id = vrbPersonWithSpeciality.orgStructure_id AND OS.deleted = 0), '') AS orgStructureName''')
                fields.append(u'''IF(vrbPersonWithSpeciality.speciality_id IS NOT NULL,
                                    (SELECT SP.name FROM rbSpeciality AS SP WHERE SP.id = vrbPersonWithSpeciality.speciality_id), '') AS specialityName''')
            order.append(u'namePayment')
            group.append(u'namePayment')
            group.append(u'Account_Item.price')
            group.append(u'Account_Item.VAT')
            stmt = db.selectStmtGroupBy(queryTable, fields, cond, group, order)
        else:
            if chkDetailPerson:
                order = [
                         tablePerson['name'].name(),
                         tableClient['lastName'].name(),
                         tableClient['firstName'].name(),
                         tableClient['patrName'].name(),
                         tableClient['id'].name(),
                         tableAction['endDate'].name()
                        ]
            else:
                order = [
                         tableClient['lastName'].name(),
                         tableClient['firstName'].name(),
                         tableClient['patrName'].name(),
                         tableClient['id'].name(),
                         tableAction['endDate'].name()
                        ]
            fields = [tableAction['endDate'].name(),
                      tableAction['id'].alias('actionId'),
                      tableClient['id'].alias('clientId'),
                      tableClient['lastName'].name(),
                      tableClient['firstName'].name(),
                      tableClient['patrName'].name(),
                      tableEvent[eventIdentifierFieldName].alias('eventIdentifier'),
                      tableActionType['code'].alias('actionTypeCode'),
                      tableActionType['name'].alias('actionTypeName'),
                      tableAccountItem['amount'].name(),
                      tableAccountItem['price'].name(),
                      tableAccountItem['sum'].alias('accountSum'),
                      tableAccountItem['VAT'],
                      tableAccountItem['usedCoefficients'],
                      tableAccount['number'].alias('accountNumber'),
                      tableAccount['date'].alias('accountDate'),
                      tableAccountItem['number'].alias('accountItemNumber'),
                      tableAccountItem['date'].alias('accountItemDate'),
                      namePaymentCols,
                      tableEventTypeIdentification['value'].alias('valueInd'),
                      u'''IF(Event.expert_id IS NOT NULL,
                            (SELECT PE.name FROM vrbPersonWithSpeciality AS PE WHERE PE.id = Event.expert_id), '') AS expertName''',
                      u'''IF(Account_Item.unit_id IS NOT NULL,
                            (SELECT MAU.name FROM rbMedicalAidUnit AS MAU WHERE MAU.id = Account_Item.unit_id ), '') AS unitName'''
                     ]
            if chkDetailPerson:
                fields.append(tablePerson['id'].alias('personExecId'))
                fields.append(tablePerson['name'].alias('personExecName'))
                fields.append(u'''IF(Action.assistant_id IS NOT NULL,
                                    (SELECT P.name FROM vrbPersonWithSpeciality AS P WHERE P.id = Action.assistant_id), '') AS assistantName''')
                fields.append(u'''IF(vrbPersonWithSpeciality.orgStructure_id IS NOT NULL,
                                    (SELECT OS.name FROM OrgStructure AS OS WHERE OS.id = vrbPersonWithSpeciality.orgStructure_id AND OS.deleted = 0), '') AS orgStructureName''')
                fields.append(u'''IF(vrbPersonWithSpeciality.speciality_id IS NOT NULL,
                                    (SELECT SP.name FROM rbSpeciality AS SP WHERE SP.id = vrbPersonWithSpeciality.speciality_id), '') AS specialityName''')
            if chkCoefficient:
                pass
            if accountingSystemId:
                cond.append(tableEventTypeIdentification['system_id'].eq(accountingSystemId))
            cond.append(tableEventType['deleted'].eq(0))
            stmt = db.selectStmt(queryTable, fields, cond, order)
    else:
        queryTable = queryTable.leftJoin(tableCreatePerson, tableCreatePerson['id'].eq(tableAction['createPerson_id']))
        if chkDetailPerson:
            order  = [tablePerson['name'].name(), tableAction['endDate'].name()]
        else:
            order  = [tableAction['endDate'].name()]
        fields = [tableAction['endDate'].name(),
                  tableAction['id'].alias('actionId'),
                  tableClient['id'].alias('clientId'),
                  tableClient['lastName'].name(),
                  tableClient['firstName'].name(),
                  tableClient['patrName'].name(),
                  tableEvent[eventIdentifierFieldName].alias('eventIdentifier'),
                  tableActionType['code'].alias('actionTypeCode'),
                  tableActionType['name'].alias('actionTypeName'),
                  tableCreatePerson['name'].alias('personName'),
                  tableAccountItem['amount'].name(),
                  tableAccountItem['price'].name(),
                  tableAccountItem['VAT'],
                  tableAccountItem['sum'].alias('accountSum'),
                  tableAccountItem['usedCoefficients'],
                  tableAccount['number'].alias('accountNumber'),
                  tableAccount['date'].alias('accountDate'),
                  tableAccountItem['number'].alias('accountItemNumber'),
                  tableAccountItem['date'].alias('accountItemDate'),
                  namePaymentCols,
                  tableEventTypeIdentification['value'].alias('valueInd'),
                  u'''IF(Event.expert_id IS NOT NULL,
                        (SELECT PE.name FROM vrbPersonWithSpeciality AS PE WHERE PE.id = Event.expert_id), '') AS expertName''',
                  u'''IF(Account_Item.unit_id IS NOT NULL,
                        (SELECT MAU.name FROM rbMedicalAidUnit AS MAU WHERE MAU.id = Account_Item.unit_id ), '') AS unitName'''
                  ]
        if chkDetailPerson:
            fields.append(tablePerson['id'].alias('personExecId'))
            fields.append(tablePerson['name'].alias('personExecName'))
            fields.append(u'''IF(Action.assistant_id IS NOT NULL,
                                (SELECT P.name FROM vrbPersonWithSpeciality AS P WHERE P.id = Action.assistant_id), '') AS assistantName''')
            fields.append(u'''IF(vrbPersonWithSpeciality.orgStructure_id IS NOT NULL,
                                (SELECT OS.name FROM OrgStructure AS OS WHERE OS.id = vrbPersonWithSpeciality.orgStructure_id AND OS.deleted = 0), '') AS orgStructureName''')
            fields.append(u'''IF(vrbPersonWithSpeciality.speciality_id IS NOT NULL,
                                (SELECT SP.name FROM rbSpeciality AS SP WHERE SP.id = vrbPersonWithSpeciality.speciality_id), '') AS specialityName''')
        if chkCoefficient:
            pass
        if accountingSystemId:
            cond.append(tableEventTypeIdentification['system_id'].eq(accountingSystemId))
        cond.append(tableEventType['deleted'].eq(0))
        stmt = db.selectStmt(queryTable, fields, cond, order)
    query = db.query(stmt)
    return query


class CReportAccountDoneActions(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Отчет по выписанным услугам')


    def getSetupDialog(self, parent):
        result = CAccountDoneActionsSetupReport(parent)
        result.setGroupByPatientVisible(True)
        result.setDateTypeVisible(True)
        result.setClientAgeCategoryVisible(True)
        result.setOnlyClientAsPersonInLPUVisible(True)
        result.setStrongOrgStructureVisible(True)
        result.setPersonVisible(True)
        result.setDetailServiceVisible(True)
        result.setEventIdentifierTypeVisible(True)
        result.setEventStatusVisible(True)
        result.setTitle(self.title())
        return result


    def build(self, params):
        query = selectData(params)
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        tableColumns = [
                        ('%2', [u'№'], CReportBase.AlignRight),
                        ('%5', [u'Код пациента'], CReportBase.AlignLeft),
                        ('%5', [u'ФИО пациента'], CReportBase.AlignLeft),
                        ('%5', [u'Количество'], CReportBase.AlignLeft),
                        ('%5', [u'Сумма'], CReportBase.AlignLeft),
                        ('%5', [u'Сумма НДС'], CReportBase.AlignLeft),
                        ('%5', [u'Итого'], CReportBase.AlignLeft),
                        ('%5', [u'Оператор'], CReportBase.AlignLeft),
                        ('%5', [u'Форма оплаты'], CReportBase.AlignLeft),
                        ('%5', [u'№ Счета'], CReportBase.AlignLeft),
                        ('%5', [u'Дата счета'], CReportBase.AlignLeft),
                        ('%5', [u'№ПП'], CReportBase.AlignLeft),
                        ('%5', [u'Дата ПП'], CReportBase.AlignLeft)
                        ]
        chkGroupByPatient = params.get('chkGroupByPatient', False)
        chkDetailService  = params.get('chkDetailService', False)
        chkDetailPerson   = params.get('chkDetailPerson', False)
        chkCoefficient    = params.get('chkCoefficient', False)
        if not chkGroupByPatient or (chkGroupByPatient and chkDetailService):
            tableColumns.insert(3, ('%5', [u'Дата и время'], CReportBase.AlignLeft))
            tableColumns.insert(4, ('%5', [u'№ИБ'], CReportBase.AlignLeft))
            tableColumns.insert(5, ('%5', [u'Код действия'], CReportBase.AlignLeft))
            tableColumns.insert(6, ('%5', [u'Наименование действия'], CReportBase.AlignLeft))
            tableColumns.insert(7, ('%5', [u'Единица измерения'], CReportBase.AlignLeft))
            tableColumns.insert(8, ('%5', [u'Цена за единицу'], CReportBase.AlignLeft))
            tableColumns.insert(13,('%5', [u'Место оказания услуги'], CReportBase.AlignLeft))
            if chkDetailPerson:
                resume = [0]*18
                resumeColumns = [13, 14, 15, 16]
            else:
                resume = [0]*13
                resumeColumns = [8, 9, 10, 11]
        else:
            if chkDetailPerson:
                resume = [0]*12
                resumeColumns = [7, 8, 9, 10]
            else:
                resume = [0]*6
                resumeColumns = [2, 3, 4, 5]
        if chkDetailPerson:
            tableColumns.insert(1, ('%5', [u'ФИО врача выполнившего услугу'], CReportBase.AlignLeft))
            tableColumns.insert(2, ('%5', [u'Специальность врача'], CReportBase.AlignLeft))
            tableColumns.insert(3, ('%5', [u'Отделение'], CReportBase.AlignLeft))
            tableColumns.insert(4, ('%5', [u'Ассистент'], CReportBase.AlignLeft))
        if chkCoefficient:
            tableColumns.append(('%5',[u'Наименование коэффициента'], CReportBase.AlignLeft))
            tableColumns.append(('%5',[u'Коэффициент'], CReportBase.AlignLeft))
        table = createTable(cursor, tableColumns)
        boldChars = QtGui.QTextCharFormat()
        boldChars.setFontWeight(QtGui.QFont.Bold)
        prevClientId = None
#        prevPersonExecId = None
        rowShift = 0
#        rowPerson = 1
        valuesList = []
        while query.next():
            record = query.record()
            clientIdValue = clientId = forceRef(record.value('clientId'))
            clientName = formatName(
                                    record.value('lastName'),
                                    record.value('firstName'),
                                    record.value('patrName')
                                   )
            VAT               = forceDouble(record.value('VAT'))
            accountNumber     = forceString(record.value('accountNumber'))
            accountDate       = forceString(record.value('accountDate'))
            accountItemNumber = forceString(record.value('accountItemNumber'))
            accountItemDate   = forceString(record.value('accountItemDate'))
            expertName        = forceString(record.value('expertName'))
            unitName          = forceString(record.value('unitName'))
            namePayment       = forceString(record.value('namePayment'))
            valueInd          = forceString(record.value('valueInd'))
            if chkGroupByPatient and not chkDetailService:
                actionsCount = forceInt(record.value('actionsCount'))
                price        = forceDouble(record.value('price'))
                priceSum     = forceDouble(record.value('priceSum'))
                VATSum = ((price*VAT)/(100.0+VAT))*actionsCount
                values = [clientIdValue, clientName, actionsCount, priceSum, VATSum, priceSum-VATSum, expertName, namePayment, accountNumber, accountDate, accountItemNumber, accountItemDate]
            else:
                date = forceString(record.value('endDate'))
                eventIdentifier = forceString(record.value('eventIdentifier'))
                actionTypeName  = forceString(record.value('actionTypeName'))
                actionTypeCode  = forceString(record.value('actionTypeCode'))
                amount     = forceDouble(record.value('amount'))
                price      = forceDouble(record.value('price'))
                priceSum   = forceDouble(record.value('accountSum'))
                VATSum = ((price*VAT)/(100.0+VAT))*amount
                if chkGroupByPatient and chkDetailService and clientId == prevClientId:
                    clientIdValue = clientName = ''
                values = [clientIdValue, clientName, date, eventIdentifier, actionTypeCode, actionTypeName, unitName, price, amount, priceSum, VATSum, priceSum-VATSum, valueInd, expertName, namePayment, accountNumber, accountDate, accountItemNumber, accountItemDate]
            if chkDetailPerson:
                personExecName = forceString(record.value('personExecName'))
                personExecId = forceRef(record.value('personExecId'))
                orgStructureName = forceString(record.value('orgStructureName'))
                specialityName = forceString(record.value('specialityName'))
                assistantName = forceString(record.value('assistantName'))
                values.insert(0, personExecId)
                values.insert(1, personExecName)
                values.insert(2, specialityName)
                values.insert(3, orgStructureName)
                values.insert(4, assistantName)
            if chkCoefficient:
                usedCoefficients = forceString(record.value('usedCoefficients'))
                usedCoefficientsList = []
                if usedCoefficients != u'':
                    coefficientList = json.loads(usedCoefficients)
                    for group, list in coefficientList.iteritems():
                        for name, value in list.iteritems():
                            usedCoefficientsList.append([name, value])
                values.append(usedCoefficientsList)
            valuesList.append(values)
        idxSum = [10, 11]
        if chkDetailPerson:
            idxSum = [15, 16]
        if chkGroupByPatient and not chkDetailService:
            if chkDetailPerson:
                idxSum = [9, 10]
            else:
                idxSum = [4, 5]
        for values in valuesList:
            i = table.addRow()
            table.setText(i, 0, i)
            len_Values = len(values)
            for valueIdx, value in enumerate(values):
                if chkDetailPerson and valueIdx in [0, 1, 2, 3]:
#                    personExecId = values[0]
#                    if personExecId != prevPersonExecId:
#                        prevPersonExecId = personExecId
#                        rowPerson = i
#                    table.setText(i, 1, values[1])
#                    table.setText(i, 2, values[2])
#                    table.setText(i, 3, values[3])
                    if valueIdx != 0:
                        valItem = values[valueIdx]
                        table.setText(i, valueIdx, valItem if valItem else u'не задано')
                else:
                    if chkCoefficient:
                        if valueIdx == len_Values-1:
                            coeffNames = u''
                            coeffValues = u''
                            for coeff in value:
                                coeffNames += coeff[0] + u'\n'
                                coeffValues += forceString(coeff[1]) + u'\n'
                            table.setText(i, valueIdx if chkDetailPerson else valueIdx+1, coeffNames)
                            table.setText(i, (valueIdx if chkDetailPerson else valueIdx+1)+1, coeffValues)
                        else:
                            if valueIdx in idxSum:
                                table.setText(i, valueIdx if chkDetailPerson else valueIdx+1, '%.2f'%(round(float(value), 2)))
                            else:
                                table.setText(i, valueIdx if chkDetailPerson else valueIdx+1, value)
                            if valueIdx in resumeColumns:
                                resume[valueIdx] += value
                    else:
                        if valueIdx in idxSum:
                            table.setText(i, valueIdx if chkDetailPerson else valueIdx+1, '%.2f'%(round(float(value), 2)))
                        else:
                            table.setText(i, valueIdx if chkDetailPerson else valueIdx+1, value)
                        if valueIdx in resumeColumns:
                            resume[valueIdx] += value
#            if chkDetailPerson:
#                table.mergeCells(rowPerson, 1, i-rowPerson+1, 1)
#                table.mergeCells(rowPerson, 2, i-rowPerson+1, 1)
#                table.mergeCells(rowPerson, 3, i-rowPerson+1, 1)
            if chkGroupByPatient and chkDetailService:
                if clientId != prevClientId:
                    prevClientId = clientId
                    if rowShift:
                        table.mergeCells(rowShift, 1 if not chkDetailPerson else 2, i-rowShift, 1)
                        table.mergeCells(rowShift, 2 if not chkDetailPerson else 3, i-rowShift, 1)
                        rowShift = 1
                    else:
                        rowShift += 1
                else:
                    rowShift += 1
        if chkGroupByPatient and chkDetailService and rowShift:
            table.mergeCells(rowShift, 1 if not chkDetailPerson else 2, i-rowShift+1, 1)
            table.mergeCells(rowShift, 2 if not chkDetailPerson else 3, i-rowShift+1, 1)
        i = table.addRow()
        table.mergeCells(i, 0, 1, 2)
        table.setText(i, 0, u'Всего', charFormat=boldChars)
        for column in resumeColumns:
            if column in idxSum:
                table.setText(i, column if chkDetailPerson else column+1, '%.2f'%(round(float(resume[column]), 2)), charFormat=boldChars)
            else:
                table.setText(i, column if chkDetailPerson else column+1, resume[column], charFormat=boldChars)
        return doc


    def getDescription(self, params):
        dateType          = params.get('dateType', None)
        begDate           = params.get('begDate', None)
        endDate           = params.get('endDate', None)
        class_            = params.get('class', None)
        actionTypeGroupId = params.get('actionTypeGroupId', None)
        chkStatus         = params.get('chkStatus', False)
        status            = params.get('status', None)
        chkGroupByPatient = params.get('chkGroupByPatient', None)
        contractText      = params.get('contractText', None)
        financeText       = params.get('financeText', None)
        confirmation      = params.get('confirmation', False)
        confirmationBegDate = params.get('confirmationBegDate', None)
        confirmationEndDate = params.get('confirmationEndDate', None)
        confirmationType    = params.get('confirmationType', 0)
        confirmationPeriodType = params.get('confirmationPeriodType', 0)
        rows = []
        if dateType is not None:
            rows.append(u'Тип дат: %s'%[u'Даты оказания услуги', u'Даты события'][dateType])
        if begDate:
            rows.append(u'Начальная дата периода: %s'%forceString(begDate))
        if endDate:
            rows.append(u'Конечная дата периода: %s'%forceString(endDate))
        if class_ is not None:
            rows.append(u'Класс типов действия: %s'%[u'статус', u'диагностика', u'лечение', u'прочие мероприятия'][class_])
        if actionTypeGroupId:
            rows.append(u'Группа типов действий: %s'%forceString(QtGui.qApp.db.translate('ActionType', 'id', actionTypeGroupId, 'CONCAT(code, \' | \', name)')))
        if chkStatus and status is not None:
            rows.append(u'Статус: %s'%CActionStatus.text(status))
        if params.get('chkDetailPerson', False):
            rows.append(u'Группировка по исполнителям')
        if chkGroupByPatient:
            rows.append(u'Группировка по пациентам')
        if financeText:
            rows.append(u'Тип финансирования: %s' % financeText)
        if contractText:
            rows.append(u'Контракт: %s' % contractText)
        chkCoefficient = params.get('chkCoefficient', False)
        if chkCoefficient:
            rows.append(u'Учитывать коэффициенты')
        if confirmation:
            rows.append(u'Тип подтверждения: %s'%{0: u'не выставлено',
                                                  1: u'выставлено',
                                                  2: u'оплачено',
                                                  3: u'отказано'}.get(confirmationType, u'не выставлено'))
            rows.append(u'Период подтверждения: %s'%{0: u'по дате формирования счета',
                                                     1: u'по дате подтверждения оплаты'}.get(confirmationPeriodType, u'по дате формирования счета'))
            if confirmationBegDate:
                rows.append(u'Начало периода подтверждения: %s'%forceString(confirmationBegDate))
            if confirmationEndDate:
                rows.append(u'Окончание периода подтверждения: %s'%forceString(confirmationEndDate))
        accountingSystemId = params.get('accountingSystemId', None)
        if accountingSystemId:
            rows.append(u'Внешняя учетная система: %s'%forceString(QtGui.qApp.db.translate('rbAccountingSystem', 'id', accountingSystemId, 'CONCAT(code, \' | \', name)')))
        rows.append(u'отчёт составлен: '+forceString(QDateTime.currentDateTime()))
        return rows

