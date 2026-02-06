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

from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignature, QDate, QDateTime

from library.Utils       import firstMonthDay, forceDouble, forceInt, forceRef, forceString, formatName, lastMonthDay
from Events.ActionStatus import CActionStatus
from Reports.Report      import CReport
from Reports.ReportBase  import CReportBase, createTable

from Reports.Ui_ReportSetupDoneActions import Ui_ReportSetupDoneActionsDialog


class CSetupReport(QtGui.QDialog, Ui_ReportSetupDoneActionsDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.cmbFinance.setTable('rbFinance', addNone=True)
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
        self.cmbReportType.setCurrentIndex(params.get('reportType', 0))
        self.chkAllOrgStructure.setChecked(params.get('chkAllOrgStructure', False))
        self.chkPatientInfo.setChecked(params.get('chkPatientInfo', False))
#        self.cmbContract.setValue(params.get('contractId', None))
        self.cmbContract.setPath(params.get('contractPath', None))
        self.cmbFinance.setValue(params.get('financeId', None))
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
        params['status']    = self.cmbStatus.value()
#        params['contractId'] = self.cmbContract.value()
        params['contractPath'] = self.cmbContract.getPath()
        params['contractIdList'] = self.cmbContract.getIdList()
        params['contractText'] = forceString(self.cmbContract.currentText())
        params['financeId']  = self.cmbFinance.value()
        params['financeText'] = self.cmbFinance.currentText()
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
        return params


    def getOrgStructureModel(self):
        return self.cmbOrgStructure.model()


    def getOrgStructureIdList(self):
        treeIndex = self.cmbOrgStructure._model.index(self.cmbOrgStructure.currentIndex(), 0, self.cmbOrgStructure.rootModelIndex())
        treeItem = treeIndex.internalPointer() if treeIndex.isValid() else None
        return treeItem.getItemIdList() if treeItem else []


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
    financeId         = params.get('financeId', None)
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
    eventIdentifierFieldName = {0:'id', 1:'externalId'}.get(eventIdentifierType, 'id')

    tableAction            = db.table('Action')
    tableActionType        = db.table('ActionType')
    tableActionTypeService = db.table('ActionType_Service')
    tableContract          = db.table('Contract')
    tablePriceList         = db.table('Contract').alias('ContractPriceList')
    tableContractTariff    = db.table('Contract_Tariff')
    tableClient            = db.table('Client')
    tableClientWork        = db.table('ClientWork')
    tableEvent             = db.table('Event')
    tableCreatePerson      = db.table('vrbPersonWithSpeciality').alias('CreatePerson')
    tablePerson            = db.table('vrbPersonWithSpeciality')
    tablePersonExec        = db.table('Person')
    queryTable = tableAction.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
    queryTable = queryTable.innerJoin(tableActionTypeService, tableActionType['id'].eq(tableActionTypeService['master_id']))
    queryTable = queryTable.innerJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))
    queryTable = queryTable.innerJoin(tableClient, tableClient['id'].eq(tableEvent['client_id']))
    queryTable = queryTable.innerJoin(tableContract, 'Contract.`id`=IF(Action.`contract_id`, Action.`contract_id`, Event.`contract_id`)')
    queryTable = queryTable.leftJoin(tablePriceList, tableContract['priceListExternal_id'].eq(tablePriceList['id']))
    queryTable = queryTable.innerJoin(tableContractTariff, '''(Contract_Tariff.id = (SELECT MIN(CT.id)
                                                                                    FROM Contract_Tariff AS CT
                                                                                    WHERE
                                                                                    CT.deleted = 0
                                                                                    AND (CT.master_id = Contract.id OR CT.master_id = ContractPriceList.id)
                                                                                    AND CT.service_id = ActionType_Service.service_id
                                                                                    AND ((Person.tariffCategory_id IS NULL AND CT.tariffCategory_id IS NULL)
                                                                                         OR (CT.tariffCategory_id = Person.tariffCategory_id OR CT.tariffCategory_id IS NULL))
                                                                                    AND (CT.eventType_id = Event.eventType_id
                                                                                         OR CT.eventType_id IS NULL)
                                                                                    AND ((CT.age IS NULL AND (CT.sex = 0 OR CT.sex = Client.sex))
                                                                                        OR (CT.age IS NOT NULL
                                                                                        AND (SELECT isSexAndAgeSuitable(Client.sex, Client.birthDate, CT.sex, CT.age, Action.begDate))))
                                                                                    AND ((CT.begDate <= Action.endDate OR CT.begDate IS NULL)
                                                                                         AND (CT.endDate >= Action.begDate OR CT.endDate IS NULL))
                                                                                    AND ((CT.result_id = Event.result_id) OR (CT.result_id IS NULL OR Event.result_id IS NULL))
                                                                                    AND ((CT.MKB IS NULL OR ((Action.MKB IS NOT NULL AND CT.MKB = Action.MKB)
                                                                                        OR (Action.MKB IS NULL AND CT.MKB = (SELECT Diagnosis.MKB
                                                                                    FROM Diagnosis INNER JOIN Diagnostic ON Diagnostic.diagnosis_id=Diagnosis.id
                                                                                    INNER JOIN rbDiagnosisType ON Diagnostic.diagnosisType_id=rbDiagnosisType.id
                                                                                    WHERE Diagnostic.event_id = Event.id AND Diagnosis.deleted = 0 AND Diagnostic.deleted = 0
                                                                                    AND (rbDiagnosisType.code = '1'
                                                                                    OR (rbDiagnosisType.code = '2' AND Diagnostic.person_id = Event.execPerson_id
                                                                                    AND (NOT EXISTS (SELECT DC.id FROM Diagnostic AS DC
                                                                                    INNER JOIN rbDiagnosisType AS DT ON DT.id = DC.diagnosisType_id WHERE DT.code = '1'
                                                                                    AND DC.event_id = Event.id
                                                                                    LIMIT 1)))) LIMIT 1)))))
                                                                                    )
                                                              AND Contract_Tariff.deleted = 0)''')
    queryTable = queryTable.leftJoin(tablePersonExec, tablePersonExec['id'].eq(tableAction['person_id']))
    contractTariffCond = 'IF(ActionType_Service.`finance_id`, ActionType_Service.`finance_id`=Contract.`finance_id` AND Contract_Tariff.`service_id`=ActionType_Service.`service_id`, ActionType_Service.`finance_id` IS NULL AND Contract_Tariff.`service_id`=ActionType_Service.`service_id`)'
    cond = [tableAction['deleted'].eq(0),
            tableActionType['deleted'].eq(0),
            tableEvent['deleted'].eq(0),
            u'Contract_Tariff.`service_id`=ActionType_Service.service_id',
            contractTariffCond
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
    if financeId:
        cond.append(tableContract['finance_id'].eq(financeId))
    if confirmation:
        tableAccountItem = db.table('Account_Item')
        queryTable = queryTable.leftJoin(tableAccountItem, tableAccountItem['action_id'].eq(tableAction['id']))
        cond.append(tableAccountItem['deleted'].eq(0))
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
            tableAccount = db.table('Account')
            queryTable = queryTable.leftJoin(tableAccount, tableAccount['id'].eq(tableAccountItem['master_id']))
            cond.append(tableAccount['deleted'].eq(0))
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
                              'Client.`id`'
                             ]
            fields = order + [tableClient['id'].alias('clientId'),
                              'SUM('+tableAction['amount'].name()+') AS actionsCount',
                              'SUM('+tableContractTariff['price'].name()+'*'+tableAction['amount'].name()+') AS priceSum',
                              tableAction['id'].alias('actionId')
                             ]
            if chkDetailPerson:
                fields.append(tablePerson['id'].alias('personExecId'))
                fields.append(tablePerson['name'].alias('personExecName'))
            stmt = db.selectStmtGroupBy(queryTable, fields, cond, group, order)
        else:
            if chkDetailPerson:
                order = [
                         tablePerson['name'].name(),
                         tableClient['lastName'].name(),
                         tableClient['firstName'].name(),
                         tableClient['patrName'].name(),
                         tableClient['id'].name(),
                         tableAction['modifyDatetime'].name()
                        ]
            else:
                order = [
                         tableClient['lastName'].name(),
                         tableClient['firstName'].name(),
                         tableClient['patrName'].name(),
                         tableClient['id'].name(),
                         tableAction['modifyDatetime'].name()
                        ]
            fields = [tableAction['modifyDatetime'].name(),
                      tableAction['id'].alias('actionId'),
                      tableClient['id'].alias('clientId'),
                      tableClient['lastName'].name(),
                      tableClient['firstName'].name(),
                      tableClient['patrName'].name(),
                      tableEvent[eventIdentifierFieldName].alias('eventIdentifier'),
                      tableActionType['code'].alias('actionTypeCode'),
                      tableActionType['name'].alias('actionTypeName'),
                      tableAction['amount'].name(),
                      tableContractTariff['price'].name()
                     ]
            if chkDetailPerson:
                fields.append(tablePerson['id'].alias('personExecId'))
                fields.append(tablePerson['name'].alias('personExecName'))
            stmt = db.selectStmt(queryTable, fields, cond, order)
    else:
        queryTable = queryTable.leftJoin(tableCreatePerson, tableCreatePerson['id'].eq(tableAction['createPerson_id']))
        if chkDetailPerson:
            order  = [tablePerson['name'].name(), tableAction['modifyDatetime'].name()]
        else:
            order  = [tableAction['modifyDatetime'].name()]
        fields = [tableAction['modifyDatetime'].name(),
                  tableAction['id'].alias('actionId'),
                  tableClient['id'].alias('clientId'),
                  tableClient['lastName'].name(),
                  tableClient['firstName'].name(),
                  tableClient['patrName'].name(),
                  tableEvent[eventIdentifierFieldName].alias('eventIdentifier'),
                  tableActionType['code'].alias('actionTypeCode'),
                  tableActionType['name'].alias('actionTypeName'),
                  tableCreatePerson['name'].alias('personName'),
                  tableAction['amount'].name(),
                  tableContractTariff['price'].name()
                  ]
        if chkDetailPerson:
            fields.append(tablePerson['id'].alias('personExecId'))
            fields.append(tablePerson['name'].alias('personExecName'))
        stmt = db.selectStmt(queryTable, fields, cond, order)
    query = db.query(stmt)
    return query


class CReportApproxDoneActions(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Предварительный отчет по выписанным услугам')


    def getSetupDialog(self, parent):
        result = CSetupReport(parent)
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
                        ('%2',
                        [u'№'], CReportBase.AlignRight),
                        ('%5',
                        [u'Код пациента'], CReportBase.AlignLeft),
                        ('%5',
                        [u'Имя пациента'], CReportBase.AlignLeft),
                        ('%5',
                        [u'Количество'], CReportBase.AlignLeft),
                        ('%5',
                        [u'Сумма'], CReportBase.AlignLeft),
                        ]
        chkGroupByPatient = params.get('chkGroupByPatient', False)
        chkDetailService  = params.get('chkDetailService', False)
        chkDetailPerson   = params.get('chkDetailPerson', False)
        if not chkGroupByPatient or (chkGroupByPatient and chkDetailService):
            tableColumns.insert(3, ('%5', [u'Дата и время'], CReportBase.AlignLeft))
            tableColumns.insert(4, ('%5', [u'№ обращения'], CReportBase.AlignLeft))
            tableColumns.insert(5, ('%5', [u'Код действия'], CReportBase.AlignLeft))
            tableColumns.insert(6, ('%5', [u'Наименование действия'], CReportBase.AlignLeft))
            tableColumns.insert(7, ('%5', [u'Оператор'], CReportBase.AlignLeft))
            if chkDetailPerson:
                resume = [0]*11
                resumeColumns = [9, 10]
            else:
                resume = [0]*9
                resumeColumns = [7, 8]
        else:
            if chkDetailPerson:
                resume = [0]*6
                resumeColumns = [4, 5]
            else:
                resume = [0]*4
                resumeColumns = [2, 3]
        if chkDetailPerson:
            tableColumns.insert(1, ('%5', [u'Исполнитель'], CReportBase.AlignLeft))
        table = createTable(cursor, tableColumns)
        boldChars = QtGui.QTextCharFormat()
        boldChars.setFontWeight(QtGui.QFont.Bold)
        prevClientId = None
        prevPersonExecId = None
        rowShift = 0
        rowPerson = 1
        valuesList = []
        while query.next():
            record = query.record()
            clientIdValue = clientId = forceRef(record.value('clientId'))
            clientName = formatName(
                                    record.value('lastName'),
                                    record.value('firstName'),
                                    record.value('patrName')
                                   )
            if chkDetailPerson:
                personExecName = forceString(record.value('personExecName'))
                personExecId = forceRef(record.value('personExecId'))
#                if prevPersonExecId == personExecId:
#                    personExecName = ''
            if chkGroupByPatient and not chkDetailService:
                actionsCount = forceInt(record.value('actionsCount'))
                priceSum = forceDouble(record.value('priceSum'))
                values = [clientIdValue, clientName, actionsCount, priceSum]
            else:
                date = forceString(record.value('modifyDatetime'))
                eventIdentifier = forceString(record.value('eventIdentifier'))
                actionTypeCode = forceString(record.value('actionTypeCode'))
                actionTypeName = forceString(record.value('actionTypeName'))
                amount = forceDouble(record.value('amount'))
                price = forceDouble(record.value('price'))
                personName = forceString(record.value('personName'))
                if chkGroupByPatient and chkDetailService and clientId == prevClientId:
                    clientIdValue = clientName = ''
                priceSum = price*amount
                values = [clientIdValue, clientName, date, eventIdentifier, actionTypeCode, actionTypeName, personName, amount, priceSum]
            if chkDetailPerson:
                values.insert(0, personExecId)
                values.insert(1, personExecName)
            valuesList.append(values)
        for values in valuesList:
            i = table.addRow()
            table.setText(i, 0, i)
            for valueIdx, value in enumerate(values):
                if chkDetailPerson and valueIdx in [0, 1]:
                    personExecId = values[0]
                    if personExecId != prevPersonExecId:
                        prevPersonExecId = personExecId
                        rowPerson = i
                        table.setText(i, 1, values[1])
                else:
                    table.setText(i, valueIdx if chkDetailPerson else valueIdx+1, value)
                    if valueIdx in resumeColumns:
                        resume[valueIdx] += value
            if chkDetailPerson:
                table.mergeCells(rowPerson, 1, i-rowPerson+1, 1)
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
        rows.append(u'отчёт составлен: '+forceString(QDateTime.currentDateTime()))
        return rows

